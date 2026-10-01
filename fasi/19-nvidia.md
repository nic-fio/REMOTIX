# Fase 19 — NVIDIA sulla scheda

*Aperta il **1 ottobre 2026** (`DECISIONI.md` §10.27). Requisito dell'utente: su una macchina con una scheda
capace di codificare, REMOTIX codifica **sulla scheda**, NVIDIA compresa. Oggi su NVIDIA si ripiega sul
processore (OpenH264).*

## 1. La strada

| scheda | codifica |
|---|---|
| Intel, AMD | VA-API (com'è oggi, `src/vadiretta.c`) |
| NVIDIA | 🔸 **NVENC**, aperta a richiesta come OpenH264 (intestazioni MIT, libreria del driver) |
| nessuna scheda capace | processore (OpenH264, `src/ripiego.c`) |

## 2. Da decidere con l'utente
- 🔸 NVENC (proposta) contro Vulkan Video.
- ❓ Il ferro per provarla: una NVIDIA vera nel server, oppure ore di macchina in affitto.

## 3. Il registro delle modifiche — per il manuale tecnico

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
