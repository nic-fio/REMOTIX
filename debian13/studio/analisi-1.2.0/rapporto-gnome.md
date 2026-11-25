# Rapporto di analisi GNOME (Debian 13, GNOME 48.7, gdm3 48.0-2) — REMOTIX 1.2.0

Legenda: [V] verificato (codice o VM `gnome`), [D] dedotto. Nessun file del repository toccato; VM `gnome` accesa solo in
modo `virtuale`, ora spenta. Nessun posto-turno preso (regola cambiata a metà lavoro).

Versioni misurate nella VM [V]: gnome-shell 48.7, mutter 48.7, gdm3 48.0-2, gnome-session 48.0-1+deb13u1, dconf 0.40.0-5
(`dconf-cli`, `dconf-service`), accountsservice 23.13.9-7, fwupd 2.0.20-1~deb13u1, gnome-software 48.3-2 (installato e
in autostart), packagekit 1.3.1, libpam-systemd 257.13.

## Scoperte generali importanti (valgono per tutte le voci sotto)
1. **Lo studio sbaglia su Debian e dconf**: `debian13/src/session.c` HA già il database dconf di sessione a tre strati
   (profilo in `$XDG_RUNTIME_DIR/remotix/dconf/profile`, `file-db:locks.db` compilato a runtime con `dconf compile`, `shm`
   in RAM, `session_dconf_prepare/neutralise`, `DCONF_KEYS`, `dconf-cli` già in `Recommends`, `control:100`). È il modello
   che Ubuntu ha ora declassato a «ripiego». Quello che a Debian manca è solo il livello superiore di Ubuntu: database di
   SISTEMA `/etc/dconf/db/remotix` + profilo in `$XDG_RUNTIME_DIR/dconf/profile` + `user-db:remotix`.
2. **`session.c` di Ubuntu/Fedora NON si può copiare intero**: ha buttato via il supporto alla Shell di GNOME 48
   (`SESSION_UNIT_SHELL_48 = org.gnome.Shell@wayland.service` esiste solo in `debian13/src/session.h:112`; Ubuntu/Fedora
   hanno solo `SESSION_UNIT_SHELL_MODEL = org.gnome.Shell@.service`, GNOME 50), l'`AssertEnvironment` (GNOME 50) contro
   `ConditionEnvironment` (48), e `graphical-session.target` fra le unità da aspettare. Ogni porting da quel file va fatto
   a blocchi, tenendo i rami GNOME 48 di Debian. Debian→Ubuntu `session.c`: 1889 righe di differenza, quasi tutte
   (dconf, `session_life` a tre risposte, KDE, GNOME 50, PATH di PAM); ho guardato gli hunk GNOME: nessun altro cambio utile.
3. Fuori elenco: **il PATH** della sessione remota su Debian è fisso `/usr/local/bin:/usr/bin:/bin` (`child.c:1781`);
   un accesso locale GNOME ha `/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games` [V, `/proc/<gnome-shell>/environ`;
   viene da gdm/`ENV_PATH` di login.defs]. `/etc/environment` su Debian è VUOTO, quindi il `child_path_ok()` di Ubuntu
   (prende il PATH dato da `pam_env`) su Debian ripiegherebbe sullo stesso valore fisso: non cambia nulla. Differenza
   minima (mancano solo i giochi), da decidere se interessa.
4. Fuori elenco: `input_dropped()` Debian (`input.c:1507`: `in && !in->wlr && in->dropped`) differisce da Ubuntu/Fedora
   (che controllano anche `wlr_input_dropped(in->wlr)`): riguarda XFCE/LXQt, non GNOME (lo segnalo agli altri).

---
## A4 — primo movimento del puntatore inviato due volte
1. Il primo `motion_absolute` dopo la (ri)partenza del dispositivo libei viene mandato due volte (difetto di mutter 51 misurato
   su Fedora: il primo clic cade sul bordo).
2. Debian oggi: `input.c:1931` invia il movimento una volta; nessun `pointer_primed` [V]. Differenza Ubuntu→Fedora in
   `input.c`: solo campo `pointer_primed` (riga 257 Fedora), azzeramento in `EI_EVENT_DEVICE_RESUMED` (1330), blocco
   `if (!in->pointer_primed)` prima di `ei_device_pointer_motion_absolute` (1940-1951): 14 righe. Debian↔Ubuntu `input.c`
   differisce solo nei commenti dconf e in `input_dropped`, quindi la patch si applica senza adattamenti.
3. **Convivenza con `touch_announce_pointer` (page.html:12361)**: sono DUE rimedi diversi che si sommano, non uno al posto
   dell'altro [V, codice]. `touch_announce_pointer` è nel client, solo layout touch, manda UN movimento
   POINTER per sessione/canvas (`touch_send`, righe 12377) perché il server conosca la posizione che la pagina disegna.
   Il raddoppio è nel server, vale per qualunque primo movimento (anche mouse), cioè per la risposta lato mutter. `page.html` è
   uguale in tutti e tre gli alberi per quella funzione (Ubuntu 12364, Fedora presente): Fedora li ha entrambi. Il «residuo
   1 caso su 13» di Debian (`debian13/PIANO.md:90`: primo tocco sul punto iniziale se la posizione arriva prima che Mutter sia
   pronto) è esattamente il sintomo che il raddoppio cura [D].
4. Verdetto: **PORTABILE COSÌ** (piccolo, 14 righe, da `fedora45/src/input.c`). Se serva davvero su mutter 48: **DA PROVARE COL
   PRODOTTO** (`check-multiuser` un utente e `check-phone tap-click-portrait`, più volte: il difetto era saltuario).
5. Rischi: nessuno per l'utente (ripetere la stessa posizione è innocuo, il commento di Fedora lo dichiara; «da togliere quando
   mutter è corretto»). Un movimento in più al primo invio.
6. Misura: nessuna possibile senza il prodotto.

## A8 — regola polkit fwupd `refresh-remote`
1. Concede alle sessioni REMOTIX l'azione che GNOME Software chiede all'avvio per aggiornare i metadati firmware.
2. Debian oggi: `remotix-remote-sessions.rules:73-79` ha solo 3 azioni di refresh (Flatpak metadata/appstream, packagekit sources-refresh)
   + 2 «di macchina» (NetworkManager, Flatpak modify-repo). La riga fwupd esiste solo in Fedora (diff Ubuntu↔Fedora); Debian↔Ubuntu: regole uguali.
3. **MISURATO nella VM** [V]: `pkaction | grep fwupd` con fwupd 2.0.20 elenca 25 azioni (clean-remote, device-*, downgrade-*,
   emulation-*, modify-config, modify-remote, update-*, verify-update…) e **`org.freedesktop.fwupd.refresh-remote` NON ESISTE**
   (`pkaction --verbose --action-id org.freedesktop.fwupd.refresh-remote`: «No action with action id»; `grep -i refresh
   org.freedesktop.fwupd.policy`: niente). Le azioni vicine: `modify-remote` e `clean-remote` hanno `implicit active =
   auth_admin_keep` (chi siede al PC deve comunque inserire la password) e `implicit any = auth_admin`.
   gnome-software 48.3 c'è ed è in autostart (`/etc/xdg/autostart/org.gnome.Software.desktop`); nella sessione locale di prova
   è partito (`gnome-software` in `ps`, giornale: solo «failed to get featured apps»), nessuna finestra di password vista [V].
4. Verdetto: **NON PORTABILE COSÌ / NON SERVE su Debian 13**: l'azione non esiste in fwupd 2.0.20, quindi la regola non avrebbe
   effetto. Aggiungerla è innocua (una regola per un'azione inesistente non si attiva mai) ma sarebbe codice morto. Resta un
   punto **DA PROVARE COL PRODOTTO**: sessione GNOME remota con gnome-software, guardare se compare una finestra polkit per un'azione
   fwupd diversa (`modify-remote` sarebbe uguale per chi è seduto, quindi non sarebbe un danno di REMOTIX). Nota: `remotix-polkit-seated`
   non cambia fra gli alberi (diff vuoto).
5. Rischi: nessuno se non si fa nulla.
6. Misure: vedi sopra (pkaction, policy, autostart, ps).

## U1 e U13 — database dconf di sistema `/etc/dconf/db/remotix`
1. I blocchi della sessione GNOME remota (niente cambio utente, niente blocco schermo, niente sospensione, tasti VT, layout,
   «Log Out» sempre visibile, ecc.) vivono in un database dconf di SISTEMA, compilato dal pacchetto, invece che in uno
   compilato a ogni avvio di sessione; il profilo sta in `$XDG_RUNTIME_DIR/dconf/profile`, senza `DCONF_PROFILE` nell'ambiente.
   U13 = una riga in `rootside.c` (`session_dconf_system_db_ensure()`, alla riga 3344 di Ubuntu) che riallinea il database se manca o è vecchio.
2. Debian oggi [V]: modello «ripiego» di Ubuntu: `session.c:1561-1604` (scatola), `DCONF_KEYS` 1624, `dconf_compile_locks` 1673, profilo
   `$XDG_RUNTIME_DIR/remotix/dconf/profile` (1720), `session_dconf_prepare` 1868, `session_dconf_neutralise` 1806,
   `DCONF_PROFILE` esportato alla Shell (`session.c:2745-2752`) e rimosso dal manager (`OUR_VARIABLES`), cintura in `child.c`
   (8688, 9861, 9940, 10222, 12434); `input.c:2233-2304` scrive il layout nel `shm`. Pacchetto: `dconf-cli` in Recommends
   (`control:100`). **Mancano**: `session_dconf_keyfiles_write`/`--dconf-keyfiles` (main.c), `session_dconf_system_db_ensure`,
   profilo runtime a due modalità (`dconf_runtime_mode`, `dconf_admin_profile`, `dconf_profile_file`, `session_dconf_object()` →
   `Writer/remotix`), regola `debian/rules` (`remotix --dconf-keyfiles …/remotix.d`), `postinst` (compila), `postrm` (toglie
   `/etc/dconf/db/remotix` e `~/.config/dconf/remotix`).
3. Che cosa SERVE su Debian: il motivo vero di Ubuntu (programmi Flutter e snap che non digeriscono `file-db`/`DCONF_PROFILE`,
   registro C5 di Ubuntu) **non esiste su Debian 13** [D, verificato: nessun snap; gnome-software 48 è GTK; nella VM nessun
   programma Flutter]. Il ripiego di Debian funziona (è quello che ha girato nella 1.0.x). I vantaggi della variante di sistema sono:
   nessuna dipendenza da un `dconf compile` a ogni nascita della sessione; modifiche del layout in `user-db:remotix` su disco
   (`~/.config/dconf/remotix`, che poi va tolto al purge) invece che in `shm` (RAM); un solo elenco di chiavi con le due
   forme. Gli svantaggi: più codice (~700 righe nel solo `session.c`, secondo il diff Debian↔Ubuntu 1557-2290), un file in `/etc`
   fuori dalla lista dei file del pacchetto (da pulire al purge), più cose da provare.
4. Misure sul dconf 0.40.0 di Debian [V]: `libdconf.so.1` contiene `dconf/profile`, `DCONF_PROFILE`, `user-db`, `service-db`,
   `system-db`, `file-db`, `/run/dconf/user` → il profilo di runtime e i tipi di sorgente esistono; `dconf compile` c'è
   (`dconf-cli` è installato di serie nelle immagini; il comando `dconf --version` non esiste in 0.40, non è un difetto).
   `/etc/dconf/profile/user` non esiste, c'è solo il profilo `ibus` con `/etc/dconf/db/ibus`: nessun conflitto di nomi. La cartella
   `/run/user/1000/dconf/` esiste già (contiene `user`, la memoria condivisa del motore): il file `profile` di Ubuntu ci convive.
   Che dconf **0.40** legga davvero `$XDG_RUNTIME_DIR/dconf/profile` NON l'ho potuto provare senza il prodotto (Ubuntu lo ha misurato
   su 0.49): **DA PROVARE COL PRODOTTO** (blocco di `disable-user-switching` e simili con profilo runtime + `system-db:remotix`).
   Il codice di Debian (`dconf_base_profile`, `session.c:1738-1760`) già elenca tra i candidati `g_get_user_runtime_dir()/dconf/profile`,
   scritto dalla lettura dei sorgenti dconf 0.40 [D].
5. **Quale variante per Debian: quella di Ubuntu** (compilazione accanto al database con nome temporaneo `remotix.new.<pid>` e
   `rename`, `session.c:1834-1895` di Ubuntu; `postinst` e `postrm` di Ubuntu). La variante di Fedora (compilare in
   `/run/remotix/dconf-compile.tmp`, nomi fissi `remotix.new`/`remotix`) esiste solo per l'etichettatura SELinux (F24); Debian non ha
   SELinux attivo (le righe `pam_selinux` ci sono ma senza criterio) né AppArmor sul lato root (solo sulla rete). Il diff Ubuntu↔Fedora
   di quella funzione è di ~60 righe, tutto SELinux.
6. Verdetto U1 e U13: **PORTABILE CON ADATTAMENTO — ma NON necessario per correttezza su Debian 13**; da decidere dal proprietario se
   lo vuole per uniformità («allineare il più possibile a Fedora»). Dimensione: grande (~800 righe fra `session.c`, `main.c`, `rootside.h`
   1 riga, `input.c` commenti, + `debian/rules`, `postinst`, `postrm`, 3 punti). Adattamenti: (a) copiare SOLO le funzioni dconf, non il
   file; (b) NON copiare `{"ubuntu-lock-on-suspend"}` (chiave di Ubuntu, su Debian lo schema non esiste: il blocco sarebbe inerte ma
   inutile); (c) tenere la chiave `scaling-factor` solo se si fa anche U4; (d) `dconf-cli` resta Recommends (il ripiego c'è comunque);
   (e) U13 dipende da U1 (stessa porzione di codice); (f) comportamento per l'utente: nessuna differenza visibile; cambiano dove si
   scrive il layout (disco al posto di RAM) e un file nuovo in `/etc/dconf/db` creato dal pacchetto (aggiornamento a caldo: la sessione
   remota già nata con il vecchio modello non vede il cambio di layout, dichiarato nel codice di Ubuntu).
   Alternativa più piccola: **non portare U1/U13** e tenere il ripiego, aggiungendo solo la chiave `scaling-factor` a `DCONF_KEYS` (se U4).
7. Misure: dpkg/apt, `ls /etc/dconf`, `strings libdconf`, dump profilo; resta da provare col prodotto (vedi 4).

## U4 — scala di GNOME 50 (`mutter_scale_to_one`)
1. Se l'utente ha una scala 200% (impostazioni o `monitors.xml`), la sessione remota la ignora riportando UN monitor a scala 1 con una
   chiamata temporanea di `ApplyMonitorsConfig` (metodo 1), invece di rifiutare il palco con la pagina nera.
2. Debian oggi: `mutter.c:395` registra solo il rifiuto («cura: `gsettings set … scaling-factor 0`»), `child.c:9079-9113` rifiuta
   la scena (guardia 2) e ritenta in loop; niente `mutter_scale_to_one`, niente `fatal`/0x0E, niente chiave `scaling-factor` bloccata.
   Debian↔Ubuntu `mutter.c`: 136 righe (di cui ~130 la funzione nuova, 1022→1152), `mutter.h`: +13 (dichiarazione); Ubuntu↔Fedora: identici.
3. Misure su mutter 48.7 nella VM [V] (sessione locale di `prova`, `GetCurrentState`): un monitor logico `Virtual-1`, scala 1.0,
   `layout-mode` = 1 (logical), **`supports-changing-layout-mode` = true**; il monitor offre le scale 1.0, 1.25, 1.51, 1.74, 2.0,
   2.5, 2.76…; `libmutter-16.so.0` contiene `ui-scaling-factor`, `scale-monitor-framebuffer`, `global-scaling-factor-changed`: ha
   quindi la lettura del `scaling-factor` e la scala intera. `org.gnome.desktop.interface scaling-factor` = 0 di serie, `~/.config/monitors.xml` assente.
   Non ho cambiato la scala nella VM (regola «solo letture»): la prova «scaling-factor 2 → il palco rifiuta» e «la correzione riporta a 1»
   resta **DA PROVARE COL PRODOTTO**. La guardia in `child.c` di Debian nasce da una misura reale di REMOTIX con `scaling-factor`=2
   (commento `child.c:9150-9155`), ma non so su quale GNOME.
4. Verdetto: **PORTABILE COSÌ** (le chiamate D-Bus `GetCurrentState`/`ApplyMonitorsConfig` sono le stesse in mutter 48: l'interfaccia
   ha `layout-mode` e `supports-changing-layout-mode`, che la funzione usa). Non fa danni su mutter 48 perché scatta solo se la scala
   LETTA non è 1 e fallisce in sicurezza (un tentativo, poi il rifiuto di prima). Utile: tappa un buco reale (utente con 200% resta
   davanti a una pagina nera). Dipende da: `child.c` (blocco 9167-9184 e i campi `fatal`/`on_stage_refused`/`scale_refused`: 0x0E e
   chiusura della sessione al posto del loop infinito — ~150 righe, vedi `child.c` Debian↔Ubuntu 398-405, 721-729, 3363-3420, 9087-9222,
   10520-10539) e, per la chiave `scaling-factor` bloccata, da U1/U13 (o dalla sola riga in `DCONF_KEYS`). Dimensione: media (130 righe
   `mutter.c` + 150 righe `child.c` + 1 riga chiave).
5. Rischi/cambi di comportamento (da approvare): (i) chi ha 200% prima vedeva una pagina nera (e un `gsettings set` come rimedio); ora
   vede il desktop a scala 1, e se non riesce la sessione si chiude con il messaggio 0x0E invece di restare in attesa — cambia il
   comportamento nel caso di rifiuto (la sessione si chiude, nulla resta vivo). (ii) La correzione è temporanea e non scrive `monitors.xml`.
6. Misure: vedi 3.

## E1 — GNOME senza «ultima difesa» nella chiusura per accesso locale
1. Se la chiusura gentile del desktop remoto non finisce quando un utente fa l'accesso locale, su KDE c'è una rete di sicurezza (il lato
   root ferma il gestore dello schermo, `kdehost_stop`); su GNOME no.
2. Com'è oggi la chiusura GNOME, identica nei tre alberi [V] (`session.c` Debian↔Ubuntu↔Fedora nel blocco `really_terminate()`/`exit_gnome()`
   uguale; Ubuntu↔Fedora cambia solo KDE): `really_terminate()` (`session.c:4440`): `exit_gnome(1)` = `org.gnome.SessionManager.Logout(1)` +
   `wait_until_done()` (10 s, `WAIT_EXIT_MS`, 108); poi, se `force_refused()` non lo vieta (genitore sparito), `exit_gnome(2)` = Logout(2)
   «forzato» + altri 10 s. Il lato root tiene il login locale fermo `PL_GRACE_MS` = 13 s (`rootside.c:2428`, uguale nei 3 alberi), poi
   conclude «l'ambito» (scope) seatless del remoto. Nessun `kdehost_stop` per GNOME (`child.c:9967`, solo KDE). La chiusura leggera
   `local_light_close` (`child.c:9921`) non tocca il gestore di sessione.
3. **Misurato nella VM** [V], sessione GNOME locale di `prova` con un inibitore di logout attivo (`gnome-session-inhibit --inhibit logout …`, che imita
   un programma con lavoro non salvato): `Logout(1)` NON chiude: la Shell mostra la finestra «Log Out prova — verrà disconnesso automaticamente
   tra 60 secondi» (schermo salvato) e dopo 8 s la Shell, `gnome-session-manager@gnome.service` e il resto sono ancora vivi. `Logout(2)`
   con la stessa situazione: la Shell dell'utente sparisce entro 0,5 s, `gnome-session-manager@gnome.service` e `graphical-session.target` vanno
   `inactive` (primo campione a 0,53 s). Quindi su GNOME 48 il caso peggiore è: 10 s di attesa + <1 s = ~10,5 s < 13 s: stesso margine di KDE (~10,9 s
   su 13 s misurato da Fedora), senza bisogno dell'ultima difesa. (Resta un processo orfano `sleep` dell'inibitore: è il mio test, non REMOTIX.)
4. Nota di struttura [V]: l'unità `org.gnome.Shell@wayland.service` ha `RefuseManualStop=on` e `RefuseManualStart=on`, `Restart=no`,
   `OnFailure=… gnome-session-shutdown.target`. Un'«ultima difesa» GNOME che facesse `StopUnit` sulla Shell verrebbe RIFIUTATA da systemd
   (come ha già fatto per i `Refuse…` di altre unità); servirebbe un `kill` o fermare `gnome-session-shutdown.target`/`gnome-session-manager@gnome.service`. Un'altra ragione per non costruirla senza un guasto visto.
   `graphical-session.target` ha `StopWhenUnneeded=yes`; `gnome-session.target` `BindsTo=graphical-session.target`, `RefuseManualStop=yes`.
5. Verdetto: **NON SERVE su Debian 13** (per ora), coerente con la decisione 4 del `PIANO-1.2.0-debian-ubuntu.md` («GNOME resta senza ultima difesa»):
   eseguire P7 (terminale con programma in corso) e il caso «programma non salvato» su GNOME col prodotto, correggere solo se fallisce.
   **DA PROVARE COL PRODOTTO**: P7 su GNOME 48 (`check-prelocal.py`, P8 per GNOME è BLOCKED), compresa la variante «gnome-session che non risponde».
6. Misure: vedi 3. Struttura delle unità utente di una sessione GNOME locale [V, `systemctl --user list-units`]: `gnome-session-manager@gnome.service`
   (gestore), `org.gnome.Shell@wayland.service` (Slice `session.slice`, Type=notify), `gnome-session.target` (BindsTo `graphical-session.target`
   e `gnome-session-monitor.service`), `gnome-session-wayland@gnome.target`, `gnome-session-wayland.target`, `gnome-session-initialized.target`,
   `gnome-session-manager.target`, `gnome-session-pre.target`, `org.gnome.SettingsDaemon.*.target/service` (≈16), `org.gnome.Shell.target`,
   `graphical-session.target` e `graphical-session-pre.target`; `graphical-session.target` richiede `basic.target` e porta in dipendenza i servizi gvfs e i portali xdg.
   (Su GNOME 50 la Shell è `org.gnome.Shell@.service` istanziato.)

## A1 e A2 (e E4) — lingua del desktop remoto, `LC_*` e `LANGUAGE`
1. Il desktop remoto parte nella lingua scelta dall'utente nelle Impostazioni (AccountsService), altrimenti in quella di sistema; anche `LC_*` e
   `LANGUAGE` di sistema arrivano al desktop e vengono rimessi a posto a fine sessione.
2. Debian oggi [V]: **il desktop remoto è SEMPRE in `C.UTF-8` (inglese)**. Il figlio costruisce `envp[16]` senza `LANG` né `LC_*`
   (`child.c:1599`, 1783-1806: solo HOME, USER, LOGNAME, PATH, SHELL, XDG_RUNTIME_DIR, DBUS e `XDG_SESSION_ID` da PAM); `session.c:2790`
   mette `LANG=<local_utf8()>`, e `local_utf8()` (1342-1378) legge `g_getenv("LANG")` del figlio, che è vuoto: cade nel ripiego `C.UTF-8` e lo
   dichiara nel log. Anche lo stack PAM di Debian (`remotix.pam`) ha già la riga `pam_env.so envfile=/etc/default/locale`: il valore è nell'ambiente
   di PAM ma non viene raccolto. `OUR_VARIABLES` (`session.c:3843`) ha solo `LANG`, non `LC_*`/`LANGUAGE`.
3. Dove sta la lingua [V, VM]: di sistema in `/etc/default/locale` (nella VM: solo `LANG=en_US.UTF-8`; le locale generate sono tutte, incl. `it_IT.utf8`).
   Di utente: AccountsService, `/var/lib/AccountsService/users/<nome>` (cartella `root:root 0700`, quindi va letta DA ROOT prima del `setuid`, come fa
   Fedora). **Nella VM i file sono assenti** (anche dopo l'accesso grafico di `prova`): il D-Bus risponde `Language ""` e `Languages []`; il file nasce
   solo quando l'utente sceglie la lingua nelle Impostazioni. Accountsservice 23.13.9 **non ha** la proprietà `FormatsLocale` [V: `busctl introspect`]; il «formato»
   delle date/numeri di GNOME sta nel dconf dell'utente (`org.gnome.system.locale region`, vuoto) e arriva alla sessione da lì. La FORMA del valore scelto
   (`it_IT.UTF-8` o `it_IT`) non l'ho potuta misurare perché non ho cambiato la lingua dell'utente (sarebbe una modifica); [D] gnome-control-center scrive `it_IT.UTF-8`;
   il codice di Fedora accetta `Languages=`/`Language=`, qualunque forma purché di caratteri semplici, e `session.c` verifica comunque che il locale esista
   e sia UTF-8 (altrimenti `C.UTF-8`): quindi un `it_IT` senza codifica NON esiste come UTF-8 e ricadrebbe in `C.UTF-8` (E4: da provare, con
   `locale-gen`/langpack nelle immagini).
4. Sessione locale GNOME su Debian [V, `/proc/<gnome-shell>/environ`, `systemctl --user show-environment`]: `LANG=en_US.UTF-8` e basta; nessun `LANGUAGE`, nessun `LC_*`
   (il file di sistema ne ha zero); `GDM_LANG=en_US.UTF-8` nel manager utente; nessuna `LC_*` perché `/etc/default/locale` ne ha zero. Con `localectl set-locale LC_TIME=…`
   comparirebbero (Fedora lo misurò sul suo gdm; su Debian [D] vale lo stesso perché la riga `pam_env envfile=/etc/default/locale` è nel PAM di gdm: `gdm-password`).
5. accountsservice nelle quattro immagini [V/D]: GNOME: `gdm3 Depends: accountsservice` (installato). KDE: `plasma-desktop Depends: accountsservice`. XFCE:
   `lightdm Suggests: accountsservice`, `xfce4-session`/`xfce4` non lo richiedono. LXQt (sddm): `sddm`, `lxqt-session`, `lxqt-core` non lo richiedono. Quindi può mancare su XFCE
   e LXQt [D da apt-cache depends; per le altre tre immagini non ho acceso le VM]. Non è un problema: senza il file `child_accounts_language()` torna falso e si usa la lingua di PAM/sistema.
   NON serve alcuna dipendenza nuova.
6. Verdetto A1 + A2: **PORTABILE CON ADATTAMENTO** (nessuno difficile; è la voce con più valore percepito: un utente italiano oggi ha il desktop remoto in inglese).
   Da `fedora45/src/child.c`: blocco 1603-1710 (`struct child_locale`, `child_locale_name_ok/_value_ok`, `child_accounts_language`, `child_locale_read`, ~110 righe),
   chiamata dopo `pam_getenvlist` (Fedora 1983-1984), uso 2065-2070 (copia in `envp`), **`envp[16]` → `envp[32]`** (Debian è 16, il tetto `ne < 14` va tolto: LANG +
   fino a 12 voci `LC_*`/`LANGUAGE` + le 8 attuali); da `fedora45/src/session.c`: 5 righe in `compose_environment` (3711-3716: `LC_*` e `LANGUAGE` dall'ambiente
   del figlio, accettando solo i nomi ammessi) e 2 righe in `OUR_VARIABLES` (4798-4799) perché a fine sessione `LANGUAGE`/`LC_*` tornino com'erano. Dimensione: piccolo-medio (~140 righe).
   Dipendenze: nessuna (il `child_path_ok()` di Ubuntu è un'altra voce, e su Debian non cambia nulla perché `/etc/environment` è vuoto).
7. Rischi/cambi di comportamento (da approvare): il desktop remoto cambia lingua rispetto a oggi (da inglese a quella dell'utente o del sistema). Chi ha il sistema in inglese non vede nulla.
   Se l'utente ha scelto una lingua il cui locale non è generato, il ripiego dichiarato è `C.UTF-8` come oggi. Il nuovo punto di lettura è un file di root dentro la home della
   gestione utenti (aperto con `O_NOFOLLOW`, file regolare piccolo, solo caratteri semplici). Da provare col prodotto (E4): utente con lingua `it_IT.UTF-8` scelta nelle Impostazioni
   (`gnome-control-center` o `busctl … SetLanguage`) e sistema `en_US`; `LANGUAGE=it:en` e `LC_TIME` impostati con `update-locale`/`localectl`; con `it_IT` senza codifica.

## C7 — aggancio «il locale chiude il remoto» per gdm3
[V, VM] **Tutti** i servizi PAM di gdm3 fanno `@include common-session`: `gdm-password`, `gdm-autologin`, `gdm-fingerprint`, `gdm-launch-environment`, `gdm-smartcard`, `-pkcs11-exclusive`,
`-sssd-exclusive`, `-sssd-or-password` (8 su 8). `pam-auth-update` mette la riga `pam_exec` (`debian/remotix.pam-config`, Priority -1, `Session-Interactive-Only: yes`, tipo Additional)
in `common-session`: gdm3 la eredita già senza altro. In `gdm-password` `common-session` viene DOPO `pam_selinux open` (che su Debian non ha SELinux, riga inerte), `pam_loginuid`,
`pam_keyinit`, `pam_limits`, `pam_env` ×2. Debian ha anche `gdm-launch-environment` (il greeter, utente `Debian-gdm`): l'aggancio c'è anche lì (lo filtra `remotix-local-login`,
non verificato qui). Nel `common-session` della VM non c'è ancora la riga REMOTIX (prodotto non installato). Verdetto: **NON SERVE nulla di nuovo** (come lo studio); resta il «provato dal proprietario sulle live» (A2 del registro).

---
## Diff dei blocchi GNOME/mutter fra i tre alberi (segnalo ciò che lo studio non elenca)
- `mutter.c/h`: Debian↔Ubuntu = U4 (sopra) + testo del messaggio di rifiuto; Ubuntu↔Fedora identici.
- `input.c`: Debian↔Ubuntu = commenti dconf + `input_dropped`; Ubuntu↔Fedora = A4.
- `rootside.c`: Debian↔Ubuntu = 1 riga (U13); Ubuntu↔Fedora identici.
- `child.c` Debian↔Ubuntu (443 righe di diff) per GNOME: (a) PATH di PAM (`child_path_ok`, 1573-1594, 1790-1801) — su Debian inerte; (b) **niente fifo di sessione**
  in Ubuntu (`--session-fd` tolto: logind 259 usa il pidfd); **Debian lo ha e DEVE tenerlo** (logind 257: `libpam-systemd` 257.13; il commento di Ubuntu lo dice «valido con logind ≥ 258») → NON copiare
  quel blocco (`child.c:1709-1737`, 1919-1924, 10090-10108); (c) `closing_asked_ms` anticipato e `session_over_early`/`session_life` a tre risposte (addio anticipato quando la sessione è certamente morta; GNOME
  e non KDE; risolve il caso RealtimeKit fino a 25 s) — voce non assegnata a me, ma tocca GNOME: richiede `session.c` `session_life()` (993-1102) e `name_owner_three`; portabile, dimensione media; (d) `STAGE_MIN`/`fatal` (U4);
  (e) KDE (`capture_watch_sequence`, `kwin_poke`, ecc.) fuori dal mio ambito. Ubuntu↔Fedora `child.c` (345 righe): A1/A2, SELinux (F5, uscite 44-47), KDE; nessun blocco GNOME nuovo.
- `session.c` GNOME-specifico fra Debian e Ubuntu: `desktop_session()` (aggiunge `ubuntu`/`kubuntu`…: non serve a Debian), `session_life()`, AssertEnvironment/SHELL_MODEL (GNOME 50: NON portare),
  `inactive_unit(busy)` (aggiunge `graphical-session.target`: «NON portare» per GNOME 48? In GNOME 48 `gnome-session-init-worker` non esiste e `graphical-session.target` si ferma con la sessione
  (`StopWhenUnneeded=yes` + `BindsTo`); aggiungerlo come condizione di attesa potrebbe solo allungare l'attesa. [D]. Da non portare senza una ragione misurata.)

## Che cosa NON sono riuscito a verificare
- Il comportamento col prodotto: A4 su mutter 48; blocchi con profilo runtime di dconf 0.40 (U1); scala 2 su mutter 48 (U4); P7 su GNOME (E1); lingua scelta dall'utente (forma del valore in AccountsService, E4).
- Le altre tre immagini (nessuna VM accesa): accountsservice dedotto da `apt-cache depends` fatto nella VM gnome.
- Se gnome-software in una sessione remota provoca una finestra polkit per un'azione fwupd diversa da `refresh-remote`.
