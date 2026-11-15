"""Tests for the AI layer. They never call Google: a fake client or a fake HTTP transport stands in.

Run from src/website:   python -m unittest test_ai -v

The tests in GeminiWireTest drive the real google-genai library and are skipped when it is
not installed; everything else runs without it.
"""
import base64
import importlib.util
import json
import logging
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import ai

try:
    HAS_SDK = importlib.util.find_spec("google.genai") is not None
except (ImportError, ValueError):
    HAS_SDK = False

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
        notes = []
        result = ai.NormalizeResult({"Weight": "obese", "Extra": "dropped", "Hazardous conditions": "none"}, SCHEMA, LABELS, 90, notes)
        self.assertEqual(len(notes), 2)                       # positions, and the fields shown as unknown
        self.assertIn("Shed, Food in bowl, Current activity, Hazardous conditions", notes[1])
        self.assertNotIn("Weight", notes[1])
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

    def test_hazard_text_that_means_nothing_to_report_becomes_none(self):
        # The dashboard raises an alert for any hazard text other than "none".
        for text in ["None", "none.", "None observed.", "N/A", "n/a", "No", "No signs of disease", "No visible signs of disease observed.",
                     "Nothing", "No other hazards", "No issues detected", "", "  ", None, False]:
            raw = GoodReply()
            raw["Hazardous conditions"]["Signs of disease"] = text
            self.assertEqual(self.Normalize(raw)["Hazardous conditions"]["Signs of disease"], "none", repr(text))
        for text in ["Stuck shed on the toes", "No UVB lamp is visible", "None of the lamps has a guard", "No water bowl"]:
            raw = GoodReply()
            raw["Hazardous conditions"]["Other"] = text
            self.assertEqual(self.Normalize(raw)["Hazardous conditions"]["Other"], text)

    def test_a_good_reply_needs_no_notes(self):
        notes = []
        ai.NormalizeResult(GoodReply(), SCHEMA, LABELS, 90, notes)
        self.assertEqual(notes, [])

    def test_not_an_object_raises(self):
        for raw in [[], "text", None, 3]:
            with self.assertRaises(ai.AiError):
                self.Normalize(raw)

    def test_an_object_with_none_of_the_fields_raises(self):
        # Otherwise {} or an error object would be saved as an analysis that says "can't see lizard" everywhere.
        for raw in [{}, {"error": "model overloaded"}, {"weight": "healthy"}]:
            with self.assertRaises(ai.AiError):
                self.Normalize(raw)

    def test_long_analysis_is_cut(self):
        raw = GoodReply()
        raw["Analysis"] = "x" * 5000
        self.assertEqual(len(self.Normalize(raw)["Analysis"]), ai.MAX_ANALYSIS_CHARS)


class NormalizeMovementTest(unittest.TestCase):
    def Positions(self, raw, width=90, notes=None):
        movement = ai.NormalizeMovement(raw, LABELS, width, notes)
        self.assertEqual([m["time"] for m in movement], LABELS)
        return [m["position_cm"] for m in movement]

    def test_matched_by_label_even_when_shuffled_or_incomplete(self):
        raw = [{"time": LABELS[2], "position_cm": 30}, {"time": LABELS[0].lower() + " ", "position_cm": 10}]
        self.assertEqual(self.Positions(raw), [10.0, None, 30.0])

    def test_matched_by_order_when_labels_are_unusable_and_count_agrees(self):
        raw = [{"time": "page 1", "position_cm": 1}, {"time": "page 2", "position_cm": 2}, {"position_cm": 3}]
        notes = []
        self.assertEqual(self.Positions(raw, notes=notes), [1.0, 2.0, 3.0])
        self.assertIn("by order", notes[0])

    def test_matched_by_order_when_one_label_was_misread_and_count_agrees(self):
        raw = [{"time": LABELS[0], "position_cm": 1}, {"time": "2026-11-12 00:07 UTC", "position_cm": 2}, {"time": LABELS[2], "position_cm": 3}]
        self.assertEqual(self.Positions(raw), [1.0, 2.0, 3.0])

    def test_other_ways_of_writing_the_same_minute_match(self):
        raw = [{"time": "2026-11-12T00:02:00Z", "position_cm": 30}, {"time": "2026-11-12 00:00", "position_cm": 10}]
        notes = []
        self.assertEqual(self.Positions(raw, notes=notes), [10.0, None, 30.0])
        self.assertIn("2 position(s) for 3 images", notes[0])

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


# ---------- calling Gemini, with a fake client (no google-genai needed) ----------

CONFIG = {"enclosureWidthCm": 90}
PDF_BYTES = b"%PDF-1.4 fake pdf bytes \xff\xfe"


def MakeBundle(folder):
    """A bundle on disk with one IMAGES chunk of three images, laid out like main.GeneratePrompts writes it."""
    (folder / "system.txt").write_text("SYSTEM PROMPT", encoding="utf-8")
    (folder / "context.txt").write_text("CONTEXT TEXT", encoding="utf-8")
    (folder / "images-01.txt").write_text("IMAGES TEXT 1", encoding="utf-8")
    (folder / "images-01.pdf").write_bytes(PDF_BYTES)
    return {"system": "system.txt", "schema": "response-schema.json", "chunks": [
        {"type": "context", "text": "context.txt"},
        {"type": "images", "text": "images-01.txt", "pdf": "images-01.pdf",
         "frames": [{"label": label, "file": f"frames/{i}.jpg"} for i, label in enumerate(LABELS)]}]}


def FakeResponse(text, finish="STOP", blocked=None, tokens=1234):
    """Shaped like the parts of google-genai's response that ai.py reads."""
    return SimpleNamespace(
        text=text, prompt_feedback=SimpleNamespace(block_reason=SimpleNamespace(name=blocked) if blocked else None),
        candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name=finish))] if finish else [],
        usage_metadata=SimpleNamespace(prompt_token_count=tokens - 34, candidates_token_count=34, total_token_count=tokens))


class FakeClient:
    """Stands in for genai.Client: records every request and answers with self.reply (a response or an exception)."""

    def __init__(self, reply):
        self.reply, self.requests, self.models = reply, [], self

    def generate_content(self, **request):
        self.requests.append(request)
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


class APIError(Exception):
    """Same name and attributes as google.genai.errors.APIError, which ai.Explain recognises by name."""

    def __init__(self, code, message=None, status=None):
        super().__init__(f"{code} {status}. {{'error': {{'message': {message!r}, 'secret-looking': 'dict repr'}}}}")
        self.code, self.message, self.status = code, message, status


class GoogleAuthError(Exception):
    """Same name as google.auth.exceptions.GoogleAuthError, the base of every sign-in error."""


class RefreshError(GoogleAuthError):
    """Same name and base as google.auth.exceptions.RefreshError."""


class ReadTimeout(TimeoutError):
    pass


class ConnectError(Exception):
    pass


class WithBundle(unittest.TestCase):
    """A bundle on disk and a fake client in place of Gemini; ai.py's remembered login is restored afterwards."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.manifest = MakeBundle(self.folder)
        self.addCleanup(setattr, ai, "_client", ai._client)
        self.addCleanup(setattr, ai, "_login", ai._login)
        logging.disable(logging.CRITICAL)                 # failed calls are logged; keep the test output clean
        self.addCleanup(logging.disable, logging.NOTSET)
        self.Use(FakeResponse(json.dumps(GoodReply())))

    def Use(self, reply):
        self.client = ai._client = FakeClient(reply)
        ai._login = (None, "test-project-123456", "a test")
        return self.client

    def Analyze(self):
        return ai.AnalyzeBundle(self.folder, self.manifest, CONFIG, SCHEMA)

    def Fails(self, fn, *words):
        """fn raises AiError; every word must be in the message the dashboard would show."""
        with self.assertRaises(ai.AiError) as caught:
            fn()
        for word in words:
            self.assertIn(word, str(caught.exception))
        return str(caught.exception)


class RequestTest(WithBundle):
    def test_an_analysis_is_one_request_with_exactly_the_bundle_files_in_order(self):
        result = self.Analyze()
        self.assertEqual(len(self.client.requests), 1)
        request = self.client.requests[0]
        self.assertEqual(set(request), {"model", "contents", "config"})
        self.assertEqual(request["model"], ai.DEFAULT_MODEL)
        self.assertEqual(request["contents"], [{"role": "user", "parts": [
            {"text": "CONTEXT TEXT"}, {"text": "IMAGES TEXT 1"},
            {"inline_data": {"mime_type": "application/pdf", "data": PDF_BYTES}}]}])
        self.assertEqual(request["config"], {
            "system_instruction": "SYSTEM PROMPT", "response_mime_type": "application/json",
            "automatic_continuation": False, "http_options": {"timeout": ai.ANALYSIS_TIMEOUT_S * 1000}})
        details = result.pop("_details")
        self.assertEqual(result, GoodReply())
        self.assertEqual(details["model"], ai.DEFAULT_MODEL)
        self.assertEqual(details["tokens"], {"prompt": 1200, "output": 34, "total": 1234})
        self.assertNotIn("notes", details)                # nothing had to be repaired
        self.assertIsInstance(details["seconds"], float)

    def test_no_schema_no_retries_no_tools_and_no_model_settings_are_sent(self):
        self.Analyze()
        config = self.client.requests[0]["config"]
        for key in ["response_schema", "response_json_schema", "tools", "temperature", "max_output_tokens", "thinking_config"]:
            self.assertNotIn(key, config)
        self.assertNotIn("retry_options", config["http_options"])

    def test_the_time_limit_is_whole_milliseconds(self):
        for timeout in [ai._Options(ai.ANALYSIS_TIMEOUT_S), ai._Options(ai.QUICK_TIMEOUT_S)]:
            ms = timeout["http_options"]["timeout"]
            self.assertIsInstance(ms, int)
            self.assertGreaterEqual(ms, 30_000)           # seconds passed by mistake would be far below this

    def test_model_and_location_come_from_the_environment(self):
        with mock.patch.dict("os.environ", {"REPTRACKER_MODEL": "gemini-other", "GOOGLE_CLOUD_LOCATION": "europe-west4"}):
            self.assertEqual(ai.Settings(), {"model": "gemini-other", "location": "europe-west4"})
            self.assertEqual(self.Analyze()["_details"]["model"], "gemini-other")
        self.assertEqual(self.client.requests[0]["model"], "gemini-other")
        with mock.patch.dict("os.environ", {"REPTRACKER_MODEL": "", "GOOGLE_CLOUD_LOCATION": ""}):
            self.assertEqual(ai.Settings(), {"model": ai.DEFAULT_MODEL, "location": ai.DEFAULT_LOCATION})

    def test_repairs_are_reported_in_notes(self):
        reply = GoodReply()
        reply["Shed"] = "peeling everywhere"
        reply["Movement Data"] = reply["Movement Data"][:2]
        self.Use(FakeResponse(json.dumps(reply)))
        result = self.Analyze()
        self.assertEqual(result["Shed"], "can't see lizard")
        self.assertEqual([m["position_cm"] for m in result["Movement Data"]], [10.0, 20.0, None])
        notes = result["_details"]["notes"]
        self.assertIn("2 position(s) for 3 images", notes[0])
        self.assertIn("Shed", notes[1])

    def test_a_question_is_one_plain_request(self):
        self.Use(FakeResponse("  She is basking on the hot side.  "))
        self.assertEqual(ai.Answer("QUESTION PROMPT"), "She is basking on the hot side.")
        self.assertEqual(self.client.requests, [{"model": ai.DEFAULT_MODEL, "contents": "QUESTION PROMPT", "config": {
            "automatic_continuation": False, "http_options": {"timeout": ai.QUICK_TIMEOUT_S * 1000}}}])

    def test_a_long_answer_is_cut(self):
        self.Use(FakeResponse("x" * 10_000))
        self.assertEqual(len(ai.Answer("q")), ai.MAX_ANSWER_CHARS)

    def test_the_connection_test_is_one_tiny_request(self):
        self.Use(FakeResponse("ready"))
        message = ai.Ping()
        self.assertIn(ai.DEFAULT_MODEL, message)
        self.assertIn("answered", message)
        self.assertEqual(len(self.client.requests), 1)
        self.assertLess(len(self.client.requests[0]["contents"]), 100)


class RefusedBeforeSendingTest(WithBundle):
    def NothingSent(self):
        self.assertEqual(self.client.requests, [])

    def test_a_bundle_without_images(self):
        self.manifest["chunks"][1]["frames"] = []
        self.Fails(self.Analyze, "no camera images")
        self.NothingSent()

    def test_a_bundle_with_a_missing_file(self):
        (self.folder / "images-01.pdf").unlink()
        self.Fails(self.Analyze, "images-01.pdf is missing", "Generate the prompts again")
        self.NothingSent()

    def test_a_request_that_is_too_large(self):
        with mock.patch.object(ai, "MAX_REQUEST_MB", 0.00001):
            self.Fails(self.Analyze, "MB", "shorter range")
        self.NothingSent()

    def test_the_size_is_measured_as_sent(self):
        # 3 MB of PDF travels as 4 MB of base64: over a 3.5 MB limit although the file itself is under it.
        (self.folder / "images-01.pdf").write_bytes(b"x" * 3 * 1024 * 1024)
        with mock.patch.object(ai, "MAX_REQUEST_MB", 3.5):
            self.Fails(self.Analyze, "4 MB request")
        with mock.patch.object(ai, "MAX_REQUEST_MB", 4.5):
            self.Analyze()

    def test_a_computer_that_is_not_set_up_is_told_before_the_files_are_read(self):
        ai._client = ai._login = None
        with mock.patch.object(ai, "Login", side_effect=ai.AiError("not signed in")) as login, \
             mock.patch.object(ai, "BuildAnalysisRequest") as build:
            self.Fails(self.Analyze, "not signed in")
        login.assert_called_once()
        build.assert_not_called()


class ReplyTest(WithBundle):
    def test_replies_that_cannot_be_used_are_never_saved(self):
        good = json.dumps(GoodReply())
        cases = [(FakeResponse("I cannot see a lizard."), ["not valid JSON"]),
                 (FakeResponse("[1, 2]"), ["not in the expected format"]),
                 (FakeResponse("{}"), ["not in the expected format"]),
                 (FakeResponse(good[:200], finish="MAX_TOKENS"), ["cut off", "shorter time range"]),
                 (FakeResponse(good[:200], finish="CONTINUATION"), ["cut off"]),
                 (FakeResponse(None, finish=None, blocked="PROHIBITED_CONTENT"), ["declined", "PROHIBITED_CONTENT"]),
                 (FakeResponse(None, finish="SAFETY"), ["no usable answer", "SAFETY"]),
                 (FakeResponse(good, finish="MALFORMED_RESPONSE"), ["no usable answer", "MALFORMED_RESPONSE"]),
                 (FakeResponse("", finish="STOP"), ["no usable answer"]),
                 (FakeResponse(None, finish=None), ["no usable answer"]),
                 (SimpleNamespace(), ["no usable answer"])]
        for response, words in cases:
            client = self.Use(response)
            message = self.Fails(self.Analyze, *words)
            self.assertIn("nothing was saved", message)
            self.assertEqual(len(client.requests), 1)     # never a second try

    def test_a_fenced_reply_is_accepted(self):
        self.Use(FakeResponse("```json\n" + json.dumps(GoodReply()) + "\n```"))
        self.assertEqual(self.Analyze()["Weight"], "healthy")


class ErrorTest(WithBundle):
    def test_every_failure_is_one_request_and_one_readable_sentence(self):
        cases = [(APIError(401, "Request had invalid authentication credentials.", "UNAUTHENTICATED"), ["gcloud auth application-default login"]),
                 (APIError(403, "Vertex AI API has not been used in project test-project-123456 before or it is disabled.", "PERMISSION_DENIED"),
                  ["Vertex AI API is enabled", "has not been used in project <project>"]),
                 (APIError(404, "Publisher model was not found.", "NOT_FOUND"), [f"'{ai.DEFAULT_MODEL}'", "'global'", "GOOGLE_CLOUD_LOCATION"]),
                 (APIError(429, "Quota exceeded.", "RESOURCE_EXHAUSTED"), ["quota", "Wait a minute"]),
                 (APIError(400, "The document has too many pages.", "INVALID_ARGUMENT"), ["error 400", "too many pages"]),
                 (APIError(413, "<html>Request Entity Too Large</html>"), ["too large", "shorter time range"]),
                 (APIError(503, "The model is overloaded.", "UNAVAILABLE"), ["Google's side", "error 503"]),
                 (APIError(504, "Deadline exceeded.", "DEADLINE_EXCEEDED"), [f"within {ai.ANALYSIS_TIMEOUT_S} s"]),
                 (APIError(418, None, None), ["error 418"]),
                 (RefreshError("('invalid_grant: Token has been expired or revoked.', {})"), ["expired", "gcloud auth application-default login"]),
                 (GoogleAuthError("something new"), ["sign-in failed", "gcloud auth application-default login"]),
                 (ReadTimeout("timed out"), [f"within {ai.ANALYSIS_TIMEOUT_S} s", "shorter time range"]),
                 (ConnectError("getaddrinfo failed"), ["Couldn't reach Google", "internet"]),
                 (RuntimeError("Cannot send a request, as the client has been closed."), ["unexpected", "RuntimeError", "terminal"])]
        for error, words in cases:
            client = self.Use(error)
            message = self.Fails(self.Analyze, *words)
            self.assertEqual(len(client.requests), 1, f"{error!r} must not be retried")
            self.assertNotIn("dict repr", message)        # never str() of Google's error
            self.assertNotIn("test-project-123456", message)
            self.assertNotIn("Traceback", message)

    def test_google_text_is_put_on_one_line_and_cut(self):
        self.Use(APIError(400, "<html>\n  <body>\n" + "very long page " * 100 + "</body></html>"))
        message = self.Fails(self.Analyze, "Google said: <html> <body> very long page")
        self.assertLess(len(message), 400)

    def test_the_time_limit_in_the_message_is_the_one_of_that_request(self):
        self.Use(ReadTimeout("timed out"))
        self.Fails(lambda: ai.Answer("q"), f"within {ai.QUICK_TIMEOUT_S} s")

    def test_a_rejected_sign_in_is_forgotten_so_a_new_login_is_picked_up(self):
        for error, forgotten in [(RefreshError("expired"), True), (APIError(401, "bad token"), True), (GoogleAuthError("x"), True),
                                 (APIError(403, "no permission"), False), (APIError(503, "busy"), False), (ReadTimeout("slow"), False)]:
            self.Use(error)
            self.Fails(self.Analyze)
            self.assertEqual(ai._client is None and ai._login is None, forgotten, repr(error))

    def test_the_client_is_held_for_the_whole_call(self):
        # google-genai closes a client that nothing refers to, so the call must not be chained off GetClient().
        class Closing(FakeClient):
            def generate_content(self, **request):
                ai._client = None                         # as if another thread had dropped the shared client meanwhile
                return super().generate_content(**request)
        self.client = ai._client = Closing(FakeResponse(json.dumps(GoodReply())))
        self.assertEqual(self.Analyze()["Weight"], "healthy")


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(setattr, ai, "_client", ai._client)
        self.addCleanup(setattr, ai, "_login", ai._login)
        ai._client = ai._login = None

    def test_without_the_library_gemini_is_not_ready_and_the_message_says_what_to_install(self):
        with mock.patch.object(ai, "_HasLibrary", return_value=False):
            status = ai.Status()
            self.assertEqual(status["ready"], False)
            self.assertIn("pip install -r requirements.txt", status["detail"])
            with self.assertRaises(ai.AiError):
                ai.Answer("q")
            with self.assertRaises(ai.AiError):
                ai.Ping()

    def test_ready_status_names_model_and_location_but_not_the_whole_project(self):
        ai._login = (None, "my-long-project-id-123", "the Google login's quota project")
        status = ai.Status()
        self.assertEqual(set(status), {"ready", "detail"})
        self.assertEqual(status["ready"], True)
        for word in [ai.DEFAULT_MODEL, ai.DEFAULT_LOCATION, "my-l…123", "quota project", "no API key"]:
            self.assertIn(word, status["detail"])
        self.assertNotIn("my-long-project-id-123", status["detail"])

    def test_status_never_raises(self):
        with mock.patch.object(ai, "Login", side_effect=RuntimeError("boom")):
            logging.disable(logging.CRITICAL)
            self.addCleanup(logging.disable, logging.NOTSET)
            self.assertEqual(ai.Status()["ready"], False)

    @unittest.skipUnless(HAS_SDK, "google-genai is not installed")
    def test_where_the_project_comes_from(self):
        import google.auth.exceptions
        import google.oauth2.credentials
        Creds = google.oauth2.credentials.Credentials
        env = {"GOOGLE_CLOUD_PROJECT": ""}
        with mock.patch.dict("os.environ", env), mock.patch("google.auth.default", return_value=(Creds(token="t", quota_project_id="quota-project"), None)):
            self.assertEqual(ai.Login()[1:], ("quota-project", "the Google login's quota project"))
        ai.Forget()
        with mock.patch.dict("os.environ", env), mock.patch("google.auth.default", return_value=(Creds(token="t", quota_project_id="quota-project"), "gcloud-project")):
            self.assertEqual(ai.Login()[1], "quota-project")
        ai.Forget()
        with mock.patch.dict("os.environ", env), mock.patch("google.auth.default", return_value=(Creds(token="t"), "gcloud-project")):
            self.assertEqual(ai.Login()[1:], ("gcloud-project", "gcloud's default project"))
        ai.Forget()
        with mock.patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "env-project"}), \
             mock.patch("google.auth.default", return_value=(Creds(token="t", quota_project_id="quota-project"), "env-project")):
            self.assertEqual(ai.Login()[1:], ("env-project", "GOOGLE_CLOUD_PROJECT"))
        ai.Forget()
        with mock.patch.dict("os.environ", env), mock.patch("google.auth.default", return_value=(Creds(token="t"), None)):
            status = ai.Status()
            self.assertEqual(status["ready"], False)
            self.assertIn("set-quota-project", status["detail"])
        with mock.patch.dict("os.environ", env), \
             mock.patch("google.auth.default", side_effect=google.auth.exceptions.DefaultCredentialsError("not found")):
            status = ai.Status()
            self.assertEqual(status["ready"], False)
            self.assertIn("gcloud auth application-default login", status["detail"])

    @unittest.skipUnless(HAS_SDK, "google-genai is not installed")
    def test_the_login_is_read_once_and_the_client_gets_project_location_and_credentials(self):
        import google.oauth2.credentials
        creds = google.oauth2.credentials.Credentials(token="t", quota_project_id="quota-project")
        with mock.patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "", "GOOGLE_API_KEY": "stray-key", "GOOGLE_CLOUD_LOCATION": ""}), \
             mock.patch("google.auth.default", return_value=(creds, None)) as default:
            for _ in range(3):
                self.assertEqual(ai.Status()["ready"], True)
            client = ai.GetClient()
            self.assertIs(ai.GetClient(), client)
            default.assert_called_once()
        api = client._api_client
        self.assertEqual((api.project, api.location, api.api_key), ("quota-project", "global", None))
        self.assertIs(api._credentials, creds)
        self.assertTrue(api.vertexai)


# ---------- the same calls through the real google-genai library, with a fake HTTP transport ----------

@unittest.skipUnless(HAS_SDK, "google-genai is not installed")
class GeminiWireTest(unittest.TestCase):
    """What actually goes over the wire, and how the real library's errors come out of ai.py."""

    def setUp(self):
        import datetime
        import google.oauth2.credentials
        from google import genai
        from google.genai import types
        try:
            import httpx2 as httpLib      # the HTTP library google-genai 3.x uses
        except ImportError:
            import httpx as httpLib
        self.httpLib, self.requests = httpLib, []
        self.reply = lambda request: (200, self.Body(json.dumps(GoodReply())))

        def Handle(request):
            self.requests.append(request)
            answer = self.reply(request)
            if isinstance(answer, Exception):
                raise answer
            return httpLib.Response(answer[0], json=answer[1])

        # A token with a far-future expiry: the library never tries to refresh it, so nothing reaches Google.
        creds = google.oauth2.credentials.Credentials(token="fake-token", expiry=datetime.datetime(2099, 1, 1),
                                                      quota_project_id="test-project")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.manifest = MakeBundle(self.folder)
        self.addCleanup(setattr, ai, "_client", ai._client)
        self.addCleanup(setattr, ai, "_login", ai._login)
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)
        ai._login = (creds, "test-project", "a test")
        ai._client = genai.Client(vertexai=True, project="test-project", location="global", credentials=creds,
                                  http_options=types.HttpOptions(client_args={"transport": httpLib.MockTransport(Handle)}))

    @staticmethod
    def Body(text, finish="STOP", **extra):
        return {"candidates": [{"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": finish, **extra}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15}}

    def Analyze(self):
        return ai.AnalyzeBundle(self.folder, self.manifest, CONFIG, SCHEMA)

    def Fails(self, fn, *words):
        with self.assertRaises(ai.AiError) as caught:
            fn()
        for word in words:
            self.assertIn(word, str(caught.exception))

    def test_the_request_on_the_wire(self):
        result = self.Analyze()
        self.assertEqual(len(self.requests), 1)
        request = self.requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(str(request.url), "https://aiplatform.googleapis.com/v1beta1/projects/test-project/locations/global"
                                           f"/publishers/google/models/{ai.DEFAULT_MODEL}:generateContent")
        self.assertEqual(request.headers["authorization"], "Bearer fake-token")
        self.assertEqual(request.headers["x-goog-user-project"], "test-project")
        self.assertEqual(request.headers["x-server-timeout"], str(ai.ANALYSIS_TIMEOUT_S))
        self.assertNotIn("x-goog-api-key", request.headers)
        body = json.loads(request.content)
        self.assertEqual(set(body), {"contents", "systemInstruction", "generationConfig"})
        self.assertEqual(body["systemInstruction"]["parts"], [{"text": "SYSTEM PROMPT"}])
        self.assertEqual(body["generationConfig"], {"responseMimeType": "application/json"})
        self.assertEqual(len(body["contents"]), 1)
        self.assertEqual(body["contents"][0]["role"], "user")
        parts = body["contents"][0]["parts"]
        self.assertEqual([p.get("text") for p in parts], ["CONTEXT TEXT", "IMAGES TEXT 1", None])
        blob = parts[2]["inlineData"]
        self.assertEqual(blob.get("mimeType") or blob.get("mime_type"), "application/pdf")
        self.assertEqual(base64.urlsafe_b64decode(blob["data"] + "=" * (-len(blob["data"]) % 4)), PDF_BYTES)
        details = result.pop("_details")
        self.assertEqual(result, GoodReply())
        self.assertEqual(details["tokens"], {"prompt": 10, "output": 5, "total": 15})

    def test_a_question_and_the_connection_test_on_the_wire(self):
        self.reply = lambda request: (200, self.Body("  She is basking.  "))
        self.assertEqual(ai.Answer("QUESTION PROMPT"), "She is basking.")
        self.assertIn("answered", ai.Ping())
        self.assertEqual(len(self.requests), 2)
        body = json.loads(self.requests[0].content)
        self.assertEqual(body["contents"], [{"parts": [{"text": "QUESTION PROMPT"}], "role": "user"}])
        self.assertNotIn("systemInstruction", body)
        self.assertEqual(body.get("generationConfig", {}), {})     # no JSON mode, no model settings
        self.assertEqual(self.requests[0].headers["x-server-timeout"], str(ai.QUICK_TIMEOUT_S))

    def test_thoughts_are_not_part_of_the_answer(self):
        body = self.Body("ignored")
        body["candidates"][0]["content"]["parts"] = [{"text": "let me think", "thought": True}, {"text": "Fine."}]
        self.reply = lambda request: (200, body)
        self.assertEqual(ai.Answer("q"), "Fine.")

    def test_a_cut_off_reply_is_refused_and_never_continued(self):
        for finish in ("MAX_TOKENS", "CONTINUATION"):
            self.requests.clear()
            # Cut off on the first request only: if the library were allowed to continue, a second request would follow.
            self.reply = lambda request: (200, self.Body('{"Weight": "heal', finish, continuationToken="dG9rZW4=")
                                          if len(self.requests) == 1 else self.Body('thy"}'))
            self.Fails(self.Analyze, "cut off", "shorter time range")
            self.assertEqual(len(self.requests), 1, finish)

    def test_blocked_and_empty_replies(self):
        self.reply = lambda request: (200, {"promptFeedback": {"blockReason": "PROHIBITED_CONTENT"}})
        self.Fails(self.Analyze, "declined", "PROHIBITED_CONTENT")
        self.reply = lambda request: (200, {"candidates": [{"finishReason": "SAFETY"}]})
        self.Fails(self.Analyze, "no usable answer", "SAFETY")
        self.reply = lambda request: (200, {})
        self.Fails(self.Analyze, "no usable answer")

    def test_http_errors_are_one_request_and_one_readable_sentence(self):
        cases = [(401, "UNAUTHENTICATED", "Request had invalid authentication credentials.", ["gcloud auth application-default login"]),
                 (403, "PERMISSION_DENIED", "Vertex AI API has not been used in project test-project before or it is disabled.",
                  ["Vertex AI API is enabled", "in project <project> before"]),
                 (404, "NOT_FOUND", "Publisher model was not found.", ["was not found at location 'global'", "REPTRACKER_MODEL"]),
                 (429, "RESOURCE_EXHAUSTED", "Quota exceeded.", ["quota", "error 429"]),
                 (400, "INVALID_ARGUMENT", "The document has too many pages.", ["error 400", "too many pages"]),
                 (503, "UNAVAILABLE", "The model is overloaded.", ["Google's side", "error 503"])]
        for code, status, message, words in cases:
            self.requests.clear()
            self.reply = lambda request: (code, {"error": {"code": code, "status": status, "message": message}})
            self.Fails(self.Analyze, *words)
            self.assertEqual(len(self.requests), 1, f"{code} must not be retried")
            if code == 401:
                self.assertIsNone(ai._client)             # the next call reads the login again
                self.setUp()

    def test_an_error_page_that_is_not_json(self):
        def Html(request):
            self.requests.append(request)
            return self.httpLib.Response(502, text="<html>\n<body>Bad Gateway</body>\n</html>")
        ai._client._api_client._httpx_client._transport = self.httpLib.MockTransport(Html)
        self.Fails(self.Analyze, "Google's side", "error 502")

    def test_timeout_and_no_network(self):
        self.reply = lambda request: self.httpLib.ReadTimeout("timed out", request=request)
        self.Fails(self.Analyze, f"within {ai.ANALYSIS_TIMEOUT_S} s")
        self.reply = lambda request: self.httpLib.ConnectError("getaddrinfo failed", request=request)
        self.Fails(self.Analyze, "Couldn't reach Google")
        self.assertEqual(len(self.requests), 2)           # one each: neither was retried

    def test_an_expired_sign_in(self):
        import google.auth.exceptions
        with mock.patch("google.genai._api_client.get_token_from_credentials",
                        side_effect=google.auth.exceptions.RefreshError("Reauthentication is needed.")):
            self.Fails(self.Analyze, "expired", "gcloud auth application-default login")
        self.assertEqual(self.requests, [])
        self.assertIsNone(ai._client)


# ---------- main.py: the provider switch around ai.py ----------

class MainTest(unittest.TestCase):
    def setUp(self):
        try:
            import main
        except ImportError as err:                        # Flask's other packages are not installed
            self.skipTest(f"main.py's packages are not installed ({err.name})")
        self.main = main
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        settings = mock.patch.object(main, "AI_SETTINGS", self.folder / "ai-settings.json")
        settings.start()
        self.addCleanup(settings.stop)

    def Ready(self, ready=True):
        return mock.patch.object(ai, "Status", return_value={"ready": ready, "detail": "why" if not ready else "set up"})

    def test_mock_is_the_default_and_both_providers_answer_both_kinds_of_request(self):
        self.assertEqual(self.main.CurrentProvider(), "mock")
        self.assertEqual(set(self.main.PROVIDERS), set(self.main.ASKERS))
        self.assertEqual(set(self.main.PROVIDERS), set(self.main.PROVIDER_LABELS))

    def test_gemini_can_only_be_chosen_when_it_is_ready(self):
        with self.Ready(False):
            with self.assertRaisesRegex(self.main.RepTrackerError, "not ready: why"):
                self.main.SetProvider("gemini")
            self.assertEqual(self.main.CurrentProvider(), "mock")
        with self.Ready(True):
            status = self.main.SetProvider("gemini")
            self.assertEqual(status["provider"], "gemini")
            self.assertEqual(self.main.CurrentProvider(), "gemini")
            self.assertEqual([p["ready"] for p in status["providers"]], [True, True])
            with self.assertRaises(self.main.RepTrackerError):
                self.main.SetProvider("chatgpt")
            self.assertEqual(self.main.SetProvider("mock")["provider"], "mock")

    def test_ai_errors_reach_the_dashboard_as_its_own_error_type(self):
        with mock.patch.object(ai, "Answer", side_effect=ai.AiError("readable message")):
            with self.assertRaisesRegex(self.main.RepTrackerError, "readable message"):
                self.main.GeminiAnswer("prompt", None, "")
        with mock.patch.object(ai, "Ping", side_effect=ai.AiError("no connection")), self.Ready(True):
            self.main.SetProvider("gemini")
            with self.assertRaisesRegex(self.main.RepTrackerError, "no connection"):
                self.main.TestProvider()

    def test_the_schema_given_to_gemini_is_the_bundles_or_the_current_one(self):
        with mock.patch.object(ai, "AnalyzeBundle", return_value={"ok": True}) as analyze:
            self.assertEqual(self.main.GeminiProvider(self.folder, {"schema": "missing.json"}, CONFIG), {"ok": True})
        self.assertEqual(analyze.call_args.args[3], SCHEMA)

    def SendWith(self, provider):
        manifest = {"range": {"start": "2026-11-12T00:00:00Z", "end": "2026-11-12T00:03:00Z"}}
        with mock.patch.object(self.main, "LoadBundle", return_value=(self.folder, manifest)), \
             mock.patch.object(self.main, "LoadConfig", return_value=CONFIG), \
             mock.patch.object(self.main, "LizardFolder", return_value=self.folder), \
             mock.patch.object(self.main, "CurrentProvider", return_value="gemini"), \
             mock.patch.dict(self.main.PROVIDERS, {"gemini": provider}):
            return self.main.SendPrompt("toy", "cheeto", "20261112-000000")

    def test_a_saved_analysis_keeps_the_details_but_a_provider_cannot_overwrite_the_entry(self):
        result = {**GoodReply(), "_details": {"model": "gemini-x", "seconds": 4.2, "tokens": {"total": 9}, "notes": ["n"],
                                              "bundleId": "evil", "provider": "evil", "range": "evil", "result": "evil"}}
        entry = self.SendWith(lambda folder, manifest, config: result)
        self.assertEqual(entry["bundleId"], "20261112-000000")
        self.assertEqual(entry["provider"], "gemini")
        self.assertEqual((entry["model"], entry["seconds"], entry["tokens"], entry["notes"]), ("gemini-x", 4.2, {"total": 9}, ["n"]))
        self.assertEqual(entry["range"]["start"], "2026-11-12T00:00:00Z")
        self.assertEqual(entry["result"], GoodReply())
        self.assertEqual(json.loads((self.folder / "analyses.json").read_text(encoding="utf-8")), [entry])

    def test_nothing_is_saved_when_the_provider_fails_and_mock_is_not_used_instead(self):
        def Failing(folder, manifest, config):
            raise self.main.RepTrackerError("Gemini is busy")
        with self.assertRaisesRegex(self.main.RepTrackerError, "Gemini is busy"):
            self.SendWith(Failing)
        self.assertFalse((self.folder / "analyses.json").exists())


if __name__ == "__main__":
    unittest.main()
