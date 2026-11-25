# Inventario G1 — manuale tecnico di REMOTIX per Fedora 45, capitoli ch01–ch05

Data: 25 nov 2026. Albero letto: `fedora45/` (spec ancora `Version: 1.0.1`, `rpm/remotix.spec:25`; il pacchetto 1.2.0 deve ancora nascere).
Base: `ubuntu26.04/manuals/sources/technical-ubuntu26.04/ch01_introduction.py … ch05_rcp.py` (56 sezioni, 2444 righe).
Metodo: lettura integrale dei cinque capitoli; `diff -rq ubuntu26.04/src fedora45/src` e diff mirati; `fedora45/PIANO.md` (D1–D8, giornale fino al 25 nov, piano manuali),
`docs/REGISTRO-problemi.md` F1–F36, `rpm/`, `selinux/`, `build/`, `server/`, `studio/1…5`. Sola lettura: nessun file toccato, nessuna macchina usata.
Dove non ho potuto controllare c'è scritto «non verificato».

## Tabella riassuntiva

| Capitolo | Sezioni | Vale com'è | Da correggere | Da riscrivere | Da togliere (intera sezione) |
|---|---|---|---|---|---|
| ch01 Introduction and concepts | 5 | 0 | 4 | 1 | 0 |
| ch02 Overall architecture | 11 | 5 | 6 | 0 | 0 |
| ch03 Startup and life cycle | 12 | 1 | 11 | 0 | 0 |
| ch04 Transport | 14 | 8 | 5 | 1 | 0 |
| ch05 The RCP/1 protocol | 14 | 10 | 3 | 1 | 0 |
| **Totale G1** | **56** | **24** | **29** | **3** | **0** |

(Le sezioni «da correggere» contengono spesso un blocco da riscrivere o da togliere: è indicato nella voce. Nessuna sezione intera va tolta.)

## Fatti-base valevoli per tutte le voci (con la prova)

- **Il codice è quasi identico a Ubuntu.** `diff -rq ubuntu26.04/src fedora45/src`: differiscono solo `child.c`, `input.c`, `kdehost.h`, `kwin.c`, `kwin.h`, `main.c` (9 righe: `--kwin-virtual`, `main.c:2886-2891`),
  `Makefile`, `remotix.pam`, `remotix-remote-sessions.rules`, `session.c`, `transport.c`, `walls.c`; nuovi `remotix-pam-hook`, `protocols/kde-output-*-v2.xml`, `protocols/README-kde-output.txt`.
  **Identici a Ubuntu**: `rcp.c/.h`, `rootside.c/.h`, `rootside_proto.h`, `webtransport.c/.h`, `sentinel.c`, `helper.c`, `authentication.c`, `rediscover.c`, `tls.c`, `certificates.c`, `page.c`, `page.html`, `cid.*`, `hsrate.h`, `resetcap.h`, `msgrate.h`.
  Conseguenza: ogni frase dei capitoli 2, 4, 5 che parla di questi file resta vera. Anche i documenti `docs/RCP.md`, `SPECS.md`, `DECISIONS*.md`, `LESSONS.md`, `REGISTRO-priorita.md` sono identici (`diff -q`): le decisioni D1–D8 di Fedora stanno solo in `fedora45/PIANO.md`, non in `docs/DECISIONS*.md` (il manuale deve citarle come «PIANO.md D1…» e il registro come «REGISTRO F…»).
- **Costanti di tempo e di tetto invariate** salvo due righe nuove: `diff <(grep -h '#define [A-Z_0-9]*_\(MS\|S\|NS\|MAX\|CAP\)\b' ubuntu26.04/src/*.[ch] | sort) <(… fedora45/src/*.[ch] | sort)` dà solo `KDE_PRELOCAL_ORDERLY_MS 5000` (`session.c:113`) e `CHILD_LOCALE_MAX 12` (`child.c`). Perciò le tabelle degli orologi (ch03 §7, ch04 §11, ch05 §11) restano vere; solo ch03 §7 riceve una riga.
- **Versioni vere su Fedora 45** (PIANO.md:62-63, studio 1-5): GNOME 51 (gdm), Plasma 6.8 (KWin 6.8; 6.8.1 sulla VM, sorgenti 6.8.3, `studio/5-kde-progetto.md:3-4`) con plasmalogin (pacchetto `plasma-login-manager`), XFCE 4.20 (lightdm), LXQt 2.4 (sddm), systemd 262, labwc 0.20.2 dai repository, `openssl-devel` 4.0.3 (D8, `build/build-rpm.sh:20-21`), ngtcp2 di Fedora 1.22.1 (troppo vecchio; statici 1.25.0 / nghttp3 1.18.0, `build/quic-static.sh:1-6,9-10`).
- **Pacchetto**: `rpm/remotix.spec` (scriptlet `%pre` r.168, `%post` r.217, `%preun` r.280, `%postun` r.380, trigger r.433-463), `remotix.service`, `remotix.sysusers`, `remotix.tmpfiles`, `remotix.firewalld.xml`, `needrestart.conf`, `org.kde.remotix.desktop`, `denied-users`, `remotix-no-suspend.conf`; modulo SELinux `selinux/remotix.{te,fc,if}`. Niente labwc nostro, niente `debian/`, niente AppArmor, niente contenitori (`CLAUDE.md` di fedora45).
- **Stato del pacchetto candidato**: `i2` (PIANO.md:454); il manuale dovrà parlare di `remotix-1.2.0-1.fc45.x86_64.rpm` (PIANO.md:483), che oggi non esiste: finché la spec dice 1.0.1 `build.py` leggerebbe 1.0.1.

---------------------------------------------------------------------------------------------------

# ch01_introduction — «Introduction and concepts» (5 sezioni)

### 1. What REMOTIX is and what it promises — DA CORREGGERE
Da cambiare (righe del sorgente Ubuntu):
- r.8 (zona della figura) «The Ubuntu 26.04 machine» → «The Fedora 45 machine»; r.18 didascalia idem.
- r.25-28: «Ubuntu 26.04 (“resolute”)… four flavours Ubuntu, Kubuntu, Xubuntu, Lubuntu» → Fedora 45, cartella `fedora45/`, quattro desktop: GNOME (Workstation), KDE Plasma, XFCE, LXQt (le Live 45-1.4, PIANO.md:7). Prova: PIANO.md:62-63.
- Tabella «Version» r.37-39: da `RX_VERSION` in `build/build-deb.sh` → da `Version:` in `rpm/remotix.spec` (`build/build-rpm.sh:37`); pacchetto `remotix-<VERSION>-1.fc45.x86_64.rpm`, installazione `sudo dnf install ./remotix-….rpm` (PIANO.md:483). Nota: oggi la spec dice 1.0.1; 1.2.0 da scrivere prima del manuale.
- «Server» r.40-45: togliere il secondo eseguibile `/usr/libexec/remotix/labwc` (labwc 0.9.3 + wlroots 0.19.2): NON esiste su Fedora (`rpm/remotix.spec:5`, D2, F7). Restano `remotix`, `remotix-local-login`; AGGIUNGERE `remotix-pam-hook` (`spec` `%files`, `src/remotix-pam-hook`) e `remotix-polkit-seated`. Rimane `remotix.service`.
- «Desktops» r.53-56: GNOME 51, KDE Plasma 6.8 (KWin da solo), XFCE 4.20, LXQt 2.4; «KDE Plasma, Kubuntu» → «KDE Plasma». XFCE e LXQt in labwc del sistema (`Recommends: labwc`, spec r.90). Dichiarare i limiti: sfondo nero e niente icone su XFCE (D7), portachiavi come Debian/Ubuntu (D6).
- «Video» r.50-51: vero, ma va aggiunto in primo piano il requisito D1: su Fedora H.264/HEVC NON sono di serie; l'amministratore installa RPM Fusion (`mesa-va-drivers-freeworld`, NVIDIA: driver proprietario) — `spec` `%post` r.~255-260, PIANO.md:96-102. Il pacchetto rifiuta una prima installazione senza nodo DRM (`%pre`, spec r.168-176) e avvisa se la scheda non codifica.
- «Packaging» r.64-65: «A single .deb built in an ubuntu:26.04 container» → «A single .rpm built on a Fedora 45 virtual machine (no containers), `build/build-rpm.sh`»; servizio installato spento (spec r.217-220, preset Fedora `disable *`). Aggiungere: modulo SELinux del pacchetto (D3), servizio firewalld `remotix` (D5).
- «Licence» r.68-71: la frase su labwc/wlroots/`remotix-<version>-labwc-source.tar.gz` è FALSA per Fedora. Difetto di sorgente: `fedora45/LICENSE.md:95-102` è uguale a quello di Ubuntu e la dice ancora (`diff -q` identico). Decisione richiesta: correggere `LICENSE.md` oppure il manuale non lo cita. `THIRD-PARTY-LICENSES` invece è già aggiornato (12 file di protocolli Wayland, MIT-CMU: `diff` con Ubuntu).
- «Size» r.66-67: conteggio automatico, **da ricontare** (generatore): `wc -l fedora45/src/*.c fedora45/src/*.h` (= 106 971 con anche `vulkanvideo_rgb_nv12_spv.h`, che il generatore esclude) e `wc -l fedora45/src/page.html` (14 326 oggi). Non copiare.
- Vale: porta 7447, WebTransport/RCP, cap 10 (`RCP_SESSION_CAP`, `rcp.h`), limiti dichiarati 8 utenti/3K, orologi 30 s/30 min/60 min (codice identico), nota «Goals, not promises» (SPECS identico).

### 2. What was verified and what was not — DA RISCRIVERE
Tutta la sezione è la storia dei giri di Ubuntu (container `rxu-*`, `unione2…unione11`, 4 VM, 4 live Ubuntu, AppArmor C4/C5). Per Fedora i fatti sono altri (tutti da PIANO.md e registro):
- Metodo: niente contenitori; banco = VM con Radeon passata (`server/vm-radeon.sh`), una Radeon, una VM per volta, istantanee `codec`/`consegna-finale-<de>`; macchina di costruzione `costruzione`; prove sulla macchina vera da chiavetta Live con `server/live-installa.sh` (PIANO.md:343-347).
- Pacchetti: `p4f`, `k4b`, `l6`, `s8…s15`, `f1`, `g6`, `h1` (sha256 `550f368b…`), `i1`, `i2` (sha256 `172d4e89…`, candidato; PIANO.md:454-455).
- Giro finale `h1` in enforcing (PIANO.md:316-320): gnome 52 PASS (FAIL pkexec noto) + `all.sh` 39 PASS; kde 76; xfce 60; lxqt 60; prova negativa 0 FAIL; AVC nostri 0. KDE con `i2` solo `check-prelocal.py` P1–P8 PASS e giro breve (PIANO.md:446-450); `i2` NON rieseguito sugli altri tre (decisione del proprietario, PIANO.md:456-457).
- Prove a mano del proprietario (PIANO.md:326-329): tutti e 4 i desktop OK con `h1` e muro SELinux; 25 nov, «il locale chiude il remoto» da chiavetta: GNOME OK, XFCE OK (chiusura ordinata 1,7 s), LXQt OK (0,7 s), KDE NON superata con `h1` (F36), poi OK con `i1` e con `i2` (forzata a 5,04 s, gancio liberato a 5,9 s, 0 rifiuti SELinux, 0 core dump).
- Non verificato / aperto da dichiarare (PIANO.md:458-461, registro): chiusura per abbandono su KDE; programmi lenti a chiudersi su KDE; più schede grafiche con KWin da solo (F12); `giro-selinux.sh` nasconde un controllo morto a metà (`check-kde-exit` «service restart», intermittente); lingua senza codifica in AccountsService (`it_IT`); GNOME senza «ultima difesa»; Debian/Ubuntu stesso codice di forzata; `catatonit`; rifiuto `search` su `/proc/sys/dev`; `force_guard_on` (session.c:8770); NVIDIA; Safari/Firefox su Windows; IPv6.
- Aperti noti: pkexec su GNOME (SHELL vuoto, comune a Ubuntu); F30 XFCE con utente `staff_u` (pannello, non nostro); F15 `avc { view }` di `xdm_t` su `stratisd_t` non nostro; F16 core dump di programmi KDE alla chiusura forzata.
- Browser: la sezione «Browsers as SPECS §11.5» e «What REMOTIX deliberately does not do» (r.139-146) valgono com'è (SPECS identico); l'avvertenza «Documents and code» (r.147-153) vale com'è (aggiungere: i documenti citano file del vecchio repo, come per Ubuntu).
- Tabella r.87: cifre dei giri Ubuntu (123/124, 121/124, 126/128, 120 PASS…) vanno tolte; le cifre Fedora sopra sono quelle del giornale e vanno ricontrollate sui log (`~/remotix-prove-live/…`, sul server `/media/REMOTIX-FEDORA/…`): «non verificato» da qui.

### 3. Basic vocabulary and the invariants — DA CORREGGERE
- Riga «Our labwc» (r.192-194): DA TOGLIERE (nessun labwc nostro; `REMOTIX_LABWC` resta solo come stringa nel Makefile r.132-133, F1/F7).
- Riga «Runtime dconf profile, system dconf database» (r.195-198): vale (`session.c`); correggere solo il «compiled by the package» → compilato dallo `%post` (spec r.~243-256) e, se manca, dal lato root a ogni avvio (`session_dconf_system_db_ensure`).
- Riga «Network side» (r.163-166, «walls»): ok; ma «the walls» includono ora l'etichetta SELinux (`walls.c:260-348`).
- AGGIUNGERE parole nuove di Fedora: **remotix_t / remotix_net_t** (domini SELinux del lato root e del lato rete, `selinux/remotix.te`, F24); **remotix-pam-hook** (blocco `pam_exec` nei file PAM di gdm, plasmalogin, lightdm, sddm, F6/F9/F21); **KWin alone / `--kwin-virtual`** (D2, F7); **kde_output_management_v2** (cambio di misura, `kwin.c`); **RPM Fusion / «freeworld»** (D1); **firewalld service `remotix`** (D5).
- Invarianti I1–I7: vale com'è. I7 («`na`») è nel codice identico (`sentinel.c`). I2/I3 ok. Nota nuova per I7: i controlli del programma ora includono i rifiuti SELinux (uscite 44-47 di `child.c`, vedi ch02 §7).
- Riga «Stage refused»: vale; aggiungere che anche il rifiuto KDE «KWin senza `kde_output_management_v2 ≥ 22`» usa lo stesso percorso `fatal` (`child.c`: `kde_refused`, F13).
- Riga «Stage»/«Found again»: nessun cambio.

### 4. The repository, folder by folder — DA CORREGGERE
- Albero r.230-244: radice `REMOTIX-UBUNTU/` → `fedora45/`; sparisce `debian/` → `rpm/` + `selinux/`; sparisce `boxes/` (non esiste: `ls fedora45`); `build/` ha solo `build-rpm.sh`, `quic-static.sh` (niente `Containerfile`, niente `labwc-ospite/`); `server/` ha `vm-radeon.sh`, `prepara-server.sh`, `live-installa.sh` (niente `vm-radeon-aggiorna/installa/controllo`, niente `vm.sh`); `prove/` ha `banco-vm/` con `autologin-lightdm.sh`, `autologin-sddm.sh`, `box.sh`, `fresh-vm.sh` e script nuovi (`giro-selinux.sh`, `giro-xfce-radeon.sh`, `giro-lxqt-radeon.sh`, `check-kde-*.py`, `wall-*.{sh,py}`); `studio/` ha 5 studi (1-gnome, 2-kde, 3-xfce, 4-lxqt, 5-kde-progetto) + `00-REGOLE-studio.md` + `manuali/` (non «1 to 16»). `licenses/how-it-works.html` esiste.
- Tabella `src/`: aggiungere `remotix-pam-hook`; `remotix.pam` è lo stack di sshd di Fedora (`authselect`, `password-auth`, `postlogin`, `pam_selinux`, `pam_env envfile=/etc/locale.conf`), non `@include common-*`; `protocols/` ha ora 12 file (+ `kde-output-device-v2`, `kde-output-management-v2`).
- Riga `debian/` r.251-256 → riga `rpm/`: `remotix.spec` (scriptlet: `%post` compila dconf e mette il gancio PAM, `%preun` chiude le sessioni e rimuove il gancio, `%postun` toglie tutto: un RPM non ha «purge»), `remotix.service`, `remotix.sysusers`, `remotix.tmpfiles`, `remotix.firewalld.xml`, `needrestart.conf`, `org.kde.remotix.desktop`, `denied-users`, `remotix-no-suspend.conf`, `remotix.conf`. Riga nuova `selinux/`: `remotix.te`, `.fc`, `.if`. Tolti: `remotix_network.apparmor`, `remotix.ufw`, `debian/rules`, `control`, `postinst`.
- Riga `build/` r.257-260: `build-rpm.sh` costruisce nella VM `costruzione` (porta ssh 2355, `build/build-rpm.sh:20-31`), NON in un contenitore; `quic-static.sh`: ragione vera (ngtcp2 di Fedora 1.22.1 < 1.25.0 richiesto), nome «26.04 packages (1.16/1.12)» da togliere.
- Riga `boxes/` r.265-267: DA TOGLIERE. Riga `server/` r.268-270: ridurre ai tre script reali. Riga `studio/` r.271-272: cinque studi + regole. Riga `docs/` r.273-275: `INVENTARIO-non-debian.md` e `PULIZIA-tranche1.md` esistono ancora (`ls fedora45/docs`); aggiungere `STORIA-ubuntu-26.04.md` (384 righe) e il registro con la sezione F (F1–F36).
- Nota «Working rules» r.277-280: `fedora45/CLAUDE.md` è giusto («Fedora 45 only», NO contenitori) ma la riga 6 dice ancora «RPM packaging goes in `rpm/` (to be written)»: stantio (difetto di sorgente, non ripeterlo). Il vecchio repo non c'entra: la regola è «non toccare `../debian13/` e `../ubuntu26.04/`».

### 5. The project in numbers — DA CORREGGERE
- La tabella è dinamica (`PARTS`, r.282-303): i conteggi escono dal generatore, NON copiare. **Da ricontare**: `git ls-files fedora45/<cartella> | xargs wc -l` per prefisso.
- Righe da cambiare nel generatore: «Package `debian/`» → `rpm/` + `selinux/`; «Build» non ha più `labwc-ospite/`; «Checks and test rigs» = `prove/` + `server/` (niente `boxes/`); regola catch-all «Manual sources» (`lambda f: True`) conta anche i sorgenti dei manuali: in `fedora45` ci saranno `user-fedora45` e `technical-fedora45` (PIANO.md:476-477), non quelli di un'altra distribuzione: il testo r.307-309 («the manual of the other distribution that was kept here») va tolto.
- Frase «A large share of the C is comment» (r.311-313): vale (commenti numerosi, p. es. `walls.c:260-348`).

---------------------------------------------------------------------------------------------------

# ch02_architecture — «Overall architecture» (11 sezioni)

### 1. The roles of the server executable — DA CORREGGERE
- Riga `--kwin-nested` (r.21-26): DA RISCRIVERE come `--kwin-virtual W H -- <kwin_wayland_wrapper> …` (`main.c:2886-2888`, `kwin.h`, `kwin_virtual_alive()`): lancia il piccolo servizio che risponde a `org.freedesktop.ScreenSaver` e poi diventa il wrapper di KWin con `--virtual`; niente labwc, niente `REMOTIX_LABWC` in uso. `--kwin-nested` oggi risponde «does not exist on this system» ed esce 2 (`main.c:2889-2891`). Prova: F7.
- Riga `--dconf-keyfiles DIR` (r.27-31): vale; «Used at build time… `debian/rules`» → generata in `%install` della spec (`remotix.spec`, riga `src/remotix --dconf-keyfiles …/remotix.d`); compilata in `/etc/dconf/db/remotix` dallo `%post`.
- Riga `--drop-render-grants` (r.35-36): «run by the package's removal scripts» vale → `%preun` (spec r.~340-350), solo alla rimozione.
- r.38-45 unità: «`debian/remotix.service`» → `rpm/remotix.service`; `remotix.conf` in `/usr/share/remotix/` come prima. Aggiungere due righe nuove dell'unità: `Environment=MESA_SHADER_CACHE_DISABLE=true` (r.39) e `ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check` (r.42): controlla a ogni avvio che il blocco del gancio sia nei file PAM delle schermate di accesso.
- Nota «Single-process mode» r.46-50: vale (`INVENTARIO-non-debian.md` esiste ancora in `fedora45/docs`).
- r.8-9 «`remotix-local-login`… PAM runs at a local login»: vale ma come lo aggancia PAM è diverso su Fedora: non `pam-auth-update`, ma `remotix-pam-hook` (F6). Il commento di `local_login.c:3-4` dice ancora `pam-auth-update`/`common-session` e «systemd 257» (stantio, difetto di sorgente).

### 2. Process tree and privileges at a glance — DA CORREGGERE
- r.98 «`sudo apt install` inside a remote desktop keeps working» → `sudo dnf install`. Nient'altro nel testo e nella figura è specifico di distribuzione.
- Vale: ruoli, identità, «cannot do» (codice identico). Aggiungere una frase: su Fedora il lato rete nasce nel dominio SELinux `remotix_net_t` e il lato root in `remotix_t` (`walls.c:260-348`, F24), le sessioni utente in `unconfined_t` (o il contesto dell'utente, F25).

### 3. The root side — DA CORREGGERE
- Passo «0b» (r.112-116): la compilazione del database dconf è cambiata in `session.c` (diff): ora compila in `/run/remotix/dconf-compile.tmp` e scrive `/etc/dconf/db/remotix.new` (aperto `O_EXCL`, poi `rename`), per poter etichettare i due nomi fissi (`remotix_dconf_db_t`, F24). Il testo «temporary file renamed over the old one» è ancora vero in sostanza, ma i nomi sono questi. `dconf-cli` → pacchetto `dconf` (debole: `Recommends: dconf`, spec r.91). «postinst» → `%post`.
- Passo 5 (walls) r.125-128: «if `walls_apply()` fails … 126»: vale; aggiungere che `walls_apply()` scrive anche l'attributo di exec SELinux (`selinux_exec_net`, `walls.c:344,780`).
- Ciclo `poll()` e `kdehost_sweep()` (r.130-136): vale; `kdehost_sweep()` esiste (`rootside.c:1677`, `rootside.c:3514`); il segno «è nostro» ora è `--kwin-virtual` o `REMOTIX_KDE_HOST=1` (`kdehost.h:50-61`).
- Paragrafi «If the network side dies / root side dies / Stopping»: valgono (rootside.c identico).
- Costanti citate (`STOP_WAIT_MS`, `KIDS_*`, `NET_*`): invariate (confronto sopra). Da ricontare solo per scrupolo: `grep -n "define STOP_WAIT_MS\|define NET_RESTART_CAP_MS" fedora45/src/*.[ch]`.
- Nuovo (a): la sezione dovrebbe dire che il lato root su Fedora gira in `remotix_t` (non confinato come `unconfined_service_t`: dominio proprio, F24/F27) e che `restorecon` è chiamato dallo `%post`.

### 4. The network side and its walls — DA CORREGGERE
- Figura `WALL_ORDER` (r.158-165): il riquadro «AppArmor / exec profile» → «MAC label / exec context» (AppArmor o SELinux: «one of the two is on, never both», `walls.c:776-781`).
- Riga «AppArmor» della tabella (r.197-201): AGGIUNGERE la riga **SELinux**: `selinux_exec_net()` legge `/proc/thread-self/attr/current`, e se il lato root è in `remotix_t` scrive `system_u:system_r:remotix_net_t:s0` in `/proc/thread-self/attr/exec` prima di `execve`; SELinux spento = nota e si prosegue; acceso ma non in `remotix_t` o dominio non caricato (EINVAL) = avviso «⚠» e si prosegue; scrittura rifiutata = lato rete NON partito (`walls.c:260-348`). La riga AppArmor resta per codice (la funzione c'è ancora) ma su Fedora non è in vigore: dire «nessun AppArmor, nota nel registro».
- Il blocco `warn("AppArmor is not yet enforcing")` (r.203-222): DA TOGLIERE/RISCRIVERE. È tutta storia di Ubuntu (C4, `deny unix addr=@*`, XKB di Ubuntu, `complain`). Per Fedora: il muro è il modulo SELinux del pacchetto, **enforcing**, 0 rifiuti nostri sui quattro desktop (F24, PIANO.md:251-257, 269-276, 316-320); limiti da dichiarare: il lato root (`remotix_t`) resta largo (F27, PIANO.md:255-256); F5/F25 utenti confinati; F28 rifiuti che non sono nostri; prova negativa 25/25. Non verificato qui: il contenuto delle regole (`selinux/remotix.te`, non letto riga per riga).
- Vale: tabella delle altre pareti (PID/mount/net namespace, identità, `no_new_privs`, seccomp): `walls.c` identico fuori da SELinux. Quattro thread del lato rete: vale (codice identico).
- Nota in fondo (r.223-226): vale.

### 5. The closed list between the two sides — VALE COM'È
`rootside_proto.h` e `rootside.c` identici a Ubuntu; tutti i numeri (16 AUTH in volo, 3/s, burst 8, 32 grant, 30 s, `ROOTSIDE_ORPHAN_UID_MS`) restano veri. Nessun riferimento a distribuzione.

### 6. The PAM helper — VALE COM'È
`helper.c`, `authentication.c` identici. Il testo parla del servizio PAM `remotix` in generale (non cita `common-auth`). Il contenuto del file PAM di Fedora (authselect, faillock) va in ch13, fuori dal gruppo.

### 7. The per-user child — DA CORREGGERE
- Passo 2 (r.308-311): «On GNOME and KDE… a card ACL for the user's private group is added (`render_grant_add()`; its effect at run time is not verified on Ubuntu 26.04)» → su Fedora il nodo di render è 0666 (`studio/1-gnome-fedora45.md:438`): «`render_grant.c` non ha niente da concedere»; l'iscrizione con `usermod -aG` e il suo effetto su Fedora sono **non verificati** (`studio/1:534` riga 12, «parziale»).
- Passo 4 (r.313-321): «logind (version 258 and later; Ubuntu 26.04 has 259.9)» → Fedora 45 ha systemd 262 (`studio/1-gnome-fedora45.md:172`); «read in the systemd 259.9 source» da togliere; «excluded on 26.04» → non c'è un logind vecchio su F45 (non verificato come caso). L'assenza di `--session-fd` vale ancora (child.c identico su questo punto).
- NUOVO passo SELinux (b), tra passo 2 e 5: `selinux_exec_like_local_login()` (`child.c:1726`, chiamata a r.1977) chiede alla tabella di libselinux il contesto di un accesso grafico (chiamante `xdm_t`), lo imposta per il prossimo exec; `selinux_exec_checked()` (`child.c:1794`) controlla subito prima dell'`execve` e rifà il portachiavi di sessione solo se l'etichetta differisce. Uscite nuove: 44 (nessun contesto), 45 (non impostabile), 46 (resterebbe in `remotix_t`), 47 (portachiavi) = login RIFIUTATO (`child.c:1144-1147`). Prova: F25, PIANO.md:565-566 (F5), 269-276. Il testo «any difference exits with 34-36» resta vero, ma l'elenco dei codici va completato.
- Passo 6 (r.324-331): «The PATH is the one `pam_env` composed from `/etc/environment` (on Ubuntu it lists `/snap/bin`…)» → su Fedora non c'è `/etc/environment` di serie: il fallback ora è `~/.local/bin:~/bin:/usr/local/bin:/usr/bin` (`child.c:2028-2037`, F4/F34), non `/usr/local/bin:/usr/bin:/bin`; AGGIUNGERE le variabili di lingua: `LANG` dall'utente (AccountsService, letto da root prima del cambio d'identità, `child.c:1603-1730`) altrimenti di sistema (`/etc/locale.conf` via `pam_env`, `remotix.pam:72`), più `LC_*` e `LANGUAGE` (`session.c:3711-3715`, `4798`); `envp[]` passa da 16 a 32 (`child.c`). Prova: F34/F35 (PIANO.md:304-325). «An empty `SHELL`» resta (pkexec noto).
- Paragrafi su `child_alive()`, close-only, `MSG_STAGE fatal`: valgono (identici). Aggiungere una frase al rifiuto: il caso KDE `kde_refused` (KWin senza `kde_output_management_v2 ≥ 22`) imposta `fatal` come il rifiuto di scala (`child.c:~9235-9255`, F13).
- Tip «Why exec»: vale.

### 8. The channel between the network side and a child — VALE COM'È
`struct head`, magic `FIG1`, `MAX_PIECE`: nessuna modifica nei diff (`child.c` cambia solo SELinux, lingua, KDE). «The twenty message kinds»: invariato; **da ricontare** `grep -c 'define MSG_' fedora45/src/child.c` e confrontare con Ubuntu (nessun `MSG_` nel diff).

### 9. The logind sentinel — VALE COM'È
`sentinel.c` identico, `na` incluso. Tutti i numeri validi.

### 10. Event loops and threads — VALE COM'È
Thread `remotix-kwin` (`kwin.c:536`) e `powerdevil` (`session.c:8342`) esistono ancora; la tabella è corretta. Da non aggiungere: `kwin_output_resize()` usa poll sul descrittore, non un thread (F13).

### 11. Where state lives, owner by owner — DA CORREGGERE
- Righe dconf (r.474-489): «made by the postinst», «removed by the postrm at remove and purge», «`~/.config/dconf/remotix`… removed by the postrm at purge» → `%post` e `%postun` (un RPM non ha purge: tutto avviene alla rimozione, `$1 -eq 0`, spec r.380-431). Aggiungere il file di lavoro `/run/remotix/dconf-compile.tmp` e `/etc/dconf/db/remotix.new` (`session.c`).
- Riga «Card ACL record, enrolments»: vedi sopra (§7): su Fedora probabilmente vuoti; non verificato.
- Riga «The stage…»: vale.
- NUOVE righe Fedora (a): `~/.config/kwinoutputconfig.json` (file di KWin, ricorda l'ultima misura di `Virtual-0`; non si tocca, F8); `/run/remotix/prelocal/<uid>` e `prelocal/.lock` (gancio locale, `local_login.c`); `/var/lib/remotix/net-user-preexisting` (`%pre`); contesti SELinux del contesto di sessione e portachiavi (`child.c`).
- «One number for the cap»: vale (`RCP_SESSION_CAP 10`, 8 utenti dichiarati).
- Non verificato: l'effetto della chiave `ubuntu-lock-on-suspend` di `DCONF_KEYS` (`session.c:1739`) su Fedora (la chiave è di Ubuntu; `dconf compile` non controlla lo schema).

---------------------------------------------------------------------------------------------------

# ch03_lifecycle — «Startup and life cycle» (12 sezioni)

### 1. Service startup, step by step — DA CORREGGERE
- r.4-15 root side: invariato; il database dconf (r.13-14) vedi ch02 §3.
- r.23-27 «The desktop»: «the package ships `debian/org.kde.remotix.desktop`» → `/usr/share/applications/org.kde.remotix.desktop` (spec, `%install`); la frase su `labwc` «only a Recommends» vale per XFCE/LXQt (spec r.90), NON per KDE (KWin da solo).
- r.20-22 «What is offered to the browser»: aggiungere la causa tipica su Fedora: senza RPM Fusion nessun codec (`THIS SERVER CANNOT ENCODE VIDEO`, `NOTHING_IN_COMMON`): è il requisito D1, `%post` avvisa a prima installazione.
- Nuovo (a): prima del root side parte `ExecStartPre=-…remotix-pam-hook check` (`rpm/remotix.service:42`): riga di registro, mai impedisce l'avvio.
- Nota «Old words, current code»: vale (main.c quasi identico).

### 1B. The card that arrives late — DA CORREGGERE
- Ultima frase r.68-69: «`debian/remotix.preinst`» → `%pre` (`rpm/remotix.spec:168-176`: rifiuto se nessun `/sys/class/drm/renderD*`); «The package» → rif invariato.
- Tabella: vale (rootside.c identico). Aggiungere che su Fedora il caso reale è «il nodo c'è ma non codifica» perché manca il driver RPM Fusion (D1): secondo ramo della tabella, ritentato fino a `child_video_retry_worthwhile()`.

### 2. The systemd unit and its life-cycle settings — DA CORREGGERE
- r.72-75: «`debian/remotix.service`, installed by `dh_installsystemd` with `--no-enable --no-start` (`debian/rules`)… postinst's debhelper part does a try-restart» → `rpm/remotix.service`, `%systemd_post`/`%systemd_preun`/`%systemd_postun_with_restart` (spec r.~277, 380-385): installato spento (preset Fedora `disable *`, spec r.218), un aggiornamento riavvia solo se girava (il riavvio chiude i desktop remoti).
- Tabella: valida per `Type`, `After`, `KillMode=mixed`, `Restart`, `RestartPreventExitStatus=78`, `LimitRTPRIO=20`, `LimitNICE=-11`, `EnvironmentFile` (unit identica salvo due righe). AGGIUNGERE righe: `Environment=MESA_SHADER_CACHE_DISABLE=true` (r.39, il probe del lato root non deve usare la cache Mesa in `/root/.cache`: `remotix_t` non ha il tipo) e `ExecStartPre=-…remotix-pam-hook check` (r.42).
- `warn` «Some comments of the package's files are stale» (r.91-97): resta vero per `rpm/remotix.service` (la riga 6 cita ancora «`--without split`»), `rpm/remotix.conf`, `remotix-no-suspend.conf`, `remotix.tmpfiles` («the engine»); **da ricontrollare** i numeri di riga (`grep -n "without split" fedora45/rpm/remotix.service`). `debian/rules` e `debian/remotix.postinst` → spec.

### 3. From password to admission — DA CORREGGERE
- Passo «Admission» (r.136-143): la voce «compositor not installed (XFCE or LXQt without `labwc`)» vale su Fedora (`session_missing_component`, `session.c:769`; pacchetto `labwc`, avviso nello `%post` «`sudo dnf install labwc`»). Aggiungere due rifiuti 0x0E nuovi: KDE senza protocollo di uscita («this KDE session cannot be used», `child.c`, F13) e rifiuto SELinux (uscite 44-47 → nascita fallita).
- «The birth» (r.144-149): il primo accesso include `usermod` — su Fedora vedi ch02 §7 (non verificato).
- Resto (deadline, fixed second, VERDICT, ADMITTED/ATTACH, `wt_dismiss_user_session_over`): valido (webtransport/rcp/main identici).
- Tip finale r.166-171: «within about 10 s; the local-login hook does it before the local desktop starts» vale; il gancio su Fedora è `remotix-pam-hook` (rif a «The local-login hold», ch14).

### 4. Birth of a graphical session — DA CORREGGERE
- GNOME (r.189-193, 219-228): regola D8 su Fedora → la sessione è `gnome` (`gnome.desktop`, `Exec=/usr/bin/gnome-session`, `DesktopNames=GNOME`, nessun candidato chiamato `fedora`: `studio/1-gnome-fedora45.md:78-86`), il template `org.gnome.Shell@.service` si istanzia `@user` (`--mode=user`, studio 1 r.139-140), `XDG_CURRENT_DESKTOP=GNOME` (non `ubuntu:GNOME`). Tolto il discorso su dock e colori di Ubuntu (`--mode=%i` → `ubuntu`). GNOME 51 (non 50); «On GNOME 50 one more guard» → su GNOME 51 la guardia `graphical-session.target` resta (studio 1 r.30: `gnome-session-init-worker` abortisce se la sessione remota è in `closing`); non verificato che sia identica a GNOME 50.
- KDE (r.193-195): DA RISCRIVERE: `startplasma-wayland`, con un drop-in su `plasma-kwin_wayland.service` che ha `Environment=REMOTIX_KDE_HOST=1` e `ExecStart=remotix --kwin-virtual W H -- <wrapper> --virtual --xwayland --width W --height H …` (`session.c:3930-3956`). `--width/--height` valgono solo la prima volta: KWin ricorda l'ultima misura in `~/.config/kwinoutputconfig.json` (F8), perciò il figlio verifica e corregge la misura PRIMA di montare lo stream con `kwin_output_resize()` (`child.c:~9217-9273`).
- XFCE/LXQt (r.195-196): vale (labwc del sistema, 0.20.2).
- «The stage» (r.207-209): vale (libei su Mutter e KWin, dispositivi virtuali su labwc).
- «The logind session» (r.211-218): «logind 258… Ubuntu 26.04 has 259.9» → systemd 262.
- Aggiungere (a): sezione/riquadro «KDE: KWin alone» (misura a caldo `kde_output_management_v2`, rifiuto pulito se manca, ripiego dichiarato se KWin tace, F7/F8/F13/F14). F14: il ridimensionamento a caldo della finestra del browser NON esiste su nessun desktop (misura solo a nascita e riaggancio).

### 5. Detach and reattach — VALE COM'È
`rcp.c`, `webtransport.c`, `main.c` (fuori KDE) invariati; `prove/check-lifecycle.py`, `check-resilience.py` esistono in `fedora45/prove`. Nessun riferimento a distribuzione.

### 6. Desktops found again after a restart — DA CORREGGERE
- Criterio (r.274-276): «`gnome-session-binary`, `startplasma-wayland` or `labwc`» → su Fedora GNOME 51 la catena è `gdm-wayland-session … gnome-session` → `gnome-session-init-worker` (`studio/1-gnome-fedora45.md:106`): il nome dell'iniziatore di sessione è **non verificato** (`gnome-session-binary`?). `startplasma-wayland` e `labwc` valgono. Resto (`rediscover.c`, `FOUND_*`, 256) valido.

### 7. The clocks, each one cited from its constant — DA CORREGGERE
- AGGIUNGERE una riga nel gruppo «Plasma logout rescue»/«Local login hold»: «KDE orderly close in a local-login close: 5 s, `KDE_PRELOCAL_ORDERLY_MS`, `session.c:113`» (prova del proprietario, 25 nov; prima era `WAIT_EXIT_MS` 10 s). Dopo la forzata: tutto fermo 0,54-0,56 s (PIANO.md:446-453).
- Tutte le altre righe: valide (confronto costanti). Da ricontare per sicurezza: `diff <(grep -h '#define [A-Z_0-9]*_MS' ubuntu26.04/src/*.[ch]|sort) <(grep -h '#define [A-Z_0-9]*_MS' fedora45/src/*.[ch]|sort)`.
- `warn` «verified only by mechanism» (r.377-380): vale.

### 8. Ending a graphical session — DA CORREGGERE
- «The close itself» (r.414-421): KDE: «forced stop of the unit» → forzata `StopUnit("graphical-session.target","fail")` (`session.c:4588-4609`, F36), non più `plasma-workspace.target`; GNOME/XFCE/LXQt invariati. Aggiungere: nel close per accesso locale KDE aspetta 5 s, non 10 (`session.c:5639`).
- Paragrafo «Plasma: a logout that stops halfway» (r.422-435): scritto su Kubuntu 26.04/Plasma 6.6 (18 nov, REGISTRO D). Su Fedora c'è Plasma 6.8: il codice è lo stesso (`session_kde_logout_watch`, non nel diff), ma che il soccorso scatti su 6.8 è **non verificato**; quello che è verificato è F36 (la forzata di `exit_kde(TRUE)`): ordinata che non finisce → forzata → tutto fermo in ~0,5 s. «Known limits»: valgono (nessuna prova diversa).
- «The light close» (r.436-442): «stops REMOTIX's own KDE compositor service only if its processes carry REMOTIX's mark» → il segno è `--kwin-virtual` (riga di comando) o `REMOTIX_KDE_HOST=1` (ambiente), `kdehost.h:50-61`; la regola SELinux che permette lo stop/status sulle unità `xdm_unit_file_t` è nuova (`selinux/remotix.te`, F36).
- «What was verified» (r.447-456): DA RISCRIVERE: tutte le cifre Ubuntu (VM GNOME 19 nov, `studio/giro2-kde.md`, Kubuntu) vanno tolte. Fedora: prove di chiavetta 25 nov (GNOME, XFCE 1,7 s, LXQt 0,7 s OK con h1; KDE OK con i1/i2), `check-prelocal.py` P1–P8 PASS su KDE, `check-kde-exit.py`. Non provato: abbandono su KDE; programmi lenti a chiudersi.
- Nuovo (a): limite dichiarato F16 (programmi di sfondo KDE abortiscono con la chiusura «da fuori», core dump di `kaccess`, `kded6`, `plasmashell`… misurati sulla VM `kde`) e «GNOME ha la stessa costruzione di KDE e nessuna ultima difesa» (messo da parte, PIANO.md:419-421).
- Nota «TERMINATE_SESSION has no trigger»: vale (`page.html` identico).

### 8B. When the session ends before the stage is gone — DA CORREGGERE
- Paragrafo d'apertura r.459-464: tutta la storia di RealtimeKit/PipeWire con le misure del 18 nov su «the 26.04 box» (17 s → 6 s, XFCE 0,25 s) è di Ubuntu: su Fedora non misurata → togliere le cifre, dire «non verificato su Fedora» (la regola è nel codice identico: `session_over_early()`, `child.c`).
- Condizioni e tabella `session_life()`: valgono. «KDE is left out (`stage_kwin`)»: vale, e su Fedora il KWin è `--virtual` (non annidato): se questa esclusione sia ancora necessaria è **non verificato** (il riavvio di KWin da parte di systemd lascia il nome senza proprietario).
- «The stage refused for the scale» (r.499-509): vale per GNOME (monitors.xml, chiave `scaling-factor` bloccata). Aggiungere il secondo rifiuto: KDE senza `kde_output_management_v2` (stessa via `fatal`/`scale_refused`, F13).
- Nuovo: «Unknown is not dead» e il ramo «unknown» all'avvio del figlio: non verificati su Fedora (come su Ubuntu, REGISTRO C5).

### 9. Stopping the service — DA CORREGGERE
- Passi 1-5 e paragrafi: validi (rootside.c e main.c identici).
- Tip finale (r.560-568): «the postinst's debhelper part restarts… The prerm does not close sessions on an upgrade» → `%systemd_postun_with_restart` e `%preun` (chiude le sessioni solo se `$1 -eq 0`, spec r.280-): su aggiornamento il riavvio chiude comunque i desktop (identico effetto). «On Ubuntu… `/etc/needrestart/conf.d/remotix.conf` (`debian/needrestart/remotix.conf`)» → il pacchetto RPM installa lo stesso file (`rpm/needrestart.conf` → `/etc/needrestart/conf.d/remotix.conf`, spec `%files`), ma `needrestart` **non è di serie su Fedora**: se esista nei repository e se `dnf-automatic` lo usi è **non verificato**. La nota va riscritta in modo condizionale.
- Aggiungere a «Tidy»/ultimo passo (r.536-543): alla rimozione del pacchetto `%preun` chiude le sessioni, ferma il servizio, toglie il gancio PAM e solo allora il `graphical-session.target` dell'utente se non ha altra sessione grafica (spec r.280-340).

### 10. The log line that marks each step — DA CORREGGERE
- Riga «Desktop cannot be born» (r.597): vale per XFCE/LXQt; per KDE aggiungere la riga di rifiuto («⛔ KDE: SESSION REFUSED, and closed — …», `child.c`) e la riga del ripiego («⚠ KDE: KWin's output did not reach WxH… DECLARED FALLBACK»).
- Riga «GNOME session chosen» (r.595): il candidato sarà `gnome` (non `ubuntu`).
- Riga «Service up»: aggiungere «SELinux: born in system_u:system_r:remotix_net_t:s0» o «⚠ SELinux: on, but the root side is not in remotix_t» (`walls.c:315-342`) accanto a «the network side's walls in force».
- AGGIUNGERE: riga d'avvio del gancio (`remotix-pam-hook check`, journal dell'unità) e la riga di chiusura di una connessione con il motivo: «connection with X closed (n left): …» (`transport.c:1021-1092`, F23; testi: `tls_alert_name`, `transport_error_name`, «idle timeout»).
- Aggiungere i messaggi dei codici 44-47 (`child.c:1144-1147`).
- Il paragrafo finale sulle priorità (33 pattern, `REGISTRO-priorita.md`): il file esiste ed è identico a Ubuntu: vale (cifre non rimisurate su Fedora).

---------------------------------------------------------------------------------------------------

# ch04_transport — «Transport» (14 sezioni)

### 1. The transport stack and the network side — DA CORREGGERE
- Nota «Libraries» (r.64-71): «`debian/control` records them in `Static-Built-Using` together with the labwc (0.9.3) and wlroots (0.19.2)» → `Provides: bundled(ngtcp2) = 1.25.0` e `bundled(nghttp3) = 1.18.0` (spec r.97-98) e `linked.json`; togliere labwc/wlroots. «26.04 packages of ngtcp2 (1.16) and nghttp3 (1.12)» → Fedora: ngtcp2 1.22.1 (`build/quic-static.sh:3`), `nghttp3-devel` assente (studio 3, riga 13); `studio/8-pacchetto-e-prove.md` non esiste in fedora45 (citare `quic-static.sh`).
- «OpenSSL is the system library (libssl-dev 3.5 or later; 3.5.5 on 26.04)» → `openssl-devel` 4.0.3 (D8: si usa quello di serie, nessun ripiego su `openssl3`; `build-rpm.sh:20-21`, spec r.49). Che `ngtcp2_crypto_ossl` usi «the native QUIC API of OpenSSL 3.5» e funzioni identica su 4.0 è dimostrato solo dal fatto che il pacchetto si costruisce e passa le prove (PIANO.md:316-320); il comportamento specifico di 4.0 non è documentato: «non verificato».
- Tabella FILES: vale; `transport.c` ha ora la funzione `close_why()` (`transport.c:1021`) e le tabelle `tls_alert_name`/`transport_error_name`: una frase in più.
- Figura e testo restanti: validi.

### 2. The WebTransport announcement and the SETTINGS rewrite — VALE COM'È
`webtransport.c/.h` identici.

### 3. Listeners, sockets and port 7447 — DA CORREGGERE
- r.107-115: «`debian/remotix.service`» → `rpm/remotix.service` (r.45: stessi `--address 0.0.0.0 --name %H --port … --split --journal`); `remotix.conf` in `/usr/share/remotix/`: vale.
- Il `warn` «TCP and UDP, and nobody opens them» (r.116-124): DA RISCRIVERE per firewalld. Fatti: il pacchetto porta `/usr/lib/firewalld/services/remotix.xml` (7447/tcp + 7447/udp, `rpm/remotix.firewalld.xml`), lo definisce e non lo apre mai (D5); `%firewalld_reload` (spec r.276, 387) perché `firewall-cmd --permanent --add-service=remotix` non risponda più INVALID_SERVICE (F20); riga per l'amministratore: `sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload` (zona predefinita; altra zona: `--zone=NOME`; F20). Zone osservate (PIANO.md:90-91, studio): GNOME e KDE (zona Workstation, porte da 1025 in su aperte: la 7447 è raggiungibile comunque), XFCE e LXQt (zona `public`, chiusa di serie). Sostituire «ufw is a recommended package of ubuntu-standard» (falso per Fedora). F17: il file XML è stato corretto (commento con `--`).
- Paragrafo IPv6: vale (IPv4 `0.0.0.0`, nessuna prova IPv6: «non verificato»).
- Tabella listeners e `SO_REUSEADDR`: vale.

### 4. QUIC transport parameters — VALE COM'È
`transport.c`: parametri non toccati (il diff è solo `close_why`, righe 955-1080 e due punti IDLE_CLOSE).

### 5. Admission of new connections, Retry and Stateless Reset — VALE COM'È
Idem; tutti i numeri invariati (`hsrate.h`, `resetcap.h`, `cid.*` identici).

### 6. TLS contexts and the two certificates — DA CORREGGERE
- r.264-269: «`debian/remotix.tmpfiles`» → `rpm/remotix.tmpfiles` (stesso contenuto: `/var/lib/remotix/net` 0700, `Z`, `z`); sysusers `rpm/remotix.sysusers`.
- Gruppi `X25519MLKEM768:…` (r.239-241): «If the installed OpenSSL does not know the ML-KEM group…»: con OpenSSL 4.0 che il gruppo sia noto e che il key share funzioni è **non verificato** (la riga 563 del manuale Ubuntu lo dichiarava non verificato anche con 3.5.5). Il testo di sezione resta valido come regola.
- Resto (due certificati, 13 giorni, P-256, `.ours`, `--name`): vale (certificates.c/tls.c identici).

### 7. Certificate pinning and the fingerprint endpoint — DA CORREGGERE
- AGGIUNGERE (a) il fatto emerso il 22 nov (F23, PIANO.md:237-239): il certificato di sessione ha `notBefore` = adesso − 1 h; un dispositivo client con l'orologio sballato vede «Opening handshake failed» perché il certificato risulta «non ancora valido». Requisito: orologio del client giusto (va anche nei «Requirements»). Il registro della connessione ora dice chi ha chiuso e perché (`close_why`, F23).
- Il resto: valido (page.c, certificates.c identici).

### 8. The page server on TCP — VALE COM'È
`page.c` e `page.html` identici; `/usr/share/remotix/page.html` vero (spec `%install`). La nota «No administrator unblock» vale (`rpm/remotix.service` senza `--command-socket`; SPECS identico).

### 9. The WebTransport layer: SETTINGS, CONNECT, streams and capsules — VALE COM'È
`webtransport.c` identico.

### 10. Streams, datagrams and the send queue — VALE COM'È

### 11. Idle timeout, keep-alive PINGs and the dead line — VALE COM'È
Il testo «the log says “thirty seconds of silence”» esiste ancora (`transport.c:2594`); dopo F23 anche la riga di chiusura dice «idle timeout» (`transport.c:2187`): se si vuole citarla, una frase in più, non obbligatoria.

### 12. Congestion, pacing and the video queue — VALE COM'È
Nessun diff.

### 13. One connection from first packet to close — DA CORREGGERE
- Passo «Close» (r.540-543): aggiungere che la riga «connection with X closed (n left)» porta ora il motivo (`close_why()`, `transport.c:1092`, F23): chi ha chiuso (PEER / WE), codice di trasporto o alert TLS (42 `bad_certificate`, 45 `certificate_expired`…), «idle timeout», o «no error recorded».
- Il resto (accept_conn, open_http3, verdict routing): vale.

### 14. What was verified for the transport — DA RISCRIVERE
Tutta la tabella cita giri Ubuntu (unione2/5, VM GNOME 19 nov, AppArmor, `package-snap.py`, OpenSSL 3.5.5). Per Fedora (da PIANO.md): browser Chrome/Firefox via `prove/all.sh` (giro finale h1: gnome 52 PASS + `all.sh` 39 PASS, kde 76, xfce 60, lxqt 60); prove del proprietario da Windows (F23: errore d'orologio), Linux, Android su tutti e quattro i desktop; rete caduta e riavvio del servizio: `check-resilience.py` (esito Fedora non registrato in modo isolato: **non verificato** dalla sola lettura di PIANO/registro); installazione e avvio dietro il muro SELinux: provati su quattro VM e quattro live (0 AVC nostri); firewalld: F17/F20; IPv6: nessuna prova; OpenSSL 4.0: costruzione e prove sì, ML-KEM e rotazione certificato «non verificato»; Safari/iOS mai. Riga «AppArmor» → «SELinux».

---------------------------------------------------------------------------------------------------

# ch05_rcp — «The RCP/1 protocol» (14 sezioni)

### 1. RCP/1 in one page and where its specification lives — VALE COM'È
`rcp.c/.h`, `docs/RCP.md` identici. Il numero «twenty-nine» hook di `rcp_hooks` è del codice identico: **da ricontare** `grep -c` sui puntatori di `struct rcp_hooks` in `fedora45/src/rcp.h` (invariato).

### 2. Message map: every type and the function that handles it — VALE COM'È
### 3. Framing and the rigor rule as implemented — VALE COM'È
### 4. The handshake step by step — VALE COM'È
(per i tre: nessun riferimento a distribuzione, codice identico)

### 5. HELLO, HERE_I_AM and capability negotiation — DA CORREGGERE
- Nota «No bench function in the product» (r.172-174): «`debian/rules` refuses to package if `BENCH_ON`… `build/build-deb.sh` has a check» → `%build` della spec: `grep -qx '#define BENCH_ON 0' src/rcp.c` (R13) e controllo di `build/build-rpm.sh`.
- Riga `video.codec` (r.158) e frase finale r.170-171: aggiungere (a) che su Fedora senza il driver RPM Fusion la lista dei codec è vuota e HELLO riceve `NOTHING_IN_COMMON` (0x09): è la manifestazione del requisito D1; «the package also refuses a new installation on a machine without a render node» vale (`%pre`).
- Resto: valido.

### 6. CREDENTIALS, the verdict and the fixed second — VALE COM'È
### 7. ATTACH and SESSION as implemented — VALE COM'È
### 8. Key frames, canvas, view and layout messages — VALE COM'È
### 9. Input, clipboard and cursor messages — VALE COM'È
### 10. Rate limits on a connected client — VALE COM'È
### 11. Clocks of an attached session — VALE COM'È
(codice identico; costanti confermate dal confronto. Nota: la riga «Limit for the key level of the ban» del §13 resta vera.)

### 12. FAREWELL, REJECTED and the sixteen reasons — DA CORREGGERE
- Riga `0x0E SESSION_UNSERVABLE` (r.338): l'elenco delle strade vale e va ESTESO con i due rifiuti di Fedora: KDE senza `kde_output_management_v2 ≥ 22` («this KDE session cannot be used», `child.c`, F13) e nascita fallita per rifiuto SELinux (uscite 44-47). La frase «the page counts six routes (`page.html`…)» resta vera perché `page.html` è identico, ma le strade del server sono ora più di quelle dichiarate dalla pagina.
- Riga «compositor not installed… `labwc`»: vale per XFCE/LXQt.
- Riga `0x04 LOCAL_SESSION_PREVAILED` (r.328): il suo percorso ora passa dal gancio `remotix-pam-hook` su quattro schermate di accesso; il testo («by hand at the real login screen of Ubuntu and Kubuntu») è di Ubuntu → Fedora: a mano su macchina vera 25 nov, GNOME/XFCE/LXQt/KDE OK (KDE dopo F36).
- Resto: valido.

### 13. Where the code departs from RCP.md — DA CORREGGERE
- Riga «Unblocking a banned address» (r.366): «`debian/remotix.service`» → `rpm/remotix.service`; il resto vale. Le altre righe (REJECT_FLOOR, PACE, 0x0F/0x10, 29 hook, PINGs, limite 20) valgono (RCP.md e rcp.c identici).

### 14. What was verified about RCP — DA RISCRIVERE
Come ch04 §14: sostituire i giri Ubuntu (unione1–5, VM GNOME) con le prove Fedora (`check-base`, `check-lifecycle`, `check-multiuser`, `check-resilience`, `check-ban`, `check-input`, `check-clipboard`, `check-prelocal`, `check-kde-*`; giro finale h1; PIANO.md:316-320). Per la riga «Reasons 0x03/0x04/0x06/0x0E»: `0x04` ora provato anche su macchina vera con le 4 chiavette (F6/F9, PIANO.md:343-367); `0x0E` per il rifiuto KDE/SELinux «non verificato» con un controllo proprio. «The 12-hour step of the ladder, BUDGET_FULL, fuzz harnesses»: restano non verificati (come Ubuntu). Il caso 10.0.2.2 della VM (ban su un solo indirizzo) vale anche per le VM Fedora (stesso banco QEMU user-net): non verificato per Fedora.

---------------------------------------------------------------------------------------------------

# Liste richieste

## (a) Cose che esistono solo su Fedora e meritano una SEZIONE NUOVA (dove)
1. **ch01, subito dopo «What REMOTIX is…»: «Requirements and what Fedora adds»** — D1 (codec da RPM Fusion: `mesa-va-drivers-freeworld`, NVIDIA proprietario; nessuna codifica software; rifiuto senza scheda, avviso se non codifica), D3 (SELinux enforcing con modulo proprio), D5 (firewalld, porta aperta dall'amministratore), D6 (portachiavi come Debian/Ubuntu), D7 (XFCE sfondo nero e niente icone), orologio del client (F23), nessuno spegnimento dal desktop. Cita `fedora45/PIANO.md` (D1–D8), non `docs/DECISIONS`.
2. **ch02, dentro «The network side and its walls» o come sezione a sé: «The SELinux wall»** — domini `remotix_t`, `remotix_net_t`, `remotix_hook_t`, `remotix_prelocal_t`; scrittura dell'attributo exec (`walls.c:260-348`); lato root largo (F27); prova negativa (F24/F31); rifiuti non nostri (F15/F28). Il dettaglio delle regole va in ch14 (fuori gruppo): dire dove.
3. **ch02 §7: «The SELinux context of the user's session»** — contesto da `xdm_t`, uscite 44-47, portachiavi (F5/F25, `child.c:1726,1794`).
4. **ch03: «KDE: KWin alone»** (nasce, misura, rifiuto, ripiego, forzata `graphical-session.target`, attesa 5 s, F7/F8/F13/F14/F36) — oppure integrata in §4 e §8; consigliata sezione propria perché sostituisce la parte «labwc annidato».
5. **ch03 o ch04: «Why a connection closed»** (`close_why`, F23).
6. **ch04 §3: sottosezione «The firewall: firewalld service and zones»** (F17/F20).
7. **ch03 §2: la coppia `ExecStartPre … remotix-pam-hook check` + trigger RPM** in breve, con rif a ch14 «The local-login hold» per il dettaglio sulle quattro schermate (gdm, plasmalogin, lightdm, sddm; F6/F9/F21).
8. **ch02 §7 o ch03 §4: «Language and PATH of the remote session»** (F4/F34/F35: AccountsService letto da root, `LC_*`, `LANGUAGE`, `~/.local/bin`).
9. **ch01 §2 (riscritta): limiti noti e prove su macchina vera da chiavetta** (`server/live-installa.sh`).

## (b) Cose di Debian/Ubuntu da TOGLIERE
- ch01: tutto ciò che riguarda `build-deb.sh`, `RX_VERSION` in `build-deb.sh`, `.deb`, `debian/`, container `debian:trixie`/`ubuntu:26.04`, `boxes/`, `labwc-ospite/`, riga «Our labwc», sapori Ubuntu/Kubuntu/Xubuntu/Lubuntu, sezione «What was verified» Ubuntu per intero, licenza labwc/wlroots (a meno che `LICENSE.md` venga corretto).
- ch02: `--kwin-nested` e labwc (riga ruoli), AppArmor `remotix_network` e l'intero `warn` C4 (profilo, XKB di Ubuntu, `complain`), `apt`, `dconf-cli`, «Ubuntu 26.04 has 259.9», `/snap/bin`, `debian/rules`/`postinst`/`postrm`/purge.
- ch03: `debian/*`, `dh_installsystemd`, `ubuntu` come sessione GNOME (`org.gnome.Shell@ubuntu`, `ubuntu:GNOME`), KWin annidato nel labwc, Kubuntu/Plasma 6.6, le cifre di RealtimeKit e dei giri Ubuntu, `needrestart` come «on Ubuntu».
- ch04: `ufw`/`ubuntu-standard`, `Static-Built-Using`, `labwc 0.9.3/wlroots 0.19.2`, ngtcp2 1.16/nghttp3 1.12, OpenSSL 3.5.5, `studio/8-pacchetto-e-prove.md`, tabella dei giri Ubuntu.
- ch05: `debian/rules`, `build/build-deb.sh`, `debian/remotix.service`, giri `unione1…5`/Ubuntu e Kubuntu.
- Difetti di sorgente da non ripetere nel manuale (o da correggere nei file, decisione al proprietario): `fedora45/CLAUDE.md:6` («RPM … to be written»), `fedora45/LICENSE.md:95-102` (labwc), `fedora45/src/local_login.c:3-4,20` (`pam-auth-update`, «systemd 257»), commenti Ubuntu in `session.c` (`ubuntu-lock-on-suspend` r.1739; `lubuntu-update` r.7031) e nome dei file di studio citati nei commenti.

## (c) Riferimenti `rif("…")` che si ROMPONO se il titolo di una sezione cambia (titoli del gruppo G1, con chi li cita)
- «Overall architecture» (capitolo): ch01 ×3, ch04, ch08, ch13 ×2, ch14, ch22 ×10
- «Startup and life cycle» (capitolo): ch01 ×3, ch04, ch06, ch12, ch14, ch15, ch21, ch22 ×3
- «Transport» (capitolo): ch02, ch05 ×7, ch08 ×2, ch09, ch14, ch22 ×4
- «The RCP/1 protocol» (capitolo): ch01 ×3, ch02, ch03, ch04 ×4, ch06 ×2, ch07, ch08 ×2, ch09 ×4, ch13, ch16, ch20, ch22 ×4
- «What was verified and what was not» (ch01 §2): ch04, ch05
- «The root side»: ch03 ×2 · «The network side and its walls»: ch02, ch03 ×2 · «The per-user child»: ch03 ×2
- «The card that arrives late»: ch03 · «From password to admission»: ch03 ×2, ch04, ch05
- «Desktops found again after a restart»: ch02, ch03 ×2, ch16, ch24 · «Ending a graphical session»: ch01, ch02, ch03 ×3, ch12
- «When the session ends before the stage is gone»: ch01, ch02 ×2, ch03, ch06, ch09 · «Stopping the service»: ch02, ch03 ×5, ch12, ch14 ×2, ch15 ×2, ch16, ch18
- «QUIC transport parameters», «Admission of new connections, Retry and Stateless Reset», «Idle timeout, keep-alive PINGs and the dead line», «What was verified for the transport»: tutti solo dentro ch04
- «Message map: every type and the function that handles it», «Clocks of an attached session», «FAREWELL, REJECTED and the sixteen reasons»: solo dentro ch05
Titoli di altri gruppi citati dal G1 (se gli altri gruppi li rinominano, si rompono i capitoli 1-5): «Screen capture» (ch06), «Quality, degradation and budget» (ch08), «Input» (ch10), «Audio and clipboard» (ch11), «The four desktops» (ch12), «Login and its defences» (ch13), «The local-login hold», «Security model», «Local excludes remote and the session cap» (ch14), «The package» (ch15), «Logging and diagnostics» (ch16), «Testing» (ch17), «Build and release» (ch18), «Conventions» (ch21), «Appendix A — Data structures and messages» (ch22), «Appendix C — Known issues and open points» (ch24). Elenco calcolato con uno script di sola lettura sui sorgenti Ubuntu.
Suggerimento: NON rinominare nessuno dei titoli sopra; se serve un titolo nuovo («Requirements and what Fedora adds», «KDE: KWin alone»…) è una voce aggiunta e non rompe nulla. `build.py --check` dirà comunque quali `rif` non si risolvono.

## Punti non verificati (riassunto)
- Contenuto vero delle regole SELinux (`selinux/remotix.te`) non letto riga per riga: per il manuale tecnico va fatto un riscontro in ch14.
- Effetto su Fedora di `usermod -aG` / `render_grant` (nodo render 0666) e della chiave dconf `ubuntu-lock-on-suspend`.
- Nome dell'iniziatore di sessione GNOME 51 per il criterio di `rediscover.c` («gnome-session-binary»?).
- Soccorso del logout Plasma (`session_kde_logout_watch`) su Plasma 6.8; esclusione di KDE dall'«early farewell» ancora necessaria con KWin `--virtual`.
- ML-KEM (`X25519MLKEM768`) e rotazione del certificato con OpenSSL 4.0; IPv6; esistenza e uso di `needrestart` su Fedora.
- Cifre dei giri Fedora (PIANO.md) non controllate sui log (stanno sul server e in `~/remotix-prove-live/`).
