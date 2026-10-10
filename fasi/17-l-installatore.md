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
