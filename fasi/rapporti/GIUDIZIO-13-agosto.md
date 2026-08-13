# Il giudizio dell'utente del 13 agosto 2026 — la prova su disco

*⛔ Questo file esiste perché la misura che chiude la fase 2 è **un giudizio**, e un giudizio senza
provenienza è un ricordo. Qui c'è la scena, il registro verbatim, le impronte e ⭐ **la misura fatta
sui pixel dello scatto**. Il gemello della fase 1 è [`GIUDIZIO-11-agosto.md`](GIUDIZIO-11-agosto.md).*

---

## La scena

| | |
|---|---|
| **chi guarda** | l'utente, dal portatile **CHUWI — 192.168.0.3**, entrato **come sé stesso** (`utente=nicfio`) |
| **che cosa apre** | `https://192.168.0.2:7561/` in **Chrome** — ⭐ la versione sta nello scatto: la scheda si chiama `REMOTIX` e la barra dice `Non sicuro` (il certificato autofirmato, com'è previsto) |
| **il bersaglio** | ⭐ **il PRODOTTO**, `/media/REMOTIX/src/remotix/remotix`, binario `131a33288c96ce5f…`, pagina `8bf84aa244d3eb8c…` — ⛔ e quella pagina è **byte per byte** `src/pagina.html` del deposito, dopo la cura del riscalamento `dc2f6a9` |
| **quando** | ⭐ `[M]` **2026-08-13**, sessione aperta alle **08:45:44 UTC**; lo scatto è delle **10:45:52 CEST**, cioè **otto secondi dopo** |
| **il registro** | `/media/REMOTIX/tmp/02-montaggio/registro.log`, righe 1556-1627, copiate qui sotto verbatim |
| **lo scatto** | `~/Immagini/Screenshots/Screenshot From 2026-08-13 10-45-52.png`, sha256 `5df4f5cef0b2f200…`, 2560×1048. ⚠ **Sta fuori dall'albero**, come i due dell'11 agosto: se serve domani, va portato dentro |

---

## Il registro del server, verbatim

```
08:45:36.914 pagina  GET / da 192.168.0.3:40580
08:45:37.173 pagina  GET /favicon.ico da 192.168.0.3:40588
08:45:43.287 pagina  GET /impronta da 192.168.0.3:34498
08:45:44.380 rcp     sessione aperta utente=nicfio via=[192.168.0.3]:35955 tela=1920x1080 vista=2545x927 disposizione=it
08:45:44.380 rcp     fotogramma 1 SPEDITO: CHIAVE 0x0301, codec 2, 1920x1080, 9746 byte di dati, stream 15, FIN (§6.2: completo) — spediti 1, abbandonati 0
```

---

## ⭐⭐ E QUESTA VOLTA IL GIUDIZIO NON È SOLO UNA FRASE: I PIXEL SONO STATI MISURATI

⛔ *La fase 1 si chiuse su una frase e su due schermate che nessuno ha misurato. Qui lo scatto è stato
**letto pixel per pixel**, e il numero che ne esce si confronta con quel che il server dichiara — che
è la sola forma di verifica che un giudizio umano ammette.*

| dal registro del server | dai pixel dello scatto |
|---|---|
| `vista=2545x927` — quel che **il client ha dichiarato** al server | la zona dipinta è alta **927 px**, misurata sul bordo della banda nera. ⭐ **Identico** |
| `tela=1920x1080` — quel che **il server ha concesso** | la zona dipinta è larga **1648 px**: `927 × 16/9 = 1646,2`. ⭐ Il rapporto misurato è **1,7778** contro un 16:9 di **1,7778** |

⇒ ⭐⭐ **La pagina riscala alla vista rispettando la proporzione, e non di un pixel storta.** È
`SPECIFICHE.md` §6.1 misurata sul vetro, non dichiarata.

⇒ ⛔ **E le bande nere non sono un difetto**: 448 px a sinistra e 464 a destra sono la conseguenza
aritmetica di una finestra **2545×927** — rapporto **2,74** — che ospita una tela **16:9**.
L'alternativa sarebbe **stirare** l'immagine, che §6.1 vieta.

⚠ **Il confronto con la mattina, sugli stessi scatti**: alle **09:40** la zona dipinta era il **60%**
della larghezza della finestra; alle **10:45** è il **64%**, e in più riempie **tutta** l'altezza. La
cura delle 08:56 ha fatto quel che prometteva.

---

## ⛔ E lo scatto ha trovato una cosa che nessun banco aveva sollevato

**La tela è 1920×1080 e viene dipinta a 1648×927: l'utente guarda il proprio desktop rimpicciolito
all'86%**, su un monitor che è largo **2560**.

⛔ Non è un difetto del riscalamento — che fa la cosa giusta — ed è **la `[?]` sulla risoluzione**:
`1920×1080` è stato **ereditato dalla scena di un banco, senza decisione né misura**, e `grep 1920
DECISIONI.md` non trova niente che lo fissi. **In v1 la tela era `2560×1080`**, che su questo schermo
riempirebbe la finestra invece di lasciare **912 px di nero**.

⇒ ⚠ **Resta aperta e dichiarata**, ed è una decisione dell'utente, non un rilievo: è la tela di tutte
le fasi che vengono dopo.

---

## ⚠ Che cosa questo giro NON è

⛔ **Non è un banco.** Non ha un atteso confrontato da una macchina (**B0.4**), non ha un controllo che
dica *no*, e non è rieseguibile senza una persona. È **I8** — *il metro è quel che l'utente vede* — e
vale per quello che è: **la sola prova che un essere umano ha guardato la cosa funzionare**.

⭐ Con una differenza dalla fase 1, e va scritta: **la metà misurabile di questo giudizio è stata
misurata**. `vista=2545x927` contro 927 px sul vetro non è un'impressione.

---

## ⛔ Che cosa era dichiarato aperto NEL MOMENTO del giudizio

*Perché un giudizio dato senza sapere che cosa manca non è un giudizio: è un'approvazione al buio.
Queste sono state messe davanti all'utente **prima** che decidesse.*

| | |
|---|---|
| ⛔ **il metro dice BOCCIATO sulla scena naturale** | 58,62 dB, rosso su **M5**, **8 guasti su 12**. Il PROMOSSO a 62,09 dB è del giro **con la mira a sfondo** |
| ⛔ **il metro non guarda a monte della cattura** | quale monitor, quale sessione, **quale utente** sono fuori dalla sua portata: il difetto «il desktop di un altro utente» **passerebbe con 62 dB** |
| ⛔ **«due utenti, ciascuno vede la propria sessione» non lo copre nessun banco** | `02-figlio-prova.py` prova la metà **negativa**; la positiva no |
| ⛔ **i dieci bit sono otto promossi, a tutt'e due i capi** | `DECISIONI.md` §2.3-ter alla sorgente, e `copyTo` a 4 byte per pixel sul telefono |
| ⛔ **il telefono non è misurato sull'hardware** | senza cavo dati non si legge il nome del decodificatore, e il criterio A/B esce `valido: false` |
| ⛔ **il piano 2 del metro non è applicabile** | la catena intera, *pagina ⟷ cattura*, **non è stata giudicata** |
| ⛔ **la risoluzione `1920×1080`** | ereditata senza decisione, e questo scatto la mette in discussione (sopra) |

⭐ **E il catalogo era pieno**: **15 su 15**, conto del **progetto** — le due copie del registro unite
e rispecchiate, 90 giri, *nessuna riga persa, nessuna inventata*.

---

## Il giudizio

⭐⭐⭐ **La fase 2 è chiusa sul giudizio dell'utente, il 13 agosto 2026.**

L'utente ha riaperto `https://192.168.0.2:7561/` dopo la cura del riscalamento, ha consegnato lo
scatto come risultato, e — messe davanti le sette cose dichiarate aperte qui sopra — ha deciso di
**chiudere la fase adesso**, con quelle scritte come aperte.

⚠ *Si scrive quel che è successo e non una frase che non è stata detta: il verdetto dell'11 agosto
era una citazione (**«Va bene, la stretta di mano funziona: fase 1 approvata»**), questo è una
**decisione presa davanti a un elenco**. Le due cose hanno lo stesso valore e non la stessa forma, e
confonderle sarebbe la forma **E8** applicata a un giudizio.*

⭐ La frase che l'utente aveva detto la mattina, davanti alla prima immagine, sta in
[`../02-primo-fotogramma.md`](../02-primo-fotogramma.md): **«È lo sfondo GNOME, è OK.»**
