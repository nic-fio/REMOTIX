# Studio 7 — XFCE su Xubuntu 26.04 e LXQt su Lubuntu 26.04

Data: 18 nov 2026. Agente di studio 7. Solo studio: nessun codice del prodotto toccato, nessuna prova del prodotto.

Convenzioni: **[V]** verificato (dove), **[W]** dal web, **[S]** supposizione.
Sigle dei percorsi: `D:` = `/home/nicfio/Documenti/REMOTIX-DEBIAN` (codice 1.0.0 attuale), `O:` = `/home/nicfio/Documenti/REMOTIX`
(vecchio albero 1.5.x), `P:` = pacchetti Ubuntu 26.04 letti nel contenitore `studio-7` sul server (cartella
`/media/REMOTIX-UBUNTU/studio/7/`: `debs/` i `.deb`, `x/<pacchetto>/` i file estratti, `src/` i sorgenti upstream, `sim-*.txt` le
simulazioni `apt-get -s install`).

---------------------------------------------------------------------------------------------------

## 1. Riassunto

1. **Il riconoscimento di Xubuntu è rotto nel codice attuale** (`D:src/session.c:382-393`): `desktop_of_session_name("xubuntu")`
   restituisce `NONE`, perché il nome non contiene «xfce». Su un Xubuntu vero `gnome-session-bin` + `gnome-shell` ci sono
   (§3), quindi il codice vede «due desktop», chiede la dichiarazione di lightdm (`user-session=xubuntu`), non la sa tradurre e ricade
   sull'ordine fisso: **GNOME vince**. Va rimessa la mappa `xubuntu`/`lubuntu` (con «ubuntu» chiesto per ultimo). Lubuntu non ha
   questo problema (un solo desktop installato).
2. **Il meccanismo D-153 (cartelle di sessione come un accesso locale) serve identico, e su Ubuntu 26.04 è vivo**:
   `/etc/X11/Xsession.d/60x11-common_xdg_path` esiste in `x11-common 1:7.7+26ubuntu1` [V]. Senza D-153 Xubuntu avrebbe il pannello standard
   di XFCE (niente whisker menu, niente `defaults.rc`, niente temi) e Lubuntu niente `xdg-Lubuntu` (pannello, tema, `session.conf`).
   Due dettagli nuovi rispetto al vecchio albero (§5.4): `XDG_SESSION_DESKTOP` sotto SDDM vale `LXQt`, non `Lubuntu`; e
   `56xubuntu-session` imposta tre variabili (`QT_QPA_PLATFORMTHEME=gtk2`, ...) che la sessione remota non ha.
3. **Il difetto del whisker menu (D-X3) non è mai stato corretto** nemmeno nel vecchio albero: `xfce_restore_copy()` è **identica**
   byte per byte nei due alberi [V: `diff` delle due funzioni]. Su Xubuntu pesa di più che su Debian: il pannello di Xubuntu **non
   ha il pulsante `actions`**, ha solo il whisker menu (`plugin-1`), quindi tutta la protezione delle voci di
   spegnimento passa dal blocco del whisker (§6.1). Causa esatta non chiarita (solo osservata), serve una riproduzione.
4. Gli altri difetti visti sul vecchio banco sono **già curati nel codice attuale** (residui nello scope, primo rientro respinto,
   logind `closing`/`active`) o **non sono difetti** (qlipper: decisione 16 nov «si lascia»); l'unico buco del codice attuale
   che resta e tocca Xubuntu è `survivor()` (processi non-dumpable come `ssh-agent`, §6.2).
5. XFCE rifiuta il Log Out mentre si avvia anche con l'`xfce4-session` di Ubuntu (4.20.4): **sì, stesso codice** [V: sorgente
   `xfsm-manager.c:2402-2454`]. La cura (forzare dopo il tempo concesso, `kill_xfce()`) è già nel codice.
6. Versioni di Ubuntu 26.04 [V]: `xfce4-session 4.20.4`, `libxfce4windowing-0-0 4.20.5` (>= 4.20.4: lo sfondo nero E1 dovrebbe
   non esserci, da verificare con una foto), `xfdesktop4 4.20.1`, `xfce4-panel 4.20.7`, `xfce4-whiskermenu-plugin 2.10.1`, `lightdm 1.32.0`,
   `lxqt-session 2.3.0`, `lxqt-panel 2.3.2`, `lxqt-wayland-session 0.3.1` (esiste ma **non** è installato da Lubuntu), `sddm 0.21.0`,
   `labwc 0.9.3`, `wlr-randr 0.4.1`, `systemd 259.9`, `xwayland 24.1.10`.
7. **`labwc`, `wlr-randr` e `xwayland` non arrivano né con `xubuntu-desktop` né con `lubuntu-desktop`** [V: simulazioni]: restano a
   carico del pacchetto REMOTIX (oggi `Recommends`, `D:debian/control:97-101`). Con `--no-install-recommends` XFCE/LXQt non nascono.

---------------------------------------------------------------------------------------------------

## 2. Come REMOTIX avvia oggi XFCE e LXQt (Debian 13, 1.0.0)

Tutto in `D:src/session.c` (7404 righe) e `D:src/session.h`.

| Pezzo | Dove | Che cosa fa |
|---|---|---|
| marcatori dei desktop | `session.c:512-615` (`recognize_desktop()`) | GNOME = `gnome-session` **e** `gnome-shell` nel PATH; KDE = `startplasma-wayland`; XFCE = `xfce4-session`; LXQt = `lxqt-session`. Ordine: KDE (senza GNOME) / GNOME / XFCE / LXQt |
| più desktop installati | `session.c:533-553` | se ≥ 2 marcatori: `declared_desktop()` sceglie il desktop dichiarato dal display manager attivo |
| dichiarazione | `session.c:440-475` (`declared_sessions()`) | lightdm: `user-session` in `/usr/share/lightdm/lightdm.conf.d`, `/usr/local/share/...`, `/etc/xdg/lightdm/...`, `/etc/lightdm/lightdm.conf.d`, poi `/etc/lightdm/lightdm.conf`; sddm: `[Autologin] Session` in `/usr/lib/sddm/sddm.conf.d`, `/etc/sddm.conf.d`, `/etc/sddm.conf`. Conta solo il DM attivo (`active_display_manager()`, `session.c:399`, legge `/etc/X11/default-display-manager` poi il link di `display-manager.service`); se è altro (gdm3...) i file di lightdm/sddm sono ignorati |
| nome → desktop | `session.c:382-393` (`desktop_of_session_name()`) | **oggi**: `xfce`→XFCE, `lxqt`→LXQt, `plasma`/`kde`→KDE, `gnome`→GNOME |
| avvio XFCE | `session.h:174` | `labwc -m --session xfce4-session` (labwc è il compositore, `xfce4-session` il suo client primario); `XFCE4_SESSION_COMPOSITOR` = quella riga |
| avvio LXQt | `session.h:219-227` | `labwc -C <cartella nostra> -S lxqt-session` (stessa forma dello script upstream `startlxqtwayland` 0.1.1, con `-C` in `XDG_RUNTIME_DIR`) |
| ambiente | `session.c:2526-2700` | XFCE: `XDG_CURRENT_DESKTOP=XFCE`, `XDG_MENU_PREFIX=xfce-`, `add_session_names(.., "xfce", TRUE)`, `XDG_CONFIG_DIRS=<labwc-xfce>:<sessione>:<resto>`. LXQt: `XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots`, `QT_QPA_PLATFORM=wayland` (nudo), `QT_QPA_PLATFORMTHEME=lxqt`, `XDG_CONFIG_DIRS=<xdg-lxqt>:<sessione>/etc:/etc/xdg:/usr/share`, `XDG_DATA_DIRS=<data-lxqt>:...` |
| cartelle di sessione (D-153) | `session.c:2270-2290` (`local_session()`) | **svuotata il 17 nov**: restituisce sempre `name/config/data = NULL`, scrive la stessa riga di log. Chiamanti: `session_config_dirs()` (2377), `session_config_given()`, `session_data_dirs()`, `add_session_names()` (2416), il ramo LXQt (2593-2597), `default_plugins()` (5124) |
| ambiente dal manager utente | `session.c:2300-2370` (`manager_value()`, `dir_in_front()`, `list_base()`) | `XDG_CONFIG_DIRS`/`XDG_DATA_DIRS` presi dal manager utente (snapd, flatpak) senza gli elementi `/remotix/`; **questo resta** e vale su Ubuntu |
| «sessione viva?» | `session.c:1015-1027` | XFCE: nome `org.xfce.SessionManager` sul bus utente; LXQt: `org.lxqt.session` |
| uscita XFCE | `session.c:3685-3735` | `org.xfce.Session.Manager.Logout(false,false)`; forzata: SIGTERM a `labwc` (`kill_xfce()`) |
| uscita LXQt | `session.c:~3750-3800` | `org.lxqt.session.logout()` su `/LXQtSession` (Q_NOREPLY), mai `lxqt-leave --logout` |
| pulizia dello scope | `session.c:4359-4420` (`survivor()`, `session_clear_out_scope()`) | dopo l'uscita, SIGTERM (poi SIGKILL dopo 2 s) a ogni processo dell'utente rimasto nello scope logind |
| voci pericolose XFCE | `session.c:5348-5530` (`xfce_restore_copy()` ecc.), `6345-6700` (`XFCE_LOCKS`, `xfce_panel_xml()`, `WHISKER_HIDE`) | blocca nel canale xfconf della sessione i pulsanti spegni/riavvia/sospendi/blocca, copia i valori dell'utente in `~/.local/state/remotix/xfce-chiavi` e li rimette alla fine |
| voci pericolose LXQt | `session.c:6155-6290` (`settings_lxqt()`), `5719-5850` (`lxqt_session_commands()`) | `.desktop` `Hidden=true` per `lxqt-leave/-lockscreen/-suspend/-hibernate/-shutdown/-reboot` in `data-lxqt`; `lxqt-leave` nostro che fa sempre `--logout` |
| chiusura leggera | `D:src/child.c:9921` (`local_light_close()`) | smonta solo ciò che è nostro quando l'utente ha una sessione locale; non ripristina le chiavi XFCE |
| chiusura per accesso locale | `D:src/rootside.c:2400-2420`, `D:src/local_login.c` | 1.0.0: `pam_exec` chiude il desktop remoto **prima** che parta quello locale (DECISIONS-11 §11.57) |

Differenza con il vecchio albero (`O:src/session.c`): l'intero blocco 270-640 è identico al nuovo, salvo `desktop_of_session_name()`
(vecchio: `xubuntu`, `lubuntu`, `kubuntu`, `ubuntu` mappati, con commento «xubuntu, lubuntu e kubuntu contengono ubuntu: chiederli
PRIMA») e `local_session()` con le tre funzioni d'appoggio (vecchio `session.c:2274-2380`: `session_folder_there()`, `by_name()`,
`local_session_name_find()`, `xsession_d_applies()`). Tolti il 17 nov: `D:docs/PULIZIA-tranche1.md` voci 4 e 7;
`D:docs/INVENTARIO-non-debian.md` righe su `session.c:381-393, 283-290, 519, 2250-2259`.

---------------------------------------------------------------------------------------------------

## 3. Che cosa c'è davvero in Ubuntu 26.04 (dai pacchetti)

### 3.1 Dipendenze dei metapacchetti [V: `apt-cache depends` e `apt-get -s install` nel contenitore, 26.04.1, indice del 18 nov]

- `xubuntu-desktop 2.272`: Depends `lightdm`, `lightdm-gtk-greeter`, `xfce4-session`, `xubuntu-default-settings`,
  `xubuntu-desktop-minimal`, `xubuntu-artwork`, ...; Recommends `xfce4-whiskermenu-plugin` (anche in `-minimal`!), `snapd`, `gnome-disk-utility`, ...
  Installazione simulata: 744 pacchetti senza Recommends, 1742 con. **Nessun `gdm3`/`sddm`/`labwc`/`lxqt-session`.**
- Pacchetti GNOME che arrivano con Xubuntu: `gnome-shell 50.1` e `gnome-settings-daemon 50.0` già **senza** Recommends
  (tirati da `network-manager-applet`, `update-notifier`, `xdg-desktop-portal-gnome`, `gnome-control-center`); con i Recommends anche
  `gnome-session-bin` (contiene `/usr/bin/gnome-session`, [V: `apt-file`]), `ubuntu-session`, `gdm3` (tirato da `gnome-shell`).
  ⇒ Con il default di `apt` (Recommends accesi) un Xubuntu ha **entrambi** i marcatori GNOME (`gnome-session` e `gnome-shell`),
  quindi il codice entra nel ramo «più desktop» (`session.c:533`). Con `--no-install-recommends` no (`gnome-session` manca): il 1.5.2 ha
  reso necessarie tutte e due.
- `lubuntu-desktop 26.04.3`: Depends `lubuntu-desktop-minimal`, `lxqt-core`, `sddm`, `sddm-theme-lubuntu`, `lxqt-notificationd`, `lxqt-policykit`, `lxqt-powermanagement`,
  ...; Recommends `lubuntu-default-settings`, `qlipper`, `snapd`. Installazione simulata: 800 / 1781 pacchetti. **Nessun GNOME, nessun KDE
  (`plasma-workspace` assente), nessun `lxqt-wayland-session`, nessun `labwc`.** ⇒ un solo marcatore: nessuna dichiarazione necessaria.
- `labwc`, `wlr-randr`, `xwayland`: assenti da entrambe le simulazioni (solo `xwayland` entra con i Recommends di Xubuntu).

### 3.2 Display manager e dichiarazione

- **Xubuntu → lightdm 1.32.0.** `xubuntu-default-settings 26.04` porta `/usr/share/lightdm/lightdm.conf.d/60-xubuntu.conf` =
  `[Seat:*] user-session=xubuntu` e `50-xubuntu-numlock.conf` [V]. Il pacchetto `lightdm` non mette nulla in `lightdm.conf.d`; mette
  `/etc/lightdm/lightdm.conf` (vuoto di sostanza). Il `postinst` di lightdm scrive `/etc/X11/default-display-manager` solo se debconf lo
  decide (`shared/default-x-display-manager`) [V: `lightdm.postinst`].
- **Lubuntu → SDDM 0.21.0.** `lubuntu-default-settings 26.04.2` porta `/etc/sddm.conf.d/lubuntu_settings.conf` con solo `[General]
  InputMethod=` e `[Theme] Current=lubuntu` [V]. **Nessuna chiave `Session`**: la dichiarazione di sddm per Lubuntu è vuota.
  Non esiste un `20-lubuntu.conf` analogo al `20-kubuntu.conf` di Kubuntu. (Il pacchetto `sddm` non porta file in `sddm.conf.d`.)
- La logica attuale `declared_sessions()` copre le cartelle giuste (lightdm: tutte e quattro + file; sddm: `/usr/lib/sddm/sddm.conf.d` e
  `/etc/sddm.conf.d`; i file veri stanno in `/usr/share/lightdm/...` per Xubuntu e `/etc/sddm.conf.d` per Kubuntu/Lubuntu) [V].

### 3.3 Sessioni offerte [V: file `.desktop` dei pacchetti]

| File | Pacchetto | `Exec` | `DesktopNames` | Nota |
|---|---|---|---|---|
| `/usr/share/xsessions/xubuntu.desktop` | xubuntu-default-settings | `startxfce4` | `XFCE` | la sessione **predefinita** di Xubuntu (X11) |
| `/usr/share/xsessions/xfce.desktop` | xfce4-session | `startxfce4` | `XFCE` | |
| `/usr/share/wayland-sessions/xfce-wayland.desktop` | xfce4-session | `startxfce4 --wayland` | `XFCE` | **esiste una sessione XFCE Wayland**; non è quella predefinita; nome sessione `xfce-wayland` → **non** ha cartella `xdg-xfce-wayland` (niente impostazioni Xubuntu) |
| `/usr/share/xsessions/Lubuntu.desktop` | lubuntu-default-settings | `/usr/bin/startlxqt` | `LXQt` | la sessione predefinita di Lubuntu (X11, `window_manager=openbox`) |
| `/usr/share/xsessions/lxqt.desktop` | lxqt-session | `startlxqt` | `LXQt` | |
| `/usr/share/wayland-sessions/lxqt-wayland.desktop` | lxqt-wayland-session | `startlxqtwayland` | `LXQt` | **non installata** da Lubuntu |
| `/usr/share/wayland-sessions/ubuntu.desktop` | ubuntu-session (tirata da Xubuntu con i Recommends) | | | non nostra, ma attenzione: un Xubuntu completo la offre |

Quindi **l'accesso locale predefinito di Xubuntu e di Lubuntu è X11**; la sessione remota REMOTIX è invece Wayland su labwc. D-153 imita
solo le *cartelle* e i nomi di sessione dell'accesso X11 predefinito (è già così nel vecchio albero e ha funzionato sul banco, §7).

### 3.4 Cartelle di sessione [V]

- Xubuntu: `/etc/xdg/xdg-xubuntu/` (da `xubuntu-default-settings`): `xfce4/panel/default.xml` (panello: `plugin-1 whiskermenu`, 2 separator, 3
  tasklist, 4 separator, 5 systray, 6 notification-plugin, 7 power-manager-plugin, 8 pulseaudio, 9 clock — **nessun `actions`**),
  `xfce4/xfconf/xfce-perchannel-xml/{xfce4-session,xfwm4,xsettings,xfce4-power-manager,xfce4-keyboard-shortcuts,xfce4-desktop,...}.xml`,
  `xfce4/whiskermenu/defaults.rc` (`show-command-switchuser=false`, `command-switchuser=dm-tool switch-to-greeter`,
  `command-lockscreen=xflock4`, `command-logout=xfce4-session-logout`), `menus/xfce-applications.menu`, `Thunar/`, `autostart/`.
  E `/usr/share/xubuntu/` (applicazioni, template). Più `/etc/X11/Xsession.d/56xubuntu-session` (§5.4).
  `xfce4-session.xml` di Xubuntu: `compat/LaunchGNOME=true`, `shutdown/LockScreen=true`, nessun `WaylandLogoutCommand`.
- Lubuntu: `/etc/xdg/xdg-Lubuntu/` (da `lubuntu-default-settings`): `lxqt/{session,lxqt,panel,windowmanagers,globalkeyshortcuts,
  notifications,lxqt-powermanagement,lxqt-runner,lxqt-config-appearance}.conf`, `pcmanfm-qt/lxqt/settings.conf`, `Kvantum/`,
  `gtk-3.0/`, `qterminal.org/`, `openbox/rc.xml`, `autostart/` (blueman, `lubuntu-update-autostart`, `lxqt-qlipper-autostart`,
  `lxqt-xscreensaver-autostart` [`X-LXQt-X11-Only=true`], nm-applet [`Hidden=true`], nm-tray, picom [**senza** `X11-Only`], print-applet).
  E `/usr/share/Lubuntu/` (applications, mimeapps) e `/usr/share/lubuntu/qt/`.
  Attenzione: la cartella `/usr/share/Lubuntu` ha la **L maiuscola**, come il nome sessione (la mappa nome→desktop minuscola va bene,
  ma `session_folder_there()` e `/etc/xdg/xdg-<nome>` vanno composti con il nome ESATTO del file).

---------------------------------------------------------------------------------------------------

## 4. Il riconoscimento su Xubuntu: la regola e il confronto

**La regola del vecchio albero (1.5.2)**, decisa dopo la misura del 14 nov: `gnome-session` da solo non è GNOME; GNOME è riconosciuto solo
con anche `gnome-shell`; se due o più desktop sono installati decide la dichiarazione del display manager **attivo**
(lightdm `user-session`; sddm `[Autologin] Session`, solo come indizio); con DM attivo altro (gdm3...) i file di lightdm/sddm contano zero
e vale l'ordine fisso GNOME, KDE, XFCE, LXQt. Una riga di log dice quando ha deciso la dichiarazione (`desktop_description`).
Fonti: `O:src/session.c:281-300, 512-620`, `O:CHANGES-1.5.md:323`, decisione D-DE-006 (`O:assessment/xfce/ubuntu2604.md` R-DE-005/006/007: VERDE).

**Il banco di allora**: l'immagine aveva Xubuntu + GNOME + **gdm3 attivo** (`/etc/X11/default-display-manager=/usr/sbin/gdm3`): con la
regola, «vinceva GNOME» **correttamente** (non era un difetto, era un banco sbagliato; R-DE-006 VERDE «con gdm3 attivo i file lightdm non
contano»). Per avere un Xubuntu vero il banco mise lightdm come DM attivo e il prodotto scelse XFCE. [V: `O:assessment/xfce/ubuntu2604.md:6-17`]
Su una macchina vera Xubuntu il DM attivo è lightdm [V: dipendenza di `xubuntu-desktop`]; gdm3 vi comparirebbe solo se
installato dai Recommends E scelto da debconf: **da misurare** (§11, incognita 1).

**Confronto con l'attuale** (`D:src/session.c`):
- La parte «`gnome-session` + `gnome-shell`», il «più desktop», `declared_sessions()`, `active_display_manager()` sono **identiche** al vecchio
  albero [V: `diff` delle righe 270-640: solo i due commenti/`desktop_of_session_name` differiscono].
- Differisce solo `desktop_of_session_name()`: **senza `xubuntu` e `lubuntu`**. Con lightdm che dichiara `xubuntu` il risultato è `NONE`
  (`session.c:485-490`: `d != NONE && present[d]` è falso), quindi `decl == NONE` e nessun marcatore viene scartato:
  `plasma` assente, `gnome` presente → il ramo `else if (gnome)` (`session.c:560`) **sceglie GNOME**. È esattamente il difetto del 1.5.2 tornato.
- Lubuntu non è colpito (nessun secondo desktop), ma D-153 ha comunque bisogno di sapere che `Lubuntu` è un nome LXQt (§5).

**Regola da ripristinare** [vecchio `O:src/session.c:381-393`]: chiedere `xubuntu` con XFCE, `lubuntu` con LXQt, `kubuntu` con KDE (agente 6), e
**solo dopo** `ubuntu` con GNOME (agente 3: `ubuntu` è la sessione GNOME di Ubuntu). L'ordine è obbligatorio perché tutti e tre i nomi
contengono «ubuntu». Con la minuscola forzata (`g_ascii_strdown`) `Lubuntu` va bene.

Altri punti del riconoscimento da sapere:
- XFCE e LXQt entrambi installati: vince XFCE con la nota «AMBIGUOUS» (`session.c:576-584`); su Xubuntu/Lubuntu non capita mai (§3.1).
- Caso Ubuntu Desktop + `xubuntu-desktop` (gdm3 resta attivo): vince GNOME per regola; è coerente con «una macchina, un desktop».
- `libpam`/`dm-tool`: la voce «Cambia utente» del whisker usa `dm-tool switch-to-greeter` (lightdm); in sessione remota sposterebbe il
  **monitor del server** alla schermata di accesso: motivo in più per bloccarla (§6.1).

---------------------------------------------------------------------------------------------------

## 5. Emulare l'accesso locale: D-153, che cosa fa e che cosa serve su Ubuntu

### 5.1 Che cosa fa un accesso locale vero [V: sorgenti e script di Ubuntu 26.04]

**Xubuntu (lightdm 1.32.0, `src/seat.c:984-991`)**: nell'ambiente del processo di sessione mette
`XDG_SESSION_DESKTOP=<nome sessione>`, `DESKTOP_SESSION=<nome sessione>`, `GDMSESSION=<nome sessione>` (`<nome sessione>` = nome del file `.desktop`,
senza estensione: `xubuntu`) e `XDG_CURRENT_DESKTOP` = `DesktopNames` unito con `:` (`XFCE`). Poi `lightdm-session` (`/usr/sbin/lightdm-session`)
legge `/etc/profile`, `~/.profile`, `/etc/xprofile`, ..., e **esegue tutti gli `/etc/X11/Xsession.d/*`** prima di `exec` della sessione.
Lì `60x11-common_xdg_path` (da `x11-common 1:7.7+26ubuntu1`) fa: se `DESKTOP_SESSION` non è vuoto, **prepone `/etc/xdg/xdg-$DESKTOP_SESSION` a
`XDG_CONFIG_DIRS`** (partendo da `/etc/xdg` se vuoto), e, se `DESKTOP_SESSION != gnome`, **prepone `/usr/share/$DESKTOP_SESSION` a `XDG_DATA_DIRS`**
(default `/usr/local/share/:/usr/share/`); entrambi con test «già presente?». Poi `56xubuntu-session` (Xubuntu) fa, se `DESKTOP_SESSION = xubuntu`:
`GTK_OVERLAY_SCROLLING=0`, `QT_QPA_PLATFORMTHEME=gtk2`, `CLUTTER_BACKEND=x11`.
Risultato atteso su Xubuntu: `XDG_CONFIG_DIRS=/etc/xdg/xdg-xubuntu:/etc/xdg`, `XDG_DATA_DIRS=/usr/share/xubuntu:/usr/local/share/:/usr/share/:...`.

**Lubuntu (SDDM 0.21.0, `src/daemon/Display.cpp:451-460`)**: `DESKTOP_SESSION` = **nome del file** senza estensione (`Lubuntu`, con la L maiuscola);
`XDG_CURRENT_DESKTOP` = `DesktopNames` con `;`→`:` (`LXQt`); **`XDG_SESSION_DESKTOP` = `DesktopNames`** (cioè `LXQt`, non `Lubuntu`: sotto
systemd sddm usa `desktopNames()`). Per una sessione **X11** lo script è `/usr/share/sddm/scripts/Xsession`, che esegue `/etc/X11/Xsession.d/*`
(quindi `60x11-common_xdg_path` con `DESKTOP_SESSION=Lubuntu` → `/etc/xdg/xdg-Lubuntu` e `/usr/share/Lubuntu`). Per una sessione **Wayland**
lo script `/usr/share/sddm/scripts/wayland-session` legge solo `/etc/profile` e `~/.profile` e **non** esegue `Xsession.d` [V: i due script];
confermato dal commento del vecchio albero («`[M]` sddm's Wayland launcher does not», `O:src/session.c:2328-2332`).

Stessa cosa in ogni caso: **chi imposta cosa**: il display manager imposta `DESKTOP_SESSION`/`XDG_SESSION_DESKTOP`/`XDG_CURRENT_DESKTOP`;
`60x11-common_xdg_path` (solo accesso X11 via `Xsession.d`) prepone le cartelle; `/etc/profile` (e `/etc/profile.d`) è letto da entrambi.

### 5.2 Che cosa faceva D-153 nel vecchio albero [V: `O:src/session.c:2240-2380`]

`local_session()` calcolava una sola volta (struttura `{name, config, data}`):
1. **nome**: GNOME → la sessione che REMOTIX avvia (`gnome_session()->id`); altrimenti il nome **dichiarato dal display manager** se nomina il desktop scelto;
   altrimenti il primo (ordine alfabetico, `strcmp`) dei file in `/usr/share/xsessions` e `/usr/share/wayland-sessions` che ha un nome di quel desktop **e**
   una cartella `/etc/xdg/xdg-<nome>` o `/usr/share/<nome>` (`session_folder_there()`);
2. **meccanismo**: `xsession_d_applies()`: vero solo se esiste `/etc/X11/Xsession.d/60x11-common_xdg_path` **e** (esiste `xsessions/<nome>.desktop` oppure il DM non è sddm);
3. se vero: `config = /etc/xdg/xdg-<nome>` (se è una cartella), `data = /usr/share/<nome>` (se esiste e `nome != gnome`); altrimenti il nome stesso è cancellato.
Usi: `session_config_dirs()` (cartella di sessione **dopo** quella di REMOTIX, prima di quella di sistema), `session_data_dirs()`, `DESKTOP_SESSION` e `XDG_SESSION_DESKTOP`
(`add_session_names()`), lettura del `default.xml` del pannello (`default_plugins()`), ramo LXQt. Provato sul vecchio banco Ubuntu 26.04 [V: `O:assessment/xfce/ubuntu2604.md`,
`O:assessment/lxqt/ubuntu2604.md`]:
- Xubuntu: `DESKTOP_SESSION=xubuntu`, `XDG_SESSION_DESKTOP=xubuntu`, `XDG_CONFIG_DIRS=/run/user/1001/remotix/labwc-xfce:/etc/xdg/xdg-xubuntu:/etc/xdg`,
  `XDG_DATA_DIRS=/usr/share/xubuntu:…`: «Xubuntu now gets its own panel, as at the machine» (`O:CHANGES-1.5.md:350`, DECISIONS §10.54).
- Lubuntu: «session «Lubuntu» (a session file with its own folders): config folder /etc/xdg/xdg-Lubuntu, data folder /usr/share/Lubuntu»;
  `XDG_CONFIG_DIRS=…/xdg-lxqt:/etc/xdg/xdg-Lubuntu:/etc:/etc/xdg:/usr/share`; `XDG_DATA_DIRS=…/data-lxqt:/usr/share/Lubuntu:/usr/local/share/:/usr/share/:/var/lib/snapd/desktop`.
Perché fu tolta il 17 nov: su Debian `60x11-common_xdg_path` non esiste → funzione sempre vuota (`D:docs/PULIZIA-tranche1.md` voce 7).

### 5.3 Serve identico o va ripensato?

**Serve, e quasi identico.** Su Ubuntu 26.04 `60x11-common_xdg_path` esiste [V], quindi `xsession_d_applies()` torna a essere vero. Si possono ripristinare le tre
funzioni e il corpo di `local_session()` così com'erano (il codice del 17 nov ha lasciato intatti tutti i chiamanti: `session_config_dirs`, `add_session_names`, ramo LXQt,
`default_plugins`). Quello che **va ripensato** (cose che il vecchio albero non faceva o faceva in modo approssimativo):

1. **`XDG_SESSION_DESKTOP` su Lubuntu**: vecchio `add_session_names(.., "lxqt", FALSE)` lo metteva a `Lubuntu` (il nome sessione). Un accesso SDDM dà `LXQt`
   (`desktopNames`). Sotto lightdm invece è il nome sessione (`xubuntu`). Va deciso se si vuole imitare *esattamente* ciascun DM (regola «remoto = locale») o tenere il nome
   sessione. Chi legge `XDG_SESSION_DESKTOP`: `systemd`/`logind` (solo informativo), alcuni portali; effetto pratico probabilmente nullo [S]. Proposta: imitare il DM attivo.
2. **`56xubuntu-session`** (§5.1): tre variabili non impostate dalla sessione remota. `QT_QPA_PLATFORMTHEME=gtk2` cambia l'aspetto delle app Qt su Xubuntu (locale: stile GTK;
   remoto: Qt nudo). `CLUTTER_BACKEND=x11` irrilevante. `GTK_OVERLAY_SCROLLING=0`: barre di scorrimento. Se vale «un'unica regola: remoto = accesso locale meno i danni da server condiviso»,
   la regola generale sarebbe «eseguire (o imitare) gli `Xsession.d` della sessione», cosa troppo larga: **proposta minima** = imitare solo `60x11-common_xdg_path` (cartelle) e
   decidere a parte le tre variabili di Xubuntu (piccole, specifiche del gusto) — decisione del proprietario (§10, punto 5).
3. **Dove sta la dichiarazione per Lubuntu**: non c'è (§3.2); il vecchio terzo ramo (file di sessione con cartella propria, primo in ordine) trova `Lubuntu` perché `lxqt.desktop` non ha
   cartella. Funziona per costruzione ma è fragile se in futuro `lxqt-session` portasse `/etc/xdg/xdg-lxqt`: la sessione `lxqt` ordinerebbe **dopo** `Lubuntu`? No: `strcmp` mette `L` (0x4C)
   prima di `l` (0x6C), quindi `Lubuntu` vince comunque, ma per caso. [S]
4. **Maiuscole**: `desktop_of_session_name()` abbassa le lettere solo per il confronto; `clean_session_name()` conserva il nome e `/etc/xdg/xdg-Lubuntu` ha la L maiuscola: va tenuto il nome esatto. (Già così nel vecchio albero.)
5. **Wayland predefinito?** Se in una release futura Lubuntu usasse `lxqt-wayland` come sessione predefinita su SDDM, `Xsession.d` non girerebbe e la cartella `xdg-Lubuntu` **non** sarebbe nel locale;
   `xsession_d_applies()` (che guarda il file `xsessions/<nome>.desktop`) lo gestisce già (§5.2 punto 2). Oggi (26.04) non è il caso [V: nessun pacchetto Wayland installato].
6. **Sessione `xfce-wayland` scelta a mano a lightdm**: locale = `DESKTOP_SESSION=xfce-wayland`, nessuna cartella Xubuntu; la dichiarazione `user-session=xubuntu` fa comunque
   imitare Xubuntu: scelta voluta («la macchina è Xubuntu»), da annotare.
7. **Dipendenza dall'ordine tra D-153 e la scelta del desktop**: `local_session()` usa `desktop_session()`; deve essere chiamata dopo `recognize_desktop()` (già vero nel vecchio codice).

### 5.4 Coordinamento con l'agente 3 (GNOME / sessione `ubuntu`)

Il corpo di `local_session()` e le funzioni sono **uno solo e comune**; l'agente 3 deve sapere:
- il ramo `d == SESSION_DESKTOP_GNOME` di `local_session_name_find()` usa `gnome_session()->id` (`ubuntu`/`gnome`) e `60x11-common_xdg_path` esclude `gnome` solo per `XDG_DATA_DIRS`;
  per `ubuntu` (cartelle `/etc/xdg/xdg-ubuntu`, `/usr/share/ubuntu` se esistono) vale lo stesso meccanismo e lo stesso `xsession_d_applies()` (GDM esegue `Xsession.d` per sessioni X11
  e, secondo il vecchio commento, il suo lanciatore Wayland — da misurare per GDM, non è affar mio);
- **la mappa dei nomi**: «ubuntu» va sempre per ultimo; i miei `xubuntu`/`lubuntu` devono precedere; Kubuntu (agente 6) usa `plasma`, non serve `kubuntu` ma non fa danno;
- `desktop_of_session_name()` è una funzione **sola**; concordo di ripristinare la versione del vecchio albero in blocco.
Nessun documento dell'agente 3 era ancora presente in `studio/` al momento della scrittura: questo paragrafo è la mia proposta scritta di forma comune.

---------------------------------------------------------------------------------------------------

## 6. I difetti già visti su Xubuntu e Lubuntu: causa, cura, stato nel codice attuale

### 6.1 Whisker menu perso dal pannello dopo una chiusura leggera (D-X3, R-DE-012/064/066) — **non curato**
- **Visto** (`O:assessment/xfce/ubuntu2604.md`): dopo la chiusura leggera (10:35:04, «the XFCE keys are NOT restored») e il ripristino alla nascita successiva (10:36:15 «`xfce4-panel
  /plugins/plugin-1/show-command-* NOT put back`»), il pannello dell'utente `prova` ha perso `plugin-1` (whisker): file utente con plugin-2…9. Inoltre, anche senza chiusura leggera, durante la sessione
  remota il file dell'utente riceve il plugin bloccato come `type="empty"`; se il Log Out avviene mentre il client si stacca il ripristino slitta alla prossima sessione (`ripristinato=false`).
- **Perché pesa su Xubuntu**: il `default.xml` di Xubuntu (§3.4) non ha `actions`; la protezione delle voci di spegnimento è solo il blocco di sei chiavi `show-command-*` del whisker
  (`WHISKER_HIDE`, `session.c:6424`; `xfce_panel_xml()` 6432). Quindi su Xubuntu **tutto** il blocco XFCE passa dal codice del whisker, mentre su Debian (pannello con `applicationsmenu` + `actions`) è il percorso `actions`.
- **Con D-153 spento (stato attuale)** il `default.xml` letto da `default_plugins()` è `/etc/xdg/xfce4/panel/default.xml` (quello di XFCE: `applicationsmenu`, `actions`...), non quello di Xubuntu: per un utente
  che non ha mai aperto XFCE la sessione remota blocca un `actions` che il suo pannello (Xubuntu) non avrà, e il pannello nasce con il layout stock di XFCE (e il «primo salvataggio lo rende suo»: è il difetto D-153 originale).
- **Causa nel meccanismo** (`session.c:5348-5420`, funzione **identica** nei due alberi): al primo avvio la copia segna le chiavi del whisker `absent=true` (il file utente non esiste ancora); al ripristino, per ogni
  `show-command-*` assente chiama `xfconf_unset()` (scrive `x` con `-n` poi `-r`, `session.c:4975`) e per `plugin-1` assente decide con `panel_action_plugins()` (che guarda solo `actions`, non `whiskermenu`) e
  `xfce_system_value()`. **Non sono riuscito a stabilire con certezza quale ramo faccia sparire `plugin-1`**: lo si è solo visto (vedi §11, incognita 3). Ipotesi [S]: lo `unset` dei figli lascia il padre `plugin-1` come `empty`
  o lo cancella insieme; oppure il ripristino del padre viene saltato perché `any=FALSE` quando il canale è ancora vuoto.
- **Quanto è raggiungibile in 1.0.0**: la chiusura leggera si ha solo quando l'utente ha **già** una sessione locale (`local_light_close()`, `child.c:9921`). Dal 18 nov l'accesso locale passa per il gancio PAM che chiude **prima**
  il desktop remoto con la chiusura completa (che rimette a posto le chiavi): la strada è molto più stretta ma esiste ancora (gancio assente/scaduto, sessione locale arrivata per altra via, `DECISIONS-11 §11.57`).
  Resta raggiungibile anche lo slittamento del ripristino alla sessione successiva.
- **Cura nota**: no, mai scritta (nel vecchio albero compare solo come difformità D-X3, `O:assessment/xfce/difformita.md:33-60`, e come «ROSSO desktop-locale»). Idea [S]: non toccare mai il valore di un plugin il cui tipo viene dal
  `default.xml` (ripristinare solo ciò che l'utente aveva esplicitamente) e controllare dopo il ripristino che `plugin-ids` e i `plugin-N` corrispondano.

### 6.2 Residui nello scope dopo Log Out; sessione `closing` per sempre (D-X8, R-SESS-053) — **curato, con un buco**
- **Visto** (Xubuntu, `O:...ubuntu2604.md`): sessione `c144 closing` con `xiccd localsearch-3 ayatana-indicat agent` dentro. **Causa**: le voci di autostart tirate dai pacchetti GNOME/GTK (§3): `xiccd`
  (`NotShowIn=GNOME;KDE;` ⇒ parte su XFCE), `localsearch-3` (`OnlyShowIn=GNOME;KDE;XFCE;...`), `geoclue-demo-agent` («agent»; parte per `compat/LaunchGNOME=true` di Xubuntu, [V: `xfce4-session.xml` e `xfsm-startup.c:234`]),
  `ayatana-indicator-application`. Si staccano dal gestore di sessione (D-Bus, doppio fork), che chiude solo i propri client: restano nello scope di logind, che non si chiude.
- **Cura nel codice attuale** [V]: `session_clear_out_scope()` (`session.c:4390`, richiamato da `session_terminate()` e dal ramo del Log Out in `child.c:8686-8705`) manda SIGTERM, dopo 2 s SIGKILL, a ogni processo
  dell'utente rimasto nello scope, per **tutti** i desktop; nata il 6 ott 2026 proprio da un caso Ubuntu 26.04 XFCE («`localsearch-3` e `agent` (geoclue)», commento `session.c:4378`).
- **Buco noto, non curato** (`O:assessment/fase3-xfce-lxqt.md:51-58`, U6): `survivor()` (`session.c:4359`) giudica «dell'utente» un processo dall'uid del suo `/proc/<pid>/comm`; un processo **non-dumpable** (`ssh-agent`) ha
  quei file di proprietà di root → viene saltato. **Su Xubuntu 26.04 questo è plausibile**: `xfce4-session 4.20.4` avvia da sé `ssh-agent` e `gpg-agent` se `/startup/ssh-agent/enabled`/`gpg-agent` (default `TRUE`) e se
  non ci sono già [V: `xfsm-startup.c:248-262`]; li arresta solo se li ha avviati lui e se riesce a farlo (Log Out forzato = no). Seconda causa: la pulizia vale solo per lo **scope del figlio corrente** (`my_scope_pid()`),
  non per un desktop adottato da un figlio successivo.
  Conseguenza misurata sul vecchio banco: `FOUND AGAIN the desktop of «prova» … stage pid 2693 «ssh-agent»` dopo il riavvio del servizio. Il 1.0.0 ha poi aggiunto «nessun desktop orfano» (DECISIONS-11 §11.56), che attenua.
  Cura nota: no (solo diagnosi). Peso medio-piccolo: giudicare l'uid dal `Uid:` di `/proc/<pid>/status` invece che dal proprietario di `comm`.
- Su Lubuntu: «VERDE» nel vecchio banco (nessun residuo); l'autostart di Lubuntu è tutto di moduli `lxqt-session` che terminano con essa.

### 6.3 Sessione logind `active` invece di `closing` su Lubuntu (R-DE-089) — **non è un difetto, già curato a monte**
- Il vecchio banco: Debian `closing`, Ubuntu (e Fedora, Arch, Tumbleweed) `active`. **Causa Debian** (`O:assessment/RAPPORTO.md` F9): con systemd 257 la FIFO di sessione di `pam_systemd` (close-on-exec) chiusa dall'`execve` del figlio
  fa mettere subito la sessione in `closing`; i logind più nuovi seguono il leader (systemd 259.9 su Ubuntu 26.04 [V]). 
- **Nel codice attuale**: il 17 nov la sessione logind è tenuta viva con `--session-fd` (DECISIONS-11 §11.56/«The logind session is kept alive through `--session-fd`», `D:docs/DECISIONS-11.md:2055`); `D:docs/REGISTRO-problemi.md` §D la dichiara «attiva per tutta la vita». Su Ubuntu il comportamento «active» è quello voluto. Da riconfermare nel giro (§12).

### 6.4 Primo rientro respinto dopo logout (LXQt, R-SESS-049/057; D-X9/D10) — **curato su Debian, non misurato su Ubuntu**
- **Visto** (LXQt Debian, 3 volte; XFCE su tutte): un attach 4-6 s dopo «Esci» riceve `SESSION state=2` (RESUMED) e subito `FAREWELL 0x10`. **Causa** (`O:assessment/fase3-xfce-lxqt.md:62-64`, RAPPORTO U7): dopo il logout il figlio restava in attesa (R-SESS-050)
  e annunciava RESUMED per un desktop che rinasce.
- **Cura nel codice attuale** [V: `D:src/child.c:8696-8705`]: dal 17 nov «il logout termina il figlio su ogni desktop» (`raise(SIGTERM)`), il prossimo accesso è una sessione NUOVA. Più il guard «non montare finché il gestore di sessione non è sul bus» (`child.c:8792-8830`, 24 set).
  Non misurato su Ubuntu; la causa non dipende da Ubuntu ⇒ atteso uguale.

### 6.5 qlipper in sessione LXQt (R-DE-075) — **non è un difetto: decisione 16 nov «si lascia»**
- Su Lubuntu `qlipper 1:5.1.2-2ubuntu3` è Recommends di `lubuntu-desktop` e di `lxqt-session`, ed è nell'autostart sia di `/etc/xdg/autostart` che di `xdg-Lubuntu/autostart/lxqt-qlipper-autostart.desktop` (`X-LXQt-Need-Tray`). Parte nella sessione remota (`QxtGlobalShortcut failed to register: Ctrl+Alt+V`).
- La regola R-DE-075 nasceva dalla ricetta del banco, non da una promessa del prodotto (`O:assessment/RAPPORTO.md:209`). **Decisione approvata il 16 nov** (`O:assessment/DECISIONI.md:70-73`): si lascia; **requisito**: copia e incolla fra browser e desktop remoto
  devono funzionare con qlipper presente, da verificare con un browser vero (mai misurato: `O:assessment/fase3-xfce-lxqt.md:88`). Nel codice attuale: nessun filtro di qlipper.
- Rischio da misurare [S]: qlipper è Qt5; la sessione LXQt imposta `QT_QPA_PLATFORM=wayland` nudo (`session.c:2613`, commento «[?] To be looked at on the box: who dies this way (qlipper is Qt5)»): se manca il plugin Qt5 Wayland qlipper morirebbe — sul vecchio banco è invece partito (pid 2872).
  Se disturba gli appunti: nasconderlo con un `lxqt-qlipper-autostart.desktop` `Hidden=true` nella cartella `xdg-lxqt/autostart` (stessa tecnica delle voci pericolose, `session.c:6155-6290`), che batte sia `/etc/xdg/autostart` sia `xdg-Lubuntu`.

### 6.6 XFCE rifiuta il Log Out mentre si avvia — **vale anche su Ubuntu; già curato**
`xfce4-session 4.20.4` (versione di Ubuntu 26.04, [V: sorgente `xfce4-session-4.20.4/xfce4-session/xfsm-manager.c:2402-2454`]): `xfsm_manager_save_yourself_dbus()` ritorna `FALSE` se `manager->state != XFSM_MANAGER_IDLE`, e `Logout` risponde
«Session manager must be in idle state when requesting a shutdown». Lo stato passa a IDLE solo in `xfsm_manager_signal_startup_done()` (`:862-872`), mentre il nome `org.xfce.SessionManager` è preso molto prima (`main.c:291`).
⇒ Il test «nome sul bus» di `session_alive()` (`session.c:1015`) non basta a dire «pronto per il logout». Cura nel codice attuale: dopo il tempo concesso all'uscita ordinata `kill_xfce()` manda SIGTERM a labwc (registro D). Su Xubuntu l'avvio è **più lungo** (`LaunchGNOME=true`, molte voci di autostart, §3), quindi la finestra «non ancora a riposo» è più larga [S]: da misurare, non da correggere prima.
Altro fatto utile del sorgente: l'uscita «come labwc --session» richiede che `XFCE4_SESSION_COMPOSITOR` contenga `labwc` e `--session` (`main.c:262-270`): altrimenti `xfce4-session` eseguirebbe `loginctl terminate-session ''`
(la «cintura del logout», `session.c:2680`): la riga `labwc -m --session xfce4-session` la soddisfa [V].

---------------------------------------------------------------------------------------------------

## 7. Altri fatti di Xubuntu/Lubuntu rilevanti per il codice

### XFCE
- Sfondo nero (E1, `D:docs/REGISTRO-problemi.md:139`): la causa è `libxfce4windowing` < 4.20.4. Ubuntu 26.04 ha **4.20.5** [V]: dovrebbe sparire; `xfdesktop4 4.20.1` (come Debian). **Da verificare con una foto** (non misurabile con i log). Il `xfce4-desktop.xml` di Xubuntu non impone sfondi per schermo.
- `xfce4-power-manager`: Xubuntu mette `blank-on-ac=15`, `dpms-enabled=true`, `dpms-on-ac-sleep/off=20/60`; REMOTIX blocca `dpms-enabled=false` e `inactivity-on-ac/battery=0` (`session.c:6368-6370`, `XFCE_LOCKS`).
  Il vecchio banco ha provato solo 11 min di inattività (< 15): oltre non misurato (ma l'orologio REMOTIX è 30 min). `xfce4-screensaver` (Recommends, `OnlyShowIn=XFCE`) parte; il vecchio banco: nessun locker attivo.
- Whisker: `show-command-switchuser`→`dm-tool switch-to-greeter` (pericoloso sul server: sposta il monitor locale al greeter): già incluso fra le sei chiavi bloccate. Le chiavi hanno nome `show-command-*` anche in 2.10.1 [V: `settings.cpp:109-169`].
- Whisker 2.10.1: il pacchetto è solo Recommends di Xubuntu: senza Recommends il pannello Xubuntu perde il menu (e `default.xml` lo nomina comunque).
- `xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/` fornisce valori di sistema per `xfce4-session`, `xfwm4`, `xsettings`, `xfce4-power-manager`, `xfce4-keyboard-shortcuts`: la `xfce_system_value()` (`session.c:4902`) cerca lungo `XDG_CONFIG_DIRS`:
  senza D-153 non vede i default di Xubuntu e potrebbe scrivere nel file utente valori che sono già «di sistema» (e non toglierli al ripristino): effetto indiretto di D-153.
- `XDG_CURRENT_DESKTOP=XFCE` nudo coincide con ciò che dà lightdm (`DesktopNames=XFCE`): nessun cambio.
- Versioni: `labwc 0.9.3` su Ubuntu contro `0.8.3` su Debian. Il vecchio banco 1.5.5 ha provato XFCE su labwc 0.9.3 senza rilievi (R-DE-056 VERDE); il codice 1.0.0 non è stato provato con 0.9.3 dopo la pulizia: i punti sensibili alla versione sono la forma delle regole `<keybind>`/`rc.xml` (`SESSION_LABWC_*`, `session.h:298-311`) e i nomi dei cursori (`shape.c:131-137`, «labwc 0.8.3 porta due serie di nomi»). [S]

### LXQt
- `lxqt-session 2.3.0` (Debian: 2.1.x) [V: sorgente `lxqt-session-2.3.0`]: stesso nome sul bus `org.lxqt.session`, oggetto `/LXQtSession`, `Q_NOREPLY void logout()` (`sessiondbusadaptor.h:78`); il WM è avviato **solo se la piattaforma è xcb** (`lxqtmodman.cpp:81-83`):
  con `QT_QPA_PLATFORM=wayland` il `window_manager=openbox` di `xdg-Lubuntu/lxqt/session.conf` è ignorato; le voci `X-LXQt-X11-Only` (xscreensaver di Lubuntu) sono saltate su Wayland (`lxqtmodman.cpp:110`). `picom.desktop` di Lubuntu **non** ha `X-LXQt-X11-Only`: parte e fallirà senza X [S, innocuo, ma può apparire nel log].
- Il codice attuale cita come riferimento `lxqt-session 2.1.1`, `lxqt-panel 2.1.4`, `lxqt-wayland-session 0.1.1` (commenti `session.c:3749-3760, 6180-6190`, `session.h:~190`): su Ubuntu sono `2.3.0`, `2.3.2`, `0.3.1`. Da riguardare: `lxqt-leave`, il menu «fancymenu» (Lubuntu: `plugins=fancymenu,...` in `panel.conf`).
- `lxqt-wayland-session 0.3.1` esiste ma **Lubuntu non lo installa**: il lanciatore resta il nostro (`labwc -C ... -S lxqt-session`). Lo script upstream 0.3.1 usa ancora `exec $COMPOSITOR -C $XDG_CONFIG_HOME/labwc -S lxqt-session` per labwc e `XDG_CURRENT_DESKTOP="LXQt:$COMPOSITOR:wlroots"` [V: `startlxqtwayland:84,116`]: la nostra riga resta coerente.
- `session.conf` di Lubuntu: `leave_confirmation=true` (come Debian: `lxqt-leave --logout` attende conferma, R-DE-073 «da decidere»; REMOTIX non lo usa), `cursor_theme=breeze_cursors`, `[Environment] TERM=qterminal`, `BROWSER=firefox`,
  `GTK_CSD=0`, `SAL_USE_VCLPLUGIN=qt6`: li legge `lxqt-session` dalla cartella di sessione (D-153) e li mette nell'ambiente. `lxqt-powermanagement.conf` di Lubuntu: nessuna azione di inattività; REMOTIX non avvia comunque `lxqt-powermanagement` (`session.c:5565`).
- R-DE-079 (vecchio ROSSO «`kf6-breeze-icon-theme`/`breeze-icon-theme` non installati»): nasceva dal banco; Lubuntu usa `Papirus` (`lxqt.conf: icon_theme=Papirus`). Non è un problema Ubuntu [S].

---------------------------------------------------------------------------------------------------

## 8. Test box: avvertenze per le macchine di prova Ubuntu
- Un'immagine con `xubuntu-desktop` + Recommends contiene `gdm3`, `gnome-shell`, `gnome-session-bin`, `ubuntu-session`: serve **registrare lightdm come DM attivo** (`D:boxes/set-dm.sh lightdm`), altrimenti si prova GNOME (successe nel vecchio banco, primo giro).
- Lubuntu: registrare `sddm`; verificare con `box-identity.sh` che `/etc/X11/default-display-manager` e `display-manager.service` coincidano.
- Con `lightdm` attivo ricordare la dichiarazione file `60-xubuntu.conf`: è dentro `xubuntu-default-settings`, che `xubuntu-desktop` porta sempre.

---------------------------------------------------------------------------------------------------

## 9. Raccordo con il piano (`PIANO.md` passi 3b, 3c, 3f)
- **3b «riconoscere i quattro gusti»**: per XFCE/LXQt basta rimettere `xubuntu`/`lubuntu` in `desktop_of_session_name()` (piccolo) — ma attenzione che la *stessa* funzione serve a KDE (`plasma`, ok) e GNOME (`ubuntu`).
- **3c «cartelle come un accesso locale»**: rimettere D-153 (medio: tre funzioni + `local_session()`; le firme esistono ancora) e decidere i due punti nuovi (`XDG_SESSION_DESKTOP` sotto SDDM, variabili di `56xubuntu-session`).
- **3f «XFCE: pannello e programmi rimasti dopo l'uscita»**: i programmi rimasti sono già curati (6.2) salvo `survivor()`; il «pannello» è D-X3 (6.1, non curato).

---------------------------------------------------------------------------------------------------

## 10. Decisioni da chiedere al proprietario
1. Xubuntu/Lubuntu: ripristinare la mappa dei nomi come nel vecchio albero (proposta: sì, in blocco con quella di Ubuntu/Kubuntu).
2. D-153: ripristinare identico, con l'aggiunta che il nome di sessione è sempre quello esatto del file.
3. `XDG_SESSION_DESKTOP` su Lubuntu: `Lubuntu` (nome sessione, come il vecchio albero) o `LXQt` (come SDDM)?
4. D-X3 (whisker): correggere ora (con riproduzione sul banco) o accettare il rischio finché la chiusura leggera è quasi irraggiungibile?
5. Variabili di `56xubuntu-session` (`QT_QPA_PLATFORMTHEME=gtk2` ...): imitarle? (cambia l'aspetto delle app Qt su Xubuntu; conferma «remoto = locale»).
6. Pacchetto: `labwc`, `wlr-randr`, `xwayland` da `Recommends` a `Depends` per Xubuntu/Lubuntu? (Con `--no-install-recommends` XFCE/LXQt non nascono; scelta già presa per Debian: Recommends, `D:debian/control:82-101`.)

---------------------------------------------------------------------------------------------------

## 11. Che cosa non si può sapere senza provare
1. Quale DM resta attivo su un `apt install xubuntu-desktop` fatto sopra un Ubuntu con `gdm3` (debconf): deve essere misurato su una VM Ubuntu Desktop + `xubuntu-desktop`. Su una Xubuntu vera da ISO è lightdm [V per dipendenza].
2. Se lo sfondo nero E1 è sparito con `libxfce4windowing 4.20.5` (serve una foto della sessione).
3. **Quale istruzione di `xfce_restore_copy()` fa sparire `plugin-1` (whisker)** e se lo fa solo dopo chiusura leggera (§6.1). Solo riproduzione sul banco con un lightdm vero.
4. Se il whisker menu viene davvero trovato e bloccato quando D-153 è attivo (`default_plugins("whiskermenu")` legge `xdg-xubuntu/xfce4/panel/default.xml` solo se la cartella è in `XDG_CONFIG_DIRS` al momento giusto; il codice calcola l'elenco **prima** di avviare il pannello).
5. Il tempo che `xfce4-session` impiega per arrivare a IDLE su Xubuntu (con `LaunchGNOME=true`) e quindi quanto è larga la finestra del rifiuto del Log Out.
6. Che qlipper non disturbi il copia/incolla con un browser vero (decisione del 16 nov, mai misurata).
7. Che `picom` (X11-only, parte comunque) non lasci rumore o processi nello scope.
8. Che `labwc 0.9.3` + `wlr-randr 0.4.1` si comportino col codice 1.0.0 come con quello 1.5.5 (taglia del canvas, scorciatoie, cursore).
9. Che sddm 0.21.0 / lightdm 1.32.0 reali non reagiscano (greeter, VT) a una sessione remota con stesso utente: il gancio PAM di 1.0.0 (§11.57) lo regola, ma va provato **su live vere** (`PIANO.md` passo 5).
10. Se Lubuntu 26.04 su macchina reale parte davvero con la sessione X11 `Lubuntu` per default (i pacchetti dicono di sì; l'ISO può avere `sddm` con `state.conf` diverso) [S].

## 12. Prove consigliate
1. **Riconoscimento** (box Xubuntu con tutto + lightdm attivo): log «startup the desktop of this machine» deve dire XFCE + dichiarazione `xubuntu`; contro-prova con gdm3 attivo (GNOME, atteso) e con `--no-install-recommends` (XFCE senza dichiarazione).
2. **Ambiente della sessione** (Xubuntu, Lubuntu): leggere l'ambiente di `xfce4-session` / `lxqt-session` e confrontarlo con un accesso locale vero della stessa VM (stesso utente, solo variabili `XDG_*`, `DESKTOP_SESSION`, `QT_QPA_*`).
3. **Pannello Xubuntu**: utente nuovo, prima sessione remota (whisker presente, sei chiavi bloccate), Log Out; poi accesso locale: il pannello è quello di Xubuntu e **il menu c'è**. Ripetere con chiusura leggera e con riavvio del servizio durante la sessione.
4. **Scope e rientro**: Log Out, attendere, `loginctl list-sessions`/`systemd-cgls`: nessun residuo (compresi `ssh-agent`, `gpg-agent`, `xiccd`, `localsearch-3`, `agent`); primo rientro entro 4-6 s: sessione NUOVA, non RESUMED.
5. **Log Out presto** (XFCE): dopo la nascita, Log Out a 1-2 s: deve comparire l'avviso del rifiuto e la chiusura forzata, senza residui.
6. **qlipper + browser vero**: copia e incolla nei due versi con qlipper in esecuzione (Lubuntu).
7. **Idle > 15 min** su Xubuntu e Lubuntu: schermo ancora «acceso», nessun locker.
8. **Su live vere** (passo 5 del piano): accesso locale con lightdm e SDDM mentre il remoto è aperto (il gancio PAM, `A2`): XFCE e LXQt entrano al primo tentativo.

---------------------------------------------------------------------------------------------------

## 13. Problemi da affrontare

| # | Che cosa | Dove nel codice | Peso | Cura già nota nel vecchio albero? |
|---|---|---|---|---|
| 1 | Riconoscimento Xubuntu: `desktop_of_session_name()` senza `xubuntu`/`lubuntu` ⇒ con lightdm che dichiara `xubuntu` vince GNOME | `D:src/session.c:382-393` (consumatori 440-500, 533-560) | piccolo | **sì**: `O:src/session.c:381-393` (stesso corpo, ordine «ubuntu» per ultimo) |
| 2 | Ripristinare D-153: nome di sessione e cartelle `xdg-xubuntu`/`xdg-Lubuntu` + `/usr/share/xubuntu`/`Lubuntu` | `D:src/session.c:2270-2290`, chiamanti 2377-2440, 2593, 5124 | medio | **sì**: `O:src/session.c:2274-2380` (3 funzioni + `local_session()`), provato su Ubuntu 26.04 (`O:assessment/*/ubuntu2604.md`) |
| 3 | `XDG_SESSION_DESKTOP` su Lubuntu: SDDM dà `LXQt`, il vecchio codice dava `Lubuntu` | `add_session_names()` `D:src/session.c:2416`, ramo LXQt 2572 | piccolo | no (decisione nuova, §10.3) |
| 4 | Variabili di `56xubuntu-session` (`QT_QPA_PLATFORMTHEME=gtk2`, `GTK_OVERLAY_SCROLLING=0`, `CLUTTER_BACKEND=x11`) non imitate | ramo XFCE `D:src/session.c:2526-2540` | piccolo | no |
| 5 | Whisker perso dal pannello (D-X3): ripristino sbagliato dopo chiusura leggera / ripristino slittato; su Xubuntu è l'unica protezione delle voci di spegnimento | `D:src/session.c:5348-5420` (`xfce_restore_copy`), `6432-6500` (`xfce_panel_xml`), `4975` (`xfconf_unset`) | medio-grande (causa non chiarita) | **no**: funzione identica nei due alberi; D-X3 solo descritta (`O:assessment/xfce/difformita.md:33-60`) |
| 6 | `survivor()` salta i processi non-dumpable (`ssh-agent`, `gpg-agent`); pulizia solo dello scope del figlio corrente ⇒ sessione `closing` e «FOUND AGAIN» | `D:src/session.c:4359-4420` | piccolo-medio | diagnosi sì (`O:assessment/fase3-xfce-lxqt.md:51-58`, U6); correzione no |
| 7 | `labwc`/`wlr-randr`/`xwayland` non portati da Xubuntu/Lubuntu: con `--no-install-recommends` XFCE/LXQt non nascono | `D:debian/control:97-101` | piccolo | `O:packaging/` (non ripreso qui) |
| 8 | Riferimenti di versione dei commenti/ipotesi: lxqt-session 2.3.0, lxqt-panel 2.3.2, labwc 0.9.3, xfce4-session 4.20.4: ricontrollare i punti che citano 2.1.x e labwc 0.8.3 | `D:src/session.c:3749-3760, 6180-6190`, `D:src/shape.c:131-137`, `D:src/session.h:298-311` | piccolo (verifica) | no |
| 9 | Log Out XFCE rifiutato mentre parte: la finestra è più larga su Xubuntu (LaunchGNOME) | `D:src/session.c:3685-3735` (`exit_xfce`, `kill_xfce`) | piccolo (già curato, solo da misurare) | sì: forzatura già nel codice (registro D) |
| 10 | Test box: Xubuntu con DM sbagliato (gdm3) prova GNOME; serve `set-dm.sh lightdm`/`sddm` e `box-identity.sh` | `D:boxes/set-dm.sh`, `D:boxes/box-identity.sh` | piccolo | sì: `O:assessment/xfce/ubuntu2604.md:6-17` |
| 11 | qlipper (Lubuntu): decisione «si lascia», requisito da misurare con browser vero | nessun codice | piccolo (misura) | decisione sì (`O:assessment/DECISIONI.md:70-73`) |
| 12 | `picom` di Lubuntu parte senza X (rumore nel log) | nessun codice | piccolo (osservazione) | no |
| 13 | Sfondo nero XFCE (E1): atteso risolto con `libxfce4windowing 4.20.5`, da verificare con una foto | nessun codice | piccolo | n/a (`D:docs/REGISTRO-problemi.md:139`) |
| 14 | Chiusura leggera ancora presente accanto al gancio PAM: percorso residuo che non ripristina le chiavi XFCE (collega 5) | `D:src/child.c:9921`, `session.c:4025-4040` | medio (decisione) | no |

---------------------------------------------------------------------------------------------------

## 14. Appendice: comandi e file letti
- Contenitore: `podman run -d --name studio-7 -v /media/REMOTIX-UBUNTU/studio/7:/w docker.io/library/ubuntu:26.04` (Ubuntu 26.04.1 LTS, indice apt del 18 nov); `deb-src` abilitato; `apt-file update` eseguito.
- File estratti con `apt-get download` + `dpkg-deb -x`: xubuntu-default-settings, lightdm, lubuntu-default-settings, sddm, xfce4-session, xfce4-panel, xfce4-whiskermenu-plugin, lxqt-session, lxqt-wayland-session, x11-common, gnome-session-bin, labwc,
  qlipper, lxqt-panel, picom, xiccd, localsearch, xfce4-screensaver, xubuntu-desktop, lubuntu-desktop, lxqt-core, ... Sorgenti: lightdm 1.32.0, sddm 0.21.0+git20250502, xfce4-session 4.20.4, lxqt-session 2.3.0, lxqt-wayland-session 0.3.1, xfce4-whiskermenu-plugin.
- Simulazioni di installazione: `/media/REMOTIX-UBUNTU/studio/7/sim-*.txt`, `simrec-*.txt` (con Recommends), elenco autostart `autostart-xubuntu-desktop.txt`, `autostart-lubuntu-desktop.txt`.
- Il contenitore `studio-7` viene fermato e tolto a fine studio; la cartella resta.
