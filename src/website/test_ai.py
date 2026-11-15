"""Tests for the AI layer. They never call Gemini: a fake client stands in for it.

Run from src/website:   python -m unittest test_ai -v
"""
import json
import unittest
from pathlib import Path

import ai

SCHEMA = json.loads((Path(__file__).parent / "prompts" / "response-schema.json").read_text(encoding="utf-8"))
LABELS = ["2026-11-12 00:00 UTC", "2026-11-12 00:01 UTC", "2026-11-12 00:02 UTC"]


def GoodReply():
    return {
        "Weight": "healthy", "Shed": "not shedding", "Food in bowl": "false", "Current activity": "basking",
        "Hazardous conditions": {"Improper substrate": False, "Unsafe lighting": False, "Temperature too high": False,
                                 "Temperature too low": False, "Humidity too high": False,
                                 "Signs of disease": "none", "Other": "none"},
        "Movement Data": [{"time": label, "position_cm": 10.0 * (i + 1)} for i, label in enumerate(LABELS)],
        "Analysis": "Cheeto basked on the hot side for the whole range.",
    }


class ParseJsonTest(unittest.TestCase):
    def test_plain_and_fenced(self):
        self.assertEqual(ai.ParseJson('{"a": 1}'), {"a": 1})
        self.assertEqual(ai.ParseJson('```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(ai.ParseJson('  ```\n{"a": 1}\n```  '), {"a": 1})

    def test_bad_replies_raise_a_readable_error(self):
        for text in ["", None, "Sorry, I can't help with that.", '{"a": 1', "```json\n```"]:
            with self.assertRaises(ai.AiError):
                ai.ParseJson(text)


class NormalizeResultTest(unittest.TestCase):
    def Normalize(self, raw, width=90):
        return ai.NormalizeResult(raw, SCHEMA, LABELS, width)

    def test_good_reply_passes_through_in_schema_order(self):
        result = self.Normalize(GoodReply())
        self.assertEqual(result, GoodReply())
        self.assertEqual(list(result), list(SCHEMA["properties"]))
        self.assertEqual(list(result["Hazardous conditions"]), list(SCHEMA["properties"]["Hazardous conditions"]["properties"]))

    def test_every_schema_enum_ends_with_its_cant_tell_option(self):
        # NormalizeResult falls back to the last option, so the schema must keep this order.
        for key, spec in SCHEMA["properties"].items():
            if "enum" in spec:
                self.assertRegex(spec["enum"][-1], r"^(can't|no )", key)

    def test_enums_ignore_case_and_fall_back(self):
        raw = GoodReply()
        raw.update({"Weight": " Healthy ", "Shed": "peeling everywhere", "Food in bowl": True, "Current activity": None})
        result = self.Normalize(raw)
        self.assertEqual(result["Weight"], "healthy")
        self.assertEqual(result["Shed"], "can't see lizard")
        self.assertEqual(result["Food in bowl"], "true")
        self.assertEqual(result["Current activity"], "can't see lizard")

    def test_missing_and_unknown_keys(self):
        result = self.Normalize({"Weight": "obese", "Extra": "dropped", "Hazardous conditions": "none"})
        self.assertNotIn("Extra", result)
        self.assertEqual(result["Weight"], "obese")
        self.assertEqual(result["Food in bowl"], "no bowl visible")
        self.assertEqual(result["Hazardous conditions"]["Unsafe lighting"], False)
        self.assertEqual(result["Hazardous conditions"]["Signs of disease"], "none")
        self.assertEqual([m["position_cm"] for m in result["Movement Data"]], [None, None, None])
        self.assertTrue(result["Analysis"])

    def test_hazards_are_coerced(self):
        raw = GoodReply()
        raw["Hazardous conditions"] = {"Improper substrate": "true", "Unsafe lighting": "no", "Temperature too high": 1,
                                       "Temperature too low": None, "Signs of disease": "  stuck shed on toes ",
                                       "Other": None, "Made up": True}
        hazards = self.Normalize(raw)["Hazardous conditions"]
        self.assertEqual(hazards["Improper substrate"], True)
        self.assertEqual(hazards["Unsafe lighting"], False)
        self.assertEqual(hazards["Temperature too high"], True)
        self.assertEqual(hazards["Temperature too low"], False)
        self.assertEqual(hazards["Humidity too high"], False)
        self.assertEqual(hazards["Signs of disease"], "stuck shed on toes")
        self.assertEqual(hazards["Other"], "none")
        self.assertNotIn("Made up", hazards)

    def test_not_an_object_raises(self):
        for raw in [[], "text", None, 3]:
            with self.assertRaises(ai.AiError):
                self.Normalize(raw)

    def test_long_analysis_is_cut(self):
        raw = GoodReply()
        raw["Analysis"] = "x" * 5000
        self.assertEqual(len(self.Normalize(raw)["Analysis"]), ai.MAX_ANALYSIS_CHARS)


class NormalizeMovementTest(unittest.TestCase):
    def Positions(self, raw, width=90):
        movement = ai.NormalizeMovement(raw, LABELS, width)
        self.assertEqual([m["time"] for m in movement], LABELS)
        return [m["position_cm"] for m in movement]

    def test_matched_by_label_even_when_shuffled_or_incomplete(self):
        raw = [{"time": LABELS[2], "position_cm": 30}, {"time": LABELS[0].lower() + " ", "position_cm": 10}]
        self.assertEqual(self.Positions(raw), [10.0, None, 30.0])

    def test_matched_by_order_when_labels_are_unusable_and_count_agrees(self):
        raw = [{"time": "page 1", "position_cm": 1}, {"time": "page 2", "position_cm": 2}, {"position_cm": 3}]
        self.assertEqual(self.Positions(raw), [1.0, 2.0, 3.0])

    def test_unusable_labels_with_wrong_count_give_no_positions(self):
        self.assertEqual(self.Positions([{"time": "page 1", "position_cm": 1}]), [None, None, None])

    def test_positions_are_clamped_rounded_and_cleaned(self):
        raw = [{"time": LABELS[0], "position_cm": -5}, {"time": LABELS[1], "position_cm": "44.44"},
               {"time": LABELS[2], "position_cm": 500}]
        self.assertEqual(self.Positions(raw), [0.0, 44.4, 90.0])
        raw = [{"time": LABELS[0], "position_cm": True}, {"time": LABELS[1], "position_cm": "left"},
               {"time": LABELS[2], "position_cm": float("nan")}]
        self.assertEqual(self.Positions(raw), [None, None, None])

    def test_garbage_input(self):
        for raw in [None, "nope", {}, [1, "a", None]]:
            self.assertEqual(self.Positions(raw), [None, None, None])

    def test_duplicate_labels_keep_the_first(self):
        raw = [{"time": LABELS[0], "position_cm": 5}, {"time": LABELS[0], "position_cm": 80}]
        self.assertEqual(self.Positions(raw), [5.0, None, None])


if __name__ == "__main__":
    unittest.main()
