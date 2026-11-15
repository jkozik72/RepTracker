"""RepTracker core: lizard configs, simulated camera and sensors, prompt bundles, AI providers.

There are no real cameras or sensors. A camera is a video in media/videos/ and a sensor is a
JSON time series in media/sensors/: {"t": <ms between samples>, "value": [samples...]}.
Both start at the lizard's createdAt time and loop when they run out.

Two separate data sets, each under data/<mode>/:
- toy:  sample lizards, videos and sensors, for trying things out
- main: starts empty; the keeper adds media and lizards

Times are ISO 8601 strings in UTC ("2026-11-14T10:00:00Z").
"""
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

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DEFAULT_SENSORS = DATA / "defaults" / "sensors"   # shared by every mode, committed, never overwritten
PROMPTS = ROOT / "prompts"
RESEARCH = ROOT / "research"

MODES = ["toy", "main"]
SPECIES = ["leopard gecko", "skink"]
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


def ListMedia(mode):
    """Names (without extension) of the videos and sensor series available in this mode.

    Sensors are this mode's uploads plus the shared defaults in data/defaults/sensors/.
    """
    defaults = DefaultSensorNames()
    return {
        "videos": sorted(p.stem for p in VideosDir(mode).glob("*.mp4")),
        "sensors": sorted(set(defaults) | {p.stem for p in SensorsDir(mode).glob("*.json")}),
        "defaultSensors": defaults,
    }


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
        lizards.append({"id": lizardId, "config": config, "latest": analyses[-1] if analyses else None})
    return lizards


# ---------- creating lizards ----------

def _Choice(value, options, field):
    if value not in options:
        if not options:
            raise RepTrackerError(f"{field}: no files yet. Turn on dev mode and upload one in Settings.")
        raise RepTrackerError(f"{field}: choose one of {', '.join(options)}.")
    return value


def CreateNewLizard(mode, formData):
    """Validate the add-lizard form, write reptiles/<id>/config.json, and add it to reptiles.json."""
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

    createdAt = FormatTime(ParseTime(formData.get("createdAt") or FormatTime(datetime.now(timezone.utc))))
    config = {
        "name": name,
        "species": _Choice(formData.get("species"), SPECIES, "Species"),
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

    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "lizard"
    lizardId, n = base, 2
    while (ReptilesDir(mode) / lizardId).exists():
        lizardId, n = f"{base}-{n}", n + 1
    WriteJson(ReptilesDir(mode) / lizardId / "config.json", config)
    index = ReadJson(IndexPath(mode), [])
    index.append({"name": name, "folder path": f"reptiles/{lizardId}"})
    WriteJson(IndexPath(mode), index)
    return {"id": lizardId, "config": config, "latest": None}


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


def GeneratePrompts(mode, lizardId, startIso, endIso):
    """Build every prompt for one lizard over a time range and write them to a bundle folder.

    One image per minute from the start. Ranges under 60 min give one shorter IMAGES chunk;
    a video shorter than the range loops, like the live camera.
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

    imageTimes = [start + timedelta(minutes=i) for i in range(max(1, math.ceil(minutes)))]
    video = config["camera"]["video"]
    duration = VideoDurationSeconds(mode, video)
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

    schema = (PROMPTS / "response-schema.json").read_text(encoding="utf-8")
    (folder / "system.txt").write_text(FillTemplate("system.txt", {**common, "response_schema": schema}), encoding="utf-8")
    shutil.copy(PROMPTS / "response-schema.json", folder / "response-schema.json")

    analyses = ReadJson(LizardFolder(mode, lizardId) / "analyses.json", [])
    previous = analyses[-1]["result"].get("Analysis", "") if analyses else "None yet."
    research = RESEARCH / f"{config['species'].replace(' ', '')}.json"
    researchText = research.read_text(encoding="utf-8").strip() if research.exists() else ""
    context = FillTemplate("context-chunk.txt", {
        **common,
        "range_start": LabelTime(start), "range_end": LabelTime(end), "range_minutes": round(minutes),
        "sensor_summary": SummarizeSensors(mode, config, start, end),
        "species_file": research.name, "research": researchText or "None yet.",
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
            "first_time": labels[0], "last_time": labels[-1],
        }), encoding="utf-8")
        chunks.append({"type": "images", "text": text, "pdf": pdf, "frames": frames})

    notes = []
    if minutes < 60:
        notes.append(f"Range is {minutes:.0f} min (< 60): one IMAGES chunk with {len(imageTimes)} image(s).")
    if minutes * 60 > duration:
        notes.append(f"Video '{video}' is {duration / 60:.1f} min, shorter than the range; it loops.")
    manifest = {
        "mode": mode, "lizardId": lizardId, "bundleId": bundleId,
        "range": {"start": FormatTime(start), "end": FormatTime(end)},
        "imageCount": len(imageTimes), "system": "system.txt", "schema": "response-schema.json",
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
# The provider is not chosen yet (Q11 on main). "mock" runs offline so the whole loop can be tested;
# a real provider is a function with the same signature added to PROVIDERS.

def _MockPosition(img, scale):
    """Mock-only stand-in for the AI: x of the dark pixels (the sample lizard is the darkest thing)."""
    g = img.convert("L")
    if g.width > 320:   # sampling a 4K frame pixel by pixel is slow; the mock doesn't need detail
        g = g.resize((320, max(1, round(320 * g.height / g.width))))
    xs = [x for x in range(0, g.width, 2) for y in range(0, g.height, 2) if g.getpixel((x, y)) < 75]
    return round(statistics.fmean(xs) / g.width * scale, 1) if len(xs) > 20 else None


def MockProvider(folder, manifest, config):
    width = config.get("enclosureWidthCm") or 100   # no width: % of the image width
    movement = []
    for chunk in manifest["chunks"]:
        for fr in chunk.get("frames", []):
            movement.append({"time": fr["label"], "position": _MockPosition(Image.open(folder / fr["file"]), width)})
    seen = [m["position"] for m in movement if m["position"] is not None]
    unit = "cm from the left wall" if config.get("enclosureWidthCm") else "% of the image width from the left"
    if not seen:
        activity = "can't see lizard"
    elif max(seen) - min(seen) > 0.25 * width:
        activity = "exploring"
    else:
        last = seen[-1] / width
        hotNear = last < 0.35 if config["sensors"]["hotSide"] == "left" else last > 0.65
        activity = "basking" if hotNear else "hiding"
    return {
        "Weight": "can't see lizard", "Shed": "can't see lizard", "Food in bowl": "no bowl visible",
        "Current activity": activity,
        "Hazardous conditions": {"Improper substrate": False, "Unsafe lighting": False, "Temperature too high": False,
                                 "Temperature too low": False, "Humidity too high": False,
                                 "Signs of disease": "none", "Other": "none"},
        "Movement Data": movement,
        "Analysis": (f"[Mock provider, not a real AI] {config['name']} was seen in {len(seen)} of {len(movement)} images"
                     + (f", between {min(seen):.0f} and {max(seen):.0f} {unit}, mostly {activity}." if seen else ".")
                     + " Weight, shed and hazards need a real provider."),
    }


PROVIDERS = {"mock": MockProvider}
PROVIDER = "mock"   # until Q11 is decided


def SendPrompt(mode, lizardId, bundleId):
    """Send a generated bundle to the AI provider, save the answer to analyses.json, and return it."""
    folder, manifest = LoadBundle(mode, lizardId, bundleId)
    config = LoadConfig(mode, lizardId)
    result = PROVIDERS[PROVIDER](folder, manifest, config)
    entry = {"bundleId": bundleId, "provider": PROVIDER, "range": manifest["range"],
             "sentAt": FormatTime(datetime.now(timezone.utc)), "result": result}
    path = LizardFolder(mode, lizardId) / "analyses.json"
    analyses = ReadJson(path, [])
    analyses.append(entry)
    WriteJson(path, analyses)
    return entry


def AskQuestion(mode, lizardId, question, nowIso):
    """Answer a keeper's question from prompts/ask.txt; returns the answer and the prompt sent."""
    config = LoadConfig(mode, lizardId)
    question = str(question or "").strip()[:500]
    if not question:
        raise RepTrackerError("Type a question first.")
    analyses = ReadJson(LizardFolder(mode, lizardId) / "analyses.json", [])
    latest = analyses[-1] if analyses else None
    now = ParseTime(nowIso)
    prompt = FillTemplate("ask.txt", {
        "name": config["name"], "species": config["species"], "question": question,
        "sensor_now": SensorsNow(mode, config, now),
        "analysis_range": f"{latest['range']['start']} to {latest['range']['end']}" if latest else "none",
        "latest_analysis": json.dumps(latest["result"], indent=2) if latest else "None yet.",
    })
    answer = ("[Mock provider, not a real AI] I can't reason about the question, but here is what I would use: "
              + (latest["result"]["Analysis"] if latest else "there is no analysis yet.")
              + " Current readings: " + SensorsNow(mode, config, now).replace("\n", "; "))
    return {"answer": answer, "prompt": prompt}
