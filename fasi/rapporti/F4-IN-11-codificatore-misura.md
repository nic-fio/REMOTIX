# F4-IN-11 — La misura del client attraversa il codificatore?

*Studio, 14 agosto 2026. Banco: `192.168.0.2`, i5-13500T, Intel UHD 730 (`/dev/dri/renderD128`,
iHD) e AMD RX 6800 (`/dev/dri/renderD129`, radeonsi). ffmpeg 7.1.5-0+deb13u1.*
*⛔ Nessuna modifica a `src/`. File temporanei in `/tmp/studio-codificatore/`.*

---

## IL VERDETTO, IN TRE RIGHE

1. ⛔ **La frase è FALSA, e cade di UN PIXEL PER LATO.** `[M]` `2133×772` esce dal codificatore
   come **`2134×772`**, e `2133×771` come **`2134×772`** — accettati, `exit=0`, **nessun avviso**.
2. ⭐ **Ma il vincolo non è «multipla di 16» e nemmeno «multipla di 8»: è PARI, e basta.** `[M]`
   `2130`, `2132`, `2134`, `2136`, `2560`, `1366` passano **esatte**; solo i dispari si spostano.
3. ⭐ **Il disegno dell'utente REGGE** — nessuna banda nera, nessuna conversione di coordinate —
   **a patto che il client tronchi la propria finestra al pari**, che è ciò che `pagina.html:2840`
   già fa e che `RCP.md:987` già impone.

---

## ⭐ LA RIGA CHE SERVE DAVVERO

> **La misura più vicina a quella chiesta dal client che attraversa TUTTA la catena senza essere
> toccata è il PARI: qualunque larghezza e altezza pari, da 320×240 a 7680×4320, arriva intatta
> fino al vetro. Non serve il multiplo di 16, non serve il multiplo di 8.**

Il costo del disegno è dunque **≤ 1 pixel per lato**, e si paga troncando in basso
(`2133 → 2132`), non lasciando arrotondare il codificatore in alto (`2133 → 2134`).

⚠ **Con una riserva che vale più del pixel**, e sta al punto 2 qui sotto: quanto sopra è vero
**sulla Intel**, che è il nodo che il prodotto usa (`figlio.c:1912`). **Sull'AMD è falso anche per
le misure pari.**

---

## ⛔⛔ IL RIFIUTO PARZIALE DEL MANDATO — il vincolo che conta non è l'allineamento

Il mandato chiedeva di misurare un **allineamento**. L'allineamento c'è ed è mite (pari).
⭐ **Ma la cosa pericolosa che ho trovato non è un allineamento: è una INCOERENZA fra due pezzi**,
e produce un errore di **40 pixel**, non di uno.

`[M]` Stessa richiesta `2134×772` (**pari**, quindi «legale»), stesso ffmpeg, due schede:

| nodo | `pic_width_in_luma_samples` | `conf_win_right_offset` | **mostrato** | chiesto |
|---|---|---|---|---|
| Intel `renderD128` | 2136 | 1 | **2134** ✅ | 2134 |
| AMD `renderD129` | **2176** | **1** | **2174** ⛔ | 2134 |

⭐ **I due scarti di conformità sono IDENTICI** (`right=1`, `bottom=2`): sono quelli che ffmpeg ha
calcolato per una superficie di **2136**. Ma nel flusso dell'AMD `pic_width_in_luma_samples` vale
**2176**. ⇒ **Il driver radeonsi ha riscritto la misura codificata e ha lasciato in piedi la
finestra di conformità di ffmpeg.** Il risultato non è «allineato»: è **incoerente**, e ritaglia
2 pixel da una tela che ne aveva 42 di troppo.

`[M]` Il modello che ne esce combacia su **5 punti su 5** dell'AMD:

```
mostrato_AMD = FFALIGN(l, 64) − 2·floor( (FFALIGN(l, 8) − l) / 2 )
```

| chiesto (AMD) | mostrato | scarto |
|---|---|---|
| 2134×772 | 2174×780 | **+40**, +8 |
| 2133×772 | 2174×780 | +41, +8 |
| 1366×768 | **1406**×768 | **+40**, 0 |
| 1920×1080 | 1920×**1088** | 0, **+8** |
| 2560×1440 | 2560×1440 | 0, 0 ✅ |

⇒ Sull'AMD **sopravvivono solo le larghezze multiple di 64 e le altezze multiple di 16**.
`[R]` Questo è lo stesso fenomeno già annotato in `src/codificatore.c:286-290` per il caso
`1920×1088`; ⭐ la novità di questo studio è che **non è limitato all'altezza e non è limitato a
8**: su una larghezza non multipla di 64 l'errore è **40 pixel**.

---

## LE SEI DOMANDE

### 1. Il nostro codificatore — che misura chiede, e che fa col dispari

`[R]` **Il dispari è già rifiutato, e ad alta voce.** `src/codificatore.c:1370-1374`:

```c
/* ⚠ 4:2:0 vuole misure pari: una larghezza dispari darebbe un croma di
 *   mezzo campione, e il codificatore lo arrotonderebbe **in silenzio**. */
if ((richiesta->larghezza & 1) || (richiesta->altezza & 1)) {
        di(errore, errore_byte, "%ux%u: 4:2:0 vuole misure pari", ...);
        return NULL;
}
```

`[R]` Stesso controllo nel ridimensionamento, `src/codificatore.c:1511-1513`.
⭐ **Il commento aveva ragione, e questo studio lo ha misurato**: `hevc_vaapi` arrotonda davvero, e
davvero in silenzio. Il controllo è a monte del difetto.

`[R]` **Secondo testimone**, `src/codificatore.c:1703-1711`: la misura **letta nei byte** del
flusso viene confrontata con quella chiesta, e la differenza è un fallimento dichiarato.
⇒ ⭐ **È questa riga che salverebbe il prodotto sull'AMD**: `2174 ≠ 2134` verrebbe intercettato e
si scenderebbe su `libx265` col ripiego dichiarato di `figlio.c:1968`.

`[R]` **La tela è 1920×1080 fissa, costante di compilazione**: `src/main.c:111-112`
(`#define TELA_L 1920u` / `TELA_A 1080u`) → `main.c:603` → `figlio.c:715-716` (argv) →
`figlio.c:2465-2466` (`strtoul`, **senza controllo di parità né clamp**).
`[R]` E lato client la stessa costante è cablata a `src/pagina.html:2841`.
`[R]` `codificatore_ridimensiona()` esiste (`codificatore.c:1504`) ma **non è chiamata da nessuno**.

`[R]` Il nodo usato in produzione è **l'Intel**: `src/figlio.c:1912`
(`#define NODO_RENDERING "/dev/dri/renderD128"`), con `hevc_vaapi` a `figlio.c:1959`.

### 2. ⭐⭐ VAAPI / libavcodec — l'allineamento vero, e il «multiplo di 16» è FOLKLORE

`[S]` **La causa, nel sorgente di ffmpeg n7.1**, `libavcodec/hw_base_encode_h265.c:230-244`:

```c
sps->pic_width_in_luma_samples  = base_ctx->surface_width;
...
sps->conf_win_right_offset  = (base_ctx->surface_width  - avctx->width)  >> desc->log2_chroma_w;
sps->conf_win_bottom_offset = (base_ctx->surface_height - avctx->height) >> desc->log2_chroma_h;
```

e `libavcodec/vaapi_encode_h265.c:1087-1090`:

```c
base_ctx->surface_width  = FFALIGN(avctx->width,  priv->min_cb_size);
base_ctx->surface_height = FFALIGN(avctx->height, priv->min_cb_size);
```

⭐ **Lo `>> log2_chroma_w` è una divisione intera che TRONCA, e il bit troncato è il pixel perso.**
In 4:2:0 `log2_chroma_w = 1`, quindi lo scarto può ritagliare solo **a passi di 2 luma**:
una misura dispari **non è esprimibile**, e ciò che esce è la misura **arrotondata in su al pari**.

`[M]` Il modello predice **8 punti su 8** sull'Intel (superficie = `FFALIGN(n, 8)`):

| chiesto | superficie | `(sup−chiesto)>>1` | previsto | **misurato** |
|---|---|---|---|---|
| 2133 | 2136 | 1 → taglia 2 | 2134 | **2134** ✅ |
| 2135 | 2136 | 0 → taglia 0 | 2136 | **2136** ✅ |
| 771 | 776 | 2 → taglia 4 | 772 | **772** ✅ |
| 773 | 776 | 1 → taglia 2 | 774 | **774** ✅ |
| 769 | 776 | 3 → taglia 6 | 770 | **770** ✅ |

`[M]` **`min_cb_size` sull'iHD vale 8, non 16** — letto nel flusso stesso:
`log2_min_luma_coding_block_size_minus3 = 0` ⇒ `MinCbSizeY = 8`, e infatti `2133 → 2136`
(se fosse 16 sarebbe `2144`) e `771 → 776` (se fosse 16 sarebbe `784`).
⛔ **Il «multiplo di 16» che si ripete è il valore di ripiego di ffmpeg quando il driver non
dichiara niente, non il vincolo di questa scheda.**

⭐ **`coded_width` contro `display_width`: la distinzione tiene, ed è esattamente il modo in cui il
problema si scioglie.** `[M]` `1918×1080` → `display 1918×1080`, `coded 1920×1080`. La tela
arbitraria **non paga niente**: si codifica allineato e si **dichiara** la misura esatta. Il
vincolo residuo è solo la **granularità dello scarto**, che è 2 perché il croma è 4:2:0.

`[M]` ⭐ **E la prova che il colpevole è il 4:2:0 e non il codificatore**: in **4:4:4** (`vuyx`,
profilo `Rext`, `log2_chroma_w = 0`) la stessa richiesta `2133×772` esce **`2133×772` esatta**,
dispari compresa, `coded 2136×776`.
⇒ `[?]` La via d'uscita per il dispari esiste ed è dichiarata, ma costa il croma pieno: **non vale
un pixel**. La cito perché chiude la domanda «è il codificatore o è il formato»: **è il formato**.

`[M]` **10 bit — il profilo che il prodotto usa davvero** (`figlio.c:1940`, `r.profondita = 10`):
comportamento **identico**. `p010` + `-profile:v main10`: `2134×772 → 2134×772` ✅;
`2133×772 → 2134×772` ⛔; `1920×1080 → 1920×1080` ✅.

`[M]` **AV1 in hardware NON ESISTE su questa GPU.** `av1_vaapi` compare in `-encoders` ma all'uso
dà *«No usable encoding profile found»*; `vainfo` non elenca **nessun** entrypoint AV1 (né
`EncSlice` né `EncSliceLP`). ⇒ `[R]` Conferma indipendente della misura già scritta in
`src/figlio.c:1947-1951`. **La domanda «che allineamento vuole AV1 in hardware» non ha oggetto.**

`[M]` **In software si fallisce invece di arrotondare** — ed è il contrasto che conta:
`libx265` a `2133×772` → *«Cannot open libx265 encoder»*, **errore**.
`libsvtav1` a `2133×772` e `2133×771` → **errore**.
⭐ **Lo stesso ingresso che il software RIFIUTA, l'hardware lo ACCETTA e mente.**

### 3. PipeWire — non allinea, e non è lui il pericolo

`[R]` La misura è chiesta come **rettangolo FISSO**, non come intervallo: `src/cattura.c:823`
(`SPA_RECTANGLE(larghezza, altezza)`) e `cattura.c:876-878`, col commento *«un intervallo aperto
lascerebbe scegliere Mutter, che sceglie 1280×720»*.
`[R]` `SPA_POD_CHOICE_RANGE_Rectangle` **non compare in tutto `src/`**; nessuno `step`, quindi
**nessun allineamento imposto da PipeWire**.
`[R]` Il formato negoziato **viene letto** (`cattura.c:369`, `spa_format_video_raw_parse`) e usato
a valle (`cattura.c:671-672`).
`[R]` Lo **stride** è letto dal manifesto e mai ricalcolato: `cattura.c:648-653`
(`passo = piano->chunk->stride`; se è 0 si scarta il fotogramma invece di inventarlo), propagato a
`cattura.c:673-675`. ⇒ **Allineamento dello stride ≠ allineamento della larghezza**: il primo è
gestito bene, il secondo non esiste in `cattura.c`.

### 4. ⛔⛔ CHI ARROTONDA IN SILENZIO — l'elenco

| # | dove | che cosa fa | si vede? |
|---|---|---|---|
| 1 | `hw_base_encode_h265.c:236` (ffmpeg) | `>> log2_chroma_w` tronca ⇒ **dispari → pari in su** | ⛔ **NO**, `exit=0` |
| 2 | driver **radeonsi** | riscrive `pic_width_in_luma_samples` e lascia lo scarto di ffmpeg ⇒ **fino a +40 px** | ⛔ **NO** |
| 3 | `cattura.c:914-915` vs `:369` | la misura **chiesta** è memorizzata e **mai confrontata** con quella negoziata | ⚠ solo un log a `:376`, non marcato come divergenza |
| 4 | `figlio.c:2074` e `:2127` vs `:2317` | encoder e intestazione RCP usano `tela_l/tela_a`; i pixel vengono da `fo` | ⛔ **NO** — due misure sotto la stessa etichetta |
| 5 | `figlio.c:2465-2466` | `tela_l/tela_a` da `argv` **senza controllo di parità** | ⚠ il rifiuto arriva dopo, a `codificatore.c:1372` |

⭐ **I difetti 1 e 2 sono coperti dal prodotto** grazie a `codificatore.c:1372` (a monte) e
`codificatore.c:1703` (a valle, secondo testimone sui byte).
⛔ **I difetti 3 e 4 NON sono coperti**: `codificatore_comprimi()` (`codificatore.c:1753`) riceve
**pixel e stride ma non larghezza e altezza**, quindi non può fare da testimone; e
`sws_getContext` (`codificatore.c:1319-1320`) usa la larghezza **della tela**, non quella del
fotogramma catturato. ⇒ `[?]` Se un compositore concedesse una misura diversa da quella chiesta, il
prodotto codificherebbe un ritaglio sbagliato **senza una riga di registro**. ⭐ **È la falla che il
disegno «tela = finestra» rende raggiungibile**, perché è il disegno che smette di chiedere sempre
1920×1080.

### 5. WebCodecs e la pagina

`[R]` **La tela si dimensiona proprio come sperato**: `src/pagina.html:2209-2210`,
`f.displayWidth || f.codedWidth` e `f.displayHeight || f.codedHeight`. ⇒ ⭐ **La distinzione
`coded`/`display` è già onorata dal client**: la finestra di conformità viene rispettata.
`[R]` `VideoDecoder.configure()` a `pagina.html:2106-2107` passa `codedWidth`/`codedHeight` presi
**dall'intestazione RCP** (`:1823`, `:1941`), non `displayWidth`. `visibleRect` non compare mai.
`[R]` Il fotogramma va su un canvas intermedio (*deposito*, `:2213-2218`); la tela **visibile** è
dimensionata sulla **vista** (`:1666`), con impaginazione a bande nere e mai stiramento
(`:1741-1751`).
`[R]` ⭐ **La pagina distingue già i due vincoli, e lo dice**: la **vista** è arrotondata solo con
`Math.round` (`:1256`), col commento *«niente arrotondamenti ai numeri pari, che sono un vincolo
della TELA e che qui sarebbero la forma E2»*; la **tela** invece è forzata pari e limitata
(`:2840-2841`, `pari = n - (n % 2)`, fra `320×240` e `7680×4320`).
`[R]` La vista viaggia una volta sola, in `ATTACCA`; ⛔ `VISTA` (0x0008) non è mai spedita, quindi
il server non sa che la finestra è cambiata **per scegliere quanti bit spendere**.
⭐ **`ADATTA_TELA` invece SI', dal 15 agosto 2026**: la pagina la manda all'attacco con la misura
della propria finestra (`chiedi_tela()`), e con `?adatta=segui` anche a ogni ridimensionamento —
`DECISIONI.md` §5.0-sexies e `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md`.
`[R]` Le coordinate del mouse si convertono a `:3767-3782` e `:4159-4160`, con tre fattori
(`sx/sy` fotogramma→tela, `vx/vy` tela→vetro, `bx0/by0` bande nere), in virgola mobile fino a un
`Math.floor` finale (`:3814-3827`). ⇒ ⭐ **È esattamente questa catena che il disegno dell'utente
vuole azzerare, e la misura di questo rapporto dice che può: basta che `tela == vista` col
troncamento al pari, e `sx = sy = 1`, `bx0 = by0 = 0`.**

### 6. La specifica lo aveva già scritto

`[S]` `RCP.md:987-990` — *«**7680×4320**, ed **entrambe DEVONO essere pari**. Fuori da lì è
`ERRORE_PROTOCOLLO`. ⭐ Il vincolo dei numeri pari non è pignoleria: i codificatori video lavorano
su blocchi, e una misura dispari viene arrotondata **da chi codifica, in silenzio** — due misure
diverse sotto la stessa etichetta.»*

⇒ ⭐ **Questo studio non ha scoperto il vincolo: lo ha CONFERMATO e ne ha misurato l'entità.** La
specifica diceva «si arrotonda in silenzio» come previsione; ora è `[M]`, col meccanismo
(`>> log2_chroma_w`), il verso (**in su**, non in giù) e la grandezza (**1 pixel**).

`[S]` E l'asimmetria che rende il disegno possibile è già scritta: `RCP.md:1661-1664` — la **vista**
ammette *«qualunque misura da 1×1 in su, dispari compresa»*, mentre la **tela** deve stare fra
`320×240` e `7680×4320` **coi lati pari**.

---

## QUEL CHE QUESTO RAPPORTO NON DICE

- ⛔ **Non ha provato il percorso vero del prodotto**, ma `ffmpeg` da riga di comando. `[?]` La
  catena di `codificatore.c` usa `AVCodecContext` direttamente e le stesse `hw_base_encode_*`, e i
  numeri di `codificatore.c:286-290` combaciano coi miei — ⚠ ma **non l'ho verificato girando il
  prodotto** a una tela dispari, perché `codificatore.c:1372` la rifiuta prima.
- ⛔ **Non ha misurato il costo in banda** di una tela non allineata. `[?]` La superficie codificata
  sale a `FFALIGN(l,8) × FFALIGN(a,8)`: per `2134×772` sono `2136×776`, cioè **+0,6 %** di pixel —
  `[?]` trascurabile, ma è un'ipotesi, non una misura di bitrate.
- ⛔ **Non ha provato misure grandi** (4K, 8K) né il tetto reale del codificatore, né il
  `misura_massima` del decodificatore del browser (`pagina.html:2727-2728`).
- ⛔ **Non ha provato `hevc_vulkan`**, che è nell'elenco di ffmpeg e potrebbe avere un'altra
  granularità. `hevc_qsv` ha fallito per un runtime mancante (MFX session -9), non per la misura.
- ⛔ **Non ha verificato WebCodecs sul vetro vero**: che Chromium accetti un flusso con
  `coded 2136×776` e `display 2134×772` è `[?]`, dedotto dal fatto che il caso `1920×1088 / 1080`
  dell'AMD funziona oggi. **Nessuno ha aperto il browser su una tela non standard.**
- ⛔ **Non dice se i compositori sanno PRODURRE una misura arbitraria**: è il fronte degli altri
  tre agenti. Questo rapporto dice solo che **se la producono pari, la catena la porta intatta**.
- `[?]` **Il modello dell'AMD è ricavato da 5 punti**, tutti combacianti, ma non l'ho confermato nel
  sorgente di Mesa: `[?]` che sia il driver a riscrivere `pic_width_in_luma_samples` è
  **un'inferenza dagli scarti di conformità identici**, non una riga letta.
