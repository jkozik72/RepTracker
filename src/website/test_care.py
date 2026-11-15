"""Tests for sign-in (auth.py, app.py), notifications, feeding, movement data and generated sensor data.
Nothing here calls an AI or the network; files go to temporary folders.

Run from src/website:   .venv/Scripts/python -m unittest test_care
"""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import auth
import main
import research


class AuthTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name, value in {"AUTH_FILE": Path(self.tmp.name) / "auth.json", "DATA": Path(self.tmp.name)}.items():
            patcher = mock.patch.object(auth, name, value)
            patcher.start(); self.addCleanup(patcher.stop)
        auth._failures.clear()

    def test_first_account_then_sign_in(self):
        self.assertFalse(auth.AccountExists())
        with self.assertRaises(auth.AuthError):
            auth.CreateAccount("ann", "short", "short")
        with self.assertRaises(auth.AuthError):
            auth.CreateAccount("ann", "long-enough-1", "different-123")
        user, account = auth.CreateAccount("Ann", "long-enough-1", "long-enough-1")
        self.assertEqual(user, "Ann")
        self.assertEqual(account, auth.AccountId())
        stored = json.loads(auth.AUTH_FILE.read_text())
        self.assertNotIn("long-enough-1", json.dumps(stored))            # only a hash is stored
        with self.assertRaises(auth.AuthError):
            auth.CreateAccount("bob", "another-pass-2", "another-pass-2")  # one account only
        self.assertEqual(auth.CheckLogin("ann", "long-enough-1", "1.2.3.4")[0], "Ann")   # username ignores case

    def test_lockout_after_repeated_wrong_passwords(self):
        auth.CreateAccount("ann", "long-enough-1", "long-enough-1")
        for _ in range(auth.FREE_TRIES):
            with self.assertRaisesRegex(auth.AuthError, "Wrong"):
                auth.CheckLogin("ann", "nope", "9.9.9.9")
        with self.assertRaisesRegex(auth.AuthError, "Too many"):
            auth.CheckLogin("ann", "long-enough-1", "9.9.9.9")         # locked, even with the right password
        self.assertEqual(auth.CheckLogin("ann", "long-enough-1", "8.8.8.8")[0], "ann")   # another address is not

    def test_pages_and_api_need_a_sign_in(self):
        import app as webapp
        client = webapp.app.test_client()
        self.assertEqual(client.get("/").status_code, 302)
        self.assertEqual(client.get("/api/toy/lizards").status_code, 401)
        self.assertIn(b"Create the account", client.get("/login").data)
        r = client.post("/login", data={"username": "ann", "password": "long-enough-1", "confirm": "long-enough-1"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(client.get("/api/me").get_json()["user"], "ann")
        auth.AUTH_FILE.unlink()                                          # the account is gone: so is the session
        self.assertEqual(client.get("/api/me").status_code, 401)


class NotificationsTest(unittest.TestCase):
    def test_events_changes_and_feedings_newest_first(self):
        analyses = [
            {"range": {"end": "2026-11-15T01:00:00Z"}, "result": {"Current activity": "hiding", "Species checks": {"shed": "no shed visible"}}},
            {"range": {"end": "2026-11-15T02:00:00Z"}, "result": {
                "Current activity": "foraging", "Species checks": {"shed": "shedding normally"}, "Eating seen": "eating",
                "Droppings seen": "new droppings", "Notable moments": [{"time": "2026-11-15 01:42 UTC", "note": "Drank."}]}},
            {"range": {"end": "2026-11-15T03:00:00Z"}, "result": {"Current activity": "can't see animal", "Species checks": {"shed": "can't see animal"}}},
        ]
        notes = main.Notifications(analyses, [{"id": "1", "time": "2026-11-14T20:00:00Z", "food": "4 crickets", "amount": "", "notes": ""}])
        texts = [n["text"] for n in notes]
        self.assertEqual(texts[0], "Seen eating.")
        self.assertIn("Activity: foraging (was hiding).", texts)
        self.assertIn("Shed: shedding normally (was no shed visible).", texts)
        self.assertIn("Drank.", texts)
        self.assertEqual(texts[-1], "Fed: 4 crickets.")
        self.assertFalse(any("can't see" in t for t in texts))          # going out of view is not a change
        self.assertEqual([n["time"] for n in notes], sorted((n["time"] for n in notes), reverse=True))


class QuietNotificationsTest(unittest.TestCase):
    def test_routine_movement_is_dropped_and_at_most_two_per_analysis(self):
        moments = [{"time": f"2026-11-15 07:{m:02d} UTC", "note": note} for m, note in [
            (18, "Cheeto climbed along the branch in the middle of the enclosure."),
            (22, "Cheeto moved toward the right-hand hide, with only its tail visible at the edge."),
            (24, "Cheeto was active on the substrate near the right side."),
            (30, "Started shedding: the skin looks dull."),
            (33, "Drank from the water bowl."),
            (35, "Dug under the hide.")]]
        notes = main.Notifications([{"range": {"end": "2026-11-15T08:00:00Z"}, "result": {"Notable moments": moments}}], [])
        self.assertEqual([n["text"] for n in notes], ["Drank from the water bowl.", "Started shedding: the skin looks dull."])


class FeedingAndMovementTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.object(main, "DATA", Path(self.tmp.name))
        patcher.start(); self.addCleanup(patcher.stop)
        folder = main.ReptilesDir("toy") / "rex"
        main.WriteJson(folder / "config.json", {"name": "Rex", "species": "x", "createdAt": "2026-11-14T00:00:00Z",
                                                "enclosureWidthCm": 90, "camera": {"view": "top", "video": "v"},
                                                "sensors": {"hotSide": "left"}})
        self.folder = folder

    def test_feeding_log_and_context(self):
        with self.assertRaises(main.RepTrackerError):
            main.AddFeeding("toy", "rex", {"time": "2026-11-14T10:00:00Z", "food": "  "})
        main.AddFeeding("toy", "rex", {"time": "2026-11-14T18:00:00Z", "food": "4 crickets", "amount": "dusted"})
        feedings = main.AddFeeding("toy", "rex", {"time": "2026-11-13T18:00:00Z", "food": "2 worms"})
        self.assertEqual([f["food"] for f in feedings], ["2 worms", "4 crickets"])   # kept in time order
        end = datetime(2026, 11, 15, 18, tzinfo=timezone.utc)
        self.assertIn("Last fed 1.0 days before", main.FeedingContext("toy", "rex", end))
        self.assertEqual(main.DeleteFeeding("toy", "rex", feedings[0]["id"])[0]["food"], "4 crickets")

    def test_movement_points_from_analyses(self):
        main.WriteJson(self.folder / "analyses.json", [
            {"imageSpacingS": 120, "range": {"end": "x"}, "result": {"Movement Data": [
                {"time": "2026-11-15 01:00 UTC", "position": 10}, {"time": "2026-11-15 01:02 UTC", "position": None}]}},
            {"range": {"end": "x"}, "result": {"Movement Data": [                       # older analysis: spacing from the times
                {"time": "2026-11-15 01:02 UTC", "position_cm": 50}, {"time": "2026-11-15 01:03 UTC", "position_cm": 60}]}},
        ])
        data = main.MovementData("toy", "rex")
        self.assertEqual(data["positionMax"], 90)
        self.assertEqual([(p["t"][11:16], p["p"], p["w"]) for p in data["points"]], [("01:00", 10, 120), ("01:02", 50, 60), ("01:03", 60, 60)])


class UploadTest(unittest.TestCase):
    """Uploads stream straight from the request body to disk, through a .part file."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.object(main, "DATA", Path(self.tmp.name))
        patcher.start(); self.addCleanup(patcher.stop)

    def test_sensor_file_streams_to_disk(self):
        import io
        body = json.dumps({"t": 60000, "value": [1, 2, 3]}).encode()
        self.assertEqual(main.SaveUpload("toy", "sensors", "my-temp.json", io.BytesIO(body), len(body)), {"kind": "sensors", "name": "my-temp"})
        folder = main.SensorsDir("toy")
        self.assertEqual((folder / "my-temp.json").read_bytes(), body)
        self.assertEqual(list(folder.glob("*.part")), [])

    def test_cut_off_and_bad_uploads_leave_nothing(self):
        import io
        body = json.dumps({"t": 60000, "value": [1, 2, 3]}).encode()
        with self.assertRaisesRegex(main.RepTrackerError, "cut off"):
            main.SaveUpload("toy", "sensors", "a.json", io.BytesIO(body[:5]), len(body))
        with self.assertRaisesRegex(main.RepTrackerError, "Not valid JSON"):
            main.SaveUpload("toy", "sensors", "b.json", io.BytesIO(b"{nope"), 5)
        with self.assertRaisesRegex(main.RepTrackerError, "Couldn't read that video"):
            main.SaveUpload("toy", "videos", "c.mp4", io.BytesIO(b"not a video"), 11)
        self.assertEqual([p.name for p in main.DATA.rglob("*") if p.is_file()], [])


class SensorDataTest(unittest.TestCase):
    def test_patterns_stay_in_go_under_go_over_or_vary(self):
        def outside(pattern):
            v = research.SensorSeries(88, 92, pattern, seed=3)["value"]
            return sum(x < 88 for x in v), sum(x > 92 for x in v), len(v)
        self.assertEqual(outside("in-bounds")[:2], (0, 0))
        below, above, n = outside("under"); self.assertGreater(below, n * 0.03); self.assertEqual(above, 0)
        below, above, n = outside("over"); self.assertGreater(above, n * 0.03); self.assertEqual(below, 0)
        below, above, n = outside("variance"); self.assertGreater(below, 0); self.assertGreater(above, 0)
        self.assertEqual(research.SensorSeries(88, 92, "in-bounds")["t"], 300000)

    def test_unknown_pattern_is_refused(self):
        with self.assertRaises(research.ResearchError):
            research.SensorSet({"slug": "x", "profile": {}}, "sideways")


if __name__ == "__main__":
    unittest.main()
