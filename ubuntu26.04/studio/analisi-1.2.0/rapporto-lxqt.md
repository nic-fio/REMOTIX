# Rapporto LXQt (Lubuntu) — REMOTIX 1.2.0 per Ubuntu 26.04

Analisi di sola lettura del 26 nov 2026: `diff` reale fra `ubuntu26.04/src`, `fedora45/src` e `debian13/src` (file per file), lettura di `debian13/PIANO.md`
(dalla riga ~300), `debian13/docs/REGISTRO-problemi.md` F-H, `debian13/studio/analisi-1.2.0/rapporto-lxqt.md`, `debian13/studio/prove-1.2.0/giro5-lxqt.md`,
`fedora45/PIANO.md` / `REGISTRO-problemi.md` / `studio/4-lxqt-fedora45.md`, `ubuntu26.04/studio/7-xubuntu-lubuntu.md`, `12-verifiche-lxqt.md`, `13-riunito-xfce-lxqt.md`,
`giro2-lxqt.md`. Nessun server toccato, niente compilato, nessun file esistente modificato.
Legenda: [V] verificato sul codice/documenti di oggi (con file:riga), [D] dedotto, «non verificato» = non ho modo di dirlo da qui.
Righe: `F` = `fedora45/`, `D` = `debian13/`, `U` = `ubuntu26.04/`.

## 0. Scoperte principali (la classificazione del 25 nov va corretta)

1. **Ubuntu non è «indietro» per LXQt: per quasi tutto ciò che riguarda LXQt `ubuntu26.04/src` è già al livello di Fedora.** Misurato [V]: `diff` Ubuntu↔Fedora di `session.c` ha **0 righe che citano lxqt, lubuntu, picom, blueman, compositor, autostart** (le 137 righe di differenza sono tutte dconf-in-`/run/remotix`/SELinux, KWin `--virtual`, `LC_*`, chiusura KDE a 5 s). Ubuntu ha già, con gli stessi nomi di Fedora: `LXQT_X11_COMPOSITORS` (U `session.c:7003`), `lxqt_session_commands()` (7022), `SESSION_NOT_IN_REMOTE_AUTOSTART` con `blueman.desktop` (3257) e `session_autostart_cover()` (3262), `LXQT_SHARED_SERVER_PROGRAMS`/`lubuntu-update` (6861-7021), `session_missing_component()` (764; `main.c:1173-1181`; seconda guardia `session.c:8449`), `session_life()` (1035; ramo LXQt `org.lxqt.session` 1332), fine-sessione-detta-subito (`session_over_early`, `finished_told`, `stage_refused_by_child`, `wt_dismiss_user_session_over`: presenti nei tre alberi), sentinella `na` (`sentinel.c`: identico nei tre alberi, 0 righe), AppArmor `deny unix (bind, listen)` (C4), `needrestart` (`debian/needrestart/remotix.conf` identico a Debian), `local_login.c` (identico nei tre), `rootside.c` (1 riga di dconf GNOME). Quindi di quel pezzo di classe A/E dello studio del 25 nov **nulla da portare per LXQt**: era una voce «Ubuntu le ha, Debian no», non «Fedora le ha, Ubuntu no».
2. **Ciò che manca davvero a Ubuntu per LXQt si riduce a sei blocchi, tutti «generali» (non di LXQt) ma con effetto su LXQt**: (a) lingua del desktop (`child.c`), (b) `LC_*`/`LANGUAGE` (`session.c`), (c) `PATH` (con una sorpresa, §3.4), (d) riga di registro della chiusura QUIC (`transport.c`), (e) controllo dell'aggancio PAM a ogni avvio del servizio (`remotix-pam-hook` + `remotix.service`), (f) cache Mesa + messaggi di testo + regola polkit fwupd. In più una voce che Fedora NON ha ma Debian sì: `manager_set_locale` (lingua nel gestore utente per KDE/XFCE/LXQt).
3. **Il codice LXQt è identico nei tre alberi**: stesso `labwc -C <cartella> -S lxqt-session` (`session.h:207-227`), stesso `write_config_labwc_lxqt()` (U 4130, 4366), stessa uscita `org.lxqt.session.logout()` → 10 s (`WAIT_EXIT_MS`, U 108) → SIGTERM a ogni `labwc` dell'utente (`kill_xfce()` U 4648; `really_terminate()` ramo LXQt U 5600-5622). I 5 s e `graphical-session.target` sono **solo KDE** (F `session.c:113`, 4559-4610, 5639): per LXQt non cambia niente, come per XFCE e GNOME (E1/A6/A7 non toccano LXQt).
4. **Lubuntu non è Fedora e non è Debian: la sessione locale è X11 + openbox (+ picom)**, non Wayland/miriway (Fedora) e non X11/xfwm4 (Debian) [V da `studio/7-xubuntu-lubuntu.md:112-117, 129-132, 325`, pacchetti estratti: `/usr/share/xsessions/Lubuntu.desktop` → `startlxqt`, `window_manager=openbox` in `/etc/xdg/xdg-Lubuntu/lxqt/session.conf`; `lxqt-wayland-session 0.3.1` esiste ma Lubuntu **non** lo installa; `labwc`, `wlr-randr`, `xwayland` non vengono né da `lubuntu-desktop` né da `xubuntu-desktop`]. Non misurato su una live Lubuntu 26.04.1 in questa analisi. Conseguenza: gli strumenti di prova di Fedora/Debian per l'accesso locale su LXQt vanno adattati in modo diverso da entrambi (§4).
5. **Il labwc usato da LXQt su Ubuntu è quello di Ubuntu** (0.9.3-1, [V] `12-verifiche-lxqt.md` D.3 e `13-riunito:Prova 1`), non il nostro `/usr/libexec/remotix/labwc` (quello serve solo a KDE: `debian/control:102-106`). `labwc` resta `Recommends` e l'avviso del `postinst` esiste già (U `debian/remotix.postinst:63-72`). Debian ha solo riformulato il testo.
6. **Il rischio numero uno di Debian (`--session-fd`/fifo di logind in `child.c`) NON esiste su Ubuntu**: U `child.c:1738-1746` dice esplicitamente che con systemd 259 logind segue il pidfd del capo-sessione e nulla deve attraversare l'`execve`. Chi porta i blocchi di `child.c` da Debian a Ubuntu deve prendere solo le funzioni `child_locale_*` e le righe del PATH e **non** il resto del file di Debian (che ha il fifo, `--session-fd`, PATH fisso senza `child_path_ok` commentato per Debian). Regola: lavorare a blocchi sul file di Ubuntu, come ha fatto Debian sul suo.

## 1. Voci da portare / da decidere per LXQt

### V1. Lingua del desktop remoto = quella scelta dall'utente, altrimenti quella di sistema (A1)
- **Che cosa è:** oggi il desktop LXQt remoto parte sempre con `LANG` fisso (fallback `C.UTF-8`), cioè in inglese; con la voce parte nella lingua che l'utente ha scelto nelle Impostazioni (file di AccountsService letto da root) o, in mancanza, in quella di sistema (`/etc/default/locale`).
- **Fedora:** `child.c:1603-1696` (`struct child_locale` 1614, `child_locale_name_ok/value_ok`, `child_accounts_language` 1649, `child_locale_read` 1690), dichiarazione `struct child_locale locale;` 1838, `envp[32]` (era 16) 1851, chiamata 1983-1984 («2-quater», ancora root, prima di cambiare identità), copia in `envp[]` 2068-2071.
- **Ubuntu oggi:** **manca** [V]: 0 occorrenze di `child_locale_`; `envp[16]` (`child.c:1628`); nessuna lingua in `envp[]`; `session.c:3699` scrive `LANG=<local_utf8()>` (cerca `C.UTF-8`/`C.utf8`, `session.c:1406`). Il file PAM c'è già: `remotix.pam:123` ha `pam_env … envfile=/etc/default/locale` (identico a Debian prima del 1.2.0 salvo commenti: `diff U D remotix.pam` = 3 sole righe di commento) — la precondizione di Debian è già soddisfatta su Ubuntu.
- **Debian:** portata quasi parola per parola (`child.c:1593-1694`, `1717`, `1730` envp[32], `1874-1875`, `1959-1962`); unica differenza dal blocco di Fedora: i commenti (`/etc/default/locale` invece di `/etc/locale.conf`). Il codice è identico.
- **Da fare su Ubuntu: portare così com'è** il blocco di Debian (che è quello di Fedora con i percorsi giusti per i `.deb`), in tre punti del file di Ubuntu: funzioni prima di `become_and_exec` (subito dopo `child_path_ok`, U 1576-1590), chiamata dopo i passi di PAM/prima di `setuid`, copia in `envp[]`; `envp[16]` → `envp[32]`.
- **Dimensione:** media (~100 righe, un file). **Rischio:** medio-basso: valori validati carattere per carattere; `session.c` controlla ancora che il locale esista e sia UTF-8 (`session.c:1386-1440`), altrimenti `C.UTF-8`. Attenzione: se il locale scelto (es. `it_IT.UTF-8`) **non è generato** sulla macchina, `session.c` ricade su `C.UTF-8` con una riga di registro [V codice] (non misurato su Lubuntu).
- **Come provarla:** utente nuovo con `Language=it_IT.UTF-8` in `/var/lib/AccountsService/users/<utente>` (come `giro5-lxqt.md` §E: file scritto a mano perché `accountsservice` non c'era nella VM Debian; **su Lubuntu 26.04 non so se `accountsservice` è installato: non verificato**), `locale-gen it_IT.UTF-8`, poi `LANG` letto dentro `labwc`, `lxqt-session`, `lxqt-panel`, `pcmanfm-qt` e in `systemctl --user show-environment`; caso senza file: lingua di `/etc/default/locale`.
- **Cambio visibile (per approvazione):** SÌ. Il desktop LXQt remoto passa dall'inglese alla lingua dell'utente/di sistema (menu, orologio, date). Decisione del proprietario del 23-25 nov per Fedora, estesa a Debian il 25 nov («allinea = come Fedora»).

### V2. `LC_*` e `LANGUAGE` di sistema arrivano al desktop e tornano com'erano a fine sessione (A2)
- **Che cosa è:** oltre a `LANG`, i formati (date, numeri, carta) di sistema.
- **Fedora:** `session.c:3711-3715` (dopo la riga `LANG=`), `OUR_VARIABLES` `4798-4799` (`LANGUAGE`, `LC_CTYPE` … `LC_ALL`).
- **Ubuntu oggi:** manca (`session.c:3699` solo `LANG`; `OUR_VARIABLES` 4783-4800 con `"LANG", "PATH"` ma senza i `LC_*`).
- **Debian:** portata uguale (`session.c:2948-2952`, `OUR_VARIABLES` 4059-4060 in `us.diff`).
- **Da fare: portare così com'è** (≈10 righe). Dipende da V1 (`child.c` deve già lasciar passare solo i nomi validi). **Piccola.** Rischio: basso. Prova: `LC_TIME` impostato con `localectl` visibile in `lxqt-panel` (orologio) e ripristinato nel gestore utente dopo il Log Out.
- **Cambio visibile:** insieme a V1 (formati in lingua di sistema).

### V3. `manager_set_locale`: la lingua va anche nel gestore dei servizi dell'utente (SOLO Debian, non Fedora)
- **Che cosa è:** prima di far nascere la sessione, la lingua (LANG/LC_*/LANGUAGE) viene messa nell'ambiente di `systemd --user` per KDE, XFCE **e LXQt**, perché da lì nascono i servizi di contorno; a fine sessione torna com'era (`OUR_VARIABLES`); nella chiusura «leggera» per accesso locale resta lì di proposito.
- **Fedora:** non c'è (0 occorrenze). **Debian:** `session.c:3583-3619` (funzione 3595), chiamata `3671-3672` (`if (e_kde() || e_xfce() || e_lxqt())`); misurato su KDE (Plasma 6.3.6) e su XFCE; su LXQt il giro 5 mostra `it_IT.UTF-8` in tutti i processi e nel gestore utente, **ma non distingue** se serviva (il codice c'era già) [V `giro5-lxqt.md` §E].
- **Ubuntu oggi:** manca. **Interazione da guardare:** la voce E3 del registro di Ubuntu (la «foto» del gestore utente può essere vecchia; `non ho potuto guardare` vale `chiuso`) riguarda proprio il ripristino di queste variabili.
- **Da fare: adattare** — portarla come Debian (30 righe + 2 di chiamata) perché la regola del proprietario è «un solo comportamento», ma **dichiarare «non vista necessaria su LXQt»** e provarla con e senza (un giro LXQt con la lingua italiana, una prova con la funzione disattivata per sapere se serve davvero). In alternativa **non portare** finché una prova su Lubuntu non mostra un processo del desktop con la lingua di sistema (la decisione è del proprietario, non mia).
- **Dimensione:** piccola. **Rischio:** medio-basso (tocca l'ambiente di `systemd --user`, condiviso con un eventuale accesso locale: da qui la regola «restituire a fine sessione»). **Prova:** `systemctl --user -M <utente>@ show-environment` durante e dopo la sessione; dopo una chiusura per accesso locale la lingua resta (voluto).
- **Cambio visibile:** nessuno oltre V1.

### V4. `PATH` come in un accesso locale (A3) — **qui il porting «così com'è» NON ha effetto su Ubuntu**
- **Che cosa è:** Fedora, quando PAM non dà un PATH, ripiega su `~/.local/bin:~/bin:/usr/local/bin:/usr/bin` invece della lista fissa, così un programma che l'utente tiene in `~/.local/bin` parte dal desktop remoto come da quello locale.
- **Fedora:** `child.c:2028-2037` (`char fallback[400]`, scarta un home con `:`). **Debian:** portato (`child.c:1919-1928`) e **ha effetto** perché su Debian `/etc/environment` è vuoto (commento `child.c:1573`) → PAM non dà PATH → vale sempre il ripiego.
- **Ubuntu oggi:** `child.c:1794-1800`: il PATH di PAM (`/etc/environment`, che su Ubuntu contiene `/snap/bin`, le cartelle sbin e i giochi: commento `child.c:1573` nella versione Ubuntu) **vince** se supera `child_path_ok()`; il ripiego fisso `/usr/local/bin:/usr/bin:/bin` scatta solo se PAM non ne dà. Porto del ripiego di Fedora = **modifica che non scatta mai** su un Lubuntu normale [D, da misurare].
- **Fatto nuovo:** in un accesso locale Lubuntu (X11: sddm `Xsession` → `/etc/X11/Xsession.d/*` e `~/.profile` di skel) `~/.local/bin` si aggiunge al PATH se la cartella esiste [D da `7-xubuntu-lubuntu.md:189-192` e dallo skel standard di Ubuntu; **non verificato su Lubuntu 26.04**]; nel remoto REMOTIX non legge `~/.profile` di proposito (`session.c:3639`, regola `CODER.md`). Quindi su Ubuntu oggi un programma in `~/.local/bin` **non** parte dal desktop LXQt remoto e il porting del ripiego non lo cambia.
- **Da fare: DECISIONE del proprietario.** Opzioni: (a) portare solo il ripiego di Fedora (innocuo, 6 righe, nessun effetto oggi); (b) far sì che il PATH remoto contenga `~/.local/bin:~/bin` davanti a quello di PAM *quando le cartelle esistono* (stesso risultato che ha un accesso locale; ~10 righe in `child.c`; **cambia il comportamento visibile**: programmi propri dell'utente trovati dal pannello/`qterminal`); (c) non fare nulla e dichiararlo. Raccomando (b) solo dopo aver misurato PATH locale e remoto su una VM Lubuntu (`echo $PATH` in `qterminal`, utente con `~/.local/bin` creato).
- **Dimensione:** piccola. **Rischio:** basso (home con `:` esclusa). **Prova:** utente con `~/.local/bin/ciao` eseguibile; `qterminal` → `ciao` remoto e in locale.
- **Cambio visibile:** (b) sì.

### V5. Riga di registro «chi ha chiuso la connessione QUIC e perché» (A5)
- **Che cosa è:** una riga in più nel registro del servizio (peer/noi/silenzio, codice TLS con nome, handshake completo o no). Non riguarda LXQt in particolare.
- **Fedora:** `transport.c:955-1080` (`close_why()` 1021, chiamate 1092, 2187, 2597). **Ubuntu oggi:** manca [V]: `diff` U↔F 151 righe, tutte aggiunte; `transport.c` Debian **identico a Fedora** (0 righe). **Debian:** copiato intero.
- **Da fare: portare così com'è** (copiare `fedora45/src/transport.c`: Ubuntu aveva lo stesso file di Debian prima). Verificato che Ubuntu usa le stesse API ngtcp2 1.25.0 statiche (`debian/control:123` `Static-Built-Using: ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0), …`).
- **Dimensione:** piccola. **Rischio:** nessun cambio di comportamento (solo testo del registro). **Prova:** compilazione nella VM di costruzione; un client che rifiuta il certificato.
- **Visibile:** no (solo registro).

### V6. «Il locale chiude il remoto» su LXQt (E1/A6/A7): nessun codice, solo prove
- **Stato nei tre alberi:** codice identico: `local_login.c` e `rootside.c` (zona PL) uguali a Fedora/Debian [V diff 0]; `really_terminate()` LXQt come in §0.3.
- **Su Ubuntu oggi:** provato solo **simulato** (hook lanciato come root con ambiente PAM finto, P1-P6 verdi su LXQt: `13-riunito:Prova 2` e `Prova 5`; i box sono contenitori senza sddm). Nessuna prova con un vero sddm Lubuntu e nessuna prova con programmi aperti (P7/P8): `non verificato`. Il registro A2 cita la prova a mano del proprietario con **la live di Debian**.
- **Differenza con Debian che conta per Ubuntu:** la sessione locale di Lubuntu è X11 con `openbox`, non xfwm4: P7 (`COMPOSITOR["lxqt"]`, Fedora `check-prelocal.py:158` = `("labwc",)`, Debian `("xfwm4","labwc")`) deve cercare **`openbox`** come «compositor» del desktop locale (in Lubuntu `picom` fa solo la composizione) [D]. Il pannello `lxqt-panel` è lo stesso (`K.PANEL`).
- **Su Ubuntu da fare:** nessuna modifica al prodotto; P7 (qterminal con `top`) e le prove a mano con live Lubuntu 26.04.1; P8 su LXQt resta BLOCKED come su Fedora/Debian (`featherpad` senza stdin noto). Dimensione: media (prove), rischio prodotto: nullo/basso. Da misurare: tempi (chiusura gentile 10 s + forzata) e assenza di core dump; `kill_xfce()` (SIGTERM a tutti i `labwc` dell'utente) non può colpire il desktop locale di Lubuntu (X11, niente `labwc` locale) [D]; lo potrebbe solo se un utente installasse `lxqt-wayland-session` e scegliesse la sessione `labwc` (non verificato).

### V7. Controllo dell'aggancio PAM a ogni avvio del servizio (B1)
- **Che cosa è:** a ogni avvio di `remotix.service` si controlla che la riga di `remotix-local-login` sia ancora in `/etc/pam.d/common-session` (sddm di Lubuntu la include) e, se manca (un aggiornamento di `sddm`/`libpam-runtime`, una modifica), la rimette; una riga di registro dice com'è andata; non impedisce mai l'avvio.
- **Fedora:** `rpm/remotix.service:42` `ExecStartPre=-…/remotix-pam-hook check` + `src/remotix-pam-hook` (per authselect/sddm: C7, **non** portabile). **Debian:** script suo, 40 righe di `sh`, `src/remotix-pam-hook` (usa `pam-auth-update --package`, regex della riga vera `session … pam_exec.so … remotix-local-login`), `debian/remotix.service:36-42` (anche `Environment=MESA_SHADER_CACHE_DISABLE=true`), `debian/rules:84` (installazione), `debian/remotix.prerm:67-75` (la riga PAM si toglie **dopo** l'arresto del servizio), `debian/remotix.postinst:27` (regex più precisa al posto di `grep -q remotix-local-login`).
- **Ubuntu oggi:** manca [V]: solo l'avviso del `postinst` (`debian/remotix.postinst:44-49`, `grep -q remotix-local-login`) e `prerm:57-64` toglie la riga **prima** di fermare il servizio.
- **Da fare: portare così com'è** lo script di Debian (`pam-auth-update` è identico su Ubuntu e Debian) + le tre righe di `service`, `rules`, `prerm`, `postinst`. **Media** (5 file di pacchetto, nessun C). **Rischio:** medio: tocca `/etc/pam.d/common-session` da `ExecStartPre` (sempre `exit 0`, mai `--force`; se l'amministratore ha modificato il file a mano `pam-auth-update` rifiuta e resta la riga di avviso). È voce generale: la analizza chi fa i desktop comuni; qui conta perché sddm di Lubuntu dipende da `common-session`.
- **Prova:** togliere la riga a mano, riavviare il servizio → riga rimessa e scritta nel registro; modificare a mano il file → solo avviso; `apt remove`/`purge` → nessuna riga residua dopo l'arresto; aggiornamento 1.0.1 → 1.2.0.

### V8. Cache grafica di Mesa nella cartella di root (B2)
- **Fedora:** `rpm/remotix.service:39`. **Debian:** `debian/remotix.service:36-42` e `postinst:38` (`MESA_SHADER_CACHE_DISABLE=true` per la sonda codec). **Ubuntu oggi:** manca; non verificato che su Ubuntu la sonda lasci davvero `/root/.cache` (su Debian sì: lo ha trovato la prova di rimozione, F12). **Portare così com'è** (2 righe). Piccola, rischio nullo. **Prova:** dopo `apt purge` nessun file `remotix`/`mesa_shader_cache` in `/root`. Non cambia i desktop degli utenti (tengono la loro cache). Valida per tutti i desktop.

### V9. Testi: «reinstalla il pacchetto» e residui di Fedora/Arch/SUSE (B3/A9)
- **Fedora:** `main.c:469-472`. **Ubuntu oggi:** testo vecchio (`main.c:466-473`: «on Fedora and Arch it is pam_deny… Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch»); anche `main.c:439-447` (commento) e `remotix.pam:5-6, 30-39`. **Debian:** `main.c:465-468` («reinstall the package from its file (sudo apt install --reinstall ./remotix_<version>_amd64.deb)») e commenti accorciati. **Da fare: adattare** copiando il testo di Debian (vale uguale per Ubuntu). Piccola, rischio nullo. Messaggi `kwin.c` (RX-KDE-001/002/003) sono KDE, fuori da LXQt. **Visibile:** solo il testo verso l'amministratore.

### V10. Regola polkit per l'aggiornamento dei metadati del firmware (A8)
- **Fedora:** `remotix-remote-sessions.rules:76-79` (`org.freedesktop.fwupd.refresh-remote`); **Debian:** aggiunta uguale (U↔D 4 righe), ma su Debian 13 «non fa nulla» (fwupd 2.0.20 senza quell'azione: F12). **Ubuntu:** manca [V]. **Da fare: portare così com'è** (4 righe) per uniformità (principio «un solo comportamento»), dichiarando «non vista scattare». **Su LXQt** l'effetto è probabilmente nullo: chi la chiede è `gnome-software` (GNOME); su Lubuntu non so quale programma tocchi fwupd al login [non verificato]. Piccola, rischio basso. Prova: `check-desktop` `no-password-windows` su LXQt (0 chiamate `BeginAuthentication`: già verde su Debian/Ubuntu).

### V11. Voci LXQt che Ubuntu ha già e che DEVONO restare (Debian le aveva tolte, Ubuntu no)
- `LXQT_SHARED_SERVER_PROGRAMS` / `lubuntu-update` (U 6861-7021, 7118-7168): senza, il secondo utente LXQt riceve «Lubuntu Update crashed too many times» (misurato `12-verifiche-lxqt.md` A, riprodotto con due utenti; cura verificata in `13-riunito:Prova 3`: nessun `lubuntu-update` nelle sessioni, nessuna finestra). Debian l'ha tolto (programma inesistente); su Ubuntu è codice vivo.
- `LXQT_X11_COMPOSITORS` con **picom** di Lubuntu (modulo senza `X-LXQt-X11-Only`: `lxqt-session` lo rilancia 5 volte, «X Compositor crashed too many times», `12-verifiche`/`giro2-lxqt.md` L1): resta, con il commento «Lubuntu's».
- `desktop_of_session_name()` con `lubuntu`/`xubuntu`/`kubuntu`/`ubuntu` (U 391-402, «ubuntu» per ultimo) e `local_session_name_find`/`local_login_adds_folders`/`login_session_desktop` (U 2946-3081; `xdg-Lubuntu` in `XDG_CONFIG_DIRS`, `XDG_SESSION_DESKTOP` come lo darebbe sddm): **specifici di Ubuntu** (`x11-common` di Ubuntu ha `60x11-common_xdg_path`). **Non** togliere come ha fatto Debian (PULIZIA voci 4 e 7): è ciò che dà al desktop remoto di Lubuntu pannello, tema e `session.conf` come in locale.
- `session.c:901-952`: scelta della sessione GNOME con `ID` di os-release (non LXQt).
- `SESSION_UNIT_SHELL_MODEL` e la scelta `@user`/`@ubuntu` (GNOME 50), `DCONF_*` in `/etc/dconf/db/remotix` (C5, `rootside.c:3344`): solo GNOME, non toccarli; **non** portare da Fedora le versioni con `/run/remotix` (SELinux).
- `child.c`: nessun `--session-fd`, nessun fifo (§0.6): **non** prendere il file di Debian; Ubuntu usa `child_path_ok()` con il PATH di `/etc/environment` (snap incluso): **non** sostituirlo con il PATH fisso di Debian.
- `debian/remotix_network.apparmor`: righe `xkeyboard-config-2`, `/etc/xkb`, `deny unix (bind, listen)` con kernel che controlla i socket (U10/U11 del 25 nov) restano; Debian ha in più la riga `org.kde.remotix.desktop r` (F10, KDE) che Ubuntu non ha (KDE: fuori da questo rapporto).
- `prove/`: `package-snap.py` (percorsi `/var/lib/snapd`, `/run/snapd*`, cloud-init), `check-desktop.py` con `sudo-rs` (`TERMINAL["gnome"]="ptyxis"`, messaggi sudo-rs, `.config/dconf/remotix$`): restano Ubuntu.
- `kill_xfce()`/`labwc` per LXQt: Ubuntu usa `labwc` di Ubuntu da PATH (`g_find_program_in_path`, U 764-775); non reintrodurre `REMOTIX_LABWC` per LXQt.

### V12. Autostart del desktop Lubuntu nella sessione remota: da misurare (non ci sono precedenti nuovi)
- **Dato:** `/etc/xdg/xdg-Lubuntu/autostart/` contiene blueman, `lubuntu-update-autostart`, `lxqt-qlipper-autostart` (`X-LXQt-Need-Tray`), `lxqt-xscreensaver-autostart` (`X-LXQt-X11-Only=true`, saltato su Wayland), nm-applet (`Hidden=true`), nm-tray, picom (senza `X11-Only`), print-applet [`7-xubuntu-lubuntu.md:129-132`]. Già coperti: picom, lubuntu-update, blueman (`session_autostart_cover` per XFCE e LXQt, U 3262/3452/7170). `qlipper` resta (decisione 16 nov «si lascia», `7:294-299`). `nm-tray` e `print-applet`: su Debian 13 partono nella sessione remota senza finestre né errori (`giro5-lxqt.md` §E); **su Lubuntu non misurato** (giro2-lxqt dice «nessuna finestra» a 40 s con 124/124 PASS).
- **`xiccd`:** Debian ha messo `xiccd.desktop` in `SESSION_NOT_IN_REMOTE_AUTOSTART` (D `session.c:2511`; era per XFCE: chiede la password di amministratore a polkit). Su LXQt-Debian `xiccd` non c'è (`giro5` §E, [V] 0 righe). **Su Lubuntu 26.04: non verificato** se `xiccd` è installato (il file `/etc/xdg/autostart/xiccd.desktop` ha `NotShowIn=GNOME;KDE` → partirebbe su LXQt; `12-verifiche-xfce.md` lo vede su Xubuntu). Voce **piccola** (una stringa, `session.c:3257`): portarla comunque è innocuo se il programma non c'è (la copertura non scrive nulla se il file di sistema manca? — **non verificato** per `xiccd`, la logica di `system_autostart_exists()`, U 3227, è da rileggere prima di decidere). Raccomando: portarla insieme alla decisione per XFCE (è la stessa riga) e provare su Lubuntu che `no-password-windows` resti verde.

## 2. Voci classificate «dubbie/specifiche» il 25 nov che per LXQt si risolvono così

| Voce del 25 nov | Esito per LXQt su Ubuntu |
|---|---|
| A4 primo movimento del puntatore (`input.c`) | **Non riguarda LXQt**: il blocco è nel ramo EI (`ei_device_pointer_motion_absolute`, F `input.c:1937-1951`); XFCE/LXQt usano `wlr_input` (`in->wlr`). Portarlo con GNOME (non cambia nulla qui). |
| A6/A7 chiusura KDE (5 s, `graphical-session.target`) | Solo KDE; LXQt resta a 10 s + forzata. Nessun lavoro. |
| E1 «ultima difesa» | Non c'è su Fedora per GNOME/XFCE/LXQt; Debian: non serve (misurato dal proprietario sulle quattro live). Ubuntu: non costruirla; P7 su Lubuntu, intervenire solo se fallisce. |
| E2 `force_guard_on` acceso dopo chiusura fallita | Stesso codice nei tre alberi (U 5541, F 5554); portare com'è = non fare nulla; annotare. |
| E3 `catatonit` | Solo banco; non pertinente a LXQt. |
| E4 lingua senza codifica / `LANGUAGE` / `FormatsLocale` | È V1/V2: da provare su Lubuntu (`it_IT`, `LANGUAGE=it:en`). |
| C1-C10, D1-D4 | Non si portano (SELinux, RPM, firewalld, KWin 6.8). Resta solo: non romperli (nessuna riga di Ubuntu li usa). |

## 3. `prove/` e banco per LXQt (cose da portare)

Differenze reali oggi [V `diff`]: Ubuntu↔Fedora: `check-prelocal.py` 307 righe (P7/P8), `check-desktop.py` 12, `lib.py` 2; solo Fedora: `check-exit.py`, `check-resize.py`, `hold.py`, `hold-user.py`, `prelocal.sh`, `banco-vm/autologin-lightdm.sh`, `banco-vm/autologin-sddm.sh`, `giro-*-radeon.sh`, `check-kde-*.py`, SELinux. Ubuntu già ha `banco-vm/box.sh` e `fresh-vm.sh` (identici a Fedora salvo percorsi) e `lib.py` con `RX_BANCO=vm` (porte 8841-8844).

1. **`check-prelocal.py` P7/P8: prendere da Debian** (`debian13/prove/check-prelocal.py`, già adattato ai `.deb`: `DM`, `command -v coredumpctl`, nessun SELinux), non da Fedora. Per Ubuntu: `DM = {"gnome":"gdm3","kde":"sddm","xfce":"lightdm","lxqt":"sddm"}`; terminale GNOME `gnome-terminal`→ per Ubuntu **`ptyxis`** (Ubuntu 26.04: `check-desktop.py:62`); **`COMPOSITOR["lxqt"] = ("openbox","labwc")`** (Lubuntu locale = X11+openbox [D]); `EDITORS` come Fedora/Debian (LXQt BLOCKED). `all.sh`: `prelocal` con timeout 2400 (Debian) e voce `apparmor`. **Media**, nessun rischio per il prodotto.
2. **`banco-vm/autologin-sddm.sh`**: copiare da Fedora (controllo `hostname = rx-lxqt`: **coincide con Ubuntu**, `vm-radeon.sh:162` `rx-$NAME`) cambiando `Session=lxqt-wayland` in **`Session=Lubuntu`** (la sessione predefinita di Lubuntu, X11) [D; il nome del file è `/usr/share/xsessions/Lubuntu.desktop`, `7:112`]. `autologin-lightdm.sh` per XFCE a parte. **Piccola.**
3. **`check-exit.py`, `hold.py`, `hold-user.py`, `prelocal.sh`**: Debian li ha presi da Fedora (0 righe di differenza per i primi tre): copiarli, cambiando solo i percorsi `/media/REMOTIX-DEBIAN/…` → `…UBUNTU/…` (`prelocal.sh:10`) e controllando che i nomi dei processi (`lxqt-panel`, `labwc`, `lxqt-session`, `pcmanfm-qt`) valgano per Lubuntu (`check-exit.py:21`). Piccola.
4. **`check-desktop.py` (LXQt, `panel.conf`)**: Fedora cerca `ls /usr/share/lxqt/panel.conf /etc/xdg/lxqt/panel.conf | head -1` (`check-desktop.py:433, 488`) perché su Fedora il file sta in `/etc/xdg/lxqt/`. **Non portare su Ubuntu**: la versione di Ubuntu (`/usr/share/lxqt/panel.conf`) ha dato 124/124 PASS su LXQt (`giro2-lxqt.md`); su Debian `ls | head -1` avrebbe scelto il file sbagliato (`lxqt-branding-debian`). Su Lubuntu 26.04.1 con `lxqt-panel 2.3.2` il file c'è (è passata la prova): non verificato oltre. `TERMINAL`/sudo-rs/dconf restano Ubuntu.
5. **`check-apparmor.py` + `lib.py` `Box.apparmor()`/`apparmor_summary()`** (Debian): portare così com'è; su Ubuntu il kernel 7.0 **controlla davvero** i socket unix, quindi il controllo è più significativo che su Debian (F9: non provato su un kernel che li controlli). `all.sh`: voce `apparmor` dopo `ban`.
6. **`fresh-vm.sh`**: aggiungere `systemd-coredump` all'elenco `P=` (Debian, `fresh-vm.sh:61`) perché il controllo dei core dump di P7/P8 non scatti «non verificato»; **decisione del proprietario** (come per Debian).
7. **Banco: `amdgpu.runpm=0`** (G1 di Debian): le quattro cadute del server erano dovute a una VM **Debian (kernel 6.12)** con la Radeon passata. **Non so se le VM Ubuntu (kernel 7.0) hanno lo stesso difetto** [non verificato]: prima di dare la Radeon a una VM Ubuntu controllare `SMU is resuming` e mettere `runpm=0` in precauzione (Debian: `COME-SI-LANCIA.md`). `ubuntu26.04/server/vm-radeon.sh` non lo menziona. **P7/P8 e il riavvio di sddm dentro la VM sono stati VIETATI su Debian con la Radeon passata**: finché non si è chiarito per Ubuntu, le prove di accesso locale vero vanno fatte solo sulle live vere (decisione già del proprietario: sue le prove a mano).
8. `live-installa.sh` (Ubuntu, `server/`) cita ancora il nome del pacchetto vecchio: aggiornare a `1.2.0` (stessa nota per tutti i desktop).
9. **Prove LXQt specifiche già disponibili, da rilanciare su Lubuntu col pacchetto 1.2.0:** `all.sh lxqt --clean` (P1-P6 + desktop + input + clipboard + media…), `hold.py` 240 s con utente nuovo (foto del desktop, nessuna finestra di password, lingua nei processi), `check-exit.py --box lxqt`, `check-lifecycle.py`.

## 4. Riepilogo per formato richiesto (voce → Fedora → Ubuntu oggi → Debian → azione → misura → rischio)

| Voce | Fedora | Ubuntu oggi | Debian | Che fare | Lavoro | Rischio |
|---|---|---|---|---|---|---|
| V1 lingua utente/sistema | `child.c:1603-1696, 1983, 2068` | manca | portata uguale `child.c:1593-1694, 1874, 1959` | così com'è (percorsi `.deb`) | medio | medio-basso |
| V2 `LC_*`/`LANGUAGE` | `session.c:3711, 4798` | manca | portata `session.c:2948` | così com'è | piccolo | basso |
| V3 `manager_set_locale` | non c'è | manca | `session.c:3583-3672` | adattare / decidere (non vista necessaria su LXQt) | piccolo | medio-basso |
| V4 `PATH` `~/.local/bin` | `child.c:2028-2037` | PATH di PAM vince (`1794-1800`) | portata (effetto reale solo su Debian) | **decisione** proprietario (porting puro = nessun effetto) | piccolo | basso |
| V5 registro QUIC | `transport.c` | manca | = Fedora | così com'è | piccolo | nullo |
| V6 locale chiude remoto | codice identico | solo simulato | provato a mano su live Debian | nessun codice; prove + adattare strumenti | medio (prove) | basso |
| V7 aggancio PAM a ogni avvio | `rpm/` (authselect) | manca | `src/remotix-pam-hook`, service/rules/prerm/postinst | così com'è (script Debian) | medio | medio |
| V8 cache Mesa | `service:39` | manca | `service:36-42`, `postinst:38` | così com'è | piccolo | nullo |
| V9 testi | `main.c:469-472` | vecchi (`466-473`) | `main.c:465-468` | adattare (testo Debian) | piccolo | nullo |
| V10 polkit fwupd | `rules:76-79` | manca | portata (inattiva) | così com'è | piccolo | basso |
| V12 `xiccd` in autostart | non c'è (Fedora: LXQt senza) | manca (stringa `3257`) | `session.c:2511` | portare con XFCE; prova su Lubuntu | piccolo | basso |
| picom, blueman, lubuntu-update, `session_missing_component`, U3, U9, C4, needrestart | presenti (stesso codice) | presenti | portati (senza nomi Lubuntu) | **niente da fare / non rimuovere** | — | — |

## 5. Segnalazioni a parte

### (1) Ciò che Ubuntu ha e Fedora no e DEVE restare (per LXQt)
`lubuntu-update` (U 6861-7021) [Fedora lo ha ancora nel codice ma Fedora non lo usa; per Ubuntu è vivo]; mappa nomi `lubuntu` (U 391-402); `local_session_name_find`/`login_session_desktop` con `xdg-Lubuntu` (U 2946-3081); labwc di distribuzione per LXQt con avviso `postinst`; AppArmor con `xkeyboard-config-2` e `deny unix (bind, listen)` (kernel 7.0); `child.c` senza fifo di logind (systemd 259); `remotix.pam` con `pam_env envfile=/etc/default/locale` e PATH da `/etc/environment` (snap incluso); `package-snap.py`; `sudo-rs` in `check-desktop.py`; `debian/needrestart`.

### (2) Dove portare la voce cambia il comportamento visibile su Lubuntu (serve l'OK del proprietario)
- **V1/V2** — il desktop LXQt remoto parla la lingua dell'utente/di sistema e usa i formati di sistema (oggi sempre inglese). Già deciso per Fedora e Debian; per Ubuntu: «allinea = come Fedora» (25 nov). Va solo avvisato che, a differenza di KDE su Debian, per LXQt non c'è un file di lingua per utente (`~/.config/lxqt/lxqt.conf` nasce senza lingua: `giro5-lxqt.md` §E) quindi segue sempre `LANG`.
- **V4 (b)** — `~/.local/bin` nel PATH remoto: **cambio nuovo e non ancora deciso** (porting puro: nessun effetto).
- **V3** — nessun cambio visibile, ma tocca l'ambiente di `systemd --user`: dichiarare.
- **V12 `xiccd`** — se `xiccd` è presente su Lubuntu, non parte più nella sessione remota: nessun cambio visibile (era una finestra di password indesiderata) se il problema esiste.
- Invisibili: V5, V7, V8, V9, V10.
- Nessun cambio per i tempi di chiusura su LXQt (10 s + forzata, come oggi).

### (3) Non verificato
- Sessione locale e display manager di una live **Lubuntu 26.04.1 vera** (X11/openbox/picom, `Session=Lubuntu`): dedotto da pacchetti estratti (`7-xubuntu-lubuntu.md`), mai guardata una live in questa analisi.
- Se `accountsservice` è installato su Lubuntu e dove sta la lingua scelta dall'installatore (Calamares → `/etc/default/locale`) [Debian LXQt VM: `accountsservice` assente].
- Se `/etc/default/locale` di una Lubuntu contiene `LANG` con un locale **generato** (e non `C.UTF-8`).
- PATH locale di Lubuntu con `~/.local/bin` (dedotto dallo skel/Xsession).
- `xiccd` e altri autostart su Lubuntu (`nm-tray`, `print-applet`, `qlipper`) nella sessione remota con labwc 0.9.3 e `lxqt-session 2.3.0`: giro2-lxqt dice nessuna finestra; non rimisurato col codice di oggi.
- Che la riga PAM di REMOTIX sia in `/etc/pam.d/sddm`/`sddm-greeter`/`sddm-autologin` di Ubuntu 26.04 con sddm 0.21.0 (Debian: `@include common-session` in tutti e tre, [V] sulla VM Debian; Ubuntu: non verificato).
- `CanHibernate`=`na` su Lubuntu e la sentinella (il codice è identico, U9 già presente).
- Regola fwupd su Ubuntu 26.04 (versione di fwupd): non verificato.
- Se le VM Ubuntu soffrono del blocco della Radeon come le Debian (`amdgpu.runpm`).
- Compilazione/avvio dei blocchi nuovi con il compilatore e le librerie di Ubuntu: nulla è stato costruito.
- `lxqt-panel`: percorso del `panel.conf` di sistema su Lubuntu 26.04.1 oggi (la prova del 18 nov passa con `/usr/share/lxqt/panel.conf`).
- `desktop_of_session_name`/`xsession_d_applies` con una Lubuntu avviata da lightdm: non rilevante per LXQt su sddm.

### (4) Voci rimaste aperte nei documenti di Debian che valgono anche per Ubuntu/LXQt
- **H1** `media/screen-updates` di poco oltre la soglia su LXQt (1,5 s contro 1,0; GNOME 1,05-1,2; KDE 1,03-1,06): causa non stabilita (VM senza monitor? strumento?). Da misurare su Lubuntu con le stesse VM; soglia non allargata.
- **H3** `kbd-not-producible` su **Firefox in LXQt**: probabile difetto dello strumento (Chrome passa; Firefox via WebDriver). Su Ubuntu Firefox è snap: stesso rischio di strumento, non verificato.
- **H4** P7/P8 automatiche solo su GNOME; su Debian le altre le ha provate a mano il proprietario sulle live. Per Ubuntu: stessa procedura (e vedi V6/§3.7 sul divieto con Radeon).
- **H5** `xiccd` su Xubuntu/Lubuntu (voce V12); lingua su Fedora KDE mai misurata; `xfconfd` resta nella lingua di sistema (XFCE).
- **E3** del registro di Ubuntu (foto del gestore utente vecchia; «non ho potuto guardare» vale «chiuso»): correzione piccola consigliata, **non fatta** né su Ubuntu né su Debian; interagisce con V3 (variabili del gestore utente).
- **G1/G3** metodo del banco: `amdgpu.runpm=0`, `systemd-coredump` nelle VM, controllo AppArmor in `all.sh`.
- **F9** AppArmor `deny unix` provato su Debian solo «senza effetto» (kernel 6.12): **Ubuntu è la prima macchina dove conta**: la prova di accesso con profilo in `enforce` (U11 del 25 nov) resta da fare.
- Licenze/manuali/sito: fuori da questo rapporto.

## 6. Ordine consigliato per LXQt (se il proprietario approva)
1. Blocchi piccoli senza rischio: V5, V8, V9, V10 (+ `xiccd` V12 se si decide).
2. V1 + V2 (+ V3 se approvata), in `child.c` e `session.c` di Ubuntu **a blocchi**, mai copiando file interi.
3. V7 (pacchetto), poi V4 dopo la misura del PATH.
4. Strumenti di prova (§3) e giro `all.sh lxqt` sulla VM Lubuntu; P7 e prove a mano sulla live Lubuntu 26.04.1.

## Riepilogo (max 15 righe, semplice)
1. Per LXQt/Lubuntu il codice di Ubuntu è già quasi pari a Fedora: i compositori X11 (picom), Bluetooth, «Lubuntu Update», il messaggio «compositor non installato», la fine-sessione detta subito, la sentinella, AppArmor e `needrestart` ci sono già. Lo studio del 25 nov lo dava per mancante: non è vero.
2. Mancano a Ubuntu soprattutto: la lingua del desktop remoto (oggi sempre inglese), i formati `LC_*`, il registro «chi ha chiuso la connessione», il controllo che l'aggancio «il locale chiude il remoto» ci sia a ogni avvio, la cache grafica nella cartella di root, i testi da correggere e una regola per gli aggiornamenti firmware.
3. Debian li ha già portati: per lingua, `LC_*`, registro, testi e regola firmware si può riusare il suo codice così com'è, con i percorsi di Ubuntu.
4. Attenzione: il pezzo di Debian che tiene viva la sessione (`--session-fd`) NON va portato su Ubuntu, che non ne ha bisogno; si lavora sempre a blocchi sul file di Ubuntu.
5. Il `PATH` con `~/.local/bin` su Ubuntu non cambia nulla se lo si porta così: va deciso dal proprietario dopo una misura su Lubuntu.
6. Chiusura per accesso locale su LXQt: nessun codice da cambiare; mancano le prove (con un vero Lubuntu e programmi aperti). Lubuntu usa X11 con openbox, quindi gli strumenti di prova di Debian e Fedora vanno adattati in modo proprio.
7. Cambi visibili da approvare: lingua e formati del desktop remoto (come su Fedora/Debian); eventualmente `~/.local/bin`.
8. Da tenere di Ubuntu e che Debian aveva tolto: `lubuntu-update`, i nomi Lubuntu, le cartelle `xdg-Lubuntu`, AppArmor per il kernel nuovo, `sudo-rs` e snap nelle prove.
9. Non verificato: la live Lubuntu 26.04.1 vera, `accountsservice`, `xiccd` e gli autostart su Lubuntu, se le VM Ubuntu bloccano il server come quelle Debian con la Radeon (prima controllare `amdgpu.runpm`).
10. Lavoro totale per LXQt: medio (una trentina di righe di prodotto da copiare, cinque file di pacchetto, un paio di strumenti di prova); il grosso sono le prove.
