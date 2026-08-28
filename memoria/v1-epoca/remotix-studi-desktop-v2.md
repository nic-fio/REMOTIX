---
name: remotix-studi-desktop-v2
description: "REMOTIX, 8 agosto 2026: XFCE e LXQt studiati a fondo; i quattro studi dei desktop vivono ora in ~/Documenti/REMOTIX_V2, e la sessione si è trasformata in brainstorming"
metadata: 
  node_type: memory
  type: project
  originSessionId: 138511ec-a8d5-41e8-aa33-68bf30c9b950
  modified: 2026-08-08T19:43:25.521Z
---

L'8 agosto 2026, dopo la chiusura di KDE, sono stati fatti **tre studi nuovi con dieci subagenti
ciascuno**: `xfce.md` (labwc/wlroots, ~10 700 righe di rapporti), `lxqt.md` (~6 200) e **`gnome.md`
(~7 200)** — quest'ultimo perché `gnome-remote-desktop.md` studiava **il server RDP di GNOME, non il
desktop**. ⚠ **Nessuno dei tre è misurato**: sono letture di codice, e ognuno finisce col proprio
piano di misure.

⛔ **Lo studio di GNOME ha trovato più difetti nostri degli altri due insieme, sul desktop che
serviamo in produzione.** I tre che pesano: (1) **R29 è sbagliata** — il DMA-BUF di Mutter **non è un
diff** (la vista virtuale è un `CoglOffscreen` persistente e il blit copia tutto), quindi la
superficie di accumulo peggiorava le cose; il difetto vero è il **release** (`can_reuse_pw_buffer` si
arrende senza `SPA_META_SyncTimeline` e riusa il buffer mentre VA-API legge). (2) **Il blocco schermo
di GNOME non mostra uno schermo: chiama `inhibit_remote_access()` e ci STACCA la sessione RDP** —
l'eccezione è `is_headless()`, che oggi abbiamo **per accidente** (Mutter si degrada da sé senza
seat), non perché l'abbiamo chiesto. (3) **La macchina si sospende da sola a 900 s** (default
`sleep-inactive-ac-type=suspend`); cura: `SessionManager.Inhibit(…, 4|8)`. Più: `EI_EVENT_KEYBOARD_MODIFIERS`
**non arriva nemmeno su GNOME** (i nostri documenti dicevano il contrario in due punti), la clipboard
**non è della sessione** ma di Mutter, e il client può sospendere gli ack con
`queueDepth == 0xFFFFFFFF` — da verificare nel nostro regolatore.

**Dove stanno**: l'utente ha chiesto di spostare tutta la documentazione dei desktop in
**`~/Documenti/REMOTIX_V2`** — `gnome-remote-desktop.md`, `kde.md`, `xfce.md`, `lxqt.md` e le cartelle
`reference-kde/`, `reference-xfce/`, `reference-lxqt/`. In `~/Documenti/REMOTIX` restano `PIANO.md`,
`SPECIFICA.md`, `REFERENCE.md`, `LEZIONI.md`, i tre studi vecchi e `strumenti/`. In REMOTIX_V2
l'utente ha messo di suo `INIZIO.md`, `CODER.md`, `REVIEWER.md` (non letti).

⭐ **Il risultato che conta più di tutti**: l'asse è **il compositore, non il desktop**. Le
combinazioni desktop×compositore realistiche su Trixie sono **9**; oggi ne sono coperte 2, e **dopo
la sola fase wlroots diventano 8 su 9** — LXQt ne porta quattro **senza una riga di codice nuovo**,
perché gira sullo stesso labwc di XFCE (o su KWin, che è già fatto).

⛔ **E il fatto che ha cambiato la fase LXQt**: su Debian Trixie **una sessione LXQt-Wayland non
esiste come pacchetto** (`lxqt-wayland-session` è in forky/sid, non in Trixie) — ma il codice Wayland
è compilato e spedito: manca **solo il lanciatore**, che REMOTIX si scrive da sé. Da qui una lezione
per la ricetta: **passo zero-bis, «questo desktop, su questa distribuzione, ha una sessione
Wayland?»** — due comandi, e vanno fatti prima di studiare.

**Lo stato della sessione**: l'utente ha dichiarato che *«questa sessione si trasforma da sviluppo a
brainstorming»* e che ha **intenzione di rivoluzionare il progetto**, dicendolo a studio completo.
Per questo `PIANO.md`, `SPECIFICA.md`, `REFERENCE.md` e `LEZIONI.md` **non sono stati aggiornati**
con i due studi nuovi: l'aggiornamento è sospeso in attesa di quella decisione.

Vedi [[remotix-prossimo-kde]], [[remotix-lezioni]], [[remotix-metodo-documentazione]].
