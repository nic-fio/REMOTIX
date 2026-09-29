# Lo stato ISO: che cosa cambia rispetto a cloud + DESKTOP (fasi/17 §7.2)

La macchina ISO è installata **dall'ISO ufficiale** con l'installatore automatico
(`17-vm.sh da-iso <macchina>-iso`, risposte in `iso-risposte/`), disco nuovo, UEFI.
Rispetto alle scelte di serie, le risposte aggiungono solo tre cose, tutte dentro
l'installazione: il server ssh (dove non c'è di serie), la chiave del banco, e sudo
senza parola (`/etc/sudoers.d/90-banco`). Lingua italiana, tastiera it, fuso Europe/Rome.

Il confronto con la macchina cloud si fa con `17-vm.sh impronta <macchina> cliente`:
la macchina parte dalla foto «cliente» in sola lettura (`-snapshot`), su porte sue.

## Stato al 29 set 2026, sera

| macchina | fatta | tempo | ISO |
|---|---|---|---|
| debian13-gnome | ✅ | 9 min | debian-13.7.0-amd64-netinst.iso (preseed) |
| fedora44-gnome | ✅ | 7 min | Fedora-Everything-netinst-x86_64-44-1.7.iso (kickstart) |
| alma10-gnome | 🔨 installazione in corso | — | AlmaLinux-10.2-x86_64-boot.iso (kickstart) |
| ubuntu2604-gnome | 🔨 in corso (le risposte sono state lette) | — | ubuntu-26.04.1-desktop-amd64.iso (autoinstall) |
| arch-kde | ⏳ preparata, non accesa | — | archlinux-2026.09.01-x86_64.iso (archinstall 4.4) |
| tumbleweed-kde | ⏳ preparata, non accesa | — | openSUSE-Tumbleweed-NET Snapshot20260924 (AutoYaST) |

Tutte e sei le ISO sono scaricate in `/media/REMOTIX/vm17/iso/` e verificate con la
sha256 del sito ufficiale.

## Che cosa si vede nelle macchine ISO (misurato)

**fedora44-gnome-iso** `[M]`: SELinux Enforcing; firewalld acceso, zona
**FedoraWorkstation** (ssh, samba-client, dhcpv6-client e **1025-65535 tcp/udp aperte**); gdm;
sessioni solo Wayland (gnome, gnome-classic); NetworkManager + resolved; radice **btrfs**,
swap su zram; flatpak con il deposito fedora; 1915 pacchetti; niente cloud-init; root bloccata;
utente in `wheel`.

**debian13-gnome-iso** `[M]`: AppArmor attivo, niente SELinux; **nessun firewall**
(né firewalld né ufw, 0 regole nft); gdm, sessioni Wayland **e X11**; NetworkManager, resolved
spento; radice ext4; 1590 pacchetti; niente cloud-init; root bloccata; l'utente è nei gruppi
che dà l'installatore: `cdrom floppy sudo audio dip video plugdev users netdev scanner
bluetooth lpadmin` — ⚠ **`video` c'è già** (dall'installatore Debian, non da noi), `render` no.

## Differenze con cloud + DESKTOP

⛔ Non ancora misurate: il confronto `impronta … cliente` va fatto con le VM libere.
Da guardare per prima cosa: gruppi dell'utente (cloud-init non dà `video`), firewall e zona,
cloud-init e netplan/networkd sulle immagini cloud, file system della radice, flatpak.
