# remotix-install.spec — il motore d'installazione di REMOTIX, per la famiglia .rpm.
#
# Il motore è un binario Go STATICO (CGO_ENABLED=0): lo stesso file per Fedora, Alma e openSUSE,
# costruito da installatore/costruisci.sh; qui lo si impacchetta soltanto (nessuna dipendenza
# dinamica da calcolare). Lo costruisce packaging/archivio/pacchetti-motore.sh, chiamato dal
# comando di rilascio (packaging/rilascio.sh). Il catalogo sta DENTRO il binario (DECISIONI §10.21).
#
# ⛔ DECISIONI §10.12: il pacchetto non accende niente. D14 (§10.23): niente timer — REMOTIX si
#    aggiorna col sistema.

%global debug_package %{nil}
# ⛔ niente brp-strip: il binario del pacchetto resta BYTE PER BYTE quello dell'archivio, il cui
#    sha256 è pubblicato (motore/remotix-install.sha256): `[M]` 30 set, fedora44, lo strip di rpm
#    lo cambiava.
%global __os_install_post %{nil}

Name:           remotix-install
Version:        %{rx_versione}
Release:        %{rx_rilascio}
Summary:        Il motore d'installazione di REMOTIX
License:        LicenseRef-Proprietary
URL:            https://github.com/nic-fio/REMOTIX
Source0:        remotix-install
Source1:        LEGGIMI
ExclusiveArch:  x86_64

%description
Il motore d'installazione di REMOTIX (un solo programma): installa, verifica, certifica e
disinstalla. Porta dentro di sé il catalogo delle combinazioni supportate, che si aggiorna con
questo pacchetto.

%prep

%build

%install
install -D -m 0755 %{SOURCE0} %{buildroot}%{_bindir}/remotix-install
install -D -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/remotix-install/LEGGIMI

%posttrans
# dopo un aggiornamento: annota le versioni, dice se l'installazione è ancora certificata
# (DECISIONI §10.12 punto 4, §10.23). ⛔ Non fa mai fallire la transazione.
%{_bindir}/remotix-install aggiornato || :

%files
%{_bindir}/remotix-install
%dir %{_datadir}/remotix-install
%{_datadir}/remotix-install/LEGGIMI
