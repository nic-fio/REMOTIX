# LEZIONI — quel che GNOME ci ha insegnato, e che serve al prossimo desktop

*Scritto il 7 agosto 2026, chiudendo il supporto a GNOME (fasi 0–10), prima di aprire la fase 11.*

> ## ⛔ Portato in REMOTIX_V2 l'8 agosto 2026 — si legge prima di tutto il resto
>
> Questo e' il **fondamento condiviso** di [`CODER.md`](CODER.md) e [`REVIEWER.md`](REVIEWER.md), che
> lo citano **29 volte su 20 sezioni diverse**. Arriva qui **senza una sola rinumerazione**: ogni
> `§x.y` citato altrove punta ancora dove puntava.
>
> **Che cosa resta vero, ed e' quasi tutto.** V2 cambia il filo — protocollo nostro (**RCP**) al
> posto di RDP, niente Windows, niente FreeRDP, HEVC e AV1 al posto dell'H.264, e i due soli client
> sono nostri. Non cambia **niente** di come si misura. Le sezioni 1 e 2, che sono il cuore, parlano
> di scene dichiarate, banchi certificati, controlli positivi e mittenti chiesti invece che dedotti:
> un banco verde mentre il difetto e' vivo mente allo stesso modo qualunque protocollo gli passi
> sopra. E la sezione 10 vale parola per parola — il progetto non si e' fermato sui problemi
> difficili, si e' fermato sulle misure che non misuravano quel che credevamo, e cambiare protocollo
> non regala nessuna immunita'.
>
> **Che cosa cambia forma** e' marcato dove capita, con la data, e sono tre punti soli: la regola dei
> tre client (§2.1), due dei vicoli ciechi (§8) e il conto del client Android (§7.4).
>
> **Dove stanno i documenti citati.** Il progetto v1 vive sotto `v1/`, e i rimandi qui sotto vanno
> letti con questa tabella accanto:
>
> | Citato come | Sta in | Quanto vale in V2 |
> |---|---|---|
> | `REFERENCE.md` | `v1/documenti/REFERENCE.md` | erano le regole di compatibilita' con i client RDP altrui. **In V2 decade quasi per intero**, perche' i client sono nostri. Le citazioni restano valide come **storia del prezzo pagato**, non come regole da applicare |
> | `PIANO.md`, `SPECIFICA.md` | `v1/documenti/` | il piano e la specifica di v1, chiusi alla fase 11 |
> | `kde.md`, `gnome.md`, `xfce.md`, `lxqt.md` | qui, al livello di V2 | intatti: parlano di compositori, non di protocollo |
> | i banchi e i programmi di misura | `v1/banchi/` | intatti, e sono la cosa piu' riutilizzabile che v1 lascia |
>
> ⚠ **E una avvertenza sul riuso**, che e' §1.11 rivolta a noi: che una lezione sia scritta qui non
> vuol dire che sia stata verificata su RCP. Una lezione di **metodo** si riusa senza ridiscuterla;
> una lezione che nomina un numero, un client o un codec e' `[M]` **su v1**, e in V2 torna `[?]`
> finche' qualcuno non la rimisura.

## Perché questo documento esiste, e in che cosa è diverso dagli altri

`REFERENCE.md` dice **che cosa fare con Mutter**: è un elenco di regole, e quando cambieremo
compositore metà di quelle regole non varranno più. Questo documento tiene l'altra metà: **quel che
resta vero quando cambia il compositore**, e che non si trova rileggendo il codice perché non sta nel
codice — sta in come si è arrivati a scriverlo.

Ogni lezione ha tre parti:

| | |
|---|---|
| **la lezione** | in una riga, scritta per essere ricordata |
| **quanto è costata** | perché una lezione senza il suo prezzo non convince nessuno, nemmeno chi l'ha pagata |
| **dove sta il dettaglio** | il rimando, per non ripetere qui quello che è già scritto altrove |

> ⚠ **Le lezioni di metodo valgono più di quelle tecniche**, e non è una frase di circostanza: le
> prime nove sezioni di questo documento hanno prodotto tutte le altre. Il progetto non si è mai
> arenato su un problema difficile — si è arenato, ogni volta, su una **misura che non misurava
> quello che credevamo**.

---

## 0. Le cinque che valgono più di tutte

Se il prossimo desktop lo apre qualcuno che ha dieci minuti, legga solo questa sezione.

| # | La lezione | Il prezzo |
|---|---|---|
| **1** | **Prima di ottimizzare quel che si elabora, misurare quel che si CONSEGNA.** | Un'intera fase (la 9) spesa a portare i millisecondi di CPU per fotogramma da 41 a 6, mentre i fotogrammi consegnati erano 18 e nessuno li aveva mai contati. Il tetto era una costante nel nostro `main.c` |
| **2** | **La scena si dichiara, e si muove sempre.** Un compositore manda un fotogramma solo quando qualcosa cambia: una scena ferma, o mossa a colpi di tastiera, misura la scena e non il compositore | **Tutte** le misure di fotogrammi al secondo prese fra la fase 3 e la fase 9 sono state buttate |
| **3** | **Una prova verde sul client sbagliato non vale niente**, e vale anche per i banchi: una prova che non riproduce il difetto **non è una prova di correttezza** | Una correzione scritta su un banco verde, spedita all'utente, gli ha peggiorato il difetto che doveva curare |
| **4** | **Non si deduce: si chiede.** Il mittente di un segnale, la strada che un buffer ha preso, che cosa il client ha davvero ricevuto | Tre diagnosi sbagliate di fila su chi uccideva il server, e una fase rimandata a torto. Chiederlo al nucleo è costato venti righe e una sola esecuzione |
| **5** | **Il metro è quel che l'utente vede**, non il numero che esce dal banco | Un cambio validato con PSNR, SSIM e l'occhio dello sviluppatore: giudizio dell'utente sul desktop vero, *«siamo tornati indietro»*, e la fase azzerata |

---

## 1. Come si misura

### 1.1 La scena si dichiara, e si muove sempre

Un compositore Wayland consegna un fotogramma **solo quando qualcosa cambia**. Ne discende che
qualunque misura di fotogrammi al secondo dipende dalla scena tanto quanto dal compositore, e che una
misura senza la scena dichiarata **non è una misura**.

E non basta che si muova: deve muoversi **a ogni ridisegno**. La scena mossa battendo tasti — che il
progetto ha usato dalla fase 3 alla fase 9 — produce raffiche e pause, e il numero che ne esce non ha
un significato.

**La forma giusta**, e va tenuta: un client a schermo intero, opaco, che ridisegna a ogni *frame
callback* del compositore (`weston-simple-egl -f -o` fa esattamente questo, e costa niente di GPU).
Accanto va **contato quanto disegna il client**: è il controllo che dice se il tetto è del
compositore o della scena. Senza quel controllo, il 7 agosto avremmo attribuito a Mutter un tetto che
era della scena — e viceversa.

*Prezzo: tutte le misure di ritmo delle fasi 3-9. Dettaglio: `REFERENCE.md` R32.*

### 1.2 Il banco si certifica prima della misura

Si accerta che il banco sappia produrre il risultato atteso **prima** di puntarlo sull'incognita.
Altrimenti un esito negativo è ambiguo fra «l'incognita non funziona» e «il banco non funzionava».

Fatto due volte, e due volte ha salvato la giornata: in fase 0, certificando con un client
strumentato che il flusso contenesse davvero RemoteFX Progressive **prima** di collegare il telefono;
in fase 4, contando i fotogrammi decodificati prima di dire «il client non disegna».

*Dettaglio: `PIANO.md` fase 0, `REFERENCE.md` §10 n.2.*

### 1.3 Un banco che NON riproduce non è una prova di correttezza

È il rovescio della 1.2, ed è più insidioso perché il banco è **verde**.

Due riproduzioni del difetto della copia zero — client in contenitore su loopback, client su
un'altra macchina in LAN — restavano verdi mentre il difetto era vivo nell'uso reale. La correzione
scritta su quella base è stata spedita all'utente e **ha peggiorato le cose**.

A trovarlo è stato un banco di forma diversa: **l'anello**, cioè un fotogramma ogni dieci registrato
di continuo con l'ora, che non chiede a nessuno di essere presente nell'istante giusto.

*Prezzo: mezza giornata dell'utente, e una correzione da ritirare. Dettaglio: `REFERENCE.md` R29.*

### 1.4 Un campione preso all'avvio non dice niente del regime

Guardando i **primi dieci** fotogrammi di una cattura, il danno risultava «copre tutto» in nove casi
su dieci, e il sospetto giusto è stato scartato. I primi dieci sono l'avvio, quando tutto viene
ridipinto. Su trecento, il rapporto si ribalta: **282 su 300 avevano danno parziale**.

La stessa forma dell'errore si era già presentata sulla misura di banda, che pesava il nulla perché i
marcatori finivano tutti prima del fotogramma.

*Dettaglio: `REFERENCE.md` R29 e R19.*

### 1.5 Si isola UNA funzione sola, e la si chiama da fuori

Quando la catena è già ristretta a due anelli, non si fa un altro giro di banco: si scrive il
programma minimo che chiama **la sola funzione sospetta** su un ingresso noto.

Quaranta righe hanno chiuso in mezz'ora una questione aperta da un giorno — il DSP che ribaltava il
segno di ogni campione PCM — dopo che cinque strati erano stati sospettati a turno.

*Dettaglio: `REFERENCE.md` R24.*

### 1.6 Non si deduce il mittente: lo si chiede al nucleo

Quando un processo muore e nessuno ammette di averlo ucciso, **non si deduce**. Tre misure concordi
su tre cgroup diversi sembravano dimostrare che fosse systemd; erano vere e non dimostravano niente,
perché il mittente non era mai stato *chiesto*.

Un gestore di segnale che registra `si_pid`, `si_uid`, `si_code` e la pila: venti righe, una sola
esecuzione, e la risposta era che il server **si uccideva da solo** dentro una libreria.

*Prezzo: tre diagnosi sbagliate e una fase rimandata a torto. Dettaglio: `REFERENCE.md` §7.4.*

### 1.7 Si verifica dal lato che deve ricevere

Il registro di chi manda dice che ha **chiamato una funzione**, non che il byte è arrivato.

Per tre fasi il server ha scritto compìto «congedo il client» mentre il client, alla stessa ora,
scriveva «errore di rete»: mancava una seconda chiamata di libreria che nessuno sospettava. E la
stessa regola ha deciso la questione dello *scaled output*: la risposta è arrivata da **una
fotografia dello schermo del client**, non dal nostro registro.

*Dettaglio: `REFERENCE.md` R12 e §10.2.*

### 1.8 Quando un componente può decidere da sé, bisogna dirgli cosa fare

Un componente che sceglie in autonomia produce **due misure diverse sotto la stessa etichetta**, che
è peggio che non misurare.

Due volte lo stesso errore: il codificatore hardware che ripiegava in silenzio sulla CPU credendosi
in GPU, e il driver che deduceva il modo di controllo del bitrate da come erano riempiti due campi —
banda costante, senza che nessuno l'avesse scelta e senza una riga di registro.

**Corollario**: quando si chiede un componente **per nome**, non si ripiega su un altro. Si fallisce
dichiarandolo.

*Dettaglio: `REFERENCE.md` R27 e R31.*

### 1.9 ⭐ Una lettura negata non è una lettura che dice zero

*Imparata il 7 agosto 2026, e costa una riga sbagliata in un documento di riferimento per mezza
giornata.*

La misura diceva: **«KWin senza monitor non apre alcun nodo DRM e non carica alcuna libreria GL,
quindi compone in software»**. Era falsa. Il comando era `ls -l /proc/<pid>/fd | grep dri`, e non
stampava niente — ma non perché non ci fossero nodi DRM: perché **il kernel negava l'intera
directory**. `/usr/bin/kwin_wayland` porta l'attributo esteso `security.capability`, e un binario con
file capabilities è **non dumpable**: `/proc/<pid>/fd` e `/proc/<pid>/maps` diventano leggibili solo
da root, **anche per l'utente che l'ha avviato**.

⛔ **Il difetto di forma è che «vuoto» e «proibito» hanno lo stesso aspetto.** Un elenco filtrato con
`grep` perde lo stato d'uscita del comando, l'errore va sullo stderr — dove nessuno guarda — e il
risultato entra nel documento come un fatto misurato.

**Le tre regole che ne derivano, e valgono per qualunque misura:**

1. **Una misura che può dire «zero» deve poter distinguere lo zero dal fallimento.** Si guarda lo
   stato d'uscita, o si stampa il conteggio *e* l'errore, non uno dei due.
2. **Ogni misura vuole un controllo positivo, sullo stesso strumento.** La stessa mattina una
   seconda misura ha cercato una stringa dentro l'indice binario di KDE e non l'ha trovata: la
   conclusione «il file non è indicizzato» sarebbe stata falsa, perché quella ricerca non trovava
   **nemmeno le 133 applicazioni di sistema** (l'indice tiene le stringhe in UTF-16). Il controllo
   positivo — *«questo strumento sa trovare qualcosa che c'è di sicuro?»* — è costato dieci secondi e
   ha impedito la seconda riga sbagliata. È §1.2 applicata a ogni singolo strumento, non solo al
   banco.
3. **Quando codice letto e misura si contraddicono, il sospetto va prima sulla misura.** Il codice
   non ha un ambiente: la misura sì, e l'ambiente è dove stanno gli errori.

*Dettaglio: `REFERENCE.md` R32 (il riquadro di chiusura) e `kde.md` §5.1.*

> ### ⭐ La quarta regola, e l'ha imposta la fase 1 ripetendo l'errore tre volte in un'ora
>
> *9 agosto 2026, primo giorno di banchi di V2. Le tre regole qui sopra erano scritte, lette e
> citate — e il difetto è tornato **tre volte nella stessa sera**, sempre nel banco, mai nel
> prodotto:*
>
> | | Che cosa ha detto il banco | Che cosa era |
> |---|---|---|
> | 1 | «0 simboli su 4» | `grep -q` con `pipefail`: il **riscontro riuscito** letto come fallimento |
> | 2 | «uscita 0» su un clone fallito | un `\| tail` in coda al comando: lo stato d'uscita era di `tail` |
> | 3 | «nessuna traccia: la previsione regge» | due alberi passati come **una** stringa: grep non ha cercato **da nessuna parte** |
>
> ⛔ **Il terzo è il peggiore, perché ha stampato un verde**: *«la previsione regge»* da una ricerca
> mai eseguita, con `2>/dev/null` a nascondere il «No such file or directory» che l'avrebbe detto.
>
> 4. ⛔ **Una misura DEVE dichiarare su che cosa ha guardato — il denominatore, non solo il
>    risultato.** «Zero occorrenze» non è un dato finché non è accompagnato da *«dentro 447 file di
>    2 alberi»* e da un controllo che cerca **una cosa che deve esserci** (*«"nghttp3" trovato in 110
>    file»*). Un conteggio senza denominatore non è una misura: è una speranza con un numero
>    davanti.
>
> ⚠ **E la ragione per cui questa regola nasce qui e non prima**: le prime tre parlano di come si
> *interpreta* un risultato. Questa dice che **il risultato va accompagnato da quel che lo rende
> leggibile**, e si applica quando lo strumento è scritto da chi misura — cioè sempre, in un
> progetto dove i banchi sono nostri. In tutt'e tre i casi la cura è stata **la stessa**: far dire
> allo strumento che cosa stava guardando, e in tutt'e tre ha trovato il difetto in un minuto.

> ### ⭐ Il corollario, che è arrivato il giorno dopo: un denominatore si legge dove la cosa succede
>
> *10 agosto 2026, la prova SNI di B2. La quarta regola era applicata — la sonda **dichiarava** il
> suo denominatore, a ogni gamba — e il denominatore era **falso**.*
>
> La sonda doveva rispondere a *«il server serve il certificato a chi non manda SNI?»*, e stampava
> `server_name spedito: '192.168.0.2'` leggendolo dalla **configurazione** di `aioquic`. Due righe
> di quella libreria, in due file diversi:
>
> | | |
> |---|---|
> | `asyncio/client.py:66-67` | se il campo è vuoto ci mette l'ospite — **anche se è un indirizzo IP** |
> | `tls.py:1551-1556` | e poi, scrivendo il ClientHello, se quel valore è un indirizzo IP **lo butta** |
>
> ⛔ **Quindi la configurazione diceva `'192.168.0.2'` e sul filo non andava niente** — e la gamba
> «con SNI», che usava l'indirizzo, mandava **esattamente quel che mandava l'altra**. Le due gambe
> misuravano la stessa cosa mentre la sonda dichiarava che erano opposte.
>
> 5. ⛔ **Un denominatore si legge dove la cosa succede** — sul filo, non nella configurazione; nel
>    processo, non nell'intenzione. E quando lì non si può leggere, lo si fa **confermare da un
>    programma che non è nostro**: qui l'ha fatto il registro di `lsquic`, che scrive *«SNI is not
>    set»* guardando lo stesso filo dall'altro capo.
>
> ⚠ **Perché è più insidioso della regola che estende**: un denominatore falso è **peggio** di
> nessun denominatore, perché dà alla misura l'aria di essere già stata controllata. Nessuno
> verifica due volte la riga che dice *«ecco su che cosa ho guardato»*.
>
> ### ⛔ E il corollario del corollario, che vale per i **verdetti** e non per le misure
>
> *Stesso giorno, la misura col browser.* Il banco ha stampato **`OK — i motori provati hanno
> registrato il loro esito`**, e i motori provati erano **zero**: il controllo di presenza guardava
> l'argomento sbagliato e li saltava tutt'e due, dicendolo in una riga di avviso che il verdetto
> finale contraddiceva.
>
> ⛔ ***«Tutti quelli provati sono andati bene» è vero anche quando i provati sono zero.*** Ed è la
> forma di verde più insidiosa di tutte, perché **non ha bisogno che qualcosa vada storto**: le
> altre nascono da un errore, questa nasce da un insieme vuoto. Un banco che non misura niente
> supera qualunque criterio scritto come *«tutti i risultati sono buoni»*.
>
> 6. ⛔ **Anche un verdetto ha un denominatore, ed è quante cose ha approvato.** Si stampa accanto
>    all'esito, e se è zero non si dà nessun esito.
>
> ⚠ **E la stessa sera, la prima regola è tornata in una veste nuova**: il banco dichiarava
> **morti** due server che stavano ascoltando, perché li controllava con `kill -0` da utente
> normale su processi di **root** — dove la risposta è *«operazione non permessa»*, cioè un errore,
> non *«non esiste»*. ⛔ **Vuoto e proibito con la stessa faccia**, per la terza volta in quattro
> giorni, stavolta su un controllo di sanità: la cura è `[ -d /proc/<pid> ]`, che tutti possono
> leggere.

> ### ⛔⭐ E la settima veste, che punta il dito sull'imputato sbagliato
>
> *10 agosto 2026, sera, banco B3.* Il banco dichiarava che il server violava un'invariante:
> accettava una seconda connessione che avrebbe dovuto rifiutare. **Il server aveva ragione dal
> primo istante.**
>
> Il banco aspettava una parola nel registro del primo client per sapere quando era attaccato — e
> **Python bufferizza lo stdout quando è rediretto su un file**. Quella riga compariva solo
> all'uscita del processo, cioè **nell'istante esatto in cui il client si staccava**. Il controllo
> stampava *«la prima è attaccata»* leggendo una verità appena scaduta.
>
> ⛔ **Non è un falso rosso: è un rosso puntato sul colpevole sbagliato.** Le altre sei vesti di
> questo difetto fermano il lavoro o lo benedicono a torto; questa manda a cercare in un posto in
> cui non c'è niente, e più il posto è plausibile — un'invariante appena scritta, un modulo appena
> nato — più a lungo ci si resta.
>
> 7. ⛔ **Quando un banco accusa il codice, il primo sospetto resta sulla misura** (§1.9 punto 3), e
>    il modo di toglierlo è **chiedere allo strumento l'istante, non il fatto**: chi ha preso il
>    posto, quando, e quanti ne restano. Due righe di strumentazione e i timestamp del trasporto
>    hanno chiuso il caso in un giro.
>
> ⭐ **E la regola pratica**: *un file scritto e chiuso è un fatto; una riga stampata è una speranza
> sul momento in cui qualcuno la vedrà.* Un banco che sincronizza due processi non lo faccia
> leggendo registri.

### 1.10 Un permesso può dipendere da una variabile d'ambiente che nessuno documenta

Il cancello della cattura su KWin è un campo in un file `.desktop` (§3 di `kde.md`) — e per cinque
prove di fila ha negato, con il file scritto giusto, nel posto giusto, con il percorso giusto. La
causa era **`XDG_MENU_PREFIX`**: senza quella variabile l'indice dei servizi di KDE si costruisce
**vuoto**, e nessun `.desktop` viene trovato — nemmeno quelli di sistema. In una sessione del desktop
la variabile c'è, perché la mette il desktop stesso; in un ambiente composto da noi, no.

**La lezione generale**: quando un meccanismo di autorizzazione consulta un **indice**, la domanda
non è solo *«il mio file è scritto bene?»* ma *«chi costruisce quell'indice, e con quale ambiente?»*.
E prima di provare varianti del proprio file, **si accende il registro del componente che nega**: qui
la riga decisiva stava in una categoria diversa da quella ovvia (`KWIN_UTILS`, non `kwin_core`) e
distingueva in una parola due cause con cure opposte — «non ho trovato il file» contro «l'ho trovato
e il campo è vuoto». Cinque avvii di banco per indovinare, tre secondi per farselo dire.

*Dettaglio: `kde.md` §3.3-bis.*

### 1.11 ⭐ Una prova indiretta prova quel che prova, non quel che speriamo

*Imparata l'8 agosto 2026, correggendo due prove scritte il giorno prima.*

Per sapere se un compositore rende in GPU o in software avevamo due prove «strutturali», scelte
perché non dipendono da quel che il compositore *dichiara* — che è il criterio giusto (§1.8). Ma
entrambe dimostrano **meno** di quel che gli avevamo attribuito:

| Prova | Le avevamo attribuito | Dimostra in realtà |
|---|---|---|
| il processo ha aperto un **render node** | «rende in GPU» | ⛔ **niente**: KWin lo apre nel costruttore del backend, **anche quando poi rende in QPainter** |
| il flusso di cattura consegna **MemFd** e non DMA-BUF | «il compositore è in software» | ⛔ **niente sul compositore**: dipende da quel che il **cliente** ha chiesto. Con un cliente che chiede DMA-BUF, lo stesso compositore lo consegna |

**La forma dell'errore è sempre la stessa**: una condizione **necessaria** viene usata come se fosse
**sufficiente**. Il render node aperto è necessario per la GPU, non sufficiente; il DMA-BUF è
possibile solo con un backend EGL, ma il suo *contrario* non dice nulla se non si è chiesto.

**Le due regole:**

1. **Per ogni prova indiretta, si scrive cosa mostrerebbe il caso opposto.** Se non si sa dire come
   apparirebbe un compositore in software, la prova non distingue e va cambiata.
2. **Se il componente sa rispondere, gli si chiede.** Su KWin la risposta esatta — driver e chip — è
   una riga di D-Bus (`org.kde.KWin.supportInformation`, `kde.md` §5.3-bis). Mezza giornata di prove
   indirette per un dato che il compositore regala.

⚠ E il corollario che tiene insieme questa lezione con §1.8: `KWIN_COMPOSE=O2` — l'interruttore che
doveva *garantire* la GPU — **è inerte** (misurato). Quindi non basta «dire al componente cosa fare»:
va anche **verificato che abbia obbedito**, e con una prova che sappia distinguere.

*Dettaglio: `kde.md` §5.1, §5.3-bis, §5.4 e `REFERENCE.md` R32.*

### 1.12 Irrigidire un servizio può rompere un permesso, e in silenzio

Per far scegliere al compositore la GPU giusta, la via ovvia era `InaccessiblePaths=` nella sua unità
systemd — una riga, nessun codice. Effetto: la GPU giusta, e **il permesso della cattura negato**, con
il solito sintomo «questo compositore non espone il protocollo». Misurato: **0 righe di registro sulla
query dei permessi contro 13** nella stessa configurazione senza quella riga; e non è la visibilità
dei file, che dentro il namespace è intatta.

**La lezione generale**: le opzioni di irrigidimento di systemd (`InaccessiblePaths`, `PrivateTmp`,
`ProtectHome`, tutto ciò che implica `PrivateMounts`) cambiano **la vista del mondo** di un processo,
e un meccanismo di autorizzazione che ispeziona *altri processi* o l'ambiente può smettere di
funzionare. Quando si irrigidisce un servizio che concede o riceve permessi, **la prova che il
permesso funziona ancora va rifatta** — non è implicita.

*Dettaglio: `kde.md` §3.3-bis e §5.6.*

---

## 2. Come si prova

### 2.1 La regola dei tre client, e le sue forme insidiose

Nessun client copre i casi degli altri. Un difetto che si vede **solo** su uno è quasi sempre
un'informazione che il server ha omesso, non un'anomalia del client — e il client indulgente la
supplisce, nascondendola.

Ma la regola ha almeno tre forme, e le abbiamo pagate tutte:

| Forma | Come si è presentata |
|---|---|
| sul **tipo** di client | due giorni per un `MapSurfaceToOutput` mancante: due client su tre disegnavano lo stesso |
| sul **numero** di connessioni | un certificato TLS condiviso uccideva il server **alla seconda** connessione; una prova a connessione singola resta verde per sempre |
| su **chi collauda** | una correzione validata su un banco che il difetto non mostrava, e fatta collaudare all'utente |

> ⚠ **In V2 questa regola cambia forma, non valore** *(8 agosto 2026)*. I client di riferimento non
> sono piu' tre e non sono piu' di altri: sono **due, e nostri** — Linux e Android, sopra lo stesso
> `librcp`. Sparisce il client indulgente che supplisce in silenzio un'informazione omessa dal
> server, ed e' la forma che ha prodotto i difetti peggiori.
>
> ⛔ **Ma sparisce anche l'avvertimento gratis, e questa e' la perdita da sorvegliare.** Quando due
> client scritti dalla stessa mano, sullo stesso codice di protocollo, sono d'accordo, **non stanno
> confermando niente**: stanno ripetendo lo stesso presupposto. In v1 il disaccordo fra mstsc e
> `xfreerdp3` era un difetto che si dichiarava da solo; in V2 quel difetto resta muto.
>
> Da cui, in concreto: le altre due forme della regola — sul **numero** di connessioni e su **chi
> collauda** — restano intatte e vanno pesate di piu'; e dove il protocollo lascia una scelta, la si
> prova **contro la specifica scritta**, non contro l'altro nostro client.

### 2.2 Una prova può essere verde per tutto il tempo in cui il difetto è vivo

Ed è la peggiore delle prove, perché dà fiducia.

| Il banco contava | Il difetto cambiava |
|---|---|
| fotogrammi spediti e blocchi riscontrati | **i campioni**, non il loro numero: l'audio era rumore a fondo scala |
| che il processo del client morisse | **quando** moriva, e perché: il client Android restava lì |
| fotogrammi consegnati | **quali**: due schermate intere che si alternavano |

Da cui la regola: **un banco che conta non basta**. Deve *ascoltare* quel che il client suona e
*guardare* quel che il client mostra — due fotogrammi consegnati a distanza devono essere diversi
quando la scena è cambiata, e uguali quando non lo è.

### 2.3 Una prova che boccia il codice giusto costa quanto una che promuove quello sbagliato

Il banco della rotella cercava `asse dy=-10` mentre il registro scriveva `asse dx=0 dy=-10`: rosso,
con il codice corretto. Un'altra volta un `$1` non espanso faceva trovare a `grep` qualunque cosa, e
i controlli diventavano verdi o rossi a caso.

*Dettaglio: `PIANO.md` fase 4, `REFERENCE.md` R29.*

### 2.3-quinquies ⭐ Due lati sincronizzati a tempo bocciano il codice giusto

Un banco che pilota **due ambienti** — la sessione di qua, il client di là — non può coordinarli con
i `sleep`: i due orologi partono quando partono, e basta che uno dei due impieghi qualche secondo in
più perché i passi si accavallino. Al banco degli appunti di KDE i due lati erano sfasati di
**tredici secondi**: il client copiava *prima* che la sessione avesse copiato, la sessione incollava
la propria roba, e il controllo diceva rosso su un codice che funzionava — cosa che si è vista solo
leggendo il registro riga per riga.

**Si sincronizzano con marcatori**: un file che il primo tocca e il secondo aspetta. Costa tre righe
e toglie di mezzo un'intera classe di falsi rossi — e di falsi verdi, che sono peggio.

⚠ E un corollario che vale per la clipboard e per ogni stato condiviso: **quel che resta dal giro
prima va svuotato all'inizio**. La clipboard del client conteneva ancora la stringa della prova
precedente, veniva annunciata alla connessione, e sembrava un risultato.

### 2.3-bis ⭐ Il banco sbaglia dove il sistema tronca, e mente in tutte e due le direzioni

*Imparata l'8 agosto 2026, aprendo la cattura di KDE, e sono tre difetti di banco in un pomeriggio —
nessuno dei tre nel codice del prodotto.*

| Il difetto del banco | Come si è presentato | La forma generale |
|---|---|---|
| `pgrep -x weston-simple-egl` | **«la scena non è partita»** mentre la cattura consegnava 58 fotogrammi al secondo | `comm` è troncato a **15 caratteri** e quel nome ne ha 17: il confronto esatto fallisce **sempre**. Si usa `pgrep -f` |
| `-sec-nla` passato a `xfreerdp3` | il client stampava la pagina d'aiuto e usciva; il banco leggeva «zero fotogrammi» e dava la colpa al **server** | un'opzione rifiutata non è un difetto del bersaglio. Si copia la riga da un banco che funziona, invece di ricordarla |
| `2>/dev/null` su un comando che contiene `sudo` | il banco restava **appeso per sempre, in silenzio** | è la trappola della fase 1, e in un pomeriggio l'ho ripagata **tre volte**: la richiesta di password va sullo stderr, e chi la deve fornire non la vede mai |

⛔ **La regola che le tiene insieme**: quando un controllo di banco è rosso e la cosa che misura
*sembra* funzionare, **il primo sospetto è il controllo** — è §1.9 applicata al banco invece che alla
misura. E quando è verde, vale §2.2.

⚠ **E la terza riga è la più istruttiva, perché la lezione era già scritta.** Sapere che `2>&1` su un
`sudo` appende non basta: la si riscrive per abitudine, ogni volta che si vuole «togliere il rumore»
da un comando. L'antidoto non è ricordarsela, è **non mettere mai `sudo` dentro un comando di cui si
redirige lo stderr**.

### 2.3-ter Un banco che rifà lo stesso ambiente due volte fallisce la seconda

*Imparata l'8 agosto 2026: la sessione Plasma partiva al primo giro e non al secondo.*

Uccidere il compositore mette in coda su systemd un lavoro di *stop* per la sua unità; chiedere di
far partire la sessione prima che quel lavoro sia finito fa **rifiutare l'intera transazione**, e il
messaggio che l'utente legge è soltanto «Could not start Plasma session».

**La forma generale**: fra «ho ucciso il processo» e «il gestore di servizi lo sa» c'è un intervallo,
e un banco che riparte in quell'intervallo si comporta in modo diverso dalla prima esecuzione. Si
ferma l'unità e si **aspetta che sia inattiva**, invece di uccidere e ripartire.

*Corollario, che è la vera ragione per cui va scritto qui*: **un banco va eseguito due volte di
fila** prima di crederci. Uno che passa solo da macchina pulita non è un banco, è una dimostrazione.

### 2.3-quater ⭐ Una decisione presa citando un comportamento non misurato è presa a metà

*Imparata l'8 agosto 2026, e l'ha trovata l'utente al primo minuto di uso vero.*

La decisione «misura fissa alla connessione» era stata scritta con accanto la ragione: *«l'immagine
si scala nel client»*. Quella frase **non era mai stata misurata**, e il client non scala niente —
apre una finestra grande quanto la tela. Il sintomo, dalla parte di chi guarda: *«non riesco a
vedere tutto lo schermo, la risoluzione sembra ignorata»*.

⛔ **E la smentita era già in casa**, misurata il giorno prima e su un'altra pagina: la scalatura
lato client passa da `MAPSURFACETOSCALEDOUTPUT`, resa da **un client su tre**.

**Le due regole:**

1. **In una decisione, la ragione va marcata come tutto il resto.** Se dice «il client farà X» e
   nessuno ha visto il client fare X, è una `[?]` — e una decisione che poggia su una `[?]` va
   scritta come provvisoria.
2. **Prima di scrivere una ragione, si cerca se il progetto l'ha già misurata.** Qui bastava
   rileggere §10.2 di `REFERENCE.md`, che è il documento delle regole. Il costo di non averlo fatto
   non è stato il codice — che era giusto — ma **il tempo dell'utente**, speso a chiedersi perché la
   sua risoluzione venisse ignorata.

### 2.4 Ciò che cambia quel che si VEDE non si spedisce validato solo sul banco

Il banco può dire che l'immagine è migliore — con PSNR, SSIM e un fotogramma guardato a occhio — e
l'utente può guardarla e dire *«siamo tornati indietro»*. Il metro è lui.

Quel che cambia l'immagine sta **dietro un interruttore spento** finché non l'ha guardato.

*Prezzo: una fase intera azzerata. Dettaglio: `PIANO.md` fase 10.*

### 2.5 All'inizio di ogni sessione: lo stato della macchina contro quel che i documenti dichiarano

Un file d'ambiente era stato **letto** all'inizio della giornata, e la riga che teneva spenta una
strada difettosa non c'era più — persa quando il file era stato riscritto per un altro motivo.
Nessuno ha confrontato quel che c'era con quel che i documenti dicevano di aspettarsi, e l'utente si
è ritrovato in faccia un difetto noto.

**E la regola generale che ne discende, che è più importante del controllo**: la protezione di un
difetto noto **non si affida a una riga di configurazione che si può perdere**. Sta nel programma,
dove per toglierla bisogna volerlo. Vale per le protezioni e vale per i valori da cui dipende quel
che si vede: il 7 agosto la cadenza a 60 è stata messa in `main.c` per questo, non in un file.

*Dettaglio: `REFERENCE.md` R29 in fondo.*

### 2.5-bis ⭐ Una macchina che si rimette da sé non è una macchina che si rimette *completa*

Il ripristino del server era scritto in tre comandi, e per un giorno intero è bastato. Il primo
riavvio vero ha mostrato che mancavano **due pezzi**, e nessuno dei due era nei documenti:

- **il disco non si monta da solo** — `/media` vuota, `/etc/fstab` senza righe, e i sorgenti stanno
  lì. Senza quel passo il primo dei tre comandi non esiste nemmeno come file;
- **i banchi dipendono da pacchetti che il provisioning non installa** (`pulseaudio-utils`, e per un
  altro banco `wl-clipboard`): c'erano perché qualcuno li aveva messi a mano mesi prima, e il
  provisioning li ereditava senza dichiararli.

⛔ **Da cui la regola**: un ripristino si prova **riavviando**, non rileggendo lo script. Le
dipendenze installate a mano diventano invisibili nel giro di un giorno, e il momento in cui te ne
accorgi è sempre quello in cui hai bisogno che la macchina riparta.

⚠ E il corollario che riguarda le misure: **una misura presa su una macchina che ha macinato altro
per un giorno vale meno**. La regressione del volume su GNOME l'ha chiesta l'utente **da macchina
appena riavviata**, e aveva ragione a chiederlo — i numeri sono venuti uguali, ma quella era
l'informazione, non il presupposto.

### 2.6 L'utente non è il banco

Ogni ipotesi che chiede «collegati e dimmi» costa un suo intervento. Da cui:

1. **appena la cura c'è, si applica e si dichiara**: «funziona, il resto è ottimizzazione» — e la
   scelta *continuo o rinvio* si mette davanti all'utente **subito**, non dopo cinque giri;
2. **si mette un tetto alla caccia**, dichiarato in partenza;
3. le prove le fa il banco; all'utente si chiede **il giudizio**, che è l'unica cosa che il banco non
   sa dare.

---

## 3. Che cosa chiedere a un compositore nuovo

Questa è la lista che a GNOME abbiamo composto in otto fasi. Al prossimo desktop si fa in un
pomeriggio, prima di scrivere una riga. Dove la risposta la conosciamo già, è in tabella.

| # | La domanda | Mutter 48.7 | KWin 6.3.6 | wlroots (sway 1.10, labwc 0.8) |
|---|---|---|---|---|
| 1 | **Come si chiede la cattura senza portale?** | D-Bus `org.gnome.Mutter.ScreenCast` | protocollo Wayland `zkde_screencast_unstable_v1` ✅ **scritto e misurato, 8 ago** | nessuna delle due: `zwlr_screencopy_manager_v1` |
| 2 | **Spinge i fotogrammi o li fa tirare?** | spinge (PipeWire) | spinge (PipeWire) | **fa tirare**: una richiesta per fotogramma |
| 3 | **Il protocollo è dietro un permesso?** | no | **sì** — un campo di un file `.desktop`: `X-KDE-Wayland-Interfaces` [R], **più `XDG_MENU_PREFIX=plasma-` nell'ambiente** [M, 7 ago] | no |
| 4 | **Senza monitor, disegna sulla GPU?** | **sì** | **sì** [M, 8 ago]: `OpenGL renderer string` lo dice a chiare lettere via D-Bus — e **questa** è la prova, non il render node aperto (§1.11) | **sì** |
| 9-bis | **Il buffer a copia zero arriva con la fence pronta?** | **no** | **no** [M, 8 ago]: 830 su 830 col disegno in corso. KWin fa `glFlush`, non `glFinish` — quindi la fence c'è e va **aspettata** | da misurare |
| 12-bis | ⭐ **Il cursore è DENTRO l'immagine catturata?** | no | **sì con `--virtual`** [M, 8 ago]: nessun piano cursore ⇒ cursore software dipinto nel framebuffer che si cattura. Il modo cursore dello screencast **non c'entra**, e non c'è leva per impedirlo. ⭐ **Ma la cura non è nasconderlo: è renderlo INVISIBILE** — un tema `XCURSOR_THEME` con un cursore 1×1 ad alfa zero, e il puntatore torna a essere quello del client, come su Mutter | da misurare |
| 10-bis | **Che cosa costa la risoluzione, per davvero?** | niente fino a 4K | **niente a copia zero** (59 fps da 720p a 4K su una Intel integrata), **tutto in memoria** (49,6 → 27,0) [M, 8 ago] | a 4K sì |
| 5 | **Si può chiedere uno schermo virtuale della misura voluta?** | sì, `RecordVirtual` | ⛔ **NO, e il codice diceva di sì** [M, 8 ago]: `stream_virtual_output` col backend `--virtual` risponde **`Could not find output`**, per ogni misura. E `--drm`, che gli output veri ce l'ha, da una sessione senza seat non parte. L'output lo crea la riga di comando del compositore, e noi ci attacchiamo | sì, backend headless |
| 6 | **Quanto consegna, con una scena che cambia a ogni ridisegno?** | **~37 su 60** | **59–60** | **61** (40 a 4K, per il costo della copia) |
| 7 | **La cadenza dichiarata come si comporta?** | se ne ottengono **sei decimi**; oltre 60 non sale; **cadenza fissa rifiutata**. ⭐ **E ora si sa perché** `[R]` **9 ago**: `maxFramerate` fa **due mestieri insieme** — è il freno della cattura *ed* è la frequenza del monitor virtuale; stesso numero da tutt'e due le parti ⇒ battimento ⇒ 0,61. **C'è un candidato per disaccoppiarli**, vedi il riquadro sotto la tabella | **fissa rifiutata anche qui** (`framerate` deve valere `0/1`); il tetto è `maxFramerate`, e lo **onora il server** [R] | da misurare |
| 8 | **Consegna fotogrammi interi o «diff»?** | ⛔ **interi anche a copia zero** — `[R]` **9 ago**, e per due anni abbiamo creduto il contrario: il blit copia l'**intero** framebuffer di vista, Cogl **svuota deliberatamente** lo stack di clip, e per un CRTC virtuale la vista è un `CoglOffscreen` **singolo e persistente**, non uno swapchain. I quattro buffer li chiedevamo noi | **interi, sempre**, su 2–4 buffer, con il danno dichiarato a parte [R] | da misurare |
| 9 | **Il buffer arriva già disegnato?** | **no**: a copia zero il 100 % arriva con il disegno in corso | **sì**: KWin fa `glFlush()`, e `glFinish()` su NVidia e llvmpipe [R] | da misurare |
| 10 | **Che cosa costa la risoluzione?** | **niente** fino a 4K | niente | a 4K sì, ed è la copia in memoria |
| 11 | **Che cosa costa la profondità di colore?** | **niente**, e non esiste un percorso a 24 bit impacchettati | — | — |

| **13** *(nuova)* | ⭐ **Uno schermo virtuale si RIDIMENSIONA a caldo?** | **sì**: la misura si concorda nella negoziazione PipeWire, cambiarla è una rinegoziazione | ⛔ **no su 6.3.6**: il modo è `const`, l'elenco è fissato nel costruttore, e `kde_output_management_v2` sa solo *scegliere* fra i modi annunciati. Risolto a monte (`kwin!7932`, milestone **6.8**) — **e per la stessa strada nostra**, la negoziazione PipeWire | `wlr_output_state_set_custom_mode` esiste e il backend headless la usa già [lettura, **da misurare**] |
| **14** *(nuova)* | ⭐ **La clipboard di chi è?** | ⚠ **del compositore anche qui** — è `MetaSelection` `[R]` **9 ago**. Della sessione remota è solo la **porta** (`EnableClipboard`), e ⛔ **senza sessione la clipboard esiste lo stesso**: la sponda X11 è incondizionata nei due versi, `xclip` funziona | **del compositore**: `zwlr_data_control_manager_v1` v2, **nessun permesso**, e c'è anche se REMOTIX non c'è | lo stesso protocollo: `appunti_wlr.c` **è già scritto per questa famiglia** |
| **15** *(nuova)* | ⭐ **C'è uno stato in cui il compositore REVOCA quel che ha già concesso, e chi ha il dito su quel pulsante?** | ⛔ **sì, ed è l'unico dei tre**: entrando nel dialogo di sblocco gnome-shell chiama `inhibit_remote_access()` e Mutter chiude ScreenCast, RemoteDesktop e InputCapture **rifiutando di ricrearli**. L'eccezione è `is_headless()` `[R]` — la nostra condizione, e **non l'abbiamo chiesta** (`gnome.md` §4) | `[?]` da verificare | `[?]` da verificare |

> ⭐ **La 15 è la domanda che questa lista non aveva**, ed è arrivata dallo studio di GNOME
> *(`gnome.md` §14, dove è chiamata «la domanda 16» contando le righe `-bis`; qui prende il primo
> numero libero, perché in questo documento **non si rinumera**)*. La 3 chiede se esiste un
> permesso; questa chiede se il permesso **può essere ritirato a caldo**, che è una cosa diversa e
> più pericolosa: si va a chiedere il permesso una volta sola, all'inizio, e nessuno torna a
> guardare. Si fa insieme alla 3.

> ## ⭐ I sei decimi di Mutter hanno un candidato di cura, e va provato per primo
>
> *Scritto il 9 agosto 2026, leggendo `gnome.md` §8.2. È `[R]`, non una misura.*
>
> Per tutto v1 i 37 fotogrammi sono stati un muro senza spiegazione, e da lì discendono due
> righe che oggi stanno in tre documenti: *«nessuna leva nostra lo sposta»* e *«il traguardo dei
> 40 ms su GNOME probabilmente non si raggiunge»* (`SPECIFICHE.md` §3.2, `DECISIONI.md` §2.5).
>
> La lettura del codice dà la causa: `maxFramerate` **è il freno della cattura e insieme la
> frequenza del monitor virtuale**. Due orologi allo stesso numero battono fra loro, e il
> battimento vale 0,61. E `ensure_virtual_monitor` **esce prima se la misura non cambia**: quindi
> negoziare alto e poi rinegoziare **la sola cadenza** dovrebbe lasciare il monitor dov'è e
> muovere solo il freno.
>
> ⛔ **Costa tre celle e zero righe di prodotto** (è la misura M3 di `gnome.md` §13), e se
> riesce porta i 60 su GNOME — con essi il traguardo dei 40 ms. Va provata **prima** di scrivere
> qualunque cosa che dia quel muro per acquisito.
>
> ⚠ **E finché non è misurata resta una `[?]`**: una spiegazione che torna non è una cura che
> funziona. Vale §1.11 — sapere *perché* una cosa succede non dimostra di saperla fermare.

> ⚠ **La colonna wlroots e' stata riempita dopo** *(8 agosto 2026)*. Le celle «da misurare» qui sopra
> hanno una risposta in **`xfce.md` §12**, che rifa' queste quattordici domande con la colonna
> wlroots piena, e in **`lxqt.md` §4** per il caso in cui il compositore lo scegliamo noi. Questa
> tabella non e' stata riscritta di proposito: le due letture stanno bene una accanto all'altra, e
> ciascuna porta la data della propria misura.

⭐ **La 13 e la 14 sono la stessa domanda in due vesti: *chi possiede la cosa?***  È la differenza
che ha deciso metà del lavoro su KDE — non «come si fa», ma «di chi è». Dove la cosa appartiene al
compositore invece che alla nostra sessione, cambia chi comanda: la misura la **subiamo**, la
clipboard la troviamo **già lì**. Si chiede per prima, insieme alla 4 e alla 6.

**Le domande 4 e 6 vanno fatte per prime**, e insieme: senza la 4 non si sa se il numero della 6 è
confrontabile. Il modo di rispondere alla 4 è guardare quali nodi DRM il processo ha aperto e quali
librerie ha caricato — non fidarsi di quel che il compositore scrive nel proprio registro.

> ## ⚠ La colonna di KWin è stata riempita leggendo il codice, il 7 agosto 2026
>
> Lo studio sta in **[`kde.md`](kde.md)**, ed è la prova che questa lista funziona: **undici domande
> su undici hanno una risposta prima di scrivere una riga**. Ma tre cose vanno dette, e sono lezioni
> a loro volta.
>
> **1. Una lettura di codice non è una misura, e non la sostituisce.** Le celle marcate `[R]` dicono
> che cosa il compositore *può* fare, non che cosa *fa* sulla nostra macchina. La riga 4 era il caso
> limite: la misura diceva «software», il codice diceva GPU. ✅ **La sera dello stesso giorno la
> misura è stata rifatta, e il codice aveva ragione**: era la *misura* a essere sbagliata (§1.9).
>
> **2. La domanda 4 va posta con lo strumento giusto, e su KWin ce n'è uno migliore**: il **tipo di
> buffer** che il flusso di cattura riesce a offrire. Il DMA-BUF è possibile *solo* con un backend
> EGL, quindi risponde alla domanda 4 senza chiedere niente al compositore — mentre «quali nodi DRM
> ha aperto» richiede di guardare il processo giusto nel momento giusto, che è precisamente dove la
> nostra misura è inciampata. ⚠ **Ma attenzione al verso**: la prova vale solo se **il cliente
> offre** il DMA-BUF. Sul banco del 7 agosto il flusso ha negoziato `MemFd` con un compositore che
> era **in GPU** — perché il limite era del nostro cliente. «Solo MemFd ⇒ CPU» si può concludere
> **solo dopo** aver verificato che il DMA-BUF sia stato chiesto.
>
> **3. Alla lista mancava una domanda, e su KDE è quella che costa più di tutte:**
> **«si può cambiare la misura dello schermo virtuale a cattura viva?»** Su Mutter sì
> (`pw_stream_update_params`), e la fase 6 ci ha costruito sopra la risoluzione dinamica. Su KWin
> **no**: un output virtuale ha un solo modo, immutabile, e va chiuso e ricreato (`kde.md` §8). È la
> **dodicesima domanda**, e chi apre il prossimo desktop la faccia insieme alla quinta.

**Gli strumenti per rispondere esistono già** e stanno in `v1/banchi/banco-compositori/` — portati
qui dal server l'8 agosto 2026, quando la macchina di prova è stata ripulita: sorgenti, script e
binari già compilati, fuori dal prodotto:

| | |
|---|---|
| `misura-cattura` | consumatore PipeWire che conta i fotogrammi e dice tipo di buffer, danno, buffer riciclati, se il disegno era finito, e la distribuzione degli intervalli. Sa montare da sé lo schermo virtuale di Mutter, oppure agganciarsi a un nodo qualunque |
| `nodo-kwin` | client del protocollo di KWin; con `--elenca` stampa tutti i protocolli che un compositore annuncia |
| `misura-wlroots` | client `wlr-screencopy` che fa la stessa misura sul modello a tiro |
| `banco.sh`, `banco-altri.sh`, `banco-catena.sh` | la cattura sola, gli altri compositori, e la catena intera fino al client |

---

## 4. Le trappole del compositore, in ordine di quando mordono

Sono di Mutter, ma la **forma** si ripresenterà: cambieranno i nomi, non i modi di fallire.

| # | La trappola | La forma generale, che è la parte utile |
|---|---|---|
| 1 | La sequenza di creazione della sessione non ammette permute | **ogni permuta è punita con un errore diverso**, e nessuno dei due dice «hai sbagliato l'ordine» |
| 2 | Ci si iscrive all'annuncio del nodo **prima** di avviare il flusso | un annuncio che arriva *durante* una chiamata: chi si iscrive dopo aspetta per sempre qualcosa di già passato |
| 3 | I metadati **si chiedono**, o non arrivano | e chiedere non obbliga a dare: chi legge deve reggere la loro assenza |
| 4 | Il tipo di buffer si concorda in **due** posti | dichiararne uno solo fa **riuscire** la negoziazione con dentro il contrario di quel che si voleva |
| 5 | Lo *stride* si legge dal buffer, mai calcolato | il produttore allinea le righe come gli conviene; dedurlo dà immagini oblique |
| 6 | Il compositore deve disegnare sulla **scheda giusta** | un buffer di un'altra scheda non è importabile, e il sintomo è composizione in software senza un errore |
| 7 | Il gestore di sessione di systemd **non aggiorna i gruppi** di un processo già vivo | il compositore non apre `/dev/dri`, disegna in software, e nessuno lo dice |
| 8 | Un fotogramma arriva **solo se qualcosa cambia** | l'ultimo va conservato e rispedito, o chi si collega a un desktop fermo resta al nero **finché non si muove qualcosa** — e allora si corregge da sé, il che lo fa sembrare un ritardo d'avvio |
| 9 | Dopo un cambio di misura il primo fotogramma è **parziale** | non si aspetta un silenzio: si aspetta un **evento**, e ne bastano due |
| 10 | Le richieste di ridimensionamento **fanno eco** | ogni sistema che risponde con latenza a chi non conosce ancora la risposta si rincorre da solo; serve assestamento **più** una guardia sull'eco |
| 11 | Ridimensionare **non deve** rifare la cattura | rifarla trascina con sé il controllo, i dispositivi di input e lo stato dei tasti premuti |

---

## 5. Le trappole che non sono del compositore, ma ti aspettano lì accanto

| | La lezione |
|---|---|
| **Il bus di sessione** | non sopravvive a un logout: l'oggetto vecchio non dà errore, **dà silenzio**. E sulla connessione condivisa la libreria può chiamare `raise(SIGTERM)` per conto tuo |
| **L'ambiente** | chi avvia una sessione **le regala tutto il proprio ambiente**, comprese le variabili che non c'entrano: una locale sbagliata ereditata da uno script ha impedito a tutte le applicazioni di partire. Si compone da zero, una variabile per volta |
| **Il ciclo asincrono** | non si aspetta mai dentro: né esplicitamente, né in un distruttore che aspetta la fine di un thread |
| **La priorità** | il percorso audio vuole tempo reale, e va **concesso dall'unità** di sistema: un processo senza quel permesso non può chiederlo, e il sintomo è audio che scoppietta *quando il desktop lavora* |
| **Chi sopravvive al logout** | non riusa **niente** della sessione morta |
| **Il volume, e dove sta la presa** | ⭐ un nodo audio applica il volume **a valle della presa del monitor**: chi cattura il monitor riceve il segnale a fondo scala qualunque cosa dica il cursore, **mute compreso**. La proprietà che sposta la presa esiste ma vale `false` di suo, e i moduli di compatibilità PulseAudio la mettono al posto tuo — quindi **una prova fatta su un sink creato con `pactl` assolve un codice che crea il sink a mano**. Si misura sul proprio, non su uno equivalente |

---

## 6. Le lezioni sulle prestazioni

### 6.1 Il tetto era un numero che avevamo scritto noi

Per due mesi i fotogrammi mancanti sono stati cercati nel codificatore, nel protocollo, nella rete e
nel telefono. Erano nella cadenza massima che dichiaravamo alla cattura: chiedendone 30 ne
arrivavano 18, chiedendone 60 ne arrivano 37.

**La regola che ne discende**: prima di ottimizzare un anello, misurare **quanto entra** in quella
catena. Un anello più veloce di quel che gli arriva non produce niente.

### 6.2 Millisecondi di CPU per fotogramma e fotogrammi al secondo sono due grandezze diverse

E possono muoversi in direzioni opposte. Misurato due volte:

| | CPU per fotogramma | fotogrammi al secondo |
|---|---|---|
| togliendo la codifica dalla CPU (fase 9) | 41 → 20 | 29 → **22,7** |
| accendendo la copia zero (fase 9, poi verificata sulla catena intera) | 16 → **3** | 32,4 → **31,5** |

**Un guadagno che si paga in fluidità non è un guadagno**, e va detto invece di mostrare il solo
numero della CPU. La copia zero vale cinque volte sul consumo e **zero** sul ritmo: chi la riprende
lo faccia per quello.

### 6.3 Il ritmo lo decide il client, se il collegamento è veloce

Il regolatore concede `MAX(2, rtt·fps/10⁶ + 2)` fotogrammi non riscontrati: su un collegamento veloce
fa **2**, quindi la portata diventa quella con cui il client riscontra. È corretto — non si somurge
un client lento — ma ha una conseguenza sul **metodo**: un banco il cui client decodifica in software
misura il client, non noi. È successo, e il numero del 4K è stato ritirato per questo.

**Prima di attribuire un tetto al server, guardare quanto lavora**: 0,08 core con la coda piena
significa che il server sta aspettando.

### 6.4 Che cosa NON costa

Alla cattura non costano **la risoluzione** (4K rende come 1080p) né **la profondità di colore**.
Quindi la scala di ripiego 4K → 2K → 1080p serve al codificatore e alla banda, **non** a guadagnare
fotogrammi. Sapere che cosa non costa vale quanto sapere che cosa costa: toglie di mezzo le leve che
non muovono niente.

---

## 7. Le lezioni sulla direzione

### 7.1 I numeri li pone l'utente, e la tecnica li serve

Fino al 7 agosto si sceglieva una strada tecnica e poi si misurava che cosa ne usciva. Da quel giorno
l'ordine è rovesciato: **una scelta tecnica si giustifica mostrando che avvicina uno dei numeri
dichiarati**; se non li muove, non si fa, per quanto sia elegante il guadagno che porta altrove.

### 7.2 Ottimizzare nella direzione sbagliata è peggio che non ottimizzare

Metà delle misure della fase 10 erano corrette e rispondevano alla domanda sbagliata: «spendere meno
banda» era considerato un guadagno, mentre per questo prodotto la banda dichiarata è un **pavimento,
non un budget**. Prima di ottimizzare una grandezza, **farsi dire se quella grandezza va minimizzata
o spesa**.

### 7.3 Il metro è quel che si vede

Un numero di prestazione che nessuno percepisce non giustifica il tempo dell'utente. E, all'opposto:
quando l'utente dice che va bene, **va bene** — la fase 10 è stata chiusa così, senza essere rifatta.

### 7.4 Le previsioni non contano, le misure sì — e vale anche per le nostre

Il 7 agosto era stato previsto che il client Android non avrebbe guadagnato niente dalla cadenza
nuova, con un ragionamento corretto e documentato: riceve un codec che si decodifica in software, e
che al server costa due volte e mezzo l'H.264. Il giudizio dell'utente è stato *«performance
eccellenti»*.

Il ragionamento era giusto e la conclusione no, perché partiva da un presupposto mai verificato — che
qualcuno dei due lati fosse al limite. Non lo era nessuno dei due: **lo era il numero che
dichiaravamo.**

> ⚠ **E in V2 il presupposto va rifatto da capo** *(8 agosto 2026)*. Il lato che qui non era stato
> verificato — «qualcuno dei due lati e' al limite» — cambia del tutto: `aFreeRDP` decodificava in
> software un codec che nessuno avrebbe scelto, mentre il client di V2 e' nostro e chiama MediaCodec
> su HEVC. **Il numero di v1 non era un tetto di Android: era il tetto di quel client.** Vale sia per
> la previsione sbagliata sia per il giudizio che l'ha smentita — nessuno dei due si eredita.

---

## 8. I vicoli ciechi già percorsi — da non rifare

| Che cosa | Esito |
|---|---|
| Limitare il server a una versione EGFX più bassa per confronto con mstsc | vicolo cieco: su quella versione mstsc spegne l'H.264 |
| Dare più thread alla conversione di colore in CPU | rumore: 13,8 ms contro 12,5. Quel tempo non è di calcolo, è di memoria |
| Aspettare la *fence* implicita del DMA-BUF | non cambia niente: è quella sbagliata. La esplicita viaggia in un metadato che non chiedevamo. ⚠ **Corretta il 9 agosto**: questa riga copre metà del contratto — l'*acquire*. Quel che manca è il **release**, e sta dall'altra parte (vedi il riquadro qui sotto) |
| Adattare la **risoluzione** alla banda | non realizzabile: lo scaled output lo rende un client su tre, e ridimensionare il monitor virtuale ridispone le finestre dell'utente |
| Dichiarare alla cattura una cadenza **fissa** invece di «quando cambia» | Mutter la rifiuta: nessun formato negoziato, zero fotogrammi |
| Alzare la cadenza dichiarata **oltre 60** | non dà niente: 120 dichiarati, 37 consegnati come con 60. ⚠ **Non chiude la strada della cadenza**: alzare il numero *una volta sola* alza tutt'e due gli orologi insieme, ed è il battimento a mangiare il guadagno. Il candidato di §3 è un'altra mossa — **rinegoziare la sola cadenza, a monitor fermo** |
| Cercare il collo di bottiglia dei fotogrammi nel codificatore, nel protocollo o nella rete | era nella nostra costante |

⚠ **Due di queste righe erano di RDP, non del problema** *(8 agosto 2026)*, e vanno lette con
attenzione perche' le altre cinque valgono ancora per intero.

| Riga | In V2 |
|---|---|
| la versione EGFX abbassata per mstsc | **decade**: non esiste ne' EGFX ne' mstsc |
| adattare la **risoluzione** alla banda | **decade a meta'**. Il primo motivo era che lo *scaled output* lo rendeva un client su tre — e i client ora sono nostri, quindi la scalatura lato client si puo' avere. Il **secondo motivo resta intero**: ridimensionare il monitor virtuale ridispone le finestre dell'utente, e quello non lo cambia nessun protocollo |
| le altre cinque | **restano**: parlano di thread, di *fence*, di Mutter e della nostra costante — nessuna di loro nominava RDP |

⛔ **E nessuna riga si cancella.** Un vicolo cieco documentato costa meno di uno riscoperto: il
giorno in cui qualcuno riproporra' «adattiamo la risoluzione alla banda», questa tabella dira' che
in v1 non si poteva e **obblighera' a dimostrare che in V2 si puo'** — che e' esattamente il lavoro
che la riga deve far fare.

> ## ⭐ Un vicolo cieco che non era un vicolo cieco: la caccia della fase 9, nel posto sbagliato
>
> *Scritto il 9 agosto 2026 da `gnome.md` §1.3 e §8.1. `[R]`, e riapre una caccia chiusa male.*
>
> Le due schermate che si alternavano sono state inseguite per due fasi come un problema di
> **acquire**: il buffer arriva col disegno in corso, quindi si aspetta la fence. La lettura del
> codice dice che il difetto è dall'altra parte, ed è un **release**: `can_reuse_pw_buffer` —
> l'unico punto in cui Mutter aspetta noi — **si arrende alla prima riga** se manca
> `SPA_META_SyncTimeline`, e riusa il buffer **mentre VA-API lo sta ancora leggendo**.
>
> ⛔ **E spiega perché la cura peggiorava le cose**: la superficie di accumulo copiava i soli
> rettangoli danneggiati da un buffer che conteneva **già il fotogramma intero** (domanda 8).
>
> **Due cure candidate, entrambe piccole**: chiedere `SPA_META_SyncTimeline` — che Mutter
> **offre**, e che oggi non chiediamo — oppure **trattenere** il `pw_buffer` fino a lettura
> finita, che è quel che fa il riferimento, cioè il contrario di quel che avevamo concluso.
>
> ⚠ **È una lettura, non una misura**, ed è la lezione 4 di `gnome.md` §14: *una misura giusta
> con una spiegazione inventata è più pericolosa di una misura sbagliata*, perché nessuno la
> rimette in discussione. R29 è rimasta in piedi due fasi per questo.

---

## 9. La ricetta, per aprire il supporto a un desktop nuovo

Nell'ordine, e ogni passo è una lezione delle sezioni precedenti messa in fila.

0. **Cercare chi l'ha già fatto — fuori da quel che si è già clonato.** *Aggiunta il 7 agosto 2026,
   e pagata lo stesso giorno*: lo studio di KDE ha concluso «in KDE non c'è traccia di RDP» dopo aver
   cercato **dentro gli otto repository che avevo scelto io**. Il riferimento principale — `KRdp`, il
   server RDP di KDE, stessa libreria, stesso compositore, 4 200 righe — stava in un nono repository,
   e a trovarlo è stata una domanda dell'utente. **La domanda giusta non è «c'è nei repo che ho?» ma
   «chi, al mondo, fa questa cosa su questo desktop?»** — e si fa prima di leggere, non dopo.
1. **Rispondere alle quindici domande della sezione 3**, con gli strumenti che ci sono già. Un
   pomeriggio, prima di scrivere una riga di prodotto. Le domande 4 e 6 per prime, e la 3 insieme
   alla 15 — *«c'è un permesso?»* e *«può essere ritirato a caldo?»* sono la stessa indagine.
   *(Diceva «undici»: erano quelle del 7 agosto, prima che gli studi ne aggiungessero quattro —
   9 agosto 2026.)*
2. **Accertare come disegna senza monitor** (GPU o software): decide se i suoi numeri sono
   confrontabili con quelli di GNOME, e se quel desktop è servibile su una macchina da server.
3. **Trovare la strada diretta al compositore**, senza portale — e scoprire subito se è dietro un
   permesso, perché il sintomo è «questo compositore non ha il protocollo» e fa perdere un
   pomeriggio a chi non se l'aspetta. ⭐ **E quando nega, la prima mossa non è provare varianti: è
   accendere il registro del componente che nega e farsi dire la causa** (§1.10). Su KWin sono tre
   secondi, e le due righe possibili hanno cure opposte.
4. **Misurare la sola cattura**, con la scena dichiarata e il conteggio di quanto disegna il client.
   Solo dopo rimettere dentro il codificatore e il filo.
5. **Riusare i banchi delle fasi che attraversano lo stesso percorso**: una fase che tocca un
   percorso condiviso si chiude rieseguendo i banchi di chi quel percorso lo attraversava già.
6. **Provare sui tre client**, e su almeno due connessioni di fila.
7. **Far giudicare l'utente**, su quel che si vede, prima di dichiarare chiuso qualunque cosa.
8. **Aggiornare i documenti nello stesso momento** in cui una misura li smentisce, con data e fonte.
   Un riferimento che invecchia in silenzio è peggio di nessun riferimento.

---

## 10. E una lezione sola su tutto il resto

Il progetto non si è mai fermato su un problema difficile.

Si è fermato, ogni volta, su **una misura che non misurava quello che credevamo**: un banco verde con
il difetto vivo, un contatore che pesava il nulla, un campione preso all'avvio, una scena che non si
muoveva, un mittente dedotto invece che chiesto, un tetto attribuito al compositore che era una
nostra costante.

Il tempo speso a certificare lo strumento è sempre stato meno di quello speso a inseguire le sue
bugie.
