---
source: docs/sources/2026-11-15-pi-hosting-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [D7, D8]
---

# Phone access, hosting on a Raspberry Pi, a one-command install (chat messages)

## Summary

The team asked about phone access, an installable app and push notifications, then set web push aside. They chose to host RepTracker on a Raspberry Pi, installed with a single command, managed from the Settings tab (update to a given branch, restart, uninstall) and reachable under the name "reptracker".

## Key points

- (Message 1) Wanted: open RepTracker from a phone, install it as an app, get notifications on the phone.
- (Message 3) Web push: not now ("lets not do this").
- (Message 3) Host on a Pi; the whole program installed with a single command.
- (Message 4) Settings tab: update to a given branch, restart, uninstall.
- (Message 4) The site is named "reptracker".
- (Message 4) Merge the open work onto main first; the installer is a new PR.

## Relevance

Sets how RepTracker is deployed: D8. Builds on the sign-in and LAN HTTPS of D7.

## Open questions

- Not yet run on a real Pi: the installer was checked for syntax and the server, HTTPS and redirect were run on Windows, not on Raspberry Pi OS.
- Phone notifications (web push or ntfy) were set aside, not dropped.

## Actions

- [x] `src/pi/install.sh`: one command, also the update path; systemd service; hostname "reptracker" (https://reptracker.local)
- [x] `reptracker-admin` and Settings: update to a branch, restart, uninstall (keeps a data backup unless asked)
- [x] cheroot as the LAN server, an HTTP-to-HTTPS redirect, the `.local` name in the certificate
- [x] D8
