---
name: remotix-metodo-documentazione
description: "REMOTIX — binding rule: all the documentation is read before writing code, and the documents are updated at the same moment a measurement disproves them"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aab51c1c-bc54-45fb-b6ac-36c9b5b96a98
  modified: 2026-08-06T04:53:19.975Z
---

In REMOTIX (`~/Documenti/REMOTIX`) a rule set by the user applies: **not a line of code
is written without first having read the documentation** — `PIANO.md`,
`SPECIFICA.md`, `REFERENCE.md` and the three studies (`protocollo-rdp.md`,
`gnome-remote-desktop.md`, `client-android.md`, `xrdp-funzionalita.md`). At the start of
every phase the user repeats it, and expects it to have really been done.

**Why:** the defects those documents collect do not give errors: they give a black screen,
disconnection or a wrong image, on one client out of three — and usually on the one that is not
being used for testing.

**How to apply:** read the documents in full (not only the indicated sections) before
touching the code; when a measurement contradicts a document, **correct it at once**
with date and source, instead of noting it elsewhere. The code is not on the notebook: it is on the
server `192.168.0.2` in `/media/REMOTIX/src/remotix-c`, reachable with
`strumenti/sshpw.py`. See [[remotix-microfono-sospeso]].
