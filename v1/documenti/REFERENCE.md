# REFERENCE — riferimento di sviluppo

*Le regole da rispettare perché il codice non entri in conflitto con i client che REMOTIX deve
servire.*

> # ⛔ Regola vincolante di metodo
>
> **Non si scrive una sola riga di codice senza aver prima consultato questo documento.**
>
> *Posta dall'utente il 3 agosto 2026.*
>
> Non è una raccomandazione di buon senso: è una regola con una ragione precisa. Le incompatibilità
> descritte qui **non si manifestano come errori**. Si manifestano come schermo nero, disconnessione
> improvvisa o immagine sbagliata, su **un client su tre** — e il client che le mostra è quasi sempre
> quello che non stiamo usando per provare.
>
> Scrivere prima e scoprire dopo costa quanto è già costato: due giorni per un `MapSurfaceToOutput`
> mancante, mezza giornata attribuita a `xdotool` per un difetto che era nostro, una prova automatica
> rimasta verde per tutto il tempo in cui il difetto c'era.
>
> **In pratica**, prima di toccare un'area:
>
> | Se stai per scrivere | Leggi prima |
> |---|---|
> | negoziazione, sicurezza, capacità | §0, §3, R13, R14 |
> | qualunque cosa su EGFX | §1.6, §5, R1, R2, R3, R6 |
> | il codificatore | R3, R4, R5, R11, §1.7, §10 n.2 e n.3 |
> | bitrate, qualità, taratura | **R31**, R11, §5.5 di `SPECIFICA.md` |
> | fotogrammi al secondo, cadenza, scelta del compositore | **R32** |
> | accelerazione hardware, GPU | **R27**, **R28**, §8.6-bis |
> | cattura a copia zero, DMA-BUF | **R29**, **R30**, §7.3 |
> | **KDE, KWin, la fase 11** | **[`kde.md`](kde.md)** per intero |
> | ridimensionamento, monitor, geometria | §7, R7, R8, R9, R10, **R10-bis** |
> | finestra minimizzata, ridisegno | **R23** |
> | cattura del desktop, sessione grafica | §7.3, §7.4, R9, R10 |
> | logout, distacco, D-Bus di sessione | §7.4, R12 |
> | input | §6, R12 |
> | misura della rete, controllo di flusso | §5, §5.1, §5.2, **R19**, **R20** |
> | audio | **§7.5**, §1.5, **R21**, **R24**, **R25**, **R26**, R19, §10 n.5 e n.8 |
> | appunti | **§7.6**, **R22**, §15 di `protocollo-rdp.md`, §14.1 di `gnome-remote-desktop.md` |
> | chiusura della connessione | R12 |
> | qualunque cosa, quando qualcosa non si vede | §8 |
>
> E quando una misura nuova contraddice questo documento, **si aggiorna il documento nello stesso
> momento**, con la data e la marca della fonte. Un riferimento che invecchia in silenzio è peggio di
> nessun riferimento.

Questo documento non spiega il protocollo — per quello c'è [`protocollo-rdp.md`](protocollo-rdp.md) —
e non racconta come funzionano gli altri server: ci sono
[`gnome-remote-desktop.md`](gnome-remote-desktop.md) e [`xrdp-funzionalita.md`](xrdp-funzionalita.md).
E non descrive gli altri compositori: per KDE c'è [`kde.md`](kde.md).
Qui ci sono **le regole**, il più corte possibile, con accanto **chi le punisce**.

> **E non contiene le lezioni: quelle stanno in [`LEZIONI.md`](LEZIONI.md).** La divisione è netta e
> conviene tenerla: qui **che cosa fare con Mutter**, e metà di queste regole cadranno quando
> cambierà il compositore; là **quel che resta vero quando il compositore cambia**, con accanto
> quanto è costato impararlo. Chi apre un desktop nuovo comincia da lì.

Ogni affermazione ha una fonte:

| Marca | Significato |
|---|---|
| **[M]** | **Misurato da noi**, sul campo. Data indicata |
| **[R]** | Letto nel codice di un riferimento (`gnome-remote-desktop` 48/51, xrdp 0.10.1, FreeRDP 3.22) |
| **[S]** | Specifica Microsoft |

---

## 0. In due minuti

Se hai poco tempo, questo è il minimo che evita i guai peggiori.

```
NEG_RSP    flags = EXTENDED_CLIENT_DATA_SUPPORTED | DYNVC_GFX_PROTOCOL_SUPPORTED
           selectedProtocol = PROTOCOL_SSL          (TLS 1.2 minimo, non solo 1.3)

EGFX       conosci tutte e DIECI le versioni, 10.6 con DUE valori
           conferma UNA versione, la più alta
           CreateSurface  E  MapSurfaceToOutput      ← sempre entrambe
           ResetGraphics con monitorCount ≥ 1, bordi INCLUSIVI

codec      AVC disponibile   → AVC420               (Windows, Linux)
           AVC_DISABLED      → RemoteFX Progressive (Android)

H.264      allineamento  w×16  h×64,  bordo RIEMPITO non tagliato
           profilo High, constraint_set4 = constraint_set5 = 1, MAI fotogrammi B
           regioni con bordi ESCLUSIVI

resize     MAI Deactivate All: si ridichiara la tela
           il layout arrivato prima di EGFX si RINVIA
           inibisci il rendering, riprendi solo a misure confermate

chiusura   SEMPRE freerdp_set_error_info() prima di Disconnect
```

---

## 1. I tre client

### 1.1 Le tre famiglie

| | **Windows** | **Linux** | **Android** |
|---|---|---|---|
| Riferimento | `mstsc.exe` (Win 10/11) | FreeRDP 3 / `xfreerdp3` | **Remote Desktop Manager** |
| Secondario | Windows App | Remmina, GNOME Connections, KRDC | Windows App *(solo verifica)* |
| **Severità** | **massima** | bassa | **massima** [M] |
| Supplisce alle omissioni del server | **no** | **sì** | **no** [M] |
| EGFX negoziata | **10.6** [M] | 8.1 per default [M] | **10.7** [M] |
| **H.264** | **sì**, anche AVC444 [M] | **sì**, AVC420 [M] | **no** [M] |
| Ridimensiona da sé | no | solo se richiesto | sì, subito |
| KLID utilizzabile | **sì** [M] | sì | **no** |

> **La regola dei tre client.** Nessuno copre i casi degli altri. Un difetto che si vede **solo** su
> mstsc o su RDM è quasi sempre **un'informazione che il server ha omesso**, non un'anomalia del
> client. FreeRDP la supplisce da sé e nasconde il difetto.
>
> **Corollario sulle prove**: una prova verde su `xfreerdp3` non dice nulla. Va fatta sul client che il
> difetto lo mostra. [M, 3 agosto: la sezione «Logout» di `prova-e2e.sh` è rimasta verde per tutto il
> tempo in cui il difetto c'era, perché collaudava l'unico client che tollerava l'omissione]

### 1.2 mstsc su Windows 11 — misurato il 3 agosto 2026

| Cosa | Valore |
|---|---|
| Identità | `[Windows platform, Windows NT]` — riconoscibile da `OsMajorType`/`OsMinorType` |
| Protocolli richiesti | `SSL \| HYBRID \| HYBRID_EX` (0x0B) — **accetta anche TLS puro** |
| TLS | moderno: TLS 1.3, 20 cipher, SNI, `key_share`, `post_handshake_auth` (Schannel) |
| Cookie | **assente** verso un host sconosciuto; `mstshash=<utente>` se ha credenziali salvate |
| EGFX | **10.6** — AVC420 **sì**, AVC444 **sì** |
| Flag di capacità | **tutti a zero**: niente `SMALL_CACHE`, `THINCLIENT`, `AVC_DISABLED` |
| Canali dinamici | `RDPGFX`, `DISP`, `AUDIO_PLAYBACK`, `AUDIO_INPUT`, `CLIPRDR`, `TELEMETRY` |
| Audio | AAC no, Opus no, **PCM sì** ⚠ (§1.5) |
| Clipboard | long format names, stream file clip, file clip no file paths, **can lock clip data**, huge file support |
| Cursore | nuovo a colori, `LARGE_POINTER_FLAG_96x96` |
| KLID | `0x0409` — **verificato corrispondente** alla tastiera reale |
| Nome computer | reale (`100E9YY1000LRE`) |
| Geometria | 2560×1080, dimensione fisica **334 mm → 82 DPI, plausibile** |
| Compressione canali | flag 1, livello 3 |

### 1.3 Remote Desktop Manager su Android — misurato il 3 agosto 2026

| Cosa | Valore |
|---|---|
| Identità | `[Unspecified platform, Unspecified version]` — **non si dichiara Android** |
| Protocolli richiesti | `SSL \| HYBRID` (0x03) — **accetta TLS puro** |
| Certificato autofirmato | accettato, connessione proseguita |
| TLS | **massimo TLS 1.2**, nessun SNI, 45 cipher fra cui Camellia e GOST `0xFF85` → OpenSSL vecchio |
| Cookie | `mstshash=<utente>` |
| EGFX | **10.7** — la più alta dei tre |
| **H.264** | **NO** — `AVC_DISABLED` ovunque (§1.4) |
| Frame acknowledge | **sì** |
| Canali dinamici | `RDPGFX`, `DISP`, `AUDIO_PLAYBACK`, `AUDIO_INPUT`, `CLIPRDR`, `TELEMETRY` (fallisce ad aprirsi) |
| **MS-RDPEI** | **non aperto** → il tocco arriva come mouse |
| Canali statici | `rdpdr`, `rdpsnd`, `cliprdr`, `drdynvc` |
| Audio | AAC no, Opus no, **PCM sì** |
| Clipboard | come mstsc, **senza** «can lock clip data» |
| KLID | `0x0409` — verosimilmente un valore fisso, vedi §6.1 |
| Nome computer | `localhost` |
| Geometria | 2560×984, dimensione fisica **1000 mm → 24 DPI, assurda** |
| Compressione canali | flag 0 |

**È un client severo**, della famiglia di mstsc: riceve, elabora, **riscontra** — e non disegna se
qualcosa non gli torna. Questo smentisce la tabella di §5.4 di `SPECIFICA.md`, che metteva
«FreeRDP / Android» nella stessa colonna degli indulgenti: quella misura era stata fatta con un client
Android ignoto.

### 1.4 ⛔ RDM non fa H.264

`gnome-remote-desktop` elenca i capability set uno per uno:

```
RDPGFX_CAPVERSION_8    flags 0x02   SMALL_CACHE
RDPGFX_CAPVERSION_81   flags 0x02   SMALL_CACHE          ← manca AVC420_ENABLED (0x10)
RDPGFX_CAPVERSION_10   flags 0x22   SMALL_CACHE | AVC_DISABLED
RDPGFX_CAPVERSION_101  flags 0x00   (campo flags non valido per la 10.1)
RDPGFX_CAPVERSION_102  flags 0x22   SMALL_CACHE | AVC_DISABLED
RDPGFX_CAPVERSION_103  flags 0x20   AVC_DISABLED
RDPGFX_CAPVERSION_104  flags 0x22   SMALL_CACHE | AVC_DISABLED
RDPGFX_CAPVERSION_107  flags 0xA2   SMALL_CACHE | AVC_DISABLED | SCALEDMAP_DISABLE
```

Conclusione del server: **`H264 (AVC444): false, H264 (AVC420): false`**.

**Verificato due volte, ed è definitivo.** Il selettore dei codec di RDM offre quattro voci — *RDP 6.0*
(bitmap RDP 6), *RDP 7.0* (RemoteFX), *RDP 8.0* (EGFX con RemoteFX Progressive), *Predefinito* — e
**nessuna voce per RDP 8.1, H.264 o AVC**. L'H.264 su EGFX arriva con la 8.1: non è nell'elenco perché
non c'è. Cambiando l'impostazione e ricollegandosi, i capability set restano **identici**.

RDM tiene correttamente distinte due cose: annuncia le versioni recenti del **protocollo** EGFX e
insieme dichiara che il **codec** H.264 non lo sa decodificare.

> **Un server che manda solo AVC420 mostra schermo nero su RDM.** Per costruzione, non per difetto.

### 1.5 ⚠ Sull'audio: nessuno dei due ha negoziato AAC

**Né mstsc né RDM** hanno dichiarato AAC o Opus. Entrambi solo PCM. [M]

Questo tocca §3.2 di `SPECIFICA.md`, che prevede AAC con PCM come base. Se tutti ripiegano su PCM,
l'AAC diventa codice scritto per nessuno.

> **Da non prendere per definitivo senza una seconda verifica.** mstsc supporta AAC in generale, e il
> risultato può dipendere da come `gnome-remote-desktop` offre i formati sul canale
> `AUDIO_PLAYBACK_DVC` piuttosto che dai client.
>
> Intanto l'ordine è chiaro: **PCM funziona con tutti e tre e va scritto per primo.** PCM stereo
> 16 bit sono ~1,4 Mbit/s, il 14 % del budget di 10 Mbps.

### 1.6 La matrice delle versioni EGFX

Il 3 agosto 2026, i tre client contro `gnome-remote-desktop` 48.1:

| Versione | mstsc | RDM | xfreerdp3 |
|---|:---:|:---:|:---:|
| 8.0 | ✓ `0x00` | ✓ `0x02` | ✓ |
| 8.1 | ✓ `0x00` ⚠ | ✓ `0x02` ⚠ | ✓ |
| 10.0 | ✓ `0x00` | ✓ `0x22` | |
| **10.1** | | ✓ `0x00` | |
| 10.2 | ✓ `0x00` | ✓ `0x22` | |
| 10.3 | ✓ `0x00` | ✓ `0x20` | |
| 10.4 | ✓ `0x00` | ✓ `0x22` | |
| **10.5** | ✓ `0x00` | | |
| **10.6** | ✓ `0x00` | | |
| **10.7** | | ✓ `0xA2` | |
| **Scelta** | **10.6** | **10.7** | **8.1** |
| **AVC420 / AVC444** | sì / sì | no / no | sì / no |

**Tre letture obbligatorie:**

1. ⚠ **In 8.1 mstsc dichiara `flags = 0x00`, senza `AVC420_ENABLED`.** Un server che ripiega sulla 8.1
   con mstsc **spegne l'H.264** → zero fotogrammi → nero. È il primo dei cinque difetti di §5.4 di
   `SPECIFICA.md`, ora **confermato sul filo**: con mstsc si deve salire alla famiglia 10.x.
2. **Ogni client ha versioni esclusive**: la 10.1 solo RDM, le 10.5 e 10.6 solo mstsc, la 10.7 solo
   RDM. Conoscerle tutte non è pignoleria (R2).
3. **mstsc lascia tutti i flag a zero**: chiede il massimo e non concede nulla.

### 1.7 Quali codec rende ciascun client

| Codec | ID | mstsc | RDM | FreeRDP |
|---|---|:---:|:---:|:---:|
| `AVC420` | `0x000B` | **sì** | **no** | sì |
| `AVC444` / `v2` | `0x000E`/`0x000F` | sì | no | no |
| `CAPROGRESSIVE` (RFX Prog.) | `0x0009` | presumibilmente | **sì** [M, 4 ago] | sì |
| `PLANAR` | `0x000A` | ? | **no** [M] | sì |
| `UNCOMPRESSED` | `0x0000` | **no** [M, 1 ago] | ? | sì |

**Il dato misurato più utile di questa tabella**: xrdp 0.10.1 è compilata senza encoder H.264 e manda
la schermata di accesso come **PLANAR su EGFX**. RDM **riscontra il fotogramma e mostra nero**. [M, 3
agosto] La causa più economica è che non renda il planar su EGFX; non è dimostrato con certezza, ma il
comportamento — ack sì, disegno no — è la firma classica.

> ✅ **RDM rende RemoteFX Progressive. Verificato il 4 agosto 2026, e il percorso Android regge.**
>
> Era il rischio aperto più grosso del progetto: RFX Progressive è il codec su cui poggia tutto il
> percorso Android, e **non lo si era mai visto funzionare** — la prova del 3 agosto mandava PLANAR.
>
> **Come è stata misurata.** `gnome-remote-desktop` 48.1 dentro la VM di runtime, su una sessione
> GNOME **Wayland** senza monitor. La VM non ha accelerazione grafica, quindi grd non ha VA-API e non
> può codificare H.264: gli resta solo RFX Progressive. Certificato **prima** di collegare il
> telefono, con un client FreeRDP strumentato — 6 fotogrammi `progressive_decompress`, tutti
> decodificati, **zero** AVC420. Poi si è collegato RDM: **il desktop compare e funziona.**
>
> Il registro di grd conferma che era proprio lui, e ricalca l'impronta di §1.3:
>
> ```
> [RDP.CLIPRDR] long format names, stream file clip, ... huge file support   (senza «can lock clip data»)
> [RDP.AUDIO_PLAYBACK] Client Formats: [AAC: false, Opus: false, PCM: true]
> [RDP.RDPGFX] Accepting RDPGFX_CAPVERSION_107 — H264 (AVC444): false, H264 (AVC420): false
> ```
>
> Cioè: alla versione EGFX **più alta dei tre client**, con l'H.264 spento, e con l'unico codec che
> grd poteva mandargli. La decisione di §10.1 — due codec sulla stessa pipeline — è confermata da una
> misura invece che dedotta da un selettore.

---

## 2. Le regole assolute

Ognuna di queste, violata, produce **schermo nero, disconnessione, o un'immagine sbagliata** — mai un
messaggio d'errore leggibile.

### R1 — `CreateSurface` e `MapSurfaceToOutput` sono due comandi, e servono entrambi

```
CreateSurface(surfaceId, w, h, XRGB_8888)
MapSurfaceToOutput(surfaceId, originX, originY)     ← NON opzionale
```

**Chi punisce**: mstsc, RDM. FreeRDP disegna lo stesso. [M, 2 agosto — due giorni per trovarlo]
[R: in `gnome-remote-desktop` le due chiamate sono adiacenti in `acquire_gfx_surface`]

### R2 — l'elenco delle versioni EGFX deve essere completo, e la 10.6 ha due valori

```
10.7 0x000A0701   10.6 0x000A0600  ← e ANCHE 0x000A0601 (valore errato ma diffuso)
10.5 0x000A0502   10.4 0x000A0400   10.3 0x000A0301   10.2 0x000A0200
10.1 0x000A0100   10.0 0x000A0002   8.1  0x00080105   8.0  0x00080004
```

Si sceglie **la più alta che il client dichiara**, si conferma **quella sola** con `CapsConfirm`.

Il valore della 10.6 nella specifica era sbagliato; l'errata `[MS-RDPEGFX]-180912` lo corregge.
**Vanno accettati entrambi.** [S] [R: FreeRDP definisce `RDPGFX_CAPVERSION_106` e `..._106_ERR`]

**Chi punisce**: ripiegare sulla 8.1 con mstsc **spegne l'H.264** (§1.6). [M]

### R3 — la logica dei flag AVC, e la scelta del codec

```
versione ≥ 10.0 :  AVC420 e AVC444 ⟺ NON (flags & RDPGFX_CAPS_FLAG_AVC_DISABLED 0x20)
versione = 8.1  :  AVC420        ⟺     (flags & RDPGFX_CAPS_FLAG_AVC420_ENABLED 0x10)
versione = 8.0  :  nessun AVC
```

**Il risultato sceglie il codec** (deciso il 3 agosto, §10.1):

```
AVC disponibile  →  RDPGFX_CODECID_AVC420        (0x000B)   Windows, Linux
AVC disabilitato →  RDPGFX_CODECID_CAPROGRESSIVE (0x0009)   Android
```

La scelta si fa **una volta, al `CapsConfirm`**, e vale per la connessione. Mandare AVC420 a un client
che ha dichiarato `AVC_DISABLED` produce **schermo nero**: riscontra i fotogrammi e non disegna.
[M, 3 agosto: è esattamente ciò che fa RDM] [R]

### R4 — allineamento del codificatore: larghezza ×16, **altezza ×64**

```c
aligned_width  = w + (w % 16 ? 16 - w % 16 : 0);
aligned_height = h + (h % 64 ? 64 - h % 64 : 0);
```

L'altezza a 64 è la parte che sorprende. **Il bordo in eccesso si riempie, non si riduce lo schermo**:
il desktop resta della misura chiesta dal client.

**Chi punisce**: mstsc — rinegoziazione e disconnessione. [M, 2 agosto] [R]

> ⚠ **Osservazione del 4 agosto, da non scambiare per una smentita.** Sul banco di R5,
> `freerdp-shadow-cli3` serve uno schermo 1282×802 su una superficie **1296×816**, cioè allinea
> **entrambi i lati a 16**, non l'altezza a 64. Non è stato provato con mstsc, quindi **R4 resta**:
> allineare a 64 soddisfa anche il 16, quindi seguirla non è mai sbagliato — al più spreca qualche
> riga. Resta da capire se il ×64 sia una pretesa di mstsc o una diagnosi imprecisa del 2 agosto;
> si chiude con una connessione mstsc, quando ce ne sarà una sotto mano.
>
> Il difetto vero del 2 agosto era comunque un altro, e la traccia lo mostra: l'altezza veniva
> **troncata** a 1024 invece che riempita a 1088 (`traccia-mstsc.log`, «fotogramma AVC420
> larghezza=2560 altezza=1024» con desktop 1080). Il desktop perdeva 56 righe, ed è quello che mstsc
> non ha digerito.

> ⚠ **Secondo indizio che il ×64 non è una pretesa del protocollo.** [R, 7 agosto 2026, da `KRdp` e
> `kpipewire`]
>
> `KRdp` **non allinea affatto** a 16 o 64: `kpipewire` allinea a **2** con un filtro `pad`, con il
> commento *«otherwise the size adjustment below will insert a row/column of garbage instead of
> black»* (`kpipewire/src/libx264encoder.cpp:29-32`), e lascia al codificatore il ritaglio dichiarato
> nella SPS — con 1080 righe x264 codifica 1088 macroblocchi e dice al decodificatore di tagliare.
> E serve mstsc.
>
> **Che cosa resta certo, e va tenuto**: il principio «il bordo si **riempie**, non si riduce lo
> schermo» (il commento di kpipewire lo conferma: senza il riempimento entra spazzatura invece di
> nero), e il divieto di **troncare**, che è il difetto vero del 2 agosto. Che cosa diventa
> `[?]`: il **quanto** — se il ×64 sia una pretesa di mstsc, del nostro codificatore, o una diagnosi
> imprecisa. Allineare a 64 non è mai sbagliato e costa qualche riga di bordo: **si continua a fare
> così**, ma senza attribuirgli difetti che non causa. Insieme a R11, questa è una regola del nostro
> **decodificatore**, non del protocollo.

### R5 — le due convenzioni di geometria, nello stesso protocollo

| Struttura | Convenzione |
|---|---|
| `RDPGFX_SURFACE_COMMAND` (`left/top/right/bottom`) | `right = x + width` → **esclusiva** [R] |
| `RECTANGLE_16` della metablock AVC420 | `right = x + width` → **esclusiva** [M, 4 agosto] |
| `MONITOR_DEF` di `ResetGraphics` | `right = left + width − 1` → **inclusiva** [R] — ma vedi il riquadro: **sbagliarla non produce uno schermo nero** |

> ✅ **Chiusa il 4 agosto: i bordi della regione AVC420 sono ESCLUSIVI.** §5.4 di `SPECIFICA.md`
> annotava «inclusivi»: è sbagliato, ed era quasi certamente un artefatto dell'API di IronRDP.
>
> **Come è stata misurata.** Un server FreeRDP (`freerdp-shadow-cli3` 3.15, cioè la stessa libreria di
> REMOTIX) davanti a uno schermo di misura deliberatamente **non allineata, 1282×802**, con il solo
> AVC420 acceso. I rettangoli sono stati letti nel client intercettando `avc420_decompress`: fra quei
> valori e i byte del filo c'è un solo passaggio, `rdpgfx_read_rect16`, che legge quattro `UINT16` in
> fila senza aggiustamenti.
>
> ```
> fotogramma 1  superficie 1296x816  rettangoli 1
>    rect[0]  left=0 top=0 right=1282 bottom=802     ← right = larghezza, non larghezza−1
> fotogramma 2  superficie 1296x816  rettangoli 6
>    rect[0]  left=64 top=0 right=128 bottom=64      ← riquadri di 64 px: right−left = 64, non 63
> ```
>
> Concorda con tutte le altre fonti: `gnome-remote-desktop` scrive `right = x + width`; il consumatore
> di FreeRDP calcola `size = right − left` e itera `for (y = top; y < bottom; y++)` (`diff_tile`); il
> produttore di FreeRDP calcola `nWidth = extents->right − extents->left`; e `rdpgfx_read_rect16`
> **rifiuta come dato non valido `left >= right`** — con la convenzione inclusiva un rettangolo largo
> un pixel avrebbe `left == right`, quindi la convenzione esclusiva è scritta nel controllo di
> validità.
>
> Da notare, per non confonderle: **i rettangoli descrivono il contenuto vero, non la superficie
> allineata.** Sopra, la superficie è 1296×816 e i rettangoli si fermano a 1282×802.

> ⚠ **E il `MONITOR_DEF` inclusivo è la scrittura corretta, non una causa di schermo nero.**
> [R, 7 agosto 2026, dal codice di `KRdp`]
>
> `KRdp` scrive il `MONITOR_DEF` di `ResetGraphics` **esclusivo** (`right = width`, non `width − 1`,
> `krdp/src/VideoStream.cpp:800-802`) — e FreeRDP lo serializza così com'è. Cioè: **dichiara da un
> anno un monitor di un pixel più grande, in tutte le versioni, e funziona con mstsc.**
>
> Questa riga resta come la specifica la vuole, e va scritta inclusiva. Ma cambia la **diagnostica**:
> se un giorno si cerca la causa di un'immagine sbagliata, **la convenzione del `MONITOR_DEF` non è
> un sospetto di primo grado** — un errore di ±1 lì non produce né nero né disconnessione. I sospetti
> di primo grado restano R1 (la superficie non mappata) e R2 (la versione EGFX ripiegata). Vale anche
> a rovescio: se avessimo attribuito a questa riga un difetto passato, quell'attribuzione va rifatta.

### R6 — `ResetGraphics` non si manda mai con l'elenco monitor vuoto

`monitorCount ≥ 1` sempre, e **tutte le superfici vanno cancellate prima**.

**Chi punisce**: mstsc — immagine disegnata fuori posto, spostata a destra. [M, 2 agosto]
[R: `gnome-remote-desktop` lo verifica con `g_assert`]

### R7 — con EGFX attivo, il ridimensionamento **non** passa dalla riattivazione

La misura nuova si comunica **ridichiarando la tela grafica** (nuova superficie + `ResetGraphics`).
Un `Deactivate All` costringe il client a rifare lo scambio di capacità.

**Chi punisce**: il client Android — dopo una riattivazione **non rinegozia più EGFX per il resto
della sessione**. [M, 2 agosto]

### R8 — un `MONITOR_LAYOUT` arrivato prima della negoziazione EGFX si rinvia

I client Android chiedono la propria misura **entro un decimo di secondo dalla connessione**, prima di
aver negoziato EGFX. Applicarlo subito ricade in R7.

Si rinvia fino a ~1,5 s aspettando la pipeline. Solo se non arriva affatto si ricorre alla
riattivazione. [M, 2 agosto]

> ⚠ **Con l'ordine di apertura dei canali della fase 6, il caso non si presenta più — e il rinvio
> resta lo stesso.** [M, 5 agosto]
>
> Il client non può chiedere una misura prima di aver ricevuto le **capacità** MS-RDPEDISP, e quelle
> partono solo quando il client conferma la creazione del canale, che avviene dopo `DRDYNVC_READY`
> — cioè nella stessa finestra in cui si negozia EGFX. Misurato su RDM: `canale DISP aperto` e
> `EGFX negoziato` a **un millesimo di distanza**, e il primo `MONITOR_LAYOUT` quasi quattro secondi
> dopo. La misura del 2 agosto era su un server che apriva i canali in un altro ordine.
>
> **Il rinvio non si toglie**: costa niente, e l'ordine dei canali è una proprietà della nostra
> implementazione, non del protocollo. Una regola che smette di servire perché il codice è cambiato
> torna a servire appena il codice cambia di nuovo.

### R9 — l'ultimo fotogramma si conserva e si rispedisce

Il compositore manda un fotogramma **solo quando qualcosa cambia**. Un fotogramma arrivato prima che il
client abbia finito di negoziare non si può disegnare, e su un desktop fermo non ne arriverà un altro:
nero a tempo indeterminato.

Insidioso perché **si corregge da sé** appena qualcuno muove qualcosa: in prova sembra un ritardo
d'avvio. [M, 2 agosto] [R: `invalidate_surface` ripropone `last_buffer`]

### R10 — dopo un cambio di misura si aspetta il ridisegno

Mutter manda un fotogramma **subito** dopo il cambio, prima che il desktop si sia ridisegnato: sfondo
vecchio e resto vuoto. Con R9 quell'immagine parziale **resta**.

Il riferimento non aspetta un silenzio: **inibisce il rendering** e lo riattiva solo quando *tutti* gli
stream hanno confermato la misura nuova. È la forma giusta. [M, 3 agosto] [R]

> ⛔ **E NOI AVEVAMO SCRITTO LA FORMA SBAGLIATA — quella che questa riga scarta.** [M, 6 agosto 2026]
>
> Si aspettava che i fotogrammi **smettessero di arrivare** (300 ms di quiete, tetto 2,5 s). Su un
> desktop fermo funziona; **su un desktop che lavora il silenzio non arriva mai**, si va sempre a
> sbattere contro il tetto, e ogni ridimensionamento costa **due secondi e mezzo** in cui al client
> non parte un fotogramma. Misurato su una sessione vera con un video in riproduzione:
>
> ```
> 20:07:21.488  ridimensiono il palco: 1024x768 → 2560x1010
> 20:07:23.994  atteso il ridisegno alla misura nuova: 44 fotogrammi raccolti   ← 2,5 s
> ```
>
> **Quanto dura davvero il ridisegno: due fotogrammi**, e non è una stima — sono i fotogrammi
> salvati su disco prima di RDP, guardati uno per uno:
>
> | | |
> |---|---|
> | fotogramma 0 | la tela è già 2560×1010 ma **solo l'angolo** è ridisegnato, alla misura di prima; il resto è bianco |
> | fotogramma 1 | completo e corretto alla misura nuova |
>
> Quindi si smette di raccogliere **appena arrivano due fotogrammi**, senza aspettare alcun silenzio;
> il silenzio resta solo per il caso opposto, un desktop così fermo da non mandarne nemmeno due.
> Misurato dopo: **119–149 ms** dalla richiesta del client alla tela ridichiarata, contro 2 536.
>
> Il pavimento è quello: due fotogrammi a 30 al secondo sono 66 ms, e scendere sotto significa
> tornare a spedire il fotogramma parziale.

> **Il transitorio che resta è del CLIENT, e non è un difetto nostro.** [M, 6 agosto 2026]
>
> Nei ~120 ms in cui la geometria è instabile non si spedisce nulla (R10-bis): il client resta
> sull'ultima immagine, alla misura vecchia, poi riceve `ResetGraphics` con la tela nuova e **riadatta
> da sé** quel che ha finché non arriva il primo fotogramma buono. Chi guarda vede per un istante due
> immagini a due scale diverse, e la tentazione è chiamarlo «sovrapposizione».
>
> **Come si è accertato che non è nostro**: salvando i fotogrammi come Mutter li consegna, prima di
> RDP (`REMOTIX_FOTO=<cartella>`, che si arma da sé a ogni ridimensionamento). Là dentro non c'è
> alcuna sovrapposizione — c'è il parziale del fotogramma 0, che non spediamo, e il completo del
> fotogramma 1, che spediamo. È la domanda di §5.7 di `SPECIFICA.md` — «GNOME disegna male» o «il
> client mostra male» — posta finalmente allo strumento giusto invece che per deduzione.

### R10-bis — un `MONITOR_LAYOUT` che arriva **durante** un ridimensionamento è un'eco

*Misurata il 5 agosto 2026, chiudendo la fase 6.*

Un ridimensionamento non è istantaneo: fra il `MONITOR_LAYOUT` e la tela ridichiarata passa circa
**mezzo secondo** — `pw_stream_update_params`, la conferma di Mutter, l'attesa del ridisegno (R10).
In quel mezzo secondo il client continua a mandarne, e **quelle richieste descrivono la finestra
com'era prima di conoscere la nostra risposta**.

Applicarle innesca una rincorsa: si applica la misura vecchia, il client vi si adegua, e rimanda
indietro quella di prima. **Va avanti da sola.**

| | 8 trascinamenti in 2,4 s |
|---|---|
| applicando ogni richiesta | **38 richieste, 37 ridimensionamenti**, e continuavano per oltre 40 s a mani ferme |
| con assestamento + guardia sull'eco | **2–4 ridimensionamenti**, poi silenzio |

Su Android ogni ridimensionamento è anche un riavvio del decodificatore
([`client-android.md`](client-android.md) §4.3): 37 invece di 2 non è una questione di eleganza.

**Che la causa sia la nostra latenza e non il protocollo** lo dicono due misure di controllo, ed è
il motivo per cui vanno fatte entrambe prima di toccare il codice:

| Banco | Esito |
|---|---|
| scena sintetica, stessa raffica (ridimensionamento **istantaneo**, non c'è palco) | 8 richieste, 8 applicazioni, **converge** |
| desktop vero, 3 trascinamenti **distanziati di 3 s** | 3 richieste, 3 applicazioni, **converge** |

Cioè l'eco compare quando, e solo quando, una richiesta arriva mentre il palco sta cambiando misura.

**Le due contromisure**, entrambe necessarie:

1. **assestamento**: non si applica finché le richieste non smettono di arrivare (~300 ms di quiete,
   con un tetto ~1,2 s), e a ridimensionamento concluso il conto **riparte**;
2. **guardia sull'eco**: si scarta la richiesta che chiede **esattamente la misura appena lasciata**
   entro ~250 ms dalla ridichiarazione della tela. Il confronto va fatto **all'arrivo**, non alla
   raccolta: la firma dell'eco è che arriva *subito*, e rimandare il confronto significa misurare
   un tempo già scaduto.

> ⚠ **Quel che resta, ed è del client**: quando il server ridimensiona, il client porta la propria
> finestra alla misura ricevuta e così **sovrascrive il proprio obiettivo**. Trascinando in fretta,
> l'ultimo trascinamento si perde *dentro il client* — `xf_disp_queueResize` di FreeRDP non spedisce
> mai subito e affida l'invio a un timer da un secondo, che nel frattempo trova l'obiettivo
> riscritto. Con trascinamenti distanziati non succede. Non è aggirabile dal server.

### R11 — mai fotogrammi B, mai codifica di campo

Profilo **H.264 High con `constraint_set4_flag = constraint_set5_flag = 1`**, cioè *Constrained High*.

1. il decodificatore software più diffuso su Android (**OpenH264**) supporta *Constrained Baseline* e
   *Constrained High*, e nient'altro; [R]
2. un fotogramma B richiede di attendere il successivo: **un fotogramma di latenza in più**.

CABAC e trasformata 8×8 invece **vanno accesi**: sono dentro Constrained High e valgono 5–10 % di
banda. [R: è esattamente quello che `gnome-remote-desktop` produce]

### R12 — si manda `SET_ERROR_INFO` prima di ogni chiusura

| Situazione | Codice |
|---|---|
| Il server chiude di sua iniziativa | `ERRINFO_RPC_INITIATED_DISCONNECT` 0x01 |
| **Rifiuto: c'è già qualcuno** | `ERRINFO_SERVER_DENIED_CONNECTION` 0x07 |
| Soppiantato da un'altra connessione | `ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION` 0x05 |
| **L'utente è uscito dalla sessione** | `ERRINFO_LOGOFF_BY_USER` 0x0C |
| Capacità inaccettabili | `ERRINFO_BAD_CAPABILITIES` 0x10EA |
| Layout monitor non valido | `ERRINFO_BAD_MONITOR_DATA` 0x1129 |
| Guasto grafico | `ERRINFO_GRAPHICS_SUBSYSTEM_FAILED` 0x112F |

> ⛔ **SERVONO DUE CHIAMATE, e questa riga per due giorni ne ha indicata una sola.**
>
> ```c
> freerdp_set_error_info(peer->context->rdp, codice);   /* REGISTRA          */
> freerdp_send_error_info(peer->context->rdp);          /* SPEDISCE          */
> peer->Disconnect(peer);                               /* e solo adesso     */
> ```
>
> `freerdp_set_error_info` **non manda niente**: registra il codice e lo scrive nel proprio
> registro. A metterlo sul filo è `freerdp_send_error_info`, che è una funzione a parte. E
> l'ordine conta: `Disconnect` butta giù il trasporto, e ciò che non è ancora partito non parte
> più.
>
> **Come si è visto.** Non dal nostro registro, che diceva compìto «congedo il client: … (0x000C)»,
> ma da quello del **client**, che alla stessa ora diceva soltanto:
> `[ERROR] transport_read_layer: BIO_read retries exceeded` e `Network disconnect!`. È la forma più
> pura del difetto che R12 esiste per togliere — e ci è cascata dentro proprio la regola scritta
> per evitarlo. [M, 4 agosto]
>
> **Corollario di metodo**: un congedo si verifica **dal lato che lo deve ricevere**. Il registro di
> chi manda dice che ha chiamato una funzione, non che il byte è arrivato.

> ⛔ **E SERVE ANCHE IL MOMENTO GIUSTO: prima dell'attivazione non parte.**
>
> `SET_ERROR_INFO` è un **Share Data PDU**: esiste solo dopo lo scambio Demand Active / Confirm
> Active, cioè dopo che la sessione RDP è stata **attivata**. Chiamare `freerdp_send_error_info`
> dentro `Capabilities` o dentro `PostConnect` — dove stanno naturalmente i rifiuti, perché è lì
> che si scopre di dover rifiutare — lo spedisce in un punto in cui il client non lo aspetta.
>
> **Come si è visto**: non come un guasto, ma come un'**intermittenza**. Lo stesso controllo del
> banco, la seconda connessione rifiutata, chiudeva `xfreerdp3` ora con uscita **7** (codice
> ricevuto) ora con uscita **147** (nessun codice), senza che nulla cambiasse fra un giro e
> l'altro. Un difetto che passa metà delle volte è più caro di uno che non passa mai: per due
> giorni è stato archiviato come «rumore del banco». [M, 4 agosto]
>
> **La forma corretta**: un rifiuto deciso presto non si spedisce, si **registra**; la connessione
> prosegue fino all'attivazione — **senza allestire nulla e senza prendere il posto** — e il
> motivo si dice nella callback `Activate` (`psPeerActivate`), che è il primo istante in cui un
> PDU di dati ha dove andare.
>
> ```c
> /* in Capabilities / PostConnect */
> cp->rifiuto = codice; cp->rifiuto_perche = perche;
> return TRUE;                       /* si prosegue solo per poter dire di no */
>
> /* in Activate */
> cp->attivo = TRUE;
> if (cp->rifiuto) { congeda(peer, cp->rifiuto, cp->rifiuto_perche); return FALSE; }
> ```

**Chi punisce**: il client Android — alla sola chiusura del socket **resta lì**, mostrando l'ultimo
fotogramma. Uno sfondo pulito senza finestre è visivamente identico a un desktop vivo. [M, 3 agosto]

### R13 — solo TLS, senza NLA: validato su tutti e tre

| Client | Chiede | Accetta `PROTOCOL_SSL`? |
|---|---|---|
| **mstsc** (Win 11) | `SSL \| HYBRID \| HYBRID_EX` (0x0B) | **sì** — prosegue con TLS, MCS, capacità, EGFX |
| **RDM** (Android) | `SSL \| HYBRID` (0x03) | **sì** |
| **xfreerdp3** | `SSL \| HYBRID` (0x03) | **sì** |

§3.6 di `SPECIFICA.md` — solo TLS, niente NLA — **regge su tutti e tre**. Nessuno pretende NLA. [M]

**Ma TLS 1.2 va supportato**: RDM non fa TLS 1.3, e un server solo-1.3 lo escluderebbe. [M]

### R14 — la guardia parte da *negato*

Senza NLA l'autenticazione avviene **dentro** il Client Info PDU, e un client può non mandare
credenziali affatto. Un server che valida «se ci sono credenziali» **non valida niente**.

La guardia parte da negato a ogni connessione, e solo il validatore la apre. Chi non passa di lì non
riceve un pixel e non comanda nulla. [M, 3 agosto]

---

## 3. Cosa dichiarare alla connessione

### 3.1 Nella risposta di negoziazione X.224

```c
selectedProtocol = PROTOCOL_SSL;
flags = EXTENDED_CLIENT_DATA_SUPPORTED    /* 0x01 - senza, niente blocco monitor  */
      | DYNVC_GFX_PROTOCOL_SUPPORTED;     /* 0x02 - dichiara che il server fa EGFX */
```

> **`EXTENDED_CLIENT_DATA_SUPPORTED` è una bandiera da un bit che decide se il multi-monitor è
> possibile.** Senza, il client non manda mai `CS_MONITOR`. [S]
>
> Sui due server osservati: **grd accende entrambi** (`flags = 0x03`), **xrdp 0.10.1 solo il primo**
> (`0x01`) pur facendo EGFX — e i client negoziano lo stesso. Non è bloccante, ma è informazione
> corretta e va data. [M, 3 agosto]

### 3.2 Impostazioni FreeRDP del peer

Base di partenza, dal riferimento, adattata alle nostre scelte:

```c
/* sicurezza: noi TLS puro, NON come gnome-remote-desktop che impone NLA */
RdpSecurity = FALSE;  TlsSecurity = TRUE;  NlaSecurity = FALSE;

ColorDepth = 32;
SupportGraphicsPipeline   = TRUE;
GfxAVC444v2 = GfxAVC444 = GfxH264 = FALSE;   /* si accendono dopo, in CapsAdvertise */
GfxSmallCache = GfxThinClient = FALSE;
SurfaceFrameMarkerEnabled = FrameMarkerCommandEnabled = TRUE;
PointerCacheSize = 100;
FastPathOutput = TRUE;
NetworkAutoDetect = TRUE;
RefreshRect = FALSE;
SupportMultitransport = FALSE;              /* niente UDP */
VCFlags = VCCAPS_COMPR_SC;  VCChunkSize = 16256;
HasExtendedMouseEvent = HasHorizontalWheel = HasRelativeMouseEvent = TRUE;
UnicodeInput = TRUE;
OsMajorType = OSMAJORTYPE_UNIX;  OsMinorType = OSMINORTYPE_PSEUDO_XSERVER;
```

### 3.3 Cosa pretendere dal client

| Requisito | Se manca |
|---|---|
| Graphics Pipeline (EGFX) | chiudere, con `ERRINFO_BAD_CAPABILITIES` |
| 32 bpp dichiarato insieme ai codec | chiudere: è violazione di protocollo |
| `DesktopResize` | chiudere |
| Canale `DRDYNVC` | chiudere |
| Pointer cache > 0 | chiudere |
| Fastpath output | chiudere |

> **Chiudere non basta: bisogna dire perché** (R12). Un client che riceve solo una chiusura di socket
> mostra «errore di rete» e l'utente non impara niente.

---

## 4. Capability set

Dei 30, ne servono **13–15**. Gli altri si lasciano spenti.

**Da riempire**: `GENERAL` 0x01, `BITMAP` 0x02, `ORDER` 0x03 (con tutti gli ordini a zero),
`CONTROL` 0x05, `ACTIVATION` 0x07, `POINTER` 0x08, `SHARE` 0x09, `INPUT` 0x0D, `FONT` 0x0E,
`VIRTUAL_CHANNEL` 0x14, `MULTI_FRAGMENT_UPDATE` 0x1A, `LARGE_POINTER` 0x1B,
`SURFACE_COMMANDS` 0x1C, `BITMAP_CODECS` 0x1D (può restare vuoto), `FRAME_ACKNOWLEDGE` 0x1E.

**Da NON dichiarare**: bitmap cache (tutte le versioni), color cache, brush, glyph cache, offscreen
cache, draw nine grid, GDI+, RAIL, window.

`LARGE_POINTER`: accendere almeno `LARGE_POINTER_FLAG_96x96` (0x01). [M: mstsc, RDM e xfreerdp3 lo
dichiarano tutti]

---

## 5. La sequenza EGFX, nell'ordine

```
1.  il client apre il canale dinamico  Microsoft::Windows::RDS::Graphics
2.  CAPSADVERTISE  (client → server)     entro 10 s, altrimenti si chiude
3.  CAPSCONFIRM    (server → client)     UNA sola versione, la più alta  (R2)
4.  RESETGRAPHICS  (server → client)     monitorCount ≥ 1, bordi INCLUSIVI  (R5, R6)
5.  CREATESURFACE                         XRGB_8888
6.  MAPSURFACETOOUTPUT                    ← non dimenticarlo mai  (R1)
7.  per ogni fotogramma:
       STARTFRAME(frameId, timestamp)
       WIRETOSURFACE_1(surfaceId, codec, left/top/right/bottom ESCLUSIVI, metablock)
       ENDFRAME(frameId)
8.  FRAMEACKNOWLEDGE (client → server)
```

**Altri PDU da gestire**, anche solo per rispondere:

- `CACHEIMPORTOFFER` → rispondere con un `CACHEIMPORTREPLY` **vuoto**. Non ignorarlo.
- `QOEFRAMEACKNOWLEDGE` → accettare e ignorare.
- un secondo `CAPSADVERTISE` è lecito **solo** se la versione iniziale era ≥ 10.3.

**`queueDepth == 0xFFFFFFFF`** (`SUSPEND_FRAME_ACKNOWLEDGEMENT`) significa *«non ti mando più
riscontri»*. Un server che aspetta i riscontri per regolare il flusso **si blocca per sempre** se non
lo gestisce. [S] [R]

`totalFramesDecoded` permette di ricostruire i fotogrammi in volo anche con ack persi:
`in_volo = totale_codificati − totalFramesDecoded`.

> ⚠ Va usato come **pavimento, mai come tetto**: si applica solo quando *abbassa* il conto locale.
> Serve a rimettersi in pari quando un riscontro si perde; un client che dichiarasse un totale più
> basso del vero — o zero, come fa chi non lo tiene — non deve poter far credere che in volo ce ne
> siano più di quanti ne siano partiti.

### 5.1 La misura della rete (MS-RDPBCGR 2.2.14)

| Cosa | Come | Perché così |
|---|---|---|
| **Cadenza sonde** | 70 ms mentre si disegna, 700 ms a riposo | dal riferimento; a riposo non c'è niente da regolare |
| **Accoppiamento** | ogni sonda col suo numero di sequenza e il suo istante | R20: i campi della libreria misurano un'altra cosa |
| **Media** | finestra mobile di 500 ms; il minimo è l'RTT base | una rete che migliora deve poter dimenticare |
| **Banda** | solo su fotogrammi ≥ 10 KB, uno per volta, numero di sequenza 0 | sotto, il tempo del client (millisecondi interi) è zero |
| **Marcatori** | attorno allo **svuotamento della coda**, non all'invio | R19 |
| **`NETCHAR_RESULT`** | al massimo una al secondo, e solo con banda e RTT noti | è informativa: il client non ne fa niente di urgente |

**Il limite dichiarato**: su rete locale il client risponde `1 ms` e il risultato è dell'ordine dei
100 Mbit/s. Non è un errore ed è inutile levigarlo — la misura di banda del protocollo serve a
distinguere una rete lenta da una veloce, non a dare un numero.

> ⛔ **E IL VALORE PUÒ ESSERE VECCHIO DI ORDINI DI GRANDEZZA, proprio quando servirebbe.**
> [M, 7 agosto 2026, fase 10]
>
> La misura si aggancia **solo ai fotogrammi ≥ 10 KB**, e dopo il passaggio a VBR (R31) un desktop
> fermo produce fotogrammi da poche centinaia di byte: la misura **non parte più**, e l'ultimo
> valore resta lì. Misurato strozzando il collegamento:
>
> | strozzatura vera | banda riportata |
> |---|---|
> | 200 kbit/s | **176 kbit/s** — giusta, perché i fotogrammi erano abbastanza grossi |
> | 100 kbit/s | **220 136 kbit/s** — il valore di prima, mai aggiornato |
>
> **Conseguenza per chi la usa**: `rete_banda_kbit()` non si può leggere come «la banda di adesso».
> Va usata solo se **fresca** — e chi decide qualcosa di importante deve avere un secondo segnale
> che non dipende dalla dimensione dei fotogrammi: l'RTT e il conto dei fotogrammi in volo, che
> arrivano da ogni riscontro.

> ⛔ **E NEMMENO UN CAMPIONE FRESCO BASTA: LA MISURA SALTA DI DUE ORDINI DI GRANDEZZA.**
> [M, 7 agosto 2026]
>
> Con la linea tenuta **ferma a 400 kbit/s**, due campioni consecutivi hanno riportato
> **332 kbit/s** e **104 304 kbit/s**. Il secondo non è un guasto: è il limite di questa sezione —
> il client misura a millisecondi interi, e una finestra che si chiude dentro lo stesso millesimo
> produce un numero enorme.
>
> Chi ci decide sopra **oscilla**, e ogni oscillazione costa un fotogramma chiave. È successo alla
> prima stesura dell'adattamento del bitrate: `10000 → 2000 → 10000` in un minuto, a linea immobile.
>
> **Due metà della stessa cura, e servono entrambe:**
>
> 1. **si prende la mediana degli ultimi campioni freschi**, non l'ultimo — un singolo valore
>    assurdo non la sposta, e sotto i tre campioni si risponde «non lo so»;
> 2. **si cambia solo se cambierebbe qualcosa**: abbassare il tetto sotto quel che si sta già
>    producendo non toglie un byte, alzarlo quando non si sta toccando quello attuale non aggiunge
>    un pixel. Su un desktop fermo — cioè quasi sempre — il tetto è irrilevante, e la cosa giusta è
>    lasciarlo dov'è.
>
> Misurato dopo la correzione, nelle stesse condizioni che prima davano tre cambi al minuto:
> **zero cambi in due minuti**, e il client non se ne accorge.

### 5.2 Il regolatore a posti-fotogramma

```
soglia = MAX(2, MIN(rtt · fps / 1e6 + 2, fps))
si strozza a  in_volo ≥ soglia
si riprende a in_volo ≤ 1
```

Cioè: quanti fotogrammi stanno in volo nel tempo di un round trip, più due. Il tetto a `fps` evita che
una rete pessima autorizzi una coda lunga un secondo — un desktop che risponde con un secondo di
ritardo invece di uno che rallenta.

L'isteresi (si riprende a ≤ 1, non a soglia−1) è del riferimento: con una soglia sola si oscilla a
ogni fotogramma attorno al punto di lavoro.

**Rispetto a `gnome-remote-desktop`, che ha tre stati e i «posti» calcolati su `ack_rate`/`enc_rate`,
qui gli stati sono due.** Non è una scorciatoia: là il renderer è guidato dal danno e può produrre a
60 al secondo, quindi serve un numero di posti; qui la produzione è già scandita dal battito del
ciclo, e l'unica domanda è «passo o non passo».

Misurato il 5 agosto, con `tc netem delay 120ms rate 250kbit` fra VM e client:

| | rete libera | strozzata |
|---|---|---|
| RTT medio | 6 ms | 556 ms |
| soglia | 2 | 18 |
| fotogrammi in volo, massimo | 1 | **10** — mai oltre la soglia |
| fotogrammi al secondo | 30 | 23 |

**`queueDepth == 0xFFFFFFFF`**: il regolatore si toglie di mezzo e non torna. Con quei client il
controllo di flusso non c'è, ed è il prezzo che il protocollo impone. Nessuno dei tre client di
riferimento lo chiede a comando: si prova con `--fingi-riscontri-sospesi`, che lo simula dopo cento
fotogrammi — cioè mentre ce ne sono in volo e il regolatore può essere strozzato.

---

## 6. Input — le conversioni esatte

### 6.1 Tastiera

```c
fullcode = (flags & KBD_FLAGS_EXTENDED) ? scancode | KBDEXT : scancode;
vkcode   = GetVirtualKeyCodeFromVirtualScanCode(fullcode, keyboardType);
vkcode   = (flags & KBD_FLAGS_EXTENDED) ? vkcode | KBDEXT : vkcode;
keycode  = GetKeycodeFromVirtualKeyCode(vkcode, WINPR_KEYCODE_TYPE_EVDEV);
```

- **si tiene il conto dei tasti premuti** e si scartano pressione ripetuta e rilascio non appaiato: il
  compositore rifiuta entrambi. A fine connessione si rilascia tutto, **anche se non c'è più una
  sessione a cui parlare**. [M, 2 agosto]
- **il tasto Pausa** arriva come sequenza `Ctrl↓(E1) → NumLock↓ → Ctrl↑(E1) → NumLock↑`: serve una
  macchina a quattro stati. Riconoscibile anche senza il flag E1. [R]
- **`FASTPATH_INPUT_EVENT_SYNC`** porta lo stato dei tasti a scatto: va usato per rilasciare tutto e
  riconciliare i lucchetti, non ignorato.

**Il KLID va usato, ma non su Android.**

| Client | KLID | Verificato |
|---|---|---|
| **mstsc** | `0x0409` (US) | ✅ **corrisponde** alla tastiera reale [M, 3 agosto] |
| **RDM** | `0x0409` (US) | ✗ non verificato, e **strutturalmente privo di senso** |

Su mstsc il KLID è informazione buona e va usata. Su Android no, e non per un difetto del client: una
tastiera software **non ha una disposizione fisica** da dichiarare — è un IME che produce testo. Quel
`0x0409` è verosimilmente un ripiego fisso.

Su Android arrivano prevalentemente **eventi Unicode**, non scancode: il percorso Unicode **è la strada
principale, non un ripiego**.

> **Il trasporto degli eventi è libei**, deciso il 4 agosto 2026 chiudendo la fase 3 (§5.8 di
> `SPECIFICA.md`). Cambia poco di questa sezione — le conversioni restano identiche — e cambia molto
> sulla disposizione: con `ei_device_keyboard_get_keymap` la keymap **si legge dalla sessione**
> invece di dedurla dal KLID, e per gli eventi Unicode si cerca quale tasto fisico produce quel
> simbolo nella disposizione corrente. Il come sta in §13.1 di `gnome-remote-desktop.md`.

### 6.3 Quel che si è misurato scrivendo l'input — 4 agosto 2026

| Cosa | Esito |
|---|---|
| `GetKeycodeFromVirtualKeyCode(vk, WINPR_KEYCODE_TYPE_EVDEV)` | restituisce il codice **evdev vero**, pronto per `ei_device_keyboard_key` **senza il −8**. Quel −8 serve solo al percorso xkb (`xkb_keycode − 8 = evdev`) [M] |
| La keymap della sessione | arriva da libei, si compila, e se ne legge il nome: `English (US)`. **La questione aperta n.7 si chiude qui** [M] |
| La regione del puntatore | Mutter espone una `ei_region` che porta il **`mapping-id` dichiarato a `RecordVirtual`**: è così che il puntatore si mette d'accordo con l'immagine. Col monitor virtuale della misura chiesta la trasformazione è l'identità [M] |
| Uno scatto di rotella | `dy = −10` verso l'alto, `+10` verso il basso — cioè `/120 → ×10`, verticale invertito [M] |
| La prima lettera | **non si perde più**, e non serve il colpo a vuoto di §5.8 di `SPECIFICA.md`: con libei i dispositivi vengono **annunciati e ripresi** (`DEVICE_ADDED` → `DEVICE_RESUMED` → `ei_device_start_emulating`) prima che si possa spedire qualcosa, quindi il difetto non può esistere [M] |

**Provato sui tre client il 4 agosto**: `xfreerdp3`, mstsc e RDM comandano il desktop — tastiera,
puntatore e rotella. [M]

Che RDM comandi vale doppio, ed è il motivo per cui va provato lì: su Android non c'è una tastiera
fisica da cui mandare scancode, quindi ciò che arriva sono **caratteri**, e l'unica strada è
tradurli nel tasto che li produce nella disposizione della sessione. **Il percorso Unicode è quindi
misurato, non solo scritto** — e con esso la keymap letta da libei, che è ciò che rende possibile
quella traduzione.

> **La regione si cerca per `mapping-id`, non per indice.** Prendere «la prima regione» funziona
> finché lo schermo è uno solo, e smette di funzionare esattamente quando serve. Il ripiego alla
> prima resta, ma va **dichiarato nel registro** quando scatta.

### 6.2 Mouse

```c
value = flags & WheelRotationMask;                       /* 0x01FF */
if (value & PTR_FLAGS_WHEEL_NEGATIVE)                    /* complemento a due */
    value = (~value & WheelRotationMask) + 1;
step = -value / 120.0;                                   /* RDP: 120 per scatto */
if (flags & PTR_FLAGS_WHEEL_NEGATIVE) step = -step;
/* verticale: invertito rispetto a Wayland.  orizzontale: concorde. */
```

**Le coordinate degli eventi di rotella sono riempite di zeri** da molti client: vanno scartate quando
`PTR_FLAGS_WHEEL` o `PTR_FLAGS_HWHEEL` sono accesi, altrimenti il puntatore salta nell'angolo a ogni
scatto. [M, 2 agosto]

Su Android il tocco arriva come **eventi mouse normali**: MS-RDPEI non viene aperto (§1.3).

---

## 7. Geometria e ridimensionamento

### 7.1 Validazione della configurazione monitor

| Vincolo | Valore | Fonte |
|---|---|---|
| Larghezza, altezza | **200 … 8192** | [S] MS-RDPEDISP |
| Dimensione fisica (mm) | 10 … 10000, altrimenti azzerare | [R] |
| Fattore di scala | 100 … 500, altrimenti azzerare | [R] |
| Monitor primario | **a (0,0)**; se nessuno lo dichiara, eleggerne uno | [R] |
| Sovrapposizioni | **vietate** | [R] |
| `DeviceScaleFactor` | **ignorare** — deprecato, solo Win 8.1 | [R] |

**La dimensione fisica va sanificata sul DPI risultante, non sui millimetri.** [M, 3 agosto]

| | dichiarata | DPI | giudizio |
|---|---|---|---|
| mstsc | 2560×1080 px su 790×334 mm, scala **125** | **82** | plausibile, **usabile** [M, 5 agosto] |
| RDM, alla connessione | 2560×984 px, dimensione fisica **assente** | — | niente da giudicare [M, 5 agosto] |
| RDM, sul canale DISP | 1384×662 px su **1384×662 mm** | **25** | assurda, **scartata** [M, 5 agosto] |
| xfreerdp3 | derivata da un 75 DPI fisso (`targetWidth / 75 × 25.4`) | 75 | plausibile — e per questo **non esercita il filtro** [M, 5 agosto] |

> ⚠ **RDM dichiara i millimetri UGUALI AI PIXEL**, e la misura del 3 agosto («984 px su 1000 mm»)
> era una lettura approssimata dello stesso fatto. Sul filo manda `PhysicalWidth == Width`, cioè uno
> schermo largo un metro e mezzo: 25 DPI. Passa indenne il filtro 10–10000 mm del riferimento, e la
> soglia sul DPI lo prende. Il registro, al primo `MONITOR_LAYOUT` di RDM:
>
> ```
> dimensione fisica scartata: 1384x662 px su 1384x662 mm fanno 25 x 25 DPI, fuori da 30..600
> ```
>
> Da notare per chi scriverà le prove: **xfreerdp3 non può esercitare questo filtro**, perché deriva
> i millimetri da un 75 DPI fisso e quindi dichiara sempre un valore plausibile. Il filtro lo prova
> RDM, e nessun altro.

Larghezza e altezza **pari**: non è nella specifica, ma un lato dispari rompe qualunque codificatore
4:2:0.

### 7.2 La macchina di ridimensionamento

```
ATTESA_CONFIG ──(nuova configurazione)──► inibisci il rendering
                                            │ (nessun fotogramma a metà strada)
                                     PREPARA_SUPERFICI
                                            │ crea/aggiorna gli stream
                                     ATTENDI_STREAM → ATTENDI_MISURE
                                            │
                                     RIPRENDI  ──► disinibisci ──► ATTESA_CONFIG
```

Regole, tutte dal riferimento:

- **l'input si scarta** in ogni stato diverso da `ATTESA_CONFIG`: la geometria non è stabile. Nel
  riferimento la guardia sta dentro `grd_rdp_layout_manager_transform_position`, quindi riguarda **il
  puntatore**, non la tastiera: una coordinata assoluta si riscala su una regione che sta cambiando
  misura, un tasto no. [R]
- una configurazione che arriva mentre se ne applica un'altra **sostituisce** quella in coda, non si
  accoda — i client mandano raffiche trascinando il bordo;
- l'inibizione **non è un flag ma un conteggio di risorse in uso**;
- il ridimensionamento **non deve rifare la cattura**: si aggiornano i parametri del flusso PipeWire.
  [R: `pw_stream_update_params`, ed è la correzione che toglie il prezzo pagato in §5.8 di
  `SPECIFICA.md`] ✅ **fatto il 5 agosto 2026, e misurato**: `misura del monitor virtuale cambiata …
  senza rifare la cattura`, con un solo montaggio del monitor virtuale in tutta la sessione.
- **la coda ha un tempo, non solo un posto**: si applica quando le richieste smettono di arrivare, e
  il conto riparte a ridimensionamento concluso. Senza, si ricade nell'eco di **R10-bis**.

> ⚠ **`MaxNumMonitors` si dichiara pari al vero.** REMOTIX serve **un monitor solo** (§3.1 di
> `SPECIFICA.md`), e lo dice: `MaxNumMonitors = 1`, `MaxMonitorAreaFactorA = B = 8192` come il
> riferimento. Non è una rinuncia nascosta — è il modo che il protocollo offre per dirlo, e un
> client corretto non chiederà mai il secondo. Se lo chiedesse, FreeRDP scarta il PDU **e chiude il
> proprio thread di lettura del canale**: da lì in poi quella sessione resterebbe senza
> ridimensionamenti. Motivo in più per dichiarare il vero. [R]

> Su Android un ridimensionamento è anche **un riavvio del decodificatore**. Un motivo in più per
> accorpare le raffiche.

> ⛔ **La fase 6 non si prova su mstsc, e non è una svista.** mstsc apre il canale
> `DisplayControl` (§1.2 lo ha misurato fra i suoi canali dinamici) ma **non manda
> `MONITOR_LAYOUT` trascinando il bordo** (§5.7 di `SPECIFICA.md`). Trascinare lì non prova nulla:
> se l'immagine segue è il client che scala. Il ridimensionamento si esercita su
> `xfreerdp3 /dynamic-resolution` e su RDM; su mstsc si verifica la **non regressione** — il canale
> si apre, le capacità partono, e non compare nessuna seconda `nuova sorgente`. È il client severo:
> una superficie cancellata a sproposito si vede lì.

### 7.3 La cattura del desktop: Mutter e PipeWire

*Scritta chiudendo la fase 3, il 4 agosto 2026. Tutto misurato su Debian Trixie, GNOME 48.7,
PipeWire 1.4.2, dentro la VM di runtime.*

**La sequenza non ammette permute**, e ogni permuta la punisce con un errore diverso. [M] [R]

```
1. RemoteDesktop.CreateSession        → percorso, e se ne legge SessionId  — NON avviarla
2. ScreenCast.CreateSession           con `remote-desktop-session-id` e `disable-animations`
3. RemoteDesktop.Session.Start        ← adesso, non prima
4. ScreenCast.Session.RecordVirtual   con `cursor-mode` e `is-platform`  → percorso del flusso
5. sottoscrizione a PipeWireStreamAdded    ← PRIMA del passo 6
6. Stream.Start                       ← il FLUSSO, non la sessione di cattura
```

| Se si sbaglia | Mutter risponde |
|---|---|
| controllo avviato prima del passo 2 | `Remote desktop session already started` |
| cattura avviata con `Session.Start` | `Must be started from remote desktop session` |
| cattura fermata con `Session.Stop` | `Must be stopped from remote desktop session` — si ferma il **controllo**, la cattura lo segue |
| ci si sottoscrive dopo il passo 6 | nessun errore: si aspetta per sempre un annuncio già passato |

**Il formato PipeWire**, riga per riga:

| Campo | Valore | Perché |
|---|---|---|
| `VIDEO_format` | `BGRx`, `BGRA` e **nient'altro** | nessun punto della catena guarda il formato negoziato: elencare una variante RGB scambierebbe rosso e blu **senza alcun errore** |
| `VIDEO_size` | **rettangolo singolo** della misura voluta | funziona, ed è la forma del riferimento [M, 4 agosto] |
| `VIDEO_framerate` | `0/1` | «mandami un fotogramma quando cambia qualcosa, non a ritmo fisso» |
| `VIDEO_maxFramerate` | intervallo `[1/1 … fps/1]` | il tetto |
| `modifier` | **presente**, salvo chi vuole i pixel in CPU | dichiararlo avvia la negoziazione DMA-BUF; tacendo si resta in memoria ordinaria. Quale delle due si dichiari **si decide a cattura viva**, e lo decide il codificatore: **R30** |

> ⛔ **Il DMA-BUF si chiede in DUE posti, e chi ne dichiara uno solo non lo ottiene.** [M, 6 agosto
> 2026]
>
> | Dove | Che cosa |
> |---|---|
> | nel **formato** | `SPA_FORMAT_VIDEO_modifier`, con `MANDATORY \| DONT_FIXATE` — altrimenti il valore lo fissa PipeWire invece di lasciarlo concordare con chi alloca |
> | in **`SPA_PARAM_Buffers`** | `SPA_PARAM_BUFFERS_dataType` con il bit di `SPA_DATA_DmaBuf` acceso |
>
> Dichiarando solo il primo la negoziazione **riesce lo stesso** e i buffer continuano ad arrivare in
> memoria ordinaria: nessun errore, nessuna riga di registro, e la cattura a copia zero semplicemente
> non c'è. Si risponde con i `Buffers` dentro `param_changed`, quando il formato è stato concordato.
>
> **E la proposta senza modificatori si lascia in elenco**, dopo quella con: se l'aggancio DMA-BUF
> non riesce si ricade sulla memoria invece di restare senza immagine. È la prudenza del riferimento
> (§11.2 di `gnome-remote-desktop.md`).
>
> ⛔ **Ma non si chiede finché non c'è chi lo sa leggere.** Un consumatore che si aspetta un
> puntatore scarta ogni buffer DMA-BUF **in silenzio**: schermo fermo, zero righe di registro. Il
> 6 agosto è successo.
>
> Da quel giorno la regola non è più «non chiederlo finché non sei pronto» ma «chiedilo solo
> mentre c'è chi lo consuma», ed è **R30**: chi consuma cambia durante la sessione, perché lo
> decide il codificatore della connessione collegata in quel momento.

> ⛔ **E il compositore deve disegnare sulla scheda GIUSTA, o il DMA-BUF non serve a niente.**
> [M, 6 agosto 2026]
>
> Mutter disegna sulla prima scheda DRM che trova. Nella VM erano tre — `bochs` (la VGA d'emergenza
> di QEMU), `virtio-gpu` e la Intel passata — e la prima è quella d'emergenza, che un nodo di
> rendering non ce l'ha: da lì la composizione in software, e soprattutto **buffer che appartengono a
> un'altra scheda**, non importabili dal codificatore.
>
> La cura è lasciare all'ospite **una sola scheda DRM**: `virtio-gpu` non si dichiara a QEMU, e
> `bochs` si spegne dal lato del kernel con `modprobe.blacklist=bochs`. La VGA d'emergenza va invece
> **lasciata a QEMU**: togliendola (`-vga none`) GRUB annuncia l'avvio e la macchina non risponde
> più, senza una riga sulla seriale.

- **Lo stride si legge dal chunk del buffer**, mai calcolato come `larghezza × 4`. Il produttore
  allinea le righe come gli conviene, e dedurlo produce immagini oblique. [M] [R]
- **La misura non si passa a `RecordVirtual`**: il monitor si chiede, non si impone, e la
  risoluzione si concorda nella negoziazione PipeWire. È la base della fase 6.
- **La sessione vive quanto la connessione D-Bus** di chi l'ha creata. Usando quella condivisa —
  che vive quanto il processo — le sessioni vanno chiuse **esplicitamente**, o ogni rimontaggio
  lascia a Mutter un monitor virtuale in più. [M]
- **Un intervallo aperto sulla misura la fa scegliere a Mutter**, che sceglie 1280×720. [M, 2 agosto]

> ⚠ **`SPA_POD_Rectangle` singolo contro intervallo chiuso: chiusa il 4 agosto.** Entrambi
> funzionano e negoziano la misura chiesta; si usa il singolo, come il riferimento. Il
> `no more input formats` misurato il 2 agosto era un fatto della catena di allora — §5.6 di
> `SPECIFICA.md` è stato corretto. [M]

**Il palco appartiene alla sessione grafica, non alla connessione.** Smontarlo alla disconnessione
lascia Mutter con **zero schermi**, e da lì `libmutter` va in asserzione fallita
(`meta_workspace_get_work_area_for_monitor: logical_monitor != NULL`), le applicazioni aperte
perdono la connessione Wayland con «Error 71 (Protocol error)» e quelle nuove non hanno dove
aprirsi. Chi si ricollega alla stessa misura ritrova il desktop com'era. [M, 3 agosto]

### 7.4 Sopravvivere al logout: il bus di sessione

*Scritta chiudendo la fase 5, il 4 agosto 2026.*

Al logout il gestore utente ferma `dbus.service` e subito dopo
`gnome-session-restart-dbus.service` ne avvia **un altro**, sullo stesso socket. Da questo fatto
discendono due regole, e ciascuna è costata un difetto.

> ⛔ **Non si chiama mai `g_bus_get_sync(G_BUS_TYPE_SESSION, …)`.**
>
> Sulla connessione **condivisa** al bus di sessione, GIO tiene acceso `exit-on-close`: quando il
> bus si chiude, la libreria chiama **`raise(SIGTERM)`** per conto nostro. REMOTIX moriva lì a ogni
> logout — e il registro di sistema diceva `remotix.service: Deactivated successfully.` **senza**
> alcuno `Stopping…` prima, cioè systemd dichiarava di non essere stato lui. [M, 4 agosto]
>
> **Come si è visto**: installando un gestore di `SIGTERM` con `SA_SIGINFO`, che registra `si_pid`,
> `si_uid`, `si_code` e la pila di chiamate. Il registro ha detto
> `SIGTERM mandato da pid 30202 (remotix) — si_code -6: raise()/pthread_kill() da dentro`, con la
> pila che passa per `libgio` → `g_signal_emit` → `gsignal`. Fino a quel momento il mittente era
> stato **dedotto** per tre volte, sempre sbagliando.
>
> **Corollario di metodo**: quando un processo muore e nessuno ammette di averlo ucciso, non si
> deduce il mittente — lo si **chiede al nucleo**. Venti righe, una sola esecuzione.
>
> Si apre invece una connessione propria, e si spegne l'interruttore comunque:
> ```c
> indirizzo = g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, …);
> bus = g_dbus_connection_new_for_address_sync(indirizzo,
>           G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
>           G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION, NULL, NULL, …);
> g_dbus_connection_set_exit_on_close(bus, FALSE);
> ```
> Per il bus di **sistema** il difetto non esiste: quello si prende come sempre.

> ⛔ **Una connessione al bus di sessione non sopravvive al logout: va buttata e riaperta.**
>
> L'oggetto vecchio resta lì, chiuso. Usarlo non dà errore: dà **silenzio** — nessuna sessione
> trovata, nessun Mutter, **schermo nero al secondo accesso**, che è il sintomo con cui si è
> presentato. Ogni presa del bus controlla `g_dbus_connection_is_closed()` e, se chiuso, ne apre
> uno nuovo; lo stesso vale per chi tiene una registrazione presso `gnome-session`. [M, 4 agosto]

**La regola generale, letta in `gnome-remote-desktop` e in `xrdp`**: il processo che sopravvive al
logout non può riusare **niente** della sessione morta. Loro la rispettano per costruzione — il
demone persistente sta sul bus di sistema e la sessione nuova la chiede a GDM o la forca via PAM.
REMOTIX tiene lo stesso processo su entrambi i lati, quindi la deve applicare a mano, in un punto
solo. [R]

### 7.5 Il suono della sessione: il sink non esiste, va creato

*Misurato il 5 agosto 2026, aprendo la fase 8, dentro la VM di runtime — Debian Trixie, GNOME 48.7,
PipeWire 1.4.2, WirePlumber attivo.*

> ⛔ **Nella sessione senza monitor non c'è alcun dispositivo audio: zero device, zero sink, zero
> source.** Chi si limita a catturare quel che esiste cattura **il nulla**, e senza un errore da
> nessuna parte. [M]

`wpctl status` nella sessione remota, con `pipewire`, `pipewire-pulse` e `wireplumber` tutti
`active`:

```
Audio
 ├─ Devices:        (vuoto)
 ├─ Sinks:          (vuoto)
 ├─ Sources:        (vuoto)
 └─ Streams:        (vuoto)
```

La causa è la macchina, non la sessione: la VM non ha alcun dispositivo sonoro (`vm.sh` non passa
nessun `-audiodev` a QEMU), e **una macchina da server è il caso normale**, non l'eccezione (§6.2 di
`SPECIFICA.md`). Anche dove una scheda ci fosse, mandare l'audio di una sessione remota agli
altoparlanti di una macchina che nessuno sta guardando sarebbe la cosa sbagliata.

> **Il riferimento qui non aiuta, e va detto.** `gnome-remote-desktop` si mette in ascolto del
> registro PipeWire e apre una cattura sul **monitor di ogni nodo con `media.class = Audio/Sink`**
> (`grd-rdp-audio-playback.c`, `registry_event_global`). Un sink non lo crea mai: presuppone che la
> macchina ne abbia uno. Sulla VM di runtime, con quel codice, non arriverebbe un campione. [R, 5
> agosto]

**Quel che funziona, misurato:** REMOTIX crea il proprio sink, e ne cattura il monitor.

| Passo | Come |
|---|---|
| 1. il sink | nodo `adapter` con `factory.name = support.null-audio-sink`, `media.class = Audio/Sink`, `audio.position = [FL,FR]` |
| 2. diventa il predefinito | da solo: è l'unico sink della sessione — `wpctl` lo marca `*` |
| 3. la cattura | flusso PipeWire in ingresso agganciato a **quel nodo**: si legge il suo monitor, cioè il mixaggio di tutte le applicazioni |

La prova: un'applicazione (`pw-play`) ha suonato un tono a 12000 di ampiezza sul sink virtuale, e la
cattura del monitor ha restituito **136 388 fotogrammi a 44 100 Hz, 2 canali, picco 12000** — cioè
esattamente ciò che era stato suonato, senza perdite né riscalature. [M, 5 agosto]

**Il sink appartiene alla sessione, la cattura alla connessione**, ed è la stessa divisione del
palco (§7.3): un sink che nascesse e morisse con il client farebbe cambiare dispositivo alle
applicazioni a ogni riconnessione — che, per chi sta ascoltando qualcosa, significa audio che si
interrompe e non riparte.

> ⛔ **Il monitor di un sink virtuale non tace mai.** Il nodo ha un proprio orologio e produce
> campioni anche quando nessuna applicazione sta suonando. Un server che spedisce quel che riceve
> manda quindi **1,4 Mbit/s di zeri per tutta la sessione** — il 14 % del budget di §3.1 di
> `SPECIFICA.md`, speso in silenzio. Misurato al primo giro del banco: 220 000 fotogrammi ogni
> cinque secondi con il desktop muto. [M, 5 agosto 2026]
>
> **Il silenzio non si spedisce**, e il primo blocco muto sì: è la coda del suono appena finito, e
> tagliarla si sentirebbe. Dopo la correzione, dieci secondi di desktop muto costano **678
> fotogrammi** invece di 440 000.

> ### ⭐ Il livello lo porta il server, e per questo il sink parte sempre al massimo
>
> *[decisione dell'utente, 8 agosto 2026: «per mstsc, linux e Android il livello del volume è quello
> del server, il client si adegua»]*
>
> Due modi di far arrivare un livello al client, e uno solo regge dappertutto:
>
> | | dipende da | esito |
> |---|---|---|
> | **il volume dentro i campioni** ✅ | **niente**: il client riceve audio già più basso | vale su mstsc, xfreerdp e RDM, e su **ogni** desktop, perché il sink lo creiamo noi e `suono.c` non nomina alcun compositore |
> | `SNDC_SETVOLUME` | dal fatto che il client onori il PDU | ⛔ scartato: si rompe in silenzio su uno dei tre, e il verso opposto (client → server) **in RDP non esiste** |
>
> Perché quel livello arrivi davvero servono **due** proprietà sul sink, e la prima mancava dal
> giorno in cui l'audio esiste:
>
> - **`monitor.channel-volumes=true`** — in PipeWire il volume si applica **a valle** della presa del
>   monitor, e senza questa il cursore non governa niente, **mute compreso** (`kde.md` §10.5);
> - **`state.restore-props=false`** — ⚠ suggerimento, non garanzia: se la versione di WirePlumber non
>   la conosce non fa nulla e non protesta.
>
> ✅ **MISURATO SU TUTTI E DUE I COMPOSITORI**, `prove/fase11-volume.sh` — e i numeri sono gli
> stessi, che è quel che ci si aspetta da una correzione che sta nel percorso condiviso:
>
> | | KWin | Mutter |
> |---|---|---|
> | cursore al 100 % | 25,89 % | 25,89 % — **25,83 % a macchina appena riavviata** |
> | al 25 % | 0,40 % | 0,40 % |
> | a 0 % | 0,00 % | 0,00 % |
>
> ⚠ La misura su Mutter è stata **rifatta dopo un riavvio del server**, su una macchina che non aveva
> mai visto KWin: è stato l'utente a chiederlo, e aveva ragione — la prima l'avevo presa su un
> sistema che aveva macinato KDE per un giorno. Stessi numeri, e adesso valgono.
>
> (tono in ingresso 25,9 %; il 25 % del cursore non è il 25 % dell'ampiezza perché PulseAudio usa una
> curva cubica — 0,25³ = 1,56 % — ed è giusto così, l'orecchio è logaritmico.)
>
> ### ⛔ APERTO — «una via nuova parte al massimo» NON funziona, e il rimedio non è quello che sembra
>
> *[M, 8 agosto 2026, e il difetto l'ha trovato il banco solo dopo che il controllo è stato
> **rinforzato**: zittendo a client collegato, il valore era già tornato al massimo alla lettura e il
> verde non provava niente (`LEZIONI.md` §1.3).]*
>
> Il sink vive quanto il **palco**, non quanto la connessione: chi zittisce, si scollega e si
> ricollega **ritrova il silenzio**. Il rimedio scritto — rialzare il volume alla creazione,
> all'avvio della cattura e a ogni `palco_assicura` — **non ha effetto**:
>
> ```
> zittito a client staccato   volumi [0.0, 0.0]  mute True
> ricollegato                 volumi [0.0, 0.0]  mute True    ⛔ su KWin E su Mutter
> ```
>
> Quel che si sa, e va usato da chi riprende:
>
> - `pw_node_set_param(..., SPA_PARAM_Props, ...)` **ritorna un numero di sequenza asincrono**
>   (`0x4000….`), cioè la richiesta è accettata e spedita — non è un errore che stiamo ignorando;
> - campionando il nodo ogni mezzo secondo per tutta la riconnessione, il valore **non si muove mai**:
>   quindi **non è una corsa** con chi ripristina, è una chiamata inerte;
> - ⭐ **`pw-cli set-param <id> Props '{ mute: false, channelVolumes: [1.0, 1.0] }'` sullo stesso
>   nodo funziona**. Cioè il meccanismo è quello giusto e il difetto è nel nostro modo di chiamarlo:
>   il sospetto è il **proxy**, che noi prendiamo da `pw_core_create_object` invece che legandolo dal
>   registro come fa `pw-cli`;
> - non è WirePlumber: il nodo porta `state.restore-props=false`, che `scripts/node/state-stream.lua`
>   confronta come stringa (`~= "false"`), e il campionamento lo esclude comunque.
>
> ⚠ Da cui **la regola promessa all'utente non è ancora mantenuta**: oggi vale «il cursore governa»,
> non «ci si collega e il volume è al massimo».

> ⛔ **Il formato negoziato con PipeWire va GUARDATO, non dato per fatto.** È la stessa trappola di
> §7.3 sul video, e sull'audio morde più forte: leggere campioni a virgola mobile come interi a 16
> bit non dà alcun errore — dà un'onda quadra a fondo scala che segue la frequenza giusta, cioè
> qualcosa che al banco sembra «audio che arriva» e all'orecchio è un ronzio. Si legge
> `spa_format_audio_raw_parse` nel `param_changed` e, se non è `S16` con i canali chiesti, si spegne
> la cattura invece di spedire rumore.

> ⛔ **E una volta catturati bene, i campioni non si consegnano a `SendSamples`**: quella funzione li
> fa passare dal DSP di FreeRDP, che sul PCM a 16 bit ne **ribalta il segno** — stesso sintomo,
> origine opposta. Si spedisce con `SendSamples2`. **R24**.

### 7.6 Gli appunti della sessione: due asimmetrie che non danno errore

*Misurate il 5 agosto 2026, scrivendo la fase 8. GNOME 48.7, `xfreerdp3` 3.15.*

Mutter espone la clipboard sulla **stessa sessione `RemoteDesktop`** del palco: `EnableClipboard`,
`SetSelection`, `SelectionRead`, `SelectionWrite`, `SelectionWriteDone`, più i segnali
`SelectionOwnerChanged` e `SelectionTransfer`. Chi non ha una sessione di controllo non ha appunti.

> ⛔ **Nel SEGNALE i tipi mime stanno dentro una tupla; nei metodi no.** [M]
>
> `SetSelection` vuole `mime-types` come `as`. `SelectionOwnerChanged` lo consegna come **`(as)`**.
> Chi legge `as` non trova nulla e **torna in silenzio**: gli appunti funzionano in un verso solo —
> dal client alla sessione sì, dalla sessione al client no — e nel registro non compare niente che
> lo spieghi. Si accettano entrambe le forme. Lo aggira anche il riferimento (`grd-session.c`, che
> cerca `(as)` e ne prende il figlio 0), il che dice che non è una nostra fantasia.

> ⛔ **`SelectionOwnerChanged` arriva anche di ritorno da una nostra `SetSelection`**, con
> `session-is-owner` a vero. Trattarlo come una copia nuova significa annunciare al client quel che
> il client ci ha appena annunciato, e da lì i due lati si rincorrono. È la stessa forma dell'eco del
> ridimensionamento (R10-bis), in un protocollo diverso.

> ⛔ **`DisableClipboard` non si chiama MAI: in Mutter 48.7 è a senso unico.** [M, 5 agosto 2026]
>
> `handle_disable_clipboard` (`meta-remote-desktop-session.c:1465`) stacca il proprio gestore di
> `owner-changed` e azzera la sorgente, ma **non rimette a falso `is_clipboard_enabled`**. Da lì in
> poi la clipboard è morta a metà: i segnali non arrivano più, e un `EnableClipboard` per riaverli
> viene rifiutato con **«Already enabled»**.
>
> Chi la spegne alla disconnessione — la cosa naturale da fare, e quella che il riferimento può
> permettersi perché lì una sessione *è* una connessione — si ritrova alla connessione successiva
> appunti che non funzionano più per il resto della sessione grafica. **Si accende una volta sola,
> quando nasce il palco, e si lascia accesa**: chiudendo la sessione di controllo se ne va tutto
> insieme.

> ⛔ **Chi si ricollega non riceve alcun segnale, e va servito lo stesso.**
>
> `SelectionOwnerChanged` arriva solo quando il proprietario **cambia**; a una riconnessione non
> cambia niente. L'ultimo elenco di tipi va quindi **ricordato dal lato sessione** — vive quanto il
> palco, non quanto la connessione — e riannunciato al client nuovo.
>
> E va riannunciato **quando il client dichiara le proprie capacità**, non prima: un `FORMAT_LIST`
> spedito mentre il canale sta ancora facendo lo scambio iniziale il client lo lascia cadere, e chi
> torna trova gli appunti vuoti senza che nulla si lamenti. [M]

**Le immagini passano tutte da `CF_DIB`, e i nomi registrati non servono a niente.** [M]

Annunciando al client di FreeRDP il formato registrato «PNG», la sua selezione X resta **senza alcun
formato**: `xf_cliprdr.c` mappa `image/png`, `image/jpeg`, `image/tiff` e i BMP tutti su
`formatToRequest = CF_DIB`, e converte in casa propria. Windows fa lo stesso — ciò che si incolla in
Paint e in Word è il DIB.

| | |
|---|---|
| Cosa copiano le applicazioni di GNOME | quasi sempre **`image/png`** |
| Cosa chiede il filo | **`CF_DIB`**, e nient'altro |
| Chi converte | **il server**: senza conversione, «copia immagine» funziona solo fra programmi che già parlano BMP |

E `CF_DIB` **è un BMP senza i suoi primi 14 byte**. Per rimetterli bisogna calcolare dove cominciano
i pixel: dimensione dell'intestazione DIB, più la tavolozza se ci sono ≤ 8 bit per pixel, più 12 byte
di maschere se la compressione è `BI_BITFIELDS`. Sbagliare quel numero dà **un'immagine spostata, non
un errore**. E le righe del BMP si scrivono **dal basso verso l'alto**: chi lo dimentica consegna
immagini capovolte, sempre senza errori — per questo il banco della fase 8 controlla il pixel *in
basso a sinistra* e non uno qualsiasi.

---

## 8. Diagnostica: dal sintomo alla causa

### 8.1 Schermo nero

| # | Causa | Come si verifica |
|---|---|---|
| 1 | **Manca `MapSurfaceToOutput`** (R1) | tracciare i PDU EGFX inviati |
| 2 | **Codec che il client non rende** (R3, §1.7) | leggere i flag AVC del client e il codec inviato |
| 3 | **L'interruttore grafico è spento nel client** | su aFreeRDP `gfx` e `gfx H264` sono spenti per default |
| 4 | **Versione EGFX ripiegata su 8.1/8.0** senza AVC (R2) | leggere la versione confermata |
| 5 | Fotogramma non compresso | mstsc **non rende** `RDPGFX_CODECID_UNCOMPRESSED` |
| 6 | **Fotogramma perso prima della negoziazione** (R9) | il nero si corregge da sé muovendo qualcosa |
| 7 | Riattivazione che ha spento EGFX (R7) | una seconda `nuova sorgente` a pochi istanti dalla prima |
| 8 | **Secondo accesso dopo un logout**: connessione al bus di sessione morta (§7.4) | il registro dice `nessuna sessione grafica: la avvio` e poi **non** dice `palco montato` |

> **Il segnale che divide 1–5 da 6–7**: se il client **riscontra i fotogrammi** (`FRAMEACKNOWLEDGE` con
> pochi ms di latenza) allora li riceve ed elabora, e il problema è **cosa gli abbiamo detto di
> farne** — non il contenuto del flusso. È il dato che ha risolto §5.4, e quello che ha inchiodato RDM
> il 3 agosto.

### 8.2 Rinegoziazione e disconnessione improvvisa

Allineamento (R4) o convenzione dei bordi (R5). Si vede quasi solo su mstsc.

### 8.3 Immagine spostata o fuori posto

`ResetGraphics` con elenco monitor vuoto (R6), oppure origine di `MapSurfaceToOutput` sbagliata.

### 8.4 Immagine parziale che resta

Fotogramma mandato prima del ridisegno (R10) insieme a R9. Firma: **alla prima connessione si vede
sbagliata, alla seconda giusta**.

### 8.5 Il client resta attaccato dopo la fine della sessione

Manca `SET_ERROR_INFO` (R12). Si vede su Android, non su `xfreerdp3` che esce da solo.

### 8.6 Il server sembra spento

Nell'ordine in cui conviene guardare:

1. **Il server c'è davvero?** `systemctl is-active remotix.service` dentro la VM, e `ss -ltn | grep
   3389`. Se il registro finisce con `arrivato SIGTERM: chiudo`, la spia del `SIGTERM` (§7.4) dice
   già **chi** è stato — non lo si deduce, lo si legge.
   [M, 5 agosto: era stata una prova a lasciarlo giù, vedi sotto]

   > ⚠ **La porta non è per forza la 3389**: `server.sh opzioni --porta N` la sposta, e il registro
   > la dichiara all'avvio (`in ascolto su *:N`). Un controllo inchiodato al 3389 dice «spento» su un
   > server sanissimo — è quel che faceva `server.sh stato`, corretto il **7 agosto 2026** perché
   > adesso la **legge da chi ascolta**. Non sopravvive a un riavvio: `/etc/default/remotix` vive in
   > RAM e `provision-server.sh` lo riscrive con le sole `--registro diagnostica`.
   >
   > ⛔ **E UN BANCO A CUI SI COLLEGA L'UTENTE STA SULLA PORTA DI SEMPRE, LA 3392.** [7 agosto 2026]
   >
   > Ogni porta nuova è una **regola in più nel firewall dell'utente**, e in un pomeriggio gliene ho
   > fatte aprire tre prima che me lo dicesse. I banchi che si collegano da soli — client nel
   > contenitore, per loopback — restano sulle proprie, perché quelle non le vede nessuno; ma quando
   > a guardare è lui, il banco prende il posto del servizio e glielo restituisce alla fine
   > (`banco-scala.sh`). Il servizio fermo per un minuto costa meno di una regola da scrivere.
   >
   > **Le porte dei banchi sono tre, e vanno lasciate libere**: **3389** (REMOTIX di runtime, in 17
   > punti), **3390** (`PORTA_CNT` di `fase6.sh` e `fase7.sh`: la scena sintetica nel contenitore) e
   > **3391** (`fase2.sh`). Un servizio parcheggiato su una di queste non dà un errore di porta: dà
   > un **banco che fallisce** — e su una di esse anche un `pkill -f "remotix --porta N"` di banco che
   > spara sul servizio. La porta di lavoro sul ferro è quindi la **3392** [utente + misura, 7 agosto
   > 2026].
2. **C'è già un client collegato?** Con la sessione unica la seconda connessione viene rifiutata.
   [M, 2 agosto: «spesso è un proprio client dimenticato aperto»]
3. **La porta arriva fin qui?** La VM è raggiungibile per inoltro di porta dall'host
   (`hostfwd=tcp::3389-:3389`): l'ascolto va verificato **sul server**, non dentro la VM.

   > **E si legge quale indirizzo, non solo quale porta.** REMOTIX apre **un solo socket, su `::`
   > con `IPV6_V6ONLY=0`**: `ss` lo scrive `*:N`, e quella stella *è* la doppia pila — l'IPv4 entra
   > come indirizzo mappato. Le tre rese di `ss` non vanno confuse, perché due sembrano uguali e non
   > lo sono:
   >
   > | `ss -ltn` | che cos'è |
   > |---|---|
   > | `*:N` | socket IPv6 a **doppia pila**: risponde anche in IPv4 — è il nostro |
   > | `[::]:N` | socket IPv6 **solo** IPv6 (`v6only=1`): in IPv4 non risponde |
   > | `0.0.0.0:N` | socket IPv4 puro |
   >
   > Misurato il **7 agosto 2026** tenendo aperta una connessione IPv4 da un'altra macchina: sul
   > server compare `[::ffff:192.168.0.2]:3392 ← [::ffff:192.168.0.3]`, cioè l'IPv4 mappato. La
   > controprova sta in `/proc`: la 3392 è in `/proc/net/tcp6` e **non** in `/proc/net/tcp`, con
   > `net.ipv6.bindv6only = 0`. Quindi «ascolta su 0.0.0.0» non si vedrà mai scritto, e non è un
   > difetto: è la stessa cosa detta in un modo solo.

> ⛔ **Una prova che spegne il server e non lo riaccende costa una diagnosi ogni volta.**
> La regola era già scritta — in fondo a `fase5.sh`, il 4 agosto — ma solo lì, e `fase3.sh` e
> `fase4.sh` continuavano a lasciare la macchina muta. Il 5 agosto la stessa diagnosi è stata pagata
> una seconda volta, con il sintomo perfetto: «da xfreerdp non entro», con il server inesistente.
> Ora tutte le prove riaccendono il servizio in chiusura.
>
> **La lezione, che vale oltre questo caso**: una regola scritta in un posto solo vale solo in quel
> posto. Quando se ne ricava una da un difetto, si cerca **chi altro** ha la stessa forma.

> ⛔ **E DAL FERRO LA STESSA REGOLA PESA DI PIÙ: un banco che finisce lascia il server con
> `--senza-autenticazione`.** [M, 6 agosto 2026]
>
> Nella VM era una macchina effimera dietro un inoltro di porta; sul server è **la 3389 aperta senza
> credenziali sulla rete di casa**. `ripristina` di `fase9.sh` rimette PAM, ma i banchi che finiscono
> con `avvia-remotix.sh --aperto` — `fase3`, `fase5`, `fase6`, `fase8-appunti` — no.
>
> **Chi chiude una sessione di lavoro controlla `/etc/default/remotix`**, e chi scrive un banco lo
> rimette com'era in chiusura. Non è igiene: è una porta.

### 8.6-ter La macchina di runtime è **il server**, dal 6 agosto 2026

*Deciso dall'utente. Il perché e il prezzo stanno in §6.2 di `SPECIFICA.md`; qui c'è quel che serve a
leggere le misure.*

| | |
|---|---|
| Macchina | il server `192.168.0.2` stesso, **senza hypervisor** |
| CPU e memoria | Intel Core i5-13500T, **20 thread**, 31 GB |
| Grafica | la **iGPU Intel diretta** (`card0`/`renderD128`, `i915`, iHD 25.2.3, `VAProfileH264High : EncSliceLP`) — più la Radeon RX 6800 (`card1`/`renderD129`) |
| Rete | quella del server: nessuno stack in spazio utente |
| Sistema | rootfs **live in RAM**: si azzera a ogni riavvio, e `provision-server.sh` va rieseguito |
| Sessione | GNOME installato sull'host, Shell con `--headless --no-x11` (§5.9-bis di `SPECIFICA.md`) |
| Guida | `server.sh`, gemello di `vm.sh`: `copia \| avvia \| ferma \| stato \| registro \| opzioni` |

**Cadono tutti e quattro i falsanti della tabella qui sotto.** Le misure delle fasi 2-9 restano valide
come **confronti** — stessa macchina, stesso minuto — e vanno **rifatte qui** prima di essere citate
come cifre del prodotto.

> ⛔ **E LA TRAPPOLA DEL TRASLOCO: `systemd --user` NON AGGIORNA I GRUPPI.** [M, 6 agosto 2026]
>
> Al primo giro sul ferro la cattura a copia zero **non si accendeva**: Mutter consegnava `MemFd`, e
> il sospetto naturale — due schede DRM invece di una, §7.3 — era **sbagliato**.
>
> La causa vera si legge in tre righe:
>
> ```
> gruppi di remotix:  27 44 991 992 1000     ← video (44) e render (991) ci sono
> gruppi della shell: 27 992 1000            ← mancano entrambi
> ```
>
> La Shell non la lancia REMOTIX: la lancia il **gestore systemd dell'utente**, che era già in piedi
> — il linger lo tiene acceso — e **i gruppi supplementari di un processo vivo non cambiano**. Quindi
> `usermod -aG render,video` non arriva a chi conta, la Shell non può aprire `/dev/dri`, e **Mutter
> ripiega sul rendering in software**: nessun errore da nessuna parte, e niente DMA-BUF da consegnare.
>
> Si accerta guardando quali nodi DRM la Shell ha aperto (`ls -l /proc/<pid>/fd | grep dri`): se non
> ne ha aperto nessuno, sta disegnando in software. Si cura riavviando `user@<uid>.service`, e
> `provision-server.sh` lo fa da sé dopo aver toccato i gruppi.
>
> Dopo la cura: la Shell apre `renderD128` e `renderD129`, la copia zero si accende, e il costo per
> fotogramma scende da **18 a 6 ms** sul desktop vero.

> ⛔ **E i banchi hanno bisogno di `sudo` senza password.** Eseguono i comandi con lo standard input
> da `/dev/null` — regola pagata in fase 4 — e `sudo` in quelle condizioni non può chiedere niente:
> non fallisce, **non torna**. Nella VM non si vedeva perché cloud-init dà `sudo` senza password.
> `provision-server.sh` installa una regola ristretta a `systemctl`, `loginctl`, `nft` e al solo
> `tee /etc/default/remotix` — `sudo tee` senza vincoli equivarrebbe a `sudo` intero. [M, 6 agosto]

### 8.6-bis Com'era fatta la VM di runtime, e che cosa falsava

*Letto sulla macchina il 5 agosto 2026, non dedotto dagli script. [M] Serve perché **ogni misura di
questo documento è stata presa lì dentro**, e tre di quelle caratteristiche cambiano il senso di
quel che si misura.*

| | |
|---|---|
| Host | server `192.168.0.2`, **Intel Core i5-13500T** (13ª gen.) |
| Virtualizzazione | QEMU diretto, `-machine q35,accel=kvm`, `-cpu host` — nessun libvirt |
| CPU e memoria | **4 vCPU**, **8 GB** |
| Disco | 40 GB qcow2 in **sovrapposizione** su un'immagine Debian 13 cloud, virtio, `cache=writeback` |
| Sistema | Debian 13 trixie, kernel 6.12, **GNOME Shell 48.7** |
| Grafica | `virtio-gpu-pci` **senza `-virgl`**, cioè senza alcun 3D — più una VGA bochs ereditata [M, 6 agosto: letto in `vm.sh`, `cmd_start`. Questa riga diceva «con `-virgl`» e si contraddiceva da sola due righe più sotto] |
| Grafica, **dalla fase 9** | in più, la **iGPU Intel dell'host passata con VFIO** (`vm.sh gpu prendi`): `i915` la prende dentro la VM e compaiono `card2` e `renderD129`. GNOME continua a comporre in software sulla virtio-gpu; la scheda vera serve **solo al codificatore**. Si restituisce con `vm.sh gpu restituisci`, e un riavvio del server la restituisce comunque [M, 6 agosto] |
| Rete | **modalità utente (SLIRP)** con inoltro di porte: `2222→22`, `3389→3389` |
| Audio | **nessun `-audiodev`**: la macchina non ha una scheda sonora (§7.5) |
| Console | `-display none`, seriale su file, monitor su socket, in demone |

**Le tre cose che falsano, e come:**

| Caratteristica | Che cosa falsa |
|---|---|
| **niente 3D** (`-virgl` assente) | GNOME Shell disegna in **software**, sulla stessa CPU su cui gira il nostro codificatore. Il margine del server è quindi molto più stretto di quello di una macchina vera: è il motivo per cui la priorità di tempo reale (R26) ha cambiato tanto |
| ~~**niente codificatore hardware**~~ | **superato il 6 agosto**: la iGPU è dentro la VM e AVC420 si codifica in GPU. Resta vero per **RemoteFX Progressive**, che è un codec a wavelet e in GPU non ci va: il percorso di Android costa CPU piena come prima, e la fase 9 non lo tocca |
| **rete SLIRP** | ogni byte RDP passa da uno stack TCP/IP **in spazio utente**, che aggiunge latenza e irregolarità sue. Qualunque conclusione su «è la rete» — la **n.12** — è confusa da questo, finché non si misura con un `tap` o su ferro |

### 8.7 Come si misura senza scrivere codice

Il banco usato il 3 agosto, ricostruibile in dieci minuti:

```
client → proxy TCP in spazio utente → server di prova
         (ogni byte su file;          (xrdp con LogLevel=TRACE, oppure
          X.224 e ClientHello          gnome-remote-desktop, che stampa
          in chiaro)                   versione EGFX e flag AVC)
```

Il proxy non richiede privilegi. `gnome-remote-desktop` è il migliore dei due bersagli perché elenca
i capability set **uno per uno** con i flag; xrdp dice solo quanti sono. Il proxy dà in chiaro la
negoziazione X.224 e l'impronta TLS — tutto il resto è dentro TLS.

---

## 9. Prima di dichiarare fatta una fase

1. **Linux, connessione semplice** — `xfreerdp3 /v:… /gfx:avc420`: il desktop compare **subito**.
2. **Linux, ridimensionamento a caldo** — con `/dynamic-resolution`: l'immagine segue senza sporcarsi.
   Nel registro dev'esserci `ridimensiono la tela grafica`, **mai** una seconda `nuova sorgente`.
3. **Windows e Android** — il desktop compare **all'istante**, non «si forma» progressivamente.
4. **Niente resta premuto** — si tiene giù un modificatore, si uccide il client di netto, e nel
   registro dev'esserci il rilascio di quel che era rimasto premuto.
5. **Nessun thread di cattura residuo** a connessioni chiuse.
6. **Il congedo arriva** — a `Esci`, il client Android deve cadere entro due secondi **con un errore
   dichiarato**, non restare a fissare l'ultimo fotogramma.

> Firma di una sessione sana nel registro: **una sola** `nuova sorgente`, seguita da `EGFX negoziato`,
> e i ridimensionamenti che passano per `ridimensiono la tela grafica`.

7. **Il ridimensionamento si ferma quando l'utente si ferma.** Si trascina il bordo avanti e
   indietro per qualche secondo, poi si lasciano le mani ferme: nei dieci secondi successivi il
   registro **non** deve mostrare altri `ridimensiono la tela grafica`. Se continuano, server e
   client si stanno rincorrendo — è R10-bis, e su Android ogni giro è un riavvio del decodificatore.

8. **Si minimizza la finestra su mstsc, e la connessione regge.** Minimizzata, nel registro deve
   comparire `smetto di codificare` e il contatore dei fotogrammi deve **fermarsi**; riaprendola,
   `riprendo` e l'immagine torna subito aggiornata. Senza, mstsc tronca la connessione dopo qualche
   decina di secondi ed è R23. Non è automatizzabile sul banco — serve un gestore di finestre — e va
   fatta a mano.

9. **La rete strozzata rallenta, non blocca.** Con `tc netem delay 120ms rate 250kbit` sul server, i
   fotogrammi devono continuare a partire — meno di prima, ma senza fermarsi — e nel registro i
   fotogrammi in volo **non devono mai superare la soglia** scritta accanto. Se la superano, il
   regolatore non sta regolando niente e il conto salirà finché il socket non cede.

---

## 10. Quello che è ancora aperto

| # | Domanda | Stato |
|---|---|---|
| 1 | ~~RDM accende AVC420?~~ | **CHIUSA: no** (§1.4) |
| 2 | ~~RDM rende RemoteFX Progressive?~~ | **CHIUSA: sì** (§1.7) [M, 4 agosto] |
| 3 | ~~I bordi della regione AVC420: inclusivi o esclusivi?~~ | **CHIUSA: esclusivi** (R5) [M, 4 agosto] |
| 4 | ~~RDM decodifica H.264 in hardware o software?~~ | **irrilevante**: non lo decodifica affatto |
| 5 | Audio e grafica insieme reggono su Android? | **RIDIMENSIONATA il 5 agosto 2026**: sì, ma peggio degli altri — vedi sotto. Nota: grd **non** ha spento l'audio per RDM, perché la sua regola guarda `OsMajorType == ANDROID/IOS` e RDM si dichiara *«Unspecified platform»* |
| 6 | ~~RDM apre MS-RDPEI?~~ | **CHIUSA: no** (§1.3) |
| 7 | ~~RDM ha un interruttore H.264 nascosto?~~ | **CHIUSA: no** (§1.4) |
| 8 | L'AAC serve a qualcuno? | aperta (§1.5) |
| 9 | Con mstsc, sfondo al 75 % dopo un cambio di misura | aperta dal 3 agosto, rimandata per decisione dell'utente |
| 11 | ~~Con mstsc, minimizzando la finestra la connessione cade~~ | **CHIUSA il 5 agosto 2026**: mancavano `refreshRectSupport` e `suppressOutputSupport` (R23) |
| 10 | ~~L'audio esce come rumore su tutti e tre i client~~ | **CHIUSA il 5 agosto 2026**: `freerdp_dsp_encode` ribaltava il segno di ogni campione (**R24**) |
| 11-bis | ~~L'audio scoppietta~~ | **CHIUSA il 5 agosto 2026**: blocchi troppo corti, che il client buttava (**R25**) |
| 12 | **Il ritmo dei blocchi regge su rete lenta?** | aperta. Il nostro regolatore guarda la nostra coda; se a riempirsi è quella del canale non lo vediamo. Il segnale che lo direbbe sono i riscontri, come in xrdp (**R25**) — e il server ora **li misura** e li scrive nel registro. ⚠ Da misurare **fuori dalla VM**: la sua rete è SLIRP in spazio utente (§8.6-bis) |
| 13 | ~~Il micro-stutter che resta: codificatore o rete?~~ | **RISPOSTA IN PARTE, 5 agosto**: sotto carico perdeva la **cattura**, non il canale — mancava la priorità di tempo reale (**R26**). Quel che resta su RDM va misurato con la n.12 |

> **La prova dell'orecchio, sui tre client.** [M, 5 agosto 2026, utente]
>
> | Client | Esito |
> |---|---|
> | `xfreerdp3` su Linux | **sincronizzato col video e comprensibile**, con qualche micro-stutter |
> | **mstsc** | idem |
> | **RDM** su Android | comprensibile, ma il micro-stutter è **molto più marcato** |
>
> **Ricaduta sulla n.5**, ed è la prima misura che abbiamo su quella domanda: audio e grafica insieme
> su Android **reggono** — il suono si capisce e sta in sincrono. Non regge *bene* come sugli altri
> due. La motivazione con cui `gnome-remote-desktop` spegne l'audio ai client Android — *«Client
> cannot handle graphics and audio simultaneously»* — descrive quindi una **degradazione, non
> un'impossibilità**, e spegnere l'audio a tutta una famiglia di client resta una scelta più drastica
> di quel che il fatto richiede.
>
> **La n.13, e come è andata a finire.** [M, 5 agosto 2026]
>
> Il primo indiziato era il **ciclo**: l'audio è cadenzato dallo stesso ciclo che codifica il video,
> e l'ordine era «svuota la coda → componi il blocco → codifica il fotogramma», quindi ogni blocco
> partiva **al giro dopo, dopo una codifica intera**. Corretto — adesso si compone prima di svuotare
> — e a desktop fermo gli strappi sono scesi da 4 a **2**, cioè alle sole giunture della sorgente.
>
> Ma **con lo schermo sotto carico ne comparivano venti**, e la bisezione ha spostato il colpevole:
> i salti stavano **già nei byte che consegniamo al canale**. Non era il trasporto, era la
> **cattura**: senza priorità di tempo reale il suo `data-loop` perde il quanto ogni volta che il
> codificatore si prende il core. La cura sta in una riga dell'unità systemd — **R26**.
>
> **Su RDM il micro-stutter è sopravvissuto alla priorità**, e allora si è misurato il server
> **mentre l'utente guardava un video** — 130 secondi di sessione vera, RDM a 2560×984 in RemoteFX
> Progressive. [M, 5 agosto 2026]
>
> **Il carico, e va detto perché è quel che dà peso ai numeri**: un video **YouTube 1080p30** in un
> browser. Cioè, sugli stessi quattro vCPU e nello stesso momento: la decodifica del video, la
> composizione di GNOME **in software** (niente virgl, §8.6-bis) e la codifica RFX Progressive di
> 2 560×984 — anch'essa in software. Non è un banco: è il caso peggiore che questa macchina possa
> vedere.
>
> | Segnale | Misura |
> |---|---|
> | fotogrammi catturati contro attesi | 5 742 878 contro 5 733 000, **scarto +0,17 %** |
> | `ERR` di `pw-top` (xrun di tutto il grafo) | **0**, dall'inizio alla fine |
> | coda del server | fra 10 e 69 ms, **mai in crescita**; zero campioni buttati |
> | blocchi riscontrati dal client | **due per blocco** — li conferma tutti |
>
> **Il lato server non perde niente**, e questo è il fatto solido. Lo scatto quindi nasce a valle, e
> le due possibilità restano rete o client — con un indizio nuovo: all'orecchio è **periodico**
> («uno scatto ogni tot»), non a raffiche casuali, che è la forma di un confine di buffer, non di una
> rete che inciampa.
>
> **L'indiziato più probabile è il telefono**, ed è la stessa cosa che abbiamo appena corretto sul
> server, a parti invertite: là il codificatore affamava la cattura, qui il decodificatore di RFX
> Progressive a 2560×984 — in software, su un telefono — compete con chi rende l'audio. È la
> motivazione di `gnome-remote-desktop` (§10.2), ma adesso con una misura sotto: **il server è
> pulito, quindi quel che resta è dall'altra parte**.
>
> **Le due prove che restano, in ordine di costo:**
>
> | Prova | Che cosa deciderebbe |
> |---|---|
> | abbassare il carico del client — meno risoluzione o meno fotogrammi al secondo — e riascoltare | se l'audio si liscia, è la **CPU del telefono**: né la rete né noi |
> | leggere il **viaggio dei riscontri**, che il server ora scrive nel registro | un massimo molto sopra la media dice che il collegamento si ferma: sarebbe la **n.12** |
>
> **E una leva che resta nostra**, se si volesse aiutare un client debole senza spegnergli l'audio:
> **il blocco più lungo**. La scorta che il client tiene vale `2 × la durata del blocco che gli
> mandiamo` (R25): oggi sono ~61 ms, e allungarli gli darebbe più margine al prezzo di altrettanto
> ritardo.

> ✅ **La n.10 è chiusa: era `freerdp_dsp_encode`.** [M, 5 agosto 2026] Il come, per intero, sta in
> **R24**.
>
> La bisezione che mancava era una sola, e la diceva già la tabella di allora: *«entra un seno, esce
> rumore, e in mezzo ci sono soltanto `freerdp_dsp_encode` e il `WAVE2`»*. Si è chiamata **la sola
> `freerdp_dsp_encode`**, fuori dal server, su un seno noto — `banco-b/spia-dsp.c`, quaranta righe —
> e ha restituito lo stesso seno con **il bit di segno ribaltato su tutti e 8 820 i campioni**:
> FreeRDP codifica il PCM a 16 bit di RDP, che è *con segno*, con `AV_CODEC_ID_PCM_U16LE`, che è
> *senza*.
>
> Si spedisce quindi con `SendSamples2`, che non passa dal DSP — come fa `gnome-remote-desktop`.
>
> **Tre lezioni, e nessuna riguarda l'audio.**
>
> | | |
> |---|---|
> | Il banco era **verde** mentre l'audio era inascoltabile | contava fotogrammi e riscontri, e il difetto cambiava i campioni senza cambiarne il numero. Ora `prove/fase8.sh` **registra quel che il client suona** (sezione 4-bis), e il controllo è stato provato a rovescio: sulla stessa registrazione col segno ribaltato diventa rosso |
> | La correzione precedente era **attribuita al posto sbagliato** | la distorsione era stata data al volume non dichiarato, e `SetVolume` sembrava averla corretta. Non l'aveva corretta: era vera solo la parte «il volume si dichiara». Un merito attribuito male è una caccia da rifare |
> | Isolare **una funzione sola** costa meno di un giro di banco | mezz'ora di programma minimo contro un giorno di sospetti su cinque strati. Quando la catena è già ristretta a due anelli, li si chiama da fuori |

> ✅ **La n.2 è stata chiusa il 4 agosto 2026: RDM rende RFX Progressive, e il desktop si vede.**
> Il come sta in §1.7. La ricetta si è rivelata quella prevista: `gnome-remote-desktop` su una
> sessione **Wayland** — nella VM di runtime, che essendo senza accelerazione grafica non lascia a
> grd altra scelta che RFX Progressive.
>
> **La lezione di metodo, che vale per le prossime misure**: il banco è stato certificato *prima* di
> collegare il client di riferimento, con un client strumentato che ha contato i fotogrammi RFX
> Progressive. Senza quel passaggio, uno schermo nero su RDM sarebbe stato indistinguibile da un
> banco che non mandava il codec giusto — ed è esattamente l'ambiguità che il 3 agosto è costata la
> domanda aperta.

### 10.1 La decisione presa il 3 agosto 2026

**Android resta fra i client di riferimento, e si aggiunge RemoteFX Progressive** come secondo codec
sulla pipeline EGFX, scelto al `CapsConfirm` (R3).

Le ragioni, in ordine di peso:

1. è l'unico modo di servire il client Android di riferimento;
2. **è la stessa struttura del riferimento**: `gnome-remote-desktop` usa AVC dove c'è accelerazione e
   RFX Progressive dove non c'è;
3. su Android **rende di più**, non è un ripiego: l'H.264 lì si decodifica in software, mentre RFX
   Progressive è un codec a wavelet per contenuto desktop che costa poca CPU
   ([`client-android.md`](client-android.md) §1.2-bis) — e la misura empirica dell'utente conferma che
   RDM è il più veloce dei tre client Android provati;
4. rende **il testo più nitido** dell'H.264 4:2:0, e apre la strada alla codifica per regioni di §5.2
   di `SPECIFICA.md` senza costi aggiuntivi.

**Il costo, messo in conto**: due contesti di codifica, selezione per client, due percorsi da
mantenere. E il tranello dell'ordine delle bande di quantizzazione, **diverso** fra MS-RDPRFX e
MS-RDPEGFX (`protocollo-rdp.md` §9.4): chi riusa `rfx_encode_message` di FreeRDP **deve rimescolare**.

**Nota che assolve il progetto**: la soglia «solo EGFX» resta giusta — RDM negozia EGFX alla versione
**10.7**, più alta di mstsc. Il problema non era la pipeline, era **il codec dentro la pipeline**.

### 10.2 Ricadute minori, acquisite

- **Audio: PCM per primo.** Né mstsc né RDM negoziano AAC o Opus (§1.5).
- **Niente tocco nativo**: MS-RDPEI non serve per RDM. La questione aperta n.1 di `SPECIFICA.md` si
  ridimensiona da «implementare MS-RDPEI» a «far funzionare bene il mouse emulato».
- **`SCALEDMAP_DISABLE`** acceso da RDM sulla 10.7: niente varianti *scaled* di `MapSurfaceTo*`.

  > ✅ **E su `xfreerdp3` invece lo scaled output SI RENDE. Misurato il 7 agosto 2026**, aprendo la
  > fase 10 — dove quella riga non è più «non le useremo comunque»: `MAPSURFACETOSCALEDOUTPUT` è
  > l'unica strada che l'adattamento di risoluzione possa prendere senza litigare con MS-RDPEDISP
  > (riquadro della fase 7 in `PIANO.md`).
  >
  > Mandando `targetWidth/Height` **metà** della superficie, il client disegna la scena intera
  > dentro 1280×720 e lascia nero il resto della finestra: cioè la scala, non il ritaglio. Il banco
  > è `prove/fase10-scala.sh`, e la prova è una **fotografia dello schermo del client** — il nostro
  > registro direbbe solo che abbiamo chiamato una funzione (corollario di R12).
  >
  > ⚠ **Non era deducibile dagli header, e la deduzione dava la risposta opposta**: il contesto
  > client di FreeRDP (`freerdp/client/rdpgfx.h`) espone `MapSurfaceToWindow` e
  > `MapSurfaceToScaledWindow` e **non** le due varianti «output» — che infatti il client gestisce
  > per conto proprio. Chi si fosse fermato a leggere l'interfaccia avrebbe concluso «non lo rende».
  >
  > ⛔ **E MSTSC NON LO RENDE.** [M, utente, 7 agosto 2026] Collegandosi al banco con la scala a
  > metà, la scena di prova compare **a finestra piena, come al solito** — mentre su `xfreerdp3`, a
  > parità di tutto, sta in un quarto con il nero attorno.
  >
  > Cioè: **lo scaled output è reso da un client su tre**, e non dai due severi. RDM lo dichiara
  > spento (`SCALEDMAP_DISABLE`); mstsc **non lo dichiara spento e lo ignora lo stesso** — che è la
  > forma peggiore, perché una capacità dedotta dai flag direbbe di sì. È R1 in una veste nuova: il
  > client accetta il comando, riscontra i fotogrammi, e disegna un'altra cosa.
  >
  > **Ricaduta sulla fase 10, e va detta invece che aggirata**: l'adattamento di risoluzione non ha
  > una strada. Quella dello scaled output serve solo `xfreerdp3`; quella del ridimensionamento del
  > monitor virtuale era già stata scartata con una misura (riquadro della fase 7 in `PIANO.md`: a
  > schermo intero il client rimanda la propria misura ogni secondo e disfa la scelta del server, e
  > cambiare la misura del monitor ridispone le finestre dell'utente). Sotto il pavimento dei
  > ~4 Mbit/s di R31 resta quindi **la sola leva dei fotogrammi**, che è quella della fase 7.
  >
  > ⚠ **La misura è una sola, riferita dall'utente.** Se un giorno qualcosa dipendesse da questa
  > riga, si rifà: `banco-scala.sh avvia`, ci si collega alla 3390 e si guarda. Costa dieci secondi.
- **RDM non si dichiara Android** (`Unspecified platform`): ogni euristica basata su `OsMajorType`
  — come quella di grd sull'audio — **non scatta** per il nostro client di riferimento.

---

## 11. Trappole dell'API di FreeRDP

*Raccolte scrivendo la fase 2, il 4 agosto 2026. Non sono difetti di FreeRDP: sono punti dove l'API
si comporta diversamente da come la si legge, e dove sbagliare non produce un errore di compilazione
né un messaggio sensato.*

### R23 — si dichiarano `refreshRectSupport` e `suppressOutputSupport`, e si onorano

> ⛔ **Senza, mstsc cade quando si minimizza la finestra.** Misurato il 5 agosto 2026, e corretto lo
> stesso giorno.

Le due capacità stanno nel **General Capability Set**, e valgono come permesso: un client corretto
**non manda mai** una richiesta di soppressione se il server ha scritto zero. REMOTIX scriveva zero —
`FreeRDP_RefreshRect` era esplicitamente `FALSE` e `FreeRDP_SuppressOutput` non era toccata — e la
conseguenza era questa:

| | |
|---|---|
| L'utente | minimizza la finestra di mstsc |
| Il client | vorrebbe dire «fermati», **non può**, e smette di guardare |
| Il server | continua a codificare e a spedire ~10 Mbit/s di H.264 a una finestra invisibile |
| Dopo qualche decina di secondi | mstsc tronca la connessione: `BIO_read … 104: Connection reset by peer` |

**La firma nel registro è quella**, e va riconosciuta: un `Connection reset by peer` **senza** nulla
che lo preceda — RTT normale, zero fotogrammi in volo, nessuna strozzatura — non è una rete che cade.
È un client che ha rinunciato.

**La correzione, e quel che si è misurato dopo:**

```
13:38:28.6  il client non vuole piu' aggiornamenti: smetto di codificare
13:38:28 → 13:38:43   fotogrammi spediti FERMI a 20, per quindici secondi
13:38:43.7  il client chiede un ridisegno di 1 aree: rispedisco il fotogramma
13:38:43.7  il client rivuole gli aggiornamenti (con area): riprendo
```

La connessione ha retto, e mstsc **manda la soppressione appena gliela si permette**: nella sessione
di prima, con le capacità a zero, di quelle righe non ce n'era una.

> **Non c'entra con la persistenza della sessione**, e conviene averlo scritto perché la domanda
> nasce da sé: qui si ferma la sola **spedizione** dei fotogrammi. Sessione grafica, palco,
> applicazioni, cattura, audio e appunti continuano identici. La disconnessione è un'altra cosa, e la
> tratta la fase 5.

Al ritorno si rispedisce l'ultimo fotogramma (`visto = 0`, cioè R9 applicata al ripristino): senza,
la finestra riaperta resterebbe su quel che c'era prima. Vale anche per il `refresh rect`, che mstsc
manda **prima** del permesso di riprendere — mandiamo sempre il fotogramma intero, quindi le aree non
si guardano.

### R15 — `WTSRegisterWtsApiFunctionTable` va chiamata una volta, prima di tutto

```c
WTSRegisterWtsApiFunctionTable(FreeRDP_InitWtsApi());   /* una volta, all'avvio */
```

Senza, WinPR non sa che l'API WTS la implementa FreeRDP: ripiega sugli stub di **FreeRDS**, prova a
caricare `libfreerds-fdsapi.so`, non la trova, e **`WTSOpenServerA` restituisce NULL**. Nessuna
connessione nasce.

Il sintomo non nomina la causa:

```
[ERROR][com.winpr.wtsapi] - InitializeWtsApiStubs_FreeRDS: failed to parse freerds.instance
[ERROR][com.winpr.library] - LoadLibraryA: failed with libfreerds-fdsapi.so
```

La chiamano tutti i server di FreeRDP (shadow, proxy, sample) e `gnome-remote-desktop`. [M, 4 agosto]

### R16 — `peer->Logon` non serve ad autenticare quando non c'è NLA

FreeRDP chiama `Logon` **alla negoziazione**, non dopo il Client Info PDU. Nel ramo senza NLA gli
passa un'identità **vuota** (`libfreerdp/core/peer.c`):

```c
client->authenticated = IFCALLRESULT(TRUE, client->Logon, client, &client->identity, FALSE);
```

Un server TLS-puro che autentica lì **non autentica niente**: è R14 in una forma nuova, e stavolta
la trappola è nell'API invece che nel protocollo.

**Dove va la guardia**: in `PostConnect`. Le credenziali del Client Info PDU arrivano allo stato
`SECURE_SETTINGS_EXCHANGE` e finiscono in `FreeRDP_Username` / `FreeRDP_Password` / `FreeRDP_Domain`;
`PostConnect` viene dopo, quindi lì ci sono davvero. E restituire `FALSE` da `PostConnect` chiude la
connessione **prima dell'attivazione**, cioè prima che si veda un pixel. [M, 4 agosto]

### R17 — certificato e chiave TLS: uno per connessione, mai condiviso

```c
freerdp_settings_set_pointer_len(imp, FreeRDP_RdpServerCertificate, certificato, 1);
```

**Non copia**: assegna il puntatore (`settings->RdpServerCertificate = cnv.v`), e
`freerdp_settings_free` lo libera insieme al peer. Condividere un solo oggetto fra le connessioni
significa che **la prima se lo porta via e la seconda usa memoria liberata**.

> ⚠ **E la documentazione dell'intestazione installata dice il contrario**, quindi chi la legge si
> convince che questa regola sia sbagliata: `freerdp3/freerdp/settings.h:579` promette *«copy created,
> previous value freed»*. Vale per gli altri campi, **non** per `RdpServerCertificate` e
> `RdpServerRsaKey`, dove la libreria **prende possesso** del puntatore. La regola resta, e la
> conferma è che `KRdp` — che serve più connessioni insieme — ricostruisce **certificato e chiave a
> ogni connessione** dal PEM (`krdp/src/RdpConnection.cpp:412-424`), tenendo da parte solo i percorsi.
> [R, 7 agosto 2026]

Si conserva il **PEM come testo** e si ricostruisce `freerdp_certificate_new_from_pem` a ogni
connessione, come fa `gnome-remote-desktop`.

**Come si manifesta**, ed è la parte da ricordare:

| | |
|---|---|
| Lato client | «non si collega», e nient'altro |
| Registro del server | `connessione da …` e poi **silenzio** |
| Dove sta la verità | `dmesg`: `segfault … in libcrypto.so.3` |

E soprattutto: **una prova a connessione singola resta verde per sempre.** È la regola dei tre client
applicata al *numero* di connessioni invece che al tipo — la prova deve aprirne almeno due di fila.
[M, 4 agosto]

### R18 — l'encoder RemoteFX Progressive c'è già, e non va rimescolato

`progressive_compress` è API pubblica di FreeRDP ed è quella che usa il suo shadow server. Il
tranello dell'ordine delle bande di quantizzazione (`protocollo-rdp.md` §9.4) riguarda **chi riusa
`rfx_encode_message`** per produrre Progressive — come fa `gnome-remote-desktop`, che infatti
rimescola. Chi usa `progressive_compress` non deve rimescolare niente.

> ✅ **Confermato sull'occhio, il 4 agosto: su RDM l'immagine si vede corretta.** Serviva, perché un
> ordine di bande sbagliato produce un'immagine sbagliata e **non** un errore di decodifica: i 296
> fotogrammi accettati da un client FreeRDP dicevano che il flusso era ben formato, non che i pixel
> fossero al posto giusto. Ora lo sappiamo. [M, 4 agosto]

### R19 — i canali dinamici **accodano**, i PDU di autodetect **no**

`WTSVirtualChannelWrite` su un canale dinamico non scrive niente sul socket: mette in coda
(`wts_queue_send_item` → `MessageQueue_Post`), e i byte partono quando il ciclo chiama
`WTSVirtualChannelManagerCheckFileDescriptor`. I PDU della misura di rete invece vanno **dritti**
(`rdp_send_message_channel_pdu`).

Chi stringe la misura di banda attorno a `SurfaceFrameCommand` manda quindi **entrambi** i marcatori
prima del fotogramma, e il client conta i byte di ciò che c'è in mezzo — cioè niente.

| Dove si mandano Start e Stop | Byte contati dal client |
|---|---|
| attorno a `SurfaceFrameCommand` | **10** (solo il PDU di Stop) |
| attorno a `WTSVirtualChannelManagerCheckFileDescriptor` | **18 533**, cioè il fotogramma |

[M, 5 agosto 2026] Il difetto **non dà nessun errore**: la misura gira, risponde, produce un numero
plausibile. È il rapporto fra byte e millisecondi a smascherarla, ed è il motivo per cui i due numeri
grezzi stanno nel registro accanto al risultato.

> Vale per qualunque cosa debba essere **ordinata rispetto ai fotogrammi**, non solo per la banda:
> due strade di scrittura, una con la coda e una senza, non conservano l'ordine delle chiamate.

### R20 — l'autodetect: ganci prima di `Initialize`, e i suoi numeri non si usano

Due tranelli nello stesso `rdpAutoDetect`.

**Il momento.** L'autodetect *alla connessione* sta nella macchina a stati fra le impostazioni
riservate e le licenze (`peer.c:927`), cioè **prima** di `PostConnect` (`peer.c:756`). Ganci
installati nel posto naturale perdono la prima misura — l'unica disponibile quando parte il primo
fotogramma. Si installano subito dopo `freerdp_peer_context_new`, prima di `peer->Initialize`.

**I numeri.** `netCharAverageRTT` e `netCharBaseRTT` li aggiorna la libreria da sé, ma
`autodetect_recv_rtt_measure_response` calcola il round trip come «adesso meno `rttMeasureStartTime`»,
dove quel campo è l'istante dell'**ultima richiesta spedita** — non di quella a cui il client sta
rispondendo. Con una sonda per volta il conto torna; con la cadenza a 70 ms su una rete lenta le sonde
si accavallano **sempre**, e il numero misura l'intervallo fra due sonde invece del ritardo della
rete. Ogni sonda va annotata col suo numero di sequenza, e la risposta accoppiata per numero.

> Quel che invece la libreria fa bene, e non va rifatto: `gcc.c:1096` spegne da solo
> `FreeRDP_NetworkAutoDetect` se il Client Core Data non porta
> `RNS_UD_CS_SUPPORT_NETCHAR_AUTODETECT`. Il prerequisito di §16 di `protocollo-rdp.md` è già
> controllato: basta leggere l'impostazione.

### R21 — `rdpsnd`: l'attivazione arriva dal Quality Mode, non dai formati

*Letto in `channels/rdpsnd/server/rdpsnd_main.c` di FreeRDP 3.15, aprendo la fase 8. [R, 5 agosto
2026]*

| Cosa | Come sta davvero |
|---|---|
| `Initialize(ctx, ownThread)` | **è** `Start`: apre il canale **e manda subito i formati del server**. Non c'è un `Open` separato da chiamare dopo |
| `Activated` | **non** scatta alla ricezione dei formati del client: per i client ≥ Windows 7 scatta al **Quality Mode PDU** (`SNDC_QUALITYMODE`), che arriva dopo. Solo i client più vecchi la fanno scattare sui formati |
| Da quale thread | dal thread del canale, se `ownThread = TRUE`. È scritto anche nell'intestazione: *«this callback is called from a different thread context»* |
| Prima di `SendSamples` | servono **`src_format` impostato** e **`SelectFormat(indice)`** chiamata, altrimenti i campioni vengono **scartati in silenzio** con `ERROR_NOT_READY` e un `WLog_WARN` che nessuno guarda |
| `SendSamples` | non spedisce a ogni chiamata: accumula fino a `latency` millisecondi (50 se non la si imposta) e allora manda un `WAVE2` |
| Canale dinamico | `use_dynamic_virtual_channel = TRUE` apre `AUDIO_PLAYBACK_DVC` con `WTSVirtualChannelOpenEx` — quindi **solo a `drdynvc` in stato READY**, come EGFX e DISP |
| I formati del client | sono il **sottoinsieme di quelli che il server ha annunciato**: chi offre solo PCM leggerà sempre «AAC no», e non avrà misurato niente sull'AAC (§10 n.8) |
| Il volume | si dichiara con `SetVolume`: un client a cui non si dice niente parte con quello che si è scelto da solo |

> ⛔ **R19 vale anche per l'audio.** `WTSVirtualChannelWrite` accoda: i campioni partono quando il
> ciclo chiama `WTSVirtualChannelManagerCheckFileDescriptor`, non quando `SendSamples` ritorna. Un
> ciclo che si ferma ferma anche il suono — e i byte dell'audio finiscono dentro la finestra della
> misura di banda, che è dove devono stare, perché sul filo ci passano davvero.

### R24 — `SendSamples` passa dal DSP, e il DSP **ribalta il segno** del PCM

*Misurato il 5 agosto 2026 con `banco-b/spia-dsp.c`, che chiama la sola `freerdp_dsp_encode` su un
seno noto — niente rete, niente client, niente cattura. [M]*

> ⛔ **Il PCM a 16 bit consegnato a `SendSamples` arriva al client con il bit di segno ribaltato, e
> si sente come rumore a fondo scala.** È la causa della questione n.10, ed è costata un giorno
> perché non è né nostra né visibile: i campioni sono giusti prima, i PDU sono formati bene dopo, e
> in mezzo c'è una funzione che si suppone non faccia niente.

`rdpsnd_server_send_wave2_pdu` chiama **sempre** `freerdp_dsp_encode`, anche quando la sorgente e la
destinazione sono lo stesso identico formato. Con `WITH_DSP_FFMPEG=ON` — che è come Debian Trixie
compila `libfreerdp3`, cioè come giriamo noi — quella funzione manda i campioni al codificatore FFmpeg
scelto da `ffmpeg_get_avcodec`, e per `WAVE_FORMAT_PCM` a 16 bit quella tabella restituisce
**`AV_CODEC_ID_PCM_U16LE`**.

Il PCM a 16 bit di RDP è **con segno** [S, MS-RDPEA]; quello di FFmpeg è **senza**. La conversione
somma `0x8000` a ogni campione.

| | picco | rms | primi campioni |
|---|---|---|---|
| seno di ampiezza 3000, in ingresso | 2 999 | 2 121 | 0, 0, 187, 187 |
| quel che ne esce | **32 768** | **30 872** | −32 768, −32 768, −32 581, −32 581 |

8 820 campioni su 8 820 sono l'originale con `x ^ 0x8000`. All'orecchio: un'onda a fondo scala che
segue la frequenza giusta — cioè qualcosa che *sembra* audio che arriva.

**Il rimedio: `SendSamples2`**, che scrive i byte come sono (`encoded = TRUE`).

| | |
|---|---|
| Perché è lecito | la sorgente **è** il formato scelto dal client: non c'è niente da convertire, e il DSP era di troppo |
| Che cosa vuole | l'**indice** del formato nell'elenco del client, e i byte già pronti — la spezzettatura la fa il chiamante |
| Da quale versione | `clientVersion >= 0x08` (`CHANNEL_VERSION_WIN_8`, in `rdpsnd_common.h`, che **non viene installato**): è la stessa soglia con cui FreeRDP sceglie fra `WAVE` e `WAVE2` |
| Chi altro fa così | **`gnome-remote-desktop`**: `grd-rdp-audio-playback.c` codifica per conto suo e chiama `SendSamples2`; per il PCM (`GRD_RDP_DSP_CODEC_NONE`) manda i byte grezzi. Il DSP di FreeRDP non lo tocca mai [R, 48.1] |

> **Non è un incidente della 3.15**: la stessa tabella sta identica nel `master` di FreeRDP. Chi
> aggiorna la libreria non deve aspettarsi che il problema sia sparito.

> **La lezione di banco**, che vale oltre l'audio: il banco della fase 8 contava i fotogrammi spediti
> e i blocchi riscontrati, ed era **verde** con l'audio inascoltabile. Nessun contatore poteva
> vedere un difetto che cambia i campioni senza cambiarne il numero. Ora il banco **registra quel che
> il client suona** e ne guarda la forma d'onda (sezione 4-bis di `prove/fase8.sh`).

> ⛔ **E chi passa a `SendSamples2` eredita un compito**: `SendSamples` accumulava fino a `latency`
> millisecondi prima di comporre un PDU, `SendSamples2` spedisce quel che gli si dà. Il ritmo va
> rifatto a mano, e senza si scoppietta: **R25**.

### R25 — il ritmo dei blocchi: interi, uno per giro, mai due di fila

*Misurato il 5 agosto 2026 col registro di `rdpsnd` del client (`xfreerdp3 /log-level:DEBUG`), che
dice a voce quel che butta. [M]*

> ⛔ **Il client BUTTA i blocchi corti.** La sua tolleranza è `2 × la durata del blocco che sta
> ricevendo`, più la propria latenza — che di norma è zero. Un blocco da 5 ms se ne porta dietro
> 10, e viene rifiutato quasi sempre.

Il conto sta nel client di FreeRDP, `rdpsnd_detect_overrun`:

```c
maxDuration = duration * 2 + rdpsnd->latency;
if (remainingDuration + duration > maxDuration)   /* butta il blocco INTERO */
```

Ne discendono due cose, e la seconda non è ovvia: **i blocchi corti muoiono**, e **il secondo di due
spediti di fila muore** — quando arriva, la coda del client è ancora piena del primo.

**Da dove venivano i blocchi corti**, nel nostro caso: il ciclo della connessione si sveglia a
*qualunque* evento — un tasto, un movimento del mouse, e perfino il riscontro di un blocco audio.
Chi spedisce «quel che c'è nell'anello» a ogni risveglio manda pezzi da cinque millisecondi. È un
anello di retroazione: più PDU → più riscontri → più risvegli → PDU più corti.

| Sei secondi di tono, misurati sul client | prima | blocchi interi | e con la coda di silenzio |
|---|---|---|---|
| blocchi buttati (`Buffer overrun … dropping`) | **35** | 0 | **0** |
| vuoti (`Buffer underrun`) | 17 | 1 | 1 |
| dimensioni ricevute | 940–6 588 byte (5–37 ms) | 11 288–12 232 byte (64–69 ms) | idem |
| strappi nell'onda che il client suona | **168** (27,9/s) | 7 | **4**, e **due sono nella sorgente** |
| picco dell'onda | 3 609, con le sbavature del ricampionatore | **3 000 esatto** | 3 000 |

> I due strappi che restano stanno a 2043 ms e 4064 ms: sono le giunture fra i tre `pw-play` del
> banco, che finiscono a metà onda. **Ci sono identici nei byte che consegniamo al canale** — cioè
> non sono nostri, sono di chi suona. Quel che passa per REMOTIX arriva com'è partito.

**Le regole, tutte con la stessa radice:**

| | |
|---|---|
| **mai un blocco parziale** | sotto i 50 ms non si spedisce: si aspetta il giro dopo. Il suono arriva in tempo reale, quindi 50 ms si riempiono in 50 ms |
| **uno per giro** | due di fila il client li rifiuta comunque |
| **in ritardo, uno più grande** | fino a 200 ms in un solo PDU: un blocco grande porta con sé una tolleranza grande, ed è così che si recupera senza farsi buttare |
| **oltre mezzo secondo in coda, si butta il passato** | spedirlo non servirebbe, e il ritardo fra ciò che si vede e ciò che si sente non tornerebbe più indietro |
| **mezzo secondo di coda di silenzio** | il silenzio non si spedisce (§7.5), ma smettere al *primo* blocco muto costa uno strappo a ogni ripresa: su una voce, a ogni pausa |

**Chi lo fa già così.** `xrdp` accumula in `g_buffer` e spedisce solo a blocco pieno — 8 192 byte per
il PCM — e ha in più un regolatore che misura il viaggio dei riscontri (§8.3.1 di
`xrdp-funzionalita.md`). E `SendSamples` di FreeRDP faceva lo stesso per chi la usava.

> **Il limite noto, e sta nella questione n.12.** Il nostro regolatore guarda **la nostra** coda. Se
> a riempirsi è la coda del canale o il buffer del client — rete lenta, non ciclo lento — la nostra
> coda resta vuota e non ce ne accorgiamo. L'unico segnale che lo direbbe sono **i riscontri**, che
> già contiamo e non usiamo; il regolatore di xrdp è fatto esattamente di quelli.

### R26 — il percorso audio vuole la priorità di tempo reale, e va **concessa dall'unità**

*Misurato il 5 agosto 2026, con lo schermo sotto carico dentro la VM di runtime. [M]*

> ⛔ **Un processo con `RLIMIT_RTPRIO` a zero — il valore predefinito — non può chiedere
> `SCHED_FIFO`.** PipeWire ci prova, gli viene negato, e il suo `data-loop` resta a priorità
> normale: lì dentro gira la raccolta dei campioni, che deve rispettare un quanto di pochi
> millisecondi **mentre nello stesso processo il codificatore video si prende un core per decine**.

Il sintomo non è un errore: è audio che scoppietta *quando il desktop lavora*, e che a desktop fermo
non si riproduce. Ed è a monte del canale — cioè invisibile a qualunque controllo sul filo.

| Sei secondi di tono, con lo schermo che scorre | senza `LimitRTPRIO` | con `LimitRTPRIO=20` |
|---|---|---|
| picco dell'onda **consegnata al canale** | **3 299** (deformata) | **3 000 esatto** |
| strappi in quel che consegniamo | 7 | 7, di cui **2 sono le giunture della sorgente** |
| strappi in quel che il client suona | 12 | **7 — identici a quelli consegnati, campione per campione** |
| blocchi buttati dal client | 0 | 0 |

La riga che conta è l'ultima: con la priorità, le due analisi coincidono fino al **conteggio dei
campioni**. Tutto quel che resta è già nella sorgente, e **il trasporto non aggiunge più niente**.

**Dove si concede**: nell'unità systemd, non nel codice — `LimitRTPRIO=20` e `LimitNICE=-11` in
`installa-servizio.sh` e in `provision-vm.sh`. Venti è modesto: sotto i thread audio del kernel,
sopra qualunque cosa faccia il codificatore.

> **Nella VM non c'è `rtkit-daemon`** (`inactive`), quindi la strada del portale non esiste e resta
> solo quella degli rlimit. Su una macchina che lo avesse, PipeWire lo userebbe da sé — ma non ci si
> può contare: un server non ha una sessione grafica a cui chiedere il portale. [M]

> **Non sostituisce l'accelerazione hardware, la anticipa**: la fase 9 toglie la CPU al
> codificatore, e quindi toglie la contesa alla radice. Ma una sessione che lavora competerà sempre
> con la cattura, e la priorità serve anche dopo.

### R27 — il codificatore hardware: tre cose che, mancando, non danno un errore utile

*Misurate il 6 agosto 2026 aprendo la fase 9, sulla iGPU Intel passata alla VM di runtime. [M]*

> ⛔ **Nessuna delle tre si presenta come «manca la GPU».** Si presentano come un codificatore
> che non si apre, o — peggio — come un ripiego silenzioso in CPU con il registro che tace.

| # | La trappola | Come si presenta | Che cosa serve |
|---|---|---|---|
| 1 | **Il nodo di rendering giusto non è il primo** | `vainfo` senza argomenti risponde `init failed`, e sembra che il passthrough non abbia funzionato | nella VM `renderD128` è **virtio-gpu**; la scheda vera è `renderD129`. Si provano **tutti** i nodi e vale quello su cui il codificatore si **apre** — che è anche l'unica prova che conti: un nodo può inizializzare VA-API e non avere il motore di codifica |
| 2 | **Il firmware del kernel** | `vainfo` elenca i profili, ma il driver dichiara **solo `CQP`** come controllo del bitrate, e chiedere VBR fa fallire l'apertura con *«Driver does not support any RC mode compatible with selected options»* | `firmware-intel-graphics` — **non** `firmware-misc-nonfree`, che su Trixie non contiene più `/lib/firmware/i915`. E va caricato **all'avvio**: installarlo a macchina accesa non cambia nulla finché non si riavvia la VM. Con GuC e HuC caricati, VBR c'è |
| 3 | **L'entrypoint è solo quello a basso consumo** | il codificatore non si apre, e senza dichiararlo si ripiegherebbe in CPU credendosi in GPU | sulle Intel recenti `vainfo` dice `VAProfileH264High : VAEntrypointEncSliceLP` **e nient'altro**: `h264_vaapi` va aperto con `low_power=1` |

> **Corollario di metodo, e vale oltre la GPU**: quando si chiede un componente **per nome**, non si
> ripiega su un altro. Chi lo indica sta misurando, e un ripiego silenzioso produce due misure
> diverse sotto la stessa etichetta — che è peggio di non misurare. `--codificatore h264_vaapi`
> fallisce dichiarandolo, invece di tornare a `libx264` in punta di piedi.

### R28 — tolta la codifica dalla CPU, il collo di bottiglia diventa la conversione di colore

*Misurato il 6 agosto 2026, con la GPU in funzione, su fotogrammi 2560×1024. [M]*

Il tempo di un fotogramma, letto dal registro di REMOTIX:

| | |
|---|---|
| conversione BGRx → NV12 (`libswscale`, in CPU) | **12,5 ms** |
| caricamento sulla superficie della scheda | 3,1 ms |
| **codifica H.264 vera (VA-API)** | **3,8 ms** |

Cioè: **il codificatore è il pezzo più economico dei tre.** Il consumo di CPU crolla — da 1,21 a
0,47 core sulla stessa scena — ma il ritmo cala, da 29 a **22,7 fotogrammi al secondo**, perché il
tempo se lo prende il pezzo rimasto.

> **Un guadagno che si paga in fluidità non è un guadagno**, e va detto invece di mostrare il solo
> numero della CPU. La cura è la **cattura zero-copy con DMA-BUF**, che consegna il fotogramma già
> sulla scheda e lascia la conversione a lei: è la seconda metà della fase 9, e adesso si sa quanto
> vale prima di scriverla.

> ⚠ **Provato e scartato, per non rifarlo**: dare più thread a `libswscale` (`sws_alloc_context` +
> `threads`) non cambia niente — 13,8 ms contro 12,5, cioè rumore. Quel tempo non è di calcolo, è
> di memoria.

### R29 — la cattura a copia zero: cinque punti dove si fallisce in silenzio

*Scritta il 6 agosto 2026, dopo averli pagati tutti e cinque. [M]*

Portare il DMA-BUF di PipeWire fino al codificatore **senza copiarlo** è possibile e vale molto —
sul desktop vero il costo per fotogramma scende da **25 a 7 ms di CPU** — ma la strada è lastricata
di rifiuti che non nominano la propria causa. Nell'ordine in cui si incontrano:

| # | Che cosa | Come si presenta | Che cosa serve |
|---|---|---|---|
| 1 | Il consumatore guarda `data` prima del tipo | il registro dice «i fotogrammi arrivano come DMA-BUF» e poi **nient'altro** | un DMA-BUF **non ha `data`**: il puntatore resta NULL. Il tipo si guarda **prima** del puntatore, o si scarta tutto |
| 2 | La dimensione dell'oggetto non dichiarata | `-5`, e nessuna spiegazione | `objects[0].size` va riempita: la si chiede a `lseek(fd, 0, SEEK_END)`, che è l'unico a sapere quanto ha allocato davvero il compositore — qui **più** di `passo × altezza` |
| 3 | Il fotogramma d'origine con un contesto DRM, e la mappatura fatta a mano | `-22`, e libav **non dice una parola**: l'errore nasce prima del driver | non si mappa a mano. Si usa il filtro **`hwmap`**, che è la strada di ffmpeg stesso, e il dispositivo si dà **al filtro** — `AVFilterGraph` non ha un campo per questo, quindi il filtro va allocato, dotato e solo dopo inizializzato |
| 4 | Il descrittore in un campo proprio, non in un riferimento | `Cannot allocate memory` da un filtro | un fotogramma che entra in un grafo dev'essere **contato per riferimenti**: se non lo è, libavfilter prova a **copiarlo**, e un fotogramma che vive sulla scheda non ha dove essere copiato. Il descrittore va dentro un `AVBufferRef` suo, uno per fotogramma |
| 5 | Il grafo che non rende nulla, e nessuno lo dice | **identico a un desktop fermo** | il ritorno di `av_buffersink_get_frame` si registra. Senza, «la scena non si muove» e «i fotogrammi spariscono da noi» sono la stessa riga di registro — ed è costata mezz'ora di esperimenti di controllo |

> ⛔ **E il bordo di R4 non lo sa riempire nessuno.** La conversione della scheda (`scale_vaapi`) sa
> cambiare formato e misura, ma **non sa deporre un'immagine dentro una più grande**: chiedendole la
> misura allineata *allunga* l'immagine invece di riempirle attorno. Si compone quindi sopra una
> superficie già allineata e già nera, creata **una volta sola** (`overlay_vaapi`): un solo passaggio
> sulla scheda, e nessun caricamento per fotogramma.

> **Che cosa NON serve, contro l'intuizione**: trattenere il buffer di PipeWire. Convertendolo subito
> — l'importazione è una chiamata, non una copia — quel che si conserva per R9 è la **superficie
> nostra**, e il buffer torna al compositore appena la richiamata finisce. Tenere in ostaggio una
> risorsa di chi ce l'ha prestata sarebbe stato il modo peggiore di rispettare R9.

> ⛔ **E IL SESTO PUNTO, TROVATO DALL'UTENTE: LO SCHERMO ALTERNA DUE FOTOGRAMMI.** [M, 7 agosto 2026]
>
> **Il fatto, misurato su una registrazione dello schermo del client** (578 fotogrammi confrontati uno
> per uno, `xfreerdp3` su LAN, desktop 1024×768):
>
> ```
>  stato | da t   a t    | fotogrammi
>      7 | 13.67 14.23 | 18     ← la scrivania CON Firefox
>      9 | 14.27 14.37 |  4     ← la scrivania SENZA Firefox
>      7 | 14.40 14.53 |  5
>      9 | 14.57 14.63 |  3          … per quattro secondi
> ```
>
> Non è un'immagine sporca, né parziale, né due immagini sovrapposte (che sarebbe R10, ed è del
> client): sono **due schermate intere e pulite che si alternano**, e ci sono fotogrammi **identici a
> quello di due prima**. Quel che il client mostra è, un giro sì e uno no, **una schermata già
> passata**.
>
> **La strada è la colpevole, ed è misurato su due client**, cambiando una cosa sola
> (`REMOTIX_DMABUF=0`, cioè gli stessi pixel per l'altra strada, stesso codificatore in GPU):
>
> | | a copia zero | in memoria |
> |---|---|---|
> | `xfreerdp3` | **alterna** | pulito |
> | mstsc | **alterna** | pulito |
>
> ### ✅ Il meccanismo, misurato il 7 agosto 2026: **il DMA-BUF è un «diff», non un fotogramma**
>
> ⛔ **E la prima diagnosi era sbagliata, per un errore di campione.** Guardando i **primi dieci**
> fotogrammi il danno risultava `copre tutto` in nove casi su dieci, e il sospetto del ridisegno
> parziale è stato scartato. I primi dieci sono l'**avvio**, quando tutto viene ridipinto. Il
> riassunto su trecento dice il contrario:
>
> ```
> cattura su 300 fotogrammi: 4 buffer distinti,
>                            disegno non finito 288, danno parziale 282
> ```
>
> **282 su 300 hanno danno parziale.** *Da un campione preso all'avvio non si conclude niente sul
> regime* — è la stessa forma dell'errore di R19, dove la misura pesava il nulla.
>
> **Il meccanismo, per intero:**
>
> 1. Mutter ricicla **quattro buffer** e, in 94 casi su 100, vi ridipinge **solo la regione cambiata**;
> 2. noi il danno lo chiediamo ma non lo **usiamo**: prendiamo il buffer come fotogramma intero;
> 3. quel che consegniamo è quindi il contenuto **vecchio** di quel buffer con sopra la sola zona
>    ridipinta — e quando la zona è piccola il risultato è, **byte per byte**, una schermata già
>    passata. Misurato sull'anello: `anello-029/030/031` identici ad `anello-024` di quattro secondi
>    prima, mentre il compositore continuava a consegnare.
>
> In memoria non succede perché lì Mutter **ricopia ogni volta il fotogramma intero**: il buffer
> parziale non esiste, e la copia che la fase 9 voleva togliere era anche l'unica cosa che ci
> sincronizzava — per caso, e senza che nessuno lo sapesse.
>
> **La correzione**: il buffer in arrivo è un *diff*. Si tiene una **superficie persistente di
> accumulo** e vi si copiano **solo i rettangoli di `SPA_META_VideoDamage`**; si codifica da quella.
> Tre trappole, tutte silenziose:
>
> | | |
> |---|---|
> | i rettangoli sono in **coordinate del flusso** | con scalatura o ritaglio vanno tradotti, o si copia la regione sbagliata e l'accumulo resta stale a pezzi |
> | `overlay_vaapi` **non deve deporre il buffer intero** sulla persistente | rimetterebbe dentro esattamente i pixel vecchi |
> | la persistente non si riscrive mentre è ancora fra i **reference frame** di `h264_vaapi` | servono `extra_hw_frames`, o i fotogrammi vecchi riappaiono da un'altra strada |
>
> **E la sincronizzazione resta da fare**: `poll(POLLIN)` dice «disegno non finito» su 288 fotogrammi
> su 300, e aspettarla non cambia nulla perché è la fence **implicita**, cioè quella sbagliata. La
> esplicita viaggia in `SPA_META_SyncTimeline`, che il riferimento chiede e noi no (§11.2 di
> `gnome-remote-desktop.md`).
>
> ### ⛔ E LA CORREZIONE CHE NE DISCENDE È STATA SCRITTA, E HA PEGGIORATO LE COSE
>
> *7 agosto 2026. Provata dall'utente su mstsc: «la situazione è anche peggiore».*
>
> L'attuazione era quella che la diagnosi indica, e che il riferimento conferma: una **superficie di
> accumulo** sempre completa, su cui si depongono le sole regioni danneggiate con una copia di
> regione in VA-API (`VAProcPipelineParameterBuffer` con `surface_region` e `output_region`, perché
> libavfilter lavora solo sul fotogramma intero), e la consegna al codificatore di una **copia**
> dell'accumulo — non dell'accumulo vivo, che il codificatore tiene fra i reference frame.
>
> **Sul banco era verde**: scena a rampa di grigi, serie monotona sul client, zero ritorni indietro.
> **Sull'uso vero era peggio di prima.** La diagnosi regge — il *diff* è misurato — e quel che non
> regge è questa attuazione: manca ancora qualcosa, e il primo sospetto resta la **sincronizzazione
> esplicita** (`SPA_META_SyncTimeline`), perché senza di essa ogni copia di regione può leggere una
> superficie che la scheda sta ancora scrivendo.
>
> Il codice resta, **dietro `REMOTIX_ACCUMULO=1`, spento di suo**: serve a chi riprenderà la caccia
> per confrontare le due strade senza ricompilare. E `REMOTIX_DMABUF=0` è diventato il predefinito
> di `provision-server.sh`.
>
> ### ⛔ E QUEL PREDEFINITO NON HA RETTO MEZZA GIORNATA
>
> *7 agosto 2026, pomeriggio. L'utente si collega e rivede il difetto: «di nuovo le schermate vecchie
> a programma chiuso e lo schermo che flasha».*
>
> La copia zero era **accesa**. Non per una regressione del codice: nel codice il predefinito era
> «accesa», e a spegnerla c'era la riga `REMOTIX_DMABUF=0` in **`/etc/default/remotix`** — un file
> che **vive in RAM** e che era stato riscritto per portare la porta alla 3392. La riga di guardia è
> sparita con la riscrittura, e `provision-server.sh` non l'ha rimessa perché la scriveva **solo se
> il file non esisteva**.
>
> **La regola, e vale molto oltre il DMA-BUF**: *la protezione di un difetto noto non si affida a una
> riga di configurazione che si può perdere.* Sta nel programma, dove per toglierla bisogna volerlo.
> Dal 7 agosto `palco.c` nasce con la copia zero **spenta** e `REMOTIX_DMABUF=1` la accende — cioè
> l'interruttore è girato rispetto a prima, ed è il verso giusto: chi misura lo accende
> deliberatamente, chi non ne sa niente non lo incontra.
>
> **E una seconda lezione, di metodo, che è costata all'utente il pomeriggio**: quel file era stato
> **letto** all'inizio della sessione, e la riga mancava già. Chi legge un file d'ambiente all'inizio
> di una fase deve confrontarlo con quel che i documenti dichiarano — «`REMOTIX_DMABUF=0` è il
> predefinito» era scritto qui sopra, e bastava accorgersi che nel file non c'era.
>
> ⛔ **E LA REGOLA DI BANCO CHE NE ESCE, che vale oltre questo caso: un banco che NON riproduce non è
> una prova di correttezza.** Due riproduzioni — client nel contenitore su loopback, client su
> un'altra macchina in LAN — hanno aperto e chiuso Firefox senza mostrare nulla, mentre il difetto
> era vivo nell'uso vero: in quegli scenari il compositore produce più spesso danno pieno o buffer
> appena allocati. A trovarlo è stato l'**anello** — un fotogramma ogni dieci registrato di continuo,
> con l'ora — che non chiede a nessuno di essere presente nell'istante giusto.
>
> **La radice comune, e vale come regola a sé**: `cattura.c` **non chiede un solo `SPA_PARAM_Meta`**.
> Il riferimento chiede sempre `SPA_META_Header` e `SPA_META_Cursor`, e la timeline quando c'è. In
> memoria l'omissione non fa danno — Mutter ricopia ogni volta il fotogramma intero — e per questo è
> rimasta invisibile dalla fase 3 alla fase 8.
>
> **Perché nessun banco l'ha vista**: contano i fotogrammi, e il numero è **giusto**. È lo stesso
> punto cieco di R24 (il segno del PCM), a cui si era risposto insegnando al banco ad *ascoltare*.
> Qui il banco deve imparare a **guardare**: due fotogrammi consegnati a distanza devono essere
> diversi quando la scena è cambiata, e uguali quando non lo è.

### R30 — le due strade dei pixel, e a sceglierle è il **codificatore**, non il codec

*Misurata il 6 agosto 2026, chiudendo la seconda metà della fase 9. [M]*

> ⛔ **Il palco che lavora sulla scheda non ha pixel in CPU, e metà dei nostri codificatori li
> vogliono lì.** Chi ne cerca non trova un errore: trova il nulla, cioè uno schermo fermo —
> indistinguibile da un desktop che non cambia (R9, con una causa nuova).

Con la cattura a copia zero il fotogramma arriva come DMA-BUF, si importa sulla scheda e non passa
mai dalla memoria. Ma tre casi diversi vogliono i pixel in memoria, e **due dei tre non si vedono
guardando il codec**:

| Chi | Perché |
|---|---|
| **RemoteFX Progressive**, cioè ogni client Android (§1.4) | è un codec a wavelet: gira in CPU, e in GPU non ci va |
| **`--codificatore libx264`**, che è AVC420 | è il termine di paragone con cui si misura la fase 9 |
| un **`h264_vaapi` che ha ripiegato** sul proprio nodo invece che sulle superfici del palco | ha un contesto suo, e le superfici del palco non le accetta |

**Da cui la regola, ed è la stessa forma di R27**: non lo si deduce dal codec, **si legge dal
codificatore che si è aperto davvero**. Dedurlo produce due strade sotto la stessa etichetta.

**Come si cambia strada**: dalla stessa porta del ridimensionamento —
`pw_stream_update_params` con la proposta di formato senza modificatori — e per la stessa ragione
(§7.3: rifare la cattura rifarebbe il controllo, e con lui i dispositivi di libei). **Misurato: il
giro completo costa 18 ms**, e Mutter rimanda subito un fotogramma per la strada nuova.

```
17:33:49.788  porto la cattura in memoria: ci sono 1 client che vogliono i pixel in CPU
17:33:49.806  i fotogrammi arrivano come memoria condivisa (MemFd)
```

**Tre cose da fare insieme, e mancandone una il difetto è silenzioso:**

1. **il bit del tipo di buffer segue il modificatore.** `SPA_PARAM_BUFFERS_dataType` va acceso su
   `SPA_DATA_DmaBuf` solo mentre lo si vuole: tornare in memoria lasciandolo acceso lascia a
   Mutter la facoltà di consegnare ancora DMA-BUF, che in memoria nessuno guarda;
2. **R9 vale per strada, non in assoluto.** Il fotogramma conservato sta su una strada sola; a chi
   legge dall'altra non serve a niente. Dopo il cambio si **aspetta il primo fotogramma della
   strada nuova** — e serve un contatore per strada, perché uno della strada vecchia ancora in volo
   farebbe dichiarare riuscito un passaggio non avvenuto;
3. **si conta, non si commuta.** Le richieste appartengono alle connessioni e si sovrappongono: si
   torna sulla scheda quando l'ultima è stata lasciata. Chi si dimentica di restituirla lascia la
   copia zero spenta per il resto della sessione — e nessuno se ne accorge, perché funziona tutto,
   solo più piano.

**Il banco è `prove/fase9.sh copia-zero`**, e prova sul **desktop vero** — non sulla scena
sintetica, che disegnamo noi in memoria e che quindi un caricamento lo pagherebbe sempre.

| Sul desktop vero, stessa scena mossa dagli stessi tasti | in memoria | a copia zero |
|---|---|---|
| ms di CPU per fotogramma | 24–25 | **7–9** |
| fotogrammi consegnati | 99–105 | **120–148** |

> ⛔ **IL CONVERTITORE NON SEGUE IL RIDIMENSIONAMENTO DA SÉ, E VA RIFATTO.** [M, 6 agosto 2026]
>
> Il suo grafo nasce con dentro la misura del desktop **e** quella allineata; un ridimensionamento le
> cambia entrambe. Chi lo tiene si ritrova superfici della misura di prima, che il codificatore
> rifiuta — e da lì **la copia zero è persa per il resto della sessione**, con un avviso che nessuno
> guarda.
>
> Il seguito era peggio del difetto: rifiutate le superfici, `apri_libav` tornava indietro del tutto
> e il chiamante passava al **candidato successivo** — da `h264_vaapi` a **`libx264`**. Un
> ridimensionamento buttava la sessione dalla GPU alla CPU, e l'avviso diceva «si torna al percorso
> in memoria»: vero per i pixel, falso per il codificatore.
>
> **Le due regole che ne discendono:**
>
> 1. il convertitore si butta quando il palco cambia misura, e il primo fotogramma della misura nuova
>    lo ricostruisce — **prima** che la connessione vada a riaprire il codificatore;
> 2. superfici della misura sbagliata fanno rinunciare **alle superfici**, non al codificatore: perdere
>    le prime costa una copia per fotogramma, perdere il secondo costa un core.
>
> Trovato dall'utente **ridimensionando la finestra a video in corso**, cioè facendo la cosa che un
> banco a misura fissa non fa mai. Ora la fa `prove/fase9.sh copia-zero`, sezione 5.

> ⛔ **E il palco può non esserci affatto.** Con `--immagine-di-prova` il server non ne crea uno, e
> `palco_superfici(NULL)` è un **segfault**: il sintomo era il server che moriva subito dopo «EGFX
> negoziato» e il client che vedeva `BIO_read retries exceeded`, cioè una caduta di rete dalla parte
> sbagliata del filo. Le funzioni sorelle — `palco_input_prendi`, `palco_suono_prendi`,
> `palco_appunti_prendi` — il controllo ce l'hanno tutte; questa è nata dopo e se l'era perso.
> [M, 6 agosto]
>
> **La lezione, e non riguarda il NULL**: il difetto è stato introdotto scrivendo la fase 9 e trovato
> eseguendo il banco della **fase 6**. Una fase che tocca un percorso condiviso va chiusa rieseguendo
> i banchi delle fasi che quel percorso lo attraversavano già — qui `fase2.sh` e la sezione 1 di
> `fase6.sh`, che sono le uniche che usano la scena sintetica **dentro** il contenitore.

### R31 — il modo di controllo del bitrate **non si sceglie: lo deduce il driver**

*Misurato il 7 agosto 2026, aprendo la fase 10, sulla iGPU Intel del server. [M]*

> ⛔ **`rc_max_rate == bit_rate` significa CBR, e nessuno l'aveva scelto.** REMOTIX riempiva i due
> campi con lo stesso valore, e il driver Intel dichiarava `RC mode: CBR` — banda **costante**,
> ottenuta riempiendo. Non c'era alcun errore, alcun avviso, e alcuna riga di registro: c'era una
> bolletta.

A 2560×1440, `h264_vaapi`, tetto di 10 000 kbit/s, misurato contro un riferimento senza perdita:

| scena | CBR *(quel che si spediva)* | VBR | QVBR | CQP 22 *(quel che fa grd)* |
|---|---|---|---|---|
| **documento fermo** | **9 875** kbit/s → 51,0 dB | 945 → 50,7 | **277** → 49,2 | 234 → 48,9 |
| video a schermo intero | 10 016 → 30,4 | 9 748 → 30,3 | 10 121 → 30,3 | **42 060** → 31,6 |
| video in una finestra | 9 967 → 42,8 | 9 629 → 42,6 | 9 500 → 42,4 | 13 555 → 43,2 |

Tre letture, e la terza è quella che decide:

1. **su un desktop fermo il CBR spendeva dieci volte la banda per 0,3 dB** — e a 234 kbit/s quel
   testo si legge già benissimo, guardato a occhio e non dedotto dal numero;
2. **CQP, la strada del riferimento, chiede 42 Mbit/s** su contenuto mosso. §9.1 di
   `gnome-remote-desktop.md` diceva che là non c'è controllo del bitrate; qui c'è il prezzo. §3.1 di
   `SPECIFICA.md` — «qui siamo soli» — è confermato da una misura;
3. **sul contenuto difficile i modi regolati sono equivalenti** (entro 0,06 dB). La scelta non si
   gioca sulla scena dura: si gioca su quanto si spende quando non serve.

**Si chiede `rc_mode` per nome** (`av_dict_set(&opzioni, "rc_mode", "VBR", 0)`) e si mette il tetto
**sopra** l'obiettivo — una volta e mezza. È il corollario di R27 applicato a un'altra domanda:
quando un componente può decidere da sé, chi misura deve dirgli cosa fare, o si ottengono due misure
diverse sotto la stessa etichetta.

Misurato sul percorso vero, scena sintetica 2560×1440, stesso banco prima e dopo:
**da 7 400 kbit/s a 99–583 kbit/s**, a parità di fotogrammi al secondo e senza differenza visibile.

> ⛔ **E SOTTO UN CERTO TETTO IL CODIFICATORE NON LO RISPETTA PIÙ, in nessun modo.**
>
> A 2560×1440 su contenuto mosso, chiedendo **2 000** kbit/s ne escono **3 702** (VBR), **3 966**
> (CBR), **4 111** (QVBR). A 1080p, chiedendone 2 000 ne escono 2 616. `libx264` invece il tetto lo
> tiene esatto (1 992).
>
> C'è un **pavimento**, ed è del codificatore hardware: attorno ai 4 Mbit/s a 1440p. Da lì in giù
> l'unica leva sono **meno pixel o meno fotogrammi**, non meno bit per fotogramma — ed è la ragione
> misurata per cui la scala 4K → 2K → 1080p di §3.1 di `SPECIFICA.md` esiste, e per cui il
> regolatore della fase 7 non basta da solo.
>
> È anche la prima verifica di §5.5 di `SPECIFICA.md` («gli encoder hardware rendono peggio a
> bitrate bassi»): sopra i 6 Mbit/s `h264_vaapi` e `libx264` si equivalgono entro 0,3 dB; sotto, il
> primo sfonda il tetto e il secondo no.

> ⚠ **E LA MISURA DELLA QUALITÀ HA TRE TRAPPOLE, tutte pagate lo stesso giorno.** Il primo banco
> dava PSNR **identico a sei decimali** con 500 e con 20 000 kbit/s — un numero che non misurava
> niente:
>
> | | |
> |---|---|
> | **il flusso grezzo si dichiara a 60 fps** | `ffprobe` legge `r_frame_rate 60/1` da un Annex B prodotto a 30, e il confronto accoppia fotogrammi diversi: si misura lo **sfasamento**, che è uguale a ogni bitrate. Si rimuxa con `-framerate 30 -c copy` prima di confrontare; `-r 30` in ingresso **non basta** |
> | **la scena finiva prima del filmato** | il testo scorreva via e restavano secondi di bianco: PSNR 72 dB, cioè la media di uno schermo vuoto |
> | **la scena era in bianco e nero** | `mse_u` e `mse_v` a zero su ogni fotogramma: il 4:2:0 non veniva esercitato affatto, e §5.2 di `SPECIFICA.md` resta fuori dalla misura |
>
> È §1.1 applicata al banco: un numero verde su uno strumento sbagliato non vale niente.

### R32 — quanto eroga il compositore, e perché i 18 fotogrammi erano nostri

*Misurato il 7 agosto 2026 sul server, sul ferro nudo, rispondendo al compito posto dall'utente.
Banco in `/media/REMOTIX/tmp/banco-compositori`, fuori dal prodotto. [M]*

> ⛔ **I 18 fotogrammi al secondo del 7 agosto non sono un limite di Mutter: sono il numero che gli
> abbiamo chiesto noi.** REMOTIX dichiara a PipeWire un massimo di **30** (`main.c`, `--fotogrammi`),
> e Mutter consegna **18,4**. Dichiarandone **60** ne consegna **37,0**. Dichiarandone 120, ancora 37.

**Come è stata fatta, perché senza questo i numeri non valgono.** Si misura **la sola cattura**, con
RDP e il codificatore fuori dai piedi; la scena è **dichiarata e si muove sempre**
(`weston-simple-egl` a schermo intero, opaco, sincronizzato al ridisegno del compositore); e in ogni
cella si è contato **anche quanto disegna il client**, che è il controllo che dice se il tetto è del
compositore o della scena.

| Controllo | Esito |
|---|---|
| desktop **fermo**, nessuna scena | **0 fotogrammi**: Mutter manda solo quando cambia qualcosa |
| quanto disegna il client, in ogni cella | **59,8–61,2 fps**, cioè il pieno |
| frequenza del monitor virtuale di Mutter | **60,000 Hz**, letta da `DisplayConfig` |

Cioè: il client disegna sessanta fotogrammi al secondo su uno schermo a sessanta hertz, e **Mutter
ne consegna trentasei**. Ne perde circa il 40 %, a ogni risoluzione e su tutte e due le strade.

#### Mutter — la tabella

*Fotogrammi al secondo consegnati; fra parentesi la mediana dell'intervallo fra un fotogramma e il
successivo.*

| | in memoria (MemFd) | a copia zero (DMA-BUF) |
|---|---|---|
| **1920×1080** | 34,0 *(33,3 ms)* | 36,6 *(33,3 ms)* |
| **2560×1440** | 31,3 *(33,3 ms)* | 36,6 *(33,3 ms)* |
| **3840×2160** | 42,5 *(17,6 ms)* | 38,2 *(33,3 ms)* |

**La risoluzione non è il fattore limitante**: da 1080p a 4K la portata non cala. Non lo è nemmeno la
**profondità di colore** — BGRA contro BGRx dà 33,2 contro 34,0 in memoria e 36,1 contro 36,6 a copia
zero, cioè rumore. E sono le uniche due che la cattura offre: **non esiste un percorso a 24 bit
impacchettati**, entrambe sono 32 bit per pixel.

**E non è nemmeno il carico.** Con `glmark2` a schermo intero che rende **2 632 fotogrammi al
secondo** e satura la GPU, Mutter ne consegna comunque **40,2** a 4K e 39,6 a 1080p.

#### La cadenza dichiarata è l'unica leva che sposta il numero

| Dichiarato a PipeWire | 1920×1080 | 3840×2160 |
|---|---|---|
| **30** *(quel che REMOTIX dichiara oggi)* | **18,4** | 18,2 |
| **60** *(quel che dichiara `gnome-remote-desktop`)* | **37,0** | 36,5 |
| 120 | 36,8 | 37,0 |

Il rapporto è costante: **si ottengono circa sei decimi di quel che si chiede** (18,4/30 e 37,0/60
sono entrambi 0,61), **e oltre i 60 non si sale.**
I 18 del 7 agosto sono quindi spiegati fino all'ultima cifra, e `TARGET_SURFACE_REFRESH_RATE = 60` del
riferimento (§10.2 di `gnome-remote-desktop.md`) è il termine di paragone giusto: **grd chiede il
doppio di noi.**

> ⚠ **E una cadenza FISSA Mutter la rifiuta.** Dichiarando `framerate = 60/1` invece di `0/1` non si
> negozia alcun formato e non arriva un fotogramma. Lo `0/1` di §7.3 non è una preferenza: è l'unica
> forma che passa.

#### Sulla scena vera — un video 60 fps a schermo intero

| | in memoria | a copia zero |
|---|---|---|
| 1920×1080 | 34,3 | 39,8 |
| 2560×1440 | 35,1 | 38,7 |
| **3840×2160** | 48,8 | **54,6** *(mediana 18,0 ms)* |

Il video a 4K è l'unica cella in cui Mutter si è avvicinata al pieno. Non è spiegato, ed è la cosa da
riprendere per prima da chi vorrà i 60: **una superficie video a schermo intero con danno pieno passa
per una strada più veloce di un client qualunque.**

#### E il DMA-BUF non porta fotogrammi: porta CPU

36,6 contro 34,0 a 1080p. Il guadagno della copia zero è quello di R29/R30 — 6 ms di CPU per
fotogramma invece di 18 — **non il ritmo**. E il prezzo resta quello misurato: su **migliaia** di
fotogrammi, **il 100 % arriva col disegno del compositore non ancora finito** (il `poll` sul
descrittore dice «non pronto»), e il 94 % porta danno solo parziale. R29 diceva 288 su 300 con un
campione di trecento; qui è confermato su tutte le celle, senza eccezioni. I buffer riciclati sono
**quattro**, come scritto.

#### I tre compositori accanto, stessa macchina, stesso minuto, stessa scena

| Compositore | Come disegna, senza monitor | 1920×1080 | 2560×1440 | 3840×2160 |
|---|---|---|---|---|
| **Mutter 48.7** — memoria | **GPU** | 34,0 | 31,3 | 42,5 |
| **Mutter 48.7** — DMA-BUF | **GPU** | 36,6 | 36,6 | 38,2 |
| **KWin 6.3.6** — memoria | **GPU** *(corretto il 7 ago, vedi sotto)* | 43,3 | 36,8 | 27,7 |
| **KWin 6.3.6** — DMA-BUF | **GPU** *(corretto il 7 ago, vedi sotto)* | **59,5** | **59,1** | **60,0** |
| **sway 1.10.1** (wlroots) — `wl_shm` | **GPU** | **61,0** | **61,5** | 40,3 |
| **labwc 0.8.3** (wlroots) — `wl_shm` | **GPU** | 60,8 *(a 1280×720)* | — | — |

**È il risultato che conta di più di tutta la misura**: con lo **stesso misuratore**, sulla stessa
macchina e nello stesso minuto, KWin e wlroots consegnano **tutti i fotogrammi** e Mutter ne consegna
sei su dieci. Il misuratore quindi non è il collo di bottiglia — se lo fosse, non avrebbe contato 60
altrove — e **la perdita è di Mutter**.

Tre cose da sapere prima di citare quella tabella, tutte misurate:

| | |
|---|---|
| ~~**KWin senza monitor disegna in software**~~ ⛔ **SMENTITA, e la smentita è una misura** | *diceva*: col backend `--virtual` non apre alcun nodo DRM e non carica alcuna libreria GL, quindi il 60 a 4K è ottenuto senza GPU. **Falso.** [M, 7 agosto 2026, sera] KWin `--virtual` apre **`/dev/dri/renderD129`** e carica **`libEGL_mesa.so`** e **`libgbm.so`**, e annuncia **`zwp_linux_dmabuf_v1` v4** — che nasce solo dal backend EGL. **La prima misura non vedeva niente perché non poteva vedere**: `/usr/bin/kwin_wayland` porta l'xattr `security.capability`, quindi è **non dumpable** e il kernel nega `/proc/<pid>/fd` e `/maps` a chi non è root. Una lettura vuota era stata letta come «zero nodi DRM». **I numeri restano; l'etichetta era sbagliata** (`kde.md` §5.1) |
| **KWin tiene la cattura dietro un controllo di permessi** | il protocollo `zkde_screencast_unstable_v1` **non viene annunciato** a un client qualunque: serve `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1`, o il permesso per la via che KDE prevede. Chi scriverà la fase 11 lo incontra al primo tentativo, e il sintomo è «questo compositore non ha il protocollo». ✅ **La via che KDE prevede è stata trovata e misurata**: un file `.desktop` con `X-KDE-Wayland-Interfaces` — nessun dialogo, mai — **più `XDG_MENU_PREFIX=plasma-` nell'ambiente**, senza la quale l'indice dei servizi di KDE resta vuoto e il permesso è negato in silenzio (`kde.md` §3 e §3.3-bis) |
| **wlroots non spinge: fa tirare** | non ha né l'interfaccia D-Bus di Mutter né il protocollo di KWin. Si cattura con `zwlr_screencopy_manager_v1` + `copy_with_damage`, cioè **una richiesta e un giro di socket per fotogramma** — e nonostante questo consegna 61. A 4K scende a 40, e lì il costo è la copia in memoria condivisa: è la stessa ragione per cui la copia zero esiste |

> ## ⛔ DUE ETICHETTE DI QUESTA TABELLA SONO SBAGLIATE, e lo dice la lettura del codice
>
> *[R, 7 agosto 2026] Studio del codice di KWin 6.3.6 — `kde.md` §5.1 e §6.4. **Nessuna misura
> nuova**: questa è una tensione fra un codice letto e una misura presa, e si scioglie **rifacendo la
> misura**, non riscrivendo il numero.*
>
> **1. «KWin compone in software» è quasi certamente falso.** Il costruttore di `VirtualBackend` apre
> da sé un **nodo di rendering** `/dev/dri/renderD*` e dichiara `OpenGLCompositing` **solo se** ci
> riesce; il renderer è **EGL su gbm** (`virtual_backend.cpp:23-81`,
> `virtual_egl_backend.cpp:108-115`). E la prova sta **in questa stessa tabella**: il giro `dmabuf`
> ha consegnato **DMA-BUF con fence**, e un flusso screencast di KWin può essere DMA-BUF **solo se il
> compositore è un backend EGL** (`screencaststream.cpp:920-925`). Cioè KWin **stava componendo sulla
> GPU**. Il 60 a 4K resta un fatto; «senza GPU» no.
>
> **Le due prove che non dipendono da quel che KWin dichiara**, da fare per prime: il **tipo di
> buffer** che il flusso offre (DmaBuf ⇒ GPU, solo MemFd ⇒ QPainter) e la presenza del global
> **`zwp_linux_dmabuf_v1`**, creato solo dal backend EGL. Non fidarsi di `compositingType`, che
> distingue OpenGL da QPainter e **non** GPU da software: con llvmpipe KWin scrive «Compositing Type:
> OpenGL» pur rendendo in CPU.
>
> ⚠ **E `KWIN_COMPOSE=O2` non protegge**: l'enforcement è un `qApp->quit()` che gira **prima** del
> ciclo di eventi (`compositor_wayland.cpp:164` contro `main.cpp:144`), quindi è inerte — KWin
> prosegue in QPainter con una sola riga critica nel registro. Tutte le misure prese con quella
> variabile la presuppongono efficace.
>
> **2. Il banco misurava KWin nudo, non una sessione Plasma.** `banco/banco-altri.sh:33` avvia
> `kwin_wayland --virtual` **senza `--xwayland`**, e su Plasma `ksmserver` forza
> `QT_QPA_PLATFORM=xcb` e dereferenzia il display X11 **senza controlli**
> (`ksmserver/main.cpp:106-124`) ed è `Requires=` della catena di sessione: **con quella riga una
> sessione Plasma non parte**. Inoltre il banco usa `stream_output` sull'uscita del backend virtuale,
> mentre il prodotto userebbe `stream_virtual_output` — che con `--virtual` **non funziona affatto**
> (`core/outputbackend.cpp:80-83`).
>
> **Che cosa se ne fa chi riprende**: i numeri di KWin restano il termine di confronto, ma vanno
> **rifatti nella configurazione del prodotto** (backend `--drm`, `.desktop` installato,
> `stream_virtual_output`, `--xwayland`) prima di essere citati come cifre di REMOTIX. Il piano di
> misure è in `kde.md` §14.

> ## ✅ CHIUSO LA SERA DELLO STESSO GIORNO — la misura è stata rifatta
>
> *[M, 7 agosto 2026, sera. Banco `reference-kde/banco/permesso4-kde.sh` … `permesso6-kde.sh`, KWin
> 6.3.6-1, Mesa 25.0.7. Il riquadro sopra resta perché è la storia di come si è arrivati qui.]*
>
> **1. «In software» era sbagliato: KWin `--virtual` compone sulla GPU.** Tre prove concordi —
> `/dev/dri/renderD129` **aperto**, `libEGL_mesa.so` + `libgbm.so` **caricate**,
> `zwp_linux_dmabuf_v1` **v4 annunciato**. Le celle della tabella sono state corrette.
>
> ⚠ **E la causa dell'errore vale più della correzione**, perché è una trappola di metodo:
> `/usr/bin/kwin_wayland` porta l'attributo esteso **`security.capability`** (`cap_sys_nice`), e un
> binario con file capabilities è **non dumpable** — il kernel nega `/proc/<pid>/fd` e
> `/proc/<pid>/maps` **anche all'utente che l'ha avviato**. La prima misura ha letto un elenco vuoto
> e l'ha scambiato per «zero nodi DRM». **Una lettura negata non è una lettura che dice zero**: `ls`
> su un `/proc` proibito e `ls` su un `/proc` senza nodi DRM stampano la stessa cosa, e vanno
> distinti guardando lo stato d'uscita. Va letto con `sudo`.
>
> ⚠ **Seconda trappola, per chi rifà la prova su Mesa ≥ 25**: llvmpipe e tutti i driver gallium
> stanno in **un'unica `libgallium-*.so`**, quindi cercare `llvmpipe`/`swrast_dri` fra le librerie
> caricate **non prova più niente**. La prova che regge è il **render node aperto**.
>
> **2. `KWIN_COMPOSE=O2` — la misura 4 di `kde.md` §14 resta da fare**: l'analisi del codice qui
> sopra non è stata verificata sul banco, e le misure di questa tabella la presuppongono.
>
> **3. E `--drm`, che il riquadro sopra dava come configurazione «del prodotto», non è praticabile**:
> da una sessione senza seat esce con stato 1 (`Failed to activate … session` →
> `No suitable DRM devices have been found`). Quindi la configurazione del prodotto su KDE è
> **`--virtual`**, e i numeri di questa tabella sono già quelli del backend giusto (`kde.md` §5.2).

> ## 📊 E l'8 agosto 2026 la misura è stata rifatta **sulla GPU che userà il prodotto**
>
> *[M] Decisione dell'utente dell'8 agosto: **«non usare la Radeon, usa la Intel integrata»**. La
> tabella qui sopra è della Radeon RX 6800; questa è della **Intel UHD Graphics 770 (ADL-S GT1)**,
> ottenuta negando alla Radeon i permessi del nodo (`kde.md` §5.6). Stessa scena dichiarata e in
> movimento, stesso misuratore, 10 s per cella, tetto dichiarato 60.*
>
> | Risoluzione | copia zero (DMA-BUF) | in memoria (MemFd) |
> |---|---|---|
> | 1280×720 | **59,4** *(mediana 16,5 ms)* | 49,6 |
> | 1920×1080 | **59,2** *(17,2 ms)* | 43,3 |
> | 2560×1440 | **59,3** *(17,2 ms)* | 37,0 |
> | **3840×2160** | **59,0** *(17,2 ms)* | **27,0** |
>
> ⭐ **Il risultato che conta per il requisito dell'utente** (30 a 1080p, 60 a 4K): **a copia zero la
> risoluzione non costa niente** — 59 fotogrammi al secondo da 720p a 4K su una GPU **integrata** — e
> **in memoria costa tutto**: 27,0 a 4K, meno della metà del bisogno. Cioè il collo di bottiglia è
> **la copia**, non il compositore né la GPU. Su KDE la copia zero non è un'ottimizzazione: è la
> condizione per i 60 a 4K.
>
> ⚠ **E due avvertenze di misura, entrambe pagate lo stesso giorno:**
>
> - ⛔ **«il render node è aperto» non prova che si stia rendendo in GPU**: con `KWIN_COMPOSE=Q`
>   (QPainter) `renderD129` risulta aperto comunque, perché lo apre il costruttore del backend.
>   **La prova che regge è la stringa del renderer**, che KWin regala su D-Bus
>   (`org.kde.KWin.supportInformation`). Il global `zwp_linux_dmabuf_v1` distingue «EGL sì/no», non
>   «GPU sì/no».
> - ⛔ **`KWIN_COMPOSE=O2` non protegge dal ripiego in software** (misura M4, verificata): con i
>   render node inaccessibili KWin scrive `forced to OpenGL`, poi `Falling back to defaults`, poi
>   `QPainter … successfully initialized`, **e parte**. Nessuna misura può appoggiarsi a quella
>   variabile; e `LIBGL_ALWAYS_SOFTWARE` **non ha alcun effetto** su KWin.
>
> **Sulla sincronizzazione**, per chi riprenderà la copia zero: su KWin **il 100 % dei buffer DMA-BUF
> arriva con il disegno in corso** (830 su 830, misurato con lo stesso `poll()` sulla fence usato per
> Mutter), perché KWin fa `glFlush()` e non `glFinish()` — che invece fa su NVidia e llvmpipe. Non è
> il difetto di R29: i fotogrammi sono **interi**, quindi non serve la superficie di accumulo; serve
> **aspettare la fence**, che è il comportamento corretto di un consumatore (`kde.md` §4.8).

> ## ✅ E L'8 AGOSTO 2026 LA CATENA VERA HA CONFERMATO I NUMERI DEL BANCO
>
> *[M] Con REMOTIX al posto del misuratore: sessione Plasma, `.desktop` installato, cattura a copia
> zero, un client collegato. Banco `prove/fase11.sh misura`, GPU **Intel UHD 770**.*
>
> | Scena dichiarata e in movimento | 1920×1080 | 3840×2160 |
> |---|---|---|
> | **REMOTIX, catena vera** | **58,1** | **58,4** |
> | il solo misuratore (tabella qui sopra) | 59,2 | 59,0 |
>
> **Il mezzo fotogramma che manca è la conversione sulla scheda**, che il misuratore non faceva. Cioè
> il numero regge fuori dal banco, ed è la prima volta che succede su un compositore diverso da Mutter.
>
> ⚠ **E il numero AL CLIENT resta un'altra cosa**: 24 fotogrammi a 4K, con il tappo che è `xfreerdp3`
> a decodificare l'H.264 in software sulla stessa macchina — esattamente la nota in fondo a questa
> regola. «REMOTIX fa 24 fps a 4K» è una frase che il banco continua a non autorizzare.
>
> ⛔ **Due cose della strada dei pixel, che valgono come regole:**
>
> 1. **la fence si aspetta**, con un tetto (50 ms) e contando le scadenze: 2 400 buffer su 2 400
>    arrivano col disegno in corso e **nessuna attesa è mai scaduta**. Non aspettarla significa
>    codificare il fotogramma di prima, senza alcun errore;
> 2. **il modificatore si chiede LINEARE per primo**: RadeonSI rifiuta i buffer con DCC e iHD li
>    accetta e poi forza LINEAR internamente — cioè accetta e sbaglia in silenzio
>    (`kpipewire/src/vaapiutils.cpp:119-135`). Chiedendolo primo si ottiene `0x0`, misurato.

#### La catena intera — e qui il numero è quello che l'utente vede

*Misurato subito dopo, stessa macchina, stessa scena. Banco `banco-catena.sh`: cambia **una** cosa
sola fra un giro e l'altro, `--fotogrammi`, che è già un'opzione. Nessuna riga di codice toccata.
L'autenticazione resta **accesa** — la credenziale passa da una FIFO, quindi non compare in `ps` e
non tocca il disco. [M, 7 agosto 2026]*

| Risoluzione | dichiarati | **fotogrammi al client** | CPU | ms di CPU per fotogramma |
|---|---|---|---|---|
| 1920×1080 | **30** *(oggi)* | **18,7** | 0,36 core | 19 |
| 1920×1080 | **60** | **32,4** | 0,53 core | 16 |
| 1920×1080 | 60, **copia zero** | 31,5 | **0,12 core** | **3** |
| 3840×2160 | **30** *(oggi)* | 14,0 | 0,55 core | 39 |
| 3840×2160 | **60** | 16,9 | 0,58 core | 34 |
| 3840×2160 | 60, **copia zero** | 17,0 | **0,08 core** | **4** |

**Tre letture, e la seconda ribalta un'aspettativa del progetto.**

1. **A 1080p la cadenza dichiarata si paga fino in fondo**: 18,7 → **32,4**, cioè il minimo di §3.1 di
   `SPECIFICA.md` superato. Dei 37 che il compositore consegna, al client ne arrivano 32,4: il
   codificatore e il filo si prendono il 12 %.
2. ⛔ **La copia zero NON porta fotogrammi, e adesso è misurato sulla catena intera**: 31,5 contro
   32,4 a 1080p, 17,0 contro 16,9 a 4K. Taglia la CPU per fotogramma da 16 a **3** ms e da 34 a
   **4** — cioè vale cinque volte sul consumo — ma **il ritmo non lo tocca**. Chi riprenderà R29 lo
   faccia per la CPU, non per la fluidità: è la stessa lezione della fase 9, misurata una seconda
   volta e più a fondo.
3. ⛔ **E il 4K di questa tabella NON misura REMOTIX: misura il client di prova.** Il registro dice
   `in volo 2 di 2` in **835** campioni su 835, con RTT 0,2 ms e il server fermo a **0,08 core**. Il
   regolatore della fase 7 concede `MAX(2, rtt·fps/10⁶ + 2)` posti, che su un collegamento veloce
   fa **2**: il server non può portarsi avanti di più di due fotogrammi, quindi la portata diventa
   **quella con cui il client riscontra**. `xfreerdp3` decodifica l'H.264 a 4K **in software, sulla
   stessa macchina**, e ne riscontra 17.

> ### ✅ E il giudizio dell'utente, che è il metro (§7 di `SPECIFICA.md`)
>
> *Acceso sul server di lavoro con `--fotogrammi 60`, il 7 agosto 2026. [M, utente]*
>
> | Client | Codec | Ritmo misurato nel registro | Giudizio |
> |---|---|---|---|
> | `xfreerdp3` | AVC420 | 32–33 | **a posto** |
> | **mstsc** | AVC420 via `h264_vaapi` **in GPU** | **29–33** in movimento, 10–15 a desktop fermo | **«va benissimo»** |
> | **RDM** su Android | RemoteFX Progressive, in CPU dai due lati | **23–29**, media 25, `in volo 0 di 3` | **«performance eccellenti»** |
>
> **La regola dei tre client è soddisfatta**, e i tre numeri vengono dal registro del server durante
> le sessioni vere dell'utente, non dal banco. Su RDM il `in volo 0 di 3` è il dato che spiega il
> giudizio: **il telefono riscontrava tutto quel che gli arrivava**, e prima gliene arrivava la metà.
>
> ✅ **E il 60 è passato nel codice** (`main.c`), non piu' in `/etc/default/remotix`. Verificato con
> la sola configurazione predefinita, catena intera: **33,3 fotogrammi al secondo a 1080p**.
>
> ⛔ **E la previsione su RDM era sbagliata, vale la pena scriverlo.** Era stato previsto «neutro, e
> forse peggio sull'audio», perché RDM riceve RemoteFX Progressive, che si decodifica in software sul
> telefono e costa al server 1,20 core contro 0,47 (fase 9). Il ragionamento era corretto e la
> conclusione no, e il motivo è quello che questa regola misura: **i 18 fotogrammi erano un tappo
> nostro, a monte di tutto**. Tolto quello, ogni client ha preso quanto ne sapeva reggere — e il
> telefono ne aveva in avanzo. Nessuno dei due lati era al limite: lo era il numero che dichiaravamo.
>
> **Da cui due cose, e la seconda è un debito di misura.**
>
> I numeri di questa tabella sono un **pavimento, non un tetto**: con un client che decodifica in
> hardware possono solo salire. E **quanto REMOTIX regga davvero a 4K resta non misurato** — per
> saperlo serve un client che non sia lui il collo di bottiglia (mstsc su una macchina vera, o un
> client con decodifica hardware). Fino ad allora, «REMOTIX fa 17 fps a 4K» è una frase che il banco
> **non** autorizza a dire.

#### Che cosa se ne fa il progetto

1. **`--fotogrammi` va dichiarato a 60**, non a 30. È una riga, e porta i fotogrammi consegnati da
   **18 a 37** dal compositore e da **18,7 a 32,4 fino al client**: da sola avvicina il minimo di
   §3.1 di `SPECIFICA.md` più di tutta la fase 9.
2. **Il minimo — 30 fps a 1080p — è raggiunto**, misurato sulla catena intera (32,4 > 30).
3. **Il desiderato — 60 fps a 4K — non lo è su Mutter**, e non per la risoluzione: il tetto è la
   consegna, ~37 col client normale e ~55 col video. Su **KWin** invece 60,0 a 4K sono misurati.
4. **Non si guadagnano fotogrammi abbassando la risoluzione o la profondità di colore**: su questa
   strada non costano niente. La scala 4K → 2K → 1080p serve al codificatore, non alla cattura.

### R22 — `cliprdr`: senza il suo thread, la sequenza iniziale non parte da sola

*Letto in `channels/cliprdr/server/cliprdr_main.c` di FreeRDP 3.15. [R, 5 agosto 2026]*

`cliprdr_server_context_new` accende `autoInitializationSequence`, e quel nome inganna: la sequenza
— `ServerCapabilities` più `CLIPRDR_MONITOR_READY` — la esegue `cliprdr_server_init`, che è
**statica** e viene chiamata **solo dal thread di `Start`**.

| Se si fa così | Cosa succede |
|---|---|
| `Open` + `Start` | il thread manda capacità e `MonitorReady`, e la sequenza parte |
| `Open` e si pompa `GetEventHandle`/`CheckEventHandle` dal proprio ciclo | il canale è aperto e **non succede niente**: il client aspetta il `MonitorReady` che non arriverà mai, e gli appunti non funzionano senza che nulla lo dica |

Chi sceglie di pompare dal proprio ciclo deve quindi rifare a mano le due chiamate. Il canale è
**statico** (`cliprdr`): va prima verificato che il client lo abbia unito, come si fa per `DRDYNVC`.
