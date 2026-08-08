# LXQt su Wayland — studio del codice, per la fase 11

*Scritto l'8 agosto 2026, con dieci ricerche parallele sui sorgenti clonati alle versioni di Debian
Trixie. È il settimo studio del progetto, e il **quarto desktop** dopo GNOME, KDE e XFCE.*

> **Le marche, e contano più delle frasi:**
>
> | | |
> |---|---|
> | **[R]** | letto nel codice, con `file:riga`. **Non è una misura** |
> | **[R-pkg]** | letto nel pacchetto Debian (`apt-cache`, `dpkg-deb -c`): dice che cosa la distribuzione *spedisce*, che è cosa diversa da che cosa il progetto *scrive* |
> | **[M]** | misurato |
> | **[?]** | deduzione o ipotesi |
> | **[✗]** | verificata assente, con il modo in cui è stata cercata e un controllo positivo |
>
> Il dettaglio sta nei **dieci rapporti** in `reference-lxqt/rapporti/`. Qui c'è quel che serve per
> decidere.

---

## 1. In due minuti, e la riga che conta più di tutte

> ## ⛔ **Su Debian Trixie, LXQt su Wayland non esiste come sessione installabile.**
>
> **[R-pkg]**, tre prove indipendenti con controllo positivo:
>
> | | |
> |---|---|
> | `lxqt-wayland-session` **non è in Trixie** | `apt-cache policy` → nessun candidato; l'indice `Packages` elenca **37** pacchetti `lxqt-*` e non lui (controllo positivo: `lxqt-session` → 2.1.1-1, `labwc` → 0.8.3-1) |
> | **nessun pacchetto LXQt** installa un file in `/usr/share/wayland-sessions/` | l'intero `wayland-sessions` di trixie/main ha **10 voci** — labwc, phosh, plasma, sway, weston, **xfce-wayland**… **nessuna LXQt**. LXQt compare solo in `xsessions/` |
> | e lo dice il codice stesso | `lxqt-config-session` crea la pagina «Wayland Settings» **solo se trova l'eseguibile `startlxqtwayland`** (`sessionconfigwindow.cpp:65`), che su Trixie non c'è; e `lxqt-session` avvia il window manager **solo su xcb** (`lxqtmodman.cpp:82-83`) |
>
> Non è un rifiuto di Debian: è un **ritardo**. Il pacchetto esiste in forky/sid a **0.3.1-1**,
> caricato dopo il freeze di Trixie.
>
> ⭐ **Ma il codice Wayland è già spedito e funzionante**: `lxqt-panel` 2.1.4 contiene
> `libwmbackend_wlroots.so` **e** `libwmbackend_kwin_wayland.so` **[R-pkg]**. **Manca solo il
> lanciatore** — che è precisamente la cosa che REMOTIX si scrive da sé, perché la sessione la
> avviamo noi. Il pezzo mancante è **uno script**, non una funzionalità.

**Il compositore è `labwc`** — lo stesso di XFCE — e la struttura è **rovesciata rispetto a X11**: è
il compositore a lanciare la sessione (`labwc -C <dir> -S lxqt-session`), non viceversa
(`lxqt-wayland-session/startlxqtwayland.in:116` **[R]**). Il logout viene gratis dal `-S`, come su
XFCE.

### 1.1 Il conto del riuso, che è il motivo per cui questo studio esiste

| | Voci | Che cosa |
|---|---|---|
| ✅ **riuso integrale** | **5 su 9** | cattura, input, appunti, ridimensionamento, audio |
| ⚙ **adattamento** | **3** | uscita/logout (cambia il bersaglio D-Bus), cursore (la cura c'è ma passa da un altro canale), energia e blocco (**nessuna** delle leve pagate su GNOME/KDE/XFCE esiste qui) |
| ✍ **da scrivere** | **1, e non è tecnica** | l'avvio della sessione — perché il pacchetto non c'è |

⭐ **Quel che LXQt aggiunge sul compositore è quasi niente**, e va detto chiaramente perché cambia la
taglia della fase: nel caso base è **lo stesso labwc di XFCE**, e il capitolo pixel/tasti/appunti è
`xfce.md` **senza modifiche**. Anzi, **meno tre trappole**:

| Trappola di XFCE | Su LXQt |
|---|---|
| `xfsettingsd` **disabilita** gli output nuovi e apre un dialogo | **[✗]** nessun componente parla `zwlr_output_manager_v1` (2 sole righe in tutto l'albero, e sono stringhe che consigliano `kanshi`) |
| il pannello **esce** se i monitor sono zero | **[✗]** QtWayland crea sempre uno **schermo segnaposto** (`qwaylanddisplay.cpp:402-412`): `screens().at(0)` non è mai fuori range |
| la chiave dello sfondo **è il nome del connector** | **[✗]** `[Desktop] Wallpaper` è unica e globale (`pcmanfm-qt/settings.cpp:243`): il nome dell'output è libero |

⭐ **È il desktop più facile dei quattro sul ridimensionamento a caldo** — e sul ridimensionamento
**siamo l'unico comandante**, cosa che non era vera né su GNOME né su KDE.

### 1.2 E le cinque cose che costano

| | |
|---|---|
| ⛔ **la sessione va composta a mano** | e con essa `XDG_CURRENT_DESKTOP`, `XDG_SESSION_TYPE`, `XDG_MENU_PREFIX`, `XDG_CONFIG_DIRS`, `QT_QPA_PLATFORM`, l'`rc.xml` di labwc e l'autostart |
| ⛔ **`XDG_CURRENT_DESKTOP` decide metà del pannello** | il backend WM è scelto **dai token della variabile**, case-sensitive, a punteggio. Sbagliarla dà un desktop **vivo e inerte**, con un solo `qWarning` |
| ⛔ **l'autostart che LXQt propone spegne l'output** | `swayidle -w timeout 300 "wlopm --off *"` (`configurations/labwc/autostart:31`): il gemello di `xfce4-power-manager`, ma a **5 minuti invece di 10** |
| ⛔ **le tre cure già pagate non si applicano** | `PowerManagement.Inhibit` **[✗] non esiste**; `LockCommand=/bin/false` qui apre una **finestra modale**; `enableIdlenessWatcher=false` **viene riscritto a `true`** dal demone al primo avvio |
| ⚠ **c'è un coinquilino della clipboard** | `qlipper`, dipendenza del metapacchetto `lxqt`, che **rimette l'ultimo elemento quando la clipboard si svuota** — come klipper, ma **senza marcatura e senza tetto di frequenza** |

### 1.3 Il passo zero: chi lo fa già

**[✗] Nessuno fa RDP su LXQt-Wayland, su nessun compositore.** Più netto che su XFCE, perché si
somma il fatto che la sessione non è pacchettizzata. Il concorrente è **`xrdp` su X11**
(`/etc/xrdp/startwm.sh` → `Xsession` → `startlxqt`; `grep -ri wayland /etc/xrdp/` → **zero**
**[R-pkg]**).

⭐ **E LXQt appare nelle guide di xrdp più di ogni altro desktop per una ragione che ci riguarda: è
quello che si consiglia quando la macchina remota è piccola.** Cioè il nostro campo esatto.

⭐ **Un precedente inatteso, e importante**: `lxqt-panel_wayland.desktop.in:14` dichiara
`X-KDE-Wayland-Interfaces=org_kde_plasma_window_management` sotto il commento *«Make KWin recognize
us as priviledged client»* **[R]**. È il **quarto precedente indipendente** del meccanismo di permesso
che abbiamo trovato su KDE — dopo KRdp, krfb e il portale — **e l'unico fuori da Plasma**.

---

## 2. La mappa

| Che cosa | Dove | Versione Trixie |
|---|---|---|
| la sessione | `reference-lxqt/lxqt-session/` | **2.1.1** |
| il pannello | `lxqt-panel/` | **2.1.4** |
| impostazioni, aspetto, monitor | `lxqt-config/` | **2.1.1** |
| la scrivania | `pcmanfm-qt/` 2.1.0, `libfm-qt/` 2.1.0 | |
| energia, scorciatoie, notifiche, policykit | `lxqt-powermanagement/` 2.1.0, `lxqt-globalkeys/` 2.1.0, `lxqt-notificationd/` 2.1.1, `lxqt-policykit/` 2.1.0 | |
| librerie e tema Qt | `liblxqt/` 2.1.0, `libqtxdg/` 4.1.0, `lxqt-qtplugin/` 2.1.0, `lxqt-themes/` 2.1.0 | |
| il menu | `lxqt-menu-data/` 2.1.0 | |
| ⚠ **il lanciatore Wayland** | `lxqt-wayland-session/` | **0.4.1 — NON è la versione di Trixie** |
| il compositore e i protocolli | `../REMOTIX_V2/reference-xfce/` (labwc 0.8.3, wlroots 0.18.2, wlr-protocols, wayland-protocols 1.38) | |

⛔ **Attenzione al clone di `lxqt-wayland-session`**: è **0.4.1** (maggio 2026) e richiede **LXQt ≥
2.4.0** e una labwc molto più nuova. **Si legge come specifica delle intenzioni, non si copia**: i
suoi file di configurazione sono per compositori che Trixie non ha. È l'unico repository dello studio
che non corrisponde alla macchina.

---

## 3. La sessione: come si compone quel che Debian non spedisce

*Dettaglio: `rapporti/01-sessione-lxqt.md`.*

### 3.1 La forma

```
labwc -C <dir nostra> -S lxqt-session
```

Il compositore è il padre; `lxqt-session` è il *primary client*: quando esce, labwc termina. È la
stessa forma di XFCE (`labwc --session xfce4-session`), quindi **il codice di avvio è lo stesso**.

### 3.2 L'ambiente — e qui si concentra il rischio

| Variabile | Valore | Perché, e che cosa succede sbagliandola |
|---|---|---|
| ⭐ `XDG_CURRENT_DESKTOP` | **`LXQt:labwc:wlroots`** | il pannello sceglie il backend WM **dai token, case-sensitive, a punteggio** (`wlroots` 50, `labwc` 30 — `lxqtpanelapplication.cpp:206-270`). Con `LXQt` secco casca sul backend **`dummy`**: taskbar vuota, pager a uno, tutto inerte, **un solo `qWarning`**. ⛔ E i moduli hanno `OnlyShowIn=LXQt;`: senza il token `LXQt` la sessione è **viva con lo schermo nero e zero messaggi** |
| `XDG_SESSION_TYPE` | `wayland` | non è cosmetica: il pannello sceglie il backend da lì, **non** da `platformName()` (`:206-209`) |
| ⭐ `QT_QPA_PLATFORM` | **`wayland` secco** | **[✗]** nessun componente LXQt la imposta. Con la lista `wayland;xcb` Qt prende «il primo che carica» con **un solo `qCWarning`**; con un elemento solo, se il plugin manca si arriva a `qFatal`. È `LEZIONI.md` §1.8 chiusa a codice |
| `XDG_CONFIG_DIRS` | **deve contenere `/usr/share`** | i default LXQt stanno in `/usr/share/lxqt/*.conf`. Col default Debian non si trovano — e spariscono **in silenzio** |
| `XDG_MENU_PREFIX` | `lxqt-` | **[✗] nessun ripiego cablato** in libqtxdg, a differenza di garcon su XFCE. ✅ Ma il file `/etc/xdg/menus/lxqt-applications.menu` **esiste** in `lxqt-menu-data` **[R-pkg]** |
| `LABWC_UPDATE_ACTIVATION_ENV` | `1` | come su XFCE: su backend headless labwc **non propaga** `WAYLAND_DISPLAY` al bus |
| `XCURSOR_THEME` (+ `XCURSOR_SIZE`) | il tema trasparente | §6.1 |
| ⛔ **da NON passare** | `DISPLAY`, `WAYLAND_DISPLAY`, `QT_QPA_PLATFORM` ereditate, `SESSION_MANAGER` | vedi sotto |

⛔ **Il ripiego a `xcb` è peggio che su KDE, e non è «un po' peggio»: è un'altra sessione.** Se Qt
sceglie xcb, `lxqt-session` **avvia un secondo window manager**, può aprire un **dialogo modale** di
scelta del WM e bloccare il ciclo eventi **30 secondi** (`lxqtmodman.cpp:82-83`, `:209-214`, `:237`);
smette di filtrare i moduli `X-LXQt-X11-Only`, accende `setxkbmap`, `xrdb`, l'osservatore udev degli
input **e quello DRM che lancia `lxqt-config-monitor -l` a ogni cambio di display** — cioè **un
secondo comandante della risoluzione**.

### 3.3 Quel che NON serve, e sono tre debiti che non paghiamo

| | |
|---|---|
| ✅ **[✗] nessun `loginctl terminate-session`** | grep su `lxqt-session` e `liblxqt`, con controllo positivo che trova quello di XFCE. **La doppia difesa di `xfce.md` §9.2 non serve** |
| ✅ **[✗] nessuna registrazione client di sessione** | né XSMP né D-Bus: il rischio «ostaggio del logout» pagato su KDE **non esiste**. E il logout non consulta inibitori, non mostra nulla, non si annulla |
| ✅ **[✗] nessun salvataggio di sessione** | la trappola `~/.cache/sessions/…` di XFCE non ha equivalente: non c'è niente da cancellare |
| ✅ **[✗] nessun seat richiesto** | `XDG_SEAT`/`XDG_VTNR`/`libsystemd` assenti dai 17 repository |
| ✅ **[✗] nessun gruppo di priorità** | gli **otto secondi** strutturali di XFCE non hanno equivalente: il tetto «desktop su» può essere corto |
| ✅ **il bus di sessione** | **[✗] `dbus-run-session` non compare da nessuna parte**: si usa `$XDG_RUNTIME_DIR/bus`. ⭐ **La decisione lasciata aperta in `xfce.md` §9.7 qui si chiude da sé** |

⛔ **Ma `lxqt-session` è subreaper** (`procreaper.cpp:56`) e al logout manda `SIGTERM` a tutto ciò che
ha il suo ppid (`:129`, `:191-198`). Noi siamo *sopra* e siamo salvi — **ma nulla di REMOTIX va
avviato sotto `lxqt-session`**, perché ogni orfano gli viene riassegnato.

### 3.4 ⭐ La prontezza si legge, meglio che sugli altri tre

Segnale **`moduleStateChanged(QString, bool)`** su `org.lxqt.session`, oggetto `/LXQtSession`
(`sessiondbusadaptor.h:53`, `:57`): si aspetta `("lxqt-panel.desktop", true)`.

⚠ Il **nome sul bus** compare nel costruttore (`sessionapplication.cpp:48`), quindi «il nome c'è» **non
significa «desktop su»** — è la stessa distinzione che su KDE ci aveva ingannati.

**Il logout**: servizio, oggetto e interfaccia sono tutti `org.lxqt.session` / `/LXQtSession`.
**[✗] Nessun segnale «sto uscendo»** — la sorveglianza passiva è `SIGCHLD` su labwc (la verità) più
`NameOwnerChanged` (l'anticipo). Per comandarlo: `logout()`, **oppure `SIGTERM` a `lxqt-session`**,
che è la stessa cosa. ⛔ Mai `lxqt-leave --logout`: apre una conferma modale.

### 3.5 ⚠ Tre finestre modali possono fermare una sessione non presidiata

1. `QMessageBox` se `dbus-update-activation-environment` non parte in 2 s (`sessionapplication.cpp:81-84`);
2. «Crash Report» dopo 5 crash in 60 s (`lxqtmodman.cpp:330`);
3. ⛔ **il caso peggiore**: `compositor=` vuoto — **che è il default di serie** — fa avviare
   `lxqt-config-session` invece del desktop. Socket, global, cattura e input sarebbero **tutti
   verdi**, e sullo schermo ci sarebbe un wizard di configurazione.

⭐ **Da cui il controllo di prontezza va fatto sul bus, non sui pixel**: `org.lxqt.session` + il
segnale del pannello. È la lezione §2.2 — *un banco che conta non basta* — in forma preventiva.

---

## 4. Il compositore: la matrice, e perché non c'è codice nuovo

*Dettaglio: `rapporti/02-compositori-matrice.md`.*

LXQt dichiara **sette** compositori (`lxqt-wayland-session/README.md:5-14`); **Trixie ne pacchettizza
quattro**: labwc 0.8.3, kwin-wayland 6.3.6, wayfire 0.9.0, sway 1.10.1. Hyprland, niri e river
**[✗]** non ci sono.

| | labwc / sway / wayfire | kwin_wayland 6.3.6 |
|---|---|---|
| **Cattura** | `zwlr_screencopy` v3 | `zkde_screencast` v5 |
| **Permesso** | **nessuno** | `.desktop` + `X-KDE-Wayland-Interfaces` |
| **Input** | `zwlr_virtual_pointer` v2 + `zwp_virtual_keyboard` v1 | libei (EIS su D-Bus) |
| **Appunti** | `zwlr_data_control` **v2** | `zwlr_data_control` **v2** ✅ |
| **Ridimensionamento** | `set_custom_mode`, **senza tetto** | ⛔ misura **fissa** con `--virtual` |

**Una riga su otto in comune fra le due famiglie** — ed è la clipboard, cioè il file che avevamo già.

⭐ **Verdetto: codice nuovo zero, per tutti e quattro.** Sei compositori su sette ricadono sul modulo
wlroots della fase XFCE; il settimo sul modulo KDE.

**Sul caso KWin**, che sarebbe «niente da scrivere»: l'affermazione **regge ma non conviene**, per
quattro riserve — lo script di LXQt pianta `XDG_MENU_PREFIX=lxqt-` e il ramo KWin **non lo corregge**
(`startlxqtwayland.in:66`, `:125-142`), il che secondo `kde.md` §3.3-bis potrebbe lasciare vuoto
l'indice dei servizi e **chiudere il cancello del permesso** [?, da misurare — ⚠ e una seconda lettura
la capovolge: `/etc/xdg/menus/lxqt-applications.menu` **esiste** in `lxqt-menu-data` **[R-pkg]**,
quindi l'indice **dovrebbe** costruirsi]; si eredita la **misura fissa** che labwc non ha; serve
comunque il nostro `.desktop`; e KWin senza Plasma non è mai stato misurato.

⭐ **La scelta indicata è labwc**: è il ripiego di LXQt stesso, il primo nel `Depends` upstream,
ha il ridimensionamento senza tetto e nessun permesso.

### 4.1 ⭐ La matrice, e il numero che cambia il senso della fase

Se un desktop non implica più un compositore, il prodotto non ha «cinque desktop»: ha una **matrice**.

| | |
|---|---|
| combinazioni realistiche su Trixie | **9** |
| coperte oggi | **2** (22 %) |
| coperte **gratis** dalla sola fase wlroots | **+5** |
| **totale dopo la fase wlroots** | ⭐ **8 su 9 — l'89 %** |

**E LXQt ne porta quattro, tutte gratis.** ⚠ Riserva: wayfire vendorizza wlroots **0.17**, quindi il
suo «gratis» è **[?]** finché non si legge quella versione.

### 4.2 Il rilevamento: non chiedere al desktop, guardare i global

`XDG_CURRENT_DESKTOP` **si scrive e non si legge**: lo script di LXQt la costruisce in **tre forme
diverse** nello stesso file, dice `wlroots` anche per compositori che non lo sono, e sbaglia già le
maiuscole in casa propria.

⭐ **Il criterio solido è enumerare i global** con un `wl_display_roundtrip` sul registry: non c'è
ambiguità, perché `zwlr_screencopy_manager_v1` e `zkde_screencast_unstable_v1` sono **mutuamente
esclusivi** su tutta Trixie. Costa zero righe nuove — la connessione al registry esiste già in
`kwin.c:451-495` — e serve anche un compositore fuori elenco.

---

## 5. Che cosa si riusa senza toccare niente

| | |
|---|---|
| **Cattura** | `zwlr_screencopy` su labwc: `xfce.md` §4 **integrale** |
| **Input** | `virtual-keyboard` + `virtual-pointer`: `xfce.md` §7 **integrale**, comprese le cinque trappole |
| **Appunti** | ✅ **`appunti_wlr.c` così com'è**, e la riserva di `xfce.md` §8 **cade**: `kwin_display_apri` **non filtra il socket per nome** (`src/kwin.c:451-484`) — prende `WAYLAND_DISPLAY` e in mancanza prova `wayland-0`…`wayland-9` |
| **Ridimensionamento** | `set_custom_mode`: **integrale, e più facile che su XFCE** (§7) |
| **Audio** | il percorso PipeWire non dipende dal desktop |

⭐ **Le scorciatoie non ci disturbano**: `lxqt-globalkeys` **[✗] non gira affatto su Wayland** — non è
il caso ambiguo del demone che ingoia i tasti senza usarli: `lxqt-session` **lo salta per
costruzione** (`X-LXQt-X11-Only=true` + `lxqtmodman.cpp:106-112`), ed è Xlib puro, **zero rami
Wayland in 3 414 righe** (controllo positivo: 60+ righe X11). Tutti i suoi clienti passano da lui via
D-Bus, quindi sono morti anche loro.

⛔ **Restano le keybind del compositore**, che sono un elenco **completo** in un file che scriviamo
noi — e `W-l → lxqt-leave --lockscreen` è fra quelle di serie (`rc.xml:295-297`): va tolta, o labwc
mangia il tasto comunque (`xfce.md` §7.5).

⚠ **Due dettagli dell'input che LXQt aggiunge:**

1. **NumLock parte spento** (`enableNumlock()` è dietro il cancello X11, e `<numlock>` è commentato in
   `rc.xml`): il tastierino esce in modalità frecce. Rimedio nostro, mettendolo in `mods_locked`;
2. la **disposizione di tastiera**: `lxqt-config-input` **si rifiuta di partire su Wayland**, e nel
   codice c'è un `// FIXME: how to set keyboard layout in Wayland?`. L'unica via è
   `XKB_DEFAULT_LAYOUT` letta da labwc, e **[✗] nessuno legge `/etc/vconsole.conf`** su Trixie: **la
   scriviamo noi, o esce `us`**;
3. ✅ la **ripetizione** la decide labwc (25 Hz / 600 ms) e la applica **esplicitamente anche alle
   tastiere virtuali**: il `[Keyboard]` di LXQt **[✗] non raggiunge il compositore**. Nulla da fare;
4. ⚠ ma `wheelScrollLines=3` in `lxqt.conf [Qt]` è applicato **da Qt dentro ogni applicazione**: un
   nostro scatto diventa **tre righe**. La manopola è lì, non nel nostro accumulatore.

---

## 6. Che cosa si adatta

### 6.1 ⭐ Il cursore: la cura c'è, ma il canale è un altro

**La buona notizia**: su labwc il cursore delle applicazioni **Qt** lo disegna **il compositore**.
labwc espone `wp_cursor_shape_manager_v1` e Qt 6.8 lo usa **prima** di caricare qualunque tema
(`qwaylandinputdevice.cpp:230-236`), e su `set_shape` labwc usa il proprio `xcursor_manager`, cioè il
tema di **`XCURSOR_THEME`**. ⇒ **una leva sola copre compositore e client Qt.**

⛔ **Le tre trappole, tutte pagate altrove in forma diversa:**

| | |
|---|---|
| `session.conf [Environment]` **non serve** | su Wayland labwc è il **padre**: le variabili di `lxqt-session` arrivano troppo tardi. E LXQt **rimuove apposta** `XCURSOR_THEME` da lì (`selectwnd.cpp:188-192`) |
| `~/.icons/default/index.theme` | `lxqt-config-appearance` vi scrive `Inherits=<tema>`, ed è **il ripiego di Xcursor**: se il nostro tema 1×1 non carica, ricompare un cursore visibile da lì |
| il ripiego di Qt sull'hint del tema | fuori da labwc, Qt legge **solo** `QPlatformTheme::MouseCursorTheme`, che `lxqt-qtplugin` prende da `session.conf [Mouse]` — con un **`cursor_size` 16 cablato** che scavalca `XCURSOR_SIZE`. ⇒ impostare **anche** quella chiave, che costa una riga |

✅ E una differenza a nostro favore rispetto a wlroots: se il tema fallisce **lato Qt**, Qt **non**
ripiega su un tema visibile (`qwaylanddisplay.cpp:1054-1064`). Il ripiego visibile resta solo quello
di wlroots, già noto.

### 6.2 ⛔ Energia e blocco: nessuna delle leve già pagate funziona qui

| Leva pagata altrove | Su LXQt |
|---|---|
| `AddInhibition` di powerdevil (KDE) | **[✗]** non esiste |
| `PowerManagement.Inhibit` (XFCE) | **[✗]** LXQt non lo espone né lo consuma: **zero occorrenze**. La domanda «il servizio ha attivazione D-Bus?» **non si pone: non c'è servizio** |
| `LockCommand=/bin/false` (XFCE) | ⛔ **qui apre una `QMessageBox` modale**: un'uscita ≠ 0 chiama `reportLockProcessError()`. Le sole scelte sicure sono **chiave assente/vuota** o **`/bin/true`** |
| KIOSK (KDE) | **[✗]** non esiste |

✅ **Ma il pericolo è molto minore, perché LXQt su Wayland è quasi disarmato:**

- **[✗] `lxqt-powermanagement` non ha alcuna leva che spenga un output**: l'unica che conosce è DPMS
  via XCB, chiusa dentro due `if (platformName()=="xcb")` **senza ramo `else`**;
- **[✗] il server non si addormenta**: le azioni di inattività valgono `-1` (niente) e `doAction(-1)` è
  un ramo vuoto;
- **[✗] «Cambia utente» non esiste in LXQt** (grep con controllo positivo): **metà del requisito è già
  soddisfatta dal desktop**;
- ✅ il blocco schermo **è già inerte**: `lock_command_wayland` è letta **senza default** e nessun file
  spedito la imposta.

⛔ **Restano due pericoli veri, e il primo non è di LXQt:**

1. **l'autostart che LXQt propone per labwc** lancia `swayidle -w timeout 300 "wlopm --off *"` — e
   `~/.config/labwc/` viene copiato **una volta sola** (`if [ ! -d … ]`), quindi una configurazione
   sbagliata è **permanente**;
2. ⛔ **se un locker è installato, il blocco riesce davvero**, perché labwc implementa
   `ext-session-lock-v1`. **Requisito nuovo: nessun `swaylock`/`waylock`/`hyprlock` nell'immagine.**

⭐ **E c'è una leva che non dipende dal desktop, ed è la migliore**: labwc crea
`zwp_idle_inhibit_manager_v1` **incondizionatamente** (`idle.c:81`), e un inibitore fa
`wlr_idle_notifier_v1_set_inhibited(true)`, che **disarma ogni timer `ext-idle-notify`**. Cioè
spegniamo il sorvegliante alla fonte, **qualunque cosa dica la configurazione di LXQt**, senza
chiedere niente a nessuno. ⛔ Non ferma però un `set_mode(OFF)` diretto: la cura di wayvnc
(riaccendere prima di catturare) resta.

⚠ **E una trappola di configurazione che è pura `LEZIONI.md` §1.9**: scrivere
`enableIdlenessWatcher=false` **non basta** — il demone lo **riscrive a `true`** al primo avvio
(`powermanagementd.cpp:112-113`). Serve **anche** `runCheckLevel=1`.

### 6.3 Le voci pericolose

**[✗] Nessun KIOSK, nessun `locked=`**: le voci vanno **tolte**, non bloccate. Tre leve, tutte senza
patch:

1. `.desktop` omonimi con `Hidden=true`/`NoDisplay=true` in `$XDG_DATA_HOME/applications/` per i sette
   file di `lxqt-leave`;
2. **togliere `fancymenu`** dalla chiave `plugins` di `panel.conf` — è il pulsante «Leave», ed è
   **incondizionato, senza chiave, cliccabile anche a menu non caricato** — o sostituirlo con
   `mainmenu`, che in 2.1.4 non ha voci di energia;
3. polkit `no` su logind, che **grigia** Suspend/Hibernate/Shutdown. ⛔ Eccezione: **«Lock screen» non
   è mai grigiata** — non esiste una `canLock()`.

⛔ **E il default Debian ha già una voce pericolosa di serie**: `lxqt-branding-debian` spedisce un
`/etc/xdg/lxqt/panel.conf` con **`lxqt-leave.desktop` fissato nel quicklaunch** **[R-pkg]**.

⚠ `lxqt-policykit-agent` **parte anche su Wayland** e fa `show()` + `activateWindow()`: un dialogo di
autenticazione in una sessione non presidiata. È **[?] una decisione dell'utente**, per coerenza con
il giudizio dato su KDE («le operazioni privilegiate nel terminale funzionano»).

✅ Le **notifiche** non rubano il fuoco (`KeyboardInteractivityNone`) e si zittiscono con
`doNotDisturb=true`. ⛔ Ma `lxqt-leave` usa `KeyboardInteractivityExclusive`: **mentre è aperto,
grabba la tastiera in esclusiva**.

---

## 7. ✅ Il ridimensionamento a caldo: qui siamo l'unico comandante

*È la voce in cui LXQt è **migliore** di tutti e tre i desktop precedenti.*

| | |
|---|---|
| **[✗] nessun componente parla `zwlr_output_manager_v1`** | 2 sole righe in tutto l'albero, e sono stringhe che consigliano `kanshi` |
| `lxqt-config-monitor` passa da **KScreen** | che su Wayland sceglie il backend KWayland, il quale pretende i protocolli **di KWin** — **[✗] assenti in labwc**. `isReady()` falso ⇒ plugin scartato |
| l'unico effetto visibile | un `QMessageBox` «Platform Unsupported… use kanshi» + `exit(1)` — **ma solo se l'utente apre a mano lo strumento**. Si nasconde con un `.desktop` omonimo `NoDisplay=true` |
| il sorvegliante DRM che rilancerebbe lo strumento | è dentro `if (isX11)`: **inerte** |
| ⛔ **da non fare** | impostare `KSCREEN_BACKEND=QScreen`: il backend è valido ma **di sola lettura**, e `setConfig` **ritorna successo** — cioè un «Applica» che non applica |

**E la catena Qt regge, verificata riga per riga**: wlroots manda `logical_size` + `done`, Qt emette
`handleScreenGeometryChange`, e ⭐ **`QWaylandWindow::reset()` ha quattro soli chiamanti, e la
geometria non è fra questi**: niente ricreazione di superfici, niente sfarfallio, niente finestra
nera. Le finestre le riposiziona **labwc**, che ricorda la geometria precedente; il pannello ascolta
`QScreen::geometryChanged` e si rimette a posto.

⛔ **Ma il divieto di `xfce.md` §6.1 si rafforza**: **distruggere** l'output fa montare a Qt un
`QPlatformPlaceholderScreen` — e vale per **tutte** le applicazioni, non solo per i pezzi del
desktop. Si ridimensiona; non si distrugge.

⚠ Una sola riserva, **[?] da misurare**: che labwc generi davvero un `output_layout.change` sul
`set_custom_mode`, che è ciò che fa partire tutta la catena. E un difetto dichiarato upstream
(`lxqt-panel#2432`) dice che **il pannello non segue il resize**: è il primo difetto che l'utente
vedrebbe.

✅ **Scala e DPI: nessuna trappola.** LXQt **[✗]** non gestisce il DPI; a `scale=1` il testo è 1:1 e
il `physical_size` 0×0 del nostro output headless è irrilevante, perché Qt su Wayland restituisce
**96 dpi fissi**. A 4K il testo è nitido ma **piccolo**: la leva pulita è il **font** in
`lxqt.conf [Qt]`, non `QT_SCALE_FACTOR` (che non tocca GTK).

✅ **Le decorazioni**: una barra sola e nessun lampo — Qt manda `unset_mode`, labwc decide per
`rc.xml`, e LXQt spedisce `<decoration>server</decoration>`. **Non toccare né quella chiave né
`QT_WAYLAND_DISABLE_WINDOWDECORATION`.**

---

## 8. Gli appunti, e il coinquilino

*Dettaglio: `rapporti/06-appunti-qt.md`.*

✅ **`appunti_wlr.c` funziona così com'è, su labwc e su KWin.** La riserva aperta da `xfce.md` §8 è
chiusa **in positivo**.

⚠ **Ma LXQt ha un coinquilino che XFCE non aveva: `qlipper`**, che il metapacchetto `lxqt` tira come
dipendenza (`qlipper | clipit | xfce4-clipman`) e `lxqt-core` raccomanda. Si autoavvia da
`/etc/xdg/autostart/`, **non** ha `X-LXQt-X11-Only`, e **rimette l'ultimo elemento quando la clipboard
si svuota** — come klipper, ma **senza marcatura e senza tetto di frequenza** (klipper almeno aveva
10/s).

⭐ **Su Wayland è quasi inerte, e il «quasi» dipende da un `Recommends`**: qlipper è Qt5 e usa solo
`QClipboard`, quindi senza fuoco non vede e non scrive. **Ma** in un'immagine costruita con
`--no-install-recommends` il plugin `qtwayland5` manca, qlipper ripiega su xcb, e **via Xwayland
rinasce coinquilino pieno**. ⚠ **Il banco deve dichiarare quale dei due casi sta misurando** — è
esattamente la forma della lezione §2.3-bis.

**Tre cose su Qt6 che cambiano il nostro codice della clipboard:**

| | |
|---|---|
| ⛔ **mai `text/markdown` in testa** | Qt6 **incolla markdown** se è il primo formato offerto (`qwidgettextcontrol.cpp:2721-2726`) |
| `text/plain;charset=utf-8` | è presentato all'applicazione **come `text/plain`**: offriamo solo l'UTF-8 |
| ⚠ **il tetto di lettura di Qt è 1 secondo** | contro i nostri 5: su rete lenta l'utente vede **un incolla muto** mentre il nostro registro dichiara un trasferimento riuscito. È la lezione §1.7 — *si verifica dal lato che deve ricevere* |

✅ **La primary selection si può ignorare** (un solo uso in tutto l'albero, e **[✗]** nessuna
configurazione che la unisca alla clipboard). ✅ Il ponte **Xwayland** è identico a XFCE, gratis nelle
due direzioni. ✅ E su LXQt+KWin **klipper non c'è**: il suo `.desktop` è `Exec=/usr/bin/false`, è una
libreria di plasmashell.

---

## 9. La configurazione: dove si scrive, e la tensione da chiudere sul banco

⛔ **`LXQt::Settings` scrive nella casa dell'utente alla sola costruzione** (`__userfile__=true` +
`sync()`, `lxqtsettings.cpp:53-59`), e **[✗] non esiste** né un `SystemScope` né un equivalente del
`locked=` di xfconf. ✅ In compenso c'è un `QFileSystemWatcher`: a differenza di `xfconfd`, LXQt
**rilegge a caldo**.

> ### ⚠ Una tensione fra i rapporti, lasciata aperta di proposito
>
> | Chi | Che cosa dice |
> |---|---|
> | `rapporti/03` | i default di sistema in **`/etc/xdg/lxqt/*.conf`** funzionano: `QSettings("lxqt", modulo)` fa fallback chiave-per-chiave, **ed è il meccanismo con cui Debian personalizza LXQt** (`lxqt-branding-debian`) |
> | `rapporti/04` e `rapporti/05` | il percorso di sistema è **uno solo**, quello fissato alla compilazione di Qt, e i file LXQt sono installati in **`/usr/share/lxqt/`** — quindi serve `XDG_CONFIG_DIRS`, e l'unica via sicura è un **`XDG_CONFIG_HOME` effimero** |
>
> **Le due cose possono coesistere** — `QSettings` legge `XDG_CONFIG_DIRS`, il cui default è
> `/etc/xdg`, e Debian può installare in tutti e due i posti. ⛔ **Ma quale percorso vinca sulla
> nostra macchina è una misura, non una lettura**, ed è di quelle che se date per scontate costano un
> pomeriggio: è precisamente la forma di `LEZIONI.md` §1.9. **Misura M6.**

⭐ **Il menu ha lo stesso difetto di garcon, aggravato**: se il file `.menu` non esiste,
`addWatchPath()` non viene **mai** chiamato ⇒ menu morto **per la vita del processo**, il plugin non
ritenta, e all'utente remoto arriva un **`QMessageBox` modale** durante l'avvio del pannello. ✅ Ma
**[✗] nessuna cache su disco** (`USE_MENU_CACHE=OFF`) — il difetto di KDE, l'indice costruito vuoto
che resta vuoto, **qui non può succedere sul disco**; e **[✗]** il difetto dei sottomenu di XFCE non
c'è, perché le directory non sono mai filtrate sull'ambiente.

⚠ **Due dipendenze fragili da tenere d'occhio**: `qt6-wayland` è solo un `Recommends` di `libqt6gui6`
— e **la libreria** `libqt6waylandclient6` è invece dipendenza dura di `lxqt-panel`, quindi **si può
avere la libreria senza il plugin, con apt contento**; e `lxqt-qtplugin` dipende da
`qt6-base-private-abi (= 6.8.2)`, **uguaglianza esatta**: un aggiornamento di Qt lo spegne, e la
sessione parte lo stesso **con un altro aspetto**.

---

## 10. Il piano di misure

*Le prime due decidono se la fase esiste; le altre sono nell'ordine in cui mordono.*

| # | La misura | Perché è lì |
|---|---|---|
| **M1** | ⭐ una sessione LXQt-Wayland **composta a mano** parte davvero: `labwc -S lxqt-session` + le sei variabili di §3.2 | è la voce «da scrivere», e su Trixie non ha precedenti: nessuno l'ha mai installata da pacchetto |
| **M2** | il controllo di prontezza è **sul bus** (`org.lxqt.session` + `moduleStateChanged`) e distingue il desktop dal **wizard** di §3.5 | il caso in cui tutto è verde e sullo schermo c'è un'altra cosa |
| **M3** | ⭐ `set_custom_mode` a cattura viva: pannello, scrivania e applicazioni Qt seguono? | §7, e il difetto `lxqt-panel#2432` dice di no |
| **M4** | il tema del cursore trasparente copre **compositore e client Qt**, e `~/.icons/default/index.theme` non lo scavalca | §6.1: tre canali, e basta che uno resti aperto |
| **M5** | l'inibizione `zwp_idle_inhibit` regge, e **nessuno** spegne l'output in 10 minuti | §6.2, autostart compreso |
| **M6** | ⭐ **quale percorso di configurazione vince**: `/etc/xdg/lxqt/` o `/usr/share/lxqt/` — e ogni valore scritto **si rilegge** | il riquadro di §9, e la lezione §1.9 |
| **M7** | `appunti_wlr.c` contro labwc, **con e senza** qlipper vivo | §8: due casi, e vanno dichiarati entrambi |
| **M8** | prova **guasta di proposito**: `XDG_CURRENT_DESKTOP` sbagliata, e poi `DISPLAY` ereditata | ⭐ imparare **come si legge il guasto** prima di incontrarlo sull'utente. Sono i due difetti che danno «sessione viva e inerte» con un solo `qWarning` |

---

## 11. Le lezioni che questo desktop aggiunge

1. ⭐ **Manca un passo zero-bis alla ricetta**: *«questo desktop, su questa distribuzione, ha una
   sessione Wayland?»* — due comandi (`apt-cache policy`, e cercare in `/usr/share/wayland-sessions/`).
   Qui avrebbero cambiato la fase **prima che cominciasse**, e invece l'abbiamo scoperto al secondo
   rapporto su dieci. Il passo zero esistente chiede *«chi lo fa al mondo?»*; questo chiede **«esiste
   sulla macchina che abbiamo?»**, ed è più a monte.
2. ⭐ **E una domanda 0 alle quattordici**: *«questo desktop ha un compositore, o ne ha un elenco?»*
   Per Mutter, KWin e labwc la risposta era una sola; per LXQt sono **sette**, e cambia la forma della
   risposta a tutte le altre — perché le domande vanno fatte al compositore, non al desktop.
3. ⚠ **Un pacchetto assente non è una funzionalità assente.** Il codice Wayland di LXQt è compilato e
   spedito: manca **il lanciatore**. Se avessimo dedotto «LXQt non fa Wayland» dal `apt-cache policy`
   avremmo saltato un desktop che invece è **il più facile dei quattro**.
4. ⚠ **La versione clonata va confrontata con quella installata, sempre.** Il nostro
   `lxqt-wayland-session` è **0.4.1** e richiede LXQt 2.4: si stava per studiare codice che su Trixie
   non gira. Per gli altri sedici repository le versioni coincidono, e questo è l'unico che avrebbe
   mentito.
5. ⭐ **Il quarto desktop conferma che l'asse giusto è il compositore, non il desktop** — che
   `SPECIFICA.md` §3.8 diceva già, ma ora ha un numero: **8 combinazioni su 9 coperte dopo la sola
   fase wlroots**, e quattro di quelle le porta LXQt senza una riga.
