# F4 · O1 — L'apparizione del desktop

*14 agosto 2026. Anello **O1** della fase 4, banco `banchi/04-b31-*`, porte 7711-7715, albero
`04-o1-src`, utente di prova `provao1` (uid 1004).*

---

## 1. Che cosa cambia per l'utente

> ⭐ **Fra il login e il desktop l'utente aspettava 5,1 secondi. Adesso ne aspetta 1,1.**

`[M]` 14 agosto 2026, macchina di prova, stessa scena, stesso quarto d'ora, **misurato dal lato che
riceve** — il client cronometra dall'istante in cui manda `CREDENZIALI` fino al fotogramma in cui
**c'è il desktop** (non «un fotogramma qualunque»):

| | login → primo pixel VERO | di cui dopo `SESSIONE` |
|---|---|---|
| ⛔ **il prodotto com'era** | **5,11 · 5,04 · 5,04 · 5,11 s** | **4,04 s** |
| ⭐ **curato** | **1,04 – 1,13 s** (7 giri) | ⭐ **0,034 – 0,124 s** |

⛔ **E dei 1,1 s che restano, 1,00 s è il secondo fisso che `RCP.md` §4.4-bis impone al server prima
di rispondere a `CREDENZIALI`.** Cioè: **quel che è nostro, dopo la cura, sono 34-124 millisecondi.**
Sotto il secondo non si scende senza toccare §4.4-bis, e quella è una regola di sicurezza.

⭐ **E in più, due difetti che potevano rovinare la macchina dell'utente sono spenti:**

| | prima | dopo |
|---|---|---|
| il registro scritto a raffica quando muore la sessione grafica | ⛔ **151,9 MB/s** (30,8 GB in ~3 min) | ⭐ **284 B/s** |
| il nucleo bruciato da un figlio senza palco | ⛔ **1,00** | ⭐ **0,00** |
| il desktop dopo che la sessione grafica torna | ⛔ **non torna mai** (zero fotogrammi) | ⭐ **1,11 s, stesso figlio** |

---

## 2. Serve una decisione di Nic?

**No, non per la cura.** ⭐ Due cose però le deve sapere, e una la deciderebbe lui se volesse:

1. ⚠ **il pavimento è il secondo fisso di §4.4-bis.** Oggi l'utente aspetta ~1,05 s, e il 95 % è
   quel secondo. Abbassarlo si può — è una scelta di sicurezza contro chi prova le parole d'ordine
   a raffica — ⛔ ma **non lo tocco io**: è `RCP.md`, ed è una decisione, non una misura;
2. ⚠ **il palco che non torna entro mezzo minuto.** Se la sessione grafica resta giù a lungo, il
   figlio riprova con un'attesa che raddoppia fino a **30 s**. ⇒ Nel caso peggiore il desktop
   ricompare 30 s dopo che la sessione è tornata. Si può stringere, al prezzo di più tentativi a
   vuoto. `[?]` nessuno ha misurato quanto dura davvero un'assenza vera.

---

## 3. Che cosa ho MISURATO

Tutto `[M]` 14 agosto 2026, `192.168.0.2`, GNOME 48.7 headless **senza** `--virtual-monitor` (la
cura di A1), HEVC in hardware (`hevc_vaapi`, `/dev/dri/renderD128`), utente nel gruppo `render`,
**scena dichiarata e in movimento** (una finestra che scrive l'ora 5 volte al secondo).

### ⛔⛔ LA TESI 1 DEL MANDATO È FALSA, E LA SMENTITA HA UNA PILA SOTTO

> *«Il ritardo NON è nostro: è l'attesa che Mutter consegni un fotogramma su un desktop fermo.»*

⛔ **Falsa.** I quattro secondi erano nostri, e stavano in **una riga di `figlio.c`**.

**Come si è arrivati alla prova, e i due passi falsi in mezzo:**

| | |
|---|---|
| il primo indizio, dal registro | fra l'accensione del canale video e il primo fotogramma il figlio scriveva *«0 fotogrammi consegnati, **0 attese a vuoto**»*. ⭐ **Zero attese a vuoto vuol dire che il ciclo non ha nemmeno provato a catturare** — cioè il contrario di «la scena è ferma» |
| ⛔ la sonda leggera ha mentito, due volte in modo diverso | campionando `/proc/<pid>/syscall` ogni 50 ms, un giro diceva `futex` per tutti e 4 i secondi e il giro dopo `recvmsg`. ⚠ **Due misure diverse sotto la stessa etichetta** — peggio che nessuna misura |
| ⭐ **la pila, con `gdb`, a 2,6 s dal login** | `#3 recvmsg · #4 ricevi_con_credenziali (fd=3) figlio.c:336 · #5 figlio_vive figlio.c:2524`. ⛔ **Il figlio era fermo dentro `recvmsg` sul socket del padre** |

**Il difetto, in una riga:** nel ciclo del figlio, `poll()` guarda **due** descrittori — il padre e
`libei` — e il codice calcolava `pf.revents` **senza guardarlo mai**. Quando `poll` si svegliava
perché aveva parlato `libei`, il figlio leggeva lo stesso il socket del padre — che dal lato del
figlio è **bloccante di proposito** (`O_NONBLOCK` lo mette il padre solo sul suo capo, e
`socketpair` fa due descrizioni di file distinte). ⇒ Il figlio restava dentro `recvmsg` finché il
padre non gli scriveva qualcosa, e **il ciclo dei fotogrammi non girava affatto**.

⇒ La cura è `if (!pf.revents) break;`. **Una riga**, e il ritardo passa da 4,04 s a 0,08 s.

⚠ **E la riga di registro che avrebbe dovuto smascherarlo accusava Mutter**: *«attese a vuoto (scena
ferma: Mutter consegna solo quando qualcosa cambia)»* con lo zero accanto. Il numero era giusto e la
parola sbagliata. ⇒ Adesso, quando i tre contatori sono tutti a zero, la riga aggiunge da sé
*«ZERO attese a vuoto vuol dire che il ciclo NON HA NEMMENO PROVATO a catturare»*.

### ⭐ Le tesi 2 e 3 — vere nel codice, e **non servono**

| tesi | esito |
|---|---|
| 2. *«il fotogramma ce l'avevamo già in `tenuto[]`, e c'è `MSG_RIMANDA_PALCO`»* | ⭐ **vera**: `[M]` il figlio codifica il primo fotogramma a **+0,21 s** dal login. ⛔ **Ma non l'ho usata**: con la riga curata il ciclo consegna un fotogramma **fresco** in 34-124 ms dopo `SESSIONE`, cioè prima di quando il client potrebbe chiederlo |
| 3. *«quel fotogramma è preso troppo presto per essere buono»* | ⭐ **vera, e misurata nei due versi**: `[M]` in un giro con la sessione appena nata il fotogramma di nascita era di **2 323 byte**; in un giro con la sessione già dipinta era di **35 834 byte**. ⇒ **Dipende da quanto GNOME aveva dipinto, e il prodotto non ha modo di saperlo** |

⛔⭐ **Perché il `tenuto` NON si rimanda, ed è la cosa che ho deciso di non fare.** Il mandato chiede
un criterio che distingua «vuoto» da «pieno» e che sia **certificato**. `cattura.c` sa già dire
`nero` e `uniforme` — misurati sui pixel — ⛔ **ma il fotogramma da 2 323 byte non è né nero né
uniforme: è lo sfondo di GNOME senza la shell.** Distinguerlo vuole i due indicatori che A1 ha
calibrato (il bordo della barra e i fronti dell'orologio), che girano su **RGB decodificato**, cioè
nel banco e non nel prodotto. ⇒ **Un criterio sui byte sarebbe un indizio travestito da misura**, e
mandarlo farebbe comparire uno schermo vuoto — che è esattamente quel che il mandato vieta.
⭐ **Non serve: il fotogramma fresco arriva prima.**

### ⭐ Le due piste che il mandato proponeva, e perché non le ho prese

| pista | esito |
|---|---|
| riavviare la cattura all'accensione del canale video | ⛔ **non serve**: il flusso consegnava già, eravamo noi a non essere lì a prendere. ⚠ Il riavvio della cattura **c'è**, ma per un'altra ragione: il rimontaggio del palco (§ qui sotto) |
| montare il monitor più tardi | ⛔ **non serve**, per la stessa ragione |
| l'`attesa 0.25 s` del ciclo | ⛔ **non era il collo di bottiglia**: `ciclo_zero` valeva **0**, cioè quell'attesa non si spendeva mai |

### ⛔⭐ I DUE DIFETTI GEMELLI — curati insieme, perché sono lo stesso fatto

*Il figlio non sa che il suo palco non c'è più, o non c'è ancora.*

⭐ **La cura è una sola: il palco si monta, si smonta e si RIMONTA**, con un'attesa che raddoppia da
1 s a 30 s. Il figlio **non esce** (`SPECIFICHE.md` §8.3 vieta di staccare) e **non resta fermo** —
un figlio senza palco non è una sessione ferma.

| scena | ⛔ prodotto com'era | ⭐ curato |
|---|---|---|
| **G1** la sessione grafica muore sotto un figlio vivo, client attaccato | **151 925 902 B/s** di registro e **1,00 nuclei** | **284 B/s**, **0,003 nuclei** |
| **G2** il figlio nasce quando la sessione non c'è | **1,00 nuclei**, e in silenzio (233 B/s) | **0,00 nuclei** |
| **G2-bis** poi la sessione nasce, e si riattacca | ⛔ **ZERO fotogrammi in 20 s** — I2 consegna lo stesso figlio rotto, due volte di fila | ⭐ **1,11 s, VERDE**, e il registro dice *«RIAVVIO LA CATTURA: il palco è tornato dopo 2000 ms»* |
| **G1-ripresa** la sessione torna sotto lo stesso figlio | *(non misurabile: il figlio non riprovava)* | ⭐ **1,12 s, VERDE, pid del figlio invariato** |

⛔⭐ **E il ciclo a vuoto ha DUE facce, e una è muta.** Con il client che chiede chiavi (come fa un
client vero che non vede niente, §5.2) il registro esplode; **senza**, il figlio brucia lo stesso un
nucleo intero e **non scrive niente**. ⇒ Il banco misura **tutt'e due** le grandezze, e un banco che
avesse guardato il solo disco avrebbe dichiarato sano un figlio che teneva un nucleo al 100 %.

### Il banco, e dove si ricontrolla

`banchi/04-b31-*`, esiti in `banchi/04-b31-esiti.jsonl` (26 righe, il prima e il dopo di ciascuna scena).

```
bash banchi/04-b31-lancia.sh certifica          # lo strumento, senza il prodotto
bash banchi/04-b31-lancia.sh porta              # (PRIMA=1 per il prodotto com'era)
bash banchi/04-b31-lancia.sh costruisci
bash banchi/04-b31-lancia.sh utente · sessione · accendi · scena
bash banchi/04-b31-lancia.sh misura <etichetta> [attesa]
bash banchi/04-b31-lancia.sh g1 <etichetta>     # la sessione muore sotto il figlio
bash banchi/04-b31-lancia.sh g2 <etichetta>     # il figlio nasce senza sessione
```

⭐ **Il giudice dei pixel è quello di A1, importato e non ricopiato** (`04-b20-desktop-vero.py`):
soglie, regola di verdetto e lettura della luminanza vengono da lì. ⛔ E la certificazione
**controlla che i miei conti siano identici ai suoi** sulle stesse due immagini fabbricate — senza
quel controllo qui ci sarebbe un secondo giudice, e allora nessuno dei due è l'arbitro.

**La certificazione dello strumento, tutta senza prodotto, senza GNOME e senza rete:**

| | |
|---|---|
| il giudice dei pixel sa dire SHELL **e** VUOTO | 2 su 2 (il `--certifica` di A1) |
| i miei B e T contro i suoi | **identici** (0,12/0 e 135,09/264) |
| ⭐ il cronometro su un giro fabbricato | **4 casi su 4**: VERDE a 1,20 s · ROSSO a 5,20 s · ⛔ **ROSSO con quattro fotogrammi VUOTI spediti subito e il desktop a 5,20 s** · ROSSO «il desktop non compare mai» |
| ⛔ il rifiuto di indovinare | 6 fotogrammi decodificati contro 5 arrivati ⇒ **NON GIUDICABILE**, e non un allineamento a occhio |
| lo ZERO ha un codice suo | uscita 5, e non «il desktop non c'è» |
| il ciclo a vuoto | **6 casi su 6**, compresi *«gira a vuoto in silenzio»* e *«scrive a raffica senza consumare»* |

⛔ **E il banco è certificato SUL DIFETTO VIVO**, con l'albero di HEAD (`PRIMA=1`): `misura` dice
**ROSSO 4,05 s**, `g1` dice **GIRA A VUOTO 151,9 MB/s + 1,00 nuclei**, `g2` dice **ZERO FOTOGRAMMI**.

---

## 4. ⛔ Che cosa NON ha funzionato

| | |
|---|---|
| ⛔ **la sonda leggera ha dato due risposte opposte** | `/proc/<pid>/syscall` a 50 ms: un giro `futex`, il giro dopo `recvmsg`. Ci ho creduto per due giri prima di accorgermene. ⭐ **Solo `gdb` ha chiuso la domanda**, e la lezione è che un campionamento non è una prova quando il difetto dura pochi secondi |
| ⛔ **ho ricopiato l'albero a server acceso** | il `rm -rf` ha cancellato il binario sotto i piedi del processo; il figlio ha fatto `execve` su un percorso morto, **uscita 37**, e il banco ha detto ZERO FOTOGRAMMI. ⚠ Il registro accusava il PRODOTTO di un difetto del lanciatore, e da fuori i due hanno la stessa faccia. Curato: `porta` adesso spegne il server per primo |
| ⛔ **la prima scena di G1 era VERDE sul difetto vivo, due volte** | (a) il client girava in sottofondo e moriva con la stretta di mano `ssh` ⇒ `codec_chiesto` a zero, e un figlio che nessuno guarda non gira a vuoto; (b) uccidendo il solo `gnome-shell` il flusso PipeWire resta vivo e `cattura_prendi` torna **ZERO**, non guasto. ⭐ Il difetto compare solo se se ne va **anche PipeWire** — che è quel che dice il registro dell'utente, *«connection error»* |
| ⛔ **e nemmeno bastava: serviva un client che CHIEDE CHIAVI** | con un client muto, il figlio resta bloccato in `recvmsg` (il difetto n. 1) e **il ciclo a vuoto non compare affatto**. ⇒ ⭐ **I due difetti si mascherano a vicenda**, e il primo nascondeva il secondo. Il banco adesso manda `RICHIEDI_CHIAVE` ogni 0,5 s, che è quel che fa un client vero che non vede niente (`[M]` A1 ne ha visti dodici di fila) |
| ⛔ **tre strade per rimettere in piedi la sessione, tutte rifiutate** | `systemctl --user start org.gnome.Shell@wayland` e `stop gnome-session-manager@gnome` escono *«may be requested by dependency only»*; un `gnome-session` nuovo con il gestore ancora attivo **esce in silenzio**. ⚠ Il sintomo era «la sessione non è partita in 60 s» con un registro **vuoto**. ⭐ La strada buona è chiedere il congedo al gestore (`org.gnome.SessionManager.Logout 2`) |
| ⛔ **il fabbricatore del giro finto sbagliava di UN fotogramma** | il demuxer `concat` ne produce uno in più, e la certificazione falliva su tutt'e quattro i casi **accusando il giudice**. ⭐ L'ha trovato il controllo che **rifiuta di allineare due liste di lunghezza diversa** — cioè il controllo funziona |
| ⚠ **la tela concessa resta una promessa che nessuno mantiene** | non l'ho toccata: è la `[?]` n. 1 della fase, lavoro della fase 6 |
| ⚠ **e resta un pezzo cieco che non ho misurato** | fra il fotogramma completo al client e il **pixel acceso** ci sono la decodifica e il disegno: `[M]` A2 dice **2,25 ms** per il disegno, ma il totale «login → vetro» non l'ho misurato. Il mio numero finisce al **fotogramma completo in mano al client** — e il confine sta nella direzione scomoda solo a metà |

---

## 5. Le cuciture che chiedo al coordinatore

⭐ **Nessuna interfaccia è cambiata**: `figlio.h`, `cattura.h`, `input.h` e `cursore.h` sono
identici. La cura vive tutta dentro `src/figlio.c` (`prendi_il_palco` è `static`), e
`src/cattura.c` / `src/cattura.h` **non sono stati toccati**.

### ⛔ Una cosa da girare a O2, ed è un numero

**`[R]` Mentre il figlio cattura, un `MSG_INPUT` può aspettare fino a `MOVIMENTO_ATTESA_S` = 250 ms.**
Il ciclo, quando sta catturando, entra in `cattura_prendi(cat, 0.25, …)` e lì dentro **non guarda il
socket del padre**. Su una scena in movimento la presa torna in ~80 ms; ⛔ **su un desktop fermo
l'attesa si spende tutta, e sono cinque volte il tetto di 50 ms di `CODER.md` §1-bis.**

⚠ Prima della mia cura questo era invisibile perché il difetto grosso lo copriva. `[?]` **quanto
morda davvero non l'ho misurato** — è il mestiere di O2, e il suo metro (`04-b30-anello-input`) lo
vedrebbe.

⭐ **La firma che propongo, se il coordinatore vuole chiuderla** — i due file sono miei, la posso
scrivere io:

```c
/* in `src/cattura.h` — aspetta il prossimo fotogramma OPPURE che `fd_sveglia`
 * diventi leggibile, e dice quale delle due e' successa.
 * ⛔ `fd_sveglia` NON viene letto: si guarda e basta.  Chi lo passa resta il
 *    padrone dei suoi byte. */
CatturaPresa cattura_prendi_o_sveglia(Cattura *cattura, double attesa_s,
                                      int fd_sveglia, gboolean *svegliato,
                                      CatturaFermo *fuori, GError **sbaglio);
```

e in `figlio.c` la chiamata diventerebbe
`cattura_prendi_o_sveglia(cat, MOVIMENTO_ATTESA_S, fd_figlio, &svegliato, &fo, &sbaglio)`,
con il ciclo che riparte da capo quando `svegliato` è vera.

### ⚠ Due righe di documento che la mia misura contraddice

1. `fasi/04-si-comanda.md` §A2 dice che la causa dei «1 748 consegnati, 0 dipinti» è **«il monitor
   aggiunto e vuoto: nulla si muove, Mutter non consegna»**. ⛔ È vero per il difetto di A1, ⚠ **ma
   la stessa frase è stata usata per spiegare i 4 secondi del login, e lì è falsa**: Mutter
   consegnava, il figlio non era lì a prendere;
2. `src/figlio.c` diceva, in commento sopra `MOVIMENTO_ATTESA_S`, *«su un desktop FERMO Mutter non
   consegna niente: questa attesa scade tutta»*. ⚠ Resta vero — ⛔ ma **non era quel che stava
   succedendo**, e il commento ha guidato la diagnosi nella direzione sbagliata. L'ho lasciato, con
   accanto la riga che dice come distinguere i due casi **dal registro**.

---

## Che cosa resta `[?]`

1. `[?]` **il totale «login → pixel acceso sul vetro»**: il mio numero finisce al fotogramma
   completo in mano al client. Mancano decodifica (`[M]` A2: 2,25 ms il disegno) e i 16-40 ms che
   nessuna API espone;
2. `[?]` **quanto morde l'attesa di 250 ms sull'input** su un desktop fermo (vedi §5);
3. `[?]` **quanto dura un'assenza vera della sessione grafica**, cioè se il tetto di 30 s
   dell'attesa che raddoppia sia troppo o troppo poco;
4. `[?]` **il secondo fisso di §4.4-bis è il 95 % di quel che l'utente aspetta adesso**: è una
   decisione di sicurezza, e va guardata sapendo questo numero.
