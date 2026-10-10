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
  all ten tests, until the clear-out three and a half minutes later;
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

**Il disegno** (`installatore/interfaccia/`, nessuna logica d'installazione, §6.6.1):
- `motore/interfaccia.go` — quel che il motore aggiunge per le interfacce: `DomandeDaFare` (la porta; il
  firewall aperto · chiuso · nessuno · altro; gli archivi di terzi che servono, e per che cosa; il desktop, se
  manca; chi non ha la scheda), `VociDiserie` (i valori predefiniti di §10), `PianoDaScelte` (le voci del file
  di risposte → `OpzioniDaRisposte` → `PianoInstallazione`: **le stesse regole** del senza domande, ma il piano
  non porta file né approvazione: la dà chi guarda il piano, con un solo «conferma»), `Motore.Fermata` (il
  pulsante «Annulla e rimetti com'era»: fra un passo e l'altro, poi tutto si annulla, **RX-AZIONE-006**);
- `interfaccia/sessione.go` — la **Sessione**, il motore da root: `Controlla` (fasi 0-2 come `verifica`),
  `Piano`, `Applica` (approvazione «a mano, nella finestra/nella TUI», gli eventi JSON del motore passati
  riga per riga); `protocollo.go` — la stessa sessione **in un altro processo**, JSON a righe su due tubi;
- `interfaccia/permessi.go` — ⭐ **la parte da root della finestra la fa partire systemd**, non pkexec:
  `StartTransientUnit` sul D-Bus di sistema col flag ALLOW_INTERACTIVE_AUTHORIZATION (polkit chiede la
  password nell'agente della sessione grafica), lo stesso eseguibile con `motore-interfaccia --lingua …`,
  stdin e stdout dell'unità = due tubi della finestra (i descrittori passano sul bus, come `systemd-run --pipe`).
  Perché: `[M]` debian13-kde **non ha pkexec** («exec: pkexec: executable file not found»: in Debian 13 è un
  pacchetto a sé, GNOME lo tira, KDE no); ed è la regola di §10.14 (con systemd e polkit dall'interno, D-Bus).
  ⚠ `Object.Call` di godbus toglie il flag interattivo: il messaggio si scrive a mano (`[M]` senza:
  `InteractiveAuthorizationRequired`). ⚠ La finestra va lanciata **dalla sessione grafica** (un terminale del
  desktop, il menu): da ssh polkit non trova l'agente;
- `interfaccia/vista.go`, `testi.go` — gli oggetti in **parole comuni**, it/en: le righe del controllo (niente
  driver né bus: «Scheda grafica virtuale», i nomi nei dettagli), le domande, i passi del piano **raccolti**
  (tre cinture = una riga; i gruppi di una persona = una riga) col cartellino della reversibilità vera del
  motore (`installa-pacchetti` è AL_MEGLIO ⇒ «Si annulla in parte»), l'avanzamento dagli eventi, il benvenuto
  (indirizzo, la porta da inoltrare sul router TCP e UDP — D6 —, le prove del certificato, le condizioni in
  parole comuni); `BloccoNelPiano`: il «no» all'archivio della codifica ferma subito (D5, **RX-H264-006**);
- `interfaccia/gui/` (etichetta `gui`) — Gio: le cinque schermate, «nessun desktop», «bloccata» e le fini
  (fermata, annullata); colori del logo, **Sora SemiBold, IBM Plex Sans, IBM Plex Mono incorporati** (OFL 1.1,
  licenze accanto; Sora 600 è l'istanza del Sora variabile di Google Fonts, Sora non ha nomi riservati), logo
  ritagliato da `grafica/logo/remotix-logo.png`; `gui --anteprima DIR --dati DIR` disegna le schermate fuori
  schermo (EGL senza superficie) in PNG; R37: da root la finestra risponde **RX-UI-003**;
- `interfaccia/tui/` — Bubble Tea v1.3.10 + lipgloss: le stesse viste in testo, da root (`sudo remotix-install
  tui`), per ssh e console; frecce, spazio, invio, esc; «a» ferma, «r» il registro, «d» i dettagli.

**Codici nuovi**: RX-UI-001…006 (senza finestra · senza sessione grafica · finestra da root · permessi negati ·
la parte da root si è interrotta · TUI senza terminale o senza root), RX-AZIONE-006 (fermata da chi installa),
RX-H264-006 (D5: senza l'archivio della codifica non si installa). ⚠ Il `vendor/` cresce a 37 MB (Gio,
go-text, x/text, Bubble Tea): la costruzione resta **senza rete**.


#### 6.6.15 10 ott 2026: i nomi in inglese (`DECISIONI.md` §10.35)

Tutto quel che l'amministratore digita o legge del motore è in inglese. I nomi nel codice Go e i commenti restano
italiani. Il formato degli oggetti passa a **`remotix-install/2`**, quello del file di risposte a
**`remotix-answers/2`** (prima `remotix-risposte/1`): niente compatibilità col vecchio, perché non ci sono
installazioni vere. Quel che segue nei paragrafi di prima resta come storia, coi nomi di allora.

| che cosa | prima | adesso |
|---|---|---|
| comandi | `verifica` · `piano` · `approva` · `applica` · `riprendi` · `annulla` · `stato` · `aggiornato` · `disinstalla` · `certifica` · `catalogo` · `installa` · `prepara-fuori-linea` · `versione` · `aiuto` (`aggiorna`/`ritorna` rimandavano al gestore) | `check` · `plan` · `approve` · `apply` · `resume` · `rollback` · `status` · `post-upgrade` · `uninstall` · `certify` · `catalog` · `install` · `prepare-offline` · `version` · `help` (`upgrade`/`downgrade`) |
| opzioni del motore | `--operazioni` · `--catalogo` · `--archivio` · `--canale stabile\|candidato` · `--porta` · `--risposte` · `--fuori-linea` · `--uscita` · `--eventi` · `--utente` · `--apri-firewall` · `--deposito` · `--pacchetto` · `--pacchetti` · `--piano` · `--installa` · `--approva` · `--tabella` | `--state-dir` · `--catalog` · `--archive` · `--channel stable\|candidate` · `--port` · `--answers` · `--offline` · `--output` · `--events` · `--users` · `--open-firewall` · `--extra-repos` · `--package` · `--packages` · `--plan` · `--install` · `--approve` · `--table` |
| ⚠ due cose diverse | `--archivio` (l'archivio firmato di REMOTIX) e `--deposito` (gli archivi di terzi: epel, rpmfusion, packman) | `--archive` e `--extra-repos`; nei fatti e nei passi gli archivi di terzi sono `repo` |
| `install.sh` | `--archivio` · `--canale` · `--verifica` · `--risposte` · `--insicuro` · `REMOTIX_ARCHIVIO` | `--archive` · `--channel` · `--check` · `--answers` · `--insecure` · `REMOTIX_ARCHIVE` |
| file di risposte | `formato` · `porta` · `archivio` · `canale = stabile\|candidato` · `utenti = tutti` · `consenso.firewall` · `consenso.deposito.<x>` · `consenso.cinture` · `consenso.aggiornamenti` · `si`/`no` (anche `sì`, `s`) | `format` · `port` · `archive` · `channel = stable\|candidate` · `users = all` · `consent.firewall` · `consent.repo.<x>` · `consent.guards` · `consent.updates` · `yes`/`no` (anche `y`, `n`) |
| stati dell'operazione | `NUOVA` · `FIDATA` · `ESAMINATA` · `VALUTATA` · `PIANIFICATA` · `APPROVATA` · `ACQUISITA` · `IN_ESECUZIONE` · `INTERROTTA` · `APPLICATA` · `IN_VERIFICA` · `VERIFICATA` · `CONFERMATA` · `CONFERMATA_A_CONDIZIONI` · `IN_ANNULLAMENTO` · `ANNULLATA` · `ANNULLATA_IN_PARTE` · `BLOCCATA` · `RIFIUTATA` | `NEW` · `TRUSTED` · `EXAMINED` · `ASSESSED` · `PLANNED` · `APPROVED` · `ACQUIRED` · `RUNNING` · `INTERRUPTED` · `APPLIED` · `VERIFYING` · `VERIFIED` · `CONFIRMED` · `CONFIRMED_WITH_CONDITIONS` · `ROLLING_BACK` · `ROLLED_BACK` · `PARTIALLY_ROLLED_BACK` · `BLOCKED` · `REFUSED` |
| esito della certificazione | `VERDE` · `A_CONDIZIONI` · `ROSSO` | `GREEN` · `CONDITIONAL` · `RED` |
| stati dei fatti, gravità, natura | `RILEVATO` · `VERIFICATO` · `SCONOSCIUTO`; `AVVISO` · `BLOCCANTE`; `SERVE_AZIONE` · `RIPROVABILE` · `RECUPERABILE` · `SERVE_ANNULLAMENTO` · `FATALE` | `DETECTED` · `VERIFIED` · `UNKNOWN`; `WARNING` · `BLOCKING`; `ACTION_NEEDED` · `RETRYABLE` · `RECOVERABLE` · `ROLLBACK_NEEDED` · `FATAL` |
| reversibilità, origine, esito di un passo | `ESATTA` · `AL_MEGLIO` · `CON_FOTOGRAFIA` · `IRREVERSIBILE`; `DIRETTA` · `INDIRETTA` · `PREESISTENTE` · `CONCORRENTE`; `COMPLETO` · `ASSENTE` · `A_META` · `ESTRANEO` | `EXACT` · `BEST_EFFORT` · `NEEDS_SNAPSHOT` · `IRREVERSIBLE`; `DIRECT` · `INDIRECT` · `PREEXISTING` · `CONCURRENT`; `COMPLETE` · `ABSENT` · `HALF_DONE` · `FOREIGN` |
| livello di compatibilità | `CERTIFICATA` · `COMPATIBILE` · `NON_SUPPORTATA` | `CERTIFIED` · `COMPATIBLE` · `UNSUPPORTED` |
| eventi del registro | `STATO` · `INTENZIONE` · `FATTA` · `FALLITA` · `INTENZIONE_ANNULLA` · `ANNULLATA` · `ANNULLAMENTO_FALLITO` · `NOTA` · `COMANDO` · `RIPRESA` | `STATE` · `INTENT` · `DONE` · `FAILED` · `ROLLBACK_INTENT` · `ROLLED_BACK` · `ROLLBACK_FAILED` · `NOTE` · `COMMAND` · `RESUMED` |
| valori dei fatti | `si` · `presente` · `assente` · `con` · `senza` · `nessuno` · `sconosciuto` · `aperto`/`aperta` · `chiuso`/`chiusa` · `altro` · `attivo`/`attiva` | `yes` · `present` · `absent` · `with` · `without` · `none` · `unknown` · `open` · `closed` · `other` · `enabled`/`active` |
| nomi dei fatti | `distro.famiglia` · `sistema.*` · `scheda.*` (`.fornitore`, `.modo`, `.gruppo`, `nodi`, `nvidia_proprietaria`) · `gruppo.*` · `pacchetto.*` · `deposito.*` · `codifica.*` (`strade`) · `porta.N.tcp_libera` · `.raggiungibile` · `firewall.tipo`/`zona`/`porta_*` · `h264.scheda`/`famiglia_driver` · `pam.base_mancanti` · `caratteri.scalabili` · `openssl.versione` | `distro.family` · `system.*` · `gpu.*` (`.vendor`, `.mode`, `.group`, `nodes`, `nvidia_proprietary`) · `group.*` · `package.*` · `repo.*` · `encoding.*` (`routes`) · `port.N.tcp_free` · `.reachable` · `firewall.type`/`zone`/`port_*` · `h264.gpu`/`driver_family` · `pam.base_missing` · `fonts.scalable` · `openssl.version` |
| tipi dei passi | `installa-pacchetti` · `installa-desktop` · `scrivi-file` · `abilita-unita` · `accendi-servizio` · `regola-firewall` · `aggiungi-utente-a-gruppo` · `aggiungi-deposito` · `attiva-cintura` · `chiudi-sessioni` · `togli-iscrizione` · `togli-registri-utente` · `disfa` | `install-packages` · `install-desktop` · `write-file` · `enable-unit` · `start-service` · `firewall-rule` · `add-user-to-group` · `add-repo` · `enable-guard` · `close-sessions` · `remove-membership` · `remove-user-logs` · `undo` |
| campi JSON (piano, profilo, rapporto, certificato, registro, eventi, pacchetto fuori linea) | `formato` · `oggetto` · `stato` · `mestiere` · `azioni` · `parametri` · `impronta` · `controlli` · `condizioni` · `esito` · `dettaglio` · … (circa 140) | `format` · `object` · `state` · `kind` · `actions` · `parameters` · `fingerprint` · `checks` · `conditions` · `result` · `detail` · … |
| file e cartelle in `/var/lib/remotix` | `operazioni/<id>/` con `stato` · `registro.jsonl` · `piano.json` · `fiducia.json` · `profilo.json` · `compatibilita.json` · `verifica.json` · `approvazione.json` · `insieme-risolto*.json` · `certificato.json`/`.txt` · `salvataggi/` (`.prima`, `.nuovo`); `piani/piano-<id>.json`; `installazione.json`; `aggiornamenti.json` | `operations/<id>/` con `state` · `log.jsonl` · `plan.json` · `trust.json` · `profile.json` · `compatibility.json` · `check.json` · `approval.json` · `resolved-set*.json` · `certificate.json`/`.txt` · `backups/` (`.before`, `.new`); `plans/plan-<id>.json`; `installation.json`; `recorded-versions.json` |
| l'archivio pubblicato | `motore/remotix-install(.sha256)` · `chiavi/remotix-archivio.asc` · `chiavi/LEGGIMI` · `LICENZE-COMPONENTI.txt` · `RILASCI.txt` · `pacman/*/remotix.versioni` · suite `<bersaglio>-stabile` | `engine/remotix-install(.sha256)` · `keys/remotix-archive.asc` · `keys/README` · `THIRD-PARTY-LICENSES.txt` · `RELEASES.txt` · `pacman/*/remotix.versions` · suite `<bersaglio>-stable` |
| il pacchetto `remotix-install` | `/usr/share/remotix-install/LEGGIMI` (italiano) | `/usr/share/remotix-install/README` (inglese) |

⚠ **Non cambiano** (sono identificativi, o li scrive il prodotto in C): i codici `RX-…` (`RX-PACCHETTI-006`,
`RX-RISPOSTE-002`…) e le condizioni `C-…` (`C-DEPOSITO`, `C-LIMITE`, `C-AMMINISTRATORE`…); il formato del catalogo
(`remotix-catalogo/1`, chiavi italiane: è un dato nostro, dentro il motore); il file `gruppi-iscritti.jsonl` e
l'uscita di `remotix --prova-codifica`, che il motore legge così come il prodotto li scrive; i file del prodotto
(`/usr/share/remotix/cinture/…`, `remotix.conf.d/porta.conf` con `REMOTIX_PORTA`).

#### 6.6.16 10 ott 2026: l'installatore di §10.36 (`DECISIONI.md` §10.36)

> Quel che sopra in §6 parla di archivio firmato, install.sh, archivi di terzi, desktop installato dal motore,
> firewall e cinture del motore, file di risposte, fuori linea, piano/approva/applica e ripresa è **storia**:
> vale questo paragrafo. Commit `2e16f8f` (motore), `8bcb881` (il .run), `623ea90` (banchi).

**Il principio** — REMOTIX non modifica il sistema: `check` dice che cosa manca (RX-MANCA-001 desktop,
-002 archivio che le dipendenze chiedono, -003 pezzi di un desktop installato, -004 nessun pacchetto per questa
distribuzione nel .run; RX-GPU-003…006 la scheda e il suo driver), **senza** suggerire pacchetti o comandi, e
`install` si ferma prima di toccare. L'eccezione voluta dall'utente: l'iscrizione ai gruppi della scheda resta
automatica (all'installazione e alla prima connessione).

**I comandi** — `check`, `install`, `uninstall`, `status` (stato + i controlli di `certifica` rifatti), `tui`;
nascosti `catalog` (per la tabella del manuale) e `post-upgrade` (per gli script dei pacchetti).

| prima | adesso |
|---|---|
| `plan` → `approve` → `apply` | `install`: controllo → simulazione del gestore → piano coi pacchetti esatti → *«Proceed? [y/N]»* dallo stdin → esecuzione → verifica → servizio acceso |
| `resume`, `rollback` | un'operazione non finita la trova `install` (la annulla: prima il rimedio del gestore, poi da capo, nessun ritentare automatico) o `uninstall` (la porta a termine) |
| `--answers FILE`, `prepare-offline`, install.sh, archivio firmato, `--archive`, `--channel`, `--extra-repos`, `--open-firewall` | il **.run**: `sudo sh remotix-X.Y.Z-R.run [install\|check\|tui]`; aggiornare = rilanciare il .run nuovo |
| cache dei pacchetti, sha256 nostri, `--download-only` | il gestore installa i file del .run e risolve le dipendenze dagli archivi della macchina; il motore simula soltanto (apt-get -s, dnf --assumeno, zypper --dry-run, pacman --print) |
| azioni `add-repo`, `install-desktop`, `firewall-rule`, `enable-guard`, i componenti e il driver Vulkan | via: li mette l'amministratore (il banco lo fa con `banchi/17-distro/17-amministratore.sh`) |

**Il .run** — `installatore/run.sh` è l'intestazione: estrae in `/var/tmp`, controlla lo sha256 del carico
(scritto dentro dal rilascio), passa `--bundle <cartella>/packages` al motore. Sotto, il tar.gz col motore statico e
`packages/<bersaglio>/` (prodotto + pacchetto `remotix-install`) per debian13, ubuntu2604, fedora44, alma10,
tumbleweed, leap16, arch. `packaging/rilascio.sh` lo costruisce e scrive accanto il .sha256 da pubblicare.

**La disinstallazione** — i pacchetti NUOVI dell'installazione, solo quelli e solo se niente altro li chiede
(la simulazione del gestore, come prima). ⚠ Non l'autoremove dei gestori: apt toglierebbe anche gli orfani di
prima, che non sono nostri.

**Numeri** — il motore (senza prove) da **12 594 a 8 959 righe**; catalogo `2026.10.10.13` (senza i campi che
servivano solo a suggerire: `comandi`, `installa`, `carattere_scalabile`, `pacchetti_desktop`,
`pacchetti_scheda`, `vulkan_nvidia`; `vulkan_scheda` diventa `vulkan_codifica`, e `senza_h264_di_serie` dice al
manuale dove il driver della distribuzione non ha H.264); formato degli oggetti `remotix-install/3`.
`go test`: verdi (interfaccia e motore); il .run provato sul portatile solo nell'intestazione (estrazione,
sha256, rifiuto di un file guasto, `check`).

**Che cosa la campagna sulle distribuzioni deve riprovare** (nulla di questo è provato sul ferro):
1. la simulazione e l'installazione dei quattro gestori coi file del .run — apt e dnf erano provati sulle VM,
   **zypper e pacman mai** su una macchina vera; dnf 4 (Alma) e dnf 5 (Fedora) con lo stesso lettore della tabella;
2. `install` fino in fondo sulle 26 combinazioni in SCATOLA con la scheda vera (in VM il controllo la rifiuta),
   dopo `17-amministratore.sh`; l'aggiornamento col .run N+1 con un browser collegato (R7, R10);
3. che `check` dica esattamente quel che manca su ognuna PRIMA della preparazione (RX-MANCA-*, RX-GPU-006 su
   Fedora/Alma/openSUSE col driver senza H.264), e niente dopo;
4. l'annullamento di un'installazione interrotta (`install` rilanciato) e il completamento di una disinstallazione
   interrotta, dal vero;
5. ⏳ **punto aperto**: i gruppi della scheda — solo `render` invece di `render` e `video` (§10.36: `video` dà
   anche `/dev/fb*` e le webcam), da misurare sui quattro desktop; per ora la logica è com'era;
6. ✅ **le licenze dei componenti di terzi** (10 ott, LICENSE.md §8): `THIRD-PARTY-LICENSES` nella radice del
   deposito, testi presi dai sorgenti esatti (ngtcp2, nghttp3 e sfparse, libopus e la libreria C di emscripten
   nel `.wasm`, le 8 descrizioni dei protocolli Wayland, Go e i 17 moduli che `go list -deps` trova nel
   motore). Viaggia in ogni pacchetto (`/usr/share/doc/remotix*/` sui .deb, `%license` sugli .rpm,
   `/usr/share/licenses/remotix*/` su Arch) e nel .run accanto al motore; `rilascio.sh` si ferma se il file non
   nomina un modulo, Go, ngtcp2, nghttp3 o libopus alla versione che entra. `packaging/archivio/` non serve più.
7. ✅ **TUI rifatta sul mockup approvato** (`grafica/tui-mockup/index.html`), commit `facc27a`: cornice fissa
   larga quanto il terminale (almeno 80 colonne; sotto, una riga che lo dice), Check › Plan › Install › Ready,
   corpo che scorre dentro la cornice, tasti in fondo; `remotix-install tui --preview 80` disegna ogni schermata
   con dati d'esempio. Non dal motore, quindi non mostrate: la **dimensione** dei pacchetti (la simulazione del
   gestore non la dà) e la **sospensione automatica** come riga del check (il motore non la rileva).
8. ✅ **labwc, wlr-randr, il carattere scalabile e breeze6-wallpapers sono dipendenze di REMOTIX** (utente,
   10 ott; `DECISIONI.md` §10.36), commit `facc27a`: il motore li aggiunge ai pacchetti, il piano li mostra in
   «Dependencies of REMOTIX» col desktop che li chiede; `17-amministratore.sh` non li prepara più. Da provare sul
   ferro: che la simulazione e l'installazione li prendano dagli archivi di ogni distribuzione.

---

## 7. Il banco: le macchine virtuali delle distribuzioni

### 7.1 L'impianto — ✅ in piedi il 29 settembre

`banchi/17-distro/17-vm.sh`, copia sul server in `/media/REMOTIX/vm17/`. Discende da
`/media/REMOTIX/vm.sh` (la VM unica di v1): QEMU diretto senza libvirt e senza root, rete in modalità
utente con inoltro delle porte, disco come sovrapposizione sull'immagine ufficiale, che resta intatta.

- **Le immagini** sono quelle *cloud* ufficiali di ogni distribuzione, con cloud-init: debian13,
  ubuntu2604, ubuntu2404, fedora44, fedora43, arch, tumbleweed, leap16, alma10.
- **Le macchine** si chiamano `<distro>-<desktop>` (`fedora44-kde`); `<distro>` da sola è «nuda».
- **Porte** sul server: ssh `2300 + 10·N + k`, REMOTIX `7500 + 10·N + k` (TCP e UDP), con N il numero
  della distribuzione e k del desktop (nudo 0, gnome 1, kde 2, xfce 3, lxqt 4).
- **Comandi**: `crea`, `avvia` (aspetta ssh e cloud-init), `vesti` (il desktop), `ssh`, `ferma`,
  `riavvia` (riavvio VERO dell'ospite, controllato col `boot_id`), `fotografa`/`torna`, `azzera`.
- `[M]` 29 set: **tutte e nove le distribuzioni partono** e rispondono a ssh in 3-39 s; SELinux
  Enforcing su Fedora e Alma.
- ⚠ Sul server QEMU va reinstallato dopo ogni riavvio (il sistema è in memoria): è nella ricetta.
- `[M]` 29 set: **le 27 macchine sono pronte** con la foto «cliente» (tutte rc=0); ubuntu2404-gnome resta per confronto, fuori dalla matrice (D7).
- **Quante VM insieme: 4** (decisione dell'utente: *«se il sistema regge passiamo da 4 a 8; se non regge
  torniamo a 4, così ci teniamo un po' di margine»*). `[M]` `17-carico.sh`, 8 VM × 10 min, ognuna con la
  schermata d'accesso, una codifica software Full HD 30 fps e 2,5 GB occupati: **8 × 6 GB e 8 × 4 GB non
  reggono, per la sola memoria** (minimo disponibile 1954 e 2868 MB contro la soglia di 3072; scambio
  medio 1536 e 2882 KiB/s contro 100); codifica 29,7-29,9 fps e ssh ≤ 0,9 s sempre dentro. Le VM
  chiedono ~4,1-4,5 GB l'una, il server ne ha ~30 liberi a riposo (il sistema sta in RAM). Una verifica
  mandata a smentire l'ha confermato, e ha trovato un'uccisione di earlyoom durante lo spegnimento
  parallelo che il giudizio non vedeva (ora le VM si spengono una alla volta, prima di leggere il
  journal). ⚠ Senza *balloon* una VM si tiene la memoria toccata: in ore di lavoro una VM da 6 GB va
  verso i 6 GB, non i 4,5 misurati in 10 minuti. Stima non misurata: 6 × 4 GB probabile, 5 × 6 GB no.

### 7.2 La macchina «come il cliente»

Gli stati di una macchina di prova, con nomi precisi:

| stato | che cos'è | foto |
|---|---|---|
| **BASE** | l'immagine *cloud* ufficiale, dopo cloud-init | il disco nuovo |
| **DESKTOP** | BASE + il desktop col **gruppo di pacchetti ufficiale** della distribuzione (`task-kde-desktop`, `kubuntu-desktop`, `dnf group install kde-desktop-environment`, `pacman -S plasma`, i *pattern* di zypper…), `graphical.target` | `cliente` (il nome di oggi nel banco) |
| **ISO** | una macchina installata **dall'ISO ufficiale** con l'installatore automatico della distribuzione (preseed, autoinstall, kickstart, archinstall, agama) e il suo desktop di serie — la più vicina a una macchina vera | `iso` |

⚠ **Una immagine cloud con un desktop sopra non è la macchina di un cliente**: manca il firewall
acceso, il display manager configurato dall'installatore, a volte SELinux in un altro stato, i
pacchetti che l'ISO mette di serie. ⇒ Il giro di ogni giorno parte da DESKTOP (veloce da rifare); lo
stato **ISO** si costruisce per una macchina per famiglia (debian13-gnome, ubuntu2604-gnome,
fedora44-gnome, arch-kde, tumbleweed-kde, alma10-gnome) e il **giro intero** passa anche da lì. Le
differenze fra DESKTOP e ISO di una stessa combinazione si annotano: se una prova cambia esito fra le
due, la verità è quella di ISO. ⛔ `vesti` non installa niente di REMOTIX: labwc, i gruppi della scheda, i codec sono mestiere
dell'installatore, e la prova deve vederli mancare se lui li dimentica.

### 7.3 Il copione di una prova

Su ogni macchina, automatico:

1. `torna cliente` (DESKTOP) o `torna iso` · impronte della macchina (`/etc`, `/usr`, gruppi, unità, firewall);
2. **installa** (lo script d'ingresso, e separatamente il gestore di pacchetti);
3. un **browser vero** entra e vede il desktop (codifica col ripiego software, Full HD: nella VM non
   c'è la scheda vera);
4. **riavvio vero** della macchina, e si rientra;
5. **aggiorna** a N+1 con una sessione viva, e si guarda che le finestre ci siano ancora;
6. **disinstalla** (`purge`), e confronta le impronte con quelle del punto 1.

### 7.4 Giro corto e giro intero

- **giro corto**, a ogni modifica dell'installatore: una macchina per famiglia (debian13, ubuntu2604,
  fedora44, arch, tumbleweed) — circa 20 minuti;
- **giro intero**, prima di dichiarare pronta una versione: tutte le 26 — circa 2 ore, tre alla volta,
  anche di notte.

### 7.5 Le due cose che la VM non prova

1. **La codifica sulla scheda vera** con la Mesa e i driver di ogni distribuzione (RPM Fusion,
   Packman): si prova in una **scatola** di quella distribuzione, che usa la scheda del server. Una
   prova per famiglia, non a ogni giro.
   ⭐ **1 ott 2026 — T10 in scatola** (decisione dell'utente): le due macchine che in VM non hanno lo
   screencast di KWin (`debian13-kde`, `leap16-kde`) fanno lo STESSO copione di §7.3 in un contenitore
   con la scheda Intel del server (`banchi/17-distro/scatole/`: `Contenitore.<m>` = il desktop col
   gruppo ufficiale, come `vesti`; `17-scatola.sh` coi verbi di `17-vm.sh`; `17-t10.sh <m> scatola`).
   Una scatola ha tre cose in più di una macchina, dichiarate: systemd e sshd su una porta sua
   (`--network=host`, quindi anche REMOTIX su una porta sua: `porta =` nel file di risposte), il
   gestore d'accesso spento (non ha un monitor e non deve prendere la scheda dell'ospite), i gruppi
   `video`/`render` allineati ai nodi dell'ospite (sulla macchina vera lo fa udev). **Non prova** il
   riavvio vero della macchina: al suo posto il riavvio del contenitore (`podman restart`), e il
   riavvio vero è verde sulle altre 30 in VM. Con la scheda vera la certificazione su Debian è
   **VERDE** (H.264 in hardware via `h264_vaapi`, iHD); su Leap resta `C-RIPIEGO` perché l'immagine
   per contenitori ha `solver.onlyRequires = true` come la Minimal-VM (§11.1) e il raccomandato
   `intel-media-driver` (repo-oss) non entra — messo a mano, `vainfo` dà H.264 EncSlice `[M]`.
   ⭐ **10 ott 2026 — le 26 in scatola** (§10.36: dalla fase 19 una macchina senza scheda non passa il
   controllo, e le VM non ne hanno): una ricetta per distribuzione col desktop come argomento
   (`Contenitore.{debian13,ubuntu2604,fedora44,alma10,arch,suse}` + `comune.sh`; le due del 1 ott sono
   assorbite), `17-scatola.sh` per le 26 con `REMOTIX_SCHEDA=intel|amd`, nome `t17-<m>-<scheda>`, porte
   proprie (ssh 8600+10n+k, REMOTIX 8800+10n+k, +100 sulla Radeon), fino a 4 accese insieme, e
   `costruisci-tutte`. ⚠ Ubuntu: `firefox`/`thunderbird` (pacchetti che installano uno snap) tenuti fuori
   con una preferenza di apt, perché snapd in una scatola non gira. Le immagini si costruiscono SUL
   SERVER (non sul portatile), a campagna xrdp finita. `[?]` nessuna ricetta è ancora stata costruita.
2. **La scheda data alla VM** (passthrough): oggi impossibile, il server parte con l'IOMMU spento; per
   accenderlo si cambia l'avvio del server, che fa l'utente. Non serve per questa fase.

---

## 8. Le prove — i requisiti misurabili

Ognuna gira sulle VM di §7; «rosso se» è la condizione che la fa fallire.

| # | requisito | la prova | rosso se |
|---|---|---|---|
| R1 | il controllo preliminare non tocca niente | impronte prima/dopo `--verifica` | una differenza |
| R2 | il controllo trova ogni difetto noto, **col suo codice** | macchine **guaste apposta**: senza scheda, senza `h264_vaapi`, NVIDIA proprietaria, porta occupata, PAM mancante, SELinux senza modulo, firewall chiuso | un guasto non detto, detto senza il **codice stabile** (§6.6.9) o senza il comando che rimedia |
| R3 | un comando installa | `install.sh`, e il gestore di pacchetti, su ogni famiglia | uscita ≠ 0, o `remotix verifica` rosso dopo |
| R4 | le dipendenze sono tutte dichiarate | installazione sulla macchina «cliente» senza niente a mano; librerie viste con l'uid di un inquilino | un `not found`, o un pacchetto aggiunto a mano |
| R5 | idempotenza | installare due volte | la seconda scrive qualcosa |
| R6 | ⭐ la disinstallazione **annulla tutto quel che REMOTIX ha fatto** (§6.6.4) — non «rimette la macchina com'era»: una dipendenza aggiornata dal gestore di pacchetti non torna indietro | impronte prima dell'installazione e dopo `purge`, confrontate col registro | una differenza **di origine DIRETTA** rimasta; una differenza INDIRETTA non dichiarata nel certificato; ⛔ un utente tolto da un gruppo in cui c'era **prima** |
| R7 | ⭐ durante un **aggiornamento del sistema** che comprende REMOTIX, REMOTIX non chiude da sé i desktop degli utenti | due utenti con un browser vero e un terminale aperto; `apt upgrade`/`dnf upgrade`/`pacman -Syu` che porta REMOTIX a N+1 | una finestra sparita, un processo del palco morto, uno schermo nero al riattacco |
| ~~R8~~ | ⛔ **tolta il 30 set** (parola dell'utente: *«io parlerei di aggiornamento del sistema, non di REMOTIX»*): l'aggiornamento del sistema lo decide e lo annuncia l'amministratore (anche con AMS, progetto a parte), e le interruzioni in quella finestra sono attese. Resta a REMOTIX solo R7. I tempi misurati (fermo ~4 s, browser di nuovo con l'immagine ~9 s) restano come informazione in §5.2 | — | — |
| R9 | il server nuovo ritrova **tutti** i palchi | `remotix stato` prima e dopo; ciascuno rientra nel **suo** | una sessione viva ma non ritrovata (il caso xrdp) |
| R10 | la scheda del browser già aperta sopravvive al cambio di versione | una scheda aperta durante R7, poi ricaricata | un errore non spiegato |
| R11 | si torna indietro | N → N+1 → N con sessione viva | una sessione persa, o la configurazione non letta |
| R12 | una configurazione sbagliata non spegne il servizio | file rotto in `/etc/remotix/remotix.conf.d/`, poi aggiornamento | il servizio vecchio fermato prima di sapere che il nuovo parte |
| R13 | ⛔ niente funzioni di banco attive | marche e opzioni di banco cercate nel binario **estratto dal pacchetto**, col controllo positivo sul binario di prova | trovate nel pacchetto, o non trovate in quello di prova |
| R14 | ⛔ niente file del banco nel pacchetto | elenco dei file contro una lista nera | una corrispondenza |
| R15 | regge il riavvio | installazione, riavvio vero, connessione | qualcosa che andava prima e non dopo |
| R16 | il certificato nasce al primo avvio e si sostituisce | cancellato e riavviato ⇒ nuovo; uno dell'amministratore ⇒ usato quello | nessun certificato, o quello dell'amministratore ignorato |
| R17 | depositi firmati e verificati | un byte alterato; una firma sbagliata | il gestore lo accetta |
| R18 | la chiave vale solo per REMOTIX, e non tocca i depositi che c'erano | `Signed-By`, niente `trusted.gpg.d`; su una macchina con **altri depositi di terzi già configurati**: le loro chiavi e i loro file invariati, e nessun pacchetto non-REMOTIX installabile dal nostro | chiave globale; un file di un altro deposito cambiato |
| R19 | SELinux attivo, zero rifiuti | Fedora, Alma, Tumbleweed in *enforcing*: sessione completa, poi `ausearch -m avc` | un rifiuto legato a REMOTIX |
| R20 | PAM giusto su ogni famiglia | accesso giusto ⇒ sessione logind `user`, `Remote=yes`; sbagliato ⇒ rifiuto; root ⇒ rifiuto | un caso diverso |
| R21 | installazione senza domande | cloud-init con un file di configurazione depositato | una domanda, un'attesa |
| R22 | installazione senza rete | sorgente preparata prima, VM senza rete | un accesso alla rete |
| R23 | costruzione riproducibile — quattro livelli: binario, pacchetto, metadati del pacchetto, deposito | due costruzioni in due contenitori puliti con lo stesso `SOURCE_DATE_EPOCH` | `diffoscope` trova differenze nel binario o nel pacchetto (T3); nei metadati e nel deposito (T8) |
| R24 | SBOM completo | lo SBOM nomina ngtcp2/nghttp3 con la versione che sta nel binario | versione assente o diversa |
| R25 | benvenuto utile | l'uscita ha le cinque voci di §6.5 punto 8 | una voce mancante |
| R26 | il registro dice tutto | ogni modifica trovata da R6 è in `modifiche.log` | una modifica non registrata |
| R27a | l'installatore **ha preparato la piattaforma** su ogni combinazione della matrice | la certificazione 7a/7b del motore (§6.0) | un controllo richiesto non PASS |
| R27b | REMOTIX **funziona** su quella piattaforma | la suite funzionale corta (fase 15) su ogni VM, in Full HD col ripiego software | un rosso che su Debian non c'è — ⚠ è una prova del **prodotto**, non dell'installatore |
| R28 | ⭐ un'installazione che fallisce a metà si annulla per intero | guasto innestato in ogni passo della fase 6 (rete tagliata, disco pieno, pacchetto rotto) | impronte diverse da prima dell'inizio |
| R29 | la certificazione non mente | la fase 7 su macchine guaste apposta (scheda che non codifica, PAM rotto, porta chiusa) | un «verde» su una macchina guasta |
| R30 | ⭐ un'installazione interrotta si riprende | QEMU ucciso in **ognuno di questi punti**: prima che il passo sia annotato; annotato ma non cominciato; a transazione del gestore di pacchetti cominciata; a metà di un file di configurazione scritto; a unità abilitata ma registro non aggiornato; durante il ritorno indietro. Poi riavvio e motore rilanciato | la macchina resta a metà; un passo rifatto due volte con effetto doppio; la ripresa non porta a COMMITTED o ROLLED_BACK |
| R31 | il piano non si applica a una macchina diversa | piano fatto, macchina cambiata (un pacchetto tolto), poi applicazione | il piano applicato lo stesso |
| R32 | ⭐ UNKNOWN non è mai PASS | ogni controllo della certificazione fatto fallire **nel modo di non sapere** (strumento assente, permesso negato, tempo scaduto) | un PASS, o un certificato COMMITTED senza CONDITIONAL/BLOCKED |
| R33 | i gruppi che c'erano restano | un utente già in `video` prima dell'installazione; dopo `purge` | l'utente tolto da `video` |
| R34 | le cinture si annullano al loro stato di prima | un `logind.conf.d` dell'amministratore già presente che tocca gli stessi tasti; installazione e `purge` | il suo file cambiato, o il comportamento di prima non tornato |
| R35 | lo stato «a condizioni» non sparisce | installazione su Fedora senza RPM Fusion (ripiego software); poi `remotix verifica` e il certificato | la condizione non scritta, o scritta solo nel piano |
| R36 | ⭐ tre interfacce, un solo motore | la stessa installazione guidata da CLI, TUI e GUI su tre copie della stessa macchina | piano, insieme risolto, registro (a parte gli orari) o certificato diversi fra le tre |
| R37 | la GUI non gira da root | processo della finestra durante l'installazione | uid 0 |
| R38 | una macchina senza desktop | VM «nuda» (senza desktop): risposta «sì» ⇒ desktop installato, `graphical.target` e schermata d'accesso NON attivati, desktop nel browser; risposta «no» ⇒ BLOCCATA con `RX-DESKTOP-001` e impronte invariate | un desktop che parte davanti al monitor; una macchina toccata dopo un «no» |
| R39 | l'aggiornamento passa dal gestore di pacchetti e non chiude i desktop | (D14, §10.23) un rilascio N+1 fatto col comando di rilascio, con un catalogo nuovo; l'aggiornamento DEL SISTEMA (`apt upgrade`, `dnf upgrade`, `pacman -Syu`) con un browser collegato | un file di REMOTIX cambiato fuori dal gestore di pacchetti; un desktop chiuso o rinato (processo diverso); il catalogo nuovo non in uso; `certifica` non verde dopo |
| R40 | ⭐ il pacchetto da solo non accende niente | `apt install`/`dnf install`/`pacman -U` del solo pacchetto su una VM «cliente»: impronte prima e dopo, porte in ascolto, gruppi; poi `remotix stato` | il servizio acceso o in ascolto; un gruppo, una regola del firewall o una cintura attivati; `remotix stato` che non dica «installazione non certificata» |
| R41 | un programma solo | durante un'installazione completa, l'albero dei processi figli del motore (`/proc`) | un processo che non sia il motore stesso o un programma dell'elenco chiuso; uno script eseguito; una chiamata a un programma non annotata nel registro |
| R42 | ⛔ *ritirata il 10 ott 2026: l'installatore parla solo inglese (`DECISIONI.md` §10.35)* — la lingua segue il sistema | la stessa installazione con `LANG=it_IT.UTF-8`, `LANG=en_US.UTF-8`, `LANG=de_DE.UTF-8` e `LANGUAGE=it:en`, in GUI (che si rilancia con polkit) e in TUI | una schermata o un messaggio nella lingua sbagliata; un codice `RX-…` diverso fra le lingue |
| R43 | la disinstallazione chiude solo le sessioni REMOTIX | un utente con un desktop REMOTIX aperto e, insieme, una sessione ssh con un processo che scrive l'ora ogni secondo; disinstallazione | il desktop REMOTIX ancora vivo; il processo della sessione ssh interrotto |

---

## 9. Le tappe

| tappa | che cosa | produce | stato |
|---|---|---|---|
| **T0** | il banco delle VM e le 27 macchine «cliente» | `banchi/17-distro/17-vm.sh`, foto `cliente` e `iso` | ✅ 29 set: 27 «cliente» + 6 «iso» (differenze in `banchi/17-distro/iso-differenze.md`); 4 VM insieme |
| **T1** | REMOTIX **compila e gira** su ogni distribuzione, installato a mano: le cure di §4.4 e §5.1 | il prodotto portabile; R27 verde, a mano | ✅ 30 set: compila 7/7; gira 7 famiglie su 7 col binario del prodotto, con le condizioni di §11.1 |
| **T2** | la **misura** di §5.2: che cosa uccide i desktop quando si ferma il servizio | la causa, e la stima vera | ✅ 29 set: nessun desktop muore; cura leggera (§5.2) |
| **T3** | le tre **ricette** dei pacchetti e i contenitori di costruzione per famiglia | `.deb`, `.rpm`, `.pkg.tar.zst`; R4, R13, R14, R23 | ✅ 30 set: .deb (Debian 13, Ubuntu 26.04), .rpm (Fedora 44, Alma 10, Tumbleweed, Leap 16), Arch; pezzi inerti (§10.12); desktop nel browser su tutte con i passi del motore a mano; R23 da fare per .rpm |
| **T4** | gli oggetti e gli stati di §6.6 (formato, registro, codici), poi il motore con la CLI, fasi 0-4: TRUST, PREFLIGHT, COMPATIBILITY, PLANNING, CONSENT & SAFETY (`remotix verifica`, `install.sh`) | R1, R2, R3, R25 | ✅ 30 set, linea A (aec8402, 56c93d3): oggetti, stati, registro, ripresa, PREFLIGHT, catalogo, CLI; R1 verde in 4 contenitori; R30 in piccolo verde (§13.1) |
| **T5** | il motore, fasi 5-8: il registro delle azioni, la certificazione, COMMIT / ROLLBACK; la disinstallazione | R5, R6, R26, R28, R29 | ✅ 30 set, linea A (56c93d3, ad5bc1b, 97918d0, 4dcaa70): le azioni vere di §10.12, la disinstallazione dal registro, `certifica` e R29; **giro completo motore → pacchetto → Chrome → disinstallazione sulle sette famiglie** (§13.1, tabella), R28 e R38 dal vero |
| **T6** | PAM per famiglia, SELinux, firewall | R19, R20 | ✅ 30 set (b2ddbbd, 75c28de, 95f86d7): PAM = sshd su ogni famiglia; modulo `remotix-selinux` (`remotix_t`); **R19 verde** (0 rifiuti in enforcing: Fedora 44, Alma 10, Tumbleweed, Leap 16 XFCE); **R20 verde** su 7 famiglie (Debian, Ubuntu, Fedora, Alma, Arch, Tumbleweed, Leap), faillock come ssh su Arch, Fedora e Alma; firewall col consenso su firewalld e ufw, disinstallazione senza resti sulla zona di serie (§13.1) |
| **T7** | l'aggiornamento senza chiudere i desktop (secondo T2 e D1) | R7-R12 | ✅ 30 set, parte del prodotto (700cc1b, 307d042): il padre nuovo ritrova i desktop vivi; **R7, R8 (misurato), R9 verdi sulle 4 scatole** (§13.1); R10-R12 coi pacchetti (T8) |
| **T8** | depositi firmati, canali, ritorno indietro, SBOM; l'aggiornamento automatico (timer, catalogo, D14) | R11, R17, R18, R24 | ✅ 30 set, con **chiavi DI PROVA** (7b063f7, 6773a66, e il commit del registro §13): l'archivio delle tre famiglie (`packaging/archivio/pubblica.sh`), la catena A nel motore, `aggiorna`/`ritorna` e il timer; **sulle VM**: installazione dall'archivio su debian13-gnome, fedora44-gnome, arch-kde; R17 9/9, R18, R39 3/3 (desktop mai chiuso, browser di nuovo dentro), R11 su apt/dnf/pacman, catena A BLOCCATA 8/8 (§13.1). Dipende ancora da D10, D11, D14 (§10) |
| **T9** | la **TUI** e la **GUI** sul motore finito (R36, R37); senza domande e senza rete; la codifica sulla scheda vera per famiglia (scatole) | R21, R22 | ⏳ 30 set, parte **senza interfacce** (c7773c5): file di risposte, `installa`, pacchetto fuori linea, `install.sh` (§6.6.12); **R21** verde (cloud-init su debian13-gnome, Chrome dentro; file senza un consenso ⇒ BLOCCATA `RX-RISPOSTE-001`), **R22** verde su debian13-gnome e fedora44-gnome (rete tolta, 0 tentativi verso fuori nella cattura, Chrome dentro), **R31** verde (§13.1). ⭐ **Le interfacce** (01b062f, §6.6.14): GUI con Gio e TUI con Bubble Tea nello stesso programma (due costruzioni dello stesso sorgente); **R36** verde (debian13-gnome, tre copie: piano, insiemi risolti e certificato uguali, registro uguale salvo la riga dell'approvazione che nomina l'interfaccia), **R37** verde (finestra uid 1000, parte da root = unità transitoria di systemd; da root RX-UI-003), **R42** verde (GUI e TUI: it, en, de→en, `LANGUAGE=it:en`→it); la GUI sul desktop vero di GNOME 48 e di KDE Plasma 6. La codifica sulla scheda vera nelle scatole da fare. ⛔ **10 ott: GUI tolta** (§10.31, §6.6.14): R36 e R37 restano prove del 30 set, il loro banco (`t9-gui.sh`, `t9-r36.sh`) non gira più |
| **T10** | il giro intero sulle 26 macchine della matrice, e la chiusura | tutti verdi | ✅ 30 set (prodotto senza ffmpeg, fase 18; rilasci di prova `0.18.1`→`0.18.4` dal comando di rilascio, chiave DI PROVA): **30 macchine su 32 (26 «cliente» + 6 «iso») VERDI** nel copione intero — install.sh (sha256) → installa (CONFERMATA_A_CONDIZIONI: `certifica` verde salvo `C-RIPIEGO`, in VM niente scheda e il video va in software OpenH264) → browser vero → riavvio vero → aggiornamento del sistema a N+1 con browser collegato e desktop vivo (RITROVATO) → disinstalla `--purge` (R43, R6). Curati in T10: via `libyuv` (cda31e6), dipendenza PipeWire+wireplumber (93040c2), Xwayland per labwc (d151ae9), e il motore che alla disinstallazione **trattiene ciò che serve a chi resta, deposito compreso** (49ef16a: alma10-kde e fedora44-gnome-iso da ANNULLATA_IN_PARTE a CONFERMATA con RX-PACCHETTI-006). **2 di piattaforma** in VM: `debian13-kde` e `leap16-kde` — KWin di quella versione senza accelerazione 3D non produce screencast in VM («monitor «», 0x0»); ubuntu/fedora/arch/tumbleweed KDE (KWin più nuovo) passano nella stessa VM. ⭐ **1 ott: le due KDE in SCATOLA con la scheda vera (§7.5), rilasci `0.18.6-1`→`-2`: PASS in tutti i passi** — installa (Debian certificazione **VERDE**, H.264 in hardware; Leap `C-RIPIEGO`, §7.5), browser vero (Chrome, «desktop kde», tela non degenere), riavvio DEL CONTENITORE (dichiarato), aggiornamento a N+1 col browser collegato e il palco uguale (kwin_wayland, plasmashell), disinstalla `--purge` (R43, R6, e nessun `sessione.log` nelle case). Curati lì: la **porta scelta** non finiva nel servizio (004aa22) e la **decisione su `sessione.log`** (9991f09, §13.1); `debian13-gnome` e `fedora44-gnome` rifatte in VM con lo stesso rilascio: PASS. ⇒ **32 su 32**. Banco `banchi/17-distro/17-t10.sh`/`17-t10-giro.sh`, `scatole/17-scatola.sh`. ⚠ In VM lo spegnimento di Fedora/RPM nel riavvio è lento (~5 min, nessun difetto) ⇒ `RX_VM_RIAVVIA_S` |

Ordine delle distribuzioni dentro ogni tappa: prima quelle che rendono di più con meno (**Debian 13,
Ubuntu 26.04**), poi **Fedora e Arch**, poi **openSUSE** (la più scomoda per H.264) e **Alma**.

Metodo, come nelle fasi 12-16: incrementi piccoli, la rete completa dopo ognuno; le rifiniture dei
banchi **non fermano** le tappe (*«ci stiamo avvitando in inezie tecniche bloccando il progetto»*,
29 set); le prove mirate si fanno in secondi, il giro intero solo quando serve.

---

## 10. Le decisioni che spettano all'utente

Una per volta, ognuna nel momento in cui serve (la tappa è indicata). R8 è stata tolta il 30 set (l'aggiornamento del sistema è dell'amministratore).

| | la domanda | quando | la proposta |
|---|---|---|---|
| **D1** | ~~Le sessioni aspettano il server nuovo invece di morire con lui?~~ ⭐ **Superata dalla misura di T2**: i desktop sopravvivono già. Resta una domanda più piccola: il figlio muore col padre (per scelta) — va bene così, visto che il desktop resta e il padre nuovo lo ritrova? | T7 | sì: il desktop è la cosa che conta, il figlio si rifà al riattacco |
| **D2** | ✅ **CHIUSA il 29 set**: sì, ngtcp2 e nghttp3 dentro — dalla regola generale dell'utente (`DECISIONI.md` §10.6): *quel che manca o è troppo vecchio lo porta REMOTIX*, salvo i codec brevettati (archivio esterno col consenso) e i desktop (fuori matrice) | — | — |
| **D3** | ✅ **CHIUSA il 30 set**: REMOTIX **rispecchia PAM** — la pila dell'accesso remoto standard della distribuzione, `pam_faillock` e `pam_selinux` compresi dove ci sono (`DECISIONI.md` §10.18); root escluso come ssh | — | — |
| **D4** | ✅ **GIÀ DECISA (`DECISIONI.md` §4.7, 15 ago 2026)**, richiamata dall'utente il 30 set: *nessuno* spegne, riavvia, sospende il server — le voci nascoste nei menu dei quattro desktop **e** le tre cinture (polkit, tasti fisici, sospensione automatica). ⇒ l'installatore le attiva **sempre, senza domanda**; dichiarate nel piano e nel benvenuto, tolte alla disinstallazione | — | — |
| **D5** | ✅ **CHIUSA il 30 set**: consenso richiesto; un «no» ⇒ REMOTIX non si installa (`DECISIONI.md` §10.20); ✅ **riconfermata il 30 set con la fase 18**: anche senza ffmpeg, quando il video andrebbe in software, un «no» al deposito dei driver (RPM Fusion, Packman) **blocca** — scelta dell'utente fra «installa dichiarando il software» e «blocca» | — | — |
| **D6** | ✅ **CHIUSA il 30 set**: l'installatore apre sul firewall la porta scelta; il router è dell'amministratore, niente UPnP (§10.20) | — | — |
| **D7** | ✅ **CHIUSA il 29 set: Ubuntu 24.04 fuori**, si parte dalla 26.04 (parola dell'utente: *«partiamo dalla 26.04»*) | — | — |
| **D8** | ✅ **CHIUSA il 30 set**: su Ubuntu la sessione `ubuntu` di serie, non il GNOME vanilla (§10.20) | — | — |
| **D9** | ✅ **CHIUSA il 30 set: dopo la fase** (conferma dell'utente). Non è un difetto né di REMOTIX né delle distribuzioni: le immutabili tengono il sistema in sola lettura per scelta, e chiedono un **terzo modo di installare** al motore (stratificare il pacchetto e riavviare — `rpm-ostree`, `transactional-update` — o un'immagine `systemd-sysext`; gruppi in `/usr/lib/group`) | — | — |
| **D10** | ✅ **1 ott, per ora** (parola dell'utente: *«per il momento la lasciamo nella cartella locale del progetto»*): le chiavi dei rilasci stanno in `.chiavi/` del progetto, **ignorata da git** (mai nel deposito né su GitHub; le copie degli agenti non la vedono); `rilascio.sh`, `pubblica.sh` e `pacchetti-motore.sh` la trovano da soli anche da un worktree. La chiave VERA si genera più avanti, a lavoro finito. — 🔸 **Direzione del 30 set** (parole dell'utente: *«un repository git privato, ad esempio REMOTIX-DATA»*; *«sto pensando di acquistare un dominio … che mi costi poco all'anno»*): `REMOTIX-DATA` **privato** per il materiale di lavoro (ricette, catalogo, script di pubblicazione — ⛔ mai la chiave); l'**archivio** pubblico di file statici firmati in HTTPS **sul VPS dell'utente** (*«ho un server VPS»*, 30 set; server web semplice, `REMOTIX-DATA` può stare lì come git privato via ssh; costruzione e firma sul portatile, sul VPS solo file già firmati, ⛔ mai la chiave), sotto un **dominio nostro** perché l'indirizzo resta scritto sulle macchine dei clienti. Aperti: il dominio (da comprare), dove si custodisce la chiave (D11) | prima del rilascio | Cloudflare Registrar o Porkbun (prezzo di rinnovo basso) |
| **D11** | ✅ **SEMPLIFICATA il 30 set**: una chiave sola, quella dell'archivio; installatore verificato con lo sha256; catalogo dentro il pacchetto (`DECISIONI.md` §10.21). Resta: dove si custodisce la chiave (con D10) | con D10 | — |
| **D12** | ✅ **CHIUSA il 30 set: Gio** (`DECISIONI.md` §10.19) — la GUI disegnata dal programma stesso, identica sui quattro desktop, senza browser; la TUI con una libreria Go nello stesso programma | — | — |
| **D13** | ✅ **CHIUSA il 30 set**: il prototipo è la base, con piccoli miglioramenti (§10.20) | — | — |
| **D14** | ✅ **CHIUSA il 30 set**: REMOTIX si aggiorna col sistema (`apt upgrade`…), niente timer nostro; a ogni versione un comando di rilascio rigenera pacchetti, installatore (sha256), catalogo e archivio (`DECISIONI.md` §10.23) | — | — |

**Le scelte di chi installa: quasi nessuna** (indicazione dell'utente, 29 set: *«non riesco ad immaginare
grandi scelte da parte dell'utente sull'installazione di REMOTIX, se non solamente la porta»*):
- **la porta** (predefinita 7447): una sola domanda, che vale per **TCP** (la pagina) **e UDP** (QUIC);
- due **consensi**, non preferenze, e **solo dove servono**: l'archivio esterno per H.264 (solo Fedora
  e openSUSE, D5) e l'apertura del firewall (solo se è acceso, D6);
- ⛔ tutto il resto ha un valore predefinito e **non si chiede**: chi entra (gli utenti della macchina,
  root escluso), il certificato (generato), le tre cinture (attive, dette nel benvenuto, D4), i gruppi
  della scheda. Chi vuole altro lo cambia dopo in `/etc/remotix/remotix.conf.d/`.

**Se sulla macchina non c'è un desktop** (proposta dell'utente, 29 set 2026: *«se REMOTIX non trova nessun
desktop installato, o chiede di installarlo all'utente oppure REMOTIX non si installa»*):
- PREFLIGHT lo rileva; nella schermata delle scelte compare **una domanda in più, solo in quel caso**:
  «su questa macchina non c'è un desktop: vuoi installarne uno?», con i soli desktop che il catalogo dà per
  buoni su quella distribuzione (Alma: GNOME e KDE), fra cui **chi installa sceglie quale** (parola dell'utente); uno è **già selezionato**, quello di riferimento della distribuzione — GNOME su Debian, Ubuntu, Fedora, Alma; KDE su openSUSE e Arch — ed è anche quello che si installa senza domande se il file di risposte non dice altro. **Sì** ⇒ l'installazione del desktop entra nel piano
  come azione dichiarata, col suo peso (pacchetti, GB); **no** ⇒ REMOTIX non si installa (BLOCCATA,
  `RX-DESKTOP-001`, col perché e il rimedio);
- lo stesso se c'è **solo un desktop non supportato** (Cinnamon, MATE, i3…): quello esistente non si tocca, il
  nuovo si aggiunge accanto;
- il desktop viene **dagli archivi della distribuzione** (il confine di `DECISIONI.md` §10.6 resta: REMOTIX
  non se lo porta dietro), e si installa **senza cambiare come parte la macchina**: niente schermata di
  accesso locale né avvio in grafica — i desktop di REMOTIX nascono senza schermo, e un server resta un
  server davanti al monitor;
- è un'azione **AL_MEGLIO** (§6.6.4): toglierla non rende la macchina identica, e il piano lo dice prima del
  consenso.

**Il linguaggio delle schermate** (indicazione dell'utente sul prototipo, 30 set: *«il riepilogo a volte usa
termini quasi da programmatore»*): chi installa legge **che cosa succede e che cosa deve decidere**, in parole
comuni («Accesso», «Protezione del sistema», «Serve il tuo consenso», «Lo sistemo io»); driver, percorsi,
nomi di pacchetti, codici `RX-…` e impronte stanno in un «Mostra i dettagli tecnici» chiuso di serie — è lì
che li cerca l'assistenza. Si scrive **«password»**, non «parola d'ordine»: è il termine che conoscono tutti (parola dell'utente, 30 set).

⇒ La GUI (e la TUI) sono **cinque schermate**: controllo della macchina · **una** schermata di scelte ·
il piano, con un solo «conferma» · l'avanzamento · il certificato e il benvenuto con l'indirizzo.

---

## 11. Punti da confermare `[?]`

La verifica sulle distribuzioni (29 set) ha chiuso i cinque punti aperti: GNOME 50 confermato con la
cura di §5.1; Fedora con Intel **senza** H.264 di serie (smentita la ricerca sugli installatori);
ngtcp2 minima 1.25.0; `pam_faillock` di Arch 3/900 s/600 s; openSUSE SELinux enforcing di serie e
`common-session-nonlogin`. Restano **da misurare** sulle VM:
- `gnome-remote-desktop` acceso di serie accanto a REMOTIX (porta 3389, niente conflitto; ma apre
  sessioni di cattura sue sullo stesso mutter);
- gli utenti `systemd-homed` (Arch);
- eventuali modifiche di Ubuntu alle unità di gnome-shell 50;
- il salto di labwc 0.8 → 0.9 / 0.20 (wlroots 0.20.2 ha ancora tutti i protocolli che usiamo `[L]`).

---

### 11.1 Gli esiti di T1 (29 set 2026, sera) `[M]`

- **Compila** (T1b + T1a unite, 8ecc925): **7 distribuzioni su 7**, ngtcp2/nghttp3 statiche, `ldd` pulito
  su ognuna; Ubuntu 24.04 si ferma a OpenSSL 3.0 (per D7: poi `codificatore.c:1419,1436` per ffmpeg 6.1 e
  `input.c:1218` per libei 1.2).
- **Gira** (T1c, a mano in 7 VM): si **entra** ovunque («Ammesso», sessione creata), ma col binario del
  prodotto **il desktop non arriva su nessuna**. Le cause:
  - **(A) difetto del prodotto**: senza accelerazione 3D il compositore non offre DMA-BUF, REMOTIX chiede
    solo quelli (`cattura.c:~1487`) e il ripiego sulla memoria scatta solo dopo il primo fotogramma, che
    non arriva mai. Vale per ogni macchina senza scheda (VM, server senza GPU). Cura in corso: ripiego
    sulla memoria **dopo** il fallimento della negoziazione, la copia zero resta la strada di serie.
    Con la memoria da subito (binario di diagnosi) il desktop arriva su Debian, Ubuntu 26.04 (**la cura di
    GNOME 50 funziona**), Arch, Fedora, Alma;
  - **(B) SELinux** su Fedora e Alma: `pam_selinux open` porta a un rifiuto `transition
    unconfined_service_t → unconfined_t` all'esecuzione del figlio; senza `pam_selinux`, zero rifiuti in
    enforcing. ⇒ T6: una regola nostra (come Cockpit) o via `pam_selinux`; ✅ **curato in T6**: `pam_selinux`
    rimesso come sshd e il modulo `remotix-selinux` (dominio `remotix_t`, §13.1), 0 rifiuti;
  - **(C) nessun ripiego senza libx264/libx265**: senza depositi di terzi (Fedora, Alma, openSUSE) REMOTIX
    rifiuta di codificare, per scelta scritta nel codice, anche dove c'è openh264 o svt-av1; con RPM
    Fusion (`libavcodec-freeworld`) o Packman (`libavcodec63`) riparte. ⇒ pesa su D5;
  - **(D)** tela nera su Tumbleweed (KWin) e Leap (labwc) — la verifica a smentire ha trovato **due cause
    diverse**, nessuna delle due quella scritta: il `CREATE_DUMB: Permission denied` è di Mesa sul nodo
    `renderD128` (il nucleo lo rifiuta a tutti, root compreso) ed esce identico su Arch, dove va.
    - **Tumbleweed: manca lo sfondo.** L'immagine *Minimal-VM* ha `solver.onlyRequires = true` ⇒ il gruppo
      KDE non porta `breeze6-wallpapers`, plasmashell non trova lo sfondo «Next» e non mostra né desktop né
      pannello (nero anche nella foto di KWin stesso). Con il pacchetto, il desktop arriva. ⇒ è della
      **piattaforma installata senza raccomandati** (un'altra ragione per lo stato ISO, §7.2);
      l'installatore su openSUSE porta `breeze6-wallpapers` (`C-COMPONENTE`);
    - **Leap 16: labwc non riesce a creare il buffer sulla scheda virtuale** (`gbm_bo_create failed`), anche
      lanciato a mano senza REMOTIX. Con `WLR_RENDERER=pixman` il desktop XFCE arriva. ⇒ limite di una
      macchina **senza 3D**, come (A). ✅ **Curato** (§13.1, `scheda_sa_disegnare()`): REMOTIX prova il
      buffer prima di dare il nodo a labwc e, se non nasce, avvia labwc con `WLR_RENDERER=pixman`
      dichiarato. `[M]` 29 set: su Leap 16 XFCE il desktop arriva, **anche col binario del prodotto**
      (labwc si cattura da `wlroots.c`, non da PipeWire: (A) qui non pesa); sull'Intel del server e del
      portatile la prova dice «sì» e la strada resta la scheda.
      - ⛔ **«rifiuta la misura» è smentito**: l'uscita passa a 1872×944 in 3 ms (riletta). Resta
        1280×720 **solo lo sfondo di xfdesktop**, anche minuti dopo: xfdesktop nasce ~150 ms **prima**
        della richiesta di misura e non ridisegna — è la stessa gara curata per LXQt (fase 14, incr. 3,
        `primario_lxqt()`), non pixman. La cura XFCE non è nello stesso punto: tocca la riga di avvio
        (`SESSIONE_RIGA_XFCE`), cioè la cintura del logout (`XFCE4_SESSION_COMPOSITOR`); e su Leap
        `wlr-randr`, che la cura di LXQt usa, **non è installato** (⇒ dipendenza per T3).
- **Chiusura di T1** (binario del prodotto con le due cure, 9e035c5): **scatole 208 PASS / 0 FAIL / 0 BLOCKED**,
  copia zero intatta su GNOME e KDE (14/14 palchi sulla scheda), la scheda Intel dice «sì» a labwc (zero
  ripieghi pixman); **VM: desktop nel browser su debian13-gnome, ubuntu2604-kde, fedora44-gnome, alma10-kde,
  arch-xfce, tumbleweed-kde** (con le condizioni: RPM Fusion e PAM senza `pam_selinux` su Fedora/Alma, 0
  rifiuti SELinux in enforcing; Packman e `breeze6-wallpapers` su Tumbleweed; su Arch il gruppo xfce4 non
  porta ffmpeg: dipendenza per T3). Su Alma RPM Fusion va **dopo** EPEL, o `libavcodec-free` va in conflitto.
  - **leap16-lxqt: mancano i caratteri.** `[M]` 29 set sera: la VM ha **solo caratteri bitmap** (PCF,
    `xorg-x11-fonts-core`; `fc-match sans` = «Misc Fixed»). Pango 1.56 non li sa misurare: l'altezza del
    titolo esce **1 398 724 px**, `create_corners()` chiede a cairo una superficie 9×1 398 724, cairo
    rifiuta (`_cairo_surface_nil_invalid_size`) e l'`assert` di `buffer_adopt_cairo_surface` (buffer.c:90)
    abbatte labwc (gdb con i simboli: `main` → `theme_init` → `create_corners` → `rounded_rect` →
    `buffer_create_cairo`). Non è pixman né LXQt: labwc nudo, senza configurazione, muore uguale. Il
    carattere lo porterebbe il pattern `lxqt` (`google-droid-fonts`, **raccomandato**), perso con
    `solver.onlyRequires` dell'immagine Minimal-VM — la stessa trappola dello sfondo di Tumbleweed; il
    pattern `xfce` porta i caratteri per altra via, e XFCE passava. È il difetto noto labwc#2525 (chiuso
    dall'autore «mancava un carattere», **nessuna cura**: nel ramo principale del 26 set 2026 l'`assert`
    c'è ancora). Con `google-droid-fonts` (+ Packman per libx265, (C)): **PASS** col binario del prodotto,
    0 SIGABRT, labwc in pixman dichiarato, desktop a 0,6 s. ⇒ **T3**: l'installatore esige un carattere
    scalabile (su openSUSE `google-droid-fonts`, `C-COMPONENTE`); REMOTIX da solo non lo può evitare —
    senza un carattere vettoriale non c'è niente da indicare a labwc. `[?]` proposta, non fatta: una
    riga «⛔ nessun carattere scalabile: labwc morirà» prima dell'avvio (fontconfig, `FC_OUTLINE`).
  - **Il primo fotogramma wlroots «NERO» nelle scatole non è nuovo e non è un guasto.** `[M]` c'era già
    in fase 16 (27 set, binario 45d048c8, `/media/REMOTIX/misure/fase16/intel-*/livello-*/server.log`):
    XFCE 107 palchi su 367, LXQt 150 su 278, e uguale sulla Radeon; 0 su GNOME/KDE (passano da PipeWire).
    Nella chiusura di T1: XFCE 12 su 14, LXQt 3 su 14 (le «24 righe» sono ognuna doppia, journal +
    registro della sessione). È il primo fotogramma preso alla nascita di labwc, prima che sfondo e
    pannello siano dipinti; le due cure non toccano la strada wlroots sull'Intel (0 ripieghi). Proposta
    non fatta: guardare il primo fotogramma dopo ~1 s, perché la riga segnali solo un nero che dura.
- **Stato ISO** (T0): 6 macchine su 6; le differenze che contano per l'installatore: `render` non c'è mai;
  Fedora Workstation apre 1025-65535, **Alma e Tumbleweed hanno la 7447 chiusa**; Tumbleweed con accesso
  automatico, btrfs e snapper (fotografie di sistema già pronte, §6.6.4), raccomandati installati; Ubuntu
  desktop minimo + snap, ufw spento; rete con NetworkManager ovunque.
- **Dipendenze di esecuzione misurate** (per T3), oltre al binario: Ubuntu 26.04 `libavcodec62 libswscale9
  libavutil60 gnome-session`; Alma 10 `epel-release`, CRB, `libavcodec-free libavutil-free libswscale-free`;
  Tumbleweed `libavcodec63 libavutil61 libswscale10`; Leap 16 `libavcodec61 libavutil59 libswscale8
  libpipewire-0_3-0 libva2 libei1 labwc xwayland` (XFCE 4.20 senza Xwayland non parte); Debian e Arch
  niente in più; Fedora la porta 7447 in firewalld (acceso dopo il gruppo Workstation).
- `provisiona.sh` installa sempre il PAM di Debian e la sua verifica si accontenta di «pam_systemd»: su
  Fedora e Arch direbbe verde con un PAM con cui non entra nessuno (**falso verde**: conferma che
  l'installatore si scrive da capo).
- Trappola del banco: il browser su `127.0.0.1`, non `localhost` (QEMU inoltra UDP solo in IPv4, Chrome
  manda QUIC a `::1`).

---

## 12. Fuori da questa fase

- le distribuzioni immutabili (D9);
- le distribuzioni senza systemd;
- la scheda data alla VM (passthrough) e le prestazioni per distribuzione;
- un pacchetto **dentro** le distribuzioni ufficiali (Debian, Fedora): con ngtcp2 incorporata non
  passerebbe le loro regole; è un passo successivo, se mai.

---

## 13. Il registro delle modifiche della fase 17 — per il manuale tecnico

*Ogni modifica si annota qui nel momento in cui entra: commit · che cosa · perché · misura ·
installata sì/no.*

### 13.1 Il prodotto (`src/`)

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| d7f82c2 | `src/Makefile`: le intestazioni di ffmpeg da `pkg-config --cflags libavcodec libavutil libswscale` | su Fedora e Alma (ffmpeg-free) stanno in `/usr/include/ffmpeg`: senza, `codificatore.c:24` non trova `<libavcodec/avcodec.h>`. Su Debian aggiunge solo `-I/usr/include/x86_64-linux-gnu`, che c'era già | `[M]` 29 set: Fedora 44 e Alma 10 compilano; Debian 13 identico (1 solo avviso, `main.c:500`) | no |
| c1573ae | `sessione.c` `unita_shell()`: la Shell si sceglie dal `FragmentPath` che il gestore d'utente dà per `@wayland` (il file `@wayland` ⇒ quella; il modello `@.service` ⇒ `@user`; altro ⇒ si ferma e lo dice); drop-in in `<istanza>.d/`, mai nel modello; la rilettura dell'`ExecStart` sulla stessa unità; lo sgombero conosce `@wayland.d` e `@user.d`; `provisiona.sh` pulisce e controlla anche `@user.d` e `@.d` (solo il nostro file) | GNOME 50 avvia `@user`: il drop-in su `@wayland` non si applicava e il controllo dava un falso verde (§5.1) | `[M]` compila pulito nel contenitore Debian 13; `[M]` sul portatile (GNOME 48.7) `FragmentPath` = `…/org.gnome.Shell@wayland.service`; `[M]` con un modello finto `x@.service` il `FragmentPath` di `x@wayland` è il modello e l'`ExecStart` di `x@user` porta `--mode=user`. ⛔ GNOME 50 vero non provato: tocca alla T1 sulle VM | no |
| 61ad596 | PAM per famiglia: `src/remotix.pam` (Debian/Ubuntu), `.fedora` (`password-auth`+`postlogin`, `pam_selinux` close/open, `pam_loginuid`; `pam_systemd` da `password-auth`), `.suse` (`common-*`, `common-session-nonlogin` + `pam_systemd`; va in `/usr/lib/pam.d`), `.arch` (`system-remote-login`). In tutti root escluso con `pam_listfile` su `/etc/remotix/utenti-negati`, in `auth` e `requisite` (niente oracolo sulla parola di root), `onerr=fail` (Cockpit usa `succeed`: il file perso toglierebbe l'esclusione in silenzio). `pam_faillock` non scelto da noi: D3 resta aperta, scritto in ogni file. `main.c` cerca il servizio in `/etc/pam.d` e poi in `/usr/lib/pam.d`; il testo su «other» corretto anche in `autenticazione.c` (e nella copia `banchi/rcp/`). `provisiona.sh` e `costruisci.sh` scrivono `utenti-negati` (root) se manca | `@include` è Debian: altrove nessuno entra (§4.3); il messaggio diceva «other è pam_deny su Debian», falso | `[M]` quattro contenitori (debian:13, fedora:44, archlinux, tumbleweed), `pam_authenticate`+`pam_acct_mgmt`: senza il file ⇒ respinto («Error in service module»); utente giusto ⇒ entra; parola sbagliata ⇒ respinto; root con la parola giusta ⇒ respinto senza che la parola venga chiesta. ⛔ La sessione (`pam_open_session`, `pam_selinux`, `pam_systemd`) non provata: nei contenitori non c'è systemd. ⚠ Da annotare, non fatto (tocca il C): `main.c` all'avvio non guarda `utenti-negati` | no |
| c687c0c | `certificati.c`: il nome del soggetto si costruisce con `X509_NAME_new` e si consegna con `X509_set_subject_name`/`X509_set_issuer_name`, invece di scrivere nel nome restituito da `X509_get_subject_name`; e l'esito di `X509_NAME_add_entry_by_txt` ora si guarda | in OpenSSL 4.0 `X509_get_subject_name` restituisce `const X509_NAME *` (Ubuntu 26.10, Fedora rawhide) | `[M]` `certificati.c` da solo con `-Wall -Werror`: su fedora:rawhide (OpenSSL **4.0.2**) il vecchio non compila (`discards 'const' qualifier`, riga 149), il nuovo sì; su debian:13 (3.5.7) compilano tutt'e due; in entrambi i certificati generati hanno soggetto = emittente = `CN=192.168.0.2` e il SAN giusto. ⚠ Il resto di `src/` con OpenSSL 4 non è stato compilato | no |
| e177e0c | `sessione.c` `registro_sessione_percorso()`: il registro della sessione passa da `/tmp/remotix-sessione-<uid>.log` a `$XDG_STATE_HOME/remotix/sessione.log` (di solito `~/.local/state/remotix/`); cartella 0700 verificata (vera, nostra, non scrivibile da altri), file aperto con `O_NOFOLLOW`, 0600, verificato regolare e nostro; se non si può, ripiego dichiarato su `XDG_RUNTIME_DIR`, e senza nemmeno quella la sessione parte senza registro (detto); il percorso passa alla shell con `g_shell_quote` | nome prevedibile in `/tmp`: un altro utente lo crea prima e il desktop non parte (con `protected_regular`), in silenzio — è R10-A9 di `fasi/10` | `[M]` compila pulito nel contenitore Debian 13; `[M]` le tre funzioni estratte e fatte girare da utente: caso normale ⇒ file 0600 al posto nuovo; cartella collegamento, file collegamento a `/etc/passwd`, cartella 0777 ⇒ ripiego dichiarato; niente casa e niente runtime ⇒ NULL dichiarato. `grep`: nessun banco legge il vecchio file (i banchi `04-*`/`06-*` usano un loro `/run/user/<uid>/remotix-sessione.log`) | no |
| fe9f354 | `Makefile`: minimi veri dichiarati e CONTROLLATI da `make dipendenze` con `pkg-config --atleast-version` (libavcodec ≥ 61.13.100, libavutil ≥ 59, libswscale ≥ 8, OpenSSL ≥ 3.5.0, ngtcp2 e ngtcp2_crypto_ossl ≥ 1.25.0, nghttp3 ≥ 1.18.0, libei ≥ 1.1.0, libpipewire ≥ 0.3.48, gio ≥ 2.80), tre esiti distinti (va / troppo vecchia / pkg-config non la conosce); con `PREFISSO` la cartella delle librerie si chiede a `pkg-config` dentro il prefisso (`lib64`, `lib/<multiarch>`, `lib`), e se non risponde si prendono le cartelle che esistono; `costruisci.sh` guarda anche `lib64`; tolto l'unico avvertimento della costruzione (`/*` in un commento di `main.c`) | «libavcodec ≥ 61» non bastava (serve FFmpeg 7.1); `dipendenze` guardava solo le intestazioni; il rpath assumeva `lib` (Fedora/SUSE: `lib64`) | `[R]` FFmpeg `APIchanges`: `avcodec_get_supported_config` = lavc 61.13.100; `[R]` libei.h 1.0.0 senza `ei_region_get_mapping_id`, 1.1.0 con; `[R]` pipewire `keys.h` 0.3.44 senza `PW_KEY_NODE_FORCE_QUANTUM`; `[M]` `cattura.c`/`cursore.c`/`suono.c` compilano con pipewire 0.3.48 (ubuntu:22.04), `input.c` con libei 1.2.1 (ubuntu:24.04); `[M]` `make dipendenze` nel contenitore: tutto OK, e con minimi finti dà NO/?? ed esce 2; `[M]` prefisso finto con `.pc` in `lib64` ⇒ `-L…/lib64 -Wl,-rpath,…/lib64`, senza `.pc` ⇒ la cartella `lib64` che c'è; costruzione da zero pulita, zero avvertimenti. `[?]` il minimo vero di nghttp3 non cercato | no |
| 192d482 | `sessione.c` `scheda_sa_disegnare()`: prima di dare il nodo a labwc (XFCE, LXQt) si crea un buffer di prova con `gbm` — XRGB8888 256×256, usi `SCANOUT\|RENDERING` e poi solo `RENDERING`, gli stessi con cui ripiega l'allocatore di wlroots. Se nessuno dei due nasce: `WLR_RENDERER=pixman`, niente `WLR_RENDER_DRM_DEVICE`, e una riga «RIPIEGO DICHIARATO» col motivo; se nasce, tutto come prima | macchina senza 3D (VM `virtio_gpu`, §11.1 D): il nodo si apre ma labwc non crea il buffer (`gbm_bo_create failed`) ⇒ tela nera. Criterio generico (si chiede alla macchina), nessuna eccezione per distribuzione o desktop | `[M]` 29 set: compila Leap 16 e Debian 13, zero avvisi. Sonda da sola (`gbm`): Intel del portatile e del server (i915) ⇒ «sì» con tutt'e due gli usi; VM Leap 16 ⇒ «no», `Permission denied`. Leap 16 XFCE installata a mano (T1c, + Packman per libx264/x265, solo diagnosi), Chrome vero: **PASS** col binario di diagnosi e **PASS col binario del prodotto**, senza impostazioni a mano; labwc con `WLR_RENDERER=pixman` nel suo ambiente. ⚠ Lo sfondo di xfdesktop resta 1280×720 (gara di nascita, §11.1 D) | no |
| 6bede6a | `cattura.c`/`cattura.h`/`figlio.c`: il **ripiego sulla memoria dopo il rifiuto della scheda**. `cattura_formato_rifiutato()` = flusso in errore **e** nessun formato mai concordato (due fatti, non il testo di PipeWire); `cattura_avvia()` lo dice con `G_IO_ERROR_NOT_SUPPORTED` se arriva prima che torni. In `prendi_il_palco()` `ripiega_se_rifiutata()` passa la strada alla MEMORIA, scrive «la strada della SCHEDA e' stata RIFIUTATA … RIPIEGO DICHIARATO», segna `scheda_mai_piu` e riapre la sola cattura sullo stesso palco. `cattura_prendi()` esce subito da un flusso in errore invece di aspettare 5 s. Niente offerta doppia (la memoria accanto alla scheda lascerebbe scegliere il compositore) e niente ripiego sul silenzio (un compositore lento su scheda vera darebbe lo stesso silenzio); nessuna eccezione per compositore | T1c: senza 3D (VM `virtio-vga` senza virgl, server senza scheda) il compositore non ha DMA-BUF, la negoziazione muore con «no more input formats» e il ripiego di `scheda_da_abbandonare` vive dentro un fotogramma che non arriva ⇒ «Ammesso» e desktop mai; il figlio rimontava sulla scheda ogni 5 s per sempre | `[M]` 29 set, binari di `costruisci-tutti.sh`, Chrome vero: **VM** debian13-gnome PASS (desktop a 4,5 s; prima del ripiego rapido 10 s), arch-kde PASS, ubuntu2604-gnome PASS (col binario vecchio 0 su 3); il rifiuto e il ripiego stanno a **7 ms** dalla cattura avviata. **Scatole Intel** (binario debian13 `3e026237`, PAM nuovo + `utenti-negati`), giro `17-cura-copia-zero` f001 f003 f004 f011 f016 f018 f018b × 4 desktop × Chrome e Firefox: **208 PASS / 0 FAIL / 0 BLOCKED** (25 min); nel registro 14 palchi per desktop tutti «SCHEDA (DMA-BUF, copia zero)», 0 «MEMORIA», 0 «RIFIUTATA»; GNOME e KDE 14/14 «i fotogrammi arrivano come DMA-BUF», XFCE e LXQt 28 «PRIMO fotogramma della SCHEDA» e 0 ripieghi wlroots | no (scatole tornate a `4fb3287d` e al PAM di prima) |
| — | ⚠ **non fatto, annotato**: `figlio.c:4684` apre sempre `renderD128` per il codificatore: con due schede può prendere quella sbagliata; va scelto dal driver (§4.4). Fuori dalla T1a per mandato | — | — | — |
| c95146c | **T3, linea B — il pacchetto `.deb`** (`packaging/debian/`, debhelper 13, `dh_installsystemd`): `/usr/libexec/remotix/remotix`, `/usr/share/remotix/{pagina.html,remotix.conf}`, `/etc/remotix/remotix.conf.d/` vuota; **conffile** `/etc/pam.d/remotix` (il PAM di Debian, `src/remotix.pam`) e `/etc/remotix/utenti-negati` (root); `remotix.service` da root (`KillMode=mixed`, `Restart=on-failure`, `--nome %H`, `--journal`, nessuna opzione di banco; certificato generato dal programma al primo avvio, `certificati.c:302`); il permesso di KWin `/usr/share/applications/org.kde.remotix.desktop` **identico byte per byte** a quello che scrive `kwin.c:606`; le tre cinture nei percorsi del **fornitore** (`/usr/share/polkit-1/rules.d/50-…`, `/usr/lib/systemd/{logind,sleep}.conf.d/`) — ⚠ **dipendono da D4, aperta**; `tmpfiles.d` (`/var/lib/remotix` 0700, `/run/remotix`); postinst: le persone (UID_MIN..UID_MAX, shell vera) nei gruppi LETTI dai nodi `/dev/dri`, ogni coppia annotata in `/var/lib/remotix/modifiche.log` come DIRETTA o PREESISTENTE, una coppia già annotata non si riscrive (R5); postrm purge: via **solo** le DIRETTE, poi `/var/lib/remotix`. **Dipendenze**: `dpkg-shlibdeps` + `libpam-systemd libpam-modules passwd systemd dbus-user-session` (usate a tempo di esecuzione, dpkg non le vede); **Recommends** `va-driver-all \| va-driver, labwc, wlr-randr, xwayland` e, solo su Ubuntu, `gnome-session \| plasma-workspace \| xfce4-session \| lxqt-session` (D8 aperta: la sessione vanilla solo se non c'è già un altro desktop). `Static-Built-Using: ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0)` (D2 chiusa). `src/costruzione/costruisci-deb.sh`: copia dell'albero, `debian/changelog` con versione e data del commit (⇒ `SOURCE_DATE_EPOCH`), `dpkg-buildpackage -b` nel contenitore, lintian, controlli R4/R13/R14/R23 sul pacchetto FINITO; `Contenitore.debian13`/`.ubuntu2604` con uno strato di attrezzi `.deb` in coda | T3 (§6.1-§6.4): la ricetta nativa, dipendenze calcolate e non scritte a mano (`LEZIONI.md` §2.5-bis) | `[M]` 29 set, 313ccfc: **compila** Debian 13 e Ubuntu 26.04; **lintian 0 E / 0 W**, 1 informazione (`systemd-service-file-missing-documentation-key`), 3 sostituzioni motivate (`pagina.html` non è documentazione; `systemctl reload systemd-logind`, che `deb-systemd-invoke` non sa fare); **R13** 0 frasi della funzione di banco nel binario estratto dal `.deb`, 1 nel controllo positivo (`rcp.o` con `BANCO_ACCESO 1`), nessuna opzione di banco nell'unità; **R14** nessun file del banco; **R4** `ldd` 108 (Debian) e 111 (Ubuntu) librerie, 0 mancanti, ngtcp2/nghttp3 non dinamiche; **R23** due costruzioni in due copie pulite ⇒ `.deb` **identici** byte per byte (Debian `a907d059…`, Ubuntu `966fcd73…`). Prove in VM: vedi §13.2 | sì, nelle VM di prova (poi tolto) |
| — | ⚠ **non fatto, annotato dalla T3** (tocca il C, fuori mandato): (1) `kwin.c:606` `kwin_scrivi_permesso()` deve smettere di **scrivere** `/usr/share/applications/org.kde.remotix.desktop` (è del pacchetto) e solo verificarlo — oggi non lo riscrive perché lo trova uguale; (2) `figlio.c:1525` `iscrivi_ai_gruppi_della_scheda()` iscrive alla prima connessione chi è nato dopo l'installazione ma **non lo annota** in `/var/lib/remotix/modifiche.log`: il purge non lo toglie; (3) con `--journal` sotto systemd **ogni riga compare due volte** nel journal (una da stderr, una strutturata): il programma dovrebbe tacere su stderr quando `JOURNAL_STREAM` è il suo stderr; (4) il certificato di §6.6.13 (`0-generato.pem`, `/etc/remotix/certificati.d/`) non c'è: il pacchetto si appoggia a quello di oggi (`pagina.pem`/`sessione.pem`, marca `.nostro`); (5) `/usr/bin/remotix` (verifica, stato…) e la configurazione vera sono di T4: oggi `remotix.conf` è un `EnvironmentFile` provvisorio | — | — | — |
| a3b722a…a6d0908 | **T3, linea D — il pacchetto Arch** (`packaging/arch/`): `PKGBUILD` che costruisce dal **tarball del commit** (`costruisci.sh`: `git archive` di `src/`, `banchi/rcp/`, `packaging/arch/`, poi `makepkg` nel contenitore `arch` come utente, namcap in un contenitore usa-e-getta, lista nera R14, `SOURCE_DATE_EPOCH` = data del commit); ngtcp2 1.25.0 e nghttp3 1.18.0 **statiche** dai tarball ufficiali con sha256 fissata, costruite in `build()` (D2 chiusa; ⓘ per §10.6 su Arch si potrebbe usare `libngtcp2`/`libnghttp3` di sistema, già 1.25 col ponte crypto_ossl: resta dentro per uniformità); `-ffile-prefix-map` (i `__FILE__` delle assert di ngtcp2 portavano `$srcdir` nel binario); `!lto !debug`. **Percorsi di Arch**: il binario in `/usr/lib/remotix/remotix` (Arch non usa libexec: namcap «ELF outside of a valid path»), `pagina.html` in `/usr/share/remotix/`, unità `remotix.service` (da root, `KillMode=mixed`, `LimitRTPRIO=20`, `LimitNICE=-11`, `Restart=on-failure`, `REMOTIX_PORTA=7447` e `REMOTIX_NOME=%H` cambiabili con un drop-in, nessuna opzione di banco), `tmpfiles.d` (`/var/lib/remotix` 0700), PAM `src/remotix.pam.arch` in `/etc/pam.d/remotix` e `/etc/remotix/utenti-negati` (root) in `backup=()` (**D3 aperta**: il `pam_faillock` arriva con `system-auth` di pambase, non aggiunto né tolto), il permesso di KWin `/usr/share/applications/org.kde.remotix.desktop` **identico byte per byte** a quello di `kwin_scrivi_permesso()` con `Exec=/usr/lib/remotix/remotix`, il servizio firewalld **definito** (`/usr/lib/firewalld/services/remotix.xml`, nessuna zona toccata); ⛔ **§10.12**: le tre cinture **spente** in `/usr/share/remotix/cinture/` (le monta il motore, D4), `remotix.install` **non** iscrive ai gruppi e non accende niente (post_install: solo un avviso; post_upgrade: `try-restart`, il posto dove richiamare il motore; pre_remove: `disable --now`; post_remove: via certificati e ban). **Dipendenze**: per **soname** (`libavcodec.so=63-64`, `libssl.so=3-64`, … calcolati da makepkg sul binario) + i pacchetti; più `labwc wlr-randr` (XFCE/LXQt, nessun gruppo di Arch li porta; labwc tira `ttf-font`, il carattere di labwc #2525) e `pipewire wireplumber pipewire-pulse` (il gruppo xfce4 non ha l'audio). ⭐ **Rolling release**: legame al **soname**, non alla versione esatta: ffmpeg si aggiorna libero finché l'ABI resta, e a un cambio di soname `pacman -Syu` **rifiuta** («breaks dependency») finché non si ricostruisce — la versione esatta bloccherebbe ogni aggiornamento di ffmpeg, sicurezza compresa, e con lui tutto il `-Syu`. A carico nostro: ricostruire a ogni soname nuovo. `Contenitore.arch`: + `labwc wlr-randr wireplumber pipewire-pulse` (makepkg vuole vedere installate anche le dipendenze di esecuzione) | T3 (§6.1-§6.4), §10.6, §10.12 | `[M]` 29 set, a6d0908: **compila** pulito (0 avvisi di REMOTIX), `make dipendenze` verde; `check()`: `BANCO_ACCESO 0`, ldd senza ngtcp2/nghttp3 né mancanti. **namcap**: 1 E — licenza `LicenseRef-REMOTIX` senza file in `/usr/share/licenses/remotix/` (manca una licenza del prodotto: da decidere); W — `libgcc` implicita (normale), «forse non servono» `systemd labwc wlr-randr pipewire wireplumber pipewire-pulse` (non collegate: servono a esecuzione, voluto); PKGBUILD pulito. **R14** 30 voci, nessuna della lista nera. **R23** due costruzioni ⇒ pacchetto **identico** byte per byte (`51d6ea2f…`); senza `SOURCE_DATE_EPOCH` stesso binario, pacchetto diverso solo per `builddate`. ⚠ R13 solo per `BANCO_ACCESO 0` nel sorgente: la ricerca delle frasi nel binario estratto (come la linea B) non è fatta. Prove in VM: §13.2 | sì, nelle VM di prova (poi tolto) |
| — | ⚠ **non fatto, annotato dalla linea D** (tocca il C): (1) come la linea B, `kwin_scrivi_permesso()` deve solo verificare (su Arch `[M]` il programma trova il file del pacchetto uguale e scrive «c'e' gia'»); (2) **R40 rosso a metà**: il pacchetto da solo non accende niente, ma `systemctl start remotix` a mano **parte** — manca il controllo `RX-INST-001` (§10.12 punto 3); (3) il prodotto a esecuzione scrive fuori dal pacchetto e dopo `-Rns` resta: `~/.local/state/remotix/sessione.log` (DIRETTA) e su XFCE le impostazioni di energia dell'utente (`xfce4-power-manager.xml`, scritta da `sessione.c`: DIRETTA ma voluta persistente da §8.2) — il motore deve dire che cosa ne fa | — | — | — |
| aec8402 | **T4, linea A, prima parte — il motore `remotix-install`** (`installatore/`, Go statico, `CGO_ENABLED=0`, 4 MB; unica dipendenza `godbus/dbus` v5.1.0 in `vendor/`, costruzione senza rete). **Oggetti** `remotix-install/1` (profilo, rapporto di compatibilità, piano, insieme risolto — vuoto, senza pacchetti —, registro, rapporto di verifica, certificato JSON + testo) ed **eventi JSON a riga** (`--eventi`, il canale di TUI e GUI). **Stati** di §6.6.2 con le sole transizioni del disegno (`stati.go`), stato in `<operazioni>/<id>/stato` scritto atomico, serratura `flock`. **Registro** `registro.jsonl`: INTENZIONE (con lo stato di prima e l'origine) → effetto → FATTA/FALLITA, fsync del file e della cartella; la riga finale troncata si toglie e si dice (`RX-RIPRESA-003`); **ripresa** con la tabella di §6.6.3 (niente ⇒ la fa; INTENZIONE ⇒ `controlla`: completo ⇒ FATTA, assente ⇒ rifà, a metà ⇒ annulla e rifà, **estraneo** ⇒ BLOCCATA `RX-RIPRESA-001`; FATTA ⇒ controllo di coerenza). **Azioni** con fai/controlla/annulla/annullata/vincoli, reversibilità e origine: `scrivi-file` (salvataggio del file di prima nella cartella dell'operazione, temporaneo a nome fisso + rinomina, cartelle create tolte se vuote), `aggiungi-utente-a-gruppo` (`gpasswd`; PREESISTENTE anche come gruppo principale, mai tolto), `abilita-unita` (D-Bus systemd1: GetUnitFileState, EnableUnitFiles, DisableUnitFiles, Reload), `regola-firewall` (D-Bus FirewallD1, vive e permanenti, solo le regole nostre si tolgono; ufw e nftables riconosciuti e dichiarati `RX-FW-004`); **dichiarati e non fatti** (`installa-desktop`, `installa-pacchetti`, `aggiungi-deposito`, `attiva-cintura`, `accendi-servizio`): stanno nel piano, e l'operazione si ferma prima di toccare con `RX-AZIONE-004`. **PREFLIGHT** in sola lettura: os-release e famiglia, immutabili, systemd, desktop e pacchetti dall'archivio (dpkg e pacman dai loro file, **una** `rpm -q` per le famiglie RPM), depositi di terzi, schede e nodi col driver (NVIDIA proprietaria), H.264 dalla libavcodec (h264_vaapi, libx264) e dai driver VA-API, SELinux/AppArmor, porta in ascolto (`/proc/net`), firewall (firewalld sul bus, i file di ufw, nftables come unità), PAM della famiglia (e `pam_faillock`, `pam_systemd`), OpenSSL, `KillUserProcesses` (logind sul bus ⇒ VERIFICATO), gruppi `video`/`render`, caratteri scalabili; ogni fatto RILEVATO/VERIFICATO/SCONOSCIUTO, i programmi lanciati nel profilo (R41). **Impronta** vincolante (sha256 del testo canonico) + annotata; il piano la porta, `applica` la rifà e dice gli elementi cambiati (`RX-PIANO-001`). **Consenso**: approvazione legata al digest del piano (`approva`, o `--approva` a mano); senza, RIFIUTATA. **Catalogo** `catalogo/catalogo.json` (incorporato; versione, sequenza, scadenza, motore minimo, firma separata prevista): la matrice di §3 e §3.1, Ubuntu 24.04 e Mint 22 fuori (D7), derivate, escluse, condizioni `C-…` (depositi H.264, `gnome-session`, `breeze6-wallpapers`, `wlr-randr`, carattere scalabile, EPEL per KDE su Alma, `C-DESKTOP`), versioni minime dei componenti; `remotix-install catalogo --tabella` **genera** le tabelle di §3.1. **Senza desktop** (§10.7): la scelta nel piano coi desktop del catalogo e quello di riferimento già selezionato; «no» ⇒ BLOCCATA `RX-DESKTOP-001`. **`installazione.json`** accanto alle operazioni (id dell'operazione CONFERMATA, solo mestieri `installazione`/`aggiornamento`: informativo, §10.12); `remotix-install aggiornato` per gli script del pacchetto (dice se certificata, rifà la verifica, TryRestartUnit sul bus). **Bilingue** (§10.15): lingua da LANGUAGE, LC_ALL, LC_MESSAGES, LANG o `--lingua`; codici in `codici.go` + `codici_en.go`, il resto in `testi.go` | §6.0, §6.6, §8 (R1, R2, R5, R28-R32, R36), DECISIONI §10.10, §10.12, §10.14, §10.15; il motore deve girare da root prima di qualunque pacchetto: niente Python né librerie | `[M]` 30 set, `go test`: **120 PASS / 0 FAIL** — il motore **ucciso con SIGKILL** (processo figlio, niente pulizia) in 35 punti dell'applicazione (per ognuna delle 7 azioni: prima dell'intenzione, dopo l'intenzione, a file scritto a metà, a effetto fatto, dopo FATTA; e in 4 transizioni) poi `riprendi` ⇒ **CONFERMATA** con la macchina **identica** a quella di un giro senza interruzioni e nessuna azione FATTA due volte; gli stessi 35 poi `annulla` ⇒ **ANNULLATA** con la macchina identica a prima (la regola del firewall e il membro di `video` che c'erano restano); ucciso in 16 punti **durante l'annullamento** ⇒ la ripresa finisce l'annullamento; interrotta prima di toccare (6 stati) ⇒ BLOCCATA senza toccare, e un `applica` nuovo parte; riga di registro troncata; FATTA disfatta da altri ⇒ BLOCCATA, poi ANNULLATA (o ANNULLATA_IN_PARTE se il file è stato cambiato dall'amministratore, che resta suo); passo che fallisce (R28 in piccolo) ⇒ ANNULLATA; impronta cambiata (R31) ⇒ BLOCCATA senza toccare; controllo senza risposta (R32) ⇒ UNKNOWN e mai CONFERMATA; idempotenza (R5) ⇒ tutto PREESISTENTE, zero scritture. Due **mutazioni** a mano (ripresa che rifotografa la macchina invece di usare lo stato di prima del registro; gruppo sempre PREESISTENTE) ⇒ rosse subito (`TestAnnullaDopoInterruzione`, più sottoprove ciascuna): le prove hanno i denti. **R1** (`prove/r1-contenitori.sh`, impronta di `/etc` con permessi, proprietari, ore e sha256): **identica** dopo `verifica` e `verifica --json` in debian:13 (161 voci), fedora:44 (1189), archlinux (948), tumbleweed (130). **Dal vero** (`prove/systemd-giro.sh`, Fedora 44 con systemd acceso in podman): piano → approva → applica ⇒ **CONFERMATA**, unità `enabled` via D-Bus, `provamotore` in `video` via `/usr/bin/gpasswd`, i due programmi lanciati nel registro; un passo che fallisce dopo i due file e l'unità ⇒ **ANNULLATA**, unità di nuovo `not-found`, `/etc` identica nei contenuti, permessi e proprietari (non nelle ore delle cartelle). Sul portatile (Debian 13, Intel): `verifica` legge logind sul bus (VERIFICATO), la libavcodec con h264_vaapi e libx264, 7 driver VA-API. ⚠ firewalld non parte in podman senza root: la regola del firewall via D-Bus è provata solo coi finti | no |
| — | ⚠ **non fatto, annotato dalla linea A** (T4 prima parte): (1) **H.264 VERIFICATO nel PREFLIGHT**: col codice di prima (un fotogramma codificato da `ffmpeg -f null`) il portatile dava `h264.scheda = si VERIFICATO`; ffmpeg non è nell'elenco chiuso di §10.14, e il PREFLIGHT ora dice SCONOSCIUTO (la prova la farà 7a col binario di REMOTIX) — metterlo nell'elenco è una riga, **decisione dell'utente**; (2) la **firma** del catalogo e del motore (TRUST): modello pronto, schema e chiavi con D11 (T8); oggi `--senza-firma` esplicito e annotato; `sequenza` del catalogo non ancora usata contro il ritorno a un catalogo vecchio; (3) TUI, GUI (D12, D13), `install.sh`, il file di risposte, la lingua nel file di risposte; (4) i **testi del catalogo** (motivi, note, la tabella di §3.1) e i dettagli diagnostici del registro sono solo italiani; (5) BLOCCATA **dopo aver toccato** la macchina (§6.6.3, ultima riga) il motore la tiene **aperta** (se ne esce con `riprendi` o `annulla`): §6.6.2 dice «BLOCCATA: niente è stato toccato» — scelta del motore, da confermare; (6) il nome del file di stato: il motore scrive `/var/lib/remotix/installazione.json`, la linea B aveva proposto `installazione-confermata`; (7) R2 (difetti noti col codice) provato solo su radici finte, non sulle VM | — | — | — |
| 165906c | **T3, linea C — il pacchetto `.rpm`** (`packaging/rpm/remotix.spec`, UN solo spec coi rami `0%{?fedora}` / `0%{?rhel}` / `0%{?suse_version}` come `cockpit.spec`): `/usr/libexec/remotix/remotix`, `/usr/share/remotix/{pagina.html,remotix.conf}`, `remotix.service` (uguale nella sostanza a quello del `.deb`: root, `--nome %H`, `--journal`, `KillMode=mixed`, nessuna opzione di banco), `tmpfiles.d` (`/var/lib/remotix` 0700, `/run/remotix`); PAM `.fedora` in `/etc/pam.d/remotix` `%config(noreplace)`, `.suse` in **`%{_pam_vendordir}`** (`/usr/lib/pam.d`); `/etc/remotix/utenti-negati` (root) `%config(noreplace)`, `/etc/remotix/remotix.conf.d/` vuota; il permesso di KWin identico byte per byte a `kwin.c`; certificati, marche `.nostro`, `ban` e `ban.nuovo` **`%ghost`** (la disinstallazione li toglie). **§10.12**: niente `%systemd_post`/`%service_add_post` (applicherebbero il *preset*: con «enable \*» il servizio si abiliterebbe da solo), niente gruppi, cinture **spente** in `/usr/share/remotix/cinture/`, firewalld solo **definito** (`/usr/lib/firewalld/services/remotix.xml`); restano `%systemd_preun` e `%systemd_postun_with_restart` (*try-restart*). **Dipendenze**: le librerie le calcola rpmbuild (anche `libssl.so.3(OPENSSL_3.5.0)`: il minimo di OpenSSL non va scritto); a mano solo quel che rpm non vede, **condizionato al desktop** (§10.7, nessun desktop tirato dentro): Fedora `(labwc if xfce4-session)`, `(xorg-x11-server-Xwayland if xfce4-session)`, `(labwc if lxqt-session)`, `(wlr-randr if lxqt-session)`, `(default-fonts-core-sans if labwc)`, `firewalld-filesystem`, Recommends `mesa-dri-drivers`, `(libva-intel-media-driver or intel-media-driver)`; openSUSE le stesse con `xwayland`, `((google-droid-fonts or dejavu-fonts or google-noto-sans-fonts or liberation-fonts) if labwc)` (labwc #2525), `(breeze6-wallpapers if plasma6-workspace)`, Recommends `Mesa-libva`, `intel-media-driver`; Alma niente in più (EPEL/CRB e RPM Fusion sono passi del motore). `Provides: bundled(ngtcp2) = 1.25.0`, `bundled(nghttp3) = 1.18.0` (D2 chiusa), controllate in `%build` con `pkg-config`. Flag di costruzione della distribuzione nell'**ambiente** (`CFLAGS ?=` del Makefile: sulla riga di comando di make scavalcherebbero i `+=`); su openSUSE `-fPIE -pie`. **`src/remotix.pam.fedora`: `pam_selinux` close/open COMMENTATO — provvisorio, la decisione è di T6** (§11.1 B). `costruisci-rpm.sh`: archivio dall'albero, `rpmbuild -ba` e rpmlint nel contenitore del bersaglio, controlli sul pacchetto finito (R4, R13 col controllo positivo, R14, XML del servizio firewalld) | T3 (§6.1-§6.4): la ricetta nativa per Fedora, Alma, Tumbleweed, Leap; §10.12 (pezzi inerti) | `[M]` 29 set: **4 su 4 costruiti** (`remotix-0.17.0-1.fc44`, `.el10`, TW, Leap); `ldd` 0 mancanti, ngtcp2/nghttp3 non dinamiche; **R13** 0 frasi di banco nel pacchetto, 1 nel controllo positivo, nessuna opzione di banco nell'unità; **R14** nessun file del banco. **rpmlint** Fedora/Alma: 0 E veri, 4 W `invalid-license` (licenza non scelta), 2 `invalid-url` (Source0 locale), 2 `no-%check-section`, 1 `no-documentation`; 64-65 E `spelling-error` (testo italiano). TW/Leap in più: E `systemd-service-without-service_add_pre/post` (**voluti**, §10.12), E `no-binary` (debugsource), W `dir-or-file-outside-snapshot` (TW), `unstripped-binary-or-object` (debuginfo), `strange-permission` (sorgenti 664), `post-without-tmpfile-creation` (Leap: il macro lì è vuoto); prima delle correzioni anche `position-independent-executable-suggested` (curato), `macro-in-comment`, `polkit-file-unauthorized` (sparito con le cinture spente). Prove in VM: §13.2 | sì, nelle VM di prova (poi tolto) |
| — | ⚠ **non fatto, annotato dalla linea C** (tocca il C o il motore): (1) come le linee B e D, `kwin_scrivi_permesso()` (`kwin.c:48`, `:606`) deve solo **verificare** il file del pacchetto: `[M]` su TW il programma lo trova uguale («c'e' gia'») e `rpm -V` resta pulito, ma se il binario cambia percorso lo riscriverebbe; (2) il **registro della sessione** in `~/.local/state/remotix/sessione.log` resta nella casa dell'utente dopo la disinstallazione (visto su 4 VM su 4): ✅ **deciso il 1 ott 2026: lo toglie il motore** (riga 9991f09); (3) le persone iscritte ai gruppi **dal prodotto** alla prima connessione (`figlio.c`, `iscrivi_ai_gruppi_della_scheda`) vanno solo nel journal: nessun registro le vede, la disinstallazione non le toglie; (4) **firewalld**: aprire e poi richiudere il servizio lascia `/etc/firewalld/zones/public.xml` (+ `.old`) che prima non c'era (Fedora, Alma): il ritorno indietro del motore deve toglierlo se l'ha creato lui; (5) su Alma **RPM Fusion va in conflitto con EPEL** (`libavcodec-freeworld` 7.1.5 vuole `libavcodec-free` ≥ 7.1.5, EPEL ha 7.1.2): serve `--allowerasing`, che toglie `libavcodec-free` (REMOTIX resta soddisfatto dalla libreria di RPM Fusion); su Fedora `libavcodec-freeworld` **retrocede** tutta ffmpeg-free 8.1.2 → 8.0.1 (CON_FOTOGRAFIA): D5 deve dirlo nel consenso | — | — | — |
| 56c93d3 | **T4-T5, linea A, seconda parte — le azioni vere di §10.12 e la disinstallazione.** `installa-pacchetti` (`gestore.go`, `azione_pacchetti.go`): Fotografa = ACQUISITION — il file del piano copiato nella cache dell'operazione e confrontato col suo sha256, poi il gestore RISOLVE, SCARICA e VERIFICA; l'insieme risolto (nome, versione, origine, sha256, nuovo/aggiornato) va nell'intenzione e in `insieme-risolto-<azione>.json`; Fai installa dalla cache; a metà ⇒ il rimedio del gestore (`dpkg --configure -a`…) e si rifà; Annulla toglie SOLO i pacchetti nuovi, dopo una simulazione che rifiuta se ne toglierebbe altri (`RX-PACCHETTI-002`); gli aggiornati restano e si dichiarano (INDIRETTA nel certificato). apt e dnf provati; zypper e pacman scritti, **non provati**. `aggiungi-deposito`: l'archivio firmato di REMOTIX (chiave in file suo, `Signed-By`/`gpgkey`, `rpm --import`; ESATTA) ed EPEL (+CRB), RPM Fusion, Packman (AL_MEGLIO, consenso D5): i pacchetti e le chiavi arrivati col deposito si riconoscono (rpm prima/dopo) e si tolgono. `attiva-cintura` (le tre di `/usr/share/remotix/cinture/` in `/etc`, consenso D4, ricarica di logind sul D-Bus). `accendi-servizio` (EnableUnitFiles + StartUnit; fatto solo con la porta in ascolto TCP e UDP). `installa-desktop` (R38: i gruppi ufficiali dal catalogo, `policy-rc.d` nostro durante la transazione su Debian, poi il display manager abilitato/acceso dall'installazione si spegne e il bersaglio d'avvio torna com'era). **Disinstallazione** (`disinstalla.go`): `remotix-install disinstalla [--purge]` fa un piano dal registro dell'installazione confermata — un passo `disfa` per ogni passo DIRETTO, all'indietro (fare = il suo annulla; annullare = il suo fai) — e, dopo lo spegnimento del servizio, `chiudi-sessioni` (logind, SOLO `Service=remotix`, IRREVERSIBILE); a CONFERMATA toglie `installazione.json`. `piano --installa --pacchetto F [--utente] [--deposito] [--apri-firewall] [--senza-cinture]`: depositi → desktop se manca → pacchetti → gruppi della scheda (letti dai nodi) → cinture → firewall → servizio. **BLOCCATA** = solo «niente toccato»; dopo aver toccato è INTERROTTA (`RX-RIPRESA-001`). **7a**: `remotix --prova-codifica` (elenco chiuso) — il binario di oggi non la ha (uscita 2) ⇒ UNKNOWN, CONFERMATA_A_CONDIZIONI (`C-LIMITE`); PREFLIGHT legge la famiglia del driver VA dai pacchetti (`h264.famiglia_driver`) | DECISIONI §10.7, §10.12, §10.14, §10.16; §6.0, §6.5-bis, §6.6.3-§6.6.6; R6, R28, R38, R43 | `[M]` 30 set. **go test: 160 PASS** (in più: pacchetti, cintura e servizio finti nel piano di prova, con uccisioni in ogni punto; disinstallazione uccisa in 6 punti ⇒ CONFERMATA con la macchina com'era salvo l'INDIRETTA dichiarata, la sessione REMOTIX chiusa e quella ssh viva; disinstallazione annullata ⇒ l'installazione torna, ANNULLATA_IN_PARTE per la chiusura IRREVERSIBILE; desktop senza grafica). **debian13-gnome «cliente»** (`17-t4-motore.sh`, .deb 37a286e): verifica → piano (7 passi) → applica in **8 s: CONFERMATA_A_CONDIZIONI** — 11 pacchetti alla versione risolta, `prova` messa in `render` (in `video` c'era già: PREESISTENTE), 3 cinture, servizio attivo con 7447 TCP+UDP, `installazione.json`; **Chrome PASS** (desktop gnome); poi `disinstalla --purge` in **20 s: CONFERMATA** — 0 processi del desktop (gnome-shell 0), **l'orologio della sessione ssh di `prova` batte ancora** (R43), `prova` di nuovo solo in `video`, remotix e le 10 dipendenze tolte, nessun pacchetto cambiato. R6 contro «prima»: DIRETTA rimasta solo la storia del motore in `/var/lib/remotix/operazioni` (col .deb nella cache); INDIRETTE `/etc/group-`/`gshadow-` (copie di gpasswd), ore delle cartelle di `/usr`, cache di icone e mime; estranee CUPS e fwupd. **debian13 nuda** (R38, `DESKTOP=lxqt`): piano con la domanda sul desktop, risposta lxqt ⇒ **1140 pacchetti** + REMOTIX in 412 s, `sddm` installato ma **disabled/inactive**, bersaglio d'avvio invariato, niente `policy-rc.d` rimasto; **Chrome PASS «desktop lxqt»**; disinstallazione CONFERMATA in 296 s (i 1140 tolti); restano, AL_MEGLIO, gli utenti e i gruppi di sistema creati dagli script dei pacchetti (Debian-exim, colord, dnsmasq…). **alma10-gnome-iso** (`17-t4-alma.sh`, firewalld acceso con la 7447 chiusa): deposito EPEL+CRB, htop via dnf (3 pacchetti), file, unità, **porta via D-Bus**, poi un gruppo con un utente inesistente ⇒ **ANNULLATA**: pacchetti rpm identici a prima, firewall (vive e permanenti) identico; restano solo `public.xml.old` (copia di firewalld), `ld.so.cache`, CUPS. Lo stesso piano con un utente vero ⇒ CONFERMATA, da fuori `7447/tcp` e `/udp` aperte vive E permanenti. Tre scoperte dal vero, curate: (1) apt 3.0 con `--no-download` e un .deb locale si ferma («Pathname to install is not absolute»): si installa senza, e «controlla» confronta ogni versione; (2) `epel-release` porta `selinux-policy-*-extra` e dnf importa due chiavi, e `dnf remove gpg-pubkey-…` esce 0 senza toglierle: ora rpm prima/dopo e `rpm -e` per le chiavi; (3) **TerminateSession non basta**: la sessione del figlio è «closing» dalla nascita (§5.2) e dopo 60 s lo scope ha ancora `remotix` e `gnome-session-binary`; il desktop GNOME vive in `user@1001.service`, NON nello scope. Con `KillSession` (SIGTERM dopo 10 s, SIGKILL dopo 20 s, sempre sulla sola sessione) il capo muore e il desktop si chiude da sé | no |
| — | ⚠ **da fare nel prodotto** (linea A, §6.5-bis): `remotix --prova-codifica [--nodo /dev/dri/renderDN]` — un fotogramma H.264 codificato come in sessione; **uscita 0** e una riga `PROVA-CODIFICA scheda <nodo> h264_vaapi` o `PROVA-CODIFICA software libx264`; **uscita 1** se non codifica; niente rete, niente file scritti. Oggi il binario risponde 2 (l'aiuto) e il motore lo dichiara UNKNOWN. ⚠ **non fatto, annotato dalla linea A**: (1) zypper e pacman mai provati su una macchina vera (T5, giri su Tumbleweed e Arch); (2) `installa-desktop` dnf/zypper/pacman: i nomi dei gruppi del catalogo (`@^…`, `pattern:…`) non provati; (3) R29, e 7a/7b oltre a codifica e porta (librerie viste con l'uid di un inquilino, PAM che rifiuta, certificato TLS); (4) la storia del motore resta in `/var/lib/remotix/operazioni` dopo la disinstallazione, col pacchetto nella cache: tenerla (è il «dnf history» di REMOTIX) o sfoltirla è da decidere; (5) su LXQt dopo la disinstallazione restano 18 processi di `prova` nel gestore d'utente (la sessione ssh lo tiene vivo): da guardare se sono del desktop chiuso; (6) i punti (5) e (6) della riga di aec8402 sono chiusi (BLOCCATA → INTERROTTA; `installazione.json`) | — | — | — |
| (questo commit) | **§6.5-bis, il file di KDE**: `kwin_scrivi_permesso()` diventa `kwin_verifica_permesso()` (`kwin.c`, `kwin.h`, `main.c`): REMOTIX **non scrive più** `/usr/share/applications/org.kde.remotix.desktop`, lo legge con `GKeyFile` e controlla che ci sia (**RX-KDE-001**), che il primo campo di `Exec=`, reso canonico con `realpath`, sia il binario che gira (`/proc/self/exe` canonico, come confronta KWin: `/usr/libexec/remotix/remotix` su deb e rpm, `/usr/lib/remotix/remotix` su Arch; **RX-KDE-002**) e che `X-KDE-Wayland-Interfaces` contenga `zkde_screencast_unstable_v1` (**RX-KDE-003**); se no una riga ⛔ nel registro d'avvio col codice e il rimedio «reinstallare REMOTIX con l'installatore». **Il banco**: `banchi/11-scatole/11-accendi.sh prodotto` mette lui il file in ogni scatola (come il pacchetto, che non guarda il desktop), stesso contenuto del pacchetto con `Exec=/opt/remotix/remotix`; copiato sul server in `/media/REMOTIX/rete11/` e nella copia `controllo` | il file è del pacchetto (identico byte per byte in `packaging/{debian,rpm,arch}`): riscriverlo darebbe due verità su che cosa è installato (`dpkg -V`, `rpm -V`); nelle scatole nessun altro lo metteva, e senza il banco KDE non si sarebbe più visto | `[M]` 29 set, scatola `kde`, binario 60ce7d23: senza file ⇒ RX-KDE-001 e il file **resta assente** dopo l'avvio; `Exec=/usr/libexec/remotix/remotix` ⇒ RX-KDE-002; senza la riga delle interfacce ⇒ RX-KDE-003; col file del banco ⇒ «verificato (e' del pacchetto: non lo scrivo)», data e misura del file **uguali** prima e dopo l'avvio. Suite corta sulle 4 scatole: **208 PASS / 0 FAIL / 0 BLOCKED** (f001 f003 f004 f011 f016 f018 f018b, Chrome e Firefox, 25 min, giro `17-cure-6.5bis`), KDE compreso col file messo dal banco, copia zero intatta (strada SCHEDA 28-29 per scatola, MEMORIA 0); poi scatole tornate a 4fb3287d e PAM d1734958 (il binario vecchio, col file del banco, dice «c'e' gia'»). 7 bersagli su 7 compilano senza avvisi | sì |
| (questo commit) | **§6.5-bis, i gruppi alla prima connessione**: `figlio.c` `iscrivi_ai_gruppi_della_scheda()` annota ogni iscrizione fatta da REMOTIX in **`/var/lib/remotix/gruppi-iscritti.jsonl`**, una riga per gruppo, **solo** per i gruppi in cui l'utente non c'era (chi c'era già, anche come gruppo principale, è PREESISTENTE: né iscritto né annotato). ⭐ **Il formato, per la linea del motore** (UTF-8, una riga JSON per riga, `\n` in fondo, stringhe con l'escape JSON di `"`, `\` e dei controlli): `{"formato":"remotix-gruppi/1","data":"2026-09-29T20:28:19Z","utente":"c18u752","uid":4013,"gruppo":"render","gid":991,"origine":"DIRETTA","da":"REMOTIX alla prima connessione"}` — `data` in UTC ISO 8601 al secondo, `uid`/`gid` numeri del momento dell'iscrizione. **Scrittura**: cartella aperta con `O_DIRECTORY\|O_NOFOLLOW`, dev'essere di root e non scrivibile da altri (se manca si crea 0700); file con `O_WRONLY\|O_APPEND\|O_NOFOLLOW` (nasce con `O_CREAT\|O_EXCL`, 0600, e allora `fsync` della cartella), dev'essere regolare, di root, non scrivibile da altri; ogni riga con **una** `write` e poi `fsync`; mai troncato né riscritto. Il file si apre **prima** di `usermod`, la riga si scrive **dopo** e solo se `usermod` è riuscito (un'iscrizione mai fatta annotata farebbe togliere un gruppo messo da altri). Se non si può annotare, l'iscrizione si fa lo stesso (sessione cieca è peggio, §4.2) e il registro dice ⛔ «iscrizione NON ANNOTATA» col rimedio `gpasswd -d`. Il motore alla disinstallazione: per ogni riga, se l'utente è ancora nel gruppo, lo toglie (DIRETTA); righe ripetute per la stessa coppia valgono una | la disinstallazione deve sapere chi ha messo REMOTIX in un gruppo (DIRETTA, si toglie) e chi c'era (PREESISTENTE, mai) — §6.6.4, R33; il journal ruota e il motore non lo legge | `[M]` 29 set, scatola `xfce`, `11-accendi.sh c18 xfce`: G SI · I SI · D SI (VERDE); prima `/var/lib/remotix` non c'era, dopo cartella `drwx------ root` e file `-rw------- root` con **2 righe** (render gid 991, video gid 44) e due righe «⭐ annotato in …» nel registro; il file tolto a fine prova | sì |
| (questo commit) | **§6.5-bis, la prova di codifica per la certificazione (fase 7a)**: `remotix --prova-codifica` (da solo, primo argomento; `figlio_prova_codifica()` in `figlio.c`): passa per **`codificatore_di()`**, la strada di una sessione vera — H.264, 8 bit (la base di §4.3), nessun tetto di livello, BGRx: `h264_vaapi` su `NODO_RENDERING` (`/dev/dri/renderD128`) con `POTENZA_RENDERING` e `QP_HARDWARE`, se non si apre il ripiego `libx264` con `CRF_SOFTWARE` — e codifica davvero un fotogramma sintetico 256×256 (al più 8 giri finché escono byte). ⭐ **Il contratto**: UNA riga JSON su stdout (il registro resta su stderr) `{"esito":"hardware"\|"software"\|"nessuno","codificatore":"h264_vaapi"\|"libx264"\|"","nodo":"/dev/dri/renderD128"\|"","motivo":"…"}`; codice d'uscita **0 se un fotogramma è uscito (hardware o software: quale lo dice `esito`) · 1 nessuno** (2 resta l'errore d'uso) — lo stesso codice che il motore della linea A aspettava (riga di 56c93d3); ⚠ **la riga invece è JSON, non `PROVA-CODIFICA …`**, e `--nodo` non c'è (il nodo è quello della sessione): `operazione.go` `provaCodifica` va adattato dalla linea del motore. `nodo` è pieno solo con «hardware»; con «software» il motivo porta il nodo provato e perché l'hardware non si è aperto. ⛔ «hardware» solo se il componente accetta superfici VA-API **e** un fotogramma è uscito con byte **e** i byte si sono riletti (`letto_dal_flusso`); ogni altra incertezza è «nessuno» col motivo. Niente rete, niente sessioni, niente certificati; **root non serve**, ma l'esito dipende dall'identità: chi non è nel gruppo del nodo vede «software» dove root vede «hardware» — la prova si fa con l'identità di cui si vuole sapere. `codificatore_di()` ora conserva la ragione dei due rifiuti (`rifiuto_hardware`, `rifiuto_software`) per il motivo | l'installatore deve dimostrare che la macchina codifica, e come, con la scelta del prodotto e non con un ffmpeg a parte (§6.0, e la nota (1) della linea A: ffmpeg non è nell'elenco chiuso) | `[M]` 29 set: VM `debian13-gnome` «cliente» (virtio-gpu) da utente e da root ⇒ `software`, `libx264`, 5313 byte, `avc1.641015` (motivi: «Invalid argument» da utente, «Input/output error» da root); nelle 4 scatole (Intel iHD 25.2.3), da root e da `provanic` (video, render) ⇒ `hardware`, `h264_vaapi`, `/dev/dri/renderD128`, 1619 byte, `avc1.640c15`, EncSliceLP — queste con la prima numerazione dei codici (3/4), la riga JSON è la stessa. Col binario finale 2db2df13: contenitore `debian13` ⇒ `software`, codice **0**; contenitore `fedora44` (ffmpeg-free, senza libx264) ⇒ `nessuno`, codice **1**, «il codificatore «libx264» non c'e' in questa libavcodec»; le 4 scatole da root ⇒ `hardware`, codice **0**. 7 bersagli su 7 compilano senza avvisi (Ubuntu 24.04 fuori, D7: l'immagine non nasce, OpenSSL 3.0) | sì |
| ad5bc1b | **T5, linea A — il desktop chiuso davvero, la storia, zypper e pacman.** `chiudi-sessioni` (§10.16): dopo le sessioni logind `Service=remotix`, il motore parla col **gestore d'utente** sul suo D-Bus privato (`/run/user/UID/systemd/private`, aperto a root) e ferma `graphical-session.target` e le unità che hanno processi nati nel desktop (riconosciuti dall'ambiente: `WAYLAND_DISPLAY`/`DISPLAY`; il bus di sessione non si ferma, se ne segnalano i soli processi grafici), toglie le due variabili dall'ambiente del gestore; solo se la persona non ha un altro desktop (una sessione `wayland`/`x11` non REMOTIX); mai `user@UID`, mai TerminateUser. **Storia**: `disinstalla` la tiene senza le cache dei pacchetti, `--purge` la toglie tutta (e `gruppi-iscritti.jsonl`). **`togli-iscrizione`**: le iscrizioni di REMOTIX alla prima connessione (`/var/lib/remotix/gruppi-iscritti.jsonl`, §6.5-bis) si tolgono come DIRETTE, i doppioni una volta. **`provaCodifica`** sul contratto JSON di `remotix --prova-codifica` (hardware ⇒ PASS; software ⇒ PASS + `C-RIPIEGO`; nessuno ⇒ FAIL; illeggibile ⇒ UNKNOWN). **zypper**: `--from packman --allow-vendor-change` per la libavcodec (passo `codec` dopo il deposito, dal catalogo: `pacchetti_codec`); `--allow-unsigned-rpm` per il SOLO file del piano (verificato dal suo sha256; l'archivio firmato è T8). **dnf**: il file del piano in una transazione sua (le dipendenze restano con `localpkg_gpgcheck=1`). **pacman**: l'insieme risolto da `pacman -U/-S --print` (prima prendeva solo il file, e la disinstallazione lasciava remotix). Il piano d'installazione aggiunge i `C-COMPONENTE` dei desktop installati (`breeze6-wallpapers`, labwc, un carattere) | DECISIONI §10.16, §6.5-bis; richiesta del coordinatore (30 set) | `[M]` 30 set, go test 161 PASS. **debian13-gnome** (.deb 5cbb97d col prodotto nuovo): CONFERMATA_A_CONDIZIONI in 8 s, `--prova-codifica` ⇒ `software libx264` (VM senza VA-API) ⇒ PASS + C-RIPIEGO; Chrome PASS; disinstallazione in 21 s: processi di `prova` **69 → 8** (systemd, sd-pam, pipewire-pulse, gcr-ssh-agent, ssh-agent: nati senza grafica; e la sessione ssh), **0 processi grafici**, l'orologio ssh batte. **debian13-lxqt**: 37 → 7 (systemd, sd-pam, pulseaudio, dbus-daemon, ssh), 0 grafici, orologio vivo. **tumbleweed-kde** (`--deposito packman`, .rpm di T3): Packman + `libavcodec63` da Packman (7 pacchetti, cambio di fornitore) + remotix + `breeze6-wallpapers` ⇒ CONFERMATA_A_CONDIZIONI in 15 s; Chrome PASS «desktop kde»; disinstallazione CONFERMATA in 19 s, 30 → 9 processi, 0 grafici; R6 contro «prima»: **nessun pacchetto diverso**, restano la chiave di Packman (ora tolta anche lei: `rpm -e`, non riprovato), `/etc/group-` e i file del desktop in `/home/prova`. Prima della cura il file .rpm senza firma era rifiutato da zypper («File is unsigned») e l'operazione si ANNULLAVA pulita (Packman e codec tolti). **arch-kde** (.pkg.tar.zst di T3): insieme risolto 9 pacchetti, CONFERMATA_A_CONDIZIONI in 3 s, Chrome PASS «desktop kde», disinstallazione CONFERMATA, 43 → 9 processi; R6: **nessun pacchetto diverso**; restano il gruppo di sistema `seat` (sysusers di seatd: INDIRETTA, pacman non lo toglie), un servizio D-Bus di sistema di KDE (`kameleon`) acceso dal desktop, i file in `/home/prova`. **Gruppi dei desktop** (`prove/gruppi-desktop.sh`, contenitori): tutti i nomi del catalogo risolti (Fedora 4 ambienti, Alma 2, Tumbleweed 4 pattern, Arch 6 gruppi); dnf 4 di Alma **non capisce `@^`**: ora `@<ambiente>` per tutti | no |
| 97918d0, 4dcaa70 | **T5, linea A — chiusura.** **`certifica`** (e la verifica dell'installazione): oltre al «controlla» di ogni passo, `codifica-h264` (REMOTIX stesso), `pam-risolta` (la pila di REMOTIX si risolve: file, `@include`/`include`/`substack`, moduli; ⚠ statica, non «rifiuta un utente inesistente»: servirebbe PAM caricato, cioè una richiesta nuova a REMOTIX), `porta-firewall` (firewalld: 7447 TCP+UDP; chiusa ⇒ FAIL non richiesto + `C-AMMINISTRATORE` col comando; ufw/nftables ⇒ UNKNOWN); esito VERDE solo se tutto PASS e nessuna condizione. **I pezzi del desktop installato dal motore** (R38) entrano nel piano (`componenti-desktop`: labwc, wlr-randr, breeze6-wallpapers, il carattere scalabile). **dnf5**: l'insieme dalla tabella di `install --assumeno` (installa/aggiorna/retrocede, mai «Skipping packages with conflicts»), `dnf download` nella cartella del passo e solo quei file; `rpm -qp` con una marca (gli avvisi NOKEY rompevano la lettura); **le chiavi del deposito** (EPEL, RPM Fusion) importate subito in rpm e tolte all'annullamento | R29, R38, T5 | `[M]` 30 set, **go test 175 PASS** (R29 in piccolo: 10 macchine guaste — scheda che non codifica, PAM senza modulo/inclusione/file, porta richiusa, firewall illeggibile, un passo disfatto — mai VERDE; installazione con la scheda che non codifica ⇒ ANNULLATA). **R29 dal vero, debian13-gnome**: sana ⇒ A_CONDIZIONI (ripiego software nella VM); PAM con un modulo che non c'è ⇒ **ROSSO**; libx264 tolta ⇒ il binario non parte ⇒ UNKNOWN ⇒ A_CONDIZIONI; servizio spento da altri ⇒ **ROSSO**; rimessa a posto ⇒ di nuovo A_CONDIZIONI; **fedora44-gnome senza `--apri-firewall`**: `porta-firewall FAIL`, A_CONDIZIONI, e Chrome davvero non entra (ERR_TIMED_OUT). **Le sette famiglie, giro completo** (`17-t4-motore.sh`: foto «cliente», il pacchetto della linea B/C/D, verifica → piano → approva → applica, certifica, Chrome vero, sessione ssh con l'orologio, `disinstalla --purge`, impronta prima/dopo): <br>• **Debian 13** (gnome, lxqt): installa 8 s, disinstalla 19-22 s; resti: `/etc/group-`/`gshadow-` (copie di gpasswd), ore delle cartelle, cache di icone/mime, CUPS/fwupd (estranei) <br>• **Ubuntu 26.04** (gnome, + `gnome-session`, D8): 16 s / 27 s; resti come Debian <br>• **Fedora 44** (gnome, RPM Fusion + `libavcodec-freeworld`, `--apri-firewall`): 14 s / 20 s; resti: la famiglia `ffmpeg-free` **retrocessa** da 8.1.2 a 8.0.1 per combaciare con RPM Fusion (INDIRETTA, resta: dichiarata), `public.xml` di firewalld riscritto uguale, CUPS <br>• **Alma 10** (gnome, EPEL + RPM Fusion): 30 s / 31 s; **nessun pacchetto diverso**; resti: `public.xml`, tuned, CUPS <br>• **Arch** (kde): 3 s / 16 s; nessun pacchetto diverso; resti: il gruppo di sistema `seat` (sysusers di seatd), un servizio D-Bus di KDE <br>• **Tumbleweed** (kde, Packman + libavcodec63 cambiando fornitore + breeze6-wallpapers): 15 s / 19 s; nessun pacchetto diverso <br>• **Leap 16** (xfce, Packman + libavcodec61 + labwc, wlr-randr): 30 s / 25 s; nessun pacchetto diverso, **nemmeno la chiave di Packman** (ora tolta: punto (3) riprovato) <br>In tutte: Chrome entra e vede il desktop giusto; dopo la disinstallazione **0 processi del desktop** nel gestore d'utente e l'orologio ssh vivo (R43); dappertutto restano i file che il desktop ha scritto in `/home/prova` | no |
| 700cc1b | **T7 — il padre nuovo ritrova i desktop vivi** (`src/ritrovo.c`/`.h`, `main.c`, `figlio.c`). **Il criterio**, uno per i quattro desktop: sessione logind col servizio PAM `remotix` (in qualunque stato: dopo la nascita è «closing», §5.2) e, nella sua scope, un processo dell'utente **capo della propria sessione di processi** (pid = sid) col padre **fuori** dalla scope — la firma di `setsid --fork` (`avvia()`); letti da logind sul bus di sistema e da `/proc`, niente bus dell'utente e niente file del figlio (i desktop nati col binario **vecchio** non li avrebbero). **All'avvio**, prima di «pronto»: una riga per desktop («RITROVATO il desktop di «u» … sessione logind cN, palco pid P «comm»») e una riga di conto (quanti, palchi su tetto, orologio). **Nei conti**: tetto = figli + ritrovati; il budget li mette dentro; l'**orologio dell'abbandono riparte dall'avvio del padre nuovo** (dichiarato: l'ultimo gesto visto dal padre di prima era nella sua memoria). **Al riattacco** `SESSIONE` dice RIPRESA, il figlio nuovo (D1 invariata) riprende lo stesso compositore e l'utente passa dai ritrovati ai figli; niente rinnovo dell'orologio. **Ripasso** ogni 10 s, solo se ce n'è: un ritrovato morto da solo esce dai conti. **Abbandono** di un ritrovato: nasce un figlio che lo chiude (`sessione_termina()`, lo sa fare solo lui dal bus dell'utente). **`loginctl terminate-user`** (iscrizione ai gruppi alla prima connessione) **non si dà** se l'utente ha un desktop REMOTIX vivo, né se logind non sa dirlo: lo si scrive, e i gruppi arrivano alla prossima nascita del desktop | §5.2, §6.5-bis, R7-R9 | `[M]` 30 set, `banchi/17-t7/`, scatole Intel, binario 36cd767c (debian13), **due giri completi** (il secondo col binario finale). Per desktop due prove, due utenti insieme (Firefox e Chrome veri, 4K), tre testimoni dell'ora (terminale vero, scope della sessione, `user@`): **aggiornamento** (desktop nati col 4fb3287d e il PAM d1734958, poi binario nuovo + PAM del prodotto e riavvio con `--tetto-sessioni 2`) e **riavvio** (desktop nati col nuovo; al secondo utente tolti `video`/`render` prima). **gnome, kde, xfce, lxqt, 8 prove su 8**: il padre nuovo dichiara **2 ritrovati** (R9); un **terzo utente resta fuori** con 0x0E «palchi 2 su 2 (0 coi figli, 2 ritrovati)» (con il codice di prima entrava: figli=0); ognuno rientra nel **suo** desktop (stesso pid del palco, riga «RIENTRA … palco pid P» uguale a quello di prima), terminale e finestre al loro posto nelle foto (R7); **0 processi del desktop persi**, testimoni col buco più lungo **1,0 s** (cioè nessuno); guardia: «iscritto a render,video, ma il gestore d'utente NON si fa rinascere: ha un desktop REMOTIX VIVO», desktop vivo. **I quattro tempi di R8**: (a) servizio fermo **4,3-4,4 s** (dallo stop al «pronto» del padre nuovo, col riavvio della scatola: stop + systemd-run); (b) desktop vivo: **0** processi persi; (c) sessione ritrovata **35-76 ms** dopo l'avvio del padre nuovo (4,3-4,4 s dallo stop); (d) il browser di nuovo con l'immagine **3,9-4,3 s** dalla scheda ricaricata (8,8-9,3 s dallo stop). **Abbandono** (gnome, `--abbandono-s 60`): ritrovato → a 60,1 s nasce il figlio, «Logout 1», sessione uscita, figlio esce; dopo: 0 processi dell'utente, 0 sessioni `remotix`. **Suite corta** col binario curato (f001 f003 f004 f011 f016 f018 + f021, chrome e firefox, 4 scatole): **224 PASS / 0 FAIL / 0 BLOCKED** (primo giro senza f021: 208 PASS). **Compila 7/7** (`costruisci-tutti.sh`; ubuntu2404 fuori per D7, immagine come prima). ⚠ Non fatto, annotato: un figlio che muore a padre vivo lascia il suo desktop fuori dai conti come prima (i ritrovati si cercano solo all'avvio) | no |
| 307d042 | `figlio.c`: chiusa la sessione su richiesta (§7.6 o abbandono) **il figlio esce** | il figlio che **apre** il desktop ne guida la sessione logind e il logout lo porta via; quello che **riprende** un desktop ritrovato sta in una sessione sua: `[M]` restava vivo e 0,6 s dopo «Logout 1» faceva **rinascere** un desktop non chiesto | `[M]` 30 set: abbandono su un ritrovato ⇒ «esco anch'io», 0 processi dopo; f021 (Esci) 16 PASS su 4 scatole × 2 browser | no |
| 6773a66 + (questo commit) | **T8 — la catena A nel motore** (`motore/firma.go`, `fiducia.go`, `installatore/chiavi/`, `strumenti/chiavi-a`). Radice ed25519 **fuori linea** (la sua pubblica scritta nel motore) che certifica **sottochiavi con periodo** (A-2026: 30 set 2026 → 29 set 2027); la sottochiave firma catalogo e motore in un file `.firma` separato (`remotix-firma/1`: catena, oggetto, sha256, certificato dentro); le **revoche** le firma solo la radice. **TRUST**: il catalogo fuori linea dato a mano (`--catalogo FILE`, firma in `FILE.firma`) è l'unico guardato; altrimenti incorporato + memorizzato (`/var/lib/remotix/fiducia/`) + archivio (`<archivio>/catalogo/<canale>/`), vince la **sequenza** più alta, poi fresco (scadenza, motore minimo). Una firma sbagliata da qualunque fonte ⇒ **BLOCCATA**; solo incorporato/memorizzato firmati da una sottochiave poi revocata o scaduta si scartano (è la rotazione). Codici nuovi RX-TRUST-006…016; 001 e 005 **ritirati** (`--senza-firma` non esiste più). **L'archivio sulla macchina** (`archivio.go`): apt deb822 `Signed-By: /usr/share/keyrings/remotix-archive-keyring.asc` + **pin** `origin "<host>"` −1 per tutto tranne i tre pacchetti REMOTIX; dnf `gpgcheck`, `repo_gpgcheck`, `includepkgs`; pacman blocco `[remotix]` fra due marche in `/etc/pacman.conf` (SigLevel Required DatabaseRequired) e la chiave in `pacman-key` (`pacman-key` e `apt-cache` entrano nell'elenco chiuso). `piano --installa --archivio URL [--canale]` installa `remotix`, `remotix-install` (e su apt `remotix-archive-keyring`) **dal gestore di pacchetti** e accende `remotix-aggiorna.timer` col consenso. **`aggiorna`** (`aggiorna.go`, `aggiorna_gestori.go`): rinfresca il SOLO archivio di REMOTIX (apt con una SourceParts sua, `dnf --repo=remotix`, pacman con una configurazione col solo `[remotix]`: niente aggiornamento parziale), sceglie secondo `aggiornamenti.conf` (D14), e fa un'**operazione** «aggiornamento» (passo `aggiorna-pacchetti`: versioni esatte, annullamento = le versioni di prima dall'archivio) — mai file sostituiti dal motore. **`ritorna --versione V`** (R11): apt `nome=versione --allow-downgrades`, `dnf downgrade` dei file verificati, `pacman -U` dalla cache o dall'archivio (`remotix.versioni`); dopo un ritorno il timer non rimette da sé la versione lasciata (RX-AGG-011). `installazione.json` resta quella dell'installazione; le versioni aggiornate in `aggiornamenti.json` (il «controlla» dell'installazione le accetta, `certifica` verde dopo un aggiornamento) | fasi/17 §6.5 p.5-6, §6.6.10, DECISIONI §10.10 | `[M]` 30 set, `go test` verde (catena A: ogni rifiuto col suo codice, la rotazione, le versioni dpkg/rpmvercmp, il blocco di pacman.conf). **Sulle VM** (evidenze `/media/REMOTIX/vm17/t8/esiti/`): installazione dall'archivio CONFERMATA_A_CONDIZIONI su debian13-gnome (9 passi), fedora44-gnome (11, con RPM Fusion), arch-kde; **R39** 3/3: il timer trova la N+1 di manutenzione e la applica con un Chrome collegato — gnome-shell/kwin **stesso pid** prima e dopo, «RITROVATO il desktop», browser di nuovo dentro in 8,8 s; il catalogo 5 (una versione di Debian in più) memorizzato dallo stesso giro; la 0.18.0 **annuale** solo avvisata (RX-AGG-003), applicata con `--annuale`; **R11** N+1→N su apt, dnf (downgrade) e pacman (-U dall'archivio, poi dalla cache), desktop sempre lo stesso; **catena A** 8/8 BLOCCATA (byte del catalogo ⇒ 007, scaduto ⇒ 002, sottochiave revocata ⇒ 010, fuori linea scaduto ⇒ 002; versioni invariate); la rotazione (revoche 2 + catalogo firmato A-2027) accettata. ⚠ **Trovato dalla fase 0**: il `.rpm` del motore 0.1.0-1 era passato per lo strip di rpm e **non corrispondeva più alla sua firma** ⇒ RX-TRUST-014, il timer fermo; curato nello spec (`__os_install_post` vuoto), 0.1.0-2 installato a mano col gestore | sì (pacchetti dell'archivio di prova) |
| (questo commit) | ⚠ **limiti dichiarati, non fatti** (T8): (1) rpm e pacman non legano una chiave a un deposito (`rpm --import`, `pacman-key --lsign-key` valgono per ogni pacchetto): R18 vale per intero solo su apt; su dnf `includepkgs` impedisce di prendere altro dal nostro archivio, su pacman niente (l'archivio contiene solo i nostri); (2) su apt un `nome=versione` esplicito dell'amministratore scavalca il pin −1 (`[M]` `hello=99.0-1` si installerebbe): mai da solo; (3) una sottochiave **revocata** che aveva firmato il motore del pacchetto lo ferma (RX-TRUST-014) finché non arriva un `remotix-install` rifirmato con la sottochiave nuova: la rotazione ordinaria va pubblicata **prima** della scadenza (§6.6.10); (4) la versione di ngtcp2/nghttp3 dello SBOM viene dal pkg-config delle `.a` collegate (`incorporate.json`, controllato contro Static-Built-Using/bundled()), non dal binario: leggerla dal binario è una riga nel prodotto (`ngtcp2_version()` nel registro d'avvio), richiesta da §6.5-bis, non fatta; (5) zypper (openSUSE) non ha ancora l'aggiornatore; (6) R23 sui metadati dell'archivio non misurata; (7) il catalogo non ha ancora un indirizzo predefinito dell'archivio (D10) | — | — | — |
| c7773c5 | **T9 — senza domande e senza rete** (`motore/risposte.go`, `fuorilinea.go`, `cmd/remotix-install/senza_domande.go`, `install.sh`; §6.6.12). **Il file di risposte** `remotix-risposte/1` → `PianoDaRisposte`: le opzioni del piano dal file; i consensi che servono **su quella macchina** (cinture sempre; firewall solo con firewalld; D5 solo dove H.264 o il desktop li chiedono; aggiornamenti solo dall'archivio) o dati o annotati fra i `mancanti` ⇒ `Applica` BLOCCATA con **RX-RISPOSTE-001** (nuovo passo della fase 4, prima dell'approvazione); voce sconosciuta RX-RISPOSTE-002, valore RX-RISPOSTE-003; il piano porta `risposte` (file, sha256, voci, predefinite, superflue, mancanti) ed è approvato «dal file». **`installa`**: piano in `/var/lib/remotix/piani/`, poi `Applica`; senza `--risposte` una conferma al terminale (senza terminale si ferma). **Il pacchetto fuori linea**: `prepara-fuori-linea` (apt: le sorgenti della macchina + l'archivio in una configurazione temporanea, `--print-uris` e `--download-only`, gli indici e l'InRelease presi dalle liste appena verificate, i `.deb` al loro posto nel pool col loro hash contro l'indice; dnf: la transazione di ogni passo **cumulativa**, `dnf download` per passo, repodata e `repomd.xml.asc` di REMOTIX; RPM Fusion: il release e i suoi depositi solo per risolvere), manifesto con impronta vincolante + **tutti** i pacchetti installati + ogni file col sha256; **sulla macchina senza rete** un gestore avvolto (`gestoreFuoriLinea`): apt con `SourceList` del pacchetto, `target=Packages`, `By-Hash=no`, liste nella cache dell'operazione; dnf dai file con `--disablerepo=*` e `localpkg_gpgcheck=1`; il passo RPM Fusion installa il release dal pacchetto; controlli RX-FUORI-001 (integrità) e 002 (macchina diversa) in fase 3. `fiducia.go` legge `file://`; `ParametriArchivio` accetta `file:///…`; per un archivio locale il pin di apt è `release o=REMOTIX` (un deposito locale non ha host) e dnf ha `includepkgs`. **`install.sh`** (§6.6.12). **Cura del PREFLIGHT** (`preflight.go` `depositi`): un deposito conta solo se una **sezione** col suo nome è **accesa**; per RPM Fusion conta «rpmfusion-free» | `[M]` fedora44-gnome: `fedora-workstation-repositories` porta `rpmfusion-nonfree-steam` SPENTO e bastava la parola ⇒ «RPM Fusion presente», nessun C-DEPOSITO, nessun consenso, e senza rete la certificazione annullava (codifica-h264 FAIL: senza RPM Fusion Fedora non ha né VA-API H.264 né libx264). Il resto: §6.0 regola 3, §6.5 punto 10, R21, R22, R31 | `[M]` 30 set: prove Go verdi (TestLeggiRisposte, TestConsensiNecessari, TestRisposteBloccate, TestDepositiAccesi, TestScriptRadice). **R31** (debian13-gnome, collegata): piano dal file, approvato dal file; `nicfio` messo in `video` ⇒ **BLOCCATA RX-PIANO-001** («gruppo.video membri= … adesso nicfio»), niente toccato; stessa foto, macchina riaccesa ⇒ **CONFERMATA_A_CONDIZIONI** e Chrome dentro (GNOME, `PASS`). **R22 debian13-gnome**: pacchetto 71 MB, 13 artefatti (9 della distribuzione: labwc, wlroots 0.18…); rete tolta (`restrict=on`, archivio non raggiungibile); un byte in un `.deb` ⇒ RX-FUORI-001; lo stesso `.deb` alterato **col manifesto aggiustato** ⇒ apt lo rifiuta contro l'indice firmato («Hashes of received file»), **ANNULLATA**, sorgenti com'erano; `nano` tolto ⇒ **BLOCCATA RX-FUORI-002** («solo nel pacchetto: nano=8.4-1+deb13u1»); pulita ⇒ **CONFERMATA_A_CONDIZIONI in 10 s**, cattura: **0 tentativi verso fuori** nella finestra dell'installazione (solo mDNS e IPv6 di vicinato); rete ridata, Chrome dentro. **R22 fedora44-gnome**: 35 MB, 14 artefatti (RPM Fusion e 11 della distribuzione: ffmpeg-free 8.0.1-6 aggiornato, x264-libs…); senza rete **CONFERMATA_A_CONDIZIONI in 9 s**, 0 tentativi verso fuori; Chrome dentro. **R21**: cloud-init su debian13-gnome (seme nuovo, `curl install.sh \| sh`, nessuno davanti) ⇒ firma VERIFICATA, **CONFERMATA_A_CONDIZIONI**, cloud-init finito in 22 s, Chrome dentro; con `risposte-manca.conf` ⇒ **BLOCCATA RX-RISPOSTE-001** (consenso.cinture), niente toccato. **install.sh**: `--verifica` da utente, `--dry-run` (piano, niente toccato), motore con un byte in più ⇒ RX-TRUST-007, firma d'altro oggetto ⇒ RX-TRUST-006/007, la sua firma «script» valida | sì (motore) |
| (questo commit) | ⚠ **non fatto, annotato** (T9): (1) il pacchetto `remotix-install` dell'archivio (0.1.0-3) ha il motore di T8: con un archivio **locale** il suo `certifica` dà FAIL sul file del deposito (non sa di `includepkgs` per `file:`), `[M]` fedora44-gnome; va ricostruito col motore di T9 (0.1.0-4) prima del rilascio; (2) zypper e pacman fuori linea (RX-FUORI-004), Packman ed EPEL nel pacchetto (RX-FUORI-005); (3) la conferma al terminale di `installa` senza `--risposte` è una riga di testo, non la TUI (D12); (4) nella VM con `restrict=on` il QUIC non passa (6 datagrammi dentro, 3 fuori): il browser entra solo con la rete ridata (riaccensione senza `restrict`, disco invariato) | — | — | — |
| b2ddbbd | **T6 — PAM come sshd** (D3, DECISIONI §10.18): `src/remotix.pam*` riga per riga come `/etc/pam.d/sshd` (`/usr/lib/pam.d/sshd` su openSUSE) più la riga di root. Debian/Ubuntu passano da `common-session-noninteractive` + `pam_systemd` per nome a `common-session` (che lo porta) con `pam_motd`, `pam_mail`, `pam_limits`, `pam_env`, `pam_loginuid` **required**; Fedora/Alma **`pam_selinux close/open` rimesso**, `pam_sepermit` in account, `pam_namespace`, `pam_motd`; openSUSE `common-session` (non più `-nonlogin`) e le `postlogin-*`. `provisiona.sh` guarda che il file arrivi a `pam_systemd` anche attraverso `common-session` | D3: *«deve rispecchiare PAM»*; e `pam_loginuid` `required` come sshd (il servizio parte da systemd, senza loginuid) | `[M]` 30 set, confronto con le VM «iso»; R20 sotto | sì (i pacchetti) |
| b2ddbbd | **T6 — il modulo SELinux** `packaging/rpm/selinux/` (`remotix.te/.fc/.if`, `remotix_porta.cil`), sottopacchetto **`remotix-selinux`** (noarch, `%selinux_modules_install`, relabel in `%posttrans`; `remotix` lo chiede con `(remotix-selinux if selinux-policy-targeted)`). Tipi: `remotix_t` (servizio), `remotix_exec_t`, `remotix_port_t` (7447 tcp+udp, `portcon` in CIL), `remotix_var_lib_t`, `remotix_var_run_t`. Regole: `auth_login_pgm_domain` (la stessa di sshd e di `cockpit_session_t`), logind sul D-Bus, `userdom_spec_domtrans_all_users` + `unconfined_domtrans` + **entrypoint dei domini utente su `remotix_exec_t`** (il figlio riesegue se stesso), `init_ranged_daemon_domain … s0 - mcs_systemhigh` come sshd, `dev_rw_dri`, segnali ai palchi; due `dontaudit` misurati (`net_admin` di sd-journal, `cap_userns sys_ptrace` del ritrovo che scorre /proc). `remotix.service` (rpm) lancia il programma **senza `/bin/sh -c`** (o il servizio resterebbe `unconfined_service_t`) | §11.1 B: `pam_selinux open` + servizio non confinato ⇒ il figlio esce con 37 | `[M]` le regole dal dominio in *permissive* con `semodule -DB`, una sessione intera (nuova, ripresa, servizio riavviato a desktop vivo, parola sbagliata, root): trovati `{ entrypoint } unconfined_t → remotix_exec_t`, `{ getattr } init_t` (in Fedora `init_ranged_daemon_domain` non chiama più `init_daemon_domain`), `{ signal } → unconfined_t`, `net_admin`, `sys_ptrace`; poi **enforcing: 0 rifiuti** su fedora44-gnome-iso, alma10-gnome-iso, alma10-gnome, tumbleweed-kde-iso, leap16-xfce (servizio `remotix_t:s0-s0:c0.c1023`, palco `unconfined_t` come chi entra con ssh; su Leap il palco nasce `unconfined_t:s0`). ⚠ Su Fedora/Alma i rifiuti stanno in audit.log (Alma) o solo nel giornale (Fedora, niente auditd): il banco legge tutti e due | sì |
| 75c28de, 95f86d7 | **T6 — il motore**: `installa-pacchetti` con più file in UNA transazione (`--pacchetto a.rpm,b.rpm`); `regola-firewall` col **servizio `remotix`** se firewalld (o ufw) lo conosce già, **le porte** altrimenti (la forma scritta nello stato di prima), regole permanenti in **una** scrittura (`update2`), all'annullamento la **zona di serie rimessa di serie** (`loadDefaults`) e il `<zona>.xml.old` che loadDefaults lascia tolto se è nato da noi; **ufw** col suo programma (entra nell'elenco chiuso: niente D-Bus), regola `ufw allow REMOTIX` dal profilo del `.deb` (`/etc/ufw/applications.d/remotix`); RX-FW-004 solo per nftables; RX-PAM-002 dice «come per ssh» | D6; «il resto public.xml» delle linee T4-T5 | `[M]` firewalld 2.4 **non vede un servizio nuovo senza reload** (`INVALID_SERVICE`, vive e permanenti) e il motore non ricarica (butterebbe le regole vive di podman/libvirt) ⇒ alla prima installazione le porte. **alma10-gnome «cliente»** (zona di serie): dopo la disinstallazione `/etc/firewalld/zones` vuota com'era (prima del cura: `public.xml.old` restava, loadDefaults rinomina). **alma10/tumbleweed «iso»** (zona già in /etc): `public.xml` identico byte per byte (sha256), ⚠ **resta cambiato `public.xml.old`**, la copia che firewalld fa da sé prima di ogni scrittura: non si evita con l'interfaccia di firewalld. **fedora44-gnome-iso**: 1025-65535 già aperte ⇒ niente toccato. **ubuntu2604-gnome-iso** con ufw acceso: `REMOTIX ALLOW` (v4 e v6) dopo, via dopo la disinstallazione. Prove `firewall_test.go` | sì (motore) |
| (questo commit) | ⚠ **visti in T6, non curati**: (1) l'aiutante non passa `PAM_RHOST` all'autenticazione (sshd sì, l'indirizzo del client): `faillock` segna «SVC remotix» invece dell'indirizzo, e `pam_access` non ha l'host; (2) **leap16-kde**: la sessione Plasma non nasce (`nessun KWin sul bus`), **anche con SELinux in permissive** ⇒ non è di T6, non era mai stata provata (T3-T5 su leap16-xfce); (3) su leap16-kde la disinstallazione si annulla: `disfa-codec` toglierebbe `kdialog` (RX-PACCHETTI-002) | per chi li riprende | `[M]` 30 set | — |
| 7583b76 | **D8 — la sessione GNOME di serie della distribuzione** (`sessione.c` `sessione_gnome()`, `unita_shell()`, `scrivi_dropin()`, sgombero; `sessione.h`; `packaging/debian/{control,rules}`). **Il criterio, uno per tutte**: candidate = `<dati di sistema>/wayland-sessions/*.desktop` il cui `Exec` lancia `gnome-session` (nome da `--session`, senza = `gnome`) **e** con `gnome-session/sessions/<nome>.session` installato; una sola ⇒ quella; più d'una ⇒ quella col nome = `ID` di os-release, poi `gnome`, poi la prima in ordine (la regola di GDM a monte; Ubuntu la corregge a mano nel suo gdm3, «Prefer ubuntu session as fallback», e qui si ottiene lo stesso senza nominarla); nessuna ⇒ **ripiego dichiarato** su `gnome`. Riga di avvio = l'`Exec` quotato argomento per argomento; `XDG_CURRENT_DESKTOP` da `DesktopNames`, `XDG_SESSION_DESKTOP` dal nome del file; gestore `gnome-session-manager@<sessione>.service`. **GNOME 50**: l'istanza della Shell la chiede la SESSIONE (`Requires` di `gnome-session@<sessione>.target`: `@user` per `gnome`, `@ubuntu` per `ubuntu`), non più `@user` fisso; il drop-in tiene **`--mode=%i`** (il modo `ubuntu` porta dock, Yaru, estensioni); lo sgombero cerca ogni `org.gnome.Shell@*.service.d` (mai quella del modello); `GNOME_SHELL_SESSION_MODE` fra le variabili rimesse com'erano. **.deb**: tolta la raccomandazione solo-Ubuntu `gnome-session \| plasma-workspace \| …` (`${remotix:Recommends}`). ⚠ **Da allineare nel motore** (altro agente, `installatore/`, non toccato): `catalogo/catalogo.json` di Ubuntu, `desktop.gnome.componenti: ["gnome-session"]` e la nota «D8 aperta» vanno tolti; e `banchi/17-distro/17-t1c-installa.sh:61` installa ancora `gnome-session` su Ubuntu | D8 dell'utente (DECISIONI §10.20): su Ubuntu chi si collega vede il desktop di Ubuntu, quello del monitor; niente eccezioni per distribuzione. `[M]` 30 set: su Ubuntu 26.04 la sessione `ubuntu` chiede `org.gnome.Shell@ubuntu.service` (`gnome-session@ubuntu.target.d/ubuntu.session.conf`) e il modo sta nell'istanza (`ExecStart=gnome-shell --mode=%i`): col codice di prima il drop-in finiva su `@user` e la Shell sarebbe nata senza `--headless` | `[M]` 30 set: costruzione 7/8 (ubuntu2404 non fa l'immagine: OpenSSL 3.0, già noto §11.1). **ubuntu2604-gnome** «cliente», .deb **senza** gnome-session (`un gnome-session`), passi del motore a mano: Chrome PASS, registro «D8: «ubuntu» (ubuntu.desktop): l'unica che la macchina propone · XDG_CURRENT_DESKTOP=ubuntu:GNOME», processo `gnome-shell --headless --no-x11 --mode=ubuntu`; **foto guardata**: dock a sinistra di Ubuntu, sfondo viola 26.04, cartella Home arancione (ding), barra nera. **debian13-gnome**: PASS, «gnome» fra `gnome`/`gnome-wayland` (stessa sessione), `@wayland` senza `--mode`; foto: GNOME Adwaita, benvenuto di Debian. **fedora44-gnome** (.rpm 0.17.0-1): «gnome» fra `gnome` e `gnome-classic` (regola «gnome»), `--mode=user`; senza RPM Fusion entra e non dipinge (causa C §11.1, nota), con `libavcodec-freeworld` PASS; foto: GNOME Adwaita, benvenuto di Fedora. **Suite corta** scatola GNOME (Debian, GNOME 48) f001 f003 f004 f016 f021 × chrome, firefox col binario f614910c: **PASS=36/36**; poi 4fb3287d rimesso, PAM d1734958 invariato, serratura libera | no (binario curato solo nelle VM e nella scatola durante la suite) |
| 01b062f | **T9 — le interfacce** (`installatore/interfaccia/`, `cmd/remotix-install/interfacce.go`, `gui_si.go`/`gui_no.go`, `motore/interfaccia.go`; §6.6.14). **Due costruzioni dello stesso sorgente**: `remotix-install` statico (motore, CLI, TUI; «gui» ⇒ RX-UI-001) e `remotix-install-gui` (etichetta `gui`, cgo, glibc di Debian 12 in `Contenitore.gui`; `costruisci.sh gui`, `costruisci.sh anteprime`). **GUI** Gio v0.10.3: cinque schermate + «nessun desktop» + «bloccata» + fini (fermata, annullata, permessi negati), colori del logo, Sora/IBM Plex incorporati (OFL), logo ritagliato; la finestra da utente, la parte da root **fatta partire da systemd** (`StartTransientUnit` via D-Bus, flag interattivo scritto a mano perché `Object.Call` di godbus lo toglie; stdin/stdout = due tubi della finestra), protocollo JSON a righe. **TUI** Bubble Tea v1.3.10, da root. **Motore**: `DomandeDaFare`, `VociDiserie`, `PianoDaScelte`, `Motore.Fermata` (RX-AZIONE-006), `Rapporto.Minima` («serve almeno Debian 13»), `Piano.Dichiarate`. **D4** (`DECISIONI.md` §4.7): le cinture sempre, fuori dai consensi; `consenso.cinture` annotata fra le superflue; via `--senza-cinture`. **D5** (§10.20): il «no» all'archivio della codifica ⇒ `RX-H264-006` nel piano (BLOCCANTE) e `Applica` BLOCCATA prima di toccare; la GUI e la TUI lo dicono subito. **D6**: il benvenuto (CLI, TUI, GUI) dice la porta da inoltrare sul router, TCP e UDP. `install.sh --finestra` (da utente, scarica la costruzione con la finestra) e `--tui` | `DECISIONI.md` §10.14, §10.15, §10.19; fasi/17 §6.6.1, §10 («quasi nessuna» scelta, il linguaggio delle schermate); pkexec lasciato perché `[M]` debian13-kde non lo ha | `[M]` 30 set: prove Go verdi (nuove: TestPianoDaScelteComeLaCLI — R36 in piccolo e D4 —, TestSenzaArchivioVideoNonSiInstalla — D5 —, TestFermataDaChiInstalla, TestTestiInterfaccia, TestVistaControlloParoleComuni). **R36** (debian13-gnome «cliente», tre copie preparate uguali, stesso binario `remotix-install-gui`): CLI (`installa`, «si» al terminale), TUI (Invio a ogni schermata), GUI (dal terminale del desktop GNOME, password nel dialogo di polkit) ⇒ tre **CONFERMATA_A_CONDIZIONI**; normalizzati identificativi e orari: `piano.json`, `insieme-risolto.json`, `insieme-risolto-pacchetti.json`, `certificato.json` **uguali**, `registro.jsonl` uguale salvo la riga APPROVATA («a mano, al terminale / nella TUI / nella finestra», che è quel che deve dire). **R37**: finestra uid 1000 in `user@1000.service`, parte da root uid 0 in `remotix-install-finestra-<pid>.service`; `sudo … gui` ⇒ RX-UI-003; senza sessione ⇒ RX-UI-002; TUI da utente ⇒ RX-UI-006. **R42**: GUI it (GNOME), en (KDE), `LANG=de_DE` ⇒ en e la parte da root `--lingua en`, `LANG=de_DE LANGUAGE=it:en` ⇒ it; TUI it, de ⇒ en, it:en ⇒ it; i codici RX- uguali. **Fermata** sul vero (debian13-kde): «Annulla e rimetti com'era» durante i pacchetti ⇒ **ANNULLATA**, pacchetti e archivio tolti. **Vincolo di §10.19**: `ldd` della costruzione con la finestra: 9 librerie grafiche; la statica «not a dynamic executable». Foto: `/media/REMOTIX/vm17/t9-gui/` (LEGGIMI.txt) | sì (archivio di T9) |
| (questo commit) | ⚠ **non fatto, annotato** (T9, interfacce): (1) la GUI non è ancora provata su Fedora (SELinux: un binario in `/tmp` fatto partire da systemd come root), Alma, openSUSE, Arch, né su XFCE/LXQt; (2) il pacchetto non porta la costruzione con la finestra (la GUI si usa per la prima installazione, da `install.sh --finestra`): un lanciatore nel menu dopo l'installazione è da decidere; (3) su GNOME la finestra si apre massimizzata (più grande dello spazio libero su 1280×800) e le decorazioni sono quelle di Gio (barra blu): KDE le dà dal compositore; (4) il dialogo di polkit dice «start transient unit remotix-install-finestra-…», non una frase nostra: con pkexec si poteva dare un'azione polkit propria (`org.remotix.install`) — un file di polkit sulla macchina prima dell'installazione, cioè una modifica in più | — | — | — |
| (questo commit) | **Il catalogo del motore dopo D8** (`installatore/catalogo/catalogo.json` 2026.09.30.6, sequenza 6, rifirmato con la sottochiave DI PROVA A-2026): Ubuntu 26.04, GNOME senza il componente `gnome-session` e senza la nota «D8 aperta» | D8: REMOTIX avvia la sessione GNOME di serie della distribuzione (su Ubuntu `ubuntu`), che c'è già: niente da aggiungere, e il piano non lo deve dire | `[M]` 30 set: TestCatalogo aggiornato (ubuntu 26.04 gnome: COMPATIBILE senza C-COMPONENTE), TestCatalogoIncorporatoFirmato verde. ⚠ Il catalogo dell'archivio (canale stabile, sequenza 5) va ripubblicato con `pubblica.sh catalogo`: finché non lo è, il motore sceglie l'incorporato (sequenza più alta) | — |
| (questo commit) | ⚠ **visti in T6, non curati**: (1) l'aiutante non passa `PAM_RHOST` all'autenticazione (sshd sì, l'indirizzo del client): `faillock` segna «SVC remotix» invece dell'indirizzo, e `pam_access` non ha l'host; (2) **leap16-kde**: la sessione Plasma non nasce (`nessun KWin sul bus`), **anche con SELinux in permissive** ⇒ non è di T6, non era mai stata provata (T3-T5 su leap16-xfce); (3) su leap16-kde la disinstallazione si annulla: `disfa-codec` toglierebbe `kdialog` (RX-PACCHETTI-002). ⇒ **Ripresi**: (1) curato, (2) e (3) spiegati — righe «T6 seguiti» qui sotto; e il livello `s0` del palco su Leap, curato | per chi li riprende | `[M]` 30 set | — |
| 1d0d9b6 | **T6 seguiti (1) — l'indirizzo del client a PAM, come sshd**: `autenticazione.c` `rcp_autentica_da()` imposta `PAM_RHOST` = l'indirizzo **nudo** del browser (da `[ind]:porta`; un IPv4 mappato `::ffff:a.b.c.d` torna IPv4, come `ipv64_normalise_mapped()` di sshd) e `PAM_TTY` = «remotix» (sshd mette «ssh»; `PAM_RUSER` sshd non lo mette, e nemmeno noi). L'indirizzo viaggia nella domanda all'aiutante (`aiutante_chiedi(…, provenienza, …)`), nella pratica in volo e, al «sì», nel verdetto (`AiutanteVerdetto` con `rhost`) fino a `figli_assicura_da()` ⇒ la sessione PAM del figlio lo riceve al posto di «remotix» (logind `RemoteHost`). `rcp_autentica()` a due argomenti resta (i banchi `01-*` la innestano); copia gemella in `banchi/rcp/` | D3 (DECISIONI §10.18): «deve rispecchiare PAM» — faillock segnava «SVC remotix» e `pam_access` non aveva l'host | `[M]` 30 set, `banchi/17-t6/t6-seguiti.sh`: **arch-kde** (faillock di serie) 2 errori ⇒ `faillock --user prova`: `RHOST 10.0.2.2` ×2; **fedora44-gnome-iso** (enforcing, `with-faillock`) lo stesso, 0 rifiuti SELinux; **debian13-gnome** e **leap16-kde**: `pam_unix(remotix:auth): authentication failure; … tty=remotix ruser= rhost=10.0.2.2 user=prova`; ovunque sessione `Service=remotix Remote=yes RemoteHost=10.0.2.2` (prima `RemoteHost=remotix`); desktop PASS su debian13-gnome, arch-kde, fedora44-gnome-iso. ⚠ Da 127.0.0.1 logind segnerà `Remote=no`, come per ssh: il guardiano (§5.1) discrimina sul seat. Compila 7 su 7, 0 avvisi | sì (pacchetti in `t6/pacchetti-seguiti/`, VM tornate alla foto) |
| 1d0d9b6 | **T6 seguiti (3) — il livello SELinux del desktop come con ssh**: `figlio.c` `livello_selinux_come_sshd()`, dopo `pam_open_session`: il ruolo e il tipo restano quelli di `pam_selinux`, il **livello** si rimette quello della mappa di login (`getseuserbyname`), se il contesto nuovo è valido (`security_check_context`) — `setexeccon`. libselinux con `dlopen` (nessuna dipendenza nuova; tace dove SELinux non c'è) | **La causa**: `pam_selinux open` cerca il dominio di chi chiama (`remotix_t`) in `contexts/users/unconfined_u` e `default_contexts`, file della politica della distribuzione che elencano `sshd_t`, `cockpit_session_t`, `xdm_t`… e non `remotix_t` (un modulo non li può estendere) ⇒ libselinux ripiega su `failsafe_context` = `unconfined_r:unconfined_t:s0`. Colpiva solo ciò che il figlio esegue **direttamente** (figlio, `startplasma-wayland`, labwc): quel che parte dal gestore d'utente (kwin, gnome-shell, pipewire) nasce da `init_t`, che è elencato, e aveva già `s0-s0:c0.c1023` — per questo su Fedora/Alma (GNOME dal gestore) non si vedeva | `[M]` 30 set, **leap16-kde enforcing**: prima figlio e `startplasma-wayland` `…:s0`, kwin `…:s0-s0:c0.c1023`; dopo tutti `s0-s0:c0.c1023` (riga «⭐ SELinux: il desktop di «prova» nasce … come con ssh (pam_selinux aveva dato …:s0)»), **0 rifiuti**; fedora44-gnome-iso 0 rifiuti in enforcing | sì |
| (questo commit) | ⚠ **T6 seguiti (2) — leap16-kde: Plasma non parte, ed è della PIATTAFORMA** (non di REMOTIX, non di SELinux): **KWin 6.4.2 si abbatte** (SIGSEGV in `EglSwapchainSlot::texture()` ← `ScreenCastStream::record`, 11 core in 55 s, uno a ogni rinascita) appena REMOTIX apre la cattura in memoria. Senza 3D (VM, llvmpipe) KWin non riesce ad allocare i buffer dell'uscita virtuale (`DRM_IOCTL_MODE_CREATE_DUMB: Permission denied` sul nodo render a ogni fotogramma), non disegna mai, e lo screencast legge una catena vuota — cfr. KDE bug 487217 (KWin annidato con llvmpipe, `EglSwapchainSlot`). Le altre strade provate a mano: `KWIN_COMPOSE=Q` ⇒ «OpenGL compositing is required for screencasting»; `KWIN_DRM_DEVICES=/dev/dri/card1` ⇒ nessun effetto. Su Tumbleweed e Arch (KWin più nuovo) nella stessa VM va ⇒ **condizione per il catalogo**: *openSUSE Leap 16 + Plasma (KWin 6.4) richiede l'accelerazione 3D* (scheda vera o virgl); senza, niente desktop KDE — XFCE e LXQt (labwc in pixman) sì. ⚠ Su ferro vero Leap KDE non è ancora provato. **E la disinstallazione che si annulla per `kdialog`** (RX-PACCHETTI-002, lavoro della linea del motore, `installatore/` non toccato): `disfa-codec` toglie solo i pacchetti **nuovi** del passo Packman (`libx264-165`, `libx265-215`, `libxvidcore4`) e lascia gli **aggiornati** (`libavcodec61` & c. di Packman, prima `7.1.5-160000.1.1` di repo-oss) — che però **richiedono proprio quelli** (`libx264.so.165`…) ⇒ `zypper rm --dry-run` trascina 53 pacchetti (libavcodec61, qt6-multimedia, kwin6, plasma6-workspace, kdialog…). La guardia ha fatto bene a fermarsi; l'elenco è sbagliato: un «nuovo» richiesto da un «aggiornato» che resta non si toglie — o si riportano gli aggiornati alla versione di prima (cambio di fornitore Packman → openSUSE) nella stessa transazione, poi si tolgono i nuovi. Su leap16-xfce non si vedeva perché nessun pacchetto del desktop chiede libavcodec61 | per la linea del motore; per il catalogo (Leap KDE) | `[M]` 30 set, leap16-kde «cliente», giornale di sistema, `coredumpctl`, registro dell'operazione `disfa-codec` e `zypper rm --dry-run` rifatto a mano | — |

| 49ef16a | **T10 — il motore trattiene ciò che serve a chi resta, anche il DEPOSITO** (`azione_deposito.go`: `Annulla` prima i pacchetti arrivati col deposito — quelli che qualcosa che resta chiede si trattengono e con loro resta il deposito, su Alma anche `epel-release` se il deposito Cisco trattenuto ne usa la chiave; `Annullata` lo dichiara con `RX-PACCHETTI-006`), e **dnf che «non risolve» vale «lo chiede chi resta»** (`gestore.go` `SimulaTogli`: `dnf remove --assumeno` esce 1 anche quando riesce, e se un pacchetto PROTETTO si romperebbe non stampa «Removing» — i nomi dei «Problem» sono i dipendenti, `problemiDnf`/`nomeDaNevra`) | la regola già decisa della disinstallazione (come RX-PACCHETTI-006 di installa-pacchetti) applicata al deposito: prima RX-PACCHETTI-002 e ANNULLATA_IN_PARTE (`[M]` T10 30 set: alma10-kde — ark, dolphin, plasma-desktop… chiedono openh264; fedora44-gnome-iso — openh264 ← libheif ← glycin ← gdk-pixbuf2 ← gnome-shell protetto, e `mozilla-openh264` ← firefox) | `[M]` 30 set: `deposito_test.go` (trattiene e dichiara; toglie quando nessuno lo chiede; epel resta col Cisco; i «Problem» di dnf ⇒ trattenuto) — go vet + go test verdi, gofmt pulito; la diagnosi dal vivo su fedora44-gnome-iso (`dnf remove --assumeno openh264` ⇒ «Failed to resolve the transaction … protected packages: gnome-shell», exit 1 anche per `remotix` da solo). Giro T10 su 0.18.4: **alma10-kde e fedora44-gnome-iso PASS** in tutto il copione — `disfa-deposito-openh264: FATTA ([RX-PACCHETTI-006] il deposito openh264 resta acceso: … lo chiede ark, dolphin, plasma-desktop…)`, su Fedora `mozilla-openh264 (lo chiede firefox)` e `openh264 (lo chiede gnome-shell, glycin-libs…)`; operazioni CONFERMATA, 0 pacchetti remotix rimasti, gruppi di «prova» come prima | nel motore (rilascio 0.18.4) |
| 93040c2 | **T10 — REMOTIX dipende dal demone PipeWire + wireplumber** (`packaging/debian/control` Depends, `packaging/rpm/remotix.spec` Requires; Arch li aveva già) | su openSUSE GNOME dell'immagine Minimal-VM PipeWire non è installato (pattern GNOME solo raccomandato) ⇒ mutter «Error connecting to the screencast service» e il desktop non arriva; dpkg/rpm vedono la libreria, non il demone; il video di GNOME/KDE e l'audio di ogni desktop ne hanno bisogno | `[M]` 30 set: installato pipewire+wireplumber su tumbleweed-gnome vivo ⇒ il desktop dipinge; il giro T10 di leap16-gnome e tumbleweed-gnome passa da FAIL a **PASS** su 0.18.2/0.18.3 | nei pacchetti (rilascio) |
| d151ae9 | **T10 — Xwayland come dipendenza di labwc** (`.rpm`: `(xorg-x11-server-Xwayland if labwc)` su Fedora, `(xwayland if labwc)` su openSUSE; prima solo `if xfce4-session`) | leap16-lxqt: labwc «cannot create xwayland server» ⇒ la barra X11 di LXQt non parte ⇒ nessun palco; Xwayland serve a labwc per gli applicativi X11 (XFCE **e** LXQt), non a un desktop solo | `[M]` 30 set: installato xwayland su leap16-lxqt vivo ⇒ il desktop dipinge; il giro T10 di leap16-lxqt passa a **PASS** su 0.18.3 | nei pacchetti (rilascio) |
| cda31e6 | **T10 — via `libyuv` dalle tre ricette** (`packaging/debian/control`, `packaging/rpm/remotix.spec`, `packaging/arch/PKGBUILD`): la conversione dei colori è di REMOTIX (`src/colori709.c`, fasi/18 §1), `libyuv` non serve e non c'è su Alma né su Arch col soname | il rilascio 0.18.1-1 si fermava su `dpkg-checkbuilddeps: unmet build dependencies: libyuv-dev` (il contenitore della fase 18 non porta libyuv) | `[M]` 30 set: `packaging/rilascio.sh 0.18.1-1` e `0.18.1-2` costruiscono le 7 famiglie (.deb Debian 13 e Ubuntu 26.04, .rpm Fedora 44/Alma 10/Tumbleweed/Leap 16, Arch), motore (due costruzioni), archivio firmato; **`ldd` di ogni binario senza libav\*/libswscale** (deb R4 32-33 librerie, rpm 28-31, 0 mancanti); SBOM ngtcp2 1.25.0/nghttp3 1.18.0; install.sh sha256 `2f7a1ca6…` | nei pacchetti di prova (poi tolti) |
| 9991f09 | **T10 — alla disinstallazione il motore toglie `~/.local/state/remotix/sessione.log` in tutte le case** (`azione_registri_utente.go`, passo `togli-registri-utente` sempre per ultimo, a sessioni chiuse: il solo `sessione.log` di ogni casa da `/etc/passwd`, e `~/.local/state/remotix/` se resta vuota; nient'altro nelle case; ESATTA: copie nella cartella dell'operazione, rimesse con permessi e proprietario se la disinstallazione si annulla). I percorsi si dichiarano nel piano («si fa sempre: …») e nel certificato («tolti: …») | decisione dell'utente del 1 ott 2026, che chiude il punto (2) della riga 165906c: il registro della sessione è DIRETTO e non è un dato dell'utente | `[M]` 1 ott: prove Go (la casa di «prova» resta senza cartella, quella di «altro» col solo file suo, l'annullamento rimette tutto); in T10 su debian13-kde e leap16-kde (scatola), debian13-gnome e fedora44-gnome (VM): prima `/home/prova/.local/state/remotix/sessione.log` c'è, dopo nessun registro nelle case; l'eccezione «atteso» tolta da `17-t10.sh` | 0.18.5+ |
| 004aa22 | **T10 — la porta scelta (`porta = N` nel file di risposte) si scrive in `/etc/remotix/remotix.conf.d/porta.conf`** (`piano_installazione.go`: un passo `scrivi-file` prima dell'accensione, solo se non è la 7447; `remotix.service` lo legge da `EnvironmentFile`; la disinstallazione lo disfa) | `[M]` 30 set, le scatole KDE (porta 8531/8532 perché `--network=host`): il motore apriva il firewall su N e verificava il servizio su N, ma non scriveva la scelta ⇒ il servizio partiva su 7447 e l'installazione si ANNULLAVA («attivo ma 8532/tcp non in ascolto»); con la porta di serie non si vedeva | `[M]` 1 ott: `TestPianoPortaScelta`; le due scatole KDE installano e ascoltano sulla loro porta (T10 PASS) | 0.18.6+ |

### 13.2 L'impianto di prova (banchi, VM)

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| (questo commit) | `banchi/17-distro/17-vm.sh`: una VM per `<distro>-<desktop>` dalle immagini cloud ufficiali, cloud-init, porte per macchina, `vesti` col gruppo di pacchetti ufficiale, foto «cliente», riavvio vero controllato col `boot_id` | decisione dell'utente del 29 set: le prove dell'installatore in VM, una per desktop | `[M]` 9 distribuzioni su 9 accese, ssh in 3-39 s | copiata sul server |
| 12f6782…(questo commit) | `banchi/17-distro/17-carico.sh`: la prova di carico delle VM; ritmo dai contatori dei fotogrammi su ~60 s; journal letto con sudo **dopo** lo spegnimento, VM spente una alla volta | decidere quante VM insieme (4 o 8) | `[M]` 8 VM non reggono (memoria); si resta a 4 | copiata sul server |
| (questo commit) | `banchi/17-t2/`: la misura di T2 (sessione viva con tre testimoni e sentinella a 50 ms; ferma / uccidi-padre / uccidi-figlio; catena dal journal) | §5.2 | `[M]` 10 prove su 4 desktop: nessun desktop muore | sul server, in /media/REMOTIX/tmp/t2 |
| (questo commit) | `src/costruzione/`: un `Contenitore.<bersaglio>` per debian13, ubuntu2604, ubuntu2404, fedora44, alma10 (EPEL+CRB), arch, tumbleweed, leap16 — dipendenze dal gestore di pacchetti della distribuzione, ngtcp2 1.25.0 e nghttp3 1.18.0 **statiche** (`quic-statiche.sh`, solo `.a` in `/usr/local/lib`, `LIBRARY_PATH`: il Makefile non cambia); `costruisci-tutti.sh` costruisce uno o tutti in una copia dell'albero e scrive per bersaglio binario, registri, versioni, `ldd` fatto nel contenitore. `src/Contenitore` resta com'era | §6.2 e §6.3: si compila per ogni distribuzione, niente `ld.so.conf.d` | `[M]` 29 set, sul portatile: **7 su 7 compilano**, `ldd` senza «not found» e senza ngtcp2/nghttp3. Ubuntu 24.04 si ferma a ngtcp2 (OpenSSL 3.0.13 senza QUIC); una sonda senza il ramo OpenSSL mostra poi solo `codificatore.c:1419,1436` (ffmpeg 6.1) e `ei_disconnect` assente (`input.c:1218`, libei 1.2.1) — D7. Versioni: OpenSSL 3.5.0 (Leap) … 3.6.4 (Arch); libavcodec 61 (Debian, Alma, Leap), 62 (Ubuntu, Fedora), 63 (Arch, TW); libei 1.3.901…1.6.0; PipeWire 1.4.2…1.6.9; glib 2.80…2.88. Arch e TW hanno già ngtcp2 1.25 con crypto_ossl: usabile, non usata per uniformità | no (solo portatile) |
| (questo commit) | **T1c**: `banchi/17-distro/17-t1c-installa.sh` (REMOTIX a mano in una VM, famiglia per famiglia: dipendenze, PAM, `utenti-negati`, polkit/logind/sleep, utente `prova`, unità transitoria sulla 7447), `17-t1c-browser.py` (Chrome vero con le guide di `12-client-veri.py`: apri → entra → primo fotogramma col giudice dei pixel), `17-t1c-guarda.sh` (labwc suo sull'Intel, `127.0.0.1` perché l'inoltro UDP di QEMU è solo IPv4) | far girare il prodotto portato e vederlo da un browser vero, prima dell'installatore | `[M]` 29 set, 7 VM «cliente», Full HD. **Col binario del prodotto: 0 su 7.** Tutte entrano («Ammesso»), nessuna dipinge: (1) nella VM `virtio_gpu` senza 3D la negoziazione PipeWire muore con «no more input formats» (strada della SCHEDA con modificatore obbligatorio, `cattura.c:1487`; il ripiego sulla memoria scatta solo dopo un fotogramma, `figlio.c:5362`) — Debian, Ubuntu, Arch, TW; (2) Fedora e Alma: figlio uscito con 37, AVC `{ transition } unconfined_service_t → unconfined_t` da `pam_selinux open`; (3) Fedora/Alma/openSUSE senza depositi di terzi: «libx265 non c'è in questa libavcodec: non se ne prende un altro» (Chrome chiede HEVC). **Col binario di diagnosi** (`-DCOPIA_ZERO=0`, non il prodotto): PASS Debian 13, Ubuntu 26.04 (GNOME 50, `@user` con `--headless`), Arch KDE; Fedora 44 e Alma 10 PASS solo con `pam_selinux` tolto dal PAM + `libavcodec-freeworld` (RPM Fusion); TW KDE (con Packman) e Leap XFCE BLOCKED dalla VM: KWin e labwc non allocano (`DRM_IOCTL_MODE_CREATE_DUMB: Permission denied` sul nodo virtio) ⇒ tela nera. `provisiona.sh` fuori da Debian installa `remotix.pam` (Debian) e la sua verifica dice lo stesso «⭐ a posto» | copiati sul server (`/media/REMOTIX/vm17/t1c/`) |
| (questo commit) | **Stato ISO**: `17-vm.sh da-iso <macchina>-iso` (ISO ufficiale scaricata e verificata con la sha256 del sito, kernel e initrd presi dall'ISO, risposte servite in HTTP su 10.0.2.2, disco NUOVO, UEFI con NVRAM propria, foto «iso» con la NVRAM), `impronta [foto]` (firewall, SELinux, display manager, rete, pacchetti; da una foto in sola lettura, porte k=6), `schermo` (schermata dal monitor, senza socat); risposte in `banchi/17-distro/iso-risposte/` (preseed, autoinstall, kickstart ×2, archinstall 4.4, AutoYaST); porte k=5 | §7.2: una immagine cloud con un desktop sopra non è la macchina di un cliente | `[M]` 29 set: **6 su 6 fatte** con la foto «iso» (ssh, sudo, graphical.target): Debian 10 min, Ubuntu 11, Fedora 7, Alma 7, Arch ~10, Tumbleweed 14. Contro cloud+DESKTOP (`impronta … cliente`): 7447 chiusa da firewalld su Alma e **Tumbleweed ISO** (la cloud TW non ha firewall), aperta su Fedora Workstation (1025-65535); `video` già dato dall'installatore Debian, `render` mai; rete NetworkManager su tutte le ISO (cloud Debian/Ubuntu/Arch: networkd); TW ISO con accesso automatico, snapper su btrfs, raccomandati (+1701 pacchetti) e root con la parola dell'utente; Alma ISO su LVM; Fedora ISO con `noopenh264` — tutto in `banchi/17-distro/iso-differenze.md` | copiata sul server |
| (questo commit) | **T3, linea B — la prova del `.deb` in VM**: `banchi/17-distro/17-t3-prova.sh <macchina> <deb>` (foto «cliente» → persona `prova` già in `video` → impronta → `apt-get install ./…deb` e nient'altro → Chrome vero su `127.0.0.1` con `17-t1c-guarda.sh` → impronta → `--reinstall` → impronta → `purge` → impronta → `autoremove --purge` → impronta → spenta e tornata a «cliente»; ⛔ non spegne una macchina già accesa, si ferma a 4 VM) e `17-t3-impronta.sh` (file di `/etc` con sha256, di `/usr` con dimensione e data, gruppi, conti, unità, pacchetti, manuali, logind/sleep in vigore, nft) | R4, R5, R6 in piccolo, a livello pacchetto (senza motore) | `[M]` 29 set, `.deb` 313ccfc, sul server in `/media/REMOTIX/vm17/t3/deb/esiti/`. **debian13-gnome**: installa con 10 dipendenze in più (labwc, wlr-randr e 8 librerie di wlroots; `va-driver` e `xwayland` c'erano già), 0 aggiornate; `nicfio` messo in `video`+`render`, `prova` in `render` (DIRETTE), `prova` in `video` PREESISTENTE; servizio attivo, certificato generato (`DNS:rx-debian13-gnome`); `ldd` da `prova` con ambiente vuoto: 0 mancanti; **Chrome PASS** («Ammesso, sessione nuova, desktop gnome», immagine a 4,8 s). **ubuntu2604-kde**: 8 dipendenze in più, `gnome-session` **non** portata (`plasma-workspace` soddisfa l'alternativa); stessi gruppi; **Chrome PASS** («desktop kde»); il file di KWin del pacchetto **non** riscritto dal programma. **R5**: fra «dopo il browser» e «reinstallato» nessun file cambiato di contenuto; restano le date delle cartelle rifatte da dpkg, `mimeinfo.cache` rigenerata da un innesco (stessa dimensione), CUPS e il numero di sessione (estranei). **R6**, prima → dopo `purge`+`autoremove`: **nessuna differenza DIRETTA**: gruppi identici a prima (`prova` resta in `video`: R33), `/etc/remotix`, `/etc/pam.d/remotix`, `/var/lib/remotix`, unità, cinture e i 10/8 pacchetti spariti; **INDIRETTE** (da dichiarare): `/etc/group-` e `/etc/gshadow-` (le copie di riserva di `gpasswd`, con lo stato di mezzo), date delle cartelle di `/usr`, cache di icone e mime rigenerate; **estranee**: CUPS, `fwupd.conf` 644→640 (fwupd, a macchina ferma di REMOTIX). ⚠ Dopo il purge `prova` ha ancora il **desktop vivo** (`session-cN.scope`): sopravvive al servizio (§5.2) ma non lo raggiunge più nessuno — domanda per T5 | copiati sul server (`/media/REMOTIX/vm17/t3/deb/`) |
| 5e287cb, 631ce8d, cdefd1f (questo commit) | **T3, linea B, rifatta per DECISIONI §10.12 (l'installatore è l'unica via) — il `.deb` coi pezzi INERTI e la prova R40**: `dh_installsystemd --no-enable --no-start --restart-after-upgrade` (in aggiornamento `try-restart`: riparte solo se girava); via il postinst (niente gruppi, niente `modifiche.log`); `prerm` che al solo `remove` ferma il servizio (con `--no-start` debhelper non lo fa più); `postrm purge` toglie solo certificati, ban, `/run/remotix` e `/var/lib/remotix` se vuota, **non tocca i gruppi**; le tre cinture SPENTE in `/usr/share/remotix/cinture/`; PAM e `utenti-negati` restano (inerti). L'unità rifiuta di partire senza `/var/lib/remotix/installazione-confermata` (nome **proposto** per T4-T5) con `RX-INST-001` e uscita 78 del processo principale (`sh -c 'test … ; exec remotix …'`) e `RestartPreventExitStatus=78` — ⚠ il controllo vero va nel programma (punto 3 di §10.12). `17-t3-prova.sh`: R40 dopo `apt install` (abilitata? attiva? porta 7447? gruppi? cinture in vigore?), `systemctl start` senza installatore, poi **i passi del motore fatti a mano e dichiarati** (`prova` nei gruppi dei nodi, cinture copiate in `/etc/{polkit-1/rules.d,systemd/logind.conf.d,systemd/sleep.conf.d}`, marca, `enable --now`), browser, reinstallazione, passi disfatti a mano, `purge`, `autoremove`; porte in ascolto nell'impronta | DECISIONI §10.12, R40 | `[M]` 29 set, `.deb` cdefd1f (lintian 0 E/0 W; R13, R14, R4 verdi; **R23** due costruzioni identiche: Debian `6655ae2c…`, Ubuntu `223fdb75…`), **debian13-gnome e ubuntu2604-kde**: dopo `apt install` **servizio disabled e inactive, 0 socket sulla 7447, gruppi identici a prima, 0 cinture in vigore** — le sole aggiunte sono i file del pacchetto, le dipendenze (10 / 8), `/var/lib/remotix` e `/run/remotix` vuote (tmpfiles) e il file di stato di debhelper; **`systemctl start`** ⇒ `failed`, `RX-INST-001` nel journal, 0 ripartenze, 0 socket (⚠ `start` esce 0: con `Type=simple` il rifiuto si legge solo nel journal e in `is-active`). `[M]` La prima versione con `ExecStartPre` ripartiva ogni 2 s (`RestartPreventExitStatus` guarda solo il processo principale) — curata. Coi passi del motore a mano: attiva, 2 socket, **Chrome PASS** su tutte e due (GNOME, KDE). **R5**: nessun file cambia contenuto; la reinstallazione aggiunge il file di stato `deb-systemd-helper-enabled/…/remotix.service` (debhelper registra l'abilitazione fatta dal motore: al purge la toglie lui) e rigenera `mimeinfo.cache`. **R6** (passi disfatti + purge + autoremove): nessuna differenza DIRETTA; INDIRETTE `/etc/group-`/`gshadow-` (copie di `gpasswd`, dai passi del motore), cache di icone e mime; estranee CUPS e `fwupd.conf`. ⚠ Il desktop di `prova` resta vivo dopo il purge — su KDE con `kdeconnectd` (1716), avahi e porte UDP sue in ascolto: la domanda per T5 si fa più concreta | copiati sul server (`/media/REMOTIX/vm17/t3/deb/`) |
| 3c8607e | **T3, linea D — la prova del pacchetto Arch in VM**: `banchi/17-distro/17-t3-pacchetto.sh <macchina> <passo>` (un passo per chiamata: `prepara` = persona `prova` già in `video`; `impronta <nome>`; `installa` = copia e `pacman -U --noconfirm`, nient'altro; `r40`; `motore-monta` / `motore-smonta` = i **passi del motore fatti a mano** — `prova` nei gruppi letti dai nodi, col registro MESSO/C'ERA, e `enable --now`; `togli` = `pacman -Rns`; `confronta`) e `17-t3-impronta-arch.sh` (file di `/etc`, `/usr/lib/systemd`, polkit, tmpfiles, applications, `/var/lib/remotix` con sha256, il resto di `/usr` e `/var/lib` con la dimensione; gruppi, conti, unità, pacchetti espliciti/dipendenze, i nomi sotto `/home`) | R4, R5, R6, R33, R40 a livello pacchetto, senza motore | `[M]` 29 set, pacchetto `0.17.0-3` (3c8607e), VM «cliente», sul server in `/media/REMOTIX/vm17/t3/arch-{kde,xfce}/` (le prove del `-1`, prima di §10.12, in `t3/arch-pkgrel1/`). **R4**: `pacman -U` da solo risolve tutto dagli archivi: **arch-kde** +8 pacchetti (labwc, wlr-randr, wlroots0.20, seatd, …), **arch-xfce** +86 (ffmpeg con x264/x265 e ~50 librerie, pipewire+wireplumber+pipewire-pulse, labwc, `gnu-free-fonts` come `ttf-font`: il gruppo xfce4 non porta né ffmpeg né l'audio); 0 aggiornati; due domande di provider (`jack`, `ttf-font`) risposte col predefinito. **R40**: dopo il solo pacchetto servizio `disabled/inactive`, 0 in ascolto sulla 7447, `render` vuoto, 0 cinture e logind/sleep in vigore invariati, firewall intatto — ⛔ ma `systemctl start remotix` **parte** (manca `RX-INST-001`, §13.1). **Passi del motore a mano** ⇒ **Chrome PASS su tutt'e due**: arch-kde «desktop kde», primo fotogramma a 4,2 s, il file di KWin trovato uguale e non riscritto; arch-xfce «desktop xfce» (sfondo nero come in T1), e col `-3` il sink audio «remotix» montato (col `-1`, senza pipewire: «contesto PipeWire non creato … SENZA SUONO»). **R5**: reinstallazione a servizio acceso e sessione viva ⇒ **0 differenze** nelle impronte; il `try-restart` riavvia il server in ~4 s e la sessione di `prova` resta (25 e 39 processi). **R6/R33**, prima → dopo `motore-smonta`+`-Rns`: **nessuna differenza DIRETTA del pacchetto** (via `/etc/remotix`, `/etc/pam.d/remotix`, `/var/lib/remotix`, unità, collegamento d'accensione, tutte le dipendenze portate); `prova` di nuovo solo in `video` (PREESISTENTE, intatta). **INDIRETTE** da dichiarare: il gruppo di sistema `seat` (sysusers di `seatd`, via labwc) che pacman non toglie ⇒ `/etc/group`, `/etc/gshadow` e le copie `-`; su XFCE il collegamento `/usr/lib/libvsscript.so` lasciato da vapoursynth (via ffmpeg); i file del desktop in `/home/prova` (KDE/XFCE, cache, pipewire). **DIRETTE del prodotto a esecuzione, rimaste**: `~/.local/state/remotix/sessione.log`, e su XFCE `xfce4-power-manager.xml` (§8.2). ⚠ Nella prova del `-1`, dopo `-Rns` la sessione KDE di `prova` era già chiusa (2 processi, il gestore d'utente); con la linea B il desktop restava vivo: non guardato oltre | copiati sul server (`/media/REMOTIX/vm17/t3/`) |
| aec8402 | **T4, linea A — le prove del motore** (`installatore/`): `costruisci.sh` (costruzione e `go test` nel contenitore `golang:1.25`, cache in `.cache/` perché `/tmp` del portatile è quasi pieno, `-mod=vendor`, niente rete); `motore/*_test.go` (la macchina finta sotto una cartella: `/etc/group`, `/etc/passwd`, systemd e firewalld finti in file JSON, così lo stato sopravvive al processo ucciso; il gancio `PuntoDiProva`, che nel binario resta sempre nil); `prove/impronta` (impronta di una cartella in Go, indipendente dal motore, con `-confronta` perché i contenitori minimi non hanno `diff`); `prove/r1-contenitori.sh` (R1 in debian:13, fedora:44, archlinux, tumbleweed); `prove/Contenitore.systemd` + `prove/systemd-giro.sh` (Fedora 44 con systemd acceso: le azioni vere sul D-Bus e `gpasswd`) | R30 e R1 in piccolo, senza le VM del server (usate da altri) | vedi §13.1, aec8402 | solo portatile |
| 165906c | **T3, linea C — la prova del `.rpm` in VM**: `banchi/17-distro/17-t3-rpm.sh <macchina> <passo>` (gemello di `17-t3-pacchetto.sh`, con dnf/zypper: `prepara` = persona `prova` già in `video`; `impronta`; `installa` = `dnf install ./…rpm` / `zypper install --allow-unsigned-rpm ./…rpm` e nient'altro; `r40`; `motore` = **i passi del motore a mano** — gruppi della scheda con `17-t3-gruppi.sh` (registro chi c'era / chi è stato messo), servizio firewalld aperto se firewalld è acceso, `enable --now`; `terzi` = RPM Fusion / Packman, **passo separato** (la condizione di §11.1, D5); `selinux` = `ausearch -m avc,user_avc,selinux_err`; `reinstalla`; `motore-annulla`; `togli` = `dnf remove` / `zypper remove --clean-deps`; `confronta`); `17-t3-impronta-rpm.sh` (file, gruppi, utenti, unità, pacchetti con la ragione dnf/zypper, contesti SELinux dei nostri percorsi, firewalld) | provare il pacchetto dove lo troverebbe un cliente, e vedere R40 | `[M]` 29 set, foto «cliente», Chrome vero su `127.0.0.1`, SELinux **enforcing** su tutte e quattro. **R40 verde 4/4**: dopo l'installazione servizio `disabled`/`inactive`, 0 in ascolto sulla 7447, 0 cinture attive, gruppi invariati, firewalld (dove acceso) senza `remotix`. **R4**: `tumbleweed-kde` porta da sé `libavcodec63 libavutil61 libswresample7 libswscale10 breeze6-wallpapers`; `leap16-xfce` 77 pacchetti (ffmpeg, pipewire, libei, libva, **labwc, xwayland**); `fedora44-kde` nessuno (ffmpeg-free già lì); `alma10-gnome` **rifiutato senza EPEL** (`nothing provides libavcodec.so.61`, niente toccato), poi con EPEL+CRB (passo del motore) 28 pacchetti da EPEL. **Desktop nel browser** coi passi del motore: senza depositi di terzi Fedora e Alma **entrano ma non dipingono** («libx265 non c'e' in questa libavcodec», causa C di §11.1); con RPM Fusion / Packman **PASS su tutte e quattro** (TW KDE, Fedora KDE, Alma GNOME, Leap XFCE). ⚠ `fedora44-gnome` era occupata da un'altra prova: Fedora provata su `fedora44-kde`. **R19** 0 rifiuti SELinux in enforcing (Fedora, Alma, TW, Leap) col PAM senza `pam_selinux`; processi del server `unconfined_service_t`. **R5**: reinstallazione ⇒ 0 differenze di REMOTIX (solo rumore del desktop: `cups/subscriptions.conf`, unità transitorie di KDE), servizio ancora acceso; `rpm -V remotix` pulito (il permesso di KWin non riscritto). **R6/R33** (impronta prima dell'installazione ↔ dopo `motore-annulla` + rimozione): **nessuna differenza DIRETTA del pacchetto** (dopo la cura `%ghost` delle marche `.nostro`, che su TW lasciavano `/var/lib/remotix`); gruppi **identici** a prima, `prova` ancora in `video` (PREESISTENTE non toccato); INDIRETTE: `/etc/group-` e `/etc/gshadow-` (copie di gpasswd), le dipendenze che `zypper --clean-deps` tiene perché raccomandate (`breeze6-wallpapers`), la casa di `prova` (file del desktop usato e `~/.local/state/remotix/sessione.log`); del **passo del motore** D5/D6, non annullato qui: il deposito di terzi e le sue librerie (Fedora: ffmpeg-free retrocessa 8.1.2 → 8.0.1), `/etc/firewalld/zones/public.xml` | sul server, in `/media/REMOTIX/vm17/t3-rpm/`; VM tornate a «cliente» |
| 56c93d3 | **T4-T5, linea A — il motore in VM**: `banchi/17-distro/17-t4-motore.sh <macchina> <remotix-install> <.deb>` (foto «cliente», o `azzera` per la nuda con `DESKTOP=`; `prova` già in `video`; impronta 17-t3; verifica → piano → approva → applica; Chrome vero con 17-t1c-guarda; una sessione ssh di `prova` con un orologio; disinstalla --purge; impronta e diff; spegne e rimette com'era), `17-t4-alma.sh` (EPEL + dnf + firewalld sul D-Bus, R28 dal vero, poi CONFERMATA), `installatore/prove/sul-server.sh` (costruisce, copia in `/media/REMOTIX/vm17/t4/`, lancia con `sg kvm`) | T4-T5 in VM, una VM sola per volta | vedi §13.1, 56c93d3 | copiati sul server (`/media/REMOTIX/vm17/t4/`) |
| (questo commit) | `banchi/17-t7/`: `t7-campagna.sh` (serratura delle scatole per tutto il giro; per desktop `aggiornamento` e `riavvio`; suite corta; `LASCIA=1`), `t7-aggiorna.py` (due utenti con Firefox e Chrome veri in due labwc diversi, testimoni come T2, riavvio con `11-accendi.sh`, i quattro tempi dal journal `short-unix`, terzo utente col tetto a 2, riattacco dei due in parallelo, pid del palco prima/dopo, processi persi, buchi dei testimoni, guardia di `terminate-user`), `t7box.py` (processi e capo del palco dentro la scatola), `t7-abbandono.py` (ritrovato con `--abbandono-s 60`), `t7-fine.sh` (abbandono, poi scatole a 4fb3287d / d1734958) | T7, R7-R9 | vedi §13.1, 700cc1b | sul server, in /media/REMOTIX/tmp/t7 (evidenze in `giro1/` e nelle cartelle `<desktop>-<modo>/`) |
| 7b063f7, (questo commit) | **T8 — l'archivio e il banco.** `packaging/archivio/pubblica.sh` (`aggiungi <canale> <bersaglio> FILE…`, `catalogo`, `revoche`, `motore`, `rigenera`: apt con apt-ftparchive, Origin/Label REMOTIX, **Valid-Until** 60 giorni, InRelease + Release.gpg; rpm firmati con rpmsign e `repomd.xml.asc`, nel contenitore fedora:44; pacman `.sig` per ogni pacchetto, `remotix.db` rifatto con la versione più nuova, `remotix.versioni` con le vecchie; SBOM SPDX 2.3 per pacchetto con `sbom.py`, R24 rosso se la versione collegata manca o differisce da quella dichiarata); `pacchetti-motore.sh` (il motore statico impacchettato per le tre famiglie con la sua firma A e il timer spento, e `remotix-archive-keyring`); `packaging/motore/` (unità `remotix-aggiorna.service`/`.timer`, spec, PKGBUILD, LEGGIMI); le ricette dei pacchetti prendono `RX_VERSIONE`/`RX_REVISIONE` e scrivono `/usr/share/remotix/incorporate.json`. `banchi/17-t8/`: `t8-vm.sh` (un passo per chiamata: accendi, terzi, impronta, motore dall'archivio, installa, stato, collega/via col Chrome che **resta collegato** — `t8-browser.py` —, palco, timer, spegni), `t8-fiducia.sh` (catena A), `t8-catenab.sh` (R17), `t8-guasta.sh` (guasti apposta nell'archivio servito, e il ripristino), `t8-terzi.sh` (l'archivio DI TERZI e l'intruso «hello» 99.0 di R18, con una chiave estranea), `t8-prepara-guasti.sh`, `t8-porta.sh` (l'archivio su `127.0.0.1:8717`, i terzi su `:8719`: dalle VM `10.0.2.2`); `17-t1c-guarda.sh` accetta `T1C_PROGRAMMA`/`T1C_EVIDENZE` | T8 | `[M]` 30 set: archivio di prova con N (0.17.0-1 / Arch -4), N+1 (-2 / -5), N+2 Arch (-6), annuale 0.18.0 (Debian), motore 0.1.0-1…3; SBOM 8/8 (ngtcp2 1.25.0, nghttp3 1.18.0, uguali a quelle dichiarate). **R17** 9/9 (per famiglia: un byte nei metadati, i metadati firmati da una chiave estranea, un byte nel pacchetto N+1: il gestore rifiuta, versione invariata; apt esce 0 e lo dice solo nel testo: il motore ora lo legge). **R18**: su debian13 e fedora44 un archivio di terzi configurato prima — i suoi file e la sua chiave identici dopo; `hello` 99.0 pubblicato apposta nel nostro archivio: apt `-1 http://10.0.2.2:8717` (installa la 2.10 di Debian), dnf «matches only excluded packages»; nessun file in `trusted.gpg.d`. Disinstallazione dopo gli aggiornamenti: depositi e `pacman.conf`/chiave **identici** a prima (debian13, arch-kde); nell'impronta solo il rumore di sistema (apt-listchanges si spegne da solo, cups, fwupd, i `-` di gpasswd) e su Arch il gruppo `seat` creato da una dipendenza (INDIRETTA) | sul server, in `/media/REMOTIX/vm17/{archivio,terzi,t8}` (i server HTTP spenti: si riaccendono con `t8-porta.sh`) |
| c7773c5 | **T9 — il banco** `banchi/17-t9/`: `t9-porta.sh` (portatile: costruisce, firma motore e `install.sh` con la sottochiave DI PROVA A-2026, un archivio **suo** in `/media/REMOTIX/vm17/t9/archivio` — copia di quello di T8 col motore nuovo — servito su 8727; quello di T8 non si tocca), `t9-vm.sh` (`accendi rete\|senza-rete`, `motore`, `prepara`, `fuori-linea`, `r21`, `guarda` con un labwc **suo**, `rete`, `spegni`), `t9-rete.py` (la cattura: in entrata dagli inoltri / cominciato dalla VM, con la finestra dell'installazione), `cloud-init-r21.yaml`, tre file di risposte (Debian, Fedora, uno senza il consenso sulle cinture). `17-vm.sh`: `RX_VM_SEME` (un seme di cloud-init diverso), `RX_VM_RETE=,restrict=on` (rete tolta, inoltri vivi), `RX_VM_CATTURA=file.pcap` (`filter-dump` sulla scheda); senza, fa quel che faceva | R21 va provato con un seme NUOVO (instance-id nuovo ⇒ cloud-init rifà utenti, file e runcmd) sulla foto «cliente»; R22 va DIMOSTRATO, non supposto: la cattura vede anche i tentativi che `restrict` butta | `[M]` 30 set: vedi §13.1, riga T9. ⚠ Il `pkill -f` di chi accende il server HTTP nella stessa riga di ssh trova la shell di ssh e la uccide: due ssh separati | copiato sul server |
| (questo commit) | **T6 — il banco** `banchi/17-t6/`: `t6-leggi-pam.sh` (le pile PAM di sshd, SELinux, firewall, faillock di una VM dalla sua foto), `t6-vm.sh` (un passo per chiamata: `accendi`, `motore`, `installa`, `entra [utente] [parola]` col Chrome vero, `sessione` (Class, Remote, contesti), `avc` (audit.log col tempo di ogni riga **e** il giornale), `modulo <pp>`, `ban-via`, `faillock [reset]`, `ssh-parola` (ssh con la parola via `SSH_ASKPASS_REQUIRE=force`), `firewall` (firewalld e ufw, sha256 dei file delle zone), `disinstalla`, `spegni`), `t6-giro.sh` (il giro intero: firewall prima → installa → R19/R20 → faillock → disinstalla → firewall dopo → rifiuti di tutto il giro), `t6-giornale.sh`, `t6-porta.sh`; `17-t1c-guarda.sh` con `T1C_UTENTE` | R19, R20, firewall | `[M]` 30 set, giri interi: fedora44-gnome-iso, alma10-gnome-iso, tumbleweed-kde-iso, alma10-gnome, ubuntu2604-gnome-iso (ufw acceso), debian13-gnome-iso, arch-kde-iso, leap16-xfce: **ovunque** entra (nuova, ripresa, dopo il riavvio del servizio), sessione logind `Class=user`, `Remote=yes`, `Service=remotix`; parola sbagliata ⇒ rifiuto; root ⇒ rifiuto (`pam_listfile: Refused user root`); **faillock** (Arch di serie, Fedora e Alma con `authselect enable-feature with-faillock`): 3 errori da REMOTIX ⇒ la parola giusta rifiutata **da REMOTIX e da ssh**, `faillock --reset` ⇒ si rientra da tutti e due. ⚠ Il `17-vm.sh` comune cambiava mentre il banco girava («syntax error» a metà giro): il banco ne usa una copia (`RX_VM`) | sul server, in /media/REMOTIX/vm17/t6 |
| 01b062f, (questo commit) | **T9 — il banco delle interfacce.** `banchi/17-t9/t9-gui.sh` (una VM «cliente» col desktop VERO: `accendi` — foto «cliente», tavoletta USB e monitor QMP, password di nicfio e di root: l'«amministratore» del dialogo di polkit —, `accedi` dalla schermata d'accesso con la tastiera, `terminale`, `finestra <lingua>` scritta nel terminale del desktop, `password`, `clic X Y` via **QMP `input-send-event`** assoluto, `scrivi`, `tasto`, `foto`, `processi`); `t9-r36.sh` (`cli` e `tui` guidate in un pty — `ssh -tt`, tasti mandati quando lo schermo mostra il testo atteso, 120×45, i punti del flusso in `.passi` per le foto in testo —, `tui-lingua`, `raccogli`, `confronta` normalizzato); `17-vm.sh`: `RX_VM_TAVOLETTA=1` (usb-tablet + QMP in `<dir>/qmp.sock`), `hmp <macchina> "<comando>"`; `t9-porta.sh` costruisce, firma e pubblica anche `remotix-install-gui`; i file di risposte senza `consenso.cinture` (`risposte-manca.conf`: ora manca `consenso.aggiornamenti`) | la finestra va provata dove la usa una persona: la sua sessione grafica, il suo agente polkit | `[M]` 30 set: ⚠ `mouse_move` del monitor HMP manda solo movimenti **relativi**, che la tavoletta scarta (nessun evento ABS nell'ospite: letto `/dev/input/event4`) ⇒ QMP; ⚠ la finestra lanciata da ssh non trova l'agente polkit («No authentication agent found») ⇒ si lancia dal terminale del desktop; ⚠ un programma Python in heredoc non legge i comandi da stdin (il heredoc È lo stdin) | copiati sul server |
| (questo commit) | **T6 seguiti — il banco** `banchi/17-t6/t6-seguiti.sh <macchina> <pacchetti> [opzioni]` (FOTO, PRIMA nell'ambiente): accende dalla foto, installa, faillock azzerato, entra (giusta), due parole sbagliate, `faillock`, le righe PAM del giornale, sessioni e contesti, rifiuti SELinux, rispegne | punto 1 e 3 dei seguiti di T6 | `[M]` 30 set: debian13-gnome, arch-kde, fedora44-gnome-iso (`with-faillock`), leap16-kde; tutte spente e tornate alla foto | sul server, `t6/pacchetti-seguiti/` |

| cda31e6, (questo commit) | **T10 — il banco del giro intero** `banchi/17-distro/17-t10.sh` (una macchina, il copione di §7.3 dall'archivio di un rilascio vero: foto → impronta → `install.sh`+sha256 con `--risposte` → browser vero → **riavvio vero** → **aggiornamento del sistema** a N+1 con un browser collegato e il palco vivo → **disinstalla --purge** con una sessione ssh viva → impronta e R6) e `17-t10-giro.sh` (più macchine, 4 alla volta, «cliente» e «iso»); l'archivio N in `t10/archivio-N`, N+1 in `t10/archivio-N1`, serviti da un http.server su `t10/arch/<macchina>` (collegamento simbolico) sulla 8737 | T10 (§9): il giro sulle 26+6 macchine della matrice, R3-R43 in un solo copione, dal prodotto della fase 18 | `[M]` 30 set: la certificazione attesa in VM è **A_CONDIZIONI** con la sola `C-RIPIEGO` (niente scheda: R35, il fotogramma va in software OpenH264, `avc1.640c15`); il riavvio con `RX_VM_RIAVVIA_S` (in VM Fedora lo spegnimento è lento, ~5 min); R6 esclude la storia del motore (`/var/lib/remotix`) e il registro di sessione (`~/.local/state/remotix`, decisione aperta) come residui DIRETTI attesi | sul server, `/media/REMOTIX/vm17/t10/` |
| ce3f2e7 | **T10 in scatola**: `banchi/17-distro/scatole/` — `Contenitore.debian13-kde` (`task-kde-desktop`) e `Contenitore.leap16-kde` (pattern `kde`) come le VM «cliente», più le tre cose di una scatola dichiarate (§7.5); `17-scatola.sh` coi verbi di `17-vm.sh` (`costruisci`, `torna`, `avvia`, `ssh`, `ferma`, `riavvia` = riavvio del contenitore, `porte`); `17-t10.sh <m> scatola` (archivio su 127.0.0.1, porta della scatola nel file di risposte, il passo 4 dichiarato). E al passo 6 i registri di sessione nelle case si guardano prima e dopo (`registri-prima/dopo.txt`): dopo non ce ne devono essere. Sul server: `/media/REMOTIX/t10-kde/` (scatole `t10-kde-debian13`, `t10-kde-leap16`, spente; porte 8541/8542 ssh, 8531/8532 REMOTIX; archivio su 8738) | le due KDE che in VM non hanno lo screencast (§9, T10); e la regola nuova su `sessione.log` | `[M]` 1 ott: le due scatole PASS in tutti i passi, le VM di controllo pure | — |

### 13.3 L'ambiente del server

| che cosa | perché |
|---|---|
| `qemu-system-x86 qemu-utils genisoimage ovmf` installati, `nicfio` nel gruppo `kvm` (29 set) | le VM di §7; ⚠ volatile: sta nella ricetta del dopo-riavvio |
