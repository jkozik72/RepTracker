"""An animal's alerts, worked out on the server for phone notifications (D10).

The same rules as getAlerts() in templates/index.html (the dashboard works them out in the browser, on the
dashboard clock); keep the two in step. Each alert has a stable key, so a phone is told once when an alert
starts, not again at every check while it lasts.
"""
from datetime import datetime, timezone

import main

UNIT_LABEL = {"F": "°F", "C": "°C", "%RH": "% RH", "g/m3": "g/m³"}
SHED = {"options": ["not shedding", "about to shed", "shedding", "stuck shed", "can't see animal"], "concernOptions": ["stuck shed"]}


def _CheckInfo(profile, checkId):
    for s in (profile or {}).get("trackedStats") or []:
        if s.get("id") == checkId:
            return s
    label = checkId.replace("_", " ").capitalize()
    return {"label": label, **(SHED if checkId == "shed" else {"options": None, "concernOptions": []})}


def FeedingState(lizard, now):
    """(state, days since fed) from the feeding log and the profile's adult feeding interval: fed / due / overdue."""
    past = [f for f in lizard.get("feedings") or [] if main.ParseTime(f["time"]) <= now]
    stages = ((lizard.get("profile") or {}).get("feeding")) or []
    stage = next((s for s in stages if s.get("stage") == "adult"), stages[0] if stages else None)
    if not past or not stage:
        return None, None
    days = (now - main.ParseTime(past[-1]["time"])).total_seconds() / 86400
    lo, hi = stage["intervalDays"]["min"], stage["intervalDays"]["max"]
    return ("fed" if days < lo else "due" if days <= hi else "overdue"), days


def SensorAlerts(mode, lizard, now):
    """Readings outside the species profile's ranges: each side's temperature, and the enclosure's humidity
    (the average of both sides)."""
    profile, config = lizard.get("profile"), lizard["config"]
    offset = main.SourceOffsetSeconds(config, now)
    if not profile or offset is None:
        return []
    out = []
    name = profile["commonName"]
    humidity = []
    for label, series, unit in main.SensorChannels(config):
        value = main.ReadSensor(mode, series, offset)
        side = "hot" if label.startswith("Hot") else "cold"
        if "temperature" in label:
            r = profile["temperaturesF"]["hotSide" if side == "hot" else "coldSide"]
            lo, hi = (r["min"], r["max"]) if unit != "C" else ((r["min"] - 32) * 5 / 9, (r["max"] - 32) * 5 / 9)
            if value < lo or value > hi:
                where = "below" if value < lo else "above"
                out.append({"key": f"temperature-{side}-{where}",
                            "text": f"{side.capitalize()} side temperature {value:.1f} {UNIT_LABEL[unit]} is {where} {lo:.0f}–{hi:.0f} {UNIT_LABEL[unit]} for {name}"})
        elif unit == "%RH":
            humidity.append(value)
    if humidity:
        r, avg = profile["humidityPercent"], sum(humidity) / len(humidity)
        if avg < r["min"] or avg > r["max"]:
            where = "below" if avg < r["min"] else "above"
            what = "both sides" if len(humidity) == 2 else "the sensor"
            out.append({"key": f"humidity-{where}",
                        "text": f"Humidity (average of {what}) {avg:.1f} % RH is {where} {r['min']:.0f}–{r['max']:.0f} % RH for {name}"})
    return out


def Alerts(mode, lizard, now=None):
    """[{key, text}] for one animal (a ListLizards entry): sensors out of range, concerning species checks,
    conditions the AI saw, body condition, weight, hazards, and overdue feeding."""
    now = now or datetime.now(timezone.utc)
    out = SensorAlerts(mode, lizard, now)
    r = (lizard.get("latest") or {}).get("result")
    profile = lizard.get("profile") or {}
    if r:
        for checkId, value in (r.get("Species checks") or {}).items():
            info = _CheckInfo(profile, checkId)
            if value in (info.get("concernOptions") or []):
                out.append({"key": f"check:{checkId}:{value}", "text": f"{info['label']}: {value}"})
        for c in r.get("Conditions seen") or []:
            urgency = (profile.get("conditions") or {}).get(c.get("name"))
            out.append({"key": f"condition:{c.get('name')}",
                        "text": f"{c.get('name')}{f' ({urgency})' if urgency else ''}{': ' + c['signs'] if c.get('signs') else ''}"})
        body = str(r.get("Body condition") or "").lower()
        if body and body != "healthy" and "see" not in body:
            out.append({"key": f"body:{body}", "text": f"Body condition: {body}"})
    state, days = FeedingState(lizard, now)
    if state == "overdue":
        out.append({"key": "feeding-overdue", "text": f"Overdue for feeding: last fed {days:.1f} days ago"})
    if r:
        for k, v in (r.get("Hazardous conditions") or {}).items():
            if v is True:
                out.append({"key": f"hazard:{k}", "text": k})
            elif isinstance(v, str) and v.strip() and v.strip().lower() != "none":
                out.append({"key": f"hazard:{k}", "text": f"{k}: {v}"})
        weight = str(r.get("Weight") or "").lower()
        if weight and weight != "healthy" and "see" not in weight:
            out.append({"key": f"weight:{weight}", "text": f"Weight: {weight}"})
    return out
