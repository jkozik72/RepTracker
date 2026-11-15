---
source: docs/sources/2026-11-15-phone-alerts-chat.md
type: internal
date: 2026-11-15
digested: 2026-11-15
relates-to: [D9, D10]
---

# Phone alerts and the Research page on phones (chat message)

## Summary

How often RepTracker analyses on its own is set in Settings. Only alerts go to phones, and a notification reads the alerts. The Research profile page needs to work on a phone.

## Key points

- The schedule is a setting.
- Alerts only; notifications (neutral events) are not sent to phones for now.
- The notification's text is the alert itself.
- The Research profile page is not phone-friendly.

## Relevance

D10. Needs D9 (a phone must trust the server for push to work).

## Open questions

- The push contact: the project's page is used (`REPTRACKER_PUSH_CONTACT` overrides it); not confirmed by the team.
- Not yet tried on a real phone: subscribing, receiving and tapping a notification.

## Actions

- [x] Server-side schedule in Settings (off, 15 min to 6 h), Main mode, even with no page open
- [x] Alerts worked out on the server every minute; a new alert is pushed once
- [x] The notification reads the alert; tapping it opens that animal
- [x] Research profile page: tables become cards on phones, facts two per row
