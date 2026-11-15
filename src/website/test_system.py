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


if __name__ == "__main__":
    unittest.main()
