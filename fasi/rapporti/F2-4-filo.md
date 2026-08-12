# F2.4 — Il filo: RCP porta un fotogramma

*Sotto-fase 4 della fase 2 «Il primo fotogramma». Aperta e scritta il **12 agosto 2026**.*
*Mandato: `fasi/rapporti/MANDATO-12-agosto-fase2.md`. Porta assegnata: **7514**.*

---

## Che cosa deve produrre

**Un fotogramma codificato che arriva dal server alla pagina dentro RCP, senza che il protocollo
diventi qualcosa che nessuno ha scritto.**

⛔ E in termini di che cosa il banco misura, che è la parte che conta: **non** «il desktop compare
nella scheda». Quella prova è verde anche quando server e pagina hanno capito `RCP.md` **nello stesso
modo sbagliato** — che è precisamente il difetto muto contro cui `RCP.md` §0 esiste. Il banco di
questa sotto-fase misura **i byte contro il documento**: un terzo lettore, in un terzo linguaggio,
che giudica il fotogramma leggendo solo `RCP.md`.

⭐ **E la risposta più importante della sotto-fase è che la fase 2 non aggiunge un byte al
protocollo.** `RCP.md` §6.2 definisce il fotogramma da prima del primo byte di codice: 28 byte di
intestazione, i due tipi, il codec, la misura, il numero, l'istante, l'input. ⛔ Il che è
obbligatorio oltre che comodo: la clausola di §9 è **consumata dal 10 agosto 2026** e nessun tipo di
messaggio nuovo può più entrare in RCP/1.

---

## ⛔ Il banco — scritto prima del prodotto

### Lo stato del prodotto, contato prima di cominciare

| | |
|---|---|
| `grep -c '0x0301\|0x0302' src/rcp.c src/webtransport.c src/pagina.html` | **0 · 0 · 0** `[M]` 12 ago 2026 |
| `grep -c 'VideoDecoder' src/pagina.html` | **0** `[M]` |

⇒ Non esiste un byte di video nel prodotto. È il momento in cui `PIANO.md` §0.4 momento 1 vuole il
banco, e ⛔ **il banco è stato costruito in modo da poter girare senza il prodotto**: il giudice del
fotogramma e l'arbitro delle registrazioni non hanno nessuna dipendenza — né rete, né `aioquic`, né
server. Non è una comodità: un banco che per esistere pretendesse il prodotto sarebbe scritto
**dopo**, cioè sapendo che cosa il prodotto fa.

### La scena, dichiarata

⚠ **E qui la scena è FERMA, contro `CODER.md` §3.2** — *«la scena si dichiara, e si muove sempre»*.
Va detto invece di essere fatto di nascosto: la fase 2 consegna **un'immagine ferma** (`PIANO.md`
«Fase 2»), quindi la scena ferma **è il soggetto**, non una distrazione. Dalla fase 3 — «Il
movimento» — quella regola torna a valere senza sconti, e il banco del credito degli stream oltre i
256 fotogrammi (`RCP.md` §2.3, §11) è dichiarato **saltato** qui, con il suo perché.

Per i pezzi che girano oggi la scena è: *nessuna rete e nessun server; i fotogrammi li fabbrica il
banco, e il giudice li legge **a pezzi**, come arriverebbero da uno stream QUIC — senza tenerli in
memoria.*

### Che cosa si conta, e sono quattro esiti non due

⛔ `RCP.md` chiede al client **tre** comportamenti diversi, e confonderli è la forma d'errore **E8**:

| esito | che cosa vuol dire | dove |
|---|---|---|
| `ACCETTATO` | si consegna al decodificatore | §6.2 |
| `SCARTATO` | ⛔ si **butta**, **non** si consegna, si tratta come un buco — e ⛔ **la sessione resta viva** | §6.2, §5.1, §5.2 |
| `ERRORE_PROTOCOLLO` | la connessione cade, col motivo | §3, §3.1 |

⚠ **Un banco a due esiti promuove `SCARTATO` a caduta della sessione**, cioè fa fallire il caso
normale di §5.1 — il server che abbandona un fotogramma di proposito.

⭐ **E il quarto esito è nuovo, e non c'era in nessun banco della fase 1: `AMBIGUO`.**
`fasi/01-filo-nudo.md` §«I dodici punti in cui `RCP.md` ammette due letture» è l'esito più prezioso
di B9 — e li ha trovati un programma scritto apposta, **dopo**. Qui il quarto esito è dentro il banco
che gira ogni giorno: un caso `AMBIGUO` non fa fallire il giro (nessuno ha sbagliato) ⛔ ma si conta,
si stampa in fondo, e porta **il testo pronto** della cura. Un'ambiguità segnalata senza la cura è
un reclamo.

### I numeri attesi, scritti PRIMA del giro

`python3 banchi/02-filo-fotogramma.py --elenco` li stampa tutti. Il riassunto:

| | atteso | misurato `[M]` 12 ago 2026 |
|---|---|---|
| casi del giudice del fotogramma | 27 — **11** violazioni · **4** scarti · **8** verdi attesi · **4** ambiguità | **27 su 27** come previsto |
| registrazioni di prova per l'arbitro | 6, con il codice d'uscita di ciascuna dichiarato | **6 su 6** |
| certificazione del giudice | sano **0** → guasto **>0 con la marca** → risanato **0**, per 3 guasti | **3 su 3** |
| certificazione dell'arbitro | sano **0** → G4 **>0** → risanato **0** | **1 su 1** |
| casi verso il server | 5 — 3 violazioni, 2 verdi attesi | ⏳ **non girati**: manca il prodotto |

### Il controllo positivo

⛔ **In coda a ogni esecuzione del giudice**, e a costo zero: si innesta **G2** — un guasto che *non
rompe niente di visibile*, un valore in più in un `set` — e si verifica che il caso `tipo-0x0300`
diventi rosso. ⚠ E si guardano **tutt'e due i giri**: se quel caso fosse rosso anche a giudice sano,
il verde di poco prima non varrebbe niente.

⛔ **E per l'arbitro** è quello che `RCP.md` §11 detta alla lettera: gli si dà una registrazione **con
un errore dentro** e si verifica che lo veda (uscita 1), e una **senza un byte di video** e si
verifica che dica «niente da giudicare» (uscita 3) — ⭐ la metà che si dimentica, perché un arbitro
che uscisse 0 lì **assolverebbe senza aver guardato**.

### Il caso opposto — che aspetto avrebbe il contrario

| se il banco fosse rotto così | come lo si vedrebbe |
|---|---|
| il giudice legge l'intestazione di **32** byte (G1) | 4 casi rossi, e la marca *«l'intestazione ne vuole 32»* — ⭐ una marca che dice **il numero sbagliato**, non solo «un caso è rosso»: distingue il rosso del guasto dal rosso di un banco che crolla |
| il giudice è indulgente su `tipo` (G2) | tutti i fotogrammi buoni continuano a passare, e **solo** `tipo-0x0300` diventa `ERRORE_PROTOCOLLO → ACCETTATO`. ⚠ Un banco fatto di soli verdi attesi resterebbe verde |
| uno stream azzerato letto come uno chiuso con FIN (G3) | `reset-a-meta` diventa `SCARTATO → ACCETTATO`: i 10 KB di un fotogramma abbandonato finiscono al decodificatore |
| l'arbitro salta il canale video (G4) | le registrazioni che devono uscire **1** escono **3**. ⛔ E **non 0**: un arbitro cieco non assolve, dichiara di non aver guardato — se uscisse 0 il guasto sarebbe invisibile |

⭐ **G4 non è un guasto inventato: è lo stato di oggi di `01-b4-validatore.py`**, la sua riga 521
(`if canale != 0x00: … continue`, verificata `[M]`). Certificare contro quel guasto è l'unico modo
di dimostrare che il nuovo arbitro **aggiunge** qualcosa invece di ripetere B4 con altre parole.

---

## Le risposte alle quattro domande del mandato

### 1. Su quale stream viaggia il fotogramma

**Uno stream unidirezionale nuovo, aperto dal server, uno per fotogramma.** `[S]` §2.5 tabella, §5
tabella, §5.1.

- ⛔ **non** quello della sessione: §2.5 dice che il controllo vive solo sul primo stream
  bidirezionale, e il server non apre stream bidirezionali affatto;
- ⛔ **non** un datagram: §2.5 mette l'audio (`0x04`) come «solo su datagram» e il video non ci
  compare; e un fotogramma non ci starebbe — §5.3 dice che il carico utile di un datagram su un
  percorso vero è **~1200 byte** `[S]`, contro un tetto di 16 MiB per fotogramma;
- ⭐ e il canale si riconosce dal **byte alto di `tipo`**, mai dal numero dello stream: è la cura del
  rilievo R11.9, e il banco la esercita.

⚠ **Ma §2.5 non chiude il caso simmetrico**, ed è la proposta **P3**: per `0x00` la tabella dice «su
uno stream unidirezionale è `ERRORE_PROTOCOLLO`», per `0x04` dice «su uno stream è
`ERRORE_PROTOCOLLO`», e per il video **non dice su che stream viva**. Un server che scrivesse
l'intestazione di 28 byte sul canale di controllo — l'unico posto in cui può, visto che gli stream
bidirezionali li apre il client — non violerebbe nessuna riga, e il client leggerebbe quei 28 byte
con l'inquadratura di §6.1, cioè come un messaggio inventato.

### 2. Che intestazione porta

⭐ **Tutto quel che il mandato chiedeva c'è già, e da prima del primo byte di codice** — §6.2:

```
 0        2        4        8        12       16       24       28   28+…
 │ tipo   │ codec  │ largh. │ altezza│ numero │ istante│ input  │ dati│
 │ u16    │ u16    │ u32    │ u32    │ u32    │ u64    │ u32    │     │
```

| la domanda | il campo |
|---|---|
| **le dimensioni** | `largh.`, `altezza` |
| **il formato** | `codec`: 1 = HEVC, 2 = AV1, e **DEVE** essere quello negoziato in §4.3 |
| **se è chiave** | `tipo`: `0x0301` chiave, `0x0302` delta |
| **la marca temporale** | `istante`: microsecondi dell'orologio **monotono del server** alla cattura. ⛔ Non è un'ora, e il client **NON DEVE** confrontarlo col proprio |

E in più: `numero` (contatore dei fotogrammi catturati, **compresi quelli abbandonati**) e `input`
(l'identificatore dell'ultimo input iniettato prima della cattura, 0 se nessuno).

⛔ **28 byte esatti, senza un byte di riempimento**, e non è pedanteria: il disegno diceva `… 24 │ 32`
fino al 9 agosto 2026 — quattro byte di riempimento mai dichiarati, che due implementazioni potevano
indovinare uguale senza che nessuno se ne accorgesse. È il difetto muto contro cui `RCP.md` è stato
scritto, e il campo lo ha già subìto una volta.

`[?]` **La profondità di colore non sta nell'intestazione**, mentre il codec sì — e tutt'e due sono
negoziati in §4.3. È un'asimmetria, non necessariamente un difetto: la profondità la porta la SPS
dell'HEVC, e §9 vieta comunque di aggiungere campi a un messaggio esistente. **Non è stata misurata**
e non si propone niente: si dichiara.

### 3. Che cosa succede se arriva prima di `SESSIONE` — I3

⛔ **Il verdetto è `ERRORE_PROTOCOLLO`, e il banco lo applica — ma è DERIVATO, non citato.**

Si ricava da §1 (*«l'ordine dei cinque passi non ammette permute … un messaggio che arriva in uno
stato in cui non è previsto è `ERRORE_PROTOCOLLO`»*), da §3 (*«un messaggio arrivato nello stato
sbagliato della macchina»*) e dall'invariante **I3** di `CODER.md` §2 (*«chi non passa dal validatore
non riceve un pixel»*).

⚠ **E l'asimmetria che invita alla lettura opposta è dentro §2.5**: per il canale di **input** la
stessa tabella scrive *«aperto ⛔ **dopo aver ricevuto `SESSIONE`** e tenuto aperto»*; per il video
non scrive niente. Chi legge le due righe una sotto l'altra ha un motivo per concludere che la
differenza sia voluta.

⛔ **E metà della regola manca davvero**: §3 dice che cosa fa **chi riceve**. Nessuna riga dice al
**server** di non aprire uno stream video prima di aver spedito `SESSIONE`. È la proposta **P1**, ed
è I3 scritta dalla parte in cui I3 si applica.

### 4. Come si rifiuta un fotogramma malformato

`RCP.md` §3.1, e i punti sono tre **in quest'ordine**: (1) nel registro, *che cosa* non si è capito;
(2) `CONGEDO(ERRORE_PROTOCOLLO)` sul canale di controllo, ⛔ **se il canale è ancora utilizzabile**;
(3) la chiusura della **sessione WebTransport** col codice d'errore applicativo pari al motivo — ⛔ e
questo è un `DEVE` **incondizionato**, ed è quello che §3.1 chiama *«quello che salva le diagnosi»*.

Il cliente di prova li esercita tutti e tre: è la metà del protocollo che nessun banco del server può
vedere, perché qui a dover chiudere è **il client**.

⚠ **E c'è un caso che NON è un rifiuto e va tenuto separato**: uno stream **azzerato**. §6.2, rilievo
R1.7: il fotogramma è incompleto, si butta, non si consegna al decodificatore, si tratta come un buco
— **e la sessione regge**. Il giudice del banco guarda il `RESET_STREAM` **prima ancora**
dell'intestazione, perché i byte di un'intestazione troncata possono essere qualunque cosa, e
leggerli darebbe `ERRORE_PROTOCOLLO` su un abbandono legale.

---

## ⛔ La verifica su `RCP.md` §12

*Il mandato chiedeva di andare a vedere se §12 esista davvero, perché `PIANO.md` lo cita.*

| | |
|---|---|
| **§12 esiste** | `RCP.md` riga 1950, titolo «⏳ Quel che RCP/1 lascia aperto, dichiarato» `[M]` |
| **chi lo cita** | `PIANO.md` riga 187, riquadro di §1.2: *«⛔ **S4** vuole un server che spedisca fotogrammi codificati … e pretende pure **una riga di protocollo** (`RCP.md` §12)»* |
| ⛔ **e la riga di protocollo NON è in §12** | in §12 quella voce è **cancellata**: *«~~la funzione di banco dell'anello del ritardo~~ — ⭐ **chiusa la notte del 9 agosto 2026**, poche ore dopo essere stata aperta dal rilievo R3.4: è **§7.5**, due tipi nuovi — `BANCO_MARCA` e `BANCO_ESITO`»* |

⇒ **Chi segue il rimando di `PIANO.md` arriva in un elenco di cose aperte e trova la sua voce
sbarrata**, con la definizione altrove. La riga di protocollo che S4 pretende è **normativa in §7.5**
(`0x000F` e `0x0010`), è entrata *con l'ultima occasione* prima che §9 chiudesse la finestra, e vale
oggi come **funzione di banco dichiarata** — ⛔ che dall'11 agosto 2026 **non deve esistere nel
binario consegnato**: non spenta, *assente*.

⚠ **E il precedente dice che questo tipo di rimando fa danni**: §12 stesso porta la correzione della
sera dell'11 agosto in cui *«due sezioni dell'arbitro davano due stati diversi alla stessa domanda, e
chi si fosse fidato di §12 avrebbe scritto un server senza quel tetto restando convinto di essere
conforme»*. Qui non è `RCP.md` a contraddirsi — §12 è corretto, la voce è giustamente sbarrata — è
**`PIANO.md` che manda al posto sbagliato**. La cura è una riga in `PIANO.md`, non in `RCP.md`, e sta
nelle cuciture.

---

## Che cosa si riusa — file e righe vere, contate

⛔ *`[M]` 12 agosto 2026, `wc -l`. Non le cifre di un piano ricopiate.*

| file | righe | come si riusa |
|---|---|---|
| `banchi/01-b3-cliente.py` | **506** | ⭐ **si importa, non si ricopia**: la classe `Cliente` di F2.4 ne **eredita**. Dentro c'è la riga che impedisce di dare gli eventi del canale di controllo allo strato HTTP/3 di `aioquic` — senza la quale la connessione muore per mano del **client** (`[M]` 10 ago 2026) — e una copia divergente riporterebbe quel difetto travestito da difetto del server |
| `banchi/01-b4-validatore.py` | **633** | ⛔ **non si tocca** (è della fase 1, mandato §2). Se ne riusa la **forma**: i quattro codici d'uscita, i denominatori, i due scostamenti di §11.1, la distinzione fra `Malformata` e `NonConforme`. E la sua **riga 521** diventa il guasto G4 |
| `banchi/01-b5-violazioni.py` | **1321** | se ne riusa la **forma**: la tabella dei casi con l'atteso dichiarato prima, i ⭐ verdi attesi, i conteggi con il denominatore calcolato e mai scritto a mano, il `--elenco` che stampa le previsioni senza misurare |
| `banchi/01-b12-guasti.py` | **(catalogo)** | la forma della riga di certificazione, e ⛔ il criterio della marca a **due metà** (rilievo R12-A.3) |
| `RCP.md` | **1971** | l'arbitro. §2.5, §3, §3.1, §5.1, §5.2, §6.0, §6.2, §7.1, §9, §11, §11.1, §12 |

**Quel che questa sotto-fase ha scritto** `[M]`:

| file | righe |
|---|---|
| `banchi/02-filo-fotogramma.py` | 1189 — il giudice del fotogramma, i 27 casi, i 3 guasti, le proposte |
| `banchi/02-filo-validatore.py` | 605 — l'arbitro del canale video sulle registrazioni di §11.1 |
| `banchi/02-filo-cliente.py` | 554 — il cliente di prova che riceve e giudica ⏳ |
| `banchi/02-filo-lancia.sh` | 250 — il giro, con lo stato iniziale verificato |
| `banchi/02-filo-esiti.jsonl` | il registro, una riga per giro |
| `banchi/02-filo-prove/*.rcpreg` | 6 registrazioni di prova, fabbricate dal banco |

---

## ⛔ Le trappole già pagate che mordono qui

| trappola | dove sta scritta | come morde qui, e che cosa fa il banco |
|---|---|---|
| **E8** — il silenzio scambiato per zero | `REVIEWER.md` §2, `LEZIONI.md` §1.9 | ⛔ è la trappola **centrale** di questa sotto-fase, ed è già stata pagata su questo esatto campo: senza le due parole di §6.2 *«ma solo se lo stream è finito con un FIN»* (rilievo R1.7, 9 ago) *«un fotogramma abbandonato e uno completo avevano lo stesso aspetto»*. ⇒ il guasto **G3** la riproduce, e l'arbitro **dichiara** i flussi di cui non ha potuto giudicare la completezza invece di darli per buoni |
| **E7** — si verifica dal lato che invia | `REVIEWER.md` §2, `LEZIONI.md` §1.7 | in v1 il server scriveva «congedo il client» e il client «errore di rete», **per tre fasi**. ⇒ il cliente di prova giudica **dal lato che riceve**, e il verdetto non si legge mai dal registro del server |
| **E1** — necessario preso per sufficiente | `LEZIONI.md` §1.11 | *«è arrivato uno stream ⇒ è arrivato un fotogramma»*. ⇒ il banco conta i **flussi giudicati** e i **byte**, e zero fotogrammi ha un codice d'uscita suo (`5`) |
| **E10** — una prova verde sul client sbagliato | `LEZIONI.md` §0.3, §2.1 | ⇒ il cliente di prova è in un **terzo linguaggio** e legge **solo** `RCP.md`; e la pagina gira su tre motori scritti da tre squadre che non ci conoscono (`PIANO.md` §1.1) |
| **un conteggio senza denominatore** | `LEZIONI.md` §1.9, rilievo R7.4 | *«nessuna violazione»* è vero anche su zero fotogrammi. ⇒ quattro denominatori nell'arbitro, tre nel giudice, e «saltato» conta nel verdetto dello script di lancio |
| **il banco che accusa il prodotto** | `LEZIONI.md` §10, `PIANO.md` §0.4 | ⇒ vedi «Che cosa NON ha funzionato»: è successo al primo giro |
| **la redirezione attorno a `ssh`/`enter.sh`** | `fasi/00-ambiente.md` B3.3 | pagata **quattro volte**, due nella sola notte dell'11 agosto, e due di quelle **dentro i file che la descrivono in testa**. ⇒ `02-filo-lancia.sh` non ne ha, e lo dichiara in testa |
| **B0.1** — lo stato iniziale dichiarato e verificato | `fasi/01-filo-nudo.md` | ⇒ lo script verifica che la **7514** sia libera, e se è occupata ⛔ **non spegne niente**: dichiara ed esce |
| **B0.4** — l'atteso lo confronta il banco | idem | ⇒ `pezzo()` confronta lo stato d'uscita, non lo stampa |
| **E11 / I7** — la protezione in una riga di configurazione | `REVIEWER.md` §2, `CODER.md` §2 | non morde qui: nessuna delle regole del video sta in una configurazione |

---

## ⛔ Che cosa NON ha funzionato

- ⛔ **Il primo giro del banco ha dato quattro rossi su quattro giudizi esatti**, e la colpa era del
  banco. Il confronto della regola citata era
  `v.regola.split(" (")[0] == c["regola"].split(" (")[0]`: pretendeva che il verdetto citasse
  **tutte** le sezioni che la previsione elenca, quindi `«RCP.md §6.2»` contro
  `«RCP.md §6.2, §5.1, §5.2»` era rosso — con `atteso ACCETTATO` e `visto ACCETTATO` sulla riga
  sopra. ⚠ È la forma che il progetto paga più spesso — *un rosso puntato sull'imputato sbagliato* —
  ed è costata poco solo perché il banco stampava *«esito giusto, REGOLA sbagliata»* invece di un
  rosso muto. ⭐ La cura è `sezione_principale()`: si pretende la sezione **portante**, e le altre
  sono contorno. Pretenderle tutte sarebbe pretendere una formulazione, non un giudizio.

- ⛔ **La prima certificazione ha fallito su due guasti su tre, e le marche erano sbagliate.** Per G2
  e G3 la marca era il **nome del caso** (`tipo-0x0300`, `reset-a-meta`), che sta nella riga stampata
  e non nel testo del verdetto — e `--certifica` gira in silenzio. ⚠ Ma la cura **non** era «cerchiamo
  anche nella riga stampata»: il nome del caso compare **anche nel giro sano**, dove quel caso passa,
  quindi avrebbe fallito la seconda metà del criterio di R12-A.3 (*la marca il giro sano NON la deve
  già dire*). ⭐ La marca giusta è `nome: atteso -> visto`: nel giro sano atteso e visto coincidono
  sempre, quindi `X: A -> B` con `A ≠ B` esiste **soltanto** quando qualcosa è rotto.

- ⚠ **`02-filo-cliente.py --elenco` moriva su CHUWI con `ModuleNotFoundError`**, perché importava
  `01-b3-cliente.py` in cima e quello importa `aioquic`, che sta solo dentro il contenitore. ⛔ E
  `--elenco` è precisamente quel che deve leggere **chi revisiona il banco prima che il prodotto
  esista**, cioè chi il contenitore non ce l'ha. Curato con un'importazione tardiva e una fabbrica per
  la classe. ⭐ `02-filo-fotogramma.py` invece non ha **nessuna** dipendenza, ed è voluto.

- ⚠ **Tre stringhe dello script di lancio contenevano backtick dentro le virgolette doppie**, e bash
  le eseguiva come comandi: `RCP.md: comando non trovato`. Innocuo, ma è la quarta veste di una
  famiglia già pagata tre volte nella fase 1 (*«tre trappole di shell in una sera, tutte la stessa»*).

- ⏳ **Il cliente di prova non è stato girato**, e non è una dimenticanza: non esiste un server che
  spedisca un fotogramma, e `aioquic` non è su CHUWI. ⛔ Il suo primo giro **è la prima misura della
  fase 2**, sulla 7514, dentro il contenitore.

---

## ⛔ Che cosa propongo a `RCP.md`

*⛔ Il documento **non è stato toccato**: lo tocca il coordinatore, alla fine, o sei agenti si
sovrascrivono l'arbitro. Qui c'è il testo esatto, pronto da incollare, col paragrafo che chiedo.*

⭐ **E nessuna di queste sette proposte aggiunge un tipo di messaggio, un motivo di congedo o un campo
a un messaggio esistente.** La clausola di §9 è consumata dal 10 agosto 2026, e ogni riga qui sotto
sta dentro quel divieto: sei sono **regole su campi che esistono già**, e la settima tocca il formato
della **registrazione**, che non è un messaggio e porta la propria versione nella magia.

⚠ **Quattro sono letture doppie vere** — due implementazioni conformi producono **byte diversi per lo
stesso ingresso** — e **tre sono regole derivate**: si ricavano da §3 e da §1, ma nessuna riga le
scrive, e il documento le scrive per casi analoghi. Confonderle gonfierebbe il conto: una regola
derivata non fa divergere due implementazioni attente, una lettura doppia sì.

---

### ⭐ P2 — `§6.2`, campo `numero` · **lettura doppia** · ⛔ la più grave

**Il caso concreto.** Il server spedisce il primo fotogramma con `numero = 0`. Il client lo
decodifica, poi si accorge di un buco e manda `RICHIEDI_CHIAVE(ultimo_numero = 0)`. ⛔ Il server non
può sapere se voglia dire *«ho decodificato il fotogramma 0»* o *«non ne ho decodificato nessuno»*.

**Perché è una contraddizione interna e non una lacuna** — tre righe di `RCP.md` che non stanno
insieme:

- §6.2: `numero` è *«contatore dei fotogrammi catturati, che cresce di uno per ogni fotogramma che il
  server decide di spedire»* — e **non dice da quanto parte**;
- §7.1: `RICHIEDI_CHIAVE.ultimo_numero` è *«l'ultimo fotogramma decodificato, **0 se nessuno**»*;
- §6.0: *«⛔ Ogni intero ha un solo significato di «assente», e va dichiarato dove serve: **non
  esistono valori sentinella impliciti**»*.

⭐ E la cura esiste già nel documento, tre sezioni più in là: §7.3 fa esattamente questo per l'`id`
dell'input — *«crescente, comincia da 1. ⛔ 0 è riservato e vuol dire "nessun input"»* — che è lo
stesso campo che torna indietro in `input` di §6.2.

> **Testo proposto**, da aggiungere alla riga `numero` della tabella dei campi di §6.2:
>
> ⛔ **Il primo fotogramma di una sessione porta `numero = 1`, e lo `0` è riservato**: vuol dire
> «nessun fotogramma», che è il significato che §7.1 gli dà in `RICHIEDI_CHIAVE`. ⚠ È la stessa
> convenzione dell'`id` dell'input (§7.3), e per la stessa ragione: senza, `RICHIEDI_CHIAVE(0)` vuol
> dire due cose e il server non può scegliere — cioè il valore sentinella implicito che §6.0 vieta.

---

### ⭐ P6 — `§5.2` · **lettura doppia** · ⛔ e morde proprio nella fase 2

**Il caso concreto.** Il server apre la sessione e spedisce come **primo** fotogramma un delta
(`0x0302`). ⛔ È conforme a **ogni riga** del documento, e la fase 2 — che consegna un'immagine ferma
— mostrerebbe spazzatura senza che nessuno abbia torto.

**E il client non ha modo di accorgersene**, che è la parte peggiore: §5.2 gli fa chiedere una chiave
*«quando si accorge di un buco nella successione dei `numero`, o quando il decodificatore rifiuta un
fotogramma»* — e qui non c'è nessun buco (è il primo), e §5.2 stesso dichiara `[S]` che *«a un delta
mancante il decodificatore **non solleva nessun errore**, si limita a produrre immagini via via più
sfasciate»*.

> **Testo proposto**, da aggiungere all'elenco «Le regole:» di §5.2, come primo punto:
>
> - ⛔ **il primo fotogramma che il server spedisce dopo `SESSIONE` DEVE essere una chiave**
>   (`0x0301`). ⚠ Senza questa riga un delta in apertura è conforme, e il client non ha modo di
>   accorgersene: non c'è nessun buco nella successione dei `numero`, e il decodificatore non
>   solleva errori. Il sintomo sarebbe *«il desktop compare a pezzi»*, e non nominerebbe né il
>   protocollo né la chiave.

---

### ⭐ P5 — `§6.2`, campi `largh.` e `altezza` · **lettura doppia**

**Il caso concreto.** La tela concessa in `SESSIONE` è 1920×1080 e arriva un fotogramma 1280×720. Il
client chiude la sessione, o riscala?

§6.2 dice *«⛔ In RCP/1 è **sempre** quella della tela, e il client riscala»*. ⚠ *«è sempre»*
**descrive**, non comanda — e §0 dichiara normativo solo ciò che porta **DEVE**, **NON DEVE**,
**PUÒ** — e nessuna riga dice **che cosa fa chi riceve**. Le due letture sono entrambe difendibili:
chiudere per §3 («un campo fuori intervallo»), o riscalare, che è quel che il client fa già per la
vista (`SPECIFICHE.md` §6.1).

> **Testo proposto**, a sostituzione della riga `largh.`, `altezza` di §6.2:
>
> | `largh.`, `altezza` | la misura di **questo** fotogramma. ⛔ In RCP/1 **DEVONO** valere la tela concessa in `SESSIONE` (§4.5), e chi ne riceve altre chiude con `ERRORE_PROTOCOLLO`: il client riscala alla **vista**, non alla tela (`SPECIFICHE.md` §6.1). Il campo esiste lo stesso perché il giorno in cui si decidesse di codificare più piccolo quando la finestra è piccola — `DECISIONI.md` §5.0-ter, che è una `[?]` volutamente fuori dal modello — **il protocollo non cambia**: cambierebbe questa riga |

---

### ⭐ P3 — `§2.5`, riga «video» · **lettura doppia**

**Il caso concreto.** Il server scrive l'intestazione di 28 byte sul **canale di controllo** — l'unico
posto in cui può, dato che §2.5 gli vieta di aprire stream bidirezionali e il canale di controllo
glielo ha aperto il client. Il client lo legge con l'inquadratura di §6.1 (`u16 tipo`, `u32
lunghezza`) e ne ricava un messaggio `0x0301` di lunghezza `0x00010000` — cioè un messaggio inventato
di 64 KiB.

§2.5 chiude questo caso **per due canali su cinque e non per il video**: per `0x00` dice *«su uno
stream unidirezionale è `ERRORE_PROTOCOLLO`»*, per `0x04` dice *«solo su datagram. Su uno stream è
`ERRORE_PROTOCOLLO`»*, per `0x03` dice soltanto che cosa segue il tipo.

> **Testo proposto**, a sostituzione della cella «Che cosa segue» della riga `0x03` di §2.5:
>
> | `0x03` | video | l'intestazione di 28 byte di §6.2, **senza** inquadratura — ⛔ e **solo su uno stream unidirezionale aperto dal server**: un `0x03` sul canale di controllo è `ERRORE_PROTOCOLLO`, come lo è un `0x00` su uno stream unidirezionale |

---

### P1 — `§2.5`, riga «video» · **regola derivata**, e la metà che manca è del server

**Il caso concreto.** Il server apre uno stream video dopo `AMMESSO` e prima di `SESSIONE`, cioè
prima che la tela sia concordata. Il client riceve un fotogramma di cui non conosce né la misura né
il codec.

Per **chi riceve** la regola si ricava: §1 (*«l'ordine dei cinque passi non ammette permute»*) più §3
(*«un messaggio arrivato nello stato sbagliato della macchina»*). ⛔ Per **chi manda** non si ricava
da nessuna parte, ed è l'invariante **I3** — *chi non passa dal validatore non riceve un pixel* —
lasciata senza una riga sul filo. ⚠ E §2.5 la scrive per il canale di input, due righe sopra.

> **Testo proposto**, a sostituzione della cella «Quanti» della riga «video» della tabella di §2.5:
>
> | **video** — unidirezionale | il server | uno **per fotogramma**, ⛔ e **nessuno prima di aver spedito `SESSIONE`**: chi ne riceve uno prima chiude con `ERRORE_PROTOCOLLO`. ⚠ È l'invariante **I3** sul filo — *chi non passa dal validatore non riceve un pixel* — e va scritta anche per chi **manda**, come lo è per il canale di input qui sotto |

---

### P4 — `§6.2` · **regola derivata**

**Il caso concreto.** Lo stream video si chiude con **FIN** dopo 12 byte. §6.2 dice *«la fine dello
stream è la fine del fotogramma»*: letta alla lettera, quello è un fotogramma con **meno sedici** byte
di dati. La regola si ricava da §3 (*«una lunghezza che non torna»*), ma §6.2 è il posto in cui chi
implementa la guarda.

> **Testo proposto**, da aggiungere all'elenco «⛔ **La regola, in due righe:**» di §6.2, come terza
> riga:
>
> - uno stream chiuso con **FIN prima dei 28 byte** dell'intestazione è `ERRORE_PROTOCOLLO`: non è un
>   fotogramma corto, è una lunghezza che non torna (§3).

---

### ⭐ P7 — `§11.1`, il blocco della registrazione · ⛔ **trovata dall'arbitro meccanico**

*E questa non l'ha trovata una rilettura: l'ha trovata `02-filo-validatore.py` provando a giudicare
una registrazione conforme, e non riuscendo a dire se il fotogramma fosse completo.*

⛔ **Il blocco di §11.1 non porta nessun campo che dica come è finito lo stream** — c'è `verso`,
`canale`, `stream`, `lunghezza`, gli intervalli oscurati, e il carico. E per il video quella è la
distinzione più importante che il documento abbia: §6.2, rilievo **R1.7** della sera del 9 agosto
2026, aggiunse due parole — *«ma solo se lo stream è finito con un FIN»* — perché senza di esse *«un
fotogramma abbandonato e uno completo avevano lo stesso aspetto»*, che il documento stesso classifica
come forma d'errore **E8**.

⇒ **La cura è stata scritta sul filo, e la registrazione la riapre.** Guardando un `.rcpreg`,
l'arbitro non può distinguere un fotogramma troncato perché il server lo ha **abbandonato di
proposito** (§5.1, legale, la sessione regge) da uno troncato perché il server **ha sbagliato** (§3,
la connessione cade). `[M]` sulla registrazione di prova conforme, l'arbitro dichiara *«di 1 su 1 NON
si è potuta giudicare la completezza»*.

⚠ È lo stesso buco che B9 aveva sfiorato sul canale di controllo — la lettura **L3**, *«il bit FIN del
frame STREAM che porta il `CONGEDO`: gli stessi byte di carico, un bit di trasporto in più»* — senza
dire che il formato della registrazione non sa scriverlo.

⭐ **E non tocca §9**: un blocco di registrazione non è un messaggio, e il formato porta già la propria
versione nella magia (`"RCPREG" 0x00 0x01`).

> **Testo proposto**, a sostituzione del disegno del blocco in §11.1:
>
> ```
> intestazione (16 byte)
>  ├── 8 byte   magia          "RCPREG" 0x00 0x02
>  ├── u32      quanti_blocchi
>  └── u32      riservato      DEVE essere 0
>
> poi `quanti_blocchi` blocchi, ciascuno:
>  ├── u8       verso          1 = client → server, 2 = server → client
>  ├── u8       canale         il byte alto di `tipo` (§2.5)
>  ├── u8       fine           ⛔ come si è chiuso lo stream DOPO questo blocco:
>  │                             0 = continua · 1 = FIN · 2 = RESET_STREAM
>  ├── u64      stream         l'identificatore dello stream QUIC
>  ├── u32      lunghezza      quanti byte di carico seguono — ⛔ la lunghezza VERA
>  ├── u16      quanti_oscurati
>  │     per ciascuno:
>  │       ├── u32   inizio        scostamento dentro il carico di questo blocco
>  │       ├── u32   quanti        ⛔ la lunghezza VERA dei byte sostituiti
>  │       └── 32 B  impronta      SHA-256 dei byte veri
>  └── `lunghezza` byte di carico
> ```
>
> ⛔ **E il campo `fine` non è un lusso.** Senza, un fotogramma **abbandonato** (§5.1, legale — il
> client butta e chiede una chiave) e uno **troncato per errore** (§3 — la connessione cade) hanno lo
> stesso aspetto nella registrazione: il validatore non può applicare la riga che §6.2 ha aggiunto
> apposta il 9 agosto 2026, ed è la forma **E8** rientrata dalla finestra. ⚠ La magia passa a
> `0x00 0x02` perché il blocco cambia misura: un validatore vecchio deve **rifiutare** il formato
> nuovo, non leggerlo di traverso.

---

### E una proposta che NON è per `RCP.md` — è per `PIANO.md`

⛔ `PIANO.md` riga 187 manda a `RCP.md` §12 per «una riga di protocollo», e in §12 quella voce è
sbarrata da tre giorni: vive in §7.5. Chi segue il rimando trova un elenco di cose aperte e la sua
voce cancellata.

> **Testo proposto** per la riga 187 di `PIANO.md`:
>
> | ⛔ **S4** | vuole un server che **spedisca fotogrammi codificati** e un decodificatore che li accetti: non è «senza prodotto», è **la fase 3** — e pretende pure **una riga di protocollo**, che ⭐ **c'è già**: è la funzione di banco di `RCP.md` **§7.5** (`BANCO_MARCA` `0x000F` e `BANCO_ESITO` `0x0010`), entrata la notte del 9 agosto 2026 con l'ultima occasione che §9 concedeva. ⚠ *Questa riga mandava a `RCP.md` §12, dove quella voce è **sbarrata** perché chiusa* |

---

## Le `[?]` da misurare

| `[?]` | perché resta aperta | chi la chiude |
|---|---|---|
| ⛔ **che un fotogramma arrivi davvero** | il prodotto non esiste: 0 occorrenze di `0x0301`/`0x0302` in `src/` `[M]` | il primo giro di `02-filo-cliente.py` sulla **7514**, dentro il contenitore. ⏳ **È la prima misura della fase 2** |
| **che il server e la pagina leggano l'intestazione come la legge il terzo lettore** | non c'è niente da confrontare | idem — ed è il confronto che nessun banco nostro può fare da solo |
| **quanto pesa davvero una chiave** a 1920×1080 in HEVC Main10 software | §6.2 mette un tetto di 16 MiB e §6.2 stesso dichiara `[?]` quanto pesi una chiave 8K a 10 bit | F2.3 (la codifica) misura il peso; il tetto lo prova questo banco |
| **la profondità di colore non sta nell'intestazione** mentre il codec sì | è un'asimmetria dichiarata, non un difetto misurato. La SPS dell'HEVC la porta, e §9 vieta comunque di aggiungere campi | nessuno oggi: si dichiara |
| **se un fotogramma di zero byte di dati** (28 byte esatti, FIN) sia legale | nessuna riga di `RCP.md` lo vieta. Il banco lo dichiara **legale** e lo lascia passare al decodificatore | ⚠ se un giorno si decidesse che è un errore, la riga va in `RCP.md`, **non** in un `if` del client |
| **quanti stream al secondo regga davvero il browser** | `RCP.md` §2.3 la dichiara `[?]` e §11 vuole un banco che tenga la sessione **oltre i primi 256 fotogrammi** | la **fase 3**: la fase 2 consegna un fotogramma fermo |
| **se i tre stream di HTTP/3 siano davvero tre** su un browser | `RCP.md` §2.3, riquadro: *«su un browser i tre potrebbero essere di più — uno stream di grease, per dire — e nessuno l'ha misurato»* | ⚠ morde **qui** quando i fotogrammi diventano molti: fase 3 |

---

## Le cuciture

### Che cosa CHIEDO alle altre sotto-fasi

| a chi | che cosa chiedo |
|---|---|
| ⛔ **F2.3** (la codifica) | **la forma esatta dei byte che vanno all'offset 28.** Precisamente: *(a)* che cosa sia un «fotogramma» come unità — l'access unit intera, con quali NAL e in che ordine; *(b)* se i parametri (VPS/SPS/PPS) siano **dentro ogni fotogramma chiave** o mandati una volta sola — ⛔ e se fossero mandati una volta sola, `RCP.md` non ha nessun posto dove metterli, e §5.2 vuole che ogni chiave si decodifichi **da sola**; *(c)* **Annex-B con i codici di partenza, o `hvcC` con le lunghezze**, che è la differenza che fa accettare o rifiutare il flusso a `VideoDecoder`; *(d)* il **livello** emesso, che §4.3 lega alla capacità `video.livello` del client — *«un livello dichiarato troppo basso non dà un errore di rete, fa rifiutare la configurazione dal decodificatore»*; *(e)* ⛔ **e se la codifica producesse un fotogramma oltre i 16 MiB**, §6.2 impone di **ricodificarlo a qualità inferiore** e scriverlo nel registro — mai spedirlo |
| **F2.2** (la cattura) | l'**istante** della cattura, in microsecondi dell'orologio **monotono** — non un'ora. È il campo `istante` di §6.2, e il client **NON DEVE** confrontarlo col proprio |
| **F2.1** (la sessione) | la misura del monitor virtuale, che diventa la **tela concessa** in `SESSIONE`: ⛔ §4.5 la vuole fra 320×240 e 7680×4320 **con i lati pari**, e §6.2 lega `largh.`/`altezza` a quella (proposta P5) |
| **il coordinatore** | ⭐ **le sette proposte a `RCP.md`** qui sopra, e la decisione se **fondere** `02-filo-validatore.py` dentro `01-b4-validatore.py` o tenerli accanto. ⚠ Io non l'ho toccato: è della fase 1 |
| **il coordinatore** | la riga 187 di `PIANO.md`, che manda a `RCP.md` §12 per una cosa che sta in §7.5 |

### Che cosa PROMETTO a F2.5 (la pagina)

⛔ **Che cosa la pagina riceve, e in che ordine.** Questo è il contratto, e sta tutto in `RCP.md` —
non è una mia invenzione:

1. la pagina apre il **primo stream bidirezionale** della sessione, che è il canale di controllo, e
   fa `CIAO → ECCOMI → CREDENZIALI → AMMESSO → ATTACCA → SESSIONE`. Da `SESSIONE` prende la **tela
   concessa**, che può essere diversa da quella chiesta (§4.5);
2. poi, e **solo** poi (proposta P1), arriva **uno stream unidirezionale nuovo, aperto dal server**.
   Uno per fotogramma. La pagina non lo apre e non risponde;
3. i primi **28 byte** di quello stream sono l'intestazione di §6.2, **in ordine di rete**
   (big-endian), **senza inquadratura** e **senza un byte di riempimento**. Dall'offset 28 in poi
   sono i byte del codec, fino alla fine dello stream;
4. ⛔ **come lo stream finisce è parte del messaggio**: **FIN** ⇒ fotogramma completo, si consegna a
   `VideoDecoder`; **`RESET_STREAM`** ⇒ fotogramma **incompleto**, ⛔ si butta, **non** si consegna, e
   si tratta come un buco (§6.2). ⚠ Non è un errore: è il caso normale di §5.1;
5. alla fase 2 arriva **un fotogramma solo**, ed è una **chiave** (`tipo = 0x0301`) — che oggi è una
   promessa mia e non una riga del documento: è la proposta **P6**;
6. la pagina non ha bisogno di ordinare niente in questa fase, ma la regola vale da subito: si scarta
   un `numero` **precedente** all'ultimo consegnato, con l'aritmetica **modulo 2³²** e le differenze
   **con segno** (§6.2). ⛔ Un confronto `<` diretto farebbe scartare **ogni** fotogramma dopo il giro
   del contatore;
7. su un **buco** nella successione dei `numero`, o su un fotogramma che il decodificatore rifiuta, la
   pagina **DEVE** mandare `RICHIEDI_CHIAVE` (`0x000D`, `u32 ultimo_numero`) sul canale di controllo
   (§5.2). ⛔ E finché la chiave non arriva **NON DEVE** mostrare fotogrammi che sa incompleti: tiene
   l'ultimo buono;
8. su una violazione, la pagina fa §3.1 **in quest'ordine**: registro, `CONGEDO(ERRORE_PROTOCOLLO)`
   sul canale se il canale è ancora utilizzabile, e ⛔ **il motivo nel codice d'errore applicativo
   della chiusura della sessione WebTransport** — che è un `DEVE` incondizionato.

⭐ **E un regalo pratico**: `banchi/02-filo-fotogramma.py` è senza dipendenze e ha la funzione
`intestazione(tipo=…, codec=…, lar=…, alt=…, num=…, ist=…, inp=…)`. F2.5 può fabbricarsi
un'intestazione conforme **senza un server**, e provare `VideoDecoder` contro i 28 byte giusti. ⚠ Ma
⛔ **non copi il giudizio**: se la pagina si riscrivesse la lettura dell'intestazione a modo suo, i
due lettori tornerebbero a essere uno.

### Che cosa prometto a F2.6 (il giudizio)

Il cliente di prova scrive una **registrazione nel formato di §11.1** (`--registra`) con dentro sia
la stretta di mano sia i blocchi video, e l'arbitro `02-filo-validatore.py` la giudica. ⛔ Ma i
**pixel** non li guarda nessuno dei due: qui si giudicano i byte contro il documento, e il metro di
F2.6 è l'utente (invariante **I8**).

---

## Che cosa resta `[?]` — e la riga per il catalogo delle certificazioni

Nella forma di `banchi/01-b12-guasti.py`, con l'atteso **scritto prima del giro** (`--elenco`):

| sigla | banco | comando | atteso sano | guasto da innestare | atteso guasto | esito `[M]` 12 ago |
|---|---|---|---|---|---|---|
| **F2.4-G1** | `02-filo-fotogramma.py` | `python3 02-filo-fotogramma.py --certifica` | **0** guasti su 27 casi | l'intestazione letta di **32** byte invece che di 28 (`INTESTAZIONE = 32`) | **> 0** guasti, e nell'uscita la marca *«l'intestazione ne vuole 32»* — ⛔ che il giro sano **non** deve già dire | ✅ sano 0 → guasto **4** → risanato 0, marca vista |
| **F2.4-G2** | idem | idem | **0** su 27 | il giudice accetta anche `tipo = 0x0300` (un valore in più in un `set`) | **> 0**, marca *«tipo-0x0300: ERRORE_PROTOCOLLO -> ACCETTATO»* | ✅ sano 0 → guasto **1** → risanato 0, marca vista |
| **F2.4-G3** | idem | idem | **0** su 27 | uno stream **azzerato** trattato come uno chiuso con FIN | **> 0**, marca *«reset-a-meta: SCARTATO -> ACCETTATO»* | ✅ sano 0 → guasto **2** → risanato 0, marca vista |
| **F2.4-G4** | `02-filo-validatore.py` | `python3 02-filo-validatore.py --certifica` | **0** prove sbagliate su 6 | l'arbitro **salta il canale video** — ⭐ che è quel che `01-b4-validatore.py` fa oggi, la sua riga 521 | le prove che devono uscire **1** escono **3** («niente da giudicare»), ⛔ **e non 0**: un arbitro cieco non assolve, dichiara di non aver guardato | ✅ sano 0 → guasto **3** → risanato 0, marca **2** volte col guasto e **0** da sano |

⛔ **E la marca ha due metà**, che è il criterio che l'11 agosto 2026 mancava proprio al banco che
certifica gli altri undici (rilievo R12-A.3): il giro guasto la deve **dire**, e il giro sano **non
la deve già dire**. Tutte e quattro le righe qui sopra sono verificate su tutt'e due le metà.

⚠ **E la certificazione vale per oggi.** Un banco certificato su un codice che nel frattempo è
cambiato non è certificato: il registro è `banchi/02-filo-esiti.jsonl`, con l'ora e la scena.

---

## Il giudizio dell'utente

⏳ **Non c'è ancora, e non può esserci**: la fase 2 si chiude quando l'utente vede il proprio desktop
in una scheda del browser, e in questa sotto-fase **non è passato un byte sulla rete**. ⛔ Il verde di
oggi vale per quel che il suo denominatore dice: 27 casi del giudice, 6 registrazioni, 4 guasti
certificati, **0** fotogrammi arrivati da un server.
