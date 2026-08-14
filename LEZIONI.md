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
callback* del compositore. Accanto va **contato quanto disegna il client**: è il controllo che dice
se il tetto è del compositore o della scena. Senza quel controllo, il 7 agosto avremmo attribuito a
Mutter un tetto che era della scena — e viceversa.

> ⛔ *Qui era nominato `weston-simple-egl -f -o` come «fa esattamente questo, e costa niente di
> GPU». **Va tolto come riferimento operativo**, per due ragioni: `[M]` **il 13 agosto 2026 non è
> installato** sulla macchina di prova (rootfs in RAM, §2.5-bis) — quindi chi seguiva questa riga
> trovava un comando che non esiste; e la frase **non portava nessuna marca**, quindi passava per un
> fatto verificato.*
>
> ⇒ ⭐ **La forma di riposo della fase 3 è la scena scritta da noi**: `banchi/03-scena.c`
> (`wl_shm` + `xdg-shell`, marca a 144 bit, quattro conti fra cui le **attese**, verifica
> `wl_surface.enter`) e `banchi/03-b14-scena.c` (la variante EGL). ⚠ **Ne esistono due**, ed è una
> decisione aperta se ne sopravviva una sola.
>
> > ⛔ ⚠ *Questa riga finiva con: «dove è stato fatto il riscontro incrociato, concordano **entro il
> > 4 %**, con **0 attese** da tutt'e due le parti». **Va ristretta**: il 4 % vale sulle celle bassa
> > e alta e sul controllo positivo, **non sulla cella D** — il risultato per cui il riscontro
> > serviva. In `banchi/03-b14-esiti-scena2.jsonl` la cella D porta `scena_sul_mio_monitor: false`,
> > `palco_stabile: false` e **1 fotogramma in 25 s**, e il controllo di ritorno di quella scena non
> > torna (52,84 contro 80,28). **Corretta il 13 agosto 2026**, rilievo del coordinatore della
> > fase 3.*

⛔ **E c'è un terzo punto, che non stava scritto qui e costa quanto i primi due: la scena deve
stare sul MONITOR CHE SI STA CATTURANDO.** Su un palco con monitor virtuali quello non è il monitor
dell'utente, e non è nemmeno «il primo»: i monitor virtuali erano **quattro**, e una scena aperta su
quello sbagliato produce un banco che gira, non fallisce, e **misura il palco di qualcun altro**.
⛔ Il sintomo è il peggiore possibile — **zero fotogrammi, o fotogrammi di una scena che non è la
nostra** — e assomiglia a un difetto del prodotto.
⇒ **La scena dichiara su quale monitor sta, e il banco lo verifica** invece di darlo per scontato.
*Prezzo: **quattro giri buttati** in un giorno solo — due allo step 3 e due allo step 1 della
fase 3.*

> ## ⛔⛔⛔ E lo stesso giorno la trappola è tornata a mordere **il risultato che la citava** — §1.1-bis
>
> *13 agosto 2026, sera. La riga qui sopra era stata scritta la mattina, dopo aver buttato quattro
> giri. Il pomeriggio, la «legge della griglia» di Mutter è stata dichiarata **verificata su 13
> punti** e scritta in **nove documenti**. Le celle della griglia erano **due**, e portavano tutt'e
> due `scena_sul_mio_monitor: **false**`.*
>
> ⭐⭐ **IL BANCO LO AVEVA SCRITTO NEL PROPRIO FILE.** Non l'ha nascosto, non l'ha sbagliato, non
> l'ha taciuto: ha stampato il campo `scena_sul_mio_monitor: false` accanto a ogni cella, ha contato
> quelle celle come **contaminate**, e sul verdetto ha scritto per esteso *«⛔ la legge NON regge su
> 0 punti su 0: la spiegazione della quantizzazione va riscritta»*. ⛔ **E nessuno ha guardato: si è
> letto il numero, e non la riga accanto.**
>
> | | |
> |---|---|
> | ⛔ **la lezione** | **Un banco che dichiara la propria invalidità non serve a niente, se chi legge guarda solo il risultato.** Il campo che salva la giornata e la riga che la butta stanno nello **stesso file**, a due centimetri l'una dall'altra |
> | ⇒ **la regola** | prima di copiare un numero in un documento, si legge **il verdetto del banco**, non la cella. Se il banco ha un campo di validità, **quel campo si cita insieme al numero**, o non si cita il numero |
> | ⚠ **e la forma d'errore** | non è distrazione: è che **un numero verosimile non attiva nessun sospetto**. I 13 punti erano plausibili, il banco aveva davvero un modo per produrli, e la spiegazione tornava. ⇒ Il controllo non può essere «sembra giusto» |
> | 💰 **il prezzo** | quattro giri buttati la mattina, e **una riga falsa in nove documenti** il pomeriggio — scritta dallo stesso progetto che aveva appena scritto la lezione per evitarla |
>
> ⭐ **E la cosa che la rende una lezione e non un aneddoto**: la trappola non è tornata su un banco
> nuovo o su un pezzo nuovo. È tornata **sul risultato che la citava**, dentro la stessa giornata, a
> lezione già scritta. ⇒ Una lezione scritta non protegge da niente finché non diventa **un campo
> che qualcuno è obbligato a leggere**.

*Prezzo della lezione intera: tutte le misure di ritmo delle fasi 3-9. Dettaglio: `REFERENCE.md`
R32.*

### 1.2 Il banco si certifica prima della misura

Si accerta che il banco sappia produrre il risultato atteso **prima** di puntarlo sull'incognita.
Altrimenti un esito negativo è ambiguo fra «l'incognita non funziona» e «il banco non funzionava».

Fatto due volte, e due volte ha salvato la giornata: in fase 0, certificando con un client
strumentato che il flusso contenesse davvero RemoteFX Progressive **prima** di collegare il telefono;
in fase 4, contando i fotogrammi decodificati prima di dire «il client non disegna».

*Dettaglio: `PIANO.md` fase 0, `REFERENCE.md` §10 n.2.*

> ### ⛔⛔ E una certificazione può essere **verde perché prova il giudice nell'unità sbagliata**
>
> *13 agosto 2026, fase 3. È il modo più insidioso di fallire questa lezione, perché la lezione
> **è stata applicata**: il giudice è stato certificato prima della misura, e il verde era vero.*
>
> ⛔ **Il verde diceva «il giudice sa distinguere», e la domanda era «sa distinguere COSA».** La
> certificazione esercitava il giudice nell'unità del **lettore** — quella in cui il dato viene
> riletto — invece che in quella dell'**acquisizione**, cioè l'unità in cui il fenomeno da misurare
> si presenta davvero. Sono due unità diverse, il giudice le tratta identiche, e la prova passa in
> tutt'e due i casi.
>
> ⇒ ⭐ **La domanda che manca a §1.2, e va posta insieme a «il banco sa produrre il risultato
> atteso?»**: *«in quale unità gliel'ho fatto produrre, ed è quella in cui il fenomeno vero
> arriva?»* Un controllo positivo costruito nell'unità comoda — quella in cui il banco già legge —
> **certifica il lettore, non la misura**.
>
> ⚠ **E si riconosce da un sintomo solo**: la certificazione è più facile da scrivere di quel che
> dovrebbe. Se costruire il caso positivo non è costato niente, va sospettato che sia stato
> costruito dalla parte sbagliata dello strumento. *(La stessa forma, dal lato della prova invece
> che della certificazione, è §2.2.)*

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

> ### ⛔ 8. «Il file c'è» e «il file è quello che ho appena costruito» sono due domande diverse
>
> *L'ottava veste, del 10 agosto 2026, e questa aveva già acceso il server sbagliato.*
>
> Il banco di B11 costruiva un server **guasto di proposito** e poi controllava di poterlo
> accendere: `test -x bsslserver`. La compilazione era **fallita** — un `struct` di troppo davanti
> a un typedef — ma il binario di due ore prima era ancora sul disco, eseguibile. ⛔ **Il banco ha
> acceso il server SANO dichiarando di aver acceso quello guasto**, e tutti e dodici i casi
> sarebbero falliti col rosso sulla **pagina**, che non c'entrava niente.
>
> ⚠ La forma è quella di §1.9 punto 1 — *una misura che può dire «zero» deve poter distinguere lo
> zero dal fallimento* — applicata a un **artefatto invece che a un numero**. Un file di ieri
> risponde «sì» a *esiste?* esattamente come uno di adesso.
>
> ⭐ **La regola**: dopo aver costruito qualcosa si guarda **l'esito del costruttore**, non la
> presenza del risultato. E quando il risultato ha una marca — qui `REMOTIX B11` nel sorgente —
> si controlla **anche quella**, perché risponde alla domanda giusta: *è dentro quel che ci doveva
> essere?*
>
> ⚠ **E lo ha trovato una prova di fumo**, non il banco: otto connessioni che chiedevano otto
> guasti e stampavano i byte dell'`ECCOMI`. Erano **tutte identiche**, compresa quella che chiedeva
> «nessun guasto». *Un banco che confronta ogni caso con un caso di controllo identico a sé
> distingue «il guasto non c'è» da «la pagina non lo vede» prima di accusare qualcuno.*

> ### ⛔ 9. Troncare un registro che qualcuno tiene aperto non lo azzera: ci scava dentro un buco
>
> *La nona veste, della notte fra l'11 e il 12 agosto 2026, e ha prodotto un **rosso falso** su un
> giro in cui tutt'e quattro le gambe erano CONFORMI.*
>
> `: > registro.log` su un file che il server tiene aperto lo porta a lunghezza zero, ⛔ **ma non
> sposta l'offset di chi ci scrive**: alla riga dopo il kernel riempie di NUL tutto quel che sta
> prima. `[M]` il registro di P5 si è ritrovato con **37.120 byte NUL in testa su 66.289**, e il
> testo vero che comincia subito dopo.
>
> ⛔ **E il modo in cui acceca è silenzioso, che è la parte che vale la lezione**: `grep` che
> incontra un NUL smette di stampare le righe e dice `binary file matches` — ⛔ **con lo stesso
> stato d'uscita 0**. Quindi `grep -c` continuava a contare, e il *controllo positivo del canale di
> lettura* del banco diceva «sano»; era `grep | sed` a ricevere quella frase al posto della riga.
> Il banco ha letto «non ho potuto sapere con che indirizzo il server ci vede» e ha mandato il
> comando di sblocco su **192.168.0.2, cioè il server stesso** — che ha risposto *«non era
> bannato»*, come risponderà sempre. ⚠ Una dichiarazione vera su un soggetto sbagliato.
>
> ⚠ **E il difetto viveva in un solo strumento**: a segmentare lo stesso registro era un programma
> Python, che il buco non ferma — quindi le gambe passavano. *Due strumenti che leggono lo stesso
> file possono vederne due cose diverse, e quello che tace non è quello che ha ragione.*
>
> ⭐ **Tre regole, non una**:
> 1. **un registro si azzera dove si azzera davvero** — quando nessuno lo tiene aperto (allo
>    spegnimento, o riaccendendo), e chi offre un comando «svuota» lo fa **rifiutare** a processo
>    vivo, spiegando perché;
> 2. **`grep -a` su ogni file da cui dipende un verdetto**: il costo è nullo, e senza, un solo byte
>    fuori posto trasforma una riga di prova in una frase su sé stesso;
> 3. ⭐ **e il buco si dichiara invece di essere aggirato** (§1.9 regola 4): il banco adesso conta i
>    NUL e li scrive, così «il registro non dice» e «il registro non l'ho potuto leggere» restano
>    due frasi diverse.

> ### ⛔⛔ 10. **«Non si è presentato» non è «regge»** — e la decima veste è la più elegante
>
> *13 agosto 2026, fase 3 step 5, il controllo **P5** dell'anello del ritardo.*
>
> Il banco doveva provare che l'anello regge i fotogrammi **fuori ordine**. Dopo **tre** iniettori
> diversi il conteggio degli scavalcati era **0**, e il banco stampava **verde**.
>
> ⛔ **Zero scavalcamenti non dice «l'anello li regge»: dice «il fenomeno non si è presentato».**
> Sono due frasi diverse, e la prima è una **proprietà del prodotto** mentre la seconda è una
> **proprietà del pomeriggio**. Il banco non aveva provato niente: aveva descritto il proprio
> insuccesso nel provocare il caso, e lo aveva scritto in verde.
>
> ⭐ **E la cura non è un controllo in più: è che il banco lo DICA.** Adesso P5 è dichiarato **NON
> ESEGUITO**, che è l'esito vero. ⛔ Un `[?]` onesto vale più di un verde: il verde entra in un
> catalogo e ogni misura che gli viene dietro **si appoggia su di lui**, perché dà fiducia (§1.3).
>
> ⚠ **E la ragione per cui l'iniettore non ci arrivava è istruttiva quanto la regola**: il fuori
> ordine non nasce (solo) dalla rete, ⛔ **nasce dalla DIMENSIONE del fotogramma** — l'evento scatta
> al *completamento* dello stream, quindi l'ordine d'arrivo è l'ordine delle **dimensioni**, e una
> chiave grossa viene scavalcata dai delta che le partono dietro. ⇒ Chi ritardava i pacchetti stava
> agendo sulla grandezza sbagliata: è §1.13, dal lato di chi **provoca** invece di chi tollera.
>
> 10. ⛔ **Un controllo che non ha visto il fenomeno DEVE dichiararsi non eseguito**, mai verde. E la
>     domanda che lo smaschera è quella di §1.11 regola 1: *«come apparirebbe il caso opposto?»* —
>     se un anello rotto darebbe **lo stesso zero**, quello zero non prova niente.

> ### ⛔⛔ 11. Un banco può accusare il prodotto di non reggere una condizione che **ha creato lui, e illegalmente**
>
> *13 agosto 2026, fase 3. È l'undicesima veste, ed è parente della settima — il dito puntato
> sull'imputato sbagliato — ma peggiore: qui **l'imputato non esiste**, perché il fatto contestato
> non è mai avvenuto sul filo.*
>
> Il banco doveva provare che il prodotto regge un credito di stream basso. Ha annunciato
> `initial_max_streams_uni = 6`, il giro è finito con `STREAM_LIMIT_ERROR`, e per qualche ora
> l'imputato è stato il prodotto.
>
> ⛔ **Il `6` non è mai stato annunciato.** Il banco lo scriveva **dopo** la stretta di mano — cosa
> che **RFC 9000 §4.6 vieta** — quindi sul filo non è mai passato. `[M]` **il server aveva 128 posti
> concessi e ne ha aperti 14.** ⇒ **La libreria non ha violato niente e il prodotto non aveva quel
> difetto.**
>
> ⚠ **Perché è più insidiosa delle altre dieci**: le altre falsificano la **lettura** di un fatto
> vero. Questa **fabbrica il fatto**, e lo fabbrica **violando la specifica che il prodotto rispetta**
> — quindi il prodotto reagisce in modo corretto a una condizione impossibile, e la sua reazione
> corretta viene letta come il difetto. ⛔ **Più il banco è sofisticato, più è capace di costruire
> condizioni che sul filo vero non esistono.**
>
> 11. ⛔ **Un banco che simula una condizione del pari DEVE essere conforme alla specifica del pari**,
>     e la conformità va **verificata sul filo, non nell'intenzione** (regola 5). La domanda è: *«quel
>     che volevo annunciare è **arrivato**, e nel momento in cui la specifica permette di dirlo?»*
>     ⭐ E si risponde **contando dal lato che riceve**: 128 concessi contro 6 dichiarati è una
>     differenza che si vede in una riga, e chiude il caso senza toccare il prodotto.
>
> ⭐⭐ **E il seguito vale quanto la lezione**: cercando il difetto falso ne è uscito uno **vero e
> peggiore** — **B-18**, un delta buttato per mancanza di posto che **non accendeva la richiesta di
> chiave**, e che sfasciava l'immagine per sempre **in silenzio**. ⇒ *Una caccia partita da un
> sospetto sbagliato non è tempo perso, purché finisca guardando il codice invece che il verdetto.*

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

> ### ⛔ Il terzo caso, dal browser: **`Emulation.setDeviceMetricsOverride` misura l'emulazione, non il browser**
>
> *13 agosto 2026, fase 3. Stessa forma, strumento diverso, ed è quello che tutti i nostri banchi
> browser hanno in mano.*
>
> ⛔ **`Emulation.setDeviceMetricsOverride` cambia `clientWidth` senza emettere `resize`.** La
> geometria si muove, il numero che il banco legge cambia, e **l'evento su cui il prodotto vive non
> arriva mai**. ⇒ Un banco che si appoggia a quel comando per provare *«la pagina reagisce al
> ridimensionamento»* prova che **l'emulazione ha cambiato un campo**, non che il browser ha
> ridimensionato niente.
>
> ⚠ **La forma è quella di questa sezione**: una condizione **necessaria** — la misura è cambiata —
> usata come se fosse **sufficiente** — quindi la pagina ha ricevuto il ridimensionamento. E il
> caso opposto, che la regola 1 impone di sapere descrivere, ha **lo stesso aspetto**: una pagina
> che ignora del tutto il ridimensionamento vede `clientWidth` cambiare esattamente allo stesso modo.
>
> ⇒ ⭐ **La cura è la regola 2**: quel che si vuole sapere è se **l'evento** è arrivato, e l'evento
> si può contare. Il banco conta gli eventi e li dichiara; e se il ridimensionamento non è arrivato
> dice *«il palco, non il prodotto»* e si ferma — invece di dare un verdetto sul prodotto.

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

### 1.13 ⭐⭐ Una tolleranza si scrive sulla **grandezza vera del fenomeno**, o si sposta di un passo a ogni rilettura

*Scritta il 12 agosto 2026, dopo che **la stessa riga di `RCP.md` è stata corretta quattro volte in
una sera** — P8 → P11 → P13 → P14 — e ogni cura ha spostato il difetto invece di toglierlo.*
*⛔ **Riaperta il 13 agosto 2026**: le volte sono **sette** — P8 → P11 → P13 → P14 → P19 → P20 → P21
— e ⛔ **P14 non «reggeva»**. Reggeva la grandezza (il campo `numero`); a essere rimasto sostitutivo
era tutto quel che le stava attorno. Il seguito è in fondo a questa sezione, e chi cita questa
lezione **rimanda qui invece di ricopiare la successione** (rilievo **R13.6**).*

**La scena.** Il protocollo aveva bisogno di tollerare i fotogrammi **già in volo** quando la tela
cambia a metà sessione. Le prime tre stesure hanno descritto quel fenomeno con una **grandezza
sostitutiva**, e ciascuna era esatta nella scena che l'aveva motivata e **sbagliata di un passo
appena fuori**:

| # | La grandezza scelta | Dove si è rotta |
|---|---|---|
| **P8** | *«la misura vale la tela precedente»* | ⛔ chi trascina una finestra manda **due** cambi di tela, e la terza misura non è né l'una né l'altra |
| **P11** | *«una tela in vigore entro il secondo appena passato»* | ⛔ un **orologio** dove quel che deve svuotarsi è una **coda**: su una linea lenta il fotogramma arriva dopo, e cade l'invariante I1 — *mai staccare* — proprio nella condizione che I1 esiste per proteggere |
| **P13** | *«finisce alla prima chiave alla misura nuova»* | ⛔ quella chiave **scavalca** i fotogrammi in volo, e non per caso: il vecchio è il più grosso e §5.2 vieta di abbandonarlo |
| ⭐ **P14** | **`numero`** — il campo che il protocollo porta già | *(regge)* |

⭐ **Che cosa andava guardato la prima volta: il campo che il protocollo porta già.** La domanda
*«questo fotogramma è stato catturato prima del cambio di tela?»* aveva **una risposta esatta dentro
i 28 byte dell'intestazione da tre giorni**: il contatore `numero`. E un fotogramma in volo ha
**sempre** un numero più basso del primo catturato dopo il cambio — non «quasi sempre»: **sempre**,
perché il contatore cresce alla cattura.

> ⛔ **La regola.** Quando si scrive una tolleranza, si nomina **la grandezza vera del fenomeno che
> si tollera** e si guarda se il protocollo — o il formato, o l'API — **la porta già**. Se si sta per
> scriverne una **sostitutiva** — una misura, un tempo, un evento — quella tolleranza si sposterà di
> un passo alla prima rilettura ostile.

⚠ **E la seconda metà è del banco, e vale quanto la prima.** Tutti e quattro i difetti sono usciti
costruendo la scena **al limite della cura appena scritta** — due cambi invece di uno, la linea lenta
invece della veloce, l'ordine d'arrivo invertito — e **nessuno** costruendo la scena che la cura
raccontava. ⇒ Il caso che conta non è quello che la regola descrive: è quello **appena fuori**.

⭐ E vale la pena notare **chi** le ha trovate, tutte e quattro: non chi rileggeva il documento, ma
chi doveva **far rispettare la regola** scrivendo l'arbitro che la giudica. *Applicare una regola è
un modo di leggerla che rileggerla non è.*

#### ⛔⛔ Il seguito del 13 agosto: le volte sono sette, e la lezione vale anche **sul contorno**

| # | La grandezza scelta | Dove si è rotta |
|---|---|---|
| **P19-P20** | §2.5: *«chi riceve un fotogramma **prima di `SESSIONE`** chiude con `ERRORE_PROTOCOLLO`»* | ⛔ **«chi ne riceve uno prima» è una grandezza sostitutiva**: i due stream QUIC sono indipendenti e niente ne ordina la consegna. Bastava **perdere il pacchetto che porta `SESSIONE`** perché un client conforme uccidesse una sessione sana — I1 rotta *perché la linea perde pacchetti*, cioè la condizione che I1 esiste per proteggere. ⭐ La grandezza vera è **`ATTACCA`**, cioè quel che il client ha spedito **lui** |
| **P21** | *«la misura che il client ha nominato»* | ⛔ **§4.5 permette al server di concedere una tela DIVERSA da quella chiesta** — su KWin < 6.8 è la strada normale. Chi chiede 1366×768 e riceve il 1280×720 che sta per essergli concesso **chiuderebbe una sessione sana**. ⭐ La grandezza vera è **«una `ADATTA_TELA` senza risposta»**, non i numeri che portava |
| ⛔⛔ **P22 — e non è una grandezza: è il CONTORNO** | §3 dichiarava *«le eccezioni sono sei, e fuori da questo elenco non se ne inventano»* | ⛔ mentre §2.5 e §6.2 **ne comandavano due che lì non c'erano**. ⇒ Un client scritto leggendo §3 **chiudeva proprio le sessioni sane che le altre due righe salvavano**. Adesso sono **otto** |

> ⭐ **La regola si allarga.** Non basta scrivere la tolleranza sulla grandezza vera: **l'elenco delle
> eccezioni è parte della tolleranza**, e invecchia da solo. Chi ne scrive una altrove **aggiunge la
> riga all'elenco nello stesso momento**, o il documento si contraddice da sé — ed è la stessa specie
> di P12, cioè un difetto **di chi scrive la specifica**, non di chi la implementa.

⭐ **E la forma comune delle tre cure è la stessa di P14**: *quel che il client ha spedito lui* —
**locale, monotono, indipendente dalla consegna**. Il campo `numero` era il primo caso; `ATTACCA` e
«una richiesta in volo» sono lo stesso principio applicato a due fenomeni diversi.

⚠ **E un agente ha rifiutato la propria prima proposta, e uno ha bocciato quella di chi lo mandava**:
*«solo se i byte di `SESSIONE` non sono ancora arrivati»* spostava la misura dal risveglio della
coroutine **ai byte, che li ritarda la rete** — sarebbe stata la settima stesura della stessa
famiglia; e *«la misura che il client ha nominato»* sarebbe stata l'ottava.

*Dettaglio: `fasi/rapporti/F2-4-filo.md`, e le righe nel riquadro in testa a `RCP.md`.*

#### ⛔ E la stessa lezione, dal lato del BANCO: **P1 a blocchi confonde il ritardo con la deriva**

*13 agosto 2026, fase 3 step 5. Non è una tolleranza di protocollo: è una tolleranza di **misura**,
e si sposta allo stesso modo.*

**P1 è il controllo decisivo dell'anello del ritardo**: il server ritarda di **N millisecondi noti**
e la mediana **deve salire di esattamente N**. Un banco che non lo supera non sa di misurare
(`web.md` §6.3).

⛔ **Il difetto: eseguirlo A BLOCCHI** — prima un blocco di campioni senza ritardo, poi un blocco
con il ritardo N. La differenza fra le due mediane contiene **due cose sommate**: il ritardo che si
è iniettato, e la **deriva** che i due orologi hanno accumulato nel tempo che separa i due blocchi.
Il banco le legge come una sola.

⚠ **E la cura che viene in mente per prima è quella sbagliata**: *allargare la tolleranza* finché il
controllo passa. È la forma esatta di §1.13 — una tolleranza scritta su una grandezza sostitutiva —
e ha il difetto in più di **rendere il controllo cieco proprio a quel che deve trovare**: un P1 con
la tolleranza larga smette di distinguere «la mediana è salita di N» da «la mediana è salita».

⭐ **La cura vera: si INTRECCIA.** I campioni con ritardo e quelli senza si alternano nella stessa
finestra di tempo, invece di stare in due blocchi consecutivi. Così la deriva agisce **allo stesso
modo sui due gruppi** e si sottrae da sé, e quel che resta nella differenza è solo il ritardo.
⇒ **La grandezza vera non era la tolleranza: era il TEMPO CHE SEPARA I DUE GRUPPI**, e la si porta
a zero invece di tollerarla.

`[M]` **P1 verde intrecciato**: N = 25 → **+25,08 ms**; N = 60 → **+58,58 ms**.
⭐ **E l'iniezione sta FUORI dal prodotto, con l'ancora d'orologio che non ci passa** — se ci
passasse, P1 passerebbe **anche a banco rotto**, che è il modo in cui un controllo decisivo smette
di esserlo senza che nessuno lo veda.

### 1.14 ⛔⛔ Un controllo che accetta **«una delle due strade»** nasconde una strada rotta per sempre

*Scritta il 13 agosto 2026, dopo che un difetto è passato **sotto le certificazioni** per due giorni.*

`RCP.md` §3.1 fa chiudere una sessione per **due strade**, e il banco che le giudica accettava
*«una delle due»*. ⇒ ⛔ **Una delle due poteva essere rotta da sempre e il banco restava verde**, perché
l'altra passava — ed è quel che è successo: `[M]` la strada persa era sempre la stessa, e il rosso è
comparso solo il giorno in cui a cadere è stata **l'altra**.

⛔ **E il difetto era più vecchio del codice che l'ha fatto emergere**: chi l'ha cercato ha sospettato
la riscrittura della sera, e i byte hanno detto che era lì da due giorni.

> **La regola.** Un criterio nella forma *«almeno una di N»* va scritto **solo** se le N sono
> davvero intercambiabili per chi le riceve. Se ciascuna ha un effetto suo — e due strade di
> chiusura ce l'hanno, perché il motivo che arriva al server è diverso — allora il criterio giusto è
> **«ciascuna quando tocca a lei»**, e il banco deve dire **quale** ha visto, non quante.

⚠ E il corollario che costa di più: **un controllo così non fallisce mai per il difetto che dovrebbe
prendere**, quindi non lo si scopre nemmeno certificandolo — i guasti innestati lo trovano verde
prima e verde dopo.

*Dettaglio: il commit `d722460` porta l'attribuzione per intero — i byte, i 33 ms contro i 3-6 dei
giri sani, e la prova che il server quello zero lo **legge** invece di sintetizzarlo. La storia della
cura dell'11 agosto sta in `README.md`. ⚠ Questa riga citava un rapporto che **non esiste**: corretta
il 13 agosto 2026, su segnalazione dell'agente che è andato a cercarlo.*

### 1.15 ⛔⛔ **Su Xvfb `requestAnimationFrame` non gira MAI** — e vale per tutti i banchi browser

*Scritta il 13 agosto 2026, fase 3. ⛔ Non è una particolarità di un banco: è una proprietà del
palco su cui girano **tutti** i banchi browser di questo progetto.*

`[M]` **0 quadri in 3 secondi**, con GPU e senza, con `visibilityState` a **«visible»**. Il browser
non dichiara niente di anomalo — la pagina si crede visibile — e i quadri semplicemente non
arrivano, perché senza schermo non c'è niente che li scandisca.

⇒ ⛔ **Ogni cammino di prodotto che passa dietro a un quadro è CODICE MORTO sul banco.** Non
«lento», non «raro»: **non eseguito**, mai, e con il banco che resta verde perché nessuno ha chiesto
se quel ramo fosse stato percorso.

> ### ⛔⛔ E la seconda metà, che è quella che ha morso davvero
>
> **In Blink l'evento `resize` si consegna DENTRO il giro di rendering** ⇒ senza quadri **non arriva
> mai**. Un intero pezzo di prodotto — quello che segue la finestra dell'utente — era irraggiungibile
> sul banco, e il banco lo dichiarava verde.
>
> ⛔ **A svegliare la conduttura era `Page.captureScreenshot`, chiamata solo `if args.copia`**: cioè
> **un'opzione di comodo di stampa**, con un effetto collaterale non dichiarato. Lo stesso banco,
> sullo stesso prodotto **sano**, dava:
>
> | | esito |
> |---|---|
> | **senza** `--copia` | ⛔ **ROSSO, 5 pretese cadute** — fra cui *«la tela è stata RICOMPOSTA (1 → 1)»* |
> | con `--copia` | verde (1 → 3) |
>
> ⛔⛔ **E il verde non era falso nel merito: era prodotto dallo STRUMENTO**, e non era mai stato
> provato capace di arrossire. Un'opzione di stampa decideva l'esito di una certificazione.

⭐ **Le tre cure, e valgono per qualunque banco browser:**

1. ⛔ **il quadro si batte apposta, un numero fisso di volte** — non «finché diventa verde», che è
   un criterio che si adatta al risultato invece di misurarlo;
2. ⭐ **si giudica PRIMA IL PALCO, e prima del prodotto**: una spia conta quadri ed eventi, e se il
   `resize` non è arrivato il banco dice *«IL PALCO, NON IL PRODOTTO»* e **si ferma**, invece di
   emettere un verdetto su qualcuno;
3. ⛔ **e il limite si scrive in testa al banco**: oggi quel banco misura *«dato un quadro, il
   prodotto segue la finestra»*, e ⏳ `[?]` **resta aperto** che il quadro arrivi **da solo** quando
   l'utente trascina una finestra vera — su Xvfb non si produce nessun quadro, quindi lì non è
   misurabile per costruzione.

⚠ **E la trappola è armata altrove senza essere ancora scattata**: un secondo banco regge solo
perché **nessuna sua pretesa passa da un quadro**. Chi ve ne aggiunga una ci cade, e ci cade in
verde. ⇒ *Un palco che non può produrre un fenomeno va dichiarato in testa al banco, o il prossimo
che scrive una pretesa non ha modo di saperlo.*

> ### ⏳ `[?]` E due misure dello stesso giorno vanno tenute AFFIANCATE, perché tirano in versi opposti
>
> | | `[M]` 13 agosto, stesso palco |
> |---|---|
> | `requestAnimationFrame` nel thread principale | ⛔ **0 quadri in 3 s** — non gira mai |
> | una `OffscreenCanvas` trasferita a un worker | ⛔ si ferma a **56,4 dipinti/s ≈ il quadro dei 60 Hz**, con **13,4-21,7 ms** di costo extra per fotogramma (`web.md` §6.1) |
>
> ⇒ ⏳ `[?]` **Sullo stesso Xvfb un cammino non vede nessun quadro e l'altro paga il quadro pieno.**
> Sono due meccanismi diversi e possono essere veri tutti e due — ⛔ **ma finché non si sa quale
> orologio scandisce il secondo, non si sa nemmeno quanto della penale del worker sia del palco e
> quanto del meccanismo.** ⇒ È la ragione tecnica per cui `web.md` §6.1 **non si seppellisce senza
> rifare il conto su hardware vero**: se quella penale è del palco, su una GPU cambia di segno.
> ⚠ *Scritto come domanda aperta e non come conclusione: nessuno dei due numeri è in discussione, è
> il loro accostamento che non ha ancora una spiegazione.*

---

## 2. Come si prova

### 2.0 ⛔⛔ Un banco che dice «no» deve dire CON CHE PALCO ha detto no

*13 agosto 2026, sera. ⛔ **È costata una corsia intera di un piano**, ed è la forma più cara
incontrata finora, perché il banco **non si è rotto**: ha risposto, con precisione, alla domanda
sbagliata.*

Una sonda chiedeva a Chrome se sapesse decodificare HEVC. Rispondeva **no**, cinque volte su cinque,
con la fermezza di una misura ripetuta. Ogni tanto usciva un **sì**, e veniva archiviato come
*«anomalia non riproducibile»*.

⛔ **La sonda lanciava Chrome con `--disable-gpu`.** Chiedeva a un browser accecato se vedesse.

| Chrome sullo stesso Xvfb | webgl | HEVC |
|---|---|---|
| **senza** la bandiera | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` | ⭐ **true** |
| **con** la bandiera | `niente webgl` | no |

Sul quel «no» era stata scritta una conclusione — *«non è un problema di codec, è un problema di
PALCO»* — e sulla conclusione **una corsia di lavoro**, dichiarata *«quella da cui comincia la
sessione»*. Il «sì» scartato come anomalia era **l'unico giro giusto**.

> ⛔⛔ **La lezione, e non è tecnica**: *«non c'è»* e *«non ho potuto guardare»* **hanno lo stesso
> aspetto**, e il secondo è più frequente del primo. ⇒ **Un banco che risponde NO deve scrivere
> accanto alla risposta la scena da cui l'ha data** — che palco, che bandiere, che hardware visibile
> — esattamente come `§1.1` pretende la scena accanto a un numero. **Un no senza la scena dichiarata
> non è un no: è un'assenza di informazione travestita da informazione.**

⭐ **E il segnale c'era già, nel verbale**: un esito che non si riproduce **una volta su sei** non è
rumore, è una **variabile non dichiarata**. ⇒ *Quando un banco dà due esiti diversi sulla stessa
domanda, la cosa da cercare non è quale dei due è vero: è **che cosa è cambiato fra i due giri**.*

> ### ⛔⛔⛔ E LA CURA DI QUESTA LEZIONE È CADUTA NELLA STESSA LEZIONE, un'ora dopo
>
> *La spiegazione qui sopra — «era la bandiera, non il palco» — è **mezza falsa**, e a trovarlo è
> stato un altro gruppo. Si lascia scritta perché **il modo in cui è caduta è la lezione vera**.*
>
> `[M]` con una controprova che **non passa dal browser** — `xlsclients`, cioè chi è davvero
> attaccato a quello schermo:
>
> | come si lancia Chrome | clienti **sull'Xvfb** | `screen` | webgl | HEVC |
> |---|---|---|---|---|
> | **come lo lanciava il banco** | ⛔ **0** | **2560×1080** | GPU | true |
> | `--ozone-platform=x11` | ⭐ **1** | 1280×1024 | *niente* | **false** |
>
> ⛔⛔ **Chrome ignora `DISPLAY` e sceglie Wayland da `XDG_SESSION_TYPE`.** ⇒ Il browser **non era
> mai stato sullo schermo finto**, in nessuno dei due bracci dell'A/B: era **sul desktop
> dell'utente**. La bandiera contava; il palco era già quello vero.
>
> ⇒ ⭐ **La lezione si rafforza invece di indebolirsi, e si allarga**: chi ha scritto la cura ha
> dichiarato una scena — *«Xvfb :85»* — **che ha creduto invece di verificare**, e l'ha scritta nel
> verbale accanto al numero. **Esattamente il difetto che stava curando.**
>
> > ⛔ **La forma completa, e vale per ogni banco browser di questo progetto**: *dichiarare un palco
> > non è averlo*. Il palco si **verifica dall'altro capo** — chi è attaccato allo schermo, che
> > misura ha lo schermo che la pagina vede, che hardware nomina — e non da come si è **lanciato** il
> > processo. **Un'intenzione scritta in una riga di comando non è una misura.**
>
> ⚠ E la conseguenza operativa è più grossa del codec da cui è partita: **i banchi browser di questo
> progetto misurano sul desktop dell'utente credendo di essere su uno schermo finto** ⇒ contesa non
> dichiarata, e ogni verbale che dice «Xvfb» dice una cosa che non è.

⚠ **Tre sorelle minori, pagate lo stesso giorno e della stessa famiglia:**

| | |
|---|---|
| ⛔ **un confronto che non era un confronto** | due codificatori cronometrati **a bitrate libero**: quello che sembrava concorrenziale consegnava **trenta volte meno byte**. ⇒ *«Più veloce» a un trentesimo del lavoro non è più veloce* — **si fissa il lavoro, e i fotogrammi in uscita si CONTANO** |
| ⛔ **un elenco creduto invece che girato** | `av1_vaapi` **compare** fra i codificatori di `ffmpeg`, e all'uso esce **218**: l'hardware l'entrypoint non ce l'ha. ⇒ *Un elenco dice che il codice c'è, non che la macchina lo sa fare* |
| ⛔⛔ **una dichiarazione d'accordo con sé stessa e discorde dai byte** | vedi §2.0-bis qui sotto: **è costata il codec dell'intero prodotto** |

### ⛔⛔ 2.0-bis Chiedere un formato non è averlo — si rilegge quel che si è PRODOTTO

*13 agosto 2026, notte. ⛔ **Il prodotto ha codificato in software per giorni per una riga di un
banco**, e la cosa notevole è che **ogni pezzo della catena rispondeva correttamente alla domanda
che gli era stata fatta**.*

Un generatore di sonde chiedeva a libx265 il profilo per nome — `-profile:v main10` — e due righe
dopo passava `-x265-params …:**keyint=1**:…`. ⛔ **`keyint=1` fa emettere «Main 10 Intra», cioè
`Rext`, `profile_idc = 4`, annullando il profilo chiesto — e senza un errore.**

Quelle sonde finivano dentro la pagina del prodotto, che le usava per decidere quali codec
dichiarare al server:

| chi | che cosa diceva | ed era **giusto** |
|---|---|---|
| la **stringa** | `hev1.1.6…` — profilo **1** | sì, per quel che dichiarava |
| i **byte** | `profile_idc = **4**` | ⛔ e nessuno li leggeva |
| `isConfigSupported` | **true** | sì: risponde **alla stringa** |
| il decodificatore | `EncodingError` **sui byte** | sì |
| la pagina | *«questo codec non arriva al pixel»* | sì, dato quel che vedeva |
| il server | negozia **l'altro codec** | sì: prende la prima voce del client |

⇒ **Nessuno ha sbagliato, e il risultato era sbagliato.** Un difetto così non lo trova chi rilegge
il codice: lo trova **chi legge i byte prodotti**.

> ⛔ **La regola**: `CODER.md` §3.9 dice *«quando si chiede un componente per nome, si verifica che
> abbia obbedito»* — e finora è stata applicata **all'ingresso**. ⇒ **Vale anche all'USCITA**: quando
> si dichiara un formato, **si rilegge il flusso e si confronta con la dichiarazione**. Una stringa e
> un flusso che non si guardano in faccia **non sono due controlli: sono zero**.

⭐ **E il costo del controllo mancante era due righe**: `ffprobe` sul flusso appena prodotto. Il
banco che adesso lo fa (`banchi/02-pagina-sonda-verifica.py`) legge le sonde **dal file del
prodotto** invece di ricopiarle, e **conta i fotogrammi** invece di chiedere.

### ⛔⛔ 2.0-ter Due misure prese in POSIZIONI diverse dentro la stessa pagina non si confrontano

*13 agosto 2026, notte. ⭐ Un banco stava per consegnare **«Firefox è il 44 % più lento di Chrome»**,
e il 44 % non era di Firefox.*

Un banco provava più configurazioni **di fila, nella stessa pagina**, e ne confrontava i tempi. Lo
scarto era stabile e riproducibile — **2,5 ms**, sempre nello stesso verso. ⛔ **Era la POSIZIONE
nella sequenza**: rovesciando l'ordine dei casi, le tre configurazioni davano lo stesso numero.

⛔⛔ **E la parte che rende la trappola cattiva**: l'effetto **tira in versi opposti sui due motori**.

| | chi corre **per primo** |
|---|---|
| **Chrome** | è il **più veloce** (7,9 ms) |
| **Firefox** | è il **più lento** (11,5 ms) |

⇒ Un banco che provasse i casi sempre nello stesso ordine — cioè **qualunque banco scritto in modo
naturale** — misurerebbe una differenza fra i due motori **che non esiste**, e la misurerebbe
**stabile**, cioè con tutta l'aria di un fatto.

> ⛔ **La regola**: *quando si confrontano N configurazioni dentro uno stesso processo, l'ordine è
> una variabile* — e come ogni variabile va **dichiarata e rovesciata**. ⭐ Il controllo costa **un
> giro in più**: si rifà la sequenza al contrario, e se i numeri si spostano, quel che si stava
> misurando era la sequenza.

⚠ **E c'è una sorella, trovata la stessa notte, che riguarda le finestre esclusive**: un banco che
misura N configurazioni di fila **è il vicino di sé stesso** — il carico a un minuto è una media, e
la configurazione appena finita si presenta come contesa a quella dopo. `[M]` **5 rifiuti su 8** con
*«browser altrui: 0»*. ⛔ **La cura non è alzare la soglia** — sarebbe spegnere l'arbitro — ma
**aspettare che la propria scia si spenga** prima di chiedere il permesso.

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

> ⛔ **E c'è una quarta riga di quella tabella, trovata il 13 agosto 2026, che non riguarda quel che
> il banco guarda ma l'unità in cui lo guarda**: una prova può essere verde per tutto il tempo
> in cui il difetto è vivo perché esercita il giudice nell'unità del **lettore** invece che in
> quella dell'**acquisizione**. Il banco guarda la cosa giusta, la conta bene, e la conta **nella
> grandezza sbagliata**. ⇒ Il rimedio sta in §1.2, ed è una domanda in più al momento della
> certificazione, non un controllo in più al momento della misura.

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
| 6 | **Quanto consegna, con una scena che cambia a ogni ridisegno?** | ⛔ **la domanda è mal posta, `[M]` 13 ago**: dipende da **come** si chiede. Chiedendo 60 a un monitor a 60: **31,5** (il «~37» di v1 **non si riproduce**). Chiedendo **90 a un monitor a 120**: **61,4**. ⇒ Alla domanda 7, e non a questa | **59–60** | **61** (40 a 4K, per il costo della copia) |
| 7 | **La cadenza dichiarata come si comporta?** | ⭐ `[M]` **13 ago**: **dipende da come si chiede**, e disaccoppiando — monitor **120**, freno **90** — se ne ottengono **61,4**; i «sei decimi» **non si riproducono** (la cella bassa dà **0,50 pulito**). ⚠ **Il perché è `[R]`, non `[M]`**: `maxFramerate` fa due mestieri insieme — freno della cattura *ed* frequenza del monitor virtuale — e nel codice il freno calcola `min_interval_us = 10⁶/maxFramerate` **troncato a intero** contro un tick da 16666,67 µs ⇒ chi cade sotto **perderebbe un tick intero**: una **griglia**, non un battimento. ⛔ *Questa cella dava la griglia come `[M]` «su 13 punti»: falso, corretto il 13 ago sera — vedi il riquadro sotto la tabella.* | **fissa rifiutata anche qui** (`framerate` deve valere `0/1`); il tetto è `maxFramerate`, e lo **onora il server** [R] | da misurare |
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

> ## ⛔⛔ ~~I sei decimi di Mutter~~ → **MISURATO il 13 agosto: non è un battimento, è una griglia**
>
> *Questo riquadro, scritto il 9 agosto 2026 leggendo `gnome.md` §8.2, diceva: «`maxFramerate` è il
> freno della cattura e insieme la frequenza del monitor virtuale. **Due orologi allo stesso numero
> battono fra loro, e il battimento vale 0,61**. Costa tre celle e zero righe di prodotto, e se
> riesce porta i 60 su GNOME». Era `[R]`, e portava accanto la propria riserva: «finché non è
> misurata resta una `[?]`; una spiegazione che torna non è una cura che funziona» (§1.11).*
>
> ⭐ **La riserva era quella giusta, e la misura le ha dato ragione due volte: la cura funziona, e la
> spiegazione era sbagliata lo stesso.**
>
> ⭐ **IL FATTO, `[M]`**: monitor a **120**, freno a **90**, e GNOME consegna **61,4** — cella **D**
> di `banchi/03-b14-esiti.jsonl`, pulita, coi tre controlli che chiudono.
>
> ⚠ **LA CAUSA, `[R]`**: letta nel codice di Mutter, `maxFramerate` non sembra un tetto continuo ma
> una **GRIGLIA**. Il freno calcola `min_interval_us = 10⁶/maxFramerate` **troncato a intero** —
> 16666 per 60 — contro un tick da **16666,67 µs**: chi cade sotto **perde un tick intero**. Non un
> **battimento** fra due orologi, una **quantizzazione**. ⭐ **È la spiegazione migliore che
> abbiamo**, ed è coerente con la cella D. ⛔ **Ma è una lettura, non una misura.**
>
> > ⛔⛔ ⚠ *Questa riga diceva: «`[M]` legge verificata su **13 punti**: 8 la confermano, **0 la
> > smentiscono**». **È FALSA.** Il file degli esiti della griglia,
> > `banchi/03-b14-esiti-griglia.jsonl`, porta **tre righe**: il terreno e **due celle**
> > (`griglia-apertura-120`, `griglia-freno-90`), **tutt'e due con `scena_sul_mio_monitor: false`**
> > ⇒ rifiutate dal banco stesso, che stampa «⛔ la legge NON regge su **0 punti su 0**». I tredici
> > punti non esistono in nessun file di esiti. **Corretta il 13 agosto 2026**, rilievo del
> > coordinatore della fase 3, verificato sui due file di esiti. ⇒ La quantizzazione torna `[R]`; la
> > tabella qui sotto resta `[M]`, perché viene tutta da `03-b14-esiti.jsonl`, sette celle tutte con
> > `scena_sul_mio_monitor: true`.*
>
> | monitor | freno | consegnati | mediana | p99 |
> |---|---|---|---|---|
> | 60 | 60 | 31,5 | 33,31 ms | 35,53 |
> | 120 | 60 | 46,13 | 24,12 ms | 29,23 |
> | ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61,4** (60,04) | ⭐ **16,66 ms** | 20,43 |
>
> ⛔ **E i «sei decimi» non si riproducono**: la cella bassa dà **0,50 pulito e deterministico** —
> che è quel che una griglia produce, e un battimento no.
>
> ⭐ **La cura riesce**: monitor 120, freno 90, e GNOME consegna **61,4**. ⛔ **Ma il prodotto oggi
> non sa chiederla** — `MOVIMENTO_FPS 60` è una costante di compilazione, `RecordVirtual` non prende
> la frequenza, e i monitor virtuali sono tutti @60. È `[M]` **sul banco** e **zero in produzione**.
>
> > ### ⭐⭐ E la lezione, che vale più del numero
> >
> > **Una spiegazione che torna, che spiega tutti i dati che abbiamo e che indica pure una cura che
> > poi funziona, può essere comunque falsa** — e non se ne accorge nessuno, perché la cura
> > funzionando la conferma. Qui il battimento spiegava lo 0,61, indicava il disaccoppiamento, e il
> > disaccoppiamento ha portato i 60: tre conferme di fila per una causa sbagliata.
> >
> > ⛔ **A smontarla non è stata la cura: è stata la CELLA APPENA FUORI** — la cella bassa, che il
> > battimento vuole a **0,61** e che dà **0,50 pulito e deterministico**. Il battimento e la
> > quantizzazione **prevedono la stessa cosa sulla cella che si voleva curare**, e cose diverse
> > **fuori**. ⇒ È §1.13 nella sua forma generale: *il caso che distingue due spiegazioni non è
> > quello che le ha prodotte, è quello appena fuori* — e la cella che le distingue costa quanto
> > quella che le conferma.
> >
> > > ⛔⛔ ⚠ *Questo capoverso diceva: «A smontarla non è stata la cura: è stata la **MISURA A
> > > TAPPETO** — **13 punti** invece dei tre che servivano a dimostrare che funziona». **È falso, e
> > > la misura a tappeto non c'è mai stata**: le sue due sole celle sono rifiutate dal banco stesso
> > > (riquadro qui sopra). A smontare il battimento è stata **una** cella pulita, la A. **Corretto
> > > il 13 agosto 2026**, rilievo del coordinatore della fase 3.* ⇒ ⭐ **E la lezione ne esce più
> > > forte, non più debole**: non serviva il tappeto, **bastava il caso appena fuori** — purché sia
> > > valido.

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

> ⭐⭐ **E il 13 agosto 2026 la lezione si è avverata una seconda volta, sul numero che questa
> sezione cita.** *«Chiedendone 60 ne arrivano 37»* non è un tetto: `[M]` **non si riproduce
> affatto** — alla cadenza che chiedevamo ne arrivano **31,5**, e chiedendone **90 a un monitor a
> 120** ne arrivano **61,4**. ⚠ **Il perché è `[R]`**: nel codice di Mutter il freno calcola
> `min_interval_us = 10⁶/maxFramerate` **troncato a intero** (16666 per 60) contro un tick da
> 16666,67 µs ⇒ chi cade sotto **perderebbe un tick intero** — il resto di una **divisione
> troncata**. *La sera del 13 agosto questa spiegazione era scritta qui come misurata: non lo è,
> vedi il riquadro di §3 domanda 7 e `gnome.md` §8.2.*
>
> ⇒ ⛔ **Il tetto era di nuovo un numero che avevamo scritto noi, e stavolta era scritto due volte**:
> una nella cadenza che chiedevamo, e una **nel modo in cui il compositore la converte**. La forma
> generale della lezione si allarga: non basta chiedersi *«quale numero abbiamo dichiarato?»*, va
> chiesto **«che cosa ne fa chi lo riceve?»** — perché un troncamento non si vede né nel nostro
> codice né nel numero che abbiamo scritto.

### 6.2 Millisecondi di CPU per fotogramma e fotogrammi al secondo sono due grandezze diverse

E possono muoversi in direzioni opposte. Misurato due volte:

| | CPU per fotogramma | fotogrammi al secondo |
|---|---|---|
| togliendo la codifica dalla CPU (fase 9) | 41 → 20 | 29 → **22,7** |
| accendendo la copia zero (fase 9, poi verificata sulla catena intera) | 16 → **3** | 32,4 → **31,5** |

**Un guadagno che si paga in fluidità non è un guadagno**, e va detto invece di mostrare il solo
numero della CPU. La copia zero vale cinque volte sul consumo e **zero** sul ritmo: chi la riprende
lo faccia per quello.

> ### ⛔⛔ E il 13 agosto 2026 è arrivato **il caso rovescio**: il ritmo sale, il ritardo **non si muove**
>
> *Le due righe qui sopra sono dello stesso segno: la CPU migliora e il ritmo peggiora. Servivano a
> impedire di vendere un guadagno di CPU come un guadagno di fluidità. ⛔ **Manca il caso opposto, e
> alla fase 3 ci si è quasi cascati.***
>
> | la leva | il ritmo | il ritardo |
> |---|---|---|
> | la cadenza disaccoppiata (monitor 120, freno 90) | ⭐ **da 31,5 a 61,4/s** | ⛔ **fermo**: `[M]` mediana **74,58 ms**, e Mutter ne vale il **22 %** |
>
> ⛔ **Raddoppiare i fotogrammi al secondo non ha tolto un millisecondo al ritardo**, e la ragione è
> che il collo era altrove: **58 ms su 74,6 sono nostri**, quasi tutti nel codificatore in software.
> I 60 fotogrammi **tolgono un ostacolo**; il numero che l'utente sente lo fa il ritardo.
>
> ⇒ ⭐ **La lezione, nella forma che le mancava: sono TRE grandezze, non due.** Millisecondi di CPU
> per fotogramma · fotogrammi al secondo · **ritardo**. Si muovono indipendentemente, e ciascuna
> coppia ha già prodotto una riga sbagliata in un documento di questo progetto.
>
> ### ⛔⛔ E la stessa sera è arrivato il caso che le fa dire cose OPPOSTE — la pagina nel worker
>
> | | thread principale | worker |
> |---|---|---|
> | ⭐ **fotogrammi dipinti sulla catena vera** | 22,8-24,2 /s | ⭐ **26,3 /s** — *il worker dipinge di PIÙ* |
> | ⛔ **tetto a saturazione, 1080p** | **127,6 /s** | ⛔ **33,9 /s** (**−73,4 %**) |
> | ⛔ **tetto a saturazione, 480p** | **230,6 /s** | ⛔ **56,4 /s** (**−75,5 %**) |
> | ⛔ **mediana del ritardo** | 73,66 / 67,79 ms | ⛔ **101,30 ms** |
>
> ⛔ **Sulla catena vera il worker sembra migliore. A saturazione è tre quarti peggiore. E il ritardo
> dice che è peggiore comunque.** ⇒ ⚠ **Quale conclusione si porta a casa dipende da quale grandezza
> si è scelta per prima** — che è il modo più educato in cui una misura può mentire.
>
> ⭐ **La regola pratica**: quando una leva tocca il percorso del video, le tre grandezze si
> **misurano e si scrivono tutte e tre**, anche quelle che non interessano. Una tabella con una
> colonna sola non è una misura corta: è una misura **orientata**.
>
> ⚠ **E il numero della catena vera aveva una spiegazione, che è la terza cosa da guardare**: il
> worker dipingeva di più perché **c'era la coda**. Un vantaggio che esiste solo finché il sistema
> non è al limite è un vantaggio che sparisce **il giorno in cui serve** (`web.md` §6.1).

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

### 7.5 ⭐⭐ Una deduzione al posto di un messaggio è un difetto che aspetta

*15 agosto 2026, notte. Trovata refutando la cura appena scritta, e vale per l'architettura, non
per una riga.*

La catena che porta la misura della finestra fino al compositore era scritta e funzionava. Il
padre chiedeva al figlio di ridimensionare, e poi **deduceva l'esito dai fotogrammi**: *«se ne
arriva uno di misura diversa, il palco ha obbedito»*. Era fedele a una regola giusta di questo
progetto — *«la verità la dice il fotogramma, non l'esito della richiesta»* — e passava tutti i casi
che avevo in mente.

⛔ **Tre agenti mandati a smentirla hanno trovato tre casi che non avevo in mente**, e sono tutti
comuni:

| il caso | che cosa deduceva il padre |
|---|---|
| il palco ha **già** quella misura | «non ha ancora obbedito» ⇒ tre secondi di attesa per una cosa già fatta |
| il palco **non c'è** o non ce l'ha fatta | «sta ancora provando» ⇒ tre secondi per una notizia che c'era subito |
| **due richieste incatenate** (l'utente trascina il bordo) | il fotogramma della PRIMA preso per la risposta della SECONDA ⇒ desktop della misura sbagliata, **coi conti dei messaggi in ordine** |

⇒ La cura non è stata «più controlli», ed è la parte che conta: è stata **un messaggio in più**, dal
processo che sapeva al processo che decideva — con dentro *a quale domanda risponde* e *che cosa è
successo davvero*.

> **Quando un pezzo deve dedurre qualcosa che un altro pezzo sa già, la deduzione non è un
> risparmio: è un difetto che aspetta il caso a cui non hai pensato.**

⚠ E il segnale che la distingue da una deduzione legittima è **sempre lo stesso**: la deduzione
regge finché gli eventi sono uno per volta, e cade appena se ne accavallano due. Se il caso «due
richieste in volo» non ha una risposta ovvia, la deduzione va sostituita da un messaggio.

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
