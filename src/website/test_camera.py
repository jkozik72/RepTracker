"""Tests for the live camera (camera.py) and how main.py and app.py use it.
No real camera: frames are written by hand, and the capture loop runs on the ffmpeg stand-in.

Run from src/website:   .venv/Scripts/python -m unittest test_camera
"""
import io
import shutil
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from PIL import Image

import auth
import camera
import main

T0 = datetime(2026, 11, 15, 10, 0, 0, tzinfo=timezone.utc)


def Jpeg(color=(40, 80, 40), size=(64, 36)):
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, format="JPEG")
    return out.getvalue()


class FrameStoreTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        p = mock.patch.object(camera, "FRAMES", Path(tmp.name) / "frames"); p.start(); self.addCleanup(p.stop)

    def test_split_jpegs_across_chunks(self):
        a, b = Jpeg((255, 0, 0)), Jpeg((0, 0, 255))
        stream = b"junk" + a + b
        chunks = [stream[:30], stream[30:len(a) + 40], stream[len(a) + 40:]]
        frames, rest = [], b""
        for c in chunks:
            got, rest = camera.SplitJpegs(rest + c)
            frames += got
        self.assertEqual(frames, [a, b])
        self.assertEqual(rest, b"")
        got, rest = camera.SplitJpegs(a[:20])
        self.assertEqual((got, rest), ([], a[:20]))   # the unfinished tail is kept

    def test_save_and_find(self):
        self.assertTrue(camera.SaveFrame(T0 + timedelta(seconds=3), Jpeg()))
        self.assertFalse(camera.SaveFrame(T0 + timedelta(seconds=7), Jpeg()))   # same 10 s slot
        path = camera.FRAMES / "20261115" / "100000.jpg"
        self.assertTrue(path.exists())
        self.assertFalse(list(camera.FRAMES.glob("*/*.part")))
        self.assertEqual(camera.FrameAt(T0 + timedelta(seconds=25)), (T0, path))
        self.assertIsNone(camera.FrameAt(T0 + timedelta(seconds=31)))
        self.assertIsNone(camera.FrameAt(T0 - timedelta(seconds=40)))

    def test_nearest_frame_across_midnight_and_empty_files_skipped(self):
        midnight = datetime(2026, 11, 16, tzinfo=timezone.utc)
        camera.SaveFrame(midnight - timedelta(seconds=10), Jpeg())
        camera.SaveFrame(midnight + timedelta(seconds=10), Jpeg())
        self.assertEqual(camera.FrameAt(midnight - timedelta(seconds=2))[0], midnight - timedelta(seconds=10))
        empty = camera.FramePath(midnight - timedelta(seconds=10))
        empty.write_bytes(b"")                                        # cut short by a power cut
        self.assertEqual(camera.FrameAt(midnight - timedelta(seconds=2))[0], midnight + timedelta(seconds=10))

    def test_damaged_frame_is_skipped(self):
        camera.SaveFrame(T0, Jpeg())
        camera.SaveFrame(T0 + timedelta(seconds=10), Jpeg())
        camera.FramePath(T0).write_bytes(b"\xff\xd8 not really")
        self.assertEqual(main.LiveFrame(T0)[0], T0 + timedelta(seconds=10))

    def test_prune(self):
        for h in (0, 50, 80, 100):
            camera.SaveFrame(T0 - timedelta(hours=h), Jpeg())
        camera.PruneFrames(T0)
        kept = sorted(camera.FRAMES.glob("*/*.jpg"))
        self.assertEqual(len(kept), 2)
        self.assertIsNone(camera.FrameAt(T0 - timedelta(hours=80)))


@unittest.skipUnless(shutil.which("ffmpeg") or Path(camera.imageio_ffmpeg.get_ffmpeg_exe()).exists(), "no ffmpeg")
class CaptureLoopTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for name, value in {"FRAMES": Path(tmp.name) / "frames", "KEEP_EVERY_S": 1}.items():
            p = mock.patch.object(camera, name, value); p.start(); self.addCleanup(p.stop)
        self.addCleanup(camera.StopCamera)

    def test_stand_in_camera_saves_frames(self):
        camera.StartCamera("test")
        deadline = time.time() + 15
        while time.time() < deadline and not (camera.LatestFrame() and len(list(camera.FRAMES.glob("*/*.jpg"))) >= 2):
            time.sleep(0.2)
        latest = camera.LatestFrame()
        self.assertIsNotNone(latest, camera.CameraStatus())
        self.assertEqual(Image.open(io.BytesIO(latest[1])).size, (1280, 720))
        self.assertGreaterEqual(len(list(camera.FRAMES.glob("*/*.jpg"))), 2)
        self.assertTrue(camera.CameraStatus()["running"])

    def test_missing_program_is_reported_and_retried(self):
        with mock.patch.object(camera, "CaptureCommand", return_value=["/nonexistent/rpicam-vid"]):
            camera.StartCamera("pi")
            deadline = time.time() + 5
            while time.time() < deadline and not camera.CameraStatus()["error"]:
                time.sleep(0.1)
            self.assertIn("missing", camera.CameraStatus()["error"])
            self.assertTrue(any(t.is_alive() for t in camera._threads))   # still trying


class LiveLizardTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for target, name, value in [(main, "DATA", root), (camera, "FRAMES", root / "frames"),
                                    (main.research, "RESEARCH", root / "research")]:
            p = mock.patch.object(target, name, value); p.start(); self.addCleanup(p.stop)
        main.WriteJson(main.ReptilesDir("toy") / "rex" / "config.json", {
            "name": "Rex", "species": "x", "createdAt": "2026-11-14T00:00:00Z", "enclosureWidthCm": 90,
            "camera": {"view": "top", "source": "live", "video": None},
            "sensors": {"hotSide": "left", **{side: {"temperature": {"series": "hot-temp-f", "unit": "F"},
                                                     "humidity": {"series": "hot-humidity-rh", "unit": "%RH"}}
                                              for side in ("hot", "cold")}}})
        p = mock.patch.object(main, "DEFAULT_SENSORS", Path(__file__).resolve().parent / "data" / "defaults" / "sensors")
        p.start(); self.addCleanup(p.stop)

    def test_prompts_use_stored_frames_and_skip_missing_minutes(self):
        for m in range(10):
            if m not in (3, 4):
                camera.SaveFrame(T0 + timedelta(minutes=m), Jpeg())
        manifest = main.GeneratePrompts("toy", "rex", main.FormatTime(T0), main.FormatTime(T0 + timedelta(minutes=10)))
        frames = manifest["chunks"][1]["frames"]
        self.assertEqual(manifest["imageCount"], 8)
        self.assertEqual(len(frames), 8)
        self.assertIn("capturedAt", frames[0])
        self.assertNotIn("videoSeconds", frames[0])
        self.assertTrue(any("2 of 10" in n for n in manifest["notes"]))

    def test_prompts_without_any_frame(self):
        with self.assertRaisesRegex(main.RepTrackerError, "no pictures"):
            main.GeneratePrompts("toy", "rex", main.FormatTime(T0), main.FormatTime(T0 + timedelta(minutes=10)))

    def test_current_picture_falls_back_to_stored_frame(self):
        camera.SaveFrame(T0, Jpeg(size=(1600, 900)))
        config = main.LoadConfig("toy", "rex")
        img = Image.open(io.BytesIO(main.CurrentPicture("toy", config, T0 + timedelta(seconds=5))))
        self.assertEqual(img.width, 1280)
        with self.assertRaises(main.RepTrackerError):
            main.CurrentPicture("toy", config, T0 + timedelta(hours=1))

    def test_form_accepts_live_only_when_the_camera_is_on(self):
        form = {"name": "Rex", "species": "x", "camera": {"view": "top", "source": "live"},
                "sensors": main.LoadConfig("toy", "rex")["sensors"]}
        with mock.patch.dict(camera._state, {"device": "off"}):
            with self.assertRaisesRegex(main.RepTrackerError, "no live camera"):
                main.LizardConfigFromForm("toy", form, "2026-11-14T00:00:00Z")
        with mock.patch.dict(camera._state, {"device": "test"}):
            config = main.LizardConfigFromForm("toy", form, "2026-11-14T00:00:00Z")
        self.assertEqual(config["camera"], {"view": "top", "source": "live", "video": None})
        self.assertTrue(main.IsLiveCamera(config))

    def test_file_cameras_have_no_source_key(self):
        main.VideosDir("toy").mkdir(parents=True, exist_ok=True)
        (main.VideosDir("toy") / "v.mp4").write_bytes(b"x")
        form = {"name": "Rex", "species": "x", "camera": {"view": "side", "video": "v"},
                "sensors": main.LoadConfig("toy", "rex")["sensors"]}
        self.assertEqual(main.LizardConfigFromForm("toy", form, "2026-11-14T00:00:00Z")["camera"], {"view": "side", "video": "v"})


class StreamTest(unittest.TestCase):
    def test_wait_for_frame(self):
        import threading
        first = (datetime.now(timezone.utc), Jpeg())
        with mock.patch.object(camera, "_latest", first):
            self.assertEqual(camera.WaitForFrame(None, timeout=0.1), first)       # a frame already there
            self.assertIsNone(camera.WaitForFrame(first[0], timeout=0.1))          # nothing newer
            threading.Timer(0.1, camera._OnFrame, args=(Jpeg((9, 9, 9)),)).start()
            with mock.patch.object(camera, "SaveFrame", return_value=False):
                newer = camera.WaitForFrame(first[0], timeout=2)
            self.assertIsNotNone(newer)
            self.assertNotEqual(newer[0], first[0])


class CameraSettingsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        p = mock.patch.object(camera, "SETTINGS_FILE", Path(tmp.name) / "settings.json"); p.start(); self.addCleanup(p.stop)

    def test_defaults_then_saved_settings_reach_the_command(self):
        self.assertIn("--lens-position", camera.CaptureCommand("pi"))
        camera.SaveCameraSettings({"focus": "auto", "exposure": "manual", "shutterMs": "16.667", "gain": 2, "awb": "daylight"})
        cmd = camera.CaptureCommand("pi")
        self.assertEqual(cmd[cmd.index("--autofocus-mode") + 1], "continuous")
        self.assertNotIn("--lens-position", cmd)
        self.assertEqual(cmd[cmd.index("--shutter") + 1], "16667")
        self.assertEqual(cmd[cmd.index("--awb") + 1], "daylight")
        self.assertEqual(camera.CameraSettings()["gain"], 2.0)
        camera.SaveCameraSettings({"frameRate": 15})
        cmd = camera.CaptureCommand("pi")
        self.assertEqual(cmd[cmd.index("--framerate") + 1], "15")
        self.assertIn("fps=15,", " ".join(camera.CaptureCommand("test")))

    def test_bad_values_are_refused(self):
        for bad in ({"gain": 40}, {"frameRate": 60}, {"awb": "purple"}, {"focus": "maybe"}, {"brightness": "x"}):
            with self.assertRaises(ValueError):
                camera.SaveCameraSettings(bad)
        self.assertFalse(camera.SETTINGS_FILE.exists())


class PictureRouteTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for target, name, value in [(auth, "AUTH_FILE", Path(tmp.name) / "auth.json"), (auth, "DATA", Path(tmp.name)),
                                    (camera, "FRAMES", Path(tmp.name) / "frames")]:
            p = mock.patch.object(target, name, value); p.start(); self.addCleanup(p.stop)
        auth._failures.clear()
        import app as webapp
        self.client = webapp.app.test_client()

    def test_picture_route(self):
        self.assertEqual(self.client.get("/media/camera/picture").status_code, 401)
        self.client.post("/login", data={"username": "ann", "password": "long-enough-1", "confirm": "long-enough-1"})
        self.assertEqual(self.client.get("/media/camera/picture?n=1").status_code, 404)
        jpeg = Jpeg()
        with mock.patch.object(camera, "_latest", (datetime.now(timezone.utc), jpeg)):
            r = self.client.get("/media/camera/picture?n=2")
            self.assertEqual((r.status_code, r.mimetype, r.data), (200, "image/jpeg", jpeg))
            self.assertEqual(r.headers["Cache-Control"], "no-store")
            ahead = (datetime.now(timezone.utc) + timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            self.assertEqual(self.client.get(f"/media/camera/picture?t={ahead}").data, jpeg)   # clock ahead: newest
        camera.SaveFrame(T0, jpeg)
        self.assertEqual(self.client.get("/media/camera/picture?t=2026-11-15T10:00:05Z&n=3").status_code, 200)
        self.assertEqual(self.client.get("/media/camera/picture?t=2026-11-15T11:00:00Z").status_code, 404)
        self.assertEqual(self.client.get("/api/camera").get_json()["device"], "off")

    def test_stream_counts_open_views(self):
        self.client.post("/login", data={"username": "ann", "password": "long-enough-1", "confirm": "long-enough-1"})
        with mock.patch.object(camera, "_latest", (datetime.now(timezone.utc), Jpeg())), \
             mock.patch.object(camera, "WaitForFrame", side_effect=[(T0, Jpeg()), None]):
            r = self.client.get("/media/camera/stream")
            self.assertTrue(r.mimetype.startswith("multipart/x-mixed-replace"))
            self.assertEqual(r.data.count(b"--frame"), 1)
            r.close()
        self.assertEqual(camera._streams, 0)                              # counted back down when it ended
        with mock.patch.object(camera, "_streams", camera.MAX_STREAMS):
            self.assertEqual(self.client.get("/media/camera/stream").status_code, 503)


if __name__ == "__main__":
    unittest.main()
