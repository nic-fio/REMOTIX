# Fase 18 — REMOTIX senza ffmpeg

*Aperta dall'utente il **30 settembre 2026** (`DECISIONI.md` §10.22, §10.25). Nasce dalla licenza: REMOTIX sarà
sotto **PolyForm Noncommercial**, incompatibile con la libavcodec **GPL** delle distribuzioni. Togliendo ffmpeg
tutte le dipendenze di REMOTIX diventano permissive (MIT, BSD, Apache).*

## 1. Che cosa fa ffmpeg oggi, e con che cosa si sostituisce

| lavoro | oggi | domani | licenza |
|---|---|---|---|
| codifica sulla scheda | `h264_vaapi`, `hevc_vaapi` (libavcodec) | **libva diretta** (parametri, buffer, intestazioni del flusso scritte da REMOTIX) | MIT |
| ripiego software | `libx264`, `libx265`, `libsvtav1` | **OpenH264** (H.264), **SVT-AV1** diretta (AV1); ⛔ niente HEVC software | BSD |
| audio | encoder Opus via libavcodec | **libopus** diretta | BSD |
| conversione dei colori | libswscale | sulla scheda (VPP di VA-API); nel ripiego una libreria permissiva (libyuv) o codice nostro | BSD |

## 2. La condizione: indistinguibile, misurato

Il cambio entra **solo** se:
- la **suite funzionale della fase 15** completa è verde sulle **4 scatole** (GNOME, KDE, XFCE, LXQt) **in
  parallelo**, coi browser veri, in 4K;
- la **campagna della fase 16** (Intel, poi Radeon; una configurazione alla volta — le prestazioni non si
  misurano in parallelo) dà ritardo, fotogrammi e qualità **uguali** a quelli misurati con ffmpeg (`fasi/16`);
- il flusso che arriva al browser è dello stesso tipo di oggi (profili, livelli, intestazioni): la pagina non
  cambia.
Se non ci arriva: resta ffmpeg, e la licenza si riapre.

## 3. Le linee di lavoro, in parallelo

- **Linea V (video)**: libva diretta per H.264 e HEVC sulla scheda; OpenH264 e SVT-AV1 per il ripiego; la
  scelta del codificatore invariata per il browser.
- **Linea A (audio e colori)**: libopus diretta; la conversione dei colori senza libswscale.
- Poi: le prove (§2), l'installatore adeguato (niente libavcodec nelle dipendenze; su openSUSE con Intel
  Packman non serve più; Fedora continua a chiedere RPM Fusion per i driver), **T10** della fase 17.

## 4. Il registro delle modifiche — per il manuale tecnico

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
