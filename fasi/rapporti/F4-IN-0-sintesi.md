# F4-IN-0 — I cinque studi dell'input, messi in colonna

⭐ **Scritto il 14 agosto 2026 a sera**, dopo cinque studi paralleli (xrdp ·
gnome-remote-desktop · xpra · Android/DeX · Devolutions RDM). ⛔ **Questo documento SUPERA
`F4-DEX-punto-di-ripresa.md` §5 e §6**, che restano com'erano scritti, con la loro data.

I cinque rapporti sono `F4-IN-1` … `F4-IN-5`. Qui c'è solo quel che sopravvive al confronto fra
loro, con le verifiche fatte **a mano** sul nostro codice.

---

## 1 · ⛔ La `[?]` che vincolava tutto è MORTA — e non era `cursor: none`

Il punto di ripresa §5 diceva: `[M]` con `cursor: none` **4 clic e ZERO movimenti**, contro
165 · 227 · 320 · 200 senza. Una variabile sola, correlazione fortissima, **meccanismo ignoto**.

⛔ **Era una coincidenza.** `[R]` `git show 0075b4f:src/pagina.html:3909` — la versione in vigore
alle 15:09 registrava **`mousemove` e basta**:

```
tela.addEventListener("mousemove", cl_su_mousemove);
```

`pointermove` in quel commit compare in **una sola riga, dentro un commento** (`:4733`) —
verificato a mano il 14 agosto 2026.

⇒ E su Samsung è documentato da **quattro progetti indipendenti** (noVNC #1727, KasmVNC #222,
Kasm workspaces #20, moonlight-android #573) che Chrome consegna i `mousemove` **solo al clic**.
**«4 clic e ZERO movimenti» è la definizione letterale di quel difetto.**

⭐ **La cura è già nel prodotto**: `pointermove` è entrato due ore dopo la misura, per un'altra
ragione. `[M]` 7 righe in `536e3d2` contro 1 (di commento) in `0075b4f`.

### E il meccanismo non esisteva comunque

`[R]` `ViewRootImpl.java:8118-8119`: `mView.dispatchPointerEvent(event)` viene **prima** di
`maybeUpdatePointerIcon(event)` — l'icona del puntatore è un **effetto** del movimento, non una
sua condizione. `PointerChoreographer::notifyMotion` inoltra **incondizionatamente**
(`:173-177`), e `InputDispatcher.cpp` non nomina mai icone né sprite (assenza certificata su
7 occorrenze di `ACTION_HOVER_MOVE` nello stesso file).

⇒ ⛔ **Il divieto «sul DeX non si può nascondere il cursore del browser» NON esiste.** noVNC mette
`cursor: none` su *ogni* dispositivo tattile (`core/util/cursor.js:9,109`) e non è rotto.

---

## 2 · ⭐⭐ Quel che i cinque dicono all'unisono: **UN puntatore, non due**

| chi | che cosa fa il puntatore |
|---|---|
| **xrdp / FreeRDP** | `[M]` 200 movimenti a schermo fermo = **0 byte** dal server. Il client **presta la forma** al cursore del sistema (`XcursorImageLoadCursor` + `XDefineCursor`) |
| **FreeRDP Android** | `[R]` **butta via** le PDU del puntatore: sei funzioni col corpo vuoto. Su Android il puntatore fluido è **quello di sistema** |
| **xpra** | `[R]` **non usa `cursor: none` da nessuna parte**; il cursore del browser veste la forma remota |
| **gnome-remote-desktop** | `[R]` percorso VNC: manda la **posizione** perché il suo client non ha modo di saperla |

> ⭐⭐ **La differenza fra loro e noi non è il protocollo: è che loro hanno UN puntatore e noi ne
> abbiamo DUE.**

`[M]` E sul DeX il cursore di sistema **non si può togliere di mezzo comunque**: è una
`SurfaceControl` con flag `eCursorWindow`, mossa dal thread di input a **125 Hz**,
**indipendente dai fotogrammi dell'applicazione**. ⇒ È la ragione per cui il puntatore *sembra*
funzionare mentre il desktop remoto è a 1,1 fotogrammi al secondo.

### ⛔ E la cura è scritta, e non è mai partita

`[R]` verificato a mano, 14 agosto 2026:

| dove | che cosa |
|---|---|
| `src/pagina.html:2983-2987` | `CURSORE_FORMA` arriva e viene **buttato** con un `nota()` |
| `src/pagina.html:3752` | `forma: function (f)` — la funzione che veste il cursore **esiste** |
| ovunque | **nessun chiamante**: l'unico altro posto dove il nome compare è un commento (`:3694`) |
| `STUDI.md` §xpra §2 | la decisione ✅ *«il cursore del browser veste la forma remota»*, **14 agosto** |

⇒ **La decisione è presa, il codice è scritto, il filo fra i due non è mai stato attaccato.**

`[R]` E la strada regge su Android: Chromium `ViewAndroidDelegate.java:316-321` traduce
`cursor: url(...) hx hy` in `PointerIcon.create(bitmap, hotspotX, hotspotY)`. Limiti di Blink:
**128 DIP duro**, **32 DIP morbido** (oltre i 32 il cursore sparisce se tocca il bordo della
vista). Punto attivo rispettato.

---

## 3 · Il fotogramma che non arriva — e chi l'ha risolto davvero

`[M]` Il difetto misurato: **134 fotogrammi in due minuti = 1,1 al secondo**, perché Mutter
consegna solo quando cambia un pixel e il cursore lo prendiamo come metadato.

| | |
|---|---|
| ⭐⭐ `[R]` **Mutter un buffer lo manda lo stesso** | in modo `METADATA` aggancia `position-invalidated`: a ogni movimento esce un buffer con `chunk->size = 0` e dentro `spa_meta_cursor->position`, **già in pixel di tela**. Tetto: 60/s |
| ⛔ **e noi lo buttiamo** | `[M]` `position` **non compare in nessuna riga di `src/`** (strumento certificato: `hotspot` e `spa_meta_cursor` si trovano) |
| ⭐ chi lo legge | `grd-vnc-pipewire-stream.c:788-789` |
| ⛔ **xpra ha il nostro identico difetto** | `codecs/pipewire/capture.py:143-145` risponde `False` quando PipeWire non consegna. **Non l'hanno risolto: hanno tolto il puntatore dal fotogramma** |
| ⛔ **xrdp gira a 0 fps** a scena ferma | e non è un difetto: `[M]` 0 byte, cursore fuori dall'immagine. Le **stesse due scelte** nostre |

⇒ ⚠ **La catena causale «1,1 fps ⇒ mouse inutilizzabile» non regge da sola.** 0 fotogrammi al
secondo vanno benissimo **purché il puntatore non dipenda dai fotogrammi**. Quel che 1,1 fps
spiega è che **il desktop non reagisce**; non spiega perché il puntatore sia scomodo.

⛔ E la strada 6.2 del punto di ripresa — *«forzare una cattura a ogni `PUNTATORE`»* — **non ha
precedenti in nessuno dei cinque**. Il cursore **dipinto** (`EMBEDDED`) ha **zero usi** in GRD.

---

## 4 · Che cosa NON possiamo fare, e va in `DECISIONI.md`

`[R]` Su Chrome per Android la **Pointer Lock** è implementata, ma `movementX` è **ricostruito**
da Chromium (`PointerLockEventHelper.java:52-108`) e i micro-movimenti sono **scartati**.
`[S]` RDM ha invece `View.requestPointerCapture()` — **una** chiamata, che a noi in un browser è
preclusa.

⚠ **E il metro di paragone regge**: l'utente, 14 agosto 2026, testuale — *«Con RDM non c'è
nessun problema»*. `[M]` È la sua esperienza diretta sulla stessa scena (DeX, stesso mouse,
stesso monitor) e **vale più di una citazione di forum**. L'ingegnere di Devolutions dice
*«janky»* del caso **generale** con monitor esterno e aggiunge che **su DeX funziona meglio**,
*«perché lo schermo esterno è trattato come un desktop pienamente indipendente»* `[S]`.

⇒ ⭐⭐ **RDM su DeX è un controllo pulito**: stessa piattaforma, stesso ferro, zero problemi. Il
DeX, il Bluetooth e Android sono **scagionati per la seconda volta** — la prima era il tratto
«prima di noi» di 9-12 ms. **Quel che resta è nostro.**

---

## 5 · Le tre cose gratis, confermate da più di una fonte

1. **Il `devicePixelRatio` fuori dalla conversione.** Terza conferma indipendente: `[R]` xrdp
   legge il fattore di scala e **non lo usa mai per moltiplicare niente**; `[S]` [MS-RDPEDISP]
   ammette **solo tre densità** — il nostro DPR **1,2** non sarebbe nemmeno rappresentabile.
2. **Vincoli di sanità per la misura del monitor** (se si prende la strada §5.1):
   `[R]`+`[S]` `200 ≤ misura ≤ 8192`, **larghezza pari** (l'altezza no: l'asimmetria è nella
   specifica). Il nostro 2560×926 li rispetta.
3. ⛔ **`getCoalescedEvents()` non vale una riga**: `[R]` Chrome passa `history_size = 0` per il
   mouse (`event_forwarder.cc:208`) mentre il percorso del tocco la legge (`:80-81`) ⇒ su DeX
   restituirà **1**, e il tetto resta 60 Hz.

---

## 6 · ⛔ I due difetti nostri trovati per strada

| dove | che cosa |
|---|---|
| `cattura.c:759` | il conto `solo_cursore` si stampa ogni 300 fotogrammi, ma il blocco sta **prima** di `restituisci:` (`:770`), dove i buffer di solo cursore saltano con un `goto` (`:634`, `:642`) ⇒ **su due minuti, zero stampe**. È il numero che decide l'intera tesi, e non poteva stamparsi |
| `pagina.html:3752` | `forma()` senza chiamanti (§2) |

⚠ E uno **loro**, che riguarda il collaudo della cura: `grd-session-vnc.c:198-199` ha `||` dove
serve `&&` ⇒ un movimento **puramente orizzontale** viene scartato. Se copiamo quella guardia, il
collaudo dev'essere *«muovi in orizzontale e conta»*, non *«muovi»*.

---

## 7 · ❓ La decisione che resta all'utente

La cura minima che i cinque studi indicano all'unisono — **vestire il cursore di sistema e
togliere la nostra freccia** — non cambia la forma del prodotto e non richiede una decisione:
attua una decisione ✅ già presa il 14 agosto.

❓ **Resta aperta la strada §5.1** — chiedere a Mutter un monitor della misura del client — che
**cambia** la forma del prodotto (bande zero, conversione a uno stadio, il 36 % di pixel neri che
sparisce) ed è dell'utente.

---

## Quel che questa sintesi non dice

- ⛔ **Nessuna misura sul DeX**: tutto quel che riguarda il dispositivo dell'utente è `[R]` o
  `[S]`. La pagina di prova è pronta — `banchi/05-dex-cursore.html`, porta **7912**.
- ⚠ **Perché il puntatore sia scomodo resta senza una causa misurata.** L'ipotesi più forte è
  §2 — due puntatori, l'utente mira con quello di sistema e il clic parte dove sta l'altro — ma
  è `[?]`, e va misurata prima di crederci.
- Le citazioni dal forum Devolutions sono passate per un riassuntore e sono marcate `[S]`⚠︎ nel
  rapporto `F4-IN-5`; il riassuntore aveva **inventato due numeri di discussione**, verificati
  404 e scartati.
