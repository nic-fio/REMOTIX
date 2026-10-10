/*
 * figlio.c — one process per user, running as that user and holding the stage.
 *
 * The reasoning, the three differences from the helper and the invariants are
 * spelled out in `figlio.h`.  Here are the choices that only show in the code.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ THE MOST IMPORTANT CHOICE IN THIS FILE: `fork()` **AND THEN `exec()`**
 *
 * A `fork()` alone would have been enough to run the child as the user.  The
 * `exec` is done too for three reasons, and the first one decides on its own:
 *
 *   1. ⛔ **the parent's memory holds the server's private TLS key**
 *      (`certificati.c`), the ban table and the state of every other
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
#include "figlio.h"

/* ⛔ ONLY for the session cap (`RCP_TETTO_SESSIONI`, `rcp_tetto()`).  ⚠ The
 *    child does NOT speak RCP: it speaks to the parent over a `SOCK_SEQPACKET`.
 *    This include is the declaration of the link between two caps, not a
 *    dependency on the protocol. */
#include "rcp.h"
#include "registro.h"
/* ⭐ PHASE 17 T7: the PARENT's half asks whether a desktop is alive before
 *    `loginctl terminate-user` (logind and /proc, nothing of the stage). */
#include "ritrovo.h"

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
#include "appunti.h"
#include "audio.h"
#include "cattura.h"
#include "wlroots.h"
#include "vulkanvideo.h"
#include <drm_fourcc.h>
#include "sentinella.h"
#include "suono.h"
#include "codificatore.h"
#include "input.h"
#include "mutter.h"
#include "kwin.h"
#include "sessione.h"

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
 *     table is **allocated** on the cap in force (`rcp_tetto()`, which
 *     `--tetto-sessioni` moves at startup).  ⛔ The `MAX_FIGLI` that was here
 *     is gone and was not left beside it as a "maximum": it would have been a
 *     second number.  The value in force for THIS table is `f->tetto`, and it
 *     is read only once, in `figli_accendi()`. */

/* ⛔ How long a newborn child is given to say WHO IT IS.  Beyond that, it is
 * declared faulty and killed: a process running as a user that does not
 * answer is not a stage, it is a forgotten process.
 * ⚠ After the first "I am", there is NO deadline: that is invariant I4 — the
 *   stage outlives the detach, and a child that is silent because nobody is
 *   asking it anything is doing its job. */
#define SCADENZA_SONO_MS 15000

/* ⛔ §6.2 of `RCP.md`: a legal frame reaches 16 MiB.  The cap is here because
 * the bytes pass through here, and a lower cap of OURS would bite in place of
 * the protocol's one — the form of error the assembly has already paid for
 * with `WT_CODA_MAX` (`P2-6-montaggio.md` §5.6). */
#define FOTOGRAMMA_MAX (16u * 1024u * 1024u)

/* How much fits in one SEQPACKET message.  ⚠ It is not a protocol cap: it is
 * the piece into which a frame that would not fit in the socket is cut. */
#define PEZZO_MAX 32768u

#define FIGLIO_VERSIONE 1

enum {
	MSG_CHI_SEI = 1,      /* parent → child */
	MSG_SPEGNITI = 2,     /* parent → child */
	MSG_RIMANDA_PALCO = 3,/* parent → child */
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
	MSG_DISPOSIZIONE = 6, /* parent → child */
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
	 *     belongs to the compositor** (`STUDI.md` §gnome §10), and this process
	 *     is the one talking to the compositor; §7.4 is written by the parent.
	 *
	 * ⛔ `MSG_APPUNTI_OFFERTA` does NOT carry the text, and it is §7.4's
	 *    "announce first, then pull" applied on this side: the client's text
	 *    is requested when someone in the session really pastes.  ⚠ Someone
	 *    who copies a whole document on the phone does not make it cross the
	 *    socket until that moment comes — and most of the time it does not. */
	MSG_APPUNTI_OFFERTA = 8,  /* parent → child */
	/* ⛔ And this one does carry it, **in pieces**: it is the answer to a
	 *    request from the session, and the cap of §5.4 is 1 000 000 bytes —
	 *    thirty times `PEZZO_MAX`. */
	MSG_APPUNTI_DAL_CLIENT = 9, /* parent → child */
	MSG_SONO = 10,      /* child → parent */
	MSG_PALCO = 11,     /* child → parent */
	MSG_FOTOGRAMMA = 12,/* child → parent */
	/* ⭐⭐ PHASE 4 — THE CURSOR SHAPE, and it crosses the boundary in the
	 *     OPPOSITE direction to input.  ⛔ For the same reason: the cursor
	 *     metadata comes from PipeWire, that is in the child, and the channel
	 *     it must be sent on (`CURSORE_FORMA`, `RCP.md` §7.2) lives in the
	 *     parent.
	 * ⚠ And like the frame it goes IN PIECES: a 256x256 BGRA cursor is 262 144
	 *   bytes, eight times `PEZZO_MAX`. */
	MSG_CURSORE = 13,   /* child → parent */
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
	MSG_TELA = 14,      /* child → parent */
	/* ⭐ §7.6 — "the graphical session is over", and no client asked for it:
	 * the user chose "Log out…" from the desktop menu. */
	MSG_SESSIONE_FINITA = 15, /* child → parent */
	/* ⭐⭐ PHASE 7 — AN ALREADY ENCODED AUDIO BLOCK, ready for the datagram.
	 *
	 * ⛔ It does NOT go in pieces like the frame and the cursor, and it is not
	 *    a simplification: a block that does not fit in a datagram **cannot be
	 *    sent at all** (`RCP.md` §6.3, "one datagram, one block"), so a block
	 *    larger than `PEZZO_MAX` would already be a defect upstream.
	 *    ⚠ The largest RCP/1 provides for is PCM: 960 bytes.
	 *
	 * ⛔ And if the socket is full the block IS DROPPED instead of waiting:
	 *    §6.3 forbids retransmission, and a child that blocked on writing would
	 *    stop the DESKTOP CAPTURE — late audio would cost the frames. */
	MSG_BLOCCO = 16, /* child → parent */
	/* ⭐⭐ PHASE 7 — "THE SESSION HAS COPIED THIS TEXT", and it goes **in
	 *     pieces** like the frame and the cursor.
	 *
	 * ⛔ It arrives ALREADY READ, and it is not a convenience: the announcement
	 *    of §7.4 carries `u32 lunghezza`, and nobody knows how long a text is
	 *    without having read it.  ⇒ The "announce first, then pull" lives on
	 *    the WIRE, where it is needed; on this side the text is already there.
	 * ⛔ And it arrives already validated as UTF-8, already without zeros in
	 *    the middle and already within the cap: those three checks are in
	 *    `appunti.c`, where the text still exists whole and where it is known
	 *    WHICH of the three bit. */
	MSG_APPUNTI_DALLA_SESSIONE = 17, /* child → parent */
	/* ⭐⭐ "SOMEONE IN THE SESSION IS PASTING" — and the parent MUST answer,
	 *     even empty-handed: a `SelectionTransfer` with no answer leaves the
	 *     pasting application hanging indefinitely, and the symptom is "the
	 *     desktop has frozen" (`src/appunti.h`). */
	MSG_APPUNTI_VUOLE = 18 /* child → parent */
};

struct testa {
	uint8_t magia[4]; /* 'F','I','G','1' */
	uint16_t tipo;
	uint16_t versione;
	uint64_t matricola;
	/* ⛔ Who the SENDER believes the child is.  It is not proof of anything —
	 *    the proof is written by the kernel — and it is here so that a mismatch
	 *    between what one believes and what the kernel says shows **at once**,
	 *    instead of becoming pixels delivered to the wrong person. */
	uint32_t uid_dichiarato;
	uint32_t byte; /* body bytes after this structure */
};

struct corpo_sono {
	uint32_t uid, euid, suid;
	uint32_t gid, egid, sgid;
	uint32_t pid, ppid;
	uint32_t descrittori;   /* how many remain open after `close_range` */
	uint32_t runtime_c_e;   /* the runtime folder exists and is its own */
	uint32_t socket_bus_c_e;/* the session bus socket exists */
	char utente[64];
	char runtime[160];
};

struct corpo_palco {
	uint32_t bus_aperto;      /* the CONNECTION to the bus succeeded */
	uint32_t stato_sessione;  /* SessioneStato, 0 = SANA */
	uint32_t presa;           /* CatturaPresa */
	uint32_t monitor_prima, monitor_dopo;
	uint32_t larghezza, altezza, stride, bit;
	uint32_t flussi;          /* how many codecs delivered */
	char monitor[64];
	char guasto[224];
};

/* ⛔⭐ The stage's answer to the canvas request.  ⚠ `avuta_l == 0` means
 *     "I did not make it", and it is NOT a size: it is the other face of the
 *     zero of `CODER.md` §3.10, declared instead of inferred from silence. */
struct corpo_tela {
	uint32_t voluta_l, voluta_a;
	uint32_t avuta_l, avuta_a;
	/* ⭐⭐ "NOT YET" — 16 Aug 2026, and it is not a third number: it is a third
	 *     FACT.  `avuta = 0x0` means "I did not make it"; silence meant "I am
	 *     still trying", ⛔ and the parent INFERRED it — that is, it did not
	 *     know it.  `LEZIONI.md` §7.5: an inference in place of a message is a
	 *     defect waiting to happen.
	 *
	 * ⇒ With this bit the parent POSTPONES the deadline of §7.1 instead of
	 *   answering `NON_ORA` to a question that is about to get a real answer. */
	uint32_t attendi;
};

/* ⛔ What the parent asks of the stage.  ⚠ `codec` at **0** means "stop
 *    capturing": it is not an implicit sentinel, it is the value §4.3/§6.2
 *    reserve for "no codec negotiated", and here it means the same thing —
 *    nobody is watching. */
struct corpo_video {
	uint8_t codec;  /* 1 = HEVC, 2 = AV1, 0 = off */
	uint8_t chiave; /* ⛔ §5.2: the next one MUST be a keyframe */
	/* ⛔⭐⭐ THE NEGOTIATED DEPTH — 17 Aug 2026, and this field is the cure for
	 *      a measured defect, not a convenience addition.
	 *
	 *      Until tonight the codec crossed this boundary and the depth did
	 *      NOT: the child wrote `r.profondita = 10` by hand, for every codec.
	 *      ⇒ The stream came out at **10 bits while `ECCOMI` declared 8**
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
	uint8_t profondita;
	/* ⛔⭐⭐ THE LEVEL REQUESTED BY THE CLIENT — 23 Aug 2026, and this field was
	 *      the `riempi` byte, kept free on purpose and named in TWO boxes
	 *      (`rcp.c` §4.3 and "LEVEL PRODUCED" further down) as the place where
	 *      the level would pass the day it was needed.
	 *
	 *      It is needed, and it is MEASURED: `[M]` 23 Aug 2026, canvas
	 *      3840x2160, H.264 — the client declares `video.livello=5.1` and the
	 *      server produces a level **5.2** stream.  `RCP.md` §4.3 line 701 is
	 *      a MUST, and the symptom of an exceeded level is NOT an error: it is
	 *      the browser's decoder refusing the configuration — "nothing shows"
	 *      without a line saying why.
	 *
	 * ⚠ In TENTHS, the alphabet of §4.3: `5.1` ⇒ **51**.  Whoever opens the
	 *   encoder converts it back codec by codec (H.264 as is, HEVC times
	 *   three): the translation lives in `codificatore.c` and nowhere else.
	 * ⛔ `0` = the client did not declare it — §4.3 does not require it — and it
	 *   means NO CEILING, not "low": the receiver does not invent one, which is
	 *   the same rule written above for `profondita`. */
	uint8_t livello_x10;
};

/* ⛔ What the parent asks of the desktop.  The actions are those of `RCP.md`
 *    §7.3 and the fields have its types — ⚠ but here they travel already
 *    VALIDATED: `rcp.c` has done its job, and this boundary does not redo it.
 *
 * ⭐ `id` is there because it is the only thing that makes the `input` field of
 *    frames (§6.2) honest: without it, the child would know it had injected
 *    **something** and not **which**. */
struct corpo_input {
	uint32_t id;       /* §7.3: grows by at least one over the whole channel */
	uint8_t azione;    /* FIGLI_INPUT_* of `figlio.h` */
	uint8_t premuto;   /* 1 pressed, 0 released */
	uint16_t codice;   /* evdev: BTN_LEFT = 0x110, KEY_A = 30 */
	int32_t a, b;      /* pointer x/y · wheel axes · letter in `a` */
};

/* ⭐ §5-bis.7: the name of an XKB layout — `it`, `de(neo)`.  ⚠ 64 bytes
 *    plus the NUL, which is the cap `RCP.md` §4.5 puts on the string: the
 *    envelope is fixed-size so that the child does not have to trust a
 *    length that comes to it from the socket. */
struct corpo_disposizione {
	char nome[65];
};

/* ⛔ The cursor shape that crosses the boundary.  ⚠ The limits of `RCP.md`
 *    §5.5 and §7.2 have already been enforced by `cursore.c`, on the other
 *    side of the pipe: they are not rechecked here — ⛔ except what is needed
 *    not to trust a sender, which in the parent is a different thing from
 *    trusting a module. */
struct corpo_cursore {
	uint16_t larghezza, altezza; /* 0x0 = hidden (§5.5) */
	int16_t attivo_x, attivo_y;
	uint32_t totale;  /* bytes of the whole image: w x h x 4 */
	uint32_t offset;
	uint32_t pezzo;
};

/* ⛔ What the parent asks of the audio.  `codec` are the numbers of `RCP.md`
 *    §6.3 — 1 = Opus, 2 = PCM — and ⚠ **not** those of §6.2: there 1 is HEVC.
 *    `0` = "off": nobody is listening, and the capture stops while the sink
 *    stays (invariant I4, like the stage). */
struct corpo_audio {
	uint8_t codec;
	uint8_t riempi[3];
};

/* An already encoded block.  `istante_us` is the child's monotonic clock, of
 * the FIRST sample of the block (§6.3) — ⛔ and the child sets it for the same
 * reason it sets `input` in frames: it is the only one that knows when the
 * samples were really taken. */
struct corpo_blocco {
	uint8_t codec;
	uint8_t riempi[3];
	uint32_t byte;
	uint64_t istante_us;
};

/* ⛔ THE CLIPBOARD TEXT, and it goes in pieces in BOTH directions.
 *
 * ⚠ One structure for both directions, and it is not laziness: the two
 *   messages carry the same object — a text up to 1 000 000 bytes long — and
 *   `serial` is the only difference.  ⛔ In the child → parent direction it is
 *   **0** and means nothing: the session copied, it did not ask.
 *
 * ⛔ And `totale` is NOT redundant with respect to `pezzo`: the receiver
 *    allocates on the first piece and refuses out-of-order pieces, exactly as
 *    for the frame — stitching a hole would mean guessing what was missing,
 *    and a text with a guessed hole pasted into a terminal is worse than a
 *    missing text (§5.4, in its own words). */
struct corpo_appunti {
	uint32_t serial; /* parent → child: Mutter's request.  Otherwise 0 */
	uint32_t totale; /* bytes of the whole text, final zero EXCLUDED */
	uint32_t offset;
	uint32_t pezzo;
	/* ⛔ "I don't have it", and it must be said with a field instead of with
	 *    `totale = 0`.  An empty text is a LEGITIMATE fact — the clipboard
	 *    emptied — and "I don't have what you asked me" is another fact:
	 *    squashing them onto the same value is the common face of "empty" and
	 *    "forbidden" that `LEZIONI.md` §1.9 forbids.  ⚠ And the two lead to two
	 *    different calls towards Mutter. */
	uint8_t niente;
	uint8_t riempi[3];
};

struct corpo_fotogramma {
	uint8_t codec; /* 1 = HEVC, 2 = AV1 — the same numbers as §4.3/§6.2 */
	uint8_t chiave;
	uint16_t riempi;
	uint32_t larghezza, altezza;
	uint64_t istante_us;
	uint32_t totale; /* bytes of the whole frame */
	uint32_t offset; /* where this piece goes */
	uint32_t pezzo;  /* how many bytes in this piece */
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
#define BUSTA_MAX (sizeof(struct testa) + sizeof(struct corpo_fotogramma) + PEZZO_MAX)
_Static_assert(sizeof(struct corpo_cursore) <= sizeof(struct corpo_fotogramma),
               "the envelope is sized on the frame: the cursor must fit in it");
_Static_assert(sizeof(struct corpo_appunti) <= sizeof(struct corpo_fotogramma),
               "the envelope is sized on the frame: the clipboard must fit in it");

/* ========================================================================== */
/* THE PARENT                                                                  */

struct figlio {
	bool usato;
	char utente[64];
	/* ⭐ PHASE 17 T6: the address of the client that caused it to be born, for
	 *    the session's `PAM_RHOST` (like sshd); "" ⇒ "remotix". */
	char rhost[64];
	uid_t uid;
	gid_t gid;
	pid_t pid;
	int fd;
	uint64_t matricola;
	uint64_t nato_ms;
	uint64_t ultimo_ricontrollo_ms;
	bool si_e_presentato;
	/* ⛔⭐ "I told it to leave" and "it has left" are two different facts,
	 *     and keeping only one of them is the defect this bench found on the
	 *     first run (12 Aug 2026, case `muore`).  See the box above
	 *     `figlio_congeda()`. */
	bool uscendo;
	uint64_t congedato_ms;
	/* The incoming frame, one piece at a time. */
	uint8_t *monta;
	size_t monta_totale, monta_avuti;
	uint8_t monta_codec, monta_chiave;
	uint32_t monta_l, monta_a;
	uint64_t monta_istante;
	uint32_t monta_input; /* §6.2, and the child STAMPS it: see `corpo_fotogramma` */
	/* ⭐ The CURSOR assembly is separate from the frame's, and it is not a
	 *    convenience: the two arrive **interleaved** on the same socket, and a
	 *    single assembly would turn every shape change into a dropped frame
	 *    (and vice versa).  ⛔ It is the out-of-order pieces trap seen from
	 *    above: it is not the sender that is wrong, it is the receiver that
	 *    does not have two tables. */
	uint8_t *cur_monta;
	size_t cur_totale, cur_avuti;
	uint16_t cur_l, cur_a;
	int16_t cur_ax, cur_ay;
	/* ⛔ The count of frames arrived from this child.  ⚠ It is here and not in
	 *    a module variable because it is PER CHILD: summed over two users it
	 *    would say the stage works even when only one of them works — two
	 *    measures under the same label. */
	uint64_t fotogrammi_avuti, byte_avuti, chiavi_avute;
	uint64_t detto_conto_ms;
	/* ⛔ What the parent has already asked of this stage: kept so as not to
	 *    repeat the same command on every round of `poll`. */
	uint8_t video_codec_chiesto;
	/* ⛔ And the depth with it: see `corpo_video`.  ⚠ `0` = never asked. */
	uint8_t video_prof_chiesta;
	/* ⛔ And the LEVEL with them (§4.3, 23 Aug 2026), for the same reason:
	 *    it belongs to the SESSION, it changes from client to client, and a
	 *    second client declaring 4.1 where the first had 5.1 is "something new
	 *    to say" even with codec and depth unchanged.  ⚠ `0` = never asked. */
	uint8_t video_liv_chiesto;
	/* ⛔ The last audio codec asked of this child, so as not to repeat the
	 *    same request on every beat — and to write the log line only when the
	 *    fact CHANGES.  ⚠ `0` = off, and it is the initial state of every
	 *    child: nobody listens until someone attaches. */
	uint8_t audio_codec_chiesto;
	/* ⭐ PHASE 7 — the THIRD assembly table, and the reason is the one written
	 *    above `cur_monta`: frames, cursors and clipboard arrive
	 *    **interleaved** on the same socket, and with only two tables every
	 *    copied text would become a dropped frame.  ⚠ One table per type, and
	 *    the count adds up whatever arrives first. */
	uint8_t *app_monta;
	size_t app_totale, app_avuti;
};

struct figli {
	/* ⛔ Allocated in `figli_accendi()` with `f->tetto` slots, freed in
	 *    `figli_spegni()`.  ⚠ All the `f->v[i]` stay written as they were:
	 *    only the loop LIMITS change, going from a `#define` to `f->tetto`. */
	struct figlio *v;
	int tetto;
	uint64_t prossima_matricola;
	uint32_t tela_l, tela_a;
	char dir_rilievo[256];
	bool c_e_rilievo;
	/* ⭐ PHASE 9 — what every child will have to repeat to itself after the
	 *    `execve`, because the encoder is over there.  ⚠ It is not USED here:
	 *    it is copied into the child's command line (`diventa_ed_esegui()`). */
	bool fase9_qualita_risale;
	uint32_t fase9_tetto_banda_mbit;
	/* ⭐ The THIRD, 24 Aug 2026, and it is born ON: an all-zero audio block
	 *    does not become a datagram.  ⚠ It is passed NEGATED in the child's
	 *    `argv` (`--niente-audio-silenzio`), because what is written at the end
	 *    is the EXCEPTION to the default, not the default. */
	bool fase9_audio_silenzio;
	char percorso_mio[512]; /* /proc/self/exe resolved, for the `exec` */
	FiglioSessioneFinita su_sessione_finita;
	void *ctx_sessione_finita;
	FiglioTelaAttendi su_tela_attendi;
	void *ctx_tela_attendi;
	/* ⭐ PHASE 7 — the audio blocks.  ⚠ It has a context of ITS OWN and does
	 *    not use `ctx` like `deposita`/`congeda`/`cursore`: those are hooked
	 *    by `main.c` as a block, this one is hooked by whoever owns the audio
	 *    channel, and tying them together would mean forcing audio on wherever
	 *    there is video. */
	FiglioBlocco su_blocco;
	void *ctx_blocco;
	/* ⭐ PHASE 7 — the clipboard.  ⚠ Context of ITS OWN like the blocks', and
	 *    for the same reason: whoever owns the clipboard channel is not the
	 *    one hooking the video, and tying them would mean forcing the
	 *    clipboard on wherever there is video.
	 * ⛔ The two hooks are attached together or not at all (`figlio.h`): one
	 *    that could receive the session's text and could not serve whoever
	 *    pastes would leave the pasting application hanging. */
	FiglioAppuntiTesto su_appunti_testo;
	FiglioAppuntiRichiesta su_appunti_richiesta;
	void *ctx_appunti;
	FiglioDeposito deposita;
	FiglioCongedo congeda;
	FiglioCursore cursore;
	FiglioTela tela;
	void *ctx;
};

static void magia_scrivi(struct testa *t)
{
	t->magia[0] = 'F';
	t->magia[1] = 'I';
	t->magia[2] = 'G';
	t->magia[3] = '1';
}

static bool magia_giusta(const struct testa *t)
{
	return t->magia[0] == 'F' && t->magia[1] == 'I' && t->magia[2] == 'G'
	       && t->magia[3] == '1' && t->versione == FIGLIO_VERSIONE;
}

/* ⛔ Reads a message AND the credentials the KERNEL attached to it.
 *
 * ⚠ `credenziali` comes out true only if the message really carried some: a
 *   message **without** credentials is not a message with the right
 *   credentials — "empty" and "forbidden" look the same (`LEZIONI.md` §1.9),
 *   and here the common face would cost the isolation between users. */
static ssize_t ricevi_con_credenziali(int fd, void *buf, size_t cap,
                                      struct ucred *chi, bool *credenziali)
{
	struct msghdr m;
	struct iovec io;
	union {
		struct cmsghdr allinea;
		char spazio[CMSG_SPACE(sizeof(struct ucred))];
	} controllo;
	struct cmsghdr *c;
	ssize_t letti;

	*credenziali = false;
	memset(&m, 0, sizeof m);
	memset(&controllo, 0, sizeof controllo);
	io.iov_base = buf;
	io.iov_len = cap;
	m.msg_iov = &io;
	m.msg_iovlen = 1;
	m.msg_control = controllo.spazio;
	m.msg_controllen = sizeof controllo.spazio;

	letti = recvmsg(fd, &m, 0);
	if (letti <= 0)
		return letti;

	for (c = CMSG_FIRSTHDR(&m); c; c = CMSG_NXTHDR(&m, c)) {
		if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_CREDENTIALS
		    && c->cmsg_len == CMSG_LEN(sizeof(struct ucred))) {
			memcpy(chi, CMSG_DATA(c), sizeof *chi);
			*credenziali = true;
		}
	}
	/* ⚠ A message truncated by the kernel (`MSG_TRUNC`) is a message that is
	 *   not what it says it is: it is dropped.  With SEQPACKET this happens
	 *   only if the sender wrote more than our buffer, that is if it is not
	 *   our code or if the two sides are not the same version. */
	if (m.msg_flags & MSG_TRUNC)
		return -2;
	return letti;
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
 *     admit another;
 *   · the user's name **still today** resolves to that uid.  ⚠ This is the
 *     only one of the five that can change while the child is alive (NSS,
 *     `/etc/passwd` rewritten, a domain answering differently): if it
 *     changes, the link between the RCP session and the child can no longer
 *     be proven, and a link that cannot be proven is a no.
 *
 * ⛔ There is no path that delivers a byte to someone who does not pass here. */
static bool credenziali_combaciano(const struct figlio *g, const struct testa *t,
                                   bool c_e, const struct ucred *chi,
                                   char *perche_no, size_t cap_perche)
{
	struct passwd pw, *ris = NULL;
	char scorta[1024];

	if (!c_e) {
		snprintf(perche_no, cap_perche,
		         "the kernel did not attach the credentials to the message");
		return false;
	}
	if (chi->pid != g->pid) {
		snprintf(perche_no, cap_perche,
		         "written by pid %ld, and the child of «%s» is pid %ld",
		         (long)chi->pid, g->utente, (long)g->pid);
		return false;
	}
	if (chi->uid != g->uid || chi->gid != g->gid) {
		snprintf(perche_no, cap_perche,
		         "the kernel says uid %ld gid %ld, and «%s» is uid %ld gid %ld",
		         (long)chi->uid, (long)chi->gid, g->utente, (long)g->uid,
		         (long)g->gid);
		return false;
	}
	if (t->matricola != g->matricola) {
		snprintf(perche_no, cap_perche, "serial %llu instead of %llu",
		         (unsigned long long)t->matricola,
		         (unsigned long long)g->matricola);
		return false;
	}
	if (t->uid_dichiarato != (uint32_t)g->uid) {
		snprintf(perche_no, cap_perche,
		         "the message declares uid %lu and the child is uid %ld",
		         (unsigned long)t->uid_dichiarato, (long)g->uid);
		return false;
	}
	if (getpwnam_r(g->utente, &pw, scorta, sizeof scorta, &ris) != 0 || !ris) {
		snprintf(perche_no, cap_perche,
		         "the name «%s» no longer resolves to any user: the "
		         "link can no longer be proven",
		         g->utente);
		return false;
	}
	if (ris->pw_uid != g->uid) {
		snprintf(perche_no, cap_perche,
		         "«%s» is now uid %ld, and the child is uid %ld: the name and "
		         "the uid have come apart",
		         g->utente, (long)ris->pw_uid, (long)g->uid);
		return false;
	}
	return true;
}

/* ⛔⭐ THE FAREWELL IS NOT THE RELEASE, AND KEEPING THEM TOGETHER IS A DEFECT —
 *     found by the bench `02-figlio-prova.py --caso muore` on the FIRST run, on
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
 *     `figlio_congeda()`  closes the socket, asks the child to leave, and
 *                         leaves the slot occupied **with the pid inside**;
 *     the reaping         in `figli_muovi()`, `waitpid(WNOHANG)`: when the
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
static const char *perche_uscito(int codice)
{
	switch (codice) {
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

/* The second half: the kernel has confirmed, the slot is freed. */
static void figlio_libera(struct figli *f, struct figlio *g, const char *perche)
{
	if (!g->usato)
		return;
	registro_dice(REG_FIGLIO,
	              "⭐ the child of «%s» (uid %ld) has been REAPED: %s.  From "
	              "now on \"dead\" and \"alive\" no longer have the same face in "
	              "/proc, and the slot is free again",
	              g->utente, (long)g->uid, perche);
	if (g->fd >= 0)
		close(g->fd);
	free(g->monta);
	/* ⛔ And the deposit is released from here too, for the paths that do not
	 *    go through the farewell (a child that died without anyone sending it
	 *    away).  ⚠ `congeda_figlio()` in `main.c` does nothing if the deposit
	 *    was not its own: calling it twice is not a defect, never calling it is. */
	if (f->congeda)
		f->congeda(f->ctx, g->utente, g->uid);
	memset(g, 0, sizeof *g);
	g->fd = -1;
}

static void figlio_congeda(struct figli *f, struct figlio *g, const char *perche)
{
	if (!g->usato || g->uscendo)
		return;
	registro_dice(REG_FIGLIO,
	              "the child of «%s» (uid %ld, pid %ld, serial %llu) is "
	              "leaving: %s — waiting for the kernel to confirm it before "
	              "freeing the slot",
	              g->utente, (long)g->uid, (long)g->pid,
	              (unsigned long long)g->matricola, perche);
	g->uscendo = true;
	g->congedato_ms = registro_ora_ms();
	if (g->fd >= 0) {
		close(g->fd);
		g->fd = -1;
	}
	/* ⛔ The closed socket is already a farewell — the child reads EOF and
	 *    exits — but "it would be enough" is not "I did it": the signal makes
	 *    the shutdown a fact instead of a race. */
	if (g->pid > 0)
		kill(g->pid, SIGTERM);
	/* ⛔ And the deposit is released AT ONCE, not at reaping: from this instant
	 *    there is no stage behind those pixels any more, and keeping them would
	 *    be showing the image of a user whose process is gone. */
	if (f->congeda)
		f->congeda(f->ctx, g->utente, g->uid);
}

static struct figlio *cerca(struct figli *f, const char *utente)
{
	for (int i = 0; i < f->tetto; i++)
		if (f->v[i].usato && strcmp(f->v[i].utente, utente) == 0)
			return &f->v[i];
	return NULL;
}

/* ⭐ The trigger reaches the PARENT and must be passed on to the children: see
 *    the box inside `figli_muovi()`.  ⛔ Here it is only noted — the work is
 *    done in the loop, not inside a signal handler. */
static volatile sig_atomic_t scatto_da_inoltrare = 0;

static void scatto_inoltro_segnale(int quale)
{
	scatto_da_inoltrare = (quale == SIGUSR2) ? 2 : 1;
}

figli *figli_accendi(uint32_t tela_l, uint32_t tela_a, const char *dir_rilievo,
                     FiglioDeposito deposita, FiglioCongedo congeda,
                     FiglioCursore cursore, FiglioTela tela, void *ctx)
{
	figli *f = (figli *)calloc(1, sizeof *f);
	ssize_t n;

	if (!f)
		return NULL;
	/* ⛔ The cap is read HERE, only once: `--tetto-sessioni` has already moved
	 *    it (it is parsed before the table exists), and from here on the
	 *    number in force for this table is `f->tetto` — reading it again later
	 *    would mean two sizes for the same array. */
	f->tetto = rcp_tetto();
	f->v = (struct figlio *)calloc((size_t)f->tetto, sizeof *f->v);
	if (!f->v) {
		free(f);
		return NULL;
	}
	for (int i = 0; i < f->tetto; i++)
		f->v[i].fd = -1;
	f->prossima_matricola = 1;
	/* ⭐ The on-demand trigger: the box is inside `figli_muovi()`. */
	signal(SIGUSR1, scatto_inoltro_segnale);
	signal(SIGUSR2, scatto_inoltro_segnale);
	f->tela_l = tela_l;
	f->tela_a = tela_a;
	f->deposita = deposita;
	f->congeda = congeda;
	f->cursore = cursore;
	f->tela = tela;
	f->ctx = ctx;
	if (dir_rilievo && dir_rilievo[0]) {
		snprintf(f->dir_rilievo, sizeof f->dir_rilievo, "%s", dir_rilievo);
		f->c_e_rilievo = true;
	}

	/* ⛔ The path of the binary is ASKED OF THE KERNEL, not inferred from
	 *    `argv[0]`: `argv[0]` is chosen by whoever launches, and an `exec` on a
	 *    path chosen by whoever launches would be a way to run as the user a
	 *    program that is not this one. */
	n = readlink("/proc/self/exe", f->percorso_mio, sizeof f->percorso_mio - 1);
	if (n <= 0) {
		registro_dice(REG_FIGLIO,
		              "⛔ I do not know which binary I am running (/proc/self/exe: "
		              "%s): NO child can be born, and every admitted user "
		              "will stay without a stage (invariant I3: failure is a "
		              "no, not a maybe)",
		              strerror(errno));
		free(f);
		return NULL;
	}
	f->percorso_mio[n] = 0;
	if (strstr(f->percorso_mio, " (deleted)")) {
		registro_dice(REG_FIGLIO,
		              "⛔ the running binary has been deleted or "
		              "replaced underfoot («%s»): I am NOT spawning children, "
		              "because I cannot prove which program would run "
		              "as the user",
		              f->percorso_mio);
		free(f->v);
		free(f);
		return NULL;
	}
	registro_dice(REG_FIGLIO,
	              "⭐ children table on: up to %d, one per user (I2), "
	              "canvas %ux%u, binary «%s»",
	              f->tetto, tela_l, tela_a, f->percorso_mio);
	return f;
}

/* ⭐⭐ The box is in `figlio.h`: here it is only noted, and whoever has no
 *     children table (`figli_accendi()` failed) does not break. */
void figli_fase9(figli *f, bool qualita_risale, uint32_t tetto_banda_mbit,
                 bool audio_silenzio)
{
	if (!f)
		return;
	f->fase9_qualita_risale = qualita_risale;
	f->fase9_tetto_banda_mbit = tetto_banda_mbit;
	f->fase9_audio_silenzio = audio_silenzio;
	/* ⛔ AND THIS LINE IS NOT THE DECLARATION OF THE VALUE IN FORCE — it is the
	 *    opposite: it says what the parent has committed to PASS.  The value
	 *    in force is written by `codificatore.c` when each encoder opens,
	 *    inside the child.  ⚠ The two lines are read as a pair: if this one
	 *    says "on" and that one says "off", the option was lost in the
	 *    parent → child hand-over, and it is not the cure that does not work. */
	registro_dice(REG_FIGLIO,
	              "⭐ PHASE 9, what the parent WILL PASS to every child on its "
	              "command line: quality climb-back %s · bandwidth ceiling "
	              "%s.  ⚠ The value IN FORCE is written by the child, line "
	              "«encoder OPENED»: if that says something else, the "
	              "hand-over was lost",
	              qualita_risale ? "ON (--qualita-risale)"
	                             : "off (I6, --qualita-risale absent)",
	              tetto_banda_mbit ? "ON" : "off (I6, floor 0)");
	/* ⛔⭐⭐ AND THE THIRD HAS A LINE OF ITS OWN, because it is the only one of
	 *      the three born ON — 24 Aug 2026, the user's decision.  ⚠ It must be
	 *      written even when on: it is the line from which a bench reads the
	 *      state of audio silence **without opening a session**, and the other
	 *      two lines of the triple (the child declaring it RECEIVED it, and
	 *      `audio.c` declaring the value IN FORCE) only arrive with the first
	 *      encoder. */
	registro_dice(REG_FIGLIO,
	              "⭐ PHASE 9, the audio silence the parent WILL PASS to every "
	              "child: %s.  ⚠ `[M]` 09-b84: 102.1 times less traffic on a "
	              "still screen (557.6 → 5.5 kbit/s), 1 248 blocks silenced out of "
	              "1 248; the price is +2 «missed» out of 5 000 at the client",
	              audio_silenzio
	                  ? "ON, and it is the DEFAULT since 24 Aug 2026 "
	                    "(the user's decision) — turned off with "
	                    "`--niente-audio-silenzio`"
	                  : "⛔ turned OFF by hand (`--niente-audio-silenzio`): silence "
	                    "is sent too, that is the product until 23 Aug "
	                    "2026.  ⚠ And it is NOT the default");
	if (tetto_banda_mbit)
		registro_dice(REG_FIGLIO,
		              "⭐ PHASE 9, the bandwidth ceiling: floor %u Mbit/s "
		              "(--tetto-banda-mbit) — wire, working point and reservoir "
		              "are derived over there, and codificatore.c writes them",
		              tetto_banda_mbit);
}

/*
 * ⛔ The PAM conversation for opening the session: it must NOT ask anything.
 *    `pam_open_session` asks no questions — and if it did, answering at
 *    random would be worse than failing (`CODER.md` §3.9: failure is
 *    declared).
 */
static int conversazione_muta_figlio(int n, const struct pam_message **m,
                                     struct pam_response **r, void *dati)
{
	(void)n;
	(void)m;
	(void)dati;
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
static void livello_selinux_come_sshd(const char *utente)
{
	void *l = dlopen("libselinux.so.1", RTLD_NOW | RTLD_LOCAL);
	if (!l)
		return;
	int (*abilitato)(void) = (int (*)(void))dlsym(l, "is_selinux_enabled");
	int (*leggi)(char **) = (int (*)(char **))dlsym(l, "getexeccon");
	int (*scrivi)(const char *) = (int (*)(const char *))dlsym(l, "setexeccon");
	int (*mappa)(const char *, char **, char **) =
		(int (*)(const char *, char **, char **))dlsym(l, "getseuserbyname");
	int (*valido)(const char *) =
		(int (*)(const char *))dlsym(l, "security_check_context");
	void (*libera)(char *) = (void (*)(char *))dlsym(l, "freecon");
	char *esec = NULL, *seuser = NULL, *livello = NULL;

	if (!abilitato || !leggi || !scrivi || !mappa || !valido || !libera ||
	    abilitato() != 1)
		goto fine;
	if (leggi(&esec) != 0 || !esec)
		goto fine; /* pam_selinux chose nothing: nothing is invented */
	if (mappa(utente, &seuser, &livello) != 0 || !livello || !livello[0])
		goto fine;
	{
		/* user:role:type:level — the level may contain ":" */
		const char *p = esec;
		for (int i = 0; i < 3 && p; i++) {
			p = strchr(p, ':');
			if (p)
				p++;
		}
		if (!p || strcmp(p, livello) == 0)
			goto fine; /* no level, or already the right one */
		char nuovo[512];
		int n = snprintf(nuovo, sizeof nuovo, "%.*s%s",
		                 (int)(p - esec), esec, livello);
		if (n <= 0 || (size_t)n >= sizeof nuovo || valido(nuovo) != 0) {
			fprintf(stderr,
			        "figlio: ⚠ SELinux: the desktop of «%s» is born «%s»; "
			        "the level of the login mapping («%s») does not make a "
			        "valid context — left as is\n",
			        utente, esec, livello);
			goto fine;
		}
		if (scrivi(nuovo) == 0)
			fprintf(stderr,
			        "figlio: ⭐ SELinux: the desktop of «%s» is born «%s» "
			        "as with ssh (pam_selinux had given «%s»: remotix_t "
			        "is not in the policy's stock contexts)\n",
			        utente, nuovo, esec);
		else
			fprintf(stderr,
			        "figlio: ⚠ SELinux: setexeccon(«%s») refused (%s): "
			        "the desktop is born «%s»\n",
			        nuovo, strerror(errno), esec);
	}
fine:
	if (esec && libera)
		libera(esec);
	free(seuser);
	free(livello);
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
static void diventa_ed_esegui(const struct figli *f, const struct figlio *g,
                              int socket_figlio, const struct passwd *pw,
                              const gid_t *gruppi, int ngruppi)
{
	char a_utente[80], a_uid[32], a_gid[32], a_l[32], a_a[32], a_matr[40];
	char a_tetto[32];
	char e_home[512], e_user[96], e_log[96], e_path[128], e_runtime[160],
		e_bus[224], e_shell[16];
	/* ⚠ Eighteen: the nine fixed ones, the NULL, and the EIGHT optional words
	 *   at the end — `--parlantina`, `--journal`, `--qualita-risale`,
	 *   `--tetto-banda-mbit` and its number, `--niente-audio-silenzio`, and
	 *   ⭐ phase 19 `--codifica` with its value.  They are added only if the
	 *   parent has them (see below).  ⛔ The count is redone for every new
	 *   word: an `argv[]` that is too short does not give an error, it writes
	 *   past the end of the stack. */
	char *argv[18];
	/* ⚠ 16 and not 9: to the seven we compose ourselves are added those that
	 *   `pam_systemd` puts in the session's environment — `XDG_SESSION_ID`
	 *   first, which is what Mutter was missing. */
	char *envp[16];
	char **ambiente_pam = NULL;
	int na = 0, ne = 0;
	uid_t r, e, s;
	gid_t rg, eg, sg;

	/* 1. the socket in the agreed place (fd 3), and without CLOEXEC: it is the
	 *    only thing that must cross the `exec`. */
	if (socket_figlio != 3) {
		if (dup2(socket_figlio, 3) < 0)
			_exit(30);
		close(socket_figlio);
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
	 *    mandate".  ⭐ At phase 5 that mandate **is this one**: `PIANO.md`
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
	 *     seat is headless **by construction**, which is what `DECISIONI.md`
	 *     §4.3-bis has asked for since August and what until today we had by
	 *     accident.
	 *
	 * ⚠ And `PAM_RHOST`: logind marks the session `Remote=yes`.  ⭐ It pays back
	 *   twice — it is the second belt of the guardian of §5.1 (`sentinella.c`
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
		struct pam_conv conv_muta = { conversazione_muta_figlio, NULL };
		pam_handle_t *pam = NULL;
		int rv;

		rv = pam_start("remotix", pw->pw_name, &conv_muta, &pam);
		if (rv != PAM_SUCCESS) {
			fprintf(stderr, "figlio: ⛔ pam_start: %s\n",
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
			             g->rhost[0] ? g->rhost : "remotix");
			pam_set_item(pam, PAM_TTY, "remotix");

			rv = pam_open_session(pam, PAM_SILENT);
			if (rv != PAM_SUCCESS) {
				fprintf(stderr,
				        "figlio: ⛔ pam_open_session: %s — the "
				        "compositor will not start\n",
				        pam_strerror(pam, rv));
			} else {
				ambiente_pam = pam_getenvlist(pam);
				/* ⭐ PHASE 17 T6: the SELinux level as for ssh. */
				livello_selinux_come_sshd(pw->pw_name);
			}
			/* ⛔ `pam_end` and not `pam_close_session`: see above. */
			pam_end(pam, PAM_SUCCESS);
		}
	}

	/* 3. the groups, then the gid, then the uid — and never the other way round. */
	if (setgroups((size_t)ngruppi, gruppi) != 0)
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
	 * ⚠ `SHELL` EMPTY by hand, as `sessione.c` does: an inherited `SHELL`
	 *   makes the sessions restart inside a login shell, and that is state 7
	 *   of the session bench.
	 * ⚠ And NO language variable: no application is started here, so there
	 *   is nothing a wrong locale could prevent.  The day this child made a
	 *   session BE BORN, the rule of `sessione.c` applies — and it must be
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
	for (int i = 0; ambiente_pam && ambiente_pam[i] && ne < 14; i++)
		if (strncmp(ambiente_pam[i], "XDG_SESSION_ID=", 15) == 0)
			envp[ne++] = ambiente_pam[i];
	envp[ne] = NULL;

	/* 6. the child's command line, which is what the bench will read in
	 *    `/proc/<pid>/cmdline`.  ⛔ No secrets in here: the password already
	 *    died with the helper, and it does not pass through here. */
	snprintf(a_utente, sizeof a_utente, "%s", pw->pw_name);
	snprintf(a_uid, sizeof a_uid, "%ld", (long)pw->pw_uid);
	snprintf(a_gid, sizeof a_gid, "%ld", (long)pw->pw_gid);
	snprintf(a_l, sizeof a_l, "%u", f->tela_l);
	snprintf(a_a, sizeof a_a, "%u", f->tela_a);
	snprintf(a_matr, sizeof a_matr, "%llu", (unsigned long long)g->matricola);
	argv[na++] = (char *)"remotix-figlio";
	argv[na++] = (char *)"--figlio-interno";
	argv[na++] = a_utente;
	argv[na++] = a_uid;
	argv[na++] = a_gid;
	argv[na++] = a_l;
	argv[na++] = a_a;
	argv[na++] = a_matr;
	argv[na++] = f->c_e_rilievo ? (char *)f->dir_rilievo : (char *)"-";
	/*
	 * ⛔⭐⭐⭐ AND THE CHATTER IS PASSED TO THE CHILD — 16 Aug 2026, and it is
	 *        the defect that cost me a whole day.
	 *
	 * ⛔ The child is NOT a fork: it is an `execve` of `remotix-figlio`.  ⇒ It
	 *    does not inherit the parent's variables, and `registro_parlantina()`
	 *    in the child stayed **off** — even when the server had started with
	 *    `--parlantina`.
	 *
	 * ⚠ So **every `registro_dettaglio()` of `figlio.c` went into the void**,
	 *   silently, without an error.  `[M]` And it cost dearly: hunting the
	 *   tail of login times I concluded for hours that certain branches "never
	 *   fired", because their line did not appear — while they fired all
	 *   right.  ⭐ Diagnostics that stay silent are not neutral: **they lie**,
	 *   and they lie in the worst direction, that is "that code does not run".
	 *
	 * ⇒ It is form E8 (`LEZIONI.md` §1.9) inside the very tool meant to unmask
	 *   it: "it did not do it" and "it did not tell me" with the same face.
	 *
	 * ⚠ At the end and optional: the child reads `argc >= 9` and this is the
	 *   tenth, so a command line without it does not break.
	 */
	if (registro_parla_molto())
		argv[na++] = (char *)"--parlantina";
	/* ⭐ And the journal (phase 16 §12), for exactly the same reason: the
	 *    parent's socket is CLOEXEC, and the child opens one of its own. */
	if (registro_nel_journal())
		argv[na++] = (char *)"--journal";
	/*
	 * ⛔⭐⭐ AND THE **THREE** CURES OF PHASE 9 PASS THROUGH HERE, for exactly the
	 *      same reason as the chatter above — and it is not an analogy, it is
	 *      the same defect.  ⚠ The third (audio silence) arrived on 24 Aug
	 *      2026, and travels NEGATED: see the box further down.
	 *
	 * ⛔ `codificatore_qualita_risale()` and `codificatore_tetto_banda()` are
	 *    statics of the PROCESS: calling them in the parent turns nothing on,
	 *    because the parent never opens an encoder.  ⚠ And the environment
	 *    above is composed from scratch (point 5): a `REMOTIX_...` does not
	 *    reach the other side, and would not even leave a line saying it did
	 *    not arrive.
	 *
	 * ⇒ The only channel that crosses the `exec` together with the socket is
	 *   this one, and the child reads them back in `figlio_vive()`.
	 *
	 * ⚠ At the end and optional: the child reads the first nine by position
	 *   and scans the rest by name, so a command line without them does not
	 *   break.  ⭐ And they appear in `/proc/<pid>/cmdline`: whoever watches a
	 *   bench sees what that child was born with, without trusting a log.
	 */
	if (f->fase9_qualita_risale)
		argv[na++] = (char *)"--qualita-risale";
	if (f->fase9_tetto_banda_mbit) {
		snprintf(a_tetto, sizeof a_tetto, "%u", f->fase9_tetto_banda_mbit);
		argv[na++] = (char *)"--tetto-banda-mbit";
		argv[na++] = a_tetto;
	}
	/* ⛔⭐⭐ AND THE THIRD TRAVELS NEGATED, which is the only form that does not lie.
	 *
	 *      The two above are born off: what is written at the end is "turn it
	 *      on".  This one is born ON (24 Aug 2026), so what is written is
	 *      "turn it off" — ⛔ and the word in `argv` is the SAME one the server
	 *      received (`--niente-audio-silenzio`), because whoever looks at a
	 *      child's `/proc/<pid>/cmdline` must be able to compare it by eye
	 *      with the parent's command line.  ⚠ If a positive `--audio-silenzio`
	 *      appeared here there would be TWO names for the same cure, and that
	 *      is exactly what this phase removed. */
	if (!f->fase9_audio_silenzio)
		argv[na++] = (char *)"--niente-audio-silenzio";
	/* ⭐ PHASE 19: the card's route, if forced (`--codifica vaapi|vulkan`):
	 *    the default "scheda" is not passed, and the child is born with the same. */
	if (strcmp(figlio_codifica_strada_chiesta(), "scheda") != 0) {
		argv[na++] = (char *)"--codifica";
		argv[na++] = (char *)figlio_codifica_strada_chiesta();
	}
	argv[na] = NULL;

	execve(f->percorso_mio, argv, envp);
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
 * ⛔⛔ And `fasi/10-multi-tenant-e-il-budget.md` §7.4 — "the session born
 *      blind", `provanic4/5/6` never succeeding in **98 · 55 · 50** attempts —
 *      is exactly this: those three users did not have the two groups, and
 *      `prova` and `provanic1`, which always saw, did.  ⇒ The defect blocked
 *      five tests and postponed a phase **without giving a single error**.
 *
 * ⭐⭐ SO THE CURE THAT COUNTS MOST IS NOT IN THE PROVISIONING: it is HERE.  A
 *     provisioning script can be forgotten, and indeed it was forgotten —
 *     `banchi/attrezzi-utenti.sh` and the terrains of phases 4/6/7/9 create
 *     tenants **without** the two groups.  ⛔ A defect that shows up as "it
 *     does not work and nobody knows why" is the one that costs months: the
 *     product must **notice it and say so**, at birth, with words that also
 *     say the cure.
 *
 * ⭐ AND THE GROUP IS READ FROM THE NODE, neither the name nor the number is
 *    hard-wired: `/dev/dri` is opened, the `st_gid` of every `cardN` and
 *    `renderDN` is taken (which is the provisioning's `stat -c %g`, done in C)
 *    and we look whether the tenant is in those groups.  ⚠ A hard-wired gid
 *    would be false on the next machine, and a hard-wired name (`render`) is
 *    false on a distribution that calls it otherwise.
 *
 * ⚠ WHY MEMBERSHIP AND NOT AN `access()`: the parent is root, and to root the
 *   kernel always says "yes".  The only question that can be asked from here,
 *   and that has the same answer the child will have, is "is this user in
 *   that group?".  ⛔ And on a normal desktop the access to the card would be
 *   given by logind's ACL (udev tag `uaccess`) to the user of the active
 *   session **on a seat** — ⇒ our session has no seat on purpose
 *   (`DECISIONI.md` §4.3-bis), so that ACL never arrives and the group is the
 *   only road.
 *
 * ⛔ AND THE SESSION IS NOT REFUSED, it is declared: on different hardware the
 *    software fallback might be slow instead of infinite (`[?]`, not
 *    measured), and a refusal would turn a declared degradation into a
 *    "cannot get in" — that is, it would put the user back to guessing, which
 *    is the defect this line cures.
 * ---------------------------------------------------------------------------
 */
#define DIR_NODI_SCHEDA "/dev/dri"
#define QUANTI_GRUPPI_SCHEDA 8

static const char *nome_del_gruppo(gid_t g, char *dove, size_t cap)
{
	struct group gr, *ris = NULL;
	char scorta[1024];

	if (getgrgid_r(g, &gr, scorta, sizeof scorta, &ris) == 0 && ris)
		snprintf(dove, cap, "%s", gr.gr_name);
	else
		snprintf(dove, cap, "gid %ld without a name", (long)g);
	return dove;
}

static bool sta_nel_gruppo(gid_t primario, const gid_t *gruppi, int ngruppi,
                           gid_t cercato)
{
	if (primario == cercato)
		return true;
	for (int i = 0; i < ngruppi; i++)
		if (gruppi[i] == cercato)
			return true;
	return false;
}

/*
 * ⭐ THE GROUPS OF THE CARD'S NODES, READ FROM THE MACHINE — in one place only.
 *
 * Returns how many it found (0 = no node, or the folder does not open: the
 * caller DECLARES it, each in its own words).  ⚠ Two functions use it — the
 * one that only says it and the one that enrols the tenant — and a second
 * copied scan would be a second place to diverge from (`LEZIONI.md` §1.47).
 */
static int raccogli_gruppi_scheda(gid_t visti[QUANTI_GRUPPI_SCHEDA],
                                  char nomi[QUANTI_GRUPPI_SCHEDA][64],
                                  char nodi[QUANTI_GRUPPI_SCHEDA][96],
                                  const char *utente)
{
	DIR *d;
	struct dirent *e;
	int nvisti = 0;

	d = opendir(DIR_NODI_SCHEDA);
	if (!d) {
		registro_dice_di(REG_FIGLIO, utente,
		                 "⚠ %s does not open (%s): I CANNOT say whether this "
		                 "tenant will see.  ⛔ On a machine without DRM nodes "
		                 "the compositor draws in software, and the session "
		                 "can be born blind without giving an error",
		                 DIR_NODI_SCHEDA, strerror(errno));
		return 0;
	}
	while ((e = readdir(d)) != NULL) {
		char percorso[96];
		struct stat st;
		bool gia = false;

		/* ⚠ `cardN` (the `video` group) and `renderDN` (the `render` group):
		 *   the two nodes have DIFFERENT groups, and both are needed.  ⛔ And
		 *   the numbers are scanned instead of hard-wired: `renderD128` and
		 *   `renderD129` swap between two boots (`provisiona.sh` §5). */
		if (strncmp(e->d_name, "renderD", 7) != 0 &&
		    strncmp(e->d_name, "card", 4) != 0)
			continue;
		/* ⚠ `%.32s` and not `%s`: `d_name` is 256 long and the compiler is
		 *   right to say so (`-Wformat-truncation`).  ⛔ A node name longer
		 *   than 32 does not exist (`renderD128` is ten letters), and if it
		 *   existed the truncated path would not open: the `stat` below
		 *   fails and that node is skipped — ⇒ never a WRONG group declared
		 *   for a half path. */
		snprintf(percorso, sizeof percorso, "%s/%.32s", DIR_NODI_SCHEDA,
		         e->d_name);
		if (stat(percorso, &st) != 0)
			continue;
		for (int i = 0; i < nvisti; i++)
			if (visti[i] == st.st_gid) {
				gia = true;
				break;
			}
		if (gia || nvisti >= QUANTI_GRUPPI_SCHEDA)
			continue;
		visti[nvisti] = st.st_gid;
		nome_del_gruppo(st.st_gid, nomi[nvisti], 64);
		snprintf(nodi[nvisti], 96, "%s", percorso);
		nvisti++;
	}
	closedir(d);
	return nvisti;
}

/* ⭐ Writes in the log whether this tenant will see or not.  It decides
 *    nothing: it declares.  Returns `true` if it is in ALL the groups of the
 *    card's nodes. */
static bool gruppi_della_scheda(const char *utente, gid_t primario,
                                const gid_t *gruppi, int ngruppi)
{
	gid_t visti[QUANTI_GRUPPI_SCHEDA];
	char nomi[QUANTI_GRUPPI_SCHEDA][64];
	char nodi[QUANTI_GRUPPI_SCHEDA][96];
	int nvisti = raccogli_gruppi_scheda(visti, nomi, nodi, utente);
	int mancanti = 0;
	char elenco[256];
	size_t usati = 0;

	if (nvisti == 0) {
		registro_dice_di(REG_FIGLIO, utente,
		                 "⚠ no `cardN`/`renderDN` node in %s: this "
		                 "machine has no card to show, and the "
		                 "compositor will draw in SOFTWARE",
		                 DIR_NODI_SCHEDA);
		return false;
	}

	for (int i = 0; i < nvisti; i++) {
		if (sta_nel_gruppo(primario, gruppi, ngruppi, visti[i])) {
			int n = snprintf(elenco + usati, sizeof elenco - usati, "%s%s",
			                 usati ? ", " : "", nomi[i]);
			if (n > 0 && (size_t)n < sizeof elenco - usati)
				usati += (size_t)n;
			continue;
		}
		mancanti++;
		/* ⛔⛔ THE LINE THAT IS WORTH THE WHOLE CHECK.  It says the defect, the
		 *     VISIBLE consequence ("it will see nothing"), and the cure in
		 *     full — including the `terminate-user`, without which a
		 *     `usermod` with the user manager alive does NOT take effect. */
		registro_dice_di(REG_FIGLIO, utente,
		                 "⛔⛔ «%s» IS NOT IN THE CARD'S GROUP «%s» (gid "
		                 "%ld, the group of %s): ⛔ THIS SESSION WILL BE BORN AND "
		                 "WILL SEE NOTHING — zero frames, no window will "
		                 "open, and the loop will go round and round between «BLACK: "
		                 "ZERO MONITORS» and «virtual monitor mounted».  ⭐ THE CURE, "
		                 "in two commands as root: `usermod -aG %s %s` and "
		                 "then `loginctl terminate-user %s` — ⚠ the second is "
		                 "NOT optional: the groups reach the compositor only "
		                 "when the user manager is BORN AGAIN.  (phase 10 §7.4, "
		                 "measured 27 Aug 2026: 0 sessions out of 4 without the "
		                 "group, 17 out of 17 with it)",
		                 utente, nomi[i], (long)visti[i], nodi[i], nomi[i],
		                 utente, utente);
	}

	if (mancanti == 0)
		registro_dice_di(REG_FIGLIO, utente,
		                 "⭐ is in the card's groups (%s): the session can "
		                 "see in hardware",
		                 elenco);
	return mancanti == 0;
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
 *    ⇒ `provisiona.sh` enrols whoever exists at installation time; ⛔ but
 *    whoever is created later would stay out, and the administrator would see
 *    a blank page without knowing why.
 *
 * ⛔⭐ AND IT IS DONE HERE, not earlier: we are in the parent, running as root,
 *     **after** PAM said yes — that is, nothing is granted to someone who
 *     merely knocks — and **before** the `fork`, so the child is born with
 *     the new groups.
 * ⚠ And it changes a declared division (I7: "the product touches the
 *   session, the machine is touched by `provisiona.sh`"): the product now
 *   touches the groups.  It is the user's decision, and it is written in the
 *   log every time.
 * ⚠ The user manager already alive does NOT take the new groups: it is made
 *   to be born again with `loginctl terminate-user` — ⛔ but ONLY if the user
 *   has no live REMOTIX desktop.  "There is no child here, so no graphical
 *   session" was true as long as the desktop died with the child; `[M]` T2
 *   (phase 17 §5.2) showed that after a service restart it survives (see the
 *   guard at the end of the function, PHASE 17 T7).
 *
 * Returns `true` if it changed something (and then the groups must be read
 * again).
 */
static bool comando_da_root(const char *quale, char *const argv[], const char *utente)
{
	pid_t p = fork();
	int stato = 0;

	if (p < 0)
		return false;
	if (p == 0) {
		execv(quale, argv);
		_exit(127);
	}
	if (waitpid(p, &stato, 0) != p)
		return false;
	if (!WIFEXITED(stato) || WEXITSTATUS(stato) != 0) {
		registro_dice_di(REG_FIGLIO, utente, "⛔ «%s» did not work (status %d)", quale,
		                 WIFEXITED(stato) ? WEXITSTATUS(stato) : -1);
		return false;
	}
	return true;
}

/*
 * ⭐ PHASE 17 (§6.5-bis) — EVERY ENROLMENT MADE BY REMOTIX IS RECORDED IN A FILE.
 *    The service log already said it (DECISIONI §7.21, guarantee 2), but the
 *    journal rotates and the installer does not read it: at uninstallation
 *    the engine must know WHO REMOTIX put in a group (origin DIRETTA, it is
 *    removed) and who was already there (PREESISTENTE, never touched —
 *    §6.6.4).
 *    ⇒ One JSON line per group, only for the groups the user was NOT in:
 *
 *    {"formato":"remotix-gruppi/1","data":"2026-09-30T10:11:12Z","utente":"mario",
 *     "uid":1005,"gruppo":"render","gid":989,"origine":"DIRETTA",
 *     "da":"REMOTIX alla prima connessione"}
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
#define GRUPPI_CARTELLA "/var/lib/remotix"
#define GRUPPI_FILE "gruppi-iscritti.jsonl"

/* The JSON text of a string: quotes, backslash and control characters. */
static void json_testo(char *d, size_t quanto, const char *s)
{
	size_t k = 0;

	for (; *s && k + 7 < quanto; s++) {
		unsigned char c = (unsigned char)*s;

		if (c == '"' || c == '\\') {
			d[k++] = '\\';
			d[k++] = (char)c;
		} else if (c < 0x20) {
			k += (size_t)snprintf(d + k, quanto - k, "\\u%04x", c);
		} else {
			d[k++] = (char)c;
		}
	}
	d[k] = '\0';
}

/* The folder: opened without following links, owned by root, not writable by
 * others.  If missing (outside the package: a bench) it is created 0700.  -1
 * with `perche` written. */
static int gruppi_apri_cartella(char *perche, size_t quanto)
{
	struct stat st;
	int dfd;

	if (mkdir(GRUPPI_CARTELLA, 0700) != 0 && errno != EEXIST) {
		snprintf(perche, quanto, "mkdir %s: %s", GRUPPI_CARTELLA, strerror(errno));
		return -1;
	}
	dfd = open(GRUPPI_CARTELLA, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
	if (dfd < 0) {
		snprintf(perche, quanto, "%s: %s", GRUPPI_CARTELLA, strerror(errno));
		return -1;
	}
	if (fstat(dfd, &st) != 0 || st.st_uid != 0 || (st.st_mode & 022)) {
		snprintf(perche, quanto, "%s is not owned by root or is writable by others", GRUPPI_CARTELLA);
		close(dfd);
		return -1;
	}
	return dfd;
}

/* The file, append-only.  -1 with `perche` written. */
static int gruppi_apri_file(char *perche, size_t quanto)
{
	struct stat st;
	int dfd = gruppi_apri_cartella(perche, quanto);
	int fd;
	bool nuovo = false;

	if (dfd < 0)
		return -1;
	fd = openat(dfd, GRUPPI_FILE, O_WRONLY | O_APPEND | O_NOFOLLOW | O_CLOEXEC);
	if (fd < 0 && errno == ENOENT) {
		fd = openat(dfd, GRUPPI_FILE,
		            O_WRONLY | O_APPEND | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
		nuovo = fd >= 0;
	}
	if (fd < 0) {
		snprintf(perche, quanto, "%s/%s: %s", GRUPPI_CARTELLA, GRUPPI_FILE, strerror(errno));
		close(dfd);
		return -1;
	}
	if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode) || st.st_uid != 0 || (st.st_mode & 022)) {
		snprintf(perche, quanto, "%s/%s is not a regular file owned by root, or is writable by others",
		         GRUPPI_CARTELLA, GRUPPI_FILE);
		close(fd);
		close(dfd);
		return -1;
	}
	/* The new name in the folder must survive a power failure as much as the
	 * line inside the file. */
	if (nuovo)
		(void)fsync(dfd);
	close(dfd);
	return fd;
}

/* One line per group.  false with `perche` written. */
static bool gruppi_annota(int fd, const char *utente, uid_t uid, const char *gruppo, gid_t gid,
                          char *perche, size_t quanto)
{
	char u[256], g[192], quando[32], riga[768];
	struct tm tm;
	time_t ora = time(NULL);
	int n;

	json_testo(u, sizeof u, utente);
	json_testo(g, sizeof g, gruppo);
	gmtime_r(&ora, &tm);
	strftime(quando, sizeof quando, "%Y-%m-%dT%H:%M:%SZ", &tm);
	n = snprintf(riga, sizeof riga,
	             "{\"formato\":\"remotix-gruppi/1\",\"data\":\"%s\",\"utente\":\"%s\","
	             "\"uid\":%lu,\"gruppo\":\"%s\",\"gid\":%lu,\"origine\":\"DIRETTA\","
	             "\"da\":\"REMOTIX alla prima connessione\"}\n",
	             quando, u, (unsigned long)uid, g, (unsigned long)gid);
	if (n <= 0 || (size_t)n >= sizeof riga) {
		snprintf(perche, quanto, "the line does not fit");
		return false;
	}
	/* ⛔ A single `write`: with O_APPEND the line arrives whole at the end, or not at all. */
	if (write(fd, riga, (size_t)n) != n) {
		snprintf(perche, quanto, "write: %s", strerror(errno));
		return false;
	}
	if (fsync(fd) != 0) {
		snprintf(perche, quanto, "fsync: %s", strerror(errno));
		return false;
	}
	return true;
}

static bool iscrivi_ai_gruppi_della_scheda(const char *utente, uid_t uid, gid_t primario,
                                           const gid_t *gruppi, int ngruppi)
{
	gid_t visti[QUANTI_GRUPPI_SCHEDA];
	char nomi[QUANTI_GRUPPI_SCHEDA][64];
	char nodi[QUANTI_GRUPPI_SCHEDA][96];
	int nvisti = raccogli_gruppi_scheda(visti, nomi, nodi, utente);
	int messi[QUANTI_GRUPPI_SCHEDA];
	int nmessi = 0;
	char elenco[256] = "";
	char perche[256] = "";
	size_t usati = 0;
	char *argv_mod[6];
	char *argv_term[4];
	int fd;

	if (nvisti == 0 || geteuid() != 0)
		return false;
	for (int i = 0; i < nvisti; i++) {
		int n;

		/* Whoever is already there is PREESISTENTE: not enrolled and not recorded. */
		if (sta_nel_gruppo(primario, gruppi, ngruppi, visti[i]))
			continue;
		n = snprintf(elenco + usati, sizeof elenco - usati, "%s%s", usati ? "," : "",
		             nomi[i]);
		if (n > 0 && (size_t)n < sizeof elenco - usati) {
			usati += (size_t)n;
			messi[nmessi++] = i;
		}
	}
	if (!usati)
		return false;

	registro_dice_di(REG_FIGLIO, utente,
	                 "⭐ FIRST CONNECTION: «%s» is not in the card's groups (%s) and "
	                 "I am PUTTING it there, now — the user's decision of 20 Sep 2026.  "
	                 "⚠ Without it, this session would be born BLIND",
	                 utente, elenco);
	argv_mod[0] = (char *)"usermod";
	argv_mod[1] = (char *)"-aG";
	argv_mod[2] = elenco;
	argv_mod[3] = (char *)utente;
	argv_mod[4] = NULL;
	/* The file is opened BEFORE touching the groups, so an obstacle is known
	 * at once; the line is written AFTER, only if `usermod` succeeded:
	 * recording an enrolment never made would make the uninstallation remove a
	 * group put there by others. */
	fd = gruppi_apri_file(perche, sizeof perche);
	if (!comando_da_root("/usr/sbin/usermod", argv_mod, utente) &&
	    !comando_da_root("/sbin/usermod", argv_mod, utente)) {
		registro_dice_di(REG_FIGLIO, utente,
		                 "⛔ I could not enrol «%s» in «%s»: the session will be born "
		                 "BLIND, and the manual cure is `usermod -aG %s %s`",
		                 utente, elenco, elenco, utente);
		if (fd >= 0)
			close(fd);
		return false;
	}
	for (int j = 0; j < nmessi; j++) {
		int i = messi[j];

		if (fd >= 0 && gruppi_annota(fd, utente, uid, nomi[i], visti[i], perche, sizeof perche))
			registro_dice_di(REG_FIGLIO, utente,
			                 "⭐ recorded in %s/%s: «%s» in «%s» (gid %ld), DIRETTA — the "
			                 "uninstallation will remove it",
			                 GRUPPI_CARTELLA, GRUPPI_FILE, utente, nomi[i], (long)visti[i]);
		else
			registro_dice_di(REG_FIGLIO, utente,
			                 "⛔ enrolment NOT RECORDED (%s): «%s» in «%s» (gid %ld) is "
			                 "the work of REMOTIX but %s/%s does not say so — the uninstallation "
			                 "will NOT remove it.  Manual remedy: `gpasswd -d %s %s` after "
			                 "uninstalling",
			                 perche, utente, nomi[i], (long)visti[i], GRUPPI_CARTELLA,
			                 GRUPPI_FILE, utente, nomi[i]);
	}
	if (fd >= 0)
		close(fd);
	/* ⚠ And the user manager is made to be BORN AGAIN, or the new groups do not
	 *   reach the compositor (`[M]` 27 Aug 2026).
	 * ⛔⭐ PHASE 17, T7 — "there is no child here, so no desktop" IS NOT
	 *     TRUE: `[M]` T2, after a service restart the REMOTIX desktop survives
	 *     without a child (`ritrovo.h`).  `terminate-user` would bring it down
	 *     with all its windows.  ⇒ logind and /proc are asked FIRST; if the
	 *     desktop is there — or it is not known — it is NOT issued, and we say
	 *     that the new groups will arrive at the next birth of the desktop. */
	{
		RitrovoDesktop vivo;
		int c = ritrovo_vivo(uid, &vivo);

		if (c != 0) {
			if (c > 0)
				registro_dice_di(REG_FIGLIO, utente,
				                 "⛔ «%s» enrolled in «%s», but the user manager is NOT "
				                 "restarted: it has a LIVE REMOTIX desktop (session %s, "
				                 "stage pid %ld «%s») and `loginctl terminate-user` would "
				                 "close it with its windows.  ⚠ The new groups "
				                 "will reach the compositor at the next birth of the "
				                 "desktop: until then it may see in software",
				                 utente, elenco, vivo.sessione, (long)vivo.palco, vivo.comm);
			else
				registro_dice_di(REG_FIGLIO, utente,
				                 "⛔ «%s» enrolled in «%s», but the user manager is NOT "
				                 "restarted: logind does not say whether it has a live REMOTIX "
				                 "desktop, and when in doubt nothing is brought down",
				                 utente, elenco);
			return true;
		}
	}
	argv_term[0] = (char *)"loginctl";
	argv_term[1] = (char *)"terminate-user";
	argv_term[2] = (char *)utente;
	argv_term[3] = NULL;
	(void)comando_da_root("/usr/bin/loginctl", argv_term, utente);
	registro_dice_di(REG_FIGLIO, utente,
	                 "⭐ «%s» enrolled in «%s» and user manager restarted: from "
	                 "now on it sees the card",
	                 utente, elenco);
	return true;
}

bool figli_assicura(figli *f, const char *utente)
{
	return figli_assicura_da(f, utente, NULL);
}

bool figli_assicura_da(figli *f, const char *utente, const char *rhost)
{
	struct figlio *g;
	struct passwd pw, *ris = NULL;
	char scorta[1024];
	gid_t gruppi[64];
	int ngruppi = (int)(sizeof gruppi / sizeof gruppi[0]);
	int sv[2];
	int uno = 1;
	int libero = -1;
	pid_t p;

	if (!f || !utente || !utente[0])
		return false;

	/* ⛔⭐ I2 — "only one graphical session per user".  Two connections of the
	 *     same user do NOT make two children: the second finds the first, and
	 *     sees the same stage.  ⚠ And if the first is dead, the slot has
	 *     already been freed by `figli_muovi()`: nothing is resurrected here. */
	g = cerca(f, utente);
	if (g) {
		registro_dice(REG_FIGLIO,
		              "«%s» is already served by the child pid %ld (uid %ld): a "
		              "second one is NOT born — invariant I2, and the stage is the "
		              "same because it belongs to the SESSION (I4)",
		              utente, (long)g->pid, (long)g->uid);
		return true;
	}

	for (int i = 0; i < f->tetto; i++)
		if (!f->v[i].usato) {
			libero = i;
			break;
		}
	if (libero < 0) {
		registro_dice(REG_FIGLIO,
		              "⛔ %d children already alive: «%s» will NOT get one, and so "
		              "will not get a stage.  It is a declared no, not a maybe "
		              "(invariant I3)",
		              f->tetto, utente);
		return false;
	}

	/* ⛔ The name is resolved HERE, in the parent, and the uid that comes out
	 *    is the one the kernel will have to stamp on every message.  ⚠
	 *    Resolving it in the child would mean letting the one to be checked
	 *    say who it is. */
	if (getpwnam_r(utente, &pw, scorta, sizeof scorta, &ris) != 0 || !ris) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» passed PAM but is not a user of this "
		              "system (getpwnam: %s): NO child.  ⚠ It is not a "
		              "contradiction — PAM can admit a name that NSS does not "
		              "resolve, and in that case there is no uid to "
		              "drop to",
		              utente, strerror(errno));
		return false;
	}
	if (pw.pw_uid == 0) {
		/* ⛔ A child at uid 0 would not be a child: it would be the parent
		 *    under another name, and the reason this file exists — root does
		 *    not talk to the session bus — would apply to it just the same. */
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» is uid 0: I am NOT spawning a privileged child.  The "
		              "child exists in order NOT to be root (DECISIONI.md "
		              "§1.10-bis), and one at uid 0 would not have anyone's "
		              "session bus anyway",
		              utente);
		return false;
	}
	if (getgrouplist(pw.pw_name, pw.pw_gid, gruppi, &ngruppi) < 0) {
		/* More groups than the buffer holds: what is there is taken and it is
		 * DECLARED, because a child with fewer groups than due may hit a
		 * permission denied much later and much further away. */
		ngruppi = (int)(sizeof gruppi / sizeof gruppi[0]);
		registro_dice(REG_FIGLIO,
		              "⚠ «%s» has more than %d groups: the child will carry %d.  "
		              "If something is denied to it, the cause is this line",
		              utente, ngruppi, ngruppi);
	}

	/* ⭐⭐⭐ AND HERE IT IS SAID WHETHER THIS TENANT WILL SEE — the box above
	 *      `gruppi_della_scheda()`.  ⛔ This is the place and no other: it is
	 *      the only point where the product holds **the user's name and their
	 *      groups together**, and it is BEFORE the `fork` — that is, the line
	 *      goes out even when no stage will then be born.  ⚠ The return value
	 *      is not looked at: the session is born anyway, and the degradation
	 *      is declared (I1). */
	/* ⭐ And if something is missing, it is REMEDIED before the `fork` (the
	 *    user's decision, 20 Sep 2026): once enrolled, the groups are read
	 *    again and declared again — the line the administrator reads must be
	 *    the TRUE one of this session, not the one from before the cure. */
	if (iscrivi_ai_gruppi_della_scheda(pw.pw_name, pw.pw_uid, pw.pw_gid, gruppi, ngruppi)) {
		ngruppi = (int)(sizeof gruppi / sizeof gruppi[0]);
		if (getgrouplist(pw.pw_name, pw.pw_gid, gruppi, &ngruppi) < 0)
			ngruppi = (int)(sizeof gruppi / sizeof gruppi[0]);
	}
	(void)gruppi_della_scheda(pw.pw_name, pw.pw_gid, gruppi, ngruppi);

	/* ⛔ `SOCK_SEQPACKET` for the same reason as the helper: the message
	 *    boundaries are kept by the kernel.  With a stream the framing would
	 *    be ours, and a defect in there would mean "someone else's pixels" —
	 *    that is I3 broken by a reading error.
	 * ⛔ And `CLOEXEC` on the parent's end: the child must NOT hold its
	 *    parent's end, or it would never notice that the parent died. */
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0) {
		registro_dice(REG_FIGLIO,
		              "⛔ no socketpair for «%s» (%s): no child, "
		              "no stage",
		              utente, strerror(errno));
		return false;
	}
	/* ⛔⭐ THIS LINE IS INVARIANT I3 OF THE WHOLE FILE.  Without
	 *     `SO_PASSCRED`, the kernel does not stamp the credentials and every
	 *     message would arrive "without a sender": the parent could only take
	 *     the child's word for it, that is check nothing. */
	if (setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &uno, sizeof uno) != 0) {
		registro_dice(REG_FIGLIO,
		              "⛔ SO_PASSCRED does not turn on (%s): without it, the kernel "
		              "does not sign the child's messages and the identity would be "
		              "ITS OWN declaration.  I am NOT spawning the child: better no "
		              "stage than a stage I do not know whose it is",
		              strerror(errno));
		close(sv[0]);
		close(sv[1]);
		return false;
	}

	g = &f->v[libero];
	memset(g, 0, sizeof *g);
	g->matricola = f->prossima_matricola;
	snprintf(g->utente, sizeof g->utente, "%s", pw.pw_name);
	snprintf(g->rhost, sizeof g->rhost, "%s", rhost ? rhost : "");
	g->uid = pw.pw_uid;
	g->gid = pw.pw_gid;

	p = fork();
	if (p < 0) {
		registro_dice(REG_FIGLIO, "⛔ fork for «%s»: %s — no stage", utente,
		              strerror(errno));
		close(sv[0]);
		close(sv[1]);
		memset(g, 0, sizeof *g);
		g->fd = -1;
		return false;
	}
	if (p == 0) {
		close(sv[0]);
		diventa_ed_esegui(f, g, sv[1], &pw, gruppi, ngruppi);
		_exit(38); /* never reached */
	}

	close(sv[1]);
	g->usato = true;
	g->pid = p;
	g->fd = sv[0];
	/* ⛔ Non-blocking on the PARENT's side, and only on that one: here we are
	 *    inside the server's single `poll` loop, and a read that waits stops
	 *    all connections together (`CODER.md` §4.4) — the defect just cured on
	 *    PAM, brought back through another door.  ⚠ The CHILD's end stays
	 *    blocking on purpose: there waiting is the job. */
	fcntl(g->fd, F_SETFL, O_NONBLOCK);
	g->nato_ms = registro_ora_ms();
	g->ultimo_ricontrollo_ms = g->nato_ms;
	f->prossima_matricola++;

	registro_dice(REG_FIGLIO,
	              "⭐ child spawned for «%s»: pid %ld, uid %ld, gid %ld, "
	              "serial %llu.  ⛔ That it REALLY is that uid is not for me "
	              "to say: the kernel will say it on each of its messages (SO_PASSCRED)",
	              g->utente, (long)g->pid, (long)g->uid, (long)g->gid,
	              (unsigned long long)g->matricola);
	return true;
}

size_t figli_descrittori(figli *f, struct pollfd *fds, size_t max)
{
	size_t n = 0;
	if (!f)
		return 0;
	for (int i = 0; i < f->tetto && n < max; i++) {
		if (!f->v[i].usato || f->v[i].fd < 0)
			continue;
		fds[n].fd = f->v[i].fd;
		fds[n].events = POLLIN;
		fds[n].revents = 0;
		n++;
	}
	return n;
}

int figli_quanti(const figli *f)
{
	int n = 0;
	if (!f)
		return 0;
	for (int i = 0; i < f->tetto; i++)
		if (f->v[i].usato)
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
 * ⚠ The index goes from 0 to `figli_quanti() − 1` and **is not stable between
 *   two calls**: slots get freed.  It serves to scan once, within the same
 *   round of the loop, and for nothing else. */
const char *figli_utente_ennesimo(const figli *f, int quale)
{
	int n = 0;

	if (!f || quale < 0)
		return NULL;
	for (int i = 0; i < f->tetto; i++) {
		if (!f->v[i].usato)
			continue;
		if (n == quale)
			return f->v[i].utente;
		n++;
	}
	return NULL;
}

pid_t figli_pid_di(const figli *f, const char *utente)
{
	const struct figlio *g;
	if (!f || !utente)
		return -1;
	g = cerca((figli *)f, utente);
	return g ? g->pid : -1;
}

/* A frame piece has arrived, and the credentials were right. */
static void monta_pezzo(struct figli *f, struct figlio *g,
                        const struct corpo_fotogramma *c, const uint8_t *dati)
{
	if (c->totale == 0 || c->totale > FOTOGRAMMA_MAX) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» announces a frame of %u bytes: outside the "
		              "cap of §6.2 (1..%u).  It is dropped, and NOT truncated: a "
		              "cut frame delivered as whole is a "
		              "frame that lies",
		              g->utente, c->totale, FOTOGRAMMA_MAX);
		return;
	}
	if (c->pezzo > PEZZO_MAX || (uint64_t)c->offset + c->pezzo > c->totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: piece out of size (offset %u + %u of %u): "
		              "discarded",
		              g->utente, c->offset, c->pezzo, c->totale);
		free(g->monta);
		g->monta = NULL;
		g->monta_totale = g->monta_avuti = 0;
		return;
	}

	if (c->offset == 0) {
		free(g->monta);
		g->monta = (uint8_t *)malloc(c->totale);
		if (!g->monta) {
			registro_dice(REG_FIGLIO,
			              "⛔ «%s»: %u bytes of frame do not fit in "
			              "memory",
			              g->utente, c->totale);
			g->monta_totale = g->monta_avuti = 0;
			return;
		}
		g->monta_totale = c->totale;
		g->monta_avuti = 0;
		g->monta_codec = c->codec;
		g->monta_chiave = c->chiave;
		g->monta_l = c->larghezza;
		g->monta_a = c->altezza;
		g->monta_istante = c->istante_us;
		g->monta_input = c->input;
	}
	/* ⛔ Pieces are accepted ONLY in order, and one out of place throws away
	 *    everything: stitching a hole would mean guessing what was missing, and
	 *    that is the leniency that hides (`REVIEWER.md` §5). */
	if (!g->monta || c->offset != g->monta_avuti || c->codec != g->monta_codec
	    || c->totale != g->monta_totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: piece out of order (expected %zu, got "
		              "%u): the whole frame is DROPPED",
		              g->utente, g->monta_avuti, c->offset);
		free(g->monta);
		g->monta = NULL;
		g->monta_totale = g->monta_avuti = 0;
		return;
	}
	memcpy(g->monta + c->offset, dati, c->pezzo);
	g->monta_avuti += c->pezzo;
	if (g->monta_avuti < g->monta_totale)
		return;

	/* ⛔⭐ AND THIS LINE MOVED TO CHATTER WITH PHASE 3.
	 *
	 *     With a single frame it was the line that proved the whole of phase 2.
	 *     ⛔ At sixty per second it becomes sixty lines per second per user,
	 *     and a log that repeats itself can no longer be read — that is the
	 *     same reason `bool video_fatto` existed.  ⚠ The fact does NOT vanish:
	 *     it stays in the chatter, and the summary count is written by
	 *     `contati` below once per second.  The first one, the one that says
	 *     whether the stage works, is written anyway. */
	if (g->fotogrammi_avuti == 0)
		registro_dice(REG_FIGLIO,
		              "⭐ FIRST complete frame from «%s» (uid %ld, kernel "
		              "stamp): codec %u, %zu bytes, %ux%u, %s",
		              g->utente, (long)g->uid, g->monta_codec, g->monta_totale,
		              g->monta_l, g->monta_a,
		              g->monta_chiave ? "KEYFRAME" : "delta");
	else
		registro_dettaglio(REG_FIGLIO,
		                   "frame from «%s»: codec %u, %zu bytes, %s",
		                   g->utente, g->monta_codec, g->monta_totale,
		                   g->monta_chiave ? "KEYFRAME" : "delta");
	g->fotogrammi_avuti++;
	g->byte_avuti += g->monta_totale;
	if (g->monta_chiave)
		g->chiavi_avute++;
	if (f->deposita)
		f->deposita(f->ctx, g->utente, g->uid, g->monta_codec,
		            g->monta_chiave != 0, g->monta, g->monta_totale, g->monta_l,
		            g->monta_a, g->monta_istante, g->monta_input);
	free(g->monta);
	g->monta = NULL;
	g->monta_totale = g->monta_avuti = 0;
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
 *         not a duplicate of the check in `appunti.c`: that one is a module
 *         we trust, this one is a socket;
 *       · **one extra byte** is allocated and the zero is put there: from
 *         here on the text travels as a string, and `appunti.c` has already
 *         guaranteed it does not contain one in the middle.
 */
static void monta_appunti(struct figli *f, struct figlio *g,
                          const struct corpo_appunti *c, const uint8_t *dati)
{
	if (c->totale > APPUNTI_TETTO) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» announces %u bytes of clipboard: over the cap of "
		              "§5.4 (%u).  It is dropped, and NOT truncated — a cut text "
		              "pasted into a terminal is worse than a missing text",
		              g->utente, c->totale, APPUNTI_TETTO);
		return;
	}
	/* ⚠ Zero bytes is a LEGITIMATE fact: the clipboard emptied.  It is
	 *   delivered, and the receiver decides — it is not this table's job. */
	if (c->totale == 0) {
		if (f->su_appunti_testo)
			f->su_appunti_testo(f->ctx_appunti, g->utente, g->uid, "", 0);
		return;
	}
	if (c->pezzo > PEZZO_MAX || (uint64_t)c->offset + c->pezzo > c->totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: clipboard piece out of size (offset %u + %u of "
		              "%u): discarded",
		              g->utente, c->offset, c->pezzo, c->totale);
		free(g->app_monta);
		g->app_monta = NULL;
		g->app_totale = g->app_avuti = 0;
		return;
	}
	if (c->offset == 0) {
		free(g->app_monta);
		g->app_monta = (uint8_t *)malloc((size_t)c->totale + 1u);
		if (!g->app_monta) {
			registro_dice(REG_FIGLIO,
			              "⛔ «%s»: %u bytes of clipboard do not fit in memory",
			              g->utente, c->totale);
			g->app_totale = g->app_avuti = 0;
			return;
		}
		g->app_totale = c->totale;
		g->app_avuti = 0;
	}
	/* ⛔ In order and nothing else, like the frame and the cursor.  ⚠ And here
	 *    the guessed hole would be **worse**: a wrong frame lasts 20 ms, a
	 *    wrong text gets pasted into a terminal. */
	if (!g->app_monta || c->offset != g->app_avuti
	    || c->totale != g->app_totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: clipboard piece out of order (expected %zu, "
		              "got %u): the whole text is DROPPED",
		              g->utente, g->app_avuti, c->offset);
		free(g->app_monta);
		g->app_monta = NULL;
		g->app_totale = g->app_avuti = 0;
		return;
	}
	memcpy(g->app_monta + c->offset, dati, c->pezzo);
	g->app_avuti += c->pezzo;
	if (g->app_avuti < g->app_totale)
		return;

	g->app_monta[g->app_totale] = 0;
	registro_dice(REG_FIGLIO,
	              "⭐ «%s» copied %zu bytes of text in the session: to the "
	              "client (§7.4)",
	              g->utente, g->app_totale);
	if (f->su_appunti_testo)
		f->su_appunti_testo(f->ctx_appunti, g->utente, g->uid,
		                    (const char *)g->app_monta, g->app_totale);
	free(g->app_monta);
	g->app_monta = NULL;
	g->app_totale = g->app_avuti = 0;
}

static void monta_cursore(struct figli *f, struct figlio *g,
                          const struct corpo_cursore *c, const uint8_t *dati)
{
	/* ⛔ The cap is that of `RCP.md` §5.5 — 256x256 in BGRA — and it is
	 *    enforced HERE because here the sender is another process.  ⚠ It is
	 *    not a duplicate of the limits of `cursore.c`: that one is a module we
	 *    trust, this one is a socket. */
	if (c->totale > (uint32_t)CURSORE_MAX_LATO * CURSORE_MAX_LATO * 4u) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» announces a cursor of %u bytes: over the cap of "
		              "§5.5 (%ux%u in BGRA).  It is dropped",
		              g->utente, c->totale, CURSORE_MAX_LATO, CURSORE_MAX_LATO);
		return;
	}

	/* ⭐ The hidden one arrives without an image, and is delivered at once: it
	 *    is the only way the client has of knowing the pointer has vanished. */
	if (c->totale == 0) {
		if (f->cursore)
			f->cursore(f->ctx, g->utente, g->uid, c->larghezza, c->altezza,
			           c->attivo_x, c->attivo_y, NULL, 0);
		return;
	}
	if (c->pezzo > PEZZO_MAX || (uint64_t)c->offset + c->pezzo > c->totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: cursor piece out of size (offset %u + %u of "
		              "%u): discarded",
		              g->utente, c->offset, c->pezzo, c->totale);
		free(g->cur_monta);
		g->cur_monta = NULL;
		g->cur_totale = g->cur_avuti = 0;
		return;
	}
	if (c->offset == 0) {
		free(g->cur_monta);
		g->cur_monta = (uint8_t *)malloc(c->totale);
		if (!g->cur_monta) {
			g->cur_totale = g->cur_avuti = 0;
			return;
		}
		g->cur_totale = c->totale;
		g->cur_avuti = 0;
		g->cur_l = c->larghezza;
		g->cur_a = c->altezza;
		g->cur_ax = c->attivo_x;
		g->cur_ay = c->attivo_y;
	}
	/* ⛔ In order and nothing else, like the frame: stitching a hole would mean
	 *    guessing what was missing — and a guessed cursor is a cursor made of
	 *    someone else's memory. */
	if (!g->cur_monta || c->offset != g->cur_avuti || c->totale != g->cur_totale
	    || c->larghezza != g->cur_l || c->altezza != g->cur_a) {
		registro_dettaglio(REG_FIGLIO,
		                   "«%s»: cursor piece out of order: dropping the half "
		                   "shape (the client keeps the previous one)",
		                   g->utente);
		free(g->cur_monta);
		g->cur_monta = NULL;
		g->cur_totale = g->cur_avuti = 0;
		return;
	}
	memcpy(g->cur_monta + c->offset, dati, c->pezzo);
	g->cur_avuti += c->pezzo;
	if (g->cur_avuti < g->cur_totale)
		return;

	if (f->cursore)
		f->cursore(f->ctx, g->utente, g->uid, g->cur_l, g->cur_a, g->cur_ax,
		           g->cur_ay, g->cur_monta, g->cur_totale);
	free(g->cur_monta);
	g->cur_monta = NULL;
	g->cur_totale = g->cur_avuti = 0;
}

/* ⛔ Returns `false` when the child is gone — and the caller MUST stop
 * reading its descriptor.  ⚠ Without this value, the loop of `figli_muovi()`
 * would keep reading a slot just zeroed: the kind of defect that reads well
 * and is never seen. */
static bool tratta(struct figli *f, struct figlio *g, const struct testa *t,
                   const uint8_t *corpo, size_t byte)
{
	switch (t->tipo) {
	case MSG_SONO: {
		struct corpo_sono s;
		if (byte < sizeof s)
			return true;
		memcpy(&s, corpo, sizeof s);
		/* ⛔ AND HERE THE CIRCLE CLOSES: the child says what the KERNEL
		 *    answered it about itself (`getresuid`), and the parent compares
		 *    it with what the KERNEL stamped on the message.  If the two
		 *    diverged, one of the two is reading a variable instead of asking
		 *    — and the child would be killed. */
		if (s.uid != (uint32_t)g->uid || s.euid != (uint32_t)g->uid
		    || s.suid != (uint32_t)g->uid) {
			registro_dice(REG_FIGLIO,
			              "⛔⛔ «%s» says it is uid %u/%u/%u and the kernel "
			              "stamped it as %ld: the child is killed",
			              g->utente, s.uid, s.euid, s.suid, (long)g->uid);
			if (g->pid > 0)
				kill(g->pid, SIGKILL);
			figlio_congeda(f, g, "declares a uid different from the stamped one");
			return false;
		}
		if (g->si_e_presentato) {
			registro_dettaglio(REG_FIGLIO,
			                   "«%s» rechecked: uid %u, pid %u, parent %u, "
			                   "%u descriptors — the link holds",
			                   g->utente, s.euid, s.pid, s.ppid, s.descrittori);
			return true;
		}
		g->si_e_presentato = true;
		registro_dice(REG_FIGLIO,
		              "⭐ «%s» introduces itself: pid %u (parent %u), uid %u/%u/%u, "
		              "gid %u/%u/%u, %u open descriptors, runtime «%s» %s, "
		              "bus socket %s",
		              g->utente, s.pid, s.ppid, s.uid, s.euid, s.suid, s.gid,
		              s.egid, s.sgid, s.descrittori, s.runtime,
		              s.runtime_c_e ? "exists and is its own" : "⛔ does NOT exist or is not its own",
		              s.socket_bus_c_e ? "exists" : "⛔ does not exist");
		return true;
	}
	case MSG_SESSIONE_FINITA:
		/*
		 * ⭐⭐ §7.6, the twin: the graphical session is over and no client
		 *     asked for it — the user chose "Log out…" in the desktop menu.
		 *
		 * ⛔ And whoever is watching must know NOW: by keeping quiet, the
		 *    clients would stay on a frozen screen until the thirty seconds of
		 *    silence, and then read "network error" — which is exactly
		 *    finding B-7.
		 */
		registro_dice(REG_FIGLIO,
		              "⭐ §7.6: the graphical session of «%s» IS OVER (no "
		              "client asked for it: the user logged out from the "
		              "desktop menu).  Whoever is watching gets the farewell 0x10",
		              g->utente);
		if (f->su_sessione_finita)
			f->su_sessione_finita(f->ctx_sessione_finita, g->utente, g->uid);
		else
			registro_dice(REG_FIGLIO,
			              "⚠ no «session over» hook: the clients of «%s» "
			              "were NOT warned, and will wait the thirty "
			              "seconds of silence",
			              g->utente);
		return true;
	case MSG_PALCO: {
		struct corpo_palco p;
		if (byte < sizeof p)
			return true;
		memcpy(&p, corpo, sizeof p);
		registro_dice(REG_FIGLIO,
		              "%s the stage of «%s»: bus %s, session %u, grab %u, "
		              "monitor «%s» (%u before, %u after), %ux%u stride %u at %u "
		              "bits, %u streams delivering%s%s",
		              p.flussi > 0 ? "⭐" : "⛔", g->utente,
		              p.bus_aperto ? "OPEN" : "⛔ NO", p.stato_sessione,
		              p.presa, p.monitor, p.monitor_prima, p.monitor_dopo,
		              p.larghezza, p.altezza, p.stride, p.bit, p.flussi,
		              p.guasto[0] ? " — " : "", p.guasto);
		return true;
	}
	case MSG_CURSORE: {
		struct corpo_cursore c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		if (byte < sizeof c + c.pezzo)
			return true;
		monta_cursore(f, g, &c, corpo + sizeof c);
		return true;
	}
	case MSG_FOTOGRAMMA: {
		struct corpo_fotogramma c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		if (byte < sizeof c + c.pezzo)
			return true;
		monta_pezzo(f, g, &c, corpo + sizeof c);
		return true;
	}
	case MSG_BLOCCO: {
		struct corpo_blocco c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		if (byte < sizeof c + c.byte)
			return true;
		/* ⛔⭐ AND HERE THE CODEC IS CHECKED, instead of trusted.
		 *
		 *     The child runs as the user and the parent is privileged: a
		 *     number that crosses that boundary is an input, not a datum.
		 *     ⚠ A `codec` that §6.3 does not define would end up **inside the
		 *     datagram** and the client would discard it — that is, the audio
		 *     would not arrive, without any line saying why. */
		if (c.codec != 1 && c.codec != 2) {
			registro_dice(REG_FIGLIO,
			              "⛔ «%s» sends an audio block with codec %u, which "
			              "§6.3 does not define (1 = Opus, 2 = PCM): DROPPED",
			              g->utente, c.codec);
			return true;
		}
		if (f->su_blocco)
			f->su_blocco(f->ctx_blocco, g->utente, g->uid, c.codec,
			             c.istante_us, corpo + sizeof c, c.byte);
		return true;
	}
	case MSG_APPUNTI_DALLA_SESSIONE: {
		struct corpo_appunti c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		if (byte < sizeof c + c.pezzo)
			return true;
		monta_appunti(f, g, &c, corpo + sizeof c);
		return true;
	}
	case MSG_APPUNTI_VUOLE: {
		struct corpo_appunti c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		/* ⛔⛔ AND IF NOBODY IS LISTENING THE ANSWER GOES OUT ANYWAY, at once
		 *      and empty-handed.
		 *
		 *      The case is real and frequent: the session outlives the client
		 *      (invariant I4), so someone can paste **when no client is
		 *      attached**.  ⚠ Keeping quiet here would leave the pasting
		 *      application hanging indefinitely, and the symptom — "the
		 *      desktop has frozen" — names neither the clipboard nor the
		 *      detach.  ⇒ The timeout is not enough: the answer goes NOW. */
		if (!f->su_appunti_richiesta) {
			registro_dice(REG_FIGLIO,
			              "«%s» is pasting (request %u) and nobody serves "
			              "the clipboard: answering «I don't have it» at once, instead of "
			              "leaving the paster hanging",
			              g->utente, c.serial);
			figli_appunti_risposta(f, g->utente, c.serial, NULL, 0);
			return true;
		}
		f->su_appunti_richiesta(f->ctx_appunti, g->utente, g->uid, c.serial);
		return true;
	}
	case MSG_TELA: {
		struct corpo_tela c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		/* ⭐⭐ "WAIT" before anything else: it is not an answer, it is the news
		 *     that an answer is on its way.  ⛔ Treating it like the others
		 *     would fire the "did not make it" branch — that is precisely the
		 *     inference this message exists to remove. */
		if (c.attendi) {
			registro_dice(REG_FIGLIO,
			              "«%s»: the stage for the canvas %ux%u is NOT there YET — "
			              "the deadline of §7.1 is postponed",
			              g->utente, c.voluta_l, c.voluta_a);
			if (f->su_tela_attendi)
				f->su_tela_attendi(f->ctx_tela_attendi, g->utente, g->uid,
				                   c.voluta_l, c.voluta_a);
			return true;
		}
		/* ⛔⭐ §7.1 — THE ANSWER TO THE CANVAS, and the parent no longer GUESSES
		 *     it from the frames: it carries the size ASKED (to recognise which
		 *     request it answers) and the size OBTAINED (`0x0` = did not make
		 *     it).
		 * ⚠ The line is written here by the parent because it is the side that
		 *   decides: the child has already written its own, with the reason. */
		registro_dice(REG_FIGLIO,
		              c.avuta_l && c.avuta_a
		                  ? "«%s»: the stage answers the canvas — asked %ux%u, "
		                    "OBTAINED %ux%u"
		                  : "«%s»: the stage did NOT make it on the canvas %ux%u "
		                    "(%ux%u): the client will know now instead of after "
		                    "the deadline of §7.1",
		              g->utente, c.voluta_l, c.voluta_a, c.avuta_l, c.avuta_a);
		if (f->tela)
			f->tela(f->ctx, g->utente, g->uid, c.voluta_l, c.voluta_a, c.avuta_l,
			        c.avuta_a);
		return true;
	}
	default:
		registro_dice(REG_FIGLIO, "⚠ «%s» sent a type I do not know (%u)",
		              g->utente, t->tipo);
		return true;
	}
}

void figli_muovi(figli *f, struct pollfd *fds, size_t n, uint64_t ora_ms)
{
	if (!f)
		return;

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
	if (scatto_da_inoltrare) {
		int quale = scatto_da_inoltrare == 2 ? SIGUSR2 : SIGUSR1;

		scatto_da_inoltrare = 0;
		for (int i = 0; i < f->tetto; i++) {
			struct figlio *g = &f->v[i];

			if (!g->usato || g->uscendo || g->pid <= 0)
				continue;
			kill(g->pid, quale);
			registro_dice(REG_FIGLIO,
			              "⭐ trigger: %s forwarded to the child of «%s» (pid %ld)",
			              quale == SIGUSR2 ? "SIGUSR2" : "SIGUSR1", g->utente,
			              (long)g->pid);
		}
	}

	for (int i = 0; i < f->tetto; i++) {
		struct figlio *g = &f->v[i];
		bool leggibile = false;

		if (!g->usato)
			continue;

		for (size_t k = 0; k < n; k++)
			if (fds[k].fd == g->fd && (fds[k].revents & (POLLIN | POLLHUP)))
				leggibile = true;

		while (leggibile) {
			uint8_t busta[BUSTA_MAX];
			struct testa t;
			struct ucred chi;
			bool c_e = false;
			char perche[256];
			ssize_t letti = ricevi_con_credenziali(g->fd, busta, sizeof busta,
			                                       &chi, &c_e);

			if (letti == 0) {
				figlio_congeda(f, g, "closed the socket (or died)");
				break;
			}
			if (letti == -2) {
				/* ⛔ Before `errno`, and not after: `-2` is a fact of OURS
				 *    (message truncated by the kernel) and `errno` at that
				 *    point still carries the outcome of something else. */
				registro_dice(REG_FIGLIO,
				              "⛔ «%s» sent a message longer than "
				              "expected: DISCARDED",
				              g->utente);
				continue;
			}
			if (letti < 0) {
				if (errno == EINTR)
					continue;
				if (errno == EAGAIN || errno == EWOULDBLOCK)
					break;
				figlio_congeda(f, g, strerror(errno));
				break;
			}
			if ((size_t)letti < sizeof t) {
				registro_dice(REG_FIGLIO,
				              "⛔ «%s»: message of %zd bytes, too short for "
				              "a header: DISCARDED",
				              g->utente, letti);
				continue;
			}
			memcpy(&t, busta, sizeof t);
			if (!magia_giusta(&t)) {
				registro_dice(REG_FIGLIO,
				              "⛔ «%s»: message without the signature of this "
				              "protocol: DISCARDED",
				              g->utente);
				continue;
			}
			/* ⛔⭐ AND HERE, BEFORE LOOKING AT A SINGLE BYTE OF THE BODY. */
			perche[0] = 0;
			if (!credenziali_combaciano(g, &t, c_e, &chi, perche,
			                            sizeof perche)) {
				registro_dice(REG_FIGLIO,
				              "⛔⛔ MESSAGE REFUSED from «%s»: %s.  ⚠ It is not "
				              "just a message to throw away: it is the link "
				              "between the RCP session and the child's identity that "
				              "can no longer be proven — and a child running as "
				              "the wrong user is I3 violated "
				              "invisibly.  The child is killed.",
				              g->utente, perche);
				if (g->pid > 0)
					kill(g->pid, SIGKILL);
				figlio_congeda(f, g, "the kernel's credentials did not match");
				break;
			}
			if ((size_t)letti < sizeof t + t.byte) {
				registro_dice(REG_FIGLIO,
				              "⛔ «%s»: the header announces %u body bytes and "
				              "%zd arrived: DISCARDED",
				              g->utente, t.byte, letti - (ssize_t)sizeof t);
				continue;
			}
			if (!tratta(f, g, &t, busta + sizeof t, t.byte))
				break;
		}

		if (!g->usato)
			continue;

		/* ⛔⭐ THE DEAD ARE REAPED, AND IT IS NOT TIDINESS — `[M]` 12 Aug 2026,
		 *     from the helper: in `/proc` a zombie and a live process have **the
		 *     same face**, and a bench asking "is the child still alive?" would
		 *     get "yes" from a corpse.  ⛔ `WNOHANG`, because we are inside the
		 *     asynchronous loop (`CODER.md` §4.4). */
		if (g->pid > 0) {
			int stato = 0;
			pid_t chiuso = waitpid(g->pid, &stato, WNOHANG);
			if (chiuso == g->pid) {
				char detto[160];
				/* ⛔ THE CAUSE, not "it ended": whoever reads the log six
				 *    hours later must be able to tell a child that exited by
				 *    itself from one that somebody killed, and by which
				 *    signal.  ⚠ The child's exit codes are in
				 *    `figlio_vive()`: 42 = "I am not who I should be". */
				if (WIFEXITED(stato))
					snprintf(detto, sizeof detto, "exited with %d — %s",
					         WEXITSTATUS(stato),
					         perche_uscito(WEXITSTATUS(stato)));
				else if (WIFSIGNALED(stato))
					snprintf(detto, sizeof detto, "killed by signal %d",
					         WTERMSIG(stato));
				else
					snprintf(detto, sizeof detto, "ended (status %d)", stato);
				g->pid = 0;
				figlio_libera(f, g, detto);
				continue;
			}
			/* ⛔ And if it does not die, we insist — but only after having asked.
			 *    ⚠ A child that ignores `SIGTERM` while holding a user's virtual
			 *    monitor is an orphan in the making. */
			if (g->uscendo && ora_ms >= g->congedato_ms + 3000) {
				registro_dice(REG_FIGLIO,
				              "⛔ the child of «%s» (pid %ld) did not die within 3 s "
				              "of the farewell: SIGKILL",
				              g->utente, (long)g->pid);
				kill(g->pid, SIGKILL);
				g->congedato_ms = ora_ms;
			}
			/* ⚠ And while it is leaving nothing more is asked of it: the slot
			 *   stays its own until the kernel confirms. */
			if (g->uscendo)
				continue;
		}

		/* ⛔ The deadline of the INTRODUCTION, and only that one.  ⚠ After it,
		 *    none: I4 — the stage outlives the detach, and a silent child is a
		 *    child nobody is asking anything. */
		if (!g->si_e_presentato && ora_ms >= g->nato_ms + SCADENZA_SONO_MS) {
			registro_dice(REG_FIGLIO,
			              "⛔ the child of «%s» (pid %ld) did not say who it is within "
			              "%d ms: killing it.  A process running as a "
			              "user that does not answer is not a stage",
			              g->utente, (long)g->pid, SCADENZA_SONO_MS);
			if (g->pid > 0)
				kill(g->pid, SIGKILL);
			/* ⚠ No waiting here: the reaping belongs to the next round. */
			figlio_congeda(f, g, "did not introduce itself in time");
		}
	}
}

/* ⛔ How often the parent asks "who are you" again.  ⚠ One minute, and the
 * number is not caution: it is the maximum time for which a child that had
 * changed identity — or a pid recycled after a death we did not reap — would
 * stay in the table without anyone having put it to the test again. */
#define RICONTROLLO_MS 60000

void figli_ricontrolla(figli *f, uint64_t ora_ms)
{
	if (!f)
		return;
	for (int i = 0; i < f->tetto; i++) {
		struct figlio *g = &f->v[i];
		struct testa t;

		if (!g->usato || g->fd < 0 || !g->si_e_presentato)
			continue;
		if (ora_ms < g->ultimo_ricontrollo_ms + RICONTROLLO_MS)
			continue;
		g->ultimo_ricontrollo_ms = ora_ms;

		memset(&t, 0, sizeof t);
		magia_scrivi(&t);
		t.tipo = MSG_CHI_SEI;
		t.versione = FIGLIO_VERSIONE;
		t.matricola = g->matricola;
		t.uid_dichiarato = (uint32_t)g->uid;
		t.byte = 0;
		/* ⚠ If the question does not go out nothing is concluded: the absence
		 *   of an answer is not an answer, and the child stays where it is.
		 *   ⛔ What is NOT done is inferring from an `EAGAIN` that the child
		 *   is dead. */
		if (send(g->fd, &t, sizeof t, MSG_NOSIGNAL) != (ssize_t)sizeof t)
			registro_dettaglio(REG_FIGLIO,
			                   "the «who are you» question to «%s» did not go out (%s): "
			                   "retrying in a minute",
			                   g->utente, strerror(errno));
	}
}

bool figli_chiedi_palco(figli *f, const char *utente)
{
	struct figlio *g;
	struct testa t;

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;
	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_RIMANDA_PALCO;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	if (send(g->fd, &t, sizeof t, MSG_NOSIGNAL) != (ssize_t)sizeof t) {
		registro_dice(REG_FIGLIO,
		              "⚠ the stage request to «%s» did not go out (%s): "
		              "that session will see nothing, and this line is the "
		              "reason",
		              utente, strerror(errno));
		return false;
	}
	registro_dice(REG_FIGLIO,
	              "asked «%s» to send its stage again: the process deposit "
	              "belongs to whoever has just passed PAM",
	              utente);
	return true;
}

/* ⛔⭐ PHASE 3 — "CAPTURE, AND THIS ONE MUST BE A KEYFRAME".
 *
 *     It is the parent half of the seam that was missing.  ⚠ The one who
 *     decides is not this file — it knows nothing about RCP sessions — but
 *     `webtransport.c`, which knows when `SESSIONE` went out and when §5.2
 *     wants a keyframe.  `main.c` acts as the bridge, because it is the only
 *     one that knows both.
 *
 * ⛔ AND THE REQUEST IS REPEATED EVEN IF THE CODEC DOES NOT CHANGE, when the
 *    keyframe is asked for: a keyframe asked twice costs one big frame, a
 *    keyframe asked zero times costs **the screen frozen forever**.  The
 *    deadline that avoids the burst is on the other side
 *    (`WT_CHIAVE_RICHIESTA_MS`), where the session's clock is. */
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
 *    16 Aug 2026: the layout declared in `ATTACCA` was validated and WRITTEN
 *    IN THE LOG, and that was the end of it.  Reattaching to an `it` session
 *    declaring `us`, `è` and `ò` arrived, which on `us` do not exist on any
 *    key.
 *
 * ⭐ And the real damage is not the accent: shortcuts travel as POSITIONS
 *    (`SPECIFICHE.md` §7.3), and on a German keyboard `Z` sits where `Y` sits
 *    for us — without renegotiating, `Ctrl+Z` arrives as `Ctrl+Y`, that is
 *    "redo" instead of "undo". */
bool figli_disposizione(figli *f, const char *utente, const char *nome)
{
	struct figlio *g;
	struct testa t;
	struct corpo_disposizione c;
	uint8_t busta[sizeof t + sizeof c];

	if (!f || !utente || !nome || !*nome)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_DISPOSIZIONE;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	snprintf(c.nome, sizeof c.nome, "%s", nome);
	memcpy(busta, &t, sizeof t);
	memcpy(busta + sizeof t, &c, sizeof c);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		/* ⛔ `registro_dice` and not `dettaglio`: it happens once per attach,
		 *    and if it does not go out the user is left with misaligned
		 *    shortcuts — which is precisely the fault nobody connects. */
		registro_dice(REG_FIGLIO,
		              "⚠ the layout «%s» for «%s» did NOT go out: the "
		              "session keeps its own, and the shortcuts will stay "
		              "misaligned",
		              nome, utente);
		return false;
	}
	return true;
}

bool figli_input(figli *f, const char *utente, uint32_t id, uint8_t azione,
                 uint16_t codice, int premuto, int32_t a, int32_t b)
{
	struct figlio *g;
	struct testa t;
	struct corpo_input c;
	uint8_t busta[sizeof t + sizeof c];

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_INPUT;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.id = id;
	c.azione = azione;
	c.premuto = premuto ? 1u : 0u;
	c.codice = codice;
	c.a = a;
	c.b = b;
	memcpy(busta, &t, sizeof t);
	memcpy(busta + sizeof t, &c, sizeof c);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		/* ⛔ `registro_dettaglio` and not `registro_dice`: a user moving the
		 *    mouse produces dozens of messages per second, and one line for
		 *    each would bury the log precisely when it needs to be read.
		 *    ⚠ But it is NOT silenced: "the input did not reach the desktop"
		 *    is a fact, and it disappears only from the chatter. */
		registro_dettaglio(REG_FIGLIO,
		                   "⚠ input %u (action %u) for «%s» did not go out "
		                   "(%s): that gesture did NOT reach the desktop",
		                   (unsigned)id, (unsigned)azione, utente,
		                   strerror(errno));
		return false;
	}
	return true;
}

/* ⭐⭐ THE MISSING CHAIN — `figli_ritela()`, and from here on the name that
 *     `DECISIONI.md` §5.0-sexies and the mandate of phase 4 mention EXISTS.
 *
 * ⛔ IT IS ONE LINE AND IT DELEGATES, and both things are on purpose: the
 *    message on the wire between parent and child stays **one** (`MSG_INPUT`,
 *    action `RITELA`), so in the child there is only one branch to read.
 *    ⚠ A second envelope would have needed a second `struct corpo_*`, a second
 *    branch and a second way to get it wrong — to carry two numbers that the
 *    existing one already carries.
 *
 * ⛔ BUT THE NAME IS NOT COSMETIC, and it is not `figli_input()` with a strange
 *    action: input is a GESTURE already validated by §7.3 that is injected and
 *    forgotten; this is a request to **reconfigure the stage** whose outcome
 *    does not come back from here — it comes back with a frame, minutes later
 *    or never.  Two different jobs with two different names, and whoever
 *    reads `main.c` sees the whole chain.
 *
 * `false` = there is no child for that user, or the request did not go out
 * — ⛔ and then the canvas will NOT change, which is declared instead of
 * waiting for a frame that will not arrive (`CODER.md` §4.2). */
bool figli_ritela(figli *f, const char *utente, uint32_t larghezza,
                  uint32_t altezza)
{
	/* ⛔ `id = 0` and not the last input id: §6.2 reserves zero for "no
	 *    input", and this is not a user action on which the latency link
	 *    should measure anything. */
	return figli_input(f, utente, 0, FIGLI_INPUT_RITELA, 0, 0,
	                   (int32_t)larghezza, (int32_t)altezza);
}

/* ⭐ §7.6 — and it delegates to `figli_input()` like `figli_ritela()`, for the
 * same reason: a single envelope on the wire between parent and child.  ⛔ But
 * with its own name, because the jobs are two and whoever reads `main.c` must
 * see the chain. */
void figli_gancio_tela_attendi(figli *f, FiglioTelaAttendi fn, void *ctx)
{
	if (!f)
		return;
	f->su_tela_attendi = fn;
	f->ctx_tela_attendi = ctx;
}

void figli_gancio_blocco(figli *f, FiglioBlocco fn, void *ctx)
{
	if (!f)
		return;
	f->su_blocco = fn;
	f->ctx_blocco = ctx;
}

void figli_gancio_appunti(figli *f, FiglioAppuntiTesto testo,
                          FiglioAppuntiRichiesta richiesta, void *ctx)
{
	if (!f)
		return;
	/* ⛔ Together or not at all (`figlio.h`): whoever hooked only `testo`
	 *    could carry to the client what the session copies and could not
	 *    serve whoever pastes — and that "could not" shows up as a frozen
	 *    desktop.  ⇒ It is declared and nothing is hooked, instead of hooking
	 *    half a channel. */
	if ((testo != NULL) != (richiesta != NULL)) {
		registro_dice(REG_FIGLIO,
		              "⛔ the two clipboard hooks are attached together or not "
		              "at all, and only one arrived (%s): I am attaching "
		              "neither",
		              testo ? "the one serving whoever pastes is missing"
		                    : "the one carrying the text to the client is missing");
		return;
	}
	f->su_appunti_testo = testo;
	f->su_appunti_richiesta = richiesta;
	f->ctx_appunti = ctx;
}

bool figli_appunti_offri(figli *f, const char *utente)
{
	struct figlio *g;
	struct testa t;
	uint8_t busta[sizeof t];

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_APPUNTI_OFFERTA;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = 0;
	memcpy(busta, &t, sizeof t);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		registro_dice(REG_FIGLIO,
		              "⚠ the clipboard offer to «%s» did not go out (%s): "
		              "inside that session it will not be possible to paste what "
		              "the client copied, and this line is the reason",
		              utente, strerror(errno));
		return false;
	}
	registro_dettaglio(REG_FIGLIO,
	                   "«%s»: the client's text offered to the session (§7.4)",
	                   utente);
	return true;
}

bool figli_appunti_risposta(figli *f, const char *utente, uint32_t serial,
                            const char *testo, size_t byte)
{
	struct figlio *g;
	size_t off = 0;

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;

	/* ⛔ The cap is enforced in THIS direction too, and the reason is
	 *    different from that of §5.4: here the text comes from the **client**,
	 *    that is from outside.  ⚠ `rcp.c` has already refused it on the wire;
	 *    this is the second door, the one protecting the child from a parent
	 *    with a defect. */
	if (testo && byte > APPUNTI_TETTO) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: %zu bytes of clipboard from the client, over the cap "
		              "of §5.4 (%u): answering «I don't have it» instead of truncating",
		              utente, byte, APPUNTI_TETTO);
		testo = NULL;
		byte = 0;
	}

	/* ⛔ The "nothing" case and the "empty text" case go down different roads,
	 *    and the difference reaches Mutter: `SelectionWriteDone(false)` versus
	 *    a descriptor opened and closed without bytes.  ⚠ Whoever pastes sees
	 *    "there was nothing to paste" in the first case and an empty line in
	 *    the second, which are two different things. */
	do {
		struct testa t;
		struct corpo_appunti c;
		uint8_t busta[sizeof t + sizeof c + PEZZO_MAX];
		size_t q = 0;

		if (testo) {
			q = byte - off;
			if (q > PEZZO_MAX)
				q = PEZZO_MAX;
		}

		memset(&t, 0, sizeof t);
		magia_scrivi(&t);
		t.tipo = MSG_APPUNTI_DAL_CLIENT;
		t.versione = FIGLIO_VERSIONE;
		t.matricola = g->matricola;
		t.uid_dichiarato = (uint32_t)g->uid;
		t.byte = (uint32_t)(sizeof c + q);
		memset(&c, 0, sizeof c);
		c.serial = serial;
		c.totale = testo ? (uint32_t)byte : 0;
		c.offset = (uint32_t)off;
		c.pezzo = (uint32_t)q;
		c.niente = testo ? 0 : 1;
		memcpy(busta, &t, sizeof t);
		memcpy(busta + sizeof t, &c, sizeof c);
		if (q)
			memcpy(busta + sizeof t + sizeof c, testo + off, q);
		if (send(g->fd, busta, sizeof t + sizeof c + q, MSG_NOSIGNAL)
		    != (ssize_t)(sizeof t + sizeof c + q)) {
			/* ⛔⛔ AND THIS IS THE CASE THAT LEAVES THE PASTER HANGING, so the
			 *      line is plain and says the symptom: without it, the defect
			 *      would be sought in the desktop instead of in a full socket. */
			registro_dice(REG_FIGLIO,
			              "⛔ «%s»: the clipboard answer (request %u, %zu "
			              "of %zu bytes) did not go out (%s).  ⚠ The application "
			              "that is pasting stays hanging until the child "
			              "reaches the end of its timeout",
			              utente, serial, off, byte, strerror(errno));
			return false;
		}
		off += q;
	} while (testo && off < byte);

	registro_dettaglio(REG_FIGLIO,
	                   "«%s»: clipboard answer (request %u) — %s",
	                   utente, serial,
	                   testo ? "delivered" : "«I don't have it»");
	return true;
}

void figli_gancio_sessione_finita(figli *f, FiglioSessioneFinita fn, void *ctx)
{
	if (!f)
		return;
	f->su_sessione_finita = fn;
	f->ctx_sessione_finita = ctx;
}

bool figli_termina_sessione(figli *f, const char *utente, int perche)
{
	/* ⛔ The `perche` travels in field `a`, which was free: the reason is on
	 *    `FIGLI_USCITA_*` in `figlio.h`. */
	return figli_input(f, utente, 0, FIGLI_INPUT_TERMINA, 0, 0, perche, 0);
}

bool figli_audio(figli *f, const char *utente, uint8_t codec)
{
	struct figlio *g;
	struct testa t;
	struct corpo_audio c;
	uint8_t busta[sizeof t + sizeof c];

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
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
	if (codec == g->audio_codec_chiesto && codec == 0)
		return true; /* off, and stays off: there is nothing to say */

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_AUDIO;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.codec = codec;
	memcpy(busta, &t, sizeof t);
	memcpy(busta + sizeof t, &c, sizeof c);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		registro_dice(REG_FIGLIO,
		              "⚠ the audio request to «%s» (codec %u) did not go out "
		              "(%s): that session will hear nothing, and this line "
		              "is the reason",
		              utente, codec, strerror(errno));
		return false;
	}
	registro_dice(REG_FIGLIO,
	              codec ? "⭐ PHASE 7: asked the session of «%s» to "
	                      "capture audio, codec %u (%s)"
	                    : "asked the session of «%s» to STOP "
	                      "capturing audio (codec %u): nobody is listening "
	                      "any more, and the sink stays up (I4)",
	              utente, codec,
	              codec == 1 ? "Opus" : codec == 2 ? "PCM" : "-");
	g->audio_codec_chiesto = codec;
	return true;
}

bool figli_video(figli *f, const char *utente, uint8_t codec,
                 uint8_t profondita, uint8_t livello_x10, bool chiave)
{
	struct figlio *g;
	struct testa t;
	struct corpo_video c;
	uint8_t busta[sizeof t + sizeof c];

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
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
	if (codec == g->video_codec_chiesto && profondita == g->video_prof_chiesta
	    && livello_x10 == g->video_liv_chiesto && !chiave)
		return true; /* nothing new to say */

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_VIDEO;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.codec = codec;
	c.chiave = chiave ? 1u : 0u;
	c.profondita = profondita;
	c.livello_x10 = livello_x10;
	memcpy(busta, &t, sizeof t);
	memcpy(busta + sizeof t, &c, sizeof c);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		registro_dice(REG_FIGLIO,
		              "⚠ the video request to «%s» (codec %u, keyframe %s) did "
		              "not go out (%s): that session will see nothing, and "
		              "this line is the reason",
		              utente, codec, chiave ? "YES" : "no", strerror(errno));
		return false;
	}
	if (codec != g->video_codec_chiesto)
		registro_dice(REG_FIGLIO,
		              codec ? "⭐ PHASE 3: asked the stage of «%s» to "
		                      "capture continuously, codec %u%s"
		                    : "asked the stage of «%s» to STOP "
		                      "capturing (codec %u): nobody is watching it "
		                      "any more%s",
		              utente, codec, chiave ? " — and the first must be a "
		                                      "KEYFRAME (§5.2)" : "");
	g->video_codec_chiesto = codec;
	g->video_prof_chiesta = profondita;
	g->video_liv_chiesto = livello_x10;
	return true;
}

void figli_spegni(figli *f)
{
	if (!f)
		return;
	for (int i = 0; i < f->tetto; i++) {
		struct figlio *g = &f->v[i];
		if (!g->usato)
			continue;
		/* ⛔ First the socket is closed — which is the most honest signal,
		 *    "there is nobody left to talk to" — and then we insist with the
		 *    signal. */
		if (g->fd >= 0) {
			close(g->fd);
			g->fd = -1;
		}
		if (g->pid > 0) {
			kill(g->pid, SIGTERM);
			/* ⚠ It WAITS, and it is outside the `poll` loop: `CODER.md` §4.4
			 *   forbids waiting INSIDE the loop, and this is the line after the
			 *   last round.  ⛔ The stage must be dismantled before the process
			 *   exits, or the virtual monitor would stay attached to the user's
			 *   session. */
			waitpid(g->pid, NULL, 0);
		}
		registro_dice(REG_FIGLIO, "the child of «%s» (pid %ld) is shut down",
		              g->utente, (long)g->pid);
		free(g->monta);
		free(g->cur_monta);
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
 * ⛔ `input_iniettato` is the `id` of the last input the COMPOSITOR TOOK — not
 *    the last received, not the last attempted.  §6.2 promises that "the
 *    effect of that input is already in the scene", and of a refused input
 *    there is no effect to see.  ⇒ It advances only when `input.c` has
 *    answered 0. */
static Input *palco_input;
/* ⭐ §5-bis.7: the layout requested when the stage was not there yet.
 *    ⛔ Empty = nothing pending.  It is applied as soon as `input_apri()`
 *    succeeds. */
static char disposizione_in_attesa[65];
static uint32_t input_iniettato;
static uint32_t input_rifiutati;
static uint32_t input_non_producibili;
/* ⭐ 24 Sep 2026 — where the pointer is, for the shape PROBE on labwc
 *    (`cattura_sonda_puntatore`): a button carries no coordinates, but it can
 *    change the shape (grabbing the title bar), and it is probed here. */
static uint32_t sonda_x, sonda_y;
static bool sonda_nota;

/* ⭐⭐ PHASE 7 — THE SESSION'S CLIPBOARD, and it lives on this side for the
 *     same reason as `palco_input`: the clipboard belongs to the compositor,
 *     and this process is the one talking to the compositor
 *     (`src/appunti.h`). */
static Appunti *palco_appunti;

/* ⭐ PHASE 12, INCREMENT 2 — the stage on KDE.  On GNOME it stays NULL and
 *    the `MutterSessione` does everything as before; on KDE `mut` stays NULL
 *    and the PipeWire node is given by KWin (`kwin.h`).  ⚠ One per child, like
 *    the other two above: a child has only one stage. */
static KwinSessione *palco_kwin;

static void chiudi_palco_kwin(void)
{
	if (palco_kwin) {
		kwin_chiudi(palco_kwin);
		palco_kwin = NULL;
	}
}

/* The stage's PipeWire node, whoever it comes from. */
static uint32_t nodo_del_palco(const MutterSessione *m)
{
	return m ? mutter_nodo(m) : kwin_nodo(palco_kwin);
}

/*
 * ⛔⭐ THE SIZE TO ASK OF THE CAPTURE, ON KDE, IS THAT OF KWIN'S OUTPUT.
 *
 * On GNOME Mutter makes a NEW monitor of the requested size (`RecordVirtual`).
 * On KDE the output `Virtual-0` is born with the session, at the size of the
 * FIRST client (increment 1, CP2), and KWin 6.3.6 does not resize it live
 * (`kwin!7932`, expected for 6.8 — `LEZIONI.md` of v1).  `[M]` 18 Sep 2026:
 * asking 1384x912 of an output of 1388x914 ⇒ `no more input formats`, and the
 * stage NEVER mounts again — the session stays in the dark.
 * ⇒ On KDE the output is captured as it is, and the page rescales: that is
 *   what §4.5 of the protocol provides when the canvas granted is not the one
 *   requested.
 * On GNOME this function changes nothing.
 */
static void misura_del_palco(uint32_t *l, uint32_t *a)
{
	uint32_t kl = 0, ka = 0;

	if (!palco_kwin)
		return;
	kwin_misura(palco_kwin, &kl, &ka);
	if (!kl || !ka || (kl == *l && ka == *a))
		return;
	registro_dice(REG_FIGLIO,
	              "⚠ the requested canvas is %ux%u but KWin's output is %ux%u, and KWin "
	              "does not resize it: capturing %ux%u and the page rescales (§4.5)",
	              *l, *a, kl, ka, kl, ka);
	*l = kl;
	*a = ka;
}

/* ⛔⛔⭐ THE OFFER THAT ARRIVED TOO EARLY, AND IS REDONE — 21 Aug 2026, defect
 *      measured with bench `07-b56`.
 *
 * ⚠ The client announces its clipboard as soon as the `SESSIONE` is born; the
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
 *    (`appunti_chiedi_l_arretrato`): instead of delaying something for
 *    everyone, ONE bit is kept and the seam is stitched. */
static bool appunti_offerta_arretrata;

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
 * ⚠ The parent answers AT ONCE when it already knows it cannot serve (no hook
 *   attached): this timeout covers the other case — the client is there and
 *   does not answer.
 */
#define APPUNTI_ATTESA_MS 4000
#define APPUNTI_IN_VOLO 8
static struct {
	bool usato;
	uint32_t serial;
	uint64_t scade_ms;
} appunti_in_volo[APPUNTI_IN_VOLO];

static int fd_figlio = 3; /* the agreed place, put there by `diventa_ed_esegui` */
static uint64_t mia_matricola;
static uid_t mio_uid;

/* How many descriptors I really have open.  ⛔ They are COUNTED, not
 * declared: it is the half of the bench that lives in the product — "the
 * child did not carry the port along" must be a number, not a promise. */
static uint32_t quanti_descrittori(void)
{
	uint32_t n = 0;
	for (int i = 0; i < 4096; i++)
		if (fcntl(i, F_GETFD) >= 0)
			n++;
	return n;
}

static bool manda(uint16_t tipo, const void *corpo, size_t byte,
                  const void *coda, size_t byte_coda)
{
	uint8_t busta[BUSTA_MAX];
	struct testa t;
	size_t n = 0;

	if (sizeof t + byte + byte_coda > sizeof busta)
		return false;
	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = tipo;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = mia_matricola;
	/* ⛔ The uid is ASKED OF THE KERNEL on every message, and not read from a
	 *    variable written at startup: the variable would say what we believed
	 *    we were, and the parent will compare this field with what the kernel
	 *    stamped.  ⚠ If the two did not match, the parent kills — and rightly
	 *    so: a child that no longer knows who it is must not deliver pixels. */
	t.uid_dichiarato = (uint32_t)geteuid();
	t.byte = (uint32_t)(byte + byte_coda);
	memcpy(busta, &t, sizeof t);
	n = sizeof t;
	if (byte) {
		memcpy(busta + n, corpo, byte);
		n += byte;
	}
	if (byte_coda) {
		memcpy(busta + n, coda, byte_coda);
		n += byte_coda;
	}
	return send(fd_figlio, busta, n, MSG_NOSIGNAL) == (ssize_t)n;
}

/* ⛔⭐ THE CANVAS THE CLIENT ASKED FOR, kept apart from the one the stage
 *     GIVES.  They are two different numbers and serve two different things:
 *
 *       `tela_voluta_*`  what the client wants ⇒ it is what is requested on
 *                        REMOUNTING the stage, or the bands would come back
 *                        after every fall of the graphical session;
 *       `tela_l`/`tela_a` what the stage delivers ⇒ it is what ends up in the
 *                        28 bytes of §6.2, and it is not invented.
 *
 * ⚠ They are born equal (the size from the command line) and diverge at the
 *   first `ADATTA_TELA` that the compositor does not serve to the letter
 *   (§4.5). */
static uint32_t tela_voluta_l, tela_voluta_a;

/* The answer of §7.1 to the parent.  ⛔ `avuta_l == 0` = "I did not make it",
 * and it is a different fact from "I am trying": without this line the parent
 * would wait to the end of the three seconds to learn something known here at
 * once. */
/* ⭐ "WAIT": the stage is not there YET, and the question will get a real
 * answer.  ⛔ It is not `0x0` — that is "I did not make it" — and it is the
 *    message that takes an inference away from the parent (`LEZIONI.md` §7.5). */
static void attendi_tela(uint32_t voluta_l, uint32_t voluta_a)
{
	struct corpo_tela c;
	memset(&c, 0, sizeof c);
	c.voluta_l = voluta_l;
	c.voluta_a = voluta_a;
	c.attendi = 1;
	if (!manda(MSG_TELA, &c, sizeof c, NULL, 0))
		registro_dice(REG_FIGLIO,
		              "⛔ the «wait» on the canvas (%ux%u) did not go out (%s): the "
		              "parent will let the deadline of §7.1 expire on a question that "
		              "was about to get an answer",
		              voluta_l, voluta_a, strerror(errno));
}

static void rispondi_tela(uint32_t voluta_l, uint32_t voluta_a, uint32_t avuta_l,
                          uint32_t avuta_a)
{
	struct corpo_tela c;
	memset(&c, 0, sizeof c);
	c.voluta_l = voluta_l;
	c.voluta_a = voluta_a;
	c.avuta_l = avuta_l;
	c.avuta_a = avuta_a;
	if (!manda(MSG_TELA, &c, sizeof c, NULL, 0))
		registro_dice(REG_FIGLIO,
		              "⛔ the answer on the canvas (%ux%u → %ux%u) did not go out "
		              "(%s): the parent will wait for the deadline of §7.1 instead of "
		              "knowing it now",
		              voluta_l, voluta_a, avuta_l, avuta_a, strerror(errno));
}

static void manda_fotogramma(uint8_t codec, bool chiave, uint32_t l, uint32_t a,
                             uint64_t istante_us, const uint8_t *dati, size_t byte,
                             uint32_t input)
{
	size_t off = 0;
	while (off < byte) {
		struct corpo_fotogramma c;
		size_t q = byte - off;
		if (q > PEZZO_MAX)
			q = PEZZO_MAX;
		memset(&c, 0, sizeof c);
		c.codec = codec;
		c.chiave = chiave ? 1u : 0u;
		c.larghezza = l;
		c.altezza = a;
		c.istante_us = istante_us;
		c.totale = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.pezzo = (uint32_t)q;
		/* ⭐ §6.2 — and the value comes FROM THE INSTANT OF CAPTURE, not from
		 *    here: between capture and this line the whole encoding passes, and
		 *    reading it now would give a number higher than the real one. */
		c.input = input;
		if (!manda(MSG_FOTOGRAMMA, &c, sizeof c, dati + off, q)) {
			registro_dice(REG_FIGLIO,
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
 * ⛔ This is the `CursoreArrivata` of `cursore.h`, and `cattura.c` calls it
 *    **from the PipeWire thread**.  ⚠ So it does NOT touch any of the loop's
 *    state and does not allocate: it takes the bytes, splits them and sends
 *    them.  A `malloc` in here would be a `malloc` on the capture's real-time
 *    thread.
 *
 * ⚠ And the image lives ONLY inside the call (`cursore.h` says so): it is
 *   copied into the envelope and no pointer to it is kept.
 *
 * Returns 0: from here on the shape belongs to the parent, and the child has
 * no way of knowing whether the client received it — ⛔ saying otherwise would
 * be faking a confirmation that does not exist. */
static int cursore_al_padre(void *chi, const CursoreForma *f)
{
	size_t byte, off = 0;

	(void)chi;
	if (!f)
		return -1;
	byte = (size_t)f->larghezza * f->altezza * 4u;
	/* ⭐ The hidden one is `0x0` with the image NULL, and it must be sent **as
	 *    a message**: it is the only way the client has of knowing the pointer
	 *    has vanished, instead of drawing the last shape forever (§5.5). */
	if (byte == 0) {
		struct corpo_cursore c;
		memset(&c, 0, sizeof c);
		c.larghezza = f->larghezza;
		c.altezza = f->altezza;
		c.attivo_x = f->attivo_x;
		c.attivo_y = f->attivo_y;
		return manda(MSG_CURSORE, &c, sizeof c, NULL, 0) ? 0 : -1;
	}
	if (!f->immagine)
		return -1;
	while (off < byte) {
		struct corpo_cursore c;
		size_t q = byte - off;
		if (q > PEZZO_MAX)
			q = PEZZO_MAX;
		memset(&c, 0, sizeof c);
		c.larghezza = f->larghezza;
		c.altezza = f->altezza;
		c.attivo_x = f->attivo_x;
		c.attivo_y = f->attivo_y;
		c.totale = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.pezzo = (uint32_t)q;
		if (!manda(MSG_CURSORE, &c, sizeof c, f->immagine + off, q)) {
			/* ⛔ In chatter, and for a precise reason: the cursor changes shape
			 *    dozens of times while the pointer crosses a window, and one
			 *    line for each would cover the log.
			 *    ⚠ But it is NOT silenced: a shape lost halfway leaves the
			 *    client with the previous cursor, which is a visible defect. */
			registro_dettaglio(REG_FIGLIO,
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
/* ⛔⛔ AND THEY RUN ON THE CLIPBOARD THREAD, not on this loop — `appunti.h`,  */
/*      "the thread contract".  ⇒ In here it is allowed to WRITE TO THE       */
/*      SOCKET (a `send` on SEQPACKET is atomic per message) and NOTHING ELSE: */
/*      ⛔ `libei` is not reentrant (`input.h`), and the table of transfers   */
/*      in flight is touched only by this thread — see below.                 */

/* ⛔ The table is written by TWO threads: the clipboard one, which puts the
 *    serials in, and the child's loop, which expires them.  ⚠ A lock for an
 *    eight-entry table costs less than a defect that shows up once every
 *    thousand pastes. */
static pthread_mutex_t appunti_lucchetto = PTHREAD_MUTEX_INITIALIZER;

static void appunti_dalla_sessione(const char *testo, size_t byte, void *dati)
{
	size_t off = 0;

	(void)dati;

	/* ⚠ The cap has already been enforced by `appunti.c`, which is where the
	 *   text exists whole.  ⛔ This line is NOT a duplicate: it is the promise
	 *   that `monta_appunti()` on the other side never receives a `totale` it
	 *   would refuse — that is, that the defect, if there were one, shows
	 *   **here** and not as a text vanished without explanation. */
	if (byte > APPUNTI_TETTO) {
		registro_dice(REG_APPUNTI,
		              "⛔ %zu bytes over the cap of §5.4 (%u) got "
		              "this far: they are NOT sent.  ⚠ If this line appears, "
		              "the check in `appunti.c` has a hole",
		              byte, APPUNTI_TETTO);
		return;
	}

	do {
		struct corpo_appunti c;
		size_t q = byte - off;

		if (q > PEZZO_MAX)
			q = PEZZO_MAX;
		memset(&c, 0, sizeof c);
		c.serial = 0; /* the session copied, it did not ask */
		c.totale = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.pezzo = (uint32_t)q;
		if (!manda(MSG_APPUNTI_DALLA_SESSIONE, &c, sizeof c,
		           q ? testo + off : NULL, q)) {
			/* ⛔ Plain and not in detail: a copied text that does not reach the
			 *    client is a fact the user SEES — pastes on the phone and finds
			 *    what was there before.  ⚠ It is also the case in which
			 *    silence most resembles working. */
			registro_dice(REG_APPUNTI,
			              "⛔ the piece at %zu of %zu bytes did not go out to the "
			              "parent (%s): what the session copied will NOT "
			              "reach the client",
			              off, byte, strerror(errno));
			return;
		}
		off += q;
	} while (off < byte);
}

static void appunti_vuole_incollare(uint32_t serial, void *dati)
{
	struct corpo_appunti c;
	uint64_t adesso = registro_ora_ms();
	int posto = -1;

	(void)dati;

	pthread_mutex_lock(&appunti_lucchetto);
	for (int i = 0; i < APPUNTI_IN_VOLO; i++)
		if (!appunti_in_volo[i].usato) {
			posto = i;
			break;
		}
	if (posto >= 0) {
		appunti_in_volo[posto].usato = true;
		appunti_in_volo[posto].serial = serial;
		appunti_in_volo[posto].scade_ms = adesso + APPUNTI_ATTESA_MS;
	}
	pthread_mutex_unlock(&appunti_lucchetto);

	/* ⛔ The table is full: «I don't have it» is answered AT ONCE instead of
	 *    adding a debt nobody will expire.  ⚠ Eight pastes together is not a
	 *    normal case — if this line appears, either someone is holding down
	 *    Ctrl+V, or the answers are not coming back. */
	if (posto < 0) {
		registro_dice(REG_APPUNTI,
		              "⛔ already %d paste requests in flight: request %u is closed "
		              "at once with «I don't have it», instead of staying without "
		              "an answer",
		              APPUNTI_IN_VOLO, serial);
		appunti_rispondi(palco_appunti, serial, NULL, 0);
		return;
	}

	memset(&c, 0, sizeof c);
	c.serial = serial;
	if (!manda(MSG_APPUNTI_VUOLE, &c, sizeof c, NULL, 0)) {
		/* ⛔ It did not go out: the answer goes NOW, without waiting for the
		 *    timeout.  The timeout is for whoever does not answer; here we
		 *    already know that nobody will. */
		registro_dice(REG_APPUNTI,
		              "⛔ the paste request %u did not go out to the "
		              "parent (%s): answering «I don't have it» at once, or the paster "
		              "stays hanging",
		              serial, strerror(errno));
		pthread_mutex_lock(&appunti_lucchetto);
		appunti_in_volo[posto].usato = false;
		pthread_mutex_unlock(&appunti_lucchetto);
		appunti_rispondi(palco_appunti, serial, NULL, 0);
	}
}

/* Whoever was in flight and got no answer within the timeout: it is answered
 * empty-handed.  ⛔ Runs on the child's loop, on every round of `poll`. */
static void appunti_scadi(uint64_t adesso)
{
	uint32_t scaduti[APPUNTI_IN_VOLO];
	int quanti = 0;

	pthread_mutex_lock(&appunti_lucchetto);
	for (int i = 0; i < APPUNTI_IN_VOLO; i++)
		if (appunti_in_volo[i].usato && adesso >= appunti_in_volo[i].scade_ms) {
			scaduti[quanti++] = appunti_in_volo[i].serial;
			appunti_in_volo[i].usato = false;
		}
	pthread_mutex_unlock(&appunti_lucchetto);

	/* ⛔ Outside the lock: `appunti_rispondi` makes synchronous D-Bus calls,
	 *    and holding it while waiting for the bus would block the clipboard
	 *    thread on every new signal. */
	for (int i = 0; i < quanti; i++) {
		registro_dice(REG_APPUNTI,
		              "⚠ no answer from the client for request %u within "
		              "%d ms: closing with «I don't have it».  ⛔ The paster sees an "
		              "empty paste, which is much better than a hung "
		              "desktop",
		              scaduti[i], APPUNTI_ATTESA_MS);
		appunti_rispondi(palco_appunti, scaduti[i], NULL, 0);
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
	bool aperto;
	uint32_t serial;
	uint8_t *dati;
	size_t totale, avuti;
} appunti_montaggio;

static void appunti_montaggio_libera(void)
{
	free(appunti_montaggio.dati);
	appunti_montaggio.dati = NULL;
	appunti_montaggio.aperto = false;
	appunti_montaggio.totale = appunti_montaggio.avuti = 0;
}

static bool appunti_riscuoti(uint32_t serial);

static void appunti_dal_client(const struct corpo_appunti *c, const uint8_t *dati)
{
	/* ⛔ "I don't have it" arrives as a FIELD, not as a zero length: an empty
	 *    text is a legitimate and different fact.  ⇒ Two roads, and two
	 *    different calls towards Mutter. */
	if (c->niente) {
		appunti_montaggio_libera();
		if (appunti_riscuoti(c->serial))
			appunti_rispondi(palco_appunti, c->serial, NULL, 0);
		else
			registro_dettaglio(REG_APPUNTI,
			                   "«I don't have it» for request %u, which is no "
			                   "longer in flight: already expired, and Mutter has already "
			                   "had its answer",
			                   c->serial);
		return;
	}

	if (c->totale > APPUNTI_TETTO) {
		registro_dice(REG_APPUNTI,
		              "⛔ the parent announces %u bytes of clipboard, over the cap "
		              "of §5.4 (%u): answering «I don't have it» instead of truncating",
		              c->totale, APPUNTI_TETTO);
		appunti_montaggio_libera();
		if (appunti_riscuoti(c->serial))
			appunti_rispondi(palco_appunti, c->serial, NULL, 0);
		return;
	}

	if (c->offset == 0) {
		appunti_montaggio_libera();
		appunti_montaggio.dati = (uint8_t *)malloc((size_t)c->totale + 1u);
		if (!appunti_montaggio.dati) {
			registro_dice(REG_APPUNTI,
			              "⛔ %u bytes of clipboard from the client do not fit in "
			              "memory: answering «I don't have it»",
			              c->totale);
			if (appunti_riscuoti(c->serial))
				appunti_rispondi(palco_appunti, c->serial, NULL, 0);
			return;
		}
		appunti_montaggio.aperto = true;
		appunti_montaggio.serial = c->serial;
		appunti_montaggio.totale = c->totale;
		appunti_montaggio.avuti = 0;
	}

	/* ⛔ In order, of the same transfer, and of the same size.  A piece that
	 *    does not add up throws everything away and ANSWERS: leaving the
	 *    assembly open halfway would mean a `SelectionTransfer` waiting for
	 *    the timeout for nothing. */
	if (!appunti_montaggio.aperto || c->serial != appunti_montaggio.serial
	    || c->offset != appunti_montaggio.avuti
	    || c->totale != appunti_montaggio.totale
	    || (uint64_t)c->offset + c->pezzo > c->totale) {
		registro_dice(REG_APPUNTI,
		              "⛔ clipboard piece out of place (request %u, offset %u "
		              "of %u): dropping the whole text and answering «I don't have it»",
		              c->serial, c->offset, c->totale);
		appunti_montaggio_libera();
		if (appunti_riscuoti(c->serial))
			appunti_rispondi(palco_appunti, c->serial, NULL, 0);
		return;
	}

	memcpy(appunti_montaggio.dati + c->offset, dati, c->pezzo);
	appunti_montaggio.avuti += c->pezzo;
	if (appunti_montaggio.avuti < appunti_montaggio.totale)
		return;

	appunti_montaggio.dati[appunti_montaggio.totale] = 0;
	/* ⛔ It is collected BEFORE answering: if the serial is no longer in
	 *    flight, the timeout has already closed it with Mutter, and a second
	 *    `SelectionWriteDone` on the same transfer is a message Mutter is no
	 *    longer waiting for. */
	if (appunti_riscuoti(appunti_montaggio.serial)) {
		registro_dice(REG_APPUNTI,
		              "⭐ %zu bytes from the client delivered to whoever is pasting "
		              "(request %u)",
		              appunti_montaggio.totale, appunti_montaggio.serial);
		appunti_rispondi(palco_appunti, appunti_montaggio.serial,
		                 (const char *)appunti_montaggio.dati,
		                 appunti_montaggio.totale);
	} else {
		registro_dice(REG_APPUNTI,
		              "⚠ the text for request %u arrived AFTER the timeout "
		              "of %d ms: it is dropped, because Mutter has already had its "
		              "answer.  ⛔ Whoever pasted saw an empty "
		              "paste, and that is the declared price of the timeout",
		              appunti_montaggio.serial, APPUNTI_ATTESA_MS);
	}
	appunti_montaggio_libera();
}

/* Was the serial really among those in flight?  ⛔ Removing it from the table
 * and serving it are one thing only, and they live here together: a serial
 * served and left in the table would be expired later, and Mutter would
 * receive **two** `SelectionWriteDone` for the same transfer. */
static bool appunti_riscuoti(uint32_t serial)
{
	bool c_era = false;

	pthread_mutex_lock(&appunti_lucchetto);
	for (int i = 0; i < APPUNTI_IN_VOLO; i++)
		if (appunti_in_volo[i].usato && appunti_in_volo[i].serial == serial) {
			appunti_in_volo[i].usato = false;
			c_era = true;
			break;
		}
	pthread_mutex_unlock(&appunti_lucchetto);
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
 *   (`FASI.md` §02-primo-fotogramma), and recapturing here would mean
 *   delivering two different images under the same label.  ⛔ The frame loop
 *   belongs to phase 3. */
static uint8_t *tenuto[3];
static size_t tenuto_byte[3];
static bool tenuto_chiave[3];
static uint32_t tenuto_l, tenuto_a;
static uint64_t tenuto_istante;
/* ⛔ And the KEPT frame carries its `input` too, the one from the instant it
 *    was captured — not the current one.  ⚠ Sending it again with the current
 *    number would tell whoever comes back that an input just arrived is
 *    already in the scene of an image frozen for minutes: and the latency
 *    link would read it as a very low latency.  It is the same reason **the
 *    same** frame is sent again and not a new one. */
static uint32_t tenuto_input;

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
/*    `cattura_avvia()` asked for 60 and the encoding request declared 30: two */
/*    different numbers for the same quantity, harmless only as long as a     */
/*    single frame was encoded.  ⇒ `MOVIMENTO_FPS`, declared here and used in  */
/*    both places.  ⭐ The value is **60** and not 30 because it is the        */
/*    desired one of `SPECIFICHE.md` §3.1, and because `LEZIONI.md` §6.1 says  */
/*    that the number asked of the capture IS the ceiling: asking for 30, 18  */
/*    arrive; asking for 60, 37 arrive.  A ceiling we put there ourselves is   */
/*    not a measure of the machine.                                            */
#define MOVIMENTO_FPS 60

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
 *    (`DECISIONI.md` §2.3-ter).
 *
 * ⛔⛔ AND IT HOLDS **ONLY IF THE ENCODER IS IN HARDWARE**: in software there is
 *      no pixel to read.  ⇒ The route is chosen first, and if the encoder
 *      falls back to the CPU the stage is REMOUNTED on memory, declaring it —
 *      see `scheda_da_abbandonare`.
 *
 * ⚠ And the TEN BITS do not come back through this door: Mutter delivers BGRx,
 *   eight bits per channel, on the card as in memory (`cattura.h`).  This
 *   route changes where the frame is, not what is inside it.
 *
 * ⭐ It can be overridden from the compile line (`-DCOPIA_ZERO=0`), and it
 *    serves ONE thing only: rebuilding the **before** with the same source as
 *    the after, for the alternating A/B comparison.  ⛔ It is not a product
 *    switch and does not become one: the product has a single value, the one
 *    below (`CODER.md` invariant I7).
 * ═══════════════════════════════════════════════════════════════════════════ */
#ifndef COPIA_ZERO
#define COPIA_ZERO 1
#endif

/* The route asked of the producer at the next mounting of the stage.
 * ⛔ It is a variable and not a constant because it can STEP BACK once: when
 *    it turns out that this machine's encoder is in software.
 *    ⚠ It never goes forward again by itself: going forward would mean
 *    retrying a route already measured impossible, at every remount. */
static CatturaStrada strada_del_palco =
    COPIA_ZERO ? CATTURA_STRADA_SCHEDA : CATTURA_STRADA_MEMORIA;
/* ⛔ THE THREE REMOUNT STATES, and they are three because they answer three
 *    different questions.  ⚠ None of them remounts anything by itself: the
 *    stage is held by the loop, and `codifica_e_manda` cannot dismantle it
 *    while it is reading inside it.
 *
 *   `scheda_da_abbandonare`  ⇒ remount in MEMORY: this frame on the card
 *                              cannot be used;
 *   `scheda_da_riprovare`    ⇒ remount on the CARD: the canvas has changed and
 *                              the earlier denial no longer holds;
 *   `scheda_mai_piu`         ⛔ this machine's encoder is in SOFTWARE: it is
 *                              not a matter of canvas, and retrying at every
 *                              resize would be remounting the stage for
 *                              nothing, forever.
 */
static bool scheda_da_abbandonare;
static bool scheda_da_riprovare;
static bool scheda_mai_piu;
/* ⛔⛔ AND THIS IS THE GUARD THAT AVOIDS THE IDLE ROUND TRIP — and it deserves a
 *     line of explanation, because it looks like the same thing and is not.
 *
 * The DMA-BUF stride is known **only after the first frame** (`cattura.h`
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
static uint32_t scheda_negata_l, scheda_negata_a;

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ PHASE 17 — THE FALLBACK AFTER THE REFUSAL: the machine without a 3D card
 *
 * ⛔ THE DEFECT, `[M]` 29 Sep 2026, T1c, 7 VMs out of 7: on a machine without
 *    3D acceleration (VM with `virtio-vga` without virgl, a server without a
 *    card) the compositor renders in software and has NO DMA-BUF buffers to
 *    offer.  The card's route asks ONLY for those (mandatory modifier,
 *    `cattura.c` `proposta()`), the negotiation dies with "no more input
 *    formats", and no frame ever arrives.  ⇒ The fallback of
 *    `scheda_da_abbandonare` did not fire: it lives INSIDE a frame.  The
 *    browser got in ("Admitted") and the desktop did not arrive; the child
 *    remounted the stage every five seconds, always on the card, forever.
 *
 * ⭐ THE CURE: when the negotiation on the card FAILS — the stream in error
 *    without a format ever having been agreed
 *    (`cattura_formato_rifiutato()`, or `G_IO_ERROR_NOT_SUPPORTED` from
 *    `cattura_avvia()`) — the route switches to MEMORY, it is declared, and
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
 * ⚠ `scheda_mai_piu`: the refusal comes from the COMPOSITOR, not from the
 *   canvas — a new canvas does not give it the buffers it lacks, and retrying
 *   at every resize would be a failed negotiation for nothing.
 * ⚠ No exceptions per compositor: the question is the same for Mutter and
 *   for KWin (wlroots has its own fallback in `cattura_avvia_wlr()`).
 * ═══════════════════════════════════════════════════════════════════════════ */
static bool ripiega_se_rifiutata(bool rifiutata, const char *perche)
{
	if (!rifiutata || strada_del_palco != CATTURA_STRADA_SCHEDA)
		return false;
	strada_del_palco = CATTURA_STRADA_MEMORIA;
	scheda_mai_piu = true;
	registro_dice(REG_FIGLIO,
	              "⛔⛔ the CARD route was REFUSED by the compositor "
	              "(no format agreed: %s) — on this machine there are no "
	              "DMA-BUF buffers to offer, usually because "
	              "3D acceleration is missing.  ⇒ DECLARED FALLBACK: remounting the capture "
	              "on MEMORY and not retrying — from here on the stretch's "
	              "numbers include the copy",
	              perche ? perche : "without explanation");
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
 *    is a RESULT (`CatturaPresa` tells it apart from a fault), not a defect.
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
 *    loop entered `cattura_prendi()` stays still in the socket for the 249 ms
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
 *   touches the exchange point of `cattura.c` (today the frame is copied only
 *   if someone is already waiting), and that piece runs on PipeWire's
 *   real-time thread: it is a cure to measure, not to improvise.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define MOVIMENTO_ATTESA_S 0.008

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
#define PALCO_RIPROVA_MIN_MS 1000
#define PALCO_RIPROVA_MAX_MS 30000

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
#define NASCITA_BRIGLIA_MS 12000

/*
 * ⛔⭐⭐ HOW OFTEN TO RETRY WHILE THE SESSION IS BEING BORN — and this number
 *       is the cure for the defect the user saw four times: *"at the fourth
 *       login the desktop took many seconds before reappearing"*.
 *
 * ⛔⛔ THE CAUSE WAS THE DOUBLING WAIT, and the reasoning justifying it is
 *     right for ONE case only.  `PALCO_RIPROVA_MIN_MS` grows 1 s → 2 s →
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
#define PALCO_NASCITA_RIPROVA_MS 200

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
static bool sessione_chiusa_dall_utente;
/* ⭐ "I have SEEN the graphical session alive": it is what separates "not born
 *    yet" from "it was there and the user logged out" (§7.6, below in
 *    `prendi_il_palco`).
 * ⛔ PHASE 12 — it was a `static` inside that function, and only reading the
 *    state set it to true: on GNOME it is read at every mounting, on KDE the
 *    stage is mounted DIRECTLY from KWin and the SANA state was never read.
 *    `[M]` 19 Sep 2026: after the logout the child said "not there yet, I have
 *    already asked for it" and waited to make it BE BORN AGAIN — that is, it
 *    prevented logging out.  ⇒ A mounted KWin stage also means "seen alive". */
static bool vista_viva;

/* When to retry, and how long was waited the last time. */
static uint64_t palco_riprova_ms;
static uint64_t palco_attesa_ms;

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
 *   caution.  Once `TELA_ATTESA_MS` has passed we start with the fallback —
 *   better a desktop to resize than no desktop.
 */
static bool tela_dal_cliente;

/* ⚠ How long the client's canvas is given before starting with the fallback.
 *   `[M]` ~650 are enough: half a second of margin and not one more, because
 *   beyond that we start making wait whoever has already pressed "Connect". */
#define TELA_ATTESA_MS 1200

/* ⭐ When we asked for the BIRTH of the graphical session, 0 if never.
 *
 * ⛔ It was a `static` inside `prendi_il_palco()`, and from there the frame
 *    loop could not see it — so it could not tell "the stage is not there
 *    YET" from "it is no longer there", and treated the two cases with the
 *    same doubling wait.  ⇒ See `PALCO_NASCITA_RIPROVA_MS`. */
static uint64_t nascita_chiesta_ms;

/* Are we inside the window in which a requested session can still show up?
 * ⚠ If so, the missing stage is a stage that is BEING BORN. */
static bool sta_nascendo(uint64_t ora_ms)
{
	return nascita_chiesta_ms != 0 &&
	       ora_ms - nascita_chiesta_ms <= NASCITA_BRIGLIA_MS;
}

#define CODEC_MAX 4
/* ⛔ FOUR SLOTS FOR THREE CODECS, and the count is on purpose: the index IS
 *    the number of §6.2 (1 = HEVC, 2 = AV1, 3 = H.264) and slot 0 stays empty.
 *    ⚠ A "tight" array with a subtraction inside would be the same thing
 *    written worse: the day a new codec took 4, the subtraction would have to
 *    be fixed in six places and the log would say numbers different from the
 *    protocol's. */
static Codificatore *codif[CODEC_MAX];
/* Which codec the parent asked for: 0 = none, that is nobody is watching. */
static uint8_t codec_chiesto;
/* ⛔⭐⭐ AND THE DEPTH THE PARENT NEGOTIATED (§4.3) — 17 Aug 2026.
 *
 *      Here there was a literal, three lines further on: `r.profondita = 10`,
 *      for EVERY codec and whatever had been negotiated.  ⛔ The stream came
 *      out at 10 bits while `ECCOMI` declared 8 — **two truths about the same
 *      fact, in two different processes**, and no bench could see them
 *      together.
 *
 * ⚠ `0` = the parent has not said it yet.  ⛔ And it does NOT count as 8: until
 *   it is known, no encoder is opened — "I don't know" and "it is eight" are
 *   two different facts, and it is precisely their confusion that produced
 *   the defect. */
static uint8_t profondita_chiesta;
/* ⛔⭐⭐ AND THE LEVEL THE CLIENT DECLARED (§4.3 line 701) — 23 Aug 2026, and it
 *      comes from the same family of defect as the line above.
 *
 *      `[M]` canvas 3840x2160, H.264: the client declares `video.livello=5.1`
 *      and the server produces **5.2**.  The requested number lived in the
 *      PARENT, the product in the CHILD, and nobody put them side by side —
 *      `LEZIONI.md` §7.5.
 *
 * ⚠ In tenths (`5.1` ⇒ 51).  ⛔ `0` = the client did not declare it, and §4.3
 *   does not require it: then NO CEILING, it opens anyway and WRITES what came
 *   out.  ⚠ And here zero does not block the opening as the depth does: the
 *   depth is always negotiated (§4.3 imposes it on both), the level is not.
 *   They are two different "zeros", and treating them alike would be
 *   inventing an obligation the document does not have. */
static uint8_t livello_chiesto_x10;
/* ⛔ §5.2 — the keyframe debt, one per codec: asking for it for HEVC does not
 *    produce it on AV1, and treating them together would give a keyframe to
 *    whoever did not ask for it and a delta to whoever did. */
/* ⛔⛔⭐ FOUR SLOTS, like `codif[]` — and this line cost a round on 20 Aug 2026.
 *      With `[3]` codec **3** wrote OUT OF BOUNDS, and the byte that got
 *      dirtied was the variable next to it: the log said
 *      "⭐ §4.3: the parent negotiated 8 bits (before **1**)" at every keyframe
 *      request, that is a memory defect disguised as a negotiation defect.
 *      ⇒ Zero frames, and no line naming the cause.
 * ⚠ The index IS the number of §6.2: whoever adds a codec widens THESE arrays,
 *   and they are FIVE since 23 Aug 2026 (`codif_liv[]` is the latest).  They
 *   are found like this: `grep "\[CODEC_MAX\]"`. */
static bool debito_chiave[CODEC_MAX];
/* ⛔ With which depth each encoder was OPENED.  ⚠ It is kept here and not
 *    asked of `codificatore.h`: that module has no reader for the depth, and
 *    adding one for a question that can be remembered would be widening an
 *    interface out of the caller's laziness. */
static uint8_t codif_prof[CODEC_MAX];
/* ⛔ And with which LEVEL IMPOSED (§4.3, in tenths; `0` = no ceiling).  ⚠ It
 *    sits next to `codif_prof[]` and for the same reason: the stage outlives
 *    the client (I4), and the second to connect can declare a level different
 *    from the first — without this memory the encoder would stay at the
 *    ceiling of the FIRST, which is exactly the defect being cured. */
static uint8_t codif_liv[CODEC_MAX];
/*
 * ⭐ PHASE 13 — THE CHANNEL ORDER THAT COMES FROM THE CAPTURE.
 *
 * ⛔⛔ It was `CODIFICATORE_PIXEL_BGRX` hard-wired inside `codificatore_di()`,
 *     and it was true for GNOME and KDE (Mutter and KWin give BGRx).  `[M]` 21
 *     Sep 2026: labwc gives **XBGR8888**, that is `R G B x`, and gives it as
 *     the ONLY format — screencopy's `buffer` event arrives only once.  ⇒ With
 *     the hard-wired order the user saw **red and blue swapped**.  Found by
 *     the adversarial reviewer, not by an image: C1 does not look at colours.
 * ⇒ The order is told by the FRAME (`formato_drm`), and if it changes the
 *   encoder is redone — the same scheme as `codif_liv`.
 */
static FormatoPixel formato_ingresso = CODIFICATORE_PIXEL_BGRX;
static FormatoPixel codif_fmt[CODEC_MAX];
static uint64_t ciclo_fotogrammi, ciclo_chiavi, ciclo_zero, ciclo_guasti;
/* ⛔ COUNTED APART from `ciclo_guasti`, and it is not pedantry: that counter
 *    enters the criterion "the loop did not even try to capture" of the
 *    summary line.  Putting here the frames discarded for inconsistent
 *    geometry would give two different facts under the same label — form E8,
 *    inside the very line that exists to unmask it. */
static uint64_t fotogrammi_incoerenti;
/* ⛔⭐ THE GROWING WAIT ON REOPENING THE ENCODER — and the reason is the same
 *     as the 30.8 GB of log of 14 Aug: if `codificatore_nuovo()` fails for a
 *     PERSISTENT cause (GPU memory, a profile that does not hold that size, a
 *     busy node), `codificatore_di()` would retry the opening **at every
 *     frame** — sixty VAAPI contexts per second, and one log line for each.
 *     ⚠ The backoff here hides nothing: the first line is always written, and
 *     the retry is declared. */
static uint64_t codif_riprova_ms[CODEC_MAX];
static uint64_t codif_attesa_ms[CODEC_MAX];
#define CODIF_RIPROVA_MIN_MS 500u
#define CODIF_RIPROVA_MAX_MS 10000u
/* ⭐ When the stream was last restarted to get a frame delivered on a still
 *    scene.  ⛔ The backoff is not caution: every restart costs the
 *    renegotiation, and doing one on every round would remove the very frames
 *    being sought.  ⚠ 400 ms is two orders of magnitude below the measured
 *    4.4 seconds and above the cost of a restart (`[M]` 41.6 ms). */
static uint64_t risveglio_ms;
#define RISVEGLIO_MS 400u
/* ⛔ Cure "A" (21 Aug 2026, 🔸 derived) skips the wake-up when something is
 *    held down.  ⚠ This flag serves only NOT to repeat the log line every
 *    400 ms while the user drags: diagnostics that drown the ones that count
 *    are diagnostics that stay silent (`LEZIONI.md` §2.7). */
static int risveglio_zitto;
static uint64_t ciclo_detto_ms;
/* ⛔ The measure of point 7, made and NOT inferred: is the `pts` Mutter attaches
 *    to the frame our monotonic clock or not?  It is looked at once, written
 *    down, and from then on it is known which instant ends up in the 28 bytes. */
static int pts_e_monotono = -1; /* -1 = not looked at yet */

static uint64_t ora_monotona_us(void)
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
 *      (`fondamenta/remotix-c/src/suono.h`, and `LEZIONI.md` §5.)
 *
 * ⇒ Between the PipeWire thread and the child's loop there is a
 *   **single-producer single-consumer ring**, without locks: the producer
 *   moves only `testa`, the consumer only `coda`, and the two indices are
 *   atomic.  The callback copies and returns.
 *
 * ⛔ AND WHEN THE RING IS FULL THE OLDEST IS DROPPED, as for datagrams
 *    (`RCP.md` §6.3): late sound is of no use to anyone.  ⚠ But here it is
 *    dropped **while counting**, and the count goes into the log — because a
 *    ring overflowing silently is a rhythm defect nobody will ever see.
 * ═══════════════════════════════════════════════════════════════════════════ */

/* One second of sound.  ⚠ It is not a cushion for smoothness: it is the gap
 * between two rounds of the child's loop, which with video on is ~8 ms
 * (`MOVIMENTO_ATTESA_S`).  One second is two orders of magnitude of margin,
 * and it costs 192 KiB — which is less than a frame. */
#define AUDIO_ANELLO_FOTOGRAMMI 48000u

static int16_t audio_anello[AUDIO_ANELLO_FOTOGRAMMI * AUDIO_CANALI];
static _Atomic uint32_t audio_testa; /* moved ONLY by the PipeWire thread */
static _Atomic uint32_t audio_coda;  /* moved ONLY by the child's loop */
static _Atomic uint64_t audio_traboccati; /* frames dropped by the producer */

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
static uint64_t audio_consumati; /* frames already out, since the base */

static void audio_anello_azzera(void)
{
	atomic_store(&audio_testa, 0);
	atomic_store(&audio_coda, 0);
	atomic_store(&audio_traboccati, 0);
	audio_base_us = 0;
	audio_consumati = 0;
}

/*
 * The samples callback.  ⛔ IT RUNS IN REAL TIME: copy and return.
 *
 * ⚠ No log line in here, and it is on purpose: `registro_dice()` writes to a
 *   descriptor, and a write that blocks inside this callback costs the
 *   desktop's frames.  The overflow is COUNTED here and WRITTEN over there,
 *   from the loop.
 */
static void audio_campioni(const int16_t *campioni, uint32_t fotogrammi, void *ctx)
{
	uint32_t testa, coda, liberi;
	(void)ctx;

	if (!fotogrammi || !campioni)
		return;

	testa = atomic_load_explicit(&audio_testa, memory_order_relaxed);
	coda = atomic_load_explicit(&audio_coda, memory_order_acquire);

	/* ⛔ One slot always stays empty: it is the only way to tell "full" from
	 *    "empty" with only two indices. */
	liberi = (coda + AUDIO_ANELLO_FOTOGRAMMI - testa - 1u) % AUDIO_ANELLO_FOTOGRAMMI;
	if (fotogrammi > liberi) {
		/* The TAIL of the block is kept, that is the most recent sound. */
		uint32_t buttati = fotogrammi - liberi;
		atomic_fetch_add_explicit(&audio_traboccati, buttati, memory_order_relaxed);
		campioni += (size_t)buttati * AUDIO_CANALI;
		fotogrammi = liberi;
		if (!fotogrammi)
			return;
	}

	for (uint32_t i = 0; i < fotogrammi; i++) {
		uint32_t p = (testa + i) % AUDIO_ANELLO_FOTOGRAMMI;
		audio_anello[p * AUDIO_CANALI] = campioni[i * AUDIO_CANALI];
		audio_anello[p * AUDIO_CANALI + 1] = campioni[i * AUDIO_CANALI + 1];
	}
	atomic_store_explicit(&audio_testa,
	                      (testa + fotogrammi) % AUDIO_ANELLO_FOTOGRAMMI,
	                      memory_order_release);
}

/* How many frames are ready to be consumed. */
static uint32_t audio_pronti(void)
{
	uint32_t testa = atomic_load_explicit(&audio_testa, memory_order_acquire);
	uint32_t coda = atomic_load_explicit(&audio_coda, memory_order_relaxed);
	return (testa + AUDIO_ANELLO_FOTOGRAMMI - coda) % AUDIO_ANELLO_FOTOGRAMMI;
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
static suono *son;
static audio_cod *acod;
/* Which audio codec the parent asked for: 0 = nobody is listening. */
static uint8_t audio_codec;
static uint64_t audio_blocchi_spediti, audio_blocchi_persi;
static uint64_t audio_detto_us;

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
 *   (`sessione.c`), not to this process, and it is a product decision.
 */
static void dichiara_priorita_audio(void)
{
	/* ⛔ The names of the threads forming the audio path.  ⚠ `data-loop` and
	 *    `module-rt` are PipeWire's, not ours: that is precisely why they must
	 *    be looked at — the priority that counts is THEIRS. */
	static const char *NOMI[] = { "data-loop", "pw-data", "pw-rt", "module-rt",
		                          "remotix-suono", "remotix-cattura" };
	struct rlimit rl;
	unsigned long tetto = 0;
	DIR *cartella;
	struct dirent *voce;
	int guardati = 0, in_tempo_reale = 0, peggior_nice = -100;
	char elenco[512];
	size_t usato = 0;

	if (getrlimit(RLIMIT_RTPRIO, &rl) == 0)
		tetto = (unsigned long) rl.rlim_cur;

	elenco[0] = '\0';
	cartella = opendir("/proc/self/task");
	while (cartella && (voce = readdir(cartella)) != NULL) {
		char percorso[128], nome[64];
		FILE *f;
		long tid;
		int politica, gentilezza;
		size_t l;

		if (voce->d_name[0] < '0' || voce->d_name[0] > '9')
			continue;
		tid = strtol(voce->d_name, NULL, 10);
		snprintf(percorso, sizeof percorso, "/proc/self/task/%ld/comm", tid);
		f = fopen(percorso, "r");
		if (!f)
			continue;
		if (!fgets(nome, sizeof nome, f)) {
			fclose(f);
			continue;
		}
		fclose(f);
		l = strlen(nome);
		while (l && (nome[l - 1] == '\n' || nome[l - 1] == ' '))
			nome[--l] = '\0';

		{
			int nostro = 0;
			for (size_t i = 0; i < sizeof NOMI / sizeof NOMI[0]; i++)
				if (strstr(nome, NOMI[i])) {
					nostro = 1;
					break;
				}
			if (!nostro)
				continue;
		}

		/* ⛔ `sched_getscheduler(tid)` and not a read of `/proc/.../stat`: it
		 *    is the same question asked of the kernel instead of a text to
		 *    parse, and it has no field index to get wrong. */
		politica = sched_getscheduler((pid_t) tid);
		errno = 0;
		gentilezza = getpriority(PRIO_PROCESS, (id_t) tid);
		if (errno)
			gentilezza = 0;

		guardati++;
		if (politica == SCHED_FIFO || politica == SCHED_RR)
			in_tempo_reale++;
		else if (gentilezza > peggior_nice)
			peggior_nice = gentilezza;

		if (usato < sizeof elenco - 48)
			usato += (size_t) snprintf(elenco + usato, sizeof elenco - usato, "%s%s(%s,nice %d)",
			                           usato ? " " : "", nome,
			                           politica == SCHED_FIFO  ? "FIFO"
			                           : politica == SCHED_RR  ? "RR"
			                           : politica == SCHED_IDLE ? "idle"
			                           : politica == SCHED_BATCH ? "batch"
			                                                     : "normal",
			                           gentilezza);
	}
	if (cartella)
		closedir(cartella);

	/* ⛔ "I found no thread" is NOT "all is well": it is a blind instrument,
	 *    and it is said in those words (`CODER.md` §3.10). */
	if (guardati == 0) {
		registro_dice(REG_FIGLIO,
		              "⚠ I FOUND NO thread of the audio path "
		              "(looking for data-loop, pw-data, pw-rt, module-rt, "
		              "remotix-suono, remotix-cattura): ⛔ this is NOT the "
		              "measure «all is well», it is «I did not look».  "
		              "RLIMIT_RTPRIO = %lu",
		              tetto);
		return;
	}

	if (in_tempo_reale == guardati)
		registro_dice(REG_FIGLIO,
		              "⭐ real-time priority OBTAINED: %d threads out of %d of the "
		              "audio path run FIFO/RR (RLIMIT_RTPRIO = %lu).  %s",
		              in_tempo_reale, guardati, tetto, elenco);
	else
		registro_dice(
		    REG_FIGLIO,
		    "⛔⛔ FIFO **NOT** OBTAINED: %d threads out of %d of the audio path run at "
		    "NORMAL policy (worst nice %d), and RLIMIT_RTPRIO = %lu — ⚠ the rlimit says «you can "
		    "ASK for it», not «you have it».  `[M]` 21 Aug 2026: on this kernel "
		    "`CONFIG_RT_GROUP_SCHED` with cgroup v2 refuses SCHED_FIFO to anyone not in the "
		    "ROOT cgroup ⇒ every process governed by systemd is excluded and `LimitRTPRIO=20` "
		    "is INERT.  ⇒ The audio will crackle WHEN THE DESKTOP IS WORKING, and with a still "
		    "desktop it does not reproduce.  ⚠ And the cure is not here: the independent referee "
		    "(`pw-record` on the same monitor) hears the same crackles at the same instants ⇒ the "
		    "defect is born in the SESSION's audio graph, not in our transport.  %s",
		    guardati - in_tempo_reale, guardati, peggior_nice == -100 ? 0 : peggior_nice, tetto,
		    elenco);
}

static void audio_regola_figlio(uint8_t codec)
{
	if (codec == audio_codec)
		return;

	/* It always stops first: `suono_ascolto_ferma()` WAITS for the PipeWire
	 * thread, and whoever returns from there is allowed to touch what the
	 * callback was using — the ring included. */
	if (audio_codec) {
		suono_ascolto_ferma(son);
		audio_cod_chiudi(acod);
		acod = NULL;
		registro_dice(REG_FIGLIO,
		              "audio turns OFF: %llu blocks sent, %llu lost, "
		              "%llu frames overflowed.  ⭐ The sink stays (I4)",
		              (unsigned long long)audio_blocchi_spediti,
		              (unsigned long long)audio_blocchi_persi,
		              (unsigned long long)atomic_load(&audio_traboccati));
	}
	audio_codec = 0;

	if (!codec)
		return;

	/* ⛔ The sink is mounted ONLY ONCE for the life of the child. */
	if (!son) {
		son = suono_apri();
		if (!son) {
			/* ⚠ DECLARED FALLBACK (`CODER.md` §4.2): the desktop keeps
			 *   working without audio, and this line is the only difference
			 *   between "degraded" and "silently broken".  The log of the
			 *   reason has already been written by `suono_apri()`. */
			registro_dice(REG_FIGLIO,
			              "⛔ the audio sink does not mount: this session "
			              "stays WITHOUT SOUND.  ⚠ The desktop goes on — it is a "
			              "declared fallback, not a hushed-up fault");
			return;
		}
	}
	/* ⛔ Invariant I5: whoever connects finds the volume AT MAXIMUM.  It is
	 *    redone at every connection and not only at creation, because a slider
	 *    left low is a state the client can neither see nor explain. */
	suono_volume_massimo(son);

	acod = audio_cod_apri(codec);
	if (!acod) {
		registro_dice(REG_FIGLIO,
		              "⛔ the audio encoder for codec %u does not open: "
		              "this session stays without sound", codec);
		return;
	}

	audio_anello_azzera();
	if (!suono_ascolto_avvia(son, audio_campioni, NULL)) {
		registro_dice(REG_FIGLIO,
		              "⛔ the monitor capture does not start: no sound");
		audio_cod_chiudi(acod);
		acod = NULL;
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
	dichiara_priorita_audio();

	audio_codec = codec;
	audio_blocchi_spediti = audio_blocchi_persi = 0;
	registro_dice(REG_FIGLIO,
	              "⭐ PHASE 7: audio turns ON — codec %u (%s), blocks of %u "
	              "frames, sink node %u",
	              codec, codec == 1 ? "Opus" : "PCM", audio_cod_blocco(acod),
	              suono_nodo(son));
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
static void audio_svuota(void)
{
	uint32_t blocco;
	int16_t campioni[AUDIO_BLOCCO_OPUS * AUDIO_CANALI];
	uint8_t fuori[AUDIO_FUORI_MAX];
	uint64_t traboccati;

	if (!audio_codec || !acod)
		return;
	blocco = audio_cod_blocco(acod);

	/* ⛔ The overflow is read HERE and not in the callback: there one cannot
	 *    write to the log without risking the desktop's frames. */
	traboccati = atomic_exchange(&audio_traboccati, 0);
	if (traboccati) {
		/* ⭐ And the clock base MOVES by the lost samples, or the `istante`
		 *    values would tell of a continuous sound where there was a gap —
		 *    and the client would reorder on a lie (§6.3). */
		audio_base_us += traboccati * 1000000u / AUDIO_FREQUENZA;
		registro_dice(REG_FIGLIO,
		              "⚠ the audio ring overflowed by %llu frames "
		              "(%llu ms): the loop does not empty it fast enough.  "
		              "⛔ It is not the network: it is here",
		              (unsigned long long)traboccati,
		              (unsigned long long)(traboccati * 1000u / AUDIO_FREQUENZA));
	}

	while (audio_pronti() >= blocco) {
		uint32_t coda = atomic_load_explicit(&audio_coda, memory_order_relaxed);
		size_t n = 0;
		uint64_t istante;

		for (uint32_t i = 0; i < blocco; i++) {
			uint32_t p = (coda + i) % AUDIO_ANELLO_FOTOGRAMMI;
			campioni[i * AUDIO_CANALI] = audio_anello[p * AUDIO_CANALI];
			campioni[i * AUDIO_CANALI + 1] = audio_anello[p * AUDIO_CANALI + 1];
		}
		atomic_store_explicit(&audio_coda,
		                      (coda + blocco) % AUDIO_ANELLO_FOTOGRAMMI,
		                      memory_order_release);

		if (!audio_base_us)
			audio_base_us = ora_monotona_us();
		istante = audio_base_us + audio_consumati * 1000000u / AUDIO_FREQUENZA;
		audio_consumati += blocco;

		if (audio_cod_passa(acod, campioni, fuori, &n)) {
			struct corpo_blocco c;
			memset(&c, 0, sizeof c);
			c.codec = audio_codec;
			c.byte = (uint32_t)n;
			c.istante_us = istante;
			/* ⛔ If it does not go out IT IS DROPPED and counted: §6.3 forbids
			 *    retransmission, and a child waiting to be able to write
			 *    would stop the desktop capture. */
			if (!manda(MSG_BLOCCO, &c, sizeof c, fuori, n))
				audio_blocchi_persi++;
			else
				audio_blocchi_spediti++;
		}
	}

	/* One line per second, with the ZEROS in it: "the loop does not run", "the
	 * session does not play" and "the blocks do not go out" must have three
	 * different faces (`CODER.md` §3.10). */
	{
		uint64_t adesso = ora_monotona_us();
		if (adesso - audio_detto_us >= 1000000u) {
			audio_detto_us = adesso;
			registro_dettaglio(REG_FIGLIO,
			                   "audio: %llu blocks sent, %llu lost, "
			                   "%llu frames waiting in the ring — codec %u",
			                   (unsigned long long)audio_blocchi_spediti,
			                   (unsigned long long)audio_blocchi_persi,
			                   (unsigned long long)audio_pronti(), audio_codec);
		}
	}
}


static void rilievo_scrivi(const char *dir, const char *nome, const void *dati,
                           size_t byte)
{
	char percorso[512];
	FILE *fp;
	size_t scritti;

	if (!dir || !dir[0] || strcmp(dir, "-") == 0)
		return;
	snprintf(percorso, sizeof percorso, "%s/%s", dir, nome);
	fp = fopen(percorso, "wb");
	if (!fp) {
		/* ⚠ The CHILD writes there, that is the user: a folder of the parent
		 *   is not theirs, and the survey does not come out.  It is said,
		 *   instead of leaving a missing file looking like a survey nobody
		 *   asked for. */
		registro_dice(REG_FIGLIO, "⛔ survey %s: %s (the user writes there, not root)",
		              percorso, strerror(errno));
		return;
	}
	scritti = fwrite(dati, 1, byte, fp);
	if (fclose(fp) != 0 || scritti != byte) {
		registro_dice(REG_FIGLIO, "⛔ survey %s: %zu bytes of %zu", percorso,
		              scritti, byte);
		return;
	}
	registro_dice(REG_FIGLIO, "survey written: %s (%zu bytes)", percorso, byte);
}

/* ------------------------------------------------------------------ *
 *  ⭐ THE ON-DEMAND SNAPSHOT — `SIGUSR1` and `SIGUSR2`, 17 Aug 2026
 *
 *  It serves ONE thing: separating the three suspects of the 64 px block
 *  artefacts measured on the user's video (capture · encoder ·
 *  browser).  On `SIGUSR1` the child asks for a KEYFRAME and then puts on
 *  disk, from the same instant:
 *
 *    `scatto-ingresso.bgrx`  the pixels the encoder HAS IN HAND
 *    `scatto-flusso.obu`     the bytes we send, from the keyframe on
 *    `scatto-uscita.bgrx`    the input of the LAST frame queued
 *
 *  ⇒ If the blocks are already in the BGRX, the fault is UPSTREAM of the
 *    encoder; if they appear only when decoding the stream with a
 *    different decoder, it is the ENCODER; if neither has them, the
 *    BROWSER remains.
 *
 *  ⛔ It is not a product switch: it writes only if `--rilievo` is there,
 *     it arms once per signal, and `SIGUSR2` closes it at once (without it,
 *     on a still scene one would wait for frames that do not arrive).
 * ------------------------------------------------------------------ */
#define SCATTO_FOTOGRAMMI 300

/* ⛔ AND IT KEEPS THE FOLDER ITSELF, instead of reading it from the parameter.
 *
 * `[M]` 17 Aug 2026, and the first snapshot was lost like this: in the main
 * ROUND `codifica_e_manda()` is called with `dir_rilievo = NULL` (the
 * `codec_chiesto` line) — the real folder arrives only at the first encoding,
 * the one at switch-on.  ⇒ `rilievo_scrivi()` exited silently, and the log
 * line said "input 2560x962, 9850880 bytes" of a file that had not been
 * written: the worst form, a green that looked at nothing (`LEZIONI.md`
 * §1.9). */
static const char *scatto_dir = NULL;

static volatile sig_atomic_t scatto_chiesto = 0;
static volatile sig_atomic_t scatto_stop = 0;
static int scatto_stato = 0; /* 0 idle · 1 waiting for the keyframe · 2 queueing */
static int scatto_restano = 0;
static FILE *scatto_fp = NULL;
static unsigned long long scatto_quanti = 0;

static void scatto_segnale(int quale)
{
	if (quale == SIGUSR2)
		scatto_stop = 1;
	else
		scatto_chiesto = 1;
}

/* Closes the stream and writes the last input.  `perche` ends up in the log,
 * so that a truncated survey is not mistaken for a finished one. */
static void scatto_chiudi(const char *dir_rilievo, const CatturaFermo *fo,
                          const char *perche)
{
	if (scatto_fp) {
		fclose(scatto_fp);
		scatto_fp = NULL;
	}
	scatto_stato = 0;
	scatto_restano = 0;
	if (fo && fo->pixel)
		rilievo_scrivi(dir_rilievo, "scatto-uscita.bgrx", fo->pixel,
		               (size_t)fo->byte);
	registro_dice(REG_FIGLIO,
	              "⭐ SNAPSHOT FINISHED (%s): %llu frames in "
	              "`scatto-flusso.obu`, and `scatto-uscita.bgrx` is the input "
	              "of the LAST of them",
	              perche, scatto_quanti);
}

/* ⛔ The same encoding request as `main.c` before 12 Aug 2026 —
 *    CRF 20, 10 bits asked on an 8-bit source (promotion DECLARED by the
 *    encoder), BGRx, keyframes on request.  ⚠ It was not "rewritten": it was
 *    MOVED, because the child is the one with the pixels.
 *
 * ⛔⭐ AND `chiavi_ogni = 0` STAYS ZERO, that is an infinite GOP, and it is a
 *     choice — not an oversight.  `RCP.md` §5.2 wants a keyframe in three
 *     cases only: the first after `SESSIONE`, the first at the new size, and
 *     when the client asks for it.  Periodic keyframes would be bandwidth
 *     spent on an insurance the protocol already buys — and `SPECIFICHE.md`
 *     §8.2 says bandwidth is spent on quality, not on caution.
 *
 *     ⛔ BUT THE PRICE IS THAT THE SEAM MUST EXIST: with an infinite GOP and
 *        nobody calling `codificatore_chiedi_chiave()`, after the first
 *        keyframe **not a single one ever arrives again**, and a client that
 *        loses a delta is left with a wrecked screen forever.  The caller is
 *        there now — `MSG_VIDEO` with `chiave = 1`, and the whole road is in
 *        the box of `wt_video_gancio()`. */
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
#define NODO_RENDERING "/dev/dri/renderD128"
/* ⭐ Phase 16, Radeon campaign: no longer a rigid `BASSA` but the written rule
 *    `LA_DICHIARATA` — *EncSliceLP if the driver declares it, otherwise full
 *    EncSlice* (see `PotenzaEntrypoint`).  On the Intel it is the same
 *    `EncSliceLP` as before; on the RX 6800 (radeonsi) `[M]` there is only
 *    `EncSlice`, and with `BASSA` the session dropped to SOFTWARE.  ⛔ The
 *    choice is made by the capability read from the driver, not by the card's
 *    name: which of the two is in force is said by the «encoder OPENED»
 *    line below, not by this one. */
#define POTENZA_RENDERING CODIFICATORE_POTENZA_LA_DICHIARATA
/* ⛔ The constant QP, and it is NOT "the CRF 20 of before": they are two
 *    different quantities (see `ModoQualita` in `codificatore.h`).  ⚠ The
 *    value is a declared placeholder — the working point between quality and
 *    bandwidth is phase 9, like the x265 preset. */
#define QP_HARDWARE 26
/* ⛔ Here there was `CRF_SOFTWARE`, the CRF of the software fallback: it left
 *    with it (phase 19, `DECISIONI.md` §10.27). */

/* ⛔ The entrypoint's name is PRINTED from `POTENZA_RENDERING`, not written by
 *    hand in the log line: it is the same form E2 as the defect of 22 Aug
 *    ("hevc_vaapi" written inside the quotes while the one failing was
 *    `h264_vaapi") — a right line with the wrong name next to it sends the
 *    hunt the wrong way.  ⚠ `NON_DICHIARATA` is there because it is the
 *    zero, that is what one gets without writing it: if it appeared in the
 *    log it would already be the diagnosis. */
static const char *potenza_nome(PotenzaEntrypoint p)
{
	switch (p) {
	case CODIFICATORE_POTENZA_PIENA:
		return "EncSlice (full)";
	case CODIFICATORE_POTENZA_BASSA:
		return "EncSliceLP (low power)";
	case CODIFICATORE_POTENZA_LA_DICHIARATA:
		return "EncSliceLP if the driver declares it, otherwise EncSlice (full) — "
		       "the one IN FORCE is told by the «encoder OPENED» line";
	default:
		return "NOT DECLARED (⛔ and so nothing opens)";
	}
}

/* ⛔⭐⭐ `RCP.md` §4.3 (line 701) — THE LEVEL PRODUCED, SAID IN THE ALPHABET IN
 *      WHICH THE CLIENT ASKS FOR IT.
 *
 *      §4.3: *"`video.livello`: the maximum level it can decode, e.g. `5.1`.
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
 *      log next to a `video.livello=5.1` must be able to see it without a
 *      table in hand.  Here it comes out in TENTHS, which is the form of §4.3
 *      and the same in which `rcp.c` reads the client's capability.
 *
 * ⚠ Returns 0 when it cannot translate — and zero is NOT "low": it is "I don't
 *   know", and the line printing it writes it in those words.  ⚠ H.264 also
 *   has level "1b", which `level_idc` does not distinguish from 1.1 without
 *   looking at another field: it is outside any canvas this product serves,
 *   and it is declared here instead of pretending it does not exist. */
static unsigned livello_in_decimi(CodecVideo codec, int livello_flusso)
{
	if (livello_flusso <= 0)
		return 0;
	switch (codec) {
	case CODIFICATORE_H264:
		return (unsigned)livello_flusso;
	case CODIFICATORE_HEVC:
		return (unsigned)livello_flusso / 3u;
	case CODIFICATORE_AV1:
		return ((unsigned)livello_flusso / 4u + 2u) * 10u
		       + (unsigned)livello_flusso % 4u;
	default:
		return 0;
	}
}

/* ⛔ The number of §6.2 and the encoder's codec are two different alphabets,
 *    and the translation lives in ONE function: the day they diverged, a
 *    single line would be what diverges.  ⚠ An unknown number does NOT become
 *    a codec "so as to go on": it is declared and nothing is encoded. */
static CodecVideo codec_del_numero(uint8_t numero)
{
	switch (numero) {
	case 1:
		return CODIFICATORE_HEVC;
	case 2:
		return CODIFICATORE_AV1;
	case 3:
		return CODIFICATORE_H264;
	default:
		registro_dice(REG_FIGLIO,
		              "⛔ unknown codec number (%u): §6.2 knows three, and I do not "
		              "invent a fourth",
		              numero);
		return (CodecVideo) 0;
	}
}

/* Why the hardware did not open, the last time it was tried ("" if it opened,
 * or if it was not tried). */
static char rifiuto_hardware[512];

/* ⭐ PHASE 18 — the node on which the card is opened.  In the session it is
 *    ALWAYS `NODO_RENDERING`: only `--prova-codifica --nodo …` moves it, to
 *    try the other card (see `figlio_prova_codifica()`).  ⛔ No environment
 *    variable touches it.  (`--software`, which skipped the card to try the
 *    fallback, left with the fallback: phase 19.) */
static const char *nodo_rendering = NODO_RENDERING;

/* ⭐ PHASE 19 — THE CARD'S ROUTE (`DECISIONI.md` §10.27).  `scheda` = chosen BY
 *    CAPABILITY (Vulkan Video if available for that codec, otherwise VA-API),
 *    and it is what the product does; `vulkan`/`vaapi` = that one and nothing
 *    else, for tests and diagnosis (`--codifica`, from the command line of the
 *    server and of `--prova-codifica`).  The component's name is born here:
 *    `h264_scheda`, `hevc_vulkan`, … (`codificatore.h`).  ⛔ The parent passes
 *    it to the child on the command line (`figli_esegui`): the child is an
 *    exec, and a static of the parent does not reach this side. */
static const char *strada_codifica = "scheda";

bool figlio_codifica_strada(const char *strada)
{
	if (!strada || (strcmp(strada, "scheda") && strcmp(strada, "vulkan") && strcmp(strada, "vaapi")))
		return false;
	strada_codifica = strada;
	return true;
}

const char *figlio_codifica_strada_chiesta(void)
{
	return strada_codifica;
}

/*
 * ⛔ PHASE 19 — THE SLABS OF `wlroots.c` AND THE ENCODING ROUTE (1 Oct 2026).
 *    With Vulkan encoding the GBM slabs must be born at the maximum canvas and
 *    not die at a size change (the Radeon GPU hang: box of `WLR_LASTRA_L` in
 *    `wlroots.c`); with VA-API not.  ⇒ It is decided ONCE, before the first
 *    stage, with the same rule as the components (`componente_di()`):
 *    "vulkan" yes, "vaapi" no, "scheda" = what the node's card declares
 *    (`codificatore_vulkan_sul_nodo`).
 */
static void lastre_per_la_strada(void)
{
	static bool deciso = false;
	bool vulkan;

	if (deciso)
		return;
	deciso = true;
	if (!strcmp(strada_codifica, "vulkan"))
		vulkan = true;
	else if (!strcmp(strada_codifica, "vaapi"))
		vulkan = false;
	else
		vulkan = codificatore_vulkan_sul_nodo(nodo_rendering);
	wlr_lastre_alla_tela_massima(vulkan);
	registro_dice(REG_FIGLIO,
	              "⭐ PHASE 19: the slabs of the wlroots capture %s (route requested «%s», node %s)",
	              vulkan ? "are born at the MAXIMUM CANVAS and stay on a size change — the "
	                       "encoding will be Vulkan (the Radeon GPU hang)"
	                     : "are of the right size and are redone on a change — the encoding "
	                       "will be VA-API",
	              strada_codifica, nodo_rendering);
}

/*
 * ⭐ 6 Oct 2026 — THE CARD'S ROUTE WHERE LINEAR IS NOT AVAILABLE (Mutter and KWin).
 * `[M]` NVIDIA (driver 595) + GNOME 50: the usual proposal (LINEAR, then
 * INVALID) ended in "no more input formats" and the session stayed BLACK.
 * ⇒ If the card refuses linear (the same question as `wlroots.c`), the
 *   proposal also offers the modifiers the Vulkan encoder imports.
 * ⛔ Where linear succeeds nothing changes: no extra modifier.
 */
static void modificatori_per_la_strada(void)
{
	static bool deciso = false;
	uint64_t m[16];
	int n = 0;

	if (deciso || strada_del_palco != CATTURA_STRADA_SCHEDA)
		return;
	deciso = true;
	if (!vulkanvideo_scheda_rifiuta_il_lineare(nodo_rendering))
		return;
	n = vulkanvideo_modificatori(nodo_rendering, DRM_FORMAT_XRGB8888, m, (int)G_N_ELEMENTS(m));
	if (n < (int)G_N_ELEMENTS(m)) {
		uint64_t a[16];
		int na = vulkanvideo_modificatori(nodo_rendering, DRM_FORMAT_ARGB8888, a,
		                                  (int)G_N_ELEMENTS(a));
		for (int i = 0; i < na && n < (int)G_N_ELEMENTS(m); i++) {
			bool gia = false;
			for (int j = 0; j < n; j++)
				gia = gia || m[j] == a[i];
			if (!gia)
				m[n++] = a[i];
		}
	}
	cattura_modificatori_scheda(m, n);
	registro_dice(REG_FIGLIO,
	              "⭐ the card %s REFUSES the linear slab (NVIDIA): the capture's "
	              "proposal also offers the %d modifiers the Vulkan encoder "
	              "imports%s",
	              nodo_rendering, n,
	              n ? "" : " — ⛔ none: the memory fallback remains if the compositor refuses");
}

/* The name of the component to request for `codec` on the route in force. */
static const char *componente_di(CodecVideo codec)
{
	static char nome[2][32];
	int quale = codec == CODIFICATORE_H264 ? 0 : 1;

	snprintf(nome[quale], sizeof nome[quale], "%s_%s", codec == CODIFICATORE_H264 ? "h264" : "hevc",
	         strada_codifica);
	return nome[quale];
}

static Codificatore *codificatore_di(CodecVideo codec, uint8_t indice,
                                     uint32_t tela_l, uint32_t tela_a)
{
	CodificatoreRichiesta r;
	char errore[512];
	uint8_t prof = profondita_chiesta;

	if (indice >= CODEC_MAX)
		return NULL;

	/* ⛔⭐ WITHOUT A NEGOTIATED DEPTH NOTHING OPENS, and it is not caution:
	 *     opening one "just because" would mean choosing ourselves what §4.3
	 *     makes the parent choose — that is putting the literal back under
	 *     another name.
	 * ⚠ In practice it is never reached: `MSG_VIDEO` carries the two numbers
	 *   together, and the loop does not capture until it has arrived.  The
	 *   line is there so that the day it were reached someone would say so. */
	if (prof != 8 && prof != 10) {
		registro_dice(REG_FIGLIO,
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
	if (codif[indice] && codif_prof[indice] != prof) {
		registro_dice(REG_FIGLIO,
		              "⭐ the negotiated depth has changed (%u → %u): redoing "
		              "encoder %u, and the next frame will be a "
		              "KEYFRAME (§5.2)",
		              codif_prof[indice], prof, indice);
		codificatore_libera(codif[indice]);
		codif[indice] = NULL;
		codif_prof[indice] = 0;
		debito_chiave[indice] = true;
	}
	/* ⛔⭐ AND THE SAME FOR THE LEVEL (§4.3 line 701) — 23 Aug 2026.  The level
	 *     is set at the encoder's OPENING and ends up in the SPS: changing it
	 *     with the encoder open does not change it in the stream.  ⇒ The
	 *     second client declaring a ceiling different from the first brings
	 *     along a new encoder, or it would see the ceiling of the FIRST — and
	 *     the symptom, again, would be a black screen without a line. */
	if (codif[indice] && codif_fmt[indice] != formato_ingresso) {
		registro_dice(REG_FIGLIO,
		              "⭐ the capture's channel order has changed (%s → %s): "
		              "redoing encoder %u, and the next frame will be "
		              "a KEYFRAME (§5.2)",
		              codif_fmt[indice] == CODIFICATORE_PIXEL_RGBX ? "RGBx" : "BGRx",
		              formato_ingresso == CODIFICATORE_PIXEL_RGBX ? "RGBx" : "BGRx",
		              indice);
		codificatore_libera(codif[indice]);
		codif[indice] = NULL;
		codif_prof[indice] = 0;
		codif_liv[indice] = 0;
		debito_chiave[indice] = true;
	}
	if (codif[indice] && codif_liv[indice] != livello_chiesto_x10) {
		registro_dice(REG_FIGLIO,
		              "⭐ §4.3: the level ceiling has changed (%u.%u → %u.%u, "
		              "0.0 = no ceiling): redoing encoder %u, and the "
		              "next frame will be a KEYFRAME (§5.2)",
		              codif_liv[indice] / 10u, codif_liv[indice] % 10u,
		              livello_chiesto_x10 / 10u, livello_chiesto_x10 % 10u,
		              indice);
		codificatore_libera(codif[indice]);
		codif[indice] = NULL;
		codif_prof[indice] = 0;
		codif_liv[indice] = 0;
		debito_chiave[indice] = true;
	}
	if (codif[indice])
		return codif[indice];

	/* ⛔⭐ AND IT IS NOT RETRIED AT EVERY FRAME — see `codif_riprova_ms`.  ⚠ The
	 *    silence here is intended and limited: the line explaining the failure
	 *    was already written by the previous attempt, and repeating it sixty
	 *    times a second is the defect this wait exists to avoid. */
	if (codif_riprova_ms[indice] && registro_ora_ms() < codif_riprova_ms[indice])
		return NULL;

	memset(&r, 0, sizeof r);
	r.codec = codec;
	r.componente = NULL;
	r.larghezza = tela_l;
	r.altezza = tela_a;
	/* ⛔ The rate is ONE, and the same one asked of the capture. */
	r.fotogrammi_al_secondo = MOVIMENTO_FPS;
	/* ⛔ On the card there is no CRF: QP is asked, and QP is written. */
	r.modo = CODIFICATORE_QUALITA_QP;
	r.qualita = QP_HARDWARE;
	/* ⛔⭐⭐ HERE THERE WAS `10`, WRITTEN BY HAND — and it is the defect measured
	 *      on 17 Aug 2026 on Firefox: 8 was declared in `ECCOMI` (§4.3) and 10
	 *      were sent on the wire.  ⇒ Now it is what the parent negotiated, and
	 *      the line above refuses to open if it does not know it. */
	r.profondita = prof;
	/* ⛔⭐⭐ THE CEILING OF §4.3, AND IT IS ASKED BEFORE INSTEAD OF DISCOVERED
	 *      AFTER — 23 Aug 2026.  Until tonight nobody asked for it: the encoder
	 *      chose the level from size and rate, and at 3840x2160 at 60/s it
	 *      chose **5.2** while the client had declared 5.1.
	 *
	 * ⛔ THE FALSIFIABLE PREDICTION, which is the point of the whole cure:
	 *      at 3840x2160 with `video.livello=5.1` imposed, the SPS MUST carry
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
	 *     `MOVIMENTO_FPS` asks for 60 (5.2 would grant 64).
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
	r.livello_x10 = (int) livello_chiesto_x10;
	r.formato = formato_ingresso;
	r.chiavi_ogni = 0;

	/*
	 * ⭐⭐ THE CARD, AND NOTHING ELSE — phase 19 (1 Oct 2026, `DECISIONI.md`
	 *     §10.27), the user's words: *"no cpu without a card"*.
	 *
	 * HEVC and H.264 open on the card (`hevc_vaapi`/`h264_vaapi` on
	 * `nodo_rendering`), with QP and not CRF.  `[M]` 13 Aug 2026: `h264_vaapi`
	 * **3.11-3.16 ms** per frame at 1920x1080 10 bits.  ⛔ If the card does not
	 * open we NO longer drop to a software encoder (OpenH264 and SVT-AV1 have
	 * left the product): the codec is not available on this machine, and that
	 * is said.  ⚠ It should not even get here: the parent tries it AT STARTUP
	 * (`figlio_capacita_video()`) and offers in `ECCOMI` only what the card can
	 * do — a browser that negotiates it anyway sees this line, and the code
	 * 0x06 of §6.2 after the wait.  ⛔ The codec is not changed under the
	 * client: it chose it (§4.3).
	 *
	 * ⚠ AV1: `[M]` 13 Aug 2026 `av1_vaapi` exits with *"No usable encoding
	 *   profile found"*, and `vainfo` gives AV1 as decode-only on both nodes
	 *   ⇒ AV1 on the card is not available, and in software no longer either.
	 */
	if (codec == CODIFICATORE_HEVC || codec == CODIFICATORE_H264) {
		/* ⭐ Phase 19: `h264_scheda`/`hevc_scheda` — the route is chosen by the
		 *    encoder by capability (Vulkan first, VA-API after), or the one
		 *    forced with `--codifica`.  Which one came out is told by the name. */
		r.componente = componente_di(codec);
		r.nodo_rendering = nodo_rendering;
		r.potenza = POTENZA_RENDERING;
		codif[indice] = codificatore_nuovo(&r, errore, sizeof errore);
		/* The reason also stays outside the log: `--prova-codifica` reports it
		 * in its `motivo`. */
		snprintf(rifiuto_hardware, sizeof rifiuto_hardware, "%s",
		         codif[indice] ? "" : errore);
		/* ⭐ 6 Oct 2026, `[M]` RTX 4090: the thirteenth concurrent encoding
		 *    returns VK_ERROR_TOO_MANY_OBJECTS.  The card is there and it is
		 *    FULL: saying "this codec is not available" would be false, and the
		 *    retry below picks it up as soon as a slot frees up. */
		if (!codif[indice] && strstr(rifiuto_hardware, "TOO_MANY_OBJECTS"))
			snprintf(errore, sizeof errore,
			         "«%s» on %.40s did not open (%.150s) ⇒ the card is there but has RUN OUT "
			         "of encoding slots (the driver's limit: `[M]` 12 at once on the "
			         "RTX 4090) — the session stays without an image until a slot "
			         "frees up",
			         r.componente, nodo_rendering, rifiuto_hardware);
		else if (!codif[indice])
			snprintf(errore, sizeof errore,
			         "«%s» on %.40s did not open (%.150s) ⇒ this codec is NOT available on "
			         "this machine: without a card there is no encoding (phase 19)",
			         r.componente, nodo_rendering, rifiuto_hardware);
	} else {
		snprintf(rifiuto_hardware, sizeof rifiuto_hardware,
		         "codec %d is not encoded on the card (AV1: decode only)",
		         (int) codec);
		snprintf(errore, sizeof errore, "%.400s — and without a card there is no encoding (phase 19)",
		         rifiuto_hardware);
	}
	if (codif[indice]) {
		codif_prof[indice] = prof;
		codif_liv[indice] = livello_chiesto_x10;
		codif_fmt[indice] = formato_ingresso;
	}
	if (!codif[indice]) {
		/* ⛔ The wait grows, and the line SAYS so: without it, this branch wrote
		 *    the log in bursts and burned a core — the same form as the 30.8 GB
		 *    of 14 August, in another point of the loop. */
		codif_attesa_ms[indice] = codif_attesa_ms[indice]
		                              ? codif_attesa_ms[indice] * 2
		                              : CODIF_RIPROVA_MIN_MS;
		if (codif_attesa_ms[indice] > CODIF_RIPROVA_MAX_MS)
			codif_attesa_ms[indice] = CODIF_RIPROVA_MAX_MS;
		codif_riprova_ms[indice] = registro_ora_ms() + codif_attesa_ms[indice];
		registro_dice(REG_FIGLIO,
		              "⛔ no video for codec %d: %s.  ⚠ Retrying in %llu "
		              "ms — not at every frame, or it would be sixty contexts "
		              "opened and closed per second",
		              (int)codec, errore,
		              (unsigned long long)codif_attesa_ms[indice]);
		return NULL;
	}
	/* ⭐ Succeeded: the wait is reset, or the next failure would start from the
	 *    bottom of the previous one. */
	codif_riprova_ms[indice] = 0;
	codif_attesa_ms[indice] = 0;
	/* ⭐ And the name carries the EFFECTIVE entrypoint (with node and vendor),
	 *    not the requested one: with `LA_DICHIARATA` they are two different
	 *    things until the driver has answered, and this is the line that says
	 *    it. */
	registro_dice(REG_FIGLIO,
	              "⭐ PHASE 3: encoder %d OPENED and KEPT ALIVE from one "
	              "frame to the next, %ux%u at %d/s — without this "
	              "prediction would not exist and every frame would be a "
	              "keyframe · route %s (requested «%s») · in force: %s",
	              (int)codec, tela_l, tela_a, MOVIMENTO_FPS,
	              codificatore_strada(codif[indice]), strada_codifica,
	              codificatore_nome(codif[indice]));
	return codif[indice];
}

static void codificatori_libera(void)
{
	for (uint8_t i = 0; i < CODEC_MAX; i++) {
		if (!codif[i])
			continue;
		codificatore_libera(codif[i]);
		codif[i] = NULL;
	}
}

/*
 * ⭐ PHASE 17 (§6.5-bis, §6.0 phase 7a) — `remotix --prova-codifica`.
 *
 * The installer's certification must know whether this machine really
 * encodes a frame in H.264 on the card: the answer is given by the product,
 * with its own choice, not by a separate program.  ⇒ It goes through
 * `codificatore_di()`, that is the road of a real session (H.264, 8 bits — the
 * baseline of §4.3 —, no level ceiling, BGRx): `h264_vaapi` on
 * `NODO_RENDERING` with `POTENZA_RENDERING` and `QP_HARDWARE`.  Then a
 * synthetic 256x256 frame is really encoded, until bytes come out (at most 8
 * rounds).
 *
 * ⛔ PHASE 19 (1 Oct 2026, `DECISIONI.md` §10.27) — *"no cpu without a
 *    card"*: if the card does not open there is no longer the software
 *    fallback (OpenH264), and the test DECLARES it with a code of its own.
 *
 * It exits with ONE JSON line on stdout (the log goes to stderr, as always):
 *   {"esito":"hardware"|"nessuno","codificatore":"h264_vulkan"|"h264_vaapi"|"",
 *    "strada":"vulkan"|"vaapi"|"",
 *    "nodo":"/dev/dri/renderD128"|"","motivo":"...",
 *    "codec":"h264"|"hevc","offerti":"hevc,h264"|"h264"|"",
 *    "hevc":"hardware"|"nessuno","h264":"hardware"|"nessuno",
 *    "hevc_strada":"vulkan"|"vaapi"|"","h264_strada":…}
 *   ⭐ PHASE 19: `strada` and `*_strada` say WHICH route of the card encoded
 *   (`DECISIONI.md` §10.27: Vulkan Video first, VA-API after); yesterday's
 *   fields stay as they were and the installer reads `esito` and the code.
 * and the exit code:
 *    0  the card encoded a frame, and the bytes read back;
 *    1  the card opens but the frame does not come out, or it is not known
 *       whether it is right;
 *    2  usage error;
 *    3  ⛔ NO CARD CAN ENCODE this codec (no node, no driver, a driver without
 *       encoding): REMOTIX does not encode here.
 *
 * THE OPTIONAL ARGUMENTS, after `--prova-codifica`:
 *      h264 | hevc          which codec to try (default h264, the baseline of §4.3)
 *      --nodo /dev/dri/…    the card to try instead of NODO_RENDERING (the
 *                           second card of a machine that has two, or a
 *                           node that does not exist to try the refusal)
 *      --codifica vaapi|vulkan|scheda   ⭐ phase 19: the route, forced (the two)
 *                           or by capability (`scheda`, the default)
 *    Without arguments it is the installer's call.  `offerti` is what the
 *    server WOULD OFFER to the browser with these same arguments.
 *
 * ⛔ "hardware" is said ONLY if the component accepts VA-API surfaces
 *    (`codificatore_in_hardware`) AND a frame came out with bytes AND the
 *    bytes were read back (`letto_dal_flusso`).  Everything not known becomes
 *    "nessuno" with the reason — never a presumed hardware.
 * ⚠ Root is not needed, but permissions matter: without the node's group
 *   (`render`) a user will see "nessuno" where root would see "hardware".  The
 *   test must be done with the identity one wants to know about.
 */
#define PROVA_LATO 256u
#define PROVA_GIRI 8
#define PROVA_NESSUNA_SCHEDA 3

/* ⭐ What this machine's card can do, codec by codec: it is the same question
 *    as `--prova-codifica`, asked at startup by the parent to decide what to
 *    offer in `ECCOMI` (`figlio_capacita_video()`). */
typedef struct {
	bool hevc_scheda;          /* the card opens and encodes HEVC on `nodo` */
	bool h264_scheda;          /* H.264 likewise */
	char nodo[64];
	char perche_hevc[768];     /* the reason, when not */
	char perche_h264[768];
	char strada_hevc[16];      /* ⭐ phase 19: "vulkan" / "vaapi" when yes, "" when not */
	char strada_h264[16];
} CapacitaVideo;

/* Opens the card for `codec` and encodes until bytes come out.  ⚠ It goes
 * through `codificatore_di()`, that is the session's road: it is the same
 * test the child will do.  The encoder stays open in `codif[]` (for the
 * confession): the caller frees it.  `*aperto` says whether the card opened —
 * the "no" of one that does not open and that of one that does not encode
 * are two different codes of `--prova-codifica`. */
static bool prova_un_codec(CodecVideo codec, uint8_t indice, char *motivo, size_t n,
                           size_t *byte_usciti, bool *aperto)
{
	static uint8_t pixel[PROVA_LATO * PROVA_LATO * 4];
	CodificatoreFotogramma fg;
	const CodificatoreConfessione *c;
	Codificatore *cod;
	bool uscito = false;

	*byte_usciti = 0;
	*aperto = false;
	profondita_chiesta = 8;
	livello_chiesto_x10 = 0;
	formato_ingresso = CODIFICATORE_PIXEL_BGRX;
	/* ⚠ It is REALLY tried, even if a round before already said no: the wait
	 *   between two attempts belongs to the session, not to the test — and
	 *   the reason is reset, or the one of the codec tried before would be
	 *   read. */
	codif_riprova_ms[indice] = 0;
	codif_attesa_ms[indice] = 0;
	rifiuto_hardware[0] = 0;
	cod = codificatore_di(codec, indice, PROVA_LATO, PROVA_LATO);
	if (!cod) {
		snprintf(motivo, n,
		         "no card can encode %s: «%s» on %s does not open (%s).  ⛔ REMOTIX "
		         "encodes only on the card (phase 19): without it, there is no video",
		         codec == CODIFICATORE_HEVC ? "HEVC" : "H.264", componente_di(codec),
		         nodo_rendering, rifiuto_hardware[0] ? rifiuto_hardware : "no reason");
		return false;
	}
	*aperto = true;
	for (int giro = 0; giro < PROVA_GIRI && !uscito; giro++) {
		/* A scrolling gradient: every frame differs from the previous one. */
		for (uint32_t y = 0; y < PROVA_LATO; y++)
			for (uint32_t x = 0; x < PROVA_LATO; x++) {
				uint8_t *p = pixel + (y * PROVA_LATO + x) * 4;

				p[0] = (uint8_t)(x + giro * 8);
				p[1] = (uint8_t)y;
				p[2] = (uint8_t)(x ^ y);
				p[3] = 0xff;
			}
		memset(&fg, 0, sizeof fg);
		if (!codificatore_comprimi(cod, pixel, PROVA_LATO * 4, &fg)) {
			c = codificatore_confessione(cod);
			snprintf(motivo, n, "«%s» opens but frame %d does not encode%s%s",
			         codificatore_nome(cod), giro + 1, c && c->perche_no[0] ? ": " : "",
			         c && c->perche_no[0] ? c->perche_no : "");
			return false;
		}
		if (fg.byte > 0) {
			uscito = true;
			*byte_usciti = fg.byte;
		}
		codificatore_rilascia(cod);
	}
	c = codificatore_confessione(cod);
	if (!uscito || !c || !c->ha_obbedito || !c->letto_dal_flusso
	    || !codificatore_in_hardware(cod)) {
		snprintf(motivo, n, "«%s» opens but after %d frames it is not known whether it encodes: %s",
		         codificatore_nome(cod), PROVA_GIRI,
		         !uscito ? "no byte came out"
		         : !c || !c->ha_obbedito ? "the encoder did not obey"
		         : !c->letto_dal_flusso  ? "the bytes do not read back"
		                                 : "it is not on the card");
		return false;
	}
	return true;
}

/* The measure, in this process: two questions, and each "no" with its reason. */
static void capacita_video_misura(CapacitaVideo *cv)
{
	size_t byte;
	bool aperto;
	char motivo[768];

	memset(cv, 0, sizeof *cv);
	snprintf(cv->nodo, sizeof cv->nodo, "%s", nodo_rendering);
	cv->hevc_scheda = prova_un_codec(CODIFICATORE_HEVC, 1, motivo, sizeof motivo, &byte, &aperto);
	if (!cv->hevc_scheda)
		snprintf(cv->perche_hevc, sizeof cv->perche_hevc, "%s",
		         rifiuto_hardware[0] ? rifiuto_hardware : motivo);
	else
		snprintf(cv->strada_hevc, sizeof cv->strada_hevc, "%s", codificatore_strada(codif[1]));
	codificatori_libera();
	cv->h264_scheda = prova_un_codec(CODIFICATORE_H264, 3, motivo, sizeof motivo, &byte, &aperto);
	if (!cv->h264_scheda)
		snprintf(cv->perche_h264, sizeof cv->perche_h264, "%s",
		         rifiuto_hardware[0] ? rifiuto_hardware : motivo);
	else
		snprintf(cv->strada_h264, sizeof cv->strada_h264, "%s", codificatore_strada(codif[3]));
	codificatori_libera();
}

/* What is OFFERED, from the measure: "hevc,h264" · "hevc" · "h264" · "" (nothing). */
static void capacita_video_offerti(const CapacitaVideo *cv, char *dove, size_t n)
{
	snprintf(dove, n, "%s%s%s", cv->hevc_scheda ? "hevc" : "",
	         cv->hevc_scheda && cv->h264_scheda ? "," : "",
	         cv->h264_scheda ? "h264" : "");
}

/* One line that says everything, for the log and for the `motivo`. */
static void capacita_video_spiega(const CapacitaVideo *cv, char *dove, size_t n)
{
	snprintf(dove, n, "card %s (route requested «%s») — HEVC: %s%.300s%s · H.264: %s%.300s%s",
	         cv->nodo, strada_codifica,
	         cv->hevc_scheda ? "yes via " : "NO (",
	         cv->hevc_scheda ? cv->strada_hevc : cv->perche_hevc, cv->hevc_scheda ? "" : ")",
	         cv->h264_scheda ? "yes via " : "NO (",
	         cv->h264_scheda ? cv->strada_h264 : cv->perche_h264, cv->h264_scheda ? "" : ")");
}

bool figlio_capacita_video(char *offerti, size_t offerti_byte, char *spiegazione,
                           size_t spiegazione_byte)
{
	/* ═══════════════════════════════════════════════════════════════════════
	 * ⭐⭐ THE TEST AT STARTUP — phase 18, the user's decision (30 Sep 2026).
	 *
	 * The browser must NOT receive in `ECCOMI` a codec the server cannot do:
	 * HEVC and H.264 are there only if the CARD encodes them.  ⛔ Phase 19
	 * (1 Oct 2026, §10.27): the software fallback (OpenH264) has left — if the
	 * card cannot encode anything it is declared at startup, with the reason,
	 * and the negotiation ends in NIENTE_IN_COMUNE.
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
	CapacitaVideo cv;
	int tubo[2];
	pid_t pid;

	memset(&cv, 0, sizeof cv);
	if (pipe(tubo) != 0) {
		snprintf(spiegazione, spiegazione_byte, "the test's pipe does not open: %s",
		         strerror(errno));
		offerti[0] = 0;
		return false;
	}
	pid = fork();
	if (pid < 0) {
		snprintf(spiegazione, spiegazione_byte, "the test does not start (fork): %s",
		         strerror(errno));
		close(tubo[0]);
		close(tubo[1]);
		offerti[0] = 0;
		return false;
	}
	if (pid == 0) {
		close(tubo[0]);
		capacita_video_misura(&cv);
		codificatori_libera();
		{
			const uint8_t *p = (const uint8_t *) &cv;
			size_t resta = sizeof cv;
			while (resta) {
				ssize_t n = write(tubo[1], p, resta);
				if (n <= 0) {
					if (n < 0 && errno == EINTR)
						continue;
					break;
				}
				p += (size_t) n;
				resta -= (size_t) n;
			}
		}
		close(tubo[1]);
		_exit(0);
	}
	close(tubo[1]);
	{
		uint8_t *p = (uint8_t *) &cv;
		size_t letti = 0;
		/* ⚠ With a maximum time: a card that does not answer must not keep the
		 *   server without a port forever.  30 s is much more than the ~100 ms
		 *   the test costs; beyond that, it is declared and we go on without
		 *   video. */
		while (letti < sizeof cv) {
			struct pollfd pf = { .fd = tubo[0], .events = POLLIN };
			int pronto = poll(&pf, 1, 30000);
			if (pronto < 0 && errno == EINTR)
				continue;
			if (pronto <= 0)
				break;
			ssize_t n = read(tubo[0], p + letti, sizeof cv - letti);
			if (n < 0 && errno == EINTR)
				continue;
			if (n <= 0)
				break;
			letti += (size_t) n;
		}
		close(tubo[0]);
		if (letti < sizeof cv) {
			int stato = 0;
			kill(pid, SIGKILL);
			waitpid(pid, &stato, 0);
			snprintf(spiegazione, spiegazione_byte,
			         "⛔ the encoding test at startup did NOT answer (%zu bytes of %zu, %s): "
			         "no video codec is offered — «I don't know» is not a «yes»",
			         letti, sizeof cv,
			         WIFSIGNALED(stato) ? "killed by a signal" : "exited without saying anything");
			offerti[0] = 0;
			return false;
		}
		waitpid(pid, NULL, 0);
	}
	cv.nodo[sizeof cv.nodo - 1] = 0;
	cv.perche_hevc[sizeof cv.perche_hevc - 1] = 0;
	cv.perche_h264[sizeof cv.perche_h264 - 1] = 0;
	cv.strada_hevc[sizeof cv.strada_hevc - 1] = 0;
	cv.strada_h264[sizeof cv.strada_h264 - 1] = 0;
	capacita_video_offerti(&cv, offerti, offerti_byte);
	capacita_video_spiega(&cv, spiegazione, spiegazione_byte);
	return offerti[0] != 0;
}

static int prova_esce(const char *esito, const char *codificatore, const char *strada,
                      const char *nodo, const char *motivo, CodecVideo codec,
                      const CapacitaVideo *cv, int codice)
{
	char c[128], n[128], m[4096], o[32], r[64], s[32], sh[32], s4[32];

	json_testo(c, sizeof c, codificatore);
	json_testo(s, sizeof s, strada);
	json_testo(n, sizeof n, nodo);
	json_testo(m, sizeof m, motivo);
	capacita_video_offerti(cv, r, sizeof r);
	json_testo(o, sizeof o, r);
	json_testo(sh, sizeof sh, cv->strada_hevc);
	json_testo(s4, sizeof s4, cv->strada_h264);
	printf("{\"esito\":\"%s\",\"codificatore\":\"%s\",\"strada\":\"%s\",\"nodo\":\"%s\","
	       "\"motivo\":\"%s\",\"codec\":\"%s\",\"offerti\":\"%s\",\"hevc\":\"%s\",\"h264\":\"%s\","
	       "\"hevc_strada\":\"%s\",\"h264_strada\":\"%s\"}\n",
	       esito, c, s, n, m, codec == CODIFICATORE_HEVC ? "hevc" : "h264", o,
	       cv->hevc_scheda ? "hardware" : "nessuno", cv->h264_scheda ? "hardware" : "nessuno", sh,
	       s4);
	/* ⛔ A line that does not come out whole is "I don't know", not the outcome
	 *    it carried. */
	if (fflush(stdout) != 0)
		return 1;
	return codice;
}

int figlio_prova_codifica(int argc, char **argv)
{
	CodecVideo codec = CODIFICATORE_H264;
	uint8_t indice = 3; /* §6.2: 3 = H.264, 1 = HEVC */
	const CodificatoreConfessione *c;
	CapacitaVideo cv;
	char motivo[2048], spiega[1024];
	size_t byte = 0;
	bool aperto = false;

	for (int i = 0; i < argc; i++) {
		if (strcmp(argv[i], "h264") == 0) {
			codec = CODIFICATORE_H264;
			indice = 3;
		} else if (strcmp(argv[i], "hevc") == 0) {
			codec = CODIFICATORE_HEVC;
			indice = 1;
		} else if (strcmp(argv[i], "--nodo") == 0 && i + 1 < argc) {
			nodo_rendering = argv[++i];
		} else if (strcmp(argv[i], "--codifica") == 0 && i + 1 < argc
		           && figlio_codifica_strada(argv[i + 1])) {
			i++;
		} else {
			fprintf(stderr,
			        "usage: remotix --prova-codifica [h264|hevc] [--nodo /dev/dri/renderDN] "
			        "[--codifica scheda|vulkan|vaapi]\n"
			        "     (--software no longer exists: the software fallback has left, phase 19)\n");
			return 2;
		}
	}

	/* ⭐ First the whole picture (it is the same measure as at startup), then
	 *    the requested test: so the JSON line also says what the server would
	 *    offer. */
	capacita_video_misura(&cv);
	codificatori_libera();
	capacita_video_spiega(&cv, spiega, sizeof spiega);
	registro_dice(REG_FIGLIO, "--prova-codifica: %s", spiega);

	if (!prova_un_codec(codec, indice, motivo, sizeof motivo, &byte, &aperto)) {
		codificatori_libera();
		if (!aperto)
			registro_dice(REG_FIGLIO,
			              "⛔⛔ NO CARD CAN ENCODE %s on this machine: %s",
			              codec == CODIFICATORE_HEVC ? "HEVC" : "H.264", motivo);
		return prova_esce("nessuno", "", "", "", motivo, codec, &cv,
		                  aperto ? 1 : PROVA_NESSUNA_SCHEDA);
	}
	c = codificatore_confessione(codif[indice]);
	snprintf(motivo, sizeof motivo, "a %ux%u frame encoded: %zu bytes, %s — %s · %s",
	         PROVA_LATO, PROVA_LATO, byte, c->stringa_codec, codificatore_nome(codif[indice]),
	         spiega);
	{
		int fine = prova_esce("hardware", c->componente ? c->componente : "",
		                      codificatore_strada(codif[indice]), nodo_rendering, motivo, codec,
		                      &cv, 0);
		codificatori_libera();
		return fine;
	}
}

/* ⛔⭐ WHICH INSTANT ENDS UP IN THE 28 BYTES, AND WHERE IT COMES FROM — point 7,
 *     decided and MEASURED instead of inferred.
 *
 *     §6.2 says "microseconds of the **server's monotonic** clock at
 *     capture".  The two possible sources are:
 *
 *       a) `CLOCK_MONOTONIC` read by US **after** `cattura_prendi()` has
 *          returned — what phase 2 did.  ⚠ It is not the instant of capture:
 *          it is the instant we noticed, and it contains the whole wait in
 *          the exchange slot;
 *       b) the `pts` PipeWire attaches to the frame (`spa_meta_header`), which
 *          is the real instant — if it is the same clock.
 *
 *     ⛔ "If" is not a word to write in a decision (`LEZIONI.md`
 *        §2.3-quater): here we LOOK.  At the first grab the `pts` and our
 *        `CLOCK_MONOTONIC` are compared; if they are less than a second apart
 *        they are the same clock and the `pts` is taken, otherwise ours is
 *        taken and **it is written that we fell back** (`CODER.md` §4.2).
 *
 *     ⚠ The latency link of step 5 relies on this number: here is the line
 *       that says which of the two it is reading. */
static uint64_t istante_del_fotogramma(const CatturaFermo *fo, uint64_t nostro_us)
{
	uint64_t pts_us;

	if (!fo->seq_nota || fo->pts <= 0) {
		if (pts_e_monotono != 0) {
			pts_e_monotono = 0;
			registro_dice(REG_FIGLIO,
			              "⚠ the frame carries no `pts` (seq_nota %d, pts "
			              "%lld): the instant of the 28 bytes is OUR "
			              "CLOCK_MONOTONIC read after the grab — declared "
			              "fallback, and it contains the wait in the exchange "
			              "slot",
			              (int)fo->seq_nota, (long long)fo->pts);
		}
		return nostro_us;
	}
	pts_us = (uint64_t)fo->pts / 1000u;
	if (pts_e_monotono < 0) {
		uint64_t scarto = pts_us > nostro_us ? pts_us - nostro_us
		                                     : nostro_us - pts_us;
		pts_e_monotono = scarto < 1000000u ? 1 : 0;
		registro_dice(REG_FIGLIO,
		              pts_e_monotono
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
		              (unsigned long long)scarto);
	}
	return pts_e_monotono ? pts_us : nostro_us;
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
 *      and in a row, and the last is `resto`: what the total has beyond the
 *      sum of the others.  A growing `resto` is a piece of the stretch nobody
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
 *        │  measure      `misura_i_pixel()`: DIAGNOSTICS, every pixel, every round
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

#define TRATTI_VOCI 10
#define TRATTI_CAMPIONI 512

/* The order is that of the box: it is also the order in which they are printed. */
static const char *const tratti_nomi[TRATTI_VOCI] = {
	"producer", "allocation", "copy",     "in slot", "measure",
	"conversion", "upload", "encoding", "sending", "rest"
};
static uint32_t tratti_campione[TRATTI_CAMPIONI][TRATTI_VOCI];
static uint32_t tratti_totale[TRATTI_CAMPIONI];
static unsigned tratti_quanti; /* how many slots are full (stops at the cap) */
static unsigned tratti_prossimo;
static uint64_t tratti_visti;  /* how many frames in all */
static uint64_t tratti_detto_us;
/* ⛔ How many frames had to do without Mutter's `pts`: without this number the
 *    "producer" item would be an average between two different quantities. */
static uint64_t tratti_senza_pts;

/* ⭐ PHASE 16 (25 Sep 2026) — OUR PIECE, SECOND BY SECOND.
 *
 * ⛔ The STRETCH line is not enough to state §3.2 of SPECIFICHE ("only the
 *    piece that is ours is measured"), for two measured reasons (`fasi/16…`
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
#define NOSTRO_SECONDO_MAX 512
static uint32_t nostro_secondo[NOSTRO_SECONDO_MAX];
static unsigned nostro_quanti;

static int tratti_confronta(const void *a, const void *b)
{
	uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
	return x < y ? -1 : (x > y ? 1 : 0);
}

/* The median of an item over the kept sample.  ⚠ It is copied before sorting:
 * the sample is a ring and sorting it in place would destroy it. */
static uint32_t tratti_mediana(int voce, uint32_t *massimo)
{
	uint32_t copia[TRATTI_CAMPIONI];
	unsigned i, n = tratti_quanti;

	if (massimo)
		*massimo = 0;
	if (!n)
		return 0;
	for (i = 0; i < n; i++) {
		copia[i] = voce < 0 ? tratti_totale[i] : tratti_campione[i][voce];
		if (massimo && copia[i] > *massimo)
			*massimo = copia[i];
	}
	qsort(copia, n, sizeof copia[0], tratti_confronta);
	return copia[n / 2];
}

/*
 * Records a frame in the breakdown and, once per second, states it.
 *
 * ⚠ One line per frame would make the log unreadable precisely when it is
 *   needed — it is the same reason the rest of the loop speaks once per
 *   second (`figlio.c`, the loop's count).
 */
static void tratti_conta(const CatturaFermo *fo, const CodificatoreFotogramma *fg,
                         uint64_t us_spedizione, uint64_t us_fine)
{
	uint32_t *v = tratti_campione[tratti_prossimo];
	uint64_t pts_us, inizio, somma = 0;
	uint64_t totale;
	int i;

	/* ⛔ Without Mutter's `pts` the stretch has no REAL start: it starts from
	 *    the arrival in the slot and the "producer" item stays at zero, which
	 *    is a declared gap and not a measured zero. */
	if (pts_e_monotono == 1 && fo->seq_nota && fo->pts > 0) {
		pts_us = (uint64_t)fo->pts / 1000u;
		inizio = pts_us;
	} else {
		tratti_senza_pts++;
		inizio = fo->us_arrivo > (fo->us_copia + fo->us_allocazione)
		             ? fo->us_arrivo - fo->us_copia - fo->us_allocazione
		             : fo->us_arrivo;
	}
	if (us_fine <= inizio)
		return; /* clocks that do not subtract: no number is invented */
	totale = us_fine - inizio;

	memset(v, 0, sizeof tratti_campione[0]);
	/* "producer" = from when Mutter says it captured to when our callback
	 *  starts copying.  ⛔ The copy and the allocation are INSIDE the
	 *  pts→arrival interval, and are subtracted, or they would count twice. */
	{
		uint64_t fino_a_copia = fo->us_arrivo > (fo->us_copia + fo->us_allocazione)
		                            ? fo->us_arrivo - fo->us_copia - fo->us_allocazione
		                            : fo->us_arrivo;
		v[0] = fino_a_copia > inizio ? (uint32_t)(fino_a_copia - inizio) : 0u;
	}
	v[1] = (uint32_t)fo->us_allocazione;
	v[2] = (uint32_t)fo->us_copia;
	v[3] = (uint32_t)fo->us_nel_posto;
	v[4] = (uint32_t)fo->us_misura;
	v[5] = (uint32_t)fg->us_conversione;
	v[6] = (uint32_t)fg->us_caricamento;
	v[7] = (uint32_t)fg->us_codifica;
	v[8] = (uint32_t)us_spedizione;
	for (i = 0; i < TRATTI_VOCI - 1; i++)
		somma += v[i];
	v[9] = somma < totale ? (uint32_t)(totale - somma) : 0u;
	tratti_totale[tratti_prossimo] = totale > 0xffffffffu ? 0xffffffffu : (uint32_t)totale;
	if (nostro_quanti < NOSTRO_SECONDO_MAX) {
		uint64_t nostro = totale > v[0] ? totale - v[0] : 0u;
		nostro_secondo[nostro_quanti++] = nostro > 0xffffffffu ? 0xffffffffu
		                                                        : (uint32_t)nostro;
	}

	tratti_prossimo = (tratti_prossimo + 1) % TRATTI_CAMPIONI;
	if (tratti_quanti < TRATTI_CAMPIONI)
		tratti_quanti++;
	tratti_visti++;

	if (us_fine - tratti_detto_us < 1000000u)
		return;
	tratti_detto_us = us_fine;
	if (nostro_quanti) {
		unsigned n = nostro_quanti;
		qsort(nostro_secondo, n, sizeof nostro_secondo[0], tratti_confronta);
		/* p95 "nearest rank": with 30 frames it is the 29th, that is the
		 * second worst — not the average of two. */
		unsigned k = (n * 95 + 99) / 100;
		registro_dice(REG_FIGLIO,
		              "⭐ OURS in the second (copy → byte out, §3.2): p95 %.2f ms · "
		              "max %.2f · median %.2f · %u frames",
		              nostro_secondo[k ? k - 1 : 0] / 1000.0,
		              nostro_secondo[n - 1] / 1000.0, nostro_secondo[n / 2] / 1000.0, n);
		nostro_quanti = 0;
	}
	{
		char riga[512];
		size_t off = 0;
		uint32_t massimo_totale = 0;
		uint32_t mediana_totale = tratti_mediana(-1, &massimo_totale);

		for (i = 0; i < TRATTI_VOCI; i++) {
			uint32_t mx = 0, md = tratti_mediana(i, &mx);
			int scritto = snprintf(riga + off, sizeof riga - off, "%s%s %.2f (max %.2f)",
			                       i ? " · " : "", tratti_nomi[i], md / 1000.0,
			                       mx / 1000.0);
			if (scritto < 0 || (size_t)scritto >= sizeof riga - off)
				break;
			off += (size_t)scritto;
		}
		registro_dice(REG_FIGLIO,
		              "⭐ STRETCH capture → byte out: median %.2f ms (max %.2f) over %u "
		              "frames of the sample, %llu in all — %s%s",
		              mediana_totale / 1000.0, massimo_totale / 1000.0, tratti_quanti,
		              (unsigned long long)tratti_visti, riga,
		              tratti_senza_pts
		                  ? "  ⚠ and some frames have no Mutter `pts`: "
		                    "for those «producer» is a gap, not a zero"
		                  : "");
	}
}

/* Encodes a frame with the LIVE encoder of that codec and sends it to the
 * parent.  ⛔ `chiave` is not assumed: it is what the encoder read from the
 * stream (`fg.chiave`), and §6.2 writes it in the `tipo` field. */
static bool codifica_e_manda(const CatturaFermo *fo, CodecVideo codec,
                             uint8_t numero, const char *dir_rilievo,
                             const char *nome_file, uint64_t istante_us,
                             uint32_t tela_l, uint32_t tela_a, uint32_t input)
{
	CodificatoreFotogramma fg;
	Codificatore *cod;
	const CodificatoreConfessione *c;

	/* ⭐ PHASE 13 — the channel order is read from the frame, not assumed.
	 *    ⚠ Only `XBGR8888`/`ABGR8888` are `R G B x`: everything else stays
	 *    BGRx, that is exactly what GNOME and KDE had before (Mutter and KWin
	 *    give BGRx, and on the card's road this field decides nothing). */
	{
		const uint32_t xb24 = (uint32_t)'X' | ((uint32_t)'B' << 8) |
		                      ((uint32_t)'2' << 16) | ((uint32_t)'4' << 24);
		const uint32_t ab24 = (uint32_t)'A' | ((uint32_t)'B' << 8) |
		                      ((uint32_t)'2' << 16) | ((uint32_t)'4' << 24);
		FormatoPixel visto = (!fo->sulla_scheda &&
		                      (fo->formato_drm == xb24 || fo->formato_drm == ab24))
		                         ? CODIFICATORE_PIXEL_RGBX
		                         : CODIFICATORE_PIXEL_BGRX;

		if (visto != formato_ingresso) {
			registro_dice(REG_FIGLIO,
			              "⭐ the capture delivers the pixels in %s order: telling the "
			              "encoder instead of letting it assume",
			              visto == CODIFICATORE_PIXEL_RGBX ? "R G B x" : "B G R x");
			formato_ingresso = visto;
		}
	}

	cod = codificatore_di(codec, numero, tela_l, tela_a);
	if (!cod)
		return false;

	/* ⛔ §5.2 — AND HERE THE REQUESTED KEYFRAME BECOMES A REAL KEYFRAME.  ⚠ It is
	 *    asked BEFORE compressing: after would be one frame late, and that
	 *    frame is precisely the one the client is waiting for. */
	if (numero < CODEC_MAX && debito_chiave[numero]) {
		codificatore_chiedi_chiave(cod);
		debito_chiave[numero] = false;
	}

	/* ⛔⛔ AND HERE IT IS CHECKED WHETHER THE ENCODER IS REALLY IN HARDWARE —
	 *     asked of the COMPONENT (`componente_e_hardware`: it accepts a surface
	 *     format, not a pixel format), not read in the name and not inferred
	 *     from having opened a render node (`LEZIONI.md` §1.11).
	 *
	 * ⚠ Until phase 18 the case existed: `codificatore_di()` fell back to
	 *   software (H.264 beyond 4096 px, which `[M]` the driver refuses).  Since
	 *   phase 19 the fallback has left and `codificatore_di()` opens only the
	 *   card; the guard stays, because it costs one line and an encoder that
	 *   were not on the card must not receive a descriptor.  It is flagged,
	 *   and dismantling is left to the loop, which is the only one holding the
	 *   stage. */
	if (fo->sulla_scheda && !codificatore_in_hardware(cod)) {
		if (!scheda_da_abbandonare) {
			scheda_da_abbandonare = true;
			scheda_mai_piu = true;
			registro_dice(REG_FIGLIO,
			              "⛔⛔ the pixels are ON THE CARD and «%s» encodes in "
			              "SOFTWARE: zero copy is not viable with this "
			              "encoder.  ⇒ Remounting the stage on MEMORY and not "
			              "retrying — ⚠ and this line is the declaration, "
			              "because from here on the stretch's numbers are those "
			              "of the other road",
			              codificatore_nome(cod));
		}
		return false;
	}

	/* ⛔⛔⛔ AND HERE THE **MEASURED** STRIDE IS CHECKED, before compressing — see
	 *      the box in `codificatore.h`.
	 *
	 * ⚠ It is the only place where the real stride is known: `cattura.h` rule 1
	 *   says the stride is READ from the chunk and not computed, so before the
	 *   first frame there was nothing to look at.
	 * ⛔ And the frame is NOT sent: the defect it stops gives no error — it
	 *   gives a desktop skewed by a few pixels per row, which passes every
	 *   check on milliseconds and every check on colour.  Better a few frames
	 *   not sent and a remount, than a wrong image for the whole session. */
	if (fo->sulla_scheda && !codificatore_stride_importabile(fo->stride)) {
		if (!scheda_da_abbandonare) {
			scheda_da_abbandonare = true;
			scheda_negata_l = fo->larghezza;
			scheda_negata_a = fo->altezza;
			registro_dice(REG_FIGLIO,
			              "⛔⛔ the DMA-BUF stride is %u on a %ux%u canvas, and "
			              "it is NOT a multiple of %u: the driver would read the rows at "
			              "a stride of its own and the desktop would come out SKEWED, without "
			              "any error.  `[M]` 22 Aug 2026: at 1552 px the "
			              "mark reads (contrast 1.000), at 1544 it does not — eight "
			              "pixels of difference and opposite verdicts.  ⇒ Remounting the "
			              "stage on MEMORY for this canvas, and zero copy "
			              "will come back by itself on a canvas with a good stride",
			              fo->stride, fo->larghezza, fo->altezza,
			              codificatore_allineamento_scheda());
		}
		return false;
	}

	if (fo->sulla_scheda) {
		CodificatoreSuperficie sup = {
			.fd = fo->fd,
			.offset = fo->offset,
			.stride = fo->stride,
			.larghezza = fo->larghezza,
			.altezza = fo->altezza,
			.formato_drm = fo->formato_drm,
			.modificatore = fo->modificatore,
			.generazione = fo->generazione,
		};
		if (!codificatore_comprimi_scheda(cod, &sup, &fg)) {
			registro_dice(REG_FIGLIO,
			              "⛔ codec %d did not deliver the frame from the "
			              "CARD: `false` is NOT «an empty frame», it is "
			              "«this one is not sent»",
			              (int)codec);
			ciclo_guasti++;
			return false;
		}
	} else if (!codificatore_comprimi(cod, fo->pixel, fo->stride, &fg)) {
		registro_dice(REG_FIGLIO,
		              "⛔ codec %d did not deliver the frame: `false` "
		              "is NOT «an empty frame», it is «this one is not "
		              "sent»",
		              (int)codec);
		ciclo_guasti++;
		return false;
	}
	c = codificatore_confessione(cod);
	/* ⛔ The first is stated, the following go to chatter: at sixty per second
	 *    this line would make the whole rest of the log unreadable — and that
	 *    is precisely the case in which the rest of the log is needed. */
	if (ciclo_fotogrammi == 0)
		registro_dice(REG_FIGLIO,
		              "⭐ FIRST frame encoded: codec %d, %zu bytes, %s, "
		              "«%s», depth in the stream %d, level %d, promotion "
		              "8→10 %s, conversion %llu us, upload to the GPU %llu "
		              "us, encoding %llu us · %s%s",
		              (int)codec, fg.byte, fg.chiave ? "KEYFRAME" : "delta",
		              c->stringa_codec, c->profondita_flusso, c->livello_flusso,
		              c->promozione_8_a_10 ? "YES (declared)" : "no",
		              (unsigned long long)fg.us_conversione,
		              (unsigned long long)fg.us_caricamento,
		              (unsigned long long)fg.us_codifica,
		              codificatore_nome(cod),
		              fg.trattenuto ? " — ⚠ HELD BACK: the encoder has "
		                              "added one frame of delay" : "");
	/* ⛔⭐⭐ AND THE LEVEL IS DECLARED A SECOND TIME, IN PLAIN FORM — §4.3, line
	 *      701.  ⚠ It is not a repetition of the line above: that one gives the
	 *      RAW number of the SPS, which for HEVC is three times as much and for
	 *      AV1 is an index.  This one gives it in the form in which the client
	 *      asks for it (`video.livello=5.1`), which is the only one in which
	 *      the two numbers can be put in a column.
	 *
	 * ⛔⭐⭐ AND SINCE 23 AUG 2026 THE PROGRAM MAKES THE COMPARISON, because the
	 *      REQUESTED number has crossed the process boundary: the `CIAO`
	 *      (§4.3) → `rcp_livello_negoziato()` → `webtransport.c` → `main.c` →
	 *      `figli_video()` → `struct corpo_video.livello_x10` → here.  It is
	 *      the same chain the negotiated DEPTH travelled on 17 Aug 2026, for a
	 *      defect of the same family — and before tonight this box said *"the
	 *      comparison is made by whoever reads the log"*, which was honest and
	 *      not enough: `[M]` at 3840x2160 the client declared 5.1 and the
	 *      server produced **5.2**, for weeks, and nobody noticed.
	 *
	 * ⛔ AND THE COMPARISON IS NOT THE CURE: the cure is **not exceeding**, and
	 *    it lives at the encoder's opening (`codificatore_di()`,
	 *    `r.livello_x10`).  This line is the CHECK — R31, *"ask by name and
	 *    verify"* — and it reads the bytes PRODUCED, not the option passed: a
	 *    component that ignored `level` without saying so shows only here.
	 *
	 * ⚠ A level produced higher than the requested one gives no error: it gives
	 *   a black screen, and that is the reason the verdict is written in plain
	 *   form instead of staying a comparison in the reader's head. */
	if (ciclo_fotogrammi == 0) {
		unsigned decimi = livello_in_decimi(codec, c->livello_flusso);
		const char *alfabeto = codec == CODIFICATORE_H264   ? "level_idc"
		                       : codec == CODIFICATORE_HEVC ? "general_level_idc, "
		                                                      "which is three times as much"
		                                                    : "seq_level_idx";
		if (!decimi)
			registro_dice(REG_FIGLIO,
			              "⚠ §4.3 — LEVEL PRODUCED: I DON'T KNOW (the SPS has "
			              "%d, and I cannot translate it for this codec) — ⛔ and «I "
			              "don't know» does NOT mean «low»: it means the ceiling "
			              "of `video.livello` cannot be verified today",
			              c->livello_flusso);
		else if (!livello_chiesto_x10)
			registro_dice(REG_FIGLIO,
			              "⭐ §4.3 — LEVEL: produced %u.%u (in the SPS %d, that is "
			              "%s) · string for the decoder «%s» · REQUESTED: "
			              "nothing.  ⚠ §4.3 does not oblige the client to declare "
			              "`video.livello`: no ceiling to enforce — but "
			              "the server produces a level anyway, and it is "
			              "this one",
			              decimi / 10u, decimi % 10u, c->livello_flusso,
			              alfabeto, c->stringa_codec);
		else if (decimi <= livello_chiesto_x10)
			registro_dice(REG_FIGLIO,
			              "⭐ §4.3 — LEVEL: produced %u.%u ≤ requested %u.%u ✓ "
			              "(in the SPS %d, that is %s) · string for the "
			              "decoder «%s».  ⭐ The ceiling was IMPOSED "
			              "at opening and READ BACK from the bytes: it is R31",
			              decimi / 10u, decimi % 10u,
			              livello_chiesto_x10 / 10u, livello_chiesto_x10 % 10u,
			              c->livello_flusso, alfabeto, c->stringa_codec);
		else
			registro_dice(REG_FIGLIO,
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
			              decimi / 10u, decimi % 10u,
			              livello_chiesto_x10 / 10u, livello_chiesto_x10 % 10u,
			              c->livello_flusso, alfabeto, c->stringa_codec);
	}
	if (ciclo_fotogrammi != 0)
		registro_dettaglio(REG_FIGLIO,
		                   "codec %d: %zu bytes, %s, upload %llu us, "
		                   "encoding %llu us%s",
		                   (int)codec, fg.byte, fg.chiave ? "KEYFRAME" : "delta",
		                   (unsigned long long)fg.us_caricamento,
		                   (unsigned long long)fg.us_codifica,
		                   fg.trattenuto ? " — HELD BACK" : "");

	ciclo_fotogrammi++;
	if (fg.chiave)
		ciclo_chiavi++;

	{
		uint64_t t_spedizione = ora_monotona_us();
		manda_fotogramma(numero, fg.chiave, tela_l, tela_a, istante_us, fg.dati,
		                 fg.byte, input);
		{
			uint64_t t_fine = ora_monotona_us();
			tratti_conta(fo, &fg, t_fine - t_spedizione, t_fine);
		}
	}
	/* ⛔ The KEPT frame is still the one from switch-on — "send the stage
	 *    again" serves whoever comes back before the loop has delivered the
	 *    first.  ⚠ And only the KEYFRAME is kept: sending a delta again to
	 *    someone who does not have its past would be a wrecked image, that is
	 *    what §5.2 forbids the client to show. */
	if (numero < 3 && fg.chiave) {
		uint8_t *copia = (uint8_t *)malloc(fg.byte);
		if (copia) {
			memcpy(copia, fg.dati, fg.byte);
			free(tenuto[numero]);
			tenuto[numero] = copia;
			tenuto_byte[numero] = fg.byte;
			tenuto_chiave[numero] = true;
			tenuto_l = tela_l;
			tenuto_a = tela_a;
			tenuto_istante = istante_us;
			tenuto_input = input;
		}
	}
	/* ⛔ The survey is written only if someone asked for it, and only the
	 *    first: sixty files per second are not a survey, they are a full disk. */
	if (ciclo_fotogrammi <= 2)
		rilievo_scrivi(dir_rilievo, nome_file, fg.dati, fg.byte);

	/* ⭐ THE ON-DEMAND SNAPSHOT — the box is above `scatto_segnale()`. */
	/* ⛔ And a `SIGUSR2` arrived when nothing was in progress does NOT stay
	 *    pending.  `[M]` 20 Aug 2026: a snapshot closed by hand six minutes
	 *    earlier had left `scatto_stop` at 1, and the NEXT snapshot closed at
	 *    the first frame — "1 frames in `scatto-flusso.obu`".
	 *    ⚠ The survey was there and looked good: it is the worst form, a green
	 *    that looked at a single frame (`LEZIONI.md` §1.9). */
	if (scatto_stop && scatto_stato == 0)
		scatto_stop = 0;
	if (scatto_chiesto) {
		scatto_chiesto = 0;
		if (scatto_stato != 0) {
			registro_dice(REG_FIGLIO,
			              "⚠ SNAPSHOT: one is already in progress, the signal "
			              "does not open a second");
		} else if (!fo->pixel) {
			/* ⛔ On the card's road the pixels are not here: it is SAID,
			 *    instead of writing an empty file looking like a survey. */
			registro_dice(REG_FIGLIO,
			              "⛔ SNAPSHOT impossible: the pixels are not in memory "
			              "(card's road), there is nothing to write");
		} else if (!scatto_dir || !scatto_dir[0] || strcmp(scatto_dir, "-") == 0) {
			registro_dice(REG_FIGLIO,
			              "⛔ SNAPSHOT impossible: the server has no survey "
			              "folder (`--rilievo`), there is nowhere to write");
		} else {
			codificatore_chiedi_chiave(cod);
			scatto_stato = 1;
			scatto_quanti = 0;
			registro_dice(REG_FIGLIO,
			              "⭐ SNAPSHOT requested: asked for a KEYFRAME, and from "
			              "that one input and stream go on disk in «%s»",
			              scatto_dir);
		}
	}
	if (scatto_stato == 1 && fg.chiave && fo->pixel) {
		char percorso[512];

		/* ⛔ `rilievo_scrivi()` says BY ITSELF whether it wrote or not: the
		 *    line below tells the geometry, not the outcome — and the two
		 *    things no longer get mixed. */
		rilievo_scrivi(scatto_dir, "scatto-ingresso.bgrx", fo->pixel,
		               (size_t)fo->byte);
		registro_dice(REG_FIGLIO,
		              "⭐ SNAPSHOT: input %ux%u, stride %u, %llu bytes — the "
		              "stream starts from THIS keyframe",
		              fo->larghezza, fo->altezza, fo->stride,
		              (unsigned long long)fo->byte);
		snprintf(percorso, sizeof percorso, "%s/scatto-flusso.obu", scatto_dir);
		scatto_fp = fopen(percorso, "wb");
		if (!scatto_fp)
			registro_dice(REG_FIGLIO, "⛔ SNAPSHOT %s: %s", percorso,
			              strerror(errno));
		scatto_stato = scatto_fp ? 2 : 0;
		scatto_restano = SCATTO_FOTOGRAMMI;
	}
	if (scatto_stato == 2 && scatto_fp) {
		if (fwrite(fg.dati, 1, fg.byte, scatto_fp) != fg.byte)
			registro_dice(REG_FIGLIO,
			              "⛔ SNAPSHOT: short write on the stream — the file is NOT "
			              "decodable to the end");
		scatto_quanti++;
		if (scatto_stop || --scatto_restano <= 0) {
			scatto_chiudi(scatto_dir, fo,
			              scatto_stop ? "closed by hand with SIGUSR2"
			                          : "requested frames reached");
			scatto_stop = 0;
		}
	}

	codificatore_rilascia(cod);
	return true;
}

/* ⛔ The stage belongs to the SESSION, not to the connection: `mutter` and
 *    `cattura` stay open as long as the child lives, because the virtual
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
 *     the PipeWire stream goes into `connection error`, `cattura_prendi`
 *     returns **at once** with a fault, and the loop spun idle writing the log
 *     in bursts — ⛔ **30.8 GB and 112 million identical lines**, that is the
 *     disk of a real machine.
 *
 * ⇒ ⭐ They are the two ends of the same thing — *the child does not know its
 *   stage is no longer there, or not there yet* — and the cure is one: **the
 *   stage is mounted, dismantled and REMOUNTED**, with a growing wait.
 * ⚠ And it does not die: `SPECIFICHE.md` §8.3 forbids disconnecting, and a
 *   frozen session is worth more than a closed one.  ⛔ But a child **without
 *   a stage** is not a frozen session: it is a child that is of no use, and
 *   that is why it keeps retrying instead of sitting there.
 *
 * `primo` = it is the birth: the diagnosis is made (the two frames proving
 * that the stage works) and the survey is written.  ⚠ Not on a remount: those
 * two are not frames of the movement, and redoing them would reset the loop's
 * counts in the middle of a live session. */
static bool prendi_il_palco(uint32_t tela_l, uint32_t tela_a,
                            const char *dir_rilievo, bool primo,
                            MutterSessione **fuori_m, Cattura **fuori_c)
{
	struct corpo_palco p;
	GError *sbaglio = NULL;
	GDBusConnection *bus;
	CatturaFermo fo;
	CatturaPresa presa;
	uint64_t istante_us;
	MutterSessione *mut = NULL;
	Cattura *cat = NULL;
	/* ⏱ the steps' stopwatch — see the box below */
	const char *crono_nome = "";
	uint64_t crono_ms = 0;

	/* ⛔⛔⭐ THE ENVELOPE IS ZEROED HERE, BEFORE ANY EXIT PATH — and until
	 *       27 Aug 2026 this `memset` sat THREE HUNDRED lines further down,
	 *       that is **after** a `manda(MSG_PALCO, &p, …)`.
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
	 *   to unmask it, and it is also `LEZIONI.md` §1.50: a right comment in
	 *   the wrong place protects nothing.
	 *
	 * ⛔ Whoever adds an early exit to this function no longer needs to think
	 *    about it: above this line nothing is sent, below it the envelope is
	 *    clean and declares "I could not look". */
	memset(&p, 0, sizeof p);
	/* ⛔ "I could not look" is the STARTING value, not "healthy": with the zero
	 *    of the `memset` an early exit path would have reported
	 *    `SESSIONE_SANA` without having looked at anything — "empty" and
	 *    "forbidden" with the same face, error form E8, inside the line meant
	 *    to unmask it.  `[M]` seen in the log of 12 Aug 2026: the stage of
	 *    "prova" said "session 0" and nobody had read it. */
	p.stato_sessione = (uint32_t)SESSIONE_NON_LETTA;

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
	 *   the two lines there is only `manda()`: if the seconds are there, they
	 *   show.
	 */
	registro_dettaglio(REG_FIGLIO,
	                   "entering the stage mounting (canvas %ux%u): telling the parent "
	                   "to wait",
	                   tela_l, tela_a);

	/*
	 * ⛔⭐⭐⭐ NOTHING IS MADE TO BE BORN UNTIL THE SIZE IS KNOWN.
	 *
	 * ⭐ It is the cure for the tail of login times, and the reason is spelled
	 *    out in full in the box of `tela_dal_cliente`: a stage mounted at the
	 *    fallback must be resized, and on Wayland the resize completes only
	 *    when the compositor delivers a frame — that is NEVER, on a freshly
	 *    born desktop that does not move.
	 *
	 * ⚠ Half a second of waiting here is worth thirteen seconds of race later.
	 *
	 * ⛔ And the wait has a CEILING, it is not forever: invariant I1 forbids
	 *    standing still out of caution.  If the client does not declare its
	 *    window within `TELA_ATTESA_MS`, we start with the fallback and
	 *    DECLARE it — better a desktop to resize than no desktop.
	 */
	if (!tela_dal_cliente) {
		static uint64_t primo_giro_ms;
		uint64_t adesso = registro_ora_ms();

		if (primo_giro_ms == 0)
			primo_giro_ms = adesso;
		if (adesso - primo_giro_ms < TELA_ATTESA_MS) {
			registro_dettaglio(REG_FIGLIO,
			                   "waiting for the client's canvas before making anything "
			                   "be born (%llu ms of %d): mounting at the fallback "
			                   "would mean resizing, and the "
			                   "resize on a still scene does not "
			                   "complete",
			                   (unsigned long long)(adesso - primo_giro_ms),
			                   TELA_ATTESA_MS);
			p.stato_sessione = (uint32_t)SESSIONE_NON_LETTA;
			snprintf(p.guasto, sizeof p.guasto,
			         "waiting for the client's canvas");
			manda(MSG_PALCO, &p, sizeof p, NULL, 0);
			return false;
		}
		if (!tela_dal_cliente) {
			static bool detto;

			if (!detto) {
				detto = true;
				registro_dice(REG_FIGLIO,
				              "⚠ the client did not declare its window "
				              "within %d ms: starting with the fallback %ux%u.  ⛔ The "
				              "desktop will be born at a size nobody "
				              "asked for and will have to be resized — but a desktop "
				              "to resize beats no desktop (I1)",
				              TELA_ATTESA_MS, tela_l, tela_a);
			}
		}
	}
	if (tela_l && tela_a)
		attendi_tela(tela_l, tela_a);
	registro_dettaglio(REG_FIGLIO, "the «wait» has gone out: now the bus");

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
	 *    always paid for (`LEZIONI.md` §1.9: silence and health with the same
	 *    face).
	 *
	 * ⚠ And it is written only when the step is SLOW: a fast step has nothing
	 *   to say, and filling the log with normal lines is the way to make the
	 *   ones that count go unread.
	 */
#define PASSO_LENTO_MS 250
#define CRONO_INIZIO(nome) \
	do { \
		crono_nome = (nome); \
		crono_ms = registro_ora_ms(); \
	} while (0)
#define CRONO_FINE() \
	do { \
		uint64_t crono_durata = registro_ora_ms() - crono_ms; \
		if (crono_durata >= PASSO_LENTO_MS) \
			registro_dice(REG_FIGLIO, \
			              "⏱ the step «%s» took %llu ms — it is THAT step that " \
			              "holds the child still, not «the session being born»", \
			              crono_nome, (unsigned long long)crono_durata); \
	} while (0)

	/* ⚠ `memset(&p, …)` and `p.stato_sessione = SESSIONE_NON_LETTA` used to be
	 *   HERE, and from here they did not cover the `manda(MSG_PALCO, …)` of the
	 *   "waiting for the client's canvas" branch, which is further up.  ⇒ Moved
	 *   to the top of the function, 27 Aug 2026: the full reason is written
	 *   there. */

	/* ⛔⭐ THE BUS, AND IT IS THE MEASURE THAT DECIDES THE WHOLE MANDATE.  `[M]`
	 *     root does not connect here; this process is the user, and it either
	 *     connects or says why. */
	CRONO_INIZIO("open the session bus");
	bus = sessione_bus(&sbaglio);
	CRONO_FINE();
	if (!bus) {
		snprintf(p.guasto, sizeof p.guasto, "session bus: %s",
		         sbaglio ? sbaglio->message : "(no details)");
		registro_dice(REG_FIGLIO,
		              "⛔ I do NOT have the session bus: %s.  ⚠ It is not «there is "
		              "no session», it is «I could not look» — and without a bus there "
		              "is nothing to capture",
		              p.guasto);
		g_clear_error(&sbaglio);
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}
	p.bus_aperto = 1;
	g_object_unref(bus);
	registro_dice(REG_FIGLIO,
	              "⭐ THE SESSION BUS IS MINE: connected as uid %ld — the "
	              "thing the root parent CANNOT do (P2-6-montaggio.md §5.4)",
	              (long)geteuid());

	/*
	 * ⛔⭐⭐ AND NOW WE TOUCH — 15 Aug 2026, phase 5.
	 *
	 * ⛔ Here it said "look, don't touch: making a session BE BORN belongs to
	 *    the real login, not to this mandate", and for phase 2 it was right.
	 *    ⭐ At phase 5 that mandate **is this one** — `PIANO.md`: "Produces:
	 *    PAM in full" — and since this process opens the PAM session itself
	 *    (`diventa_ed_esegui`, step 2-bis) `/run/user/<uid>` exists by
	 *    construction: the objection that line carried has fallen.
	 *
	 * ⛔ THE PRICE OF NOT DOING IT, measured on the evening of 15 Aug: the
	 *    machine reboots, nobody remakes the session, and the user enters and
	 *    **sees nothing**.  The log said three times "SESSION DEAD: I look and
	 *    don't touch", which is a perfect diagnosis of a product that does not
	 *    do its job.
	 *
	 * ⚠ AND IT DOES NOT WAIT: `sessione_fai_nascere()` asks and returns.  The
	 *   wait already exists and is our retry loop (1 s → 30 s); a second wait
	 *   inside this process would be 40 s in which the parent receives neither
	 *   a frame nor an answer (`LEZIONI.md` §6.2-bis).
	 *
	 * ⚠ And it is asked at most once a minute: `gnome-session` takes a few
	 *   seconds to show up on the bus, and without this rein every retry would
	 *   start another one.
	 */
	CRONO_INIZIO("read the session state (GetCurrentState)");
	p.stato_sessione = (uint32_t)sessione_stato(tela_l, tela_a, NULL);
	CRONO_FINE();
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
		 *       (`DECISIONI.md` §4.1-quater: "the page goes back to the login
		 *       form").
		 *
		 * ⚠ And the same holds if the compositor DIED by itself: from our side
		 *   it is indistinguishable from a logout, and the right behaviour is
		 *   the same — telling whoever is watching instead of making a desktop
		 *   the user had closed reappear.
		 */
		if (p.stato_sessione != SESSIONE_MORTA &&
		    p.stato_sessione != SESSIONE_NON_LETTA)
			vista_viva = true;
		else if (p.stato_sessione == SESSIONE_MORTA && vista_viva) {
			vista_viva = false;
			sessione_chiusa_dall_utente = true;
			registro_dice(REG_FIGLIO,
			              "⭐ §7.6: the graphical session WAS THERE and now is NO "
			              "LONGER — the user logged out from the "
			              "desktop menu.  ⛔ I am NOT making it be born again: remaking it "
			              "would mean preventing them from logging out.  Warning the "
			              "parent, which gives whoever is watching the farewell 0x10");
			manda(MSG_SESSIONE_FINITA, NULL, 0, NULL, 0);
			manda(MSG_PALCO, &p, sizeof p, NULL, 0);
			/* ⭐ and nobody who had detached from the desktop stays in the scope */
			sessione_sgombera_scope();
			/* ⭐ R1/R2: the user at the monitor finds the manager as it was */
			sessione_sgombera_gestore("the session is over (§7.6)");
			return false;
		}
	}
	if (p.stato_sessione == SESSIONE_MORTA && sessione_chiusa_dall_utente) {
		/* ⛔ The third state: the user LOGGED OUT.  Remaking it now would mean
		 *    making the desktop they just closed reappear — that is preventing
		 *    them from logging out.  A NEW attach is awaited. */
		registro_dettaglio(REG_FIGLIO,
		                   "the graphical session of «%s» was CLOSED "
		                   "by the user: not remaking it until someone "
		                   "reattaches",
		                   g_get_user_name());
	} else if (p.stato_sessione == SESSIONE_MORTA) {
		uint64_t adesso_ms = registro_ora_ms();

		if (!sta_nascendo(adesso_ms)) {
			nascita_chiesta_ms = adesso_ms;
			registro_dice(REG_FIGLIO,
			              "⭐ no graphical session for «%s»: I AM MAKING IT "
			              "BE BORN (canvas %ux%u) and returning at once — "
			              "finding it is the next attempt's job",
			              g_get_user_name(), tela_l, tela_a);
			if (!sessione_fai_nascere(tela_l, tela_a))
				registro_dice(REG_FIGLIO,
				              "⛔ the graphical session of «%s» did not "
				              "start: the stage will be left with nothing to "
				              "capture, and the «sessione» lines above "
				              "say why",
				              g_get_user_name());
		} else {
			registro_dice(REG_FIGLIO,
			              "the graphical session of «%s» is not there yet: "
			              "I already asked for it %llu ms ago and am waiting for it "
			              "to show up on the bus",
			              g_get_user_name(),
			              (unsigned long long)(adesso_ms - nascita_chiesta_ms));
		}
	} else if (p.stato_sessione != SESSIONE_SANA) {
		registro_dice(REG_FIGLIO,
		              "⚠ this user's graphical session is «%s» (%u): "
		              "not touching it — states other than «dead» are governed by "
		              "sessione_assicura(), and bringing down a live one would take "
		              "the desktop away from whoever is watching it (I4)",
		              sessione_marca((SessioneStato)p.stato_sessione),
		              p.stato_sessione);
	}

	/*
	 * ⛔⭐⭐ WE DO NOT MOUNT ON TOP OF A COMPOSITOR THAT HAS NOT ANSWERED — 16 Aug
	 *       2026, and it is the other half of `ATTESA_SONDAGGIO_MS`.
	 *
	 * ⛔ `SESSIONE_NON_LETTA` does not mean "not there" and does not mean
	 *    "there": it means **"it has its name on the bus and did not answer
	 *    me"**, that is it is still being born.  ⇒ Going on to mount would
	 *    mean making a more expensive call to that same silent compositor —
	 *    `CreateSession` on RemoteDesktop, which in `mutter.c` has a ceiling
	 *    of **fifteen seconds**.
	 *
	 * ⚠ That is, the block would be moved instead of removed: the short poll
	 *   would serve no purpose, and the child would stay silent all the same.
	 *
	 * ⭐ The right answer is the one the loop already knows how to use: "not
	 *    now".  We return, say "WAIT" to the parent, and retry in 200 ms.
	 */
	if (p.stato_sessione == (uint32_t)SESSIONE_NON_LETTA) {
		snprintf(p.guasto, sizeof p.guasto,
		         "the compositor did not answer the poll: it is still being born");
		registro_dettaglio(REG_FIGLIO,
		                   "the compositor of «%s» has its name on the bus but did not "
		                   "answer within the poll: I am NOT trying to mount on "
		                   "top of it — it would be a fifteen-second call to "
		                   "someone who does not answer.  Retrying shortly",
		                   g_get_user_name());
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}

	/*
	 * ⭐⭐ PHASE 13 — ON XFCE THERE IS NO STAGE TO OPEN FIRST.
	 *
	 * On GNOME Mutter is asked for a virtual monitor; on KDE KWin is asked for
	 * the stream of the one that exists.  ⛔ On wlroots there is no stream to
	 * mount: we talk directly to the compositor, and the source is the capture
	 * itself (`cattura_avvia_wlr`, further down).
	 *
	 * ⇒ Nothing is done here, and we say why: an empty branch without a line
	 *   looks like a forgotten branch.
	 */
	/* ⭐ PHASE 14 — `sessione_su_wlroots()` and not `== XFCE`, here and in the
	 *    other four places of this file (capture, input, clipboard, remount):
	 *    the question is about the COMPOSITOR, and labwc serves XFCE and LXQt
	 *    (`sessione.h`).  ⛔ With `== XFCE` LXQt fell into the GNOME/KDE branch,
	 *    without a warning. */
	if (sessione_su_wlroots()) {
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
		 * ⭐ The cure is the form of `SESSIONE_NON_LETTA` above: "not now".  We
		 *    return, the parent hears WAIT, and the loop retries densely
		 *    (`PALCO_NASCITA_RIPROVA_MS`, while it is being born or someone is
		 *    watching).  The mounting that succeeds has read SANA, and
		 *    `vista_viva` is true by construction.
		 * ⛔ And the birth is NOT requested at every round: the rein is
		 *    `sta_nascendo()` (above), and after the rein
		 *    `sessione_fai_nascere()` refuses while labwc is alive
		 *    (`unita_inattiva()`).  It is the same fate as GNOME when Mutter
		 *    does not appear: the mounting fails and is retried.
		 * ⚠ And if the manager NEVER appears (broken session) we do not stay
		 *   silent: every five seconds a line says so, with the time since the
		 *   birth was requested.
		 */
		if (p.stato_sessione == SESSIONE_MORTA) {
			static uint64_t detto_ms;
			uint64_t ora_ms = registro_ora_ms();

			snprintf(p.guasto, sizeof p.guasto,
			         "the session manager is not on the bus yet");
			if (ora_ms - detto_ms >= 5000) {
				detto_ms = ora_ms;
				registro_dice(REG_FIGLIO,
				              "⏳ %s: labwc perhaps is there, the session manager "
				              "is NOT (birth requested %llu ms ago) — ⛔ not mounting "
				              "the capture: a mounting that reads DEAD does not "
				              "turn on «seen alive», and the «Log out» after would make it "
				              "BE BORN AGAIN.  Retrying shortly",
				              sessione_desktop() == SESSIONE_DESKTOP_LXQT ? "LXQt" : "XFCE",
				              nascita_chiesta_ms
				                  ? (unsigned long long)(ora_ms - nascita_chiesta_ms)
				                  : 0ULL);
			}
			manda(MSG_PALCO, &p, sizeof p, NULL, 0);
			return false;
		}
		registro_dettaglio(REG_FIGLIO,
		                   "%s: no stage to open — on this family the "
		                   "capture talks to the compositor without going through a "
		                   "mounted stream",
		                   sessione_desktop() == SESSIONE_DESKTOP_LXQT ? "LXQt" : "XFCE");
		/*
		 * ⛔⛔ AND HERE `vista_viva = true` IS NOT WRITTEN — 21 Sep 2026, and it
		 *     cost the user's farewell.
		 *
		 * `[M]` The first draft wrote it, by analogy with the KDE branch.  But
		 * on KDE it comes AFTER a successful `kwin_apri()`, that is after a
		 * fact; here it came before any fact.  ⇒ The capture tried to open half
		 * a second before labwc was ready, failed, and at the next round the
		 * state said DEAD with `vista_viva` already true: *"the session was
		 * there and now it is no longer — the user logged out"*, farewell
		 * 0x10, and the client thrown out of a desktop that was being born.
		 * ⭐ On XFCE "seen alive" is already set by reading the state, when the
		 *   session manager appears on the bus: that is the right fact, and it
		 *   is enough.
		 */
	} else if (sessione_desktop() == SESSIONE_DESKTOP_KDE) {
		/* ⭐ On KDE the monitor is already there (`kwin_wayland --virtual`, born
		 *    with the session): KWin is asked for its stream.  The GNOME branch
		 *    below is not touched. */
		chiudi_palco_kwin();
		CRONO_INIZIO("mount the stage (kwin_apri)");
		palco_kwin = kwin_apri(&sbaglio);
		CRONO_FINE();
		if (!palco_kwin) {
			snprintf(p.guasto, sizeof p.guasto, "KWin: %s",
			         sbaglio ? sbaglio->message : "(no details)");
			registro_dice(REG_FIGLIO, "⛔ no stream from KWin: %s", p.guasto);
			g_clear_error(&sbaglio);
			manda(MSG_PALCO, &p, sizeof p, NULL, 0);
			return false;
		}
		vista_viva = true;
	} else {
	CRONO_INIZIO("mount the stage (mutter_apri)");
	mut = mutter_apri(&sbaglio);
	CRONO_FINE();
	if (!mut) {
		snprintf(p.guasto, sizeof p.guasto, "ScreenCast: %s",
		         sbaglio ? sbaglio->message : "(no details)");
		registro_dice(REG_FIGLIO, "⛔ no virtual monitor to capture: %s",
		              p.guasto);
		g_clear_error(&sbaglio);
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}
	}

	/* ⭐ PHASE 17 — we come back here ONCE, if the card was refused:
	 *    `ripiega_se_rifiutata()`.  The stage (Mutter or KWin) stays the same. */
rimonta_la_cattura:
	/* ⛔ The rate is asked ONCE and with ONE name: `MOVIMENTO_FPS`.  Here there
	 *    was the literal 60 and the encoding request declared 30 — two
	 *    different numbers for the same quantity. */
	/* ⛔ The route is DECLARED in the log at mounting, because it is the fact
	 *    that explains all the stretch numbers that will come later: a
	 *    "conversion 0.9 ms" on the card and one on memory are not the same
	 *    quantity. */
	registro_dice(REG_FIGLIO,
	              "⭐ the stage mounts on the «%s» route%s",
	              strada_del_palco == CATTURA_STRADA_SCHEDA
	                  ? "CARD (DMA-BUF, zero copy)"
	                  : "MEMORY (the pixels are copied)",
	              strada_del_palco == CATTURA_STRADA_SCHEDA
	                  ? " — ⚠ it holds only if the encoder is in hardware, and if it "
	                    "is not this stage is remounted on memory, declaring it"
	                  : "");
	misura_del_palco(&tela_l, &tela_a);
	/* ⭐ PHASE 13 — the other door: the source within reach.  ⛔ `nodo_del_palco()`
	 *    is not even called, because on this family a node does not exist. */
	if (sessione_su_wlroots()) {
		lastre_per_la_strada();
		cat = cattura_avvia_wlr(tela_l, tela_a, MOVIMENTO_FPS, strada_del_palco,
		                        CATTURA_COLORE_BGRX, &sbaglio);
	} else {
		modificatori_per_la_strada();
		cat = cattura_avvia(nodo_del_palco(mut), tela_l, tela_a, MOVIMENTO_FPS,
		                    strada_del_palco, CATTURA_COLORE_BGRX, NULL, NULL,
		                    NULL, &sbaglio);
	}
	if (!cat && ripiega_se_rifiutata(
	                sbaglio && g_error_matches(sbaglio, G_IO_ERROR,
	                                           G_IO_ERROR_NOT_SUPPORTED),
	                sbaglio ? sbaglio->message : NULL)) {
		g_clear_error(&sbaglio);
		goto rimonta_la_cattura;
	}
	if (!cat) {
		snprintf(p.guasto, sizeof p.guasto, "capture: %s",
		         sbaglio ? sbaglio->message : "(no details)");
		registro_dice(REG_FIGLIO, "⛔ the capture does not open: %s", p.guasto);
		g_clear_error(&sbaglio);
		mutter_chiudi(mut);
		chiudi_palco_kwin();
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}
	/* ⭐ PHASE 12 — on Plasma the cursor theme is invisible on purpose
	 *    (`sessione.c`), so the metadata will always say "no image": that
	 *    hiding must NOT be delivered, or whoever is watching is left without a
	 *    pointer (`cursore.h`, and `[M]` the user's test of 20 Sep 2026). */
	if (palco_kwin)
		cattura_cursore_mai_nascondere(cat, "KWin --virtual: the session's cursor "
		                                    "theme is invisible");
	*fuori_m = mut;
	*fuori_c = cat;

	memset(&fo, 0, sizeof fo);
	presa = cattura_prendi(cat, 5.0, &fo, &sbaglio);
	istante_us = istante_del_fotogramma(&fo, ora_monotona_us());
	p.presa = (uint32_t)presa;
	/* ⛔ `PIXEL_ALTROVE` IS A DELIVERED FRAME, not a no-show: on the card's
	 *    road the pixels are not in memory, and the frame is there all the
	 *    same (`cattura.h`).  ⚠ Treating it as a fault here would mean
	 *    dismantling the stage at every successful mounting. */
	/* ⭐ PHASE 17 — the refusal that arrives AFTER `cattura_avvia()`: it is the
	 *    measured case (`[M]` 29 Sep, grab 2 "fell during the grab, fault: no
	 *    more input formats").  Only the capture is stopped, and reopened. */
	if (presa != CATTURA_PRESA_FATTA && presa != CATTURA_PRESA_PIXEL_ALTROVE &&
	    ripiega_se_rifiutata(cattura_formato_rifiutato(cat),
	                         cattura_guasto(cat))) {
		g_clear_error(&sbaglio);
		cattura_fermo_libera(&fo);
		cattura_ferma(cat);
		cat = NULL;
		*fuori_c = NULL;
		goto rimonta_la_cattura;
	}
	if (presa != CATTURA_PRESA_FATTA && presa != CATTURA_PRESA_PIXEL_ALTROVE) {
		snprintf(p.guasto, sizeof p.guasto, "grab %u: %s", (unsigned)presa,
		         sbaglio ? sbaglio->message : "no frame");
		registro_dice(REG_FIGLIO,
		              "⛔ no frame in 5 s (%s): it is a RESULT if the "
		              "desktop has not changed, a fault if the stream never "
		              "started — and the two numbers are different on purpose",
		              p.guasto);
		g_clear_error(&sbaglio);
		/* ⛔⭐ AND HERE IT IS DISMANTLED, instead of staying with half a stage.
		 *
		 *     Before, it returned leaving `*fuori_c` full: the loop found a live
		 *     capture that did not deliver, and had no way of telling it apart
		 *     from a healthy one.  ⚠ "The stream never started" and "the scene
		 *     is still" are two different things (`cattura.h`), and this is the
		 *     first.  ⇒ It is dismantled, and the caller will retry. */
		cattura_fermo_libera(&fo);
		cattura_ferma(cat);
		mutter_chiudi(mut);
		chiudi_palco_kwin();
		*fuori_c = NULL;
		*fuori_m = NULL;
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}

	/* ⛔ The monitor's name AFTER the first frame, not after `cattura_avvia`:
	 *    the seam corrected on 12 Aug 2026 (`P2-6-montaggio.md` §5.1). */
	if (!mut && palco_kwin) {
		/* ⭐ On KDE the monitor is the session's, and `kwin.c` has already said
		 *    the scale if it is not 1.  "Before" and "after" are the same
		 *    number: the stage adds none. */
		p.monitor_prima = p.monitor_dopo = kwin_quante_uscite(palco_kwin);
		snprintf(p.monitor, sizeof p.monitor, "%s",
		         kwin_nome_uscita(palco_kwin) ? kwin_nome_uscita(palco_kwin)
		                                      : "(no name)");
	} else if (!mut) {
		/* ⭐ PHASE 13 — on wlroots there is neither a Mutter session nor a KWin
		 *    stage: the monitor is the compositor's output, and the capture has
		 *    already said so.  ⛔ Without this branch `mutter_monitor_cerca(NULL)`
		 *    was called, which is a failed assertion in the log — noise that
		 *    looks like a fault, `[M]` 21 Sep 2026. */
		uint32_t l = 0, a = 0;

		cattura_misura_negoziata(cat, &l, &a);
		p.monitor_prima = p.monitor_dopo = 1;
		snprintf(p.monitor, sizeof p.monitor, "%s",
		         cattura_uscita_nome(cat) ?: "(the compositor's output)");
	} else if (mutter_monitor_cerca(mut)) {
		guint prima = 0, dopo = 0;
		double scala;

		mutter_monitor_conteggi(mut, &prima, &dopo);
		p.monitor_prima = prima;
		p.monitor_dopo = dopo;
		snprintf(p.monitor, sizeof p.monitor, "%s", mutter_monitor_nostro(mut));

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
		scala = mutter_scala_nostra(mut);
		/* ⛔ AND THE GOOD CASE IS WRITTEN, not left to silence: "the guard looked
		 *    and the scale is 1.0" and "the guard was not run" would have the
		 *    same face — which is the error form this project pays for most
		 *    often.  ⚠ One line per stage mounting, not per frame. */
		if (scala == 1.0)
			registro_dice(REG_FIGLIO,
			              "⭐ guard 2 (§5.0-sexies): the scale of our monitor "
			              "«%s» is 1.000 — the input's coordinate space "
			              "coincides with the stream's pixels",
			              p.monitor);
		if (scala < 0)
			registro_dice(REG_FIGLIO,
			              "⚠ the scale of our logical monitor could not be "
			              "read: I GO ON, and I do not say 1.0 out of habit "
			              "(guard 2 of DECISIONI.md §5.0-sexies)");
		else if (scala != 1.0) {
			registro_dice(REG_FIGLIO,
			              "⛔⛔ SCALE %.3f on OUR monitor «%s» instead of 1.0: "
			              "the input's coordinate space does not coincide with "
			              "the stream's pixels, and the pointer would go elsewhere "
			              "without anything saying so.  ⇒ I am NOT taking the stage "
			              "(guard 2 of DECISIONI.md §5.0-sexies).  The cure is "
			              "a single line, on this user's session: "
			              "`gsettings set org.gnome.desktop.interface "
			              "scaling-factor 0` — then the session restarts by itself, "
			              "without restarting anything",
			              scala, p.monitor);
			p.stato_sessione = 0;
			snprintf(p.guasto, sizeof p.guasto,
			         "scale %.3f instead of 1.0 on monitor «%s»: the pointer "
			         "would go elsewhere (guard 2, DECISIONI.md §5.0-sexies)",
			         scala, p.monitor);
			cattura_fermo_libera(&fo);
			manda(MSG_PALCO, &p, sizeof p, NULL, 0);
			return false;
		}
	} else {
		snprintf(p.monitor, sizeof p.monitor, "(I could not tell)");
	}

	p.larghezza = fo.larghezza;
	p.altezza = fo.altezza;
	p.stride = fo.stride;
	p.bit = (uint32_t)fo.consegna.bit_per_canale;
	registro_dice(REG_FIGLIO,
	              "⭐ frame captured AS «%s»: %ux%u, stride %u READ, "
	              "%llu bytes, %s at %d bits, %s",
	              getenv("USER") ? getenv("USER") : "?", fo.larghezza,
	              fo.altezza, fo.stride, (unsigned long long)fo.byte,
	              fo.consegna.formato ? fo.consegna.formato : "(unknown)",
	              fo.consegna.bit_per_canale,
	              /* ⛔ THREE answers and not two: since 22 Aug 2026 the pass over
	               *    the pixels is done at a cadence (`cattura.c`,
	               *    `MISURA_PIXEL_OGNI_MS`), and on a frame not looked at
	               *    `nero == FALSE` means **"I did not look"**, not "it is
	               *    not black".  ⚠ Here it is always the FIRST frame — which
	               *    is always looked at — but the line is written right
	               *    anyway: it is the one that one day will be copied
	               *    elsewhere. */
	              !fo.consegna.pixel_misurati ? "⚠ the pixels were not looked at "
	                                            "(cadence): it is NOT «not black»"
	              : fo.consegna.nero          ? "⛔ BLACK"
	                                          : "not black");

	rilievo_scrivi(dir_rilievo, "cattura.bgrx", fo.pixel, (size_t)fo.byte);

	/* ⛔⭐ AND THIS FIRST ENCODING STAYS, even if there is the loop now: it does
	 *     not serve to send, it serves to PROVE the stage works before anyone
	 *     asks for it.  `p.flussi` is the number `MSG_PALCO` carries to the
	 *     parent, and it is the only line that distinguishes "nobody is
	 *     watching" from "the encoder does not open".  ⚠ And the two encoders
	 *     stay OPEN: they are the ones the loop will use.
	 * ⛔ §5.2: both first frames must be a KEYFRAME, and it is asked instead of
	 *    hoped for. */
	debito_chiave[1] = debito_chiave[2] = debito_chiave[3] = true;
	if (primo) {
		/* ⚠ `input = 0` and it is NOT a placeholder value: §6.2 says "0 if
		 *   none", and here there is nobody yet — the input channel is born
		 *   when the client opens its stream, and these two frames are the
		 *   diagnosis of switch-on, not of movement. */
		/* ⛔⛔ AND THE SIZE IS THE FRAME'S, not the requested one — defect found
		 *     while refuting, on the night of 15 Aug 2026.
		 *
		 *     Here the encoder was born at `tela_l x tela_a` (the REQUESTED)
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
		if (fo.stride >= (guint64) fo.larghezza * 4u
		    && fo.byte >= (guint64) fo.stride * fo.altezza) {
			if (codifica_e_manda(&fo, CODIFICATORE_HEVC, 1, dir_rilievo,
			                     "flusso-hevc.265", istante_us, fo.larghezza,
			                     fo.altezza, 0))
				p.flussi++;
			/* ⛔ AV1 is gone: it was encoded only in software (SVT-AV1), and
			 *    the software fallback left with phase 19. */
			/* ⭐ The second, since 20 August: a client negotiating H.264 finds
			 *    the first frame already in the deposit like the other, instead
			 *    of waiting for something to move on the desktop. */
			if (codifica_e_manda(&fo, CODIFICATORE_H264, 3, dir_rilievo,
			                     "flusso-h264.264", istante_us, fo.larghezza,
			                     fo.altezza, 0))
				p.flussi++;
			/* ⚠ And the stage's size is NOT written here: `tela_l`/`tela_a` are
			 *   this function's PARAMETERS, not the loop's variables — writing
			 *   into them would seem to update the stage and would update
			 *   nothing.  The reconciliation at the loop's first round takes
			 *   care of it, which is the only place where that number changes. */
		} else {
			registro_dice(REG_FIGLIO,
			              "⛔ the switch-on diagnosis does NOT encode: the "
			              "frame declares %ux%u with stride %u and carries %llu "
			              "bytes — whoever compressed it would read beyond the copy",
			              fo.larghezza, fo.altezza, fo.stride,
			              (unsigned long long)fo.byte);
		}
		/* ⛔ And the loop's counters start again from zero: these two are not
		 *    frames of the movement, they are the switch-on diagnosis.  Adding
		 *    them would say "two frames delivered" to a user who has not seen
		 *    a single one. */
		ciclo_fotogrammi = ciclo_chiavi = 0;
	} else {
		/* ⚠ On a remount the diagnosis is not redone: it would cost ~80 ms of
		 *   encoding in the middle of a live session, and the two frames would
		 *   go to a client already watching.  ⛔ `p.flussi` stays 0 and the log
		 *   says so: it is a remount, not a birth. */
		p.flussi = 0;
	}

	cattura_fermo_libera(&fo);
	manda(MSG_PALCO, &p, sizeof p, NULL, 0);

	/* ⭐⭐ AND THE STAGE'S TWO SEAMS LIVE HERE, not in the caller: whoever
	 *     remounts the stage must remount **all** of them, and leaving one out
	 *     would mean a desktop that is seen and cannot be driven — without any
	 *     error anywhere.
	 *
	 * ⛔ `cursore_apri()` wants the recipient **at opening**, and the opening
	 *    happens inside `cattura_avvia()`: so the registration goes through
	 *    `cattura.h`.  ⚠ Without this line the pipe would be written in full
	 *    and **empty**.
	 * ⛔ And `input_apri()` goes on the `RemoteDesktop` session that `mutter.c`
	 *    has just started: on a remount that is **another session**, and an
	 *    `Input` hooked to the old one will no longer inject anything. */
	cattura_cursore(cat, cursore_al_padre, NULL);
	if (palco_input) {
		input_chiudi(palco_input);
		palco_input = NULL;
	}
	{
		char *sbaglio_input = NULL;
		/* ⭐ PHASE 12, INCREMENT 3 — on KDE the channel is given by KWin, at
		 *    the output's size (`tela_l`/`tela_a` have already been aligned by
		 *    `misura_del_palco()`). */
		/* ⭐ PHASE 13, INCREMENT 3 — on XFCE (wlroots) `libei` does not exist:
		 *    Wayland virtual keyboard and pointer, with the same contract
		 *    (`input.h`).  ⛔ The branch comes FIRST and does not touch the
		 *    GNOME and KDE line below. */
		if (sessione_su_wlroots())
			palco_input = input_apri_wlr(tela_l, tela_a, &sbaglio_input);
		else
		palco_input = palco_kwin
		                  ? input_apri_kwin(palco_kwin, tela_l, tela_a, &sbaglio_input)
		                  : input_apri(mut, tela_l, tela_a, &sbaglio_input);
		if (palco_input && disposizione_in_attesa[0]) {
			/* ⛔ Before saying the channel is open: the layout requested at
			 *    attach had arrived with the stage closed, and if it is not
			 *    applied HERE the user types the first keys on the wrong
			 *    layout — and `Ctrl+Z` does "redo". */
			registro_dice(REG_FIGLIO,
			              "⭐ §5-bis.7: applying now the layout «%s», "
			              "which had been requested when the stage was not there "
			              "yet",
			              disposizione_in_attesa);
			input_disposizione(palco_input, disposizione_in_attesa);
			disposizione_in_attesa[0] = '\0';
		}
		if (palco_input) {
			registro_dice(REG_FIGLIO,
			              "⭐⭐ THE INPUT CHANNEL IS OPEN on the canvas %ux%u: "
			              "from now on what the user does in the browser reaches "
			              "the desktop (§7.3)",
			              tela_l, tela_a);
			/* ⭐ PHASE 15, D-007 — on wlroots the output's size is given at
			 *    the capture's BIRTH (`cattura_avvia_wlr()`): on reattach with
			 *    a smaller window the session's windows stayed where they
			 *    were.  ⇒ They are brought back inside now that the channel
			 *    exists.  (Harmless at the first birth, and it does nothing on
			 *    GNOME and KDE.) */
			input_riporta_dentro(palco_input);
		} else
			/* ⛔ And if it does not open we do NOT die: `CODER.md` §4.2 —
			 *    degrade, do not fail.  A user who sees the desktop and cannot
			 *    drive it has less than they are owed; a user whose session
			 *    falls **has nothing**.  ⚠ But the fallback is DECLARED. */
			registro_dice(REG_FIGLIO,
			              "⛔ the input channel does NOT open (%s): the desktop "
			              "is SEEN but cannot be DRIVEN.  ⚠ The session stays "
			              "up — §8.3 forbids disconnecting — and this line is "
			              "the declared fallback",
			              sbaglio_input ? sbaglio_input : "no details");
		free(sbaglio_input);
	}

	/*
	 * ⭐⭐ AND THE STAGE'S THIRD SEAM: THE CLIPBOARD — phase 7.
	 *
	 * ⛔ It must be remounted **together with the other two**, and for the same
	 *    reason: on a remount the `RemoteDesktop` session is **another one**,
	 *    and an `Appunti` hooked to the old one would no longer receive any
	 *    signal — without any error anywhere.  ⚠ The symptom would be "the
	 *    clipboard stopped working at some point", which does not name the
	 *    remount.
	 *
	 * ⛔ And it is CLOSED before reopening, the old one is not left standing:
	 *    `appunti_chiudi()` never calls `DisableClipboard` (trap 1 of
	 *    `appunti.h`), so closing here does not burn the graphical session's
	 *    clipboard — it only closes our thread and the subscriptions.
	 */
	if (palco_appunti) {
		appunti_chiudi(palco_appunti);
		palco_appunti = NULL;
	}
	{
		GError *sbaglio_app = NULL;

		/* ⭐ PHASE 13 — on XFCE the clipboard goes through labwc, with the same
		 *    wlroots protocol KDE already uses (`appunti_kde.c`).  ⛔ The new
		 *    branch comes FIRST, and the two below are the ones from before.
		 * ⭐ PHASE 12 — on KDE the clipboard goes through KWin (`appunti_kde.c`). */
		if (sessione_su_wlroots())
			palco_appunti = appunti_apri_wlroots(&sbaglio_app);
		else
			palco_appunti = palco_kwin
			                    ? appunti_apri_kde(&sbaglio_app)
			                    : appunti_apri(mutter_bus(mut),
			                                   mutter_percorso_controllo(mut),
			                                   &sbaglio_app);
		if (palco_appunti) {
			appunti_ascolta(palco_appunti, appunti_dalla_sessione,
			                appunti_vuole_incollare, NULL);
			registro_dice(REG_FIGLIO,
			              "⭐⭐ THE CLIPBOARD IS OPEN, in both directions and text "
			              "only: from now on what is copied in the desktop can "
			              "be pasted on the device, and vice versa (§7.4)");
			/* ⭐ AND FIRST OF ALL: the clipboard already in the desktop is
			 *    ASKED FOR, or connecting loses it (see the box in
			 *    `appunti.c`).  ⛔ And it is asked BEFORE the pending offer:
			 *    offering first, our text would be read instead of its own. */
			appunti_leggi_adesso(palco_appunti);

			/* ⭐ And the offer that arrived while we were not there is redone NOW. */
			if (appunti_offerta_arretrata) {
				GError *sb = NULL;

				appunti_offerta_arretrata = false;
				if (appunti_offri(palco_appunti, &sb))
					registro_dice(REG_APPUNTI,
					              "⭐ CLIPBOARD: the client had announced BEFORE "
					              "the clipboard opened, and the offer has been "
					              "REDONE now: inside the desktop the "
					              "«Paste» item has something to give again");
				else
					registro_dice(REG_APPUNTI,
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
			registro_dice(REG_FIGLIO,
			              "⛔ the clipboard does NOT open (%s): the desktop is seen "
			              "and driven, but copy-paste between the two worlds is "
			              "not there.  ⚠ The session stays up, and this line is "
			              "the declared fallback",
			              sbaglio_app ? sbaglio_app->message : "no details");
		}
		g_clear_error(&sbaglio_app);
	}

	/*
	 * ⭐⭐ AND HERE, ONLY ONCE PER SESSION, THE THREE THINGS TO DO WHEN THE
	 *     STAGE IS THERE — and not before, because before there was no
	 *     session to tell them to.
	 *
	 * ⛔ "Written" is not "in force" (`REVIEWER.md` E1): the two checks do not
	 *    serve to protect — the polkit rule and the seatless session protect —
	 *    they serve to **know whether those protections are really there**.
	 *    And the child does them because it is the user: `[M]` root gets the
	 *    answer "yes" from logind, which looks at `CAP_SYS_BOOT` before polkit.
	 */
	{
		static bool gia_fatto;

		if (!gia_fatto) {
			sentinella *guardia;
			char dettaglio[192];

			gia_fatto = true;

			/* 1. ⛔ Suspension, and it is not theoretical: `[M]` the
			 *    "Automatic Suspend" notification appeared in the remote
			 *    desktop. */
			sessione_inibisci();

			guardia = sentinella_apri();
			if (!guardia) {
				registro_dice(REG_FIGLIO,
				              "⚠ without the system bus I cannot VERIFY "
				              "either headless or the ban on powering off: "
				              "the protections may be there, ⛔ but from here "
				              "I don't know — and «I don't know» is not «fine»");
			} else {
				/* 2. Headless, which since 15 August is by construction. */
				dettaglio[0] = '\0';
				if (sentinella_senza_seat(guardia, dettaglio, sizeof dettaglio))
					registro_dice(REG_FIGLIO,
					              "⭐ VERIFIED: my session has no "
					              "seat (%s) ⇒ Mutter is headless, and "
					              "GNOME's screen lock does not revoke "
					              "capture and input from us (§4.3-bis)",
					              dettaglio);
				else
					registro_dice(REG_FIGLIO,
					              "⛔⛔ MY SESSION IS NOT HEADLESS "
					              "(%s): this session works as long as "
					              "nobody locks the screen, and then Mutter "
					              "CLOSES capture and input on us, refusing to "
					              "recreate them.  ⚠ I do not exit — I1: a "
					              "session with a risk is worth more than "
					              "no session — but this line is the "
					              "declared failure of §4.3-bis",
					              dettaglio[0] ? dettaglio : "no details");

				/* 3. The three belts of §4.7. */
				dettaglio[0] = '\0';
				if (sentinella_spegnimento_vietato(guardia, dettaglio,
				                                   sizeof dettaglio))
					registro_dice(REG_FIGLIO,
					              "⭐ VERIFIED: from this session the machine "
					              "can NOT be powered off or suspended (%s) "
					              "— §4.7, and the three belts are in force",
					              dettaglio);
				else
					registro_dice(REG_FIGLIO,
					              "⛔⛔ FROM THIS SESSION THE MACHINE CAN BE "
					              "POWERED OFF OR SUSPENDED (%s): §4.7 says "
					              "nobody must be able to do it, and the "
					              "machine belongs to several people.  ⇒ The "
					              "polkit rule is missing, or it does not cover all "
					              "twelve actions",
					              dettaglio[0] ? dettaglio : "no details");
				sentinella_chiudi(guardia);
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
static void smonta_il_palco(MutterSessione **m, Cattura **c)
{
	if (palco_input) {
		int quanti = input_rilascia_tutto(palco_input);
		if (quanti > 0)
			registro_dice(REG_FIGLIO,
			              "⭐ §7.3: the stage is dismantled and %d keys and "
			              "buttons were still held down: released",
			              quanti);
		input_chiudi(palco_input);
		palco_input = NULL;
	}
	/* ⛔⭐ AND THE CLIPBOARD IS CLOSED BEFORE THE SESSION, not after: the two
	 *     subscriptions and the thread live on `mutter_bus()`, which belongs
	 *     to the `MutterSessione` closed three lines below.  ⚠ Closing the
	 *     other way round would leave a thread talking on a bus already gone.
	 * ⛔ And `DisableClipboard` is NOT called (trap 1 of `appunti.h`): whoever
	 *    called it at dismantling would find, at the remount, a dead clipboard
	 *    **for the rest of the graphical session**. */
	if (palco_appunti) {
		appunti_chiudi(palco_appunti);
		palco_appunti = NULL;
		appunti_montaggio_libera();
	}
	if (*c) {
		cattura_ferma(*c);
		*c = NULL;
	}
	if (*m) {
		mutter_chiudi(*m);
		*m = NULL;
	}
	chiudi_palco_kwin();
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ AND THE PIXELS' ROUTE IS CHANGED **WITHOUT DISMANTLING THE STAGE** — 25
 *       Aug 2026, and it is the cure of `fasi/10-…md` §8.2 **P1**.
 *
 * ⛔⛔ THE FACT, `[M]` 25 Aug 2026 (core read with gdb, not inferred):
 *
 *   with a view **1268** wide — the one Firefox opens by itself — the DMA-BUF
 *   stride comes out **5072**, which is not a multiple of 64; the zero-copy
 *   guard refuses it (`codifica_e_manda`), `scheda_da_abbandonare` was set,
 *   and the loop **dismantled the whole stage** to remount it on memory.
 *   ⇒ `smonta_il_palco()` → `input_chiudi()` → **`ei_disconnect()`**, and there
 *   the child died of **SIGSEGV**:
 *
 *       #0  ei_disconnect ()   from /lib/x86_64-linux-gnu/libei.so.1
 *       #2  input_chiudi (in=…) at input.c:1613
 *       #3  smonta_il_palco () at figlio.c
 *
 *   `[M]` And the piece that explains the **when**: in the core `in->puntatore`
 *   and `in->tastiera_dev` were **NULL** and `regione_nota` **false** — the
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
 * ⛔ What is remounted is what MUST be remounted: the `Cattura` and its cursor
 *    seam (`cursore_apri()` wants the recipient at opening, and the opening is
 *    inside `cattura_avvia()` — see the box of the three seams in
 *    `prendi_il_palco()`).
 *
 * ⚠ And if the PipeWire node cannot be taken back (the producer withdrew it),
 *   `false` is returned **without inventing anything**: the caller dismantles
 *   the stage for real, which is the old road — demoted from normal to
 *   fallback.
 * ═══════════════════════════════════════════════════════════════════════════ */
static bool rimonta_solo_la_cattura(MutterSessione *m, Cattura **c, uint32_t l,
                                    uint32_t a)
{
	GError *sbaglio = NULL;
	Cattura *nuova;

	/*
	 * ⭐ PHASE 13 — XFCE (wlroots): here the source IS the capture.  There is
	 *    no PipeWire node nor a Mutter/KWin session to take back: remounting
	 *    means stopping the `Cattura` and reopening it with
	 *    `cattura_avvia_wlr()` on the new route.  ⛔ Input (`input_apri_wlr`)
	 *    and clipboard stay alive: they belong to the stage, not to the stream.
	 * ⛔ The branch comes FIRST and always returns: below, the GNOME and KDE
	 *    path stays the one from before, word for word.  Without this branch
	 *    `m` and `palco_kwin` are NULL on XFCE, the guard below returned
	 *    `false` and the caller dismantled the WHOLE stage (input and clipboard
	 *    included).
	 */
	if (sessione_su_wlroots()) {
		if (!c)
			return false;
		if (*c) {
			cattura_ferma(*c);
			*c = NULL;
		}
		misura_del_palco(&l, &a);
		lastre_per_la_strada();
		nuova = cattura_avvia_wlr(l, a, MOVIMENTO_FPS, strada_del_palco,
		                          CATTURA_COLORE_BGRX, &sbaglio);
		if (!nuova) {
			registro_dice(REG_FIGLIO,
			              "⛔ wlroots: the capture did NOT reopen on the route "
			              "«%s» (%s): dismantling the whole stage, which is the "
			              "fallback",
			              strada_del_palco == CATTURA_STRADA_SCHEDA ? "CARD"
			                                                        : "MEMORY",
			              sbaglio ? sbaglio->message : "no details");
			g_clear_error(&sbaglio);
			return false;
		}
		g_clear_error(&sbaglio);
		*c = nuova;
		/* ⚠ The same seam as `prendi_il_palco()`: on wlroots the registration
		 *   is accepted and never calls back (the pointer is in the pixels),
		 *   but it is done anyway — a remounted stage must be the same as a
		 *   mounted one. */
		cattura_cursore(*c, cursore_al_padre, NULL);
		registro_dice(REG_FIGLIO,
		              "⭐⭐ wlroots: the PIXELS' ROUTE changed to «%s» "
		              "remounting ONLY the capture (canvas %ux%u): input and clipboard "
		              "were NOT touched",
		              strada_del_palco == CATTURA_STRADA_SCHEDA
		                  ? "CARD (DMA-BUF, zero copy)"
		                  : "MEMORY (the pixels are copied)",
		              l, a);
		return true;
	}

	if ((!m && !palco_kwin) || !c)
		return false;

	/* ⛔ First the old one is stopped: two streams on the same node would mean
	 *    two consumers, and the producer would deliver to both — that is
	 *    double the GPU work for nothing. */
	if (*c) {
		cattura_ferma(*c);
		*c = NULL;
	}

	misura_del_palco(&l, &a);
	nuova = cattura_avvia(nodo_del_palco(m), l, a, MOVIMENTO_FPS, strada_del_palco,
	                      CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (nuova && palco_kwin)
		cattura_cursore_mai_nascondere(nuova, "KWin --virtual: the session's cursor "
		                                      "theme is invisible");
	if (!nuova) {
		registro_dice(REG_FIGLIO,
		              "⛔ the capture did NOT reopen on node %u on the route "
		              "«%s» (%s): dismantling the whole stage, which is the fallback "
		              "— ⚠ and it costs the graphical session, not only the stream",
		              nodo_del_palco(m),
		              strada_del_palco == CATTURA_STRADA_SCHEDA ? "CARD"
		                                                        : "MEMORY",
		              sbaglio ? sbaglio->message : "no details");
		g_clear_error(&sbaglio);
		return false;
	}
	g_clear_error(&sbaglio);
	*c = nuova;
	/* ⛔ The cursor seam is redone AT ONCE: the pipe towards the parent is
	 *    registered on the `Cattura`, and the previous one is gone.  ⚠ Without
	 *    this line the pointer would stop changing shape **without any
	 *    error**, and the symptom would appear hours later. */
	cattura_cursore(*c, cursore_al_padre, NULL);
	registro_dice(REG_FIGLIO,
	              "⭐⭐ the PIXELS' ROUTE changed to «%s» remounting ONLY "
	              "the stream (node %u, canvas %ux%u): the graphical session, the "
	              "input channel and the clipboard were NOT touched.  ⛔ And "
	              "this is the cure of P1: dismantling the stage to change "
	              "route closed a freshly born EIS channel, and `ei_disconnect()` "
	              "killed the child with a SIGSEGV before the first frame",
	              strada_del_palco == CATTURA_STRADA_SCHEDA
	                  ? "CARD (DMA-BUF, zero copy)"
	                  : "MEMORY (the pixels are copied)",
	              nodo_del_palco(m), l, a);
	return true;
}

/* ⛔ The child's entry point.  `main.c` gets here BEFORE anything else, and
 *    it never returns. */
void figlio_vive(int argc, char **argv)
{
	struct corpo_sono s;
	struct stat st;
	uint32_t tela_l, tela_a;
	const char *utente, *dir_rilievo;
	uid_t atteso;
	gid_t atteso_g;
	MutterSessione *mut = NULL;
	Cattura *cat = NULL;
	int uno = 1;
	uid_t r, e, sv;
	gid_t rg, eg, sg;
	/* ⭐ PHASE 9 — what the parent wrote on the command line, and that this
	 *    process must repeat to itself: see below. */
	bool f9_risale = false;
	uint32_t f9_tetto = 0;
	/* ⛔ `true`, and not `false` like the two above: this cure is born ON
	 *    (24 Aug 2026), so the absence of the word at the end means "on".
	 *    ⚠ And the child can NOT just ask `audio.c` for the default: it must
	 *    be able to declare what REACHED it, or "the option was lost in the
	 *    hand-over" and "the cure does not work" have the same face (form D5). */
	bool f9_audio_silenzio = true;

	/* `--figlio-interno <user> <uid> <gid> <w> <h> <serial> <survey>` */
	if (argc < 9)
		_exit(40);
	utente = argv[2];
	/* ⛔⭐ AND FROM HERE ON EVERY LINE OF THIS PROCESS SAYS WHOSE IT IS — 25
	 *     Aug 2026, R10-A4 / P6.  The box is in `registro.h`.
	 *
	 *     ⭐ This process serves **a single** session: the identity belongs to
	 *        the process, not to the line, and it is set in one place only.
	 *        ⇒ It cures in one go the families `[M]` §6.7 measured at
	 *        **0.0 %** — `ciclo-cattura` and `audio-blocchi` (359 lines in
	 *        90 s with four sessions) — and with them the **70** of
	 *        `codificatore.c`, which knows nothing about sessions and writes
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
	registro_identita(utente);
	atteso = (uid_t)strtoul(argv[3], NULL, 10);
	atteso_g = (gid_t)strtoul(argv[4], NULL, 10);
	tela_l = (uint32_t)strtoul(argv[5], NULL, 10);
	tela_a = (uint32_t)strtoul(argv[6], NULL, 10);
	/* ⛔ The WANTED canvas is born equal to the starting one and diverges at
	 *    the first `ADATTA_TELA`: it is the one requested on REMOUNTING the
	 *    stage.  ⚠ Without it, a stage falling after a resize was born again
	 *    at the command line's size, and the bands came back without any line
	 *    connecting the two things. */
	tela_voluta_l = tela_l;
	tela_voluta_a = tela_a;
	mia_matricola = strtoull(argv[7], NULL, 10);
	dir_rilievo = argv[8];
	/* ⭐ The snapshot keeps it: see the box above `scatto_dir`. */
	scatto_dir = dir_rilievo;
	/* ⭐ The chatter, if the parent passed it to us: see the box in
	 *    `figli_esegui()`.  ⛔ Without it, every `registro_dettaglio` of this
	 *    file is written and reaches nobody. */
	/* ⛔⭐⭐ AND THE **THREE** CURES OF PHASE 9 ARE TURNED ON HERE, INSIDE THE CHILD.
	 *
	 *      The box explaining why they cannot come from anywhere else is in
	 *      `figlio.h`, above `figli_fase9()`: they are statics of the process,
	 *      and the process that opens the encoders is this one.
	 *
	 * ⚠ BEFORE `prendi_il_palco()`, which already opens the first encoder: two
	 *   lines further down and the first session would be born without the
	 *   cure, with the startup line saying "off" — that is the defect disguised
	 *   as a measure that this whole phase tries to avoid.
	 * ⚠ They are scanned by NAME and not by position, like the chatter: the
	 *   first nine are fixed, these are optional and may both be missing.
	 */
	for (int i = 9; i < argc; i++) {
		if (strcmp(argv[i], "--parlantina") == 0)
			registro_parlantina(true);
		else if (strcmp(argv[i], "--journal") == 0)
			registro_journal(true); /* ⚠ if it does not open, stderr remains */
		else if (strcmp(argv[i], "--qualita-risale") == 0)
			f9_risale = true;
		else if (strcmp(argv[i], "--tetto-banda-mbit") == 0 && i + 1 < argc)
			f9_tetto = (uint32_t)strtoul(argv[++i], NULL, 10);
		/* ⭐ PHASE 19: the forced card route (the server's `--codifica`), for
		 *    the same reason as the three lines above — it is a static of THIS
		 *    process, and the parent repeats it to it.  ⚠ A value that is not
		 *    recognised stays "scheda", and the encoder's line says so. */
		else if (strcmp(argv[i], "--codifica") == 0 && i + 1 < argc)
			figlio_codifica_strada(argv[++i]);
		/* ⛔⭐ AND THIS ONE IS READ NEGATED, because it is born ON (24 Aug 2026):
		 *     the word at the end is the EXCEPTION to the default.  ⚠ An absence
		 *     here means "on", which is the opposite of the two lines above —
		 *     and it is the reason `f9_audio_silenzio` starts from `true`. */
		else if (strcmp(argv[i], "--niente-audio-silenzio") == 0)
			f9_audio_silenzio = false;
	}
	codificatore_qualita_risale(f9_risale);
	codificatore_tetto_banda(f9_tetto);
	/* ⛔ And the audio encoder lives in THIS process, like the video one: the
	 *    line of the value IN FORCE is written by `audio.c` when each encoder
	 *    opens, and it is the third of the triple (parent WILL PASS · child
	 *    RECEIVED · in force). */
	audio_silenzio_taci(f9_audio_silenzio);

	signal(SIGTERM, SIG_DFL);
	signal(SIGINT, SIG_DFL);
	signal(SIGPIPE, SIG_IGN);
	/* ⭐ The on-demand snapshot: the box is above `scatto_segnale()`. */
	signal(SIGUSR1, scatto_segnale);
	signal(SIGUSR2, scatto_segnale);

	/* ⛔ If the server dies, this process dies with it: no orphan attached to a
	 *    user's virtual monitor.  ⚠ And it is armed AFTER the privilege drop,
	 *    because a credentials change can reset it — ⭐ and for this reason it
	 *    is NOT the only road: the EOF on the socket (the loop below) closes
	 *    anyway, and two independent nets are two on purpose. */
	prctl(PR_SET_PDEATHSIG, SIGTERM);

	/* ⛔⭐ AND IT IS RECHECKED THAT WE ARE WHO WE MUST BE, AFTER THE `exec`.
	 *     `diventa_ed_esegui()` has already verified it, but that was another
	 *     program: what counts here is what the KERNEL now says about this
	 *     process.  A new image trusting its own `argv` would be a child
	 *     declaring itself. */
	if (getresuid(&r, &e, &sv) != 0 || getresgid(&rg, &eg, &sg) != 0)
		_exit(41);
	if (r != atteso || e != atteso || sv != atteso || rg != atteso_g
	    || eg != atteso_g || sg != atteso_g) {
		registro_dice(REG_FIGLIO,
		              "⛔⛔ I AM NOT WHO I SHOULD BE: they wanted me as uid %ld gid "
		              "%ld and the kernel says uid %ld/%ld/%ld gid %ld/%ld/%ld.  "
		              "EXITING without touching anything: a child running as "
		              "the wrong user is I3 violated invisibly",
		              (long)atteso, (long)atteso_g, (long)r, (long)e, (long)sv,
		              (long)rg, (long)eg, (long)sg);
		_exit(42);
	}
	mio_uid = e;

	/* ⛔ The child too wants the kernel's stamp on the parent's messages: the
	 *    link is verified **at both ends**.  ⚠ `SO_PEERCRED` here would tell
	 *    the truth (root created the socketpair), but it must be the same
	 *    proof the parent makes — and the parent's is per message. */
	setsockopt(fd_figlio, SOL_SOCKET, SO_PASSCRED, &uno, sizeof uno);

	memset(&s, 0, sizeof s);
	s.uid = r;
	s.euid = e;
	s.suid = sv;
	s.gid = rg;
	s.egid = eg;
	s.sgid = sg;
	s.pid = (uint32_t)getpid();
	s.ppid = (uint32_t)getppid();
	s.descrittori = quanti_descrittori();
	snprintf(s.utente, sizeof s.utente, "%s", utente);
	snprintf(s.runtime, sizeof s.runtime, "%s",
	         getenv("XDG_RUNTIME_DIR") ? getenv("XDG_RUNTIME_DIR") : "(none)");
	/* ⛔ "It exists" and "it is its own" are two different facts: someone
	 *    else's runtime folder would be a permission denied much later. */
	if (s.runtime[0] != '(' && stat(s.runtime, &st) == 0 && st.st_uid == e)
		s.runtime_c_e = 1;
	{
		char percorso[224];
		snprintf(percorso, sizeof percorso, "%s/bus", s.runtime);
		if (s.runtime_c_e && stat(percorso, &st) == 0)
			s.socket_bus_c_e = 1;
	}

	registro_dice(REG_FIGLIO,
	              "⭐ I am the child of «%s»: pid %u, uid %u (asked of the kernel, "
	              "not inferred), %u open descriptors — the server's port is NOT "
	              "among them",
	              utente, s.pid, s.euid, s.descrittori);

	/* ⭐ PHASE 15, D-015 — the SESSION's dconf, here and not later: before any
	 *    `GSettings` (`sessione_impostazioni()`, `input_disposizione()`) and
	 *    before the threads — `g_setenv` must not be done with other threads
	 *    alive.  GNOME only; the box is in `sessione.c`. */
	sessione_dconf_prepara();
	/* ⭐ R1/R2 — and what a badly ended session left in the user manager goes
	 *    away now (only with the session dead: see the box). */
	sessione_sgombera_gestore("child startup: leftovers from before");

	/* ⛔⭐⭐ THE PHASE 9 PARAMETERS ARE WRITTEN AT BIRTH — 23 Aug 2026.
	 *
	 *      The rule is already written, and it is in `src/riavvia-7700.sh`:
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
	 *   written by `codificatore.c` when it opens — "written" is not "in force"
	 *   (`REVIEWER.md` E1), and these lines are the "asked" half of the
	 *   comparison, not the verdict.
	 *
	 * ⚠ The canvas is the one at BIRTH: §4.5 can change it with the session
	 *   open, and the new value is written by the «encoder OPENED» line.
	 * ⚠ The depth is NOT there on purpose: at birth it is not negotiated, and
	 *   writing one here would be putting back by hand the lie of 17 August. */
	registro_dice(REG_FIGLIO,
	              "⭐⛔ PARAMETERS IN FORCE (phase 9), what the child ASKS FOR: "
	              "rate %d/s · canvas at birth %ux%u · INFINITE GOP "
	              "(chiavi_ogni = 0: keyframes only on request, §5.2 — it is a "
	              "choice, not an oversight)",
	              MOVIMENTO_FPS, tela_l, tela_a);
	registro_dice(REG_FIGLIO,
	              "⭐⛔ PARAMETERS IN FORCE (phase 9), quality and encoder "
	              "REQUESTED: QP %d on the card (no software fallback, phase "
	              "19) · node %s · entrypoint %s",
	              QP_HARDWARE, NODO_RENDERING,
	              potenza_nome(POTENZA_RENDERING));

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
	 *      1. `figli_fase9()` in the parent — "what I WILL PASS";
	 *      2. this one — "what REACHED me";
	 *      3. `codificatore.c` at opening — "what is IN FORCE".
	 *    If the three do not agree, the point where it gets lost is between the
	 *    two that diverge, and there is nothing to guess. */
	registro_dice(REG_FIGLIO,
	              "⭐⛔ PARAMETERS IN FORCE (phase 9), what the child "
	              "RECEIVED on its command line: quality climb-back "
	              "%s · bandwidth ceiling %s (floor %u Mbit/s) · ⭐ audio "
	              "silence %s — ⚠ asked of the "
	              "encoder now, before the first stage.  Whether it took them "
	              "is told by the «encoder OPENED» line (video) and the "
	              "«digital silence cure» line (audio)",
	              f9_risale ? "ON" : "off (I6)",
	              f9_tetto ? "ON" : "off (I6)", f9_tetto,
	              f9_audio_silenzio
	                  ? "ON (default since 24 Aug 2026)"
	                  : "turned OFF by hand (--niente-audio-silenzio)");

	if (!manda(MSG_SONO, &s, sizeof s, NULL, 0)) {
		registro_dice(REG_FIGLIO, "⛔ I cannot introduce myself to the parent (%s)",
		              strerror(errno));
		_exit(43);
	}

	/* ⛔⭐ AND THE STAGE IS TAKEN AT ONCE, without waiting for someone to ask.
	 *
	 *     The reason is a number: §4.4-bis imposes on the server a fixed second
	 *     before answering `CREDENZIALI`, and the RCP session cannot reach
	 *     `SESSIONE` before that.  ⇒ Between "PAM said yes" and "a frame is
	 *     needed" there is **at least one second guaranteed by the protocol**,
	 *     and it is all the time this child has to be born, connect to the
	 *     bus, capture and encode.  Waiting for a request would throw it away. */
	if (!prendi_il_palco(tela_l, tela_a, dir_rilievo, true, &mut, &cat)) {
		/* ⛔⭐ AND IF AT BIRTH THE STAGE IS NOT THERE, WE DO NOT STAY LIKE THIS —
		 *     it is the second twin defect, `[M]` from the user's real
		 *     session: a child born without a graphical session **never**
		 *     tried another, and at the next login invariant I2 handed them
		 *     that very child.  The user saw "no desktop" twice in a row for
		 *     this reason. */
		registro_dice(REG_FIGLIO,
		              "⛔ NO STAGE at birth: the graphical session of "
		              "«%s» is not there (yet).  ⚠ I do NOT exit — §8.3 forbids "
		              "disconnecting — and I do NOT stand still: retrying, the first time "
		              "in %d ms",
		              utente, PALCO_RIPROVA_MIN_MS);
		palco_riprova_ms = registro_ora_ms() + PALCO_RIPROVA_MIN_MS;
		palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
	}

	/* ═══════════════════════════════════════════════════════════════════ */
	/* ⭐⭐ THE LOOP OF PHASE 3 — capture, encode, send; and listen.        */
	/*                                                                     */
	/* ⛔ TWO THINGS TO DO AND ONLY ONE PROCESS, and the order matters.  The */
	/*    loop looks FIRST at whether the parent said something (which     */
	/*    does not wait: `poll` with zero) and THEN captures (which         */
	/*    waits).  The other way round, a `MSG_SPEGNITI` or a requested     */
	/*    keyframe would sit still for the whole capture wait — that is up  */
	/*    to a quarter of a second, which on the latency of                 */
	/*    `SPECIFICHE.md` §3.2 is five times the ceiling.                   */
	/*                                                                     */
	/* ⛔ AND WHEN NOBODY IS WATCHING NOTHING IS CAPTURED: `codec_chiesto`  */
	/*    at zero means the last session has gone.  ⚠ It is NOT invariant   */
	/*    I1 the other way round — I1 forbids lowering the rate out of      */
	/*    caution **while someone is watching**; here nobody is watching,   */
	/*    and the stage (I4) stays up: only the loop stops.  Then we wait   */
	/*    on the socket, and the process costs zero.                        */
	for (;;) {
		uint8_t busta[BUSTA_MAX];
		struct testa t;
		struct ucred chi;
		bool c_e = false;
		ssize_t letti;
		struct pollfd pf;
		int pronto;
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
		if (!cat) {
			static uint64_t battito_ms;
			uint64_t adesso = registro_ora_ms();

			if (adesso - battito_ms >= 1000) {
				battito_ms = adesso;
				registro_dice(REG_FIGLIO,
				              "♥ loop ALIVE without a stage: codec %u, wanted canvas "
				              "%ux%u, next attempt in %lld ms",
				              (unsigned)codec_chiesto, tela_voluta_l, tela_voluta_a,
				              (long long)((int64_t)palco_riprova_ms - (int64_t)adesso));
			}
		}

		/* ── 1. what the parent has to say, without waiting ────────────── */
		for (;;) {
			struct pollfd due[2];
			int quanti = 1;
			int fd_ei;

			pf.fd = fd_figlio;
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
			fd_ei = palco_input ? input_descrittore(palco_input) : -1;
			if (fd_ei >= 0) {
				due[1].fd = fd_ei;
				due[1].events = POLLIN;
				due[1].revents = 0;
				quanti = 2;
			}
			/* ⛔ Zero when capturing, the ceiling when not capturing: so the
			 *    idle process does not spin and the working one does not
			 *    lose time.
			 * ⛔⭐ And "capturing" requires TWO things: that someone is
			 *     watching **and** that the stage is there.  With
			 *     `codec_chiesto` alone, a child that lost the stage while a
			 *     client was watching ran with `poll` at zero — that is it
			 *     burned a whole core capturing nothing.  `[M]` it is the
			 *     silent half of the 14 August defect: the log is cured by
			 *     removing a line, this is not. */
			/* ⛔⭐⭐ AND THE `poll` WAIT GETS SHORTER WHEN AN ATTEMPT IS DUE —
			 *       16 Aug 2026, and without this line the cure of
			 *       `PALCO_NASCITA_RIPROVA_MS` did not reach the ground.
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
				int attesa_ms = (codec_chiesto && cat) ? 0 : 1000;

				/*
				 * ⛔⭐⭐ AND ZERO MEANS "NOW", NOT "NOT ARMED" — 16 Aug 2026,
				 *       and it is the SECOND time this number deceives in this
				 *       file.
				 *
				 * `[M]` The client's canvas arrives, the handler sets
				 * `palco_riprova_ms = 0` to say "retry at once", and this
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
				 *    puts `palco_riprova_ms` back in the future, so the zero
				 *    holds for one round only.
				 */
				if (!cat) {
					uint64_t adesso = registro_ora_ms();

					attesa_ms = palco_riprova_ms > adesso
					                ? (int)(palco_riprova_ms - adesso)
					                : 0;
					if (attesa_ms > 1000)
						attesa_ms = 1000;
				}
				/* ⛔⭐ AND WITH AUDIO ON THE LOOP CANNOT SLEEP A SECOND.  The
				 *     ring fills at 48 000 frames per second whatever the video
				 *     does: a 1000 ms wait would make it overflow **while the
				 *     desktop is still**, that is precisely when the user is
				 *     listening to music without touching anything.
				 * ⚠ 5 ms is a PCM block (§5.3): the loop wakes up in time to
				 *   take them away one at a time, instead of piling them up
				 *   and then dropping them. */
				if (audio_codec && attesa_ms > 5)
					attesa_ms = 5;
				pronto = poll(due, (nfds_t)quanti, attesa_ms);
			}
			pf.revents = due[0].revents;
			/* ⛔⛔ AND HERE THE DEBT TOWARDS WHOEVER IS PASTING IS PAID, at
			 *      every wake-up of the loop — even when the `poll` expired
			 *      empty.
			 *
			 *      ⚠ It is the only place where the `APPUNTI_ATTESA_MS` timeout
			 *        can fire: the clipboard thread has no clock (it waits for
			 *        D-Bus signals, and if none arrive it sleeps forever), so
			 *        an unanswered request would stay hanging until someone
			 *        copies something else.
			 *      ⛔ That is, without this line the timeout would exist on
			 *        paper and never fire — the worst form of a protection:
			 *        the one read in the code that is not there. */
			appunti_scadi(registro_ora_ms());
			/* ⭐ If `libei` spoke, it is served AT ONCE — even before reading
			 *    the parent: it is the path on which latency is measured. */
			if (pronto > 0 && quanti == 2 && due[1].revents)
				input_gira(palco_input);
			if (pronto < 0) {
				if (errno == EINTR)
					continue;
				fine = true;
				break;
			}
			if (pronto == 0)
				break;
			/* ⛔⛔⛔ AND HERE WERE THE FOUR SECONDS THE USER WAITED.
			 *
			 * `[M]` 14 Aug 2026, stack read with `gdb` 2.6 s after login: the
			 * child was stuck in `recvmsg` at `figlio.c:336`, that is on this
			 * line, on **fd 3** — the parent's socket.
			 *
			 * ⛔ The line above computed `pf.revents` and **nobody looked at
			 *    it**.  When the `poll` wakes up because `libei` spoke
			 *    (due[1]) and the parent said NOTHING, `pronto` is > 0 anyway:
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

			letti = ricevi_con_credenziali(fd_figlio, busta, sizeof busta, &chi,
			                               &c_e);
			if (letti == 0) {
				registro_dice(REG_FIGLIO,
				              "the parent closed the socket: dismantling the stage and "
				              "exiting.  ⚠ It is the SECOND safety net, the one "
				              "that does not depend on PR_SET_PDEATHSIG");
				fine = true;
				break;
			}
			if (letti < 0) {
				if (errno == EINTR)
					continue;
				if (errno == EAGAIN || errno == EWOULDBLOCK)
					break;
				fine = true;
				break;
			}
			if ((size_t)letti < sizeof t)
				continue;
			memcpy(&t, busta, sizeof t);
			if (!magia_giusta(&t))
				continue;
			/* ⛔ The parent must be root AND must be my parent process.  A
			 *    message without the kernel's stamp is not a message from the
			 *    parent. */
			if (!c_e || chi.uid != 0) {
				registro_dice(REG_FIGLIO,
				              "⛔ a message that claims to come from the parent and "
				              "does not carry root's stamp (uid %ld): DISCARDED",
				              c_e ? (long)chi.uid : -1L);
				continue;
			}
			if (t.uid_dichiarato != (uint32_t)mio_uid) {
				registro_dice(REG_FIGLIO,
				              "⛔ the parent believes I am uid %lu and the kernel "
				              "says %ld: I do NOT answer",
				              (unsigned long)t.uid_dichiarato, (long)mio_uid);
				continue;
			}
			if (t.tipo == MSG_SPEGNITI) {
				fine = true;
				break;
			}
			if (t.tipo == MSG_VIDEO) {
				struct corpo_video cv;
				if ((size_t)letti < sizeof t + sizeof cv)
					continue;
				memcpy(&cv, busta + sizeof t, sizeof cv);
				/* ⛔⭐ THE CEILING IS 3 SINCE 20 AUG 2026 (H.264, §1.13-ter), and
				 *     this line cost a round: the parent already negotiated
				 *     codec 3 and the child REFUSED it here — "the parent asks
				 *     for codec 3, which §6.2 does not define" — with the
				 *     session alive, zero frames and the page not knowing why.
				 * ⚠ The maximum number lives in ONE place only: here.  A second
				 *   check elsewhere with a number of its own is exactly the
				 *   defect just paid for. */
				if (cv.codec > CODIFICATORE_H264) {
					registro_dice(REG_FIGLIO,
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
				if (cv.codec != 0 && sessione_chiusa_dall_utente) {
					sessione_chiusa_dall_utente = false;
					registro_dice(REG_FIGLIO,
					              "⭐ §7.6: someone reattaches after a logout "
					              "— from now on the graphical session can be made "
					              "to be born again, and it will be NEW");
				}
				if (cv.codec != codec_chiesto)
					registro_dice(REG_FIGLIO,
					              cv.codec
					                  ? "⭐ PHASE 3: the frame loop turns "
					                    "ON, codec %u, %d/s asked of the "
					                    "capture"
					                  : "the frame loop turns OFF "
					                    "(codec %u): nobody is watching any more, and "
					                    "the stage stays up (I4).  %d/s",
					              cv.codec, MOVIMENTO_FPS);
				/* ⛔ And the depth with it: they are the same fact, and
				 *    separating them is exactly what has just been cured. */
				if (cv.profondita && cv.profondita != profondita_chiesta) {
					registro_dice(REG_FIGLIO,
					              "⭐ §4.3: the parent negotiated %u bits "
					              "(before %u)",
					              cv.profondita, profondita_chiesta);
					profondita_chiesta = cv.profondita;
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
				if (cv.codec && cv.livello_x10 != livello_chiesto_x10) {
					if (cv.livello_x10)
						registro_dice(REG_FIGLIO,
						              "⭐ §4.3: the client declares "
						              "video.livello=%u.%u (before %s) — I WILL "
						              "IMPOSE it on the encoder, and then "
						              "read it back from the SPS",
						              cv.livello_x10 / 10u,
						              cv.livello_x10 % 10u,
						              livello_chiesto_x10 ? "another one" : "none");
					else
						registro_dice(REG_FIGLIO,
						              "⚠ §4.3: no video.livello declared "
						              "(before %u.%u) — NO CEILING, and I do not "
						              "invent one: the level produced is "
						              "written anyway",
						              livello_chiesto_x10 / 10u,
						              livello_chiesto_x10 % 10u);
					livello_chiesto_x10 = cv.livello_x10;
				}
				codec_chiesto = cv.codec;
				/* ⛔ §5.2: the debt is set on the REQUESTED codec, not on all.
				 *    Asking for a keyframe for HEVC does not produce one on
				 *    AV1, and setting them together would give a keyframe to
				 *    whoever did not ask for it. */
				if (cv.chiave && cv.codec)
					debito_chiave[cv.codec] = true;
				continue;
			}
			if (t.tipo == MSG_AUDIO) {
				struct corpo_audio ca;

				if ((size_t)letti < sizeof t + sizeof ca)
					continue;
				memcpy(&ca, busta + sizeof t, sizeof ca);
				if (ca.codec > 2) {
					registro_dice(REG_FIGLIO,
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
					suono_volume_massimo(son);
					registro_dettaglio(REG_FIGLIO,
					                   "someone else connects: volume at "
					                   "maximum (I5), capture unchanged");
					continue;
				}
				audio_regola_figlio(ca.codec);
				continue;
			}
			/* ⭐⭐ PHASE 7 — "THE CLIENT HAS COPIED SOME TEXT": it is offered to
			 *     the session, and from there on someone will be able to
			 *     paste it.
			 * ⛔ It does not carry the text, and it is §7.4's "announce first,
			 *    then pull": the text is requested when someone really
			 *    pastes. */
			if (t.tipo == MSG_APPUNTI_OFFERTA) {
				GError *sb = NULL;

				if (!palco_appunti) {
					/* ⚠ It is not a fault: it is the stage not being there yet,
					 *   or the clipboard that did not open (the declared
					 *   fallback further up).  It is said, and we go on. */
					appunti_offerta_arretrata = true;
					registro_dettaglio(REG_APPUNTI,
					                   "the client copied some text and the "
					                   "session's clipboard is not there "
					                   "YET: the offer is REDONE as soon as it "
					                   "opens, instead of falling");
					continue;
				}
				if (!appunti_offri(palco_appunti, &sb))
					registro_dice(REG_APPUNTI,
					              "⛔ the offer to the session did not succeed "
					              "(%s): inside the desktop it will not be possible to "
					              "paste what the client copied",
					              sb ? sb->message : "no details");
				g_clear_error(&sb);
				continue;
			}
			/* ⭐⭐ AND THE ANSWER TO WHOEVER IS PASTING, which arrives **in
			 *     pieces**. */
			if (t.tipo == MSG_APPUNTI_DAL_CLIENT) {
				struct corpo_appunti ca;

				if ((size_t)letti < sizeof t + sizeof ca)
					continue;
				memcpy(&ca, busta + sizeof t, sizeof ca);
				if ((size_t)letti < sizeof t + sizeof ca + ca.pezzo)
					continue;
				appunti_dal_client(&ca, busta + sizeof t + sizeof ca);
				continue;
			}
			if (t.tipo == MSG_DISPOSIZIONE) {
				struct corpo_disposizione cd;

				if ((size_t)letti < sizeof t + sizeof cd)
					continue;
				memcpy(&cd, busta + sizeof t, sizeof cd);
				/* ⛔ WE impose the NUL: the envelope comes from a socket, and
				 *    an unterminated string read as such is a memory defect,
				 *    not a keyboard one. */
				cd.nome[sizeof cd.nome - 1] = '\0';
				/* ⚠ And if the stage is not there yet, it is DECLARED: "I did
				 *   not apply it" and "there was nothing to apply" are two
				 *   different facts (`LEZIONI.md` §1.9 rule 1). */
				if (!palco_input) {
					/* ⛔ It is NOT thrown away: it is KEPT.  `rcp.c` asks for
					 *    it when `SESSIONE` has gone out, and `libei` opens a
					 *    few hundredths later — throwing it away here would
					 *    mean the cure works on every attach except the FIRST. */
					snprintf(disposizione_in_attesa,
					         sizeof disposizione_in_attesa, "%s", cd.nome);
					registro_dice(REG_FIGLIO,
					              "⚠ layout «%s» requested but the input channel "
					              "is not there yet: KEPT, it is "
					              "applied when the stage opens",
					              cd.nome);
				}
				else
					input_disposizione(palco_input, cd.nome);
				continue;
			}
			if (t.tipo == MSG_INPUT) {
				struct corpo_input ci;
				int e;

				if ((size_t)letti < sizeof t + sizeof ci)
					continue;
				memcpy(&ci, busta + sizeof t, sizeof ci);
				/* ⛔⭐ THE CANVAS IS NOT AN INPUT, and it goes BEFORE the guard
				 *     below.  ⚠ Defect found while rereading, on 15 Aug 2026:
				 *     `FIGLI_INPUT_RITELA` travels inside `MSG_INPUT` so as not
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
				if (ci.azione == FIGLI_INPUT_TERMINA) {
					/* ⛔ The REAL cause is said, not the usual one: for a day
					 *    this line said "the user asked" even when the one
					 *    asking was a clock. */
					registro_dice(REG_FIGLIO,
					              ci.a == FIGLI_USCITA_ABBANDONO
					                  ? "⭐ §5.3: the session is ABANDONED — "
					                    "closing the graphical session and with it its "
					                    "programs.  ⚠ Nobody asked for it: "
					                    "the ceiling expired, and the "
					                    "number is in the parent's line"
					                  : "⭐ §7.6: the user asked to LOG OUT — "
					                    "closing the graphical session and with it its "
					                    "programs.  At the next attach a NEW one "
					                    "will be born");
					if (!sessione_termina()) {
						registro_dice(REG_FIGLIO,
						              "⛔ the graphical session did NOT "
						              "end: the user asked to "
						              "log out and the desktop is still "
						              "there.  ⚠ The client has already been "
						              "given the farewell 0x10, so "
						              "now the two truths do not "
						              "match — and this line is "
						              "the only place where it shows");
						continue;
					}
					/* ⛔⭐ PHASE 17 T7 — AND THE CHILD EXITS WITH IT.
					 *     As long as it was the one opening the desktop's logind
					 *     session, the logout took it away (SIGTERM, see
					 *     `congeda_figlio()` in the parent: "child dead =
					 *     session over").  ⚠ The child that TAKES BACK a desktop
					 *     found again sits in a logind session of its own, and
					 *     the logout does not touch it: `[M]` 30 Sep 2026, it
					 *     stayed alive and at the next round MADE a desktop nobody
					 *     had asked for be born again.  ⇒ Once the session is
					 *     closed, it exits: the stage is gone, and the next attach
					 *     will make a NEW child and desktop be born. */
					registro_dice(REG_FIGLIO,
					              "⭐ the graphical session is closed: I am exiting too "
					              "— the next attach will have a NEW child and "
					              "desktop");
					fine = true;
					break;
				}

				if (ci.azione == FIGLI_INPUT_RITELA) {
					CatturaRitela r;
					uint32_t ora_l = 0, ora_a = 0;

					/* ⛔ The WANTED canvas is remembered BEFORE trying, and it
					 *    is not the same thing as `tela_l`/`tela_a` (which are
					 *    what the stage GIVES): it serves the remount.
					 *    ⚠ Without it, a stage falling after a resize is born
					 *    again at the previous size and the bands come back —
					 *    and no line connects the two things. */
					tela_voluta_l = (uint32_t)ci.a;
					tela_voluta_a = (uint32_t)ci.b;
					/* ⭐ From now on the canvas is THE CLIENT'S, not the command
					 *    line's fallback: see `tela_dal_cliente`. */
					if (!tela_dal_cliente) {
						tela_dal_cliente = true;
						/* ⭐ And it is retried AT ONCE: waiting for the next
						 *    retry would mean throwing away the half second
						 *    just waited on purpose. */
						palco_riprova_ms = 0;
						registro_dice(REG_FIGLIO,
						              "⭐ the CLIENT's canvas has arrived (%ux%u): "
						              "from now on the session can be born "
						              "at the right size, without resizing it "
						              "later",
						              tela_voluta_l, tela_voluta_a);
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
						 *      2. we answer `NON_ORA`, and `rcp.c` CLOSES the
						 *         request: `tela_volo = false`;
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
						registro_dice(REG_FIGLIO,
						              "§7.1: the parent asks for the canvas %ux%u but the "
						              "stage is not there YET: telling it «WAIT», "
						              "and retrying AT ONCE instead of finishing the wait "
						              "— there is someone waiting",
						              (unsigned)ci.a, (unsigned)ci.b);
						attendi_tela(tela_voluta_l, tela_voluta_a);
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
						palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
						palco_riprova_ms = 0;
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
					 * ⚠ `!palco_input` is not a fault: it is a session without
					 *   input, and the line was already written by whoever did
					 *   not open it.
					 */
					if (palco_input) {
						int giu = input_rilascia_tutto(palco_input);
						if (giu > 0)
							registro_dice(REG_FIGLIO,
							              "⭐ §7.1: RELEASED %d keys and "
							              "buttons BEFORE resizing — the "
							              "canvas change makes the libei devices "
							              "be recreated, and a button pressed during "
							              "the turnover stays down IN THE SEAT "
							              "forever (Mutter, `meta-seat-impl.c` "
							              "`update_button_count()`): from then on "
							              "the desktop no longer takes a click",
							              giu);
						else
							registro_dettaglio(REG_FIGLIO,
							                   "§7.1: nothing to release before "
							                   "the resize (%d)", giu);
					}
					/* ⭐ PHASE 12 — on KDE the output is not resized
					 *    (`misura_del_palco()`): the answer is the size that
					 *    exists, and the page rescales.  Asking the capture for
					 *    another would make it fall forever. */
					if (palco_kwin) {
						uint32_t kl = tela_voluta_l, ka = tela_voluta_a;

						misura_del_palco(&kl, &ka);
						rispondi_tela(tela_voluta_l, tela_voluta_a, kl, ka);
						continue;
					}
					r = cattura_ridimensiona(cat, tela_voluta_l, tela_voluta_a);
					if (r == CATTURA_RITELA_CHIESTA) {
						/*
						 * ⛔ "REQUESTED" IS NOT "THE STREAM IS STILL ALIVE" — `[M]`
						 *    22 Aug 2026, bench
						 *    `banchi/06-b5-esiti-cattura.c` case 2: if the
						 *    producer cannot hold the size, the renegotiation
						 *    does not leave the stream where it was, it **kills**
						 *    it 2 ms after this return.
						 *
						 * ⭐ And no new outcome is needed here, because the road
						 *    to know it is already the one this loop travels:
						 *    `cattura_prendi()` looks at the state BEFORE
						 *    waiting ⇒ `[M]` **8.1 ms**, a single round, and the
						 *    message names "error, no more input formats".  From
						 *    there it goes through `THE STAGE HAS GONE FROM UNDER
						 *    OUR FEET` and remounts.
						 *
						 * ⏳⛔ AND THE DEFECT THAT REMAINS OPEN, declared instead
						 *     of hushed up: the remount asks for
						 *     `prendi_il_palco(tela_voluta_*)`, that is **the same
						 *     size that has just killed the stage**, and with
						 *     `codec_chiesto && tela_voluta_l` it picks the SHORT
						 *     wait.  `[M]` (bench 06-b5 case 3) `cattura_avvia()`
						 *     at that size **SUCCEEDS 3 times out of 3** and the
						 *     stage is dead 300 ms later, 3 out of 3 ⇒ the loop
						 *     does not get out by itself, and `attendi_tela()` at
						 *     every round also prevents the parent from expiring.
						 *     ⚠ On the real product it is `[?]`: Mutter granted 30
						 *     sizes out of 30 up to 7680x4320, and
						 *     `rcp_misura_ammessa()` since 1 Oct 2026 cuts at
						 *     4096x2304.  The cure lies in the remount policy,
						 *     not here.
						 */
						registro_dice(REG_FIGLIO,
						              "⭐ §7.1: canvas %ux%u REQUESTED of the compositor.  "
						              "The answer to the client goes out when a "
						              "frame arrives, not from this line",
						              (unsigned)ci.a, (unsigned)ci.b);
						continue;
					}
					if (r == CATTURA_RITELA_GIA_COSI) {
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
						 * `cattura_misura_negoziata()` returns `FALSE` when the
						 * format **has not been negotiated yet**, and in that
						 * case ⛔ it writes NOTHING in the two parameters: `ora_l`
						 * and `ora_a` stay the zeros they are born with.  ⚠ And
						 * for `rispondi_tela()` zero is not "I don't know": it is
						 * **"I did not make it"** (`figlio.h`, `corpo_tela`),
						 * which `rcp.c` passes on to the client as
						 * `TELA(RIFIUTATA, NON_ORA)`.
						 *
						 * ⇒ On a **healthy** session the client was told no for a
						 *   canvas the stage already has, and the page showed
						 *   "fit" as failed.  ⛔ It is the form of `CODER.md`
						 *   §3.10 — *a denied reading is not a reading that says
						 *   zero* — inside the message that exists precisely to
						 *   take an inference away from the parent (`LEZIONI.md`
						 *   §7.5).
						 *
						 * ⚠ The window is narrow and must be said: between
						 *   `cattura_avvia()` and the first format callback.
						 *   `[M]` 16 Aug 2026, 38 passes through this branch on
						 *   bench 06-b35: **zero** with the format unknown — that
						 *   is the defect is REAL and I have not seen it fire.
						 *   ⇒ The cure is written anyway, because the case is
						 *   named by the code and the price of getting it wrong
						 *   is a "no" to someone who did nothing wrong.
						 *
						 * ⭐ And the right answer is the REQUESTED size: in this
						 *   branch `cattura_ridimensiona()` answered `GIA_COSI`
						 *   precisely **because** the requested size is the one
						 *   the stream has (`cattura.c`, the guard of §kde
						 *   §8.2-bis: with the format unknown it compares the
						 *   requested one).  ⇒ Saying it is not an invention: it
						 *   is the only number known for certain in that branch.
						 */
						if (!cattura_misura_negoziata(cat, &ora_l, &ora_a)) {
							ora_l = tela_voluta_l;
							ora_a = tela_voluta_a;
							registro_dice(REG_FIGLIO,
							              "⚠ §7.1: the stage already has the canvas %ux%u, "
							              "but the format is NOT negotiated "
							              "yet: answering with the "
							              "REQUESTED size.  ⛔ A zero here would mean "
							              "«I did not make it» to a client that "
							              "did nothing wrong (CODER.md §3.10)",
							              (unsigned)ci.a, (unsigned)ci.b);
						} else
							registro_dice(REG_FIGLIO,
							              "§7.1: the stage already has the canvas %ux%u "
							              "(negotiated %ux%u): answering at once",
							              (unsigned)ci.a, (unsigned)ci.b, ora_l,
							              ora_a);
						rispondi_tela(tela_voluta_l, tela_voluta_a, ora_l, ora_a);
						continue;
					}
					registro_dice(REG_FIGLIO,
					              "⛔ §7.1: canvas %ux%u NOT requested — the stream is not "
					              "able right now.  Saying it at once: the client will get "
					              "`TELA(NON_ORA)` instead of three seconds of waiting",
					              (unsigned)ci.a, (unsigned)ci.b);
					rispondi_tela(tela_voluta_l, tela_voluta_a, 0, 0);
					continue;
				}
				if (!palco_input) {
					/* ⛔ "I have no input channel" is NOT "the client made a
					 *    mistake": it is DECLARED and we carry on, and the
					 *    session stays up.  ⚠ In chatter: at sixty messages per
					 *    second one line for each would bury the log. */
					registro_dettaglio(REG_FIGLIO,
					                   "input %u (action %u) and no channel "
					                   "to the compositor: NOT injected",
					                   (unsigned)ci.id, (unsigned)ci.azione);
					input_rifiutati++;
					continue;
				}
				switch (ci.azione) {
				case FIGLI_INPUT_PUNTATORE:
					e = input_puntatore(palco_input, (uint32_t)ci.a,
					                    (uint32_t)ci.b);
					break;
				case FIGLI_INPUT_PULSANTE:
					e = input_pulsante(palco_input, ci.codice, ci.premuto);
					break;
				case FIGLI_INPUT_ROTELLA:
					/* ⛔ The sign is inverted by `input_rotella()`, only once:
					 *    here it passes whole, half notches included. */
					e = input_rotella(palco_input, ci.a, ci.b);
					break;
				case FIGLI_INPUT_LETTERA:
					e = input_lettera(palco_input, (uint32_t)ci.a);
					break;
				case FIGLI_INPUT_POSIZIONE:
					e = input_posizione(palco_input, ci.codice, ci.premuto);
					break;
				case FIGLI_INPUT_RILASCIA_TUTTO: {
					int quanti = input_rilascia_tutto(palco_input);
					registro_dice(REG_FIGLIO,
					              "⭐ §7.3: released %d keys and buttons "
					              "that were still held down.  ⚠ Zero is NOT a "
					              "fault: it means nothing was "
					              "pressed",
					              quanti);
					continue;
				}
				/* ⛔ `FIGLI_INPUT_RITELA` does not appear here: it is served
				 *    BEFORE the input channel guard, a few lines up, and the
				 *    reason is there.  ⚠ If it reappeared in this `switch` there
				 *    would be two roads for the same message, and the second
				 *    would never be travelled — that is code that looks alive. */
				default:
					registro_dice(REG_FIGLIO,
					              "⛔ unknown input action %u: NOT "
					              "injected",
					              (unsigned)ci.azione);
					input_rifiutati++;
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
					input_iniettato = ci.id;
					/* ⭐ THE REAL SHAPE ON LABWC: after every pointer gesture
					 *    TAKEN, the probe looks at the pixel of the encoded theme
					 *    under the point (`wlroots.h`).  On GNOME and KDE it does
					 *    nothing: the shape already comes from the metadata. */
					if (ci.azione == FIGLI_INPUT_PUNTATORE) {
						sonda_x = (uint32_t)ci.a;
						sonda_y = (uint32_t)ci.b;
						sonda_nota = true;
					}
					if (sonda_nota && (ci.azione == FIGLI_INPUT_PUNTATORE ||
					                   ci.azione == FIGLI_INPUT_PULSANTE))
						cattura_sonda_puntatore(cat, sonda_x, sonda_y);
				} else if (e == 1) {
					/* ⛔ Only `input_lettera`: "not producible with this
					 *    layout".  The log line has already been written by
					 *    `tastiera.c`, with WHICH layout in it: here it is only
					 *    counted, or the same thing would end up twice in two
					 *    different wordings. */
					input_non_producibili++;
				} else {
					input_rifiutati++;
					registro_dettaglio(REG_FIGLIO,
					                   "input %u (action %u): the compositor "
					                   "did not take it",
					                   (unsigned)ci.id, (unsigned)ci.azione);
				}
				continue;
			}
			if (t.tipo == MSG_RIMANDA_PALCO) {
				int quanti = 0;
				for (uint8_t c = 1; c < 3; c++) {
					if (!tenuto[c])
						continue;
					manda_fotogramma(c, tenuto_chiave[c], tenuto_l, tenuto_a,
					                 tenuto_istante, tenuto[c], tenuto_byte[c],
					                 tenuto_input);
					quanti++;
				}
				registro_dice(REG_FIGLIO,
				              quanti
				                  ? "the parent asked for the stage: sending again %d "
				                    "streams (the last KEYFRAME kept — a delta "
				                    "without its past would be a wrecked "
				                    "image, §5.2)"
				                  : "the parent asked for the stage and I have "
				                    "nothing to send again (%d): the reason is "
				                    "in the lines above",
				              quanti);
				/* ⛔ And the debt is set: whoever comes back needs a NEW
				 *    keyframe, not the previous one — that one is already being
				 *    received, but its decoder starts again from there and the
				 *    deltas that follow belong to another chain. */
				if (codec_chiesto)
					debito_chiave[codec_chiesto] = true;

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
				if (palco_appunti)
					appunti_leggi_adesso(palco_appunti);
				continue;
			}
			if (t.tipo == MSG_CHI_SEI) {
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
				s.descrittori = quanti_descrittori();
				manda(MSG_SONO, &s, sizeof s, NULL, 0);
				continue;
			}
		}
		if (fine)
			break;

		/* ── 1-bis. the input channel, which has a voice of its own ──────── */
		/* ⛔⭐ `libei` is NOT a library one just calls: it is a peer that
		 *     SPEAKS, and among the things it says are the two silent
		 *     turnovers of `STUDI.md` §gnome §9 — a keymap change destroys and
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
		if (palco_input)
			input_gira(palco_input);

		/* ── 1-ter. the stage that is not there: it is REMOUNTED ─────────── */
		/* ⛔⭐ THE TWO TWIN DEFECTS ARE CURED HERE, AND IT IS THE SAME PLACE
		 *     BECAUSE THEY ARE THE SAME FACT: *the child does not know its
		 *     stage is no longer there, or not there yet.*
		 *
		 *   · not there YET — the graphical session did not exist at birth;
		 *   · no longer there — the session died under a live child, and
		 *     `cattura_prendi` declared the fault below.
		 *
		 * ⚠ And it does not disconnect (§8.3): the RCP session stays up, the
		 *   client stays connected, and when the stage comes back the desktop
		 *   reappears by itself.  ⛔ But it does not stand still either: a child
		 *   without a stage is not a frozen session, it is a child of no use. */
		if (!cat) {
			uint64_t ora = registro_ora_ms();
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
			if (ora < palco_riprova_ms) {
				static uint64_t detto_ms;

				if (ora - detto_ms >= 1000) {
					detto_ms = ora;
					registro_dice(REG_FIGLIO,
					              "⏳ without a stage and WAITING: %llu ms to the "
					              "next attempt (current wait %llu ms, "
					              "birth requested %llu ms ago) — ⚠ I am not "
					              "trying and failing: I am not trying",
					              (unsigned long long)(palco_riprova_ms - ora),
					              (unsigned long long)palco_attesa_ms,
					              nascita_chiesta_ms
					                  ? (unsigned long long)(ora - nascita_chiesta_ms)
					                  : 0ULL);
				}
			}
			if (ora >= palco_riprova_ms) {
				/* ⛔⭐ AND THE WHOLE ATTEMPT IS TIMED, not its three main
				 *     steps.
				 *
				 * `[M]` 16 Aug 2026: the three stopwatches inside
				 * `prendi_il_palco` were silent — no step above 250 ms — and yet
				 * in nineteen seconds there were TEN attempts, that is almost
				 * two seconds each.  ⇒ The time lay in a piece no stopwatch
				 * covered, and the candidate is the DISMANTLING of an attempt
				 * failed halfway: it closes objects on a compositor that does
				 * not answer, and `mutter.c` waits there up to FIFTEEN seconds.
				 *
				 * ⚠ Lesson, and it holds beyond this defect: **a stopwatch on
				 *   the steps you suspect measures your suspicions.**  What is
				 *   needed goes around the whole round. */
				uint64_t tentativo_ms = registro_ora_ms();
				bool preso;

				/* ⛔ It is remounted at the WANTED canvas, not at the one the
				 *    fallen stage had: what the client asked for does not die
				 *    with the graphical session.  ⚠ If the compositor grants
				 *    something else, the reconciliation of point 2 will say so
				 *    and the parent will know. */
				preso = prendi_il_palco(tela_voluta_l, tela_voluta_a, dir_rilievo,
				                        false, &mut, &cat);
				if (registro_ora_ms() - tentativo_ms >= 250)
					registro_dice(REG_FIGLIO,
					              "⏱ the WHOLE ATTEMPT (%s) took "
					              "%llu ms — and the stopwatches of the single steps "
					              "are silent: the time lies outside them",
					              preso ? "succeeded" : "failed",
					              (unsigned long long)(registro_ora_ms() - tentativo_ms));
				if (preso) {
					registro_dice(REG_FIGLIO,
					              "⭐⭐ RESTARTING THE CAPTURE: the stage came back "
					              "after %llu ms of waiting — and the next "
					              "frame will be a KEYFRAME (§5.2), because "
					              "whoever is watching has lost the stream's past",
					              (unsigned long long)palco_attesa_ms);
					palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
					palco_riprova_ms = 0;
					/* ⛔ §5.2: after a gap the client can NOT decode a delta —
					 *    its decoder no longer has the past of this chain.  The
					 *    debt is set on the REQUESTED codec, not on all. */
					if (codec_chiesto)
						debito_chiave[codec_chiesto] = true;
				} else {
					/* ⛔ What the attempt left halfway is dismantled: a `mut`
					 *    open without capture would keep a virtual monitor
					 *    nobody consumes. */
					smonta_il_palco(&mut, &cat);
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
					 * ⇒ See `PALCO_NASCITA_RIPROVA_MS`: it is the cure for "at
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
					 *     could not fire, because `nascita_chiesta_ms` is written
					 *     ONLY when the session turns out DEAD.
					 *
					 * ⭐ And the slow rounds are EXACTLY those in which the
					 *    session is not dead: it is the previous one still
					 *    closing (B7 of `SPECIFICHE.md` §5.9; `[M]` `loginctl`
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
				if (sta_nascendo(ora) || !tela_dal_cliente ||
				    (codec_chiesto && tela_voluta_l)) {
						palco_attesa_ms = PALCO_NASCITA_RIPROVA_MS;
						palco_riprova_ms = ora + palco_attesa_ms;
						registro_dettaglio(REG_FIGLIO,
						                   "without a stage and SOMEONE IS WATCHING (or the "
						                   "session is being born, requested %llu "
						                   "ms ago): retrying in %llu ms — densely "
						                   "on purpose, the doubling wait is "
						                   "for the stage that is NO LONGER there, "
						                   "not for the one that is not there YET",
						                   nascita_chiesta_ms
						                       ? (unsigned long long)(ora - nascita_chiesta_ms)
						                       : 0ULL,
						                   (unsigned long long)palco_attesa_ms);
						if (tela_voluta_l && tela_voluta_a)
							attendi_tela(tela_voluta_l, tela_voluta_a);
						/* ⛔⭐⭐ AND THE AUDIO RING IS EMPTIED BEFORE LEAVING
						 *       HERE, because this `continue` skips the
						 *       `audio_svuota()` line further down — and it is
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
						 *   nothing: `audio_svuota()` exits at once if audio is
						 *   not on, and what it touches (ring, audio encoder,
						 *   socket to the parent) has NOTHING to do with the
						 *   stage — the sink is a PipeWire node of ours, not a
						 *   canvas of the compositor. */
						audio_svuota();
						continue;
					}
					if (palco_attesa_ms < PALCO_RIPROVA_MIN_MS)
						palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
					else
						palco_attesa_ms *= 2;
					if (palco_attesa_ms > PALCO_RIPROVA_MAX_MS)
						palco_attesa_ms = PALCO_RIPROVA_MAX_MS;
					palco_riprova_ms = ora + palco_attesa_ms;
					registro_dice(REG_FIGLIO,
					              "⛔ NO STAGE: the attempt did not succeed "
					              "— retrying in %llu ms.  ⚠ The wait grows "
					              "on purpose: without it, this loop writes gigabytes "
					              "of log and burns a core",
					              (unsigned long long)palco_attesa_ms);
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
					if (tela_voluta_l && tela_voluta_a)
						attendi_tela(tela_voluta_l, tela_voluta_a);
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
		 *     birth of the session.  ⇒ There `audio_svuota()` is called by
		 *     hand, and the reason is written next to that `continue`.
		 * ⚠ Whoever adds a `continue` in this loop must decide the same, and
		 *   say so: above this line one passes through here, below one does
		 *   not. */
		audio_svuota();

		/* ── 2. the frame ────────────────────────────────────────────────── */
		if (!codec_chiesto || !cat)
			continue;
		{
			CatturaFermo fo;
			GError *sbaglio = NULL;
			CatturaPresa presa;
			uint64_t istante_us, adesso;

			memset(&fo, 0, sizeof fo);
			presa = cattura_prendi(cat, MOVIMENTO_ATTESA_S, &fo, &sbaglio);
			/* ⛔⭐ THE COUNT IS WRITTEN BEFORE LOOKING AT THE OUTCOME, AND IT IS
			 *     A CURE FOUND BY THE FIRST LIVE RUN (13 Aug 2026).
			 *
			 *     The first draft wrote this line only AFTER a delivered frame:
			 *     on a still desktop — that is on every machine without a
			 *     declared scene — the loop ran and the log said NOTHING.
			 *     ⛔ "The loop does not start", "the capture does not deliver"
			 *     and "the scene is still" all three had the same face:
			 *     silence.  It is exactly `LEZIONI.md` §1.9 — "empty" and
			 *     "forbidden" with the same look — inside the line that should
			 *     unmask it.
			 *
			 *     ⇒ Now it is written anyway, once per second, with the ZEROS
			 *     in it: whoever reads tells the three things apart without
			 *     inferring. */
			adesso = ora_monotona_us();
			if (adesso - ciclo_detto_ms >= 1000000u) {
				ciclo_detto_ms = adesso;
				registro_dice(REG_FIGLIO,
				              "loop: %llu frames delivered (%llu keyframes), "
				              "%llu empty waits (still scene: Mutter delivers "
				              "only when something changes), %llu faults — codec "
				              "%u, %d/s requested, wait %.2f s%s",
				              (unsigned long long)ciclo_fotogrammi,
				              (unsigned long long)ciclo_chiavi,
				              (unsigned long long)ciclo_zero,
				              (unsigned long long)ciclo_guasti, codec_chiesto,
				              MOVIMENTO_FPS, MOVIMENTO_ATTESA_S,
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
				              (ciclo_fotogrammi == 0 && ciclo_zero == 0
				               && ciclo_guasti == 0)
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
			 *    stream, which is what `cattura_risveglia()` does.
			 *
			 * ⚠ And it is done ONLY when a keyframe is due — that is when there
			 *   really is someone who cannot paint anything — and no more than
			 *   once every `RISVEGLIO_MS`: every restart costs the
			 *   renegotiation, and doing sixty per second would remove precisely
			 *   the frames being sought. */
			/* ⚠ `codec_chiesto` sits inside the array, and the bound is ONE:
			 *   whoever adds a codec must not find a second one written by hand
			 *   here (it was `< 3`, and it was left behind on 20 August). */
			if (presa == CATTURA_PRESA_ZERO && codec_chiesto < CODEC_MAX
			    && debito_chiave[codec_chiesto]) {
				uint64_t adesso_ms = registro_ora_ms();
				if (adesso_ms - risveglio_ms >= RISVEGLIO_MS) {
					/*
					 * ⛔⛔⛔ CURE "A" — 21 Aug 2026.  🔸 DERIVED by the
					 *       coordinator, and the price below is VISIBLE to the
					 *       user: when they see it, the judgement is theirs.
					 *
					 * THE FACT, `[M]` (bench `banchi/06-b33-risveglio.*`):
					 * `cattura_risveglia()` makes Mutter recreate the absolute
					 * devices — **3 wake-ups, 3 turnovers, with ZERO canvas
					 * changes** — and if at that moment a button is pressed,
					 * that button stays down **in the seat** and ⛔ **the
					 * desktop no longer takes a click for the whole session**.
					 * It is `fasi/06-la-tela-e-la-vista.md` §4.6, for the
					 * second door §7.1 found.
					 *
					 * ⛔ And this line sits in the worst possible place: one
					 *    gets here when **the scene is still**, that is exactly
					 *    when the user can hold the mouse down on a motionless
					 *    desktop.
					 *
					 * ⛔ The obvious cure — releasing first, as is done at
					 *    `:3964` before `cattura_ridimensiona()` — IS FORBIDDEN
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
					 *    ⚠ It is limited and heals by itself: `risveglio_ms` is
					 *      NOT touched, so at the first release the backoff has
					 *      already expired and the next round wakes up.
					 *    ⚠ And the scene is rare: a drag **moves** the desktop,
					 *      and then the grab is not ZERO and one does not even
					 *      get here.
					 *
					 * ⚠ What this guard does NOT cover is repaired by cure "C"
					 *   in `input.c` (`guarisci()`): the doors we do not control —
					 *   `monitors-changed`, the keymap change, and those GNOME
					 *   will add.
					 */
					unsigned giu = palco_input ? input_premuti(palco_input) : 0;

					if (giu) {
						/* ⛔ And it is said ONCE per wait, not at every round: at
						 *    400 ms each these lines would drown the log
						 *    precisely while the user drags. */
						if (!risveglio_zitto) {
							risveglio_zitto = 1;
							registro_dice(
							    REG_FIGLIO,
							    "⛔ a KEYFRAME is due and the scene is still, but %u "
							    "keys and buttons are HELD DOWN: I am NOT waking up "
							    "the stream.  ⭐ The wake-up makes the libei devices "
							    "be recreated (`[M]` §7.1) and a button pressed during "
							    "the turnover stays down IN THE SEAT forever.  🔸 The "
							    "price, declared: whoever has just attached may "
							    "see the blank page until the user lets go",
							    giu);
						}
					} else {
						risveglio_zitto = 0;
						risveglio_ms = adesso_ms;
						registro_dice(REG_FIGLIO,
						              "⭐ a KEYFRAME is due and the scene has been still for "
						              "%u ms: restarting the stream to get "
						              "a frame delivered.  ⚠ Without it, the user looks at a "
						              "blank page until something moves on the "
						              "desktop (`[M]` 4.4 s on 14 Aug 2026)",
						              (unsigned)RISVEGLIO_MS);
						cattura_risveglia(cat);
					}
				}
			}

			/* ⛔⭐ PHASE 12 — ON PLASMA THE SESSION DIES SILENTLY.  `[M]` 19
			 *    Sep 2026, the user's logout: KWin goes away, and the grab
			 *    returns "zero" forever — the child woke up the stream every
			 *    400 ms and the page stayed frozen on the last image instead of
			 *    going back to the login form (`DECISIONI.md` §4.1-quater).
			 *    ⇒ The connection to KWin is checked, and if it has fallen the
			 *    same road as "the stage has gone" is taken: dismantled, the
			 *    remount asks `sessione_stato()`, which says DEAD. */
			if (palco_kwin && kwin_chiuso(palco_kwin)) {
				registro_dice(REG_FIGLIO,
				              "⛔⛔ KWIN IS GONE: the Plasma session is over "
				              "(logout, or the compositor died).  Dismantling the "
				              "stage, and the next attempt will be able to say whether the "
				              "session is closed");
				g_clear_error(&sbaglio);
				cattura_fermo_libera(&fo);
				smonta_il_palco(&mut, &cat);
				palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
				palco_riprova_ms = registro_ora_ms() + palco_attesa_ms;
				continue;
			}
			if (presa == CATTURA_PRESA_ZERO) {
				/* ⛔ ZERO AND FAILURE ARE TWO DIFFERENT THINGS, and this is the
				 *    zero: the stream was active for the whole wait and nothing
				 *    arrived.  On Mutter it is the STILL DESKTOP, and it is a
				 *    result — `LEZIONI.md` §1.1: "a Wayland compositor delivers
				 *    a frame only when something changes".
				 *    ⚠ Nothing is encoded and nothing is sent: I1 forbids
				 *    lowering the rate out of caution, not standing still when
				 *    the scene does not move. */
				ciclo_zero++;
				g_clear_error(&sbaglio);
				continue;
			}
			if (presa != CATTURA_PRESA_FATTA
			    && presa != CATTURA_PRESA_PIXEL_ALTROVE) {
				/* ⛔⛔ AND HERE WERE THE 30.8 GB OF LOG.
				 *
				 * `[M]` 14 Aug 2026, the user's real session: the graphical
				 * session died under a live child, the PipeWire stream went
				 * into `connection error`, and `cattura_prendi` from that
				 * moment returns **at once** — the 0.25 s wait is not even
				 * spent, because the stream's state is checked before waiting
				 * (`cattura.c`).  ⇒ This `continue` put the loop back at the
				 * top **millions of times per second**, and every round wrote
				 * this line: 112 million identical lines, all in the same
				 * millisecond, and the disk full.
				 *
				 * ⇒ ⭐ Now the stage is DISMANTLED: `cat` becomes NULL, the
				 *   loop does not pass here again, and the remount with the
				 *   growing wait is at point 1-ter.  ⚠ The line is written
				 *   **once per loss**, not once per round. */
				ciclo_guasti++;
				registro_dice(REG_FIGLIO,
				              "⛔⛔ THE STAGE HAS GONE FROM UNDER OUR FEET "
				              "(grab %u: %s).  ⚠ It is NOT «the scene is still»: "
				              "it is the graphical session that is no longer there.  Dismantling "
				              "the stage and remounting it when it comes back — the RCP "
				              "session stays up (§8.3), and whoever is watching will see "
				              "the last image until the desktop reappears",
				              (unsigned)presa,
				              sbaglio ? sbaglio->message : "no details");
				g_clear_error(&sbaglio);
				cattura_fermo_libera(&fo);
				smonta_il_palco(&mut, &cat);
				palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
				palco_riprova_ms = registro_ora_ms() + palco_attesa_ms;
				continue;
			}
			g_clear_error(&sbaglio);

			/* ══ ⭐⭐ THE NEW SIZE HAS ARRIVED — and THE FRAME says it ══════════
			 *
			 * ⛔ It is the point where the resize becomes a fact, and there is
			 *    ONE on purpose: the request starts from `FIGLI_INPUT_RITELA`,
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
			 *      **not** width and height (`codificatore.h`): fed with an
			 *      image larger than the one it is open for it does not
			 *      complain — it crops or pads, and the defect shows only in the
			 *      image.  ⭐ And the reopening brings along the keyframe §5.2
			 *      demands ("on HEVC in Chrome a delta at the new size raises
			 *      nothing: the decoder keeps emitting frames at the OLD size");
			 *   2. the POINTER REGION is remapped.  Without it, the pointer stays
			 *      in the previous space and goes elsewhere — the defect measured
			 *      for two days on the DeX;
			 *   3. `tela_l`/`tela_a` become the real ones, because they are the
			 *      numbers that end up in the 28 bytes of §6.2 and that the
			 *      parent compares with the canvas in force.  ⛔ Until they were,
			 *      those two fields said what the child had REQUESTED at birth:
			 *      a size DECLARED and never verified, that is guard 3 of
			 *      §5.0-sexies open at the last link.
			 *
			 * ⚠ And this round's frame is sent ANYWAY, at its own size: it is
			 *   the first at the new size, and it is the one that makes the
			 *   parent send `TELA(ADATTATA)` (§7.1).  Throwing it away would mean
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
			 *    `tela_l`/`tela_a` to a size those pixels did not have.
			 *
			 * ⚠ `larghezza`/`altezza` at zero made the old guard EMPTY
			 *   (`byte < 0` is always false): they are named, instead of
			 *   trusting the numbers to add up. */
			/* ⚠ And it holds on both roads, with the same arithmetic: on the
			 *   card `byte` is not a copy to read but `stride x height` read
			 *   from the chunk, and whoever imports the DMA-BUF describes exactly
			 *   that region.  ⛔ A stride shorter than the declared width would
			 *   make the GPU read beyond the object, which is the same defect as
			 *   before with another reader. */
			if (!fo.larghezza || !fo.altezza || !fo.stride
			    || fo.stride < (guint64) fo.larghezza * 4u
			    || fo.byte < (guint64) fo.stride * fo.altezza) {
				fotogrammi_incoerenti++;
				if (fotogrammi_incoerenti == 1)
					registro_dice(REG_FIGLIO,
					              "⛔ frame DISCARDED: it declares %ux%u with stride %u "
					              "and carries %llu bytes — whoever compresses it would read "
					              "beyond the copy (stride >= %llu and bytes >= "
					              "%llu are needed).  ⚠ It is the window between a renegotiation and "
					              "the new buffers",
					              fo.larghezza, fo.altezza, fo.stride,
					              (unsigned long long)fo.byte,
					              (unsigned long long)((guint64)fo.larghezza * 4u),
					              (unsigned long long)((guint64)fo.stride * fo.altezza));
				cattura_fermo_libera(&fo);
				continue;
			}

			if (fo.larghezza != tela_l || fo.altezza != tela_a) {
				uint32_t chiesta_l = 0, chiesta_a = 0;
				char errore[256];

				/* ⭐ AND THIS IS THE PLACE WHERE THE DIVERGENCE IS REALLY READ,
				 *    and it is the only one: `cattura.c` sees it on the FORMAT —
				 *    where it cannot know whether that `Format` answers the
				 *    current request or a superseded one — while here it is seen
				 *    on the PIXELS, which have arrived and cannot be taken back.
				 *    It is the rule of §5.0-sexies: *"the frame tells the truth"*.
				 *
				 * ⚠ `[M]` 22 Aug 2026, bench `banchi/06-b5-esiti-cattura.c`
				 *   case 4: here too the two numbers can diverge for an INNOCENT
				 *   reason — two chained `ADATTA_TELA` (the user dragging the
				 *   edge), where this frame answers the earlier request and the
				 *   new one's is on its way.  ⇒ The line NAMES both motives
				 *   instead of accusing one: a log that attributes the wrong
				 *   cause costs more than a silent log.  ⛔ And in neither case
				 *   does the behaviour change: the reconciliation below looks at
				 *   the frame, which is right in both. */
				cattura_misura_chiesta(cat, &chiesta_l, &chiesta_a);
				registro_dice(REG_FIGLIO,
				              "⭐⭐ NEW CANVAS FROM THE STAGE: %ux%u → %ux%u (asked of the "
				              "producer %ux%u)%s.  Reopening the encoder, "
				              "remapping the pointer, and from here the 28 bytes of §6.2 "
				              "carry the new size",
				              tela_l, tela_a, fo.larghezza, fo.altezza, chiesta_l,
				              chiesta_a,
				              (chiesta_l == fo.larghezza && chiesta_a == fo.altezza)
				                  ? ""
				                  : " — ⛔ GRANTED DIFFERS FROM REQUESTED: either the "
				                    "compositor granted something else (§4.5 "
				                    "allows it), or this frame answers a "
				                    "SUPERSEDED request (`[M]` two chained ADATTA_TELA, "
				                    "bench 06-b5 case 4).  ⚠ Reconciling "
				                    "on the FRAME, which is right in both");

				/* 1. the encoder, ⛔ ALL the live ones: the keyframe debt is per
				 *    codec, and an encoder open and not resized would deliver
				 *    cropped images at the first frame after a codec change. */
				for (uint8_t c = 1; c < CODEC_MAX; c++) {
					if (!codif[c])
						continue;
					if (!codificatore_ridimensiona(codif[c], fo.larghezza,
					                               fo.altezza, errore,
					                               sizeof errore)) {
						registro_dice(REG_FIGLIO,
						              "⛔⛔ encoder %u did NOT reopen at "
						              "%ux%u (%s): DROPPING it instead of feeding it "
						              "an image that is not its own — better "
						              "no frame than a cropped one",
						              c, fo.larghezza, fo.altezza, errore);
						codificatore_libera(codif[c]);
						codif[c] = NULL;
					}
					/* ⛔ §5.2: the first at the new size MUST be a keyframe.
					 *    `codificatore_ridimensiona()` already imposes it by
					 *    itself; the debt is set anyway, because an encoder
					 *    DROPPED above will be born again from the
					 *    `codificatore_di()` further down and that one knows
					 *    nothing about this change. */
					debito_chiave[c] = true;
				}

				/* 2. the pointer region.  ⚠ If there is no input channel it is not
				 *    a fault: it is a session without input, and it is silent here
				 *    because the line was already written by whoever did not open
				 *    it. */
				if (palco_input
				    && input_ritela(palco_input, fo.larghezza, fo.altezza) != 0)
					registro_dice(REG_FIGLIO,
					              "⛔ the pointer region did NOT get remapped "
					              "on %ux%u: from here on the pointer would go "
					              "where it must not",
					              fo.larghezza, fo.altezza);
				/* ⭐ PHASE 15, D-007 — the screen changed size: the windows left
				 *    partly outside are brought back inside (on GNOME and KDE the
				 *    compositor does it, and the call does nothing).  ⚠ HERE, at
				 *    the first frame of the new size: labwc has already redone
				 *    the layout. */
				if (palco_input)
					input_riporta_dentro(palco_input);

				/* 3. ⛔ AND THE KEPT KEYFRAMES ARE THROWN AWAY — defect found
				 *    while refuting: `tenuto[]` is per CODEC, but
				 *    `tenuto_l`/`tenuto_a` are a single pair.  ⇒ After a resize
				 *    the inactive codec kept a keyframe of the OLD size that
				 *    `MSG_RIMANDA_PALCO` would have sent declaring the NEW size:
				 *    the client would have sized the canvas on one number and
				 *    received pixels of another — that is the stretched image and
				 *    the misplaced pointer, the defect this chain exists to
				 *    close. */
				for (uint8_t c = 0; c < 3; c++) {
					if (!tenuto[c])
						continue;
					free(tenuto[c]);
					tenuto[c] = NULL;
					tenuto_byte[c] = 0;
					tenuto_chiave[c] = false;
				}

				/* 4. and the real size becomes ours. */
				tela_l = fo.larghezza;
				tela_a = fo.altezza;

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
				if (COPIA_ZERO && !scheda_mai_piu && scheda_negata_l != 0
				    && strada_del_palco == CATTURA_STRADA_MEMORIA
				    && (fo.larghezza != scheda_negata_l
				        || fo.altezza != scheda_negata_a)) {
					scheda_negata_l = 0;
					scheda_negata_a = 0;
					scheda_da_riprovare = true;
					registro_dice(REG_FIGLIO,
					              "⭐ new canvas %ux%u: zero copy had been "
					              "denied for the previous canvas, and on this one it is "
					              "retried",
					              fo.larghezza, fo.altezza);
				}

				/* 5. ⭐⭐ AND THE PARENT IS ANSWERED, as it is waiting for this
				 *    number: without it, it would have to GUESS from the frames
				 *    which request this size answers — and with two chained
				 *    requests it would guess wrong.  ⚠ It is sent even when
				 *    nobody had asked for anything (the stage drifting by
				 *    itself): it is a fact, and whoever receives it decides what
				 *    to do with it. */
				rispondi_tela(tela_voluta_l, tela_voluta_a, tela_l, tela_a);
			}

			istante_us = istante_del_fotogramma(&fo, ora_monotona_us());
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
			codifica_e_manda(&fo, codec_del_numero(codec_chiesto),
			                 codec_chiesto, NULL, NULL, istante_us, tela_l,
			                 tela_a, input_iniettato);
			/* ⛔⭐ THE RELEASE — and on the card's road this line is NOT a
			 *     clean-up: it is the cure of `LEZIONI.md` §8.  Until it is
			 *     called, Mutter's buffer is ours; and it is called AFTER the
			 *     encoding, that is after the GPU has finished reading it
			 *     (`codificatore_comprimi_scheda` really waits before
			 *     returning).  ⚠ Moving it two lines up would bring back the
			 *     two alternating screens. */
			cattura_fermo_libera(&fo);

			/* ⛔ And if the card turned out not viable — encoder in software,
			 *    or a stride that cannot be imported — the PIXELS' ROUTE
			 *    changes.  ⚠ It is done HERE and not inside `codifica_e_manda`:
			 *    the hold is already released, and remounting with a buffer
			 *    still in hand would return a `pw_buffer` to a capture that is
			 *    gone.
			 *
			 * ⛔⛔⛔ AND SINCE 25 AUG 2026 **ONLY THE STREAM** IS REMOUNTED, not
			 *      the stage: the box above `rimonta_solo_la_cattura()` carries
			 *      the core and the stack.  In short — dismantling the stage
			 *      closed a **freshly born** EIS channel, and `ei_disconnect()`
			 *      killed the child with a SIGSEGV **before the first frame**,
			 *      for a window 1268 px wide.  ⚠ The dismantling stays as a
			 *      FALLBACK, for the only case in which the node cannot be taken
			 *      back. */
			if (scheda_da_abbandonare || scheda_da_riprovare) {
				strada_del_palco = scheda_da_riprovare
				                       ? CATTURA_STRADA_SCHEDA
				                       : CATTURA_STRADA_MEMORIA;
				scheda_da_abbandonare = false;
				scheda_da_riprovare = false;
				if (rimonta_solo_la_cattura(mut, &cat, tela_l, tela_a))
					continue;
				smonta_il_palco(&mut, &cat);
				palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
				palco_riprova_ms = registro_ora_ms() + palco_attesa_ms;
				continue;
			}
		}
	}

	codificatori_libera();
	for (uint8_t c = 0; c < 3; c++) {
		free(tenuto[c]);
		tenuto[c] = NULL;
	}
	registro_dice(REG_FIGLIO,
	              "the loop stops: %llu frames delivered (%llu keyframes), "
	              "%llu empty waits, %llu faults",
	              (unsigned long long)ciclo_fotogrammi,
	              (unsigned long long)ciclo_chiavi,
	              (unsigned long long)ciclo_zero,
	              (unsigned long long)ciclo_guasti);

	/* ⛔⭐ AND BEFORE EVERYTHING ELSE WHAT WAS LEFT HELD DOWN IS RELEASED.
	 *
	 *     `RCP.md` §11 calls it "the rule with the highest damage/cost ratio
	 *     of the document", and here it bites in the worst way: the stage
	 *     outlives the client (I4), so a Ctrl left pressed **does not go away
	 *     with the connection** — it stays on the user's desktop, which at
	 *     reattach is found unusable without the two things being connected.
	 * ⚠ And it is done here too, not only at the end of each connection: this
	 *   is the last instant in which someone can still do it. */
	registro_dice(REG_FIGLIO,
	              "the input channel closes: %u injected, %u refused "
	              "by the compositor, %u not producible with the layout (§7.3)",
	              (unsigned)input_iniettato, (unsigned)input_rifiutati,
	              (unsigned)input_non_producibili);
	/* ⚠ And the release is done by `smonta_il_palco`, which is the SAME
	 *   dismantling as the remount: two roads to dismantle the stage would
	 *   mean that one of the two, one day, will forget a piece. */
	smonta_il_palco(&mut, &cat);
	/* ⛔ And the audio is turned off BEFORE exiting, in the right order:
	 *    `audio_regola_figlio(0)` stops the capture and WAITS for the PipeWire
	 *    thread.  ⚠ Exiting with that thread still alive would mean letting it
	 *    write into the ring of a dying process — and the defect would show up
	 *    every now and then, at exit, which is the place where nobody looks. */
	audio_regola_figlio(0);
	if (son) {
		suono_chiudi(son);
		son = NULL;
	}
	/* ⭐ R1/R2: if the session is gone, the manager goes back to how it was */
	sessione_sgombera_gestore("the child exits");
	registro_dice(REG_FIGLIO, "the child of «%s» has dismantled the stage and is exiting",
	              utente);
	_exit(0);
}
