# Studio 1 — Come nasce una sessione GNOME 50 su Ubuntu 26.04 e che cosa deve cambiare in REMOTIX

18 nov 2026, agente di studio 1. Solo studio: nessun file del prodotto toccato, nessuna prova del prodotto.
Legenda: **[V]** verificato (dove), **[W]** dal web, **[S]** supposizione.
Abbreviazioni: `DEB` = `/home/nicfio/Documenti/REMOTIX-DEBIAN` (codice 1.0.0), `OLD` = `/home/nicfio/Documenti/REMOTIX` (albero 1.5.x ritirato).
Fatti Ubuntu: contenitore `studio-1` (immagine `ubuntu:26.04`, 26.04.1 LTS «resolute») sul server; pacchetti scaricati e spacchettati in
`/media/REMOTIX-UBUNTU/studio/1/x/<pacchetto>/`, sorgenti in `.../1/src/` (gnome-session 50.1, gnome-shell 50.1, mutter 50.1, gdm3 50.1),
sorgenti upstream 48 [W] (download.gnome.org: gnome-session 48.0, gnome-shell 48.7, mutter 48.7) in `.../1/old48/`.
Il contenitore è stato rimosso a fine lavoro; la cartella resta.

---------------------------------------------------------------------------------------------------------------------------------

## 0. In breve

1. Su Ubuntu 26.04 la shell non ha più l'unità `org.gnome.Shell@wayland.service` ma il **template** `org.gnome.Shell@.service`
   con `ExecStart=/usr/bin/gnome-shell --mode=%i`; la sessione `ubuntu` chiede l'istanza `org.gnome.Shell@ubuntu.service`
   (la `gnome`: `@user`). [V] pacchetti `gnome-shell-common` 50.1-0ubuntu1.5, `ubuntu-session` 50.1-0ubuntu0.1.
2. Il codice Debian (`unit_shell()`, `session.c:2863`) non riconosce il template: **su Ubuntu fallisce chiuso** («I do not recognise the
   Shell unit»), `write_dropin()` torna FALSE, `session_spawn()` rifiuta di far nascere la sessione (`session.c:7065-7071`). Nessun falso
   verde, ma nessun desktop. Il pezzo tolto il 17 nov (PULIZIA voce 6) è esattamente ciò che serve.
3. Il drop-in deve riportare `--mode=%i` (la modalità `ubuntu` vive nel nome dell'istanza: dock, Yaru, estensioni). Senza, la shell parte in
   modalità `user`. [V] `gnome-shell/src/main.c` 50.1: la modalità viene da `--mode`, da `GNOME_SHELL_SESSION_MODE`, o `user`.
4. Le opzioni che REMOTIX usa (`--headless`, `--no-x11`) esistono ancora in 50 con lo stesso senso. [V] `gnome-shell --help` e un avvio vero
   nel contenitore: `gnome-shell --headless --no-x11 --mode=ubuntu` → «Running GNOME Shell (using mutter 50.1) as a Wayland display server»,
   «Created surfaceless renderer without GPU», «Using Wayland display name 'wayland-0'».
   **Spariti** in 50: `--nested`, `--x11`, `--replace`, `--display`, `--sm-*`, `--sync` (provati: «Unknown option»). Nuovo: `--devkit`.
   `--virtual-monitor` c'è ancora (REMOTIX non lo usa dal 14 ago).
5. gnome-session 50 non è più quello di 48 dentro: nessun gestore di servizi interno, tutto systemd; il «capo» (leader) è
   `gnome-session-init-worker` e **rifiuta di partire se `graphical-session.target` è già attivo** («A graphical session is already running!»).
   Questo è un fatto nuovo: tocca il guardiano di nascita (`inactive_unit()`) e la convivenza locale/remoto.
6. I nomi delle due unità che REMOTIX aspetta alla chiusura (`gnome-session-manager@<sessione>.service`, `gnome-session-restart-dbus.service`)
   e l'API `org.gnome.Mutter.DisplayConfig.GetCurrentState` sono **invariati** [V].
7. Per la scelta della sessione: su Ubuntu standard l'unico file in `wayland-sessions` è `ubuntu.desktop`; se si installa `gnome-session`
   compare anche `gnome.desktop` e il codice Debian sceglierebbe `gnome`, non `ubuntu` (voce 5 della pulizia). Cura nota.

---------------------------------------------------------------------------------------------------------------------------------

## 1. Come REMOTIX avvia GNOME oggi (DEB, Debian 13, GNOME 48) — il percorso

Tutti i riferimenti sono `DEB/src/session.c` salvo diversa indicazione.

**1.1 Chi chiama.** `child.c:8649` legge lo stato (`session_state`); se `SESSION_DEAD` e non «chiusa dall'utente» (`child.c:8703-8730`) e fuori
dal freno `is_being_born()` (`BIRTH_REIN_MS 12000`, `child.c:5489`) chiama `session_spawn(canvas_w, canvas_h)` (`child.c:8722`) e **torna subito**
(non aspetta: l'attesa è il ciclo di riprova del padre, 1 s → 30 s). `session_ensure()` (`session.c:7209`, con attese `WAIT_STARTUP_MS 40000`,
`GRACE_MONITOR_MS 5000`) non è chiamata dal figlio: è solo definita e dichiarata in `session.h:642`.

**1.2 `session_spawn()` (`session.c:7017-7207`).** Ordine fisso:
1. `is_nobody()`: nessun desktop riconosciuto ⇒ non tenta (`7031`).
2. `session_state()` deve dare `SESSION_DEAD` (`7040`).
3. `session_clear_out_handler("birth: …")` (ripulisce residui di una sessione finita male), `session_snapshot_handler()` (foto delle variabili del
   gestore utente, `3904`), `dconf_profile_reinstate()` (`7053-7060`).
4. **`write_dropin(width, height)`** PRIMA del comando (`7065`): se FALSE, niente nascita.
5. `systemctl --user is-system-running` ≠ `stopping` (`7094-7110`).
6. `inactive_unit()`: la sessione precedente deve essere davvero finita (`7127`; `3544-3619`).
7. Rimozione di un `pipewire-pulse` rimasto di una sessione precedente (`7156-7196`).
8. `session_dconf_birth()` (solo GNOME) e `session_settings()` (`7202-7204`).
9. `start()` (`7206`).

**1.3 `write_dropin()` (`2909-3182`).** Per GNOME (ramo non-KDE, non-XFCE/LXQt):
- `unit = unit_shell()` (`2962`); NULL ⇒ FALSE.
- Cartella: `$XDG_RUNTIME_DIR/systemd/user.control/<unit>.d/`, file `zz-remotix-monitor.conf` (`2969-2975`). Il `zz-` serve a vincere su altri
  drop-in (ordinamento per nome di file fra tutte le cartelle).
- Contenuto (`3098-3101`): `[Service]\nExecStart=\nExecStart=<gnome-shell trovato nel PATH, altrimenti /usr/bin/gnome-shell> --headless --no-x11\n`.
  `width`/`height` NON entrano (dal 14 ago 2026: nessun `--virtual-monitor`; l'unico monitor lo monta la cattura con `RecordVirtual`).
- `systemctl --user daemon-reload`, poi rilegge `systemctl --user show -p ExecStart --value <unit>` e controlla che contenga `--headless --no-x11`
  e **non** `--virtual-monitor` (`3140-3165`): «scritto non vuol dire in vigore» (errore E1).

**1.4 `unit_shell()` (`2863-2882`).** Chiede al gestore `systemctl --user show -p FragmentPath --value org.gnome.Shell@wayland.service`;
se il percorso finisce in `/org.gnome.Shell@wayland.service` restituisce quel nome; altrimenti log «I do not recognise the Shell unit» e NULL.
Costante `SESSION_UNIT_SHELL_48` in `session.h:112`.

**1.5 `start()` (`3424-3505`).** `command = gnome_session()->line` (la riga `Exec` della sessione, argomento per argomento,
preceduta da `exec`); ambiente composto da zero (`compose_environment()`); log della sessione (`log_session_path()`); `setsid --fork sh -c
"exec >>log 2>&1; <command>"` con `g_spawn_sync` (`3432`, `3497`). `setsid --fork` stacca la sessione dal gruppo di processi:
se REMOTIX si riavvia il desktop sopravvive (T2 del 29 set). Ritorna TRUE appena `setsid` ha forkato: **non dice se gnome-session ha avuto successo**.

**1.6 `gnome_session()` (`859-952`, criterio D8).** Candidati: `<XDG data dirs>/wayland-sessions/*.desktop` la cui `Exec` lancia `gnome-session`
(nome da `--session=`, senza: `gnome`) E per cui esiste `<data>/gnome-session/sessions/<nome>.session`, e `TryExec` trovabile. Scelta:
(1) uno solo ⇒ quello; (2) più d'uno ⇒ quello di nome `gnome` (`SESSION_GNOME_FALLBACK`, `session.h:105`); (3) altrimenti il primo in ordine alfabetico;
(4) nessuno ⇒ fallback dichiarato a `gnome`. Produce: `name` (`--session`), `id` (file senza estensione → `XDG_SESSION_DESKTOP`),
`line`, `desktop` (da `DesktopNames` unito con `:` → `XDG_CURRENT_DESKTOP`), `handler` (`gnome-session-manager@<name>.service`).

**1.7 `compose_environment()` (`2438-2790`), blocco GNOME (`2705-2790`).** Da zero: `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`,
`XDG_CURRENT_DESKTOP` (da `desktop`), `XDG_SESSION_DESKTOP` (da `id`), `add_session_names()` (qui oggi vuoto: `local_session()` è un guscio vuoto, `2270-2289`),
eventuale `XDG_CONFIG_DIRS`, **`XDG_SESSION_TYPE=wayland`** (`2730`; serve all'unità della shell), **`SHELL=` vuoto** (`2744`; evita il re-exec in
login shell di gnome-session), `DCONF_PROFILE` (`2751`), poi `LANG` UTF-8, `HOME`, `USER`, `PATH`. Non passa `XDG_SESSION_ID`
(scelta dichiarata `2753-2762`).

**1.8 «Desktop pronto».** `session_alive()` (`993-1041`): per GNOME `org.gnome.Mutter.DisplayConfig` ha un proprietario sul bus (`NameHasOwner`,
`NO_AUTO_START`) E la chiamata `GetCurrentState` ottiene risposta (senza interpretarla). `session_state()` (`1203-1311`) legge la risposta:
0 monitor ⇒ `SESSION_BLACK` (cioè il caso BUONO dopo la cura del 14 ago); 1 monitor ⇒ `HEALTHY` (che ora è un difetto: la sessione ha preso un monitor suo);
più monitor ⇒ `SELF_CHOSEN` (cattura viva, non si tocca). Tipo atteso `TYPE_STATE "(ua((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv})"` (`145`).
**Nessun controllo di «shell pronta» oltre a questo**: né `gnome-session-initialized.target`, né il segnale `SessionRunning` (mai emesso/usato).
Il figlio non monta la cattura finché lo stato è `NOT_READ` (`child.c:8764-8780`).

**1.9 Guardie di nascita/fine.** `inactive_unit()` (`3544-3619`): per GNOME `unit_stopped(gnome_session()->handler) && unit_stopped("gnome-session-restart-dbus.service")`
(`3618`; `unit_stopped` accetta `inactive`/`failed`/`unknown`, `3532`). Costanti: `session.h:112-119`.

**1.10 Pulizia.** `OUR_VARIABLES` (`3843`: `DCONF_PROFILE`, `XDG_*`, `SHELL`, `LANG`, `PATH`, `WAYLAND_DISPLAY`, `DISPLAY`, `GNOME_SHELL_SESSION_MODE`…) e
`OUR_DROPINS` (`3856`, solo KDE e xfconfd); le istanze della shell sono cercate **per nome di cartella** `org.gnome.Shell@*.service.d` e di ognuna
si toglie SOLO `zz-remotix-monitor.conf` (`3994-4015`). Quindi la pulizia è già generica per qualunque istanza (`@wayland`, `@user`, `@ubuntu`).

**1.11 Come un desktop vivo viene ritrovato.** `rediscover.h:27-36`: criterio funzionale, senza nomi di processo: sessione logind del servizio PAM
`remotix`; nel suo scope un processo dell'utente con pid = sid e padre fuori dallo scope (firma di `setsid --fork`). Nessun `grep` di
`gnome-session-binary` nel codice (verificato: solo commenti `rediscover.h:27`, `session.c:2741`, `child.c:11531`). In 50 il processo con pid = sid
è `gnome-session-init-worker` (vedi §4): il criterio regge.

---------------------------------------------------------------------------------------------------------------------------------

## 2. Che cosa fu tolto il 17 nov e che cosa faceva — confronto OLD / DEB (`diff` solo zone GNOME)

`docs/PULIZIA-tranche1.md` voci 4, 5, 6, 7 (DEB). Diff reale fra `DEB/src/session.c` e `OLD/src/session.c` (solo hunk GNOME):

**2.1 Voce 6 — template GNOME 50 (`unit_shell()`, `SESSION_UNIT_SHELL_MODEL`, `--mode=%i`, guardia cartella template).**

| Zona | OLD | DEB |
|---|---|---|
| `session.h` | `107-127` testo + `#define SESSION_UNIT_SHELL_MODEL "org.gnome.Shell@.service"` (riga 130) | `107-110` (testo ridotto), la costante non c'è più |
| `unit_shell()` | `OLD session.c:2966-3009`: se `FragmentPath` di `@wayland` finisce in `@wayland.service` ⇒ `@wayland`; se finisce in `@.service` (template) ⇒ chiede `systemctl --user show -p Requires --value gnome-session@<gnome_session()->name>.target`, scorre le voci e prende la prima `org.gnome.Shell@…​.service` diversa dal template; nessuna ⇒ NULL con log | `DEB 2863-2882`: solo il primo caso |
| contenuto drop-in | `OLD 3231-3234`: `ExecStart=%s --headless --no-x11%s` con suffisso `" --mode=%i"` se `unit != SESSION_UNIT_SHELL_48` | `DEB 3098-3101`: nessun suffisso |
| pulizia istanze | `OLD 4133-4136`: salta la cartella `org.gnome.Shell@.service.d` | `DEB 3994-4002`: nessun salto (innocuo: da noi non si scrive mai là, e si toglie comunque solo il nostro file) |

Perché esisteva (OLD `phases/17-the-installer.md` §5.1 righe 281-298; `DECISIONS.md` §10.20 D8): su GNOME 50 `systemctl show -p ExecStart org.gnome.Shell@wayland.service`
**crea l'istanza «wayland» dal template, le applica il nostro drop-in e restituisce la nostra riga**: il controllo passava, ma gnome-session avviava `@user`/`@ubuntu`
senza `--headless`. Era un **falso verde**; la cura sceglie l'unità da ciò che è installato e rilegge lo stesso nome. La seconda parte (`--mode=%i`) venne dopo,
con la sessione `ubuntu` (OLD `phases/17-the-installer.md` riga 1466, `[M]` 30 set: «process `gnome-shell --headless --no-x11 --mode=ubuntu`; screenshot: dock di Ubuntu a sinistra»).
⚠ Il testo di §5.1 (righe 296-304: «la riga `--headless --no-x11` senza `--mode=%i`») è **superato** dal commit 7583b76 (riga 1466): il codice finale tiene `--mode=%i`.

**2.2 Voce 5 — `os-release ID` in `gnome_session()` (OLD `session.c:871` e `916-920`).** Dopo il criterio «uno solo» e prima di «`gnome`»: se un
candidato ha `--session` = `ID` di os-release (`ubuntu`) lo sceglie (`g_get_os_info(G_OS_INFO_KEY_ID)`). Serve quando la macchina offre sia `ubuntu` sia
`gnome`. Su Debian non ha effetto (nessuna sessione `debian`). Su Ubuntu **cambia il risultato** (vedi problema 4).

**2.3 Voce 4 — nomi Ubuntu in `desktop_of_session_name()`** (OLD `session.c:381-393`: `xubuntu`, `lubuntu`, `kubuntu`, `ubuntu` — con l'avvertenza che i tre sapori contengono «ubuntu» e vanno chiesti PRIMA).
Riguarda il riconoscimento del sapore (agente 3/6); per GNOME conta solo perché `declared_sessions()` (lightdm/sddm) non è usata con gdm3.

**2.4 Voce 7 — D-153, ambiente «come un login locale»** (OLD `session.c:2274-2346`: `session_folder_there()`, `by_name()`, `local_session_name_find()`, `xsession_d_applies()`;
`DECISIONS.md` §10.54 righe 7202-7240): imposta `DESKTOP_SESSION=<sessione>`, aggiunge `/etc/xdg/xdg-<sessione>` a `XDG_CONFIG_DIRS` e `/usr/share/<sessione>` (mai per `gnome`)
a `XDG_DATA_DIRS`, **solo se** `/etc/X11/Xsession.d/60x11-common_xdg_path` esiste e il login locale della sessione passa da `Xsession.d`. Per GNOME il nome è
quello della sessione che REMOTIX avvia. Vedi §6: su Ubuntu serve ancora.

**2.5 Altri hunk GNOME della diff (solo commenti/prefissi):** `session.c:1103` (`⚠`↔`⛔` in un log), `2825` (idem). Nessun'altra differenza di comportamento GNOME.
Il resto della diff è KDE (`session_kde_logout_watch`, `4176-4295`) e `session_force_unless_orphaned` (1.0.0 Debian), non pertinente.

---------------------------------------------------------------------------------------------------------------------------------

## 3. La realtà di Ubuntu 26.04 [V] (pacchetti veri, contenitore `studio-1`)

**3.1 Versioni** (`apt-cache policy`, suite `resolute`+`-updates`): `gnome-shell` 50.1-0ubuntu1.5 · `gnome-shell-common` idem · `mutter` / `mutter-common` / `libmutter-18-0`
50.1-0ubuntu2.5 · `gnome-session`, `gnome-session-bin`, `gnome-session-common`, `ubuntu-session`, `gdm3` 50.1-0ubuntu0.1 · `gnome-settings-daemon` 50.0-1ubuntu1 ·
`ubuntu-settings` 26.04.6 · `systemd` 259.9-0ubuntu0.1 · `dbus` 1.16.2-2ubuntu4 · `xwayland` 2:24.1.10-1 · `ubuntu-desktop` 1.570.4.
Debian 13 (da OLD/DEB, `PULIZIA-tranche1.md` riga 6): gnome-shell 48.7, gnome-session 48.x.

**3.2 Chi porta che cosa** (`dpkg-deb -x`):
- `gnome-session-bin`: `/usr/bin/gnome-session`, `/usr/bin/gnome-session-inhibit`, `/usr/bin/gnome-session-quit`, `/usr/libexec/gnome-session-ctl`, `/usr/libexec/gnome-session-init-worker`,
  `/usr/libexec/gnome-session-service`. **Nessuna unità systemd.**
- `gnome-session-common`: tutte le unità `/usr/lib/systemd/user/gnome-session*`: `gnome-session@.target`, `gnome-session.target`, `gnome-session-manager@.service`,
  `gnome-session-manager.target`, `gnome-session-pre.target`, `gnome-session-initialized.target`, `gnome-session-basic-services.target`, `gnome-session-services.target`,
  `gnome-session-shutdown.target`, `gnome-session-restart-dbus.service`, `gnome-session-monitor.service`, `gnome-session-signal-init.service`,
  `gnome-session-x11-services(-ready).target`, `app-gnome-.scope.d/override.conf`, `app-flatpak-.scope.d/override.conf`; più `/etc/profile.d/xdg_dirs_desktop_session.sh`.
- `gnome-shell-common`: `/usr/lib/systemd/user/org.gnome.Shell@.service` (template), `org.gnome.Shell-disable-extensions.service`, e `/usr/share/gnome-shell/modes/ubuntu.json`.
  La modalità `user` non ha file: è interna alla shell.
- `gnome-session` (**non** installato da `ubuntu-desktop`: `apt-cache depends ubuntu-desktop` non lo contiene): `/usr/share/wayland-sessions/gnome.desktop`,
  `/usr/share/gnome-session/sessions/gnome.session`, `/usr/lib/systemd/user/gnome-session@gnome.target.d/gnome.session.conf`.
- `ubuntu-session` (Depends: gnome-session-bin, gnome-session-common, gnome-settings-daemon, gnome-shell, gnome-shell-ubuntu-extensions, xdg-desktop-portal-gnome, xwayland,
  yaru-theme-gnome-shell, user-session-migration): `/usr/share/wayland-sessions/ubuntu.desktop`, `/usr/share/gnome-session/sessions/ubuntu.session`,
  `/usr/lib/systemd/user/gnome-session@ubuntu.target.d/ubuntu.session.conf`.
- `gdm3`: `gnome-session@gnome-login.target.d/gnome-login.session.conf` (`Requires=org.gnome.Shell@gdm.service`), `gnome-login.session` (`Kiosk=true`),
  `/usr/share/gdm/greeter/wayland-sessions/gnome-greeter.desktop`, `gnome-initial-setup.desktop`; due drop-in `70-gdm-skip.conf` per unità snapd.
- `gnome-settings-daemon-common`: tutte le `org.gnome.SettingsDaemon.*.{service,target}` (Power, MediaKeys, Color, … nomi invariati).

**3.3 Contenuto delle unità decisive** (testo reale):

`org.gnome.Shell@.service`:
```
[Unit] Description=GNOME Shell
OnFailure=org.gnome.Shell-disable-extensions.service gnome-session-shutdown.target
OnFailureJobMode=replace-irreversibly
CollectMode=inactive-or-failed
RefuseManualStart=on  RefuseManualStop=on
After=gnome-session-manager.target
Requisite=gnome-session-initialized.target  PartOf=gnome-session-initialized.target  Before=gnome-session-initialized.target
AssertEnvironment=XDG_SESSION_TYPE=wayland
[Service] Slice=session.slice  Type=notify
ExecStart=/usr/bin/gnome-shell --mode=%i
SuccessExitStatus=1
ExecStopPost=-systemctl --user unset-environment GNOME_SETUP_DISPLAY WAYLAND_DISPLAY DISPLAY XAUTHORITY
Restart=no  TimeoutStopSec=5  OOMScoreAdjust=-1000
```
`gnome-session@ubuntu.target.d/ubuntu.session.conf`: `Requires=gnome-session-services.target` + `Requires=org.gnome.Shell@ubuntu.service`.
`gnome-session@gnome.target.d/gnome.session.conf`: `Requires=gnome-session-services.target` + `Requires=org.gnome.Shell@user.service`.
`gnome-session@.target`: `Requires=gnome-session-initialized.target`, `Requires=gnome-session.target`, `Requires=gnome-session-manager@.service`
(il `@.` diventa l'istanza `@<sessione>`), `PartOf=graphical-session.target`, `OnFailure=gnome-session-shutdown.target`.
`gnome-session-manager@.service`: `Type=notify`, `ExecStart=/usr/libexec/gnome-session-service --session=%i`, `ExecStopPost=-/usr/libexec/gnome-session-ctl --shutdown`.
`gnome-session-restart-dbus.service`: `ExecStart=/usr/libexec/gnome-session-ctl --restart-dbus` (che fa `StopUnit("dbus.service","fail")`: `tools/gnome-session-ctl.c` 50.1 ~righe 105-135).
`gnome-session-shutdown.target`: `Conflicts=graphical-session.target … gnome-session.target …`, `Wants=gnome-session-restart-dbus.service`.
`gnome-session-services.target` ha `Wants=` per gsd (Color, Datetime, Housekeeping, PrintNotifications, ScreensaverProxy, Sound, Wwan), `gnome-disk-utility-notify.service`,
`localsearch-3.service`, `gcr-ssh-agent.socket`, `gnome-software.service`, `user-dirs-update-gtk.service`, `evolution-alarm-notify.service` (tutti `Wants`, non `Requires`).

**3.4 File sessione** `[V]`:
`/usr/share/wayland-sessions/ubuntu.desktop`: `Exec=/usr/bin/gnome-session --session=ubuntu`, `TryExec=/usr/bin/gnome-session`, `DesktopNames=ubuntu;GNOME`, `X-GDM-SessionRegisters=true`, `X-GDM-CanRunHeadless=true`.
`gnome.desktop`: `Exec=/usr/bin/gnome-session --session=gnome`, `DesktopNames=GNOME`.
`/usr/share/gnome-session/sessions/ubuntu.session`: solo `[GNOME Session] Name=Ubuntu` (nessun `RequiredComponents`: tolti in gnome-session 49).
**Non c'è nessun `env GNOME_SHELL_SESSION_MODE=…` nella `Exec`** (c'era nelle Ubuntu precedenti): la modalità arriva solo dal nome dell'istanza. Non esistono `xsessions/*` di gnome-session 50 (X11 tolto).
Con `has_candidate()` (`DEB 816-857`) risulta: nome `ubuntu`, `id` `ubuntu`, `desktop` `ubuntu:GNOME`, handler `gnome-session-manager@ubuntu.service`, riga `exec '/usr/bin/gnome-session' '--session=ubuntu'` ✓.

**3.5 Modalità `ubuntu`** (`gnome-shell-common` `modes/ubuntu.json`): `parentMode: user`, stylesheet Yaru, `enabledExtensions`: `ubuntu-dock@`, `ubuntu-appindicators@`, `ding@rastersoft.com`, `tiling-assistant@`,
`snapd-prompting@`, `snapd-search-provider@`, `web-search-provider@ubuntu.com`. (Estensioni: argomento dell'agente 3.)
Patch Ubuntu rilevanti alla shell: `ubuntu/desktop_detect.patch` (`js/misc/desktop.js`: legge `XDG_CURRENT_DESKTOP`, quindi serve `ubuntu:GNOME`), `ubuntu/layout-Make-starting-in-the-overview-configurable…` (chiave `org.gnome.shell start-in-overview`, agente 3).

---------------------------------------------------------------------------------------------------------------------------------

## 4. gnome-session 50 rispetto a 48 (sorgenti: 50.1 Ubuntu `[V]`; 48.0 upstream `[W]`; `NEWS` di 50.1)

**Dal NEWS di 50.1** (`apt-get source gnome-session`): 49.alpha: rimossi XSMP e ripristino sessione, X11 disattivato, `gnome-dummy` tolta;
49.beta: **gnome-session non è più uno script di shell** (tutto in C), **gestore di servizi interno rimosso** (tutto systemd), tolta la «fail whale», tolte le
sessioni di ripiego («fallback»), nuova `gnome-session-basic-services.target`, opzione `--autostart` rimossa (sessioni kiosk: `Kiosk=true`);
49.rc: la parte systemd del leader in un eseguibile a parte (`gnome-session-init-worker`);
50.alpha: **X11 tolto** (le unità `gnome-session*.target` sono solo Wayland), **le unità prendono la modalità della shell come argomento** (`org.gnome.Shell@.service`),
e: «**Improved safety check that enforces only one active graphical session per user by checking for any running graphical session, not just another GNOME session**».

**Confronto strutturale (unità):**

| | 48.0 [W] (Debian 13) | 50.1 [V] (Ubuntu 26.04) |
|---|---|---|
| processo capo | `gnome-session` = script `gnome-session.in` → `exec gnome-session-binary` (anche con `--systemd-service` per il gestore) | `gnome-session` (binario C) → `execl` di `/usr/libexec/gnome-session-init-worker <sessione>`; il gestore è `gnome-session-service --session=%i` |
| avvia | `gnome-session-wayland@<sessione>.target` (da `XDG_SESSION_TYPE`, `main.c:645-657`) | direttamente `gnome-session@<sessione>.target` (`leader-systemd.c:305-308`) |
| shell | `org.gnome.Shell@wayland.service` (file vero; c'è anche `@x11`), `ConditionEnvironment=XDG_SESSION_TYPE=%I` | template `org.gnome.Shell@.service`, `--mode=%i`, `AssertEnvironment=XDG_SESSION_TYPE=wayland` |
| chi chiede la shell | `gnome-session@<sessione>.target` + `gnome-session-wayland.target` | drop-in `gnome-session@<sessione>.target.d/<sessione>.session.conf` (`Requires=org.gnome.Shell@<istanza>.service`) |
| unità gestore/dbus | `gnome-session-manager@.service`, `gnome-session-restart-dbus.service` | **stessi nomi** |
| fallimento | `gnome-session-failed.target` (X11), shutdown (Wayland) | solo `gnome-session-shutdown.target` |
| controllo «sessione già attiva» | solo «Session manager already running!» (nome sul bus, `main.c:687`) | **`graphical-session.target` attivo ⇒ `g_error("A graphical session is already running!")`** (`leader-systemd.c:290-291`), PRIMA di avviare qualsiasi unità; in più `ResetFailed` globale (`297-302`) |
| login shell | `gnome-session.in`: la condizione testa `XDG_SESSION_TYPE = "xwayland"` (refuso: mai vera su Wayland) ⇒ **in 48.0 il re-exec non avviene** [W; se Debian lo patchi: non verificato] | `leader-main.c:72-118`: con `XDG_SESSION_TYPE=wayland`, `SHELL` non vuoto e in `/etc/shells` (non `false`/`nologin`) ⇒ **re-exec reale** `exec -l $SHELL -c 'exec gnome-session --no-reexec …'` |
| variabili che il leader aggiunge | `XDG_MENU_PREFIX=gnome-`, `QT_IM_MODULE`/`XMODIFIERS` (se ibus), `GIO_USE_VFS`… (`main.c`) | `XDG_MENU_PREFIX=gnome-`, `GNOME_DESKTOP_SESSION_ID=this-is-deprecated`, e se c'è `ibus-daemon` nel PATH: `QT_IM_MODULES=wayland;ibus`, `QT_IM_MODULE=ibus`, `XMODIFIERS=@im=ibus` (`leader-main.c:121-188`). Se `XDG_SESSION_TYPE=tty` lo forza a `wayland` (`244-247`) |
| esporta ambiente | `variable_blacklist` = NOTIFY_SOCKET, XDG_SEAT, XDG_SESSION_ID, XDG_VTNR; lista «unset se non impostate»: DISPLAY, XAUTHORITY, WAYLAND_DISPLAY, WAYLAND_SOCKET, GNOME_SHELL_SESSION_MODE, GNOME_SETUP_DISPLAY, LC_* | **uguali** (`gsm-util.c:46-85` 50.1) ⇒ `OUR_VARIABLES` (`DEB 3843`) copre ancora l'essenziale |
| D-Bus `org.gnome.SessionManager` | `Logout`, `IsSessionRunning`, `SessionOver` (mai emesso) | stessi metodi/segnali; aggiunti `Suspend`, `CanReboot`, `CanSuspend`, `RegisterRestore`, `RequestShutdown/Reboot`; tolti `GetClients`, `IsAutostartConditionHandled` (diff delle XML). `Logout` c'è (chiusura: agente 2) |

**Il leader (50) in dettaglio** (`gnome-session/leader-systemd.c`, 333 righe, `[V]`): esporta l'ambiente nel gestore systemd; si collega al bus di sessione; **se
`graphical-session.target` è attivo ⇒ `g_error` (abort)**; `ResetFailed`; `StartUnit(gnome-session@<sessione>.target, "fail")`; apre la FIFO
`$XDG_RUNTIME_DIR/gnome-session-leader-fifo` e **resta vivo** fino alla fine della sessione (SIGTERM/SIGHUP/SIGINT ⇒ avvia `gnome-session-shutdown.target`; si chiude quando
`graphical-session-pre.target` diventa `inactive`). Stessa forma del `gnome-session-binary` di 48 (FIFO + attesa): la lezione «un sentinella gratuito» di `STUDIES.md` §gnome §3.2 (OLD righe 767-771) vale ancora.
Dopo `exec` il pid non cambia ⇒ il leader resta pid = sid (firma di `setsid --fork`), con `comm` `gnome-session-i` (15 caratteri).

---------------------------------------------------------------------------------------------------------------------------------

## 5. Le opzioni di mutter/gnome-shell che REMOTIX usa: esistono ancora? [V]

| Opzione | 48.7 [W] | 50.1 [V] | Senso |
|---|---|---|---|
| `--headless` | sì | sì (`mutter 50.1 src/core/meta-context-main.c:380`; `gnome-shell --help`) | backend nativo `META_BACKEND_NATIVE_MODE_HEADLESS` (`create_headless_backend`); `needs_outputs = !(mode & HEADLESS)` ⇒ **zero monitor propri** (`meta-backend-native.c:253`) — identico a 48 (`:240`) |
| `--no-x11` | sì | sì (`:361`, solo se mutter ha Xwayland) | politica X11 disabilitata. Senza `--no-x11`: `ON_DEMAND` se la shell gira in un'unità utente (`sd_pid_get_user_unit`), `MANDATORY` altrimenti (`meta_context_main_get_x11_display_policy`) |
| `--wayland` | sì | sì (`:354`) | non usata da REMOTIX |
| `--virtual-monitor WxH[@R]` | sì | sì (`:385`); callback con vendor `MetaVendor`, prodotto `MetaVirtualMonitor`, seriale `0x%.2x` | non più usata dal 14 ago 2026 |
| `--mode=<m>` | sì | sì (shell `main.c:604`) | `user` (default), `gdm`, `ubuntu`, … |
| `--display-server` | sì | sì | «display server completo» (non usata) |
| `--nested` | sì | **no** («Unknown option» provato) | — |
| `--x11` / `--replace` / `--display` / `--sm-*` / `--sync` | sì | **no** | — |
| `--devkit` | no | sì (nuovo, esegue come headless) | strumenti di sviluppo |

Precedenza della modalità (shell 50 `src/main.c:702-718`): `session_mode = getenv("GNOME_SHELL_SESSION_MODE")`, poi `meta_context_configure()` applica `--mode`
(la riga di comando vince), se NULL ⇒ `gdm` (con `--gdm-mode`) oppure `user`. Uguale in 48 (`main.c:616-632`).
Prodotto virtuale della cattura: `"Virtual remote monitor"` (50: `meta-screen-cast-virtual-stream-src.c:723, 879`; 48: `:608`) — la stringa che `session.h:420-435` descrive è invariata;
novità 50: la sorgente gestisce `mode_infos`/`preferred_scale` e `ScreenCast` accetta una proprietà `"modes"` (agente 4).
`gnome-shell` 50 in headless **non** inibisce l'accesso remoto: `js/ui/main.js:145-153` fa `inhibit_remote_access()` solo `if (!global.backend.is_headless())` — identico a 48; è ciò su cui contano i blocchi di lockdown in dconf.
Un test reale (nel contenitore, bus di sessione volatile, nessuna cartella REMOTIX): `gnome-shell --headless --no-x11 --mode=ubuntu` parte come compositor Wayland, poi cade
per mancanza del bus di sistema (`timeLimitsManager.js`): atteso in un contenitore nudo. Log: `/media/REMOTIX-UBUNTU/studio/1/gs-A.log`.

`org.gnome.Mutter.DisplayConfig.GetCurrentState`: firma identica in 48.7 e 50.1 (`a((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv}`, `diff` dei due XML: cambiano solo `SetLuminance`/`ResetLuminance` e campi di proprietà) ⇒ `TYPE_STATE` (`DEB 145`) resta valido.
Mutter non ha file di attivazione D-Bus per `org.gnome.Mutter.DisplayConfig` fra i pacchetti verificati (nessun `.service` che lo nomini): `ask_mutter()` usa comunque `NameHasOwner` + `NO_AUTO_START` (`DEB 233-277`), quindi non dipende dall'attivazione.
Chiavi dconf che REMOTIX blocca (`DEB 1620-1647`): tutte presenti negli schemi di 50 [V] (`switch-to-session-1…12` in `org.gnome.mutter.wayland.keybindings`, `always-show-log-out`, `disable-user-switching`, `disable-lock-screen`, `sleep-inactive-{ac,battery}-type`, `idle-delay`, `lock-enabled`, `input-sources`).

---------------------------------------------------------------------------------------------------------------------------------

## 6. L'ambiente di un login locale su Ubuntu GNOME 50 e quello che REMOTIX dà (D-153)

- **GDM 50** (`daemon/gdm-session.c:2838-2860` `set_up_session_environment`): imposta `GDMSESSION`, `DESKTOP_SESSION`, `XDG_SESSION_DESKTOP` = nome della sessione (`ubuntu`), `XDG_CURRENT_DESKTOP` = `DesktopNames` (`ubuntu:GNOME`),
  `XDG_SESSION_TYPE=wayland` (`send_session_type`, `2889`); `gdm-session-worker.c:1463` imposta `SHELL` dal passwd. Fonde l'ambiente del gestore utente (`gdm-wayland-session.c:325-343`).
- Con `SHELL` valida, **gnome-session 50 si rilancia in login shell** ⇒ legge `/etc/profile`, `/etc/profile.d/*` e `~/.profile`. Fra questi `/etc/profile.d/xdg_dirs_desktop_session.sh` (pacchetto `gnome-session-common`):
  con `DESKTOP_SESSION` non vuoto antepone `/etc/xdg/xdg-$DESKTOP_SESSION` a `XDG_CONFIG_DIRS` e, se la sessione non è `gnome`, `/usr/share/$DESKTOP_SESSION` a `XDG_DATA_DIRS`.
  Per `ubuntu`: `/usr/share/ubuntu/applications/{gnome-initial-setup,info,texdoctk}.desktop` (pacchetto `ubuntu-settings`; nascondono voci) esiste; `/etc/xdg/xdg-ubuntu` no [V].
  (`/etc/X11/Xsession.d/60x11-common_xdg_path` di `x11-common` fa lo stesso; `gdm3` esegue `Xsession.d` con la patch `debian/run_xsession.d.patch`: vedi `OLD DECISIONS.md` §10.54.)
- REMOTIX: `SHELL=` vuoto ⇒ **nessun re-exec, nessun profile** ⇒ la sessione remota non ha `/usr/share/ubuntu` in `XDG_DATA_DIRS`. DEB oggi non lo aggiunge perché `local_session()` è vuoto (`DEB 2270-2289`); il vecchio albero lo faceva (OLD `2274-2379`).
  Effetto atteso [S]: compaiono voci che un login locale Ubuntu nasconde (assistente di primo avvio). La prova su Ubuntu GNOME del 1.5.x (14 nov) è alla base di D-153.
- Nota di principio: in 48 il login locale non passa da `~/.profile` (refuso upstream, sopra); in 50 sì. REMOTIX continuerà a non farlo (CODER §4.5, ambiente composto) ⇒ le variabili che l'utente mette in `~/.profile`/`~/.bash_profile` mancano nella sessione GNOME remota, **diversamente** dal login locale. È una decisione da portare al proprietario (regola «uniformità»: remoto = login locale meno i danni).

---------------------------------------------------------------------------------------------------------------------------------

## 7. Decisioni e lezioni già scritte (OLD) — paragrafi

- `DECISIONS.md` §10.20 (righe 6086-6100), **D8**: «l'utente vede il desktop originale di Ubuntu»: sessione `ubuntu`, la predefinita della distribuzione, niente `gnome-session` vanilla in più.
- `phases/17-the-installer.md` §5.1 (righe 281-304): «GNOME 50: il servizio della shell ha cambiato nome»; `--headless`/`--no-x11` presenti in mutter 50; `org.gnome.Shell@headless.service` non funziona (diventerebbe `--mode=headless`);
  falso verde del check; cura (`c1573ae`). Righe 1315-1345 (§11, 11.1): «GNOME 50 confermato… la cura funziona» su Ubuntu 26.04 (binario diagnostico); riga 1466 (`7583b76`): D8 completo con `--mode=%i`.
  Riga 1338 e 1490: sulle VM «con il binario diagnostico: PASS … Ubuntu 26.04 (GNOME 50, `@user` con `--headless`)» — quella riga dice `@user`; la 1466 corregge in `@ubuntu`.
- `phases/17-the-installer.md` §5.2 (righe 306-331): T2: chi sopravvive al riavvio del servizio; «sul desktop ripreso GNOME è prima ZERO MONITOR».
- `LESSONS.md` §1.22 (righe 927-940): **un drop-in systemd vince per NOME** (`zz-r` < `zz-s`): perciò il controllo «scritto non è in vigore»; riga 935 conferma `--headless --no-x11` e nessun monitor virtuale.
- `STUDIES.md` §gnome §3 (righe 740-799; 750-768): sessione senza monitor; `SHELL` vuoto (`gnome-session.in:3-14`: vedi correzione sopra); FIFO e attesa; `SessionOver` mai emesso.
- `assessment/gnome/ubuntu2604.md` (OLD): giro del 16 nov su `t17-ubuntu2604-gnome-intel`: **100 controlli verdi su 112**, sessione di default `/usr/libexec/gnome-session-service --session=ubuntu`, `gnome-session-init-worker ubuntu` (R-DE-011 VERDE);
  rossi: R-LOGIN-010/013 (utente inesistente 0x0E a 1,2 s contro 0x07 a 2,7 s: causa NSS `sss`, `rootside.c`), non pertinenti all'avvio. Nessun rosso sull'avvio di GNOME 50.
- `CHANGES-1.5.md` riga 349 (rara dconf profile rimasto, ~1 su 53) e 304 («GNOME recente… REMOTIX riconosce la fine della sessione anche senza segnale») — chiusura, agente 2.
- `phases/19-nvidia.md` righe 336, 448-503: GNOME 50.1 su Ubuntu 26.04 con NVIDIA; F-003 «chiude» intermittente 3/23 non risolto (cattura, agente 4).
- DEB `docs/PULIZIA-tranche1.md` voci 4-7 e `docs/INVENTARIO-non-debian.md` righe 32-35: l'inventario dice esplicitamente «`@ubuntu` handling… can be removed later» — oggi serve.

---------------------------------------------------------------------------------------------------------------------------------

## 8. Fatti che contraddicono il piano o gli studi precedenti

1. **PIANO.md** (passo 3a) dice che «il modo di avviare» GNOME «è cambiato»: vero, ma in modo più ampio del nome dell'unità: cambia il leader (`init-worker`), il bersaglio avviato
   (`gnome-session@<sessione>.target`), e c'è il nuovo controllo «sessione grafica già attiva» (§4). Il codice Debian su Ubuntu **non parte** (non è «solo da ritoccare»).
2. **PULIZIA voce 5** («il risultato non cambia») è vera su Debian ma **falsa su Ubuntu** se sono presenti sia `ubuntu.desktop` sia `gnome.desktop`: il codice Debian sceglie `gnome`, D8 vuole `ubuntu`.
3. **OLD `phases/17` §5.1 righe 296-304** («`--headless --no-x11` senza `--mode=%i`») è superata dal codice finale del vecchio albero (con `--mode=%i`).
4. **`STUDIES.md` §gnome §3.1 / `session.c:2735-2740`**: «gnome-session.in:3-14 si rilancia in login shell» è vero per gnome-session 50 (C, `XDG_SESSION_TYPE=wayland`), mentre nel `gnome-session.in` upstream 48.0 la condizione è `xwayland` (refuso) e non scattava mai [W, Debian potrebbe averlo corretto: non verificato]. `SHELL=` vuoto resta la cura giusta, ora anche necessaria.
5. **`session.c:2722-2729`** (commento): «`ConditionEnvironment=XDG_SESSION_TYPE=wayland`… senza, il compositore non parte AFFATTO — sessione monca e nessuna riga»: in 50 è `AssertEnvironment`: senza la variabile il lavoro **fallisce**, `OnFailure=gnome-session-shutdown.target` e la sessione si smonta subito (fallimento rumoroso, non silenzioso).
6. **Il guasto A1 del registro** (`REGISTRO-problemi.md` righe 15-27, «il desktop locale… trovava `gnome-session-wayland@gnome.target` ancora attivo («Session manager already running!») e moriva in 0,4 s», `rootside.c:1757-1759`) nasce da nomi di 48: su Ubuntu il messaggio sarà «A graphical session is already running!» e il bersaglio `gnome-session@ubuntu.target`. Il meccanismo è lo stesso, ma 50 lo rende **esplicito e più largo** (qualunque sessione grafica, non solo GNOME).

---------------------------------------------------------------------------------------------------------------------------------

## 9. Problemi da affrontare

Peso: piccolo (< mezza giornata, poche righe), medio, grande. «Cura nota» = esiste codice che ha già funzionato su Ubuntu 26.04 nel vecchio albero.

1. **Unità della shell: template + istanza per sessione.** `unit_shell()` (`DEB session.c:2863-2882`), `session.h:107-112`.
   Su Ubuntu il codice attuale non riconosce l'unità e blocca la nascita. Va reintrodotto il ramo template: `FragmentPath` di `@wayland` che finisce in `@.service` ⇒ si legge `Requires` di
   `gnome-session@<gnome_session()->name>.target` e si prende l'istanza `org.gnome.Shell@…​.service`; costante `SESSION_UNIT_SHELL_MODEL`; mai la cartella del template (si applicherebbe anche alla shell di GDM, `@gdm`).
   **Peso medio** (è il cuore; poco codice ma va provato). **Cura nota: sì** — `OLD src/session.c:2966-3009`, `OLD src/session.h:107-130`, `DECISIONS` §10.20. Nota di progetto: il codice Ubuntu non ha più bisogno del ramo `@wayland`
   (GNOME 48): si può semplificare a «template o errore dichiarato», ma l'uniformità col codice Debian suggerisce di tenere la forma vecchia.
2. **Drop-in con `--mode=%i`.** `DEB session.c:3098-3104`. Riga: `ExecStart=%s --headless --no-x11 --mode=%i`; `expected` resta `--headless --no-x11` (la sottostringa si trova ancora nell'`ExecStart` espanso, dove `%i` è già `ubuntu`).
   Senza: la shell `@ubuntu` parte in modalità `user` (niente dock, colori Adwaita). **Peso piccolo.** **Cura nota: sì** — `OLD session.c:3226-3234`. Da non dimenticare: il controllo `--virtual-monitor` assente resta utile.
3. **Pulizia delle istanze.** `DEB session.c:3994-4015` è già generica (`org.gnome.Shell@*.service.d`, solo il nostro file). Basta (facoltativo) rimettere la guardia sul template (`OLD 4133-4136`) per chiarezza. `rootside.c:1745` e il `postrm`/`prerm` non nominano `@wayland`. **Peso piccolo (quasi zero).** Cura nota: sì.
4. **Scelta della sessione con `ubuntu` e `gnome` insieme.** `DEB session.c:914-923`. Reintrodurre il criterio «nome = `ID` di os-release» (`OLD session.c:871, 916-920`) prima di «`gnome`». Su Ubuntu standard c'è solo `ubuntu` (nessun effetto); con `gnome-session` installato dà `ubuntu` come vuole D8. **Peso piccolo.** **Cura nota: sì.**
   (Per Kubuntu/Xubuntu/Lubuntu `ubuntu-session` può comparire come dipendenza: il riconoscimento del sapore è dell'agente 3/6.)
5. **Ambiente «come un login locale» per la sessione `ubuntu` (D-153).** `DEB session.c:2270-2289` (`local_session()` vuoto), `2416-2432`. Servono almeno `DESKTOP_SESSION=ubuntu` e `/usr/share/ubuntu` davanti a `XDG_DATA_DIRS` (la data dir con voci nascoste), alla base del gestore utente; `/etc/xdg/xdg-ubuntu` non esiste (nessun effetto).
   **Peso medio** (condiviso con le sessioni degli altri sapori: XFCE/LXQt hanno `xdg-xubuntu`, `xdg-lubuntu`; piano 3c, stesso file). **Cura nota: sì** — `OLD session.c:2274-2379`, `DECISIONS` §10.54; il vecchio codice dipende da `xsession_d_applies()` (presenza di `60x11-common_xdg_path` + non sddm): per GNOME su gdm3 vale. In 50 il vero meccanismo di un login locale è `/etc/profile.d/xdg_dirs_desktop_session.sh` (§6); l'effetto sulle liste è lo stesso.
6. **Guardia nuova di gnome-session 50: `graphical-session.target` attivo ⇒ il leader abortisce.** `inactive_unit()` (`DEB session.c:3544-3619`) guarda solo `gnome-session-manager@<s>.service` e `gnome-session-restart-dbus.service`. Va aggiunto `graphical-session.target` (stesso `unit_stopped()`), altrimenti una nascita troppo vicina alla fine della sessione precedente fa partire un `gnome-session` che muore subito
   (`start()` ritorna TRUE comunque: `3497-3504`; il freno `BIRTH_REIN_MS`=12 s, `child.c:5489`, farebbe aspettare invano 12 s). Va anche letto nel log di sessione («A graphical session is already running!»). **Peso piccolo.** **Cura nota: no** (nuova in 50).
7. **Convivenza locale/remoto (A1/A2 del registro) con i nomi nuovi.** Il commento di `rootside.c:1745-1765` e di `REGISTRO-problemi.md` A1 nomina `gnome-session-wayland@…`; su 50 il guasto locale è «A graphical session is already running!». Il rimedio (PAM, desktop remoto chiuso prima del login locale) resta; la schermata di accesso di GNOME 50 (`loginDialog.js:1374-1397` `_findConflictingSession`: stessa logica `active`/`online`) resta uguale a 48.
   Vale la prova «remoto aperto → riavvio del servizio → accesso locale» (registro A1, «su una distribuzione nuova»). **Peso piccolo** (solo commenti/log + prova). Cura nota: no, ma il comportamento è lo stesso.
8. **Variabili che il leader 50 immette nel gestore utente e non sono in `OUR_VARIABLES`.** `GNOME_DESKTOP_SESSION_ID`, `QT_IM_MODULES` (nuova, plurale); `QT_IM_MODULE`/`XMODIFIERS` c'erano già in 48. `OUR_VARIABLES` (`DEB 3843`) non le ripristina a fine sessione. Sono costanti (non ci sono nostri percorsi) e uguali a ciò che un login locale GNOME imposta, quindi probabilmente innocue [S]; da decidere se aggiungerle. **Peso piccolo.** Cura nota: no.
9. **Commenti e diagnostica che nominano cose di 48.** `session.c:2722-2729` (`ConditionEnvironment`), `session.h:2-8` (storia), `session.c:2741` e `rediscover.h:27` (`gnome-session-binary`, ora `gnome-session-init-worker`/`gnome-session-service`), `session.c:3611-3617` («`gnome-session-manager@…` e `restart-dbus` hanno ancora questi nomi»: confermato in 50.1).
   Il codice non nomina `gnome-session-binary` in alcun confronto ⇒ nessun cambio funzionale. **Peso piccolo.** Cura: n/a.
10. **Login shell e `~/.profile`.** `SHELL=` vuoto (`DEB 2744`) resta obbligatorio, ora più che mai (50 fa davvero il re-exec). Decisione per il proprietario: la sessione GNOME remota non vedrà ciò che l'utente mette in `~/.profile` (il login locale 50 sì). **Peso piccolo** (nessun codice; documentare). Cura: n/a.
11. **Tempi.** `WAIT_STARTUP_MS 40000`, `BIRTH_REIN_MS 12000`: la sessione `ubuntu` carica più servizi (`gnome-software`, `evolution-alarm-notify`, estensioni, `localsearch`, snapd-prompting); nel vecchio albero la nascita non dava rossi (`assessment/gnome/ubuntu2604.md`), ma con GNOME 50.1 e `systemd 259` non è misurata sul codice 1.0.0. **Peso piccolo** (misura). Cura: n/a.
12. **Dipendenze del `.deb` su Ubuntu** (`debian/control:90` nomina D8). Niente da cambiare per l'avvio: `ubuntu-desktop` porta `ubuntu-session`, `gnome-shell`, `gnome-session-bin`, `gnome-session-common` (ma non `gnome-session`). `recognize_desktop()` vuole `gnome-session` (binario) e `gnome-shell` nel PATH: ci sono. **Peso piccolo/nessuno.** Cura: n/a.

---------------------------------------------------------------------------------------------------------------------------------

## 10. Che cosa non si può sapere senza provare

- **Che il template funzioni dal vivo col nostro drop-in:** `systemd` istanzia `org.gnome.Shell@ubuntu.service` dal template e applica `…/org.gnome.Shell@ubuntu.service.d/zz-remotix-monitor.conf` da `user.control`;
  `systemctl --user show -p ExecStart --value` deve restituire `--headless --no-x11 --mode=ubuntu` (con `%i` espanso). Nel contenitore non c'è un user manager: non ho potuto dimostrarlo qui (`systemctl cat`/`analyze` non accettano `--root`). Nel vecchio albero era `[M]` il 30 set 2026 (`phases/17` riga 1466) con GNOME 50 su 26.04.
- **L'output di `systemctl --user show -p Requires --value gnome-session@ubuntu.target`:** dai file ci si aspetta `…org.gnome.Shell@ubuntu.service`, `gnome-session-manager@ubuntu.service`, `gnome-session-services.target`, `gnome-session-initialized.target`, `gnome-session.target` (il `@.` del template diventa l'istanza). Da confermare con il gestore vero.
- **Il tempo reale di nascita** della sessione `ubuntu` headless con le estensioni (dock, ding, appindicators…) e se `GetCurrentState` risponde prima o dopo `gnome-session-initialized.target`.
- **Che `GetCurrentState` risponda con zero monitor sulla 50.1 in headless:** il codice di mutter lo permette (`needs_outputs=false`, identico a 48), e il giro del 16 nov sul 1.5.x lo ha mostrato verde; non rimisurato sul 1.0.0.
- **Comportamento di `gnome-session-init-worker` come figlio di `setsid --fork sh -c exec`, con `SHELL=` vuoto e senza `XDG_SESSION_ID`, sotto la sessione logind del servizio PAM `remotix`** (il leader è dentro lo scope logind, come GDM): non si può leggere dai sorgenti con certezza; il vecchio albero lo provò su 26.04.
- **L'effetto di `/usr/share/ubuntu` mancante** (assistente di primo avvio che ricompare?) senza D-153: solo supposizione [S].
- **Che l'abort «A graphical session is already running!» si veda nel log di sessione** nel punto in cui REMOTIX lo cerca, e dopo quanto il guardiano `inactive_unit()` oggi lo eviterebbe da solo.
- **Se Debian 13 avesse corretto il refuso `xwayland`** nel `gnome-session.in` 48 (non ho il pacchetto Debian qui).

---------------------------------------------------------------------------------------------------------------------------------

## 11. Prove consigliate (da fare solo su decisione del proprietario)

1. **Macchina di prova Ubuntu (gusto GNOME), da pulita:** con il codice portato (problemi 1, 2, 4), nascita della sessione da un accesso; controlli, in ordine:
   `systemctl --user show -p ExecStart --value org.gnome.Shell@ubuntu.service` (deve contenere `--headless --no-x11 --mode=ubuntu`); `systemctl --user show -p Requires --value gnome-session@ubuntu.target`;
   `systemctl --user show -p FragmentPath --value org.gnome.Shell@wayland.service` (deve finire in `@.service`); `ps` della shell (`gnome-shell --headless --no-x11 --mode=ubuntu`) e del leader (`gnome-session-init-worker ubuntu`);
   `GetCurrentState` a 0 monitor; poi, con un client, il monitor `Virtual remote monitor` e la barra/dock di Ubuntu.
2. **Stessa prova con `gnome-session` (vanilla) installato**: deve restare `ubuntu` (problema 4).
3. **Nascita subito dopo il logout** (come la prova di agosto «utente che esce e rientra»): verificare nel log di sessione assenza di «A graphical session is already running!» e che `inactive_unit()` (con `graphical-session.target` aggiunto) aspetti.
4. **Remoto aperto → riavvio del servizio → accesso locale** (registro A1) e **accesso locale con remoto aperto** (A2) su Ubuntu GNOME: leggere nel log di gnome-session il messaggio di 50.
5. **Ambiente:** confrontare `XDG_DATA_DIRS`, `XDG_CONFIG_DIRS`, `DESKTOP_SESSION`, `XDG_CURRENT_DESKTOP`, `XDG_SESSION_DESKTOP` letti da `/proc/<gnome-shell>/environ` in un login locale (GDM) e in una sessione REMOTIX; vedere se compare l'assistente di primo avvio.
6. **Fine sessione:** dopo il logout, `systemctl --user show-environment` non deve contenere `DCONF_PROFILE`, `XDG_*` nostri; vedere se restano `GNOME_DESKTOP_SESSION_ID`/`QT_IM_MODULES` (problema 8).
7. **Controllo di regressione su Debian** (se il codice Debian condiviso cambia): `@wayland` deve continuare a essere riconosciuto (la forma vecchia del ramo).
