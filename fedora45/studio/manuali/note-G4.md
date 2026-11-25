# Note G4 — capitoli ch15–ch18 del manuale tecnico di Fedora 45 (25 nov 2026)

Scritto dal gruppo G4. File toccati: solo `manuals/sources/technical-fedora45/ch15_package.py … ch18_build.py`.
`build.py --check` si ferma alla mappa dei file (ch23_map.py, atteso); i miei file sono stati controllati a mano
contro i nomi di `check-iniziale.md` (nessun file inesistente citato in `<code>`, tranne dove il testo dice espressamente
che «non esiste» e il nome è in `sysf()`).

## 1. Titoli cambiati, aggiunti, tolti (rimandi `rif()` da sistemare negli altri capitoli)

TITOLI RINOMINATI (obbligatori: contenevano Ubuntu, .deb, build-deb.sh, debian/rules):
- «What was verified on Ubuntu 26.04, and what was not» → «What was verified on Fedora 45, and what was not» (rif: ch15 no, ch17 ×4 in Ubuntu)
- «The build of the .deb in one container» → «The RPM build on the build VM»
- «What build-deb.sh does, step by step» → «What build-rpm.sh does, step by step» (rif in ch15 dell'Ubuntu)
- «debian/rules: the overrides and the guards» → «The spec file: %build, %install and the guards» (rif in ch15 dell'Ubuntu)
- «Our own labwc (KDE)» → «KDE with KWin alone» (9 rimandi di Ubuntu: ch12, ch14, ch15 ×2, ch16, ch18 ×3: G1–G3/G5 devono aggiornarli)

TITOLI TOLTI:
- «The four test boxes» (ch17): nessun contenitore su Fedora. I rimandi di ch17 sono stati riscritti; restano da sistemare quelli dei capitoli di altri gruppi, se ce ne sono.
- «The real-system virtual machine» (ch17): `server/vm.sh` non esiste su Fedora.

TITOLI AGGIUNTI:
- ch15: «The SELinux module», «The PAM service file on Fedora», «The local-login hook on four login screens», «KDE with KWin alone» (al posto di labwc), «What the administrator provides» (codec, firewall, SELinux, orologio, desktop).
- ch17: «The checks born on Fedora», «Testing the real machine from a live USB».

TITOLI CONSERVATI anche se il testo cambia: «The preinst refusals», «The postinst: user, folders and encoding test», «Removal: prerm, postrm and purge» (l'inventario li suggeriva da rinominare ma non li dava obbligatori; il testo dice che sono `%pre`, `%post`, `%preun/%postun`; se il coordinatore vuole rinominarli vanno aggiornati i rimandi di tutti i gruppi), «The package checks R4, R13, R14, R23 and R24» (nel testo dico che su Fedora sono attivi solo R4, R13, R24), «The build image and the static QUIC libraries» (non c'è immagine: la sezione lo dice).

## 2. Cose non verificate (dichiarate nel testo come tali)

- Cifre del pacchetto 1.2.0 (numero di voci dell'rpm, librerie legate, versioni del toolchain e di OpenSSL): pacchetto non ancora ricostruito, nessun `controlli.txt` letto. Il testo rimanda al `controlli.txt` di `build-rpm.sh`.
- Estratto di giornale di una partenza vera su Fedora: nessuno (giornali in `~/remotix-prove-live/` e sul server non letti). La sezione «The startup declarations» descrive la riga dei muri di Fedora dal codice (`walls.c`), non da un giro.
- Se `power-implied` e `power-local-seat` passano su Fedora; se il drop-in needrestart ha effetto su Fedora (needrestart non è di serie); la procedura `remotix-pam-hook remove` come comando dell'amministratore; rifiuto «senza scheda» del `%pre`; aarch64.
- Se P7/P8 di `check-prelocal.py` entrano nei 900 s di `all.sh`; il percorso esatto dei log dei giri Fedora.
- uid dell'utente `remotix` su Fedora; il Makefile si ferma con messaggio chiaro se manca `libselinux-devel`? (non verificato, `make deps` non lo controlla).
- Priorità giornale delle righe nate su Fedora (⏳, ⛔ KDE, 44–47): lette dal codice con la regola della testa, non misurate.

## 3. Difetti dei SORGENTI da decidere (NON toccati, NON descritti come funzioni nel manuale)

- `src/main.c:467-473`: messaggio «Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch». Il manuale lo cita come testo vero del programma e dice che su Fedora il file è `/etc/pam.d/remotix`.
- `src/main.c:1189-1192`: il messaggio dice `--no-install-recommends` (opzione di apt); su Fedora è `--setopt=install_weak_deps=False`. Il manuale lo dice.
- `src/session.c` messaggi D-015: citano ancora il pacchetto `dconf-cli` (su Fedora è `dconf`). Il manuale lo dice.
- `rpm/remotix.service` (commento prima di `KillMode`), `rpm/remotix.spec:220`, `rpm/remotix.tmpfiles:1`: commenti vecchi («i desktop restano vivi», «created by postinst»). Il manuale ne parla come «Stale wording».
- `src/remotix-remote-sessions.rules`: il commento dice «five actions», ne ha sei su Fedora (fwupd). Il manuale dice sei.
- `src/kwin.c`, `src/main.c` (`--kwin-nested`), `src/Makefile` (`REMOTIX_LABWC`): codice labwc-per-KDE raggiungibile solo in teoria (F7). Il manuale lo dice «non raggiungibile, da togliere», non come funzione.
- `server/live-installa.sh`: `PACCHETTO=remotix-1.0.1-1.fc45.x86_64.rpm` in testa, da portare a 1.2.0 prima di un nuovo uso (detto nel testo).
- `prove/check-package.py`, `package-snap.py`, `fresh.sh`, `banco-vm/fresh-vm.sh`, `matrix.sh`: ancora di Ubuntu, non funzionano su Fedora (detto nel testo). `prove/check-prelocal.py` ha ancora il docstring con `common-session`.
- `prove/lib.py` `sweep()` non conosce i prefissi `kx kr kb` né `pl3`; il testo lo dichiara.
- `LICENSE.md`: l'inventario (T6) diceva che al righe 95–97 parlava ancora del labwc di Ubuntu; PIANO.md dice che il 25 nov è stato corretto. Nel testo scrivo solo che è stato corretto (come dice PIANO.md), senza averlo riletto.

## 4. Punti da far leggere al revisore

- ch15 «Removal»: ordine in `%preun` diverso da Debian (PAM tolta dopo l'arresto del servizio); non esiste purge.
- ch17 «What was verified on Fedora 45»: tabella dei giri costruita solo da PIANO.md e registro; le cifre (52/76/60/60, 25/25, 78, 64) sono quelle scritte lì, con data, non ricontate.
- Conteggio ricontato: 127 righe di verdetto per desktop (prelocal 8 invece di 6), 19 azioni polkit di spegnimento, 24 chiavi dconf (12 VT + 12), 6 azioni «refresh» nella regola 40-.


## Correzioni del 25 nov 2026 (dopo la revisione)
- I punti 1-3 del §3 non sono piu veri: il 25 nov i sorgenti sono stati corretti (PIANO.md:524-527). `src/main.c`: il messaggio PAM finisce con «The package installs that file: reinstall the package (sudo dnf reinstall remotix)»; `--setopt=install_weak_deps=False` e gia nel testo di `session_missing_component()`; i messaggi D-015 di `session.c` dicono «package dconf» o non nominano pacchetti. Il manuale ora dice questo.
- §4: le azioni polkit sul lato refresh sono 4 (3 + fwupd), piu 2 di `machine`: sei in tutto, non «sei sul lato refresh».
