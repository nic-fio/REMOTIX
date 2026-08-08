# CODER — Le regole di chi scrive

Le regole da rispettare mentre si scrive codice, perché il prodotto si avvicini
ai numeri dichiarati e non si allontani da ciò che l'utente vede.

⛔ **Regola vincolante.** Non si scrive una sola riga di codice senza aver prima
letto questo documento e le sezioni di `SPECIFICA.md` che l'area tocca. È la stessa
regola di `REFERENCE.md` §7.0, estesa a tutto il lavoro e non solo al protocollo.

---

## 0. Come leggere questo documento

Questo documento dice **cosa costruire e come costruirlo**. Non contiene il metodo
di misura — quello sta in `LEZIONI.md`, che è il fondamento condiviso e va letto
prima di cominciare. Qui ci sono le regole operative, il più corte possibile, con
accanto la ragione di ciascuna.

Il rapporto con l'altro documento: ogni regola scritta qui ha una verifica
corrispondente in `REVIEWER.md`. Se una regola esiste qui ma non là, è una regola
non verificata. Se una verifica esiste là ma non qui, sta controllando qualcosa che
nessuno ha detto di fare. Entrambi i casi sono un difetto della coppia.

Il fondamento condiviso, che qui si richiama ma non si riscrive:
- `LEZIONI.md` — il metodo: come si misura, come si prova, come si impara.
- `SPECIFICA.md` §3.1 — i due numeri che ogni scelta tecnica deve avvicinare.
- `REFERENCE.md` — le regole di compatibilità con i client, per chi tocca il filo.

Quando una misura nuova contraddice questo documento, si aggiorna il documento nello
stesso momento, con la data e la fonte. Un riferimento che invecchia in silenzio è
peggio di nessun riferimento.

---

## 1. Il principio fondante: i numeri li pone l'utente

> «Le soluzioni tecniche devono essere prese in funzione di questi vincoli,
> non il contrario.» — `SPECIFICA.md` §3.1

|         | Valore                                     |
|---------|--------------------------------------------|
| MINIMO  | 30 fps a 1080p, profondità colore 24 bit   |
| DESIDERATO | 60 fps a 4K, profondità colore 32 bit   |

Da questo discende la regola di lavoro che governa tutto il resto:

**Una scelta tecnica si giustifica mostrando che avvicina uno dei due numeri qui
sopra. Una scelta che li lascia dove sono non si fa, per quanto sia elegante il
guadagno che porta altrove.**

E la banda dichiarata è un **pavimento, non un budget**. Si spende, non si risparmia:
la banda non spesa non torna utile a nessuno, e la qualità persa si vede.
(`LEZIONI.md` §7.2 — ottimizzare nella direzione sbagliata è peggio che non ottimizzare.)

---

## 2. Gli invarianti da proteggere

Questi non si negoziano. Sono le proprietà del prodotto che il codice non deve
rompere. Se una modifica li tocca, si ferma e si segnala — anche se il codice è
logicamente corretto.

| # | Invariante | Dove sta scritto |
|---|-----------|------------------|
| I1 | La banda dichiarata è un pavimento. Un adattamento può salire, mai scendere sotto il valore dichiarato senza una degradazione dichiarata. | `SPECIFICA.md` §3.1 |
| I2 | Una sola sessione grafica per utente; la sessione locale vince sull'RDP; la seconda connessione è rifiutata con messaggio esplicito. | `SPECIFICA.md` §3.4 |
| I3 | La guardia dell'autenticazione parte da negato. Chi non passa dal validatore non riceve un pixel e non comanda nulla. | `REFERENCE.md` R14 |
| I4 | Il palco (cattura, controllo, monitor virtuale) appartiene alla sessione, non alla connessione. Sopravvive al distacco. | `SPECIFICA.md` §3.3-ter |
| I5 | Il volume appartiene alla sessione. Chi si collega trova il livello al massimo; un cursore lasciato in basso non sopravvive alla riconnessione. | `REFERENCE.md` §7.5 |
| I6 | Ciò che cambia quel che si VEDE sta dietro un interruttore spento finché l'utente non lo guarda. | `LEZIONI.md` §2.4 |
| I7 | La protezione di un difetto noto sta nel programma, non in una riga di configurazione che si può perdere. | `LEZIONI.md` §2.5, `REFERENCE.md` R29 |
| I8 | Il metro è quel che l'utente vede, non il numero che esce dal banco. | `LEZIONI.md` §0.5, §7.3 |

---

## 3. Le regole di misura

Il progetto non si è mai arenato su un problema difficile. Si è arenato, ogni volta,
su una misura che non misurava quello che credevamo. (`LEZIONI.md` §10.) Queste sono
le regole che lo impediscono. Sono richiamate qui perché il coder misura mentre
sviluppa; il dettaglio e il prezzo di ciascuna stanno in `LEZIONI.md` §1 e §2.

### 3.1 Prima di ottimizzare un anello, misura quanto entra nella catena
Un anello più veloce di quel che gli arriva non produce niente. I 18 fotogrammi che
sembravano un limite della macchina erano una costante scritta nel nostro codice.
Misura la consegna, non solo l'elaborazione.

### 3.2 La scena si dichiara, e si muove sempre
Un compositore manda un fotogramma solo quando qualcosa cambia. Una misura senza una
scena dichiarata e sempre in movimento misura la scena, non il codice.

### 3.3 Il banco si certifica prima della misura
Accerta che il banco sappia produrre il risultato atteso prima di puntarlo
sull'incognita. Altrimenti un esito negativo è ambiguo fra «non funziona l'incognita»
e «non funzionava il banco».

### 3.4 Un banco che NON riproduce non è una prova di correttezza
È il rovescio della 3.3, ed è più insidioso perché il banco è verde. Se il difetto è
vivo nell'uso reale e il banco resta verde, la correzione scritta su quel banco va
spedita all'utente e peggiora le cose. Prima il banco che il difetto lo fa comparire,
poi la correzione.

### 3.5 Un campione preso all'avvio non dice niente del regime
I primi fotogrammi sono l'avvio, quando tutto viene ridipinto. La distribuzione del
danno sul regime è diversa da quella all'avvio. Si misura sul regime.

### 3.6 Isola UNA funzione sola, e chiamala da fuori
Quando la catena è già ristretta a due anelli, non fare un altro giro di banco:
scrivi il programma minimo che chiama la sola funzione sospetta su un ingresso noto.
Costa meno e chiude prima.

### 3.7 Non si deduce il mittente: lo si chiede al nucleo
Quando un processo muore, o un permesso è negato, non dedurre chi o cosa. Chiedilo.
Un gestore di segnale che registra chi l'ha mandato, o il registro del componente che
nega, valgono più di tre diagnosi per deduzione.

### 3.8 Verifica dal lato che deve ricevere
Il registro di chi manda dice che ha chiamato una funzione, non che il byte è arrivato.
Un congedo, un fotogramma, un livello di volume si verificano dal lato che li consuma.

### 3.9 Quando un componente può decidere da sé, digli cosa fare
Un componente che sceglie in autonomia produce due misure diverse sotto la stessa
etichetta, che è peggio che non misurare. Chiedi il componente per nome, e verifica
che abbia obbedito. Se non obbedisce, dichiara il fallimento: non ripiegare in silenzio.

### 3.10 Una lettura negata non è una lettura che dice zero
«Vuoto» e «proibito» hanno lo stesso aspetto. Una misura che può dire «zero» deve
poter distinguere lo zero dal fallimento: si guarda lo stato d'uscita, o si stampano
conteggio ed errore, non uno dei due. E ogni misura vuole un controllo positivo sullo
stesso strumento: «questo strumento sa trovare qualcosa che c'è di sicuro?»

### 3.11 Quando codice letto e misura si contraddicono, il sospetto va prima sulla misura
Il codice non ha un ambiente: la misura sì, e l'ambiente è dove stanno gli errori.

---

## 4. Le regole di scrittura

Queste governano la forma del codice, indipendentemente da cosa misura.

### 4.1 Dipendere, non riscrivere
Ogni componente che scriviamo è un componente da mantenere per sempre. Si usano i
meccanismi di sistema esistenti. (`SPECIFICA.md` §2.)

### 4.2 Degradare, non fallire
Ogni dipendenza mancante ha un ripiego. Il servizio funziona comunque, con meno.
Ma il ripiego si dichiara: un ripiego silenzioso produce due comportamenti sotto la
stessa etichetta. (`SPECIFICA.md` §2, regola 3.9.)

### 4.3 Parlare direttamente al compositore
Si evita il portale quando questo implica richieste di autorizzazione a video,
inaccettabili per un servizio non presidiato. (`SPECIFICA.md` §2.)

### 4.4 Non aspettare mai dentro il ciclo asincrono
Né esplicitamente, né in un distruttore che aspetta la fine di un thread. Un'attesa
nascosta ferma tutte le connessioni affidate a quel thread, non solo la propria.
(`LEZIONI.md` §5, `SPECIFICA.md` §5.7 regola 7.)

### 4.5 L'ambiente di una sessione si compone da zero, una variabile per volta
Chi avvia una sessione le regala tutto il proprio ambiente, comprese le variabili che
non c'entrano. Una locale sbagliata ereditata da uno script può impedire a tutte le
applicazioni di partire. Non passare il tuo ambiente: componilo. (`LEZIONI.md` §5,
`SPECIFICA.md` §5.9-bis.)

### 4.6 Il silenzio non è zero, e il verde non è vero
Un banco verde mentre il difetto è vivo è la peggiore delle prove, perché dà fiducia.
Se un controllo conta qualcosa, assicurati che sappia vedere il difetto che cerchi —
non solo il suo numero. (`LEZIONI.md` §2.2.)

---

## 5. L'obbligo di aggiornamento

Quando una misura contraddice questo documento, o `SPECIFICA.md`, o `REFERENCE.md`,
si aggiorna il documento **nello stesso momento**, con la data e la marca della fonte.

Le marche:
| Marca | Significato |
|-------|-------------|
| `[M]` | Misurato da noi, sul campo. Data indicata. |
| `[R]` | Letto nel codice di un riferimento. |
| `[S]` | Letto nella specifica. |
| `[?]` | Ipotizzato, non ancora misurato. |

Una decisione che poggia su una `[?]` va scritta come provvisoria. Una ragione non
misurata in una decisione è una decisione presa a metà. (`LEZIONI.md` §2.3-quater.)

---

## 6. Il rapporto con il revisore

Il revisore cerca contraddizioni, non verità. Il suo verdetto è sempre «questo
contraddice X», mai «questo è giusto». Il suo lavoro non sostituisce la misura:
la precede e la prepara.

Il coder non deve:
- chiedere al revisore di misurare al suo posto — la misura è del coder, sul ferro;
- trattare una review verde come un'assoluzione — è solo «non ho trovato niente»;
- riscrivere il codice su una segnalazione `[?]` senza prima misurarla.

Il coder deve:
- rendere il codice verificabile: ogni invariante di §2 deve avere un punto in cui
  il revisore può leggere se è rispettato o violato;
- dichiarare i ripieghi e le degradazioni nel registro, perché il revisore possa
  distinguere un comportamento voluto da uno accidentale;
- consegnare al revisore, insieme al codice, la misura che lo accompagna e la scena
  che l'ha prodotta.

Quando il revisore segnala una contraddizione `[R]` — confermata da una regola già
scritta — la si corregge. Quando segnala un sospetto `[?]`, lo si misura prima di
decidere. La misura chiude il cerchio, non la review.
