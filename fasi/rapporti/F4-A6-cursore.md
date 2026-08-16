# F4-A6 — Il cursore: il canale adesso ha una sorgente

*14 agosto 2026. Anello **A6** della fase 4. File toccati: `src/cursore.c` (era un abbozzo di due
righe), `src/cattura.c`, `src/cattura.h` (una riga di interfaccia, §5), `banchi/04-b26-*`.*

---

## 1. Che cosa cambia per l'utente

**Il puntatore che la pagina disegna adesso ha la forma giusta**: freccia, barretta, mano — prima
il client non riceveva nessuna forma perché non ne arrivava nessuna dal compositore.

---

## 2. Serve una decisione di Nic?

**No.** Nessuna scelta è rimasta aperta. Due cose da **sapere**, non da decidere:

1. ⚠ **la prima forma può tardare** — su un flusso appena aperto Mutter manda solo la *posizione*
   finché la forma non **cambia** (§4.2). Fino ad allora il client tiene il puntatore che ha.
   Nel prodotto reale il primo passaggio sopra una finestra la fa arrivare;
2. ⚠ **sopra 256 si taglia** e si dichiara. Non è mai scattato `[?]` (§6).

---

## 3. Che cosa ho MISURATO — e quali `[R]` sono diventati `[M]`

Tutto su **NIC-OS**, sessione GNOME dell'utente `prova` (uid 1001, **senza `--virtual-monitor`**),
Mutter 48.7, `RecordVirtual` con `cursor-mode = 2`, strada memoria, BGRx 1920×1080.
Si ricontrolla con `sudo bash /media/REMOTIX/src/04-b26-lancia.sh tutto`; il deposito sta in
`banchi/04-b26-esiti-{senza,con,incorporato,prodotto}.jsonl`.

### 3.1 ⭐ Il `[R]` principale è diventato `[M]` — **prima** di curarlo

> `STUDI.md` §gnome §1.1 punto 6 / §5.2, `[R]`: *«chiediamo `cursor-mode=2` (metadato) ma non chiediamo il
> metadato ⇒ il cursore non arriva affatto»*.

| giro | che negoziazione | buffer | `SPA_META_Cursor` | `CURSORE_FORMA` |
|---|---|---:|---:|---:|
| `--sonda-senza` ⛔ **il difetto** | solo `Header` + `VideoDamage` — l'elenco che `cattura.c` aveva fino a stamattina | **62** | **0** | **0** |
| `--sonda-con` ⭐ **il controllo positivo** | la stessa sonda **più** `SPA_META_Cursor` | **49** | **49** (589 872 byte l'uno) | **4** |

⇒ `[M]` **14 agosto 2026**: il difetto è **riprodotto su 62 buffer**, e lo strumento che dice «zero»
è **lo stesso** che, con una riga di differenza, dice 49 su 49. ⛔ Lo zero è uno zero, non una cecità.

### 3.2 ⭐ Il cursore NON è nell'immagine — guardato su un fotogramma, con controllo positivo

Il banco mette una **tinta piatta nota** sullo sfondo (`#3465a4`/`#3465a5`), ferma il puntatore su
(400, 400) e conta, in un riquadro 96×96 attorno al puntatore, **quanti pixel non sono di quella
tinta**. Un cursore dipinto dentro sarebbe una macchia.

| giro | `cursor-mode` | pixel fuori dalla tinta attorno al puntatore |
|---|---|---:|
| `--prodotto` | **2** (METADATA) — quel che chiede il prodotto | **0** su 9216 |
| `--incorporato` ⭐ **controllo positivo** | **1** (EMBEDDED) — lo dipinge Mutter | **762** su 9216 |
| riquadro di fondo, dove il puntatore non è mai stato | — | **0** |

⇒ `[M]` **14 agosto 2026**: con `cursor-mode = 2` **non c'è un solo pixel** del puntatore
nell'immagine, e lo stesso strumento, sulla stessa scatola, ne conta **762** quando il puntatore
c'è davvero. `SPECIFICHE.md` §7.1 e `DECISIONI.md` §5-bis.2 sono rispettati **e verificati**, non
sperati.

*Secondo controllo, indipendente: la forma vera arrivata in banda laterale (32×32), composta a mano
dentro il fotogramma, cambia 347 pixel — l'ordine di grandezza torna.*

### 3.3 ⭐ La forma arriva in banda laterale — letta DAI BYTE, non dal registro

`04-b26-cursore` serializza ogni `CursoreForma` **come la scriverebbe `rcp.c`** (`RCP.md` §7.2,
big-endian) e ne deposita i byte; `04-b26-guarda.py` li **rilegge** e li misura. Giro `--prodotto`:

| serie | momento | forma | punto attivo | lunghezza | attesa `8 + l×a×4` |
|---:|---|---|---|---:|---:|
| 1 | la forma cambia | 48×48 | 6, 2 | 9 224 | 9 224 |
| 2 | un tocco | **0×0 — nascosto** | 0, 0 | 8 | 8 |
| 3 | il puntatore torna | 48×48 | 6, 2 | 9 224 | 9 224 |
| 4 | forma diversa | 32×32 | 3, 1 | 4 104 | 4 104 |

`[M]` **zero violazioni** di §7.2 e §5.5 su tutti i messaggi di tutti i giri: misura ≤ 256, lunghezza
esatta, nascosto = `0×0` con punto attivo `0,0`, punto attivo dentro l'immagine.

### 3.4 ⭐ Non si rimanda mille volte la stessa immagine

| | |
|---|---:|
| metadati letti (uno per **ogni** buffer) | **52** |
| `CURSORE_FORMA` partite | **4** — il **7,7 %** |
| **40 movimenti** del puntatore senza cambiargli forma | **0** forme nuove |

⛔ E il rovescio è misurato anche lui, perché «non rimanda sempre» non diventi «non manda mai»:
un tocco → **1** forma nascosta; il ritorno del puntatore → **1** forma; una forma diversa → **1**
forma.

### 3.5 `[R]` nuovi, letti riga per riga in `reference-gnome/mutter`

| | |
|---|---|
| Mutter manda la bitmap in **`SPA_VIDEO_FORMAT_RGBA`**, e `draw_cursor_into` legge la texture come `COGL_PIXEL_FORMAT_RGBA_8888_PRE` ⇒ **premoltiplicata** | il filo vuole BGRA premoltiplicato ⇒ si scambiano **solo** rosso e blu (`cursore.c`) |
| il metadato è allocato per **384×384** (`CURSOR_META_SIZE`), il filo si ferma a **256** | il taglio sta in `cursore.c` e si dichiara |
| «cursore invisibile» arriva come bitmap **azzerata** (`set_empty_cursor_sprite_metadata` scrive `format = RGBA` e poi rifà `= {0}`) | ⇒ trattata come **nascosto**, e la scelta è dichiarata nel file |
| `id = 0` ⇒ puntatore non visibile **o** fuori dal flusso | ⇒ **nascosto** |
| un evento di **touchscreen** mette `pointer_visible = FALSE` (`meta-backend.c:1170`) | è così che il banco fa comparire lo stato «nascosto» a comando |

---

## 4. ⛔ Che cosa NON ha funzionato

### 4.1 ⛔ Il primo banco è nato con `mutter_apri`, e ha misurato niente

Mutter lega la sessione RemoteDesktop **al peer D-Bus** che l'ha creata. `src/mutter.c` apre una
connessione **privata** e non la espone: il banco muoveva il puntatore da una connessione sua e si
prendeva `AccessDenied` su **tutti e 40** i movimenti — con un solo buffer arrivato e un banco che
sembrava funzionare. ⇒ La sequenza D-Bus è stata **riscritta dentro il banco**. Effetto collaterale
buono: il banco non dipende più da `src/mutter.c`, che l'anello A4 sta cambiando adesso.

### 4.2 ⛔⛔ **La forma può non arrivare MAI su un flusso appena aperto** — e non è un difetto nostro

`[M]` primo giro con il metadato chiesto: **43 metadati su 43 buffer, e `bitmap_offset = 0` su
tutti** — cioè solo la posizione, mai la forma. `[R]`
`meta-screen-cast-virtual-stream-src.c`: la bitmap viaggia **solo** se `cursor_bitmap_invalid`, che
nasce **falso** (l'oggetto è azzerato) e diventa vero **soltanto** sul segnale `cursor-changed`.
`enable()` non lo accende.

⇒ Su un desktop fermo il client riceve la posizione e **nessuna forma**, senza nessun errore.
`cursore.c` lo **dichiara** invece di inventarsi una freccia (`forma_ignota`, una riga di registro),
e il banco fa cambiare la forma a comando per poterne misurare una.
⚠ Resta `[?]` **quanto** duri in uso reale: appena il puntatore passa sopra una finestra che
imposta un cursore, `cursor-changed` scatta.

### 4.3 ⛔ Su un monitor virtuale fermo NON arriva nessun fotogramma — e nemmeno muovendo il puntatore

`[M]`: `cattura_prendi` tornava `ZERO` (che è uno zero **legittimo**, non un guasto) per cinque
secondi di fila, in **tutt'e due** i modi del cursore. La cadenza è `0/1`, e muovere il puntatore in
modo METADATA non cambia un pixel — per costruzione. ⇒ Il banco **ridipinge a comando** cambiando la
tinta dello sfondo di **una unità** su un canale: abbastanza per far arrivare un fotogramma, non
abbastanza per cambiare un giudizio. ⭐ È la stessa mossa che dà alla domanda 1 la sua *«zona di
colore noto»*.

### 4.4 ⚠ Il monitor su cui ho misurato NON è quello con la shell

Sulla sessione di `prova` c'erano già **due** «Virtual remote monitor» montati da altri anelli in
parallelo; il mio `RecordVirtual` ne ha montato un terzo, che ha lo **sfondo** ma non barra né dock.
⚠ Per le due domande di A6 non cambia nulla — anzi il fondo fermo rende la misura più pulita — ma
va scritto: **il fotogramma giudicato non è il desktop completo.**

### 4.5 ⚠ La sessione di `prova` è stata toccata, e rimessa

Il banco cambia `org.gnome.desktop.interface cursor-size` e quattro chiavi di
`org.gnome.desktop.background`, e le **rimette con `gsettings reset`** alla fine del giro. Se un
giro cade a metà, lo sfondo di `prova` resta a tinta piatta: si rimette con
`gsettings reset org.gnome.desktop.background primary-color` (e `picture-uri`).

---

## 5. Le cuciture che chiedo al coordinatore

### 5.1 ⛔ Una riga in `src/cattura.h` — già scritta, da benedire o da spostare

```c
void cattura_cursore(Cattura *cattura, CursoreArrivata quando_cambia, void *chi);
```

⚠ Ho dovuto scriverla per forza: `cursore_apri()` vuole il destinatario **all'apertura**, e
l'apertura avviene dentro `cattura_avvia`, cioè prima che chiunque possa registrarsi. Dentro,
`cattura.c` rimbalza sotto lucchetto verso chi si è registrato. ⛔ **Non ho toccato `cursore.h`.**

Con essa, in `CatturaConteggi` sono entrati tre contatori — `cursore_assente`, `cursore_metadati`,
`cursore_malformati` — e i primi due sono **due e non uno** apposta: distinguono «il puntatore non
c'era» da «il metadato non l'abbiamo chiesto».

### 5.2 ⛔ Due righe nel `Makefile` (che è tuo), oggi mancanti

```make
cattura.o:        cattura.h cursore.h registro.h
cursore.o:        cursore.h registro.h
```

Oggi `cattura.o` non dipende da `cursore.h` e `cursore.o` non ha riga: cambiando il contratto del
cursore, `make` **non ricompilerebbe**.

### 5.3 ⭐ Chi consuma la forma — la riga che manca per chiudere il canale

Nessuno chiama ancora `cattura_cursore`. Va cucita nel figlio, dove nasce la cattura:

```c
/* in figlio.c, dopo cattura_avvia: */
cattura_cursore(cattura, /* CursoreArrivata */ rcp_cursore_forma, sessione_rcp);
```

⛔ E il lato `rcp.c` è dell'anello **A3**: gli serve una funzione con **esattamente** questa firma —

```c
int rcp_cursore_forma(void *chi, const CursoreForma *forma);
```

— che scriva `CURSORE_FORMA` (`RCP.md` §7.2, big-endian: `u16 larghezza`, `u16 altezza`,
`i16 attivo_x`, `i16 attivo_y`, poi `larghezza × altezza × 4` byte BGRA premoltiplicati) e ritorni
`0` se accettata, `-1` se rifiutata. ⚠ **L'immagine vive solo per la durata della chiamata**, e la
chiamata arriva dal **thread di tempo reale di PipeWire**: chi la vuole tenere la copia, e non
aspetta niente lì dentro.

⛔ **I limiti li ho già fatti rispettare io** (`cursore.c`): misura ≤ 256, lunghezza esatta,
nascosto = `0×0` con punto attivo `0,0`. `rcp.c` non deve rifarli — deve fidarsi e scriverli.

### 5.4 ⭐ A A4 (`src/mutter.c`): **non cambiare `cursor-mode`**

`src/mutter.c:439` chiede `cursor-mode = 2` ed **è giusto così** — misurato in §3.2: con 2 i pixel
sono puliti e la forma arriva in banda laterale; con 1 il puntatore finisce nell'immagine e l'utente
ne vedrebbe **due** (`SPECIFICHE.md` §7.1). ⛔ **Non ho toccato `mutter.c`.**

### 5.5 ⚠ Per la fase 11 (KDE) e per wlroots — la trappola che qui NON è scattata

Su Mutter **non serve** nessun tema di cursore trasparente: `cursor-mode = 2` toglie il puntatore
dai pixel da sé (`inhibit_cursor_overlay`), ed è misurato. ⛔ **Ma se un giorno servisse, il canale
non è `XCURSOR_THEME`**: Mutter non la legge (l'unico `getenv` rilevante è `XCURSOR_PATH`), legge
`org.gnome.desktop.interface cursor-theme` — e **un tema vuoto dà un quadrato grigio**, che è peggio
del difetto che si voleva curare. Su KWin e wlroots il canale è invece `XCURSOR_THEME`
(`DECISIONI.md` §5-bis.2), e là il tema si verifica **caricato**, non scritto.

---

## 6. Che cosa resta `[?]`

1. `[?]` **il taglio a 256 non è mai scattato**: Mutter alloca il metadato per 384×384, ma i temi di
   GNOME misurati arrivano a 48. Se un giorno scattasse, la cosa da misurare è se convenga
   **sottocampionare** invece di tagliare l'angolo;
2. `[?]` **`format = 0` letto come «nascosto»** è `[R]` su Mutter (è l'unico modo in cui manda un
   puntatore senza immagine) ma la lettera di `spa/buffer/meta.h` direbbe «nessuna informazione
   nuova»: su un altro compositore va **rimisurato**;
3. `[?]` **quanto tarda la prima forma** in uso reale (§4.2);
4. `[?]` tutto il resto **fuori da Mutter**: KWin e wlroots non sono stati toccati da questo anello.
