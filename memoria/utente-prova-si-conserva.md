---
name: utente-prova-si-conserva
description: "On the server there is the user «prova» with a GNOME session without monitors of its own — it is kept, it serves future tests"
metadata: 
  node_type: memory
  type: project
  originSessionId: fdd77192-6559-451a-b716-757dd9b5b3a4
  modified: 2026-08-15T06:03:22.479Z
---

On the test machine (192.168.0.2) there is the user **`prova`** (uid 1001, password
`prova2026`, `enable-linger` on). ⭐ **Nic asked to keep it**: *«ci servirà
in seguito»* (14 Aug 2026).

Its graphical session is started with a drop-in
`~/.config/systemd/user/org.gnome.Shell@wayland.service.d/zz-senza-monitor.conf` that
launches `gnome-shell --headless --no-x11` ⛔ **without `--virtual-monitor`**.

**Why:** it is the only way, today, to see the **real desktop** inside REMOTIX. The product
creates the session with a monitor of its own (`sessione.c:650`) and then captures another one mounted by
`RecordVirtual` (`mutter.c:450`): the shell stays on the first and the user looks at the second,
empty. Without monitors of its own, the one from `RecordVirtual` is the only one and the shell goes onto it.

⛔⛔ **AND EVERY TEST USER MUST BE PUT IN THE `render` GROUP** — `usermod -aG render,video <utente>`.
`[M]` 14 Aug 2026: `prova` was not in it, so the **child** (which runs as that user) could not open
`/dev/dri/renderD128` and the encoder fell back to software **declaring it** — ⛔ **100 ms per
frame instead of 4.8**, twenty times. The symptom for the user is «it's slow», and the line that
explains it is in the log where nobody reads it. ⚠ The cure holds for **any** new test
user: `nicfio` is in `render` and `video` by itself, users created by hand are not.

**How to apply:** do not recreate the user or the session at every test — verify that it is
already there. And ⛔ **do not use `nicfio` for these tests**: it has a graphical session of its own, and
`SPECIFICHE.md` §5.1 allows only one per user.

⚠ **And that machine's clock is TWO HOURS behind** the laptop
(`[M]` 15 Aug 2026): the log's times are not yours, and comparing them without
knowing it makes you look for events in the wrong place.

⚠ **The machine suspends by itself**: `[M]` on 15 Aug the GNOME notification
«Automatic Suspend — Suspending soon because of inactivity» appeared **inside
the remote desktop**, in two screenshots. `sleep-inactive-ac-type` is `suspend` at
900 s, and the inhibition (`SessionManager.Inhibit`, `SUSPEND|IDLE`) **is not yet
written** — it is work for phase 5. A long test left alone can end up in
suspension without anyone connecting it to the result.

⚠ **And if the graphical session dies** (it happened on 14 Aug), it is brought back up from root with
`setpriv --reuid=1001 --regid=1001 --init-groups env -i … setsid --fork sh -c 'exec gnome-session
--session=gnome'` and the environment built from scratch (`XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`,
`XDG_SESSION_TYPE=wayland`). ⛔ **And then kill the product's child left without a stage**, or
invariant I2 will keep delivering the broken one at every login.

The detail is in `fasi/rapporti/F5-desktop-vero.md`; see also [[remotix-convenzioni]].
