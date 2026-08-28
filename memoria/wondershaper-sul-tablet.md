---
name: wondershaper-sul-tablet
description: "Per strozzare il PERCORSO VERO in fase 9 c'è wondershaper in ~/.local/bin sul tablet di Nic — non solo netem su lo"
metadata:
  type: reference
---

`wondershaper` sta in **`~/.local/bin` sul tablet** di Nic. Lo ha segnalato lui il 23 agosto 2026,
aprendo la fase 9.

**Why:** i banchi di rete esistenti strozzano con `tc netem` su **`lo`** della macchina di prova
(`banchi/07-b64-rete.py`, `banchi/07-b65-datagram.py`), e quella metà ha un limite **dichiarato**:
su `lo` la MTU è 65536, quindi non rimisura quanti byte porta davvero un datagram. Strozzando dal
lato del **client** si misura il percorso vero — WiFi, MTU vera, coda vera.

**How to apply:**
- serve alla fase 9 al **nuovo punto di lavoro: 20 Mbit/s**, il pavimento dichiarato
  (`DECISIONI.md` §3.1-bis) — non più i 2 Mbit/s che il piano diceva;
- vale l'isolamento di [[banchi-in-parallelo-isolamento]]: una regola di `tc` va rimossa anche se
  il copione muore, o resta addosso alla macchina;
- e resta [[la-prova-la-fa-lutente]]: strozzare serve a produrre la scena, il giudizio è suo.
