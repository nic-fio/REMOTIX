# Come si lanciano le prove sul banco a VM, Ubuntu 26.04 (modello: `debian13/studio/prove-1.2.0/COME-SI-LANCIA.md`)

Scritto il 26 nov 2026 mentre si portavano gli strumenti di Debian 1.2.0. Cio' che e' marcato **[IPOTESI]** non e' ancora stato visto su una VM
Ubuntu: verificarlo al primo giro e correggere questo file.

# DIVIETI (da Debian, 26 nov 2026: il server e' caduto quattro volte; per Ubuntu vale ancora solo il punto 1)

1. **`amdgpu.runpm=0` OBBLIGATORIO.** Prima che una VM riceva la Radeon, nel suo `GRUB_CMDLINE_LINUX` (`/etc/default/grub`, poi `update-grub`;
   copia di prima in `/etc/default/grub.prima-runpm`) deve esserci `amdgpu.runpm=0`. Controlli nella VM: `cat /proc/cmdline` lo contiene,
   `cat /sys/module/amdgpu/parameters/runpm` = 0, `journalctl -k -b | grep -c "SMU is resuming"` = 0. Se non e' cosi': spegnere subito.
   Su Ubuntu (kernel diverso da 6.12) non si sa se serve: **[IPOTESI]**, ma per prudenza si fa uguale.
2. **Il divieto di Debian (P7-P9, riavvio del display manager, accessi locali con la Radeon passata) NON vale per Ubuntu** (decisione del proprietario, 26 nov 2026:
   i blocchi del server venivano dai driver vecchi delle macchine Debian). Sul banco di Ubuntu P7, P8, P9 e `RX_LOCALE_VERO=1` sono PERMESSI; la protezione
   `amdgpu.runpm=0` la verifica `vm-radeon.sh` da solo (punto 1).
   `all.sh` di default lancia comunque `prelocal` con solo P1-P6 e mostra una riga SKIP `prelocal/real-login`; P7, P8, P9 entrano con `RX_LOCALE_VERO=1`
   (limite di `all.sh` per `prelocal`: 1200 s di default, 3900 s con il consenso; il limite interno di `check-prelocal.py` e' 900 s per P1-P6 piu' 700 s per
   ciascuno di P7-P9, cioe' 3000 s; tutti e due moltiplicati per `RX_TEMPO`). Un giro completo: `RX_LOCALE_VERO=1 ./all.sh <de> --clean`.
   Prima di lanciare uno strumento che non si conosce, leggerne il codice.

# Le quattro macchine

| `--box` | VM | display manager | sessione locale | ssh | REMOTIX | terminale | note |
|---|---|---|---|---|---|---|---|
| `gnome` | `ubuntu` | gdm3 | `ubuntu` (Wayland) | 2341 | 8841 | `ptyxis` | autologin in `/etc/gdm3/custom.conf` |
| `kde` | `kubuntu` | sddm | `plasma` (Wayland) | 2342 | 8842 | `konsole` | editor: `kwrite`, se manca `kate` |
| `xfce` | `xubuntu` | lightdm | `xubuntu` (X11, xfwm4) | 2343 | 8843 | `xfce4-terminal` | editor: `mousepad` |
| `lxqt` | `lubuntu` | sddm | `Lubuntu` (X11, openbox) | 2344 | 8844 | `qterminal` | compositor locale `openbox` |

Utenti `prova` (con sudo) e `prova2`, password `prova2026`; nome host `rx-<vm>` (`rx-ubuntu`, `rx-kubuntu`, `rx-xubuntu`, `rx-lubuntu`);
cartella del banco sul server `/media/REMOTIX-UBUNTU`. Una sola VM alla volta riceve la Radeon.
Le prove si scelgono con `RX_BANCO=vm` e `--box gnome|kde|xfce|lxqt` (il nome `--box` e' quello del desktop, non della VM).

# Particolarita' di Ubuntu da ricordare nei risultati
- **snap**: Firefox, e altro, sono snap. Il caso **P9** di `check-prelocal.py` apre Firefox (snap) dentro il desktop remoto, poi fa l'accesso locale vero
  e cerca residui: processi `firefox`, unita' `snap.firefox.firefox-<uuid>.scope`.
- **sudo-rs**: i rifiuti hanno altre parole (`I'm sorry <user>. I'm afraid I can't do that`, `interactive authentication is required`): `check-desktop.py` le conosce.
- **apport al posto di `coredumpctl`**: i casi P7-P9 cercano i crash dell'utente con `coredumpctl` se c'e', altrimenti in `/var/crash/*.crash`
  (file dell'utente piu' recenti dell'inizio del caso). apport non registra tutti i crash: e' un indizio, non una prova di «nessuno».
  La riga del risultato dice quale dei due ha guardato, o «NOT checked» se nessuno e' attivo.
- **AppArmor**: il profilo `remotix_network` e' in **complain**, voluto (manuali). `aa-status` mostra `remotix_network (complain)`; `check-package.py apparmor`
  ora accetta complain e enforce. `check-apparmor.py` conta come FAIL ogni riga `ALLOWED` o `DENIED` del profilo: per il resto del sistema (snap) non guarda nulla.
- **Percorsi del pacchetto**: `/etc/dconf/db/remotix` e' fatto dal postinst e tolto dal postrm: `check-package.py` lo sa (atteso all'installazione, assente dopo il purge).

# 0. Dopo un riavvio del server (gira in RAM)
    scp ubuntu26.04/server/prepara-server.sh nicfio@192.168.0.2:/tmp/ && ssh nicfio@192.168.0.2 'bash /tmp/prepara-server.sh'
Deve finire con `ALL OK`. Sul server esiste anche `ubuntu26.04/server/prepara-server-vm.sh` (QEMU/OVMF/ACL, chromium, firefox-esr, labwc, wlr-randr, python3-pil,
libavcodec, PipeWire con sink nullo `rx_null`, limiti inotify): rilanciarlo dal repository dopo ogni riavvio del server. Controllo veloce prima di lanciare:
`ssh nicfio@192.168.0.2 'which python3 chromium firefox-esr labwc'` (sintomo se manca: `all.sh` finisce in un minuto con tutte le voci
`BLOCKED (no verdict, exit 127)` e `python3: command not found`; `summary.txt` esiste subito, non fidarsi del solo file).

# 1. Copiare le prove sul server (dal tablet, ogni volta che le correggi)
    cd ubuntu26.04; tar -C prove --exclude=log -cf - . | ssh nicfio@192.168.0.2 'mkdir -p /media/REMOTIX-UBUNTU/tmp/prove-run/prove && tar -C /media/REMOTIX-UBUNTU/tmp/prove-run/prove -xf -'
Il tablet non ha `rsync`. I log restano in `prove-run/prove/log/<TAG>/`; i log lunghi non si leggono: solo `grep -E '^(PASS|FAIL|BLOCKED) '`.

# 2. Accendere la VM e installare il pacchetto
    V=/media/REMOTIX-UBUNTU/vm-radeon/vm-radeon.sh
    $V stato <vm>          # «Radeon held by VM: none» prima di accendere
    $V accendi <vm>        # con la Radeon; ssh risponde in ~30-60 s
    cd /media/REMOTIX-UBUNTU/tmp/prove-run/prove; export RX_BANCO=vm
    DEB=/media/REMOTIX-UBUNTU/pacchetti/<cartella>/remotix_1.2.0-1+ubuntu26.04_amd64.deb ./banco-vm/fresh-vm.sh <de>      # <de> = gnome|kde|xfce|lxqt
`fresh-vm.sh` mette la chiave del banco per root, installa il `.deb`, riavvia il servizio, e controlla che la VM sia Ubuntu 26.04. Il nome del `.deb` e'
**[IPOTESI]** (la versione vera e' quella costruita). Verifica: `./banco-vm/box.sh ssh <de> 'journalctl -u remotix | grep pam-hook'`.
`$V ssh <vm> ...` entra come `prova` (journal incompleto, niente `aa-status`): per i controlli da root usare `./banco-vm/box.sh ssh <de> '...' </dev/null`.

# 3. Giro completo (in background, output su file)
    L=/media/REMOTIX-UBUNTU/log/<giro>/<de>; mkdir -p $L
    TAG=<de>-<giro> nohup ./all.sh <de> --clean --only <elenco senza prelocal, vedi sopra> > $L/all.stdout 2>&1 &
Il log di ogni prova e' `log/<TAG>/<voce>.out`; a fine giro `log/<TAG>/summary.txt` (esiste solo alla fine). La voce `apparmor` (nuova, ultima) guarda il registro del
kernel di tutto il giro: il giro dice in `all.sh` quando e' partito (`T0`). Con `--only` il giro e' PARZIALE e finisce con codice 3 anche se tutto e' verde (e' detto nel riepilogo).
Non usare Monitor con grep ripetuto sui FAIL. Attesa dal tablet: cicli `for i in $(seq 34); do [ -f summary.txt ] && break; sleep 5; done`. Il registratore avviato con `nohup ... &`
dentro una chiamata ssh muore alla chiusura: usare `setsid nohup sh -c '...' </dev/null &`.

# 4. Locale-chiude-remoto (P1-P9)
    RX_BANCO=vm python3 check-prelocal.py --box <de> --only P1,P2,P3,P4,P5,P6 > $L/prelocal.out 2>&1       # senza accessi locali veri
    RX_BANCO=vm python3 check-prelocal.py --box <de> --only P7,P8,P9 > $L/prelocal-busy.out 2>&1           # accesso locale VERO, riavvio del display manager
I tre casi con programmi aperti (accesso locale vero) sono PERMESSI sul banco di Ubuntu con la Radeon passata (decisione del proprietario, 26 nov 2026; vedi i divieti in cima). Ogni caso dura circa 3 minuti.
- **P7** terminale con `top` aperto; **P8** editor con testo non salvato (solo `kde`: kwrite o kate, e `xfce`: mousepad; `gnome` e `lxqt`: BLOCKED); **P9** Firefox (snap) aperto.
- Utenti usati: `pl1`, `pl2` (P1-P5), `pl3` (P7), `pl4` (P8), `pl5` (P9). Non girano insieme a `all.sh` (stessi utenti `pl*`).
- Lo strumento a mano: `prelocal.sh <de> 1|2a|2b|3` (stesso divieto), con `banco-vm/autologin-gdm3.sh`, `autologin-sddm.sh`, `autologin-lightdm.sh`.
- Stato dei programmi aperti nel desktop remoto, a mano: `RX_BANCO=vm RX_BOX=<de> python3 hold.py 120` (`hold-user.py` se l'utente lo fa la prova).

# 5. Altri strumenti portati da Debian
- `check-exit.py --box xfce|lxqt` (tre modi di chiudere il desktop remoto: terminate-session, riavvio del servizio, chiusura del browser). Non fa parte di `all.sh`.
- `check-kde-exit.py --box kde` (gli stessi tre casi per KDE; il Log Out dal menu di KDE si prova a mano). Non fa parte di `all.sh`.
- `check-apparmor.py --box <de> [--since <epoch>]` (anche dentro `all.sh`).

# 6. Cose da verificare sulle macchine virtuali
**VERIFICATI sulla VM GNOME (`ubuntu`) nel primo giro, 26 nov 2026:**
- sessione `ubuntu`; `/etc/gdm3/custom.conf` con la sezione `[daemon]` e autologin che fa partire `ubuntu`; `ptyxis -x top` (prima forma);
- gestore dei core: **apport** su Ubuntu, Xubuntu e Lubuntu, ma **`systemd-coredump` + `coredumpctl` su Kubuntu** (il codice sceglie da solo);
- **`kate` e non `kwrite`** su Kubuntu; compositore locale **`openbox`** su Lubuntu; nomi host `rx-<vm>`;
- il profilo della Firefox snap in `/tmp/rx-snap-profile-<uid>` funziona.
Primo giro GNOME: 125 PASS, 1 FAIL noto (`users-shell-and-environment`); P7 e P9 PASS, P8 BLOCKED per costruzione (GNOME non ha un editor con testo non salvato senza interazione).
Correzioni a `check-prelocal.py` fatte dal giro: P9 prende `WAYLAND_DISPLAY`/`DISPLAY` da `systemctl --user show-environment`; `unit_residue` non conta i `.timer` e conta una `.slice`
solo se contiene un processo del desktop REMOTO (la slice `app-gnome\x2dsession\x2dmanager.slice` ha lo stesso nome nella sessione locale e in quella remota); P9 aspetta la finestra
fino a 30 s (controllo ogni 2 s).

**ANCORA DA VERIFICARE (IPOTESI):**
1. Sessioni delle altre VM: `ls /usr/share/wayland-sessions /usr/share/xsessions`. Attese `plasma` (Kubuntu), `xubuntu`, `Lubuntu`; scritte in `banco-vm/autologin-sddm.sh` e `autologin-lightdm.sh`.
2. Programmi su Xubuntu (`mousepad`), Lubuntu (`qterminal`), `firefox` snap su tutte, nome del `.deb`.
3. Che `amdgpu.runpm=0` serva anche sui kernel Ubuntu (lo verifica `vm-radeon.sh`).
4. Il controllo `which python3 chromium firefox-esr labwc` e' sul server: `firefox-esr` e' il nome di Debian; adattarlo se il server lo chiama diversamente.
