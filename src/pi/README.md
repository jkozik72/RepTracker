# RepTracker on a Raspberry Pi

One command installs RepTracker as a service that starts at boot (D8). Needs Raspberry Pi OS Bookworm or newer (64-bit recommended), a Pi 4 or 5, and internet access.

```
curl -fsSL https://raw.githubusercontent.com/jkozik72/RepTracker/main/src/pi/install.sh | sudo bash
```

Then open **https://reptracker.local** on any device on the same network (or the Pi's IP, which the installer prints). The browser warns once about the self-signed certificate. The first visit creates the sign-in account.

| Option (after `sudo bash -s --`) | Does |
|---|---|
| `--branch <name>` | Run another branch (default `main`) |
| `--port <n>` | HTTPS port (default 443). Port 80 redirects to it |
| `--keep-hostname` | Don't rename the Pi to `reptracker` |

For example: `curl -fsSL <url> | sudo bash -s -- --branch src/pi-install`

## Manage it

In **Settings → This installation**, or on the Pi:

| Command | Does |
|---|---|
| `sudo reptracker-admin update [branch]` | Download the branch (default: the current one), install its packages, restart |
| `sudo reptracker-admin restart` | Restart |
| `sudo reptracker-admin uninstall [--delete-data]` | Remove RepTracker and give the Pi its old name back. The data is copied to `/opt/reptracker-backup-<date>` unless `--delete-data` |
| `sudo reptracker-admin status` / `log` | Service state and version / the last task's output |
| `sudo journalctl -u reptracker -f` | The server's log |

Running the install command again also updates, and applies changes to the installation itself (the service, the admin command).

## What goes where

| Path | What |
|---|---|
| `/opt/reptracker/app` | The repository; data in `src/website/data/` and `research/` (kept across updates) |
| `/opt/reptracker/venv` | Python packages |
| `/etc/reptracker.env` | Port, redirect port, the Pi's old name |
| `/etc/systemd/system/reptracker.service` | The service (user `reptracker`) |
| `/usr/local/sbin/reptracker-admin`, `/etc/sudoers.d/reptracker` | The admin command and the one sudo rule that lets the app run it |

Updates reset tracked files (for example Toy mode's sample animals); Main data, profiles, the account and keys are untracked or git-ignored and stay.
