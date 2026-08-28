---
name: documentazione-v1-misurata
description: "~/Documenti/REMOTIX è la documentazione di v1 (600 KB di misure): si legge PRIMA di rifare una cosa che in v1 funzionava"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 779c5805-3064-4996-b3bd-0230542c5ee9
  modified: 2026-08-17T10:00:01.747Z
---

`~/Documenti/REMOTIX/` — **non** è codice, è la **documentazione di v1**, e
porta misure che in V2 non sono state rifatte:

| file | che cosa contiene |
|---|---|
| `REFERENCE.md` (168 KB) | le regole misurate: **R25** il ritmo dei blocchi audio, **R26** la priorità di tempo reale, R27 il codificatore hardware, R24 il segno del PCM |
| `SPECIFICA.md` (134 KB) | §7.5 il sink virtuale creato da noi |
| `PIANO.md`, `LEZIONI.md` | le fasi di v1 e il metodo |
| `protocollo-rdp.md`, `xrdp-funzionalita.md` | il protocollo morto, tenuto per le lezioni |

⛔ **R26 è quella che è costata di più a non leggerla**: un processo con
`RLIMIT_RTPRIO` a zero non può chiedere `SCHED_FIFO`, PipeWire se la vede
negare, e il sintomo è **audio che scoppietta quando il desktop lavora** —
invisibile a ogni controllo sul filo. Si concede nell'**unità systemd**
(`LimitRTPRIO=20`, `LimitNICE=-11`), non nel codice.

**Why:** il 17 agosto 2026 ho inseguito per ore un difetto dell'audio che v1
aveva già misurato e scritto il 5 agosto. È stato Nic a dire *«nella prima
versione l'audio funzionava, esamina quella cartella»*.

**How to apply:** è il **punto 0 della ricetta** di `LEZIONI.md` §9 — *«chi, al
mondo, fa già questa cosa?»* — nella variante che conta di più: **chi, in casa
nostra, l'ha già risolta?** Prima di scrivere un pezzo che v1 aveva, si cerca
qui. ⚠ Il codice di v1 sta altrove (`REMOTIX/v1/remotix-c/src/`): questa
cartella sono le **misure**.

Vedi [[misura-anche-chi-ascolta]], [[remotix-convenzioni]].
