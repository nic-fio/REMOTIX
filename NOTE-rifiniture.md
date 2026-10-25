# Branch rifiniture: notes

## CSP connect-src narrowed to 'self' (page.c, commit 65c2c4cb)
What proves it: only a real browser opening the session, because the CSP is enforced by the engine, not by the server.
- benches/15-suite/15-f001-login-and-first-image.py (--box <desk> --browser chrome|firefox): login ends in ADMITTED
  and the first image shows, so the WebTransport to https://<host>/rcp/1 was allowed by connect-src. If the engine did
  not match 'self', the connect fails with a CSP error before any admission (the console is saved in the evidence).
- benches/15-suite/15-f004-the-mouse.py: the same session, plus the control traffic after the first image.
Run both on Chrome AND Firefox, at least on gnome and kde, with the final branch. Nothing at the server side (unit tests,
fuzz, curl) can show it: curl only sees the header text.
Also worth a look: the browser console of one run has no "Refused to connect ... Content Security Policy" line.
