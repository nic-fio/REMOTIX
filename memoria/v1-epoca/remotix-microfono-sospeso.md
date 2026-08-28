---
name: remotix-microfono-sospeso
description: "REMOTIX — il microfono (fase 8, voce 4, MS-RDPEAI) è sospeso per decisione dell'utente dal 6 agosto 2026"
metadata: 
  node_type: memory
  type: project
  originSessionId: aab51c1c-bc54-45fb-b6ac-36c9b5b96a98
  modified: 2026-08-06T04:53:09.136Z
---

Nel progetto REMOTIX la voce 4 della fase 8 — **microfono, MS-RDPEAI** — è **sospesa
per decisione esplicita dell'utente (6 agosto 2026)**: non si scrive finché non sarà
lui a dirlo. Le voci 0, 1 e 2 (sink virtuale, audio in uscita PCM, appunti) sono chiuse
e misurate; la fase 8 non resta aperta per questo.

**Why:** l'utente decide le funzionalità e il loro ordine; la sospensione è una scelta
di priorità, non un blocco tecnico.

**How to apply:** non proporre né iniziare il canale `AUDIO_INPUT`; se un lavoro lo
sfiora, fermarsi e chiedere. Annotato anche in `PIANO.md`, fase 8. Vedi
[[remotix-metodo-documentazione]].
