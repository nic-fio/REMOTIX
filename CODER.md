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

> ## ⛔ Dove stanno i documenti citati — si legge prima di andare a cercarli
>
> *Aggiunto il 9 agosto 2026: questo documento è arrivato da v1 **senza rinumerazione**, come
> `LEZIONI.md`, e come quello cita i nomi vecchi. Chi cercasse `SPECIFICA.md` nella cartella di
> V2 non lo troverebbe, ed è precisamente il primo documento che §0 gli obbliga a leggere.*
>
> | Citato qui come | Sta in | Quanto vale in V2 |
> |---|---|---|
> | `SPECIFICA.md` | `v1/documenti/SPECIFICA.md` | ⛔ **si legge `SPECIFICHE.md`**, al livello di V2, che la sostituisce per intero. I §x.y citati qui sotto puntano alla vecchia, e la corrispondenza va cercata per argomento |
> | `REFERENCE.md` | `v1/documenti/REFERENCE.md` | erano le regole di compatibilità con i client RDP altrui. **In V2 decade quasi per intero**: i client sono nostri e l'arbitro è `RCP.md`. Le citazioni restano valide come **storia del prezzo pagato**, non come regole da applicare |
> | `PIANO.md` di v1 | `v1/documenti/PIANO.md` | chiuso alla fase 11. Il piano vivo è `PIANO.md` al livello di V2 |
>
> ⚠ **E i tre documenti che in V2 non esistevano affatto**, e che qui non sono citati perché sono
> nati dopo: `RCP.md` (l'arbitro del filo), `DECISIONI.md` (il perché di ogni scelta, con la
> data e chi l'ha presa) e `SPECIFICHE.md`. Chi tocca il filo legge `RCP.md`, non `REFERENCE.md`.

Quando una misura nuova contraddice questo documento, si aggiorna il documento nello
stesso momento, con la data e la fonte. Un riferimento che invecchia in silenzio è
peggio di nessun riferimento.

---

## 1. Il principio fondante: i numeri li pone l'utente

> «Le soluzioni tecniche devono essere prese in funzione di questi vincoli,
> non il contrario.» — `SPECIFICA.md` §3.1

|         | Valore                                     |
|---------|--------------------------------------------|
| MINIMO  | 25 fps a 480p, profondità colore 24 bit    |
| DESIDERATO | 60 fps a 4K, 10 bit per canale          |

> ⚠ **Il minimo è stato abbassato l'8 agosto 2026, per decisione dell'utente.** Diceva
> «30 fps a 1080p», ed era il numero di v1. Il cambiamento non è solo di valore, è di
> **natura**: a 1080p30 il minimo era un traguardo da inseguire — e v1 lo superava già,
> con 37 fotogrammi consegnati dalla cattura di Mutter e 60 da KWin. A 480p25 diventa
> una **garanzia di servizio**: il livello sotto cui non si scende e non si stacca, per
> quanto brutta sia la linea.

> ⚠ **E il colore è stato riscritto lo stesso giorno.** Il desiderato diceva «profondità
> colore 32 bit», che non è una grandezza esistente: 32 bpp sono 24 bit di colore più 8
> di alfa, e l'alfa non si trasmette. L'intenzione dell'utente era «massima qualità»,
> e sotto quella parola stavano **due leve distinte** che il numero confondeva:
>
> | Leva | Che difetto cura | Prezzo |
> |---|---|---|
> | **10 bit per canale** | le strisce sulle sfumature morbide | quasi nulla, e in hardware ovunque — decoder Android compreso |
> | **4:4:4** (colore a piena risoluzione) | il testo colorato sfrangiato — il difetto misurato in v1, `SPECIFICA.md` §5.2 | ~50 % di banda, **nessun decoder Android in hardware**: rimetterebbe il telefono in software, cioè il muro che V2 nasce per abbattere |
>
> **Scelto il 10 bit** — la massima qualità ottenibile su entrambi i client insieme, in
> hardware, senza compromessi.
>
> ⚠ **Il 4:4:4 resta una `[?]`, non una promessa.** Sarebbe un'opzione per il solo client
> Linux su GPU capaci (NVIDIA sì, Intel a volte, AMD no), ma **nessuno ha misurato quanto
> si veda davvero la differenza** sul desktop dell'utente. Vale `LEZIONI.md` §2.3-quater —
> una ragione non misurata rende la decisione presa a metà — e §2.4: sta dietro un
> interruttore spento finché l'utente non l'ha guardata. Si decide su un banco che metta
> le due immagini a confronto, e a giudicare è lui (§7.3).

Da questo discende la regola di lavoro che governa tutto il resto. Va letta in **due
tempi**, perché un'asticella che ogni scelta supera non filtra più niente:

**Verso l'alto filtra il desiderato: una scelta tecnica si giustifica mostrando che
avvicina i 60 fps a 4K. Una scelta che lascia quel numero dove sta non si fa, per
quanto sia elegante il guadagno che porta altrove.**

**Verso il basso vincola il minimo: una scelta non si fa se può portare l'utente sotto
i 480p a 25 fps — e nemmeno se, per non scendere sotto, gli toglie la sessione. Una
sessione brutta vale più di una sessione chiusa.**

### 1-bis. Il terzo numero: il ritardo

*Posto dall'utente il 9 agosto 2026, e prima di quel giorno non esisteva: né
`SPECIFICHE.md` né la specifica di v1 nominavano la latenza.*

|         | Dall'input che arriva al fotogramma che parte |
|---------|------------------------------------------------|
| TETTO   | **50 ms** — non si supera                      |
| TRAGUARDO | **40 ms** — dove si punta                    |

⛔ **Si misura solo il pezzo che è nostro, e non è una furbizia: è l'unico modo di
avere un requisito difendibile.** La rete non è nostra e cambia da un minuto
all'altro; un requisito «100 ms end-to-end» si fallisce stando fermi, per colpa di
una galleria, e un requisito che si può fallire senza aver sbagliato niente **non
viene misurato da nessuno**. Il totale che l'utente sente è questo più la rete:
si **dichiara**, non si promette.

⚠ **E il ritardo pesa più dei fotogrammi**: 30 fotogrammi al secondo con 40 ms si
usano benissimo, 60 con 200 ms sono insopportabili. Una scelta tecnica che alza il
ritmo peggiorando il ritardo **non si fa**, ed è il tipo di scambio che si presenta
di continuo — ogni memoria intermedia che aggiungi compra fluidità e vende risposta.

E la banda dichiarata è un **pavimento, non un budget**. Si spende, non si risparmia:
la banda non spesa non torna utile a nessuno, e la qualità persa si vede.
(`LEZIONI.md` §7.2 — ottimizzare nella direzione sbagliata è peggio che non ottimizzare.)

> ### ⛔⛔ DOVE FINISCE LA MISURA — *13 agosto 2026, e vale 11 ms su 50*
>
> **La misura del ritardo finisce al DISEGNO FINITO, non al richiamo del decodificatore.**
>
> ⛔ Non è una sfumatura di metodo: la prima stesura del metro chiudeva al **richiamo**, e si
> regalava **~11 ms** — nostri, misurabili, e dentro il tetto. Spostato il confine, il numero è
> salito da **63,8 a 74,6 ms** e lo si è lasciato salire.
>
> ⇒ ⭐ **La regola per chi scrive un metro: il confine si sposta nella direzione SCOMODA.** Ogni
> confine ha due posizioni difendibili, e quella che favorisce chi misura si sceglie da sé se
> nessuno la nomina. Si nomina, e si sceglie l'altra.
>
> ⚠ **E si dichiara che cosa resta fuori anche quando non si può misurare**: fra il disegno finito
> e il pixel acceso passano `[?]` **16-40 ms** che nessuna API espone. Si stimano e si scrivono
> accanto al numero — ⛔ **ma non su Xvfb, dove quel pezzo non esiste** (`STUDI.md` §web §6.2).
>
> ⛔ **Il numero misurato, e il tetto è sforato**: `[M]` mediana **74,58 ms** cattura → vetro, che
> con il pezzo cieco fanno **90-115 ms** sullo schermo dell'utente. ⛔⛔ **E il 78 % è nostro**: a
> Mutter va il 22 %, il resto sta quasi tutto nel codificatore in software (`SPECIFICHE.md` §3.2).
>
> ### ⭐⭐ E il 15 agosto 2026 si è scoperto che c'era un SECONDO anello, e nessuno lo misurava
>
> Il numero qui sopra è **cattura → vetro** su una scena **in movimento**. ⛔ L'anello che l'utente
> sente quando **clicca** è un altro — *input ricevuto → fotogramma che parte* — e si misura su una
> scena **ferma**, che è la condizione in cui si clicca. Nessun banco lo guardava.
>
> `[M]` Misurato sui clic veri dell'utente: **mediana 136 ms, peggiore 502**. La causa era una sola
> riga (`MOVIMENTO_ATTESA_S 0.25`): il ciclo del figlio legge i messaggi del padre **prima**
> dell'attesa del fotogramma, e chi arriva durante l'attesa la paga tutta.
> ⇒ Portata a 8 ms: **mediana 41 ms, peggiore 47** — dentro il tetto.
>
> ⚠ **La lezione è di metodo, non di numeri**: un'attesa dimensionata su un anello diventa il
> ritardo di ogni altro anello che passa dallo stesso ciclo (`LEZIONI.md` §6.2-bis, `REVIEWER.md`
> **E13**). E la riga di registro che lo spiegava — *«3 attese a vuoto al secondo»* — era stampata da
> un giorno (§6.2-ter).

---

## 2. Gli invarianti da proteggere

Questi non si negoziano. Sono le proprietà del prodotto che il codice non deve
rompere. Se una modifica li tocca, si ferma e si segnala — anche se il codice è
logicamente corretto.

| # | Invariante | Dove sta scritto |
|---|-----------|------------------|
| I1 | Il ritmo non cala mai per prudenza, per risparmio o perché la scena è ferma: cala **solo** quando la misura dimostra che la linea non porta, e ogni discesa è dichiarata nel registro. Sotto il minimo si continua a calare i **fotogrammi** — mai a sgranare l'immagine, e **mai a staccare**. | `SPECIFICHE.md`, deciso l'8 agosto 2026 |
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

### 4.1-bis Si dipende dal compositore, non dal suo contorno
*Posta dall'utente l'8 agosto 2026: «voglio evitare di smettere di correre dietro ai
compositor e cominciare a dover inseguire i display manager».*

La 4.1 dice di appoggiarsi ai meccanismi che ci sono. Questa dice **quali**, perché
presi alla lettera insieme si contraddicono.

**Il compositore si insegue per forza**: solo lui consegna i fotogrammi e accetta
l'input. `mutter.c` e `kwin.c` esistono per questo, e continueranno a esistere.

**Il contorno no.** Blocca-schermo, demoni di inattività, gestori dell'energia,
display manager: fanno la stessa cosa in quattro modi diversi, con quattro
configurazioni diverse che si riscrivono da sole. Inseguirli è una tassa che si paga
per sempre e non compra niente che non sappiamo fare noi una volta sola.

**La prova da fare, prima di appoggiarsi a un meccanismo:**

> *Quante implementazioni diverse di questa cosa dovrei inseguire, e quanto mi costa
> farla da me?*

Quattro implementazioni divergenti e un costo nostro piccolo ⇒ **si fa da noi, una
volta.** Un'implementazione sola, o standard fra i desktop ⇒ vale la 4.1 per intero.

⚠ **E questo non è un permesso di riscrivere.** `logind`, PAM, PipeWire, `libei`,
`xkbcommon`, QUIC: uno solo ciascuno, uguale ovunque. Lì la 4.1 vale senza sconti, e
scrivere il nostro sarebbe il difetto che la 4.1 vieta.

*Applicata in `DECISIONI.md` §4.3 (il blocco è nostro), dove il conto era: quattro cure
diverse — e tre delle quattro erano righe di configurazione, cioè I7 — contro un
contatore e un congedo.*

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
