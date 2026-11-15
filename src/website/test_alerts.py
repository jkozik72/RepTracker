"""Tests for alerts worked out on the server, the schedule, and phone alerts (alerts.py, scheduler.py, push.py).
Nothing here calls an AI or a push service: those calls are mocked; files go to temporary folders.

Run from src/website:   .venv/Scripts/python -m unittest test_alerts
"""
import base64
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import alerts
import main
import push
import scheduler

NOW = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
PROFILE = {"commonName": "Leopard gecko", "temperaturesF": {"hotSide": {"min": 88, "max": 92}, "coldSide": {"min": 72, "max": 78}},
           "humidityPercent": {"min": 30, "max": 40}, "conditions": {"Mouth rot": "vet soon"},
           "trackedStats": [{"id": "shed", "label": "Shed", "options": ["not shedding", "stuck shed"], "concernOptions": ["stuck shed"]}],
           "feeding": [{"stage": "adult", "intervalDays": {"min": 2, "max": 3}}]}


def Lizard(result=None, feedings=(), profile=PROFILE):
    return {"id": "rex", "config": {"name": "Rex", "createdAt": "2026-11-14T00:00:00Z", "sensors": {}},
            "profile": profile, "latest": {"result": result} if result else None, "feedings": list(feedings)}


class AlertsTest(unittest.TestCase):
    def sensors(self, readings):
        """Patch the sensor readings: {label prefix: value}."""
        chans = [("Hot side (left) temperature", "h-t", "F"), ("Hot side (left) humidity", "h-h", "%RH"),
                 ("Cold side (right) temperature", "c-t", "F"), ("Cold side (right) humidity", "c-h", "%RH")]
        values = dict(zip(["h-t", "h-h", "c-t", "c-h"], readings))
        for p in (mock.patch.object(main, "SensorChannels", return_value=chans),
                  mock.patch.object(main, "SourceOffsetSeconds", return_value=60),
                  mock.patch.object(main, "ReadSensor", side_effect=lambda mode, s, off: values[s])):
            p.start(); self.addCleanup(p.stop)

    def test_sensor_alerts_have_stable_keys(self):
        self.sensors([95.2, 20, 75, 30])
        out = alerts.Alerts("main", Lizard(), NOW)
        self.assertEqual([a["key"] for a in out], ["temperature-hot-above", "humidity-below"])
        self.assertIn("Hot side temperature 95.2 °F is above 88–92 °F for Leopard gecko", out[0]["text"])
        self.sensors([96.0, 20, 75, 30])   # a new value: the same alert, the same key
        self.assertEqual(alerts.Alerts("main", Lizard(), NOW)[0]["key"], "temperature-hot-above")

    def test_analysis_and_feeding_alerts_like_the_dashboard(self):
        self.sensors([90, 35, 75, 35])     # in range
        result = {"Species checks": {"shed": "stuck shed"}, "Conditions seen": [{"name": "Mouth rot", "signs": "swollen jaw"}],
                  "Body condition": "underweight", "Hazardous conditions": {"Loose substrate": True, "Notes": "none"}}
        fed = [{"time": "2026-11-10T12:00:00Z", "food": "crickets"}]
        texts = [a["text"] for a in alerts.Alerts("main", Lizard(result, fed), NOW)]
        self.assertEqual(texts, ["Shed: stuck shed", "Mouth rot (vet soon): swollen jaw", "Body condition: underweight",
                                 "Overdue for feeding: last fed 5.0 days ago", "Loose substrate"])

    def test_no_profile_no_sensor_alerts(self):
        self.sensors([120, 0, 0, 0])
        self.assertEqual(alerts.Alerts("main", Lizard(profile=None), NOW), [])


class ScheduleAndPushTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for p in (mock.patch.object(push, "DATA", Path(tmp.name) / "push"),
                  mock.patch.object(scheduler, "SETTINGS", Path(tmp.name) / "schedule.json")):
            p.start(); self.addCleanup(p.stop)

    def test_new_alerts_are_sent_once(self):
        found = [[{"key": "a", "text": "Hot side too hot"}], [{"key": "a", "text": "Hot side too hot (now 97)"}],
                 [{"key": "a", "text": "x"}, {"key": "b", "text": "Shed: stuck shed"}], [], [{"key": "a", "text": "Hot side too hot"}]]
        with mock.patch.object(main, "ListLizards", return_value=[Lizard()]), \
             mock.patch.object(alerts, "Alerts", side_effect=found), mock.patch.object(push, "Send", return_value=1) as send:
            sent = [scheduler.CheckAlerts(NOW) for _ in found]
        self.assertEqual([[a for s in batch for a in s["alerts"]] for batch in sent],
                         [["Hot side too hot"], [], ["Shed: stuck shed"], [], ["Hot side too hot"]])   # again after it cleared
        self.assertEqual(send.call_args_list[0].args[:2], ("Rex: alert", "Hot side too hot"))
        self.assertEqual(send.call_args_list[0].kwargs["url"], "/#lizard-rex")

    def test_one_failing_animal_does_not_stop_the_others(self):
        two = [Lizard(), {**Lizard(), "id": "kit", "config": {**Lizard()["config"], "name": "Kit"}}]
        with mock.patch.object(main, "ListLizards", return_value=two), \
             mock.patch.object(main, "GeneratePrompts", side_effect=[main.RepTrackerError("camera not started"), {"bundleId": "b1"}]) as gen, \
             mock.patch.object(main, "SendPrompt") as send:
            results = scheduler.AnalyzeAll(NOW, 60, None)
        self.assertEqual([(r["name"], r["ok"]) for r in results], [("Rex", False), ("Kit", True)])
        self.assertEqual(gen.call_args.args[2:], ("2026-11-15T11:00:00Z", "2026-11-15T12:00:00Z", None))
        send.assert_called_once_with("main", "kit", "b1")

    def test_schedule_settings(self):
        self.assertEqual(scheduler.Settings(), {"intervalMinutes": 0, "images": None})
        scheduler.SaveSettings({"intervalMinutes": 60, "images": 10})
        self.assertEqual(scheduler.Settings(), {"intervalMinutes": 60, "images": 10})
        for bad in ({"intervalMinutes": 7}, {"intervalMinutes": 60, "images": 9999}):
            with self.assertRaises(main.RepTrackerError):
                scheduler.SaveSettings(bad)

    def phone(self):
        """A stand-in phone's push subscription, with real keys (as a browser makes them)."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        key = ec.generate_private_key(ec.SECP256R1())
        raw = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
        return {"endpoint": "https://push.example.test/abc", "keys": {"p256dh": b64(raw), "auth": b64(os.urandom(16))}}

    def test_send_encrypts_signs_and_drops_gone_phones(self):
        with self.assertRaises(push.PushError):
            push.Subscribe({"endpoint": "http://insecure"}, "x")
        push.Subscribe(self.phone(), "Android phone")
        gone = {**self.phone(), "endpoint": "https://push.example.test/gone"}
        push.Subscribe(gone, "Old phone")
        self.assertEqual([d["name"] for d in push.Devices()], ["Android phone", "Old phone"])
        calls = []
        def post(url, data=None, headers=None, timeout=None, **kw):
            calls.append((url, data, headers))
            return mock.Mock(status_code=410 if url.endswith("gone") else 201, text="", headers={})
        with mock.patch("pywebpush.requests.post", side_effect=post):
            sent = push.Send("Rex: alert", "Hot side too hot", url="/#lizard-rex", tag="alert-rex")
        self.assertEqual(sent, 1)
        url, body, headers = calls[0]
        self.assertNotIn(b"Hot side", body)                                # encrypted
        self.assertEqual(headers["Content-Encoding"], "aes128gcm")
        self.assertTrue(headers["Authorization"].startswith("vapid t="))   # signed with the server's keys
        claims = json.loads(base64.urlsafe_b64decode(headers["Authorization"].split("t=")[1].split(",")[0].split(".")[1] + "=="))
        self.assertEqual(claims["sub"], push.CONTACT)
        self.assertEqual([d["name"] for d in push.Devices()], ["Android phone"])   # the gone one was dropped
        if os.name == "posix":
            self.assertEqual(os.stat(push.DATA / "vapid.json").st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
