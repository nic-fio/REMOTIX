# remotix.spec — il pacchetto nativo di REMOTIX per la famiglia .rpm.
#
#   Fedora 44 · Alma 10 (Rocky/RHEL 10 compatibili) · openSUSE Tumbleweed · Leap 16
#
# ⭐ UN solo spec coi rami %%if, come fa Cockpit (`tools/cockpit.spec`):
#    0%%{?fedora} · 0%%{?rhel} · 0%%{?suse_version}.  `fasi/17-l-installatore.md`
#    §6.1-§6.4.  Si costruisce DENTRO il contenitore di ogni bersaglio
#    (`src/costruzione/Contenitore.<bersaglio>`) con `packaging/rpm/costruisci-rpm.sh`.
#
# ⭐ Le librerie le calcola rpmbuild leggendo il binario (le «Requires» automatiche
#    per soname: libavcodec, libssl, libpam, libpipewire, libei, libva, …): e' la
#    cura di `LEZIONI.md` §2.5-bis.  Qui sotto si scrive A MANO solo quel che rpm
#    NON puo' vedere, perche' si carica o si esegue a tempo di esecuzione: il
#    compositore per XFCE/LXQt, wlr-randr, Xwayland, lo sfondo di Plasma, i
#    driver VA-API.  (OpenSSL >= 3.5 lo vede da se': `libssl.so.3(OPENSSL_3.5.0)`.)
#
# ⭐ `DECISIONI.md` §10.12 — il pacchetto porta solo pezzi INERTI (programma,
#    pagina, unita' disabilitata, PAM, /etc/remotix, le cinture SPENTE in
#    /usr/share/remotix/cinture/, la definizione firewalld).  Non abilita ne' avvia il servizio, non tocca gruppi, cinture ne'
#    firewall: li monta il motore, col consenso e nel suo registro (R40).
#    ⛔ Nessuna guardia che impedisca al servizio di partire (niente
#    ExecCondition, niente ConditionPathExists su una marca): le vie sono DUE,
#    l'installatore o il sorgente a mano; `remotix stato` dira' solo, per
#    informazione, se l'installazione e' certificata.
#
# ⛔ Mai nel pacchetto (§6.4, R14): utenti di prova, `sudoers.d` dei banchi,
#    `gpu-udev.sh`, `riavvia-*.sh`, `ld.so.conf.d`, `provisiona.sh`.
# ⛔ Il pacchetto non tira MAI dentro un desktop (`DECISIONI.md` §10.7: senza
#    desktop lo installa il motore): le dipendenze legate a un desktop sono
#    CONDIZIONATE, `(X if <sessione del desktop>)`.
# ⛔ Il pacchetto non aggiunge MAI depositi (RPM Fusion, Packman, EPEL): §4.2
#    regola 2 e D5.  Lo fara' il motore d'installazione, col consenso.

%global ngtcp2_ver  1.25.0
%global nghttp3_ver 1.18.0

# openSUSE tiene i file PAM dei pacchetti in /usr/lib/pam.d (§4.3)
%if 0%{?suse_version}
%{!?_pam_vendordir: %global _pam_vendordir %{_prefix}/lib/pam.d}
%global pamdir      %{_pam_vendordir}
%global pamsorgente remotix.pam.suse
%else
%global pamdir      %{_sysconfdir}/pam.d
%global pamsorgente remotix.pam.fedora
%endif

Name:           remotix
# La versione e il rilascio li dà il comando di rilascio (packaging/rilascio.sh) attraverso
# costruisci-rpm.sh: RX_VERSIONE (--define "rx_versione X.Y.Z") e RX_REVISIONE
# (--define "rx_rilascio N"); predefiniti 0.17.0 e 1.
Version:        %{?rx_versione}%{!?rx_versione:0.17.0}
Release:        %{?rx_rilascio}%{!?rx_rilascio:1}%{?dist}
Summary:        Il desktop di questa macchina nel browser
# ⚠ La licenza del prodotto non e' ancora scelta (deposito privato).
License:        LicenseRef-Proprietary
URL:            https://github.com/nic-fio/REMOTIX
# Un archivio di src/, banchi/rcp/ (la copia gemella che `make` confronta) e
# packaging/rpm/, fatto da `costruisci-rpm.sh`.
Source0:        %{name}-%{version}.tar.gz

ExclusiveArch:  x86_64

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconfig
BuildRequires:  systemd-rpm-macros
BuildRequires:  pam-devel
BuildRequires:  pkgconfig(openssl) >= 3.5.0
BuildRequires:  pkgconfig(gio-2.0) >= 2.80
BuildRequires:  pkgconfig(libpipewire-0.3) >= 0.3.48
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libva)
BuildRequires:  pkgconfig(libavcodec) >= 61.13.100
BuildRequires:  pkgconfig(libavutil) >= 59
BuildRequires:  pkgconfig(libswscale) >= 8
BuildRequires:  pkgconfig(libei-1.0) >= 1.1.0
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-scanner)
BuildRequires:  pkgconfig(gbm)
# ⚠ ngtcp2 >= 1.25.0 e nghttp3: NON sono un BuildRequires, perche' quasi nessuna
#   distribuzione le ha (§6.3).  Le costruisce il contenitore, SOLO statiche, in
#   /usr/local/lib (`src/costruzione/quic-statiche.sh`); %%build controlla che ci
#   siano e che la versione sia quella dichiarata qui sotto.
# ⭐ D2 CHIUSA (`DECISIONI.md` §10.6): ngtcp2 e nghttp3 DENTRO il binario, con gli
#   aggiornamenti di sicurezza a carico nostro — quel che manca o e' troppo
#   vecchio lo porta REMOTIX, salvo i codec brevettati e i desktop.
Provides:       bundled(ngtcp2) = %{ngtcp2_ver}
Provides:       bundled(nghttp3) = %{nghttp3_ver}

# ⭐ SELinux (T6, `DECISIONI.md` §10.18): il PAM di REMOTIX e' quello di sshd, con
#    `pam_selinux`; il passaggio al contesto dell'utente lo permette il modulo di
#    REMOTIX, nel sottopacchetto remotix-selinux (come cockpit-ws-selinux).  Lo tira
#    dentro il gestore di pacchetti SOLO dove c'e' la politica «targeted»: Fedora,
#    Alma, openSUSE (Tumbleweed e Leap 16 sono in enforcing di serie).
%global selinuxtype targeted
BuildRequires:  selinux-policy-devel
BuildRequires:  bzip2
Requires:       (%{name}-selinux = %{version}-%{release} if selinux-policy-%{selinuxtype})

%if 0%{?fedora} || 0%{?rhel}
# Il servizio firewalld e' DEFINITO nella cartella di firewalld-filesystem (niente
# demone, niente regole): aprirlo e' del motore, col consenso (D6).
Requires:       firewalld-filesystem
%endif

%if 0%{?fedora}
# XFCE e LXQt girano sotto labwc (REMOTIX lo avvia; nessun gruppo di serie lo porta,
# §4.6).  xfce4-session 4.20 e' X11: sotto labwc vuole Xwayland.  LXQt: la misura
# del monitor passa da wlr-randr (`primario_lxqt()`).  Dipendenze CONDIZIONATE:
# solo se quel desktop c'e'.
Requires:       (labwc if xfce4-session)
Requires:       (xorg-x11-server-Xwayland if xfce4-session)
Requires:       (labwc if lxqt-session)
Requires:       (wlr-randr if lxqt-session)
# labwc MUORE senza un carattere scalabile (labwc #2525: con i soli caratteri
# bitmap la barra del titolo esce alta 1,4 milioni di pixel e `buffer.c:90`
# abortisce).  Su Fedora i gruppi dei desktop lo portano, ma una macchina con
# labwc e senza desktop di serie no: il sans di serie della distribuzione.
Requires:       (default-fonts-core-sans if labwc)
# I driver VA-API: si caricano con dlopen, rpm non li vede.  Su Fedora il driver
# Mesa (AMD, virtio) sta in mesa-dri-drivers, quello Intel libero in
# libva-intel-media-driver.  ⚠ NESSUNO dei due codifica H.264 di serie (§4.2):
# serve RPM Fusion (mesa-va-drivers-freeworld / intel-media-driver), che il
# pacchetto NON aggiunge (D5).  Recommends: sulla macchina senza scheda Intel il
# driver Intel non serve, e chi li toglie non deve rompere il pacchetto.
Recommends:     mesa-dri-drivers
Recommends:     (libva-intel-media-driver or intel-media-driver)
%endif

%if 0%{?rhel}
# ⚠ Alma/RHEL 10: libavcodec-free sta in EPEL 10 (con CRB): senza EPEL la
#   dipendenza automatica su libavcodec.so.61 non si risolve e l'installazione
#   si ferma.  Il pacchetto NON aggiunge EPEL: e' un passo del motore (§6.0).
# ⛔ Niente labwc/XFCE/LXQt in RHEL/EPEL 10 (§3): nessuna dipendenza da scrivere.
# ⛔ Mesa di RHEL 10 e' senza VA-API e EPEL non ha il driver Intel (§4.2): la
#   codifica sulla scheda c'e' solo con depositi di terzi.
%endif

%if 0%{?suse_version}
Requires:       (labwc if xfce4-session)
Requires:       (xwayland if xfce4-session)
Requires:       (labwc if lxqt-session)
Requires:       (wlr-randr if lxqt-session)
# ⛔ labwc MUORE senza un carattere scalabile (labwc #2525, `buffer.c:90`): il
# gruppo LXQt di openSUSE porta `google-droid-fonts` solo come RACCOMANDATO, e
# sulle installazioni senza raccomandati non c'e'.  Uno qualunque dei sans scalabili.
Requires:       ((google-droid-fonts or dejavu-fonts or google-noto-sans-fonts or liberation-fonts) if labwc)
# `[M]` T1 (§11.1 D): senza breeze6-wallpapers plasmashell non trova lo sfondo e
# non mostra ne' desktop ne' pannello (tela nera).  Sulle installazioni senza
# «raccomandati» (l'immagine Minimal, `solver.onlyRequires`) il gruppo KDE non lo porta.
Requires:       (breeze6-wallpapers if plasma6-workspace)
# driver VA-API (dlopen).  ⚠ La ffmpeg di openSUSE non ha h264_vaapi (§4.2): senza
# Packman REMOTIX non codifica su nessuna scheda.  Il pacchetto NON aggiunge Packman (D5).
Recommends:     Mesa-libva
Recommends:     intel-media-driver
%endif

%description
REMOTIX porta il desktop di questa macchina (GNOME, KDE Plasma, XFCE, LXQt) in
un browser, con WebTransport e video H.264 codificato sulla scheda grafica.
Ogni utente della macchina entra con la sua parola d'ordine; root no.

⚠ La codifica H.264 usa i codec e i driver della distribuzione: su Fedora e
openSUSE servono RPM Fusion o Packman, che questo pacchetto non aggiunge.

%package selinux
Summary:        Il modulo SELinux di REMOTIX
BuildArch:      noarch
Requires(post): selinux-policy-%{selinuxtype}
Requires(post): selinux-policy-base
Requires(post): libselinux-utils
Requires(post): policycoreutils

%description selinux
Il modulo SELinux del servizio REMOTIX: il dominio remotix_t, la porta 7447
(remotix_port_t) e il passaggio al contesto dell'utente all'apertura della
sessione, come per sshd.

%prep
%autosetup -n %{name}-%{version}

%build
# ⛔ Le statiche di ngtcp2/nghttp3 devono esserci, e della versione dichiarata:
#    un binario con una ngtcp2 diversa da quella di `Provides: bundled(...)`
#    sarebbe uno SBOM che mente (R24).
for l in libngtcp2 libngtcp2_crypto_ossl libnghttp3; do
    pkg-config --exists $l || { echo "⛔ $l: manca (si costruisce nei contenitori di src/costruzione/)"; exit 1; }
done
test "$(pkg-config --modversion libngtcp2)"  = %{ngtcp2_ver}  || { echo "⛔ ngtcp2 $(pkg-config --modversion libngtcp2), dichiarata %{ngtcp2_ver}"; exit 1; }
test "$(pkg-config --modversion libnghttp3)" = %{nghttp3_ver} || { echo "⛔ nghttp3 $(pkg-config --modversion libnghttp3), dichiarata %{nghttp3_ver}"; exit 1; }
# I flag della distribuzione (FORTIFY, PIE, protezione dello stack, …) NELL'AMBIENTE:
# il Makefile ha `CFLAGS ?=` e poi `CFLAGS +=`.  Passati sulla riga di comando di
# make scavalcherebbero anche i `+=` (e sparirebbero le intestazioni di ffmpeg).
cd src
export CFLAGS="%{optflags} -std=gnu11 -Wall -Wextra -Wno-unused-parameter"
export LDFLAGS="%{?build_ldflags}"
%if 0%{?suse_version}
# openSUSE: %%{optflags} non chiede PIE (rpmlint: position-independent-executable-suggested)
CFLAGS="$CFLAGS -fPIE"; LDFLAGS="$LDFLAGS -pie"
%endif
make pulisci >/dev/null
make %{?_smp_mflags} tutto
cd ..

# Il modulo SELinux, con le interfacce della politica di QUESTA distribuzione.
# ⚠ `--define "rx_selinux_permissivo 1"` (costruisci-rpm.sh: RX_SELINUX_PERMISSIVO=1)
#   costruisce il modulo col dominio in «permissive»: per MISURARE i rifiuti di una
#   sessione intera in un giro solo.  ⛔ Mai in un pacchetto pubblicato.
cd packaging/rpm/selinux
%{?rx_selinux_permissivo:echo 'permissive remotix_t;' >> remotix.te}
make -f %{_datadir}/selinux/devel/Makefile remotix.pp
bzip2 -9 remotix.pp
cd ../../..

%install
install -D -m 0755 src/remotix %{buildroot}%{_libexecdir}/remotix/remotix
install -D -m 0644 src/pagina.html %{buildroot}%{_datadir}/remotix/pagina.html
# I PREDEFINITI (porta, opzioni): del pacchetto, un aggiornamento li riscrive.
# Le scelte dell'amministratore in /etc/remotix/remotix.conf.d/*.conf (vincono).
install -D -m 0644 packaging/rpm/remotix.conf %{buildroot}%{_datadir}/remotix/remotix.conf
# R24 (T8): le versioni delle statiche COLLEGATE (pkg-config nel contenitore di
# costruzione), per lo SBOM dell'archivio.
printf '{"formato":"remotix-incorporate/1","ngtcp2":"%s","nghttp3":"%s","fonte":"pkg-config delle .a collegate"}\n' \
    "$(pkg-config --modversion libngtcp2)" "$(pkg-config --modversion libnghttp3)" \
    > %{buildroot}%{_datadir}/remotix/incorporate.json
install -D -m 0644 packaging/rpm/remotix.service %{buildroot}%{_unitdir}/remotix.service
install -D -m 0644 packaging/rpm/remotix.tmpfiles %{buildroot}%{_tmpfilesdir}/remotix.conf
install -D -m 0644 src/%{pamsorgente} %{buildroot}%{pamdir}/remotix

# /etc/remotix: chi e' escluso (il PAM ha onerr=fail: senza il file non entra
# nessuno, quindi il file arriva col pacchetto e non si tocca se cambiato), e la
# cartella delle scelte dell'amministratore (vuota: il formato e' del motore, T4).
install -d -m 0755 %{buildroot}%{_sysconfdir}/remotix/remotix.conf.d
printf 'root\n' > %{buildroot}%{_sysconfdir}/remotix/utenti-negati
chmod 0644 %{buildroot}%{_sysconfdir}/remotix/utenti-negati

# Il permesso di cattura di KWin (`zkde_screencast_unstable_v1`): KWin lo cerca in
# XDG_DATA_DIRS.  ⚠ Oggi lo scrive ANCHE il programma, da root, mentre gira
# (`src/kwin.c:48`, `kwin_scrivi_permesso()`): il contenuto qui e' identico byte
# per byte a quello che scriverebbe, quindi non lo riscrive.  ⇒ Da cambiare nel C
# (§4.4): a esecuzione solo la verifica (`kwin.c:342`).  Non cambiato in T3.
install -D -m 0644 packaging/rpm/org.kde.remotix.desktop %{buildroot}%{_datadir}/applications/org.kde.remotix.desktop

# ⭐ `DECISIONI.md` §10.12 — l'installatore e' l'unica via: le tre cinture di
#   §4.7 (niente spegnimento, niente sospensione, i tasti non spengono) arrivano
#   SPENTE, fuori dai percorsi che polkit e systemd leggono.  Le monta il motore,
#   col consenso (D4 aperta: sempre, o scelta dell'amministratore?) e nel suo
#   registro; i percorsi dove andranno sono quelli del FORNITORE
#   (/usr/share/polkit-1/rules.d/50-…, /usr/lib/systemd/{logind,sleep}.conf.d/),
#   mai /etc: un file dell'amministratore con lo stesso nome in /etc vince (R34).
install -D -m 0644 src/remotix-niente-spegnimento.rules %{buildroot}%{_datadir}/remotix/cinture/50-remotix-niente-spegnimento.rules
install -D -m 0644 src/remotix-tasti.conf %{buildroot}%{_datadir}/remotix/cinture/remotix-tasti.conf
install -D -m 0644 packaging/rpm/remotix-niente-sospensione.conf %{buildroot}%{_datadir}/remotix/cinture/remotix-niente-sospensione.conf

# firewalld: il servizio «remotix» DEFINITO, non aperto (D6, §10.12): il file
# rende noto un nome a firewalld e non cambia nessuna zona.  L'apertura
# (`firewall-cmd --permanent --add-service=remotix`) e' del motore, col consenso.
install -D -m 0644 packaging/rpm/remotix-firewalld.xml %{buildroot}%{_prefix}/lib/firewalld/services/remotix.xml

# remotix-selinux: il modulo (il dominio) e la porta (portcon, in CIL)
install -D -m 0644 packaging/rpm/selinux/remotix.pp.bz2 %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/remotix.pp.bz2
install -D -m 0644 packaging/rpm/selinux/remotix_porta.cil %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/remotix_porta.cil

# I file che il servizio genera da se': dichiarati %%ghost, cosi' li conosce rpm
# e la disinstallazione li toglie (origine DIRETTA, §6.6.4).  `[M]` T3 su
# Tumbleweed: senza i due `.nostro` (le marche di `certificati.c:317,320`)
# /var/lib/remotix restava dopo `zypper remove`.
install -d -m 0700 %{buildroot}%{_sharedstatedir}/remotix/certificati
for f in pagina.pem pagina.key pagina.nostro sessione.pem sessione.key sessione.nostro; do
    touch %{buildroot}%{_sharedstatedir}/remotix/certificati/$f
done
touch %{buildroot}%{_sharedstatedir}/remotix/ban %{buildroot}%{_sharedstatedir}/remotix/ban.nuovo

# ⭐ `DECISIONI.md` §10.12 — gli scriptlet NON accendono niente (R40):
#   · niente %%systemd_post / %%service_add_post: applicherebbero il «preset»
#     della macchina, e con un preset «enable *» il servizio si abiliterebbe da
#     solo.  L'accensione (`systemctl enable --now`) e' del motore;
#   · niente gruppi della scheda: li mette il motore (`aggiungi-utente-a-gruppo`),
#     col suo registro;
#   · niente cinture, niente firewall, niente `systemctl reload systemd-logind`.
#   systemd rilegge da se' le unita' nuove (i trigger di file di systemd).

%post
# Solo la cartella /var/lib/remotix (0700), che rpm crea gia' col %%dir: inerte.
%tmpfiles_create remotix.conf

%preun
# Alla disinstallazione: se il motore l'aveva acceso, si ferma e si disabilita
# (niente resta abilitato a puntare a un file che non c'e' piu').
%if 0%{?suse_version}
%service_del_preun remotix.service
%else
%systemd_preun remotix.service
%endif

%postun
# All'aggiornamento: `try-restart`, cioe' SOLO se era gia' acceso (T2, §5.2, T7:
# i desktop sopravvivono, il servizio nuovo li ritrova, chi e' collegato
# riattacca).  REMOTIX si aggiorna col sistema (DECISIONI §10.23): dnf upgrade,
# zypper up.
%if 0%{?suse_version}
%service_del_postun remotix.service
%else
%systemd_postun_with_restart remotix.service
%endif

%posttrans
# Dopo la transazione (anche remotix-install e' gia' al suo posto): il motore
# annota le versioni e dice se l'installazione e' ancora certificata
# (DECISIONI §10.12 punto 4, §10.23).  ⛔ Non fa mai fallire la transazione.
if [ -x /usr/bin/remotix-install ]; then
	/usr/bin/remotix-install aggiornato || :
fi

%files
%dir %{_libexecdir}/remotix
%{_libexecdir}/remotix/remotix
%dir %{_datadir}/remotix
%{_datadir}/remotix/pagina.html
%{_datadir}/remotix/remotix.conf
%{_datadir}/remotix/incorporate.json
%dir %{_datadir}/remotix/cinture
%{_datadir}/remotix/cinture/50-remotix-niente-spegnimento.rules
%{_datadir}/remotix/cinture/remotix-tasti.conf
%{_datadir}/remotix/cinture/remotix-niente-sospensione.conf
%{_unitdir}/remotix.service
%{_tmpfilesdir}/remotix.conf
%if 0%{?suse_version}
# /usr/lib/pam.d e' del fornitore: l'amministratore la cambia con un suo
# /etc/pam.d/remotix, che vince.  Nessun %%config.
%{pamdir}/remotix
%else
%config(noreplace) %{pamdir}/remotix
%endif
%dir %{_sysconfdir}/remotix
%dir %{_sysconfdir}/remotix/remotix.conf.d
%config(noreplace) %{_sysconfdir}/remotix/utenti-negati
%{_datadir}/applications/org.kde.remotix.desktop
%if 0%{?suse_version}
%dir %{_prefix}/lib/firewalld
%dir %{_prefix}/lib/firewalld/services
%endif
%{_prefix}/lib/firewalld/services/remotix.xml
%ghost %dir %attr(0700,root,root) /run/remotix
%dir %attr(0700,root,root) %{_sharedstatedir}/remotix
%dir %attr(0700,root,root) %{_sharedstatedir}/remotix/certificati
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificati/pagina.pem
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificati/pagina.key
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificati/sessione.pem
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificati/sessione.key
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificati/pagina.nostro
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificati/sessione.nostro
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/ban
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/ban.nuovo

# ⭐ remotix-selinux: gli scriptlet sono quelli della politica (come cockpit-ws-selinux).
#   Il modulo si carica e basta: non accende niente (R40).  Il ricalcolo delle etichette
#   si fa in %%posttrans, quando anche i file di remotix sono al loro posto (nella stessa
#   transazione rpm li scrive con le etichette di PRIMA del modulo).
%pre selinux
%selinux_relabel_pre -s %{selinuxtype}

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/remotix.pp.bz2 %{_datadir}/selinux/packages/%{selinuxtype}/remotix_porta.cil

%postun selinux
%selinux_modules_uninstall -s %{selinuxtype} remotix_porta remotix

%posttrans selinux
%selinux_relabel_post -s %{selinuxtype}

%files selinux
%{_datadir}/selinux/packages/%{selinuxtype}/remotix.pp.bz2
%{_datadir}/selinux/packages/%{selinuxtype}/remotix_porta.cil
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/remotix
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/remotix_porta

%changelog
* Wed Sep 30 2026 nicfio <nicfio@gmail.com> - 0.17.0-1
- Fase 17, T6: il PAM di sshd (D3), il sottopacchetto remotix-selinux.
* Tue Sep 29 2026 nicfio <nicfio@gmail.com> - 0.17.0-1
- Fase 17, T3: il primo pacchetto nativo per Fedora, Alma, Tumbleweed e Leap.
