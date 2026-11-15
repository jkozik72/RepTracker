"""Sign-in for RepTracker, so it can be served on a LAN.

- One account. The first visit creates it; after that every page and API call needs a sign-in.
- The password is stored as a salted hash (werkzeug's scrypt), never in plain text: data/auth.json.
- The session cookie is signed with a random key made on first run: data/secret_key.
- Wrong passwords lock that address out for a while, doubling each time (from 30 s up to 15 min).
- For LAN hosting, a self-signed TLS certificate is made once (data/tls/), so passwords are not sent
  in plain text over Wi-Fi. Browsers warn about it once, because no public authority signed it.

All of data/auth.json, data/secret_key and data/tls/ are git-ignored.
"""
import datetime
import ipaddress
import json
import secrets
import socket
import threading
import time
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

DATA = Path(__file__).resolve().parent / "data"
AUTH_FILE = DATA / "auth.json"
SECRET_FILE = DATA / "secret_key"
TLS_DIR = DATA / "tls"
MIN_PASSWORD = 10
FREE_TRIES = 5

_lock = threading.Lock()
_failures = {}   # address -> (failed tries, locked until epoch s)


class AuthError(Exception):
    """A sign-in problem with a message that is safe to show on the page."""


def AccountExists():
    return AUTH_FILE.exists()


def CreateAccount(username, password, confirm):
    """The first visit's account. Refused once an account exists."""
    username = " ".join(str(username or "").split())
    if AccountExists():
        raise AuthError("An account already exists. Sign in instead.")
    if not 3 <= len(username) <= 40:
        raise AuthError("Username: 3 to 40 characters.")
    if len(password or "") < MIN_PASSWORD:
        raise AuthError(f"Password: at least {MIN_PASSWORD} characters.")
    if password != confirm:
        raise AuthError("The two passwords are not the same.")
    DATA.mkdir(parents=True, exist_ok=True)
    with _lock:
        if AccountExists():   # two first visits at once
            raise AuthError("An account already exists. Sign in instead.")
        AUTH_FILE.write_text(json.dumps({"id": secrets.token_hex(16), "username": username,
                                         "passwordHash": generate_password_hash(password)}), encoding="utf-8")
    return username, AccountId()


def _LockedFor(address):
    tries, until = _failures.get(address, (0, 0))
    return max(0, until - time.time())


def CheckLogin(username, password, address):
    """(username, account id) if the sign-in is right; AuthError otherwise (with a lockout after repeated failures)."""
    wait = _LockedFor(address)
    if wait:
        raise AuthError(f"Too many wrong passwords. Try again in {int(wait) + 1} s.")
    try:
        account = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        raise AuthError("No account yet. Reload the page to create one.")
    # Always check the hash, so a wrong username takes as long as a wrong password.
    good = check_password_hash(account["passwordHash"], password or "") and secrets.compare_digest(
        " ".join(str(username or "").split()).lower(), account["username"].lower())
    with _lock:
        if good:
            _failures.pop(address, None)
            return account["username"], account.get("id")
        tries = _failures.get(address, (0, 0))[0] + 1
        until = time.time() + min(900, 30 * 2 ** (tries - FREE_TRIES)) if tries >= FREE_TRIES else 0
        _failures[address] = (tries, until)
    raise AuthError("Wrong username or password.")


def AccountId():
    """The account's random id; a session is valid only for this id, so a new account signs everyone out."""
    try:
        return json.loads(AUTH_FILE.read_text(encoding="utf-8")).get("id")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def SecretKey():
    """The key that signs session cookies; made on first run and kept, so sign-ins survive a restart."""
    if not SECRET_FILE.exists():
        DATA.mkdir(parents=True, exist_ok=True)
        SECRET_FILE.write_text(secrets.token_hex(32), encoding="utf-8")
    return SECRET_FILE.read_text(encoding="utf-8").strip()


def LanAddresses():
    """This computer's IPv4 addresses on the local network (best effort)."""
    found = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except OSError:
        pass
    try:   # the address used for outgoing traffic; nothing is sent
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))
            found.add(s.getsockname()[0])
    except OSError:
        pass
    return sorted(a for a in found if not a.startswith("127."))


def Certificate():
    """(cert path, key path) of a self-signed certificate for this computer, made once (valid 2 years)."""
    cert, key = TLS_DIR / "cert.pem", TLS_DIR / "key.pem"
    if cert.exists() and key.exists():
        return str(cert), str(key)
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    host = socket.gethostname()
    names = [x509.DNSName("localhost"), x509.DNSName(host), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
    names += [x509.IPAddress(ipaddress.ip_address(a)) for a in LanAddresses()]
    private = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"RepTracker on {host}")])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(private.public_key())
                   .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=5))
                   .not_valid_after(now + datetime.timedelta(days=730))
                   .add_extension(x509.SubjectAlternativeName(names), critical=False)
                   .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                   .sign(private, hashes.SHA256()))
    TLS_DIR.mkdir(parents=True, exist_ok=True)
    key.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return str(cert), str(key)
