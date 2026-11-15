"""Claude (Anthropic API) as an AI provider for RepTracker.

main.py owns the prompts and the bundle format; this file only sends a bundle (or a question)
to Claude and forces the reply into the shape of prompts/response-schema.json. The reply
clean-up (ParseJson, NormalizeResult, FrameLabels) is shared with the Gemini provider in ai.py.

The API key comes from, in order:
    1. the key saved in Settings (dev mode), kept in data/claude-key.json (git-ignored, never sent to the page)
    2. the ANTHROPIC_API_KEY environment variable

The model is chosen in Settings (dev mode) from MODELS and kept in data/claude-settings.json
(git-ignored); without a choice, REPTRACKER_CLAUDE_MODEL, else "claude-opus-5-5".

One analysis is one request (max_retries=0), like the Gemini provider. Refusals are handled on
Anthropic's side by the server-side fallback ("fallbacks": "default"), which re-runs a declined
request on another Claude model inside the same call. Claude Haiku 5.5 has no server-side
fallback, so it is sent without one: a refusal there simply fails and nothing is saved.

The anthropic package is imported only when Claude is used. To check the key from a terminal:
    python claude_ai.py
"""
import base64
import importlib.util
import json
import logging
import math
import os
import re
import threading
import time
from pathlib import Path

from ai import AiError, FrameLabels, NormalizeResult, ParseJson

DEFAULT_MODEL = "claude-opus-5-5"
# The models offered in Settings, most capable first. Prices: Anthropic API list prices per million tokens.
MODELS = [
    {"id": "claude-opus-5-5", "label": "Claude Opus 5.5", "price": "$4 in / $20 out per million tokens",
     "note": "Most capable; the default.", "fallback": True},
    {"id": "claude-sonnet-5-5", "label": "Claude Sonnet 5.5", "price": "$2 in / $10 out per million tokens",
     "note": "Half the price of Opus.", "fallback": True},
    {"id": "claude-haiku-5-5", "label": "Claude Haiku 5.5", "price": "$0.10 in / $0.50 out per million tokens "
     "(prompts over 100K tokens: $0.50 / $2.50)", "note": "Cheapest. No refusal fallback.", "fallback": False},
]
FALLBACK_MODELS = {m["id"] for m in MODELS if m["fallback"]}
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_REQUEST_MB = 30          # the Messages API takes 32 MB per request; PDFs travel as base64
MAX_PDF_PAGES = 600          # pages across all PDFs in one request
ANALYSIS_TIMEOUT_S = 300
QUICK_TIMEOUT_S = 60
ANALYSIS_MAX_TOKENS = 16000
ANSWER_MAX_TOKENS = 4000
MAX_ANSWER_CHARS = 4000
KEY_FILE = Path(__file__).resolve().parent / "data" / "claude-key.json"
MODEL_FILE = Path(__file__).resolve().parent / "data" / "claude-settings.json"

log = logging.getLogger("reptracker.claude")
_lock = threading.RLock()
_client = None      # (key it was made with, client); tests put a fake client here through SetClient


# ---------- the API key ----------

def _SavedKey():
    try:
        return (json.loads(KEY_FILE.read_text(encoding="utf-8")).get("apiKey") or "").strip()
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return ""


def ApiKey():
    """(key, where it came from); ("", "") when there is none."""
    saved = _SavedKey()
    if saved:
        return saved, "Settings"
    env = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    return (env, "the ANTHROPIC_API_KEY environment variable") if env else ("", "")


def SaveKey(key):
    """Keep the key on this computer (data/claude-key.json, git-ignored). It is never sent back to the page."""
    key = str(key or "").strip()
    if not re.fullmatch(r"sk-ant-[A-Za-z0-9_\-]{20,}", key):
        raise AiError('That doesn\'t look like an Anthropic API key. Keys start with "sk-ant-"; '
                      "copy it again from the Claude Console (API keys page).")
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(json.dumps({"apiKey": key}), encoding="utf-8")
    Forget()


def RemoveKey():
    KEY_FILE.unlink(missing_ok=True)
    Forget()


def MaskKey(key):
    """Enough of a key to recognize it, not enough to use it."""
    return f"{key[:7]}…{key[-4:]}" if len(key) > 14 else "…"


def _SavedModel():
    try:
        model = json.loads(MODEL_FILE.read_text(encoding="utf-8")).get("model")
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return ""
    return model if model in {m["id"] for m in MODELS} else ""


def Settings():
    """The model to use: the one chosen in Settings, else REPTRACKER_CLAUDE_MODEL, else the default."""
    return {"model": _SavedModel() or os.environ.get("REPTRACKER_CLAUDE_MODEL") or DEFAULT_MODEL}


def SetModel(model):
    """Choose the Claude model for this computer (data/claude-settings.json, git-ignored)."""
    if model not in {m["id"] for m in MODELS}:
        raise AiError(f"Unknown Claude model. Choose one of: {', '.join(m['id'] for m in MODELS)}.")
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    MODEL_FILE.write_text(json.dumps({"model": model}), encoding="utf-8")


def _HasLibrary():
    try:
        return importlib.util.find_spec("anthropic") is not None
    except (ImportError, ValueError):
        return False


def Status():
    """Whether Claude is set up on this computer, checked without calling it: {"ready", "detail", "keySaved", "keyMask"}."""
    key, source = ApiKey()
    saved = bool(_SavedKey())
    base = {"keySaved": saved, "keyMask": MaskKey(key) if key else "", "model": Settings()["model"],
            "models": [{k: m[k] for k in ("id", "label", "price", "note")} for m in MODELS]}
    if not _HasLibrary():
        return {**base, "ready": False,
                "detail": 'Claude needs the anthropic package. In src/website run "pip install -r requirements.txt", then restart app.py.'}
    if not key:
        return {**base, "ready": False, "detail": "No API key yet. Paste an Anthropic API key below and save it."}
    return {**base, "ready": True,
            "detail": (f"Set up: model {Settings()['model']}, API key {MaskKey(key)} from {source}. "
                       "Test connection checks that Anthropic accepts it.")}


def Forget():
    """Drop the client, so the next call reads the key again."""
    global _client
    with _lock:
        _client = None


def SetClient(client):
    """For tests: use this client instead of a real one."""
    global _client
    with _lock:
        _client = ("test", client)


def GetClient():
    """The Anthropic client for the current key, created on first use. No network call happens here."""
    global _client
    with _lock:
        key, _ = ApiKey()
        if _client is not None and _client[0] in (key, "test"):
            return _client[1]
        if not _HasLibrary():
            raise AiError('Claude needs the anthropic package. In src/website run "pip install -r requirements.txt", then restart app.py.')
        if not key:
            raise AiError("No Anthropic API key is set. Add one in Settings (dev mode), under Claude.")
        import anthropic
        _client = (key, anthropic.Anthropic(api_key=key, max_retries=0))
        return _client[1]


# ---------- errors ----------

def _Is(err, *names):
    """True if err's class, or one it inherits from, has one of these names. Avoids importing the SDK."""
    return any(c.__name__ in names for c in type(err).__mro__)


def _Said(err):
    said = " ".join(str(getattr(err, "message", None) or "").split())
    key, _ = ApiKey()
    return (said.replace(key, MaskKey(key)) if key else said)[:300]


def Explain(err, timeoutS=ANALYSIS_TIMEOUT_S):
    """Any error from the anthropic library as an AiError a keeper can act on."""
    model = Settings()["model"]
    said = _Said(err)
    claudeSaid = f" Anthropic said: {said}" if said else ""
    if _Is(err, "AuthenticationError"):
        return AiError("Anthropic did not accept the API key (error 401). Check the key in Settings, or make a new one in the Claude Console.")
    if _Is(err, "PermissionDeniedError"):
        return AiError(f"This API key may not use model {model} (error 403).{claudeSaid}")
    if _Is(err, "NotFoundError"):
        return AiError(f"Model '{model}' was not found (error 404). Choose another model in Settings.")
    if _Is(err, "RequestTooLargeError"):
        return AiError("Anthropic says the request is too large (error 413). Generate prompts for a shorter time range.")
    if _Is(err, "RateLimitError"):
        return AiError("Claude is busy or this key's rate limit is used up (error 429). Wait a minute, then try again.")
    if _Is(err, "APITimeoutError"):
        return AiError(f"Claude did not answer within {timeoutS} s, so the request was stopped and nothing was saved. "
                       "Try again, or use a shorter time range.")
    if _Is(err, "APIConnectionError"):
        return AiError("Couldn't reach Anthropic. Check the internet connection, then try again.")
    if _Is(err, "BadRequestError"):
        return AiError(f"Claude did not accept the request (error 400).{claudeSaid}")
    if _Is(err, "APIStatusError"):
        code = getattr(err, "status_code", None)
        if isinstance(code, int) and code >= 500:
            return AiError(f"Claude had a problem on Anthropic's side (error {code}). Nothing was saved; try again in a moment.")
        return AiError(f"Claude did not accept the request (error {code}).{claudeSaid}")
    return AiError(f"Something unexpected went wrong while calling Claude ({type(err).__name__}). "
                   "The details are in the terminal that runs app.py.")


# ---------- requests (plain dicts, so they can be built and tested without the SDK) ----------

def _BundleFile(folder, name):
    path = folder / str(name)
    if not path.is_file():
        raise AiError(f"This prompt bundle is incomplete ({name} is missing). Generate the prompts again.")
    return path


def _PdfPages(data):
    """Page count of a PDF made by Pillow (counts its /Type /Page objects)."""
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", data))


def StructuredSchema(schema):
    """response-schema.json in the form structured outputs accept: no $schema or title keys,
    and a list of types ("number" or null) written as anyOf."""
    if isinstance(schema, list):
        return [StructuredSchema(s) for s in schema]
    if not isinstance(schema, dict):
        return schema
    out = {}
    for key, value in schema.items():
        if key in ("$schema", "title"):
            continue
        if key == "type" and isinstance(value, list):
            out["anyOf"] = [{"type": t} for t in value]
            continue
        out[key] = StructuredSchema(value)
    return out


def _Common(timeoutS, maxTokens):
    """What every request shares. The refusal fallback is sent only to models that accept it."""
    model = Settings()["model"]
    common = {"model": model, "max_tokens": maxTokens, "timeout": timeoutS}
    if model in FALLBACK_MODELS:
        common.update(betas=[FALLBACK_BETA], fallbacks="default")
    return common


def BuildAnalysisRequest(folder, manifest, schema):
    """The one request for one analysis, as keyword arguments for client.beta.messages.create.

    System: system.txt. One user turn: for each chunk, its PDF (if any) and then its text, in the
    bundle's order. The reply is constrained to the response schema (structured outputs).
    """
    system = _BundleFile(folder, manifest["system"])
    files = [(_BundleFile(folder, chunk["text"]), _BundleFile(folder, chunk["pdf"]) if chunk.get("pdf") else None)
             for chunk in manifest["chunks"]]
    size = system.stat().st_size + sum(text.stat().st_size + (4 * math.ceil(pdf.stat().st_size / 3) if pdf else 0)
                                       for text, pdf in files)
    if size > MAX_REQUEST_MB * 1024 * 1024:
        raise AiError(f"This time range makes a {size / 1024 / 1024:.0f} MB request, and Claude takes at most "
                      f"{MAX_REQUEST_MB} MB in one call. Generate prompts for a shorter range.")
    content, pages = [], 0
    for text, pdf in files:
        if pdf:
            data = pdf.read_bytes()
            pages += _PdfPages(data)
            content.append({"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                                           "data": base64.standard_b64encode(data).decode("ascii")}})
        content.append({"type": "text", "text": text.read_text(encoding="utf-8")})
    if pages > MAX_PDF_PAGES:
        raise AiError(f"This time range has {pages} images, and Claude reads at most {MAX_PDF_PAGES} PDF pages in one call. "
                      "Generate prompts for a shorter range.")
    return {
        **_Common(ANALYSIS_TIMEOUT_S, ANALYSIS_MAX_TOKENS),
        "system": system.read_text(encoding="utf-8"),
        "messages": [{"role": "user", "content": content}],
        "output_config": {"effort": "medium", "format": {"type": "json_schema", "schema": StructuredSchema(schema)}},
    }


def _Call(request):
    """The only place RepTracker talks to Claude: one request in, one response out, plus the seconds it took."""
    client = GetClient()
    started = time.monotonic()
    try:
        response = client.beta.messages.create(**request)
    except Exception as err:
        log.warning("Claude call failed: %s", type(err).__name__)
        if _Is(err, "AuthenticationError"):
            Forget()
        raise Explain(err, request.get("timeout", ANALYSIS_TIMEOUT_S)) from err
    return response, round(time.monotonic() - started, 1)


def ReadReply(response):
    """The text of Claude's reply, or an AiError that says why there is none (refused, cut off, empty)."""
    reason = getattr(response, "stop_reason", None)
    if reason == "refusal":
        details = getattr(response, "stop_details", None)
        category = getattr(details, "category", None)
        raise AiError(f"Claude declined this request{f' ({category})' if category else ''}, so nothing was saved.")
    if reason == "max_tokens":
        raise AiError("Claude's answer was cut off before it finished, so nothing was saved. Try a shorter time range.")
    text = "".join(getattr(b, "text", "") for b in (getattr(response, "content", None) or [])
                   if getattr(b, "type", None) == "text").strip()
    if not text:
        raise AiError("Claude returned no usable answer, so nothing was saved. Try again.")
    return text


def _Details(response, request, seconds, notes):
    """What the dashboard shows next to a result: model, seconds, tokens, and notes about repairs."""
    details = {"model": getattr(response, "model", None) or request["model"], "seconds": seconds}
    usage = getattr(response, "usage", None)
    if usage is not None and getattr(usage, "input_tokens", None) is not None:
        prompt, output = usage.input_tokens, getattr(usage, "output_tokens", 0) or 0
        details["tokens"] = {"prompt": prompt, "output": output, "total": prompt + output}
    if any(getattr(b, "type", None) == "fallback" for b in (getattr(response, "content", None) or [])):
        notes = notes + [f"{request['model']} declined; another Claude model answered instead (server-side fallback)."]
    if notes:
        details["notes"] = notes
    return details


def AnalyzeBundle(folder, manifest, config, schema):
    """Send one prompt bundle to Claude in one call; returns a dict shaped like response-schema.json,
    plus "_details" (model, seconds, tokens, notes) for the dashboard."""
    labels = FrameLabels(manifest)
    if not labels:
        raise AiError("This prompt bundle has no camera images, so there is nothing to analyze. Generate the prompts again.")
    GetClient()               # stop here, before the PDFs are read, if there is no key
    request = BuildAnalysisRequest(folder, manifest, schema)
    response, seconds = _Call(request)
    notes = []
    result = NormalizeResult(ParseJson(ReadReply(response)), schema, labels, config.get("enclosureWidthCm") or 100, notes)
    result["_details"] = _Details(response, request, seconds, notes)
    return result


def Answer(prompt, image=None):
    """Send a keeper's question (already filled into prompts/ask.txt) to Claude; returns the answer as text.

    image: JPEG bytes of the current camera picture (vision), sent before the question.
    """
    content = prompt
    if image:
        content = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                "data": base64.standard_b64encode(image).decode("ascii")}},
                   {"type": "text", "text": prompt}]
    request = {**_Common(QUICK_TIMEOUT_S, ANSWER_MAX_TOKENS), "output_config": {"effort": "low"},
               "messages": [{"role": "user", "content": content}]}
    response, _ = _Call(request)
    return ReadReply(response)[:MAX_ANSWER_CHARS]


def Ping():
    """One tiny request that proves the key and model work; returns a sentence."""
    request = {**_Common(QUICK_TIMEOUT_S, 1024), "output_config": {"effort": "low"},
               "messages": [{"role": "user", "content": "Reply with the single word: ready"}]}
    response, seconds = _Call(request)
    ReadReply(response)
    return f"Claude answered in {seconds} s (model {getattr(response, 'model', None) or request['model']})."


if __name__ == "__main__":    # python claude_ai.py: the connection check, without the dashboard
    status = Status()
    print(("Ready. " if status["ready"] else "Not ready. ") + status["detail"])
    if status["ready"]:
        try:
            print(Ping())
        except AiError as problem:
            print(f"The test request failed: {problem}")
