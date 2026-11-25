# Note G5 — capitoli ch19–ch25 del manuale tecnico Fedora 45

Data: 25 nov 2026. Scritto dallo scrittore G5. Cio' che non ho potuto chiudere, i cambi di titolo, i difetti del prodotto emersi (non toccati).

## 1. Titoli di sezione cambiati (per i `rif()` degli altri gruppi)

Nessun altro sorgente di `technical-fedora45/` (al momento della consegna) usa i vecchi titoli; chi li citasse deve aggiornarsi.

- ch19: «Picture, frame rate and sound measured on 19 November 2026» → «Picture, frame rate and sound: what is and is not measured»
- ch19: «Session and login timings measured on 19 November 2026» → «Session and login timings recorded on Fedora 45»
- ch20: «Porting from Debian to Ubuntu: what changed in practice» → «Porting to Fedora: what changed in practice»
- ch21: «Conventions of the Ubuntu tree» → «Conventions of the Fedora tree»
- ch24: «Ubuntu: what real machines showed that the boxes did not» → «Fedora: what real machines showed that the VMs did not»
- ch24: «Ubuntu: open points» → «Fedora: open points»
- Nessuna sezione aggiunta o tolta; i titoli di capitolo sono invariati. ch25: voci del glossario tolte (AppArmor, Our labwc, Flutter program, Snap, sudo-rs/rust-coreutils, Unione) e aggiunte (SELinux, AVC, authselect, remotix-pam-hook, firewalld service, RPM Fusion, plasmalogin, KWin alone, wheel, graphical-session.target, Forced close, Round (giro), Bench (banco)).

## 2. I tre punti piu' importanti

1. **Nessuna cifra di prestazione di Fedora e' nell'albero** (fps, sincronia audio, latenze, tempi di `check-lifecycle`): stanno nei log sul server e sul tablet. ch19 §3 e §7 lo dicono chiaramente; le uniche cifre citate sono quelle del registro/PIANO con data (tempi di chiusura del locale-chiude-remoto, conteggi PASS del giro h1, prove su macchina vera del 25 nov). Se il proprietario vuole le cifre di `check-media`, bisogna leggerle da `prove-sel/log-final/h1/` sul server e aggiungerle a ch19.
2. **File di licenza stantii**: `LICENSE.md` (r.95-102) e `THIRD-PARTY-LICENSES` (r.9, 24-25, 1174) descrivono ancora il labwc proprio di Ubuntu, che il pacchetto Fedora non contiene, ma lo spec li installa (`%license`, `%doc`). Il manuale lo dice in ch21 §1 e in ch24 «Contradictions». Decisione del proprietario: correggere i file.
3. **Etichette e conteggi ricontati sull'albero Fedora**: `all.sh` ha **16** etichette (il manuale Ubuntu e l'inventario dicevano 15), 19 file `check-*.py`, 12 `_Static_assert`, `registro_dice(` 1264 volte, 59 header (45 con guardia `REMOTIX_`, 53 con `#ifndef`, 5 `#pragma once`), `src/*.c`+`*.h` 106.971 righe, `page.html` 14.326 righe e 941.549 byte (il manuale Ubuntu diceva 937.399 per un file identico: era un conteggio vecchio), 19 azioni polkit.

## 3. Cose non verificate (non affermate nei capitoli, o dichiarate «non verificato»)

- Versioni di Chrome/Firefox del banco Fedora; modello della Radeon; gruppo proprietario dei render node su Fedora; kernel di Fedora 45 (ch19, ch20, ch24).
- `power-implied` su GNOME, KDE e LXQt (provato solo su XFCE, F33).
- `check-package.py` mai eseguito su Fedora; riproducibilita' (R23) e lintian: assenti da `build-rpm.sh`; `SOURCE_DATE_EPOCH` nel modo RPM.
- Come `session.c` tratta i nomi `gdm` e `plasmalogin` nei lettori del display manager (conosce `gdm3`, lightdm, sddm); nomi delle sessioni Fedora (`gnome`, `plasma`, `xfce`, `lxqt`) non controllati uno per uno.
- Se la porta 7447 e' raggiungibile con la zona Workstation (GNOME/KDE) senza aprirla; se `build-rpm.sh` rispetta la regola «mai in /tmp sul server».
- `canvas-limits` 4096x2304, `session-cap` con tetto 2, `check-multiuser` su KDE/XFCE/LXQt, HEVC nel browser, KWin 6.8 e perdita di frame (non misurata), rami dconf «vita sconosciuta» / `dconf` assente.
- `lib.sweep()` non contiene (non verificato) i prefissi degli utenti dei check nuovi di Fedora (`kr1`, `kx1`, `lc1`).
- Flatpak, due utenti con telefono, Samsung DeX: non provati su Fedora.

## 4. Difetti del prodotto o dei file (NON toccati, non descritti come funzioni)

- `server/live-installa.sh:13` ha `PACCHETTO=remotix-1.0.1-1.fc45.x86_64.rpm`: il pacchetto e' 1.2.0.
- `src/main.c:467-473`: messaggio a runtime «Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch» (su Fedora il file lo mette il pacchetto: andrebbe «dnf reinstall remotix»).
- Commenti di `main.c:3972,3977` e di `rpm/remotix.spec:220` («the desktops stay alive» all'aggiornamento) contraddicono DECISIONS-11 §11.56 (lo stop chiude i desktop).
- `CLAUDE.md` di fedora45: «RPM packaging goes in rpm/ (to be written)» e «the Debian packaging to translate is ../ubuntu26.04/debian/» sono stantie.
- Codice labwc-per-KDE irraggiungibile e `LABWC ?=`/`-DREMOTIX_LABWC` orfani nel Makefile (F7): da togliere dopo le prove.
- `prove/lib.py:34,37` e `prove/fresh.sh:5` cercano ancora `boxes/` e citano le porte 8821-8824.
- `force_guard_on` resta acceso dopo una chiusura per accesso locale fallita (in questo albero `session.c:5549-5560`, il PIANO dice 8770); commento di `child.c` sul contesto SELinux degli utenti confinati da allineare (il PIANO cita `child.c:1636`, la riga si e' spostata; il commento e' circa a `child.c:1708`); `giro-selinux.sh` nasconde un controllo morto a meta'.
- `pkexec` su GNOME con SHELL vuoto (FAIL noto, comune a Ubuntu); GNOME senza «ultima difesa» nella chiusura per accesso locale.

## 5. Scelte di scrittura da sapere

- ch20 §2 e §3: tabelle con colonna «Ubuntu, per confronto» (inventario: «decidere se tenere la colonna Debian»: ho tenuto solo Ubuntu, la Debian e' nel ch20 §1).
- ch23: la mappa elenca esattamente i file di `git ls-files --cached --others --exclude-standard src rpm selinux build prove server` (ricontrollato: 0 mancanti, 0 in eccesso); `_manual_rows()` ora testa `technical-fedora45`.
- ch24: righe di «Contradictions» che citano file cambiati su Fedora (`main.c`, `child.c`, `session.c`, `walls.c`) non portano piu' il numero di riga di Ubuntu: citano il testo o la funzione.
- `build.py --check` sui miei capitoli: nessuna contestazione. Restano contestazioni su altri capitoli (ch02/03/10/12/15/17, citazioni di `plasma-kwin_wayland.service` in `c()`, `./all.sh`, `./giro-selinux.sh`) e la differenza del file HTML finale.
