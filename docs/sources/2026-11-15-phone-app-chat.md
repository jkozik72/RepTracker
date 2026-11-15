# Phone access, photos with questions, an installable app (chat messages, 2026-11-15)

Saved verbatim from a Claude Code chat with a team member, 2026-11-15.

> The webpage can't be reached from my android phone and im on the network

> yes add the QR code, make the web app more mobile friendly, and lets talk about making the app so it can be downloaded on a phone (what we talked about with the mailto)

> When I ask a question, there is a camera Icon to optionally take or attach an image, this replaces the image that is had from the video feed. and yes after this merge everything into main. I like option A but is it safe?

> Yes, build it

Context from the same chat: option A was "RepTracker's own certificate authority, installed once on each phone"; option B was Tailscale. The answer to "is it safe" proposed limiting the authority to RepTracker's own addresses (a name constraint), keeping its key on the Pi, and noted that Android only lets the browser use such certificates.
