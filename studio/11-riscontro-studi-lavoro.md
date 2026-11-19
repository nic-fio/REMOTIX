# Studio 11 — Riscontro: che cosa hanno segnalato gli studi e i rapporti, e che cosa ne è stato

Data: 18 nov 2026 (notte). Solo lettura: nessun file del prodotto, delle prove o dei rapporti è stato toccato; questo è l'unico documento scritto.
Perché: nel giro di misura sono usciti due difetti (il gestore di effetti `picom` su Lubuntu, l'uscita da KDE «da riprovare») che gli studi
avevano già segnalato e che nessuno aveva trasformato in lavoro. Qui si controlla, voce per voce, che non ce ne siano altri.

## Come leggere le tabelle
Stati (la prima parola della colonna «Stato» è quella che conta; i numeri in fondo si contano su di essa):
- **FATTO**: c'è la modifica nel codice o nelle prove (dove: diff in `~/Documenti/REMOTIX-UBUNTU-lavori*/` o `file:riga` dell'albero attuale).
- **VERIFICATO**: visto dal vivo nel giro `unione1` (rapporti `studio/giro1-*.md`) o nello studio 10.
- **IN VERIFICA ORA**: coperto dal giro di conferma `unione2` in corso (righe del giro, finestra di errore su Lubuntu, uscita KDE presto e con
  lavoro non salvato, portachiavi GNOME, snap dentro la sessione, variabili Xubuntu).
- **DECISO**: scelta del proprietario (quale).
- **RIMANDATO**: si può accertare solo su macchina vera (schermata di accesso, AppArmor severo, snap, needrestart, confronto con un accesso locale).
- **SCOPERTO**: né fatto, né verificato, né deciso, e fattibile nei contenitori o nel codice. Sono raccolte in fondo, ordinate per rischio.
Quando una voce è «FATTO» ma l'effetto dal vivo non è stato visto, lo si scrive nella nota; se manca anche quello e la cosa è fattibile, è SCOPERTO.
Le decisioni del proprietario già prese (non riproposte): 1.0.0; componente KDE proprio; repo unico; niente macchine con più desktop;
nessuna segnalazione a monte; pulsanti Ctrl+Alt+Canc/Fine tolti; portachiavi GNOME e variabili `56xubuntu-session` come su Debian;
`~/.profile` e `~/.gnomerc` non letti come su Debian.
Sigle: **D-A** = decisione A (repo unico), **D-D** = niente più desktop installati, **D-E** = niente segnalazioni a monte, **D-K** = componente KDE proprio,
**D-P** = portachiavi GNOME + Xubuntu come Debian, **D-F** = file di avvio personali non letti.

---

## PIANO.md e REGISTRO-problemi.md (fonte: sezioni «Dopo lo studio», «Avanzamento», «Da fare prima del rilascio», «Decisioni rimandate»)

| # | Voce segnalata | Stato |
|---|---|---|
| P1 | Passo 1 pacchetto (nomi, dipendenze, universe) | VERIFICATO: pacchetto unico costruito, lintian 0/0, installa sui 4 box (PIANO «Avanzamento») |
| P2 | 3a GNOME 50 avvio | VERIFICATO: G2 (`--mode=ubuntu`, dock, Yaru), G4 |
| P3 | 3b riconoscere i 4 gusti | VERIFICATO: X1 (`DESKTOP_SESSION=xubuntu`), L1, K1; codice `session.c:389-391` |
| P4 | 3c cartelle come accesso locale, `/snap/bin`, tre variabili Xubuntu | VERIFICATO per cartelle e PATH (G1, X1, L1, K1); variabili Xubuntu: DECISO (D-P: non si riproducono) |
| P5 | 3d KDE componente proprio | VERIFICATO: K1 (hash uguale al .deb), studio 10 (759/760 fotogrammi contro 0/755) |
| P6 | 3e nome utente inesistente | VERIFICATO: riga di `check-ban` (stessa frase, stessi tempi) PASS nel giro1; nessuna modifica (già nel codice 1.0.0) |
| P7 | 3f pannello XFCE perso | VERIFICATO nei casi a–d (X2–X5); casi H1b e «not repaired now» mai prodotti → vedi S9.5 / **SCOPERTA 4** |
| P8 | 3g avviso falso fifo | VERIFICATO: G3 (nessun «close at the exec»); `child.c` senza `--session-fd`, `DECISIONS-11.md` §11.55 annotato |
| P9 | 3g needrestart non riavvii `remotix.service` | FATTO: `debian/remotix.needrestart` (file nel pacchetto, L6); effetto non visto → RIMANDATO (needrestart assente nel box) |
| P10 | 3g due percorsi AppArmor (xkb) | FATTO: `debian/remotix_network.apparmor:41-46`; in severo → RIMANDATO |
| P11 | 3g chiave `ubuntu-lock-on-suspend` | FATTO: `session.c:1651` |
| P12 | 3h prove che presumono Debian (sudo, terminale, percorsi), VM senza scheda video | FATTO: `prove.diff`, `check-desktop.py` (sudo-rs, ptyxis), `vm.sh`; la VM Ubuntu non è mai stata avviata → **SCOPERTA 24** |
| P13 | Da vedere solo provando: ridimensionamento GNOME 50 | VERIFICATO: righe `desktop/canvas-limits`, `lifecycle/reattach-other-size`, `reattach-windows-inside` PASS su GNOME |
| P14 | Firefox e altri snap dentro la sessione | IN VERIFICA ORA (snap nella sessione) |
| P15 | Portafoglio KDE | VERIFICATO in parte: K5 (nessuna finestra, `kwalletd6` mai visto); app che usa davvero il portafoglio mai provata → **SCOPERTA 8** |
| P16 | Portachiavi GNOME | DECISO D-P; fatti in verifica ora |
| P17 | Uscita da KDE | FATTO (3 giri di revisione, `kde-uscita.diff`) + IN VERIFICA ORA; vuoti rimasti → **SCOPERTA 1** |
| P18 | Schermata di accesso GNOME 50 con remoto aperto, «Force Stop» | RIMANDATO (prova su macchina vera) |
| P19 | AppArmor severo | RIMANDATO (serve Ubuntu vera) |
| P20 | Xubuntu costruita con accorgimento (DM) | FATTO: `boxes/Containerfile`; VERIFICATO X1 (lightdm, sessione xubuntu) |
| P21 | Difetto 1 del giro: KDE Log Out presto | FATTO (`kde-uscita.diff`) + IN VERIFICA ORA |
| P22 | Difetto 2 del giro: Lubuntu `picom` | FATTO (`lxqt-avvio.diff`; `session.c:6231` lista `LXQT_X11_COMPOSITORS`) + IN VERIFICA ORA |
| P23 | `mouse-drag`/`tap-and-half-drag` non verdi | FATTO (`prove2.diff`, rilascio dagli eventi grezzi; registro B3-bis) + IN VERIFICA ORA |
| P24 | Righe Ctrl+Alt+Canc/Fine | DECISO (pulsanti tolti, prove allineate: registro B3; `prove2.diff`) |
| P25 | KDE `media/codec` Firefox (bordo 130 px, non rieseguito) | IN VERIFICA ORA (righe del giro); resta il rischio di archiviarla se passa una volta sola |
| P26 | KDE `reattach-windows-inside` | FATTO (`prove2.diff`, misura della finestra) |
| P27 | KDE `settings-intact`, `lifecycle/logout` FAIL (variante ksmserver «NoReply» 35 s) | IN VERIFICA ORA; ⚠ la cura nuova «se ksmserver non risponde non si forza nulla» non copre questa variante → nota alla **SCOPERTA 1** |
| P28 | Lezione 1: installare lo stesso numero di versione non sostituiva il programma | FATTO: `box.sh` con `--reinstall`; «confronto dopo l'installazione» ancora da aggiungere → **SCOPERTA 10** |
| P29 | Lezione 2: «0 avvisi» va letto nel registro | **SCOPERTO**: `build/build-deb.sh` non conta gli avvisi del compilatore (→ **SCOPERTA 10**) |
| P30 | Lezioni 1-3 «da portare nel registro dei problemi» | **SCOPERTO**: nel registro non c'è (grep) → **SCOPERTA 12** |
| P31 | Data di costruzione giusta; testi di licenza ripuliti dai resti della 1.5 (Go, `.run`, `remotix-install`) | RIMANDATO (annotato nel PIANO «prima del rilascio»); controllato: `LICENSE.md:13`, `THIRD-PARTY-LICENSES:11,27-29,1661…` li hanno ancora → **SCOPERTA 20** |
| P32 | Decisioni rimandate: file di avvio personali | DECISO D-F |
| P33 | Registro: voce per ogni problema chiuso/rimandato (regola del PIANO) | **SCOPERTO**: del lavoro Ubuntu ci sono solo B3-bis, la riga KDE in D e E1; mancano pannello XFCE, avvio GNOME 50, pidfd, needrestart, labwc proprio, picom, sudo-rs ecc. → **SCOPERTA 12** |
| P34 | `DECISIONS-11.md` aggiornato con le scelte Ubuntu | **SCOPERTO**: nel diff solo 4 righe (nota `--session-fd`); niente su labwc proprio per Kubuntu, ripristino D-153, mappa nomi, needrestart → **SCOPERTA 12** |
| P35 | Registro A1/A2 «su una distribuzione nuova»: remoto aperto → riavvio servizio → accesso locale | RIMANDATO (schermate di accesso vere) |
| P36 | Registro B2, regola «un tempo strano va spiegato» (RealtimeKit nei contenitori) | VERIFICATO: G3 spiega i 25 s |

---

## Studio 1 — Avvio GNOME 50 (fonte: §8 fatti, §9 problemi, §10 non si sa, §11 prove)

| # | Voce | Stato |
|---|---|---|
| S1.1 | Unità shell: template + istanza | VERIFICATO: `session.c:3045` (`SESSION_UNIT_SHELL_MODEL`), G2 `gnome-shell --headless --no-x11 --mode=ubuntu` |
| S1.2 | Drop-in con `--mode=%i` | VERIFICATO: `session.c:3271`; G2 |
| S1.3 | Pulizia delle istanze | VERIFICATO: `session.c:4201`; G5 (cartella sparita dopo Log Out, senza linger) |
| S1.4 | Scelta sessione `ubuntu`/`gnome` per `ID` os-release | FATTO: `session.c:923`; con `gnome-session` installato accanto: DECISO D-D (nessun supporto a più sessioni); prova mai fatta |
| S1.5 | D-153 per `ubuntu` (`DESKTOP_SESSION`, `/usr/share/ubuntu` in `XDG_DATA_DIRS`) | VERIFICATO: G1 valori per intero |
| S1.6 | Guardia `graphical-session.target` | VERIFICATO: `session.c:3802-3820`; G4 rifiuto→attesa→nascita; ma rientro reale vicino al Log Out non misurato → **SCOPERTA 2** |
| S1.7 | Convivenza locale/remoto con i nomi nuovi (A1/A2) | RIMANDATO (accesso locale vero) |
| S1.8 | Variabili del leader 50 non in `OUR_VARIABLES` (`GNOME_DESKTOP_SESSION_ID`, `QT_IM_MODULES`) | **SCOPERTO**: nessuna occorrenza in `session.c`; prova 6 dello studio (linger) non fatta → **SCOPERTA 9** |
| S1.9 | Commenti e diagnostica con nomi di 48 | **SCOPERTO** (solo commenti): `child.c:1674` dice ancora `ConditionEnvironment` (50: `Assert…`), `rediscover.h:27` `gnome-session-binary` → **SCOPERTA 21** |
| S1.10 | Login shell e `~/.profile` | DECISO D-F |
| S1.11 | Tempi di nascita (`WAIT_STARTUP_MS`, `BIRTH_REIN_MS`) con GNOME 50.1 | VERIFICATO: nascite senza rosso nel giro (116/124); G4 primo fotogramma 27 s solo nel caso di rifiuto |
| S1.12 | Dipendenze del `.deb` | VERIFICATO (installa sul box GNOME; `recognize_desktop` ok) |
| S1.13 | Fatto 2 (PULIZIA voce 5 falsa con `ubuntu`+`gnome`) | FATTO (come S1.4) |
| S1.14 | Fatto 3-5 (storia, `SHELL=` vuoto, Assert) | VERIFICATO: G1 `SHELL=` vuoto, shell su 50 parte |
| S1.15 | Fatto 6 (A1 nasce da nomi di 48) | FATTO nel codice (guardia); la prova locale → RIMANDATO |
| S1.16 | §10: template dal vivo con il drop-in | VERIFICATO: G2, G5 |
| S1.17 | §10: output `Requires` di `gnome-session@ubuntu.target` | VERIFICATO indirettamente (nascita riuscita, `session.c:3045` lo legge); non registrato a parte |
| S1.18 | §10: tempo reale di nascita con estensioni | VERIFICATO: giro1 (nascite ok) |
| S1.19 | §10: `GetCurrentState` a zero monitor | VERIFICATO: nascita senza monitor ok in G2/G4 |
| S1.20 | §10: `gnome-session-init-worker` con `SHELL=` vuoto sotto la sessione `remotix` | VERIFICATO: G1, G3 |
| S1.21 | §10: effetto di `/usr/share/ubuntu` mancante / assistente primo avvio | VERIFICATO: G2 (nessun `gnome-initial-setup`, un utente nuovo, un accesso) |
| S1.22 | §10: abort «A graphical session is already running!» nel registro | VERIFICATO: G4 (riga di rifiuto nomina `graphical-session.target`) |
| S1.23 | §10: refuso `xwayland` di gnome-session 48 | DECISO per irrilevanza (solo Debian; D-A: Debian non si tocca) |
| S1.24 | Prove 2 (con `gnome-session` vanilla) | DECISO D-D (vedi S1.4) |
| S1.25 | Prova 3 (rientro subito dopo il logout) | **SCOPERTO** → **SCOPERTA 2** |
| S1.26 | Prova 4 (remoto aperto → riavvio servizio → locale; locale con remoto aperto) | RIMANDATO |
| S1.27 | Prova 5 (confronto ambiente con login locale GDM) | RIMANDATO (valori attesi confermati in G1, confronto vero no) |
| S1.28 | Prova 6 (fine sessione: variabili dello user manager, con linger) | **SCOPERTO** → **SCOPERTA 9** |
| S1.29 | Prova 7 (regressione Debian) | DECISO D-A (Debian non toccato) |

## Studio 2 — Chiusura GNOME 50 e GDM (fonte: §8 problemi 1-11, §9, §10)

| # | Voce | Stato |
|---|---|---|
| S2.1 | Avviso falso fifo (systemd ≥258) | VERIFICATO: G3; `DECISIONS-11.md` §11.55 |
| S2.2 | Gancio PAM su GDM 50 (ordine con il dialogo) | RIMANDATO |
| S2.3 | «Force Stop» di GDM 50.1 | RIMANDATO |
| S2.4 | Guardia di nascita dopo il logout, rientro <1 s | **SCOPERTO**: G4 forza il bersaglio a mano; rientro reale a 0,3/1/3/10 s mai misurato → **SCOPERTA 2** |
| S2.5 | Nessuna prova con GDM e greeter reali | RIMANDATO |
| S2.6 | «Chi resta vivo dopo il Log Out» su GNOME 50 | VERIFICATO senza linger (G3: 0 processi, scope sparito); con linger → **SCOPERTA 9** |
| S2.7 | uutils/sudo-rs: script del pacchetto e prove | FATTO (prove: `check-desktop.py` sudo-rs); script del pacchetto `prerm`/`postinst`/`postrm` mai eseguiti su Ubuntu (`check-package` non è in `all.sh`) → **SCOPERTA 3** |
| S2.8 | Dopo Log Out con linger: variabili dello user manager | **SCOPERTO** → **SCOPERTA 9** |
| S2.9 | `gnome-initial-setup`/autologin e il gancio | RIMANDATO (greeter vero); primo accesso utente nuovo senza assistente: VERIFICATO G2 |
| S2.10 | `gnome-remote-desktop` di sistema: scriverlo nei manuali | RIMANDATO (passo 6) → in **SCOPERTA 13** |
| S2.11 | `GetCurrentState`/`session_alive()` senza auto-start | VERIFICATO: giro1 (lifecycle PASS) |
| S2.§9.1 | Login locale con desktop `closing` orfano | RIMANDATO |
| S2.§9.2 | Tempo reale del gancio (0,7 s su Debian) | RIMANDATO |
| S2.§9.4 | `pam_open_session` con `CreateSessionWithPIDFD` senza avvisi | VERIFICATO: G3 (nessun avviso nel journal) |
| S2.§9.5 | Inibitori di logout che spostano il ramo forzato su GNOME | **SCOPERTO** (si lega a **SCOPERTA 1**: Log Out presto/con app aperte su GNOME) |
| S2.§9.6 | `localsearch-3`/`app-*@autostart` con linger | **SCOPERTO** → **SCOPERTA 9** |
| S2.§9.7 | `raise(SIGTERM)` da GIO su gdm 50 | VERIFICATO: G3 (client avvisato in pochi secondi) |
| S2.P5 | `loginctl terminate-session` e Force Stop dall'esterno | **SCOPERTO** per il primo (fattibile nel box); Force Stop vero → RIMANDATO |
| S2.P6 | Journal di nascita (`LEADER_PIDFDID`) | VERIFICATO: G3 |
| S2.P7 | grep opzioni GNU nelle prove/script | FATTO per le prove; script del pacchetto → **SCOPERTA 3** |

## Studio 3 — Sessione «ubuntu» (fonte: §7 problemi 1-10, §8, §9)

| # | Voce | Stato |
|---|---|---|
| S3.1 | `gnome_session()` per `ID` os-release | FATTO `session.c:923` (D8 log in G1) |
| S3.2 | `local_session()` per GNOME | VERIFICATO: G1 (`D-153 … data folder /usr/share/ubuntu, common /usr/share/gnome`) |
| S3.3 | `unit_shell()` e drop-in per 50 | VERIFICATO: G2 |
| S3.4 | `desktop_of_session_name()` con `ubuntu` | VERIFICATO: G1 (D8) |
| S3.5 | `XDG_CURRENT_DESKTOP=ubuntu:GNOME` | VERIFICATO: G1 (shell, app ptyxis, manager, gsd-media-keys) |
| S3.6 | Emulazione `profile.d`/`~/.profile`, `~/.gnomerc`, `im-config` | DECISO D-F; `XDG_CONFIG_DIRS` non impostata su GNOME (differenza senza effetto, G1) → in **SCOPERTA 13** (manuale) |
| S3.7 | Con GNOME puro installato (sessione salvata dell'utente) | DECISO D-D |
| S3.8 | Riverifica di dconf 0.49, commenti `[R]` 0.40/48 | VERIFICATO: G1 `D-015 … 20 in force, 0 NOT` |
| S3.9 | `AssertEnvironment` (commento) | **SCOPERTO** (solo commento) → **SCOPERTA 21** |
| S3.10 | Prima configurazione «Welcome to Ubuntu» | VERIFICATO: G2 |
| S3.§8.a | Valore esatto di `XDG_DATA_DIRS`/`PATH` in un login GDM locale | RIMANDATO (confronto con accesso locale) |
| S3.§8.b | Rilancio in login shell in ogni accesso GDM | RIMANDATO |
| S3.§8.c | `~/.profile` di Ubuntu aggiunge `~/.local/bin` al PATH | DECISO D-F (non letto, come Debian) |
| S3.§8.d | Chiave `Session=` di AccountsService | DECISO D-D (nessun lavoro per seguire la scelta alla schermata di accesso) |
| S3.§8.e | `user-session-migration` nella sessione remota | **SCOPERTO**, ma costo minimo: nessun difetto visto in tutto il giro1 (basso) |
| S3.P3 | Prova D8 con/senza `gnome-session` | DECISO D-D |
| S3.P4 | `gsettings` letti da un'app della sessione restano Yaru | **SCOPERTO**: G1 «non verificato» (la prova senza ambiente non vale); l'aspetto Yaru si vede solo nella foto → **SCOPERTA 18** |
| S3.P5 | `dconf dump` dopo la sessione senza chiavi nostre | VERIFICATO in parte (G5 pulizia drop-in; il dump non è citato) |
| S3.P7 | `lightdm.conf.d/50-ubuntu.conf` su Xubuntu/Kubuntu | VERIFICATO: X1 (dichiarazione `xubuntu` vince) |

## Studio 4 — Mutter 50, cattura/input/appunti/audio (fonte: §11 problemi 1-12, §12, §13)

| # | Voce | Stato |
|---|---|---|
| S4.1 | Rinegoziazione extra dopo cambio monitor (resize) | VERIFICATO: righe reattach/canvas-limits PASS su GNOME |
| S4.2 | Margine buffer 8 invece di 16 | VERIFICATO: righe `media` PASS su GNOME |
| S4.3 | Pong delle ricevute di tasto (libeis 1.5) | VERIFICATO: righe `input` tastiera PASS |
| S4.4 | Intel e Radeon su Ubuntu 26.04 + GNOME 50 mai provati con la suite funzionale | **SCOPERTO**: i rapporti del giro non dicono su quale scheda (Intel/Radeon) è girato → **SCOPERTA 17** |
| S4.5 | F-003 Chrome «chiude», solo NVIDIA | RIMANDATO (serve scheda NVIDIA) |
| S4.6 | Chiave `ubuntu-lock-on-suspend` | FATTO `session.c:1651` |
| S4.7 | Commenti falsi su 50 (`input.c:2059-2084`, `gsd-keyboard`, `SetKeymap`) | **SCOPERTO** (solo commenti) → **SCOPERTA 21** |
| S4.8 | Colore: Mutter 50 con gamma 2.2 | **SCOPERTO**: nessun confronto di immagini Debian/Ubuntu → **SCOPERTA 25** |
| S4.9 | Xwayland assente (`--no-x11`) | DECISO per uniformità con Debian (nessuna scelta nuova); da dire nel manuale → **SCOPERTA 13** |
| S4.10 | `INVENTARIO-non-debian.md:42` (libei 1.4 su Debian 13) | **SCOPERTO** (solo testo; Debian non toccato per D-A) |
| S4.11 | Confini con avvio/chiusura (`graphical-session.target`, `RegisterDisplay`) | VERIFICATO (G4) / `RegisterDisplay` → RIMANDATO (GDM) |
| S4.12 | Cura «C» (tasto rimasto premuto dopo rimodellamento dei device) su Mutter 50 | **SCOPERTO**: bench `06-b33` non presente nell'albero Ubuntu → **SCOPERTA 14** |
| S4.§12.a | Cambio monitor: callback/buffer in più, frame nero | VERIFICATO (righe del giro) |
| S4.§12.b | Colori e ombre | vedi S4.8 |
| S4.§12.c | `wireplumber` sink predefinito `remotix` | VERIFICATO: righe `audio` (2) PASS |
| S4.§12.d | `gnome-remote-desktop` con RDP acceso nel dconf | RIMANDATO (locale esclude remoto) |
| S4.§12.e | Modificatori DMA-BUF su Intel/Radeon | **SCOPERTO** → **SCOPERTA 17** |
| S4.P7 | Prova scala (`scaling-factor=2` deve rifiutare come Debian) | **SCOPERTO** → **SCOPERTA 26** |
| S4.P8 | Microprova Xwayland | DECISO (vedi S4.9) |
| S4.P9 | Compilazione con pipewire 1.6.2 / libei 1.5.0 senza avvisi nuovi | VERIFICATO: costruzione, «6 avvisi noti» (4 base + 2 sorgenti altrui) |
| S4.P10 | `ss -ltnp` con `gnome-remote-desktop` installato e non abilitato | **SCOPERTO**, costo minimo (un comando) → **SCOPERTA 23** |

## Studio 5 — Sistema (fonte: «Fatti che contraddicono», «Problemi da affrontare» 1-13, «Non si può sapere», «Prove consigliate»)

| # | Voce | Stato |
|---|---|---|
| S5.F1 | 3e già nel codice: serve solo la prova | VERIFICATO (P6) |
| S5.F2 | Sessione logind con pidfd, «active» | VERIFICATO: G3, L3 |
| S5.F3/4 | AppArmor più severo in enforce (percorsi) | FATTO nel profilo; in severo → RIMANDATO |
| S5.F5 | `remotix.pam` = `sshd` di Ubuntu | VERIFICATO nello studio; confronto sulle quattro immagini live → RIMANDATO |
| S5.F6 | Test `sudo` per sudo-rs | FATTO (`check-desktop.py`) |
| S5.1 | AppArmor: righe xkb | FATTO `remotix_network.apparmor:41-46` |
| S5.2 | AppArmor: regole `dbus`, `/run/systemd/userdb/`; giro complain→enforce | RIMANDATO (kernel Ubuntu vero) |
| S5.3 | Avviso fifo | VERIFICATO (G3) |
| S5.4 | Sessione con pidfd: chiusura, riattacco, stop servizio, «closing» | VERIFICATO: righe lifecycle e resilience PASS, G3, L3 |
| S5.5 | needrestart non riavvii `remotix.service` | FATTO (L6); effetto → RIMANDATO |
| S5.6 | PATH con `/snap/bin` | VERIFICATO: G1, X1, L1, K1 |
| S5.7 | Firefox/Thunderbird snap in sessione | IN VERIFICA ORA |
| S5.8 | Test sudo-rs e C8 con `firefox-esr` | FATTO (`check-desktop.py`); il C8 per Firefox snap non è citato |
| S5.9 | `pam_motd` e script di `/etc/update-motd.d`: latenza alla nascita | **SCOPERTO**: nessuna misura → **SCOPERTA 15** |
| S5.10 | `systemd-oomd` può uccidere `user@UID.service` | **SCOPERTO**: nessun codice, nessuna decisione, nessuna nota → **SCOPERTA 16** |
| S5.11 | Mancano `pam_gnome_keyring`/`pam_kwallet` | DECISO D-P (GNOME); KWallet: osservato (K5), decisione non scritta → **SCOPERTA 8** |
| S5.12 | `include if exists <local/remotix_network>` | FATTO `remotix_network.apparmor:111` |
| S5.13 | Commento «nessuna capability» vs `nis` | FATTO `remotix_network.apparmor:19-21,29` |
| S5.§N.1 | Kernel Ubuntu: `apparmor_restrict_unprivileged_userns`, mediazione dbus | RIMANDATO |
| S5.§N.2 | Altri rifiuti in enforce | RIMANDATO |
| S5.§N.3 | Sessioni con pidfd: stop del servizio, riavvio con desktop vivi | VERIFICATO (resilience `service-restart`) |
| S5.§N.4 | Snap su ognuno dei quattro gusti | IN VERIFICA ORA (poi per gli altri tre gusti → RIMANDATO se unione2 non li tocca) |
| S5.§N.5 | PATH reale visto dalle app | VERIFICATO: G1 (app ptyxis), K1 |
| S5.§N.6 | Latenza di `pam_sss` con `sssd` assente | **SCOPERTO** (stesso blocco di **SCOPERTA 15**) |
| S5.§N.7 | Tempo e byte per nome inesistente su Ubuntu GNOME con `sss` | VERIFICATO: riga di `check-ban` (con `sss` in nsswitch del box non dichiarato: basso) |
| S5.§N.8 | needrestart su Ubuntu Server | RIMANDATO |
| S5.§N.9 | Finestre polkit non richieste su Ubuntu 26.04 | VERIFICATO: `desktop/no-password-windows` PASS su tutti e quattro |
| S5.§N.10 | `systemd-oomd` con più utenti | **SCOPERTO** (vedi S5.10) |
| S5.P5 | needrestart con e senza il file di configurazione | RIMANDATO |
| S5.P6 | Confronto PAM riga per riga con `/etc/pam.d/sshd` su ogni immagine | RIMANDATO |
| S5.P7 | Censimento polkit con utente remoto su ciascuna immagine | VERIFICATO (come S5.§N.9) |
| S5.P9 | `apt install ./remotix_*.deb` su Desktop pulita e su Server; postinst/prerm/postrm; senza `apparmor` | install: VERIFICATO (4 box); prerm/postrm/purge/Server/senza apparmor: **SCOPERTO** (il primo fattibile) → **SCOPERTA 3** |
| S5.§9 | `update-notifier`, `apport`, `ubuntu-report` rumore in sessione | **SCOPERTO**: visto una notifica «lubuntu-update» (L2), mai guardato altro → **SCOPERTA 27** |
| S5.§8 | Le postinst delle librerie di sistema riavviano servizi da sole | **SCOPERTO** (costo basso, solo lettura, dopo needrestart) — contato in **SCOPERTA 27** |

## Studio 6 — Kubuntu, KWin, labwc proprio (fonte: «Problemi da affrontare» 1-13, §6, §7, §8, «Non si può sapere», «Prove consigliate»)

| # | Voce | Stato |
|---|---|---|
| S6.1 | Rimettere il labwc proprio | VERIFICATO: K1 (`/usr/libexec/remotix/labwc`, hash uguale al .deb); D-K |
| S6.2 | Costruzione condizionale (solo Ubuntu ≥ 26.04) | DECISO D-A (albero solo Ubuntu: nessuna condizione) |
| S6.3 | Build di labwc+wlroots nel `.deb` | VERIFICATO: costruzione, `ldd` senza libwlroots, riproducibile (R4, R23) |
| S6.4 | Documenti di licenza riscritti | FATTO in parte (`LICENSE.md`, `debian/copyright:47`); resti 1.5 → **SCOPERTA 20** |
| S6.5 | Manutenzione di sicurezza della copia statica | FATTO come regola (`docs/DECISIONS.md` §10.43); segnalare la patch a wlroots: DECISO D-E |
| S6.6 | Prova che con il labwc di Ubuntu il difetto c'è e con il proprio no | VERIFICATO: studio 10 |
| S6.7 | Ripiego senza labwc proprio | VERIFICATO: K4 (dichiarato); riaggancio con altra dimensione nel ripiego non provato (limite dichiarato) |
| S6.8 | Logout KDE su Ubuntu (R-DE-051) | VERIFICATO in parte (K2b 0 processi) + FATTO + IN VERIFICA ORA; vuoti → **SCOPERTA 1** |
| S6.9 | kwallet/gnome-keyring | vedi S5.11 |
| S6.10 | Rilevazione con più desktop, `declared_sessions()` sddm | DECISO D-D |
| S6.11 | Greeter sddm non confuso con un desktop reale | RIMANDATO |
| S6.12 | `CAP_SYS_NICE` nei contenitori | FATTO `boxes/box.sh:65` |
| S6.13 | R-SEC-035 falso allarme (attesa 300 ms) | VERIFICATO: `desktop/power-entries-absent` PASS (giro1) |
| S6.§6.1-3 | Appunti `ext_data_control`, layout F-009, frame vuoti | VERIFICATO: righe `clipboard`, `input`, K6 PASS su KDE |
| S6.§N.1-2 | Difetto con labwc di Ubuntu; copertura radice 1x1 | VERIFICATO: studio 10 (a)(b)(c) |
| S6.§N.3 | SRU di labwc/wlroots Ubuntu | **SCOPERTO**, ma non è un lavoro: da riguardare prima del rilascio (nota in **SCOPERTA 20**) |
| S6.§N.4 | Pixman nella build statica (`node=pixman`) | VERIFICATO: K1/K6 (KWin nasce, finestre si aggiornano) |
| S6.§N.5 | `pam_kwallet5` con il servizio `remotix` | VERIFICATO in parte (K5) → **SCOPERTA 8** |
| S6.§N.7 | Ritardo di un fotogramma del `presented` a 4K con GPU reali | RIMANDATO (macchina vera) |
| S6.P2 | Sessione KDE completa: F-003/F-016/F-018 | VERIFICATO: giro1 KDE 111/124, K6 |
| S6.P4 | Logout: 30 s senza processi, `/run/user` pulito | VERIFICATO: K2b |
| S6.P6 | sddm presente, remoto con greeter acceso | RIMANDATO |
| S6.§8 | `plasma-login-manager` non in Ubuntu 26.04 | DECISO (nessuna azione ora; da guardare con 26.10) |

## Studio 7 — Xubuntu e Lubuntu (fonte: §6, §10 decisioni, §11 non si sa, §12 prove, §13 problemi 1-14)

| # | Voce | Stato |
|---|---|---|
| S7.1 | Riconoscimento Xubuntu/Lubuntu | VERIFICATO: X1, L1; `session.c:389-391` |
| S7.2 | D-153 `xdg-xubuntu`/`xdg-Lubuntu` | VERIFICATO: X1, L1 |
| S7.3 | `XDG_SESSION_DESKTOP` su Lubuntu (`LXQt` come sddm) | VERIFICATO: L1 (`LXQt`) |
| S7.4 | Variabili di `56xubuntu-session` | DECISO D-P; IN VERIFICA ORA (elenco dei fatti); differenza da dichiarare nel manuale |
| S7.5 | Whisker perso (D-X3) | VERIFICATO: X2, X4, X5; casi H1b, «not repaired now» → **SCOPERTA 4**; chiusura leggera → **SCOPERTA 5** |
| S7.6 | `survivor()` salta i processi non-dumpable (`ssh-agent`, `gpg-agent`) | **SCOPERTO**: `session.c:4689` invariato (`st_uid` del file `comm`); X8 «non so se sono mai nati» → **SCOPERTA 6** |
| S7.7 | `labwc`/`wlr-randr`/`xwayland` Recommends | **SCOPERTO**: nessuna decisione scritta, nessun avviso in `postinst` (come Debian); con `--no-install-recommends` XFCE/LXQt non nascono → **SCOPERTA 22** |
| S7.8 | Riferimenti di versione nei commenti (lxqt 2.1.1, labwc 0.8.3) | FATTO per la sostanza (giro1 con labwc 0.9.3 e lxqt 2.3.0 verde); commenti vecchi in `session.h:216,230,245`, `shape.c:133` → **SCOPERTA 21** |
| S7.9 | Log Out XFCE rifiutato mentre parte | **SCOPERTO**: curato su Debian, mai misurato su Xubuntu (avvio più lungo, `LaunchGNOME`); le prove di Log Out aspettano che il desktop sia a riposo → **SCOPERTA 1** |
| S7.10 | Box Xubuntu con DM giusto | FATTO e VERIFICATO (X1) |
| S7.11 | qlipper di Lubuntu | VERIFICATO: L4 (acceso, appunti PASS nei due versi) |
| S7.12 | `picom` di Lubuntu (era «innocuo, rumore nel log») | FATTO (`lxqt-avvio.diff`) + IN VERIFICA ORA |
| S7.13 | Sfondo nero XFCE (E1) | VERIFICATO: X7 foto, nessun nero |
| S7.14 | Chiusura leggera residua accanto al gancio PAM | **SCOPERTO** → **SCOPERTA 5** |
| S7.§10.3 | `XDG_SESSION_DESKTOP` LXQt o Lubuntu | FATTO (come DM, vedi S7.3) |
| S7.§11.1 | Quale DM resta attivo con `xubuntu-desktop` su Ubuntu con gdm3 | VERIFICATO nei box (X1); sulla macchina vera → RIMANDATO |
| S7.§11.5 | Tempo di `xfce4-session` per arrivare a riposo | **SCOPERTO** → **SCOPERTA 1** |
| S7.§11.6 | qlipper col browser vero | VERIFICATO (L4) |
| S7.§11.7 | `picom` non lasci processi nello scope | IN VERIFICA ORA (picom) ; L5 nessun residuo |
| S7.§11.8 | `labwc 0.9.3` + `wlr-randr 0.4.1` con il codice 1.0.0 | VERIFICATO: giro1 xfce/lxqt 117/124 |
| S7.§11.9 | sddm/lightdm reali non reagiscono a una sessione remota | RIMANDATO |
| S7.§11.10 | Lubuntu parte con la sessione X11 `Lubuntu` su macchina vera | RIMANDATO |
| S7.P1 | Riconoscimento con `--no-install-recommends` | **SCOPERTO** → **SCOPERTA 3** |
| S7.P2 | Ambiente a confronto con un accesso locale vero | RIMANDATO |
| S7.P3-4 | Pannello Xubuntu; scope e rientro entro 4-6 s | VERIFICATO: X2-X5, X8; L3 (5 rientri su 5) |
| S7.P5 | Log Out presto (XFCE) a 1-2 s | **SCOPERTO** → **SCOPERTA 1** |
| S7.P7 | Inattività > 15 min su Xubuntu e Lubuntu (schermo acceso, nessun blocco) | **SCOPERTO**: provati solo 11 min nel vecchio banco → **SCOPERTA 7** |
| S7.P8 | Accesso locale con lightdm/SDDM mentre il remoto è aperto | RIMANDATO |

## Studio 8 — Pacchetto e macchine di prova (fonte: «Problemi da affrontare» 1-16, «Non si può sapere», «Prove consigliate»)

| # | Voce | Stato |
|---|---|---|
| S8.1 | Contenitore di costruzione Ubuntu | FATTO (`costruzione.diff`, `build/Containerfile`) |
| S8.2 | Dipendenze in universe | FATTO e dichiarato (`debian/control`) |
| S8.3 | `mesa-va-drivers` non esiste | FATTO (`control`) |
| S8.4 | Ubuntu GNOME senza `va-driver-all` | FATTO: `postinst:37-42` avvisa; resta con `--no-install-recommends` (come Debian) |
| S8.5 | ngtcp2/nghttp3 statici con gcc 15 | VERIFICATO: costruzione riuscita |
| S8.6 | Labwc proprio per Kubuntu | VERIFICATO (S6.1) |
| S8.7 | Box Ubuntu (DM, pin, utente `ubuntu`) | FATTO (`macchine.diff`) e VERIFICATO (X1, L1) |
| S8.8 | Nomi e porte distinti | FATTO (`box.sh`, `lib.py`, `base-check.py`: 2221-2224, 8821-8824) |
| S8.9 | lintian 2.129 | VERIFICATO: lintian 0/0 |
| S8.10 | Riproducibilità | VERIFICATO: costruita due volte (R23) |
| S8.11 | Ordine della riga `pam_exec` in `common-session` | VERIFICATO: `prelocal` 6 PASS sui quattro gusti |
| S8.12 | Prove: percorsi, ptyxis, snap-SKIP, regex, `gnome-tour` | FATTO (`prove.diff`) |
| S8.13 | VM: `server/vm.sh` per Ubuntu, `virtio-vga` per il nodo render | FATTO (`vm.sh`) ma mai avviata → **SCOPERTA 24** |
| S8.14 | ISO live: scarico e procedura | RIMANDATO (lavoro del proprietario) |
| S8.15 | `prepara-server.sh` per Ubuntu | FATTO (`prepara-server.diff`, approvato) ma «non eseguito» → **SCOPERTA 11** |
| S8.16 | Immagini fedeli alle ISO (metapacchetto completo o minimal) | RIMANDATO (live) |
| S8.§N.1 | ngtcp2/nghttp3 compilano | VERIFICATO |
| S8.§N.3 | Ordine in `common-session` per gusto | VERIFICATO (S8.11) |
| S8.§N.4-5 | Box con systemd che tira `snapd`; unità fallite | VERIFICATO: PIANO (3 unità attese: netplan, tpm) |
| S8.§N.6 | `universe` e spazio overlay sulle live | RIMANDATO |
| S8.§N.7 | VM con `virtio-vga` offre `renderD128` | **SCOPERTO** → **SCOPERTA 24** |
| S8.§N.8 | Enforce AppArmor | RIMANDATO |
| S8.P3 | `apt install` con e senza `--no-install-recommends`; `check-package` | **SCOPERTO** → **SCOPERTA 3** |
| S8.P4 | `systemctl --failed` e `apt install firefox` con/senza pin | VERIFICATO in parte (PIANO: 3 unità attese); installazione di Firefox → IN VERIFICA ORA (snap) |

## Studio 9 — Pannello XFCE, plugin perso (fonte: §9 problemi 1-7, §10, §8 prove)

| # | Voce | Stato |
|---|---|---|
| S9.1 | Tipo del plugin «di sistema» mai scritto nel file utente | VERIFICATO: X2 (`plugin-1 type="string" value="whiskermenu"`), `xfce-pannello.diff` |
| S9.2 | Ripristino con il blocco ancora in memoria | FATTO (`xfce-pannello.diff`); la riga «not repaired now» non osservata → **SCOPERTA 4** |
| S9.3 | `xfconf_unset` dell'ultimo figlio cancella il padre | VERIFICATO: X4 (nodo resta) |
| S9.4 | Controllo «ogni id ha il tipo» + riparazione | VERIFICATO: X5 (`had no type: put back as «whiskermenu»`), `session.c:5895-5962` |
| S9.5 | Protezione voci di spegnimento solo dal whisker | VERIFICATO: X2 (sei chiavi bloccate) |
| S9.6 | Finestra «Plugin could not be loaded» | VERIFICATO: X2, X3 (0 finestre) |
| S9.7 | D-153 e whisker di Xubuntu | VERIFICATO (X1, X2) |
| S9.§10.1 | Ordine reale dei due ripristini | VERIFICATO: X3 (journal della nascita) |
| S9.§10.2 | xfconfd memorizza il padre `type="empty"` con figli bloccati | VERIFICATO: X2 (file di blocco) |
| S9.§10.3 | Figlio non bloccato sotto `plugin-1` (`favorites`) | **SCOPERTO** → **SCOPERTA 4** |
| S9.§10.4 | Ripristino con blocco in memoria fuori dalla chiusura leggera | **SCOPERTO** → **SCOPERTA 4** |
| S9.§10.5 | Finestra «could not be loaded» senza nessuno che la veda | VERIFICATO per evitare il caso (X5) |
| S9.P1 | xfconf puro senza REMOTIX | **SCOPERTO**, ora superflua (causa curata e confermata da X2-X5) |
| S9.P3 | Chiusura leggera passo per passo (H1a/H1b) | VERIFICATO per H1a (X3); H1b non prodotta → **SCOPERTA 4** |

## Rapporti del giro `unione1` (fonte: righe non PASS, difetti, «non visto/non verificato»)

| # | Voce | Stato |
|---|---|---|
| G.1 | `pkexec` su GNOME (`SHELL=` vuota) | DECISO (registro E2; scelta 1.5.3) |
| G.2 | `mouse-drag` Chrome/Firefox, `phone/tap-and-half-drag-select` | FATTO (`prove2.diff`) + IN VERIFICA ORA |
| G.3 | Pulsanti Ctrl+Alt (6 righe) | DECISO (B3) + FATTO `prove2.diff` |
| G.4 | GNOME: gsettings dall'interno di un'app | **SCOPERTO** → **SCOPERTA 18** |
| G.5 | GNOME: ptyxis assente dall'istantanea («non indagato») | **SCOPERTO** → **SCOPERTA 18** |
| G.6 | GNOME: assistente di primo avvio con secondo accesso | **SCOPERTO**, basso (S1.21 coperto per un accesso) |
| G.7 | GNOME G5 (`user.control`) con linger; G4 senza linger | **SCOPERTO** → **SCOPERTA 9** |
| G.8 | GNOME: causa della selezione parziale `help ` (telefono) | IN VERIFICA ORA (stessa riga) |
| G.9 | GNOME: confronto con ambiente GDM locale vero | RIMANDATO |
| G.10 | GNOME: schermo vuoto 27 s dopo il rifiuto (client senza messaggio) | **SCOPERTO** → **SCOPERTA 2** |
| G.11 | GNOME: `XDG_CONFIG_DIRS` non impostata (la imposterebbe `profile.d`) | DECISO D-F (differenza dichiarata) → **SCOPERTA 13** |
| G.12 | GNOME: `snap list` nel box (socket attivo, nessuno snap installato) | IN VERIFICA ORA (snap) |
| K.1 | KDE: Log Out presto perso (K2a), 42 processi, client non avvisato | FATTO + IN VERIFICA ORA |
| K.2 | KDE: `lifecycle/logout` con ksmserver `NoReply` (35 s) | IN VERIFICA ORA; ⚠ vedi nota **SCOPERTA 1** |
| K.3 | KDE: `media/codec` Firefox 130 px | IN VERIFICA ORA |
| K.4 | KDE: `reattach-windows-inside` | FATTO (`prove2.diff`) |
| K.5 | KDE: K4 riaggancio con altra dimensione nel ripiego `--virtual` | RIMANDATO/dichiarato (limite scritto nel registro e in K4); basso |
| K.6 | KDE: K6 con Firefox e misura dei `wl_callback.done` | **SCOPERTO**, ora coperto in parte da `media/screen-updates` PASS e dallo studio 10 (basso) |
| K.7 | KDE: `settings-intact`, journal non letto | IN VERIFICA ORA |
| K.8 | KDE: utenti `gk1…gk10` nel box | n/a (ripulito, nessun processo) |
| X.1 | XFCE: variante H1b e riga «not repaired now» non prodotte | **SCOPERTO** → **SCOPERTA 4** |
| X.2 | XFCE: accesso locale vero con lightdm | RIMANDATO |
| X.3 | XFCE: processi durante la sessione (`ssh-agent`, `gpg-agent`, `xiccd`, `localsearch-3`) | **SCOPERTO** → **SCOPERTA 6** |
| X.4 | XFCE: `user@UID.service` `failed (timeout)` da `mpris-proxy` dopo ogni Log Out | **SCOPERTO**: classificato «ambiente» ma non spiegato → **SCOPERTA 19** |
| X.5 | XFCE: chiusura leggera lascia lo xfconfd locale con le chiavi bloccate | **SCOPERTO** → **SCOPERTA 5** |
| L.1 | LXQt: finestra «X Compositor crashed too many times» (picom) | FATTO (`lxqt-avvio.diff`) + IN VERIFICA ORA |
| L.2 | LXQt: il «Crash Report» compare anche senza utente nuovo | IN VERIFICA ORA |
| L.3 | LXQt: `needrestart` non installato nel box | RIMANDATO |
| L.4 | LXQt: accesso locale SDDM vero | RIMANDATO |
| L.5 | LXQt: `Hidden=true` per picom non provato | IN VERIFICA ORA |
| L.6 | LXQt: esito vuoto nella pagina nei rientri | n/a (limite della prova; il giornale e gli id logind provano) |
| 10.1 | Studio 10: una sola macchina/versione di Firefox; `weston-simple-egl`, GTK4, fullscreen Firefox | **SCOPERTO**, basso (la conclusione regge su 759/760 contro 0/755) |

---

## Conteggio
280 righe nelle tabelle (conteggio sulla prima parola della colonna «Stato»): VERIFICATO 99 · FATTO 46 · RIMANDATO 40 · DECISO 22 ·
IN VERIFICA ORA 13 · SCOPERTO 55 · 5 righe senza stato proprio (rimandi o «n/a»).
Le 55 righe SCOPERTE si raccolgono in 27 voci distinte qui sotto (molte righe cadono sulla stessa voce); 4 voci sono a rischio alto, 7 medio, 16 basso.

---

## Voci SCOPERTE, ordinate per rischio per l'utente

Rischio alto = guasto visibile o perdita di dati; medio = guasto visibile ma raro o con strada di uscita; basso = rumore, documentazione, qualità delle prove.
Costo: «V» = una verifica mirata in un box; «M» = una modifica (poi revisore e riprova); «D» = decisione del proprietario; «S» = solo scrittura di documenti.

### Rischio alto

**1. Log Out nei primi secondi, su GNOME, XFCE, LXQt (e le varianti KDE ancora scoperte).**
- Che cosa può andare storto: l'utente preme «Esci» appena il desktop è nato; il desktop resta vivo e il browser non viene avvisato (come è successo su KDE: 42 processi rimasti).
  Su XFCE il rifiuto «deve essere a riposo» è documentato (studio 7 §6.6) e su Xubuntu l'avvio è più lungo (`LaunchGNOME`); su GNOME gli inibitori di Ubuntu (dock) possono spostare il Log Out sul ramo forzato (studio 2 §9.5).
- Dove: `prove/check-lifecycle.py` (`wait_idle` prima del gesto: il Log Out si prova sempre a desktop già a riposo, per questo non è mai uscito); codice `session.c` (`exit_xfce`/`kill_xfce`), `child.c:10393`. Nessuna riga stabile in `prove/` per l'uscita presto, con lavoro non salvato o con «Annulla» (il registro D chiede proprio queste tre).
- Voci in più su KDE non coperte da `unione2` a quanto dice il mandato: la finestra «Esci» annullata («Annulla»); la variante in cui ksmserver non risponde (`NoReply`, 35 s, vista una volta, causa ignota): la cura nuova per scelta NON forza nulla in quel caso, quindi il desktop resterebbe su.
- Costo: V per ogni macchina (stesso gesto a 1, 3, 8, 16 s dalla nascita; su KDE anche Annulla e NoReply); M solo se fallisce; poi una riga permanente in `prove/`.
- Macchine: gnome, xfce, lxqt (kde per Annulla e NoReply).

**2. Rientro subito dopo un Log Out su GNOME: schermo vuoto fino a 27 s, senza messaggio.**
- Che cosa può andare storto: dopo «Esci» l'utente riapre la pagina e rientra entro pochi secondi; `graphical-session.target` è ancora attivo, la nascita viene rifiutata e ritentata ogni 12 s, il browser vede lo schermo nero senza alcun testo (G4: +27 s; la prova forzava il bersaglio a mano).
  Nessuno ha misurato un rientro vero a 0,3 / 1 / 3 / 10 s (studio 2 prova 3, studio 1 prova 3); il Log Out su GNOME impiega 11,4 s a sparire da logind (G3).
- Dove: `session.c:3802-3820` (`inactive_unit`), `child.c` (ritentativo `BIRTH_REIN_MS` 12 s); manca la riga nella prova.
- Costo: V (rientri a distanza crescente, con e senza linger), poi eventualmente M (messaggio al client o ritentativo più corto).
- Macchina: gnome.

**3. Il controllo del pacchetto (`check-package.py`) non è mai stato eseguito su Ubuntu.**
- Che cosa può andare storto: `apt remove` con un utente collegato (desktop da chiudere, gruppi da togliere, nessun residuo), `purge`, reinstallazione, rifiuto dell'utente «remotix», `--no-install-recommends` (XFCE/LXQt senza `labwc`, KDE senza), `prerm`/`postrm` con uutils (Rust) e systemd 259, AppArmor assente. `all.sh` non lo include (lo dice il suo commento); nei rapporti non compare. Un guasto qui lascia desktop o utenti rimasti sulla macchina del cliente alla disinstallazione.
- Dove: `prove/check-package.py`, `debian/remotix.prerm|postinst|postrm|preinst`.
- Costo: V (script già esistente; azzera il box, quindi dopo `unione2` e un box per volta).
- Macchine: gnome e kde almeno (poi xfce, lxqt).

**4. XFCE: il menu del pannello può ancora sparire in due strade non provate.**
- Che cosa può andare storto: (a) lo xfconfd viene riavviato a mano mentre c'è la sessione locale (caso H1b); (b) il nodo `plugin-N` senza tipo con il blocco ancora in memoria (riga «not repaired now» mai vista); (c) un figlio non bloccato sotto `plugin-1` (es. `favorites`) che ferma la cascata e lascia il padre vuoto. Su Xubuntu il menu è l'unica protezione delle voci di spegnimento.
- Dove: `session.c:5895-5962` e il ripristino; rapporto X3/X5/X6 «non prodotto».
- Costo: V (script nel box: sessione con posto simulata come in X3, poi `systemctl --user restart xfconfd`, nuova sessione; nodo senza tipo costruito a mano).
- Macchina: xfce.

### Rischio medio

**5. XFCE: dopo la chiusura leggera l'accesso locale resta con le voci di spegnimento nascoste.**
- Che cosa può andare storto: X3 mostra che dopo `light close` lo xfconfd locale ha ancora il blocco e `show-command-shutdown=false`; il codice scrive «NO try-restart of xfconfd» e «XFCE keys NOT restored». L'utente al suo computer non vede «Spegni/Riavvia» nel menu finché non riavvia xfconfd. Strada stretta dal 18 nov (il gancio PAM chiude per intero), ma esiste se il gancio manca o scade.
- Dove: `session.c:4215-4226`, `child.c:9921` (`local_light_close`).
- Costo: D (accettare e scrivere nel manuale) oppure M (riavviare xfconfd a chiusura leggera, con il rischio descritto nello studio 9).
- Macchina: xfce.

**6. XFCE/GNOME: `ssh-agent` e `gpg-agent` possono restare nello scope dopo il Log Out.**
- Che cosa può andare storto: `survivor()` giudica «dell'utente» un processo dal proprietario del file `comm`; un processo non-dumpable (`ssh-agent`, `gpg-agent`) ha quel file di root e viene saltato; la sessione logind resterebbe «closing» e il rientro riceverebbe «FOUND AGAIN» (studio 7 §6.2). `xfce4-session` 4.20.4 li avvia da sé. Nei campioni di X8 non c'erano dopo, ma nessuno ha elencato i processi DURANTE la sessione.
- Dove: `session.c:4689` (`survivor`), la lista di `session_clear_out_scope`.
- Costo: V (elencare i processi in sessione e dopo un Log Out forzato) + M di 3 righe (leggere `Uid:` da `/proc/<pid>/status`).
- Macchina: xfce (e gnome, per `gcr-ssh-agent`).

**7. Inattività lunga (15-20 minuti) su Xubuntu e Lubuntu: blocco schermo o schermo spento nel remoto.**
- Che cosa può andare storto: Xubuntu mette `blank-on-ac=15` e DPMS 20/60, `xfce4-screensaver` parte (Recommends); il vecchio banco ha provato solo 11 minuti. Se compare un blocco, l'utente remoto si trova davanti una finestra di password per un account senza il suo portachiavi.
  I tasti sono «in vigore» (`settings-intact`), ma l'effetto reale a tempo non è stato osservato su nessun gusto di Ubuntu.
- Dove: `session.c` `XFCE_LOCKS` (~righe 6368-6370 nel vecchio numero), studio 7 §7.
- Costo: V di attesa (20-25 minuti, nessun carico) sui quattro box in parallelo.
- Macchine: xfce, lxqt (gnome e kde per completezza).

**8. KDE: un'app che apre davvero il portafoglio (browser, Discover) può far comparire la finestra «crea portafoglio».**
- Che cosa può andare storto: K5 ha visto solo il desktop vuoto (nessuna finestra, `kwalletd6` mai partito, `ksecretd` sì). La prova 5 dello studio 6 (avviare un'app che chiede il portafoglio) non è stata fatta, né la decisione per KDE è scritta (D-P parla di GNOME e Xubuntu). Se la finestra compare è una richiesta di password non voluta (regola 1.5.3).
- Dove: `src/remotix.pam` (nessuna riga `pam_kwallet5`), `desktop/no-password-windows` (non prova app che usano il portafoglio).
- Costo: V (un'app con KWallet nel box) + D (come per GNOME: allinearsi a Debian).
- Macchina: kde.

**9. Con linger acceso, dopo il Log Out restano variabili, drop-in e processi dello user manager.**
- Che cosa può andare storto: G5 e G4 non hanno guardato la cartella `user.control` né l'ambiente con linger; `GNOME_DESKTOP_SESSION_ID` e `QT_IM_MODULES` che il leader 50 immette non sono in `OUR_VARIABLES` (`session.c:4041`); `localsearch-3`, `gcr-ssh-agent`, `app-*@autostart` con linger mai censiti. Effetto probabile: una sessione locale XFCE/KDE successiva dello stesso utente eredita variabili GNOME.
- Dove: `session.c:4041-4060`, `4201-4240`; prove 6/8 dello studio 2.
- Costo: V (Log Out con `loginctl enable-linger`, poi `systemctl --user show-environment`, `ls user.control`, `ps`); M se serve aggiungere due nomi.
- Macchina: gnome (poi xfce).

**10. Gli strumenti di prova possono ancora mentire (installazione e avvisi).**
- Che cosa può andare storto: il confronto «il programma nel box è quello del `.deb`» dopo l'installazione è ancora «da aggiungere» (PIANO) e `build-deb.sh` non conta gli avvisi del compilatore (lezione 2: «0 avvisi» letto nel registro). Prove vere su un binario sbagliato, o una protezione spenta senza che nessuno se ne accorga.
- Dove: `boxes/box.sh` (`install`), `build/build-deb.sh`.
- Costo: M piccola (hash dopo l'install; conteggio avvisi confrontato con i 6 noti).
- Macchina: tutte (server).

**11. `prepara-server.sh` per Ubuntu non è mai stato eseguito.**
- Che cosa può andare storto: il server è a RAM, ogni riavvio lo azzera (memoria del progetto); lo script adattato è «approvato, non eseguito»: al prossimo riavvio potrebbe fallire e fermare tutte le prove.
- Dove: `server/prepara-server.sh`, `prepara-server.diff`.
- Costo: V (esecuzione di prova, o solo il controllo finale, dopo `unione2`).
- Macchina: server (tutte).

### Rischio basso (ma da non perdere)

**12. Registro dei problemi e `DECISIONS-11.md` non aggiornati con il lavoro Ubuntu.** Mancano le voci su: avvio GNOME 50 e unità template, pidfd/systemd 259, labwc proprio per Kubuntu, mappa dei nomi e D-153, pannello XFCE (cause H1/H1b e cure C1-C4), `picom`/qlipper, needrestart, `/snap/bin`, sudo-rs/uutils, Xubuntu con gdm3, e le tre lezioni di metodo del PIANO. Regola del PIANO e del registro B5. Costo S. Macchina: nessuna.

**13. Elenco delle differenze da scrivere nel manuale (passo 6).** Portachiavi GNOME e variabili Xubuntu non riprodotti (D-P); `~/.profile`/`~/.gnomerc` non letti (D-F); `XDG_CONFIG_DIRS` non impostata su GNOME; `pkexec` con `SHELL=` vuota; Xwayland assente; `gnome-remote-desktop` di sistema e «Force Stop» (ora chiude anche il desktop remoto); needrestart lascia le librerie vecchie fino al riavvio del servizio; `systemd-oomd`; limiti dell'uscita KDE (spegni/riavvia chiesti dal desktop non rilasciano il nome; riavvio di KWin durante l'attesa); ripiego KDE senza labwc proprio (niente adattamento al riaggancio). Costo S. Macchina: nessuna.

**14. Cura «C» (tasto rimasto premuto dopo che Mutter rifà i dispositivi) non rimisurata su Mutter 50.** Visibile se succede (tasto che ripete all'infinito) ma il codice non è cambiato. Dove: `mutter.c:804-879`; il banco `06-b33-wakeup` non è nell'albero Ubuntu. Costo: M (portare la prova) poi V. Macchina: gnome.

**15. `pam_motd` e gli script di `/etc/update-motd.d` possono rallentare la nascita della sessione.** Mai misurato (studio 5 §9; `pam_sss` con `sssd` assente). Dove: `src/remotix.pam:116-117`. Costo: V (tempo di `pam_open_session` sul Desktop completo). Macchina: gnome (poi kde).

**16. `systemd-oomd` può uccidere `user@UID.service`, quindi il desktop remoto, sotto pressione di memoria.** Nessun codice, nessuna decisione, nessuna nota (grep nei documenti: nulla). Costo: D (lasciare come l'accesso locale e dichiararlo) + S; non provabile con poco. Macchina: gnome, kde (Desktop con oomd).

**17. I rapporti non dicono su quale scheda video è girato il giro.** Studio 4: Intel e Radeon su Ubuntu + GNOME 50 mai provati con la suite funzionale; DMA-BUF e modificatori da vedere. Costo: V (leggere dai registri quale scheda ha scelto REMOTIX) e, se una sola, un secondo giro su quella mancante (M di tempo, non di codice). Macchine: tutte.

**18. GNOME: valori di `gsettings` letti da una app della sessione e finestra del terminale assente dall'istantanea.** G1 e G2 lo dichiarano «non verificato / non indagato». Costo: V (una app avviata con l'ambiente giusto: tema, posizione del dock; foto con la finestra aperta). Macchina: gnome.

**19. `user@UID.service` finisce `failed (timeout)` dopo il Log Out (`mpris-proxy` non si ferma), su tutti i box.** Classificato «ambiente del contenitore» ma non spiegato; se succede anche su macchina vera, il gestore utente impiega ~40 s a morire e un rientro in quel tempo potrebbe trovarlo «closing». Costo: V (`systemctl --user status mpris-proxy` nel box, `bluez` presente?). Macchine: tutte.

**20. Testi di licenza e data di costruzione.** `LICENSE.md:13` parla di «installer (`remotix-*.run`)», `THIRD-PARTY-LICENSES` elenca Go 1.25 e 17 moduli di `remotix-install` (righe 11, 27-29, 1661-…): il `.deb` finito dice cose non vere. Annotato nel PIANO «prima del rilascio» ma senza passo di controllo; stesso discorso per la data di costruzione e per le SRU di labwc/wlroots (controllare prima di rilasciare). Costo: S/M piccola. Macchina: nessuna.

**21. Commenti falsi o vecchi.** `child.c:1674` (`ConditionEnvironment`), `input.c:2059-2084` («Mutter non offre la leva», `gsd-keyboard`), `rediscover.h:27` (`gnome-session-binary`), `session.h:216,230,245` e `shape.c:133` (labwc 0.8.3, lxqt-session 2.1.1). Il codice è giusto; i commenti ingannano chi rilegge. Costo: M di 10 minuti. Macchina: nessuna.

**22. `labwc`, `wlr-randr`, `xwayland` solo «Recommends» su Xubuntu/Lubuntu.** Nessuna decisione scritta (lo studio la chiedeva), nessun avviso nel `postinst` (c'è solo quello per `va-driver-all`): con `--no-install-recommends` XFCE e LXQt non nascono e l'utente non sa perché. Come Debian, quindi D per analogia. Costo: D + eventuale M (un avviso). Macchine: xfce, lxqt.

**23. Nessuna porta in ascolto con `gnome-remote-desktop` installato e non abilitato (prova P10).** Un comando (`ss -ltnp`, `grdctl status`). Costo: V minimo. Macchina: gnome.

**24. La VM Ubuntu (`server/vm.sh`, `virtio-vga`) non è mai stata avviata.** Il `preinst` rifiuta l'installazione senza nodo render; la modifica a `vm.sh` è approvata ma non provata. Serve per le prove del passo 5. Costo: V (un avvio). Macchina: server.

**25. Colori: Mutter 50 compone con gamma 2.2, lo stream lo dichiara.** Nessun confronto di una stessa scena tra Debian e Ubuntu. Costo: V (due foto) ma serve una macchina Debian. Macchina: gnome.

**26. Scala: `scaling-factor=2` impostato dall'utente deve essere rifiutato come su Debian.** Mai provato su Mutter 50 (studio 4 P7). Costo: V. Macchina: gnome.

**27. Rumore nella sessione remota: notifiche di aggiornamento/apport/`ubuntu-report`.** Una notifica «lubuntu-update: Updates available!» vista in L2; mai guardato il resto; le postinst delle librerie che riavviano servizi da sole non sono state lette. Costo: V (foto + lettura). Macchine: lxqt, gnome.
