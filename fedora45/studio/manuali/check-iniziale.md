# check --check: stato iniziale (25 nov 2026)

Esito di `build.py --check` sui capitoli ancora di Ubuntu copiati in `manuals/sources/`. Lista di lavoro degli scrittori.
Le contestazioni sono quelle del generatore (percorsi citati in <code> che non esistono in fedora45/); sono attribuite al capitolo cercando il testo nei sorgenti.
Il generatore adesso si FERMA (SystemExit) alla mappa dei file, finché ch23_map.py non è riscritto: per questo l'elenco è stato prodotto con una copia 'tollerante' di build.py (in scratchpad), non con build.py vero.

## Contestazioni generali

- «manuals/Technical Manual — Fedora 45.html» does not match the sources: python3 manuals/sources/build.py
- «manuals/User Manual — Fedora 45.html» does not match the sources: python3 manuals/sources/build.py
  (le prime due spariranno quando i file HTML finali saranno generati in `fedora45/manuals/`; per ora si generano con --outdir.)

## Mappa dei file (technical-fedora45/ch23_map.py)

Fa fallire la generazione. Differenze con l'albero reale di fedora45/: 35 file mancanti nella mappa, 40 citati che non esistono più (boxes/, debian/, build-deb.sh, Containerfile, labwc-ospite, server/vm*.sh di Ubuntu...).
Elenco completo: lanciare build.py (stampa 'missing …' / 'no longer exists …'). File mancanti, per cartella: rpm/ (11), selinux/ (3), prove/ (18 tra check-*, giro-*, wall-*, hold*, banco-vm), build/build-rpm.sh, src/protocols/ (3), src/remotix-pam-hook.

## Percorsi citati che non esistono, per capitolo

### technical-fedora45/ch01_introduction.py (8)
- `build/build-deb.sh`
- `studio/14-canvas-xfce.md`
- `needrestart/remotix.conf`
- `build-deb.sh`
- `vm-radeon-aggiorna.sh`
- `vm-radeon-installa.sh`
- `vm-radeon-controllo.sh`
- `vm.sh`

### technical-fedora45/ch05_rcp.py (3)
- `build/build-deb.sh`
- `build-deb.sh`
- `debian/remotix.service`

### technical-fedora45/ch15_package.py (7)
- `build/build-deb.sh`
- `build-deb.sh`
- `vm-radeon-installa.sh`
- `debian/remotix.service`
- `studio/8-pacchetto-e-prove.md`
- `studio/7-xubuntu-lubuntu.md`
- `server/vm-radeon-installa.sh`

### technical-fedora45/ch17_testing.py (17)
- `build/build-deb.sh`
- `studio/14-canvas-xfce.md`
- `build-deb.sh`
- `vm-radeon-aggiorna.sh`
- `vm-radeon-installa.sh`
- `vm-radeon-controllo.sh`
- `studio/8-pacchetto-e-prove.md`
- `boxes/box.sh`
- `boxes/set-dm.sh`
- `boxes/box-identity.sh`
- `boxes/common.sh`
- `boxes/power.sh`
- `server/vm.sh`
- `vm.sh`
- `server/vm-login-test.py`
- `server/vm-radeon-login-test.py`
- `vm-radeon-login-test.py`

### technical-fedora45/ch18_build.py (8)
- `build/build-deb.sh`
- `needrestart/remotix.conf`
- `build-deb.sh`
- `debian/needrestart/remotix.conf`
- `studio/8-pacchetto-e-prove.md`
- `fetch.sh`
- `labwc-ospite/build.sh`
- `build/labwc-ospite/fetch.sh`

### technical-fedora45/ch20_extending.py (10)
- `build/build-deb.sh`
- `needrestart/remotix.conf`
- `build-deb.sh`
- `debian/needrestart/remotix.conf`
- `studio/8-pacchetto-e-prove.md`
- `fetch.sh`
- `build/labwc-ospite/build.sh`
- `boxes/box.sh`
- `labwc-ospite/build.sh`
- `build/labwc-ospite/fetch.sh`

### technical-fedora45/ch21_conventions.py (8)
- `build/build-deb.sh`
- `build-deb.sh`
- `vm-radeon-aggiorna.sh`
- `vm-radeon-installa.sh`
- `vm-radeon-controllo.sh`
- `server/vm-radeon-installa.sh`
- `server/vm-radeon-controllo.sh`
- `server/vm-radeon-aggiorna.sh`

### technical-fedora45/ch23_map.py (27)
- `build/build-deb.sh`
- `needrestart/remotix.conf`
- `build-deb.sh`
- `vm-radeon-aggiorna.sh`
- `vm-radeon-installa.sh`
- `vm-radeon-controllo.sh`
- `debian/remotix.service`
- `debian/remotix.conf`
- `debian/remotix-no-suspend.conf`
- `debian/needrestart/remotix.conf`
- `fetch.sh`
- `build/labwc-ospite/build.sh`
- `server/vm-radeon-installa.sh`
- `server/vm-radeon-controllo.sh`
- `boxes/box.sh`
- `boxes/set-dm.sh`
- `boxes/box-identity.sh`
- `boxes/common.sh`
- `boxes/power.sh`
- `server/vm.sh`
- `vm.sh`
- `server/vm-login-test.py`
- `server/vm-radeon-login-test.py`
- `vm-radeon-login-test.py`
- `labwc-ospite/build.sh`
- `build/labwc-ospite/fetch.sh`
- `server/vm-radeon-aggiorna.sh`

### technical-fedora45/ch24_problems.py (4)
- `build/build-deb.sh`
- `build-deb.sh`
- `debian/remotix.service`
- `studio/11-riscontro-studi-lavoro.md`

### technical-fedora45/ch06_capture.py (3)
- `studio/14-canvas-xfce.md`
- `studio/10-kde-controprova-labwc.md`
- `fetch.sh`

### technical-fedora45/ch03_lifecycle.py (7)
- `needrestart/remotix.conf`
- `debian/remotix.service`
- `debian/remotix.conf`
- `debian/remotix-no-suspend.conf`
- `studio/1-gnome50-avvio.md`
- `studio/giro2-kde.md`
- `debian/needrestart/remotix.conf`

### technical-fedora45/ch14_security.py (2)
- `needrestart/remotix.conf`
- `debian/needrestart/remotix.conf`

### technical-fedora45/ch16_logging.py (4)
- `vm-radeon-controllo.sh`
- `debian/remotix.service`
- `debian/remotix.conf`
- `server/vm-radeon-controllo.sh`

### technical-fedora45/ch02_architecture.py (2)
- `debian/remotix.service`
- `debian/remotix.conf`

### technical-fedora45/ch04_transport.py (2)
- `debian/remotix.service`
- `studio/8-pacchetto-e-prove.md`

### technical-fedora45/ch08_quality.py (2)
- `debian/remotix.service`
- `debian/remotix.conf`

### technical-fedora45/ch09_page.py (1)
- `debian/remotix.service`

### user-fedora45/ch05_looking_after.py (1)
- `debian/remotix.service`

### technical-fedora45/ch12_desktops.py (8)
- `studio/1-gnome50-avvio.md`
- `studio/3-sessione-ubuntu.md`
- `studio/4-mutter50-cattura-input.md`
- `studio/6-kubuntu-kwin-labwc.md`
- `studio/7-xubuntu-lubuntu.md`
- `build/labwc-ospite/build.sh`
- `studio/giro2-gnome.md`
- `labwc-ospite/build.sh`

### technical-fedora45/ch10_input.py (2)
- `studio/giro2-kde.md`
- `studio/giro2-xfce.md`

## Controlli che NON hanno protestato (da tenere d'occhio)

- Variabili REMOTIX_*, codici RX-…, funzioni citate, testo italiano, link interni, versione: nessuna contestazione (la versione letta dallo spec è 1.0.1).
- Il controllo sui riferimenti dei capitoli a Ubuntu (apt, dpkg, AppArmor, .deb, labwc) NON esiste in build.py: lo scrittore deve cercarli a mano.
