#!/usr/bin/env bash
# Install or update RepTracker on a Raspberry Pi (or any Debian-based Linux with systemd).
#
#   curl -fsSL https://raw.githubusercontent.com/jkozik72/RepTracker/main/src/pi/install.sh | sudo bash
#
# Options (after "sudo bash -s --"):
#   --branch <name>    the branch to run (default: main, or the one already installed)
#   --port <n>         the HTTPS port (default 443, so the address needs no port)
#   --keep-hostname    don't rename this computer to "reptracker"
#   --repo <url>       clone from another repository
#
# Running it again updates RepTracker and keeps all its data (animals, profiles, account, keys).
# What it sets up:
#   /opt/reptracker/app        the repository (owned by the "reptracker" system user)
#   /opt/reptracker/venv       its Python packages
#   /etc/reptracker.env        settings for the service
#   reptracker.service         starts at boot, restarts if it stops
#   /usr/local/sbin/reptracker-admin   update, restart, uninstall (also used by the Settings tab)
set -euo pipefail

INSTALLER_VERSION=1
REPO="https://github.com/jkozik72/RepTracker.git"
BRANCH=""
PORT=443
PORT_SET=0
KEEP_HOSTNAME=0
NAME=reptracker
HOME_DIR=/opt/reptracker
APP="$HOME_DIR/app"
VENV="$HOME_DIR/venv"
ENV_FILE=/etc/reptracker.env

say() { printf '\n\033[1;32m==>\033[0m %s\n' "$*"; }
die() { printf '\n\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --port) PORT="${2:-}"; PORT_SET=1; shift 2 ;;
    --keep-hostname) KEEP_HOSTNAME=1; shift ;;
    --repo) REPO="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0" 2>/dev/null || true; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
done

[ "$(id -u)" -eq 0 ] || die "Run it with sudo:  curl -fsSL <this script's URL> | sudo bash"
command -v apt-get >/dev/null || die "This installer needs a Debian-based system (Raspberry Pi OS, Debian, Ubuntu)."
case "$PORT" in ''|*[!0-9]*) die "--port must be a number." ;; esac
if [ -n "$BRANCH" ] && ! printf '%s' "$BRANCH" | grep -Eq '^[A-Za-z0-9._][A-Za-z0-9._/-]{0,99}$'; then
  die "Not a valid branch name: $BRANCH"
fi
HAS_SYSTEMD=0; [ -d /run/systemd/system ] && HAS_SYSTEMD=1

say "Installing system packages (git, Python, ffmpeg, avahi for the .local name)"
export DEBIAN_FRONTEND=noninteractive
# A fresh Pi often runs its automatic updates (unattended-upgrades) for a few minutes after boot, holding
# apt's lock. Wait for it (up to 15 min) instead of failing.
if fuser /var/lib/dpkg/lock-frontend /var/lib/apt/lists/lock >/dev/null 2>&1; then
  echo "   The Pi is installing its own updates; waiting for them to finish (this can take a few minutes)..."
fi
APT=(apt-get -o DPkg::Lock::Timeout=900)
"${APT[@]}" update -qq
"${APT[@]}" install -y -qq git python3 python3-venv python3-pip ffmpeg avahi-daemon ca-certificates sudo >/dev/null

PY_OK=$(python3 -c 'import sys; print(int(sys.version_info >= (3, 11)))')
[ "$PY_OK" = 1 ] || die "RepTracker needs Python 3.11 or newer; this system has $(python3 --version). Use Raspberry Pi OS Bookworm or newer."

say "Creating the reptracker system user"
id -u "$NAME" >/dev/null 2>&1 || useradd --system --home-dir "$HOME_DIR" --shell /usr/sbin/nologin "$NAME"
install -d -o "$NAME" -g "$NAME" -m 750 "$HOME_DIR"
as_app() { runuser -u "$NAME" -- "$@"; }

if [ -d "$APP/.git" ]; then
  [ -n "$BRANCH" ] || BRANCH=$(as_app git -C "$APP" rev-parse --abbrev-ref HEAD)
  say "Updating $APP to branch $BRANCH"
  as_app git -C "$APP" fetch --prune origin
  as_app git -C "$APP" rev-parse --verify --quiet "origin/$BRANCH" >/dev/null || die "No branch \"$BRANCH\" on GitHub."
  # Tracked files follow the branch. Untracked and git-ignored files (Main data, profiles, account, keys) stay.
  as_app git -C "$APP" checkout -q -f -B "$BRANCH" "origin/$BRANCH"
else
  BRANCH=${BRANCH:-main}
  say "Downloading RepTracker ($BRANCH) into $APP"
  as_app git clone -q --branch "$BRANCH" "$REPO" "$APP"
fi

say "Installing Python packages (a few minutes the first time)"
[ -x "$VENV/bin/python" ] || as_app python3 -m venv "$VENV"
as_app "$VENV/bin/pip" install -q --upgrade pip
as_app "$VENV/bin/pip" install -q -r "$APP/src/website/requirements.txt"

say "Writing $ENV_FILE"
ORIGINAL_HOSTNAME=$(hostname)
if [ -f "$ENV_FILE" ]; then
  # Keep earlier choices (port, the hostname to give back on uninstall), add anything new.
  ORIGINAL_HOSTNAME=$(sed -n 's/^REPTRACKER_ORIGINAL_HOSTNAME=//p' "$ENV_FILE" | head -1)
  OLD_PORT=$(sed -n 's/^REPTRACKER_PORT=//p' "$ENV_FILE" | head -1)
  if [ -n "$OLD_PORT" ] && [ "$PORT_SET" = 0 ]; then PORT=$OLD_PORT; fi
fi
REDIRECT=80; [ "$PORT" = 80 ] && REDIRECT=0
cat > "$ENV_FILE" <<EOF
# RepTracker settings, read by reptracker.service.
# After changing one:  sudo systemctl restart reptracker
REPTRACKER_PORT=$PORT
# Plain-HTTP port that only redirects to HTTPS (0 = off)
REPTRACKER_HTTP_REDIRECT=$REDIRECT
REPTRACKER_MANAGED=1
REPTRACKER_HOME=$HOME_DIR
REPTRACKER_INSTALLER_VERSION=$INSTALLER_VERSION
REPTRACKER_ORIGINAL_HOSTNAME=${ORIGINAL_HOSTNAME:-raspberrypi}
IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg
EOF
chmod 644 "$ENV_FILE"

say "Installing the admin command and its sudo rule"
install -o root -g root -m 755 "$APP/src/pi/reptracker-admin" /usr/local/sbin/reptracker-admin
SUDOERS=$(mktemp)
echo "$NAME ALL=(root) NOPASSWD: /usr/local/sbin/reptracker-admin" > "$SUDOERS"
visudo -cqf "$SUDOERS" || die "The sudo rule did not validate."
install -o root -g root -m 440 "$SUDOERS" /etc/sudoers.d/reptracker
rm -f "$SUDOERS"
touch "$HOME_DIR/task.log"; chown root:"$NAME" "$HOME_DIR/task.log"; chmod 644 "$HOME_DIR/task.log"

if [ "$KEEP_HOSTNAME" = 0 ] && [ "$(hostname)" != "$NAME" ]; then
  say "Renaming this computer to \"$NAME\" (so the address is https://$NAME.local)"
  OLD=$(hostname)
  if command -v hostnamectl >/dev/null && [ "$HAS_SYSTEMD" = 1 ]; then hostnamectl set-hostname "$NAME"; else echo "$NAME" > /etc/hostname; hostname "$NAME" 2>/dev/null || true; fi
  if grep -q '^127\.0\.1\.1' /etc/hosts; then sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$NAME/" /etc/hosts; else printf '127.0.1.1\t%s\n' "$NAME" >> /etc/hosts; fi
  [ "$HAS_SYSTEMD" = 1 ] && systemctl restart avahi-daemon || true
  echo "   (was \"$OLD\"; uninstalling gives the old name back)"
fi

if [ "$HAS_SYSTEMD" = 1 ]; then
  say "Starting the reptracker service"
  install -o root -g root -m 644 "$APP/src/pi/reptracker.service" /etc/systemd/system/reptracker.service
  systemctl daemon-reload
  systemctl enable -q reptracker
  systemctl restart reptracker
  sleep 3
  systemctl is-active -q reptracker || die "The service did not start. See:  sudo journalctl -u reptracker -n 50"
else
  say "No systemd here: start it yourself with"
  echo "   sudo -u $NAME env \$(grep -v '^#' $ENV_FILE | xargs) $VENV/bin/python $APP/src/website/app.py --lan --port $PORT"
fi

HOST=$(hostname)
PORT_PART=""; [ "$PORT" = 443 ] || PORT_PART=":$PORT"
say "RepTracker is installed ($BRANCH, $(as_app git -C "$APP" log -1 --format='%h %s'))"
echo "   Open  https://$HOST.local$PORT_PART  (or https://<this Pi's IP>$PORT_PART)"
for ip in $(hostname -I 2>/dev/null); do case "$ip" in *:*) ;; *) echo "         https://$ip$PORT_PART" ;; esac; done
echo "   The browser warns once about the self-signed certificate; the first visit creates the sign-in account."
echo "   Update, restart or uninstall in Settings, or:  sudo reptracker-admin help"
