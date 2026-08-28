---
name: remotix-metodo-documentazione
description: "REMOTIX — regola vincolante: si legge tutta la documentazione prima di scrivere codice, e si aggiornano i documenti nello stesso momento in cui una misura li smentisce"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aab51c1c-bc54-45fb-b6ac-36c9b5b96a98
  modified: 2026-08-06T04:53:19.975Z
---

In REMOTIX (`~/Documenti/REMOTIX`) vale una regola posta dall'utente: **non si scrive
una riga di codice senza aver prima letto la documentazione** — `PIANO.md`,
`SPECIFICA.md`, `REFERENCE.md` e i tre studi (`protocollo-rdp.md`,
`gnome-remote-desktop.md`, `client-android.md`, `xrdp-funzionalita.md`). All'inizio di
ogni fase l'utente lo ripete, e si aspetta che sia stato fatto davvero.

**Why:** i difetti che quei documenti raccolgono non danno errori: danno schermo nero,
disconnessione o immagine sbagliata, su un client su tre — e di norma su quello che non
si sta usando per provare.

**How to apply:** leggere i documenti per intero (non solo le sezioni indicate) prima di
toccare il codice; quando una misura contraddice un documento, **correggerlo subito**
con data e fonte, invece di annotarlo altrove. Il codice non è sul notebook: sta sul
server `192.168.0.2` in `/media/REMOTIX/src/remotix-c`, raggiungibile con
`strumenti/sshpw.py`. Vedi [[remotix-microfono-sospeso]].
