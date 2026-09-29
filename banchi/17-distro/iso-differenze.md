# Lo stato ISO: che cosa cambia rispetto a cloud + DESKTOP (fasi/17 §7.2)

La macchina ISO è installata **dall'ISO ufficiale**, con l'installatore automatico della
distribuzione (`17-vm.sh da-iso <macchina>-iso`, risposte in `iso-risposte/`), su un disco nuovo
e con firmware UEFI. Rispetto alle scelte di serie, le risposte aggiungono solo tre cose, tutte
dentro l'installazione: il server ssh dove di serie non c'è, la chiave del banco e sudo senza
parola (`/etc/sudoers.d/90-banco`). Lingua italiana, tastiera it, fuso Europe/Rome: come un
cliente italiano.

Il confronto si fa con `17-vm.sh impronta <macchina> cliente` e `impronta <macchina>-iso iso`.
La macchina parte dalla foto in sola lettura (`-snapshot`) e su porte sue (k=6). I file stanno
sul server: `…/<macchina>{,-iso}/{impronta,pacchetti,unita}-{cliente,iso}.txt`. Tutto misurato
il 29 set 2026 `[M]`.

## Le macchine

| macchina | fatta | tempo | ISO e installatore |
|---|---|---|---|
| debian13-gnome | ✅ | 10 min | debian-13.7.0-amd64-netinst, preseed |
| ubuntu2604-gnome | ✅ | 11 min | ubuntu-26.04.1-desktop, autoinstall (la strada del desktop va fino in fondo) |
| fedora44-gnome | ✅ | 7 min | Fedora-Everything-netinst 44-1.7, kickstart, `@^workstation-product-environment` |
| alma10-gnome | ✅ | 7 min | AlmaLinux-10.2 boot, kickstart, `@^graphical-server-environment` |
| arch-kde | ✅ | ~10 min | archlinux-2026.09.01, archinstall 4.4, profilo Desktop/KDE Plasma, sddm |
| tumbleweed-kde | ✅ | 14 min | Tumbleweed NET Snapshot20260924, AutoYaST, i pattern del ruolo KDE di serie |

Tutte le ISO sono verificate con la sha256 del sito ufficiale. Dopo il riavvio, su ogni macchina
ssh ha risposto, sudo funziona e `graphical.target` è attivo.

## Le differenze che contano per l'installatore

| | cloud + DESKTOP (foto `cliente`) | ISO (foto `iso`) |
|---|---|---|
| **gruppi dell'utente** | solo il suo gruppo, dappertutto (cloud-init) | Debian: `cdrom floppy sudo audio dip video plugdev users netdev scanner bluetooth lpadmin`, cioè **`video` c'è già**; Ubuntu: `adm cdrom sudo dip plugdev users lpadmin lxd`, senza `video`; Fedora, Alma e Arch: `wheel`; Tumbleweed: nessuno. **`render` non c'è mai.** |
| **firewall** | Fedora: zona `public` (ssh mdns dhcpv6); Alma: `public` (ssh cockpit dhcpv6); **Tumbleweed: nessun firewall**; Debian e Arch: nessuno; Ubuntu: ufw installato ma spento | **Fedora: zona `FedoraWorkstation`, con 1025-65535 tcp/udp APERTE** (la 7447 passa senza fare niente); Alma: `public` (ssh cockpit dhcpv6) come la cloud, quindi la 7447 è chiusa; **Tumbleweed: firewalld acceso, `public` con solo dhcpv6 e ssh (ssh aperto da noi), quindi la 7447 è chiusa**; Debian e Arch: nessuno; Ubuntu: ufw spento |
| **SELinux / AppArmor** | Fedora, Alma, Tumbleweed: SELinux Enforcing; Debian, Ubuntu: AppArmor; Arch: niente | uguale. Su Tumbleweed SELinux è Enforcing in tutt'e due, con `selinux-policy-targeted`. |
| **rete** | Debian e Ubuntu: **systemd-networkd + netplan `50-cloud-init.yaml`** (NM c'è ma non gestisce la scheda), resolved acceso; Arch: **networkd + resolved, NM spento**; Fedora, Alma, Tumbleweed: NetworkManager | **NetworkManager dappertutto**. Ubuntu: netplan `01-network-manager-all.yaml`. resolved: acceso su Ubuntu e Fedora, spento su Debian, Arch e Tumbleweed. |
| **display manager** | gdm (Debian, Ubuntu, Fedora, Alma), sddm (Arch), `display-manager.service` (Tumbleweed) | uguale, ma Tumbleweed usa `display-manager-legacy.service` con **accesso automatico** (`DISPLAYMANAGER_AUTOLOGIN="nicfio"`, la casella di serie), quindi c'è già una sessione aperta sullo schermo |
| **disco e foto di sistema** | ext4 (Debian, Ubuntu), btrfs (Fedora, Arch), xfs (Alma, Tumbleweed); nessuno snapper | Debian ext4 + swap su partizione; Ubuntu ext4 + `/swap.img`; Fedora btrfs + zram; Alma **LVM** + xfs; Arch ext4 + zram; **Tumbleweed btrfs con snapper** (config `root`, 3 foto già dopo l'installazione; `/` è `/@/.snapshots/1/snapshot`). Quindi ogni zypper di REMOTIX lascia una foto pre/post. |
| **raccomandati** | **Tumbleweed Minimal-VM: `solver.onlyRequires = true`** (`/usr/etc/zypp/zypp.conf.d/no-recommends.conf`); gli altri come di serie | **Tumbleweed: raccomandati installati**, 2706 pacchetti contro 1057 (+1701: PackageKit, Firefox, gstreamer-plugins-good, pipewire-pulseaudio/jack, VLC, i pattern `office`, `multimedia`, `games`, `kde_pim`…); apt con raccomandati su Debian e Ubuntu, dnf con i deboli, come nelle cloud |
| **pacchetti** | Ubuntu: il desktop cloud è `ubuntu-desktop` pieno (+219: git, deja-dup, gnome-calendar, lvm2…) | Ubuntu: l'ISO mette `ubuntu-desktop-minimal` (la «selezione predefinita»), più snap (snap-store, firmware-updater, desktop-security-center); Fedora: **`noopenh264`** al posto di `openh264`/`mozilla-openh264` della cloud; Arch: `intel-media-driver`, vulkan-intel/radeon/nouveau, xf86-video-*, linux-firmware, `pipewire-jack`/`-alsa` (la cloud ha `jack2`); Debian: nftables installato ma senza regole, exim4 non c'è |
| **root** | bloccata dappertutto | bloccata dappertutto, **tranne Tumbleweed: stessa parola dell'utente** (la casella di serie) |
| **PAM** | `pam_faillock`: Arch in 5 file, Tumbleweed in 2, gli altri in 0 | uguale |
| **in ascolto** | Debian e Fedora: LLMNR 5355 (resolved), exim su 25 (Debian) | niente 5355 su Debian; cups 631 quasi dappertutto; Arch solo 22 |
| **firmware** | BIOS (SeaBIOS) | UEFI (OVMF, senza Secure Boot) |
| **cloud-init** | c'è dappertutto | non c'è |

## In breve: che cosa vuol dire per l'installatore

1. **La porta 7447 è chiusa su Alma e Tumbleweed ISO**, ed è aperta senza fare niente su Fedora
   Workstation. Sulla cloud Tumbleweed invece non c'è nessun firewall: una prova solo su DESKTOP
   non vedrebbe il firewall da aprire.
2. **I gruppi `video`/`render`**: su Debian ISO `video` c'è già; `render` non c'è da nessuna parte.
3. **La rete sulle cloud Debian, Ubuntu e Arch non è NetworkManager**: le macchine vere sì.
4. **Tumbleweed ISO**: accesso automatico acceso (c'è già un desktop aperto), snapper su btrfs (foto
   a ogni zypper), raccomandati installati, root con la parola dell'utente.
5. **Alma ISO su LVM**, **Fedora ISO con `noopenh264`**, **Ubuntu ISO col desktop minimo**.

## Note del banco

- Arch: il primo giro di archinstall è fallito, perché `sector_size: null` non passa in 4.4. Serve
  `{"unit": "B", "value": 512}`, ed è corretto. Al secondo giro il copione `da-iso` si è fermato
  senza messaggio dopo l'installazione (archinstall rc=0), per una causa non trovata. Primo avvio,
  impronta, spegnimento e foto li ho fatti a mano, coi comandi del banco.
- Tumbleweed: la ISO NET offre quattro prodotti (Aeon, Kalpa, MicroOS, openSUSE), e AutoYaST vuole
  `<products>openSUSE</products>`. L'ho aggiunto.
- L'impronta leggeva SELinux con `getenforce`, che su openSUSE non è nel PATH dell'utente, e dava
  «assente». Ora legge `/sys/fs/selinux/enforce`. Sulle due Tumbleweed l'ho controllato a mano:
  Enforcing.
