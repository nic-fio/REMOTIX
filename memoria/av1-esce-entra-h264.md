---
name: av1-esce-entra-h264
description: "17 ago 2026, deciso dall'utente: AV1 esce dal prodotto, entra H.264 — Firefox Android non ha né HEVC né AV1, e qui l'AV1 è l'unico codec senza hardware"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6917bf53-6d6d-42bb-8bd5-f1d628833c28
  modified: 2026-08-17T17:37:11.600Z
---

⛔⛔ **Deciso dall'utente il 17 agosto 2026**: *«la scelta è obbligata: dobbiamo
abbandonare AV1»*, e il sostituto scelto è **H.264**.

**La causa, ed è sua**: **Firefox per Android non supporta né HEVC né AV1.**
⇒ Per quel browser il prodotto non esisteva, il che contraddice la riga
d'apertura del `README` — *«nessun client da installare, basta un browser
moderno»*.

**E la misura che la conferma** (`vainfo` sul CHUWI, 17 ago):

| codec | decodifica sul tablet | Firefox | codifica sul server |
|---|---|---|---|
| HEVC | ⭐ hardware | ⛔ **no** | ⭐ hardware, 3,16 ms |
| AV1 | ⛔ **nessun profilo** | sì | ⛔ **non esiste**, solo software |
| H.264 | ⭐ hardware | sì | ⭐ hardware, **3,11 ms** (il più veloce) |
| VP9 | ⭐ hardware | sì | ⭐ hardware, 6,95-7,28 ms |

⇒ AV1 era **l'unico codec senza hardware da nessuna parte** in questo impianto.

⭐ **E la stringa è già verificata**: `avc1.640032` (High, livello 5.0) —
Firefox l'accetta e decodifica 300 fotogrammi su 300 con zero errori
(`banchi/07-b48`). Non va indovinata.

⚠ **Due cose misurate che serviranno scrivendo il codificatore:**
- il fotogramma che WebCodecs consegna su Firefox è **`BGRX`**, non planare: la
  conversione di colore la fa già il decodificatore;
- il decodificatore H.264 **in hardware** su questa macchina converte con una
  scala diversa da `ffmpeg`: **+8 livelli sulle zone chiare**, liscio e
  uniforme. Non è un guasto di blocchi, ma è un colore sbagliato per l'utente.

**Il lavoro che ne segue** (non ancora fatto): `RCP.md` §4.3 e §6.2 (il registro
dei codec, oggi `1` = HEVC, `2` = AV1), `codificatore.c` (`h264_vaapi` **e** il
lettore dei NAL che riconosce l'IDR, perché §5.2 vuole la chiave vera),
`figlio.c` (il terzo codec nelle strutture per-codec), `pagina.html`
(`CODEC_RCP`, la preferenza, e il flusso di prova della sonda, che è dipinto
davvero e va fabbricato).

⭐⭐ **FATTO il 20 agosto 2026**: `rcp.h` (`RCP_CODEC_VIDEO_MAX`), `rcp.c`
(`hevc,h264`), `codificatore.c` (`h264_vaapi`, 1,6 ms; lettore Annex-B e SPS di
H.264), `figlio.c`, `pagina.html` (sonde **generate**, `avc1.6400<liv esa>`).
⛔ E il numero **2 resta AV1 per sempre**: non si riusa.

⚠ **La trappola pagata**: un numero nuovo entra in cinque posti e uno resta
indietro — quattro array per-codec lunghi `[3]` (scrittura fuori dai limiti che
sporcava la variabile accanto) e una guardia **silenziosa** in
`wt_video_diffondi()` che buttava ogni fotogramma. Vedi `LEZIONI.md` §1.17.

⛔⛔⭐ **E IL 21 AGOSTO 2026 LA PREMESSA E' RISULTATA INCOMPLETA — misurato sul
telefono vero.** Firefox 154 su Android 16 non e' un browser «senza HEVC e senza
AV1»: e' un browser **senza WebCodecs**. `[M]` La pagina, nel registro del
server: *«WebCodecs NON c'e'»*, e `typeof VideoDecoder === "undefined"`.

⇒ **Il passaggio a H.264 NON ha aperto Firefox Android**, e nessun codec potra'
mai farlo: in `pagina.html` la strada verso i pixel e' UNA — WebCodecs — e non
c'e' **nessuna** occorrenza di `MediaSource`. ⚠ La decisione su H.264 resta
buona per gli altri motivi della tabella qui sopra (l'AV1 senza hardware da
nessuna parte), ma la ragione «cosi' Firefox Android funziona» **era falsa**.

⚠ **Chrome per Android ha WebCodecs**: li' il prodotto ha una strada. E se un
giorno si volesse Firefox Android, serve un secondo percorso di disegno (MSE con
un `<video>`), che e' lavoro vero e cambia il ritardo — non un interruttore.

Vedi [[niente-eccezioni-per-compositore]], [[prestazioni-sul-ferro-modesto]],
[[i-quadrati-sono-della-tela-2d]].
