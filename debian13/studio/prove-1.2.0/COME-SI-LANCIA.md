# DIVIETO: P7 e P8 e il riavvio del display manager fanno CADERE IL SERVER (26 nov 2026)
Due volte (01:17 e 08:26) il server intero si e' bloccato, nello stesso passo sulla VM `kde`: `check-prelocal.py`, P1-P6 passati, poi P7
(accesso locale vero: autologin di sddm + `systemctl restart sddm` DENTRO la VM con la Radeon passata). Un minuto dopo il server e' morto
(memoria libera 11 GB, swap non usato: non e' la memoria). Ogni caduta richiede il ripristino a mano del proprietario.
Con la Radeon passata e' VIETATO: `check-prelocal.py` senza `--only P1,P2,P3,P4,P5,P6` (P7/P8), `prelocal.sh`, `banco-vm/autologin-*.sh` con riavvio,
`systemctl restart|stop gdm3|sddm|lightdm` nella VM, accessi locali grafici, `reboot` dall'interno della VM, `all.sh` senza escludere `prelocal`
(usare `--only` con le altre voci: `LABELS` in `all.sh`). Prima di lanciare uno strumento che non si conosce, leggerne il codice.

# Come si lanciano le prove sul banco a VM (scritto dal giro GNOME, 25 nov 2026)

Tutto gira SUL SERVER (`nicfio@192.168.0.2`); dal tablet si comanda solo via ssh. Il tablet NON ha `rsync` (si usa `tar` via ssh).

## 0. Dopo un riavvio del server (gira in RAM)
Copia e lancia `debian13/server/prepara-server-vm.sh` (idempotente, ~1 minuto se i pacchetti ci sono, di piu' se vanno scaricati):
    scp debian13/server/prepara-server-vm.sh nicfio@192.168.0.2:/tmp/ && ssh nicfio@192.168.0.2 'bash /tmp/prepara-server-vm.sh'
Ora comprende: QEMU/OVMF/ACL su /dev/kvm, moduli, E gli strumenti delle prove (chromium, firefox-esr, labwc, wlr-randr,
python3-pil, libavcodec61, PipeWire con sink nullo `rx_null` a mano, limiti inotify). Deve finire con `ALL OK`.
Niente contenitori. Le librerie Python delle prove sono solo PIL (+ `gi` DENTRO la VM, installato da fresh-vm.sh).

## 1. Copiare le prove sul server (dal tablet, ogni volta che le correggi)
    cd debian13; tar -C prove --exclude=log -cf - . | ssh nicfio@192.168.0.2 'mkdir -p /media/REMOTIX-DEBIAN/tmp/prove-run/prove && tar -C /media/REMOTIX-DEBIAN/tmp/prove-run/prove -xf -'
(i log restano in `prove-run/prove/log/<TAG>/`; i log lunghi non si leggono: solo `grep -E '^(PASS|FAIL|BLOCKED) '`.)

## 2. Accendere la VM e installare il pacchetto
    V=/media/REMOTIX-DEBIAN/vm-radeon/vm-radeon-1.2.0.sh
    $V stato <vm>          # "Radeon held by VM: none" prima di accendere
    $V accendi <vm>        # con la Radeon; ssh risponde in ~30-60 s; `is-system-running` resta "starting" su GNOME (normale)
    cd /media/REMOTIX-DEBIAN/tmp/prove-run/prove; export RX_BANCO=vm
    DEB=/media/REMOTIX-DEBIAN/pacchetti/giro1/remotix_1.2.0-1+deb13_amd64.deb ./banco-vm/fresh-vm.sh <vm>
fresh-vm.sh: ~18 s; mette la chiave del banco per root, installa il .deb (tira dentro labwc), aggiunge wl-clipboard, riavvia il servizio.
Verifiche: `./banco-vm/box.sh ssh <vm> 'journalctl -u remotix | grep pam-hook'` ("the local-login hook is in place in /etc/pam.d/common-session").
TRAPPOLA: il profilo AppArmor `remotix_network` e' installato in **complain**, non enforce (voluto e scritto nei manuali): `aa-status`
mostra "remotix_network (complain)". Il brief dice "enforce": non e' un difetto.

## 3. Giro completo (in background, output su file)
    L=/media/REMOTIX-DEBIAN/log/giro1/<vm>; mkdir -p $L
    TAG=<vm>-giro1 nohup ./all.sh <vm> --clean > $L/all.stdout 2>&1 &
Il log di ogni prova e' `log/<TAG>/<voce>.out`, a fine giro `log/<TAG>/summary.txt` (esiste solo alla fine: si usa per aspettare).
Tempi misurati su GNOME: base-chrome 30 s, base-firefox 30 s, lifecycle ~3 min, multiuser ~5 min, desktop ~7 min, media ~4 min,
resilience: lunga (decine di minuti; limite 90 min con RX_TEMPO=2). Giro intero: vedi il rapporto giro1-gnome.md.
Attesa dal tablet: i comandi ssh oltre 180 s passano in background da soli; usa cicli `for i in $(seq 34); do [ -f summary.txt ] && break; sleep 5; done`.
NON usare Monitor con grep ripetuto sui FAIL (ripete la stessa riga ogni ciclo).

## 4. Locale-chiude-remoto
    RX_BANCO=vm python3 check-prelocal.py --box <vm> > $L/prelocal.out 2>&1
(P1-P8; P8 BLOCKED su GNOME/LXQt). Prima: giro `all.sh` finito (non girano insieme: stessi utenti `pl*`).

## 5. Chiusura
    $V spegni <vm>; $V stato <vm>      # Radeon di nuovo "none"
    $V istantanea <vm> giro1           # a VM spenta

## Trappole nuove (giro 2 KDE, 26 nov 2026)
- Dopo un riavvio del server `prepara-server-vm.sh` va copiato e lanciato DI NUOVO dal repository, anche se "gia' rilanciato": la copia
  rimasta sul server puo' essere la versione vecchia (senza i passi per le prove). Sintomo: `all.sh` finisce in 1 minuto con tutte le voci
  `BLOCKED (no verdict, exit 127)` e `python3: command not found` (summary.txt esiste subito: non fidarsi del solo file). Controllo veloce prima di lanciare:
  `ssh nicfio@192.168.0.2 'which python3 chromium firefox-esr labwc'`.
- Il registratore della memoria avviato con `nohup ... &` dentro una chiamata ssh muore alla chiusura della chiamata: usare `setsid nohup sh -c '...' </dev/null &`.
- `vm-radeon-1.2.0.sh ssh <vm> ...` entra come `prova` (journal incompleto, nessun `aa-status`): per i controlli da root usare `./banco-vm/box.sh ssh <vm> '...' </dev/null`.
- Le voci specifiche di KDE: `check-exit.py` non vale per KDE (solo xfce/lxqt); il Log Out dal menu di KDE non e' coperto da `check-kde-exit.py`
  (che prova terminate-session, restart del servizio, chiusura del browser): va fatto a mano.
