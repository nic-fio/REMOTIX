# remotix-install.spec — the REMOTIX installation engine, for the .rpm family.
#
# The engine is a STATIC Go binary (CGO_ENABLED=0): the same file for Fedora, Alma and openSUSE,
# built by installatore/costruisci.sh; here it is only packaged (no dynamic dependency
# to compute). Built by packaging/motore/pacchetti-motore.sh, called by the
# release command (packaging/rilascio.sh). The catalogue lives INSIDE the binary (DECISIONI §10.21).
#
# ⛔ DECISIONI §10.12: the package enables nothing. D14 (§10.23): no timer — REMOTIX
#    updates with the system.

%global debug_package %{nil}
# ⛔ no brp-strip: the package binary stays BYTE FOR BYTE the one in the .run (the same
#    engine that installed it): `[M]` 30 Sep, fedora44, rpm's strip changed it.
%global __os_install_post %{nil}

Name:           remotix-install
Version:        %{rx_versione}
Release:        %{rx_rilascio}
Summary:        The REMOTIX installation engine
License:        LicenseRef-Proprietary
URL:            https://github.com/nic-fio/REMOTIX
Source0:        remotix-install
Source1:        README
ExclusiveArch:  x86_64

%description
The REMOTIX installation engine (a single program): installs, checks, certifies and
uninstalls. It carries inside it the catalogue of supported combinations, which is updated with
this package.

%prep

%build

%install
install -D -m 0755 %{SOURCE0} %{buildroot}%{_bindir}/remotix-install
install -D -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/remotix-install/README

%posttrans
# after an upgrade: records the versions, says whether the installation is still certified
# (DECISIONI §10.12 point 4, §10.23). ⛔ It never makes the transaction fail.
%{_bindir}/remotix-install post-upgrade || :

%files
%{_bindir}/remotix-install
%dir %{_datadir}/remotix-install
%{_datadir}/remotix-install/README
