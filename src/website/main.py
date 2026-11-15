"""RepTracker core: lizard configs, simulated camera and sensors, prompt bundles, AI providers.

There are no real cameras or sensors. A camera is a video in media/videos/ and a sensor is a
JSON time series in media/sensors/: {"t": <ms between samples>, "value": [samples...]}.
Both start at the lizard's createdAt time and loop when they run out.

Two separate data sets, each under data/<mode>/:
- toy:  sample lizards, videos and sensors, for trying things out
- main: starts empty; the keeper adds media and lizards

Times are ISO 8601 strings in UTC ("2026-11-14T10:00:00Z").
"""
import base64
import bisect
import io
import json
import math
import re
import shutil
import statistics
import subprocess
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

import ai
import claude_ai
import research

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DEFAULT_SENSORS = DATA / "defaults" / "sensors"   # shared by every mode, committed, never overwritten
PROMPTS = ROOT / "prompts"
RESEARCH = ROOT / "research"
AI_SETTINGS = DATA / "ai-settings.json"   # which AI provider this computer uses (git-ignored)

MODES = ["toy", "main"]
CAMERA_VIEWS = ["top", "side"]
SIDES = ["left", "right"]
TEMP_UNITS = ["F", "C"]
HUMIDITY_UNITS = ["%RH", "g/m3"]
IMAGES_PER_CHUNK = 60          # 1 image per minute -> one PDF per hour of range
MAX_RANGE_MIN = 6 * 60         # keeps a request to 6 PDFs / 360 pages


class RepTrackerError(Exception):
    """An error whose message is safe to show on the dashboard."""


# ---------- paths per mode ----------

def ModeRoot(mode):
    if mode not in MODES:
        raise RepTrackerError(f"Unknown mode '{mode}'.")
    return DATA / mode


def VideosDir(mode):
    return ModeRoot(mode) / "media" / "videos"


def SensorsDir(mode):
    return ModeRoot(mode) / "media" / "sensors"


def ReptilesDir(mode):
    return ModeRoot(mode) / "reptiles"


def IndexPath(mode):
    return ModeRoot(mode) / "reptiles.json"


# ---------- time ----------

def ParseTime(value):
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        raise RepTrackerError(f"Not a valid time: {value}")
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def FormatTime(t):
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def SourceOffsetSeconds(config, t):
    """Seconds since the lizard's camera and sensors started, or None before that."""
    offset = (t - ParseTime(config["createdAt"])).total_seconds()
    return offset if offset >= 0 else None


# ---------- files ----------

def ReadJson(path, fallback):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def WriteJson(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def DefaultSensorNames():
    return sorted(p.stem for p in DEFAULT_SENSORS.glob("*.json"))


SAMPLE_VIDEOS = {"toy": {"gecko-top", "skink-side", "short-clip-top"}}   # committed samples (tools/make_samples.py)


def ListMedia(mode):
    """Names (without extension) of the videos and sensor series available in this mode.

    Sensors are this mode's uploads plus the shared defaults in data/defaults/sensors/.
    """
    defaults = DefaultSensorNames()
    return {
        "videos": sorted(p.stem for p in VideosDir(mode).glob("*.mp4")),
        "sensors": sorted(set(defaults) | {p.stem for p in SensorsDir(mode).glob("*.json")}),
        "defaultSensors": defaults,
        "sampleVideos": sorted(SAMPLE_VIDEOS.get(mode, set())),
    }


def DeleteVideo(mode, name):
    """Delete an uploaded camera video from this mode's media folder, for good.

    Refused for the committed sample videos, and for a video a lizard on the dashboard still uses.
    """
    if not re.fullmatch(r"[a-z0-9-]+", name or ""):
        raise RepTrackerError("Unknown video.")
    path = VideosDir(mode) / f"{name}.mp4"
    if not path.exists():
        raise RepTrackerError(f"There is no video '{name}' in {mode} mode.")
    if name in SAMPLE_VIDEOS.get(mode, set()):
        raise RepTrackerError(f"'{name}' is a sample video that comes with the app; it can't be deleted.")
    users = [l["config"]["name"] for l in ListLizards(mode) if l["config"]["camera"]["video"] == name]
    if users:
        raise RepTrackerError(f"'{name}' is the camera of {', '.join(users)}. Remove "
                              f"{'that lizard' if len(users) == 1 else 'those lizards'} first, then delete the video.")
    path.unlink()
    VideoDurationSeconds.cache_clear()
    return ListMedia(mode)


def SensorPath(mode, name):
    """Where a sensor series lives: this mode's uploads first, then the shared defaults."""
    for folder in (SensorsDir(mode), DEFAULT_SENSORS):
        path = folder / f"{name}.json"
        if path.exists():
            return path
    raise RepTrackerError(f"Sensor series '{name}' not found.")


def MediaName(fileName):
    """A safe file stem from an uploaded file name: lowercase letters, digits and hyphens."""
    stem = re.sub(r"[^a-z0-9]+", "-", Path(fileName or "").stem.lower()).strip("-")
    if not stem:
        raise RepTrackerError("The file needs a name made of letters or digits.")
    return stem[:60]


MAX_SENSOR_BYTES = 50 * 1024 * 1024


def SaveUpload(mode, kind, upload):
    """Save an uploaded camera video (.mp4) or sensor series (.json) into this mode's media folder.

    upload is the request's file (has .filename, .save(path) and .read()). Videos are streamed
    to disk, so multi-GB files never sit in memory.
    """
    fileName = upload.filename or ""
    name = MediaName(fileName)
    if kind == "videos":
        if not fileName.lower().endswith(".mp4"):
            raise RepTrackerError("Videos must be .mp4 files.")
        path = VideosDir(mode) / f"{name}.mp4"
    elif kind == "sensors":
        if not fileName.lower().endswith(".json"):
            raise RepTrackerError("Sensor data must be a .json file.")
        if name in DefaultSensorNames():
            raise RepTrackerError(f"'{name}' is a default sensor file; rename yours to upload it.")
        data = upload.read(MAX_SENSOR_BYTES + 1)
        if len(data) > MAX_SENSOR_BYTES:
            raise RepTrackerError("Sensor files are limited to 50 MB.")
        try:
            series = json.loads(data.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            raise RepTrackerError(f"Not valid JSON: {err}")
        CheckSeries(series)
        path = SensorsDir(mode) / f"{name}.json"
    else:
        raise RepTrackerError("Upload a video or a sensor file.")
    if path.exists():
        raise RepTrackerError(f"'{path.name}' already exists in {mode} mode; rename the file to upload it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind == "videos":
        upload.save(str(path))
    else:
        path.write_bytes(data)
    if kind == "videos":
        try:
            if VideoDurationSeconds(mode, name) <= 0:
                raise ValueError
        except Exception:
            path.unlink(missing_ok=True)
            VideoDurationSeconds.cache_clear()
            raise RepTrackerError("Couldn't read that video. Upload an .mp4 that plays.")
    return {"kind": kind, "name": name}


def LizardFolder(mode, lizardId):
    if not re.fullmatch(r"[a-z0-9-]+", lizardId or ""):
        raise RepTrackerError("Unknown lizard.")
    return ReptilesDir(mode) / lizardId


def LoadConfig(mode, lizardId):
    config = ReadJson(LizardFolder(mode, lizardId) / "config.json", None)
    if config is None:
        raise RepTrackerError("Unknown lizard.")
    return config


def ProfileBrief(species):
    """What the dashboard needs from a species profile: its name and the ranges for sensor alerts."""
    record = research.FindRecord(species)
    if not record:
        return None
    p = record["profile"]
    return {"slug": record["slug"], "commonName": p["commonName"], "temperaturesF": p["temperaturesF"],
            "humidityPercent": p["humidityPercent"],
            "trackedStats": [{k: s[k] for k in ("id", "label", "options", "concernOptions")} for s in p.get("trackedStats", [])],
            "conditions": {c["name"]: c["urgency"] for c in p.get("conditions", [])}}


def ListLizards(mode):
    """Every lizard in this mode's reptiles.json with its config and latest analysis."""
    lizards = []
    for entry in ReadJson(IndexPath(mode), []):
        lizardId = Path(entry["folder path"]).name
        folder = ReptilesDir(mode) / lizardId
        config = ReadJson(folder / "config.json", None)
        if config is None:
            continue  # listed but never configured
        analyses = ReadJson(folder / "analyses.json", [])
        lizards.append({"id": lizardId, "config": config, "latest": analyses[-1] if analyses else None,
                        "profile": ProfileBrief(config["species"])})
    return lizards


# ---------- creating lizards ----------

def _Choice(value, options, field):
    if value not in options:
        if not options:
            raise RepTrackerError(f"{field}: no files yet. Turn on dev mode and upload one in Settings.")
        raise RepTrackerError(f"{field}: choose one of {', '.join(options)}.")
    return value


def _Species(value):
    """The species as the keeper typed it, in plain English (matched to a profile on the Research tab)."""
    species = " ".join(str(value or "").split())
    if not 1 <= len(species) <= 60:
        raise RepTrackerError('Species: type it in plain English, 1 to 60 characters (for example "leopard gecko").')
    return species


def LizardConfigFromForm(mode, formData, createdAt):
    """Validate the add/edit-lizard form; returns the config to save. createdAt is kept as given."""
    media = ListMedia(mode)
    name = str(formData.get("name", "")).strip()
    if not name or len(name) > 40:
        raise RepTrackerError("Name: 1 to 40 characters.")
    width = formData.get("enclosureWidthCm")
    if width in (None, ""):
        width = None   # optional: position is then a % of the video's width
    else:
        try:
            width = float(width)
        except (TypeError, ValueError):
            width = 0
        if not 10 <= width <= 1000:
            raise RepTrackerError("Enclosure width: 10 to 1000 cm, or leave it blank.")
    camera = formData.get("camera") or {}
    sensors = formData.get("sensors") or {}
    hotSide = _Choice(sensors.get("hotSide"), SIDES, "Hot side")

    def Sensor(key, label):
        s = sensors.get(key) or {}
        t, h = s.get("temperature") or {}, s.get("humidity") or {}
        return {
            "temperature": {"series": _Choice(t.get("series"), media["sensors"], f"{label} temperature"),
                            "unit": _Choice(t.get("unit"), TEMP_UNITS, f"{label} temperature unit")},
            "humidity": {"series": _Choice(h.get("series"), media["sensors"], f"{label} humidity"),
                         "unit": _Choice(h.get("unit"), HUMIDITY_UNITS, f"{label} humidity unit")},
        }

    return {
        "name": name,
        "species": _Species(formData.get("species")),
        "enclosureWidthCm": width,
        "createdAt": createdAt,
        "camera": {
            "view": _Choice(camera.get("view"), CAMERA_VIEWS, "Camera view"),
            "video": _Choice(camera.get("video"), media["videos"], "Camera video"),
        },
        "sensors": {
            "hotSide": hotSide,
            "hot": Sensor("hot", "Hot side"),
            "cold": Sensor("cold", "Cold side"),
        },
    }


def CreateNewLizard(mode, formData):
    """Validate the add-lizard form, write reptiles/<id>/config.json, and add it to reptiles.json."""
    createdAt = FormatTime(ParseTime(formData.get("createdAt") or FormatTime(datetime.now(timezone.utc))))
    config = LizardConfigFromForm(mode, formData, createdAt)
    name = config["name"]
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "lizard"
    lizardId, n = base, 2
    while (ReptilesDir(mode) / lizardId).exists():
        lizardId, n = f"{base}-{n}", n + 1
    WriteJson(ReptilesDir(mode) / lizardId / "config.json", config)
    index = ReadJson(IndexPath(mode), [])
    index.append({"name": name, "folder path": f"reptiles/{lizardId}"})
    WriteJson(IndexPath(mode), index)
    return {"id": lizardId, "config": config, "latest": None, "profile": ProfileBrief(config["species"])}


def UpdateLizard(mode, lizardId, formData):
    """Change a lizard's settings (name, species, width, camera, sensors). Its id, start time
    (createdAt) and saved analyses stay, so the camera and sensors keep their place in time."""
    old = LoadConfig(mode, lizardId)
    config = LizardConfigFromForm(mode, formData, old["createdAt"])
    WriteJson(LizardFolder(mode, lizardId) / "config.json", config)
    index = ReadJson(IndexPath(mode), [])
    for entry in index:
        if Path(entry["folder path"]).name == lizardId:
            entry["name"] = config["name"]
    WriteJson(IndexPath(mode), index)
    analyses = ReadJson(LizardFolder(mode, lizardId) / "analyses.json", [])
    return {"id": lizardId, "config": config, "latest": analyses[-1] if analyses else None,
            "profile": ProfileBrief(config["species"])}


def RemoveLizard(mode, lizardId):
    """Take a lizard off the dashboard. Its folder stays, so nothing is lost."""
    LizardFolder(mode, lizardId)
    index = [e for e in ReadJson(IndexPath(mode), []) if Path(e["folder path"]).name != lizardId]
    WriteJson(IndexPath(mode), index)


# ---------- simulated sensors ----------

def CheckSeries(series):
    """Raise unless series is {"t": ms between samples > 0, "value": [numbers]}."""
    if not isinstance(series, dict) or "t" not in series or "value" not in series:
        raise RepTrackerError('Sensor JSON needs a "t" key (ms between samples) and a "value" list.')
    t, values = series["t"], series["value"]
    if isinstance(t, bool) or not isinstance(t, (int, float)) or t <= 0:
        raise RepTrackerError('"t" must be a positive number of milliseconds.')
    if not isinstance(values, list) or not values or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        raise RepTrackerError('"value" must be a non-empty list of numbers.')


@lru_cache(maxsize=128)
def LoadSeries(mode, name):
    """A sensor series as (step_s, values). Sample i is at i * step_s; it loops after the last one."""
    series = ReadJson(SensorPath(mode, name), None)
    if series is None:
        raise RepTrackerError(f"Sensor series '{name}' isn't valid JSON.")
    CheckSeries(series)
    return series["t"] / 1000, tuple(float(v) for v in series["value"])


def ReadSensor(mode, name, offsetS):
    """The series value at offsetS seconds after the lizard started (latest sample at or before it)."""
    step, values = LoadSeries(mode, name)
    return values[int(offsetS // step) % len(values)]


def SensorChannels(config):
    """[(label, series, unit)] for the four channels: hot/cold x temperature/humidity."""
    s = config["sensors"]
    coldSide = "right" if s["hotSide"] == "left" else "left"
    out = []
    for key, side in (("hot", s["hotSide"]), ("cold", coldSide)):
        for kind in ("temperature", "humidity"):
            ch = s[key][kind]
            out.append((f"{key.capitalize()} side ({side}) {kind}", ch["series"], ch["unit"]))
    return out


def SummarizeSensors(mode, config, start, end):
    lines = []
    for label, series, unit in SensorChannels(config):
        vals = []
        t = start
        while t <= end:
            off = SourceOffsetSeconds(config, t)
            if off is not None:
                vals.append(ReadSensor(mode, series, off))
            t += timedelta(minutes=1)
        if vals:
            lines.append(f"- {label}: {min(vals):.1f} / {statistics.fmean(vals):.1f} / {max(vals):.1f} / {vals[-1]:.1f} {unit}")
        else:
            lines.append(f"- {label}: no readings in range")
    return "\n".join(lines)


def SensorsNow(mode, config, t):
    off = SourceOffsetSeconds(config, t)
    if off is None:
        return "No readings yet."
    return "\n".join(f"- {label}: {ReadSensor(mode, series, off):.1f} {unit}" for label, series, unit in SensorChannels(config))


# ---------- simulated camera ----------

@lru_cache(maxsize=64)
def VideoDurationSeconds(mode, name):
    path = VideosDir(mode) / f"{name}.mp4"
    if not path.exists():
        raise RepTrackerError(f"Video '{name}' not found.")
    # Read the duration from the file's metadata (about 1 s). Decoding every frame to count
    # them took 95 s on an 82-min 720p video, so that is only the fallback.
    frames = imageio_ffmpeg.read_frames(str(path))
    try:
        secs = next(frames).get("duration")
    finally:
        frames.close()
    if not secs or secs <= 0:
        _, secs = imageio_ffmpeg.count_frames_and_secs(str(path))
    return secs


def TakeAPicture(mode, videoName, videoSeconds):
    """Grab one frame from the camera video at videoSeconds; returns a PIL image."""
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-ss", f"{videoSeconds:.2f}",
           "-i", str(VideosDir(mode) / f"{videoName}.mp4"), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(out)).convert("RGB")


def ParsePDF(images, labels, pdfPath):
    """Put the images into one PDF, one per page, each with its timestamp label above it."""
    pages = []
    for img, label in zip(images, labels):
        page = Image.new("RGB", (img.width, img.height + 22), "white")
        page.paste(img, (0, 22))
        ImageDraw.Draw(page).text((6, 5), label, fill="black")
        pages.append(page)
    pages[0].save(pdfPath, save_all=True, append_images=pages[1:], resolution=72)


# ---------- prompts ----------

def FillTemplate(fileName, values):
    """Read prompts/<fileName> and replace each {{key}} with values[key]."""
    text = (PROMPTS / fileName).read_text(encoding="utf-8")
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(values.get(m.group(1), m.group(0))), text)


def PositionScale(config):
    """Template values for position: cm from the left wall, or % of the video's width if no width is set."""
    width = config.get("enclosureWidthCm")
    if width:
        return {"enclosure_width": f"{width:g} cm", "position_unit": "cm from the left wall", "position_max": f"{width:g}"}
    return {"enclosure_width": "not set", "position_unit": "percent of the image width from the left edge", "position_max": "100"}


def LabelTime(t):
    return t.strftime("%Y-%m-%d %H:%M UTC")


def GeneratePrompts(mode, lizardId, startIso, endIso, imageCount=None):
    """Build every prompt for one lizard over a time range and write them to a bundle folder.

    imageCount images are spread evenly over the range, at least 1 min apart (so every image has its
    own minute label); None means 1 per minute. Fewer than 60 images give one shorter IMAGES chunk.
    No video moment is sent twice: when the range is longer than the video (the live camera
    loops), only the last part of the range that fits in one pass of the video is analysed.
    """
    config = LoadConfig(mode, lizardId)
    start, end = ParseTime(startIso), ParseTime(endIso)
    created = ParseTime(config["createdAt"])
    if end <= start:
        raise RepTrackerError("The range must end after it starts.")
    if end <= created:
        raise RepTrackerError(f"{config['name']}'s camera starts at {LabelTime(created)}; pick a range after that.")
    start = max(start, created)
    minutes = (end - start).total_seconds() / 60
    if minutes > MAX_RANGE_MIN:
        raise RepTrackerError(f"Ranges are limited to {MAX_RANGE_MIN // 60} h ({MAX_RANGE_MIN} images).")

    video = config["camera"]["video"]
    duration = VideoDurationSeconds(mode, video)
    # One pass of the looping video at most, so no video moment is sent twice.
    requestedMinutes = minutes
    trimmed = minutes * 60 > duration
    if trimmed:
        minutes = max(1, int(duration // 60))
        start = end - timedelta(minutes=minutes)
    perMinute = max(1, math.ceil(minutes))                    # the most images the range can hold, 1 min apart
    if imageCount is None:
        count = perMinute
    else:
        try:
            count = int(imageCount)
        except (TypeError, ValueError):
            raise RepTrackerError("Images: a whole number, at least 1.")
        if count < 1:
            raise RepTrackerError("Images: a whole number, at least 1.")
    capped = count > perMinute
    count = min(count, perMinute)
    spacing = (end - start) / count if count < perMinute else timedelta(minutes=1)
    imageTimes = [start + spacing * i for i in range(count)]
    spacingMin = spacing.total_seconds() / 60
    hotSide = config["sensors"]["hotSide"]
    common = {
        "name": config["name"], "species": config["species"],
        **PositionScale(config),
        "camera_view": config["camera"]["view"], "hot_side": hotSide,
        "cold_side": "right" if hotSide == "left" else "left",
    }

    bundleId = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    folder = LizardFolder(mode, lizardId) / "prompts" / bundleId
    (folder / "frames").mkdir(parents=True, exist_ok=True)

    # The answer format for this animal: the base format with its species' activities, checks and conditions
    base = json.loads((PROMPTS / "response-schema.json").read_text(encoding="utf-8"))
    schema = json.dumps(research.BuildResponseSchema(base, research.FindRecord(config["species"])), indent=2, ensure_ascii=False)
    (folder / "system.txt").write_text(FillTemplate("system.txt", {**common, "response_schema": schema}), encoding="utf-8")
    (folder / "response-schema.json").write_text(schema, encoding="utf-8")

    analyses = ReadJson(LizardFolder(mode, lizardId) / "analyses.json", [])
    previous = analyses[-1]["result"].get("Analysis", "") if analyses else "None yet."
    profile = research.FindRecord(config["species"])
    researchText = research.PromptText(profile) if profile else ""
    context = FillTemplate("context-chunk.txt", {
        **common,
        "range_start": LabelTime(start), "range_end": LabelTime(end), "range_minutes": round(minutes),
        "sensor_summary": SummarizeSensors(mode, config, start, end),
        "species_file": f"{profile['slug']}/profile.json" if profile else "no profile yet",
        "research": researchText or "None yet. (A profile can be created on the Research tab.)",
        "previous_analysis": previous,
    })
    (folder / "context.txt").write_text(context, encoding="utf-8")

    chunks = [{"type": "context", "text": "context.txt"}]
    groups = [imageTimes[i:i + IMAGES_PER_CHUNK] for i in range(0, len(imageTimes), IMAGES_PER_CHUNK)]
    for n, group in enumerate(groups, 1):
        images, labels, frames = [], [], []
        for t in group:
            videoS = SourceOffsetSeconds(config, t) % duration
            img = TakeAPicture(mode, video, min(videoS, max(duration - 0.5, 0)))
            frame = f"frames/{t.strftime('%Y%m%d-%H%M')}.jpg"
            img.save(folder / frame, quality=85)
            images.append(img)
            labels.append(LabelTime(t))
            frames.append({"time": FormatTime(t), "label": LabelTime(t), "videoSeconds": round(videoS, 1), "file": frame})
        pdf = f"images-{n:02d}.pdf"
        ParsePDF(images, labels, folder / pdf)
        text = f"images-{n:02d}.txt"
        (folder / text).write_text(FillTemplate("images-chunk.txt", {
            **common, "chunk_index": n, "chunk_count": len(groups), "image_count": len(group),
            "image_spacing": "one per minute" if spacingMin <= 1.001 else f"one every {spacingMin:.0f} min" if spacingMin >= 2 else f"one every {spacingMin:.1f} min",
            "first_time": labels[0], "last_time": labels[-1],
        }), encoding="utf-8")
        chunks.append({"type": "images", "text": text, "pdf": pdf, "frames": frames})

    notes = []
    if trimmed:
        notes.append(f"Video '{video}' is {duration / 60:.1f} min, shorter than the {requestedMinutes:.0f}-min range, and it loops. "
                     f"So no moment is sent twice, only the last {minutes:.0f} min ({LabelTime(start)} to {LabelTime(end)}) were analysed.")
    if capped:
        notes.append(f"{imageCount} images were asked for, but images are at least 1 min apart, so this {minutes:.0f}-min range holds {count}.")
    if count < perMinute:
        notes.append(f"{count} images spread over {minutes:.0f} min: one every {spacingMin:.1f} min.")
    elif count < 60:
        notes.append(f"{count} image(s), one per minute: one IMAGES chunk.")
    manifest = {
        "mode": mode, "lizardId": lizardId, "bundleId": bundleId,
        "range": {"start": FormatTime(start), "end": FormatTime(end)},
        "imageCount": len(imageTimes), "imageSpacingS": round(spacing.total_seconds()), "system": "system.txt", "schema": "response-schema.json",
        "chunks": chunks, "notes": notes,
    }
    WriteJson(folder / "manifest.json", manifest)
    return manifest


def LoadBundle(mode, lizardId, bundleId):
    if not re.fullmatch(r"\d{8}-\d{6}", bundleId or ""):
        raise RepTrackerError("Unknown prompt bundle.")
    folder = LizardFolder(mode, lizardId) / "prompts" / bundleId
    manifest = ReadJson(folder / "manifest.json", None)
    if manifest is None:
        raise RepTrackerError("Unknown prompt bundle.")
    return folder, manifest


# ---------- AI providers ----------
# A provider is two functions with fixed signatures, registered under one name:
#   PROVIDERS[name](folder, manifest, config) -> a dict shaped like prompts/response-schema.json,
#                                                 plus an optional "_details" dict (see DETAIL_KEYS)
#   ASKERS[name](prompt, latest, sensorsNow, image=None) -> the answer to a keeper's question, as text;
#                                                 image is JPEG bytes of the camera now, when vision is on
# "mock" runs offline so the whole loop can be tested without an AI. "claude" (claude_ai.py, needs an
# Anthropic API key) and "gemini" (ai.py, needs a Google Cloud login) are the real ones. The provider
# in use is chosen in Settings (dev mode) and saved in data/ai-settings.json.

def _MockPosition(img, scale):
    """Mock-only stand-in for the AI: x of the dark pixels (the sample lizard is the darkest thing)."""
    g = img.convert("L")
    if g.width > 320:   # sampling a 4K frame pixel by pixel is slow; the mock doesn't need detail
        g = g.resize((320, max(1, round(320 * g.height / g.width))))
    xs = [x for x in range(0, g.width, 2) for y in range(0, g.height, 2) if g.getpixel((x, y)) < 75]
    return round(statistics.fmean(xs) / g.width * scale, 1) if len(xs) > 20 else None


def MockProvider(folder, manifest, config):
    """Offline stand-in: position from dark pixels; every other field from the bundle's own answer format,
    as "can't see" or nothing found, so the dashboard shows the species' stats without inventing values."""
    schema = ReadJson(folder / manifest["schema"], None) or ReadJson(PROMPTS / "response-schema.json", {})
    props = schema.get("properties", {})
    width = config.get("enclosureWidthCm") or 100   # no width: % of the image width
    movement = []
    for chunk in manifest["chunks"]:
        for fr in chunk.get("frames", []):
            movement.append({"time": fr["label"], "position": _MockPosition(Image.open(folder / fr["file"]), width)})
    seen = [m["position"] for m in movement if m["position"] is not None]
    unit = "cm from the left wall" if config.get("enclosureWidthCm") else "% of the image width from the left"
    if not seen:
        activity = "can't see animal"
    elif max(seen) - min(seen) > 0.25 * width:
        activity = "exploring"
    else:
        last = seen[-1] / width
        hotNear = last < 0.35 if config["sensors"]["hotSide"] == "left" else last > 0.65
        activity = "basking" if hotNear else "hiding"
    activities = props.get("Current activity", {}).get("enum", [])
    if activities and activity not in activities:
        activity = "other" if "other" in activities else activities[-1]
    last = lambda key, fallback: (props.get(key, {}).get("enum") or [fallback])[-1]
    result = {
        "Animal visible": "partly" if seen else "no",
        "Current activity": activity,
        "Body condition": last("Body condition", "can't see animal"),
        "Eating seen": last("Eating seen", "can't see animal"),
        "Droppings seen": last("Droppings seen", "can't tell"),
        "Food in bowl": "no bowl visible",
        "Conditions seen": [],
        "Hazardous conditions": {"Improper substrate": False, "Unsafe lighting": False, "Temperature too high": False,
                                 "Temperature too low": False, "Humidity too high": False, "Other": "none"},
        "Movement Data": movement,
        "Analysis": (f"[Mock provider, not a real AI] {config['name']} was seen in {len(seen)} of {len(movement)} images"
                     + (f", between {min(seen):.0f} and {max(seen):.0f} {unit}, mostly {activity}." if seen else ".")
                     + " Body condition, species checks and conditions need a real provider."),
    }
    checks = props.get("Species checks", {}).get("properties", {})
    if checks:
        result["Species checks"] = {sid: spec["enum"][-1] for sid, spec in checks.items()}
    return result


def MockAnswer(prompt, latest, sensorsNow, image=None):
    return (("[The Mock can't see pictures; the one attached was ignored.] " if image else "") +"[Mock provider, not a real AI] I can't reason about the question, but here is what I would use: "
            + (latest["result"]["Analysis"] if latest else "there is no analysis yet.")
            + " Current readings: " + sensorsNow.replace("\n", "; "))


def _CallAi(fn, *args):
    """Run a function from ai.py; its errors become messages the dashboard can show."""
    try:
        return fn(*args)
    except ai.AiError as err:
        raise RepTrackerError(str(err)) from err


def GeminiProvider(folder, manifest, config):
    schema = ReadJson(folder / manifest["schema"], None) or ReadJson(PROMPTS / "response-schema.json", {})
    return _CallAi(ai.AnalyzeBundle, folder, manifest, config, schema)


def GeminiAnswer(prompt, latest, sensorsNow, image=None):
    return _CallAi(ai.Answer, prompt, image)


def ClaudeProvider(folder, manifest, config):
    schema = ReadJson(folder / manifest["schema"], None) or ReadJson(PROMPTS / "response-schema.json", {})
    return _CallAi(claude_ai.AnalyzeBundle, folder, manifest, config, schema)


def ClaudeAnswer(prompt, latest, sensorsNow, image=None):
    return _CallAi(claude_ai.Answer, prompt, image)


PROVIDERS = {"mock": MockProvider, "claude": ClaudeProvider, "gemini": GeminiProvider}
ASKERS = {"mock": MockAnswer, "claude": ClaudeAnswer, "gemini": GeminiAnswer}
PINGS = {"claude": lambda: claude_ai.Ping(), "gemini": lambda: ai.Ping()}   # looked up at call time, so tests can patch them
PROVIDER_LABELS = {"mock": "Mock (offline, not a real AI)", "claude": "Claude (Anthropic API)",
                   "gemini": "Gemini (Google Vertex AI)"}
DEFAULT_PROVIDER = "mock"   # works on any computer; switch to a real AI in Settings
DETAIL_KEYS = ["model", "seconds", "tokens", "notes"]   # what a provider may add to a saved analysis


def CurrentProvider():
    """The provider chosen in Settings, or the default if none was chosen."""
    name = ReadJson(AI_SETTINGS, {}).get("provider")
    return name if name in PROVIDERS else DEFAULT_PROVIDER


def AiStatus():
    """What the Settings page shows: the provider in use and whether each one is ready."""
    gemini, claude = ai.Status(), claude_ai.Status()
    return {
        "provider": CurrentProvider(),
        "providers": [
            {"name": "mock", "label": PROVIDER_LABELS["mock"], "ready": True,
             "detail": "Runs on this computer. Estimates position from dark pixels; every other field is a placeholder."},
            {"name": "claude", "label": PROVIDER_LABELS["claude"], "ready": claude["ready"], "detail": claude["detail"],
             "apiKey": {"saved": claude["keySaved"], "mask": claude["keyMask"]},   # never the key itself
             "model": claude["model"], "models": claude["models"]},
            {"name": "gemini", "label": PROVIDER_LABELS["gemini"], "ready": gemini["ready"], "detail": gemini["detail"]},
        ],
    }


def SaveClaudeKey(key):
    """Save the Anthropic API key on this computer (data/claude-key.json, git-ignored)."""
    _CallAi(claude_ai.SaveKey, key)
    return AiStatus()


def SetClaudeModel(model):
    """Choose which Claude model analyses and questions use on this computer."""
    _CallAi(claude_ai.SetModel, model)
    return AiStatus()


def RemoveClaudeKey():
    """Forget the saved key. If Claude was in use and is no longer ready, go back to the Mock."""
    claude_ai.RemoveKey()
    if CurrentProvider() == "claude" and not claude_ai.Status()["ready"]:
        WriteJson(AI_SETTINGS, {"provider": DEFAULT_PROVIDER})
    return AiStatus()


def SetProvider(name):
    """Choose the AI provider for this computer. A provider that is not ready is refused."""
    if name not in PROVIDERS:
        raise RepTrackerError(f"Unknown AI provider. Choose one of: {', '.join(PROVIDERS)}.")
    status = next(p for p in AiStatus()["providers"] if p["name"] == name)
    if not status["ready"]:
        raise RepTrackerError(f"{status['label']} is not ready: {status['detail']}")
    WriteJson(AI_SETTINGS, {"provider": name})
    return AiStatus()


def TestProvider():
    """Make one tiny request to the provider in use, to prove the connection before a demo."""
    name = CurrentProvider()
    if name == "mock":
        return {"provider": name, "ok": True, "message": "The Mock provider runs offline, so there is nothing to connect to."}
    return {"provider": name, "ok": True, "message": _CallAi(PINGS[name])}


def SendPrompt(mode, lizardId, bundleId):
    """Send a generated bundle to the AI provider, save the answer to analyses.json, and return it."""
    folder, manifest = LoadBundle(mode, lizardId, bundleId)
    config = LoadConfig(mode, lizardId)
    provider = CurrentProvider()
    result = PROVIDERS[provider](folder, manifest, config)
    details = result.pop("_details", None) or {}
    entry = {"bundleId": bundleId, "provider": provider,
             **{key: details[key] for key in DETAIL_KEYS if key in details}, "range": manifest["range"],
             "sentAt": FormatTime(datetime.now(timezone.utc)), "result": result}
    path = LizardFolder(mode, lizardId) / "analyses.json"
    analyses = ReadJson(path, [])
    analyses.append(entry)
    WriteJson(path, analyses)
    return entry


def CurrentPicture(mode, config, now, maxWidth=1280):
    """The camera picture at this moment, as JPEG bytes, for a question with vision."""
    offset = SourceOffsetSeconds(config, now)
    if offset is None:
        raise RepTrackerError(f"{config['name']}'s camera starts at {LabelTime(ParseTime(config['createdAt']))}; there is no picture yet.")
    video = config["camera"]["video"]
    duration = VideoDurationSeconds(mode, video)
    img = TakeAPicture(mode, video, min(offset % duration, max(duration - 0.5, 0)))
    if img.width > maxWidth:
        img = img.resize((maxWidth, round(maxWidth * img.height / img.width)))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()


def AskQuestion(mode, lizardId, question, nowIso, vision=False):
    """Answer a keeper's question from prompts/ask.txt; returns the answer and the prompt sent.

    With vision, the camera picture at nowIso is sent too, and returned as a data: URL for the page.
    """
    config = LoadConfig(mode, lizardId)
    question = str(question or "").strip()[:500]
    if not question:
        raise RepTrackerError("Type a question first.")
    analyses = ReadJson(LizardFolder(mode, lizardId) / "analyses.json", [])
    latest = analyses[-1] if analyses else None
    now = ParseTime(nowIso)
    sensorsNow = SensorsNow(mode, config, now)
    # No picture before the lizard's camera starts: the question is asked without one.
    image = CurrentPicture(mode, config, now) if vision and SourceOffsetSeconds(config, now) is not None else None
    prompt = FillTemplate("ask.txt", {
        "image_note": (f"A picture from the camera at {LabelTime(now)} is attached. Use it to answer." if image
                       else "No picture is attached."),
        "name": config["name"], "species": config["species"], "question": question,
        "sensor_now": sensorsNow,
        "analysis_range": f"{latest['range']['start']} to {latest['range']['end']}" if latest else "none",
        "latest_analysis": json.dumps(latest["result"], indent=2) if latest else "None yet.",
    })
    provider = CurrentProvider()
    answer = ASKERS[provider](prompt, latest, sensorsNow, image)
    reply = {"answer": answer, "prompt": prompt, "provider": provider}
    if image:
        reply["image"] = "data:image/jpeg;base64," + base64.standard_b64encode(image).decode("ascii")
    return reply


# ---------- species profiles (Research tab) ----------
# A researcher turns prompts/research.txt into a dict shaped like prompts/profile-schema.json:
#   RESEARCHERS[name](prompt, schema) -> (profile, details)

def MockResearch(prompt, schema):
    species = re.search(r"^\s{4}(.+)$", prompt, re.M).group(1).strip()

    def r(lo, hi):
        return {"min": lo, "max": hi}

    return ({
        "commonName": species.title(), "scientificName": "unknown (Mock)", "animalType": "other",
        "activityPattern": "cathemeral", "habitat": "terrestrial",
        "summary": f"[Mock provider, not real research] Placeholder profile for {species}. "
                   "Select Claude in Settings and regenerate for a real one.",
        "adultSize": {"lengthCm": r(10, 30), "weightG": r(20, 100)}, "lifespanYears": r(5, 15),
        "temperaturesF": {"hotSide": r(88, 92), "coldSide": r(72, 78), "night": r(65, 75), "basking": r(90, 95)},
        "humidityPercent": r(30, 50), "uvb": "Mock: unknown.", "diet": "Mock: unknown.",
        "feeding": [{"stage": "adult", "intervalDays": r(2, 3), "notes": "Mock value."}],
        "droppings": {"intervalDays": r(1, 3), "notes": "Mock value."},
        "shedding": {"type": "patches", "intervalDays": r(30, 45), "signs": "Mock value."},
        "observableActivities": ["basking", "hiding", "exploring"],
        "trackedStats": [{"id": "shed", "label": "Shed (Mock)", "question": "Mock check: is the animal shedding?",
                          "options": ["not shedding", "about to shed", "shedding", "stuck shed"], "concernOptions": ["stuck shed"]}],
        "bodyCondition": {"healthy": "Mock value.", "underweight": "Mock value.", "overweight": "Mock value."},
        "conditions": [{"name": "Example condition (Mock)", "visibleSigns": ["mock sign"], "urgency": "monitor", "notes": "Mock value."}],
        "hazards": [{"name": "Example hazard (Mock)", "description": "Mock value."}],
        "husbandryNotes": "Mock value.", "confidence": "None: this is a Mock placeholder.",
    }, {"model": "mock"})


def ClaudeResearch(prompt, schema):
    return _CallAi(claude_ai.Research, prompt, schema)


def GeminiResearch(prompt, schema):
    raise RepTrackerError("Research isn't available with Gemini yet. Select Claude (or the Mock) in Settings.")


RESEARCHERS = {"mock": MockResearch, "claude": ClaudeResearch, "gemini": GeminiResearch}


def _ResearchCall(fn, *args):
    try:
        return fn(*args)
    except research.ResearchError as err:
        raise RepTrackerError(str(err)) from err


def _ProfileUsers():
    used = {}
    for mode in MODES:
        for l in ListLizards(mode):
            if l["profile"]:
                used.setdefault(l["profile"]["slug"], []).append(f"{l['config']['name']} ({mode})")
    return used


def ListProfiles():
    used = _ProfileUsers()
    return [{**research.Summary(r), "usedBy": used.get(r["slug"], [])} for r in research.ListRecords()]


def GetProfile(slug):
    record = _ResearchCall(research.ReadRecord, slug)
    if not record:
        raise RepTrackerError("Unknown species profile.")
    return {**record, "usedBy": _ProfileUsers().get(slug, [])}


def CreateProfile(species, regenerate=False):
    """Research a species with the AI provider in use: one call, then reference photos. Saved in research/<slug>/."""
    species = _Species(species)
    existing = research.FindRecord(species)
    if existing and not regenerate:
        raise RepTrackerError(f"There is already a profile for this species: {existing['profile']['commonName']}. "
                              "Open it, or Regenerate it to replace it.")
    if existing:
        species = existing["species"]
    schemaText = (PROMPTS / "profile-schema.json").read_text(encoding="utf-8")
    prompt = FillTemplate("research.txt", {"species": species, "profile_schema": schemaText})
    provider = CurrentProvider()
    raw, details = RESEARCHERS[provider](prompt, json.loads(schemaText))
    profile, notes = _ResearchCall(research.NormalizeProfile, raw)
    record = _ResearchCall(research.NewRecord, species, profile, provider, details.get("model"))
    if existing:
        record["slug"] = existing["slug"]
    record["notes"] = notes + (details.get("notes") or [])
    record["tokens"] = details.get("tokens")
    record["images"], imageNote = research.FetchImages(record)
    if imageNote:
        record["notes"].append(imageNote)
    research.WriteRecord(record)
    return GetProfile(record["slug"])


def UpdateProfile(slug, profile):
    """Save a keeper's corrections to a profile (the JSON edited on the Research tab)."""
    record = GetProfile(slug)
    record.pop("usedBy", None)
    record["profile"], record["notes"] = _ResearchCall(research.NormalizeProfile, profile)
    record["edited"] = True
    research.WriteRecord(record)
    return GetProfile(slug)


def DeleteProfile(slug):
    folder = _ResearchCall(research.Folder, slug)
    if not (folder / "profile.json").exists():
        raise RepTrackerError("Unknown species profile.")
    shutil.rmtree(folder)
    return ListProfiles()
