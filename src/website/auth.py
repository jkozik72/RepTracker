"""Sign-in for RepTracker, so it can be served on a LAN.

- One account. The first visit creates it; after that every page and API call needs a sign-in.
- The password is stored as a salted hash (werkzeug's scrypt), never in plain text: data/auth.json.
- The session cookie is signed with a random key made on first run: data/secret_key.
- Wrong passwords lock that address out for a while, doubling each time (from 30 s up to 15 min).
- For LAN hosting, HTTPS with a certificate from RepTracker's own certificate authority (data/tls/), so
  passwords are not sent in plain text over Wi-Fi. A phone that installs the authority's certificate once
  trusts the server (no warnings, and the app can be installed); others see a warning once (D9).

All of data/auth.json, data/secret_key and data/tls/ are git-ignored.
"""
import datetime
import ipaddress
import json
import os
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


def HostNames():
    """This computer's names: its hostname and the hostname.local that mDNS (avahi, Bonjour) announces."""
    host = socket.gethostname().split(".")[0].lower()
    return [host, f"{host}.local"]


CA_DAYS = 3650      # the local certificate authority: 10 years, installed once on each phone
SERVER_DAYS = 397   # this server's certificate: phones refuse longer ones; renewed by itself, no new install
# The only addresses the authority may vouch for (a name constraint that browsers enforce): .local names,
# localhost, and private network addresses. Even a stolen authority key can't fake any other website.
PRIVATE_NETS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16"]


def _Private(address):
    ip = ipaddress.ip_address(address)
    return any(ip in ipaddress.ip_network(n) for n in PRIVATE_NETS)


def _WritePrivate(path, data):
    """A file only this user can read (the authority's and the server's private keys)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)


def Authority():
    """(certificate, private key) of RepTracker's own certificate authority, made once (data/tls/ca.pem and
    ca-key.pem). Phones install its certificate once to trust this server: no warnings, and the browser
    allows installing the app. Name-constrained to .local, localhost and private addresses (D9)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    ca, caKey = TLS_DIR / "ca.pem", TLS_DIR / "ca-key.pem"
    if ca.exists() and caKey.exists():
        return x509.load_pem_x509_certificate(ca.read_bytes()), serialization.load_pem_private_key(caKey.read_bytes(), None)
    private = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.ORGANIZATION_NAME, "RepTracker"),
                         x509.NameAttribute(NameOID.COMMON_NAME, f"RepTracker local authority ({socket.gethostname()})")])
    now = datetime.datetime.now(datetime.timezone.utc)
    permitted = [x509.DNSName("local"), x509.DNSName("localhost")] + [x509.IPAddress(ipaddress.ip_network(n)) for n in PRIVATE_NETS]
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(private.public_key())
                   .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=5))
                   .not_valid_after(now + datetime.timedelta(days=CA_DAYS))
                   .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                   .add_extension(x509.KeyUsage(digital_signature=False, content_commitment=False, key_encipherment=False,
                                                data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True,
                                                encipher_only=False, decipher_only=False), critical=True)
                   .add_extension(x509.NameConstraints(permitted_subtrees=permitted, excluded_subtrees=None), critical=True)
                   .add_extension(x509.SubjectKeyIdentifier.from_public_key(private.public_key()), critical=False)
                   .sign(private, hashes.SHA256()))
    _WritePrivate(caKey, private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    ca.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return certificate, private


def AuthorityCertificate():
    """The authority's certificate (DER, what a phone installs) and its SHA-256 fingerprint to compare on the phone."""
    from cryptography.hazmat.primitives import hashes, serialization
    certificate, _ = Authority()
    fingerprint = certificate.fingerprint(hashes.SHA256()).hex().upper()
    return certificate.public_bytes(serialization.Encoding.DER), ":".join(fingerprint[i:i + 2] for i in range(0, len(fingerprint), 2))


def Certificate():
    """(cert path, key path) of this server's certificate, signed by Authority(). Made again when the computer's
    name or network addresses change or it is within 30 days of expiring; phones that trust the authority
    trust each new one."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
    cert, key, made = TLS_DIR / "cert.pem", TLS_DIR / "key.pem", TLS_DIR / "names.txt"
    authority, authorityKey = Authority()
    dns = ["localhost"] + [n for n in HostNames() if n.endswith(".local")]
    ips = ["127.0.0.1"] + [a for a in LanAddresses() if _Private(a)]
    signature = " ".join(dns + ips)
    now = datetime.datetime.now(datetime.timezone.utc)
    if cert.exists() and key.exists() and made.exists() and made.read_text(encoding="utf-8").strip() == signature:
        current = x509.load_pem_x509_certificate(cert.read_bytes())
        if current.issuer == authority.subject and current.not_valid_after_utc > now + datetime.timedelta(days=30):
            return str(cert), str(key)
    private = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, dns[-1])])
    names = [x509.DNSName(n) for n in dns] + [x509.IPAddress(ipaddress.ip_address(a)) for a in ips]
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(authority.subject).public_key(private.public_key())
                   .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=5))
                   .not_valid_after(now + datetime.timedelta(days=SERVER_DAYS))
                   .add_extension(x509.SubjectAlternativeName(names), critical=False)
                   .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                   .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False, key_encipherment=False,
                                                data_encipherment=False, key_agreement=False, key_cert_sign=False, crl_sign=False,
                                                encipher_only=False, decipher_only=False), critical=True)
                   .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
                   .add_extension(x509.SubjectKeyIdentifier.from_public_key(private.public_key()), critical=False)
                   .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(authorityKey.public_key()), critical=False)
                   .sign(authorityKey, hashes.SHA256()))
    _WritePrivate(key, private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    made.write_text(signature, encoding="utf-8")
    return str(cert), str(key)
