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

## ⚠ Quel che ancora NON è a posto, dichiarato

- ⛔ **La voce «Power Off» resta nel menu** anche con tutte e quattro le `Can*` a «no» e
  `gnome-session.CanShutdown` a **false** `[M]`. ⭐ La causa è di gnome-shell, e la dichiara il suo
  sorgente: *«we don't get change notifications for [Polkit policy], so their value may be
  outdated»* — la legge all'avvio e la tiene in cache. ⚠ **L'azione fallisce comunque** (logind
  nega), ⛔ ma una voce che promette e non mantiene è quel che `DECISIONI.md` §4.7 voleva togliere.
- ⏳ Il **primo avvio dopo un logout** a volte fallisce e si recupera in ~13 s: `[M]` col banco
  automatico, 3 giri su 5 puliti al primo colpo, gli altri dopo un ri-tentativo.
