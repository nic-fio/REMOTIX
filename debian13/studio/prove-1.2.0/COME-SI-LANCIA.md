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
