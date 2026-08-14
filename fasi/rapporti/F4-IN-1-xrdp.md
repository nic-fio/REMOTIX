# F4-IN-1 · xrdp e xorgxrdp — il puntatore che non costa niente

⭐ Studio dell'input, 14 agosto 2026 (sera). Bersaglio: **xrdp 0.10.1** e **xorgxrdp 0.10.2**,
le versioni **installate e accese su CHUWI**. Misure fatte sul ferro, su questa macchina.

---

## ⭐⭐ IL VERDETTO IN TRE RIGHE

1. **La frase del mandato è per metà falsa, e la metà falsa è quella che conta**: xrdp non manda
   **mai** la posizione del cursore — il *Pointer Position Update* è `#define`-ito e **mai usato**
   (`[R]` `common/ms-rdpbcgr.h:547` e `:572`, zero utilizzi in tutto l'albero), e `[M]` **200
   movimenti del mouse su schermo fermo = 0 byte dal server**. Non è che «RDP manda la posizione in
   PDU dedicate»: **non la manda proprio**.
2. **Il difetto di REMOTIX su xrdp non si presenta, ma non perché xrdp mandi più fotogrammi — ne
   manda MENO di noi**: `[R]` `xorgxrdp/module/rdpCursor.c:411-416` `rdpSpriteMoveCursor()` ha il
   **corpo vuoto**, e `[R]` `rdpClientCon.c:2857` non spedisce niente se la regione sporca è vuota.
   Schermo fermo + mouse che si muove = **0 fotogrammi al secondo**, contro i nostri 1,1. ⇒ **La
   nostra diagnosi «1,1 fps ⇒ desktop fermo ⇒ mouse inutilizzabile» è sbagliata nella catena
   causale**: 0 fps va benissimo, purché il puntatore non dipenda dai fotogrammi.
3. ⭐⭐ **E la cura NON è «copiare quel meccanismo» come l'abbiamo inteso il 14 agosto.** Il client
   di xrdp **non disegna** il puntatore: prende la forma ricevuta e la **installa come icona del
   cursore di sistema** (`[M]` `nm -D /usr/bin/xfreerdp3` → `XcursorImageLoadCursor` +
   `XDefineCursor`). ⇒ **La trasposizione giusta nel browser è `cursor: url(...) hx hy`, non
   `cursor: none` + una freccia disegnata sulla tela.** È la strada che nessun rapporto di questa
   fase ha mai considerato, e che **non può ricadere nella regressione di §5**.

> ## ⭐⭐⭐ LA RIGA CHE CAMBIA IL PRODOTTO
>
> **`[R]` Chromium, `ui/android/java/src/org/chromium/ui/base/ViewAndroidDelegate.java:316-321`:**
> ```java
> public void onCursorChangedToCustom(Bitmap customCursorBitmap, int hotspotX, int hotspotY) {
>     ViewGroup containerView = getContainerViewGroup();
>     if (containerView == null) return;
>     PointerIcon icon = PointerIcon.create(customCursorBitmap, hotspotX, hotspotY);
>     containerView.setPointerIcon(icon);
> }
> ```
> **`cursor: url(...) hx hy` su Android diventa `PointerIcon.create(bitmap, hotspot)` — cioè un
> puntatore di SISTEMA con la nostra forma.** Il DeX continua a muoverlo lui, alla velocità della
> mano, senza un fotogramma, senza un salto di rete, **e senza nasconderlo mai**.
>
> **E dieci righe più sotto, la `[?]` di §5 del punto-di-ripresa diventa `[R]`:**
> `ViewAndroidDelegate.java:329-331` — `CursorType.NONE` → `PointerIcon.TYPE_NULL`.
> ⇒ **`cursor: none` è letteralmente `PointerIcon.TYPE_NULL`**: l'ipotesi scritta a mano il 14
> agosto era giusta, ed è ora letta nella fonte.
>
> Vincolo di misura: `[R]` `third_party/blink/renderer/core/input/event_handler.cc:263`
> `kMaximumCursorSizeWithoutFallback = 32` ⇒ **la forma va tenuta a 32×32 px CSS o meno**, altrimenti
> Blink la lascia cadere quando non è tutta dentro il visual viewport (`event_handler.cc:729-756`).
> ⭐ È esattamente la misura classica del cursore RDP.

---

## 0 · Che cosa ho letto e che cosa ho misurato

| | |
|---|---|
| sorgente xrdp | `/tmp/studio-input/xrdp/xrdp`, tag **v0.10.1**, commit `1c33f3d9af22cac303803a4132a6b1aea5ebf1ce` |
| sorgente xorgxrdp | `/tmp/studio-input/xrdp/xorgxrdp`, tag **v0.10.2**, commit `fb49d67b6c94217cb64020986c983abe52ce06f2` |
| controllo su `devel` | xrdp `origin/devel` commit `a02ed627` (solo per la verifica del §1) |
| binari installati | `xrdp 0.10.1-3.1+deb13u1`, `xorgxrdp 1:0.10.2-1`, `freerdp3-x11 3.15.0+dfsg-2.1+deb13u3` |
| Chromium | ramo `main`, file scaricati da `raw.githubusercontent.com/chromium/chromium/main` il **14 agosto 2026** |
| banco di misura | display X privato **`:91`** (Xvfb 1600×900), client `xfreerdp3` → `127.0.0.1:3389` |
| ⛔ risorse | **nessuna porta di ascolto occupata da me**; nessun servizio fermato o riavviato; `xrdp` e `xrdp-sesman` verificati `active` prima e dopo. Nessuna scrittura fuori da `/tmp/studio-input/xrdp/` e dallo scratchpad |

⚠ **Il limite della misura, dichiarato subito**: non ho le credenziali dell'utente e **non le ho
chieste né indovinate**. La sessione RDP che ho aperto si ferma alla **finestra di accesso di
xrdp**, disegnata dal gestore di finestre interno di xrdp (`xrdp_wm.c`) e **non da xorgxrdp**. ⇒ Le
misure di byte valgono per il **protocollo RDP** (libxrdp, comune a tutti i moduli) e **non**
provano il comportamento di `xorgxrdp` sul filo; quel pezzo è `[R]`, letto nel codice.

---

## ⭐ Le misure `[M]` — 14 agosto 2026, CHUWI

Socket misurato con `ss -tin` sui contatori del nucleo (`bytes_sent` = client→server,
`bytes_received` = server→client), presa `127.0.0.1:50818 → 127.0.0.1:3389`.
Schermo remoto: **la finestra di accesso di xrdp, immobile** (verificata con una schermata).

| prova | client → server | **server → client** |
|---|---|---|
| **10 s fermo**, nessun movimento (controllo) | 0 B | **0 B** |
| ⭐⭐ **200 movimenti in 10 s sullo sfondo** (nessun cambio di forma) | 6.400 B (**32 B/movimento**) | ⭐⭐ **0 B — ZERO** |
| 100 movimenti **dentro** lo stesso campo di testo | 3.200 B | **31 B** (un solo cambio di forma, all'ingresso) |
| ⭐ **80 cambi di forma** (40 andate/ritorni sfondo ↔ campo) | 2.560 B | **2.480 B = 31 B per cambio di forma** |
| ⭐ **500 movimenti in 30 ms** (≈16.600 eventi/s) | 16.000 B (**32 B ciascuno**) | — |

**Che cosa provano, una per una:**

- ⭐⭐ **Riga 2 — il cuore**: il puntatore si muove sul vetro del client e il server **non manda un
  solo byte**. Non un fotogramma, non un PDU di posizione, **niente**. Il costo di rete del
  movimento del mouse, in discesa, è **esattamente zero**.
- ⭐ **Riga 4 — la cache funziona**: 31 byte per cambio di forma, costante su 80 cambi ⇒ sono tutti
  colpi di **cache** (`TS_FP_CACHEDPOINTERATTRIBUTE`: 5 byte utili + intestazione fastpath + ~22
  byte di TLS 1.3). La forma vera si paga **una volta sola per forma**.
- ⭐ **Riga 5 — nessun accorpamento in salita**: 500 movimenti in 30 ms, **32 byte ciascuno, tutti
  spediti**. Il client non ne fonde nessuno e il server non ne rifiuta nessuno. `[S]` Il carico
  utile fastpath di un evento mouse è 9 byte (`eventHeader` 1 + `pointerFlags` 2 + `xPos` 2 +
  `yPos` 2 + intestazione fastpath 2): i 32 misurati sono 9 utili + ~22 di TLS. ⇒ **Il costo di un
  movimento è la busta, non la lettera.**

**`[M]` La prova del meccanismo, dal binario installato** — `nm -D` su `/usr/bin/xfreerdp3`:
```
U XCreateFontCursor      U XcursorImageLoadCursor   U XDefineCursor
U XFreeCursor            U XUndefineCursor          U XWarpPointer
```
⇒ Il client di xrdp **non dipinge il puntatore in nessun buffer**: costruisce un cursore X dalla
forma ricevuta (`XcursorImageLoadCursor`) e lo **appiccica alla finestra** (`XDefineCursor`). Da
quel momento **è il server X locale a muoverlo**, esattamente come farebbe Android col
`PointerIcon`.

---

## 1 · Quando il mouse si muove e sullo schermo non cambia niente, che cosa viaggia sul filo?

**In salita: 32 byte per movimento (9 utili). In discesa: NIENTE.** `[M]` (tabella sopra).

### 1.1 Il Pointer Position Update esiste nella specifica e **non esiste in xrdp**

`[S]` MS-RDPBCGR §2.2.9.1.1.4.2 definisce il *Pointer Position Update PDU*: il server **può**
dire al client dove sta il puntatore.

`[R]` xrdp lo **conosce e non lo usa mai**:

| costante | dove | utilizzi in tutto l'albero `.c`/`.h` |
|---|---|---|
| `RDP_POINTER_MOVE 3` (`TS_PTRMSGTYPE_POSITION`) | `common/ms-rdpbcgr.h:547` | **0** |
| `FASTPATH_UPDATETYPE_PTR_POSITION 0x8` | `common/ms-rdpbcgr.h:572` | **0** |
| `RDP_POINTER_SYSTEM 1` | `common/ms-rdpbcgr.h:546` | **0** |
| `FASTPATH_UPDATETYPE_PTR_NULL 0x5` / `PTR_DEFAULT 0x6` | `common/ms-rdpbcgr.h:570-571` | **0** |

⛔ **Certificazione dello strumento** (regola §8 del briefing). La stessa ricerca, sullo stesso
albero, trova **usate** le sorelle di quelle costanti: `FASTPATH_UPDATETYPE_COLOR`
(`libxrdp/libxrdp.c:863`), `FASTPATH_UPDATETYPE_POINTER` (`:881`), `FASTPATH_UPDATETYPE_CACHED`
(`:954`), `RDP_POINTER_COLOR` (`:776`), `RDP_POINTER_POINTER` (`:784`), `RDP_POINTER_CACHED`
(`:939`). ⇒ La ricerca guarda nel posto giusto: l'assenza è **vera**, non un artefatto.

⭐ **Seconda verifica, per letterale e non per nome**: enumerate **tutte e 9** le chiamate
`xrdp_rdp_send_fastpath()` dell'albero (`xrdp_rdp.c:905`, `xrdp_orders.c:161`, `:201`,
`libxrdp.c:344`, `:862`, `:880`, `:953`, `:1712`, `:1753`) — nessuna passa `0x8`; e **tutte e 2**
le `xrdp_rdp_send_data(..., RDP_DATA_PDU_POINTER)` (`libxrdp.c:912`, `:966`) — i soli `messageType`
scritti nello stream sono `6`, `8` e `7` (colore, nuovo, in cache). **Nessun `3`.**

⭐ **Terza verifica, sul ramo di sviluppo**: su `origin/devel` (`a02ed627`, agosto 2026) la ricerca
trova **una sola riga**, `common/ms-rdpbcgr.h:578` `#define FASTPATH_UPDATETYPE_PTR_POSITION 0x8`:
`RDP_POINTER_MOVE` **è stato addirittura rimosso**. ⇒ Non è una svista di una versione: xrdp non ha
**mai** avuto intenzione di mandare la posizione.

### 1.2 E xorgxrdp non se ne accorge nemmeno

`[R]` `xorgxrdp/module/rdpCursor.c:411-416`, **corpo integrale**:
```c
void
rdpSpriteMoveCursor(DeviceIntPtr pDev, ScreenPtr pScr, int x, int y)
{
    LLOGLN(10, ("rdpSpriteMoveCursor:"));
}
```
La macro è compilata via (`LOG_LEVEL 1` a `rdpCursor.c:100`, la guardia è `10 < 1`). ⇒ **Muovere
il puntatore nel server X non scrive nel framebuffer, non sporca niente, non manda niente.**

⭐ **La distinzione che il mandato chiedeva è risolta nel senso più forte:** xrdp **non rimanda mai
al client la posizione che il client gli ha appena mandato**. Non c'è nessun giro di rete e nessun
puntatore «indietro». ⇒ **Il puntatore lo muove il client da solo, a costo zero.** È la cosa che ci
serve, e c'è.

### 1.3 ⭐⭐ Il colpo di scena: xrdp è a **0 fotogrammi al secondo**, non a 60

`[R]` Con lo schermo fermo, xorgxrdp non manda niente — **tre guardie in cascata**:

| guardia | dove | che cosa fa |
|---|---|---|
| regione sporca vuota | `module/rdpClientCon.c:2857` `if (num_rects > 0)` | non cattura e non spedisce |
| niente da spedire | `module/rdpClientCon.c:2631-2635` | `return 0`, «nothing to send» |
| pixel identici (RFX/GFX) | `module/rdpCapture.c:966-972` | la tile 64×64 con lo stesso CRC viene **tolta** dall'invio |

E il timer **non gira a vuoto**: `[R]` `module/rdpClientCon.c:2982-3013` `rdpScheduleDeferredUpdate()`
è **one-shot** con guardia `if (clientCon->updateScheduled) return;` (`:2988`), e si riarma alla
fine solo se resta roba sporca — `[R]` `rdpClientCon.c:2970-2973`:
```c
if (rdpRegionNotEmpty(clientCon->dirtyRegion)) { rdpScheduleDeferredUpdate(clientCon); }
```
⇒ **Scena ferma = nessun timer attivo, zero tick, zero byte.** Il risveglio arriva dal `damage`
(`xrdpdev/xrdpdev.c:444-450`, `DamageReportRawRegion`) o dall'ack del client
(`rdpClientCon.c:1263`, `:1287`).

⭐⭐ **Conseguenza per noi, ed è la parte che ribalta la diagnosi del 14 agosto.** `figlio.c` e
`mutter.c:503` fanno **la stessa identica cosa** di xorgxrdp: fotogramma solo quando cambia
qualcosa, cursore fuori dall'immagine. **Non c'è niente di sbagliato in quelle due scelte**: sono
esattamente il progetto di un server RDP maturo, e xrdp le porta più in là di noi (0 fps contro
1,1). Il difetto di REMOTIX **non è che il desktop sia fermo**: è che **il puntatore è agganciato ai
fotogrammi**, e su xrdp non lo è.

---

## 2 · Chi disegna il puntatore, e che cosa succede quando la forma cambia

**Lo disegna il sistema operativo del client, con una forma che gli passa il client RDP.** Tre
anelli:

**(a) xorgxrdp intercetta la forma, non la posizione.** `[R]` `xrdpdev/xrdpdev.c:369-378` installa
`miPointerSpriteFuncRec` proprie (`rdpSpriteRealizeCursor`, `rdpSpriteSetCursor`,
`rdpSpriteMoveCursor`, …). ⭐ La prova che il cursore **non finisce nell'immagine catturata**:
`[R]` `xrdpdev/xrdpdev.c:734-743` sceglie il ramo «hardware cursor» e il ramo `miDCInitialize`
(*mi Damage Cursor*, il cursore software, quello che **dipingerebbe** nel framebuffer) sta
nell'`#else` ed è **codice morto**; e `[R]` `module/rdpCursor.c:105-118` — `rdpSpriteRealizeCursor`
e `rdpSpriteUnrealizeCursor` fanno solo `return TRUE`, `rdpSpriteSetCursorCon`
(`rdpCursor.c:228-391`) scrive in un buffer temporaneo allocato a `:265` e liberato a `:390`, **mai
in `dev->pfbMemory`** (che è quello catturato, `rdpClientCon.c:3044`).

⭐ **È esattamente la nostra `cursor-mode: CURSORE_METADATO` di `mutter.c:503`.** La scelta che il
punto-di-ripresa considera «metà del difetto» è **la stessa scelta di xorgxrdp**, e lì non fa
danno.

**(b) La forma viaggia da sola.** `[R]` `module/rdpCursor.c:377-389`: 32×32 classico, oppure fino a
**96×96** se il client dichiara `LARGE_POINTER_FLAG_96x96` (`rdpCursor.c:276-277`); ARGB 32 bpp se
il cursore X ha `bits->argb` e il client sa fare il puntatore «nuovo» (`:293-299`), altrimenti
mono source+mask; righe ribaltate perché RDP vuole il bottom-up (`:332`, `:360`, `:369`).

**(c) xrdp lo impacchetta in una delle tre forme di PDU** (`[R]` `libxrdp/libxrdp.c`):

| PDU | quando | dove |
|---|---|---|
| `TS_COLORPOINTERATTRIBUTE` (`RDP_POINTER_COLOR`) | client **senza** «new cursors» (solo 24 bpp) | `libxrdp.c:776`, guardia `:734-742` |
| `TS_POINTERATTRIBUTE` (`RDP_POINTER_POINTER`, «New Pointer») | client con `pointer_flags & 1` — porta `xorBpp` | `libxrdp.c:784`, `:790` |
| `TS_CACHEDPOINTERATTRIBUTE` (`RDP_POINTER_CACHED`) | forma **già vista**: manda solo l'indice | `libxrdp.c:939`, `:946` |
| `TS_SYSTEMPOINTERATTRIBUTE` | ⛔ **mai** (`RDP_POINTER_SYSTEM` ha 0 utilizzi) | — |

Nel nostro `/etc/xrdp/xrdp.ini` è attivo `new_cursors=true` e `use_fastpath=both` ⇒ in vigore la
via fastpath, `FASTPATH_UPDATETYPE_POINTER` / `..._CACHED`.

### ⭐ La cache dei cursori: a che serve e quanto è grande

`[R]` **32 slot allocati** (`xrdp/xrdp_types.h:322` `struct xrdp_pointer_item pointer_items[32];`),
ma il limite in vigore è **`min(quel che dichiara il client, 32)`** —
`libxrdp/xrdp_caps.c:385-387` e `:392-394` (`i = MIN(i, 32)`), letto dalla capability
`CAPSTYPE_POINTER` del client. Il server, dal canto suo, dichiara **25** (`0x19`,
`libxrdp/xrdp_caps.c:1256-1257`).

Politica (`[R]` `xrdp/xrdp_cache.c:602-670`):
1. `pointer_stamp++` (`:614`);
2. **cerca una forma identica** confrontando hotspot, `data` e `mask` byte a byte (`:617-635`): se
   la trova, manda **solo l'indice** (`xrdp_wm_set_pointer`, `:630`) — ⭐ **i 31 byte che ho
   misurato**;
3. altrimenti **LRU** sullo stamp più vecchio a partire da `i = 2` (`:640-649`) e manda la forma
   intera (`:660`).

⛔ **Gli indici 0 e 1 sono riservati** ai due cursori statici della finestra di accesso
(`xrdp/xrdp_wm.c:616` e `:622`, via `xrdp_cache_add_pointer_static`, `xrdp_cache.c:676`).

⭐ **A che serve, in una riga:** a rendere il cambio di forma **31 byte invece di 4 KB**. Con 25-30
forme in cache, un desktop intero (freccia, I-beam, mani, ridimensionamenti, attesa) sta tutto
dentro e **dopo il primo giro non si paga più nessuna forma**. `[M]` Confermato: 80 cambi di forma
di fila, tutti a 31 byte.

⚠ Difettuccio letto di passaggio, non nostro: `xrdp_cache_add_pointer_static`
(`xrdp/xrdp_cache.c:676`) **non copia `width`/`height`** (a differenza di `xrdp_cache_add_pointer`,
`:657-659`) ma li usa a `:696-697`.

---

## 3 · Il client chiede la misura del desktop al server?

**Sì, due volte, e xrdp gliela dà — non impagina MAI.** È il sesto progetto su sei a fare così.

**(a) All'aggancio**: `TS_UD_CS_CORE.desktopWidth/desktopHeight` e, per il multi-monitor,
`TS_UD_CS_MONITOR` (`[R]` `libxrdp/xrdp_sec.c:2239` → `libxrdp_process_monitor_stream(s, desc, 0)`).

**(b) A caldo**: ⭐ **il canale `Display Control` (MS-RDPEDISP) è attuato per intero.**

| pezzo | dove |
|---|---|
| apertura del canale dinamico | `xrdp/xrdp_mm.c:1992-2016` `dynamic_monitor_initialize()` |
| il server manda `DISPLAYCONTROL_PDU_TYPE_CAPS` (5) all'apertura | `xrdp/xrdp_mm.c:1147` |
| arrivo del `MONITOR_LAYOUT` dal client | `xrdp/xrdp_mm.c:1537-1625` `dynamic_monitor_data()` |
| coda + macchina a stati | `xrdp/xrdp_mm.c:1619` `list_add_item(wm->mm->resize_queue, …)`, `:1873` |

`[M]` **Verificato sul filo**: il registro di `xfreerdp3` mostra il canale
`{Microsoft::Windows::RDS::DisplayControl:2}` aperto durante il mio aggancio.

### Con quali unità

`[R]` `libxrdp/libxrdp.c:2004-2025` — il `DISPLAYCONTROL_MONITOR_LAYOUT` porta:
**`Width` e `Height` in PIXEL DEL DISPOSITIVO**, più `PhysicalWidth`/`PhysicalHeight` **in
millimetri**, `Orientation` in gradi, `DesktopScaleFactor` (percentuale 100-500) e
`DeviceScaleFactor` (solo 100, 140 o 180).

⭐⭐ **E adesso la cosa che ci riguarda di più**: `DesktopScaleFactor` e `DeviceScaleFactor` sono
letti (`libxrdp.c:2024-2025`), validati (`:1849-1876`), salvati e copiati (`:2154-2155`)… e
**mai usati per moltiplicare niente**. ⛔ Certificazione: la ricerca `desktop_scale_factor` su tutto
l'albero (escluse le prove) restituisce **solo** parsing, validazione e copia — **zero consumatori**.
⇒ **xrdp ignora completamente il DPI: il desktop ha esattamente i pixel che il client chiede, 1:1.**

⚠ **Per REMOTIX questo è un avvertimento diretto**: sul DeX abbiamo `devicePixelRatio` **1,2**. Il
mondo RDP dice: **manda i pixel veri e basta**, non mandare una misura logica e non farti scalare
da nessuno.

### Che cosa fa il server quando non può accontentare

**Rifiuta, non arrotonda.** `[R]` `libxrdp/libxrdp.c:1993-2019`:

| condizione | esito |
|---|---|
| `width > 8192` o `width < 200` o ⭐ **`width % 2 != 0`** | `SEC_PROCESS_MONITORS_ERR_INVALID_MONITOR` — **tutto il PDU cade** |
| `height > 8192` o `height < 200` | idem |
| `monitor_layout_size != 40` | errore (`xrdp_mm.c:1594-1602`) |
| misura già in vigore | ignorato in silenzio (`xrdp_mm.c:1917-1929` `already_this_size`) |
| accesso in corso | ignorato (`xrdp/xrdp_wm.c:2423-2434` `xrdp_wm_can_resize()`) |
| output soppresso dal client | ignorato (`xrdp_mm.c:1553-1559`) |

⭐ **Da rubare subito, e costa una riga**: **la larghezza deve essere PARI**. Se un giorno chiediamo
a Mutter la misura del client (strada §5.1), la vista DeX `2560×926` va bene, ma una `2133` no.
Arrotondare **noi**, in giù, al pari.

Lato X, il ridimensionamento vero: `[R]` `xorgxrdp/module/rdpRandR.c:118-210` `rdpRRScreenSetSize()`
— rialloca il framebuffer (`:156-162`), reinizializza le regioni della root (`:188-198`),
`RRScreenSizeNotify` (`:199-201`). ⭐ **Non esiste nessuna tabella di modi video predefiniti**: il
modo è **fabbricato al volo** dalla misura chiesta (`rdpRandR.c:411-461`, nome `"1920x1080"`,
50 Hz nominali, `dotClock = 50 * w * h`), e `rdpRROutputValidateMode` **accetta sempre**
(`:249-255`). Limiti globali `256×256` … `16384×16384` (`xrdpdev/xrdpdev.c:536`). Un `xrandr`
lanciato dentro la sessione viene **respinto** (`rdpRandR.c:130-140`, `allow_screen_resize == 0`):
la misura la comanda **solo** il client RDP.

### ⛔ E quanto costa il ridimensionamento

`[R]` `xrdp/xrdp_mm.c:1675-1868` — **una macchina a 14 stati**: sopprimi l'output → **distruggi il
codificatore** → smonta la superficie eGFX → chiudi il canale eGFX → ridimensiona il monitor sul
modulo → `libxrdp_reset` → **azzera tutte le cache** (`xrdp_cache_reset`, `:1783`) → ricarica colori
e puntatori statici → ridimensiona la finestra → riapri eGFX → **ricrea il codificatore** →
invalida tutto lo schermo → riattiva l'output.

⇒ **Non è un'operazione da fare a ogni sussulto della finestra.** Se prendiamo la strada §5.1, il
ridimensionamento va **strozzato** (xrdp lo strozza con la coda `resize_queue` e la guardia
`already_this_size`), non attaccato a `resize` del browser.

---

## 4 · Quanti stadi ha la conversione delle coordinate, e dove vive l'offset

**Uno solo lato client, ZERO lato server — e nessun offset da nessuna parte.**

- **Lato server, xrdp**: nessuna conversione. `[R]` `xrdp/xrdp_wm.c:1143-1200` prende `x, y` dal PDU,
  li **limita** ai bordi (`:1152-1170`) e li passa **tali e quali** al modulo (`:1200`).
- **Lato server, xorgxrdp**: nessuna conversione. `[R]` `xrdpmouse/rdpMouse.c:203-209` — le
  coordinate sono **assolute in pixel del desktop**, solo limitate a `[0, w-2] × [0, h-2]` (con un
  commento che spiega il `-2`: «senza, succedono cose strane quando si trascina oltre la larghezza»).
  Poi `[R]` `rdpMouse.c:100-106` `xf86PostMotionEvent(device, TRUE, 0, 2, x, y)` — quel `TRUE` è
  **`is_absolute`**.
- **Lato client**: un solo passaggio, da pixel della finestra a pixel del desktop; e siccome il
  desktop **è** della misura della finestra (§3), nel caso normale è l'**identità**.

⭐⭐ **Sono sei progetti su sei.** `F4-AND-4` ne aveva contati cinque con **uno** stadio; xrdp è il
sesto, e ne ha **meno di uno**. ⛔ Noi ne abbiamo **tre** (vetro→tela, bande dentro la tela,
tela→desktop) e **due offset** (`bx0`, `by0`) che nessun altro ha, perché nessun altro impagina.

⚠ **La banda nera non è un dettaglio estetico: è il generatore di stadi.** Togliere le bande
(strada §5.1) non toglie «il 36 % di pixel neri»: toglie **due stadi su tre e tutti gli offset**.

---

## 5 · Come si misura e come si limita la latenza dell'input

### In ingresso: **nessun limite, nessun accorpamento, nessuno scarto**

`[R]` La catena completa, dal PDU alla `write()`, **senza un solo punto di accodamento**:

| # | dove | che cosa |
|---|---|---|
| 1 | `libxrdp/xrdp_rdp.c:469` | `if (header[0] != 0x3)` → fastpath. ⭐ La scelta è **per pacchetto**, a runtime |
| 2 | `libxrdp/xrdp_fastpath.c:342` | `for (i = 0; i < self->numEvents; i++)` — **tutti**, nessun filtro |
| 3 | `libxrdp/xrdp_fastpath.c:204-228` | legge `pointerFlags`/`xPos`/`yPos`, richiama subito |
| 4 | `xrdp/xrdp_wm.c:2023-2024` → `:1794-1797` | smista `PTRFLAGS_MOVE` |
| 5 | ⭐ `xrdp/xrdp_wm.c:1200` | `mod_event(mod, WM_MOUSEMOVE, x, y, 0, 0)` — **incondizionata**, nessun confronto con la posizione precedente |
| 6 | `xup/xup.c:311-323` | costruisce il messaggio 103 e `lib_send_copy` |
| 7 | `common/trans.c:624` | `trans_send(...)` — **`write()` immediata** |

⚠ E in un caso xrdp manda **più** eventi del client, non meno: `xrdp/xrdp_wm.c:1364` emette un
`WM_MOUSEMOVE` in più prima di un tasto premuto.

L'unico scarto sta **in fondo**, in xorgxrdp: `[R]` `xrdpmouse/rdpMouse.c:126-132` — se la posizione
è **identica** all'ultima, non inietta l'evento di moto. È deduplicazione, **non** accorpamento
temporale: non c'è nessun timer, nessuna coda, nessun ritardo.

⭐ `[M]` **Confermato sul ferro**: 500 movimenti in 30 ms, tutti spediti, 32 byte l'uno.

`use_fastpath` in `/etc/xrdp/xrdp.ini` è **`both`** ⇒ bit 1 (uscita) + bit 2 (ingresso), negoziati
con le capability del client (`[R]` `libxrdp/xrdp_caps.c:114-119` per l'uscita, `:412-425` per
l'ingresso). Lo slowpath (`xrdp_rdp.c:992` `xrdp_rdp_process_data_input`) resta vivo in parallelo:
è il byte 0x03 a decidere.

### In uscita: **nessun limite in fotogrammi/secondo, un credito ad ack**

⛔ **Non esiste nessun cap temporale in xrdp.** Ricerca su `xrdp_encoder.c` e `xrdp_mm.c` per
`fps|frame_rate|framerate|g_sleep`: unico riscontro `xrdp_encoder.c:1187` `g_sleep(100)`, che è un
errore di attesa. `MAX_QUEUED_FRAMES` **non esiste**.

Il controllo è **a credito**:

| | |
|---|---|
| eGFX, per difetto | **2 fotogrammi in volo** (`[R]` `xrdp/xrdp_encoder.c:37`, `:248`), con `XRDP_GFX_FRAMES_IN_FLIGHT` fra 1 e 16 (`:39-40`, `:246-255`) |
| non-eGFX | **lo dice il client**: `max_unacknowledged_frame_count` (`[R]` `libxrdp/xrdp_caps.c:695-696`, usato a `xrdp_encoder.c:290`) |
| il cancello | `[R]` `xrdp/xrdp_mm.c:1420-1428`: `if (frame_id_client + fif > frame_id_server) mod_frame_ack(...)` |

⭐⭐ **E qui c'è la cosa più elegante di xrdp**: se il client non manda l'ack, xrdp **non accoda e
non scarta** — **smette di dare l'ack a xorgxrdp**, e xorgxrdp **smette di produrre**
(`[R]` `xorgxrdp/module/rdpClientCon.c:2914-2919`: se `rect_id > rect_id_ack` la callback esce
subito). **La contropressione risale fino al server X.** Nessun fotogramma vecchio esiste mai.

Il cap temporale, l'unico, sta in xorgxrdp: `[R]` `module/rdpClientCon.c:2978-2980`
```c
#define MIN_MS_BETWEEN_FRAMES 40            /* = 25 fotogrammi al secondo */
#define MIN_MS_TO_WAIT_FOR_MORE_UPDATES 4   /* attesa breve per accorpare il damage */
```
⭐ **25 fps, non 60** — e con un'attesa di soli **4 ms** per accorpare altri danni, non 40. ⇒ La
latenza aggiunta dall'accorpamento è **4 ms**, non un periodo di fotogramma.

### `Suppress Output`

`[R]` `libxrdp/xrdp_rdp.c:1436-1455` — è una **maschera di ragioni** (`XSO_REASON_CLIENT_REQUEST`,
`_DEACTIVATE_REACTIVATE`, `_DYNAMIC_RESIZE`, `libxrdp/libxrdp.h:410-418`), non un booleano; notifica
il modulo **solo se lo stato aggregato cambia** (`:1450-1455`). xrdp **non filtra localmente**:
gira l'ordine a xorgxrdp (opcode 108, `xup/xup.c:1090-1109`) che smette di generare
(`rdpClientCon.c:2901-2905`). ⭐ Il caso d'uso: finestra del client **minimizzata**.

⚠ Difetto letto di passaggio, **non nostro**: `xrdp/xrdp_wm.c:2049-2052`, al `case 0x5559` manca il
`break;` e cade nel `case 0x555a` eseguendo anche `xrdp_mm_up_and_running()`. Fall-through non
commentato.

---

## 6 · Che cosa c'è di specifico per Android, per il tocco e per DeX

⛔ **In xrdp: NIENTE, e non poteva essercene.** xrdp è un server; il client non lo scrive lui.
Ricerca `android|touch|gesture|dex` su tutto l'albero: nessun riscontro pertinente. La domanda **non
si applica al bersaglio**.

⭐ **Ma il meccanismo di xrdp mi ha portato dritto alla risposta, che sta in Chromium.** Poiché il
mestiere del client di xrdp è «prendi la forma, dalla al cursore di sistema», ho letto **come lo
farebbe il nostro client**, che è una pagina web su Chrome per Android:

`[R]` Chromium ramo `main`, letto il 14 agosto 2026:

| passo | file:riga | che cosa |
|---|---|---|
| Blink decide il cursore | `third_party/blink/renderer/core/input/event_handler.cc:263` | `kMaximumCursorSizeWithoutFallback = 32` |
| … e lo lascia cadere se troppo grande e non contenuto | `event_handler.cc:729-756` | sopra 32 px CSS, se il rettangolo del cursore non sta **tutto** nel visual viewport, si passa oltre |
| il browser lo passa alla vista Android | `content/browser/renderer_host/render_widget_host_view_android.cc:1374-1378` | `UpdateCursor` → `view_.OnCursorChanged(cursor)` |
| forma personalizzata → bitmap + hotspot | `ui/android/view_android.cc:475-485` | `kCustom` → `Java_ViewAndroidDelegate_onCursorChangedToCustom(env, delegate, bitmap, hotspot.x(), hotspot.y())` |
| ⭐⭐ e in Java diventa un **puntatore di sistema** | `ui/android/java/src/org/chromium/ui/base/ViewAndroidDelegate.java:316-321` | `PointerIcon.create(bitmap, hotspotX, hotspotY)` → `containerView.setPointerIcon(icon)` |
| ⭐ e `cursor: none` diventa… | `ViewAndroidDelegate.java:329-331` | `CursorType.NONE` → **`PointerIcon.TYPE_NULL`** |

⭐⭐ **Due conclusioni, e sono le più importanti del rapporto.**

**(1) La `[?]` di §5 del punto-di-ripresa è ora `[R]`.** L'ipotesi scritta a mano
(«nascondere l'icona del puntatore = `PointerIcon.TYPE_NULL`») **è letteralmente il codice**. La
regressione delle 15:09 — `[M]` 4 clic e **zero movimenti** — ha finalmente un meccanismo:
`cursor: none` sulla tela ⇒ `setPointerIcon(TYPE_NULL)` sulla `ViewGroup` di Chrome.
⚠ Resta `[?]` **solo** l'ultimo anello: che `TYPE_NULL` porti via anche gli eventi di passaggio del
DeX. Ma non serve più deciderlo, perché —

**(2) …con `cursor: url()` la domanda non si pone.** Il puntatore **resta un puntatore di sistema
vero**, con tutti i suoi eventi; cambia **solo la sua immagine**. È lo stesso identico gesto che
`xfreerdp3` fa con `XDefineCursor`. ⇒ **La strada «disegniamo noi il puntatore» era preclusa; la
strada «prestiamo la nostra forma al puntatore di sistema» non lo è, e nessun rapporto di questa
fase l'aveva considerata.**

⛔ **Certificazione**: ricerca `PointerIcon|cursor: *url|cursor: *none` su **tutti** i rapporti
`F4-*.md`. Riscontri: solo `cursor: none` (F4-A7:64, F4-A7:239, F4-DEX:87, F4-DEX:94) e
`PointerIcon.TYPE_NULL` in F4-DEX:100. **`cursor: url` non compare in nessun rapporto.** La ricerca
funziona (20 occorrenze di «puntatore» in `F4-AND-1`): l'assenza è vera.

---

## 7 · Che cosa ruberei per REMOTIX, e che cosa NON ruberei

### ⭐⭐ Da rubare — in ordine di forza

| # | che cosa | fonte | costo | guadagno |
|---|---|---|---|---|
| **1** | ⭐⭐ **La forma del cursore al puntatore di SISTEMA, via `cursor: url(dati) hx hy`** — mai `cursor: none`, mai una freccia disegnata | `[M]` `nm -D xfreerdp3`; `[R]` `ViewAndroidDelegate.java:316-321` | una regola CSS impostata da JS + il cursore che già riceviamo come metadato da Mutter | **puntatore alla velocità della mano, zero fotogrammi, zero rete, e nessuna possibilità di ricadere nella regressione di §5** |
| **2** | ⭐ **La cache delle forme, con confronto byte a byte e LRU** | `[R]` `xrdp/xrdp_cache.c:617-649`; `[M]` 31 B per cambio | ~40 righe: una mappa forma→`data:` URL già costruito | dopo il primo giro, cambiare forma costa **zero rete e zero costruzione di immagine** |
| **3** | **La larghezza PARI e i limiti 200…8192** sulla misura chiesta al server | `[R]` `libxrdp/libxrdp.c:1993-2019` | una riga di arrotondamento | evita un rifiuto silenzioso quando prenderemo la strada §5.1 |
| **4** | **Ignorare il DPI: mandare i pixel veri, 1:1** | `[R]` scale factor letti e mai usati, `libxrdp.c:1849-1876` | niente (è una **rinuncia**) | toglie di mezzo il `devicePixelRatio` **1,2** del DeX, che oggi è un moltiplicatore in mezzo alla catena |
| **5** | **La contropressione ad ack invece della coda**: se il client non conferma, **fermare la sorgente**, non accodare né scartare | `[R]` `xrdp/xrdp_mm.c:1420-1428` + `rdpClientCon.c:2914-2919` | medio | nessun fotogramma vecchio esiste mai ⇒ niente «giro completo» inquinato |
| **6** | **La coda di ridimensionamento con `already_this_size`** | `[R]` `xrdp/xrdp_mm.c:1889-1949` | piccolo | il ridimensionamento è **carissimo** (14 stati): va strozzato |
| **7** | **4 ms di attesa per accorpare il damage** (non un periodo di fotogramma) | `[R]` `rdpClientCon.c:2979` | — | accorpa senza aggiungere latenza percepibile |

### ⛔ Da NON rubare

| che cosa | perché |
|---|---|
| **Il PDU di posizione del puntatore** (§2.2.9.1.1.4.2) | ⭐ **xrdp non lo usa, e ha ragione**: rimandare al client la posizione che il client ha appena mandato costa un giro di rete e fa vedere il puntatore **indietro**. Se un giorno ci servisse (un'applicazione remota che **sposta** il puntatore), sarà un caso raro da trattare a parte |
| **Il cursore dipinto dentro l'immagine** (strada §6.2 del punto-di-ripresa) | ⛔ **xorgxrdp fa il contrario** (`xrdpdev.c:734-743`, il cursore software è codice morto), e con la cura #1 il problema che quella strada risolveva **non esiste più**. Costerebbe un fotogramma per ogni movimento del mouse: il rimedio peggiore del male |
| **Forzare una cattura all'arrivo di un `PUNTATORE`** (l'altra metà di §6.2) | idem: dopo #1 non serve a niente, e ci farebbe codificare fotogrammi identici |
| **Il cap a 25 fps** | è un vincolo di xorgxrdp che sconta il RemoteFX su CPU; noi codifichiamo in hardware |
| **La macchina a 14 stati del ridimensionamento** | è complessità che nasce dal dover smontare eGFX e cache RDP: noi non abbiamo né l'uno né le altre |
| **La deduplicazione a `old_cursor_x/y`** (`rdpMouse.c:126-132`) | risparmia un evento X, non un byte di rete. `[M]` La nostra coda non si è **mai** riempita (sorpassi 0): non è il nostro problema |

---

## 8 · ⭐⭐ La refutazione del mandato

> **La frase da refutare**: «Con un puntatore disegnato dal client — RDP manda la forma e la
> posizione del cursore in PDU dedicate, indipendenti dagli aggiornamenti dello schermo — muovere il
> mouse non richiede nessun fotogramma nuovo. Quindi il difetto di REMOTIX su xrdp NON si presenta,
> e la cura è copiare quel meccanismo.»

Sono quattro affermazioni. **Due reggono, due cadono — e quelle che cadono sono le due che
comandano la cura.**

| # | affermazione | esito | prova |
|---|---|---|---|
| a | «RDP manda la forma **e la posizione** in PDU dedicate» | ⛔ **FALSA per xrdp** | `[S]` il PDU esiste nella specifica; `[R]` `ms-rdpbcgr.h:547` e `:572` sono `#define` con **zero utilizzi** (verificato per nome, per letterale e su `devel`); `[R]` `rdpCursor.c:411-416` corpo **vuoto**; `[M]` **0 byte** su 200 movimenti. **Viaggia solo la forma.** |
| b | «muovere il mouse non richiede nessun fotogramma nuovo» | ✅ **VERA, e più forte del previsto** | `[M]` 0 byte in discesa; `[R]` `rdpClientCon.c:2857`, `:2970-2973` — schermo fermo = **0 fps**, meno dei nostri 1,1 |
| c | «il difetto di REMOTIX su xrdp non si presenta» | ✅ **VERA — ma smentisce la nostra diagnosi** | xrdp ha **la stessa** cattura su cambiamento e **lo stesso** cursore fuori dall'immagine (`xrdpdev.c:734-743` ≡ `mutter.c:503`). ⇒ ⭐ **Le due «scelte che insieme fanno il difetto» sono innocenti**: sono il progetto standard. Il difetto è un **terzo** pezzo: che da noi il puntatore dipende dal fotogramma |
| d | ⭐⭐ «**la cura è copiare quel meccanismo**» | ⛔ **FALSA COME L'ABBIAMO INTESA** | il client di xrdp **non disegna niente**: `[M]` `XcursorImageLoadCursor` + `XDefineCursor` — **presta la forma al cursore del sistema operativo**. Copiare «il client disegna il puntatore» è **esattamente la cura provata alle 15:09**, quella che ha dato `[M]` **4 clic e zero movimenti** |

### ⭐ Che cosa resta in mano, ed è più di quanto chiedeva il mandato

Il mandato divideva il mondo in due: *o* il client disegna il puntatore *o* il server rimanda la
posizione. **xrdp sta in una terza casella che non era nell'elenco**, e il punto-di-ripresa non
l'aveva vista nemmeno lui (§5: «se è vera, la strada *disegniamo noi il puntatore* è preclusa e
resta solo la 6.1»):

| | chi lo muove | chi decide la forma | costo del movimento | rischio §5 |
|---|---|---|---|---|
| REMOTIX oggi | il fotogramma dal server | Mutter (metadato, buttato) | **un fotogramma** | — |
| la cura delle 15:09 | la pagina, su tela | la pagina | zero | ⛔ **fatale** (`cursor: none` = `TYPE_NULL`) |
| il PDU di posizione | il server | il server | un giro di rete | — |
| ⭐⭐ **xrdp** | **il sistema operativo del client** | **il server, come forma** | ⭐ **zero** | ✅ **nessuno: il puntatore non si nasconde mai** |

⇒ **La frase del mandato va riscritta così**, e questa è misurata:

> Con un puntatore che è **il puntatore di sistema del client**, a cui il server presta **solo la
> forma** (mai la posizione), muovere il mouse costa **zero byte in discesa e zero fotogrammi**.
> Il difetto di REMOTIX non si presenta perché **il puntatore è scollegato dai fotogrammi**, non
> perché arrivino più fotogrammi — anzi ne arrivano **meno** (0 contro 1,1). La cura è
> **`cursor: url(dati) hx hy` sulla tela, forma ≤ 32×32, con una cache delle forme; e mai
> `cursor: none`.**

⚠ E c'è una conseguenza sulla priorità delle strade aperte. La strada **§5.1** (chiedere a Mutter la
misura del client) resta giustissima e **guadagna** una motivazione nuova e più forte di quella
scritta finora — non «il 36 % di pixel neri», ma **due stadi di conversione e due offset che
spariscono** (§4). Ma **non è la cura del mouse**: sei progetti su sei non impaginano *e* hanno il
puntatore locale, e sono due cose indipendenti. ⭐ **La cura del mouse è la #1 della tabella §7, e
non richiede nessuna decisione dell'utente**: non cambia la forma del prodotto, cambia una regola
CSS.

---

## ⛔ Quel che questo rapporto NON dice

1. ⭐ **Non ho misurato una sessione xorgxrdp vera.** Non ho le credenziali dell'utente e **non le ho
   chieste né tentate**: la mia sessione RDP si è fermata alla **finestra di accesso**, disegnata da
   `xrdp_wm.c`. ⇒ Tutti i numeri `[M]` valgono per **libxrdp** (il livello RDP, comune a ogni
   modulo). Il comportamento di **xorgxrdp** — `rdpSpriteMoveCursor` vuoto, le tre guardie sullo
   schermo fermo, i 25 fps — è **`[R]`, letto nel codice, non misurato**.
2. **Non ho misurato il ridimensionamento dinamico.** `[R]` `xrdp_wm_can_resize()`
   (`xrdp/xrdp_wm.c:2423-2434`) restituisce 0 finché l'accesso è in corso ⇒ dalla finestra di
   accesso il canale Display Control è aperto ma **inerte**. Ho verificato `[M]` solo che il canale
   `{Microsoft::Windows::RDS::DisplayControl:2}` viene aperto.
3. **Non ho misurato la latenza.** Nessun numero di questo rapporto è un millisecondo di ritardo
   percepito. Senza una sessione vera non c'era niente su cui cronometrare.
4. ⚠ **Non ho provato `cursor: url()` sul DeX.** ⭐ **È la misura che vale di più adesso**, e va
   fatta prima di scrivere una riga: sul DeX vero, `#schermo { cursor: url(freccia.png) 4 4, auto }`
   — il puntatore prende la nostra forma? Continua a mandare `pointermove`? Il conteggio dei
   movimenti resta sui 165-320 delle sessioni buone, e **non** sui 4 della regressione?
5. **Non ho letto il sorgente di FreeRDP.** La prova che il client installa il cursore di sistema è
   `[M]` dai simboli dinamici del binario installato (`nm -D`), non `[R]` dal codice. È una prova
   forte ma indiretta: dice **quali chiamate X esistono nel binario**, non in quale ordine.
6. **Il codice Chromium è del ramo `main` di oggi**, non della versione di Chrome installata sul DeX
   dell'utente. La riga `PointerIcon.create(...)` è stabile da anni `[?]`, ma non l'ho verificato su
   una versione precisa.
7. **Non ho misurato quanto costa la prima forma** (quella non in cache): so `[M]` che quelle in
   cache costano 31 byte, non so quanto pesa una `TS_POINTERATTRIBUTE` ARGB 32×32 sul filo (`[S]`
   ~4 KB di calcolo, non misurati).
8. **`RemoteFX`, `eGFX` e il codificatore di xrdp non li ho studiati.** Il mandato era sull'input.
9. **Non ho verificato che `TYPE_NULL` tolga davvero gli eventi di passaggio su DeX.** So `[R]` che
   `cursor: none` **diventa** `TYPE_NULL`; l'ultimo anello resta `[?]`. Con la cura #1 la domanda
   diventa però irrilevante.
10. **Non ho toccato `src/`, non ho fatto commit, non ho fermato né riavviato niente.** `xrdp` e
    `xrdp-sesman` verificati `active` prima e dopo. Il display Xvfb `:91` e il client `xfreerdp3`
    sono stati chiusi a fine misura, verificato.
