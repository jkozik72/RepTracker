"""This installation: its branch and commit, and update / restart / uninstall on a Pi (D8).

Update, restart and uninstall work only when RepTracker was installed by src/pi/install.sh: the service
sets REPTRACKER_MANAGED=1, and the app runs the root-owned /usr/local/sbin/reptracker-admin through
one sudo rule. Anywhere else (a laptop running app.py) the Settings tab only shows the branch and commit.
"""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ADMIN = "/usr/local/sbin/reptracker-admin"
BRANCH_RE = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/-]{0,99}$")   # the same check as reptracker-admin


class AdminError(Exception):
    """A problem with an update, restart or uninstall, with a message for the page."""


def Managed():
    return os.environ.get("REPTRACKER_MANAGED") == "1" and Path(ADMIN).exists()


def TaskLog():
    return Path(os.environ.get("REPTRACKER_HOME", "/opt/reptracker")) / "task.log"


def _Git(*args, timeout=20):
    try:
        out = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def Info():
    """Branch, commit and whether update / restart / uninstall are available."""
    commit = _Git("log", "-1", "--format=%h%x1f%s%x1f%cI")
    sha, subject, date = (commit.split("\x1f") + ["", "", ""])[:3] if commit else ("", "", "")
    log = TaskLog()
    try:
        task = log.read_text(encoding="utf-8", errors="replace")[-4000:] if Managed() and log.exists() else ""
    except OSError:
        task = ""
    return {"managed": Managed(), "branch": _Git("rev-parse", "--abbrev-ref", "HEAD") or "",
            "commit": sha, "subject": subject, "date": date, "task": task,
            "installer": os.environ.get("REPTRACKER_INSTALLER_VERSION", "")}


def Branches():
    """The branches on GitHub (origin), sorted with main first."""
    out = _Git("ls-remote", "--heads", "origin", timeout=30)
    if out is None:
        raise AdminError("Couldn't list the branches on GitHub (no internet, or no git here).")
    names = sorted({line.split("refs/heads/", 1)[1] for line in out.splitlines() if "refs/heads/" in line})
    return sorted(names, key=lambda n: (n != "main", n))


def Run(action, branch=None, deleteData=False):
    """Start an update, restart or uninstall; it runs detached and writes its progress to the task log."""
    if not Managed():
        raise AdminError("Update, restart and uninstall work only on a Pi installed with src/pi/install.sh.")
    if action == "update":
        if not branch or not BRANCH_RE.match(branch):
            raise AdminError("Pick a branch.")
        args = ["update", branch]
    elif action == "restart":
        args = ["restart"]
    elif action == "uninstall":
        args = ["uninstall"] + (["--delete-data"] if deleteData else [])
    else:
        raise AdminError(f"Unknown action: {action}")
    try:
        out = subprocess.run(["sudo", "-n", ADMIN, *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as err:
        raise AdminError(f"Couldn't start it: {err}")
    if out.returncode != 0:
        raise AdminError((out.stderr or out.stdout).strip() or "reptracker-admin failed.")
    return {"started": action, "message": out.stdout.strip()}
