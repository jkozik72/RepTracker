---
source: docs/sources/2026-11-15-phone-app-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [D7, D8, D9]
---

# Phone access, photos with questions, an installable app (chat messages)

## Summary

An Android phone could not open `reptracker.local`. The team asked for a QR code, a phone-friendly layout, a camera button on questions (the photo replaces the video frame), and an app that can be installed on a phone. Of the two ways to give phones a certificate they trust, they chose RepTracker's own certificate authority (option A) over Tailscale, asked whether it is safe, and asked to build it.

## Key points

- (Message 1) Android: the site can't be reached by name on the home network.
- (Message 2) QR code, phone-friendly layout, an installable app.
- (Message 3) A camera icon on Ask to take or attach a photo; it replaces the camera picture.
- (Message 3) Option A (own certificate authority), if it is safe.
- (Message 4) Build it.

## Relevance

Sets how phones trust the server and install the app: D9. Push notifications, server-side analyses and the push contact (`mailto:` or a URL) are the next parts, not decided yet.

## Open questions

- Push notifications: contact for the push services (the repo's URL or an email), how often the Pi analyses on its own, alerts only or all notifications.
- Not yet tried on a real Android phone or iPhone: the certificate install steps and the install prompt.

## Actions

- [x] QR code and addresses in Settings (IP first)
- [x] Phone layout: readable charts, 40px controls, 16px fields
- [x] Ask: camera / attach button; photo replaces the camera picture
- [x] Own certificate authority, name-constrained; tests prove it can't vouch for other sites (D9)
- [x] Installable app: manifest, icons, service worker, offline page, install steps in Settings
