# SESSIONE.md — la scaletta di una sessione, passo per passo

> ⛔ **Perché questo documento esiste, e perché non esisteva prima.**
>
> La mattina del **16 agosto 2026** l'utente ha provato cinque volte la stessa scena — collegati,
> esci, ricollegati — e ogni volta ha trovato un difetto diverso: bande nere, desktop «rotto»,
> nessun input, il desktop che compare dopo molti secondi. ⛔ Ogni volta si curava **il sintomo che
> il registro mostrava**, e si tornava a provare.
>
> ⭐ Erano **quasi tutti lo stesso difetto**, visto da facce diverse: un passo di questa scaletta
> che non era mai stato scritto, e quindi nemmeno verificato.
>
> ⇒ *«Prepara una nota in cui riporti la scaletta punto per punto di cosa deve avvenire per il
> corretto set-up di una sessione»* — **suggerimento dell'utente**, ed è il documento che avrebbe
> risparmiato quella mattina.

⚠ **Come si legge**: la colonna «se manca» è quella che serve quando qualcosa non va. Si parte dal
sintomo, si trova il passo, e si guarda **chi** doveva farlo. ⛔ Non si parte mai dal codice.

---

## Parte A — quel che dev'essere vero PRIMA, e non lo fa il prodotto

*Sta in `src/provisiona.sh`, e si verifica con `sudo bash src/provisiona.sh verifica`.*

| # | che cosa | chi | se manca |
|---|---|---|---|
| A1 | l'**utente esiste** e ha una parola d'ordine | provisioning | PAM rifiuta: «utente o parola d'ordine non corretti» — e la diagnosi punta sulla parola |
| A2 | ⛔ l'utente è nei gruppi **`video`** e **`render`** | provisioning | ⚠ **il sintomo è «lento», non «rotto»**: senza seat non arrivano le ACL di `uaccess`, Mesa ripiega su **llvmpipe** e il compositore disegna in software. `[M]` un comando nel terminale risponde dopo un secondo |
| A3 | `/etc/pam.d/remotix` esiste **e chiama `pam_systemd`** | provisioning | nessuna sessione logind ⇒ il compositore **non parte affatto** (vedi B3) |
| A4 | la regola **polkit** (12 azioni) e `logind.conf` | provisioning | un utente remoto può spegnere la macchina e portarla via a tutti (`DECISIONI.md` §4.7) |
| A5 | la regola **udev** della scheda | provisioning | il compositore sceglie la GPU **a caso**; le misure valgono per quel ferro e non per il prodotto (§4.6-quinquies) |
| A6 | ⛔ **il server NON gira dentro una sessione utente** | chi avvia il servizio | `pam_systemd`, se chi chiama sta già in una sessione, **non ne crea una seconda e non lo dice**: i figli restano senza runtime, senza bus e senza desktop. ⚠ In produzione non capita (unità di sistema); **capita solo in prova**, cioè dove si studia |

> ### ⛔⛔ A6, la trappola dentro la trappola: `setsid` **non basta**
>
> `[M]` **16 agosto 2026.** Il server era stato riavviato via `ssh`, e
> `riavvia-7700.sh` lo lanciava con `setsid` — messo lì per un'altra ragione giusta (`sudo` con
> `use_pty` stronca quel che resta nel suo pseudo-terminale).
>
> ⇒ ⚠ **`setsid` stacca dal terminale, non dalla sessione di logind.** Il processo resta nel cgroup
> della sessione `ssh` di chi ha dato il comando, e da lì A6 scatta in pieno: `[M]` `loginctl` non
> mostrava **nessuna** sessione per `prova`, `/run/user/1001` non esisteva, e il registro ripeteva
> *«NON ho il bus di sessione: Could not connect: No such file or directory»*. **Otto giri di banco
> falliti su otto**, e la faccia del difetto era la solita: «il desktop non parte».
>
> ⭐ **La cura è farlo partire dove starebbe in produzione**: `systemd-run --unit=…`, cioè un'unità
> di sistema transitoria in `system.slice`. ⛔ E **si verifica**, perché A6 è silenzioso per
> costruzione: `riavvia-7700.sh` legge `/proc/PID/cgroup` del processo vivo e **rifiuta di dare
> l'OK** se ci trova `user@` o `session-`.
>
> ⚠ E c'era un secondo insegnamento nello stesso file: ⛔ **lo script che avvia il prodotto non era
> nel deposito** — viveva solo sulla macchina di prova. Le sue trappole erano scritte solo dentro se
> stesso, nessuna revisione le ha mai lette, e quella nuova è costata un'ora di diagnosi su un
> difetto che *questa tabella aveva già scritto*. ⇒ Adesso sta in `src/riavvia-7700.sh`.

---

## Parte B — quel che fa il prodotto, in quest'ordine

| # | che cosa | dove | se manca / se va storto |
|---|---|---|---|
| B1 | **PAM autentica** (asincrono, l'aiutante) | `aiutante.c` | il filo si ferma per secondi (§1.10) |
| B2 | nasce il **figlio**: gruppi → gid → uid, e si verifica col nucleo | `figlio.c` | un processo che gira come chi non deve |
| B3 | ⛔⭐ il figlio **apre la sessione PAM**: `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`, `PAM_RHOST`, **nessun `XDG_SEAT`** | `figlio.c`, passo 2-bis | ⛔ Mutter chiede `sd_pid_get_session()`, riceve **ENXIO** e muore con *«Failed to find any matching session»*. ⚠ Il **linger** non basta: dà runtime e bus, ma mette i processi in uno scope di classe `manager` |
| B4 | le variabili **`XDG_*`** si **leggono** da `pam_getenvlist`, non si inventano | `figlio.c` | un valore *dichiarato* al posto di uno *avuto*: regge finché regge |
| B5 | il client **ATTACCA dichiarando la tela = la finestra** | `pagina.html` | ⛔ la sessione nasce con la tela sbagliata e va **ridimensionata**, e il ridimensionamento è una gara: bande nere, desktop «rotto», input nel posto sbagliato |
| B6 | ⛔ il server **dice al palco la tela** nell'istante in cui la concede | `rcp.c`, dopo `SESSIONE` | il palco nasce a una misura che nessuno ha chiesto, e ogni fotogramma si butta |
| B7 | ⛔ **la sessione precedente dev'essere FINITA** — il gestore d'utente **e** `gnome-session-restart-dbus.service` | `sessione.c` | ⛔ la sessione nuova nasce dentro quella che muore e **muore con lei senza scrivere una riga**: `[M]` il suo registro resta a **zero byte** |
| B8 | si scrivono le **impostazioni**: `Ctrl+Alt+F*` svuotate, «Esci…» acceso, sospensione automatica spenta, blocca-schermo spento | `sessione.c` | il logout non ha una voce; la macchina si addormenta sotto una sessione viva |
| B9 | si scrive il **drop-in** della Shell (`--headless --no-x11`, ⛔ **senza `--virtual-monitor`**) | `sessione.c` | con un monitor suo la sessione è «sana» per v1 e **nera** per noi |
| B10 | si **avvia** `gnome-session`, e ⛔ **non si aspetta**: la risposta è il fotogramma | `sessione.c` + il ciclo di ri-tentativi | un figlio che aspetta 40 s è un figlio che non risponde al padre |
| B11 | il figlio **dice «ATTENDI»** finché il palco non c'è, e riprova subito | `figlio.c` | il padre **deduce** un fallimento dal silenzio e risponde `NON_ORA`: da lì i due lati non si rimettono più d'accordo |
| B12 | monta il **palco**: `RecordVirtual` → PipeWire → il monitor | `mutter.c`, `cattura.c` | nessun pixel |
| B13 | apre il **canale di input** (`libei`) sulla tela | `input.c` | il desktop si vede e non si comanda |
| B14 | **inibisce** sospensione e inattività (`SUSPEND\|IDLE`, ⛔ mai `LOGOUT`) | `sessione.c` | la notifica «Automatic Suspend», e la macchina che si addormenta |
| B15 | ⭐ **verifica**: la sessione non ha seat, e da qui non si spegne | `figlio.c` + `sentinella.c` | «scritto non è in vigore» (E1). ⛔ E la fa **il figlio**: root si sente rispondere «yes» perché logind guarda `CAP_SYS_BOOT` prima di polkit |

---

## Parte C — l'uscita, che è l'altra metà

| # | che cosa | se va storto |
|---|---|---|
| C1 | il **filo che cade** (scheda chiusa, PC spento, campo perso) ⇒ il posto si libera, **la sessione resta viva** (I4) | si perde il lavoro di chi voleva solo cambiare stanza |
| C2 | **«Esci»** — dal menu o con `Ctrl+Alt+Fine` ⇒ la sessione finisce e i programmi si chiudono | — |
| C3 | ⛔ il congedo **`0x10`** parte **PRIMA** che la sessione muoia, e va a **tutti** i client di quell'utente | chi guarda resta su uno schermo fermo per trenta secondi e legge «errore di rete» (rilievo B-7) |
| C4 | ⛔ il figlio **non** rifà la sessione dopo un'uscita: aspetta un attacco nuovo | il desktop che l'utente ha appena chiuso **ricompare da solo** |
| C5 | la pagina torna al **modulo di accesso**, e si rispoglia: via `data-schermo`, via la Pointer Lock, via lo schermo intero | un modulo di accesso dentro il vestito del desktop, col mouse ancora catturato |

---

## Parte D — dal sintomo al passo

⭐ **È la tabella da leggere per prima quando qualcosa non va.**

| il sintomo | il passo |
|---|---|
| «il desktop non compare» | B3 · B7 · A6 |
| «compare dopo molti secondi» | B7 (l'avvio fallito si recupera in ~13 s) · B10 |
| «bande nere ai lati» | B5 · B6 |
| «il desktop è rotto» | B5 · B6 (la tela e il palco non combaciano) |
| «nessun input» | B13 · **B6** (la regione del puntatore segue la tela: se la tela balla, i clic finiscono altrove) |
| «va lento» | **A2** (llvmpipe) · A5 (scheda sbagliata) |
| «il terminale resta congelato finché non muovo il mouse» | la coda della raffica in `cattura.c` (`LEZIONI.md` §6.5) |
| «si può spegnere la macchina» | A4 · B15 |

---

## ⏱ I tempi, misurati (16 agosto 2026, 20 giri, GPU integrata)

| fase | mediana | p90 | max |
|---|---|---|---|
| login → richiesta della sessione | 244 ms | 300 ms | 301 ms |
| ⛔ richiesta → palco montato | **2907 ms** | 16969 ms | 17885 ms |
| palco → primo fotogramma | 84 ms | 89 ms | 91 ms |
| ⭐ **TOTALE login → desktop** | **3211 ms** | 17255 ms | 18158 ms |

⭐ **Il giro tipico è 3,2 s**, e di questi ~2,9 sono `gnome-session` che si alza: quel che facciamo noi
sta in ~330 ms. ⛔ **La coda no**: circa un giro su sette costa 13-18 secondi, e sotto c'è il
**punto aperto** qui sotto.

## ⚠ Quel che ancora NON è a posto, dichiarato

- ⛔ **La voce «Power Off» resta nel menu** anche con tutte e quattro le `Can*` a «no» e
  `gnome-session.CanShutdown` a **false** `[M]`. ⭐ La causa è di gnome-shell, e la dichiara il suo
  sorgente: *«we don't get change notifications for [Polkit policy], so their value may be
  outdated»* — la legge all'avvio e la tiene in cache. ⚠ **L'azione fallisce comunque** (logind
  nega), ⛔ ma una voce che promette e non mantiene è quel che `DECISIONI.md` §4.7 voleva togliere.
> ### ⭐⭐⭐ LA CODA: TROVATA, ed è il ridimensionamento contro una scena ferma
>
> `[M]` 16 agosto 2026, registro pulito e figlio finalmente **parlante** (vedi sotto). In un giro
> lento:
>
> - fotogrammi spediti: **uno solo, e a `1920x1080`** — cioè alla tela di **riserva**, non a quella
>   chiesta dal cliente (`2544x926`);
> - righe «TELA NUOVA DAL PALCO»: **zero** — il ridimensionamento **non è mai avvenuto**;
> - e il ciclo lo diceva: *«1 fotogrammi consegnati, **3538 attese a vuoto** (scena ferma: Mutter
>   consegna solo quando qualcosa cambia)»*.
>
> ⇒ ⛔ **Il palco nasce alla tela sbagliata.** Il figlio viene generato con `1920x1080` (il valore
> della tabella dei figli) **prima** che il cliente dichiari la sua finestra, monta il palco a quella
> misura, e spedisce una chiave sbagliata. Poi arriva `2544x926` e serve un ridimensionamento —
> ⛔ **ma su Wayland il ridimensionamento si compie solo quando il compositore consegna un
> fotogramma nuovo, e su un desktop appena nato non cambia niente.** ⇒ Si aspetta che qualcosa si
> muova da sé.
>
> ⭐ **E questa è la causa comune di tutti i sintomi che l'utente ha elencato il 16 agosto**: bande
> nere (fotogramma alla misura sbagliata), «desktop rotto», «nessun input» (la regione del puntatore
> segue la tela), «ci mette molti secondi». ⚠ B5 e B6 di questa tabella lo dicevano già a parole; la
> cura scritta (`rcp.c` §4.5, dire al palco la tela) **arriva troppo tardi**, perché il figlio ha
> già montato.
>
> ⇒ ⭐ **La cura**: il figlio non fa nascere la sessione né monta il palco **finché non sa la tela del
> cliente**. ⚠ Con un tetto (`TELA_ATTESA_MS`), perché I1 vieta di stare fermi per prudenza: se il
> cliente non la dichiara, si parte col ripiego e lo si **dichiara**.
>
> ### ⭐⭐ E la misura, 20 giri, prima e dopo
>
> | | prima | dopo |
> |---|---|---|
> | ⛔ **richiesta → palco** | 2907 ms · p90 **16969** | **~900 ms**, costante (839-980) |
> | ⭐ **totale al desktop** | 3211 ms · p90 **17255** · max **18158** | ~4200 ms · **max 5146** |
> | fotogrammi alla misura sbagliata | 1 su 1 a `1920x1080` | ⭐ **nessuno**: tutti a `2544x926` |
>
> ⇒ ⭐ **La coda è sparita**: da diciassette secondi a cinque. ⚠ E la mediana cresce di un secondo,
> perché adesso il secondo fisso dell'ammissione sta sul percorso critico — la sessione non può
> nascere prima che il cliente sia ammesso. ⭐ È uno scambio che conviene: **un secondo sempre**
> contro **diciassette un giro su sette**.
>
> ⏳ **Quel che resta da guadagnare**: il padre conosce la finestra chiesta già dall'`ATTACCA`, cioè
> **prima** che scada il secondo fisso. Mandandola al figlio subito si recupererebbero ~950 ms.

- ⛔⛔ **LA CODA: un giro su sette costa 13-18 secondi** — ⭐ **causa trovata**, vedi il riquadro qui
  sopra. Qui resta il diario di come ci si è arrivati, che vale più della causa. `[M]`
  Quel che si è ESCLUSO con la misura, e ognuno era una diagnosi che sembrava giusta:

  | ipotesi | come è stata esclusa |
  |---|---|
  | l'attesa che raddoppia (1→2→4→…→30 s) | ⭐ era **vera** e curata (vedi sotto), ma la coda resta |
  | il gestore d'utente che rinasce | curato col **linger**: bus 2,6 s → **18 ms** `[M]`, coda invariata |
  | il sondaggio a Mutter da 5 s | tetto sceso a 400 ms, coda invariata; e `[M]` quel tetto non scatta mai |
  | un passo lento dentro `prendi_il_palco` | ⏱ i tre cronometri **tacciono**: nessun passo sopra 250 ms |
  | il figlio che aspetta invece di provare | ⏳ **nessuna riga**: non sta aspettando |

  ⇒ ⚠ Nei 17 secondi il figlio **non scrive niente, non aspetta e non ha passi lenti**: le tre cose
  insieme non tornano, quindi manca ancora un pezzo di strumentazione. ⭐ **Il sospettato che
  resta**, ed è l'unica regione non ancora cronometrata: il **montaggio della cattura dopo
  `mutter_apri`** — `ATTESA_AVVIO_S 10` in `cattura.c` e `ATTESA_NODO_MS 10000` in `mutter.c`.
  Dieci secondi più l'avvio del compositore fanno proprio i diciassette.

  ⛔⛔ **E LA RAGIONE PER CUI CI SONO VOLUTE SEI DIAGNOSI È UNA SOLA, ed è la peggiore possibile:
  il figlio non aveva la parlantina.**

  `[M]` Il figlio **non è un `fork`**: è un `execve` di `remotix-figlio`. ⇒ Non ereditava il
  flag `--parlantina`, e **ogni `registro_dettaglio()` di `figlio.c` finiva nel nulla, in silenzio,
  senza un errore.** ⚠ Metà della strumentazione di quel file non è mai arrivata al registro.

  ⭐ E ha mentito nella direzione peggiore: cercando la coda, ho concluso per ore che certi rami
  «non scattavano mai» *perché la loro riga non compariva* — mentre scattavano eccome. ⇒ È la forma
  **E8** (`LEZIONI.md` §1.9) dentro lo strumento che serve a smascherarla: «non l'ha fatto» e «non
  me l'ha detto» con la stessa faccia.

  ⇒ *Una diagnostica che tace non è neutra: **mente**.* E la prima cosa da verificare su uno
  strumento non è che dica il vero, è che **dica**.

- ⭐ **Curato**: l'attesa fra un tentativo e l'altro raddoppiava fino a 30 s **anche mentre un
  cliente stava a guardare uno schermo fermo**. `[M]` Il registro: *«attesa in corso 30000 ms,
  nascita chiesta 0 ms fa»* — e i due numeri insieme dicono tutto: raddoppiava, e la guardia non
  poteva scattare perché si arma solo quando la sessione risulta **morta**, mentre i giri lenti sono
  proprio quelli in cui la precedente **sta ancora chiudendo** (`State=closing`). ⇒ Adesso: se
  qualcuno guarda, si riprova ogni **200 ms**. p90 da 21,2 s a 17,3 s, e le punte a 30 s sparite.
