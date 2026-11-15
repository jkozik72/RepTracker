"""RepTracker live camera: a frame store fed by one capture child process.

One camera per computer (like the AI provider). The child (rpicam-vid on a Raspberry Pi, or ffmpeg replaying a
toy video as a stand-in) writes MJPEG, a plain run of JPEGs, to stdout. A thread here reads it, keeps the newest
frame in memory for the live picture, and saves one frame every KEEP_EVERY_S seconds to
data/camera/frames/YYYYMMDD/HHMMSS.jpg (UTC). Frames older than KEEP_HOURS are deleted; analyses keep their own
copies, so nothing derived from them is lost.

There is no video: the app only ever needs a picture for a time T and a picture for now.
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / "data" / "camera" / "frames"   # git-ignored
SETTINGS_FILE = ROOT / "data" / "camera" / "settings.json"   # set from the add/edit-animal form
TEST_VIDEO = ROOT / "data" / "toy" / "media" / "videos" / "gecko-top.mp4"
DEVICES = ["off", "pi", "test"]
DEFAULT_LOOK = "--autofocus-mode manual --lens-position 2.0"   # 0.5 m; used until settings are saved

# The camera's picture settings, set in the add/edit-animal form. One camera per computer, so one set.
# focus: auto (continuous) or manual at lensPosition (dioptres: 0 = infinity, 2 = 50 cm, 3.3 = 30 cm).
# exposure: auto (with ev compensation) or manual (shutterMs, gain). The rest map to rpicam-vid options.
AWB_MODES = ["auto", "daylight", "cloudy", "indoor", "fluorescent", "tungsten", "incandescent"]
DEFAULT_SETTINGS = {"focus": "manual", "lensPosition": 2.0, "exposure": "auto", "ev": 0.0, "shutterMs": 16.667,
                    "gain": 1.0, "awb": "auto", "brightness": 0.0, "contrast": 1.0}
SETTING_RANGES = {"lensPosition": (0, 10), "ev": (-8, 8), "shutterMs": (0.1, 200), "gain": (1, 16),
                  "brightness": (-1, 1), "contrast": (0, 4)}

KEEP_HOURS = 72          # how far back stored frames go
KEEP_EVERY_S = 10        # one stored frame per slot of this many seconds
FIND_WITHIN_S = 30       # a frame for time T is the nearest stored one within this many seconds
STALL_S = 15             # no frame for this long: the child is killed and restarted
FRESH_S = 5              # the newest frame counts as "now" for this long
PRUNE_EVERY_S = 60
MAX_BUFFER = 20 * 1024 * 1024

_lock = threading.Lock()
_stop = threading.Event()
_restart = threading.Event()
_state = {"device": "off", "running": False, "lastFrameAt": None, "error": None}
_latest = None            # (time, jpeg bytes)
_child = None
_lastFrameMono = 0.0
_threads = []


def _Now():
    return datetime.now(timezone.utc)


def _Iso(t):
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- the capture command ----------

def CaptureCommand(device):
    """The child process that writes MJPEG to stdout for this device."""
    if device == "pi":
        look = (SettingsArgs(CameraSettings()) if SETTINGS_FILE.exists()
                else shlex.split(os.environ.get("REPTRACKER_CAMERA_ARGS", DEFAULT_LOOK)))
        return (["rpicam-vid", "--nopreview", "--timeout", "0", "--codec", "mjpeg", "--quality", "80", "--flush",
                 "--mode", "2304:1296", "--width", "1280", "--height", "720", "--framerate", "5", "--output", "-"] + look)
    if device == "test":   # the stand-in shows brightness and contrast, so the settings visibly do something
        s = CameraSettings()
        return [imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-re", "-stream_loop", "-1", "-i", str(TEST_VIDEO),
                "-vf", f"fps=5,scale=1280:720,eq=brightness={s['brightness']}:contrast={s['contrast']}",
                "-f", "mjpeg", "-q:v", "4", "-"]
    raise ValueError(f"Unknown camera device '{device}'; use one of {', '.join(DEVICES)}.")


def CameraSettings():
    """The saved picture settings, with defaults for anything not saved."""
    try:
        saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    return {**DEFAULT_SETTINGS, **{k: v for k, v in saved.items() if k in DEFAULT_SETTINGS}}


def CheckSettings(values):
    """Validate picture settings (missing keys keep their saved value); returns the full set. ValueError if wrong."""
    s = CameraSettings()
    for key, value in (values or {}).items():
        if key not in DEFAULT_SETTINGS:
            continue
        if key == "focus":
            if value not in ("auto", "manual"):
                raise ValueError("Focus: auto or manual.")
        elif key == "exposure":
            if value not in ("auto", "manual"):
                raise ValueError("Exposure: auto or manual.")
        elif key == "awb":
            if value not in AWB_MODES:
                raise ValueError(f"White balance: one of {', '.join(AWB_MODES)}.")
        else:
            lo, hi = SETTING_RANGES[key]
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"{key}: a number from {lo} to {hi}.")
            if not lo <= value <= hi:
                raise ValueError(f"{key}: a number from {lo} to {hi}.")
        s[key] = value
    return s


def SettingsArgs(s):
    """rpicam-vid options for the picture settings."""
    args = ["--autofocus-mode", "continuous"] if s["focus"] == "auto" else ["--autofocus-mode", "manual", "--lens-position", f"{s['lensPosition']:g}"]
    if s["exposure"] == "manual":
        args += ["--shutter", str(round(s["shutterMs"] * 1000)), "--gain", f"{s['gain']:g}"]
    else:
        args += ["--ev", f"{s['ev']:g}"]
    return args + ["--awb", s["awb"], "--brightness", f"{s['brightness']:g}", "--contrast", f"{s['contrast']:g}"]


def SaveCameraSettings(values):
    """Validate and save the picture settings, then restart capture so they take effect (a gap of a few seconds)."""
    s = CheckSettings(values)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    part = SETTINGS_FILE.with_name(SETTINGS_FILE.name + ".part")
    part.write_text(json.dumps(s, indent=2), encoding="utf-8")
    os.replace(part, SETTINGS_FILE)
    RestartCapture()
    return s


def RestartCapture():
    """Stop the capture child; the capture loop starts it again at once with the current settings."""
    proc = _child
    if proc:
        _restart.set()
        proc.kill()


def SplitJpegs(buffer):
    """Cut complete JPEGs (FF D8 ... FF D9) out of a byte stream; returns (frames, unfinished rest).
    Bytes outside a JPEG are dropped. MJPEG from rpicam-vid and ffmpeg has no embedded thumbnails."""
    frames, pos = [], 0
    while True:
        start = buffer.find(b"\xff\xd8", pos)
        if start < 0:
            return frames, (b"\xff" if buffer.endswith(b"\xff") else b"")
        end = buffer.find(b"\xff\xd9", start + 2)
        if end < 0:
            return frames, buffer[start:]
        frames.append(buffer[start:end + 2])
        pos = end + 2


# ---------- the frame store ----------

def SlotTime(t):
    """The start of t's KEEP_EVERY_S slot."""
    t = t.astimezone(timezone.utc)
    return t.replace(microsecond=0) - timedelta(seconds=t.second % KEEP_EVERY_S)


def FramePath(slot):
    return FRAMES / slot.strftime("%Y%m%d") / f"{slot.strftime('%H%M%S')}.jpg"


def SaveFrame(t, jpeg):
    """Store the frame as its slot's picture if that slot has none yet; returns True when written.
    Written to a .part file, synced, then renamed, so a power cut leaves no half-written frame under its name."""
    path = FramePath(SlotTime(t))
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    try:
        with open(part, "wb") as out:
            out.write(jpeg)
            out.flush()
            os.fsync(out.fileno())
        os.replace(part, path)
    finally:
        part.unlink(missing_ok=True)
    return True


def FrameCandidates(t):
    """Stored frames near t, nearest first, within FIND_WITHIN_S: (frameTime, path). Empty files are skipped."""
    t = t.astimezone(timezone.utc)
    base = SlotTime(t + timedelta(seconds=KEEP_EVERY_S / 2))   # t rounded to the nearest slot
    steps = int(FIND_WITHIN_S // KEEP_EVERY_S)
    slots = [base + timedelta(seconds=KEEP_EVERY_S * k) for n in range(steps + 1) for k in ((0,) if n == 0 else (-n, n))]
    for slot in sorted(slots, key=lambda s: abs((s - t).total_seconds())):
        if abs((slot - t).total_seconds()) > FIND_WITHIN_S:
            continue
        path = FramePath(slot)
        try:
            if path.stat().st_size > 0:
                yield slot, path
        except OSError:
            continue


def FrameAt(t):
    """The stored frame nearest t within FIND_WITHIN_S, as (frameTime, path), or None."""
    return next(FrameCandidates(t), None)


def LatestFrame():
    """The newest frame from the camera, as (frameTime, jpeg bytes), or None."""
    return _latest


def PruneFrames(now=None):
    """Delete stored frames older than KEEP_HOURS, and empty day folders."""
    cutoff = (now or _Now()) - timedelta(hours=KEEP_HOURS)
    if not FRAMES.exists():
        return
    for day in sorted(FRAMES.iterdir()):
        try:
            date = datetime.strptime(day.name, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if date + timedelta(days=1) <= cutoff:
            shutil.rmtree(day, ignore_errors=True)
            continue
        if date > cutoff:
            continue
        for f in day.glob("*.jpg"):
            try:
                t = datetime.strptime(day.name + f.stem, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if t < cutoff:
                f.unlink(missing_ok=True)
        if not any(day.iterdir()):
            day.rmdir()


def _RemoveParts():
    if FRAMES.exists():
        for p in FRAMES.glob("*/*.part"):
            p.unlink(missing_ok=True)


# ---------- capture ----------

def CameraStatus():
    """What the dashboard shows about this computer's camera."""
    with _lock:
        s = dict(_state)
    return {**s, "keepHours": KEEP_HOURS, "keepEveryS": KEEP_EVERY_S, "serverTime": _Iso(_Now()),
            "settings": CameraSettings(), "awbModes": AWB_MODES}


def _SetState(**kw):
    with _lock:
        _state.update(kw)


def _OnFrame(jpeg, onSaved=None):
    global _latest, _lastFrameMono
    t = _Now()
    _latest = (t, jpeg)
    _lastFrameMono = time.monotonic()
    _SetState(running=True, lastFrameAt=_Iso(t))
    try:
        if SaveFrame(t, jpeg):
            with _lock:
                if _state["error"] and _state["error"].startswith("Couldn't save"):
                    _state["error"] = None
            if onSaved:
                onSaved(FramePath(SlotTime(t)))
    except OSError as err:   # disk full, etc.: the live picture carries on
        _SetState(error=f"Couldn't save camera pictures: {err}")


def _RunChild(device, onSaved=None):
    """Run the capture child until it ends or is killed; returns how many frames it gave."""
    global _child, _lastFrameMono
    proc = subprocess.Popen(CaptureCommand(device), stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)   # stderr to the log
    _child, _lastFrameMono = proc, time.monotonic()
    buf, got, lastPrune = b"", 0, 0.0
    try:
        while not _stop.is_set():
            chunk = proc.stdout.read1(65536)
            if not chunk:
                break
            frames, buf = SplitJpegs(buf + chunk)
            if len(buf) > MAX_BUFFER:
                buf = b""
            for jpeg in frames:
                _OnFrame(jpeg, onSaved)
                got += 1
            if got and time.monotonic() - lastPrune > PRUNE_EVERY_S:
                lastPrune = time.monotonic()
                try:
                    PruneFrames()
                except OSError as err:
                    _SetState(error=f"Couldn't delete old camera pictures: {err}")
    finally:
        _child = None
        proc.kill()
        proc.wait()
        proc.stdout.close()
    return got, proc.returncode


def _CaptureLoop(device, onSaved=None):
    delay = 2
    while not _stop.is_set():
        try:
            got, code = _RunChild(device, onSaved)
            if got:
                delay = 2
            if _restart.is_set():   # new settings: start again at once
                _restart.clear()
                continue
            if not _stop.is_set():
                _SetState(error=f"The camera stopped (exit code {code}); restarting.")
        except FileNotFoundError as err:
            _SetState(error=f"The camera program is missing: {err.filename or err}")
        except Exception as err:   # anything else: record it and try again
            _SetState(error=f"Camera error: {type(err).__name__}: {err}")
        _SetState(running=False)
        if _stop.wait(delay):
            break
        delay = min(delay * 2, 30)


def _Watchdog():
    while not _stop.wait(1):
        proc = _child
        if proc and time.monotonic() - _lastFrameMono > STALL_S:
            _SetState(error=f"No picture from the camera for {STALL_S} s; restarting it.")
            proc.kill()


def StartCamera(device, onSaved=None):
    """Start capturing from device ("off", "pi" or "test") in background threads."""
    if device not in DEVICES:
        raise ValueError(f"Unknown camera device '{device}'; use one of {', '.join(DEVICES)}.")
    StopCamera()
    _SetState(device=device, running=False, lastFrameAt=None, error=None)
    if device == "off":
        return
    _stop.clear()
    _RemoveParts()
    for target, a in ((_CaptureLoop, (device, onSaved)), (_Watchdog, ())):
        th = threading.Thread(target=target, args=a, daemon=True, name=f"camera-{target.__name__.strip('_')}")
        th.start()
        _threads.append(th)


def StopCamera():
    global _latest
    _stop.set()
    proc = _child
    if proc:
        proc.kill()
    for th in _threads:
        th.join(timeout=5)
    _threads.clear()
    _latest = None
    _SetState(device="off", running=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the RepTracker camera in the foreground and print each saved frame")
    parser.add_argument("--camera", choices=DEVICES[1:], default="test")
    args = parser.parse_args()
    StartCamera(args.camera, onSaved=lambda p: print("saved", p, flush=True))
    try:
        while True:
            time.sleep(5)
            s = CameraStatus()
            if s["error"]:
                print("error:", s["error"], flush=True)
    except KeyboardInterrupt:
        StopCamera()
