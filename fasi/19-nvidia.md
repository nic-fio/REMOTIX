# Fase 19 — La codifica sempre sulla scheda: Vulkan per primo

*Aperta il **1 ottobre 2026** (`DECISIONI.md` §10.27). Requisito dell'utente: su una macchina con una scheda
capace di codificare, REMOTIX codifica **sulla scheda**, NVIDIA compresa. Oggi su NVIDIA si ripiega sul
processore (OpenH264).*

## 1. La strada (decisa il 1 ott, `DECISIONI.md` §10.27)

Si sceglie **per capacità**, all'avvio, non per marca:

| ordine | strada | oggi la usano |
|---|---|---|
| 1 | **Vulkan Video** (H.264 per Firefox, HEVC per Chrome) | AMD (RADV, `[M]` Mesa 25.0.7), NVIDIA (driver proprietario) |
| 2 | **VA-API** (`src/vadiretta.c`, com'è oggi) | Intel integrata e Arc (in Vulkan solo sperimentale, `[M]` Mesa 26.2.3) |
| — | ⛔ niente processore | senza scheda capace REMOTIX non si installa |

## 2. Il lavoro
1. La strada Vulkan (codifica H.264 e HEVC, copia zero da dmabuf, conversione dei colori sulla scheda), provata
   sulla Radeon contro VA-API: flusso dello stesso tipo, qualità e tempi non peggiori.
2. Via il ripiego software (`src/ripiego.c`, `src/colori709.c` se non serve più alla strada dalla memoria,
   OpenH264, SVT-AV1) dal prodotto, dai pacchetti, dal catalogo e dal motore dell'installatore; il controllo
   preliminare rifiuta senza una scheda capace, con la ragione.
3. Le prove: suite sulle 4 scatole (Intel = VA-API, Radeon = Vulkan); T10 ridotto al rifiuto pulito nelle VM, le
   prove complete nei contenitori con la scheda vera.
4. ❓ NVIDIA: serve una scheda vera (nel server, o macchina in affitto).

## 3. Il registro delle modifiche — per il manuale tecnico

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
