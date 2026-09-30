# remotix-install.spec — il motore d'installazione di REMOTIX, per la famiglia .rpm (T8).
#
# Il motore è un binario Go STATICO (CGO_ENABLED=0): lo stesso file per Fedora, Alma e openSUSE,
# costruito da installatore/costruisci.sh; qui lo si impacchetta soltanto (nessuna dipendenza
# dinamica da calcolare). Lo costruisce packaging/archivio/pacchetti-motore.sh.
#
# ⛔ DECISIONI §10.12: pezzi INERTI. Il timer degli aggiornamenti c'è ma SPENTO (niente
#    %%systemd_post: applicherebbe il «preset» della macchina); lo accende il motore col consenso.

%global debug_package %{nil}
# ⛔ niente brp-strip: il binario deve restare BYTE PER BYTE quello firmato (catena A, la firma del
#    motore in /usr/share/remotix-install). `[M]` 30 set, fedora44: con lo strip di rpm la firma non
#    corrispondeva più (RX-TRUST-014).
%global __os_install_post %{nil}

Name:           remotix-install
Version:        %{rx_versione}
Release:        %{rx_rilascio}
Summary:        Il motore d'installazione di REMOTIX
License:        LicenseRef-Proprietary
URL:            https://github.com/nic-fio/REMOTIX
Source0:        remotix-install
Source1:        remotix-install.firma
Source2:        remotix-aggiorna.service
Source3:        remotix-aggiorna.timer
Source4:        LEGGIMI
ExclusiveArch:  x86_64

%description
Il motore d'installazione di REMOTIX (un solo programma): installa, aggiorna senza chiudere i
desktop, disinstalla e certifica. Porta il timer degli aggiornamenti automatici, spento finché
il motore non lo accende col consenso.

%prep

%build

%install
install -D -m 0755 %{SOURCE0} %{buildroot}%{_bindir}/remotix-install
install -D -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/remotix-install/remotix-install.firma
install -D -m 0644 %{SOURCE4} %{buildroot}%{_datadir}/remotix-install/LEGGIMI
install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/remotix-aggiorna.service
install -D -m 0644 %{SOURCE3} %{buildroot}%{_unitdir}/remotix-aggiorna.timer

%preun
# alla disinstallazione (non all'aggiornamento) il timer si spegne se qualcuno l'aveva acceso
%systemd_preun remotix-aggiorna.timer

%files
%{_bindir}/remotix-install
%dir %{_datadir}/remotix-install
%{_datadir}/remotix-install/remotix-install.firma
%{_datadir}/remotix-install/LEGGIMI
%{_unitdir}/remotix-aggiorna.service
%{_unitdir}/remotix-aggiorna.timer
