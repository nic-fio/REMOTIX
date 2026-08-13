# GNOME come desktop — studio del codice, per la fase 11

*Scritto l'8 agosto 2026, con dieci ricerche parallele sui sorgenti clonati alle versioni di Debian
Trixie. È l'ottavo studio del progetto, e chiude il giro dei quattro desktop.*

> ## ⚠ Perché questo studio esiste, e perché arriva per ultimo
>
> GNOME è il desktop che REMOTIX serve **in produzione da dieci fasi**. Ma il documento che avevamo —
> `gnome-remote-desktop.md` — studia **il server RDP di GNOME**, cioè un concorrente, **non il
> desktop**. Sessione, schermo di blocco, energia, voci pericolose, configurazione: su KDE, XFCE e
> LXQt li abbiamo studiati tutti; su GNOME **mai**, perché nessuno ci aveva costretti.
>
> ⭐ **Il risultato è che questo studio trova più difetti nostri di quanti ne trovino gli altri tre
> messi insieme** — e tutti sul desktop che consideravamo finito.

> **Le marche:** **[R]** letto nel codice, con `file:riga` — non è una misura · **[R-pkg]** letto nel
> pacchetto Debian · **[M]** misurato · **[?]** dedotto · **[✗]** verificato assente, con controllo
> positivo · **`[≠]`** ⚠ **il codice contraddice un nostro documento**.
>
> Dettaglio nei dieci rapporti in `reference-gnome/rapporti/`.

---

## 1. In due minuti

### 1.1 ⛔ Le sette cose che su GNOME non abbiamo mai fatto

*Lette nel codice del prodotto sul server, sola lettura.*

| # | | |
|---|---|---|
| 1 | **il drop-in dell'unità della Shell** | `scrivi_dropin()` è chiamata **solo** `if (tipo == COMPOSITORE_KWIN)` (`src/sessione.c:671`). Su GNOME la Shell parte con `ExecStart=/usr/bin/gnome-shell` secco, **senza `--headless`** |
| 2 | **l'inibizione dell'energia** | `energia_inibisci()` **ritorna NULL** su Mutter (`src/energia.c:112-113`) |
| 3 | **il blocco schermo** | zero chiavi, zero recupero |
| 4 | **le voci pericolose** | nessun lockdown — su KDE l'utente l'aveva chiesto e l'aveva avuto |
| 5 | **la configurazione** | **zero occorrenze** di `gsettings`/`dconf`/`org.gnome.desktop` in tutto `src/` |
| 6 | **`SPA_META_Cursor`** | chiediamo `cursor-mode=2` (metadato) ma non chiediamo il metadato ⇒ **il cursore non arriva affatto** |
| 7 | **`SPA_META_SyncTimeline`** | e **Mutter lo offre** — è il *release* mancante della copia zero, cioè la caccia della fase 9 nel posto giusto |

⭐ **Una sola mossa ne paga tre**: un profilo dconf in `$XDG_RUNTIME_DIR` chiude insieme il blocco
schermo, le voci pericolose e la configurazione (§6).

### 1.2 ⛔ E la cosa che ci tiene in piedi oggi è un incidente

**Su GNOME lo schermo di blocco non mostra uno schermo di blocco: ci stacca la sessione RDP.**
Entrando in `unlock-dialog`, gnome-shell chiama `inhibit_remote_access()` e Mutter — testualmente —
*«Any active remote access session will be terminated»*: chiude ScreenCast, RemoteDesktop e
InputCapture, **e rifiuta di ricrearne**.

✅ **L'eccezione è `is_headless()`.** E noi siamo headless — **ma non perché l'abbiamo chiesto**: Mutter
si degrada da sé quando la sessione logind non ha un seat, con un `g_message`
(`meta-backend-native.c:759-764`). ⛔ **La precondizione che ci salva non è scritta in nessuna nostra
riga.**

### 1.3 ⭐ E la scoperta che riapre una caccia chiusa male

**R29 è sbagliata: il DMA-BUF di Mutter non è un «diff».** Due prove indipendenti nel codice — il blit
copia **l'intero** framebuffer di vista, e Cogl **svuota deliberatamente lo stack di clip** prima di
`glBlitFramebuffer`; e per un CRTC virtuale la vista è un **`CoglOffscreen` singolo e persistente**,
non uno swapchain, quindi il ridisegno parziale vi si **accumula**.

⭐ **Da cui si spiega perché la cura peggiorava le cose**: la superficie di accumulo copiava i soli
rettangoli danneggiati da un buffer che conteneva **già il fotogramma intero**.

⭐ **E il difetto vero è il *release***: `can_reuse_pw_buffer` — l'unico punto in cui Mutter aspetta
noi — **si arrende alla prima riga** se manca `SPA_META_SyncTimeline`, e riusa il buffer **mentre
VA-API lo sta ancora leggendo**. Due schermate che si alternano è esattamente il sintomo che ci si
aspetta da lì. E il riferimento fa il contrario di quel che avevamo concluso: **trattiene** il
`pw_buffer` fino a lettura finita.

⚠ **È una lettura di codice, non una misura** — ma è coerente con tutti i sintomi, e le due cure
candidate sono entrambe piccole.

---

## 2. La mappa

| Che cosa | Dove | Versione Trixie |
|---|---|---|
| il compositore | `reference-gnome/mutter/` | **48.7** |
| la shell | `gnome-shell/` | **48.7** |
| la sessione | `gnome-session/` | **48.0** |
| energia, media keys, xsettings | `gnome-settings-daemon/` | **48.1** |
| gli schemi | `gsettings-desktop-schemas/` | **48.0** |
| il gestore d'accesso | `gdm/` | **48.0** |
| il concorrente | `gnome-remote-desktop/` | **48.1** |
| il portale, le impostazioni, dconf | `xdg-desktop-portal-gnome/` 48.0, `gnome-control-center/` 48.4, `dconf/` 0.40.0 | |

⚠ **[M] Sul server GNOME non è più installato** (`dpkg-query` → not-installed, nessuna
`gnome.desktop`): **niente di questo studio è oggi verificabile sulla nostra macchina**, e il
ripristino va rifatto prima di qualunque misura.

---

## 3. La sessione senza monitor

*Dettaglio: `rapporti/01-sessione-gnome.md`, `08-gdm-remote-login.md`.*

### 3.1 ⭐ La più semplice delle tre famiglie

| | |
|---|---|
| **Mutter** | ⭐ **nessuna opzione necessaria**: se la sessione logind è di tipo `wayland`, attiva e **senza seat**, si mette in headless **da solo** (`meta-backend-native.c:759-764`) |
| KWin | `--virtual --width/--height` obbligatori; `--drm` da SSH **esce con stato 1** |
| labwc | `WLR_BACKENDS=headless` obbligatoria |

⚠ **Ma serve che la sessione logind esista**, e che `XDG_SESSION_ID` sia esportata, o Mutter può
agganciare la sessione sbagliata. ⛔ **E `--virtual-monitor` non è opzionale**: in headless
`needs_outputs=false`, quindi senza quell'opzione la sessione parte **viva, completa e nera**.

**La forma**: ambiente da zero + drop-in su `org.gnome.Shell@wayland.service` con
`gnome-shell --headless --virtual-monitor WxH`, poi `gnome-session --session=gnome`.

⛔ **`SHELL` va messa vuota**: `gnome-session.in:3-14` si ri-esegue dentro una shell di **login** se
`$SHELL` è in `/etc/shells` — cioè si riporta dentro `~/.profile`. È `LEZIONI.md` §5 in agguato.

### 3.2 ⭐ Il logout: una sentinella gratis, e un segnale che non esiste

`gnome-session` **non esce** dopo aver avviato il target: apre un fifo e dorme, uscendo esattamente a
sessione smontata (`main.c:447-487`). È la forma di `labwc --session`: **si sorveglia con un
`SIGCHLD`**, senza `RegisterClient`.

⛔ **[✗] `SessionOver` è dichiarato nell'XML e non viene MAI emesso** — un solo hit in tutti i
repository, la riga dell'XML stessa (controllo positivo: `SessionRunning` c'è anche
nell'implementazione). Chi ci avesse progettato sopra avrebbe aspettato per sempre.

⛔ **`Logout(1)` non basta**: mostra il dialogo se esiste un inibitore. Il congedo va su **`Logout(2)`**.

**La prontezza**: `SessionRunning` **più** `IsSessionRunning()`, che esiste apposta per la corsa fra
sottoscrizione ed evento. ⛔ Il nome `org.gnome.Shell` **non** è un indicatore: è preso prima di
`meta_context_start()`.

✅ **[✗] Nessun equivalente degli 8 s di XFCE**: la catena è a eventi. ✅ **[✗] Nessun
`loginctl terminate-session`, nessun subreaper.**

### 3.3 ⭐ Trovata la riga del difetto storico del bus

Il «bus di sessione che non dà errore, dà silenzio» di `LEZIONI.md` §5 ha un colpevole con nome e
riga: `gnome-session-shutdown.target` tira `gnome-session-restart-dbus.service`, che fa
`StopUnit("dbus.service")` sul manager d'utente (`tools/gnome-session-ctl.c:130-133`). **Il demone
muore, il socket resta.**

⚠ E il ragionamento che salva KDE — «bus d'utente ⇒ sopravvive» — **qui è falso**, pur essendo vera la
premessa. **[?] Contromisura da provare**: mascherare quel servizio (il legame è `Wants=`, debole).

### 3.4 ✅ GDM non ci ostacola

Tutta la sua manovra sul VT è dentro `if (seat_id == "seat0" && seat0_has_vts)`, e l'unico «kill» che
possiede agisce solo su sessioni create da lui. **Una sessione senza seat non la vede: `gdm3` può
restare acceso.** Va spento solo se un giorno vorremo un seat vero.

---

## 4. ⛔ La revoca: lo stato che GNOME ha e gli altri no

*È il fatto più importante del capitolo desktop, e non ha analoghi.*

| | |
|---|---|
| **che cosa succede** | entrando in `unlock-dialog`, gnome-shell chiama `inhibit_remote_access()` (`js/ui/main.js:136-145`); Mutter chiude **ScreenCast, RemoteDesktop e InputCapture** e **rifiuta di ricrearne** (`meta-remote-access-controller.c:146-164`, `meta-backend.c:1454-1468`, `meta-dbus-session-manager.c:349-353`) |
| **l'eccezione** | ✅ `is_headless()` — vero **solo** con backend headless (`meta-backend-native.c:361-369`) |
| **il recupero** | ⭐ esiste e **non chiede password**: `org.gnome.ScreenSaver.SetActive(false)`, oppure il segnale `Unlock` di logind. ⚠ Va eseguito **dal processo REMOTIX**, non dal client |

**Le tre difese, in ordine di forza:**

1. ⭐⭐ **non far girare `gdm.service`**: lo ScreenShield è creato solo se `canLock()`, che interroga
   `org.gnome.DisplayManager` — **[✗] nome non attivabile via D-Bus**. Senza GDM il blocco è
   **impossibile**. ⚠ Ma su Trixie GDM **è attivo**, quindi da solo non basta;
2. **un session mode nostro**: il modo esclude `unlockDialog` ⇒ gnome-shell rifiuta di bloccare.
   ⛔ `parentMode:"user"` **lo rimette**: va ricopiato per intero;
3. **il lockdown** (§5).

⭐ **Da cui la domanda 16 per `LEZIONI.md`**: *«c'è uno stato in cui il compositore ci REVOCA quel che
ci ha già concesso, e chi ha il dito su quel pulsante?»* La domanda 3 chiede se c'è un permesso; questa
chiede se il permesso **può essere ritirato a caldo**, ed è una cosa diversa. Su GNOME esiste un'API
dedicata a farlo.

---

## 5. Il lockdown, le voci, il cursore

*Dettaglio: `rapporti/02-shell-blocco-voci.md`.*

### 5.1 ⭐ Il lockdown vale più del KIOSK di KDE

Delle undici chiavi di `org.gnome.desktop.lockdown`, **quattro** sono lette da gnome-shell 48.7 e una
da gnome-session — e **la voce sparisce**, non si ingrigisce (`system.js:218-226` lega `can-*` a
`visible`), con l'intero pulsante nascosto se spariscono tutte.

| chiave | effetto |
|---|---|
| `disable-lock-screen` | toglie «Blocca». ⛔ **Non copre `SetActive(true)`** — falla nota |
| `disable-user-switching` | toglie «Cambia utente». ⛔ Da togliere **sempre**: l'azione **blocca prima di fallire** |
| `disable-log-out` | ⭐ la più potente: gnome-session risponde `false` a `CanShutdown` ⇒ spariscono **anche Spegni e Riavvia**. ⛔ Ma rifiuta pure `SessionManager.Logout`: **il nostro congedo va rifatto passivo** |
| `disable-command-line` | toglie il dialogo Esegui |

⛔ **[✗] Due chiavi da non mettere**: `user-administration-disabled` **non è letta da nessuno**, e
`idle-activation-enabled` è deprecata e ignorata.

⚠ **La scorciatoia del blocco non è `Ctrl+Alt+L`**: è `<Super>l` più `screensaver-static`, e **le due
liste si concatenano** — vanno azzerate entrambe. ⚠ E come su KDE, la regola polkit per Sospendi va
scritta **`no`, non `auth_admin`**: `challenge` **mostra** la voce.

### 5.2 ⭐ Il cursore: la cura di KDE non serve, e c'è di meglio

Su Mutter il cursore non è nell'immagine **perché lo chiediamo noi**: dichiariamo `metadata` e Mutter
risponde con `inhibit_cursor_overlay`. Con `cursor-mode=1` sarebbe dentro, come su KWin e wlroots.

⭐ **La scelta giusta è `cursor-mode=2` (METADATA)**: pixel puliti **e** forma, posizione e hotspot in
banda laterale, da inoltrare come **cursore RDP nativo** — cioè la cosa a cui su KDE avevamo dovuto
rinunciare. ⛔ **Ma oggi non chiediamo `SPA_META_Cursor`, quindi quei dati non arrivano affatto.**

⛔ E se un giorno servisse il tema trasparente, **il canale non è `XCURSOR_THEME`**: Mutter non la
legge (l'unico `getenv` rilevante è `XCURSOR_PATH`), legge `org.gnome.desktop.interface cursor-theme`.
Trappola peggiore di wlroots: un tema vuoto dà un **quadrato grigio**.

### 5.3 ⚠ I dialoghi che compaiono da soli

Otto, e tre ci riguardano davvero: il **fail-whale** di gnome-session (trigger concreto per noi: il
controllo GL fallito), il **dialogo di benvenuto** (si spegne impostando una chiave, non bloccandola),
e ⭐ il **dialogo di accessibilità innescabile dal nostro stesso input** (Maiusc premuto cinque volte):
il cancello è `org.gnome.desktop.a11y.keyboard enable`, che è già `false` di suo ma **va bloccato**.

✅ **[✗] E la trappola di KWin senza output non ha gemelli**: nessun segnaposto, il vincolo del
puntatore è un no-op, la tastiera non è toccata. Lo schermo virtuale su GNOME è precondizione del
*disegno*, non della sopravvivenza.

---

## 6. ⭐ dconf: l'unica configurazione dei quattro desktop che regge

*Dettaglio: `rapporti/04-dconf-configurazione.md` — ed è l'unico rapporto con misure `[M]` proprie.*

| | |
|---|---|
| **i lock reggono** | `gsettings set` su chiave bloccata **esce con 1** e lo dice: il controllo è **sincrono e locale**, prima che parta il messaggio D-Bus. ⭐ Dove xfconf usciva con successo e ripristinava in silenzio |
| **vincono sul valore dell'utente** | **[M]** utente `true`, lock e db `false` ⇒ `gsettings get` risponde `false`: il valore in casa viene **saltato in lettura** |
| ⭐ **non serve root** | `$XDG_RUNTIME_DIR/dconf/profile` è la terza priorità di caricamento. **[M]** scritto il file la sessione vede valori e lock; cancellato, torna tutto com'era; **zero byte scritti in `~`** |

**Le tre trappole, tutte misurate:**

1. ⛔ **`.gschema.override` non è un'alternativa**: cambia il *default*, che sta **sotto** al valore
   dell'utente — e l'utente ha già `lock-enabled=true`, che è sempre il caso reale;
2. ⛔ **`XDG_CONFIG_HOME` effimero fallisce in silenzio**: `dconf-service` è un processo separato con
   **il suo** ambiente ⇒ la scrittura riesce e finisce **nella casa vera**;
3. ⛔ **un lock senza valore non congela: azzera al default del fornitore** (600 → 300). Ogni chiave
   bloccata va **anche** valorizzata.

⚠ E due dettagli che costano un pomeriggio: una riga di lock **senza `/` iniziale è scartata in
silenzio** (l'unica verifica è `gsettings writable` chiave per chiave), e **`file-db:` non rilegge mai**
a caldo — se serve il caldo serve `system-db:`, e quindi root.

⭐ **Il precedente da copiare è GDM, non `gnome-remote-desktop`**: GDM fa esattamente questo — profilo
nell'ambiente di lancio, `file-db:`, **28 chiavi bloccate** **[R-pkg]** — e da lì si rubano due righe
che non avremmo pensato: azzerare la scorciatoia del blocco **oltre** a disabilitarlo, e neutralizzare
il terminale predefinito.

⛔ **[✗] `gnome-remote-desktop` non configura la sessione affatto**: nessun profilo, nessun lock,
nessuna inibizione. **Il vuoto è nostro, non stiamo duplicando niente.**

---

## 7. ⛔ L'energia: il server si addormenta

*Dettaglio: `rapporti/03-energia-inibizioni.md`.*

**Il default upstream *e* Debian di `sleep-inactive-ac-type` è `suspend`, con timeout 900 s**, e
`gsd-power` chiama `logind Suspend(false)`.

⚠ **Oggi non ci morde, ma per accidente**: `SessionIsActive` è falso perché non esiste una sessione
logind grafica, quindi gsd-power si disarma da sé. **Un guadagno che non abbiamo scelto e che una
misura può ribaltare** — misurato: una sessione logind **senza seat** risulta comunque `Active=yes`.

⭐ **La cura è una chiamata sola**: `org.gnome.SessionManager.Inhibit(app_id, 0, reason, 12)` — cioè
`SUSPEND(4) | IDLE(8)` **insieme**. Con il solo `IDLE`, se lo screensaver si è acceso prima
dell'inibizione, l'unica difesa che resta chiede il bit `SUSPEND`: è la forma attenuata del difetto
pagato su KDE. ⛔ **Mai il bit `LOGOUT(1)`**: ci renderebbe ostaggio dell'uscita dell'utente.

✅ **La precondizione quasi non si pone**: `Inhibit` sta sullo **stesso oggetto** di `RegisterClient`,
che REMOTIX già chiama (`src/uscita.c:180`) — se la registrazione riesce, il nome c'è.

⭐ **Due buone notizie:**

- **l'input che iniettiamo azzera davvero l'inattività** — né via D-Bus né via libei l'evento è marcato
  `SYNTHETIC` (`core/events.c:126-138`): un utente remoto che lavora tiene sveglia la sessione da sé.
  Ma un client passivo no;
- ✅ **se perdessimo la corsa, l'immagine non muore**: `PowerSaveMode` **non ferma** i fotogrammi di un
  monitor virtuale, perché le view virtuali sono offscreen. Il difetto di labwc non si ripresenta, e
  **la cura di wayvnc non serve**. Si vedrebbe però la schermata di blocco — cioè §4.

⚠ E tre trappole di configurazione: `idle-delay=0` **non** ferma la sospensione (il timer di sleep ha
un timeout proprio); `idle-delay=0` con `idle-dim=true` accende un dim a 60 s; `disable-lock-screen`
ferma `lock()` ma **non** `activate()` — la leva vera è `lock-enabled=false`.

---

## 8. La cattura, riletta nel codice

*Dettaglio: `rapporti/05-mutter-cattura.md`. Sette `[≠]`.*

### 8.1 Le correzioni a R29

| Che cosa dicevamo | Che cosa dice il codice |
|---|---|
| il DMA-BUF è un **diff** su quattro buffer riciclati | ⛔ **falso**: blit dell'intero framebuffer, stack di clip **svuotato deliberatamente**, e la vista virtuale è un `CoglOffscreen` **persistente** |
| la cura è una **superficie di accumulo** | ⛔ per questo peggiorava: copiavamo i rettangoli danneggiati da un buffer **già intero** |
| «la fence implicita è quella sbagliata» | ⚠ copre metà del contratto — l'*acquire*. Quel che manca è il **release** |
| «trattenere il buffer non serve» | ⛔ il riferimento fa **il contrario**, ed è l'unica protezione senza timeline |
| «la timeline quando c'è» | ⛔ `gnome-remote-desktop` 48.1 **non nomina mai** `SPA_META_SyncTimeline` |
| «`cattura.c` non chiede un solo `SPA_PARAM_Meta`» | ⚠ superata: oggi chiede Header e VideoDamage |

**Il contratto della timeline, per chi la scriverà**: `blocks=3`, i due `spa_data` `SyncObj` in **coda**
(stesso fd), primo `SPA_PARAM_Buffers` con `metaType` MANDATORY; e i buffer vanno alzati (Mutter ne
propone fino a 16; i nostri quattro li chiediamo noi).

### 8.2 ⭐ La cadenza: il fatto è `[M]`, ⚠ **la causa è `[R]`**. *Misurato il 13 agosto 2026, e corretto la sera stessa*

`framerate` è un **valore fisso `0/1`** — ecco perché una cadenza fissa non negozia. E il
`maxFramerate` fa **due cose insieme**: è il freno della cattura **ed è la frequenza del monitor
virtuale**.

⛔ *Questo paragrafo diceva: «Stesso numero ⇒ **battimento** ⇒ 0,61». **È sbagliato**, e la misura
della fase 3 (step 1, M3) lo smentisce in tutt'e due le metà: né il battimento né lo 0,61.*

⭐ **IL FATTO, che è `[M]` e non si tocca**: negoziando il monitor a **120 Hz** e rinegoziando la
**sola** cadenza a **90**, GNOME consegna **61,4 fotogrammi al secondo** (60,04 dalla mediana), con
intervallo mediano **16,66 ms** e p99 **20,43**. È la cella **D** di `banchi/03-b14-esiti.jsonl`.

⚠ **LA CAUSA, che è `[R]` e va detta per quello che è**: letta nel codice di Mutter, `maxFramerate`
non sembra un tetto continuo ma una **griglia** — il freno calcola
`min_interval_us = 10⁶/maxFramerate` **troncato a intero** (16666 per 60) e lo mette contro un tick
da **16666,67 µs**, e chi cade sotto **perde un tick intero**. ⭐ **Resta la spiegazione migliore che
abbiamo**, ed è **coerente con la cella D**, che è pulita. ⛔ **Ma è una lettura del codice, non una
legge misurata**, e non va scritta come se lo fosse.

> ⛔⛔ ⚠ *Qui stava scritto, e in altri otto documenti con lei: «`[M]` legge verificata su **13
> punti**: 8 la confermano, **0 la smentiscono**». **È FALSO.** Il file degli esiti della griglia —
> `banchi/03-b14-esiti-griglia.jsonl` — porta **tre righe in tutto**: il terreno e **due celle**
> (`griglia-apertura-120` e `griglia-freno-90`), e **tutt'e due portano `scena_sul_mio_monitor:
> false`** ⇒ sono **rifiutate dal banco stesso**, che sul proprio verdetto stampa «⛔ la legge NON
> regge su **0 punti su 0**». I tredici punti non stanno in nessun file di esiti. ⇒ La
> quantizzazione **torna `[R]`**. **Corretta il 13 agosto 2026**, rilievo del coordinatore della
> fase 3, verificato riga per riga sui due file di esiti.*
>
> ⭐⭐ **E la ragione del rifiuto è la trappola numero uno di `LEZIONI.md` §1.1**: *la scena deve
> stare sul monitor che si sta catturando*. Il banco **lo aveva scritto nel proprio file**, campo per
> campo, e nessuno ha guardato quel campo: si è letto il numero e non la riga accanto.

**La tabella qui sotto viene TUTTA da `banchi/03-b14-esiti.jsonl`** — sette celle, **tutte** con
`scena_sul_mio_monitor: true`, con i tre controlli (positivo: crollo a 9,57 chiedendo 10; negativo:
60→60 resta su 46,07; ritorno: 83,03, cioè torna su B) che chiudono:

| monitor | freno | consegnati | mediana | p99 | cella |
|---|---|---|---|---|---|
| 60 | 60 | 31,5 | 33,31 ms | 35,53 | **A** |
| 120 | 120 | 82,9 | 12,12 ms | 18,53 | **B** |
| 120 | 60 | 46,13 | 24,12 ms | 29,23 | **C** |
| ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61,4** (60,04) | ⭐ **16,66 ms** | 20,43 | ⭐ **D** |

⛔ **E i «sei decimi» non si riproducono**: la cella bassa dà **0,50 pulito e deterministico**, che è
quel che una griglia produce e un battimento no. ⭐ **Questa cella è pulita** — è la **A**, e regge.

> ⛔ ⚠ *E cade anche il riscontro incrociato.* Qui stava scritto: «Riscontro incrociato con una
> seconda scena indipendente: concordano **entro il 4 %**, attese **0** ovunque». ⛔ **Non regge**, e
> lo dice il file stesso, `banchi/03-b14-esiti-scena2.jsonl`: la sua **cella D** — cioè proprio il
> risultato da confermare — porta `scena_sul_mio_monitor: false`, `palco_stabile: false` e **1
> fotogramma in 25 s (0,04/s)**, e non ha nemmeno il conto delle attese, perché il suo step 2 non
> c'è. E il suo **controllo di RITORNO** dà **52,84** contro gli **80,28** della sua stessa cella B:
> **non torna**, quindi la catena dei controlli di quella scena **non chiude**. Entro il 4 %
> concordano solo la cella A (31,28 contro 31,5), la B (3,2 %) e il controllo positivo; la C sta al
> **5,4 %** e il controllo negativo al **7 %**. ⇒ ⛔ **Il 61,4 oggi ha UNA scena sola.** Corretto il
> 13 agosto 2026, stesso rilievo.

⭐ **`ensure_virtual_monitor` esce prima se la misura non cambia**, e il disaccoppiamento
**funziona**: negoziare alto (monitor 120) e rinegoziare la sola cadenza (freno 90) porta GNOME a
**61,4**, cioè quanto KWin. È costato tre celle e **zero righe di prodotto**, come previsto.

⛔⛔ **Ma il prodotto oggi non sa chiederlo, e va scritto qui**: `MOVIMENTO_FPS 60` è una costante di
compilazione (`src/figlio.c:1465`), `main.c` non ha nessuna opzione di cadenza, e **`RecordVirtual`
non prende la frequenza** (`src/mutter.h:82`) — i quattro monitor virtuali sono tutti
**1920×1080@60**. ⇒ Il risultato è `[M]` **sul banco** e **zero in produzione**.

⛔⛔ **E sulla catena vera il collo NON è `maxFramerate`: è il codificatore in software.** Misurato
il ritardo cattura → vetro (mediana **74,58 ms**, `SPECIFICHE.md` §3.2), il disegno → cattura di
Mutter pesa **16,66 ms su 74,6, cioè il 22 %**: il **78 % è nostro**, e ~39 ms stanno nel tratto
cattura → primo byte in pagina, dominato dal codificatore in software (libsvtav1 / libx265). ⇒ Il
figlio del prodotto consegna **23,93 fotogrammi/s con ZERO attese a vuoto**: **non aspetta mai
Mutter**. Alzare la cadenza della cattura non sposterebbe il ritardo.

### 8.3 Il resto

**[✗] Un fotogramma intero a richiesta non esiste** (nessuna proprietà, nessun flag, nessun parametro)
— **e non serve**, visto §8.1. **[✗] Solo `BGRx` e `BGRA`**: R32 confermata riga per riga. ⛔ **I buffer
di solo cursore stantii esistono anche su Mutter**, l'analogo esatto di `kde.md` §4.7 — già gestito nel
nostro codice dal 7 agosto.

---

## 9. L'input, riletto nel codice

*Dettaglio: `rapporti/06-mutter-input.md`. Quattro `[≠]`.*

⛔ **`EI_EVENT_KEYBOARD_MODIFIERS` non arriva nemmeno su GNOME**: `eis_device_keyboard_send_xkb_modifiers`
ha **zero occorrenze** in Mutter 48.7 (controllo positivo: 25 altre `eis_device_*` usate). La frase che
avevamo in **due** documenti — su KWin non arriva, *a differenza di GNOME* — **è falsa: sono pari**.

✅ **La fonte vera su GNOME sono due proprietà D-Bus** (`CapsLockState`/`NumLockState`) con
`SYNC_CREATE`, che danno anche lo **stato iniziale** — cosa che su labwc non abbiamo.

| Altro `[≠]` | |
|---|---|
| il `mapping-id` | **non lo dichiariamo noi**: lo genera Mutter come UUID e ce lo pubblica nei `Parameters`. Il verso è **Mutter → noi**, e `compositore_mapping_id` è invertito |
| il tasto Pausa | il riferimento pretende il flag E1: il nostro «riconoscibile anche senza» è **una scelta**, non un fatto |
| touch/RDPEI | **[✗] non esiste nella 48.1**: tre sezioni del nostro documento descrivono la **49+** |

⭐ **La rotella `/120 → ×10` è giusta, ma non per la ragione scritta**: con `scroll_delta` Mutter forza
`SOURCE_WHEEL` e **salta** l'accumulatore. La soglia reale di uno scatto è **60**, cioè mezzo. ⚠ E
`ei_device_scroll_discrete` fa una **divisione intera per 120**: i mezzi scatti spariscono.

⛔ **Due ricambi che toccano la fase 6**: un cambio di **keymap** distrugge e ricrea il dispositivo
tastiera; un cambio di **geometria** distrugge e ricrea tutti i dispositivi assoluti. Il puntatore al
device vecchio smette di funzionare **senza errore**: keymap e regioni vanno rilette **a ogni
`DEVICE_ADDED`**.

⚠ E un fallimento silenzioso da conoscere: `transform_position` che fallisce **non è un errore** — una
riga di log e il metodo D-Bus **ritorna con successo**.

---

## 10. La clipboard

*Dettaglio: `rapporti/07-clipboard-portale.md`. Sei `[≠]`.*

⛔ **La clipboard di GNOME non è della sessione RemoteDesktop.** È `MetaSelection`, cioè **del
compositore**, come su KDE e wlroots; della sessione è solo la **porta**. La riga della domanda 14 in
`LEZIONI.md` va riscritta.

| Che cosa dicevamo | Che cosa dice il codice |
|---|---|
| «chi si ricollega non riceve un annuncio, e ci è costato» | ⛔ **falso**: `EnableClipboard` con opzioni **vuote** emette subito `SelectionOwnerChanged`. Era la nostra ricetta a perderlo |
| «l'eco va distinta con un'euristica» | ✅ è **etichettata** (`session-is-owner`), e `SelectionRead` sulla propria selezione è **rifiutata**: lo stallo di KWin qui è impossibile |
| «la clipboard non sopravvive alla morte di chi ha copiato» | ⛔ **su GNOME sopravvive**: Mutter ha un **clipboard manager interno**, avviato incondizionatamente — ma **in un solo tipo MIME**, con tetti 4 MiB / 200 MiB |
| «senza sessione la clipboard non esiste» | ⛔ **la sponda X11 è incondizionata nei due versi** (zero controlli sul fuoco): `xclip` funziona senza sessione, **e il banco su GNOME può usarlo** |

**Tre trappole operative:**

1. ⛔ **`DisableClipboard` è a senso unico**, per un difetto di Mutter: il flag ha **un solo
   assegnamento in tutto il file**, a `TRUE`. Dopo il Disable, `Enable` risponde «Already enabled» e
   gli annunci non arrivano più. **Regola: non chiamarla mai** — per lasciare la clipboard si usa
   `SetSelection` senza `mime-types`;
2. ⛔ **firma asimmetrica**: `mime-types` è **`as`** in ingresso e **`(as)`** in uscita. Chi legge il
   segnale con il tipo sbagliato ottiene `NULL` **senza errore** — confermato da tre implementazioni
   indipendenti;
3. ⛔ **gnome-shell azzera la clipboard a ogni blocco schermo**: ci strappa la proprietà in silenzio.

⚠ E `POLLHUP` vale «pronto» anche qui, ma il fd di `SelectionWrite` che riceviamo è **bloccante**,
mentre quello di `SelectionRead` arriva già non bloccante.

---

## 11. Il concorrente, guardato in faccia

*Dettaglio: `rapporti/09-chi-lo-fa.md`.*

> ⭐ **`gnome-remote-desktop` è un ottimo backend RDP e un prodotto incompleto; REMOTIX è un prodotto
> più completo con un backend meno rifinito.**

**Che cosa facciamo noi che lui non fa** — e gli otto che contano stanno tutti fra «accendi una Debian
senza monitor» e «vedi un desktop»:

| | |
|---|---|
| ⭐ **avviamo la sessione** | il suo README dice che la sessione headless dev'essere *«independently set up»*. **[✗]** nessun codice che avvii un compositore |
| ⭐ **autenticazione vera** | lui impone NLA con un **file SAM fabbricato**, credenziali scollegate dall'account. **[✗] Kerberos nella 48.1 non esiste** |
| **TLS puro** | il suo rifiuto del ripiego è la causa di una fila di segnalazioni chiuse come «Not GNOME» |
| ⭐ **H.264 su GPU di serie** | ⛔ da lui la VA-API è **dietro una variabile di debug**: senza NVIDIA il percorso normale è **RemoteFX Progressive in CPU** |
| **controllo del bitrate** | lui è QP fisso a 22, nessun target |
| ⛔ **rifiuto della seconda connessione** | **[✗]** in headless 48.1 **nessuna politica**: sessioni parallele illimitate |
| **il resto** | certificato generato da noi, distinzione logout/distacco, sink audio creato dal nulla, inibizioni, più compositori, numeri propri |

**Dove è avanti lui** — quasi tutte **ore di lavoro**, non vantaggi strutturali: il **cursore**
(572 righe, cache LRU — noi non lo mandiamo affatto), i **file negli appunti** via FUSE, il
**microfono**, **AAC/Opus**, un **regolatore di latenza audio a 300 ms**, la **gestione della
sospensione degli ack**, il ridimensionamento senza rifare la cattura, il multi-monitor, la
**strumentazione** (metriche con fotogrammi saltati e un canale di telemetria che legge i tempi del
client), il **Remote Login**, e il **confezionamento**.

> ### ⛔ Una cosa da verificare nel nostro codice **subito**, non a fine studio
>
> Il client RDP può **sospendere gli ack** mandando `queueDepth == 0xFFFFFFFF`, e un regolatore che
> non lo gestisce **si ferma per sempre**. Il nostro concede `MAX(2, rtt·fps/10⁶+2)` posti: se quel
> valore viene trattato come un numero, la coda si chiude e il desktop si pianta.

⚠ **Il documento `gnome-remote-desktop.md` è scritto sulla 51.alpha**, non sulla 48.1 di Trixie: sei
sezioni sono da correggere (niente Kerberos, niente touch, niente throttler, `CURSOR_MODE_EMBEDDED`
mai usato, VA-API dietro debug, due formule di posti invece di una). ⛔ E Debian dichiara **trixie
48.1-4 vulnerabile a CVE-2025-5024**, un DoS non autenticato.

### 11.1 ⭐ L'handover di GNOME 48, che è portabile

Il socket TCP **non viene mai chiuso**: viaggia come **file descriptor su D-Bus**, e chi lo instrada
aveva letto in **`MSG_PEEK`**, quindi il destinatario rifà la negoziazione RDP da zero. Più il **Server
Redirection PDU** con routing token, che è RDP puro e FreeRDP lo espone.

**Sei cose da copiare, tutte portabili su KDE, XFCE e LXQt**: il socket per fd; `MSG_PEEK` per
instradare senza consumare; il Redirection PDU; autorizzare **per sessione logind** invece che per
polkit; `Inhibit("sleep","block")` finché c'è un client; l'autolicenziamento del greeter.

⛔ **Ma non conviene appoggiarsi al Remote Login**: significherebbe **smettere di essere il server RDP**
(lui il server, noi al massimo un client), funzionerebbe **solo su GNOME** — quindi la strada «avvio da
me» resterebbe da scrivere comunque per gli altri tre, e sarebbero **due prodotti**. Con in più un dato
di campo: l'handover **fallisce a caso in circa due avvii su tre** su Fedora 42, e sono cinque processi
in tre contesti di sicurezza sincronizzati su un timeout di 30 s.

---

## 12. La matrice, rifatta col denominatore giusto

*`lxqt.md` §4.1 contava 9 combinazioni. Erano **10**.*

**Cinnamon 6.4.10 e muffin 6.4.1 sono in Trixie** con una sessione `cinnamon-wayland.desktop`
**[R-pkg]**. ⛔ Ma muffin **rinomina il bus in `org.cinnamon.Muffin.*`** ed è un fork della linea 3.38,
a ~10 cicli da Mutter: **non è gratis né dalla fase wlroots né dal lavoro su GNOME**.

| | |
|---|---|
| combinazioni realistiche su Trixie | **10** |
| coperte oggi | **2** (20 %) |
| dopo la sola fase wlroots | **8 su 10 — 80 %** |
| la prossima che costa meno | **LXQt su labwc: zero righe** |

⭐ **Ma la cosa che costa davvero meno non è una combinazione nuova: sono le cinque voci del debito di
§1.1**, sul desktop che serviamo già.

---

## 13. Il piano di misure

⚠ **Passo zero: rimettere GNOME sul server**, che oggi non è installato.

| # | La misura | Perché |
|---|---|---|
| **M1** | ⛔ il nostro regolatore regge `queueDepth == 0xFFFFFFFF` | §11: un desktop che si pianta per sempre. Si prova con un client strumentato, non aspettando |
| **M2** | headless sì/no contro `inhibit_remote_access` | §4: è la precondizione che oggi abbiamo **per accidente** |
| ⚠ **M3** | la cadenza disaccoppiata — ⭐ **il fatto è ottenuto**, ⛔ **ma la misura è MEZZA e non è chiusa** | §8.2: `[M]` monitor 120 + freno 90 ⇒ **61,4 consegnati** (60,04), mediana **16,66 ms** — cella **D**, pulita, con i tre controlli che chiudono. ⛔ **Ma la causa è `[R]`, non `[M]`**: la «legge della griglia» su 13 punti **non esiste** (vedi il riquadro di §8.2), e ⛔ **il riscontro su una seconda scena non c'è**: la cella D di `03-b14-esiti-scena2.jsonl` è rifiutata dal banco. ⚠ **Non attuabile dal prodotto oggi** (`RecordVirtual` non prende la frequenza), e ⛔ **non è la cura del ritardo**: sulla catena vera il collo è il codificatore in software |
| **M4** | `SPA_META_SyncTimeline` con acquire/release, **oppure** trattenere il `pw_buffer` | §8.1: è la caccia della fase 9 nel posto giusto |
| **M5** | `SPA_META_Cursor` + `cursor-mode=2` → cursore RDP nativo | §5.2: oggi il puntatore non arriva da nessuna parte |
| **M6** | il profilo dconf in `$XDG_RUNTIME_DIR` con i lock, e **ogni chiave riletta** | §6: paga §1.1 punti 3, 4 e 5 insieme |
| **M7** | `Inhibit(…, 12)` regge 20 minuti, e la macchina non si sospende | §7 |
| **M8** | la clipboard: annuncio alla riconnessione, e il blocco schermo che la azzera | §10 |
| **M9** | prova **guasta di proposito**: `SHELL` non vuota, e `--virtual-monitor` assente | ⭐ imparare come si legge il guasto: sessione **viva, completa e nera** |

> ### ⚠ M3 — **lo stato vero**, scritto il 13 agosto 2026 dopo il rilievo
>
> *Stamattina questa riga diceva **✅ CHIUSA il 13 agosto 2026**, e lo diceva **sulla base della
> griglia**. La griglia è caduta — le sue due celle sono rifiutate dal banco stesso, §8.2. ⇒ **M3 non
> è chiusa e non è aperta: è mezza**, e va tenuta mezza finché non si fanno le due metà che mancano.
> ⛔ Non la si forza a «chiusa» perché il numero è bello, né ad «aperta» perché una riga era falsa.*
>
> | | |
> |---|---|
> | ✅ **quel che M3 HA ottenuto** | `[M]` **61,4** a monitor 120 e freno 90 — cella **D** di `banchi/03-b14-esiti.jsonl`, `scena_sul_mio_monitor: true`, con controllo positivo (crollo a 9,57), negativo (fermo su 46,07) e di ritorno (83,03) che chiudono. **Questo è un fatto, e resta** |
> | ⛔ **quel che M3 NON ha** | la **causa**. La quantizzazione è `[R]`: letta nel codice di Mutter, coerente con la cella D, **mai misurata su una griglia di punti** |
> | ⛔ **e nemmeno** | il **riscontro su una seconda scena**: la cella D di `banchi/03-b14-esiti-scena2.jsonl` porta `scena_sul_mio_monitor: false` e **1 fotogramma in 25 s** ⇒ il 61,4 ha **una scena sola** |
> | ⇒ **che cosa la chiuderebbe** | rifare la **griglia** con la scena sul monitor che si cattura, e rifare la **cella D** sulla seconda scena. È lo stesso banco `banchi/03-b14-cadenza.py`, e ⭐ **il campo per accorgersene ce l'ha già**: è `scena_sul_mio_monitor`, e stamattina nessuno l'ha guardato |

---

## 14. Le lezioni che questo studio aggiunge

1. ⭐ **La domanda 16**: *«c'è uno stato in cui il compositore ci REVOCA quel che ci ha già concesso, e
   chi ha il dito su quel pulsante?»* La domanda 3 chiede se esiste un permesso; questa chiede se può
   essere **ritirato a caldo**. Su GNOME esiste un'API che *«termina ogni sessione di accesso remoto
   attiva»*, e nessuna delle quindici domande la copriva.
2. ⛔ **Il desktop che serviamo meglio è quello che abbiamo studiato peggio.** Dieci fasi su GNOME
   hanno prodotto una conoscenza profonda della *cattura* e nessuna del *desktop*: sette voci mai
   affrontate, e due di esse (§4 e §7) sono difetti che l'utente incontrerebbe **lasciando la sessione
   ferma venti minuti**.
3. ⭐ **Una condizione che ci salva per accidente va scritta come requisito.** Siamo headless perché
   Mutter si degrada da sé senza seat, non perché l'abbiamo chiesto — e da quella condizione dipende
   il fatto che un blocco schermo non ci stacchi. È la forma generale di `LEZIONI.md` §2.5: *la
   protezione di un difetto noto non si affida a qualcosa che si può perdere.*
4. ⚠ **Le misure invecchiano peggio delle letture.** R29 è stata scritta da misure corrette e da una
   **diagnosi sbagliata**, ed è rimasta in piedi due fasi perché nessuno aveva letto il codice che le
   stava sotto. La lezione §1.9 diceva «quando codice e misura si contraddicono, sospetta la misura»;
   questo studio aggiunge il caso opposto — **una misura giusta con una spiegazione inventata è più
   pericolosa di una misura sbagliata**, perché nessuno la rimette in discussione.
