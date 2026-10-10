# Phase 17 — The installer, and REMOTIX on Linux in general

*Opened by the user on **29 Sep 2026**, with phase 16 closed in its numbers. This document fixes,
**before** the work, everything the phase will do: the question, what the survey of the distributions
found, the shape of the installer, the milestones, the tests, and the decisions that belong to the user.
The decisions taken are also in `DECISIONI.md` §10; here is the how.*

*Marks: `[M]` measured on the hardware · `[L]` read in a primary source (sources, package files,
official documentation) · `[D]` deduced · `[?]` to be confirmed. The survey of 29 September is
almost all `[L]`: no distribution other than Debian has run REMOTIX yet.*

---

## 1. The question

REMOTIX was born and grew up on **Debian 13 Trixie**. The goal is for it to run **on Linux in general**,
and to be installed with a **professional system, of absolute excellence**.

The user's words (29 Sep 2026):

> *«Al momento REMOTIX è stato sviluppato su Debian Trixie, ma l'obiettivo è farlo girare su Linux in
> generale. Per ottenere questo risultato, e quindi avere basi solide per costruire l'installer, è
> necessario fare un'indagine approfondita sulle principali distro.»*
>
> *«REMOTIX dovrà essere dotato di un sistema di installazione professionale, di assoluta eccellenza.»*

⇒ The installer is a **product requirement**, not an end-of-work finishing touch, and it is measured like
the rest. It is a real subsystem: wide (distributions × desktops × cards × three jobs), even though
each of its pieces is known and others have already solved it.

**"Installing" is three jobs**, and the installer does all three:

| | the machine before | what must happen |
|---|---|---|
| **first installation** | REMOTIX is not there | check that the machine has what is needed, install, say how to get in |
| **update** | REMOTIX is there and **in use**: maybe 5 people connected | change version **without closing the desktops** of those connected |
| **uninstallation** | REMOTIX is there | remove it, and the machine **goes back to how it was** |

---

## 2. The user's decisions (29 Sep 2026)

| | decision | why |
|---|---|---|
| **Linux in general** | Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE | `DECISIONI.md` §10.1 |
| **an installer of excellence** | product requirement, with measurable tests | `DECISIONI.md` §10.2 |
| **first the survey, then the installer** | the installer is written only once, already knowing the differences | done on 29 Sep, §4 |
| **the tests in VIRTUAL MACHINES, not in the boxes** | *«stavolta non dobbiamo misurare le performance, ma il corretto funzionamento dell'installer, quindi la potenza bruta della GPU non serve»* | a VM has the kernel, SELinux, firewall and boot **of the distribution**; a box uses the server's kernel (Debian) and would say "all fine" where the real machine would refuse |
| **the engine in eight phases** | PREFLIGHT, COMPATIBILITY, PLANNING, CONSENT & SAFETY, ACQUISITION, INSTALLATION & CONFIGURATION, VERIFICATION & CERTIFICATION, COMMIT / ROLLBACK | the user's proposal, strengthened at his request (TRUST, three outcomes per desktop, the plan as a document, the switch-on between 7a and 7b, RESUME), §6.0 |
| **TUI and GUI indispensable** | *«su TUI e GUI dico che è un requisito irrinunciabile»* — ⛔ superseded on 5 Oct: no GUI, only a polished TUI (`DECISIONI.md` §10.31); GUI removed from the code on 10 Oct | §6.6.1, D12 |
| **the missing dependencies are brought by REMOTIX** | *«se ci sono pacchetti/dipendenze assenti da una particolare distro, REMOTIX le deve includere e/o scaricare»*; exception the patented codecs, boundary the desktops | `DECISIONI.md` §10.6; D2 closed |
| **one VM per desktop** | *«4 VM distinte, esempio Ubuntu/GNOME, Ubuntu/KDE, Ubuntu/XFCE, Ubuntu/LXQt»* | the customer usually has **one** desktop: with four together, a piece forgotten for XFCE would arrive anyway dragged in by KDE, and the test would say green |

---

## 3. Where REMOTIX can run: the matrix

Distributions and desktops that enter the phase (✅ = to port and test; ⛔ = out, with the why).

| distribution | GNOME | KDE | XFCE | LXQt | notes |
|---|---|---|---|---|---|
| **Debian 13** (reference) | ✅ | ✅ | ✅ | ✅ | today's base |
| **Ubuntu 26.04 LTS** | ✅ | ✅ | ✅ | ✅ | GNOME 50 (§5.1); the "vanilla" GNOME must be installed (§4.6) |
| Ubuntu 24.04 LTS | ⛔ | ⛔ | ⛔ | ⛔ | **out** (D7, the user's decision of 29 Sep): we start from 26.04. KDE 5.27, XFCE 4.18 and LXQt 1.4 do not run on Wayland; GNOME 46 does, but would require bundling OpenSSL 3.5 and two adaptations for ffmpeg 6.1 and libei 1.2. With it Mint 22 stays out too (Mint 23 will be "compatible, not certified") |
| **Fedora 44** | ✅ | ✅ | ✅ | ✅ | GNOME 50; H.264 from RPM Fusion (§4.2) |
| Fedora 43 | · | · | · | · | **analysed, not certified**: GNOME 49, leaves support at the end of 2026; its bare VM is there for comparisons |
| **Alma 10** (certified) · Rocky / RHEL 10 (compatible, not certified) | ✅ | ✅ | ⛔ | ⛔ | KDE from EPEL; neither labwc nor XFCE nor LXQt in RHEL/EPEL 10; on AMD no VA-API (Mesa without it) |
| **Arch** (Manjaro, EndeavourOS) | ✅ | ✅ | ✅ | ✅ | all official, including ngtcp2 1.25 and the codecs |
| **openSUSE Tumbleweed** | ✅ | ✅ | ✅ | ✅ | GNOME 50; H.264 only with Packman (§4.2) |
| **openSUSE Leap 16** | ✅ | ✅ | ✅ | ✅ | XFCE and LXQt under Wayland "experimental" for SUSE; ngtcp2 to be bundled |

**Out, and why** (`[L]`):
- **Debian 12** and **RHEL 9**: mutter 43 / GNOME 40, no libei, no labwc — the base is too old.
- **openSUSE Leap 15.6**: end of life on 30 April 2026. **SLES 16**: only GNOME, no Packman — to be
  reconsidered if a customer asks for it.
- **Linux Mint Cinnamon**: it is not one of the four desktops (Muffin does not have mutter's APIs). Mint 22
  carries the limits of Ubuntu 24.04.
- **Distributions without systemd** (Alpine, Devuan, Artix with OpenRC…): REMOTIX uses logind, the user
  manager and `systemctl --user` everywhere (`figlio.c:1158-1163`). It must be written in the requirements.
- **Immutable ones** (Silverblue/Kinoite, Aeon/Kalpa, Ubuntu Core, SteamOS): `/usr` read-only, groups
  in `/usr/lib/group`, installation with a reboot. Postponed until after the phase (§12, D9).

⇒ **The certification matrix: 26 virtual machines** — Debian 13, Ubuntu 26.04, Fedora 44, Arch,
Tumbleweed, Leap 16 × 4 desktops (24), plus Alma 10 × 2 (GNOME, KDE) = **26**. **Fedora 43 and Ubuntu 24.04 (D7) are analysed but outside
the matrix.**

⚠ **What is certified, and what is not.** Only what runs in our VMs is certified: **Alma 10**,
not "the RHEL 10 family". Rocky 10 and RHEL 10 are declared **compatible, not certified**: same
package base, but nobody has tested them. The same for Manjaro and EndeavourOS with respect to Arch,
and for Mint 23 with respect to Ubuntu 26.04. A derivative becomes certified only with its own VM in the
matrix.

### 3.1 The supported versions — for the technical manual

*The user's request (30 Sep 2026): «andrà documentato, anche nel manuale tecnico, da quali versioni gli
SO sono supportati da REMOTIX». ⚠ The single source is the engine's **catalog** (§6.6.8): the manual's
table is **generated** from the catalog at every release, not copied by hand. This is today's.*

**The distributions**

| distribution | minimum version | status | desktops | conditions |
|---|---|---|---|---|
| Debian | **13** (Trixie) | certified | GNOME, KDE, XFCE, LXQt | — |
| Ubuntu | **26.04 LTS** | certified | GNOME, KDE, XFCE, LXQt | `gnome-session` for GNOME (D8) |
| Fedora | **44** | certified | GNOME, KDE, XFCE, LXQt | H.264: RPM Fusion (D5); PAM without `pam_selinux` until T6 |
| AlmaLinux | **10.1** (OpenSSL 3.5) | certified | GNOME, KDE | EPEL and CRB; H.264: RPM Fusion; no XFCE/LXQt |
| Arch Linux | rolling (from Sep 2026) | certified | GNOME, KDE, XFCE, LXQt | — |
| openSUSE Tumbleweed | rolling (from Sep 2026) | certified | GNOME, KDE, XFCE, LXQt | H.264: Packman; `breeze6-wallpapers` (KDE) |
| openSUSE Leap | **16.0** | certified | GNOME, KDE, XFCE, LXQt | H.264: Packman; a scalable font for LXQt (`google-droid-fonts`) |
| Rocky Linux, RHEL | 10.1 | compatible, not certified | GNOME, KDE | like Alma |
| Manjaro, EndeavourOS | rolling | compatible, not certified | like Arch | Manjaro is a few weeks behind |
| Linux Mint | **23** (base 26.04) | compatible, not certified | those of Ubuntu (not Cinnamon) | like Ubuntu |

**The principle** (`DECISIONI.md` §10.9): a new product, new-generation technologies; a version
**enters** when it has the minimum components and passes the round on the VMs, **leaves** when the distribution stops
updating it.

**Out, and why**: Debian 12 and RHEL 9 (base too old: mutter 43/GNOME 40, no libei, no
labwc); Ubuntu 24.04 and Mint 22 (D7); Fedora 43 (out of support at the end of 2026); openSUSE Leap 15.6 (end of life);
SLES 16 (only GNOME, no Packman: reconsidered on request); distributions without systemd; immutable ones (D9).

**The minimum versions of the components** (for whoever uses a distribution not in the list; `[L]` from the code and from the
phase's measurements):

| component | minimum | why |
|---|---|---|
| Linux kernel | that of the oldest certified distribution (6.12) | i915/xe and amdgpu drivers, DMA-BUF |
| systemd / logind | with `systemctl --user` and `Remote=yes` sessions | the per-user sessions |
| OpenSSL | **3.5** | the QUIC API of the `ngtcp2_crypto_ossl` bridge |
| ngtcp2 / nghttp3 | 1.25.0 / 1.18.0 | inside the binary (`DECISIONI.md` §10.6) |
| libavcodec (ffmpeg) | **61.13.100** (ffmpeg 7.1) | `avcodec_get_supported_config` |
| libei | 1.3 | `ei_disconnect` |
| PipeWire | 0.3.48 | the capture of GNOME and KDE |
| GNOME (mutter) | **46** (`ConnectToEIS` API, `--headless`); from 50 the `@user` unit | `sessione.c` |
| KDE Plasma (KWin) | **6.1** (`connectToEIS`) | `kwin.c` |
| XFCE | **4.20** (Wayland) | the session under labwc |
| LXQt | **2.0** (Wayland) | the session under labwc |
| labwc / wlroots | labwc 0.8 with `-m/-C/-S`; wlroots 0.18 (screencopy, virtual pointer/keyboard, data-control, output-management) | `wlroots.c`, `sessione.c` |
| a scalable font | any (DejaVu, Noto, Droid…) | without one, labwc dies (labwc #2525) |
| VA-API | driver with H.264 encoding (`iHD` Intel, `radeonsi` AMD) — ⭐ **integrated** cards are fine: the test server is an integrated Intel UHD 770; proprietary NVIDIA no | encoding on the card (the software fallback is gone since phase 19, §10.27) |
| Vulkan Video (AMD, NVIDIA) | AMD: Mesa's RADV; **NVIDIA: proprietary driver ≥ 550 with its Vulkan ICD**, installed by the customer (`DECISIONI.md` §10.34). `[?]` The minimum NVIDIA card generation is not measured: only an RTX 4090 was tested; "from RTX 20 / T4 up" was the rental's advice. NVIDIA certified on Ubuntu 26.04 (phase 19), compatible elsewhere | encoding on the card; ⛔ no software fallback since phase 19 (§10.27) |

---

## 4. What the survey found

Five searches in parallel on 29 September (Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE, and "how
the best ones install"), then two verifications sent to **refute them** (one on the distributions, one on
the REMOTIX code). The verification on the distributions is `[?]` until it comes back: the points it touches are
marked.

### 4.1 The items, family by family

| item | Debian 13 | Ubuntu 26.04 | Fedora 44 | RHEL/Alma 10 | Arch | openSUSE TW / Leap 16 |
|---|---|---|---|---|---|---|
| **H.264 on the card** | ✅ | ✅ Mesa with the codecs | ⛔ Intel and AMD: RPM Fusion | Intel: RPM Fusion; ⛔ AMD: Mesa without VA-API | ✅ all official | ⛔ ffmpeg without `h264_vaapi`: Packman needed |
| **x264 software fallback** | ✅ | ✅ | ⛔ only RPM Fusion | ⛔ only RPM Fusion | ✅ | ⛔ only Packman |
| **OpenSSL ≥ 3.5** (QUIC) | ✅ 3.5 | ✅ 3.5 (26.10: **4.0**) | ✅ 3.5 | ✅ from 10.1 | ✅ 3.6 | ✅ 3.5 |
| **ngtcp2 ≥ 1.25** | from source | ⛔ 1.16 | ⛔ 1.21 | ⛔ 1.22 (EPEL) | ✅ 1.25 | TW ✅ · Leap ⛔ 1.6 |
| **PAM** | `common-*` ✅ | `common-*` ✅ | ⛔ `password-auth` | ⛔ `password-auth` | ⛔ `system-auth`, no `@include` | ⛔ a different name, and in `/usr/lib/pam.d` |
| **SELinux / AppArmor** | — | AppArmor, does not affect us | SELinux **active** | SELinux **active** | — | SELinux **active** (TW since 2025, Leap 16) |
| **default firewall** | — | ufw (off) | firewalld (Workstation: port open; Server: closed) | firewalld, **closed** | — (EndeavourOS: firewalld) | firewalld, **closed** |
| **GNOME** | 48 | **50** ⚠ §5.1 | **50** ⚠ | 47→49 | **50** ⚠ | TW **50** ⚠ · Leap 48 |
| **KDE Plasma** | 6.3 | 6.6 | 6.x | 6.x (EPEL) | 6.7 | 6.7 · 6.4 |
| **labwc** (XFCE, LXQt) | 0.8.3 | 0.9.3 | 0.9.6 | ⛔ absent | 0.20.2 | 0.20.2 · 0.8.1 |
| **new services** | enabled | enabled | **disabled** (preset) | disabled | **disabled** (`disable *`) | disabled |

`[M]` 29 Sep, from the official images booted in a VM: SELinux **Enforcing** on Fedora 43/44 and Alma 10;
on openSUSE the processes have the SELinux label but the minimal image has no `getenforce` (`[?]`);
**no firewall active** in any *cloud* image — at the customer's, who installs from the ISO, it will not
be so: the firewall tests turn it on on purpose (R2).

### 4.2 H.264 encoding and the patents

REMOTIX **does not contain** an H.264 encoder: it uses the card's (`h264_vaapi`, via libavcodec
and VA-API) and, as a fallback, the distribution's `libx264` (`codificatore.c:1350`).

Fedora and openSUSE remove H.264 from their packages because of the patents, in different places:
- **Fedora**: the "free" ffmpeg has `h264_vaapi`, but **no card encodes H.264 out of the box**: Mesa is
  built without it (AMD ⇒ `mesa-va-drivers-freeworld` from RPM Fusion), and the reduced Intel driver
  (`intel-media-driver-free`) is built with `AVC_Encode_VDEnc_Supported=no` and
  `AVC_Encode_VME_Supported=no` since 2023 (Intel ⇒ `intel-media-driver` from RPM Fusion) `[L]` spec F44.
- **openSUSE**: the official ffmpeg **does not have `h264_vaapi`** (`[L]` in the encoder list of
  Tumbleweed's `libavcodec62-8.1.2`, opened: there are `av1/vp9/mpeg2_vaapi` and `libopenh264`). Without Packman REMOTIX does not encode, on any card: **the worst case**.
- **RHEL 10**: Mesa built **without VA-API**, and RPM Fusion does not replace it: on AMD nothing; EPEL 10
  does not even have the Intel driver. ⇒ On RHEL/Alma 10 video on the card exists only with third-party
  repositories, and XFCE/LXQt are not there: **a weak target**, kept for GNOME and KDE with the declared fallback.
- **NVIDIA with the proprietary driver**: does not encode via VA-API on any distribution `[D]`. The
  preliminary check recognises it and says so beforehand.

⇒ Rules for the installer:
1. ⛔ **Never distribute an implementation of H.264** (neither x264 nor a "complete" ffmpeg inside the
   package): REMOTIX **uses** the machine's, as gnome-remote-desktop does inside Fedora.
2. ⛔ **Never add third-party repositories silently** (RPM Fusion, Packman): the preliminary check
   **says so**, with the exact command, and does it only if the administrator consents (D5).
3. It is not legal advice: before distributing at large, a lawyer is needed. The last H.264 patent
   expires between 2027 and 2030 (the sources disagree).

### 4.3 PAM: the access file

`/etc/pam.d/remotix` (source `src/remotix.pam`) tells the system which checks to do when
someone types name and password in the page. Today it refers to Debian's standard checks
(`@include common-auth`, lines 43, 48, 50, 83). ⛔ And `@include` itself is **a Debian modification** to
Linux-PAM (patch `031_pam_include`): elsewhere the line is "illegal module type" and **authentication
fails too** `[L]`. ⇒ On Fedora, RHEL, Arch and openSUSE today **nobody gets in**.

⇒ **One file per family**, as Cockpit does (which does the same job on all four):

| family | base | where |
|---|---|---|
| Debian/Ubuntu | like `/etc/pam.d/sshd`: `common-auth`, `pam_nologin` + `common-account`, `pam_selinux` (silent without SELinux), `pam_loginuid`, `pam_keyinit`, `common-session`, `pam_motd`, `pam_mail`, `pam_limits`, `pam_env`, `common-password` | `/etc/pam.d/remotix` |
| Fedora/RHEL | like `/etc/pam.d/sshd`: `password-auth` + `postlogin`, `pam_sepermit` and `pam_nologin` in account, `pam_selinux close/open`, `pam_loginuid`, `pam_namespace`, `pam_keyinit`, `pam_motd` | `/etc/pam.d/remotix` |
| openSUSE | like `/usr/lib/pam.d/sshd`: `common-*` (substack) + `postlogin-*`, `pam_loginuid`, `pam_keyinit`, `pam_motd`; `pam_selinux` comes from `common-session` | **`/usr/lib/pam.d/remotix`** |
| Arch | like `/etc/pam.d/sshd`: `system-remote-login` | `/etc/pam.d/remotix` |

In all of them: `pam_systemd` (without it, the desktop is not born) and **root excluded** by default.
⭐ **T6 (30 Sep, D3 closed, DECISIONI §10.18): each file is the distribution's sshd stack line by line**
(`[M]` read on the "iso" VMs with `banchi/17-t6/t6-leggi-pam.sh`: Fedora and Alma identical, Tumbleweed and
Leap identical, Debian and Ubuntu identical), with ONE extra line at the top: root excluded. Where SELinux is present
(Fedora, Alma, openSUSE) the transition to the user's context is allowed by the `remotix-selinux` module.
On Arch also `pam_systemd_home`, or `systemd-homed` users do not get in `[?]` to be measured.

⚠ **The lockout on attempts.** Arch (and Fedora/RHEL with authselect) put `pam_faillock` in the default
stack: three wrong passwords in 15 minutes lock the account for 10 minutes — **even for whoever
sits in front of the machine** (`[L]` pambase: `pam_faillock` without parameters ⇒ deny=3,
fail_interval=900 s, unlock_time=600 s). Remotely, anyone who reaches the port and knows a user
name can lock out the owner; the per-address ban is not enough if the attempts come from
several addresses. ⇒ **Decision D3.**

### 4.4 The REMOTIX code: the things tied to Debian

Confirmed by the verification on the code (`[L]`), with the right line:

| where | what | cure |
|---|---|---|
| `src/remotix.pam:43,48,50,83` | `@include common-*` | one file per family (§4.3) |
| `src/sessione.h:95`, `sessione.c:1850-1960` | the `--headless` drop-in for `org.gnome.Shell@wayland.service` | GNOME 50 calls it `@user` (§5.1) |
| `src/main.c:348-358`, `autenticazione.c:158` | the warning looks for the PAM only in `/etc/pam.d`, and the message about "other" is **wrong even on Debian** | look in `/usr/lib/pam.d` too; right text |
| `src/kwin.c:48` (`main.c:1924`) | writes `/usr/share/applications/org.kde.remotix.desktop` **while running**, as root | the package brings it; at run time only the check (`kwin.c:342`) |
| `src/Makefile:238-239` | `-L… /lib` and rpath on `lib` (Fedora/SUSE: `lib64`) | static ngtcp2/nghttp3 (§6.3): rpath no longer needed |
| `src/Makefile:33` | declares libavcodec ≥ 61, 7.1 is needed; `dipendenze` checks only the headers | real minimum versions, checked |
| `src/codificatore.c:1419,1436` | `avcodec_get_supported_config` (missing in Ubuntu 24.04's ffmpeg 6.1) | an `#if`, only if D7 says yes |
| `src/certificati.c:149` | `const` with OpenSSL 4.0 (Ubuntu 26.10, Fedora rawhide) | 5 lines |
| `src/figlio.c:4684` | fixed `renderD128` node for the encoder | with several cards it takes the wrong one: choose by the driver |
| `src/sessione.c:2236` | session log with a predictable name in `/tmp` | another user can create it first: move it to `~/.local/state/remotix/` |
| `src/sessione.h:94,96` | GNOME recognised by the mere presence of `gnome-session`, session always `gnome` | on Ubuntu the "vanilla" GNOME is needed (§4.6) |
| `src/provisiona.sh` | users `prova`/`prova2` with a plaintext password, the benches' `sudoers`, `gpu-udev.sh`, `ld.so.conf.d` | ⛔ it is a **bench** provisioner: the installer is written from scratch, and none of this enters the package |
| `src/Contenitore` | `debian:13` image, `apt`, pkgconfig `x86_64-linux-gnu` | one build container per family |

Minimum versions never declared, to be written: labwc with `-m/-C/-S` (tuned on 0.8.3), KWin ≥ 6.1
(`connectToEIS`), mutter's APIs, `wlr-randr` (LXQt), `xfconfd.service`, OpenSSL ≥ 3.5, ngtcp2 ≥ 1.25.

### 4.5 The bench function in the binary

The plan asked that the installed binary **not contain** the bench function (`BANCO_MARCA`,
`BANCO_ESITO`). `[L]` The code is always compiled, but turned off by `#define BANCO_ACCESO 0`
(`rcp.c:186`): the server refuses every mark and declares it. ⇒ Today's binary is already "product-grade"
for this function. Other tools remain compiled (`--audio-prova`, `--rilievo`, `--comando-socket`,
`--sblocca`, `--parlantina`, the snapshot with `SIGUSR1/2`): the package's unit **does not pass them**, and the
R13 test checks those too.

### 4.6 Other differences the installer must handle

- **Ubuntu**: the default GNOME is the `ubuntu` session (dock, Ubuntu colours); REMOTIX starts the
  `gnome` session, which exists only with the `gnome-session` package (universe) ⇒ either it is brought as a dependency, or
  REMOTIX learns the `ubuntu` session (**decision D8**: which GNOME does whoever connects see?).
- **labwc** is not installed by any default XFCE/LXQt group (Xubuntu and Lubuntu stay on X11):
  the installer brings it.
- **`video`/`render` groups**: different numbers from one machine to another — the code already reads them from
  the card's node (`provisiona.sh:71-83`). On Arch `renderD*` is open to everyone (0666).
- **`/etc/login.defs`**: on openSUSE it is in `/usr/etc` (the script works today by chance).
- **Firmware** split into pieces on Arch (`linux-firmware-intel`, `-amdgpu`).
- **Rolling release** (Arch, Tumbleweed): ffmpeg and ngtcp2 often change the library number; a
  prebuilt binary would break at the first system update ⇒ the package is tied to the exact
  version, or is rebuilt at every change (§6.2).

---

## 5. The two product cures that come BEFORE the installer

### 5.1 GNOME 50: the Shell's service has changed name

`[L]` Since GNOME 50 (Fedora 44, Ubuntu 26.04, Tumbleweed, Arch; sooner or later Debian) the
`org.gnome.Shell@wayland.service` unit no longer exists: there is `org.gnome.Shell@.service` with
`ExecStart=gnome-shell --mode=%i`, and the session asks for `org.gnome.Shell@user.service`. Our
drop-in with `--headless` ends up under a name nobody uses ⇒ the Shell is born **without a virtual
screen**. gnome-session 49+ has also been rewritten (REMOTIX knows the internal mechanisms
of 48 in depth, `sessione.h:420-523`) ⇒ **everything to be retested** on GNOME 50.

`[L]` gnome-shell commit `0eb754a08` (13 Nov 2025): the unit becomes the template
`org.gnome.Shell@.service` with `ExecStart=gnome-shell --mode=%i`; `@user` is requested by gnome-session 50.
GNOME 50 is on Fedora 44, Ubuntu 26.04, Tumbleweed and Arch; Fedora 43 (49), Leap 16 (48) and Debian 13
(48) still have `@wayland`. `--headless` and `--no-x11` are still in mutter 50;
`org.gnome.Shell@headless.service` does **not** work (it would become `--mode=headless`, which does not exist).

⛔ **And our check would give a false green**: on GNOME 50 `systemctl --user show -p ExecStart
org.gnome.Shell@wayland.service` creates the "wayland" instance from the template, applies our drop-in to it and
returns our line — the check passes, while gnome-session starts `@user` without `--headless`.

Cure (`sessione.c`, `sessione.h`): choose the unit from what is installed (`@wayland` if present,
otherwise `@user`); the drop-in in `<unità>.d/`, **not** in the template's folder (it would also touch
GDM); the line `--headless --no-x11` without `--mode=%i`; reread the same chosen unit; the cleanup in
`provisiona.sh:245,510` extended to `@user` and `@`. Tested on `fedora44-gnome` and `ubuntu2604-gnome`.

### 5.2 Updating without closing the desktops: the measurement (T2, 29 Sep 2026) `[M]`

`PIANO.md` (Phase 15), `fasi/10` §7.5, `SPECIFICHE.md` and `DECISIONI.md` said that stopping the service
kills the sessions because of `KillMode=mixed` (measurement of 25 August). The verification on the code had already
refuted the cause; **the T2 measurement refutes the fact**:

- **ten tests with real Firefox** on the four boxes: 4 "stop" (`systemctl stop`, `KillMode=mixed`),
  4 "kill the parent" (`kill -KILL` to the parent only), 2 "kill the child" (SIGTERM to the child only). In
  each session three witnesses writing the time every second (the desktop's real terminal, a
  process in `session-cN.scope`, one in `user@.service`) and a 50 ms sentinel on births and deaths;
- **only parent, PAM helper and child die**, within 0.06-1.2 s (GNOME: Stopping 53.596, "the child is
  off" 54.307, unit Deactivated 54.311, then nothing else). logind does nothing
  (`KillUserProcesses=no`): no session closed;
- **the compositor, the session and the programs survive**: the three witnesses beat without gaps, in
  all ten tests, until the clear-out 3 and a half minutes later;
- **on reattach** the same compositor comes back, with the same pid, and the terminal where it was. On GNOME the
  resumed desktop is at first "ZERO MONITOR" (the virtual monitor belonged to the dead child): the new child
  mounts another and the windows reappear;
- **the cause**: the stage starts with `setsid --fork` and stays outside the unit; the child's death does not
  propagate and nobody closes the logind session. The fact of 25 August does not reproduce today (it is not known whether
  back then the desktop really died or whether the line "New session … empty" was read as a death: even
  a successful reattach opens a new logind session).

⇒ **The cure is the light one, 1-2 days; the "keeper" is not needed.** Still to do (T7):
1. the **new parent finds the live desktops** at start-up: today it restarts with "tenants=0" and nobody
   counts those desktops (neither the session cap, nor the budget, nor the abandonment clock);
2. **`loginctl terminate-user`** (`figlio.c:1577`) must not be issued when the user already has a live desktop.

✅ **Done in T7 (30 Sep 2026, 700cc1b)**: the new parent finds the live desktops at start-up (`src/ritrovo.c`:
logind session with the PAM service `remotix` and, in its scope, the stage leader born from `setsid --fork`), it
declares them in the log, counts them in the cap, the budget and the abandonment clock (which restarts from the start-up of the
new parent, declared); on reattach each one goes back into **its own** desktop; `terminate-user` is no longer issued on a
live desktop. D1 unchanged: the child dies with the parent and is remade on reattach. Measurements in §13.1.

⚠ Two things for the installer: (a) the child's logind session shows as "closing" 24 ms after
birth (`pam_end` without `pam_close_session`): with **`KillUserProcesses=yes`** the desktop could die —
`[?]` to be measured, and the preliminary check must read that setting; (b) each reattach leaves
one more logind session (with a dead leader), harmless for the user.

What the best ones teach (`[L]`): **NoMachine** throws everyone out at every update and writes it
in the guide; **xrdp** has sessions that survive but that nobody finds again (black screen). ⇒ REMOTIX already has
the difficult half (surviving); it lacks xrdp's half (**finding again**). QUIC connections do not
survive anyway: the honest promise remains *"updating costs whoever is connected a reattach of a few
seconds; the windows stay"*.

The bench: `banchi/17-t2/` (`t2-misura.py`, `t2box.py`, `lancia.sh`, `catena.sh`, `riassunto.sh`,
`tabella.sh`); the evidence on the server in `/media/REMOTIX/tmp/t2/<desktop>-<azione>/`.

---

## 6. The shape of the installer

### 6.0 The installation engine — the user's scheme, strengthened (29 Sep 2026)

**The user's proposal**, in eight phases: PREFLIGHT (know the system) · COMPATIBILITY (establish
what is supported) · PLANNING (build the plan) · CONSENT & SAFETY (present the plan and prepare
the protection) · ACQUISITION (packages, resources, dependencies) · INSTALLATION & CONFIGURATION
(apply the plan) · VERIFICATION & CERTIFICATION (prove that the product works) · COMMIT /
ROLLBACK (make the operation final or cancel it).

What it adds to a "good" installer: an **explicit plan presented before acting**, and
an operation that is **confirmed or cancelled as a whole** — also the first installation that fails
halfway, not only the update. The user asked to strengthen it at the weak points; the six
additions, all in the joints between one phase and the next:

1. **a phase zero, TRUST**: the engine runs commands as root on someone else's machine; before
   everything it makes sure that **the catalog** (the supported combinations) is the right one and that it
   understands it — after D11 (§6.6.10) it is the one the engine carries inside, delivered by the package
   manager (the `remotix-install` package) or by `install.sh` (the sha256);
2. **COMPATIBILITY has three outcomes, per desktop**: *certified* (tested in our VMs, §7) ·
   *conditional* (RPM Fusion, labwc, software fallback…) · *not supported*; and a machine can
   be fine for GNOME and not for XFCE;
3. **the plan is a document**: it is saved, read, approved, applied even on a hundred identical
   machines; each action carries **how it is done, how it is verified, how it is undone** — the undo is born
   with the step, it is not added later; and the plan carries the **fingerprint** of the machine on which it was
   made: if the machine changed between the plan and the execution, the plan is no longer valid;
4. **ACQUISITION is not harmless**: adding the RPM Fusion repository already changes the machine ⇒ it is
   an action of the plan like the others; and the rule: **nothing is installed until everything is downloaded
   and verified** — a network that drops halfway stops the operation *before* touching the machine;
5. **between installing and verifying there is the SWITCH-ON**: install with the service stopped, do the
   checks that do not need the service (7a), switch on, do the live ones (7b) — most
   errors are discovered when undoing costs little and nobody is connected;
6. **RESUME**: every step is written in the log **before** doing it; if the power goes during
   phase 6, on the next round the engine finds the operation open and offers to complete it or cancel it.
   And in the update, going back too respects the rule of not closing the desktops.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          REMOTIX INSTALL ENGINE                          │
├──────────────────────────────────────────────────────────────────────────┤
│ 0. TRUST                 the package's catalog, and the engine understands it│
│ 1. PREFLIGHT             know the system — read-only; the fingerprint    │
│ 2. COMPATIBILITY         per desktop: certified · conditional · no       │
│ 3. PLANNING              the plan as a document: do / verify / undo      │
│ 4. CONSENT & SAFETY      approval (by hand or from file), backups,       │
│                          log open                                        │
│ 5. ACQUISITION           everything downloaded and verified before touching│
│ 6. INSTALLATION & CONF.  with the service stopped, each step noted first │
│ 7. VERIFICATION & CERT.  7a without service → SWITCH-ON → 7b live        │
│ 8. COMMIT / ROLLBACK     confirm, or undo by walking back the log        │
│ ↺  RESUME                an interrupted operation is completed or undone │
└──────────────────────────────────────────────────────────────────────────┘
```

**One engine, three jobs.** The phases hold for installing, updating and uninstalling:

| phase | first installation | update | uninstallation |
|---|---|---|---|
| 0 TRUST | the engine's catalog (§6.6.10) | same | same |
| 1 PREFLIGHT | distribution, card (proprietary NVIDIA included), H.264, desktop, PAM, port, firewall, SELinux | in addition: the installed version and **the open sessions** | what is there, and the log of the changes made by REMOTIX |
| 2 COMPATIBILITY | the machine against the catalog (§3), desktop by desktop | N+1 on the same machine; N+1 accepts N's configuration | — |
| 3 PLANNING | actions: repositories, packages, groups, firewall | in addition: "whoever is connected reattaches in a few seconds" | what is removed, what stays (configuration, if not `purge`) |
| 4 CONSENT & SAFETY | yes/no for each choice (D5, D6); backup of what will be touched | backup of `/etc/remotix` and `/var/lib/remotix` | backup of the configuration |
| 5 ACQUISITION | repositories (noted) and packages downloaded and **verified** | N+1 | — |
| 6 INSTALLATION | the package manager installs, service stopped; the engine does the rest and notes it | the installation of N+1 **while N is still serving** | the package manager removes; the engine undoes its log |
| 7 VERIFICATION | 7a · switch-on · 7b | 7a · restart of the service without closing the desktops (§5.2) · 7b + sessions found again | the fingerprints back to how they were |
| 8 COMMIT / ROLLBACK | green ⇒ confirm; red ⇒ undo everything | red ⇒ back to N, **without closing the desktops** | — |

⭐ **A single, monolithic program** (`DECISIONI.md` §10.14): `remotix-install` is engine, CLI, TUI and GUI in one
executable; it talks to systemd, logind, firewalld and polkit from the inside (D-Bus); it launches only a closed list
of system programs (the package manager, `usermod`/`gpasswd`) with the full path and every call
in the log; the GUI runs as the user and relaunches the same executable with polkit's permissions.

**Three rules that hold the scheme up:**

1. ⛔ **Phases 5 and 6 are run by the distribution's package manager, not by the engine.** The engine
   directs (decides, asks, checks, undoes); REMOTIX's files are put in place by `apt`, `dnf`, `zypper`,
   `pacman`. If the engine copied them there would be **two truths** about what is installed, and system
   updates would not know it (Tailscale and Netdata do it this way, §6.5).
2. ⭐ **Going back is ours.** Only `dnf` has a real "undo" (`dnf history undo`), and
   openSUSE on btrfs has system snapshots (snapper); `apt` and `pacman` do not. ⇒ The engine walks
   the **log** backwards (the actions of the plan, each with its "how it is undone"); where the
   machine offers system snapshots, it uses them in addition. The honest promise: *"everything
   we did is undone"*.
3. **Consent even with nobody in front of the screen**: the approved plan is a file, and it is
   applied from cloud-init or Ansible on many machines; the engine refuses it if the fingerprint does not match.

**The certification (phase 7), with what the engine can prove by itself** — it has no browser:
- *7a, with the service stopped*: the libraries seen with a tenant's uid (no `not found`); the PAM
  stack loads and refuses a nonexistent user; the configuration reads; the card **really
  encodes** a test frame in H.264 (or the software fallback is declared); for each installed
  desktop, the stage **starts without a screen** and produces an image;
- *7b, with the service on*: active, port 7447 answers (TCP and UDP), the TLS certificate is the
  expected one, the firewall lets it through.

The rest (a real browser that gets in and works) is proved by the VMs of §7, before every release — and
it is what makes a combination "certified" in the catalog. The outcome is written in the **installation
certificate** (`/var/lib/remotix/certificato-<data>.txt`): version, machine, each test with
its outcome — the same that the welcome summarises.

### 6.1 Native packages, and an entry script

Discarded, with the why (`[L]`, the cases of RustDesk and Sunshine):
- **Flatpak, Snap, AppImage**: they do not install system services or PAM files, or cannot load
  the machine's VA-API drivers, Mesa and PAM;
- **a single static binary**: REMOTIX loads at run time the PAM modules, the card's driver,
  Mesa, PipeWire — they must be the machine's.

⇒ **Native packages** for each family (`.deb`, `.rpm`, `.pkg.tar.zst`), like Cockpit, Docker,
Tailscale, gnome-remote-desktop:

```
                     one source (git)
                           │
     ┌─────────────────────┼─────────────────────────┐
packaging/debian/   packaging/rpm/remotix.spec   packaging/arch/PKGBUILD
                    (%if fedora / rhel / suse,
                     like Cockpit)
     │                     │                         │
     ▼                     ▼                         ▼
 built INSIDE the root of each distribution (podman containers)
 ngtcp2 + nghttp3 static, pinned version · everything else from the distribution
                           │
                           ▼
 signed repositories:  apt (deb822 + keyring) · dnf / zypper · pacman
 channels: stable · candidate     old versions kept (to go back)
                           │
                           ▼
 install.sh — recognises the distribution, --verifica, adds the repository, installs
 (a convenient entry, like Tailscale; ⛔ never copies product files)
```

The native tools (`dpkg-shlibdeps`, `rpmbuild`, `makepkg`) **read the binary and compute by
themselves** the libraries it needs: it is the cure for the lesson of `LEZIONI.md` §2.5-bis (the packages
installed by hand that nobody declared). That is why no nFPM/fpm, which package ready-made files
with dependencies written by hand.

### 6.2 It is compiled for each distribution

The binary **is not copied** from one distribution to another: libavcodec (60, 61, 62), OpenSSL (3 or 4),
libei have different versions. One build container per target, like `src/Contenitore` today
for Debian. On rolling releases the package is tied to the exact versions of ffmpeg: better an
update **refused** by the package manager than one that breaks silently.

### 6.3 What goes into the binary and what does not

| | choice | why |
|---|---|---|
| **ngtcp2, nghttp3** | inside, **static**, pinned version | ngtcp2 ≥ **1.25.0** is needed (26 Jul 2026: required by the `NGTCP2_STREAM_CLOSE2_FLAG_*` flags of `trasporto.c:296-299`; without them, 1.23) and almost no distribution has it; they are small. ⚠ **Security updates become ours** — **decision D2** |
| OpenSSL | from the distribution | it is the security library best looked after by the distributions |
| libavcodec, drivers, Mesa | ⛔ from the distribution, **never** inside | that is where the patented codecs live (§4.2) |
| PAM, PipeWire, libei, glib, Wayland | from the distribution | they must match the machine |

⇒ `ld.so.conf.d` **disappears**: today `provisiona.sh:394` puts our ngtcp2 in front of the system's,
which curl and the package manager use too. With the static ones no library remains
outside the system paths.

### 6.4 What the package installs

| what | where |
|---|---|
| server and child | `/usr/libexec/remotix/` |
| the administrator's command | `/usr/bin/remotix` — `verifica`, `stato`, `certificato`, `configurazione` |
| unit | `/usr/lib/systemd/system/remotix.service` (root; certificate generated at start-up if missing) |
| defaults / the administrator's choices | `/usr/share/remotix/remotix.conf` · `/etc/remotix/remotix.conf.d/` (empty) |
| PAM | one file per family (§4.3) |
| KWin's capture permission | `/usr/share/applications/org.kde.remotix.desktop` (today the program writes it, §4.4) |
| the three belts of `DECISIONI.md` §4.7 (no shutdown, suspend, keys) | `/usr/share/polkit-1/rules.d/`, `/usr/lib/systemd/{logind,sleep}.conf.d/` — ⚠ they change the machine: **decision D4** |
| firewall | `/usr/lib/firewalld/services/remotix.xml`, `/etc/ufw/applications.d/remotix` — **defined**, opened only with consent (D6) |
| folders | `/var/lib/remotix` (0700), `/run/remotix` via `tmpfiles.d` |
| SELinux | `remotix-selinux` subpackage, **only if** the tests say it is needed (first it is tested without) |
| ⛔ **never** | test users, the benches' `sudoers.d`, `gpu-udev.sh`, `riavvia-*.sh`, `ld.so.conf.d` |

⭐ **The installer is the only way** (`DECISIONI.md` §10.12): the package carries the **inert** pieces — no
service on, no groups, no firewall, the belts off in `/usr/share/remotix/`; the engine
mounts them with consent and records them; there are only two ways — the installer or the source code by hand, at one's own risk — and REMOTIX has neither locks nor options for an intermediate way: `remotix stato` only says whether the installation is certified by the installer;
a package update calls the engine back. What follows must be read this way: it is done by **the engine**, not
by the package scripts.

After the installation: people are enrolled in the card's groups (`DECISIONI.md` §7.21) **and
it is noted** (who was already there, who was put there by REMOTIX), or the uninstallation does not know what to remove.

### 6.5 The qualities of excellence

Taken from those who do them best (`[L]`): Cockpit for PAM, SELinux and certificate; Tailscale for the entry
script; Netdata for `--dry-run` and installation without network; GitLab for the backup before
updating; Syncthing for the "candidate" channel; OpenSSH for the configuration tested before
restarting. ⚠ And **not** to be copied: Chrome (a cron that rewrites the repository), Docker (the
uninstallation that leaves the machine different, and says so), Netdata's telemetry (a server that does
login does not phone home).

1. **The preliminary check**, before touching anything: `install.sh --verifica` and, once installation
   is done, `remotix verifica`. It looks at distribution and version, card and node, **H.264 really
   available** (VA-API profile and `h264_vaapi` in libavcodec), desktops present and versions, PAM,
   port 7447 free, firewall, SELinux, OpenSSL. Each problem with a message in plain Italian
   **and the command that solves it**. ⚠ It is not in the package scripts: a package that refuses to
   install because the card is missing breaks images and cloud-init. The package warns; the
   check decides when it is called.
2. **Idempotence**: running again changes nothing.
3. **Uninstallation** that puts the machine back as it was; `remove` keeps the configuration, `purge`
   removes everything; it removes from the groups **only** those REMOTIX had put there.
4. **Update** without closing the desktops (§5.2), with the configuration **tested before**
   asking for the service restart.
5. **Going back to the previous version**: the repository keeps the old ones; before updating,
   `/etc/remotix` and `/var/lib/remotix` are backed up; version N−1 reads N's configuration.
6. **Signatures**: ONE key (§6.6.10), for the REMOTIX repository only (`Signed-By`, never `trusted.gpg.d`),
   in the `remotix-archive-keyring` package; where it is kept and how it is changed: with D10.
7. **Configuration**: defaults in `/usr`, the administrator's choices in `/etc`, which win;
   `remotix configurazione --mostra` says which file each entry comes from.
8. **Welcome** at the end: the addresses to open, the certificate's fingerprint, who can get in
   (root excluded), what REMOTIX changed on the machine, the state of H.264.
9. **Installation log** and log of the changes to the machine
   (`/var/lib/remotix/modifiche.log`).
10. **No questions** for whoever manages many machines (cloud-init, Ansible) and **no network**.
11. **Reproducible build** (`SOURCE_DATE_EPOCH`) and an **SBOM** that names ngtcp2 and nghttp3 with the
    exact version.

### 6.5-bis What the installer asks of REMOTIX — closed list (30 Sep 2026)

*The user's concern: «su T5 andrà fatto un ragionamento, perché rischiamo di dover introdurre
funzionalità in REMOTIX non previste». ⇒ What the installer asks of the product is **only** in this
list; a new request goes through the user before entering.*

| request to REMOTIX | why | status |
|---|---|---|
| find the live desktops again after a service restart | update without closing the desktops (§5.2, T7) | decided (T2) |
| an encoding test: one frame in H.264, and say whether it succeeds | the certification, phase 7 (§6.0) | proposed on 30 Sep |
| `remotix stato`: installation certified or not, active conditions | support (§10.12) | decided |
| no longer write KDE's file by itself (`kwin.c:48`) | the package owns its files | correction |
| note whom it enrols in the groups at the first connection (`figlio.c:~1525`) | the uninstallation knows whom to remove | correction |

⛔ They are **not** in REMOTIX, and the engine does them: groups, belts, firewall, desktops, archives, packages, and at
**uninstallation** the closing of the open desktops — the engine finds them through logind (sessions with the PAM service
`remotix`) and has logind close them (see below).

**The uninstallation** (the user's word, 30 Sep: *«è un'operazione dell'admin del server: l'admin avverte
gli utenti nelle modalità classiche (email, WhatsApp…); poi, quando avvia la disinstallazione, l'installer
chiude le sessioni REMOTIX degli utenti e i loro processi e avvia la pulizia del sistema»*):
1. **first**, the administrator warns people with his own means — REMOTIX does not have and will not have a messaging system
   for this;
2. **no extra question**: if there are still people connected, their REMOTIX sessions are closed and that is that
   — they had been warned (the user's word, 30 Sep). The uninstallation plan, which is confirmed only once
   like every plan, carries only the line "I close the REMOTIX sessions still open (N)";
3. the engine closes **the REMOTIX sessions** and all the programs born inside them (logind `TerminateSession`
   on the session, which takes away its process group) — ⚠ **not** all the user's processes: the same
   person may have a session in front of the monitor or a job over ssh, and those are not touched;
4. then the **cleanup** of the system, walking back the log (§6.6.4).

### 6.6 The engine specification — states, log, actions, trust (29 Sep 2026)

*Written after a review of the draft brought by the user: the eight-phase architecture holds; what
was missing was making its promises **precise enough to be tested automatically**. Here is fixed
what changes the engine's data and behaviour — changing it later would mean rewriting it. The
details that depend on things that do not exist today (the public repository, the custody of the key)
have their model here and their decision at the milestone.*

#### 6.6.1 The contract: the engine's objects

The engine produces and consumes **seven objects**, JSON files with a format version
(`"formato": "remotix-install/1"`). They are its own: whoever uses the engine reads them, nobody invents them.

| object | who produces it | what it contains |
|---|---|---|
| **Machine profile** | PREFLIGHT | every fact detected, each with the state RILEVATO / VERIFICATO / SCONOSCIUTO (§6.6.7) |
| **Compatibility report** | COMPATIBILITY | per desktop: level and conditions (§6.6.8), with the catalog version used |
| **Plan** | PLANNING | the actions (§6.6.4) with their intents and constraints; the fingerprint (§6.6.5); the choices to approve |
| **Resolved set** | ACQUISITION | the exact artefacts the plan becomes (§6.6.6) |
| **Execution log** | INSTALLATION, and going back | the write-ahead journal (§6.6.3) |
| **Verification report** | VERIFICATION | each check with outcome PASS / FAIL / UNKNOWN / N.A. |
| **Installation certificate** | COMMIT | the final state (§6.6.2), the conditions, the references to engine, catalog, plan, product (§6.6.11) |

> ⛔ **10 Oct 2026: the GUI has been removed** (`DECISIONI.md` §10.31, decided on 5 Oct): the interfaces are **two**, the
> command line and the TUI. The table below remains as the history of the design of 29 Sep.

**The interfaces: three, and TUI and GUI are an indispensable requirement** (the user's word, 29 Sep
2026):

| interface | for whom | how it runs |
|---|---|---|
| **CLI** (`remotix-install`, and `install.sh` which downloads it) | whoever administers from a terminal, and the installation without questions (§6.6.12) | as root |
| **TUI** (full screen in the terminal) | whoever administers via ssh or from the console, even on a machine with nobody in front | as root, in the terminal |
| **GUI** (a window in the desktop) | whoever administers from the machine's desktop | ⛔ **as the user, not as root** (under Wayland a graphical client as root is wrong and often refused): it asks the engine for permissions with **polkit**, like the distributions' graphical installers |

⛔ **The interfaces contain no installation logic.** They show the engine's objects (profile,
report, plan, progress from the log, certificate) and collect consent; they never choose
packages, repositories, PAM or rollbacks. There is only one engine, and the three interfaces talk to it
in the same way: the engine writes the objects and the events (JSON, one line per event) and reads the
consent as an approved plan. ⇒ The same operation gives the same plan, the same log and the
same certificate whatever interface drives it (R36). The tool for TUI and GUI is **decision D12**.

#### 6.6.2 The states of the operation

An operation (installation, update, uninstallation) has an identifier and **one state**,
written in `/var/lib/remotix/operazioni/<id>/stato`:

```
NUOVA → FIDATA → ESAMINATA → VALUTATA → PIANIFICATA → APPROVATA → ACQUISITA
      → IN_ESECUZIONE → APPLICATA → IN_VERIFICA → VERIFICATA → CONFERMATA
                ↓ interruption          ↓ red                 ↓ red
            INTERROTTA ──resume──→ IN_ESECUZIONE         IN_ANNULLAMENTO → ANNULLATA
                                                              ↓ an action cannot be undone
                                                          ANNULLATA_IN_PARTE
from phases 0-5, without having touched anything:  BLOCCATA (intervention needed) · RIFIUTATA (no consent)
```

| final state | means | the certificate says |
|---|---|---|
| **CONFERMATA** | installed and verified, all required checks PASS | the platform: CERTIFICATA or COMPATIBILE |
| **CONFERMATA_A_CONDIZIONI** | installed and verified, with active conditions (§6.6.8) | the conditions, one by one |
| **ANNULLATA** | everything REMOTIX did has been undone | what remains that is INDIRETTO (§6.6.4) |
| **ANNULLATA_IN_PARTE** | going back could not undo everything | the exact list of what remains, and why |
| **BLOCCATA / RIFIUTATA** | nothing has been touched | the reason code (§6.6.9) |

Rules: ⛔ **no state is skipped**; the valid transitions are only those drawn; the engine
refuses to start if it finds an operation in a non-final state and **not** its own (it must first be resumed or
cancelled). ⭐ **installed ≠ certified**: CONFERMATA_A_CONDIZIONI on a COMPATIBILE platform is
a successful installation, but not a certified combination.

#### 6.6.3 The log: write-ahead and resume

Every action of the plan runs in four beats, and the log (`registro.jsonl`, one line per
event, `fsync` of the file and the folder before going on) notes them:

```
INTENZIONE(azione, stato_prima)  → [effect]  → FATTA(azione, stato_dopo)
                                            ↘ FALLITA(azione, codice)
```

Each action has three functions (§6.6.4): **do**, **check** (says whether the effect is there, without changing
anything), **undo**. The resume after an interruption looks at the last line of each action:

| in the log | what happened | what the resume does |
|---|---|---|
| nothing | not started | does it |
| INTENZIONE without FATTA | started; perhaps finished, perhaps not, perhaps halfway | calls **check**: effect complete ⇒ notes FATTA; absent ⇒ redoes it; **halfway** ⇒ undoes what is there and redoes it |
| FATTA | finished and noted | moves on |
| FATTA but the effect is no longer there (consistency check) | someone undid it afterwards | ⛔ stops: BLOCCATA, "the machine changed during the operation" |

⇒ That is why every action must be **idempotent** (redoing it does not double the effect) and its
**check** must be able to tell complete / absent / halfway. A configuration file is always written
to a temporary name and then renamed (never halfway); a unit is enabled and checked with
`systemctl is-enabled`.

⚠ **The package manager's transaction is a special action**: an interruption halfway leaves the
manager in its intermediate state. The resume uses **the manager's own remedy** before everything else:
`dpkg --configure -a` (apt), repeating the transaction with `dnf` (and `rpm --verify`), removing
the lock file and `pacman -Dk` (pacman), `zypper verify` (zypper); then the action's **check**
looks at the packages one by one.

#### 6.6.4 The actions: how far they can be undone, and whose the change is

Each action of the plan declares **how reversible it is**:

| class | means | examples |
|---|---|---|
| **ESATTA** | back to the state before, byte for byte | a file of ours in `/etc`; an enabled unit; a user added to a group they were not in; a firewall rule added |
| **AL_MEGLIO** | goes back, but not necessarily to the same state | a dependency package removed (if nobody else wants it); a repository removed (but the packages taken from there remain, and it is said) |
| **CON_FOTOGRAFIA** | reversible only with a system snapshot (snapper, btrfs, LVM) | a dependency **upgraded** by the package manager |
| **IRREVERSIBILE** | cannot be undone | a format conversion the old version does not read |

⛔ An IRREVERSIBILE action has **a line of its own in the consent**, and the plan does not contain it if there is
an alternative. The certificate says which CON_FOTOGRAFIA actions were done without a snapshot.

And every **change** to the machine has an **origin**, which decides how far going back is
authorised:

| origin | example | going back |
|---|---|---|
| **DIRETTA** | REMOTIX's PAM file; a user put in `render` by us | undoes it |
| **INDIRETTA** | libX upgraded from 1.0 to 1.1 because REMOTIX asks for it | ⛔ does not touch it (a library others may already be using is not downgraded); it **declares** it |
| **PREESISTENTE** | the user was already in `video` before | ⛔ never touches it |
| **CONCORRENTE** | the administrator changes the same thing during the operation | ⛔ does not touch it; the operation stops (§6.6.3, last line) |

⇒ **The normative promise** (R6, R28): *"everything REMOTIX did directly is undone; what
happened indirectly is declared; what was there before is not touched"*. The dependencies
**installed** for us are removed if nobody else wants them (the managers' "automatic" mark:
`apt-mark auto`, `dnf` *userinstalled*, `pacman --asdeps`); those **upgraded** stay upgraded.

For each change that touches a state that already existed (the three belts, the groups, the firewall) the log
notes **the state before, the change, the consent, the state after, how it is undone** (R33, R34).

#### 6.6.5 The machine's fingerprint

The plan is valid only for the machine on which it was made. The fingerprint has two parts:

| **binding** — if it changes, the plan is no longer valid | **noted** — recorded, does not invalidate |
|---|---|
| distribution, version, architecture | machine name, addresses |
| the installed desktops and their versions | packages the plan does not touch and does not depend on |
| the packages the plan touches or depends on, with the version | load, free memory |
| the configured repositories (list and keys) | |
| card, driver, detected H.264 capability | |
| the files the plan writes or reads (PAM, logind, polkit, firewall), with their sha256 fingerprint | |
| the `video`/`render` groups and their members | |
| SELinux and its state, the firewall and its state | |
| version of the engine and of the catalog | |

The binding fingerprint is a sha256 over the canonical text of these elements (sorted, one element per
line); the plan contains it, APPLY recomputes it and compares it. R31 tests each element.

#### 6.6.6 From the plan to the artefacts: PLAN → RESOLUTION → ARTIFACTS → VERIFY → APPLY

The plan contains **intents with constraints** ("`remotix` ≥ 1.4, from the REMOTIX repository; `labwc` from the
distribution's repository"), not files. ACQUISITION **resolves** them into the **resolved set**: for each
package name, exact version, architecture, repository, **digest** (sha256), verified signature. Then:
- APPLY installs **exactly** that set, from the already-verified local cache (`apt install
  nome=versione` on the already-downloaded `.deb` files, `dnf install` on the files, `pacman -U` on the files) — never "the latest
  version" taken at the moment;
- if the resolution goes outside the plan's constraints (the repository changed between the plan and the execution), it
  goes back to PLANNING with a **new consent**;
- the resolved set enters the log: it says, afterwards, what was installed bit by bit.

#### 6.6.7 Facts and checks: detected is not verified, and UNKNOWN is not PASS

Each fact of the profile has one of three states:

| state | example |
|---|---|
| **RILEVATO** | "PipeWire is installed", "there is an AMD card", "the PAM file exists", "firewalld is there" |
| **VERIFICATO** | "PipeWire answers", "the card encoded an H.264 frame", "the PAM stack refuses a nonexistent user", "the port is reachable" |
| **SCONOSCIUTO** | the tool is not there, the permission is missing, the time ran out |

And each check of the certification has one of four outcomes: **PASS**, **FAIL**, **UNKNOWN**,
**N.A.** (not applicable: the XFCE check on a machine without XFCE).

⛔ **The general rule: UNKNOWN is never PASS.** A check that cannot prove its
property gives UNKNOWN; a **required** check in UNKNOWN takes the operation to CONFERMATA_A_CONDIZIONI
(if the property has a declared fallback) or to IN_ANNULLAMENTO (if not). ⛔ And a fact that is only
RILEVATO is never enough for a PASS. It is the lesson of the false green of GNOME 50 (§5.1) and of the counters
that do not see the image: a green on incomplete information is worse than a red (R32).

#### 6.6.8 Compatibility: levels and conditions

The level, **per desktop**:

| level | means |
|---|---|
| **CERTIFICATA** | the combination distribution × version × desktop is in the matrix (§3) and the catalog records a whole green round on it |
| **COMPATIBILE** | no known reason for refusal, but none of our VMs has tested it (Rocky 10, Manjaro, Mint 23…) |
| **NON_SUPPORTATA** | a known reason, with its code (§6.6.9) |

And, on top of CERTIFICATA or COMPATIBILE, zero or more **conditions**, each with its code:

| code | condition | example |
|---|---|---|
| `C-DEPOSITO` | a third-party repository is needed | RPM Fusion, Packman |
| `C-COMPONENTE` | the installer adds a piece the default desktop does not have | labwc for XFCE and LXQt; `gnome-session` on Ubuntu |
| `C-RIPIEGO` | a function falls back | H.264 in software (no encoding on the card) |
| `C-LIMITE` | a function is missing | no audio, a screen size that cannot be reached |
| `C-HARDWARE` | a requirement of the card | NVIDIA with the proprietary driver |
| `C-AMMINISTRATORE` | a manual step is needed | opening the port on the router |
| `C-DESKTOP` | the desktop is not there (or not supported) and the installer adds it from the distribution's archives | Ubuntu Server, a cloud image, a machine with only Cinnamon |

⭐ The conditions **do not disappear after the plan**: they are in the certificate, in `remotix verifica` and in
`remotix stato` as long as they hold (R35); if one is resolved (the administrator adds RPM Fusion later),
`remotix verifica` sees it and says so.

The **catalog** (the combinations and their rules) has a version, a sequence and the minimum version
of the engine that understands it; it travels INSIDE the engine, and the engine in the `remotix-install` package
(§6.6.10). The certificate records which catalog decided the state of that installation.

#### 6.6.9 Outcomes and codes

Every message of the engine has:
- a **severity**: `INFO` · `AVVISO` · `BLOCCANTE`;
- a **nature**: `SERVE_AZIONE` (by the administrator) · `RIPROVABILE` (e.g. network) · `RECUPERABILE` (the
  resume fixes it) · `SERVE_ANNULLAMENTO` · `FATALE`;
- a **stable code** `RX-<AREA>-<NNN>` (`RX-PAM-001` "the distribution's access stack cannot be
  found", `RX-H264-003` "the card does not encode H.264: on Fedora RPM Fusion is needed"), with the text in
  plain Italian, the command that remedies it, and the manual page.

The same code appears in the command line, in the log, in the certificate, in the manual and in every
future interface. ⛔ A code is never reused for another meaning.

#### 6.6.10 Trust: a single key (`DECISIONI.md` §10.21, 30 Sep 2026)

| what | who guarantees it | how |
|---|---|---|
| `install.sh`, downloaded by hand | the administrator | the **sha256** published on the REMOTIX site, over HTTPS |
| the engine downloaded by `install.sh` (`remotix-install`, `-gui`) | `install.sh` | the **sha256** written inside `install.sh` by the release command (a development copy: the one published next to the engine, **only over HTTPS**; http only with `--insicuro`, for the tests) — `RX-TRUST-017` if it does not match |
| the packages (`remotix`, `remotix-install`, `remotix-selinux`, `remotix-archive-keyring`) and the archive metadata | the **package manager** | REMOTIX's **single key** (GPG), which signs packages and archive: apt (`Signed-By`, `Valid-Until`), dnf (`gpgcheck`, `repo_gpgcheck`), zypper, pacman — R17 |
| the **catalog** | whoever delivered the engine | it is INSIDE the engine (`installatore/catalogo/catalogo.json`, embedded), and the engine inside the `remotix-install` package: it is updated **like every package** (`apt upgrade`…, §10.23) |

Phase 0 TRUST, therefore: the catalog is the one of the running engine — from the package (`/usr/bin/remotix-install`:
"guaranteed by the package manager") or downloaded by `install.sh` ("verified with the sha256") — or one
given by hand with `--catalogo FILE` (it is the administrator's, and the certificate says so). One check remains:
that it can be read (`RX-TRUST-004`) and that this engine understands it (`RX-TRUST-003`); no expiry, no
catalog stored on the machine. ⚠ Honestly: the sha256 of `install.sh` is worth as much as the site that
publishes it (HTTPS); from there down the chain is closed. **Retired** (not reused): `RX-TRUST-002`, `006`…`016`
(the old "chain A": ed25519 root, subkeys, revocations, signatures of the engine and of the catalog, `fiducia`).
Still to decide, with **D10**, where the key and its backup copy are kept.

#### 6.6.11 The certificate is verified afterwards

The certificate is a JSON (plus its readable version) with: identifier of the operation, final
state (§6.6.2), product version, **version and digest of the engine**, **version and digest of the
catalog**, **digest of the plan** and of the resolved set, the fingerprint, each check with its outcome, the
conditions. ⚠ Honestly: on the machine itself it cannot be signed in a way that holds against root.
"Verifiable" means: `remotix verifica --certificato <file>` recomputes the digests from the objects
kept in `/var/lib/remotix/operazioni/<id>/` and **redoes the checks**, saying what is still
as it was and what has changed.

#### 6.6.12 No questions does not mean no consent; and what "no network" means

- **No questions**: the consent is **given beforehand**, as an **approved plan** (a file, made on a
  reference machine with the same binding fingerprint) or an answers file that the engine
  turns into a plan and records. ⛔ Never a switch that skips CONSENT & SAFETY; every action, even
  those of D5 and D6 (repositories, firewall), is in the plan, in the consent and in the log.
- **No network** (R22): an **offline bundle**, prepared on a connected machine for a given
  fingerprint, which contains the engine (with the catalog inside) and its sha256, the resolved set (all
  the artefacts, with digests and signatures), and the signed metadata of the repositories. The engine uses it as a local repository; the
  signatures are verified as online.

⭐ **How it is made (T9, 30 Sep 2026)** — the code in `installatore/motore/risposte.go` and `fuorilinea.go`:
- **the answers file** (`remotix-risposte/1`), plain text, one entry per line: `formato`, `lingua`
  (it · en; wins over the system language, DECISIONI §10.15), `porta`, `canale`, `utenti` (tutti · names),
  `desktop` (only if missing: if the file is silent the reference one applies, §10), and the consents
  `consenso.firewall` (D6, only with firewalld on) — ⭐ the belts **are not asked** (D4 was already decided:
  `DECISIONI.md` §4.7; a `consenso.cinture` from an old file is noted among the "superflue" and does not count, T9),
  `consenso.deposito.rpmfusion|packman|epel` (D5, only where needed), each one "si" or "no" (`consenso.aggiornamenti`
  is retired with D14, §10.23: in an old file it is "superflua"). The engine knows which consents are needed **on that machine**: if one is missing the plan
  is made (to show it) with `mancanti` written inside, and the operation is **BLOCCATA** with `RX-RISPOSTE-001`
  before touching anything; an unknown entry (a typo in a consent) is `RX-RISPOSTE-002`,
  a wrong value `RX-RISPOSTE-003`. The plan carries the file (path, sha256, entries, defaulted,
  superfluous) and the approval "no questions: answers file … (sha256 …)": all in the log.
  `remotix-install installa --risposte FILE` does plan, recording and application; `piano --installa
  --risposte FILE` does only the plan, which is carried **approved** to other machines with the same fingerprint
  (`applica FILE-PIANO`, refused with `RX-PIANO-001` if the fingerprint does not match, R31);
- **the offline bundle**: `remotix-install prepara-fuori-linea --archivio URL --risposte FILE
  --uscita DIR` on a **connected machine identical** to the one without network (same binding fingerprint and
  **same installed packages**: the resolved set depends on what is already there). Inside: the manifest
  `fuori-linea.json` (the fingerprint, the list of packages, the resolved set, each file with its sha256),
  `archivio/` (the engine with its sha256 — the catalog is inside —, the public key, the REMOTIX repository
  with its signed metadata and only the packages that are needed), `distro/apt/<n>/` (apt: a **partial** copy
  of each repository of the distribution, with its InRelease signed by the distribution, the indexes it
  certifies and in the pool only the `.deb` files that are missing), `distro/rpm/<passo>/` (dnf: the missing `.rpm` files,
  signed one by one), `terzi/rpmfusion/` (on Fedora, with the D5 consent: without RPM Fusion REMOTIX does not
  encode, §11.1 C). On the machine without network: `installa --fuori-linea DIR --risposte FILE`; the archive
  becomes `file://DIR/archivio`; each file is verified against the manifest (`RX-FUORI-001`), the machine against the
  bundle (`RX-FUORI-002`); apt reads **only** the bundle's repositories (temporary configuration,
  `target=Packages`) and verifies InRelease → indexes → `.deb` as online; dnf installs the files with
  `localpkg_gpgcheck=1` and no repository. Limits: zypper and pacman not yet (`RX-FUORI-004`),
  Packman and EPEL do not enter (`RX-FUORI-005`). ⚠ The bundle must be put in a folder that the `_apt`
  user reads (not `/root`): the local REMOTIX repository stays configured afterwards, for the updates
  brought with a new bundle, and from `/root` `apt-get update` does not read it;
- **the entry script** `installatore/install.sh`: all in functions, `main "$@"` on the last line;
  it recognises the family (`/etc/os-release`), downloads the static engine from the archive, verifies its
  **sha256** (§6.6.10: written in the script by the release command) and hands over to it (`installa`,
  `verifica`, `piano`); `--verifica`
  (also as a user), `--dry-run` (as root: the plan reads the files it would touch), `--risposte`,
  `--lingua`; bilingual (⛔ since 10 Oct 2026 English only, without `--lingua`: `DECISIONI.md` §10.35); the engine sits in a temporary folder; ⛔ no product file copied
  (`TestScript` checks it too). `pubblica.sh script` puts it in the archive with the sha256s of the two
  engines inside, and `install.sh.sha256` next to it (the one to publish on the site);
- **cloud-init** (R21): `banchi/17-t9/cloud-init-r21.yaml`, a user-data that writes the answers file and
  launches `curl …/install.sh | sh -s -- --archivio … --risposte …`.

#### 6.6.13 The server certificate (R16)

`/var/lib/remotix/certificati/0-generato.pem` is generated at first start-up if missing. The administrator
puts his own in `/etc/remotix/certificati.d/` (certificate + key, same base name); **the one
whose name comes last in alphabetical order wins**, and the administrator's always win over the
generated one (Cockpit's rule). `remotix certificato --mostra` says which is in use and where it comes from.

#### 6.6.14 The interfaces: TUI and GUI (T9, 30 Sep 2026)

> ⛔ **10 Oct 2026: the GUI has been removed** (`DECISIONI.md` §10.31). Removed `interfaccia/gui/`, `protocollo.go`,
> `permessi.go` (the root part started by systemd and polkit), `Contenitore.gui`, `gui_si.go`/`gui_no.go`, the
> commands `gui` and `motore-interfaccia`, `install.sh --finestra`, `remotix-install-gui` from the release command and
> from the archive, the OFL fonts, Gio from `go.mod` and from `vendor/`. **A single build** remains, static:
> engine, CLI and TUI. RX-UI-001…004 retired (they remain in the codes, marked); RX-UI-005 and 006 in force. What
> follows is the design of 30 Sep, as history; for the TUI and the Session it still holds.

⭐ **Two builds of the same source** (the constraint of `DECISIONI.md` §10.19, verified): Gio v0.10.3 on
Linux binds to the graphics libraries **at link time** (pkg-config: wayland-client, wayland-cursor,
wayland-egl, egl, x11, xkbcommon, xkbcommon-x11, x11-xcb, xcursor, xfixes; only Vulkan on demand): a
binary with the window on a machine without those libraries does not even reach `main`. Loading them "only
when needed" would mean rewriting Gio's calls. ⇒ `remotix-install` (static, without cgo: engine,
CLI, TUI — the package's one, goes everywhere) and `remotix-install-gui` (`gui` tag, cgo,
built on **Debian 12's glibc** in `installatore/Contenitore.gui`, so that it runs on Alma 10 too): **the
same commands plus `gui`**. The static one answers `gui` with **RX-UI-001**. `install.sh --finestra` downloads the
second (with its sha256), `--tui` the first. On each machine **one file** remains, a program that starts
itself as root; in the archive there are two binaries, each with its sha256.

**The design** (`installatore/interfaccia/`, no installation logic, §6.6.1):
- `motore/interfaccia.go` — what the engine adds for the interfaces: `DomandeDaFare` (the port; the
  firewall open · closed · none · other; the third-party archives that are needed, and for what; the desktop, if
  missing; who does not have the card), `VociDiserie` (the default values of §10), `PianoDaScelte` (the entries of the answers
  file → `OpzioniDaRisposte` → `PianoInstallazione`: **the same rules** as no-questions, but the plan
  carries neither file nor approval: it is given by whoever looks at the plan, with a single "confirm"), `Motore.Fermata` (the
  "Cancel and put back as it was" button: between one step and the next, then everything is undone, **RX-AZIONE-006**);
- `interfaccia/sessione.go` — the **Session**, the engine as root: `Controlla` (phases 0-2 like `verifica`),
  `Piano`, `Applica` (approval "by hand, in the window/in the TUI", the engine's JSON events passed
  line by line); `protocollo.go` — the same session **in another process**, line-based JSON over two pipes;
- `interfaccia/permessi.go` — ⭐ **the window's root part is started by systemd**, not pkexec:
  `StartTransientUnit` on the system D-Bus with the ALLOW_INTERACTIVE_AUTHORIZATION flag (polkit asks for the
  password in the graphical session's agent), the same executable with `motore-interfaccia --lingua …`,
  the unit's stdin and stdout = two pipes of the window (the descriptors travel on the bus, like `systemd-run --pipe`).
  Why: `[M]` debian13-kde **does not have pkexec** ("exec: pkexec: executable file not found": in Debian 13 it is a
  separate package, GNOME pulls it in, KDE does not); and it is the rule of §10.14 (with systemd and polkit from the inside, D-Bus).
  ⚠ godbus's `Object.Call` drops the interactive flag: the message is written by hand (`[M]` without it:
  `InteractiveAuthorizationRequired`). ⚠ The window must be launched **from the graphical session** (a desktop
  terminal, the menu): from ssh polkit does not find the agent;
- `interfaccia/vista.go`, `testi.go` — the objects in **everyday words**, it/en: the lines of the check (no
  driver or bus: "Virtual graphics card", the names in the details), the questions, the plan's steps **grouped**
  (three belts = one line; a person's groups = one line) with the tag of the engine's true
  reversibility (`installa-pacchetti` is AL_MEGLIO ⇒ "Partly undone"), the progress from the events, the welcome
  (address, the port to forward on the router TCP and UDP — D6 —, the certificate's tests, the conditions in
  everyday words); `BloccoNelPiano`: the "no" to the encoding archive stops at once (D5, **RX-H264-006**);
- `interfaccia/gui/` (`gui` tag) — Gio: the five screens, "no desktop", "blocked" and the endings
  (stopped, cancelled); the logo's colours, **Sora SemiBold, IBM Plex Sans, IBM Plex Mono embedded** (OFL 1.1,
  licences alongside; Sora 600 is the instance of Google Fonts' variable Sora, Sora has no reserved names), logo
  cropped from `grafica/logo/remotix-logo.png`; `gui --anteprima DIR --dati DIR` draws the screens off
  screen (EGL without a surface) as PNG; R37: as root the window answers **RX-UI-003**;
- `interfaccia/tui/` — Bubble Tea v1.3.10 + lipgloss: the same views in text, as root (`sudo remotix-install
  tui`), for ssh and console; arrows, space, enter, esc; "a" stops, "r" the log, "d" the details.

**New codes**: RX-UI-001…006 (no window · no graphical session · window as root · permissions denied ·
the root part was interrupted · TUI without a terminal or without root), RX-AZIONE-006 (stopped by whoever installs),
RX-H264-006 (D5: without the encoding archive it does not install). ⚠ The `vendor/` grows to 37 MB (Gio,
go-text, x/text, Bubble Tea): the build stays **without network**.


#### 6.6.15 10 Oct 2026: the names in English (`DECISIONI.md` §10.35)

Everything the administrator types or reads from the engine is in English. The names in the Go code and the comments stay
Italian. The object format moves to **`remotix-install/2`**, the answers file's to
**`remotix-answers/2`** (before `remotix-risposte/1`): no compatibility with the old one, because there are no
real installations. What follows in the earlier paragraphs remains as history, with the names of the time.

| what | before | now |
|---|---|---|
| commands | `verifica` · `piano` · `approva` · `applica` · `riprendi` · `annulla` · `stato` · `aggiornato` · `disinstalla` · `certifica` · `catalogo` · `installa` · `prepara-fuori-linea` · `versione` · `aiuto` (`aggiorna`/`ritorna` referred to the manager) | `check` · `plan` · `approve` · `apply` · `resume` · `rollback` · `status` · `post-upgrade` · `uninstall` · `certify` · `catalog` · `install` · `prepare-offline` · `version` · `help` (`upgrade`/`downgrade`) |
| engine options | `--operazioni` · `--catalogo` · `--archivio` · `--canale stabile\|candidato` · `--porta` · `--risposte` · `--fuori-linea` · `--uscita` · `--eventi` · `--utente` · `--apri-firewall` · `--deposito` · `--pacchetto` · `--pacchetti` · `--piano` · `--installa` · `--approva` · `--tabella` | `--state-dir` · `--catalog` · `--archive` · `--channel stable\|candidate` · `--port` · `--answers` · `--offline` · `--output` · `--events` · `--users` · `--open-firewall` · `--extra-repos` · `--package` · `--packages` · `--plan` · `--install` · `--approve` · `--table` |
| ⚠ two different things | `--archivio` (REMOTIX's signed archive) and `--deposito` (the third-party archives: epel, rpmfusion, packman) | `--archive` and `--extra-repos`; in the facts and in the steps the third-party archives are `repo` |
| `install.sh` | `--archivio` · `--canale` · `--verifica` · `--risposte` · `--insicuro` · `REMOTIX_ARCHIVIO` | `--archive` · `--channel` · `--check` · `--answers` · `--insecure` · `REMOTIX_ARCHIVE` |
| answers file | `formato` · `porta` · `archivio` · `canale = stabile\|candidato` · `utenti = tutti` · `consenso.firewall` · `consenso.deposito.<x>` · `consenso.cinture` · `consenso.aggiornamenti` · `si`/`no` (also `sì`, `s`) | `format` · `port` · `archive` · `channel = stable\|candidate` · `users = all` · `consent.firewall` · `consent.repo.<x>` · `consent.guards` · `consent.updates` · `yes`/`no` (also `y`, `n`) |
| operation states | `NUOVA` · `FIDATA` · `ESAMINATA` · `VALUTATA` · `PIANIFICATA` · `APPROVATA` · `ACQUISITA` · `IN_ESECUZIONE` · `INTERROTTA` · `APPLICATA` · `IN_VERIFICA` · `VERIFICATA` · `CONFERMATA` · `CONFERMATA_A_CONDIZIONI` · `IN_ANNULLAMENTO` · `ANNULLATA` · `ANNULLATA_IN_PARTE` · `BLOCCATA` · `RIFIUTATA` | `NEW` · `TRUSTED` · `EXAMINED` · `ASSESSED` · `PLANNED` · `APPROVED` · `ACQUIRED` · `RUNNING` · `INTERRUPTED` · `APPLIED` · `VERIFYING` · `VERIFIED` · `CONFIRMED` · `CONFIRMED_WITH_CONDITIONS` · `ROLLING_BACK` · `ROLLED_BACK` · `PARTIALLY_ROLLED_BACK` · `BLOCKED` · `REFUSED` |
| certification outcome | `VERDE` · `A_CONDIZIONI` · `ROSSO` | `GREEN` · `CONDITIONAL` · `RED` |
| fact states, severity, nature | `RILEVATO` · `VERIFICATO` · `SCONOSCIUTO`; `AVVISO` · `BLOCCANTE`; `SERVE_AZIONE` · `RIPROVABILE` · `RECUPERABILE` · `SERVE_ANNULLAMENTO` · `FATALE` | `DETECTED` · `VERIFIED` · `UNKNOWN`; `WARNING` · `BLOCKING`; `ACTION_NEEDED` · `RETRYABLE` · `RECOVERABLE` · `ROLLBACK_NEEDED` · `FATAL` |
| reversibility, origin, outcome of a step | `ESATTA` · `AL_MEGLIO` · `CON_FOTOGRAFIA` · `IRREVERSIBILE`; `DIRETTA` · `INDIRETTA` · `PREESISTENTE` · `CONCORRENTE`; `COMPLETO` · `ASSENTE` · `A_META` · `ESTRANEO` | `EXACT` · `BEST_EFFORT` · `NEEDS_SNAPSHOT` · `IRREVERSIBLE`; `DIRECT` · `INDIRECT` · `PREEXISTING` · `CONCURRENT`; `COMPLETE` · `ABSENT` · `HALF_DONE` · `FOREIGN` |
| compatibility level | `CERTIFICATA` · `COMPATIBILE` · `NON_SUPPORTATA` | `CERTIFIED` · `COMPATIBLE` · `UNSUPPORTED` |
| log events | `STATO` · `INTENZIONE` · `FATTA` · `FALLITA` · `INTENZIONE_ANNULLA` · `ANNULLATA` · `ANNULLAMENTO_FALLITO` · `NOTA` · `COMANDO` · `RIPRESA` | `STATE` · `INTENT` · `DONE` · `FAILED` · `ROLLBACK_INTENT` · `ROLLED_BACK` · `ROLLBACK_FAILED` · `NOTE` · `COMMAND` · `RESUMED` |
| fact values | `si` · `presente` · `assente` · `con` · `senza` · `nessuno` · `sconosciuto` · `aperto`/`aperta` · `chiuso`/`chiusa` · `altro` · `attivo`/`attiva` | `yes` · `present` · `absent` · `with` · `without` · `none` · `unknown` · `open` · `closed` · `other` · `enabled`/`active` |
| fact names | `distro.famiglia` · `sistema.*` · `scheda.*` (`.fornitore`, `.modo`, `.gruppo`, `nodi`, `nvidia_proprietaria`) · `gruppo.*` · `pacchetto.*` · `deposito.*` · `codifica.*` (`strade`) · `porta.N.tcp_libera` · `.raggiungibile` · `firewall.tipo`/`zona`/`porta_*` · `h264.scheda`/`famiglia_driver` · `pam.base_mancanti` · `caratteri.scalabili` · `openssl.versione` | `distro.family` · `system.*` · `gpu.*` (`.vendor`, `.mode`, `.group`, `nodes`, `nvidia_proprietary`) · `group.*` · `package.*` · `repo.*` · `encoding.*` (`routes`) · `port.N.tcp_free` · `.reachable` · `firewall.type`/`zone`/`port_*` · `h264.gpu`/`driver_family` · `pam.base_missing` · `fonts.scalable` · `openssl.version` |
| step types | `installa-pacchetti` · `installa-desktop` · `scrivi-file` · `abilita-unita` · `accendi-servizio` · `regola-firewall` · `aggiungi-utente-a-gruppo` · `aggiungi-deposito` · `attiva-cintura` · `chiudi-sessioni` · `togli-iscrizione` · `togli-registri-utente` · `disfa` | `install-packages` · `install-desktop` · `write-file` · `enable-unit` · `start-service` · `firewall-rule` · `add-user-to-group` · `add-repo` · `enable-guard` · `close-sessions` · `remove-membership` · `remove-user-logs` · `undo` |
| JSON fields (plan, profile, report, certificate, log, events, offline bundle) | `formato` · `oggetto` · `stato` · `mestiere` · `azioni` · `parametri` · `impronta` · `controlli` · `condizioni` · `esito` · `dettaglio` · … (about 140) | `format` · `object` · `state` · `kind` · `actions` · `parameters` · `fingerprint` · `checks` · `conditions` · `result` · `detail` · … |
| files and folders in `/var/lib/remotix` | `operazioni/<id>/` with `stato` · `registro.jsonl` · `piano.json` · `fiducia.json` · `profilo.json` · `compatibilita.json` · `verifica.json` · `approvazione.json` · `insieme-risolto*.json` · `certificato.json`/`.txt` · `salvataggi/` (`.prima`, `.nuovo`); `piani/piano-<id>.json`; `installazione.json`; `aggiornamenti.json` | `operations/<id>/` with `state` · `log.jsonl` · `plan.json` · `trust.json` · `profile.json` · `compatibility.json` · `check.json` · `approval.json` · `resolved-set*.json` · `certificate.json`/`.txt` · `backups/` (`.before`, `.new`); `plans/plan-<id>.json`; `installation.json`; `recorded-versions.json` |
| the published archive | `motore/remotix-install(.sha256)` · `chiavi/remotix-archivio.asc` · `chiavi/LEGGIMI` · `LICENZE-COMPONENTI.txt` · `RILASCI.txt` · `pacman/*/remotix.versioni` · suite `<bersaglio>-stabile` | `engine/remotix-install(.sha256)` · `keys/remotix-archive.asc` · `keys/README` · `THIRD-PARTY-LICENSES.txt` · `RELEASES.txt` · `pacman/*/remotix.versions` · suite `<bersaglio>-stable` |
| the `remotix-install` package | `/usr/share/remotix-install/LEGGIMI` (Italian) | `/usr/share/remotix-install/README` (English) |

⚠ **They do not change** (they are identifiers, or the C product writes them): the `RX-…` codes (`RX-PACCHETTI-006`,
`RX-RISPOSTE-002`…) and the `C-…` conditions (`C-DEPOSITO`, `C-LIMITE`, `C-AMMINISTRATORE`…); the catalog format
(`remotix-catalogo/1`, Italian keys: it is our own data, inside the engine); the file `gruppi-iscritti.jsonl` and
the output of `remotix --prova-codifica`, which the engine reads as the product writes them; the product's files
(`/usr/share/remotix/cinture/…`, `remotix.conf.d/porta.conf` with `REMOTIX_PORTA`).

#### 6.6.16 10 Oct 2026: the installer of §10.36 (`DECISIONI.md` §10.36)

> What §6 above says about the signed archive, install.sh, third-party archives, desktop installed by the engine,
> the engine's firewall and belts, answers file, offline, plan/approve/apply and resume is **history**:
> this paragraph is what holds. Commits `2e16f8f` (engine), `8bcb881` (the .run), `623ea90` (benches).

**The principle** — REMOTIX does not modify the system: `check` says what is missing (RX-MANCA-001 desktop,
-002 archive the dependencies ask for, -003 pieces of an installed desktop, -004 no package for this
distribution in the .run; RX-GPU-003…006 the card and its driver), **without** suggesting packages or commands, and
`install` stops before touching. The exception wanted by the user: enrolment in the card's groups stays
automatic (at installation and at the first connection).

**The commands** — `check`, `install`, `uninstall`, `status` (state + the checks of `certifica` redone), `tui`;
hidden `catalog` (for the manual's table) and `post-upgrade` (for the package scripts).

| before | now |
|---|---|
| `plan` → `approve` → `apply` | `install`: check → simulation by the manager → plan with the exact packages → *«Proceed? [y/N]»* from stdin → execution → verification → service on |
| `resume`, `rollback` | an unfinished operation is found by `install` (it cancels it: first the manager's remedy, then from scratch, no automatic retry) or by `uninstall` (it completes it) |
| `--answers FILE`, `prepare-offline`, install.sh, signed archive, `--archive`, `--channel`, `--extra-repos`, `--open-firewall` | the **.run**: `sudo sh remotix-X.Y.Z-R.run [install\|check\|tui]`; updating = relaunching the new .run |
| package cache, our own sha256s, `--download-only` | the manager installs the .run's files and resolves the dependencies from the machine's archives; the engine only simulates (apt-get -s, dnf --assumeno, zypper --dry-run, pacman --print) |
| actions `add-repo`, `install-desktop`, `firewall-rule`, `enable-guard`, the components and the Vulkan driver | gone: the administrator puts them in place (the bench does it with `banchi/17-distro/17-amministratore.sh`) |

**The .run** — `installatore/run.sh` is the header: it extracts into `/var/tmp`, checks the sha256 of the payload
(written inside by the release), passes `--bundle <cartella>/packages` to the engine. Below, the tar.gz with the static engine and
`packages/<bersaglio>/` (product + `remotix-install` package) for debian13, ubuntu2604, fedora44, alma10,
tumbleweed, leap16, arch. `packaging/rilascio.sh` builds it and writes alongside the .sha256 to be published.

**The uninstallation** — the NEW packages of the installation, only those and only if nothing else asks for them
(the manager's simulation, as before). ⚠ Not the managers' autoremove: apt would also remove the orphans from
before, which are not ours.

**Numbers** — the engine (without tests) from **12 594 to 8 959 lines**; catalog `2026.10.10.13` (without the fields that
served only to suggest: `comandi`, `installa`, `carattere_scalabile`, `pacchetti_desktop`,
`pacchetti_scheda`, `vulkan_nvidia`; `vulkan_scheda` becomes `vulkan_codifica`, and `senza_h264_di_serie` tells the
manual where the distribution's driver does not have H.264); object format `remotix-install/3`.
`go test`: green (interface and engine); the .run tested on the laptop only in the header (extraction,
sha256, refusal of a broken file, `check`).

**What the campaign on the distributions must retest** (none of this is tested on the hardware):
1. the simulation and installation of the four managers with the .run's files — apt and dnf were tested on the VMs,
   **zypper and pacman never** on a real machine; dnf 4 (Alma) and dnf 5 (Fedora) with the same table reader;
2. `install` all the way on the 26 combinations in a BOX with the real card (in a VM the check refuses it),
   after `17-amministratore.sh`; the update with the N+1 .run with a browser connected (R7, R10);
3. that `check` says exactly what is missing on each one BEFORE the preparation (RX-MANCA-*, RX-GPU-006 on
   Fedora/Alma/openSUSE with the driver without H.264), and nothing after;
4. the cancellation of an interrupted installation (`install` relaunched) and the completion of an interrupted
   uninstallation, for real;
5. ⏳ **open point**: the card's groups — only `render` instead of `render` and `video` (§10.36: `video` also gives
   `/dev/fb*` and the webcams), to be measured on the four desktops; for now the logic is as it was;
6. ✅ **the licences of the third-party components** (10 Oct, LICENSE.md §8): `THIRD-PARTY-LICENSES` at the root of the
   repository, texts taken from the exact sources (ngtcp2, nghttp3 and sfparse, libopus and emscripten's C library
   in the `.wasm`, the 8 Wayland protocol descriptions, Go and the 17 modules `go list -deps` finds in the
   engine). It travels in every package (`/usr/share/doc/remotix*/` on the .deb, `%license` on the .rpm,
   `/usr/share/licenses/remotix*/` on Arch) and in the .run next to the engine; `rilascio.sh` stops if the file does not
   name a module, Go, ngtcp2, nghttp3 or libopus at the version that goes in. `packaging/archivio/` is no longer needed.
7. ✅ **TUI redone on the approved mockup** (`grafica/tui-mockup/index.html`), commit `facc27a`: fixed frame
   as wide as the terminal (at least 80 columns; below that, a line that says so), Check › Plan › Install › Ready,
   a body that scrolls inside the frame, keys at the bottom; `remotix-install tui --preview 80` draws every screen
   with sample data. Not from the engine, therefore not shown: the **size** of the packages (the manager's simulation
   does not give it) and **automatic suspend** as a line of the check (the engine does not detect it).
8. ✅ **labwc, wlr-randr, the scalable font and breeze6-wallpapers are dependencies of REMOTIX** (user,
   10 Oct; `DECISIONI.md` §10.36), commit `facc27a`: the engine adds them to the packages, the plan shows them in
   "Dependencies of REMOTIX" with the desktop that asks for them; `17-amministratore.sh` no longer prepares them. To be tested on the
   hardware: that the simulation and the installation take them from each distribution's archives.

---

## 7. The bench: the virtual machines of the distributions

### 7.1 The setup — ✅ up and running on 29 September

`banchi/17-distro/17-vm.sh`, copy on the server in `/media/REMOTIX/vm17/`. It descends from
`/media/REMOTIX/vm.sh` (v1's single VM): QEMU directly without libvirt and without root, network in user
mode with port forwarding, disk as an overlay on the official image, which stays intact.

- **The images** are the official *cloud* ones of each distribution, with cloud-init: debian13,
  ubuntu2604, ubuntu2404, fedora44, fedora43, arch, tumbleweed, leap16, alma10.
- **The machines** are called `<distro>-<desktop>` (`fedora44-kde`); `<distro>` alone is "bare".
- **Ports** on the server: ssh `2300 + 10·N + k`, REMOTIX `7500 + 10·N + k` (TCP and UDP), with N the number
  of the distribution and k of the desktop (bare 0, gnome 1, kde 2, xfce 3, lxqt 4).
- **Commands**: `crea`, `avvia` (waits for ssh and cloud-init), `vesti` (the desktop), `ssh`, `ferma`,
  `riavvia` (a REAL reboot of the guest, checked with the `boot_id`), `fotografa`/`torna`, `azzera`.
- `[M]` 29 Sep: **all nine distributions start** and answer ssh in 3-39 s; SELinux
  Enforcing on Fedora and Alma.
- ⚠ On the server QEMU must be reinstalled after every reboot (the system is in memory): it is in the recipe.
- `[M]` 29 Sep: **the 27 machines are ready** with the "cliente" snapshot (all rc=0); ubuntu2404-gnome stays for comparison, outside the matrix (D7).
- **How many VMs together: 4** (the user's decision: *«se il sistema regge passiamo da 4 a 8; se non regge
  torniamo a 4, così ci teniamo un po' di margine»*). `[M]` `17-carico.sh`, 8 VMs × 10 min, each with the
  login screen, a Full HD 30 fps software encode and 2.5 GB in use: **8 × 6 GB and 8 × 4 GB do not
  hold, for memory alone** (minimum available 1954 and 2868 MB against the threshold of 3072; mean
  swap 1536 and 2882 KiB/s against 100); encoding 29.7-29.9 fps and ssh ≤ 0.9 s always within. The VMs
  ask ~4.1-4.5 GB each, the server has ~30 free at rest (the system lives in RAM). A verification
  sent to refute it confirmed it, and found an earlyoom kill during the parallel
  shutdown that the verdict did not see (now the VMs shut down one at a time, before reading the
  journal). ⚠ Without a *balloon* a VM keeps the memory it touched: over hours of work a 6 GB VM goes
  towards 6 GB, not the 4.5 measured in 10 minutes. Unmeasured estimate: 6 × 4 GB probable, 5 × 6 GB no.

### 7.2 The machine "like the customer's"

The states of a test machine, with precise names:

| state | what it is | snapshot |
|---|---|---|
| **BASE** | the official *cloud* image, after cloud-init | the new disk |
| **DESKTOP** | BASE + the desktop with the distribution's **official package group** (`task-kde-desktop`, `kubuntu-desktop`, `dnf group install kde-desktop-environment`, `pacman -S plasma`, zypper's *patterns*…), `graphical.target` | `cliente` (today's name in the bench) |
| **ISO** | a machine installed **from the official ISO** with the distribution's automatic installer (preseed, autoinstall, kickstart, archinstall, agama) and its default desktop — the closest to a real machine | `iso` |

⚠ **A cloud image with a desktop on top is not a customer's machine**: it lacks the firewall
on, the display manager configured by the installer, sometimes SELinux in another state, the
packages the ISO puts in by default. ⇒ The everyday round starts from DESKTOP (quick to redo); the
**ISO** state is built for one machine per family (debian13-gnome, ubuntu2604-gnome,
fedora44-gnome, arch-kde, tumbleweed-kde, alma10-gnome) and the **whole round** goes through there too. The
differences between DESKTOP and ISO of the same combination are noted: if a test changes outcome between the
two, the truth is ISO's. ⛔ `vesti` installs nothing of REMOTIX: labwc, the card's groups, the codecs are the
installer's job, and the test must see them missing if it forgets them.

### 7.3 The script of a test

On each machine, automatic:

1. `torna cliente` (DESKTOP) or `torna iso` · fingerprints of the machine (`/etc`, `/usr`, groups, units, firewall);
2. **install** (the entry script, and separately the package manager);
3. a **real browser** gets in and sees the desktop (encoding with the software fallback, Full HD: in the VM there
   is no real card);
4. **real reboot** of the machine, and get back in;
5. **update** to N+1 with a live session, and check that the windows are still there;
6. **uninstall** (`purge`), and compare the fingerprints with those of point 1.

### 7.4 Short round and whole round

- **short round**, at every change to the installer: one machine per family (debian13, ubuntu2604,
  fedora44, arch, tumbleweed) — about 20 minutes;
- **whole round**, before declaring a version ready: all 26 — about 2 hours, three at a time,
  also at night.

### 7.5 The two things the VM does not test

1. **Encoding on the real card** with the Mesa and the drivers of each distribution (RPM Fusion,
   Packman): it is tested in a **box** of that distribution, which uses the server's card. One
   test per family, not at every round.
   ⭐ **1 Oct 2026 — T10 in a box** (the user's decision): the two machines that in a VM do not have
   KWin's screencast (`debian13-kde`, `leap16-kde`) run the SAME script of §7.3 in a container
   with the server's Intel card (`banchi/17-distro/scatole/`: `Contenitore.<m>` = the desktop with the
   official group, like `vesti`; `17-scatola.sh` with the verbs of `17-vm.sh`; `17-t10.sh <m> scatola`).
   A box has three things more than a machine, declared: systemd and sshd on a port of its own
   (`--network=host`, hence REMOTIX on a port of its own too: `porta =` in the answers file), the
   login manager off (it has no monitor and must not grab the host's card), the
   `video`/`render` groups aligned with the host's nodes (on the real machine udev does it). It **does not test** the
   real reboot of the machine: in its place the container's restart (`podman restart`), and the
   real reboot is green on the other 30 in VMs. With the real card the certification on Debian is
   **VERDE** (H.264 in hardware via `h264_vaapi`, iHD); on Leap it stays `C-RIPIEGO` because the image
   for containers has `solver.onlyRequires = true` like the Minimal-VM (§11.1) and the recommended
   `intel-media-driver` (repo-oss) does not go in — added by hand, `vainfo` gives H.264 EncSlice `[M]`.
   ⭐ **10 Oct 2026 — the 26 in boxes** (§10.36: since phase 19 a machine without a card does not pass the
   check, and the VMs have none): one recipe per distribution with the desktop as argument
   (`Contenitore.{debian13,ubuntu2604,fedora44,alma10,arch,suse}` + `comune.sh`; the two of 1 Oct are
   absorbed), `17-scatola.sh` for the 26 with `REMOTIX_SCHEDA=intel|amd`, name `t17-<m>-<scheda>`, own
   ports (ssh 8600+10n+k, REMOTIX 8800+10n+k, +100 on the Radeon), up to 4 on together, and
   `costruisci-tutte`. ⚠ Ubuntu: `firefox`/`thunderbird` (packages that install a snap) kept out
   with an apt preference, because snapd does not run in a box. The images are built ON THE
   SERVER (not on the laptop), once the xrdp campaign is over. `[?]` no recipe has been built yet.
2. **The card given to the VM** (passthrough): impossible today, the server boots with the IOMMU off; to
   turn it on the server's boot must be changed, which the user does. Not needed for this phase.

---

## 8. The tests — the measurable requirements

Each one runs on the VMs of §7; "red if" is the condition that makes it fail.

| # | requirement | the test | red if |
|---|---|---|---|
| R1 | the preliminary check touches nothing | fingerprints before/after `--verifica` | a difference |
| R2 | the check finds every known defect, **with its code** | machines **broken on purpose**: no card, no `h264_vaapi`, proprietary NVIDIA, port taken, PAM missing, SELinux without module, firewall closed | a fault not reported, reported without the **stable code** (§6.6.9) or without the command that remedies it |
| R3 | one command installs | `install.sh`, and the package manager, on every family | exit ≠ 0, or `remotix verifica` red afterwards |
| R4 | the dependencies are all declared | installation on the "cliente" machine with nothing by hand; libraries seen with a tenant's uid | a `not found`, or a package added by hand |
| R5 | idempotence | install twice | the second writes something |
| R6 | ⭐ the uninstallation **undoes everything REMOTIX did** (§6.6.4) — not "puts the machine back as it was": a dependency upgraded by the package manager does not go back | fingerprints before the installation and after `purge`, compared with the log | a difference **of DIRETTA origin** left; an INDIRETTA difference not declared in the certificate; ⛔ a user removed from a group they were in **before** |
| R7 | ⭐ during a **system update** that includes REMOTIX, REMOTIX does not close the users' desktops by itself | two users with a real browser and a terminal open; `apt upgrade`/`dnf upgrade`/`pacman -Syu` that takes REMOTIX to N+1 | a window gone, a stage process dead, a black screen on reattach |
| ~~R8~~ | ⛔ **removed on 30 Sep** (the user's word: *«io parlerei di aggiornamento del sistema, non di REMOTIX»*): the system update is decided and announced by the administrator (also with AMS, a separate project), and the interruptions in that window are expected. Only R7 stays with REMOTIX. The measured times (down ~4 s, browser with the image again ~9 s) remain as information in §5.2 | — | — |
| R9 | the new server finds **all** the stages again | `remotix stato` before and after; each goes back into **its own** | a session alive but not found again (the xrdp case) |
| R10 | the browser tab already open survives the version change | a tab open during R7, then reloaded | an unexplained error |
| R11 | going back works | N → N+1 → N with a live session | a session lost, or the configuration not read |
| R12 | a wrong configuration does not turn off the service | broken file in `/etc/remotix/remotix.conf.d/`, then update | the old service stopped before knowing that the new one starts |
| R13 | ⛔ no bench functions active | bench marks and options searched for in the binary **extracted from the package**, with the positive check on the test binary | found in the package, or not found in the test one |
| R14 | ⛔ no bench files in the package | list of files against a blacklist | a match |
| R15 | survives the reboot | installation, real reboot, connection | something that worked before and not after |
| R16 | the certificate is born at first start-up and can be replaced | deleted and restarted ⇒ new; one from the administrator ⇒ that one used | no certificate, or the administrator's ignored |
| R17 | signed and verified repositories | one byte altered; a wrong signature | the manager accepts it |
| R18 | the key is valid only for REMOTIX, and does not touch the repositories that were there | `Signed-By`, no `trusted.gpg.d`; on a machine with **other third-party repositories already configured**: their keys and their files unchanged, and no non-REMOTIX package installable from ours | global key; a file of another repository changed |
| R19 | SELinux active, zero denials | Fedora, Alma, Tumbleweed in *enforcing*: complete session, then `ausearch -m avc` | a denial related to REMOTIX |
| R20 | right PAM on every family | right login ⇒ logind session `user`, `Remote=yes`; wrong ⇒ refusal; root ⇒ refusal | a different case |
| R21 | installation without questions | cloud-init with a configuration file deposited | a question, a wait |
| R22 | installation without network | source prepared beforehand, VM without network | an access to the network |
| R23 | reproducible build — four levels: binary, package, package metadata, repository | two builds in two clean containers with the same `SOURCE_DATE_EPOCH` | `diffoscope` finds differences in the binary or in the package (T3); in the metadata and in the repository (T8) |
| R24 | complete SBOM | the SBOM names ngtcp2/nghttp3 with the version that is in the binary | version absent or different |
| R25 | useful welcome | the output has the five items of §6.5 point 8 | an item missing |
| R26 | the log says everything | every change found by R6 is in `modifiche.log` | an unrecorded change |
| R27a | the installer **has prepared the platform** on every combination of the matrix | the engine's 7a/7b certification (§6.0) | a required check not PASS |
| R27b | REMOTIX **works** on that platform | the short functional suite (phase 15) on each VM, in Full HD with the software fallback | a red that is not there on Debian — ⚠ it is a test of the **product**, not of the installer |
| R28 | ⭐ an installation that fails halfway is undone as a whole | fault injected at every step of phase 6 (network cut, disk full, broken package) | fingerprints different from before the start |
| R29 | the certification does not lie | phase 7 on machines broken on purpose (card that does not encode, broken PAM, closed port) | a "green" on a broken machine |
| R30 | ⭐ an interrupted installation is resumed | QEMU killed at **each of these points**: before the step is noted; noted but not started; with the package manager's transaction started; halfway through writing a configuration file; with the unit enabled but the log not updated; during the rollback. Then reboot and engine relaunched | the machine stays halfway; a step redone twice with a double effect; the resume does not lead to COMMITTED or ROLLED_BACK |
| R31 | the plan does not apply to a different machine | plan made, machine changed (a package removed), then application | the plan applied anyway |
| R32 | ⭐ UNKNOWN is never PASS | every check of the certification made to fail **by not knowing** (tool absent, permission denied, time out) | a PASS, or a COMMITTED certificate without CONDITIONAL/BLOCKED |
| R33 | the groups that were there stay | a user already in `video` before the installation; after `purge` | the user removed from `video` |
| R34 | the belts are undone to their previous state | an administrator's `logind.conf.d` already present that touches the same keys; installation and `purge` | his file changed, or the previous behaviour not back |
| R35 | the "conditional" state does not disappear | installation on Fedora without RPM Fusion (software fallback); then `remotix verifica` and the certificate | the condition not written, or written only in the plan |
| R36 | ⭐ three interfaces, a single engine | the same installation driven from CLI, TUI and GUI on three copies of the same machine | plan, resolved set, log (apart from the times) or certificate different among the three |
| R37 | the GUI does not run as root | the window's process during the installation | uid 0 |
| R38 | a machine without a desktop | "bare" VM (without desktop): answer "yes" ⇒ desktop installed, `graphical.target` and login screen NOT activated, desktop in the browser; answer "no" ⇒ BLOCCATA with `RX-DESKTOP-001` and fingerprints unchanged | a desktop that starts in front of the monitor; a machine touched after a "no" |
| R39 | the update goes through the package manager and does not close the desktops | (D14, §10.23) an N+1 release made with the release command, with a new catalog; the SYSTEM update (`apt upgrade`, `dnf upgrade`, `pacman -Syu`) with a browser connected | a REMOTIX file changed outside the package manager; a desktop closed or reborn (different process); the new catalog not in use; `certifica` not green afterwards |
| R40 | ⭐ the package alone turns nothing on | `apt install`/`dnf install`/`pacman -U` of the package alone on a "cliente" VM: fingerprints before and after, listening ports, groups; then `remotix stato` | the service on or listening; a group, a firewall rule or a belt activated; `remotix stato` that does not say "installation not certified" |
| R41 | a single program | during a complete installation, the tree of the engine's child processes (`/proc`) | a process that is neither the engine itself nor a program of the closed list; a script run; a call to a program not noted in the log |
| R42 | ⛔ *retired on 10 Oct 2026: the installer speaks only English (`DECISIONI.md` §10.35)* — the language follows the system | the same installation with `LANG=it_IT.UTF-8`, `LANG=en_US.UTF-8`, `LANG=de_DE.UTF-8` and `LANGUAGE=it:en`, in GUI (which relaunches itself with polkit) and in TUI | a screen or a message in the wrong language; an `RX-…` code different between languages |
| R43 | the uninstallation closes only the REMOTIX sessions | a user with a REMOTIX desktop open and, at the same time, an ssh session with a process that writes the time every second; uninstallation | the REMOTIX desktop still alive; the ssh session's process interrupted |

---

## 9. The milestones

| milestone | what | produces | status |
|---|---|---|---|
| **T0** | the VM bench and the 27 "cliente" machines | `banchi/17-distro/17-vm.sh`, snapshots `cliente` and `iso` | ✅ 29 Sep: 27 "cliente" + 6 "iso" (differences in `banchi/17-distro/iso-differenze.md`); 4 VMs together |
| **T1** | REMOTIX **compiles and runs** on every distribution, installed by hand: the cures of §4.4 and §5.1 | the portable product; R27 green, by hand | ✅ 30 Sep: compiles 7/7; runs 7 families out of 7 with the product binary, with the conditions of §11.1 |
| **T2** | the **measurement** of §5.2: what kills the desktops when the service is stopped | the cause, and the real estimate | ✅ 29 Sep: no desktop dies; light cure (§5.2) |
| **T3** | the three package **recipes** and the build containers per family | `.deb`, `.rpm`, `.pkg.tar.zst`; R4, R13, R14, R23 | ✅ 30 Sep: .deb (Debian 13, Ubuntu 26.04), .rpm (Fedora 44, Alma 10, Tumbleweed, Leap 16), Arch; inert pieces (§10.12); desktop in the browser on all of them with the engine's steps by hand; R23 to do for .rpm |
| **T4** | the objects and states of §6.6 (format, log, codes), then the engine with the CLI, phases 0-4: TRUST, PREFLIGHT, COMPATIBILITY, PLANNING, CONSENT & SAFETY (`remotix verifica`, `install.sh`) | R1, R2, R3, R25 | ✅ 30 Sep, line A (aec8402, 56c93d3): objects, states, log, resume, PREFLIGHT, catalog, CLI; R1 green in 4 containers; R30 in small green (§13.1) |
| **T5** | the engine, phases 5-8: the log of the actions, the certification, COMMIT / ROLLBACK; the uninstallation | R5, R6, R26, R28, R29 | ✅ 30 Sep, line A (56c93d3, ad5bc1b, 97918d0, 4dcaa70): the real actions of §10.12, the uninstallation from the log, `certifica` and R29; **complete round engine → package → Chrome → uninstallation on the seven families** (§13.1, table), R28 and R38 for real |
| **T6** | PAM per family, SELinux, firewall | R19, R20 | ✅ 30 Sep (b2ddbbd, 75c28de, 95f86d7): PAM = sshd on every family; `remotix-selinux` module (`remotix_t`); **R19 green** (0 denials in enforcing: Fedora 44, Alma 10, Tumbleweed, Leap 16 XFCE); **R20 green** on 7 families (Debian, Ubuntu, Fedora, Alma, Arch, Tumbleweed, Leap), faillock like ssh on Arch, Fedora and Alma; firewall with consent on firewalld and ufw, uninstallation without leftovers on the default zone (§13.1) |
| **T7** | the update without closing the desktops (according to T2 and D1) | R7-R12 | ✅ 30 Sep, the product's part (700cc1b, 307d042): the new parent finds the live desktops again; **R7, R8 (measured), R9 green on the 4 boxes** (§13.1); R10-R12 with the packages (T8) |
| **T8** | signed repositories, channels, rollback, SBOM; the automatic update (timer, catalog, D14) | R11, R17, R18, R24 | ✅ 30 Sep, with **TEST keys** (7b063f7, 6773a66, and the commit of the log §13): the archive of the three families (`packaging/archivio/pubblica.sh`), chain A in the engine, `aggiorna`/`ritorna` and the timer; **on the VMs**: installation from the archive on debian13-gnome, fedora44-gnome, arch-kde; R17 9/9, R18, R39 3/3 (desktop never closed, browser back in), R11 on apt/dnf/pacman, chain A BLOCCATA 8/8 (§13.1). Still depends on D10, D11, D14 (§10) |
| **T9** | the **TUI** and the **GUI** on the finished engine (R36, R37); without questions and without network; encoding on the real card per family (boxes) | R21, R22 | ⏳ 30 Sep, the part **without interfaces** (c7773c5): answers file, `installa`, offline bundle, `install.sh` (§6.6.12); **R21** green (cloud-init on debian13-gnome, Chrome in; file without a consent ⇒ BLOCCATA `RX-RISPOSTE-001`), **R22** green on debian13-gnome and fedora44-gnome (network removed, 0 attempts outwards in the capture, Chrome in), **R31** green (§13.1). ⭐ **The interfaces** (01b062f, §6.6.14): GUI with Gio and TUI with Bubble Tea in the same program (two builds of the same source); **R36** green (debian13-gnome, three copies: plan, resolved sets and certificate identical, log identical except the approval line that names the interface), **R37** green (window uid 1000, root part = transient systemd unit; as root RX-UI-003), **R42** green (GUI and TUI: it, en, de→en, `LANGUAGE=it:en`→it); the GUI on the real desktop of GNOME 48 and of KDE Plasma 6. Encoding on the real card in the boxes still to do. ⛔ **10 Oct: GUI removed** (§10.31, §6.6.14): R36 and R37 remain tests of 30 Sep, their bench (`t9-gui.sh`, `t9-r36.sh`) no longer runs |
| **T10** | the whole round on the 26 machines of the matrix, and the closure | all green | ✅ 30 Sep (product without ffmpeg, phase 18; test releases `0.18.1`→`0.18.4` from the release command, TEST key): **30 machines out of 32 (26 "cliente" + 6 "iso") GREEN** in the whole script — install.sh (sha256) → installa (CONFERMATA_A_CONDIZIONI: `certifica` green except `C-RIPIEGO`, in a VM no card and the video goes in software OpenH264) → real browser → real reboot → system update to N+1 with browser connected and desktop alive (RITROVATO) → uninstall `--purge` (R43, R6). Cured in T10: `libyuv` gone (cda31e6), PipeWire+wireplumber dependency (93040c2), Xwayland for labwc (d151ae9), and the engine which at uninstallation **keeps what is needed by what remains, repository included** (49ef16a: alma10-kde and fedora44-gnome-iso from ANNULLATA_IN_PARTE to CONFERMATA with RX-PACCHETTI-006). **2 platform ones** in VMs: `debian13-kde` and `leap16-kde` — the KWin of that version without 3D acceleration produces no screencast in a VM («monitor «», 0x0»); ubuntu/fedora/arch/tumbleweed KDE (newer KWin) pass in the same VM. ⭐ **1 Oct: the two KDE ones in a BOX with the real card (§7.5), releases `0.18.6-1`→`-2`: PASS at every step** — installa (Debian certification **VERDE**, H.264 in hardware; Leap `C-RIPIEGO`, §7.5), real browser (Chrome, «desktop kde», non-degenerate canvas), restart OF THE CONTAINER (declared), update to N+1 with the browser connected and the same stage (kwin_wayland, plasmashell), uninstall `--purge` (R43, R6, and no `sessione.log` in the homes). Cured there: the **chosen port** did not reach the service (004aa22) and the **decision on `sessione.log`** (9991f09, §13.1); `debian13-gnome` and `fedora44-gnome` redone in VMs with the same release: PASS. ⇒ **32 out of 32**. Bench `banchi/17-distro/17-t10.sh`/`17-t10-giro.sh`, `scatole/17-scatola.sh`. ⚠ In a VM Fedora/RPM's shutdown in the reboot is slow (~5 min, no defect) ⇒ `RX_VM_RIAVVIA_S` |

Order of the distributions within each milestone: first those that yield the most for the least (**Debian 13,
Ubuntu 26.04**), then **Fedora and Arch**, then **openSUSE** (the most awkward for H.264) and **Alma**.

Method, as in phases 12-16: small increments, the complete net after each one; the polishing of the
benches **does not stop** the milestones (*«ci stiamo avvitando in inezie tecniche bloccando il progetto»*,
29 Sep); targeted tests are done in seconds, the whole round only when needed.

---

## 10. The decisions that belong to the user

One at a time, each at the moment it is needed (the milestone is indicated). R8 was removed on 30 Sep (the system update belongs to the administrator).

| | the question | when | the proposal |
|---|---|---|---|
| **D1** | ~~Do the sessions wait for the new server instead of dying with it?~~ ⭐ **Superseded by the T2 measurement**: the desktops already survive. A smaller question remains: the child dies with the parent (by choice) — is that fine, given that the desktop stays and the new parent finds it again? | T7 | yes: the desktop is the thing that counts, the child is remade on reattach |
| **D2** | ✅ **CLOSED on 29 Sep**: yes, ngtcp2 and nghttp3 inside — from the user's general rule (`DECISIONI.md` §10.6): *what is missing or too old is brought by REMOTIX*, except the patented codecs (external archive with consent) and the desktops (outside the matrix) | — | — |
| **D3** | ✅ **CLOSED on 30 Sep**: REMOTIX **mirrors PAM** — the distribution's standard remote-access stack, `pam_faillock` and `pam_selinux` included where present (`DECISIONI.md` §10.18); root excluded like ssh | — | — |
| **D4** | ✅ **ALREADY DECIDED (`DECISIONI.md` §4.7, 15 Aug 2026)**, recalled by the user on 30 Sep: *nobody* shuts down, reboots, suspends the server — the entries hidden in the menus of the four desktops **and** the three belts (polkit, physical keys, automatic suspend). ⇒ the installer activates them **always, without asking**; declared in the plan and in the welcome, removed at uninstallation | — | — |
| **D5** | ✅ **CLOSED on 30 Sep**: consent required; a "no" ⇒ REMOTIX is not installed (`DECISIONI.md` §10.20); ✅ **reconfirmed on 30 Sep with phase 18**: even without ffmpeg, when the video would go in software, a "no" to the drivers' repository (RPM Fusion, Packman) **blocks** — the user's choice between "install declaring the software" and "block" | — | — |
| **D6** | ✅ **CLOSED on 30 Sep**: the installer opens the chosen port on the firewall; the router is the administrator's, no UPnP (§10.20) | — | — |
| **D7** | ✅ **CLOSED on 29 Sep: Ubuntu 24.04 out**, we start from 26.04 (the user's word: *«partiamo dalla 26.04»*) | — | — |
| **D8** | ✅ **CLOSED on 30 Sep**: on Ubuntu the default `ubuntu` session, not vanilla GNOME (§10.20) | — | — |
| **D9** | ✅ **CLOSED on 30 Sep: after the phase** (the user's confirmation). It is a defect neither of REMOTIX nor of the distributions: the immutable ones keep the system read-only by choice, and ask the engine for a **third way of installing** (layering the package and rebooting — `rpm-ostree`, `transactional-update` — or a `systemd-sysext` image; groups in `/usr/lib/group`) | — | — |
| **D10** | ✅ **1 Oct, for now** (the user's word: *«per il momento la lasciamo nella cartella locale del progetto»*): the release keys are in the project's `.chiavi/`, **ignored by git** (never in the repository nor on GitHub; the agents' copies do not see it); `rilascio.sh`, `pubblica.sh` and `pacchetti-motore.sh` find it by themselves even from a worktree. The REAL key is generated later, when the work is finished. — 🔸 **Direction of 30 Sep** (the user's words: *«un repository git privato, ad esempio REMOTIX-DATA»*; *«sto pensando di acquistare un dominio … che mi costi poco all'anno»*): `REMOTIX-DATA` **private** for the working material (recipes, catalog, publishing scripts — ⛔ never the key); the public **archive** of signed static files over HTTPS **on the user's VPS** (*«ho un server VPS»*, 30 Sep; a simple web server, `REMOTIX-DATA` can live there as a private git over ssh; build and signing on the laptop, on the VPS only already-signed files, ⛔ never the key), under **a domain of our own** because the address stays written on the customers' machines. Open: the domain (to be bought), where the key is kept (D11) | before the release | Cloudflare Registrar or Porkbun (low renewal price) |
| **D11** | ✅ **SIMPLIFIED on 30 Sep**: a single key, the archive's; installer verified with the sha256; catalog inside the package (`DECISIONI.md` §10.21). Remaining: where the key is kept (with D10) | with D10 | — |
| **D12** | ✅ **CLOSED on 30 Sep: Gio** (`DECISIONI.md` §10.19) — the GUI drawn by the program itself, identical on the four desktops, without a browser; the TUI with a Go library in the same program | — | — |
| **D13** | ✅ **CLOSED on 30 Sep**: the prototype is the base, with small improvements (§10.20) | — | — |
| **D14** | ✅ **CLOSED on 30 Sep**: REMOTIX is updated with the system (`apt upgrade`…), no timer of our own; at every version a release command regenerates packages, installer (sha256), catalog and archive (`DECISIONI.md` §10.23) | — | — |

**The choices of whoever installs: almost none** (the user's indication, 29 Sep: *«non riesco ad immaginare
grandi scelte da parte dell'utente sull'installazione di REMOTIX, se non solamente la porta»*):
- **the port** (default 7447): a single question, which holds for **TCP** (the page) **and UDP** (QUIC);
- two **consents**, not preferences, and **only where needed**: the external archive for H.264 (only Fedora
  and openSUSE, D5) and opening the firewall (only if it is on, D6);
- ⛔ everything else has a default value and **is not asked**: who gets in (the machine's users,
  root excluded), the certificate (generated), the three belts (active, stated in the welcome, D4), the card's
  groups. Whoever wants something else changes it later in `/etc/remotix/remotix.conf.d/`.

**If there is no desktop on the machine** (the user's proposal, 29 Sep 2026: *«se REMOTIX non trova nessun
desktop installato, o chiede di installarlo all'utente oppure REMOTIX non si installa»*):
- PREFLIGHT detects it; in the choices screen **one more question appears, only in that case**:
  "there is no desktop on this machine: do you want to install one?", with only the desktops the catalog considers
  good on that distribution (Alma: GNOME and KDE), among which **whoever installs chooses which** (the user's word); one is **already selected**, the distribution's reference one — GNOME on Debian, Ubuntu, Fedora, Alma; KDE on openSUSE and Arch — and it is also the one installed without questions if the answers file says nothing else. **Yes** ⇒ the desktop installation enters the plan
  as a declared action, with its weight (packages, GB); **no** ⇒ REMOTIX is not installed (BLOCCATA,
  `RX-DESKTOP-001`, with the why and the remedy);
- the same if there is **only an unsupported desktop** (Cinnamon, MATE, i3…): the existing one is not touched, the
  new one is added alongside;
- the desktop comes **from the distribution's archives** (the boundary of `DECISIONI.md` §10.6 stays: REMOTIX
  does not carry it along), and it is installed **without changing how the machine boots**: no local login
  screen nor graphical boot — REMOTIX's desktops are born without a screen, and a server stays a
  server in front of the monitor;
- it is an **AL_MEGLIO** action (§6.6.4): removing it does not make the machine identical, and the plan says so before the
  consent.

**The language of the screens** (the user's indication on the prototype, 30 Sep: *«il riepilogo a volte usa
termini quasi da programmatore»*): whoever installs reads **what happens and what they must decide**, in everyday
words ("Access", "System protection", "Your consent is needed", "I'll take care of it"); drivers, paths,
package names, `RX-…` codes and fingerprints are in a "Show technical details" closed by default — that is where
support looks for them. One writes **«password»**, not «parola d'ordine»: it is the term everybody knows (the user's word, 30 Sep).

⇒ The GUI (and the TUI) are **five screens**: check of the machine · **one** screen of choices ·
the plan, with a single "confirm" · the progress · the certificate and the welcome with the address.

---

## 11. Points to be confirmed `[?]`

The verification on the distributions (29 Sep) closed the five open points: GNOME 50 confirmed with the
cure of §5.1; Fedora with Intel **without** H.264 by default (the survey on the installers refuted);
minimum ngtcp2 1.25.0; Arch's `pam_faillock` 3/900 s/600 s; openSUSE SELinux enforcing by default and
`common-session-nonlogin`. Still **to be measured** on the VMs:
- `gnome-remote-desktop` on by default next to REMOTIX (port 3389, no conflict; but it opens
  capture sessions of its own on the same mutter);
- the `systemd-homed` users (Arch);
- any Ubuntu modifications to the gnome-shell 50 units;
- the jump of labwc 0.8 → 0.9 / 0.20 (wlroots 0.20.2 still has all the protocols we use `[L]`).

---

### 11.1 The outcomes of T1 (29 Sep 2026, evening) `[M]`

- **Compiles** (T1b + T1a merged, 8ecc925): **7 distributions out of 7**, ngtcp2/nghttp3 static, `ldd` clean
  on each; Ubuntu 24.04 stops at OpenSSL 3.0 (for D7: then `codificatore.c:1419,1436` for ffmpeg 6.1 and
  `input.c:1218` for libei 1.2).
- **Runs** (T1c, by hand in 7 VMs): one **gets in** everywhere («Ammesso», session created), but with the product
  binary **the desktop arrives on none**. The causes:
  - **(A) product defect**: without 3D acceleration the compositor does not offer DMA-BUF, REMOTIX asks
    only for those (`cattura.c:~1487`) and the fallback to memory kicks in only after the first frame, which
    never arrives. It holds for every machine without a card (VM, server without GPU). Cure in progress: fallback
    to memory **after** the negotiation fails, zero-copy stays the default route.
    With memory from the start (diagnostic binary) the desktop arrives on Debian, Ubuntu 26.04 (**the GNOME 50
    cure works**), Arch, Fedora, Alma;
  - **(B) SELinux** on Fedora and Alma: `pam_selinux open` leads to a denial `transition
    unconfined_service_t → unconfined_t` at the child's execution; without `pam_selinux`, zero denials in
    enforcing. ⇒ T6: a rule of our own (like Cockpit) or via `pam_selinux`; ✅ **cured in T6**: `pam_selinux`
    put back like sshd and the `remotix-selinux` module (`remotix_t` domain, §13.1), 0 denials;
  - **(C) no fallback without libx264/libx265**: without third-party repositories (Fedora, Alma, openSUSE) REMOTIX
    refuses to encode, by a choice written in the code, even where openh264 or svt-av1 are present; with RPM
    Fusion (`libavcodec-freeworld`) or Packman (`libavcodec63`) it works again. ⇒ weighs on D5;
  - **(D)** black canvas on Tumbleweed (KWin) and Leap (labwc) — the verification sent to refute found **two different
    causes**, neither of them the one written: the `CREATE_DUMB: Permission denied` is Mesa's on the
    `renderD128` node (the kernel refuses it to everyone, root included) and comes out identical on Arch, where it works.
    - **Tumbleweed: the wallpaper is missing.** The *Minimal-VM* image has `solver.onlyRequires = true` ⇒ the
      KDE group does not bring `breeze6-wallpapers`, plasmashell does not find the «Next» wallpaper and shows neither desktop nor
      panel (black even in KWin's own screenshot). With the package, the desktop arrives. ⇒ it belongs to the
      **platform installed without recommended packages** (another reason for the ISO state, §7.2);
      the installer on openSUSE brings `breeze6-wallpapers` (`C-COMPONENTE`);
    - **Leap 16: labwc cannot create the buffer on the virtual card** (`gbm_bo_create failed`), even
      launched by hand without REMOTIX. With `WLR_RENDERER=pixman` the XFCE desktop arrives. ⇒ limit of a
      machine **without 3D**, like (A). ✅ **Cured** (§13.1, `scheda_sa_disegnare()`): REMOTIX tests the
      buffer before giving the node to labwc and, if it is not born, starts labwc with `WLR_RENDERER=pixman`
      declared. `[M]` 29 Sep: on Leap 16 XFCE the desktop arrives, **even with the product binary**
      (labwc is captured from `wlroots.c`, not from PipeWire: (A) does not weigh here); on the server's and the
      laptop's Intel the test says "yes" and the route stays the card.
      - ⛔ **"refuses the size" is refuted**: the output moves to 1872×944 in 3 ms (reread). What stays
        1280×720 is **only xfdesktop's wallpaper**, even minutes later: xfdesktop is born ~150 ms **before**
        the size request and does not redraw — it is the same race cured for LXQt (phase 14, incr. 3,
        `primario_lxqt()`), not pixman. The XFCE cure is not in the same place: it touches the start line
        (`SESSIONE_RIGA_XFCE`), that is the logout belt (`XFCE4_SESSION_COMPOSITOR`); and on Leap
        `wlr-randr`, which the LXQt cure uses, **is not installed** (⇒ dependency for T3).
- **Closure of T1** (product binary with the two cures, 9e035c5): **boxes 208 PASS / 0 FAIL / 0 BLOCKED**,
  zero-copy intact on GNOME and KDE (14/14 stages on the card), the Intel card says "yes" to labwc (zero
  pixman fallbacks); **VMs: desktop in the browser on debian13-gnome, ubuntu2604-kde, fedora44-gnome, alma10-kde,
  arch-xfce, tumbleweed-kde** (with the conditions: RPM Fusion and PAM without `pam_selinux` on Fedora/Alma, 0
  SELinux denials in enforcing; Packman and `breeze6-wallpapers` on Tumbleweed; on Arch the xfce4 group does not
  bring ffmpeg: dependency for T3). On Alma RPM Fusion goes **after** EPEL, or `libavcodec-free` conflicts.
  - **leap16-lxqt: the fonts are missing.** `[M]` 29 Sep evening: the VM has **only bitmap fonts** (PCF,
    `xorg-x11-fonts-core`; `fc-match sans` = «Misc Fixed»). Pango 1.56 cannot measure them: the height of the
    title comes out **1 398 724 px**, `create_corners()` asks cairo for a 9×1 398 724 surface, cairo
    refuses (`_cairo_surface_nil_invalid_size`) and the `assert` of `buffer_adopt_cairo_surface` (buffer.c:90)
    brings labwc down (gdb with symbols: `main` → `theme_init` → `create_corners` → `rounded_rect` →
    `buffer_create_cairo`). It is neither pixman nor LXQt: bare labwc, without configuration, dies the same way. The
    font would be brought by the `lxqt` pattern (`google-droid-fonts`, **recommended**), lost with
    the Minimal-VM image's `solver.onlyRequires` — the same trap as Tumbleweed's wallpaper; the
    `xfce` pattern brings fonts by another route, and XFCE passed. It is the known defect labwc#2525 (closed
    by the author "a font was missing", **no cure**: in the main branch of 26 Sep 2026 the `assert`
    is still there). With `google-droid-fonts` (+ Packman for libx265, (C)): **PASS** with the product binary,
    0 SIGABRT, labwc in pixman declared, desktop at 0.6 s. ⇒ **T3**: the installer requires a scalable
    font (on openSUSE `google-droid-fonts`, `C-COMPONENTE`); REMOTIX alone cannot avoid it —
    without a vector font there is nothing to point labwc to. `[?]` proposal, not done: a
    line "⛔ no scalable font: labwc will die" before start-up (fontconfig, `FC_OUTLINE`).
  - **The first wlroots frame "BLACK" in the boxes is not new and is not a fault.** `[M]` it was already there
    in phase 16 (27 Sep, binary 45d048c8, `/media/REMOTIX/misure/fase16/intel-*/livello-*/server.log`):
    XFCE 107 stages out of 367, LXQt 150 out of 278, and the same on the Radeon; 0 on GNOME/KDE (they go through PipeWire).
    In the closure of T1: XFCE 12 out of 14, LXQt 3 out of 14 (the "24 lines" are each doubled, journal +
    session log). It is the first frame taken at labwc's birth, before wallpaper and
    panel are painted; the two cures do not touch the wlroots route on the Intel (0 fallbacks). Proposal
    not done: look at the first frame after ~1 s, so that the line flags only a black that lasts.
- **ISO state** (T0): 6 machines out of 6; the differences that count for the installer: `render` is never there;
  Fedora Workstation opens 1025-65535, **Alma and Tumbleweed have 7447 closed**; Tumbleweed with automatic
  login, btrfs and snapper (system snapshots already in place, §6.6.4), recommended packages installed; Ubuntu
  minimal desktop + snap, ufw off; network with NetworkManager everywhere.
- **Measured run-time dependencies** (for T3), beyond the binary: Ubuntu 26.04 `libavcodec62 libswscale9
  libavutil60 gnome-session`; Alma 10 `epel-release`, CRB, `libavcodec-free libavutil-free libswscale-free`;
  Tumbleweed `libavcodec63 libavutil61 libswscale10`; Leap 16 `libavcodec61 libavutil59 libswscale8
  libpipewire-0_3-0 libva2 libei1 labwc xwayland` (XFCE 4.20 does not start without Xwayland); Debian and Arch
  nothing more; Fedora port 7447 in firewalld (on after the Workstation group).
- `provisiona.sh` always installs Debian's PAM and its check is satisfied with "pam_systemd": on
  Fedora and Arch it would say green with a PAM with which nobody gets in (**false green**: it confirms that
  the installer is written from scratch).
- A bench trap: the browser on `127.0.0.1`, not `localhost` (QEMU forwards UDP only in IPv4, Chrome
  sends QUIC to `::1`).

---

## 12. Outside this phase

- the immutable distributions (D9);
- the distributions without systemd;
- the card given to the VM (passthrough) and the performance per distribution;
- a package **inside** the official distributions (Debian, Fedora): with ngtcp2 embedded it would not
  pass their rules; it is a later step, if ever.

---

## 13. The change log of phase 17 — for the technical manual

*Each change is noted here at the moment it goes in: commit · what · why · measurement ·
installed yes/no.*

### 13.1 The product (`src/`)

| commit | what | why | measurement | installed |
|---|---|---|---|---|
| d7f82c2 | `src/Makefile`: ffmpeg's headers from `pkg-config --cflags libavcodec libavutil libswscale` | on Fedora and Alma (ffmpeg-free) they are in `/usr/include/ffmpeg`: without it, `codificatore.c:24` does not find `<libavcodec/avcodec.h>`. On Debian it only adds `-I/usr/include/x86_64-linux-gnu`, which was already there | `[M]` 29 Sep: Fedora 44 and Alma 10 compile; Debian 13 identical (1 warning only, `main.c:500`) | no |
| c1573ae | `sessione.c` `unita_shell()`: the Shell is chosen from the `FragmentPath` that the user manager gives for `@wayland` (the `@wayland` file ⇒ that one; the `@.service` template ⇒ `@user`; anything else ⇒ it stops and says so); drop-in in `<istanza>.d/`, never in the template; the rereading of the `ExecStart` on the same unit; the clear-out knows `@wayland.d` and `@user.d`; `provisiona.sh` cleans and checks `@user.d` and `@.d` too (only our file) | GNOME 50 starts `@user`: the drop-in on `@wayland` was not applied and the check gave a false green (§5.1) | `[M]` compiles clean in the Debian 13 container; `[M]` on the laptop (GNOME 48.7) `FragmentPath` = `…/org.gnome.Shell@wayland.service`; `[M]` with a fake template `x@.service` the `FragmentPath` of `x@wayland` is the template and the `ExecStart` of `x@user` carries `--mode=user`. ⛔ Real GNOME 50 not tested: that is T1's job on the VMs | no |
| 61ad596 | PAM per family: `src/remotix.pam` (Debian/Ubuntu), `.fedora` (`password-auth`+`postlogin`, `pam_selinux` close/open, `pam_loginuid`; `pam_systemd` from `password-auth`), `.suse` (`common-*`, `common-session-nonlogin` + `pam_systemd`; goes in `/usr/lib/pam.d`), `.arch` (`system-remote-login`). In all of them root excluded with `pam_listfile` on `/etc/remotix/utenti-negati`, in `auth` and `requisite` (no oracle on root's password), `onerr=fail` (Cockpit uses `succeed`: a lost file would remove the exclusion silently). `pam_faillock` not chosen by us: D3 stays open, written in every file. `main.c` looks for the service in `/etc/pam.d` and then in `/usr/lib/pam.d`; the text about "other" corrected in `autenticazione.c` too (and in the copy `banchi/rcp/`). `provisiona.sh` and `costruisci.sh` write `utenti-negati` (root) if missing | `@include` is Debian's: elsewhere nobody gets in (§4.3); the message said "other is pam_deny on Debian", false | `[M]` four containers (debian:13, fedora:44, archlinux, tumbleweed), `pam_authenticate`+`pam_acct_mgmt`: without the file ⇒ rejected ("Error in service module"); right user ⇒ gets in; wrong password ⇒ rejected; root with the right password ⇒ rejected without the password being asked. ⛔ The session (`pam_open_session`, `pam_selinux`, `pam_systemd`) not tested: there is no systemd in the containers. ⚠ To be noted, not done (it touches the C): `main.c` does not look at `utenti-negati` at start-up | no |
| c687c0c | `certificati.c`: the subject name is built with `X509_NAME_new` and handed over with `X509_set_subject_name`/`X509_set_issuer_name`, instead of writing into the name returned by `X509_get_subject_name`; and the outcome of `X509_NAME_add_entry_by_txt` is now checked | in OpenSSL 4.0 `X509_get_subject_name` returns `const X509_NAME *` (Ubuntu 26.10, Fedora rawhide) | `[M]` `certificati.c` alone with `-Wall -Werror`: on fedora:rawhide (OpenSSL **4.0.2**) the old one does not compile (`discards 'const' qualifier`, line 149), the new one does; on debian:13 (3.5.7) both compile; in both the generated certificates have subject = issuer = `CN=192.168.0.2` and the right SAN. ⚠ The rest of `src/` has not been compiled with OpenSSL 4 | no |
| e177e0c | `sessione.c` `registro_sessione_percorso()`: the session log moves from `/tmp/remotix-sessione-<uid>.log` to `$XDG_STATE_HOME/remotix/sessione.log` (usually `~/.local/state/remotix/`); folder 0700 verified (real, ours, not writable by others), file opened with `O_NOFOLLOW`, 0600, verified regular and ours; if that is not possible, declared fallback to `XDG_RUNTIME_DIR`, and without even that the session starts without a log (stated); the path passes to the shell with `g_shell_quote` | predictable name in `/tmp`: another user creates it first and the desktop does not start (with `protected_regular`), silently — it is R10-A9 of `fasi/10` | `[M]` compiles clean in the Debian 13 container; `[M]` the three functions extracted and run as a user: normal case ⇒ 0600 file in the new place; folder a link, file a link to `/etc/passwd`, folder 0777 ⇒ declared fallback; no home and no runtime ⇒ NULL declared. `grep`: no bench reads the old file (the `04-*`/`06-*` benches use their own `/run/user/<uid>/remotix-sessione.log`) | no |
| fe9f354 | `Makefile`: real minimums declared and CHECKED by `make dipendenze` with `pkg-config --atleast-version` (libavcodec ≥ 61.13.100, libavutil ≥ 59, libswscale ≥ 8, OpenSSL ≥ 3.5.0, ngtcp2 and ngtcp2_crypto_ossl ≥ 1.25.0, nghttp3 ≥ 1.18.0, libei ≥ 1.1.0, libpipewire ≥ 0.3.48, gio ≥ 2.80), three distinct outcomes (fine / too old / pkg-config does not know it); with `PREFISSO` the library folder is asked of `pkg-config` inside the prefix (`lib64`, `lib/<multiarch>`, `lib`), and if it does not answer the folders that exist are taken; `costruisci.sh` looks at `lib64` too; removed the only warning of the build (`/*` in a comment of `main.c`) | "libavcodec ≥ 61" was not enough (FFmpeg 7.1 is needed); `dipendenze` looked only at the headers; the rpath assumed `lib` (Fedora/SUSE: `lib64`) | `[R]` FFmpeg `APIchanges`: `avcodec_get_supported_config` = lavc 61.13.100; `[R]` libei.h 1.0.0 without `ei_region_get_mapping_id`, 1.1.0 with it; `[R]` pipewire `keys.h` 0.3.44 without `PW_KEY_NODE_FORCE_QUANTUM`; `[M]` `cattura.c`/`cursore.c`/`suono.c` compile with pipewire 0.3.48 (ubuntu:22.04), `input.c` with libei 1.2.1 (ubuntu:24.04); `[M]` `make dipendenze` in the container: all OK, and with fake minimums it gives NO/?? and exits 2; `[M]` fake prefix with `.pc` in `lib64` ⇒ `-L…/lib64 -Wl,-rpath,…/lib64`, without `.pc` ⇒ the `lib64` folder that exists; build from scratch clean, zero warnings. `[?]` nghttp3's real minimum not looked for | no |
| 192d482 | `sessione.c` `scheda_sa_disegnare()`: before giving the node to labwc (XFCE, LXQt) a test buffer is created with `gbm` — XRGB8888 256×256, usages `SCANOUT\|RENDERING` and then only `RENDERING`, the same with which wlroots' allocator falls back. If neither is born: `WLR_RENDERER=pixman`, no `WLR_RENDER_DRM_DEVICE`, and a line «RIPIEGO DICHIARATO» with the reason; if it is born, everything as before | machine without 3D (VM `virtio_gpu`, §11.1 D): the node opens but labwc does not create the buffer (`gbm_bo_create failed`) ⇒ black canvas. A generic criterion (the machine is asked), no exception per distribution or desktop | `[M]` 29 Sep: compiles on Leap 16 and Debian 13, zero warnings. Probe alone (`gbm`): Intel of the laptop and of the server (i915) ⇒ "yes" with both usages; Leap 16 VM ⇒ "no", `Permission denied`. Leap 16 XFCE installed by hand (T1c, + Packman for libx264/x265, diagnosis only), real Chrome: **PASS** with the diagnostic binary and **PASS with the product binary**, with no manual settings; labwc with `WLR_RENDERER=pixman` in its environment. ⚠ xfdesktop's wallpaper stays 1280×720 (birth race, §11.1 D) | no |
| 6bede6a | `cattura.c`/`cattura.h`/`figlio.c`: the **fallback to memory after the card is refused**. `cattura_formato_rifiutato()` = stream in error **and** no format ever agreed (two facts, not PipeWire's text); `cattura_avvia()` says so with `G_IO_ERROR_NOT_SUPPORTED` if it arrives before it returns. In `prendi_il_palco()` `ripiega_se_rifiutata()` switches the route to MEMORY, writes «la strada della SCHEDA e' stata RIFIUTATA … RIPIEGO DICHIARATO», sets `scheda_mai_piu` and reopens only the capture on the same stage. `cattura_prendi()` leaves a stream in error at once instead of waiting 5 s. No double offer (memory next to the card would let the compositor choose) and no fallback on silence (a slow compositor on a real card would give the same silence); no exception per compositor | T1c: without 3D (VM `virtio-vga` without virgl, server without a card) the compositor has no DMA-BUF, the negotiation dies with "no more input formats" and the fallback of `scheda_da_abbandonare` lives inside a frame that does not arrive ⇒ «Ammesso» and desktop never; the child remounted on the card every 5 s forever | `[M]` 29 Sep, binaries of `costruisci-tutti.sh`, real Chrome: **VM** debian13-gnome PASS (desktop at 4.5 s; before the quick fallback 10 s), arch-kde PASS, ubuntu2604-gnome PASS (with the old binary 0 out of 3); the refusal and the fallback are **7 ms** from the capture started. **Intel boxes** (binary debian13 `3e026237`, new PAM + `utenti-negati`), round `17-cura-copia-zero` f001 f003 f004 f011 f016 f018 f018b × 4 desktops × Chrome and Firefox: **208 PASS / 0 FAIL / 0 BLOCKED** (25 min); in the log 14 stages per desktop all «SCHEDA (DMA-BUF, copia zero)», 0 «MEMORIA», 0 «RIFIUTATA»; GNOME and KDE 14/14 «i fotogrammi arrivano come DMA-BUF», XFCE and LXQt 28 «PRIMO fotogramma della SCHEDA» and 0 wlroots fallbacks | no (boxes back to `4fb3287d` and to the previous PAM) |
| — | ⚠ **not done, noted**: `figlio.c:4684` always opens `renderD128` for the encoder: with two cards it may take the wrong one; it must be chosen by the driver (§4.4). Outside T1a by mandate | — | — | — |
| c95146c | **T3, line B — the `.deb` package** (`packaging/debian/`, debhelper 13, `dh_installsystemd`): `/usr/libexec/remotix/remotix`, `/usr/share/remotix/{pagina.html,remotix.conf}`, `/etc/remotix/remotix.conf.d/` empty; **conffiles** `/etc/pam.d/remotix` (Debian's PAM, `src/remotix.pam`) and `/etc/remotix/utenti-negati` (root); `remotix.service` as root (`KillMode=mixed`, `Restart=on-failure`, `--nome %H`, `--journal`, no bench options; certificate generated by the program at first start-up, `certificati.c:302`); KWin's permission `/usr/share/applications/org.kde.remotix.desktop` **identical byte for byte** to the one `kwin.c:606` writes; the three belts in the **vendor** paths (`/usr/share/polkit-1/rules.d/50-…`, `/usr/lib/systemd/{logind,sleep}.conf.d/`) — ⚠ **they depend on D4, open**; `tmpfiles.d` (`/var/lib/remotix` 0700, `/run/remotix`); postinst: the people (UID_MIN..UID_MAX, real shell) in the groups READ from the `/dev/dri` nodes, each pair noted in `/var/lib/remotix/modifiche.log` as DIRETTA or PREESISTENTE, a pair already noted is not rewritten (R5); postrm purge: away **only** the DIRETTA ones, then `/var/lib/remotix`. **Dependencies**: `dpkg-shlibdeps` + `libpam-systemd libpam-modules passwd systemd dbus-user-session` (used at run time, dpkg does not see them); **Recommends** `va-driver-all \| va-driver, labwc, wlr-randr, xwayland` and, only on Ubuntu, `gnome-session \| plasma-workspace \| xfce4-session \| lxqt-session` (D8 open: the vanilla session only if there is not already another desktop). `Static-Built-Using: ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0)` (D2 closed). `src/costruzione/costruisci-deb.sh`: copy of the tree, `debian/changelog` with version and date of the commit (⇒ `SOURCE_DATE_EPOCH`), `dpkg-buildpackage -b` in the container, lintian, R4/R13/R14/R23 checks on the FINISHED package; `Contenitore.debian13`/`.ubuntu2604` with a layer of `.deb` tools at the end | T3 (§6.1-§6.4): the native recipe, dependencies computed and not written by hand (`LEZIONI.md` §2.5-bis) | `[M]` 29 Sep, 313ccfc: **compiles** Debian 13 and Ubuntu 26.04; **lintian 0 E / 0 W**, 1 info (`systemd-service-file-missing-documentation-key`), 3 justified overrides (`pagina.html` is not documentation; `systemctl reload systemd-logind`, which `deb-systemd-invoke` cannot do); **R13** 0 phrases of the bench function in the binary extracted from the `.deb`, 1 in the positive check (`rcp.o` with `BANCO_ACCESO 1`), no bench option in the unit; **R14** no bench file; **R4** `ldd` 108 (Debian) and 111 (Ubuntu) libraries, 0 missing, ngtcp2/nghttp3 not dynamic; **R23** two builds in two clean copies ⇒ `.deb` **identical** byte for byte (Debian `a907d059…`, Ubuntu `966fcd73…`). Tests in VMs: see §13.2 | yes, in the test VMs (then removed) |
| — | ⚠ **not done, noted by T3** (it touches the C, outside the mandate): (1) `kwin.c:606` `kwin_scrivi_permesso()` must stop **writing** `/usr/share/applications/org.kde.remotix.desktop` (it belongs to the package) and only check it — today it does not rewrite it because it finds it identical; (2) `figlio.c:1525` `iscrivi_ai_gruppi_della_scheda()` enrols at the first connection whoever was born after the installation but **does not note it** in `/var/lib/remotix/modifiche.log`: purge does not remove it; (3) with `--journal` under systemd **every line appears twice** in the journal (one from stderr, one structured): the program should be silent on stderr when `JOURNAL_STREAM` is its stderr; (4) the certificate of §6.6.13 (`0-generato.pem`, `/etc/remotix/certificati.d/`) is not there: the package relies on today's (`pagina.pem`/`sessione.pem`, mark `.nostro`); (5) `/usr/bin/remotix` (verifica, stato…) and the real configuration belong to T4: today `remotix.conf` is a provisional `EnvironmentFile` | — | — | — |
| a3b722a…a6d0908 | **T3, line D — the Arch package** (`packaging/arch/`): `PKGBUILD` that builds from the **commit's tarball** (`costruisci.sh`: `git archive` of `src/`, `banchi/rcp/`, `packaging/arch/`, then `makepkg` in the `arch` container as a user, namcap in a throwaway container, R14 blacklist, `SOURCE_DATE_EPOCH` = date of the commit); ngtcp2 1.25.0 and nghttp3 1.18.0 **static** from the official tarballs with pinned sha256, built in `build()` (D2 closed; ⓘ per §10.6 on Arch the system `libngtcp2`/`libnghttp3` could be used, already 1.25 with the crypto_ossl bridge: it stays inside for uniformity); `-ffile-prefix-map` (the `__FILE__` of ngtcp2's asserts carried `$srcdir` into the binary); `!lto !debug`. **Arch paths**: the binary in `/usr/lib/remotix/remotix` (Arch does not use libexec: namcap «ELF outside of a valid path»), `pagina.html` in `/usr/share/remotix/`, unit `remotix.service` (as root, `KillMode=mixed`, `LimitRTPRIO=20`, `LimitNICE=-11`, `Restart=on-failure`, `REMOTIX_PORTA=7447` and `REMOTIX_NOME=%H` changeable with a drop-in, no bench options), `tmpfiles.d` (`/var/lib/remotix` 0700), PAM `src/remotix.pam.arch` in `/etc/pam.d/remotix` and `/etc/remotix/utenti-negati` (root) in `backup=()` (**D3 open**: `pam_faillock` comes with pambase's `system-auth`, neither added nor removed), KWin's permission `/usr/share/applications/org.kde.remotix.desktop` **identical byte for byte** to that of `kwin_scrivi_permesso()` with `Exec=/usr/lib/remotix/remotix`, the firewalld service **defined** (`/usr/lib/firewalld/services/remotix.xml`, no zone touched); ⛔ **§10.12**: the three belts **off** in `/usr/share/remotix/cinture/` (the engine mounts them, D4), `remotix.install` does **not** enrol in the groups and turns nothing on (post_install: only a notice; post_upgrade: `try-restart`, the place where the engine is called back; pre_remove: `disable --now`; post_remove: certificates and ban removed). **Dependencies**: by **soname** (`libavcodec.so=63-64`, `libssl.so=3-64`, … computed by makepkg on the binary) + the packages; plus `labwc wlr-randr` (XFCE/LXQt, no Arch group brings them; labwc pulls `ttf-font`, the font of labwc #2525) and `pipewire wireplumber pipewire-pulse` (the xfce4 group has no audio). ⭐ **Rolling release**: tie to the **soname**, not to the exact version: ffmpeg updates freely as long as the ABI stays, and at a soname change `pacman -Syu` **refuses** («breaks dependency») until it is rebuilt — the exact version would block every ffmpeg update, security included, and with it the whole `-Syu`. Our burden: rebuild at every new soname. `Contenitore.arch`: + `labwc wlr-randr wireplumber pipewire-pulse` (makepkg wants to see the run-time dependencies installed too) | T3 (§6.1-§6.4), §10.6, §10.12 | `[M]` 29 Sep, a6d0908: **compiles** clean (0 REMOTIX warnings), `make dipendenze` green; `check()`: `BANCO_ACCESO 0`, ldd without ngtcp2/nghttp3 and nothing missing. **namcap**: 1 E — licence `LicenseRef-REMOTIX` without a file in `/usr/share/licenses/remotix/` (a product licence is missing: to be decided); W — implicit `libgcc` (normal), "perhaps not needed" `systemd labwc wlr-randr pipewire wireplumber pipewire-pulse` (not linked: they are needed at run time, intended); PKGBUILD clean. **R14** 30 entries, none from the blacklist. **R23** two builds ⇒ package **identical** byte for byte (`51d6ea2f…`); without `SOURCE_DATE_EPOCH` same binary, package different only in `builddate`. ⚠ R13 only via `BANCO_ACCESO 0` in the source: the search for the phrases in the extracted binary (like line B) is not done. Tests in VMs: §13.2 | yes, in the test VMs (then removed) |
| — | ⚠ **not done, noted by line D** (it touches the C): (1) like line B, `kwin_scrivi_permesso()` must only check (on Arch `[M]` the program finds the package's file identical and writes «c'e' gia'»); (2) **R40 half red**: the package alone turns nothing on, but `systemctl start remotix` by hand **starts** — the `RX-INST-001` check is missing (§10.12 point 3); (3) the product at run time writes outside the package and after `-Rns` it remains: `~/.local/state/remotix/sessione.log` (DIRETTA) and on XFCE the user's power settings (`xfce4-power-manager.xml`, written by `sessione.c`: DIRETTA but meant to persist by §8.2) — the engine must say what it does with them | — | — | — |
| aec8402 | **T4, line A, first part — the `remotix-install` engine** (`installatore/`, static Go, `CGO_ENABLED=0`, 4 MB; only dependency `godbus/dbus` v5.1.0 in `vendor/`, build without network). **Objects** `remotix-install/1` (profile, compatibility report, plan, resolved set — empty, without packages —, log, verification report, certificate JSON + text) and **line-based JSON events** (`--eventi`, the channel of TUI and GUI). **States** of §6.6.2 with only the transitions of the design (`stati.go`), state in `<operazioni>/<id>/stato` written atomically, `flock` lock. **Log** `registro.jsonl`: INTENZIONE (with the previous state and the origin) → effect → FATTA/FALLITA, fsync of the file and the folder; the truncated final line is removed and stated (`RX-RIPRESA-003`); **resume** with the table of §6.6.3 (nothing ⇒ does it; INTENZIONE ⇒ `controlla`: complete ⇒ FATTA, absent ⇒ redoes, halfway ⇒ undoes and redoes, **foreign** ⇒ BLOCCATA `RX-RIPRESA-001`; FATTA ⇒ consistency check). **Actions** with do/check/undo/undone/constraints, reversibility and origin: `scrivi-file` (backup of the previous file in the operation's folder, temporary with a fixed name + rename, created folders removed if empty), `aggiungi-utente-a-gruppo` (`gpasswd`; PREESISTENTE also as primary group, never removed), `abilita-unita` (D-Bus systemd1: GetUnitFileState, EnableUnitFiles, DisableUnitFiles, Reload), `regola-firewall` (D-Bus FirewallD1, runtime and permanent, only our rules are removed; ufw and nftables recognised and declared `RX-FW-004`); **declared and not done** (`installa-desktop`, `installa-pacchetti`, `aggiungi-deposito`, `attiva-cintura`, `accendi-servizio`): they are in the plan, and the operation stops before touching with `RX-AZIONE-004`. **PREFLIGHT** read-only: os-release and family, immutable ones, systemd, desktops and packages from the database (dpkg and pacman from their files, **one** `rpm -q` for the RPM families), third-party repositories, cards and nodes with the driver (proprietary NVIDIA), H.264 from libavcodec (h264_vaapi, libx264) and from the VA-API drivers, SELinux/AppArmor, port listening (`/proc/net`), firewall (firewalld on the bus, ufw's files, nftables as a unit), the family's PAM (and `pam_faillock`, `pam_systemd`), OpenSSL, `KillUserProcesses` (logind on the bus ⇒ VERIFICATO), `video`/`render` groups, scalable fonts; each fact RILEVATO/VERIFICATO/SCONOSCIUTO, the programs launched in the profile (R41). **Fingerprint** binding (sha256 of the canonical text) + noted; the plan carries it, `applica` redoes it and says which elements changed (`RX-PIANO-001`). **Consent**: approval tied to the plan's digest (`approva`, or `--approva` by hand); without it, RIFIUTATA. **Catalog** `catalogo/catalogo.json` (embedded; version, sequence, expiry, minimum engine, separate signature planned): the matrix of §3 and §3.1, Ubuntu 24.04 and Mint 22 out (D7), derivatives, exclusions, `C-…` conditions (H.264 repositories, `gnome-session`, `breeze6-wallpapers`, `wlr-randr`, scalable font, EPEL for KDE on Alma, `C-DESKTOP`), minimum versions of the components; `remotix-install catalogo --tabella` **generates** the tables of §3.1. **Without a desktop** (§10.7): the choice in the plan with the catalog's desktops and the reference one already selected; "no" ⇒ BLOCCATA `RX-DESKTOP-001`. **`installazione.json`** next to the operations (id of the CONFERMATA operation, only the `installazione`/`aggiornamento` kinds: informative, §10.12); `remotix-install aggiornato` for the package scripts (says whether certified, redoes the verification, TryRestartUnit on the bus). **Bilingual** (§10.15): language from LANGUAGE, LC_ALL, LC_MESSAGES, LANG or `--lingua`; codes in `codici.go` + `codici_en.go`, the rest in `testi.go` | §6.0, §6.6, §8 (R1, R2, R5, R28-R32, R36), DECISIONI §10.10, §10.12, §10.14, §10.15; the engine must run as root before any package: no Python or libraries | `[M]` 30 Sep, `go test`: **120 PASS / 0 FAIL** — the engine **killed with SIGKILL** (child process, no cleanup) at 35 points of the application (for each of the 7 actions: before the intent, after the intent, with the file half written, with the effect done, after FATTA; and in 4 transitions) then `riprendi` ⇒ **CONFERMATA** with the machine **identical** to that of an uninterrupted round and no action FATTA twice; the same 35 then `annulla` ⇒ **ANNULLATA** with the machine identical to before (the firewall rule and the `video` member that were there stay); killed at 16 points **during the rollback** ⇒ the resume finishes the rollback; interrupted before touching (6 states) ⇒ BLOCCATA without touching, and a new `applica` starts; truncated log line; FATTA undone by others ⇒ BLOCCATA, then ANNULLATA (or ANNULLATA_IN_PARTE if the file was changed by the administrator, which stays his); a step that fails (R28 in small) ⇒ ANNULLATA; fingerprint changed (R31) ⇒ BLOCCATA without touching; check without an answer (R32) ⇒ UNKNOWN and never CONFERMATA; idempotence (R5) ⇒ all PREESISTENTE, zero writes. Two **mutations** by hand (resume that re-snapshots the machine instead of using the previous state from the log; group always PREESISTENTE) ⇒ red at once (`TestAnnullaDopoInterruzione`, plus subtests each): the tests have teeth. **R1** (`prove/r1-contenitori.sh`, fingerprint of `/etc` with permissions, owners, times and sha256): **identical** after `verifica` and `verifica --json` in debian:13 (161 entries), fedora:44 (1189), archlinux (948), tumbleweed (130). **For real** (`prove/systemd-giro.sh`, Fedora 44 with systemd running in podman): plan → approve → apply ⇒ **CONFERMATA**, unit `enabled` via D-Bus, `provamotore` in `video` via `/usr/bin/gpasswd`, the two programs launched in the log; a step that fails after the two files and the unit ⇒ **ANNULLATA**, unit `not-found` again, `/etc` identical in contents, permissions and owners (not in the folders' times). On the laptop (Debian 13, Intel): `verifica` reads logind on the bus (VERIFICATO), libavcodec with h264_vaapi and libx264, 7 VA-API drivers. ⚠ firewalld does not start in rootless podman: the firewall rule via D-Bus is tested only with the fakes | no |
| — | ⚠ **not done, noted by line A** (T4 first part): (1) **H.264 VERIFICATO in PREFLIGHT**: with the previous code (a frame encoded by `ffmpeg -f null`) the laptop gave `h264.scheda = si VERIFICATO`; ffmpeg is not in the closed list of §10.14, and PREFLIGHT now says SCONOSCIUTO (7a will do the test with the REMOTIX binary) — putting it in the list is one line, **the user's decision**; (2) the **signature** of the catalog and of the engine (TRUST): model ready, scheme and keys with D11 (T8); today `--senza-firma` explicit and noted; the catalog's `sequenza` not yet used against going back to an old catalog; (3) TUI, GUI (D12, D13), `install.sh`, the answers file, the language in the answers file; (4) the **catalog texts** (reasons, notes, the table of §3.1) and the log's diagnostic details are Italian only; (5) BLOCCATA **after having touched** the machine (§6.6.3, last line) the engine keeps it **open** (one gets out with `riprendi` or `annulla`): §6.6.2 says "BLOCCATA: nothing has been touched" — the engine's choice, to be confirmed; (6) the name of the state file: the engine writes `/var/lib/remotix/installazione.json`, line B had proposed `installazione-confermata`; (7) R2 (known defects with the code) tested only on fake roots, not on the VMs | — | — | — |
| 165906c | **T3, line C — the `.rpm` package** (`packaging/rpm/remotix.spec`, ONE single spec with the branches `0%{?fedora}` / `0%{?rhel}` / `0%{?suse_version}` like `cockpit.spec`): `/usr/libexec/remotix/remotix`, `/usr/share/remotix/{pagina.html,remotix.conf}`, `remotix.service` (the same in substance as the `.deb`'s: root, `--nome %H`, `--journal`, `KillMode=mixed`, no bench options), `tmpfiles.d` (`/var/lib/remotix` 0700, `/run/remotix`); PAM `.fedora` in `/etc/pam.d/remotix` `%config(noreplace)`, `.suse` in **`%{_pam_vendordir}`** (`/usr/lib/pam.d`); `/etc/remotix/utenti-negati` (root) `%config(noreplace)`, `/etc/remotix/remotix.conf.d/` empty; KWin's permission identical byte for byte to `kwin.c`; certificates, `.nostro` marks, `ban` and `ban.nuovo` **`%ghost`** (the uninstallation removes them). **§10.12**: no `%systemd_post`/`%service_add_post` (they would apply the *preset*: with «enable \*» the service would enable itself), no groups, belts **off** in `/usr/share/remotix/cinture/`, firewalld only **defined** (`/usr/lib/firewalld/services/remotix.xml`); `%systemd_preun` and `%systemd_postun_with_restart` (*try-restart*) remain. **Dependencies**: the libraries are computed by rpmbuild (including `libssl.so.3(OPENSSL_3.5.0)`: OpenSSL's minimum need not be written); by hand only what rpm does not see, **conditioned on the desktop** (§10.7, no desktop pulled in): Fedora `(labwc if xfce4-session)`, `(xorg-x11-server-Xwayland if xfce4-session)`, `(labwc if lxqt-session)`, `(wlr-randr if lxqt-session)`, `(default-fonts-core-sans if labwc)`, `firewalld-filesystem`, Recommends `mesa-dri-drivers`, `(libva-intel-media-driver or intel-media-driver)`; openSUSE the same with `xwayland`, `((google-droid-fonts or dejavu-fonts or google-noto-sans-fonts or liberation-fonts) if labwc)` (labwc #2525), `(breeze6-wallpapers if plasma6-workspace)`, Recommends `Mesa-libva`, `intel-media-driver`; Alma nothing more (EPEL/CRB and RPM Fusion are steps of the engine). `Provides: bundled(ngtcp2) = 1.25.0`, `bundled(nghttp3) = 1.18.0` (D2 closed), checked in `%build` with `pkg-config`. The distribution's build flags in the **environment** (`CFLAGS ?=` of the Makefile: on make's command line they would override the `+=`); on openSUSE `-fPIE -pie`. **`src/remotix.pam.fedora`: `pam_selinux` close/open COMMENTED OUT — provisional, the decision belongs to T6** (§11.1 B). `costruisci-rpm.sh`: archive from the tree, `rpmbuild -ba` and rpmlint in the target's container, checks on the finished package (R4, R13 with the positive check, R14, XML of the firewalld service) | T3 (§6.1-§6.4): the native recipe for Fedora, Alma, Tumbleweed, Leap; §10.12 (inert pieces) | `[M]` 29 Sep: **4 out of 4 built** (`remotix-0.17.0-1.fc44`, `.el10`, TW, Leap); `ldd` 0 missing, ngtcp2/nghttp3 not dynamic; **R13** 0 bench phrases in the package, 1 in the positive check, no bench option in the unit; **R14** no bench file. **rpmlint** Fedora/Alma: 0 real E, 4 W `invalid-license` (licence not chosen), 2 `invalid-url` (local Source0), 2 `no-%check-section`, 1 `no-documentation`; 64-65 E `spelling-error` (Italian text). TW/Leap in addition: E `systemd-service-without-service_add_pre/post` (**intended**, §10.12), E `no-binary` (debugsource), W `dir-or-file-outside-snapshot` (TW), `unstripped-binary-or-object` (debuginfo), `strange-permission` (sources 664), `post-without-tmpfile-creation` (Leap: the macro there is empty); before the corrections also `position-independent-executable-suggested` (cured), `macro-in-comment`, `polkit-file-unauthorized` (gone with the belts off). Tests in VMs: §13.2 | yes, in the test VMs (then removed) |
| — | ⚠ **not done, noted by line C** (it touches the C or the engine): (1) like lines B and D, `kwin_scrivi_permesso()` (`kwin.c:48`, `:606`) must only **check** the package's file: `[M]` on TW the program finds it identical («c'e' gia'») and `rpm -V` stays clean, but if the binary changed path it would rewrite it; (2) the **session log** in `~/.local/state/remotix/sessione.log` stays in the user's home after the uninstallation (seen on 4 VMs out of 4): ✅ **decided on 1 Oct 2026: the engine removes it** (row 9991f09); (3) the people enrolled in the groups **by the product** at the first connection (`figlio.c`, `iscrivi_ai_gruppi_della_scheda`) go only to the journal: no log sees them, the uninstallation does not remove them; (4) **firewalld**: opening and then closing the service again leaves `/etc/firewalld/zones/public.xml` (+ `.old`), which was not there before (Fedora, Alma): the engine's rollback must remove it if it created it; (5) on Alma **RPM Fusion conflicts with EPEL** (`libavcodec-freeworld` 7.1.5 wants `libavcodec-free` ≥ 7.1.5, EPEL has 7.1.2): `--allowerasing` is needed, which removes `libavcodec-free` (REMOTIX stays satisfied by RPM Fusion's library); on Fedora `libavcodec-freeworld` **downgrades** the whole ffmpeg-free 8.1.2 → 8.0.1 (CON_FOTOGRAFIA): D5 must say it in the consent | — | — | — |
| 56c93d3 | **T4-T5, line A, second part — the real actions of §10.12 and the uninstallation.** `installa-pacchetti` (`gestore.go`, `azione_pacchetti.go`): Snapshot = ACQUISITION — the plan's file copied into the operation's cache and compared with its sha256, then the manager RESOLVES, DOWNLOADS and VERIFIES; the resolved set (name, version, origin, sha256, new/upgraded) goes into the intent and into `insieme-risolto-<azione>.json`; Do installs from the cache; halfway ⇒ the manager's remedy (`dpkg --configure -a`…) and it is redone; Undo removes ONLY the new packages, after a simulation that refuses if it would remove others (`RX-PACCHETTI-002`); the upgraded ones stay and are declared (INDIRETTA in the certificate). apt and dnf tested; zypper and pacman written, **not tested**. `aggiungi-deposito`: REMOTIX's signed archive (key in its own file, `Signed-By`/`gpgkey`, `rpm --import`; ESATTA) and EPEL (+CRB), RPM Fusion, Packman (AL_MEGLIO, D5 consent): the packages and keys that arrived with the repository are recognised (rpm before/after) and removed. `attiva-cintura` (the three of `/usr/share/remotix/cinture/` in `/etc`, D4 consent, logind reload over D-Bus). `accendi-servizio` (EnableUnitFiles + StartUnit; done only with the port listening TCP and UDP). `installa-desktop` (R38: the official groups from the catalog, our own `policy-rc.d` during the transaction on Debian, then the display manager enabled/started by the installation is turned off and the boot target goes back to how it was). **Uninstallation** (`disinstalla.go`): `remotix-install disinstalla [--purge]` makes a plan from the log of the confirmed installation — a `disfa` step for each DIRETTO step, backwards (doing = its undo; undoing = its do) — and, after the service is stopped, `chiudi-sessioni` (logind, ONLY `Service=remotix`, IRREVERSIBILE); at CONFERMATA it removes `installazione.json`. `piano --installa --pacchetto F [--utente] [--deposito] [--apri-firewall] [--senza-cinture]`: repositories → desktop if missing → packages → the card's groups (read from the nodes) → belts → firewall → service. **BLOCCATA** = only "nothing touched"; after having touched it is INTERROTTA (`RX-RIPRESA-001`). **7a**: `remotix --prova-codifica` (closed list) — today's binary does not have it (exit 2) ⇒ UNKNOWN, CONFERMATA_A_CONDIZIONI (`C-LIMITE`); PREFLIGHT reads the VA driver family from the packages (`h264.famiglia_driver`) | DECISIONI §10.7, §10.12, §10.14, §10.16; §6.0, §6.5-bis, §6.6.3-§6.6.6; R6, R28, R38, R43 | `[M]` 30 Sep. **go test: 160 PASS** (in addition: fake packages, belt and service in the test plan, with kills at every point; uninstallation killed at 6 points ⇒ CONFERMATA with the machine as it was except the declared INDIRETTA, the REMOTIX session closed and the ssh one alive; uninstallation rolled back ⇒ the installation comes back, ANNULLATA_IN_PARTE because of the IRREVERSIBILE closure; desktop without graphics). **debian13-gnome "cliente"** (`17-t4-motore.sh`, .deb 37a286e): verifica → piano (7 steps) → applica in **8 s: CONFERMATA_A_CONDIZIONI** — 11 packages at the resolved version, `prova` put in `render` (it was already in `video`: PREESISTENTE), 3 belts, service active with 7447 TCP+UDP, `installazione.json`; **Chrome PASS** (desktop gnome); then `disinstalla --purge` in **20 s: CONFERMATA** — 0 desktop processes (gnome-shell 0), **the clock of `prova`'s ssh session is still beating** (R43), `prova` again only in `video`, remotix and the 10 dependencies removed, no package changed. R6 against "before": DIRETTA left only the engine's history in `/var/lib/remotix/operazioni` (with the .deb in the cache); INDIRETTA `/etc/group-`/`gshadow-` (gpasswd's copies), times of the `/usr` folders, icon and mime caches; foreign CUPS and fwupd. **bare debian13** (R38, `DESKTOP=lxqt`): plan with the question about the desktop, answer lxqt ⇒ **1140 packages** + REMOTIX in 412 s, `sddm` installed but **disabled/inactive**, boot target unchanged, no `policy-rc.d` left; **Chrome PASS «desktop lxqt»**; uninstallation CONFERMATA in 296 s (the 1140 removed); what remains, AL_MEGLIO, are the system users and groups created by the package scripts (Debian-exim, colord, dnsmasq…). **alma10-gnome-iso** (`17-t4-alma.sh`, firewalld on with 7447 closed): EPEL+CRB repository, htop via dnf (3 packages), file, unit, **port via D-Bus**, then a group with a nonexistent user ⇒ **ANNULLATA**: rpm packages identical to before, firewall (runtime and permanent) identical; only `public.xml.old` (firewalld's copy), `ld.so.cache`, CUPS remain. The same plan with a real user ⇒ CONFERMATA, from outside `7447/tcp` and `/udp` open runtime AND permanent. Three discoveries for real, cured: (1) apt 3.0 with `--no-download` and a local .deb stops («Pathname to install is not absolute»): it installs without it, and "check" compares every version; (2) `epel-release` brings `selinux-policy-*-extra` and dnf imports two keys, and `dnf remove gpg-pubkey-…` exits 0 without removing them: now rpm before/after and `rpm -e` for the keys; (3) **TerminateSession is not enough**: the child's session is "closing" from birth (§5.2) and after 60 s the scope still has `remotix` and `gnome-session-binary`; the GNOME desktop lives in `user@1001.service`, NOT in the scope. With `KillSession` (SIGTERM after 10 s, SIGKILL after 20 s, always on that session alone) the leader dies and the desktop closes by itself | no |
| — | ⚠ **to do in the product** (line A, §6.5-bis): `remotix --prova-codifica [--nodo /dev/dri/renderDN]` — one H.264 frame encoded as in a session; **exit 0** and a line `PROVA-CODIFICA scheda <nodo> h264_vaapi` or `PROVA-CODIFICA software libx264`; **exit 1** if it does not encode; no network, no files written. Today the binary answers 2 (the help) and the engine declares it UNKNOWN. ⚠ **not done, noted by line A**: (1) zypper and pacman never tested on a real machine (T5, rounds on Tumbleweed and Arch); (2) `installa-desktop` dnf/zypper/pacman: the catalog's group names (`@^…`, `pattern:…`) not tested; (3) R29, and 7a/7b beyond encoding and port (libraries seen with a tenant's uid, PAM that refuses, TLS certificate); (4) the engine's history stays in `/var/lib/remotix/operazioni` after the uninstallation, with the package in the cache: keeping it (it is REMOTIX's "dnf history") or pruning it is to be decided; (5) on LXQt after the uninstallation 18 processes of `prova` remain in the user manager (the ssh session keeps it alive): to be looked at whether they belong to the closed desktop; (6) points (5) and (6) of the aec8402 row are closed (BLOCCATA → INTERROTTA; `installazione.json`) | — | — | — |
| (this commit) | **§6.5-bis, KDE's file**: `kwin_scrivi_permesso()` becomes `kwin_verifica_permesso()` (`kwin.c`, `kwin.h`, `main.c`): REMOTIX **no longer writes** `/usr/share/applications/org.kde.remotix.desktop`, it reads it with `GKeyFile` and checks that it is there (**RX-KDE-001**), that the first field of `Exec=`, made canonical with `realpath`, is the running binary (`/proc/self/exe` canonical, as KWin compares: `/usr/libexec/remotix/remotix` on deb and rpm, `/usr/lib/remotix/remotix` on Arch; **RX-KDE-002**) and that `X-KDE-Wayland-Interfaces` contains `zkde_screencast_unstable_v1` (**RX-KDE-003**); if not, a ⛔ line in the start-up log with the code and the remedy «reinstallare REMOTIX con l'installatore». **The bench**: `banchi/11-scatole/11-accendi.sh prodotto` puts the file itself in every box (like the package, which does not look at the desktop), same content as the package with `Exec=/opt/remotix/remotix`; copied on the server into `/media/REMOTIX/rete11/` and into the `controllo` copy | the file belongs to the package (identical byte for byte in `packaging/{debian,rpm,arch}`): rewriting it would give two truths about what is installed (`dpkg -V`, `rpm -V`); in the boxes nobody else put it there, and without the bench KDE would no longer have been seen | `[M]` 29 Sep, `kde` box, binary 60ce7d23: without the file ⇒ RX-KDE-001 and the file **stays absent** after start-up; `Exec=/usr/libexec/remotix/remotix` ⇒ RX-KDE-002; without the interfaces line ⇒ RX-KDE-003; with the bench's file ⇒ «verificato (e' del pacchetto: non lo scrivo)», date and size of the file **identical** before and after start-up. Short suite on the 4 boxes: **208 PASS / 0 FAIL / 0 BLOCKED** (f001 f003 f004 f011 f016 f018 f018b, Chrome and Firefox, 25 min, round `17-cure-6.5bis`), KDE included with the file put by the bench, zero-copy intact (CARD route 28-29 per box, MEMORY 0); then boxes back to 4fb3287d and PAM d1734958 (the old binary, with the bench's file, says «c'e' gia'»). 7 targets out of 7 compile without warnings | yes |
| (this commit) | **§6.5-bis, the groups at the first connection**: `figlio.c` `iscrivi_ai_gruppi_della_scheda()` notes every enrolment made by REMOTIX in **`/var/lib/remotix/gruppi-iscritti.jsonl`**, one line per group, **only** for the groups the user was not in (whoever was already there, even as primary group, is PREESISTENTE: neither enrolled nor noted). ⭐ **The format, for the engine's line** (UTF-8, one JSON line per line, `\n` at the end, strings with JSON escaping of `"`, `\` and the control characters): `{"formato":"remotix-gruppi/1","data":"2026-09-29T20:28:19Z","utente":"c18u752","uid":4013,"gruppo":"render","gid":991,"origine":"DIRETTA","da":"REMOTIX alla prima connessione"}` — `data` in UTC ISO 8601 to the second, `uid`/`gid` numbers at the moment of enrolment. **Writing**: folder opened with `O_DIRECTORY\|O_NOFOLLOW`, it must belong to root and not be writable by others (if missing it is created 0700); file with `O_WRONLY\|O_APPEND\|O_NOFOLLOW` (born with `O_CREAT\|O_EXCL`, 0600, and then `fsync` of the folder), it must be regular, root's, not writable by others; each line with **one** `write` and then `fsync`; never truncated or rewritten. The file is opened **before** `usermod`, the line is written **after** and only if `usermod` succeeded (an enrolment never made but noted would get a group put by others removed). If it cannot be noted, the enrolment is done anyway (a blind session is worse, §4.2) and the log says ⛔ «iscrizione NON ANNOTATA» with the remedy `gpasswd -d`. The engine at uninstallation: for each line, if the user is still in the group, it removes them (DIRETTA); repeated lines for the same pair count as one | the uninstallation must know whom REMOTIX put in a group (DIRETTA, removed) and who was there (PREESISTENTE, never) — §6.6.4, R33; the journal rotates and the engine does not read it | `[M]` 29 Sep, `xfce` box, `11-accendi.sh c18 xfce`: G SI · I SI · D SI (VERDE); before, `/var/lib/remotix` was not there, after it a folder `drwx------ root` and a file `-rw------- root` with **2 lines** (render gid 991, video gid 44) and two lines «⭐ annotato in …» in the log; the file removed at the end of the test | yes |
| (this commit) | **§6.5-bis, the encoding test for the certification (phase 7a)**: `remotix --prova-codifica` (alone, first argument; `figlio_prova_codifica()` in `figlio.c`): it goes through **`codificatore_di()`**, the route of a real session — H.264, 8 bit (the base of §4.3), no level cap, BGRx: `h264_vaapi` on `NODO_RENDERING` (`/dev/dri/renderD128`) with `POTENZA_RENDERING` and `QP_HARDWARE`, if it does not open the `libx264` fallback with `CRF_SOFTWARE` — and really encodes a synthetic 256×256 frame (at most 8 rounds until bytes come out). ⭐ **The contract**: ONE JSON line on stdout (the log stays on stderr) `{"esito":"hardware"\|"software"\|"nessuno","codificatore":"h264_vaapi"\|"libx264"\|"","nodo":"/dev/dri/renderD128"\|"","motivo":"…"}`; exit code **0 if a frame came out (hardware or software: which one is said by `esito`) · 1 none** (2 stays the usage error) — the same code the engine of line A expected (row of 56c93d3); ⚠ **the line however is JSON, not `PROVA-CODIFICA …`**, and `--nodo` is not there (the node is the session's): `operazione.go` `provaCodifica` must be adapted by the engine's line. `nodo` is filled only with "hardware"; with "software" the reason carries the node tried and why the hardware did not open. ⛔ "hardware" only if the component accepts VA-API surfaces **and** a frame came out with bytes **and** the bytes were read back (`letto_dal_flusso`); every other uncertainty is "nessuno" with the reason. No network, no sessions, no certificates; **root is not needed**, but the outcome depends on the identity: whoever is not in the node's group sees "software" where root sees "hardware" — the test is done with the identity one wants to know about. `codificatore_di()` now keeps the reason of the two refusals (`rifiuto_hardware`, `rifiuto_software`) for the reason field | the installer must prove that the machine encodes, and how, with the product's choice and not with a separate ffmpeg (§6.0, and note (1) of line A: ffmpeg is not in the closed list) | `[M]` 29 Sep: VM `debian13-gnome` "cliente" (virtio-gpu) as a user and as root ⇒ `software`, `libx264`, 5313 bytes, `avc1.641015` (reasons: «Invalid argument» as a user, «Input/output error» as root); in the 4 boxes (Intel iHD 25.2.3), as root and as `provanic` (video, render) ⇒ `hardware`, `h264_vaapi`, `/dev/dri/renderD128`, 1619 bytes, `avc1.640c15`, EncSliceLP — these with the first numbering of the codes (3/4), the JSON line is the same. With the final binary 2db2df13: `debian13` container ⇒ `software`, code **0**; `fedora44` container (ffmpeg-free, without libx264) ⇒ `nessuno`, code **1**, «il codificatore «libx264» non c'e' in questa libavcodec»; the 4 boxes as root ⇒ `hardware`, code **0**. 7 targets out of 7 compile without warnings (Ubuntu 24.04 out, D7: the image is not born, OpenSSL 3.0) | yes |
| ad5bc1b | **T5, line A — the desktop really closed, the history, zypper and pacman.** `chiudi-sessioni` (§10.16): after the logind sessions `Service=remotix`, the engine talks to the **user manager** on its private D-Bus (`/run/user/UID/systemd/private`, open to root) and stops `graphical-session.target` and the units that have processes born in the desktop (recognised by the environment: `WAYLAND_DISPLAY`/`DISPLAY`; the session bus is not stopped, only its graphical processes are reported), removes the two variables from the manager's environment; only if the person does not have another desktop (a non-REMOTIX `wayland`/`x11` session); never `user@UID`, never TerminateUser. **History**: `disinstalla` keeps it without the package caches, `--purge` removes all of it (and `gruppi-iscritti.jsonl`). **`togli-iscrizione`**: REMOTIX's enrolments at the first connection (`/var/lib/remotix/gruppi-iscritti.jsonl`, §6.5-bis) are removed as DIRETTA, duplicates once. **`provaCodifica`** on the JSON contract of `remotix --prova-codifica` (hardware ⇒ PASS; software ⇒ PASS + `C-RIPIEGO`; nessuno ⇒ FAIL; unreadable ⇒ UNKNOWN). **zypper**: `--from packman --allow-vendor-change` for libavcodec (step `codec` after the repository, from the catalog: `pacchetti_codec`); `--allow-unsigned-rpm` for the plan's file ONLY (verified by its sha256; the signed archive is T8). **dnf**: the plan's file in a transaction of its own (the dependencies stay with `localpkg_gpgcheck=1`). **pacman**: the resolved set from `pacman -U/-S --print` (before, it took only the file, and the uninstallation left remotix). The installation plan adds the `C-COMPONENTE` of the installed desktops (`breeze6-wallpapers`, labwc, a font) | DECISIONI §10.16, §6.5-bis; the coordinator's request (30 Sep) | `[M]` 30 Sep, go test 161 PASS. **debian13-gnome** (.deb 5cbb97d with the new product): CONFERMATA_A_CONDIZIONI in 8 s, `--prova-codifica` ⇒ `software libx264` (VM without VA-API) ⇒ PASS + C-RIPIEGO; Chrome PASS; uninstallation in 21 s: processes of `prova` **69 → 8** (systemd, sd-pam, pipewire-pulse, gcr-ssh-agent, ssh-agent: born without graphics; and the ssh session), **0 graphical processes**, the ssh clock beats. **debian13-lxqt**: 37 → 7 (systemd, sd-pam, pulseaudio, dbus-daemon, ssh), 0 graphical, clock alive. **tumbleweed-kde** (`--deposito packman`, T3's .rpm): Packman + `libavcodec63` from Packman (7 packages, vendor change) + remotix + `breeze6-wallpapers` ⇒ CONFERMATA_A_CONDIZIONI in 15 s; Chrome PASS «desktop kde»; uninstallation CONFERMATA in 19 s, 30 → 9 processes, 0 graphical; R6 against "before": **no package different**, what remains is Packman's key (now removed too: `rpm -e`, not retested), `/etc/group-` and the desktop's files in `/home/prova`. Before the cure the unsigned .rpm file was refused by zypper («File is unsigned») and the operation was ROLLED BACK cleanly (Packman and codec removed). **arch-kde** (T3's .pkg.tar.zst): resolved set 9 packages, CONFERMATA_A_CONDIZIONI in 3 s, Chrome PASS «desktop kde», uninstallation CONFERMATA, 43 → 9 processes; R6: **no package different**; what remains is the system group `seat` (seatd's sysusers: INDIRETTA, pacman does not remove it), a KDE system D-Bus service (`kameleon`) started by the desktop, the files in `/home/prova`. **The desktops' groups** (`prove/gruppi-desktop.sh`, containers): all the catalog's names resolved (Fedora 4 environments, Alma 2, Tumbleweed 4 patterns, Arch 6 groups); Alma's dnf 4 **does not understand `@^`**: now `@<ambiente>` for all | no |
| 97918d0, 4dcaa70 | **T5, line A — closure.** **`certifica`** (and the verification of the installation): besides the "check" of every step, `codifica-h264` (REMOTIX itself), `pam-risolta` (REMOTIX's stack resolves: files, `@include`/`include`/`substack`, modules; ⚠ static, not "refuses a nonexistent user": that would need PAM loaded, that is a new request to REMOTIX), `porta-firewall` (firewalld: 7447 TCP+UDP; closed ⇒ non-required FAIL + `C-AMMINISTRATORE` with the command; ufw/nftables ⇒ UNKNOWN); outcome VERDE only if everything PASS and no condition. **The pieces of the desktop installed by the engine** (R38) enter the plan (`componenti-desktop`: labwc, wlr-randr, breeze6-wallpapers, the scalable font). **dnf5**: the set from the table of `install --assumeno` (install/upgrade/downgrade, never «Skipping packages with conflicts»), `dnf download` into the step's folder and only those files; `rpm -qp` with a marker (the NOKEY warnings broke the parsing); **the repository keys** (EPEL, RPM Fusion) imported into rpm at once and removed at rollback | R29, R38, T5 | `[M]` 30 Sep, **go test 175 PASS** (R29 in small: 10 broken machines — card that does not encode, PAM without module/include/file, port closed again, firewall unreadable, a step undone — never VERDE; installation with the card that does not encode ⇒ ANNULLATA). **R29 for real, debian13-gnome**: healthy ⇒ A_CONDIZIONI (software fallback in the VM); PAM with a module that does not exist ⇒ **ROSSO**; libx264 removed ⇒ the binary does not start ⇒ UNKNOWN ⇒ A_CONDIZIONI; service stopped by others ⇒ **ROSSO**; put back in order ⇒ A_CONDIZIONI again; **fedora44-gnome without `--apri-firewall`**: `porta-firewall FAIL`, A_CONDIZIONI, and Chrome really does not get in (ERR_TIMED_OUT). **The seven families, complete round** (`17-t4-motore.sh`: "cliente" snapshot, the package of line B/C/D, verifica → piano → approva → applica, certifica, real Chrome, ssh session with the clock, `disinstalla --purge`, fingerprint before/after): <br>• **Debian 13** (gnome, lxqt): installs 8 s, uninstalls 19-22 s; leftovers: `/etc/group-`/`gshadow-` (gpasswd's copies), folder times, icon/mime caches, CUPS/fwupd (foreign) <br>• **Ubuntu 26.04** (gnome, + `gnome-session`, D8): 16 s / 27 s; leftovers like Debian <br>• **Fedora 44** (gnome, RPM Fusion + `libavcodec-freeworld`, `--apri-firewall`): 14 s / 20 s; leftovers: the `ffmpeg-free` family **downgraded** from 8.1.2 to 8.0.1 to match RPM Fusion (INDIRETTA, it stays: declared), firewalld's `public.xml` rewritten identical, CUPS <br>• **Alma 10** (gnome, EPEL + RPM Fusion): 30 s / 31 s; **no package different**; leftovers: `public.xml`, tuned, CUPS <br>• **Arch** (kde): 3 s / 16 s; no package different; leftovers: the system group `seat` (seatd's sysusers), a KDE D-Bus service <br>• **Tumbleweed** (kde, Packman + libavcodec63 changing vendor + breeze6-wallpapers): 15 s / 19 s; no package different <br>• **Leap 16** (xfce, Packman + libavcodec61 + labwc, wlr-randr): 30 s / 25 s; no package different, **not even Packman's key** (now removed: point (3) retested) <br>In all of them: Chrome gets in and sees the right desktop; after the uninstallation **0 desktop processes** in the user manager and the ssh clock alive (R43); everywhere the files the desktop wrote in `/home/prova` remain | no |
| 700cc1b | **T7 — the new parent finds the live desktops again** (`src/ritrovo.c`/`.h`, `main.c`, `figlio.c`). **The criterion**, one for the four desktops: logind session with the PAM service `remotix` (in any state: after birth it is "closing", §5.2) and, in its scope, a process of the user **leader of its own process session** (pid = sid) with the parent **outside** the scope — the signature of `setsid --fork` (`avvia()`); read from logind on the system bus and from `/proc`, no user bus and no files from the child (the desktops born with the **old** binary would not have them). **At start-up**, before "ready": one line per desktop («RITROVATO il desktop di «u» … sessione logind cN, palco pid P «comm»») and a count line (how many, stages over cap, clock). **In the counts**: cap = children + found; the budget includes them; the **abandonment clock restarts from the new parent's start-up** (declared: the last gesture seen by the previous parent was in its memory). **On reattach** `SESSIONE` says RIPRESA, the new child (D1 unchanged) takes up the same compositor and the user moves from the found ones to the children; no renewal of the clock. **Recheck** every 10 s, only if there are any: a found one that died by itself leaves the counts. **Abandonment** of a found one: a child is born that closes it (`sessione_termina()`, only it can do that from the user bus). **`loginctl terminate-user`** (enrolment in the groups at the first connection) **is not issued** if the user has a live REMOTIX desktop, nor if logind cannot tell: it is written, and the groups arrive at the next birth of the desktop | §5.2, §6.5-bis, R7-R9 | `[M]` 30 Sep, `banchi/17-t7/`, Intel boxes, binary 36cd767c (debian13), **two complete rounds** (the second with the final binary). Per desktop two tests, two users together (real Firefox and Chrome, 4K), three time witnesses (real terminal, the session's scope, `user@`): **update** (desktops born with 4fb3287d and PAM d1734958, then new binary + the product's PAM and restart with `--tetto-sessioni 2`) and **restart** (desktops born with the new one; for the second user `video`/`render` removed beforehand). **gnome, kde, xfce, lxqt, 8 tests out of 8**: the new parent declares **2 found** (R9); a **third user stays out** with 0x0E «palchi 2 su 2 (0 coi figli, 2 ritrovati)» (with the previous code they got in: children=0); each one goes back into **their own** desktop (same stage pid, line «RIENTRA … palco pid P» identical to the one before), terminal and windows in their place in the screenshots (R7); **0 desktop processes lost**, witnesses with the longest gap **1.0 s** (that is, none); guard: «iscritto a render,video, ma il gestore d'utente NON si fa rinascere: ha un desktop REMOTIX VIVO», desktop alive. **The four times of R8**: (a) service down **4.3-4.4 s** (from the stop to the "ready" of the new parent, with the box's restart: stop + systemd-run); (b) desktop alive: **0** processes lost; (c) session found again **35-76 ms** after the new parent's start-up (4.3-4.4 s from the stop); (d) the browser with the image again **3.9-4.3 s** from the reloaded tab (8.8-9.3 s from the stop). **Abandonment** (gnome, `--abbandono-s 60`): found → at 60.1 s the child is born, «Logout 1», session exited, child exits; afterwards: 0 processes of the user, 0 `remotix` sessions. **Short suite** with the cured binary (f001 f003 f004 f011 f016 f018 + f021, chrome and firefox, 4 boxes): **224 PASS / 0 FAIL / 0 BLOCKED** (first round without f021: 208 PASS). **Compiles 7/7** (`costruisci-tutti.sh`; ubuntu2404 out for D7, image as before). ⚠ Not done, noted: a child that dies with the parent alive leaves its desktop outside the counts as before (the found ones are looked for only at start-up) | no |
| 307d042 | `figlio.c`: once the session is closed on request (§7.6 or abandonment) **the child exits** | the child that **opens** the desktop drives its logind session and the logout takes it away; the one that **takes up** a found desktop is in a session of its own: `[M]` it stayed alive and 0.6 s after «Logout 1» it made an unrequested desktop **be reborn** | `[M]` 30 Sep: abandonment on a found one ⇒ «esco anch'io», 0 processes afterwards; f021 (Exit) 16 PASS on 4 boxes × 2 browsers | no |
| 6773a66 + (this commit) | **T8 — chain A in the engine** (`motore/firma.go`, `fiducia.go`, `installatore/chiavi/`, `strumenti/chiavi-a`). An **offline** ed25519 root (its public key written in the engine) which certifies **subkeys with a period** (A-2026: 30 Sep 2026 → 29 Sep 2027); the subkey signs catalog and engine in a separate `.firma` file (`remotix-firma/1`: chain, object, sha256, certificate inside); the **revocations** are signed only by the root. **TRUST**: the offline catalog given by hand (`--catalogo FILE`, signature in `FILE.firma`) is the only one looked at; otherwise embedded + stored (`/var/lib/remotix/fiducia/`) + archive (`<archivio>/catalogo/<canale>/`), the highest **sequence** wins, then fresh (expiry, minimum engine). A wrong signature from any source ⇒ **BLOCCATA**; only embedded/stored ones signed by a subkey later revoked or expired are discarded (that is the rotation). New codes RX-TRUST-006…016; 001 and 005 **retired** (`--senza-firma` no longer exists). **The archive on the machine** (`archivio.go`): apt deb822 `Signed-By: /usr/share/keyrings/remotix-archive-keyring.asc` + **pin** `origin "<host>"` −1 for everything except the three REMOTIX packages; dnf `gpgcheck`, `repo_gpgcheck`, `includepkgs`; pacman a `[remotix]` block between two markers in `/etc/pacman.conf` (SigLevel Required DatabaseRequired) and the key in `pacman-key` (`pacman-key` and `apt-cache` enter the closed list). `piano --installa --archivio URL [--canale]` installs `remotix`, `remotix-install` (and on apt `remotix-archive-keyring`) **from the package manager** and turns on `remotix-aggiorna.timer` with consent. **`aggiorna`** (`aggiorna.go`, `aggiorna_gestori.go`): refreshes ONLY REMOTIX's archive (apt with a SourceParts of its own, `dnf --repo=remotix`, pacman with a configuration with only `[remotix]`: no partial upgrade), chooses according to `aggiornamenti.conf` (D14), and makes an "update" **operation** (step `aggiorna-pacchetti`: exact versions, undo = the previous versions from the archive) — never files replaced by the engine. **`ritorna --versione V`** (R11): apt `nome=versione --allow-downgrades`, `dnf downgrade` of the verified files, `pacman -U` from the cache or from the archive (`remotix.versioni`); after a rollback the timer does not put back by itself the version left (RX-AGG-011). `installazione.json` stays the installation's; the updated versions in `aggiornamenti.json` (the installation's "check" accepts them, `certifica` green after an update) | fasi/17 §6.5 p.5-6, §6.6.10, DECISIONI §10.10 | `[M]` 30 Sep, `go test` green (chain A: each refusal with its code, the rotation, the dpkg/rpmvercmp versions, the pacman.conf block). **On the VMs** (evidence `/media/REMOTIX/vm17/t8/esiti/`): installation from the archive CONFERMATA_A_CONDIZIONI on debian13-gnome (9 steps), fedora44-gnome (11, with RPM Fusion), arch-kde; **R39** 3/3: the timer finds the maintenance N+1 and applies it with a Chrome connected — gnome-shell/kwin **same pid** before and after, «RITROVATO il desktop», browser back in within 8.8 s; catalog 5 (one more Debian version) stored by the same round; the **annual** 0.18.0 only notified (RX-AGG-003), applied with `--annuale`; **R11** N+1→N on apt, dnf (downgrade) and pacman (-U from the archive, then from the cache), desktop always the same; **chain A** 8/8 BLOCCATA (catalog byte ⇒ 007, expired ⇒ 002, revoked subkey ⇒ 010, offline expired ⇒ 002; versions unchanged); the rotation (revocations 2 + catalog signed A-2027) accepted. ⚠ **Found by phase 0**: the engine's `.rpm` 0.1.0-1 had gone through rpm's strip and **no longer matched its signature** ⇒ RX-TRUST-014, the timer stopped; cured in the spec (empty `__os_install_post`), 0.1.0-2 installed by hand with the manager | yes (packages from the test archive) |
| (this commit) | ⚠ **limits declared, not done** (T8): (1) rpm and pacman do not tie a key to a repository (`rpm --import`, `pacman-key --lsign-key` hold for every package): R18 holds in full only on apt; on dnf `includepkgs` prevents taking anything else from our archive, on pacman nothing (the archive contains only ours); (2) on apt an explicit `nome=versione` by the administrator overrides the −1 pin (`[M]` `hello=99.0-1` would install): never by itself; (3) a **revoked** subkey that had signed the package's engine stops it (RX-TRUST-014) until a `remotix-install` re-signed with the new subkey arrives: the ordinary rotation must be published **before** the expiry (§6.6.10); (4) the ngtcp2/nghttp3 version in the SBOM comes from the pkg-config of the linked `.a` files (`incorporate.json`, checked against Static-Built-Using/bundled()), not from the binary: reading it from the binary is one line in the product (`ngtcp2_version()` in the start-up log), requested by §6.5-bis, not done; (5) zypper (openSUSE) does not have the updater yet; (6) R23 on the archive metadata not measured; (7) the catalog does not yet have a default archive address (D10) | — | — | — |
| c7773c5 | **T9 — without questions and without network** (`motore/risposte.go`, `fuorilinea.go`, `cmd/remotix-install/senza_domande.go`, `install.sh`; §6.6.12). **The answers file** `remotix-risposte/1` → `PianoDaRisposte`: the plan's options from the file; the consents needed **on that machine** (belts always; firewall only with firewalld; D5 only where H.264 or the desktop ask for them; updates only from the archive) are either given or noted among the `mancanti` ⇒ `Applica` BLOCCATA with **RX-RISPOSTE-001** (a new step of phase 4, before the approval); unknown entry RX-RISPOSTE-002, value RX-RISPOSTE-003; the plan carries `risposte` (file, sha256, entries, defaulted, superfluous, missing) and is approved "from the file". **`installa`**: plan in `/var/lib/remotix/piani/`, then `Applica`; without `--risposte` a confirmation at the terminal (without a terminal it stops). **The offline bundle**: `prepara-fuori-linea` (apt: the machine's sources + the archive in a temporary configuration, `--print-uris` and `--download-only`, the indexes and the InRelease taken from the lists just verified, the `.deb` files in their place in the pool with their hash against the index; dnf: the transaction of each step **cumulative**, `dnf download` per step, REMOTIX's repodata and `repomd.xml.asc`; RPM Fusion: the release and its repositories only for resolving), manifest with binding fingerprint + **all** the installed packages + every file with its sha256; **on the machine without network** a wrapped manager (`gestoreFuoriLinea`): apt with the bundle's `SourceList`, `target=Packages`, `By-Hash=no`, lists in the operation's cache; dnf from the files with `--disablerepo=*` and `localpkg_gpgcheck=1`; the RPM Fusion step installs the release from the bundle; checks RX-FUORI-001 (integrity) and 002 (different machine) in phase 3. `fiducia.go` reads `file://`; `ParametriArchivio` accepts `file:///…`; for a local archive apt's pin is `release o=REMOTIX` (a local repository has no host) and dnf has `includepkgs`. **`install.sh`** (§6.6.12). **PREFLIGHT cure** (`preflight.go` `depositi`): a repository counts only if a **section** with its name is **enabled**; for RPM Fusion "rpmfusion-free" counts | `[M]` fedora44-gnome: `fedora-workstation-repositories` brings `rpmfusion-nonfree-steam` DISABLED and the word was enough ⇒ "RPM Fusion present", no C-DEPOSITO, no consent, and without network the certification rolled back (codifica-h264 FAIL: without RPM Fusion Fedora has neither VA-API H.264 nor libx264). The rest: §6.0 rule 3, §6.5 point 10, R21, R22, R31 | `[M]` 30 Sep: Go tests green (TestLeggiRisposte, TestConsensiNecessari, TestRisposteBloccate, TestDepositiAccesi, TestScriptRadice). **R31** (debian13-gnome, connected): plan from the file, approved from the file; `nicfio` put in `video` ⇒ **BLOCCATA RX-PIANO-001** («gruppo.video membri= … adesso nicfio»), nothing touched; same snapshot, machine restarted ⇒ **CONFERMATA_A_CONDIZIONI** and Chrome in (GNOME, `PASS`). **R22 debian13-gnome**: bundle 71 MB, 13 artefacts (9 from the distribution: labwc, wlroots 0.18…); network removed (`restrict=on`, archive unreachable); one byte in a `.deb` ⇒ RX-FUORI-001; the same `.deb` altered **with the manifest adjusted** ⇒ apt refuses it against the signed index («Hashes of received file»), **ANNULLATA**, sources as they were; `nano` removed ⇒ **BLOCCATA RX-FUORI-002** («solo nel pacchetto: nano=8.4-1+deb13u1»); clean ⇒ **CONFERMATA_A_CONDIZIONI in 10 s**, capture: **0 attempts outwards** in the installation window (only mDNS and IPv6 neighbour traffic); network given back, Chrome in. **R22 fedora44-gnome**: 35 MB, 14 artefacts (RPM Fusion and 11 from the distribution: ffmpeg-free 8.0.1-6 upgraded, x264-libs…); without network **CONFERMATA_A_CONDIZIONI in 9 s**, 0 attempts outwards; Chrome in. **R21**: cloud-init on debian13-gnome (new seed, `curl install.sh \| sh`, nobody in front) ⇒ signature VERIFIED, **CONFERMATA_A_CONDIZIONI**, cloud-init finished in 22 s, Chrome in; with `risposte-manca.conf` ⇒ **BLOCCATA RX-RISPOSTE-001** (consenso.cinture), nothing touched. **install.sh**: `--verifica` as a user, `--dry-run` (plan, nothing touched), engine with one extra byte ⇒ RX-TRUST-007, signature of another object ⇒ RX-TRUST-006/007, its "script" signature valid | yes (engine) |
| (this commit) | ⚠ **not done, noted** (T9): (1) the archive's `remotix-install` package (0.1.0-3) has T8's engine: with a **local** archive its `certifica` gives FAIL on the repository file (it does not know about `includepkgs` for `file:`), `[M]` fedora44-gnome; it must be rebuilt with T9's engine (0.1.0-4) before the release; (2) zypper and pacman offline (RX-FUORI-004), Packman and EPEL in the bundle (RX-FUORI-005); (3) the terminal confirmation of `installa` without `--risposte` is a line of text, not the TUI (D12); (4) in the VM with `restrict=on` QUIC does not pass (6 datagrams in, 3 out): the browser gets in only with the network given back (restart without `restrict`, disk unchanged) | — | — | — |
| b2ddbbd | **T6 — PAM like sshd** (D3, DECISIONI §10.18): `src/remotix.pam*` line by line like `/etc/pam.d/sshd` (`/usr/lib/pam.d/sshd` on openSUSE) plus the root line. Debian/Ubuntu move from `common-session-noninteractive` + `pam_systemd` by name to `common-session` (which brings it) with `pam_motd`, `pam_mail`, `pam_limits`, `pam_env`, `pam_loginuid` **required**; Fedora/Alma **`pam_selinux close/open` put back**, `pam_sepermit` in account, `pam_namespace`, `pam_motd`; openSUSE `common-session` (no longer `-nonlogin`) and the `postlogin-*`. `provisiona.sh` checks that the file reaches `pam_systemd` also through `common-session` | D3: *«deve rispecchiare PAM»*; and `pam_loginuid` `required` like sshd (the service starts from systemd, without loginuid) | `[M]` 30 Sep, comparison with the "iso" VMs; R20 below | yes (the packages) |
| b2ddbbd | **T6 — the SELinux module** `packaging/rpm/selinux/` (`remotix.te/.fc/.if`, `remotix_porta.cil`), subpackage **`remotix-selinux`** (noarch, `%selinux_modules_install`, relabel in `%posttrans`; `remotix` asks for it with `(remotix-selinux if selinux-policy-targeted)`). Types: `remotix_t` (service), `remotix_exec_t`, `remotix_port_t` (7447 tcp+udp, `portcon` in CIL), `remotix_var_lib_t`, `remotix_var_run_t`. Rules: `auth_login_pgm_domain` (the same as sshd and `cockpit_session_t`), logind over D-Bus, `userdom_spec_domtrans_all_users` + `unconfined_domtrans` + **entrypoint of the user domains on `remotix_exec_t`** (the child re-executes itself), `init_ranged_daemon_domain … s0 - mcs_systemhigh` like sshd, `dev_rw_dri`, signals to the stages; two measured `dontaudit` (sd-journal's `net_admin`, `cap_userns sys_ptrace` of the finder that walks /proc). `remotix.service` (rpm) launches the program **without `/bin/sh -c`** (or the service would stay `unconfined_service_t`) | §11.1 B: `pam_selinux open` + unconfined service ⇒ the child exits with 37 | `[M]` the rules from the domain in *permissive* with `semodule -DB`, a whole session (new, resumed, service restarted with the desktop alive, wrong password, root): found `{ entrypoint } unconfined_t → remotix_exec_t`, `{ getattr } init_t` (in Fedora `init_ranged_daemon_domain` no longer calls `init_daemon_domain`), `{ signal } → unconfined_t`, `net_admin`, `sys_ptrace`; then **enforcing: 0 denials** on fedora44-gnome-iso, alma10-gnome-iso, alma10-gnome, tumbleweed-kde-iso, leap16-xfce (service `remotix_t:s0-s0:c0.c1023`, stage `unconfined_t` like whoever gets in with ssh; on Leap the stage is born `unconfined_t:s0`). ⚠ On Fedora/Alma the denials are in audit.log (Alma) or only in the journal (Fedora, no auditd): the bench reads both | yes |
| 75c28de, 95f86d7 | **T6 — the engine**: `installa-pacchetti` with several files in ONE transaction (`--pacchetto a.rpm,b.rpm`); `regola-firewall` with the **`remotix` service** if firewalld (or ufw) already knows it, **the ports** otherwise (the form written in the previous state), permanent rules in **one** write (`update2`), at rollback the **default zone put back to default** (`loadDefaults`) and the `<zona>.xml.old` that loadDefaults leaves removed if it was born from us; **ufw** with its own program (it enters the closed list: no D-Bus), rule `ufw allow REMOTIX` from the `.deb`'s profile (`/etc/ufw/applications.d/remotix`); RX-FW-004 only for nftables; RX-PAM-002 says "as for ssh" | D6; "the public.xml leftover" of the T4-T5 rows | `[M]` firewalld 2.4 **does not see a new service without a reload** (`INVALID_SERVICE`, runtime and permanent) and the engine does not reload (it would throw away podman/libvirt's runtime rules) ⇒ at the first installation the ports. **alma10-gnome "cliente"** (default zone): after the uninstallation `/etc/firewalld/zones` empty as it was (before the cure: `public.xml.old` stayed, loadDefaults renames). **alma10/tumbleweed "iso"** (zone already in /etc): `public.xml` identical byte for byte (sha256), ⚠ **`public.xml.old` stays changed**, the copy firewalld makes by itself before every write: it cannot be avoided with firewalld's interface. **fedora44-gnome-iso**: 1025-65535 already open ⇒ nothing touched. **ubuntu2604-gnome-iso** with ufw on: `REMOTIX ALLOW` (v4 and v6) after, gone after the uninstallation. Tests `firewall_test.go` | yes (engine) |
| (this commit) | ⚠ **seen in T6, not cured**: (1) the helper does not pass `PAM_RHOST` to authentication (sshd does, the client's address): `faillock` records «SVC remotix» instead of the address, and `pam_access` does not have the host; (2) **leap16-kde**: the Plasma session is not born (`nessun KWin sul bus`), **even with SELinux in permissive** ⇒ it does not belong to T6, it had never been tested (T3-T5 on leap16-xfce); (3) on leap16-kde the uninstallation rolls back: `disfa-codec` would remove `kdialog` (RX-PACCHETTI-002) | for whoever takes them up | `[M]` 30 Sep | — |
| 7583b76 | **D8 — the distribution's default GNOME session** (`sessione.c` `sessione_gnome()`, `unita_shell()`, `scrivi_dropin()`, clear-out; `sessione.h`; `packaging/debian/{control,rules}`). **The criterion, one for all**: candidates = `<dati di sistema>/wayland-sessions/*.desktop` whose `Exec` launches `gnome-session` (name from `--session`, without it = `gnome`) **and** with `gnome-session/sessions/<nome>.session` installed; only one ⇒ that one; more than one ⇒ the one whose name = os-release's `ID`, then `gnome`, then the first in order (GDM's upstream rule; Ubuntu corrects it by hand in its gdm3, «Prefer ubuntu session as fallback», and here the same is obtained without naming it); none ⇒ **declared fallback** to `gnome`. Start line = the `Exec` quoted argument by argument; `XDG_CURRENT_DESKTOP` from `DesktopNames`, `XDG_SESSION_DESKTOP` from the file name; manager `gnome-session-manager@<sessione>.service`. **GNOME 50**: the Shell instance is asked for by the SESSION (`Requires` of `gnome-session@<sessione>.target`: `@user` for `gnome`, `@ubuntu` for `ubuntu`), no longer a fixed `@user`; the drop-in keeps **`--mode=%i`** (the `ubuntu` mode brings dock, Yaru, extensions); the clear-out looks for every `org.gnome.Shell@*.service.d` (never the template's); `GNOME_SHELL_SESSION_MODE` among the variables put back as they were. **.deb**: removed the Ubuntu-only recommendation `gnome-session \| plasma-workspace \| …` (`${remotix:Recommends}`). ⚠ **To be aligned in the engine** (another agent, `installatore/`, not touched): Ubuntu's `catalogo/catalogo.json`, `desktop.gnome.componenti: ["gnome-session"]` and the note "D8 open" must be removed; and `banchi/17-distro/17-t1c-installa.sh:61` still installs `gnome-session` on Ubuntu | the user's D8 (DECISIONI §10.20): on Ubuntu whoever connects sees Ubuntu's desktop, the one on the monitor; no exceptions per distribution. `[M]` 30 Sep: on Ubuntu 26.04 the `ubuntu` session asks for `org.gnome.Shell@ubuntu.service` (`gnome-session@ubuntu.target.d/ubuntu.session.conf`) and the mode is in the instance (`ExecStart=gnome-shell --mode=%i`): with the previous code the drop-in ended up on `@user` and the Shell would have been born without `--headless` | `[M]` 30 Sep: build 7/8 (ubuntu2404 does not make the image: OpenSSL 3.0, already known §11.1). **ubuntu2604-gnome** "cliente", .deb **without** gnome-session (`un gnome-session`), engine steps by hand: Chrome PASS, log «D8: «ubuntu» (ubuntu.desktop): l'unica che la macchina propone · XDG_CURRENT_DESKTOP=ubuntu:GNOME», process `gnome-shell --headless --no-x11 --mode=ubuntu`; **screenshot looked at**: Ubuntu's dock on the left, 26.04 purple wallpaper, orange Home folder (ding), black bar. **debian13-gnome**: PASS, «gnome» among `gnome`/`gnome-wayland` (same session), `@wayland` without `--mode`; screenshot: GNOME Adwaita, Debian's welcome. **fedora44-gnome** (.rpm 0.17.0-1): «gnome» between `gnome` and `gnome-classic` (rule "gnome"), `--mode=user`; without RPM Fusion it gets in and does not paint (cause C §11.1, known), with `libavcodec-freeworld` PASS; screenshot: GNOME Adwaita, Fedora's welcome. **Short suite** GNOME box (Debian, GNOME 48) f001 f003 f004 f016 f021 × chrome, firefox with binary f614910c: **PASS=36/36**; then 4fb3287d put back, PAM d1734958 unchanged, lock free | no (cured binary only in the VMs and in the box during the suite) |
| 01b062f | **T9 — the interfaces** (`installatore/interfaccia/`, `cmd/remotix-install/interfacce.go`, `gui_si.go`/`gui_no.go`, `motore/interfaccia.go`; §6.6.14). **Two builds of the same source**: static `remotix-install` (engine, CLI, TUI; "gui" ⇒ RX-UI-001) and `remotix-install-gui` (`gui` tag, cgo, Debian 12's glibc in `Contenitore.gui`; `costruisci.sh gui`, `costruisci.sh anteprime`). **GUI** Gio v0.10.3: five screens + "no desktop" + "blocked" + endings (stopped, cancelled, permissions denied), the logo's colours, Sora/IBM Plex embedded (OFL), logo cropped; the window as a user, the root part **started by systemd** (`StartTransientUnit` via D-Bus, interactive flag written by hand because godbus's `Object.Call` drops it; stdin/stdout = two pipes of the window), line-based JSON protocol. **TUI** Bubble Tea v1.3.10, as root. **Engine**: `DomandeDaFare`, `VociDiserie`, `PianoDaScelte`, `Motore.Fermata` (RX-AZIONE-006), `Rapporto.Minima` ("at least Debian 13 is needed"), `Piano.Dichiarate`. **D4** (`DECISIONI.md` §4.7): the belts always, outside the consents; `consenso.cinture` noted among the superfluous; gone `--senza-cinture`. **D5** (§10.20): the "no" to the encoding archive ⇒ `RX-H264-006` in the plan (BLOCCANTE) and `Applica` BLOCCATA before touching; the GUI and the TUI say so at once. **D6**: the welcome (CLI, TUI, GUI) states the port to forward on the router, TCP and UDP. `install.sh --finestra` (as a user, downloads the build with the window) and `--tui` | `DECISIONI.md` §10.14, §10.15, §10.19; fasi/17 §6.6.1, §10 ("almost no" choice, the language of the screens); pkexec left aside because `[M]` debian13-kde does not have it | `[M]` 30 Sep: Go tests green (new: TestPianoDaScelteComeLaCLI — R36 in small and D4 —, TestSenzaArchivioVideoNonSiInstalla — D5 —, TestFermataDaChiInstalla, TestTestiInterfaccia, TestVistaControlloParoleComuni). **R36** (debian13-gnome "cliente", three copies prepared identical, same binary `remotix-install-gui`): CLI (`installa`, "si" at the terminal), TUI (Enter at every screen), GUI (from the GNOME desktop's terminal, password in polkit's dialog) ⇒ three **CONFERMATA_A_CONDIZIONI**; identifiers and times normalised: `piano.json`, `insieme-risolto.json`, `insieme-risolto-pacchetti.json`, `certificato.json` **identical**, `registro.jsonl` identical except the APPROVATA line («a mano, al terminale / nella TUI / nella finestra», which is what it must say). **R37**: window uid 1000 in `user@1000.service`, root part uid 0 in `remotix-install-finestra-<pid>.service`; `sudo … gui` ⇒ RX-UI-003; without a session ⇒ RX-UI-002; TUI as a user ⇒ RX-UI-006. **R42**: GUI it (GNOME), en (KDE), `LANG=de_DE` ⇒ en and the root part `--lingua en`, `LANG=de_DE LANGUAGE=it:en` ⇒ it; TUI it, de ⇒ en, it:en ⇒ it; the RX- codes identical. **Stop** for real (debian13-kde): "Cancel and put back as it was" during the packages ⇒ **ANNULLATA**, packages and archive removed. **Constraint of §10.19**: `ldd` of the build with the window: 9 graphics libraries; the static one «not a dynamic executable». Screenshots: `/media/REMOTIX/vm17/t9-gui/` (LEGGIMI.txt) | yes (T9's archive) |
| (this commit) | ⚠ **not done, noted** (T9, interfaces): (1) the GUI is not yet tested on Fedora (SELinux: a binary in `/tmp` started by systemd as root), Alma, openSUSE, Arch, nor on XFCE/LXQt; (2) the package does not carry the build with the window (the GUI is used for the first installation, from `install.sh --finestra`): a launcher in the menu after the installation is to be decided; (3) on GNOME the window opens maximised (bigger than the free space on 1280×800) and the decorations are Gio's (blue bar): KDE gives them from the compositor; (4) polkit's dialog says «start transient unit remotix-install-finestra-…», not a sentence of ours: with pkexec one could give a polkit action of our own (`org.remotix.install`) — a polkit file on the machine before the installation, that is one more change | — | — | — |
| (this commit) | **The engine's catalog after D8** (`installatore/catalogo/catalogo.json` 2026.09.30.6, sequence 6, re-signed with the TEST subkey A-2026): Ubuntu 26.04, GNOME without the `gnome-session` component and without the note "D8 open" | D8: REMOTIX starts the distribution's default GNOME session (on Ubuntu `ubuntu`), which is already there: nothing to add, and the plan must not say it | `[M]` 30 Sep: TestCatalogo updated (ubuntu 26.04 gnome: COMPATIBILE without C-COMPONENTE), TestCatalogoIncorporatoFirmato green. ⚠ The archive's catalog (stable channel, sequence 5) must be republished with `pubblica.sh catalogo`: until it is, the engine chooses the embedded one (higher sequence) | — |
| (this commit) | ⚠ **seen in T6, not cured**: (1) the helper does not pass `PAM_RHOST` to authentication (sshd does, the client's address): `faillock` records «SVC remotix» instead of the address, and `pam_access` does not have the host; (2) **leap16-kde**: the Plasma session is not born (`nessun KWin sul bus`), **even with SELinux in permissive** ⇒ it does not belong to T6, it had never been tested (T3-T5 on leap16-xfce); (3) on leap16-kde the uninstallation rolls back: `disfa-codec` would remove `kdialog` (RX-PACCHETTI-002). ⇒ **Taken up**: (1) cured, (2) and (3) explained — rows "T6 follow-ups" below; and the stage's `s0` level on Leap, cured | for whoever takes them up | `[M]` 30 Sep | — |
| 1d0d9b6 | **T6 follow-ups (1) — the client's address to PAM, like sshd**: `autenticazione.c` `rcp_autentica_da()` sets `PAM_RHOST` = the browser's **bare** address (from `[ind]:porta`; a mapped IPv4 `::ffff:a.b.c.d` goes back to IPv4, like sshd's `ipv64_normalise_mapped()`) and `PAM_TTY` = "remotix" (sshd puts "ssh"; sshd does not set `PAM_RUSER`, and neither do we). The address travels in the question to the helper (`aiutante_chiedi(…, provenienza, …)`), in the in-flight request and, on "yes", in the verdict (`AiutanteVerdetto` with `rhost`) up to `figli_assicura_da()` ⇒ the child's PAM session receives it in place of "remotix" (logind `RemoteHost`). The two-argument `rcp_autentica()` stays (the `01-*` benches hook into it); twin copy in `banchi/rcp/` | D3 (DECISIONI §10.18): «deve rispecchiare PAM» — faillock recorded «SVC remotix» and `pam_access` did not have the host | `[M]` 30 Sep, `banchi/17-t6/t6-seguiti.sh`: **arch-kde** (default faillock) 2 errors ⇒ `faillock --user prova`: `RHOST 10.0.2.2` ×2; **fedora44-gnome-iso** (enforcing, `with-faillock`) the same, 0 SELinux denials; **debian13-gnome** and **leap16-kde**: `pam_unix(remotix:auth): authentication failure; … tty=remotix ruser= rhost=10.0.2.2 user=prova`; everywhere session `Service=remotix Remote=yes RemoteHost=10.0.2.2` (before `RemoteHost=remotix`); desktop PASS on debian13-gnome, arch-kde, fedora44-gnome-iso. ⚠ From 127.0.0.1 logind will record `Remote=no`, as for ssh: the guard (§5.1) discriminates on the seat. Compiles 7 out of 7, 0 warnings | yes (packages in `t6/pacchetti-seguiti/`, VMs back to the snapshot) |
| 1d0d9b6 | **T6 follow-ups (3) — the desktop's SELinux level as with ssh**: `figlio.c` `livello_selinux_come_sshd()`, after `pam_open_session`: role and type stay those of `pam_selinux`, the **level** is put back to the login map's (`getseuserbyname`), if the new context is valid (`security_check_context`) — `setexeccon`. libselinux with `dlopen` (no new dependency; silent where SELinux is absent) | **The cause**: `pam_selinux open` looks for the caller's domain (`remotix_t`) in `contexts/users/unconfined_u` and `default_contexts`, files of the distribution's policy that list `sshd_t`, `cockpit_session_t`, `xdm_t`… and not `remotix_t` (a module cannot extend them) ⇒ libselinux falls back to `failsafe_context` = `unconfined_r:unconfined_t:s0`. It hit only what the child executes **directly** (child, `startplasma-wayland`, labwc): what starts from the user manager (kwin, gnome-shell, pipewire) is born from `init_t`, which is listed, and already had `s0-s0:c0.c1023` — that is why on Fedora/Alma (GNOME from the manager) it was not seen | `[M]` 30 Sep, **leap16-kde enforcing**: before, child and `startplasma-wayland` `…:s0`, kwin `…:s0-s0:c0.c1023`; after, all `s0-s0:c0.c1023` (line «⭐ SELinux: il desktop di «prova» nasce … come con ssh (pam_selinux aveva dato …:s0)»), **0 denials**; fedora44-gnome-iso 0 denials in enforcing | yes |
| (this commit) | ⚠ **T6 follow-ups (2) — leap16-kde: Plasma does not start, and it is the PLATFORM's** (not REMOTIX's, not SELinux's): **KWin 6.4.2 crashes** (SIGSEGV in `EglSwapchainSlot::texture()` ← `ScreenCastStream::record`, 11 cores in 55 s, one at each rebirth) as soon as REMOTIX opens the capture in memory. Without 3D (VM, llvmpipe) KWin cannot allocate the buffers of the virtual output (`DRM_IOCTL_MODE_CREATE_DUMB: Permission denied` on the render node at every frame), never draws, and the screencast reads an empty chain — cf. KDE bug 487217 (nested KWin with llvmpipe, `EglSwapchainSlot`). The other routes tried by hand: `KWIN_COMPOSE=Q` ⇒ «OpenGL compositing is required for screencasting»; `KWIN_DRM_DEVICES=/dev/dri/card1` ⇒ no effect. On Tumbleweed and Arch (newer KWin) in the same VM it works ⇒ **a condition for the catalog**: *openSUSE Leap 16 + Plasma (KWin 6.4) requires 3D acceleration* (real card or virgl); without it, no KDE desktop — XFCE and LXQt (labwc in pixman) yes. ⚠ On real hardware Leap KDE is not yet tested. **And the uninstallation that rolls back because of `kdialog`** (RX-PACCHETTI-002, work for the engine's line, `installatore/` not touched): `disfa-codec` removes only the **new** packages of the Packman step (`libx264-165`, `libx265-215`, `libxvidcore4`) and leaves the **upgraded** ones (Packman's `libavcodec61` & co., before `7.1.5-160000.1.1` from repo-oss) — which however **require precisely those** (`libx264.so.165`…) ⇒ `zypper rm --dry-run` drags along 53 packages (libavcodec61, qt6-multimedia, kwin6, plasma6-workspace, kdialog…). The guard was right to stop; the list is wrong: a "new" package required by an "upgraded" one that stays is not removed — or the upgraded ones are brought back to the previous version (vendor change Packman → openSUSE) in the same transaction, then the new ones are removed. On leap16-xfce it was not seen because no desktop package asks for libavcodec61 | for the engine's line; for the catalog (Leap KDE) | `[M]` 30 Sep, leap16-kde "cliente", system journal, `coredumpctl`, log of the `disfa-codec` operation and `zypper rm --dry-run` redone by hand | — |

| 49ef16a | **T10 — the engine keeps what is needed by what remains, the REPOSITORY too** (`azione_deposito.go`: `Annulla` first the packages that arrived with the repository — those that something remaining asks for are kept and with them the repository stays, on Alma also `epel-release` if the kept Cisco repository uses its key; `Annullata` declares it with `RX-PACCHETTI-006`), and **dnf that "does not resolve" counts as "asked for by what remains"** (`gestore.go` `SimulaTogli`: `dnf remove --assumeno` exits 1 even when it succeeds, and if a PROTECTED package would break it does not print «Removing» — the names in the «Problem» lines are the dependants, `problemiDnf`/`nomeDaNevra`) | the already decided rule of the uninstallation (like RX-PACCHETTI-006 of installa-pacchetti) applied to the repository: before, RX-PACCHETTI-002 and ANNULLATA_IN_PARTE (`[M]` T10 30 Sep: alma10-kde — ark, dolphin, plasma-desktop… ask for openh264; fedora44-gnome-iso — openh264 ← libheif ← glycin ← gdk-pixbuf2 ← protected gnome-shell, and `mozilla-openh264` ← firefox) | `[M]` 30 Sep: `deposito_test.go` (keeps and declares; removes when nobody asks for it; epel stays with Cisco; dnf's «Problem» ⇒ kept) — go vet + go test green, gofmt clean; the live diagnosis on fedora44-gnome-iso (`dnf remove --assumeno openh264` ⇒ «Failed to resolve the transaction … protected packages: gnome-shell», exit 1 even for `remotix` alone). T10 round on 0.18.4: **alma10-kde and fedora44-gnome-iso PASS** in the whole script — `disfa-deposito-openh264: FATTA ([RX-PACCHETTI-006] il deposito openh264 resta acceso: … lo chiede ark, dolphin, plasma-desktop…)`, on Fedora `mozilla-openh264 (lo chiede firefox)` and `openh264 (lo chiede gnome-shell, glycin-libs…)`; operations CONFERMATA, 0 remotix packages left, groups of "prova" as before | in the engine (release 0.18.4) |
| 93040c2 | **T10 — REMOTIX depends on the PipeWire daemon + wireplumber** (`packaging/debian/control` Depends, `packaging/rpm/remotix.spec` Requires; Arch already had them) | on openSUSE GNOME from the Minimal-VM image PipeWire is not installed (GNOME pattern only recommended) ⇒ mutter «Error connecting to the screencast service» and the desktop does not arrive; dpkg/rpm see the library, not the daemon; the video of GNOME/KDE and the audio of every desktop need it | `[M]` 30 Sep: pipewire+wireplumber installed on a live tumbleweed-gnome ⇒ the desktop paints; the T10 round of leap16-gnome and tumbleweed-gnome goes from FAIL to **PASS** on 0.18.2/0.18.3 | in the packages (release) |
| d151ae9 | **T10 — Xwayland as a dependency of labwc** (`.rpm`: `(xorg-x11-server-Xwayland if labwc)` on Fedora, `(xwayland if labwc)` on openSUSE; before only `if xfce4-session`) | leap16-lxqt: labwc «cannot create xwayland server» ⇒ LXQt's X11 panel does not start ⇒ no stage; Xwayland is needed by labwc for X11 applications (XFCE **and** LXQt), not by one desktop only | `[M]` 30 Sep: xwayland installed on a live leap16-lxqt ⇒ the desktop paints; the T10 round of leap16-lxqt goes to **PASS** on 0.18.3 | in the packages (release) |
| cda31e6 | **T10 — `libyuv` gone from the three recipes** (`packaging/debian/control`, `packaging/rpm/remotix.spec`, `packaging/arch/PKGBUILD`): colour conversion is REMOTIX's own (`src/colori709.c`, fasi/18 §1), `libyuv` is not needed and is not on Alma nor on Arch with the soname | release 0.18.1-1 stopped on `dpkg-checkbuilddeps: unmet build dependencies: libyuv-dev` (the phase 18 container does not carry libyuv) | `[M]` 30 Sep: `packaging/rilascio.sh 0.18.1-1` and `0.18.1-2` build the 7 families (.deb Debian 13 and Ubuntu 26.04, .rpm Fedora 44/Alma 10/Tumbleweed/Leap 16, Arch), engine (two builds), signed archive; **`ldd` of every binary without libav\*/libswscale** (deb R4 32-33 libraries, rpm 28-31, 0 missing); SBOM ngtcp2 1.25.0/nghttp3 1.18.0; install.sh sha256 `2f7a1ca6…` | in the test packages (then removed) |
| 9991f09 | **T10 — at uninstallation the engine removes `~/.local/state/remotix/sessione.log` in all homes** (`azione_registri_utente.go`, step `togli-registri-utente` always last, with the sessions closed: only the `sessione.log` of each home from `/etc/passwd`, and `~/.local/state/remotix/` if it stays empty; nothing else in the homes; ESATTA: copies in the operation's folder, put back with permissions and owner if the uninstallation rolls back). The paths are declared in the plan ("always done: …") and in the certificate ("removed: …") | the user's decision of 1 Oct 2026, which closes point (2) of row 165906c: the session log is DIRETTO and is not user data | `[M]` 1 Oct: Go tests (the home of "prova" is left without the folder, that of "altro" with only its own file, the rollback puts everything back); in T10 on debian13-kde and leap16-kde (box), debian13-gnome and fedora44-gnome (VM): before, `/home/prova/.local/state/remotix/sessione.log` is there, after, no log in the homes; the "expected" exception removed from `17-t10.sh` | 0.18.5+ |
| 004aa22 | **T10 — the chosen port (`porta = N` in the answers file) is written in `/etc/remotix/remotix.conf.d/porta.conf`** (`piano_installazione.go`: a `scrivi-file` step before the switch-on, only if it is not 7447; `remotix.service` reads it from `EnvironmentFile`; the uninstallation undoes it) | `[M]` 30 Sep, the KDE boxes (port 8531/8532 because of `--network=host`): the engine opened the firewall on N and checked the service on N, but did not write the choice ⇒ the service started on 7447 and the installation ROLLED BACK («attivo ma 8532/tcp non in ascolto»); with the default port it was not seen | `[M]` 1 Oct: `TestPianoPortaScelta`; the two KDE boxes install and listen on their port (T10 PASS) | 0.18.6+ |
### 13.2 The test setup (benches, VMs)

| commit | what | why | measurement | installed |
|---|---|---|---|---|
| (this commit) | `banchi/17-distro/17-vm.sh`: one VM per `<distro>-<desktop>` from the official cloud images, cloud-init, ports per machine, `vesti` with the official package group, "cliente" snapshot, real reboot checked with the `boot_id` | the user's decision of 29 Sep: the installer's tests in VMs, one per desktop | `[M]` 9 distributions out of 9 booted, ssh in 3-39 s | copied to the server |
| 12f6782…(this commit) | `banchi/17-distro/17-carico.sh`: the load test of the VMs; rate from the frame counters over ~60 s; journal read with sudo **after** shutdown, VMs shut down one at a time | decide how many VMs together (4 or 8) | `[M]` 8 VMs do not hold (memory); we stay at 4 | copied to the server |
| (this commit) | `banchi/17-t2/`: the T2 measurement (live session with three witnesses and a 50 ms sentinel; stop / kill-parent / kill-child; chain from the journal) | §5.2 | `[M]` 10 tests on 4 desktops: no desktop dies | on the server, in /media/REMOTIX/tmp/t2 |
| (this commit) | `src/costruzione/`: a `Contenitore.<bersaglio>` for debian13, ubuntu2604, ubuntu2404, fedora44, alma10 (EPEL+CRB), arch, tumbleweed, leap16 — dependencies from the distribution's package manager, ngtcp2 1.25.0 and nghttp3 1.18.0 **static** (`quic-statiche.sh`, only `.a` in `/usr/local/lib`, `LIBRARY_PATH`: the Makefile does not change); `costruisci-tutti.sh` builds one or all of them in a copy of the tree and writes per target binary, logs, versions, `ldd` done in the container. `src/Contenitore` stays as it was | §6.2 and §6.3: compiled for each distribution, no `ld.so.conf.d` | `[M]` 29 Sep, on the laptop: **7 out of 7 compile**, `ldd` without "not found" and without ngtcp2/nghttp3. Ubuntu 24.04 stops at ngtcp2 (OpenSSL 3.0.13 without QUIC); a probe without the OpenSSL branch then shows only `codificatore.c:1419,1436` (ffmpeg 6.1) and `ei_disconnect` absent (`input.c:1218`, libei 1.2.1) — D7. Versions: OpenSSL 3.5.0 (Leap) … 3.6.4 (Arch); libavcodec 61 (Debian, Alma, Leap), 62 (Ubuntu, Fedora), 63 (Arch, TW); libei 1.3.901…1.6.0; PipeWire 1.4.2…1.6.9; glib 2.80…2.88. Arch and TW already have ngtcp2 1.25 with crypto_ossl: usable, not used for uniformity | no (laptop only) |
| (this commit) | **T1c**: `banchi/17-distro/17-t1c-installa.sh` (REMOTIX by hand in a VM, family by family: dependencies, PAM, `utenti-negati`, polkit/logind/sleep, user `prova`, transient unit on 7447), `17-t1c-browser.py` (real Chrome with the guides of `12-client-veri.py`: open → get in → first frame with the pixel judge), `17-t1c-guarda.sh` (its own labwc on the Intel, `127.0.0.1` because QEMU's UDP forwarding is IPv4 only) | run the ported product and see it from a real browser, before the installer | `[M]` 29 Sep, 7 "cliente" VMs, Full HD. **With the product binary: 0 out of 7.** All get in («Ammesso»), none paints: (1) in the `virtio_gpu` VM without 3D the PipeWire negotiation dies with «no more input formats» (CARD route with mandatory modifier, `cattura.c:1487`; the fallback to memory kicks in only after a frame, `figlio.c:5362`) — Debian, Ubuntu, Arch, TW; (2) Fedora and Alma: child exited with 37, AVC `{ transition } unconfined_service_t → unconfined_t` from `pam_selinux open`; (3) Fedora/Alma/openSUSE without third-party repositories: «libx265 non c'è in questa libavcodec: non se ne prende un altro» (Chrome asks for HEVC). **With the diagnostic binary** (`-DCOPIA_ZERO=0`, not the product): PASS Debian 13, Ubuntu 26.04 (GNOME 50, `@user` with `--headless`), Arch KDE; Fedora 44 and Alma 10 PASS only with `pam_selinux` removed from the PAM + `libavcodec-freeworld` (RPM Fusion); TW KDE (with Packman) and Leap XFCE BLOCKED by the VM: KWin and labwc do not allocate (`DRM_IOCTL_MODE_CREATE_DUMB: Permission denied` on the virtio node) ⇒ black canvas. `provisiona.sh` outside Debian installs `remotix.pam` (Debian) and its check says all the same «⭐ a posto» | copied to the server (`/media/REMOTIX/vm17/t1c/`) |
| (this commit) | **ISO state**: `17-vm.sh da-iso <macchina>-iso` (official ISO downloaded and verified with the site's sha256, kernel and initrd taken from the ISO, answers served over HTTP on 10.0.2.2, NEW disk, UEFI with its own NVRAM, "iso" snapshot with the NVRAM), `impronta [foto]` (firewall, SELinux, display manager, network, packages; from a read-only snapshot, ports k=6), `schermo` (screenshot from the monitor, without socat); answers in `banchi/17-distro/iso-risposte/` (preseed, autoinstall, kickstart ×2, archinstall 4.4, AutoYaST); ports k=5 | §7.2: a cloud image with a desktop on top is not a customer's machine | `[M]` 29 Sep: **6 out of 6 done** with the "iso" snapshot (ssh, sudo, graphical.target): Debian 10 min, Ubuntu 11, Fedora 7, Alma 7, Arch ~10, Tumbleweed 14. Against cloud+DESKTOP (`impronta … cliente`): 7447 closed by firewalld on Alma and **Tumbleweed ISO** (the TW cloud has no firewall), open on Fedora Workstation (1025-65535); `video` already given by the Debian installer, `render` never; NetworkManager network on all the ISOs (cloud Debian/Ubuntu/Arch: networkd); TW ISO with automatic login, snapper on btrfs, recommended packages (+1701 packages) and root with the user's password; Alma ISO on LVM; Fedora ISO with `noopenh264` — all in `banchi/17-distro/iso-differenze.md` | copied to the server |
| (this commit) | **T3, line B — the test of the `.deb` in a VM**: `banchi/17-distro/17-t3-prova.sh <macchina> <deb>` ("cliente" snapshot → person `prova` already in `video` → fingerprint → `apt-get install ./…deb` and nothing else → real Chrome on `127.0.0.1` with `17-t1c-guarda.sh` → fingerprint → `--reinstall` → fingerprint → `purge` → fingerprint → `autoremove --purge` → fingerprint → shut down and back to "cliente"; ⛔ it does not shut down a machine already running, it stops at 4 VMs) and `17-t3-impronta.sh` (files of `/etc` with sha256, of `/usr` with size and date, groups, accounts, units, packages, manuals, logind/sleep in force, nft) | R4, R5, R6 in small, at package level (without the engine) | `[M]` 29 Sep, `.deb` 313ccfc, on the server in `/media/REMOTIX/vm17/t3/deb/esiti/`. **debian13-gnome**: installs with 10 extra dependencies (labwc, wlr-randr and 8 wlroots libraries; `va-driver` and `xwayland` were already there), 0 upgraded; `nicfio` put in `video`+`render`, `prova` in `render` (DIRETTE), `prova` in `video` PREESISTENTE; service active, certificate generated (`DNS:rx-debian13-gnome`); `ldd` as `prova` with an empty environment: 0 missing; **Chrome PASS** («Ammesso, sessione nuova, desktop gnome», image at 4.8 s). **ubuntu2604-kde**: 8 extra dependencies, `gnome-session` **not** brought (`plasma-workspace` satisfies the alternative); same groups; **Chrome PASS** («desktop kde»); the package's KWin file **not** rewritten by the program. **R5**: between "after the browser" and "reinstalled" no file changed content; what remains is the dates of the folders redone by dpkg, `mimeinfo.cache` regenerated by a trigger (same size), CUPS and the session number (foreign). **R6**, before → after `purge`+`autoremove`: **no DIRETTA difference**: groups identical to before (`prova` stays in `video`: R33), `/etc/remotix`, `/etc/pam.d/remotix`, `/var/lib/remotix`, units, belts and the 10/8 packages gone; **INDIRETTE** (to be declared): `/etc/group-` and `/etc/gshadow-` (`gpasswd`'s backup copies, with the intermediate state), dates of the `/usr` folders, icon and mime caches regenerated; **foreign**: CUPS, `fwupd.conf` 644→640 (fwupd, with the machine idle as far as REMOTIX is concerned). ⚠ After the purge `prova` still has the **desktop alive** (`session-cN.scope`): it survives the service (§5.2) but nobody reaches it any more — a question for T5 | copied to the server (`/media/REMOTIX/vm17/t3/deb/`) |
| 5e287cb, 631ce8d, cdefd1f (this commit) | **T3, line B, redone for DECISIONI §10.12 (the installer is the only way) — the `.deb` with INERT pieces and the R40 test**: `dh_installsystemd --no-enable --no-start --restart-after-upgrade` (on upgrade `try-restart`: it restarts only if it was running); postinst gone (no groups, no `modifiche.log`); `prerm` which on `remove` alone stops the service (with `--no-start` debhelper no longer does it); `postrm purge` removes only certificates, ban, `/run/remotix` and `/var/lib/remotix` if empty, **does not touch the groups**; the three belts OFF in `/usr/share/remotix/cinture/`; PAM and `utenti-negati` stay (inert). The unit refuses to start without `/var/lib/remotix/installazione-confermata` (name **proposed** for T4-T5) with `RX-INST-001` and exit 78 of the main process (`sh -c 'test … ; exec remotix …'`) and `RestartPreventExitStatus=78` — ⚠ the real check belongs in the program (point 3 of §10.12). `17-t3-prova.sh`: R40 after `apt install` (enabled? active? port 7447? groups? belts in force?), `systemctl start` without the installer, then **the engine's steps done by hand and declared** (`prova` in the nodes' groups, belts copied into `/etc/{polkit-1/rules.d,systemd/logind.conf.d,systemd/sleep.conf.d}`, marker, `enable --now`), browser, reinstallation, steps undone by hand, `purge`, `autoremove`; listening ports in the fingerprint | DECISIONI §10.12, R40 | `[M]` 29 Sep, `.deb` cdefd1f (lintian 0 E/0 W; R13, R14, R4 green; **R23** two identical builds: Debian `6655ae2c…`, Ubuntu `223fdb75…`), **debian13-gnome and ubuntu2604-kde**: after `apt install` **service disabled and inactive, 0 sockets on 7447, groups identical to before, 0 belts in force** — the only additions are the package's files, the dependencies (10 / 8), `/var/lib/remotix` and `/run/remotix` empty (tmpfiles) and debhelper's state file; **`systemctl start`** ⇒ `failed`, `RX-INST-001` in the journal, 0 restarts, 0 sockets (⚠ `start` exits 0: with `Type=simple` the refusal is read only in the journal and in `is-active`). `[M]` The first version with `ExecStartPre` restarted every 2 s (`RestartPreventExitStatus` looks only at the main process) — cured. With the engine's steps by hand: active, 2 sockets, **Chrome PASS** on both (GNOME, KDE). **R5**: no file changes content; the reinstallation adds the state file `deb-systemd-helper-enabled/…/remotix.service` (debhelper records the enabling done by the engine: at purge it removes it itself) and regenerates `mimeinfo.cache`. **R6** (steps undone + purge + autoremove): no DIRETTA difference; INDIRETTE `/etc/group-`/`gshadow-` (`gpasswd`'s copies, from the engine's steps), icon and mime caches; foreign CUPS and `fwupd.conf`. ⚠ `prova`'s desktop stays alive after the purge — on KDE with `kdeconnectd` (1716), avahi and its own UDP ports listening: the question for T5 becomes more concrete | copied to the server (`/media/REMOTIX/vm17/t3/deb/`) |
| 3c8607e | **T3, line D — the test of the Arch package in a VM**: `banchi/17-distro/17-t3-pacchetto.sh <macchina> <passo>` (one step per call: `prepara` = person `prova` already in `video`; `impronta <nome>`; `installa` = copy and `pacman -U --noconfirm`, nothing else; `r40`; `motore-monta` / `motore-smonta` = **the engine's steps done by hand** — `prova` in the groups read from the nodes, with the log MESSO/C'ERA, and `enable --now`; `togli` = `pacman -Rns`; `confronta`) and `17-t3-impronta-arch.sh` (files of `/etc`, `/usr/lib/systemd`, polkit, tmpfiles, applications, `/var/lib/remotix` with sha256, the rest of `/usr` and `/var/lib` with the size; groups, accounts, units, explicit packages/dependencies, the names under `/home`) | R4, R5, R6, R33, R40 at package level, without the engine | `[M]` 29 Sep, package `0.17.0-3` (3c8607e), "cliente" VMs, on the server in `/media/REMOTIX/vm17/t3/arch-{kde,xfce}/` (the tests of `-1`, before §10.12, in `t3/arch-pkgrel1/`). **R4**: `pacman -U` alone resolves everything from the archives: **arch-kde** +8 packages (labwc, wlr-randr, wlroots0.20, seatd, …), **arch-xfce** +86 (ffmpeg with x264/x265 and ~50 libraries, pipewire+wireplumber+pipewire-pulse, labwc, `gnu-free-fonts` as `ttf-font`: the xfce4 group brings neither ffmpeg nor audio); 0 upgraded; two provider questions (`jack`, `ttf-font`) answered with the default. **R40**: after the package alone, service `disabled/inactive`, 0 listening on 7447, `render` empty, 0 belts and logind/sleep in force unchanged, firewall intact — ⛔ but `systemctl start remotix` **starts** (`RX-INST-001` missing, §13.1). **The engine's steps by hand** ⇒ **Chrome PASS on both**: arch-kde «desktop kde», first frame at 4.2 s, KWin's file found identical and not rewritten; arch-xfce «desktop xfce» (black wallpaper as in T1), and with `-3` the «remotix» audio sink mounted (with `-1`, without pipewire: «contesto PipeWire non creato … SENZA SUONO»). **R5**: reinstallation with the service on and a live session ⇒ **0 differences** in the fingerprints; the `try-restart` restarts the server in ~4 s and `prova`'s session stays (25 and 39 processes). **R6/R33**, before → after `motore-smonta`+`-Rns`: **no DIRETTA difference from the package** (gone `/etc/remotix`, `/etc/pam.d/remotix`, `/var/lib/remotix`, units, enabling link, all the dependencies brought); `prova` again only in `video` (PREESISTENTE, intact). **INDIRETTE** to be declared: the system group `seat` (`seatd`'s sysusers, via labwc) which pacman does not remove ⇒ `/etc/group`, `/etc/gshadow` and the `-` copies; on XFCE the link `/usr/lib/libvsscript.so` left by vapoursynth (via ffmpeg); the desktop's files in `/home/prova` (KDE/XFCE, cache, pipewire). **DIRETTE from the product at run time, left over**: `~/.local/state/remotix/sessione.log`, and on XFCE `xfce4-power-manager.xml` (§8.2). ⚠ In the test of `-1`, after `-Rns` `prova`'s KDE session was already closed (2 processes, the user manager); with line B the desktop stayed alive: not looked into further | copied to the server (`/media/REMOTIX/vm17/t3/`) |
| aec8402 | **T4, line A — the engine's tests** (`installatore/`): `costruisci.sh` (build and `go test` in the `golang:1.25` container, cache in `.cache/` because the laptop's `/tmp` is almost full, `-mod=vendor`, no network); `motore/*_test.go` (the fake machine under a folder: `/etc/group`, `/etc/passwd`, fake systemd and firewalld in JSON files, so that the state survives the killed process; the `PuntoDiProva` hook, which in the binary always stays nil); `prove/impronta` (fingerprint of a folder in Go, independent of the engine, with `-confronta` because the minimal containers have no `diff`); `prove/r1-contenitori.sh` (R1 in debian:13, fedora:44, archlinux, tumbleweed); `prove/Contenitore.systemd` + `prove/systemd-giro.sh` (Fedora 44 with systemd running: the real actions over D-Bus and `gpasswd`) | R30 and R1 in small, without the server's VMs (used by others) | see §13.1, aec8402 | laptop only |
| 165906c | **T3, line C — the test of the `.rpm` in a VM**: `banchi/17-distro/17-t3-rpm.sh <macchina> <passo>` (twin of `17-t3-pacchetto.sh`, with dnf/zypper: `prepara` = person `prova` already in `video`; `impronta`; `installa` = `dnf install ./…rpm` / `zypper install --allow-unsigned-rpm ./…rpm` and nothing else; `r40`; `motore` = **the engine's steps by hand** — the card's groups with `17-t3-gruppi.sh` (log of who was there / who was put there), firewalld service opened if firewalld is on, `enable --now`; `terzi` = RPM Fusion / Packman, **a separate step** (the condition of §11.1, D5); `selinux` = `ausearch -m avc,user_avc,selinux_err`; `reinstalla`; `motore-annulla`; `togli` = `dnf remove` / `zypper remove --clean-deps`; `confronta`); `17-t3-impronta-rpm.sh` (files, groups, users, units, packages with the dnf/zypper reason, SELinux contexts of our paths, firewalld) | test the package where a customer would find it, and see R40 | `[M]` 29 Sep, "cliente" snapshot, real Chrome on `127.0.0.1`, SELinux **enforcing** on all four. **R40 green 4/4**: after the installation service `disabled`/`inactive`, 0 listening on 7447, 0 belts active, groups unchanged, firewalld (where on) without `remotix`. **R4**: `tumbleweed-kde` brings by itself `libavcodec63 libavutil61 libswresample7 libswscale10 breeze6-wallpapers`; `leap16-xfce` 77 packages (ffmpeg, pipewire, libei, libva, **labwc, xwayland**); `fedora44-kde` none (ffmpeg-free already there); `alma10-gnome` **refused without EPEL** (`nothing provides libavcodec.so.61`, nothing touched), then with EPEL+CRB (an engine step) 28 packages from EPEL. **Desktop in the browser** with the engine's steps: without third-party repositories Fedora and Alma **get in but do not paint** («libx265 non c'e' in questa libavcodec», cause C of §11.1); with RPM Fusion / Packman **PASS on all four** (TW KDE, Fedora KDE, Alma GNOME, Leap XFCE). ⚠ `fedora44-gnome` was busy with another test: Fedora tested on `fedora44-kde`. **R19** 0 SELinux denials in enforcing (Fedora, Alma, TW, Leap) with the PAM without `pam_selinux`; server processes `unconfined_service_t`. **R5**: reinstallation ⇒ 0 REMOTIX differences (only desktop noise: `cups/subscriptions.conf`, KDE's transient units), service still on; `rpm -V remotix` clean (KWin's permission not rewritten). **R6/R33** (fingerprint before the installation ↔ after `motore-annulla` + removal): **no DIRETTA difference from the package** (after the `%ghost` cure for the `.nostro` marks, which on TW left `/var/lib/remotix`); groups **identical** to before, `prova` still in `video` (PREESISTENTE not touched); INDIRETTE: `/etc/group-` and `/etc/gshadow-` (gpasswd's copies), the dependencies that `zypper --clean-deps` keeps because recommended (`breeze6-wallpapers`), `prova`'s home (files of the desktop used and `~/.local/state/remotix/sessione.log`); from the **engine's step** D5/D6, not undone here: the third-party repository and its libraries (Fedora: ffmpeg-free downgraded 8.1.2 → 8.0.1), `/etc/firewalld/zones/public.xml` | on the server, in `/media/REMOTIX/vm17/t3-rpm/`; VMs back to "cliente" |
| 56c93d3 | **T4-T5, line A — the engine in a VM**: `banchi/17-distro/17-t4-motore.sh <macchina> <remotix-install> <.deb>` ("cliente" snapshot, or `azzera` for the bare one with `DESKTOP=`; `prova` already in `video`; 17-t3 fingerprint; verifica → piano → approva → applica; real Chrome with 17-t1c-guarda; an ssh session of `prova` with a clock; disinstalla --purge; fingerprint and diff; shuts down and puts back as it was), `17-t4-alma.sh` (EPEL + dnf + firewalld over D-Bus, R28 for real, then CONFERMATA), `installatore/prove/sul-server.sh` (builds, copies to `/media/REMOTIX/vm17/t4/`, launches with `sg kvm`) | T4-T5 in a VM, one VM at a time | see §13.1, 56c93d3 | copied to the server (`/media/REMOTIX/vm17/t4/`) |
| (this commit) | `banchi/17-t7/`: `t7-campagna.sh` (lock of the boxes for the whole round; per desktop `aggiornamento` and `riavvio`; short suite; `LASCIA=1`), `t7-aggiorna.py` (two users with real Firefox and Chrome in two different labwc, witnesses like T2, restart with `11-accendi.sh`, the four times from the `short-unix` journal, third user with the cap at 2, reattach of the two in parallel, stage pid before/after, processes lost, witness gaps, `terminate-user` guard), `t7box.py` (processes and stage leader inside the box), `t7-abbandono.py` (found one with `--abbandono-s 60`), `t7-fine.sh` (abandonment, then boxes to 4fb3287d / d1734958) | T7, R7-R9 | see §13.1, 700cc1b | on the server, in /media/REMOTIX/tmp/t7 (evidence in `giro1/` and in the `<desktop>-<modo>/` folders) |
| 7b063f7, (this commit) | **T8 — the archive and the bench.** `packaging/archivio/pubblica.sh` (`aggiungi <canale> <bersaglio> FILE…`, `catalogo`, `revoche`, `motore`, `rigenera`: apt with apt-ftparchive, Origin/Label REMOTIX, **Valid-Until** 60 days, InRelease + Release.gpg; rpms signed with rpmsign and `repomd.xml.asc`, in the fedora:44 container; pacman `.sig` for every package, `remotix.db` redone with the newest version, `remotix.versioni` with the old ones; SPDX 2.3 SBOM per package with `sbom.py`, R24 red if the linked version is missing or differs from the declared one); `pacchetti-motore.sh` (the static engine packaged for the three families with its A signature and the timer off, and `remotix-archive-keyring`); `packaging/motore/` (units `remotix-aggiorna.service`/`.timer`, spec, PKGBUILD, LEGGIMI); the package recipes take `RX_VERSIONE`/`RX_REVISIONE` and write `/usr/share/remotix/incorporate.json`. `banchi/17-t8/`: `t8-vm.sh` (one step per call: accendi, terzi, impronta, engine from the archive, installa, stato, collega/via with the Chrome that **stays connected** — `t8-browser.py` —, palco, timer, spegni), `t8-fiducia.sh` (chain A), `t8-catenab.sh` (R17), `t8-guasta.sh` (faults on purpose in the served archive, and the restore), `t8-terzi.sh` (the THIRD-PARTY archive and R18's intruder «hello» 99.0, with a foreign key), `t8-prepara-guasti.sh`, `t8-porta.sh` (the archive on `127.0.0.1:8717`, the third parties on `:8719`: from the VMs `10.0.2.2`); `17-t1c-guarda.sh` accepts `T1C_PROGRAMMA`/`T1C_EVIDENZE` | T8 | `[M]` 30 Sep: test archive with N (0.17.0-1 / Arch -4), N+1 (-2 / -5), N+2 Arch (-6), annual 0.18.0 (Debian), engine 0.1.0-1…3; SBOM 8/8 (ngtcp2 1.25.0, nghttp3 1.18.0, the same as those declared). **R17** 9/9 (per family: one byte in the metadata, the metadata signed by a foreign key, one byte in the N+1 package: the manager refuses, version unchanged; apt exits 0 and says it only in the text: the engine now reads it). **R18**: on debian13 and fedora44 a third-party archive configured beforehand — its files and its key identical afterwards; `hello` 99.0 published on purpose in our archive: apt `-1 http://10.0.2.2:8717` (installs Debian's 2.10), dnf «matches only excluded packages»; no file in `trusted.gpg.d`. Uninstallation after the updates: repositories and `pacman.conf`/key **identical** to before (debian13, arch-kde); in the fingerprint only system noise (apt-listchanges turns itself off, cups, fwupd, gpasswd's `-` files) and on Arch the `seat` group created by a dependency (INDIRETTA) | on the server, in `/media/REMOTIX/vm17/{archivio,terzi,t8}` (the HTTP servers off: they are turned back on with `t8-porta.sh`) |
| c7773c5 | **T9 — the bench** `banchi/17-t9/`: `t9-porta.sh` (laptop: builds, signs engine and `install.sh` with the TEST subkey A-2026, an archive **of its own** in `/media/REMOTIX/vm17/t9/archivio` — a copy of T8's with the new engine — served on 8727; T8's is not touched), `t9-vm.sh` (`accendi rete\|senza-rete`, `motore`, `prepara`, `fuori-linea`, `r21`, `guarda` with a labwc **of its own**, `rete`, `spegni`), `t9-rete.py` (the capture: incoming from the forwards / started by the VM, with the installation window), `cloud-init-r21.yaml`, three answers files (Debian, Fedora, one without the consent on the belts). `17-vm.sh`: `RX_VM_SEME` (a different cloud-init seed), `RX_VM_RETE=,restrict=on` (network removed, forwards alive), `RX_VM_CATTURA=file.pcap` (`filter-dump` on the NIC); without them, it does what it did | R21 must be tested with a NEW seed (new instance-id ⇒ cloud-init redoes users, files and runcmd) on the "cliente" snapshot; R22 must be PROVED, not assumed: the capture also sees the attempts that `restrict` throws away | `[M]` 30 Sep: see §13.1, T9 row. ⚠ The `pkill -f` of whoever starts the HTTP server in the same ssh line finds ssh's shell and kills it: two separate ssh | copied to the server |
| (this commit) | **T6 — the bench** `banchi/17-t6/`: `t6-leggi-pam.sh` (the PAM stacks of sshd, SELinux, firewall, faillock of a VM from its snapshot), `t6-vm.sh` (one step per call: `accendi`, `motore`, `installa`, `entra [utente] [parola]` with real Chrome, `sessione` (Class, Remote, contexts), `avc` (audit.log with the time of each line **and** the journal), `modulo <pp>`, `ban-via`, `faillock [reset]`, `ssh-parola` (ssh with the password via `SSH_ASKPASS_REQUIRE=force`), `firewall` (firewalld and ufw, sha256 of the zone files), `disinstalla`, `spegni`), `t6-giro.sh` (the whole round: firewall before → install → R19/R20 → faillock → uninstall → firewall after → denials of the whole round), `t6-giornale.sh`, `t6-porta.sh`; `17-t1c-guarda.sh` with `T1C_UTENTE` | R19, R20, firewall | `[M]` 30 Sep, whole rounds: fedora44-gnome-iso, alma10-gnome-iso, tumbleweed-kde-iso, alma10-gnome, ubuntu2604-gnome-iso (ufw on), debian13-gnome-iso, arch-kde-iso, leap16-xfce: **everywhere** it gets in (new, resumed, after the service restart), logind session `Class=user`, `Remote=yes`, `Service=remotix`; wrong password ⇒ refusal; root ⇒ refusal (`pam_listfile: Refused user root`); **faillock** (Arch by default, Fedora and Alma with `authselect enable-feature with-faillock`): 3 errors from REMOTIX ⇒ the right password refused **by REMOTIX and by ssh**, `faillock --reset` ⇒ one gets back in from both. ⚠ The shared `17-vm.sh` changed while the bench was running («syntax error» halfway through a round): the bench uses a copy of it (`RX_VM`) | on the server, in /media/REMOTIX/vm17/t6 |
| 01b062f, (this commit) | **T9 — the interfaces' bench.** `banchi/17-t9/t9-gui.sh` (a "cliente" VM with the REAL desktop: `accendi` — "cliente" snapshot, USB tablet and QMP monitor, passwords of nicfio and of root: the "administrator" of polkit's dialog —, `accedi` from the login screen with the keyboard, `terminale`, `finestra <lingua>` typed in the desktop's terminal, `password`, `clic X Y` via absolute **QMP `input-send-event`**, `scrivi`, `tasto`, `foto`, `processi`); `t9-r36.sh` (`cli` and `tui` driven in a pty — `ssh -tt`, keys sent when the screen shows the expected text, 120×45, the points of the flow in `.passi` for the text screenshots —, `tui-lingua`, `raccogli`, normalised `confronta`); `17-vm.sh`: `RX_VM_TAVOLETTA=1` (usb-tablet + QMP in `<dir>/qmp.sock`), `hmp <macchina> "<comando>"`; `t9-porta.sh` builds, signs and publishes `remotix-install-gui` too; the answers files without `consenso.cinture` (`risposte-manca.conf`: now `consenso.aggiornamenti` is missing) | the window must be tested where a person uses it: their graphical session, their polkit agent | `[M]` 30 Sep: ⚠ the HMP monitor's `mouse_move` sends only **relative** motions, which the tablet discards (no ABS event in the guest: read `/dev/input/event4`) ⇒ QMP; ⚠ the window launched from ssh does not find the polkit agent («No authentication agent found») ⇒ it is launched from the desktop's terminal; ⚠ a Python program in a heredoc does not read commands from stdin (the heredoc IS the stdin) | copied to the server |
| (this commit) | **T6 follow-ups — the bench** `banchi/17-t6/t6-seguiti.sh <macchina> <pacchetti> [opzioni]` (FOTO, PRIMA in the environment): boots from the snapshot, installs, faillock reset, gets in (right), two wrong passwords, `faillock`, the PAM lines of the journal, sessions and contexts, SELinux denials, shuts down again | points 1 and 3 of the T6 follow-ups | `[M]` 30 Sep: debian13-gnome, arch-kde, fedora44-gnome-iso (`with-faillock`), leap16-kde; all shut down and back to the snapshot | on the server, `t6/pacchetti-seguiti/` |

| cda31e6, (this commit) | **T10 — the bench of the whole round** `banchi/17-distro/17-t10.sh` (one machine, the script of §7.3 from the archive of a real release: snapshot → fingerprint → `install.sh`+sha256 with `--risposte` → real browser → **real reboot** → **system update** to N+1 with a browser connected and the stage alive → **disinstalla --purge** with a live ssh session → fingerprint and R6) and `17-t10-giro.sh` (several machines, 4 at a time, "cliente" and "iso"); archive N in `t10/archivio-N`, N+1 in `t10/archivio-N1`, served by an http.server on `t10/arch/<macchina>` (symbolic link) on 8737 | T10 (§9): the round on the 26+6 machines of the matrix, R3-R43 in a single script, from the product of phase 18 | `[M]` 30 Sep: the certification expected in a VM is **A_CONDIZIONI** with only `C-RIPIEGO` (no card: R35, the frame goes in software OpenH264, `avc1.640c15`); the reboot with `RX_VM_RIAVVIA_S` (in a VM Fedora's shutdown is slow, ~5 min); R6 excludes the engine's history (`/var/lib/remotix`) and the session log (`~/.local/state/remotix`, open decision) as expected DIRETTA leftovers | on the server, `/media/REMOTIX/vm17/t10/` |
| ce3f2e7 | **T10 in a box**: `banchi/17-distro/scatole/` — `Contenitore.debian13-kde` (`task-kde-desktop`) and `Contenitore.leap16-kde` (`kde` pattern) like the "cliente" VMs, plus the three things of a box, declared (§7.5); `17-scatola.sh` with the verbs of `17-vm.sh` (`costruisci`, `torna`, `avvia`, `ssh`, `ferma`, `riavvia` = restart of the container, `porte`); `17-t10.sh <m> scatola` (archive on 127.0.0.1, the box's port in the answers file, step 4 declared). And at step 6 the session logs in the homes are looked at before and after (`registri-prima/dopo.txt`): after, there must be none. On the server: `/media/REMOTIX/t10-kde/` (boxes `t10-kde-debian13`, `t10-kde-leap16`, off; ports 8541/8542 ssh, 8531/8532 REMOTIX; archive on 8738) | the two KDE ones that in a VM do not have the screencast (§9, T10); and the new rule on `sessione.log` | `[M]` 1 Oct: the two boxes PASS at every step, the control VMs too | — |

### 13.3 The server environment

| what | why |
|---|---|
| `qemu-system-x86 qemu-utils genisoimage ovmf` installed, `nicfio` in the `kvm` group (29 Sep) | the VMs of §7; ⚠ volatile: it is in the after-reboot recipe |
