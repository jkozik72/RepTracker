"""Species profiles: what RepTracker knows about a species, written once by the AI and reused.

A keeper types a species in plain English on the Research tab. One AI call fills in
prompts/profile-schema.json (ranges, feeding, droppings, shedding, conditions and their visible
signs, hazards...). The profile is saved in research/<slug>/profile.json and is then used by every
analysis of an animal of that species (the CONTEXT chunk) and for sensor alerts on the dashboard.

Reference photos come from Wikimedia Commons (search by scientific name), saved in
research/<slug>/images/ with their author, licence and source page. Profiles are committed;
photos are git-ignored and can be fetched again.

Nothing here calls an AI provider: main.py does that and hands the reply to NormalizeProfile.
"""
import html
import json
import logging
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT / "research"
PROMPTS = ROOT / "prompts"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "RepTracker/0.1 (local reptile-care dashboard; species reference photos)"
MAX_IMAGES = 6
IMAGE_WIDTH = 640

log = logging.getLogger("reptracker.research")


class ResearchError(Exception):
    """A problem with a profile, with a message that is safe to show on the page."""


# ---------- names and files ----------

def Slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")[:60]


def Folder(slug):
    if not re.fullmatch(r"[a-z0-9-]+", slug or ""):
        raise ResearchError("Unknown species profile.")
    return RESEARCH / slug


def ReadRecord(slug):
    try:
        return json.loads((Folder(slug) / "profile.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def WriteRecord(record):
    folder = Folder(record["slug"])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "profile.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")


def Schema():
    return json.loads((PROMPTS / "profile-schema.json").read_text(encoding="utf-8"))


def ListRecords():
    records = []
    for path in sorted(RESEARCH.glob("*/profile.json")):
        record = ReadRecord(path.parent.name)
        if record:
            records.append(record)
    return records


def Summary(record):
    """What the Research list shows for one profile."""
    p = record["profile"]
    return {"slug": record["slug"], "species": record["species"], "commonName": p["commonName"],
            "scientificName": p["scientificName"], "animalType": p["animalType"], "createdAt": record["createdAt"],
            "provider": record.get("provider"), "model": record.get("model"), "edited": record.get("edited", False),
            "image": record["images"][0]["file"] if record.get("images") else None}


def FindRecord(species):
    """The profile for a species as a keeper wrote it: matches the typed name, common name or scientific name."""
    want = Slug(species)
    if not want:
        return None
    direct = ReadRecord(want) if (RESEARCH / want / "profile.json").exists() else None
    if direct:
        return direct
    for record in ListRecords():
        p = record["profile"]
        if want in (Slug(record["species"]), Slug(p["commonName"]), Slug(p["scientificName"])):
            return record
    return None


def NewRecord(species, profile, provider, model):
    slug = Slug(species)
    if not slug:
        raise ResearchError("Type a species first.")
    return {"slug": slug, "species": species.strip(), "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "provider": provider, "model": model, "edited": False, "profile": profile, "images": []}


# ---------- forcing a reply into the profile schema ----------

def _Resolve(schema, root):
    ref = schema.get("$ref") if isinstance(schema, dict) else None
    if ref and ref.startswith("#/$defs/"):
        return root["$defs"][ref.split("/")[-1]]
    return schema


def _Normalize(value, schema, root, path, notes):
    schema = _Resolve(schema, root)
    if "enum" in schema:
        if value in schema["enum"]:
            return value
        fallback = "other" if "other" in schema["enum"] else schema["enum"][-1]
        notes.append(f"{path}: {value!r} is not one of {schema['enum']}; used {fallback!r}.")
        return fallback
    kind = schema.get("type")
    if kind == "object":
        value = value if isinstance(value, dict) else {}
        out = {}
        for key in schema.get("required", []):
            out[key] = _Normalize(value.get(key), schema["properties"][key], root, f"{path}.{key}" if path else key, notes)
        if set(out) == {"min", "max"} and isinstance(out["min"], float) and out["min"] > out["max"]:
            out["min"], out["max"] = out["max"], out["min"]
            notes.append(f"{path}: min was above max; swapped.")
        return out
    if kind == "array":
        items = value if isinstance(value, list) else []
        return [_Normalize(item, schema["items"], root, f"{path}[{i}]", notes) for i, item in enumerate(items)]
    if kind == "number":
        try:
            number = float(value)
            if number != number or number in (float("inf"), float("-inf")):
                raise ValueError
            return number
        except (TypeError, ValueError):
            notes.append(f"{path}: {value!r} is not a number; used 0.")
            return 0.0
    return "" if value is None else str(value).strip()


def RequestSchema(schema=None):
    """The profile schema in the form sent to the AI. Structured outputs compile the schema into a grammar with a
    size limit, and per-sex condition lists pushed it over. So the request asks for sexNotes as three texts and a
    "sex" on each condition; FromRequestShape turns the reply back into profile-schema.json's shape."""
    s = json.loads(json.dumps(schema or Schema()))
    s["properties"]["sexNotes"] = {
        "type": "object", "additionalProperties": False, "required": ["howToTell", "male", "female"],
        "description": "differences between the sexes",
        "properties": {"howToTell": {"type": "string", "description": "how a keeper can tell males from females, and from what age"},
                       "male": {"type": "string", "description": "care and behaviour specific to males"},
                       "female": {"type": "string", "description": "care and behaviour specific to females"}}}
    condition = s["$defs"]["condition"]
    condition["properties"]["sex"] = {"enum": ["both", "male", "female"],
                                      "description": "who gets it: both sexes, or only males or only females"}
    condition["required"].append("sex")
    return s


def FromRequestShape(raw):
    """A reply in RequestSchema's shape, in profile-schema.json's: sex-specific conditions move under sexNotes."""
    if not isinstance(raw, dict):
        return raw
    notes = raw.get("sexNotes")
    if not isinstance(notes, dict) or isinstance(notes.get("male"), dict):
        return raw   # already in the stored shape (an older reply, or a keeper's edit)
    out = dict(raw)
    general, bySex = [], {"male": [], "female": []}
    for c in raw.get("conditions") or []:
        if not isinstance(c, dict):
            continue
        sex = c.get("sex")
        c = {k: v for k, v in c.items() if k != "sex"}
        (bySex[sex] if sex in bySex else general).append(c)
    out["conditions"] = general
    out["sexNotes"] = {"howToTell": notes.get("howToTell", ""),
                       "male": {"notes": notes.get("male", ""), "conditions": bySex["male"]},
                       "female": {"notes": notes.get("female", ""), "conditions": bySex["female"]}}
    return out


def NormalizeProfile(raw, schema=None):
    """Force an AI reply (or a keeper's edit) into prompts/profile-schema.json; returns (profile, notes)."""
    schema = schema or Schema()
    if not isinstance(raw, dict) or not str(raw.get("commonName") or "").strip():
        raise ResearchError("The profile has no common name, so it was not saved. Try again.")
    notes = []
    raw = FromRequestShape(raw)
    profile = _Normalize(raw, schema, schema, "", notes)
    profile["trackedStats"] = CleanTrackedStats(profile.get("trackedStats", []), notes)
    return profile, notes


CANT_SEE = "can't see animal"


def CleanTrackedStats(stats, notes):
    """Species checks the dashboard can use: unique snake_case ids, at least two options, concern options that
    are real options, and a "can't see animal" option last. At most 6."""
    out, seen = [], set()
    for stat in stats[:6]:
        sid = re.sub(r"[^a-z0-9]+", "_", (stat.get("id") or stat.get("label") or "").lower()).strip("_")[:40]
        options = list(dict.fromkeys(o.strip() for o in stat.get("options", []) if o and o.strip() and o.strip().lower() != CANT_SEE))
        if not sid or sid in seen or len(options) < 2:
            notes.append(f"Dropped species check {stat.get('label') or sid!r}: it needs a unique name and at least two options.")
            continue
        seen.add(sid)
        concerns = [c for c in dict.fromkeys(c.strip() for c in stat.get("concernOptions", [])) if c in options]
        out.append({"id": sid, "label": stat.get("label") or sid.replace("_", " ").title(), "question": stat.get("question", ""),
                    "options": options + [CANT_SEE], "concernOptions": concerns})
    return out


# ---------- reference photos (Wikimedia Commons) ----------

def _Text(value):
    """Plain text from a Commons metadata field (which may hold HTML)."""
    return html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()[:200]


def _Get(url, timeoutS=15):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeoutS) as response:
        return response.read()


def FetchImages(record):
    """Download up to MAX_IMAGES reference photos for a profile; returns (images, note). Never raises."""
    p = record["profile"]
    known = p["scientificName"] and not p["scientificName"].lower().startswith("unknown")
    query = p["scientificName"] if known else p["commonName"]
    params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
              "gsrnamespace": "6", "gsrlimit": str(MAX_IMAGES * 2), "prop": "imageinfo",
              "iiprop": "url|mime|extmetadata", "iiurlwidth": str(IMAGE_WIDTH)}
    folder = Folder(record["slug"]) / "images"
    try:
        data = json.loads(_Get(f"{COMMONS_API}?{urllib.parse.urlencode(params)}"))
    except Exception as err:   # offline, blocked, or Commons changed: the profile still works without photos
        log.warning("Commons search failed: %r", err)
        return [], "Couldn't reach Wikimedia Commons for photos; the profile was saved without them."
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda pg: pg.get("index", 0))
    images = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        if info.get("mime") not in ("image/jpeg", "image/png") or not info.get("thumburl"):
            continue
        meta = info.get("extmetadata") or {}
        name = f"{len(images) + 1:02d}{'.png' if info['mime'] == 'image/png' else '.jpg'}"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / name).write_bytes(_Get(info["thumburl"]))
        except Exception as err:
            log.warning("Photo download failed: %r", err)
            continue
        images.append({"file": name, "title": _Text(page.get("title", "")).removeprefix("File:"),
                       "author": _Text((meta.get("Artist") or {}).get("value")) or "unknown",
                       "license": _Text((meta.get("LicenseShortName") or {}).get("value")) or "see source",
                       "source": info.get("descriptionurl", "")})
        if len(images) == MAX_IMAGES:
            break
    note = "" if images else f"Wikimedia Commons had no photos for \"{query}\"."
    return images, note


# ---------- sensor data from a profile (dev mode) ----------

SENSOR_PATTERNS = {
    "in-bounds": "In bounds: a gentle day/night swing inside the ranges",
    "under": "Goes under: in bounds, with stretches of several hours below the range",
    "over": "Goes over: in bounds, with stretches of several hours above the range",
    "variance": "High variance: centred, but noisy enough to cross both edges often",
}


def SensorSeries(lo, hi, pattern, days=7, stepS=300, seed=0, bias=0.0):
    """A finite sensor series {"t": ms, "value": [...]} for a range [lo, hi].

    bias moves the centre inside the range (-1 = at lo, +1 = at hi); the hot side's humidity uses -0.3.
    """
    import math
    import random
    rnd = random.Random(seed)
    half, mid = (hi - lo) / 2 or 1.0, (lo + hi) / 2
    centre = mid + bias * half * 0.6
    n = int(days * 86400 / stepS)
    # stretches out of range for "under"/"over": three windows of 3 to 8 h, at random points
    windows = [(start, start + rnd.uniform(3, 8) * 3600) for start in sorted(rnd.uniform(0.5, days - 0.5) * 86400 for _ in range(3))]
    values = []
    for k in range(n):
        t = k * stepS
        daily = math.sin(2 * math.pi * (t / 86400 - 0.25))
        if pattern == "variance":
            v = centre + daily * half * 0.4 + rnd.gauss(0, half * 0.9)
        else:
            v = centre + daily * half * 0.35 + rnd.gauss(0, half * 0.08)
            v = min(max(v, lo + half * 0.05), hi - half * 0.05)     # in bounds, with a small margin
            for a, b in windows:
                if pattern in ("under", "over") and a <= t <= b:
                    # ramp out and back over the window, peaking at 30-60 % of the range past the edge
                    depth = math.sin(math.pi * (t - a) / (b - a)) * half * rnd.uniform(0.6, 1.2)
                    v = (lo - depth * 0.5) if pattern == "under" else (hi + depth * 0.5)
                    v += rnd.gauss(0, half * 0.05)
        values.append(round(v, 1))
    return {"t": stepS * 1000, "value": values}


def SensorSet(record, pattern):
    """Four sensor series for a profile and a pattern: {name: series}. Temperatures in degrees F, humidity in % RH."""
    if pattern not in SENSOR_PATTERNS:
        raise ResearchError(f"Unknown pattern. Choose one of: {', '.join(SENSOR_PATTERNS)}.")
    p, slug = record["profile"], record["slug"]
    t, h = p["temperaturesF"], p["humidityPercent"]
    seed = sum(map(ord, slug + pattern))
    return {
        f"{slug}-{pattern}-hot-temp-f": SensorSeries(t["hotSide"]["min"], t["hotSide"]["max"], pattern, seed=seed + 1),
        f"{slug}-{pattern}-cold-temp-f": SensorSeries(t["coldSide"]["min"], t["coldSide"]["max"], pattern, seed=seed + 2),
        f"{slug}-{pattern}-hot-humidity-rh": SensorSeries(h["min"], h["max"], pattern, seed=seed + 3, bias=-0.3),
        f"{slug}-{pattern}-cold-humidity-rh": SensorSeries(h["min"], h["max"], pattern, seed=seed + 4, bias=0.3),
    }


# ---------- the answer format for one animal ----------

def BuildResponseSchema(base, record, sex="unknown"):
    """prompts/response-schema.json for one animal: the species' activities, checks and named conditions.

    Without a profile the base format is used as is (its default check is shed). A profile with no checks
    (or one made before checks existed) keeps the shed check only if the species sheds in one piece or in patches.
    """
    import copy
    schema = copy.deepcopy(base)
    if not record:
        return schema
    p, props = record["profile"], schema["properties"]
    activities = [a.strip().lower() for a in p.get("observableActivities", []) if a and a.strip()]
    props["Current activity"]["enum"] = list(dict.fromkeys(activities + ["other", CANT_SEE]))
    stats = p.get("trackedStats") or []
    if stats:
        checks = {s["id"]: {"enum": s["options"], "description": f"{s['label']}: {s['question']}"} for s in stats}
    elif p.get("shedding", {}).get("type") in ("whole", "patches"):
        checks = props["Species checks"]["properties"]
    else:
        checks = {}
    if checks:
        props["Species checks"]["properties"] = checks
        props["Species checks"]["required"] = list(checks)
    else:
        del props["Species checks"]
        schema["required"].remove("Species checks")
    names = [c["name"] for c in p.get("conditions", []) + SexConditions(p, sex) if c.get("name")]
    if names:
        props["Conditions seen"]["items"]["properties"]["name"] = {"enum": list(dict.fromkeys(names + ["other"])),
                                                                   "description": "a condition from the species profile, or other"}
    return schema


def SexConditions(p, sex):
    """Sex-specific conditions for an animal: its own sex's, or both when the sex is unknown."""
    notes = p.get("sexNotes") or {}
    sexes = [sex] if sex in ("male", "female") else ["male", "female"]
    return [c for s in sexes for c in (notes.get(s) or {}).get("conditions", [])]


# ---------- the profile in an analysis prompt ----------

def _R(r, unit=""):
    lo, hi = r["min"], r["max"]
    fmt = lambda v: f"{v:g}"
    return f"{fmt(lo)}{unit}" if lo == hi else f"{fmt(lo)}-{fmt(hi)}{unit}"


def PromptText(record, sex="unknown"):
    """The profile as plain text for the CONTEXT chunk of an analysis."""
    p = record["profile"]
    t = p["temperaturesF"]
    lines = [
        f"{p['commonName']} ({p['scientificName']}): {p['animalType']}, {p['habitat']}, {p['activityPattern']}.",
        p["summary"],
        f"Temperatures (F): hot side {_R(t['hotSide'])}, cold side {_R(t['coldSide'])}, basking {_R(t['basking'])}, night {_R(t['night'])}. "
        f"Humidity {_R(p['humidityPercent'], '%')}. UVB: {p['uvb']}",
        f"Adult size: {_R(p['adultSize']['lengthCm'], ' cm')}, {_R(p['adultSize']['weightG'], ' g')}.",
        "Feeding: " + "; ".join(f"{f['stage']} every {_R(f['intervalDays'], ' days')}" for f in p["feeding"]) + f". Diet: {p['diet']}",
        f"Droppings: about every {_R(p['droppings']['intervalDays'], ' days')}. {p['droppings']['notes']}",
        f"Shedding: {p['shedding']['type']}, about every {_R(p['shedding']['intervalDays'], ' days')}. Signs: {p['shedding']['signs']}",
        "Activities a camera can see: " + ", ".join(p["observableActivities"]) + ".",
        *(["Species checks (answer each in \"Species checks\"):"] +
          [f"- {s['label']}: {s['question']} Concerns: {', '.join(s['concernOptions']) or 'none'}." for s in p.get("trackedStats", [])]
          if p.get("trackedStats") else []),
        f"Body condition. Healthy: {p['bodyCondition']['healthy']} Underweight: {p['bodyCondition']['underweight']} "
        f"Overweight: {p['bodyCondition']['overweight']}",
        "Conditions to watch for (visible signs):",
        *[f"- {c['name']} [{c['urgency']}]: {'; '.join(c['visibleSigns'])}" for c in p["conditions"]],
        "Hazards:",
        *[f"- {h['name']}: {h['description']}" for h in p["hazards"]],
    ]
    notes = p.get("sexNotes")
    if notes:
        lines.append(f"Telling the sexes apart: {notes['howToTell']}")
        for s in ([sex] if sex in ("male", "female") else ["male", "female"]):
            part = notes.get(s) or {}
            if part.get("notes"):
                lines.append(f"{s.capitalize()}s: {part['notes']}")
            lines += [f"- {c['name']} ({s}) [{c['urgency']}]: {'; '.join(c['visibleSigns'])}" for c in part.get("conditions", [])]
    if record.get("edited"):
        lines.append("(This profile was checked and edited by the keeper.)")
    return "\n".join(line for line in lines if line)
