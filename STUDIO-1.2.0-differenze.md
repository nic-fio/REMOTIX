# STUDIO 1.2.0 — che cosa portare da Fedora a Ubuntu 26.04 e Debian 13

Studio di sola lettura del 25 nov 2026, per la prossima sessione. Nessun file del prodotto è stato toccato.
Metodo: `diff` di `ubuntu26.04/src` contro `fedora45/src` (14 file diversi + 5 file nuovi), poi `debian13/src` contro `ubuntu26.04/src`,
lettura di `fedora45/PIANO.md`, `fedora45/docs/REGISTRO-problemi.md` (F1-F36), `PIANO-1.0.2-debian-ubuntu.md`, i tre `PIANO.md` e i tre `CLAUDE.md`.
Dove non ho verificato scrivo «non verificato». Le righe citate sono di `fedora45/src` salvo diverso avviso.

## Riepilogo (linguaggio semplice)

1. Fedora è nata da Ubuntu e il codice del prodotto differisce da Ubuntu solo in 14 file; quasi tutto ciò che è nato su Fedora è o SELinux/RPM/firewalld, o KDE con KWin 6.8 da solo.
2. Si può portare così com'è (classe A, 9 voci): lingua della sessione (scelta dell'utente, altrimenti di sistema, più formati `LC_*`), percorso `PATH` come in locale, primo movimento del puntatore su GNOME, riga di registro «perché la connessione si è chiusa», chiusura forzata di KDE che ferma tutto il desktop, attesa di 5 s invece di 10 su KDE, una regola polkit per fwupd, pulizia di testi vecchi.
3. Si porta ma adattando (classe B, 3 voci): controllo a ogni avvio che l'aggancio «il locale chiude il remoto» ci sia ancora; la cache Mesa del lato root; i messaggi «reinstalla il pacchetto» (valgono anche su Debian/Ubuntu: `apt install --reinstall remotix` da solo non funziona per un pacchetto installato da file).
4. Specifico di Fedora, NON si porta (classe C, 10 voci): SELinux, RPM, firewalld, RPM Fusion, authselect e i file PAM dei display manager. Debian e Ubuntu hanno già `pam-auth-update`, che aggancia tutti i display manager insieme: lì non c'è nulla da portare.
5. Legato a KWin 6.8 (classe D, 4 voci): KDE con KWin da solo e cambio di risoluzione a caldo. Debian 13 ha KWin 6.3.6 e Ubuntu 26.04 KWin 6.6.6/6.6.7: restano col nostro labwc che ospita KWin.
6. Da decidere o provare (classe E, 4 voci): GNOME senza «ultima difesa», `force_guard_on` che resta acceso, `catatonit`, lingua senza codifica.
7. Scoperta importante: Debian è indietro anche rispetto a Ubuntu. Il lavoro di Ubuntu del 18-19 nov (database dconf di sistema, messaggio «compositor non installato», chiusura della sessione detta prima di smontare lo stage, controllo scala GNOME 50, fotogramma perso di KWin, profilo AppArmor corretto per il kernel nuovo, ecc.) NON è in `debian13/`. Allineare Debian vuol dire prima raggiungere Ubuntu, poi aggiungere le voci A/B.
8. Licenze: in Debian e Ubuntu `THIRD-PARTY-LICENSES` cita ancora «remotix-install» e 17 moduli Go (20 righe) e `LICENSE.md` cita ancora l'installatore `.run`. In Ubuntu labwc 0.9.3 + wlroots 0.19.2 SONO davvero nel pacchetto (restano); in Debian NO (il pacchetto usa il labwc della distribuzione): lì le voci su labwc/wlroots vanno tolte.
9. Senza contenitori: nessun `.deb` si può costruire con `build-deb.sh` (usa podman). Serve una macchina virtuale «costruzione» per Debian e una per Ubuntu, come Fedora (`build-rpm.sh`). Sul server di Debian il banco a VM esiste come script nuovo (`debian13/server/vm-radeon.sh`, 435 righe, non ancora in git).
10. Ordine proposto: codice A/B prima su Ubuntu (più vicino a Fedora e già aggiornato), poi Debian (allineamento a Ubuntu + A/B); i banchi di entrambe si preparano insieme.
11. Quattro domande al proprietario in fondo.

## Versioni di riferimento (dai PIANO e dagli studi)

| | Plasma / KWin | GNOME / mutter | Come parte KDE nel prodotto |
|---|---|---|---|
| Fedora 45 | 6.8.3 | 51 | KWin da solo `--virtual`, nessun labwc |
| Ubuntu 26.04 | 6.6.6-6.6.7 (studio `6-kubuntu-kwin-labwc.md`; il labwc di Ubuntu NON basta con KWin ≥ 6.5) | 50 | KWin dentro il NOSTRO labwc 0.9.3 + wlroots 0.19.2 (nel pacchetto) |
| Debian 13 | 6.3.6 (manuale tecnico e docs di Debian) | 48 | KWin dentro il labwc della distribuzione (`Recommends: labwc`); senza labwc ripiega su `--virtual` a misura fissa |

## Classe A — portabile così com'è

«Ubuntu?» e «Debian?» = la stessa cosa esiste già nel loro `src/`? (grep fatto).

| # | Che cosa | Dove (`fedora45/src`) | Fonte | Ubuntu? | Debian? | Lavoro |
|---|---|---|---|---|---|---|
| A1 | Lingua del desktop remoto = quella scelta dall'utente nelle Impostazioni (AccountsService, letta da root PRIMA del cambio d'identità), altrimenti quella di sistema; solo caratteri semplici; `session.c` controlla ancora che il locale esista (ripiego C.UTF-8) | `child.c:1608-1710` (`child_locale_*`, `child_accounts_language`), chiamata `1983-1984`, uso `2065-2070`, `envp[32]` (`1848`) | F34, F35 M (23 nov); decisione del proprietario 23-25 nov | no (C.UTF-8 fisso) | no | medio |
| A2 | Anche `LC_*` e `LANGUAGE` di sistema arrivano al desktop e sono ripristinati a fine sessione | `child.c` (stesso blocco), `session.c:3711-3716`, elenco `OUR_VARIABLES` `4798-4799` | F35 N | no | no | piccolo |
| A3 | `PATH` come in un accesso locale: se PAM non ne dà uno, il ripiego include `~/.local/bin:~/bin` | `child.c:2025-2040` | F4, F33 3, F34 | in parte: Ubuntu già prende il PATH da PAM (`child.c:1797`), ripiego fisso senza `~/.local/bin` | no: PATH fisso `/usr/local/bin:/usr/bin:/bin` (`child.c:1781`) | piccolo; non verificato se il PATH locale di Debian/Ubuntu ha `~/.local/bin` |
| A4 | Primo movimento assoluto del puntatore inviato due volte (difetto mutter: il primo clic dopo l'accesso cade sul bordo) | `input.c:257`, `1330`, `1937-1952` | F34 (mutter 51), F35 O; vecchio piano 1.0.2 punto B; E2 di Ubuntu «saltuario» | no | no (in `page.html` c'è `touch_announce_pointer`, residuo «1 caso su 13», PIANO Debian 17 nov) | piccolo; da provare su GNOME 48 e 50 con `check-multiuser`/`check-phone` |
| A5 | Riga di registro che dice chi ha chiuso la connessione QUIC e perché (alert TLS, silenzio, handshake) | `transport.c:952-1080`, `1087-1110`, `2184`, `2589` | F23, F31, F33 I | no | no | piccolo; usa l'API di ngtcp2 1.25, già quella dei due pacchetti (`Static-Built-Using: ngtcp2 1.25.0`) |
| A6 | Chiusura FORZATA di KDE (accesso locale con programma che non si chiude): ferma `graphical-session.target`, non solo `plasma-workspace.target` | `session.c:4588-4610`, `5645` | F36 (i1), PIANO 25 nov | no (`SESSION_UNIT_PLASMA`, `ubuntu26.04/src/session.c:4598`) | no (stessa costruzione) | piccolo codice, medio prove: la stessa struttura di unità esiste in Debian/Ubuntu (commento «PHASE 12» di `session.c`), ma i tempi su Plasma 6.3/6.6 sono non verificati: P7/P8 decidono |
| A7 | Su KDE, solo nella chiusura per accesso locale, la chiusura gentile aspetta 5 s invece di 10 | `session.c:113`, `4558-4590` (`wait_until_done_ms`), `5639` | F36 (i2); prova riuscita dal proprietario 25 nov | no | no | piccolo; compromesso dichiarato: una chiusura sana fra 5 e 10 s viene troncata |
| A8 | Regola polkit: `org.freedesktop.fwupd.refresh-remote` concessa alle sessioni REMOTIX (altrimenti finestra di password sul desktop GNOME) | `remotix-remote-sessions.rules:73-79` | F3 | no | no | piccolo; non verificato su Ubuntu (usa snap/App Center) e su GNOME 48 di Debian |
| A9 | Residui di testo verso l'amministratore: nel messaggio «servizio PAM mancante» Ubuntu e Debian citano ancora «Fedora and Arch… `.fedora`, `.suse`, `.arch`» | `ubuntu26.04/src/main.c:439, 466-472` e identico in `debian13/src/main.c`; la versione di Fedora è già riscritta (`fedora45/src/main.c`) | PIANO 25 nov («correggi»); note in `studio/manuali/note-*.md` | testo vecchio | testo vecchio | piccolo (solo testo; in Debian/Ubuntu il rimedio è quello di B3) |

## Classe B — portabile ma da adattare

| # | Che cosa | Dove | Fonte | Ubuntu? | Debian? | Lavoro |
|---|---|---|---|---|---|---|
| B1 | Controllo che la riga dell'aggancio «il locale chiude il remoto» ci sia ancora, a OGNI avvio del servizio, con una riga nel registro (criterio D4: «tutto automatico, l'admin non controlla nulla»). Su Fedora: `ExecStartPre=-remotix-pam-hook check` | `rpm/remotix.service:42`, `src/remotix-pam-hook` (comando `check`) | D4, F6 | no: solo un avviso nel `postinst` (`debian/remotix.postinst:44-49`) e il controllo periodico di 5 s | idem (non verificato riga per riga) | medio: su Debian il controllo è «`remotix-local-login` è in `/etc/pam.d/common-session`?», niente `authselect` |
| B2 | La sonda codec del lato root apre la cache Mesa in `/root/.cache`: `Environment=MESA_SHADER_CACHE_DISABLE=true` nell'unità | `rpm/remotix.service:39` | F24 (nata da un rifiuto SELinux) | no | no | piccolo; su Debian/Ubuntu non dà errore ma lascia file in `/root` (principio «purge pulito»): non verificato che li lasci |
| B3 | Messaggi «reinstalla il pacchetto»: il revisore ha mostrato che il rimedio «per nome» non funziona con un pacchetto installato da file; su Fedora ora «reinstall the package from its file». Su Debian/Ubuntu `apt install --reinstall remotix` ha lo stesso difetto | `kwin.c` ×3 (RX-KDE-001/002/003), `main.c:466-472` | PIANO 25 nov sera | testo vecchio (`ubuntu26.04/src/kwin.c`) | testo vecchio | piccolo; da decidere il testo esatto per `.deb` |

## Classe C — specifico di Fedora, NON si porta

| # | Che cosa | Dove | Fonte | Ubuntu? | Debian? | Equivalente già presente |
|---|---|---|---|---|---|---|
| C1 | Modulo SELinux (`remotix_t`, `remotix_net_t`, `remotix_hook_t`; regole `stop/status` su `xdm_unit_file_t`, lettura `accountsd_var_lib_t`, utenti confinati F5/F25, F30) | `selinux/*` | F2, F24-F28, F36 | n/a | n/a | AppArmor `remotix_network.apparmor` (esiste in entrambi) |
| C2 | Contesto SELinux della parte di rete (`remotix_net_t` scritto in `attr/exec`) | `walls.c:257-346` | F24 | n/a | n/a | AppArmor in `walls.c` (già c'è) |
| C3 | Contesto e portachiavi SELinux dell'utente (uscite 44-47) | `child.c:1141-1145`, `1700-1820`, `1972-1980`, `2190-2200` | F25, F32, F33 H | n/a | n/a | — |
| C4 | `-lselinux` | `Makefile:319-322` | F24 | n/a | n/a | — |
| C5 | Database dconf compilato in `/run/remotix` con nomi fissi (per l'etichetta SELinux) | `session.c:1840-1900` | F24 | n/a: lì compila accanto al database (`/etc/dconf/db`) | no (Debian non ha nemmeno il database di sistema, vedi sezione 2) | — |
| C6 | Pacchetto RPM, unità, `remotix.firewalld.xml`, `%firewalld_reload`, sysusers/tmpfiles RPM | `rpm/*`, `build/build-rpm.sh` | F1, F17, F20, F33 6 | n/a | n/a | `debian/*` e scheda `ufw` (`debian/remotix.ufw`) |
| C7 | Aggancio PAM «il locale chiude il remoto» per display manager: `remotix-pam-hook`, trigger RPM, correzione `.rpmnew` di sddm, ordine delle righe prima di `pam_selinux open` | `src/remotix-pam-hook`, `rpm/remotix.spec` | F6, F9, F18, F19, F21 | già risolto in un colpo da `pam-auth-update` su `common-session` (gdm3, sddm, lightdm lo includono) | idem | `debian/remotix.pam-config`; provato dal proprietario sulle live Debian (A2 del registro) |
| C8 | File PAM `remotix.pam` per Fedora (`password-auth`, `postlogin`, `pam_selinux … env_params`, `/etc/locale.conf`) | `src/remotix.pam` | F2, F34 | Debian e Ubuntu hanno lo stesso file (confrontato: identico fra loro), basato su `/etc/pam.d/sshd` di Debian, con `pam_env envfile=/etc/default/locale` | idem | — |
| C9 | Messaggi con `dnf`, pacchetto `dconf` (non `dconf-cli`) | `kwin.c`, `main.c:466-472`, `session.c:1870`, `2479` | PIANO 25 nov | n/a | n/a | testi `apt` (si adattano in B3/A9) |
| C10 | Codec video: RPM Fusion (`freeworld`) come dipendenza dichiarata | `server/live-installa.sh`, manuali | D1 | n/a: Mesa di Debian/Ubuntu ha già H.264 | n/a | già verificato dal pacchetto (rifiuto senza scheda, avviso se non codifica) |

## Classe D — legato a KWin 6.8 da solo (NON portabile finché Plasma è più vecchio)

| # | Che cosa | Dove | Fonte | Ubuntu (KWin 6.6) | Debian (KWin 6.3.6) |
|---|---|---|---|---|---|
| D1 | Avvio di KDE con `kwin_wayland --virtual` e wrapper `--kwin-virtual`, segno `REMOTIX_KDE_HOST=1`, nessuna scelta della scheda per KWin (F12) | `kwin.c:1713` (`kwin_virtual_alive`), `main.c:2882`, `session.c:3927-3960`, `kdehost.h:47-60` | F7, D2 | no: usa labwc nostro (`--kwin-nested`) | no: usa labwc di distribuzione |
| D2 | Cambio di risoluzione di KWin a caldo con `kde_output_management_v2` ≥ 22 (`add_cvt`) e i due protocolli copiati | `kwin.c:2053` (`kwin_output_resize`), `protocols/kde-output-*.xml`, `Makefile:288-296` | F7, F8, F13 | no | no (KWin 6.3.6 «cannot resize a virtual output»; il codice rifiuta pulito se il protocollo manca) |
| D3 | Ciclo di nascita/riaggancio KDE con correzione della misura PRIMA di montare lo stream, rifiuto `kde_refused`, ripiego dichiarato, ritentativi | `child.c:5886`, `8997`, `9035`, `9214-9290`, `11660` | F13, F14 | no | no |
| D4 | Aggancio di plasmalogin (il nuovo display manager di Plasma 6.8; su Debian/Ubuntu oggi sddm) | `remotix-pam-hook`, F9 | F9 | non verificato se i file PAM di plasmalogin includano `common-session`: da guardare quando Plasma 6.8 arriverà (Debian forky) | idem |

Il PIANO D2 dice che «quando Debian e Ubuntu avranno KDE 6.8 lo troveranno già scritto e provato»: nessun lavoro ora, solo non rompere nulla.

## Classe E — dubbi: serve una decisione o una prova

| # | Che cosa | Dove | Fonte | Posizione |
|---|---|---|---|---|
| E1 | GNOME ha la stessa costruzione di KDE ma nessuna «ultima difesa» (fermare il gestore dello schermo dalla parte root) se la chiusura gentile non finisce | `session.c` (chiusura GNOME), `rootside.c` | PIANO 25 nov «messo da parte (1)» | Il proprietario ha detto «sistemiamo solo KDE» per Fedora. Proposta: non costruirla; eseguire P7/P8 anche su GNOME (P8 per GNOME è BLOCKED, solo P7) e correggere solo se fallisce |
| E2 | `force_guard_on` resta acceso dopo una chiusura per accesso locale fallita | `session.c:5546-5560` (`force_guard_on`, anche usata a `5639`) | PIANO 25 nov (revisore) | Non corretto su Fedora: portarlo com'è (stesso comportamento) e annotare |
| E3 | `catatonit` (aiutante di podman avviato da Konsole) resta nel gestore dell'utente | solo banco | F36 | Probabilmente assente su Debian/Ubuntu (non c'è podman nelle live): non verificato; già nell'elenco degli aiutanti tollerati di `check-prelocal.py` |
| E4 | Non provati su Fedora: lingua senza codifica in AccountsService (`it_IT`), `LANGUAGE`, `FormatsLocale` | `child.c` A1/A2 | F34, F35, PIANO 25 nov | Da provare su Debian/Ubuntu al primo giro (desktop davvero in italiano con langpacks) |

## 2. Debian 13 contro Ubuntu 26.04 (`src/`, 23 file diversi)

Il confronto dice una cosa netta: **Ubuntu ha 8 giorni di lavoro in più** (voci del 18-19 nov, `[M]` su macchina vera Ubuntu) che Debian non ha. `debian13/src/session.c` ha 7404 righe, quello di Ubuntu 8829 (2177 righe di diff). Verificato col grep: in `debian13/src` mancano `db/remotix`, `blueman`, `DCONF_RT_REF`, `rcp_admitted_waiting`, `session_dconf_system_db_ensure`, «compositor is not installed», `lubuntu-update`.

### Che cosa ha Ubuntu che Debian non ha

| # | Che cosa | Dove (Ubuntu) | Natura | Va su Debian? |
|---|---|---|---|---|
| U1 | Database dconf di sistema `/etc/dconf/db/remotix` + profilo in `$XDG_RUNTIME_DIR/dconf/profile`, compilato dal `postinst`; ripiego dichiarato; blocchi GNOME | `session.c` (`dconf_*`, `session_dconf_*`), `rootside.c`, `debian/rules`, `postinst`/`postrm`, `control` | Nato per snap e Flutter (C5 del registro), ma è il modello generale | Sì per allineare (grande); su Debian non c'è lo sintomo (nessuno snap) |
| U2 | «Il desktop non può nascere: il compositor non è installato» (0x0E, nome del pacchetto) | `main.c`, `session.c` (`session_missing_component`), `page.html` | Generale | Sì (piccolo) |
| U3 | «La sessione è finita» detta PRIMA di smontare lo stage; `wt_dismiss_user_session_over`; `rcp_admitted_waiting`; scala rifiutata (`stage_refused_by_child`) | `child.c/h`, `webtransport.c/h`, `rcp.c/h`, `main.c` | Generale (robustezza del congedo) | Sì (medio) |
| U4 | Controllo e rimessa a 1 della scala di GNOME 50 (`mutter_scale_to_one`); `wlr_input_dropped` corretto | `mutter.c/h`, `input.c` | Legato a GNOME 50 | Non verificato se serve su GNOME 48; la guardia è a runtime |
| U5 | Fotogramma perso di KWin (`capture_frame_lost`, `kwin_poke`) | `capture.c/h`, `kwin.c/h`, `child.c` | Misurato su KWin 6.6.7 | Non verificato su KWin 6.3.6; innocuo se non scatta |
| U6 | Sidecar `org.freedesktop.ScreenSaver` risposto (Ctrl+Alt+Canc su KDE) | `kwin.c` | «Plasma 6.4 e successivi» (commento) | Su Plasma 6.3.6 probabilmente non serve: non verificato |
| U7 | Chiusura KDE: «Plasma muore in silenzio» (PHASE 12), `session_kde_logout_watch`, systemd che rifiuta lo stop | `session.c` | Plasma 6.x | Non verificato quale parte valga per 6.3 |
| U8 | XFCE: integrità del pannello (`xfce_panel_integrity`), autostart nascosti (`blueman`), `lubuntu-update`, tasto di blocco sospensione Ubuntu | `session.c` | Parte Ubuntu (Xubuntu/Lubuntu), parte generale | Misto; `blueman` e pannello probabilmente generali |
| U9 | Sentinella: errori di `logind` leggibili, «na» = non disponibile | `sentinel.c/h` | Generale | Sì (piccolo) |
| U10 | Tastiera: percorsi `xkeyboard-config-2` e `/etc/xkb` nel profilo AppArmor | `debian/remotix_network.apparmor` | xkb-data 2.46 di Ubuntu | Innocuo se aggiunto: non verificato che Debian 13 ne abbia bisogno |
| U11 | **AppArmor: `deny unix (bind, listen) addr=@**` al posto di `deny unix addr=@*`** (la riga vecchia vieta TUTTI i socket sul kernel nuovo: ogni accesso rifiutato) | `debian/remotix_network.apparmor:108-116` | Correzione C4 del registro, trovata su live Ubuntu kernel 7.0 | **Sì, da portare comunque**: su Debian 13 oggi «non ha effetto», ma un kernel nuovo la romperebbe (il registro lo dice) |
| U12 | Pacchetto: labwc nostro (build, `control`, `rules`, `labwc-ospite/`, `LABWC` nel `Makefile`) | `build/labwc-ospite/`, `debian/rules` | Solo Ubuntu (KWin ≥ 6.5) | **No**: Debian resta col labwc di distribuzione |
| U13 | `rootside.c` chiama `session_dconf_system_db_ensure()` | `rootside.c` (1 riga) | Segue U1 | Con U1 |

### Che cosa è specifico di Ubuntu (non si porta su Debian)

snap e programmi Flutter (causa di U1, non il modello), AppArmor con kernel che controlla i socket unix (U11 invece va portato per prudenza), `xkb-data 2.46` (U10), labwc nostro (U12), `lubuntu-update` e gli autostart di Ubuntu, GNOME 50 (U4), KWin 6.6 (U5, U6). `sudo-rs`: non l'ho trovato in `src/` né in `debian/` di Ubuntu (grep): non verificato nei manuali. Il registro `docs/REGISTRO-problemi.md` di Debian manca delle voci B3-bis, C4, C5, E3, E4 di Ubuntu (rinumerazione da fare).

## 3. Fuori da `src/`

### Strumenti di prova (`prove/`)

| Che cosa | Stato | Adattamento |
|---|---|---|
| `check-prelocal.py` P7 (terminale con `top`) e P8 (editor con testo non salvato) | Fedora, non in Ubuntu/Debian (Debian ha già P1-P6) | Nomi dei display manager (`gdm3`, `sddm`, `lightdm`, `sddm`; non `plasmalogin`), file di autologin (`/etc/gdm3/daemon.conf` e simili, non `custom.conf`), terminale e editor di Debian/Ubuntu (`kwrite`, `mousepad`; GNOME terminal/Ptyxis non verificato), P6 di Debian controlla `common-session` (già giusto) |
| `check-exit.py`, `check-resize.py`, `hold.py`, `hold-user.py`, `prelocal.sh`, `banco-vm/autologin-lightdm.sh`, `autologin-sddm.sh` | Solo Fedora | Generici; percorsi e `PORTS` da cambiare (`lib.py`: Ubuntu 8841-8844, Debian 8861-8864, Fedora 8851-8854) |
| `check-kde-birth/exit/live/resize.py` | Fedora (KWin da solo) | `check-kde-exit.py` forse riusabile per A6/A7; gli altri sono D |
| `giro-selinux.sh`, `wall-*.sh`, `wall-neg-domain.py`, `giro-*-radeon.sh` | Fedora (SELinux e giri) | C: non si portano (aperto su Fedora: `giro-selinux.sh` nasconde un controllo morto a metà, solo Fedora) |
| `debian13/prove/` manca `banco-vm/` e differisce da Ubuntu in 11 file (`all.sh`, `avlib.py`, `lib.py`, `check-desktop.py`, …) | Debian indietro | Si allinea con U-lavoro |

### Banco a macchine virtuali e costruzione senza contenitori

- `debian13/server/vm-radeon.sh` (435 righe, non in git): quattro VM Debian dalle live 13.8.0, porte ssh 2361-2364 e REMOTIX 8861-8864, cartella `/media/REMOTIX-DEBIAN/vm-radeon/`; **non ha la VM «costruzione»** (Fedora ce l'ha: ssh 2355). `debian13/server/prepara-server-vm.sh` (nuovo, senza podman). Ubuntu: `ubuntu26.04/server/vm-radeon.sh` (338 righe, porte 2341-2344/8841-8844, ISO 26.04.1), senza «costruzione».
- `build/build-deb.sh` (Debian e Ubuntu) fa `command -v podman` e costruisce in un contenitore (`build/Containerfile`): **vietato**. Fedora ha `build/build-rpm.sh`: copia l'albero nella VM `costruzione`, `dnf builddep`, ngtcp2/nghttp3 statici con `quic-static.sh` (già nei due alberi), `rpmbuild`, controlli R13/R4. Per i `.deb`: stessa strada con `apt build-dep`, `dpkg-buildpackage -b`, lintian, `changelog` generato da `RX_VERSION`/`RX_REVISION`/`SOURCE_DATE_EPOCH`; in Ubuntu in più la costruzione di labwc/wlroots (`build/labwc-ospite/build.sh`, tarball con sha256) e il sorgente `remotix-<versione>-labwc-source.tar.gz` (GPL: va pubblicato). I `Containerfile` non si cancellano (regola «mai cancellare»): restano come documentazione finché il proprietario non dice altro. Non verificato: che `dpkg-buildpackage` nella VM dia gli stessi byte della versione in contenitore (il flag `TWICE=1` esiste già).
- `server/live-installa.sh`: Ubuntu e Fedora ce l'hanno (da chiavetta live); Debian NO. Dentro c'è il nome del pacchetto (`remotix_1.0.0-…` in Ubuntu, `1.0.1` in Fedora): da aggiornare a 1.2.0 e da creare per Debian.

### Licenze

| File | Debian | Ubuntu | Fedora (già fatto 25 nov) |
|---|---|---|---|
| `THIRD-PARTY-LICENSES` | 20 righe su «remotix-install», Go 1.25.14 e 17 moduli Go; voci labwc 0.9.3 e wlroots 0.19.2 (16-17 righe) | stesso residuo Go/installatore; labwc/wlroots: restano (SONO nel pacchetto: `debian/rules`, `control` `Static-Built-Using: labwc (= 0.9.3), wlroots (= 0.19.2)`) | tolto tutto; restano 17 voci |
| `LICENSE.md` | §1 cita ancora `remotix-*.run`; §8 dice che il pacchetto «for RHEL / AlmaLinux 10» porta labwc in `/usr/lib/remotix/labwc` dentro il `.run`: **falso** per Debian (il pacchetto non ha labwc: verificato in `debian/rules` e `control`) | §1 cita `remotix-*.run`; §8 su labwc è VERO (`/usr/libexec/remotix/labwc`, sorgente accanto al pacchetto) e va solo tenuto aggiornato | senza labwc, senza `.run` |

Azione 1.2.0 (stessa regola dell'ordine «elimina riferimento a materiale che non c'è»): Debian = come Fedora + togliere anche labwc/wlroots e §8; Ubuntu = togliere installatore/Go e `.run`, tenere labwc/wlroots. Sono testi legali del proprietario: va mostrata la proposta riga per riga prima di scrivere. Non verificato il numero esatto di righe da togliere in Ubuntu (ho contato solo le occorrenze).

### Manuali (solo elenco dei capitoli toccati da A/B)

Technical (`manuals/sources/technical-*/`): **ch03** ciclo di vita (chiusura forzata, 5 s, A6/A7); **ch04**/**ch16** registro (riga «perché si è chiusa», A5); **ch10** input (primo movimento, A4); **ch12** desktop (lingua, PATH, KDE); **ch13** accesso (lingua dell'utente, aggancio e B1); **ch15** pacchetto (versione, B2/B3); **ch17** prove (P7/P8, banco a VM); **ch18** costruzione (senza contenitori); **ch24** problemi (voci F nuove); **ch09**/**ch20**/**ch21** solo per i riferimenti alla lingua. Per Debian si aggiungono i capitoli toccati da U1-U11 (non ho contato). User: **ch02** (installazione, «Requirements» e orologio del dispositivo se il proprietario vuole), **ch03** (lingua), **ch04** (problemi noti). `build.py --check` va rieseguito su entrambi. Versione 1.2.0 letta da `debian/` (come Fedora la legge da `rpm/remotix.spec`: non verificato come i due `build.py` di Debian/Ubuntu leggano la versione).

### Sito

Il sito non ha sorgenti nel repo. Sul tablet c'è `~/remotix-1.2.0-fedora/sito-prima/` (copia di sicurezza di oggi) e `sito-nuovo/` (con `fedora45.html`, indice, docs). Per Debian e Ubuntu alla 1.2.0: voce «1.2.0» nella storia delle due pagine, pacchetti e impronte nuovi, manuali nuovi, nota sull'orologio e sulla lingua; le pagine di oggi restano alla 1.0.1 finché non esce la 1.2.0. Solo su ordine del proprietario.

## 4. Le cose «messe da parte» su Fedora (PIANO 25 nov e F36 «Resta»)

| Voce | Riguarda Debian/Ubuntu? | Dove nello studio |
|---|---|---|
| GNOME senza «ultima difesa» | Sì: stessa costruzione | E1 |
| Debian/Ubuntu con lo stesso codice di forzata | È proprio A6/A7 | A6, A7 |
| `catatonit` | Quasi certamente no | E3 |
| Rifiuto innocuo `search` su `/proc/sys/dev` (SELinux) | No | C1 |
| `force_guard_on` acceso dopo una chiusura fallita | Sì (stesso codice) | E2 |
| Residui di testo (commenti, strumenti di prova ancora di Ubuntu, codice labwc-per-KDE irraggiungibile, `giro-selinux.sh`, commento `child.c:1636`) | In parte: commenti e testi sì (A9), il codice labwc-per-KDE NO (in Debian/Ubuntu è vivo) | A9; `fedora45/studio/manuali/note-*.md` |
| `dm_restart` del banco fragile su plasmalogin | Solo Fedora | C7 |
| `pkexec` su GNOME (SHELL vuoto, FAIL noto in tutte e tre) | Sì, già noto (E2 del registro di Ubuntu); non corretto | fuori perimetro |
| Orologio del dispositivo client sballato (F23) | Sì: stesso margine di un'ora in `certificates.c` | solo nota nel manuale utente |

## Domande per il proprietario

1. **Debian è indietro rispetto a Ubuntu: la 1.2.0 deve prima portare Debian al livello di Ubuntu (voci U1-U11, circa 8 giorni di lavoro) e poi aggiungere A/B?** Raccomando sì per tutto ciò che è generale (U1 database dconf, U2, U3, U9, U11); per le voci misurate solo su Ubuntu (U4 GNOME 50, U5 KWin 6.6, U6 Plasma ≥ 6.4) raccomando di portarle comunque se sono guardie a runtime, ma di dirlo come «non provato su Debian» nel manuale.
2. **Ampiezza delle prove.** Raccomando: giro base+input su tutti e otto i desktop, P1-P8 sui quattro display manager di ciascuna distro, giro completo (`all.sh`) su GNOME e KDE di ciascuna, aggiornamento 1.0.1 → 1.2.0 con una sessione aperta, e le tue prove da chiavetta (live Debian 13.8.0 e Ubuntu 26.04.1, regola F36: sempre con programmi aperti nel remoto) su tutti e otto. In alternativa, ridotta: giro completo solo su GNOME e KDE (risparmia circa 3 ore di Radeon).
3. **Sezione «Requirements» e nota «orologio del dispositivo» nei manuali utente di Debian e Ubuntu.** Per Fedora c'è (D1: «se serve, la stessa sezione anche nei manuali di Debian e Ubuntu»). Raccomando sì, breve: scheda che codifica H.264, porta 7447 nel firewall (`ufw`), orologio giusto.
4. **GNOME (e XFCE/LXQt) restano senza «ultima difesa»?** Raccomando sì: stessa decisione di Fedora, ma con P7 eseguito anche su di loro; si interviene solo se fallisce.

(Non chiedo: numero di versione 1.2.0, `.deb` costruiti in VM, ripulitura delle licenze, 5 s su KDE, uniformità delle regole: decisi.)

## Ordine di lavoro proposto

1. **Banchi (in parallelo, senza Radeon):** Ubuntu = quattro VM + «costruzione»; Debian = completare le quattro VM già in preparazione + «costruzione». Riscrivere `build-deb.sh` in versione VM (modello `build-rpm.sh`). Prima di partire: baseline con il codice 1.0.1 su un desktop per distro (P1-P8 sul 1.0.1 per vedere i difetti di partenza, in particolare F36 su KDE).
2. **Ubuntu prima per il codice**: è nato da Fedora, i file diversi sono pochi e già noti, ha già il lavoro del 18-19 nov, e tutto A/B si scrive una volta lì. Poi il programmatore porta le stesse modifiche su Debian dopo l'allineamento U1-U11 (Debian prende il codice di Ubuntu file per file, tenendo il labwc di distribuzione e senza `Makefile` `LABWC`). Un solo programmatore per albero (le modifiche agli stessi file vanno in sequenza), revisore (Fable) alla fine di ciascun gruppo.
3. **Debian per le prove su macchina vera per prima?** No: la Radeon è una sola; si fa fila Ubuntu poi Debian, ma Debian ha più rischio (banco mai provato con la Radeon, codice più vecchio): conviene avviare presto il suo banco.
4. Pacchetti 1.2.0 costruiti in VM, giro di prove, consegna delle macchine con pacchetto finale, chiavetta del proprietario, poi chiusura (registro dei problemi, manuali, licenze). Pubblicazione solo su suo ordine.

## Che cosa va provato e come

- **Banco a VM** (come Fedora): quattro VM per distro dalle live (Debian 13.8.0 e Ubuntu 26.04.1 in `/media/DOWNLOAD`), una sola con la Radeon alla volta, istantanea `pulito` e poi `codec`/pacchetto; nessun contenitore.
- **A1/A2 (lingua):** utente con scelta in AccountsService (`SetLanguage`), utente senza scelta, sistema in `it_IT`, locale inesistente (il desktop deve partire lo stesso), `LC_TIME` di sistema; desktop visto davvero in italiano con langpacks su almeno un desktop per distro. Su Debian e Ubuntu la lingua di sistema arriva da `/etc/default/locale` (riga `pam_env` già nel file PAM): E4.
- **A4:** `check-multiuser` (one-user, two-users) e `check-phone` su GNOME 48 (Debian) e 50 (Ubuntu): prima il difetto con 1.0.1, poi con la cura.
- **A6/A7/B1:** `check-prelocal.py` P1-P8 con SELinux n/a, AppArmor in vigore, su gdm3, sddm (KDE e LXQt), lightdm; tempi (forzata a ~5 s, tutto fermo ~0,5 s dopo) e assenza di core dump.
- **U11:** accesso riuscito con AppArmor in `enforce` su macchina vera o VM e riga «§5.1 … CONNECTED» nel registro (regola C4).
- **Aggiornamento** 1.0.1 → 1.2.0 con sessioni aperte, rimozione e purge puliti (nessun file in `/root` né nelle home).
- **Chiavetta del proprietario** (come Fedora, 25 nov): l'installatore da live (`live-installa.sh`, servito dal tablet) e la prova «il locale chiude il remoto» su ciascuna delle otto live, con programmi aperti (uno che si chiude da solo, uno che chiede conferma); registri salvati sul tablet in `~/remotix-prove-live/`.
- **Non verificato in questo studio:** il contenuto riga per riga dei 23 file di `debian13/src` contro Ubuntu (ho classificato i blocchi dai marcatori del codice e dal registro); lo stato dei 25 capitoli dei manuali; `check-desktop.py` e `banco-vm/box.sh` di Fedora (differiscono in 17 e 42 righe); lo stato reale del server e delle quattro VM Debian (non mi collego, per ordine).
