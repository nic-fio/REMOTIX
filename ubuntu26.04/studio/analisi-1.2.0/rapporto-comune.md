# Ubuntu 26.04 alla 1.2.0 — analisi della parte NON legata a un desktop

Studio di SOLA LETTURA del 26 nov 2026. Nessun file esistente toccato, nulla compilato, nessun collegamento al server.
Metodo: `diff` reale file per file fra `ubuntu26.04/`, `fedora45/` e `debian13/` (`diff -rq` per l'elenco, poi lettura dei blocchi),
`cmp` per i file identici, `grep` per verificare ogni affermazione dello `STUDIO-1.2.0-differenze.md` e del
`PIANO-1.2.0-debian-ubuntu.md` del 25 nov. Le righe citate sono del file nominato nella colonna o nel testo; dove scrivo
«non verificato» non l'ho potuto controllare (niente macchina, niente server).

Sigle: U = `ubuntu26.04/`, F = `fedora45/`, D = `debian13/`. «Comune» = lo analizzo io; GNOME/KDE/XFCE/LXQt = altri quattro agenti.

## 0. Scoperta principale: lo studio del 25 nov va corretto

Lo studio diceva «Debian è indietro rispetto a Ubuntu». Oggi è il contrario per la parte 1.2.0, e per Ubuntu il lavoro è molto
più piccolo di quanto la classificazione A-E lasciava credere:

1. **Quasi tutto il codice «nuovo» di Debian 1.2.0 che non viene da Fedora è già in Ubuntu** perché Debian lo ha preso da Ubuntu.
   `cmp` dice che sono IDENTICI fra U, D e F: `capture.c`, `capture.h`, `mutter.c`, `mutter.h`, `sentinel.c`, `webtransport.c`,
   `rcp.c`, `rcp.h`, `page.html`, `keyboard.c`, `local_login.c`, `walls.c` (U = D), ecc.: tutti i file di `src/` che NON compaiono
   nelle due tabelle del §1. Quindi in Ubuntu ci sono già: fine della sessione detta subito (`wt_dismiss_user_session_over`),
   «compositor non installato» (`session_missing_component`, `main.c:1173-1181`), scala di GNOME 50 (`mutter_scale_to_one`),
   fotogramma perso di KWin (`capture_frame_lost`, `kwin_poke`), servizio `org.freedesktop.ScreenSaver` (`kwin.c`), integrità del
   pannello XFCE (`xfce_panel_integrity`), autostart nascosti (`blueman`, `session.c:3257`), sentinella «na» (`sentinel.c:913`),
   Log Out di KDE (`session_kde_logout_watch`), `needrestart` (`debian/needrestart/remotix.conf`, `remotix.install:1`).
2. **Ubuntu differisce da Fedora in soli 14 file di `src/`** (tabella 1.A) e da Debian 1.2.0 in 12 (tabella 1.B).
3. La parte che resta da portare in Ubuntu e non è di un desktop è: lingua + `LC_*`; riga di registro sulla chiusura della
   connessione (`transport.c` intero); controllo dell'aggancio PAM a ogni avvio; cache Mesa; testi «reinstalla il pacchetto» e
   residui di testo; regola polkit fwupd; AppArmor (riga per `org.kde.remotix.desktop`); ordine in `prerm`; `check` della riga PAM
   nel `postinst`; versione; licenze; costruzione senza contenitori; banco (prove P1-P8, check-apparmor, script VM).
4. Il `PATH` (voce A3 dello studio) per Ubuntu è quasi un non-lavoro e **una decisione del proprietario** (vedi voce C3).
5. Tutto il resto di Fedora (SELinux, RPM, firewalld, authselect, KWin da solo, `kde_output_management_v2`) non si porta.
6. **Attenzione a non copiare da Debian il filo della sessione logind**: Debian (systemd 257) passa a `remotix-child` un
   descrittore `--session-fd` (`debian13/src/child.c:1717, 1840-1868, 2076-2081, 10369-10387`); Ubuntu (systemd 259.9) usa il
   pidfd e NON deve riceverlo (`ubuntu26.04/src/child.c:1738-1746`, commento «needs nothing to cross the execve»).

---

## 1. Tabelle dei file di `src/` che differiscono

Conteggio: righe che compaiono solo in U (`<`) e solo nell'altro (`>`), da `diff`; «blocchi» = hunk. Le attribuzioni ai desktop sono
fatte leggendo i blocchi (approssimate dove un hunk mescola più cose).

### 1.A Ubuntu contro Fedora (14 file diversi, 5 nuovi in F)

| File | solo U | solo F | blocchi | A chi appartiene la differenza |
|---|---|---|---|---|
| `child.c` | 12 | 333 | 18 | **Comune** ≈ 120 righe F (lingua `1603-1710`, uso `1838, 1851, 1983-1984, 2068-2071`, PATH `2028-2037`); **SELinux, non si porta** ≈ 125 (include `51-54`, uscite 44-47 `1144-1147`, `1711-1816`, `1975-1980`, `2193-2198`); **KDE (D)** ≈ 90 (`kde_refused` `5886`, `8997-9044`, `9217-9273`, `11663-11678`: KWin da solo) |
| `input.c` | 0 | 14 | 3 | **GNOME** (primo movimento del puntatore: `257`, `1330`, `1940-1951`) |
| `kdehost.h` | 13 | 44 | 7 | **KDE (D)**: marchi `--kwin-virtual` / `REMOTIX_KDE_HOST`; in U restano `remotix-kwin-host` / `--kwin-nested` e DEVONO restare |
| `kwin.c` | 3 | 522 | 5 | **KDE (D)** `1696-2212` (`kwin_virtual_alive`, `kwin_output_resize`); più 3 testi «reinstalla» (`814, 825, 842`) = **comune** |
| `kwin.h` | 0 | 17 | 1 | **KDE (D)** |
| `main.c` | 8 | 12 | 4 | **Comune**: testi `466-472` (PAM) e `1189-1190` (Recommends vs «weak dependency»: quello di U è giusto per apt); KDE: `2885-2891` (`--kwin-virtual`) |
| `Makefile` | 2 | 5 | 3 | KDE (D) protocolli `291-298` e **SELinux** `-lselinux` `322`: nessuno dei due si porta |
| `remotix.pam` | 104 | 51 | 14 | **Comune ma non portabile**: il file di F è per authselect/`/etc/locale.conf`; quello di U è già `sshd` + `pam_env envfile=/etc/default/locale` (giusto) |
| `remotix-remote-sessions.rules` | 1 | 4 | 1 | **Comune**: regola fwupd `76-79` |
| `session.c` | 62 | 75 | 30 | **Comune** ≈ 7 righe F (`3711-3715` `LC_*`, `4798-4799` `OUR_VARIABLES`); **KDE** ≈ 70 (`113` 5 s, `3930-3956` KWin da solo, `4561-4581` `wait_until_done_ms`, `4588-4610` `graphical-session.target`, `5639-5648`); **SELinux/RPM, non si porta** ≈ 80 (compilazione dconf in `/run/remotix` `1843-1906`, testo `dconf` invece di `dconf-cli` `1866, 2482`) |
| `transport.c` | 8 | 143 | 8 | **Comune**: riga «perché si è chiusa la connessione» (`955-1080`, uso `1090-1105`, `2187-2189`, `2592-2600`) |
| `walls.c` | 2 | 94 | 4 | **SELinux, non si porta** (`260-348`); 2 righe di commento |
| `protocols/kde-output-*.xml`, `README-kde-output.txt` | — | file nuovi | — | KDE (D), non si porta |
| `remotix-pam-hook` | — | file nuovo (335 righe) | — | **Comune** ma di F è per authselect/sddm/plasmalogin: **non si porta**; si porta la versione di D (37 righe, voce C5) |

Identici fra U e F (e quindi niente da fare): tutti gli altri file di `src/`, compreso `page.html`, `rootside.c`, `session.h`,
`mutter.c`, `capture.c`, `sentinel.c`, `webtransport.c`, `rcp.c`, `local_login.c`.

### 1.B Ubuntu contro Debian 1.2.0 (12 file diversi, 1 nuovo in D)

| File | solo U | solo D | blocchi | A chi appartiene |
|---|---|---|---|---|
| `child.c` | 34 | 188 | 20 | **Comune** (lingua, PATH: stesso codice di F, `D 1594-1694, 1717, 1730, 1874-1875, 1919-1928, 1959-1962`); **specifico di D, NON si porta**: fifo della sessione logind (`D 1840-1868, 2076-2081, 10369-10387`); commenti sul modello dconf (GNOME, U) |
| `input.c` | 6 | 17 | 6 | **GNOME**: `pointer_primed` (D `257, 1330, 1946-1951`); le 6 righe di U sono commenti sul database dconf (restano) |
| `kwin.c` | 19 | 12 | 9 | **KDE**: nostro labwc (`REMOTIX_LABWC`, `access(...)`) contro `labwc` del PATH: resta di U; **comune**: 3 testi «reinstalla» (D `810, 820, 837`) |
| `main.c` | 16 | 7 | 4 | **Comune**: testi `439-447, 466-473` (D li ha riscritti); GNOME: U ha `--dconf-keyfiles` (`2862-2865`), resta |
| `Makefile` | 6 | 0 | 1 | **KDE**: `LABWC ?= /usr/libexec/remotix/labwc` `128-133`, resta di U |
| `remotix.pam` | 9 | 6 | 3 | **Comune**: solo commenti (intestazione «DEBIAN 13 ONLY», cenni a Fedora/openSUSE/Arch `6, 30-40`); è un conffile |
| `remotix-remote-sessions.rules` | 1 | 4 | 1 | **Comune**: regola fwupd (D `76-79`) |
| `rootside.c` | 1 | 0 | 1 | **GNOME**: `session_dconf_system_db_ensure()` `3344`, resta di U |
| `session.c` | 1050 | 233 | 125 | **GNOME** quasi tutto (database dconf di sistema, unità `org.gnome.Shell@.service` di GNOME 50, 800+ righe di U che restano); **comune/desktop di D da portare**: `manager_set_locale` (D `3585-3640`, chiamata `3672`), KDE 5 s e `graphical-session.target` (D `113, 3822-3840, 3870, 4890-4899`), `LC_*` (D `2951, 4059`), `xiccd` (XFCE, D `2505-2511`) |
| `session.h` | 35 | 23 | 10 | **GNOME**: dichiarazioni dconf/Shell di U restano; D aggiunge `SESSION_UNIT_GRAPHICAL` (U lo ha già, `session.h:118-120`) |
| `transport.c` | 8 | 143 | 8 | **Comune**: D = F byte per byte (`cmp`), da prendere intero |
| `remotix-pam-hook` | — | nuovo (37 righe) | — | **Comune**: controllo dell'aggancio (voce C5) |

Identici fra U e D: `capture.c`, `mutter.c`, `walls.c`, `sentinel.c`, `webtransport.c`, `page.html`, `local_login.c`, `rcp.c`, `child.h`, ...

---

## 2. Voci comuni, una per una

Formato: **che cosa è** — Fedora (file:righe) — Ubuntu oggi — Debian — che cosa fare — dimensione/rischio — come provarla.
Numerazione C1... (comune); la classificazione dello studio del 25 nov è fra parentesi.

### C1 (A1+A2). Lingua e formati del desktop remoto
- **Che cosa è:** il desktop remoto parte nella lingua scelta dall'utente nelle Impostazioni (AccountsService), altrimenti in quella di sistema, più i formati `LC_*` e `LANGUAGE`; oggi parte sempre in `C.UTF-8`/inglese.
- **Fedora:** `child.c:1603-1710` (`child_locale_*`, `child_accounts_language` letta da root PRIMA del cambio d'identità), chiamata `1983-1984`, uso `2068-2071`, `struct child_locale locale` `1838`, `envp[32]` `1851`; `session.c:3711-3715` (`LC_*`/`LANGUAGE` nell'ambiente), `4798-4799` (`OUR_VARIABLES`, ripristino a fine sessione). Registro F34, F35 M/N.
- **Ubuntu oggi: MANCA.** `child.c:1628` `envp[16]`, nessuna lettura di AccountsService; `session.c:3699` mette sempre `LANG=%s` da `local_utf8()` (`1406` ripiego `C.UTF-8`); `session.c:4786` `OUR_VARIABLES` senza `LC_*`. La fonte di sistema c'è già: `remotix.pam` (ultima parte) ha `pam_env envfile=/etc/default/locale`, quindi `pam_environment` porta già `LANG`/`LC_*`/`LANGUAGE` di sistema.
- **Debian:** portato a blocchi, identico a F salvo il nome del file: `child.c:1594-1694` (blocco), `1717, 1730, 1874-1875, 1959-1962`; `session.c:2951, 4059`; commento «`/etc/default/locale`» al posto di `/etc/locale.conf`. In più (solo D, non in F) `manager_set_locale` (`session.c:3585-3640`, chiamata `3672`): la lingua entra anche nel gestore utente di systemd per KDE, XFCE, LXQt; a fine sessione torna com'era, nella chiusura «leggera» resta di proposito (registro F1, `debian13/docs/REGISTRO-problemi.md:240-256`). Misurato su GNOME e XFCE/LXQt; su KDE la lingua segue `plasma-localerc` dell'utente.
- **Fare su Ubuntu:** portare così com'è il blocco di D (stesso `child.c` di U salvo i punti sotto). Le tre inserzioni in `child.c` di U: dopo `1594` (fine di `child_path_ok`), `envp[16]`→`32` a `1628`, struct locale a `1615`, passo «2-quater» dopo `1751`, e due righe `envp` dopo `1825`. `session.c:3699` e `4786`. **`manager_set_locale` di D: portarla solo se Kubuntu/Xubuntu/Lubuntu mostrano lo stesso sintomo (misurare: la lingua nel gestore utente `systemd --user` su KDE, XFCE, LXQt); è di competenza degli agenti dei desktop, ma è una funzione comune.** Non copiare il resto di `child.c` di D (fifo logind).
- **Dimensione/rischio:** medio / medio. Il rischio è in `child.c`: l'inserzione fra `fork` ed `exec` (una graffa mancante è già stata trovata nella revisione di D, registro F2).
- **Come provarla:** utente con scelta in AccountsService (`busctl … SetLanguage it_IT.UTF-8`), utente senza scelta, sistema in `it_IT`, locale NON generato sul sistema (il desktop deve partire lo stesso con `C.UTF-8`: Ubuntu live ha pochi locale generati), `LC_TIME` di sistema, `LANGUAGE=it:en`; leggere la lingua DENTRO i processi del desktop (non solo del figlio), su almeno un desktop per variante. Non verificato su Ubuntu: dove stia `LANGUAGE` in `/etc/default/locale` e se le virgolette di quel file passino bene da `pam_env` (D lo ha misurato su Debian, non su Ubuntu).

### C2 (A5). Riga di registro sul perché si è chiusa una connessione
- **Cosa è:** una riga che dice chi ha chiuso la connessione QUIC (alert TLS, silenzio, handshake) e perché; non cambia nessun comportamento.
- **Fedora:** `transport.c:955-1080` (`tls_alert_name`, `transport_error_name`, `close_why` `1021`), uso `1090-1105`, `2187-2189`, `2592-2600`. Registro F23, F31, F33 I.
- **Ubuntu oggi: MANCA** (`grep close_why` vuoto). Ubuntu `transport.c` = vecchio.
- **Debian:** `debian13/src/transport.c` è **identico a `fedora45/src/transport.c`** (`cmp`). Registro D F12.
- **Fare:** sostituire `ubuntu26.04/src/transport.c` con quello di D/F (le 3 modifiche nei punti di chiamata più un blocco nuovo; nessun altro cambio in U: i soli blocchi diversi sono i 143 righe di F e 3 punti). Usa l'API di ngtcp2 1.25, la stessa che U già costruisce (`Static-Built-Using: ngtcp2 1.25.0`).
- **Dimensione/rischio:** piccolo / basso (solo registro).
- **Prova:** compilazione; una connessione chiusa dal browser e una lasciata in silenzio, leggere la riga nel `journalctl -u remotix`.

### C3 (A3). `PATH` come in un accesso locale
- **Cosa è:** se PAM non dà un `PATH`, il ripiego include `~/.local/bin:~/bin`.
- **Fedora:** `child.c:2028-2037` (`fallback[400]`).
- **Ubuntu oggi: DIVERSO.** `child.c:1790-1800`: il `PATH` viene da `pam_env` (`/etc/environment` di Ubuntu: `/usr/local/sbin:...:/snap/bin`), controllato da `child_path_ok()` (`1573-1592`); il ripiego `/usr/local/bin:/usr/bin:/bin` scatta solo se PAM non ne dà. La nota di F (registro F34) dice che su Ubuntu «il `PATH` coincide col locale grazie a `/etc/environment`».
- **Debian:** portato come F (`child.c:1919-1928`) perché `/etc/environment` di Debian è vuoto (commento `D 1573`).
- **Fare su Ubuntu:** **non portare il ripiego (non serve: PAM dà sempre un `PATH`).** Se il proprietario vuole `~/.local/bin` e `~/bin` anche su Ubuntu serve un cambio diverso (anteporli al `PATH` di PAM se la cartella esiste): è un cambio di comportamento visibile → domanda al proprietario. Lo studio `11-riscontro-studi-lavoro.md:143` registra «`~/.profile` di Ubuntu aggiunge `~/.local/bin`: DECISO D-F, non letto, come Debian».
- **Dimensione/rischio:** nullo (non portare) o piccolo/basso (se deciso).
- **Prova (se deciso):** programma in `~/.local/bin` lanciato da un terminale del desktop remoto, `echo $PATH` uguale a quello del terminale nel desktop locale dello stesso utente (non verificato che coincida su Ubuntu: dipende da `~/.profile` e dal modo in cui gdm avvia la sessione).

### C4 (A8). Regola polkit per fwupd
- **Cosa è:** concede alle sessioni REMOTIX `org.freedesktop.fwupd.refresh-remote`, altrimenti finestra di password sul desktop GNOME (gnome-software aggiorna i metadati del firmware all'accesso).
- **Fedora:** `remotix-remote-sessions.rules:76-79`.
- **Ubuntu oggi: MANCA** (`src/remotix-remote-sessions.rules:76`, l'elenco finisce con `...system-sources-refresh`).
- **Debian:** `debian13/src/remotix-remote-sessions.rules:76-79`, identica a F; su Debian 13 non fa nulla (fwupd 2.0.20 non ha l'azione), «innocua, non vista in azione» (registro F12).
- **Fare:** portare così com'è (4 righe). Il file è nel pacchetto; i test `power-implied`/`power-local-seat` sulle 19 azioni restano.
- **Dimensione/rischio:** piccolo / basso. Non verificato: se fwupd di Ubuntu 26.04 ha quell'azione e se il Centro software di Ubuntu (snap) la richiede.
- **Prova:** `pkaction --action-id org.freedesktop.fwupd.refresh-remote` sulla macchina; accesso remoto su Ubuntu GNOME e osservare se compare la finestra di password al primo accesso.

### C5 (B1). Controllo dell'aggancio «il locale chiude il remoto» a ogni avvio
- **Cosa è:** a ogni avvio del servizio un controllo verifica che la riga PAM di `remotix-local-login` sia ancora in `common-session`, la rimette a posto se manca e lo scrive nel registro; non impedisce mai l'avvio.
- **Fedora:** `rpm/remotix.service:42` (`ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check`), `src/remotix-pam-hook` (335 righe, authselect/sddm/plasmalogin: **non portabile**), `rpm/remotix.spec:158, 253, 338`.
- **Ubuntu oggi: MANCA** il controllo periodico a ogni avvio. C'è solo l'avviso nel `postinst` (`debian/remotix.postinst:44-49`) e il controllo periodico di 5 s del programma. L'aggancio in sé (`remotix.pam-config`, `pam-auth-update`) è identico a quello di D (`cmp`).
- **Debian:** nuovo script di 37 righe `debian13/src/remotix-pam-hook` (controlla `^\s*session\s.*pam_exec\.so.*remotix-local-login` in `/etc/pam.d/common-session`; se manca `pam-auth-update --package` non interattivo; mai `--force`/`--enable`; esce sempre 0), installato da `debian13/debian/rules:84`, chiamato da `debian/remotix.service:42` (`ExecStartPre=-`). Se l'amministratore ha modificato a mano il file, `pam-auth-update` rifiuta e resta solo la riga di avviso (registro F11).
- **Fare su Ubuntu:** **portare così com'è** (file `src/remotix-pam-hook`, riga in `rules`, due righe nell'unità dopo la riga `35`/prima di `[Install]`). Ubuntu ha lo stesso `pam-auth-update`, gli stessi file `/etc/pam.d/common-session`, e i quattro display manager (`gdm3`, `sddm`, `lightdm`) includono `common-session` (verificato dallo studio `5-sistema-ubuntu.md` §3.1 sui pacchetti, non sulla macchina).
- **Dimensione/rischio:** piccolo / medio: modifica `/etc/pam.d/common-session` all'avvio del servizio (come già fa il `postinst`). Non verificato: se l'unità di Ubuntu ha restrizioni (`ProtectSystem=`) che impediscono a `pam-auth-update` di scrivere; D con la stessa unità funziona.
- **Prova:** togliere la riga a mano, riavviare il servizio, leggere nel registro «put back»; con il file modificato a mano (deve dire «NOT in … could not be put back»); `check-prelocal.py` P6; `lintian` pulito.

### C6 (B2). Cache Mesa del lato root
- **Cosa è:** la prova dei codec del lato root faceva scrivere a Mesa una cache in `/root/.cache` che dopo la rimozione restava; ora il servizio e il `postinst` la disattivano (`MESA_SHADER_CACHE_DISABLE=true`).
- **Fedora:** `rpm/remotix.service:39` (nata da un rifiuto SELinux, registro F24).
- **Ubuntu oggi: MANCA** (`debian/remotix.service` senza `Environment=`, `debian/remotix.postinst:57` senza la variabile).
- **Debian:** `debian/remotix.service:36-39`, `debian/remotix.postinst:38`. Misurata su Debian come «l'unica eccezione trovata dopo la rimozione» (registro G3).
- **Fare:** portare così com'è (2 righe + 1 commento). Non tocca i desktop degli utenti.
- **Dimensione/rischio:** piccolo / basso. **Residuo del 1.0.1**: un Ubuntu già installato con la 1.0.1 può avere già `/root/.cache/mesa_shader_cache` e `~/.cache/radv_builtin_shaders` (non verificato che su Ubuntu ci siano); la regola «mai cancellare» impedisce di toglierli di nascosto in `postrm`/`postinst`: decisione del proprietario (lasciarli e dirlo, o fare ripulire all'`purge` solo `/root/.cache/mesa_shader_cache`).
- **Prova:** installazione pulita + `remove` + `purge`, poi `find /root /etc /usr /var /home -name '*remotix*'` e `ls /root/.cache` (D lo fa nel giro di prove).

### C7 (B3+A9). Messaggi «reinstalla il pacchetto» e residui di testo
- **Cosa è:** il rimedio `apt install --reinstall remotix` per nome non funziona per un pacchetto installato da file; e il messaggio «servizio PAM mancante» cita ancora Fedora, Arch, SUSE (`.fedora`, `.suse`, `.arch`).
- **Fedora:** `kwin.c:814, 825, 842` («reinstall the package from its file (sudo dnf reinstall ./remotix-<version>.rpm)»), `main.c:466-472`.
- **Ubuntu oggi: testo VECCHIO.** `kwin.c:812, 822, 839` («reinstall the package (apt install --reinstall remotix)»), `main.c:439-447, 469-473`.
- **Debian:** riscritti: `kwin.c:810, 820, 837` (`sudo apt install --reinstall ./remotix_<version>_amd64.deb`), `main.c:439-443, 465-468`.
- **Fare:** portare il testo di D identico (il nome del file `.deb` di Ubuntu è `remotix_<versione>_amd64.deb`, la parte `+ubuntu26.04` sta nella versione: il testo di D è valido). Aggiungere la pulizia dei commenti vecchi (elenco al §7, voce «testi vecchi»).
- **Dimensione/rischio:** piccolo / nullo (testi).
- **Prova:** compilazione; il messaggio `RX-KDE-001` si vede togliendo `/usr/share/applications/org.kde.remotix.desktop` su Kubuntu (agente KDE).

### C8. AppArmor (profilo del lato rete)
- **Cosa è:** correzioni del profilo `remotix_network` che Debian ha trovato in 1.2.0 e che Ubuntu ha già solo in parte.
- **Fedora:** n/a (SELinux).
- **Ubuntu oggi:** ha già la correzione `deny unix (bind, listen) addr=@**` (C4 del registro, `remotix_network.apparmor:100-110`) e i percorsi `xkeyboard-config-2` e `/etc/xkb` (righe `36-48`, specifici di Ubuntu: **devono restare**). **MANCA** la riga `/usr/share/applications/org.kde.remotix.desktop r,` (D la ha a `33-35`): il profilo è in «complain», senza di essa il lato rete segnala una riga ALLOWED per ogni avvio di KDE (D l'ha trovata con `check-apparmor.py` su KDE, registro F10).
- **Debian:** `debian/remotix_network.apparmor:33-35`.
- **Fare:** aggiungere la riga `r` (1 riga + commento). Il profilo resta in `complain` (decisione già scritta nei manuali). La riga `capability net_bind_service` da `nameservice → nis` (commento Ubuntu `20-21, 29`) resta com'è.
- **Dimensione/rischio:** piccolo / basso (il profilo è conffile: l'aggiornamento mostra la richiesta dpkg solo a chi lo ha modificato).
- **Prova:** `check-apparmor.py` (da portare, C13) su Kubuntu; `aa-status` mostra `remotix_network (complain)`. Mai passato a enforce con prove su Ubuntu: i limiti noti (autobind, secondo muro landlock) restano da riguardare in quel momento.

### C9. `postinst`/`prerm`/`postrm` — correzioni di Debian 1.2.0
- **Cosa è:** (a) la riga PAM del gancio si toglie DOPO l'arresto del servizio (altrimenti un riavvio fra la rimozione della riga e l'arresto la rimette: l'unità la rimette a ogni avvio, vedi C5); (b) il controllo «la riga c'è già?» cerca la riga vera e non qualunque riga con il nome.
- **Fedora:** RPM: `%preun` (`rpm/remotix.spec:280-370`, la riga è tolta a servizio già fermo).
- **Ubuntu oggi: come D 1.0.1.** `debian/remotix.prerm:57-64` toglie la riga PAM PRIMA di fermare il servizio (`deb-systemd-invoke stop` più sotto); `debian/remotix.postinst:46` fa `grep -q remotix-local-login`.
- **Debian:** `prerm:67-75` (blocco spostato dopo lo stop); `postinst:27` (`grep -Eq '^[[:space:]]*session…pam_exec\.so.*remotix-local-login'`).
- **Fare:** (a) è NECESSARIA appena si porta C5, altrimenti il purge può lasciare la riga PAM; (b) portare. Entrambe piccole.
- **Dimensione/rischio:** piccolo / medio (ordine in `prerm`: rimozione con utente collegato). 
- **Prova:** `remove` con un desktop remoto aperto e con il servizio riavviato fra le due fasi; `grep remotix /etc/pam.d/*` vuoto dopo `remove`; `purge` pulito.

### C10. Testi e commenti vecchi dentro il pacchetto
Solo testo, nessuna logica; serve il lavoro in un'unica passata (nell'elenco di D `docs/INVENTARIO-non-debian.md`):
- `src/remotix.pam:1-6, 30-40` («DEBIAN 13 ONLY», Fedora/openSUSE/Arch) — **conffile**: gli utenti che non l'hanno modificato lo ricevono senza domande.
- `src/main.c:3967-3972` («the desktops stay alive»: dal §11.56 i desktop si chiudono con il servizio), identico in F e D e **non corretto da nessuno dei due**; `debian/remotix.postinst:11`, `debian/remotix.prerm:11-15, 71`, `debian/remotix.service:40-42`, `debian/rules:121` con la stessa idea; `src/local_login.c:20` («systemd 257» mentre U gira su 259), `src/Makefile:12-14, 56-61` (ngtcp2/nghttp3, vecchio script), `src/session.c:1641` e `session.h:552` («older than the package's keyfiles»), `src/session.c:2385` (la riga di registro dice «three layers compiled now» anche quando `dconf` manca: voce nota del PIANO di Ubuntu del 20 nov); commenti con «Arch/openSUSE/Fedora» in `child.c:9845-9855, 11687`, `session.c:784-791, 1689, 4264, 4766, 5924, 6842, 7802`, `authentication.c:93-103`, `card_pick.c:17`, `certificates.c:152`: sono misure di altre distribuzioni dentro commenti, vere; si possono lasciare.
- Dal PIANO di Ubuntu (20 nov), voci «piccole, non bloccanti, nessuna fatta»: avviso del `postinst` su `labwc` che non scatta su Xubuntu perché lì c'è `gnome-shell` (non riverificato oggi); `prove/check-package.py` non conosce `/etc/dconf/db/remotix` e pretende AppArmor in enforce (`check-package.py:290-291`, identico in D che ha lo stesso difetto).
- **Dimensione/rischio:** piccolo / nullo.

### C11. Voci di F che NON si portano (verificate)
| F | Perché non su Ubuntu | Equivalente in Ubuntu |
|---|---|---|
| SELinux (`selinux/*`, `child.c` 44-47, `walls.c:260-348`, `-lselinux`) | Ubuntu non ha SELinux | AppArmor `remotix_network` in `walls.c` (già c'è, U = D) |
| RPM (`rpm/*`), `remotix.firewalld.xml`, RPM Fusion | altro gestore di pacchetti | `debian/*`, `debian/remotix.ufw` (identico a D), Mesa di Ubuntu ha H.264 |
| `remotix-pam-hook` di F, trigger sddm/`.rpmnew`, plasmalogin | authselect | `pam-auth-update` su `common-session`, già nel pacchetto (`remotix.pam-config`) |
| `remotix.pam` di F | stack authselect | quello di U è già `sshd` di Ubuntu (15 righe su 15 uguali, studio `5-sistema-ubuntu.md` §3.1) |
| Compilazione dconf in `/run/remotix` con nomi fissi (`session.c:1843-1906`) | serviva all'etichetta SELinux | U compila accanto al database con nome temporaneo (`session.c:1840-1895`): giusto per AppArmor |
| KWin da solo, `kde_output_management_v2`, `kwin_output_resize`, `--kwin-virtual` | richiedono KWin 6.8 (U ha 6.6) | labwc nostro 0.9.3 + wlroots 0.19.2, `--kwin-nested`: resta |

---

## 3. Pacchetto (`ubuntu26.04/debian/`) contro D e F

### Differenze già giuste (restano)
`debian/control` (Build-Depends labwc/meson, `libpam-runtime`, Recommends `dconf-cli`, `Static-Built-Using: … labwc, wlroots`),
`debian/rules` (costruzione di labwc nostro, `--dconf-keyfiles`, `LABWC_PATH`), `debian/copyright` (stanza `usr/libexec/remotix/labwc`:
VERA, il pacchetto contiene davvero il binario), `postinst`/`postrm` (compilazione/rimozione del database dconf `/etc/dconf/db/remotix`,
rimozione di `~/.config/dconf/remotix` degli utenti al purge, `postrm:31-35, 57-63`).

### Da portare da D (tutti piccoli)
| File | Cosa | Voce |
|---|---|---|
| `debian/remotix.service` | + `Environment=MESA_SHADER_CACHE_DISABLE=true` e `ExecStartPre=-…/remotix-pam-hook check`; commento `40-42` («desktops survive the stop») da correggere | C5, C6, C10 |
| `debian/rules` | + `install -D -m 0755 src/remotix-pam-hook $(B)/usr/libexec/remotix/remotix-pam-hook`; commento `121` | C5, C10 |
| `debian/remotix.postinst` | `MESA_SHADER_CACHE_DISABLE=true` sul `--encoding-test` (`57`); regex del controllo PAM (`46`); commenti `11` | C6, C9 |
| `debian/remotix.prerm` | blocco `pam-auth-update --remove` spostato dopo `deb-systemd-invoke stop` (`57-64` → dopo `76`) | C9 |
| `debian/remotix_network.apparmor` | + riga `org.kde.remotix.desktop r,` | C8 |
| `debian/changelog` | non nel repo (generato dallo script di costruzione) | §4 |

### Aggiornamento 1.0.1 → 1.2.0 (da provare con una sessione aperta)
- Il `debian/rules:119-123` usa `dh_installsystemd --restart-after-upgrade`: con il §11.56 il riavvio chiude tutti i desktop remoti aperti. È il comportamento della 1.0.1 (già provato dal proprietario sul tablet Debian 1.0.1→1.2.0 «senza avvisi»); su Ubuntu non verificato. Se vale la pena, il manuale lo dice.
- Conffile che cambiano di contenuto: `/etc/pam.d/remotix` (solo commenti), `/etc/apparmor.d/remotix_network` (una riga), `/etc/needrestart/conf.d/remotix.conf` (invariato). dpkg chiede conferma solo a chi li ha modificati.
- `postinst` ricompila `/etc/dconf/db/remotix` a ogni `configure`: nessun cambio di formato fra 1.0.1 e 1.2.0 (nessun file toccato in `session.c` per le chiavi: non verificato in dettaglio, le chiavi sono nella tabella `DCONF_KEYS` che nella 1.2.0 non cambia, ma D ne ha una copia diversa: non applicabile a U).
- La riga PAM resta quella di 1.0.1 (stesso `remotix.pam-config`).

### Disinstallazione pulita
- `postrm` di Ubuntu già toglie: `~/.local/state/remotix` (file elencati), `~/.config/dconf/remotix`, `/etc/dconf/db/remotix` e `remotix.new.*`. Per la 1.2.0 va aggiunto solo il controllo C6 (cache Mesa) e la verifica C9. Controllo suggerito dopo `purge`: nessun file di REMOTIX in `/etc /usr /var /root /home` (come D, registro G3).
- Dopo la 1.2.0 resta da decidere (regola «mai cancellare»): niente rimozione di `/root/.cache` residuo della 1.0.1.

---

## 4. Costruzione senza contenitori

**Oggi:** `ubuntu26.04/build/build-deb.sh` (206 righe) fa `command -v podman` (riga 38-40 in uso, immagine da `build/Containerfile`): **vietato**. Il **solo** posto dove la versione corrente si legge è la riga `build/build-deb.sh:42` (`RX_VERSION:-1.0.1~dev`): `manuals/sources/build.py:36` la legge da lì con una regex. Quindi anche dopo il nuovo script la riga di `build-deb.sh` va portata a `1.2.0~dev` (D lo ha fatto, `debian13/build/build-deb.sh:38`), oppure `build.py` va cambiato.

**Come ha fatto D:** `debian13/build/build-deb-vm.sh` (225 righe): copia l'albero (`src/`, `debian/`, licenze) in un `stage`, scrive `debian/changelog` (da `RX_VERSION`/`RX_REVISION`/`SOURCE_DATE_EPOCH`, `+deb13`), appende `LICENSE.md` a `debian/copyright`, copia in una VM `costruzione` (ssh 2365, mai la Radeon), lì: `apt install` delle dipendenze (`DEPS=...`), `quic-static.sh` (ngtcp2 1.25.0/nghttp3 1.18.0 statici, saltato se già presenti), `dpkg-buildpackage -b -us -uc`, `lintian -I --pedantic`, controlli R13 (funzione di banco non nel binario, con controllo positivo `rcp.o` con `BENCH_ON 1`), R13 opzioni di banco nell'unità, R14 file di banco, R4 `ldd`, R23 (`TWICE=1`), riporta `.deb`, `.buildinfo`, `.sha256`, log in `/media/REMOTIX-DEBIAN/pacchetti/<etichetta>/`; accende e spegne la VM da solo (`vm-radeon-1.2.0.sh accendi costruzione virtuale`, `spegni costruzione`). Fedora: `build-rpm.sh` (107 righe), stessa idea con `dnf builddep` e `rpmbuild`.

**Che cosa serve per Ubuntu (tutto da scrivere, nulla esiste):**
1. **VM `costruzione`** nel banco di Ubuntu: una quinta voce in `server/vm-radeon.sh` (ora solo `ubuntu`, `kubuntu`, `xubuntu`, `lubuntu`, `vm-radeon.sh:21-26`, nessuna `costruzione`; porte ssh 2341-2344 e 8841-8844), con ssh 2345 (proposta, come D 2365 e F 2355), `RXP=0`, `FWD=""`, 8 CPU, 6 GB, solo `virtuale`, e il rifiuto della Radeon per questa VM (come D `vm-radeon.sh:43, 351`). Immagine: Xubuntu 26.04.1 live (come `xubuntu`: `casper/minimal.squashfs` + `minimal.standard.squashfs`), hostname proposto `rx-ub-costruzione`.
2. **`build/build-deb-vm.sh` per Ubuntu**, copiato da D con: `ubuntu26.04` / `+ubuntu26.04` / `resolute` nel changelog; `/media/REMOTIX-UBUNTU`; porta della VM; elenco `DEPS` di Ubuntu = quello del `Containerfile` di Ubuntu (`build-essential pkg-config git ca-certificates cmake ninja-build libssl-dev libpam0g-dev libglib2.0-dev libpipewire-0.3-dev libdrm-dev libva-dev libopus-dev zlib1g-dev libei-dev libxkbcommon-dev libgbm-dev libwayland-dev libvulkan-dev`) **più** quelli del labwc nostro (`curl meson patch hwdata wayland-protocols libegl-dev libgles-dev libinput-dev libpixman-1-dev libseat-dev libudev-dev libdisplay-info-dev libxml2-dev libcairo2-dev libpango1.0-dev libpng-dev`) più `debhelper dh-apparmor dpkg-dev fakeroot lintian binutils`.
3. **Il labwc nostro dentro la costruzione** (ciò che D non ha): `debian/rules` si aspetta `LABWC_SOURCES ?= /usr/local/src/labwc-sources` (`rules:22-28`) con i due tarball già lì (`labwc-0.9.3.tar.gz`, `wlroots-0.19.2.tar.gz`), verificati col sha256 di `build/labwc-ospite/VERSIONS` (`fetch.sh`), e copia `build/labwc-ospite/` nell'albero come `labwc-ospite/` (`build-deb.sh:73-74`). Nella VM: o `fetch.sh` scarica da GitHub/gitlab (serve rete nella VM), o i tarball si copiano già pronti dal tablet (meglio: nessuna rete durante la costruzione; `fetch.sh` li ricontrolla comunque). Passare `LABWC_SOURCES=<cartella>` a `dpkg-buildpackage` (`rules` lo accetta come variabile di ambiente di make: non verificato che `dpkg-buildpackage` lo faccia passare senza `export`).
4. **Controlli in più rispetto a D**, già nel `build-deb.sh` di U e da portare nel nuovo script: `R4 ldd-labwc` (labwc dal pacchetto: nessun «not found», nessuna libwlroots collegata) e `labwc-source` (archivio `remotix-<versione>-labwc-source.tar.gz` GPL, con i due tarball + patch + ricetta, 7 file, sha256, deterministico; `build-deb.sh:121-148`) e `R23 labwc-source-riproducibile`. L'archivio va **pubblicato** accanto al pacchetto (LICENSE.md §8).
5. **Cartella di uscita** `/media/REMOTIX-UBUNTU/pacchetti/<etichetta>/`; il vecchio `build/build-deb.sh` e `Containerfile` restano (regola «mai cancellare»; D li tiene come documentazione).
6. **Server:** serve `prepara-server-vm.sh` (voce D, §5) con `BASE=/media/REMOTIX-UBUNTU`; `server/prepara-server.sh` di U invece installa podman e fa `self-check` con `podman run`: non riutilizzabile.
- **Rischio:** medio. Non verificato: che `dpkg-buildpackage` nella VM dia gli stessi byte dei pacchetti 1.0.1 (usare `TWICE=1` e `SOURCE_DATE_EPOCH` fisso); che `universe` (per `libva-dev`) sia attivo nella VM da squashfs; che meson 1.x di Ubuntu 26.04 compili wlroots 0.19.2 senza `-Werror` (U già usa `-Dwerror=false`, `labwc-ospite/build.sh`).
- **Prova:** `build-deb-vm.sh prova1` e `TWICE=1`; `lintian` E=0; verificare che `labwc` e il sorgente `labwc-source` siano nel pacchetto e nei controlli.

---

## 5. Banco di prova

### 5.1 `ubuntu26.04/prove/` contro D e F

Identici in U, D, F (nessuna azione): `avlib.py`, `check-audio/ban/base/clipboard/input/lifecycle/media/multiuser/phone/resilience.py`, `deskkit.py`, `inputlib.py`, `browserlib.py` e altri.

| File | Differenza | Che cosa fare su Ubuntu |
|---|---|---|
| `check-prelocal.py` | **U ha solo P1-P6** (`main` alla riga 131); D e F hanno anche P7 (terminale con `top`) e P8 (editor con testo non salvato), `--only`, `autologin()`, `dm_restart()`, `busy_case()` (D `177-406`, F `178-370`); D è adattato a Debian: DM `gdm3`/`sddm`/`lightdm`/`sddm`, file di autologin `/etc/gdm3/daemon.conf` e gli script `banco-vm/autologin-{lightdm,sddm}.sh`, terminale e editor (`konsole -e top`; `kwrite`, `mousepad`) | portare la versione di D adattando: gruppo DM di Ubuntu (gdm3, sddm, lightdm, sddm), terminale (`ptyxis` per GNOME 50: già usato da `check-desktop.py:62` di U), editor: **Kubuntu ha `kate`, non `kwrite`**: da misurare (D dice che se manca il caso risponde BLOCKED); P8 su GNOME e LXQt resta BLOCKED come in D. **P7/P8 sulle macchine virtuali con Radeon sono stati VIETATI in D per i blocchi del server (registro D G1): per Ubuntu non verificato se la causa (`amdgpu.runpm=0`) valga anche col kernel 7.0 di Ubuntu; fino a prova contraria applicare le stesse regole (guardare `runpm` della VM prima di dare la Radeon) e fare P7/P8 solo sulle live del proprietario** |
| `check-apparmor.py` | solo in D (legge il registro del kernel e conta le righe `ALLOWED/DENIED` del profilo `remotix_network`); `lib.py` D `173-215` (`Box.apparmor`, `apparmor_summary`) | portare e aggiungere `apparmor` a `LABELS` in `all.sh` (D riga 19) con il `T0` (D `60-61, 78`). Su Ubuntu AppArmor c'è in kernel (a differenza di D: più utile). Non verificato: dove va il registro (journal del kernel contro auditd) sul kernel 7.0 |
| `check-exit.py`, `check-kde-exit.py`, `hold.py`, `hold-user.py`, `prelocal.sh`, `banco-vm/autologin-lightdm.sh`, `autologin-sddm.sh` | solo in D e F | `check-exit.py`: XFCE/LXQt; `check-kde-exit.py`: KDE (restart del servizio, chiusura del browser; **il Log Out dal menu va a mano**, D `COME-SI-LANCIA.md`); `hold*.py` e `prelocal.sh`: generici. Adattare `PORTS` (U 8841-8844 sono già in `lib.py:40`) e nomi VM |
| `all.sh` | D aggiunge la voce `apparmor`, `prelocal` con tempo 2400 (U 900), T0 | portare |
| `lib.py` | D: porte 8861-8864 e funzioni AppArmor; U: porte `8841-8844` + `PORTS` di box `8821-8824` | portare solo le funzioni, NON le porte. Il filtro `\.config/dconf/remotix$` di `check-desktop.py:367` (U) resta |
| `check-desktop.py` | U: `ptyxis`, `sudo-rs` (`309-311`), filtro dconf; F ha 10 righe diverse, D 3 | restano; da aggiungere soltanto se serve il controllo nuovo di F |
| `check-package.py` | identico in D (stesso difetto: pretende AppArmor in enforce, `290-291`) | aggiungere il caso `/etc/dconf/db/remotix` e accettare `complain` (voce del PIANO di Ubuntu del 20 nov, nessuna fatta) |
| `fresh.sh`, `banco-vm/fresh-vm.sh`, `box.sh` | cambiano solo cartelle e nomi; D aggiunge `systemd-coredump` ai pacchetti (`fresh-vm.sh:61`) | portare `systemd-coredump` (controllo dei core dump, decisione del proprietario in D) |
| `check-kde-birth/live/resize.py`, `check-resize.py` | solo F (KWin da solo) | **non si portano** |
| `giro-*-radeon.sh`, `giro-selinux.sh`, `wall-*.sh`, `wall-neg-domain.py` | solo F, SELinux | **non si portano** |
| `package-snap.py` | solo in U e D, differisce di poco | verificare che i controlli sugli snap restino (specifico di Ubuntu) |

Casi «il locale chiude il remoto» con programmi aperti (regola F36): P7 (terminale con `top`, chiusura che non finisce da sola) e P8 (editor con testo non salvato) devono girare, su macchina vera, su tutte le quattro live di Ubuntu prima di pubblicare, come D (`COME-SI-LANCIA.md`). Aperto: la chiusura forzata di Kubuntu con il labwc nostro e Plasma 6.6 (voce KDE).

### 5.2 `ubuntu26.04/server/` contro D e F — che cosa manca agli script di Ubuntu

| Script | Stato in U | Manca rispetto a D/F |
|---|---|---|
| `vm-radeon.sh` (338 righe) | quattro VM `ubuntu` (autoinstall), `kubuntu`, `xubuntu`, `lubuntu` (squashfs), comandi `crea`, `accendi`, `spegni`, `prova-avvio`, `ssh`, `istantanea`/`ripristina`, `stato` | `accendi <vm> virtuale` (senza Radeon, `virtio-vga`, 5 GB), `schermo`, `tasti`, `scrivi`, `wait_ssh`, la VM `costruzione`, `RX_VM_MEM` ovunque, il controllo che la Radeon non sia già presa da **QUALSIASI** qemu del server (D guarda anche i banchi di Fedora e Debian, U solo `$ROOT`); hostname `rx-ub-<nome>`; `lock` c'è |
| `prepara-server.sh` (165 righe) | installa **podman** e fa `self-check` con `podman run ubuntu:26.04` | sostituire con `prepara-server-vm.sh` di D (94 righe, senza podman, con QEMU/OVMF, `/dev/kvm`, strumenti di prova: `chromium firefox-esr labwc wlr-randr python3-pil libavcodec61 PipeWire` con sink nullo `rx_null`, limiti inotify); cambiare solo `BASE=/media/REMOTIX-UBUNTU`. In più U ha bisogno di `genisoimage` e `xorriso` per la sola VM `ubuntu` (autoinstall): D non li ha |
| `live-installa.sh` (209 righe) | pacchetto `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (riga 12), sorgente `http://192.168.0.2:8830` | aggiornare il nome del pacchetto a 1.2.0; D ha in più: rete controllata con `apt` stesso, `wget` o `curl`, `labwc`/`wlr-randr`/`xwayland` installati a mano se mancano, chiave ssh facoltativa per il tablet (`accesso_tablet`), registri conservati in caso di avviso, avviso se la codifica fallisce; la parte specifica di U (`universe`, `componenti_universe`, `add-apt-repository`, `ubuntu.sources`) **resta**; indirizzo del file server: D e F usano il tablet `192.168.0.22:8830`, U ancora `192.168.0.2` (da decidere dove li serve) |
| `vm-radeon-aggiorna.sh`, `vm-radeon-controllo.sh`, `vm-radeon-installa.sh`, `vm-radeon-login-test.py` | solo U, usano le porte `2441-2444` delle VM avviate con `prova-avvio` e podman? (no: solo qemu) | non hanno equivalente in D/F: restano; aggiornare solo se cambiano nomi/porte |
| `VM-BANCO.md` | non esiste in U | scrivere sul modello di `debian13/server/VM-BANCO.md` (comandi, porte, utenti, `amdgpu.runpm`, `costruzione`) |
| `runpm` | D: regola dei blocchi (4 server bloccati il 26 nov 2026) `amdgpu.runpm=0` nel GRUB di OGNI VM Debian prima di dare la Radeon | Ubuntu: non verificato se serve (kernel 7.0, non 6.12). Controllo da fare comunque prima del primo giro: `cat /proc/cmdline`, `/sys/module/amdgpu/parameters/runpm`, `journalctl -k -b | grep -c "SMU is resuming"`; se compare, applicare la cura di D |

Letti anche: `debian13/server/VM-BANCO.md`, `debian13/studio/prove-1.2.0/COME-SI-LANCIA.md` (riavvio del server ⇒ `prepara-server-vm.sh` ricopiato; `fresh-vm.sh`; `all.sh` in background; P1-P6 con `--only`; trappole sui `nohup` e sul `ssh` come `prova`).

---

## 6. Licenze

Regola (proprietario, 26 nov): i file di licenza rispecchiano ciò che il pacchetto di QUELLA distribuzione contiene davvero.

| File | Stato in U | Azione proposta |
|---|---|---|
| `LICENSE.md` | riga `13-14` cita «the installer (`remotix-*.run`), the packages it contains»; §8 (`94-102`) su labwc/wlroots: **VERO**, il pacchetto ha `/usr/libexec/remotix/labwc` (`debian/rules`, `control: Static-Built-Using: labwc (= 0.9.3), wlroots (= 0.19.2)`) e il sorgente accanto al pacchetto | togliere SOLO il riferimento a `remotix-*.run` (D/F hanno «the REMOTIX packages»); NON toccare §8 |
| `THIRD-PARTY-LICENSES` (2171 righe) | righe `11` e `27-29` («remotix-install package and the installation engine inside the .run file», «Installation engine: Go 1.25.14, 17 Go modules»); stanze **Go 1.25.14 e 17 moduli Go** da `1660` a `2171` (≈ 510 righe, voci `1661…2138`); stanze labwc `1236-1601` e wlroots `1602-1659`: **restano** (VERE) | togliere le due righe della premessa, la voce «Installation engine» dell'indice e le stanze Go (`1660-2171`); lasciare ngtcp2, nghttp3, sfparse, libopus, Emscripten, musl, i 10 protocolli Wayland, labwc, wlroots. D: 1224 righe; F: 1256; U atteso ≈ 1659 righe (non verificato: non ho contato un risultato definitivo) |
| `debian/copyright` | ha già la stanza `usr/libexec/remotix/labwc` | nessuna azione (verificare che i numeri di versione siano gli stessi) |
| `licenses/how-it-works.html` | identico in U, D, F (42462 byte); nessun riferimento a `remotix-install`, `.run`, installer, labwc, wlroots, Go (`grep`) | nessuna azione |

Sono testi legali del proprietario: la proposta riga per riga va mostrata prima di scrivere. Nel pacchetto entrano solo `LICENSE.md` (come `copyright`) e `THIRD-PARTY-LICENSES`; `licenses/` NO.

---

## 7. Documenti da aggiornare alla fine (solo elenco)

- `ubuntu26.04/CLAUDE.md`: parla ancora di «REMOTIX-DEBIAN», «Debian 13 (trixie) only», `build/build-deb.sh` in un contenitore `debian:trixie` con `/media/REMOTIX-DEBIAN/pacchetti`, «the old repo ~/Documenti/REMOTIX is read-only reference». Va riscritto sul modello di `debian13/CLAUDE.md` (versione 1.2.0, `build-deb-vm.sh`, banco a VM, `amdgpu.runpm` se serve, directory `prove/`, `server/`, `studio/`, licenze).
- `ubuntu26.04/PIANO.md`: aggiungere la sezione 1.2.0 e le voci «piccole non fatte».
- `docs/REGISTRO-problemi.md`: aggiungere le sezioni F (1.2.0 su Ubuntu), G (banco e costruzione senza contenitori), H (aperti), sul modello di D `232-455`; riesaminare E3/E4 (già di Ubuntu). La voce `docs/STORIA-ubuntu-26.04.md` contiene ancora l'indirizzo di casa e la password di prova (decisione del 20 nov ancora aperta). `docs/SPECS.md` (20 righe diverse da D), `DECISIONS.md` (2), `DECISIONS-11.md` (4): D ha corretto la frase NVIDIA («nessuno l'ha mai visto funzionare») perché NVIDIA è stata MISURATA su RTX 4090 il 5-6 ott 2026 su Ubuntu 26.04 (D `SPECS.md`, `DECISIONS.md`); riportare la stessa correzione e togliere il «NON verificata» del 1 ott. `docs/RIPRISTINO.md` differisce da D in 237 righe: non analizzato.
- Manuali (`manuals/sources/technical-ubuntu26.04/`, `user-ubuntu26.04/`): versione `1.0.1` ricorre 22 volte nei sorgenti (D ha 43 `1.2.0`); `build.py:36` legge la versione da `build/build-deb.sh`. Capitoli toccati: utente **ch01_overview** (aggiungere la sezione «Requirements» come in D/F: scheda che codifica H.264, porta 7447 aperta con `ufw`, orologio del dispositivo giusto) e **ch02_installing**, **ch03_using** (lingua), **ch04_problems**; tecnico **ch03** (chiusura forzata di KDE, 5 s), **ch04**/**ch16** (riga «perché si è chiusa»), **ch10** (primo movimento, GNOME), **ch12** (lingua), **ch13** (aggancio e controllo a ogni avvio), **ch15** (pacchetto, `needrestart`, cache Mesa, polkit fwupd), **ch17** (prove P7/P8, banco a VM, `amdgpu.runpm`), **ch18** (costruzione senza contenitori, labwc), **ch24** (problemi nuovi), più **ch07**, **ch14**, **ch19**, **ch24** per NVIDIA. NVIDIA dichiarata «mai provata» in: `ch14_security.py:593` («NVIDIA (deferred)»), `ch24_problems.py:27-28`, `ch19_performance.py:200`, `ch17_testing.py:542` e ripreso in `ch07_encoding.py:246` («Written, and recorded in comments as measured on an RTX 4090»: già giusto); la frase «nobody has seen it work» di `docs/DECISIONS.md` va corretta. `build.py --check` va rieseguito.
- Sito, GitHub, rilascio: solo su ordine; `Technical Manual — Ubuntu 26.04.html` e `User Manual — Ubuntu 26.04.html` rigenerati con `build.py`.

---

## 8. Segnalazioni a parte

### (1) Ciò che Ubuntu ha e Fedora/Debian no, e DEVE restare
- **Database dconf di sistema** `/etc/dconf/db/remotix` + profilo runtime (`session.c` ~800 righe di differenza da D, `session.h:518-553`, `rootside.c:3344`, `main.c:2862-2865`, `rules:63-66`, `postinst:22-40`, `postrm:31-35, 57-63`, `control`): nato per i programmi snap e Flutter (registro C5). In F lo schema è diverso per SELinux e non va usato come modello; D non lo ha per decisione del proprietario del 25 nov.
- **Labwc nostro 0.9.3 + wlroots 0.19.2** con patch (`build/labwc-ospite/`, `rules:22-54`, `control` Build-Depends e `Static-Built-Using`, `kwin.c:1520-1588` con `REMOTIX_LABWC`, `Makefile:128-133`, `debian/copyright`, `LICENSE.md` §8, `THIRD-PARTY-LICENSES` labwc/wlroots) e `--kwin-nested` con KWin dentro (`kdehost.h`, marchio `remotix-kwin-host`).
- **Pidfd di logind** (systemd 259.9): `child.c:1738-1746`. Non portare il `--session-fd` di D.
- **GNOME 50**: unità `org.gnome.Shell@.service` modello (`session.h:97-120`, `SESSION_UNIT_SHELL_MODEL`, `unit_shell()`), controllo scala (`mutter.c`), `wlr_input_dropped` (`input.c`).
- **AppArmor di Ubuntu**: `xkeyboard-config-2`, `/etc/xkb`, `/etc/X11/xkb` (`remotix_network.apparmor:36-48`); la nota su `abstractions/nis`.
- **Snap, universe, `va-driver-all` solo in universe**: `live-installa.sh` (universe), Depends/Recommends di `control`, gestione degli snap nel `prerm` e nelle prove (`package-snap.py`).
- **Cose di Xubuntu/Lubuntu**: `lubuntu-update` (`session.c`), tasto di blocco sospensione di Ubuntu, `ptyxis`, `sudo-rs` nei test (`check-desktop.py`).
- **Il testo «dconf-cli»** nei messaggi (`session.c:1866, 2471`): è il nome del pacchetto Debian/Ubuntu; F dice `dconf`.

### (2) Dove portare la voce cambia il comportamento visibile su Ubuntu (serve l'OK del proprietario)
La regola del proprietario del 25 nov («allineare come Fedora senza domande voce per voce») copre quasi tutto, ma questi cambiano ciò che l'utente vede:
1. **C1** il desktop remoto non parla più sempre inglese: lingua dell'utente o di sistema, con date e numeri (anche `LANGUAGE`). Su KDE segue `plasma-localerc`.
2. **C3** `PATH` con `~/.local/bin`: **solo se voluto**; portare il ripiego di F non cambia niente su Ubuntu.
3. **A4 (GNOME)** il primo movimento del puntatore inviato due volte (agente GNOME): il primo clic dopo l'accesso non cade più sul bordo.
4. **A6/A7 (KDE)**: chiusura gentile di 5 s invece di 10 per accesso locale, chiusura forzata che ferma `graphical-session.target`: un programma sano che impiega fra 5 e 10 s a chiudersi viene troncato (decisione già presa su Fedora e Debian).
5. **C5** all'avvio il servizio può riscrivere `/etc/pam.d/common-session` (aggancio) — prima lo faceva solo il `postinst`.
6. **C6** la cache grafica del lato root non c'è più (nessun effetto visibile).
7. **C4** regola polkit per fwupd (può sparire una finestra di password sul desktop GNOME, se l'azione esiste su Ubuntu: non verificato).
8. **Aggiornamento**: l'installazione della 1.2.0 sopra una 1.0.1 con un desktop remoto aperto lo chiude (riavvio del servizio, §11.56).
9. **C6/residuo**: file `.cache` della 1.0.1 non rimossi senza ordine.
10. **P7/P8 e il Log Out di KDE** sono prove a mano del proprietario (come D); la sezione «Requirements» e la frase su NVIDIA nei manuali sono testo per il proprietario.

### (3) Non verificato
- Qualunque comportamento su macchina vera o VM di Ubuntu (non mi sono collegato): lingua dentro i processi, P1-P8, aggiornamento 1.0.1 → 1.2.0, `pam-auth-update` da `ExecStartPre`, `amdgpu.runpm` col kernel 7.0.
- Se `/etc/default/locale` di Ubuntu 26.04 contiene `LANG`, `LANGUAGE`, `LC_*` come ci si aspetta (la riga `pam_env` c'è già nel file PAM); se il locale scelto dall'utente è generato (live: pochi locale).
- Se il `PATH` locale di Ubuntu contiene `~/.local/bin` (dipende da `~/.profile` e da come gdm avvia la sessione).
- Se `fwupd` di Ubuntu 26.04 ha l'azione `refresh-remote`; se il Centro software di Ubuntu la richiede.
- Se `dpkg-buildpackage` in VM passa `LABWC_SOURCES` dall'ambiente; se `universe` è attivo nella VM `costruzione`; che i `.deb` costruiti nella VM abbiano gli stessi byte di quelli in contenitore.
- Se Xubuntu avvia `xiccd` e se in sessione remota chiede la password di amministratore (voce XFCE, `xiccd` compare nell'elenco dei processi di Xubuntu: `studio/12-verifiche-xfce.md:118`, `7-xubuntu-lubuntu.md:270`; D l'ha risolto escludendolo dall'avvio: `session.c:2505-2511`); se Kubuntu ha `kwrite` (per P8) o solo `kate`.
- Il numero esatto di righe delle licenze dopo la pulizia; il contenuto di `docs/RIPRISTINO.md` (237 righe di differenza da D).
- Lo stato del server e delle VM Ubuntu (cancellate il 20 nov, secondo il PIANO di Ubuntu): non mi collego.

### (4) Voci rimaste aperte per Ubuntu nei documenti di Debian
Da `debian13/docs/REGISTRO-problemi.md` e `debian13/PIANO.md`:
- **H5 / F6:** «se Xubuntu ha `xiccd`» (sopra). Probabile sì; la finestra di password non è stata vista su Ubuntu.
- **H5:** su Fedora, se la lingua dell'utente arriva al desktop KDE (mai misurato) — riguarda anche Kubuntu per C1.
- **F1:** `xfconfd` resta nella lingua di sistema su XFCE.
- **F9:** correzione AppArmor `deny unix` già in U; limite noto dell'«autobind» da riguardare al passaggio a `enforce`.
- **F13 (E3):** variabili del gestore utente, «foto» vecchia, «non ho potuto guardare» vale «chiuso» (`session_alive()`, `child.c`): voce di Ubuntu, correzione consigliata, **non fatta**.
- **F13 (E4):** piccoli scatti video da Chrome su Android, misurati su Ubuntu; non bloccanti.
- **H1:** `media/screen-updates` di poco oltre soglia (1,0-1,5 s contro 1,0) su GNOME, KDE, LXQt; da misurare su Ubuntu e confrontare.
- **H2:** `pkexec` su GNOME (SHELL vuota): noto.
- **H3:** `kbd-not-producible` su Firefox in LXQt: probabile difetto dello strumento.
- **H4:** P7/P8 automatiche solo su GNOME; il resto a mano sulle live.
- **G1:** blocchi del server con la Radeon nelle VM Debian (`runpm`).
- **PIANO D «Rischi»:** protezioni nate su GNOME 50 / KWin 6.6 (quelle di U) non viste scattare su Debian: per Ubuntu valgono già come misurate.
- **PIANO D «Aperti»:** sfondo nero su XFCE (difetto di `libxfce4windowing` 4.20.2 di Debian; Ubuntu ha la libreria nuova: non verificato che lo sfondo compaia).

---

## 9. Riepilogo (linguaggio semplice, ≤ 20 righe)

1. Lo studio del 25 nov va corretto: Ubuntu non è «da portare quasi da zero»; quasi tutto ciò che Debian ha fatto per la 1.2.0 (e non viene da Fedora) l'ha preso da Ubuntu, quindi in Ubuntu c'è già.
2. Ubuntu differisce da Fedora in 14 file e da Debian in 12. Fuori dai desktop restano da portare poche cose, quasi tutte piccole.
3. Si porta così com'è: la riga di registro sul perché una connessione si chiude (un solo file, uguale in Debian e Fedora), la regola per gli aggiornamenti firmware, la cache grafica di root disattivata, i testi «reinstalla il pacchetto», la riga in più nel profilo di sicurezza.
4. Si porta con cura: lingua e formati del desktop remoto (la parte più delicata, dentro il file che avvia la sessione), il controllo a ogni avvio che «il locale chiude il remoto» sia agganciato (script di 37 righe già pronto in Debian), l'ordine nello script di rimozione.
5. Il `PATH` per Ubuntu quasi non serve: il sistema ne dà già uno. Se si vuole `~/.local/bin` lo decide il proprietario.
6. Non si porta nulla di SELinux, RPM, firewalld, KWin da solo; e non si copia da Debian il meccanismo della sessione di systemd 257 (Ubuntu usa systemd 259).
7. Deve restare tutto ciò che è solo di Ubuntu: database dconf di sistema, il nostro labwc con KDE, regole AppArmor per la tastiera, GNOME 50, snap.
8. La costruzione oggi usa podman (vietato): serve una VM «costruzione» per Ubuntu e uno script nuovo sul modello di Debian, con in più la costruzione del nostro labwc/wlroots e il sorgente da pubblicare.
9. Il banco: a Ubuntu mancano le prove P7/P8 (con programmi aperti), il controllo dei rifiuti AppArmor, il modo «virtuale» senza Radeon nello script delle VM, la VM di costruzione e uno script senza podman per preparare il server.
10. Licenze: togliere installatore, `.run` e i moduli Go (circa 510 righe); labwc e wlroots restano, perché nel pacchetto ci sono davvero.
11. Da decidere dal proprietario: PATH con `~/.local/bin`; i file di cache lasciati dalla 1.0.1; che l'aggiornamento chiuda i desktop aperti; la sezione «Requirements» e la correzione su NVIDIA nei manuali.
12. Da non dimenticare: «il locale chiude il remoto» va provato sempre con programmi aperti, su macchina vera, prima di pubblicare; Ubuntu (kernel 7.0) va controllato per il blocco della Radeon.
13. Non ho potuto verificare nulla su macchina (lingua, aggiornamento, kernel): tutto ciò che dipende da una prova è segnato «non verificato».
