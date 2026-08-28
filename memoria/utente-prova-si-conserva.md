---
name: utente-prova-si-conserva
description: "Sul server c'è l'utente «prova» con una sessione GNOME senza monitor propri — si conserva, serve alle prove future"
metadata: 
  node_type: memory
  type: project
  originSessionId: fdd77192-6559-451a-b716-757dd9b5b3a4
  modified: 2026-08-15T06:03:22.479Z
---

Sulla macchina di prova (192.168.0.2) esiste l'utente **`prova`** (uid 1001, parola
`prova2026`, `enable-linger` acceso). ⭐ **Nic ha chiesto di conservarlo**: *«ci servirà
in seguito»* (14 agosto 2026).

La sua sessione grafica è avviata con un drop-in
`~/.config/systemd/user/org.gnome.Shell@wayland.service.d/zz-senza-monitor.conf` che
lancia `gnome-shell --headless --no-x11` ⛔ **senza `--virtual-monitor`**.

**Why:** è l'unico modo, oggi, per vedere il **desktop vero** dentro REMOTIX. Il prodotto
crea la sessione con un monitor suo (`sessione.c:650`) e poi ne cattura un altro montato da
`RecordVirtual` (`mutter.c:450`): la shell resta sul primo e l'utente guarda il secondo,
vuoto. Senza monitor propri, quello di `RecordVirtual` è l'unico e la shell ci va sopra.

⛔⛔ **E OGNI UTENTE DI PROVA VA MESSO NEL GRUPPO `render`** — `usermod -aG render,video <utente>`.
`[M]` 14 agosto 2026: `prova` non c'era, quindi il **figlio** (che gira come lui) non poteva aprire
`/dev/dri/renderD128` e il codificatore ripiegava in software **dichiarandolo** — ⛔ **100 ms per
fotogramma invece di 4,8**, venti volte. Il sintomo per l'utente è «è lento», e la riga che lo
spiega sta nel registro dove nessuno la legge. ⚠ La cura vale per **qualunque** utente di prova
nuovo: `nicfio` è in `render` e `video` di suo, gli utenti creati a mano no.

**How to apply:** non ricreare l'utente né la sessione a ogni prova — verificare che ci sia
già. E ⛔ **non usare `nicfio` per queste prove**: ha una sessione grafica sua, e
`SPECIFICHE.md` §5.1 ne ammette una sola per utente.

⚠ **E l'orologio di quella macchina è indietro di DUE ORE** rispetto al portatile
(`[M]` 15 agosto 2026): le ore del registro non sono le tue, e confrontarle senza
saperlo fa cercare eventi nel posto sbagliato.

⚠ **La macchina si sospende da sola**: `[M]` 15 agosto la notifica di GNOME
«Automatic Suspend — Suspending soon because of inactivity» è comparsa **dentro
il desktop remoto**, in due schermate. `sleep-inactive-ac-type` vale `suspend` a
900 s, e l'inibizione (`SessionManager.Inhibit`, `SUSPEND|IDLE`) **non è ancora
scritta** — è lavoro della fase 5. Una prova lunga lasciata sola può finire in
sospensione senza che nessuno lo colleghi al risultato.

⚠ **E se la sessione grafica muore** (è successo il 14 agosto), si rimette in piedi da root con
`setpriv --reuid=1001 --regid=1001 --init-groups env -i … setsid --fork sh -c 'exec gnome-session
--session=gnome'` e l'ambiente composto da zero (`XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`,
`XDG_SESSION_TYPE=wayland`). ⛔ **E poi si uccide il figlio del prodotto rimasto senza palco**, o
l'invariante I2 continuerà a consegnare quello rotto a ogni login.

Il dettaglio sta in `fasi/rapporti/F5-desktop-vero.md`; vedi anche [[remotix-convenzioni]].
