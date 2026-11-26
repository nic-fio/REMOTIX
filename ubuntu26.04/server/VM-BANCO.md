# Banco di prova Ubuntu 26.04: le macchine virtuali

Macchine virtuali PULITE (nessun REMOTIX dentro) sul server di sviluppo: una per desktop, più `costruzione`. Dati in `/media/REMOTIX-UBUNTU/vm-radeon/<vm>/`.

## Come si usa
Script: `ubuntu26.04/server/vm-radeon.sh` (copia sul server in `/media/REMOTIX-UBUNTU/vm-radeon/vm-radeon.sh`). Dopo ogni riavvio del server (gira in RAM) prima si lancia `prepara-server-vm.sh` (stessa cartella, senza contenitori): rimette QEMU, OVMF, strumenti per i dischi, ACL su `/dev/kvm`, e la protezione lato server della Radeon: registro del kernel su disco riga per riga in `/media/REMOTIX-UBUNTU/log/server/`; `vfio-pci` con `disable_idle_d3=1` (scritto in `/etc/modprobe.d/remotix-vfio.conf` e, se il modulo era già caricato con il file nuovo o con il parametro diverso da Y, scaricato e ricaricato quando nessuno lo usa; se non si può, il passo dice FAIL); `power/control=on` per la scheda e i ponti PCI sopra di lei. Il passo stampa i valori letti.

- `stato <vm>`: acceso o spento, chi ha la Radeon, e per ogni VM se il marcatore `runpm.ok` c'è.
- `accendi <vm>`: con la Radeon (12 GB, 8 CPU), solo dopo la prova del blocco (vedi sotto). `accendi <vm> virtuale`: senza Radeon, scheda virtuale (5 GB, 4 CPU); più VM virtuali insieme sono possibili.
- `spegni <vm>`: spegne e restituisce la Radeon (solo se la teneva questa VM).
- `ssh <vm> [comando]`, `prova-avvio <vm> [--resta]`, `schermo <vm> <file.png>`, `tasti <vm> <tasto>...`, `scrivi <vm> <testo>` (questi tre per le VM accese in modo `virtuale`).
- `istantanea <vm> <etichetta>`, `ripristina <vm> <etichetta>` (VM spenta; `ripristina` butta lo stato attuale, salvato prima come `prima-...`, e cancella il marcatore).
- `crea <vm>`: costruisce il disco (ubuntu: autoinstall; le altre: dallo squashfs della ISO, con il kernel di Ubuntu), poi un primo avvio virtuale di controllo. Rifiuta se il disco esiste.

## Regola Radeon (strutturale, non dipende da chi lancia)
Il 26 nov 2026 il server si è bloccato 4 volte perché il driver amdgpu della VM metteva a riposo la Radeon. Ora:
1. `crea` scrive nella VM `amdgpu.runpm=0` (`/etc/default/grub.d/zz-remotix-banco.cfg`, il nome ordina per ultimo così nessun altro file `99-*` può annullarlo; `crea` fallisce se al primo avvio il parametro manca).
2. `accendi <vm>` con la Radeon esige il file `runpm.ok`, scritto solo dopo aver visto il parametro in `/proc/cmdline` con la VM accesa SENZA Radeon. Il marcatore vale per UN solo avvio: ogni avvio della VM fatto dallo script lo cancella, quindi ogni `accendi` con la Radeon è preceduto da una prova fresca (circa 15-30 s in più). Se manca, lo script fa da solo l'avvio virtuale, applica il parametro se serve, riavvia, ricontrolla; se non ottiene la prova rifiuta e la scheda non viene data. Nessuna opzione per saltare il controllo.
3. Dopo l'avvio con la Radeon (e anche se la VM era già accesa con la Radeon), `/sys/module/amdgpu/parameters/runpm` deve valere 0 e il parametro deve stare in `/proc/cmdline` (riletto tre volte); altrimenti la VM viene spenta subito e la scheda restituita. Se lo script è interrotto fra il prendere la scheda e l'avvio di qemu, la scheda torna al server. Se ssh non risponde, avviso ben visibile ma la VM non viene spenta.
Una sola VM in tutto il server può avere la Radeon (controllo valido per tutti i banchi).

## Porte e utenti
| VM | ssh | REMOTIX (tcp+udp, verso 7447 della VM) | immagine |
|---|---|---|---|
| ubuntu | 2341 | 8841 | Ubuntu 26.04.1 |
| kubuntu | 2342 | 8842 | Kubuntu 26.04.1 |
| xubuntu | 2343 | 8843 | Xubuntu 26.04.1 |
| lubuntu | 2344 | 8844 | Lubuntu 26.04.1 |
| costruzione | 2345 | nessuna | Xubuntu (8 CPU, 6 GB, solo `virtuale`, mai la Radeon; hostname `rx-ub-costruzione`) |

Utenti: `prova` (password `prova2026`, gruppo `sudo`) e `prova2` (stessa password, senza sudo); ssh anche con la chiave `vmkey` di ogni VM. Hostname `rx-<nome>`. Lingua `en_US.UTF-8`, tastiera `us`, fuso Europe/Rome. Nessun autologin.
