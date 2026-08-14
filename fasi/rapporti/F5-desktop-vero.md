# Il desktop vero — perché non si vedeva, e la prova che adesso si vede

*14 agosto 2026, mattina. ⭐ Nato da una domanda dell'utente: **«se il server non mostra il desktop,
a che serve REMOTIX?»** — fatta guardando la cosa vera, trenta secondi dopo il giudizio della
fase 3.*

---

## ⭐⭐⭐ In una riga

**Le due metà del prodotto si contraddicevano**: una **crea** la sessione con un monitor suo,
l'altra **ne crea un secondo** e cattura quello. La shell resta sul primo, e l'utente guarda il
secondo — **vuoto**.

---

## Il difetto, letto nel codice e poi provato

| dove | che cosa fa | |
|---|---|---|
| `src/sessione.c:650` | scrive l'unità con `ExecStart=… --headless --no-x11 **--virtual-monitor %ux%u**` | ⇒ la sessione nasce **con un monitor suo**, e GNOME ci mette la shell |
| `src/mutter.c:450` | cattura con **`RecordVirtual`**, che **monta un monitor nuovo** e registra quello | ⇒ si guarda **il secondo**, dove non c'è niente |

⛔ **E il commento di `mutter.c:376` dichiara l'intenzione giusta**, che l'altra metà tradisce:

> *«ZERO monitor è la sessione nera… Non si fallisce (il nostro `RecordVirtual` ne monta uno suo),
> ma si DICHIARA: chi legge zero fotogrammi più tardi deve avere questa riga sotto gli occhi.»*

⇒ ⭐ **Il disegno era: la sessione NON ha monitor propri, e l'unico è il nostro.** `sessione.c`
gliene dà uno lo stesso.

⚠ **E il sintomo era stato visto e accettato due volte**: il giudizio della fase 2 si chiuse su
*«è lo sfondo GNOME, è OK»* — **uno sfondo vuoto preso per un successo** — e quello ha nascosto la
domanda per due fasi intere.

---

## L'esperimento — ⛔ fatto SENZA toccare il prodotto

*La regola: si prova la tesi prima di curare il codice, o si cura il posto sbagliato.*

⭐ **E si prova su un utente NUOVO**, perché `SPECIFICHE.md` §5.1 dà **una sola sessione grafica per
utente**: quella di `nicfio` esisteva già, con un monitor suo, dal 12 agosto.
⇒ *L'intuizione è dell'utente: «un utente non può avere due desktop, allora crea un utente di prova».*

| passo | |
|---|---|
| **1** | utente `prova` (uid 1001), parola d'ordine, `enable-linger` |
| **2** | ⭐ drop-in `zz-senza-monitor.conf`: `ExecStart=/usr/bin/gnome-shell --headless --no-x11` — ⛔ **senza `--virtual-monitor`** |
| **3** | sessione avviata con la ricetta di `banchi/00-sessione-gnome.sh` (`gnome-session --session=gnome`, ambiente composto da zero) |
| **4** | `[M]` **`GetCurrentState` → 0 monitor**: è la sessione *«viva, completa e nera»* di `gnome.md` §3.1 |
| **5** | l'utente si collega a `https://192.168.0.2:7571/` come `prova` |

### ⭐⭐⭐ L'esito

**Il desktop c'è**: barra in alto con l'orologio, indicatori a destra, sfondo Debian, **la dock in
basso con Firefox e i File**, e la notifica *«Screen Lock disabled»*.
*(La prova sta in `F3-verbali/desktop-vero-14ago.png`.)*

⇒ ⭐ **La tesi regge**: senza monitor propri, quello di `RecordVirtual` è **l'unico**, e GNOME ci
mette la shell.

---

## La cura nel prodotto — ⏳ da fare, e sono due posti non uno

| | |
|---|---|
| **1** | `src/sessione.c:650` — **non passare `--virtual-monitor`** quando la sessione è creata per un client remoto |
| **2** | `src/sessione.c:668` — ⛔ **e il controllo che rilegge l'`ExecStart` in vigore va cambiato con lui**: oggi pretende `--virtual-monitor %ux%u` e **fallirebbe** sulla sessione curata. *Scritto non è in vigore, forma E1: il controllo è giusto, l'atteso no* |

⚠ **E due cose che questa prova NON dice, e vanno misurate prima di crederle:**

1. ⛔ **la misura del monitor**: con `--virtual-monitor` la dava la sessione; ora la dà
   `RecordVirtual`. **Chi decide 1920×1080, e che cosa succede se il client ne chiede un'altra?**
   È la domanda di `RCP.md` §4.5 (la tela concessa), e adesso tocca questo pezzo.
2. ⚠ **la sessione prima del primo client è NERA** (0 monitor). Per una sessione **solo remota** va
   bene; ⛔ ma `PIANO.md:399` dice *«`--virtual-monitor` non è opzionale»* e `gnome.md` §108 lo
   ripete: **quelle due righe adesso sono da riscrivere**, perché sono vere solo per una sessione
   che deve vivere **senza** nessuno che la catturi.

---

## ⭐ E la riga da portarsi via

*Il difetto non era in un pezzo: era **fra due pezzi**, ciascuno corretto per conto suo.*
`sessione.c` fa bene a dare un monitor a una sessione che deve poter vivere da sola; `mutter.c` fa
bene a montarne uno per catturarlo. ⛔ **Nessuno dei due sbagliava, e il risultato era uno schermo
vuoto** — la stessa forma della notte prima, quando la stringa del codec e i suoi byte dicevano due
cose diverse e ogni pezzo rispondeva bene alla propria domanda.

⇒ **Le cuciture non hanno un proprietario, e per questo nessun banco le guardava.**
