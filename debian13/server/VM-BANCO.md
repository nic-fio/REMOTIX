# Banco di prova Debian 13: le quattro VM

Quattro macchine virtuali PULITE (nessun REMOTIX dentro) sul server di sviluppo, una per desktop. Create il 25 nov 2026.

## Come si usa
Script: `debian13/server/vm-radeon.sh` (copia sul server in `/media/REMOTIX-DEBIAN/vm-radeon/vm-radeon.sh`). Stessa interfaccia di quello di Fedora.
Dopo un riavvio del server (il sistema gira in RAM) prima si lancia `prepara-server-vm.sh` (stessa cartella): rimette QEMU, OVMF, strumenti per i dischi, ACL su `/dev/kvm`.

- `vm-radeon.sh stato <vm>`: acceso o spento, chi ha la Radeon (controllo valido per tutti i banchi: Fedora, Ubuntu, Debian).
- `vm-radeon.sh accendi <vm>`: con la Radeon (12 GB di RAM). `accendi <vm> virtuale`: senza Radeon, scheda virtuale (5 GB).
- `vm-radeon.sh spegni <vm>`: spegne e restituisce la Radeon al server (solo se la teneva questa VM).
- `vm-radeon.sh ssh <vm> [comando]`, `prova-avvio <vm> [--resta]` (avvio virtuale con rapporto, poi spegne).
- `vm-radeon.sh schermo <vm> <file.png>`, `tasti <vm> <tasto>...`, `scrivi <vm> <testo>`: per le VM accese in modo `virtuale`.
- `vm-radeon.sh istantanea <vm> <etichetta>`, `ripristina <vm> <etichetta>` (VM spenta; `ripristina` butta lo stato attuale, salvato prima come `prima-...`).
- `vm-radeon.sh crea <vm>`: costruisce il disco dallo squashfs della ISO (rifiuta se il disco esiste). `crea` scrive a schermo (rsync in `<vm>/build/rsync.log`); i log di oggi in `/media/REMOTIX-DEBIAN/vm-radeon/logs/` ci sono perché li ho messi a mano con la redirezione, lo script non li crea né li usa.

Una sola VM in tutto il server può avere la Radeon; al massimo due VM accese insieme è una regola d'uso (memoria del server), lo script non la impone.

## Porte, utenti, cartelle
| VM | ssh | REMOTIX (tcp+udp, verso 7447 della VM) | display manager |
|---|---|---|---|
| gnome | 2361 | 8861 | gdm3 |
| kde | 2362 | 8862 | sddm |
| xfce | 2363 | 8863 | lightdm |
| lxqt | 2364 | 8864 | sddm |

Utenti: `prova` (password `prova2026`, gruppo `sudo`) e `prova2` (stessa password, senza sudo); ssh anche con la chiave `vmkey` di ogni VM. Hostname `rx-deb-<nome>` (es. `rx-deb-gnome`). Lingua `en_US.UTF-8`, tastiera `us` pc105, fuso Europe/Rome, come le VM di Fedora. Nessun autologin.
Dati di ogni VM: `/media/REMOTIX-DEBIAN/vm-radeon/<vm>/` (`disk.qcow2`, `OVMF_VARS.fd`, `vmkey`, `serial.log`). Istantanea `pulito` su tutte e quattro.

## Come sono fatte
Debian 13 installato davvero su disco (GPT, EFI da 512 MB, ext4, UEFI), costruito dallo squashfs della ISO live con il kernel di Debian (mai quello del server); tolti i pacchetti live-* e calamares; archivi `main non-free-firmware` + updates + security; `apt full-upgrade` fatto alla creazione; `firmware-amd-graphics` presente; openssh-server aggiunto. GRUB: dentro la catena (chroot sul disco su loop) `grub-probe` non riconosce il disco, quindi lo script scrive un `grub.cfg` iniziale a mano e, al primo avvio in VM, lancia `grub-install` + `update-grub` (configurazione vera, scritta solo nelle variabili UEFI della VM).

## Versioni trovate
Kernel `6.12.118+deb13-amd64`, systemd 257.13, firmware-amd-graphics 20250410-2 (tutte e quattro).
- gnome: GNOME Shell 48.7, gdm3 48.0-2.
- kde: Plasma 6.3.6 (plasma-desktop), sddm 0.21.0 (sessione di serie: Plasma Wayland).
- xfce: Xfce 4.20 (xfce4-session 4.20.2, panel 4.20.4, xfwm4 4.20.0), lightdm 1.32.0.
- lxqt: lxqt-session 2.1.1, sddm 0.21.0.
- labwc: NON installato in nessuna VM, ma disponibile nei repository: 0.8.3-1 (trixie).

## Verifiche (25 nov 2026)
| | gnome | kde | xfce | lxqt |
|---|---|---|---|---|
| (a) avvio virtuale fino al display manager (`prova-avvio`) | sì | sì | sì | sì |
| (b) con la Radeon: amdgpu caricato, `/dev/dri/renderD128`, display manager attivo | sì | sì | sì | sì |
| (b) `is-system-running` con la Radeon | running, dopo `plymouth quit` (vedi sotto) | running | running | running |
| unità fallite | nessuna (virtuale e Radeon) | nessuna | nessuna | nessuna |
| (c) accesso locale di `prova` fino al desktop, in modo virtuale | sì (GNOME Shell, mostra il tour di benvenuto) | sì (kwin_wayland + plasmashell) | sì (xfce4-session, panel, xfwm4, xfdesktop) | sì (desktop LXQt, schermata vista) |
| (d) archivi Debian raggiungibili (`deb.debian.org`, HTTP 200) | sì | sì | sì | sì |

Note:
- GNOME con la Radeon e senza monitor collegato: `is-system-running` resta `starting` per sempre perché `plymouth-quit-wait.service` aspetta che la shell di gdm disegni il primo fotogramma, e la Radeon non ha monitor (tutte le uscite `disconnected`). Con `plymouth quit` va a `running` e non ci sono unità fallite. Non è stato toccato niente: lo segnalo, la decisione è del proprietario.
- Nel greeter di sddm (lxqt, kde) il tasto `ret` del comando `tasti` non invia: usare `kp_enter`. In gdm il greeter parte con `prova` selezionato (`ret`, poi password e `ret`). In lightdm: utente, `tab`, password, `kp_enter`.
- L'accesso locale è stato provato SOLO in modo virtuale; con la Radeon non c'è schermo, quindi il login locale non è stato visto. Dopo i test la home di `prova` ha le impostazioni create dal primo accesso (l'istantanea `pulito` è stata presa dopo i test, a VM spenta).

## Non fatto / differenze dal brief
- Hostname: i dischi sono stati creati con `rx-<nome>` e rinominati a mano in `rx-deb-<nome>` (hostnamectl e /etc/hosts) prima dell'istantanea `pulito`; lo script ora crea già `rx-deb-<nome>`.
- Il disco di `lxqt` è stato creato con la prima versione dello script (senza il grub scritto a mano): ha lo stesso risultato verificato. Le altre tre con la versione finale.
- Nessun tentativo di login locale con la Radeon accesa (nessuno schermo).
