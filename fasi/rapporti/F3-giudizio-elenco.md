# Il giudizio della fase 3 — l'elenco da leggere PRIMA di guardare

*Preparato la notte del 13 agosto 2026 perché domattina costi quindici minuti.*

⛔ **Perché un elenco e non «guarda e dimmi»**: `PIANO.md` §0.3 dice che una fase si chiude su una
misura giudicata dall'utente. ⚠ Ma un'approvazione data **senza sapere che cosa manca** è
un'approvazione al buio — è la forma della fase 2, e si ripete qui.

---

## 1. Che cosa devi fare, in tre righe

> *(i comandi esatti stanno in fondo, in «Come si accende»)*

1. accendi la sessione e apri la scheda;
2. **muovi il tuo desktop** — trascina una finestra, scorri una pagina, apri il menu;
3. dimmi **se è fluido abbastanza**, con parole tue.

⭐ **Non ti sto chiedendo di validare un numero.** Il tuo giudizio e il numero dell'anello sono
**due cose separate**, e valgono tutt'e due:

| | che cosa dice | su che scena |
|---|---|---|
| **il tuo giudizio** | *«è fluido abbastanza»* | **il tuo desktop**, che si muove quando lo muovi tu |
| **il numero dell'anello** | il ritardo mediano in millisecondi | una scena **dichiarata e ripetibile**, non la tua |

⇒ ⛔ Il tuo giudizio **non conferma né smentisce** il numero, e viceversa. Se ti sembra fluido e il
numero sfora, valgono tutt'e due e la contraddizione è **un dato**, non un errore.

---

## 2. ⛔ Che cosa NON è ancora a posto — si legge prima di approvare

*Questa sezione viene riempita a fine notte con quel che sarà vero allora. Le righe qui sotto sono
quelle note alle 23:00 del 13 agosto; ⛔ quelle superate saranno barrate e datate.*

| | che cosa manca | quanto pesa sul tuo giudizio |
|---|---|---|
| **1** | ⏳ **Il numero con la codifica in hardware** — è il lavoro della notte | ⚠ **molto**: se non c'è, stai giudicando la fluidità del prodotto **col freno a mano tirato** (la codifica in software vale il **55 %** del ritardo) |
| **2** | ⛔ **I banchi browser misuravano sul tuo desktop** credendo di essere su uno schermo finto | ⭐ **nessuno**: riguarda i banchi, non il prodotto. Ma spiega perché i numeri di ieri portavano dentro la contesa col tuo desktop |
| **3** | ⏳ **`P5R` e la marca di `03-b19`** non sono rigirati | poco: è debito di catalogo, non del prodotto |
| **4** | ⛔ **22 file del prodotto non sono guardati da nessuna certificazione** | ⚠ **da sapere**: non vuol dire che un guasto passerebbe, vuol dire che una riga verde continuerebbe a dire «certificato» su un prodotto che nel frattempo è un altro. **È lavoro di una fase sua** |
| **5** | ⛔ **`03-b16` non si rigira** finché il palco non è a posto | poco, e la ragione è scritta a catalogo |
| **6** | ⏳ **I millisecondi del secondo motore (Firefox)** restano `[?]` per contaminazione **dichiarata** | poco: i conteggi e i sì/no reggono, mancano i tempi |

---

## 3. ⭐ Che cosa invece regge, e su questo puoi appoggiarti

| | |
|---|---|
| il **numero della fase** | **72,397 ms** di mediana, rimisurati con banco e pagina diversi da quelli che l'avevano prodotto (n=508) — e la codifica vale **39,82 ms, il 55 %** |
| la **codifica in hardware** | funziona: il tratto passa da **28,03 a 2,64 ms** (scena facile) e da **113,10 a 3,93** (dura) |
| il **client** | `VideoDecoder` decodifica HEVC Main10: **120 fotogrammi su 120**, due strade di confezionamento, 5 giri su 5 |
| il **catalogo** | 25 banchi, e quelli certificati lo sono col ciclo intero **sano → guasto → risanato**, con la marca **misurata** |

---

## 4. ⏳ Le due domande che hai lasciato aperte di proposito

⛔ **Non sono dimenticanze: sono decisioni tue, e nessuna delle due va decisa prima del giudizio.**

| | | quando si chiude |
|---|---|---|
| **D1** | **il debito di chiave strozzato** a una richiesta al secondo — un abbandono legittimo ne può generare fino a sessanta illegittimi | ⭐ **subito DOPO il tuo giudizio, e costa zero**: si legge il registro **della sessione in cui hai guardato**. Tre numeri: quante volte scatta, quanti delta per volta, quanto passa fino alla chiave |
| **D2** | **dove finisce di contare il tetto dei 50 ms** — al **disegno** o al **pixel acceso**? Con un codificatore gratis fa **~35,4** al disegno e **51-75** sul vetro: *la stessa architettura è promossa o bocciata a seconda di dove metti il traguardo* | **dopo** il numero in hardware, con due numeri veri davanti invece di una forbice. ⛔ E la decidi **tu** |

---

## 5. Come si accende

*(riempito a fine notte con i comandi esatti e la porta, verificati su una sessione vera —
⛔ non scritti a memoria)*

---

## 6. ⚠ Una cosa da sapere mentre guardi

Il prodotto sceglie il codec **negoziandolo col browser**. Stanotte è stato scoperto che per giorni
ha negoziato **AV1 in software** per via di una riga in un banco, e che **AV1 in hardware su questa
macchina non esiste**. ⇒ Se domattina la sessione dovesse negoziare AV1, **quel che stai guardando è
il prodotto col freno a mano**, e va detto **prima** che tu dia il giudizio — non dopo.

⭐ **Te lo dirò io, letto dal registro della tua sessione**, non da un'aspettativa.
