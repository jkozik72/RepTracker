"""The real AI behind RepTracker: Google Gemini, called through Vertex AI.

main.py owns the prompts and the bundle format; this file only sends a bundle (or a
question) to Gemini and forces the reply into the shape of prompts/response-schema.json.

Nothing secret lives here and there is no API key. Authentication is the Google login
of the computer that runs the app (Application Default Credentials):

    gcloud auth application-default login
    gcloud auth application-default set-quota-project <project id>

Settings, all optional environment variables:
    GOOGLE_CLOUD_PROJECT    project to use; default: the quota project of the login above
    GOOGLE_CLOUD_LOCATION   default "global"
    REPTRACKER_MODEL        default "gemini-3.8-flash"

One analysis is one HTTPS request: no retries and no follow-up requests.

google-genai is imported only when Gemini is used, so the Mock provider keeps working
without it. To check the connection from a terminal:   python ai.py
"""
import importlib.util
import json
import logging
import math
import os
import re
import threading
import time

DEFAULT_LOCATION = "global"    # the default model answered 404 from us-central1
DEFAULT_MODEL = "gemini-3.8-flash"
MAX_REQUEST_MB = 18            # size of one request as sent (PDFs travel as base64). Our own cautious limit:
                               # the library states none, and Google's real limit has not been tested.
ANALYSIS_TIMEOUT_S = 300       # one analysis. A guess until real calls are timed.
QUICK_TIMEOUT_S = 60           # a question, or the connection test
MAX_ANALYSIS_CHARS = 2000
MAX_ANSWER_CHARS = 4000
CLOUD_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

TRUE_WORDS = {"true", "yes", "y", "1"}
# Every way of writing "nothing to report" in a free-text hazard field. Anything else is shown as an alert.
NONE_LIKE = re.compile(
    r"^(none|nothing|nil|null|false|no|n/?a|not applicable"
    r"|no (visible |obvious |apparent |clear |other |additional )*"
    r"(signs?( of (disease|illness|sickness))?|disease|illness|hazards?|issues?|concerns?|problems?))"
    r"( (was |were |is |are )?(observed|visible|seen|noted|detected|apparent|identified|reported|found|present))?$")

log = logging.getLogger("reptracker.ai")


class AiError(Exception):
    """A problem with the AI call, with a message that is safe to show on the dashboard."""


# ---------- forcing a reply into the schema (no network, no SDK) ----------

def ParseJson(text):
    """The model's reply as a Python object; tolerates a Markdown code fence around the JSON."""
    text = (text or "").strip()
    fence = re.match(r"^```[a-zA-Z]*\s*\n(.*?)\n?```\s*$", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, RecursionError):
        raise AiError("The AI's answer was not valid JSON, so nothing was saved. Try sending again.")


def _Enum(value, options):
    """The option that matches value (ignoring case and surrounding spaces), or None."""
    if isinstance(value, bool):
        value = "true" if value else "false"
    text = str(value).strip().lower() if value is not None else ""
    return next((option for option in options if text == option.lower()), None)


def _Bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    return str(value).strip().lower() in TRUE_WORDS if value is not None else False


def _Text(value, limit):
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()[:limit]


def _HazardText(value):
    """A free-text hazard; "none" for every way of saying there is nothing to report ("None observed.", "N/A")."""
    text = _Text(value, 300)
    plain = re.sub(r"\s+", " ", text.lower()).strip(" .!")
    return "none" if not plain or NONE_LIKE.match(plain) else text


def _Position(value, widthCm):
    """cm from the left wall, clamped to the enclosure; None when missing or not a number."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return round(min(max(number, 0.0), float(widthCm)), 1)


def _LabelKey(label):
    """What two timestamps must share to be the same image: date, hour and minute.

    "2026-11-12 00:05 UTC", "2026-11-12T00:05:00Z" and " 2026-11-12  00:05 utc" all give the same key.
    """
    text = re.sub(r"\s+", " ", str(label or "")).strip().lower()
    stamp = re.search(r"(\d{4})-(\d\d)-(\d\d)[ t](\d\d):(\d\d)", text)
    return "".join(stamp.groups()) if stamp else text


def NormalizeMovement(raw, frameLabels, widthCm, notes=None):
    """One {"time", "position_cm"} per camera image, in the order the images were sent.

    Entries are matched to images by their timestamp. If there is exactly one entry per image
    but the timestamps don't all match, they are matched by order instead. An image with no
    usable entry gets None. Anything that had to be repaired is described in notes (a list).
    """
    notes = [] if notes is None else notes
    entries = [e for e in raw if isinstance(e, dict)] if isinstance(raw, list) else []
    byLabel = {}
    for entry in entries:
        byLabel.setdefault(_LabelKey(entry.get("time")), entry)
    matched = sum(1 for label in frameLabels if _LabelKey(label) in byLabel)
    useOrder = len(entries) == len(frameLabels) and matched < len(frameLabels)
    if useOrder:
        notes.append("The AI's timestamps did not all match the images, so its positions were matched to the images by order.")
    elif matched < len(frameLabels):
        notes.append(f"The AI returned {len(entries)} position(s) for {len(frameLabels)} images; "
                     f"{len(frameLabels) - matched} image(s) had no matching entry and have no position.")
    movement = []
    for i, label in enumerate(frameLabels):
        entry = entries[i] if useOrder else byLabel.get(_LabelKey(label))
        movement.append({"time": label, "position_cm": _Position(entry.get("position_cm"), widthCm) if entry else None})
    return movement


def NormalizeResult(raw, schema, frameLabels, widthCm, notes=None):
    """Force the model's reply into the shape of response-schema.json.

    Unknown keys are dropped; a missing or off-list value becomes that field's "can't tell"
    option (the last one of its enum), False, or "none". Anything that had to be repaired is
    described in notes (a list). Raises AiError if the reply is not a JSON object with at
    least one of the schema's fields.
    """
    notes = [] if notes is None else notes
    if not isinstance(raw, dict) or not any(key in raw for key in schema["properties"]):
        raise AiError("The AI's answer was not in the expected format, so nothing was saved. Try sending again.")
    result, unknown = {}, []
    for key, spec in schema["properties"].items():
        value = raw.get(key)
        if "enum" in spec:
            option = _Enum(value, spec["enum"])
            if option is None:
                unknown.append(key)
            result[key] = option or spec["enum"][-1]
        elif key == "Hazardous conditions":
            hazards = value if isinstance(value, dict) else {}
            if not hazards:
                unknown.append(key)
            result[key] = {}
            for name, sub in spec["properties"].items():
                result[key][name] = _Bool(hazards.get(name)) if sub.get("type") == "boolean" else _HazardText(hazards.get(name))
        elif key == "Movement Data":
            result[key] = NormalizeMovement(value, frameLabels, widthCm, notes)
        else:
            result[key] = _Text(value, MAX_ANALYSIS_CHARS)
    if unknown:
        notes.append("The AI left these out or gave an answer that is not on the list, so they show as unknown: "
                     + ", ".join(unknown) + ".")
    if not result.get("Analysis"):
        result["Analysis"] = "The AI returned no written summary for this range."
    return result


def FrameLabels(manifest):
    """Timestamp labels of every camera image in a bundle, in the order they are sent."""
    return [frame["label"] for chunk in manifest["chunks"] for frame in chunk.get("frames", [])]


# ---------- this computer's Google login ----------

_lock = threading.RLock()
_login = None     # (credentials, project, where the project came from), kept once the login is found
_client = None    # the google-genai client, made on first use; tests put a fake here


def Settings():
    """Which model and location to use, read from the environment on every call."""
    return {"model": os.environ.get("REPTRACKER_MODEL") or DEFAULT_MODEL,
            "location": os.environ.get("GOOGLE_CLOUD_LOCATION") or DEFAULT_LOCATION}


def Forget():
    """Drop the remembered login and client, so the next call reads the Google login from disk again."""
    global _login, _client
    with _lock:
        _login = _client = None


def _HasLibrary():
    try:
        return importlib.util.find_spec("google.genai") is not None
    except (ImportError, ValueError):
        return False


def Login():
    """This computer's Google login and the project to use: (credentials, project, source).

    The project is GOOGLE_CLOUD_PROJECT if set, else the quota project stored with the login
    (gcloud auth application-default set-quota-project), else gcloud's default project.
    No network call happens here. Raises AiError that says which command fixes it.
    """
    global _login
    with _lock:
        if _login is not None:
            return _login
        missing = AiError('Gemini needs the google-genai package. In src/website run '
                          '"pip install -r requirements.txt", then restart app.py.')
        if not _HasLibrary():
            raise missing
        try:
            import google.auth
            from google.auth.exceptions import DefaultCredentialsError
        except ImportError:
            raise missing
        # RepTracker runs on a laptop, never on Google's own servers. Without this, a computer that is
        # not signed in waits several seconds for a Google Cloud metadata server that is not there.
        os.environ.setdefault("NO_GCE_CHECK", "true")
        try:
            credentials, gcloudProject = google.auth.default(scopes=[CLOUD_SCOPE])
        except DefaultCredentialsError:
            raise AiError('This computer is not signed in to Google Cloud. In a terminal run '
                          '"gcloud auth application-default login", then try again.')
        candidates = ((os.environ.get("GOOGLE_CLOUD_PROJECT"), "GOOGLE_CLOUD_PROJECT"),
                      (getattr(credentials, "quota_project_id", None), "the Google login's quota project"),
                      (gcloudProject, "gcloud's default project"))
        found = next(((project, source) for project, source in candidates if project), None)
        if found is None:
            raise AiError('Signed in to Google, but no Google Cloud project is set. In a terminal run '
                          '"gcloud auth application-default set-quota-project <project id>", then try again.')
        _login = (credentials, *found)
        return _login


def _Mask(project):
    """A project ID short enough to show on a screen other people can see."""
    return project if len(project) <= 8 else f"{project[:4]}…{project[-3:]}"


def Status():
    """Whether Gemini is set up on this computer, checked without calling it: {"ready", "detail"}."""
    settings = Settings()
    try:
        _, project, source = Login()
    except AiError as err:
        return {"ready": False, "detail": str(err)}
    except Exception as err:   # the status line must never break the page
        log.warning("Could not read the Google login: %r", err)
        return {"ready": False, "detail": f"Couldn't read this computer's Google login ({type(err).__name__})."}
    return {"ready": True,
            "detail": (f"Set up: model {settings['model']}, location {settings['location']}, project {_Mask(project)} "
                       f"(from {source}). Signs in with this computer's Google login; there is no API key. "
                       "Test connection checks that Google accepts it.")}


def GetClient():
    """The google-genai client for this computer, created on first use. No network call happens here."""
    global _client
    with _lock:
        if _client is None:
            credentials, project, _ = Login()
            try:
                from google import genai
                # project, location and credentials are all passed on purpose: without them the library
                # looks for an API key or another project in the environment.
                _client = genai.Client(vertexai=True, project=project, location=Settings()["location"],
                                       credentials=credentials)
            except Exception as err:
                log.warning("Could not create the Gemini client: %r", err)
                raise Explain(err) from err
        return _client


# ---------- calling Gemini ----------
# Flow of one analysis:  BuildAnalysisRequest (files -> request, pure)  ->  _Call (the only network
# line)  ->  ReadReply (response -> text, pure)  ->  ParseJson  ->  NormalizeResult (above, pure).
# Requests are plain dicts, so they can be built, printed and tested without google-genai.

def _Is(err, *names):
    """True if err's class, or one it inherits from, has one of these names. Avoids importing the SDK."""
    return any(c.__name__ in names for c in type(err).__mro__)


def _Said(err):
    """Google's own error message on one line, without the project ID; "" if there is none."""
    said = " ".join(str(getattr(err, "message", None) or "").split())
    if _login:
        said = said.replace(_login[1], "<project>")
    return said[:300]


def Explain(err, timeoutS=ANALYSIS_TIMEOUT_S):
    """Any error from the Google libraries as an AiError a keeper can act on."""
    settings = Settings()
    signIn = 'In a terminal run "gcloud auth application-default login", then try again.'
    slow = (f"Gemini did not answer within {timeoutS} s, so the request was stopped and nothing was saved. "
            "Try again, or use a shorter time range.")
    if _Is(err, "APIError"):                      # google.genai.errors: Google answered with an HTTP error
        code, said = getattr(err, "code", None), _Said(err)
        googleSaid = f" Google said: {said}" if said else ""
        if code == 401:
            return AiError(f"Google did not accept this computer's sign-in (error 401). {signIn}")
        if code == 403:
            return AiError("Google refused the request (error 403). Check that the Vertex AI API is enabled in the "
                           f"project and that your Google account may use it.{googleSaid}")
        if code == 404:
            return AiError(f"Model '{settings['model']}' was not found at location '{settings['location']}' (error 404). "
                           "Check REPTRACKER_MODEL and GOOGLE_CLOUD_LOCATION; some models are only served from location 'global'.")
        if code in (408, 504):
            return AiError(slow)
        if code == 413:
            return AiError("Google says the request is too large (error 413). Generate prompts for a shorter time range.")
        if code == 429:
            return AiError("Gemini is busy or this project's quota is used up (error 429). Wait a minute, then try again.")
        if isinstance(code, int) and code >= 500:
            return AiError(f"Gemini had a problem on Google's side (error {code}). Nothing was saved; try again in a moment.")
        return AiError(f"Gemini did not accept the request (error {code}).{googleSaid}")
    if _Is(err, "RefreshError"):                  # google.auth: the saved login no longer works
        return AiError(f"The Google sign-in on this computer has expired. {signIn}")
    if _Is(err, "DefaultCredentialsError"):
        return AiError(f"This computer is not signed in to Google Cloud. {signIn}")
    if _Is(err, "TimeoutException", "TimeoutError", "Timeout"):
        return AiError(slow)
    if _Is(err, "TransportError", "NetworkError", "ConnectError", "ConnectionError"):
        return AiError("Couldn't reach Google. Check the internet connection, then try again.")
    if _Is(err, "GoogleAuthError"):
        return AiError(f"Google sign-in failed ({type(err).__name__}). {signIn}")
    return AiError(f"Something unexpected went wrong while calling Gemini ({type(err).__name__}). "
                   "The details are in the terminal that runs app.py.")


def _Call(request):
    """The only place RepTracker talks to Gemini: one request in, one response out, plus the seconds it took."""
    client = GetClient()      # kept in a variable for the whole call: the library closes a client nobody holds
    timeoutS = request["config"]["http_options"]["timeout"] // 1000
    started = time.monotonic()
    try:
        response = client.models.generate_content(**request)
    except Exception as err:
        log.warning("Gemini call failed: %r", err)
        if _Is(err, "GoogleAuthError") or getattr(err, "code", None) == 401:
            Forget()          # after a new "gcloud auth application-default login" the next call picks up the new login
        raise Explain(err, timeoutS) from err
    return response, round(time.monotonic() - started, 1)


def _Name(value):
    return str(getattr(value, "name", None) or value or "")


def ReadReply(response):
    """The text of Gemini's reply, or an AiError that says why there is none (blocked, cut off, empty)."""
    blocked = getattr(getattr(response, "prompt_feedback", None), "block_reason", None)
    if blocked:
        raise AiError(f"Gemini declined this request ({_Name(blocked)}), so nothing was saved.")
    candidates = getattr(response, "candidates", None) or []
    reason = _Name(getattr(candidates[0], "finish_reason", None)) if candidates else ""
    if reason in ("MAX_TOKENS", "CONTINUATION"):
        raise AiError("Gemini's answer was cut off before it finished, so nothing was saved. Try a shorter time range.")
    text = (getattr(response, "text", None) or "").strip()
    if not text or reason not in ("", "STOP"):
        why = f" (reason: {reason})" if reason not in ("", "STOP") else ""
        raise AiError(f"Gemini returned no usable answer{why}, so nothing was saved. Try again.")
    return text


def _Options(timeoutS):
    """What every request shares: one HTTP call only (no hidden follow-up requests) and a time limit in ms."""
    return {"automatic_continuation": False, "http_options": {"timeout": timeoutS * 1000}}


def _BundleFile(folder, name):
    path = folder / str(name)
    if not path.is_file():
        raise AiError(f"This prompt bundle is incomplete ({name} is missing). Generate the prompts again.")
    return path


def BuildAnalysisRequest(folder, manifest):
    """The one request for one analysis, as plain data.

    System instruction: system.txt. One user turn: context.txt, then for each IMAGES chunk its
    images-NN.txt followed by images-NN.pdf. The reply must be JSON. Raises AiError if a file is
    missing or the request would be larger than MAX_REQUEST_MB.
    """
    system = _BundleFile(folder, manifest["system"])
    files = [(_BundleFile(folder, chunk["text"]), _BundleFile(folder, chunk["pdf"]) if chunk.get("pdf") else None)
             for chunk in manifest["chunks"]]
    size = system.stat().st_size + sum(text.stat().st_size + (4 * math.ceil(pdf.stat().st_size / 3) if pdf else 0)
                                       for text, pdf in files)      # a PDF is sent as base64: 4 bytes for every 3
    if size > MAX_REQUEST_MB * 1024 * 1024:
        raise AiError(f"This time range makes a {size / 1024 / 1024:.0f} MB request, and RepTracker sends at most "
                      f"{MAX_REQUEST_MB} MB in one AI call. Generate prompts for a shorter range.")
    parts = []
    for text, pdf in files:
        parts.append({"text": text.read_text(encoding="utf-8")})
        if pdf:
            parts.append({"inline_data": {"mime_type": "application/pdf", "data": pdf.read_bytes()}})
    return {
        "model": Settings()["model"],
        "contents": [{"role": "user", "parts": parts}],
        "config": {"system_instruction": system.read_text(encoding="utf-8"),
                   "response_mime_type": "application/json", **_Options(ANALYSIS_TIMEOUT_S)},
    }


def _Details(response, request, seconds, notes):
    """What the dashboard shows next to a result: model, seconds, tokens, and notes about repairs."""
    details = {"model": request["model"], "seconds": seconds}
    usage = getattr(response, "usage_metadata", None)
    if getattr(usage, "total_token_count", None) is not None:
        details["tokens"] = {"prompt": getattr(usage, "prompt_token_count", None),
                             "output": getattr(usage, "candidates_token_count", None),
                             "total": usage.total_token_count}
    if notes:
        details["notes"] = notes
    return details


def AnalyzeBundle(folder, manifest, config, schema):
    """Send one prompt bundle to Gemini in one call; returns a dict shaped like response-schema.json.

    The extra "_details" key (model, seconds, tokens, notes) is for the dashboard, not part of the schema.
    """
    labels = FrameLabels(manifest)
    if not labels:
        raise AiError("This prompt bundle has no camera images, so there is nothing to analyze. Generate the prompts again.")
    GetClient()               # first: stop here, before the PDFs are read, if this computer is not set up
    request = BuildAnalysisRequest(folder, manifest)
    response, seconds = _Call(request)
    notes = []
    result = NormalizeResult(ParseJson(ReadReply(response)), schema, labels, config["enclosureWidthCm"], notes)
    result["_details"] = _Details(response, request, seconds, notes)
    return result


def Answer(prompt):
    """Send a keeper's question (already filled into prompts/ask.txt) to Gemini; returns the answer as text."""
    request = {"model": Settings()["model"], "contents": prompt, "config": _Options(QUICK_TIMEOUT_S)}
    response, _ = _Call(request)
    return ReadReply(response)[:MAX_ANSWER_CHARS]


def Ping():
    """One tiny request that proves the login, project, location and model all work; returns a sentence."""
    settings = Settings()
    request = {"model": settings["model"], "contents": "Reply with the single word: ready", "config": _Options(QUICK_TIMEOUT_S)}
    response, seconds = _Call(request)
    ReadReply(response)
    return f"Gemini answered in {seconds} s (model {settings['model']}, location {settings['location']})."


if __name__ == "__main__":    # python ai.py: the connection check, without the dashboard
    status = Status()
    print(("Ready. " if status["ready"] else "Not ready. ") + status["detail"])
    if status["ready"]:
        try:
            print(Ping())
        except AiError as problem:
            print(f"The test request failed: {problem}")
