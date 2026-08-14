# Il giudizio della fase 3 — l'elenco da leggere PRIMA di guardare

*Preparato la notte del 13 agosto 2026 perché domattina costi quindici minuti.*

⛔ **Perché un elenco e non «guarda e dimmi»**: `PIANO.md` §0.3 dice che una fase si chiude su una
misura giudicata dall'utente. ⚠ Ma un'approvazione data **senza sapere che cosa manca** è
un'approvazione al buio — è la forma della fase 2, e si ripete qui.

---

## 0. ⭐⭐ IL NUMERO C'È — e porta una domanda che è tua

*Misurato la notte del 13 agosto, **quattro** giri, **una variabile per volta**, e il numero finale
è preso **sull'albero del deposito** — cioè esattamente su quel che guarderai.*

| | totale | codifica | **disegno** | **fotogrammi/s** | P1 |
|---|---|---|---|---|---|
| **AV1 in software** *(la 7561, quel che girava fino a ieri)* | **71,86 ms** | 39,67 | ⭐ 9,07 | 22,0 | ✅ |
| ⭐ **HEVC in hardware** *(la 7571, quel che guarderai)* | **78,12 ms** | ⭐ **31,78** | ⛔ **28,00** ⚠ *(non è «disegno»: vedi la riga 2 più sotto)* | ⭐ **30,0** | ✅ |
| *(HEVC in software, per capire)* | 109,77 | ⛔ 63,22 | 28,99 | 14,6 | — |

⚠ **E il numero della fase è 78,1, non il 75,2 misurato prima su una copia**: quel giro aveva un
controllo del banco **rosso**, questo no. ⛔ **Si è preso il peggiore dei due — non si sceglie il più
bello.**

⭐⭐ **La codifica in hardware funziona**: la chiave costa **23 volte meno** (4 894 µs contro
114 533), e **il ritmo raddoppia**.
⭐⭐ **E l'architettura è ASSOLTA**: tolta la codifica, gli altri quattro tratti **restano dove
erano** (Mutter −0,01 · filo −0,07 · decodifica −0,72). ⇒ *Non c'era un secondo problema nascosto
dietro il primo.*

> ### ⛔ E la domanda che devi decidere tu, guardando
>
> **HEVC in hardware ha 3 ms di ritardo IN PIÙ e 9 fotogrammi al secondo IN PIÙ.**
> ⇒ Le due cose tirano in versi opposti, e **nessun numero può dire quale conti di più per un occhio
> umano**. È esattamente ciò per cui il tuo giudizio esiste.
>
> ⚠ Se vuoi confrontarle davvero, si può accendere **anche l'altra configurazione** e passare
> dall'una all'altra: costa cinque minuti in più. Dimmelo e lo preparo.

⛔ **E il perché dei 3 ms in più, che è la scoperta della notte**: passando a HEVC **il disegno va da
9,1 a 25,1 ms**. ⇒ **Il collo di bottiglia non è più la codifica: è il disegno**, il 33 % del
ritardo, e **nessuno lo stava guardando**. È il primo lavoro della fase che verrà.

⚠ **Una riserva scritta, non nascosta**: nel giro in hardware un controllo del banco (P1, la taratura
del ritardo iniettato) è **rosso**. Il ponte è **scagionato con una misura** (scarto di consegna
**0 µs** su 20 000 pacchetti), e la pista è la saturazione a 30 fps — ⛔ ma è **una lettura, non una
misura**, e stanotte si sta cercando di trasformarla in una. **Il numero ti arriva con questo
asterisco**, non senza.

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
| ✅ | ~~il numero con la codifica in hardware~~ | ⭐ **fatto**: 78,1 ms, P1 verde, sull'albero che guarderai |
| ✅ | ~~la codifica in hardware nel prodotto~~ | ⭐ **fatta**: non più su una copia. Il ritorno indietro è **una riga** |
| **1** | ⛔⛔ **Il numero SFORA**: 78,1 contro il tetto di **50** e il traguardo di **40** — e col pezzo cieco dichiarato sta fra **94 e 118 ms** sul vetro | ⚠ **è il fatto centrale**. ⛔ Ma guarda **prima** e leggi **dopo**: il numero non è la fluidità, e i due giudizi restano separati |
| **2** | ⚠ ~~**Il collo di bottiglia adesso è il DISEGNO**: 28,0 ms su 78,1~~ ⇒ ⛔ **l'etichetta è FALSA, corretta il 14 agosto 2026**: il disegno costa **2,25 ms** `[M]`, i 28,0 erano **l'attesa del fotogramma dalla GPU**. Il totale resta vero (`F4-A2`, `F4-A10`) | ⭐ **nessuno sul giudizio**, ma è **il primo lavoro della prossima fase**, e non era in nessun piano |
| **3** | ⛔ **I banchi browser misuravano sul tuo desktop** credendo di essere su uno schermo finto | ⭐ **nessuno**: riguarda i banchi. Ma spiega perché i numeri di ieri portavano dentro la contesa col tuo desktop |
| **4** | ⏳ **6 banchi su 25 non hanno una certificazione che regge** — `B10 · B13` (scadute, **non rigirabili**: gli alberi dei loro guasti non esistono più) · `P5 · P5R` (non c'era il tempo, e **non sono state comprate**) · `03-b16` (aspetta il palco) · `03-b19` (mai provato) | ⚠ **poco sul prodotto**, ma va saputo: **non è che siano rosse — è che la loro riga verde descrive un prodotto di ieri**. ⭐ **P1 è stata rigirata stanotte** e regge |
| **5** | ⛔ **22 file del prodotto non sono guardati da nessuna certificazione** | ⚠ **da sapere**: una riga verde continuerebbe a dire «certificato» su un prodotto che nel frattempo è un altro. **È lavoro di una fase sua** |
| **6** | ⛔ **`03-b16` non si rigira** finché il palco non è a posto | poco, e la ragione è scritta a catalogo |
| **7** | ⚠ **Due difetti del banco dell'anello, trovati e NON curati** | `regime()` non butta il transitorio della **sessione**; `misura()` non deposita la riga se la stampa esplode. ⛔ Lasciati scritti perché *un banco curato che nessuno ha visto arrossire non è curato* |

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

## 5. Come si accende — ⭐ e puoi confrontare le due configurazioni

⭐⭐ **La tua porta 7561 NON è stata toccata.** Ci gira ancora il server che hai acceso tu
(da 12 ore, binario e pagina di ieri): ⇒ è **la configurazione vecchia**, AV1 in software.

⭐ Quella nuova sta sulla **7571** — la porta che `02-figlio-accendi.sh` usa **per progetto**, da
root, mostrando il desktop di chi entra.

| apri | che cosa stai guardando |
|---|---|
| `https://192.168.0.2:7561/` | ⏳ **il vecchio**: AV1 in software · 72,40 ms · **21 fps** |
| `https://192.168.0.2:7571/` | ⭐ **il nuovo**: HEVC in **hardware** · 75,23 ms · **30 fps** |

⇒ ⭐ **Puoi tenerle aperte in due schede e passare dall'una all'altra.** È il confronto che ti
avevo offerto, e costa zero: le due configurazioni **esistono già tutt'e due**, su due porte
diverse, senza che nessuno debba spegnere niente.

⚠ **Entra come te stesso** in tutt'e due, come per il giudizio della fase 2.

### ⭐ Tutt'e due sono ACCESE adesso — non c'è niente da lanciare

`[M]` verificato alla chiusura della notte:

```
:7448 :7501 :7561 :7571          ← le porte vive sul server
pid 326940  da 13h23  …/src/remotix/remotix           --porta 7561   ← il tuo, intatto
pid 410731  da 16m56  …/02-figlio-src/src/remotix     --porta 7571   ← il nuovo
```

⇒ **Apri due schede e basta.** Se una delle due non rispondesse, si riaccende così:

| | |
|---|---|
| la **7571** | `bash banchi/02-figlio-lancia.sh accendi` *(da CHUWI; lo script fa il resto)* |
| la **7561** | ⛔ **è tua**: nessuno l'ha toccata, e nessuno la riaccenda al posto tuo |

### ⭐⭐ E la 7571 è stata provata fino al pixel, non solo accesa

`[M]` sessione vera contro `https://192.168.0.2:7571/`, **quattro fatti nello stesso giro**:

```
negoziato video.codec=hevc — codec 1
aperto: HEVC 10 bit via hevc_vaapi (in HARDWARE · /dev/dri/renderD128 · Intel iHD)
PRIMO fotogramma codificato: CHIAVE, «hev1.2.4.L120.B0»
t+ 4s  consegnati  567 · dipinti  567 · scartati_ordine 0 · buchi 0
t+20s  consegnati 1047 · dipinti 1047 · scartati_ordine 0 · buchi 0
```

⭐ **+120 ogni 4 secondi = 30 fps esatti**, e `consegnati == dipinti` a ogni lettura: **non ne cade
uno**. ⇒ **La 7571 non mente**: dice HEVC in hardware e lo fa **fino al vetro**.

⚠ **Ma la scena di quella prova era SINTETICA, non il tuo desktop**: i 1 047 fotogrammi dicono che
la catena regge a 30/s, ⛔ **non** che il *tuo* desktop ti sembrerà fluido. **Quella domanda te la
porti tu, ed è tutto il punto.**

---

## 6. ⚠ Una cosa da sapere mentre guardi

Il prodotto sceglie il codec **negoziandolo col browser**. Stanotte è stato scoperto che per giorni
ha negoziato **AV1 in software** per via di una riga in un banco, e che **AV1 in hardware su questa
macchina non esiste**. ⇒ Se domattina la sessione dovesse negoziare AV1, **quel che stai guardando è
il prodotto col freno a mano**, e va detto **prima** che tu dia il giudizio — non dopo.

⭐ **Te lo dirò io, letto dal registro della tua sessione**, non da un'aspettativa.
