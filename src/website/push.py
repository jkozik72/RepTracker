"""Phone notifications through the browsers' push services (Web Push), for alerts only (D10).

- data/push/vapid.json: this server's push keys (made once). Phones only accept pushes signed with them.
- data/push/subscriptions.json: one entry per phone or browser that turned alerts on.
The push services (Google's for Android, Apple's for iPhone) pass each message on encrypted: they can't read it.
They require a contact for whoever runs the server; RepTracker gives the project's page, not an email address
(REPTRACKER_PUSH_CONTACT overrides it). All of data/push/ is git-ignored.
"""
import base64
import json
import logging
import os
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "push"
CONTACT = os.environ.get("REPTRACKER_PUSH_CONTACT", "https://github.com/jkozik72/RepTracker")
_lock = threading.Lock()
log = logging.getLogger("reptracker.push")


class PushError(Exception):
    """A problem with phone alerts, with a message for the page."""


def _Read(name, default):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _Write(name, value, private=False):
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / name
    text = json.dumps(value, indent=2).encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 if private else 0o644)
    with os.fdopen(fd, "wb") as f:
        f.write(text)


def Keys():
    """(private key PEM, public key for the browser, base64url) of this server's push keys, made once."""
    keys = _Read("vapid.json", None)
    if not keys:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        private = ec.generate_private_key(ec.SECP256R1())
        pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                    serialization.NoEncryption()).decode()
        raw = private.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        keys = {"privateKey": pem, "publicKey": base64.urlsafe_b64encode(raw).rstrip(b"=").decode()}
        _Write("vapid.json", keys, private=True)
    return keys["privateKey"], keys["publicKey"]


def Devices():
    """The phones and browsers with alerts on: [{id, name, added}] (no push addresses)."""
    return [{k: s[k] for k in ("id", "name", "added")} for s in _Read("subscriptions.json", [])]


def Subscribe(subscription, name):
    """Add (or refresh) a browser's push subscription: {endpoint, keys: {p256dh, auth}} from PushManager."""
    endpoint = str((subscription or {}).get("endpoint") or "")
    keys = (subscription or {}).get("keys") or {}
    if not endpoint.startswith("https://") or not keys.get("p256dh") or not keys.get("auth"):
        raise PushError("That browser didn't give a usable push subscription.")
    name = " ".join(str(name or "").split())[:60] or "A phone"
    with _lock:
        subs = [s for s in _Read("subscriptions.json", []) if s["endpoint"] != endpoint]
        entry = {"id": secrets.token_hex(6), "name": name, "added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "endpoint": endpoint, "keys": {"p256dh": keys["p256dh"], "auth": keys["auth"]}}
        subs.append(entry)
        _Write("subscriptions.json", subs, private=True)
    return entry["id"]


def Unsubscribe(deviceId=None, endpoint=None):
    with _lock:
        subs = _Read("subscriptions.json", [])
        keep = [s for s in subs if s["id"] != deviceId and s["endpoint"] != endpoint]
        _Write("subscriptions.json", keep, private=True)
    return len(subs) - len(keep)


def Send(title, body, url="/", tag=None):
    """Send one notification to every device with alerts on; returns how many got it. Devices the push
    service says are gone (404 / 410) are removed."""
    from py_vapid import Vapid02
    from pywebpush import WebPushException, webpush
    subs = _Read("subscriptions.json", [])
    if not subs:
        return 0
    private = Vapid02.from_pem(Keys()[0].encode())   # RFC 8292 signatures ("vapid t=..., k=...")
    private.conf["no-strict"] = True   # py_vapid's own check refuses an https contact with a path; RFC 8292 allows any URL
    payload = json.dumps({"title": title, "body": body, "url": url, "tag": tag})
    sent, gone = 0, []
    for s in subs:
        try:
            webpush({"endpoint": s["endpoint"], "keys": s["keys"]}, payload, vapid_private_key=private,
                    vapid_claims={"sub": CONTACT if CONTACT.startswith(("mailto:", "https://")) else f"mailto:{CONTACT}"},
                    ttl=12 * 3600, timeout=15)
            sent += 1
        except WebPushException as err:
            status = getattr(getattr(err, "response", None), "status_code", None)
            if status in (404, 410):
                gone.append(s["endpoint"])
            else:
                log.warning("Push to %s failed: %s", s["name"], status or err)
        except Exception as err:   # no internet, for example: try again with the next alert
            log.warning("Push to %s failed: %s", s["name"], type(err).__name__)
    for endpoint in gone:
        Unsubscribe(endpoint=endpoint)
    return sent
