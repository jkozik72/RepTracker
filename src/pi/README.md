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

## On a phone

In **Settings → Open on your phone**: scan the QR code (use the IP address on Android), download the RepTracker certificate and install it once (the steps for Android and iPhone are there), then install RepTracker as an app. The certificate can only vouch for RepTracker's own addresses (D9).

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
| `/etc/reptracker.env` | Port, redirect port, the Pi's old name, the camera (`REPTRACKER_CAMERA`, `REPTRACKER_CAMERA_ARGS`) |
| `/opt/reptracker/app/src/website/data/camera/frames/` | Live camera pictures, one per 10 s, kept 72 h |
| `/etc/systemd/system/reptracker.service` | The service (user `reptracker`) |
| `/usr/local/sbin/reptracker-admin`, `/etc/sudoers.d/reptracker` | The admin command and the one sudo rule that lets the app run it |

Updates reset tracked files (for example Toy mode's sample animals); Main data, profiles, the account and keys are untracked or git-ignored and stay.

## Live camera (Pi Camera Module 3)

The installer installs `rpicam-vid` if it is missing, adds `reptracker` to group `video`, and sets `REPTRACKER_CAMERA=pi`. Then **Add animal → Camera → Source: Camera**, where its picture settings (focus, exposure, white balance, brightness, contrast) are set with a live preview. Settings → Update does not change the service or `/etc/reptracker.env`: run the install command again.

- A Pi 5 needs the **Standard–Mini** camera cable (the camera comes with a Standard–Standard one). Power off before plugging it in.
- Check the camera before RepTracker:

```
rpicam-hello --list-cameras
rpicam-still -n -t 2000 -o /tmp/test.jpg
sudo -u reptracker rpicam-vid -n -t 3000 --codec mjpeg --mode 2304:1296 --width 1280 --height 720 --framerate 5 -o - | wc -c
timedatectl
```

The first must list `imx708`; the third prints about a million bytes (0: check group `video`); `timedatectl` must say the clock is synchronized.

- Filming a laptop screen about 30 cm away, a starting point (not yet tried on the Pi): Focus manual at 3.0, Exposure manual with shutter 16.7 ms and gain 1, White balance daylight. Until settings are saved in the form, `REPTRACKER_CAMERA_ARGS` in `/etc/reptracker.env` is used.
- Without a camera (any computer): `python app.py --camera test` replays a toy video as the live camera.
