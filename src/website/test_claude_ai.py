"""Tests for the Claude provider. A fake client stands in for Anthropic: nothing here calls the API.

Run from src/website:   .venv/Scripts/python -m unittest test_claude_ai
"""
import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image

import claude_ai
from ai import AiError

LABELS = ["2026-11-12 00:00 UTC", "2026-11-12 00:01 UTC", "2026-11-12 00:02 UTC"]
SCHEMA = json.loads((Path(__file__).resolve().parent / "prompts" / "response-schema.json").read_text(encoding="utf-8"))
CONFIG = {"enclosureWidthCm": 90}
GOOD = {
    "Weight": "healthy", "Shed": "not shedding", "Food in bowl": "false", "Current activity": "basking",
    "Hazardous conditions": {"Improper substrate": False, "Unsafe lighting": False, "Temperature too high": False,
                             "Temperature too low": False, "Humidity too high": False,
                             "Signs of disease": "none", "Other": "none"},
    "Movement Data": [{"time": label, "position": 10.0 * (i + 1)} for i, label in enumerate(LABELS)],
    "Analysis": "Basked under the lamp the whole time.",
}


def Reply(text, stop="end_turn", extra_blocks=(), model="claude-opus-5-5"):
    return SimpleNamespace(stop_reason=stop, stop_details=None, model=model,
                           content=[*extra_blocks, SimpleNamespace(type="text", text=text)],
                           usage=SimpleNamespace(input_tokens=1200, output_tokens=300))


class FakeClient:
    def __init__(self, reply=None, error=None):
        self.calls, self.reply, self.error = [], reply, error
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.reply


def MakeBundle(folder, pages=3):
    folder = Path(folder)
    (folder / "system.txt").write_text("system prompt", encoding="utf-8")
    (folder / "context.txt").write_text("context chunk", encoding="utf-8")
    (folder / "images-01.txt").write_text("images chunk 1 of 1", encoding="utf-8")
    imgs = [Image.new("RGB", (64, 36), (i * 40, 80, 120)) for i in range(pages)]
    imgs[0].save(folder / "images-01.pdf", save_all=True, append_images=imgs[1:])
    return {"system": "system.txt", "schema": "response-schema.json",
            "chunks": [{"type": "context", "text": "context.txt"},
                       {"type": "images", "text": "images-01.txt", "pdf": "images-01.pdf",
                        "frames": [{"label": label} for label in LABELS[:pages]]}]}


class ClaudeTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.keyFile = Path(self.tmp.name) / "data" / "claude-key.json"
        patcher = mock.patch.object(claude_ai, "KEY_FILE", self.keyFile)
        patcher.start(); self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ, {}, clear=False)
        env.start(); self.addCleanup(env.stop)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("REPTRACKER_CLAUDE_MODEL", None)
        claude_ai.Forget(); self.addCleanup(claude_ai.Forget)


class KeyTest(ClaudeTestCase):
    def test_no_key_is_not_ready(self):
        status = claude_ai.Status()
        self.assertFalse(status["ready"])
        self.assertIn("No API key", status["detail"])

    def test_bad_key_is_refused_and_not_saved(self):
        for bad in ["", "hello", "sk-ant-short", "sk-proj-" + "x" * 40]:
            with self.assertRaises(AiError):
                claude_ai.SaveKey(bad)
        self.assertFalse(self.keyFile.exists())

    def test_save_mask_and_remove(self):
        key = "sk-ant-api03-" + "a" * 40 + "WXYZ"
        claude_ai.SaveKey("  " + key + "\n")
        status = claude_ai.Status()
        self.assertTrue(status["ready"])
        self.assertTrue(status["keySaved"])
        self.assertEqual(status["keyMask"], "sk-ant-…WXYZ")
        self.assertNotIn(key, json.dumps(status))          # the key itself never leaves the server
        claude_ai.RemoveKey()
        self.assertFalse(claude_ai.Status()["ready"])

    def test_saved_key_wins_over_environment(self):
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-env-" + "e" * 30
        self.assertIn("environment", claude_ai.ApiKey()[1])
        claude_ai.SaveKey("sk-ant-saved-" + "s" * 30)
        self.assertEqual(claude_ai.ApiKey()[1], "Settings")


class RequestTest(ClaudeTestCase):
    def test_request_shape(self):
        manifest = MakeBundle(self.tmp.name)
        request = claude_ai.BuildAnalysisRequest(Path(self.tmp.name), manifest, SCHEMA)
        self.assertEqual(request["model"], "claude-opus-5-5")
        self.assertEqual(request["fallbacks"], "default")
        self.assertIn(claude_ai.FALLBACK_BETA, request["betas"])
        self.assertEqual(request["system"], "system prompt")
        content = request["messages"][0]["content"]
        self.assertEqual([b["type"] for b in content], ["text", "document", "text"])
        pdf = base64.standard_b64decode(content[1]["source"]["data"])
        self.assertTrue(pdf.startswith(b"%PDF"))
        schema = request["output_config"]["format"]["schema"]
        self.assertNotIn("$schema", schema)
        self.assertNotIn("title", schema)
        position = schema["properties"]["Movement Data"]["items"]["properties"]["position"]
        self.assertEqual(position["anyOf"], [{"type": "number"}, {"type": "null"}])

    def test_model_can_be_changed(self):
        os.environ["REPTRACKER_CLAUDE_MODEL"] = "claude-sonnet-5-5"
        request = claude_ai.BuildAnalysisRequest(Path(self.tmp.name), MakeBundle(self.tmp.name), SCHEMA)
        self.assertEqual(request["model"], "claude-sonnet-5-5")

    def test_page_count(self):
        MakeBundle(self.tmp.name, pages=3)
        self.assertEqual(claude_ai._PdfPages((Path(self.tmp.name) / "images-01.pdf").read_bytes()), 3)

    def test_too_many_pages_is_refused(self):
        manifest = MakeBundle(self.tmp.name)
        with mock.patch.object(claude_ai, "MAX_PDF_PAGES", 2), self.assertRaises(AiError) as caught:
            claude_ai.BuildAnalysisRequest(Path(self.tmp.name), manifest, SCHEMA)
        self.assertIn("shorter range", str(caught.exception))

    def test_missing_file(self):
        manifest = MakeBundle(self.tmp.name)
        (Path(self.tmp.name) / "images-01.pdf").unlink()
        with self.assertRaises(AiError):
            claude_ai.BuildAnalysisRequest(Path(self.tmp.name), manifest, SCHEMA)


class AnalyzeTest(ClaudeTestCase):
    def Analyze(self, client, pages=3, config=CONFIG):
        claude_ai.SetClient(client)
        return claude_ai.AnalyzeBundle(Path(self.tmp.name), MakeBundle(self.tmp.name, pages), config, SCHEMA)

    def test_good_reply(self):
        client = FakeClient(Reply(json.dumps(GOOD)))
        result = self.Analyze(client)
        self.assertEqual(len(client.calls), 1)                     # one analysis is one request
        self.assertEqual(result["Current activity"], "basking")
        self.assertEqual([m["position"] for m in result["Movement Data"]], [10.0, 20.0, 30.0])
        self.assertEqual(result["_details"]["tokens"], {"prompt": 1200, "output": 300, "total": 1500})
        self.assertEqual(result["_details"]["model"], "claude-opus-5-5")

    def test_no_width_clamps_to_percent(self):
        reply = dict(GOOD, **{"Movement Data": [{"time": LABELS[0], "position": 140}]})
        result = self.Analyze(FakeClient(Reply(json.dumps(reply))), pages=1, config={"enclosureWidthCm": None})
        self.assertEqual(result["Movement Data"][0]["position"], 100.0)

    def test_fallback_is_noted(self):
        reply = Reply(json.dumps(GOOD), extra_blocks=[SimpleNamespace(type="fallback")], model="claude-opus-4-8")
        result = self.Analyze(FakeClient(reply))
        self.assertTrue(any("fallback" in n for n in result["_details"]["notes"]))
        self.assertEqual(result["_details"]["model"], "claude-opus-4-8")

    def test_refusal(self):
        with self.assertRaises(AiError) as caught:
            self.Analyze(FakeClient(Reply("", stop="refusal")))
        self.assertIn("declined", str(caught.exception))

    def test_cut_off(self):
        with self.assertRaises(AiError) as caught:
            self.Analyze(FakeClient(Reply('{"Weight": "hea', stop="max_tokens")))
        self.assertIn("cut off", str(caught.exception))

    def test_not_json(self):
        with self.assertRaises(AiError):
            self.Analyze(FakeClient(Reply("I think it is fine.")))

    def test_api_errors_become_sentences(self):
        AuthenticationError = type("AuthenticationError", (Exception,), {})
        RateLimitError = type("RateLimitError", (Exception,), {})
        APIConnectionError = type("APIConnectionError", (Exception,), {})
        for err, words in [(AuthenticationError("bad key"), "API key"), (RateLimitError("slow down"), "429"),
                           (APIConnectionError("offline"), "Couldn't reach")]:
            with self.subTest(err=type(err).__name__), self.assertRaises(AiError) as caught:
                self.Analyze(FakeClient(error=err))
            self.assertIn(words, str(caught.exception))


class AnswerAndPingTest(ClaudeTestCase):
    def test_answer(self):
        client = FakeClient(Reply("Yes, the warm side is in range."))
        claude_ai.SetClient(client)
        self.assertEqual(claude_ai.Answer("Is it warm enough?"), "Yes, the warm side is in range.")
        self.assertEqual(client.calls[0]["output_config"], {"effort": "low"})

    def test_answer_with_vision_sends_the_picture_first(self):
        client = FakeClient(Reply("It is on the warm rock."))
        claude_ai.SetClient(client)
        claude_ai.Answer("Where is it?", b"\xff\xd8fake-jpeg")
        content = client.calls[0]["messages"][0]["content"]
        self.assertEqual([b["type"] for b in content], ["image", "text"])
        self.assertEqual(content[0]["source"]["media_type"], "image/jpeg")
        self.assertEqual(base64.standard_b64decode(content[0]["source"]["data"]), b"\xff\xd8fake-jpeg")

    def test_ping(self):
        claude_ai.SetClient(FakeClient(Reply("ready")))
        self.assertIn("Claude answered", claude_ai.Ping())

    def test_no_key_stops_before_calling(self):
        with self.assertRaises(AiError) as caught:
            claude_ai.Answer("hello")
        self.assertIn("API key", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
