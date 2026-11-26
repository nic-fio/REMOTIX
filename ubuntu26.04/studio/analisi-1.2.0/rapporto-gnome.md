# Rapporto di analisi GNOME (Ubuntu 26.04, GNOME 50.1, mutter 50.1, gdm3 50.1) — REMOTIX 1.2.0

Data: 26 nov 2026. Sola lettura: nessun file del prodotto toccato, nessun server, nessuna VM, nessuna compilazione.
Legenda: [V] verificato leggendo il codice di oggi (`diff` reale) o i documenti del repo; [D] dedotto; «non verificato» = nessuna misura
possibile qui (non ho potuto toccare macchine: tutte le versioni di GNOME 50 sono quelle misurate negli studi di Ubuntu del 18-19 nov,
`studio/1-gnome50-avvio.md`, `2-gnome50-chiusura-gdm.md`, `3-sessione-ubuntu.md`, `4-mutter50-cattura-input.md`, `12-verifiche-gnome.md`).
Percorsi: `U` = `ubuntu26.04/`, `D` = `debian13/`, `F` = `fedora45/`; i numeri di riga sono quelli di oggi.

## 0. Scoperte generali (valgono per tutte le voci sotto)

1. **Ubuntu è già quasi a 1.2.0 per tutto ciò che è GNOME.** `diff` Ubuntu↔Fedora in `src/`: 14 file; per GNOME restano SOLO
   (a) lingua/`LC_*` (`child.c`, `session.c`), (b) primo movimento del puntatore (`input.c`, 14 righe), (c) riga polkit fwupd (`remotix-remote-sessions.rules`),
   (d) il gancio PAM per scrittura/controllo a ogni avvio (`remotix-pam-hook`, `remotix.service`; solo per `.deb` va riscritto, vedi B1),
   (e) testi e log di connessione (`main.c`, `transport.c`). Tutto il resto delle differenze è KDE (KWin 6.8, `kwin.c`, `kdehost.h`, protocolli),
   SELinux/RPM (`walls.c`, `child.c` uscite 44-47, `Makefile -lselinux`, `remotix.pam`), compilazione del dconf con nomi fissi per l'etichetta
   SELinux (`session.c:1843-1906` di Fedora). [V: `diff -rq` e `diff` file per file.]
2. **Lo studio del 25 nov va corretto su quattro punti** (verificati sul codice di oggi):
   - «Debian è indietro rispetto a Ubuntu»: **non più vero.** Debian ha già portato da Ubuntu `mutter.c/h`, `capture.c/h`, sentinella («na»),
     `session_life()` a tre risposte, «fine sessione detta prima», «compositor non installato», scala GNOME (`mutter_scale_to_one`, `mutter.c:980`
     identico nei tre alberi [V `cmp`]), AppArmor `deny unix (bind, listen)`. Debian NON ha portato (per decisione del proprietario) il database dconf
     di sistema: lì il database a tre strati «di ripiego» resta il modello; Ubuntu tiene quello di sistema.
   - A3 «PATH come in locale, da portare così com'è, Ubuntu in parte»: su Ubuntu la voce è **inerte** (vedi voce 2): il ripiego di Fedora scatta solo
     se PAM non dà nessun `PATH`, e su Ubuntu `/etc/environment` lo dà sempre.
   - A8 «regola polkit fwupd, da portare»: su Debian l'azione **non esiste** in fwupd 2.0.20 (misurato); su Ubuntu non so, vedi voce 4.
   - B1 «controllo del gancio a ogni avvio»: Debian ha già scritto la versione `.deb` (script di 38 righe, `D/src/remotix-pam-hook`), si copia.
3. **Che cosa Ubuntu ha di diverso da Debian e DEVE restare** (sono i punti dove copiare un file intero da Debian rovinerebbe Ubuntu): vedi sezione S1.
4. **Che cosa di Fedora NON entra mai in Ubuntu GNOME:** SELinux (uscite 44-47 di `child.c`, `selinux/*`, `walls.c`), `authselect`/`remotix-pam-hook` di Fedora
   (file PAM di gdm copiati in `/etc/pam.d`), RPM/firewalld, `Environment=` d'unità specifici, `/etc/locale.conf`, `session.c` compilazione dconf con nomi fissi.
   Su Ubuntu l'aggancio «il locale chiude il remoto» è UNA riga in `common-session` messa da `pam-auth-update`, e tutti e 7 i file PAM di gdm3 50.1 la
   ereditano (`@include common-session`) [V `studio/2-gnome50-chiusura-gdm.md` §3.2-3.4].

---
## 1. Lingua del desktop remoto, `LC_*` e `LANGUAGE` (voci A1, A2, E4 dello studio)

1. **Che cosa è:** il desktop remoto parte nella lingua scelta dall'utente nelle Impostazioni (AccountsService), altrimenti in quella di sistema;
   anche `LC_*` e `LANGUAGE` di sistema arrivano alla sessione e a fine sessione tornano com'erano.
2. **Fedora:** `F/src/child.c:1603-~1703` (`struct child_locale`, `child_locale_name_ok/_value_ok`, `child_accounts_language`, `child_locale_read`),
   dichiarazione 1838, `envp[32]` a 1851, chiamata (2-quater, ancora da root, PRIMA del cambio di identità) 1983-1984, uso in `envp` 2068-2071;
   `F/src/session.c:3711-3715` (`LC_*`/`LANGUAGE` da `environ` in `compose_environment`) e `4798-4799` (nomi in `OUR_VARIABLES`).
3. **Ubuntu oggi: MANCA** [V]. Il figlio costruisce `envp[16]` (`U/src/child.c:1628`) con soli HOME/USER/LOGNAME/PATH/SHELL/XDG_RUNTIME_DIR/DBUS e
   `XDG_SESSION_ID` (1775-1825); nessun `LANG`; `session.c:3699` mette `LANG=<local_utf8()>` (1402-1440), che legge `g_getenv("LANG")` del figlio,
   vuoto: ripiego `C.UTF-8` (riga di registro «declared fallback»). `OUR_VARIABLES` (`session.c:4786`) ha solo `LANG`. Il file PAM ha già la riga giusta
   (`remotix.pam`, ultime righe: `pam_env.so envfile=/etc/default/locale`) [V]: il valore c'è nell'ambiente PAM e non lo si raccoglie.
4. **Debian:** portato a blocchi (non copiando `child.c`): `D/src/child.c:1594-1694` (identico a Fedora, solo il commento dice `/etc/default/locale`),
   dichiarazione 1717, `envp[32]` 1730, chiamata 1874-1876, uso 1959-1962; `D/src/session.c:2948-2951` e `4059-4060`. Aggiunta Debian nata dalle prove:
   `manager_set_locale()` (`D/src/session.c:3583-3615`, chiamata 3672) che passa la lingua anche al gestore utente, **solo per KDE, XFCE, LXQt**
   (su GNOME 48 `gnome-session` esporta da sé tutto il suo ambiente: misurato). Registro Debian F1.
5. **Che fare su Ubuntu: PORTARE (adattare poco).** I blocchi di Debian si applicano quasi senza modifiche, perché `child.c` Ubuntu↔Debian differisce
   solo per il fifo di sessione e per i commenti. Dettagli:
   - `child.c`: i 3 punti (blocco funzioni dopo `child_path_ok()`, chiamata dopo `pam_getenvlist`, copia in `envp` DOPO `XDG_SESSION_ID`), `envp[16]→[32]`
     (il tetto `ne < 14` del ciclo `XDG_SESSION_ID` resta com'è: `XDG_SESSION_ID` è già dentro prima delle voci di lingua, in Fedora e Debian è così).
   - `session.c`: 5 righe in `compose_environment` e 2 in `OUR_VARIABLES`.
   - **NON** portare `manager_set_locale` su GNOME (come Debian): su GNOME 50 il leader `gnome-session-init-worker` esporta l'ambiente al gestore
     (`OUR_VARIABLES` lo dice, `session.c:4786-4800`, misurato il 18 nov); che `LANG`/`LC_*` arrivino davvero a `gnome-shell` su GNOME 50 va misurato (su Fedora/GNOME 51
     arrivano: F34/F35).
   - Il file PAM non cambia (`/etc/default/locale` c'è già). Il commento «DEBIAN 13 ONLY» in testa a `remotix.pam` è residuo da correggere (voce di pulizia).
6. **Dimensione:** medio (~140 righe, tutte già scritte e riviste in Debian). **Rischio:** medio-basso (i tre punti di `child.c` stanno fra `fork` ed `exec`:
   un errore qui rompe ogni accesso; il revisore deve guardare i tre punti e il buffer `envp[32]`).
7. **Specificità di Ubuntu da verificare, NON presumere (non verificato):**
   - Le patch Ubuntu di gdm3 `dont_set_language_env` e `revert_override_LANG_with_accountservices` (`studio/2-gnome50-chiusura-gdm.md` §4.1) cambiano come
     il LOGIN LOCALE sceglie la lingua: la regola «remoto = login locale» va rimisurata su un accesso locale Ubuntu vero (che `LANG` ha `gnome-shell` dopo un
     login locale con lingua scelta in AccountsService, con e senza `LANGUAGE`).
   - `/var/lib/AccountsService/users/` (permessi, chiavi `Languages=`/`Language=`) su Ubuntu 26.04: nessuna misura qui. Debian ha misurato `root:root 0700` e che
     `SetLanguage` scrive `Languages=`; accountsservice di Ubuntu: stessa versione? non verificato.
   - Che `/etc/default/locale` sia ancora il file di sistema primario su 26.04 (e non `/etc/locale.conf`): non verificato.
   - Locali generati: su Ubuntu `locale -a` ha di serie pochi locali; con `it_IT.UTF-8` non generato `session.c` ripiega su `C.UTF-8` (come oggi): da provare con i
     language pack (E4: anche il caso `it_IT` senza codifica).
   - uutils/`LANGUAGE` in `/etc/default/locale`: l'installatore Ubuntu può scriverci `LANGUAGE`; passerebbe (nome ammesso).
8. **Prova:** utente con `SetLanguage it_IT.UTF-8` (`busctl`), sistema `en_US`, VM `ubuntu`: `/proc/<gnome-shell>/environ` e gestore utente `LANG=it_IT.UTF-8`; utente
   senza scelta: lingua di sistema; `LC_TIME` messo con `update-locale`/`localectl`; locale inesistente (il desktop deve partire lo stesso); con language pack,
   desktop visto in italiano. Confrontare col login locale gdm dello stesso utente.
9. **Cambia il comportamento visibile?** **SÌ** (serve l'OK del proprietario): oggi un utente italiano ha il desktop remoto in inglese (`C.UTF-8`); dopo, nella sua
   lingua; anche chi ha il sistema in inglese passa da `C.UTF-8` a `en_US.UTF-8` (ordinamenti, formati: piccolo ma reale). Decisione già presa su Fedora (23-25 nov) e
   regola «allineare = come Fedora».

---
## 2. `PATH` della sessione (voce A3)

1. **Che cosa è:** il `PATH` del desktop remoto uguale a quello di un login locale; il ripiego di Fedora aggiunge `~/.local/bin` e `~/bin`.
2. **Fedora:** `F/src/child.c:2028-2037`: se PAM non dà un `PATH` (Fedora non ha `/etc/environment`), ripiego `~/.local/bin:~/bin:/usr/local/bin:/usr/bin`;
   se PAM ne dà uno, resta quello.
3. **Ubuntu oggi:** `U/src/child.c:1573-1594` (`child_path_ok`) e 1790-1801: prende il `PATH` composto da `pam_env` da `/etc/environment`, che su Ubuntu contiene
   sbin, giochi e `/snap/bin` (misurato nei giri: `studio/giro1-gnome.md:30`: `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin`). Fallback fisso senza `~/.local/bin`.
4. **Debian:** portato il ripiego di Fedora (`D/src/child.c:1919-1928`); su Debian `/etc/environment` è vuoto, quindi il ripiego scatta (misurato: `PATH=/home/bc1/.local/bin:...`).
5. **Che fare su Ubuntu:** **non portare, o portare sapendo che non fa nulla.** Con il codice di Ubuntu, PAM dà sempre il `PATH` e il ripiego di Fedora non scatterebbe mai:
   è codice morto su Ubuntu. Il ripiego si può portare per uniformità del file (3 righe, uguale a Debian) ma NON ottiene l'effetto di Fedora (`~/.local/bin` nel `PATH`).
   Su Ubuntu in locale `~/.local/bin` arriva dal `~/.profile` dell'utente, che gnome-session 50 legge perché rilancia la shell di login (con `SHELL` valida); REMOTIX
   mette `SHELL=` vuoto per costruzione e **non legge `~/.profile`** (decisione D-F, `studio/11-riscontro-studi-lavoro.md:143`, `studio/1-gnome50-avvio.md` §6,
   `studio/3-sessione-ubuntu.md` §3.2). Quindi su Ubuntu la differenza locale/remoto sul `PATH` esiste già, non è quella di Fedora, e riguarda tutte le variabili di `~/.profile`.
6. **Dimensione:** piccola se solo il ripiego; media/da decidere se si vuole davvero avere `~/.local/bin` (nuova regola: es. anteporlo al `PATH` di PAM se la cartella esiste).
7. **Cambia il comportamento visibile?** Solo se si sceglie la regola nuova: **richiede decisione del proprietario** (non l'ho scelta io). Portare il solo ripiego: nessun effetto.
8. **Non verificato:** se su Ubuntu 26.04 un login locale GNOME ha `~/.local/bin` nel `PATH` (dipende da `~/.profile` dello scheletro e dall'esistenza della cartella).
9. **Prova:** confrontare `/proc/<gnome-shell>/environ` di un login locale e di uno remoto dello stesso utente con `~/.local/bin` esistente.

---
## 3. Primo movimento del puntatore inviato due volte (voce A4)

1. **Che cosa è:** il primo movimento assoluto dopo la (ri)partenza del dispositivo libei viene mandato due volte (difetto di mutter 51 misurato su Fedora: il primo clic cade sul bordo).
2. **Fedora:** `F/src/input.c:257` (campo `pointer_primed`), `1330` (azzeramento in `EI_EVENT_DEVICE_RESUMED`), `1940-1951` (blocco prima di `ei_device_pointer_motion_absolute`); il diff Ubuntu↔Fedora di `input.c` è esattamente queste 14 righe [V].
3. **Ubuntu oggi: MANCA.** `U/src/input.c:256` (struct), `1324-1330` (DEVICE_RESUMED, dopo `in->pointer_active = TRUE`), `1936` (singola chiamata). Il registro Ubuntu (E2, `docs/REGISTRO-problemi.md:335`) ha già «primo tocco da telefono su GNOME, saltuario»: Fedora (F34) lo attribuisce alla stessa causa; non provato su Ubuntu.
4. **Debian:** portata così com'è (`D/src/input.c:257, 1330, 1940-1951`); registro Debian F8; su mutter 48 «non misurato». In Debian `touch_announce_pointer` (client, `page.html`) convive: sono due rimedi diversi (uguali nei tre `page.html`: 4 occorrenze ciascuno).
5. **Che fare su Ubuntu: PORTARE COSÌ COM'È** (`input.c` Ubuntu e Debian differiscono solo nei commenti dconf: la toppa si applica senza adattamenti).
6. **Dimensione:** piccola (14 righe). **Rischio:** nessuno per l'utente (ripetere la stessa posizione è innocuo; il commento dice «da togliere quando mutter è corretto»).
7. **Prova:** `check-multiuser` (one-user, two-users) e `check-phone tap-click-portrait`, più volte (il difetto era saltuario); prima col 1.0.1 per vedere se su mutter 50 il difetto c'è, poi col 1.2.0. Gli strumenti non misurano la posizione del primo clic oltre `input/mouse-coordinates` e `phone/tap-click-*` (Debian lo dice); una prova a mano da telefono è la sola vera.
8. **Cambia il comportamento visibile?** Solo in meglio, se il difetto esiste; un movimento in più al primo invio.
9. **Non verificato:** se mutter 50.1 ha il difetto (misurato solo su mutter 51.0).

---
## 4. Regola polkit fwupd `refresh-remote` (voce A8)

1. **Che cosa è:** concede alle sessioni REMOTIX l'azione che GNOME Software chiede all'avvio per aggiornare i metadati del firmware (senza, una finestra di password copre il desktop).
2. **Fedora:** `F/src/remotix-remote-sessions.rules:79` (aggiunta alla lista `refresh`, righe 73-79), registro F3 (decisione del 14 nov: l'aggiornamento dell'elenco programmi vale per tutti gli utenti REMOTIX).
3. **Ubuntu oggi: MANCA** (`U/src/remotix-remote-sessions.rules:73-77`: solo Flatpak ×2 e `packagekit.system-sources-refresh`).
4. **Debian:** inserita (`D/src/remotix-remote-sessions.rules:76-79`) ma **inerte**: `pkaction` su fwupd 2.0.20 non ha `org.freedesktop.fwupd.refresh-remote` (misurato nella VM Debian, rapporto GNOME Debian; registro Debian F12).
5. **Che fare su Ubuntu: ADATTARE = portare come Debian (commento onesto) e MISURARE.** Una regola per un'azione inesistente non si attiva mai: innocua. Su Ubuntu serve la misura: `pkaction | grep fwupd` (versione di fwupd 26.04: **non verificato**) e se in una sessione remota GNOME compare una finestra polkit per un'azione fwupd.
   Specificità Ubuntu: `gnome-software.service` è nella sessione `ubuntu` (`studio/1-gnome50-avvio.md:197`, `Wants`), ma il «software center» di serie è App Center (snap) e il Firmware Updater è uno snap Flutter (`docs/STORIA-ubuntu-26.04.md:325`: snap `firmware-updater` su ubuntu, xubuntu, lubuntu): le azioni fwupd che chiedono possono essere altre.
6. **Dimensione:** piccola. **Rischio:** basso (è un'autorizzazione di sistema: dà alla sessione remota ciò che già ha chi siede al PC).
7. **Prova:** VM `ubuntu`, sessione remota nuova: nel registro di polkit nessun `BeginAuthentication`; `pkaction` come sopra.
8. **Cambia il comportamento visibile?** Concede un permesso in più alle sessioni remote (solo se l'azione esiste): **da dichiarare al proprietario** (Fedora lo ha già deciso, ma su Ubuntu l'azione potrebbe essere un'altra).

---
## 5. Controllo del gancio «il locale chiude il remoto» a ogni avvio del servizio (voce B1, criterio D4 «tutto automatico»)

1. **Che cosa è:** a ogni avvio del servizio si controlla che la riga di `remotix-local-login` sia ancora in `/etc/pam.d/common-session` e, se manca (un aggiornamento, una modifica a mano), si rimette; una riga nel registro.
2. **Fedora:** `F/src/remotix-pam-hook` (comando `check`, con `authselect`), `F/rpm/remotix.service:42` (`ExecStartPre=-…check`); dopo gdm in aggiornamento ci sono anche i trigger RPM (non servono su `.deb`).
3. **Ubuntu oggi: MANCA.** Solo un avviso in `postinst` (`U/debian/remotix.postinst:40-49`, `grep -q remotix-local-login`) e il controllo periodico di 5 s lato root. `prerm` toglie la riga PRIMA di fermare il servizio (`U/debian/remotix.prerm:57-64`).
4. **Debian:** script nuovo di 38 righe `D/src/remotix-pam-hook` (`check`: se la riga c'è, nulla; se no `pam-auth-update --package`, mai `--force`/`--enable`, sempre exit 0), installato da `D/debian/rules:84`, `D/debian/remotix.service:40-42` (`ExecStartPre=-`), `postinst:25-30` (cerca la riga vera `session…pam_exec.so…remotix-local-login` con `grep -E`), `prerm:67-75` (riga tolta DOPO l'arresto del servizio; prima un riavvio fra rimozione e arresto la rimetteva). Registro Debian F11.
5. **Che fare su Ubuntu: PORTARE COSÌ COM'È.** `pam-auth-update` di Ubuntu è identico a quello di Debian 13 [V, `studio/2-gnome50-chiusura-gdm.md` §3.5]; l'ordine della riga (dopo `pam_systemd`) è provato su Ubuntu in contenitore (§3.4). Lo script non usa niente di GNU-specifico (solo `grep -E`, `command -v`, `echo`).
6. **Dimensione:** media (1 file nuovo + 4 modifiche in `service`, `rules`, `postinst`, `prerm`). **Rischio:** basso-medio: tocca `/etc/pam.d` a ogni avvio; sicurezza data da «mai `--force`» ed exit 0. L'AppArmor del lato root non c'è (solo rete): nessun profilo da aggiornare.
7. **Prova:** togliere la riga a mano (`pam-auth-update --remove remotix`), riavviare il servizio: riga rimessa e riga di registro; modifica a mano di `common-session`: solo avviso; `apt remove` con servizio attivo: riga tolta e non rimessa; `apt upgrade` 1.0.1→1.2.0; P6 di `check-prelocal`.
8. **Cambia il comportamento visibile?** L'amministratore vede una riga di registro nuova a ogni avvio; il servizio può modificare `common-session` da solo (l'aggancio era già del pacchetto, ma messo solo a `configure`). **Da dichiarare** (criterio D4 già deciso su Fedora).

---
## 6. Cache Mesa di root (voce B2)

1. **Che cosa è:** la prova dei codec del lato root faceva scrivere a Mesa una cache in `/root/.cache`, che dopo `apt purge` restava; ora `MESA_SHADER_CACHE_DISABLE=true`.
2. **Fedora:** `F/rpm/remotix.service:39`. **Debian:** `D/debian/remotix.service:36-39` e `D/debian/remotix.postinst:38` (prova all'installazione con la variabile). **Ubuntu:** `U/debian/remotix.service` (manca dopo la riga 35), `U/debian/remotix.postinst:57` (manca).
3. **Che fare:** PORTARE COSÌ COM'È. Piccolo, rischio nullo (i desktop degli utenti tengono la loro cache: l'ambiente PAM è pulito). Prova: dopo `apt purge` nessun file in `/root`. Non verificato che Ubuntu lasci davvero quei file (stesso codice di Debian, che li ha visti).
4. **Visibile?** No (solo pulizia, principio «purge pulito»).

---
## 7. Testi dei messaggi (voci A9, B3)

1. `U/src/main.c:439-447` (commento) e `466-473` (messaggio «servizio PAM mancante») citano ancora «Fedora and Arch… `.fedora`, `.suse`, `.arch`». Fedora lo ha riscritto (`F/src/main.c:469-472`); Debian: `D/src/main.c:439-443`, `465-468` («reinstall the package from its file (sudo apt install --reinstall ./remotix_<version>_amd64.deb)»).
2. **PORTARE come Debian** (testo identico e già riveduto). Piccolo. Non cambia il comportamento, solo il testo mostrato all'amministratore. (I tre messaggi `RX-KDE-001/002/003` di `kwin.c` sono KDE: li guarda l'altro agente.)

---
## 8. «Perché la connessione si è chiusa» nel registro (voce A5) — comune, qui solo per l'effetto su GNOME

`F/src/transport.c:952-1110`, `2184`, `2589` (chiamata `close_why`); `D/src/transport.c` è identico a Fedora (`diff` vuoto) [V]; `U/src/transport.c` ha 151 righe di differenza. Nessun effetto particolare su GNOME (log). PORTARE COSÌ COM'È (piccolo). L'API è quella di ngtcp2 1.25, già nel pacchetto Ubuntu (`Static-Built-Using: ngtcp2 (= 1.25.0)`). Prova: chiudere il browser con e senza saluto, guardare le righe `farewell`/`idle timeout (silence)` (Debian le ha viste).

---
## 9. Chiusura GNOME per accesso locale: «ultima difesa» (voce E1) e `force_guard_on` (E2)

1. **Che cosa è:** su KDE, se la chiusura gentile non finisce quando un utente fa il login locale, c'è una rete di sicurezza lato root (`kdehost_stop`); su GNOME no.
2. **Ubuntu oggi (identico a Fedora e Debian per GNOME) [V]:** `really_terminate()` (`U/src/session.c:5555`): `exit_gnome(1)` (`Logout(1)`, 5645) + `wait_until_done()` 10 s (`WAIT_EXIT_MS`, 108), poi, se `force_refused()` (5545) non lo vieta, `exit_gnome(2)` (5655) + altri 10 s; il lato root tiene il login locale `PL_GRACE_MS` = 13 s (`U/src/rootside.c:2428`), poi chiude lo scope. `kdehost_stop` solo KDE (`child.c:9978`, 10039, 10108, 12658).
3. **Fedora:** nessuna modifica a GNOME (decisione del proprietario: «sistemiamo solo KDE»); messo da parte (registro F36 «Resta»); GNOME su macchina vera con gdm 51: OK. **Debian:** non costruita; misurata su GNOME 48 in VM con un inibitore di logout vero (`gnome-session-inhibit`): `Logout(1)` non chiude (finestra 60 s), `Logout(2)` sì in <1 s: caso peggiore ~10,5 s < 13 s. Provata a mano dal proprietario sulle live: GNOME OK (registro Debian H4).
4. **Che fare su Ubuntu: NON PORTARE nulla (come Fedora e Debian), ma PROVARE su GNOME 50.** Su GNOME 50 non c'è alcuna misura con inibitore: gnome-session 50 ha cambiato struttura (leader `gnome-session-init-worker`, `gnome-session-manager@.service`) e, nella 50.1, `Logout(2)` non è stato provato. Non costruire l'«ultima difesa» senza un guasto visto; per di più su GNOME la Shell ha `RefuseManualStop` (uno `StopUnit` verrebbe rifiutato; Debian lo ha misurato su 48; su 50 non verificato).
5. **E2 `force_guard_on`:** codice identico nei tre alberi; resta acceso dopo una chiusura fallita (`session.c:5536-5550`). Portare = nulla da fare, stesso comportamento di Fedora; annotare nel registro. Nessun effetto particolare su GNOME.
6. **Dimensione:** nessun codice; la prova è media. **Rischio della prova:** P7 riavvia gdm3 nella VM con la Radeon passata: **su Debian (kernel 6.12) questo ha bloccato il server 4 volte** per il `runpm` di amdgpu (registro Debian G1); la causa NON è stata dimostrata per un guest Ubuntu (kernel 7.0), ma conviene mettere `amdgpu.runpm=0` anche nelle VM Ubuntu prima di dare loro la scheda [D, prudenza].
7. **Cambia il comportamento visibile?** No (non si cambia nulla).
8. **Non verificato:** il comportamento di `Logout(1)/(2)` con inibitore su GNOME 50.1 (inclusi gli inibitori dell'estensione `ubuntu-dock`, ipotesi di `studio/2-gnome50-chiusura-gdm.md` §9.5); P8 per GNOME resta BLOCKED (nessun editor semplice senza interazione).

---
## 10. Strumenti di prova (`prove/`) che riguardano GNOME

| Che cosa | Fedora | Debian (portato) | Ubuntu oggi | Fare |
|---|---|---|---|---|
| `check-prelocal.py` P7 (terminale con `top`) e P8 (editor non salvato; GNOME: BLOCKED) | `F/prove/check-prelocal.py` (609 righe) | `D/prove/check-prelocal.py` (627 righe) | 334 righe, solo P1-P6 [V] | portare da Debian e adattare (sotto) |
| `unit_residue` (non conta come residuo una `.slice` vuota o un `.socket`) | no | `D/prove/check-prelocal.py:191-210`, nato da un FAIL dello strumento su GNOME 48: restavano `app-gnome-session-manager.slice`, `app-org.gnome.Terminal.slice` vuote e `gnome-keyring-daemon.socket` | no | portare; probabile identico su Ubuntu ([D], da misurare) |
| `check-apparmor.py` + `Box.apparmor()` in `lib.py:173-215` + `all.sh` (6, 19, 60-61, 76-78) | no (SELinux: `ausearch`) | sì | no | portare così com'è: su Ubuntu l'AppArmor controlla DAVVERO i socket (kernel 7.0; C4), quindi il controllo vale più che su Debian |
| `check-exit.py`, `hold.py`, `hold-user.py`, `prelocal.sh` | sì | sì (copie) | no | portare (generici; porte e utenti da adattare) |
| controllo core dump con `coredumpctl` | sì | «non installato → detto, non dichiarato» | no | adattare: Ubuntu tiene i core con `apport`, non `systemd-coredump` [D, non verificato]; installare `systemd-coredump` nelle VM come ha fatto Debian (decisione del proprietario) |

**Adattamenti per Ubuntu GNOME di P7:** display manager `gdm3` (`DM["gnome"]`), file di autologin `/etc/gdm3/custom.conf` (Ubuntu: `studio/8-pacchetto-e-prove.md:243`; Debian usa `daemon.conf`; per gdm3 50.1 **non verificato**, controllare nella VM), terminale GNOME di Ubuntu **ptyxis** (`U/prove/check-desktop.py:62`; Fedora ha già la lista `ptyxis -s -x top`, `ptyxis -s -- top`), sessione `ubuntu` (non `gnome`). Per un P7 che davvero costringa la strada forzata su GNOME serve un programma che trattenga il logout (per esempio `gnome-session-inhibit --inhibit logout …`): `top` in un terminale su Debian GNOME si chiudeva da solo in 0,87 s (la strada forzata non è girata). Gli script nuovi di Debian usano `date -d @N`, `find -exec cat`, `awk`: Ubuntu 26.04 ha uutils coreutils e `sudo-rs` (`check-desktop.py` Ubuntu è già adattato per `sudo-rs`); l'effetto sugli script nuovi è **non verificato**.
**Dimensione:** media. **Rischio:** solo di strumento (FAIL = prodotto; BLOCKED = strumento non ha potuto guardare). **Visibile?** No.

---
## 11. Voci dello studio che NON toccano GNOME su Ubuntu (verificato)

- C1-C10 (SELinux, RPM, firewalld, authselect, RPM Fusion): non si portano. L'equivalente Ubuntu c'è già (AppArmor, `pam-auth-update`, `ufw`).
- C7 aggancio per display manager: su gdm3 nulla da fare [V]: tutti i 7 file PAM includono `common-session` (§3.2 dello studio 2 di Ubuntu). Resta «provato dal proprietario sulla live» (A2 del registro).
- D1-D4 (KWin 6.8, `--virtual`, `kde_output_management_v2`, plasmalogin): KDE.
- A6, A7 (KDE: chiusura forzata e 5 s): KDE (`session.c:4588-4610`, 5639 di Fedora).
- U1-U13 (database dconf di sistema, «compositor non installato», fine sessione detta prima, scala GNOME 50, sentinella, AppArmor…): **già in Ubuntu** (sono nate lì); Debian le ha già ricevute (tranne U1/U13 per scelta).

---
## S1. Che cosa Ubuntu ha e Fedora (o Debian) no e DEVE restare

(Per GNOME; confermato con `diff`: dove Ubuntu e Fedora differiscono in `session.c`/`child.c` non c'è nulla di GNOME oltre ai punti 1-2 qui sopra.)
1. **Database dconf di sistema `/etc/dconf/db/remotix`** con profilo in `$XDG_RUNTIME_DIR/dconf/profile`, `system-db:remotix` + `user-db:remotix`
   (`~/.config/dconf/remotix`, tolto al purge): `session.c:1718-1745` (`DCONF_KEYS`, con `ubuntu-lock-on-suspend`, `scaling-factor`), `1774-1815`
   (`session_dconf_keyfiles_write`), `1825-1906` (`session_dconf_system_db_ensure`, variante con nome temporaneo `remotix.new.<pid>` + `rename`: la
   variante a nomi fissi di Fedora è solo per l'etichetta SELinux e NON si copia), `1970` (`dconf_runtime_mode`), `rootside.c:3344`, `main.c --dconf-keyfiles`,
   `debian/rules` (genera i keyfile), `postinst` (compila), `postrm` (toglie). Motivo: programmi Flutter e snap (Firmware Updater, Security Center, installatore)
   non digeriscono `DCONF_PROFILE` (registro C5). Debian non lo ha: NON copiare file `session.c` da Debian.
2. **Avvio della Shell di GNOME 50:** `SESSION_UNIT_SHELL_MODEL = org.gnome.Shell@.service` (`session.h:118`, `session.c:3760-3791`, 4951) con `--mode=%i` (la modalità `ubuntu`),
   `AssertEnvironment=XDG_SESSION_TYPE=wayland` (`session.c:3632`), attesa anche di `graphical-session.target` (`inactive_unit`). Debian ha il ramo GNOME 48 (`SESSION_UNIT_SHELL_48`): non copiare.
3. **Sessione `ubuntu`** (D8: criterio `ID` di os-release; `desktop_session()` aggiunge `ubuntu`), `XDG_CURRENT_DESKTOP=ubuntu:GNOME`.
4. **`child_path_ok()` e `PATH` da PAM** (`child.c:1573-1594`, 1790-1801): su Ubuntu serve (snap); su Debian è inerte.
5. **Niente fifo di sessione `--session-fd`** (`logind` 259 usa il pidfd: `child.c:1738-1746`). Debian ne ha bisogno (logind 257) e lo tiene: NON copiare quel blocco da Debian (`D/src/child.c:1840-1868`, 2076-2081, 10369-10387).
6. **Notifica «Screen Lock disabled»:** creazione/rimozione di `~/.local/share/gnome-shell/lock-warning-shown` (`session.c:2049-2150`, 2724-2768). Fedora lo ha (identico); **Debian NO** (0 occorrenze) e non è nell'analisi di Debian: GNOME 48 su Debian potrebbe mostrare la notifica la prima volta di ogni utente (non verificato; segnalo per completezza, non è lavoro di Ubuntu).
7. **Variabili del gestore utente in `OUR_VARIABLES`** per GNOME 50 (`GNOME_DESKTOP_SESSION_ID`, `QT_IM_MODULE(S)`, `XMODIFIERS`, `session.c:4786-4800`): quattro nate con linger acceso.
8. **AppArmor del lato rete:** percorsi `xkeyboard-config-2`, `/etc/xkb` (xkb-data 2.46) e la riga `deny unix (bind, listen)` (C4): restano; la riga `org.kde.remotix.desktop r` è KDE (Debian F10; la guarda l'altro agente).
9. **`needrestart`** (`debian/needrestart/remotix.conf`) e `remotix-no-suspend.conf`: già uguali a Debian.
10. **Prove:** `ptyxis`, `sudo-rs`, `package-snap.py`, `.config/dconf/remotix` nella lista del purge (`check-desktop.py:62, 309-311, 367`).
11. **Gdm 50.1 «Force Stop»** (uccide con `TerminateSession` anche la sessione REMOTIX) e `graphical-session.target` come condizione di nascita: comportamento di Ubuntu, nessuna modifica; da non toccare.

---
## S2. Punti in cui portare la voce CAMBIA il comportamento visibile su Ubuntu (da far approvare al proprietario)

1. **Lingua e `LC_*`/`LANGUAGE`** (voce 1): il desktop remoto passa da inglese `C.UTF-8` alla lingua dell'utente/di sistema. Decisione già presa su Fedora, ma su Ubuntu `gdm3` ha patch di lingua proprie (verificare che il login locale si comporti come immagino). **Sì, visibile.**
2. **`PATH`** (voce 2): nessun cambiamento se si porta solo il ripiego; se si vuole `~/.local/bin` come in locale, **è una regola nuova** (e riguarda anche le altre variabili di `~/.profile`, D-F).
3. **Regola polkit fwupd** (voce 4): permesso in più alle sessioni remote, se l'azione esiste su Ubuntu.
4. **Controllo del gancio a ogni avvio** (voce 5): il servizio può riscrivere `common-session`; riga di registro nuova.
5. **Nessun cambiamento visibile, solo correttezza/pulizia:** puntatore (voce 3, solo in meglio), Mesa (6), testi (7), registro di connessione (8), ordine in `prerm` (voce 5), prove (10).
6. **Versione 1.2.0, licenze, manuali, sito:** comuni a tutti i desktop, non analizzati qui; per GNOME i manuali devono dire: lingua, `PATH`, aggancio controllato, e (se non misurato) «non provato su GNOME 50».

---
## S3. Che cosa NON ho potuto verificare (scritto «non verificato», mai supposto)

- Qualunque comportamento a runtime con il prodotto: lingua su gnome-shell 50.1; primo clic su mutter 50.1; chiusura `Logout(1)/(2)` con inibitore su gnome-session 50.1; P7 su GDM 50.1 con autologin; scala 2 con 1.2.0 (su Ubuntu la scala è già blindata da `scaling-factor` bloccato + `mutter_scale_to_one`, 1.0.0 non rimisurato qui).
- Versione di fwupd e azioni polkit di Ubuntu 26.04; se `gnome-software` è installato nelle immagini live Ubuntu.
- Permessi e chiavi di `/var/lib/AccountsService/users/` su Ubuntu; se `/etc/default/locale` è il file primario su 26.04; effetto delle patch gdm `dont_set_language_env` / `revert_override_LANG_with_accountservices` sulla lingua del login locale.
- `/etc/gdm3/custom.conf` come file di autologin per gdm3 50.1 (lo studio 8 lo dice per Ubuntu; non l'ho riverificato).
- Se Ubuntu lascia file in `/root/.cache` (Mesa) senza la variabile; se Ubuntu ha `coredumpctl` utile (apport) nelle VM; se `date -d @N` e simili funzionano con uutils.
- Se `~/.local/bin` è nel `PATH` di un login locale Ubuntu.
- Lo stato del server e delle VM Ubuntu (non mi sono collegato); se le VM Ubuntu con la Radeon soffrono dello stesso blocco `runpm` delle Debian.

## S4. Voci rimaste aperte per Ubuntu nei documenti di Debian (registro, sezioni F-H, e `PIANO.md`)

- **H1** `media/screen-updates` oltre soglia di poco su GNOME, KDE, LXQt (1,05-1,5 s contro 1,0 s) in Debian, causa non stabilita. Su Ubuntu 1.0.0 la voce era PASS (`studio/giro2-gnome.md`, 123 PASS su 124): il confronto 1.0.1 vs 1.2.0 sullo STESSO banco dirà se è una regressione del 1.2.0 o del banco Debian.
- **H2** `pkexec` su GNOME (SHELL vuoto, nessuna finestra): FAIL noto e voluto anche su Ubuntu (`desktop/users-shell-and-environment`).
- **H3** `kbd-not-producible` su Firefox in LXQt: non GNOME.
- **H4** P7/P8 automatiche solo su GNOME e vietate sulle altre VM per G1; il proprietario le prova sulle live: su Ubuntu la stessa decisione va presa.
- **H5** da verificare altrove: lingua utente su KDE di Fedora (non GNOME), `xiccd` su Xubuntu (non GNOME), `xfconfd` in XFCE.
- **F9** (AppArmor `deny unix`): «non provata su un kernel che li controlli»: Ubuntu 26.04 È quel kernel (C4 l'ha trovata proprio lì): Ubuntu ha già la misura, Debian no.
- **F13/C5** (database dconf di sistema): Debian lo dichiara «non portata»: su Ubuntu resta e la differenza va dichiarata nei manuali nel verso opposto.
- **F13/E3** (variabili del gestore utente: foto vecchia; «non ho potuto guardare» vale «chiuso») ed **E4** (scatti video da Chrome Android): nati su Ubuntu, restano aperti anche lì, non corretti.
- **G1** blocchi del server per `amdgpu runpm` nelle VM Debian; **G3** controlli nuovi nelle prove (AppArmor, `systemd-coredump`, purge pulito): per Ubuntu vedi voce 10.
- Decisioni del proprietario ancora aperte nel piano Debian: `systemd-coredump` nelle VM (poi sì, G3) e controllo rifiuti AppArmor (poi sì, G3).

---
## Riepilogo (linguaggio semplice)

1. Per GNOME, Ubuntu è già quasi alla 1.2.0: il lavoro nato su Ubuntu a novembre (database delle impostazioni di sistema, messaggi di fine sessione, scala dello schermo di GNOME 50, correzione di AppArmor) c'è già, e Debian lo ha già copiato.
2. Da Fedora mancano solo poche cose per GNOME: la lingua del desktop remoto, il primo movimento del puntatore, una riga di permessi per gli aggiornamenti del firmware, il controllo automatico del gancio «il locale chiude il remoto», una piccola pulizia della cache grafica di root, alcuni testi e il registro «perché la connessione si è chiusa».
3. Quasi tutto si porta copiando i pezzi già scritti e riveduti per Debian (stesso sistema dei pacchetti `.deb`); i pezzi di Debian che riguardano GNOME 48 o il vecchio meccanismo di sessione NON vanno copiati.
4. Il `PATH` con `~/.local/bin` di Fedora, su Ubuntu non farebbe nulla (Ubuntu ha già un percorso dato dal sistema): se il proprietario lo vuole serve una regola nuova, che non ho deciso io.
5. La regola sui permessi del firmware su Debian non serve (l'azione non esiste lì): su Ubuntu va misurata prima di dire se serve.
6. «Ultima difesa» alla chiusura di GNOME: non costruirla (come Fedora e Debian), ma provare la chiusura con un programma aperto su GNOME 50, che nessuno ha ancora misurato.
7. Cambiano per l'utente solo: la lingua del desktop remoto (da inglese alla sua lingua), il permesso firmware, e il servizio che si rimette a posto da solo la riga PAM a ogni avvio: tutti e tre vanno approvati dal proprietario.
8. Gli strumenti di prova (P7/P8, controllo AppArmor, `hold`) vanno portati da Debian con piccoli adattamenti per Ubuntu (gdm3, terminale ptyxis, file di autologin).
9. Rischio principale: i tre punti di `child.c` fra `fork` ed `exec` per la lingua; per i banchi, mettere `amdgpu.runpm=0` nelle VM Ubuntu per prudenza (su Debian ha evitato blocchi del server).
10. Non verificato: tutto ciò che richiede macchine (lingua su GNOME 50, primo clic, chiusura con inibitore, versione di fwupd, file di AccountsService, uutils).
