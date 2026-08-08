# KDE Plasma e KWin — studio del codice, per la fase 11

*Analisi condotta sul codice sorgente originale di KDE, clonato da `invent.kde.org` il 7 agosto 2026
e tenuto in `reference-kde/`, con la stessa convenzione di `reference/xrdp`.*

| Repository | Versione clonata | Perché |
|---|---|---|
| `plasma/kwin` | tag **v6.3.6** | il compositore: è **lui** che possiede schermo e input |
| `plasma/plasma-workspace` | tag **v6.3.6** | la sessione: avvio, logout, ksmserver, klipper |
| `plasma/kpipewire` | tag **v6.3.6** | consuma PipeWire e **codifica in H.264**: fa il nostro stesso lavoro |
| `plasma/xdg-desktop-portal-kde` | tag **v6.3.6** | la via «ufficiale» alla cattura, e il consenso |
| `plasma/libkscreen` | tag **v6.3.6** | configurazione degli schermi da fuori |
| `plasma/powerdevil` | tag **v6.3.6** | energia, inibizioni, spegnimento |
| **`plasma/krdp`** | tag **v6.3.6** *e* master `1dd52ba` (6.7.80) | ⭐ **il server RDP di KDE**: stessa libreria RDP, stesso compositore, stessi client. **È il riferimento principale della fase**, l'equivalente di `gnome-remote-desktop` |
| `network/krfb` | master `6b2832b` (KDE Gear 26.11.70) | il desktop remoto VNC di KDE |
| `libraries/plasma-wayland-protocols` | master | gli XML dei protocolli di KDE |

**6.3.6 è la versione di Debian Trixie** (§3.8 di `SPECIFICA.md`), cioè quella che gira sulla
macchina di runtime: le righe citate qui sono quelle che l'utente ha davvero installate.

Insieme ai sorgenti di KDE è stato riletto **il nostro codice di banco** — `banco/nodo-kwin.c` (il
client del protocollo di KWin), `banco/misura-cattura.c` (il consumatore PipeWire),
`banco/banco-altri.sh`, `banco/zkde-screencast-unstable-v1.xml` — perché metà del valore di questo
studio sta nel confronto fra quel che KDE fa e quel che noi abbiamo già scritto.

Ogni affermazione porta una marca, come in `REFERENCE.md`:

| Marca | Significato |
|---|---|
| **[R]** | **letto nel codice**, con `file:riga`. È il grosso di questo documento |
| **[M]** | misurato da noi, sul campo, con data |
| **[?]** | **non deciso dal codice**: va misurato sul banco. Le `[?]` sono elencate in §14 |
| **[✗]** | **cercato e non trovato**: una dichiarazione negativa, che vale quanto una positiva |

> ⚠ **Questo documento è di lettura, non di misura.** `LEZIONI.md` §1 dice che il progetto non si è
> mai fermato su un problema difficile ma su una misura che non misurava quel che credevamo: qui non
> c'è nessuna misura nuova, e nemmeno una riga eseguita. Quel che c'è è il codice, che dice **che cosa
> è possibile** — e in tre punti dice che **una nostra misura del 7 agosto guardava la cosa sbagliata**
> (§5.1 e §15). Prima di spostare un numero nei documenti si rifà la misura.

---

## 1. In due minuti

Le **quattro domande** che `PIANO.md` fase 11 e la memoria di progetto chiedevano di chiudere prima
di progettare qualunque cosa, con la risposta che il codice dà:

| # | La domanda | La risposta |
|---|---|---|
| **1** | **Come si ottiene il permesso della cattura, per un servizio non presidiato?** | ✅ **Un file `.desktop` con `X-KDE-Wayland-Interfaces`.** Nessun dialogo, nemmeno la prima volta; sopravvive a riavvio e logout; nessuna patch. È il meccanismo con cui si autorizzano il portale di KDE e `krfb-virtualmonitor` (§3). ✅ **MISURATO il 7 agosto — funziona**, e con un requisito in più che il codice non mostrava: **`XDG_MENU_PREFIX=plasma-`** nell'ambiente, o l'indice dei servizi resta vuoto e il cancello non si apre (§3.3-bis) |
| **2** | **KWin senza monitor può disegnare sulla GPU?** | ✅ **Sì**, e ora **misurato**, non solo letto: `renderD129` aperto, `libEGL_mesa`+`libgbm` caricate, `zwp_linux_dmabuf_v1` v4 annunciato. **La nostra misura del 7 agosto («zero nodi DRM, nessuna libreria GL») era sbagliata nell'etichetta: R32 va corretta** (§5.1) |
| **3** | **Come si avvia una sessione Plasma senza monitor?** | ✅ Ambiente da zero con **due** variabili obbligatorie (**più `XDG_MENU_PREFIX`, vedi la domanda 1**), unità del compositore sovrascritta, `startplasma-wayland`. Più semplice di GNOME. Con **due vincoli duri**: `--xwayland` non è opzionale, e `--virtual` non sa creare output a richiesta (§6). ⛔ **E `--virtual` non è più una scelta**: `--drm` da una sessione senza seat non parte [M] (§5.2) |
| **4** | **Per quale strada passa l'input?** | ✅ **libei**, con una sola chiamata D-Bus a KWin e **senza alcun controllo di permesso**. `SPECIFICA.md` §3.8 («protocollo `kde-fake-input`») è superata dal codice: `fake_input` è la strada vecchia (§7). ✅ **MISURATO**: `connectToEIS(7)` da una shell SSH qualunque → `(handle 0, 1)` |

E le **undici domande al compositore nuovo** di `LEZIONI.md` §3, con la colonna di KWin riempita
da questo studio. Le celle marcate `[?]` sono quelle che il codice non decide.

| # | La domanda | Mutter 48.7 | **KWin 6.3.6** |
|---|---|---|---|
| 1 | Come si chiede la cattura senza portale? | D-Bus `org.gnome.Mutter.ScreenCast` | protocollo Wayland `zkde_screencast_unstable_v1` **v5** [R] |
| 2 | Spinge i fotogrammi o li fa tirare? | spinge (PipeWire) | **spinge** (PipeWire), e frena lui sul `maxFramerate` [R] |
| 3 | Il protocollo è dietro un permesso? | no | **sì**, e il permesso è **un campo di un file `.desktop`** [R] — **+ `XDG_MENU_PREFIX`** [M, 7 ago] |
| 4 | Senza monitor, disegna sulla GPU? | sì | **sì** [R] **e misurato** [M, 7 ago]: render node aperto, EGL/gbm, dmabuf v4 |
| 5 | Si può chiedere uno schermo virtuale della misura voluta? | sì, `RecordVirtual` | **sì**, `stream_virtual_output` — ma **solo col backend `--drm`** [R] |
| 6 | Quanto consegna, con una scena che cambia a ogni ridisegno? | ~37 su 60 | **59–60** [M, 7 agosto] — misurato però con `--virtual` + `stream_output`, non nella configurazione del prodotto |
| 7 | La cadenza dichiarata come si comporta? | sei decimi, oltre 60 non sale, **fissa rifiutata** | `framerate` **deve** essere `0/1`; il tetto è `maxFramerate`, **onorato lato server** con aritmetica intera in ms [R] |
| 8 | Consegna fotogrammi interi o «diff»? | **a copia zero è un diff** | **interi, sempre** [R] — il difetto di R29 non si ripresenta |
| 9 | Il buffer arriva già disegnato? | **no**: il 100 % col disegno in corso | **sì**: KWin fa `glFlush()`, o `glFinish()` su NVidia e llvmpipe [R] |
| 10 | Che cosa costa la risoluzione? | niente fino a 4K | niente [M] |
| 11 | Che cosa costa la profondità di colore? | niente | niente; `BGRx` è negoziabile [R] |

> ### ⭐ E su KDE **esiste un `gnome-remote-desktop`**: si chiama `KRdp`
>
> *Trovato la sera del 7 agosto, dopo una domanda dell'utente. La prima stesura di questo documento
> diceva che in KDE non c'era traccia di RDP, e sbagliava (§12.0).*
>
> Server RDP di KDE, **C++ su FreeRDP + kpipewire**, 4 222 righe nella versione di Trixie. Conferma
> per intero la risposta alla domanda 1 — il suo `.desktop` dichiara
> `X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input,zkde_screencast_unstable_v1` — e conferma **i due
> codec**, **il regolatore a fotogrammi in volo dall'RTT**, **i bordi esclusivi delle regioni** e
> **TLS puro quando si autentica con PAM**. Non risolve invece le due cose che restano nostre:
> **non avvia la sessione** (vive dentro Plasma) e **non ridimensiona lo schermo virtuale**.
>
> ⛔ **E `xrdp` non c'entra**: non ha alcun percorso Wayland — lancia un `Xorg` o un `Xvnc` e dentro
> ci fa girare la sessione **X11** di Plasma (§12.3). Non ha risolto il nostro problema: l'ha evitato.

**Il quadro in una riga**: su KDE la cattura è **più semplice e più sana** che su GNOME (fotogrammi
interi, sincronizzazione fatta dal compositore), l'input è **più corto** (una chiamata D-Bus,
nessun permesso), la sessione è **più prevedibile** (nessun `ConditionEnvironment`, il bus non muore)
— e in cambio **la risoluzione dinamica non c'è**: un output virtuale di KWin non si ridimensiona, e
va chiuso e rifatto (§8).

> ### ⛔ «CURSORE FUORI DAL PERCORSO DEL CODIFICATORE» ERA SCRITTO QUI, ED È FALSO CON `--virtual`
>
> *[M, 8 agosto 2026, e l'ha visto l'utente al primo uso: «non c'è la scia, ma è quello di KDE che
> segue quello vero» — cioè **due puntatori**.]*
>
> Il modo cursore `Metadata` governa se lo screencast **aggiunge** un cursore, non se la scena ne
> contiene già uno. E con il backend `--virtual` ne contiene sempre uno:
>
> | | |
> |---|---|
> | `compositor_wayland.cpp:573-608` | se il backend non ha un piano cursore, `hardwareCursor` resta falso e il **cursorLayer software** viene reso visibile |
> | `backends/virtual/` | ⛔ **non definisce `cursorLayer()`** [✗]: il backend virtuale un piano cursore non ce l'ha |
> | `virtual_egl_backend.cpp:187-194` | `textureForOutput` restituisce il **framebuffer dell'uscita**, cioè quello in cui il cursorLayer è stato dipinto |
> | `pointer_input.cpp:99-108` | e KWin lo mostra appena esiste un dispositivo di puntamento sul seat — il nostro, di libei |
>
> **Non c'è alcuna leva per impedirlo**: `Cursors::hideCursor()` è interna e la chiamano solo
> `pointer_input` e `hide_cursor_spy`; nessun protocollo, nessun D-Bus. Chiedere il modo `Hidden` non
> cambierebbe niente. Con il backend `--drm` — che §5.2 ha escluso — ci sarebbe un piano cursore e il
> problema non esisterebbe.
>
> ✅ **L'unica cura è dall'altra parte**: si dice al **client** di nascondere il proprio puntatore,
> con `SYSPTR_NULL`, che è RDP di base. Il prezzo è che il puntatore si muove alla latenza del
> **video** invece che a quella della rete — su una LAN è un fotogramma.
>
> ⚠ **E su Mutter NON si fa**: là il cursore è davvero fuori dall'immagine, e nascondere quello del
> client lascerebbe l'utente senza alcun puntatore. È una differenza fra compositori, non una
> preferenza.
>
> ### ⛔ E la cura funziona su due client su tre — non su tutti
>
> *[M, 8 agosto 2026, giudizio dell'utente su xfreerdp e su RDM]*
>
> | client | esito |
> |---|---|
> | **xfreerdp** | ✅ un puntatore solo, quello di KDE |
> | **RDM (Android)** | ⛔ **restano due**, pur avendo il server dichiarato e il client **accettato** il PDU (`14:02:28 puntatore del client nascosto`, cioè `PointerSystem()` ha risposto vero) |
>
> La spiegazione è che il secondo puntatore di RDM **non è il puntatore RDP**: è il *touch pointer*
> che l'applicazione disegna sopra la propria finestra per rendere usabile un desktop col dito.
> Vive fuori dal protocollo, e **nessun server può toglierlo** — si spegne solo dalle impostazioni
> del client, passando alla modalità mouse.
>
> ⚠ Da cui la regola generale: `SYSPTR_NULL` toglie il puntatore che il client disegna **per conto
> del protocollo**, non ogni pixel a forma di freccia. È l'ennesima forma della regola dei tre
> client (`LEZIONI.md` §2.1): la stessa riga di codice dà tre esiti.
>
> ### ⭐ E allora la cura giusta è l'opposta: il cursore di KDE si rende TRASPARENTE
>
> *[M, 8 agosto 2026, dopo che l'utente ha chiesto di chiudere il punto sul serio]*
>
> Il ragionamento di sopra è giusto e la conclusione era corta. Vero che con `--virtual` KWin
> disegna il cursore dentro l'immagine e che non c'è leva per impedirglielo — **ma non serve
> impedirglielo: basta che quel che disegna non si veda.**
>
> KWin prende il tema del cursore da **`XCURSOR_THEME`, e lo guarda solo se c'è anche
> `XCURSOR_SIZE`** (`cursor.cpp:134-145`: `if (!themeName.isEmpty() && ok)`). L'ambiente della
> sessione lo componiamo noi. Quindi: un tema con un cursore **1×1 ad alfa zero**, scritto in
> `$XDG_RUNTIME_DIR/remotix/icons/` e indicato con `XCURSOR_PATH`, e il puntatore torna a essere
> **quello che il client disegna da sé — come su Mutter**, alla latenza della rete invece che del
> video, e **uno solo su ogni client**, compresi quelli che se lo disegnano per conto proprio.
>
> ✅ **Misurato**: `XCURSOR_THEME=remotix-invisibile`, `XCURSOR_SIZE=24` e `XCURSOR_PATH` presenti
> nell'ambiente di `kwin_wayland` (letto da `/proc/<pid>/environ` con `sudo`, §del binario non
> dumpable), **68 forme scritte**, file `Xcur v1.0 1×1 alfa 0` di 68 byte, e **nessuna riga
> «Failed to load cursor theme»** nel journal dell'unità del compositore.
>
> ⛔ **Il tema deve caricarsi davvero.** Se `CursorTheme` risulta vuoto KWin **ripiega sul tema
> predefinito** (`pointer_input.cpp:1183-1196`), cioè sul cursore visibile: un tema con zero forme
> non nasconde niente, lo *rimette*. Per questo le forme si scrivono tutte, e per questo il controllo
> che vale è l'assenza del ripiego, non la presenza dei file.
>
> ⚠ **Il prezzo**: si perde il cambio di forma — la I sul testo, le frecce di ridimensionamento —
> esattamente come su GNOME oggi. Restituirlo significa mandare la forma vera sul **canale puntatore
> di RDP**, prendendola dai metadati PipeWire che già chiediamo (modo `Metadata`): è un lavoro a sé,
> e vale per tutti e due i compositori.
>
> Da cui `compositore_cursore_nell_immagine()` **è tornata falsa anche su KWin**, e `SYSPTR_NULL`
> non si manda più. La funzione resta scritta: il giorno in cui un compositore disegnasse il cursore
> nell'immagine **senza** lasciarci cambiare il tema, la risposta è lì e non va ritrovata da capo.

---

## 2. La mappa: dove sta ciascuna cosa

| Che cosa | Dove, in `reference-kde/` |
|---|---|
| Il protocollo di cattura, lato Wayland | `kwin/src/wayland/screencast_v1.{h,cpp}` — solo segnali Qt |
| Il motore della cattura | `kwin/src/plugins/screencast/` — `screencastmanager.cpp`, `screencaststream.cpp` (1000 righe), `outputscreencastsource.cpp`, `regionscreencastsource.cpp`, `screencastbuffer.cpp` |
| Il filtro dei permessi | `kwin/src/wayland_server.cpp:127-193`, `kwin/src/utils/serviceutils.h`, `kwin/src/utils/executable_path_proc.cpp` |
| L'input moderno (libei) | `kwin/src/plugins/eis/` — `eisbackend.cpp`, `eiscontext.cpp`, `eisdevice.cpp` (1829 righe) |
| L'input vecchio | `kwin/src/backends/fakeinput/fakeinputbackend.cpp` |
| I backend di uscita | `kwin/src/backends/{drm,virtual,wayland,x11}/` |
| Gli output e la loro configurazione | `kwin/src/core/output.{h,cpp}`, `kwin/src/wayland/outputmanagement_v2.cpp`, `kwin/src/core/outputconfigurationstore.cpp` |
| Gli appunti | `kwin/src/wayland/datacontrol*_v1.cpp`, `kwin/src/wayland/seat.cpp`, `kwin/src/xwayland/clipboard.cpp`, `plasma-workspace/klipper/` |
| L'avvio della sessione | `plasma-workspace/startkde/startplasma{,-wayland}.cpp`, `startkde/systemd/*.target`, `kwin/plasma-kwin_wayland.service.in`, `kwin/src/helpers/wayland_wrapper/kwin_wrapper.cpp` |
| Il logout | `plasma-workspace/startkde/plasma-shutdown/shutdown.cpp`, `plasma-workspace/ksmserver/{logout,server}.cpp`, `kwin/src/sm.cpp` |
| Energia e inibizioni | `powerdevil/daemon/powerdevilpolicyagent.cpp`, `powerdevil/daemon/powerdevilsettingsdefaults.cpp` |
| Il consumatore PipeWire di KDE, con encoder | `kpipewire/src/` — `pipewiresourcestream.cpp`, `pipewireproduce.cpp`, `h264vaapiencoder.cpp`, `vaapiutils.cpp` |
| Il desktop remoto di KDE | `krfb/framebuffers/pipewire/pw_framebuffer.cpp`, `krfb/events/xdp/xdpevents.cpp` |

---

## 3. ⛔ Il cancello: come KWin decide chi può catturare

È la risposta alla **prima** domanda della fase, e conviene metterla prima di tutto il resto perché
condiziona ogni prova: **finché il cancello è chiuso, il sintomo è «questo compositore non espone il
protocollo», e non arriva alcun errore.**

### 3.1 Il meccanismo, per intero

**[R]** KWin installa un filtro globale di libwayland — `wl_display_set_global_filter`
(`kwin/src/wayland/filtered_display.cpp:44`) — e `KWinDisplay::allowInterface()`
(`kwin/src/wayland_server.cpp:146-192`) nega il bind di **sei** interfacce a chi non le dichiara.
La lista nera, `wayland_server.cpp:129-136`:

```cpp
const QSet<QByteArray> interfacesBlackList = {
    QByteArrayLiteral("org_kde_plasma_window_management"),
    QByteArrayLiteral("org_kde_kwin_fake_input"),
    QByteArrayLiteral("org_kde_kwin_keystate"),
    QByteArrayLiteral("zkde_screencast_unstable_v1"),      // ← la cattura
    QByteArrayLiteral("org_kde_plasma_activation_feedback"),
    QByteArrayLiteral("kde_lockscreen_overlay_v1"),
};
```

Se il filtro nega, **il global non viene nemmeno annunciato nel registry**: il client vede un
compositore senza quel protocollo. Il diagnostico esiste ma è `qCDebug`, spento per difetto
(`wayland_server.cpp:184`).

Il criterio **non** è uid, non è pid, non è polkit, non è un elenco in `kwinrc`. È una catena di
tre passi, tutti **[R]**:

1. `SO_PEERCRED` sul socket del client → pid;
2. pid → `/proc/<pid>/exe`, risolto canonicamente (`kwin/src/utils/executable_path_proc.cpp:11-14`);
3. si cercano **tutte** le applicazioni installate e si prende quella il cui **primo token di
   `Exec=`**, canonicalizzato, coincide con quel percorso (`kwin/src/utils/serviceutils.h:27-49`,
   via `KApplicationTrader::query`); di quella si legge il campo
   **`X-KDE-Wayland-Interfaces`** (`serviceutils.h:24`).

Autorizzato **solo** se quel campo contiene il nome esatto dell'interfaccia.

Le due scorciatoie: il client è KWin stesso (`client->processId() == getpid()`,
`wayland_server.cpp:152`), oppure `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` **nell'ambiente di KWin**
(`:168`, letta in una `static`), che apre **tutte e sei** le interfacce a **tutti** i client.

### 3.2 I precedenti, cioè il modello da copiare

**[R]** Tutti nel sistema reale, tutti con lo stesso meccanismo:

| File `.desktop` | Interfacce dichiarate |
|---|---|
| `xdg-desktop-portal-kde/data/org.freedesktop.impl.portal.desktop.kde.desktop.in:49-51` | `org_kde_kwin_fake_input,org_kde_plasma_window_management,zkde_screencast_unstable_v1` |
| **`krfb/krfb/org.kde.krfb.virtualmonitor.desktop.cmake:84`** | `zkde_screencast_unstable_v1`, con `NoDisplay=true` — **è il nostro caso identico** |
| `plasma-workspace/shell/org.kde.plasmashell.desktop.cmake:76` | `…,zkde_screencast_unstable_v1,…` |
| `kpipewire/tests/org.kde.kpipewireheadlesstest.desktop.cmake:6` | `zkde_screencast_unstable_v1` |

E il messaggio che kpipewire stampa a se stesso quando il global manca dice esattamente dove
guardare: *«Remember requesting the interface on your desktop file:
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1»*
(`kpipewire/tests/screencasting.cpp:79`, `plasma-workspace/libtaskmanager/screencasting.cpp:44`).

### 3.3 I tre punti fragili, tutti di confezionamento

1. ⛔ **REMOTIX non deve girare come root.** `/proc/<pid>/exe` di un processo di **altro uid** non è
   leggibile, `executablePath()` torna vuoto, e `wayland_server.cpp:170-173` **nega**. Va eseguito
   come servizio dell'utente — che è comunque quel che §3.4 di `SPECIFICA.md` prescrive.
2. ⛔ **`Exec=` deve nominare l'eseguibile che apre il socket**, non un lanciatore di shell: il
   confronto è sul percorso canonico del binario vero.
3. ✅ **`kbuildsycoca6` non serve, e non serve riavviare KWin.** [R, `kf6-kservice 6.13.0-1`, la
   versione di Trixie] `ensureCacheValid()` ricostruisce la cache **dentro il processo di KWin**, con
   un limite di frequenza di **1 500 ms** (`ksycoca_ms_between_checks`). Quindi un `.desktop`
   installato è visibile entro un secondo e mezzo — e *Sunshine*, che se lo scrive a runtime, aspetta
   **3 000 ms** per prudenza (§12.4).
4. ⛔ **Il quarto punto fragile, e rompe tutto in silenzio**: `serviceutils.h:35` prende
   `servicesFound.first()`, e il bug KDE **446628** (confermato dal 2021) mostra che **un `.desktop`
   d'utente omonimo ombreggia quello di sistema** — se quello che vince non ha il campo, il permesso
   è negato senza un errore. E contano gli `XDG_DATA_DIRS` **di KWin**, non i nostri: la §6.1
   prescrive di comporre l'ambiente da zero, quindi il file va installato dove **il compositore**
   guarda.

### 3.3-bis ⭐ MISURATO — il cancello si apre, ma dipende da `XDG_MENU_PREFIX`

> **[M] Misura M1, banco del 7 agosto 2026, KWin 6.3.6-1 e kf6-kservice 6.13.0-1.**
>
> **Il meccanismo di §3.1 funziona**: con un `.desktop` che dichiara
> `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1` e `NoDisplay=true` — la forma di KRdp e di
> krfb — KWin annuncia il global e la cattura parte. Nessun dialogo, nessun portale, come previsto.
>
> **Ma prima di funzionare ha negato per cinque volte, e la causa non è nulla di ciò che §3.3
> elenca.** Il diniego era questo, e il documento va letto con questa aggiunta:
>
> ⛔ **`kbuildsycoca6` non indicizza nulla se `XDG_MENU_PREFIX` non è impostata.** L'indice dei
> servizi si costruisce a partire da `${XDG_MENU_PREFIX}applications.menu`, e Debian **non installa
> `/etc/xdg/menus/applications.menu`**: installa `plasma-applications.menu` e
> `kf5-applications.menu`. Senza il prefisso, `kbuildsycoca6` esce con **stato 0** dicendo soltanto
> `"applications.menu" not found in QList("/etc/xdg/menus")`, e `KApplicationTrader::query` non
> trova **nessuna** applicazione — nemmeno le 133 di sistema.
>
> La prova, nella dimensione della cache: **226 275 byte** senza il prefisso, **379 292** con
> `XDG_MENU_PREFIX=plasma-`. E il verdetto di KWin passa da
>
> ```
> KWIN_UTILS: Could not find the desktop file for "…/nodo-kwin"
> kwin_core:  Interface "zkde_screencast_unstable_v1" not in X-KDE-Wayland-Interfaces of "…/nodo-kwin"
> ```
> a
> ```
> KWIN_UTILS: Interfaces found for "…/nodo-kwin" "X-KDE-Wayland-Interfaces" : QList("zkde_screencast_unstable_v1")
> ```
>
> ✅ **In una sessione Plasma vera il problema non si vede**, perché `startplasma` imposta la
> variabile da sé: `qputenv("XDG_MENU_PREFIX", "plasma-")`
> (`plasma-workspace/startkde/startplasma.cpp:366`). **Riguarda noi** perché §6.1 prescrive di
> comporre l'ambiente da zero: se la componiamo senza quella variabile, il cancello resta chiuso e
> il sintomo è quello di §3 — «il compositore non espone il protocollo».
>
> ⛔ **E c'è una fragilità che va scritta**: il nome del file di cache **non** dipende dal prefisso
> (`ksycoca6_<locale>_<hash>`, e l'hash è lo stesso nei due casi). Quindi un qualunque processo che
> ricostruisca l'indice **senza** il prefisso sovrascrive quello buono, e il permesso torna a essere
> negato **a KWin già avviato** — un guasto intermittente, senza messaggi. Chi confeziona il
> servizio esporta `XDG_MENU_PREFIX=plasma-` nell'ambiente di **tutto** l'albero della sessione.
>
> **Come si diagnostica in tre secondi**, che è la cosa da ricordare: la riga che dice la causa sta
> nella categoria **`KWIN_UTILS`**, non in `kwin_core` (`kwin/src/utils/serviceutils.h:40,46`), e si
> accende con `QT_LOGGING_RULES='KWIN_UTILS.debug=true'`. Le due righe hanno cure opposte:
> *«Could not find the desktop file»* = l'indice non associa (questo caso); *«Interfaces found … :
> ()»* = associa, e manca il campo.
>
> Altri due fatti misurati, che escludono le spiegazioni comode: il diniego era identico per un
> cliente in **`/usr/bin`** (`wayland-info`) e per il nostro su `/media` — quindi **non** era il
> montaggio, e **non** era `NoDisplay`, né le virgolette in `Exec`, né un argomento in `Exec`: tutte
> e cinque le varianti negate, tutte con la stessa riga.

> ### ✅✅ E il cancello si apre anche DENTRO una sessione Plasma vera
>
> **[M] 8 agosto 2026.** La prova di §3.3-bis era su un `kwin_wayland` nudo. Ripetuta dentro una
> sessione avviata con `startplasma-wayland` (la ricetta di §6.1), con lo stesso `.desktop`:
>
> ```
> KWIN_UTILS: Interfaces found for "…/nodo-kwin" "X-KDE-Wayland-Interfaces" : QList("zkde_screencast_unstable_v1")
> ⇒ zkde_screencast annunciato, e un flusso vero: nodo PipeWire 55
> ```
>
> Quindi la catena intera — sessione Plasma, permesso, cattura, flusso PipeWire — **è verificata sul
> campo**. Nella stessa sessione KWin scrive 13 righe `Interfaces found for …`, fra cui quelle del
> portale di KDE con le sue tre interfacce: cioè si vede il meccanismo funzionare anche per gli altri.
>
> ⛔ **MA una cosa lo rompe, e va scritta perché la si incontra proprio confezionando il servizio:
> `InaccessiblePaths=` nell'unità del compositore chiude il cancello.** Serviva a scegliere la GPU
> (§5.6) e ha questo effetto collaterale: con quella riga il global **non** viene annunciato, e KWin
> **non arriva nemmeno a interrogare l'indice** — **0 righe `KWIN_UTILS` contro 13** nello stesso
> ambiente. Non è la visibilità dei file: dentro il namespace, `nsenter` mostra il `.desktop` e la
> cache `ksycoca6_en_…` presenti e leggibili; e non è `/proc`, che è montato normalmente e mostra gli
> altri processi. Il meccanismo esatto **non è stato dimostrato** (l'ipotesi residua è la prima
> condizione di `allowInterface()`: `executablePath()` vuoto ⇒ nega, `wayland_server.cpp:170-173`).
>
> **La regola che ne segue è comunque netta**: l'unità del compositore **non si irrigidisce con
> namespace di monti** (`InaccessiblePaths`, e per prudenza tutto ciò che implica `PrivateMounts`).
> Quel che serve si ottiene altrimenti — per la GPU, coi permessi del nodo (§5.6).

### 3.4 Chi è protetto e chi non lo è — la tabella che conta

**[R]** Il modello dei permessi di KWin 6.3.6 è **incompleto**, e per noi è una fortuna. Riassunto
per tutto ciò che ci serve:

| Ci serve per | Interfaccia / oggetto | Protetto? |
|---|---|---|
| cattura + output virtuale | `zkde_screencast_unstable_v1` | **sì** — `.desktop` con `X-KDE-Wayland-Interfaces` |
| **input** | `org.kde.KWin.EIS.RemoteDesktop` (D-Bus) | **NO, nessun controllo** (`kwin/src/plugins/eis/eisbackend.cpp:70`, `ExportAllInvokables`) |
| input, strada vecchia | `org_kde_kwin_fake_input` | **sì**, stessa via `.desktop` — e il suo `authenticate` non autentica nulla (`fakeinputbackend.cpp:107-113`, `// TODO: make secure`) |
| **appunti** | `zwlr_data_control_manager_v1` | **NO** (`wayland_server.cpp:386`, non in lista nera) |
| leggere/scrivere il layout schermi | `kde_output_device_v2`, `kde_output_management_v2` | **NO** |
| stato dei tasti a scatto | `org_kde_kwin_keystate` | **sì**, stessa via `.desktop` |
| catture singole | `org.kde.KWin.ScreenShot2` | **sì**, via `X-KDE-DBUS-Restricted-Interfaces` (`screenshotdbusinterface2.cpp:331-355`) — **unico oggetto D-Bus protetto in tutto KWin** |

**Da cui la ricetta di confezionamento**: un solo `.desktop`, che dichiara
`zkde_screencast_unstable_v1` (per la cattura) e — se e quando serviranno — `org_kde_kwin_keystate`
e `org_kde_kwin_fake_input`. L'input via EIS non ne ha bisogno.

> ⚠ **Un buco che non useremo, ma che dice com'è fatto il modello.** [R]
> `wp_security_context_manager_v1` **non è in lista nera** (`wayland_server.cpp:378`): un client
> qualunque può dichiarare come `app_id` il nome del `.desktop` di qualcun altro e riconnettersi
> ottenendo l'autorizzazione (`wayland_server.cpp:121-127` + `display.cpp:282-297`, e
> `serviceutils.h:51-58` che per i client in sandbox usa `KService::serviceByDesktopName`).
> Il modello è **dichiarativo**, non impositivo. La variante *legittima* di questa via — dichiarare
> il **proprio** app-id — è l'unica scappatoia se un giorno il vincolo su `Exec=` ci fosse scomodo.

### 3.5 Le vie che NON prendiamo, e perché va scritto

| Via | Esito |
|---|---|
| **Il portale con `restore_token`** | implementato (`xdg-desktop-portal-kde/src/screencast.cpp:222-279`), ma **il primo consenso è un dialogo modale** (`:272`), il token identifica il monitor per **posizione** (`outputsmodel.cpp:93-94`) e se non risolve **ricompare il dialogo**. Per un servizio non presidiato: **no** |
| **La «mega-autorizzazione» di KDE** | esiste e è documentata nel commento: *«Particularly useful for headless setups and when the user is not physically at the machine»* (`xdg-desktop-portal-kde/src/remotedesktop.cpp:34-71`, usata a `:227` per **saltare del tutto il dialogo**). ✅ **E si scrive**, contro quel che diceva la prima stesura di questo documento: `flatpak permission-set kde-authorized remote-desktop <app-id> yes` — documentato in `xdg-desktop-portal-kde!326`, unita nel **gennaio 2025, milestone 6.3: c'è già in Trixie** [I]. Per un'applicazione non in sandbox l'`app-id` viene dal **nome dell'unità systemd** (`app-<app-id>.service`), quindi REMOTIX può averne uno. Resta il **piano B** — passa comunque dal portale — ma ora è verificato, non congetturato |
| `zwlr_screencopy_manager_v1`, `ext_image_copy_capture_v1` | ⛔ **non esistono in KWin 6.3.6**: non sono filtrati, sono **assenti** [✗]. Della famiglia wlroots KWin implementa solo `wlr-layer-shell` e **`wlr-data-control`** |
| `org.kde.KWin.ScreenShot2` | **uno scatto per chiamata**, immagine cruda su una pipe. Nessuna continuità, nessun output virtuale: non serve |
| `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` | è la scorciatoia con cui abbiamo misurato (`banco/banco-altri.sh:33`). Da banco, non da prodotto — e apre anche `fake_input` a chiunque |

---

## 4. La cattura: `zkde_screencast_unstable_v1`

### 4.1 Le due metà, e la versione

**[R]** Il protocollo è un guscio di segnali Qt (`kwin/src/wayland/screencast_v1.cpp`), il motore è
un **plugin** (`kwin/src/plugins/screencast/`, `EnabledByDefault: true`, caricato solo in modalità
Wayland, `main.cpp:28-35`).

**KWin 6.3.6 annuncia la versione 5** (`screencast_v1.cpp:18`, `static int s_version = 5`), anche
se compilato contro un `plasma-wayland-protocols` che dichiara la 6. Il nostro
`banco/zkde-screencast-unstable-v1.xml` **è la copia giusta**: è la v5, e l'unica differenza dal
master è l'evento `serial` aggiunto nella 6.

### 4.2 Le richieste

**[R]** `screencast_v1.cpp:89-142`:

| Richiesta | `since` | Argomenti | Note |
|---|---|---|---|
| `stream_output` | 1 | `new_id`, `wl_output`, `pointer` | cattura un'uscita esistente |
| `stream_window` | 1 | `new_id`, `window_uuid`, `pointer` | una finestra |
| **`stream_virtual_output`** | 2 | `new_id`, `name`, `width`, `height`, `scale`, `pointer` | **fa creare l'uscita** — l'analogo di `RecordVirtual` |
| `stream_region` | 3 | `new_id`, `x`, `y`, `width`, `height`, `scale`, `pointer` | un rettangolo dello spazio di lavoro |
| `stream_virtual_output_with_description` | 4 | come sopra + `description` | la descrizione compare in kscreen |

`pointer` è l'enum del cursore, e **non è validato** (cast secco, `screencast_v1.cpp:91`):

| Valore | Modo | Effetto |
|---|---|---|
| 1 | `Hidden` | nessun cursore |
| 2 | `Embedded` | disegnato nel buffer |
| **4** | **`Metadata`** | come `SPA_META_Cursor`, fuori dall'immagine |

Vanno mandati esattamente 1, 2 o 4: con 0 o 3 nessun `case` corrisponde ma il flag del contenuto
viene comunque alzato — stato incoerente.

### 4.3 `stream_virtual_output`, in dettaglio

**[R]** `screencastmanager.cpp:56-68`:

```cpp
auto output = kwinApp()->outputBackend()->createVirtualOutput(name, description, size, scale);
streamOutput(stream, output, mode);
connect(stream, &ScreencastStreamV1Interface::finished, output, [output] {
    kwinApp()->outputBackend()->removeVirtualOutput(output);
});
```

Cioè: **l'uscita vive quanto lo stream**. Sul backend DRM diventa una `DrmVirtualOutput`
(`drm_backend.cpp:340-347`), e da lì discendono cinque fatti che pesano su tutto il resto:

| | **[R]** |
|---|---|
| Il nome dell'uscita diventa **`"Virtual-" + name`** | `drm_virtual_output.cpp:32`. È l'**unico** modo per ritrovare il proprio `wl_output`: il protocollo non dice al client quale uscita ha creato. `wl_output` è annunciato a **v4**, che ha `name` (`kwin/src/wayland/output.cpp:24,159`) |
| **Un solo modo**, della misura chiesta, a **60000 mHz fissi** | `drm_virtual_output.cpp:28`. Da qui l'impossibilità di ridimensionare (§8) |
| `width`/`height` sono i **pixel** del modo | l'XML li chiama «logical»; `scale` finisce solo nella geometria logica (`core/output.cpp:457-459`). **Si passa `scale = 1` e la misura in pixel**: `DrmVirtualOutput` usa la misura tale e quale, mentre il backend annidato fa `size * scale` (`wayland_backend.cpp:567`) — due interpretazioni diverse nello stesso protocollo |
| La cadenza è un **`SoftwareVsyncMonitor`**, cioè un `QTimer` a granularità di millisecondo | `drm_virtual_output.cpp:24,51-56`; `softwarevsyncmonitor.cpp:44-56`. **È il tetto strutturale a ~60 fps**, e la sua irregolarità |
| **Nessuna validazione della misura** | `screencast_v1.cpp:98-112` passa due `int32` grezzi: nessun minimo, nessun massimo, nessun rifiuto dei negativi (`stream_region`, per confronto, almeno controlla `isValid()`). **[?]** che cosa fa con 0×0 o 16384² va misurato |

### 4.4 Il nodo PipeWire, e perché la trappola di Mutter qui non esiste

**[R]** La catena: richiesta → `integrateStreams()` collega **prima** i tre segnali e **poi** chiama
`init()` (`screencastmanager.cpp:131-145`) → `pw_stream_connect(... PW_DIRECTION_OUTPUT,
PW_STREAM_FLAG_DRIVER | PW_STREAM_FLAG_ALLOC_BUFFERS ...)` → allo stato `PAUSED` KWin legge l'id del
nodo e lo annuncia una volta sola (`screencaststream.cpp:126-131`) → evento `created`.

**La trappola numero 2 di `LEZIONI.md` §4 — «ci si iscrive all'annuncio del nodo prima di avviare
il flusso» — su KDE non può presentarsi.** Su Mutter l'annuncio è un broadcast D-Bus su un oggetto
creato dal server, e chi si iscrive tardi perde qualcosa di già passato. Qui l'oggetto
`zkde_screencast_stream_unstable_v1` ha un **id allocato dal client nella stessa richiesta**: gli
eventi finiscono nella coda della connessione e arrivano al primo dispatch. Basta registrare il
listener prima di `wl_display_dispatch` — e `banco/nodo-kwin.c:142-143` lo fa già.

⚠ **Ma `failed` è sincrono** (`screencastmanager.cpp:82,141-144`): chi non ha il listener attivo lo
perde e aspetta per sempre. **Serve un timeout comunque.**

**[R]** L'id del nodo **non cambia** per tutta la vita del flusso, comprese le rinegoziazioni di
formato e i cambi di misura.

### 4.5 Il formato, riga per riga

**[R]** `screencaststream.cpp:735-783`. KWin propone **fino a tre** `SPA_PARAM_EnumFormat`:
DMA-BUF con un solo modificatore (dopo la fissazione), DMA-BUF con l'intera lista
(`MANDATORY | DONT_FIXATE`), e **memoria condivisa** senza la proprietà `modifier`.

| Campo | Valore | Nota |
|---|---|---|
| formato pixel | 11 corrispondenze DRM↔SPA; per output e regione il formato DMA-BUF è **sempre `DRM_FORMAT_ARGB8888`** | e per BGRA/RGBA KWin annuncia anche la variante senza alfa: **`BGRx` è negoziabile**, ed è quel che serve a RDP (`:775-783`) |
| `VIDEO_size` | rettangolo singolo della misura corrente | `resize()` lo aggiorna in banda (§8.3) |
| **`VIDEO_framerate`** | **`SPA_FRACTION(0,1)` fisso** | ⛔ chi propone una cadenza **fissa** diversa non trova intersezione: la stessa forma del vicolo cieco di Mutter, e la nostra opzione `--fissa` del banco **è inutilizzabile su KWin** |
| `VIDEO_maxFramerate` | `RANGE(default = refreshRate/1000, 1/1, refreshRate)` | **è il freno server-side**: KWin coalizza il danno e blitta a quel ritmo (`:507-516`) |
| buffer | **`RANGE(3, 2, 4)`** | il consumatore può stringere, non allargare. Il nostro banco chiede `RANGE(4,2,8)`: si intersecano su 2..4 |
| tipo di dato | `1 << SPA_DATA_DmaBuf` **oppure** `1 << SPA_DATA_MemFd` | mai un'unione; **`MemPtr` non è mai offerto**: il `mmap` lo fa il consumatore |

⚠ **L'aritmetica del freno è intera, in millisecondi** (`:507-516`): chiedendo 60 si ottiene un
intervallo di 16 ms (≈62 fps), chiedendo 30 si ottiene 33 ms (≈30,3). Il danno accumulato non si
perde.

⛔ **E se un modificatore fallisce, viene rimosso per sempre.** `onStreamParamChanged` prova ad
allocare davvero un buffer (`testCreateDmaBuf`, `:920-951`); se non riesce, quei modificatori
escono dalle offerte future (`:260-264`): un client che insiste non otterrà il DMA-BUF una seconda
volta.

**I metadati offerti**, sempre (`:196-217`):

| Meta | Dimensione |
|---|---|
| `SPA_META_Header` | `sizeof(spa_meta_header)` |
| `SPA_META_VideoDamage` | `RANGE(16 regioni, 1, 16)` |
| `SPA_META_Cursor` | bitmap fino a **256×256** |
| `SPA_META_SyncTimeline` | **solo con DMA-BUF** |

### 4.6 ✅ Fotogrammi interi, non un «diff» — la differenza che conta

**[R]** `screencaststream.cpp:618` → `outputscreencastsource.cpp:63-80`:

```cpp
GLFramebuffer::pushFramebuffer(target);
outputTexture->render(textureSize());   // l'INTERA texture, sempre
GLFramebuffer::popFramebuffer();
```

Nessuno scissoring, nessun uso della regione danneggiata. Lo stesso per il ramo in memoria
(`screencastutils.h:42-77`) e per la regione. E la texture di partenza è essa stessa completa: il
layer dell'uscita ricicla uno swapchain con *damage journal* e **ripara ogni slot in base alla sua
età** prima di ridisegnarlo (`drm_virtual_egl_layer.cpp:76-88`,
`drm_egl_layer_surface.cpp:192-199`).

| | Mutter (misurato, R29) | **KWin 6.3.6** [R] |
|---|---|---|
| Contenuto del buffer prestato | **un *diff*** sul buffer riciclato | **fotogramma intero** |
| Buffer riciclati | 4 | 2–4, default 3 |
| Danno dichiarato | sì | sì, fino a 16 rettangoli, poi il *bounding rect* |

> ✅ **Ricaduta diretta sul difetto che tiene spenta la copia zero su GNOME.** La superficie di
> accumulo di R29 **non serve su KWin**: il danno serve a non ricodificare quel che non è cambiato,
> non a ricostruire il fotogramma. Chi porta la cattura su KDE non eredita quel debito.

Il danno arriva già **in pixel** (`outputscreencastsource.cpp:92-97`), e la lista è chiusa da una
regione sentinella `SPA_REGION(0,0,0,0)` (`:703-728`).

### 4.7 ⛔ La trappola vera: i buffer «corrotti» del cursore

**[R]** `screencaststream.cpp:659-664`:

```cpp
if (effectiveContents & Content::Video) {
    spa_data->chunk->flags = SPA_CHUNK_FLAG_NONE;
} else {
    // in pipewire terms, corrupted means "do not look at the frame contents" and here they're empty.
    spa_data->chunk->flags = SPA_CHUNK_FLAG_CORRUPTED;
}
```

In modo cursore `Metadata`, **ogni movimento del puntatore** produce un buffer senza
`m_source->render()` (`:447-451`, `:590-596`): dentro ci sono i pixel **stantii** di due-quattro
fotogrammi prima, e l'unica indicazione è quel flag.

> ⛔ **È l'analogo funzionale della trappola di Mutter, in una veste nuova**: un consumatore che
> ignora `chunk->flags` mostra un fotogramma vecchio **a ogni movimento del mouse**. kpipewire lo
> gestisce (`kpipewire/src/pipewiresourcestream.cpp:618-621`); **`banco/misura-cattura.c` no**, e li
> conta come fotogrammi consegnati — cioè la nostra misura di fps su KWin è gonfiabile muovendo il
> mouse. Su un desktop non presidiato il mouse è fermo e le misure del 7 agosto probabilmente
> reggono, ma il conteggio va reso onesto prima di rimisurare.

### 4.8 ✅ La sincronizzazione: **la fa KWin**, e spiega un nostro vicolo cieco

**[R]** `screencaststream.cpp:637-655`. Con explicit sync attivo KWin **non aspetta** il
completamento GPU e mette i punti in `acquire_point`/`release_point`; senza, fa **`glFlush()`** — e
**`glFinish()` su NVidia e llvmpipe**, con il commento *«Implicit sync is broken on Nvidia and with
llvmpipe»*.

> ⛔ **`LEZIONI.md` §8 registra come vicolo cieco «aspettare la *fence* implicita del DMA-BUF: non
> cambia niente, è quella sbagliata».** Il codice di KWin dice il perché in generale: **non c'è
> alcuna fence implicita da aspettare se chi disegna non l'ha messa.** La domanda giusta da fare a
> Mutter non è «la fence è pronta?» ma «Mutter fa il flush?». È un'ipotesi nuova su un difetto che
> avevamo lasciato aperto, e non costa niente verificarla.

**Il contratto di `SPA_META_SyncTimeline`, che non stava da nessuna parte** [R]
(`screencastbuffer.cpp:86-107`, `screencaststream.cpp:534-537`, `606-613`, `639-647`):

- due `spa_data` in più, di tipo `SPA_DATA_SyncObj`, agli indici `planeCount` e `planeCount+1`,
  **con lo stesso fd**; `blocks = planeCount + 2`;
- `acquire_point` e `release_point` nel metadato;
- il produttore **non riusa il buffer** finché il `release_point` non è materializzato;
- KWin propone **due** `SPA_PARAM_Buffers`: il primo con `metaType` `SPA_META_SyncTimeline` marcato
  `MANDATORY`, il secondo di ripiego «per implicit sync o MemFd». **Chiedere la timeline è una
  scelta deliberata del consumatore**, non un caso.

Per REMOTIX: l'implicit sync è la strada corta e basta, perché KWin fa il flush. L'explicit è
un'ottimizzazione successiva.

> ### ⚠ MISURATO — «la fa KWin» va inteso alla lettera: **flush non è finish**
>
> **[M] 8 agosto 2026, con una scena in movimento** (`weston-simple-egl` a schermo intero) e il
> misuratore che interroga la fence implicita con `poll(POLLIN, 0)` sul descrittore del DMA-BUF —
> **lo stesso metodo con cui misurammo Mutter**, quindi i due numeri sono confrontabili:
>
> | percorso | fotogrammi | «disegno non finito» |
> |---|---|---|
> | **DMA-BUF** | 594 in 10,03 s | **830 su 830** |
> | in memoria (MemFd) | 435 in 10,03 s | **0** |
>
> ⛔ Cioè **su questa macchina il 100 % dei buffer DMA-BUF arriva con il disegno in corso.** Non
> contraddice §4.8: KWin fa `glFlush()`, che **sottomette** il lavoro alla GPU e non aspetta che sia
> finito (`glFinish()` lo fa **solo** su NVidia e llvmpipe — cioè proprio dove la fence implicita è
> rotta). Su AMD e su Intel, quindi, **la fence c'è ed è il consumatore che deve aspettarla.**
>
> ✅ **La buona notizia resta intatta, ed è un'altra**: i fotogrammi sono **interi** (§4.6), quindi il
> difetto di R29 — il «diff» su buffer riciclati, che ci ha fatto spegnere la copia zero su GNOME —
> **non si ripresenta**. Su KDE la copia zero richiede *una* cosa: aspettare la fence prima di
> codificare, che è il comportamento corretto di qualunque consumatore.
>
> ⚠ E il conteggio dei buffer: 830 buffer contro 594 fotogrammi contati, con «danno parziale 829,
> pieno 1». I ~236 di differenza sono verosimilmente i buffer di **solo cursore** di §4.7, che il
> misuratore scarta: un'altra ragione per rendere onesto quel conteggio prima di citarlo.

### 4.9 Ciclo di vita — e i due modi di perdere il flusso

**[R]** `screencaststream.cpp`, `screencastmanager.cpp`, `outputscreencastsource.cpp`:

| Evento | Che cosa fa KWin |
|---|---|
| il client Wayland si disconnette | `finished()` → `close()`; per un output virtuale, `removeVirtualOutput()` |
| **il consumatore PipeWire si sgancia** (`UNCONNECTED`) | ⛔ **`close()`**: il flusso non sopravvive, e con lui **muore l'output virtuale** (`:142-144`) |
| il consumatore mette in pausa | `m_source->pause()`: si scollega dal danno |
| il consumatore riparte (`STREAMING`) | ✅ `resume()` → **un fotogramma pieno subito** (`outputscreencastsource.cpp:99-109`) |
| **l'uscita viene disabilitata** (`enabled=false`, per esempio da kscreen) | ⛔ `closed()` → flusso morto (`outputscreencastsource.cpp:27-32`) |
| PipeWire cade (`-EPIPE`) | `close()` |

> ⛔ **Regola per il palco su KDE**: fra due client RDP **non si distrugge il `pw_stream`** — si fa
> `pw_stream_set_active(false)`. Un `UNCONNECTED` smonta l'output virtuale, e chi si ricollega non
> trova più niente. È la stessa forma della regola del palco di §7.3 di `REFERENCE.md`, con un
> meccanismo diverso.

**Nessuna richiesta «mandami un fotogramma pieno adesso»** esiste nel protocollo [✗]: il fotogramma
pieno arriva solo alla ripresa da pausa. **R9 vale identica su KDE**: l'ultimo fotogramma va
conservato e rispedito da noi.

**Sessione inattiva (cambio VT) — buona notizia da confermare.** `DrmGpu::setActive(false)`
inibisce i render loop **solo** dei `m_drmOutputs`, e i virtual output vivono in un'altra lista
(`drm_gpu.cpp:710-723`, `drm_backend.cpp:340-347`); `present()` di un virtual output non fa alcun
commit KMS. **Sulla carta la cattura continua a sessione in background** — è esattamente ciò che
serve a un servizio non presidiato. **[?]** da misurare con un `chvt`. Lo stesso per il DPMS:
`DrmVirtualOutput::setDpmsMode()` scrive solo lo stato, non inibisce il render loop
(`drm_virtual_output.cpp:66-71`).

### 4.10 Il cursore

**[R]** Il modo si decide **una volta sola**, prima di `init()`, e **non è cambiabile a flusso
vivo** (`setCursorMode`, `:915-918`).

Con `Metadata` (`addCursorMetadata`, `:801-860`): posizione e hotspot **già scalati** e mappati
nell'output, a ogni movimento; **la bitmap solo quando la forma cambia** (`bitmap_offset = 0`
altrimenti — il consumatore deve **ricordare** l'ultima forma); formato RGBA premoltiplicato,
**troncata** a 256×256, non scalata; `id = 0` quando il cursore non è visibile.

Tre vincoli **[R]**:

1. il cursore c'è **solo se sta sopra il nostro output** (`cursor->isOnOutput`,
   `outputscreencastsource.cpp:124-131`): con un output virtuale bisogna portarci il puntatore, e
   prevedere il caso «è andato altrove» — il client resta senza cursore, senza errore;
2. gli aggiornamenti di cursore passano dallo **stesso freno** del video: negoziare un
   `maxFramerate` basso **strozza anche il cursore** (`:501-517`). Conviene negoziare alto e
   limitare la codifica da noi;
3. `Cursors::isCursorHidden()` lo azzera in blocco.

> **Per RDP il modo giusto è `Metadata` (4)**: RDP ha un canale puntatore proprio, e così il cursore
> non costa una ricodifica. Il prezzo è §4.7. Se si volesse partire semplici, `Embedded` (2) è a
> prova di errore ma paga un fotogramma intero per ogni movimento del mouse.
>
> E una nota che vale di più: **la posizione del cursore la sappiamo già noi**, perché siamo noi a
> iniettare il movimento. Il metadato serve per la **forma** e per i movimenti che non generiamo.

---

## 5. Senza monitor: i backend, e la GPU

### 5.1 ⛔ La nostra misura del 7 agosto è contraddetta dal codice

`REFERENCE.md` R32 e `LEZIONI.md` §3 dicono: *«KWin senza monitor disegna in software: col backend
`--virtual` non apre alcun nodo DRM e non carica alcuna libreria GL»*. Il codice dice il contrario.

**[R]** `kwin/src/backends/virtual/virtual_backend.cpp:23-56`: il costruttore del backend enumera i
dispositivi DRM con `drmGetDevices2()` e apre un **nodo di rendering** (`DRM_NODE_RENDER`,
`renderD*`) con un `::open(O_RDWR)` diretto — **senza logind**. E `:73-81`:
`OpenGLCompositing` è dichiarato **solo se** quel nodo si è aperto; altrimenti resta soltanto
`QPainterCompositing`. Il renderer OpenGL è **EGL su gbm** (`virtual_egl_backend.cpp:108-115`,
`EGL_PLATFORM_GBM_KHR`), con swapchain di buffer gbm.

E la prova sta **nella nostra stessa tabella**: `banco/tabella-altri.txt` riporta per KWin
`tipo=DMA-BUF`, `fence=1010`, 59,50 fps. Ma un flusso screencast **può essere DMA-BUF solo se il
compositore è un `AbstractEglBackend`** (`screencaststream.cpp:920-925`, e `:154-155` per la scelta
del tipo di buffer). Cioè: **in quella misura KWin stava già componendo sulla GPU.**

Le sole cause di un `findRenderDevice() == nullptr`, dal codice: nessun `/dev/dri` visibile;
**permessi** sul render node (gruppo `render`) — e allora compare `Failed to open drm node: <path>`
(`core/drmdevice.cpp:77`, `qCWarning`, **visibile per difetto**); gbm/Mesa mancante.

> ⛔ **Che cosa va fatto, e in quale ordine.** Non si corregge il documento su una lettura di codice:
> si rifà la misura, con le due prove che non dipendono da quel che KWin dichiara (§5.3). Poi si
> corregge R32 con data e fonte. Fino a quel momento, **il numero «KWin: 60 fps a 4K» resta valido
> come misura e sospetto quanto alla sua etichetta**: quel che è in dubbio non è il 60, è il «in
> software».

> ### ✅ MISURATO — e l'etichetta «in software» era sbagliata
>
> **[M] Misura M3, banco del 7 agosto 2026, `kwin_wayland --virtual` 6.3.6-1, Mesa 25.0.7.**
> Le tre prove, tutte concordi:
>
> | Prova | Esito |
> |---|---|
> | nodi DRM aperti dal compositore | **`/dev/dri/renderD129`** — un render node, aperto |
> | librerie di rendering caricate | `libEGL.so.1.1.0`, **`libEGL_mesa.so.0.0.0`**, `libgbm.so.1.0.0`, `libgallium-25.0.7` |
> | global `zwp_linux_dmabuf_v1` | **annunciato, versione 4** — e nasce solo da `AbstractEglBackend::initWayland()` |
>
> **Verdetto: KWin senza monitor compone sulla GPU.** La lettura del codice era giusta e la nostra
> etichetta era sbagliata: **R32 va corretta**, il «60 fps a 4K» resta ma non è «in software».
>
> ⚠ **Una trappola nella prova, per chi la rifà.** Su Mesa 25 tutti i driver gallium — llvmpipe
> compreso — stanno in **un'unica** `libgallium-*.so`: quindi *«non vedo llvmpipe fra le librerie»*
> **non prova niente**, e la vecchia ricerca di `swrast_dri`/`llvmpipe` per nome non funziona più.
>
> ⛔ **E la prova che avevo dato per buona il 7 agosto — «il render node aperto» — NON prova la GPU.**
> [M, 8 agosto] Con `KWIN_COMPOSE=Q`, cioè KWin **in QPainter**, `/dev/dri/renderD129` risulta
> **aperto comunque**: il nodo lo apre il *costruttore* di `VirtualBackend`, prima che si scelga il
> compositore. Quindi quella riga dice «il backend ha trovato un device», non «sta rendendo in GPU».
>
> ✅ **La prova che regge è una sola, e KWin la regala** (§5.3-bis): la stringa del renderer, via
> `org.kde.KWin.supportInformation` su D-Bus. Sul banco:
> `OpenGL renderer string: AMD Radeon RX 6800 (radeonsi, navi21, LLVM 19.1.7, DRM 3.64, 7.0)`,
> `Mesa 25.0.7`. Nessuna interpretazione possibile.
>
> La gerarchia delle prove, dopo il banco, dalla più forte alla più debole:
>
> | Prova | Che cosa dimostra davvero |
> |---|---|
> | **stringa del renderer** (`supportInformation`) | ✅ il driver e il chip esatti: **GPU o llvmpipe** |
> | `zwp_linux_dmabuf_v1` annunciato | **EGL sì/no** — con `KWIN_COMPOSE=Q` scompare (0), con OpenGL c'è (1). **Non** distingue GPU da llvmpipe |
> | render node aperto | ⛔ **niente**: aperto anche in QPainter |
>
> ⚠ **E per leggere quel `/proc` serve `sudo`, con una ragione precisa**: `/usr/bin/kwin_wayland`
> porta l'attributo esteso **`security.capability`** (verificato: `cap_sys_nice`), e un binario con
> file capabilities è **non dumpable** — il kernel nega `/proc/<pid>/fd` e `/proc/<pid>/maps` anche
> all'utente che l'ha avviato. Non è un difetto del banco. (Copiare il binario per perdere l'xattr
> **non** è una scorciatoia praticabile: la copia non carica il plugin QPA `wayland-org.kde.kwin.qpa`
> e muore con `Aborted`.)
>
> 🟡 **Quel che invece resta aperto è il tipo di buffer (M3d).** Il flusso negoziato sul banco è
> `1280x720 BGRx, modificatore 0x0, memoria` — cioè **MemFd**, non DMA-BUF. Ma questo **non**
> contraddice il verdetto: è il *nostro* cliente che non offre DMA-BUF (la copia zero è rinviata
> dalla fase 9). Il criterio di §5.3 punto 1 vale solo a parti invertite: se il cliente offre
> DMA-BUF e KWin lo nega, allora KWin è in QPainter. Da rifare quando il cliente saprà offrirlo.

### 5.2 I backend, e la scelta fra `--virtual` e `--drm`

**[R]** La selezione è in `main_wayland.cpp:428-463`, e l'ordine conta: `--drm` → `--x11-display` →
`--wayland-display` → `--virtual` → **poi** l'euristica sull'ambiente (`WAYLAND_DISPLAY` → annidato
Wayland, `DISPLAY` → annidato X11, **altrimenti drm**).

> ⛔ **Da cui una regola operativa**: il backend si passa **sempre** esplicitamente. Se REMOTIX gira
> dentro una sessione dove `WAYLAND_DISPLAY` o `DISPLAY` sono impostate, senza opzione KWin sceglie
> il backend annidato; con l'ambiente pulito sceglie **drm** e senza logind muore.

| | `--virtual` | `--drm` con zero uscite fisiche |
|---|---|---|
| GPU | **sì**, su un render node, per difetto [R] | sì, sul nodo primario `card*` [R] |
| Prerequisiti | **solo r/w su `/dev/dri/renderD*`**; niente logind, niente seat, niente DRM master (`Session::Type::Noop`, `main_wayland.cpp:513`) | **sessione logind attivabile su un seat**, con `Activate` + `TakeControl` + `TakeDevice` (`session_logind.cpp:109-131`, `161-188`) |
| `stream_virtual_output` | ⛔ **NON funziona**: `VirtualBackend` non ridefinisce `createVirtualOutput()`, la base torna `nullptr` (`core/outputbackend.cpp:80-83`) → `sendFailed("Could not find output")` | ✅ funziona (`drm_backend.cpp:340-347`) |
| Uscite | fisse, decise all'avvio (`--output-count`, `--width`, `--height`, `--scale`) | nessuna all'avvio; si creano a runtime |
| Scanout diretto | no | sì (`drm_virtual_egl_layer.cpp:140-153`) |
| Modificatori DRM | no: swapchain forzata a `DRM_FORMAT_MOD_INVALID` | sì |
| Scelta della GPU | **nessuna**: prende la prima che si apre, nessuna variabile [R] | `KWIN_DRM_DEVICES` |
| libinput / `/dev/input` | non serve: `createInputBackend()` non è ridefinito, nessun libinput | serve |
| Se fallisce | compone in software con due `qCWarning` | ⛔ `std::exit(1)`, **rumoroso** |

**[R]** `--drm` **parte con zero connettori collegati**: `DrmGpu::updateOutputs()` non crea nulla e
torna `true`, la GPU primaria sopravvive, `EglGbmBackend::init()` non tocca le uscite, e il
Workspace mette un `PlaceholderOutput` 1920×1080 **non composto e non esposto come `wl_output`**
(`workspace.cpp:1217-1231`). Alla prima `stream_virtual_output` il segnaposto viene distrutto e
nasce un `wl_output` vero. E **non accetta mai un render node**: `drmIsKMS()` lo scarta
(`drm_backend.cpp:216-220`), l'enumerazione udev cerca solo `card[0-9]`.

⛔ **`--drm` con una sessione Noop è impossibile per costruzione**: `NoopSession::openRestricted()`
torna `-1` sempre (`session_noop.cpp:41-44`), quindi tutte le `addGpu` falliscono e KWin esce.

> ### ⛔ MISURATO — `--drm` **non** è praticabile senza seat, e quindi la scelta è già fatta
>
> **[M] Misura M2, banco del 7 agosto 2026.** Era «la domanda che decide», e la risposta è **no**.
> Da una sessione senza seat (`loginctl show-session`: `Seat=` vuoto, `Remote=yes`, `VTNr=0`, con
> `seat0` esistente e la console su tty1), `kwin_wayland --drm` **esce con stato 1** dicendo:
>
> ```
> kwin_core:        Failed to activate /org/freedesktop/login1/session/_351 session.
>                   Maybe another compositor is running?
> kwin_wayland_drm: failed to open drm device at "/dev/dri/card0"
> kwin_wayland_drm: failed to open drm device at "/dev/dri/card1"
> kwin_wayland_drm: No suitable DRM devices have been found
> ```
>
> ⚠ **E non è un problema di permessi Unix**, che è la spiegazione comoda da escludere: nello stesso
> ambiente e con gli stessi gruppi, il giro `--virtual` **apre `renderD129` senza difficoltà**. Il
> punto di rottura è `Activate()`, cioè esattamente la riga di `session_logind.cpp:109-131` che la
> tabella qui sopra dà come prerequisito.
>
> **Conseguenza per la fase**: l'unico modo di avere `--drm` sarebbe una sessione **su `seat0`**,
> cioè imitare un display manager e **occupare la console fisica** — e allora non è più un servizio
> remoto che convive con l'utente locale. Quindi **la «scelta fra `--virtual` e `--drm`» (§13.4,
> decisione 1) non è una scelta**: è `--virtual`, e con essa il prezzo di §8.1 (nessun
> `stream_virtual_output`, nessun ridimensionamento prima di KWin 6.8).
>
> ⚠ **Nota di banco**: ogni comando SSH apre una sessione logind **nuova** (49, 50, 51…), tutte senza
> seat. Un identificativo di sessione letto in un comando non vale nel comando successivo — «No
> session '49' known» — e chi scrive prove su logind deve rileggerlo ogni volta.

### 5.3 Come si accerta se KWin è in GPU o in software

**[R]** Le due prove che non dipendono da quel che KWin dichiara:

1. **Il tipo di buffer che il flusso screencast offre.** DMA-BUF ⇒ EGL/gbm su un nodo DRM reale;
   solo MemFd ⇒ QPainter, cioè CPU (`screencaststream.cpp:920-925`, `154-155`). Nessun modo di
   simulare l'uno con l'altro.
2. **La presenza del global `zwp_linux_dmabuf_v1`**, creato pigramente e **solo** da
   `AbstractEglBackend::initWayland()` (`abstract_egl_backend.cpp:118-196`,
   `wayland_server.cpp:516-530`). Se `wayland-info` sul socket di KWin non lo elenca, KWin è in
   QPainter.

Più, dal sistema operativo: `ls -l /proc/$(pidof kwin_wayland)/fd | grep dri`.

⚠ **Quello che invece non basta**: `compositingType` distingue OpenGL da QPainter, **non GPU da
software**; e `supportInformation` va letto **insieme** alla riga `OpenGL renderer string`, perché
llvmpipe e softpipe **non** fanno ripiegare KWin su QPainter (`m_recommendedCompositor` resta
`OpenGLCompositing`, `glplatform.h:331`, `glplatform.cpp:876-886`). *«Compositing Type: OpenGL»* su
llvmpipe è possibile, ed è il caso peggiore: rendering software travestito da GPU.

### 5.4 ⛔ `KWIN_COMPOSE` non protegge all'avvio

**[R]** L'enforcement di `KWIN_COMPOSE` è `qApp->quit()` (`compositor_wayland.cpp:164`), ma
`createRenderer()` gira dentro `performStartup()`, chiamata **sincronamente** da
`Application::start()` **prima** di `a.exec()` (`main.cpp:144`, `main_wayland.cpp:620-622`). Senza
ciclo di eventi, `quit()` è inerte: il ciclo dei candidati prosegue, QPainter riesce, e **KWin parte
in software nonostante `KWIN_COMPOSE=O2`**, con una sola `qCCritical` a testimoniarlo.

> È la lezione 1.8 di `LEZIONI.md` in casa d'altri: **quando un componente può decidere da sé,
> bisogna dirgli cosa fare — e verificare che abbia obbedito.** Tutte le misure prese con
> `KWIN_COMPOSE=O2` presuppongono che quell'interruttore funzioni.

> ### ⛔ MISURATO — `KWIN_COMPOSE=O2` **non protegge**, e la lettura del codice era giusta
>
> **[M] Misura M4, 8 agosto 2026.** Per rispondere bisognava rendere OpenGL *impossibile*, e non
> bastava renderlo *lento*: `LIBGL_ALWAYS_SOFTWARE=1`, `GALLIUM_DRIVER`, `MESA_LOADER_DRIVER_OVERRIDE`
> e `__EGL_VENDOR_LIBRARY_DIRS` **non hanno alcun effetto** su KWin (il renderer resta
> `AMD Radeon RX 6800 (radeonsi)`: verificato con `supportInformation`). La condizione si ottiene
> togliendo l'accesso ai render node — sul banco con un namespace di monti privato.
>
> Allora, con tutti i render node inaccessibili:
>
> | | esito |
> |---|---|
> | senza `KWIN_COMPOSE` *(controllo)* | `Configured compositor not supported by Platform. Falling back to defaults` → **QPainter**, e KWin parte |
> | **con `KWIN_COMPOSE=O2`** | `Compositing forced to OpenGL mode by environment variable` → **`Falling back to defaults`** → **`QPainter compositing has been successfully initialized`**, e **KWin parte** |
>
> ⛔ **Quindi l'interruttore è inerte**, esattamente come diceva §5.4: il `qApp->quit()` gira prima del
> ciclo di eventi. **Conseguenza operativa**: `KWIN_COMPOSE=O2` non va usato come garanzia in nessuna
> nostra ricetta né in nessun banco; l'unico modo di sapere come sta rendendo KWin è **chiederglielo**
> (la stringa del renderer, §5.1). E la cattura resta disponibile anche in QPainter: `zkde_screencast`
> è annunciato e il global `zwp_linux_dmabuf_v1` scompare — l'unico segno visibile del ripiego.

### 5.3-bis ✅ La prova diretta: chiedere a KWin che renderer usa

**[M, 8 agosto 2026]** La misura che chiude ogni dubbio su GPU-o-software, e che non richiede né
`/proc` né `sudo`:

```sh
gdbus call --session --dest org.kde.KWin --object-path /KWin \
    --method org.kde.KWin.supportInformation | grep -oE 'OpenGL renderer string: [^\\]*'
```

Funziona su KWin nudo e dentro una sessione Plasma. In QPainter la riga **non c'è** — che è a sua
volta una risposta.

### 5.6 ⚙ Scegliere QUALE GPU usa il compositore — deciso dall'utente

> **Decisione dell'utente, 8 agosto 2026: «non usare la Radeon, usa la Intel integrata».**
> La macchina di prova ha due GPU: Intel AlderLake-S (i915) su `renderD128` e Radeon RX 6800
> (amdgpu) su `renderD129`.

**[R]** Con `--virtual` **non esiste alcuna leva**: `findRenderDevice()`
(`virtual_backend.cpp:23-56`) itera `drmGetDevices2()` e prende **la prima che si apre**, senza
guardare nessuna variabile — `KWIN_DRM_DEVICES` vale solo per il backend `drm`. Sul banco l'ordine
mette la Radeon davanti, e KWin prende quella.

**[M]** Quindi la Intel si ottiene in un modo solo: **rendere l'altra GPU non apribile da quel
processo**. Due strade provate, e una sola va bene:

| Strada | GPU | Cancello della cattura |
|---|---|---|
| `InaccessiblePaths=/dev/dri/renderD129` nell'unità | ✅ Intel | ⛔ **chiuso** (§3.3-bis, riquadro) |
| `DeviceAllow=` + `DevicePolicy=closed` | ⛔ nessun effetto: resta la Radeon (in un'unità **d'utente** il controllo dei device non è delegato) | ✅ aperto |
| ✅ **permessi del nodo** (`renderD129` fuori dal gruppo `render`) | ✅ **Intel** | ✅ **aperto**, e flusso PipeWire ottenuto |

✅ **La via buona è la terza**, e per il prodotto si scrive come **regola udev** che assegna il nodo
della GPU da non usare a un gruppo che l'utente del servizio non ha — identificando la scheda per
**id PCI** (`/dev/dri/by-path/pci-0000:03:00.0-render`), perché il numero del nodo non è stabile.

⚠ **E il prezzo va detto**: negare il nodo coi permessi lo nega **a tutta la sessione dell'utente**,
non solo al compositore. Se un giorno servisse la Radeon per un'altra cosa nella stessa sessione, la
strada giusta diventa un'altra (per esempio far scegliere a *noi* il device e non a KWin, che oggi
non è possibile senza toccare KWin).

### 5.7 📊 Quanto eroga la cattura **sulla Intel integrata** — la tabella che conta per il prodotto

**[M] 8 agosto 2026.** Le tabelle di `REFERENCE.md` R32 sono della Radeon; queste sono della GPU che
il prodotto userà. Misura della **sola cattura**, scena dichiarata e in movimento
(`weston-simple-egl` a schermo intero, sincronizzato al ridisegno), tetto dichiarato 60 fps, 10
secondi per cella, `kwin_wayland --virtual` con la Radeon negata:

| Risoluzione | copia zero (DMA-BUF) | in memoria (MemFd) |
|---|---|---|
| 1280×720 | **59,4** *(mediana 16,5 ms)* | 49,6 *(20,2 ms)* |
| 1920×1080 | **59,2** *(17,2 ms)* | 43,3 *(23,2 ms)* |
| 2560×1440 | **59,3** *(17,2 ms)* | 37,0 *(27,0 ms)* |
| **3840×2160** | **59,0** *(17,2 ms)* | **27,0** *(37,4 ms)* |

⭐ **Due letture, e sono le più importanti di tutta la fase:**

1. ✅ **A copia zero la risoluzione non costa niente**: 59 fotogrammi al secondo **da 720p a 4K**, con
   la mediana degli intervalli ferma a 17 ms. Il requisito dell'utente — *«30 a 1080p, 60 a 4K»*
   (`REFERENCE.md` R32, e la memoria del progetto) — **è raggiungibile su una Intel integrata**.
2. ⛔ **In memoria la risoluzione costa tutto**: da 49,6 a **27,0** salendo a 4K, cioè meno della metà
   del bisogno. **Il collo di bottiglia è la copia**, non il compositore e non la GPU.

> **Da cui la conseguenza per il piano**: su KDE la copia zero non è un'ottimizzazione, è **la
> condizione** per i 60 a 4K. E su KDE è anche più facile che su GNOME, perché i fotogrammi sono
> interi (§4.6) e resta solo da aspettare la fence (§4.8). La fase 9, rinviata su GNOME per il
> «diff», qui va ripresa con una prospettiva diversa.

E il ripiego è silenzioso quasi ovunque: le righe che lo raccontano sono `qCDebug`, spente per
difetto. L'unica visibile è *«Configured compositor not supported by Platform. Falling back to
defaults»* (`:139`) — che scatta proprio nel caso «il render node non si è aperto». Sul backend
`drm` nemmeno quella: `supportedCompositors()` dichiara sempre `{OpenGL, QPainter}`.

### 5.5 Xwayland — meglio che su GNOME

**[R]** `--xwayland` è opzionale sulla riga di comando e in compilazione; l'avvio è **pigro** (parte
solo quando un client tocca il socket X11, `xwaylandlauncher.cpp:95-99`) e **non bloccante**
(`-displayfd` + `QSocketNotifier`); un fallimento produce un `qCWarning` e **il compositore
continua**; un crash ha una politica di riavvio con conteggio.

> La questione aperta n.8 di `SPECIFICA.md` — «Xwayland non completa l'avvio e a volte si porta
> dietro il compositore» — **su KWin non ha l'equivalente**: qui un Xwayland assente o bloccato non
> appende il compositore. Ma vedi §6.4: su Plasma, X11 serve **a ksmserver**, e quindi
> `--xwayland` diventa obbligatorio per un'altra ragione.

---

## 6. La sessione Plasma senza monitor

### 6.1 La ricetta

**[R]**, e le due variabili obbligatorie sono solo due:

```sh
# 1. ambiente composto da zero (env_clear), con:
XDG_RUNTIME_DIR=/run/user/1000                         # obbligatoria: senza, wl_socket_create()
                                                       # torna NULL e il wrapper fa qFatal
                                                       #   [R] wl-socket.c:132-136
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus  # obbligatoria: senza, return 1
                                                       #   [R] startplasma-wayland.cpp:58-61
HOME= USER= PATH= SHELL=
LANG=it_IT.UTF-8                                       # consigliata [R] startplasma.cpp:213-216

# ⛔ NON impostare DISPLAY, WAYLAND_DISPLAY, QT_QPA_PLATFORM
#    [R] main_wayland.cpp:452-463, ksmserver/main.cpp:106-117

# 2. sovrascrittura dell'unità del compositore — su Wayland è l'unica leva
#    $XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d/remotix.conf
[Service]
ExecStart=
ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width W --height H --no-lockscreen
#    poi: systemctl --user daemon-reload

# 3. avvio
exec /usr/bin/startplasma-wayland
```

**Che cosa mette Plasma da sé**, e che quindi non va dichiarato (`startplasma.cpp:353-414`,
`startplasma-wayland.cpp:64`): `XDG_CURRENT_DESKTOP=KDE`, `XDG_SESSION_TYPE=wayland`,
`KDE_FULL_SESSION`, `KDE_SESSION_VERSION=6`, `KDE_SESSION_UID`, `XDG_MENU_PREFIX`,
`XDG_CONFIG_DIRS`, le `XKB_DEFAULT_*` da locale1, `LANG`/`LC_*` da `plasma-localerc`. E
`WAYLAND_DISPLAY`/`DISPLAY`/`XAUTHORITY` le esporta il wrapper del compositore
(`kwin_wrapper.cpp:157-163`).

> ⛔ **E fra quelle che «mette Plasma da sé» ce n'è una che non è un dettaglio: `XDG_MENU_PREFIX`.**
> [M, 7 agosto 2026] Senza di essa **il permesso della cattura non funziona**, per la ragione
> spiegata in §3.3-bis: l'indice dei servizi resta vuoto e KWin non trova nessun `.desktop`. In
> questa ricetta è coperta, perché `startplasma` la imposta
> (`startplasma.cpp:366` — e **non** esegue `kbuildsycoca6`: l'indice si costruisce da sé nel primo
> processo KDE che lo usa, che dentro la sessione ha già il prefisso giusto).
>
> **Il pericolo è per chi non passa da `startplasma-wayland`**: un banco che avvia `kwin_wayland` a
> mano, uno script di manutenzione o un `kbuildsycoca6` lanciato da una shell SSH **senza** il
> prefisso sovrascrivono l'indice buono e chiudono il cancello a compositore già avviato, senza un
> messaggio. Chi scrive prove esporta `XDG_MENU_PREFIX=plasma-` **sempre**.

> ### ✅ MISURATO — la ricetta funziona, con tre precisazioni
>
> **[M] 8 agosto 2026.** `startplasma-wayland` avviato da una shell SSH con l'ambiente qui sopra e il
> drop-in dell'unità: **plasmashell compare in 1 secondo**, il socket è `wayland-0`, KWin risponde su
> D-Bus, la cattura è autorizzata e un flusso PipeWire si monta (§3.3-bis). Le tre precisazioni:
>
> 1. ⛔ **niente `InaccessiblePaths=` (né altro che implichi un namespace di monti) nel drop-in**:
>    chiude il cancello della cattura (§3.3-bis, riquadro). Per la GPU si usano i permessi del nodo
>    (§5.6).
> 2. ⚠ **`ksmserver` e `Xwayland` non sono partiti affatto** (zero processi), e la sessione ha
>    funzionato comunque: plasmashell, kwin_wayland e kded6 in piedi. Su questo §6.4 va riletta — il
>    vincolo «`--xwayland` è obbligatorio per ksmserver» **non si è manifestato** in questa prova, e
>    Xwayland parte pigramente (§5.5). Resta da capire se ksmserver serva per il *logout ordinato* o
>    per il ripristino della sessione: **non si tolga `--xwayland` prima di averlo verificato.**
> 3. ⚠ La sessione **crea 23 file di configurazione** in `~/.config` al primo avvio (`kdeglobals`,
>    `plasmashellrc`, `plasma-localerc`, `kwinrc`…). È normale, ma va saputo: la prima sessione
>    scrive nella casa dell'utente, e `plasma-localerc` fissa la locale (sul banco: `LANG=C.UTF-8`).

> ✅ **Il difetto silenzioso pagato su GNOME non c'è.** `ConditionEnvironment=` **non esiste in
> nessuna unità** dei sette repo [R]: su GNOME l'unità della Shell portava
> `ConditionEnvironment=XDG_SESSION_TYPE=wayland` e senza quella variabile il compositore non
> partiva affatto, senza che nessuno lo spiegasse (§5.9-bis di `SPECIFICA.md`).
>
> ✅ **E Plasma fa da sé la pulizia che noi facciamo a mano.** `dropSessionVarsFromSystemdEnvironment()`
> (`startplasma.cpp:445-473`) toglie a **ogni avvio** dall'ambiente del manager systemd le variabili
> di sessione (`DISPLAY`, `XAUTHORITY`, `WAYLAND_DISPLAY`, `WAYLAND_SOCKET`, tutte le `XDG_*`), con
> il commento: *«Those can be leftovers from previous sessions … e.g. `$DISPLAY` might break
> kwin_wayland»*. È la nostra lezione «chi sopravvive al logout non riusa niente della sessione
> morta», applicata dal desktop stesso.

### 6.2 La catena, e chi lancia il compositore

**[R]** `startplasma-wayland` **non lancia KWin**: fa `StartUnit("plasma-workspace-wayland.target")`
(`startplasma.cpp:726`), e l'unità è

```ini
# kwin/plasma-kwin_wayland.service.in
ExecStart=<bindir>/kwin_wayland_wrapper --xwayland
BusName=org.kde.KWinWrapper
PartOf=graphical-session.target
```

Il wrapper **rigira tutti i propri argomenti** a `kwin_wayland` (`kwin_wrapper.cpp:128-130`): basta
aggiungerli all'`ExecStart`. La ricetta per farlo senza toccare `$HOME` è di KDE stessa —
copia in `$XDG_RUNTIME_DIR/systemd/user.control` più `daemon-reload`
(`login-sessions/startplasma-dev.sh.cmake:8-13`).

L'ordine effettivo che ne risulta: `plasma-kwin_wayland` → `kcminit` → `kded6` →
**`ksmserver`** → `plasmashell` → `plasma-core.target` → `plasma-workspace.target`
(powerdevil, kglobalaccel, kwallet-pam, …) → `graphical-session.target` → autostart.

⚠ **Due fragilità da conoscere** [R]: l'unità del compositore dichiara `BusName=` **senza
`Type=dbus`**, quindi l'ordinamento di ksmserver poggia solo su `After=`, cioè sull'*exec* del
wrapper e non sull'export di `DISPLAY` — nella strada classica il commento è esplicito: *«This must
block until started as it sets the WAYLAND_DISPLAY/DISPLAY env variables needed for the rest of the
boot»* (`plasma-session/startup.cpp:162-165`). E `plasma-core.target` /
`plasma-workspace.target` hanno `RefuseManualStart=yes`: si avvia **solo**
`plasma-workspace-wayland.target`.

### 6.3 ✅ Non serve una sessione logind su un seat — con `--virtual`

**[R]** `--virtual` impone `Session::Type::Noop` (`main_wayland.cpp:513`): **niente logind, niente
seat, niente `/dev/dri` via `TakeDevice`, niente `/dev/input`**. `XDG_SEAT` e `XDG_VTNR` **non sono
letti da nessuno dei sette repo** [✗]. È l'equivalente esatto del nostro accertamento su
`gnome-session` (§5.9-bis di `SPECIFICA.md`).

Con `--drm`, invece, serve una sessione logind **attivabile** su un seat: cioè quel che fa un
gestore di accesso, e che per definizione non abbiamo. **È il compromesso centrale della fase**
(§13).

### 6.4 ⛔ `--xwayland` non è opzionale, e la ragione è ksmserver

**[R]** `plasma-workspace/ksmserver/main.cpp`: forza `QT_QPA_PLATFORM=xcb` (`:106-107`, *«force xcb
QPA plugin as ksmserver is very X11 specific»*), costruisce una `QGuiApplication`, e a `:124`
dereferenzia il display X11 **senza alcun controllo di nullità**. E `ksmserver` è `Requires=` di
`plasma-core.target`, che è `Requires=` della catena fino al target di sessione: **un suo guasto
abbatte tutta la sessione.**

> Cioè: KWin non ha bisogno di Xwayland, **Plasma sì**. E la nostra riga di banco
> (`banco/banco-altri.sh:33`) avvia KWin **senza** `--xwayland`: con quella riga una **sessione
> Plasma non parte**. I 59–60 fps misurati valgono per **KWin nudo**, non per una sessione Plasma
> completa — e questa è la seconda etichetta da correggere sulle misure del 7 agosto.

### 6.5 Il logout: non c'è `RegisterClient`, e la strada buona è passiva

**[R]** Gli attori sono quattro: `plasma-shutdown` (`org.kde.Shutdown`), `ksmserver-logout-greeter`
(`org.kde.LogoutPrompt`), `ksmserver` (`org.kde.ksmserver`), KWin (`org.kde.KWin` `/Session`).

| Come accorgersene | Quando | Rischio |
|---|---|---|
| ✅ **`NameOwnerChanged` su `org.kde.Shutdown`** (nome attivabile: compare quando il logout comincia, `plasma-shutdown/shutdown.cpp:20-23`) | **all'inizio** | nessuno: siamo spettatori |
| ✅ **`NameOwnerChanged` su `org.kde.KWinWrapper`** (sparisce a sessione finita) | alla fine | nessuno |
| ⚠ registrazione **XSMP** presso ksmserver (`$SESSION_MANAGER`, libSM/libICE) | all'inizio, con obbligo di risposta | **la regola dell'ostaggio vale identica**: chi si registra e non risponde frena il logout di **15 s** (`ksmserver/logout.cpp:293-303`), poi viene ignorato |

Le prime due sono esattamente quel che fa `startplasma` per decidere di uscire
(`startplasma.cpp:673-689`). **È la strada da prendere**: costa due sottoscrizioni sul bus e non
mette in gioco la sessione dell'utente. L'equivalente vero di `RegisterClient` esiste — ma è XSMP su
ICE, richiede `libSM`/`libICE` e un `DISPLAY`, e `org.kde.KSMServerInterface` **non ha alcun segnale
«la sessione sta finendo»** [R].

**Comandare il logout da fuori** [R]:

| Che si vuole | Chiamata |
|---|---|
| senza conferma (= `Logout(1)` di GNOME) | `org.kde.Shutdown` `/Shutdown` `logout()` |
| con conferma | `org.kde.LogoutPrompt` `/LogoutPrompt` `promptLogout()` |
| **forzato** (`Logout(2)` **non esiste** [✗]) | `StopUnit("plasma-workspace.target", "fail")` — è quel che fa `plasma-shutdown` alla fine (`shutdown.cpp:151-157`) |
| brutale | `org.kde.KWin` `/Session` `quit()` |

⛔ **E il percorso ordinato può annullarsi da sé.** `KWin::SessionManager::closeWaylandWindows()`
(`kwin/src/sm.cpp:422-508`): dopo **10 s** mostra una notifica persistente con *Cancel Logout* /
*Log Out Anyway*, e se **nessuno risponde** attende fino a **2 minuti** prima di procedere. In una
sessione non presidiata nessuno risponde mai: la seconda metà del nostro `sgombera` (§5.10 di
`SPECIFICA.md`, `Logout(1)` e poi `Logout(2)`) **va riprogettata su KDE** — il secondo passo è
`StopUnit`.

E per non far comparire finestre che nessuno vedrà: `ksmserverrc [General] confirmLogout=false`
(`sessionmanagementbackend.cpp:49-52`).

### 6.6 ✅ Il bus di sessione non muore — se è quello d'utente

**[R]** In tutti e sette i repo **non c'è alcun riferimento a `dbus.service`, `dbus-launch` o
`dbus --exit-with-session`** fuori dai test: Plasma **non gestisce il ciclo di vita del bus**. Lo
pretende in piedi, oppure si fa avvolgere da `plasma-dbus-run-session-if-needed`, che mette
`dbus-run-session` davanti **solo se** `DBUS_SESSION_BUS_ADDRESS` è vuota.

> ✅ **Ricaduta**: se usiamo il bus **d'utente** (`/run/user/UID/bus`) e lo dichiariamo
> nell'ambiente, **sopravvive al logout** e la connessione resta valida. I due difetti pagati su
> GNOME — la connessione da buttare e riaprire, e `exit-on-close` che chiama `raise(SIGTERM)` per
> conto nostro (§7.4 di `REFERENCE.md`) — **non si presentano**, purché non si lasci lavorare
> `dbus-run-session`. **È una scelta nostra, e va fatta per il bus d'utente.**

> ### ✅ MISURATO — misura M9: il logout non porta via niente di nostro
>
> **[M] 8 agosto 2026.** Sessione Plasma vera, chiusa con `org.kde.Shutdown.logout()` — la sentinella
> passiva di §6.5, chiamata come la chiamerebbe il prodotto:
>
> | Dopo il logout | |
> |---|---|
> | `plasmashell`, `kwin_wayland`, `kded6` | **tutti spariti** (0 processi) |
> | il socket `wayland-0` | **sparito** |
> | **il bus d'utente** | ✅ **risponde ancora** (`GetId` riesce sulla stessa connessione) |
> | `systemd --user` | ✅ vivo (`degraded`, per unità di sessione terminate) |
>
> Quindi la scelta «bus d'utente» è confermata dal campo, e il difetto di GNOME **non si ripresenta**.
> ⚠ Un dettaglio da non dimenticare: dopo il logout il socket è `wayland-0` *libero di nuovo*, e al
> riavvio della sessione il numero **può cambiare** — va riletto, come dice il capoverso qui sotto.

**Riavviare la sessione dallo stesso processo funziona** [R], e Plasma lo prevede: `ResetFailed` e
`Reload` a ogni avvio (`startplasma.cpp:648-649`). Cambiano `WAYLAND_DISPLAY` (il socket è il primo
`wayland-N` libero), `DISPLAY` e `SESSION_MANAGER`: **vanno riletti, non ricordati.**

### 6.7 La disposizione di tastiera

**[R]** Su Wayland la impone **KWin**, che legge `kxkbrc [Layout]` da sé (non esiste più un `kxkb`
separato). Tre vie per noi:

1. **`XKB_DEFAULT_LAYOUT`/`_VARIANT`/`_MODEL`/`_OPTIONS` nell'ambiente di `kwin_wayland`**, che
   `applyEnvironmentRules()` usa come riempimento (`xkb.cpp:557-575`); con
   **`KWIN_XKB_DEFAULT_KEYMAP=1`** si **forza** l'uso del solo ambiente, ignorando `kxkbrc` e
   locale1 (`xkb.cpp:522-545`). **È la leva pulita**: la disposizione arriva dal client e la si mette
   nell'ambiente prima di avviare il compositore;
2. D-Bus `org.kde.keyboard` `/Layouts`: `getLayout`, **`setLayout(index)`**, `getLayoutsList`,
   `switchToNextLayout` (`keyboard_layout.cpp:186-245`), senza permessi — ma **sceglie solo fra le
   disposizioni già caricate**;
3. scrivere `kxkbrc` e far ricaricare KWin (`org.kde.KWin` `/KWin` `reconfigure()`). **[?]** quale
   dei due basti.

E comunque: **la keymap della sessione la leggiamo da libei** (§7.4), come su GNOME. Questa sezione
serve per il caso in cui la si voglia *imporre*.

### 6.8 Le animazioni: nessun gancio per-cattura

**[R]** Mutter offre `disable-animations` come opzione della sessione di cattura; il protocollo di
KWin ha **una sola** opzione per stream — il modo del cursore — e nel plugin di cattura non c'è una
riga sulle animazioni [✗]. Su KDE si spengono **a sessione**:

| Leva | Dove | Note |
|---|---|---|
| `KWIN_EFFECTS_FORCE_ANIMATIONS=0` | ambiente di `kwin_wayland` | dichiara le animazioni **non supportate** (`effecthandler.cpp:1425-1433`); letta in una `static`, **non cambiabile a caldo** |
| `AnimationDurationFactor=0` nel gruppo `[KDE]` | `kwinrc` **e** `kdeglobals` | vale **a caldo**, un `KConfigWatcher` la sorveglia (`options.cpp:96-101`); ⚠ `0` non azzera i tempi, li porta a **1 ms** (`effect/effect.cpp:447-457`) |

---

## 7. L'input: KWin parla libei

### 7.1 ✅ Un backend EIS vero, e si apre con una chiamata D-Bus

**[R]** `kwin/src/plugins/eis/`, 1829 righe, plugin **attivo per default**, caricato solo in
modalità Wayland. Il descrittore si ottiene così:

```
servizio     org.kde.KWin
oggetto      /org/kde/KWin/EIS/RemoteDesktop
interfaccia  org.kde.KWin.EIS.RemoteDesktop
metodo       connectToEIS(i capabilities) → (h fd, i cookie)
             disconnect(i cookie)
```

(`eisbackend.h:39-40`, `eisbackend.cpp:70-104`; firma confermata dall'altro lato,
`xdg-desktop-portal-kde/src/remotedesktop.cpp:457-460`). La maschera è quella del portale xdg:
**tastiera 1, puntatore 2, tocco 4** → per noi **7**. Il `cookie` serve a chiudere.

> ⛔ **Nessun controllo sul chiamante.** `registerObject` è `ExportAllInvokables` senza filtro, e
> `message().service()` è usato **solo** per la durata di vita (se il chiamante muore, il contesto
> cade). Nessun pid, nessun `.desktop`, nessun `X-KDE-DBUS-Restricted-Interfaces`, nessun dialogo:
> il meccanismo esiste in KWin ma **in tutto 6.3.6 lo usa solo `ScreenShot2`**.
>
> Per un servizio non presidiato è **meglio di GNOME**: nessuna sessione da creare, nessun portale.
> Va però trattato come **una porta che può chiudersi**: l'errore D-Bus è un caso normale, non un
> bug, e il ripiego è `fake_input` (che invece il `.desktop` lo richiede).

⚠ **Trappola di distribuzione** [R]: `libeis-1.0` è **opzionale** in compilazione
(`kwin/CMakeLists.txt:319-320`, `431`). Se la distribuzione compila KWin senza, il plugin **non
esiste** e l'oggetto D-Bus non compare: non è un errore a runtime, è un'assenza. **[?]** lo stato di
Debian Trixie va misurato.

**I dispositivi** (`eiscontext.cpp:155-174`, `eisbackend.cpp:116-171`): fino a tre per seat —
«eis pointer» (relativo), **«eis absolute device»** (assoluto **+ tocco**), «eis keyboard». Il seat
annuncia solo le capacità concesse dalla maschera. Il nostro contesto deve essere **sender**: un
receiver viene buttato giù (`eiscontext.cpp:127-131`).

### 7.2 Che cosa si riusa del nostro `input.c`, e che cosa cambia

Il confronto con le quattro cose che libei ci dà su GNOME:

| | via **EIS** su KWin | via `fake_input` |
|---|---|---|
| **keymap della sessione** | ✅ **sì**, XKB testo v1 su memfd sigillato (`eisbackend.cpp:159-171`) | no |
| **stato dei modificatori a scatto** | ⛔ **no**: `eis_device_keyboard_send_xkb_modifiers` **non è chiamato da nessuna parte in KWin** [✗] | no |
| **ping / sincronizzazione** | ✅ sì — ma per una proprietà accidentale: non c'è un `case EIS_EVENT_SYNC`, e il pong parte perché l'`unref` è fuori dallo `switch` (`eiscontext.cpp:333`) | no |
| **regioni degli schermi** | ✅ sì, una per output — ⚠ **senza `mapping_id`** (`eis_region_set_mapping_id` non è chiamato) [✗] | no |

**Le quattro cose da toccare, tutte circoscritte:**

1. ⛔ **La rotella va cambiata.** Il nostro `/120 → ×10` usa `ei_device_scroll_delta`, che su KWin
   dà `deltaV120 = 0` (`eiscontext.cpp:246-258`) → un `wl_pointer.axis` liscio **senza
   `axis_value120` né `axis_discrete`** (`pointer.cpp:281-358`): chi conta gli scatti non ne vede
   nessuno, e Xwayland deve indovinare i bottoni 4/5. Va usato **`ei_device_scroll_discrete(±120)`**,
   che KWin converte in `delta = 15` + `deltaV120 = ±120` (`eiscontext.cpp:272-286`), cioè la
   rotella vera. **Si passa il valore RDP quasi com'è: più semplice di oggi.** Verticale negato
   (la convenzione `wl_pointer` è positivo = giù).

   > **✅ Misura M10, chiusa l'8 agosto 2026 — per lettura, e la lettura è conclusiva.**
   > `eiscontext.cpp:272-285`: KWin **non inverte nulla** e tratta i due assi **con la stessa
   > formula**, senza casi particolari:
   > ```cpp
   > constexpr auto anglePer120Step = 15 / 120.0;
   > if (x != 0) Q_EMIT device->pointerAxisChanged(PointerAxis::Horizontal, x * anglePer120Step, x, …);
   > if (y != 0) Q_EMIT device->pointerAxisChanged(PointerAxis::Vertical,   y * anglePer120Step, y, …);
   > ```
   > Il segno passa **tale e quale** sia nel delta angolare sia nel `v120` grezzo. Quindi il verso che
   > arriva alle applicazioni è quello di libinput, **identico per verticale e orizzontale**, e
   > l'adattamento da RDP è **tutto nostro** — come già su GNOME. Non c'è nessuna asimmetria di KWin
   > da compensare, che era il sospetto. ⚠ Resta da guardare **con l'occhio** nella fase, perché il
   > verso è una di quelle cose che si giudicano vedendole (`LEZIONI.md` §7.3).
2. ⛔ **I modificatori a scatto non arrivano.** La riconciliazione di BlocMaiusc/BlocNum dopo un
   ping — quella che su GNOME abbiamo fatto bene — **per questa strada non si fa**. Il ripiego è
   `org_kde_kwin_keystate` v5 (`kwin/src/wayland/keystate.cpp`), che dà `unlocked/latched/locked/pressed`
   **con notifica spontanea**, ma è **in lista nera**: richiede di essere anche client Wayland e di
   dichiararlo nel `.desktop`. **È una scelta da mettere davanti all'utente** (§13.4).
3. **Le regioni si cercano per geometria**, non per chiave: sono già in coordinate globali logiche,
   quindi `transform_position` si semplifica — cambia il criterio di ricerca, non la formula. E
   `libei` scarta una posizione assoluta **fuori da ogni regione**.
4. **I dispositivi si ricambiano.** A ogni cambio di output o di disposizione KWin fa
   `eis_device_remove` + `eis_device_add` (`eisdevice.cpp:42-53`, via `updateScreens`/`updateKeymap`):
   dal nostro lato il dispositivo **scompare e ricompare**. Va retto il ricambio, rileggendo keymap
   e regioni a ogni `DEVICE_ADDED`.

**Quel che invece resta identico** [R]:

| | |
|---|---|
| tasti | **codice evdev senza il −8**: KWin somma lui l'offset, in un punto solo (`xkb.cpp:45`, `772`). La nostra conversione scancode RDP → `WINPR_KEYCODE_TYPE_EVDEV` vale tale e quale |
| bottoni | codici evdev intatti (`BTN_LEFT` 0x110 …) |
| movimento assoluto | coordinate **globali logiche**, formula riusabile |
| tocco | stesse coordinate, sul dispositivo assoluto |
| `ei_device_frame()` | **obbligatorio**: senza, i client Wayland non applicano il movimento (`eiscontext.cpp:190-200` → `wl_pointer.frame`) |
| pressioni ripetute e rilasci non appaiati | **KWin li scarta in silenzio** (`eiscontext.cpp:287-303`): non siamo *costretti* a tenere il conto come su Mutter, ma le nostre tabelle restano utili — servono a noi per sapere che cosa rilasciare |
| rilascio a fine connessione | ✅ **KWin fa da rete di sicurezza**: nel distruttore del dispositivo rilascia ogni tasto e bottone premuto e annulla i tocchi (`eisdevice.cpp:27-40`), e il contesto cade quando il servizio D-Bus chiamante scompare |
| Xwayland | ✅ l'input iniettato **la raggiunge** per la via normale del `wl_seat` (`xwayland.cpp:240-330`): nessun XTEST, nessuna strada separata |

⚠ **Un difetto di KWin trovato per strada** [R]: quattro `continue` dentro lo `switch` di
`eiscontext.cpp` (righe 236, 241, 294, 300) saltano l'`eis_event_unref` finale — ogni pressione
ripetuta e ogni rilascio non appaiato **perde un riferimento**. Non ci cambia niente
funzionalmente, ma è un motivo per non bombardare KWin di eventi ridondanti.

### 7.3 `fake_input`, la strada vecchia

**[R]** `org_kde_kwin_fake_input` (non `zkde_fake_input`), implementato in
`kwin/src/backends/fakeinput/fakeinputbackend.cpp`, **versione 5** mentre l'XML dichiara la 6
(`keyboard_keysym` **non è implementato**). È a senso unico: **zero eventi**. Il suo `authenticate`
ignora gli argomenti e non autentica nulla (`:107-113`, `// TODO: make secure`), ma il permesso
vero è il filtro dei global.

E il suo limite serio: `axis` forza **`deltaV120 = 0` sempre** (`:179`) — **fake_input non può
produrre uno scatto discreto**. È la ragione tecnica per cui krfb scorre male su Wayland.

---

## 8. Output, geometria e risoluzione dinamica

### 8.1 ⛔ Un output virtuale non si ridimensiona

È il risultato più costoso di questo studio. Quattro barriere, tutte **[R]**:

1. **il modo è immutabile**: `OutputMode::m_size` e `m_refreshRate` sono `const`
   (`core/output.h:127-128`);
2. **l'elenco dei modi non viene mai riscritto** per un output virtuale: `DrmVirtualOutput` lo fissa
   nel costruttore (`drm_virtual_output.cpp:37-40`), `VirtualOutput` in `init()`. Le sole
   riscritture a runtime sono nei backend annidati e nei connettori DRM veri;
3. **`kde_output_management_v2` può solo *scegliere* un modo esistente**: la richiesta prende un
   `wl_resource` di `kde_output_device_mode_v2`, cioè un oggetto già annunciato
   (`outputmanagement_v2.cpp:122-142`). Non esiste una richiesta «misura arbitraria» — e libkscreen
   è lo stesso protocollo con un cappotto, quindi non è una via alternativa;
4. e se anche ci fosse un secondo modo, **su DRM verrebbe ignorato**: `Output::applyChanges()` non
   tocca mai `currentMode` (`core/output.cpp:517-543`).

**Non esistono** [✗]: `org.kde.KWin.VirtualOutputs` (c'era in KWin 5), una variabile `KWIN_*` che
crei output, una richiesta di resize nel protocollo screencast. `VirtualBackend::setVirtualOutputs()`
esiste ma i suoi **unici chiamanti sono gli autotest**.

> ### ✅ MISURATO — misure M7 e M11
>
> **[M] 8 agosto 2026.**
>
> **M7a — `stream_virtual_output` con `--virtual` non funziona**, come diceva la lettura del codice:
> `KWin ha rifiutato: Could not find output`. Verificato, e senza sorprese.
>
> **M11 — le misure assurde**: `0x0`, `-1x-1`, `1x1`, `16384x16384`, `99999x99999` → **tutte
> rifiutate con la stessa riga** (`Could not find output`) e **KWin resta vivo dopo tutte e cinque**.
> ⚠ Ma il rifiuto arriva perché *manca l'output virtuale*, non perché KWin **validi** le misure:
> quindi **la validazione resta non misurata**, e non è misurabile con `--virtual` — servirebbe
> `--drm`, che §5.2 ha escluso. Chi un giorno girasse su KWin ≥ 6.8 la rifaccia.
>
> **M7b — quanto costa mettere in piedi un flusso**: dal collegamento al socket al nodo PipeWire
> annunciato, **65, 65 e 67 ms** su tre giri consecutivi. È la componente fissa del «buco» del
> ripiego «chiudi e rifai» (§8.3); a quella va aggiunto il tempo di ricreare l'output, che su
> `--virtual` non si può misurare perché l'output non si crea affatto.

### 8.2 Il paradosso: tutto il resto c'è già, ed è identico a Mutter

**[R]** `ScreenCastStream::resize()` (`screencaststream.cpp:672-682`) fa
**`pw_stream_update_params`** sullo stesso nodo, ed è chiamata **alla fine di ogni fotogramma**
confrontando `m_source->textureSize()` (`:669`). Il consumatore vede solo un
`param_changed(SPA_PARAM_Format)`, poi i buffer nuovi. **Se l'output potesse cambiare modo, lo
stream lo seguirebbe da solo** — è precisamente la meccanica che la fase 6 ci ha dato su GNOME. E
funziona già oggi per gli **output reali**: se l'utente cambia risoluzione a un monitor mentre lo
catturiamo, lo stream si adegua.

Manca un pezzo minuscolo: un `DrmVirtualOutput::resize()` modellato su `WaylandOutput::resize()`
(`wayland_output.cpp:293-303`) più una richiesta nel protocollo. **Una dozzina di righe upstream.**

> ## ✅ E QUELLE RIGHE SONO GIÀ STATE SCRITTE — nove giorni prima di questo studio
>
> *[I] `kwin!7932` «screencast: Resizable Virtual Monitors», **unita il 29 luglio 2026** (commit
> `452707eb`, milestone **6.8**), con `kpipewire!205` e `krdp!113`.*
>
> **E il modo in cui l'hanno fatto è quello che ci serve.** Non una richiesta nuova nel protocollo —
> quella è stata **proposta e respinta** (`plasma-wayland-protocols!138` + `kwin!9519`, 1–2 luglio
> 2026, chiuse in un giorno) con questa motivazione di David Edmundson: *«We have this over pipewire
> […] Which is better because: things work the same in gnome; sandboxed clients using the portal can
> resize it»*. Il meccanismo scelto è **la negoziazione PipeWire**: il consumatore propone un
> `SPA_POD_CHOICE_RANGE_Rectangle` e **KWin segue la misura dello stream**, con i limiti 200×200 …
> 10000×10000.
>
> **Cioè: è esattamente il codice della nostra fase 6**, e il lato consumatore sono tre righe.
>
> ⚠ **Ma è la 6.8, cioè ottobre 2026**: su Trixie (6.3.6) non c'è, e non c'è nemmeno su sid. Da cui la
> conseguenza operativa, che vale più del fatto: **il ridimensionamento su KDE non è una funzionalità
> perduta, è una che arriva** — e il nostro codice va scritto **nella forma della negoziazione**, che
> è quella che diventa giusta da sé quando l'utente aggiorna. La strategia (A) resta il ripiego per
> le versioni che non ce l'hanno, non la strada principale.
>
> Da tenere d'occhio, perché è il tavolo su cui chiedere quel che ci manca:
> `plasma-wayland-protocols!130`, **una versione 2 del protocollo di cattura**, in bozza da marzo 2026.

### 8.2-bis ⛔ La guardia obbligatoria: senza, la rinegoziazione si morde la coda

*Dal rapporto 16 §1.5, e non è una nostra deduzione: è un difetto **trovato da altri** durante la
revisione di `kwin!7932`, cioè proprio il lavoro che porterà il ridimensionamento in 6.8.*

**[I]** Nick Haghiri, 3 luglio 2026, sulla richiesta di merge di KWin:

> *«Resizing re-emits `outputsQueried()`, which triggers a full output reconfiguration, which can
> cause the stream to renegotiate again and call back into `resize()`. … this results in repeatedly
> tearing down and recreating the capture pipeline. Symptoms: the `ScreencastLayer` gets
> destroyed/recreated many times per session, PipeWire toggles `streaming ↔ paused` repeatedly, and
> video freezes intermittently.»*

La cura, nel codice unito ([C] `outputscreencastsource.cpp:170-181`), è **una riga**:

```cpp
void OutputScreenCastSource::resize(const QSize &size)
{
    if (m_output->pixelSize() == size) {   // ← senza questo, ciclo infinito
        return;
    }
    m_output->resize(size);
}
```

> ### ✅ E L'INPUT È STATO SCRITTO E PROVATO — 8 agosto 2026, voce 2
>
> *Le quattro differenze di §7.2 sono tutte nel codice, e tutte e quattro hanno una riga di banco.*
>
> | | Esito |
> |---|---|
> | `connectToEIS(7)` da REMOTIX | ✅ **concesso**, gettone 1, nessun permesso chiesto. ⚠ Il descrittore viaggia in una **lista a parte**: il tipo `h` porta solo un indice, e chi legge il corpo del messaggio prende uno **zero** — cioè lo standard input, un fd validissimo che punta alla cosa sbagliata |
> | la keymap | ✅ letta da libei: `English (US)`, come su GNOME |
> | la rotella | ✅ **scatti discreti nei due versi**, misurati. Il valore di RDP si passa quasi com'è |
> | le regioni | ✅ trovata per **geometria**: `0,0 1920x1080`, con `mapping-id «assente»` — cioè il criterio per chiave non poteva funzionare, ed è esattamente quel che questo documento prevedeva |
> | `org_kde_kwin_keystate` | ✅ **parla**, e `fetchStates` dà lo stato di partenza. Lo stesso `.desktop` della cattura lo autorizza: è un nome in più, come previsto |
>
> ⛔ **E la conferma che vale di più è negativa**: `EI_EVENT_KEYBOARD_MODIFIERS` non è mai arrivato,
> in nessuna prova. La riconciliazione dei lucchetti scritta per GNOME, su KDE, **non girerebbe** — e
> senza `keystate` sarebbe rimasta lì, scritta e morta, senza che nessun banco se ne accorgesse.

⛔ **E lo specchio vale per noi, che siamo il consumatore.** kpipewire applica la stessa guardia
([C] `pipewiresourcestream.cpp:467-475`): se la misura richiesta è **uguale** a quella già richiesta,
**non si segnala nulla**. Senza quella condizione, ogni cambio di formato del flusso richiama la
nostra richiesta di misura, che richiama un cambio di formato: video che si blocca a intermittenza e
flusso che sfarfalla fra `streaming` e `paused`.

> ⚠ **Perché conta adesso**: l'utente ha deciso (8 agosto) che il ridimensionamento si scrive **nella
> forma della negoziazione**, così da accendersi da sé su KWin 6.8. Quella forma **include questa
> guardia**: è la prima riga della funzione, non un'ottimizzazione. Chi la dimentica non vede il
> difetto su Trixie (dove il resize non funziona) e lo scopre **il giorno dell'aggiornamento a 6.8**.

### 8.3 Le strategie residue, e il loro prezzo

| | Che cos'è | Prezzo |
|---|---|---|
| **(A)** chiudere lo stream e rifarlo con la misura nuova | l'unica via completa oggi | ✅ **su KDE non trascina l'input**: EIS e `fake_input` sono indipendenti dallo screencast, quindi **lo stato dei tasti premuti non si perde** — il prezzo che §5.8 di `SPECIFICA.md` accettava a malincuore su GNOME qui non si paga. Restano: un buco video di qualche fotogramma, un **nuovo nodo PipeWire**, e il riposizionamento delle finestre |
| **(B)** output virtuale grande + `stream_region` ricreata | economica: non tocca gli output | dà un **ritaglio**, non un desktop ridimensionato: le finestre massimizzate restano grandi. E la regione è `const`: va ricreata. Serve al *letterboxing*, non a MS-RDPEDISP |
| **(C)** `kde_output_management_v2` su una delle 15 misure comuni | solo per monitor fisici | fuori discussione su una sessione viva |
| **(D)** patch upstream | il pezzo mancante | la strada giusta se la fase 11 diventa un impegno lungo |

⛔ **E c'è un prezzo che nessuna delle quattro evita**: **ridimensionare un output ridispone le
finestre dell'utente**, per due vie [R] — `desktopResized()` → `rearrange()` →
`Window::checkWorkspacePosition()` (massimizzate, fullscreen, edge-keeping, correzione off-screen,
`window.cpp:4052-4253`), e il `PlacementTracker`, la cui chiave **contiene la geometria
dell'output** (`workspace.cpp:296-297`): ogni misura è una chiave, e **tornando a una misura già
vista le finestre vengono teleportate indietro**. In più `updateOutputs()` **annulla un
trascinamento in corso**. KWin stesso, quando subisce ridimensionamenti, li accorpa a un fotogramma
con il commento *«Output resizing is a resource intensive task»* (`wayland_output.cpp:342-349`).

> È lo stesso prezzo che su GNOME ha fatto scartare l'adattamento automatico di risoluzione (§3.1 di
> `SPECIFICA.md`, riquadro della fase 7 in `PIANO.md`). Su KDE quindi **MS-RDPEDISP è una scelta da
> ripesare**, non un lavoro da rifare: si può servire la misura chiesta **alla connessione** e
> accorpare i cambi con l'assestamento di R10-bis, che già abbiamo.

### 8.4 I protocolli degli output, e i vincoli sulla geometria

**[R]** Nessuno dei protocolli di output è dietro un permesso:

| Protocollo | Versione | Che cosa dà |
|---|---|---|
| `kde_output_device_v2` | **11** | leggere tutto: geometria, misura fisica, modi, scala, EDID, `enabled`, uuid, VRR, HDR |
| `kde_output_management_v2` | **12** | scrivere: `enable`, `mode` (solo esistenti), `transform`, `position`, `scale`, `overscan`, … |
| `wl_output` | **4** | ha `name`/`description`: **è così che si ritrova `"Virtual-remotix"`** |
| `zxdg_output_manager_v1` | 3 | posizione e misura logiche |
| `wlr-output-management` | **assente** [✗] | — |

Vincoli e trappole [R]:

- ⛔ **su DRM `width`/`height` sono pixel**, non unità logiche — l'XML dice «logical» e krfb ci
  casca. **Si passa `scale = 1`**;
- ⛔ **la scala richiesta viene buttata via**: `generateConfig` la rimpiazza con `chooseScale()`
  (`outputconfigurationstore.cpp:507`, `607-656`), che su un `physicalSize` pari ai pixel dà sempre
  1.0;
- larghezza e altezza **pari** non sono richieste da KWin, ma le richiede il codificatore 4:2:0:
  vincolo nostro;
- ✅ **il metro dichiarato dal client Android non può arrivare a KWin**: `stream_virtual_output` non
  ha un argomento di misura fisica, e `DrmVirtualOutput` impone `physicalSize = size`. Anche se
  arrivasse, `chooseScale()` è difeso (`< 3 mm` → scala 1, con il commento *«these are all caused by
  the screen mis-reporting its size»*) e la scala è limitata a `[1.0, 3.0]`. Il filtro sul DPI di
  `misura.c` resta comunque necessario **per il nostro lato** (la superficie EGFX e il codificatore).

---

## 9. Gli appunti: più facili che su GNOME

**[R]** La via è **`zwlr_data_control_manager_v1` versione 2** (`wayland_server.cpp:386`), e
**non è in lista nera**: nessun permesso, nessun `.desktop`. `ext_data_control_v1` non esiste in
6.3.6 [✗], e il portale RemoteDesktop di KDE dichiara `clipboard_enabled: false`
(`remotedesktop.cpp:264`) — la via GNOME (la clipboard dentro la sessione di controllo) **non ha
equivalente**, e non serve.

**Leggere**: `get_data_device(seat)` → il server manda **subito** `data_offer` + gli `offer(mime)` +
`selection`; poi `receive(mime, fd)` e si legge fino a EOF, mentre il proprietario scrive.
⚠ Un `offer(mime)` può arrivare **dopo** `selection`: l'elenco dei tipi non è completo all'istante
dell'evento.

**Scrivere**: `create_data_source()` → `offer(mime)` → `set_selection(source)`. ⚠ **Un source si usa
una volta sola** (`error_used_source`), e quando qualcuno legge riceviamo `send(mime, fd)` con KWin
che **chiude subito la propria copia del fd**: scrivere e chiudere è a nostro carico, e **senza
bloccare** il loop (una pipe da 64 KB con un consumatore lento ci blocca).

**Le tre asimmetrie di Mutter, riposte a KWin** [R]:

| La domanda | Mutter | **KWin** |
|---|---|---|
| Chi si ricollega riceve un annuncio? | **no**, e ci è costato | ✅ **sì**: `registerDataControlDevice()` manda subito selezione e primary selection (`seat.cpp:228-229`) — ⚠ se non c'è selezione manda un annuncio **vuoto**, non l'assenza di annuncio |
| L'annuncio torna indietro dopo una nostra scrittura (eco)? | sì | ⛔ **sì**: `setSelection()` cicla su **tutti** i data control device, **compreso l'originatore** (`seat.cpp:1257-1259`), e il filtro «stessa selezione» non aiuta perché ogni source è nuovo |
| Esiste un interruttore irreversibile (`DisableClipboard`)? | **sì**, e ci ha ucciso gli appunti | ✅ **no** [✗]: la clipboard non appartiene a una sessione |

⛔ **Due trappole dell'eco**, da evitare per costruzione: leggere l'eco significa farsi chiedere i
dati **dal proprio source** (stallo, se la lettura è sincrona); girarlo al client RDP significa
entrare nel ciclo. Il criterio robusto: **ignorare il primo `selection` che arriva dopo un nostro
`set_selection`**, confrontando anche la lista dei tipi. **[?]** Nel protocollo non c'è un serial né
un'attribuzione.

**I due coinquilini** [R]:

- **klipper** *rimette* l'ultimo elemento quando la clipboard si svuota, marcandolo
  `application/x-kde-onlyReplaceEmpty` (`klipper/systemclipboard.cpp:403-411`): se distruggiamo il
  nostro source senza sostituirlo, **il contenuto precedente torna**. E si difende dai cicli con
  **10 cambi al secondo** (`:50`): non superarli. ⚠ E KWin ha un aggiramento dedicato
  (`seat.cpp:200-226`) che **annulla in silenzio** un `set_selection` che dichiari quel tipo mime:
  **non usarlo mai**;
- **la sponda Xwayland**: X11 → Wayland è incondizionato; **Wayland → X11 solo quando una finestra
  Xwayland è attiva** (`xwayland/clipboard.cpp:88-100`, con il commento *«shield against snooping X
  windows»*), e si recupera al primo `windowActivated`. ⛔ **Una prova con `xclip` fallisce senza
  errore**: è la forma di banco verde su difetto vivo che `LEZIONI.md` §2.2 elenca.

### 9.1 ✅ SCRITTA E PROVATA — 8 agosto 2026, `prove/fase11-appunti.sh`

```
OK  la sessione ha copiato qualcosa: 6 tipi
OK  il client ha «SESSIONE-VERSO-CLIENT-àèìòù-ok»
OK  la sessione incolla «CLIENT-VERSO-SESSIONE-àèìòù-ok»
OK  nessun ciclo (2 annunci veri, 1 eco buttata)
OK  l'eco e' arrivata ed e' stata riconosciuta
guasti: 0
```

Sta in **`src/appunti_wlr.c`**, e il nome dice `wlr` non `kwin` di proposito: il protocollo è di
wlroots, quindi il file serve già anche i compositori di XFCE e LXQt (§3.8 di `SPECIFICA.md`). La
porta `appunti.h` è rimasta una, con `appunti.c` ridotto a smistamento e la strada di Mutter spostata
in `appunti_mutter.c` — la stessa forma di `compositore.c`.

> ### ⛔ La guardia contro l'eco: il criterio di §9 era più debole del necessario
>
> «Ignorare il **primo** `selection` dopo un nostro `set_selection`» è una regola a tempo, e le
> regole a tempo si sbagliano quando due cose capitano insieme. Il criterio scritto è invece **di
> stato**: si ignora un annuncio se **la sorgente è ancora nostra** *e* i tipi coincidono.
>
> Regge perché l'ordine lo garantisce KWin: quando qualcun altro copia, è lo stesso `setSelection` a
> mandare prima `cancelled` alla vecchia sorgente e poi l'annuncio ai device. A quel punto «la
> sorgente è nostra» è già falso e l'annuncio passa. Nessun contatore, nessuna finestra temporale.

> ### ⛔ `POLLHUP` vale come «pronto», e trattarlo da guasto costa una diagnosi sbagliata
>
> *[M, 8 agosto 2026 — il primo giro del banco]*
>
> Chi possiede gli appunti scrive e chiude. Con dati corti la `poll` può tornare con **`POLLHUP` e
> basta**: i byte sono nel tubo, ma nessuno li ha ancora letti. Il codice guardava solo `POLLIN` e
> concludeva «non ha risposto» — **subito**, scrivendo a registro una scadenza di cinque secondi
> *che non era mai passata*. Il registro diceva `entro 5000 ms` a tre secondi dall'annuncio, e quel
> numero impossibile è stato l'unico indizio.
>
> In lettura `POLLHUP` è un esito (la `read` che segue dirà zero); in scrittura no, lì vuol dire che
> chi incollava se n'è andato.

⚠ **E l'annuncio non si consegna quando arriva `selection`**: un `offer(mime)` può arrivare dopo, e
un elenco monco fa incollare la cosa sbagliata senza che nessuno se ne accorga. La pompa fa un giro
completo — `wl_display_roundtrip` — e *poi* consegna.

---

## 10. Il sistema attorno: energia, blocco, credenziali, audio

### 10.1 ✅ La cura di §3.4-bis funziona, e Plasma **nasconde**

**[R]** `sessionmanagementbackend.cpp:108-121` accende la voce di menu solo se logind risponde
`"yes"` o `"challenge"`; i valori di difetto sono `false`, e i consumatori usano `visible:` /
`addIfValid`. Quindi `sleep.conf` + la regola polkit di §3.4-bis di `SPECIFICA.md` **valgono
identiche su KDE**, e in dote arriva che `canSuspend=false` porta l'auto-sospensione di powerdevil a
`NoAction` da sé.

⛔ **Ma la regola polkit va scritta `no`, non *auth_admin***: `"challenge"` **mostra** la voce.

### 10.2 ⛔ Su KDE c'è un secondo comandante dell'inattività, e il blocco si accende da sé

Due difetti di configurazione che una sessione remota incontra dopo pochi minuti, entrambi **[R]**:

| | |
|---|---|
| powerdevil ha **«spegni lo schermo dopo 10 minuti» acceso per difetto**, indipendente dalla cura di logind | `powerdevilsettingsdefaults.cpp:61-80` |
| `kscreenlockerrc [Daemon] Autolock` vale **`true`** con `Timeout=5` minuti | `kscreenlockersettings.kcfg:8-18` |

**La via precisa per inibire**: `org.kde.Solid.PowerManagement.PolicyAgent.AddInhibition(types=4, …)`
— dove `4` è `ChangeScreenSettings` e **implica** `InterruptSession`
(`powerdevilpolicyagent.cpp:737-745`); nessun controllo di permesso, effetto dopo **5 s**, si
rilascia da sé alla caduta del nome D-Bus. ⚠ La via freedesktop
(`org.freedesktop.PowerManagement.Inhibit`) mappa **solo** su `InterruptSession`
(`powerdevilfdoconnector.cpp:84-93`): **non ferma lo schermo.**

⛔ **E a blocco attivo la nostra inibizione viene ignorata** (`powerdevilpolicyagent.cpp:509`):
spegnere il locker non è una comodità, è **una dipendenza**. La leva è
`kwin_wayland --no-lockscreen` (`main_wayland.cpp:550-556`) — che le unità systemd stock **non
passano**, perché su Wayland il blocco è di KWin (`ksmserver/main.cpp:171-175`).

Due note che ridimensionano il problema, entrambe **[R]**: la cattura **non si ferma** al blocco (ma
la scena rende il lockscreen, quindi si vedrebbe **l'immagine di blocco**), e **l'input iniettato
raggiunge il greeter** — cioè l'utente remoto può sbloccare digitando. Il blocco è una seccatura,
non un'esclusione. E l'input iniettato **azzera i timer di inattività** (EIS →
`simulateUserActivity`), quindi una sessione usata non si blocca.

### 10.3 ⛔ Senza nessun output, KWin si autoblocca

**[R]** `workspace.cpp:1216-1223`: con zero uscite abilitate il Workspace monta un
`PlaceholderOutput` con render loop inibito **e un filtro che inghiotte tutto l'input**. **Lo schermo
virtuale è una precondizione, non un risultato**: fra la morte di uno stream e la creazione del
successivo (strategia (A) di §8.3) si passa da lì.

### 10.4 Le altre voci, in breve

| | **[R]** |
|---|---|
| **kwallet** | nessuno lo avvia in questo albero; il rischio di un dialogo di credenziali in una sessione non presidiata resta da misurare **[?]** |
| **Il sink audio** | **zero righe di Plasma toccano i dispositivi audio**, e la lista di preferenze di Phonon è stata svuotata (`kdeplatformplugin.cpp:128-149`). La scelta di §7.5 di `REFERENCE.md` — creiamo noi il sink virtuale e ne catturiamo il monitor — **si riusa identica**. Conferma finale: una misura, non un lavoro |
| **Notifiche che compaiono da sole** | ⛔ il modulo kded `devicenotifications` (autoload `true`) fa comparire *«Display Detected/Removed»* **a ogni schermo virtuale che creiamo o distruggiamo** (`devicenotifications.cpp:290-351`) — cioè, con la strategia (A), **a ogni cambio di risoluzione** |
| **Permessi D-Bus** | **nessun controllo** su nessuna interfaccia di sistema di KWin/Plasma/powerdevil, salvo `ScreenShot2` e `PlasmaShell.evaluateScript` |
| ~~**Rischio da chiudere per primo**~~ **misura M12, corretta l'8 agosto** | il `QMessageBox` modale *«Plasma Failed To Start»* c'è (`shell/main.cpp:176-179`), **ma non è il primo rischio, e non scatta al primo fallimento.** Rileggendo `shell/main.cpp:160-181`: al primo errore di contesto OpenGL plasmashell **scrive `SceneGraphBackend=software` in `kdeglobals` — `Global | Persistent` — e si riavvia da sé** (`QProcess::startDetached`); il dialogo compare **solo al secondo giro**, se anche il ripiego software fallisce. ⛔ **Il rischio vero è quindi un'altra cosa: una sessione avviata senza GPU lascia una configurazione permanente** che rende software il rendering anche quando la GPU torna. [M] Nella sessione misurata, **con** la GPU: zero righe `Open GL context could not be created` e **nessun `SceneGraphBackend` scritto**, come deve essere. ⚠ La riproduzione del caso «senza GPU» non è stata fatta: negare la GPU al solo compositore non basta (plasmashell è un'altra unità), servirebbe negarla a tutta la sessione |
| **Le regole di sessione** (le nove combinazioni di §3.4) | non dipendono dal desktop: logind è lo stesso. **Niente da rifare**, salvo verificare che il *tipo* di sessione si comporti come su GNOME **[?]** |

### 10.5 ⛔ Il cursore del volume non governava niente — e non era colpa di KDE

*[M, 8 agosto 2026, aperto dall'utente: «se abbasso il volume l'audio resta sempre alto; in pratica
audio del server e del client sono scollegati»]*

Il sink virtuale lo creiamo noi (§7.5 di `REFERENCE.md`) e ne catturiamo il monitor. **In PipeWire
il volume di un nodo si applica a valle della presa del monitor**, e la proprietà che sposta la
presa — `monitor.channel-volumes` — vale **`false`** se non la si chiede. Chi crea il sink con
`pactl load-module module-null-sink` non se ne accorge mai, perché `pipewire-pulse` la mette da sé
per compatibilità con PulseAudio, dove il monitor è sempre stato a valle del volume. Noi il sink lo
creiamo a mano, con `pw_core_create_object`, e ce la scordavamo.

La misura, tono a 440 Hz di ampiezza nota (25,9 % del fondo scala), letto sul monitor:

| volume del sink | `monitor.channel-volumes` **non chiesta** (com'era) | chiesta (sink di `pactl`) |
|---|---|---|
| 100 % | 25,39 % | 25,39 % |
| 25 % | **25,39 %** | 0,40 % |
| 10 % | — | 0,03 % |
| 0 % | **25,39 %** | 0,00 % |

I numeri della colonna di destra non sono «quasi giusti»: sono **esattamente** la curva cubica di
PulseAudio (0,25³ = 1,56 %, e 25,9 × 0,0156 = 0,40). La colonna di sinistra è piatta: il volume non
arriva, **mute compreso**. Nella sessione viva il nodo era a `channelVolumes 0.0` e `mute true`
mentre il client riceveva il segnale intero.

✅ **Cura**: `"monitor.channel-volumes", "true"` fra le proprietà del sink, in `suono.c`.

> ⚠ **Il verso conta, ed è il motivo per cui questo cursore è l'unico che può funzionare.** RDP ha
> un solo PDU di volume, `SNDC_SETVOLUME`, e va **dal server al client** — noi lo mandiamo a fondo
> scala alla scelta del formato (`altoparlante.c`). **Non esiste il verso opposto**: un client non
> ha modo di dire al server «abbassa». Quindi l'unico cursore che governa davvero il livello è
> quello che si vede **dentro** la sessione, e va fatto funzionare.

### 10.6 Le voci di menu che non possono funzionare, tolte dal menu

*[chiesto dall'utente, 8 agosto 2026: «sarebbe meglio nascondere le voci di *switch user* e *lock*
(anche se non funzionano, ed è il comportamento corretto)»]*

In una sessione servita da REMOTIX **«Blocca schermo» e «Cambia utente» non possono funzionare**, ed
è giusto così: il locker lo spegniamo noi con `--no-lockscreen`, perché a blocco attivo powerdevil
ignora le inibizioni (§10.2), e cambiare utente vorrebbe dire un display manager che qui non c'è. Ma
**una voce che non fa niente è peggio di una voce che manca**: chi la preme conclude che il server è
rotto.

La leva è **KIOSK**, cioè `KAuthorized`. I nomi delle azioni non si indovinano, sono quelli che
Plasma interroga davvero:

| che cosa governa | azione | dove |
|---|---|---|
| `SessionManagement::canLock()` | `lock_screen` | `libkworkspace/sessionmanagement.cpp:126-129` |
| `SessionManagement::canSwitchUser()` | `start_new_session` | `libkworkspace/sessionmanagement.cpp:121-124` |
| `SessionsModel::canSwitchUser()` | `switch_user` | `components/sessionsprivate/sessionsmodel.cpp:45` |

⚠ **`switch_user` e `start_new_session` servono tutti e due**: il primo governa l'elenco delle
sessioni, il secondo il pulsante. Toglierne uno lascia mezza interfaccia.

Il file si scrive in `$XDG_RUNTIME_DIR/remotix/xdg/kdeglobals` e la cartella si mette **in testa a
`XDG_CONFIG_DIRS`**, dove KConfig la legge come configurazione di *sistema*:

```ini
[KDE Action Restrictions][$i]
action/lock_screen=false
action/start_new_session=false
action/switch_user=false
```

> ⚠ `[$i]` non è decorativo: senza, il `kdeglobals` dell'utente — che sta più in alto — rimette le
> voci al loro posto.
>
> ⚠ `/etc/xdg` **si tiene in coda, non si sostituisce**: da lì viene `menus/plasma-applications.menu`,
> cioè proprio il file che `XDG_MENU_PREFIX` va a cercare. Sostituirlo spegnerebbe la cattura per la
> strada di §3.3-bis.
>
> ⛔ E **`logout` non si tocca**: è la strada con cui si chiude la sessione, e quella su cui poggia
> la sentinella di uscita.

Non si scrive in `~/.config`: quel che imponiamo vale per la sessione servita, e non deve cambiare
la configurazione che l'utente si è scelto né sopravvivere alla macchina. Conseguenza: **ha effetto
dal prossimo avvio di sessione**, non su una sessione già viva.

---

## 11. `kpipewire`: il codice che fa il nostro stesso lavoro

È il pezzo più direttamente trasferibile di tutto KDE: consuma PipeWire e **codifica in H.264**.

### 11.1 Danno e sincronizzazione: **non li fa**, e il perché è la risposta

**[R]** `SPA_META_VideoDamage` è chiesto **solo** se qualcuno chiama `setDamageEnabled(true)`, e
**nessuno lo chiama** in tutto l'albero (`pipewiresourcestream.cpp:68`, `369-379`; zero chiamanti in
`src/` e `tests/`). Quando arriva, l'unico consumatore è un **overlay di debug** che disegna i
rettangoli in rosso (`pipewiresourceitem.cpp:295-310`). Di sincronizzazione **non c'è niente**: zero
`SPA_META_SyncTimeline`, zero `poll()` su un fd di buffer, zero ioctl, zero `eglCreateSyncKHR`, zero
`glFinish` [✗].

**E non è una svista**: è il lato consumatore di quel che §4.6 e §4.8 dicono del produttore — KWin
ridisegna il fotogramma intero e si sincronizza lui. Il danno, su KDE, **è un suggerimento**.

> ✅ **Conclusione che vale per tutto il progetto**: il difetto delle schermate alternate (R29) **è di
> Mutter, non del modello PipeWire**. E la cura che abbiamo scritto — la superficie di accumulo — su
> KWin non serve.

### 11.2 Le tre cose da copiare

1. ⛔ **Per la codifica in GPU si chiede solo `DRM_FORMAT_MOD_LINEAR`** (`vaapiutils.cpp:119-135`):
   RadeonSI **rifiuta** i buffer con DCC, iHD li **accetta e poi forza LINEAR internamente** — cioè
   accetta e sbaglia in silenzio, la nostra forma di guasto preferita (R27, R30). Giorni risparmiati.
2. **Il contesto VAAPI non si crea: lo si fa creare al grafo di filtri.**
   `hwmap=mode=direct:derive_device=vaapi,scale_vaapi=format=nv12:mode=fast`, `hw_device_ctx`
   assegnato a **ogni** filtro *prima* di `avfilter_graph_config()`, e poi lo si prende dal
   buffersink con `av_buffersink_get_hw_frames_ctx()` (`h264vaapiencoder.cpp:89-97`, `151`). Cura
   preventivamente il terzo caso di R30 — l'`h264_vaapi` che si è aperto con un contesto proprio.
3. **Quando un modificatore fallisce non si spegne il DMA-BUF**: si toglie *quel* modificatore e si
   rinegozia, rientrando nel thread giusto con `pw_loop_add_event`/`pw_loop_signal_event`
   (`pipewiresourcestream.cpp:261-273`). È anche il meccanismo per cambiare strada a caldo senza
   rifare la cattura — cioè la nostra R30, scritta da altri.

Regalo misurato da altri, due ore per provarlo: `flags +mv4` e `-flags +loop` su **tutti** gli
encoder, con il commento *«disable motion estimation … speeds up encoding by an order of
magnitude»*.

### 11.3 Che cosa kpipewire **non** fa

| | |
|---|---|
| **controllo del bitrate** | ⛔ **assente** per H.264: mai `bit_rate`, mai `rc_mode`. È **lo stesso vuoto di `gnome-remote-desktop`** (§9.1) e di R31: su quel punto REMOTIX resta solo, e ora la solitudine è confermata da due riferimenti invece di uno |
| ridimensionamento a caldo | assente |
| cursore su DMA-BUF | non composto |
| `max_b_frames` | **0 in ogni encoder** — conferma indipendente di R11 |

**Quattro difetti da non copiare** [R]: `stride*height*4`, un `ceil` su una divisione intera, la
cadenza in aritmetica intera con divisione per zero, `mapoffset` ignorato.

**Riusabile da un programma in C**, riscrivendo solo i tipi Qt: `queryDmaBufModifiers`,
`buildFormat`, la costruzione dell'`AVDRMFrameDescriptor`, e tutto `vaapiutils.cpp`. **Da
riscrivere**: il percorso software (tre copie per fotogramma), il bitrate, il danno, il cursore.

---

## 12. I riferimenti di KDE, e quanto valgono

### 12.0 ⭐ `KRdp` — il riferimento vero, e lo studio l'aveva mancato

> ⛔ **Correzione del 7 agosto 2026, sera.** La prima stesura di questo documento diceva
> *«altre tracce di RDP in KDE: nessuna»*. **Era falso**, e per un errore di metodo che vale la pena
> registrare: la ricerca era stata fatta **dentro i repository clonati**, e `krdp` non era fra quelli.
> Cercare in casa propria non è cercare. Lo ha trovato una domanda dell'utente — *«su KDE qualcuno ha
> affrontato i problemi prima di noi: xrdp. Come fa con KWin?»* — e la risposta è che xrdp non
> c'entra (§12.3), ma **qualcun altro sì**.

**Che cos'è.** `KRdp` è il server RDP di KDE: **C++ su FreeRDP**, con `kpipewire` per i pixel, ed è
quel che Plasma 6.2+ presenta come *«Condivisione del desktop (RDP)»* nelle Impostazioni di sistema.
**4 222 righe** nella 6.3.6 di Trixie, 5 877 nel master. Cioè: stessa libreria RDP, stesso
compositore, stessi client, e un ordine di grandezza in meno di `gnome-remote-desktop` — che lo rende
leggibile per intero in una sessione.

**La conferma che pesa più di tutte** — il suo file `.desktop`, `server/org.kde.krdpserver.desktop.cmake`:

```ini
[Desktop Entry]
Type=Application
Exec=@CMAKE_INSTALL_PREFIX@/bin/krdpserver
NoDisplay=true
X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input,zkde_screencast_unstable_v1
```

**La via del permesso di §3 non è una nostra deduzione: è quel che fa il server RDP di KDE**, per la
cattura *e* per l'input, in tre righe e senza un dialogo.

**Come è fatto** — tutto **[R]**, sul master salvo dove indicato:

| | |
|---|---|
| **Dove gira** | `server/app-org.kde.krdpserver.service.in`: `Type=exec`, `After=plasma-core.target`, **`WantedBy=plasma-workspace.target`** — cioè **dentro** una sessione Plasma già in piedi, come servizio d'utente. ⛔ **Non avvia la sessione**: è la differenza strutturale con REMOTIX, e il motivo per cui KRdp non risolve la nostra §6 |
| **La cattura** | due strade, e ⛔ **quella predefinita è il portale**, non i protocolli di Plasma: la diretta si sceglie con **`--plasma`** (`server/main.cpp:128`), e **l'unità systemd non lo passa**. La diretta è `PlasmaScreencastV1Session.cpp:173-199` (`createVirtualMonitorStream`, `createOutputStream`, `createWorkspaceStream`, tutte con cursore `Metadata`) |
| **La misura** | `server/main.cpp:49-52`: **`--virtual-monitor 1920x1080@1`**, opzione a riga di comando. La misura la decide **chi avvia il servizio**, non il client. ⛔ **E senza `--plasma` non può funzionare**: KRdp chiede al portale il tipo di sorgente «virtuale» (4), che `xdg-desktop-portal-kde` **non annuncia**, e il cui dialogo non costruisce alcun elenco (`screenchooserdialog.cpp:148-231`) — pagina vuota. Cioè: **lo schermo virtuale esiste solo sulla strada diretta** |
| **L'input** | ⛔ **`fake_input`, non EIS**: `PlasmaScreencastV1Session.cpp:26-35, 164-165` lega `org_kde_kwin_fake_input` **v4** e chiama `authenticate("krdpserver", "")`. Non usa il backend EIS di KWin |
| **La keymap** | ✅ **la legge dal `wl_seat`**, essendo client Wayland: `wl_keyboard.keymap` → `xkb_keymap_new_from_string` (`:121-143`). Poi `keycodeFromKeysym()` cerca il tasto che produce il simbolo e **applica i livelli** — livello 1 → `KEY_LEFTSHIFT`, livello 2 → `KEY_RIGHTALT` (`:68-89`, `:265-278`), con `EVDEV_OFFSET = 8`. È **il nostro percorso Unicode**, scritto da loro senza libei |
| **I due codec** | ✅ **la nostra stessa struttura** (R3): `VideoStream.cpp:635-656` — H.264 se il client dichiara AVC **e** YUV420, altrimenti **RemoteFX Progressive** (`progressive_context_new(TRUE)`). `KRDP_DISABLE_H264` forza il ripiego. ⚠ Il profilo è **`H264Baseline`** (`:273`), non *Constrained High* come R11 |
| **La codifica** | delegata a `kpipewire`: `PipeWireEncodedStream` con `EncodingPreference::Speed`, `ColorRange::Full`, `quality` 0–100 (`--quality`), `maxFramerate`, `maxPendingFrames`. Nessun bitrate dichiarato — coerente con §11.3 |
| **Il regolatore** | ✅ **lo stesso della nostra fase 7**: `NetworkDetection::rttChanged` → `updateInFlightWindow()`, `hasInFlightCapacity()`, coda dei fotogrammi e un thread di spedizione (`VideoStream.cpp:376-398`). L'ultimo commit del master è *«smooth the RTT used for the in-flight window»* |
| **Il danno** | ✅ **lo usa**, al contrario di krfb: `setDamageEnabled(true)` sul percorso Progressive (`:299`), accumulo del danno fra i fotogrammi in coda (`:456-466`) e conversione in `REGION16` di FreeRDP (`:201-238`) — con i bordi **esclusivi**, `right = rect.right() + 1`: la nostra R5, confermata da un terzo |
| **Il ridimensionamento** | ⚠ `DisplayControl.cpp` **esiste solo nel master**: `MaxNumMonitors = 1`, factor 8192 (identici ai nostri), accetta **solo** `NumMonitors == 1`, e il layout arrivato va a **`VideoStream::setRequestedSize`** (`server/SessionController.cpp:58`) → cioè **all'encoder**, non all'output. ⛔ **Nemmeno KRdp ridimensiona lo schermo virtuale**, e nella 6.3.6 di Trixie **non ha il ridimensionamento affatto** (`kpipewire` 6.3.6 non ha nemmeno `setRequestedSize` [✗]) |
| **La sicurezza** | `RdpConnection.cpp:426-428`: `NlaSecurity = !usePam`, **`TlsSecurity = usePam`** — cioè **NLA per difetto, e TLS puro quando si autentica con PAM**, che è la nostra scelta (§3.6). E PAM c'è davvero (`pam_appl.h`, `:88-134`) |
| **Le capacità** | `ColorDepth = 32`, `SupportGraphicsPipeline`, `NetworkAutoDetect = true`, e rifiuti espliciti se mancano pipeline grafica o pointer cache (`:573-584`): le nostre §3.2 e §3.3 |
| **Una trappola che noi non avevamo** | `VideoStream.cpp:575-588`: *«Windows clients (mstsc) send CapsAdvertise **twice**»* — e KRdp tratta il secondo come **reset del canale**, distruggendo le superfici e rifacendole. La nostra R2 dice che un secondo `CapsAdvertise` è lecito solo da 10.3; questo dice **che cosa farne** |

**Che cosa non risolve per noi**, e va detto: **non avvia la sessione** (vive dentro Plasma, quindi la
nostra §6 resta interamente nostra), **non ridimensiona** (§8 resta aperta), e usa la strada
dell'input **vecchia** — dove noi abbiamo già scritto quella nuova. Non ho ancora letto in dettaglio
`Clipboard.cpp`, `Cursor.cpp`, `NetworkDetection.cpp` e `PortalSession.cpp`: sono **la prossima
lettura**, e sono tutti pezzi che ci servono.

### 12.0-bis ⛔ I difetti di KRdp da non ripetere — l'elenco che vale più del codice

*Riversato dai rapporti 12 §6.4, 14 §2.2 e 15 §8.1-8.2 l'8 agosto 2026 (passo 0 del piano di lavoro).
Il ramo di sviluppo di KRdp ne ha corretti diciotto rispetto alla 6.3.6 di Trixie: **ogni riga
corretta è un difetto che noi non dobbiamo scrivere**. Qui stanno i quattordici che ci riguardano,
in ordine di quanto morderebbero noi.*

| ⛔ | Il difetto | Dove, nella 6.3.6 | Che cosa ci insegna |
|---|---|---|---|
| **1** | **Il client senza AVC420+YUV420 veniva *disconnesso***: `qCWarning("Client does not support H.264…"); return CHANNEL_RC_INITIALIZATION_ERROR` | `VideoStream.cpp:308-313` | ⭐ **conferma la nostra R3 come necessità, non come lusso**: senza RemoteFX Progressive il nostro client Android non si collegherebbe affatto |
| **2** | **`RDPGFX_SURFACE_COMMAND` riempita a metà**: 10 campi su 13, gli altri **spazzatura di stack** — `contextId` compreso, che per AVC420 deve valere 0 | `:377-392` vs `freerdp/channels/rdpgfx.h:195-210` | **si azzera la struttura** (`= {}`) prima di riempirla. È della stessa famiglia del nostro difetto sul `MONITOR_DEF` (R5) |
| **3** | **Nessun codice di ritorno controllato**: `ResetGraphics`, `CreateSurface`, `MapSurfaceToOutput`, `StartFrame`, `SurfaceCommand`, `EndFrame` — tutti chiamati e ignorati | `:367`, `:376`, `:385`, `:411-414` | ⭐ *«un errore su `CreateSurface` diventa uno schermo nero senza una riga di log»* — **è il modo in cui abbiamo perso tempo noi** |
| **4** | **Nessuna `DeleteSurface`, mai**, e `ResetGraphics` chiamata con superfici vive | `:349-385` | le superfici **si accumulano nel client**. È precisamente quel che la nostra **R6** vieta |
| **5** | **`pendingFrames` (una `QSet`) usata da due thread senza lock** | `:118`, `:333`, `:344`, `:397` | corruzione della tabella hash e `erase` di un iteratore invalido: un crash che arriva a caso |
| **6** | **Nessuna contropressione**: si spediva tutto quel che c'era in coda | `:174-188` | su rete lenta il buffer TCP si gonfia: **secondi** di latenza che non recuperano più |
| **7** | **`queueDepth`/`SUSPEND_FRAME_ACKNOWLEDGEMENT` ignorati** con la finestra in volo attiva | `:677-692` (**anche nel master**) | **blocco eterno**: se il client dice «non aspettare i miei riscontri» e noi aspettiamo, non parte più niente. Quando è sospeso, **la finestra si disattiva** |
| **8** | **Nessun recupero dai riscontri persi** | idem | `totalFramesDecoded` **come pavimento**, e una scadenza per i fotogrammi in attesa |
| **9** | **`close()` chiudeva il canale *prima* di fermare il thread di spedizione**; il distruttore era **vuoto** | `:194-207`, `:143-145` | l'ordine giusto è: **fermare i flussi → aspettare i thread → svuotare le code → distruggere le superfici → chiudere il canale** |
| **10** | **Lo stimatore di cadenza con la condizione sempre falsa**: `(estimate.timeStamp - now) > periodo` con `timeStamp <= now`, cioè differenza **negativa** | `:427-433` | perdita di memoria illimitata **e** una media calcolata su tutta la sessione, che quindi non si adatta più a niente. ⭐ Un difetto che **nessuna prova funzionale trova**: il programma funziona, solo non regola più |
| **11** | **Misura di banda aperta e chiusa attorno a *ogni* fotogramma** | `:353`, `:416` | la misura di banda è un giro di richiesta/risposta: farla 60 volte al secondo **la rende rumore** |
| **12** | **Numero di sequenza `uint32` in un campo a 16 bit**: l'RTT muore dopo **~76 minuti** e l'hash delle richieste cresce senza limite | `NetworkDetection.cpp:69`, `:75`, `:244-252` | contatore **`uint16_t`** con giro esplicito, e **scadenza** delle richieste senza risposta. ⚠ Ed è una prova che va fatta **a 90 minuti**, non a cinque |
| **13** | **La cadenza delle sonde appesa ai risvegli del socket**: a desktop fermo la misura **si spegne** | `RdpConnection.cpp:563` | un timer vero, o un'attesa con **timeout** pari alla cadenza |
| **14** | **La rotella con `angleDelta/120`**, divisione **intera** | `PortalSession.cpp:161` | qualunque scatto sotto una tacca **si perde**. Conferma §7.2: si usa `ei_device_scroll_discrete(±120)` e si passa il valore quasi com'è |

> ⭐ **E il difetto più istruttivo di tutti sta nel rapporto 14 §2.2**: nella 6.3.6 **il verso di
> pressione e rilascio dei tasti era invertito**. È lo stesso punto che nel nostro `input.c:218`
> abbiamo verificato essere giusto (`gboolean premuto = !(flags & KBD_FLAGS_RELEASE)`). Un server RDP
> maturo, dentro KDE, ha spedito per una release un difetto che si vede alla prima parola digitata:
> **la prova sui tre client non è burocrazia.**

### 12.1 `krfb` — per metà, e non per la metà che si spera

`gnome-remote-desktop` era un riferimento pieno: stesso linguaggio, stessa libreria RDP, stesso
compositore, 68 730 righe. **krfb è ~5 000 righe di C++ e parla VNC**, e su questo ramo
⛔ **non apre nemmeno la porta**: `RfbServer::start()` racchiude `rfbInitServer` in
`if (passwordSet())` e torna `true` comunque, e nel percorso normale nessuno chiama `setPasswordSet`
(`rfbserver.cpp:114`). Va letto come **archivio**, non come metro.

**Le tre cose per cui vale** [R]:

1. ✅ **conferma il nostro modello di palco**: un framebuffer per processo, vivo dall'avvio alla
   chiusura, indifferente al connettersi dei client (`rfbservermanager.cpp:113-133`;
   `startMonitor`/`stopMonitor` **vuoti**);
2. **la sequenza dei pixel su KWin in un file solo** (`pw_framebuffer.cpp:125-346`), traducibile in
   C quasi riga per riga se un giorno passassimo dal portale — e la scelta chiave: aprire una
   sessione **RemoteDesktop** e innestarvi `ScreenCast.SelectSources`, che su KDE compra **un solo
   dialogo** per schermo e input e l'accesso alla mega-autorizzazione;
3. **otto difetti reali che possiamo non pagare**, e due sono della famiglia che ci ha già morso:
   il **danno mai negoziato** (`setDamageEnabled` non è chiamato in tutto l'albero, quindi krfb
   accoda **lo schermo intero a ogni fotogramma**), e un `QTimer` a 50 ms che impone **20 fps** —
   cioè un tetto scritto in casa propria, esattamente il difetto dei nostri 18 (R32). Gli altri:
   `buttonMask` passato dove il portale vuole uno `state` 0/1 (`xdpevents.cpp:78` → pulsanti
   incastrati), doppio evento di rotella per scatto, uno scatto che arriva come `delta=±1 px`,
   `||` invece di `&&` nel cursore, pixel fisici dove servono unità logiche, e nessun ascolto della
   fine della sessione.

*(La prima stesura scriveva qui «altre tracce di RDP in KDE: nessuna». Era falso: vedi §12.0.)*

### 12.4 Gli altri due, trovati cercando fuori casa

*[I]/[C], 7 agosto 2026. Sono la prova che il passo zero di `LEZIONI.md` §9 serve: nessuno dei due
stava nei repository che avevo scelto.*

| | |
|---|---|
| **Sunshine** | ha da maggio 2026 un `kwingrab.cpp` (772 righe) che parla **il nostro stesso protocollo diretto**, e che **si scrive da sé il file `.desktop`** con `X-KDE-Wayland-Interfaces` a runtime, aspettando 3 000 ms perché KWin lo veda. È la **terza implementazione indipendente** del cancello di §3, dopo KRdp e krfb: la via del permesso non è più un'interpretazione |
| **Chrome Remote Desktop** | il bug KDE **512620** è stato aperto da un ingegnere Google che sta portando CRD su KDE Wayland. È un quarto riferimento serio, e vale tenerlo d'occhio |

**E una cosa che nessuno fa** [✗]: **`kwin_wayland --drm` senza monitor**. Cercata nel codice, nei
bug, nelle wiki e nei forum: nessun precedente. La misura resta interamente nostra. Due bug
confermano però che **non stiamo aggirando una via ufficiale, perché non ce n'è una**: il **492285**
dice che `startplasma` non inoltra la scelta del backend al compositore (nessuna merge request), e il
**523735**, aperto sei giorni prima di questo studio, **chiede proprio la sessione headless** — e
nessuno l'ha risolta.

**Due regali dal fronte dell'input** [I]: `krdp!217` sta portando KRdp **a libei, rendendolo
obbligatorio** — cioè la strada che abbiamo scelto è la direzione in cui KDE si sta muovendo, e la
loro conversione a `fake_input` diventerà codice morto. E nella discussione di quella merge request
c'è la risposta parziale a una nostra misura aperta: **con libei il verso della rotella è quello di
Wayland**, senza l'inversione che il portale si porta dietro. Più, nel master di KWin,
`EIS_DEVICE_CAP_TEXT` (richiede libeis ≥ 1.6, non ancora disponibile): il giorno in cui arriva, il
nostro giro «carattere → keysym → tasto → livelli» diventa superfluo.

⚠ **E una precisazione sulle versioni**: Debian Trixie ha **krdp 6.3.5-1**, non 6.3.6 — il tag che
abbiamo clonato è una versione che sulla macchina dell'utente non c'è. Per le differenze fra 6.3.5 e
6.3.6 non ho materiale [?].

### 12.3 `xrdp` — non affronta KWin: lo evita

*Verificato sul sorgente il 7 agosto 2026 (clone di `neutrinolabs/xrdp` master).*

La domanda «come fa xrdp con KWin?» ha una risposta secca: **non ci parla**. In tutto il codice C di
xrdp la parola *wayland* compare **11 volte**, e nessuna riguarda la cattura o l'input: sono nomi di
display (`"wayland-n"`), un commento, e **una riga che dichiara a `pam_systemd` il tipo di sessione**
(`sesman/libsesman/verify_user_pam.c:405-413`) quando il display non è X11 — cioè una predisposizione
di etichetta, non un'implementazione.

Che cosa fa invece: `sesman/sesexec/session.c` lancia **`Xorg`** (con `xorgxrdp`) oppure **`Xvnc`**, e
dentro quel server X esegue `sesman/startwm.sh`, che a sua volta chiama la sessione del desktop —
per KDE, `startplasma-x11`. Cioè xrdp fa girare **Plasma in sessione X11**, dove il compositore è
`kwin_x11` e la cattura è una cattura X11: nessun protocollo Wayland, nessun PipeWire, nessun
permesso da chiedere.

**Ne discendono tre cose per noi:**

1. ⛔ **xrdp non è un riferimento per la fase 11.** I problemi che stiamo studiando — il permesso
   della cattura, l'output virtuale, l'input su Wayland — nel suo modello **non esistono**. Il
   riferimento è `KRdp` (§12.0);
2. **quella strada esiste ancora, e funziona oggi**: Plasma 6.3.6 ha ancora la sessione X11
   (`plasma-workspace/login-sessions/plasmax11.desktop.cmake`, `startkde/startplasma-x11.cpp`,
   `kwin/src/main_x11.cpp`) [R]. È **la ragione per cui xrdp su KDE va**, ed è anche la ragione per
   cui non ci serve: §4.5 di `SPECIFICA.md` ha escluso le sessioni X11 — un secondo percorso completo
   di cattura e input — e KDE quella sessione la sta chiudendo;
3. e vale la pena registrarlo come **conferma della scelta di fondo del progetto**: il concorrente più
   diffuso non ha ancora affrontato Wayland, mentre REMOTIX su Wayland ha già un desktop che
   funziona.

### 12.2 Il portale — da conoscere per scartarlo con cognizione

**[R]** Sette fatti che decidono:

| | |
|---|---|
| `ConnectToEIS` **esiste** in 6.3.6 | ed è **un inoltro di sei righe utili** a `org.kde.KWin.EIS.RemoteDesktop`: passare dal portale **non aggiunge nulla** rispetto a chiamare KWin, tranne il dialogo |
| l'output virtuale **non è annunciato** fra le sorgenti | `AvailableSourceTypes = Monitor\|Window` (`screencast.h:53-56`): solo l'utente può scegliere «schermo virtuale» nel dialogo |
| e la sua misura è **cablata a 1920×1080** | `screencast.cpp:299` — nessun modo di chiedere 4K, cioè il numero desiderato dall'utente |
| il nodo PipeWire lo crea e lo possiede **KWin** | `screencastmanager.cpp:84-90`; il portale attende `created` in un event loop bloccante con **timeout di 3 s** (`waylandintegration.cpp:354`) |
| i `Notify*` passano da `fake_input` | e portano due difetti: `NotifyPointerAxis` **inverte il segno di y** (`:434`) mentre `NotifyPointerAxisDiscrete` no, e `NotifyKeyboardKeysym` **non rilascia mai** il modificatore che premette (`:579-592`) |
| ⛔ `XDG_CURRENT_DESKTOP` deve valere **esattamente `KDE`** | altrimenti ScreenCast e RemoteDesktop **non vengono nemmeno registrati** (`desktopportal.cpp:43-44`). **Prima riga di qualunque diagnosi** |
| la mega-autorizzazione | §3.5: la scappatoia documentata per il non presidiato, ma **nessuna interfaccia scrive** quella voce |

---

## 13. Il conto per REMOTIX

### 13.1 Che cosa conferma

| Decisione di REMOTIX | Conferma nel codice di KDE |
|---|---|
| **Parlare al compositore, non al portale** | il portale di KDE è **un client** dello stesso protocollo, e aggiunge solo il dialogo (§12.2) |
| **Il palco appartiene alla sessione, non alla connessione** | krfb lo pratica per costruzione (§12.1); e su KWin è obbligatorio: un `UNCONNECTED` smonta l'output virtuale (§4.9) |
| **R9** — l'ultimo fotogramma si conserva e si rispedisce | nessuna richiesta «mandami un fotogramma pieno» esiste [✗]; il pieno arriva solo alla ripresa da pausa |
| **Cadenza dichiarata «quando cambia»** | `framerate` **deve** essere `0/1`; il tetto è `maxFramerate` (§4.5) |
| **Lo stride si legge dal chunk** | `SPA_ROUND_UP_N(width*bpp, 4)`: non è `width × 4` |
| **Il codificatore senza fotogrammi B** | `max_b_frames = 0` in ogni encoder di kpipewire (§11.3) |
| **Il sink audio lo creiamo noi** | zero righe di Plasma toccano i dispositivi audio (§10.4) |
| **`libavcodec` invece delle API dei costruttori** | kpipewire scrive contro libav, non contro libva a mano — e il controllo del bitrate **non ce l'ha nemmeno lui** (§11.3) |
| **Le nove combinazioni di §3.4** | logind è lo stesso: niente da rifare |
| **Il conto dei tasti premuti** | KWin scarta ripetizioni e rilasci non appaiati, e rilascia tutto alla morte del client (§7.2) |
| ⭐ **Il `.desktop` come via del permesso** | **è quel che fa `KRdp`**, il server RDP di KDE, per la cattura *e* per l'input (§12.0) |
| ⭐ **I due codec sulla stessa pipeline** (R3) | `KRdp` fa la stessa scelta: H.264 se il client dichiara AVC **e** YUV420, altrimenti RemoteFX Progressive |
| ⭐ **Il regolatore a fotogrammi in volo con soglia dall'RTT** (fase 7) | `KRdp` ha lo stesso meccanismo, e nel master lo ha appena raffinato smussando l'RTT |
| ⭐ **I bordi esclusivi delle regioni** (R5) | `KRdp` scrive `right = rect.right() + 1`: terza fonte concorde |
| ⭐ **TLS puro con PAM** (§3.6) | `KRdp`: `TlsSecurity = usePam`, `NlaSecurity = !usePam` — la nostra scelta è anche la sua, quando autentica come noi |

### 13.2 Che cosa smentisce, o corregge

1. ⛔ **`SPECIFICA.md` §3.8 va corretta**: dice *«KWin: cattura PipeWire via **portale**, input
   interfacce KWin, protocollo `kde-fake-input`»*. Il codice dice: cattura **via protocollo Wayland
   diretto** (il portale è un client come noi), input **via libei/EIS su D-Bus** (`fake_input` è la
   strada vecchia).
2. ⛔ **`REFERENCE.md` R32 e `LEZIONI.md` §3 riga 4**: *«KWin senza monitor disegna in software»* è
   contraddetto dal codice, e la nostra stessa tabella (DMA-BUF con fence) lo conferma. **Da
   rimisurare prima di correggere** (§5.1, §15).
3. ⛔ **Le misure dei 59–60 fps hanno due etichette da rivedere**: sono state prese con
   `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` (cioè scavalcando il cancello) e con `--virtual` +
   `stream_output` **senza `--xwayland`** — cioè su **KWin nudo**, non su una sessione Plasma, e non
   nella configurazione del prodotto (`stream_virtual_output`, che con `--virtual` **non funziona**).
   Il numero resta un fatto; la sua etichetta no.
4. ⛔ **La risoluzione dinamica non si fa come su GNOME** (§8): un output virtuale non si
   ridimensiona. Il prezzo che la fase 6 aveva estinto torna, in forma diversa — e su KDE **non
   trascina l'input**.
5. ✅ **Due debiti di GNOME non si presentano**: la connessione al bus di sessione che non
   sopravvive al logout (§6.6), e il difetto delle schermate alternate a copia zero (§4.6).
6. ⚠ **`banco/misura-cattura.c` va corretto prima di rimisurare su KWin**: `--fissa` non può
   negoziare (§4.5), e i buffer `SPA_CHUNK_FLAG_CORRUPTED` del cursore vengono contati come
   fotogrammi (§4.7).

### 13.3 Che cosa conviene copiare, in ordine di resa

0. ⭐ **Leggere per intero `KRdp`** — 4 222 righe, cioè una sessione di lettura: è un server RDP
   sullo stesso compositore, con la stessa libreria, e ogni sua scelta è una risposta a una domanda
   che abbiamo (§12.0). Restano da leggere `Clipboard.cpp`, `Cursor.cpp`, `NetworkDetection.cpp` e
   `PortalSession.cpp`.
1. **Il `.desktop` con `X-KDE-Wayland-Interfaces`**, sul modello di
   `org.kde.krdpserver.desktop` (§12.0) o di `org.kde.krfb.virtualmonitor.desktop` (§3.2). È la
   chiave della fase, e sono tre righe.
2. **`ei_device_scroll_discrete(±120)`** invece del nostro `/120 → ×10` (§7.2): più semplice di
   quel che facciamo, e produce una rotella vera.
3. **Il solo `DRM_FORMAT_MOD_LINEAR` per la codifica in GPU** e **il contesto VAAPI creato dal
   grafo di filtri** (§11.2): due difetti silenziosi già pagati da altri.
4. **La rinegoziazione dei modificatori invece dello spegnimento del DMA-BUF** (§11.2).
5. **`AddInhibition(types=4)` di powerdevil** per non farsi spegnere lo schermo sotto i piedi
   (§10.2).
6. **`org.kde.Shutdown` come sentinella passiva del logout** (§6.5): due sottoscrizioni, zero
   rischio di tenere in ostaggio la sessione dell'utente.
7. **`KWIN_XKB_DEFAULT_KEYMAP` + `XKB_DEFAULT_*` nell'ambiente del compositore** (§6.7), se un
   giorno servisse *imporre* la disposizione invece di leggerla.

### 13.4 Le scelte da mettere davanti all'utente, prima di scrivere

Sono decisioni di prodotto, non di tecnica, e `LEZIONI.md` §2.6 dice di metterle davanti **subito**.

> ⚠ **Erano tre; dopo il banco del 7 agosto 2026 ne restano due**, ed è un miglioramento: **la prima
> l'ha decisa la misura, non l'utente** (M2, §5.2). Vale la regola di
> `remotix-prove-sul-banco-non-sull-utente`: quel che si può misurare non si chiede.

> ### ✅ DECISO DALL'UTENTE l'8 agosto 2026 — tutte e tre, e nella direzione migliore
>
> | La domanda | La decisione |
> |---|---|
> | **La copia zero: adesso o dopo?** *(domanda nuova, nata dalle misure di §5.7)* | ✅ **adesso, dentro il lavoro su KDE.** Quindi **la cattura si scrive a copia zero dal principio**, con l'attesa della fence (§4.8) — non si scrive in memoria per poi tornarci sopra. È la condizione dei 60 fps a 4K |
| **Il ridimensionamento su Trixie** | ✅ **misura fissa alla connessione**: nessun buco video, nessuna finestra riposizionata, nessuna notifica di sistema. ⛔ **E si scrive nella forma della negoziazione PipeWire** (§8.2), che è il codice della fase 6: così su **KWin 6.8** il ridimensionamento vero si accende da sé, senza che nessuno riscriva niente |

> ### ⛔ «L'IMMAGINE SI SCALA NEL CLIENT» ERA FALSO — e l'ha trovato l'utente
>
> *[M, 8 agosto 2026: «non riesco a vedere tutto lo schermo, la risoluzione sembra ignorata».]*
>
> La decisione qui sopra è stata scritta con accanto la frase «l'immagine si scala nel client», e
> quella frase **non era mai stata misurata**. `xfreerdp3` non scala niente: apre una finestra
> **grande quanto la tela dichiarata**. Con il desktop a 1920×1080 e uno schermo più piccolo, la
> finestra non ci sta — e chi guarda vede «la risoluzione che ho chiesto viene ignorata», che è
> esattamente quel che succede.
>
> **La scalatura lato client esiste, e passa da `MAPSURFACETOSCALEDOUTPUT`** — che il **7 agosto**
> avevamo già misurato essere resa da **un client su tre**: `xfreerdp3` sì, mstsc no, RDM la dichiara
> spenta (§10.2 di `REFERENCE.md`). Cioè: la smentita era già in casa, su un'altra pagina, e la
> decisione dell'8 agosto l'ha ignorata.
>
> ⭐ **Quel che regge davvero della decisione, ed è più forte di quel che si pensava**: la misura del
> desktop la fissa **la prima connessione**, e su KDE è REMOTIX ad avviare la sessione — quindi il
> desktop nasce *esattamente* della misura chiesta. Il prezzo non è un'immagine scalata: è che **per
> cambiare misura bisogna far finire la sessione**. Adesso il registro lo dice, invece di lasciar
> credere a una scalatura che non avviene.
>
> **La lezione, che non riguarda KDE**: una decisione di prodotto presa citando un comportamento non
> misurato è una decisione presa a metà. `LEZIONI.md` §1.11 lo dice per le prove; vale identico per
> le premesse.
| **BlocMaiusc e BlocNum** | ✅ **si legge lo stato vero da KWin**, con `org_kde_kwin_keystate` v5. Costa poco **perché su KDE siamo già client Wayland** per la cattura: basta aggiungere il nome dell'interfaccia allo stesso `.desktop` (`X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1,org_kde_kwin_keystate`) e un ascoltatore. ⚠ Nella valutazione del 7 agosto l'avevo data come «una seconda strada nel codice»: **era sbagliata**, la connessione Wayland c'è comunque |

| | La scelta | Il prezzo di ciascuna via |
|---|---|---|
| ~~**1**~~ | ~~**`--virtual` o `--drm`?**~~ ⛔ **NON è più una scelta: la misura M2 del 7 agosto 2026 l'ha chiusa.** `--drm` da una sessione senza seat esce con stato 1 (`Failed to activate … session`, poi `No suitable DRM devices have been found`), e l'unico modo di avercelo sarebbe occupare `seat0`, cioè la console fisica. **Si va di `--virtual`**, pagando §8.1: risoluzione fissa all'avvio e nessun `stream_virtual_output` prima di KWin 6.8. Non c'è niente da chiedere all'utente | (riquadro in §5.2) |
| **2** | ~~**La risoluzione dinamica su KDE**~~ ✅ **la scelta si è ridotta da sé**: il ridimensionamento arriva in **KWin 6.8** per **negoziazione PipeWire**, cioè con il codice che la fase 6 ha già scritto (§8.2). Quindi si scrive **in quella forma** — che diventa giusta da sé quando l'utente aggiorna — e per le versioni che non ce l'hanno (Trixie compresa) resta la domanda **piccola**: ripiego «chiudi e rifai lo stream», o misura fissa alla connessione? | Il ripiego costa un buco video, le finestre ridisposte e una notifica di sistema a ogni giro; la misura fissa non costa nulla e si vede solo come immagine scalata. **Da decidere guardando**, e non blocca niente |
| **3** | **BlocMaiusc e BlocNum**: aprire **anche** una connessione Wayland (per `org_kde_kwin_keystate`, che richiede il `.desktop`), tenere il conto approssimato, o rinviare? | La prima costa una seconda strada nel codice; la seconda è quel che facevamo su GNOME prima di libei |

---

## 14. Le domande che il codice non chiude — il piano di misure

In ordine di quanto pesano. Sono le `[?]` di questo documento, e sono il contenuto della prima
giornata di banco della fase 11.

> ### Lo stato dopo il banco del 7 agosto 2026
>
> **Cinque chiuse su dodici, e sono le cinque che pesano di più**: le due «decisive» (M1, M2) più
> M3, M5, M6. Nessuna ha smentito il codice; **una ha smentito noi** (R32, il «in software»), e una
> ha aggiunto un requisito che nessuna lettura di codice aveva mostrato (`XDG_MENU_PREFIX`, §3.3-bis).
> Gli script del banco stanno in `reference-kde/banco/` (`misure-kde.sh`, `permesso-kde.sh` …
> `permesso6-kde.sh`) e sul server in `/media/REMOTIX/tmp/banco-compositori/`.

| # | Che cosa | Perché pesa |
|---|---|---|
| ~~**1**~~ | ✅ **CHIUSA: sì, autorizza** — con `NoDisplay=true`, la forma di KRdp. ⛔ **Ma a una condizione che il codice non mostrava: `XDG_MENU_PREFIX=plasma-`**, senza la quale `kbuildsycoca6` non indicizza **niente** e KWin dice `Could not find the desktop file for …`. Cinque varianti del file negate prima di trovarlo. §3.3-bis | è il cancello: se non passa, tutto il resto è teoria (§3) |
| ~~**2**~~ | ⛔ **CHIUSA: no.** `--drm` senza seat esce con 1 (`Failed to activate … session` → `No suitable DRM devices`), e **non** per permessi Unix: nello stesso ambiente `--virtual` apre `renderD129`. Quindi **`--virtual`**, e la decisione 1 di §13.4 non si chiede più all'utente. §5.2 | decide la scelta n.1 di §13.4 (§5.2, §6.3) |
| ~~**3**~~ | ✅ **CHIUSA: GPU.** `renderD129` aperto, `libEGL_mesa` + `libgbm` caricate, `zwp_linux_dmabuf_v1` **v4** annunciato. **R32 va corretta.** ⚠ Due trappole trovate: su Mesa 25 llvmpipe sta dentro `libgallium-*.so` (cercarlo per nome non prova nulla), e `kwin_wayland` è **non dumpable** per l'xattr `security.capability` (il `/proc` va letto con `sudo`). 🟡 Resta **M3d**, il tipo di buffer: negoziato `MemFd/BGRx/LINEAR`, ma per limite del **nostro** cliente. §5.1 | corregge R32 (§5.1, §5.3) |
| ~~**4**~~ | ⛔ **CHIUSA: parte in software.** Con i render node inaccessibili e `KWIN_COMPOSE=O2`: `forced to OpenGL` → `Falling back to defaults` → `QPainter … successfully initialized`, **e KWin parte**. L'interruttore è **inerte**: va cassato dalle ricette e da ogni banco, e l'unico modo di sapere come rende KWin è **chiederglielo** (§5.3-bis). ⚠ Nota: `LIBGL_ALWAYS_SOFTWARE` e le altre variabili di Mesa **non hanno effetto** su KWin. §5.4 | se parte, va cassato dalle nostre ricette, e tutte le misure fatte con quella variabile vanno rilette (§5.4) |
| ~~**5**~~ | ✅ **CHIUSA: sì, senza nulla.** `gdbus … org.kde.KWin.EIS.RemoteDesktop.connectToEIS 7` da una shell SSH qualunque → **`(handle 0, 1)`**: un descrittore e un cookie, **senza sessione, senza portale, senza dialogo e senza `.desktop`**. L'input via libei su KDE è confermato sul campo | è la quarta domanda della fase, e il codice dice sì (§7.1) |
| ~~**6**~~ | ✅ **CHIUSA: sì.** `libeis-dev` è nei `Build-Depends` di `kwin 4:6.3.6-1`, e — prova che non mente — **`eis.so` è dentro il pacchetto `kwin-common`** (`/usr/lib/<triplet>/qt6/plugins/kwin/plugins/eis.so`), libei 1.3.901. ⚠ `kwin-wayland` **non** dipende da `libeis1`: guardare lì avrebbe dato la risposta sbagliata | la premessa dell'input c'è (§7.1) |
| ~~**7**~~ | ✅ **CHIUSA in parte.** Montare un flusso costa **65–67 ms** (tre giri), ed è la componente fissa del buco. Il tempo di *ricreare l'output* non è misurabile su `--virtual`, dove `stream_virtual_output` è rifiutato (`Could not find output`, verificato). §8.1 | decide la scelta n.2 di §13.4 (§8.3) |
| ~~**8**~~ | ✅ **CHIUSA: la cattura è indipendente dal VT.** Il compositore `--virtual` **non apre nessuna tty/console** (verificato su `/proc/<pid>/fd`), la sua sessione ha `VTNr=0` e `Seat=` vuoto; cambiando VT (tty1 → tty2 → tty1 con `VT_ACTIVATE`, perché `chvt` non è installato) **compositore, flusso e protocollo restano tutti vivi**. §4.9 | è la condizione di un servizio non presidiato (§4.9) |
| ~~**9**~~ | ✅ **CHIUSA: sì.** Dopo `org.kde.Shutdown.logout()` tutti i processi Plasma spariscono e il socket Wayland con loro, **ma il bus d'utente risponde ancora sulla stessa connessione** e `systemd --user` è vivo. Il difetto di GNOME non si ripresenta. §6.6 | se sì, un difetto di GNOME non si ripresenta (§6.6) |
| ~~**10**~~ | ✅ **CHIUSA per lettura, e la lettura è conclusiva**: `eiscontext.cpp:272-285` **non inverte** e usa **la stessa formula per i due assi** (`delta = v120 × 15/120`, `v120` grezzo a valle). Nessuna asimmetria di KWin da compensare: l'adattamento è tutto nostro. Resta la verifica a occhio nella fase. §7.2 | §7.2 |
| ~~**11**~~ | 🟡 **CHIUSA per quel che si può**: `0x0`, `-1x-1`, `1x1`, `16384²`, `99999²` **tutte rifiutate** e **KWin sopravvive a tutte**. Ma il rifiuto è per l'assenza di output virtuale, non per validazione: **la validazione resta non misurabile con `--virtual`**. §8.1 | nessuna validazione nel codice (§4.3) |
| ~~**12**~~ | 🟡 **CORRETTA**: il dialogo **non** è il primo rischio. Al primo fallimento di OpenGL plasmashell scrive **`SceneGraphBackend=software` in modo persistente** e si riavvia; il `QMessageBox` è solo al secondo giro. Il rischio vero è **la configurazione permanente lasciata nella casa dell'utente**. Con la GPU: nulla di tutto questo (verificato). §10.4 | dieci secondi, e blocca una sessione (§10.4) |
| **13** *(nuova, dal banco)* | **`InaccessiblePaths=` nell'unità del compositore chiude il cancello della cattura** — 0 righe `KWIN_UTILS` contro 13. Il meccanismo non è dimostrato; la regola operativa sì: **niente namespace di monti nell'unità di KWin**. §3.3-bis | era la via ovvia per scegliere la GPU, ed è una trappola |

**Il metodo, che vale più dell'elenco**: le misure 3 e 4 vanno fatte **prima** delle altre e con le
prove che non dipendono da quel che KWin dichiara. È la lezione 1.8 di `LEZIONI.md`, e su KWin il
codice mostra due punti in cui il ripiego è silenzioso per costruzione.

> ### Lo stato dopo il secondo giorno di banco (8 agosto 2026)
>
> **Dodici su dodici hanno una risposta**, più una tredicesima trovata strada facendo. Sette sono
> state chiuse in questa giornata (M3d, M4, M7, M8, M9, M10, M11, M12), e i risultati che cambiano il
> piano sono tre:
>
> 1. ⭐ **la copia zero è la condizione dei 60 fps a 4K** sulla GPU scelta dall'utente (§5.7);
> 2. ⛔ **`KWIN_COMPOSE=O2` non protegge** (M4), quindi ogni misura va accompagnata dalla stringa del
>    renderer (§5.3-bis);
> 3. ⛔ **il modo ovvio di scegliere la GPU rompe il permesso della cattura** (§5.6, §3.3-bis).
>
> ⚠ **E due prove strutturali che avevamo per buone non valgono**: «render node aperto» non prova la
> GPU (aperto anche in QPainter), e «il flusso è MemFd» non prova che il compositore sia in software
> (dipende da cosa chiede il *cliente*). Le lezioni sono in `LEZIONI.md` §1.9 e §1.11.

> ### ✅ E L'8 AGOSTO 2026 LA VOCE 1 HA MESSO ALLA PROVA IL DOCUMENTO INTERO
>
> *Banco `prove/fase11.sh`, con REMOTIX vero al posto di `nodo-kwin`. Il racconto sta in `PIANO.md`
> fase 11; qui c'è quel che cambia in questo documento.*
>
> **Niente di quel che è scritto qui è stato smentito.** Le quattro cose che il campo ha aggiunto:
>
> | | |
> |---|---|
> | ✅ **il cancello si apre anche per noi** (§3) | `.desktop` con `Exec=` sul binario canonico e `NoDisplay=true`, più `XDG_MENU_PREFIX=plasma-` nell'ambiente di KWin: il global compare, nessun dialogo. Con `--installa-desktop` il file lo scrive REMOTIX stesso, da `/proc/self/exe` |
> | ✅ **la fence si aspetta, e basta** (§4.8) | **2 400 buffer su 2 400** col disegno in corso — la misura dell'8 agosto confermata su un campione otto volte più grande — e **zero attese scadute** con un tetto di 50 ms. Il difetto di R29 non si ripresenta: i fotogrammi sono interi |
> | ✅ **il modificatore che si ottiene è `0x0`, lineare** (§11.2) | è quello che il codificatore vuole, e per averlo è bastato metterlo **primo** nell'enum della proposta. `INVALID` resta come seconda scelta |
> | ✅ **il ritmo regge, sulla catena vera** (§5.7) | **58,1 fps a 1080p e 58,4 a 4K** sulla Intel, contro i 59,2 e 59,0 misurati col solo `misura-cattura`. La differenza è la conversione sulla scheda, che il banco non faceva |
>
> ⛔ **E una trappola nuova, che non è di KDE ma dei banchi che rifanno la sessione**: uccidere
> `kwin_wayland` mette in coda su systemd un lavoro di *stop* per la sua unità, e un
> `StartUnit("plasma-workspace-wayland.target")` che arrivi prima che quel lavoro sia finito viene
> **rifiutato in blocco** — *«Transaction … is destructive»* — con `startplasma-wayland` che dice
> soltanto «Could not start Plasma session». Chi rifà la sessione due volte di fila fallisce la
> seconda: si ferma il target e si **aspetta** che l'unità sia `inactive`.

---

## 14-bis. ✅ Lo studio è chiuso — quel che si è imparato SCRIVENDO, non leggendo

*8 agosto 2026, a fase 11 conclusa per KDE.*

Le dodici misure sono chiuse (§14), e la loro resa è alta: **undici domande su undici avevano una
risposta prima di scrivere una riga**. Ma quattro difetti sono comparsi solo mettendo il codice
davanti a un utente, e vale la pena elencarli perché **sono il tipo di cosa che rileggere il codice
non trova** — e quindi si ripresenterà su XFCE:

| Trovato da | Che cosa | Dove sta ora |
|---|---|---|
| **l'utente, al primo sguardo** | due puntatori del mouse | riquadro in testa: il cursore è dentro l'immagine, e la cura è un tema trasparente |
| **l'utente** | il cursore del volume non governava niente | §10.5 — e il difetto era **anche su GNOME**, da sempre |
| **l'utente** | «Blocca» e «Cambia utente» inerti nel menu | §10.6 — KIOSK, tre azioni e non due |
| **il banco, ma solo dopo averlo rinforzato** | «una via audio nuova parte al massimo» non funziona | `REFERENCE.md` §7.5, **aperto** |

⭐ **Tre su quattro erano nel percorso condiviso**, cioè erano difetti di GNOME che nessuno aveva
visto in dieci fasi. Aprire un secondo compositore non ha solo aggiunto un desktop: ha fatto da
banco al primo.

⛔ **E la lezione di metodo, che è la più cara**: il difetto del volume è rimasto invisibile perché
la prova era stata fatta su **un sink equivalente creato con `pactl`** invece che sul nostro — e
`pipewire-pulse` mette da sé la proprietà che a noi mancava. Un banco che prova *qualcosa di simile*
assolve il codice (`LEZIONI.md` §1.11 e §5).

---

## 15. Le correzioni da fare ai documenti

Come prescrive §7.0 di `SPECIFICA.md`, quando una misura contraddice un documento lo si aggiorna
**nello stesso momento**. Le prime tre righe nascevano da una **lettura di codice** e furono annotate
come tensioni da sciogliere; **il banco del 7 agosto 2026 le ha sciolte**, e ora sono smentite vere:

| Documento | Che cosa dice oggi | Che cosa dice il banco |
|---|---|---|
| `SPECIFICA.md` §3.8 | «KWin: cattura via **portale**, input `kde-fake-input`» | cattura via **protocollo Wayland diretto**, input via **libei/EIS** (§13.2 n.1) — **correzione applicata**, con la data. E ora **misurata**: `connectToEIS(7)` → `(handle 0, 1)`, e il `.desktop` apre il global |
| `REFERENCE.md` **R32** | «KWin senza monitor disegna in software: zero nodi DRM, nessuna libreria GL» | ⛔ **smentita, con tre prove** [M]: `renderD129` aperto, `libEGL_mesa`+`libgbm` caricate, `zwp_linux_dmabuf_v1` v4 annunciato. **Va corretta**: il «60 fps a 4K» resta, l'etichetta «in software» no (§5.1) |
| `LEZIONI.md` §3, riga 4 e riga «KWin tiene la cattura dietro un controllo di permessi» | «NO, in software»; «serve il permesso per la via che KDE prevede» | la prima come sopra; la seconda ha ora **una risposta misurata**: il `.desktop` **più `XDG_MENU_PREFIX=plasma-`** (§3.3-bis) |
| `PIANO.md` fase 11 | le quattro domande d'apertura | **quattro su quattro hanno risposta di banco**, e la decisione «`--virtual` o `--drm`» è stata chiusa da una misura invece che dall'utente (§5.2) |

> ✅ **Tutte applicate**, e l'ultima l'8 agosto 2026 con la chiusura della fase. Due correzioni si
> sono aggiunte strada facendo, e vanno lette insieme alle prime perché nascono dallo stesso errore —
> **aver creduto a una lettura di codice senza misurarla**:
>
> | Documento | Che cosa diceva | Che cosa dice il banco |
> |---|---|---|
> | `LEZIONI.md` §3, domanda 5 | «KWin: sì, `stream_virtual_output`» | ⛔ **no**: col backend `--virtual` risponde `Could not find output`, per ogni misura. **Corretta** |
> | questo documento, in testa | «il cursore è fuori dal percorso del codificatore» | ⛔ **è dentro l'immagine**, e l'ha visto l'utente prima di noi. **Corretta**, con la cura |

---

## 16. Che cosa non c'è, per non cercarlo

Tutte dichiarazioni negative verificate per grep su tutti gli otto repository [✗]:

| Funzionalità | Stato in KDE 6.3.6 |
|---|---|
| `zwlr_screencopy_manager_v1`, `ext_image_copy_capture_v1` | **assenti** in KWin |
| Un'interfaccia D-Bus di screencast (l'analogo di `org.gnome.Mutter.ScreenCast`) | **assente**: la cattura passa dal protocollo Wayland, punto |
| `org.kde.KWin.VirtualOutputs` | **assente** (c'era in KWin 5) |
| Una richiesta di **resize** nel protocollo screencast | **proposta e respinta** (`plasma-wayland-protocols!138`), perché la strada scelta è la **negoziazione PipeWire**: unita in `kwin!7932`, milestone **6.8** — non c'è in Trixie, ma arriva (§8.2) |
| `wlr-output-management`, `ext-data-control-v1`, `kde_primary_output_v1` (global) | **assenti** |
| `eis_device_keyboard_send_xkb_modifiers` in KWin | **assente**: nessun `KEYBOARD_MODIFIERS` |
| `eis_region_set_mapping_id` in KWin | **assente**: regioni senza chiave |
| `keyboard_keysym` di `fake_input` v6 | **non implementato** (KWin ferma a v5) |
| Un controllo di permesso su `org.kde.KWin.EIS.RemoteDesktop` | **assente** |
| `EnableClipboard`/`DisableClipboard` | **assenti**: la clipboard non appartiene a una sessione |
| Un `Logout(2)` forzato | **assente**: la forzatura è `StopUnit` |
| `RegisterClient`/`EndSession` su D-Bus | **assenti**: l'equivalente è XSMP su ICE |
| `ConditionEnvironment=` nelle unità di KDE | **assente** |
| Un renderer **Vulkan** in KWin | **assente** |
| `libseat`/`seatd` | **assenti**: solo logind, ConsoleKit, Noop |
| Controllo del bitrate H.264 in kpipewire | **assente**, come in `gnome-remote-desktop` |
| ~~Un backend RDP in KDE~~ | ⛔ **sbagliato**: c'è **`KRdp`** (§12.0), che è il riferimento della fase |
| Un `disable-animations` per sessione di cattura | **assente**: si spengono a sessione |
