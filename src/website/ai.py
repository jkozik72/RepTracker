"""The real AI behind RepTracker: Google Gemini, called through Vertex AI.

main.py owns the prompts and the bundle format; this file only sends a bundle (or a
question) to Gemini and forces the reply into the shape of prompts/response-schema.json.

Nothing secret lives here and there is no API key. Authentication is the Google login
of the computer that runs the app (Application Default Credentials):

    gcloud auth application-default login
    gcloud auth application-default set-quota-project <project id>

Settings, all optional environment variables:
    GOOGLE_CLOUD_PROJECT    project to bill; default: the quota project of the login above
    GOOGLE_CLOUD_LOCATION   default "global"
    REPTRACKER_MODEL        default "gemini-3.8-flash"

google-genai is imported only when Gemini is used, so the Mock provider keeps working
without it.
"""
import json
import math
import os
import re

DEFAULT_LOCATION = "global"
DEFAULT_MODEL = "gemini-3.8-flash"
MAX_REQUEST_MB = 18            # inline attachments; larger requests are refused before sending
REQUEST_TIMEOUT_S = 180
MAX_ANALYSIS_CHARS = 2000

TRUE_WORDS = {"true", "yes", "y", "1"}


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
    """The option that matches value (ignoring case and surrounding spaces), else the last option.

    In response-schema.json the last option of every enum is its "can't tell" answer.
    """
    if isinstance(value, bool):
        value = "true" if value else "false"
    text = str(value).strip().lower() if value is not None else ""
    for option in options:
        if text == option.lower():
            return option
    return options[-1]


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
    return re.sub(r"\s+", " ", str(label or "")).strip().lower()


def NormalizeMovement(raw, frameLabels, widthCm):
    """One {"time", "position_cm"} per camera image, in the order the images were sent.

    Entries are matched to images by their timestamp label; if the labels don't match but
    the count does, they are matched by order. An image with no usable entry gets None.
    """
    entries = [e for e in raw if isinstance(e, dict)] if isinstance(raw, list) else []
    byLabel = {}
    for entry in entries:
        byLabel.setdefault(_LabelKey(entry.get("time")), entry)
    matched = sum(1 for label in frameLabels if _LabelKey(label) in byLabel)
    useOrder = matched == 0 and len(entries) == len(frameLabels)
    movement = []
    for i, label in enumerate(frameLabels):
        entry = entries[i] if useOrder else byLabel.get(_LabelKey(label))
        movement.append({"time": label, "position_cm": _Position(entry.get("position_cm"), widthCm) if entry else None})
    return movement


def NormalizeResult(raw, schema, frameLabels, widthCm):
    """Force the model's reply into the shape of response-schema.json.

    Unknown keys are dropped; a missing or off-list value becomes that field's "can't tell"
    option, False, or "none". Raises AiError if the reply is not a JSON object at all.
    """
    if not isinstance(raw, dict):
        raise AiError("The AI's answer was not in the expected format, so nothing was saved. Try sending again.")
    result = {}
    for key, spec in schema["properties"].items():
        value = raw.get(key)
        if "enum" in spec:
            result[key] = _Enum(value, spec["enum"])
        elif key == "Hazardous conditions":
            hazards = value if isinstance(value, dict) else {}
            result[key] = {}
            for name, sub in spec["properties"].items():
                if sub.get("type") == "boolean":
                    result[key][name] = _Bool(hazards.get(name))
                else:
                    result[key][name] = _Text(hazards.get(name), 300) or "none"
        elif key == "Movement Data":
            result[key] = NormalizeMovement(value, frameLabels, widthCm)
        else:
            result[key] = _Text(value, MAX_ANALYSIS_CHARS)
    if not result.get("Analysis"):
        result["Analysis"] = "The AI returned no written summary for this range."
    return result


def FrameLabels(manifest):
    """Timestamp labels of every camera image in a bundle, in the order they are sent."""
    return [frame["label"] for chunk in manifest["chunks"] for frame in chunk.get("frames", [])]


# ---------- calling Gemini ----------
# Work in progress: the request code is being written. Until then Gemini reports "not ready",
# so the dashboard stays on the Mock provider.

def Status():
    return {"ready": False, "detail": "The Gemini connection is not finished yet."}


def AnalyzeBundle(folder, manifest, config, schema):
    raise AiError("The Gemini connection is not finished yet.")


def Answer(prompt):
    raise AiError("The Gemini connection is not finished yet.")


def Ping():
    raise AiError("The Gemini connection is not finished yet.")
