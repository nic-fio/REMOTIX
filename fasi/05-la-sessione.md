# Fase 5 — La sessione

⭐ **Aperta il 15 agosto 2026**, col suo documento e prima di una riga di codice (`fasi/README.md`).
Il mandato di partenza è [`rapporti/F5-IN-0-mandato.md`](rapporti/F5-IN-0-mandato.md); il piano è
`PIANO.md` §«Fase 5 — La sessione».

> **La scena che l'utente giudicherà**: *«chiude il client, va a pranzo, riapre — e ritrova tutto
> com'era»*.

⛔ **E il 15 agosto l'utente ha aggiunto quattro punti** che il piano non conteneva, o conteneva
sparsi. Sono il §1 di questo documento, prima del resto, perché due di essi **cambiano l'ordine del
lavoro**: il primo tocca la configurazione del desktop, il secondo apre una decisione di protocollo.

---

## 1 · ⭐ I QUATTRO PUNTI AGGIUNTI DALL'UTENTE

### 1.1 ⛔ Togliere «Spegni, Riavvia, Sospendi, Iberna» dal menu di sistema del desktop

*Motivo dichiarato dall'utente: un utente collegato da remoto non deve poter «sfilare da sotto il
naso» la macchina agli altri, in remoto o in locale.*

`SPECIFICHE.md` §11.3 lo prometteva già in una riga — *«spegnimento, riavvio, sospensione: **tolti**
alla sessione remota»* — e **nessuna riga di codice la mantiene**.

⭐ **La leva ovvia è quella sbagliata, ed è misurabile nelle fonti che abbiamo in casa:**

| strada | che cosa fa davvero |
|---|---|
| ❌ `org.gnome.desktop.lockdown disable-log-out` | fa sparire Spegni **e** Riavvia — ⛔ **ma fa sparire anche «Esci…»**, e fa rifiutare `org.gnome.SessionManager.Logout` con `GSM_MANAGER_ERROR_LOCKED_DOWN`. Cioè ci porta via **il punto 1.2 dell'utente** *e* il congedo che `sessione.c:789` usa oggi per fermare la sessione |
| ✅ **regola polkit `no`** su `org.freedesktop.login1.power-off`, `reboot`, `suspend`, `hibernate` (e le varianti `*-multiple-sessions`, `*-ignore-inhibit`) | `[R]` `gsm-manager.c`: `CanShutdown = !lockdown && (can_stop ‖ can_restart ‖ can_suspend ‖ can_hibernate)`, e ciascuno dei quattro è vero solo se logind risponde `yes` o `challenge` (`gsm-systemd.c:698-803`). Con tutt'e quattro a `no` ⇒ `CanShutdown` falso ⇒ gnome-shell nasconde **Spegni** e **Riavvia** (`systemActions.js:340-359`), e **Sospendi** cade per conto suo (`loginManager` `CanSuspend`). ⭐ **«Esci…» resta**, perché dipende solo da `disable-log-out` |

⛔ **`no`, mai `auth_admin`**: `"challenge"` **mostra** la voce — vale su GNOME e su KDE
(`gnome.md` §5.1, `kde.md` §1579). ⚠ E la voce **sparisce**, non si ingrigisce: `system.js:218-226`
lega `can-*` a `visible`.

> ### ✅ E LA PORTATA È DECISA — dall'utente, il 15 agosto 2026
>
> > *«No, nessuno può spegnere, riavviare, mettere in standby o sospensione il server, altrimenti si
> > rischia di "buttare fuori" anche altri eventuali utenti collegati alla macchina.»*
> > *«L'utente collegato a REMOTIX può solo fare espressamente il logout o, ovviamente, operare sul
> > PC che sta utilizzando.»*
>
> ⇒ `DECISIONI.md` §4.7, e `SPECIFICHE.md` §11.3 è stata allargata: **non «alla sessione remota»,
> a tutti**. ⛔ La regola polkit si scrive **piatta**, senza `subject.local`: la discriminante che
> avevo proposto non serve più, e con lei sparisce la misura che sarebbe costata.
>
> ⭐ **Il metro del banco, ed è più forte di «le voci sono sparite»:** *nel menu di sistema del
> desktop remoto resta «Esci…» **e nient'altro** di quella famiglia.*

**Il lavoro, allora — tre cinture, perché le strade sono tre** (`DECISIONI.md` §4.7):

1. **la regola polkit**, piatta, sulle quattro azioni e le loro varianti `*-multiple-sessions` /
   `*-ignore-inhibit`. ⭐ Copre **due strade con una riga sola**, perché guarda l'azione e non
   l'interfaccia: il menu **e** `systemctl poweroff` da un terminale dentro la sessione;
2. **`logind.conf`**: `HandlePowerKey`, `HandleSuspendKey`, `HandleHibernateKey`, `HandleLidSwitch`
   = `ignore` — ⛔ il tasto fisico **non passa da polkit**, e la prima cintura non lo vede;
3. **la sospensione automatica**, che è §2.2 di questo documento: l'`Inhibit` **e**
   `sleep-inactive-ac-type=nothing`. ⚠ Due cinture per **due sintomi**: polkit impedisce il fatto,
   dconf toglie dallo schermo la notifica *«Automatic Suspend»* che l'utente vedrebbe lo stesso.

**E quel che resta da fare bene:**

- ⚠ **sono tutte righe di configurazione, cioè quel che I7 vieta**: vanno **installate da noi** e
  **verificate dopo l'avvio**, come l'headless di `DECISIONI.md` §4.3-bis. ⭐ Qui la verifica non ha
  incognite: si chiede a logind `CanPowerOff` / `CanReboot` / `CanSuspend` / `CanHibernate`
  **dalla sessione dell'utente** e si pretende **`no`**; se risponde `yes` o `challenge`, si dichiara
  il fallimento;
- ⚠ **root resta, e deve restare**: `systemctl --force poweroff` parla con PID 1 e salta logind.
  ⭐ È la strada dell'amministratore, e i client attaccati lo vengono a sapere con
  `SERVER_IN_CHIUSURA 0x0C` — ⭐ già emesso da `main.c:850`, cura del rilievo B-7. ⇒ **questo
  percorso va provato in questa fase**: adesso è l'unico spegnimento legittimo che esista;
- gli altri desktop arrivano con le loro fasi (KDE è la 10): la regola polkit è **la stessa per
  tutti e quattro** — `xfce.md` §618 dice che su XFCE non esiste nessuna chiave e restano solo
  polkit e logind — ⛔ ma **si verifica desktop per desktop**, quando la fase arriva.

### 1.2 ⛔⛔ Chiusura della scheda **contro** «Esci» dal menu: due esiti, e oggi uno solo esiste

> ## ⭐⭐ LA DISTINZIONE, DETTATA DALL'UTENTE IL 15 AGOSTO 2026
>
> > *«Distinguiamo il comportamento del PC usato dall'utente rispetto a quello che fa REMOTIX. Se
> > l'utente chiude, spegne o riavvia il **proprio** PC, questo lo trattiamo come browser chiuso /
> > connessione caduta. Se invece sceglie la voce «Esci/logout», allora significa che l'utente vuole
> > **terminare la sessione**, il che comporta la chiusura di tutti i programmi che aveva in
> > esecuzione.»*
>
> ⭐ **Il PC dell'utente non è mai un caso speciale**, e questo toglie lavoro invece di aggiungerne:
> scheda chiusa, browser chiuso, PC spento, PC riavviato, campo perso in galleria — **un caso solo**,
> quello già misurato. Non c'è niente da rilevare dal lato client e niente da distinguere sul filo.
>
> ⭐ **«Esci/logout» è l'unico gesto che significa «ho finito»**, e la sua conseguenza è dichiarata:
> **i programmi dell'utente si chiudono**. Non è un distacco più forte: è l'altro verso.
>
> ⛔ **E tre cose smettono di essere domande:**
>
> 1. ⛔ **`disable-log-out` è VIETATA.** Toglieva la voce «Esci…» e faceva rifiutare
>    `SessionManager.Logout`: adesso che il logout è una funzione **promessa**, quella chiave
>    toglierebbe la funzione. ⇒ per §1.1 resta **solo** la regola polkit — la strada si è chiusa da
>    sé, senza doverla scegliere. *(Era la domanda 2 di §4, e decade.)*
> 2. **`org.gnome.shell always-show-log-out` va acceso.** `[R]` Senza, su una macchina con un utente
>    e una sessione sola gnome-shell **non mostra** la voce. ⚠ E rovescia
>    `reference-gnome/rapporti/02-shell-blocco-voci.md:214` — *«va lasciata `false`»* — che era
>    scritto quando l'obiettivo era togliere voci, non darne una. *(Era la domanda 3 di §4, e
>    decade.)*
> 3. **Fra il clic e la fine non tocchiamo niente**: se un programma ha lavoro non salvato, GNOME
>    mostra il **suo** dialogo dentro il desktop remoto, come se l'utente fosse al monitor. È I8, e
>    vale anche qui.

| caso | oggi | che cosa manca |
|---|---|---|
| **1 · il filo cade** — scheda chiusa, browser chiuso, ⭐ **il PC dell'utente spento o riavviato** | ⭐ **vivo e misurato**: `pagina.html:2504` aggancia `pagehide` (⛔ non `beforeunload`) e spedisce `CONGEDO 0x01` prima di morire — `[M]` il server l'ha visto arrivare. Il posto si libera, **la sessione sopravvive** (I4, `SPECIFICHE.md` §5.2). ⚠ E quando il PC muore di colpo il `CONGEDO` non parte affatto: allora è l'orologio del **silenzio** a liberare il posto, 30 s (§5.3) — ⭐ **stesso esito, altra strada** | il **banco** che lo provi, e lo provi **due volte di fila** (`LEZIONI.md` §2.3-ter) |
| **2 · l'utente sceglie «Esci…» nel menu del desktop** | ⛔ **non è definito da nessuna parte e non è gestito**: `gnome-session` esce, Mutter muore, il palco cade — e sul filo **non parte nessun motivo**. Il client vede una connessione che si spegne, cioè esattamente la forma di guasto del rilievo **B-7** | tutto quel che segue |

**Quel che il caso 2 richiede, in ordine:**

- **chi se ne accorge**: il figlio sorveglia già l'unità `gnome-session-manager@gnome.service`
  (`sessione.c`, `unita_inattiva()`); qui serve accorgersene **mentre accade**, non chiederlo;
- ⛔ **il motivo deve partire PRIMA che il filo muoia**, ed è la parte che oggi non esiste: quando
  Mutter cade, il palco cade con lui e il canale non serve più a niente. ⚠ È l'ordine, non il
  contenuto, a essere il difetto — la stessa forma del rilievo **B-7**;
- ✅ **il motivo sul filo è `0x10 SESSIONE_TERMINATA`**, aggiunto a `RCP.md` §8.2 il 15 agosto: non
  il riuso di `0x01`, che porta la promessa opposta *«riattacca e ritrovi tutto»*. ⇒ da definire in
  `rcp.h`, da **emettere** in `rcp.c`, e da leggere in `pagina.html` — ⛔ e i tre pezzi vanno insieme,
  o è il rilievo B-7 daccapo;
- ✅ **che cosa legge l'utente**: *«la sessione è terminata»* sopra il **modulo di accesso**
  (deciso dall'utente il 15 agosto, `DECISIONI.md` §4.1-quater). ⛔ Non una schermata di chiusura;
- **la pulizia**: posto liberato, palco smontato, e il prossimo attacco è una **sessione nuova** —
  non un riattacco a un palco morto;
- ⭐ **la seconda strada per lo stesso logout** (`DECISIONI.md` §4.1-quinquies, 15 agosto): la
  scorciatoia **`Ctrl+Alt+Fine`** gestita **dalla pagina** — con `preventDefault()`, la conferma
  *«terminare la sessione?»*, e ⛔ da **aggiungere alla sonda S3** (`banchi/04-b29-scorciatoie.py`,
  42 combinazioni: questa non c'è) e misurare su due motori prima di prometterla. ⛔ **Nessun
  bottone a schermo**: la voce del menu si raggiunge col dito e basta a sé stessa. ⚠ E le due strade
  finiscono **nella stessa** `sessione_termina()`: un solo percorso di uscita, o due che divergono;
- ⚠ **e la nostra `sessione_termina()` resta valida**: chiude con `SessionManager.Logout`, che
  `disable-log-out` avrebbe ucciso (`gnome.md` §5.1). ⭐ Vietando quella chiave, il congedo del
  server e il logout dell'utente **passano dalla stessa porta**, e la porta resta aperta.

### 1.3 Il riattacco da uno schermo di misura diversa — e i compositori

⭐ **Tre quarti sono già fatti e misurati**, ma nella **coda della fase 4** (`04-si-comanda.md`,
`rapporti/F4-IN-13-la-tela-che-cambia.md`): la tela è la finestra, `SESSIONE` concede la tela che il
palco ha già con **zero fotogrammi scartati** `[M]`, e il ridimensionamento a caldo costa **6 ms**.

**Quel che resta a questa fase:**

- ⛔ **il banco che, DOPO il riattacco a misura diversa, batte un tasto e muove il puntatore.** La
  ragione è misurata: al cambio di geometria **`libei` distrugge e ricrea i dispositivi assoluti**
  (`[M]` 15 ago, *«il puntatore è stato TOLTO dal compositore, ricambio n. 640»*), e un cambio di
  **keymap** ricrea la tastiera; il puntatore al dispositivo vecchio smette di funzionare **senza
  errore** (`gnome.md` §9). Senza quel banco la prova è **verde per costruzione**;
- ⚠ **che fine fanno le finestre aperte** quando la tela rimpicciolisce e poi torna grande. È un
  comportamento del compositore, non nostro: va **dichiarato** dopo averlo guardato, non sperato;
- **la tabella dei compositori**, che è la parte «studia bene i compositori» del punto:

| | ridimensiona a caldo? |
|---|---|
| **Mutter** (GNOME) | ✅ `[M]` — è la strada su cui la coda della fase 4 è stata misurata |
| ⛔ **KWin** | **no fino a `v6.7.4` compreso** — `[R]` verificato su invent.kde.org il 14 ago: il ridimensionamento c'è **solo su `master`**, `Plasma/6.8` **non esiste** e non ha data. Riavviare KWin ucciderebbe la sessione, cioè proprio il distacco che il modello offre ⇒ **ripiego dichiarato** (`DECISIONI.md` §5.0-bis): si tiene la tela vecchia e riscala il client. ⛔ La riga nel registro (`COMPOSITORE_INCAPACE`) esiste nel codice ed è provata **su un ospite finto** — verificabile davvero solo alla **fase 10** |
| **labwc** (XFCE, LXQt) | ⚠ e il rischio non è la misura: su **XFCE** `xfsettingsd` è il primo client della sessione e **spegne ogni output nuovo** (`enabled = FALSE`); su **LXQt** non c'è niente di simile (`SPECIFICHE.md` §11.2) |
| **muffin** (Cinnamon) | la riga peggiore, e prima del ridimensionamento mancano `RecordVirtual`, libei e gli appunti |

⭐ **La memoria dell'utente era giusta**: KWin è il caso problematico, e la sua degradazione è
**l'unico punto del modello che non può essere servito**.

### 1.4 L'utente che ha **già** una sessione grafica attiva

`SPECIFICHE.md` §5.1 li elenca tutti e quattro. Lo stato, oggi:

| situazione | motivo | stato |
|---|---|---|
| remota viva + un **secondo dispositivo** | `0x0F GIA_ATTIVA_REMOTA` | ⭐ **vivo e provato** `[M]`: il registro dei posti in `rcp.c`, e il caso 18 del banco `04-b31` |
| remota **muta da 30 s** + un altro dispositivo | *(entra)* | vivo: `torna_a_parlare()` |
| ⛔ **locale già attiva**, arriva la remota | `0x05 GIA_ATTIVA_LOCALE` | **definito in `rcp.h:45` e MAI EMESSO da nessun `.c`** |
| ⛔ remota viva, **si apre la locale** | `0x04 SESSIONE_LOCALE_PREVALSA` | **definito in `rcp.h:44` e MAI EMESSO** |

⛔ È la stessa forma di guasto di `RCP_SERVER_IN_CHIUSURA` (rilievo **B-7**): un motivo che esiste
nell'intestazione e che nessuno spedisce. ⭐ E la pagina **è già pronta a leggerli**
(`pagina.html:440-441`): manca solo chi li manda.

**Quel che serve:**

- **chi guarda le sessioni locali — logind.** Oggi l'unico file che lo nomina è `sessione.c`, di
  sfuggita. Il pezzo da riportare è `v1/remotix-c/src/sentinella.c` (307 righe): `ListSessions` +
  i segnali `SessionNew` / `SessionRemoved`, e le proprietà `Type`, `Remote`, `Active`;
- ⛔⛔ **la definizione di «sessione grafica locale», scritta prima del codice — e la prima stesura
  ovvia è SBAGLIATA.** Il criterio che viene in mente è `Type ∈ {wayland, x11}` **e**
  `Remote = false`; ⛔ ma `[R]` **noi non chiamiamo `pam_set_item(PAM_RHOST, …)` da nessuna parte**
  — `autenticazione.c:176` fa `pam_start` e basta — quindi `pam_systemd` crea le **nostre** sessioni
  senza host remoto e logind le segna con ogni probabilità `Remote=no`. ⇒ ⭐ **con quel criterio la
  nostra sessione remota conterebbe come locale, e ci rifiuteremmo da soli con `0x05`.**

  **Due cure, e conviene farle tutt'e due:**
  1. **il discrimine è il SEAT, non `Remote`**: locale = **ha un seat** (`seat0`); la nostra
     headless non ne ha (è la stessa proprietà su cui Mutter decide `is_headless()`, §2.3);
  2. ⭐ **e `PAM_RHOST` va impostato lo stesso**, con l'indirizzo del client: costa una riga e
     ripaga due volte — logind segna la sessione `Remote=yes`, **e** l'accesso finisce nei registri
     di sistema (`last`, audit) con la provenienza, che oggi non c'è.

  ⏳ `[?]` **Da misurare sulla macchina**, e non è dedotto: `loginctl show-session` sulla sessione
  di `prova` e su quella locale di `nicfio`, guardando `Type`, `Class`, `Remote`, `Seat`, `Active`.
  ⚠ Tentato il 15 agosto sera: la macchina non rispondeva a ssh;
- le sessioni **testuali** (ssh, tty) devono continuare a convivere: sono innumerevoli, §5.1;
- ⚠ il caso `0x04` è l'unico in cui **il server butta fuori un client sano**: `DECISIONI.md` §4.1-bis
  lo ammette solo con un motivo dicibile, ed è per questo che il motivo esiste. Il banco lo verifica
  **dal lato che lo riceve**.

### 1.5 ⭐ Il multi-tenant: la domanda dell'utente, e la riga dove passa il confine

*Chiesto dall'utente il 15 agosto: «poiché qui trattiamo le sessioni, mi chiedo se il multi-tenant
non ricada in questa fase».*

✅ **Deciso dall'utente lo stesso giorno: «potremmo anche lasciare in questa fase 1 solo utente, e
nella fase 12 il multi-tenant».** ⇒ `DECISIONI.md` §4.6-quater, dove il confine vive per intero.
⚠ La domanda era buona perché i documenti dicevano cose diverse: `SPECIFICHE.md` §5.5 dice *«il
multi-tenant è delle fasi da 5 in poi»*, `PIANO.md` intitola la fase 12 «Multi-tenant e il budget».

| | dove | in breve |
|---|---|---|
| **un utente remoto per volta** | ⭐ **questa fase** | nessuna prova di due sessioni remote insieme, nessun budget, nessun conteggio |
| **più sessioni insieme, il budget, `BUDGET_PIENO`, `MAX_ATTACCATE` configurabile** | **fase 12** | hanno bisogno di un numero vero, e lo dà il codificatore hardware della **fase 8** |
| ⛔ **il codice chiavato sull'utente**, e il guardiano di logind che **discrimina per utente** | ⭐ **questa fase, e non è rinviabile** | ⛔ non perché sia importante: perché **non si può scrivere «per un utente solo»** |

⛔ **E la ragione per cui l'ultima riga non si rinvia è che la macchina la smaschera da sola.** Il
guardiano di §1.4 risponde a una domanda che suona in due modi diversissimi — *«c'è una sessione
grafica locale?»* contro *«c'è una sessione grafica locale **di questo utente**?»* — che sono una
riga di differenza e due prodotti diversi. ⭐ E la macchina di prova è **già** nella configurazione
che smaschera l'errore: `nicfio` ha la sua sessione grafica **locale**, `prova` si collega da
**remoto**. Scritto male, `prova` viene rifiutato con `0x05` **il primo giorno**.

⇒ ⭐ **Il banco di `0x04`/`0x05` si scrive su quella coppia** — locale `nicfio` e remota `prova`, che
**devono convivere senza toccarsi** — e costa quanto costerebbe comunque.

⚠ **E il ripiego resta dichiarato**: `MAX_ATTACCATE` è un `#define` a **16** (`rcp.c:490`) dove
§5.5 promette **dieci configurabile**. Oggi non morde, e la sua scadenza è la fase 12.

---

## 2 · Quel che il piano chiedeva già, e resta

*Dal mandato §3 e §4 — nessuno di questi ha un banco, ed è esattamente il lavoro della fase.*

1. ⛔ **Il rilascio dei tasti al distacco, CON UN TASTO PREMUTO DAVVERO.** `RCP.md` §11 la chiama
   *«la regola col rapporto danno/costo più alto del documento»*. `[M]` **16 agosto, venti giri col
   browser**: si legge *«RILASCIO AL DISTACCO: **0** fra tasti e pulsanti»* in tutti e venti — ⛔ cioè
   la riga si scrive, e non ha mai avuto niente da rilasciare. **La prova non è mai stata fatta.**
   ⇒ ⭐ **È il prossimo punto.**
2. ✅ **L'inibizione della sospensione** — `[M]` 16 agosto, **20 giri su 20**: *«sospensione e
   inattività INIBITE al gestore di sessione (flag 12 = SUSPEND\|IDLE — mai LOGOUT)»*. ~~Quel che
   segue resta come cronaca di com'era:~~ `[M]` 15 agosto: la notifica **«Automatic Suspend —
   Suspending soon because of inactivity»** compare in due schermate del desktop remoto.
   `sleep-inactive-ac-type` vale `suspend` a **900 s**. La cura è una chiamata:
   `SessionManager.Inhibit(…, 12)` = `SUSPEND|IDLE` **insieme**, ⛔ **mai** il bit `LOGOUT`.
   ⚠ `energia.c` **non esiste in `src/`**: va portato da `v1/remotix-c/src/energia.c`.
   ⚠ E senza questa, il banco delle **sei ore** non misura niente.
3. ✅ **L'headless si dichiara e si verifica dopo l'avvio** — `[M]` 16 agosto, **20 giri su 20**: il
   figlio scrive *«VERIFICATO: la mia sessione non ha seat ⇒ Mutter è headless»*. ⛔ Non è più «per
   accidente»: è un fatto letto dal nucleo a ogni sessione.
4. **I tre orologi, ciascuno col suo banco**: 30 s di silenzio, 30 min di inattività, 6 ore di
   abbandono. ⚠ Il terzo **incrocia** il punto 2.
5. **Distacco e riaggancio due volte di fila** — *«un banco che passa solo da macchina pulita non è
   un banco, è una dimostrazione»*.
6. ⛔ **La sessione senza nessuno che guarda**: in v1 il monitor virtuale spariva al distacco e
   `libmutter` andava in asserzione fallita.
7. ✅ **PAM per intero**: asincrono (`aiutante.c`) **e** la sessione PAM aperta dal figlio (passo
   2-bis). `[M]` provato venti volte col browser: *«PAM ha risposto: ammesso — e il filo non si è mai
   fermato»*.

⇒ ⭐ **Restano il 1, il 4, il 5 e il 6.**

---

## 3 · Quel che la coda della fase 4 lascia aperto e che passa di qui

| | |
|---|---|
| ⏳ la riga che manca a `RCP.md` §7.1 | che cosa fa il server quando il palco cambia misura **da sé** |
| ⚠ i 4 ms di ritardo medio aggiunto | `MOVIMENTO_ATTESA_S` a 8 ms è un ripiego dichiarato |
| ⚠ i banchi RCP/1 non esercitano `ADATTA_TELA` | `01-b3` e `01-b4` restano verdi perché il filo non è cambiato |

---

## 4 · ⛔ LE DECISIONI CHE ASPETTANO L'UTENTE

*⭐ Le domande si affrontano **una alla volta**, per volontà dell'utente.*

**Chiuse:**

| | |
|---|---|
| ✅ **le due uscite** — il filo che cade contro il logout | `DECISIONI.md` §4.1-ter, 15 agosto |
| ✅ **dopo il logout la pagina torna al modulo di accesso**, e il motivo è `0x10` | `DECISIONI.md` §4.1-quater, `RCP.md` §8.2, 15 agosto |
| ✅ ~~`disable-log-out`?~~ **vietata** · ✅ ~~`always-show-log-out`?~~ **acceso** | cadute per conseguenza, non per scelta |
| ✅ **nessuno spegne il server**, chi è davanti alla macchina compreso — e l'utente remoto ha **il solo logout** | `DECISIONI.md` §4.7, `SPECIFICHE.md` §11.3, 15 agosto |
| ✅ **il logout si raggiunge in due modi**: la voce del menu e `Ctrl+Alt+Fine` — ❌ `Ctrl+Alt+F12` e ❌ `Win+F12` scartate **con una misura ciascuna**, ❌ **nessun bottone a schermo** | `DECISIONI.md` §4.1-quinquies, `SPECIFICHE.md` §5.2-bis, 15 agosto |
| ✅ **il multi-tenant è della fase 12** — qui **un utente remoto per volta**, ⛔ ma il guardiano di logind discrimina **per utente** | `DECISIONI.md` §4.6-quater, 15 agosto |

| ✅ **due secondi all'accesso vanno bene; diciotto no** — 16 agosto. ⇒ Il guadagno da 2,1 s a ~1,2 s (dichiarare la misura della finestra nel saluto invece che dopo l'ammissione) **non si fa adesso**: costa mezza giornata **nella stretta di mano**, che è l'unico pezzo dove uno sbaglio è un buco e non un difetto estetico. ⭐ Si riprende quando il protocollo si aprirà comunque — la fase 12 tocca quella zona | qui sotto, e la misura è già fatta |

**Aperte:** ⭐ nessuna. ⇒ Il lavoro della fase è quello di §1, §2 e §3, e il prossimo gesto è il
**banco**, non il codice.

### ⏳ Il secondo che si potrebbe recuperare, con la misura già fatta

`[M]` L'accesso costa **2087 ms** di mediana, e **968** sono il figlio che aspetta: il browser
dichiara la misura della sua finestra **solo dopo essere stato ammesso**, e prima di allora la
sessione non può nascere perché non si sa a che misura.

⇒ Se la misura arrivasse **col saluto** — come già fa il tetto del decodificatore — la sessione
nascerebbe **durante** il secondo fisso invece che dopo: accesso a **~1,2 s**. ⛔ E il secondo fisso
resterebbe intatto: cambia *quando si dichiara la misura*, non *quando si risponde*, quindi il
canale del cronometro resta chiuso.

⚠ **Il costo**: `RCP.md`, `pagina.html`, `rcp.c` **e il suo gemello identico byte per byte** in
`banchi/rcp/`, `figlio.c`, il client di banco, più una prova per il caso «client vecchio che non lo
manda». **Mezza giornata**, e nel pezzo più delicato del programma.

---

## 5 · Che cosa non ha funzionato

### 15 agosto 2026, sera — quattro cose, e tre le ha trovate il banco

1. ⛔⛔ **La pila PAM del prodotto non chiamava `pam_systemd`.** `src/remotix.pam` chiudeva con
   `common-session-noninteractive`, che su Debian **non** contiene `pam_systemd` — quindi nessuna
   sessione logind, quindi niente `is_headless()` e niente soggetto per §5.1. ⭐ **E funzionava
   lo stesso, per un accidente rovesciato**: il file non era installato, PAM ripiegava su `other`,
   e `other` include `common-session`, che `pam_systemd` ce l'ha. ⇒ Installare il nostro file
   «come si deve» avrebbe **rotto** quel che l'assenza del file faceva funzionare.
   *(`DECISIONI.md` §1.10-ter.)*
2. ⛔ **La regola polkit di v1 copriva 3 azioni su 12**, e la mancante era
   `power-off-multiple-sessions` — cioè **il caso multi-utente**, l'unico per cui la regola era
   stata scritta. Con un utente solo funzionava.
3. ⛔ **Il mio ragionamento su root era sbagliato**, e me l'ha detto la misura: avevo scritto in
   `DECISIONI.md` che serviva un'eccezione per root, altrimenti `sudo systemctl poweroff` sarebbe
   fallito. `[M]` Non serve: logind guarda `CAP_SYS_BOOT` **prima** di polkit. ⇒ La voce è stata
   corretta, e con lei la conseguenza vera — **la verifica non si può fare dal server, che è root**.
4. ⛔⛔ **Il banco è stato verde due volte per il motivo sbagliato**, ed è la forma che questo
   progetto paga più spesso:
   - la prima perché **gli utenti di prova non esistevano** (il rootfs vive in RAM e il riavvio li
     aveva cancellati come la chiave ssh): PAM apriva sessioni per un conto inesistente, e i casi
     «falso» erano falsi perché **non c'era niente**;
   - la seconda perché **logind rifiutava in silenzio** la seconda sessione sulla stessa console
     virtuale: `pam_systemd` è `optional`, PAM tornava `SUCCESS`, e il caso 6 era verde **perché
     vuoto**.
   ⇒ In tutt'e due i casi a smascherarlo è stato **il dump di `loginctl` dentro il banco**: un banco
   che dice solo il colore fa ricominciare la caccia da capo.

### 15 agosto 2026, 19:02 UTC — lo schermo nero, e la domanda dell'utente

**Il sintomo**: l'utente si collega, entra, e **non vede il desktop**. La domanda che ha fatto —
*«sicuri che non hai introdotto regressioni?»* — era quella giusta da fare.

**Non era una regressione**, e il registro lo diceva per intero: l'attacco è passato (nessun `0x05`,
nessun rifiuto), e il figlio ha scritto tre volte

> ⛔ *runtime «/run/user/1001» NON c'è, socket del bus non c'è — senza bus non c'è niente da catturare*

⇒ Il riavvio aveva cancellato l'utente `prova` insieme alla chiave ssh (rootfs in RAM); ricreandolo
**non avevo acceso il linger**, e `/run/user/<uid>` lo crea quello. Curato con
`loginctl enable-linger prova prova2`, e scritto come **requisito** in `DECISIONI.md` §1.10-ter.

> ### ⭐⭐ E l'utente ha visto sotto il sintomo un tema — 15 agosto 2026
>
> > *«Bisogna fare attenzione al corretto setting delle variabili d'ambiente (XDG…). Dovrebbe essere
> > compito del session manager, ma per qualche motivo in REMOTIX sembra che non vengano
> > impostate.»*
>
> ⭐ **Ha ragione, e la ragione è strutturale**: quelle variabili le imposta `pam_systemd` al login,
> e ⛔ **noi il login non lo facciamo** — `figlio.c:2428` dichiara fuori mandato far nascere la
> sessione. ⇒ Nessuno le imposta, e noi le **componiamo a mano**.
>
> **Quel che c'è oggi**, letto nel codice:
>
> | dove | che cosa compone |
> |---|---|
> | `figlio.c:723-737` | `HOME`, `USER`, `LOGNAME`, `PATH`, `SHELL=` (vuota), `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS` — **sette, e nient'altro esiste dall'altra parte** (`execve`) |
> | `sessione.c:492-511` | le due di sopra più `XDG_CURRENT_DESKTOP`, `XDG_SESSION_DESKTOP`, `XDG_SESSION_TYPE`, `LANG` |
>
> ⛔ **E `XDG_RUNTIME_DIR` è ASSERITA, non ottenuta**: si scrive `/run/user/<uid>` per convenzione.
> La convenzione è giusta su systemd — ⚠ ma è esattamente la forma del guasto di stasera: un valore
> **dichiarato** al posto di un valore **avuto**.
>
> ⚠ **Quel che nessuno imposta, e che ricade sui predefiniti in silenzio**: `XDG_DATA_DIRS`,
> `XDG_CONFIG_DIRS`, `XDG_DATA_HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME`,
> `XDG_SESSION_CLASS`. ⛔ E `XDG_SESSION_ID` **di proposito** (`sessione.c:523`).
>
> ⇒ **Il lavoro che ne nasce, per questa fase:**
> 1. un posto solo che compone l'ambiente **e lo verifica**, scrivendo per ogni variabile **da dove
>    viene** — asserita, ereditata, dedotta. Oggi `sessione.c` già lo fa per il bus (*«assente: uso
>    …»*), ed è la forma da estendere;
> 2. ⛔ `XDG_RUNTIME_DIR` si **verifica prima di `execve`**: esiste, ed è di quell'uid. Se non c'è, il
>    messaggio deve **nominare la causa probabile** — *«quell'utente ha il linger acceso?»* — invece
>    del solo sintomo, che stasera è costato un giro;
> 3. decidere se le sei `XDG_*_DIRS`/`_HOME` vadano dichiarate invece di lasciate al predefinito.

### 15 agosto 2026, 20:00 UTC — ⛔⛔ il lag, e il prezzo nascosto dell'headless

**Il sintomo**, riferito dall'utente: *«qualche piccolo lag in generale»*, e poi il numero che conta —
*«impartisco un comando nel terminale e risponde con 1-2 secondi di ritardo»*.

**Le due cose escluse per prime, con una misura ciascuna** — ⛔ e la prima è quella che avevo
aggiunto io, quindi andava esclusa per prima:

| sospetto | misura |
|---|---|
| il **ripasso di logind** ogni 2 s, sincrono nel ciclo dei fotogrammi | ⭐ `[M]` 200 chiamate: **mediana 0,125 ms**, p95 0,226, **max 0,351 ms**. ⇒ Non è quello, e il ripiego «sincrono» di `sentinella.c` regge |
| il **danno degenerato** — `libmutter-WARNING: Not enough buffers (4) to accommodate damaged regions (6)` | `[M]` 18 avvisi in tutto, non continui. ⚠ E la lettura del sorgente di Mutter (`meta-screen-cast-stream-src.c:891`) dice che **non** sono i buffer PipeWire: sono i **posti-regione** nel metadato `VideoDamage`, che chiediamo `×4` con tetto `×16` (`cattura.c:419`). Quando le regioni sono di più, Mutter dichiara **tutto il fotogramma danneggiato**. ⏳ Difetto vero, piccolo, da curare — ma non è questo il lag |

⛔ **La causa era il compositore che disegnava IN SOFTWARE**, e l'ho introdotta io: `[M]`
`gnome-shell` non aveva **nessun** nodo `/dev/dri/*` aperto. Ricreando l'utente `prova` dopo il
riavvio l'ho fatto con `useradd` nudo — `groups=prova` e basta — mentre `nicfio` è in **`video`
(44)** e **`render` (991)**, e i nodi sono `root:render` in modo `0660`. Senza accesso alla GPU,
Mesa ripiega su llvmpipe e il compositore compone **a mano** un desktop di 2544×926.

**La cura, in due passi e il secondo non è ovvio**: `usermod -aG video,render prova` — ⛔ **e far
rinascere `user@1001.service`**, perché il compositore lo avvia il **gestore d'utente**, che le
credenziali le fissa alla propria partenza: `[M]` dopo il solo `usermod` il processo aveva ancora
`Groups: 1001`. Dopo il riavvio del gestore: `Groups: 44 991 1001` e **10 descrittori** su
`/dev/dri/renderD129`.

> ### ⭐⭐ E LA DOMANDA DELL'UTENTE HA SCOPERTO UN PREZZO CHE NON ERA SCRITTO DA NESSUNA PARTE
>
> > *«Nei DE normali l'utente NON appartiene ai gruppi `video` e `render`, eppure usano
> > l'accelerazione hardware. Come mai?»*
>
> ⭐ **Perché su un desktop normale non servono i gruppi: serve il SEAT.** `[M]` verificato sulla
> macchina: `/dev/dri/renderD129` porta i tag udev **`uaccess`** e **`seat`**, e logind concede
> l'accesso con un'**ACL per utente** — è il `+` nei permessi — all'utente della sessione **attiva
> su quel seat**. Nessun gruppo, nessuna configurazione: la dà il fatto di essere seduti lì.
>
> ⛔ **E noi quel seat non ce l'abbiamo, di proposito**: è la condizione di `is_headless()`
> (`DECISIONI.md` §4.3-bis), cioè quel che ci salva dalla revoca del blocca-schermo di GNOME.
> `[M]` `getfacl` sul nodo, adesso: **nessuna voce per utente** — perché nessuna sessione sta su un
> seat.
>
> ⇒ ⛔⛔ **Il prezzo dell'headless è la perdita delle ACL di `uaccess`**, e nessun documento lo
> diceva. Per una sessione REMOTIX i gruppi `video` e `render` **non sono una comodità
> dell'ambiente di prova: sono un requisito del prodotto**, esattamente come il linger — e come
> quello vanno dichiarati e verificati, o si ripaga una serata.
>
> ⚠ **E c'è una coda da non perdere**: senza la regola udev di `DECISIONI.md` §4.6-ter — `[M]` non
> installata: `/etc/udev/rules.d` è vuota — i gruppi danno accesso a **tutt'e due** le schede, e
> `[M]` il compositore ha scelto **`renderD129`, l'AMD**. Che sia quella giusta è una decisione
> della fase 8, non un caso da lasciare all'ordine di enumerazione.

### 15 agosto 2026, 22:09 — ⭐⭐ la controprova, e la porta l'utente

*Registrazione dello schermo del client, 17,3 s a 2560×1080, consegnata dall'utente.*

**La scena**: il banco WebGL **«Aquarium»** di `webglsamples.org` — 100 pesci, tela 1024×1024 —
girato **dentro** il desktop remoto in Firefox, e guardato attraverso REMOTIX.

| che cosa | misura |
|---|---|
| il contatore dell'Aquarium, **letto a piena risoluzione su 16 secondi consecutivi** | ⭐ **58 · 59 · 60 · 61** — inchiodato a sessanta, mai un tuffo |
| fotogrammi **distinti** arrivati sullo schermo del client (`mpdecimate`) | ⭐ **453 su 17,26 s = 26,2 al secondo** ⚠ e il tetto è del registratore, che campiona a 30: non si distingue «26 consegnati» da «più di 26, campionati 30» |

⭐ **È la controprova della cura di §5 di stanotte**: llvmpipe non fa 60 fps su un WebGL con 100
pesci, neanche per sbaglio. ⇒ La GPU c'è, e il difetto dei gruppi mancanti era davvero tutto il lag.

⚠ **E quel che questa misura NON dice, dichiarato**: non è una misura di **latenza** — dice che il
flusso è fluido, non quanto tempo passa fra il tasto e il pixel. Quella resta `[M]` 41 ms della coda
della fase 4, e va rifatta su questa configurazione.

> ### ⛔⛔ E QUESTA MISURA È STATA FATTA SULLA SCHEDA SBAGLIATA — vincolo posto dall'utente, 15 agosto
>
> > *«I test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco. La solidità del
> > sistema la si vede su GPU poco potenti, non mostri come la RX 6800.»*
>
> `[M]` I 60 fps dell'Aquarium sono stati presi sulla **Radeon RX 6800**, perché senza la regola
> udev di `DECISIONI.md` §4.6-ter — non installata — la scheda **la sceglieva il compositore**, e
> aveva preso la discreta. ⇒ ⛔ **Il numero non vale come misura del prodotto**: dice quanto è veloce
> quel ferro.
>
> ⭐ **Curato la sera stessa** (`DECISIONI.md` §4.6-quinquies): `gpu-udev.sh 0000:03:00.0` esclude la
> Radeon, e `[M]` dopo il riavvio del gestore e della sessione `gnome-shell` apre **6 descrittori su
> `renderD128`** — la **Intel UHD 730**, e solo quella.
>
> ⇒ **La misura dell'Aquarium va rifatta sull'integrata**, ed è quella che conta.
>
> ### ⭐⭐⭐ E RIFATTA SULL'INTEGRATA REGGE — riferita dall'utente, 15 agosto 2026, 20:15
>
> > *«Su Android ho 60 fps fissi con il test Aquarium.»*
>
> `[M]` **Verificato che la scena fosse quella giusta prima di crederci**: `gnome-shell` pid 22462 —
> quello nato **dopo** la regola udev — ha 6 descrittori su **`renderD128`**, la Intel UHD 730; e il
> registro dice che alle `20:15:12` si è collegato **`192.168.0.24`**, un dispositivo diverso dal
> portatile (`.3`), con tela 2544×926 e vista 2560×926: il **DeX**.
>
> ⇒ ⭐ **WebGL Aquarium, 100 pesci, 60 fps fissi — sulla GPU integrata, guardato da Android.** ⚠ E
> vale doppio perché DeX è l'uso **primario** (`DECISIONI.md` §5-bis.0), cioè il caso in cui il filo
> è più lungo e il dispositivo più debole. ⛔ Resta quel che questa misura non è: **non è latenza**.

### 15 agosto 2026, 20:27 UTC — ⭐⭐⭐ IL PRODOTTO FA NASCERE LA SESSIONE, e la catena si chiude

*Ordine dei lavori **cambiato su indicazione dell'utente**: «il discorso `Ctrl+Alt+Fine` introduce
poi anche il discorso della persistenza della sessione, del detach e re-attach». ⛔ Aveva ragione, e
la conseguenza era più stretta di così: **implementare il logout prima che il prodotto possieda la
nascita della sessione sarebbe stato dannoso** — `Ctrl+Alt+Fine` avrebbe chiuso la sessione e
nessuno ne avrebbe fatta un'altra. Una funzione che porta l'utente allo schermo nero.*

**Che cosa è stato scritto:**

| | |
|---|---|
| `figlio.c`, `diventa_ed_esegui()` **passo 2-bis** | apre la **sessione PAM** dopo la chiusura dei descrittori e prima di scendere all'uid: `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`, `PAM_RHOST`, ⛔ **nessun `XDG_SEAT`** — headless per costruzione. `pam_end` **senza** `pam_close_session`: la sessione è del processo guida, ed è I4 vista dal sistema |
| `figlio.c`, `prendi_il_palco()` | la riga *«guardo e non tocco»* è diventata **«LA FACCIO NASCERE io»**, con la briglia di un minuto |
| `sessione.c/h`, `sessione_fai_nascere()` | fa nascere **senza aspettare**: `sessione_assicura()` attende fino a 40 s, e chi chiama è l'unico processo che in quei 40 s deve rispondere al padre (`LEZIONI.md` §6.2-bis). ⭐ L'attesa esiste già ed è il ciclo di ri-tentativi |
| `/media/REMOTIX/tmp/riavvia-7700-unita.sh` | ⛔ **il server fuori da ogni sessione utente** — vedi sotto |

⛔⛔ **E il vincolo di dispiegamento che ne nasce, misurato**: `pam_systemd`, quando chi chiama sta
già in una sessione, **non ne crea una seconda e non lo dice**. `[M]` Col vecchio
`riavvia-7700.sh` — che usa `setsid`, il quale stacca il terminale ma **non cambia il cgroup** — il
server stava in `session-127.scope` (la ssh di `nicfio`), e i figli restavano senza sessione: **lo
stesso schermo nero, per una causa nuova**. Con `systemd-run` sta in `system.slice`.

**La prova, da piazza pulita** — nessuna sessione di `prova`, nessun `/run/user/1001`, ⛔ **linger
spento**, nessuna impalcatura:

| ora | il registro |
|---|---|
| 20:27:15 | `⭐ IL BUS DI SESSIONE È MIO: collegato come uid 1001` |
| 20:27:15 | `⭐ nessuna sessione grafica per «prova»: LA FACCIO NASCERE io (tela 1920x1080) e torno subito` |
| 20:27:15 | `sessione avvio la sessione grafica: exec gnome-session --session=gnome` |
| 20:27:47 | `cattura il nostro monitor è Meta-0 («Virtual remote monitor»), 0 prima e 1 dopo` |
| 20:27:47 | ⭐ `fotogramma catturato COME «prova»: 1920x1080 … BGRx a 8 bit, **non nero**` |

`[M]` **E la sessione nata dal prodotto è quella giusta**: `loginctl` la dà `c52`, **`Class=user`**,
`RemoteHost=remotix`, **`Seat=` vuoto**; e il compositore apre **`renderD128`**, l'integrata — la
regola udev regge anche su una sessione che nasce da sola.

⚠ **Il prezzo, dichiarato**: dal primo attacco al primo fotogramma passano **~32 secondi**, ed è
l'avvio a freddo di `gnome-session`. Succede una volta per sessione, ⛔ ma in quei 32 s il client è
attaccato e non vede niente — e oggi non gli diciamo perché. ⏳ Da coprire.

### 15 agosto 2026, 20:50 UTC — ⛔⛔ «il terminale è congelato finché non muovo il mouse»

**Il sintomo, e l'ha isolato l'utente** dopo che io avevo inseguito la banda per mezz'ora:

> *«Dal terminale do il comando `exit` e il terminale sembra come congelato: non appena muovo il
> mouse allora si chiude correttamente.»*

⭐ **Quella frase è la diagnosi**: se lo schermo si allinea appena arriva *un fotogramma qualunque*,
allora il fotogramma giusto **era stato prodotto e non è stato consegnato**.

**Quel che avevo escluso prima, con le misure** — e servono, perché dicono dove NON è:

| | |
|---|---|
| dal palco al filo | `[M]` **0 ms** di mediana e p95, **1 ms** il massimo su 200 fotogrammi |
| il codificatore | `hevc_vaapi` **in hardware** su `renderD128`, chiave in **8,8 ms** |
| il ripasso di logind | `[M]` 0,125 ms di mediana |
| la banda | ⚠ c'erano abbandoni a 45 Mbit/s **con l'Aquarium in moto** — ⛔ ma l'utente ha detto *«niente Aquarium»*, e la pista è caduta |

⛔⛔ **LA CAUSA, e stava scritta in un commento del nostro codice**: `cattura.c` consegnava il
fotogramma **solo se qualcuno lo stava aspettando in quell'istante** —
`if (qualcuno_aspetta && !posto_pieno)` — con questa giustificazione: *«copiare 8 MB per nessuno
sarebbe lavoro dentro la richiamata di tempo reale, fatto per niente»*.

⭐ **Il ragionamento è giusto per il caso a regime e sbaglia il caso che l'utente vede.** La finestra
che si chiude produce una **raffica**: prendiamo il primo fotogramma e passiamo ~20 ms a convertirlo
e comprimerlo; ⛔ tutti quelli che arrivano in quei 20 ms trovano `qualcuno_aspetta == FALSE` e
**vengono buttati — compreso l'ultimo**, quello con la finestra già sparita. Poi la scena è ferma e
Mutter non manda più niente (cadenza `0/1`: *«un fotogramma quando cambia qualcosa»*). ⇒ L'utente
resta a guardare il **primo** fotogramma della raffica, finché un movimento non ne produce un altro.

⛔ **E la seconda metà dello stesso difetto era dal lato di chi consuma**: `cattura_prendi()`
all'ingresso faceva `posto_pieno = FALSE`, cioè **buttava via il fotogramma che trovava già pronto**
e si metteva ad aspettarne uno nuovo che, a scena ferma, non sarebbe mai arrivato.

**La cura**: si tiene **sempre l'ultimo** — un posto solo, vince il più recente, che è anche la
politica giusta per un desktop remoto (di un fotogramma vecchio non se ne fa niente nessuno). ⭐ E il
costo che il vecchio commento temeva **si paga meno di prima**: il buffer si **riusa**
(`posto_capienza`), quindi la richiamata di tempo reale fa una `memcpy` e non più una
`g_free`+`g_malloc` da 8 MB.

⚠ **Con un contatore nuovo nella riga di riassunto** — *«sostituiti nel posto N (prima del 15 ago
erano PERSI)»* — perché il numero che conta non è che la cura c'è: è **quante volte serve**.

> ### ⭐⭐⭐ CONFERMATO DALL'UTENTE — 15 agosto 2026, e il giudizio va oltre il difetto
>
> > *«Ora il terminale si chiude subito, problema risolto **sia su Linux sia su Android**. Inoltre
> > adesso il sistema mi sembra **tremendamente responsivo**, i tempi di risposta sono istantanei
> > anche su Android, e considerando che sia su una Intel integrata direi risultato eccellente.»*
>
> ⭐ **E il guadagno è più grande della cura, per una ragione che vale la pena capire**: non si
> perdeva solo l'ultimo fotogramma — si perdevano **tutti quelli di ogni raffica**, cioè quelli che
> arrivavano mentre comprimevamo il precedente. ⇒ Ogni finestra che si apre, ogni scorrimento, ogni
> riga di terminale era più a scatti del necessario, **e nessuno l'aveva mai notato** perché il
> difetto si vedeva solo nella coda.
>
> ⇒ ⚠ *Un difetto che si manifesta in un caso limite può costare in tutti gli altri, in silenzio.*
> La lezione per intero è in `LEZIONI.md` §6.5.
>
> ⏳ **E ora la misura di latenza va rifatta**: i `[M]` 41 ms della coda della fase 4 sono di prima
> di questa cura, e su una configurazione diversa. Il numero vero non lo sappiamo ancora.

*⚠ L'orologio della macchina di prova è **UTC**, cioè due ore indietro rispetto al nostro: le ore
qui sotto sono le sue.*

### 15 agosto 2026, 18:20-18:35 UTC — la macchina, dopo il riavvio

*La macchina si era inchiodata; l'utente l'ha riavviata, e il rootfs vive in RAM ⇒ chiave ssh
reinstallata e `provision-server.sh` rieseguito.*

| | esito |
|---|---|
| **`provision-server.sh`** | passato, ⛔ **tranne la §4** (*«daemon-reload d'utente fallito»*, il bus d'utente non c'era). ⭐ **E non è un problema**: quella sezione scrive `--virtual-monitor` in `/etc/systemd/user/`, cioè proprio quel che v2 **non vuole più** dal 14 agosto — `sessione.c` scrive il suo drop-in `zz-` apposta per vincere su quello. ⇒ **provisioning di v1 rimasto indietro**, da rifare per v2 |
| ⭐ **`loginctl` — il discrimine** | `[M]` la sessione **ssh** risulta `Remote=yes`, `RemoteHost=192.168.0.3`, `Type=tty`, **`Seat=` vuoto**. Il seat esiste (`seat0`) ma ⛔ **nessuna sessione grafica locale è viva**: per provare `0x05` servirà un accesso vero alla consolle |
| ⛔⛔ **la regola polkit di v1 copriva 3 azioni su 12** | `[M]` `org.freedesktop.login1.policy` ha anche `*-multiple-sessions` e `*-ignore-inhibit`. ⇒ Con **più utenti** logind chiede `power-off-multiple-sessions`, che v1 non nominava: **falliva esattamente nel caso per cui era scritta**. ⚠ E `…login1.halt` **non esiste**: riga morta |
| ⭐ **root non ha bisogno di eccezioni** | `[M]` con la regola in vigore: da `nicfio` `CanPowerOff="no"`, **da root `"yes"`** — logind guarda `CAP_SYS_BOOT` **prima** di polkit. ⇒ ⛔ **la verifica va fatta dal FIGLIO, non dal server**, che è root e si sentirebbe dire sempre di sì |
| ⭐ **il tasto fisico era vivo** | `[M]` tutte le righe `Handle*` di `logind.conf` erano **commentate** ⇒ `HandlePowerKey=poweroff`. Il pulsante spegneva il server con chiunque collegato sopra |
| ✅ **le due cinture installate e rilette** | `[M]` da `nicfio`: `CanPowerOff` `CanReboot` `CanSuspend` `CanHibernate` = **tutte `"no"`**; `systemd-analyze cat-config` dice `HandlePowerKey=ignore`, `HandleSuspendKey=ignore`, `HandleLidSwitch=ignore`. ⇒ `src/remotix-niente-spegnimento.rules` e `src/remotix-tasti.conf`, **nel repository** (I7) |
| ⭐ **la sospensione ha una cintura più forte** | `[M]` `sleep.conf.d AllowSuspend=no` fa dire `CanSuspend="no"` **anche a root**: è systemd a rifiutare, non polkit |

### 15 agosto 2026, 18:31-18:45 UTC — il guardiano di logind, costruito e certificato

| | |
|---|---|
| **il codice** | `src/sentinella.c` + `.h` (nuovi), il gancio `sessione_locale` in `rcp.h`/`rcp.c`, `wt_locale_gancio` e `wt_sorveglia_locali()` in `webtransport.c`, la cucitura in `main.c` con ripasso ogni **2 s** |
| ⭐ **è vivo sul server** | `[M]` nel registro: *«guardiano delle sessioni locali pronto (bus di sistema); il discrimine è il SEAT, non «Remote»»* |
| ⭐⭐ **la misura che giustifica il discrimine** | `[M]` una sessione fatta **come la nostra** — `pam_open_session` senza `XDG_SEAT` — risulta a logind: `Seat=` **vuoto**, `Remote=no`, `Type=wayland`. ⛔ Cioè **indistinguibile da una locale** se il criterio fosse `Remote`: il primo utente collegato sarebbe stato respinto con `0x05` dalla sua stessa sessione |
| ✅ **il banco** | `banchi/05-b1-sentinella.c`, **6 casi, 0 rossi**: nessuna sessione · una come la nostra · una locale (`seat0`, wayland) · chiusa la locale · la locale è **di un altro utente** · l'utente è alla consolle **in una sessione di testo** |
| ⭐⭐ **certificato** | `banchi/05-b1-certifica.sh`, **3 guasti innestati, tutti e tre cadono dove devono**: tolto il seat → rossi 2 4 5 6; tolto l'utente → 5 6; tolto il tipo grafico → 6 |
| ⛔ **e la certificazione ha scritto il banco, non solo controllato** | il guasto «il tipo grafico non si guarda più» non faceva cadere **niente** ⇒ nessun caso esercitava quel controllo. ⭐ Da lì è nato il **caso 6** — l'utente alla consolle in una sessione di testo, che `SPECIFICHE.md` §5.1 ammette esplicitamente («testuali e grafiche convivono») e che nessuno aveva provato |
| ⏳ **quel che il banco NON prova**, dichiarato | non prova il filo (`0x05` non è mai uscito su una connessione vera), non prova `0x04` end-to-end, e ⛔ **non prova la scena con una sessione locale VERA**: sulla macchina non c'è nessuno alla consolle, e le sessioni del banco le crea PAM |

## 7 · Il giudizio dell'utente

*(la fase si chiude qui, non su un documento completo)*
