# Giro 5, VM lxqt (26 nov 2026), pacchetto giro5, con `amdgpu.runpm=0`

## Orari (ore del server; dettaglio in `log/passi-lxqt.log`, memoria in `log/memoria-lxqt.log`)
11:15 server su da 53 min, `pgrep -c qemu`=0. 11:16 passo A (VM accesa SENZA Radeon, `virtuale`). B (con Radeon) e C (installazione) attorno alle 11:18.
Voci di `all.sh` dalle ~11:19 alle 12:01, P1-P6 12:02-12:03, voci LXQt 12:04-12:08, purge e reinstallazione 12:08, VM spenta 12:08:53, istantanea 12:09:03.

## A. Rimedio
Chiave `vmkey` non era autorizzata per `root` (box.sh rootkey fallito: `prova` con `vmkey` non entra): messa a mano via `vm-radeon-1.2.0.sh ssh lxqt` + `sudo -S` (password del banco). Strumenti non modificati.
`GRUB_CMDLINE_LINUX=""` -> `"amdgpu.runpm=0"`, copia `/etc/default/grub.prima-runpm`, `update-grub` ok, `grep -c amdgpu.runpm=0 /boot/grub/grub.cfg` = 5. VM spenta.
## B. Con la Radeon
`/proc/cmdline` contiene `amdgpu.runpm=0`; `/sys/module/amdgpu/parameters/runpm` = 0; "SMU is resuming" = 0, e resta 0 dopo OGNI voce (controllato dopo ogni voce e alla fine).
## C. Installazione (`fresh-vm.sh`, giro5)
Installato, tira dentro `labwc` 0.8.3-1, servizio attivo; `remotix-pam-hook: the local-login hook is in place in /etc/pam.d/common-session`; AppArmor `remotix_network` caricato (complain, voluto).

## D. Voci di `all.sh` (una per comando, TAG `lxqt-giro5-<voce>`)
| voce | esito |
|---|---|
| base-chrome, base-firefox | tutto PASS (page, login, desktop, **mouse, keyboard**) |
| lifecycle | PASS (4/4) |
| multiuser | PASS (3/3) |
| media | PASS video, codec, two-sessions-budget; **FAIL screen-updates** (NOTO, vedi sotto) |
| resilience | PASS (5/5, compreso clocks) |
| audio-chrome, audio-firefox | PASS |
| clipboard | PASS (2 direzioni) |
| input-chrome | tutto PASS (25), compreso mouse-coordinates |
| input-firefox | tutto PASS tranne **FAIL kbd-not-producible** (vedi sotto) |
| phone | PASS (tutte) |
| ban | PASS (8/8) |
| apparmor | PASS (nessuna riga ALLOWED/DENIED) |
| desktop | PASS tutte (10): power-entries-absent, **no-password-windows (0 chiamate BeginAuthentication)**, users-shell-and-environment (qterminal, /bin/bash), power-implied, power-local-seat, settings-intact, canvas-limits, reattach-windows-inside, session-cap |
| check-prelocal P1-P6 | PASS tutti |
`prelocal` di `all.sh`, `package`, P7, P8 non lanciati (vietati/esclusi).

FAIL:
- `media/screen-updates`: NOTO come su GNOME e KDE, poco oltre soglia: ultimo valore a schermo 1502 ms (mediana) / 1517 ms (peggiore) dopo l'ultimo cambio; primo avvistamento 1577 ms (min 1542); 445 screenshot, valori 29..189, 159/159 visti (100%), 0 passi indietro; animazione 60 Hz: 61.2 frame/s. Nelle 4 raffiche le soglie fallite: "final 184/277/370/463 only ~1.5 s after the last change".
- `input-firefox/kbd-not-producible`: STRUMENTO (probabile; da confermare): la voce passa su Chrome (2 righe «not producible» nel registro), su Firefox la riga e' 1 su 2 (`entry 'xyz'` giusto: nulla di finto arrivato al desktop). Riga: "typed x È y (emoji) z: entry 'xyz' is right but the journal declares 1 of the 2 characters". Firefox (WebDriver) manda probabilmente l'emoji come un solo evento o lo perde prima del prodotto. Non c'entra LXQt (logica della tastiera, non del desktop); non toccato.

## E. Voci specifiche di LXQt (utente nuovo `lx1`, `hold.py` 240 s, foto `shots/hold-desktop.png`)
- Desktop dentro `labwc` 0.8.3-1. Processi dell'utente remoto: `remotix-child`, `labwc`, `lxqt-session`, `lxqt-panel`, `pcmanfm-qt`, piu' `lxqt-policykit-agent`, `lxqt-notificationd`, `lxqt-runner`, `xdg-desktop-portal(-gtk,-lxqt)`, gvfs, at-spi, `geoclue agent`, `applet.py` (print-applet), `qlipper`, `nm-tray`. Registro del servizio: nessun errore (solo la riga informativa «decoder pace off»).
- FINESTRE DI PASSWORD: NO. Foto del desktop: nessuna finestra (desktop con icone Cestino, Computer, home, Rete in italiano; pannello con orologio, nm-tray, qlipper). Sessione tenuta oltre 2 minuti (ricontrollo del registro a 120 s di eta'): nessuna azione polkit chiesta dalla sessione. Registro `journalctl -b | grep polkit`: solo «Registered/Unregistered Authentication Agent ... /usr/bin/lxqt-policykit-agent» (unico agente: `lxqt-policykit-agent`, locale it_IT.UTF-8 per lx1) e un `org.freedesktop.policykit.exec ... FAILED to authenticate` alle 11:54:56 (utente `dk1`, il `pkexec` della voce `desktop`: NOTO, e nessuna finestra, nessun FAIL). `xiccd` NON e' installato, non e' in `/etc/xdg/autostart`, `colord` e' installato ma inattivo; 0 righe `color-manager`/`xiccd` nel registro. Quindi il difetto di XFCE (azione `org.freedesktop.color-manager.create-device`) su LXQt non c'e'.
- LINGUA (utente nuovo, `it_IT.UTF-8` PRIMA del primo accesso; `accountsservice` NON e' installato nella VM: file scritto a mano `/var/lib/AccountsService/users/lx1` con `[User]` e `Language=it_IT.UTF-8`; `locale-gen it_IT.UTF-8` fatto):
  | processo | LANG |
  |---|---|
  | remotix-child | it_IT.UTF-8 |
  | labwc | it_IT.UTF-8 |
  | lxqt-session | it_IT.UTF-8 |
  | lxqt-panel | it_IT.UTF-8 |
  | pcmanfm-qt | it_IT.UTF-8 |
  | `systemctl --user -M lx1@ show-environment` | it_IT.UTF-8 |
  Nessun `LANGUAGE` / `LC_*`. LXQt non scrive nessuna riga di lingua: `~/.config/lxqt/lxqt.conf` e `session.conf` nascono con solo `[General]` e `__userfile__=true`. Lingua rimessa vuota (`Language=`).
- Autostart di Debian LXQt nella sessione remota: partono `nm-tray`, `qlipper`, `print-applet` (`applet.py`), `lxqt-policykit-agent`; `pulseaudio.desktop` non genera un processo (c'e' `pipewire-pulse`). Nessuna finestra, nessun errore nel registro dell'utente a parte `wireplumber: 'api.libcamera.enum.manager' could not be loaded` (la VM non ha camera; innocuo). Nessuna finestra `xscreensaver`/`orca`.
- `pkexec` (SHELL vuoto): non e' comparso come FAIL su LXQt (la voce `users-shell-and-environment` passa). Il pannello ha un pulsante di spegnimento in basso a destra (polkit rifiuta le 19 azioni, `power-entries-absent` PASS).

## F. Chiusura
`apt purge remotix`: pacchetto sparito; nessun file `*remotix*` in `/etc /usr /var /root /home /opt` (all'inizio restava `/run/user/1036/remotix`, volatile, della sessione di `lx1` ancora in chiusura: scomparsa da sola pochi secondi dopo), nessun riferimento in `pam.d`/`apparmor.d`/`polkit-1`; l'utente `remotix` ricreato dalla reinstallazione (UID 988). Reinstallato giro5 (`dpkg --audit` vuoto), servizio abilitato e attivo.
VM spenta 12:08:53; Radeon libera ("Radeon held by VM: none"); `pgrep -c qemu`=0; istantanea `giro5` creata; registratore fermo. «SMU is resuming» = 0 per tutta la durata. Rimasto nella VM: utenti di prova, `it_IT.UTF-8` generato, `/etc/default/grub.prima-runpm`.
