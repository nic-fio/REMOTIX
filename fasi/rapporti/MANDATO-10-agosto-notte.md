# MANDATO — la revisione avversariale della notte del 10 agosto 2026

*Scritto **prima** che i cinque agenti consegnino, perché un mandato scritto dopo si adatta a quel
che è stato prodotto — e allora non è più un mandato, è un commento.*

---

## 0. Che cosa è stato sviluppato stanotte, e da chi

Cinque agenti in parallelo, con la proprietà dei file divisa perché non si pestassero i piedi:

| # | Che cosa | File suoi |
|---|---|---|
| 1 | **il ban lato ospite** (la pagina che dice «tentativi esauriti», il caricamento del file dei ban, il comando di sblocco) e **B8 riscritto** | `banchi/01-b8-*`, `banchi/01-b3-rcp-innesta.py` |
| 2 | ⭐ **il binario di prodotto**: il server nostro, che oggi non esiste — tutto quel che parla RCP è innestato con uno script nel server d'esempio di `ngtcp2` | `src/` |
| 3 | **i banchi non finiti**: B6, B9, B12, B13, C2 | `banchi/01-b6-*`, `01-b9-*`, `01-b12-*`, `01-b13-*`, `01-c2-*` |
| 4 | **le misure della sonda**: S7 e S1b eseguibili, le altre no — il ferro non c'è | `banchi/01-s*`, `web/rapporti/` |
| 5 | **le tre decisioni aperte** e i rilievi `R11` rimasti | i `.md` alla radice e in `fasi/` |

---

## 1. Il ruolo, e non è quello di controllare i compiti

`REVIEWER.md` §0: **trovi contraddizioni, non verità.** Il verdetto ha sempre la forma
*«questo contraddice X»*, mai *«questo è giusto»*, e una revisione verde è **«non ho trovato
niente»** — non un'assoluzione.

⛔ **E qui pesa più del solito**, per tre ragioni che si sommano:

1. il codice di stanotte è stato scritto **da cinque mani diverse che non si sono parlate**. Dove due
   di loro hanno fatto la stessa cosa in due modi, nessuno se ne è accorto;
2. buttando RDP il progetto ha perso l'arbitro esterno (`PIANO.md` §0.4): **due programmi scritti
   dalla stessa mano che vanno d'accordo non confermano niente**;
3. ⛔ **il banco è il primo imputato** (`REVIEWER.md` §1). Un difetto nel prodotto lo trova un banco
   buono; un difetto nel banco non lo trova nessuno, **e avvelena ogni misura successiva perché dà
   fiducia**.

---

## 2. Le lenti, e sono quattro

Ciascun revisore ne prende **una sola**, e non legge i rapporti degli altri: una spiegazione del
perché una cosa è giusta **àncora** chi legge, e trasforma la ricerca di contraddizioni in una
verifica di coerenza con la spiegazione (`PIANO.md` §0.4).

| Lente | Che cosa cerca |
|---|---|
| **A — il banco come strumento** | i banchi di stanotte sanno diventare **rossi**? dichiarano il denominatore? distinguono lo zero dal fallimento? hanno il controllo che dice *no*? un verdetto su zero cose passa? |
| **B — il prodotto contro l'arbitro** | il codice nuovo contraddice `RCP.md`? Riga per riga, con il byte che uscirebbe sul filo |
| **C — la coerenza fra i documenti e quel che è stato fatto** | i `.md` dichiarano cose che il codice non fa, o tacciono cose che il codice fa? le `[?]` sono state promosse a fatti in silenzio? i numeri hanno la data, la scena e la provenienza? |
| **D — le cuciture fra i cinque** | ⭐ **la lente che nessuna revisione precedente ha avuto**: cinque agenti, cinque pezzi che devono combaciare. Il ban lo scrive uno e lo chiama un altro; il banco di uno misura il prodotto di un altro; il documento di uno dichiara il numero di un altro |

---

## 3. Le forme d'errore da cui partire, perché sono già state pagate

Il catalogo intero sta in `REVIEWER.md` §2 (E1-E11). Queste tre sono quelle che questo progetto ha
ripagato **più volte**, e valgono come lista di caccia:

- **E1 — necessario scambiato per sufficiente**: *«il flag c'è ⇒ la funzione c'è»*, *«ha aperto un
  render node ⇒ rende in GPU»*, *«il file esiste ⇒ è quello che ho appena costruito»*;
- **E8 — il silenzio scambiato per zero**: «vuoto» e «proibito» hanno la stessa faccia. `[M]` sette
  volte in quattro giorni, l'ultima su un controllo di sanità;
- **E5 — un fatto che era una deduzione mai misurata**: una riga scritta con accanto una ragione che
  nessuno ha verificato.

⛔ **E la settima veste, che è la più cara**: un banco che **accusa il codice sbagliato**. Quando un
banco è rosso e la cosa che misura sembra funzionare, **il primo sospetto resta sulla misura**.

---

## 4. Le cinque domande al banco (`REVIEWER.md` §1)

1. la scena si dichiara e si muove sempre?
2. il banco è **certificato** prima di essere usato — cioè qualcuno ha costruito il guasto e l'ha
   visto diventare rosso?
3. riproduce davvero il difetto, o è verde perché non guarda?
4. distingue **lo zero dal fallimento**?
5. ha un **controllo positivo** — lo strumento sa trovare qualcosa che c'è di sicuro?

---

## 5. La forma di ogni rilievo, e senza questa non è un rilievo

```
DOVE:              file e riga
COSA CONTRADDICE:  una lezione (LEZIONI.md §x), una regola, un invariante (I1..I8),
                   una riga di RCP.md, o un altro pezzo di codice
COME SI DIMOSTRA:  il caso concreto — un ingresso, non un'ipotesi
MARCA:             [R] contraddizione confermata da una regola già scritta
                   [?] sospetto non ancora confermato
                   [M] solo se hai potuto eseguirlo
```

⛔ **Un rilievo senza «come si dimostra» è un'ipotesi, non un difetto.**

⭐ **E si scrive anche quel che si è provato a rompere senza riuscirci**: è informazione, e impedisce
al prossimo di rifare la stessa caccia.

---

## 6. Che cosa NON deve fare il revisore

- **non misura** — la misura è del coder, sul ferro;
- **non riscrive** — trova e segnala; chi riscrive perde la distanza che gli permette di trovare;
- **non approva per assenza di difetti**;
- ⛔ **non supplisce**: se un pezzo omette un'informazione e un altro la copre in silenzio, lo segnala
  lo stesso. **L'indulgenza che nasconde è esattamente ciò che deve togliere.**
