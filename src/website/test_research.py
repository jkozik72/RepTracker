"""Tests for species profiles (research.py) and the Claude research request. Nothing here calls an AI
or Wikimedia Commons.

Run from src/website:   .venv/Scripts/python -m unittest test_research
"""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import claude_ai
import research

SCHEMA = research.Schema()


def R(lo, hi):
    return {"min": lo, "max": hi}


GOOD = {
    "commonName": "Leopard gecko", "scientificName": "Eublepharis macularius", "animalType": "lizard",
    "activityPattern": "crepuscular", "habitat": "terrestrial", "summary": "A ground-dwelling gecko.",
    "adultSize": {"lengthCm": R(18, 25), "weightG": R(45, 80)}, "lifespanYears": R(15, 20),
    "temperaturesF": {"hotSide": R(88, 92), "coldSide": R(72, 78), "night": R(65, 75), "basking": R(90, 95)},
    "humidityPercent": R(30, 40), "uvb": "Low-level UVB helps.", "diet": "Insects.",
    "feeding": [{"stage": "adult", "intervalDays": R(2, 3), "notes": ""}],
    "droppings": {"intervalDays": R(1, 3), "notes": "Brown with a white urate."},
    "shedding": {"type": "whole", "intervalDays": R(28, 42), "signs": "Pale, dull skin."},
    "observableActivities": ["basking", "hiding"],
    "bodyCondition": {"healthy": "Thick tail.", "underweight": "Thin tail.", "overweight": "Fat pads in armpits."},
    "conditions": [{"name": "Metabolic bone disease", "visibleSigns": ["bowed legs"], "urgency": "vet soon", "notes": ""}],
    "hazards": [{"name": "Loose sand", "description": "Impaction risk."}],
    "husbandryNotes": "", "confidence": "Well established.",
}


class NormalizeTest(unittest.TestCase):
    def test_good_profile_is_kept(self):
        profile, notes = research.NormalizeProfile(json.loads(json.dumps(GOOD)))
        self.assertEqual(profile["temperaturesF"]["hotSide"], {"min": 88.0, "max": 92.0})
        self.assertEqual(notes, [])

    def test_repairs(self):
        raw = json.loads(json.dumps(GOOD))
        raw["animalType"] = "gecko"                                   # not in the enum
        raw["temperaturesF"]["coldSide"] = {"min": 80, "max": "70"}   # backwards, and a string
        raw["humidityPercent"] = {"min": "lots", "max": 40}
        del raw["hazards"]
        raw["extra"] = "dropped"
        profile, notes = research.NormalizeProfile(raw)
        self.assertEqual(profile["animalType"], "other")
        self.assertEqual(profile["temperaturesF"]["coldSide"], {"min": 70.0, "max": 80.0})
        self.assertEqual(profile["humidityPercent"]["min"], 0.0)
        self.assertEqual(profile["hazards"], [])
        self.assertNotIn("extra", profile)
        self.assertTrue(any("swapped" in n for n in notes))

    def test_no_name_is_refused(self):
        for bad in [None, "text", {}, {"commonName": "  "}]:
            with self.assertRaises(research.ResearchError):
                research.NormalizeProfile(bad)


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.object(research, "RESEARCH", Path(self.tmp.name))
        patcher.start(); self.addCleanup(patcher.stop)

    def Save(self, species="leopard gecko"):
        profile, _ = research.NormalizeProfile(json.loads(json.dumps(GOOD)))
        record = research.NewRecord(species, profile, "claude", "claude-haiku-5-5")
        research.WriteRecord(record)
        return record

    def test_found_by_typed_common_or_scientific_name(self):
        self.Save("leo gecko")
        for typed in ["leo gecko", "Leo  Gecko", "leopard gecko", "Eublepharis macularius"]:
            with self.subTest(typed=typed):
                self.assertEqual(research.FindRecord(typed)["slug"], "leo-gecko")
        self.assertIsNone(research.FindRecord("crested gecko"))

    def test_summary_and_prompt_text(self):
        record = self.Save()
        summary = research.Summary(record)
        self.assertEqual(summary["scientificName"], "Eublepharis macularius")
        text = research.PromptText(record)
        self.assertIn("hot side 88-92", text)
        self.assertIn("Metabolic bone disease [vet soon]: bowed legs", text)

    def test_bad_slug_is_refused(self):
        with self.assertRaises(research.ResearchError):
            research.Folder("../escape")

    def test_photos_never_break_a_profile(self):
        record = self.Save()
        with mock.patch.object(research, "_Get", side_effect=OSError("offline")):
            images, note = research.FetchImages(record)
        self.assertEqual(images, [])
        self.assertIn("Wikimedia Commons", note)

    def test_photos_are_saved_with_attribution(self):
        record = self.Save()
        search = {"query": {"pages": {"1": {"index": 1, "title": "File:Gecko.jpg", "imageinfo": [{
            "mime": "image/jpeg", "thumburl": "https://upload.example/gecko.jpg", "descriptionurl": "https://commons.example/Gecko",
            "extmetadata": {"Artist": {"value": "<a href='x'>Ann Example</a>"}, "LicenseShortName": {"value": "CC BY-SA 4.0"}}}]},
            "2": {"index": 2, "title": "File:Map.svg", "imageinfo": [{"mime": "image/svg+xml", "thumburl": "https://upload.example/map.png"}]}}}}
        def fake(url, timeoutS=15):
            return json.dumps(search).encode() if "api.php" in url else b"\xff\xd8jpeg"
        with mock.patch.object(research, "_Get", side_effect=fake):
            images, note = research.FetchImages(record)
        self.assertEqual(note, "")
        self.assertEqual(images, [{"file": "01.jpg", "title": "Gecko.jpg", "author": "Ann Example", "license": "CC BY-SA 4.0",
                                   "source": "https://commons.example/Gecko"}])
        self.assertTrue((Path(self.tmp.name) / record["slug"] / "images" / "01.jpg").exists())


BASE = json.loads((Path(__file__).parent / "prompts" / "response-schema.json").read_text(encoding="utf-8"))
TURTLE_STATS = [{"id": "Shell condition", "label": "Shell", "question": "Look at the shell.",
                 "options": ["normal", "scute shedding", "soft or pitted patches", "white spots", "can't see animal"],
                 "concernOptions": ["soft or pitted patches", "white spots", "not an option"]}]


class SpeciesChecksTest(unittest.TestCase):
    def test_checks_are_cleaned(self):
        notes = []
        stats = research.CleanTrackedStats(TURTLE_STATS + [{"id": "x", "label": "Bad", "options": ["only one"], "concernOptions": []}], notes)
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]["id"], "shell_condition")
        self.assertEqual(stats[0]["options"][-1], "can't see animal")
        self.assertEqual(stats[0]["options"].count("can't see animal"), 1)
        self.assertEqual(stats[0]["concernOptions"], ["soft or pitted patches", "white spots"])
        self.assertTrue(any("Bad" in n for n in notes))

    def Profile(self, **changes):
        raw = json.loads(json.dumps(GOOD)); raw["trackedStats"] = TURTLE_STATS
        raw["observableActivities"] = ["Basking", "swimming"]
        raw["conditions"] = [{"name": "Shell rot", "visibleSigns": ["white patches"], "urgency": "vet soon", "notes": ""}]
        raw.update(changes)
        return {"profile": research.NormalizeProfile(raw)[0]}

    def test_format_built_from_a_profile(self):
        schema = research.BuildResponseSchema(BASE, self.Profile())
        props = schema["properties"]
        self.assertEqual(props["Current activity"]["enum"], ["basking", "swimming", "other", "can't see animal"])
        self.assertEqual(list(props["Species checks"]["properties"]), ["shell_condition"])
        self.assertEqual(props["Species checks"]["required"], ["shell_condition"])
        self.assertEqual(props["Conditions seen"]["items"]["properties"]["name"]["enum"], ["Shell rot", "other"])
        self.assertEqual(BASE["properties"]["Species checks"]["required"], ["shed"])     # the base is not changed

    def test_no_profile_keeps_the_base_and_no_checks_drops_them(self):
        self.assertEqual(research.BuildResponseSchema(BASE, None), BASE)
        frog = self.Profile(trackedStats=[], shedding={"type": "continuous", "intervalDays": R(7, 14), "signs": ""})
        schema = research.BuildResponseSchema(BASE, frog)
        self.assertNotIn("Species checks", schema["properties"])
        self.assertNotIn("Species checks", schema["required"])

    def test_nested_answers_are_cleaned(self):
        import ai
        schema = research.BuildResponseSchema(BASE, self.Profile())
        reply = {"Current activity": "Swimming", "Species checks": {"shell_condition": "White Spots", "extra": "x"},
                 "Conditions seen": [{"name": "shell rot", "signs": "white patch"}, {"name": "made up", "signs": "y"}, "junk"]}
        result = ai.NormalizeResult(reply, schema, [], 100, [])
        self.assertEqual(result["Current activity"], "swimming")
        self.assertEqual(result["Species checks"], {"shell_condition": "white spots"})
        self.assertEqual(result["Conditions seen"], [{"name": "Shell rot", "signs": "white patch"}, {"name": "other", "signs": "y"}])


class ClaudeResearchTest(unittest.TestCase):
    def test_request_is_structured_and_answer_is_parsed(self):
        calls = []
        reply = SimpleNamespace(stop_reason="end_turn", stop_details=None, model="claude-haiku-5-5",
                                content=[SimpleNamespace(type="text", text=json.dumps(GOOD))],
                                usage=SimpleNamespace(input_tokens=900, output_tokens=1800))
        claude_ai.SetClient(SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: calls.append(kw) or reply))))
        self.addCleanup(claude_ai.Forget)
        profile, details = claude_ai.Research("research prompt", SCHEMA)
        self.assertEqual(profile["commonName"], "Leopard gecko")
        self.assertEqual(details["tokens"]["total"], 2700)
        schema = calls[0]["output_config"]["format"]["schema"]
        self.assertNotIn("$schema", schema)
        self.assertNotIn("title", schema)
        self.assertIn("range", schema["$defs"])
        self.assertEqual(calls[0]["messages"][0]["content"], "research prompt")


if __name__ == "__main__":
    unittest.main()
