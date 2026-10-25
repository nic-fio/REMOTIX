/*
 * child.c — one process per user, running as that user and holding the stage.
 *
 * The reasoning, the three differences from the helper and the invariants are
 * spelled out in `child.h`.  Here are the choices that only show in the code.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ THE MOST IMPORTANT CHOICE IN THIS FILE: `fork()` **AND THEN `exec()`**
 *
 * A `fork()` alone would have been enough to run the child as the user.  The
 * `exec` is done too for three reasons, and the first one decides on its own:
 *
 *   1. ⛔ **the parent's memory holds the server's private TLS key**
 *      (`certificates.c`), the ban table and the state of every other
 *      session.  A child running as the user **without** `exec` would hand it
 *      over: `/proc/self/mem` is readable by the owner of the process, and
 *      the user is the owner.  ⇒ It would be the worst defect this work could
 *      produce — isolation between users built and then handed to the first
 *      one who walks in;
 *   2. ⭐ **the environment is composed from scratch** (`CODER.md` §4.5) — and
 *      with `execve` it is not a discipline, it is the signature of the call:
 *      `envp` is written variable by variable, and what is not written is not
 *      there;
 *   3. ⚠ **the child opens PipeWire and GLib, which make threads.**  The parent
 *      never touches them (it is root: it would have nobody to talk to), so
 *      the `fork` starts from a single-threaded process — but a fresh image
 *      removes the question instead of answering "today it is fine".
 *
 * ⛔ And the drop to the user happens BEFORE `exec`, not after: so the new image
 *    is born already without privileges, and there is no instant in which the
 *    user's code could run as root.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ THE CHECK THAT WOULD HAVE LOOKED LIKE A CHECK — `SO_PEERCRED`
 *
 * The question "who is at the other end of this socket?" has an obvious
 * answer, `getsockopt(SO_PEERCRED)`, ⛔ **and on a `socketpair()` it is the
 * wrong answer**: the kernel puts there the credentials of the process that
 * called `socketpair()` — that is the parent, root — on **both** ends, and
 * never updates them again.  ⇒ A parent that checked that way would have read
 * `uid 0` for a child dropped to `uid 1001`, would have seen a number, and
 * would have checked nothing.
 *
 * ⭐ What is used is `SO_PASSCRED` + `SCM_CREDENTIALS`: the kernel stamps
 *    **every message** with the pid/uid/gid **of the sender at the moment of
 *    writing**, and an unprivileged process cannot declare false ones.  It is
 *    the only way "verified on every message" is a fact and not a promise.
 */
#include "child.h"

/* ⛔ ONLY for the session cap (`RCP_SESSION_CAP`, `rcp_cap()`).  ⚠ The
 *    child does NOT speak RCP: it speaks to the parent over a `SOCK_SEQPACKET`.
 *    This include is the declaration of the link between two caps, not a
 *    dependency on the protocol. */
#include "rcp.h"
#include "log.h"
#include "rootside.h"
#include "reapwait.h"
/* ⭐ PHASE 17 T7: the PARENT's half asks logind and /proc whether a desktop
 *    is alive (nothing of the stage). */
#include "rediscover.h"
#include "render_grant.h"
#include "render_node.h"

#include <dirent.h>
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <stdatomic.h>
#include <grp.h>
#include <poll.h>
#include <pthread.h>
#include <pwd.h>
#include <security/pam_appl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* Only the child needs the stage.  The parent includes none of this, and it is
 * not tidiness: it is the declaration that root does not talk to it. */
#include "clipboard.h"
#include "audio.h"
#include "capture.h"
#include "unchanged.h"
#include "wlroots.h"
#include "vulkanvideo.h"
#include <drm_fourcc.h>
#include "sentinel.h"
#include "sound.h"
#include "encoder.h"
#include "input.h"
#include "mutter.h"
#include "kwin.h"
#include "session.h"

/* ⛔⭐ THE SAME SESSION CAP AS `rcp.c`, AND NOW IT IS TRUE — 25 Aug
 *     2026.  One user per child (I2), so the number is the same.
 *
 * ⛔ Until yesterday this comment said *"when that becomes a pixel budget,
 *    this will follow it from the same place"*, and ⛔ **the link did not
 *    exist**: `MAX_ATTACCATE` was a `static` of `rcp.c` and this was an
 *    independent literal.  `[M]` §6.4 measured it: tree built with
 *    `MAX_ATTACCATE=2`, and `MAX_FIGLI` stayed **16**.
 * ⇒ Now the number comes from `rcp.h`, and the compiler knows the link the
 *   comment declared.  ⚠ This file includes `rcp.h` **only** for this:
 *   the child does not speak RCP, it speaks to the parent. */
/* ⭐⭐ AND SINCE THE EVENING OF 25 AUG 2026 IT IS NO LONGER A FIXED SIZE: the
 *     table is **allocated** on the cap in force (`rcp_cap()`, which
 *     `--session-cap` moves at startup).  ⛔ The `MAX_FIGLI` that was here
 *     is gone and was not left beside it as a "maximum": it would have been a
 *     second number.  The value in force for THIS table is `f->cap`, and it
 *     is read only once, in `children_turn_on()`. */

/* ⛔ How long a newborn child is given to say WHO IT IS.  Beyond that, it is
 * declared faulty and killed: a process running as a user that does not
 * answer is not a stage, it is a forgotten process.
 * ⚠ After the first "I am", there is NO deadline: that is invariant I4 — the
 *   stage outlives the detach, and a child that is silent because nobody is
 *   asking it anything is doing its job. */
#define SHOW_UP_DEADLINE_MS 15000
/* ⭐ Audit of the session (25 Oct 2026): the once-a-minute «who are you» question (`children_recheck()`) is the only thing the parent ASKS of a child that
 *   has already introduced itself.  If it stays unanswered this long the child's loop is stuck (a call that does not return), and nobody will ever notice:
 *   it is killed — unless it has sent ANY message since the question: a child that is still delivering (frames, canvas, ...) but does not answer is not
 *   killed, one line says so and the wait starts again.  This does not touch I4: the child is not silent because nobody asks it anything, it is being
 *   asked, every minute. */
#define WHOAMI_DEADLINE_MS 180000

/* ⛔ §6.2 of `RCP.md`: a legal frame reaches 16 MiB.  The cap is here because
 * the bytes pass through here, and a lower cap of OURS would bite in place of
 * the protocol's one — the form of error the assembly has already paid for
 * with `WT_QUEUE_MAX` (`P2-6-montaggio.md` §5.6). */
#define FRAME_MAX (16u * 1024u * 1024u)

/* How much fits in one SEQPACKET message.  ⚠ It is not a protocol cap: it is
 * the piece into which a frame that would not fit in the socket is cut. */
#define MAX_PIECE 32768u

/* ⛔ THE SHARE OF ONE CHILD IN ONE ROUND OF `poll` (fairness review, 15 Oct 2026).
 *
 *     The child runs as the session user, and the parent reads it inside the
 *     server's single loop.  Reading a socket "until it is empty" let ONE child
 *     that writes without pause hold `children_move()` for as long as it wrote
 *     — measured: 2.95 s, 374k–584k messages — and every other session, the
 *     page and the logins waited behind it.
 * ⇒ At most `ROUND_MSGS_MAX` messages or `ROUND_NS_MAX` of reading per child
 *   per round, whichever comes first, then the next child.  ⚠ Nothing is lost:
 *   `poll` is level-triggered and wakes again at once while messages are still
 *   queued.  An honest 4K keyframe (~64 pieces of `MAX_PIECE`) takes two
 *   rounds instead of one. */
#define ROUND_MSGS_MAX 32
#define ROUND_NS_MAX 2000000ull

/* ⛔ A REFUSED message writes a line in root's log, and a child that sends
 *    nothing else would write the log full.  ⇒ The first `REFUSED_LOG_BURST`
 *    of every `REFUSED_LOG_WINDOW_MS` are written as they are, the rest only
 *    counted, and the count is written once the window has passed. */
#define REFUSED_LOG_BURST 5
#define REFUSED_LOG_WINDOW_MS 10000

/* ⛔ And a child that sends ONLY refused messages, this many in a row without a
 *    single one accepted, is not a stage with a bug: our own child never writes
 *    one (same binary, same version).  It is sent away like the other
 *    violations (wrong credentials, wrong uid in INTRO): SIGKILL and farewell.
 *    ⚠ An honest message in between starts the count again. */
#define REFUSED_STREAK_MAX 4096

/* ⛔ How often the parent asks "who are you" again — and checks that the
 * user's NAME still resolves to the child's uid.  ⚠ One minute, and the number
 * is not caution: it is the maximum time for which a child that had changed
 * identity — or a pid recycled after a death we did not reap, or a name NSS
 * now gives to another uid — would stay in the table without anyone having put
 * it to the test again. */
#define RECHECK_MS 60000
/* a child that answers «my name no longer resolves» every minute is told in the log once in this time */
#define NAME_GONE_LOG_MS 600000

#define CHILD_VERSION 1

/* ⛔ How long «the end was asked» counts as «closing» for a child that is still
 *    alive (see `closing_asked_ms`): the desktop logs out in a few seconds; past
 *    this the child is treated as alive again, and a login attaches to it. */
#define CLOSING_GRACE_MS 30000
/* ⭐ 1.5: SIGKILLs (3 s apart) before a slot whose CHILD_EXITED never came is freed (network mode). */
#define EXITED_FALLBACK_ROUNDS 10

enum {
	MSG_CHI_SEI = 1,      /* parent → child */
	MSG_SHUT_DOWN = 2,     /* parent → child */
	MSG_RESEND_STAGE = 3,/* parent → child */
	/* ⭐⭐ PHASE 3 — "capture, and this one must be a keyframe".  ⛔ It is the
	 *     seam that was missing: `codificatore_chiedi_chiave()` had no caller
	 *     in the product, and the stage lives in ANOTHER PROCESS — this is the
	 *     line that crosses the boundary. */
	MSG_VIDEO = 4,        /* parent → child */
	/* ⭐⭐ PHASE 4 — INPUT.  ⛔ And the reason it crosses the socket is the
	 *     same as `MSG_VIDEO`, and it is a fact of the architecture, not a
	 *     choice: **`libei` talks to the user's session, and the user's
	 *     session is in THIS process**, while QUIC, RCP and the client's
	 *     bytes are in the parent.  ⇒ Between the key pressed in the browser
	 *     and the key pressed on the desktop there is a process boundary, and
	 *     this is the line that crosses it. */
	MSG_INPUT = 5,        /* parent → child */
	/* ⭐⭐ §5-bis.7 — THE KEYBOARD LAYOUT, and it crosses the boundary for the
	 *     same reason as input: the layout is applied by the user's SESSION,
	 *     which is in this process, and the one asking for it is the client,
	 *     which talks to the parent.
	 * ⛔ And it has an envelope of ITS OWN instead of travelling inside
	 *    `MSG_INPUT` like `RITELA`: the name is a 64-byte string, and putting
	 *    it in the input body would mean paying for it on EVERY mouse movement
	 *    — dozens per second — for something that happens once per attach.
	 *    `CODER.md` §1-bis: every extra byte on the hot path is paid in
	 *    latency, and that is the number that weighs more than frames. */
	MSG_LAYOUT = 6, /* parent → child */
	/* ⭐⭐ PHASE 7 — AUDIO, and it crosses the boundary for the THIRD time for
	 *     the same reason as `MSG_VIDEO` and `MSG_INPUT`, which by now is a law
	 *     of the architecture and not a choice:
	 *
	 *       **PipeWire talks to the user's session, and the user's session
	 *       is in THIS process**; the datagrams of `RCP.md` §6.3 are written
	 *       by the parent, which holds QUIC.
	 *
	 * ⛔ And the child ENCODES before sending, instead of shipping the raw
	 *    samples.  It is not just any optimisation: 20 ms of stereo PCM are
	 *    **3840 bytes**, the same block in Opus measures `[M]` **241-439**.
	 *    Shipping raw would mean paying **ten times** the socket for every
	 *    block, fifty times a second, on a path that `CODER.md` §1-bis says
	 *    to measure in latency.
	 * ⚠ The price, declared: the codec is negotiated by the PARENT (§4.3) and
	 *   the encoding is done by the child, so the number must cross the
	 *   boundary — and that is exactly what this message carries. */
	MSG_AUDIO = 7,        /* parent → child */
	/* ⭐⭐ PHASE 7 — THE CLIPBOARD, and it crosses the boundary for the FOURTH
	 *     time for the same reason as video, input and audio: **the clipboard
	 *     belongs to the compositor** (`STUDIES.md` §gnome §10), and this process
	 *     is the one talking to the compositor; §7.4 is written by the parent.
	 *
	 * ⛔ `MSG_CLIPBOARD_OFFER` does NOT carry the text, and it is §7.4's
	 *    "announce first, then pull" applied on this side: the client's text
	 *    is requested when someone in the session really pastes.  ⚠ Someone
	 *    who copies a whole document on the phone does not make it cross the
	 *    socket until that moment comes — and most of the time it does not. */
	MSG_CLIPBOARD_OFFER = 8,  /* parent → child */
	/* ⛔ And this one does carry it, **in pieces**: it is the answer to a
	 *    request from the session, and the cap of §5.4 is 1 000 000 bytes —
	 *    thirty times `MAX_PIECE`. */
	MSG_CLIPBOARD_FROM_CLIENT = 9, /* parent → child */
	MSG_INTRO = 10,      /* child → parent */
	MSG_STAGE = 11,     /* child → parent */
	MSG_FRAME = 12,/* child → parent */
	/* ⭐⭐ PHASE 4 — THE CURSOR SHAPE, and it crosses the boundary in the
	 *     OPPOSITE direction to input.  ⛔ For the same reason: the cursor
	 *     metadata comes from PipeWire, that is in the child, and the channel
	 *     it must be sent on (`CURSOR_SHAPE`, `RCP.md` §7.2) lives in the
	 *     parent.
	 * ⚠ And like the frame it goes IN PIECES: a 256x256 BGRA cursor is 262 144
	 *   bytes, eight times `MAX_PIECE`. */
	MSG_CURSOR = 13,   /* child → parent */
	/* ⭐⭐ THE ANSWER TO THE CANVAS — 15 Aug 2026, and it was born from a refutation.
	 *
	 * ⛔ The first draft did not have this message: the parent ASKED for the
	 *    canvas and then GUESSED the answer from the frames — "if one of a
	 *    different size arrives, the stage has obeyed".  ⚠ And guessing was
	 *    not enough, for three cases that cannot be told apart by looking at
	 *    the pixels:
	 *
	 *      · the stage ALREADY has that size ⇒ no new frame will arrive, and
	 *        the parent would wait to the end of the three seconds for nothing;
	 *      · the stage is not there or did not make it ⇒ the fact is known
	 *        AT ONCE, and in the wrong process;
	 *      · two chained requests (the user drags the edge) ⇒ the frame of the
	 *        FIRST would have been taken as the answer to the SECOND, and the
	 *        desktop would have settled on the wrong size **without any count
	 *        noticing**.
	 *
	 * ⇒ The child answers, and carries BOTH numbers: what it had been asked
	 *   (so the parent recognises which request it is answering) and what the
	 *   stage really has (`0x0` = it did not make it).  ⭐ And it sends it only
	 *   after SEEING a frame at that size, except in the "I already have it"
	 *   case: the truth remains the frame, this is the way to say it. */
	MSG_CANVAS = 14,      /* child → parent */
	/* ⭐ §7.6 — "the graphical session is over", and no client asked for it:
	 * the user chose "Log out…" from the desktop menu. */
	MSG_SESSION_FINISHED = 15, /* child → parent */
	/* ⭐⭐ PHASE 7 — AN ALREADY ENCODED AUDIO BLOCK, ready for the datagram.
	 *
	 * ⛔ It does NOT go in pieces like the frame and the cursor, and it is not
	 *    a simplification: a block that does not fit in a datagram **cannot be
	 *    sent at all** (`RCP.md` §6.3, "one datagram, one block"), so a block
	 *    larger than `MAX_PIECE` would already be a defect upstream.
	 *    ⚠ The largest RCP/1 provides for is PCM: 960 bytes.
	 *
	 * ⛔ And if the socket is full the block IS DROPPED instead of waiting:
	 *    §6.3 forbids retransmission, and a child that blocked on writing would
	 *    stop the DESKTOP CAPTURE — late audio would cost the frames. */
	MSG_BLOCK = 16, /* child → parent */
	/* ⭐⭐ PHASE 7 — "THE SESSION HAS COPIED THIS TEXT", and it goes **in
	 *     pieces** like the frame and the cursor.
	 *
	 * ⛔ It arrives ALREADY READ, and it is not a convenience: the announcement
	 *    of §7.4 carries `u32 length`, and nobody knows how long a text is
	 *    without having read it.  ⇒ The "announce first, then pull" lives on
	 *    the WIRE, where it is needed; on this side the text is already there.
	 * ⛔ And it arrives already validated as UTF-8, already without zeros in
	 *    the middle and already within the cap: those three checks are in
	 *    `clipboard.c`, where the text still exists whole and where it is known
	 *    WHICH of the three bit. */
	MSG_CLIPBOARD_FROM_SESSION = 17, /* child → parent */
	/* ⭐⭐ "SOMEONE IN THE SESSION IS PASTING" — and the parent MUST answer,
	 *     even empty-handed: a `SelectionTransfer` with no answer leaves the
	 *     pasting application hanging indefinitely, and the symptom is "the
	 *     desktop has frozen" (`src/clipboard.h`). */
	MSG_CLIPBOARD_REQUEST = 18, /* child → parent */
	/* ⏳ `RCP.md` §13 (PROPOSED) — «the client's decoder is behind: take no
	 *    more than N frames per second».  ⛔ It crosses the boundary for the
	 *    same reason as `MSG_VIDEO`: the capture and the encoder are HERE, the
	 *    client's message arrives in the parent. */
	MSG_PACE = 19 /* parent → child */
};

struct head {
	uint8_t magic[4]; /* 'F','I','G','1' */
	uint16_t kind;
	uint16_t version;
	uint64_t serial;
	/* ⛔ Who the SENDER believes the child is.  It is not proof of anything —
	 *    the proof is written by the kernel — and it is here so that a mismatch
	 *    between what one believes and what the kernel says shows **at once**,
	 *    instead of becoming pixels delivered to the wrong person. */
	uint32_t declared_uid;
	uint32_t byte; /* body bytes after this structure */
};

struct body_whoami {
	uint32_t uid, euid, suid;
	uint32_t gid, egid, sgid;
	uint32_t pid, ppid;
	uint32_t descriptors;   /* how many remain open after `close_range` */
	uint32_t runtime_c_e;   /* the runtime folder exists and is its own */
	uint32_t socket_bus_c_e;/* the session bus socket exists */
	char user[64];
	char runtime[160];
	/* ⭐ The NAME check, moved out of the parent's loop (candidate `nss-fuori`): in the answer to the parent's «who are
	 * you» question (every RECHECK_MS) the CHILD looks its own name up and says what NSS answered.  At the end of the
	 * struct on purpose: a body of the old size (the first introduction, the fuzz seeds) still reads, with 0 = not asked. */
	uint32_t name_check; /* NAME_NOT_ASKED / NAME_HOLDS / NAME_GONE / NAME_OTHER_UID */
	uint32_t name_uid;   /* NAME_OTHER_UID: the uid NSS gave the name */
};
/* the size of the body before `name_check` existed: the least a parent accepts */
#define WHOAMI_MIN offsetof(struct body_whoami, name_check)
enum { NAME_NOT_ASKED = 0, NAME_HOLDS = 1, NAME_GONE = 2, NAME_OTHER_UID = 3 };

struct body_stage {
	uint32_t bus_open;      /* the CONNECTION to the bus succeeded */
	uint32_t state_session;  /* SessionState, 0 = SANA */
	uint32_t take;           /* CaptureTake */
	uint32_t monitor_before, monitor_after;
	uint32_t width, height, stride, bit;
	uint32_t streams;          /* how many codecs delivered */
	char monitor[64];
	char fault[224];
};

/* ⛔⭐ The stage's answer to the canvas request.  ⚠ `got_w == 0` means
 *     "I did not make it", and it is NOT a size: it is the other face of the
 *     zero of `CODER.md` §3.10, declared instead of inferred from silence. */
struct body_canvas {
	uint32_t intended_w, intended_h;
	uint32_t got_w, got_h;
	/* ⭐⭐ "NOT YET" — 16 Aug 2026, and it is not a third number: it is a third
	 *     FACT.  `avuta = 0x0` means "I did not make it"; silence meant "I am
	 *     still trying", ⛔ and the parent INFERRED it — that is, it did not
	 *     know it.  `LESSONS.md` §7.5: an inference in place of a message is a
	 *     defect waiting to happen.
	 *
	 * ⇒ With this bit the parent POSTPONES the deadline of §7.1 instead of
	 *   answering `NOT_NOW` to a question that is about to get a real answer. */
	uint32_t should_wait;
};

/* ⛔ What the parent asks of the stage.  ⚠ `codec` at **0** means "stop
 *    capturing": it is not an implicit sentinel, it is the value §4.3/§6.2
 *    reserve for "no codec negotiated", and here it means the same thing —
 *    nobody is watching. */
struct body_video {
	uint8_t codec;  /* 1 = HEVC, 3 = H.264 (2 = AV1 retired), 0 = off */
	uint8_t key; /* ⛔ §5.2: the next one MUST be a keyframe */
	/* ⛔⭐⭐ THE NEGOTIATED DEPTH — 17 Aug 2026, and this field is the cure for
	 *      a measured defect, not a convenience addition.
	 *
	 *      Until tonight the codec crossed this boundary and the depth did
	 *      NOT: the child wrote `r.depth = 10` by hand, for every codec.
	 *      ⇒ The stream came out at **10 bits while `HERE_I_AM` declared 8**
	 *      (§4.3), and no bench could see it — the two numbers live in two
	 *      different PROCESSES.
	 *
	 * ⚠ On Chrome+HEVC it did not show: HEVC carries its parameters in the
	 *   stream (VPS/SPS) and the decoder reconfigures itself.
	 * ⛔ On Firefox+AV1 it did: the page configures the string with the
	 *   NEGOTIATED depth (`av01.0.12M.08`) and dav1d trusts that.  `[M]` first
	 *   artefacts, then the decoder hangs and the desktop stops.
	 *
	 * ⚠ `0` = not negotiated, and it does NOT mean 8: the receiver must NOT
	 *   pick one on its own — that would be redoing by hand the defect just
	 *   removed. */
	uint8_t depth;
	/* ⛔⭐⭐ THE LEVEL REQUESTED BY THE CLIENT — 23 Aug 2026, and this field was
	 *      the `fill` byte, kept free on purpose and named in TWO boxes
	 *      (`rcp.c` §4.3 and "LEVEL PRODUCED" further down) as the place where
	 *      the level would pass the day it was needed.
	 *
	 *      It is needed, and it is MEASURED: `[M]` 23 Aug 2026, canvas
	 *      3840x2160, H.264 — the client declares `video.level=5.1` and the
	 *      server produces a level **5.2** stream.  `RCP.md` §4.3 line 701 is
	 *      a MUST, and the symptom of an exceeded level is NOT an error: it is
	 *      the browser's decoder refusing the configuration — "nothing shows"
	 *      without a line saying why.
	 *
	 * ⚠ In TENTHS, the alphabet of §4.3: `5.1` ⇒ **51**.  Whoever opens the
	 *   encoder converts it back codec by codec (H.264 as is, HEVC times
	 *   three): the translation lives in `encoder.c` and nowhere else.
	 * ⛔ `0` = the client did not declare it — §4.3 does not require it — and it
	 *   means NO CEILING, not "low": the receiver does not invent one, which is
	 *   the same rule written above for `depth`. */
	uint8_t livello_x10;
};

/* ⛔ What the parent asks of the desktop.  The actions are those of `RCP.md`
 *    §7.3 and the fields have its types — ⚠ but here they travel already
 *    VALIDATED: `rcp.c` has done its job, and this boundary does not redo it.
 *
 * ⭐ `id` is there because it is the only thing that makes the `input` field of
 *    frames (§6.2) honest: without it, the child would know it had injected
 *    **something** and not **which**. */
struct body_input {
	uint32_t id;       /* §7.3: grows by at least one over the whole channel */
	uint8_t action;    /* FIGLI_INPUT_* of `child.h` */
	uint8_t pressed;   /* 1 pressed, 0 released */
	uint16_t code;   /* evdev: BTN_LEFT = 0x110, KEY_A = 30 */
	int32_t a, b;      /* pointer x/y · wheel axes · letter in `a` */
};

/* ⭐ §5-bis.7: the name of an XKB layout — `it`, `de(neo)`.  ⚠ 64 bytes
 *    plus the NUL, which is the cap `RCP.md` §4.5 puts on the string: the
 *    envelope is fixed-size so that the child does not have to trust a
 *    length that comes to it from the socket. */
struct body_layout {
	char name[65];
};

/* ⏳ §13: `max_fps` already clamped by `rcp.c`; 0 = no ceiling.  ⚠ The child
 *    clamps AGAIN (`pace_set()`): a number that comes from a socket is not
 *    trusted because a module on the other side promised it. */
struct body_pace {
	uint16_t max_fps;
	uint16_t fill;
};

/* ⛔ The cursor shape that crosses the boundary.  ⚠ The limits of `RCP.md`
 *    §5.5 and §7.2 have already been enforced by `cursor.c`, on the other
 *    side of the pipe: they are not rechecked here — ⛔ except what is needed
 *    not to trust a sender, which in the parent is a different thing from
 *    trusting a module. */
struct body_cursor {
	uint16_t width, height; /* 0x0 = hidden (§5.5) */
	int16_t active_x, active_y;
	uint32_t total;  /* bytes of the whole image: w x h x 4 */
	uint32_t offset;
	uint32_t piece;
};

/* ⛔ What the parent asks of the audio.  `codec` are the numbers of `RCP.md`
 *    §6.3 — 1 = Opus, 2 = PCM — and ⚠ **not** those of §6.2: there 1 is HEVC.
 *    `0` = "off": nobody is listening, and the capture stops while the sink
 *    stays (invariant I4, like the stage). */
struct body_audio {
	uint8_t codec;
	uint8_t fill[3];
};

/* An already encoded block.  `instant_us` is the child's monotonic clock, of
 * the FIRST sample of the block (§6.3) — ⛔ and the child sets it for the same
 * reason it sets `input` in frames: it is the only one that knows when the
 * samples were really taken. */
struct body_block {
	uint8_t codec;
	uint8_t fill[3];
	uint32_t byte;
	uint64_t instant_us;
};

/* ⛔ THE CLIPBOARD TEXT, and it goes in pieces in BOTH directions.
 *
 * ⚠ One structure for both directions, and it is not laziness: the two
 *   messages carry the same object — a text up to 1 000 000 bytes long — and
 *   `serial` is the only difference.  ⛔ In the child → parent direction it is
 *   **0** and means nothing: the session copied, it did not ask.
 *
 * ⛔ And `total` is NOT redundant with respect to `piece`: the receiver
 *    allocates on the first piece and refuses out-of-order pieces, exactly as
 *    for the frame — stitching a hole would mean guessing what was missing,
 *    and a text with a guessed hole pasted into a terminal is worse than a
 *    missing text (§5.4, in its own words). */
struct body_clipboard {
	uint32_t serial; /* parent → child: Mutter's request.  Otherwise 0 */
	uint32_t total; /* bytes of the whole text, final zero EXCLUDED */
	uint32_t offset;
	uint32_t piece;
	/* ⛔ "I don't have it", and it must be said with a field instead of with
	 *    `total = 0`.  An empty text is a LEGITIMATE fact — the clipboard
	 *    emptied — and "I don't have what you asked me" is another fact:
	 *    squashing them onto the same value is the common face of "empty" and
	 *    "forbidden" that `LESSONS.md` §1.9 forbids.  ⚠ And the two lead to two
	 *    different calls towards Mutter. */
	uint8_t nothing;
	uint8_t fill[3];
};

struct body_frame {
	uint8_t codec; /* 1 = HEVC, 2 = AV1 — the same numbers as §4.3/§6.2 */
	uint8_t key;
	uint16_t fill;
	uint32_t width, height;
	uint64_t instant_us;
	uint32_t total; /* bytes of the whole frame */
	uint32_t offset; /* where this piece goes */
	uint32_t piece;  /* how many bytes in this piece */
	/* ⭐⭐ §6.2 — "the identifier of the last input INJECTED before the
	 *     capture, 0 if none".
	 *
	 * ⛔⛔ AND IT TRAVELS FROM HERE, not from the parent, and that is the choice
	 *      that makes the field true instead of plausible.  The parent knows
	 *      what it **sent**; only the child knows what the compositor **took**,
	 *      and knows at what instant it captured.  ⇒ Filling it in the parent
	 *      would say "the last input SENT to the stage before the frame was
	 *      sent": a higher number, and a bigger promise than the frame can
	 *      keep — that is, the latency link would measure a latency shorter
	 *      than the real one, in our favour.
	 * ⚠ `CODER.md` §1-bis: "the boundary moves in the UNCOMFORTABLE direction". */
	uint32_t input;
};

/* The longest message that passes through here. */
#define MAX_ENVELOPE (sizeof(struct head) + sizeof(struct body_frame) + MAX_PIECE)
_Static_assert(sizeof(struct body_cursor) <= sizeof(struct body_frame),
               "the envelope is sized on the frame: the cursor must fit in it");
_Static_assert(sizeof(struct body_clipboard) <= sizeof(struct body_frame),
               "the envelope is sized on the frame: the clipboard must fit in it");

/* ========================================================================== */
/* THE PARENT                                                                  */

struct child {
	bool used;
	char user[64];
	/* ⭐ PHASE 17 T6: the address of the client that caused it to be born, for
	 *    the session's `PAM_RHOST` (like sshd); "" ⇒ "remotix". */
	char rhost[64];
	uid_t uid;
	gid_t gid;
	/* ⭐ 1.5: this child's desktop holds a card grant (`render_grant.h`),
	 *    taken back when the child is reaped. */
	bool render_grant;
	pid_t pid;
	int fd;
	uint64_t serial;
	uint64_t born_ms;
	uint64_t last_recheck_ms;
	/* ⭐ The «who are you» question that is still unanswered since this instant (0 = none), and the last instant ANY accepted message came from the child. */
	uint64_t whoami_asked_ms;
	uint64_t last_heard_ms;
	/* ⭐ The last time the child answered «my name no longer resolves» and a line said so (see `handle()`, MSG_INTRO): a
	 *    line at most every NAME_GONE_LOG_MS per child. */
	uint64_t name_gone_logged_ms;
	/* ⭐ 1.5 (§11.50), network mode only (inert in the single-process server):
	 *    the name as typed at the login when it differs from the canonical one
	 *    the root side resolved; a close-only child (CLOSE_ORPHAN); the root
	 *    side's CHILD_EXITED; the SIGKILLs sent while exiting. */
	char alias[64];
	bool close_only;
	bool reaped;
	int reaped_status;
	int kill_rounds;
	/* ⛔ The refused messages: in a row (`REFUSED_STREAK_MAX`), and the log
	 *    lines of the current window (`REFUSED_LOG_BURST`) with what was only
	 *    counted.  `refused_now`: the message being handled was refused. */
	uint32_t refused_streak;
	uint64_t refused_window_ms;
	uint32_t refused_logged;
	uint64_t refused_hidden;
	bool refused_now;
	bool showed_up;
	/* ⛔⭐ "I told it to leave" and "it has left" are two different facts,
	 *     and keeping only one of them is the defect this bench found on the
	 *     first run (12 Aug 2026, case `dies`).  See the box above
	 *     `child_dismiss()`. */
	bool exiting;
	uint64_t dismissed_ms;
	/* ⛔ The parent asked this child to END its session (`children_terminate_
	 *    session()`, §7.6 or §5.3) and it has not died yet: a login in that
	 *    window must not be attached to a desktop that is closing (review of
	 *    eab9623a).  Holds for `CLOSING_GRACE_MS` at most — a child that does
	 *    not close is not a closing child for ever. */
	uint64_t closing_asked_ms;
	/* The incoming frame, one piece at a time. */
	uint8_t *assembly;
	size_t assembly_total, assembly_got;
	uint8_t assembly_codec, assembly_key;
	uint32_t assembly_w, assembly_h;
	uint64_t assembly_instant;
	uint32_t assembly_input; /* §6.2, and the child STAMPS it: see `body_frame` */
	/* ⭐ The CURSOR assembly is separate from the frame's, and it is not a
	 *    convenience: the two arrive **interleaved** on the same socket, and a
	 *    single assembly would turn every shape change into a dropped frame
	 *    (and vice versa).  ⛔ It is the out-of-order pieces trap seen from
	 *    above: it is not the sender that is wrong, it is the receiver that
	 *    does not have two tables. */
	uint8_t *cur_mount;
	size_t cur_total, cur_got;
	uint16_t cur_l, cur_a;
	int16_t cur_ax, cur_ay;
	/* ⛔ The count of frames arrived from this child.  ⚠ It is here and not in
	 *    a module variable because it is PER CHILD: summed over two users it
	 *    would say the stage works even when only one of them works — two
	 *    measures under the same label. */
	uint64_t frames_received, byte_got, keys_received;
	uint64_t count_logged_ms;
	/* ⛔ What the parent has already asked of this stage: kept so as not to
	 *    repeat the same command on every round of `poll`. */
	uint8_t requested_video_codec;
	/* ⛔ And the depth with it: see `body_video`.  ⚠ `0` = never asked. */
	uint8_t video_profile_requested;
	/* ⛔ And the LEVEL with them (§4.3, 23 Aug 2026), for the same reason:
	 *    it belongs to the SESSION, it changes from client to client, and a
	 *    second client declaring 4.1 where the first had 5.1 is "something new
	 *    to say" even with codec and depth unchanged.  ⚠ `0` = never asked. */
	uint8_t video_level_requested;
	/* ⛔ The last audio codec asked of this child, so as not to repeat the
	 *    same request on every beat — and to write the log line only when the
	 *    fact CHANGES.  ⚠ `0` = off, and it is the initial state of every
	 *    child: nobody listens until someone attaches. */
	uint8_t requested_audio_codec;
	/* ⭐ PHASE 7 — the THIRD assembly table, and the reason is the one written
	 *    above `cur_mount`: frames, cursors and clipboard arrive
	 *    **interleaved** on the same socket, and with only two tables every
	 *    copied text would become a dropped frame.  ⚠ One table per type, and
	 *    the count adds up whatever arrives first. */
	uint8_t *app_mount;
	size_t app_total, app_got;
};

struct children {
	/* ⛔ Allocated in `children_turn_on()` with `f->cap` slots, freed in
	 *    `children_turn_off()`.  ⚠ All the `f->v[i]` stay written as they were:
	 *    only the loop LIMITS change, going from a `#define` to `f->cap`. */
	struct child *v;
	int cap;
	/* ⭐ sigchld.h: true = the loop says nobody died since the last scan, skip `waitpid()` this round (false = always reap) */
	bool reap_hold;
	uint64_t next_serial;
	uint32_t canvas_w, canvas_h;
	char dir_survey[256];
	bool has_survey;
	/* ⭐ PHASE 9 — what every child will have to repeat to itself after the
	 *    `execve`, because the encoder is over there.  ⚠ It is not USED here:
	 *    it is copied into the child's command line (`become_and_exec()`). */
	bool phase9_quality_rises;
	uint32_t phase9_bandwidth_cap_mbit;
	/* ⭐ The THIRD, 24 Aug 2026, and it is born ON: an all-zero audio block
	 *    does not become a datagram.  ⚠ It is passed NEGATED in the child's
	 *    `argv` (`--no-audio-silence`), because what is written at the end
	 *    is the EXCEPTION to the default, not the default. */
	bool phase9_audio_silence;
	char my_path[512]; /* /proc/self/exe resolved, for the `exec` */
	/* ⭐ 1.5 (§11.50): true in the network side, whose children are born, signalled and reaped by the root side. */
	bool remote;
	ChildSessionFinished on_session_finished;
	void *ctx_session_finished;
	ChildCanvasWait on_canvas_wait;
	void *ctx_canvas_wait;
	/* ⭐ PHASE 7 — the audio blocks.  ⚠ It has a context of ITS OWN and does
	 *    not use `ctx` like `deposit`/`dismiss`/`cursor`: those are hooked
	 *    by `main.c` as a block, this one is hooked by whoever owns the audio
	 *    channel, and tying them together would mean forcing audio on wherever
	 *    there is video. */
	ChildBlock on_block;
	void *ctx_block;
	/* ⭐ PHASE 7 — the clipboard.  ⚠ Context of ITS OWN like the blocks', and
	 *    for the same reason: whoever owns the clipboard channel is not the
	 *    one hooking the video, and tying them would mean forcing the
	 *    clipboard on wherever there is video.
	 * ⛔ The two hooks are attached together or not at all (`child.h`): one
	 *    that could receive the session's text and could not needs whoever
	 *    pastes would leave the pasting application hanging. */
	ChildClipboardText on_clipboard_text;
	ChildClipboardRequest on_clipboard_request;
	void *ctx_clipboard;
	ChildRepository deposit;
	ChildFarewell dismiss;
	ChildCursor cursor;
	ChildCanvas canvas;
	void *ctx;
	/* the instant of the current `children_move()` round, for the refusal log */
	uint64_t round_ms;
};

static void magic_write(struct head *t)
{
	t->magic[0] = 'F';
	t->magic[1] = 'I';
	t->magic[2] = 'G';
	t->magic[3] = '1';
}

static bool magic_ok(const struct head *t)
{
	return t->magic[0] == 'F' && t->magic[1] == 'I' && t->magic[2] == 'G'
	       && t->magic[3] == '1' && t->version == CHILD_VERSION;
}

/* ⛔ Reads a message AND the credentials the KERNEL attached to it.
 *
 * ⚠ `credentials` comes out true only if the message really carried some: a
 *   message **without** credentials is not a message with the right
 *   credentials — "empty" and "forbidden" look the same (`LESSONS.md` §1.9),
 *   and here the common face would cost the isolation between users. */
static ssize_t receive_with_credentials(int fd, void *buf, size_t cap,
                                      struct ucred *chi, bool *credentials)
{
	struct msghdr m;
	struct iovec io;
	union {
		struct cmsghdr align;
		char space[CMSG_SPACE(sizeof(struct ucred))];
	} check;
	struct cmsghdr *c;
	ssize_t readings;

	*credentials = false;
	memset(&m, 0, sizeof m);
	memset(&check, 0, sizeof check);
	io.iov_base = buf;
	io.iov_len = cap;
	m.msg_iov = &io;
	m.msg_iovlen = 1;
	m.msg_control = check.space;
	m.msg_controllen = sizeof check.space;

	readings = recvmsg(fd, &m, 0);
	if (readings <= 0)
		return readings;

	for (c = CMSG_FIRSTHDR(&m); c; c = CMSG_NXTHDR(&m, c)) {
		if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_CREDENTIALS
		    && c->cmsg_len == CMSG_LEN(sizeof(struct ucred))) {
			memcpy(chi, CMSG_DATA(c), sizeof *chi);
			*credentials = true;
		}
	}
	/* ⚠ A message truncated by the kernel (`MSG_TRUNC`) is a message that is
	 *   not what it says it is: it is dropped.  With SEQPACKET this happens
	 *   only if the sender wrote more than our buffer, that is if it is not
	 *   our code or if the two sides are not the same version. */
	if (m.msg_flags & MSG_TRUNC)
		return -2;
	return readings;
}

/* ⛔⭐ THE WALL, AND THERE IS ONLY ONE — invariant I3.
 *
 * For a message to count, all these things must be true together:
 *
 *   · the kernel attached the credentials (not "there were none");
 *   · the sender's pid is **that very child**, not another process holding
 *     the same descriptor;
 *   · the uid and gid stamped by the kernel are those the parent resolved
 *     from the NAME of the RCP session's user;
 *   · the serial number is its own — the equivalent of the helper's case
 *     number, and it serves the same purpose: that one's answer does not
 *     admit another.
 *
 * ⚠ The fifth fact — the user's name **still today** resolves to that uid —
 *   is the only one that can change while the child is alive (NSS,
 *   `/etc/passwd` rewritten, a domain answering differently), and it is no
 *   longer asked HERE, on every message: the parent asks at a login
 *   (`name_still_ours()`), and the CHILD answers the periodic one in its reply to
 *   the «who are you» question of `children_recheck()` (`body_whoami.name_check`).
 *
 * ⛔ There is no path that delivers a byte to someone who does not pass here. */
static bool credentials_match(const struct child *g, const struct head *t,
                                   bool c_e, const struct ucred *chi,
                                   char *why_no, size_t cap_why)
{
	if (!c_e) {
		snprintf(why_no, cap_why,
		         "the kernel did not attach the credentials to the message");
		return false;
	}
	if (chi->pid != g->pid) {
		snprintf(why_no, cap_why,
		         "written by pid %ld, and the child of «%s» is pid %ld",
		         (long)chi->pid, g->user, (long)g->pid);
		return false;
	}
	if (chi->uid != g->uid || chi->gid != g->gid) {
		snprintf(why_no, cap_why,
		         "the kernel says uid %ld gid %ld, and «%s» is uid %ld gid %ld",
		         (long)chi->uid, (long)chi->gid, g->user, (long)g->uid,
		         (long)g->gid);
		return false;
	}
	if (t->serial != g->serial) {
		snprintf(why_no, cap_why, "serial %llu instead of %llu",
		         (unsigned long long)t->serial,
		         (unsigned long long)g->serial);
		return false;
	}
	if (t->declared_uid != (uint32_t)g->uid) {
		snprintf(why_no, cap_why,
		         "the message declares uid %lu and the child is uid %ld",
		         (unsigned long)t->declared_uid, (long)g->uid);
		return false;
	}
	return true;
}

/* ⛔⭐ THE NAME STILL RESOLVES TO THE CHILD'S UID — the fifth fact of the wall
 *     above.  WHAT IT PROTECTS: the link between the NAME an RCP session logged in
 *     with and the child (a uid) that serves it.  If the name is later given to
 *     ANOTHER uid (usermod -u, an account deleted and recreated, a domain that
 *     answers differently) or vanishes, the next person to log in under that name
 *     would be attached to the previous owner's desktop (I2: a login finds the
 *     child BY NAME).  The kernel's credentials (pid, uid, gid) and the header
 *     (serial, declared uid) are checked on EVERY message: they cost nothing and
 *     are the isolation between users.
 *
 *     WHO ASKS NSS, AND WHEN:
 *       · the parent, at the spawn and at every LOGIN (`children_ensure_from()`):
 *         once, where it is the security-critical moment;
 *       · the CHILD, once per `RECHECK_MS`, in its answer to the parent's «who are
 *         you» (`body_whoami.name_check`): it was asked by the parent on a timer
 *         until the candidate `nss-fuori`, and with sssd/LDAP every lookup is a
 *         call that can wait on the network — inside the server's single loop, the
 *         one that delivers every user's video.  Now a slow NSS stalls only the
 *         stage of the child that asks.  A child that lied would only keep its own
 *         (stale) session until someone logs in under the name, and the parent's
 *         login check then kills it.
 *       · the child's answer «another uid» costs the child at once; its answer
 *         «gone» does NOT: the child asks NSS as an ordinary user, and a directory
 *         that needs root to bind would make every child say «gone» every minute.
 *         «Gone» is logged (rarely) and left to the login check, made as root. */
/* ⭐ The lookup itself, shared by the two sides: what NSS says about `user` against `uid`.  It BLOCKS on sssd/LDAP, so it
 *    must never run in the parent's loop except at a login (below): the periodic check is made by the CHILD, which asks
 *    NSS for its own name when the parent's question arrives (`name_check` of `body_whoami`), at the cost of its own
 *    stage only. */
static int name_resolution(const char *user, uid_t uid, uid_t *other)
{
	struct passwd pw, *result = NULL;
	char spare[1024];

	if (getpwnam_r(user, &pw, spare, sizeof spare, &result) != 0 || !result)
		return NAME_GONE;
	if (result->pw_uid != uid) {
		if (other)
			*other = result->pw_uid;
		return NAME_OTHER_UID;
	}
	return NAME_HOLDS;
}

static void name_why(const char *user, uid_t uid, int check, uid_t other, char *why_no, size_t cap_why)
{
	if (check == NAME_OTHER_UID)
		snprintf(why_no, cap_why,
		         "«%s» is now uid %ld, and the child is uid %ld: the name and "
		         "the uid have come apart",
		         user, (long)other, (long)uid);
	else
		snprintf(why_no, cap_why,
		         "the name «%s» no longer resolves to any user: the "
		         "link can no longer be proven",
		         user);
}

/* The parent's own check, ONLY at a login (`children_ensure_from()`): the moment a name NSS now gives to another uid would
 * be bound to a stage.  One lookup per login, as the spawn has. */
static bool name_still_ours(const struct child *g, char *why_no, size_t cap_why)
{
	uid_t other = 0;
	int check = name_resolution(g->user, g->uid, &other);

	if (check == NAME_HOLDS)
		return true;
	name_why(g->user, g->uid, check, other, why_no, cap_why);
	return false;
}

/* ⛔⭐ THE FAREWELL IS NOT THE RELEASE, AND KEEPING THEM TOGETHER IS A DEFECT —
 *     found by the bench `02-child-test.py --case dies` on the FIRST run, on
 *     12 Aug 2026, and cured here.
 *
 *     What it did before: the child was killed, its socket gave EOF, and the
 *     parent freed the slot **at once**, zeroing the pid.  ⛔ So the
 *     `waitpid()` further down had no pid left to reap, and the child stayed
 *     a **zombie**.  `[M]` the bench: *"after 15 s the pid is still there,
 *     state Z"*.
 *
 * ⚠ And it is THE SAME LESSON the helper had already paid for today, showing
 *   up one step further on: in `/proc` a zombie and a live process have the
 *   same face, so "the child is dead" and "the child does not die" are
 *   indistinguishable for whoever diagnoses — and they were indistinguishable
 *   for the PARENT too, which had nothing left to look at in the slot.
 *
 * ⇒ From here on there are two steps:
 *     `child_dismiss()`  closes the socket, asks the child to leave, and
 *                         leaves the slot occupied **with the pid inside**;
 *     the reaping         in `children_move()`, `waitpid(WNOHANG)`: when the
 *                         kernel confirms the death, THEN the slot is
 *                         freed — and the log line carries the real CAUSE
 *                         (the signal, or the exit code), not "it closed
 *                         the socket".
 */
/* ⛔⭐ THE CHILD'S EXIT CODES, TRANSLATED INTO WORDS — and it is not cosmetics.
 *
 *     `[M]` 12 Aug 2026, first run of the `uid` fault: the child exited
 *     **35**, and the log said only *"it exited with 35"*.  ⛔ The number is a
 *     fact and not a diagnosis: the reader does not know whether the child did
 *     not drop to the user, did not find the binary or did not manage to
 *     introduce itself — and those are three different faults with three
 *     different cures.
 *
 * ⚠ And between the `fork` and the `exec` nothing is written to the log: we
 *   are in a freshly forked process, and the only honest way to speak is the
 *   exit code.  ⇒ The translation lives HERE, in the parent, which has the log.
 *
 * ⭐ And the table also has the merit of saying how many walls there are: 35
 *    and 42 are the SAME check done twice, before and after the `exec`, and
 *    the third wall — the credentials stamped by the kernel — does not appear
 *    here because it does not make the child exit: the parent kills it. */
static const char *why_exited(int code)
{
	switch (code) {
	case 0:  return "finished its job";
	case 30: return "could not put the socket in the agreed place";
	case 31: return "could not take the user's groups";
	case 32: return "could not drop to the user's gid";
	case 33: return "could not drop to the user's uid";
	case 34: return "could not ASK the kernel who it is (getresuid)";
	case 35: return "⛔ DID NOT DROP to the user: the kernel says a uid different "
	                "from the one requested, and the child stopped BEFORE "
	                "executing anything";
	case 36: return "⛔ did not drop to the user's gid";
	case 37: return "could not execute the server binary";
	case 40: return "was launched with a command line that is not its own";
	case 41: return "could not ask the kernel who it is, after the exec";
	case 42: return "⛔ IS NOT WHO IT SHOULD BE: it noticed by itself, "
	                "after the exec, and touched nothing";
	case 43: return "did not manage to introduce itself to the parent";
	default: return "(a code this parent does not know)";
	}
}

/* ⛔ The summary of what was only counted, once its window has passed (or the
 *    child is leaving): the fact stays in the log, as one line. */
static void refusals_flush(struct child *g, uint64_t now_ms, bool force)
{
	if (!g->refused_hidden)
		return;
	if (!force && now_ms < g->refused_window_ms + REFUSED_LOG_WINDOW_MS)
		return;
	registro_dice(LOG_CHILD,
	              "⛔ «%s»: %llu more refused messages since %llu ms ago, not "
	              "written one by one (the first %d of every %d s are)",
	              g->user, (unsigned long long)g->refused_hidden,
	              (unsigned long long)(now_ms > g->refused_window_ms
	                                       ? now_ms - g->refused_window_ms : 0),
	              REFUSED_LOG_BURST, REFUSED_LOG_WINDOW_MS / 1000);
	g->refused_hidden = 0;
	g->refused_logged = 0;
	g->refused_window_ms = now_ms;
}

/* ⛔ A message of this child is REFUSED: counted (in a row, for
 *    `REFUSED_STREAK_MAX`), and the answer says whether its line may be written
 *    (`REFUSED_LOG_BURST` per `REFUSED_LOG_WINDOW_MS`) or only counted.
 *    ⚠ `f->round_ms` is the instant of the current `children_move()`. */
static bool refused(struct children *f, struct child *g)
{
	uint64_t now_ms = f->round_ms;

	g->refused_now = true;
	if (g->refused_streak < UINT32_MAX)
		g->refused_streak++;
	if (g->refused_logged == 0 && !g->refused_hidden)
		g->refused_window_ms = now_ms;
	refusals_flush(g, now_ms, false);
	if (now_ms >= g->refused_window_ms + REFUSED_LOG_WINDOW_MS) {
		g->refused_window_ms = now_ms;
		g->refused_logged = 0;
	}
	if (g->refused_logged < REFUSED_LOG_BURST) {
		g->refused_logged++;
		return true;
	}
	g->refused_hidden++;
	return false;
}

/* ⛔ The same, for a body too short for what its type says: it was dropped
 *    without a line before, and it still is — but it counts in the streak.
 *    ⚠ Returns `true`: the child is still there (see `handle()`). */
static bool refused_quietly(struct child *g)
{
	g->refused_now = true;
	if (g->refused_streak < UINT32_MAX)
		g->refused_streak++;
	return true;
}

/* The second half: the kernel has confirmed, the slot is freed. */
static void child_signal(struct children *f, struct child *g, int sig);

static void child_free(struct children *f, struct child *g, const char *why)
{
	if (!g->used)
		return;
	refusals_flush(g, log_now_ms(), true);
	registro_dice(LOG_CHILD,
	              "⭐ the child of «%s» (uid %ld) has been REAPED: %s.  From "
	              "now on \"dead\" and \"alive\" no longer have the same face in "
	              "/proc, and the slot is free again",
	              g->user, (long)g->uid, why);
	if (g->fd >= 0)
		close(g->fd);
	if (g->app_mount)
		explicit_bzero(g->app_mount, g->app_total);
	free(g->app_mount);
	free(g->cur_mount);
	free(g->assembly);
	/* ⛔ And the deposit is released from here too, for the paths that do not
	 *    go through the farewell (a child that died without anyone sending it
	 *    away).  ⚠ `dismiss_child()` in `main.c` does nothing if the deposit
	 *    was not its own: calling it twice is not a defect, never calling it is. */
	if (f->dismiss)
		f->dismiss(f->ctx, g->user, g->uid);
	if (g->render_grant)
		render_grant_remove(g->user, g->uid, g->gid);
	memset(g, 0, sizeof *g);
	g->fd = -1;
}

static void child_dismiss(struct children *f, struct child *g, const char *why)
{
	if (!g->used || g->exiting)
		return;
	refusals_flush(g, log_now_ms(), true);
	registro_dice(LOG_CHILD,
	              "the child of «%s» (uid %ld, pid %ld, serial %llu) is "
	              "leaving: %s — waiting for the kernel to confirm it before "
	              "freeing the slot",
	              g->user, (long)g->uid, (long)g->pid,
	              (unsigned long long)g->serial, why);
	g->exiting = true;
	g->dismissed_ms = log_now_ms();
	if (g->fd >= 0) {
		close(g->fd);
		g->fd = -1;
	}
	/* ⛔ The closed socket is already a farewell — the child reads EOF and
	 *    exits — but "it would be enough" is not "I did it": the signal makes
	 *    the shutdown a fact instead of a race. */
	if (g->pid > 0)
		child_signal(f, g, SIGTERM);
	/* ⛔ And the deposit is released AT ONCE, not at reaping: from this instant
	 *    there is no stage behind those pixels any more, and keeping them would
	 *    be showing the image of a user whose process is gone. */
	if (f->dismiss)
		f->dismiss(f->ctx, g->user, g->uid);
}

/* ⛔ The desktop was asked to close (or the child is leaving), within
 *    `CLOSING_GRACE_MS`. */
static bool child_closing(const struct child *g)
{
	return g->exiting || g->close_only
	       || (g->closing_asked_ms
	           && log_now_ms() < g->closing_asked_ms + CLOSING_GRACE_MS);
}

/* ⛔ The slot is found by its canonical name or by the name as typed
 *    (`alias`): exact strings, no NSS — this runs on every message. */
static struct child *search(struct children *f, const char *user)
{
	for (int i = 0; i < f->cap; i++)
		if (f->v[i].used && (strcmp(f->v[i].user, user) == 0
		                     || (f->v[i].alias[0] && strcmp(f->v[i].alias, user) == 0)))
			return &f->v[i];
	return NULL;
}

/* ⛔ Review 4, finding 6: at a LOGIN only.  The slot holds the CANONICAL name
 *    the root side resolved (M3), the login brings the name as TYPED.  With an
 *    NSS that folds case or has aliases, a second login «BRUNO» missed
 *    «bruno»'s child, asked a SPAWN, and the root side's own_by_uid() answered
 *    «closing» for the whole life of that desktop.  ⇒ An exact miss is looked
 *    up again BY UID — the uid NSS gives the typed name, the root side's own
 *    rule — and the typed name is kept as the slot's alias, so the session's
 *    messages find it without NSS.  ⚠ One lookup per login, on a miss only. */
static struct child *search_login(struct children *f, const char *user)
{
	struct child *g = search(f, user);
	struct passwd pw, *r = NULL;
	char buf[4096];

	/* ⚠ network mode only: there the root side resolved the name and the
	 *   slot may hold another spelling; in the single-process server the slot
	 *   holds what was typed, and the spawn's own lookup follows (I3: a full
	 *   table asks NSS nothing) */
	if (g || !f->remote)
		return g;
	if (getpwnam_r(user, &pw, buf, sizeof buf, &r) != 0 || !r || r->pw_uid == 0)
		return NULL;
	for (int i = 0; i < f->cap; i++)
		if (f->v[i].used && f->v[i].uid == r->pw_uid && strlen(user) < sizeof f->v[i].alias) {
			snprintf(f->v[i].alias, sizeof f->v[i].alias, "%s", user);
			return &f->v[i];
		}
	return NULL;
}

/* ⭐ 1.5 (§11.50): the root side's client is referenced WEAKLY, so the seams
 *    and the fuzz harness that `#include` this file without `rootside.c`
 *    still link — and there `f->remote` is never true. */
#pragma weak rootside_attached
#pragma weak rootside_spawn
#pragma weak rootside_close_orphan
#pragma weak rootside_signal
#pragma weak rootside_hook_child_exited
#pragma weak rootside_pump_until

/* ⛔ The one road by which the parent half signals a child.  In network mode
 *    the child is the ROOT SIDE's (another uid, not our child): SIGNAL by
 *    serial, and the root side checks it is one of its own, unreaped. */
static void child_signal(struct children *f, struct child *g, int sig)
{
	if (g->pid <= 0)
		return;
	if (f->remote) {
		if (!rootside_signal || !rootside_signal(g->serial, sig))
			registro_dice(LOG_CHILD,
			              "⛔ the %s for the child of «%s» (serial %llu) did not "
			              "reach the root side",
			              sig == SIGKILL ? "SIGKILL" : "SIGTERM", g->user,
			              (unsigned long long)g->serial);
		return;
	}
	kill(g->pid, sig);
}

/* ⛔ THE CAUSE of a death, not "it ended": whoever reads the log six hours later must be able to tell a child that exited by itself from
 * one that somebody killed, and by which signal.  ⚠ The child's exit codes are in `child_alive()`: 42 = "I am not who I should be". */
static void say_how_it_ended(int state, char *said, size_t cap)
{
	if (WIFEXITED(state))
		snprintf(said, cap, "exited with %d — %s", WEXITSTATUS(state), why_exited(WEXITSTATUS(state)));
	else if (WIFSIGNALED(state))
		snprintf(said, cap, "killed by signal %d", WTERMSIG(state));
	else
		snprintf(said, cap, "ended (status %d)", state);
}

/* ⛔ The reaping, `WNOHANG`: our own `waitpid()`, or in network mode the
 *    CHILD_EXITED the root side sent (it reaped, and removed the render
 *    grant, before telling). */
static pid_t child_reap(struct children *f, struct child *g, int *state)
{
	if (f->remote) {
		if (!g->reaped)
			return 0;
		*state = g->reaped_status;
		return g->pid;
	}
	/* ⭐ sigchld.h: no SIGCHLD since the last scan (and no safety scan due) = nobody to reap this round; the slot is looked at again
	 *    at the next scan (a signal, or one second at most). */
	if (f->reap_hold)
		return 0;
	return waitpid(g->pid, state, WNOHANG);
}

void children_reap_hold(children *f, bool hold)
{
	if (f)
		f->reap_hold = hold;
}

static void child_exited_event(void *ctx, uint64_t serial, int wait_status)
{
	struct children *f = (struct children *)ctx;

	for (int i = 0; i < f->cap; i++)
		if (f->v[i].used && f->v[i].serial == serial) {
			f->v[i].reaped = true;
			f->v[i].reaped_status = wait_status;
			return;
		}
	log_detail(LOG_CHILD,
	           "CHILD_EXITED for serial %llu, which is not in this table (born "
	           "for a previous network side): nothing to free",
	           (unsigned long long)serial);
}


/* ⭐ The trigger reaches the PARENT and must be passed on to the children: see
 *    the box inside `children_move()`.  ⛔ Here it is only noted — the work is
 *    done in the loop, not inside a signal handler. */
static volatile sig_atomic_t shot_to_forward = 0;

static void shot_forward_signal(int which)
{
	shot_to_forward = (which == SIGUSR2) ? 2 : 1;
}

children *children_turn_on(uint32_t canvas_w, uint32_t canvas_h, const char *dir_survey,
                     ChildRepository deposit, ChildFarewell dismiss,
                     ChildCursor cursor, ChildCanvas canvas, void *ctx)
{
	children *f = (children *)calloc(1, sizeof *f);
	ssize_t n;

	if (!f)
		return NULL;
	/* ⛔ The cap is read HERE, only once: `--session-cap` has already moved
	 *    it (it is parsed before the table exists), and from here on the
	 *    number in force for this table is `f->cap` — reading it again later
	 *    would mean two sizes for the same array. */
	f->cap = rcp_cap();
	f->v = (struct child *)calloc((size_t)f->cap, sizeof *f->v);
	if (!f->v) {
		free(f);
		return NULL;
	}
	for (int i = 0; i < f->cap; i++)
		f->v[i].fd = -1;
	f->next_serial = 1;
	/* ⭐ The on-demand trigger: the box is inside `children_move()`. */
	signal(SIGUSR1, shot_forward_signal);
	signal(SIGUSR2, shot_forward_signal);
	f->canvas_w = canvas_w;
	f->canvas_h = canvas_h;
	f->deposit = deposit;
	f->dismiss = dismiss;
	f->cursor = cursor;
	f->canvas = canvas;
	f->ctx = ctx;
	/* ⭐ 1.5 (§11.50): attached to a root side, the children are born, signalled
	 *    and reaped THERE; only their sockets are here.  (Nobody is attached
	 *    in the single-process server: this branch is inert.) */
	if (rootside_attached && rootside_attached()) {
		f->remote = true;
		rootside_hook_child_exited(child_exited_event, f);
		registro_dice(LOG_CHILD,
		              "⭐ children table on: up to %d, one per user (I2), "
		              "canvas %ux%u — born, signalled and reaped by the ROOT "
		              "SIDE (DECISIONS.md §11.50): only their sockets are here",
		              f->cap, canvas_w, canvas_h);
		return f;
	}
	/* ⭐ 1.5: card grants left by a previous run whose desktop is gone
	 *    (`render_grant.h`) — before any child is born. */
	render_grant_sweep();
	if (dir_survey && dir_survey[0]) {
		snprintf(f->dir_survey, sizeof f->dir_survey, "%s", dir_survey);
		f->has_survey = true;
	}

	/* ⛔ The path of the binary is ASKED OF THE KERNEL, not inferred from
	 *    `argv[0]`: `argv[0]` is chosen by whoever launches, and an `exec` on a
	 *    path chosen by whoever launches would be a way to run as the user a
	 *    program that is not this one. */
	n = readlink("/proc/self/exe", f->my_path, sizeof f->my_path - 1);
	if (n <= 0) {
		registro_dice(LOG_CHILD,
		              "⛔ I do not know which binary I am running (/proc/self/exe: "
		              "%s): NO child can be born, and every admitted user "
		              "will stay without a stage (invariant I3: failure is a "
		              "no, not a maybe)",
		              strerror(errno));
		free(f);
		return NULL;
	}
	f->my_path[n] = 0;
	if (strstr(f->my_path, " (deleted)")) {
		registro_dice(LOG_CHILD,
		              "⛔ the running binary has been deleted or "
		              "replaced underfoot («%s»): I am NOT spawning children, "
		              "because I cannot prove which program would run "
		              "as the user",
		              f->my_path);
		free(f->v);
		free(f);
		return NULL;
	}
	registro_dice(LOG_CHILD,
	              "⭐ children table on: up to %d, one per user (I2), "
	              "canvas %ux%u, binary «%s»",
	              f->cap, canvas_w, canvas_h, f->my_path);
	return f;
}

/* ⭐⭐ The box is in `child.h`: here it is only noted, and whoever has no
 *     children table (`children_turn_on()` failed) does not break. */
void children_phase9(children *f, bool quality_recovery, uint32_t bandwidth_cap_mbit,
                 bool audio_silence)
{
	if (!f)
		return;
	f->phase9_quality_rises = quality_recovery;
	f->phase9_bandwidth_cap_mbit = bandwidth_cap_mbit;
	f->phase9_audio_silence = audio_silence;
	/* ⛔ AND THIS LINE IS NOT THE DECLARATION OF THE VALUE IN FORCE — it is the
	 *    opposite: it says what the parent has committed to PASS.  The value
	 *    in force is written by `encoder.c` when each encoder opens,
	 *    inside the child.  ⚠ The two lines are read as a pair: if this one
	 *    says "on" and that one says "off", the option was lost in the
	 *    parent → child hand-over, and it is not the cure that does not work. */
	registro_dice(LOG_CHILD,
	              "⭐ PHASE 9, what the parent WILL PASS to every child on its "
	              "command line: quality climb-back %s · bandwidth ceiling "
	              "%s.  ⚠ The value IN FORCE is written by the child, line "
	              "«encoder OPENED»: if that says something else, the "
	              "hand-over was lost",
	              quality_recovery ? "ON (--quality-recovery)"
	                             : "off (I6, --quality-recovery absent)",
	              bandwidth_cap_mbit ? "ON" : "off (I6, floor 0)");
	/* ⛔⭐⭐ AND THE THIRD HAS A LINE OF ITS OWN, because it is the only one of
	 *      the three born ON — 24 Aug 2026, the user's decision.  ⚠ It must be
	 *      written even when on: it is the line from which a bench reads the
	 *      state of audio silence **without opening a session**, and the other
	 *      two lines of the triple (the child declaring it RECEIVED it, and
	 *      `audio.c` declaring the value IN FORCE) only arrive with the first
	 *      encoder. */
	registro_dice(LOG_CHILD,
	              "⭐ PHASE 9, the audio silence the parent WILL PASS to every "
	              "child: %s.  ⚠ `[M]` 09-b84: 102.1 times less traffic on a "
	              "still screen (557.6 → 5.5 kbit/s), 1 248 blocks silenced out of "
	              "1 248; the price is +2 «missed» out of 5 000 at the client",
	              audio_silence
	                  ? "ON, and it is the DEFAULT since 24 Aug 2026 "
	                    "(the user's decision) — turned off with "
	                    "`--no-audio-silence`"
	                  : "⛔ turned OFF by hand (`--no-audio-silence`): silence "
	                    "is sent too, that is the product until 23 Aug "
	                    "2026.  ⚠ And it is NOT the default");
	if (bandwidth_cap_mbit)
		registro_dice(LOG_CHILD,
		              "⭐ PHASE 9, the bandwidth ceiling: floor %u Mbit/s "
		              "(--bandwidth-cap-mbit) — wire, working point and reservoir "
		              "are derived over there, and encoder.c writes them",
		              bandwidth_cap_mbit);
}

/*
 * ⛔ The PAM conversation for opening the session: it must NOT ask anything.
 *    `pam_open_session` asks no questions — and if it did, answering at
 *    random would be worse than failing (`CODER.md` §3.9: failure is
 *    declared).
 */
static int child_silent_conversation(int n, const struct pam_message **m,
                                     struct pam_response **r, void *data)
{
	(void)n;
	(void)m;
	(void)data;
	*r = NULL;
	return PAM_CONV_ERR;
}

/*
 * ⭐ PHASE 17 T6 — THE SELinux LEVEL OF THE DESKTOP, AS FOR sshd.
 *
 * `[M]` 30 Sep 2026, leap16-kde in enforcing: the child and what it executes
 * directly (startplasma-wayland, labwc) were born
 * `unconfined_u:unconfined_r:unconfined_t:s0`, while whoever logs in with ssh
 * (and everything started by the user manager, kwin included) has
 * `s0-s0:c0.c1023`.  The cause: `pam_selinux open` looks up the domain of its
 * caller — `remotix_t`, ours — in `contexts/users/<user>` and in
 * `contexts/default_contexts`.  Those files are written by the distribution's
 * policy and list `sshd_t`, `cockpit_session_t`, `xdm_t`… but not
 * `remotix_t`, and no module can extend them (`semodule` does not touch them).
 * ⇒ libselinux falls back to `failsafe_context` (`unconfined_r:unconfined_t:s0`),
 *   level written out in full: `s0`.
 *
 * ⇒ The cure here: the role and the type stay those `pam_selinux` chose
 *   (for an `unconfined_u` user they are the same as ssh), the LEVEL is set
 *   back to the one of the login mapping (`getseuserbyname`, `semanage login`)
 *   — the same one sshd gets from its line.  Only if `pam_selinux` set a
 *   context, and only if the new context is valid for the policy; otherwise
 *   it is left as is and that is written down.
 * ⚠ libselinux is opened with `dlopen`: it is there where SELinux is (Fedora,
 *   Alma, openSUSE), and on Debian or Arch this step stays silent.  No new
 *   dependency.
 */
static void selinux_level_like_sshd(const char *user)
{
	void *l = dlopen("libselinux.so.1", RTLD_NOW | RTLD_LOCAL);
	if (!l)
		return;
	int (*enabled)(void) = (int (*)(void))dlsym(l, "is_selinux_enabled");
	int (*load)(char **) = (int (*)(char **))dlsym(l, "getexeccon");
	int (*write)(const char *) = (int (*)(const char *))dlsym(l, "setexeccon");
	int (*map)(const char *, char **, char **) =
		(int (*)(const char *, char **, char **))dlsym(l, "getseuserbyname");
	int (*valid)(const char *) =
		(int (*)(const char *))dlsym(l, "security_check_context");
	void (*free_fn)(char *) = (void (*)(char *))dlsym(l, "freecon");
	char *exec_ctx = NULL, *seuser = NULL, *level = NULL;

	if (!enabled || !load || !write || !map || !valid || !free_fn ||
	    enabled() != 1)
		goto fine;
	if (load(&exec_ctx) != 0 || !exec_ctx)
		goto fine; /* pam_selinux chose nothing: nothing is invented */
	if (map(user, &seuser, &level) != 0 || !level || !level[0])
		goto fine;
	{
		/* user:role:type:level — the level may contain ":" */
		const char *p = exec_ctx;
		for (int i = 0; i < 3 && p; i++) {
			p = strchr(p, ':');
			if (p)
				p++;
		}
		if (!p || strcmp(p, level) == 0)
			goto fine; /* no level, or already the right one */
		char fresh[512];
		int n = snprintf(fresh, sizeof fresh, "%.*s%s",
		                 (int)(p - exec_ctx), exec_ctx, level);
		if (n <= 0 || (size_t)n >= sizeof fresh || valid(fresh) != 0) {
			fprintf(stderr,
			        "child: ⚠ SELinux: the desktop of «%s» is born «%s»; "
			        "the level of the login mapping («%s») does not make a "
			        "valid context — left as is\n",
			        user, exec_ctx, level);
			goto fine;
		}
		if (write(fresh) == 0)
			fprintf(stderr,
			        "child: ⭐ SELinux: the desktop of «%s» is born «%s» "
			        "as with ssh (pam_selinux had given «%s»: remotix_t "
			        "is not in the policy's stock contexts)\n",
			        user, fresh, exec_ctx);
		else
			fprintf(stderr,
			        "child: ⚠ SELinux: setexeccon(«%s») refused (%s): "
			        "the desktop is born «%s»\n",
			        fresh, strerror(errno), exec_ctx);
	}
fine:
	if (exec_ctx && free_fn)
		free_fn(exec_ctx);
	free(seuser);
	free(level);
	dlclose(l);
}

/* ⛔ What is done AFTER the `fork` and BEFORE the `exec`, and in this order.
 *    Every permutation is punished with a different defect, and none of the
 *    three says "you got the order wrong" (error form E4):
 *
 *      · the groups BEFORE the uid, or there is no longer the right to change
 *        them;
 *      · `setgid` before `setuid`, or the privilege to do it is lost;
 *      · the descriptors are closed BEFORE dropping, but AFTER putting the
 *        socket in its place.
 *
 * ⚠ This function never returns: either it does `exec`, or it exits with a
 *   code. */
static void become_and_exec(const struct birth_opts *b, uint64_t serial,
                              const char *rhost, int socket_child,
                              const struct passwd *pw,
                              const gid_t *groups, int ngroups)
{
	char a_user[80], a_uid[32], a_gid[32], a_l[32], a_a[32], a_serial[40];
	char a_cap[32], a_parent[32];
	char e_home[512], e_user[96], e_log[96], e_path[128], e_runtime[160],
		e_bus[224], e_shell[16];
	/* ⚠ Twenty: the nine fixed ones, the NULL, and the TEN optional words
	 *   at the end — `--verbose`, `--journal`, `--quality-recovery`,
	 *   `--bandwidth-cap-mbit` and its number, `--no-audio-silence`,
	 *   ⭐ phase 19 `--encoding-route` with its value, and ⭐ 1.5 `--render-node`
	 *   with its value.  They are added only if the
	 *   parent has them (see below).  ⛔ The count is redone for every new
	 *   word: an `argv[]` that is too short does not give an error, it writes
	 *   past the end of the stack. */
	char *argv[23];
	/* ⚠ 16 and not 9: to the seven we compose ourselves are added those that
	 *   `pam_systemd` puts in the session's environment — `XDG_SESSION_ID`
	 *   first, which is what Mutter was missing. */
	char *envp[16];
	char **pam_environment = NULL;
	int na = 0, ne = 0;
	uid_t r, e, s;
	gid_t rg, eg, sg;

	/* ⭐ sigchld.h: the parent's SIGCHLD handler is still ours between the fork and the execve (only a flag is set, harmless); the default
	 *    from the first line, so that nothing of the parent's loop is left in a process that is about to become something else. */
	signal(SIGCHLD, SIG_DFL);

	/* 1. the socket in the agreed place (fd 3), and without CLOEXEC: it is the
	 *    only thing that must cross the `exec`. */
	if (socket_child != 3) {
		if (dup2(socket_child, 3) < 0)
			_exit(30);
		close(socket_child);
	}
	fcntl(3, F_SETFD, 0);

	/* 2. ⛔ EVERYTHING ELSE IS CLOSED, and this line is half of the cure that
	 *    the helper buys by being born early.  A child that carried along the
	 *    UDP socket and the TCP listener would keep the port busy even after
	 *    the server died, and the symptom would be "address already in use"
	 *    with no server in sight.
	 * ⚠ 0,1,2 stay: the child's log goes out through the same stderr as the
	 *   parent, and that is what makes "who said what" readable.
	 * ⚠ And the `exec` would close the CLOEXEC ones anyway — but "someone else
	 *   would have closed them" is not "I closed them", and not all of them
	 *   are. */
	if (close_range(4, ~0U, 0) != 0) {
		/* Declared fallback: the slow road, one descriptor at a time. */
		for (int i = 4; i < 4096; i++)
			close(i);
	}

	/*
	 * 2-bis. ⛔⭐⭐ THE PAM SESSION — and on 15 Aug 2026 this line was not there.
	 *
	 * ⛔ THE DEFECT IT CURES, measured on the evening of 15 Aug: without a logind
	 *    session the compositor **does not start at all**.  Mutter asks
	 *    `sd_pid_get_session()`, gets the answer **ENXIO** — "this process is
	 *    not in any session" — and dies with *"Failed to find any matching
	 *    session"*.  ⚠ And `linger` is NOT enough: it gives `/run/user/<uid>`
	 *    and the bus, but it puts the processes in `user@<uid>.service`, which
	 *    is a scope of class `manager` — not a session.
	 *
	 * ⛔ HERE IT USED TO SAY THE OPPOSITE, and it was right for another phase:
	 *    "making a session BE BORN belongs to the real login, not to this
	 *    mandate".  ⭐ At phase 5 that mandate **is this one**: `PLAN.md`
	 *    says "Produces: **PAM in full**".
	 *
	 * ⭐ AND THE THREE THINGS TOLD TO `pam_systemd` each have a reason:
	 *
	 *   · `XDG_SESSION_TYPE=wayland` — the Shell's unit carries
	 *     `ConditionEnvironment=XDG_SESSION_TYPE=wayland`: without it, the
	 *     compositor is not started AT ALL, and there is no line saying why;
	 *   · `XDG_SESSION_CLASS=user` — `manager` is what linger gives, and it is
	 *     precisely the class that is not enough for Mutter;
	 *   · ⛔ **no `XDG_SEAT`, and it is not an oversight**: a session without a
	 *     seat is headless **by construction**, which is what `DECISIONS.md`
	 *     §4.3-bis has asked for since August and what until today we had by
	 *     accident.
	 *
	 * ⚠ And `PAM_RHOST`: logind marks the session `Remote=yes`.  ⭐ It pays back
	 *   twice — it is the second belt of the guardian of §5.1 (`sentinel.c`
	 *   discriminates on the seat, and this is the independent confirmation)
	 *   and it makes the origin appear in the system logs.
	 *
	 * ⛔ `pam_end()` WITHOUT `pam_close_session()`, and it is on purpose: closing
	 *    the session would take it away at once.  The logind session belongs
	 *    to the LEADER process — which is this one, after the `exec` — and
	 *    logind takes it back when it dies.  ⚠ Which makes invariant I4 true on
	 *    the system side: the stage outlives the client because the child
	 *    outlives it.
	 *
	 * ⚠ And if PAM does not make it we do NOT exit: we go on and write it down.
	 *   A session without logind is broken, ⛔ but a child that dies here does
	 *   not even leave a line for whoever reads the log (invariant I1).
	 */
	{
		struct pam_conv silent_conv = { child_silent_conversation, NULL };
		pam_handle_t *pam = NULL;
		int rv;

		rv = pam_start("remotix", pw->pw_name, &silent_conv, &pam);
		if (rv != PAM_SUCCESS) {
			fprintf(stderr, "child: ⛔ pam_start: %s\n",
			        pam_strerror(NULL, rv));
		} else {
			pam_putenv(pam, "XDG_SESSION_TYPE=wayland");
			pam_putenv(pam, "XDG_SESSION_CLASS=user");
			/* ⭐ PHASE 17 T6: the client's real address, like sshd
			 *    (logind `RemoteHost`, `pam_lastlog` and the logs
			 *    write it); "remotix" only if unknown.  ⚠ From 127.0.0.1
			 *    logind marks `Remote=no`, as for ssh from 127.0.0.1: the
			 *    guardian of §5.1 discriminates on the seat, not on Remote. */
			pam_set_item(pam, PAM_RHOST,
			             rhost && rhost[0] ? rhost : "remotix");
			pam_set_item(pam, PAM_TTY, "remotix");

			rv = pam_open_session(pam, PAM_SILENT);
			if (rv != PAM_SUCCESS) {
				fprintf(stderr,
				        "child: ⛔ pam_open_session: %s — the "
				        "compositor will not start\n",
				        pam_strerror(pam, rv));
			} else {
				pam_environment = pam_getenvlist(pam);
				/* ⭐ PHASE 17 T6: the SELinux level as for ssh. */
				selinux_level_like_sshd(pw->pw_name);
			}
			/* ⛔ `pam_end` and not `pam_close_session`: see above. */
			pam_end(pam, PAM_SUCCESS);
		}
	}

	/* 3. the groups, then the gid, then the uid — and never the other way round. */
	if (setgroups((size_t)ngroups, groups) != 0)
		_exit(31);
	if (setgid(pw->pw_gid) != 0)
		_exit(32);
	if (setuid(pw->pw_uid) != 0)
		_exit(33);

	/* 4. ⛔⭐ AND IT IS VERIFIED THAT THE DROP REALLY HAPPENED, BY ASKING THE KERNEL.
	 *
	 *    `setuid()` returning 0 says the call succeeded, not that **all three**
	 *    uids changed: if a saved-set-uid remained at zero, this process could
	 *    become root again with one line.  ⇒ All six are read with
	 *    `getresuid`/`getresgid`, and if a single one is not the expected one
	 *    the child does NOT start.  ⚠ It is invariant I7 read from the inside:
	 *    the protection lives in the program. */
	if (getresuid(&r, &e, &s) != 0 || getresgid(&rg, &eg, &sg) != 0)
		_exit(34);
	if (r != pw->pw_uid || e != pw->pw_uid || s != pw->pw_uid)
		_exit(35);
	if (rg != pw->pw_gid || eg != pw->pw_gid || sg != pw->pw_gid)
		_exit(36);

	/* 5. ⛔ The environment is composed from scratch, one variable at a time
	 *    (`CODER.md` §4.5).  ⚠ And with `execve` there is no way to get it
	 *    wrong by distraction: what is not in this list does not exist on the
	 *    other side.
	 *
	 * ⚠ `SHELL` EMPTY by hand, as `session.c` does: an inherited `SHELL`
	 *   makes the sessions restart inside a login shell, and that is state 7
	 *   of the session bench.
	 * ⚠ And NO language variable: no application is started here, so there
	 *   is nothing a wrong local could prevent.  The day this child made a
	 *   session BE BORN, the rule of `session.c` applies — and it must be
	 *   written there, not guessed here. */
	snprintf(e_home, sizeof e_home, "HOME=%s", pw->pw_dir);
	snprintf(e_user, sizeof e_user, "USER=%s", pw->pw_name);
	snprintf(e_log, sizeof e_log, "LOGNAME=%s", pw->pw_name);
	snprintf(e_path, sizeof e_path, "PATH=/usr/local/bin:/usr/bin:/bin");
	snprintf(e_shell, sizeof e_shell, "SHELL=");
	snprintf(e_runtime, sizeof e_runtime, "XDG_RUNTIME_DIR=/run/user/%ld",
	         (long)pw->pw_uid);
	snprintf(e_bus, sizeof e_bus,
	         "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%ld/bus",
	         (long)pw->pw_uid);
	envp[ne++] = e_home;
	envp[ne++] = e_user;
	envp[ne++] = e_log;
	envp[ne++] = e_path;
	envp[ne++] = e_shell;
	envp[ne++] = e_runtime;
	envp[ne++] = e_bus;
	/* ⭐⭐ AND HERE WE STOP INVENTING THEM — the user's remark of 15 Aug
	 *     2026: *"the XDG variables should be set by the session manager, and
	 *     in REMOTIX it seems they are not set"*.  Right: nobody set them
	 *     because nobody opened the session.  Now we open it, and what
	 *     `pam_systemd` puts in it is **read** instead of inferred.
	 * ⛔ `XDG_SESSION_ID` is the one that counts: it is the thread that ties
	 *    this process to the logind session, and it is what Mutter was
	 *    looking for. */
	for (int i = 0; pam_environment && pam_environment[i] && ne < 14; i++)
		if (strncmp(pam_environment[i], "XDG_SESSION_ID=", 15) == 0)
			envp[ne++] = pam_environment[i];
	envp[ne] = NULL;

	/* 6. the child's command line, which is what the bench will read in
	 *    `/proc/<pid>/cmdline`.  ⛔ No secrets in here: the password already
	 *    died with the helper, and it does not pass through here. */
	snprintf(a_user, sizeof a_user, "%s", pw->pw_name);
	snprintf(a_uid, sizeof a_uid, "%ld", (long)pw->pw_uid);
	snprintf(a_gid, sizeof a_gid, "%ld", (long)pw->pw_gid);
	snprintf(a_l, sizeof a_l, "%u", b->canvas_w);
	snprintf(a_a, sizeof a_a, "%u", b->canvas_h);
	snprintf(a_serial, sizeof a_serial, "%llu", (unsigned long long)serial);
	argv[na++] = (char *)"remotix-child";
	argv[na++] = (char *)"--internal-child";
	argv[na++] = a_user;
	argv[na++] = a_uid;
	argv[na++] = a_gid;
	argv[na++] = a_l;
	argv[na++] = a_a;
	argv[na++] = a_serial;
	argv[na++] = b->dir_survey && b->dir_survey[0] ? (char *)b->dir_survey : (char *)"-";
	/*
	 * ⛔⭐⭐⭐ AND THE CHATTER IS PASSED TO THE CHILD — 16 Aug 2026, and it is
	 *        the defect that cost me a whole day.
	 *
	 * ⛔ The child is NOT a fork: it is an `execve` of `remotix-child`.  ⇒ It
	 *    does not inherit the parent's variables, and `log_chatter()`
	 *    in the child stayed **off** — even when the server had started with
	 *    `--verbose`.
	 *
	 * ⚠ So **every `log_detail()` of `child.c` went into the void**,
	 *   silently, without an error.  `[M]` And it cost dearly: hunting the
	 *   tail of login times I concluded for hours that certain branches "never
	 *   fired", because their line did not appear — while they fired all
	 *   right.  ⭐ Diagnostics that stay silent are not neutral: **they lie**,
	 *   and they lie in the worst direction, that is "that code does not run".
	 *
	 * ⇒ It is form E8 (`LESSONS.md` §1.9) inside the very tool meant to unmask
	 *   it: "it did not do it" and "it did not tell me" with the same face.
	 *
	 * ⚠ At the end and optional: the child reads `argc >= 9` and this is the
	 *   tenth, so a command line without it does not break.
	 */
	if (log_verbose())
		argv[na++] = (char *)"--verbose";
	/* ⭐ And the journal (phase 16 §12), for exactly the same reason: the
	 *    parent's socket is CLOEXEC, and the child opens one of its own. */
	if (log_to_journal())
		argv[na++] = (char *)"--journal";
	/*
	 * ⛔⭐⭐ AND THE **THREE** CURES OF PHASE 9 PASS THROUGH HERE, for exactly the
	 *      same reason as the chatter above — and it is not an analogy, it is
	 *      the same defect.  ⚠ The third (audio silence) arrived on 24 Aug
	 *      2026, and travels NEGATED: see the box further down.
	 *
	 * ⛔ `encoder_quality_rises()` and `codificatore_tetto_banda()` are
	 *    statics of the PROCESS: calling them in the parent turns nothing on,
	 *    because the parent never opens an encoder.  ⚠ And the environment
	 *    above is composed from scratch (point 5): a `REMOTIX_...` does not
	 *    reach the other side, and would not even leave a line saying it did
	 *    not arrive.
	 *
	 * ⇒ The only channel that crosses the `exec` together with the socket is
	 *   this one, and the child reads them back in `child_alive()`.
	 *
	 * ⚠ At the end and optional: the child reads the first nine by position
	 *   and scans the rest by name, so a command line without them does not
	 *   break.  ⭐ And they appear in `/proc/<pid>/cmdline`: whoever watches a
	 *   bench sees what that child was born with, without trusting a log.
	 */
	if (b->quality_rises)
		argv[na++] = (char *)"--quality-recovery";
	if (b->bandwidth_cap_mbit) {
		snprintf(a_cap, sizeof a_cap, "%u", b->bandwidth_cap_mbit);
		argv[na++] = (char *)"--bandwidth-cap-mbit";
		argv[na++] = a_cap;
	}
	/* ⛔⭐⭐ AND THE THIRD TRAVELS NEGATED, which is the only form that does not lie.
	 *
	 *      The two above are born off: what is written at the end is "turn it
	 *      on".  This one is born ON (24 Aug 2026), so what is written is
	 *      "turn it off" — ⛔ and the word in `argv` is the SAME one the server
	 *      received (`--no-audio-silence`), because whoever looks at a
	 *      child's `/proc/<pid>/cmdline` must be able to compare it by eye
	 *      with the parent's command line.  ⚠ If a positive `--audio-silenzio`
	 *      appeared here there would be TWO names for the same cure, and that
	 *      is exactly what this phase removed. */
	if (!b->audio_silence)
		argv[na++] = (char *)"--no-audio-silence";
	/* ⭐ PHASE 19: the card's route, if forced (`--encoding-route vaapi|vulkan`):
	 *    the default "card" is not passed, and the child is born with the same. */
	if (strcmp(child_encoding_route_requested(), "card") != 0) {
		argv[na++] = (char *)"--encoding-route";
		argv[na++] = (char *)child_encoding_route_requested();
	}
	/* ⭐ 1.5: `--render-node`, if given (`choose_render_node()`). */
	if (child_render_node_requested()[0]) {
		argv[na++] = (char *)"--render-node";
		argv[na++] = (char *)child_render_node_requested();
	}
	/* ⭐ 1.5 (§11.50): the uid whose stamp the child accepts on the parent's
	 *    messages — `remotix`, the network side, which holds the other end.
	 *    ⛔ Written by the ROOT SIDE from its own knowledge, never from a
	 *    request; absent = 0, the single-process server's root. */
	if (b->parent_uid >= 0) {
		snprintf(a_parent, sizeof a_parent, "%ld", b->parent_uid);
		argv[na++] = (char *)"--parent-uid";
		argv[na++] = a_parent;
	}
	/* ⛔ 1.5 (§11.50): a birth WITHOUT a password (CLOSE_ORPHAN) is a child
	 *    that can only close the desktop — the root side's choice, never the
	 *    request's (`child_alive()`, the box at `close_only`). */
	if (b->close_only)
		argv[na++] = (char *)"--close-only";
	argv[na] = NULL;

	execve(b->my_path, argv, envp);
	_exit(37);
}

/*
 * ---------------------------------------------------------------------------
 * ⛔⭐⭐⭐ THE CHECK THAT MAKES THE OLDEST DEFECT OF THE PROJECT **NOISY** —
 *        27 Aug 2026, phase 11.
 *
 * ⛔ THE DEFECT, `[M]` measured on the real machine on 27 Aug 2026: a tenant
 *    who is NOT in the group of the card's node (`video` and `render` on this
 *    machine) gives birth to a session that **looks alive and sees nothing**.
 *    Zero `negotiated format`, zero frames, and the loop going round and round
 *    between "BLACK: ZERO MONITORS" and "virtual monitor mounted" for eighty-two
 *    seconds.  ⭐ The measure: **0 out of 4** without the groups, **17 out of
 *    17** with the groups, and the **counter-proof** on the same user (given
 *    the two groups and the user manager restarted ⇒ it sees in 2.04 s).
 *
 * ⛔⛔ And `phases/10-multi-tenant-and-the-budget.md` §7.4 — "the session born
 *      blind", `provanic4/5/6` never succeeding in **98 · 55 · 50** attempts —
 *      is exactly this: those three users did not have the two groups, and
 *      `prova` and `provanic1`, which always saw, did.  ⇒ The defect blocked
 *      five tests and postponed a phase **without giving a single error**.
 *
 * ⭐⭐ SO THE CURE THAT COUNTS MOST IS NOT IN THE PROVISIONING: it is HERE.  A
 *     provisioning script can be forgotten, and indeed it was forgotten —
 *     `benches/tools-users.sh` and the terrains of phases 4/6/7/9 create
 *     tenants **without** the two groups.  ⛔ A defect that shows up as "it
 *     does not work and nobody knows why" is the one that costs months: the
 *     product must **notice it and say so**, at birth, with words that also
 *     say the cure.
 *
 * ⭐ AND THE GROUP IS READ FROM THE NODE, neither the name nor the number is
 *    hard-wired: `/dev/dri` is opened, the `st_gid` of every `renderDN` is
 *    taken (which is the provisioning's `stat -c %g`, done in C) and we look
 *    whether the tenant is in those groups.  ⚠ A hard-wired gid would be false
 *    on the next machine, and a hard-wired name (`render`) is false on a
 *    distribution that calls it otherwise.
 * ⭐ 1.5 (DECISIONS.md §10.36, §11.38): ONLY the render nodes, no more `cardN`
 *    (`video`).  `[M]` 13 Oct 2026 (§11.4), the four desktops on the boxes and
 *    GNOME on the tablet: every compositor opened `renderD128` and never
 *    `card0`; and `video` also gives `/dev/fb*` and the webcams.
 *
 * ⚠ WHY MEMBERSHIP AND NOT AN `access()`: the parent is root, and to root the
 *   kernel always says "yes".  The only question that can be asked from here,
 *   and that has the same answer the child will have, is "is this user in
 *   that group?".  ⛔ And on a normal desktop the access to the card would be
 *   given by logind's ACL (udev tag `uaccess`) to the user of the active
 *   session **on a seat** — ⇒ our session has no seat on purpose
 *   (`DECISIONS.md` §4.3-bis), so that ACL never arrives and the group is the
 *   only road.
 *
 * ⛔ AND THE SESSION IS NOT REFUSED, it is declared: on different hardware the
 *    software fallback might be slow instead of infinite (`[?]`, not
 *    measured), and a refusal would turn a declared degradation into a
 *    "cannot get in" — that is, it would put the user back to guessing, which
 *    is the defect this line cures.
 * ---------------------------------------------------------------------------
 */
#define CARD_NODES_DIR "/dev/dri"
#define MAX_CARD_GROUPS 8

static const char *group_name(gid_t g, char *dove, size_t cap)
{
	struct group gr, *result = NULL;
	char spare[1024];

	if (getgrgid_r(g, &gr, spare, sizeof spare, &result) == 0 && result)
		snprintf(dove, cap, "%s", gr.gr_name);
	else
		snprintf(dove, cap, "gid %ld without a name", (long)g);
	return dove;
}

static bool is_in_group(gid_t primary, const gid_t *groups, int ngroups,
                           gid_t searched)
{
	if (primary == searched)
		return true;
	for (int i = 0; i < ngroups; i++)
		if (groups[i] == searched)
			return true;
	return false;
}

/*
 * ⭐ THE GROUPS OF THE CARD'S NODES, READ FROM THE MACHINE — in one place only.
 *
 * Returns how many it found (0 = no node, or the folder does not open: the
 * caller DECLARES it, each in its own words).  ⚠ Two functions use it — the
 * one that only says it and the one that enrols the tenant — and a second
 * copied scan would be a second place to diverge from (`LESSONS.md` §1.47).
 */
static int collect_card_groups(gid_t seen_items[MAX_CARD_GROUPS],
                                  char names[MAX_CARD_GROUPS][64],
                                  char nodes[MAX_CARD_GROUPS][96],
                                  const char *user)
{
	DIR *d;
	struct dirent *e;
	int nseen = 0;

	d = opendir(CARD_NODES_DIR);
	if (!d) {
		log_says_of(LOG_CHILD, user,
		                 "⚠ %s does not open (%s): I CANNOT say whether this "
		                 "tenant will see.  ⛔ On a machine without DRM nodes "
		                 "the compositor draws in software, and the session "
		                 "can be born blind without giving an error",
		                 CARD_NODES_DIR, strerror(errno));
		return 0;
	}
	while ((e = readdir(d)) != NULL) {
		char fpath[96];
		struct stat st;
		bool already = false;

		/* ⭐ 1.5: only `renderDN` (usually the `render` group, but its
		 *   real group is read below with `stat`).  ⛔ `cardN` (`video`) is no
		 *   longer asked: `[M]` 13 Oct 2026 no compositor of the four desktops
		 *   opened it (DECISIONS.md §11.4, §11.38), and `video` also opens
		 *   `/dev/fb*` and the webcams.  ⛔ And the numbers are scanned
		 *   instead of hard-wired: `renderD128` and `renderD129` swap between
		 *   two boots (`provision.sh` §5). */
		if (strncmp(e->d_name, "renderD", 7) != 0)
			continue;
		/* ⚠ `%.32s` and not `%s`: `d_name` is 256 long and the compiler is
		 *   right to say so (`-Wformat-truncation`).  ⛔ A node name longer
		 *   than 32 does not exist (`renderD128` is ten letters), and if it
		 *   existed the truncated path would not open: the `stat` below
		 *   fails and that node is skipped — ⇒ never a WRONG group declared
		 *   for a half path. */
		snprintf(fpath, sizeof fpath, "%s/%.32s", CARD_NODES_DIR,
		         e->d_name);
		if (stat(fpath, &st) != 0)
			continue;
		for (int i = 0; i < nseen; i++)
			if (seen_items[i] == st.st_gid) {
				already = true;
				break;
			}
		if (already || nseen >= MAX_CARD_GROUPS)
			continue;
		seen_items[nseen] = st.st_gid;
		group_name(st.st_gid, names[nseen], 64);
		snprintf(nodes[nseen], 96, "%s", fpath);
		nseen++;
	}
	closedir(d);
	return nseen;
}

/* ⭐ Writes in the log whether this tenant will see or not.  It decides
 *    nothing: it declares.  Returns `true` if it is in ALL the groups of the
 *    card's nodes. */
static bool card_groups(const char *user, gid_t primary,
                                const gid_t *groups, int ngroups)
{
	gid_t seen_items[MAX_CARD_GROUPS];
	char names[MAX_CARD_GROUPS][64];
	char nodes[MAX_CARD_GROUPS][96];
	int nseen = collect_card_groups(seen_items, names, nodes, user);
	int missing_list = 0;
	char listing[256];
	size_t used_len = 0;

	if (nseen == 0) {
		log_says_of(LOG_CHILD, user,
		                 "⚠ no `renderDN` node in %s: this "
		                 "machine has no card to show, and the "
		                 "compositor will draw in SOFTWARE",
		                 CARD_NODES_DIR);
		return false;
	}

	for (int i = 0; i < nseen; i++) {
		if (is_in_group(primary, groups, ngroups, seen_items[i])) {
			int n = snprintf(listing + used_len, sizeof listing - used_len, "%s%s",
			                 used_len ? ", " : "", names[i]);
			if (n > 0 && (size_t)n < sizeof listing - used_len)
				used_len += (size_t)n;
			continue;
		}
		missing_list++;
		/* ⛔⛔ THE LINE THAT IS WORTH THE WHOLE CHECK.  It says the defect, the
		 *     VISIBLE consequence ("it will see nothing"), and the cure in
		 *     full.  ⭐ 1.5: no `terminate-user` in the cure any more — it
		 *     closed the user's other sessions; a user manager left with the
		 *     old groups is bridged at the next login (`render_grant.h`). */
		log_says_of(LOG_CHILD, user,
		                 "⛔⛔ «%s» IS NOT IN THE CARD'S GROUP «%s» (gid "
		                 "%ld, the group of %s): ⛔ THIS SESSION WILL BE BORN AND "
		                 "WILL SEE NOTHING — zero frames, no window will "
		                 "open, and the loop will go round and round between «BLACK: "
		                 "ZERO MONITORS» and «virtual monitor mounted».  ⭐ THE CURE, "
		                 "as root: `usermod -aG %s %s`, then sign in again — "
		                 "REMOTIX bridges a user manager still alive with the old "
		                 "groups, and closes nothing.  (phase 10 §7.4, "
		                 "measured 27 Aug 2026: 0 sessions out of 4 without the "
		                 "group, 17 out of 17 with it)",
		                 user, names[i], (long)seen_items[i], nodes[i], names[i],
		                 user);
	}

	if (missing_list == 0)
		log_says_of(LOG_CHILD, user,
		                 "⭐ is in the card's groups (%s): the session can "
		                 "see in hardware",
		                 listing);
	return missing_list == 0;
}

/*
 * ⭐⭐ ENROLMENT IN THE CARD'S GROUPS, AT THE FIRST CONNECTION.
 *     *[Decided by the user on 20 Sep 2026: "the installation procedure adds
 *       the users present in the system; once in service, every new user is
 *       added to the groups at the first connection".]*
 *
 * ⛔ THE FACT THAT MAKES IT NECESSARY: on a normal desktop the permission on
 *    the card is given by logind with an ACL to whoever sits in front; our
 *    session has no physical seat, so the groups remain — and without them,
 *    `[M]` 27 Aug 2026, the session is born BLIND (0 out of 4) and **no error
 *    says so**.
 *    ⇒ `provision.sh` enrols whoever exists at installation time; ⛔ but
 *    whoever is created later would stay out, and the administrator would see
 *    a blank page without knowing why.
 *
 * ⛔⭐ AND IT IS DONE HERE, not earlier: we are in the parent, running as root,
 *     **after** PAM said yes — that is, nothing is granted to someone who
 *     merely knocks — and **before** the `fork`, so the child is born with
 *     the new groups.
 * ⚠ And it changes a declared division (I7: "the product touches the
 *   session, the machine is touched by `provision.sh`"): the product now
 *   touches the groups.  It is the user's decision, and it is written in the
 *   log every time.
 * ⚠ The user manager already alive does NOT take the new groups, and it is
 *   NOT made to be born again (1.5, DECISIONS.md §11.4: `loginctl
 *   terminate-user` closed the user's other sessions).  The card is bridged by
 *   `render_grant.h` instead.
 *
 * Returns `true` if it changed something (and then the groups must be read
 * again).
 */
static bool run_as_root(const char *which, char *const argv[], const char *user)
{
	pid_t p = fork();
	int state = 0;

	if (p < 0)
		return false;
	if (p == 0) {
		execv(which, argv);
		_exit(127);
	}
	if (waitpid(p, &state, 0) != p)
		return false;
	if (!WIFEXITED(state) || WEXITSTATUS(state) != 0) {
		log_says_of(LOG_CHILD, user, "⛔ «%s» did not work (status %d)", which,
		                 WIFEXITED(state) ? WEXITSTATUS(state) : -1);
		return false;
	}
	return true;
}

/*
 * ⭐ PHASE 17 (§6.5-bis) — EVERY ENROLMENT MADE BY REMOTIX IS RECORDED IN A FILE.
 *    The service log already said it (DECISIONI §7.21, guarantee 2), but the
 *    journal rotates and the installer does not read it: at uninstallation
 *    the engine must know WHO REMOTIX put in a group (origin DIRECT, it is
 *    removed) and who was already there (PREEXISTING, never touched —
 *    §6.6.4).
 *    ⇒ One JSON line per group, only for the groups the user was NOT in:
 *
 *    {"format":"remotix-enrollments/1","time":"2026-09-30T10:11:12Z","user":"mario",
 *     "uid":1005,"group":"render","gid":989,"origin":"DIRECT",
 *     "by":"REMOTIX at first connection"}
 *
 * ⛔ The file is opened append-only (`O_APPEND`), never rewritten nor
 *    truncated; the folder is opened without following links and must be
 *    owned by root and not writable by others, the file likewise and
 *    regular; every line goes out with ONE `write` and then `fsync` (and the
 *    folder is synced when the file is born).
 * ⚠ If it cannot be recorded, the enrolment is done anyway — a blind session
 *   is worse (§4.2) — but it is SAID, with what the uninstallation will not
 *   know.
 */
#define GROUPS_DIR "/var/lib/remotix"
#define GROUPS_FILE "group-enrollments.jsonl"

/* The JSON text of a string: quotes, backslash and control characters. */
static void json_text(char *d, size_t how_much, const char *s)
{
	size_t k = 0;

	for (; *s && k + 7 < how_much; s++) {
		unsigned char c = (unsigned char)*s;

		if (c == '"' || c == '\\') {
			d[k++] = '\\';
			d[k++] = (char)c;
		} else if (c < 0x20) {
			k += (size_t)snprintf(d + k, how_much - k, "\\u%04x", c);
		} else {
			d[k++] = (char)c;
		}
	}
	d[k] = '\0';
}

/* The folder: opened without following links, owned by root, not writable by
 * others.  If missing (outside the package: a bench) it is created 0700.  -1
 * with `why` written. */
static int groups_open_folder(char *why, size_t how_much)
{
	struct stat st;
	int dfd;

	if (mkdir(GROUPS_DIR, 0700) != 0 && errno != EEXIST) {
		snprintf(why, how_much, "mkdir %s: %s", GROUPS_DIR, strerror(errno));
		return -1;
	}
	dfd = open(GROUPS_DIR, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
	if (dfd < 0) {
		snprintf(why, how_much, "%s: %s", GROUPS_DIR, strerror(errno));
		return -1;
	}
	if (fstat(dfd, &st) != 0 || st.st_uid != 0 || (st.st_mode & 022)) {
		snprintf(why, how_much, "%s is not owned by root or is writable by others", GROUPS_DIR);
		close(dfd);
		return -1;
	}
	return dfd;
}

/* The file, append-only.  -1 with `why` written. */
static int groups_open_file(char *why, size_t how_much)
{
	struct stat st;
	int dfd = groups_open_folder(why, how_much);
	int fd;
	bool fresh = false;

	if (dfd < 0)
		return -1;
	fd = openat(dfd, GROUPS_FILE, O_WRONLY | O_APPEND | O_NOFOLLOW | O_CLOEXEC);
	if (fd < 0 && errno == ENOENT) {
		fd = openat(dfd, GROUPS_FILE,
		            O_WRONLY | O_APPEND | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
		fresh = fd >= 0;
	}
	if (fd < 0) {
		snprintf(why, how_much, "%s/%s: %s", GROUPS_DIR, GROUPS_FILE, strerror(errno));
		close(dfd);
		return -1;
	}
	if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode) || st.st_uid != 0 || (st.st_mode & 022)) {
		snprintf(why, how_much, "%s/%s is not a regular file owned by root, or is writable by others",
		         GROUPS_DIR, GROUPS_FILE);
		close(fd);
		close(dfd);
		return -1;
	}
	/* The new name in the folder must survive a power failure as much as the
	 * line inside the file. */
	if (fresh)
		(void)fsync(dfd);
	close(dfd);
	return fd;
}

/* One line per group.  false with `why` written. */
static bool groups_annotate(int fd, const char *user, uid_t uid, const char *group, gid_t gid,
                          char *why, size_t how_much)
{
	char u[256], g[192], when[32], line[768];
	struct tm tm;
	time_t now = time(NULL);
	int n;

	json_text(u, sizeof u, user);
	json_text(g, sizeof g, group);
	gmtime_r(&now, &tm);
	strftime(when, sizeof when, "%Y-%m-%dT%H:%M:%SZ", &tm);
	n = snprintf(line, sizeof line,
	             "{\"format\":\"remotix-enrollments/1\",\"time\":\"%s\",\"user\":\"%s\","
	             "\"uid\":%lu,\"group\":\"%s\",\"gid\":%lu,\"origin\":\"DIRECT\","
	             "\"by\":\"REMOTIX at first connection\"}\n",
	             when, u, (unsigned long)uid, g, (unsigned long)gid);
	if (n <= 0 || (size_t)n >= sizeof line) {
		snprintf(why, how_much, "the line does not fit");
		return false;
	}
	/* ⛔ A single `write`: with O_APPEND the line arrives whole at the end, or not at all. */
	if (write(fd, line, (size_t)n) != n) {
		snprintf(why, how_much, "write: %s", strerror(errno));
		return false;
	}
	if (fsync(fd) != 0) {
		snprintf(why, how_much, "fsync: %s", strerror(errno));
		return false;
	}
	return true;
}

static bool enroll_in_card_groups(const char *user, uid_t uid, gid_t primary,
                                           const gid_t *groups, int ngroups)
{
	gid_t seen_items[MAX_CARD_GROUPS];
	char names[MAX_CARD_GROUPS][64];
	char nodes[MAX_CARD_GROUPS][96];
	int nseen = collect_card_groups(seen_items, names, nodes, user);
	int placed[MAX_CARD_GROUPS];
	int nplaced = 0;
	char listing[256] = "";
	char why[256] = "";
	size_t used_len = 0;
	char *argv_mod[6];
	int fd;

	if (nseen == 0 || geteuid() != 0)
		return false;
	for (int i = 0; i < nseen; i++) {
		int n;

		/* Whoever is already there is PREEXISTING: not enrolled and not recorded. */
		if (is_in_group(primary, groups, ngroups, seen_items[i]))
			continue;
		n = snprintf(listing + used_len, sizeof listing - used_len, "%s%s", used_len ? "," : "",
		             names[i]);
		if (n > 0 && (size_t)n < sizeof listing - used_len) {
			used_len += (size_t)n;
			placed[nplaced++] = i;
		}
	}
	if (!used_len)
		return false;

	log_says_of(LOG_CHILD, user,
	                 "⭐ FIRST CONNECTION: «%s» is not in the card's groups (%s) and "
	                 "I am PUTTING it there, now — the user's decision of 20 Sep 2026.  "
	                 "⚠ Without it, this session would be born BLIND.  Only the group "
	                 "of the render nodes, read from /dev/dri/renderD* (not `video`: "
	                 "DECISIONS.md §11.38)",
	                 user, listing);
	argv_mod[0] = (char *)"usermod";
	argv_mod[1] = (char *)"-aG";
	argv_mod[2] = listing;
	argv_mod[3] = (char *)user;
	argv_mod[4] = NULL;
	/* The file is opened BEFORE touching the groups, so an obstacle is known
	 * at once; the line is written AFTER, only if `usermod` succeeded:
	 * recording an enrolment never made would make the uninstallation remove a
	 * group put there by others. */
	fd = groups_open_file(why, sizeof why);
	if (!run_as_root("/usr/sbin/usermod", argv_mod, user) &&
	    !run_as_root("/sbin/usermod", argv_mod, user)) {
		log_says_of(LOG_CHILD, user,
		                 "⛔ I could not enrol «%s» in «%s»: the session will be born "
		                 "BLIND, and the manual cure is `usermod -aG %s %s`",
		                 user, listing, listing, user);
		if (fd >= 0)
			close(fd);
		return false;
	}
	for (int j = 0; j < nplaced; j++) {
		int i = placed[j];

		if (fd >= 0 && groups_annotate(fd, user, uid, names[i], seen_items[i], why, sizeof why))
			log_says_of(LOG_CHILD, user,
			                 "⭐ recorded in %s/%s: «%s» in «%s» (gid %ld), DIRECT — the "
			                 "uninstallation will remove it",
			                 GROUPS_DIR, GROUPS_FILE, user, names[i], (long)seen_items[i]);
		else
			log_says_of(LOG_CHILD, user,
			                 "⛔ enrolment NOT RECORDED (%s): «%s» in «%s» (gid %ld) is "
			                 "the work of REMOTIX but %s/%s does not say so — the uninstallation "
			                 "will NOT remove it.  Manual remedy: `gpasswd -d %s %s` after "
			                 "uninstalling",
			                 why, user, names[i], (long)seen_items[i], GROUPS_DIR,
			                 GROUPS_FILE, user, names[i]);
	}
	if (fd >= 0)
		close(fd);
	/* ⛔⭐ 1.5 (DECISIONS.md §11.4): the user manager is NOT made to be born
	 *     again.  Until 1.0 `loginctl terminate-user` did it, and `[M]` 12 Oct
	 *     2026 it killed the user's SSH session (SPECS §5.1).  If a manager is
	 *     alive with the old groups, the card is bridged by `render_grant`
	 *     (GNOME, KDE) in `children_ensure_from()`; the desktop is born anyway. */
	log_says_of(LOG_CHILD, user,
	                 "⭐ «%s» enrolled in «%s»: a user manager born from now on carries the "
	                 "groups.  Nothing is closed",
	                 user, listing);
	return true;
}

/* ⭐ 1.5 (DECISIONS-11.md §11.50) — THE BIRTH, on its own: resolves `user`,
 *    enrols it in the card groups, makes the pair, takes the render grant,
 *    forks and `become_and_exec()`s.  It was the second half of
 *    `children_ensure_from()`; the table (search, slot, name check) stays
 *    there.  Called by `children_ensure_from()` in the single-process server;
 *    the root side of the split will call it too (phase D). */
child_outcome child_birth(const struct birth_opts *b, const char *user,
                          const char *rhost, uint64_t serial,
                          struct child_born *out)
{
	struct passwd pw, *result = NULL;
	char spare[1024];
	gid_t groups[64];
	int ngroups = (int)(sizeof groups / sizeof groups[0]);
	int sv[2];
	int uno = 1;
	bool grant = false;
	pid_t p;

	if (!b || !user || !user[0] || !out)
		return CHILD_FAILED;

	/* ⛔ The name is resolved HERE, in the parent, and the uid that comes out
	 *    is the one the kernel will have to stamp on every message.  ⚠
	 *    Resolving it in the child would mean letting the one to be checked
	 *    say who it is. */
	if (getpwnam_r(user, &pw, spare, sizeof spare, &result) != 0 || !result) {
		registro_dice(LOG_CHILD,
		              "⛔ «%s» passed PAM but is not a user of this "
		              "system (getpwnam: %s): NO child.  ⚠ It is not a "
		              "contradiction — PAM can admit a name that NSS does not "
		              "resolve, and in that case there is no uid to "
		              "drop to",
		              user, strerror(errno));
		return CHILD_NAME_UNKNOWN;
	}
	if (pw.pw_uid == 0) {
		/* ⛔ A child at uid 0 would not be a child: it would be the parent
		 *    under another name, and the reason this file exists — root does
		 *    not talk to the session bus — would apply to it just the same. */
		registro_dice(LOG_CHILD,
		              "⛔ «%s» is uid 0: I am NOT spawning a privileged child.  The "
		              "child exists in order NOT to be root (DECISIONS.md "
		              "§1.10-bis), and one at uid 0 would not have anyone's "
		              "session bus anyway",
		              user);
		return CHILD_FAILED;
	}
	if (getgrouplist(pw.pw_name, pw.pw_gid, groups, &ngroups) < 0) {
		/* More groups than the buffer holds: what is there is taken and it is
		 * DECLARED, because a child with fewer groups than due may hit a
		 * permission denied much later and much further away. */
		ngroups = (int)(sizeof groups / sizeof groups[0]);
		registro_dice(LOG_CHILD,
		              "⚠ «%s» has more than %d groups: the child will carry %d.  "
		              "If something is denied to it, the cause is this line",
		              user, ngroups, ngroups);
	}

	/* ⭐⭐⭐ AND HERE IT IS SAID WHETHER THIS TENANT WILL SEE — the box above
	 *      `card_groups()`.  ⛔ This is the place and no other: it is
	 *      the only point where the product holds **the user's name and their
	 *      groups together**, and it is BEFORE the `fork` — that is, the line
	 *      goes out even when no stage will then be born.  ⚠ The return value
	 *      is not looked at: the session is born anyway, and the degradation
	 *      is declared (I1). */
	/* ⭐ And if something is missing, it is REMEDIED before the `fork` (the
	 *    user's decision, 20 Sep 2026): once enrolled, the groups are read
	 *    again and declared again — the line the administrator reads must be
	 *    the TRUE one of this session, not the one from before the cure. */
	/* ⛔ A close-only child (CLOSE_ORPHAN, no password) has no stage: no
	 *    enrolment and no card grant for it (review 2, L2) — or a hijacked
	 *    network side could re-enrol a user an administrator took out. */
	if (!b->close_only
	    && enroll_in_card_groups(pw.pw_name, pw.pw_uid, pw.pw_gid, groups, ngroups)) {
		ngroups = (int)(sizeof groups / sizeof groups[0]);
		if (getgrouplist(pw.pw_name, pw.pw_gid, groups, &ngroups) < 0)
			ngroups = (int)(sizeof groups / sizeof groups[0]);
	}
	(void)card_groups(pw.pw_name, pw.pw_gid, groups, ngroups);

	/* ⛔ `SOCK_SEQPACKET` for the same reason as the helper: the message
	 *    boundaries are kept by the kernel.  With a stream the framing would
	 *    be ours, and a defect in there would mean "someone else's pixels" —
	 *    that is I3 broken by a reading error.
	 * ⛔ And `CLOEXEC` on the parent's end: the child must NOT hold its
	 *    parent's end, or it would never notice that the parent died. */
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0) {
		registro_dice(LOG_CHILD,
		              "⛔ no socketpair for «%s» (%s): no child, "
		              "no stage",
		              user, strerror(errno));
		return CHILD_FAILED;
	}
	/* ⛔⭐ THIS LINE IS INVARIANT I3 OF THE WHOLE FILE.  Without
	 *     `SO_PASSCRED`, the kernel does not stamp the credentials and every
	 *     message would arrive "without a sender": the parent could only take
	 *     the child's word for it, that is check nothing. */
	if (setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &uno, sizeof uno) != 0) {
		registro_dice(LOG_CHILD,
		              "⛔ SO_PASSCRED does not turn on (%s): without it, the kernel "
		              "does not sign the child's messages and the identity would be "
		              "ITS OWN declaration.  I am NOT spawning the child: better no "
		              "stage than a stage I do not know whose it is",
		              strerror(errno));
		close(sv[0]);
		close(sv[1]);
		return CHILD_FAILED;
	}

	/* ⭐⭐ 1.5 (DECISIONS.md §11.4) — THE CARD FOR A STALE USER MANAGER.
	 *    On GNOME and KDE the compositor is born from the user manager: if that
	 *    one is alive with groups older than `render`, the desktop would draw in
	 *    software.  ⇒ An ACL for the user's private group on `renderD*`, for the
	 *    life of this child.  XFCE and LXQt need nothing: labwc is born from
	 *    the child, with the groups read above.  `[M]` 13 Oct 2026, the four
	 *    boxes and the tablet. */
	{
		DesktopSession ds = desktop_session();

		if (!b->close_only && (ds == SESSION_DESKTOP_GNOME || ds == SESSION_DESKTOP_KDE)) {
			int need = render_grant_needed(pw.pw_uid, pw.pw_name);

			if (need > 0)
				grant = render_grant_add(pw.pw_name, pw.pw_uid, pw.pw_gid);
			else if (need < 0)
				log_says_of(LOG_CHILD, pw.pw_name,
				            "⚠ the groups of «%s»'s user manager cannot be read: no card "
				            "grant, and if they are old the desktop draws in software",
				            pw.pw_name);
		}
	}

	p = fork();
	if (p < 0) {
		registro_dice(LOG_CHILD, "⛔ fork for «%s»: %s — no stage", user,
		              strerror(errno));
		close(sv[0]);
		close(sv[1]);
		if (grant)
			render_grant_remove(pw.pw_name, pw.pw_uid, pw.pw_gid);
		return CHILD_FAILED;
	}
	if (p == 0) {
		close(sv[0]);
		become_and_exec(b, serial, rhost, sv[1], &pw, groups, ngroups);
		_exit(38); /* never reached */
	}

	close(sv[1]);
	/* ⛔ Non-blocking on the PARENT's side, and only on that one: here we are
	 *    inside the server's single `poll` loop, and a read that waits stops
	 *    all connections together (`CODER.md` §4.4) — the defect just cured on
	 *    PAM, brought back through another door.  ⚠ The CHILD's end stays
	 *    blocking on purpose: there waiting is the job. */
	fcntl(sv[0], F_SETFL, O_NONBLOCK);

	memset(out, 0, sizeof *out);
	out->pid = p;
	out->fd = sv[0];
	out->uid = pw.pw_uid;
	out->gid = pw.pw_gid;
	out->render_grant = grant;
	snprintf(out->user, sizeof out->user, "%s", pw.pw_name);

	registro_dice(LOG_CHILD,
	              "⭐ child spawned for «%s»: pid %ld, uid %ld, gid %ld, "
	              "serial %llu.  ⛔ That it REALLY is that uid is not for me "
	              "to say: the kernel will say it on each of its messages (SO_PASSCRED)",
	              out->user, (long)out->pid, (long)out->uid, (long)out->gid,
	              (unsigned long long)serial);
	return CHILD_READY;
}

static void birth_opts_of(const struct children *f, struct birth_opts *b)
{
	memset(b, 0, sizeof *b);
	b->canvas_w = f->canvas_w;
	b->canvas_h = f->canvas_h;
	b->dir_survey = f->has_survey ? f->dir_survey : NULL;
	b->quality_rises = f->phase9_quality_rises;
	b->bandwidth_cap_mbit = f->phase9_bandwidth_cap_mbit;
	b->audio_silence = f->phase9_audio_silence;
	b->my_path = f->my_path;
	b->parent_uid = -1; /* the parent is root: the child's default */
}

#define SPAWN_WAIT_MS 15000

static const char *refusal_text(int r)
{
	switch (r) {
	case RXR_REF_GRANT:        return "no valid grant (unknown, used or expired)";
	case RXR_REF_FULL:         return "the root side's children are at its cap";
	case RXR_REF_USER:         return "the name is refused (uid 0, denied-users, or it no longer resolves)";
	case RXR_REF_NO_ORPHAN:    return "no live remotix session of that user in logind";
	case RXR_REF_FAILED:       return "the birth failed: the reason is in the root side's line above";
	case RXR_REF_CLOSING:      return "a child of that user is still being closed";
	case RXR_REF_MOVED:        return "the name now points to another uid";
	case RXR_REF_NAME_UNKNOWN: return "the name could not be looked up now";
	case RXR_REF_RATE:         return "over the root side's rate bound (one close-only birth per user every 30 s, or the CLOSE_ORPHAN bucket)";
	case ROOTSIDE_NO_ANSWER:   return "no answer from the root side within the wait";
	case ROOTSIDE_NO_GRANT:    return "no grant kept for this login (expired, used, or the table was full)";
	case ROOTSIDE_NOT_SENT:    return "the request could not be sent to the root side";
	case ROOTSIDE_LOST:        return "the root channel is lost";
	default:                   return "a refusal this side does not know";
	}
}

/* ⭐⭐ 1.5 (§11.50) — the network side's birth: SPAWN with the grant of this
 *     login (or CLOSE_ORPHAN for a desktop found again: `rhost` NULL), and the
 *     slot is filled with what the root side answered — serial, pid, uid,
 *     gid and the socket end.  ⛔ The uid/gid are the ROOT SIDE's resolution:
 *     the kernel stamps them on every message, and `credentials_match()`
 *     compares, unchanged. */
static child_outcome ensure_remote(struct children *f, struct child *g,
                                   const char *user, const char *rhost)
{
	struct rootside_born b;
	int one = 1;
	int r;
	uint64_t asked_ms = log_now_ms();

	if (rhost)
		r = rootside_spawn(user, rhost, f->canvas_w, f->canvas_h, SPAWN_WAIT_MS, &b);
	else
		r = rootside_close_orphan(user, SPAWN_WAIT_MS, &b);
	if (r != 0) {
		registro_dice(LOG_CHILD,
		              "⛔ the root side did NOT give birth to a child for «%s» "
		              "(%s): %s",
		              user, rhost ? "SPAWN" : "CLOSE_ORPHAN", refusal_text(r));
		return r == RXR_REF_CLOSING        ? CHILD_CLOSING
		       : r == RXR_REF_MOVED        ? CHILD_NAME_MOVED
		       : r == RXR_REF_NAME_UNKNOWN ? CHILD_NAME_UNKNOWN
		                                   : CHILD_FAILED;
	}
	/* ⛔ Review 2, M3: the request number already binds the answer to the
	 *    ask, and the root side writes the CANONICAL name (NSS's `pw_name`):
	 *    with sssd case-insensitive or an alias «BRUNO» comes back «bruno».
	 *    Comparing it with the typed name killed every child of such a user
	 *    — never able to log in, worse than 1.0, which kept `c.user` as it
	 *    was.  ⇒ The canonical name is taken; the uid ≠ 0, the length and
	 *    the socket are still checked. */
	if (!b.user[0] || strlen(b.user) >= sizeof g->user || b.uid == 0 || b.fd < 0) {
		registro_dice(LOG_CHILD,
		              "⛔⛔ the root side answered SPAWNED for «%s» with user «%s» "
		              "uid %ld: not a child this side can hold — the child is killed",
		              user, b.user, (long)b.uid);
		(void)rootside_signal(b.serial, SIGKILL);
		if (b.fd >= 0)
			close(b.fd);
		return CHILD_FAILED;
	}
	/* ⛔ `SO_PASSCRED` is per socket: set again on the end received. */
	if (setsockopt(b.fd, SOL_SOCKET, SO_PASSCRED, &one, sizeof one) != 0) {
		registro_dice(LOG_CHILD,
		              "⛔ SO_PASSCRED does not turn on on the socket of «%s» (%s): "
		              "the child is killed — no stage I cannot prove",
		              user, strerror(errno));
		(void)rootside_signal(b.serial, SIGKILL);
		close(b.fd);
		return CHILD_FAILED;
	}
	fcntl(b.fd, F_SETFL, O_NONBLOCK);
	fcntl(b.fd, F_SETFD, FD_CLOEXEC);
	memset(g, 0, sizeof *g);
	g->serial = b.serial;
	memcpy(g->user, b.user, strlen(b.user) + 1); /* < sizeof g->user, checked above */
	/* review 4, finding 6: the typed name, for the session's messages */
	if (strcmp(user, b.user) != 0 && strlen(user) < sizeof g->alias)
		snprintf(g->alias, sizeof g->alias, "%s", user);
	snprintf(g->rhost, sizeof g->rhost, "%s", rhost ? rhost : "");
	g->close_only = rhost == NULL; /* CLOSE_ORPHAN: the root side made it --close-only */
	g->uid = b.uid;
	g->gid = b.gid;
	g->used = true;
	g->pid = b.pid;
	g->fd = b.fd;
	g->born_ms = log_now_ms();
	g->last_recheck_ms = g->born_ms;
	/* ⭐ «SPAWNED after N ms»: the time this loop stood still waiting for the
	 *    root side (enrolment, render grant, fork) — read by the stress bench. */
	registro_dice(LOG_CHILD,
	              "⭐ the root side gave birth to the child of «%s»: pid %ld, uid "
	              "%ld, gid %ld, serial %llu — SPAWNED after %llu ms; its socket is "
	              "here, and the kernel stamps every message (SO_PASSCRED)",
	              g->user, (long)g->pid, (long)g->uid, (long)g->gid,
	              (unsigned long long)g->serial,
	              (unsigned long long)(g->born_ms - asked_ms));
	return CHILD_READY;
}

bool children_ensure(children *f, const char *user)
{
	return children_ensure_from(f, user, NULL) == CHILD_READY;
}

child_outcome children_ensure_from(children *f, const char *user, const char *rhost)
{
	struct child *g;
	int free_slot = -1;

	if (!f || !user || !user[0])
		return CHILD_FAILED;

	/* ⛔⭐ I2 — "only one graphical session per user".  Two connections of the
	 *     same user do NOT make two children: the second finds the first, and
	 *     sees the same stage.  ⚠ And if the first is dead, the slot has
	 *     already been freed by `children_move()`: nothing is resurrected here. */
	g = search_login(f, user);
	/* ⭐ 1.5 (network mode only): a close-only child is a desktop being closed,
	 *    not a stage to attach to. */
	if (g && g->close_only)
		return CHILD_CLOSING;
	if (g && !g->exiting) {
		/* ⛔ A new RCP session attaching to this child: the name is checked
		 *    again NOW, once per login — the per-message check is gone
		 *    (`name_still_ours()`), and a login is exactly the moment a
		 *    name NSS now gives to another uid would be bound to a stage. */
		char why[256];

		why[0] = 0;
		if (!name_still_ours(g, why, sizeof why)) {
			registro_dice(LOG_CHILD,
			              "⛔⛔ «%s» logs in and its child can no longer be "
			              "proven to be that user: %s.  The child is killed, "
			              "and this login gets none",
			              user, why);
			if (g->pid > 0)
				child_signal(f, g, SIGKILL);
			child_dismiss(f, g, "its name no longer resolves to its uid");
			return CHILD_NAME_MOVED;
		}
	}
	if (g) {
		registro_dice(LOG_CHILD,
		              "«%s» is already served by the child pid %ld (uid %ld): a "
		              "second one is NOT born — invariant I2, and the stage is the "
		              "same because it belongs to the SESSION (I4)",
		              user, (long)g->pid, (long)g->uid);
		return CHILD_READY;
	}

	for (int i = 0; i < f->cap; i++)
		if (!f->v[i].used) {
			free_slot = i;
			break;
		}
	if (free_slot < 0) {
		registro_dice(LOG_CHILD,
		              "⛔ %d children already alive: «%s» will NOT get one, and so "
		              "will not get a stage.  It is a declared no, not a maybe "
		              "(invariant I3)",
		              f->cap, user);
		return CHILD_FAILED;
	}

	if (f->remote)
		return ensure_remote(f, &f->v[free_slot], user, rhost);
	{
		struct birth_opts b;
		struct child_born c;
		child_outcome o;

		birth_opts_of(f, &b);
		o = child_birth(&b, user, rhost, f->next_serial, &c);
		if (o != CHILD_READY)
			return o;
		g = &f->v[free_slot];
		memset(g, 0, sizeof *g);
		g->render_grant = c.render_grant;
		g->serial = f->next_serial;
		snprintf(g->user, sizeof g->user, "%s", c.user);
		snprintf(g->rhost, sizeof g->rhost, "%s", rhost ? rhost : "");
		g->uid = c.uid;
		g->gid = c.gid;
		g->used = true;
		g->pid = c.pid;
		g->fd = c.fd;
	}
	g->born_ms = log_now_ms();
	g->last_recheck_ms = g->born_ms;
	f->next_serial++;
	return CHILD_READY;
}

size_t children_descriptors(children *f, struct pollfd *fds, size_t max)
{
	size_t n = 0;
	if (!f)
		return 0;
	for (int i = 0; i < f->cap && n < max; i++) {
		if (!f->v[i].used || f->v[i].fd < 0)
			continue;
		fds[n].fd = f->v[i].fd;
		fds[n].events = POLLIN;
		fds[n].revents = 0;
		n++;
	}
	return n;
}

int children_count(const children *f)
{
	int n = 0;
	if (!f)
		return 0;
	for (int i = 0; i < f->cap; i++)
		if (f->v[i].used)
			n++;
	return n;
}

/* ⭐⭐ WHO IS INSIDE — phase 10, and it serves the BUDGET.
 *
 * ⛔ "Who is inside" for the budget is NOT "who has a slot in the session
 *    registry": it is **who has a stage**.  The two sets do not coincide, and
 *    that is the fact of §3.2: a session that left its slot through silence
 *    **still encodes** as long as its stage is alive — the *ghost* — and costs
 *    the GPU exactly as much as the others.  ⇒ A budget counted on the slots
 *    **underestimates**, and underestimating is the direction that starves
 *    everyone (§1.33).
 *
 * ⚠ The index goes from 0 to `children_count() − 1` and **is not stable between
 *   two calls**: slots get freed.  It serves to scan once, within the same
 *   round of the loop, and for nothing else. */
const char *children_nth_user(const children *f, int which)
{
	int n = 0;

	if (!f || which < 0)
		return NULL;
	for (int i = 0; i < f->cap; i++) {
		if (!f->v[i].used)
			continue;
		if (n == which)
			return f->v[i].user;
		n++;
	}
	return NULL;
}

bool children_alive_of(const children *f, const char *user)
{
	const struct child *g;
	if (!f || !user)
		return false;
	g = search((children *)f, user);
	return g && g->pid > 0 && !child_closing(g);
}

pid_t children_pid_of(const children *f, const char *user)
{
	const struct child *g;
	if (!f || !user)
		return -1;
	g = search((children *)f, user);
	return g ? g->pid : -1;
}

/* A frame piece has arrived, and the credentials were right. */
static void assemble_piece(struct children *f, struct child *g,
                        const struct body_frame *c, const uint8_t *data)
{
	if (c->total == 0 || c->total > FRAME_MAX) {
		if (refused(f, g))
			registro_dice(LOG_CHILD,
			              "⛔ «%s» announces a frame of %u bytes: outside the "
			              "cap of §6.2 (1..%u).  It is dropped, and NOT truncated: a "
			              "cut frame delivered as whole is a "
			              "frame that lies",
			              g->user, c->total, FRAME_MAX);
		return;
	}
	if (c->piece > MAX_PIECE || (uint64_t)c->offset + c->piece > c->total) {
		if (refused(f, g))
			registro_dice(LOG_CHILD,
			              "⛔ «%s»: piece out of size (offset %u + %u of %u): "
			              "discarded",
			              g->user, c->offset, c->piece, c->total);
		free(g->assembly);
		g->assembly = NULL;
		g->assembly_total = g->assembly_got = 0;
		return;
	}

	if (c->offset == 0) {
		free(g->assembly);
		g->assembly = (uint8_t *)malloc(c->total);
		if (!g->assembly) {
			registro_dice(LOG_CHILD,
			              "⛔ «%s»: %u bytes of frame do not fit in "
			              "memory",
			              g->user, c->total);
			g->assembly_total = g->assembly_got = 0;
			return;
		}
		g->assembly_total = c->total;
		g->assembly_got = 0;
		g->assembly_codec = c->codec;
		g->assembly_key = c->key;
		g->assembly_w = c->width;
		g->assembly_h = c->height;
		g->assembly_instant = c->instant_us;
		g->assembly_input = c->input;
	}
	/* ⛔ Pieces are accepted ONLY in order, and one out of place throws away
	 *    everything: stitching a hole would mean guessing what was missing, and
	 *    that is the leniency that hides (`REVIEWER.md` §5). */
	if (!g->assembly || c->offset != g->assembly_got || c->codec != g->assembly_codec
	    || c->total != g->assembly_total) {
		if (refused(f, g))
			registro_dice(LOG_CHILD,
			              "⛔ «%s»: piece out of order (expected %zu, got "
			              "%u): the whole frame is DROPPED",
			              g->user, g->assembly_got, c->offset);
		free(g->assembly);
		g->assembly = NULL;
		g->assembly_total = g->assembly_got = 0;
		return;
	}
	memcpy(g->assembly + c->offset, data, c->piece);
	g->assembly_got += c->piece;
	if (g->assembly_got < g->assembly_total)
		return;

	/* ⛔⭐ AND THIS LINE MOVED TO CHATTER WITH PHASE 3.
	 *
	 *     With a single frame it was the line that proved the whole of phase 2.
	 *     ⛔ At sixty per second it becomes sixty lines per second per user,
	 *     and a log that repeats itself can no longer be read — that is the
	 *     same reason `bool video_fatto` existed.  ⚠ The fact does NOT vanish:
	 *     it stays in the chatter, and the summary count is written by
	 *     `counted` below once per second.  The first one, the one that says
	 *     whether the stage works, is written anyway. */
	if (g->frames_received == 0)
		registro_dice(LOG_CHILD,
		              "⭐ FIRST complete frame from «%s» (uid %ld, kernel "
		              "stamp): codec %u, %zu bytes, %ux%u, %s",
		              g->user, (long)g->uid, g->assembly_codec, g->assembly_total,
		              g->assembly_w, g->assembly_h,
		              g->assembly_key ? "KEYFRAME" : "delta");
	else
		log_detail(LOG_CHILD,
		                   "frame from «%s»: codec %u, %zu bytes, %s",
		                   g->user, g->assembly_codec, g->assembly_total,
		                   g->assembly_key ? "KEYFRAME" : "delta");
	g->frames_received++;
	g->byte_got += g->assembly_total;
	if (g->assembly_key)
		g->keys_received++;
	if (f->deposit)
		f->deposit(f->ctx, g->user, g->uid, g->assembly_codec,
		            g->assembly_key != 0, g->assembly, g->assembly_total, g->assembly_w,
		            g->assembly_h, g->assembly_instant, g->assembly_input);
	free(g->assembly);
	g->assembly = NULL;
	g->assembly_total = g->assembly_got = 0;
}

/* ⭐⭐ A CURSOR piece has arrived, and the credentials were right.
 *
 * ⚠ Why it has its own assembly and does not reuse the frame's: the two
 *   arrive interleaved on the same socket, and with a single table every
 *   shape change would drop the half-assembled frame and vice versa. */
/* ⭐⭐ PHASE 7 — the clipboard text the SESSION copied, one piece at a time.
 *     Same mould as the cursor, and the differences are two and declared:
 *
 *       · the cap is that of `RCP.md` §5.4 — **1 000 000 bytes** — and it is
 *         enforced HERE because here the sender is another process.  ⚠ It is
 *         not a duplicate of the check in `clipboard.c`: that one is a module
 *         we trust, this one is a socket;
 *       · **one extra byte** is allocated and the zero is put there: from
 *         here on the text travels as a string, and `clipboard.c` has already
 *         guaranteed it does not contain one in the middle.
 */
static void assemble_clipboard(struct children *f, struct child *g,
                          const struct body_clipboard *c, const uint8_t *data)
{
	if (c->total > CLIPBOARD_CAP) {
		if (refused(f, g))
			registro_dice(LOG_CHILD,
			              "⛔ «%s» announces %u bytes of clipboard: over the cap of "
			              "§5.4 (%u).  It is dropped, and NOT truncated — a cut text "
			              "pasted into a terminal is worse than a missing text",
			              g->user, c->total, CLIPBOARD_CAP);
		return;
	}
	/* ⚠ Zero bytes is a LEGITIMATE fact: the clipboard emptied.  It is
	 *   delivered, and the receiver decides — it is not this table's job. */
	if (c->total == 0) {
		if (f->on_clipboard_text)
			f->on_clipboard_text(f->ctx_clipboard, g->user, g->uid, "", 0);
		return;
	}
	if (c->piece > MAX_PIECE || (uint64_t)c->offset + c->piece > c->total) {
		if (refused(f, g))
			registro_dice(LOG_CHILD,
			              "⛔ «%s»: clipboard piece out of size (offset %u + %u of "
			              "%u): discarded",
			              g->user, c->offset, c->piece, c->total);
		if (g->app_mount)
			explicit_bzero(g->app_mount, g->app_total);
		free(g->app_mount);
		g->app_mount = NULL;
		g->app_total = g->app_got = 0;
		return;
	}
	if (c->offset == 0) {
		if (g->app_mount)
			explicit_bzero(g->app_mount, g->app_total);
		free(g->app_mount);
		g->app_mount = (uint8_t *)malloc((size_t)c->total + 1u);
		if (!g->app_mount) {
			registro_dice(LOG_CHILD,
			              "⛔ «%s»: %u bytes of clipboard do not fit in memory",
			              g->user, c->total);
			g->app_total = g->app_got = 0;
			return;
		}
		g->app_total = c->total;
		g->app_got = 0;
	}
	/* ⛔ In order and nothing else, like the frame and the cursor.  ⚠ And here
	 *    the guessed hole would be **worse**: a wrong frame lasts 20 ms, a
	 *    wrong text gets pasted into a terminal. */
	if (!g->app_mount || c->offset != g->app_got
	    || c->total != g->app_total) {
		if (refused(f, g))
			registro_dice(LOG_CHILD,
			              "⛔ «%s»: clipboard piece out of order (expected %zu, "
			              "got %u): the whole text is DROPPED",
			              g->user, g->app_got, c->offset);
		if (g->app_mount)
			explicit_bzero(g->app_mount, g->app_total);
		free(g->app_mount);
		g->app_mount = NULL;
		g->app_total = g->app_got = 0;
		return;
	}
	memcpy(g->app_mount + c->offset, data, c->piece);
	g->app_got += c->piece;
	if (g->app_got < g->app_total)
		return;

	g->app_mount[g->app_total] = 0;
	registro_dice(LOG_CHILD,
	              "⭐ «%s» copied %zu bytes of text in the session: to the "
	              "client (§7.4)",
	              g->user, g->app_total);
	if (f->on_clipboard_text)
		f->on_clipboard_text(f->ctx_clipboard, g->user, g->uid,
		                    (const char *)g->app_mount, g->app_total);
	explicit_bzero(g->app_mount, g->app_total);
	free(g->app_mount);
	g->app_mount = NULL;
	g->app_total = g->app_got = 0;
}

static void assemble_cursor(struct children *f, struct child *g,
                          const struct body_cursor *c, const uint8_t *data)
{
	/* ⛔ The cap is that of `RCP.md` §5.5 — 256x256 in BGRA — and it is
	 *    enforced HERE because here the sender is another process.  ⚠ It is
	 *    not a duplicate of the limits of `cursor.c`: that one is a module we
	 *    trust, this one is a socket. */
	if (c->total > (uint32_t)CURSOR_MAX_SIDE * CURSOR_MAX_SIDE * 4u) {
		if (refused(f, g))
			registro_dice(LOG_CHILD,
			              "⛔ «%s» announces a cursor of %u bytes: over the cap of "
			              "§5.5 (%ux%u in BGRA).  It is dropped",
			              g->user, c->total, CURSOR_MAX_SIDE, CURSOR_MAX_SIDE);
		return;
	}

	/* ⭐ The hidden one arrives without an image, and is delivered at once: it
	 *    is the only way the client has of knowing the pointer has vanished. */
	if (c->total == 0) {
		if (f->cursor)
			f->cursor(f->ctx, g->user, g->uid, c->width, c->height,
			           c->active_x, c->active_y, NULL, 0);
		return;
	}
	if (c->piece > MAX_PIECE || (uint64_t)c->offset + c->piece > c->total) {
		if (refused(f, g))
			registro_dice(LOG_CHILD,
			              "⛔ «%s»: cursor piece out of size (offset %u + %u of "
			              "%u): discarded",
			              g->user, c->offset, c->piece, c->total);
		free(g->cur_mount);
		g->cur_mount = NULL;
		g->cur_total = g->cur_got = 0;
		return;
	}
	if (c->offset == 0) {
		free(g->cur_mount);
		g->cur_mount = (uint8_t *)malloc(c->total);
		if (!g->cur_mount) {
			g->cur_total = g->cur_got = 0;
			return;
		}
		g->cur_total = c->total;
		g->cur_got = 0;
		g->cur_l = c->width;
		g->cur_a = c->height;
		g->cur_ax = c->active_x;
		g->cur_ay = c->active_y;
	}
	/* ⛔ In order and nothing else, like the frame: stitching a hole would mean
	 *    guessing what was missing — and a guessed cursor is a cursor made of
	 *    someone else's memory. */
	if (!g->cur_mount || c->offset != g->cur_got || c->total != g->cur_total
	    || c->width != g->cur_l || c->height != g->cur_a) {
		if (refused(f, g))
			log_detail(LOG_CHILD,
			                   "«%s»: cursor piece out of order: dropping the half "
			                   "shape (the client keeps the previous one)",
			                   g->user);
		free(g->cur_mount);
		g->cur_mount = NULL;
		g->cur_total = g->cur_got = 0;
		return;
	}
	memcpy(g->cur_mount + c->offset, data, c->piece);
	g->cur_got += c->piece;
	if (g->cur_got < g->cur_total)
		return;

	if (f->cursor)
		f->cursor(f->ctx, g->user, g->uid, g->cur_l, g->cur_a, g->cur_ax,
		           g->cur_ay, g->cur_mount, g->cur_total);
	free(g->cur_mount);
	g->cur_mount = NULL;
	g->cur_total = g->cur_got = 0;
}

/* ⛔ Returns `false` when the child is gone — and the caller MUST stop
 * reading its descriptor.  ⚠ Without this value, the loop of `children_move()`
 * would keep reading a slot just zeroed: the kind of defect that reads well
 * and is never seen. */
static bool handle(struct children *f, struct child *g, const struct head *t,
                   const uint8_t *body, size_t byte)
{
	switch (t->kind) {
	case MSG_INTRO: {
		struct body_whoami s;
		if (byte < WHOAMI_MIN)
			return refused_quietly(g);
		memset(&s, 0, sizeof s);
		memcpy(&s, body, byte < sizeof s ? byte : sizeof s);
		g->whoami_asked_ms = 0; /* it answered: no question is waiting any more */
		/* ⛔ 24 Oct 2026, review of the child-msg fuzz (present since 1.0: the same lines are
		 *   in 04f6aa18): the socket is UNTRUSTED, and `user` and `runtime` are fixed arrays
		 *   that the log prints with %s.  Nothing guaranteed the final zero: a child that
		 *   fills them to the last byte made the log read past the copy. */
		s.user[sizeof s.user - 1] = 0;
		s.runtime[sizeof s.runtime - 1] = 0;
		/* ⛔ AND HERE THE CIRCLE CLOSES: the child says what the KERNEL
		 *    answered it about itself (`getresuid`), and the parent compares
		 *    it with what the KERNEL stamped on the message.  If the two
		 *    diverged, one of the two is reading a variable instead of asking
		 *    — and the child would be killed. */
		if (s.uid != (uint32_t)g->uid || s.euid != (uint32_t)g->uid
		    || s.suid != (uint32_t)g->uid) {
			registro_dice(LOG_CHILD,
			              "⛔⛔ «%s» says it is uid %u/%u/%u and the kernel "
			              "stamped it as %ld: the child is killed",
			              g->user, s.uid, s.euid, s.suid, (long)g->uid);
			if (g->pid > 0)
				child_signal(f, g, SIGKILL);
			child_dismiss(f, g, "declares a uid different from the stamped one");
			return false;
		}
		/* ⭐⛔ THE NAME, answered by the child (see `body_whoami`): the periodic check that used to run in the parent's
		 *    loop.  A name that moved to another uid costs the child as before — the parent still asks NSS
		 *    itself at every login, so a child that lied here is found out the moment someone logs in under that name. */
		/* ⚠ ONLY «another uid» costs the child.  «Gone» is NOT acted on here: the child asks NSS as an ordinary user, and a
		 *   directory that wants root to bind (LDAP, sssd with a protected cache) would make EVERY child answer «gone» and
		 *   die every minute.  «Gone» is a line in the log, at most one per NAME_GONE_LOG_MS per child; the decision is left
		 *   to the check the PARENT makes at every login (`children_ensure_from()`, as root), which kills the child the
		 *   moment someone logs in under a name that really no longer resolves.  A child not yet introduced
		 *   (`showed_up` false: its birth message, name_check 0) is never judged. */
		if (g->showed_up && s.name_check == NAME_GONE) {
			uint64_t now = log_now_ms();

			if (g->name_gone_logged_ms == 0 || now >= g->name_gone_logged_ms + NAME_GONE_LOG_MS) {
				g->name_gone_logged_ms = now ? now : 1;
				registro_dice(LOG_CHILD,
				              "⚠ the child of «%s» says its name does not resolve (it asks NSS as the user, which "
				              "may not be allowed to): nothing is done now — the check at the next login of «%s» decides",
				              g->user, g->user);
			}
		}
		if (g->showed_up && s.name_check == NAME_OTHER_UID) {
			char why[256];

			name_why(g->user, g->uid, (int)s.name_check, (uid_t)s.name_uid, why, sizeof why);
			registro_dice(LOG_CHILD,
			              "⛔⛔ the child of «%s» can no longer be "
			              "proven to be that user: %s.  ⚠ A child "
			              "running as the wrong user is I3 violated "
			              "invisibly.  The child is killed.",
			              g->user, why);
			if (g->pid > 0)
				child_signal(f, g, SIGKILL);
			child_dismiss(f, g, "its name no longer resolves to its uid");
			return false;
		}
		if (g->showed_up) {
			log_detail(LOG_CHILD,
			                   "«%s» rechecked: uid %u, pid %u, parent %u, "
			                   "%u descriptors — the link holds",
			                   g->user, s.euid, s.pid, s.ppid, s.descriptors);
			return true;
		}
		g->showed_up = true;
		registro_dice(LOG_CHILD,
		              "⭐ «%s» introduces itself: pid %u (parent %u), uid %u/%u/%u, "
		              "gid %u/%u/%u, %u open descriptors, runtime «%s» %s, "
		              "bus socket %s",
		              g->user, s.pid, s.ppid, s.uid, s.euid, s.suid, s.gid,
		              s.egid, s.sgid, s.descriptors, s.runtime,
		              s.runtime_c_e ? "exists and is its own" : "⛔ does NOT exist or is not its own",
		              s.socket_bus_c_e ? "exists" : "⛔ does not exist");
		return true;
	}
	case MSG_SESSION_FINISHED:
		/*
		 * ⭐⭐ §7.6, the twin: the graphical session is over and no client
		 *     asked for it — the user chose "Log out…" in the desktop menu.
		 *
		 * ⛔ And whoever is watching must know NOW: by keeping quiet, the
		 *    clients would stay on a frozen screen until the thirty seconds of
		 *    silence, and then read "network error" — which is exactly
		 *    finding B-7.
		 */
		registro_dice(LOG_CHILD,
		              "⭐ §7.6: the graphical session of «%s» IS OVER (no "
		              "client asked for it: the user logged out from the "
		              "desktop menu).  Whoever is watching gets the farewell 0x10",
		              g->user);
		if (f->on_session_finished)
			f->on_session_finished(f->ctx_session_finished, g->user, g->uid);
		else
			registro_dice(LOG_CHILD,
			              "⚠ no «session over» hook: the clients of «%s» "
			              "were NOT warned, and will wait the thirty "
			              "seconds of silence",
			              g->user);
		return true;
	case MSG_STAGE: {
		struct body_stage p;
		if (byte < sizeof p)
			return refused_quietly(g);
		memcpy(&p, body, sizeof p);
		/* ⛔ 24 Oct 2026, review of the child-msg fuzz (present since 1.0, 04f6aa18): `monitor`
		 *   and `fault` come from the untrusted socket and the log prints them with %s: the
		 *   final zero is FORCED, not assumed. */
		p.monitor[sizeof p.monitor - 1] = 0;
		p.fault[sizeof p.fault - 1] = 0;
		registro_dice(LOG_CHILD,
		              "%s the stage of «%s»: bus %s, session %u, grab %u, "
		              "monitor «%s» (%u before, %u after), %ux%u stride %u at %u "
		              "bits, %u streams delivering%s%s",
		              p.streams > 0 ? "⭐" : "⛔", g->user,
		              p.bus_open ? "OPEN" : "⛔ NO", p.state_session,
		              p.take, p.monitor, p.monitor_before, p.monitor_after,
		              p.width, p.height, p.stride, p.bit, p.streams,
		              p.fault[0] ? " — " : "", p.fault);
		return true;
	}
	case MSG_CURSOR: {
		struct body_cursor c;
		if (byte < sizeof c)
			return refused_quietly(g);
		memcpy(&c, body, sizeof c);
		if (byte < sizeof c + c.piece)
			return refused_quietly(g);
		assemble_cursor(f, g, &c, body + sizeof c);
		return true;
	}
	case MSG_FRAME: {
		struct body_frame c;
		if (byte < sizeof c)
			return refused_quietly(g);
		memcpy(&c, body, sizeof c);
		if (byte < sizeof c + c.piece)
			return refused_quietly(g);
		assemble_piece(f, g, &c, body + sizeof c);
		return true;
	}
	case MSG_BLOCK: {
		struct body_block c;
		if (byte < sizeof c)
			return refused_quietly(g);
		memcpy(&c, body, sizeof c);
		if (byte < sizeof c + c.byte)
			return refused_quietly(g);
		/* ⛔⭐ AND HERE THE CODEC IS CHECKED, instead of trusted.
		 *
		 *     The child runs as the user and the parent is privileged: a
		 *     number that crosses that boundary is an input, not a datum.
		 *     ⚠ A `codec` that §6.3 does not define would end up **inside the
		 *     datagram** and the client would discard it — that is, the audio
		 *     would not arrive, without any line saying why. */
		if (c.codec != 1 && c.codec != 2) {
			if (refused(f, g))
				registro_dice(LOG_CHILD,
				              "⛔ «%s» sends an audio block with codec %u, which "
				              "§6.3 does not define (1 = Opus, 2 = PCM): DROPPED",
				              g->user, c.codec);
			return true;
		}
		if (f->on_block)
			f->on_block(f->ctx_block, g->user, g->uid, c.codec,
			             c.instant_us, body + sizeof c, c.byte);
		return true;
	}
	case MSG_CLIPBOARD_FROM_SESSION: {
		struct body_clipboard c;
		if (byte < sizeof c)
			return refused_quietly(g);
		memcpy(&c, body, sizeof c);
		if (byte < sizeof c + c.piece)
			return refused_quietly(g);
		assemble_clipboard(f, g, &c, body + sizeof c);
		return true;
	}
	case MSG_CLIPBOARD_REQUEST: {
		struct body_clipboard c;
		if (byte < sizeof c)
			return refused_quietly(g);
		memcpy(&c, body, sizeof c);
		/* ⛔⛔ AND IF NOBODY IS LISTENING THE ANSWER GOES OUT ANYWAY, at once
		 *      and empty-handed.
		 *
		 *      The case is real and frequent: the session outlives the client
		 *      (invariant I4), so someone can paste **when no client is
		 *      attached**.  ⚠ Keeping quiet here would leave the pasting
		 *      application hanging indefinitely, and the symptom — "the
		 *      desktop has frozen" — names neither the clipboard nor the
		 *      detach.  ⇒ The timeout is not enough: the answer goes NOW. */
		if (!f->on_clipboard_request) {
			registro_dice(LOG_CHILD,
			              "«%s» is pasting (request %u) and nobody serves "
			              "the clipboard: answering «I don't have it» at once, instead of "
			              "leaving the paster hanging",
			              g->user, c.serial);
			children_clipboard_response(f, g->user, c.serial, NULL, 0);
			return true;
		}
		f->on_clipboard_request(f->ctx_clipboard, g->user, g->uid, c.serial);
		return true;
	}
	case MSG_CANVAS: {
		struct body_canvas c;
		if (byte < sizeof c)
			return refused_quietly(g);
		memcpy(&c, body, sizeof c);
		/* ⭐⭐ "WAIT" before anything else: it is not an answer, it is the news
		 *     that an answer is on its way.  ⛔ Treating it like the others
		 *     would fire the "did not make it" branch — that is precisely the
		 *     inference this message exists to remove. */
		if (c.should_wait) {
			registro_dice(LOG_CHILD,
			              "«%s»: the stage for the canvas %ux%u is NOT there YET — "
			              "the deadline of §7.1 is postponed",
			              g->user, c.intended_w, c.intended_h);
			if (f->on_canvas_wait)
				f->on_canvas_wait(f->ctx_canvas_wait, g->user, g->uid,
				                   c.intended_w, c.intended_h);
			return true;
		}
		/* ⛔⭐ §7.1 — THE ANSWER TO THE CANVAS, and the parent no longer GUESSES
		 *     it from the frames: it carries the size ASKED (to recognise which
		 *     request it answers) and the size OBTAINED (`0x0` = did not make
		 *     it).
		 * ⚠ The line is written here by the parent because it is the side that
		 *   decides: the child has already written its own, with the reason. */
		registro_dice(LOG_CHILD,
		              c.got_w && c.got_h
		                  ? "«%s»: the stage answers the canvas — asked %ux%u, "
		                    "OBTAINED %ux%u"
		                  : "«%s»: the stage did NOT make it on the canvas %ux%u "
		                    "(%ux%u): the client will know now instead of after "
		                    "the deadline of §7.1",
		              g->user, c.intended_w, c.intended_h, c.got_w, c.got_h);
		if (f->canvas)
			f->canvas(f->ctx, g->user, g->uid, c.intended_w, c.intended_h, c.got_w,
			        c.got_h);
		return true;
	}
	default:
		if (refused(f, g))
			registro_dice(LOG_CHILD, "⚠ «%s» sent a type I do not know (%u)",
			              g->user, t->kind);
		return true;
	}
}

/* ⛔ `REFUSED_STREAK_MAX` refused messages in a row and not one accepted: the
 *    child is sent away like the other violations.  Returns `false` when it
 *    is gone — and the caller MUST stop reading its descriptor. */
static bool refused_too_many(struct children *f, struct child *g)
{
	if (g->refused_streak < REFUSED_STREAK_MAX)
		return true;
	refusals_flush(g, f->round_ms, true);
	registro_dice(LOG_CHILD,
	              "⛔⛔ «%s» sent %u refused messages in a row and not one "
	              "accepted: our own child never writes one.  It is not a stage, "
	              "it is a flood running as that user: the child is killed",
	              g->user, g->refused_streak);
	if (g->pid > 0)
		child_signal(f, g, SIGKILL);
	child_dismiss(f, g, "sent only refused messages");
	return false;
}

/* ⭐ The clock of a round's share (`ROUND_NS_MAX`): monotonic, in ns. */
static uint64_t round_clock_ns(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

void children_move(children *f, struct pollfd *fds, size_t n, uint64_t now_ms)
{
	if (!f)
		return;
	f->round_ms = now_ms;

	/* ⭐ FORWARDING THE TRIGGER — the parent photographs nothing: it only
	 *    knows where the children are, and there the pixels are.
	 *
	 * ⛔ And the forwarding exists for a precise reason, not for elegance: the
	 *    child runs with the user's uid and whoever diagnoses is not that
	 *    user; the only road without a password is
	 *    `systemctl kill --kill-whom=main`, which delivers the signal TO THE
	 *    PARENT ONLY.  ⚠ The `--kill-whom=all` road would also deliver to
	 *    `gnome-shell`, for which `SIGUSR1` means "die": it would shut down the
	 *    very scene one wanted to photograph. */
	/* ⭐ 1.5: the children are the root side's, not ours to signal. */
	if (shot_to_forward && f->remote)
		shot_to_forward = 0;
	if (shot_to_forward) {
		int which = shot_to_forward == 2 ? SIGUSR2 : SIGUSR1;

		shot_to_forward = 0;
		for (int i = 0; i < f->cap; i++) {
			struct child *g = &f->v[i];

			if (!g->used || g->exiting || g->pid <= 0)
				continue;
			kill(g->pid, which);
			registro_dice(LOG_CHILD,
			              "⭐ trigger: %s forwarded to the child of «%s» (pid %ld)",
			              which == SIGUSR2 ? "SIGUSR2" : "SIGUSR1", g->user,
			              (long)g->pid);
		}
	}

	for (int i = 0; i < f->cap; i++) {
		struct child *g = &f->v[i];
		bool readable = false;

		if (!g->used)
			continue;

		for (size_t k = 0; k < n; k++)
			if (fds[k].fd == g->fd && (fds[k].revents & (POLLIN | POLLHUP)))
				readable = true;

		/* ⛔ The summary of the refusals only counted, once their window
		 *    has passed — even if this child has gone quiet since. */
		refusals_flush(g, now_ms, false);

		/* ⛔ This child's share of the round: `ROUND_MSGS_MAX` messages or
		 *    `ROUND_NS_MAX`, then the next one (see the box at the top).
		 *    ⚠ What stays queued is read at the next round: `poll` wakes again
		 *    at once for it. */
		uint64_t round_start_ns = readable ? round_clock_ns() : 0;
		int round_msgs = 0;

		while (readable) {
			if (round_msgs >= ROUND_MSGS_MAX
			    || (round_msgs > 0
			        && round_clock_ns() - round_start_ns >= ROUND_NS_MAX))
				break;
			round_msgs++;
			uint8_t envelope[MAX_ENVELOPE];
			struct head t;
			struct ucred chi;
			bool c_e = false;
			char why[256];
			ssize_t readings = receive_with_credentials(g->fd, envelope, sizeof envelope,
			                                       &chi, &c_e);

			if (readings == 0) {
				child_dismiss(f, g, "closed the socket (or died)");
				break;
			}
			if (readings == -2) {
				/* ⛔ Before `errno`, and not after: `-2` is a fact of OURS
				 *    (message truncated by the kernel) and `errno` at that
				 *    point still carries the outcome of something else. */
				if (refused(f, g))
					registro_dice(LOG_CHILD,
					              "⛔ «%s» sent a message longer than "
					              "expected: DISCARDED",
					              g->user);
				if (!refused_too_many(f, g))
					break;
				continue;
			}
			if (readings < 0) {
				if (errno == EINTR)
					continue;
				if (errno == EAGAIN || errno == EWOULDBLOCK)
					break;
				child_dismiss(f, g, strerror(errno));
				break;
			}
			if ((size_t)readings < sizeof t) {
				if (refused(f, g))
					registro_dice(LOG_CHILD,
					              "⛔ «%s»: message of %zd bytes, too short for "
					              "a header: DISCARDED",
					              g->user, readings);
				if (!refused_too_many(f, g))
					break;
				continue;
			}
			memcpy(&t, envelope, sizeof t);
			if (!magic_ok(&t)) {
				if (refused(f, g))
					registro_dice(LOG_CHILD,
					              "⛔ «%s»: message without the signature of this "
					              "protocol: DISCARDED",
					              g->user);
				if (!refused_too_many(f, g))
					break;
				continue;
			}
			/* ⛔⭐ AND HERE, BEFORE LOOKING AT A SINGLE BYTE OF THE BODY. */
			why[0] = 0;
			if (!credentials_match(g, &t, c_e, &chi, why,
			                            sizeof why)) {
				registro_dice(LOG_CHILD,
				              "⛔⛔ MESSAGE REFUSED from «%s»: %s.  ⚠ It is not "
				              "just a message to throw away: it is the link "
				              "between the RCP session and the child's identity that "
				              "can no longer be proven — and a child running as "
				              "the wrong user is I3 violated "
				              "invisibly.  The child is killed.",
				              g->user, why);
				if (g->pid > 0)
					child_signal(f, g, SIGKILL);
				child_dismiss(f, g, "the kernel's credentials did not match");
				break;
			}
			if ((size_t)readings < sizeof t + t.byte) {
				if (refused(f, g))
					registro_dice(LOG_CHILD,
					              "⛔ «%s»: the header announces %u body bytes and "
					              "%zd arrived: DISCARDED",
					              g->user, t.byte, readings - (ssize_t)sizeof t);
				if (!refused_too_many(f, g))
					break;
				continue;
			}
			g->refused_now = false;
			g->last_heard_ms = f->round_ms; /* a message that passed every wall: the child is alive and delivering */
			if (!handle(f, g, &t, envelope + sizeof t, t.byte))
				break;
			/* ⭐ An accepted message starts the streak again; a refused one
			 *    may have been the last allowed. */
			if (!g->refused_now)
				g->refused_streak = 0;
			else if (!refused_too_many(f, g))
				break;
		}

		if (!g->used)
			continue;

		/* ⛔⭐ THE DEAD ARE REAPED, AND IT IS NOT TIDINESS — `[M]` 12 Aug 2026,
		 *     from the helper: in `/proc` a zombie and a live process have **the
		 *     same face**, and a bench asking "is the child still alive?" would
		 *     get "yes" from a corpse.  ⛔ `WNOHANG`, because we are inside the
		 *     asynchronous loop (`CODER.md` §4.4). */
		if (g->pid > 0) {
			int state = 0;
			pid_t closed = child_reap(f, g, &state);
			if (closed == g->pid) {
				char said[160];
				say_how_it_ended(state, said, sizeof said);
				g->pid = 0;
				child_free(f, g, said);
				continue;
			}
			/* ⛔ And if it does not die, we insist — but only after having asked.
			 *    ⚠ A child that ignores `SIGTERM` while holding a user's virtual
			 *    monitor is an orphan in the making. */
			if (g->exiting && now_ms >= g->dismissed_ms + 3000) {
				/* ⛔ Review 4, finding 5: in network mode the death arrives as
				 *    the root side's CHILD_EXITED.  If that event never comes
				 *    (lost by a root side whose outbox was full), the slot
				 *    stayed «exiting» for ever.  ⇒ After EXITED_FALLBACK_ROUNDS
				 *    unanswered SIGKILLs (3 s apart) the slot is freed as exited.
				 *    Safe: if the child were still alive the root side would
				 *    refuse a new SPAWN for that uid, never make a second desktop. */
				if (f->remote && g->kill_rounds >= EXITED_FALLBACK_ROUNDS) {
					registro_dice(LOG_CHILD,
					              "⛔ the child of «%s» (serial %llu): no CHILD_EXITED "
					              "from the root side %d s after the farewell and %d "
					              "SIGKILL — the slot is freed as exited",
					              g->user, (unsigned long long)g->serial,
					              3 * (EXITED_FALLBACK_ROUNDS + 1), g->kill_rounds);
					g->pid = 0;
					child_free(f, g, "no CHILD_EXITED from the root side: treated as exited");
					continue;
				}
				/* ⭐ sigchld.h: with the reaping driven by SIGCHLD this child may already be dead and simply not looked at yet: one
				 *    waitpid() (not held) before the line and the kill — a corpse is collected, not «insisted upon». */
				if (!f->remote) {
					int late = 0;
					if (waitpid(g->pid, &late, WNOHANG) == g->pid) {
						char said[160];
						say_how_it_ended(late, said, sizeof said);
						g->pid = 0;
						child_free(f, g, said);
						continue;
					}
				}
				registro_dice(LOG_CHILD,
				              "⛔ the child of «%s» (pid %ld) did not die within 3 s "
				              "of the farewell: SIGKILL",
				              g->user, (long)g->pid);
				child_signal(f, g, SIGKILL);
				g->dismissed_ms = now_ms;
				g->kill_rounds++;
			}
			/* ⚠ And while it is leaving nothing more is asked of it: the slot
			 *   stays its own until the kernel confirms. */
			if (g->exiting)
				continue;
		}

		/* ⛔ The deadline of the INTRODUCTION, and only that one.  ⚠ After it,
		 *    none: I4 — the stage outlives the detach, and a silent child is a
		 *    child nobody is asking anything. */
		if (!g->showed_up && now_ms >= g->born_ms + SHOW_UP_DEADLINE_MS) {
			registro_dice(LOG_CHILD,
			              "⛔ the child of «%s» (pid %ld) did not say who it is within "
			              "%d ms: killing it.  A process running as a "
			              "user that does not answer is not a stage",
			              g->user, (long)g->pid, SHOW_UP_DEADLINE_MS);
			if (g->pid > 0)
				child_signal(f, g, SIGKILL);
			/* ⚠ No waiting here: the reaping belongs to the next round. */
			child_dismiss(f, g, "did not introduce itself in time");
		}
	}
}

/* ⛔ The minute timer: `RECHECK_MS`, defined at the top. */
void children_recheck(children *f, uint64_t now_ms)
{
	if (!f)
		return;
	for (int i = 0; i < f->cap; i++) {
		struct child *g = &f->v[i];
		struct head t;

		if (!g->used || g->fd < 0 || g->exiting)
			continue;
		/* ⛔⭐ THE NAME is NOT looked up here any more (candidate `nss-fuori`): `getpwnam_r()` blocks on sssd/LDAP, and
		 *     this is the loop that delivers every user's video.  The «who are you» question below carries the check:
		 *     the child looks its own name up and answers it in `body_whoami.name_check` (see `handle()`, MSG_INTRO). */
		if (!g->showed_up)
			continue;
		/* ⭐ The question that nobody answers (see WHOAMI_DEADLINE_MS) */
		if (g->whoami_asked_ms && now_ms >= g->whoami_asked_ms + WHOAMI_DEADLINE_MS) {
			if (g->last_heard_ms > g->whoami_asked_ms) {
				registro_dice(LOG_CHILD,
				              "⚠ the child of «%s» (pid %ld) has not answered the «who are you» question for %d s but is still sending "
				              "messages: it is NOT killed",
				              g->user, (long)g->pid, WHOAMI_DEADLINE_MS / 1000);
				g->whoami_asked_ms = now_ms;
			} else {
				registro_dice(LOG_CHILD,
				              "⛔ the child of «%s» (pid %ld) has not answered the «who are you» question for %d s and sent nothing at all: "
				              "its loop is stuck. SIGKILL",
				              g->user, (long)g->pid, WHOAMI_DEADLINE_MS / 1000);
				if (g->pid > 0)
					child_signal(f, g, SIGKILL);
				child_dismiss(f, g, "did not answer the «who are you» question");
				continue;
			}
		}
		if (now_ms < g->last_recheck_ms + RECHECK_MS)
			continue;
		g->last_recheck_ms = now_ms;
		/* ⚠ The wait is armed when the question is ASKED, even if it does not go out: a child that does not even empty its socket is stuck too */
		if (!g->whoami_asked_ms)
			g->whoami_asked_ms = now_ms;

		memset(&t, 0, sizeof t);
		magic_write(&t);
		t.kind = MSG_CHI_SEI;
		t.version = CHILD_VERSION;
		t.serial = g->serial;
		t.declared_uid = (uint32_t)g->uid;
		t.byte = 0;
		/* ⚠ If the question does not go out nothing is concluded: the absence
		 *   of an answer is not an answer, and the child stays where it is.
		 *   ⛔ What is NOT done is inferring from an `EAGAIN` that the child
		 *   is dead. */
		if (send(g->fd, &t, sizeof t, MSG_NOSIGNAL) != (ssize_t)sizeof t)
			log_detail(LOG_CHILD,
			                   "the «who are you» question to «%s» did not go out (%s): "
			                   "retrying in a minute",
			                   g->user, strerror(errno));
	}
}

bool children_ask_stage(children *f, const char *user)
{
	struct child *g;
	struct head t;

	if (!f || !user)
		return false;
	g = search(f, user);
	if (!g || g->fd < 0 || g->exiting)
		return false;
	memset(&t, 0, sizeof t);
	magic_write(&t);
	t.kind = MSG_RESEND_STAGE;
	t.version = CHILD_VERSION;
	t.serial = g->serial;
	t.declared_uid = (uint32_t)g->uid;
	if (send(g->fd, &t, sizeof t, MSG_NOSIGNAL) != (ssize_t)sizeof t) {
		registro_dice(LOG_CHILD,
		              "⚠ the stage request to «%s» did not go out (%s): "
		              "that session will see nothing, and this line is the "
		              "reason",
		              user, strerror(errno));
		return false;
	}
	registro_dice(LOG_CHILD,
	              "asked «%s» to send its stage again: the process deposit "
	              "belongs to whoever has just passed PAM",
	              user);
	return true;
}

/* ⛔⭐ PHASE 3 — "CAPTURE, AND THIS ONE MUST BE A KEYFRAME".
 *
 *     It is the parent half of the seam that was missing.  ⚠ The one who
 *     decides is not this file — it knows nothing about RCP sessions — but
 *     `webtransport.c`, which knows when `SESSION` went out and when §5.2
 *     wants a keyframe.  `main.c` acts as the bridge, because it is the only
 *     one that knows both.
 *
 * ⛔ AND THE REQUEST IS REPEATED EVEN IF THE CODEC DOES NOT CHANGE, when the
 *    keyframe is asked for: a keyframe asked twice costs one big frame, a
 *    keyframe asked zero times costs **the screen frozen forever**.  The
 *    deadline that avoids the burst is on the other side
 *    (`WT_KEY_REQUEST_MS`), where the session's clock is. */
/* ⭐⭐ PHASE 4 — the PARENT half of the input seam.
 *
 * ⚠ How short it is, and why it is right that it is: nothing is validated
 *   and nothing is transformed here.  `rcp.c` has already applied `RCP.md`
 *   §7.3 in full — ranges, surrogates, coordinates on the canvas, increasing
 *   `id` — and `input.c` will apply the compositor's rules.  ⛔ One more check
 *   in the middle is not caution: it is a **third** rule that, the day one of
 *   the two changes, silently stays behind.
 *
 * ⛔ And NO state is kept: no "last id sent", no cache of what is pressed.
 *    The one keeping count is `input.c`, which is the only one that knows
 *    what the compositor really took — and two counters on the same quantity
 *    are two truths that diverge at the first lost message. */
/* ⭐⭐ §5-bis.7 — "PUT THIS LAYOUT IN THE SESSION".
 *
 * ⛔ The defect this function closes, measured by bench `06-b34` on
 *    16 Aug 2026: the layout declared in `ATTACH` was validated and WRITTEN
 *    IN THE LOG, and that was the end of it.  Reattaching to an `it` session
 *    declaring `us`, `è` and `ò` arrived, which on `us` do not exist on any
 *    key.
 *
 * ⭐ And the real damage is not the accent: shortcuts travel as POSITIONS
 *    (`SPECS.md` §7.3), and on a German keyboard `Z` sits where `Y` sits
 *    for us — without renegotiating, `Ctrl+Z` arrives as `Ctrl+Y`, that is
 *    "redo" instead of "undo". */
bool children_layout(children *f, const char *user, const char *name)
{
	struct child *g;
	struct head t;
	struct body_layout c;
	uint8_t envelope[sizeof t + sizeof c];

	if (!f || !user || !name || !*name)
		return false;
	g = search(f, user);
	if (!g || g->fd < 0 || g->exiting)
		return false;

	memset(&t, 0, sizeof t);
	magic_write(&t);
	t.kind = MSG_LAYOUT;
	t.version = CHILD_VERSION;
	t.serial = g->serial;
	t.declared_uid = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	snprintf(c.name, sizeof c.name, "%s", name);
	memcpy(envelope, &t, sizeof t);
	memcpy(envelope + sizeof t, &c, sizeof c);
	if (send(g->fd, envelope, sizeof envelope, MSG_NOSIGNAL) != (ssize_t)sizeof envelope) {
		/* ⛔ `registro_dice` and not `detail`: it happens once per attach,
		 *    and if it does not go out the user is left with misaligned
		 *    shortcuts — which is precisely the fault nobody connects. */
		registro_dice(LOG_CHILD,
		              "⚠ the layout «%s» for «%s» did NOT go out: the "
		              "session keeps its own, and the shortcuts will stay "
		              "misaligned",
		              name, user);
		return false;
	}
	return true;
}

bool children_pace(children *f, const char *user, uint16_t max_fps)
{
	struct child *g;
	struct head t;
	struct body_pace c;
	uint8_t envelope[sizeof t + sizeof c];

	if (!f || !user)
		return false;
	g = search(f, user);
	if (!g || g->fd < 0 || g->exiting)
		return false;

	memset(&t, 0, sizeof t);
	magic_write(&t);
	t.kind = MSG_PACE;
	t.version = CHILD_VERSION;
	t.serial = g->serial;
	t.declared_uid = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.max_fps = max_fps;
	memcpy(envelope, &t, sizeof t);
	memcpy(envelope + sizeof t, &c, sizeof c);
	if (send(g->fd, envelope, sizeof envelope, MSG_NOSIGNAL) != (ssize_t)sizeof envelope) {
		registro_dice(LOG_CHILD,
		              "⚠ the pace %u/s for «%s» did NOT go out (%s): the stage "
		              "keeps its rate",
		              (unsigned)max_fps, user, strerror(errno));
		return false;
	}
	return true;
}

bool children_input(children *f, const char *user, uint32_t id, uint8_t action,
                 uint16_t code, int pressed, int32_t a, int32_t b)
{
	struct child *g;
	struct head t;
	struct body_input c;
	uint8_t envelope[sizeof t + sizeof c];

	if (!f || !user)
		return false;
	g = search(f, user);
	if (!g || g->fd < 0 || g->exiting)
		return false;

	memset(&t, 0, sizeof t);
	magic_write(&t);
	t.kind = MSG_INPUT;
	t.version = CHILD_VERSION;
	t.serial = g->serial;
	t.declared_uid = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.id = id;
	c.action = action;
	c.pressed = pressed ? 1u : 0u;
	c.code = code;
	c.a = a;
	c.b = b;
	memcpy(envelope, &t, sizeof t);
	memcpy(envelope + sizeof t, &c, sizeof c);
	if (send(g->fd, envelope, sizeof envelope, MSG_NOSIGNAL) != (ssize_t)sizeof envelope) {
		/* ⛔ `log_detail` and not `registro_dice`: a user moving the
		 *    mouse produces dozens of messages per second, and one line for
		 *    each would bury the log precisely when it needs to be read.
		 *    ⚠ But it is NOT silenced: "the input did not reach the desktop"
		 *    is a fact, and it disappears only from the chatter. */
		log_detail(LOG_CHILD,
		                   "⚠ input %u (action %u) for «%s» did not go out "
		                   "(%s): that gesture did NOT reach the desktop",
		                   (unsigned)id, (unsigned)action, user,
		                   strerror(errno));
		return false;
	}
	return true;
}

/* ⭐⭐ THE MISSING CHAIN — `children_recanvas()`, and from here on the name that
 *     `DECISIONS.md` §5.0-sexies and the mandate of phase 4 mention EXISTS.
 *
 * ⛔ IT IS ONE LINE AND IT DELEGATES, and both things are on purpose: the
 *    message on the wire between parent and child stays **one** (`MSG_INPUT`,
 *    action `RITELA`), so in the child there is only one branch to read.
 *    ⚠ A second envelope would have needed a second `struct corpo_*`, a second
 *    branch and a second way to get it wrong — to carry two numbers that the
 *    existing one already carries.
 *
 * ⛔ BUT THE NAME IS NOT COSMETIC, and it is not `children_input()` with a strange
 *    action: input is a GESTURE already validated by §7.3 that is injected and
 *    forgotten; this is a request to **reconfigure the stage** whose outcome
 *    does not come back from here — it comes back with a frame, minutes later
 *    or never.  Two different jobs with two different names, and whoever
 *    reads `main.c` sees the whole chain.
 *
 * `false` = there is no child for that user, or the request did not go out
 * — ⛔ and then the canvas will NOT change, which is declared instead of
 * waiting for a frame that will not arrive (`CODER.md` §4.2). */
bool children_recanvas(children *f, const char *user, uint32_t width,
                  uint32_t height)
{
	/* ⛔ `id = 0` and not the last input id: §6.2 reserves zero for "no
	 *    input", and this is not a user action on which the latency link
	 *    should measure anything. */
	return children_input(f, user, 0, CHILDREN_INPUT_RECANVAS, 0, 0,
	                   (int32_t)width, (int32_t)height);
}

/* ⭐ §7.6 — and it delegates to `children_input()` like `children_recanvas()`, for the
 * same reason: a single envelope on the wire between parent and child.  ⛔ But
 * with its own name, because the jobs are two and whoever reads `main.c` must
 * see the chain. */
void children_hook_canvas_wait(children *f, ChildCanvasWait fn, void *ctx)
{
	if (!f)
		return;
	f->on_canvas_wait = fn;
	f->ctx_canvas_wait = ctx;
}

void children_hook_block(children *f, ChildBlock fn, void *ctx)
{
	if (!f)
		return;
	f->on_block = fn;
	f->ctx_block = ctx;
}

void children_hook_clipboard(children *f, ChildClipboardText text,
                          ChildClipboardRequest request, void *ctx)
{
	if (!f)
		return;
	/* ⛔ Together or not at all (`child.h`): whoever hooked only `text`
	 *    could carry to the client what the session copies and could not
	 *    needs whoever pastes — and that "could not" shows up as a frozen
	 *    desktop.  ⇒ It is declared and nothing is hooked, instead of hooking
	 *    half a channel. */
	if ((text != NULL) != (request != NULL)) {
		registro_dice(LOG_CHILD,
		              "⛔ the two clipboard hooks are attached together or not "
		              "at all, and only one arrived (%s): I am attaching "
		              "neither",
		              text ? "the one serving whoever pastes is missing"
		                    : "the one carrying the text to the client is missing");
		return;
	}
	f->on_clipboard_text = text;
	f->on_clipboard_request = request;
	f->ctx_clipboard = ctx;
}

bool children_clipboard_offer(children *f, const char *user)
{
	struct child *g;
	struct head t;
	uint8_t envelope[sizeof t];

	if (!f || !user)
		return false;
	g = search(f, user);
	if (!g || g->fd < 0 || g->exiting)
		return false;

	memset(&t, 0, sizeof t);
	magic_write(&t);
	t.kind = MSG_CLIPBOARD_OFFER;
	t.version = CHILD_VERSION;
	t.serial = g->serial;
	t.declared_uid = (uint32_t)g->uid;
	t.byte = 0;
	memcpy(envelope, &t, sizeof t);
	if (send(g->fd, envelope, sizeof envelope, MSG_NOSIGNAL) != (ssize_t)sizeof envelope) {
		registro_dice(LOG_CHILD,
		              "⚠ the clipboard offer to «%s» did not go out (%s): "
		              "inside that session it will not be possible to paste what "
		              "the client copied, and this line is the reason",
		              user, strerror(errno));
		return false;
	}
	log_detail(LOG_CHILD,
	                   "«%s»: the client's text offered to the session (§7.4)",
	                   user);
	return true;
}

bool children_clipboard_response(children *f, const char *user, uint32_t serial,
                            const char *text, size_t byte)
{
	struct child *g;
	size_t off = 0;

	if (!f || !user)
		return false;
	g = search(f, user);
	if (!g || g->fd < 0 || g->exiting)
		return false;

	/* ⛔ The cap is enforced in THIS direction too, and the reason is
	 *    different from that of §5.4: here the text comes from the **client**,
	 *    that is from outside.  ⚠ `rcp.c` has already refused it on the wire;
	 *    this is the second door, the one protecting the child from a parent
	 *    with a defect. */
	if (text && byte > CLIPBOARD_CAP) {
		registro_dice(LOG_CHILD,
		              "⛔ «%s»: %zu bytes of clipboard from the client, over the cap "
		              "of §5.4 (%u): answering «I don't have it» instead of truncating",
		              user, byte, CLIPBOARD_CAP);
		text = NULL;
		byte = 0;
	}

	/* ⛔ The "nothing" case and the "empty text" case go down different roads,
	 *    and the difference reaches Mutter: `SelectionWriteDone(false)` versus
	 *    a descriptor opened and closed without bytes.  ⚠ Whoever pastes sees
	 *    "there was nothing to paste" in the first case and an empty line in
	 *    the second, which are two different things. */
	do {
		struct head t;
		struct body_clipboard c;
		uint8_t envelope[sizeof t + sizeof c + MAX_PIECE];
		size_t q = 0;

		if (text) {
			q = byte - off;
			if (q > MAX_PIECE)
				q = MAX_PIECE;
		}

		memset(&t, 0, sizeof t);
		magic_write(&t);
		t.kind = MSG_CLIPBOARD_FROM_CLIENT;
		t.version = CHILD_VERSION;
		t.serial = g->serial;
		t.declared_uid = (uint32_t)g->uid;
		t.byte = (uint32_t)(sizeof c + q);
		memset(&c, 0, sizeof c);
		c.serial = serial;
		c.total = text ? (uint32_t)byte : 0;
		c.offset = (uint32_t)off;
		c.piece = (uint32_t)q;
		c.nothing = text ? 0 : 1;
		memcpy(envelope, &t, sizeof t);
		memcpy(envelope + sizeof t, &c, sizeof c);
		if (q)
			memcpy(envelope + sizeof t + sizeof c, text + off, q);
		ssize_t sent = send(g->fd, envelope, sizeof t + sizeof c + q, MSG_NOSIGNAL);
		explicit_bzero(envelope, sizeof t + sizeof c + q);
		if (sent != (ssize_t)(sizeof t + sizeof c + q)) {
			/* ⛔⛔ AND THIS IS THE CASE THAT LEAVES THE PASTER HANGING, so the
			 *      line is plain and says the symptom: without it, the defect
			 *      would be sought in the desktop instead of in a full socket. */
			registro_dice(LOG_CHILD,
			              "⛔ «%s»: the clipboard answer (request %u, %zu "
			              "of %zu bytes) did not go out (%s).  ⚠ The application "
			              "that is pasting stays hanging until the child "
			              "reaches the end of its timeout",
			              user, serial, off, byte, strerror(errno));
			return false;
		}
		off += q;
	} while (text && off < byte);

	log_detail(LOG_CHILD,
	                   "«%s»: clipboard answer (request %u) — %s",
	                   user, serial,
	                   text ? "delivered" : "«I don't have it»");
	return true;
}

void children_hook_session_finished(children *f, ChildSessionFinished fn, void *ctx)
{
	if (!f)
		return;
	f->on_session_finished = fn;
	f->ctx_session_finished = ctx;
}

bool children_terminate_session(children *f, const char *user, int why)
{
	/* ⛔ The `why` travels in field `a`, which was free: the reason is on
	 *    `FIGLI_USCITA_*` in `child.h`. */
	if (!children_input(f, user, 0, CHILDREN_INPUT_TERMINATE, 0, 0, why, 0))
		return false;
	/* ⛔ From here the desktop is closing: a login now gets «retry», not a
	 *    desktop about to vanish (`children_alive_of()`). */
	struct child *g = search(f, user);
	if (g)
		g->closing_asked_ms = log_now_ms() ? log_now_ms() : 1;
	return true;
}

bool children_audio(children *f, const char *user, uint8_t codec)
{
	struct child *g;
	struct head t;
	struct body_audio c;
	uint8_t envelope[sizeof t + sizeof c];

	if (!f || !user)
		return false;
	g = search(f, user);
	if (!g || g->fd < 0 || g->exiting)
		return false;
	/* ⛔⭐ AND WITH THE CODEC UNCHANGED THE MESSAGE GOES OUT ANYWAY, if the codec
	 *     is not zero — and it is INVARIANT I5, not an oversight.
	 *
	 *     "The volume belongs to the session: whoever connects finds it at
	 *     maximum."  ⚠ With the "nothing new to say" shortcut the second one
	 *     to connect would send nothing, and would find the volume where the
	 *     first had left it — that is a state that **the client can neither
	 *     see nor explain**, which is the reason I5 exists.
	 *
	 * ⚠ The price is an eight-byte message per attach: it is paid once per
	 *   connection, not per block. */
	if (codec == g->requested_audio_codec && codec == 0)
		return true; /* off, and stays off: there is nothing to say */

	memset(&t, 0, sizeof t);
	magic_write(&t);
	t.kind = MSG_AUDIO;
	t.version = CHILD_VERSION;
	t.serial = g->serial;
	t.declared_uid = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.codec = codec;
	memcpy(envelope, &t, sizeof t);
	memcpy(envelope + sizeof t, &c, sizeof c);
	if (send(g->fd, envelope, sizeof envelope, MSG_NOSIGNAL) != (ssize_t)sizeof envelope) {
		registro_dice(LOG_CHILD,
		              "⚠ the audio request to «%s» (codec %u) did not go out "
		              "(%s): that session will hear nothing, and this line "
		              "is the reason",
		              user, codec, strerror(errno));
		return false;
	}
	registro_dice(LOG_CHILD,
	              codec ? "⭐ PHASE 7: asked the session of «%s» to "
	                      "capture audio, codec %u (%s)"
	                    : "asked the session of «%s» to STOP "
	                      "capturing audio (codec %u): nobody is listening "
	                      "any more, and the sink stays up (I4)",
	              user, codec,
	              codec == 1 ? "Opus" : codec == 2 ? "PCM" : "-");
	g->requested_audio_codec = codec;
	return true;
}

bool children_video(children *f, const char *user, uint8_t codec,
                 uint8_t depth, uint8_t livello_x10, bool key)
{
	struct child *g;
	struct head t;
	struct body_video c;
	uint8_t envelope[sizeof t + sizeof c];

	if (!f || !user)
		return false;
	g = search(f, user);
	if (!g || g->fd < 0 || g->exiting)
		return false;
	/* ⛔ And the depth enters the comparison: a second client negotiating 8
	 *    bits where the first had 10 is "something new to say", even if the
	 *    codec is the same.  ⚠ Without this line the message would not go
	 *    out, and the stream would stay at the depth of the FIRST — that is
	 *    exactly the lie this field exists to remove. */
	/* ⛔ And the LEVEL enters the comparison for the same reason as the depth
	 *    (§4.3, 23 Aug 2026): a second client declaring 4.1 where the first
	 *    had 5.1 changes neither codec nor depth, and without this line the
	 *    message would not go out — the stream would stay at the ceiling of
	 *    the FIRST and the second would see a mute black screen. */
	if (codec == g->requested_video_codec && depth == g->video_profile_requested
	    && livello_x10 == g->video_level_requested && !key)
		return true; /* nothing new to say */

	memset(&t, 0, sizeof t);
	magic_write(&t);
	t.kind = MSG_VIDEO;
	t.version = CHILD_VERSION;
	t.serial = g->serial;
	t.declared_uid = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.codec = codec;
	c.key = key ? 1u : 0u;
	c.depth = depth;
	c.livello_x10 = livello_x10;
	memcpy(envelope, &t, sizeof t);
	memcpy(envelope + sizeof t, &c, sizeof c);
	if (send(g->fd, envelope, sizeof envelope, MSG_NOSIGNAL) != (ssize_t)sizeof envelope) {
		registro_dice(LOG_CHILD,
		              "⚠ the video request to «%s» (codec %u, keyframe %s) did "
		              "not go out (%s): that session will see nothing, and "
		              "this line is the reason",
		              user, codec, key ? "YES" : "no", strerror(errno));
		return false;
	}
	if (codec != g->requested_video_codec)
		registro_dice(LOG_CHILD,
		              codec ? "⭐ PHASE 3: asked the stage of «%s» to "
		                      "capture continuously, codec %u%s"
		                    : "asked the stage of «%s» to STOP "
		                      "capturing (codec %u): nobody is watching it "
		                      "any more%s",
		              user, codec, key ? " — and the first must be a "
		                                      "KEYFRAME (§5.2)" : "");
	g->requested_video_codec = codec;
	g->video_profile_requested = depth;
	g->video_level_requested = livello_x10;
	return true;
}

/* ⭐ 1.5 (DECISIONS-11 §11.4): the card grants (`render_grant.h`) of the desktops that SURVIVE the
 *   shutdown of the service are LEFT IN PLACE here — this function does not call `child_free()`,
 *   so it takes none back.  The desktop lives on without a child (`rediscover.h`), is found again
 *   at the next start, and `render_grant_sweep()` keeps its grant ("KEPT", no child) or takes it
 *   back once the desktop is gone.  Uninstalling removes what is left. */
/* ⭐ 1.5: how long `children_turn_off()` waits for one child's CHILD_EXITED;
 *    the root side waits 5 s for the whole network side (§11.50). */
#define TURN_OFF_WAIT_MS 1500
/* ⭐ Audit of the session (25 Oct 2026): in single-process mode the wait was `waitpid(pid, NULL, 0)`, WITHOUT a limit; now SIGTERM, the same
 *    TURN_OFF_WAIT_MS, then SIGKILL and TURN_OFF_KILL_WAIT_MS more (reapwait.h).  A child still not reaped after that is said and left to init. */
#define TURN_OFF_KILL_WAIT_MS 1000

static bool child_reaped_now(void *ctx)
{
	return ((const struct child *)ctx)->reaped;
}

void children_turn_off(children *f)
{
	if (!f)
		return;
	for (int i = 0; i < f->cap; i++) {
		struct child *g = &f->v[i];
		bool left_to_init = false;
		if (!g->used)
			continue;
		/* ⛔ First the socket is closed — which is the most honest signal,
		 *    "there is nobody left to talk to" — and then we insist with the
		 *    signal. */
		if (g->fd >= 0) {
			close(g->fd);
			g->fd = -1;
		}
		if (g->pid > 0) {
			child_signal(f, g, SIGTERM);
			/* ⚠ It WAITS, and it is outside the `poll` loop: `CODER.md` §4.4
			 *   forbids waiting INSIDE the loop, and this is the line after the
			 *   last round.  ⛔ The stage must be dismantled before the process
			 *   exits, or the virtual monitor would stay attached to the user's
			 *   session.
			 * ⭐ 1.5: in network mode the wait is for the root side's
			 *    CHILD_EXITED, at most `TURN_OFF_WAIT_MS` per child. */
			if (f->remote) {
				rootside_pump_until(child_reaped_now, g, TURN_OFF_WAIT_MS);
			} else if (!reap_within(g->pid, TURN_OFF_WAIT_MS)) {
				registro_dice(LOG_CHILD, "⛔ the child of «%s» (pid %ld) did not die within %d ms of the SIGTERM: SIGKILL",
				              g->user, (long)g->pid, TURN_OFF_WAIT_MS);
				child_signal(f, g, SIGKILL);
				if (!reap_within(g->pid, TURN_OFF_KILL_WAIT_MS)) {
					registro_dice(LOG_CHILD, "⛔ the child of «%s» (pid %ld) is STILL not reaped %d ms after the SIGKILL "
					              "(a call that does not return?): the shutdown goes on without it",
					              g->user, (long)g->pid, TURN_OFF_KILL_WAIT_MS);
					left_to_init = true; /* said below as «not shut down» */
				}
			}
		}
		/* review 4 B, finding 17: «shut down» only when it is known */
		if (left_to_init)
			registro_dice(LOG_CHILD, "⚠ the child of «%s» (pid %ld) is not confirmed shut down: left to init", g->user, (long)g->pid);
		else if (f->remote && g->pid > 0 && !child_reaped_now(g))
			registro_dice(LOG_CHILD, "⚠ the child of «%s» (pid %ld): no CHILD_EXITED "
			              "within %d ms of the SIGTERM — this side leaves it to the "
			              "root side", g->user, (long)g->pid, TURN_OFF_WAIT_MS);
		else
			registro_dice(LOG_CHILD, "the child of «%s» (pid %ld) is shut down",
			              g->user, (long)g->pid);
		if (g->app_mount)
			explicit_bzero(g->app_mount, g->app_total);
		free(g->app_mount);
		free(g->assembly);
		free(g->cur_mount);
		memset(g, 0, sizeof *g);
		g->fd = -1;
	}
	free(f->v);
	free(f);
}

/* ========================================================================== */
/* ⭐ THE CHILD — from here down we run as the user, and there is no going back */

/* ⭐⭐ PHASE 4 — the input channel lives HERE, and it could not live elsewhere:
 *     `libei` talks to the graphical session, and the graphical session
 *     belongs to this process.
 *
 * ⛔ `input_injected` is the `id` of the last input the COMPOSITOR TOOK — not
 *    the last received, not the last attempted.  §6.2 promises that "the
 *    effect of that input is already in the scene", and of a refused input
 *    there is no effect to see.  ⇒ It advances only when `input.c` has
 *    answered 0. */
static Input *stage_input;
/* ⭐ §5-bis.7: the layout requested when the stage was not there yet.
 *    ⛔ Empty = nothing pending.  It is applied as soon as `input_open()`
 *    succeeds. */
static char pending_layout[65];
static uint32_t input_injected;
static uint32_t input_refused;
static uint32_t input_unproducible;
/* ⭐ 24 Sep 2026 — where the pointer is, for the shape PROBE on labwc
 *    (`capture_probe_pointer`): a button carries no coordinates, but it can
 *    change the shape (grabbing the title bar), and it is probed here. */
static uint32_t probe_x, probe_y;
static bool probe_note;

/* ⭐⭐ PHASE 7 — THE SESSION'S CLIPBOARD, and it lives on this side for the
 *     same reason as `stage_input`: the clipboard belongs to the compositor,
 *     and this process is the one talking to the compositor
 *     (`src/clipboard.h`). */
static Clipboard *stage_clipboard;

/* ⭐ PHASE 12, INCREMENT 2 — the stage on KDE.  On GNOME it stays NULL and
 *    the `MutterSession` does everything as before; on KDE `mut` stays NULL
 *    and the PipeWire node is given by KWin (`kwin.h`).  ⚠ One per child, like
 *    the other two above: a child has only one stage. */
static KwinSession *stage_kwin;

static void close_stage_kwin(void)
{
	if (stage_kwin) {
		kwin_close(stage_kwin);
		stage_kwin = NULL;
	}
}

/* The stage's PipeWire node, whoever it comes from. */
static uint32_t stage_node(const MutterSession *m)
{
	return m ? mutter_node(m) : kwin_node(stage_kwin);
}

/*
 * ⛔⭐ THE SIZE TO ASK OF THE CAPTURE, ON KDE, IS THAT OF KWIN'S OUTPUT.
 *
 * On GNOME Mutter makes a NEW monitor of the requested size (`RecordVirtual`).
 * On KDE the output `Virtual-0` is born with the session, at the size of the
 * FIRST client (increment 1, CP2), and KWin 6.3.6 does not resize it live
 * (`kwin!7932`, expected for 6.8 — `LESSONS.md` of v1).  `[M]` 18 Sep 2026:
 * asking 1384x912 of an output of 1388x914 ⇒ `no more input formats`, and the
 * stage NEVER mounts again — the session stays in the dark.
 * ⇒ On KDE the output is captured as it is, and the page rescales: that is
 *   what §4.5 of the protocol provides when the canvas granted is not the one
 *   requested.
 * On GNOME this function changes nothing.
 */
static void stage_size(uint32_t *l, uint32_t *a)
{
	uint32_t kl = 0, ka = 0;

	if (!stage_kwin)
		return;
	kwin_measure(stage_kwin, &kl, &ka);
	if (!kl || !ka || (kl == *l && ka == *a))
		return;
	registro_dice(LOG_CHILD,
	              "⚠ the requested canvas is %ux%u but KWin's output is %ux%u, and KWin "
	              "does not resize it: capturing %ux%u and the page rescales (§4.5)",
	              *l, *a, kl, ka, kl, ka);
	*l = kl;
	*a = ka;
}

/* ⛔⛔⭐ THE OFFER THAT ARRIVED TOO EARLY, AND IS REDONE — 21 Aug 2026, defect
 *      measured with bench `07-b56`.
 *
 * ⚠ The client announces its clipboard as soon as the `SESSION` is born; the
 *   graphical session's clipboard opens a few tens of milliseconds LATER,
 *   when Mutter has answered.  `[M]` Log of 06:00:15 — the announcement at
 *   .868, the opening at .982: 114 ms.
 *   ⛔ In between the offer fell («the session's clipboard is not there») and
 *     nobody ever redid it: the compositor did not become owner of the
 *     selection, and inside the desktop the menu's "Paste" item had nothing
 *     to give.  ⇒ From outside: "it does not work with the mouse".
 *
 * ⭐ It is remembered that it fell, and it is redone as soon as the channel is
 *    there.  It is the same form as the pending request of `rcp.c`
 *    (`clipboard_ask_backlog`): instead of delaying something for
 *    everyone, ONE bit is kept and the seam is stitched. */
static bool clipboard_pending_offer;

/*
 * ⛔⛔ THE TIMEOUT OF WHOEVER PASTES, AND IT LIVES IN THE CHILD — not in the parent.
 *
 * A `SelectionTransfer` without an answer leaves the pasting application
 * hanging **indefinitely**, and the symptom is "the desktop has frozen".
 * ⇒ Someone must always answer.
 *
 * ⭐ And that someone is THIS process, not the parent, for a reason that is
 *    not convenience: the parent may have no client attached (the session
 *    outlives the client — invariant I4), the client may vanish halfway
 *    through the transfer, and the parent itself may die.  ⛔ The debt towards
 *    Mutter instead stays with whoever has the session, and the session is
 *    here.
 *
 * ⚠ The parent answers AT ONCE when it already knows it cannot needs (no hook
 *   attached): this timeout covers the other case — the client is there and
 *   does not answer.
 */
#define CLIPBOARD_WAIT_MS 4000
#define CLIPBOARD_IN_FLIGHT 8
static struct {
	bool used;
	uint32_t serial;
	uint64_t expires_ms;
} clipboard_in_flight[CLIPBOARD_IN_FLIGHT];

static int fd_child = 3; /* the agreed place, put there by `become_and_exec` */
static uint64_t my_serial;
static uid_t my_uid;

/* How many descriptors I really have open.  ⛔ They are COUNTED, not
 * declared: it is the half of the bench that lives in the product — "the
 * child did not carry the port along" must be a number, not a promise. */
static uint32_t how_many_descriptors(void)
{
	uint32_t n = 0;
	for (int i = 0; i < 4096; i++)
		if (fcntl(i, F_GETFD) >= 0)
			n++;
	return n;
}

static bool send_msg(uint16_t kind, const void *body, size_t byte,
                  const void *queue, size_t byte_queue)
{
	uint8_t envelope[MAX_ENVELOPE];
	struct head t;
	size_t n = 0;

	if (sizeof t + byte + byte_queue > sizeof envelope)
		return false;
	memset(&t, 0, sizeof t);
	magic_write(&t);
	t.kind = kind;
	t.version = CHILD_VERSION;
	t.serial = my_serial;
	/* ⛔ The uid is ASKED OF THE KERNEL on every message, and not read from a
	 *    variable written at startup: the variable would say what we believed
	 *    we were, and the parent will compare this field with what the kernel
	 *    stamped.  ⚠ If the two did not match, the parent kills — and rightly
	 *    so: a child that no longer knows who it is must not deliver pixels. */
	t.declared_uid = (uint32_t)geteuid();
	t.byte = (uint32_t)(byte + byte_queue);
	memcpy(envelope, &t, sizeof t);
	n = sizeof t;
	if (byte) {
		memcpy(envelope + n, body, byte);
		n += byte;
	}
	if (byte_queue) {
		memcpy(envelope + n, queue, byte_queue);
		n += byte_queue;
	}
	return send(fd_child, envelope, n, MSG_NOSIGNAL) == (ssize_t)n;
}

/* ⛔⭐ THE CANVAS THE CLIENT ASKED FOR, kept apart from the one the stage
 *     GIVES.  They are two different numbers and needs two different things:
 *
 *       `tela_voluta_*`  what the client wants ⇒ it is what is requested on
 *                        REMOUNTING the stage, or the bands would come back
 *                        after every fall of the graphical session;
 *       `canvas_w`/`canvas_h` what the stage delivers ⇒ it is what ends up in the
 *                        28 bytes of §6.2, and it is not invented.
 *
 * ⚠ They are born equal (the size from the command line) and diverge at the
 *   first `FIT_CANVAS` that the compositor does not needs to the letter
 *   (§4.5). */
static uint32_t canvas_intended_w, canvas_intended_h;

/* The answer of §7.1 to the parent.  ⛔ `got_w == 0` = "I did not make it",
 * and it is a different fact from "I am trying": without this line the parent
 * would wait to the end of the three seconds to learn something known here at
 * once. */
/* ⭐ "WAIT": the stage is not there YET, and the question will get a real
 * answer.  ⛔ It is not `0x0` — that is "I did not make it" — and it is the
 *    message that takes an inference away from the parent (`LESSONS.md` §7.5). */
static void wait_canvas(uint32_t intended_w, uint32_t intended_h)
{
	struct body_canvas c;
	memset(&c, 0, sizeof c);
	c.intended_w = intended_w;
	c.intended_h = intended_h;
	c.should_wait = 1;
	if (!send_msg(MSG_CANVAS, &c, sizeof c, NULL, 0))
		registro_dice(LOG_CHILD,
		              "⛔ the «wait» on the canvas (%ux%u) did not go out (%s): the "
		              "parent will let the deadline of §7.1 expire on a question that "
		              "was about to get an answer",
		              intended_w, intended_h, strerror(errno));
}

static void reply_canvas(uint32_t intended_w, uint32_t intended_h, uint32_t got_w,
                          uint32_t got_h)
{
	struct body_canvas c;
	memset(&c, 0, sizeof c);
	c.intended_w = intended_w;
	c.intended_h = intended_h;
	c.got_w = got_w;
	c.got_h = got_h;
	if (!send_msg(MSG_CANVAS, &c, sizeof c, NULL, 0))
		registro_dice(LOG_CHILD,
		              "⛔ the answer on the canvas (%ux%u → %ux%u) did not go out "
		              "(%s): the parent will wait for the deadline of §7.1 instead of "
		              "knowing it now",
		              intended_w, intended_h, got_w, got_h, strerror(errno));
}

static void send_frame(uint8_t codec, bool key, uint32_t l, uint32_t a,
                             uint64_t instant_us, const uint8_t *data, size_t byte,
                             uint32_t input)
{
	size_t off = 0;
	while (off < byte) {
		struct body_frame c;
		size_t q = byte - off;
		if (q > MAX_PIECE)
			q = MAX_PIECE;
		memset(&c, 0, sizeof c);
		c.codec = codec;
		c.key = key ? 1u : 0u;
		c.width = l;
		c.height = a;
		c.instant_us = instant_us;
		c.total = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.piece = (uint32_t)q;
		/* ⭐ §6.2 — and the value comes FROM THE INSTANT OF CAPTURE, not from
		 *    here: between capture and this line the whole encoding passes, and
		 *    reading it now would give a number higher than the real one. */
		c.input = input;
		if (!send_msg(MSG_FRAME, &c, sizeof c, data + off, q)) {
			registro_dice(LOG_CHILD,
			              "⛔ the piece at %zu of %zu did not go out (%s): the "
			              "parent will not receive the frame, and will NOT "
			              "receive half of one",
			              off, byte, strerror(errno));
			return;
		}
		off += q;
	}
}

/* ⭐⭐ THE CURSOR SHAPE, from PipeWire's metadata to the wire — and in between
 *     there is a process boundary.
 *
 * ⛔ This is the `CursorArrived` of `cursor.h`, and `capture.c` calls it
 *    **from the PipeWire thread**.  ⚠ So it does NOT touch any of the loop's
 *    state and does not allocate: it takes the bytes, splits them and sends
 *    them.  A `malloc` in here would be a `malloc` on the capture's real-time
 *    thread.
 *
 * ⚠ And the image lives ONLY inside the call (`cursor.h` says so): it is
 *   copied into the envelope and no pointer to it is kept.
 *
 * Returns 0: from here on the shape belongs to the parent, and the child has
 * no way of knowing whether the client received it — ⛔ saying otherwise would
 * be faking a confirmation that does not exist. */
static int cursor_to_parent(void *chi, const CursorShape *f)
{
	size_t byte, off = 0;

	(void)chi;
	if (!f)
		return -1;
	byte = (size_t)f->width * f->height * 4u;
	/* ⭐ The hidden one is `0x0` with the image NULL, and it must be sent **as
	 *    a message**: it is the only way the client has of knowing the pointer
	 *    has vanished, instead of drawing the last shape forever (§5.5). */
	if (byte == 0) {
		struct body_cursor c;
		memset(&c, 0, sizeof c);
		c.width = f->width;
		c.height = f->height;
		c.active_x = f->active_x;
		c.active_y = f->active_y;
		return send_msg(MSG_CURSOR, &c, sizeof c, NULL, 0) ? 0 : -1;
	}
	if (!f->bitmap)
		return -1;
	while (off < byte) {
		struct body_cursor c;
		size_t q = byte - off;
		if (q > MAX_PIECE)
			q = MAX_PIECE;
		memset(&c, 0, sizeof c);
		c.width = f->width;
		c.height = f->height;
		c.active_x = f->active_x;
		c.active_y = f->active_y;
		c.total = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.piece = (uint32_t)q;
		if (!send_msg(MSG_CURSOR, &c, sizeof c, f->bitmap + off, q)) {
			/* ⛔ In chatter, and for a precise reason: the cursor changes shape
			 *    dozens of times while the pointer crosses a window, and one
			 *    line for each would cover the log.
			 *    ⚠ But it is NOT silenced: a shape lost halfway leaves the
			 *    client with the previous cursor, which is a visible defect. */
			log_detail(LOG_CHILD,
			                   "the cursor piece at %zu of %zu did not "
			                   "go out (%s): the client keeps the old shape",
			                   off, byte, strerror(errno));
			return -1;
		}
		off += q;
	}
	return 0;
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ PHASE 7 — THE CLIPBOARD: the two callbacks that cross the boundary.     */
/*                                                                            */
/* ⛔⛔ AND THEY RUN ON THE CLIPBOARD THREAD, not on this loop — `clipboard.h`,  */
/*      "the thread contract".  ⇒ In here it is allowed to WRITE TO THE       */
/*      SOCKET (a `send` on SEQPACKET is atomic per message) and NOTHING ELSE: */
/*      ⛔ `libei` is not reentrant (`input.h`), and the table of transfers   */
/*      in flight is touched only by this thread — see below.                 */

/* ⛔ The table is written by TWO threads: the clipboard one, which puts the
 *    serials in, and the child's loop, which expires them.  ⚠ A lock for an
 *    eight-entry table costs less than a defect that shows up once every
 *    thousand pastes. */
static pthread_mutex_t clipboard_lock = PTHREAD_MUTEX_INITIALIZER;

static void clipboard_from_session(const char *text, size_t byte, void *data)
{
	size_t off = 0;

	(void)data;

	/* ⚠ The cap has already been enforced by `clipboard.c`, which is where the
	 *   text exists whole.  ⛔ This line is NOT a duplicate: it is the promise
	 *   that `assemble_clipboard()` on the other side never receives a `total` it
	 *   would refuse — that is, that the defect, if there were one, shows
	 *   **here** and not as a text vanished without explanation. */
	if (byte > CLIPBOARD_CAP) {
		registro_dice(LOG_CLIPBOARD,
		              "⛔ %zu bytes over the cap of §5.4 (%u) got "
		              "this far: they are NOT sent.  ⚠ If this line appears, "
		              "the check in `clipboard.c` has a hole",
		              byte, CLIPBOARD_CAP);
		return;
	}

	do {
		struct body_clipboard c;
		size_t q = byte - off;

		if (q > MAX_PIECE)
			q = MAX_PIECE;
		memset(&c, 0, sizeof c);
		c.serial = 0; /* the session copied, it did not ask */
		c.total = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.piece = (uint32_t)q;
		if (!send_msg(MSG_CLIPBOARD_FROM_SESSION, &c, sizeof c,
		           q ? text + off : NULL, q)) {
			/* ⛔ Plain and not in detail: a copied text that does not reach the
			 *    client is a fact the user SEES — pastes on the phone and finds
			 *    what was there before.  ⚠ It is also the case in which
			 *    silence most resembles working. */
			registro_dice(LOG_CLIPBOARD,
			              "⛔ the piece at %zu of %zu bytes did not go out to the "
			              "parent (%s): what the session copied will NOT "
			              "reach the client",
			              off, byte, strerror(errno));
			return;
		}
		off += q;
	} while (off < byte);
}

static void clipboard_wants_paste(uint32_t serial, void *data)
{
	struct body_clipboard c;
	uint64_t t_now = log_now_ms();
	int slot = -1;

	(void)data;

	pthread_mutex_lock(&clipboard_lock);
	for (int i = 0; i < CLIPBOARD_IN_FLIGHT; i++)
		if (!clipboard_in_flight[i].used) {
			slot = i;
			break;
		}
	if (slot >= 0) {
		clipboard_in_flight[slot].used = true;
		clipboard_in_flight[slot].serial = serial;
		clipboard_in_flight[slot].expires_ms = t_now + CLIPBOARD_WAIT_MS;
	}
	pthread_mutex_unlock(&clipboard_lock);

	/* ⛔ The table is full: «I don't have it» is answered AT ONCE instead of
	 *    adding a debt nobody will expire.  ⚠ Eight pastes together is not a
	 *    normal case — if this line appears, either someone is holding down
	 *    Ctrl+V, or the answers are not coming back. */
	if (slot < 0) {
		registro_dice(LOG_CLIPBOARD,
		              "⛔ already %d paste requests in flight: request %u is closed "
		              "at once with «I don't have it», instead of staying without "
		              "an answer",
		              CLIPBOARD_IN_FLIGHT, serial);
		clipboard_reply(stage_clipboard, serial, NULL, 0);
		return;
	}

	memset(&c, 0, sizeof c);
	c.serial = serial;
	if (!send_msg(MSG_CLIPBOARD_REQUEST, &c, sizeof c, NULL, 0)) {
		/* ⛔ It did not go out: the answer goes NOW, without waiting for the
		 *    timeout.  The timeout is for whoever does not answer; here we
		 *    already know that nobody will. */
		registro_dice(LOG_CLIPBOARD,
		              "⛔ the paste request %u did not go out to the "
		              "parent (%s): answering «I don't have it» at once, or the paster "
		              "stays hanging",
		              serial, strerror(errno));
		pthread_mutex_lock(&clipboard_lock);
		clipboard_in_flight[slot].used = false;
		pthread_mutex_unlock(&clipboard_lock);
		clipboard_reply(stage_clipboard, serial, NULL, 0);
	}
}

/* Whoever was in flight and got no answer within the timeout: it is answered
 * empty-handed.  ⛔ Runs on the child's loop, on every round of `poll`. */
static void clipboard_expire(uint64_t t_now)
{
	uint32_t expired[CLIPBOARD_IN_FLIGHT];
	int amount = 0;

	pthread_mutex_lock(&clipboard_lock);
	for (int i = 0; i < CLIPBOARD_IN_FLIGHT; i++)
		if (clipboard_in_flight[i].used && t_now >= clipboard_in_flight[i].expires_ms) {
			expired[amount++] = clipboard_in_flight[i].serial;
			clipboard_in_flight[i].used = false;
		}
	pthread_mutex_unlock(&clipboard_lock);

	/* ⛔ Outside the lock: `clipboard_reply` makes synchronous D-Bus calls,
	 *    and holding it while waiting for the bus would block the clipboard
	 *    thread on every new signal. */
	for (int i = 0; i < amount; i++) {
		registro_dice(LOG_CLIPBOARD,
		              "⚠ no answer from the client for request %u within "
		              "%d ms: closing with «I don't have it».  ⛔ The paster sees an "
		              "empty paste, which is much better than a hung "
		              "desktop",
		              expired[i], CLIPBOARD_WAIT_MS);
		clipboard_reply(stage_clipboard, expired[i], NULL, 0);
	}
}

/*
 * The text the CLIENT copied, assembled one piece at a time.
 *
 * ⛔ One table only, and that is enough: requests are served **one at a time**
 *    on the wire (`rcp.c` does not keep two open towards the same client), and
 *    two interleaved assemblies here would mean two mixed texts — that is
 *    exactly what the transfer identifier of §7.4 exists to avoid.
 *    ⚠ If one day the parent opened two, this function **says so** instead of
 *    mixing: a `serial` that changes halfway through the assembly throws
 *    everything away.
 */
static struct {
	bool is_opened;
	uint32_t serial;
	uint8_t *data;
	size_t total, received;
} clipboard_assembly;

static void clipboard_assembly_free(void)
{
	if (clipboard_assembly.data)
		explicit_bzero(clipboard_assembly.data, clipboard_assembly.total);
	free(clipboard_assembly.data);
	clipboard_assembly.data = NULL;
	clipboard_assembly.is_opened = false;
	clipboard_assembly.total = clipboard_assembly.received = 0;
}

static bool clipboard_collect(uint32_t serial);

static void clipboard_from_client(const struct body_clipboard *c, const uint8_t *data)
{
	/* ⛔ "I don't have it" arrives as a FIELD, not as a zero length: an empty
	 *    text is a legitimate and different fact.  ⇒ Two roads, and two
	 *    different calls towards Mutter. */
	if (c->nothing) {
		clipboard_assembly_free();
		if (clipboard_collect(c->serial))
			clipboard_reply(stage_clipboard, c->serial, NULL, 0);
		else
			log_detail(LOG_CLIPBOARD,
			                   "«I don't have it» for request %u, which is no "
			                   "longer in flight: already expired, and Mutter has already "
			                   "had its answer",
			                   c->serial);
		return;
	}

	if (c->total > CLIPBOARD_CAP) {
		registro_dice(LOG_CLIPBOARD,
		              "⛔ the parent announces %u bytes of clipboard, over the cap "
		              "of §5.4 (%u): answering «I don't have it» instead of truncating",
		              c->total, CLIPBOARD_CAP);
		clipboard_assembly_free();
		if (clipboard_collect(c->serial))
			clipboard_reply(stage_clipboard, c->serial, NULL, 0);
		return;
	}

	if (c->offset == 0) {
		clipboard_assembly_free();
		clipboard_assembly.data = (uint8_t *)malloc((size_t)c->total + 1u);
		if (!clipboard_assembly.data) {
			registro_dice(LOG_CLIPBOARD,
			              "⛔ %u bytes of clipboard from the client do not fit in "
			              "memory: answering «I don't have it»",
			              c->total);
			if (clipboard_collect(c->serial))
				clipboard_reply(stage_clipboard, c->serial, NULL, 0);
			return;
		}
		clipboard_assembly.is_opened = true;
		clipboard_assembly.serial = c->serial;
		clipboard_assembly.total = c->total;
		clipboard_assembly.received = 0;
	}

	/* ⛔ In order, of the same transfer, and of the same size.  A piece that
	 *    does not add up throws everything away and ANSWERS: leaving the
	 *    assembly open halfway would mean a `SelectionTransfer` waiting for
	 *    the timeout for nothing. */
	if (!clipboard_assembly.is_opened || c->serial != clipboard_assembly.serial
	    || c->offset != clipboard_assembly.received
	    || c->total != clipboard_assembly.total
	    || (uint64_t)c->offset + c->piece > c->total) {
		registro_dice(LOG_CLIPBOARD,
		              "⛔ clipboard piece out of place (request %u, offset %u "
		              "of %u): dropping the whole text and answering «I don't have it»",
		              c->serial, c->offset, c->total);
		clipboard_assembly_free();
		if (clipboard_collect(c->serial))
			clipboard_reply(stage_clipboard, c->serial, NULL, 0);
		return;
	}

	memcpy(clipboard_assembly.data + c->offset, data, c->piece);
	clipboard_assembly.received += c->piece;
	if (clipboard_assembly.received < clipboard_assembly.total)
		return;

	clipboard_assembly.data[clipboard_assembly.total] = 0;
	/* ⛔ It is collected BEFORE answering: if the serial is no longer in
	 *    flight, the timeout has already closed it with Mutter, and a second
	 *    `SelectionWriteDone` on the same transfer is a message Mutter is no
	 *    longer waiting for. */
	if (clipboard_collect(clipboard_assembly.serial)) {
		registro_dice(LOG_CLIPBOARD,
		              "⭐ %zu bytes from the client delivered to whoever is pasting "
		              "(request %u)",
		              clipboard_assembly.total, clipboard_assembly.serial);
		clipboard_reply(stage_clipboard, clipboard_assembly.serial,
		                 (const char *)clipboard_assembly.data,
		                 clipboard_assembly.total);
	} else {
		registro_dice(LOG_CLIPBOARD,
		              "⚠ the text for request %u arrived AFTER the timeout "
		              "of %d ms: it is dropped, because Mutter has already had its "
		              "answer.  ⛔ Whoever pasted saw an empty "
		              "paste, and that is the declared price of the timeout",
		              clipboard_assembly.serial, CLIPBOARD_WAIT_MS);
	}
	clipboard_assembly_free();
}

/* Was the serial really among those in flight?  ⛔ Removing it from the table
 * and serving it are one thing only, and they live here together: a serial
 * served and left in the table would be expired later, and Mutter would
 * receive **two** `SelectionWriteDone` for the same transfer. */
static bool clipboard_collect(uint32_t serial)
{
	bool c_era = false;

	pthread_mutex_lock(&clipboard_lock);
	for (int i = 0; i < CLIPBOARD_IN_FLIGHT; i++)
		if (clipboard_in_flight[i].used && clipboard_in_flight[i].serial == serial) {
			clipboard_in_flight[i].used = false;
			c_era = true;
			break;
		}
	pthread_mutex_unlock(&clipboard_lock);
	return c_era;
}

/* ⛔⭐ THE CHILD KEEPS WHAT IT HAS ENCODED, and the reason is not speed: it is
 *     that the PARENT has a single deposit (`webtransport.c`), so when another
 *     user enters the parent EMPTIES it — and the first user, who still has
 *     their child alive, should be able to have it sent again without
 *     recapturing.
 *
 * ⚠ And **the same frame** is sent again, not a new one: phase 2 is a still
 *   image, the one from when the stage was switched on
 *   (`PHASES.md` §02-primo-fotogramma), and recapturing here would mean
 *   delivering two different images under the same label.  ⛔ The frame loop
 *   belongs to phase 3. */
static uint8_t *kept[3];
static size_t kept_byte[3];
static bool kept_key[3];
static uint32_t kept_w, kept_h;
static uint64_t kept_instant;
/* ⛔ And the KEPT frame carries its `input` too, the one from the instant it
 *    was captured — not the current one.  ⚠ Sending it again with the current
 *    number would tell whoever comes back that an input just arrived is
 *    already in the scene of an image frozen for minutes: and the latency
 *    link would read it as a very low latency.  It is the same reason **the
 *    same** frame is sent again and not a new one. */
static uint32_t kept_input;

/* ═══════════════════════════════════════════════════════════════════════════ */
/* ⭐⭐ PHASE 3 — THE FRAME LOOP, INSIDE THE CHILD                              */
/*                                                                             */
/* ⛔⭐ THERE IS ONE ENCODER PER CODEC, AND IT LIVES FROM ONE FRAME TO THE       */
/*     NEXT.  Until phase 2 one was created per frame —                        */
/*     `codificatore_nuovo()` … `codificatore_libera()` inside the same        */
/*     function — and with a single frame it did not show.  ⛔ With the loop, */
/*     a new encoder on every round means that **prediction does not           */
/*     exist**: every frame would be a keyframe, that is ten times the         */
/*     bandwidth of a delta, forever.  ⚠ And it is not only bandwidth:         */
/*     `RCP.md` §5.2 builds the whole abandonment cure on the difference       */
/*     between keyframe and delta, and without deltas that cure has no object. */
/*                                                                             */
/* ⛔ AND THERE IS **ONE** RATE, where before there were two.                  */
/*    `capture_start()` asked for 60 and the encoding request declared 30: two */
/*    different numbers for the same quantity, harmless only as long as a     */
/*    single frame was encoded.  ⇒ `MOTION_FPS`, declared here and used in  */
/*    both places.  ⭐ The value is **60** and not 30 because it is the        */
/*    desired one of `SPECS.md` §3.1, and because `LESSONS.md` §6.1 says  */
/*    that the number asked of the capture IS the ceiling: asking for 30, 18  */
/*    arrive; asking for 60, 37 arrive.  A ceiling we put there ourselves is   */
/*    not a measure of the machine.                                            */
#define MOTION_FPS 60

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ THE PIXELS' ROUTE — and since 22 Aug 2026 the default is THE CARD
 *
 * ⛔ UNTIL TODAY THE FRAME TOOK THIS ROUND TRIP: it left the GPU (where Mutter
 *    had composed it), was COPIED into system memory, CONVERTED on the CPU by
 *    `sws_scale`, and UPLOADED again to the GPU to be encoded.  `[M]` 22 Aug
 *    2026, agent C, inside the product: copy 1.65 · conversion 8.15 ·
 *    upload 1.16 = **10.96 ms out of 18.86, 58 % of the stretch**.
 *
 * ⭐ The card's route — the DMA-BUF delivered by Mutter and imported as a
 *    VA-API surface — removes all three steps: the frame **was already on the
 *    GPU**.  `[M]` Mutter really does deliver the DMA-BUF: 388 frames, 4
 *    buffers, LINEAR modifier, stride 7680 read from the chunk
 *    (`DECISIONS.md` §2.3-ter).
 *
 * ⛔⛔ AND IT HOLDS **ONLY IF THE ENCODER IS IN HARDWARE**: in software there is
 *      no pixel to read.  ⇒ The route is chosen first, and if the encoder
 *      falls back to the CPU the stage is REMOUNTED on memory, declaring it —
 *      see `card_to_abandon`.
 *
 * ⚠ And the TEN BITS do not come back through this door: Mutter delivers BGRx,
 *   eight bits per channel, on the card as in memory (`capture.h`).  This
 *   route changes where the frame is, not what is inside it.
 *
 * ⭐ It can be overridden from the compile line (`-DCOPIA_ZERO=0`), and it
 *    serves ONE thing only: rebuilding the **before** with the same source as
 *    the after, for the alternating A/B comparison.  ⛔ It is not a product
 *    switch and does not become one: the product has a single value, the one
 *    below (`CODER.md` invariant I7).
 * ═══════════════════════════════════════════════════════════════════════════ */
#ifndef ZERO_COPY
#define ZERO_COPY 1
#endif

/* The route asked of the producer at the next mounting of the stage.
 * ⛔ It is a variable and not a constant because it can STEP BACK once: when
 *    it turns out that this machine's encoder is in software.
 *    ⚠ It never goes forward again by itself: going forward would mean
 *    retrying a route already measured impossible, at every remount. */
static CaptureRoute stage_route =
    ZERO_COPY ? CAPTURE_ROUTE_CARD : CAPTURE_ROUTE_MEMORY;
/* ⛔ THE THREE REMOUNT STATES, and they are three because they answer three
 *    different questions.  ⚠ None of them remounts anything by itself: the
 *    stage is held by the loop, and `encode_and_send` cannot dismantle it
 *    while it is reading inside it.
 *
 *   `card_to_abandon`  ⇒ remount in MEMORY: this frame on the card
 *                              cannot be used;
 *   `card_to_retry`    ⇒ remount on the CARD: the canvas has changed and
 *                              the earlier denial no longer holds;
 *   `card_never_again`         ⛔ this machine's encoder is in SOFTWARE: it is
 *                              not a matter of canvas, and retrying at every
 *                              resize would be remounting the stage for
 *                              nothing, forever.
 */
static bool card_to_abandon;
static bool card_to_retry;
static bool card_never_again;
/* ⛔⛔ AND THIS IS THE GUARD THAT AVOIDS THE IDLE ROUND TRIP — and it deserves a
 *     line of explanation, because it looks like the same thing and is not.
 *
 * The DMA-BUF stride is known **only after the first frame** (`capture.h`
 * rule 1: the stride is READ from the chunk, never computed).  ⇒ With a canvas
 * whose stride is not importable the stage is born on the card, delivers a
 * frame, it is refused, and the stage is remounted on memory.  Without memory
 * of that verdict it would be redone at every round.
 *
 * ⭐ Here the canvas for which the card was denied is kept, and the card is
 *    not retried until the canvas changes.  ⛔ And the verdict stays the one
 *    MEASURED on the real stride: this is the memory of that verdict, not a
 *    prediction replacing it.
 */
static uint32_t card_denied_w, card_denied_h;

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ PHASE 17 — THE FALLBACK AFTER THE REFUSAL: the machine without a 3D card
 *
 * ⛔ THE DEFECT, `[M]` 29 Sep 2026, T1c, 7 VMs out of 7: on a machine without
 *    3D acceleration (VM with `virtio-vga` without virgl, a server without a
 *    card) the compositor renders in software and has NO DMA-BUF buffers to
 *    offer.  The card's route asks ONLY for those (mandatory modifier,
 *    `capture.c` `proposal()`), the negotiation dies with "no more input
 *    formats", and no frame ever arrives.  ⇒ The fallback of
 *    `card_to_abandon` did not fire: it lives INSIDE a frame.  The
 *    browser got in ("Admitted") and the desktop did not arrive; the child
 *    remounted the stage every five seconds, always on the card, forever.
 *
 * ⭐ THE CURE: when the negotiation on the card FAILS — the stream in error
 *    without a format ever having been agreed
 *    (`capture_format_refused()`, or `G_IO_ERROR_NOT_SUPPORTED` from
 *    `capture_start()`) — the route switches to MEMORY, it is declared, and
 *    the capture is reopened at once on the same stage.
 *
 * ⛔⛔ AND THE TWO ROUTES ARE NOT OFFERED TOGETHER, on purpose: a proposal with
 *      memory next to the card would let the compositor choose, and on
 *      machines with the real card zero copy would be lost where it exists
 *      today.  Here memory arrives only AFTER a measured "no".
 * ⛔ And it does NOT fire on silence (no frame in 5 s): on a real card a
 *    compositor slow to be born would give the same silence, and zero copy
 *    would go away because of a race.  It fires on the refusal, which is a
 *    fact.
 * ⚠ `card_never_again`: the refusal comes from the COMPOSITOR, not from the
 *   canvas — a new canvas does not give it the buffers it lacks, and retrying
 *   at every resize would be a failed negotiation for nothing.
 * ⚠ No exceptions per compositor: the question is the same for Mutter and
 *   for KWin (wlroots has its own fallback in `capture_start_wlr()`).
 * ═══════════════════════════════════════════════════════════════════════════ */
static bool falls_back_if_refused(bool refused, const char *why)
{
	if (!refused || stage_route != CAPTURE_ROUTE_CARD)
		return false;
	stage_route = CAPTURE_ROUTE_MEMORY;
	card_never_again = true;
	registro_dice(LOG_CHILD,
	              "⛔⛔ the CARD route was REFUSED by the compositor "
	              "(no format agreed: %s) — on this machine there are no "
	              "DMA-BUF buffers to offer, usually because "
	              "3D acceleration is missing.  ⇒ DECLARED FALLBACK: remounting the capture "
	              "on MEMORY and not retrying — from here on the stretch's "
	              "numbers include the copy",
	              why ? why : "without explanation");
	return true;
}

/* ⛔ How long a frame from the capture is awaited within one round of the loop.
 *
 * ⚠ It is not a rate ceiling: it is how long we stay still BEFORE going back to
 *   look whether the parent said something.  ⭐ Here waiting IS allowed — this
 *   is another process, and `CODER.md` §4.4 forbids waiting inside the
 *   server's asynchronous loop, not here.
 * ⛔ And on a STILL desktop Mutter delivers nothing: this wait expires
 *    entirely, and the next round starts again.  Zero frames on a still scene
 *    is a RESULT (`CaptureTake` tells it apart from a fault), not a defect.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * ⛔⛔⛔ AND IT WAS 0.25 — that is A QUARTER OF A SECOND OF LATENCY ON EVERY CLICK.
 *
 *     `[M]` 15 Aug 2026, measured on the user's REAL clicks (log of 05:25,
 *     twenty-five presses): **click → first frame sent, median 136 ms, worst
 *     502 ms**.  And the loop's summary line said the cause without anyone
 *     reading it: **"3-4 empty waits per second"**, that is four rounds per
 *     second, that is 250 ms per round.
 *
 * ⛔ THE MECHANISM, and the line above almost said it: the parent's input is
 *    read **before** the wait.  A click arriving one millisecond AFTER the
 *    loop entered `capture_take()` stays still in the socket for the 249 ms
 *    that remain.  ⚠ On a moving desktop it does not show — the frame arrives
 *    at once and the round restarts; on a STILL desktop, which is the case in
 *    which one clicks, the whole of it is paid.  ⇒ Expected average latency:
 *    **125 ms**, and the measured one is 136.
 *
 * ⇒ ⭐ With 8 ms the average added latency drops to **4 ms**, and the loop
 *   wakes up 125 times per second instead of 4: it is an empty `poll()` and a
 *   wait on a condition, that is nothing next to sixty frames per second to
 *   convert and compress.
 *
 * ⚠ AND IT REMAINS A FALLBACK, declared: the REAL cure is not to wait on a
 *   timer at all — a descriptor the capture writes when a frame is ready, put
 *   in the same `poll()` as the parent's socket and `libei`.  Then the added
 *   latency would be **zero** instead of four milliseconds, and the wake-ups
 *   would drop to the useful ones.  ⛔ It was not done tonight because it
 *   touches the exchange point of `capture.c` (today the frame is copied only
 *   if someone is already waiting), and that piece runs on PipeWire's
 *   real-time thread: it is a cure to measure, not to improvise.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define MOTION_WAIT_S 0.008

/* ⛔⭐ HOW LONG TO WAIT BEFORE TRYING AGAIN TO MOUNT THE STAGE, AND WHY IT
 *     GROWS.
 *
 * `[M]` 14 Aug 2026, the user's real session: without any wait the loop spun
 * idle and wrote **30.8 GB of log in a few minutes**, 112 million identical
 * lines all in the same millisecond.  ⇒ The defect was not "retrying": it was
 * **retrying without ever stopping**.
 *
 * ⚠ The minimum is one second because a graphical session being born takes
 *   seconds, and retrying ten times per second does not make it be born
 *   sooner.
 * ⚠ The maximum is half a minute because beyond that nothing is gained and the
 *   real case would be lost: a user who logs in again on a machine where the
 *   session has just come back must find it, not wait a quarter of an hour. */
#define STAGE_RETRY_MIN_MS 1000
#define STAGE_RETRY_MAX_MS 30000

/*
 * ⚠ How long to wait before asking again for the BIRTH of the graphical session.
 *
 * ⛔⛔ IT WAS ONE MINUTE, AND IT WAS THE DEFECT — 16 Aug 2026.  The reasoning
 *     ("`gnome-session` takes a few seconds, and without a rein we would start
 *     one on every round") was right; ⛔ the number was not.
 *
 * `[M]` After a logout the user manager is still shutting down, and the
 * session we start at that instant **dies with it**.  With the rein at one
 * minute the child did not retry for sixty seconds: the client waited, saw
 * nothing and left.  ⇒ One round yes and one no, which is exactly the rhythm
 * the user saw five times in a row.
 *
 * ⭐ Twelve seconds: more than the time `gnome-session` takes to appear on the
 *    bus (`[M]` 3 s on the test machine, with margin for a loaded machine),
 *    and short enough that a failed start is recovered while whoever is
 *    watching is still there.
 *
 * ⚠ And the rein remains necessary: without it, a retry every second would
 *   start ten `gnome-session` before the first one shows up.
 */
#define BIRTH_REIN_MS 12000

/*
 * ⛔⭐⭐ HOW OFTEN TO RETRY WHILE THE SESSION IS BEING BORN — and this number
 *       is the cure for the defect the user saw four times: *"at the fourth
 *       login the desktop took many seconds before reappearing"*.
 *
 * ⛔⛔ THE CAUSE WAS THE DOUBLING WAIT, and the reasoning justifying it is
 *     right for ONE case only.  `STAGE_RETRY_MIN_MS` grows 1 s → 2 s →
 *     4 s → 8 s, and that is what is needed when the stage **is no longer
 *     there**: a dead session does not come back because it is called more
 *     often, and without a brake that loop has already written 30 GB of log
 *     (14 Aug).
 *
 * ⛔ But when the stage **is not there YET** the same wait is exactly the
 *    defect.  `[M]` 16 Aug 2026, twenty timed rounds: `gnome-session` shows up
 *    on the bus after ~2.9 s, and the attempts fall at 0, 1, 3, 7 s.
 *    ⇒ If it shows up at 2.9 s we find it at 3 s (100 ms lost, and it is the
 *    good case, median 3193 ms); ⛔ **if it takes 3.2 s the attempt at 3 s
 *    misses it and the next one is at SEVEN**.  The user waits four seconds
 *    of pure clock, with the session already ready and nobody looking at it.
 *
 * ⭐ And it shows in the measure itself: median 2880 ms, p90 **3891 ms**.
 *    Those two numbers are not a distribution, they are **two steps** — the
 *    attempt at 3 s and the one after.
 *
 * ⇒ The two cases the loop's comment distinguished in words — "not there yet"
 *   and "no longer there" — are now distinguished in time too: as long as we
 *   are inside the birth window we retry every 200 ms, after that the
 *   doubling rein comes back.  ⚠ The cost is sixty D-Bus calls to a name that
 *   does not answer, in twelve seconds: nothing.  The gain is up to four
 *   seconds of idle waiting, and those are the seconds the user sees.
 */
#define STAGE_BIRTH_RETRY_MS 200

/*
 * ⛔⭐ "THE USER LOGGED OUT": the third state, and without it the child REMAKES
 *     the session three seconds after letting it die.
 *
 * `[M]` 15 Aug 2026, logout bench: the child recognised the transition ("it
 * was there and is no longer"), gave the client the farewell `0x10`, and at
 * the next attempt — with the switch already lowered again — it saw a session
 * DEAD like any other and made it be born again.  ⇒ The user would have
 * logged out and the desktop would have come back by itself.
 *
 * ⭐ The states are THREE, not two: "it was never there" (it is made to be
 *    born), "it is there" (not touched), "the user closed it" (⛔ NOT remade
 *    until a NEW attach arrives).  ⚠ The return to the first state is decided
 *    by the arrival of a client — that is `MSG_VIDEO` with a codec — because
 *    that is the gesture with which the user says "I want a desktop again".
 */
static bool session_closed_by_user;
/* ⭐ "I have SEEN the graphical session alive": it is what separates "not born
 *    yet" from "it was there and the user logged out" (§7.6, below in
 *    `take_stage`).
 * ⛔ PHASE 12 — it was a `static` inside that function, and only reading the
 *    state set it to true: on GNOME it is read at every mounting, on KDE the
 *    stage is mounted DIRECTLY from KWin and the SANA state was never read.
 *    `[M]` 19 Sep 2026: after the logout the child said "not there yet, I have
 *    already asked for it" and waited to make it BE BORN AGAIN — that is, it
 *    prevented logging out.  ⇒ A mounted KWin stage also means "seen alive". */
static bool vista_viva;

/* When to retry, and how long was waited the last time. */
static uint64_t stage_retry_ms;
static uint64_t stage_wait_ms;

/*
 * ⛔⭐⭐⭐ "THE CLIENT'S CANVAS HAS ARRIVED" — and without this the stage was
 *        born at the wrong size, always.
 *
 * `[M]` 16 Aug 2026, and this is the common cause of ALL the symptoms the
 * user listed: black bands, "broken desktop", "no input", "it takes many
 * seconds".  The chain:
 *
 *   1. the child is born with `1920x1080` — the value of the children table,
 *      that is a FALLBACK — because at `fork` time the client's window has
 *      not been declared yet;
 *   2. it immediately mounts the stage at that size and sends a wrong
 *      keyframe;
 *   3. ~650 ms later the real canvas arrives (`2544x926`) and a resize would
 *      be needed;
 *   4. ⛔ but on Wayland the resize completes ONLY when the compositor
 *      delivers a new frame — and a desktop just born changes nothing.
 *      `[M]` "1 frames delivered, **3538 empty waits** (still scene: Mutter
 *      delivers only when something changes)".
 *
 * ⇒ We waited for something to move by itself: thirteen, seventeen, thirty
 *   seconds.  ⭐ Half a second of waiting here removes them all.
 *
 * ⚠ And we do NOT wait forever: invariant I1 forbids standing still out of
 *   caution.  Once `CANVAS_WAIT_MS` has passed we start with the fallback —
 *   better a desktop to resize than no desktop.
 */
static bool canvas_from_client;

/* ⚠ How long the client's canvas is given before starting with the fallback.
 *   `[M]` ~650 are enough: half a second of margin and not one more, because
 *   beyond that we start making wait whoever has already pressed "Connect". */
#define CANVAS_WAIT_MS 1200

/* ⭐ When we asked for the BIRTH of the graphical session, 0 if never.
 *
 * ⛔ It was a `static` inside `take_stage()`, and from there the frame
 *    loop could not see it — so it could not tell "the stage is not there
 *    YET" from "it is no longer there", and treated the two cases with the
 *    same doubling wait.  ⇒ See `STAGE_BIRTH_RETRY_MS`. */
static uint64_t birth_requested_ms;

/* Are we inside the window in which a requested session can still show up?
 * ⚠ If so, the missing stage is a stage that is BEING BORN. */
static bool is_being_born(uint64_t now_ms)
{
	return birth_requested_ms != 0 &&
	       now_ms - birth_requested_ms <= BIRTH_REIN_MS;
}

#define CODEC_MAX 4
/* ⛔ FOUR SLOTS FOR THREE CODECS, and the count is on purpose: the index IS
 *    the number of §6.2 (1 = HEVC, 2 = AV1, 3 = H.264) and slot 0 stays empty.
 *    ⚠ A "tight" array with a subtraction inside would be the same thing
 *    written worse: the day a new codec took 4, the subtraction would have to
 *    be fixed in six places and the log would say numbers different from the
 *    protocol's. */
static Encoder *enc[CODEC_MAX];
/* Which codec the parent asked for: 0 = none, that is nobody is watching. */
static uint8_t requested_codec;
/* ⛔⭐⭐ AND THE DEPTH THE PARENT NEGOTIATED (§4.3) — 17 Aug 2026.
 *
 *      Here there was a literal, three lines further on: `r.depth = 10`,
 *      for EVERY codec and whatever had been negotiated.  ⛔ The stream came
 *      out at 10 bits while `HERE_I_AM` declared 8 — **two truths about the same
 *      fact, in two different processes**, and no bench could see them
 *      together.
 *
 * ⚠ `0` = the parent has not said it yet.  ⛔ And it does NOT count as 8: until
 *   it is known, no encoder is opened — "I don't know" and "it is eight" are
 *   two different facts, and it is precisely their confusion that produced
 *   the defect. */
static uint8_t requested_depth;
/* ⛔⭐⭐ AND THE LEVEL THE CLIENT DECLARED (§4.3 line 701) — 23 Aug 2026, and it
 *      comes from the same family of defect as the line above.
 *
 *      `[M]` canvas 3840x2160, H.264: the client declares `video.level=5.1`
 *      and the server produces **5.2**.  The requested number lived in the
 *      PARENT, the product in the CHILD, and nobody put them side by side —
 *      `LESSONS.md` §7.5.
 *
 * ⚠ In tenths (`5.1` ⇒ 51).  ⛔ `0` = the client did not declare it, and §4.3
 *   does not require it: then NO CEILING, it opens anyway and WRITES what came
 *   out.  ⚠ And here zero does not block the opening as the depth does: the
 *   depth is always negotiated (§4.3 imposes it on both), the level is not.
 *   They are two different "zeros", and treating them alike would be
 *   inventing an obligation the document does not have. */
static uint8_t requested_level_x10;
/* ⛔ §5.2 — the keyframe debt, one per codec: asking for it for HEVC does not
 *    produce it on AV1, and treating them together would give a keyframe to
 *    whoever did not ask for it and a delta to whoever did. */
/* ⛔⛔⭐ FOUR SLOTS, like `enc[]` — and this line cost a round on 20 Aug 2026.
 *      With `[3]` codec **3** wrote OUT OF BOUNDS, and the byte that got
 *      dirtied was the variable next to it: the log said
 *      "⭐ §4.3: the parent negotiated 8 bits (before **1**)" at every keyframe
 *      request, that is a memory defect disguised as a negotiation defect.
 *      ⇒ Zero frames, and no line naming the cause.
 * ⚠ The index IS the number of §6.2: whoever adds a codec widens THESE arrays,
 *   and they are FIVE since 23 Aug 2026 (`enc_level[]` is the latest).  They
 *   are found like this: `grep "\[CODEC_MAX\]"`. */
static bool key_debt[CODEC_MAX];
/* ⏳ `RCP.md` §13 (PROPOSED) — THE DECODER'S PACE.  `pace_interval_us` = 0 is
 *    no ceiling (the default, and the state at every new viewer); otherwise
 *    the frame loop does not TAKE a frame from the capture until that long has
 *    passed since the last one it encoded (`pace_last_us`).
 * ⭐ Nothing is lost by waiting: the capture slot keeps only the newest picture
 *    and the UNION of the damage (`capture.c`, 15 Oct 2026), so the next frame
 *    carries every change, and the delta chain stays whole.
 * ⛔ A keyframe owed (`key_debt`) is never held back. */
static uint64_t pace_interval_us;
static uint64_t pace_last_us;
static uint16_t pace_fps;
static uint64_t pace_held, pace_held_logged;

static void pace_set(uint16_t max_fps, const char *why)
{
	/* ⛔ The same clamp as `rcp_pace_clamp()`, redone on this side of the
	 *    socket: 0 or ≥ MOTION_FPS = no ceiling, below 5 = 5. */
	if (max_fps >= MOTION_FPS)
		max_fps = 0;
	else if (max_fps && max_fps < 5)
		max_fps = 5;
	if (max_fps == pace_fps)
		return;
	registro_dice(LOG_CHILD,
	              max_fps ? "⏳ PACE (RCP.md §13): at most %u frames/s are taken "
	                        "from the capture (before %u, 0 = no ceiling) — %s.  "
	                        "%llu rounds held back so far"
	                      : "⏳ PACE (RCP.md §13): ceiling LIFTED (%u, before %u) "
	                        "— %s.  %llu rounds held back so far",
	              (unsigned)max_fps, (unsigned)pace_fps, why,
	              (unsigned long long)pace_held);
	pace_fps = max_fps;
	pace_interval_us = max_fps ? 1000000u / max_fps : 0;
}

/* How long the loop may still wait before the next frame is due; 0 = due now
 * (or no ceiling, or a keyframe owed). */
static uint64_t pace_wait_us(uint64_t now_us)
{
	if (!pace_interval_us || !requested_codec)
		return 0;
	if (requested_codec < CODEC_MAX && key_debt[requested_codec])
		return 0;
	if (now_us - pace_last_us >= pace_interval_us)
		return 0;
	return pace_interval_us - (now_us - pace_last_us);
}
/* ⛔ With which depth each encoder was OPENED.  ⚠ It is kept here and not
 *    asked of `encoder.h`: that module has no reader for the depth, and
 *    adding one for a question that can be remembered would be widening an
 *    interface out of the caller's laziness. */
static uint8_t enc_profile[CODEC_MAX];
/* ⛔ And with which LEVEL IMPOSED (§4.3, in tenths; `0` = no ceiling).  ⚠ It
 *    sits next to `enc_profile[]` and for the same reason: the stage outlives
 *    the client (I4), and the second to connect can declare a level different
 *    from the first — without this memory the encoder would stay at the
 *    ceiling of the FIRST, which is exactly the defect being cured. */
static uint8_t enc_level[CODEC_MAX];
/*
 * ⭐ PHASE 13 — THE CHANNEL ORDER THAT COMES FROM THE CAPTURE.
 *
 * ⛔⛔ It was `ENCODER_PIXEL_BGRX` hard-wired inside `encoder_of()`,
 *     and it was true for GNOME and KDE (Mutter and KWin give BGRx).  `[M]` 21
 *     Sep 2026: labwc gives **XBGR8888**, that is `R G B x`, and gives it as
 *     the ONLY format — screencopy's `buffer` event arrives only once.  ⇒ With
 *     the hard-wired order the user saw **red and blue swapped**.  Found by
 *     the adversarial reviewer, not by an image: C1 does not look at colours.
 * ⇒ The order is told by the FRAME (`formato_drm`), and if it changes the
 *   encoder is redone — the same scheme as `enc_level`.
 */
static FormatoPixel input_format = ENCODER_PIXEL_BGRX;
static FormatoPixel enc_fmt[CODEC_MAX];
static uint64_t cycle_frames, cycle_keys, cycle_zero, cycle_faults;
/* ⛔ COUNTED APART from `cycle_faults`, and it is not pedantry: that counter
 *    enters the criterion "the loop did not even try to capture" of the
 *    summary line.  Putting here the frames discarded for inconsistent
 *    geometry would give two different facts under the same label — form E8,
 *    inside the very line that exists to unmask it. */
static uint64_t inconsistent_frames;
/* ⛔⭐ THE GROWING WAIT ON REOPENING THE ENCODER — and the reason is the same
 *     as the 30.8 GB of log of 14 Aug: if `codificatore_nuovo()` fails for a
 *     PERSISTENT cause (GPU memory, a profile that does not hold that size, a
 *     busy node), `encoder_of()` would retry the opening **at every
 *     frame** — sixty VAAPI contexts per second, and one log line for each.
 *     ⚠ The backoff here hides nothing: the first line is always written, and
 *     the retry is declared. */
static uint64_t enc_retry_ms[CODEC_MAX];
static uint64_t enc_wait_ms[CODEC_MAX];
#define ENC_RETRY_MIN_MS 500u
#define ENC_RETRY_MAX_MS 10000u
/* ⭐ When the stream was last restarted to get a frame delivered on a still
 *    scene.  ⛔ The backoff is not caution: every restart costs the
 *    renegotiation, and doing one on every round would remove the very frames
 *    being sought.  ⚠ 400 ms is two orders of magnitude below the measured
 *    4.4 seconds and above the cost of a restart (`[M]` 41.6 ms). */
static uint64_t wakeup_ms;
/* ⭐ The last restart asked by a stale «unchanged» card frame (`unchanged.h`). */
static uint64_t uc_wake_ms;
#define WAKEUP_MS 400u
/* ⛔ Cure "A" (21 Aug 2026, 🔸 derived) skips the wake-up when something is
 *    held down.  ⚠ This flag serves only NOT to repeat the log line every
 *    400 ms while the user drags: diagnostics that drown the ones that count
 *    are diagnostics that stay silent (`LESSONS.md` §2.7). */
static int wakeup_quiet;
static uint64_t cycle_logged_ms;
/* ⛔ The measure of point 7, made and NOT inferred: is the `pts` Mutter attaches
 *    to the frame our monotonic clock or not?  It is looked at once, written
 *    down, and from then on it is known which instant ends up in the 28 bytes. */
static int pts_is_monotonic = -1; /* -1 = not looked at yet */

static uint64_t now_monotonic_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t)t.tv_sec * 1000000u + (uint64_t)(t.tv_nsec / 1000);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ PHASE 7 — AUDIO INSIDE THE CHILD
 *
 * ⛔⛔ AND THE FIRST THING IS A CONSTRAINT, NOT AN ARCHITECTURE: the samples
 *      callback runs on the **PipeWire thread, in real time**.
 *
 *      Whoever writes in there a call that waits — a contended lock, a `send`
 *      on a socket, an unlucky `malloc` — **does not stop only the audio: it
 *      makes the whole PipeWire graph miss its quantum, desktop capture
 *      included**.  ⚠ That is, audio would take the frames away with it, and
 *      the symptom would be "the video stutters", which does not name audio.
 *      (`fondamenta/remotix-c/src/suono.h`, and `LESSONS.md` §5.)
 *
 * ⇒ Between the PipeWire thread and the child's loop there is a
 *   **single-producer single-consumer ring**, without locks: the producer
 *   moves only `head`, the consumer only `queue`, and the two indices are
 *   atomic.  The callback copies and returns.
 *
 * ⛔ AND WHEN THE RING IS FULL THE OLDEST IS DROPPED, as for datagrams
 *    (`RCP.md` §6.3): late sound is of no use to anyone.  ⚠ But here it is
 *    dropped **while counting**, and the count goes into the log — because a
 *    ring overflowing silently is a rhythm defect nobody will ever see.
 * ═══════════════════════════════════════════════════════════════════════════ */

/* One second of sound.  ⚠ It is not a cushion for smoothness: it is the gap
 * between two rounds of the child's loop, which with video on is ~8 ms
 * (`MOTION_WAIT_S`).  One second is two orders of magnitude of margin,
 * and it costs 192 KiB — which is less than a frame. */
#define AUDIO_RING_FRAMES 48000u

static int16_t audio_ring[AUDIO_RING_FRAMES * AUDIO_CHANNELS];
static _Atomic uint32_t audio_head; /* moved ONLY by the PipeWire thread */
static _Atomic uint32_t audio_queue;  /* moved ONLY by the child's loop */
static _Atomic uint64_t audio_overflowed; /* frames dropped by the producer */

/* ⛔ The audio clock is the SAMPLE COUNT, not `CLOCK_MONOTONIC`.
 *
 *    `RCP.md` §6.3 wants "the instant of the FIRST sample of the block", and
 *    the first sample has its own instant that depends on the sound card, not
 *    on the moment our loop woke up.  ⚠ Using wall time at the moment of
 *    sending would put in the field **when we shipped it**, which is a higher
 *    and jittery number: the client would use it to reorder and would reorder
 *    on our jitter instead of on the sound.
 *
 * ⇒ `audio_base_us` is the real time of the first captured sample; from there
 *   on time is counted by the sample rate.  ⛔ And when the ring overflows the
 *   base MOVES by the lost samples, or the clock would tell of a continuous
 *   sound where there was a gap. */
static uint64_t audio_base_us;
static uint64_t audio_consumed; /* frames already out, since the base */

static void audio_ring_reset(void)
{
	atomic_store(&audio_head, 0);
	atomic_store(&audio_queue, 0);
	atomic_store(&audio_overflowed, 0);
	audio_base_us = 0;
	audio_consumed = 0;
}

/*
 * The samples callback.  ⛔ IT RUNS IN REAL TIME: copy and return.
 *
 * ⚠ No log line in here, and it is on purpose: `registro_dice()` writes to a
 *   descriptor, and a write that blocks inside this callback costs the
 *   desktop's frames.  The overflow is COUNTED here and WRITTEN over there,
 *   from the loop.
 */
static void audio_samples(const int16_t *samples, uint32_t frames, void *ctx)
{
	uint32_t head, queue, free_n;
	(void)ctx;

	if (!frames || !samples)
		return;

	head = atomic_load_explicit(&audio_head, memory_order_relaxed);
	queue = atomic_load_explicit(&audio_queue, memory_order_acquire);

	/* ⛔ One slot always stays empty: it is the only way to tell "full" from
	 *    "empty" with only two indices. */
	free_n = (queue + AUDIO_RING_FRAMES - head - 1u) % AUDIO_RING_FRAMES;
	if (frames > free_n) {
		/* The TAIL of the block is kept, that is the most recent sound. */
		uint32_t dropped = frames - free_n;
		atomic_fetch_add_explicit(&audio_overflowed, dropped, memory_order_relaxed);
		samples += (size_t)dropped * AUDIO_CHANNELS;
		frames = free_n;
		if (!frames)
			return;
	}

	for (uint32_t i = 0; i < frames; i++) {
		uint32_t p = (head + i) % AUDIO_RING_FRAMES;
		audio_ring[p * AUDIO_CHANNELS] = samples[i * AUDIO_CHANNELS];
		audio_ring[p * AUDIO_CHANNELS + 1] = samples[i * AUDIO_CHANNELS + 1];
	}
	atomic_store_explicit(&audio_head,
	                      (head + frames) % AUDIO_RING_FRAMES,
	                      memory_order_release);
}

/* How many frames are ready to be consumed. */
static uint32_t audio_ready(void)
{
	uint32_t head = atomic_load_explicit(&audio_head, memory_order_acquire);
	uint32_t queue = atomic_load_explicit(&audio_queue, memory_order_relaxed);
	return (head + AUDIO_RING_FRAMES - queue) % AUDIO_RING_FRAMES;
}

/* ═══ PHASE 7 — the audio state in the child ════════════════════════════════
 *
 * ⛔ `son` and `acod` have TWO DIFFERENT LIVES, and it is the same division as
 *    the stage (invariant I4):
 *
 *      `son`   the SINK, belongs to the **session**: it is born with the first
 *              listener and does not die until the child dies.  ⚠ Making it
 *              vanish at every detach would cut the sound for whoever listens
 *              **inside** the session and would leave the applications
 *              already open on a dead device (`fondamenta/remotix-c/src/suono.h`);
 *      `acod`  the ENCODER, belongs to the **connection**: it depends on the
 *              codec that connection negotiated (§4.3), and is redone when
 *              the codec changes. */
static sound *snd;
static audio_cod *aenc;
/* Which audio codec the parent asked for: 0 = nobody is listening. */
static uint8_t audio_codec;
static uint64_t audio_blocks_sent, audio_blocks_lost;
static uint64_t audio_logged_us;

/*
 * Turns audio on, changes it or turns it off.  `codec` 0 = off (§6.3: 1 Opus,
 * 2 PCM).
 *
 * ⛔ TURNING OFF STOPS THE CAPTURE, NOT THE SINK — invariant I4.  The device
 *    applications play on belongs to the session; consuming the monitor
 *    belongs to whoever listens.
 */
/*
 * ⛔⛔⛔ THE **EFFECTIVE** SCHEDULING POLICY OF THE AUDIO PATH — and not the
 *       permission to ask for it.  *Rewritten on 21 Aug 2026 on the measure of
 *       A8, and the previous line was a false green.*
 *
 * WHAT WAS THERE, and why it was wrong: `RLIMIT_RTPRIO` was read and, if not
 * zero, *"⭐ real-time priority granted by the unit"* was written.
 * ⛔ **True of the rlimit, false of the effect**: the rlimit only says "you
 * are allowed to ASK", not "you got it".
 *
 * `[M]` A8, 21 Aug 2026, on THIS machine:
 *   · the kernel refuses `SCHED_FIFO` to anyone not in the **root** cgroup
 *     (`CONFIG_RT_GROUP_SCHED` with cgroup v2): `chrt -f 10 /bin/true` fails
 *     **as root** inside a slice and succeeds in the root.  ⇒ Every process
 *     governed by systemd is excluded, and **`LimitRTPRIO=20` is inert**;
 *   · snapshot of the audio path threads in the live child — `remotix-suono`,
 *     `remotix-cattura`, two `data-loop.0`, two `module-rt`: **all at normal
 *     policy, nice 0**;
 *   · `rtkit-daemon` inactive, group `pipewire` empty, and PipeWire asks for
 *     `rt.prio` **88**, not 20.
 *
 * ⛔ And the reason removing the line is not enough: without it, "I do not
 *    have the priority" and "I did not look" look the same.  ⇒ We **look**,
 *    and declare what was seen — `CODER.md` §4.6, *green is not true*: a line
 *    asserting a privilege nobody uses is worse than silence, because it is a
 *    number nobody compares.
 *
 * ⚠ AND THE CURE IS NOT HERE, declared so that nobody goes looking for it:
 *   `[M]` A8, the lever that works on this kernel is **`nice`** (crackles from
 *   10.4/s to 0.27/s at `nice -20`).  ⛔ But an independent referee —
 *   `pw-record` on the same monitor — hears **the same crackles at the same
 *   instants, and always a bit more** ⇒ the defect is born **upstream of
 *   us**, in the session's audio graph, and we carry it faithfully.  ⇒ The
 *   priority must be given to **the whole audio path of the session**
 *   (`session.c`), not to this process, and it is a product decision.
 */
static void declare_audio_priority(void)
{
	/* ⛔ The names of the threads forming the audio path.  ⚠ `data-loop` and
	 *    `module-rt` are PipeWire's, not ours: that is precisely why they must
	 *    be looked at — the priority that counts is THEIRS. */
	static const char *NAMES[] = { "data-loop", "pw-data", "pw-rt", "module-rt",
		                          "remotix-suono", "remotix-cattura" };
	struct rlimit rl;
	unsigned long cap = 0;
	DIR *folder;
	struct dirent *entry;
	int watched = 0, realtime = 0, worst_nice = -100;
	char listing[512];
	size_t used = 0;

	if (getrlimit(RLIMIT_RTPRIO, &rl) == 0)
		cap = (unsigned long) rl.rlim_cur;

	listing[0] = '\0';
	folder = opendir("/proc/self/task");
	while (folder && (entry = readdir(folder)) != NULL) {
		char fpath[128], name[64];
		FILE *f;
		long tid;
		int policy, niceness;
		size_t l;

		if (entry->d_name[0] < '0' || entry->d_name[0] > '9')
			continue;
		tid = strtol(entry->d_name, NULL, 10);
		snprintf(fpath, sizeof fpath, "/proc/self/task/%ld/comm", tid);
		f = fopen(fpath, "r");
		if (!f)
			continue;
		if (!fgets(name, sizeof name, f)) {
			fclose(f);
			continue;
		}
		fclose(f);
		l = strlen(name);
		while (l && (name[l - 1] == '\n' || name[l - 1] == ' '))
			name[--l] = '\0';

		{
			int our = 0;
			for (size_t i = 0; i < sizeof NAMES / sizeof NAMES[0]; i++)
				if (strstr(name, NAMES[i])) {
					our = 1;
					break;
				}
			if (!our)
				continue;
		}

		/* ⛔ `sched_getscheduler(tid)` and not a read of `/proc/.../stat`: it
		 *    is the same question asked of the kernel instead of a text to
		 *    parse, and it has no field index to get wrong. */
		policy = sched_getscheduler((pid_t) tid);
		errno = 0;
		niceness = getpriority(PRIO_PROCESS, (id_t) tid);
		if (errno)
			niceness = 0;

		watched++;
		if (policy == SCHED_FIFO || policy == SCHED_RR)
			realtime++;
		else if (niceness > worst_nice)
			worst_nice = niceness;

		if (used < sizeof listing - 48)
			used += (size_t) snprintf(listing + used, sizeof listing - used, "%s%s(%s,nice %d)",
			                           used ? " " : "", name,
			                           policy == SCHED_FIFO  ? "FIFO"
			                           : policy == SCHED_RR  ? "RR"
			                           : policy == SCHED_IDLE ? "idle"
			                           : policy == SCHED_BATCH ? "batch"
			                                                     : "normal",
			                           niceness);
	}
	if (folder)
		closedir(folder);

	/* ⛔ "I found no thread" is NOT "all is well": it is a blind instrument,
	 *    and it is said in those words (`CODER.md` §3.10). */
	if (watched == 0) {
		registro_dice(LOG_CHILD,
		              "⚠ I FOUND NO thread of the audio path "
		              "(looking for data-loop, pw-data, pw-rt, module-rt, "
		              "remotix-suono, remotix-cattura): ⛔ this is NOT the "
		              "measure «all is well», it is «I did not look».  "
		              "RLIMIT_RTPRIO = %lu",
		              cap);
		return;
	}

	if (realtime == watched)
		registro_dice(LOG_CHILD,
		              "⭐ real-time priority OBTAINED: %d threads out of %d of the "
		              "audio path run FIFO/RR (RLIMIT_RTPRIO = %lu).  %s",
		              realtime, watched, cap, listing);
	else
		registro_dice(
		    LOG_CHILD,
		    "⛔⛔ FIFO **NOT** OBTAINED: %d threads out of %d of the audio path run at "
		    "NORMAL policy (worst nice %d), and RLIMIT_RTPRIO = %lu — ⚠ the rlimit says «you can "
		    "ASK for it», not «you have it».  `[M]` 21 Aug 2026: on this kernel "
		    "`CONFIG_RT_GROUP_SCHED` with cgroup v2 refuses SCHED_FIFO to anyone not in the "
		    "ROOT cgroup ⇒ every process governed by systemd is excluded and `LimitRTPRIO=20` "
		    "is INERT.  ⇒ The audio will crackle WHEN THE DESKTOP IS WORKING, and with a still "
		    "desktop it does not reproduce.  ⚠ And the cure is not here: the independent referee "
		    "(`pw-record` on the same monitor) hears the same crackles at the same instants ⇒ the "
		    "defect is born in the SESSION's audio graph, not in our transport.  %s",
		    watched - realtime, watched, worst_nice == -100 ? 0 : worst_nice, cap,
		    listing);
}

static void audio_rule_child(uint8_t codec)
{
	if (codec == audio_codec)
		return;

	/* It always stops first: `sound_listen_stop()` WAITS for the PipeWire
	 * thread, and whoever returns from there is allowed to touch what the
	 * callback was using — the ring included. */
	if (audio_codec) {
		sound_listen_stop(snd);
		audio_enc_close(aenc);
		aenc = NULL;
		registro_dice(LOG_CHILD,
		              "audio turns OFF: %llu blocks sent, %llu lost, "
		              "%llu frames overflowed.  ⭐ The sink stays (I4)",
		              (unsigned long long)audio_blocks_sent,
		              (unsigned long long)audio_blocks_lost,
		              (unsigned long long)atomic_load(&audio_overflowed));
	}
	audio_codec = 0;

	if (!codec)
		return;

	/* ⛔ The sink is mounted ONLY ONCE for the life of the child. */
	if (!snd) {
		snd = sound_open();
		if (!snd) {
			/* ⚠ DECLARED FALLBACK (`CODER.md` §4.2): the desktop keeps
			 *   working without audio, and this line is the only difference
			 *   between "degraded" and "silently broken".  The log of the
			 *   reason has already been written by `sound_open()`. */
			registro_dice(LOG_CHILD,
			              "⛔ the audio sink does not mount: this session "
			              "stays WITHOUT SOUND.  ⚠ The desktop goes on — it is a "
			              "declared fallback, not a hushed-up fault");
			return;
		}
	}
	/* ⛔ Invariant I5: whoever connects finds the volume AT MAXIMUM.  It is
	 *    redone at every connection and not only at creation, because a slider
	 *    left low is a state the client can neither see nor explain. */
	sound_max_volume(snd);

	aenc = audio_enc_open(codec);
	if (!aenc) {
		registro_dice(LOG_CHILD,
		              "⛔ the audio encoder for codec %u does not open: "
		              "this session stays without sound", codec);
		return;
	}

	audio_ring_reset();
	if (!sound_listen_start(snd, audio_samples, NULL)) {
		registro_dice(LOG_CHILD,
		              "⛔ the monitor capture does not start: no sound");
		audio_enc_close(aenc);
		aenc = NULL;
		return;
	}
	/* ⛔⛔ AND IT IS CHECKED WHETHER REAL-TIME PRIORITY WAS OBTAINED, instead
	 *      of hoping for it — invariant I7: "the protection against a known
	 *      defect lives in the program, not in a configuration line that can
	 *      get lost".
	 *
	 *      ⚠ Here the configuration line is needed regardless (an rlimit is
	 *      granted by the unit, not by the code), ⇒ what the program can do is
	 *      **notice it is missing and say so**.
	 *
	 * ⛔ It is R26 of v1, `[M]` 5 Aug 2026 and found again on the 17th: with
	 *    `RLIMIT_RTPRIO` at zero PipeWire cannot ask for `SCHED_FIFO`, and its
	 *    data loop collects the samples at normal priority **while in this very
	 *    process the video encoder takes a core**.  The symptom is not an
	 *    error: it is audio that crackles **when the desktop is working**, and
	 *    that with a still desktop does not reproduce — that is invisible to
	 *    every bench that looks at bytes instead of time. */
	declare_audio_priority();

	audio_codec = codec;
	audio_blocks_sent = audio_blocks_lost = 0;
	registro_dice(LOG_CHILD,
	              "⭐ PHASE 7: audio turns ON — codec %u (%s), blocks of %u "
	              "frames, sink node %u",
	              codec, codec == 1 ? "Opus" : "PCM", audio_enc_block(aenc),
	              sound_node(snd));
}

/*
 * Empties the ring, one block at a time, and sends to the parent.
 *
 * ⛔ It is called on every round of the loop, BEFORE the video part: the video
 *    part exits with `continue` when nobody is watching, and audio would end
 *    up inside it by accident — that is, a session with audio on and video
 *    off would not play, and no line would say why.
 *
 * ⛔⭐ AND IT IS CALLED FROM TWO PLACES, not one: the other is the `continue`
 *     of the "no stage and SOMEONE IS WATCHING" branch, which would skip the
 *     first for the whole time the session is being born (`[M]` 27 Aug 2026:
 *     4 631 505 frames overflowed, 96 489 ms).  ⚠ "On every round" must be
 *     kept true: whoever adds an early exit to the loop must pass through
 *     here first.
 *
 * ⭐ And it is safe outside the stage: it exits at once if audio is not on,
 *   and touches neither the capture nor the canvas — only the ring, the audio
 *   encoder and the socket to the parent.
 */
static void audio_drain(void)
{
	uint32_t block;
	int16_t samples[AUDIO_BLOCK_OPUS * AUDIO_CHANNELS];
	uint8_t report[AUDIO_OUT_MAX];
	uint64_t overflowed;

	if (!audio_codec || !aenc)
		return;
	block = audio_enc_block(aenc);

	/* ⛔ The overflow is read HERE and not in the callback: there one cannot
	 *    write to the log without risking the desktop's frames. */
	overflowed = atomic_exchange(&audio_overflowed, 0);
	if (overflowed) {
		/* ⭐ And the clock base MOVES by the lost samples, or the `instant`
		 *    values would tell of a continuous sound where there was a gap —
		 *    and the client would reorder on a lie (§6.3). */
		audio_base_us += overflowed * 1000000u / AUDIO_FREQUENCY;
		registro_dice(LOG_CHILD,
		              "⚠ the audio ring overflowed by %llu frames "
		              "(%llu ms): the loop does not empty it fast enough.  "
		              "⛔ It is not the network: it is here",
		              (unsigned long long)overflowed,
		              (unsigned long long)(overflowed * 1000u / AUDIO_FREQUENCY));
	}

	while (audio_ready() >= block) {
		uint32_t queue = atomic_load_explicit(&audio_queue, memory_order_relaxed);
		size_t n = 0;
		uint64_t instant;

		for (uint32_t i = 0; i < block; i++) {
			uint32_t p = (queue + i) % AUDIO_RING_FRAMES;
			samples[i * AUDIO_CHANNELS] = audio_ring[p * AUDIO_CHANNELS];
			samples[i * AUDIO_CHANNELS + 1] = audio_ring[p * AUDIO_CHANNELS + 1];
		}
		atomic_store_explicit(&audio_queue,
		                      (queue + block) % AUDIO_RING_FRAMES,
		                      memory_order_release);

		if (!audio_base_us)
			audio_base_us = now_monotonic_us();
		instant = audio_base_us + audio_consumed * 1000000u / AUDIO_FREQUENCY;
		audio_consumed += block;

		if (audio_enc_pass(aenc, samples, report, &n)) {
			struct body_block c;
			memset(&c, 0, sizeof c);
			c.codec = audio_codec;
			c.byte = (uint32_t)n;
			c.instant_us = instant;
			/* ⛔ If it does not go out IT IS DROPPED and counted: §6.3 forbids
			 *    retransmission, and a child waiting to be able to write
			 *    would stop the desktop capture. */
			if (!send_msg(MSG_BLOCK, &c, sizeof c, report, n))
				audio_blocks_lost++;
			else
				audio_blocks_sent++;
		}
	}

	/* One line per second, with the ZEROS in it: "the loop does not run", "the
	 * session does not play" and "the blocks do not go out" must have three
	 * different faces (`CODER.md` §3.10). */
	{
		uint64_t t_now = now_monotonic_us();
		if (t_now - audio_logged_us >= 1000000u) {
			audio_logged_us = t_now;
			log_detail(LOG_CHILD,
			                   "audio: %llu blocks sent, %llu lost, "
			                   "%llu frames waiting in the ring — codec %u",
			                   (unsigned long long)audio_blocks_sent,
			                   (unsigned long long)audio_blocks_lost,
			                   (unsigned long long)audio_ready(), audio_codec);
		}
	}
}


static void survey_write(const char *dir, const char *name, const void *data,
                           size_t byte)
{
	char fpath[512];
	FILE *fp;
	size_t written;

	if (!dir || !dir[0] || strcmp(dir, "-") == 0)
		return;
	snprintf(fpath, sizeof fpath, "%s/%s", dir, name);
	fp = fopen(fpath, "wb");
	if (!fp) {
		/* ⚠ The CHILD writes there, that is the user: a folder of the parent
		 *   is not theirs, and the survey does not come out.  It is said,
		 *   instead of leaving a missing file looking like a survey nobody
		 *   asked for. */
		registro_dice(LOG_CHILD, "⛔ survey %s: %s (the user writes there, not root)",
		              fpath, strerror(errno));
		return;
	}
	written = fwrite(data, 1, byte, fp);
	if (fclose(fp) != 0 || written != byte) {
		registro_dice(LOG_CHILD, "⛔ survey %s: %zu bytes of %zu", fpath,
		              written, byte);
		return;
	}
	registro_dice(LOG_CHILD, "survey written: %s (%zu bytes)", fpath, byte);
}

/* ------------------------------------------------------------------ *
 *  ⭐ THE ON-DEMAND SNAPSHOT — `SIGUSR1` and `SIGUSR2`, 17 Aug 2026
 *
 *  It serves ONE thing: separating the three suspects of the 64 px block
 *  artefacts measured on the user's video (capture · encoder ·
 *  browser).  On `SIGUSR1` the child asks for a KEYFRAME and then puts on
 *  disk, from the same instant:
 *
 *    `shot-input.bgrx`  the pixels the encoder HAS IN HAND
 *    `shot-stream.obu`     the bytes we send, from the keyframe on
 *    `shot-output.bgrx`    the input of the LAST frame queued
 *
 *  ⇒ If the blocks are already in the BGRX, the fault is UPSTREAM of the
 *    encoder; if they appear only when decoding the stream with a
 *    different decoder, it is the ENCODER; if neither has them, the
 *    BROWSER remains.
 *
 *  ⛔ It is not a product switch: it writes only if `--survey` is there,
 *     it arms once per signal, and `SIGUSR2` closes it at once (without it,
 *     on a still scene one would wait for frames that do not arrive).
 * ------------------------------------------------------------------ */
#define SHOT_FRAMES 300

/* ⛔ AND IT KEEPS THE FOLDER ITSELF, instead of reading it from the parameter.
 *
 * `[M]` 17 Aug 2026, and the first snapshot was lost like this: in the main
 * ROUND `encode_and_send()` is called with `dir_survey = NULL` (the
 * `requested_codec` line) — the real folder arrives only at the first encoding,
 * the one at switch-on.  ⇒ `survey_write()` exited silently, and the log
 * line said "input 2560x962, 9850880 bytes" of a file that had not been
 * written: the worst form, a green that looked at nothing (`LESSONS.md`
 * §1.9). */
static const char *shot_dir = NULL;

static volatile sig_atomic_t shot_requested = 0;
static volatile sig_atomic_t shot_stop = 0;
static int shot_state = 0; /* 0 idle · 1 waiting for the keyframe · 2 queueing */
static int shots_left = 0;
static FILE *shot_fp = NULL;
static unsigned long long shot_count = 0;

static void shot_signal(int which)
{
	if (which == SIGUSR2)
		shot_stop = 1;
	else
		shot_requested = 1;
}

/* Closes the stream and writes the last input.  `why` ends up in the log,
 * so that a truncated survey is not mistaken for a finished one. */
static void shot_close(const char *dir_survey, const CaptureStopped *fo,
                          const char *why)
{
	if (shot_fp) {
		fclose(shot_fp);
		shot_fp = NULL;
	}
	shot_state = 0;
	shots_left = 0;
	if (fo && fo->pixel)
		survey_write(dir_survey, "shot-output.bgrx", fo->pixel,
		               (size_t)fo->byte);
	registro_dice(LOG_CHILD,
	              "⭐ SNAPSHOT FINISHED (%s): %llu frames in "
	              "`shot-stream.obu`, and `shot-output.bgrx` is the input "
	              "of the LAST of them",
	              why, shot_count);
}

/* ⛔ The same encoding request as `main.c` before 12 Aug 2026 —
 *    CRF 20, 10 bits asked on an 8-bit source (promotion DECLARED by the
 *    encoder), BGRx, keyframes on request.  ⚠ It was not "rewritten": it was
 *    MOVED, because the child is the one with the pixels.
 *
 * ⛔⭐ AND `chiavi_ogni = 0` STAYS ZERO, that is an infinite GOP, and it is a
 *     choice — not an oversight.  `RCP.md` §5.2 wants a keyframe in three
 *     cases only: the first after `SESSION`, the first at the new size, and
 *     when the client asks for it.  Periodic keyframes would be bandwidth
 *     spent on an insurance the protocol already buys — and `SPECS.md`
 *     §8.2 says bandwidth is spent on quality, not on caution.
 *
 *     ⛔ BUT THE PRICE IS THAT THE SEAM MUST EXIST: with an infinite GOP and
 *        nobody calling `codificatore_chiedi_chiave()`, after the first
 *        keyframe **not a single one ever arrives again**, and a client that
 *        loses a delta is left with a wrecked screen forever.  The caller is
 *        there now — `MSG_VIDEO` with `key = 1`, and the whole road is in
 *        the box of `wt_video_hook()`. */
/* ⛔⭐ THE RENDER NODE AND THE ENTRYPOINT — DECLARED HERE, NOT GUESSED AND
 *     NOT IN A CONFIGURATION LINE.
 *
 * `CODER.md` invariant I7: *"the protection against a known defect lives in
 * the program, not in a configuration line that can get lost"*.  A node taken
 * from an environment variable would vanish the day someone starts the
 * service by hand, and the symptom would be **the encoder in software with
 * the same label**: two different rates under the same name.
 *
 * ⭐ And the two numbers sit next to the line because this is a CHOICE, and a
 *    choice without the reckoning beside it is a preference:
 *
 *   `[M]` 13 Aug 2026, 1920×1080 10 bits, 120 frames, all at 20 Mbit/s,
 *   output frames COUNTED with `ffprobe`:
 *
 *     /dev/dri/renderD128   Intel iHD 25.2.3    EncSliceLP   ⭐ 3.16-3.24 ms
 *     /dev/dri/renderD129   AMD radeonsi 25.0.7 EncSlice        3.43 ms
 *     the software fallback (AV1 at the time)          an order of magnitude more
 *
 * ⚠ **And the two nodes are NOT two faces of the same card**: `renderD128` is
 *   the Intel iGPU (0000:00:02.0, i915), `renderD129` is a discrete **AMD
 *   Radeon RX 6800** (0000:03:00.0, amdgpu).  Whoever read "two nodes" as
 *   "two queues of the same GPU" would pick at random between two different
 *   machines.
 *
 * ⛔ **Why the Intel and not the AMD, which has the FULL entrypoint**: it is
 *    faster `[M]`, and above all it is **the card that composes the desktop**
 *    — that is the one on which the frames already are when phase 8 removes
 *    the copy.
 *    ⚠ The price is declared and not hidden: `EncSliceLP` is the **low
 *    power** encoding, it is not equivalent to the full one, and the quality
 *    comparison between the two at equal bitrate `[?]` **has not been
 *    measured**.
 */
#define RENDER_NODE "/dev/dri/renderD128"
/* ⭐ Phase 16, Radeon campaign: no longer a rigid `BASSA` but the written rule
 *    `LA_DICHIARATA` — *EncSliceLP if the driver declares it, otherwise full
 *    EncSlice* (see `PotenzaEntrypoint`).  On the Intel it is the same
 *    `EncSliceLP` as before; on the RX 6800 (radeonsi) `[M]` there is only
 *    `EncSlice`, and with `BASSA` the session dropped to SOFTWARE.  ⛔ The
 *    choice is made by the capability read from the driver, not by the card's
 *    name: which of the two is in force is said by the «encoder OPENED»
 *    line below, not by this one. */
#define RENDER_POWER ENCODER_POWER_DECLARED
/* ⛔ The constant QP, and it is NOT "the CRF 20 of before": they are two
 *    different quantities (see `ModoQualita` in `encoder.h`).  ⚠ The
 *    value is a declared placeholder — the working point between quality and
 *    bandwidth is phase 9, like the x265 preset. */
#define QP_HARDWARE 26
/* ⛔ Here there was `CRF_SOFTWARE`, the CRF of the software fallback: it left
 *    with it (phase 19, `DECISIONS.md` §10.27). */

/* ⛔ The entrypoint's name is PRINTED from `RENDER_POWER`, not written by
 *    hand in the log line: it is the same form E2 as the defect of 22 Aug
 *    ("hevc_vaapi" written inside the quotes while the one failing was
 *    `h264_vaapi") — a right line with the wrong name next to it sends the
 *    hunt the wrong way.  ⚠ `NON_DICHIARATA` is there because it is the
 *    zero, that is what one gets without writing it: if it appeared in the
 *    log it would already be the diagnosis. */
static const char *power_name(PotenzaEntrypoint p)
{
	switch (p) {
	case ENCODER_POWER_FULL:
		return "EncSlice (full)";
	case ENCODER_POWER_LOW:
		return "EncSliceLP (low power)";
	case ENCODER_POWER_DECLARED:
		return "EncSliceLP if the driver declares it, otherwise EncSlice (full) — "
		       "the one IN FORCE is told by the «encoder OPENED» line";
	default:
		return "NOT DECLARED (⛔ and so nothing opens)";
	}
}

/* ⛔⭐⭐ `RCP.md` §4.3 (line 701) — THE LEVEL PRODUCED, SAID IN THE ALPHABET IN
 *      WHICH THE CLIENT ASKS FOR IT.
 *
 *      §4.3: *"`video.level`: the maximum level it can decode, e.g. `5.1`.
 *      ⛔ The server MUST emit a stream of a level not higher, and does not
 *      guess it: a level declared too low does not give a network error, it
 *      makes the DECODER REFUSE THE CONFIGURATION and the symptom is "the
 *      browser does not open the stream" (finding O12)"*.
 *
 * ⛔ AND THE COMPARISON CANNOT BE MADE ON THE RAW NUMBER, because the three
 *    codecs write it in three different alphabets — and it is exactly the way
 *    a log line can be true and unreadable at the same time:
 *
 *      H.264   `level_idc`         = major*10 + minor       ⇒ 5.1 is **51**
 *      HEVC    `general_level_idc` = (major*10+minor)*3     ⇒ 5.1 is **153**
 *      AV1     `seq_level_idx`     = (major−2)*4+minor      ⇒ 5.1 is **13**
 *
 *    ⇒ "level 51" and "level 153" are the SAME level, and whoever reads the
 *      log next to a `video.level=5.1` must be able to see it without a
 *      table in hand.  Here it comes out in TENTHS, which is the form of §4.3
 *      and the same in which `rcp.c` reads the client's capability.
 *
 * ⚠ Returns 0 when it cannot translate — and zero is NOT "low": it is "I don't
 *   know", and the line printing it writes it in those words.  ⚠ H.264 also
 *   has level "1b", which `level_idc` does not distinguish from 1.1 without
 *   looking at another field: it is outside any canvas this product serves,
 *   and it is declared here instead of pretending it does not exist. */
static unsigned level_in_tenths(CodecVideo codec, int stream_level)
{
	if (stream_level <= 0)
		return 0;
	switch (codec) {
	case CODIFICATORE_H264:
		return (unsigned)stream_level;
	case CODIFICATORE_HEVC:
		return (unsigned)stream_level / 3u;
	case CODIFICATORE_AV1:
		return ((unsigned)stream_level / 4u + 2u) * 10u
		       + (unsigned)stream_level % 4u;
	default:
		return 0;
	}
}

/* ⛔ The number of §6.2 and the encoder's codec are two different alphabets,
 *    and the translation lives in ONE function: the day they diverged, a
 *    single line would be what diverges.  ⚠ An unknown number does NOT become
 *    a codec "so as to go on": it is declared and nothing is encoded. */
static CodecVideo codec_from_number(uint8_t nr)
{
	switch (nr) {
	case 1:
		return CODIFICATORE_HEVC;
	case 2:
		return CODIFICATORE_AV1;
	case 3:
		return CODIFICATORE_H264;
	default:
		registro_dice(LOG_CHILD,
		              "⛔ unknown codec number (%u): §6.2 knows three, and I do not "
		              "invent a fourth",
		              nr);
		return (CodecVideo) 0;
	}
}

/* Why the hardware did not open, the last time it was tried ("" if it opened,
 * or if it was not tried). */
static char hardware_refusal[512];

/* ⭐ PHASE 18 — the node on which the card is opened.  ⛔ No environment
 *    variable touches it.  (`--software`, which skipped the card to try the
 *    fallback, left with the fallback: phase 19.)
 * ⭐⭐ 1.5 (SPECS audit, 15 Oct 2026) — NO LONGER ALWAYS `RENDER_NODE`.  With
 *    two cards `renderD128` is the one the KERNEL numbered first, not the one
 *    the compositor draws on (cross-card import: it fails or it is slow).
 *    In the session, `choose_render_node()` takes, in this order:
 *      1. the compositor's card — `linux-dmabuf` v4 `main_device`
 *         (`render_node.c`);
 *      2. `--render-node /dev/dri/renderDN` (the server's option, repeated to
 *         the child like `--encoding-route`);
 *      3. `RENDER_NODE`.
 *    ⚠ On a one-card machine the three are the same node: nothing changes.
 *    ⚠ The parent's startup measure (`capabilities_video_measure()`) has no
 *      compositor yet: it runs on 2 or 3.  `--encoding-test --node …` still
 *      forces a node for the test. */
static char render_node_buf[64] = RENDER_NODE;
static const char *nodo_rendering = render_node_buf;
/* `--render-node`, "" = not given */
static char render_node_option[64];
/* the session's choice is made: it does not move under an open encoder */
static bool render_node_latched;
/* true only in `child_alive()`: the parent's measure and `--encoding-test` have
 * no compositor to ask */
static bool in_session_child;

/* ⭐ 1.5 (review of 13422add) — a `--render-node` that is not a DRM card is
 *    REFUSED, and the refusal is SAID once: dropped in silence, the session
 *    would go to `RENDER_NODE` and nobody would know the option was ignored
 *    (the parent stops with a usage error; the child, which receives it
 *    repeated, may live in a box where the path does not exist). */
bool child_render_node(const char *node)
{
	static bool refusal_said;
	char why[128] = "";

	if (node && strlen(node) >= sizeof render_node_option)
		snprintf(why, sizeof why, "longer than %zu characters", sizeof render_node_option - 1);
	if (why[0] || !render_node_is_drm(node, why, sizeof why)) {
		if (!refusal_said) {
			refusal_said = true;
			registro_dice(LOG_CHILD,
			              "⛔ --render-node «%.64s» REFUSED (%s): it is not a DRM card "
			              "(a character device with major %u under /dev/dri/) — the "
			              "encoding card stays the compositor's, or %s",
			              node ? node : "(null)", why, RENDER_NODE_DRM_MAJOR,
			              render_node_option[0] ? render_node_option : RENDER_NODE);
		}
		return false;
	}
	snprintf(render_node_option, sizeof render_node_option, "%s", node);
	snprintf(render_node_buf, sizeof render_node_buf, "%s", node);
	return true;
}

const char *child_render_node_requested(void)
{
	return render_node_option;
}

/* ⭐ 1.5 — the node the parent's startup measure tested (the codecs offered
 *    in HERE_I_AM are true THERE): `--render-node`, otherwise `RENDER_NODE`. */
static const char *startup_node(void)
{
	return render_node_option[0] ? render_node_option : RENDER_NODE;
}

/*
 * ⭐ 1.5 — the session's card, chosen ONCE and said ONCE (with PCI address,
 *    driver and vendor:device, because «renderD129» alone does not say which
 *    machine it is).
 * ⚠ `final` = latch even without an answer: the encoder is about to open,
 *   and the node must not move under it.  Without `final`, a compositor not
 *   yet reachable (labwc still being born) is asked again at the next mount.
 */
static void choose_render_node(bool final)
{
	char node[64], why[256] = "", desc[160];
	const char *come;
	bool reached = false;

	if (render_node_latched)
		return;
	if (render_node_of_compositor(node, sizeof node, why, sizeof why, &reached)) {
		if (render_node_option[0] && !render_node_same(render_node_option, node))
			registro_dice(LOG_CHILD,
			              "⚠ --render-node %s is NOT the compositor's card (%s): the "
			              "frames are on the compositor's, and the encoder goes there",
			              render_node_option, node);
		snprintf(render_node_buf, sizeof render_node_buf, "%s", node);
		come = "the compositor's card (linux-dmabuf main_device)";
	} else {
		if (!reached && !final)
			return; /* asked again at the next mount */
		snprintf(render_node_buf, sizeof render_node_buf, "%s",
		         render_node_option[0] ? render_node_option : RENDER_NODE);
		come = render_node_option[0] ? "--render-node" : "the default " RENDER_NODE;
	}
	render_node_latched = true;
	render_node_describe(render_node_buf, desc, sizeof desc);
	registro_dice(LOG_CHILD, "⭐ the encoding card: %s (%s) — from %s%s%s", render_node_buf,
	              desc, come, why[0] ? "; the compositor did not say it: " : "", why);
}

/* ⭐ PHASE 19 — THE CARD'S ROUTE (`DECISIONS.md` §10.27).  `card` = chosen BY
 *    CAPABILITY (Vulkan Video if available for that codec, otherwise VA-API),
 *    and it is what the product does; `vulkan`/`vaapi` = that one and nothing
 *    else, for tests and diagnosis (`--encoding-route`, from the command line of the
 *    server and of `--encoding-test`).  The component's name is born here:
 *    `h264_card`, `hevc_vulkan`, … (`encoder.h`).  ⛔ The parent passes
 *    it to the child on the command line (`figli_esegui`): the child is an
 *    exec, and a static of the parent does not reach this side. */
static const char *encode_route = "card";

bool child_encoding_route(const char *route)
{
	if (!route || (strcmp(route, "card") && strcmp(route, "vulkan") && strcmp(route, "vaapi")))
		return false;
	encode_route = route;
	return true;
}

const char *child_encoding_route_requested(void)
{
	return encode_route;
}

/*
 * ⛔ PHASE 19 — THE SLABS OF `wlroots.c` AND THE ENCODING ROUTE (1 Oct 2026).
 *    With Vulkan encoding the GBM slabs must be born at the maximum canvas and
 *    not die at a size change (the Radeon GPU hang: box of `WLR_SLAB_W` in
 *    `wlroots.c`); with VA-API not.  ⇒ It is decided ONCE, before the first
 *    stage, with the same rule as the components (`component_of()`):
 *    "vulkan" yes, "vaapi" no, "card" = what the node's card declares
 *    (`encoder_vulkan_on_node`).
 */
static void slabs_per_route(void)
{
	/* ⭐ 1.5 (review of 13422add): decided ONCE — but a decision taken while
	 *    the compositor did not answer yet (labwc still being born) is
	 *    PROVISIONAL: it was taken on `--render-node`/`RENDER_NODE`, and the
	 *    next mount (before the encoder opens) takes it again on the card
	 *    the compositor names.  ⚠ The setter is read at `capture_start_wlr()`:
	 *    redoing it here, before the next start, is in time. */
	static bool decided = false, provisional = false, was = false;
	bool vulkan;

	choose_render_node(false);
	if (decided && !provisional)
		return;
	if (decided && !render_node_latched)
		return; /* still no answer: the provisional one stands */
	if (!strcmp(encode_route, "vulkan"))
		vulkan = true;
	else if (!strcmp(encode_route, "vaapi"))
		vulkan = false;
	else {
		vulkan = encoder_vulkan_on_node(nodo_rendering);
		/* ⚠ Two cards, and the encoder may fall back to the startup one
		 *   (`node_of_codec()`): the big slabs if EITHER encodes in Vulkan.
		 *   On one card it is the same question, asked once. */
		if (!vulkan && in_session_child && !render_node_same(nodo_rendering, startup_node()))
			vulkan = encoder_vulkan_on_node(startup_node());
	}
	if (decided && vulkan == was) {
		provisional = !render_node_latched;
		return; /* the same answer: nothing to say again */
	}
	decided = true;
	was = vulkan;
	provisional = !render_node_latched;
	wlr_slabs_at_max_canvas(vulkan);
	registro_dice(LOG_CHILD,
	              "⭐ PHASE 19: the slabs of the wlroots capture %s (route requested «%s», node %s)%s",
	              vulkan ? "are born at the MAXIMUM CANVAS and stay on a size change — the "
	                       "encoding will be Vulkan (the Radeon GPU hang)"
	                     : "are of the right size and are redone on a change — the encoding "
	                       "will be VA-API",
	              encode_route, nodo_rendering,
	              provisional ? " — ⚠ PROVISIONAL: the compositor did not answer yet, "
	                            "decided again at the next mount" : "");
}

/*
 * ⭐ 6 Oct 2026 — THE CARD'S ROUTE WHERE LINEAR IS NOT AVAILABLE (Mutter and KWin).
 * `[M]` NVIDIA (driver 595) + GNOME 50: the usual proposal (LINEAR, then
 * INVALID) ended in "no more input formats" and the session stayed BLACK.
 * ⇒ If the card refuses linear (the same question as `wlroots.c`), the
 *   proposal also offers the modifiers the Vulkan encoder imports.
 * ⛔ Where linear succeeds nothing changes: no extra modifier.
 */
static void modifiers_per_route(void)
{
	/* ⭐ 1.5: PROVISIONAL like `slabs_per_route()` while the compositor has
	 *    not answered — the card asked may not be the one that encodes. */
	static bool decided = false, provisional = false;
	static char asked[64];
	uint64_t m[16];
	int n = 0;

	choose_render_node(false);
	if (stage_route != CAPTURE_ROUTE_CARD)
		return;
	if (decided && (!provisional || !render_node_latched))
		return;
	provisional = !render_node_latched;
	if (decided && !strcmp(asked, nodo_rendering))
		return; /* the same card: the same answer */
	if (decided)
		capture_modifiers_card(NULL, 0); /* the provisional list goes */
	decided = true;
	snprintf(asked, sizeof asked, "%s", nodo_rendering);
	if (!vulkanvideo_card_rejects_linear(nodo_rendering))
		return;
	n = vulkanvideo_modifiers(nodo_rendering, DRM_FORMAT_XRGB8888, m, (int)G_N_ELEMENTS(m));
	if (n < (int)G_N_ELEMENTS(m)) {
		uint64_t a[16];
		int na = vulkanvideo_modifiers(nodo_rendering, DRM_FORMAT_ARGB8888, a,
		                                  (int)G_N_ELEMENTS(a));
		for (int i = 0; i < na && n < (int)G_N_ELEMENTS(m); i++) {
			bool already = false;
			for (int j = 0; j < n; j++)
				already = already || m[j] == a[i];
			if (!already)
				m[n++] = a[i];
		}
	}
	capture_modifiers_card(m, n);
	registro_dice(LOG_CHILD,
	              "⭐ the card %s REFUSES the linear slab (NVIDIA): the capture's "
	              "proposal also offers the %d modifiers the Vulkan encoder "
	              "imports%s%s",
	              nodo_rendering, n,
	              n ? "" : " — ⛔ none: the memory fallback remains if the compositor refuses",
	              provisional ? " — ⚠ PROVISIONAL: the compositor did not answer yet, "
	                            "decided again at the next mount" : "");
}

/* The name of the component to request for `codec` on the route in force. */
static const char *component_of(CodecVideo codec)
{
	static char name[2][32];
	int which = codec == CODIFICATORE_H264 ? 0 : 1;

	snprintf(name[which], sizeof name[which], "%s_%s", codec == CODIFICATORE_H264 ? "h264" : "hevc",
	         encode_route);
	return name[which];
}

static const char *node_of_codec(CodecVideo codec, uint8_t idx, uint8_t depth);

static Encoder *encoder_of(CodecVideo codec, uint8_t idx,
                                     uint32_t canvas_w, uint32_t canvas_h)
{
	CodificatoreRichiesta r;
	char error[512];
	uint8_t prof = requested_depth;

	if (idx >= CODEC_MAX)
		return NULL;
	/* ⭐ 1.5: in the session, the card is latched before the first opening. */
	if (in_session_child)
		choose_render_node(true);

	/* ⛔⭐ WITHOUT A NEGOTIATED DEPTH NOTHING OPENS, and it is not caution:
	 *     opening one "just because" would mean choosing ourselves what §4.3
	 *     makes the parent choose — that is putting the literal back under
	 *     another name.
	 * ⚠ In practice it is never reached: `MSG_VIDEO` carries the two numbers
	 *   together, and the loop does not capture until it has arrived.  The
	 *   line is there so that the day it were reached someone would say so. */
	if (prof != 8 && prof != 10) {
		registro_dice(LOG_CHILD,
		              "⛔ no encoder: the parent did not say which "
		              "depth was negotiated (§4.3, I have «%u»).  ⚠ I do NOT "
		              "choose one myself: it would be the lie of 17 August put back by "
		              "hand",
		              prof);
		return NULL;
	}

	/* ⛔⭐ AND IF THE DEPTH HAS CHANGED, THE ENCODER IS REDONE.
	 *
	 *     The stage outlives the client (I4): the second to connect may have
	 *     negotiated 8 where the first had 10.  ⚠ Keeping the old one, the
	 *     stream would stay at the depth of the FIRST and the second would see
	 *     artefacts — that is the same defect as tonight, with another cause.
	 * ⛔ And the next frame must be a KEYFRAME: a new encoder does not have the
	 *    stream's past (§5.2). */
	if (enc[idx] && enc_profile[idx] != prof) {
		registro_dice(LOG_CHILD,
		              "⭐ the negotiated depth has changed (%u → %u): redoing "
		              "encoder %u, and the next frame will be a "
		              "KEYFRAME (§5.2)",
		              enc_profile[idx], prof, idx);
		codificatore_libera(enc[idx]);
		enc[idx] = NULL;
		enc_profile[idx] = 0;
		key_debt[idx] = true;
	}
	/* ⛔⭐ AND THE SAME FOR THE LEVEL (§4.3 line 701) — 23 Aug 2026.  The level
	 *     is set at the encoder's OPENING and ends up in the SPS: changing it
	 *     with the encoder open does not change it in the stream.  ⇒ The
	 *     second client declaring a ceiling different from the first brings
	 *     along a new encoder, or it would see the ceiling of the FIRST — and
	 *     the symptom, again, would be a black screen without a line. */
	if (enc[idx] && enc_fmt[idx] != input_format) {
		registro_dice(LOG_CHILD,
		              "⭐ the capture's channel order has changed (%s → %s): "
		              "redoing encoder %u, and the next frame will be "
		              "a KEYFRAME (§5.2)",
		              enc_fmt[idx] == CODIFICATORE_PIXEL_RGBX ? "RGBx" : "BGRx",
		              input_format == CODIFICATORE_PIXEL_RGBX ? "RGBx" : "BGRx",
		              idx);
		codificatore_libera(enc[idx]);
		enc[idx] = NULL;
		enc_profile[idx] = 0;
		enc_level[idx] = 0;
		key_debt[idx] = true;
	}
	if (enc[idx] && enc_level[idx] != requested_level_x10) {
		registro_dice(LOG_CHILD,
		              "⭐ §4.3: the level ceiling has changed (%u.%u → %u.%u, "
		              "0.0 = no ceiling): redoing encoder %u, and the "
		              "next frame will be a KEYFRAME (§5.2)",
		              enc_level[idx] / 10u, enc_level[idx] % 10u,
		              requested_level_x10 / 10u, requested_level_x10 % 10u,
		              idx);
		codificatore_libera(enc[idx]);
		enc[idx] = NULL;
		enc_profile[idx] = 0;
		enc_level[idx] = 0;
		key_debt[idx] = true;
	}
	if (enc[idx])
		return enc[idx];

	/* ⛔⭐ AND IT IS NOT RETRIED AT EVERY FRAME — see `enc_retry_ms`.  ⚠ The
	 *    silence here is intended and limited: the line explaining the failure
	 *    was already written by the previous attempt, and repeating it sixty
	 *    times a second is the defect this wait exists to avoid. */
	if (enc_retry_ms[idx] && log_now_ms() < enc_retry_ms[idx])
		return NULL;

	memset(&r, 0, sizeof r);
	r.codec = codec;
	r.componente = NULL;
	r.width = canvas_w;
	r.height = canvas_h;
	/* ⛔ The rate is ONE, and the same one asked of the capture. */
	r.fotogrammi_al_secondo = MOTION_FPS;
	/* ⛔ On the card there is no CRF: QP is asked, and QP is written. */
	r.mode = CODIFICATORE_QUALITA_QP;
	r.quality = QP_HARDWARE;
	/* ⛔⭐⭐ HERE THERE WAS `10`, WRITTEN BY HAND — and it is the defect measured
	 *      on 17 Aug 2026 on Firefox: 8 was declared in `HERE_I_AM` (§4.3) and 10
	 *      were sent on the wire.  ⇒ Now it is what the parent negotiated, and
	 *      the line above refuses to open if it does not know it. */
	r.depth = prof;
	/* ⛔⭐⭐ THE CEILING OF §4.3, AND IT IS ASKED BEFORE INSTEAD OF DISCOVERED
	 *      AFTER — 23 Aug 2026.  Until tonight nobody asked for it: the encoder
	 *      chose the level from size and rate, and at 3840x2160 at 60/s it
	 *      chose **5.2** while the client had declared 5.1.
	 *
	 * ⛔ THE FALSIFIABLE PREDICTION, which is the point of the whole cure:
	 *      at 3840x2160 with `video.level=5.1` imposed, the SPS MUST carry
	 *      `level_idc = 51` (H.264) / `general_level_idc = 153` (HEVC), and
	 *      the «§4.3 — LIVELLO» line below must say **5.1 ≤ 5.1 ✓**.
	 *      ⚠ If the encoder had NOT obeyed, that line would say **5.2 > 5.1**
	 *      with a ⛔ in front — that is tonight's defect, identical, but named
	 *      by a line instead of by a black screen.
	 *      ⭐ It is R31 in its purest form: ask by name, and verify by reading
	 *      back the bytes produced.
	 *
	 * ⚠⚠ AND WHAT IT COSTS, said and not hidden: a level is also a ceiling on
	 *     PIXELS and RATE.  H.264 5.1 grants `MaxMBPS = 983 040`; at 3840x2160
	 *     a frame is 32 400 macroblocks ⇒ a ceiling of **~30 fps**, while
	 *     `MOTION_FPS` asks for 60 (5.2 would grant 64).
	 *     ⛔ Imposing the level does NOT lower the rate — the encoder prints 51
	 *     in the SPS and goes on at 60 — so what is seen does not change (and
	 *     that is why the cure is not under I6).  ⚠ But the stream declares a
	 *     level whose rate limits it does NOT respect: it is exactly what the
	 *     client ASKED for by declaring 5.1 at 4K, and it is something to write
	 *     down, not to hide.  ⇒ The alternative — halving the rate to 30 —
	 *     would change what is seen, and that one would indeed need a switch:
	 *     it is not done here.
	 *
	 * ⚠ `0` = the client declared nothing (§4.3 does not require it): no
	 *   ceiling, the encoder chooses, and the chosen level is WRITTEN anyway —
	 *   whoever reads the log must know what came out. */
	r.livello_x10 = (int) requested_level_x10;
	r.fmt = input_format;
	r.chiavi_ogni = 0;

	/*
	 * ⭐⭐ THE CARD, AND NOTHING ELSE — phase 19 (1 Oct 2026, `DECISIONS.md`
	 *     §10.27), the user's words: *"no cpu without a card"*.
	 *
	 * HEVC and H.264 open on the card (`hevc_vaapi`/`h264_vaapi` on
	 * `nodo_rendering`), with QP and not CRF.  `[M]` 13 Aug 2026: `h264_vaapi`
	 * **3.11-3.16 ms** per frame at 1920x1080 10 bits.  ⛔ If the card does not
	 * open we NO longer drop to a software encoder (OpenH264 and SVT-AV1 have
	 * left the product): the codec is not available on this machine, and that
	 * is said.  ⚠ It should not even get here: the parent tries it AT STARTUP
	 * (`child_video_capabilities()`) and offers in `HERE_I_AM` only what the card can
	 * do — a browser that negotiates it anyway sees this line, and the code
	 * 0x06 of §6.2 after the wait.  ⛔ The codec is not changed under the
	 * client: it chose it (§4.3).
	 *
	 * ⚠ AV1: `[M]` 13 Aug 2026 `av1_vaapi` exits with *"No usable encoding
	 *   profile found"*, and `vainfo` gives AV1 as decode-only on both nodes
	 *   ⇒ AV1 on the card is not available, and in software no longer either.
	 */
	if (codec == CODIFICATORE_HEVC || codec == CODIFICATORE_H264) {
		/* ⭐ Phase 19: `h264_card`/`hevc_card` — the route is chosen by the
		 *    encoder by capability (Vulkan first, VA-API after), or the one
		 *    forced with `--encoding-route`.  Which one came out is told by the name. */
		r.componente = component_of(codec);
		/* ⭐ 1.5: the session's card, unless the codec is not there
		 *    (`node_of_codec()`: tested once, then the startup card). */
		r.nodo_rendering = node_of_codec(codec, idx, prof);
		r.power = RENDER_POWER;
		enc[idx] = codificatore_nuovo(&r, error, sizeof error);
		/* The reason also stays outside the log: `--encoding-test` reports it
		 * in its `reason`. */
		snprintf(hardware_refusal, sizeof hardware_refusal, "%s",
		         enc[idx] ? "" : error);
		/* ⭐ 6 Oct 2026, `[M]` RTX 4090: the thirteenth concurrent encoding
		 *    returns VK_ERROR_TOO_MANY_OBJECTS.  The card is there and it is
		 *    FULL: saying "this codec is not available" would be false, and the
		 *    retry below picks it up as soon as a slot frees up. */
		if (!enc[idx] && strstr(hardware_refusal, "TOO_MANY_OBJECTS"))
			snprintf(error, sizeof error,
			         "«%s» on %.40s did not open (%.150s) ⇒ the card is there but has RUN OUT "
			         "of encoding slots (the driver's limit: `[M]` 12 at once on the "
			         "RTX 4090) — the session stays without an image until a slot "
			         "frees up",
			         r.componente, r.nodo_rendering, hardware_refusal);
		else if (!enc[idx])
			snprintf(error, sizeof error,
			         "«%s» on %.40s did not open (%.150s) ⇒ this codec is NOT available on "
			         "this machine: without a card there is no encoding (phase 19)",
			         r.componente, r.nodo_rendering, hardware_refusal);
	} else {
		snprintf(hardware_refusal, sizeof hardware_refusal,
		         "codec %d is not encoded on the card (AV1: decode only)",
		         (int) codec);
		snprintf(error, sizeof error, "%.400s — and without a card there is no encoding (phase 19)",
		         hardware_refusal);
	}
	if (enc[idx]) {
		enc_profile[idx] = prof;
		enc_level[idx] = requested_level_x10;
		enc_fmt[idx] = input_format;
	}
	if (!enc[idx]) {
		/* ⛔ The wait grows, and the line SAYS so: without it, this branch wrote
		 *    the log in bursts and burned a core — the same form as the 30.8 GB
		 *    of 14 August, in another point of the loop. */
		enc_wait_ms[idx] = enc_wait_ms[idx]
		                              ? enc_wait_ms[idx] * 2
		                              : ENC_RETRY_MIN_MS;
		if (enc_wait_ms[idx] > ENC_RETRY_MAX_MS)
			enc_wait_ms[idx] = ENC_RETRY_MAX_MS;
		enc_retry_ms[idx] = log_now_ms() + enc_wait_ms[idx];
		registro_dice(LOG_CHILD,
		              "⛔ no video for codec %d: %s.  ⚠ Retrying in %llu "
		              "ms — not at every frame, or it would be sixty contexts "
		              "opened and closed per second",
		              (int)codec, error,
		              (unsigned long long)enc_wait_ms[idx]);
		return NULL;
	}
	/* ⭐ Succeeded: the wait is reset, or the next failure would start from the
	 *    bottom of the previous one. */
	enc_retry_ms[idx] = 0;
	enc_wait_ms[idx] = 0;
	/* ⭐ And the name carries the EFFECTIVE entrypoint (with node and vendor),
	 *    not the requested one: with `LA_DICHIARATA` they are two different
	 *    things until the driver has answered, and this is the line that says
	 *    it. */
	registro_dice(LOG_CHILD,
	              "⭐ PHASE 3: encoder %d OPENED and KEPT ALIVE from one "
	              "frame to the next, %ux%u at %d/s — without this "
	              "prediction would not exist and every frame would be a "
	              "keyframe · route %s (requested «%s») · in force: %s",
	              (int)codec, canvas_w, canvas_h, MOTION_FPS,
	              encoder_route(enc[idx]), encode_route,
	              encoder_name(enc[idx]));
	return enc[idx];
}

static void encoders_free(void)
{
	for (uint8_t i = 0; i < CODEC_MAX; i++) {
		if (!enc[i])
			continue;
		codificatore_libera(enc[i]);
		enc[i] = NULL;
	}
}

/*
 * ⭐ PHASE 17 (§6.5-bis, §6.0 phase 7a) — `remotix --encoding-test`.
 *
 * The installer's certification must know whether this machine really
 * encodes a frame in H.264 on the card: the answer is given by the product,
 * with its own choice, not by a separate program.  ⇒ It goes through
 * `encoder_of()`, that is the road of a real session (H.264, 8 bits — the
 * baseline of §4.3 —, no level ceiling, BGRx): `h264_vaapi` on
 * `RENDER_NODE` with `RENDER_POWER` and `QP_HARDWARE`.  Then a
 * synthetic 256x256 frame is really encoded, until bytes come out (at most 8
 * rounds).
 *
 * ⛔ PHASE 19 (1 Oct 2026, `DECISIONS.md` §10.27) — *"no cpu without a
 *    card"*: if the card does not open there is no longer the software
 *    fallback (OpenH264), and the test DECLARES it with a code of its own.
 *
 * It exits with ONE JSON line on stdout (the log goes to stderr, as always):
 *   {"outcome":"hardware"|"none","encoder":"h264_vulkan"|"h264_vaapi"|"",
 *    "route":"vulkan"|"vaapi"|"",
 *    "node":"/dev/dri/renderD128"|"","reason":"...",
 *    "codec":"h264"|"hevc","offered":"hevc,h264"|"h264"|"",
 *    "hevc":"hardware"|"none","h264":"hardware"|"none",
 *    "hevc_strada":"vulkan"|"vaapi"|"","h264_strada":…}
 *   ⭐ PHASE 19: `route` and `*_strada` say WHICH route of the card encoded
 *   (`DECISIONS.md` §10.27: Vulkan Video first, VA-API after); yesterday's
 *   fields stay as they were and the installer reads `outcome` and the code.
 * and the exit code:
 *    0  the card encoded a frame, and the bytes read back;
 *    1  the card opens but the frame does not come out, or it is not known
 *       whether it is right;
 *    2  usage error;
 *    3  ⛔ NO CARD CAN ENCODE this codec (no node, no driver, a driver without
 *       encoding): REMOTIX does not encode here.
 *
 * THE OPTIONAL ARGUMENTS, after `--encoding-test`:
 *      h264 | hevc          which codec to try (default h264, the baseline of §4.3)
 *      --node /dev/dri/…    the card to try instead of RENDER_NODE (the
 *                           second card of a machine that has two, or a
 *                           node that does not exist to try the refusal)
 *      --encoding-route vaapi|vulkan|card   ⭐ phase 19: the route, forced (the two)
 *                           or by capability (`card`, the default)
 *    Without arguments it is the installer's call.  `offered` is what the
 *    server WOULD OFFER to the browser with these same arguments.
 *
 * ⛔ "hardware" is said ONLY if the component accepts VA-API surfaces
 *    (`codificatore_in_hardware`) AND a frame came out with bytes AND the
 *    bytes were read back (`read_from_stream`).  Everything not known becomes
 *    "none" with the reason — never a presumed hardware.
 * ⚠ Root is not needed, but permissions matter: without the node's group
 *   (`render`) a user will see "none" where root would see "hardware".  The
 *   test must be done with the identity one wants to know about.
 */
#define PROBE_SIDE 256u
#define PROBE_ROUNDS 8
#define PROBE_NO_CARD 3

/* ⭐ What this machine's card can do, codec by codec: it is the same question
 *    as `--encoding-test`, asked at startup by the parent to decide what to
 *    offer in `HERE_I_AM` (`child_video_capabilities()`). */
typedef struct {
	bool hevc_card;          /* the card opens and encodes HEVC on `node` */
	bool h264_card;          /* H.264 likewise */
	char node[64];
	char why_hevc[768];     /* the reason, when not */
	char why_h264[768];
	char route_hevc[16];      /* ⭐ phase 19: "vulkan" / "vaapi" when yes, "" when not */
	char route_h264[16];
} VideoCapabilities;

/* ⭐ The frames of the test, on an encoder already open: a synthetic frame is
 *    encoded until bytes come out (at most `PROBE_ROUNDS`), and "yes" only if
 *    the confession says it obeyed, read back and is on the card.  ⚠ Shared
 *    by `test_codec()` (startup, `--encoding-test`) and `node_of_codec()`
 *    (the session's card, 1.5): ONE test, not two that drift apart. */
static bool probe_frames(Encoder *cod, char *reason, size_t n, size_t *bytes_out)
{
	static uint8_t pixel[PROBE_SIDE * PROBE_SIDE * 4];
	EncoderFrame fg;
	const EncoderConfession *c;
	bool has_exited = false;

	*bytes_out = 0;
	for (int cur_round = 0; cur_round < PROBE_ROUNDS && !has_exited; cur_round++) {
		/* A scrolling gradient: every frame differs from the previous one. */
		for (uint32_t y = 0; y < PROBE_SIDE; y++)
			for (uint32_t x = 0; x < PROBE_SIDE; x++) {
				uint8_t *p = pixel + (y * PROBE_SIDE + x) * 4;

				p[0] = (uint8_t)(x + cur_round * 8);
				p[1] = (uint8_t)y;
				p[2] = (uint8_t)(x ^ y);
				p[3] = 0xff;
			}
		memset(&fg, 0, sizeof fg);
		if (!codificatore_comprimi(cod, pixel, PROBE_SIDE * 4, &fg)) {
			c = codificatore_confessione(cod);
			snprintf(reason, n, "«%s» opens but frame %d does not encode%s%s",
			         encoder_name(cod), cur_round + 1, c && c->why_no[0] ? ": " : "",
			         c && c->why_no[0] ? c->why_no : "");
			return false;
		}
		if (fg.byte > 0) {
			has_exited = true;
			*bytes_out = fg.byte;
		}
		codificatore_rilascia(cod);
	}
	c = codificatore_confessione(cod);
	if (!has_exited || !c || !c->has_obeyed || !c->read_from_stream
	    || !codificatore_in_hardware(cod)) {
		snprintf(reason, n, "«%s» opens but after %d frames it is not known whether it encodes: %s",
		         encoder_name(cod), PROBE_ROUNDS,
		         !has_exited ? "no byte came out"
		         : !c || !c->has_obeyed ? "the encoder did not obey"
		         : !c->read_from_stream  ? "the bytes do not read back"
		                                 : "it is not on the card");
		return false;
	}
	return true;
}

/* Opens the card for `codec` and encodes until bytes come out.  ⚠ It goes
 * through `encoder_of()`, that is the session's road: it is the same
 * test the child will do.  The encoder stays open in `enc[]` (for the
 * confession): the caller frees it.  `*is_opened` says whether the card opened —
 * the "no" of one that does not open and that of one that does not encode
 * are two different codes of `--encoding-test`. */
static bool test_codec(CodecVideo codec, uint8_t idx, char *reason, size_t n,
                           size_t *bytes_out, bool *is_opened)
{
	Encoder *cod;

	*bytes_out = 0;
	*is_opened = false;
	requested_depth = 8;
	requested_level_x10 = 0;
	input_format = ENCODER_PIXEL_BGRX;
	/* ⚠ It is REALLY tried, even if a round before already said no: the wait
	 *   between two attempts belongs to the session, not to the test — and
	 *   the reason is reset, or the one of the codec tried before would be
	 *   read. */
	enc_retry_ms[idx] = 0;
	enc_wait_ms[idx] = 0;
	hardware_refusal[0] = 0;
	cod = encoder_of(codec, idx, PROBE_SIDE, PROBE_SIDE);
	if (!cod) {
		snprintf(reason, n,
		         "no card can encode %s: «%s» on %s does not open (%s).  ⛔ REMOTIX "
		         "encodes only on the card (phase 19): without it, there is no video",
		         codec == CODIFICATORE_HEVC ? "HEVC" : "H.264", component_of(codec),
		         nodo_rendering, hardware_refusal[0] ? hardware_refusal : "no reason");
		return false;
	}
	*is_opened = true;
	return probe_frames(cod, reason, n, bytes_out);
}

/*
 * ⭐ 1.5 (review of 13422add/541479fc) — THE CODEC ON THE SESSION'S CARD.
 *
 * The codecs offered in HERE_I_AM were measured AT STARTUP on
 * `startup_node()` (`--render-node` or `RENDER_NODE`): the parent has no
 * compositor to ask.  The session encodes on the compositor's card
 * (`choose_render_node()`), and on a two-card machine that may be ANOTHER
 * card — one where the negotiated codec does not exist (the Intel without
 * HEVC 10 bits, a Radeon without the VA-API driver…).  Without this test
 * the encoder would fail there and `encoder_of()` would retry forever on a
 * codec the card lacks: a black screen.
 *   ⇒ When the two nodes DIFFER, the same test as at startup (`probe_frames()`,
 *     H.264/HEVC at the NEGOTIATED depth, 256x256, the route in force) is run
 *     ONCE per codec and depth on the session's node, before the first
 *     encoder.  Yes ⇒ that node.  No ⇒
 *     the line says why, and the codec goes to the startup node: the
 *     cross-card import of before 13422add, which is slower but is an image.
 * ⛔ On one card (or when the compositor named the startup node) nothing is
 *    tested: the startup measure already said it.
 * ⚠ A card that is FULL (`TOO_MANY_OBJECTS`, the RTX 4090 at 12 encodings) is
 *   not a card without the codec: nothing is decided, the session's node is
 *   kept and `encoder_of()`'s wait does the rest.
 * ⚠ Outside the session (`--encoding-test`, the startup measure) it is
 *   `nodo_rendering`, untouched.
 */
static const char *node_of_codec(CodecVideo codec, uint8_t idx, uint8_t depth)
{
	/* ⚠ per codec AND per depth: a card with HEVC 8 bits may lack HEVC
	 *   10 bits (the Intel case above), and a second client may negotiate
	 *   the other depth (`encoder_of()` redoes the encoder) */
	static char chosen_by_depth[CODEC_MAX][2][64];
	char (*chosen)[64];
	int d;
	CodificatoreRichiesta r;
	Encoder *cod;
	char error[512] = "", reason[768] = "", desc[160];
	size_t bytes = 0;
	bool yes;

	if (!in_session_child || idx >= CODEC_MAX)
		return nodo_rendering;
	chosen = chosen_by_depth[idx];
	d = depth == 10 ? 1 : 0;
	if (chosen[d][0])
		return chosen[d];
	if (render_node_same(nodo_rendering, startup_node())) {
		snprintf(chosen[d], sizeof chosen[d], "%s", nodo_rendering);
		return chosen[d];
	}

	memset(&r, 0, sizeof r);
	r.codec = codec;
	r.componente = component_of(codec);
	r.width = PROBE_SIDE;
	r.height = PROBE_SIDE;
	r.fotogrammi_al_secondo = MOTION_FPS;
	r.mode = CODIFICATORE_QUALITA_QP;
	r.quality = QP_HARDWARE;
	/* ⚠ the NEGOTIATED depth, not the startup measure's 8: tested at 8, the
	 *   Intel without HEVC 10 bits would say yes and the real encoder (at 10)
	 *   would then fail there and retry forever — the black screen this test
	 *   exists to avoid (review of bc3158bf) */
	r.depth = depth;
	r.livello_x10 = 0;
	r.fmt = ENCODER_PIXEL_BGRX;
	r.chiavi_ogni = 0;
	r.nodo_rendering = nodo_rendering;
	r.power = RENDER_POWER;
	cod = codificatore_nuovo(&r, error, sizeof error);
	if (!cod) {
		if (strstr(error, "TOO_MANY_OBJECTS"))
			return nodo_rendering; /* full, not without: decided at the next try */
		snprintf(reason, sizeof reason, "«%s» does not open (%.400s)", r.componente, error);
		yes = false;
	} else {
		yes = probe_frames(cod, reason, sizeof reason, &bytes);
		codificatore_libera(cod);
	}
	if (yes) {
		snprintf(chosen[d], sizeof chosen[d], "%s", nodo_rendering);
		registro_dice(LOG_CHILD,
		              "⭐ codec %d at %u bits tested on the session's card %s (it is not "
		              "the startup card %s): it encodes (%zu bytes) — the encoder opens there",
		              (int)codec, depth, nodo_rendering, startup_node(), bytes);
		return chosen[d];
	}
	snprintf(chosen[d], sizeof chosen[d], "%s", startup_node());
	render_node_describe(chosen[d], desc, sizeof desc);
	registro_dice(LOG_CHILD,
	              "⛔ codec %d at %u bits does NOT encode on the compositor's card %s: "
	              "%s.  ⇒ It falls back to the startup card %s (%s), where the startup "
	              "measure found it — every frame is a cross-card import (slower, as "
	              "before 1.5), and it is not retried on %s",
	              (int)codec, depth, nodo_rendering, reason, chosen[d], desc,
	              nodo_rendering);
	return chosen[d];
}

/* The measure, in this process: two questions, and each "no" with its reason. */
static void capabilities_video_measure(VideoCapabilities *cv)
{
	size_t byte;
	bool is_opened;
	char reason[768];

	memset(cv, 0, sizeof *cv);
	snprintf(cv->node, sizeof cv->node, "%s", nodo_rendering);
	cv->hevc_card = test_codec(CODIFICATORE_HEVC, 1, reason, sizeof reason, &byte, &is_opened);
	if (!cv->hevc_card)
		snprintf(cv->why_hevc, sizeof cv->why_hevc, "%s",
		         hardware_refusal[0] ? hardware_refusal : reason);
	else
		snprintf(cv->route_hevc, sizeof cv->route_hevc, "%s", encoder_route(enc[1]));
	encoders_free();
	cv->h264_card = test_codec(CODIFICATORE_H264, 3, reason, sizeof reason, &byte, &is_opened);
	if (!cv->h264_card)
		snprintf(cv->why_h264, sizeof cv->why_h264, "%s",
		         hardware_refusal[0] ? hardware_refusal : reason);
	else
		snprintf(cv->route_h264, sizeof cv->route_h264, "%s", encoder_route(enc[3]));
	encoders_free();
}

/* What is OFFERED, from the measure: "hevc,h264" · "hevc" · "h264" · "" (nothing). */
static void capabilities_video_offered(const VideoCapabilities *cv, char *dove, size_t n)
{
	snprintf(dove, n, "%s%s%s", cv->hevc_card ? "hevc" : "",
	         cv->hevc_card && cv->h264_card ? "," : "",
	         cv->h264_card ? "h264" : "");
}

/* One line that says everything, for the log and for the `reason`. */
static void capabilities_video_explain(const VideoCapabilities *cv, char *dove, size_t n)
{
	snprintf(dove, n, "card %s (route requested «%s») — HEVC: %s%.300s%s · H.264: %s%.300s%s",
	         cv->node, encode_route,
	         cv->hevc_card ? "yes via " : "NO (",
	         cv->hevc_card ? cv->route_hevc : cv->why_hevc, cv->hevc_card ? "" : ")",
	         cv->h264_card ? "yes via " : "NO (",
	         cv->h264_card ? cv->route_h264 : cv->why_h264, cv->h264_card ? "" : ")");
}

bool child_video_capabilities(char *offered, size_t offered_bytes, char *explanation,
                           size_t explanation_byte)
{
	/* ═══════════════════════════════════════════════════════════════════════
	 * ⭐⭐ THE TEST AT STARTUP — phase 18, the user's decision (30 Sep 2026).
	 *
	 * The browser must NOT receive in `HERE_I_AM` a codec the server cannot do:
	 * HEVC and H.264 are there only if the CARD encodes them.  ⛔ Phase 19
	 * (1 Oct 2026, §10.27): the software fallback (OpenH264) has left — if the
	 * card cannot encode anything it is declared at startup, with the reason,
	 * and the negotiation ends in NOTHING_IN_COMMON.
	 *
	 * ⚠ IN A SEPARATE PROCESS: the test opens the card's driver, and a driver
	 *   that crashes must not take the server down with it before it has
	 *   opened the port.  The child writes the measure on a pipe and dies; if
	 *   nothing arrives, "I don't know" is a declared "no" — not a "yes".
	 * ⚠ It runs as ROOT (it is the parent): a user without the `render` group
	 *   would see less.  The session's child enrols the user in the card's
	 *   groups at the first connection (§6.5-bis), so root's answer is the
	 *   right one for the session.
	 * ═══════════════════════════════════════════════════════════════════════ */
	VideoCapabilities cv;
	int pipe_fd[2];
	pid_t pid;

	memset(&cv, 0, sizeof cv);
	if (pipe(pipe_fd) != 0) {
		snprintf(explanation, explanation_byte, "the test's pipe does not open: %s",
		         strerror(errno));
		offered[0] = 0;
		return false;
	}
	pid = fork();
	if (pid < 0) {
		snprintf(explanation, explanation_byte, "the test does not start (fork): %s",
		         strerror(errno));
		close(pipe_fd[0]);
		close(pipe_fd[1]);
		offered[0] = 0;
		return false;
	}
	if (pid == 0) {
		close(pipe_fd[0]);
		capabilities_video_measure(&cv);
		encoders_free();
		{
			const uint8_t *p = (const uint8_t *) &cv;
			size_t stays = sizeof cv;
			while (stays) {
				ssize_t n = write(pipe_fd[1], p, stays);
				if (n <= 0) {
					if (n < 0 && errno == EINTR)
						continue;
					break;
				}
				p += (size_t) n;
				stays -= (size_t) n;
			}
		}
		close(pipe_fd[1]);
		_exit(0);
	}
	close(pipe_fd[1]);
	{
		uint8_t *p = (uint8_t *) &cv;
		size_t readings = 0;
		/* ⚠ With a maximum time: a card that does not answer must not keep the
		 *   server without a port forever.  30 s is much more than the ~100 ms
		 *   the test costs; beyond that, it is declared and we go on without
		 *   video. */
		while (readings < sizeof cv) {
			struct pollfd pf = { .fd = pipe_fd[0], .events = POLLIN };
			int ready = poll(&pf, 1, 30000);
			if (ready < 0 && errno == EINTR)
				continue;
			if (ready <= 0)
				break;
			ssize_t n = read(pipe_fd[0], p + readings, sizeof cv - readings);
			if (n < 0 && errno == EINTR)
				continue;
			if (n <= 0)
				break;
			readings += (size_t) n;
		}
		close(pipe_fd[0]);
		if (readings < sizeof cv) {
			int state = 0;
			kill(pid, SIGKILL);
			waitpid(pid, &state, 0);
			snprintf(explanation, explanation_byte,
			         "⛔ the encoding test at startup did NOT answer (%zu bytes of %zu, %s): "
			         "no video codec is offered — «I don't know» is not a «yes»",
			         readings, sizeof cv,
			         WIFSIGNALED(state) ? "killed by a signal" : "exited without saying anything");
			offered[0] = 0;
			return false;
		}
		waitpid(pid, NULL, 0);
	}
	cv.node[sizeof cv.node - 1] = 0;
	cv.why_hevc[sizeof cv.why_hevc - 1] = 0;
	cv.why_h264[sizeof cv.why_h264 - 1] = 0;
	cv.route_hevc[sizeof cv.route_hevc - 1] = 0;
	cv.route_h264[sizeof cv.route_h264 - 1] = 0;
	capabilities_video_offered(&cv, offered, offered_bytes);
	capabilities_video_explain(&cv, explanation, explanation_byte);
	return offered[0] != 0;
}

static int test_exits(const char *outcome, const char *encoder, const char *route,
                      const char *node, const char *reason, CodecVideo codec,
                      const VideoCapabilities *cv, int code)
{
	char c[128], n[128], m[4096], o[32], r[64], s[32], sh[32], s4[32];

	json_text(c, sizeof c, encoder);
	json_text(s, sizeof s, route);
	json_text(n, sizeof n, node);
	json_text(m, sizeof m, reason);
	capabilities_video_offered(cv, r, sizeof r);
	json_text(o, sizeof o, r);
	json_text(sh, sizeof sh, cv->route_hevc);
	json_text(s4, sizeof s4, cv->route_h264);
	printf("{\"outcome\":\"%s\",\"encoder\":\"%s\",\"route\":\"%s\",\"node\":\"%s\","
	       "\"reason\":\"%s\",\"codec\":\"%s\",\"offered\":\"%s\",\"hevc\":\"%s\",\"h264\":\"%s\","
	       "\"hevc_route\":\"%s\",\"h264_route\":\"%s\"}\n",
	       outcome, c, s, n, m, codec == CODIFICATORE_HEVC ? "hevc" : "h264", o,
	       cv->hevc_card ? "hardware" : "none", cv->h264_card ? "hardware" : "none", sh,
	       s4);
	/* ⛔ A line that does not come out whole is "I don't know", not the outcome
	 *    it carried. */
	if (fflush(stdout) != 0)
		return 1;
	return code;
}

int child_test_encoding(int argc, char **argv)
{
	CodecVideo codec = CODIFICATORE_H264;
	uint8_t idx = 3; /* §6.2: 3 = H.264, 1 = HEVC */
	const EncoderConfession *c;
	VideoCapabilities cv;
	char reason[2048], explain[1024];
	size_t byte = 0;
	bool is_opened = false;

	for (int i = 0; i < argc; i++) {
		if (strcmp(argv[i], "h264") == 0) {
			codec = CODIFICATORE_H264;
			idx = 3;
		} else if (strcmp(argv[i], "hevc") == 0) {
			codec = CODIFICATORE_HEVC;
			idx = 1;
		} else if (strcmp(argv[i], "--node") == 0 && i + 1 < argc) {
			/* a path that does not fit is refused, not cut: a truncated path names ANOTHER node */
			if (strlen(argv[i + 1]) >= sizeof render_node_buf) {
				fprintf(stderr, "⛔ --node: the path is longer than %zu characters\n",
				        sizeof render_node_buf - 1);
				return 2;
			}
			snprintf(render_node_buf, sizeof render_node_buf, "%s", argv[++i]);
		} else if (strcmp(argv[i], "--encoding-route") == 0 && i + 1 < argc
		           && child_encoding_route(argv[i + 1])) {
			i++;
		} else {
			fprintf(stderr,
			        "usage: remotix --encoding-test [h264|hevc] [--node /dev/dri/renderDN] "
			        "[--encoding-route card|vulkan|vaapi]\n"
			        "     (--software no longer exists: the software fallback has left, phase 19)\n");
			return 2;
		}
	}

	/* ⭐ First the whole picture (it is the same measure as at startup), then
	 *    the requested test: so the JSON line also says what the server would
	 *    offer. */
	capabilities_video_measure(&cv);
	encoders_free();
	capabilities_video_explain(&cv, explain, sizeof explain);
	registro_dice(LOG_CHILD, "--encoding-test: %s", explain);

	if (!test_codec(codec, idx, reason, sizeof reason, &byte, &is_opened)) {
		encoders_free();
		if (!is_opened)
			registro_dice(LOG_CHILD,
			              "⛔⛔ NO CARD CAN ENCODE %s on this machine: %s",
			              codec == CODIFICATORE_HEVC ? "HEVC" : "H.264", reason);
		return test_exits("none", "", "", "", reason, codec, &cv,
		                  is_opened ? 1 : PROBE_NO_CARD);
	}
	c = codificatore_confessione(enc[idx]);
	snprintf(reason, sizeof reason, "a %ux%u frame encoded: %zu bytes, %s — %s · %s",
	         PROBE_SIDE, PROBE_SIDE, byte, c->codec_string, encoder_name(enc[idx]),
	         explain);
	{
		int fine = test_exits("hardware", c->componente ? c->componente : "",
		                      encoder_route(enc[idx]), nodo_rendering, reason, codec,
		                      &cv, 0);
		encoders_free();
		return fine;
	}
}

/* ⛔⭐ WHICH INSTANT ENDS UP IN THE 28 BYTES, AND WHERE IT COMES FROM — point 7,
 *     decided and MEASURED instead of inferred.
 *
 *     §6.2 says "microseconds of the **server's monotonic** clock at
 *     capture".  The two possible sources are:
 *
 *       a) `CLOCK_MONOTONIC` read by US **after** `capture_take()` has
 *          returned — what phase 2 did.  ⚠ It is not the instant of capture:
 *          it is the instant we noticed, and it contains the whole wait in
 *          the exchange slot;
 *       b) the `pts` PipeWire attaches to the frame (`spa_meta_header`), which
 *          is the real instant — if it is the same clock.
 *
 *     ⛔ "If" is not a word to write in a decision (`LESSONS.md`
 *        §2.3-quater): here we LOOK.  At the first grab the `pts` and our
 *        `CLOCK_MONOTONIC` are compared; if they are less than a second apart
 *        they are the same clock and the `pts` is taken, otherwise ours is
 *        taken and **it is written that we fell back** (`CODER.md` §4.2).
 *
 *     ⚠ The latency link of step 5 relies on this number: here is the line
 *       that says which of the two it is reading. */
static uint64_t frame_instant(const CaptureStopped *fo, uint64_t our_us)
{
	uint64_t pts_us;

	if (!fo->seq_known || fo->pts <= 0) {
		if (pts_is_monotonic != 0) {
			pts_is_monotonic = 0;
			registro_dice(LOG_CHILD,
			              "⚠ the frame carries no `pts` (seq_nota %d, pts "
			              "%lld): the instant of the 28 bytes is OUR "
			              "CLOCK_MONOTONIC read after the grab — declared "
			              "fallback, and it contains the wait in the exchange "
			              "slot",
			              (int)fo->seq_known, (long long)fo->pts);
		}
		return our_us;
	}
	pts_us = (uint64_t)fo->pts / 1000u;
	if (pts_is_monotonic < 0) {
		uint64_t gap = pts_us > our_us ? pts_us - our_us
		                                     : our_us - pts_us;
		pts_is_monotonic = gap < 1000000u ? 1 : 0;
		registro_dice(LOG_CHILD,
		              pts_is_monotonic
		                  ? "⭐ MEASURED: Mutter's `pts` is the same "
		                    "CLOCK_MONOTONIC as ours (offset %llu us) ⇒ the 28 "
		                    "bytes of §6.2 get the REAL instant of capture, "
		                    "not the one at which we noticed"
		                  : "⚠ MEASURED: Mutter's `pts` is NOT our "
		                    "CLOCK_MONOTONIC (offset %llu us, over one second) "
		                    "⇒ the 28 bytes get OUR clock read after "
		                    "the grab.  Declared fallback (CODER.md §4.2): "
		                    "the latency link also reads the wait in the "
		                    "exchange slot",
		              (unsigned long long)gap);
	}
	return pts_is_monotonic ? pts_us : our_us;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ PHASE 8 — THE BREAKDOWN OF THE `capture → first byte` STRETCH
 *
 * ⛔ THE FACT THAT GIVES BIRTH TO IT, and it must be said because it is the only
 *    reason this code exists: `[M]` phase 4, that stretch is worth **30.37 ms**,
 *    and the three times the encoder already declared — conversion **5.6**,
 *    upload **2.9**, encoding **5.3** — explain **13.8** of it.
 *    ⇒ **~16 ms had no owner.**  An unnamed margin cannot be cured: **first
 *    instrument, then cure**, or the cure is born without a "before".
 *
 * ⛔⛔ AND THE BREAKDOWN MUST HAVE NO HOLES, which is precisely the property
 *      that made phase 4's worth something (sum of the stretches 139.08
 *      against a total of 139.40: gap **0.32 ms**).  ⇒ The items are disjoint
 *      and in a row, and the last is `rest`: what the total has beyond the
 *      sum of the others.  A growing `rest` is a piece of the stretch nobody
 *      is looking at yet — and it shows at once, instead of vanishing in the
 *      average.
 *
 *      Mutter's pts
 *        │  producer     Mutter+PipeWire up to our callback
 *        │  allocation   the g_malloc of the slot (0 if the buffer is reused)
 *        │  copy         the memcpy inside the real-time callback
 *      arrival in the slot
 *        │  in slot      ⭐ WAITING: the frame ages until the loop comes back
 *        │               to ask for it.  ⛔ It is not work
 *      grab
 *        │  measure      `measure_pixels()`: DIAGNOSTICS, every pixel, every round
 *        │  conversion   colori709 (BGRx → NV12/I420)  (from the encoder)
 *        │  upload       system memory → GPU           (from the encoder)
 *        │  encoding     the call to the encoder       (from the encoder)
 *        │  sending      the pieces towards the parent
 *      first byte out
 *
 * ⚠ AND THE BOUNDARY MUST BE DECLARED: here the stretch ends **when the bytes
 *   have left towards the parent**, not when they arrive in the page.  Phase
 *   4's number is measured by the client; this is the piece of it that lives
 *   inside the child, and it is the only one this process can see without
 *   inferring.
 *
 * ⛔ AND MEDIANS ARE GIVEN, not averages: a frame that takes a page fault or a
 *    preemption moves the average and not the median, and phase 4 had the
 *    medians.  ⚠ The **maximum** is given beside it, because it is the only
 *    place where those hits still show.
 * ═══════════════════════════════════════════════════════════════════════════ */

#define STRETCH_ENTRIES 10
#define STRETCH_SAMPLES 512

/* The order is that of the box: it is also the order in which they are printed. */
static const char *const stretches_names[STRETCH_ENTRIES] = {
	"producer", "allocation", "copy",     "in slot", "measure",
	"conversion", "upload", "encoding", "sending", "rest"
};
static uint32_t stretches_sample[STRETCH_SAMPLES][STRETCH_ENTRIES];
static uint32_t stretches_total[STRETCH_SAMPLES];
static unsigned stretches_n; /* how many slots are full (stops at the cap) */
static unsigned stretches_next;
static uint64_t stretches_seen;  /* how many frames in all */
static uint64_t stretches_logged_us;
/* ⛔ How many frames had to do without Mutter's `pts`: without this number the
 *    "producer" item would be an average between two different quantities. */
static uint64_t stretches_without_pts;

/* ⭐ PHASE 16 (25 Sep 2026) — OUR PIECE, SECOND BY SECOND.
 *
 * ⛔ The STRETCH line is not enough to state §3.2 of SPECIFICHE ("only the
 *    piece that is ours is measured"), for two measured reasons (`phases/16…`
 *    §9): its `max` is that of the 512-frame ring, not of the second — a
 *    birth spike stays inside it for 8-17 s —, and its total starts from the
 *    compositor's `pts`, that is it contains "producer", which is the
 *    compositor's work.
 * ⭐ Here: for each frame `total − producer` (from our copy to the byte out,
 *    waiting in the slot included: that one is ours), collected ONLY in the
 *    second that is closing, and given with the p95 and the maximum of that
 *    second.
 * ⚠ On the wlroots road the "copy" is the compositor's blit onto our
 *   DMA-BUF: it stays inside, on the cautious side. */
#define OUR_SECOND_MAX 512
static uint32_t our_second[OUR_SECOND_MAX];
static unsigned our_count;

static int stretches_compare(const void *a, const void *b)
{
	uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
	return x < y ? -1 : (x > y ? 1 : 0);
}

/* The median of an item over the kept sample.  ⚠ It is copied before sorting:
 * the sample is a ring and sorting it in place would destroy it. */
static uint32_t stretches_median(int entry, uint32_t *maximum)
{
	uint32_t copied[STRETCH_SAMPLES];
	unsigned i, n = stretches_n;

	if (maximum)
		*maximum = 0;
	if (!n)
		return 0;
	for (i = 0; i < n; i++) {
		copied[i] = entry < 0 ? stretches_total[i] : stretches_sample[i][entry];
		if (maximum && copied[i] > *maximum)
			*maximum = copied[i];
	}
	qsort(copied, n, sizeof copied[0], stretches_compare);
	return copied[n / 2];
}

/*
 * Records a frame in the breakdown and, once per second, states it.
 *
 * ⚠ One line per frame would make the log unreadable precisely when it is
 *   needed — it is the same reason the rest of the loop speaks once per
 *   second (`child.c`, the loop's count).
 */
static void stretches_count(const CaptureStopped *fo, const EncoderFrame *fg,
                         uint64_t send_us, uint64_t us_fine)
{
	uint32_t *v = stretches_sample[stretches_next];
	uint64_t pts_us, start, total_sum = 0;
	uint64_t total;
	int i;

	/* ⛔ Without Mutter's `pts` the stretch has no REAL start: it starts from
	 *    the arrival in the slot and the "producer" item stays at zero, which
	 *    is a declared gap and not a measured zero. */
	if (pts_is_monotonic == 1 && fo->seq_known && fo->pts > 0) {
		pts_us = (uint64_t)fo->pts / 1000u;
		start = pts_us;
	} else {
		stretches_without_pts++;
		start = fo->arrival_us > (fo->copy_us + fo->alloc_us)
		             ? fo->arrival_us - fo->copy_us - fo->alloc_us
		             : fo->arrival_us;
	}
	if (us_fine <= start)
		return; /* clocks that do not subtract: no number is invented */
	total = us_fine - start;

	memset(v, 0, sizeof stretches_sample[0]);
	/* "producer" = from when Mutter says it captured to when our callback
	 *  starts copying.  ⛔ The copy and the allocation are INSIDE the
	 *  pts→arrival interval, and are subtracted, or they would count twice. */
	{
		uint64_t until_copy = fo->arrival_us > (fo->copy_us + fo->alloc_us)
		                            ? fo->arrival_us - fo->copy_us - fo->alloc_us
		                            : fo->arrival_us;
		v[0] = until_copy > start ? (uint32_t)(until_copy - start) : 0u;
	}
	v[1] = (uint32_t)fo->alloc_us;
	v[2] = (uint32_t)fo->copy_us;
	v[3] = (uint32_t)fo->in_slot_us;
	v[4] = (uint32_t)fo->measure_us;
	v[5] = (uint32_t)fg->us_conversione;
	v[6] = (uint32_t)fg->upload_us;
	v[7] = (uint32_t)fg->us_codifica;
	v[8] = (uint32_t)send_us;
	for (i = 0; i < STRETCH_ENTRIES - 1; i++)
		total_sum += v[i];
	v[9] = total_sum < total ? (uint32_t)(total - total_sum) : 0u;
	stretches_total[stretches_next] = total > 0xffffffffu ? 0xffffffffu : (uint32_t)total;
	if (our_count < OUR_SECOND_MAX) {
		uint64_t our = total > v[0] ? total - v[0] : 0u;
		our_second[our_count++] = our > 0xffffffffu ? 0xffffffffu
		                                                        : (uint32_t)our;
	}

	stretches_next = (stretches_next + 1) % STRETCH_SAMPLES;
	if (stretches_n < STRETCH_SAMPLES)
		stretches_n++;
	stretches_seen++;

	if (us_fine - stretches_logged_us < 1000000u)
		return;
	stretches_logged_us = us_fine;
	if (our_count) {
		unsigned n = our_count;
		qsort(our_second, n, sizeof our_second[0], stretches_compare);
		/* p95 "nearest rank": with 30 frames it is the 29th, that is the
		 * second worst — not the average of two. */
		unsigned k = (n * 95 + 99) / 100;
		registro_dice(LOG_CHILD,
		              "⭐ OURS in the second (copy → byte out, §3.2): p95 %.2f ms · "
		              "max %.2f · median %.2f · %u frames",
		              our_second[k ? k - 1 : 0] / 1000.0,
		              our_second[n - 1] / 1000.0, our_second[n / 2] / 1000.0, n);
		our_count = 0;
	}
	{
		char line[512];
		size_t off = 0;
		uint32_t max_total = 0;
		uint32_t total_median = stretches_median(-1, &max_total);

		for (i = 0; i < STRETCH_ENTRIES; i++) {
			uint32_t mx = 0, md = stretches_median(i, &mx);
			int n_written = snprintf(line + off, sizeof line - off, "%s%s %.2f (max %.2f)",
			                       i ? " · " : "", stretches_names[i], md / 1000.0,
			                       mx / 1000.0);
			if (n_written < 0 || (size_t)n_written >= sizeof line - off)
				break;
			off += (size_t)n_written;
		}
		registro_dice(LOG_CHILD,
		              "⭐ STRETCH capture → byte out: median %.2f ms (max %.2f) over %u "
		              "frames of the sample, %llu in all — %s%s",
		              total_median / 1000.0, max_total / 1000.0, stretches_n,
		              (unsigned long long)stretches_seen, line,
		              stretches_without_pts
		                  ? "  ⚠ and some frames have no Mutter `pts`: "
		                    "for those «producer» is a gap, not a zero"
		                  : "");
	}
}

/* Encodes a frame with the LIVE encoder of that codec and sends it to the
 * parent.  ⛔ `key` is not assumed: it is what the encoder read from the
 * stream (`fg.key`), and §6.2 writes it in the `kind` field. */
static bool encode_and_send(const CaptureStopped *fo, CodecVideo codec,
                             uint8_t nr, const char *dir_survey,
                             const char *file_name, uint64_t instant_us,
                             uint32_t canvas_w, uint32_t canvas_h, uint32_t input)
{
	EncoderFrame fg;
	Encoder *cod;
	const EncoderConfession *c;

	/* ⭐ PHASE 13 — the channel order is read from the frame, not assumed.
	 *    ⚠ Only `XBGR8888`/`ABGR8888` are `R G B x`: everything else stays
	 *    BGRx, that is exactly what GNOME and KDE had before (Mutter and KWin
	 *    give BGRx, and on the card's road this field decides nothing). */
	{
		const uint32_t xb24 = (uint32_t)'X' | ((uint32_t)'B' << 8) |
		                      ((uint32_t)'2' << 16) | ((uint32_t)'4' << 24);
		const uint32_t ab24 = (uint32_t)'A' | ((uint32_t)'B' << 8) |
		                      ((uint32_t)'2' << 16) | ((uint32_t)'4' << 24);
		FormatoPixel seen = (!fo->on_card &&
		                      (fo->formato_drm == xb24 || fo->formato_drm == ab24))
		                         ? CODIFICATORE_PIXEL_RGBX
		                         : ENCODER_PIXEL_BGRX;

		if (seen != input_format) {
			registro_dice(LOG_CHILD,
			              "⭐ the capture delivers the pixels in %s order: telling the "
			              "encoder instead of letting it assume",
			              seen == CODIFICATORE_PIXEL_RGBX ? "R G B x" : "B G R x");
			input_format = seen;
		}
	}

	cod = encoder_of(codec, nr, canvas_w, canvas_h);
	if (!cod)
		return false;

	/* ⛔ §5.2 — AND HERE THE REQUESTED KEYFRAME BECOMES A REAL KEYFRAME.  ⚠ It is
	 *    asked BEFORE compressing: after would be one frame late, and that
	 *    frame is precisely the one the client is waiting for. */
	if (nr < CODEC_MAX && key_debt[nr]) {
		codificatore_chiedi_chiave(cod);
		key_debt[nr] = false;
	}

	/* ⛔⛔ AND HERE IT IS CHECKED WHETHER THE ENCODER IS REALLY IN HARDWARE —
	 *     asked of the COMPONENT (`componente_e_hardware`: it accepts a surface
	 *     format, not a pixel format), not read in the name and not inferred
	 *     from having opened a render node (`LESSONS.md` §1.11).
	 *
	 * ⚠ Until phase 18 the case existed: `encoder_of()` fell back to
	 *   software (H.264 beyond 4096 px, which `[M]` the driver refuses).  Since
	 *   phase 19 the fallback has left and `encoder_of()` opens only the
	 *   card; the guard stays, because it costs one line and an encoder that
	 *   were not on the card must not receive a descriptor.  It is flagged,
	 *   and dismantling is left to the loop, which is the only one holding the
	 *   stage. */
	if (fo->on_card && !codificatore_in_hardware(cod)) {
		if (!card_to_abandon) {
			card_to_abandon = true;
			card_never_again = true;
			registro_dice(LOG_CHILD,
			              "⛔⛔ the pixels are ON THE CARD and «%s» encodes in "
			              "SOFTWARE: zero copy is not viable with this "
			              "encoder.  ⇒ Remounting the stage on MEMORY and not "
			              "retrying — ⚠ and this line is the declaration, "
			              "because from here on the stretch's numbers are those "
			              "of the other road",
			              encoder_name(cod));
		}
		return false;
	}

	/* ⛔⛔⛔ AND HERE THE **MEASURED** STRIDE IS CHECKED, before compressing — see
	 *      the box in `encoder.h`.
	 *
	 * ⚠ It is the only place where the real stride is known: `capture.h` rule 1
	 *   says the stride is READ from the chunk and not computed, so before the
	 *   first frame there was nothing to look at.
	 * ⛔ And the frame is NOT sent: the defect it stops gives no error — it
	 *   gives a desktop skewed by a few pixels per row, which passes every
	 *   check on milliseconds and every check on colour.  Better a few frames
	 *   not sent and a remount, than a wrong image for the whole session. */
	if (fo->on_card && !encoder_stride_importable(fo->stride)) {
		if (!card_to_abandon) {
			card_to_abandon = true;
			card_denied_w = fo->width;
			card_denied_h = fo->height;
			registro_dice(LOG_CHILD,
			              "⛔⛔ the DMA-BUF stride is %u on a %ux%u canvas, and "
			              "it is NOT a multiple of %u: the driver would read the rows at "
			              "a stride of its own and the desktop would come out SKEWED, without "
			              "any error.  `[M]` 22 Aug 2026: at 1552 px the "
			              "mark reads (contrast 1.000), at 1544 it does not — eight "
			              "pixels of difference and opposite verdicts.  ⇒ Remounting the "
			              "stage on MEMORY for this canvas, and zero copy "
			              "will come back by itself on a canvas with a good stride",
			              fo->stride, fo->width, fo->height,
			              encoder_card_alignment());
		}
		return false;
	}

	if (fo->on_card) {
		EncoderSurface sup = {
			.fd = fo->fd,
			.offset = fo->offset,
			.stride = fo->stride,
			.width = fo->width,
			.height = fo->height,
			.formato_drm = fo->formato_drm,
			.modifier = fo->modifier,
			.generation = fo->generation,
		};
		if (!codificatore_comprimi_scheda(cod, &sup, &fg)) {
			registro_dice(LOG_CHILD,
			              "⛔ codec %d did not deliver the frame from the "
			              "CARD: `false` is NOT «an empty frame», it is "
			              "«this one is not sent»",
			              (int)codec);
			cycle_faults++;
			return false;
		}
	} else if (!codificatore_comprimi(cod, fo->pixel, fo->stride, &fg)) {
		registro_dice(LOG_CHILD,
		              "⛔ codec %d did not deliver the frame: `false` "
		              "is NOT «an empty frame», it is «this one is not "
		              "sent»",
		              (int)codec);
		cycle_faults++;
		return false;
	}
	c = codificatore_confessione(cod);
	/* ⛔ The first is stated, the following go to chatter: at sixty per second
	 *    this line would make the whole rest of the log unreadable — and that
	 *    is precisely the case in which the rest of the log is needed. */
	if (cycle_frames == 0)
		registro_dice(LOG_CHILD,
		              "⭐ FIRST frame encoded: codec %d, %zu bytes, %s, "
		              "«%s», depth in the stream %d, level %d, promotion "
		              "8→10 %s, conversion %llu us, upload to the GPU %llu "
		              "us, encoding %llu us · %s%s",
		              (int)codec, fg.byte, fg.key ? "KEYFRAME" : "delta",
		              c->codec_string, c->stream_depth, c->stream_level,
		              c->promotion_8_to_10 ? "YES (declared)" : "no",
		              (unsigned long long)fg.us_conversione,
		              (unsigned long long)fg.upload_us,
		              (unsigned long long)fg.us_codifica,
		              encoder_name(cod),
		              fg.trattenuto ? " — ⚠ HELD BACK: the encoder has "
		                              "added one frame of delay" : "");
	/* ⛔⭐⭐ AND THE LEVEL IS DECLARED A SECOND TIME, IN PLAIN FORM — §4.3, line
	 *      701.  ⚠ It is not a repetition of the line above: that one gives the
	 *      RAW number of the SPS, which for HEVC is three times as much and for
	 *      AV1 is an index.  This one gives it in the form in which the client
	 *      asks for it (`video.level=5.1`), which is the only one in which
	 *      the two numbers can be put in a column.
	 *
	 * ⛔⭐⭐ AND SINCE 23 AUG 2026 THE PROGRAM MAKES THE COMPARISON, because the
	 *      REQUESTED number has crossed the process boundary: the `HELLO`
	 *      (§4.3) → `rcp_level_negotiated()` → `webtransport.c` → `main.c` →
	 *      `children_video()` → `struct body_video.livello_x10` → here.  It is
	 *      the same chain the negotiated DEPTH travelled on 17 Aug 2026, for a
	 *      defect of the same family — and before tonight this box said *"the
	 *      comparison is made by whoever reads the log"*, which was honest and
	 *      not enough: `[M]` at 3840x2160 the client declared 5.1 and the
	 *      server produced **5.2**, for weeks, and nobody noticed.
	 *
	 * ⛔ AND THE COMPARISON IS NOT THE CURE: the cure is **not exceeding**, and
	 *    it lives at the encoder's opening (`encoder_of()`,
	 *    `r.livello_x10`).  This line is the CHECK — R31, *"ask by name and
	 *    verify"* — and it reads the bytes PRODUCED, not the option passed: a
	 *    component that ignored `level` without saying so shows only here.
	 *
	 * ⚠ A level produced higher than the requested one gives no error: it gives
	 *   a black screen, and that is the reason the verdict is written in plain
	 *   form instead of staying a comparison in the reader's head. */
	if (cycle_frames == 0) {
		unsigned tenths = level_in_tenths(codec, c->stream_level);
		const char *alphabet = codec == CODIFICATORE_H264   ? "level_idc"
		                       : codec == CODIFICATORE_HEVC ? "general_level_idc, "
		                                                      "which is three times as much"
		                                                    : "seq_level_idx";
		if (!tenths)
			registro_dice(LOG_CHILD,
			              "⚠ §4.3 — LEVEL PRODUCED: I DON'T KNOW (the SPS has "
			              "%d, and I cannot translate it for this codec) — ⛔ and «I "
			              "don't know» does NOT mean «low»: it means the ceiling "
			              "of `video.level` cannot be verified today",
			              c->stream_level);
		else if (!requested_level_x10)
			registro_dice(LOG_CHILD,
			              "⭐ §4.3 — LEVEL: produced %u.%u (in the SPS %d, that is "
			              "%s) · string for the decoder «%s» · REQUESTED: "
			              "nothing.  ⚠ §4.3 does not oblige the client to declare "
			              "`video.level`: no ceiling to enforce — but "
			              "the server produces a level anyway, and it is "
			              "this one",
			              tenths / 10u, tenths % 10u, c->stream_level,
			              alphabet, c->codec_string);
		else if (tenths <= requested_level_x10)
			registro_dice(LOG_CHILD,
			              "⭐ §4.3 — LEVEL: produced %u.%u ≤ requested %u.%u ✓ "
			              "(in the SPS %d, that is %s) · string for the "
			              "decoder «%s».  ⭐ The ceiling was IMPOSED "
			              "at opening and READ BACK from the bytes: it is R31",
			              tenths / 10u, tenths % 10u,
			              requested_level_x10 / 10u, requested_level_x10 % 10u,
			              c->stream_level, alphabet, c->codec_string);
		else
			registro_dice(LOG_CHILD,
			              "⛔⛔ §4.3 VIOLATED (line 701) — LEVEL: produced "
			              "%u.%u > requested %u.%u (in the SPS %d, that is %s) · "
			              "string for the decoder «%s».  ⛔ The "
			              "encoder did NOT obey the imposed level: the "
			              "browser's decoder may REFUSE the "
			              "configuration, and the symptom will be «nothing "
			              "shows» WITHOUT any other error.  ⚠ §4.3 does not "
			              "list the level among the farewells: the session stays "
			              "up, and this line is the only place where the "
			              "fact is written",
			              tenths / 10u, tenths % 10u,
			              requested_level_x10 / 10u, requested_level_x10 % 10u,
			              c->stream_level, alphabet, c->codec_string);
	}
	if (cycle_frames != 0)
		log_detail(LOG_CHILD,
		                   "codec %d: %zu bytes, %s, upload %llu us, "
		                   "encoding %llu us%s",
		                   (int)codec, fg.byte, fg.key ? "KEYFRAME" : "delta",
		                   (unsigned long long)fg.upload_us,
		                   (unsigned long long)fg.us_codifica,
		                   fg.trattenuto ? " — HELD BACK" : "");

	cycle_frames++;
	if (fg.key)
		cycle_keys++;

	{
		uint64_t t_dispatch = now_monotonic_us();
		send_frame(nr, fg.key, canvas_w, canvas_h, instant_us, fg.data,
		                 fg.byte, input);
		{
			uint64_t t_fine = now_monotonic_us();
			stretches_count(fo, &fg, t_fine - t_dispatch, t_fine);
		}
	}
	/* ⛔ The KEPT frame is still the one from switch-on — "send the stage
	 *    again" serves whoever comes back before the loop has delivered the
	 *    first.  ⚠ And only the KEYFRAME is kept: sending a delta again to
	 *    someone who does not have its past would be a wrecked image, that is
	 *    what §5.2 forbids the client to show. */
	if (nr < 3 && fg.key) {
		uint8_t *copied = (uint8_t *)malloc(fg.byte);
		if (copied) {
			memcpy(copied, fg.data, fg.byte);
			free(kept[nr]);
			kept[nr] = copied;
			kept_byte[nr] = fg.byte;
			kept_key[nr] = true;
			kept_w = canvas_w;
			kept_h = canvas_h;
			kept_instant = instant_us;
			kept_input = input;
		}
	}
	/* ⛔ The survey is written only if someone asked for it, and only the
	 *    first: sixty files per second are not a survey, they are a full disk. */
	if (cycle_frames <= 2)
		survey_write(dir_survey, file_name, fg.data, fg.byte);

	/* ⭐ THE ON-DEMAND SNAPSHOT — the box is above `shot_signal()`. */
	/* ⛔ And a `SIGUSR2` arrived when nothing was in progress does NOT stay
	 *    pending.  `[M]` 20 Aug 2026: a snapshot closed by hand six minutes
	 *    earlier had left `shot_stop` at 1, and the NEXT snapshot closed at
	 *    the first frame — "1 frames in `shot-stream.obu`".
	 *    ⚠ The survey was there and looked good: it is the worst form, a green
	 *    that looked at a single frame (`LESSONS.md` §1.9). */
	if (shot_stop && shot_state == 0)
		shot_stop = 0;
	if (shot_requested) {
		shot_requested = 0;
		if (shot_state != 0) {
			registro_dice(LOG_CHILD,
			              "⚠ SNAPSHOT: one is already in progress, the signal "
			              "does not open a second");
		} else if (!fo->pixel) {
			/* ⛔ On the card's road the pixels are not here: it is SAID,
			 *    instead of writing an empty file looking like a survey. */
			registro_dice(LOG_CHILD,
			              "⛔ SNAPSHOT impossible: the pixels are not in memory "
			              "(card's road), there is nothing to write");
		} else if (!shot_dir || !shot_dir[0] || strcmp(shot_dir, "-") == 0) {
			registro_dice(LOG_CHILD,
			              "⛔ SNAPSHOT impossible: the server has no survey "
			              "folder (`--survey`), there is nowhere to write");
		} else {
			codificatore_chiedi_chiave(cod);
			shot_state = 1;
			shot_count = 0;
			registro_dice(LOG_CHILD,
			              "⭐ SNAPSHOT requested: asked for a KEYFRAME, and from "
			              "that one input and stream go on disk in «%s»",
			              shot_dir);
		}
	}
	if (shot_state == 1 && fg.key && fo->pixel) {
		char fpath[512];

		/* ⛔ `survey_write()` says BY ITSELF whether it wrote or not: the
		 *    line below tells the geometry, not the outcome — and the two
		 *    things no longer get mixed. */
		survey_write(shot_dir, "shot-input.bgrx", fo->pixel,
		               (size_t)fo->byte);
		registro_dice(LOG_CHILD,
		              "⭐ SNAPSHOT: input %ux%u, stride %u, %llu bytes — the "
		              "stream starts from THIS keyframe",
		              fo->width, fo->height, fo->stride,
		              (unsigned long long)fo->byte);
		snprintf(fpath, sizeof fpath, "%s/shot-stream.obu", shot_dir);
		shot_fp = fopen(fpath, "wb");
		if (!shot_fp)
			registro_dice(LOG_CHILD, "⛔ SNAPSHOT %s: %s", fpath,
			              strerror(errno));
		shot_state = shot_fp ? 2 : 0;
		shots_left = SHOT_FRAMES;
	}
	if (shot_state == 2 && shot_fp) {
		if (fwrite(fg.data, 1, fg.byte, shot_fp) != fg.byte)
			registro_dice(LOG_CHILD,
			              "⛔ SNAPSHOT: short write on the stream — the file is NOT "
			              "decodable to the end");
		shot_count++;
		if (shot_stop || --shots_left <= 0) {
			shot_close(shot_dir, fo,
			              shot_stop ? "closed by hand with SIGUSR2"
			                          : "requested frames reached");
			shot_stop = 0;
		}
	}

	codificatore_rilascia(cod);
	return true;
}

/* ⛔ The stage belongs to the SESSION, not to the connection: `mutter` and
 *    `capture` stay open as long as the child lives, because the virtual
 *    monitor exists as long as someone consumes the stream.  ⚠ It is
 *    invariant I4 made of processes: what dismantles the stage is the child's
 *    death, not the fall of a connection.
 *
 * ⛔⭐ BUT THE STAGE MAY NOT BE THERE, AND THEY ARE TWO CASES THAT ARE THE SAME —
 *     `[M]` from the user's real session, 14 Aug 2026:
 *
 *   · **not there yet**: if the graphical session does not exist when the
 *     child is born, this function failed and **nobody ever tried another**.
 *     At the next login invariant I2 handed the user **that very child** —
 *     and the user saw "no desktop" twice in a row;
 *   · **no longer there**: if the graphical session dies under a live child,
 *     the PipeWire stream goes into `connection error`, `capture_take`
 *     returns **at once** with a fault, and the loop spun idle writing the log
 *     in bursts — ⛔ **30.8 GB and 112 million identical lines**, that is the
 *     disk of a real machine.
 *
 * ⇒ ⭐ They are the two ends of the same thing — *the child does not know its
 *   stage is no longer there, or not there yet* — and the cure is one: **the
 *   stage is mounted, dismantled and REMOUNTED**, with a growing wait.
 * ⚠ And it does not die: `SPECS.md` §8.3 forbids disconnecting, and a
 *   frozen session is worth more than a closed one.  ⛔ But a child **without
 *   a stage** is not a frozen session: it is a child that is of no use, and
 *   that is why it keeps retrying instead of sitting there.
 *
 * `first` = it is the birth: the diagnosis is made (the two frames proving
 * that the stage works) and the survey is written.  ⚠ Not on a remount: those
 * two are not frames of the movement, and redoing them would reset the loop's
 * counts in the middle of a live session. */
static bool take_stage(uint32_t canvas_w, uint32_t canvas_h,
                            const char *dir_survey, bool first,
                            MutterSession **out_m, Capture **out_c)
{
	struct body_stage p;
	GError *mistake = NULL;
	GDBusConnection *bus;
	CaptureStopped fo;
	CaptureTake take;
	uint64_t instant_us;
	MutterSession *mut = NULL;
	Capture *cat = NULL;
	/* ⏱ the steps' stopwatch — see the box below */
	const char *chrono_name = "";
	uint64_t chrono_ms = 0;

	/* ⛔⛔⭐ THE ENVELOPE IS ZEROED HERE, BEFORE ANY EXIT PATH — and until
	 *       27 Aug 2026 this `memset` sat THREE HUNDRED lines further down,
	 *       that is **after** a `send_msg(MSG_STAGE, &p, …)`.
	 *
	 * ⛔ That branch — "waiting for the client's canvas" — sent the parent a
	 *    structure never written: field by field, stack memory as the
	 *    previous call had left it.
	 *
	 * `[M]` 27 Aug 2026, and it has already produced a wrong diagnosis that
	 * lasted months: the so-called "third state" of the stage, the line *"(0
	 * before, 2 after)"*, was GARBAGE.  ⇒ It appeared even on machines where
	 * no monitor could have been born, always and only on that line, and next
	 * to numbers that unmasked themselves (`stride 958311266`).  For months
	 * that `2` was read as "two monitors appeared": it was a number nobody
	 * had ever written.
	 *
	 * ⚠ And the comment below already said it — "an early exit path would
	 *   have reported without having looked at anything" — but it sat AFTER
	 *   the early exit it described.  ⇒ It is form E8 inside the line meant
	 *   to unmask it, and it is also `LESSONS.md` §1.50: a right comment in
	 *   the wrong place protects nothing.
	 *
	 * ⛔ Whoever adds an early exit to this function no longer needs to think
	 *    about it: above this line nothing is sent, below it the envelope is
	 *    clean and declares "I could not look". */
	memset(&p, 0, sizeof p);
	/* ⛔ "I could not look" is the STARTING value, not "healthy": with the zero
	 *    of the `memset` an early exit path would have reported
	 *    `SESSION_HEALTHY` without having looked at anything — "empty" and
	 *    "forbidden" with the same face, error form E8, inside the line meant
	 *    to unmask it.  `[M]` seen in the log of 12 Aug 2026: the stage of
	 *    "prova" said "session 0" and nobody had read it. */
	p.state_session = (uint32_t)SESSION_NOT_READ;

	/*
	 * ⭐ AND FIRST OF ALL: if someone is waiting for a canvas, they are told.
	 *
	 * ⛔ Mounting the stage takes SECONDS — the session being born,
	 *    `ScreenCast`, the PipeWire negotiation — and in all that time this
	 *    function sends nothing.  ⚠ The deadline of §7.1 is three seconds:
	 *    without this line it would expire **inside** the mounting, that is
	 *    precisely while the answer is being prepared.
	 */
	/*
	 * ⛔⭐⭐ AND THE FIRST LINE IS WRITTEN BY THE CHILD, BEFORE TALKING TO THE PARENT.
	 *
	 * `[M]` 16 Aug 2026: in the twenty-one-second hole the only line at the
	 * boundary was written by **the parent** (when it received the "wait"),
	 * and from a parent's line one does not know when the CHILD sent it — one
	 * knows when the parent read it.  ⛔ It is form E6, the sender inferred
	 * instead of asked, inside the very boundary meant to delimit the defect.
	 *
	 * ⇒ Now the child says "about to speak" and "I have spoken", and between
	 *   the two lines there is only `send_msg()`: if the seconds are there, they
	 *   show.
	 */
	log_detail(LOG_CHILD,
	                   "entering the stage mounting (canvas %ux%u): telling the parent "
	                   "to wait",
	                   canvas_w, canvas_h);

	/*
	 * ⛔⭐⭐⭐ NOTHING IS MADE TO BE BORN UNTIL THE SIZE IS KNOWN.
	 *
	 * ⭐ It is the cure for the tail of login times, and the reason is spelled
	 *    out in full in the box of `canvas_from_client`: a stage mounted at the
	 *    fallback must be resized, and on Wayland the resize completes only
	 *    when the compositor delivers a frame — that is NEVER, on a freshly
	 *    born desktop that does not move.
	 *
	 * ⚠ Half a second of waiting here is worth thirteen seconds of race later.
	 *
	 * ⛔ And the wait has a CEILING, it is not forever: invariant I1 forbids
	 *    standing still out of caution.  If the client does not declare its
	 *    window within `CANVAS_WAIT_MS`, we start with the fallback and
	 *    DECLARE it — better a desktop to resize than no desktop.
	 */
	if (!canvas_from_client) {
		static uint64_t first_round_ms;
		uint64_t t_now = log_now_ms();

		if (first_round_ms == 0)
			first_round_ms = t_now;
		if (t_now - first_round_ms < CANVAS_WAIT_MS) {
			log_detail(LOG_CHILD,
			                   "waiting for the client's canvas before making anything "
			                   "be born (%llu ms of %d): mounting at the fallback "
			                   "would mean resizing, and the "
			                   "resize on a still scene does not "
			                   "complete",
			                   (unsigned long long)(t_now - first_round_ms),
			                   CANVAS_WAIT_MS);
			p.state_session = (uint32_t)SESSION_NOT_READ;
			snprintf(p.fault, sizeof p.fault,
			         "waiting for the client's canvas");
			send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
			return false;
		}
		if (!canvas_from_client) {
			static bool said;

			if (!said) {
				said = true;
				registro_dice(LOG_CHILD,
				              "⚠ the client did not declare its window "
				              "within %d ms: starting with the fallback %ux%u.  ⛔ The "
				              "desktop will be born at a size nobody "
				              "asked for and will have to be resized — but a desktop "
				              "to resize beats no desktop (I1)",
				              CANVAS_WAIT_MS, canvas_w, canvas_h);
			}
		}
	}
	if (canvas_w && canvas_h)
		wait_canvas(canvas_w, canvas_h);
	log_detail(LOG_CHILD, "the «wait» has gone out: now the bus");

	/*
	 * ⛔⭐⭐ THE STOPWATCH INSIDE THE STEPS, and it is not a luxury: it is the
	 *       tool I had to build after THREE wrong diagnoses in a row.
	 *
	 * `[M]` 16 Aug 2026.  The measure said "median 3.2 s, p90 21 s", and the
	 * log between the two lines delimiting the hole did not have **a single
	 * line**.  ⇒ From outside one could only INFER which step was eating them,
	 * and I inferred wrong three times: first the doubling wait, then the user
	 * manager, then the poll to Mutter.  Each time the cure was reasonable and
	 * the next measure said no.
	 *
	 * ⭐ A step that can last twenty seconds and leaves no trace is a step on
	 *    which one can only guess — and it is exactly the form this project has
	 *    always paid for (`LESSONS.md` §1.9: silence and health with the same
	 *    face).
	 *
	 * ⚠ And it is written only when the step is SLOW: a fast step has nothing
	 *   to say, and filling the log with normal lines is the way to make the
	 *   ones that count go unread.
	 */
#define SLOW_STEP_MS 250
#define CHRONO_START(name) \
	do { \
		chrono_name = (name); \
		chrono_ms = log_now_ms(); \
	} while (0)
#define CHRONO_END() \
	do { \
		uint64_t chrono_duration = log_now_ms() - chrono_ms; \
		if (chrono_duration >= SLOW_STEP_MS) \
			registro_dice(LOG_CHILD, \
			              "⏱ the step «%s» took %llu ms — it is THAT step that " \
			              "holds the child still, not «the session being born»", \
			              chrono_name, (unsigned long long)chrono_duration); \
	} while (0)

	/* ⚠ `memset(&p, …)` and `p.state_session = SESSION_NOT_READ` used to be
	 *   HERE, and from here they did not cover the `send_msg(MSG_STAGE, …)` of the
	 *   "waiting for the client's canvas" branch, which is further up.  ⇒ Moved
	 *   to the top of the function, 27 Aug 2026: the full reason is written
	 *   there. */

	/* ⛔⭐ THE BUS, AND IT IS THE MEASURE THAT DECIDES THE WHOLE MANDATE.  `[M]`
	 *     root does not connect here; this process is the user, and it either
	 *     connects or says why. */
	CHRONO_START("open the session bus");
	bus = sess_bus(&mistake);
	CHRONO_END();
	if (!bus) {
		snprintf(p.fault, sizeof p.fault, "session bus: %s",
		         mistake ? mistake->message : "(no details)");
		registro_dice(LOG_CHILD,
		              "⛔ I do NOT have the session bus: %s.  ⚠ It is not «there is "
		              "no session», it is «I could not look» — and without a bus there "
		              "is nothing to capture",
		              p.fault);
		g_clear_error(&mistake);
		send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
		return false;
	}
	p.bus_open = 1;
	g_object_unref(bus);
	registro_dice(LOG_CHILD,
	              "⭐ THE SESSION BUS IS MINE: connected as uid %ld — the "
	              "thing the root parent CANNOT do (P2-6-montaggio.md §5.4)",
	              (long)geteuid());

	/*
	 * ⛔⭐⭐ AND NOW WE TOUCH — 15 Aug 2026, phase 5.
	 *
	 * ⛔ Here it said "look, don't touch: making a session BE BORN belongs to
	 *    the real login, not to this mandate", and for phase 2 it was right.
	 *    ⭐ At phase 5 that mandate **is this one** — `PLAN.md`: "Produces:
	 *    PAM in full" — and since this process opens the PAM session itself
	 *    (`become_and_exec`, step 2-bis) `/run/user/<uid>` exists by
	 *    construction: the objection that line carried has fallen.
	 *
	 * ⛔ THE PRICE OF NOT DOING IT, measured on the evening of 15 Aug: the
	 *    machine reboots, nobody remakes the session, and the user enters and
	 *    **sees nothing**.  The log said three times "SESSION DEAD: I look and
	 *    don't touch", which is a perfect diagnosis of a product that does not
	 *    do its job.
	 *
	 * ⚠ AND IT DOES NOT WAIT: `session_spawn()` asks and returns.  The
	 *   wait already exists and is our retry loop (1 s → 30 s); a second wait
	 *   inside this process would be 40 s in which the parent receives neither
	 *   a frame nor an answer (`LESSONS.md` §6.2-bis).
	 *
	 * ⚠ And it is asked at most once a minute: `gnome-session` takes a few
	 *   seconds to show up on the bus, and without this rein every retry would
	 *   start another one.
	 */
	CHRONO_START("read the session state (GetCurrentState)");
	p.state_session = (uint32_t)session_state(canvas_w, canvas_h, NULL);
	CHRONO_END();
	{
		/*
		 * ⭐⭐ "IT WAS THERE AND NOW IT IS NO LONGER" — §7.6, the twin, and the
		 *     distinction that decides ALL the behaviour.
		 *
		 * ⛔ A DEAD session means two opposite things:
		 *
		 *   · it was NEVER there (first attach, machine just rebooted)
		 *     ⇒ it is made to be born, and that is what the user expects;
		 *   · it was there and the user LOGGED OUT from the desktop menu
		 *     ⇒ ⛔ it is NOT remade: remaking it would mean **preventing them
		 *       from logging out**.  Whoever is watching is warned with `0x10`,
		 *       and the next one will be born at the next attach
		 *       (`DECISIONS.md` §4.1-quater: "the page goes back to the login
		 *       form").
		 *
		 * ⚠ And the same holds if the compositor DIED by itself: from our side
		 *   it is indistinguishable from a logout, and the right behaviour is
		 *   the same — telling whoever is watching instead of making a desktop
		 *   the user had closed reappear.
		 */
		if (p.state_session != SESSION_DEAD &&
		    p.state_session != SESSION_NOT_READ)
			vista_viva = true;
		else if (p.state_session == SESSION_DEAD && vista_viva) {
			vista_viva = false;
			session_closed_by_user = true;
			registro_dice(LOG_CHILD,
			              "⭐ §7.6: the graphical session WAS THERE and now is NO "
			              "LONGER — the user logged out from the "
			              "desktop menu.  ⛔ I am NOT making it be born again: remaking it "
			              "would mean preventing them from logging out.  Warning the "
			              "parent, which gives whoever is watching the farewell 0x10");
			send_msg(MSG_SESSION_FINISHED, NULL, 0, NULL, 0);
			send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
			/* ⭐ and nobody who had detached from the desktop stays in the scope */
			session_clear_out_scope();
			/* ⭐ R1/R2: the user at the monitor finds the manager as it was */
			session_clear_out_handler("the session is over (§7.6)");
			return false;
		}
	}
	if (p.state_session == SESSION_DEAD && session_closed_by_user) {
		/* ⛔ The third state: the user LOGGED OUT.  Remaking it now would mean
		 *    making the desktop they just closed reappear — that is preventing
		 *    them from logging out.  A NEW attach is awaited. */
		log_detail(LOG_CHILD,
		                   "the graphical session of «%s» was CLOSED "
		                   "by the user: not remaking it until someone "
		                   "reattaches",
		                   g_get_user_name());
	} else if (p.state_session == SESSION_DEAD) {
		uint64_t current_ms = log_now_ms();

		if (!is_being_born(current_ms)) {
			birth_requested_ms = current_ms;
			registro_dice(LOG_CHILD,
			              "⭐ no graphical session for «%s»: I AM MAKING IT "
			              "BE BORN (canvas %ux%u) and returning at once — "
			              "finding it is the next attempt's job",
			              g_get_user_name(), canvas_w, canvas_h);
			if (!session_spawn(canvas_w, canvas_h))
				registro_dice(LOG_CHILD,
				              "⛔ the graphical session of «%s» did not "
				              "start: the stage will be left with nothing to "
				              "capture, and the «session» lines above "
				              "say why",
				              g_get_user_name());
		} else {
			registro_dice(LOG_CHILD,
			              "the graphical session of «%s» is not there yet: "
			              "I already asked for it %llu ms ago and am waiting for it "
			              "to show up on the bus",
			              g_get_user_name(),
			              (unsigned long long)(current_ms - birth_requested_ms));
		}
	} else if (p.state_session != SESSION_HEALTHY) {
		registro_dice(LOG_CHILD,
		              "⚠ this user's graphical session is «%s» (%u): "
		              "not touching it — states other than «dead» are governed by "
		              "session_ensure(), and bringing down a live one would take "
		              "the desktop away from whoever is watching it (I4)",
		              session_mark((SessionState)p.state_session),
		              p.state_session);
	}

	/*
	 * ⛔⭐⭐ WE DO NOT MOUNT ON TOP OF A COMPOSITOR THAT HAS NOT ANSWERED — 16 Aug
	 *       2026, and it is the other half of `WAIT_POLL_MS`.
	 *
	 * ⛔ `SESSION_NOT_READ` does not mean "not there" and does not mean
	 *    "there": it means **"it has its name on the bus and did not answer
	 *    me"**, that is it is still being born.  ⇒ Going on to mount would
	 *    mean making a more expensive call to that same silent compositor —
	 *    `CreateSession` on RemoteDesktop, which in `mutter.c` has a ceiling
	 *    of **fifteen seconds**.
	 *
	 * ⚠ That is, the block would be moved instead of removed: the short poll
	 *   would needs no purpose, and the child would stay silent all the same.
	 *
	 * ⭐ The right answer is the one the loop already knows how to use: "not
	 *    now".  We return, say "WAIT" to the parent, and retry in 200 ms.
	 */
	if (p.state_session == (uint32_t)SESSION_NOT_READ) {
		snprintf(p.fault, sizeof p.fault,
		         "the compositor did not answer the poll: it is still being born");
		log_detail(LOG_CHILD,
		                   "the compositor of «%s» has its name on the bus but did not "
		                   "answer within the poll: I am NOT trying to mount on "
		                   "top of it — it would be a fifteen-second call to "
		                   "someone who does not answer.  Retrying shortly",
		                   g_get_user_name());
		send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
		return false;
	}

	/*
	 * ⭐⭐ PHASE 13 — ON XFCE THERE IS NO STAGE TO OPEN FIRST.
	 *
	 * On GNOME Mutter is asked for a virtual monitor; on KDE KWin is asked for
	 * the stream of the one that exists.  ⛔ On wlroots there is no stream to
	 * mount: we talk directly to the compositor, and the source is the capture
	 * itself (`capture_start_wlr`, further down).
	 *
	 * ⇒ Nothing is done here, and we say why: an empty branch without a line
	 *   looks like a forgotten branch.
	 */
	/* ⭐ PHASE 14 — `session_on_wlroots()` and not `== XFCE`, here and in the
	 *    other four places of this file (capture, input, clipboard, remount):
	 *    the question is about the COMPOSITOR, and labwc serves XFCE and LXQt
	 *    (`session.h`).  ⛔ With `== XFCE` LXQt fell into the GNOME/KDE branch,
	 *    without a warning. */
	if (session_on_wlroots()) {
		/*
		 * ⛔⭐⭐ BUT WE DO NOT MOUNT UNTIL THE SESSION MANAGER IS ON THE BUS
		 *       — 24 Sep 2026, and it was the LXQt logout that did not close.
		 *
		 * `[M]` On LXQt "Log out" made the session BE BORN AGAIN instead of
		 * closing it: 16 times out of 20.  The chain, read from the code
		 * (`[R]`):
		 *
		 *   1. labwc is already there, `lxqt-session` not yet ⇒ the state says
		 *      DEAD, and this branch mounted the capture ANYWAY (labwc
		 *      answers);
		 *   2. on this family "seen alive" is turned on ONLY by reading the
		 *      state at mounting (above) ⇒ and the mounting had read it DEAD:
		 *      `vista_viva` stayed false for the whole session;
		 *   3. at "Log out" the stage falls, the remount reads DEAD with
		 *      `vista_viva` false ⇒ "it was never there" ⇒ IT MAKES IT BE BORN.
		 *
		 * ⚠ `wlr-randr` before `exec lxqt-session` (e4ecfbb) widens the window
		 *   between labwc and the manager, and makes the race almost certain.
		 *
		 * ⭐ The cure is the form of `SESSION_NOT_READ` above: "not now".  We
		 *    return, the parent hears WAIT, and the loop retries densely
		 *    (`STAGE_BIRTH_RETRY_MS`, while it is being born or someone is
		 *    watching).  The mounting that succeeds has read SANA, and
		 *    `vista_viva` is true by construction.
		 * ⛔ And the birth is NOT requested at every round: the rein is
		 *    `is_being_born()` (above), and after the rein
		 *    `session_spawn()` refuses while labwc is alive
		 *    (`inactive_unit()`).  It is the same fate as GNOME when Mutter
		 *    does not appear: the mounting fails and is retried.
		 * ⚠ And if the manager NEVER appears (broken session) we do not stay
		 *   silent: every five seconds a line says so, with the time since the
		 *   birth was requested.
		 */
		if (p.state_session == SESSION_DEAD) {
			static uint64_t logged_ms;
			uint64_t now_ms = log_now_ms();

			snprintf(p.fault, sizeof p.fault,
			         "the session manager is not on the bus yet");
			if (now_ms - logged_ms >= 5000) {
				logged_ms = now_ms;
				registro_dice(LOG_CHILD,
				              "⏳ %s: labwc perhaps is there, the session manager "
				              "is NOT (birth requested %llu ms ago) — ⛔ not mounting "
				              "the capture: a mounting that reads DEAD does not "
				              "turn on «seen alive», and the «Log out» after would make it "
				              "BE BORN AGAIN.  Retrying shortly",
				              desktop_session() == SESSION_DESKTOP_LXQT ? "LXQt" : "XFCE",
				              birth_requested_ms
				                  ? (unsigned long long)(now_ms - birth_requested_ms)
				                  : 0ULL);
			}
			send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
			return false;
		}
		log_detail(LOG_CHILD,
		                   "%s: no stage to open — on this family the "
		                   "capture talks to the compositor without going through a "
		                   "mounted stream",
		                   desktop_session() == SESSION_DESKTOP_LXQT ? "LXQt" : "XFCE");
		/*
		 * ⛔⛔ AND HERE `vista_viva = true` IS NOT WRITTEN — 21 Sep 2026, and it
		 *     cost the user's farewell.
		 *
		 * `[M]` The first draft wrote it, by analogy with the KDE branch.  But
		 * on KDE it comes AFTER a successful `kwin_open()`, that is after a
		 * fact; here it came before any fact.  ⇒ The capture tried to open half
		 * a second before labwc was ready, failed, and at the next round the
		 * state said DEAD with `vista_viva` already true: *"the session was
		 * there and now it is no longer — the user logged out"*, farewell
		 * 0x10, and the client thrown out of a desktop that was being born.
		 * ⭐ On XFCE "seen alive" is already set by reading the state, when the
		 *   session manager appears on the bus: that is the right fact, and it
		 *   is enough.
		 */
	} else if (desktop_session() == SESSION_DESKTOP_KDE) {
		/* ⭐ On KDE the monitor is already there (`kwin_wayland --virtual`, born
		 *    with the session): KWin is asked for its stream.  The GNOME branch
		 *    below is not touched. */
		close_stage_kwin();
		if (!kwin_host_settle(3.0, &mistake)) {
			registro_dice(LOG_CHILD, "⚠ KDE: KWin's output did not settle on the host's "
			                          "size (%s): mounting anyway",
			              mistake ? mistake->message : "?");
			g_clear_error(&mistake);
		}
		CHRONO_START("mount the stage (kwin_open)");
		stage_kwin = kwin_open(&mistake);
		CHRONO_END();
		if (!stage_kwin) {
			snprintf(p.fault, sizeof p.fault, "KWin: %s",
			         mistake ? mistake->message : "(no details)");
			registro_dice(LOG_CHILD, "⛔ no stream from KWin: %s", p.fault);
			g_clear_error(&mistake);
			send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
			return false;
		}
		vista_viva = true;
	} else {
	CHRONO_START("mount the stage (mutter_apri)");
	mut = mutter_open(&mistake);
	CHRONO_END();
	if (!mut) {
		snprintf(p.fault, sizeof p.fault, "ScreenCast: %s",
		         mistake ? mistake->message : "(no details)");
		registro_dice(LOG_CHILD, "⛔ no virtual monitor to capture: %s",
		              p.fault);
		g_clear_error(&mistake);
		send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
		return false;
	}
	}

	/* ⭐ PHASE 17 — we come back here ONCE, if the card was refused:
	 *    `falls_back_if_refused()`.  The stage (Mutter or KWin) stays the same. */
remount_capture:
	/* ⛔ The rate is asked ONCE and with ONE name: `MOTION_FPS`.  Here there
	 *    was the literal 60 and the encoding request declared 30 — two
	 *    different numbers for the same quantity. */
	/* ⛔ The route is DECLARED in the log at mounting, because it is the fact
	 *    that explains all the stretch numbers that will come later: a
	 *    "conversion 0.9 ms" on the card and one on memory are not the same
	 *    quantity. */
	registro_dice(LOG_CHILD,
	              "⭐ the stage mounts on the «%s» route%s",
	              stage_route == CAPTURE_ROUTE_CARD
	                  ? "CARD (DMA-BUF, zero copy)"
	                  : "MEMORY (the pixels are copied)",
	              stage_route == CAPTURE_ROUTE_CARD
	                  ? " — ⚠ it holds only if the encoder is in hardware, and if it "
	                    "is not this stage is remounted on memory, declaring it"
	                  : "");
	stage_size(&canvas_w, &canvas_h);
	/* ⭐ PHASE 13 — the other door: the source within reach.  ⛔ `stage_node()`
	 *    is not even called, because on this family a node does not exist. */
	if (session_on_wlroots()) {
		slabs_per_route();
		cat = capture_start_wlr(canvas_w, canvas_h, MOTION_FPS, stage_route,
		                        CAPTURE_COLOR_BGRX, &mistake);
	} else {
		modifiers_per_route();
		cat = capture_start(stage_node(mut), canvas_w, canvas_h, MOTION_FPS,
		                    stage_route, CAPTURE_COLOR_BGRX, NULL, NULL,
		                    NULL, &mistake);
	}
	if (!cat && falls_back_if_refused(
	                mistake && g_error_matches(mistake, G_IO_ERROR,
	                                           G_IO_ERROR_NOT_SUPPORTED),
	                mistake ? mistake->message : NULL)) {
		g_clear_error(&mistake);
		goto remount_capture;
	}
	if (!cat) {
		snprintf(p.fault, sizeof p.fault, "capture: %s",
		         mistake ? mistake->message : "(no details)");
		registro_dice(LOG_CHILD, "⛔ the capture does not open: %s", p.fault);
		g_clear_error(&mistake);
		mutter_close(mut);
		close_stage_kwin();
		send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
		return false;
	}
	/* ⭐ PHASE 12 — on Plasma the cursor theme is invisible on purpose
	 *    (`session.c`), so the metadata will always say "no image": that
	 *    hiding must NOT be delivered, or whoever is watching is left without a
	 *    pointer (`cursor.h`, and `[M]` the user's test of 20 Sep 2026). */
	if (stage_kwin) {
		capture_cursor_never_hide(cat, "KWin --virtual: the session's cursor "
		                                    "theme is invisible");
		/* ⭐ 15 Oct 2026 — `[M]` KWin sends ~50 frames/s where 5 change
		 *    (`unchanged.h`): the copies of the same picture are not encoded. */
		capture_skip_unchanged(cat, "KWin: whole frames and exact damage");
	}
	*out_m = mut;
	*out_c = cat;

	memset(&fo, 0, sizeof fo);
	take = capture_take(cat, 5.0, &fo, &mistake);
	instant_us = frame_instant(&fo, now_monotonic_us());
	p.take = (uint32_t)take;
	/* ⛔ `PIXEL_ALTROVE` IS A DELIVERED FRAME, not a no-show: on the card's
	 *    road the pixels are not in memory, and the frame is there all the
	 *    same (`capture.h`).  ⚠ Treating it as a fault here would mean
	 *    dismantling the stage at every successful mounting. */
	/* ⭐ PHASE 17 — the refusal that arrives AFTER `capture_start()`: it is the
	 *    measured case (`[M]` 29 Sep, grab 2 "fell during the grab, fault: no
	 *    more input formats").  Only the capture is stopped, and reopened. */
	if (take != CAPTURE_TAKE_DONE && take != CAPTURE_TAKE_PIXEL_ELSEWHERE &&
	    falls_back_if_refused(capture_format_refused(cat),
	                         capture_fault(cat))) {
		g_clear_error(&mistake);
		capture_stopped_free(&fo);
		capture_stop(cat);
		cat = NULL;
		*out_c = NULL;
		goto remount_capture;
	}
	if (take != CAPTURE_TAKE_DONE && take != CAPTURE_TAKE_PIXEL_ELSEWHERE) {
		snprintf(p.fault, sizeof p.fault, "grab %u: %s", (unsigned)take,
		         mistake ? mistake->message : "no frame");
		registro_dice(LOG_CHILD,
		              "⛔ no frame in 5 s (%s): it is a RESULT if the "
		              "desktop has not changed, a fault if the stream never "
		              "started — and the two numbers are different on purpose",
		              p.fault);
		g_clear_error(&mistake);
		/* ⛔⭐ AND HERE IT IS DISMANTLED, instead of staying with half a stage.
		 *
		 *     Before, it returned leaving `*out_c` full: the loop found a live
		 *     capture that did not deliver, and had no way of telling it apart
		 *     from a healthy one.  ⚠ "The stream never started" and "the scene
		 *     is still" are two different things (`capture.h`), and this is the
		 *     first.  ⇒ It is dismantled, and the caller will retry. */
		capture_stopped_free(&fo);
		capture_stop(cat);
		mutter_close(mut);
		close_stage_kwin();
		*out_c = NULL;
		*out_m = NULL;
		send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
		return false;
	}

	/* ⛔ The monitor's name AFTER the first frame, not after `capture_start`:
	 *    the seam corrected on 12 Aug 2026 (`P2-6-montaggio.md` §5.1). */
	if (!mut && stage_kwin) {
		/* ⭐ On KDE the monitor is the session's, and `kwin.c` has already said
		 *    the scale if it is not 1.  "Before" and "after" are the same
		 *    number: the stage adds none. */
		p.monitor_before = p.monitor_after = kwin_output_count(stage_kwin);
		snprintf(p.monitor, sizeof p.monitor, "%s",
		         kwin_output_name(stage_kwin) ? kwin_output_name(stage_kwin)
		                                      : "(no name)");
	} else if (!mut) {
		/* ⭐ PHASE 13 — on wlroots there is neither a Mutter session nor a KWin
		 *    stage: the monitor is the compositor's output, and the capture has
		 *    already said so.  ⛔ Without this branch `mutter_find_monitor(NULL)`
		 *    was called, which is a failed assertion in the log — noise that
		 *    looks like a fault, `[M]` 21 Sep 2026. */
		uint32_t l = 0, a = 0;

		capture_negotiated_size(cat, &l, &a);
		p.monitor_before = p.monitor_after = 1;
		snprintf(p.monitor, sizeof p.monitor, "%s",
		         capture_output_name(cat) ?: "(the compositor's output)");
	} else if (mutter_find_monitor(mut)) {
		guint before = 0, after = 0;
		double scale_factor;

		mutter_monitor_counts(mut, &before, &after);
		p.monitor_before = before;
		p.monitor_after = after;
		snprintf(p.monitor, sizeof p.monitor, "%s", mutter_our_monitor(mut));

		/* ⛔⭐⭐ GUARD 2 OF §5.0-sexies, AND SINCE TONIGHT IT IS A CONDITION OF
		 *     SERVICE — "read the scale and FAIL if it is not 1.0".
		 *
		 * ⚠ Until yesterday it was read and stated, and that was enough: with
		 *   the canvas fixed at 1920x1080 the damage was theoretical.  ⛔ Since
		 *   tonight the canvas takes the client's size, so the logical monitor's
		 *   layout and the stream's pixels really diverge — and that layout **is
		 *   the coordinate space of the input**: `[M]` with
		 *   `scaling-factor = 2` the layout of a 2133 canvas becomes
		 *   `1067 x 2 = 2134`, and the pointer goes elsewhere **without any line
		 *   saying so**.
		 *
		 * ⛔ And it FAILS instead of serving: a desktop that is seen and driven
		 *    WRONG is worse than a desktop that does not start, because the
		 *    second has a line explaining it and the first does not.  ⚠ And it
		 *    is not a death: the stage is remounted with the growing wait, so as
		 *    soon as the user changes the setting the session restarts by
		 *    itself.
		 *
		 * ⛔ "I don't know" is NOT "fine": if the scale could not be read we go
		 *    on declaring it, because refusing on an absence of data would shut
		 *    down the service on a machine that has no defect. */
		scale_factor = mutter_our_scale(mut);
		/* ⛔ AND THE GOOD CASE IS WRITTEN, not left to silence: "the guard looked
		 *    and the scale is 1.0" and "the guard was not run" would have the
		 *    same face — which is the error form this project pays for most
		 *    often.  ⚠ One line per stage mounting, not per frame. */
		if (scale_factor == 1.0)
			registro_dice(LOG_CHILD,
			              "⭐ guard 2 (§5.0-sexies): the scale of our monitor "
			              "«%s» is 1.000 — the input's coordinate space "
			              "coincides with the stream's pixels",
			              p.monitor);
		if (scale_factor < 0)
			registro_dice(LOG_CHILD,
			              "⚠ the scale of our logical monitor could not be "
			              "read: I GO ON, and I do not say 1.0 out of habit "
			              "(guard 2 of DECISIONS.md §5.0-sexies)");
		else if (scale_factor != 1.0) {
			registro_dice(LOG_CHILD,
			              "⛔⛔ SCALE %.3f on OUR monitor «%s» instead of 1.0: "
			              "the input's coordinate space does not coincide with "
			              "the stream's pixels, and the pointer would go elsewhere "
			              "without anything saying so.  ⇒ I am NOT taking the stage "
			              "(guard 2 of DECISIONS.md §5.0-sexies).  The cure is "
			              "a single line, on this user's session: "
			              "`gsettings set org.gnome.desktop.interface "
			              "scaling-factor 0` — then the session restarts by itself, "
			              "without restarting anything",
			              scale_factor, p.monitor);
			p.state_session = 0;
			snprintf(p.fault, sizeof p.fault,
			         "scale %.3f instead of 1.0 on monitor «%s»: the pointer "
			         "would go elsewhere (guard 2, DECISIONS.md §5.0-sexies)",
			         scale_factor, p.monitor);
			capture_stopped_free(&fo);
			send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);
			return false;
		}
	} else {
		snprintf(p.monitor, sizeof p.monitor, "(I could not tell)");
	}

	p.width = fo.width;
	p.height = fo.height;
	p.stride = fo.stride;
	p.bit = (uint32_t)fo.delivery.bit_per_channel;
	registro_dice(LOG_CHILD,
	              "⭐ frame captured AS «%s»: %ux%u, stride %u READ, "
	              "%llu bytes, %s at %d bits, %s",
	              getenv("USER") ? getenv("USER") : "?", fo.width,
	              fo.height, fo.stride, (unsigned long long)fo.byte,
	              fo.delivery.fmt ? fo.delivery.fmt : "(unknown)",
	              fo.delivery.bit_per_channel,
	              /* ⛔ THREE answers and not two: since 22 Aug 2026 the pass over
	               *    the pixels is done at a cadence (`capture.c`,
	               *    `PIXEL_SCAN_EVERY_MS`), and on a frame not looked at
	               *    `nero == FALSE` means **"I did not look"**, not "it is
	               *    not black".  ⚠ Here it is always the FIRST frame — which
	               *    is always looked at — but the line is written right
	               *    anyway: it is the one that one day will be copied
	               *    elsewhere. */
	              !fo.delivery.measured_pixels ? "⚠ the pixels were not looked at "
	                                            "(cadence): it is NOT «not black»"
	              : fo.delivery.nero          ? "⛔ BLACK"
	                                          : "not black");

	survey_write(dir_survey, "cattura.bgrx", fo.pixel, (size_t)fo.byte);

	/* ⛔⭐ AND THIS FIRST ENCODING STAYS, even if there is the loop now: it does
	 *     not needs to send, it serves to PROVE the stage works before anyone
	 *     asks for it.  `p.streams` is the number `MSG_STAGE` carries to the
	 *     parent, and it is the only line that distinguishes "nobody is
	 *     watching" from "the encoder does not open".  ⚠ And the two encoders
	 *     stay OPEN: they are the ones the loop will use.
	 * ⛔ §5.2: both first frames must be a KEYFRAME, and it is asked instead of
	 *    hoped for. */
	key_debt[1] = key_debt[2] = key_debt[3] = true;
	if (first) {
		/* ⚠ `input = 0` and it is NOT a placeholder value: §6.2 says "0 if
		 *   none", and here there is nobody yet — the input channel is born
		 *   when the client opens its stream, and these two frames are the
		 *   diagnosis of switch-on, not of movement. */
		/* ⛔⛔ AND THE SIZE IS THE FRAME'S, not the requested one — defect found
		 *     while refuting, on the night of 15 Aug 2026.
		 *
		 *     Here the encoder was born at `canvas_w x canvas_h` (the REQUESTED)
		 *     and was fed with `fo.pixel`/`fo.stride` (the ARRIVED), without
		 *     the reconciliation and without the guard on the bytes, both of
		 *     which live in the loop further down.  ⚠ Today the case is
		 *     unreachable — the proposal declares the size as a FIXED
		 *     rectangle, so either it is obtained or the negotiation fails —
		 *     ⛔ but the new code RECOGNISES the "granted differs from
		 *     requested" case (§4.5) and protected it in one place and not in
		 *     the other: an inconsistency within the same change.  ⇒ Here what
		 *     the pixels are is used, and the same guard as the loop decides
		 *     whether they can be touched. */
		if (fo.stride >= (guint64) fo.width * 4u
		    && fo.byte >= (guint64) fo.stride * fo.height) {
			if (encode_and_send(&fo, CODIFICATORE_HEVC, 1, dir_survey,
			                     "flusso-hevc.265", instant_us, fo.width,
			                     fo.height, 0))
				p.streams++;
			/* ⛔ AV1 is gone: it was encoded only in software (SVT-AV1), and
			 *    the software fallback left with phase 19. */
			/* ⭐ The second, since 20 August: a client negotiating H.264 finds
			 *    the first frame already in the deposit like the other, instead
			 *    of waiting for something to move on the desktop. */
			if (encode_and_send(&fo, CODIFICATORE_H264, 3, dir_survey,
			                     "flusso-h264.264", instant_us, fo.width,
			                     fo.height, 0))
				p.streams++;
			/* ⚠ And the stage's size is NOT written here: `canvas_w`/`canvas_h` are
			 *   this function's PARAMETERS, not the loop's variables — writing
			 *   into them would seem to update the stage and would update
			 *   nothing.  The reconciliation at the loop's first round takes
			 *   care of it, which is the only place where that number changes. */
		} else {
			registro_dice(LOG_CHILD,
			              "⛔ the switch-on diagnosis does NOT encode: the "
			              "frame declares %ux%u with stride %u and carries %llu "
			              "bytes — whoever compressed it would read beyond the copy",
			              fo.width, fo.height, fo.stride,
			              (unsigned long long)fo.byte);
		}
		/* ⛔ And the loop's counters start again from zero: these two are not
		 *    frames of the movement, they are the switch-on diagnosis.  Adding
		 *    them would say "two frames delivered" to a user who has not seen
		 *    a single one. */
		cycle_frames = cycle_keys = 0;
	} else {
		/* ⚠ On a remount the diagnosis is not redone: it would cost ~80 ms of
		 *   encoding in the middle of a live session, and the two frames would
		 *   go to a client already watching.  ⛔ `p.streams` stays 0 and the log
		 *   says so: it is a remount, not a birth. */
		p.streams = 0;
	}

	capture_stopped_free(&fo);
	send_msg(MSG_STAGE, &p, sizeof p, NULL, 0);

	/* ⭐⭐ AND THE STAGE'S TWO SEAMS LIVE HERE, not in the caller: whoever
	 *     remounts the stage must remount **all** of them, and leaving one out
	 *     would mean a desktop that is seen and cannot be driven — without any
	 *     error anywhere.
	 *
	 * ⛔ `cursor_open()` wants the recipient **at opening**, and the opening
	 *    happens inside `capture_start()`: so the registration goes through
	 *    `capture.h`.  ⚠ Without this line the pipe would be written in full
	 *    and **empty**.
	 * ⛔ And `input_open()` goes on the `RemoteDesktop` session that `mutter.c`
	 *    has just started: on a remount that is **another session**, and an
	 *    `Input` hooked to the old one will no longer inject anything. */
	capture_cursor(cat, cursor_to_parent, NULL);
	if (stage_input) {
		input_close(stage_input);
		stage_input = NULL;
	}
	{
		char *err_input = NULL;
		/* ⭐ PHASE 12, INCREMENT 3 — on KDE the channel is given by KWin, at
		 *    the output's size (`canvas_w`/`canvas_h` have already been aligned by
		 *    `stage_size()`). */
		/* ⭐ PHASE 13, INCREMENT 3 — on XFCE (wlroots) `libei` does not exist:
		 *    Wayland virtual keyboard and pointer, with the same contract
		 *    (`input.h`).  ⛔ The branch comes FIRST and does not touch the
		 *    GNOME and KDE line below. */
		if (session_on_wlroots())
			stage_input = input_open_wlr(canvas_w, canvas_h, &err_input);
		else
		stage_input = stage_kwin
		                  ? input_open_kwin(stage_kwin, canvas_w, canvas_h, &err_input)
		                  : input_open(mut, canvas_w, canvas_h, &err_input);
		if (stage_input && pending_layout[0]) {
			/* ⛔ Before saying the channel is open: the layout requested at
			 *    attach had arrived with the stage closed, and if it is not
			 *    applied HERE the user types the first keys on the wrong
			 *    layout — and `Ctrl+Z` does "redo". */
			registro_dice(LOG_CHILD,
			              "⭐ §5-bis.7: applying now the layout «%s», "
			              "which had been requested when the stage was not there "
			              "yet",
			              pending_layout);
			input_layout(stage_input, pending_layout);
			pending_layout[0] = '\0';
		}
		if (stage_input) {
			registro_dice(LOG_CHILD,
			              "⭐⭐ THE INPUT CHANNEL IS OPEN on the canvas %ux%u: "
			              "from now on what the user does in the browser reaches "
			              "the desktop (§7.3)",
			              canvas_w, canvas_h);
			/* ⭐ PHASE 15, D-007 — on wlroots the output's size is given at
			 *    the capture's BIRTH (`capture_start_wlr()`): on reattach with
			 *    a smaller window the session's windows stayed where they
			 *    were.  ⇒ They are brought back inside now that the channel
			 *    exists.  (Harmless at the first birth, and it does nothing on
			 *    GNOME and KDE.) */
			input_bring_back_inside(stage_input);
		} else
			/* ⛔ And if it does not open we do NOT die: `CODER.md` §4.2 —
			 *    degrade, do not fail.  A user who sees the desktop and cannot
			 *    drive it has less than they are owed; a user whose session
			 *    falls **has nothing**.  ⚠ But the fallback is DECLARED. */
			registro_dice(LOG_CHILD,
			              "⛔ the input channel does NOT open (%s): the desktop "
			              "is SEEN but cannot be DRIVEN.  ⚠ The session stays "
			              "up — §8.3 forbids disconnecting — and this line is "
			              "the declared fallback",
			              err_input ? err_input : "no details");
		free(err_input);
	}

	/*
	 * ⭐⭐ AND THE STAGE'S THIRD SEAM: THE CLIPBOARD — phase 7.
	 *
	 * ⛔ It must be remounted **together with the other two**, and for the same
	 *    reason: on a remount the `RemoteDesktop` session is **another one**,
	 *    and an `Clipboard` hooked to the old one would no longer receive any
	 *    signal — without any error anywhere.  ⚠ The symptom would be "the
	 *    clipboard stopped working at some point", which does not name the
	 *    remount.
	 *
	 * ⛔ And it is CLOSED before reopening, the old one is not left standing:
	 *    `clipboard_close()` never calls `DisableClipboard` (trap 1 of
	 *    `clipboard.h`), so closing here does not burn the graphical session's
	 *    clipboard — it only closes our thread and the subscriptions.
	 */
	if (stage_clipboard) {
		clipboard_close(stage_clipboard);
		stage_clipboard = NULL;
	}
	{
		GError *err_app = NULL;

		/* ⭐ PHASE 13 — on XFCE the clipboard goes through labwc, with the same
		 *    wlroots protocol KDE already uses (`clipboard_kde.c`).  ⛔ The new
		 *    branch comes FIRST, and the two below are the ones from before.
		 * ⭐ PHASE 12 — on KDE the clipboard goes through KWin (`clipboard_kde.c`). */
		if (session_on_wlroots())
			stage_clipboard = clipboard_open_wlroots(&err_app);
		else
			stage_clipboard = stage_kwin
			                    ? clipboard_open_kde(&err_app)
			                    : clipboard_open(mutter_bus(mut),
			                                   mutter_control_path(mut),
			                                   &err_app);
		if (stage_clipboard) {
			clipboard_listen(stage_clipboard, clipboard_from_session,
			                clipboard_wants_paste, NULL);
			registro_dice(LOG_CHILD,
			              "⭐⭐ THE CLIPBOARD IS OPEN, in both directions and text "
			              "only: from now on what is copied in the desktop can "
			              "be pasted on the device, and vice versa (§7.4)");
			/* ⭐ AND FIRST OF ALL: the clipboard already in the desktop is
			 *    ASKED FOR, or connecting loses it (see the box in
			 *    `clipboard.c`).  ⛔ And it is asked BEFORE the pending offer:
			 *    offering first, our text would be read instead of its own. */
			clipboard_read_now(stage_clipboard);

			/* ⭐ And the offer that arrived while we were not there is redone NOW. */
			if (clipboard_pending_offer) {
				GError *sb = NULL;

				clipboard_pending_offer = false;
				if (clipboard_offer(stage_clipboard, &sb))
					registro_dice(LOG_CLIPBOARD,
					              "⭐ CLIPBOARD: the client had announced BEFORE "
					              "the clipboard opened, and the offer has been "
					              "REDONE now: inside the desktop the "
					              "«Paste» item has something to give again");
				else
					registro_dice(LOG_CLIPBOARD,
					              "⛔ CLIPBOARD: the pending offer did not "
					              "succeed (%s): inside the desktop it will not be "
					              "possible to paste what the client has "
					              "copied",
					              sb ? sb->message : "no details");
				g_clear_error(&sb);
			}
		} else {
			/* ⛔ And if it does not open we do NOT die: `CODER.md` §4.2 —
			 *    degrade, do not fail.  A user without a clipboard has less than
			 *    they are owed; a user whose session falls has nothing.
			 *    ⚠ But the fallback is DECLARED, or "the clipboard does not
			 *    work" and "the clipboard never started" have the same face. */
			registro_dice(LOG_CHILD,
			              "⛔ the clipboard does NOT open (%s): the desktop is seen "
			              "and driven, but copy-paste between the two worlds is "
			              "not there.  ⚠ The session stays up, and this line is "
			              "the declared fallback",
			              err_app ? err_app->message : "no details");
		}
		g_clear_error(&err_app);
	}

	/*
	 * ⭐⭐ AND HERE, ONLY ONCE PER SESSION, THE THREE THINGS TO DO WHEN THE
	 *     STAGE IS THERE — and not before, because before there was no
	 *     session to tell them to.
	 *
	 * ⛔ "Written" is not "in force" (`REVIEWER.md` E1): the two checks do not
	 *    needs to protect — the polkit rule and the seatless session protect —
	 *    they needs to **know whether those protections are really there**.
	 *    And the child does them because it is the user: `[M]` root gets the
	 *    answer "yes" from logind, which looks at `CAP_SYS_BOOT` before polkit.
	 */
	{
		static bool already_done;

		if (!already_done) {
			sentinel *guard;
			char detail[192];

			already_done = true;

			/* 1. ⛔ Suspension, and it is not theoretical: `[M]` the
			 *    "Automatic Suspend" notification appeared in the remote
			 *    desktop. */
			session_inhibit();

			guard = sentinel_open();
			if (!guard) {
				registro_dice(LOG_CHILD,
				              "⚠ without the system bus I cannot VERIFY "
				              "either headless or the ban on powering off: "
				              "the protections may be there, ⛔ but from here "
				              "I don't know — and «I don't know» is not «fine»");
			} else {
				/* 2. Headless, which since 15 August is by construction. */
				detail[0] = '\0';
				if (sentinel_without_seat(guard, detail, sizeof detail))
					registro_dice(LOG_CHILD,
					              "⭐ VERIFIED: my session has no "
					              "seat (%s) ⇒ Mutter is headless, and "
					              "GNOME's screen lock does not revoke "
					              "capture and input from us (§4.3-bis)",
					              detail);
				else
					registro_dice(LOG_CHILD,
					              "⛔⛔ MY SESSION IS NOT HEADLESS "
					              "(%s): this session works as long as "
					              "nobody locks the screen, and then Mutter "
					              "CLOSES capture and input on us, refusing to "
					              "recreate them.  ⚠ I do not exit — I1: a "
					              "session with a risk is worth more than "
					              "no session — but this line is the "
					              "declared failure of §4.3-bis",
					              detail[0] ? detail : "no details");

				/* 3. The three belts of §4.7. */
				detail[0] = '\0';
				if (sentinel_shutdown_forbidden(guard, detail,
				                                   sizeof detail))
					registro_dice(LOG_CHILD,
					              "⭐ VERIFIED: from this session the machine "
					              "can NOT be powered off or suspended (%s) "
					              "— §4.7, and the three belts are in force",
					              detail);
				else
					registro_dice(LOG_CHILD,
					              "⛔⛔ FROM THIS SESSION THE MACHINE CAN BE "
					              "POWERED OFF OR SUSPENDED (%s): §4.7 says "
					              "nobody must be able to do it, and the "
					              "machine belongs to several people.  ⇒ The "
					              "polkit rule is missing, or it does not cover all "
					              "twelve actions",
					              detail[0] ? detail : "no details");
				sentinel_close(guard);
			}
		}
	}

	return true;
}

/* ⛔⭐ AND THE STAGE IS REALLY DISMANTLED, all three pieces and in this order.
 *
 *     First the input (which talks to the `RemoteDesktop` session of `mut`),
 *     then the capture (which has its own thread and callbacks running over
 *     there), then `mut`.  ⚠ The other way round the session would be
 *     destroyed while someone is using it.
 *
 * ⛔ And first of all whatever was left held down is RELEASED (`RCP.md` §11):
 *    the stage that goes away does not take a pressed Ctrl with it, and at the
 *    remount the user would find an unusable desktop without connecting the
 *    two things.
 */
static void unmount_stage(MutterSession **m, Capture **c)
{
	if (stage_input) {
		int amount = input_release_all(stage_input);
		if (amount > 0)
			registro_dice(LOG_CHILD,
			              "⭐ §7.3: the stage is dismantled and %d keys and "
			              "buttons were still held down: released",
			              amount);
		input_close(stage_input);
		stage_input = NULL;
	}
	/* ⛔⭐ AND THE CLIPBOARD IS CLOSED BEFORE THE SESSION, not after: the two
	 *     subscriptions and the thread live on `mutter_bus()`, which belongs
	 *     to the `MutterSession` closed three lines below.  ⚠ Closing the
	 *     other way round would leave a thread talking on a bus already gone.
	 * ⛔ And `DisableClipboard` is NOT called (trap 1 of `clipboard.h`): whoever
	 *    called it at dismantling would find, at the remount, a dead clipboard
	 *    **for the rest of the graphical session**. */
	if (stage_clipboard) {
		clipboard_close(stage_clipboard);
		stage_clipboard = NULL;
		clipboard_assembly_free();
	}
	if (*c) {
		capture_stop(*c);
		*c = NULL;
	}
	if (*m) {
		mutter_close(*m);
		*m = NULL;
	}
	close_stage_kwin();
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ AND THE PIXELS' ROUTE IS CHANGED **WITHOUT DISMANTLING THE STAGE** — 25
 *       Aug 2026, and it is the cure of `phases/10-…md` §8.2 **P1**.
 *
 * ⛔⛔ THE FACT, `[M]` 25 Aug 2026 (core read with gdb, not inferred):
 *
 *   with a view **1268** wide — the one Firefox opens by itself — the DMA-BUF
 *   stride comes out **5072**, which is not a multiple of 64; the zero-copy
 *   guard refuses it (`encode_and_send`), `card_to_abandon` was set,
 *   and the loop **dismantled the whole stage** to remount it on memory.
 *   ⇒ `unmount_stage()` → `input_close()` → **`ei_disconnect()`**, and there
 *   the child died of **SIGSEGV**:
 *
 *       #0  ei_disconnect ()   from /lib/x86_64-linux-gnu/libei.so.1
 *       #2  input_close (in=…) at input.c:1613
 *       #3  unmount_stage () at child.c
 *
 *   `[M]` And the piece that explains the **when**: in the core `in->pointer`
 *   and `in->keyboard_dev` were **NULL** and `region_known` **false** — the
 *   EIS channel had been opened **33 ms earlier** and the handshake had not
 *   arrived yet.  ⇒ Closing a freshly born libei channel makes it crash inside
 *   the library.  ⭐ The reverse proof is measured: with the **same** fallback
 *   on a 1268 canvas requested with a **mature** stage (20 s), the child
 *   survives and memory mounts — 25 Aug 2026.
 *
 * ⇒ ⭐⭐ THE CURE IS THE RIGHT ROAD, not a sticking plaster: **the pixels' route
 *      is a property of the STREAM, not of the graphical session.**  The input
 *      channel, the clipboard and the `RemoteDesktop` session have nothing to
 *      do with the pixels being in a DMA-BUF or in a memfd: dismantling them
 *      was throwing away three healthy things to change one.
 *
 * ⭐ And more is gained than the defect being cured:
 *     · the input channel **is not recreated** ⇒ no turnover of libei
 *       devices, that is none of the defect §7.1 has been fighting for days;
 *     · the clipboard stays alive;
 *     · `CreateSession` on `RemoteDesktop`, which costs ~1 s, is not redone;
 *     · the parent receives no "the stage has gone", so **no farewell** and no
 *       black page.
 *
 * ⛔ What is remounted is what MUST be remounted: the `Capture` and its cursor
 *    seam (`cursor_open()` wants the recipient at opening, and the opening is
 *    inside `capture_start()` — see the box of the three seams in
 *    `take_stage()`).
 *
 * ⚠ And if the PipeWire node cannot be taken back (the producer withdrew it),
 *   `false` is returned **without inventing anything**: the caller dismantles
 *   the stage for real, which is the old road — demoted from normal to
 *   fallback.
 * ═══════════════════════════════════════════════════════════════════════════ */
static bool remount_only_capture(MutterSession *m, Capture **c, uint32_t l,
                                    uint32_t a)
{
	GError *mistake = NULL;
	Capture *new_one;

	/*
	 * ⭐ PHASE 13 — XFCE (wlroots): here the source IS the capture.  There is
	 *    no PipeWire node nor a Mutter/KWin session to take back: remounting
	 *    means stopping the `Capture` and reopening it with
	 *    `capture_start_wlr()` on the new route.  ⛔ Input (`input_open_wlr`)
	 *    and clipboard stay alive: they belong to the stage, not to the stream.
	 * ⛔ The branch comes FIRST and always returns: below, the GNOME and KDE
	 *    path stays the one from before, word for word.  Without this branch
	 *    `m` and `stage_kwin` are NULL on XFCE, the guard below returned
	 *    `false` and the caller dismantled the WHOLE stage (input and clipboard
	 *    included).
	 */
	if (session_on_wlroots()) {
		if (!c)
			return false;
		if (*c) {
			capture_stop(*c);
			*c = NULL;
		}
		stage_size(&l, &a);
		slabs_per_route();
		new_one = capture_start_wlr(l, a, MOTION_FPS, stage_route,
		                          CAPTURE_COLOR_BGRX, &mistake);
		if (!new_one) {
			registro_dice(LOG_CHILD,
			              "⛔ wlroots: the capture did NOT reopen on the route "
			              "«%s» (%s): dismantling the whole stage, which is the "
			              "fallback",
			              stage_route == CAPTURE_ROUTE_CARD ? "CARD"
			                                                        : "MEMORY",
			              mistake ? mistake->message : "no details");
			g_clear_error(&mistake);
			return false;
		}
		g_clear_error(&mistake);
		*c = new_one;
		/* ⚠ The same seam as `take_stage()`: on wlroots the registration
		 *   is accepted and never calls back (the pointer is in the pixels),
		 *   but it is done anyway — a remounted stage must be the same as a
		 *   mounted one. */
		capture_cursor(*c, cursor_to_parent, NULL);
		registro_dice(LOG_CHILD,
		              "⭐⭐ wlroots: the PIXELS' ROUTE changed to «%s» "
		              "remounting ONLY the capture (canvas %ux%u): input and clipboard "
		              "were NOT touched",
		              stage_route == CAPTURE_ROUTE_CARD
		                  ? "CARD (DMA-BUF, zero copy)"
		                  : "MEMORY (the pixels are copied)",
		              l, a);
		return true;
	}

	if ((!m && !stage_kwin) || !c)
		return false;

	/* ⛔ First the old one is stopped: two streams on the same node would mean
	 *    two consumers, and the producer would deliver to both — that is
	 *    double the GPU work for nothing. */
	if (*c) {
		capture_stop(*c);
		*c = NULL;
	}

	stage_size(&l, &a);
	new_one = capture_start(stage_node(m), l, a, MOTION_FPS, stage_route,
	                      CAPTURE_COLOR_BGRX, NULL, NULL, NULL, &mistake);
	if (new_one && stage_kwin) {
		capture_cursor_never_hide(new_one, "KWin --virtual: the session's cursor "
		                                      "theme is invisible");
		capture_skip_unchanged(new_one, "KWin: whole frames and exact damage");
	}
	if (!new_one) {
		registro_dice(LOG_CHILD,
		              "⛔ the capture did NOT reopen on node %u on the route "
		              "«%s» (%s): dismantling the whole stage, which is the fallback "
		              "— ⚠ and it costs the graphical session, not only the stream",
		              stage_node(m),
		              stage_route == CAPTURE_ROUTE_CARD ? "CARD"
		                                                        : "MEMORY",
		              mistake ? mistake->message : "no details");
		g_clear_error(&mistake);
		return false;
	}
	g_clear_error(&mistake);
	*c = new_one;
	/* ⛔ The cursor seam is redone AT ONCE: the pipe towards the parent is
	 *    registered on the `Capture`, and the previous one is gone.  ⚠ Without
	 *    this line the pointer would stop changing shape **without any
	 *    error**, and the symptom would appear hours later. */
	capture_cursor(*c, cursor_to_parent, NULL);
	registro_dice(LOG_CHILD,
	              "⭐⭐ the PIXELS' ROUTE changed to «%s» remounting ONLY "
	              "the stream (node %u, canvas %ux%u): the graphical session, the "
	              "input channel and the clipboard were NOT touched.  ⛔ And "
	              "this is the cure of P1: dismantling the stage to change "
	              "route closed a freshly born EIS channel, and `ei_disconnect()` "
	              "killed the child with a SIGSEGV before the first frame",
	              stage_route == CAPTURE_ROUTE_CARD
	                  ? "CARD (DMA-BUF, zero copy)"
	                  : "MEMORY (the pixels are copied)",
	              stage_node(m), l, a);
	return true;
}

/* ⛔ The child's entry point.  `main.c` gets here BEFORE anything else, and
 *    it never returns. */
/* ⭐ 1.5 (§11.50): whose stamp the parent's messages must carry.  0 = root, the
 *    single-process server's parent; the root side writes `--parent-uid N` for
 *    the network side's `remotix`.  Nobody passes it today. */
static uid_t parent_uid = 0;
/* ⛔⭐ 1.5 (§11.50, review of the split, finding 1) — `--close-only`, written
 *     by the ROOT SIDE for CLOSE_ORPHAN, the one birth without a password.
 *     A hijacked network side could ask it for any user with an abandoned
 *     desktop; a full child there would be video and input on that desktop
 *     without the password.  ⇒ This child takes NO stage (no capture, no
 *     frame, no `libei`, no clipboard), discards every message but «end the
 *     session» (and `MSG_SHUT_DOWN`, `MSG_CHI_SEI`), exits after the attempt
 *     whatever its outcome, and by itself after `CLOSE_ONLY_LIFE_MS`.  ⚠ The
 *     most the network side gets is what CLOSE_ORPHAN is for: that abandoned
 *     desktop closed.  Nobody passes it today (phase D5, inert). */
static bool close_only = false;
static uint64_t close_only_since_ms;
#define CLOSE_ONLY_LIFE_MS 30000

void child_alive(int argc, char **argv)
{
	struct body_whoami s;
	struct stat st;
	uint32_t canvas_w, canvas_h;
	const char *user, *dir_survey;
	uid_t expected;
	gid_t expected_g;
	MutterSession *mut = NULL;
	Capture *cat = NULL;
	int uno = 1;
	uid_t r, e, sv;
	gid_t rg, eg, sg;
	/* ⭐ PHASE 9 — what the parent wrote on the command line, and that this
	 *    process must repeat to itself: see below. */
	bool f9_rises = false;
	uint32_t f9_cap = 0;
	/* ⛔ `true`, and not `false` like the two above: this cure is born ON
	 *    (24 Aug 2026), so the absence of the word at the end means "on".
	 *    ⚠ And the child can NOT just ask `audio.c` for the default: it must
	 *    be able to declare what REACHED it, or "the option was lost in the
	 *    hand-over" and "the cure does not work" have the same face (form D5). */
	bool f9_audio_silence = true;

	/* `--internal-child <user> <uid> <gid> <w> <h> <serial> <survey>` */
	if (argc < 9)
		_exit(40);
	in_session_child = true;
	user = argv[2];
	/* ⛔⭐ AND FROM HERE ON EVERY LINE OF THIS PROCESS SAYS WHOSE IT IS — 25
	 *     Aug 2026, R10-A4 / P6.  The box is in `log.h`.
	 *
	 *     ⭐ This process serves **a single** session: the identity belongs to
	 *        the process, not to the line, and it is set in one place only.
	 *        ⇒ It cures in one go the families `[M]` §6.7 measured at
	 *        **0.0 %** — `ciclo-cattura` and `audio-blocchi` (359 lines in
	 *        90 s with four sessions) — and with them the **70** of
	 *        `encoder.c`, which knows nothing about sessions and writes
	 *        in the `"video"` area, ⛔ the SAME string as the parent's
	 *        `REG_VIDEO`: without this line those two families could not be
	 *        told apart **even by area**.
	 *
	 * ⚠ BEFORE anything else that may write, and in particular before the uid
	 *   recheck further down: the line "⛔⛔ I AM NOT WHO I SHOULD BE" is
	 *   precisely one of those read when there are ten users, and it would
	 *   come out without a name.
	 * ⚠ And the identity does NOT cross the `exec`: the parent's stayed in the
	 *   previous image, and this is a new image. */
	log_identity(user);
	expected = (uid_t)strtoul(argv[3], NULL, 10);
	expected_g = (gid_t)strtoul(argv[4], NULL, 10);
	canvas_w = (uint32_t)strtoul(argv[5], NULL, 10);
	canvas_h = (uint32_t)strtoul(argv[6], NULL, 10);
	/* ⛔ The WANTED canvas is born equal to the starting one and diverges at
	 *    the first `FIT_CANVAS`: it is the one requested on REMOUNTING the
	 *    stage.  ⚠ Without it, a stage falling after a resize was born again
	 *    at the command line's size, and the bands came back without any line
	 *    connecting the two things. */
	canvas_intended_w = canvas_w;
	canvas_intended_h = canvas_h;
	my_serial = strtoull(argv[7], NULL, 10);
	dir_survey = argv[8];
	/* ⭐ The snapshot keeps it: see the box above `shot_dir`. */
	shot_dir = dir_survey;
	/* ⭐ The chatter, if the parent passed it to us: see the box in
	 *    `figli_esegui()`.  ⛔ Without it, every `log_detail` of this
	 *    file is written and reaches nobody. */
	/* ⛔⭐⭐ AND THE **THREE** CURES OF PHASE 9 ARE TURNED ON HERE, INSIDE THE CHILD.
	 *
	 *      The box explaining why they cannot come from anywhere else is in
	 *      `child.h`, above `children_phase9()`: they are statics of the process,
	 *      and the process that opens the encoders is this one.
	 *
	 * ⚠ BEFORE `take_stage()`, which already opens the first encoder: two
	 *   lines further down and the first session would be born without the
	 *   cure, with the startup line saying "off" — that is the defect disguised
	 *   as a measure that this whole phase tries to avoid.
	 * ⚠ They are scanned by NAME and not by position, like the chatter: the
	 *   first nine are fixed, these are optional and may both be missing.
	 */
	for (int i = 9; i < argc; i++) {
		if (strcmp(argv[i], "--verbose") == 0)
			log_chatter(true);
		else if (strcmp(argv[i], "--journal") == 0)
			log_journal(true); /* ⚠ if it does not open, stderr remains */
		else if (strcmp(argv[i], "--quality-recovery") == 0)
			f9_rises = true;
		else if (strcmp(argv[i], "--bandwidth-cap-mbit") == 0 && i + 1 < argc)
			f9_cap = (uint32_t)strtoul(argv[++i], NULL, 10);
		/* ⭐ PHASE 19: the forced card route (the server's `--encoding-route`), for
		 *    the same reason as the three lines above — it is a static of THIS
		 *    process, and the parent repeats it to it.  ⚠ A value that is not
		 *    recognised stays "card", and the encoder's line says so. */
		else if (strcmp(argv[i], "--encoding-route") == 0 && i + 1 < argc)
			child_encoding_route(argv[++i]);
		/* ⭐ 1.5: the server's `--render-node`, repeated (the fallback when
		 *    the compositor does not name its card). */
		else if (strcmp(argv[i], "--render-node") == 0 && i + 1 < argc)
			child_render_node(argv[++i]);
		/* ⛔⭐ AND THIS ONE IS READ NEGATED, because it is born ON (24 Aug 2026):
		 *     the word at the end is the EXCEPTION to the default.  ⚠ An absence
		 *     here means "on", which is the opposite of the two lines above —
		 *     and it is the reason `f9_audio_silence` starts from `true`. */
		else if (strcmp(argv[i], "--no-audio-silence") == 0)
			f9_audio_silence = false;
		/* ⭐ 1.5 (§11.50): the network side's uid, written by the root side. */
		else if (strcmp(argv[i], "--parent-uid") == 0 && i + 1 < argc) {
			/* ⛔ review 4 B, finding 3: digits only and a uid that fits — a
			 *    bare strtoul made garbage or an empty value uid 0, the
			 *    single-process server's parent, without a line.  0 written
			 *    as «0» stays legal (the bench's fake parent is root). */
			const char *v = argv[++i];
			char *end = NULL;
			unsigned long pu;

			errno = 0;
			pu = strtoul(v, &end, 10);
			if (!v[0] || v[0] < '0' || v[0] > '9' || *end || errno
			    || pu != (unsigned long)(uid_t)pu || (uid_t)pu == (uid_t)-1) {
				fprintf(stderr, "child: ⛔ --parent-uid «%s» is not a uid: this child "
				        "does not start\n", v);
				_exit(40);
			}
			parent_uid = (uid_t)pu;
		}
		else if (strcmp(argv[i], "--close-only") == 0)
			close_only = true;
	}
	encoder_quality_rises(f9_rises);
	codificatore_tetto_banda(f9_cap);
	/* ⛔ And the audio encoder lives in THIS process, like the video one: the
	 *    line of the value IN FORCE is written by `audio.c` when each encoder
	 *    opens, and it is the third of the triple (parent WILL PASS · child
	 *    RECEIVED · in force). */
	audio_silence_hush(f9_audio_silence);

	signal(SIGTERM, SIG_DFL);
	signal(SIGINT, SIG_DFL);
	signal(SIGPIPE, SIG_IGN);
	/* ⭐ The on-demand snapshot: the box is above `shot_signal()`. */
	signal(SIGUSR1, shot_signal);
	signal(SIGUSR2, shot_signal);

	/* ⛔ If the server dies, this process dies with it: no orphan attached to a
	 *    user's virtual monitor.  ⚠ And it is armed AFTER the privilege drop,
	 *    because a credentials change can reset it — ⭐ and for this reason it
	 *    is NOT the only road: the EOF on the socket (the loop below) closes
	 *    anyway, and two independent nets are two on purpose. */
	prctl(PR_SET_PDEATHSIG, SIGTERM);

	/* ⛔⭐ AND IT IS RECHECKED THAT WE ARE WHO WE MUST BE, AFTER THE `exec`.
	 *     `become_and_exec()` has already verified it, but that was another
	 *     program: what counts here is what the KERNEL now says about this
	 *     process.  A new image trusting its own `argv` would be a child
	 *     declaring itself. */
	if (getresuid(&r, &e, &sv) != 0 || getresgid(&rg, &eg, &sg) != 0)
		_exit(41);
	if (r != expected || e != expected || sv != expected || rg != expected_g
	    || eg != expected_g || sg != expected_g) {
		registro_dice(LOG_CHILD,
		              "⛔⛔ I AM NOT WHO I SHOULD BE: they wanted me as uid %ld gid "
		              "%ld and the kernel says uid %ld/%ld/%ld gid %ld/%ld/%ld.  "
		              "EXITING without touching anything: a child running as "
		              "the wrong user is I3 violated invisibly",
		              (long)expected, (long)expected_g, (long)r, (long)e, (long)sv,
		              (long)rg, (long)eg, (long)sg);
		_exit(42);
	}
	my_uid = e;

	/* ⛔ The child too wants the kernel's stamp on the parent's messages: the
	 *    link is verified **at both ends**.  ⚠ `SO_PEERCRED` here would tell
	 *    the truth (root created the socketpair), but it must be the same
	 *    proof the parent makes — and the parent's is per message. */
	setsockopt(fd_child, SOL_SOCKET, SO_PASSCRED, &uno, sizeof uno);

	memset(&s, 0, sizeof s);
	s.uid = r;
	s.euid = e;
	s.suid = sv;
	s.gid = rg;
	s.egid = eg;
	s.sgid = sg;
	s.pid = (uint32_t)getpid();
	s.ppid = (uint32_t)getppid();
	s.descriptors = how_many_descriptors();
	snprintf(s.user, sizeof s.user, "%s", user);
	snprintf(s.runtime, sizeof s.runtime, "%s",
	         getenv("XDG_RUNTIME_DIR") ? getenv("XDG_RUNTIME_DIR") : "(none)");
	/* ⛔ "It exists" and "it is its own" are two different facts: someone
	 *    else's runtime folder would be a permission denied much later. */
	if (s.runtime[0] != '(' && stat(s.runtime, &st) == 0 && st.st_uid == e)
		s.runtime_c_e = 1;
	{
		char fpath[224];
		snprintf(fpath, sizeof fpath, "%s/bus", s.runtime);
		if (s.runtime_c_e && stat(fpath, &st) == 0)
			s.socket_bus_c_e = 1;
	}

	registro_dice(LOG_CHILD,
	              "⭐ I am the child of «%s»: pid %u, uid %u (asked of the kernel, "
	              "not inferred), %u open descriptors — the server's port is NOT "
	              "among them",
	              user, s.pid, s.euid, s.descriptors);

	/* ⭐ PHASE 15, D-015 — the SESSION's dconf, here and not later: before any
	 *    `GSettings` (`session_settings()`, `input_layout()`) and
	 *    before the threads — `g_setenv` must not be done with other threads
	 *    alive.  GNOME only; the box is in `session.c`. */
	/* ⛔ NOT for the close-only child (review 4, finding 2): it is born
	 *    without a password for a LIVE desktop found again, and only «end the
	 *    session» may come out of it — preparing the session's dconf and
	 *    clearing the user manager's environment are a desktop's birth, and
	 *    would touch the very session it exists to close. */
	if (!close_only) {
		session_dconf_prepare();
		/* ⭐ R1/R2 — and what a badly ended session left in the user manager
		 *    goes away now (only with the session dead: see the box). */
		session_clear_out_handler("child startup: leftovers from before");
	}

	/* ⛔⭐⭐ THE PHASE 9 PARAMETERS ARE WRITTEN AT BIRTH — 23 Aug 2026.
	 *
	 *      The rule is already written, and it is in `src/restart-7700.sh`:
	 *      *"the server writes the value IN FORCE at startup, so one does not
	 *      test a ceiling believing one is testing another"*.  ⛔ It held for
	 *      the three clocks of §5.3 and NOT for what governs image and rate —
	 *      that is precisely the two quantities phase 9 goes on to tune.
	 *
	 * ⛔ AND TUNING WITHOUT THESE LINES IS NOT A MEASURE.  "I tested QP 26" is
	 *    a sentence that holds only if someone wrote that it was 26: a number
	 *    changed in a `#define` and forgotten produces a whole bench of real
	 *    numbers attributed to the wrong value — and nobody notices, because
	 *    the frames come out all the same.
	 *
	 * ⚠ AND HERE WHAT THE CHILD **ASKS FOR** IS WRITTEN, not what the encoder
	 *   **does**: they are two different things and live in two files.  The QP
	 *   really accepted, the ceilings and the entrypoint's confirmation are
	 *   written by `encoder.c` when it opens — "written" is not "in force"
	 *   (`REVIEWER.md` E1), and these lines are the "asked" half of the
	 *   comparison, not the verdict.
	 *
	 * ⚠ The canvas is the one at BIRTH: §4.5 can change it with the session
	 *   open, and the new value is written by the «encoder OPENED» line.
	 * ⚠ The depth is NOT there on purpose: at birth it is not negotiated, and
	 *   writing one here would be putting back by hand the lie of 17 August. */
	registro_dice(LOG_CHILD,
	              "⭐⛔ PARAMETERS IN FORCE (phase 9), what the child ASKS FOR: "
	              "rate %d/s · canvas at birth %ux%u · INFINITE GOP "
	              "(chiavi_ogni = 0: keyframes only on request, §5.2 — it is a "
	              "choice, not an oversight)",
	              MOTION_FPS, canvas_w, canvas_h);
	registro_dice(LOG_CHILD,
	              "⭐⛔ PARAMETERS IN FORCE (phase 9), quality and encoder "
	              "REQUESTED: QP %d on the card (no software fallback, phase "
	              "19) · node %s · entrypoint %s",
	              QP_HARDWARE, RENDER_NODE,
	              power_name(RENDER_POWER));

	/* ⛔⭐⭐ AND THIS IS THE LINE THAT TAKES DOWN FORM D5 — "a stale binary
	 *      stays green".
	 *
	 * ⛔ An option accepted by the parent and lost in the parent → child
	 *    hand-over has EXACTLY the same face as a cure that does not work: the
	 *    bench measures, sees no difference, and the red lands on the wrong
	 *    suspect.  ⇒ The one declaring it received it is the child, which read
	 *    it from its own `argv` — not the parent, which only wrote it.
	 *
	 * ⚠ It is the "received" half of three lines read in a row:
	 *      1. `children_phase9()` in the parent — "what I WILL PASS";
	 *      2. this one — "what REACHED me";
	 *      3. `encoder.c` at opening — "what is IN FORCE".
	 *    If the three do not agree, the point where it gets lost is between the
	 *    two that diverge, and there is nothing to guess. */
	registro_dice(LOG_CHILD,
	              "⭐⛔ PARAMETERS IN FORCE (phase 9), what the child "
	              "RECEIVED on its command line: quality climb-back "
	              "%s · bandwidth ceiling %s (floor %u Mbit/s) · ⭐ audio "
	              "silence %s — ⚠ asked of the "
	              "encoder now, before the first stage.  Whether it took them "
	              "is told by the «encoder OPENED» line (video) and the "
	              "«digital silence cure» line (audio)",
	              f9_rises ? "ON" : "off (I6)",
	              f9_cap ? "ON" : "off (I6)", f9_cap,
	              f9_audio_silence
	                  ? "ON (default since 24 Aug 2026)"
	                  : "turned OFF by hand (--no-audio-silence)");

	if (!send_msg(MSG_INTRO, &s, sizeof s, NULL, 0)) {
		registro_dice(LOG_CHILD, "⛔ I cannot introduce myself to the parent (%s)",
		              strerror(errno));
		_exit(43);
	}

	/* ⛔⭐ AND THE STAGE IS TAKEN AT ONCE, without waiting for someone to ask.
	 *
	 *     The reason is a number: §4.4-bis imposes on the server a fixed second
	 *     before answering `CREDENTIALS`, and the RCP session cannot reach
	 *     `SESSION` before that.  ⇒ Between "PAM said yes" and "a frame is
	 *     needed" there is **at least one second guaranteed by the protocol**,
	 *     and it is all the time this child has to be born, connect to the
	 *     bus, capture and encode.  Waiting for a request would throw it away. */
	if (close_only) {
		/* ⛔ No stage, ever: the retry is put where it never comes. */
		registro_dice(LOG_CHILD,
		              "⭐ CLOSE-ONLY child of «%s» (born for a desktop found again, "
		              "without a password — DECISIONS.md §11.50): no stage, no frame, "
		              "no input; only «end the session» is obeyed, and I exit within "
		              "%d s",
		              user, CLOSE_ONLY_LIFE_MS / 1000);
		stage_retry_ms = UINT64_MAX;
		close_only_since_ms = log_now_ms();
	} else if (!take_stage(canvas_w, canvas_h, dir_survey, true, &mut, &cat)) {
		/* ⛔⭐ AND IF AT BIRTH THE STAGE IS NOT THERE, WE DO NOT STAY LIKE THIS —
		 *     it is the second twin defect, `[M]` from the user's real
		 *     session: a child born without a graphical session **never**
		 *     tried another, and at the next login invariant I2 handed them
		 *     that very child.  The user saw "no desktop" twice in a row for
		 *     this reason. */
		registro_dice(LOG_CHILD,
		              "⛔ NO STAGE at birth: the graphical session of "
		              "«%s» is not there (yet).  ⚠ I do NOT exit — §8.3 forbids "
		              "disconnecting — and I do NOT stand still: retrying, the first time "
		              "in %d ms",
		              user, STAGE_RETRY_MIN_MS);
		stage_retry_ms = log_now_ms() + STAGE_RETRY_MIN_MS;
		stage_wait_ms = STAGE_RETRY_MIN_MS;
	}

	/* ═══════════════════════════════════════════════════════════════════ */
	/* ⭐⭐ THE LOOP OF PHASE 3 — capture, encode, send; and listen.        */
	/*                                                                     */
	/* ⛔ TWO THINGS TO DO AND ONLY ONE PROCESS, and the order matters.  The */
	/*    loop looks FIRST at whether the parent said something (which     */
	/*    does not wait: `poll` with zero) and THEN captures (which         */
	/*    waits).  The other way round, a `MSG_SHUT_DOWN` or a requested     */
	/*    keyframe would sit still for the whole capture wait — that is up  */
	/*    to a quarter of a second, which on the latency of                 */
	/*    `SPECS.md` §3.2 is five times the ceiling.                   */
	/*                                                                     */
	/* ⛔ AND WHEN NOBODY IS WATCHING NOTHING IS CAPTURED: `requested_codec`  */
	/*    at zero means the last session has gone.  ⚠ It is NOT invariant   */
	/*    I1 the other way round — I1 forbids lowering the rate out of      */
	/*    caution **while someone is watching**; here nobody is watching,   */
	/*    and the stage (I4) stays up: only the loop stops.  Then we wait   */
	/*    on the socket, and the process costs zero.                        */
	for (;;) {
		uint8_t envelope[MAX_ENVELOPE];
		struct head t;
		struct ucred chi;
		bool c_e = false;
		ssize_t readings;
		struct pollfd pf;
		int ready;
		bool fine = false;

		/*
		 * ⛔⭐⭐ THE LOOP'S HEARTBEAT, and it is needed because without it I spent
		 *       a day reading the source instead of the facts.
		 *
		 * `[M]` 16 Aug 2026: in the slow rounds EIGHTEEN SECONDS passed between
		 * two lines that in the code are a few instructions apart, and in
		 * between the child wrote nothing.  From outside the possible cases
		 * were three — stuck in a call, waiting, or the loop not turning —
		 * ⛔ and the first two I had already instrumented and they were silent.
		 * ⇒ The third remains, and to see it a line written **anyway** is
		 * needed.
		 *
		 * ⚠ One per second, and only while there is no stage: when the desktop
		 *   runs, this line never appears.
		 */
		/* ⛔ The close-only child's own end (box at `close_only`). */
		if (close_only && log_now_ms() >= close_only_since_ms + CLOSE_ONLY_LIFE_MS) {
			registro_dice(LOG_CHILD,
			              "⭐ CLOSE-ONLY child: no «end the session» within %d s — "
			              "exiting, the desktop untouched",
			              CLOSE_ONLY_LIFE_MS / 1000);
			break;
		}
		if (!cat && !close_only) {
			static uint64_t heartbeat_ms;
			uint64_t t_now = log_now_ms();

			if (t_now - heartbeat_ms >= 1000) {
				heartbeat_ms = t_now;
				registro_dice(LOG_CHILD,
				              "♥ loop ALIVE without a stage: codec %u, wanted canvas "
				              "%ux%u, next attempt in %lld ms",
				              (unsigned)requested_codec, canvas_intended_w, canvas_intended_h,
				              (long long)((int64_t)stage_retry_ms - (int64_t)t_now));
			}
		}

		/* ── 1. what the parent has to say, without waiting ────────────── */
		for (;;) {
			struct pollfd due[2];
			int amount = 1;
			int fd_ei;

			pf.fd = fd_child;
			pf.events = POLLIN;
			pf.revents = 0;
			due[0] = pf;
			/* ⭐⭐ AND THE `libei` DESCRIPTOR IS IN THE SAME `poll`, not in a
			 *     poll at intervals.  ⛔ It is not a convenience: polling every
			 *     N milliseconds GIVES AWAY up to N milliseconds of the user's
			 *     time **on every gesture**, and the ceiling of `CODER.md`
			 *     §1-bis is 50 ms in all.  ⚠ When nothing is captured this
			 *     `poll` waits a whole second: without this line, a click on a
			 *     still desktop would arrive **up to a second later**. */
			fd_ei = stage_input ? input_descriptor(stage_input) : -1;
			if (fd_ei >= 0) {
				due[1].fd = fd_ei;
				due[1].events = POLLIN;
				due[1].revents = 0;
				amount = 2;
			}
			/* ⛔ Zero when capturing, the ceiling when not capturing: so the
			 *    idle process does not spin and the working one does not
			 *    lose time.
			 * ⛔⭐ And "capturing" requires TWO things: that someone is
			 *     watching **and** that the stage is there.  With
			 *     `requested_codec` alone, a child that lost the stage while a
			 *     client was watching ran with `poll` at zero — that is it
			 *     burned a whole core capturing nothing.  `[M]` it is the
			 *     silent half of the 14 August defect: the log is cured by
			 *     removing a line, this is not. */
			/* ⛔⭐⭐ AND THE `poll` WAIT GETS SHORTER WHEN AN ATTEMPT IS DUE —
			 *       16 Aug 2026, and without this line the cure of
			 *       `STAGE_BIRTH_RETRY_MS` did not reach the ground.
			 *
			 * ⛔ The loop, without a stage, slept **one fixed second**.  ⇒ A
			 *    retry scheduled in 200 ms could not fire at 200 ms: it fired
			 *    at the next wake-up, that is at a thousand.  The small number
			 *    would have stayed written in the source and false in fact —
			 *    and it is the "written is not in force" form that
			 *    `REVIEWER.md` calls E1, inside the cure of a timing defect.
			 *
			 * ⭐ Now we wake up WHEN the attempt is due, not at a fixed
			 *    cadence: the second stays as a ceiling (the parent must be
			 *    able to speak anyway), but it is no longer a floor. */
			{
				int wait_ms = (requested_codec && cat) ? 0 : 1000;

				/*
				 * ⛔⭐⭐ AND ZERO MEANS "NOW", NOT "NOT ARMED" — 16 Aug 2026,
				 *       and it is the SECOND time this number deceives in this
				 *       file.
				 *
				 * `[M]` The client's canvas arrives, the handler sets
				 * `stage_retry_ms = 0` to say "retry at once", and this
				 * `poll` — which read zero as "no attempt scheduled" — went to
				 * sleep.  ⇒ Between "the canvas has arrived" and "entering the
				 * mounting" **2000 ms flat** passed, that is two whole sleeps,
				 * and half the gain of the canvas cure was thrown away.
				 *
				 * ⚠ Zero as "not armed" had already done damage here on 15
				 *   August.  ⇒ Now it has ONE meaning only: "the attempt is
				 *   due", and the wait is always "how long is left", zero
				 *   included.
				 *
				 * ⛔ And it does not spin: the following attempt immediately
				 *    puts `stage_retry_ms` back in the future, so the zero
				 *    holds for one round only.
				 */
				if (!cat) {
					uint64_t t_now = log_now_ms();

					/* ⚠ Compared before the cast: a retry far away
					 *   (`close_only`'s «never») is not a negative int. */
					wait_ms = stage_retry_ms <= t_now ? 0
					          : stage_retry_ms - t_now > 1000 ? 1000
					          : (int)(stage_retry_ms - t_now);
				}
				/* ⛔⭐ AND WITH AUDIO ON THE LOOP CANNOT SLEEP A SECOND.  The
				 *     ring fills at 48 000 frames per second whatever the video
				 *     does: a 1000 ms wait would make it overflow **while the
				 *     desktop is still**, that is precisely when the user is
				 *     listening to music without touching anything.
				 * ⚠ 5 ms is a PCM block (§5.3): the loop wakes up in time to
				 *   take them away one at a time, instead of piling them up
				 *   and then dropping them. */
				/* ⏳ §13: with a pace in force the loop SLEEPS until the next
				 *    frame is due, instead of spinning on a zero wait — and
				 *    it still wakes up at once for the parent and for
				 *    `libei`, which are in this same `poll`. */
				if (requested_codec && cat && wait_ms == 0) {
					uint64_t pw = pace_wait_us(now_monotonic_us());

					if (pw)
						wait_ms = (int)((pw + 999u) / 1000u);
				}
				if (audio_codec && wait_ms > 5)
					wait_ms = 5;
				ready = poll(due, (nfds_t)amount, wait_ms);
			}
			pf.revents = due[0].revents;
			/* ⛔⛔ AND HERE THE DEBT TOWARDS WHOEVER IS PASTING IS PAID, at
			 *      every wake-up of the loop — even when the `poll` expired
			 *      empty.
			 *
			 *      ⚠ It is the only place where the `CLIPBOARD_WAIT_MS` timeout
			 *        can fire: the clipboard thread has no clock (it waits for
			 *        D-Bus signals, and if none arrive it sleeps forever), so
			 *        an unanswered request would stay hanging until someone
			 *        copies something else.
			 *      ⛔ That is, without this line the timeout would exist on
			 *        paper and never fire — the worst form of a protection:
			 *        the one read in the code that is not there. */
			clipboard_expire(log_now_ms());
			/* ⭐ If `libei` spoke, it is served AT ONCE — even before reading
			 *    the parent: it is the path on which latency is measured. */
			if (ready > 0 && amount == 2 && due[1].revents)
				input_run(stage_input);
			if (ready < 0) {
				if (errno == EINTR)
					continue;
				fine = true;
				break;
			}
			if (ready == 0)
				break;
			/* ⛔⛔⛔ AND HERE WERE THE FOUR SECONDS THE USER WAITED.
			 *
			 * `[M]` 14 Aug 2026, stack read with `gdb` 2.6 s after login: the
			 * child was stuck in `recvmsg` at `child.c:336`, that is on this
			 * line, on **fd 3** — the parent's socket.
			 *
			 * ⛔ The line above computed `pf.revents` and **nobody looked at
			 *    it**.  When the `poll` wakes up because `libei` spoke
			 *    (due[1]) and the parent said NOTHING, `ready` is > 0 anyway:
			 *    we got here and read regardless — and the CHILD's end is
			 *    **blocking on purpose** (the parent sets `O_NONBLOCK` only on
			 *    its own, and `socketpair` makes two distinct file
			 *    descriptions).  ⇒ The child stayed inside `recvmsg` until the
			 *    parent wrote it something, and **the frame loop did not turn
			 *    at all**: the log said so, and nobody had read it — *"0
			 *    frames delivered, **0 empty waits**"* for four seconds.
			 *
			 * ⚠ And it is the reason the thesis *"the latency is not ours, it
			 *   is Mutter that does not deliver on a still desktop"* was
			 *   **false**: Mutter had the frames, and we were not there to
			 *   take them.  ⭐ The log line that should have unmasked it said
			 *   *"still scene: Mutter delivers only when something changes"* —
			 *   that is it accused the compositor of a defect of ours. */
			if (!pf.revents)
				break;

			readings = receive_with_credentials(fd_child, envelope, sizeof envelope, &chi,
			                               &c_e);
			if (readings == 0) {
				registro_dice(LOG_CHILD,
				              "the parent closed the socket: dismantling the stage and "
				              "exiting.  ⚠ It is the SECOND safety net, the one "
				              "that does not depend on PR_SET_PDEATHSIG");
				fine = true;
				break;
			}
			if (readings < 0) {
				if (errno == EINTR)
					continue;
				if (errno == EAGAIN || errno == EWOULDBLOCK)
					break;
				fine = true;
				break;
			}
			if ((size_t)readings < sizeof t)
				continue;
			memcpy(&t, envelope, sizeof t);
			if (!magic_ok(&t))
				continue;
			/* ⛔ The parent must be root — or, since 1.5 (§11.50), the
			 *    network side's `remotix`, as the root side wrote on my
			 *    command line (`--parent-uid`).  A message without the
			 *    kernel's stamp is not a message from the parent. */
			if (!c_e || chi.uid != parent_uid) {
				if (parent_uid == 0)
					registro_dice(LOG_CHILD,
					              "⛔ a message that claims to come from the parent and "
					              "does not carry root's stamp (uid %ld): DISCARDED",
					              c_e ? (long)chi.uid : -1L);
				else
					registro_dice(LOG_CHILD,
					              "⛔ a message that claims to come from the parent and "
					              "does not carry its stamp (uid %ld, expected %ld): "
					              "DISCARDED",
					              c_e ? (long)chi.uid : -1L, (long)parent_uid);
				continue;
			}
			if (t.declared_uid != (uint32_t)my_uid) {
				registro_dice(LOG_CHILD,
				              "⛔ the parent believes I am uid %lu and the kernel "
				              "says %ld: I do NOT answer",
				              (unsigned long)t.declared_uid, (long)my_uid);
				continue;
			}
			if (t.kind == MSG_SHUT_DOWN) {
				fine = true;
				break;
			}
			/* ⛔ The close-only child (box at `close_only`): «end the
			 *    session» and «who are you», nothing else — no video, audio,
			 *    clipboard, layout, pace or gesture reaches this desktop. */
			if (close_only && t.kind != MSG_CHI_SEI) {
				struct body_input ci;

				if (t.kind != MSG_INPUT || (size_t)readings < sizeof t + sizeof ci)
					ci.action = 0;
				else
					memcpy(&ci, envelope + sizeof t, sizeof ci);
				if (t.kind != MSG_INPUT || ci.action != CHILDREN_INPUT_TERMINATE) {
					log_detail(LOG_CHILD,
					           "CLOSE-ONLY child: a message of kind %u DISCARDED — "
					           "only «end the session» is obeyed here",
					           (unsigned)t.kind);
					/* ⛔ review 4, finding 7: the life ceiling is checked
					 *    HERE too — this read loop leaves only when the socket
					 *    is quiet, so a network side that keeps sending
					 *    discarded messages kept the child alive past 30 s.
					 *    Out of the read loop, the check at the top of the
					 *    outer loop ends it with its line. */
					if (log_now_ms() >= close_only_since_ms + CLOSE_ONLY_LIFE_MS)
						break;
					continue;
				}
			}
			if (t.kind == MSG_VIDEO) {
				struct body_video cv;
				if ((size_t)readings < sizeof t + sizeof cv)
					continue;
				memcpy(&cv, envelope + sizeof t, sizeof cv);
				/* ⛔⭐ THE CEILING IS 3 SINCE 20 AUG 2026 (H.264, §1.13-ter), and
				 *     this line cost a round: the parent already negotiated
				 *     codec 3 and the child REFUSED it here — "the parent asks
				 *     for codec 3, which §6.2 does not define" — with the
				 *     session alive, zero frames and the page not knowing why.
				 * ⚠ The maximum number lives in ONE place only: here.  A second
				 *   check elsewhere with a number of its own is exactly the
				 *   defect just paid for. */
				if (cv.codec > CODIFICATORE_H264) {
					registro_dice(LOG_CHILD,
					              "⛔ the parent asks for codec %u, which §6.2 does not "
					              "define: I am NOT changing anything",
					              cv.codec);
					continue;
				}
				/* ⭐ The return from the third state to the first: someone wants
				 *    a desktop again.  ⛔ It is HERE and not elsewhere because
				 *    this is the only message that says "there is a client
				 *    watching": the session's birth must follow a WILL, not a
				 *    clock. */
				if (cv.codec != 0 && session_closed_by_user) {
					session_closed_by_user = false;
					registro_dice(LOG_CHILD,
					              "⭐ §7.6: someone reattaches after a logout "
					              "— from now on the graphical session can be made "
					              "to be born again, and it will be NEW");
				}
				if (cv.codec != requested_codec)
					registro_dice(LOG_CHILD,
					              cv.codec
					                  ? "⭐ PHASE 3: the frame loop turns "
					                    "ON, codec %u, %d/s asked of the "
					                    "capture"
					                  : "the frame loop turns OFF "
					                    "(codec %u): nobody is watching any more, and "
					                    "the stage stays up (I4).  %d/s",
					              cv.codec, MOTION_FPS);
				/* ⛔ And the depth with it: they are the same fact, and
				 *    separating them is exactly what has just been cured. */
				if (cv.depth && cv.depth != requested_depth) {
					registro_dice(LOG_CHILD,
					              "⭐ §4.3: the parent negotiated %u bits "
					              "(before %u)",
					              cv.depth, requested_depth);
					requested_depth = cv.depth;
				}
				/* ⛔⭐ AND THE LEVEL WITH THEM — §4.3 line 701, 23 Aug 2026.
				 *
				 * ⚠ The condition is NOT `cv.livello_x10 && ...` as for the
				 *   depth: here ZERO IS A VALUE — it means "this client
				 *   declares no level", and going from 5.1 to "no ceiling" is
				 *   a real change to be logged and obeyed.  ⛔ Treating it as
				 *   "it did not tell me" would keep in force the previous
				 *   client's ceiling, that is the error that I4 (the stage
				 *   outlives the client) makes possible.
				 * ⚠ `cv.codec &&` is there because "off" (codec 0) carries
				 *   zeros in all fields: it is not a client declaring "no
				 *   level", it is no client. */
				if (cv.codec && cv.livello_x10 != requested_level_x10) {
					if (cv.livello_x10)
						registro_dice(LOG_CHILD,
						              "⭐ §4.3: the client declares "
						              "video.level=%u.%u (before %s) — I WILL "
						              "IMPOSE it on the encoder, and then "
						              "read it back from the SPS",
						              cv.livello_x10 / 10u,
						              cv.livello_x10 % 10u,
						              requested_level_x10 ? "another one" : "none");
					else
						registro_dice(LOG_CHILD,
						              "⚠ §4.3: no video.level declared "
						              "(before %u.%u) — NO CEILING, and I do not "
						              "invent one: the level produced is "
						              "written anyway",
						              requested_level_x10 / 10u,
						              requested_level_x10 % 10u);
					requested_level_x10 = cv.livello_x10;
				}
				/* ⏳ §13.5: the ceiling belongs to the SESSION that asked for
				 *    it.  When the codec changes — nobody watches any more, or
				 *    a new viewer arrives — it is lifted here too, not only by
				 *    the parent at the end of the session. */
				if (cv.codec != requested_codec)
					pace_set(0, cv.codec ? "a new viewer" : "nobody is watching");
				requested_codec = cv.codec;
				/* ⛔ §5.2: the debt is set on the REQUESTED codec, not on all.
				 *    Asking for a keyframe for HEVC does not produce one on
				 *    AV1, and setting them together would give a keyframe to
				 *    whoever did not ask for it. */
				if (cv.key && cv.codec)
					key_debt[cv.codec] = true;
				continue;
			}
			if (t.kind == MSG_AUDIO) {
				struct body_audio ca;

				if ((size_t)readings < sizeof t + sizeof ca)
					continue;
				memcpy(&ca, envelope + sizeof t, sizeof ca);
				if (ca.codec > 2) {
					registro_dice(LOG_CHILD,
					              "⛔ the parent asks for audio codec %u, which "
					              "§6.3 does not define: I am NOT changing anything",
					              ca.codec);
					continue;
				}
				/* ⛔ The UNCHANGED codec is not a useless message: it is
				 *    someone who has just connected, and invariant I5 owes
				 *    them the volume at maximum.  ⚠ Rebuilding capture and
				 *    encoder instead no: that would cut the sound for whoever
				 *    is already listening. */
				if (ca.codec && ca.codec == audio_codec) {
					sound_max_volume(snd);
					log_detail(LOG_CHILD,
					                   "someone else connects: volume at "
					                   "maximum (I5), capture unchanged");
					continue;
				}
				audio_rule_child(ca.codec);
				continue;
			}
			/* ⭐⭐ PHASE 7 — "THE CLIENT HAS COPIED SOME TEXT": it is offered to
			 *     the session, and from there on someone will be able to
			 *     paste it.
			 * ⛔ It does not carry the text, and it is §7.4's "announce first,
			 *    then pull": the text is requested when someone really
			 *    pastes. */
			if (t.kind == MSG_CLIPBOARD_OFFER) {
				GError *sb = NULL;

				if (!stage_clipboard) {
					/* ⚠ It is not a fault: it is the stage not being there yet,
					 *   or the clipboard that did not open (the declared
					 *   fallback further up).  It is said, and we go on. */
					clipboard_pending_offer = true;
					log_detail(LOG_CLIPBOARD,
					                   "the client copied some text and the "
					                   "session's clipboard is not there "
					                   "YET: the offer is REDONE as soon as it "
					                   "opens, instead of falling");
					continue;
				}
				if (!clipboard_offer(stage_clipboard, &sb))
					registro_dice(LOG_CLIPBOARD,
					              "⛔ the offer to the session did not succeed "
					              "(%s): inside the desktop it will not be possible to "
					              "paste what the client copied",
					              sb ? sb->message : "no details");
				g_clear_error(&sb);
				continue;
			}
			/* ⭐⭐ AND THE ANSWER TO WHOEVER IS PASTING, which arrives **in
			 *     pieces**. */
			if (t.kind == MSG_CLIPBOARD_FROM_CLIENT) {
				struct body_clipboard ca;

				if ((size_t)readings < sizeof t + sizeof ca)
					continue;
				memcpy(&ca, envelope + sizeof t, sizeof ca);
				if ((size_t)readings < sizeof t + sizeof ca + ca.piece)
					continue;
				clipboard_from_client(&ca, envelope + sizeof t + sizeof ca);
				continue;
			}
			/* ⏳ `RCP.md` §13 (PROPOSED) — the client's decoder pace. */
			if (t.kind == MSG_PACE) {
				struct body_pace cp;

				if ((size_t)readings < sizeof t + sizeof cp)
					continue;
				memcpy(&cp, envelope + sizeof t, sizeof cp);
				pace_set(cp.max_fps, "the client's decoder asked for it");
				continue;
			}
			if (t.kind == MSG_LAYOUT) {
				struct body_layout cd;

				if ((size_t)readings < sizeof t + sizeof cd)
					continue;
				memcpy(&cd, envelope + sizeof t, sizeof cd);
				/* ⛔ WE impose the NUL: the envelope comes from a socket, and
				 *    an unterminated string read as such is a memory defect,
				 *    not a keyboard one. */
				cd.name[sizeof cd.name - 1] = '\0';
				/* ⚠ And if the stage is not there yet, it is DECLARED: "I did
				 *   not apply it" and "there was nothing to apply" are two
				 *   different facts (`LESSONS.md` §1.9 rule 1). */
				if (!stage_input) {
					/* ⛔ It is NOT thrown away: it is KEPT.  `rcp.c` asks for
					 *    it when `SESSION` has gone out, and `libei` opens a
					 *    few hundredths later — throwing it away here would
					 *    mean the cure works on every attach except the FIRST. */
					snprintf(pending_layout,
					         sizeof pending_layout, "%s", cd.name);
					registro_dice(LOG_CHILD,
					              "⚠ layout «%s» requested but the input channel "
					              "is not there yet: KEPT, it is "
					              "applied when the stage opens",
					              cd.name);
				}
				else
					input_layout(stage_input, cd.name);
				continue;
			}
			if (t.kind == MSG_INPUT) {
				struct body_input ci;
				int e;

				if ((size_t)readings < sizeof t + sizeof ci)
					continue;
				memcpy(&ci, envelope + sizeof t, sizeof ci);
				/* ⛔⭐ THE CANVAS IS NOT AN INPUT, and it goes BEFORE the guard
				 *     below.  ⚠ Defect found while rereading, on 15 Aug 2026:
				 *     `CHILDREN_INPUT_RECANVAS` travels inside `MSG_INPUT` so as not
				 *     to have two envelopes on the wire between parent and
				 *     child — ⛔ but the guard "I have no channel to the
				 *     compositor" belongs to GESTURES, and applied to the
				 *     canvas it would have tied the monitor resize to `libei`
				 *     opening.  ⇒ The symptom would have been: a session in
				 *     which the input did not open (a `libei` that does not
				 *     answer) also stays with black bands and interpolated
				 *     text, **and no line connects the two things**. */
				/*
				 * ⭐⭐ §7.6 — "END THE SESSION", and it lives HERE, before the
				 *     gestures guard, for the same reason as the canvas:
				 *     logging out is not a gesture, and tying it to `libei`
				 *     opening would mean that in a session where the input did
				 *     not open **one cannot even log out**.
				 *
				 * ⛔ And the farewell `0x10` has ALREADY GONE OUT when this line
				 *    runs: `rcp.c` sends it before calling the hook, because
				 *    when the compositor falls the stage falls with it and the
				 *    channel is no longer needed (`RCP.md` §7.6).
				 */
				if (ci.action == CHILDREN_INPUT_TERMINATE) {
					/* ⛔ The REAL cause is said, not the usual one: for a day
					 *    this line said "the user asked" even when the one
					 *    asking was a clock. */
					registro_dice(LOG_CHILD,
					              ci.a == CHILDREN_EXIT_ABANDON
					                  ? "⭐ §5.3: the session is ABANDONED — "
					                    "closing the graphical session and with it its "
					                    "programs.  ⚠ Nobody asked for it: "
					                    "the ceiling expired, and the "
					                    "number is in the parent's line"
					                  : "⭐ §7.6: the user asked to LOG OUT — "
					                    "closing the graphical session and with it its "
					                    "programs.  At the next attach a NEW one "
					                    "will be born");
					if (!session_terminate()) {
						registro_dice(LOG_CHILD,
						              "⛔ the graphical session did NOT "
						              "end: the user asked to "
						              "log out and the desktop is still "
						              "there.  ⚠ The client has already been "
						              "given the farewell 0x10, so "
						              "now the two truths do not "
						              "match — and this line is "
						              "the only place where it shows");
						/* ⛔ The close-only child has nothing else to
						 *    do: it does not stay to be bound to a
						 *    login (box at `close_only`). */
						if (close_only) {
							fine = true;
							break;
						}
						continue;
					}
					/* ⛔⭐ PHASE 17 T7 — AND THE CHILD EXITS WITH IT.
					 *     As long as it was the one opening the desktop's logind
					 *     session, the logout took it away (SIGTERM, see
					 *     `dismiss_child()` in the parent: "child dead =
					 *     session over").  ⚠ The child that TAKES BACK a desktop
					 *     found again sits in a logind session of its own, and
					 *     the logout does not touch it: `[M]` 30 Sep 2026, it
					 *     stayed alive and at the next round MADE a desktop nobody
					 *     had asked for be born again.  ⇒ Once the session is
					 *     closed, it exits: the stage is gone, and the next attach
					 *     will make a NEW child and desktop be born. */
					registro_dice(LOG_CHILD,
					              "⭐ the graphical session is closed: I am exiting too "
					              "— the next attach will have a NEW child and "
					              "desktop");
					fine = true;
					break;
				}

				if (ci.action == CHILDREN_INPUT_RECANVAS) {
					CaptureRecanvas r;
					uint32_t now_w = 0, now_h = 0;

					/* ⛔ The WANTED canvas is remembered BEFORE trying, and it
					 *    is not the same thing as `canvas_w`/`canvas_h` (which are
					 *    what the stage GIVES): it serves the remount.
					 *    ⚠ Without it, a stage falling after a resize is born
					 *    again at the previous size and the bands come back —
					 *    and no line connects the two things. */
					canvas_intended_w = (uint32_t)ci.a;
					canvas_intended_h = (uint32_t)ci.b;
					/* ⭐ From now on the canvas is THE CLIENT'S, not the command
					 *    line's fallback: see `canvas_from_client`. */
					if (!canvas_from_client) {
						canvas_from_client = true;
						/* ⭐ And it is retried AT ONCE: waiting for the next
						 *    retry would mean throwing away the half second
						 *    just waited on purpose. */
						stage_retry_ms = 0;
						registro_dice(LOG_CHILD,
						              "⭐ the CLIENT's canvas has arrived (%ux%u): "
						              "from now on the session can be born "
						              "at the right size, without resizing it "
						              "later",
						              canvas_intended_w, canvas_intended_h);
					}

					if (!cat) {
						/*
						 * ⛔⛔ AND HERE WE KEEP QUIET, ON PURPOSE — and until 16
						 *     Aug 2026 "I did not make it" was answered at once.
						 *
						 * ⭐ That answer looked like a kindness — "I say it at
						 *    once instead of making it wait" — ⛔ and it was the
						 *    cause of the BLACK BANDS the user saw on 16 Aug,
						 *    through a four-step chain:
						 *
						 *      1. the client asks for 2544x926 while the stage is
						 *         not there yet (server just restarted);
						 *      2. we answer `NOT_NOW`, and `rcp.c` CLOSES the
						 *         request: `canvas_flight = false`;
						 *      3. `[M]` 2.2 s later the stage mounts — and it
						 *         mounts at the WANTED size, which we remembered
						 *         above: 2544x926, right;
						 *      4. ⛔ but for `rcp.c` there is no longer any
						 *         request in flight: it sees a frame of a size
						 *         different from the canvas in force and
						 *         **brings the stage back to 1920x1080**.  Bands.
						 *
						 * ⇒ "I did not make it" and "not yet" are two different
						 *   facts (`CODER.md` §3.10, and the same form by which
						 *   zero is not failure).  Here the stage did not fail:
						 *   IT IS NOT THERE.  And §7.1 already has the right
						 *   answer for this case — the three-second deadline —
						 *   ⭐ and the real answer comes with the FRAME, which is
						 *   exactly what happens when the stage mounts at the
						 *   wanted size.
						 *
						 * ⚠ The price, declared: if the stage does NOT mount
						 *   within the three seconds, the client waits for the
						 *   deadline instead of knowing at once.  ⛔ Three seconds
						 *   of waiting are worth less than black bands for the
						 *   whole session.
						 */
						registro_dice(LOG_CHILD,
						              "§7.1: the parent asks for the canvas %ux%u but the "
						              "stage is not there YET: telling it «WAIT», "
						              "and retrying AT ONCE instead of finishing the wait "
						              "— there is someone waiting",
						              (unsigned)ci.a, (unsigned)ci.b);
						wait_canvas(canvas_intended_w, canvas_intended_h);
						/*
						 * ⛔⭐ AND THE WAIT IS RESET — 16 Aug 2026, and without
						 *     this line the "wait" was useless.
						 *
						 * `[M]` The deadline of §7.1 was postponed by three
						 * seconds ONCE, and then the child went silent: between
						 * one attempt and the next the wait doubles (1, 2, 4, 8
						 * s…), and in that silence the deadline expired anyway.
						 *
						 * ⇒ A canvas request is the news that **someone is
						 *   waiting**: the growing wait serves not to burn a
						 *   core when nobody is watching, not to make whoever
						 *   watches wait.  ⚠ And so the next round sends
						 *   another "wait", and the deadline is postponed until
						 *   the stage is really there.
						 */
						stage_wait_ms = STAGE_RETRY_MIN_MS;
						stage_retry_ms = 0;
						continue;
					}
					/*
					 * ⛔⛔⭐ EVERYTHING IS RELEASED **BEFORE** RESIZING — and this
					 *       line is worth "on Android the mouse no longer takes
					 *       clicks".
					 *
					 * `[R]` The chain is entirely inside Mutter, and no link is
					 * ours (measured by subphase 6.1, 16 Aug 2026):
					 *
					 *   1. `meta-eis-client.c:197-206` — on a geometry change
					 *      `remove_viewport_devices()` calls `eis_device_remove()`
					 *      and ⛔ **does not go through `drop_device()`**, which is
					 *      the only place where Mutter releases what was pressed;
					 *   2. `meta-eis-client.c:612-621` — `handle_button()`
					 *      **silently swallows** the release of a button not
					 *      pressed *on that* device, and after the turnover the
					 *      device is another one;
					 *   3. `meta-seat-impl.c:899-908` — `update_button_count()`
					 *      belongs to the **seat**, shared: the dead device's
					 *      press keeps it at 1, every press after brings it to 2
					 *      (discarded) and every release brings it back to 1
					 *      (discarded).  ⛔ **It never drops to zero**, and from
					 *      then on the desktop no longer takes a click — without
					 *      an error anywhere.
					 *
					 * ⇒ `[M]` It cannot be recovered from `input.c`: press+release
					 *   on the new device goes 1→2→1 and delivers nothing.  ⭐ The
					 *   only instant in which the release reaches anyone is
					 *   **now**, while the old devices are still alive.
					 *
					 * ⚠ And the cost, declared: whoever holds a button down while
					 *   the canvas changes sees it released.  ⛔ It is worth
					 *   infinitely less than a desktop that takes no click for
					 *   the whole session — and it is exactly the damage/cost
					 *   ratio that `RCP.md` §11 declares the highest of the
					 *   document.
					 *
					 * ⚠ `!stage_input` is not a fault: it is a session without
					 *   input, and the line was already written by whoever did
					 *   not open it.
					 */
					if (stage_input) {
						int down = input_release_all(stage_input);
						if (down > 0)
							registro_dice(LOG_CHILD,
							              "⭐ §7.1: RELEASED %d keys and "
							              "buttons BEFORE resizing — the "
							              "canvas change makes the libei devices "
							              "be recreated, and a button pressed during "
							              "the turnover stays down IN THE SEAT "
							              "forever (Mutter, `meta-seat-impl.c` "
							              "`update_button_count()`): from then on "
							              "the desktop no longer takes a click",
							              down);
						else
							log_detail(LOG_CHILD,
							                   "§7.1: nothing to release before "
							                   "the resize (%d)", down);
					}
					/* ⭐ PHASE 12 — on KDE the output is not resized
					 *    (`stage_size()`): the answer is the size that
					 *    exists, and the page rescales.  Asking the capture for
					 *    another would make it fall forever. */
					/* ⭐⭐ 11 Oct 2026 — and now it IS resized, by changing
					 *      the size of the labwc that hosts KWin (`kwin.h`,
					 *      «the nested KWin», `DECISIONS.md` §10.40):
					 *   1. the stage is dismantled FIRST — KWin's stream
					 *      would otherwise renegotiate to a size our fixed
					 *      offer refuses, and die under our feet;
					 *   2. the host goes to the new size, and KWin's output
					 *      is READ BACK at that size (not believed);
					 *   3. the stage is remounted at once at the wanted
					 *      canvas: the frame that arrives makes the
					 *      reconciliation of «NEW CANVAS FROM THE STAGE»
					 *      (encoder, pointer, §6.2) and the answer to the
					 *      parent — the same road as every other desktop.
					 * ⚠ A session born before this road (KWin `--virtual`) has
					 *   no host: there the old fallback holds, DECLARED. */
					if (stage_kwin) {
						uint32_t kl = canvas_intended_w, ka = canvas_intended_h;
						uint32_t ol = 0, oa = 0;
						g_autoptr(GError) why = NULL;
						uint64_t t_recanvas = log_now_ms();

						kwin_measure(stage_kwin, &ol, &oa);
						if ((ol != kl || oa != ka) && kwin_host_exists()) {
							unmount_stage(&mut, &cat);
							if (kwin_host_resize(kl, ka, 3.0, &why)) {
								registro_dice(LOG_CHILD,
								              "⭐ §7.1 KDE: canvas %ux%u → %ux%u by "
								              "resizing KWin's host (%llu ms); "
								              "remounting the stage now",
								              ol, oa, kl, ka,
								              (unsigned long long)(log_now_ms()
								                                   - t_recanvas));
							} else {
								registro_dice(LOG_CHILD,
								              "⛔ §7.1 KDE: KWin's host did not reach "
								              "%ux%u (%s): remounting the stage at "
								              "the size KWin has",
								              kl, ka,
								              why ? why->message : "?");
							}
							stage_wait_ms = STAGE_RETRY_MIN_MS;
							stage_retry_ms = 0;
							wait_canvas(canvas_intended_w, canvas_intended_h);
							continue;
						}
						if (ol != kl || oa != ka)
							registro_dice(LOG_CHILD,
							              "⚠ §7.1 KDE: this Plasma session has no "
							              "host for KWin (KWin --virtual: born before "
							              "11 Oct 2026, or labwc is not installed): "
							              "the canvas stays %ux%u and the page "
							              "rescales — DECLARED FALLBACK",
							              ol, oa);
						stage_size(&kl, &ka);
						reply_canvas(canvas_intended_w, canvas_intended_h, kl, ka);
						continue;
					}
					r = capture_resize(cat, canvas_intended_w, canvas_intended_h);
					if (r == CAPTURE_RECANVAS_REQUESTED) {
						/*
						 * ⛔ "REQUESTED" IS NOT "THE STREAM IS STILL ALIVE" — `[M]`
						 *    22 Aug 2026, bench
						 *    `benches/06-b5-capture-outcomes.c` case 2: if the
						 *    producer cannot hold the size, the renegotiation
						 *    does not leave the stream where it was, it **kills**
						 *    it 2 ms after this return.
						 *
						 * ⭐ And no new outcome is needed here, because the road
						 *    to know it is already the one this loop travels:
						 *    `capture_take()` looks at the state BEFORE
						 *    waiting ⇒ `[M]` **8.1 ms**, a single round, and the
						 *    message names "error, no more input formats".  From
						 *    there it goes through `THE STAGE HAS GONE FROM UNDER
						 *    OUR FEET` and remounts.
						 *
						 * ⏳⛔ AND THE DEFECT THAT REMAINS OPEN, declared instead
						 *     of hushed up: the remount asks for
						 *     `take_stage(tela_voluta_*)`, that is **the same
						 *     size that has just killed the stage**, and with
						 *     `requested_codec && canvas_intended_w` it picks the SHORT
						 *     wait.  `[M]` (bench 06-b5 case 3) `capture_start()`
						 *     at that size **SUCCEEDS 3 times out of 3** and the
						 *     stage is dead 300 ms later, 3 out of 3 ⇒ the loop
						 *     does not get out by itself, and `wait_canvas()` at
						 *     every round also prevents the parent from expiring.
						 *     ⚠ On the real product it is `[?]`: Mutter granted 30
						 *     sizes out of 30 up to 7680x4320, and
						 *     `rcp_size_allowed()` since 1 Oct 2026 cuts at
						 *     4096x2304.  The cure lies in the remount policy,
						 *     not here.
						 */
						registro_dice(LOG_CHILD,
						              "⭐ §7.1: canvas %ux%u REQUESTED of the compositor.  "
						              "The answer to the client goes out when a "
						              "frame arrives, not from this line",
						              (unsigned)ci.a, (unsigned)ci.b);
						continue;
					}
					if (r == CAPTURE_RECANVAS_UNCHANGED) {
						/* ⭐ The stream ALREADY has that size: no "new" frame
						 *    will arrive, because those arriving are already of
						 *    the right size.  ⇒ The answer goes at once, or the
						 *    parent would wait for the three-second deadline for
						 *    something already done. */
						/*
						 * ⛔⛔ AND "I DON'T KNOW" IS NOT SENT AS "I DID NOT MAKE
						 *     IT" — defect found **while rereading** on the
						 *     night of 16 Aug 2026, subphase 6.3.
						 *
						 * `capture_negotiated_size()` returns `FALSE` when the
						 * format **has not been negotiated yet**, and in that
						 * case ⛔ it writes NOTHING in the two parameters: `now_w`
						 * and `now_h` stay the zeros they are born with.  ⚠ And
						 * for `reply_canvas()` zero is not "I don't know": it is
						 * **"I did not make it"** (`child.h`, `body_canvas`),
						 * which `rcp.c` passes on to the client as
						 * `CANVAS(REFUSED, NOT_NOW)`.
						 *
						 * ⇒ On a **healthy** session the client was told no for a
						 *   canvas the stage already has, and the page showed
						 *   "fit" as failed.  ⛔ It is the form of `CODER.md`
						 *   §3.10 — *a denied reading is not a reading that says
						 *   zero* — inside the message that exists precisely to
						 *   take an inference away from the parent (`LESSONS.md`
						 *   §7.5).
						 *
						 * ⚠ The window is narrow and must be said: between
						 *   `capture_start()` and the first format callback.
						 *   `[M]` 16 Aug 2026, 38 passes through this branch on
						 *   bench 06-b35: **zero** with the format unknown — that
						 *   is the defect is REAL and I have not seen it fire.
						 *   ⇒ The cure is written anyway, because the case is
						 *   named by the code and the price of getting it wrong
						 *   is a "no" to someone who did nothing wrong.
						 *
						 * ⭐ And the right answer is the REQUESTED size: in this
						 *   branch `capture_resize()` answered `GIA_COSI`
						 *   precisely **because** the requested size is the one
						 *   the stream has (`capture.c`, the guard of §kde
						 *   §8.2-bis: with the format unknown it compares the
						 *   requested one).  ⇒ Saying it is not an invention: it
						 *   is the only number known for certain in that branch.
						 */
						if (!capture_negotiated_size(cat, &now_w, &now_h)) {
							now_w = canvas_intended_w;
							now_h = canvas_intended_h;
							registro_dice(LOG_CHILD,
							              "⚠ §7.1: the stage already has the canvas %ux%u, "
							              "but the format is NOT negotiated "
							              "yet: answering with the "
							              "REQUESTED size.  ⛔ A zero here would mean "
							              "«I did not make it» to a client that "
							              "did nothing wrong (CODER.md §3.10)",
							              (unsigned)ci.a, (unsigned)ci.b);
						} else
							registro_dice(LOG_CHILD,
							              "§7.1: the stage already has the canvas %ux%u "
							              "(negotiated %ux%u): answering at once",
							              (unsigned)ci.a, (unsigned)ci.b, now_w,
							              now_h);
						reply_canvas(canvas_intended_w, canvas_intended_h, now_w, now_h);
						continue;
					}
					registro_dice(LOG_CHILD,
					              "⛔ §7.1: canvas %ux%u NOT requested — the stream is not "
					              "able right now.  Saying it at once: the client will get "
					              "`CANVAS(NOT_NOW)` instead of three seconds of waiting",
					              (unsigned)ci.a, (unsigned)ci.b);
					reply_canvas(canvas_intended_w, canvas_intended_h, 0, 0);
					continue;
				}
				if (!stage_input) {
					/* ⛔ "I have no input channel" is NOT "the client made a
					 *    mistake": it is DECLARED and we carry on, and the
					 *    session stays up.  ⚠ In chatter: at sixty messages per
					 *    second one line for each would bury the log. */
					log_detail(LOG_CHILD,
					                   "input %u (action %u) and no channel "
					                   "to the compositor: NOT injected",
					                   (unsigned)ci.id, (unsigned)ci.action);
					input_refused++;
					continue;
				}
				switch (ci.action) {
				case CHILDREN_INPUT_POINTER:
					e = input_pointer(stage_input, (uint32_t)ci.a,
					                    (uint32_t)ci.b);
					break;
				case CHILDREN_INPUT_BUTTON:
					e = input_button(stage_input, ci.code, ci.pressed);
					break;
				case CHILDREN_INPUT_WHEEL:
					/* ⛔ The sign is inverted by `input_wheel()`, only once:
					 *    here it passes whole, half notches included. */
					e = input_wheel(stage_input, ci.a, ci.b);
					break;
				case CHILDREN_INPUT_LETTER:
					e = input_letter(stage_input, (uint32_t)ci.a);
					break;
				case CHILDREN_INPUT_POSITION:
					e = input_position(stage_input, ci.code, ci.pressed);
					break;
				case CHILDREN_INPUT_RELEASE_ALL: {
					int amount = input_release_all(stage_input);
					registro_dice(LOG_CHILD,
					              "⭐ §7.3: released %d keys and buttons "
					              "that were still held down.  ⚠ Zero is NOT a "
					              "fault: it means nothing was "
					              "pressed",
					              amount);
					continue;
				}
				/* ⛔ `CHILDREN_INPUT_RECANVAS` does not appear here: it is served
				 *    BEFORE the input channel guard, a few lines up, and the
				 *    reason is there.  ⚠ If it reappeared in this `switch` there
				 *    would be two roads for the same message, and the second
				 *    would never be travelled — that is code that looks alive. */
				default:
					registro_dice(LOG_CHILD,
					              "⛔ unknown input action %u: NOT "
					              "injected",
					              (unsigned)ci.action);
					input_refused++;
					continue;
				}

				/* ⛔⭐ AND HERE LIES THE POINT OF THE WHOLE SEAM: the counter
				 *     advances ONLY if the compositor took it.  §6.2 promises
				 *     that "the effect of that input is already in the scene",
				 *     and of a refused input there is no effect to see.
				 *     ⚠ Making it advance anyway would turn the `input` field
				 *     into a promise the frame does not keep — and the latency
				 *     link would believe it. */
				if (e == 0) {
					input_injected = ci.id;
					/* ⭐ THE REAL SHAPE ON LABWC: after every pointer gesture
					 *    TAKEN, the probe looks at the pixel of the encoded theme
					 *    under the point (`wlroots.h`).  On GNOME and KDE it does
					 *    nothing: the shape already comes from the metadata. */
					if (ci.action == CHILDREN_INPUT_POINTER) {
						probe_x = (uint32_t)ci.a;
						probe_y = (uint32_t)ci.b;
						probe_note = true;
					}
					if (probe_note && (ci.action == CHILDREN_INPUT_POINTER ||
					                   ci.action == CHILDREN_INPUT_BUTTON))
						capture_probe_pointer(cat, probe_x, probe_y);
				} else if (e == 1) {
					/* ⛔ Only `input_letter`: "not producible with this
					 *    layout".  The log line has already been written by
					 *    `keyboard.c`, with WHICH layout in it: here it is only
					 *    counted, or the same thing would end up twice in two
					 *    different wordings. */
					input_unproducible++;
				} else {
					input_refused++;
					log_detail(LOG_CHILD,
					                   "input %u (action %u): the compositor "
					                   "did not take it",
					                   (unsigned)ci.id, (unsigned)ci.action);
				}
				continue;
			}
			if (t.kind == MSG_RESEND_STAGE) {
				int amount = 0;
				for (uint8_t c = 1; c < 3; c++) {
					if (!kept[c])
						continue;
					send_frame(c, kept_key[c], kept_w, kept_h,
					                 kept_instant, kept[c], kept_byte[c],
					                 kept_input);
					amount++;
				}
				registro_dice(LOG_CHILD,
				              amount
				                  ? "the parent asked for the stage: sending again %d "
				                    "streams (the last KEYFRAME kept — a delta "
				                    "without its past would be a wrecked "
				                    "image, §5.2)"
				                  : "the parent asked for the stage and I have "
				                    "nothing to send again (%d): the reason is "
				                    "in the lines above",
				              amount);
				/* ⛔ And the debt is set: whoever comes back needs a NEW
				 *    keyframe, not the previous one — that one is already being
				 *    received, but its decoder starts again from there and the
				 *    deltas that follow belong to another chain. */
				if (requested_codec)
					key_debt[requested_codec] = true;

				/* ⛔⛔⭐ AND THE CLIPBOARD IS SENT AGAIN TOO — 21 Aug 2026.
				 *
				 * ⚠ This message means "a client has REATTACHED to a child that
				 *   already existed" (`main.c`, the `c_era` branch).  The child
				 *   survives between one connection and the next, so the
				 *   reading done when the clipboard was switched on happened
				 *   ONCE only: the new client does not know what is in the
				 *   desktop's clipboard.
				 * ⛔ And then, as soon as it announced itself to be found, it
				 *   took the selection empty-handed and **erased** what the
				 *   user had copied over there.  `[M]` measured on 21 Aug:
				 *   `wl-paste` said "TESTO-CHE-ERA-GIA-NEL-DESKTOP" before and
				 *   "" after the connection.
				 * ⇒ Whoever comes back receives the desktop's clipboard as they
				 *   receive the last frame: it is the same idea, applied to the
				 *   other thing the stage has to give. */
				if (stage_clipboard)
					clipboard_read_now(stage_clipboard);
				continue;
			}
			if (t.kind == MSG_CHI_SEI) {
				/* ⛔ It is READ AGAIN from the kernel, the earlier copy is not
				 *    reprinted. */
				getresuid(&r, &e, &sv);
				getresgid(&rg, &eg, &sg);
				s.uid = r;
				s.euid = e;
				s.suid = sv;
				s.gid = rg;
				s.egid = eg;
				s.sgid = sg;
				s.ppid = (uint32_t)getppid();
				s.descriptors = how_many_descriptors();
				/* ⭐ the periodic NAME check, made HERE (it may wait for NSS; it stalls this stage only) */
				{
					uid_t other = 0;

					s.name_check = (uint32_t)name_resolution(user, e, &other);
					s.name_uid = s.name_check == NAME_OTHER_UID ? (uint32_t)other : 0;
				}
				send_msg(MSG_INTRO, &s, sizeof s, NULL, 0);
				continue;
			}
		}
		if (fine)
			break;

		/* ── 1-bis. the input channel, which has a voice of its own ──────── */
		/* ⛔⭐ `libei` is NOT a library one just calls: it is a peer that
		 *     SPEAKS, and among the things it says are the two silent
		 *     turnovers of `STUDIES.md` §gnome §9 — a keymap change destroys and
		 *     recreates the keyboard device, a geometry change all the
		 *     absolute devices.  ⚠ And the pointer hooked to the old device
		 *     stops working **without an error**: whoever does not run this
		 *     loop sees no fault, only a desktop that at some point no longer
		 *     answers.
		 * ⚠ It sits HERE, between the parent's messages and the capture, for
		 *   the same reason as the order above: it does not wait, and putting
		 *   it after the capture would make it pay up to a quarter of a
		 *   second. */
		/* ⚠ And this stays as a safety net, not as the main road: the main road
		 *   is the `poll` above.  ⛔ It is needed because `libei` may have work
		 *   to do without the descriptor being readable (its own deadlines),
		 *   and a loop that trusted only the descriptor would miss them
		 *   **without any error**. */
		if (stage_input)
			input_run(stage_input);

		/* ── 1-ter. the stage that is not there: it is REMOUNTED ─────────── */
		/* ⛔⭐ THE TWO TWIN DEFECTS ARE CURED HERE, AND IT IS THE SAME PLACE
		 *     BECAUSE THEY ARE THE SAME FACT: *the child does not know its
		 *     stage is no longer there, or not there yet.*
		 *
		 *   · not there YET — the graphical session did not exist at birth;
		 *   · no longer there — the session died under a live child, and
		 *     `capture_take` declared the fault below.
		 *
		 * ⚠ And it does not disconnect (§8.3): the RCP session stays up, the
		 *   client stays connected, and when the stage comes back the desktop
		 *   reappears by itself.  ⛔ But it does not stand still either: a child
		 *   without a stage is not a frozen session, it is a child of no use. */
		if (!cat && !close_only) {
			uint64_t now = log_now_ms();
			/*
			 * ⛔⭐ AND IF WE ARE ONLY WAITING, IT IS SAID — once per second,
			 *     and no more.
			 *
			 * `[M]` 16 Aug 2026: one round in five took THIRTY seconds to make
			 * the desktop appear, and in those thirty seconds the child did not
			 * write **a single line**.  ⛔ From outside the two cases have the
			 * same face — "it is trying and failing" and "it is not trying at
			 * all" — and the difference is the whole diagnosis.  ⇒ I guessed
			 * three times, and three times the next measure said no.
			 *
			 * ⭐ A wait that does not declare itself is a wait that cannot be
			 *    cured.  This line costs one line per second and is worth the
			 *    three diagnoses it spared me.
			 */
			if (now < stage_retry_ms) {
				static uint64_t logged_ms;

				if (now - logged_ms >= 1000) {
					logged_ms = now;
					registro_dice(LOG_CHILD,
					              "⏳ without a stage and WAITING: %llu ms to the "
					              "next attempt (current wait %llu ms, "
					              "birth requested %llu ms ago) — ⚠ I am not "
					              "trying and failing: I am not trying",
					              (unsigned long long)(stage_retry_ms - now),
					              (unsigned long long)stage_wait_ms,
					              birth_requested_ms
					                  ? (unsigned long long)(now - birth_requested_ms)
					                  : 0ULL);
				}
			}
			if (now >= stage_retry_ms) {
				/* ⛔⭐ AND THE WHOLE ATTEMPT IS TIMED, not its three main
				 *     steps.
				 *
				 * `[M]` 16 Aug 2026: the three stopwatches inside
				 * `take_stage` were silent — no step above 250 ms — and yet
				 * in nineteen seconds there were TEN attempts, that is almost
				 * two seconds each.  ⇒ The time lay in a piece no stopwatch
				 * covered, and the candidate is the DISMANTLING of an attempt
				 * failed halfway: it closes objects on a compositor that does
				 * not answer, and `mutter.c` waits there up to FIFTEEN seconds.
				 *
				 * ⚠ Lesson, and it holds beyond this defect: **a stopwatch on
				 *   the steps you suspect measures your suspicions.**  What is
				 *   needed goes around the whole round. */
				uint64_t attempt_ms = log_now_ms();
				bool taken;

				/* ⛔ It is remounted at the WANTED canvas, not at the one the
				 *    fallen stage had: what the client asked for does not die
				 *    with the graphical session.  ⚠ If the compositor grants
				 *    something else, the reconciliation of point 2 will say so
				 *    and the parent will know. */
				taken = take_stage(canvas_intended_w, canvas_intended_h, dir_survey,
				                        false, &mut, &cat);
				if (log_now_ms() - attempt_ms >= 250)
					registro_dice(LOG_CHILD,
					              "⏱ the WHOLE ATTEMPT (%s) took "
					              "%llu ms — and the stopwatches of the single steps "
					              "are silent: the time lies outside them",
					              taken ? "succeeded" : "failed",
					              (unsigned long long)(log_now_ms() - attempt_ms));
				if (taken) {
					registro_dice(LOG_CHILD,
					              "⭐⭐ RESTARTING THE CAPTURE: the stage came back "
					              "after %llu ms of waiting — and the next "
					              "frame will be a KEYFRAME (§5.2), because "
					              "whoever is watching has lost the stream's past",
					              (unsigned long long)stage_wait_ms);
					stage_wait_ms = STAGE_RETRY_MIN_MS;
					stage_retry_ms = 0;
					/* ⛔ §5.2: after a gap the client can NOT decode a delta —
					 *    its decoder no longer has the past of this chain.  The
					 *    debt is set on the REQUESTED codec, not on all. */
					if (requested_codec)
						key_debt[requested_codec] = true;
				} else {
					/* ⛔ What the attempt left halfway is dismantled: a `mut`
					 *    open without capture would keep a virtual monitor
					 *    nobody consumes. */
					unmount_stage(&mut, &cat);
					/* ⛔⭐ HERE THE TWO CASES THE COMMENT ABOVE ALREADY NAMED
					 *     ARE TOLD APART, and until 16 Aug 2026 it treated both
					 *     with the same wait.
					 *
					 *   · not there YET — the session was requested and
					 *     `gnome-session` is getting up: ⭐ we retry DENSELY,
					 *     because the only thing separating us from the desktop
					 *     is noticing it, and noticing costs a D-Bus call to a
					 *     name that is not there.
					 *   · no longer there — or not arriving: ⚠ the wait doubles,
					 *     and it is the rein of the 30 GB of log.
					 *
					 * ⇒ See `STAGE_BIRTH_RETRY_MS`: it is the cure for "at
					 *   the fourth login the desktop took many seconds".
					 *
					 * ⛔⭐⭐⭐ AND THE REAL RULE IS THE SECOND CONDITION, which
					 *        cost four wrong diagnoses:
					 *        **the doubling wait is for when NOBODY IS
					 *        WATCHING.**
					 *
					 * `[M]` 16 Aug 2026.  As soon as the child had a line to say
					 * it, it gave both pieces together:
					 *
					 *   "⏳ without a stage and WAITING: 4962 ms to the next
					 *    attempt (current wait **30000 ms**, birth requested
					 *    **0 ms** ago)"
					 *
					 *   · `current wait 30000` ⇒ the wait really doubled, up to
					 *     the ceiling: 2, 4, 8, 16, 30 seconds;
					 *   · `birth requested 0 ms ago` ⇒ ⛔ and the guard above
					 *     could not fire, because `birth_requested_ms` is written
					 *     ONLY when the session turns out DEAD.
					 *
					 * ⭐ And the slow rounds are EXACTLY those in which the
					 *    session is not dead: it is the previous one still
					 *    closing (B7 of `SPECS.md` §5.9; `[M]` `loginctl`
					 *    says `State=closing`).  The child, rightly, does not
					 *    touch it — bringing down a live one would take the
					 *    desktop away from whoever watches it (I4) — ⛔ but then
					 *    it started waiting THIRTY SECONDS for a stage arriving
					 *    in three.
					 *
					 * ⇒ ⚠ The rein of the 30 GB remains necessary, but the case
					 *   it cured was another: a child WITHOUT A CLIENT remounting
					 *   forever.  ⭐ When instead a client is attached and is
					 *   asking for a canvas, on the other side there is a person
					 *   in front of a frozen screen, and the only defensible wait
					 *   is the shortest.
					 *
					 * ⛔ And it costs nothing: the log line is written at most
					 *    once per second anyway. */
					/* ⛔⭐ And "waiting for the client's canvas" is a "not
				 *     yet", not a failure: `[M]` 16 Aug 2026, without this
				 *     third condition the guard's refusal ended up in the
				 *     doubling wait, and the session was born at 3.2 s
				 *     instead of 1.1 — that is the cure ate half of its
				 *     gain. */
				if (is_being_born(now) || !canvas_from_client ||
				    (requested_codec && canvas_intended_w)) {
						stage_wait_ms = STAGE_BIRTH_RETRY_MS;
						stage_retry_ms = now + stage_wait_ms;
						log_detail(LOG_CHILD,
						                   "without a stage and SOMEONE IS WATCHING (or the "
						                   "session is being born, requested %llu "
						                   "ms ago): retrying in %llu ms — densely "
						                   "on purpose, the doubling wait is "
						                   "for the stage that is NO LONGER there, "
						                   "not for the one that is not there YET",
						                   birth_requested_ms
						                       ? (unsigned long long)(now - birth_requested_ms)
						                       : 0ULL,
						                   (unsigned long long)stage_wait_ms);
						if (canvas_intended_w && canvas_intended_h)
							wait_canvas(canvas_intended_w, canvas_intended_h);
						/* ⛔⭐⭐ AND THE AUDIO RING IS EMPTIED BEFORE LEAVING
						 *       HERE, because this `continue` skips the
						 *       `audio_drain()` line further down — and it is
						 *       a real defect of the product, not a lab case.
						 *
						 * `[M]` 27 Aug 2026, inside the GNOME box: a freshly
						 * born session stays without a stage for a while (~97 s
						 * there for a reason of the environment, ~2 s
						 * elsewhere), and for all that time the round went
						 * through here.  ⇒ The child declared it itself as soon
						 * as the stage arrived: *"the audio ring overflowed by
						 * 4 631 505 frames (96 489 ms)"*, and the sound
						 * restarted at ~200 blocks/s to work off the backlog.
						 *
						 * ⚠ The sound capture does NOT wait for the stage: it
						 *   starts at `MSG_AUDIO`, that is as soon as someone
						 *   connects, and from that instant PipeWire writes into
						 *   the ring.  ⛔ If nobody reads it, the ring goes round
						 *   on itself and the samples are dropped.
						 *
						 * ⭐ And calling it here costs nothing and risks
						 *   nothing: `audio_drain()` exits at once if audio is
						 *   not on, and what it touches (ring, audio encoder,
						 *   socket to the parent) has NOTHING to do with the
						 *   stage — the sink is a PipeWire node of ours, not a
						 *   canvas of the compositor. */
						audio_drain();
						continue;
					}
					if (stage_wait_ms < STAGE_RETRY_MIN_MS)
						stage_wait_ms = STAGE_RETRY_MIN_MS;
					else
						stage_wait_ms *= 2;
					if (stage_wait_ms > STAGE_RETRY_MAX_MS)
						stage_wait_ms = STAGE_RETRY_MAX_MS;
					stage_retry_ms = now + stage_wait_ms;
					registro_dice(LOG_CHILD,
					              "⛔ NO STAGE: the attempt did not succeed "
					              "— retrying in %llu ms.  ⚠ The wait grows "
					              "on purpose: without it, this loop writes gigabytes "
					              "of log and burns a core",
					              (unsigned long long)stage_wait_ms);
					/*
					 * ⭐⭐ AND "WAIT" KEEPS BEING SAID — 16 Aug 2026, and
					 *     without this line the earlier cure was useless:
					 *     saying it ONCE moves the deadline of §7.1 three
					 *     seconds from now, and `[M]` the stage took FIVE
					 *     seconds to mount after a logout.
					 *
					 * ⇒ As long as there is a wanted size and a stage that is
					 *   not there, the parent must know at every round that
					 *   someone is still trying.  ⚠ It is the opposite of
					 *   silence: whoever keeps quiet makes others infer, and the
					 *   inference was the defect.
					 */
					if (canvas_intended_w && canvas_intended_h)
						wait_canvas(canvas_intended_w, canvas_intended_h);
				}
			}
		}

		/* ── 1-bis. the audio ────────────────────────────────────────────── */
		/* ⛔ THIS LINE GUARDS AGAINST ONE `continue` ONLY: the one of the video
		 *    part, below (§2).  ⚠ It sits BEFORE it and it is not a detail of
		 *    order — that `continue` fires every time nobody is watching, and
		 *    audio would end up inside it by accident.  ⇒ A session with audio
		 *    on and video off **would not play**, and no line would say why.
		 *    The case is not theoretical: it is what happens to whoever listens
		 *    to music with the browser tab in the background.
		 *
		 * ⛔⭐ AND IT DOES NOT COVER THE OTHER `continue`s OF THE ROUND — the
		 *     comment that said only the first half cost the defect of 27 Aug
		 *     2026: whoever read it concluded "audio is safe", and the
		 *     `continue` of the "without a stage and SOMEONE IS WATCHING"
		 *     branch (§1-ter, further up) skipped this line for the whole
		 *     birth of the session.  ⇒ There `audio_drain()` is called by
		 *     hand, and the reason is written next to that `continue`.
		 * ⚠ Whoever adds a `continue` in this loop must decide the same, and
		 *   say so: above this line one passes through here, below one does
		 *   not. */
		audio_drain();

		/* ── 2. the frame ────────────────────────────────────────────────── */
		if (!requested_codec || !cat)
			continue;
		/* ⏳ §13 — THE DECODER'S PACE: not due yet ⇒ the capture is not even
		 *    looked at.  ⭐ Its slot keeps the newest picture and the union of
		 *    the damage, so the frame taken later carries every change.
		 * ⚠ After `audio_drain()` on purpose: the audio does not wait for the
		 *   video's pace (see the box above that line). */
		if (pace_wait_us(now_monotonic_us())) {
			pace_held++;
			if (pace_held - pace_held_logged >= 1000u) {
				pace_held_logged = pace_held;
				log_detail(LOG_CHILD,
				           "⏳ PACE %u/s in force: %llu rounds held back so far",
				           (unsigned)pace_fps, (unsigned long long)pace_held);
			}
			continue;
		}
		{
			CaptureStopped fo;
			GError *mistake = NULL;
			CaptureTake take;
			uint64_t instant_us, t_now;

			memset(&fo, 0, sizeof fo);
			/* ⭐ A keyframe due takes whatever comes, even a copy of the
			 *    picture: holding it back would turn into a stream restart
			 *    (the wake-up below), which costs far more (`unchanged.h`). */
			capture_unchanged_bypass(cat, requested_codec < CODEC_MAX &&
			                                  key_debt[requested_codec]);
			take = capture_take(cat, MOTION_WAIT_S, &fo, &mistake);
			/* ⛔⭐ THE COUNT IS WRITTEN BEFORE LOOKING AT THE OUTCOME, AND IT IS
			 *     A CURE FOUND BY THE FIRST LIVE RUN (13 Aug 2026).
			 *
			 *     The first draft wrote this line only AFTER a delivered frame:
			 *     on a still desktop — that is on every machine without a
			 *     declared scene — the loop ran and the log said NOTHING.
			 *     ⛔ "The loop does not start", "the capture does not deliver"
			 *     and "the scene is still" all three had the same face:
			 *     silence.  It is exactly `LESSONS.md` §1.9 — "empty" and
			 *     "forbidden" with the same look — inside the line that should
			 *     unmask it.
			 *
			 *     ⇒ Now it is written anyway, once per second, with the ZEROS
			 *     in it: whoever reads tells the three things apart without
			 *     inferring. */
			t_now = now_monotonic_us();
			if (t_now - cycle_logged_ms >= 1000000u) {
				cycle_logged_ms = t_now;
				registro_dice(LOG_CHILD,
				              "loop: %llu frames delivered (%llu keyframes), "
				              "%llu empty waits (still scene: Mutter delivers "
				              "only when something changes), %llu faults — codec "
				              "%u, %d/s requested, wait %.2f s%s",
				              (unsigned long long)cycle_frames,
				              (unsigned long long)cycle_keys,
				              (unsigned long long)cycle_zero,
				              (unsigned long long)cycle_faults, requested_codec,
				              MOTION_FPS, MOTION_WAIT_S,
				              /* ⛔⭐ AND THIS TAIL IS WORTH AS MUCH AS THE LINE.
				               *
				               * `[M]` 14 Aug 2026: for four seconds the log
				               * said *"0 frames delivered, 0 empty waits
				               * (still scene: Mutter delivers only when
				               * something changes)"* — and whoever read it
				               * concluded the latency was Mutter's.  ⛔ It was
				               * the opposite: **zero empty waits means nobody
				               * even tried to capture**, that is the loop was
				               * stuck elsewhere.  The line had the right number
				               * and the wrong word next to it. */
				              (cycle_frames == 0 && cycle_zero == 0
				               && cycle_faults == 0)
				                  ? "  ⛔⛔ and ZERO empty waits means that "
				                    "the loop DID NOT EVEN TRY to capture: "
				                    "it is NOT «the scene is still», it is this "
				                    "process being somewhere else"
				                  : "");
			}

			/* ⭐⭐ THE FOURTH SYMPTOM — the 4 seconds between login and desktop,
			 *     and they are cured HERE because here are both the facts
			 *     needed: "someone is waiting for a frame" and "none is
			 *     arriving".
			 *
			 * `[M]` 14 Aug 2026, log of 21:32:55: a keyframe request every
			 * 200 ms for **4.4 seconds** and **659 empty waits**, because a
			 * Wayland compositor delivers only when the scene changes — and a
			 * freshly switched-on desktop is still.  ⇒ The client asks for the
			 * image, the stage has nothing to give, and neither of the two is
			 * wrong.
			 *
			 * ⛔ Xpra orders "repaint now" (`buffer_refresh`) and on Wayland
			 *    that cannot be done.  ⭐ The only lever is restarting the
			 *    stream, which is what `capture_wake()` does.
			 *
			 * ⚠ And it is done ONLY when a keyframe is due — that is when there
			 *   really is someone who cannot paint anything — and no more than
			 *   once every `WAKEUP_MS`: every restart costs the
			 *   renegotiation, and doing sixty per second would remove precisely
			 *   the frames being sought. */
			/* ⚠ `requested_codec` sits inside the array, and the bound is ONE:
			 *   whoever adds a codec must not find a second one written by hand
			 *   here (it was `< 3`, and it was left behind on 20 August). */
			if (take == CAPTURE_TAKE_ZERO && requested_codec < CODEC_MAX
			    && key_debt[requested_codec]) {
				uint64_t current_ms = log_now_ms();
				if (current_ms - wakeup_ms >= WAKEUP_MS) {
					/*
					 * ⛔⛔⛔ CURE "A" — 21 Aug 2026.  🔸 DERIVED by the
					 *       coordinator, and the price below is VISIBLE to the
					 *       user: when they see it, the judgement is theirs.
					 *
					 * THE FACT, `[M]` (bench `benches/06-b33-wakeup.*`):
					 * `capture_wake()` makes Mutter recreate the absolute
					 * devices — **3 wake-ups, 3 turnovers, with ZERO canvas
					 * changes** — and if at that moment a button is pressed,
					 * that button stays down **in the seat** and ⛔ **the
					 * desktop no longer takes a click for the whole session**.
					 * It is `phases/06-the-canvas-and-the-view.md` §4.6, for the
					 * second door §7.1 found.
					 *
					 * ⛔ And this line sits in the worst possible place: one
					 *    gets here when **the scene is still**, that is exactly
					 *    when the user can hold the mouse down on a motionless
					 *    desktop.
					 *
					 * ⛔ The obvious cure — releasing first, as is done at
					 *    `:3964` before `capture_resize()` — IS FORBIDDEN
					 *    HERE: there it is the client that asked for the canvas
					 *    change, here nobody asked for anything, and releasing
					 *    would destroy **every drag**.
					 *
					 * ⇒ We do not wake up: we wait for the user to let go.
					 *
					 * 🔸 THE PRICE, and the user will see it: on a still
					 *    desktop, with a key or a button held down, the keyframe
					 *    does not go out — and a client just attached may stay
					 *    with the **blank page** until it is released.
					 *    ⚠ It is limited and heals by itself: `wakeup_ms` is
					 *      NOT touched, so at the first release the backoff has
					 *      already expired and the next round wakes up.
					 *    ⚠ And the scene is rare: a drag **moves** the desktop,
					 *      and then the grab is not ZERO and one does not even
					 *      get here.
					 *
					 * ⚠ What this guard does NOT cover is repaired by cure "C"
					 *   in `input.c` (`heal()`): the doors we do not control —
					 *   `monitors-changed`, the keymap change, and those GNOME
					 *   will add.
					 */
					unsigned down = stage_input ? input_pressed(stage_input) : 0;

					if (down) {
						/* ⛔ And it is said ONCE per wait, not at every round: at
						 *    400 ms each these lines would drown the log
						 *    precisely while the user drags. */
						if (!wakeup_quiet) {
							wakeup_quiet = 1;
							registro_dice(
							    LOG_CHILD,
							    "⛔ a KEYFRAME is due and the scene is still, but %u "
							    "keys and buttons are HELD DOWN: I am NOT waking up "
							    "the stream.  ⭐ The wake-up makes the libei devices "
							    "be recreated (`[M]` §7.1) and a button pressed during "
							    "the turnover stays down IN THE SEAT forever.  🔸 The "
							    "price, declared: whoever has just attached may "
							    "see the blank page until the user lets go",
							    down);
						}
					} else {
						wakeup_quiet = 0;
						wakeup_ms = current_ms;
						registro_dice(LOG_CHILD,
						              "⭐ a KEYFRAME is due and the scene has been still for "
						              "%u ms: restarting the stream to get "
						              "a frame delivered.  ⚠ Without it, the user looks at a "
						              "blank page until something moves on the "
						              "desktop (`[M]` 4.4 s on 14 Aug 2026)",
						              (unsigned)WAKEUP_MS);
						capture_wake(cat);
					}
				}
			}

			/* ⭐ 15 Oct 2026 — a frame held back as «unchanged» on the CARD
			 *    and then the scene went still (`unchanged.h`, «pending»): it
			 *    may hide a change whose damage KWin lost, its buffer is
			 *    already back with KWin, and no frame will come by itself.
			 *    ⇒ The same restart as above, with the same guards (no key or
			 *    button down, `WAKEUP_MS`), and at most one every
			 *    `UC_WAKE_GAP_MS`.  ⚠ `capture_wake()` clears the flag; a
			 *    refused restart is retried at the next round. */
			if (take == CAPTURE_TAKE_ZERO && capture_unchanged_stale(cat)) {
				uint64_t current_ms = log_now_ms();

				if (current_ms - wakeup_ms >= WAKEUP_MS
				    && current_ms - uc_wake_ms >= UC_WAKE_GAP_MS
				    && !(stage_input && input_pressed(stage_input))) {
					wakeup_ms = current_ms;
					uc_wake_ms = current_ms;
					capture_wake(cat);
				}
			}

			/* ⛔⭐ PHASE 12 — ON PLASMA THE SESSION DIES SILENTLY.  `[M]` 19
			 *    Sep 2026, the user's logout: KWin goes away, and the grab
			 *    returns "zero" forever — the child woke up the stream every
			 *    400 ms and the page stayed frozen on the last image instead of
			 *    going back to the login form (`DECISIONS.md` §4.1-quater).
			 *    ⇒ The connection to KWin is checked, and if it has fallen the
			 *    same road as "the stage has gone" is taken: dismantled, the
			 *    remount asks `session_state()`, which says DEAD. */
			if (stage_kwin && kwin_closed(stage_kwin)) {
				registro_dice(LOG_CHILD,
				              "⛔⛔ KWIN IS GONE: the Plasma session is over "
				              "(logout, or the compositor died).  Dismantling the "
				              "stage, and the next attempt will be able to say whether the "
				              "session is closed");
				g_clear_error(&mistake);
				capture_stopped_free(&fo);
				unmount_stage(&mut, &cat);
				stage_wait_ms = STAGE_RETRY_MIN_MS;
				stage_retry_ms = log_now_ms() + stage_wait_ms;
				continue;
			}
			if (take == CAPTURE_TAKE_ZERO) {
				/* ⛔ ZERO AND FAILURE ARE TWO DIFFERENT THINGS, and this is the
				 *    zero: the stream was active for the whole wait and nothing
				 *    arrived.  On Mutter it is the STILL DESKTOP, and it is a
				 *    result — `LESSONS.md` §1.1: "a Wayland compositor delivers
				 *    a frame only when something changes".
				 *    ⚠ Nothing is encoded and nothing is sent: I1 forbids
				 *    lowering the rate out of caution, not standing still when
				 *    the scene does not move. */
				cycle_zero++;
				g_clear_error(&mistake);
				continue;
			}
			if (take != CAPTURE_TAKE_DONE
			    && take != CAPTURE_TAKE_PIXEL_ELSEWHERE) {
				/* ⛔⛔ AND HERE WERE THE 30.8 GB OF LOG.
				 *
				 * `[M]` 14 Aug 2026, the user's real session: the graphical
				 * session died under a live child, the PipeWire stream went
				 * into `connection error`, and `capture_take` from that
				 * moment returns **at once** — the 0.25 s wait is not even
				 * spent, because the stream's state is checked before waiting
				 * (`capture.c`).  ⇒ This `continue` put the loop back at the
				 * top **millions of times per second**, and every round wrote
				 * this line: 112 million identical lines, all in the same
				 * millisecond, and the disk full.
				 *
				 * ⇒ ⭐ Now the stage is DISMANTLED: `cat` becomes NULL, the
				 *   loop does not pass here again, and the remount with the
				 *   growing wait is at point 1-ter.  ⚠ The line is written
				 *   **once per loss**, not once per round. */
				cycle_faults++;
				registro_dice(LOG_CHILD,
				              "⛔⛔ THE STAGE HAS GONE FROM UNDER OUR FEET "
				              "(grab %u: %s).  ⚠ It is NOT «the scene is still»: "
				              "it is the graphical session that is no longer there.  Dismantling "
				              "the stage and remounting it when it comes back — the RCP "
				              "session stays up (§8.3), and whoever is watching will see "
				              "the last image until the desktop reappears",
				              (unsigned)take,
				              mistake ? mistake->message : "no details");
				g_clear_error(&mistake);
				capture_stopped_free(&fo);
				unmount_stage(&mut, &cat);
				stage_wait_ms = STAGE_RETRY_MIN_MS;
				stage_retry_ms = log_now_ms() + stage_wait_ms;
				continue;
			}
			g_clear_error(&mistake);

			/* ══ ⭐⭐ THE NEW SIZE HAS ARRIVED — and THE FRAME says it ══════════
			 *
			 * ⛔ It is the point where the resize becomes a fact, and there is
			 *    ONE on purpose: the request starts from `CHILDREN_INPUT_RECANVAS`,
			 *    but between the request and the pixels there is a compositor
			 *    that can grant something else (`RCP.md` §4.5), answer
			 *    "succeeded" without doing anything (`[M]` labwc), or not make
			 *    it.  ⇒ Here we do not look at what was REQUESTED: we look at
			 *    what ARRIVED.
			 *
			 * ⛔⛔ AND ALL THREE THINGS MUST BE DONE, or the defect is worse than
			 *     the one being cured:
			 *
			 *   1. the ENCODER is reopened at the new size.  ⚠
			 *      `codificatore_comprimi()` receives the pixels and the stride,
			 *      **not** width and height (`encoder.h`): fed with an
			 *      image larger than the one it is open for it does not
			 *      complain — it crops or pads, and the defect shows only in the
			 *      image.  ⭐ And the reopening brings along the keyframe §5.2
			 *      demands ("on HEVC in Chrome a delta at the new size raises
			 *      nothing: the decoder keeps emitting frames at the OLD size");
			 *   2. the POINTER REGION is remapped.  Without it, the pointer stays
			 *      in the previous space and goes elsewhere — the defect measured
			 *      for two days on the DeX;
			 *   3. `canvas_w`/`canvas_h` become the real ones, because they are the
			 *      numbers that end up in the 28 bytes of §6.2 and that the
			 *      parent compares with the canvas in force.  ⛔ Until they were,
			 *      those two fields said what the child had REQUESTED at birth:
			 *      a size DECLARED and never verified, that is guard 3 of
			 *      §5.0-sexies open at the last link.
			 *
			 * ⚠ And this round's frame is sent ANYWAY, at its own size: it is
			 *   the first at the new size, and it is the one that makes the
			 *   parent send `CANVAS(FITTED)` (§7.1).  Throwing it away would mean
			 *   postponing by a round the thing everyone is waiting for. */
			/* ⛔⛔ AND FIRST OF ALL: THE FRAME MUST CONTAIN WHAT IT DECLARES —
			 *     the guard born while refuting, on the night of 15 Aug 2026,
			 *     and the first draft put it AFTER the reconciliation.
			 *
			 * `codificatore_comprimi()` receives **the pixels and the stride**,
			 * not width and height: it reads up to `(height-1) x stride +
			 * width x 4` bytes, and it knows the geometry from its opening.
			 * ⇒ TWO checks are needed, not one:
			 *
			 *   · `stride >= width x 4`  — the "canvas WIDENS" direction, which
			 *     the check on bytes alone does NOT cover: with the old stride
			 *     and the new width the sums add up and the read goes out
			 *     anyway;
			 *   · `bytes >= stride x height` — the "canvas GROWS TALLER"
			 *     direction.
			 *
			 * ⛔ And it sits BEFORE the reconciliation because a frame that is
			 *    then discarded must not have already made the encoders reopen
			 *    (a VAAPI context), remapped the pointer and moved
			 *    `canvas_w`/`canvas_h` to a size those pixels did not have.
			 *
			 * ⚠ `width`/`height` at zero made the old guard EMPTY
			 *   (`byte < 0` is always false): they are named, instead of
			 *   trusting the numbers to add up. */
			/* ⚠ And it holds on both roads, with the same arithmetic: on the
			 *   card `byte` is not a copy to read but `stride x height` read
			 *   from the chunk, and whoever imports the DMA-BUF describes exactly
			 *   that region.  ⛔ A stride shorter than the declared width would
			 *   make the GPU read beyond the object, which is the same defect as
			 *   before with another reader. */
			if (!fo.width || !fo.height || !fo.stride
			    || fo.stride < (guint64) fo.width * 4u
			    || fo.byte < (guint64) fo.stride * fo.height) {
				inconsistent_frames++;
				if (inconsistent_frames == 1)
					registro_dice(LOG_CHILD,
					              "⛔ frame DISCARDED: it declares %ux%u with stride %u "
					              "and carries %llu bytes — whoever compresses it would read "
					              "beyond the copy (stride >= %llu and bytes >= "
					              "%llu are needed).  ⚠ It is the window between a renegotiation and "
					              "the new buffers",
					              fo.width, fo.height, fo.stride,
					              (unsigned long long)fo.byte,
					              (unsigned long long)((guint64)fo.width * 4u),
					              (unsigned long long)((guint64)fo.stride * fo.height));
				capture_stopped_free(&fo);
				continue;
			}

			if (fo.width != canvas_w || fo.height != canvas_h) {
				uint32_t requested_w = 0, requested_h = 0;
				char error[256];

				/* ⭐ AND THIS IS THE PLACE WHERE THE DIVERGENCE IS REALLY READ,
				 *    and it is the only one: `capture.c` sees it on the FORMAT —
				 *    where it cannot know whether that `Format` answers the
				 *    current request or a superseded one — while here it is seen
				 *    on the PIXELS, which have arrived and cannot be taken back.
				 *    It is the rule of §5.0-sexies: *"the frame tells the truth"*.
				 *
				 * ⚠ `[M]` 22 Aug 2026, bench `benches/06-b5-capture-outcomes.c`
				 *   case 4: here too the two numbers can diverge for an INNOCENT
				 *   reason — two chained `FIT_CANVAS` (the user dragging the
				 *   edge), where this frame answers the earlier request and the
				 *   new one's is on its way.  ⇒ The line NAMES both motives
				 *   instead of accusing one: a log that attributes the wrong
				 *   cause costs more than a silent log.  ⛔ And in neither case
				 *   does the behaviour change: the reconciliation below looks at
				 *   the frame, which is right in both. */
				capture_measure_requested(cat, &requested_w, &requested_h);
				registro_dice(LOG_CHILD,
				              "⭐⭐ NEW CANVAS FROM THE STAGE: %ux%u → %ux%u (asked of the "
				              "producer %ux%u)%s.  Reopening the encoder, "
				              "remapping the pointer, and from here the 28 bytes of §6.2 "
				              "carry the new size",
				              canvas_w, canvas_h, fo.width, fo.height, requested_w,
				              requested_h,
				              (requested_w == fo.width && requested_h == fo.height)
				                  ? ""
				                  : " — ⛔ GRANTED DIFFERS FROM REQUESTED: either the "
				                    "compositor granted something else (§4.5 "
				                    "allows it), or this frame answers a "
				                    "SUPERSEDED request (`[M]` two chained FIT_CANVAS, "
				                    "bench 06-b5 case 4).  ⚠ Reconciling "
				                    "on the FRAME, which is right in both");

				/* 1. the encoder, ⛔ ALL the live ones: the keyframe debt is per
				 *    codec, and an encoder open and not resized would deliver
				 *    cropped images at the first frame after a codec change. */
				for (uint8_t c = 1; c < CODEC_MAX; c++) {
					if (!enc[c])
						continue;
					if (!codificatore_ridimensiona(enc[c], fo.width,
					                               fo.height, error,
					                               sizeof error)) {
						registro_dice(LOG_CHILD,
						              "⛔⛔ encoder %u did NOT reopen at "
						              "%ux%u (%s): DROPPING it instead of feeding it "
						              "an image that is not its own — better "
						              "no frame than a cropped one",
						              c, fo.width, fo.height, error);
						codificatore_libera(enc[c]);
						enc[c] = NULL;
					}
					/* ⛔ §5.2: the first at the new size MUST be a keyframe.
					 *    `codificatore_ridimensiona()` already imposes it by
					 *    itself; the debt is set anyway, because an encoder
					 *    DROPPED above will be born again from the
					 *    `encoder_of()` further down and that one knows
					 *    nothing about this change. */
					key_debt[c] = true;
				}

				/* 2. the pointer region.  ⚠ If there is no input channel it is not
				 *    a fault: it is a session without input, and it is silent here
				 *    because the line was already written by whoever did not open
				 *    it. */
				if (stage_input
				    && input_recanvas(stage_input, fo.width, fo.height) != 0)
					registro_dice(LOG_CHILD,
					              "⛔ the pointer region did NOT get remapped "
					              "on %ux%u: from here on the pointer would go "
					              "where it must not",
					              fo.width, fo.height);
				/* ⭐ PHASE 15, D-007 — the screen changed size: the windows left
				 *    partly outside are brought back inside (on GNOME and KDE the
				 *    compositor does it, and the call does nothing).  ⚠ HERE, at
				 *    the first frame of the new size: labwc has already redone
				 *    the layout. */
				if (stage_input)
					input_bring_back_inside(stage_input);

				/* 3. ⛔ AND THE KEPT KEYFRAMES ARE THROWN AWAY — defect found
				 *    while refuting: `kept[]` is per CODEC, but
				 *    `kept_w`/`kept_h` are a single pair.  ⇒ After a resize
				 *    the inactive codec kept a keyframe of the OLD size that
				 *    `MSG_RESEND_STAGE` would have sent declaring the NEW size:
				 *    the client would have sized the canvas on one number and
				 *    received pixels of another — that is the stretched image and
				 *    the misplaced pointer, the defect this chain exists to
				 *    close. */
				for (uint8_t c = 0; c < 3; c++) {
					if (!kept[c])
						continue;
					free(kept[c]);
					kept[c] = NULL;
					kept_byte[c] = 0;
					kept_key[c] = false;
				}

				/* 4. and the real size becomes ours. */
				canvas_w = fo.width;
				canvas_h = fo.height;

				/* ⭐ 4-bis.  AND ZERO COPY IS RETRIED, because the canvas has
				 *    changed: it had been denied for the PREVIOUS canvas, and on
				 *    this one the stride may be good.  ⛔ Without this line a
				 *    single crooked canvas would switch off zero copy for the
				 *    whole session, including the canvases that would be fine —
				 *    that is a permanent cure for a temporary defect.
				 * ⚠ Nothing is remounted here: it is flagged, and the loop
				 *   remounts the stage a little further down.  ⛔ And the verdict
				 *   will again be given by the MEASURED stride, not by a
				 *   computation on the width. */
				if (ZERO_COPY && !card_never_again && card_denied_w != 0
				    && stage_route == CAPTURE_ROUTE_MEMORY
				    && (fo.width != card_denied_w
				        || fo.height != card_denied_h)) {
					card_denied_w = 0;
					card_denied_h = 0;
					card_to_retry = true;
					registro_dice(LOG_CHILD,
					              "⭐ new canvas %ux%u: zero copy had been "
					              "denied for the previous canvas, and on this one it is "
					              "retried",
					              fo.width, fo.height);
				}

				/* 5. ⭐⭐ AND THE PARENT IS ANSWERED, as it is waiting for this
				 *    number: without it, it would have to GUESS from the frames
				 *    which request this size answers — and with two chained
				 *    requests it would guess wrong.  ⚠ It is sent even when
				 *    nobody had asked for anything (the stage drifting by
				 *    itself): it is a fact, and whoever receives it decides what
				 *    to do with it. */
				reply_canvas(canvas_intended_w, canvas_intended_h, canvas_w, canvas_h);
			}

			instant_us = frame_instant(&fo, now_monotonic_us());
			/* ⭐⭐ §6.2 — THE STAMP IS TAKEN HERE, at the instant of capture,
			 *     and nowhere else.  ⛔ Reading it after encoding would say
			 *     "the last input injected before SENDING", which is a higher
			 *     number: the latency link would measure a latency shorter
			 *     than the real one — **in our favour**, that is the direction
			 *     in which nobody errs by accident (`CODER.md` §1-bis, "the
			 *     boundary moves in the uncomfortable direction"). */
			/* ⛔ The number → codec map lives HERE and nowhere else: with two
			 *    codecs a `? :` was enough, with the third a nested `? :` would
			 *    say "AV1" of every number it does not know — and the symptom
			 *    would be an AV1 stream sent with label 3. */
			/* ⏳ §13: the pace counts from the last frame ENCODED. */
			pace_last_us = now_monotonic_us();
			/* ⛔ 15 Oct 2026 — a frame NOT encoded must not stay the
			 *    reference of the «unchanged» filter (`unchanged.h`): the
			 *    next copy of the same picture would be held back, and the
			 *    change it carries would never reach the client. */
			if (!encode_and_send(&fo, codec_from_number(requested_codec),
			                     requested_codec, NULL, NULL, instant_us, canvas_w,
			                     canvas_h, input_injected))
				capture_unchanged_forget(cat);
			/* ⛔⭐ THE RELEASE — and on the card's road this line is NOT a
			 *     clean-up: it is the cure of `LESSONS.md` §8.  Until it is
			 *     called, Mutter's buffer is ours; and it is called AFTER the
			 *     encoding, that is after the GPU has finished reading it
			 *     (`codificatore_comprimi_scheda` really waits before
			 *     returning).  ⚠ Moving it two lines up would bring back the
			 *     two alternating screens. */
			capture_stopped_free(&fo);

			/* ⛔ And if the card turned out not viable — encoder in software,
			 *    or a stride that cannot be imported — the PIXELS' ROUTE
			 *    changes.  ⚠ It is done HERE and not inside `encode_and_send`:
			 *    the hold is already released, and remounting with a buffer
			 *    still in hand would return a `pw_buffer` to a capture that is
			 *    gone.
			 *
			 * ⛔⛔⛔ AND SINCE 25 AUG 2026 **ONLY THE STREAM** IS REMOUNTED, not
			 *      the stage: the box above `remount_only_capture()` carries
			 *      the core and the stack.  In short — dismantling the stage
			 *      closed a **freshly born** EIS channel, and `ei_disconnect()`
			 *      killed the child with a SIGSEGV **before the first frame**,
			 *      for a window 1268 px wide.  ⚠ The dismantling stays as a
			 *      FALLBACK, for the only case in which the node cannot be taken
			 *      back. */
			if (card_to_abandon || card_to_retry) {
				stage_route = card_to_retry
				                       ? CAPTURE_ROUTE_CARD
				                       : CAPTURE_ROUTE_MEMORY;
				card_to_abandon = false;
				card_to_retry = false;
				if (remount_only_capture(mut, &cat, canvas_w, canvas_h))
					continue;
				unmount_stage(&mut, &cat);
				stage_wait_ms = STAGE_RETRY_MIN_MS;
				stage_retry_ms = log_now_ms() + stage_wait_ms;
				continue;
			}
		}
	}

	encoders_free();
	for (uint8_t c = 0; c < 3; c++) {
		free(kept[c]);
		kept[c] = NULL;
	}
	registro_dice(LOG_CHILD,
	              "the loop stops: %llu frames delivered (%llu keyframes), "
	              "%llu empty waits, %llu faults",
	              (unsigned long long)cycle_frames,
	              (unsigned long long)cycle_keys,
	              (unsigned long long)cycle_zero,
	              (unsigned long long)cycle_faults);

	/* ⛔⭐ AND BEFORE EVERYTHING ELSE WHAT WAS LEFT HELD DOWN IS RELEASED.
	 *
	 *     `RCP.md` §11 calls it "the rule with the highest damage/cost ratio
	 *     of the document", and here it bites in the worst way: the stage
	 *     outlives the client (I4), so a Ctrl left pressed **does not go away
	 *     with the connection** — it stays on the user's desktop, which at
	 *     reattach is found unusable without the two things being connected.
	 * ⚠ And it is done here too, not only at the end of each connection: this
	 *   is the last instant in which someone can still do it. */
	registro_dice(LOG_CHILD,
	              "the input channel closes: %u injected, %u refused "
	              "by the compositor, %u not producible with the layout (§7.3)",
	              (unsigned)input_injected, (unsigned)input_refused,
	              (unsigned)input_unproducible);
	/* ⚠ And the release is done by `unmount_stage`, which is the SAME
	 *   dismantling as the remount: two roads to dismantle the stage would
	 *   mean that one of the two, one day, will forget a piece. */
	unmount_stage(&mut, &cat);
	/* ⛔ And the audio is turned off BEFORE exiting, in the right order:
	 *    `audio_rule_child(0)` stops the capture and WAITS for the PipeWire
	 *    thread.  ⚠ Exiting with that thread still alive would mean letting it
	 *    write into the ring of a dying process — and the defect would show up
	 *    every now and then, at exit, which is the place where nobody looks. */
	audio_rule_child(0);
	if (snd) {
		sound_close(snd);
		snd = NULL;
	}
	/* ⭐ R1/R2: if the session is gone, the manager goes back to how it was */
	session_clear_out_handler("the child exits");
	registro_dice(LOG_CHILD, "the child of «%s» has dismantled the stage and is exiting",
	              user);
	_exit(0);
}
