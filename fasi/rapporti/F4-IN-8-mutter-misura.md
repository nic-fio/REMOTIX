# F4-IN-8 — Mutter sa dare una superficie della misura ESATTA che chiediamo noi?

*Studio del 14 agosto 2026, sera. ⛔ Nessuna riga di `src/` toccata. I banchi sono
`banchi/04-in8-misura.c` (Mutter) e `banchi/04-in8-parita.c` (i codificatori), costruiti con
`banchi/04-in8-costruisci.sh`. Tutte le `[M]` vengono da 192.168.0.2, GNOME Shell 48.7 / Mutter
48.7.*

---

## Il verdetto, in tre righe

1. **SÌ — Mutter dà esattamente la misura che chiediamo.** `[M]` Chiesto 2133×772, ottenuto
   2133×772: monitor `2133x772@60.000`, monitor logico a **scala 1.000000**, passo del buffer 8532
   = 2133×4 senza un byte di riempimento. **Nessun arrotondamento, nessun vincolo di parità,
   nessuna banda nera** — la superficie è dipinta al 100 % fino all'ultima colonna e all'ultima
   riga. Il cambio a caldo funziona: 20 misure diverse in 2 secondi, **20 concordate esatte**,
   ~40 ms di buco l'una, senza rifare la sessione.
2. **MA la parità esiste davvero — ed è NOSTRA, non di Mutter.** `[M]` `libx265` e `libsvtav1` a
   `yuv420p10le` **rifiutano l'apertura** con larghezza o altezza dispari: 2133×772 ⛔, 2134×773 ⛔,
   2134×772 ⭐. ⇒ La tela va **arrotondata al pari verso il basso** (2133 → 2132). È un pixel, ed è
   una decisione dichiarata (`TELA(ADATTATA)`), non una conversione nascosta.
3. **⛔⛔ E c'è una trappola che uccide:** una misura **oltre 16384** in una qualsiasi delle due
   dimensioni **ammazza `gnome-shell`** — non un errore, la sessione sparisce. `[M]` 16384 ⭐,
   16385 ☠. Mutter ne dichiara 16386 in altezza: **la sua API mente**.

⇒ **La conversione delle coordinate può sparire**, e la frase da refutare regge con due
correzioni: la misura dev'essere **pari** (per il nostro codificatore) e **≤ 16384** (o si perde la
sessione dell'utente).

---

## ⭐ La frase, giudicata pezzo per pezzo

> *«Mutter sa creare un monitor virtuale di misura arbitraria scelta dal client, sa cambiarla a
> sessione aperta senza rompere il flusso, e non impone né arrotondamenti né limiti che ci
> obblighino a riscalare.»*

| pezzo | esito | prova |
|---|---|---|
| misura arbitraria scelta dal client | ⭐ **VERO** | `[M]` 1×1, 3×3, 100×100, 1919×1079, 1601×903, 2133×772, 7680×4320, 16384×1000, 1000×16384 — **tutte concordate esatte** |
| cambiarla a sessione aperta | ⭐ **VERO** | `[M]` 20 cambi in 2 s, tutti esatti; nessun `RecordVirtual` nuovo, nessuna sessione nuova |
| senza rompere il flusso | ⚠ **quasi** | `[M]` il flusso passa da `streaming` a `paused` e torna: ~20 ms fermo, primo fotogramma nuovo a **41,6 ms** dalla richiesta. Non c'è fotogramma nero, non c'è input perso — c'è un **buco** |
| nessun arrotondamento | ⭐ **VERO in Mutter** | `[M]` mai una misura diversa da quella chiesta, in 30 prove |
| nessun limite che obblighi a riscalare | ⛔ **FALSO in tre punti** | il tetto 16384 (letale), il `scaling-factor` globale (silenzioso), e la parità del **nostro** codificatore |

---

## 1 · La creazione — che cosa ammette davvero l'API

`[S]` `reference-gnome/mutter/data/dbus-interfaces/org.gnome.Mutter.ScreenCast.xml:158-185`:

> *«RecordVirtual: Record a virtual area that will be represented as a virtual monitor. **The width
> and height corresponds to the non-scaled intended stream size.**»*

⛔ **Il metodo non ha nessun argomento di misura** — solo `properties`, e le sole proprietà lette
sono `cursor-mode` e `is-platform`. ⇒ `src/mutter.c:501-519` **non ha niente da correggere**: la
misura non si passa lì perché lì non esiste. Confermato guardando anche gli XML (la lezione già
pagata: `data/dbus-interfaces/`, non `src/`) — nessun `CreateVirtualMonitor`, nessun `SetSize`,
nessun `Resize` in tutta l'interfaccia.

**La misura si chiede sul flusso PipeWire, e Mutter la prende alla lettera.** La catena, letta:

| passo | file e riga | che cosa fa |
|---|---|---|
| Mutter offre un **intervallo**, non una misura | `meta-screen-cast-stream-src.c:1344-1356` | `SPA_POD_CHOICE_RANGE_Rectangle(default, min, max)` — ⛔ **un intervallo, senza passo**: niente multipli di 2, di 4 o di 8 |
| e per il flusso virtuale l'intervallo resta APERTO | `meta-screen-cast-virtual-stream-src.c:67-74` | `get_specs()` ritorna `FALSE` ⇒ `:1299-1310` **non** stringe `min = max = width×height` come farebbe per un monitor vero |
| il consumatore fissa il rettangolo | `src/cattura.c:875-883` | `SPA_POD_Rectangle(&misura)` — **noi lo facciamo già**, e il commento dice perché |
| Mutter legge quel che è stato concordato | `meta-screen-cast-stream-src.c:1512-1513` | `spa_format_video_raw_parse()` |
| e ci costruisce il monitor, **senza toccare i numeri** | `meta-screen-cast-virtual-stream-src.c:601-609` | `width = video_format->size.width; height = …` → `meta_virtual_monitor_info_new(width, height, …)` |

⇒ ⭐ **Fra la misura che chiediamo e il modo del monitor non c'è nessuna funzione**: è
un'assegnazione.

---

## 2 · I limiti — minimo, massimo, parità

`[R]` `meta-screen-cast-stream-src.c:67-69`:

```c
#define DEFAULT_SIZE SPA_RECTANGLE (1280, 720)
#define MIN_SIZE     SPA_RECTANGLE (1, 1)
#define MAX_SIZE     SPA_RECTANGLE (16384, 16386)
```

| domanda | risposta | marca |
|---|---|---|
| minimo | **1×1** — e funziona davvero: fotogrammi da 4 byte | `[M]` |
| la larghezza dev'essere pari? | ⭐ **NO.** 2133, 1601, 1919, 16385 — nessuna parità richiesta né applicata | `[M]` |
| multipla di 4 / 8 / 16? | ⭐ **NO** | `[M]` |
| il passo del buffer aggiunge riempimento? | **NO** su BGRx: `SPA_ROUND_UP_N(width × 4, 4)` è già `width × 4`. `[M]` 2133 → 8532 | `[R]` `:703` + `[M]` |
| massimo **dichiarato** | 16384 × 16386 | `[R]` `:69` |
| massimo **vero** | ⛔ **16384 in tutte e due le dimensioni** | `[M]` |

### ⛔⛔ Il massimo dichiarato è una bugia, e la bugia costa la sessione

`[M]` misurato quattro volte, con questi esiti **diversi fra loro**:

| chiesto | esito |
|---|---|
| 16384×1000 · 1000×16384 | ⭐ concordato esatto, fotogrammi normali |
| **16385**×1000 | ☠ formato concordato, poi `connection error`: **`gnome-shell` muore** |
| 1000×**16386** (dentro il `MAX_SIZE` dichiarato!) | ☠ idem |
| 20000×20000 | ⚠ **errore pulito e dichiarato**: `no more input formats`, sessione viva |

La riga che lo spiega, dal registro di Mutter `[M]`:

```
libmutter-ERROR **: Failed to allocate back buffer texture:
                    Failed to create texture 2d due to size/format constraints
```

⇒ Il tetto vero non è `MAX_SIZE`: è il **massimo della texture GL** (16384 su questa macchina,
`i915` + `amdgpu`), e Mutter non lo controlla — **aborta**. ⛔ Sopra il `MAX_SIZE` la negoziazione
SPA fallisce pulita; **dentro** il `MAX_SIZE` ma sopra il limite GL si muore. La zona letale è
esattamente `16385 … 16386`, cioè quella che l'API dichiara ammessa.

### ⭐ E il tetto è sul PALCO INTERO, non sul nostro monitor

`[M]` Nella sessione di prova esisteva già un monitor a 1920, e il nostro finiva a x = 1920.
Chiedendo 16384×1000 il fotogramma è tornato **nero per l'11,7 % a destra**: `1920 + 14464 =
16384`. Chiedendo 14464×1000 — cioè fino al bordo esatto — **100 % dipinto**.

⇒ ⛔ **Lo spazio utile è `16384 − (posizione del nostro monitor)`**. Nella sessione del prodotto
(senza monitor propri) il nostro è a (0,0) e li ha tutti; ma se un giorno ce ne fosse un altro, il
tetto scenderebbe **senza un errore**, con una banda nera come unico sintomo.

---

## 3 · ⛔⛔ La domanda pericolosa: errore esplicito o arrotondamento silenzioso?

**In Mutter: nessun arrotondamento silenzioso.** `[M]` 30 richieste, 30 misure identiche a quelle
chieste. I due modi di sbagliare sono **entrambi rumorosi**: `no more input formats` (fuori
intervallo) o la morte del compositore (oltre il limite GL). Non esiste il caso «ti do 1280×720 e
non te lo dico».

⭐ ⚠ **Ma un arrotondamento silenzioso c'è, e sta un piano più su: la SCALA del monitor logico.**

`[R]` `meta-monitor.c:1979-1993` — `meta_monitor_calculate_mode_scale()`:

```c
if (meta_settings_get_global_scaling_factor (settings, &global_scaling_factor))
  return global_scaling_factor;          /* ⛔ PRIMA di tutto, e senza guardare la lista */
return calculate_scale (monitor, monitor_mode, constraints);
```

e `[R]` `meta-monitor.c:1922-1925` — il caso normale:

```c
meta_monitor_get_physical_dimensions (monitor, &width_mm, &height_mm);
if (width_mm == 0 || height_mm == 0)
  return 1.0;
```

`[R]` `native/meta-output-virtual.c:41-68` **non assegna mai `width_mm`/`height_mm`** ⇒ restano 0
⇒ **scala 1,0 sempre**, per costruzione. `[M]` Confermato su tutte le misure provate.

⛔ **Tranne quando `org.gnome.desktop.interface scaling-factor` è diverso da 0.** `[M]` messo a 2:

```
monitor Meta-1 «Virtual remote monitor» modo 2133x772@60.000  scale ammesse: 1.0000
LOGICO a (1920,0)  SCALA 2.000000
```

⛔ Si legga due volte: **l'unica scala ammessa per quel modo è 1,0, e Mutter ne applica 2,0** — la
riga `:1988` scavalca la lista. E allora `[R]` `meta-monitor-config-manager.c:716-718`:

```c
case META_LOGICAL_MONITOR_LAYOUT_MODE_LOGICAL:
  *width  = (int) roundf (mode_width / scale);      /* 2133 / 2 → 1067 */
  *height = (int) roundf (mode_height / scale);     /* 772 / 2  → 386  */
```

⇒ i **pixel** restano 2133×772, ma lo **spazio delle coordinate** diventa 1067×386 — e 1067×2 =
2134 ≠ 2133: **mezzo pixel di scarto che nessuno dichiara**. Che quello sia lo spazio dell'input è
letto, non supposto: `[R]` `meta-screen-cast-virtual-stream.c:99-117`,
`meta_screen_cast_virtual_stream_get_size()` ritorna **il layout del monitor logico**, non la
misura del flusso; e `[R]` `:134-144` `transform_coordinate()` è **l'identità**.

⭐ **A scala 1 le due misure coincidono e la conversione è davvero l'identità.** A scala ≠ 1 c'è un
fattore che nessuna nostra riga conosce — ed è esattamente la famiglia di difetti costata questa
settimana.

⇒ ⛔ **Da fare comunque**, anche accettando la proposta: **leggere la scala** del nostro monitor
logico da `DisplayConfig.GetCurrentState` dopo il primo fotogramma, e **fallire dichiarandolo** se
non è 1,0. `[M]` Sulla macchina di prova `scaling-factor` è 0 per `nicfio` e per `provao2` — cioè
oggi siamo al sicuro **per configurazione, non per costruzione**.

---

## 4 · Il cambio a caldo — verificato, e quanto costa

`F4-IN-2` §Q3 diceva `[R]` che gnome-remote-desktop ridimensiona con `pw_stream_update_params()`
senza rifare la sessione, e che la durata *«non è misurata da nessuno»*. **Adesso lo è.**

Il meccanismo, letto: `[R]` `meta-screen-cast-stream-src.c:1672-1673` chiama
`notify_params_updated` → `[R]` `meta-screen-cast-virtual-stream-src.c:616-660`
`ensure_virtual_monitor()`:

```c
if (mode_info->width  == video_format->size.width &&
    mode_info->height == video_format->size.height)
  return;                                            /* stessa misura: non fa NULLA */
meta_virtual_monitor_set_mode (virtual_monitor, w, h, refresh_rate);
meta_monitor_manager_reload (monitor_manager);
```

⇒ nessun monitor nuovo, nessuna sessione nuova: **si cambia il modo del monitor che c'è**
(`[R]` `native/meta-virtual-monitor-native.c:39-64`).

### `[M]` Quanto costa, misurato

Un cambio da 2133×772 a 1601×903, orologio monotono:

| evento | dalla richiesta |
|---|---|
| `streaming` → `paused` | **1 ms** |
| formato nuovo concordato (esatto) | **4 ms** |
| `paused` → `streaming` | **19 ms** |
| **primo fotogramma alla misura nuova** | **41,6 ms** (secondo giro: 55,7 ms) |

- **il flusso non si interrompe**: si mette in pausa e riparte, stesso nodo, stesso `pw_stream`;
- **nessun fotogramma nero**: `[M]` il primo fotogramma nuovo ha il 100 % dei pixel non neri, con
  le ultime 4 colonne e le ultime 4 righe illuminate (83,3 e 87,4 di luminanza media);
- **nessun input perso**: `ConnectToEIS` non viene rifatto, il descrittore EIS resta lo stesso;
- **il buco è ~40 ms**, cioè **due fotogrammi e mezzo a 60 Hz**.

### `[M]` E regge la raffica

Venti misure diverse a 100 ms l'una dall'altra (`1201×801`, `1238×814`, … `1904×1048`), cioè quel
che fa una finestra di browser trascinata: **20 chieste, 20 concordate esatte**, sessione viva,
ogni giro ~20 ms di pausa. ⭐ Nessuna misura persa, nessuna fuori ordine, nessun accumulo.

---

## 5 · Il rapporto d'aspetto e il DPI

- **il rapporto non viene normalizzato**: `[M]` 2133×772 (2,76:1) e 16384×1000 (16,4:1) accettati
  senza una parola;
- **la scala di GNOME non cambia**: `[M]` 1,000000 in tutte le prove — e per costruzione, perché
  `width_mm = 0` (§3);
- ⚠ **la lista delle scale ammesse invece cambia, e a nostro favore**: `[M]` per 1920×1080 Mutter
  ne offre sei (1 · 1,25 · 1,5 · 1,7391 · 2 · 2,3077); per **2133×772 ne offre una sola: 1,0000**.
  `[R]` `meta-monitor.c:2045-2075` — una scala sopravvive solo se `width/scala` e `height/scala`
  sono interi entro una soglia, e una misura «strana» non ne ammette quasi nessuna. ⇒ ⭐ **una
  misura arbitraria è più difficile da riscalare di una tonda**, anche per l'utente che ci provasse
  dalle impostazioni;
- **che cosa vede il desktop dentro**: `[M]` il desktop dipinge **tutta** la superficie. Griglia
  8×4 di luminanza su 1601×903: valori da 63,5 a 93,7, nessuna cella nera, gradiente continuo dello
  sfondo fino ai bordi. ⛔ Nessuna banda, nessun angolo 1280×720 dipinto dentro un rettangolo più
  grande.
- ⚠ `MINIMUM_LOGICAL_AREA` (`meta-monitor.c:36`, 800×480 = 384 000) **non** rifiuta le misure
  piccole: `[M]` 100×100 e 3×3 accettate esatte. Serve solo a filtrare quali modi si *offrono* e
  quali scale sono valide.

---

## 6 · ⛔ Il vincolo vero, e non è di Mutter: **il nostro codificatore vuole misure pari**

`[M]` `banchi/04-in8-parita.c`, aprendo davvero i codificatori di `src/codificatore.c:631` a
`yuv420p10le`:

| misura | `libx265` | `libsvtav1` |
|---|---|---|
| 1920×1080 | ⭐ aperto, pacchetto emesso | ⭐ aperto, pacchetto emesso |
| **2133**×772 (larghezza dispari) | ⛔ `Invalid data found when processing input` | ⛔ `Invalid argument` |
| 2134×**773** (altezza dispari) | ⛔ rifiutato | ⛔ rifiutato |
| 2134×772 (tutte e due pari) | ⭐ aperto | ⭐ aperto |
| 1601×903 (tutte e due dispari) | ⛔ rifiutato | ⛔ rifiutato |

⇒ **Le due dimensioni devono essere pari**, ed è il 4:2:0 dei formati che usiamo — non un capriccio
del compositore. ⛔ È esattamente il vincolo che `F4-IN-1` aveva visto in xrdp e in KasmVNC
(`Math.floor(x/2)*2`): **ce l'hanno tutti, e ce l'abbiamo anche noi — solo che il nostro è nel
codificatore, non nel compositore.**

⭐ E il rimedio non rimette una scala: **arrotondare al pari verso il basso**. 2133 → 2132. Si
perde **una colonna di pixel**, non un fattore di scala; la tela concessa resta ≠ da quella chiesta
di al massimo 1 px per asse, e il protocollo ha già il modo di dirlo (`RCP.md` §4.5: il server può
concedere una tela diversa; §7.1: `TELA(ADATTATA)`).

⚠ **Come si concilia con `F4-IN-11`**, che dallo stesso banco conclude *«2133×772 esce come
2134×772, accettato, `exit=0`, nessun avviso»*: sono **due piani diversi e concordano**. `F4-IN-11`
misura la **catena ffmpeg**, che davanti al codificatore ha chi rimedia (riempimento e finestra di
conformità) e **arrotonda in ALTO in silenzio**; qui si misura la chiamata che `codificatore.c` fa
davvero — `avcodec_open2()` con `ctx->width` esatto (`:1086-1087`) — e a quel piano **non c'è
nessun rimedio: si prende un errore**. ⇒ Le due letture dicono la stessa cosa da due lati: **il
dispari non attraversa**, e chi lo lascia passare lo cambia senza dirlo. ⭐ E il rimedio è lo stesso
in tutti e due i rapporti: **troncare al pari verso il basso**, invece di lasciar arrotondare in
alto qualcun altro.

---

## 7 · Che cosa cambiare da noi, in concreto

| file e riga | oggi | domani |
|---|---|---|
| `src/mutter.c:501-519` | `RecordVirtual` con `cursor-mode` + `is-platform` | ⭐ **niente**: l'API non prende misure |
| `src/cattura.c:875-883` | `SPA_POD_Rectangle(&misura)` — rettangolo **fisso** | ⭐ **niente**: è già il verso giusto, ed è il motivo per cui la misura arriva esatta |
| `src/cattura.c:891-915` | `cattura_avvia(nodo, larghezza, altezza, …)` | ⭐ **niente**: già parametrico |
| **`src/cattura.c` — manca** | nessun modo di cambiare misura a flusso aperto | ⛔ **da aggiungere**: `cattura_ridimensiona(Cattura*, l, a)` = ricostruire il POD di `proposta()` e chiamare `pw_stream_update_params()`. `[M]` 41 ms, misura esatta, 20 di fila reggono |
| `src/main.c:111-112` | `#define TELA_L 1920u` / `TELA_A 1080u` | ⛔ la costante diventa un **valore predefinito**: la misura vera arriva dal `CIAO`/`ADATTA_TELA` del client |
| `src/figlio.c:2261` · `:2465-2466` | `tela_l`/`tela_a` da `argv[5]`/`argv[6]`, immutabili per tutta la vita del figlio | ⛔ devono diventare **variabili di stato del figlio**, aggiornabili |
| `src/input.h` → `input_ritela()` | ⭐ **esiste già** (14 agosto) | va **chiamata** dopo ogni ridimensionamento riuscito |
| `src/codificatore.c:1086-1087` | `ctx->width/height` fissi all'apertura | ⛔ un cambio di tela **richiede un codificatore nuovo** e un fotogramma chiave — `RCP.md` §7.1 lo dice già (`:1200`) |
| **nuovo, in `mutter.c`** | — | ⛔ **leggere la scala** del nostro monitor logico e **fallire se non è 1,0** (§3): è la sola difesa contro la conversione invisibile |
| **nuovo, dove si giudica `ADATTA_TELA`** | — | ⛔ due paletti: **arrotondare al pari verso il basso**, e **rifiutare > 16384** con `TELA(MISURA_FUORI_LIMITI)` — perché sopra quel numero non si sbaglia un fotogramma, **si perde la sessione dell'utente** |

---

## Quel che questo rapporto NON dice

1. ⛔ **La strada della scheda (DMA-BUF) non è misurata.** Tutte le `[M]` sono su `MemFd`
   (`CATTURA_STRADA_MEMORIA`, quel che il prodotto usa oggi). Su DMA-BUF il passo lo decide il
   driver (`meta-screen-cast-stream-src.c:694-695`, `cogl_dma_buf_handle_get_stride`) e una
   larghezza dispari **potrebbe** portare riempimento. Non provato.
2. ⛔ **`hevc_vaapi` non è stato giudicato.** Il banco `04-in8-parita.c` gli passa `AV_PIX_FMT_VAAPI`
   senza un `hw_frames_ctx`, e lui rifiuta **per quel motivo** — anche a 1920×1080. ⇒ Sulla parità
   in hardware **non abbiamo un risultato**, e `codificatore.c:286-287` fa già capire che con
   `hevc_vaapi` su AMD la finestra di conformità c'è.
3. ⛔ **Il tetto 16384 è di QUESTA macchina.** È il massimo della texture GL di `i915`/`amdgpu`
   qui; su un'altra scheda può essere 8192. ⇒ Il paletto non va scritto come costante: va **chiesto**
   o tenuto molto basso.
4. ⚠ **La misura del buco (41 ms) è su un desktop fermo.** Con la scena in movimento e la codifica
   in corso può essere diversa; e il tempo per **riaprire il codificatore** e mandare la chiave
   nuova non è contato — è del tutto fuori da questa misura.
5. ⚠ **Non è misurato che cosa vede l'utente durante il buco.** Il flusso non manda niente per
   ~40 ms; se la pagina tenga l'ultimo fotogramma o lampeggi dipende da `pagina.html`, e non l'ho
   guardato.
6. ⚠ **La sessione di prova aveva già un monitor** (`gnome-shell --headless --virtual-monitor
   1920x1080` di `nicfio`), quindi il nostro nasceva a x = 1920. La condizione del prodotto — un
   solo monitor virtuale a (0,0) — l'ho dedotta, non misurata. ⛔ È anche il motivo per cui il tetto
   utile misurato era 14464 e non 16384.
7. ⛔ **Ho ammazzato due volte la sessione GNOME di `nicfio`** provando 16385 e 16386, e l'ho
   riavviata con `banchi/00-sessione-gnome.sh avvia`. Le sessioni di `prova`, `provao1` e `provao2`
   e il server sulla 7700 **non sono stati toccati** — verificato dopo ogni caduta.
8. ⚠ **Non ho provato il cambio a caldo mentre l'input scorre.** `[R]` `libei` distrugge e ricrea i
   dispositivi assoluti a ogni cambio di geometria (`src/input.h`), e `on_monitors_changed`
   (`meta-screen-cast-virtual-stream-src.c:213-231`) chiama `meta_eis_viewport_notify_changed()` a
   ogni ridimensionamento. ⇒ **A ogni cambio di tela i dispositivi di input vengono rifatti**, e
   quanti eventi si perdano nel mezzo **non è misurato**.
