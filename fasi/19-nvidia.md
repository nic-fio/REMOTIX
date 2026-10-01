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
   preliminare rifiuta senza una scheda capace, con la ragione.  ⭐ Fatto dalla linea 1 (§3);
   `src/colori709.c` RESTA: serve alla strada «dalla memoria» di VA-API.
3. Le prove: suite sulle 4 scatole (Intel = VA-API, Radeon = Vulkan); T10 ridotto al rifiuto pulito nelle VM, le
   prove complete nei contenitori con la scheda vera.
4. ❓ NVIDIA: serve una scheda vera (nel server, o macchina in affitto).

## 3. Il registro delle modifiche — per il manuale tecnico

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| `9162e76` | **via il ripiego su CPU dal prodotto**: tolti `src/ripiego.c/.h` (OpenH264 via dlopen, SVT-AV1), il confine `sw_*` di `codificatore.c`, `codificatore_ripiego_software/_software_pronto/_software_rimedio`, `CRF_SOFTWARE`, `--software` di `--prova-codifica`, AV1 dal rilievo. `codificatore_di()` apre solo `h264_vaapi`/`hevc_vaapi`; un altro nome si rifiuta con la ragione. `--prova-codifica`: esito `hardware`\|`nessuno`, niente `rimedio`, codici **0** scheda · **1** si apre ma non esce · **2** uso · **3** nessuna scheda. All'avvio il server lo dichiara (*«QUESTO SERVER NON SA CODIFICARE VIDEO»*, con la ragione per codec) e l'`ECCOMI` non offre codec. Makefile: via openh264/SvtAv1Enc da CFLAGS, LIBS, `MINIMI` e intestazioni controllate (`-ldl` resta: libselinux in `figlio.c`). `colori709.c` RESTA (strada «dalla memoria»). Contenitori di costruzione e scatole senza le due librerie; `costruisci-tutti.sh` rifiuta un `ldd` che le nomina. Banchi 18-*: compilano senza `src/ripiego.c` (18-software lo prende da git `6bacca7`, come storia) | `DECISIONI.md` §10.27: *«niente cpu senza scheda»*, *«eliminare la questione della codifica su cpu senza scheda»*, indipendenza da ffmpeg e altri pezzi per le licenze | `[M]` 1 ott, sul server (`/media/REMOTIX/src/f19-cpu`): `--prova-codifica` Intel renderD128 H.264 e HEVC = `hardware`, codice 0; Radeon renderD129 H.264 e HEVC = `hardware`, codice 0; `--nodo /dev/dri/renderD199` = `nessuno`, codice **3**; `--software` = uso, codice 2. Server su 7633 col driver VA nascosto (`LIBVA_DRIVERS_PATH` vuota): riga ⛔⛔ all'avvio, `offerti` vuoto; con la scheda `«hevc,h264»`. `ldd` del binario (contenitore) senza openh264/SvtAv1 | no |
| `35e3b44` | **via OpenH264 e SVT-AV1 dai pacchetti**: `debian/control` (Build-Depends, Recommends `libopenh264-8 \| libopenh264-cisco8`), `remotix.spec` (BuildRequires, `Recommends: openh264` su Fedora e Alma), `PKGBUILD` (depends `openh264`, `svt-av1`), il testo delle licenze | come sopra | — (si costruiscono col rilascio) | no |
