---
name: costruire-serve-il-contenitore
description: "Come si costruisce REMOTIX_V2: due strade, podman sul portatile per compilare ed enter.sh sulla macchina di prova per far girare"
metadata:
  node_type: memory
  type: project
  modified: 2026-08-14T23:13:10.891Z
  originSessionId: 704c141d-0a68-4975-8670-6223b9edf97e
---

✅ **Sciolto la notte del 15 agosto 2026, senza chiedere all'utente.** Il blocco
del 14 agosto («non riesco a costruire il C») era **un errore di percorso**:
dentro `bash /media/REMOTIX/enter.sh` il `/srv/src` che si vede **È**
`/media/REMOTIX/src` dell'host — l'`enter.sh` lo monta con `--bind`. I sorgenti
erano stati copiati in `/srv/src/...` **dell'host**, che è un'altra cartella.

⭐ **Due strade, e rispondono a due domande diverse:**

| domanda | strada |
|---|---|
| **«compila?»** — venti secondi, mentre si scrive | `bash src/costruisci-in-contenitore.sh` sul portatile: `podman` **da utente**, niente `sudo`, l'albero montato, il binario esce **dell'utente**. L'immagine si fa una volta: `podman build -t remotix-costruzione -f src/Contenitore src/` (~4 min: dentro ci sono ngtcp2 1.25 e nghttp3 1.18 dai sorgenti) |
| **«gira?»** — solo lì | sulla macchina di prova: `tar` dei sorgenti in `/media/REMOTIX/src/04-vero-src/`, poi `bash /media/REMOTIX/enter.sh --root 'bash /srv/src/04-vero-src/src/costruisci.sh'`, poi `sudo -S -p 'Password:' /media/REMOTIX/tmp/riavvia-7700.sh` |

⛔ **Il binario del contenitore NON si copia sulla macchina di prova**: è legato
a ngtcp2/nghttp3 di `/usr/local` **dentro l'immagine**, e là servono quelli di
`/media/REMOTIX/src/b2`. Il `riavvia-7700.sh` lo verifica e rifiuta di partire.

**Why:** «compila» non è «gira», e stanotte sono servite tutt'e due dieci volte:
si scrive e si compila sul portatile, si prova sulla macchina vera. La password
di `sudo` sulla macchina di prova è quella di `~/SERVER.ssh` e si passa con
`printf 'nicfio\n' | sudo -S -p 'Password: ' -v` **prima** di chiamare
`enter.sh`, senza redirezioni attorno a `enter.sh`.

**How to apply:** la pagina non ha bisogno di costruzione, si copia e basta —
ma il server va **riavviato**, perché `pagina.c` la legge una volta all'avvio.
E per leggere il registro: `sudo -S -p 'Password:' tail /media/REMOTIX/tmp/04-vero/registro.log`.

Vedi [[dex-mouse-aperto]] e `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md` §1.
