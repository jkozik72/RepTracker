"""Tests for this installation's info and update / restart / uninstall (system.py, app.py), and the
certificate's names (auth.py). Nothing here runs sudo, git fetch or the network; those calls are mocked.

Run from src/website:   .venv/Scripts/python -m unittest test_system
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import auth
import system


def _Done(stdout="", returncode=0, stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class SystemTest(unittest.TestCase):
    def managed(self):
        env = mock.patch.dict(os.environ, {"REPTRACKER_MANAGED": "1"})
        exists = mock.patch.object(system.Path, "exists", return_value=True)
        for p in (env, exists):
            p.start(); self.addCleanup(p.stop)

    def test_info_from_this_checkout(self):
        info = system.Info()
        self.assertFalse(info["managed"])                      # no installer on this computer
        self.assertRegex(info["commit"], r"^[0-9a-f]{7,}$")
        self.assertTrue(info["branch"])

    def test_actions_need_the_installer(self):
        with self.assertRaisesRegex(system.AdminError, "install.sh"):
            system.Run("restart")

    def test_actions_run_the_admin_command_through_sudo(self):
        self.managed()
        with mock.patch.object(system.subprocess, "run", return_value=_Done("Started")) as run:
            system.Run("update", "src/pi-install")
            system.Run("restart")
            system.Run("uninstall", deleteData=True)
        calls = [c.args[0] for c in run.call_args_list]
        self.assertEqual(calls, [["sudo", "-n", system.ADMIN, "update", "src/pi-install"],
                                 ["sudo", "-n", system.ADMIN, "restart"],
                                 ["sudo", "-n", system.ADMIN, "uninstall", "--delete-data"]])

    def test_bad_branch_names_and_failures_are_refused(self):
        self.managed()
        with mock.patch.object(system.subprocess, "run", return_value=_Done(returncode=1, stderr="sudo: a password is required")) as run:
            for bad in ("", "-x", "main; rm -rf /", "a b", "../x" * 40):
                with self.assertRaises(system.AdminError):
                    system.Run("update", bad)
            run.assert_not_called()
            with self.assertRaisesRegex(system.AdminError, "password is required"):
                system.Run("restart")
        with self.assertRaises(system.AdminError):
            system.Run("reboot")

    def test_branches_main_first(self):
        out = "a1\trefs/heads/src/x\nb2\trefs/heads/main\nc3\trefs/heads/docs/y\n"
        with mock.patch.object(system.subprocess, "run", return_value=_Done(out)):
            self.assertEqual(system.Branches(), ["main", "docs/y", "src/x"])


class SystemRoutesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for name, value in {"AUTH_FILE": Path(tmp.name) / "auth.json", "DATA": Path(tmp.name)}.items():
            p = mock.patch.object(auth, name, value); p.start(); self.addCleanup(p.stop)
        auth._failures.clear()
        import app as webapp
        self.client = webapp.app.test_client()
        self.client.post("/login", data={"username": "ann", "password": "long-enough-1", "confirm": "long-enough-1"})

    def test_uninstall_needs_the_password(self):
        with mock.patch.object(system, "Run", return_value={"started": "uninstall"}) as run:
            r = self.client.post("/api/system/uninstall", json={"password": "wrong"})
            self.assertEqual(r.status_code, 400)
            run.assert_not_called()
            r = self.client.post("/api/system/uninstall", json={"password": "long-enough-1", "deleteData": False})
            self.assertEqual(r.status_code, 200)
            run.assert_called_once_with("uninstall", None, False)

    def test_not_installed_is_a_clear_error(self):
        r = self.client.post("/api/system/restart", json={})
        self.assertEqual(r.status_code, 400)
        self.assertIn("install.sh", r.get_json()["error"])
        self.assertIn("commit", self.client.get("/api/system").get_json())


class PhoneTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for name, value in {"AUTH_FILE": Path(tmp.name) / "auth.json", "DATA": Path(tmp.name), "TLS_DIR": Path(tmp.name) / "tls"}.items():
            p = mock.patch.object(auth, name, value); p.start(); self.addCleanup(p.stop)
        auth._failures.clear()
        import app as webapp
        self.webapp = webapp
        self.client = webapp.app.test_client()
        self.client.post("/login", data={"username": "ann", "password": "long-enough-1", "confirm": "long-enough-1"})
        p = mock.patch.object(auth, "LanAddresses", return_value=["100.64.1.2", "192.168.1.20"]); p.start(); self.addCleanup(p.stop)

    def test_no_links_without_lan(self):
        with mock.patch.dict(self.webapp.app.config, {"LAN_PORT": None}):
            self.assertEqual(self.client.get("/api/phone").get_json(), {"lan": False, "links": []})

    def test_links_ip_first_and_qr_only_for_them(self):
        with mock.patch.dict(self.webapp.app.config, {"LAN_PORT": 443}),              mock.patch.object(auth, "HostNames", return_value=["reptracker", "reptracker.local"]):
            links = self.client.get("/api/phone").get_json()["links"]
            self.assertEqual([l["url"] for l in links], ["https://192.168.1.20", "https://100.64.1.2", "https://reptracker.local"])
            self.assertIn("Tailscale", links[1]["label"])
            r = self.client.get("/api/phone/qr.svg", query_string={"url": "https://192.168.1.20"})
            self.assertEqual(r.mimetype, "image/svg+xml")
            self.assertTrue(r.data.startswith(b"<svg"))
            self.assertEqual(self.client.get("/api/phone/qr.svg", query_string={"url": "https://example.com"}).status_code, 404)


class InstallableAppTest(unittest.TestCase):
    """What makes RepTracker installable opens without signing in; nothing else does (D9)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for name, value in {"AUTH_FILE": Path(tmp.name) / "auth.json", "DATA": Path(tmp.name), "TLS_DIR": Path(tmp.name) / "tls"}.items():
            p = mock.patch.object(auth, name, value); p.start(); self.addCleanup(p.stop)
        import app as webapp
        self.client = webapp.app.test_client()   # not signed in

    def test_manifest_worker_icons_and_certificate_are_open(self):
        import json
        from cryptography import x509
        manifest = json.loads(self.client.get("/manifest.webmanifest").data)
        self.assertEqual((manifest["display"], manifest["start_url"]), ("standalone", "/"))
        for icon in manifest["icons"]:
            self.assertEqual(self.client.get(icon["src"]).status_code, 200, icon["src"])
        worker = self.client.get("/sw.js")
        self.assertEqual((worker.status_code, worker.mimetype), (200, "text/javascript"))
        self.assertEqual(self.client.get("/static/offline.html").status_code, 200)
        ca = self.client.get("/reptracker-ca.crt")
        self.assertEqual(ca.mimetype, "application/x-x509-ca-cert")
        self.assertTrue(x509.load_der_x509_certificate(ca.data).extensions.get_extension_for_class(x509.BasicConstraints).value.ca)
        self.assertNotIn(b"PRIVATE", ca.data)

    def test_everything_else_still_needs_a_sign_in(self):
        self.assertEqual(self.client.get("/").status_code, 302)
        self.assertEqual(self.client.get("/api/phone").status_code, 401)
        self.assertEqual(self.client.get("/api/system").status_code, 401)


class AddressTest(unittest.TestCase):
    def test_the_open_address_comes_first_and_bad_ones_are_left_out(self):
        import app as webapp
        with mock.patch.dict(webapp.app.config, {"LAN_PORT": 443}), \
             mock.patch.object(auth, "LanAddresses", return_value=["10.8.0.2", "192.168.1.20", "100.64.1.2"]), \
             mock.patch.object(auth, "HostNames", return_value=["reptracker", "reptracker.local"]), \
             mock.patch.object(auth, "AuthorityCertificate", return_value=(b"", "AA")):
            urls = [l["url"] for l in webapp.PhoneLinks("192.168.1.20")["links"]]
            self.assertEqual(urls, ["https://192.168.1.20", "https://10.8.0.2", "https://100.64.1.2", "https://reptracker.local"])
            self.assertEqual(webapp.PhoneLinks("localhost:5000")["links"][0]["url"], "https://10.8.0.2")   # this computer: not useful
            self.assertEqual(webapp.PhoneLinks("evil.example")["links"][0]["url"], "https://10.8.0.2")     # only its own addresses

    def test_lan_addresses_skip_loopback_link_local_and_junk(self):
        addrinfo = [(0, 0, 0, "", ("127.0.1.1", 0)), (0, 0, 0, "", ("192.168.1.20", 0))]
        hostname_i = mock.Mock(stdout="192.168.1.20 169.254.3.4 172.17.0.1 fe80::1 junk\n")
        with mock.patch.object(auth.socket, "getaddrinfo", return_value=addrinfo), \
             mock.patch.object(auth.sys, "platform", "linux"), mock.patch("subprocess.run", return_value=hostname_i):
            found = auth.LanAddresses()
        self.assertNotIn("127.0.1.1", found); self.assertNotIn("169.254.3.4", found); self.assertNotIn("junk", found)
        self.assertIn("192.168.1.20", found); self.assertIn("172.17.0.1", found)
        self.assertEqual(len(found), len(set(found)))


class CertificateTest(unittest.TestCase):
    def test_local_name_and_remade_after_a_rename(self):
        from cryptography import x509
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        with mock.patch.object(auth, "TLS_DIR", Path(tmp.name)), mock.patch.object(auth, "LanAddresses", return_value=[]):
            def names(host):
                with mock.patch.object(auth.socket, "gethostname", return_value=host):
                    cert = x509.load_pem_x509_certificate(Path(auth.Certificate()[0]).read_bytes())
                return cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)
            self.assertIn("raspberrypi.local", names("raspberrypi"))
            first = (Path(tmp.name) / "cert.pem").read_bytes()
            self.assertIn("reptracker.local", names("reptracker"))
            self.assertNotEqual(first, (Path(tmp.name) / "cert.pem").read_bytes())


class AuthorityTest(unittest.TestCase):
    """RepTracker's own certificate authority (D9): its server certificate verifies like a real one, and the
    authority can't vouch for any other website, even with its private key (the name constraint)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for p in (mock.patch.object(auth, "TLS_DIR", Path(tmp.name)),
                  mock.patch.object(auth, "LanAddresses", return_value=["192.168.1.20", "203.0.113.9"]),
                  mock.patch.object(auth.socket, "gethostname", return_value="reptracker")):
            p.start(); self.addCleanup(p.stop)

    def verifier(self, name):
        import datetime
        import ipaddress
        from cryptography import x509
        from cryptography.x509.verification import DNSName, IPAddress, PolicyBuilder, Store
        ca, _ = auth.Authority()
        subject = IPAddress(ipaddress.ip_address(name)) if name[0].isdigit() else DNSName(name)
        now = datetime.datetime.now(datetime.timezone.utc)
        return PolicyBuilder().store(Store([ca])).time(now).build_server_verifier(subject)

    def leaf(self, *names):
        """A certificate for these names, signed with the authority's private key (as a thief could)."""
        import datetime
        import ipaddress
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
        ca, caKey = auth.Authority()
        key = ec.generate_private_key(ec.SECP256R1())
        now = datetime.datetime.now(datetime.timezone.utc)
        sans = [x509.IPAddress(ipaddress.ip_address(n)) if n[0].isdigit() else x509.DNSName(n) for n in names]
        return (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, names[0])]))
                .issuer_name(ca.subject).public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - datetime.timedelta(minutes=5)).not_valid_after(now + datetime.timedelta(days=30))
                .add_extension(x509.SubjectAlternativeName(sans), critical=False)
                .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
                .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(caKey.public_key()), critical=False)
                .sign(caKey, hashes.SHA256()))

    def test_server_certificate_verifies_for_its_names(self):
        from cryptography import x509
        server = x509.load_pem_x509_certificate(Path(auth.Certificate()[0]).read_bytes())
        for name in ("reptracker.local", "localhost", "192.168.1.20", "127.0.0.1"):
            self.verifier(name).verify(server, [])
        sans = server.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        self.assertNotIn("203.0.113.9", [str(a) for a in sans.get_values_for_type(x509.IPAddress)])   # public: left out

    def test_authority_cannot_vouch_for_other_websites(self):
        from cryptography.x509.verification import VerificationError
        for name in ("www.mybank.com", "google.com", "8.8.8.8", "reptracker.local.evil.com"):
            with self.subTest(name=name), self.assertRaises(VerificationError):
                self.verifier(name).verify(self.leaf(name), [])
        with self.assertRaises(VerificationError):   # one outside name spoils the whole certificate
            self.verifier("reptracker.local").verify(self.leaf("reptracker.local", "google.com"), [])
        self.verifier("printer.local").verify(self.leaf("printer.local"), [])   # inside the constraint: fine

    def test_keys_stay_private_and_the_authority_is_kept(self):
        import os
        auth.Certificate()
        first = auth.AuthorityCertificate()
        self.assertEqual(auth.AuthorityCertificate(), first)          # made once
        self.assertRegex(first[1], r"^([0-9A-F]{2}:){31}[0-9A-F]{2}$")
        if os.name == "posix":
            for name in ("ca-key.pem", "key.pem"):
                self.assertEqual(os.stat(auth.TLS_DIR / name).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
