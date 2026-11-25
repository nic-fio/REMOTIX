# Inventario G4 — manuale tecnico di Fedora 45, capitoli ch15–ch18 (pacchetto, log, prove, build)

Data: 25 nov 2026. Sola lettura. Base: `ubuntu26.04/manuals/sources/technical-ubuntu26.04/ch15_package.py … ch18_build.py` (2002 righe, 38 sezioni:
8 + 12 + 10 + 8; l'inventario di Ubuntu ne contava 36 per questo gruppo, il conteggio di `CHAPTER` dà 38). Confronto con `fedora45/`:
`PIANO.md`, `docs/REGISTRO-problemi.md` (F1–F36), `rpm/remotix.spec`, `rpm/*`, `selinux/*`, `build/*`, `prove/*`, `server/*`, `diff -rq ubuntu26.04/src fedora45/src`.
Formato come `ubuntu26.04/studio/16-inventario-manuale-tecnico.md`. Dove non ho potuto verificare c'è scritto «non verificato».
Nessun comando è stato eseguito sul server o su una VM: nessun rpm, nessun log di giro è stato letto (stanno sul server e sul tablet in `~/remotix-prove-live/`, non letti).

## Riepilogo

| Capitolo | Sezioni | Vale com'è | Da correggere | Da riscrivere | Da togliere |
|---|---|---|---|---|---|
| ch15 The package | 8 | 0 | 2 | 5 | 1 |
| ch16 Logging and diagnostics | 12 | 4 | 7 | 1 | 0 |
| ch17 Testing | 10 | 0 | 4 | 4 | 2 |
| ch18 Build and release | 8 | 0 | 3 | 5 | 0 |
| Totale G4 | 38 | 4 | 16 | 15 | 3 |

Fatti trasversali emersi (valgono per più sezioni; li cito con la sigla T1…):
- T1. `rpm/remotix.spec` (502 righe) sostituisce `ubuntu26.04/debian/`: `%pre` 168, `%post` 217, `%preun` 280, `%postun` 380, trigger 433–464, `%files` 466, `%changelog` 496. `Version: 1.2.0` (spec:24), `ExclusiveArch: x86_64 aarch64` (spec:40). Non esiste «purge» in RPM: tutto ciò che Debian fa in `postrm purge` sta in `%postun` con `$1 -eq 0` (spec:380–430, commento spec:389–390).
- T2. Il labwc patchato di Ubuntu NON è nel pacchetto Fedora (decisione D2; spec:4, registro F1/F7). Su KDE gira `kwin_wayland --virtual` da solo, avviato da `remotix --kwin-virtual` (`src/main.c:2886-2892`, `src/kwin.c:1713`). Il codice labwc-per-KDE è rimasto nel sorgente ma irraggiungibile (F7): `kwin_nested_alive()` (`kwin.c:1490`), `REMOTIX_LABWC` (`src/Makefile:132-133`, `kwin.c:1531`); `--kwin-nested` risponde con errore.
- T3. SELinux (modulo `selinux/remotix.te|fc|if`, `policy_module(remotix, 1.1.1)`, te:1) prende il posto di AppArmor: tre domini `remotix_t` (lato root), `remotix_net_t` (rete), `remotix_hook_t` (gancio del login locale). Registro F24–F28, F31–F33.
- T4. Il gancio del login locale non è un profilo `pam-auth-update` ma lo script `/usr/libexec/remotix/remotix-pam-hook` (`src/remotix-pam-hook`, 335 righe), che mette la riga `pam_exec … remotix-local-login` nei file PAM di gdm, plasmalogin, lightdm, sddm, subito dopo `pam_selinux close` (hook:14-20), non dopo `pam_systemd`. Chiamato da `%post` (spec:253), `%preun` (spec:338), trigger (spec:433-464) e da `ExecStartPre=-… check` (`rpm/remotix.service:42`).
- T5. Le prove in `fedora45/prove/` sono ereditate da Ubuntu e SOLO IN PARTE adattate: `check-package.py` (55 occorrenze di apt/dpkg/.deb/AppArmor), `package-snap.py`, `fresh.sh` (`DEB=`, `/media/REMOTIX-UBUNTU/pacchetti`), `all.sh` (testo «path-to.deb»), `banco-vm/fresh-vm.sh` (`apt-get`, righe 3, 12, 14, 66) sono ancora quelli di Ubuntu e su Fedora non funzionerebbero; `lib.py` ha solo le porte nuove (8851–8854, lib.py:40); `banco-vm/box.sh` ha `install` con `rpm -U --nosignature --replacepkgs … || dnf -y install`. Non esiste `fedora45/boxes/` (niente contenitori, regola del proprietario).
- T6. Codice del prodotto che dice cose false su Fedora (difetti del sorgente, non del manuale: il manuale non li deve ripetere come veri, vedi punto (b)): `src/kwin.c:814, 825, 842` («apt install --reinstall remotix»), `src/main.c:467-473` («Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch»), `src/main.c:1189-1192` («`--no-install-recommends`»), `rpm/remotix.service:46-49` e `rpm/remotix.spec:220` («the desktops stay alive», falso dal 17 nov: lo stop chiude i desktop), `rpm/remotix.tmpfiles:1` («PHASE F … created by postinst»), `rpm/remotix.spec:239-244` ok. Decisione da chiedere: correggere i sorgenti o citarli com'è.

---

# ch15_package.py — «The package» (8 sezioni)

### 15.1 What the package is and how it is built — DA RISCRIVERE
Tutto il paragrafo è Debian. Per Fedora:
- Un solo pacchetto binario `remotix`, da `rpm/remotix.spec` (non da `debian/`); niente `3.0 (native)`, `debhelper-compat`, `Rules-Requires-Root` (prova: spec:1-40).
- Installazione: `sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm` (non `apt install ./remotix_*.deb`). Nome file = `Version 1.2.0` + `Release 1%{?dist}` (spec:24-25) → «1.2.0-1.fc45»; la riga «changelog names the suite resolute» va tolta.
- Build: sulla VM `costruzione`, senza contenitori (build/build-rpm.sh, vedi ch18); non «in an ubuntu:26.04 container».
- `Architecture: any` → `ExclusiveArch: x86_64 aarch64` (spec:40). I «muri» di rete esistono per x86_64 e aarch64: non verificato sul codice per aarch64 (stesso `walls.c` di Ubuntu più la parte SELinux, walls.c:260-348).
- Elenco di ciò che il pacchetto cambia: utente di sistema `remotix` + cartelle (sysusers/tmpfiles), «scheda» firewalld (non ufw) definita e non aperta (`/usr/lib/firewalld/services/remotix.xml`, spec:146), due regole polkit, il modulo SELinux (`/usr/share/selinux/packages/remotix.pp.bz2`, spec:131), il gancio del login locale (righe nei file PAM delle schermate di accesso, NON `/etc/pam.d/common-session` che su Fedora non esiste: check-prelocal.py:552), servizio installato spento.
- Tre cose specifiche: non più «labwc guest + dconf + needrestart» ma «modulo SELinux + `remotix-pam-hook` con i trigger + dconf (compilato in `%post`)»; il drop-in needrestart c'è ancora (`rpm/needrestart.conf`, spec:162).
- La nota «Stale wording» (commenti che parlano di «engine», di KillMode e «the desktops stay alive») si applica ancora a `rpm/remotix.service:46-49`, spec:220, `rpm/remotix.tmpfiles:1`, ma con file diversi: elencarli come in T6. Il pezzo su `--session-fd` (DECISIONS-11 §11.55) vale solo se si è verificato il codice di `child.c`: non verificato.
- Prove sul numero di versione: «1.2.0» nel manuale deve venire dallo spec (piano manuali, passo 4), non essere scritto a mano.

### 15.2 Package metadata: Depends and Recommends — DA RISCRIVERE
Tabella e liste con nomi Fedora (spec:70-102). Non esiste `dpkg-shlibdeps`: rpm trova da solo le librerie del binario (commento spec:67).
- `Requires` (spec:70-77): `pam`, `gawk` (usato in `%preun`), `systemd-pam` (= `pam_systemd`, al posto di `libpam-systemd`), `shadow-utils` (usermod/gpasswd/userdel), `systemd`, `dbus-broker` (al posto di `dbus-user-session`), `pipewire`, `wireplumber`; più `Requires(post|preun|postun)` (spec:78-84: `systemd`, `shadow-utils`, `util-linux-core` per `runuser`) e `firewalld-filesystem` (spec:102). Non c'è un equivalente di `libpam-runtime` (niente `pam-auth-update`) né di `libpam-modules`.
- `Recommends` (spec:90-94): `labwc`, `dconf` (NON `dconf-cli`), `wlr-randr`, `xorg-x11-server-Xwayland`, `dejavu-sans-fonts`. NON ci sono `va-driver-all`, `mesa-vulkan-drivers`: i codec sono un requisito dell'amministratore (D1, spec:86-89): RPM Fusion, `mesa-va-drivers-freeworld`.
- Il paragrafo su «va-driver» e `universe` va tolto (non c'è `universe`); il Mesa di Fedora esclude H.264/HEVC (PIANO.md «Ostacoli», punto 1).
- Static-Built-Using → `Provides: bundled(ngtcp2) = 1.25.0`, `bundled(nghttp3) = 1.18.0` (spec:97-98). labwc e wlroots NON sono più statici nel pacchetto.
- Build-Depends → `BuildRequires` (spec:43-65): `openssl-devel` (OpenSSL di Fedora 4.0, D8, nessun ripiego su `openssl3`; il minimo 3.5.0 resta in `MINIMI`, Makefile:424), `pam-devel`, `libselinux-devel` (nuovo), `glib2-devel >= 2.80`, `pipewire-devel`, `libdrm-devel`, `libva-devel`, `opus-devel`, `zlib-devel`, `libei-devel >= 1.3.901`, `libxkbcommon-devel`, `mesa-libgbm-devel`, `wayland-devel`, `vulkan-headers`, `vulkan-loader-devel`, `systemd-rpm-macros`, `firewalld-filesystem`, `%{?selinux_requires}`. Niente `dh-apparmor`, `meson`, `hwdata`, `libseat-dev`… (servivano al labwc).
- Il paragrafo «What apt really installed … logs vm-radeon-installa-<name>.log» è di Ubuntu: da togliere. Per Fedora esiste solo `server/live-installa.sh` (installa codec RPM Fusion, `dnf install` dell'rpm, firewalld a runtime, `systemctl enable --now`): cosa abbia tirato dentro dnf sulle quattro VM: non verificato.
- Il rifiuto con codice 0x0E senza `labwc` e l'avviso del `%post` (spec:268-274) valgono ancora; sulle VM Fedora il caso XFCE/LXQt senza labwc: non verificato. Nota: Fedora non porta `gnome-shell` su XFCE, quindi l'avvertimento «Xubuntu carries gnome-shell» va tolto.
- `check-package.py recommends`: non aggiornato (elenca i Recommends Debian, vedi 17.5).
- `universe`: tutto il paragrafo va tolto.

### 15.3 The preinst refusals — DA CORREGGERE
È `%pre` (spec:168-214); stesse due rifiuti, stessa logica, stessi messaggi in inglese (spec:179-180, 205-206).
- Sostituire «preinst» con «%pre»; `$1 = install` → `$1 -eq 1` (spec:171).
- Rifiuto senza render node: stesso test `/sys/class/drm/renderD*` (spec:172-178). Non verificato su Fedora il rifiuto senza scheda (una VM con `virtio-vga` ha il nodo, come su Ubuntu).
- Rifiuto per «account `remotix` di una persona»: identico (UID_MIN da `/etc/login.defs`, shell, home `/home`, `/root`, `/var/home`: spec:182-209).
- Novità: `%global __sysusers_path ^$` (spec:20): rpm 6 crea l'utente PRIMA di `%pre`; il pacchetto lo spegne per poter vedere se l'account esisteva già, e in `%post` esegue `systemd-sysusers` a mano. Il file `net-user-preexisting` si scrive solo se `/usr/lib/sysusers.d/remotix.conf` non c'è ancora (spec:208-212). Da spiegare.
- Ultima riga di `%pre`: `%selinux_relabel_pre -s targeted` (spec:214), solo dopo i rifiuti.
- Il paragrafo «Verification on Ubuntu 26.04» (check-package.py preinst, «not part of the VM bench») va riscritto: `check-package.py` non è adattato a rpm (T5).

### 15.4 The postinst: user, folders and encoding test — DA RISCRIVERE
È `%post` (spec:217-277); ordine diverso e voci nuove:
1. `%selinux_modules_install -s targeted …remotix.pp.bz2` e `%selinux_relabel_post` (spec:223-224). Se `selinuxenabled` e il modulo non risulta in `semodule -l`, avviso con il comando `sudo semodule -X 200 -i …` (spec:226-228). Come per Debian: avviso, mai fallimento.
2. `systemd-sysusers remotix.conf`, `systemd-tmpfiles --create remotix.conf` (spec:230-231): uguale. La frase «dh_installsysusers belongs from compat 14» si toglie (non c'è debhelper).
3. Compilazione dconf (spec:233-249): uguale a Ubuntu nel `%post` (`/etc/dconf/db/remotix.new.$$` poi `mv`); ma il pacchetto di riferimento è `dconf` (non `dconf-cli`). ATTENZIONE: il servizio, all'avvio, ricompila diversamente su Fedora: nel lavoro root compila in `/run/remotix/dconf-compile.tmp` e crea solo i due nomi fissi `/etc/dconf/db/remotix.new` e `remotix` (`src/session.c`, registro F24 «Il database dconf»; transizioni SELinux per nome, te:252-258): la frase del manuale «`session_dconf_system_db_ensure()` compiles to a temporary file» va corretta. Le 24 chiavi: da ricontare (`remotix --dconf-keyfiles DIR` poi contare).
4. `restorecon -R /var/lib/remotix /run/remotix /etc/dconf/db/remotix` (spec:251): NUOVO.
5. Gancio del login locale: `remotix-pam-hook apply` (spec:253), al posto di `pam-auth-update`. Avviso: «the hook of the local login could not be fully applied». Spariscono «pam-auth-update not found» e «common-session was edited by hand». Come controllare: `grep -l remotix-local-login /etc/pam.d/*` (non `common-session`); disattivare: NON esiste un menu; `remotix-pam-hook remove` è l'unico modo, ma non è stato provato come procedura per l'amministratore: non verificato. L'avvio del servizio riapplica la riga (`ExecStartPre … check`).
6. Test di codifica `timeout 30 remotix --encoding-test h264`, solo a prima installazione (`$1 -eq 1`, spec:258-264): uguale, ma l'avviso dice di abilitare RPM Fusion (free) e installare `mesa-va-drivers-freeworld` (spec:260-262), non `va-driver-all`.
7. Avviso labwc mancante: stesso test, comando `sudo dnf install labwc` (spec:268-274).
8. `%firewalld_reload` (spec:276) e `%systemd_post remotix.service` (spec:277): NUOVI. Il reload serve perché subito dopo l'installazione `firewall-cmd --permanent --add-service=remotix` rispondeva INVALID_SERVICE (registro F17, F20); non apre nulla (D5).
- Il riquadro «Warning» sul commento in testa («the engine…») non si applica allo spec (il commento di spec:217-221 dice però «the desktops stay alive» sull'upgrade: falso, T6).
- Tolti: tutto `#DEBHELPER#`, `dh_apparmor`, il profilo `remotix_network`.

### 15.5 Files the package installs — DA RISCRIVERE
Da `%install` (spec:135-165) e `%files` (spec:466-494); l'albero va rifatto:
- `/usr/libexec/remotix/`: `remotix`, `remotix-local-login`, `remotix-polkit-seated`, `remotix-pam-hook` (NUOVO); NON `labwc`.
- `/usr/share/remotix/`: `page.html`, `remotix.conf`, `linked.json`, `dconf/remotix.d/`, `belts/` (due file) — come Ubuntu.
- NUOVI: `/usr/share/selinux/packages/remotix.pp.bz2`; `/usr/lib/firewalld/services/remotix.xml` (7447/tcp e 7447/udp, `rpm/remotix.firewalld.xml:7-8`).
- Tolti: `/usr/share/pam-configs/remotix`, `/etc/ufw/applications.d/remotix`, `/etc/apparmor.d/remotix_network`, `/usr/share/doc/remotix/copyright` (ora `%license LICENSE.md`, `%doc THIRD-PARTY-LICENSES`, spec:467-468).
- `/etc`: `%config(noreplace)` per `/etc/remotix/denied-users`, `/etc/pam.d/remotix`, `/etc/needrestart/conf.d/remotix.conf` (spec:482-486). Sono 3, non 5: «The release package declares five» da correggere. `/etc/remotix/remotix.conf.d/` cartella vuota.
- Unità in `%{_unitdir}` = `/usr/lib/systemd/system/remotix.service`; sysusers in `/usr/lib/sysusers.d/`, tmpfiles in `/usr/lib/tmpfiles.d/`.
- Numero di voci: «59 entries» da ricontare con `rpm -qlp remotix-1.2.0-1.fc45.x86_64.rpm | wc -l` (non ho il file).
- `src/remotix.pam` è lo stack di `sshd` di Fedora (`password-auth` + `postlogin`, due `pam_selinux`, `pam_loginuid`, `pam_namespace`, due `pam_env`, la seconda su `/etc/locale.conf`): src/remotix.pam:33-72. Sezione NUOVA da scrivere (vedi (a)).
- Le due regole polkit: `40-remotix-remote-sessions.rules` ha SEI azioni sul lato «refresh/macchina» (Fedora aggiunge `org.freedesktop.fwupd.refresh-remote`, src/remotix-remote-sessions.rules:76-79; il commento del file dice ancora «the five actions»), non cinque. `50-remotix-no-poweroff.rules`: 19 azioni (`grep -c '"org\.' src/remotix-no-poweroff.rules` → 19); il sorgente è identico a Ubuntu per questa parte. Il gruppo admin è `wheel` (dichiarato nel commento del file).
- Sottosezione «The AppArmor profile» (tutta, tre punti) → DA TOGLIERE e sostituire con «The SELinux module» (vedi (a)): tipi dei file da `selinux/remotix.fc:1-8`.
- Il paragrafo «Folders created at run time» (tmpfiles) vale quasi com'è: confrontato `diff ubuntu26.04/debian/remotix.tmpfiles fedora45/rpm/remotix.tmpfiles` → solo il commento; ma l'uid di `remotix` («got uid 972») è di una VM Ubuntu: non verificato su Fedora.
- Il paragrafo «firewall profile» (ufw) → firewalld: riga dell'amministratore da registro F20: `sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload` (zona predefinita; altra zona con `--zone=NOME`); la porta nel profilo è 7447 fissa come per ufw (`REMOTIX_PORT` in `rpm/remotix.conf:10`).
- Vale com'è: file KDE `org.kde.remotix.desktop` (`rpm/org.kde.remotix.desktop:7`), certificato non nel pacchetto, nessun file di bench (spec:126 BENCH_ON).
- Il ramo «The unit comes from debhelper» → «The unit is installed by `%install` (spec:162)».

### 15.6 Our own labwc (KDE) — DA TOGLIERE
Il pacchetto Fedora non costruisce né installa il labwc nostro (spec:4; F1, F7, decisione D2). Sezione sostituita da «KDE with KWin alone» (vedi (a)). Per verità storica, due righe di rimando alla differenza con Ubuntu. Tolti dal testo anche: licenza GPL di labwc nel pacchetto (ma `LICENSE.md:95-97` di Fedora dice ancora «the REMOTIX package for Ubuntu 26.04 carries labwc»: difetto del sorgente, T6), `remotix-<ver>-labwc-source.tar.gz`, `build/labwc-ospite/` (non esiste in `fedora45/build/`).

### 15.7 Removal: prerm, postrm and purge — DA RISCRIVERE
`%preun` (spec:280-377) e `%postun` (spec:380-430); RPM non ha «purge»: tutto ciò che Debian fa in `purge` avviene alla rimozione (`$1 -eq 0`).
- Ordine in `%preun`: NON si toglie la riga PAM per prima. Qui: chiude le sessioni (`loginctl terminate-session`, 15 s poi SIGKILL sullo scope, 5 s), ferma il servizio, POI `remotix-pam-hook remove` (spec:338: il servizio acceso rimetterebbe la riga con `ExecStartPre`), seconda spazzata, `graphical-session.target` per chi non ha altre sessioni, `gpasswd -d`, `--drop-render-grants`. Il resto della logica è uguale.
- `%postun` (spec:380-430): `%selinux_modules_uninstall -s targeted remotix`, `%selinux_relabel_post`, `%systemd_postun_with_restart`, `%firewalld_reload`; poi, solo a rimozione: rimuove `/var/lib/remotix/net`, `certificates`, `ban`, `/run/remotix`, il registro `render-grants` (a meno del marcatore), i file prodotto nelle case (`runuser`, per nome), l'utente `remotix` (solo se non preesisteva e uid 1–999), `/etc/dconf/db/remotix*`, `*.rpmsave` per nome, `rmdir` delle cartelle vuote, `needrestart/conf.d`. NUOVO: `restorecon -R /var/lib/remotix` se la cartella resta (spec:422).
- Spariscono: scrittura su `/sys/kernel/security/apparmor/.remove`, `deb-systemd-invoke`, i lintian-override.
- Frasi da non copiare: «apt remove keeps the configuration»: su Fedora `dnf remove` toglie i `%config(noreplace)` non modificati e lascia `*.rpmsave` per quelli modificati (spec:427-428 li tolgono per nome). Il limite «utenti non elencati» (warning) vale uguale.
- Nuovo, da dire: i trigger su `gdm`, `lightdm`, `sddm`, `plasma-login-manager` (spec:433-464): perché sddm è speciale (i suoi file PAM sono `%config` di sddm, modificati sul posto: F21, spec:442-451).
- Verifica: rimozione, reinstallazione e aggiornamento provati su VM (F24: «aggiornamento da l6/k4b provato; rimozione… reinstallazione da zero»), `check-package.py` non adattato e non eseguito (T5). La parte «not run on Ubuntu 26.04» va riscritta con questi fatti; la rimozione del pacchetto 1.2.0: non verificato (pacchetto non ancora ricostruito, PIANO.md «piano manuali», punto 4).

### 15.8 Service policy: installed disabled — DA CORREGGERE
- Il codice `dh_installsystemd` sparisce: sono i macro `%systemd_post/%systemd_preun/%systemd_postun_with_restart` (spec:277, 377, 385). Il preset di Fedora è `disable *`: installato spento è il comportamento normale (PIANO.md «Che cosa regge già»). Su upgrade `%systemd_postun_with_restart` riavvia il servizio solo se era acceso: il riavvio chiude i desktop (T6).
- Comandi: `sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm` e `sudo systemctl enable --now remotix`; reinstallare: `sudo dnf reinstall ./remotix-….rpm` (il banco usa `rpm -U --nosignature --replacepkgs`, banco-vm/box.sh).
- Aggiungere la riga firewalld (F20) dopo l'enable.
- needrestart: il drop-in `$nrconf{override_rc}{qr(^remotix\.service$)} = 0;` è identico (`rpm/needrestart.conf:8`), ma su Fedora `needrestart` non è di serie e lo strumento equivalente è `dnf needs-restarting`: non verificato che il drop-in abbia effetto su Fedora; il commento del file cita «dnf-automatic with needrestart».
- Nome `%H` nel certificato e `REMOTIX_OPTIONS=--name <IP>`: identico (rpm/remotix.service:13-15, 45).
- Nuovo: `ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check` e `Environment=MESA_SHADER_CACHE_DISABLE=true` (rpm/remotix.service:39, 42) — solo Fedora.
- Riferimento a «point 1 of decision §10.12 of DECISIONS.md»: vale se `docs/DECISIONS.md` c'è in fedora45 (c'è: `ls fedora45/docs`).

---

# ch16_logging.py — «Logging and diagnostics» (12 sezioni)

Nota di metodo: `src/log.c`, `src/log.h`, `docs/REGISTRO-priorita.md`, `rootside.c`, `sentinel.c`, `page.c` sono IDENTICI a Ubuntu (`diff -q`, nessuna differenza); le tabelle che descrivono il funzionamento di `line()` e delle aree valgono. Cambiano i file della distribuzione e le righe di `session.c`, `child.c`, `kwin.c`, `transport.c`, `walls.c`, `main.c`.

### 16.1 The log module — DA CORREGGERE
Una riga: la nota «Outside the funnel» cita `kwin_nested_alive()` e il prefisso `remotix --kwin-nested:`; su Fedora l'aiutante è `kwin_virtual_alive()` con prefisso `remotix --kwin-virtual:` (`src/kwin.c:1713, 1729, 1734, 1743`). Il resto vale (funzioni, macro, tabella `src/log.h`). Ricontare il numero di righe del log di esempio «28,035» solo se lo si cita: è un commento di `log.c`, invariato.

### 16.2 Anatomy of a log line — VALE COM'È
Stesse regole (buffer 4096, controlli, identità 48). `log.c` invariato. Le tre righe di esempio sono generiche.

### 16.3 Log areas — VALE COM'È
Nessuna area nuova su Fedora (`grep` delle costanti: stesso `log.h`). Le righe SELinux e KDE nuove usano aree già esistenti (`rootside`, `child`, `session`, `quic`, `capture`).

### 16.4 Whose line it is — VALE COM'È
`log_user()` e HMAC invariati (rcp.c identico). Le cifre «57,121 lines in 90 s» sono un commento di `log.h`.

### 16.5 Where the log lines go — DA CORREGGERE
- `debian/remotix.service` → `rpm/remotix.service`; `--journal` è in `ExecStart` (rpm/remotix.service:45). Stessa tabella dei flussi.
- Frase finale: «The package removes the file when the package is purged» → «alla rimozione del pacchetto, `%postun`, per utente e per nome, `runuser`» (spec:400-410); i file in elenco sono gli stessi (`session.log`, `xfce-chiavi`, `xfce-vecchi-ripristinati`, `lxqt-restored`, `gnome-ripristinato`) più `~/.config/dconf/remotix`.
- Nota SELinux nuova: la parte di rete scrive solo `/var/lib/remotix/net` e `/run/remotix/net` (F24); `session.log` lo scrive il figlio nel contesto dell'utente (nessun cambio): non verificato che serva una regola.

### 16.6 The systemd journal output — DA CORREGGERE
- La nota «A profile can silence the journal» (AppArmor, `deny unix addr=@*`, difetto C4) è di Ubuntu: su Fedora l'equivalente è il modulo SELinux: `logging_send_syslog_msg(remotix_net_t)` permette al lato di rete di scrivere sul journal (`selinux/remotix.te:294`). I rifiuti SELinux appaiono come AVC nel journal, e NON sono silenziosi come un `deny` AppArmor in complain; `ausearch` sulle VM non li vedeva «anche quando il giornale ha gli AVC» (F24): usare `journalctl -b -g 'avc:'`.
- Il resto (campi `MESSAGE`, `PRIORITY`, `REMOTIX_AREA`, `REMOTIX_TENANT`, scelte di progetto, comandi `journalctl`) vale.
- Il rimando `rif("Files the package installs")` nella nota va aggiornato se si cambia titolo (vedi (c)).

### 16.7 Journal priorities and the rule of the head mark — DA CORREGGERE
- La tabella e i conteggi (33 pattern, 5/24/4) vengono da `docs/REGISTRO-priorita.md` (invariato, misurato su quattro contenitori Debian 13): vanno dichiarati «non rimisurati su Fedora», non «su Ubuntu 26.04».
- Righe nate su Fedora da classificare con la regola del segno in testa (`log.c`: ⛔ → 3, ⚠ → 4, altro → 6): `⛔ KDE: SESSION REFUSED, and closed` (child.c), `⏳ KDE: KWin's output is not ready yet … attempts since the last line` (il segno ⏳ NON è né ⛔ né ⚠: esce con priorità 6 «info»), `⭐ KWin alone: the output … is WxH after N ms` (kwin.c), le uscite 44–47 del figlio (sotto, 16.9), la riga `connection with … closed — the PEER closed it: transport error … TLS alert …` (transport.c `close_why()`, F23, area `quic`). Nessuna misurata: «non verificato».

### 16.8 What never enters the log — VALE COM'È
Regole invariate: password, caratteri digitati, `log_speakable_key`, ecc. Una frase da controllare: «`RCP: ⛔ PAM COULD NOT JUDGE` (for example a missing PAM service file)» vale; su Fedora un file `/etc/pam.d/remotix` mancante porta a `pam_deny` («other»), come dice `main.c:467-470`.

### 16.9 The startup declarations — DA RISCRIVERE
La tabella delle dichiarazioni vale in gran parte; l'estratto reale e le voci di piattaforma no.
- Estratto «A real start on Ubuntu 26.04» (journal del 19 nov, VM Ubuntu, `vm-radeon-controllo.sh`): da TOGLIERE. Serve un estratto Fedora preso da un log vero (ci sono i giornali della prova da chiavetta in `~/remotix-prove-live/fedora45-*` sul tablet: non letti, «non verificato»). Anche la riga «uid 972», «landlock ABI 8» e il kernel «7.0»: non verificati su Fedora.
- Riga dei muri: oggi dice `AppArmor: …; landlock ABI …` ; su Fedora il codice (`walls.c:226, 250` e `307, 318, 334, 340`) scrive in sequenza una nota AppArmor (di norma `AppArmor: off`, kernel senza AppArmor: non verificato) e una nota `SELinux: born in system_u:system_r:remotix_net_t:s0`; la tabella va scritta con `walls_in_force()` che ora ha le due.
- KDE: righe `RX-KDE-001/002/003` (`kwin.c:773-777, 814, 824, 841`): il rimedio stampato dal sorgente dice «apt install --reinstall remotix» (T6): su Fedora il rimedio vero è `sudo dnf reinstall remotix`.
- Riga «PAM service DOES NOT EXIST … the administrator runs apt install --reinstall remotix»: nel sorgente Fedora il testo è quello di `main.c:467-473` (nomina `src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch`, non `apt`): citare il testo vero. Su Fedora senza il file ogni password giusta è rifiutata (`pam_deny`).
- Riga «labwc missing → 0x0E»: `main.c:1186-1192` vale per XFCE/LXQt, ma il testo parla di `--no-install-recommends`: su Fedora è `--setopt=install_weak_deps=False` (spec:264-266 lo dice giusto); KDE non ha bisogno del labwc (la condizione resta in `session_missing_component()`, session.c:769).
- Sezione «D-015 dconf»: valida (stesse righe; session.c identico salvo il modo di compilare), ma `dconf-cli` → `dconf`, e le righe `rootside ⭐ D-015: … compiled now from /usr/share/remotix/dconf/remotix.d` usano `/run/remotix/dconf-compile.tmp` (T3/15.4). Le righe «from the runs of 19 Nov on the Ubuntu VM» (log `log/dconf-correzione/`) non valgono per Fedora.
- Tabella «Other declarations of this tree»: la riga `labwc` mancante vale per XFCE/LXQt; la riga sulla scala (0x0E) e `the desktop of this machine` valgono (non provate su Fedora: non verificato).
- Aggiungere: uscite del figlio con SELinux acceso (`src/child.c`): 44 «no context like a local login's could be worked out», 45 «the exec context could not be set», 46 «the next exec would not leave the root side's domain», 47 «the session keyring could not be made with the user's context»: tutte «the login is REFUSED» (F25, F31); riga KDE `⛔ KDE: SESSION REFUSED, and closed — %s` e `⏳ KDE: KWin's output is not ready yet`.
- Aggiungere: riga di chiusura QUIC col motivo (F23): `connection with <addr> closed (N left) — the PEER closed it: transport error CRYPTO 0x12e = TLS alert 46 certificate_unknown …; TLS handshake NOT completed` (area `quic`). Utile perché l'orologio sbagliato del dispositivo client è la causa nota di «Opening handshake failed».

### 16.10 Lines of the stop, the orphan rule and the local-login hold — DA CORREGGERE
`rootside.c` è identico, quindi quasi tutte le righe valgono. Cambia solo KDE (session.c):
- Righe `session` nuove/diverse nella chiusura per accesso locale su KDE: `asking the Plasma session to exit (org.kde.Shutdown.logout)`, poi `⚠ the session does not exit: I close it by force (StopUnit graphical-session.target), whatever was not saved is lost` (session.c:5635-5648; prima era `plasma-workspace.target`: F36). Attesa dell'ordinata: 5 s in chiusura per accesso locale (`KDE_PRELOCAL_ORDERLY_MS 5000`, session.c:~112), 10 s altrimenti (`WAIT_EXIT_MS 10000`, session.c:108).
- La riga `⚠ local login of «user» … STILL there after 20 s` resta (PL_CEIL_MS 20000, rootside.c:2431); su KDE a Fedora la forzata dopo 5 s e tutto fermo in ~0,56 s (F36): da citare come tempi misurati sulla macchina vera (registro F36), non come garanzia.
- Il rifiuto SELinux che prima si vedeva (`avc: denied { stop } … tcontext=xdm_unit_file_t`, 3 rifiuti) è la regola `allow remotix_t xdm_unit_file_t:service { stop status };` (te:214): da dire nel manuale come diagnosi.
- «Not traced: what the page shows during the hold»: invariato (non verificato).
- Limite dichiarato in F36 («Resta»): GNOME ha la stessa costruzione di KDE senza ultima difesa; alla scadenza il login passa comunque (comportamento di oggi su GNOME/XFCE/LXQt).

### 16.11 Environment variables read by the product — DA CORREGGERE
- Elenco dei nomi `REMOTIX_`: Fedora ha UNO IN PIÙ rispetto a Ubuntu: `REMOTIX_KDE_HOST` (`src/kdehost.h:61`, `#define KDEHOST_ENV "REMOTIX_KDE_HOST=1"`, messo nell'unità di KWin da `session.c`; serve alla spazzata per riconoscere un KWin di REMOTIX, F7). Verificato con `grep -rhoE 'REMOTIX_[A-Z0-9_]+' src/*.c src/*.h | sort -u` su entrambi gli alberi. Non è una variabile letta con `getenv()` ma letta da `/proc/<pid>/environ`: dirlo.
- `REMOTIX_LABWC` resta come #define (Makefile:132-133) ma su Fedora non è mai impostato dal pacchetto (spec:123: `make … all` senza `LABWC=`) e il codice che lo usa è irraggiungibile (kwin.c:1531): riscrivere la frase.
- `REMOTIX_PORT` e `REMOTIX_OPTIONS`: «read by debian/remotix.service» → `rpm/remotix.service:30-31, 45` e defaults in `rpm/remotix.conf:10, 14`.
- Aggiungere nella frase delle variabili «standard»: `LANG` scelta dall'utente (AccountsService) o di sistema, `LC_*` e `LANGUAGE` da `/etc/locale.conf` (`child.c` `child_locale_read`, `session.c:3711`, F34/F35) e `PATH` (come in un accesso locale, F4). Il manuale Ubuntu dice che la lingua è `C.UTF-8`: su Fedora no.
- La variabile `MESA_SHADER_CACHE_DISABLE` è nel `[Service]` dell'unità (rpm/remotix.service:39), non è REMOTIX_: citarla in nota.
- Il resto vale (`REMOTIX_PAM_LOG_TAG`, `REMOTIX_VPP_PADDING`, `REMOTIX_VULKAN_CONVERSION`, avvertenza sul figlio).

### 16.12 Diagnostic instruments — DA CORREGGERE
- `remotix --dconf-keyfiles DIR` è eseguito «by `debian/rules`» → da `%install` dello spec (spec:~140: `src/remotix --dconf-keyfiles $B…/dconf/remotix.d`).
- Aggiungere: `journalctl -b -g 'avc:'` (rifiuti SELinux), `sudo ausearch -m avc,user_avc,selinux_err -ts <ora>`, `prove/wall-selinux.sh` (prova negativa del muro) e `prove/wall-sesearch.sh`; `prove/hold.py` / `hold-user.py` (aiutanti di banco che tengono aperta una sessione).
- Il remedy «reinstall» in `RX-KDE-00x` va letto come `dnf reinstall` (T6).
- Vale: `--verbose`, `--encoding-test`, `GET /fingerprint`, modalità diagnostica della pagina (`?logbook`), procedura «reading a defect report».

---

# ch17_testing.py — «Testing» (10 sezioni)

### 17.1 What a check is and how it decides — DA CORREGGERE
- Le regole (tre verdetti, niente di condiviso, ogni attesa ha scadenza, utenti propri, verdetti dall'applicazione) valgono (lib.py quasi identico: solo `PORTS`, lib.py:40).
- Da correggere: «installs the package in a box (a container, or one of the four VMs)» → solo le quattro VM più la `costruzione`; la figura «Box (container or bench VM) … installed from the .deb» → «VM Fedora … installed from the .rpm»; tolti «podman with root access» e le porte 8821–8824 (restano 8851–8854, lib.py:40).
- Prefissi degli utenti: la lista di tredici prefissi (`bc lc mu rs ac cb bn dk dkf md in ph pl`) e `lib.sweep()` (lib.py:206) NON contengono i prefissi dei controlli nati su Fedora: `kx` (check-exit, check-kde-exit), `kr` (check-kde-live, check-kde-resize, check-resize), `kb` (check-kde-birth); `pl3` usato da check-prelocal. Da ricontare con `grep -n 'Rig(\|"[a-z][a-z][0-9]"' prove/check-*.py`.
- Nota «Where they run»: i pacchetti del server per le VM sono quelli di `server/prepara-server.sh` (`qemu-system-x86 qemu-utils ovmf gdisk dosfstools rsync attr btrfs-progs erofs-utils acl`, righe ~33-36): NON `genisoimage xorriso`; il server resta Debian 13 con rootfs in RAM, niente podman.
- Aggiungere: SELinux enforcing è lo stato normale delle VM (PIANO.md, regole di studio).
- «Nothing in this chapter was run while writing the manual»: vero anche per Fedora; i risultati vanno da PIANO.md e registro (vedi 17.10).

### 17.2 The files of prove/ — DA CORREGGERE
Righe da modificare nella tabella:
- `lib.py`: porte 8851–8854 (non 8821/8841); `Box` non usa più `boxes/` ma `banco-vm/box.sh` con `RX_BANCO=vm`.
- `package-snap.py`: ancora dpkg/AppArmor (package-snap.py:9, 106-108, 177): non adattato; cita snapd/cloud-init di Ubuntu.
- `check-package.py`: ancora apt/deb (T5); la riga «NOT part of all.sh» resta vera.
- `check-desktop.py`: due ritocchi Fedora: pannello LXQt da `/etc/xdg/lxqt/panel.conf` se manca `/usr/share/lxqt/panel.conf` (check-desktop.py:433, 488); per KDE una finestra rimpicciolita da KWin passa se resta dentro l'immagine ed è almeno metà (834-842).
- `check-prelocal.py`: ora 8 casi (P1–P8; P7 terminale con `top`, P8 editor con testo non salvato; `--only`; P6 su Fedora controlla che la riga del gancio sia PRIMA di `pam_selinux open` in ogni file PAM delle schermate di accesso, check-prelocal.py:551-566; il docstring in testa dice ancora `common-session`).
- `fresh.sh`, `banco-vm/fresh-vm.sh`: ancora Ubuntu (T5). `banco-vm/box.sh`: `install <de> <x.rpm>`.
- Righe NUOVE: `check-exit.py` (XFCE/LXQt: terminate-session, restart, close-and-wait), `check-kde-exit.py` (idem su KDE), `check-kde-birth.py` (KWin ricorda l'ultima misura, F8), `check-kde-live.py`, `check-kde-resize.py`, `check-resize.py` (riattacchi con misure diverse, 10 giri), `giro-selinux.sh`, `giro-xfce-radeon.sh`, `giro-lxqt-radeon.sh`, `prelocal.sh` (login locale vero su lightdm/sddm), `banco-vm/autologin-lightdm.sh`, `banco-vm/autologin-sddm.sh`, `wall-selinux.sh`, `wall-sesearch.sh`, `wall-neg-domain.py`, `hold.py`, `hold-user.py`. Nessuno è in `all.sh`.
- `headless-multi.sh`, `lifecycle-window.py`: nessun chiamante (come Ubuntu).
- La cartella dei log: `/media/REMOTIX-FEDORA/…` (non `/media/REMOTIX-UBUNTU/albero/prove/log/`): il percorso esatto delle uscite dei giri Fedora è NON VERIFICATO (`prelocal.sh` usa `/media/REMOTIX-FEDORA/tmp/prove-run/prove`).

### 17.3 The checks of all.sh and what each proves — DA CORREGGERE
Elenco dei check e nomi dei verdetti invariati (`check-base.py` NAMES identico, check-desktop idem salvo una condizione). Da correggere:
- `check-prelocal.py` (900 s di limite in all.sh): ora ha 8 nomi; all.sh lo lancia senza `--only` (all.sh:74), quindi P7/P8 (circa 3 minuti l'uno, richiedono il display manager della VM) entrano nel giro: se rientrino nei 900 s (1800 con RX_TEMPO=2): non verificato.
- Riga `P6`: sostituire `common-session` con «i file PAM delle schermate di accesso (gdm-*, plasmalogin*, lightdm*, sddm*)».
- «125 verdict rows»: da ricontare con i tuple `NAMES` (script nel report di Ubuntu; qui `python3 - <<…` che importi `NAMES` da ogni `check-*.py`), perché prelocal passa da 6 a 8 e `check-phone`/`check-input` vanno riletti.
- `power-entries-absent`: «15 login1 actions» → 19 (il commento nella tabella dice «refuses the 15»; `src/remotix-no-poweroff.rules` ne ha 19: `grep -c '"org\.' …` → 19). I due controlli di Ubuntu `power-implied` e `power-local-seat` vanno sulla policy di Fedora: PASS/FAIL su Fedora: non verificato (non ci sono log nel registro).
- «users-shell-and-environment»: su GNOME in Fedora il terminale è `ptyxis` (check-prelocal.py `TERMINALS`, 'Fedora 45 Workstation has Ptyxis'); `sudo-rs` è di Ubuntu (check-desktop.py:309): su Fedora `sudo` è quello GNU. Il FAIL noto di GNOME `pkexec` (SHELL vuoto) c'è anche su Fedora (PIANO.md: «FAIL pkexec noto»).
- La frase su `check-ban.py` e `127.0.0.1`/`10.0.2.2`: invariata per le VM.
- La riga SKIP `prelocal/real-greeter` dice «(GDM/SDDM/LightDM)»: aggiungere plasmalogin (all.sh:77); la prova vera si fa a mano da chiavetta (PIANO.md, 25 nov).
- Controlli dei FAIL già noti senza il muro SELinux (registro F29): `two-users`, `three-users`, `tap-click-portrait` (poi chiusi da g6: «two/three-users e phone ora PASS», PIANO.md); `check-kde-live` «Chromium GONE» (banco, non prodotto).
- «The two checks added on 20 Nov 2026» (power-implied, power-local-seat con `unione10/11` e VM Ubuntu): da TOGLIERE come storia di Ubuntu; la descrizione dei due controlli può restare.

### 17.4 Running the suite — DA RISCRIVERE
- Tutti i percorsi `/media/REMOTIX-UBUNTU/albero/prove` → `/media/REMOTIX-FEDORA/…` (il percorso esatto della copia dell'albero sul server: non verificato). Niente più banco a contenitori né `RX_BANCO` come scelta: sulle VM è `RX_BANCO=vm`.
- `all.sh --fresh <deb>` e `--clean`: su Fedora NON funzionano (fresh.sh e `banco-vm/fresh-vm.sh` usano apt e `.deb`, T5). La procedura reale: VM accesa con `server/vm-radeon.sh accendi <de>` (Radeon) o `… virtuale`, pacchetto con `banco-vm/box.sh install <de> <x.rpm>`, firewall (F20), poi `prove/giro-selinux.sh <de> [--extra]` (giro-selinux.sh:1-37) e `giro-xfce-radeon.sh` / `giro-lxqt-radeon.sh`, oppure un controllo alla volta con `RX_BANCO=vm python3 check-<x>.py --box <de>`.
- Il limite complessivo «17,860 s» e l'esito 0/1/2/3 di `all.sh` valgono (all.sh invariato); il «47 min» è di Ubuntu: da togliere.
- La nota «No layout difference» (fresh.sh/boxes): da togliere (non c'è `boxes/`).
- Aggiungere: l'ordine dei desktop (uno alla volta, una sola Radeon), la regola «le prove le decide il proprietario» (memoria `feedback-user-decides-tests`), e che i giri su macchina vera (chiavetta) sono a mano.

### 17.5 The package check — DA RISCRIVERE
`check-package.py` è ancora quello di Ubuntu (apt, dpkg, `pam-auth-update`, AppArmor, `.deb`): non applicabile e MAI eseguito su Fedora. Cosa si può dire di vero:
- I controlli del pacchetto Fedora sono due: quelli di `build/build-rpm.sh` (R13 e R4, vedi ch18) e le prove a mano/da script su VM (registro F18, F19, F21, F24: installazione, aggiornamento, rimozione «byte per byte» del blocco PAM di sddm, rimozione con cartella rimasta, reinstallazione da zero, riavvio con il modulo).
- Non esistono su Fedora `apparmor` (sostituito dalla prova negativa `prove/wall-selinux.sh`: 25/25 sui quattro desktop, PIANO.md s13/s15), `purge`, `reinstall` automatici.
- Il «Warning: not aligned with the new postinst» (dconf) non serve più; sostituirlo con «`check-package.py` non adattato a rpm».
- Proposta per il revisore: o togliere la sezione e spostare i fatti in «Package» (ch15), o scrivere «strumento ereditato, non usato su Fedora».

### 17.6 The four test boxes — DA TOGLIERE
`fedora45/` non ha `boxes/`; la regola del proprietario è «niente contenitori, niente podman» (CLAUDE.md di fedora45, memoria `remotix-vm-test-bench`). La sezione descrive i contenitori `rxu-*`, `box.sh`, `Containerfile`, `set-dm.sh`, `power.sh`, `box-identity.sh`: tutto da togliere. Rimandi da sistemare: `rif("The four test boxes")` è usato da ch17 (S3, S1 una volta) (vedi (c)).

### 17.7 The real-system virtual machine — DA TOGLIERE
`server/vm.sh` (immagine cloud Ubuntu, `virtio-vga`, cloud-init, porta 2301/8901) e `vm-login-test.py` non esistono in `fedora45/server/` (`diff -rq ubuntu26.04/server fedora45/server`). Contenuto utile da portare nella sezione VM bench: la VM `virtio-vga` ha il render node ma non codifica (vale ancora per `accendi <nome> virtuale`).

### 17.8 The VM bench — DA RISCRIVERE
Struttura valida (quattro VM + una per la build, una sola Radeon, snapshot), contenuto Fedora (server/vm-radeon.sh, 496 righe; banco-vm/box.sh):
- Macchine: `gnome`, `kde`, `xfce`, `lxqt` (ssh 2351–2354, REMOTIX 8851–8854) e `costruzione` (ssh 2355, solo virtuale, 8 CPU, 6G, ISO Xfce Live, senza porta REMOTIX: vm-radeon.sh:40-41). ISO: Fedora Live 45-1.4 in `/media/DOWNLOAD` (`Fedora-Xfce-Live-45-1.4.x86_64.iso`, vm-radeon.sh:41; per gli altri nomi: non verificato, la tabella `case` è alle righe 36-48).
- `crea`: il disco è costruito dal contenuto della ISO Live «come fa il payload live-image di Anaconda» (rsync, BLS, grub2-editenv, `kernel-install`, relabel SELinux al primo boot: vm-radeon.sh:9, 152-164, 309-312, 340); NON autoinstall e NON squashfs di casper. Il disco è btrfs (`btrfs subvolume create root/home`, riga 195).
- Risorse: 4 CPU, 5G di RAM, disco 40G (vm-radeon.sh:~31: `CPUS=4 MEM=5G DISKSZ=40G`), non 8 CPU/12 GB; OVMF `OVMF_CODE_4M.fd`.
- Comandi: gli stessi di Ubuntu più `accendi <nome> virtuale`, `schermo`, `tasti`, `scrivi` (vm-radeon.sh:4-7); `istantanea` e `ripristina` (il ripristino SCARTA lo stato corrente, nessun `prima-<data>` automatico: vm-radeon.sh:14: da verificare nel codice, non verificato).
- Istantanee Fedora: `pulito`, `codec` (RPM Fusion; da cui partono i test, fedora45/CLAUDE.md), `consegna-<de>`, `dopo-prove-proprietario`, `finale-<de>`, `consegna-finale-<de>`, `selinux-<de>`/`selinux2-<de>`, `kde-i1-provato`, `kde-i2-provato` (PIANO.md). Cifre degli ISO e dei kernel: non verificate.
- Script attorno: NON esistono `vm-radeon-installa.sh`, `vm-radeon-aggiorna.sh`, `vm-radeon-controllo.sh`, `vm-radeon-login-test.py`. Esistono: `server/live-installa.sh` (334 righe: installa i codec da RPM Fusion, `dnf install` dell'rpm, firewalld a runtime, `systemctl enable --now remotix`, due utenti di prova; per macchine vere avviate da chiavetta Live; ATTENZIONE: `PACCHETTO=remotix-1.0.1-1.fc45.x86_64.rpm` in testa, da aggiornare a 1.2.0), `server/prepara-server.sh` (90 righe, rimette sul server in RAM solo ciò che serve alle VM), `prove/banco-vm/box.sh` (verbi `ssh rootkey install status reset`; `install` con `rpm -U --nosignature --replacepkgs`), `autologin-lightdm.sh`, `autologin-sddm.sh`.
- Il giro «adattato» (`RX_BANCO=vm`, `RX_TEMPO=2`, note e SKIP): vale per i primi due; `fresh-vm.sh` non va (T5).
- «The round of the release package on the GNOME machine» (unione10, 47 min, `vm-gnome-unione10`): DA TOGLIERE. Sostituire con i giri Fedora di PIANO.md: h1 in enforcing, gnome 52 PASS (+ all.sh 39 PASS), kde 76/78, xfce 60, lxqt 60, prova negativa 25/25 (23 nov); poi i2 su KDE (P1–P8 PASS, 25 nov). I log: «non verificato» (non letti).
- «What was done by hand on real machines»: DA RISCRIVERE con le prove del proprietario del 22–23 nov (quattro desktop provati con l1/`l6`, poi h1) e del 25 nov da chiavetta (live Fedora 45 con Intel + Radeon, pacchetto h1/i1/i2, `live-installa.sh`): GNOME OK, XFCE OK, LXQt OK, KDE prima NON superata (F36) poi OK con i2. Registri nel tablet: `~/remotix-prove-live/fedora45-*-25nov*` (non letti).
- Snapshot UEFI: invariato.

### 17.9 What only a real machine or a real phone can prove — DA CORREGGERE
- Riga «AppArmor in enforce mode» → «SELinux»: su Fedora il muro è in enforcing e provato (F24: 0 AVC nostri sui quattro desktop, prova negativa 25/25). Non provato (da PIANO.md 22 nov e F24): accesso locale vero da gdm/plasmalogin col muro e riavvio VM col modulo; quest'ultimo poi fatto. Riga da riscrivere.
- Riga «A real graphical login at the machine»: oggi provato a mano su macchina vera da chiavetta sui quattro desktop (PIANO.md 25 nov: GNOME, XFCE, LXQt OK con h1, KDE OK con i2); resta non automatizzabile (all.sh SKIP).
- Riga «The first touch on GNOME»: su Fedora è il difetto di mutter 51 del primo movimento assoluto a coordinata 0 (F34); cura in `input.c` (primo movimento inviato due volte); `two-users/three-users/tap-click-portrait` PASS dopo g6. Differenza con Ubuntu/Debian dichiarata in F34.
- Riga «NVIDIA and Intel»: su Fedora la codifica è riuscita sulla Intel della macchina vera (PIANO.md 25 nov); NVIDIA non provata.
- Riga «snap and Flutter»: da TOGLIERE (Fedora non ha snap); i programmi Flatpak «partono senza nulla di speciale» solo da studio (PIANO.md «Che cosa regge già»), nessun controllo: non verificato.
- Riga «The removal and the purge of the package»: riscrivere (RPM: nessun purge; rimozione e aggiornamento provati su VM, F21/F24).
- Nuove righe: lingua non-C (AccountsService senza codifica, `it_IT`: «da provare», PIANO.md); utenti SELinux confinati provati su GNOME/XFCE/KDE (F25), XFCE+`staff_u` pannello non parte (F30, non nostro).
- Vale: telefono vero, canvas oltre 3840x2160, reti vere, tastiere vere, carichi veri.
- «The lesson of the containers»: riformulare (C4/C5 sono di Ubuntu); la lezione generale (un banco che non gira la protezione non può mostrarne il difetto) è confermata da F36: il banco non vedeva il guasto di KDE perché `check-prelocal.py` apriva un desktop vuoto.

### 17.10 What was verified on Ubuntu 26.04, and what was not — DA RISCRIVERE
Tutta la sezione è la storia di Ubuntu (unione1…unione11, giri 18 nov su contenitori, primo accesso su live Ubuntu 26.04.1). Va sostituita con «What was verified on Fedora 45». Fonti: `PIANO.md` (diario fino al 25 nov), `docs/REGISTRO-problemi.md` F1–F36. Contenuti da riassumere (cifre da `PIANO.md`, NON ricontate):
- Pacchetti di prova in sequenza: p4f (GNOME), k4b (KDE), l6 (XFCE/LXQt), s8/s13/s15 (muro SELinux), f1, g6, h1 (finale dei quattro desktop, 23 nov), i1/i2 (KDE, 25 nov). Il pacchetto 1.2.0 (stesso codice di i2 con un altro numero): non verificato che sia stato ricostruito o riprovato.
- Giri: h1 in enforcing gnome 52 PASS (+ all.sh 39 PASS), kde 76, xfce 60, lxqt 60, prova negativa 0 FAIL, AVC nostri 0; i2 su KDE P1–P8 PASS.
- Prove a mano del proprietario con h1 sui quattro desktop (23 nov) e da chiavetta il 25 nov (vedi 17.8).
- Aperti (PIANO.md 23–25 nov): `prove/giro-selinux.sh` nasconde un controllo morto a metà (`check-kde-exit` «service restart», intermittente); commento a `child.c:1636`; lingua senza codifica; `fedora45/` non è in git; GNOME senza «ultima difesa» (F36); `catatonit`; rifiuto innocuo `search` su `/proc/sys/dev`; `force_guard_on` resta acceso dopo un login locale fallito (`session.c:5549`, PIANO.md cita `:8770`: numero di riga da riverificare).
- «Package checks of the build system» (R13/R4/R14/R23/R24): per Fedora vedi ch18.
- I checks non eseguiti o non aggiornati: `check-package.py`; `power-implied`/`power-local-seat` su Fedora.

---

# ch18_build.py — «Build and release» (8 sezioni)

### 18.1 The build of the .deb in one container — DA RISCRIVERE
Per Fedora: nessun contenitore, nessun podman. `build/build-rpm.sh [etichetta]` (107 righe) copia l'albero sulla VM `costruzione` (ssh 2355, via server `nicfio@192.168.0.2`, chiave `…/costruzione/vmkey`), vi installa le dipendenze (`dnf -y install cmake ninja-build git gcc-c++ rpm-build selinux-policy-devel` + `dnf builddep` dallo spec), costruisce ngtcp2/nghttp3 statici, esegue `rpmbuild -bb`, controlla R13 e R4, riporta l'rpm e i log in `/media/REMOTIX-FEDORA/pacchetti/<etichetta>/` (rifiuta di sovrascrivere). Figura «BUILD» e la tabella «The pieces» da rifare: `build/build-rpm.sh`, `build/quic-static.sh`, `rpm/remotix.spec`, `src/Makefile`; spariscono `build/Containerfile`, `labwc-ospite/`, `debian/control`, `debian/rules`. Versioni del toolchain («gcc 15.2.0, debhelper…») sono di Ubuntu: da ricontare dal `controlli.txt`/`rpmbuild.log` sulla VM (non letto). La VM deve essere accesa a mano (lo script non la accende: `vm-radeon.sh accendi costruzione virtuale`).

### 18.2 The build image and the static QUIC libraries — DA CORREGGERE
- Non c'è immagine: le librerie statiche si costruiscono sulla VM una volta (`quic-static.sh`, saltato se già presenti: build-rpm.sh passo 3).
- `build/quic-static.sh`: stessa ricetta di Ubuntu (ngtcp2 v1.25.0, nghttp3 v1.18.0, statico, `libdir=lib`, controllo finale che non ci siano `.so`); l'intestazione dice che il ngtcp2 di Fedora è 1.22.1, troppo vecchio (quic-static.sh:3-4). Le cifre di Ubuntu «ngtcp2 1.16.0 / nghttp3 1.12.0» vanno tolte; la versione di nghttp3 in Fedora: non verificato.
- OpenSSL: `openssl-devel` di Fedora (4.0), D8; minimo 3.5.0 in `MINIMI` (Makefile:424). La frase «Ubuntu 26.04 has 3.5.5» → versione di Fedora ricavata da `make deps` sulla VM: non verificata.
- «The versions are written in four places» → su Fedora: i default di `quic-static.sh`, i due `test` in `%build` (spec:124-125), `Provides: bundled()` (spec:97-98), `MINIMI` (Makefile:425). Le tre del labwc spariscono.
- Pinning: ngtcp2/nghttp3 con tag, non per hash (invariato). labwc/wlroots: non più.
- Il Warning sulla rete (GitHub, gitlab, archivi Ubuntu) → GitHub (clone dei due tag) e repository Fedora per `dnf`.

### 18.3 What build-deb.sh does, step by step — DA RISCRIVERE
`build-deb.sh` non esiste in `fedora45/build/`. Passi di `build-rpm.sh` (righe 1-107): (1) copia di `src/`, `rpm/`, `LICENSE.md`, `THIRD-PARTY-LICENSES`, `selinux/` in un tar, rimuove i residui di una compilazione locale; (2) dipendenze con dnf; (3) ngtcp2/nghttp3 statici; (4) `rpmbuild -bb`; (5) controlli R13 e R4 sull'rpm (`rpm2cpio`, `strings`, `ldd`), scrive `controlli.txt` con `Requires`, `Recommends`, `Provides`, `Files`; se una riga R13/R4 manca o dice NO, il pacchetto non viene riportato; (6) riporta rpm e log. Variabili: `RX_SERVER` (default `nicfio@192.168.0.2`), `RX_GUEST_PORT` (2355); non esistono `OUTPUT`, `WORK`, `IMAGE`, `RX_VERSION`, `RX_REVISION`, `SOURCE_DATE_EPOCH`, `TWICE`. Non esistono lintian né rpmlint, né R14, né R23, né l'archivio dei sorgenti labwc. Tabella delle variabili e dell'ordine: tutta da riscrivere. Uscita: 1 se un controllo dice NO, 2 per errori di uso o VM spenta.

### 18.4 src/Makefile: sources, libraries, minimum versions — DA CORREGGERE
- Il testo è generato da `src/Makefile` (le liste `SORGENTI`, `PROTOCOLLI`, `MINIMI` si leggono dal file: se `build.py` punta a `fedora45/` i numeri sono automatici, da riverificare con `build.py --check`). Differenza reale con Ubuntu: `PROTOCOLLI` ha due voci in più, `kde-output-device-v2` e `kde-output-management-v2` (Makefile:291-298; XML fissati in `src/protocols/`, README `README-kde-output.txt`: copia non modificata da plasma-wayland-protocols, commit cd65734…, perché il pacchetto Fedora 1.23.0 non li porta); `SORGENTI`: nessun file nuovo (`diff` del Makefile mostra solo protocolli e `-lselinux`).
- Tabella «libraries»: aggiungere `-lselinux` (Makefile:322) e dirlo (per `child.c`, `walls.c`).
- Riga «LABWC»: il #define esiste ancora ma il pacchetto non lo imposta e il codice è morto (T2).
- «`debian/rules` runs `make deps` first» → `%build` (spec:122-123: `make -C src deps TWIN=none`); `TWIN=none` anche nello spec (spec:123, 130).
- `libselinux-devel` è nei BuildRequires (spec:48) ma `make deps` non controlla libselinux (MINIMI non la elenca): non verificato che il Makefile fallisca con un messaggio chiaro se manca.
- Il resto vale: `CFLAGS`, `gnu11` (nello spec: `make … CFLAGS="%{optflags} -std=gnu11 -Wall -Wextra -Wno-unused-parameter" LDFLAGS="%{build_ldflags}"`, spec:131), `.flags`, bench, `DEPS_PREFIX`, `TWIN`, `fingerprints`.
- La riga «MINIMI»: stessi minimi; valore reale dei moduli sulla VM di Fedora: non verificato.

### 18.5 debian/rules: the overrides and the guards — DA RISCRIVERE
Sostituire con «`rpm/remotix.spec`: %build e %install». Corrispondenze: `R_CFLAGS` → `%{optflags}` + `-std=gnu11` (gcc 15 avrebbe default gnu23: lo dice il commento spec:128-130); `override_dh_auto_configure` → `make -C src deps TWIN=none`; guardie R24 e R13 nello `%build` (spec:124-126); `override_dh_auto_build` → `make -C src all …` e, in più, il modulo SELinux (`make -C selinux -f /usr/share/selinux/devel/Makefile remotix.pp` + `bzip2 -9`, spec:132-134); `override_dh_auto_install` → `%install` (spec:135-165); `%{rxlibexec}` = `%{_libexecdir}/remotix`. Sparisce tutta la parte labwc/meson/`--wrap-mode=nodownload`, `hardening=+all` (su Fedora i flag di hardening sono quelli di `%{optflags}`/`%{build_ldflags}`), `override_dh_installsystemd`, `execute_after_dh_auto_install` e il drop-in needrestart come riga `.install` (ora `install -D … %{SOURCE7}`, spec:162-163). `debug_package` spento (spec:14).

### 18.6 The package checks R4, R13, R14, R23 and R24 — DA RISCRIVERE
Su Fedora esistono:
- R13: due livelli come su Debian: nello `%build` la riga `#define BENCH_ON 0` in `rcp.c` (spec:126); su rpm finito `strings | grep -c 'the BENCH FUNCTION is ON'` (build-rpm.sh, blocco «checks»). Manca il controllo positivo (rcp.o con BENCH_ON=1) e il controllo che l'unità non passi opzioni di bench: non verificato che esista altrove.
- R4: solo `ldd` del server (nessuna libreria mancante, niente ngtcp2/nghttp3 dinamici); NIENTE `ldd-labwc`.
- R24: i due `test` di `pkg-config --modversion` (spec:124-125).
- NON esistono su Fedora: R14 (nessun file di bench/test nel pacchetto), R23 (riproducibilità con `TWICE=1`), `labwc-source`, lintian/rpmlint. La sezione «What was recorded» (33 librerie, 59 voci, 1.456.680 byte del labwc, 3.707.960 byte del server, lintian 0/0) è di Ubuntu: da togliere; per Fedora le cifre vanno ricavate da `controlli.txt` di un pacchetto costruito (es. `/media/REMOTIX-FEDORA/pacchetti/<etichetta>/controlli.txt`): non letto, «non verificato». Il warning su `SOURCE_DATE_EPOCH` non ha senso senza R23.
- I label R4/R13/R14/R23/R24 restano «requisiti del lavoro di impacchettamento di prima»: dire quali sono attivi.

### 18.7 Version and release — DA RISCRIVERE
- La versione sta in `rpm/remotix.spec:24` (`Version: 1.2.0`), `Release: 1%{?dist}`; file `remotix-1.2.0-1.fc45.x86_64.rpm`. NON esistono `RX_VERSION`, `RX_REVISION`, `~dev`, `+ubuntu26.04`, `debian/changelog`: la storia è nel `%changelog` dello spec (spec:496-502; ultima voce 25 nov 2026, «First release for Fedora 45… KDE: a local login closes the remote desktop also when a program does not close by itself»).
- La copertina: `manuals/sources/build.py` deve leggere la versione da `rpm/remotix.spec` (piano manuali, passo 2, PIANO.md): da verificare in `fedora45/manuals/sources/build.py` (non letto: non verificato).
- Comando di build: `build/build-rpm.sh <etichetta>` (non `RX_VERSION=… build-deb.sh`).
- «What release means»: nessuno script di rilascio, firma, repository; il pacchetto non è firmato (installazione con `rpm -U --nosignature` nel banco). Sito e rilascio solo su ordine del proprietario (PIANO.md). Il pacchetto 1.2.0 non è ancora ricostruito: non verificato (piano manuali, passo 4).
- Licenza: la nota «a release has two files to publish» (sorgente di labwc, GPL-2) NON vale per Fedora: il labwc di Fedora è un pacchetto della distribuzione, non nostro. `LICENSE.md:95-97` lo dice ancora al contrario (T6).
- Debian 13 ha il suo manuale e il suffisso `+deb13`: la frase finale va riscritta per Fedora (`.fc45`).

### 18.8 Generated and vendored inputs — DA CORREGGERE
- `opus.wasm` e `build.sh` di `src/opus-wasm/`, `vulkanvideo_rgb_nv12_spv.h`: identici a Ubuntu (`diff -rq` non li elenca); le frasi valgono; la verifica `sh src/opus-wasm/build.sh --verify` non eseguita («not run»: resta vero).
- `src/protocols/*.xml`: aggiungere i due XML di KDE fissati (commit e motivo in `README-kde-output.txt`; licenza MIT-CMU nella `THIRD-PARTY-LICENSES`).
- Riga labwc/wlroots/patch: DA TOGLIERE (niente `build/labwc-ospite/`, spec:4).
- La mancanza dello script del shader (`benches/19-vulkan/19-shader.sh`) resta vera.
- La nota «See Extending REMOTIX and porting…» vale (rif a ch20, vedi (c)).

---

# Elenchi richiesti

## (a) Cose che esistono solo su Fedora e meritano una sezione NUOVA
Nel capitolo indicato:
1. ch15 «The SELinux module» (sostituisce «The AppArmor profile» dentro 15.5, o sezione propria): tre domini, `selinux/remotix.fc:1-8` (tipi dei file), niente tipo di porta proprio (te:~33-37), `%selinux_*` nello spec, `restorecon`, comando di ripiego `semodule -X 200 -i`, nessun `permissive`/`dontaudit` nostro (te:36), regola `stop/status` su `xdm_unit_file_t` (te:214, F36), utenti confinati (F25), lato root largo (F27), rifiuti non nostri (F28, F30). Fonte: F24–F28, F31–F33.
2. ch15 «The local-login hook on four login screens» (rimanda al capitolo del login, ch13, ma pacchetto/trigger vanno in ch15): `remotix-pam-hook` apply/check/remove/prepare, trigger `gdm`, `lightdm`, `sddm`, `plasma-login-manager` (spec:433-464), perché non `authselect`, perché sddm si modifica sul posto (F21), `ExecStartPre … check`.
3. ch15 «Requirements» / «Firewall and codecs»: codec da RPM Fusion (D1: `mesa-va-drivers-freeworld`), firewalld (`remotix.firewalld.xml`, riga F20, `%firewalld_reload`), SELinux enforcing, orologio del dispositivo client giusto (F23, piano manuali).
4. ch15 «The PAM service file on Fedora» (`src/remotix.pam`): `password-auth`, `postlogin`, `pam_selinux` ×2, `pam_loginuid`, `pam_namespace`, `pam_env` ×2 (la seconda su `/etc/locale.conf`), nessun portachiavi (D6), `pam_listfile` per root (src/remotix.pam:33-72).
5. ch15 «KDE with KWin alone» (sostituisce 15.6): `--kwin-virtual`, `REMOTIX_KDE_HOST=1`, `kde-output-management-v2`, misura di nascita corretta prima dello stream (F8), `graphical-session.target` (F36), attesa 5 s.
6. ch16 «Lines new on Fedora» (nella sezione startup): SELinux 44–47, `KDE: SESSION REFUSED`, `KDE: KWin's output is not ready yet`, `KWin alone: the output is`, `connection … closed — the PEER closed it` (F23), righe della chiusura KDE (session.c:5635-5648), riga SELinux dei muri (walls.c:340).
7. ch16 «Reading the SELinux denials» in «Diagnostic instruments»: `journalctl -b -g 'avc:'`, `ausearch`, `prove/wall-selinux.sh`.
8. ch17 «The VM bench for Fedora»: costruzione, `virtuale`, `schermo/tasti/scrivi`, ISO Live, relabel (17.8 sopra).
9. ch17 «The Fedora-only checks»: `check-exit`, `check-kde-*`, `check-resize`, `check-prelocal` P7/P8, `giro-*`, `wall-*`, `prelocal.sh`, `autologin-*.sh`, `hold*.py` — con a fianco il fatto che NON sono in `all.sh`.
10. ch17 «Testing the real machine from a live USB» (`server/live-installa.sh`, prova «il locale chiude il remoto», PIANO.md 25 nov).
11. ch18 «The RPM build on the build VM» (build-rpm.sh), «Scriptlets and macros» (`%selinux_*`, `%firewalld_reload`, `%systemd_*`, `%triggerprein`), «Weak dependencies and `bundled()`».

## (b) Cose di Debian/Ubuntu da togliere
`apt`, `dpkg`, `.deb`, `debhelper`/`dh_*`, `lintian`, `Static-Built-Using`, `universe`, `libpam-runtime`/`pam-auth-update`/`common-session`, `ufw`, `AppArmor` e `dh_apparmor`, `remotix_network`, `snap`, `ubuntu:26.04`, `resolute`, `+ubuntu26.04`, `1.0.1~dev`, `debian/*`, `build-deb.sh`, `RX_VERSION`/`RX_REVISION`/`TWICE`/R14/R23/labwc-source, `labwc-ospite`, `boxes/`, contenitori/podman, `server/vm.sh`, `vm-radeon-installa|aggiorna|controllo.sh`, `vm-login-test.py`, `unione1…11`, `docs/STORIA-ubuntu-26.04.md` (c'è in `fedora45/docs/` ma è la storia di Ubuntu: non citarlo come fonte Fedora, 16 occorrenze nei quattro capitoli), `studio/7-xubuntu-lubuntu.md`, `studio/8-pacchetto-e-prove.md`, `studio/14-canvas-xfce.md` (non esistono in `fedora45/studio/`), `/media/REMOTIX-UBUNTU/…`, snap/Flutter, sudo-rs, ISO Ubuntu/Kubuntu/Xubuntu/Lubuntu, kernel 7.0.0-xx, 8 CPU/12 GB delle VM Ubuntu, uid 972.
Anche dai SORGENTI del prodotto (da decidere con il proprietario, T6): messaggi con `apt install --reinstall`, `--no-install-recommends`, «Install the file of the family … .fedora, .suse, .arch», commenti sul riavvio che lascia vivi i desktop, `LICENSE.md:95-97`.

## (c) Rimandi `rif("…")` che si romperebbero se cambia un titolo
Conteggio dei rimandi che puntano ai titoli dei miei capitoli (da tutti i `ch*.py` di Ubuntu; il generatore risolve per titolo esatto):
- Titoli di sezione: «Files the package installs» (ch13 ×2, ch14 ×2, ch16 ×1, ch17 ×1), «Our own labwc (KDE)» (ch12, ch14, ch15 ×2, ch16, ch18 ×3: se la sezione viene tolta o rinominata, rompe 9 rimandi), «Removal: prerm, postrm and purge» (ch12, ch14, ch16), «The postinst: user, folders and encoding test» (ch15 ×2, ch18), «Package metadata: Depends and Recommends» (ch18), «Service policy: installed disabled» (ch15), «The startup declarations» (ch15 ×4, ch16, ch17 ×2), «Where the log lines go» (ch12, ch16), «Anatomy of a log line», «Log areas», «Whose line it is» (×2), «The systemd journal output» (×2), «Journal priorities and the rule of the head mark» (×2), «What never enters the log», «Environment variables read by the product» (tutti ch16), «The checks of all.sh and what each proves» (ch15, ch17 ×2), «Running the suite» (ch17), «The package check» (ch15 ×2, ch17 ×2), «The four test boxes» (ch17: la sezione va tolta, ma il rimando c'è), «The VM bench» (ch15, ch17 ×6, ch19, ch20 ×2), «What only a real machine or a real phone can prove» (ch15, ch17), «What was verified on Ubuntu 26.04, and what was not» (ch17 ×4: il titolo contiene «Ubuntu 26.04», va cambiato, quindi vanno cambiati anche i 4 rimandi), «What build-deb.sh does, step by step» (ch15; titolo con `build-deb.sh`), «debian/rules: the overrides and the guards» (ch15; titolo con `debian/rules`), «The package checks R4, R13, R14, R23 and R24» (ch17), «Version and release» (ch15, ch18).
- Titoli di capitolo usati nei rimandi: «The package» (9 file), «Logging and diagnostics» (7), «Testing» (11), «Build and release» (5).
- Rimandi in uscita dai miei capitoli verso titoli di altri gruppi (se G1–G3/G5 li cambiano si rompono): «The local-login hold» ×6, «Security model» ×4, «Stopping the service» ×4, «Appendix C — Known issues and open points» ×3, «Login and its defences» ×3, «Startup and life cycle», «The RCP/1 protocol», «Desktops found again after a restart», «The browser page», «Performance and capacity», «Extending REMOTIX and porting to another distribution».
- Titoli che il piano suggerisce di cambiare: 15.1 («…how it is built»: ok), 15.6 (togliere), 17.6, 17.7 (togliere), 17.10 («Ubuntu 26.04»), 18.1 («.deb»), 18.3 («build-deb.sh»), 18.5 («debian/rules»), 15.3/15.4/15.7 («preinst», «postinst», «prerm, postrm and purge» → `%pre`, `%post`, `%preun/%postun`). Con titoli nuovi vanno aggiornati TUTTI i rimandi elencati sopra, nei capitoli di tutti i gruppi.

## Punti non verificati (riassunto)
Vedi la risposta finale.
