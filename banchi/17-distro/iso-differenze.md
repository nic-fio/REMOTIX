# The ISO state: what changes compared with cloud + DESKTOP (fasi/17 §7.2)

The ISO machine is installed **from the official ISO**, with the distribution's automatic
installer (`17-vm.sh da-iso <machine>-iso`, answers in `iso-risposte/`), on a new disk
and with UEFI firmware. Compared with the default choices, the answers add only three things, all
inside the installation: the ssh server where there is none by default, the bench key and passwordless
sudo (`/etc/sudoers.d/90-banco`). Italian language, it keyboard, Europe/Rome time zone: like an
Italian customer.

The comparison is made with `17-vm.sh impronta <machine> cliente` and `impronta <machine>-iso iso`.
The machine starts from the read-only snapshot (`-snapshot`) and on its own ports (k=6). The files are
on the server: `…/<machine>{,-iso}/{impronta,pacchetti,unita}-{cliente,iso}.txt`. All measured
on 29 Sep 2026 `[M]`.

## The machines

| machine | done | time | ISO and installer |
|---|---|---|---|
| debian13-gnome | ✅ | 10 min | debian-13.7.0-amd64-netinst, preseed |
| ubuntu2604-gnome | ✅ | 11 min | ubuntu-26.04.1-desktop, autoinstall (the desktop path goes all the way) |
| fedora44-gnome | ✅ | 7 min | Fedora-Everything-netinst 44-1.7, kickstart, `@^workstation-product-environment` |
| alma10-gnome | ✅ | 7 min | AlmaLinux-10.2 boot, kickstart, `@^graphical-server-environment` |
| arch-kde | ✅ | ~10 min | archlinux-2026.09.01, archinstall 4.4, Desktop/KDE Plasma profile, sddm |
| tumbleweed-kde | ✅ | 14 min | Tumbleweed NET Snapshot20260924, AutoYaST, the default KDE role's patterns |

All the ISOs are verified with the sha256 from the official site. After the reboot, on every machine
ssh answered, sudo works and `graphical.target` is active.

## The differences that matter for the installer

| | cloud + DESKTOP (`cliente` snapshot) | ISO (`iso` snapshot) |
|---|---|---|
| **user's groups** | only their own group, everywhere (cloud-init) | Debian: `cdrom floppy sudo audio dip video plugdev users netdev scanner bluetooth lpadmin`, i.e. **`video` is already there**; Ubuntu: `adm cdrom sudo dip plugdev users lpadmin lxd`, without `video`; Fedora, Alma and Arch: `wheel`; Tumbleweed: none. **`render` is never there.** |
| **firewall** | Fedora: zone `public` (ssh mdns dhcpv6); Alma: `public` (ssh cockpit dhcpv6); **Tumbleweed: no firewall**; Debian and Arch: none; Ubuntu: ufw installed but off | **Fedora: zone `FedoraWorkstation`, with 1025-65535 tcp/udp OPEN** (7447 passes without doing anything); Alma: `public` (ssh cockpit dhcpv6) like the cloud one, so 7447 is closed; **Tumbleweed: firewalld on, `public` with only dhcpv6 and ssh (ssh opened by us), so 7447 is closed**; Debian and Arch: none; Ubuntu: ufw off |
| **SELinux / AppArmor** | Fedora, Alma, Tumbleweed: SELinux Enforcing; Debian, Ubuntu: AppArmor; Arch: nothing | the same. On Tumbleweed SELinux is Enforcing in both, with `selinux-policy-targeted`. |
| **network** | Debian and Ubuntu: **systemd-networkd + netplan `50-cloud-init.yaml`** (NM is there but does not manage the interface), resolved on; Arch: **networkd + resolved, NM off**; Fedora, Alma, Tumbleweed: NetworkManager | **NetworkManager everywhere**. Ubuntu: netplan `01-network-manager-all.yaml`. resolved: on for Ubuntu and Fedora, off for Debian, Arch and Tumbleweed. |
| **display manager** | gdm (Debian, Ubuntu, Fedora, Alma), sddm (Arch), `display-manager.service` (Tumbleweed) | the same, but Tumbleweed uses `display-manager-legacy.service` with **automatic login** (`DISPLAYMANAGER_AUTOLOGIN="nicfio"`, the default box), so there is already a session open on the screen |
| **disk and system snapshots** | ext4 (Debian, Ubuntu), btrfs (Fedora, Arch), xfs (Alma, Tumbleweed); no snapper | Debian ext4 + swap on a partition; Ubuntu ext4 + `/swap.img`; Fedora btrfs + zram; Alma **LVM** + xfs; Arch ext4 + zram; **Tumbleweed btrfs with snapper** (config `root`, 3 snapshots already after installation; `/` is `/@/.snapshots/1/snapshot`). So every REMOTIX zypper leaves a pre/post snapshot. |
| **recommends** | **Tumbleweed Minimal-VM: `solver.onlyRequires = true`** (`/usr/etc/zypp/zypp.conf.d/no-recommends.conf`); the others as default | **Tumbleweed: recommends installed**, 2706 packages against 1057 (+1701: PackageKit, Firefox, gstreamer-plugins-good, pipewire-pulseaudio/jack, VLC, the `office`, `multimedia`, `games`, `kde_pim` patterns…); apt with recommends on Debian and Ubuntu, dnf with weak deps, as in the cloud ones |
| **packages** | Ubuntu: the cloud desktop is full `ubuntu-desktop` (+219: git, deja-dup, gnome-calendar, lvm2…) | Ubuntu: the ISO installs `ubuntu-desktop-minimal` (the "default selection"), plus snaps (snap-store, firmware-updater, desktop-security-center); Fedora: **`noopenh264`** instead of the cloud's `openh264`/`mozilla-openh264`; Arch: `intel-media-driver`, vulkan-intel/radeon/nouveau, xf86-video-*, linux-firmware, `pipewire-jack`/`-alsa` (the cloud has `jack2`); Debian: nftables installed but with no rules, exim4 is not there |
| **root** | locked everywhere | locked everywhere, **except Tumbleweed: same password as the user** (the default box) |
| **PAM** | `pam_faillock`: Arch in 5 files, Tumbleweed in 2, the others in 0 | the same |
| **listening** | Debian and Fedora: LLMNR 5355 (resolved), exim on 25 (Debian) | no 5355 on Debian; cups 631 almost everywhere; Arch only 22 |
| **firmware** | BIOS (SeaBIOS) | UEFI (OVMF, without Secure Boot) |
| **cloud-init** | there everywhere | not there |

## In short: what it means for the installer

1. **Port 7447 is closed on Alma and Tumbleweed ISO**, and is open without doing anything on Fedora
   Workstation. On the cloud Tumbleweed instead there is no firewall at all: a test only on DESKTOP
   would not see the firewall to open.
2. **The `video`/`render` groups**: on Debian ISO `video` is already there; `render` is nowhere.
3. **The network on the Debian, Ubuntu and Arch cloud images is not NetworkManager**: the real machines are.
4. **Tumbleweed ISO**: automatic login on (there is already a desktop open), snapper on btrfs (a snapshot
   at every zypper), recommends installed, root with the user's password.
5. **Alma ISO on LVM**, **Fedora ISO with `noopenh264`**, **Ubuntu ISO with the minimal desktop**.

## Bench notes

- Arch: the first archinstall run failed, because `sector_size: null` does not pass in 4.4. It needs
  `{"unit": "B", "value": 512}`, and it is fixed. On the second run the `da-iso` script stopped
  without a message after the installation (archinstall rc=0), for a cause not found. First boot,
  fingerprint, power-off and snapshot I did by hand, with the bench's commands.
- Tumbleweed: the NET ISO offers four products (Aeon, Kalpa, MicroOS, openSUSE), and AutoYaST wants
  `<products>openSUSE</products>`. I added it.
- The fingerprint read SELinux with `getenforce`, which on openSUSE is not in the user's PATH, and gave
  "absent". Now it reads `/sys/fs/selinux/enforce`. On the two Tumbleweed machines I checked by hand:
  Enforcing.
