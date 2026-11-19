# Studio 3 — La sessione «ubuntu» di Ubuntu 26.04 e l'emulazione dell'accesso locale

Agente di studio 3, 18 nov 2026. Solo studio: nessun file del prodotto toccato, nessuna prova del prodotto.
Legenda: **[V]** verificato (dove), **[W]** dal web, **[S]** supposizione.
Fatti veri raccolti nel contenitore `studio-3` (ubuntu:26.04 = «26.04.1 LTS Resolute Raccoon», archivi `resolute` e `resolute-updates`);
pacchetti scaricati con `apt-get download`, estratti con `dpkg-deb -x`, sorgenti con `apt-get source`. File di lavoro in
`/media/REMOTIX-UBUNTU/studio/3/` (`debs/`, `x/`, `src/`, script `s3*.sh`).

Versioni Ubuntu 26.04 che contano (tutte [V] da `apt-cache policy`/nomi dei `.deb`):
`gnome-session` / `gnome-session-bin` / `gnome-session-common` / `ubuntu-session` **50.1-0ubuntu0.1** (updates; 50.0-0ubuntu3 in release),
`gnome-shell` 50.1-0ubuntu1.5, `gdm3` 50.1-0ubuntu0.1, `ubuntu-settings` 26.04.6, `ubuntu-desktop(-minimal)` 1.570.4,
`gnome-shell-ubuntu-extensions` 50.26.04.8ubuntu, `yaru-theme-*` 26.04.5.1ubuntu, `x11-common` 1:7.7+26ubuntu1, `glib2.0` 2.88.0-1ubuntu0.1,
`dconf` 0.49.0-4, `gsettings-desktop-schemas` 50.0-1ubuntu2, `snapd` (environment.d), `im-config`.

---

## 1. Quali sessioni esistono e che cosa contengono

### 1.1 Pacchetti e file [V]
- `gnome-session-bin` (main): `/usr/bin/gnome-session` (ELF, non più script), `/usr/libexec/gnome-session-{ctl,init-worker,service}`.
- `gnome-session-common` (main): unità systemd utente (`gnome-session-manager@.service`, `gnome-session@.target`, `gnome-session.target`, …),
  `/etc/X11/Xsession.d/55gnome-session_gnomerc`, **`/etc/profile.d/gnome-session_gnomerc.sh`**, **`/etc/profile.d/xdg_dirs_desktop_session.sh`**,
  `/usr/share/applications/{gnome,ubuntu}-mimeapps.list`, `/usr/share/xdg-desktop-portal/gnome-portals.conf`.
- **`ubuntu-session`** (main, **Depends: gnome-session-bin, gnome-session-common, gnome-settings-daemon, gnome-shell,
  gnome-shell-ubuntu-extensions, xdg-desktop-portal-gnome, xwayland, yaru-theme-gnome-shell, user-session-migration**): 
  `/usr/share/wayland-sessions/ubuntu.desktop`, `/usr/share/gnome-session/sessions/ubuntu.session`,
  `/usr/lib/systemd/user/gnome-session@ubuntu.target.d/ubuntu.session.conf`, `/usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf`
  (`[Seat:*] user-session=ubuntu`), uno script di migrazione impostazioni.
- **`gnome-session`** (il pacchetto «gnome» puro, **universe**): `/usr/share/wayland-sessions/gnome.desktop`,
  `/usr/share/gnome-session/sessions/gnome.session`, `gnome-session@gnome.target.d/gnome.session.conf`.
  `ubuntu-desktop`/`ubuntu-desktop-minimal` **non** lo richiedono (Depends: `ubuntu-session`); `gnome-shell` ha «Recommends: ubuntu-session | gnome-session»
  (alternativa, non entrambi) [V `apt-cache depends`]. Lo porta `vanilla-gnome-desktop` (rdepends [V]).
- **Non esiste alcun `/usr/share/xsessions/*.desktop`** nei pacchetti della sessione: in 26.04 (GNOME 50) niente sessione X11 [V: elenco file dei `.deb`].
  Le sole sessioni sono dunque Wayland: `ubuntu.desktop` e (se installato `gnome-session`) `gnome.desktop`.
  Niente `gnome-wayland.desktop`, niente `ubuntu-xorg`, niente `gnome-classic` in questi pacchetti.

### 1.2 Contenuto dei `.desktop` e dei `.session` [V]
```
ubuntu.desktop: Exec=/usr/bin/gnome-session --session=ubuntu   TryExec=/usr/bin/gnome-session
                DesktopNames=ubuntu;GNOME   X-GDM-SessionRegisters=true   X-GDM-CanRunHeadless=true
gnome.desktop:  Exec=/usr/bin/gnome-session --session=gnome    TryExec=/usr/bin/gnome-session
                DesktopNames=GNOME          X-GDM-SessionRegisters=true   X-GDM-CanRunHeadless=true
ubuntu.session: [GNOME Session] Name=Ubuntu            gnome.session: Name=GNOME (con molte traduzioni)
```
(`Exec=… --session=gnome` è una patch Ubuntu: `gnome-session-50.1/debian/patches/ubuntu/ubuntu-sessions.patch`.) I `.session` di GNOME 50 non hanno più
`RequiredComponents`: contengono solo il nome; i componenti sono unità systemd. Le altre due sessioni `gnome-login.session` e
`gnome-initial-setup.session` sono `Kiosk=true` (greeter e prima configurazione, non sono sessioni utente).

### 1.3 Come la modalità `ubuntu` arriva alla Shell [V]
- `gnome-session@ubuntu.target.d/ubuntu.session.conf`: `Requires=gnome-session-services.target` + **`Requires=org.gnome.Shell@ubuntu.service`**.
  Quello di `gnome`: `Requires=org.gnome.Shell@user.service`.
- `org.gnome.Shell@.service` (gnome-shell-common/gnome-shell) è un **modello**: `ExecStart=/usr/bin/gnome-shell --mode=%i`,
  `AssertEnvironment=XDG_SESSION_TYPE=wayland`, `Type=notify`, `Slice=session.slice`, `Restart=no`. L'istanza = la modalità: `@ubuntu` → `--mode=ubuntu`, `@user` → `--mode=user`.
- `gnome-session-manager@<nome>.service` (da `gnome-session-common`): `ExecStart=/usr/libexec/gnome-session-service --session=%i`; `<nome>` è il valore di `--session`.
- `/usr/share/gnome-shell/modes/ubuntu.json` [V]: `parentMode: user`, `stylesheetName: Yaru/gnome-shell.css`, `colorScheme: prefer-light`,
  `themeResourceName`/`iconsResourceName` Yaru, `enabledExtensions`: `ubuntu-dock@ubuntu.com`, `ubuntu-appindicators@ubuntu.com`, `ding@rastersoft.com`,
  `tiling-assistant@ubuntu.com`, `snapd-prompting@canonical.com`, `snapd-search-provider@canonical.com`, `web-search-provider@ubuntu.com`.
  Esiste anche `initial-setup.json`. Le estensioni (pacchetto `gnome-shell-ubuntu-extensions`, che **Provides** `gnome-shell-extension-{appindicator,desktop-icons-ng,ubuntu-dock,ubuntu-tiling-assistant}`; i nomi separati citati nel compito non esistono più come pacchetti in 26.04 [V `apt-cache`]) vivono in `/usr/share/gnome-shell/extensions/<uuid>/`.
- `GNOME_SHELL_SESSION_MODE`: gnome-shell (`src/main.c:702`, [V sorgente 50.1]) la legge come **valore iniziale**, poi `--mode=` la **sovrascrive** (opzione parsata dopo, `main.c:604`); se vale NULL, `gdm`/`user`.
  `gnome-session` (`gsm-util.c:61-68`) la mette nella lista delle variabili che **vengono tolte** dagli ambienti dei servizi se non sono nell'ambiente di gnome-session (protezione dai residui di sessioni precedenti). 
  Quindi: **la modalità arriva dal nome dell'istanza dell'unità**, scelta da `--session=<nome>` → `gnome-session@<nome>.target` → `Requires=org.gnome.Shell@<modo>.service`. La variabile ambiente non è il canale.
  Conseguenza per REMOTIX: se il drop-in sostituisce `ExecStart` della Shell, deve mantenere `--mode=%i` (vedi problema 3).

---

## 2. Variabili d'ambiente e chi le imposta in un accesso Wayland da GDM

### 2.1 La catena vera (tutta [V] da sorgenti 50.1, salvo dove indicato)
1. **PAM / GDM session worker** (`gdm3-50.1/daemon/gdm-session-worker.c`): imposta nell'ambiente PAM `LOGNAME USER USERNAME HOME PWD SHELL` (shell dalla riga passwd, `:1452-1463`), `PATH` se manca, `XDG_SEAT`, `XDG_SESSION_CLASS`, `XDG_SESSION_EXTRA_DEVICE_ACCESS=render:accel`, `XDG_VTNR`, `XDG_SESSION_ID`.
2. **GDM** (`daemon/gdm-session.c:2838-2872`, `set_up_session_environment`): `GDMSESSION`, **`DESKTOP_SESSION`**, **`XDG_SESSION_DESKTOP`** = nome della sessione (il nome del file `.desktop` senza estensione, es. `ubuntu`), e **`XDG_CURRENT_DESKTOP`** = `DesktopNames` unito con `:` → **`ubuntu:GNOME`** (il `;` del file diventa `:`).
   La lingua non è più impostata da GDM (patch Ubuntu `dont_set_language_env`; `~/.pam_environment`/AccountsService altrove).
3. **`gdm-wayland-session`** (`daemon/gdm-wayland-session.c:~300-360`): **NON passa da `/etc/gdm3/Xsession`** e quindi non esegue `Xsession.d`. Avvia direttamente il comando della sessione; l'ambiente è quello GDM + quello **importato dal `systemd --user`** (`PATH` solo come ripiego; le variabili impostate da GDM hanno la precedenza).
   Quel `systemd --user` ha l'ambiente dei **generator**: `30-systemd-environment-d-generator` (legge `/usr/lib/environment.d/*.conf`, `/etc/environment.d`) e `60-flatpak`. Es. `snapd` (`/usr/lib/environment.d/990-snapd.conf`): `PATH=$PATH:/snap/bin` e `XDG_DATA_DIRS=${XDG_DATA_DIRS:-/usr/local/share/:/usr/share/}:/var/lib/snapd/desktop` [V].
4. **`gnome-session` (leader, `gnome-session/leader-main.c:~65-110`)** — **PASSAGGIO CHIAVE**: se `XDG_SESSION_TYPE=wayland`, la classe non è `greeter` e `$SHELL` è una shell valida (in `/etc/shells`, non `nologin`), il leader **si rilancia dentro una login shell**: `execv($SHELL, ["-bash","-c","exec gnome-session --no-reexec --session=ubuntu"])`.
   La login shell legge **`/etc/profile` → `/etc/profile.d/*.sh`** e poi `~/.profile`/`~/.bash_profile`. È da qui che, in un accesso Wayland, arrivano:
   - `gnome-session_gnomerc.sh` (gnome-session-common): sorgente `~/.gnomerc` (solo se `XDG_CURRENT_DESKTOP` contiene `GNOME`) e **`/usr/share/gnome` davanti a `XDG_DATA_DIRS`**;
   - **`xdg_dirs_desktop_session.sh`** (gnome-session-common): se `DESKTOP_SESSION` non è vuoto → **`/etc/xdg/xdg-$DESKTOP_SESSION` davanti a `XDG_CONFIG_DIRS`** (anche se la cartella non esiste: lo script non lo controlla) e, se `DESKTOP_SESSION != gnome`, **`/usr/share/$DESKTOP_SESSION` davanti a `XDG_DATA_DIRS`** → su Ubuntu **`/usr/share/ubuntu`**. È la stessa logica di `Xsession.d/60x11-common_xdg_path`, ma in forma `profile.d`;
   - `snapd`: `apps-bin-path.sh` (PATH `/snap/bin`, `/var/lib/snapd/desktop` in `XDG_DATA_DIRS`); `base-files`: `01-locale-fix.sh`; `language-selector-common`: `cedilla-portuguese.sh` (LC_CTYPE per portoghese); `im-config`: `im-config_wayland.sh` (variabili input method); `libvte-2.91-common`: `vte-2.91.sh`;
   - tutto ciò che l'utente mette in `~/.profile` (variabili personali).
   Poi il leader (`set_up_environment`): `GNOME_DESKTOP_SESSION_ID=this-is-deprecated`, **`XDG_MENU_PREFIX=gnome-`**, `QT_IM_MODULE(S)`/`XMODIFIERS` se c'è ibus, e carica l'ambiente nel `systemd --user` e in D-Bus (`UpdateActivationEnvironment`) tramite `gnome-session-init-worker`.
   `gnome-session-init-worker` usa `GNOME_SHELL_SESSION_MODE`, `GNOME_SETUP_DISPLAY`, `XDG_SEAT/SESSION_ID/VTNR` (stringhe del binario [V]).
5. `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`: da logind/PAM/GDM.

### 2.2 Valori attesi in una sessione locale Ubuntu 26.04 con GDM (ricostruiti)
| Variabile | Valore | Chi |
|---|---|---|
| `XDG_CURRENT_DESKTOP` | `ubuntu:GNOME` | GDM da `DesktopNames` [V] |
| `XDG_SESSION_DESKTOP`, `DESKTOP_SESSION`, `GDMSESSION` | `ubuntu` | GDM [V] |
| `GNOME_SHELL_SESSION_MODE` | non impostata (la Shell prende `--mode=ubuntu` dall'istanza) | [V] |
| `XDG_CONFIG_DIRS` | `/etc/xdg/xdg-ubuntu:/etc/xdg` (cartella `xdg-ubuntu` **inesistente** in 26.04: `apt-file search` vuoto) | `profile.d/xdg_dirs_desktop_session.sh` [V] |
| `XDG_DATA_DIRS` | `/usr/share/ubuntu:/usr/share/gnome:/usr/local/share/:/usr/share/:/var/lib/snapd/desktop` (ordine esatto **[S]**: i due `profile.d` girano in ordine alfabetico, `gnome-session_gnomerc.sh` prima, poi `xdg_dirs_…`; il resto dal manager) | profile.d + environment.d [V per gli elementi, S per l'ordine] |
| `XDG_MENU_PREFIX` | `gnome-` | leader di gnome-session [V] |
| `SHELL` | shell dell'utente (es. `/bin/bash`) | GDM da passwd [V] |

`/usr/share/ubuntu/` appartiene a `ubuntu-settings` 26.04.6 e contiene solo tre `.desktop` che **nascondono** voci (`gnome-initial-setup.desktop` con `NoDisplay=true` e `X-GNOME-HiddenUnderSystemd=true`, `info.desktop`, `texdoctk.desktop`) [V].
Nessun pacchetto in 26.04 ha `/etc/xdg/xdg-ubuntu` né `/usr/share/gdm/env.d` [V `apt-file`]. `gdm/env.d` è letto solo per il greeter/initial-setup (`gdm-launch-environment.c:346`).

### 2.3 Lo script `/etc/X11/Xsession.d/60x11-common_xdg_path` esiste ancora in 26.04? **Sì** [V]
Pacchetto `x11-common` 1:7.7+26ubuntu1, testo identico nella logica a quello di `profile.d` (con `DESKTOP_SESSION` → `xdg-<s>` davanti a `XDG_CONFIG_DIRS`; dati non per `gnome`). Ma:
- Su **GDM + Wayland** (la sola cosa che offre l'Ubuntu GNOME 26.04) **non gira mai** (punto 3 sopra); gira solo per sessioni X11 e per lightdm/sddm che usano `Xsession`.
- Ciò che, su Ubuntu GNOME 26.04, produce davvero `/usr/share/ubuntu` è lo **script `profile.d`** di `gnome-session-common` via il rilancio in login shell del leader.
- **La premessa con cui il codice D-153 era stato scritto e poi tolto era quindi incompleta**: tolto perché su Debian `x11-common` non ha il file (`docs/PULIZIA-tranche1.md` voce 7), ma su Ubuntu GNOME il meccanismo operante è un altro (profile.d) e **su Debian 13 `gnome-session-common` potrebbe avere o no lo stesso snippet [S, non controllato]**: sul tablet non ho scaricato i pacchetti Debian; il commento di `local_session()` in REMOTIX-DEBIAN (`session.c:2268`) dice «`x11-common` non lo ha» ma non parla di `profile.d`.

Differenza con REMOTIX (che imposta `SHELL=` **vuoto** apposta, `session.c:2733-2741`, per non far rilanciare gnome-session in login shell): **la sessione remota non esegue `/etc/profile`, `profile.d`, `~/.profile`**. Quindi tutto ciò che nella tabella viene dai `profile.d`/`~/.profile` va **emulato da REMOTIX** o è perso. (Per `PATH`/snap/flatpak ci pensa già `manager_value()` che prende le liste dal manager utente.)

---

## 3. Il vecchio albero: D8 e D-153

### 3.1 D8 — sessione GNOME da usare
Fonti: `REMOTIX/DECISIONS.md:6086-6097` (§10.20, parole dell'utente 30 set 2026: «l'utente vede il desktop originale di Ubuntu (o altrimenti saremo costretti a implementare un nostro session manager)»); `REMOTIX/src/session.c:745-935` (`gnome_session()`); `REMOTIX/phases/17-the-installer.md:1466` (commit 7583b76, con misure).
Criterio (una regola per tutti, nessuna distro nominata):
1. candidati = `<XDG data>/wayland-sessions/*.desktop` il cui `Exec` lancia `gnome-session` (nome dall'argomento `--session`, senza = `gnome`) **e** esiste `<data>/gnome-session/sessions/<nome>.session`;
2. uno solo → quello (Ubuntu stock: `ubuntu`);
3. più d'uno → **quello col nome uguale a `ID` di os-release** (`g_get_os_info(G_OS_INFO_KEY_ID)`, `session.c:871`) → altrimenti `gnome` → altrimenti il primo in ordine alfabetico (regola GDM upstream; la regola 3 «dà lo stesso risultato della patch Ubuntu `prefer_ubuntu_session_fallback` senza nominare Ubuntu»);
4. nessun candidato → ripiego dichiarato `gnome` (a log).
Valori: avvio = `Exec` argomento per argomento (quotato); `XDG_CURRENT_DESKTOP` da `DesktopNames`; `XDG_SESSION_DESKTOP` dal nome del file; manager `gnome-session-manager@<nome>.service`.
Per GNOME 50: l'istanza della Shell è chiesta per **sessione** (`Requires` di `gnome-session@<sessione>.target`: `@user`/`@ubuntu`), il drop-in mantiene `--mode=%i`, il clear-out cerca ogni `org.gnome.Shell@*.service.d` (mai quello del modello). Misure del 30 set (phases/17): su Ubuntu 26.04 senza `gnome-session` il log diceva «D8: «ubuntu» (ubuntu.desktop): l'unica…· XDG_CURRENT_DESKTOP=ubuntu:GNOME», processo `gnome-shell --headless --no-x11 --mode=ubuntu`, schermata: dock a sinistra, sfondo 26.04, cartella Home arancione (ding).

### 3.2 D-153 — emulare l'ambiente di un accesso locale
Fonti: `REMOTIX/DECISIONS.md:7205-7248` (§10.54, decisione dell'utente 14 nov: «la sessione REMOTIX si comporta come un normale accesso locale, tranne ciò che danneggia gli altri utenti di un server condiviso; **nessuna distribuzione nominata nella logica**»), `REMOTIX/src/session.c:2240-2370`.
Meccanismo: `local_session()` ricavava nome, cartella config e cartella dati:
- nome: GNOME → `gnome_session()->id`; altrimenti la sessione dichiarata dal display manager (`declared_sessions()`: lightdm `user-session`, sddm `[Autologin] Session`) se nomina il desktop scelto; altrimenti il primo file in `xsessions`/`wayland-sessions` del desktop che abbia una cartella propria (`session_folder_there()`, ordine alfabetico `by_name()`), tramite `local_session_name_find()`;
- `xsession_d_applies()`: il meccanismo si applicava solo se esisteva `/etc/X11/Xsession.d/60x11-common_xdg_path` **e** il login locale di quella sessione esegue `Xsession.d` (file in `xsessions/` oppure display manager diverso da sddm; verificato in `/etc/gdm3/Xsession`; `sddm/scripts/wayland-session` solo legge il profilo → niente per Plasma Wayland);
- se applicabile: `config=/etc/xdg/xdg-<nome>` e `data=/usr/share/<nome>` **solo se esistono** (mai per `gnome` sui dati), poi `DESKTOP_SESSION=<nome>`, `XDG_SESSION_DESKTOP`, e la lista davanti a `XDG_CONFIG_DIRS`/`XDG_DATA_DIRS`, **dietro** alle cartelle proprie di REMOTIX.
Base delle liste (revisione 14 nov): il valore del **manager utente** (`manager_value()`, filtra elementi non assoluti/pericolosi e quelli con `/remotix/`) → poi quello del processo → default. Così Firefox snap, App Center, flatpak restano nei menu.
Misura citata (§10.54): Xubuntu 26.04, `XDG_CONFIG_DIRS=/etc/xdg/xdg-xubuntu:/etc/xdg`; «Ubuntu GNOME ha `/usr/share/ubuntu` (voci nascoste, es. l'assistente di prima configurazione) e non ha `/etc/xdg/xdg-ubuntu`: stesso vuoto sul lato dati» — **questa riga su Ubuntu GNOME era dedotta dal meccanismo, non misurata** [S: non ho trovato in `REMOTIX/` alcuna misura di XDG_DATA_DIRS su Ubuntu GNOME; `grep usr/share/ubuntu` trova solo quella frase].

### 3.3 Che cosa è rimasto in `REMOTIX-DEBIAN/src/session.c`
- `desktop_of_session_name()` (`:382`): solo `xfce`, `lxqt`, `plasma|kde`, `gnome`. Mancano `xubuntu`, `lubuntu`, `kubuntu` e **`ubuntu`** (tolti, voce 4 della pulizia). Effetto su Ubuntu: `declared_desktop()` non classifica un `user-session=ubuntu` (che `ubuntu-session` installa in `lightdm.conf.d/50-ubuntu.conf`). Con GDM attivo è irrilevante (`declared_sessions()` torna FALSE per DM diverso da lightdm/sddm), rilevante per Xubuntu/Lubuntu (agente 7).
- `gnome_session()` (`:859-951`): conserva i punti 1, 2, 4, **ma il punto 3 è ridotto a «`gnome`, poi il primo alfabetico»** (la corrispondenza con os-release è stata tolta, voce 5). **Regressione su Ubuntu quando sono installate entrambe `gnome` e `ubuntu`**: sceglierebbe `gnome` (Adwaita, modalità `user`, niente dock) mentre GDM sceglie `ubuntu` (patch `prefer_ubuntu_session_fallback`, ordine: **sessione salvata dell'utente → `ubuntu` → `gnome` → primo alfabetico**, `gdm-session.c:get_default_session_name/get_fallback_session_name`). Con solo `ubuntu` installato (stock) funziona (punto 2).
- `local_session()` (`:2270`): corpo svuotato, restituisce sempre una struct vuota (name/config/data NULL) e scrive la stessa riga di log. Di conseguenza, per GNOME: **`DESKTOP_SESSION` non viene mai impostata**, `XDG_CONFIG_DIRS`/`XDG_DATA_DIRS` ricevono solo il valore del manager (`add_session_names`, `session_config_dirs`, `session_data_dirs`: rimasti e già pronti a ricevere i dati). `XDG_CURRENT_DESKTOP` e `XDG_SESSION_DESKTOP` per GNOME restano giusti (`session.c:2712-2714`, da `gnome_session()`: `ubuntu:GNOME`, `ubuntu`).
- `unit_shell()` (`:2860-2882`): conosce solo `org.gnome.Shell@wayland.service` (GNOME ≤ 49); su Ubuntu 26.04 **tornerà NULL** («I do not recognise the Shell unit») → `write_dropin()` fallisce → nessuna sessione (voce 6 della pulizia: il ramo modello GNOME 50 è stato tolto). Il punto di confine con l'agente 1, ma dipende da D8.
- `has_candidate()` (`:818-857`), `name_from_exec()`, `c_e_il_file_session()`: restano giusti per i file 26.04 (provato a mano sul testo: `Exec=/usr/bin/gnome-session --session=ubuntu`, `TryExec` trovato in PATH, `.session` esiste, `DesktopNames=ubuntu;GNOME` → `ubuntu:GNOME` con `g_strjoinv(":")`). Nota: se un `Exec` non avesse `--session`, il codice assume `gnome`, mentre il default reale di gnome-session è la chiave gsettings `org.gnome.desktop.session session-name`, che su Ubuntu è sovrascritta a `"ubuntu"` (`ubuntu-settings` 10_ubuntu-settings.gschema.override) — in 26.04 i due `.desktop` hanno sempre `--session=`, quindi il caso non si presenta [V].
- `recognize_desktop()`: ancora corretto per Ubuntu GNOME (richiede `gnome-session` **e** `gnome-shell` nel PATH; `gnome-session-bin` fornisce `/usr/bin/gnome-session`).
- Pulizia a fine sessione: già gestisce ogni `org.gnome.Shell@*.service.d` (`session.c:3989-4010`) e `OUR_VARIABLES` include `DESKTOP_SESSION` (`:3844`) — OK per Ubuntu.

---

## 4. Impostazioni predefinite di Ubuntu, Yaru, dock: arrivano da sole?

### 4.1 Meccanismo [V]
- Le impostazioni Ubuntu sono **override di gschema**, non dconf di sistema: `ubuntu-settings` ha `/usr/share/glib-2.0/schemas/10_ubuntu-settings.gschema.override` (gruppi `[org.gnome.shell:ubuntu]`, `[org.gnome.desktop.interface:ubuntu]` con `gtk-theme=Yaru`, `icon-theme=Yaru`, `cursor-theme=Yaru`, font `Ubuntu Sans`, `[org.gnome.mutter:ubuntu]`, `[org.gnome.desktop.wm.preferences:ubuntu]` con `button-layout=':minimize,maximize,close'`, `favorite-apps`, `[org.gnome.shell.extensions.ding:ubuntu]`, …; globale `[org.gnome.desktop.session] session-name="ubuntu"`) e `gnome-shell-ubuntu-extensions` ha `10_ubuntu-dock.gschema.override` (`[org.gnome.shell.extensions.dash-to-dock:ubuntu]`: `dock-position='LEFT'`, `dock-fixed=true`, `extend-height=true`, …). Il commento del file dice: «Mirror G-S default experience … as we are using a G-S mode, the default overrides aren't used».
- **Il suffisso `:ubuntu` è un override «per desktop» di GLib**, valutato **in ogni processo GSettings** contro **`XDG_CURRENT_DESKTOP`** separato da `:` (`glib2.0-2.88.0/gio/gsettingsschema.c:1491-1510`; compilazione in `glib-compile-schemas.c:1926-2135`). Quindi **tutte le impostazioni Ubuntu dipendono da `XDG_CURRENT_DESKTOP` contenente `ubuntu`** nell'ambiente di ogni app (non dalle cartelle). Con `XDG_CURRENT_DESKTOP=GNOME` (sessione `gnome`) l'aspetto è Adwaita.
- **Nessun dconf di sistema né profilo `user`** in Ubuntu stock: `apt-file search` non trova `etc/dconf/db` né `dconf/profile/user` (solo `ibus`, e `gdm` di edubuntu); `ubuntu-settings` non ha `etc/dconf`. Quindi `dconf_base_profile()` di REMOTIX troverà NULL e userà `user-db:user` [V per l'assenza, il codice di ricerca è lo stesso in dconf 0.49: `engine/dconf-engine-profile.c:32-63,196,291-299`].
- Yaru shell (CSS, risorse) viene da `ubuntu.json` (modalità), Yaru GTK/icone dal gschema `:ubuntu`; entrambi richiedono, rispettivamente, `--mode=ubuntu` e `XDG_CURRENT_DESKTOP=ubuntu:GNOME`.
- Altri file legati a `XDG_CURRENT_DESKTOP`: `/usr/share/applications/ubuntu-mimeapps.list` e `gnome-mimeapps.list` (nome `<desktop>-mimeapps.list` per specifica XDG [S sul dettaglio d'uso]), `xdg-desktop-portal/gnome-portals.conf` (il portale cerca `<desktop>-portals.conf` per ciascun elemento; `ubuntu-portals.conf` non c'è, cade su `gnome`) [S sul meccanismo del portale].
- `user-session-migration` (servizio utente `graphical-session-pre.target`, script `ubuntu-settings-migrate-to-defaults.18.10.1.py`): una tantum per utente, porta le chiavi vecchie ai default. Gira anche in remoto (stesso manager).
- Prima configurazione: `gnome-initial-setup` (Recommends di `ubuntu-desktop`) ha unità utente `gnome-initial-setup-first-login.service` in `gnome-session.target.wants`, con `ConditionPathExists=!%E/gnome-initial-setup-done`, `ConditionUser=!@system`, `ConditionEnvironment=XDG_SESSION_CLASS=user`. Un nuovo utente al primo accesso (anche remoto) può vedere «Welcome to Ubuntu»; sul locale accade lo stesso [S].

### 4.2 Che cosa fa REMOTIX con dconf (`REMOTIX-DEBIAN/src/session.c:1564-2000`, `child.c:10212`, `input.c:2224`, `debian/control:60,100`)
- Profilo di sessione `$XDG_RUNTIME_DIR/remotix/dconf/profile` a tre strati (`user-db`, `service-db:shm/remotix`, `file-db:…/locks.db` compilato con `dconf compile` da `dconf-cli`), esportato come `DCONF_PROFILE` nell'ambiente di gnome-session (`session.c:2754`); alla fine «neutralizzato» (solo base utente).
- Chiavi scritte **e bloccate** (`DCONF_KEYS`, `:1624`): `switch-to-session-1..12` (mutter), `org.gnome.shell always-show-log-out=true`, `lockdown disable-user-switching`, `disable-lock-screen`, `power sleep-inactive-ac-type/battery-type='nothing'`, `session idle-delay=0`, `screensaver lock-enabled=false`; solo-lock (valore da `shm`): `input-sources sources/current/mru-sources`.
- Rapporto con Ubuntu: `always-show-log-out=true` coincide con l'override Ubuntu `[org.gnome.shell:ubuntu]` (nessun conflitto). Gli override di gschema sono **default** (valori «dentro» `gschemas.compiled`), gli strati dconf di REMOTIX sono **valori memorizzati**: non si pestano, i valori Ubuntu restano finché l'utente non li cambia. `DCONF_PROFILE` in `gnome-session` + `XDG_CURRENT_DESKTOP` in tutti gli ambienti sono le due condizioni.
- dconf Ubuntu 26.04 è la **0.49** (Debian 13 ha 0.40: i commenti `[R] dconf 0.40` del codice vanno riverificati: ordine di ricerca del profilo, semantica `service-db`, effetto del lock) → prova consigliata.

---

## 5. Se è installato anche il GNOME «puro» (`gnome-session`, sessione `gnome`)

Fatti [V]: la macchina offre due file in `wayland-sessions` (`gnome`, `ubuntu`). GDM sceglie per il login: sessione scelta nella schermata → altrimenti **salvata** per l'utente (`gdm-session-worker.c:2422`, AccountsService `Session`, nome del file esatto **[S]**) → altrimenti fallback: **`ubuntu`** (patch Ubuntu `prefer_ubuntu_session_fallback`) → `gnome` → primo alfabetico.
Proposta di regola generale, **senza nominare Ubuntu**, coerente col principio del proprietario («il remoto si comporta come l'accesso locale»):
- **R1 (già in D8, da ripristinare):** fra più sessioni vince quella col **nome uguale a `ID` di os-release** (Ubuntu: `ubuntu`; Debian/Fedora: nessuna corrisponde → `gnome` → primo alfabetico). Pro: 8 righe (vedi `REMOTIX/src/session.c:895-925`), già provata il 30 set. Contro: euristica legata al nome della distribuzione; per Kubuntu/Xubuntu `ID=ubuntu` ma lì il desktop non è GNOME e il passo non è raggiunto.
- **R2 (più fedele, nuova):** prima la **sessione salvata dell'utente** (come GDM): leggere `/var/lib/AccountsService/users/<utente>` (chiave `Session=`) o chiedere ad `org.freedesktop.Accounts`; se nomina un candidato valido, usarla; altrimenti R1. Se un utente sceglie «GNOME» al monitor, il remoto gli darà «GNOME». Contro: oggi `DECISIONS.md` §0.6 dice «una macchina, un desktop» e il codice (`session.c:298`) dichiara **di non** leggere AccountsService; inoltre il processo `rootside` ha i permessi, ma la sessione di un altro utente non è nello stesso `gnome_session()` (singleton per processo: `gnome_session()` è calcolata una volta per processo ed è senza utente) → richiede di passare l'utente: **modifica strutturale (medio)**. **Decisione del proprietario.**
- Raccomandazione allo studio: **R1 subito** (copre Ubuntu stock e Ubuntu+`gnome-session` con utenti che non hanno mai cambiato sessione); R2 come decisione da proporre, perché è l'unico modo di non dare un desktop diverso a chi ha scelto «GNOME» in locale.

---

## 6. Risultati del vecchio banco: `REMOTIX/assessment/gnome/ubuntu2604.md`
- Box `t17-ubuntu2604-gnome-intel` (16 nov): 100 verdi su 112; A–D verdi. **R-DE-011 VERDE**: «sessione di default della distro: `/usr/libexec/gnome-session-service --session=ubuntu`, `gnome-session-init-worker ubuntu`». Dunque su 26.04 con sola `ubuntu` il D8 funzionava (riga 12).
- Difformità specifica di Ubuntu: **R-LOGIN-010/013** (utente inesistente → 0x0E in 1,2 s, password sbagliata 0x07 in 2,7 s) — agente 2/6, non qui (`assessment/gnome/difformita.md:53-58`).
- Non verificati su Ubuntu: R-SEC-028 AppArmor, R-AUDIO-015 RTPRIO, R-INST-006 firewall, «/» ro.
- **Il vecchio banco non misurava né `XDG_DATA_DIRS` né `DESKTOP_SESSION` né il tema della sessione remota di Ubuntu GNOME** oltre allo screenshot del 30 set (dock a sinistra, sfondo viola, Home arancione). Non c'è alcuna verifica dell'ambiente della sessione contro un accesso locale su Ubuntu GNOME.

---

## 7. Problemi da affrontare

1. **`gnome_session()`: ripristinare la corrispondenza con `ID` di os-release** (regola 3 di D8). Dove: `REMOTIX-DEBIAN/src/session.c:859-951` (dopo il blocco «only one»); vecchio codice `REMOTIX/src/session.c:871,914-920`. Peso **piccolo** (≈8 righe). Cura nota: **sì**, `REMOTIX/src/session.c` e `phases/17-the-installer.md:1466`. Senza di essa, Ubuntu con `gnome-session` installato dà `gnome` invece di `ubuntu`.
2. **Ripristinare un `local_session()` per GNOME** (almeno `DESKTOP_SESSION=<id>` e le cartelle dati/config della sessione): oggi `DESKTOP_SESSION` non è impostata per GNOME e `/usr/share/ubuntu` non è in `XDG_DATA_DIRS` (voci nascoste, es. assistente prima configurazione/`info.desktop`). Dove: `session.c:2270` (`local_session()`), usato da `add_session_names()`, `session_config_dirs()`, `session_data_dirs()`. Peso **medio**. Cura nota: **parziale**: `REMOTIX/src/session.c:2240-2370` ma con premessa errata (cerca `60x11-common_xdg_path`, che su GNOME/GDM Wayland non gira): **il criterio d'applicazione va riscritto**: la regola vera è «la sessione GNOME locale esegue `/etc/profile.d/xdg_dirs_desktop_session.sh` (e `gnome-session_gnomerc.sh`) perché gnome-session si rilancia in login shell; REMOTIX mette `SHELL=` vuoto → li emula». Applicabilità testabile in modo generale: esistenza di `/etc/profile.d/xdg_dirs_desktop_session.sh` (e, per X11/lightdm, `Xsession.d/60x11-common_xdg_path`) — **una regola, nessun nome di distro**. Va decisa la tabella di emulazione: `XDG_CONFIG_DIRS` con `/etc/xdg/xdg-<s>` (solo se esiste, come D-153, o sempre come fa lo script — nessuna differenza pratica), `XDG_DATA_DIRS` con `/usr/share/<s>` (se `s != gnome`) e `/usr/share/gnome` (se esiste).
3. **`unit_shell()`/drop-in per GNOME 50**: istanza `@ubuntu` (e `@user` per `gnome`), `ExecStart=… --mode=%i`, controllo del risultato. Dove: `session.c:2860-2882` (`unit_shell()`), `:3126-3240` (`write_dropin()`), `session.h:97-112`. Peso **grande** (è il cuore del lancio; agente 1 lo studia come unità — qui solo il legame D8). Cura nota: **sì** (`REMOTIX/src/session.c:2951-3010,3226-3233`, `session.h:129-130`, commit 7583b76). Se la modalità non resta `ubuntu` → niente dock/Yaru.
4. **`desktop_of_session_name()`: reintrodurre `ubuntu`→GNOME** (e `kubuntu/xubuntu/lubuntu` per l'agente 7). Dove: `session.c:382`. Peso **piccolo**. Cura nota: **sì** (voce 4 di `docs/PULIZIA-tranche1.md`). Rischio: `ubuntu-session` installa `lightdm.conf.d/50-ubuntu.conf` anche sulle altre varianti: vale sempre l'ultimo file (`60-xubuntu.conf`) → serve il test.
5. **`XDG_CURRENT_DESKTOP` deve restare `ubuntu:GNOME`** in ogni processo (override gschema per desktop): oggi lo mette `compose_environment()` (`session.c:2712`) e finisce nel manager via gnome-session. Peso **piccolo** (già fatto; da proteggere con un controllo di prova su `/proc/<gnome-shell>/environ` e su un'app avviata via D-Bus). Cura nota: sì (stesso codice).
6. **Emulazione di `profile.d`/`~/.profile` a SHELL vuota**: restano fuori `~/.gnomerc` (solo X11/Wayland con `XDG_CURRENT_DESKTOP=GNOME`), `im-config` (variabili input method), `cedilla-portuguese.sh`, variabili personali di `~/.profile`. Dove: `session.c:2733-2741`. Peso **medio** come decisione, **piccolo** se si accetta la differenza dichiarata (scelta già fatta per Debian: ambiente composto da zero). Cura nota: no.
7. **Sessione con GNOME puro installato (R2: sessione salvata dell'utente)** — decisione del proprietario (sezione 5). Dove: `session.c:298` (dichiarazione «non letta»), `gnome_session()` (singleton senza utente). Peso **medio**. Cura nota: no.
8. **Versioni: gnome-session 50 e dconf 0.49 vs Debian 13 (48, 0.40)**: i commenti `[R]` che citano 0.40/48 e l'`ExecStart` delle unità vanno riverificati su 26.04 (profilo dconf, lock, `gnome-session-ctl`). Peso **medio** (solo prove). Cura nota: parziale (vecchio banco GNOME 26.04 verde su S3/S5).
9. **Condizione del servizio Shell**: `AssertEnvironment=XDG_SESSION_TYPE=wayland` (nel 26.04 è **Assert**, nel codice vecchio si citava `ConditionEnvironment`): il codice già mette `XDG_SESSION_TYPE=wayland` (`:2724`). Peso **piccolo** (aggiornare il commento). Cura nota: sì.
10. **Prima configurazione («Welcome to Ubuntu»)** per un nuovo utente al primo accesso remoto: coerente col locale, ma disturba il flusso di prova. Peso **piccolo**, cura nota: no (solo da osservare).

## 8. Che cosa non si può sapere senza provare
- Il valore **esatto** di `XDG_DATA_DIRS`/`XDG_CONFIG_DIRS`/`PATH` in una sessione GDM locale di Ubuntu 26.04 (ordine fra `/usr/share/ubuntu`, `/usr/share/gnome`, snapd), e se `/usr/share/gnome` esiste.
- Se in 26.04 il rilancio in login shell avviene davvero in ogni accesso GDM (richiede `SHELL` valida e `XDG_SESSION_TYPE=wayland` nell'ambiente del leader; letto nel sorgente, non osservato).
- Se `~/.profile` standard di Ubuntu (skeleton) aggiunge qualcosa di importante (`~/.local/bin` nel `PATH`).
- Se il chiave `Session=` di AccountsService è il posto/nome giusto (non verificato nel sorgente di accountsservice/gdm settings).
- Se la prima configurazione parte in remoto, e se `ubuntu-desktop` la installa (`gnome-initial-setup` è solo Recommends).
- Se dconf 0.49 si comporta come 0.40 con i tre strati e i lock.
- Se `user-session-migration` ha effetti collaterali nella sessione remota.
- Se, con `gnome-session` (universe) installato, il login locale offre «Ubuntu» e «GNOME» nel menu e quale è marcata di default per un utente nuovo (letto: fallback `ubuntu`).

## 9. Prove consigliate (le decide il proprietario)
1. **Fotografia dell'ambiente locale**: su una VM Ubuntu 26.04 Desktop (immagine vera), login da GDM, poi `systemctl --user show-environment`, `tr '\0' '\n' < /proc/$(pgrep -u $USER gnome-shell)/environ`, `echo $XDG_DATA_DIRS $XDG_CONFIG_DIRS $DESKTOP_SESSION $XDG_CURRENT_DESKTOP` in un terminale, e `gsettings get org.gnome.desktop.interface gtk-theme`. Ripetere con `gnome-session` installato e selezionando «GNOME».
2. **Stessa fotografia nella sessione remota** (dopo il porting) e confronto riga per riga, con `diff` su un elenco di variabili.
3. **Prova D8**: VM con `ubuntu-desktop-minimal` (solo `ubuntu`) e VM con in più `gnome-session`; il log `D8:` deve dire `ubuntu` in entrambe.
4. **Prova modalità**: `/proc/<gnome-shell>/cmdline` contiene `--mode=ubuntu`; schermata con dock a sinistra, Yaru, cartella Home arancione (ding); `gsettings` default letti da un'app avviata via D-Bus restano `Yaru`.
5. **Prova dconf**: `dconf dump /` dell'utente dopo una sessione remota non contiene le chiavi di REMOTIX; i lock funzionano (0.49).
6. **Prova prima configurazione**: nuovo utente appena creato, primo accesso remoto e locale: stesso comportamento.
7. **Prova `lightdm.conf.d/50-ubuntu.conf`** su Xubuntu/Kubuntu (agente 7): `declared_sessions()` torna la sessione giusta.
