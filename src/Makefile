# Makefile — REMOTIX, the server.
#
# -----------------------------------------------------------------------------
# ⛔ THE DEPENDENCIES, DECLARED — not "the ones that were on the machine"
#
# `LESSONS.md` §2.5-bis: "dependencies installed by hand become invisible
# within a day, and the moment you notice is always the one in
# which you need the machine to start again".  Hence this list, and the
# `dipendenze` target that CHECKS them before compiling instead of letting them fail
# twenty lines later with an error that does not name them.
#
#   ngtcp2 >= 1.25            QUIC                      (DECISIONS.md §6.4)
#   ngtcp2_crypto_ossl        the bridge to OpenSSL     (see src/tls.h)
#   nghttp3 >= 1.18           HTTP/3
#   OpenSSL >= 3.5            TLS 1.3 with the native QUIC API, and X509 for the
#                             two certificates (src/certificates.c)
#   libpam                    authentication            (SPECS.md §4.2)
#
# ⭐ AND THE FIVE OF PHASE 2, grafted on 12 August 2026 by the assembly
#    (`fasi/rapporti/P2-6-montaggio.md`).  Each one names the link that
#    carries it, because "which library is needed for what" is the question asked
#    the day one is missing:
#
#   gio-2.0 >= 2.80           the session bus: the virtual monitor
#                             (`src/session.c`) AND Mutter's ScreenCast
#                             sequence (`src/mutter.c`).  ⛔ ONCE ONLY:
#                             it serves two links, and two `pkg-config` calls that
#                             name it twice put the same -l twice
#                             without anyone noticing
#   libpipewire-0.3           the frame stream          (`src/capture.c`)
#   libdrm                    the `DRM_FORMAT_MOD_*`: headers ONLY, no
#                             library to link (`src/capture.c`)
#   ⭐ PHASE 18 (30 Sep 2026, `DECISIONS.md` §10.25): ffmpeg has LEFT the
#      product — no `-lavcodec`, `-lavutil`, `-lswscale`.  In its place:
#   libva, libva-drm            encoding on the card (`src/vadirect.c`)
#   (the BT.709 colours are ours: `src/colors709.c`, no dependency)
#   ⛔ PHASE 19 (1 Oct 2026, `DECISIONS.md` §10.27): OpenH264 and SvtAv1Enc, the
#      software fallback of `src/ripiego.c`, LEFT with the fallback —
#      *"no CPU without a card"*.
#
# ⭐ AND THE SEVENTH, of PHASE 13 (21 September 2026):
#
#   gbm                       `src/wlroots.c`, the CARD path on labwc:
#                             the buffer into which the compositor copies the
#                             frame on the GPU is allocated by US, on a
#                             `renderD*` node, and `gbm` is the only generic API
#                             that does it.  ⛔ Without it, on XFCE the pixels go through
#                             memory: `glReadPixels` in the compositor (which
#                             BLOCKS its loop, `STUDIES.md` §xfce §4.4) plus
#                             our `memcpy`.  ⚠ On Trixie `libgbm-dev`
#                             to build; `libgbm1` to run, and it is already there
#                             wherever labwc runs (wlroots wants it for itself).
#
# On Debian Trixie: `libssl-dev`, `libpam0g-dev`, `libglib2.0-dev`,
# `libpipewire-0.3-dev`, `libdrm-dev`, `libva-dev`, `libopus-dev`.
# ⚠ `ngtcp2` and `nghttp3` are NOT
# enough in the packaged version (1.11 / 1.8): they must be built from
# source, and that is what `benches/01-b2-build-ngtcp2.sh` does.
#
# -----------------------------------------------------------------------------
#   make DEPS_PREFIX=/path/where/ngtcp2/and/nghttp3/are
#
# If `pkg-config` finds them by itself, DEPS_PREFIX is not needed.

CC      ?= cc
DEPS_PREFIX ?=

NOME    := remotix

# ⭐ THE FOUR FILES OF PHASE 2 are at the end, and in chain order: session
#    (the stage) → capture+mutter (the pixels) → encoder (the bytes).  ⚠ The
#    fifth link, the video channel, does NOT appear: it lives in `rcp.c`, which was
#    already there — and it is why it is born already compared with `benches/rcp/`.
SORGENTI := main.c transport.c webtransport.c page.c command.c certificates.c \
            budget.c \
            tls.c log.c rcp.c authentication.c helper.c child.c \
            session.c capture.c mutter.c encoder.c vadirect.c \
            vulkanvideo.c bit_writer.c colors709.c audio.c sound.c \
            input.c keyboard.c cursor.c sentinel.c clipboard.c kwin.c \
            clipboard_kde.c wlroots.c wlr_input.c shape.c rediscover.c \
            render_grant.c render_node.c
OGGETTI  := $(SORGENTI:.c=.o)

# -----------------------------------------------------------------------------
# ⛔⭐ THE THREE COPIES THAT MUST BE ONE — finding R12.3, night of 10 August 2026.
#
# `rcp.c`, `rcp.h` and `authentication.c` exist in TWO folders of this
# repo — here and in `benches/rcp/` — because they are the same module mounted on two
# hosts: the product server and the graft into ngtcp2's example.  ⛔ Until
# tonight they were identical **by luck, not by construction**: no file of the
# repo compared the two copies.
#
# The concrete case nobody would have seen: `BAN_DURATION` is changed in
# `src/rcp.c` from twelve hours to one.  The product bans for an hour; `01-b6-launch.sh`
# stays green because it compares `benches/rcp/` with the copy compiled inside
# `examples/`; B8 stays green because it starts `bsslserver`.  ⛔ The defect does not
# change the colour of anything.
#
# ⭐ Hence this check, which comes BEFORE compilation and stops it.
#
# ⛔ AND THE FACTS ARE THREE, not two — `LESSONS.md` §1.9 rule 1, the common
#    face of "empty" and "forbidden":
#
#      the copies match             it compiles
#      the copies DIVERGE           ⛔ it does not compile, and the `diff` is printed
#      the twin copy IS NOT THERE   ⛔ it does not compile, unless whoever builds
#                                   DECLARES IT with TWIN=none
#
#    ⚠ The third is the one a hastily written check confuses with the
#      first: "I found no differences" and "I could not look" have the
#      same face, and the second looking like the first is a check
#      switched off that looks switched on.
TWIN ?= ../benches/rcp
GEMELLATI := rcp.c rcp.h authentication.c

# ⚠ `-std=gnu11` and not `c11`: `accept4`, `SOCK_NONBLOCK` and the ancillary
#   messages are needed, which pure POSIX does not carry.
AVVERTIMENTI := -Wall -Wextra -Wno-unused-parameter
CFLAGS   ?= -O2 -g -std=gnu11 $(AVVERTIMENTI)

# ⛔ `override`, and not a plain `+=`: whoever passes `CFLAGS=` on the command line
#    — as `build.sh` does, adding the `-I`s — would erase this
#    line together with the rest, and `struct in6_pktinfo` would vanish with an error that
#    names no option.
override CFLAGS += -D_GNU_SOURCE
# ⭐ DECISIONI §10.43 — the labwc that hosts the nested KWin (`kwin.c`): empty = the
#    distribution's, from PATH (six distributions); a path = OUR labwc at that exact path,
#    for the distributions without one (RHEL/Alma 10: `packaging/rpm/remotix.spec`).
#    A build-time choice of the package, never a runtime switch.  `make clean` first.
LABWC ?=
ifneq ($(LABWC),)
override CFLAGS += -DREMOTIX_LABWC='"$(LABWC)"'
endif
# ⭐ DECISIONS §11.6, §11.10 — bench-only endpoints and messages (`BENCH_MARK`).
BENCH ?= 0
ifeq ($(BENCH),1)
override CFLAGS += -DREMOTIX_BENCH
endif

# ⛔⭐ THE LIBRARIES OF PHASE 2, ASKED OF `pkg-config` ONCE ONLY.
#
# ⚠ `gio-2.0` is wanted by TWO links — `session.c` (the drop-in of the Shell's
#   unit and the bus) and `mutter.c` (the ScreenCast sequence).  The two reports
#   each ask for it for themselves: putting it twice is not a compilation
#   error, it is a list nobody can read any more.  ⇒ Here it is named
#   once, and the two lines below are the single place to look.
#
# ⚠ `libdrm` is only in the CFLAGS: `capture.c` takes its `DRM_FORMAT_MOD_*`,
#   which are macros in `drm_fourcc.h`.  ⛔ Putting it in the LIBS too would link
#   a library of which no function is used — and the day someone
#   removed the `#include` nobody would notice.
#
# ⛔ `override` for the same reason as the line above: `build.sh`
#    passes `CFLAGS=` on the command line to add ngtcp2's `-I`s, and
#    a plain `+=` would vanish together with the rest.  The symptom would be
#    `gio/gio.h: No such file`, which names no option.
F2_CFLAGS := $(shell pkg-config --cflags gio-2.0 libpipewire-0.3 libdrm)
F2_LIBS   := $(shell pkg-config --libs   gio-2.0 libpipewire-0.3)
override CFLAGS += $(F2_CFLAGS)

# ⭐⭐ THE SIXTH OF PHASE 3, grafted on 13 August 2026: **libva**.
#
#   libva >= 1.22            `src/encoder.c` uses it for TWO things only, and
#                            neither of them is done by libavcodec:
#                              · `vaQueryVendorString()` — WHO answered on
#                                the node that was opened.  ⛔ `[M]` 13 August: the
#                                two nodes of the test machine are Intel
#                                (renderD128, iHD) and AMD (renderD129,
#                                radeonsi) — deducing the vendor from the node
#                                number is exactly the way to go wrong
#                                without noticing;
#                              · `vaQueryConfigEntrypoints()` — whether the pair
#                                (profile, entrypoint) really exists, BEFORE
#                                opening.  Between "I asked for low_power=1" and "the
#                                driver has it" there is the same distance as
#                                between an option printed as an error and
#                                an exit 0.
#
# ⚠ On Debian Trixie: `apt install libva-dev`.  `[M]` 13 Aug 2026: in the
#   test machine's container it was already there (1.22.0), pulled in by
#   `libavutil-dev`.  ⛔ The line stays here anyway: a dependency that is there
#   because another one brought it along vanishes the day that other one
#   changes its mind, and it is the defect this list exists not to have.
# ⭐⭐ PHASE 18 (30 Sep 2026): libva has become THE card path —
#    `src/vadirect.c` uses it for everything (configuration, parameters, packed
#    headers, coded buffers), and `libva-drm` opens the node (`vaGetDisplayDRM`)
#    in place of `av_hwdevice_ctx_create`.
F3_CFLAGS := $(shell pkg-config --cflags libva libva-drm)
F3_LIBS   := $(shell pkg-config --libs   libva libva-drm)
override CFLAGS += $(F3_CFLAGS)

# ⛔ PHASE 19 (1 Oct 2026): here there were OpenH264 (only `--cflags`, opened with
#    `dlopen`) and SVT-AV1, the software fallback of `src/ripiego.c` — gone
#    with the fallback (`DECISIONS.md` §10.27).  ⚠ `-ldl` STAYS: `child.c` opens
#    libselinux with `dlopen` (Fedora, Alma), and with the old glibc it is needed.
DL_LIBS := -ldl

# ⭐⭐ PHASE 19 (1 Oct 2026, `DECISIONS.md` §10.27) — **Vulkan**: the card
#     path tried BEFORE VA-API (`src/vulkanvideo.c`, Vulkan Video:
#     `VK_KHR_video_encode_queue` + H.264/H.265).  ONLY the loader is linked
#     (`libvulkan`, Apache-2.0); the drivers (ICD: RADV, NVIDIA, ANV) live in the
#     system and the loader loads them at run time.  The shader is SPIR-V
#     already in the repository (`vulkanvideo_rgb_nv12_spv.h`): no glslang here.
#   ⚠ On Debian Trixie: `apt install libvulkan-dev` (1.4.309).  The minimum
#     1.3.274 is the header in which the video encode extensions
#     left provisional (`[R]` SDK 1.3.274, Dec 2023; `[?]` not tried
#     with an older header).
F19_CFLAGS := $(shell pkg-config --cflags vulkan)
F19_LIBS   := $(shell pkg-config --libs   vulkan)
override CFLAGS += $(F19_CFLAGS)

# ⭐ PHASE 18, line A — `libopus` DIRECTLY for audio (`src/audio.c`), since 30
#    September 2026: Opus no longer goes through libavcodec (`DECISIONS.md` §10.25).
#    `[M]` 30 Sep 2026: `opus.pc` 1.5.2 is in `remotix-costruzione` and in the
#    server's `devroot`.  ⚠ On Debian Trixie: `apt install libopus-dev`.
#    ⚠ The minimum 1.3 is for `OPUS_SET_PHASE_INVERSION_DISABLED`, which `audio.c`
#      dictates as libavcodec did: `[?]` appeared between 1.2 and 1.3, and
#      1.3.1 is the oldest we have around (Debian 12, Ubuntu 22.04).
F18A_CFLAGS := $(shell pkg-config --cflags opus)
F18A_LIBS   := $(shell pkg-config --libs   opus)
override CFLAGS += $(F18A_CFLAGS)

# ⭐⭐ THE TWO OF PHASE 4, grafted on 14 August 2026: **libei** and
#     **xkbcommon**.  The input channel wants them, and neither can be
#     replaced by a line of ours:
#
#   libei-1.0    `src/input.c` — it is THE ONLY way to inject input into a
#                Wayland compositor.  ⛔ Here `CODER.md` §4.1-bis holds without
#                discounts: a single implementation, the same everywhere.
#                `[M]` 14 Aug 2026, in the test machine's container:
#                **1.3.901**.
#
#   xkbcommon    `src/keyboard.c` — the only library that can answer the
#                question "with this layout, which key produces this
#                letter?".  `[M]` 14 Aug 2026: **1.7.0**.
#
# ⚠ On Debian Trixie: `apt install libei-dev libxkbcommon-dev`.
F4_CFLAGS := $(shell pkg-config --cflags libei-1.0 xkbcommon)
# ⭐ 15 Oct 2026 — the compositor's RECEIPT for every key (`ei_ping`, «@since
#    1.4» in the header, present in 1.3.901 = Debian 13's): `input.c` compiles
#    it only where libei has it.  ⚠ Ubuntu 24.04 (1.2.x) builds without it.
F4_CFLAGS += $(shell pkg-config --atleast-version=1.3.901 libei-1.0 && echo -DREMOTIX_EI_PING)
F4_LIBS   := $(shell pkg-config --libs   libei-1.0 xkbcommon)
override CFLAGS += $(F4_CFLAGS)

# ⭐ PHASE 12 — the stage on KDE (`kwin.c`): the Wayland protocol
#    `zkde_screencast_unstable_v1`, whose XML is in `protocols/` (taken from
#    v1's `fondamenta/remotix-c/src/protocolli/`, which had it from
#    plasma-wayland-protocols).  The protocol code is generated by
#    `wayland-scanner` at every build: only the XML is in the repository.
# ⚠ On Debian Trixie: `apt install libwayland-dev` (brings `wayland-scanner`).
F12_CFLAGS := $(shell pkg-config --cflags wayland-client)
F12_LIBS   := $(shell pkg-config --libs   wayland-client)
# ⭐ PHASE 13 — `gbm`: see the box at the top.  ⛔ A line of its own, and not inside
#    F12: the day it were missing, the error must name IT.
F13_CFLAGS := $(shell pkg-config --cflags gbm)
F13_LIBS   := $(shell pkg-config --libs   gbm)
override CFLAGS += $(F13_CFLAGS)
override CFLAGS += $(F12_CFLAGS) -I.
SCANNER    ?= wayland-scanner
# ⭐ PHASE 13: `wlr-screencopy-unstable-v1` — capture on wlroots (labwc, and
#    so XFCE and LXQt).  The XML is NOT packaged in Debian: it is in the
#    wlr-protocols source, and here it is in the repository like the other two.
# ⭐⭐ And that it is THE RIGHT ONE was not believed: regenerating the
#     protocol code from it, the tables come out **identical** to those v1
#     had generated in 2026 (`fondamenta/banchi/banco-compositori/`).  The
#     only differences are in the comments — among which, and it must be known:
#     ⚠ *"This protocol is deprecated … ext-image-copy-capture-v1 should be
#       used instead"*.  ⛔ But `[M]` 20 Sep 2026 labwc on Trixie **does not expose**
#       `ext_image_copy_capture_manager_v1`: we write against screencopy, and
#       we know it from day one instead of discovering it (`STUDIES.md` §xfce §4.6).
# ⭐ PHASE 13 — `wlr-output-management-unstable-v1`: the SIZE of the output.
#    ⛔ On wlroots the canvas is not negotiated with the stream (there is no stream there): it is
#    changed at the output, and this is the protocol that does it.  `[M]` v4 on labwc.
# ⭐ PHASE 13, INCREMENT 3 — INPUT on wlroots: libei does not exist there (`[✗]`
#    `STUDIES.md` §xfce §7), and the way is two Wayland protocols, `[M]`
#    announced by labwc: `zwp_virtual_keyboard_manager_v1` v1 (from Purism, and
#    ⚠ despite the `zwp_` prefix it is NOT in wayland-protocols: it is in the
#    wlroots source, `protocol/`) and `zwlr_virtual_pointer_manager_v1` v2
#    (from wlr-protocols).  They are in `protocols/` like the others.
# ⭐ PHASE 13 — `linux-dmabuf-unstable-v1`: the CARD's `wl_buffer`.  It is in
#    `wayland-protocols`, which the container does NOT have: the XML is in the repository like
#    the others, copied from wayland-protocols 1.44.  ⚠ At most v4 is bound
#    (`[M]` labwc announces it): it is the one with `main_device`.
# ⭐ 11 Oct 2026 — `wlr-layer-shell-unstable-v1` (wlr-protocols) and `xdg-shell`
#    (wayland-protocols 1.44, needed because layer-shell names `xdg_popup`):
#    the nested KWin's «ticker», a 1x1 transparent surface on the labwc that
#    hosts KWin (`kwin.c`).
PROTOCOLLI := zkde-screencast-unstable-v1 wlr-data-control-unstable-v1 \
              wlr-screencopy-unstable-v1 wlr-output-management-unstable-v1 \
              virtual-keyboard-unstable-v1 wlr-virtual-pointer-unstable-v1 \
              linux-dmabuf-unstable-v1 ext-data-control-v1 \
              wlr-layer-shell-unstable-v1 xdg-shell
GENERATI   := $(PROTOCOLLI:%=%-client-protocol.h) $(PROTOCOLLI:%=%-protocol.c)

# ⭐ PHASE 17 — the DEPS_PREFIX's library folder is not always `lib`:
#    cmake calls it `lib64` on Fedora and openSUSE and `lib/<multiarch>` on Debian
#    (`phases/17-the-installer.md` §4.4).  ⇒ `pkg-config` is asked INSIDE the
#    prefix (`PKG_CONFIG_LIBDIR`, which REPLACES the system folders, and
#    without `PKG_CONFIG_PATH`, which would be searched FIRST: `[M]` in the container
#    the ngtcp2 of `/usr/local` answered instead of the prefix's); if
#    it does not answer, the folders that exist.
#    ⛔ With static ngtcp2/nghttp3 (§6.3) the rpath will no longer be needed: until
#    then, let it at least point where they are.
ifneq ($(DEPS_PREFIX),)
MULTIARCH   := $(shell $(CC) -print-multiarch 2>/dev/null)
PC_PREFISSO := $(DEPS_PREFIX)/lib64/pkgconfig:$(DEPS_PREFIX)/lib/pkgconfig$(if $(MULTIARCH),:$(DEPS_PREFIX)/lib/$(MULTIARCH)/pkgconfig)
LIB_PREFISSO := $(sort $(shell env -u PKG_CONFIG_PATH PKG_CONFIG_LIBDIR='$(PC_PREFISSO)' pkg-config --variable=libdir libngtcp2 libnghttp3 2>/dev/null))
ifeq ($(LIB_PREFISSO),)
LIB_PREFISSO := $(wildcard $(DEPS_PREFIX)/lib64 $(if $(MULTIARCH),$(DEPS_PREFIX)/lib/$(MULTIARCH)) $(DEPS_PREFIX)/lib)
endif
CFLAGS  += -I$(DEPS_PREFIX)/include
LDFLAGS += $(foreach d,$(LIB_PREFISSO),-L$(d) -Wl,-rpath,$(d))
endif

# ⛔ `ngtcp2_crypto_ossl` goes BEFORE `ngtcp2`: the linker resolves symbols from
#    left to right, and the other way round the bridge's symbols would be missing.
LIBS := -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam \
        -lm $(F2_LIBS) $(F3_LIBS) $(F4_LIBS) \
        $(F12_LIBS) $(F13_LIBS) $(F18A_LIBS) $(F19_LIBS) $(DL_LIBS)
# ⚠ `-lm` is from phase 7: the test tone of `webtransport.c` calls `sin()`.
#   On glibc 2.35+ it would be superfluous (the math functions are in `libc`),
#   ⛔ but depending on that detail means breaking on a different libc
#   with an error that does not name the phase that introduced it.

.PHONY: all clean deps fingerprints bench-w1 bench-unchanged test-session test-colors709 FORCE

all: fingerprints $(NOME)

# ⛔ The comparison of the three copies: see the box at the top.  It always prints the
#    fingerprints of what it compared, so that "compared" is a readable fact
#    and not a green line.
fingerprints:
	@if [ "$(TWIN)" = "none" ]; then \
	  printf '  ⛔ TWIN=none: I did NOT compare src/ with benches/rcp/.\n'; \
	  printf '     It is not «the copies match»: it is «I did not look», and whoever\n'; \
	  printf '     builds has DECLARED it (finding R12.3).\n'; \
	  exit 0; \
	fi; \
	if [ ! -d "$(TWIN)" ]; then \
	  printf '  ⛔ the twin copy «%s» IS NOT THERE: I cannot prove that\n' "$(TWIN)"; \
	  printf '     src/rcp.c and benches/rcp/rcp.c are the same module — and they are\n'; \
	  printf '     the same module mounted on two hosts (R12.3).\n'; \
	  printf '     Pass TWIN=<path>, or TWIN=none to\n'; \
	  printf '     DECLARE building without the comparison.\n'; \
	  exit 2; \
	fi; \
	stato=0; \
	for f in $(GEMELLATI); do \
	  if [ ! -f "$(TWIN)/$$f" ]; then \
	    printf '  ⛔ %s/%s does not exist\n' "$(TWIN)" "$$f"; stato=1; continue; \
	  fi; \
	  if cmp -s "$$f" "$(TWIN)/$$f"; then \
	    printf '  OK  %-18s identical to %s  (%s)\n' "$$f" "$(TWIN)/$$f" \
	      "$$(md5sum < $$f | cut -c1-32)"; \
	  else \
	    printf '  ⛔ %s DIVERGES from %s/%s:\n' "$$f" "$(TWIN)" "$$f"; \
	    diff -u "$(TWIN)/$$f" "$$f" | head -40; \
	    stato=1; \
	  fi; \
	done; \
	if [ $$stato -ne 0 ]; then \
	  printf '  ⛔ the two copies of the SAME module do not match: not compiling.\n'; \
	  printf '     If the change is intended, it must be carried into both — or the\n'; \
	  printf '     product and the bench will measure two different codes (R12.3).\n'; \
	fi; \
	exit $$stato

$(NOME): $(OGGETTI) $(PROTOCOLLI:%=%-protocol.o)
	$(CC) $(CFLAGS) -o $@ $(OGGETTI) $(PROTOCOLLI:%=%-protocol.o) $(LDFLAGS) $(LIBS)

# ⭐ 24 Oct 2026: `-MMD -MP` writes `<obj>.d` (the headers each object really includes) and `-include` below reads them, so a
#   changed header rebuilds every object that includes it, whatever the hand-written lines further down say (those had
#   obsolete object names and covered only some objects).  Same flags otherwise, same object code.
%.o: %.c
	$(CC) $(CFLAGS) -MMD -MP -c -o $@ $<

kwin.o clipboard_kde.o wlroots.o wlr_input.o render_node.o: $(PROTOCOLLI:%=%-client-protocol.h)

# -----------------------------------------------------------------------------
# ⭐ THE CAPTURE BENCH ON WLROOTS — `benches/13-w1-one-frame.c`.
#
# ⛔ It links the SAME objects as the product (`wlroots.o`, `log.o`), not a
#    copy: it is rule R12.3 applied to a new module — a bench that
#    compiled a second `wlroots.c` would measure a code different from the one
#    that runs, and it is the defect that rule exists to prevent.
# ⚠ It is here and not in `benches/`: the product's Makefile is the only place that
#   knows how the protocol headers are generated.
# -----------------------------------------------------------------------------
BANCO_W1 := ../benches/13-w1-one-frame

$(BANCO_W1): ../benches/13-w1-one-frame.c wlroots.o registro.o \
             wlr-screencopy-unstable-v1-protocol.o \
             wlr-output-management-unstable-v1-protocol.o \
             linux-dmabuf-unstable-v1-protocol.o
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS) -lglib-2.0 -lgobject-2.0 -lgio-2.0 -lwayland-client \
	      $(F13_LIBS)

bench-w1: $(BANCO_W1)

# -----------------------------------------------------------------------------
# ⭐ THE TEST OF THE ORPHAN pcmanfm-qt PROFILE — `benches/21-session-orphan-test.c`.
#
# ⛔ `orphan_profile_pcmanfm_lxqt()` is `static` in session.c, and session.o pulls
#    in the whole product: the function is CUT from session.c (the same text that
#    is built, rule R12.3) into `orphan-extract.c`, and compiled with `log.o`.
#    No such function in session.c (the code before 8124e05c) ⇒ an EMPTY one, and
#    it is said: the old code did nothing, and the test must go red on it.
# ⚠ The system folders are `$(TEST_SESSION)/sys-a` and `sys-b`, fixed at build
#   time; HOME is a fresh temporary folder made by the test.
# -----------------------------------------------------------------------------
TEST_SESSION ?= /tmp/remotix-test-session

test-session: log.o ../benches/21-session-orphan-test.c session.c
	@mkdir -p $(TEST_SESSION)
	@sed -n '/^static void orphan_profile_pcmanfm_lxqt(void)$$/,/^}$$/p' session.c \
	  > $(TEST_SESSION)/body.c; \
	if [ -s $(TEST_SESSION)/body.c ]; then \
	  { echo '#define ORPHAN_EXTRACTED 1'; cat $(TEST_SESSION)/body.c; } > $(TEST_SESSION)/orphan-extract.c; \
	else \
	  echo '  ⛔ orphan_profile_pcmanfm_lxqt() is NOT in session.c: testing an empty one'; \
	  { echo '#define ORPHAN_EXTRACTED 0'; \
	    echo 'static void orphan_profile_pcmanfm_lxqt(void) {}'; } > $(TEST_SESSION)/orphan-extract.c; \
	fi
	$(CC) $(CFLAGS) -I. -I$(TEST_SESSION) \
	  '-DORPHAN_SYSTEM_A="$(TEST_SESSION)/sys-a"' '-DORPHAN_SYSTEM_B="$(TEST_SESSION)/sys-b"' \
	  $$(pkg-config --cflags glib-2.0) -o $(TEST_SESSION)/test \
	  ../benches/21-session-orphan-test.c log.o $$(pkg-config --libs glib-2.0)
	$(TEST_SESSION)/test
# ⭐ 15 Oct 2026 — the desk test of the «unchanged» filter (`unchanged.h`):
#    the header itself, the SAME one capture.c includes, on synthetic frames.
BANCO_UC := ../benches/20-unchanged-test

$(BANCO_UC): ../benches/20-unchanged-test.c unchanged.h
	$(CC) $(CFLAGS) $(shell pkg-config --cflags glib-2.0) -o $@ $< \
	      $(shell pkg-config --libs glib-2.0)

bench-unchanged: $(BANCO_UC)
	$(BANCO_UC)


# ⭐ 15 Oct 2026 — the desk test of the LAST rows of the 4:2:0 conversion
#    (`colors709.c`), the arithmetic of F-011's green last row, and the padding
#    of the card's aligned surface: see the box at the top of
#    `benches/23-colors709-edge-test.c`.  Built twice, with the SSE2 and with
#    the plain C (`COLORS709_NO_SIMD`): two codes, one answer.
#    ⛔ A fresh `mktemp -d`: here a binary is built AND run.
test-colors709: ../benches/23-colors709-edge-test.c colors709.c colors709.h
	@set -e; d=$$(mktemp -d "$${TMPDIR:-/tmp}/remotix-test-colors709.XXXXXX"); \
	trap 'rm -rf "$$d"' EXIT; \
	$(CC) $(CFLAGS) -I. -o "$$d/simd" ../benches/23-colors709-edge-test.c colors709.c -lm; \
	$(CC) $(CFLAGS) -I. -DCOLORS709_NO_SIMD -o "$$d/c" \
	  ../benches/23-colors709-edge-test.c colors709.c -lm; \
	"$$d/simd"; "$$d/c"

%-client-protocol.h: protocols/%.xml
	$(SCANNER) client-header $< $@

%-protocol.c: protocols/%.xml
	$(SCANNER) private-code $< $@

clean:
	rm -f $(OGGETTI) $(OGGETTI:.o=.d) $(NOME) $(GENERATI) $(PROTOCOLLI:%=%-protocol.o) .flags

# ⛔ The dependency check SAYS what is missing, instead of making the
#    compiler fail on an `#include` nobody connects to the missing library.
#
# ⭐ PHASE 17 — and now it also looks at the MINIMUM VERSIONS, not only that the
#    headers are there: an old header is there, and the compiler
#    falls twenty lines later on a function that does not exist.
#    The minimums, and where they come from (`phases/17-the-installer.md` §4.4):
#      (openh264 2.5 and SvtAv1Enc 2.3 left with the fallback, phase 19)
#      openssl 3.5.0          the native QUIC API (`ngtcp2_crypto_ossl`)
#      libngtcp2 1.25.0       the `NGTCP2_STREAM_CLOSE2_FLAG_*` of `transport.c`
#      libnghttp3 1.18.0      the one it is built with (`src/Containerfile`);
#                             `[?]` the real minimum was not looked for
#      libei-1.0 1.1.0        `ei_region_get_mapping_id` (`input.c`); `[R]` missing
#                             in the 1.0.0 header, present in 1.1.0
#      libpipewire-0.3 0.3.48 `PW_KEY_NODE_FORCE_QUANTUM`; `[M]` 29 Sep 2026:
#                             capture/cursor/sound compile with Ubuntu 22.04's
#                             0.3.48; `[R]` the key is missing in 0.3.44
#      gio-2.0 2.80           as it was declared; we would need 2.72
#                             (`g_get_user_state_dir`, `session.c`)
#    ⛔ Three outcomes and not two: "too old", "pkg-config does not know it" (which
#       with DEPS_PREFIX may only mean that the `.pc` is not in the path) and
#       "fine".  The first two make it exit with an error, but they are SAID differently.
#      vulkan 1.3.274         the final video encode extensions (phase 19,
#                             `src/vulkanvideo.c`); `[?]` not tried below
MINIMI := openssl:3.5.0 libva-drm:0 \
          libngtcp2:1.25.0 libngtcp2_crypto_ossl:1.25.0 libnghttp3:1.18.0 \
          libei-1.0:1.1.0 libpipewire-0.3:0.3.48 gio-2.0:2.80 xkbcommon:0 \
          libva:0 libdrm:0 gbm:0 wayland-client:0 opus:1.3 vulkan:1.3.274

deps:
	@stato=0; \
	if [ -n "$(DEPS_PREFIX)" ]; then \
	  PKG_CONFIG_PATH="$(PC_PREFISSO)$${PKG_CONFIG_PATH:+:$$PKG_CONFIG_PATH}"; \
	  export PKG_CONFIG_PATH; \
	fi; \
	for m in $(MINIMI); do \
	  p=$${m%%:*}; v=$${m#*:}; d=">= $$v"; [ "$$v" = 0 ] && d="no minimum"; \
	  if ! pkg-config --exists "$$p" 2>/dev/null; then \
	    printf '  ??  %-24s pkg-config does not know it (%s)\n' "$$p" "$$d"; stato=1; \
	  elif pkg-config --atleast-version="$$v" "$$p"; then \
	    printf '  OK  %-24s %s (%s)\n' "$$p" "$$(pkg-config --modversion $$p)" "$$d"; \
	  else \
	    printf '  NO  %-24s %s: TOO OLD, >= %s needed\n' "$$p" "$$(pkg-config --modversion $$p)" "$$v"; stato=1; \
	  fi; \
	done; \
	for h in ngtcp2/ngtcp2.h ngtcp2/ngtcp2_crypto_ossl.h nghttp3/nghttp3.h \
	         openssl/ssl.h security/pam_appl.h \
	         gio/gio.h pipewire/pipewire.h drm_fourcc.h \
	         va/va.h va/va_drm.h gbm.h opus.h vulkan/vulkan.h; do \
	  if printf '#include <%s>\nint main(void){return 0;}\n' "$$h" | \
	     $(CC) $(CFLAGS) -x c - -o /dev/null $(LDFLAGS) $(LIBS) 2>/dev/null; then \
	    printf '  OK  %s\n' "$$h"; \
	  else \
	    printf '  NO  %s\n' "$$h"; stato=1; \
	  fi; \
	done; \
	exit $$stato

# ⛔ Phase 16 (25 Sep 2026): `log.h` has become a file of MACROS
#    (`registro_dice` & co. add __FILE__/__LINE__): an old object
#    looks for the symbol that is no longer there and linking falls half way.  Every
#    object goes through the log, so it depends on it — all of them, without a list.
$(OGGETTI): log.h .flags

.flags: FORCE
	@printf '%s\n' '$(CFLAGS)' > $@.tmp && (cmp -s $@.tmp $@ || mv -f $@.tmp $@) && rm -f $@.tmp

# ⛔ `main.c` NO LONGER depends on `session.h`, `capture.h`, `mutter.h` and
#    `encoder.h`, and the line that removes them is the same decision as
#    `DECISIONS.md` §1.10-bis: those four links are opened by the CHILD, which runs
#    as the user.  The parent is root, and root has nobody to talk to.
main.o:           helper.h certificates.h command.h child.h page.h rcp.h \
                  log.h tls.h transport.h rediscover.h
transport.o:      transport.h helper.h log.h webtransport.h
webtransport.o:   webtransport.h helper.h rcp.h log.h child.h audio.h
page.o:         page.h certificates.h rcp.h log.h
command.o:        command.h rcp.h log.h
certificates.o:    certificates.h log.h
tls.o:            tls.h log.h
log.o:       log.h
rcp.o:            rcp.h
# ⚠ `authentication.c` includes no header of ours, so this
#   line has no prerequisites — but it is there, because it was the only one of the ten
#   missing and a uniform omission reads better than a single exception.
authentication.o:
# ⭐ `helper.c` — the process that queries PAM in place of the single thread
#    (`DECISIONS.md` §1.10).  ⚠ It is NOT among the `GEMELLATI`: it belongs to the PRODUCT
#    only, because the graft of `benches/rcp/` has no loop of its own to free.
helper.o:       helper.h log.h
# ⭐ `child.c` — one process per user, running as them (`DECISIONS.md`
#    §1.10-bis).  ⚠ It is the ONLY file that sits on both sides of the
#    privilege drop: the parent's half includes nothing of phase 2, the
#    child's half includes all four.  ⚠ It is NOT among the `GEMELLATI`: it belongs to the
#    product only, like `helper.c`.
child.o:         child.h log.h session.h capture.h mutter.h encoder.h \
                  input.h sentinel.h audio.h sound.h clipboard.h rediscover.h \
                  render_grant.h render_node.h unchanged.h

# ⭐ THE FOUR OF PHASE 2.  ⚠ NONE is among the `GEMELLATI`: they belong to the PRODUCT
#    only — in `benches/rcp/` they do not exist, because the graft into ngtcp2's
#    example has neither a graphical session nor an encoder.
session.o:       session.h log.h

# ⭐ THE GUARDIAN OF PHASE 5 — the emitter that was missing for `0x04` and `0x05`.
# ⚠ It is not among the `GEMELLATI` and cannot go there: `rcp.c` reaches it by
#   HOOK, because the copy grafted into ngtcp2 has no system bus.
sentinel.o:     sentinel.h log.h
# ⭐ PHASE 17, T7 — the live desktops left by a previous parent (logind and /proc).
rediscover.o:        rediscover.h
# ⭐ 1.5 (DECISIONS.md §11.4) — the card for a stale user manager.
render_grant.o:   render_grant.h rediscover.h log.h
# ⭐ 1.5 (SPECS audit, 15 Oct 2026) — which card encodes: the compositor's.
render_node.o:    render_node.h kwin.h
capture.o:        capture.h log.h cursor.h unchanged.h
mutter.o:         mutter.h log.h
encoder.o:   encoder.h log.h vadirect.h vulkanvideo.h bit_writer.h colors709.h
# ⭐ PHASE 18: the card with direct libva, and the bit writer of the headers;
#    our BT.709 colours (the card's "from memory" path).  ⛔ The
#    software fallback (`ripiego.c`: OpenH264, SVT-AV1) is gone, phase 19.
vadirect.o:      vadirect.h log.h bit_writer.h colors709.h
# ⭐ PHASE 19: the card in Vulkan Video, with the embedded SPIR-V shader
#    (`vulkanvideo_rgb_nv12_spv.h`, generated by `benches/19-vulkan/19-shader.sh`
#    from the `.comp` next to it: the shader compiler is NOT needed to build).
#    ⚠ `-Wno-missing-field-initializers`: Vulkan structures have dozens
#    of fields and are filled by name (`.sType = …`), and `-Wextra`'s warning
#    on every `{ .sType }` would cover the real warnings.  Only on this object.
vulkanvideo.o:    vulkanvideo.h log.h vulkanvideo_rgb_nv12_spv.h
vulkanvideo.o:    CFLAGS += -Wno-missing-field-initializers
bit_writer.o:  bit_writer.h
colors709.o:      colors709.h

# ⭐ THE SOUND ENCODER — phase 7.  ⚠ It is not among the `GEMELLATI`: it belongs to the
#   product, and the graft into ngtcp2 has nothing to play.
#   ⛔ Since 30 Sep 2026 (phase 18) it calls `libopus` directly: the dependency is
#      `F18A_LIBS` above.  Until the 29th it went through `libavcodec`.
audio.o:          audio.h log.h

# ⭐ THE SESSION'S SOUND — phase 7: the virtual sink and the capture of its
#   MONITOR.  ⛔ In the session there is nothing to capture and it must be CREATED: `[M]`
#   5 August 2026, with pipewire/wireplumber all running `wpctl status` shows
#   zero devices, zero sinks, zero sources — it is the normal case of a server without a
#   sound card.  ⚠ The reference (`gnome-remote-desktop`) opens the capture
#   on the sinks it FINDS and never creates a sink: with its code, here, not a
#   single sample would arrive — and without an error anywhere.
sound.o:          sound.h log.h audio.h

# ⭐⭐ THE THREE OF PHASE 4 — and their lines are not a formality.
#
# ⛔ `input.h`, `keyboard.h` and `cursor.h` are the SEAMS, and a seam is
#    changed by the coordinator while the links write the implementation: without
#    these lines `make` would leave standing a `.o` compiled against the
#    contract of half an hour ago.  ⚠ The symptom would not be an error: it would be a
#    program that links and misbehaves — the most expensive form of error
#    of all, because nobody connects it to the change that produced it.
#    `[M]` 14 August 2026: the defect was reported by the cursor
#    link, which had noticed that `capture.o` was not rebuilt.
input.o:          input.h keyboard.h log.h mutter.h session.h kwin.h
keyboard.o:       keyboard.h log.h
cursor.o:        cursor.h log.h

# ⭐ THE SESSION'S CLIPBOARD — phase 7.  ⚠ It is not among the `GEMELLATI` and cannot
#    go there: it speaks D-Bus (`gio-2.0`), which is not inside ngtcp2's `examples/`.
#    ⛔ It is the same reason why `rcp.c` reaches this module
#    by HOOKS and not by `#include`.
clipboard.o:        clipboard.h log.h

# ⭐ The automatic dependencies written by `-MMD` (absent on the first build: `-include` does not mind).
-include $(OGGETTI:.o=.d)
