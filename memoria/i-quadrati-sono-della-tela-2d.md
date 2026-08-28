---
name: i-quadrati-sono-della-tela-2d
description: "I blocchi 64x192 non erano di REMOTIX: è la tela 2D che si rompe andando allo schermo. `bitmaprenderer` è pulito, e la caccia è chiusa il 17 ago 2026"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6917bf53-6d6d-42bb-8bd5-f1d628833c28
  modified: 2026-08-17T18:01:46.539Z
---

⭐⭐⭐ **17 agosto 2026, sera — la caccia è chiusa, e la colpa NON era nostra.**
L'utente vedeva blocchi rettangolari da **64×192** che si spostavano col
contenuto. Sono stati scagionati, uno per uno e con la misura accanto:

| imputato | la prova |
|---|---|
| la cattura / Mutter | `scatto-ingresso.bgrx` preso **mentre i blocchi erano in vista**: pulito |
| il codificatore, 300 delta in catena | gli stessi byte via `ffmpeg`: **0 superblocchi rovinati su 600**, media 1,68 |
| la forma dei pezzi | 300 unità temporali, 1 fotogramma ciascuna, nessun nascosto |
| `VideoDecoder` | `copyTo` contro la verità: 0 fuori posto |
| la tela **riletta** | `getImageData` contro la verità: **0 su 180 000**, peggio 2,9 livelli |
| **la tela DIPINTA sullo schermo** | ⛔ **fotografata col cellulare: i rettangoli ci sono** |

⇒ **I pixel entrano giusti nella tela e si rompono quando la tela va allo
schermo.** Nessun programma può leggerli lì: `getImageData` legge il magazzino,
non quel che il compositore ha acceso.

⛔ **E non è il browser**: Firefox **e** Chrome fanno lo stesso. Non è la GPU in
generale: `ffplay` e YouTube — che dipingono in un **`<video>`** — sono
**puliti**. È la strada della **`<canvas>` 2D**.

⭐⭐ **LA CURA, misurata**: dipingere con **`createImageBitmap()` +
`transferFromImageBitmap()`** su un contesto **`bitmaprenderer`**, che non ha il
magazzino 2D. Giudizio dell'utente sulla stessa scena: *«NIENTE ARTEFATTI!»*

⭐⭐ **ED È NEL PRODOTTO dal 20 agosto 2026** (`src/pagina.html`): una sola
conversione invece di due `drawImage`, il deposito non serve più
(`transferFromImageBitmap` dimensiona la tela da sé e il contenuto sopravvive al
ridimensionamento), numero d'ordine + epoca perché `createImageBitmap` è
asincrona, e `?tela=2d` accende la strada vecchia per confronto. `[M]` col
testimone Marionette: `dipinti == consegnati`, `tard 0`, `err 0`, PNG nitido.
⏳ **Manca il giudizio dell'utente sul PRODOTTO** (finora era su un banco), e
`[?]` quanto costa `createImageBitmap` — il conto da battere è 34,03 ms.

**Che cosa comportava, e adesso è fatto:**
- oggi il fotogramma passa da **due** tele 2D: `deposito_p.drawImage(f)` e poi
  `componi()` → `pennello.drawImage(deposito)`;
- ⭐ il **cursore non è dipinto sulla tela** — è un cursore CSS — quindi la tela
  visibile non deve comporre niente, e `bitmaprenderer` le basta;
- ⚠ l'unica cosa che si perde è **centrare/incorniciare** quando la finestra è
  più larga dell'immagine: si fa col CSS;
- ⚠ e va **misurato il costo**: `createImageBitmap` è asincrona, e il ritardo è
  il numero per cui esiste la fase 3.

Il banco che lo dimostra è `banchi/07-b48` (+ `07-b49` per l'occhio) e **non ha
una riga di REMOTIX dentro**.

⛔⛔⭐ **20 agosto 2026: erano DUE difetti sovrapposti, non uno.** La cura
`bitmaprenderer` ha ripulito **Chrome** e su **Firefox** i blocchi restavano.
Il secondo imputato è il suo **decodificatore AV1**, isolato con tre immagini
dello stesso istante (`banchi/07-b52`): cattura pulita · flusso spedito riletto
da `ffmpeg/dav1d` pulito su 22 delta · Chrome pulito · **Firefox a blocchi**, con
`dipinti == consegnati` e zero errori.

⭐⭐ **La cura è H.264, ed è nel prodotto dal 20 agosto**: stessa scena, 35
consegnati = 35 dipinti, **nessun blocco**. ⇒ La decisione [[av1-esce-entra-h264]],
nata per Firefox Android, era anche la cura di questo.

Vedi [[av1-esce-entra-h264]], [[le-prove-le-eseguo-io]], [[la-prova-la-fa-lutente]].
