"""Gemini access for RepTracker, through Vertex AI (Agent Platform).

Nothing secret lives here. Authentication comes from the Google login on the
machine that runs the app:

    gcloud auth application-default login
    gcloud auth application-default set-quota-project <project id>

Set GOOGLE_CLOUD_PROJECT to use a different project than the default below.
"""

import json
import mimetypes
import os
from pathlib import Path

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "project-199a0511-ef62-43de-851")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
MODEL = os.environ.get("REPTRACKER_MODEL", "gemini-3.8-flash")

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGES = 8  # newest images sent per call; keeps one call small and cheap

_client = None


def GetClient():
    """Create the Gemini client on first use, so importing this file needs no login."""
    global _client
    if _client is None:
        from google import genai

        _client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    return _client


def CollectMedia(path):
    """Return the files to send for `path`: a PDF, one image, or a folder of images.

    From a folder, the newest MAX_IMAGES images are returned, oldest first.
    """
    path = Path(path)
    if path.is_dir():
        images = [p for p in path.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES]
        images.sort(key=lambda p: (p.stat().st_mtime, p.name))
        return images[-MAX_IMAGES:]
    if path.is_file() and (path.suffix.lower() in IMAGE_SUFFIXES or path.suffix.lower() == ".pdf"):
        return [path]
    return []


def BuildPrompt(promptTemplate, species, schema, options, research):
    """Assemble the text part of the request from the prompt template and the schema."""
    lines = [
        promptTemplate.replace("{species}", species).strip(),
        "",
        "JSON schema to fill out (keep every key exactly as written):",
        json.dumps(schema, indent=2),
        "",
        "Allowed values:",
    ]
    for key, allowed in options.items():
        lines.append(f'- "{key}": one of {json.dumps(allowed)}')
    lines += [
        "- Temperatures are in degrees F and humidity in percent. Use null unless a",
        "  thermometer or hygrometer reading is clearly visible in the images.",
        "- Booleans under \"Hazardous conditions\" are true only if the images or readings show it.",
        "",
        f"Ideal conditions for {species}:",
        research.strip() or "(no research available yet; judge from the images alone)",
    ]
    return "\n".join(lines)


def ParseJson(text):
    """Parse the model's reply as JSON, tolerating a Markdown code fence around it."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


def NormalizeReport(raw, schema, options):
    """Force a model reply into the shape of `schema`.

    Unknown keys are dropped and missing keys get the schema's default. A value
    outside its allowed options becomes the "can't see lizard" option if the field
    has one, otherwise the schema's default.
    """
    report = {}
    for key, default in schema.items():
        value = raw.get(key, default) if isinstance(raw, dict) else default
        if isinstance(default, dict):
            report[key] = NormalizeReport(value, default, options)
        elif key in options:
            allowed = options[key]
            match = next((a for a in allowed if str(value).strip().lower() == a.lower()), None)
            if match is None:
                match = allowed[-1] if allowed[-1].startswith("can't") else default
            report[key] = match
        else:
            report[key] = value
    return report


def AnalyzeEnclosure(mediaPaths, species, research, schema, options, promptTemplate):
    """Send the images and research to Gemini in one call and return the filled-out schema."""
    from google.genai import types

    parts = []
    for path in mediaPaths:
        mimeType = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        parts.append(types.Part.from_bytes(data=Path(path).read_bytes(), mime_type=mimeType))
    parts.append(types.Part.from_text(text=BuildPrompt(promptTemplate, species, schema, options, research)))

    response = GetClient().models.generate_content(
        model=MODEL,
        contents=parts,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0),
    )
    return NormalizeReport(ParseJson(response.text), schema, options)
