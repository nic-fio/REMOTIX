# Studio 8 — Pacchetto per Ubuntu 26.04 e macchine di prova dei quattro gusti (18 nov 2026)

Solo studio: nulla è stato costruito, nessuna immagine di prova creata. I fatti su Ubuntu 26.04 vengono da un contenitore
usa-e-getta `studio-8` (immagine `ubuntu:26.04`, risulta «Ubuntu 26.04.1 LTS», suite `resolute`, archivi `archive.ubuntu.com`,
componenti main universe restricted multiverse) sul server; più quattro «chroot» in `/root/r-<gusto>` dentro quel contenitore, nei
quali ho installato davvero i quattro metapacchetti (solo per misurarli e leggerne i file; non sono immagini di prova). Le uscite
lunghe sono in `/media/REMOTIX-UBUNTU/studio/8/` (`sim-*.txt`, `sim2-*.txt`, `inst-*.log`, `inst-status.txt`, `misure.txt`).

Legenda: **[V]** verificato (dove) · **[W]** dal web · **[S]** supposizione.

---

## 1. Costruzione del pacchetto

### 1.1 Come è fatto oggi (Debian 13)

- `build/build-deb.sh` (151 righe): costruisce l'immagine `localhost/remotix-debian-build` da `build/Containerfile`, fa una COPIA dell'albero
  (`src/`, `debian/`, `THIRD-PARTY-LICENSES`; appende `LICENSE.md` a `debian/copyright`), scrive `debian/changelog`
  (righe 56-62: `remotix ($VERSION) trixie; urgency=medium`, riga di firma col maintainer), lancia `dpkg-buildpackage -b -us -uc` nel
  contenitore (`podman run --rm --userns=keep-id`, riga 76-80), poi `lintian -I --pedantic`, poi i controlli R13/R14/R4 (R23 con `TWICE=1`).
  Uscite in `$OUTPUT` (default `/media/REMOTIX-DEBIAN/pacchetti`, riga 35). `VERSION="$VERSION_UP-$REVISION+deb13"` (riga 52).
- `build/Containerfile:6-27`: base `debian:trixie`; `apt-get install --no-install-recommends` di build-essential, pkg-config, git, ca-certificates,
  cmake, ninja-build, libssl-dev, libpam0g-dev, libglib2.0-dev, libpipewire-0.3-dev, libdrm-dev, libva-dev, libopus-dev, zlib1g-dev, libei-dev,
  libxkbcommon-dev, libgbm-dev, libwayland-dev, libvulkan-dev; poi `quic-static.sh` (ngtcp2 v1.25.0 e nghttp3 v1.18.0 da GitHub, SOLO statici in
  `/usr/local/lib`); poi, ultimo strato: debhelper, dh-apparmor, dpkg-dev, fakeroot, lintian, binutils.
- `build/quic-static.sh` (75 righe): `git clone --depth 1 -b vX --recursive`, cmake+ninja, `-DENABLE_OPENSSL=ON`, poi controlla che non ci siano `.so`.
  Nessun nome di distribuzione: **vale così com'è su Ubuntu** (serve rete e git).
- `debian/rules:9-104`: `hardening=+all`, `buildflags.mk`, `R_CFLAGS` con `-std=gnu11`; `dh_auto_configure` = `make -C src deps TWIN=none`;
  `dh_auto_build` verifica `pkg-config --modversion libngtcp2 = 1.25.0` e `libnghttp3 = 1.18.0` (righe 36-37) e `BENCH_ON 0`; installa i file;
  `dh_apparmor --profile-name=remotix_network -premotix` (riga 97); `dh_installsystemd --no-enable --no-start --restart-after-upgrade` (riga 104).
- `src/Makefile:415-447`: `MINIMI := openssl:3.5.0 libva-drm:0 libngtcp2:1.25.0 libngtcp2_crypto_ossl:1.25.0 libnghttp3:1.18.0 libei-1.0:1.3.901
  libpipewire-0.3:0.3.48 gio-2.0:2.80 xkbcommon:0 libva:0 libdrm:0 gbm:0 wayland-client:0 opus:1.3 vulkan:1.3.274 zlib:1.2`; più la prova di
  compilazione di 15 header (ngtcp2, nghttp3, openssl/ssl.h, pam, gio, pipewire, drm_fourcc, va, gbm, opus, vulkan, zlib).

### 1.2 Tabella dei pacchetti: Debian 13 → Ubuntu 26.04 [V: `apt-cache policy/show` nel contenitore studio-8]

Per Debian 13 uso i numeri scritti nei commenti dell'albero Debian (`debian/control`, `build/Containerfile`); non ho avviato un contenitore
Debian (non richiesto): dove non sono citati sono **[S]**.

**Pacchetti di costruzione (Build-Depends e immagine)**

| Pacchetto | Ubuntu 26.04 | componente | minimo richiesto | esito |
|---|---|---|---|---|
| build-essential | 12.12ubuntu2.26.04.2 | main | – | uguale |
| pkgconf / pkg-config | 2.5.1-4 (entrambi) | main | – | uguale (`pkgconf \| pkg-config` soddisfatto) |
| git, ca-certificates, cmake | 2.53.0 / 20260816 / 4.2.3 | main | – | uguale (cmake 4.x con i CMakeLists di ngtcp2 1.25 e nghttp3 1.18: [S] nessun problema) |
| ninja-build | 1.13.2-1 | **universe** | – | in universe (nel contenitore di costruzione universe è già abilitato) |
| libssl-dev | 3.5.5-1ubuntu3.7 | main | `>= 3.5` (control:85), `openssl:3.5.0` | **OK**. L'API QUIC (`SSL_new_listener`, `SSL_set_quic_tls_cbs`) è nelle libssl di Ubuntu [V: `grep -a` su `libssl.so.3`] |
| libpam0g-dev | 1.7.0-5ubuntu3.2 | main | – | uguale |
| libglib2.0-dev | 2.88.0-1ubuntu0.1 | main | `>= 2.80` | OK |
| libpipewire-0.3-dev | 1.6.2-1ubuntu1.2 | main | 0.3.48 | OK |
| libdrm-dev | 2.4.131-1 | main | – | OK |
| libva-dev | 2.23.0-1ubuntu1 | **universe** | – | **universe** (su Debian è main) |
| libopus-dev | 1.6.1-1 | main | `opus >= 1.3` | OK |
| zlib1g-dev | 1:1.3.dfsg+really1.3.1-1ubuntu3.2 | main | 1.2 | OK |
| libei-dev | 1.5.0-3 | main | `>= 1.3.901` | OK |
| libxkbcommon-dev | 1.13.1-1 | main | – | OK |
| libgbm-dev | 26.0.8-1ubuntu0.3 | main | – | OK (è Mesa) |
| libwayland-dev | 1.24.0-2 | main | – | OK |
| libvulkan-dev | 1.4.341.0-1 | main | `>= 1.3.274` | OK (Debian 13: 1.4.309) |
| debhelper | 13.31ubuntu1 (Debian 13: 13.24.2) | main | `debhelper-compat (= 13)` | **OK**: compat 13 ancora ammesso (massimo 15). `dh_installsysusers` entra nella sequenza solo da compat 14 [V: `root_sequence.pm:51` in libdebhelper-perl], quindi il passo manuale di `debian/rules:90-92` resta necessario, come su Debian |
| dh-apparmor | 5.0.2-0ubuntu1~26.04.1 | **universe** | – | in universe; porta `dh_apparmor` |
| dpkg-dev / fakeroot / binutils | 1.23.7ubuntu1 / 1.37.2-1 / 2.46-3ubuntu2 | main | – | OK |
| lintian | 2.129.0ubuntu2.2 | main | – | OK, più nuovo di quello di Debian 13: possibili tag nuovi (problema 9) |
| gcc | 4:15.2.0-5ubuntu1 (Debian 13: 14.2) | main | – | gcc 15 ha default `gnu23`, ma `rules:18` passa `-std=gnu11`: nessun cambio. Possibili avvisi nuovi [S] |
| glibc (libc6) | 2.43-2ubuntu2.7 (Debian 13: 2.41) | main | – | i `shlibs:Depends` salgono da soli |
| openssl (binario) | 3.5.5-1ubuntu3.7 | main | – | OK |

**Solo per il «nostro labwc»** (vedi 1.6): meson 1.10.1 (universe), patch, hwdata, wayland-protocols 1.47, libegl-dev, libgles-dev 1.7.0-3, libinput-dev 1.31.1,
libpixman-1-dev 0.46.4, libseat-dev 0.9.2-2 (universe), libudev-dev 259.9, libdisplay-info-dev 0.3.0, libxml2-dev 2.15.2, libcairo2-dev, libpango1.0-dev, libpng-dev: tutti esistono [V].

**ngtcp2 / nghttp3 di Ubuntu**: `libngtcp2-dev` 1.16.0-1ubuntu0.1, `libngtcp2-crypto-ossl-dev` 1.16.0, `libnghttp3-dev` 1.12.0-1 (tutti universe) [V]: **troppo vecchi** (servono 1.25.0 e 1.18.0 e le bandiere `NGTCP2_STREAM_CLOSE2_FLAG_*`). `quic-static.sh` resta indispensabile.
Nessun conflitto: nel contenitore di costruzione i `-dev` di Ubuntu non sono installati; i `.a` in `/usr/local/lib` + `PKG_CONFIG_PATH=/usr/local/lib/pkgconfig` vincono. Se un giorno un Build-Depends tirasse dentro `libngtcp2-dev`, il test di `rules:36-37` (`= 1.25.0`) lo scoprirebbe subito.
**OpenSSL e QUIC statico**: ngtcp2 1.25 con `-DENABLE_OPENSSL=ON` compila `ngtcp2_crypto_ossl` contro OpenSSL >= 3.5; Ubuntu ha 3.5.5 con le funzioni QUIC [V]; che compili davvero con gcc 15/cmake 4 è **[S] da provare**. Il binario si lega dinamicamente a `libssl3t64`.

**Pacchetti di esecuzione (Depends, Recommends)**

| Pacchetto | Ubuntu 26.04 | componente | differenza rispetto a Debian 13 |
|---|---|---|---|
| libpam-systemd / systemd | 259.9-0ubuntu0.1 | main | uguale nome. `systemd` ha `Provides: systemd-sysusers, systemd-tmpfiles` |
| libpam-runtime (>= 1.0.1-6) / libpam-modules | 1.7.0-5ubuntu3.2 | main | OK; `libpam-runtime` ha `pam-auth-update` |
| passwd | 1:4.17.4-2ubuntu3 | main | OK |
| dbus-user-session | 1.16.2-2ubuntu4 | main | OK |
| pipewire / wireplumber | 1.6.2-1ubuntu1.2 / 0.5.13-1ubuntu1.1 | main | OK |
| va-driver-all | 2.23.0-1ubuntu1 | **universe** | in universe; Depends: i965-va-driver + intel-media-va-driver (niente Mesa, come annotato in `control:146-156`) |
| mesa-va-drivers | **non esiste come pacchetto**: nome virtuale (`Provides`) di `mesa-libgallium` 26.0.8 | main | **confluito** [V: `apt-cache policy` ABSENT; reverse-provides = mesa-libgallium]. Non va mai nominato |
| mesa-libgallium | 26.0.8-1ubuntu0.3 | main | porta i driver VA di Mesa (radeonsi, nouveau) e i Gallium; già presente con ogni desktop |
| intel-media-va-driver | 26.1.2+dfsg1-1 | universe | esiste |
| intel-media-va-driver-non-free | 26.1.2+ds-1 | **multiverse** | esiste ma non si raccomanda (richiederebbe multiverse) |
| i965-va-driver | 2.4.1+dfsg1-2build1 | universe | (+ `i965-va-driver-shaders` multiverse) |
| mesa-vulkan-drivers | 26.0.8-1ubuntu0.3 | main | esiste, uguale |
| labwc | 0.9.3-1 | **universe** | in universe (Debian 13: main) |
| wlr-randr | 0.4.1-1build1 | **universe** | in universe |
| xwayland | 2:24.1.10-1 | main | uguale |
| dconf-cli | 0.49.0-4 | main | uguale |
| fonts-dejavu-core | 2.37-8build1 | main | uguale |
| apparmor | 5.0.2-0ubuntu1~26.04.1 | main | non nominato (Ubuntu lo ha sempre) |
| ufw | 0.36.2-9build1 | main | solo se l'amministratore lo usa |
| polkitd / pkexec | 127-2ubuntu1.1 | main | `policykit-1` non esiste più (non è nominato) |
| libssl3t64, libpipewire-0.3-0t64, libglib2.0-0t64, libva2, libopus0, libvulkan1, libei1, libgbm1, libxkbcommon0, libdrm2, libwayland-client0 | main | **t64**: trixie ha già fatto la transizione, i nomi coincidono; `${shlibs:Depends}` li calcola da solo: nessuna modifica |

**Desktop**: `ubuntu-session` 50.1 (main), `gdm3` 50.1 (main), `gnome-session` 50.1 (**universe**: D8 «niente gnome-session fra i Recommends» resta valida), `mutter` 50.1 universe,
`kwin-wayland` 6.6.7 / `plasma-workspace` 6.6.7 / `sddm` 0.21.0+git20250502 / `xfce4-session` 4.20.4 / `lxqt-session` 2.3.0 / `lxqt-wayland-session` 0.3.1 / `lightdm` 1.32.0 / `lightdm-gtk-greeter` 2.0.9 / `slick-greeter` 2.2.5: tutti **universe**.
Su Ubuntu **solo GNOME è in main**; gli altri tre gusti sono interamente in universe.

### 1.3 Che cosa va adattato nella costruzione (riga per riga)

1. `build/Containerfile:6` `debian:trixie` → `docker.io/library/ubuntu:26.04`. L'elenco `apt-get install` vale invariato (tutti i nomi esistono). `universe` serve (ninja-build, libva-dev, dh-apparmor) ed è già abilitato nell'immagine [V: `ubuntu.sources`].
2. `build/build-deb.sh:52` suffisso `+deb13` → `+ubuntu26.04`; riga 58 `trixie` → `resolute` (il vecchio albero usava `dist=resolute`, `src/build-targets/build-deb.sh:57`); riga 33 `IMAGE=localhost/remotix-debian-build` → nome diverso (`remotix-ubuntu-build`) per non scavalcare quella Debian sullo stesso server; righe 2, 9, 35 (testo e `OUTPUT`) → `/media/REMOTIX-UBUNTU/pacchetti`.
   Nome risultante `remotix_1.0.0-1+ubuntu26.04_amd64.deb` = `$VERSION_UP-$REVISION+ubuntu26.04` con `RX_VERSION=1.0.0 RX_REVISION=1` (dpkg ammette il `+` nella revisione). Il default `1.0.0~dev` (riga 36) va bene per le prove.
3. Firma del changelog: usare lo stesso maintainer dell'albero Debian (nota: il vecchio albero 1.5 usava un altro indirizzo nella firma, `src/build-targets/build-deb.sh:85`: non riprenderlo; coerenza col controllo dei dati personali del rilascio).
4. `debian/rules`: il commento di testata («Debian 13 only») va aggiornato. Il blocco «nostro labwc» entra solo se il passo 2 del piano lo richiede (1.6).
5. `debian/control`: `Standards-Version 4.7.2` ok (lintian 2.129 può segnalare una versione più nuova [S]); Depends/Recommends: 1.4.
6. Controlli di `build-deb.sh`: R13/R14/R4 non nominano distribuzioni e valgono. `ldd` con usrmerge identico.

### 1.4 Depends / Recommends / Suggests su Ubuntu

- **Depends**: tutti i nomi esistono in main: nessuna modifica.
- **Recommends**: `va-driver-all` invariato (universe; resta un Recommends, quindi un sistema con solo main installa lo stesso senza). Conferma per Ubuntu del ragionamento del 14 nov (`control:146-156`): niente `| va-driver` (soddisfatto da `mesa-libgallium`, quindi apt non tirerebbe `intel-media-va-driver`). `mesa-vulkan-drivers`, `dconf-cli`, `xwayland`, `fonts-dejavu-core` main; `labwc`, `wlr-randr` universe (presenti su Kubuntu/Xubuntu/Lubuntu; su Ubuntu GNOME universe di solito c'è ma non è garantito).
- **Suggests**: nessuno oggi e nessuno necessario.

### 1.5 Riproducibilità (`SOURCE_DATE_EPOCH`)

`build-deb.sh:45-50` deriva `SOURCE_DATE_EPOCH` dal file più recente di `src/`, `debian/`, `LICENSE.md`, `THIRD-PARTY-LICENSES`; i buildflags di dpkg mettono `-ffile-prefix-map`; la variabile arriva al contenitore con `-e SOURCE_DATE_EPOCH` (riga 77).
Su Ubuntu il meccanismo è identico, con tre avvertenze:
- con una copia per `git clone` le mtime sono l'ora del clone e il pacchetto cambierebbe a ogni clone: per Ubuntu fissare `SOURCE_DATE_EPOCH` esplicito (es. ora dell'ultimo commit) [S];
- R23 (`TWICE=1`) confronta due costruzioni nella stessa immagine: vale; fra due immagini costruite in giorni diversi gli aggiornamenti di Ubuntu (`resolute-updates`) cambiano le librerie e il `.buildinfo`;
- ngtcp2/nghttp3 sono clonati da tag (stessi sorgenti) e compilati con gcc 15 di Ubuntu: stessi byte solo a parità di immagine.

### 1.6 Il «nostro labwc» per KDE

Nel vecchio albero il `.deb` per Ubuntu 26.04 includeva un `labwc` proprio (labwc 0.9.3 + wlroots 0.19.2 patchato e statico) in `/usr/lib/remotix/labwc` per ospitare KWin >= 6.5 annidato [V: `REMOTIX/packaging/debian/rules:30-37,65-83`, `packaging/labwc-ospite/{VERSIONS,build.sh,fetch.sh}`]. Il ramo Debian lo ha tolto il 17 nov (`INVENTARIO-non-debian.md:13`).
Se il passo 2 del piano lo richiede, da riprendere: `packaging/labwc-ospite/*` (build.sh, fetch.sh, VERSIONS, la patch `wlroots-0.19.2-remotix-presented-root.patch`), il blocco `REMOTIX_LABWC_OSPITE` di `rules` (criterio `dpkg-vendor --is Ubuntu && VERSION_ID >= 26.04`; `dpkg-vendor` sta in dpkg-dev, che nel contenitore c'è), `src/kwin.c:1322-1385` e `LABWC=` in `src/Makefile`, l'estensione dei Build-Depends (vecchio `build-deb.sh:68-76`: un awk che aggiunge l'elenco alla riga dopo `libvulkan-dev`) e lo strato di Containerfile (elenco in 1.2: tutti esistono su 26.04).
`fetch.sh` scarica da GitHub e gitlab.freedesktop.org con sha256: serve rete in costruzione. Licenze: labwc GPL-2, wlroots MIT; sorgenti da pubblicare (decisione 1 del piano). Vedi anche lo studio 6 (Kubuntu/KWin).

---

## 2. Script del pacchetto: che cosa presuppone Debian, e se vale su Ubuntu

Fonte: `REMOTIX-DEBIAN/debian/` e `src/remotix.pam`; verifiche nel contenitore Ubuntu 26.04.

| File:riga | Presupposto | Su Ubuntu 26.04 |
|---|---|---|
| `remotix.preinst:18-28` | esiste `/sys/class/drm/renderD*` | Vale (kernel). Nei box e nelle VM serve il nodo render (§3, §5) |
| `preinst:32-60` | `getent passwd remotix`, `UID_MIN` da `/etc/login.defs`, utente di sistema | Vale: `UID_MIN 1000` [V]. Nell'immagine base esiste l'utente `ubuntu` uid 1000 (shell bash, home): non è `remotix` ma sposta gli uid dei nostri utenti di prova (§3.4) |
| `postinst:18-19` | `systemd-sysusers remotix.conf`, `systemd-tmpfiles --create remotix.conf` | `systemd` 259 fornisce entrambi; sintassi dei file standard |
| `postinst:24-31` | `pam-auth-update --package`; profilo `/usr/share/pam-configs/remotix` (`Priority: -1`, `Session-Type: Additional`, `Session-Interactive-Only`) | `libpam-runtime` 1.7.0-5ubuntu3.2 ha `pam-auth-update` e `common-session` ha lo stesso formato di Debian (blocco Primary `pam_permit`/`pam_umask`, blocco Additional `pam_unix`) [V]. Nel contenitore base i profili sono solo `mkhomedir` e `unix`: con un desktop si aggiungono `systemd`, `gnome-keyring`/`kwallet` ecc.; l'ordine fra la riga `pam_exec` e `pam_systemd` dipende dalle Priority [S] → da misurare (problema 11) |
| `postinst:37-42` | `remotix --encoding-test h264` | Dipende da VA/Mesa; vedi §1.2 |
| `prerm:17-123` | `loginctl`, `systemctl`, `deb-systemd-invoke`, `gpasswd`, `pam-auth-update --remove` | `init-system-helpers` 1.69 (`deb-systemd-invoke`), `passwd` (`gpasswd`): valgono |
| `postrm:15-63` | `runuser`, `userdel/groupdel`, `/sys/kernel/security/apparmor/.remove` | `runuser` in util-linux 2.41 (main). `.remove` c'è solo con AppArmor attivo: la riga 59 è già protetta da `-w` |
| `rules:97` `dh_apparmor` | `dh-apparmor`; postinst generato con `apparmor_parser -r -W -T` | `dh-apparmor` è in universe (Build-Depends ok). Il profilo `remotix_network` include `<tunables/global>`, `<abstractions/base>`, `<abstractions/nameservice>`: esistono in apparmor 5.0.2 [V]. Il profilo è in complain; su Ubuntu l'enforce non è mai stato provato (piano, rischi). La rete usa `unshare(CLONE_NEWNET/NEWNS)` come root (`walls.c:501,696`) e blocca `CLONE_NEWUSER` con seccomp (`walls.c:635-639`): non tocca il limite `apparmor_restrict_unprivileged_userns` di Ubuntu [S] |
| `remotix.pam-config` | formato pam-auth-update | identico |
| `src/remotix.pam` (conffile) | copia di `/etc/pam.d/sshd` + riga `pam_listfile` | **Identico a `/etc/pam.d/sshd` di Ubuntu 26.04** [V: estratto da openssh-server 1:10.2p1-2ubuntu3.8]; `/etc/pam.d/other` include i `common-*` come su Debian [V] |
| `remotix.ufw` | INI in `/etc/ufw/applications.d/remotix` | valido; dpkg crea la cartella se ufw manca. ufw è in main, spento di default |
| `remotix.sysusers`/`.tmpfiles` | `/usr/sbin/nologin`, `/var/lib/remotix`, `/run/remotix` | validi (usrmerge) |
| `remotix.service` | `After=network.target systemd-logind.service`, `LimitNICE=-11`, `KillMode=mixed` | valido con systemd 259 |
| `remotix-no-suspend.conf` | `[Sleep] AllowSuspend=no…` | valido |
| `rules:74-79` polkit | `/usr/share/polkit-1/rules.d/` | `polkitd` 127 (main), cartella standard |
| `remotix.lintian-overrides` | due tag | da ricontrollare con lintian 2.129 (problema 9) |

Altre note: `snapd` (main) è su quasi ogni desktop Ubuntu e carica profili AppArmor suoi: non interagisce con `remotix_network`. Su una macchina con solo `main` abilitato i Recommends `labwc`, `wlr-randr`, `va-driver-all` non arrivano.

---

## 3. Macchine di prova (box): come sono fatte e che cosa cambia

### 3.1 Come sono fatte (Debian 13)

- `boxes/Containerfile:1-44`: `FROM debian:trixie`; `ARG DESKTOP` (gnome|kde|xfce|lxqt); installa il minimo (`systemd systemd-sysv dbus dbus-user-session libpam-systemd sudo procps iproute2 ca-certificates curl openssh-server`);
  dichiara il display manager a debconf (`gnome→gdm3`, `kde|lxqt→sddm`, `xfce→lightdm`) PRIMA di `apt-get install -y -q task-$DESKTOP-desktop` (con Recommends), poi lo registra con `box-set-dm`;
  strumenti di prova (`openssh-client python3 python3-gi gir1.2-gtk-4.0 libglib2.0-bin gawk openssl wl-clipboard`, `pcmanfm-qt` per LXQt);
  nasconde il Welcome Center di KDE; `common.sh` (porta ssh, journald persistente, `box-gruppi.service`); due utenti `prova`/`prova2` password `prova2026`; chiave root; `box-identity.sh debian 13 $DESKTOP -`; `STOPSIGNAL SIGRTMIN+3`, `CMD /sbin/init`.
- `boxes/box.sh:60-165`: podman come root (sudo con password vuota), `--cgroup-manager=cgroupfs`; immagine `rx/<de>:latest`, contenitore `rx-<de>`; porte ssh 2211-2214 e REMOTIX 8811-8814 (xfce=1, lxqt=2, gnome=3, kde=4);
  `podman run -d --systemd=always --pids-limit 16384 --network=host --device /dev/dri --ulimit memlock=-1:-1 --cap-add=AUDIT_WRITE,AUDIT_CONTROL,SYS_ADMIN,SYS_NICE,WAKE_ALARM`;
  `power.sh` (tmpfs su `/sys/power` + riavvio di logind), attesa ssh; `install` copia il `.deb`, `apt-get update`, `apt-get install -y ./file.deb`, scrive `REMOTIX_PORT=<porta>` in `/etc/remotix/remotix.conf.d/10-box-port.conf`.
- `boxes/common.sh:1-57`: `multi-user.target` (niente display manager acceso: il box non ha schermo), sshd su 127.0.0.1 con la porta del box, journald persistente, `box-gruppi.service` che allinea i gruppi `video`/`render` ai gid dei nodi `/dev/dri` dell'host.
- `boxes/set-dm.sh:1-40`: scrive `/etc/X11/default-display-manager` e abilita l'unità (in un `podman build` il postinst non lo fa), crea il link `display-manager.service`; FALLISCE se non è registrato.
- `boxes/power.sh:1-61`: già nato su Ubuntu 26.04 (commento riga 271 del vecchio `11-box-power.sh`): vale su Ubuntu.
- `boxes/box-identity.sh:1-263`: già conosce Ubuntu (§3.4 punto 7).
- `server/prepara-server.sh` (154 righe): il server è una macchina **Debian** a rootfs RAM; ricrea cartelle in `/media/REMOTIX-DEBIAN`, installa podman ecc., e (riga 84) i pacchetti del browser di prova **sull'host**: `chromium firefox-esr labwc wlr-randr python3-pil libavcodec61 fonts-dejavu-core`, più `pipewire pipewire-pulse wireplumber pulseaudio-utils` (riga 97) e `qemu-system-x86 qemu-utils genisoimage acl` (riga 131); self-check con `debian:trixie` (righe 146-152).

### 3.2 Misura dei quattro metapacchetti su Ubuntu 26.04

**Simulazione** `apt-get -s` sul contenitore pulito [V: `sim-*.txt`], pacchetti nuovi installati:

| Metapacchetto | con Recommends | senza Recommends | porta dentro (con Recommends) |
|---|---|---|---|
| `ubuntu-desktop-minimal` 1.570.4 (main) | 1256 | 727 | gdm3, gnome-shell, ubuntu-session, **snapd, firefox** |
| `ubuntu-desktop` 1.570.4 (main) | 1405 | 728 | idem + thunderbird |
| `kubuntu-desktop` 1.496 (universe) | 1824 | 972 | sddm, sddm-theme-breeze, kwin-wayland, plasma-workspace, snapd, firefox, ufw, va-driver-all, intel-media-va-driver |
| `xubuntu-desktop-minimal` 2.272 (universe) | 1230 | 433 | lightdm, lightdm-gtk-greeter **e anche gdm3, gnome-shell, ubuntu-session** (Recommends), snapd |
| `xubuntu-desktop` 2.272 (universe) | 1727 | 731 | lightdm + **gdm3, gnome-shell, ubuntu-session**, snapd, firefox, thunderbird |
| `lubuntu-desktop` 26.04.3 (universe) | 1766 | 787 | sddm, lxqt-session, openbox, snapd, firefox |

L'`xubuntu-desktop` senza Recommends porta comunque `gnome-shell` (non `gdm3`): arriva da una Depends di un pacchetto GNOME (`language-selector-gnome`/`update-manager` sono Depends di `xubuntu-desktop`, `control` dei metapacchetti [V: `apt-cache depends`]).
`xubuntu-desktop-minimal` senza Recommends: 433 pacchetti, lightdm, niente GNOME.

**Con i «pin» del vecchio Containerfile** (`gnome-shell gdm3 ubuntu-session` a -1 sui gusti non GNOME; `firefox thunderbird chromium-browser` a -1 per tutti) [V: `sim2-*.txt`]: kubuntu 1823, xubuntu-desktop 1591, xubuntu-desktop-minimal 997, lubuntu 1765, tutti `rc=0`, **gnome-shell=0 e gdm3=0**: i pin non rompono nessuna dipendenza dura. `snapd` resta (Recommends) ma non serve in un contenitore. Con pin -1 anche su `snapd`: ubuntu-desktop 1401 pacchetti, snapd=0, `rc=0` [V: `sim3-*.txt`].

**Installazione vera (chroot)** [V: `inst-*.log`, `misure.txt`]: `debootstrap --variant=minbase resolute`, archivi main+universe+updates+security, `apt-get install -y <metapacchetto>` PLAIN (con Recommends, senza debconf né pin: come farebbe un utente che aggiunge il metapacchetto a un sistema minimo), `policy-rc.d` che risponde 101, nessun systemd in esecuzione.
(Nota di metodo: in un contenitore senza `CAP_MKNOD` ho dovuto sostituire `mknod` con `touch`, quindi `/dev/null` nel chroot era un file normale e il pacchetto `dictionaries-common` non si è configurato: `rc=100` in tutti e quattro. È un difetto del mio chroot, non di Ubuntu; tutti gli altri pacchetti sono configurati.)

| | Ubuntu (`ubuntu-desktop`) | Kubuntu | Xubuntu | Lubuntu |
|---|---|---|---|---|
| pacchetti nuovi / da scaricare | 1417 / 931 MB | 1837 / 1419 MB | 1597 / 1033 MB | 1778 / 1187 MB |
| spazio aggiunto (apt) | 3163 MB | 4445 MB | 3685 MB | 3863 MB |
| chroot finale (con base minbase) | 4462 MB | 6242 MB | 5112 MB | 5463 MB |
| tempo (4 in parallelo) | 17 min | 24 min | 22 min | 24 min |
| `/etc/X11/default-display-manager` | **`/usr/sbin/gdm3`** | `/usr/bin/sddm` | **`/usr/sbin/gdm3`** | `/usr/bin/sddm` |
| `display-manager.service` → | gdm3 | sddm | **gdm3** | sddm |
| DM installati | gdm3 | sddm | **lightdm e gdm3** | sddm |
| gnome-shell / ubuntu-session | sì / sì | no / no | **sì / sì** | no / no |
| `x-session-manager` (alternativa) | gnome-session | (non impostata) | **gnome-session** | startlxqt |
| sessioni (`xsessions`, `wayland-sessions`) | solo wayland: `ubuntu` | solo wayland: `plasma` (nessuna sessione X) | `xubuntu`, `xfce`, `lightdm-xsession` + wayland `ubuntu`, `xfce-wayland` | `Lubuntu`, `lxqt`, `openbox` (X); nessuna sessione wayland |
| snapd / firefox (snap) | installati; firefox si installa (vedi sotto) | idem | idem | idem |
| terminale / file manager | **ptyxis** / nautilus | konsole / dolphin | xfce4-terminal / thunar (+ nautilus) | qterminal / pcmanfm-qt |
| `labwc`, `wlr-randr` | assenti | assenti | assenti | assenti |
| `va-driver-all` | assente (Ubuntu GNOME non lo raccomanda: arriva solo `mesa-libgallium`) | sì (+ intel-media-va-driver) | sì | sì |
| profili `pam-auth-update` | capability fprintd gnome-keyring mkhomedir pwquality sss systemd unix | capability fprintd mkhomedir systemd unix | capability gnome-keyring mkhomedir systemd unix | capability mkhomedir systemd unix |

Fatti che contano:
- **Conferma di BOX-01**: `xubuntu-desktop` nudo → **gdm3 è il predefinito** (e `display-manager.service`), con gnome-shell e ubuntu-session installati e l'alternativa `x-session-manager` che punta a `gnome-session`. Il guaio del vecchio albero si riproduce identico.
- Kubuntu e Lubuntu: sddm predefinito senza accorgimenti; Lubuntu non porta nessuna sessione Wayland (`lxqt-wayland-session` non è fra le dipendenze del metapacchetto) e non porta `labwc`/`wlr-randr`: li metterà il `Recommends` del nostro pacchetto.
- Ubuntu GNOME: `va-driver-all` non c'è (solo `mesa-libgallium` e `mesa-vulkan-drivers`): su una macchina Intel il nostro Recommends `va-driver-all` è quello che porta `intel-media-va-driver`.
- **Terminale di GNOME su Ubuntu 26.04 = `ptyxis`** (non `gnome-terminal`): `prove/check-desktop.py:54` va aggiornato per il gusto Ubuntu.
- `common-session` dopo il desktop: il blocco Additional contiene `pam_unix` e poi `pam_systemd` (e `pam_sss` su Ubuntu); la nostra riga (Priority -1, `Additional`) verrà messa fra/dopo quelle: l'ordine esatto va misurato installando il `.deb` (problema 11).
- **Snap in installazione**: nel chroot (senza `/run/snapd.socket`) la preinst di `firefox`/`thunderbird` stampa «System doesn't have a working snapd, skipping» e prosegue [V: `firefox.preinst`: `skip_unusable_snapd` = niente `/run/snapd.socket`]. Quindi la vecchia affermazione «la preinst fallisce» vale solo in un box avviato con systemd (dove `snapd.socket` esiste e `snap install firefox` va a vuoto o fallisce [S]). Il pin -1 resta la cura sicura.

### 3.3 Il guaio noto: Xubuntu con gdm3, e la cura del vecchio albero

Nel vecchio albero `ubuntu2604-xfce` aveva `xubuntu-desktop` **più** `gnome-shell`, `ubuntu-session` e `gdm3` come display manager attivo (BOX-01: `assessment/banchi/box-ambiente.md:80-99`; `assessment/xfce/ubuntu2604.md:7-14`; `RAPPORTO.md:394`): gdm3 veniva configurato dopo lightdm e diventava il registrato; il prodotto lo prendeva per un GNOME. Cura trovata il 16 nov (`benches/17-distro/boxes/Containerfile.ubuntu2604:19-33`):
1. dichiarare il display manager a debconf PRIMA (`echo "$DM shared/default-x-display-manager select $DM" | debconf-set-selections`);
2. per i gusti non GNOME, `apt` preference -1 su `gnome-shell gdm3 ubuntu-session`;
3. `set-dm.sh` (registrazione a mano, perché in `podman build` il postinst non la fa);
4. `box-identity.sh:156-161` fa fallire la costruzione se un gusto non GNOME ha `gnome-shell`, `gdm3` o la sessione `ubuntu`.
Ora verificato: i pin passano senza conflitti (3.2). Le macchine **vere** (ISO Xubuntu) non hanno gnome-shell: l'ISO installa la lista propria del gusto, non `xubuntu-desktop` con tutti i Recommends. Quindi il box con i pin è più fedele del box «nudo».
Alternativa già indicata dal vecchio studio (BOX-01): partire dal `casper/*.squashfs` della ISO del gusto (`unsquashfs` + `podman import`): è il filesystem di un cliente vero. Costo: ISO 3,7–6,2 GB (§5.2) più lo squashfs scompattato (stima 6–9 GB per gusto [S]).

File di configurazione dei display manager nei pacchetti [V: contenuto dei `.deb`]:
- Xubuntu: `xubuntu-default-settings` → `/usr/share/lightdm/lightdm.conf.d/60-xubuntu.conf` (`[Seat:*] user-session=xubuntu`) e `50-xubuntu-numlock.conf`; sessione `/usr/share/xsessions/xubuntu.desktop`. `ubuntu-session` porta `/usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf` (`user-session=ubuntu`): se c'è anche quello, vince `60-xubuntu` per l'ordine alfabetico.
- Kubuntu: `kubuntu-settings-desktop` → `/etc/sddm.conf.d/10-wayland.conf` (`DisplayServer=wayland`, `CompositorCommand=kwin_wayland --drm …`) e `/etc/sddm.conf.d/20-kubuntu.conf` (`[Autologin] Session=plasma`, `User=` vuoto, `Relogin=false`; `[Theme]`, `[Users]`): è l'«autologin» vuoto che `box-identity.sh:175-183` legge come sessione predefinita (`Session` di `[Autologin]`).
- Lubuntu: `lubuntu-default-settings` → `/etc/sddm.conf.d/lubuntu_settings.conf` (`[Theme] Current=lubuntu`, nessuna `DefaultSession`), sessione `/usr/share/xsessions/Lubuntu.desktop`; la sessione Wayland è di `lxqt-wayland-session` [S].
- Ubuntu: gdm3 con `/etc/gdm3/custom.conf`; sessione `/usr/share/wayland-sessions/ubuntu.desktop` (da `ubuntu-session`).

### 3.4 Che cosa cambia nelle macchine di prova (file per file)

1. `boxes/Containerfile:5` → `docker.io/library/ubuntu:26.04`. Differenze dell'immagine base [V]: utente `ubuntu` uid/gid 1000 già presente (gruppi `video`, `sudo`); `/usr/sbin/policy-rc.d` presente; `apt` svuota la cache a ogni operazione (`docker-clean`); `strings`, `dpkg-vendor` assenti; nessun gruppo `render`. L'utente `ubuntu` fa slittare `prova`/`prova2` a uid 1001/1002: o si toglie (`userdel -r ubuntu`) per avere uid come in Debian, o si accetta (`package-snap.py` confronta utenti prima/dopo).
2. `boxes/Containerfile:17-21`: `task-$DESKTOP-desktop` → il metapacchetto del gusto, con il debconf del display manager e i pin del vecchio `Containerfile.ubuntu2604` (§3.3). **Decisione del proprietario**: `ubuntu-desktop` o `ubuntu-desktop-minimal` per GNOME. L'ISO ufficiale installa `ubuntu-desktop-minimal` (`iso-differences.md`: «the ISO installs ubuntu-desktop-minimal»), `apt install ubuntu-desktop` dà il completo. Per gli altri gusti il metapacchetto completo ha il nome del gusto; l'ISO ne installa un sottoinsieme (non verificato quale).
   Display manager di ciascun gusto: Ubuntu→gdm3, Kubuntu→sddm, Xubuntu→lightdm (+`lightdm-gtk-greeter`), Lubuntu→sddm [V: Depends dei metapacchetti]; il predefinito effettivo in `/etc/X11/default-display-manager`: vedi misura nei chroot (3.2).
3. **debconf non interattivo**: `DEBIAN_FRONTEND=noninteractive` basta (come nel vecchio Containerfile Ubuntu, che funzionava); `debconf-set-selections` è nel pacchetto `debconf`.
4. **snap nel contenitore**: i metapacchetti raccomandano `snapd` e `firefox` (pacchetto di transizione che scarica lo snap: `firefox 1:1snap1-0ubuntu9.1`, `chromium-browser 2:1snap1-0ubuntu4` [V]); nel contenitore `snapd` non può girare (niente squashfs/AppArmor di snap) e il vecchio `Containerfile.ubuntu2604:9-12` annotava che la preinst dei pacchetti-snap fallisce (in un `podman build` senza `/run/snapd.socket` oggi salta invece senza errore: vedi 3.2). Cura già in uso: pin -1 su `firefox thunderbird chromium-browser`; `snapd` può restare (inattivo) o essere escluso (pin -1: simulazione ok).
   **Browser delle prove**: le prove NON usano il browser del box. Girano **sul server (host Debian)**: Chromium/Firefox ESR dell'host (`prove/lib.py:483,593`, `browserlib.py:99,199`) dentro un labwc headless (`lib.py:300-337`), con PipeWire-pulse dell'host (`lib.py:38,741`), puntati alla porta del box (`https://<host>:881x/`, `lib.py:723`). I browser snap di Ubuntu non servono e il browser delle prove non cambia.
5. `boxes/Containerfile:24-26`: i pacchetti di prova sono presenti su Ubuntu: `python3-gi`, `gir1.2-gtk-4.0`, `libglib2.0-bin`, `gawk`, `wl-clipboard`, `pcmanfm-qt` [S per pacchetto: il vecchio `Containerfile.ubuntu2604:35-37` ha la stessa riga e funzionava il 16-17 nov].
6. Welcome Center di KDE (righe 30-33): il vecchio Containerfile Ubuntu ha la stessa soluzione (`Containerfile.ubuntu2604:41-44`) e funzionava.
7. `boxes/box-identity.sh`: pronto per Ubuntu. `desktop_of` (47-58) mette `xubuntu|lubuntu|kubuntu` prima di `ubuntu`; regola «gusto non GNOME senza gnome-shell/gdm3/sessione ubuntu» (156-161) già presente; `WANT` gnome=`gdm`, kde=`sddm plasmalogin`, xfce=`lightdm`, lxqt=`sddm` valgono per i 4 gusti. Chiamata: `box-identity.sh ubuntu 26.04 $DESKTOP -`. Lubuntu: nessuna `DefaultSession` dichiarata → il controllo (righe 195-231) ricade sull'alternativa `x-session-manager` o dà «NOT-VERIFIABLE» se ci sono sessioni di altri desktop [S].
8. `boxes/set-dm.sh`: già «Debian/Ubuntu family»; per gdm3 prova le unità `gdm3` poi `gdm` (righe 239-247).
9. `boxes/common.sh`, `power.sh`: nessun nome Debian. Il gruppo `render` lo crea systemd/udev all'avvio; `box-gruppi.service` allinea `video`/`render` ai gid dei nodi dell'host.
10. `boxes/box.sh:76-81`: nomi e porte coincidono con quelli dei box Debian e i box usano `--network=host`: per girare insieme ai Debian servono nomi/immagini/porte diversi (es. `rxu-<de>`, `rxu/<de>`, ssh 2221-2224, REMOTIX 8821-8824). `box.sh` va copiato per Ubuntu e `PORTS` (`lib.py:37`, `base-check.py:23`) parametrizzato.
11. `boxes/box.sh:107-110`: `--device /dev/dri` e le `--cap-add` non cambiano (con systemd 259 su Ubuntu 26.04 hanno funzionato nel vecchio banco).
12. Il display manager **non gira** nei box (multi-user.target, nessun monitor): serve solo che sia registrato (`/etc/X11/default-display-manager` + `display-manager.service`) e che i suoi file di configurazione siano quelli del gusto (§3.3), perché il prodotto li legge. Una «schermata di accesso vera» (piano, passo 0) esiste solo nelle macchine vere/VM, non nei box.

### 3.5 Spazio e tempi misurati (installazione plain del metapacchetto in chroot, 4 in parallelo sulla stessa macchina)

Vedi la tabella di 3.2 (righe «spazio», «chroot finale» e «tempo»). Riassunto: ogni immagine di box con il metapacchetto PLAIN pesa **4,5–6,2 GB** (come chroot; come immagine podman di strati una cifra simile più la base di ~80 MB), con 0,9–1,4 GB da scaricare e **17–24 minuti** a costruirla (tempo con quattro costruzioni insieme sulla macchina del server). I pin diminuiscono di poco (kubuntu 1823 contro 1837 pacchetti, xubuntu 1591 contro 1727 nella simulazione).

---

## 4. Prove (`REMOTIX-DEBIAN/prove/`): che cosa nomina Debian

Dove girano: `prove/*.py` girano **sul server** e comandano i box con `boxes/box.sh ssh` (`lib.py:121`, `base-check.py:87`). Il browser è Chromium o Firefox ESR dell'**host** in un labwc headless dell'host. Nulla di tutto questo dipende dalla distribuzione nel box. Elenco di ciò che nomina Debian, suoi percorsi o pacchetti:

| file:riga | che cosa | su Ubuntu |
|---|---|---|
| `fresh.sh:3,6` | `DEB` di default cerca `/media/REMOTIX-DEBIAN/pacchetti/remotix_*.deb` | cambiare in `/media/REMOTIX-UBUNTU/pacchetti` (o passare `DEB=`) |
| `server/vm-login-test.py:6` | `sys.path.insert(0, "/media/REMOTIX-DEBIAN/prove")` | cambiare |
| `lib.py:37`, `base-check.py:23` | `PORTS` 8811-8814 | parametrizzare per i box Ubuntu (§3.4 punto 10) |
| `lib.py:483-485`, `browserlib.py:99` | `google-chrome` o `chromium` (host) | nessun cambio |
| `lib.py:593`, `browserlib.py:199` | `firefox-esr` o `firefox` (host) | nessun cambio |
| `check-package.py:72,101,112` | `apt-get`, `dpkg-query`, `apt-get update` nel box | uguali su Ubuntu |
| `check-package.py:109-111` | toglie `/usr/sbin/policy-rc.d` («the Docker debian one») | l'immagine Ubuntu lo ha uguale [V]: funziona; aggiornare il commento |
| `check-package.py:138-139,181,364,433`, `check-prelocal.py:20,305-313` | riga `pam_exec … remotix-local-login` in `/etc/pam.d/common-session` e suo ordine rispetto a `pam_systemd` | file e formato esistono; l'ordine va misurato (problema 11) |
| `check-ban.py:329-332` | `ls /usr/bin/remotix* /usr/sbin/remotix*`, `dpkg -s remotix` | uguali |
| `check-lifecycle.py:28-31`, `deskkit.py:14-19` | «Log Out» per desktop (`xfce4-session-logout --logout`, `org.lxqt.session`, `org.gnome.SessionManager Logout`, `org.kde.Shutdown logout`) | Xubuntu/Lubuntu/Kubuntu uguali; GNOME 50: agenti 1-7 |
| `check-desktop.py:54-55` | `TERMINAL = xfce4-terminal, qterminal, gnome-terminal, konsole`; `FILEMGR = thunar, pcmanfm-qt, nautilus, dolphin` | **da cambiare**: su Ubuntu 26.04 il terminale di GNOME è `ptyxis` [V: chroot], non `gnome-terminal`; Xubuntu ha anche nautilus oltre a thunar (non va confuso: è il segno del GNOME rimasto) |
| `check-desktop.py:118-120` | lockdown GNOME e GDM | da riverificare su GNOME 50 |
| `check-input.py:72-76` | `pkill gnome-tour` | Ubuntu: il primo accesso usa `gnome-initial-setup`? da verificare (agenti 1-7) |
| `check-prelocal.py:42,100` | regex delle unità utente `graphical-session.target\|app-\|org.gnome.\|plasma-\|xfce\|lxqt` | Ubuntu aggiunge unità proprie (`snap.*`, `ubuntu-*`, `gnome-…`): da misurare [S] |
| `package-snap.py:23-29` | elenco SKIP di percorsi (`/run/lightdm`, `/run/gdm3`, `/run/sddm`, …) | su Ubuntu servono in più `/var/lib/snapd`, `/run/snapd*`, `/var/lib/cloud` se presenti, `/run/systemd/resolve` [S] |
| `lib.py:155-157` | `useradd`, `chpasswd`, `usermod -aG video,render,users` | uguali |
| `all.sh:12-13` | accetta `xfce\|lxqt\|gnome\|kde` | uguale (nomi di desktop) |

In breve: le prove sono quasi tutte indipendenti dalla distribuzione. Cambiano percorsi (`/media/REMOTIX-DEBIAN`), porte e nomi dei box; da controllare `common-session` e gli strumenti dei desktop nei box Ubuntu.

---

## 5. VM e macchine vere

### 5.1 `server/vm.sh` e l'immagine cloud

- `vm.sh:1-46`: immagine `debian-13-genericcloud-amd64.qcow2`, ssh 2301, REMOTIX 8901→7447 (TCP+UDP) con `-netdev user`, `qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 4096`, **SeaBIOS** (niente OVMF), seed `cidata` con `genisoimage` (`#cloud-config` con utente `prova`/`prova`), disco 20G.
- Equivalente Ubuntu 26.04 [W+V: cartella letta con `curl` dal server]: `https://cloud-images.ubuntu.com/releases/26.04/release/ubuntu-26.04-server-cloudimg-amd64.img` (821,65 MiB; esiste anche `…-amd64v3.img`), con `SHA256SUMS` nella stessa cartella. È un'immagine qcow2 [S]; usa `cloud-init`, quindi lo stesso seed `cidata` vale (utente predefinito `ubuntu`, ma il seed crea `prova`). Il vecchio `17-vm.sh:81` usava lo stesso indirizzo. L'immagine amd64 parte anche in BIOS [S].
- Per «vestirla» col gusto il vecchio `17-vm.sh:392-395` faceva `apt-get install -y -q ubuntu-desktop|kubuntu-desktop|xubuntu-desktop|lubuntu-desktop`: stessi problemi di §3.3 (Xubuntu+gdm3, snap) e stessa cura.
- **Attenzione (vale anche per la VM Debian)**: dal 17 nov `preinst` rifiuta l'installazione senza nodo `renderD*`. `vm.sh:186-189` non dà una scheda con render node (VGA standard → solo `card0`): l'installazione del `.deb` nella VM fallirebbe. Serve `-device virtio-vga`/`virtio-gpu-pci` (dà un `renderD128`; la codifica VA-API non funziona nella VM, quindi la prova di codifica del `postinst` darà avviso) o la scheda passata (`RX_VM_GPU_PASSTHROUGH` del vecchio `17-vm.sh`, che richiede UEFI/OVMF; `ovmf` esiste in Ubuntu 26.04 come 2025.11-3ubuntu7.3 [V], sull'host Debian non l'ho controllato).

### 5.2 Le quattro ISO live ufficiali (26.04.1)

[W+V: elenchi delle cartelle e `Content-Length` letti dal server con `curl -sIL`]

| Gusto | cartella | file | dimensione |
|---|---|---|---|
| Ubuntu | `https://releases.ubuntu.com/26.04/` | `ubuntu-26.04.1-desktop-amd64.iso` (c'è anche la 26.04.0) | 6182 MiB |
| Kubuntu | `https://cdimage.ubuntu.com/kubuntu/releases/26.04/release/` | `kubuntu-26.04.1-desktop-amd64.iso` | 4838 MiB |
| Xubuntu | `https://cdimage.ubuntu.com/xubuntu/releases/26.04/release/` | `xubuntu-26.04.1-desktop-amd64.iso` (esiste anche `xubuntu-26.04.1-minimal-amd64.iso`) | 4946 MiB |
| Lubuntu | `https://cdimage.ubuntu.com/lubuntu/releases/26.04/release/` | `lubuntu-26.04.1-desktop-amd64.iso` | 3746 MiB |

Ogni cartella ha `SHA256SUMS` (e i `.torrent`). Totale circa 19,7 GB.
**Installare un `.deb` locale su una live**: la sessione live ha rete (NetworkManager) e l'utente live ha `sudo` senza password [S]. `sudo apt install ./remotix_1.0.0-1+ubuntu26.04_amd64.deb` risolve i Depends da main; i Recommends (`labwc`, `wlr-randr`, `va-driver-all`) stanno in universe: la live ha di norma `main universe restricted multiverse` in `ubuntu.sources` [S, non verificato: serve avviare una live; se non c'è, `sudo add-apt-repository universe` o `apt install --no-install-recommends`]. Spazio: la live scrive in un overlay su RAM (circa metà della memoria): il `.deb` e le poche dipendenze mancanti (pipewire/wireplumber/libpam-systemd di norma già presenti nelle live) entrano; `labwc` e i driver VA/Vulkan potrebbero valere qualche decina di MB [S]. La sessione grafica della live è in autologin: il principio «locale esclude remoto» (memoria 1.5.4) va provato proprio con quella sessione. Il `preinst` esige un nodo render: la macchina vera lo ha.

---

## 6. Spazio e tempi (stima)

| voce | spazio | tempo | fonte |
|---|---|---|---|
| immagine di costruzione (base Ubuntu + 376 pacchetti di build + ngtcp2/nghttp3 statici) | download 209 MB, installato circa 1,0–1,3 GB [S] | pochi minuti + compilazione ngtcp2/nghttp3 (alcuni minuti) | [V] 376 pacchetti, 209 MB (`bsz.sh`) |
| in più per il «nostro labwc» (se serve) | +203 pacchetti, +103 MB download | compilazione wlroots+labwc: 5–15 min [S] | [V] |
| una costruzione del `.deb` + lintian + controlli | poche decine di MB | 3–6 min [S] (nessun dato misurato) | [S] |
| 4 immagini di box (plain) | 4,5 + 6,2 + 5,1 + 5,5 = **~21 GB** (chroot) | 17–24 min in parallelo | [V] |
| cache `apt` dei download (se non svuotata) | +4,6 GB | | [V: 931+1419+1033+1187 MB] |
| 4 ISO live | **19,7 GB** (6182+4838+4946+3746 MiB) | download: dipende dalla linea | [V] |
| immagine cloud Ubuntu + disco VM (20 GB sparso) | 0,8 GB + fino a 20 GB | avvio 1–2 min [S] | [V] per l'immagine |
| VM «vestita» col gusto (cloud + metapacchetto) | ~8–10 GB scritti [S] | 25–35 min [S] | [S] |
| TOTALE ambiente completo | ~21 + 2 + 20 + 20 = circa 65–70 GB | | |
Sul server restano 1,1 TB liberi in `/media` [V: `df`]: nessun problema di spazio. I miei chroot di misura (~21 GB) sono dentro il contenitore `studio-8` e vanno via con lui.

---

## Problemi da affrontare

1. **Contenitore di costruzione Ubuntu** (`build/Containerfile:6`, `build/build-deb.sh:33,35,52,58`): base, suffisso `+ubuntu26.04`, suite `resolute`, nome dell'immagine e `OUTPUT`. Peso **piccolo**. Cura nota: sì, vecchio `src/build-targets/{Containerfile.ubuntu2604,build-deb.sh}` (stesso schema).
2. **Dipendenze in universe** (`debian/control`: `libva-dev`, `dh-apparmor` come Build-Depends; `va-driver-all`, `labwc`, `wlr-randr` come Recommends; `ninja-build` in immagine). Nessuna modifica ai nomi, ma il pacchetto dipende da universe a costruzione e (per i Recommends) a installazione. Peso **piccolo**; da dichiarare nella documentazione. Cura nota: sì, già annotato in `control:146-156`.
3. **`mesa-va-drivers` non esiste** (confluito in `mesa-libgallium`): non va nominato; `va-driver-all` da solo (già così). Peso **piccolo**. Cura nota: sì (`control:146-156`).
4. **Ubuntu GNOME non porta `va-driver-all`** ma solo Mesa: su Intel il Recommends è decisivo, e con `--no-install-recommends` l'Intel non codifica. Il `preinst`/`postinst` già lo dice (`postinst:37-42`). Peso **piccolo**; decisione: lasciare così. Cura: nessuna necessaria.
5. **ngtcp2 1.25 / nghttp3 1.18 statici con OpenSSL 3.5.5 e gcc 15 / cmake 4.2** (`build/quic-static.sh`): le librerie di Ubuntu (1.16 / 1.12) sono troppo vecchie, il vecchio albero costruiva già gli stessi tag su Ubuntu 26.04. Peso **piccolo** se riesce al primo colpo; cura nota: sì (`REMOTIX/src/build-targets/Containerfile.ubuntu2604` usa lo stesso `quic-static.sh`).
6. **«Nostro labwc» per Kubuntu** (`rules`, `Containerfile`, `build-deb.sh`, `control` + `labwc-ospite/`): da reinserire SOLO se il passo 2 del piano lo chiede. Peso **medio** (7 file da riprendere, tutti i pacchetti esistono, serve rete a costruire e i sorgenti vanno pubblicati). Cura nota: sì, `REMOTIX/packaging/labwc-ospite/*` e `packaging/debian/rules:30-83`.
7. **Box Ubuntu**: `boxes/Containerfile`, `box.sh`, `box-identity.sh`, `set-dm.sh`: base `ubuntu:26.04`, metapacchetti dei gusti, **debconf del display manager + pin -1** su `gnome-shell gdm3 ubuntu-session` (non GNOME) e su `firefox thunderbird chromium-browser`, utente `ubuntu` uid 1000 da gestire, `box-identity.sh ubuntu 26.04 …`. Il difetto BOX-01 (Xubuntu = gdm3 + GNOME) è **confermato oggi** in modo identico. Peso **medio**. Cura nota: sì, `REMOTIX/benches/17-distro/boxes/Containerfile.ubuntu2604:19-33` (+ `box-identity.sh`, `set-dm.sh`); i pin passano senza conflitti (verificato).
8. **Nomi e porte dei box**: stessi nomi (`rx-<de>`) e porte (2211-2214, 8811-8814) dei box Debian con rete host: servono nomi e porte distinti (`box.sh:76-81`, `lib.py:37`, `base-check.py:23`) e cartelle di lavoro in `/media/REMOTIX-UBUNTU`. Peso **piccolo**. Cura nota: no (nuova, perché Debian e Ubuntu non coesistevano).
9. **lintian 2.129 (Ubuntu) contro 2.122 (Debian 13)**: possibili tag nuovi/rinominati; i due override (`remotix.lintian-overrides`) e `Standards-Version 4.7.2` da ricontrollare. Peso **piccolo**. Cura nota: no.
10. **Riproducibilità**: `SOURCE_DATE_EPOCH` esplicito se l'albero Ubuntu nasce da un clone (le mtime non contano più); R23 vale solo a parità di immagine. Peso **piccolo**. Cura nota: sì (`build-deb.sh:45-50` già lo prevede).
11. **Ordine in `common-session`** della riga `pam_exec … remotix-local-login` (profilo `Priority -1`): su Ubuntu `common-session` ha più profili (`systemd`, `sss`, `gnome-keyring`, `kwallet`…) e `prove/check-prelocal.py:305-313` pretende `pam_exec` DOPO `pam_systemd`. Peso **medio** (tocca il principio «locale esclude remoto»). Cura nota: no (la riga è del 1.0.0 Debian; nel vecchio albero non c'era).
12. **Prove**: percorsi `/media/REMOTIX-DEBIAN` (`fresh.sh:3,6`, `vm-login-test.py:6`), `TERMINAL gnome = ptyxis` (`check-desktop.py:54`), SKIP di `package-snap.py` (`/var/lib/snapd`, `/run/snapd*`…), regex di unità utente di `check-prelocal.py:42,100`, `gnome-tour` (`check-input.py:74`). Peso **piccolo**. Cura nota: parziale (vecchio `benches/15-suite/box17.py`, `15-g1b-common.py`).
13. **VM**: `server/vm.sh` per Ubuntu (immagine `ubuntu-26.04-server-cloudimg-amd64.img`, utente `prova` via cloud-init, ssh/REMOTIX su porte diverse) e, **per Debian e Ubuntu**, un dispositivo con nodo render (`virtio-vga`/`virtio-gpu-pci`) altrimenti il `preinst` rifiuta l'installazione. Peso **piccolo/medio**. Cura nota: sì in parte (`REMOTIX/benches/17-distro/17-vm.sh`, `RX_VM_GPU_PASSTHROUGH`).
14. **ISO live**: scaricare e verificare le quattro ISO (19,7 GB) e preparare una procedura per installare il `.deb` (rete, universe, spazio overlay). Peso **piccolo** (lavoro del proprietario). Cura nota: parziale (`17-vm.sh` `from-iso`, `iso-answers/ubuntu2604.user-data`).
15. **`prepara-server.sh`**: il server è Debian a rootfs RAM; `BASE=/media/REMOTIX-DEBIAN` e il self-check `debian:trixie` vanno affiancati da una versione per `/media/REMOTIX-UBUNTU` e `ubuntu:26.04` (non toccare quella Debian). Peso **piccolo**. Cura nota: no.
16. **Immagini fedeli ai clienti**: il box con `apt install <metapacchetto>` + pin non è identico a una ISO (la ISO ha una lista suo propria, per esempio Ubuntu installa `ubuntu-desktop-minimal`). Decidere il metapacchetto di Ubuntu (completo o minimal) e, se si vuole fedeltà vera, l'immagine dal `casper/*.squashfs`. Peso **medio** (decisione + lavoro). Cura nota: sì come idea (BOX-01), no come codice.

## Che cosa non si può sapere senza provare

- Se ngtcp2 1.25 / nghttp3 1.18 compilano con gcc 15 + cmake 4.2 + OpenSSL 3.5.5 di Ubuntu (alto grado di fiducia, ma non costruito).
- Il risultato di lintian 2.129 sul pacchetto vero, e se il pacchetto è riproducibile bit per bit.
- L'ordine effettivo delle righe in `common-session` dopo `pam-auth-update` con la nostra riga, per ciascun gusto con il desktop completo.
- Come reagisce un box **avviato con systemd** quando un `apt` tira dentro `firefox`/`snapd` (preinst che trova `snapd.socket`): il pin -1 evita la domanda ma non l'abbiamo provato avviato.
- Se un box Ubuntu con systemd 259 e `--network=host` accetta `snapd.service`/`apparmor.service` senza rumore (units fallite in `systemctl --failed`, come i `degraded` visti per il box Debian).
- Se `universe` è abilitato sulle quattro live ufficiali, e quanto spazio ha l'overlay in RAM.
- Se la VM con `virtio-vga` offre un `renderD128` sul nucleo di Ubuntu cloud e se serve ancora OVMF per la scheda passata; se l'immagine cloud Ubuntu parte in BIOS con `genisoimage`+`cidata` come quella Debian.
- Quale lista di pacchetti installa davvero ciascuna ISO live (è una selezione, non il metapacchetto intero).
- Se l'enforce di AppArmor su Ubuntu rompe `remotix_network` (non misurabile in contenitore: il kernel dell'host è Debian).

## Prove consigliate

(Tutte da fare solo quando il proprietario dà il via.)
1. **Costruzione**: `build-deb.sh` adattato su Ubuntu, `TWICE=1`, con lettura di `controlli.txt` e `lintian.txt`; confronto con la costruzione Debian.
2. **Immagini dei box**: costruire una per volta (xubuntu per prima: è quella che aveva il guaio) e far girare `box-identity.sh ubuntu 26.04 <de> -`; confrontare con la tabella 3.2 (DM, sessioni, `x-session-manager`).
3. **Installazione del `.deb`** sui quattro box puliti (`box.sh install`), con `apt` completo e con `--no-install-recommends`; poi `check-package.py` (install/remove/purge) e `check-prelocal.py` per l'ordine in `common-session`.
4. **Box avviato con systemd**: `systemctl --failed`, presenza di `snapd`, esito di `apt install firefox` con e senza pin.
5. **VM**: cloud image con `virtio-vga` e il metapacchetto di un gusto; verificare che il `preinst` passi.
6. **Live** (proprietario): le quattro ISO 26.04.1; `apt install ./remotix_1.0.0-1+ubuntu26.04_amd64.deb`; verificare universe, spazio e il comportamento con la sessione locale già attiva.
