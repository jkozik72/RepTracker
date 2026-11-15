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

LOG=/var/log/reptracker-install.log
TOTAL=7
STEP=0
RUN_PID=""
TTY=0; [ -t 1 ] && TTY=1
if [ "$(locale charmap 2>/dev/null)" = "UTF-8" ]; then
  FULL="█"; EMPTY="░"; SPIN=(⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏); OK="✓"
else
  FULL="#"; EMPTY="-"; SPIN=('|' '/' '-' '\'); OK="ok"
fi
GREEN=$'\033[1;32m'; RED=$'\033[1;31m'; DIM=$'\033[2m'; OFF=$'\033[0m'
[ "$TTY" = 1 ] || { GREEN=""; RED=""; DIM=""; OFF=""; }

bar() {   # bar <done> <total>: [██████░░░░░░]
  local width=24 filled i out=""
  filled=$(( $1 * width / $2 ))
  for ((i = 0; i < width; i++)); do if [ "$i" -lt "$filled" ]; then out+="$FULL"; else out+="$EMPTY"; fi; done
  printf '%s' "$out"
}
# step <title>: the next of the TOTAL steps, with the overall progress bar
step() {
  STEP=$((STEP + 1))
  printf '\n%s[%s]%s %d/%d  %s\n' "$GREEN" "$(bar $((STEP - 1)) "$TOTAL")" "$OFF" "$STEP" "$TOTAL" "$*"
}
elapsed() { local s=$(( $(date +%s) - $1 )); if [ "$s" -ge 60 ]; then printf '%dm%02ds' $((s / 60)) $((s % 60)); else printf '%ds' "$s"; fi; }
# run <what> <command...>: runs the command with its output in $LOG; on a terminal, a spinner, the time so far
# and the command's latest output line. On failure, shows the end of the log and stops.
run() {
  local what="$1" start rc=0 i=0 cols last note
  shift
  start=$(date +%s)
  echo "--- $what: $*" >> "$LOG"
  "$@" >> "$LOG" 2>&1 < /dev/null &
  RUN_PID=$!
  if [ "$TTY" = 1 ]; then
    cols=$(tput cols 2>/dev/null || echo 80)
    while kill -0 "$RUN_PID" 2>/dev/null; do
      last=$(tail -n 1 "$LOG" 2>/dev/null | tr -d '\r' | tr -s ' ')
      note=""
      if tail -n 3 "$LOG" | grep -qi "waiting for cache lock\|could not get lock"; then note=" (waiting for the Pi's own updates to finish)"; last=""; fi
      printf '\r\033[K  %s %s %s%s%s' "${SPIN[i % ${#SPIN[@]}]}" "$what" "$(elapsed "$start")" "$note" \
        "$( [ -n "$last" ] && printf '  %s' "$DIM${last:0:$(( cols > 60 ? cols - ${#what} - 20 : 20 ))}$OFF" )"
      i=$((i + 1))
      sleep 0.2
    done
  fi
  wait "$RUN_PID" || rc=$?
  RUN_PID=""
  [ "$TTY" = 1 ] && printf '\r\033[K'
  if [ "$rc" -ne 0 ]; then
    printf '  %s✗ %s%s (failed after %s)\n\n' "$RED" "$what" "$OFF" "$(elapsed "$start")"
    awk '/^--- /{buf=""} {buf=buf $0 ORS} END{printf "%s", buf}' "$LOG" | tail -n 15 | sed 's/^/    /'   # this step's output
    die "That step failed. The whole log is in $LOG. Running the same command again picks up where it stopped."
  fi
  printf '  %s%s%s %s %s(%s)%s\n' "$GREEN" "$OK" "$OFF" "$what" "$DIM" "$(elapsed "$start")" "$OFF"
}
done_line() { printf '  %s%s%s %s\n' "$GREEN" "$OK" "$OFF" "$*"; }
say() { printf '  %s\n' "$*"; }
die() { printf '\n%sError:%s %s\n' "$RED" "$OFF" "$*" >&2; exit 1; }
trap '[ -n "$RUN_PID" ] && kill "$RUN_PID" 2>/dev/null; printf "\n"; exit 130' INT TERM

ORIG_ARGS=("$@")
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

# GitHub's raw file links are cached for about 5 minutes, so a just-pushed fix may not be in the copy that
# curl fetched. Ask GitHub's API for the branch's latest commit (not cached) and, if this copy is older,
# run that commit's installer instead. Any failure here just carries on with this copy.
if [ -z "${REPTRACKER_FRESH:-}" ] && [ "$REPO" = "https://github.com/jkozik72/RepTracker.git" ] && command -v curl >/dev/null; then
  REF=$BRANCH
  [ -n "$REF" ] || REF=$(git -C "$APP" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  REF=${REF:-main}
  SHA=$(curl -fsS --max-time 10 -H "Accept: application/vnd.github.sha" "https://api.github.com/repos/jkozik72/RepTracker/commits/$REF" 2>/dev/null || true)
  if printf '%s' "$SHA" | grep -Eq '^[0-9a-f]{40}$'; then
    FRESH=$(mktemp)
    if curl -fsS --max-time 30 "https://raw.githubusercontent.com/jkozik72/RepTracker/$SHA/src/pi/install.sh" -o "$FRESH" 2>/dev/null        && [ -s "$FRESH" ] && ! cmp -s "$FRESH" "${BASH_SOURCE[0]:-/dev/null}"; then
      REPTRACKER_FRESH=1 exec bash "$FRESH" "${ORIG_ARGS[@]}"
    fi
    rm -f "$FRESH"
  fi
fi
: > "$LOG"
printf '%sInstalling RepTracker%s  (details: %s)\n' "$GREEN" "$OFF" "$LOG"

step "System packages: git, Python, ffmpeg, avahi (for the .local name)"
export DEBIAN_FRONTEND=noninteractive
# A fresh Pi often runs its automatic updates (unattended-upgrades) for a few minutes after boot, holding
# apt's lock. Wait for it (up to 15 min) instead of failing.
APT=(apt-get -o DPkg::Lock::Timeout=900)
run "Reading the package lists" "${APT[@]}" update
run "Installing packages (the first time: a few minutes)" "${APT[@]}" install -y git python3 python3-venv python3-pip ffmpeg avahi-daemon ca-certificates sudo

PY_OK=$(python3 -c 'import sys; print(int(sys.version_info >= (3, 11)))')
[ "$PY_OK" = 1 ] || die "RepTracker needs Python 3.11 or newer; this system has $(python3 --version). Use Raspberry Pi OS Bookworm or newer."

step "The reptracker system user"
id -u "$NAME" >/dev/null 2>&1 || useradd --system --home-dir "$HOME_DIR" --shell /usr/sbin/nologin "$NAME"
install -d -o "$NAME" -g "$NAME" -m 750 "$HOME_DIR"
as_app() { runuser -u "$NAME" -- "$@"; }
done_line "User $NAME, home $HOME_DIR"

if [ -d "$APP/.git" ]; then
  [ -n "$BRANCH" ] || BRANCH=$(as_app git -C "$APP" rev-parse --abbrev-ref HEAD)
  step "Updating RepTracker to branch $BRANCH"
  run "Fetching from GitHub" as_app git -C "$APP" fetch --prune origin
  as_app git -C "$APP" rev-parse --verify --quiet "origin/$BRANCH" >/dev/null || die "No branch \"$BRANCH\" on GitHub."
  # Tracked files follow the branch. Untracked and git-ignored files (Main data, profiles, account, keys) stay.
  run "Switching to $BRANCH" as_app git -C "$APP" checkout -q -f -B "$BRANCH" "origin/$BRANCH"
else
  BRANCH=${BRANCH:-main}
  step "Downloading RepTracker ($BRANCH)"
  run "Cloning into $APP" as_app git clone --progress --branch "$BRANCH" "$REPO" "$APP"
fi

step "Python packages"
[ -x "$VENV/bin/python" ] || run "Making the Python environment" as_app python3 -m venv "$VENV"
run "Updating pip" as_app "$VENV/bin/pip" install --upgrade pip
run "Installing RepTracker's packages (the first time: a few minutes)" as_app "$VENV/bin/pip" install -r "$APP/src/website/requirements.txt"

step "Settings and the admin command"
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

done_line "Settings in $ENV_FILE"
install -o root -g root -m 755 "$APP/src/pi/reptracker-admin" /usr/local/sbin/reptracker-admin
SUDOERS=$(mktemp)
echo "$NAME ALL=(root) NOPASSWD: /usr/local/sbin/reptracker-admin" > "$SUDOERS"
visudo -cqf "$SUDOERS" || die "The sudo rule did not validate."
install -o root -g root -m 440 "$SUDOERS" /etc/sudoers.d/reptracker
rm -f "$SUDOERS"
touch "$HOME_DIR/task.log"; chown root:"$NAME" "$HOME_DIR/task.log"; chmod 644 "$HOME_DIR/task.log"
done_line "reptracker-admin and its sudo rule"

step "The computer's name"
if [ "$KEEP_HOSTNAME" = 0 ] && [ "$(hostname)" != "$NAME" ]; then
  OLD=$(hostname)
  if command -v hostnamectl >/dev/null && [ "$HAS_SYSTEMD" = 1 ]; then hostnamectl set-hostname "$NAME"; else echo "$NAME" > /etc/hostname; hostname "$NAME" 2>/dev/null || true; fi
  if grep -q '^127\.0\.1\.1' /etc/hosts; then sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$NAME/" /etc/hosts; else printf '127.0.1.1\t%s\n' "$NAME" >> /etc/hosts; fi
  [ "$HAS_SYSTEMD" = 1 ] && systemctl restart avahi-daemon || true
  done_line "Renamed \"$OLD\" to \"$NAME\", so the address is https://$NAME.local (uninstalling gives the old name back)"
else
  done_line "Keeping the name \"$(hostname)\""
fi

if [ "$HAS_SYSTEMD" = 1 ]; then
  step "Starting the service"
  install -o root -g root -m 644 "$APP/src/pi/reptracker.service" /etc/systemd/system/reptracker.service
  systemctl daemon-reload
  systemctl enable -q reptracker
  systemctl restart reptracker
  run "Waiting for RepTracker to start" sleep 3
  systemctl is-active -q reptracker || die "The service did not start. See:  sudo journalctl -u reptracker -n 50"
  done_line "reptracker.service is running and starts at boot"
else
  step "No systemd here: start it yourself with"
  echo "   sudo -u $NAME env \$(grep -v '^#' $ENV_FILE | xargs) $VENV/bin/python $APP/src/website/app.py --lan --port $PORT"
fi

HOST=$(hostname)
PORT_PART=""; [ "$PORT" = 443 ] || PORT_PART=":$PORT"
printf '\n%s[%s]%s Done. RepTracker is installed (%s, %s)\n' "$GREEN" "$(bar 1 1)" "$OFF" "$BRANCH" "$(as_app git -C "$APP" log -1 --format='%h %s')"
echo "   Open  https://$HOST.local$PORT_PART  (or https://<this Pi's IP>$PORT_PART)"
for ip in $(hostname -I 2>/dev/null); do case "$ip" in *:*) ;; *) echo "         https://$ip$PORT_PART" ;; esac; done
echo "   The browser warns once about the self-signed certificate; the first visit creates the sign-in account."
echo "   Update, restart or uninstall in Settings, or:  sudo reptracker-admin help"
