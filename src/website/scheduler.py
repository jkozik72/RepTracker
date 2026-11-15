"""Automatic analyses and phone alerts, run by the server itself, so they happen with no page open (D10).

- Every interval mark of real time (set in Settings, data/schedule.json), each Main-mode animal is analysed
  for the interval that just ended, with the AI provider in use. A real provider bills every call.
- Every minute, each Main-mode animal's alerts are worked out (alerts.py); an alert that wasn't there at the
  previous check goes to the phones with alerts on (push.py). Alerts only: notifications stay on the page.
Toy mode and the dev clock are not touched: the page's own polling (dev mode) is for those.
"""
import logging
import threading
import time
from datetime import datetime, timedelta, timezone

import alerts
import main
import push

INTERVALS = [0, 15, 30, 60, 120, 180, 360]   # minutes; 0 = off
SETTINGS = main.DATA / "schedule.json"
MODE = "main"
CHECK_S = 60
log = logging.getLogger("reptracker.scheduler")
_status = {"running": False, "lastRun": None, "lastResults": [], "nextRun": None}
_thread = None


def Settings():
    s = main.ReadJson(SETTINGS, {})
    interval = s.get("intervalMinutes", 0)
    images = s.get("images")
    return {"intervalMinutes": interval if interval in INTERVALS else 0,
            "images": images if isinstance(images, int) and 1 <= images <= main.MAX_RANGE_MIN else None}


def SaveSettings(body):
    interval = body.get("intervalMinutes")
    if interval not in INTERVALS:
        raise main.RepTrackerError("Pick an interval from the list.")
    images = body.get("images")
    if images not in (None, "") and not (isinstance(images, int) and 1 <= images <= main.MAX_RANGE_MIN):
        raise main.RepTrackerError("Images: a whole number from 1 to 360, or empty for 1 per minute.")
    main.WriteJson(SETTINGS, {"intervalMinutes": interval, "images": images or None})
    _status["nextRun"] = _NextMark(datetime.now(timezone.utc), interval)
    return Status()


def _NextMark(now, interval):
    if not interval:
        return None
    step = interval * 60
    return main.FormatTime(datetime.fromtimestamp((now.timestamp() // step + 1) * step, timezone.utc))


def Status():
    return {**Settings(), "intervals": INTERVALS, "running": _status["running"], "lastRun": _status["lastRun"],
            "lastResults": _status["lastResults"], "nextRun": _status["nextRun"], "serverRuns": _thread is not None,
            "devices": push.Devices(), "publicKey": push.Keys()[1]}


def AnalyzeAll(mark, interval, images):
    """Analyse every Main-mode animal for [mark - interval, mark]; returns [{name, ok, message}]."""
    results = []
    start = mark - timedelta(minutes=interval)
    for l in main.ListLizards(MODE):
        name = l["config"]["name"]
        try:
            manifest = main.GeneratePrompts(MODE, l["id"], main.FormatTime(start), main.FormatTime(mark), images)
            main.SendPrompt(MODE, l["id"], manifest["bundleId"])
            results.append({"name": name, "ok": True, "message": "analysed"})
        except Exception as err:   # one animal's problem (camera not started, AI error) doesn't stop the others
            results.append({"name": name, "ok": False, "message": str(err)[:200]})
            log.warning("Scheduled analysis of %s failed: %s", name, err)
    return results


def CheckAlerts(now=None):
    """Send a notification for each animal with an alert that wasn't there at the previous check; returns
    [{name, alerts}] of what was sent. What was seen is kept in data/push/sent.json, so a restart doesn't
    repeat alerts."""
    now = now or datetime.now(timezone.utc)
    seen = push._Read("sent.json", {})
    sent = []
    for l in main.ListLizards(MODE):
        current = alerts.Alerts(MODE, l, now)
        before = set(seen.get(l["id"], []))
        new = [a for a in current if a["key"] not in before]
        seen[l["id"]] = [a["key"] for a in current]
        if new:
            name = l["config"]["name"]
            title = f"{name}: alert" if len(new) == 1 else f"{name}: {len(new)} alerts"
            push.Send(title, "\n".join(a["text"] for a in new), url=f"/#lizard-{l['id']}", tag=f"alert-{l['id']}")
            sent.append({"name": name, "alerts": [a["text"] for a in new]})
    push._Write("sent.json", seen)
    return sent


def _Loop():
    lastMark = None
    while True:
        now = datetime.now(timezone.utc)
        s = Settings()
        try:
            if s["intervalMinutes"]:
                step = s["intervalMinutes"] * 60
                mark = datetime.fromtimestamp(now.timestamp() // step * step, timezone.utc)
                if lastMark is None:
                    lastMark = mark                      # start at the next mark, not at once
                elif mark > lastMark:
                    lastMark = mark
                    _status["running"] = True
                    _status["lastResults"] = AnalyzeAll(mark, s["intervalMinutes"], s["images"])
                    _status["lastRun"] = main.FormatTime(mark)
            _status["nextRun"] = _NextMark(datetime.now(timezone.utc), s["intervalMinutes"])
            CheckAlerts()
        except Exception:
            log.exception("Scheduler pass failed")
        finally:
            _status["running"] = False
        time.sleep(CHECK_S - time.time() % CHECK_S + 1)   # just after each whole minute


def Start():
    """Start the background loop once (app.py does this when it serves)."""
    global _thread
    if _thread is None:
        _thread = threading.Thread(target=_Loop, name="reptracker-scheduler", daemon=True)
        _thread.start()
