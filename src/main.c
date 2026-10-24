/*
 * main.c — REMOTIX, the server.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT THIS PROGRAM IS, AND WHAT IT IS NOT YET
 *
 * It is the server of `SPECS.md` §1: the RCP handshake over WebTransport, the
 * page served by the server itself, the per-user children with video, audio,
 * input and clipboard.  (It began as the bare wire of phase 1; the first log
 * line still says so, and the benches look for it.)
 *
 * ⚠ What the user sees and judges: they open `https://address:7447`, click
 *   the warning the first time on that device, type user and password, and the
 *   page says «admitted, new session, canvas 1920×1080, GNOME desktop» — or it
 *   says WHY not, with a sentence and not with a number (`RCP.md` §8.2).
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE TWO LISTENERS, WITH THE SAME PORT NUMBER
 *
 * `RCP.md` §2.4: **7447**, UDP for HTTP/3 and WebTransport, TCP for the first
 * load of the page.  ⚠ And the two things are INDEPENDENT: WebTransport does
 * not use `Alt-Svc`, it opens its connection on its own (measurement S1).
 * ⛔ The silent fallback to TCP declared as a danger in `PLAN.md` phase 1
 * cannot happen — that line predates the measurement.
 *
 * ---------------------------------------------------------------------------
 * ⛔ ONE SINGLE THREAD, AND NOW IT IS NO LONGER A PROBLEM — 12 Aug 2026
 *
 * Everything runs in a single `poll` loop, and stays that way.  ⛔ What has
 * changed is that **the loop no longer calls PAM**: `DECISIONS.md` §1.10, from
 * the user, at the close of phase 1.
 *
 * ⚠ What this box said until yesterday — «the PAM check BLOCKS that thread,
 *   so one user's handshake delays everyone else's packets» — was true and
 *   MEASURED: `[M]` B8, evening of 11 August, **from 1.0 to 2.2 seconds per
 *   attempt**, and it was PAM adding them (+1034 ms beyond the fixed second on
 *   the rejected against +84 ms on the admitted, the signature of
 *   `pam_faildelay`).
 *
 * ⭐ Now PAM is queried by a **helper process** (`helper.c`), and the shape
 *    is the one the user decided: a process, not a thread, because PAM is not
 *    reliably reentrant.  Three lines remain in here: the helper's descriptor
 *    enters the `poll` together with the others, the answers are delivered,
 *    and the questions without an answer expire.
 *
 * ⛔ And the reason it was cured BEFORE phase 2, which is not elegance:
 *    without video the symptom was «the last of ten waits ten seconds»; with
 *    video it would have been **the screen of everyone connected freezing
 *    every time someone else logs in** — and whoever sees it blames the video,
 *    because that is where it shows.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ AND SINCE 12 AUG 2026 THIS PROCESS NO LONGER CAPTURES ANYTHING — §1.10-bis
 *
 * `DECISIONS.md` §1.10-bis: the server stays **privileged**, and for every
 * admitted user it spawns a **child that runs as that user**, which holds the
 * session bus, the capture and the devices.  ⛔ The reason is a measurement,
 * not a preference: `[M]` root does not connect to the user's session bus, and
 * `[M]` only root can check another user's password with PAM.
 *
 * ⇒ Out of here went `session_ensure()` and `first_frame()`, which
 *   until yesterday sat right in this file: now they live in `child.c`, on
 *   the other side of the privilege drop.  ⭐ And it is not only a matter of
 *   permissions: **this process no longer touches GLib, PipeWire or D-Bus**,
 *   so the `fork()` that spawns a child starts from a single-threaded process
 *   — which is the only condition in which a `fork` from a library with
 *   threads is not a gamble.
 */
#include "helper.h"
/* ⛔ For `audio_silence_hush()`: the test tone of `--audio-test` opens an
 *    audio encoder in THIS process, not only in the child.  ⚠ If only the
 *    child received the switch, the tone bench and the real-session bench
 *    would measure two different products. */
#include "audio.h"
#include "budget.h"
#include "certificates.h"
#include "command.h"
#include "child.h"
#include "sentinel.h"
#include "rediscover.h"
#include "page.h"
#include "rcp.h"
#include "log.h"
#include "tls.h"
#include "transport.h"
#include "webtransport.h"
#include "session.h"
#include "kwin.h"

#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <openssl/ssl.h>

#define DEFAULT_PORT "7447" /* RCP.md §2.4 */

/* ⛔⭐ THE CANVAS, IN ONE PLACE ONLY — and until 12 Aug 2026 there were three.
 *
 *     `PLAN.md` phase 1 declares «canvas 1920×1080»; `src/page.html` asks
 *     for it in the `HELLO` (line 1503); `P2-1-sessione.md` §6.3 wrote
 *     `1920, 1080` by hand inside `main.c` and declared it a debt: *«whoever
 *     grafts should tie them to a single constant, or in two weeks they will
 *     be three places»*.
 *
 * ⭐ Here the constant is one, and it is used by all three things that must
 *    match: the virtual monitor asked of the session, the size with which the
 *    capture is opened, and the size with which encoding happens.  ⛔ If they
 *    did not match the symptom would NOT be an error: it would be a §6.2
 *    header declaring one size while the pixels carry another, and the client
 *    has no way to notice.
 *
 * ⚠ What stays outside, and must be said: the canvas the client ASKS for in
 *   the `HELLO`.  That one is the client's, §4.5 allows the server to reduce
 *   it, and `video_forse()` in `webtransport.c` refuses to send if it does not
 *   match this one — instead of sending a frame that lies. */
#define CANVAS_W 1920u
#define CANVAS_H 1080u

/* 1 for UDP, 1 for the TCP listener, the rest for the TCP connections. */
#define MAX_POLL 64

/* ⭐ §5.1 — how often the local graphical sessions are checked again.
 *
 * ⚠ Two seconds, and the two numbers that justify them are one per direction:
 *   it is the maximum DELAY between «the user sat down in front of the
 *   machine» and «the remote session drops» — which nobody watches with a
 *   stopwatch — and it is also the COST, because every check is a synchronous
 *   call to logind inside the loop that delivers frames (`LESSONS.md`
 *   §6.2-bis).
 *
 * ⭐ AND SINCE 25 AUG 2026 THE COST NO LONGER DEPENDS ON THE TENANTS: the
 *   check asks **one** question for everyone (`sentinel_locals()`), not one
 *   for each.  `[M]` §6.13: it was `N × D`, and at N=7 with logind at 286 ms
 *   every desktop collapsed to 1.3 frames/s without a line being written. */
#define LOCAL_SWEEP_MS 2000

/* ⭐ How often the guard's count is written — see the caller of
 *   `sentinel_counts()` in the loop.  ⚠ One minute: it is a cumulative count,
 *   and at every check it would be 43 200 lines a day, almost all the same. */
#define GUARDIAN_COUNT_MS 60000

static volatile sig_atomic_t stop_requested;

static void on_signal(int s)
{
	(void)s;
	stop_requested = 1;
}

static void help(const char *name)
{
	fprintf(stderr,
	        "REMOTIX — the server\n"
	        "\n"
	        "  %s [options]\n"
	        "  %s --encoding-test [h264|hevc] [--node /dev/dri/renderDN]\n"
	        "                    [--encoding-route card|vulkan|vaapi]\n"
	        "                    one frame with the choice of a real session,\n"
	        "                    on the card; one JSON line on stdout,\n"
	        "                    exits 0 if the card encodes, 3 if no card\n"
	        "                    can encode, 1 if it opens and produces\n"
	        "                    nothing\n"
	        "\n"
	        "  --encoding-route ROUTE\n"
	        "                    ⭐ phase 19: the card's route — `card`\n"
	        "                    (default: by CAPABILITY, Vulkan Video if\n"
	        "                    the card offers it for that codec, otherwise\n"
	        "                    VA-API), `vulkan` or `vaapi` to force it in\n"
	        "                    tests and diagnosis (it fails saying so\n"
	        "                    if absent: no fallback to the other)\n"
	        "\n"
	        "  --address ADDR    what to listen on (default: 0.0.0.0)\n"
	        "  --name NAME       the name or address that goes into the certificate\n"
	        "                    (default: the one of --address, and if it is\n"
	        "                     0.0.0.0 it must be declared: a wrong\n"
	        "                     subjectAltName makes a DIFFERENT warning appear)\n"
	        "  --port N          default: %s  (RCP.md §2.4)\n"
	        "  --certificates DIR\n"
	        "                    where the two certificates are kept\n"
	        "  --page FILE       the page to serve over TCP\n"
	        "  --ban-file FILE   where the address ban is kept\n"
	        "                    (RCP.md §4.4-bis: it survives restart)\n"
	        "  --command-socket PATH\n"
	        "                    the 0600 Unix socket of the unblock command:\n"
	        "                    «UNBLOCK <address>» or «PING».  Without it,\n"
	        "                    the only way out of the ban is the 12 hours\n"
	        "  --survey DIR      ⭐ phase 2: writes there the captured frame\n"
	        "                    (cattura.bgrx) and the two encoded streams.\n"
	        "                    Without it, writes nothing.  It serves the\n"
	        "                    pixel comparison of F2.6\n"
	        "  --verbose         detailed log\n"
	        "  --journal         ⭐ phase 16 §12: every log line ALSO goes\n"
	        "                    to the systemd journal, with the fields REMOTIX_AREA,\n"
	        "                    REMOTIX_TENANT, PRIORITY (3 ⛔, 4 ⚠, 6; the\n"
	        "                    --verbose detail lines never reach the journal)\n"
	        "                    and SYSLOG_IDENTIFIER=remotix.  The\n"
	        "                    line on stderr stays identical; it also applies\n"
	        "                    to the children (journalctl -t remotix)\n"
	        "\n"
	        "  ⭐⭐⭐ PHASE 9 — THE FIVE CURES, AND SINCE 24 AUG 2026 ALL FIVE\n"
	        "     ARE ON (the user's decision, after looking at them\n"
	        "     on the real desktop: invariant I6 was walked through, not\n"
	        "     bypassed).  ⛔ Each one can still be turned off, with ONE road\n"
	        "     only; the value in force ends up in the log at startup,\n"
	        "     on AND off.  The five, and how they are turned off:\n"
	        "        video queue threshold     --clear-threshold-ms 0\n"
	        "        rate regulator            --no-adaptive-rate\n"
	        "        dead line                 --no-dead-line\n"
	        "        ghost eviction            --eviction-ms 0\n"
	        "        audio silence             --no-audio-silence\n"
	        "  --clear-threshold-ms N\n"
	        "                    §5.1: a delta stuck in the queue is abandoned\n"
	        "                    only if the queue does not drain within N ms;\n"
	        "                    below the threshold it is KEPT.  ⭐ DEFAULT 100\n"
	        "                    (on since 24 Aug 2026).  0 = OFF, and it\n"
	        "                    abandons at every more recent frame,\n"
	        "                    as it was until 23 Aug.  ⚠ The price, `[M]`\n"
	        "                    09-b79: up to +160 ms of drift on a bad\n"
	        "                    network, ZERO on the healthy line.  The line is\n"
	        "                    written by webtransport.c\n"
	        "  --quality-recovery\n"
	        "                    quality goes back up one step after a\n"
	        "                    number of comfortable frames below the ceiling of\n"
	        "                    §6.2.  Without it, once down it stays down for\n"
	        "                    the whole session.  ⛔ It lives in the CHILD: the\n"
	        "                    line is written by encoder.c at opening\n"
	        "  --bandwidth-cap-mbit N\n"
	        "                    N is the FLOOR in Mbit/s (30, §3.1-sexies),\n"
	        "                    not the ceiling: wire, working point and\n"
	        "                    reservoir are derived from it.  0 = off, and\n"
	        "                    then nobody says no to bandwidth.  ⛔ It lives\n"
	        "                    in the CHILD, and applies only in hardware\n"
	        "  --eviction-ms N   ⭐ the GHOST: if a user's slot is\n"
	        "                    held by a client silent for more than N\n"
	        "                    ms, and whoever asks for that slot is a client\n"
	        "                    of the SAME user, the slot is taken away\n"
	        "                    and goes to the newcomer.  ⭐ DEFAULT 15000\n"
	        "                    (on since 24 Aug 2026), that is half\n"
	        "                    the silence clock: it does not go\n"
	        "                    lower, because the browser's keep-alive is silent\n"
	        "                    `[M]` 15 s and a LIVE idle client would be\n"
	        "                    evicted.  ⚠ `[M]` the ghost goes from 32.13 s and\n"
	        "                    14 refusals to 16.83 s and 7.  0 = OFF, and the\n"
	        "                    slot is freed only by the silence clock\n"
	        "                    (30 s): whoever comes back after a drop is\n"
	        "                    told the slot is taken — by themselves\n"
	        "  --no-adaptive-rate\n"
	        "                    ⭐⭐ TURNS OFF the rate regulator, which since 24\n"
	        "                    Aug 2026 is ON by default: a frame does not\n"
	        "                    leave when two deltas in flight still have\n"
	        "                    bytes in the output queue\n"
	        "  --no-dead-line\n"
	        "                    ⛔⭐ TURNS OFF the DEAD LINE, which since 24 Aug 2026\n"
	        "                    is ON by default: a session is CLOSED\n"
	        "                    when the line can no longer be served — the\n"
	        "                    wire drops and one gets back in by hand (the\n"
	        "                    user's decision, 23 Aug 2026).  TWO causes: the\n"
	        "                    output STALL and the client's SILENCE;\n"
	        "                    every trigger writes in the log a\n"
	        "                    `dead-line` line with the numbers it decided on (I1).\n"
	        "                    ⛔⛔ IT IS THE CURE THAT CLOSES A SESSION: `[M]`\n"
	        "                    margin >10x above the worst line that HOLDS\n"
	        "                    and 2.9x below the one that serves nobody\n"
	        "\n"
	        "  ⭐⭐⭐ PHASE 10 — THE COMPOSITION BUDGET, and it is born OFF (I6)\n"
	        "  --budget-mpixel-s N\n"
	        "                    the Mpixel/s of COMPOSITION this machine\n"
	        "                    holds.  ⛔ 0 = OFF, and it is the DEFAULT:\n"
	        "                    without it, the server ADMITS EVERYONE and starves them\n"
	        "                    together (`[M]` the eleventh gets in and the first\n"
	        "                    session goes from 39.60 to 0.96 fps, −97.6 %%).\n"
	        "                    ⛔ It is NOT the ENCODER's number: `[M]` on\n"
	        "                    a UHD 770 the bare encoder holds 1.86\n"
	        "                    Gpixel/s and composition 0.97 — what saturates is\n"
	        "                    the compositor, not us.  Giving the former here\n"
	        "                    would admit ~22 sessions where six fit.\n"
	        "                    ⛔⛔ AND IT DOES NOT SELF-TUNE: until the machine\n"
	        "                    has GIVEN WAY at least once, the maximum\n"
	        "                    read is a lower bound, not a\n"
	        "                    ceiling.  Whoever types this option declares\n"
	        "                    they have measured.  Whoever does not fit receives FAREWELL\n"
	        "                    0x06 BUDGET_FULL, before their stage is born\n"
	        "  --reserve F       0..1, how much of the worst case of an\n"
	        "                    IDLE tenant is kept aside.  ⭐ 0.5 is the\n"
	        "                    DEFAULT: `[M]` 0 false yes and 0 false no,\n"
	        "                    cap 6 saturated / 10 idle.  0 = «delivered»\n"
	        "                    rule (6 saturated, idle unlimited: blind\n"
	        "                    to WAKE-UP) · 1 = «worst» rule (5 and 6,\n"
	        "                    with one false no).  ⛔ It serves against wake-up:\n"
	        "                    `[M]` eight idle ones at 0.01 %% each wake up\n"
	        "                    in 19 ms and ask for 130 %% of the engine\n"
	        "  --session-cap N\n"
	        "                    the ADMINISTRATIVE cap (§4.6): how many users\n"
	        "                    served at most.  ⭐ DEFAULT 10\n"
	        "                    (SPECS.md §5.5; it was 16 until 25 Aug\n"
	        "                    2026, and nobody had chosen it).  From here the\n"
	        "                    four tables that count a user are\n"
	        "                    sized.  ⚠ Whoever does not fit receives 0x0E, which is\n"
	        "                    a different fact from 0x06: the table is full, the\n"
	        "                    machine is not\n"
	        "  --no-audio-silence\n"
	        "                    ⭐⭐ TURNS OFF the AUDIO SILENCE, which since 24\n"
	        "                    Aug 2026 is ON by default: a block in which\n"
	        "                    ALL the samples are exactly zero does not\n"
	        "                    become a datagram.  ⚠ `[M]` 09-b84: 102.1\n"
	        "                    times less traffic with a still screen (557.6 →\n"
	        "                    5.5 kbit/s), 1 248 blocks silenced out of 1 248; the\n"
	        "                    price is +2 «missed» out of 5 000 at the client.\n"
	        "                    ⛔ Until 23 Aug it was a compile-time `-D`,\n"
	        "                    and that `-D` has been REMOVED: one road only\n"
	        "  --dead-line-stall-ms N\n"
	        "                    for how many ms no frame has gone out WHILE\n"
	        "                    HAVING some to send.  ⛔ Both halves\n"
	        "                    count: with a still scene there is nothing to\n"
	        "                    send, and the count does not even start.\n"
	        "                    Default 5000: 5.0 times above the whole empty\n"
	        "                    second of `raffica-1`, which HOLDS and\n"
	        "                    delivers 23.94 frames/s, and 2.9 times below\n"
	        "                    the 14.26 s of `raffica-forte`, which serves\n"
	        "                    nobody — `[M]` 23 Aug 2026.  0 = silence\n"
	        "                    only.  ⛔⛔ And LOSS is not a cause:\n"
	        "                    on a line that reorders, the loss\n"
	        "                    fraction measures the REORDERING — `casa-cattiva`\n"
	        "                    declared 512‰ of it and HELD for ten minutes,\n"
	        "                    `raffica-forte` 123‰ and did not hold.  The\n"
	        "                    number stays in the log as a WITNESS\n"
	        "  --dead-line-silence-s N\n"
	        "                    the seconds without a packet from the client.\n"
	        "                    Default 10.  ⚠ It also turns on the transport\n"
	        "                    PINGs at HALF this number, or «does not\n"
	        "                    answer» and «we did not ask it anything»\n"
	        "                    would look the same.  0 = stall\n"
	        "                    only\n"
	        "\n"
	        "  ⛔ `--internal-child` is NOT typed by hand: it is the line with which\n"
	        "     this same binary restarts as the child of an admitted\n"
	        "     user (DECISIONS.md §1.10-bis).  If you see it in `ps`, that\n"
	        "     is a child, not a second server.\n",
	        name, name, DEFAULT_PORT);
}

/* ⛔⭐ THE PAM SERVICE FILE, CHECKED AT STARTUP — finding B-11.
 *
 *     `SPECS.md` §4.2 wants the `remotix` service.  If the file is not
 *     there, Linux-PAM falls back to the `other` service, and neither outcome
 *     is acceptable: on Fedora and Arch `other` is `pam_deny` (**every** right
 *     password refused, and the user reads «user or password not correct» — a
 *     diagnosis pointing at the password while the defect is a missing file);
 *     on Debian it includes the common stacks, that is a stack that is not
 *     ours and without the exclusion of root (`src/remotix.pam`).
 *
 * ⭐ PHASE 17 (`phases/17-the-installer.md` §4.3-§4.4): the file is looked for
 *    where Linux-PAM looks for it — first `/etc/pam.d`, then `/usr/lib/pam.d`,
 *    where the openSUSE package puts it.
 *
 * ⚠ It does NOT refuse to start: without PAM the server is useless, but the
 *   ban of §4.4-bis, the page and the certificates work anyway, and turning
 *   everything off would put the red on the wrong defendant.  ⛔ The line,
 *   however, is written, and it is the protection invariant I7 asks for: it
 *   lives in the program, not in an installation note that gets lost. */
static void look_pam_service(void)
{
	static const char *const dove[] = { "/etc/pam.d/remotix", "/usr/lib/pam.d/remotix" };
	struct stat st;
	for (size_t i = 0; i < sizeof dove / sizeof dove[0]; i++) {
		if (stat(dove[i], &st) == 0) {
			registro_dice(LOG_STARTUP,
			              "PAM service «remotix»: %s is there (SPECS.md §4.2)",
			              dove[i]);
			return;
		}
	}
	registro_dice(LOG_STARTUP,
	              "⛔ the PAM service «remotix» DOES NOT EXIST (neither %s nor %s): PAM "
	              "will fall back to the «other» service, which is NOT the "
	              "REMOTIX stack — on Fedora and Arch it is pam_deny (EVERY right "
	              "password refused, and the user will read «user or password "
	              "not correct»), on Debian the common stacks without "
	              "the exclusion of root.  Install the file of the family: "
	              "src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch.",
	              dove[0], dove[1]);
}

/* ⛔ The two things the `poll` loop must be able to reach when a PAM verdict
 * arrives, and not one only: the transport (to get `ADMITTED` out) and the
 * children table (to spawn the stage of whoever got in).  ⚠ It lives in a
 * structure and not in two globals: a global is a second place where a thing
 * can be alive or dead. */
struct bridge {
	transport *t;
	children *f;
};

/* ⛔⭐⭐ PHASE 17, T7 — THE DESKTOPS FOUND AGAIN: live stages that no child holds.
 *
 *     `[M]` T2 (`phases/17-the-installer.md` §5.2): stopping the service does
 *     NOT kill the desktops — parent, helper and child die, the stage born
 *     with `setsid --fork` stays with its programs.  ⛔ And this parent
 *     restarted with an empty children table: nobody counted those desktops,
 *     neither the session cap, nor the budget, nor the abandonment clock.
 *
 * ⭐ At startup they are looked for (`rediscover.h`: logind session `remotix` with
 *    the stage leader inside) and they sit HERE, «waiting for reattach»:
 *      · the CAP counts children + found again (`stage_count()`);
 *      · the BUDGET puts them in the count like the stages with children;
 *      · the ABANDONMENT CLOCK starts from this parent's startup — declared:
 *        the last gesture seen by the previous parent was in its memory, and
 *        is gone;
 *      · at REATTACH the new child is born (D1: the child dies with the parent
 *        by choice, and is remade here), picks up the same compositor, and the
 *        user leaves this table to enter the children one;
 *      · if the clock expires without anyone coming back, a child is spawned
 *        to close the desktop: only it knows how to close every desktop,
 *        since it sits in the user's session bus (`session_terminate()`).
 * ⚠ And every FOUND_AGAIN_SWEEP_MS it is checked again that they are still
 *   there: a desktop that died on its own must not hold a slot of the cap for
 *   an hour.
 * ⛔ They are looked for ONLY at startup.  A child that dies while the parent
 *    is alive leaves its desktop as before (`dismiss_child()`): it is not the
 *    case of this stage. */
#define FOUND_AGAIN_SWEEP_MS 10000u
#define MAX_FOUND_AGAIN 256

static void presence_mark(const char *user, uint64_t now_ms);
static void presence_forget(const char *user);
/* ⚠ Tentative definition (C11 §6.9.2): the value and its box are further
 *   down, with the third clock of §5.3. */
static uint64_t abandon_ms;

static RediscoveredDesktop *found_again;
static int found_again_n;

static int found_again_index(const char *user)
{
	for (int i = 0; user && i < found_again_n; i++)
		if (strcmp(found_again[i].user, user) == 0)
			return i;
	return -1;
}

static bool found_again_of(const char *user)
{
	return found_again_index(user) >= 0;
}

static void found_again_remove(const char *user)
{
	int i = found_again_index(user);

	if (i < 0)
		return;
	found_again[i] = found_again[found_again_n - 1];
	found_again_n--;
}

/* ⭐ «How many stages are alive»: the children, plus the desktops found again
 *    that do not have a child yet — whoever comes back leaves `found_again` when
 *    theirs is born, so nobody is counted twice. */
static int stage_count(const struct bridge *p)
{
	return children_count(p->f) + found_again_n;
}

static void found_again_at_startup(uint64_t now_ms)
{
	char why[256] = "";
	char listing[1024] = "";
	size_t used_len = 0;
	int n;

	found_again = calloc(MAX_FOUND_AGAIN, sizeof *found_again);
	if (!found_again) {
		registro_dice(LOG_CHILD,
		              "⛔ PHASE 17 T7: no memory for the table of desktops "
		              "found again: those left alive by a previous parent are NOT "
		              "counted (cap, budget, abandonment)");
		return;
	}
	n = rediscover_search(found_again, MAX_FOUND_AGAIN, why, sizeof why);
	if (n < 0) {
		registro_dice(LOG_CHILD,
		              "⛔ PHASE 17 T7: could not look for live REMOTIX desktops "
		              "(%s).  ⚠ If the service was restarted with desktops "
		              "open, they are NOT counted: neither cap, nor budget, nor "
		              "abandonment clock",
		              why);
		return;
	}
	found_again_n = n;
	for (int i = 0; i < n; i++) {
		int k;

		registro_dice(LOG_CHILD,
		              "⭐ PHASE 17 T7 — FOUND AGAIN the desktop of «%s» (uid %ld): "
		              "logind session %s (PAM service «%s», %u in all), stage "
		              "pid %ld «%s».  It stays WAITING FOR REATTACH: it counts in the "
		              "cap and in the budget, and at reattach the new child picks up "
		              "this same desktop",
		              found_again[i].user, (long)found_again[i].uid,
		              found_again[i].session, FOUND_AGAIN_PAM_SERVICE,
		              found_again[i].sessions, (long)found_again[i].stage,
		              found_again[i].comm);
		/* ⚠ The abandonment clock restarts from NOW, and it is said below. */
		presence_mark(found_again[i].user, now_ms);
		k = snprintf(listing + used_len, sizeof listing - used_len, "%s«%s»",
		             used_len ? ", " : "", found_again[i].user);
		if (k > 0 && (size_t)k < sizeof listing - used_len)
			used_len += (size_t)k;
	}
	registro_dice(LOG_CHILD,
	              "⭐ PHASE 17 T7 — live REMOTIX desktops found again at startup: %d%s%s.  "
	              "The stages count %d out of a cap of %d; the "
	              "abandonment clock (%llu s) restarts for them from the startup of this "
	              "parent — the last gesture seen by the previous parent was not "
	              "kept",
	              n, n ? ": " : " (no logind session «remotix» with a live stage)",
	              listing, n, rcp_cap(),
	              (unsigned long long)(abandon_ms / 1000));
	if (n > rcp_cap())
		registro_dice(LOG_CHILD,
		              "⚠ PHASE 17 T7: the desktops found again (%d) are MORE than the "
		              "session cap (%d): no NEW user gets in until they "
		              "leave — whoever has their own desktop gets back in anyway",
		              n, rcp_cap());
}

/* ⭐ The check: a desktop found again that has died in the meantime leaves the counts.
 * ⚠ Only if there is at least one: with an empty table nobody is asked
 *   anything, and the loop that delivers frames does not pay. */
static void found_again_sweep(uint64_t now_ms)
{
	static uint64_t last;
	static bool mute_logged;
	RediscoveredDesktop *living;
	char why[256] = "";
	int n;

	if (!found_again_n || now_ms - last < FOUND_AGAIN_SWEEP_MS)
		return;
	last = now_ms;
	living = calloc(MAX_FOUND_AGAIN, sizeof *living);
	if (!living)
		return;
	n = rediscover_search(living, MAX_FOUND_AGAIN, why, sizeof why);
	if (n < 0) {
		if (!mute_logged) {
			mute_logged = true;
			registro_dice(LOG_CHILD,
			              "⚠ PHASE 17 T7: the check of the desktops found again got no "
			              "answer (%s): they stay in the counts until it is known",
			              why);
		}
		free(living);
		return;
	}
	mute_logged = false;
	for (int i = found_again_n - 1; i >= 0; i--) {
		bool c_e = false;
		char chi[sizeof found_again[0].user];

		for (int k = 0; k < n; k++)
			if (living[k].uid == found_again[i].uid)
				c_e = true;
		if (c_e)
			continue;
		memcpy(chi, found_again[i].user, sizeof chi);
		registro_dice(LOG_CHILD,
		              "⚠ PHASE 17 T7: the desktop found again of «%s» is gone "
		              "(the stage pid %ld «%s» vanished without anyone "
		              "coming back): it leaves the cap, the budget and the "
		              "abandonment clock",
		              chi, (long)found_again[i].stage, found_again[i].comm);
		found_again_remove(chi);
		presence_forget(chi);
	}
	free(living);
}

/* ⛔⭐⭐⭐ «DOES IT FIT?» — THE BUDGET'S QUESTION, phase 10 (25 Aug 2026).
 *
 *     ⛔ The defect it cures, `[M]` §S.2: the product **had no budget — it
 *     accepted everyone and starved everyone together**.  The eleventh got in
 *     with `denied 0` and the first session went from **39.60 to 0.96 fps**
 *     (−97.6 %), with 104 paired reds against invariant **I1**.
 *
 * ⛔ AND THE QUANTITY IS **COMPOSITION**, not encoding.  `DECISIONS.md`
 *    §4.6 says *«the real limit is set by the encoder»*: `[M]` on this
 *    hardware **it is not true** — the bare encoder holds 1.86 Gpixel/s,
 *    composition **0.97**, and what saturates `rcs0` is `gnome-shell` at
 *    99.5 % while `remotix` sits at 0.00 % (§6.11, §6.15).  The why of every
 *    number is in `budget.h`, at the top: **here there is only the seam**.
 *
 * ⭐⭐ AND «WHOEVER IS INSIDE» ARE THE **STAGES**, not the slots of the RCP
 *     registry: a session that left its slot through silence **still encodes**
 *     as long as its stage is alive (§3.2, the *ghost*), and costs the GPU as
 *     much as the others.  ⇒ Counting the slots would underestimate
 *     **precisely in the scene where the machine is struggling**, which is the
 *     direction that starves everyone.
 *
 * ⛔ Returns `true` also when the budget is OFF and when it says «I do not
 *    know»: a budget that refused for not having been able to measure would
 *    make the user pay for a fault of ours.  ⚠ The «I do not know» is written,
 *    the yes is not. */
static bool has_capabilities(struct bridge *p, const char *user, char *why,
                         size_t why_cap, uint8_t *reason)
{
	struct budget_count tally;
	enum budget_outcome e;
	uint32_t tl = CANVAS_W, ta = CANVAS_H, ml, ma;
	int amount;

	if (!budget_on())
		return true;

	/* ⭐ THE CEILING OF THE NEWCOMER'S CANVAS, and it is known from the `HELLO`.
	 *
	 * ⛔ Here the canvas is not decided yet — it is decided at `SESSION` — but
	 *    §4.5 requires that the granted one not exceed the client's
	 *    `video.max_size`, and that number has already arrived.  ⇒ The
	 *    **minimum of the stage canvas and the client's ceiling** is counted,
	 *    that is an upper bound of the real cost: uncomfortable direction
	 *    (`LESSONS.md` §1.33).
	 * ⚠ If the client did not declare it the stage canvas stays, which is a
	 *   good upper bound all the same — and NOT a zero. */
	if (wt_max_size_of(user, &ml, &ma) && ml && ma) {
		if (ml < tl)
			tl = ml;
		if (ma < ta)
			ta = ma;
	}

	budget_count_open(&tally);
	amount = children_count(p->f);
	for (int i = 0; i < amount; i++) {
		const char *chi = children_nth_user(p->f, i);

		if (chi && chi[0])
			budget_count_inside(&tally, chi);
	}
	/* ⭐ PHASE 17 T7: and the desktops found again, which do not have a child
	 *    yet but go back to composing as soon as their user returns. */
	for (int i = 0; i < found_again_n; i++)
		budget_count_inside(&tally, found_again[i].user);
	e = budget_count_verdict(&tally, user, tl, ta, why, why_cap);
	if (e == BUDGET_DOES_NOT_HOLD) {
		*reason = RCP_BUDGET_FULL;
		return false;
	}
	if (e == BUDGET_UNKNOWN) {
		/* ⛔ «I could not measure» is not «it does not hold»: admit, and
		 *    declare it — a declared hole is worth more than an invented number. */
		registro_dice(REG_BUDGET,
		              "⚠ «%s» ADMITTED without the budget's judgement: %s",
		              user, why && why[0] ? why : "I did not measure");
		if (why && why_cap)
			why[0] = '\0';
		return true;
	}
	log_detail(REG_BUDGET, "«%s» fits: %s", user,
	                   why && why[0] ? why : "");
	if (why && why_cap)
		why[0] = '\0';
	return true;
}

/* ⛔⭐ THE BRIDGE BETWEEN THE HELPER, THE TRANSPORT AND THE CHILD.
 *
 *     `DECISIONS.md` §1.10-bis: the child is born **when PAM has said yes**,
 *     and this is the only line of the program where that fact exists with the
 *     user's NAME next to it.  ⛔ Not an instant before: a child spawned on
 *     `CREDENTIALS` would run as a user who has not yet proved to be who they
 *     are — invariant I3.
 *
 * ⚠ And the order of the two lines matters: first the child, then the verdict
 *   on the wire.  The child must start connecting to the bus and capturing
 *   **while** the fixed second of §4.4-bis runs, which is the only time
 *   guaranteed by the protocol before the session reaches `SESSION`.
 *   ⛔ Neither waits for the other: `children_ensure()` does a `fork` and
 *   returns, `transport_verdict()` moves the state forward.  The loop does
 *   not stop.
 *
 * ⭐ AND SINCE 25 AUG 2026 THE STEPS ARE THREE, not two: first we check
 *    **whether a stage fits**, then the child, then the verdict — and if the
 *    stage does not fit a FAREWELL goes out instead of silence.  It is the cure
 *    of defect **P3**, and the long box sits on the line that does it. */
/* ⭐ D-004: the presence table is further down, with its box; here it is only
 *    needed to start the clock at the birth of the stage. */
static void presence_mark(const char *user, uint64_t now_ms);

static void delivery_verdict(void *ctx, uint64_t ticket, bool admitted,
                              const char *user, const char *rhost)
{
	struct bridge *p = (struct bridge *)ctx;
	/* ⛔ The farewell is sent AFTER `transport_verdict()`: the long reason is
	 *    at the end of the function, in the box «AND THE FAREWELL GOES OUT
	 *    HERE, AFTER THE VERDICT». */
	char without_stage[320] = "";
	/* ⛔⭐ AND SINCE 25 AUG 2026 (evening) THE REASONS ARE **TWO**, not one —
	 *     §8.1 **D5**, and the two do NOT replace each other:
	 *
	 *       `0x0E` SESSION_UNSERVABLE  «the table is full»
	 *                                      ⇒ **administrative** limit
	 *                                      ⇒ gesture: *«try again, or ask to
	 *                                        raise the cap»*
	 *       `0x06` BUDGET_FULL            «this machine has no composition
	 *                                      capacity left»
	 *                                      ⇒ **physical** limit
	 *                                      ⇒ gesture: *«try again, or get in
	 *                                        asking for less quality»*
	 *
	 * ⚠ Two different facts cannot have the same outcome (finding R9.3): it is
	 *   the same rule for which `0x0F` had been removed from here.  ⛔ And
	 *   `0x06` was declared in `rcp.h` from day one and **nobody had ever sent
	 *   it** (`[M]` §3.4: `grep -r RCP_BUDGET_FULL src/ --include=*.c` ⇒ zero
	 *   callers).  This is the line that gives it its first sender. */
	uint8_t no_reason = RCP_SESSION_UNSERVABLE;
	/* ⭐ D-001: the stage was already there ⇒ `SESSION` will say `2 = RESUMED`. */
	bool resumed = false;

	if (admitted && user && user[0]) {
		/* ⛔ «It was already there» and «I have just spawned it» are two
		 *    different facts, and the difference is needed a line below: a
		 *    child just born is NOT asked to resend the stage — it is taking
		 *    it right now, and the request would produce a double frame. */
		bool c_era = children_pid_of(p->f, user) > 0;

		/* ⭐ D-001 — and «it was already there» is exactly the RESUMED of
		 *    §4.5: the child lives as long as the graphical session (child
		 *    dead = session over, see `dismiss_child()`). */
		resumed = c_era;
		/* ⭐⭐ PHASE 17 T7 — the child is not there, but the DESKTOP is: a
		 *     previous parent left it alive and this one found it again at
		 *     startup.  ⇒ For the counts it is like `c_era` (it is already
		 *     inside the cap and the budget, and the clock is not renewed);
		 *     for the child it is not — it is born now (D1) and picks up the
		 *     same compositor. */
		bool recovered = !c_era && found_again_of(user);

		if (recovered)
			resumed = true;

		/* ⛔⛔⭐ THE NO IS SAID BEFORE SPAWNING THE CHILD — 25 Aug 2026,
		 *      defect **P3** / finding **R10-A1**, and this is the line that
		 *      cures it.
		 *
		 * THE FACT.  The two caps are freed on DIFFERENT EVENTS: the slot in
		 * `attached[]` becomes free at detach (six roads, all through
		 * `slot_leave()`), ⛔ **the child does not** — it is invariant **I4**:
		 * the stage belongs to the session, not to the connection, and dies
		 * only by explicit logout or by abandonment at 60 minutes without input.
		 * ⇒ **The children table can be full while the slot table is empty.**
		 *   Ten tenants get in in the morning, work, close the browser: the
		 *   ten stages stay alive for up to an hour, and the eleventh finds
		 *   the slot free and the stage not.
		 *
		 * ⛔⛔ THE SYMPTOM THAT WAS THERE BEFORE.  `children_ensure()` returned
		 *      `false`, a log line was written — *«is ADMITTED but has no
		 *      child: gets in and does not see a pixel»* — and **NOTHING went out on
		 *      the wire**: neither `0x0E`, nor `0x06`.  The user received
		 *      `ADMITTED`, received `SESSION`, and looked at a **black page
		 *      without explanation and without any time after which it would
		 *      improve**.  ⛔ Which is precisely the defect for which
		 *      `slot_take()` had already been cured (finding **R9.3**): a
		 *      fact of the SERVER that reaches the client as silence.
		 *
		 * ⭐ THE MODEL IS `slot_take()`, in `rcp.c`: it tells «taken» from
		 *    «no more slots» and for the second sends `0x0E` with the detail in
		 *    the body.  `[M]` §6.4 saw it trigger 10 times out of 10, and §6.8
		 *    measured that the capsule reaches the browser 10 out of 10.  This
		 *    is the same seam, one step higher.
		 *
		 * ⛔ AND THE QUESTION IS ASKED **BEFORE**, not after.  `[M]` §6.4 point
		 *    6: at the end of the round a user **never admitted** had **42
		 *    processes and a `gnome-shell`** — that is PAM passed, child born,
		 *    graphical session on, and then the refusal.  *«Refusing after
		 *    turning on a desktop is not refusing: it is logging in and then
		 *    throwing out.»*  Here the cap is checked **ahead of**
		 *    `children_ensure()`, and whoever does not fit spawns nothing:
		 *    neither process, nor logind session, nor compositor.
		 *
		 * ⚠ `children_count()` and `children_pid_of()` already existed: no new
		 *   function is needed, what is needed is **asking first**. */
		if (!resumed && stage_count(p) >= rcp_cap()) {
			registro_dice(LOG_CHILD,
			              "⛔ «%s» passed PAM but will NOT have a stage: the "
			              "stages are %d out of %d (%d with children, %d found again "
			              "at startup and waiting for reattach), and ⛔ the slot "
			              "in the session registry may be FREE all "
			              "the same — the stage outlives the client (I4), the "
			              "slot does not.  ⭐ The child is NOT spawned: no "
			              "graphical session for whoever will be sent away (§8.1 D6), "
			              "and the no goes out on the wire with 0x0E",
			              user, stage_count(p), rcp_cap(),
			              children_count(p->f), found_again_n);
			snprintf(without_stage, sizeof without_stage,
			         "all the stages of this server are in use (%d of "
			         "%d): they are live graphical sessions, which are freed at "
			         "logout or after abandonment",
			         stage_count(p), rcp_cap());
		} else if (!resumed && !has_capabilities(p, user, without_stage,
		                                   sizeof without_stage, &no_reason)) {
			/* ⛔⭐⭐⭐ THE BUDGET — phase 10, and it is the reason for the phase.
			 *
			 *     ⛔ Until tonight this machine **accepted everyone and
			 *     starved them together**: `[M]` §S.2 — on the saturated scene
			 *     the eleventh got in with `denied 0`, and the first session
			 *     went from **39.60 to 0.96 fps** (−97.6 %), that is 104 paired
			 *     reds against invariant **I1**.
			 *
			 * ⭐ The question is asked HERE and not further on, for the same
			 *    reason as the stages branch: `[M]` §6.4 point 6 — a user
			 *    **never admitted** had 42 processes and a `gnome-shell`.
			 *    *«Refusing after turning on a desktop is not refusing: it is
			 *    logging in and then throwing out.»*
			 * ⚠ And only if `!c_era`: a user who already has a stage is already
			 *   inside the count — refusing them the reattach would be a false
			 *   NO on a capacity they are already spending anyway.
			 * ⛔ The why and the scene are in `budget.h`, at the top: here there
			 *    is the seam, not the calibration. */
			registro_dice(REG_BUDGET,
			              "⛔ «%s» passed PAM but does NOT get in: %s.  ⭐ The "
			              "child is NOT spawned (§8.1 D6) and the no goes out on the "
			              "wire with 0x06 BUDGET_FULL — which is a "
			              "PHYSICAL limit, not the full table of 0x0E",
			              user, without_stage);
		} else if (!children_ensure_from(p->f, user, rhost)) {
			/* ⚠ The OTHER five roads by which a child is not born: a name PAM
			 *   admits and NSS does not resolve, uid 0, `socketpair`,
			 *   `SO_PASSCRED`, `fork`.  ⛔ None of these is capacity: they are
			 *   faults of ours or of configuration, and the precise why is in
			 *   the line `children_ensure()` has just written.
			 * ⭐ But for whoever is at the other end of the wire the outcome is
			 *   identical — a black page — so the farewell is the same, and the
			 *   detail tells whoever diagnoses where to look. */
			registro_dice(LOG_CHILD,
			              "⛔ «%s» is ADMITTED but has no child, and NOT because of the "
			              "cap (stages %d out of %d): the why is in the line just "
			              "above.  ⭐ It is sent away with 0x0E instead of getting in "
			              "on a black page",
			              user, stage_count(p), rcp_cap());
			snprintf(without_stage, sizeof without_stage,
			         "the stage of «%s» did not mount and it is not a capacity "
			         "problem: the cause is in the previous log "
			         "line",
			         user);
		} else if (recovered) {
			/* ⭐ PHASE 17 T7: the child is born, and from now on the desktop is
			 *    its own — it leaves the found-again list so as not to count it
			 *    twice.  ⛔ The presence slot is NOT touched: it is a reattach,
			 *    and a reattach does not renew the clock (§5.3, 16 Aug 2026). */
			int i = found_again_index(user);

			registro_dice(LOG_CHILD,
			              "⭐ PHASE 17 T7 — «%s» COMES BACK to their desktop "
			              "found again (logind session %s, stage pid %ld «%s»): "
			              "the new child picks it up, and SESSION will say "
			              "RESUMED",
			              user, found_again[i].session,
			              (long)found_again[i].stage, found_again[i].comm);
			found_again_remove(user);
		} else if (!c_era) {
			/* ⛔⭐ D-004 (phase 15) — THE ABANDONMENT CLOCK STARTS AT BIRTH, not
			 *     at the first gesture.
			 *
			 * ⛔ Before, the presence table was filled ONLY in
			 *    `input_to_child()`: a session opened and never touched did
			 *    not enter the table, and ⛔ **never expired** — the stage stayed
			 *    alive forever, against §5.3 («60 minutes without input»).
			 * ⭐ From here the clock counts from when the session was born.
			 *    ⚠ And ONLY at birth: a reattach (`c_era`) does NOT renew it —
			 *    §5.3, decision of 16 Aug 2026: «one who attaches and just
			 *    watches no longer renews anything».
			 * ⚠ And it overwrites an old slot of the same user, if one was left
			 *   from a finished session: a new session does not inherit the
			 *   expiry of the dead one. */
			presence_mark(user, log_now_ms());
		} else {
			/* ⛔ A child that was already there may have its loop OFF — that
			 *    user's last session had gone and the stage had stopped
			 *    capturing.  ⚠ It is asked for the held frame (the last
			 *    KEYFRAME) so whoever comes back sees something at once, while
			 *    `video_rule()` turns the loop back on as soon as `SESSION`
			 *    starts.  ⛔ Not to a child JUST BORN: it is already taking it,
			 *    and the request would make it send the same frame twice. */
			children_ask_stage(p->f, user);
		}
		/* ⛔⭐ AND HERE THE COUNT OF THE DENIED IS WRITTEN — one line per
		 *     verdict, **even when the budget is off**, and that is the case
		 *     that matters: `[M]` §S.2 describes the defect in two words —
		 *     *«gets in with `denied 0`»* — and reading that zero is the fact
		 *     that proves **I6**.
		 * ⚠ It sits AFTER the chain and not inside its branches: a count
		 *   written in three different places is a count that one day will
		 *   forget one. */
		budget_verdict_line(user, without_stage[0] == '\0', no_reason,
		                     rcp_cap(), without_stage);
	}
	/* ⛔ `resumed` only if it really gets in: with a farewell on its way there
	 *    is no `SESSION` to fill. */
	transport_verdict(p->t, ticket, admitted, resumed && !without_stage[0]);

	/* ⛔⭐ AND THE FAREWELL GOES OUT HERE, AFTER THE VERDICT — and the order is
	 *     measured, not aesthetic.  Three reasons, all necessary:
	 *
	 *  1. ⛔ **`transport_verdict()` is the only place where the count of
	 *     §4.4-bis is reset** (`rcp_verdict()` → `reset_failed()`).
	 *     Sending the farewell first, the session would already be
	 *     `S_FINISHED`, nobody would take the verdict, and ⛔ **a user who got
	 *     the password right would keep the failed attempts on them**: two
	 *     mistakes and this one would ban them for twelve hours.
	 *  2. ⭐ This way the client **never sees `ADMITTED`**: `ADMITTED` does not
	 *     leave from here, it leaves from `rcp_time()` when the fixed second
	 *     has passed, and at that point the session is already over with its
	 *     reason.  ⇒ One single truth on the wire, not «get in» followed by
	 *     «get out».
	 *  3. ⚠ §4.4-bis is not violated.  That rule wants **the timer not to
	 *     distinguish what the reason does not distinguish**; here the reason
	 *     already distinguishes, and it is a declared choice: whoever passes
	 *     PAM and has no stage receives `0x0E`, whoever gets the password
	 *     wrong receives `0x07`.  ⛔ Yes, this tells whoever knocks that the
	 *     password was right — and it is the declared price of not leaving them
	 *     in front of a black page.  It is the same price `slot_take()`
	 *     already pays today with a full table.
	 *
	 * ⚠ And it goes through `wt_dismiss_user()` — the same road as §7.6 —
	 *   because it is `webtransport.c` that knows which sessions belong to that
	 *   user.  ⛔ It sends ALL of them away, and that is right here: if we got
	 *   to this branch, that user has no stage, so **none** of their sessions
	 *   is seeing a pixel.  Nothing is being taken away from anyone.
	 *
	 * ⛔ WHAT THIS CURE DOES NOT CURE: the reason is `0x0E`
	 *    (`SESSION_UNSERVABLE`) and **not** `0x06` (`BUDGET_FULL`), and it
	 *    is a choice.  `0x06` says *«this machine has no composition capacity
	 *    left»*, that is a **physical** limit; here the limit is a `#define`
	 *    — a table full of stages **nobody is watching** — that is an
	 *    **administrative** limit, which is exactly what `0x0E` already says
	 *    for the slot table.  ⭐ `phases/10-…md` §8.1 D5: the two reasons are
	 *    ADDED, they do not replace each other, and `0x06` belongs to the
	 *    budget's round. */
	if (without_stage[0]) {
		size_t how_many = wt_dismiss_user(user, no_reason, without_stage, NULL);
		registro_dice(REG_WT,
		              "⛔ sent away %zu clients of «%s» with %#04x: %s.  ⚠ If here "
		              "you read ZERO, the no reached NOBODY and the user "
		              "is in front of a black page — it is defect P3, not its "
		              "cure",
		              how_many, user, no_reason, without_stage);
	}
}

/* ⛔⭐ THE FRAME THAT ARRIVES FROM THE STAGE, AND WHERE IT ENDS UP.
 *
 *     Until phase 2 it ended up in a PROCESS DEPOT — one copy per codec, with
 *     an OWNER — and the box that stood here declared the price: «two users
 *     connected together cannot both see their own desktop; the real cure is a
 *     depot **per session** in `webtransport.c`».
 *
 * ⭐ THE REAL CURE HAS BEEN DONE, and it is better than a depot per session:
 *    there is no depot any more.  The child captures continuously and every
 *    frame is delivered **at once** to that user's sessions —
 *    `wt_video_broadcast()` compares the name of the user who captured with the
 *    one PAM admitted on each session, and they are two different facts both
 *    asked of whoever knows them.
 *
 * ⛔ So the guard of invariant I3 has not disappeared: it has moved to where
 *    it was needed.  The defect measured on 12 Aug 2026 — «prova» receiving
 *    «nicfio»'s desktop — is no longer possible because there is no longer any
 *    place where a user's pixels wait for just any session.
 *
 * ⚠ And the price declared back then is PAID: two users connected together
 *   each see their own, and neither has to log in again.  ⭐ It is worth
 *   writing down, because it was the defect the document called «ugly and not
 *   curable here». */
static void deposit_frame(void *ctx, const char *user, uid_t uid,
                                uint8_t codec, bool key, const uint8_t *data,
                                size_t byte, uint32_t width,
                                uint32_t height, uint64_t instant_us,
                                uint32_t input)
{
	(void)ctx;
	(void)uid;
	/* ⭐⭐ PHASE 4 — AND HERE `input` IS NO LONGER ZERO.
	 *
	 * ⚠ This line said: «`input` is 0 … when input arrives (phase 5) its
	 *   identifier will pass here».  ⛔ Two things were wrong: the phase is
	 *   **4**, and above all the number **is not born here**.
	 *
	 * ⛔ It is stamped BY THE CHILD, at the instant of capture, and arrives here
	 *    inside the frame.  The parent knows what it has **sent** to the
	 *    stage; only the child knows what the compositor has **taken** and
	 *    when it captured.  ⇒ Filling it here would say «the last input sent
	 *    before the sending», a higher number: and the delay ring
	 *    (`DECISIONS.md` §2.6) would measure a delay shorter than the truth, in
	 *    our favour.  `CODER.md` §1-bis: the boundary moves in the
	 *    **uncomfortable** direction.
	 * ⚠ And zero stays legitimate: §6.2 reserves it for «none», and it is what
	 *   applies until the client has opened its input channel. */
	/* ⛔⭐⭐ AND THE BUDGET PASSES HERE TOO — phase 10, 25 Aug 2026, and the
	 *      line sits BEFORE the broadcast on purpose.
	 *
	 *     ⭐ This is the only point of the program where **every** frame of
	 *     **every** stage passes with width, height and instant: it is exactly
	 *     the accumulator the budget needed, and that is why no new channel
	 *     between parent and child was needed (§6.9 point 5).
	 *
	 * ⛔⛔ AND THERE IS NO GUARD ON «SOMEONE IS WATCHING», and that is the
	 *      point: the child calls this function even when no session is
	 *      attached (§3.2, the *ghost*).  Those pixels **were really composed
	 *      and encoded**, so they really cost — and a budget that skipped them
	 *      would underestimate precisely in the scene where the machine is
	 *      struggling.
	 * ⚠ Before `wt_video_broadcast()` because the cost belongs to the STAGE and
	 *   not to the connection: if it were counted only for the frames that
	 *   find a recipient, the network would be counted instead of the GPU. */
	budget_deposit(user, width, height, instant_us);

	wt_video_broadcast(user, codec, key, data, byte, width, height,
	                  instant_us, input);
}

/* ⭐⭐ THE CURSOR SHAPE, from the stage to the wire — the third pipe that
 *     crosses the process boundary, and the only one that crosses it **the
 *     other way round**.
 *
 * ⛔ The cursor metadata arrives from PipeWire, that is in the child; the
 *    `CURSOR_SHAPE` channel (`RCP.md` §7.2) lives in the parent.  ⚠ And the
 *    POSITION does not travel: it belongs to the client, which draws the
 *    pointer itself — only the shape passes here, and the delay of one network
 *    round trip on the shape is the accepted compromise (`DECISIONS.md`
 *    §5-bis.4). */
static void cursor_from_stage(void *ctx, const char *user, uid_t uid,
                              uint16_t width, uint16_t height,
                              int16_t hot_x, int16_t hot_y,
                              const uint8_t *bitmap, size_t byte)
{
	(void)ctx;
	(void)uid;
	wt_cursor_broadcast(user, width, height, hot_x, hot_y, bitmap,
	                    byte);
}

/* ⛔⭐ THE SEAM BETWEEN THE REQUESTED KEYFRAME AND THE ENCODER — point 4 of
 *     phase 3, and it crosses TWO module boundaries and one process boundary.
 *
 *     Who knows a keyframe is needed: `rcp.c` (§5.2 — first after `SESSION`,
 *     canvas changed, the client's `REQUEST_KEY`, delta abandoned).
 *     Who knows which session it belongs to: `webtransport.c`.
 *     Who has the encoder: the CHILD, which is another process.
 *     ⇒ `main.c` is the only one that knows all three, and decides nothing: it
 *     passes it on.
 *
 * ⚠ Without this line, `rcp_video_needs_key()` stayed READ and useless and
 *   `codificatore_chiedi_chiave()` had **no caller in the product**: the
 *   symptom was «the desktop freezes and never restarts», and it named neither
 *   the keyframe nor the encoder.
 *
 * ⛔⭐ AND THREE FACTS OF THE SESSION PASS HERE, not one: the codec, the
 *     DEPTH (17 Aug 2026) and from tonight the LEVEL (§4.3 line 701).
 *     ⚠ All three belong to the CLIENT and not to the server — they change from
 *     session to session — and that is the reason they travel this way and not
 *     on the child's command line, which the child reads once at birth. */
static void video_ask(void *ctx, const char *user, uint8_t codec,
                         uint8_t depth, uint8_t livello_x10, bool key)
{
	struct bridge *p = (struct bridge *)ctx;
	if (!p || !p->f)
		return;
	children_video(p->f, user, codec, depth, livello_x10, key);
}

/* ⭐⭐ THE AUDIO SEAM — phase 7, and it is the third of the same family.
 *
 *     Who knows a session has negotiated an audio codec: `rcp.c` (§4.3).
 *     Who knows which session it belongs to: `webtransport.c`.
 *     ⛔ Who has PipeWire: the CHILD, which runs as the user — another process.
 *     ⇒ `main.c` is the only one that knows all three, and **decides nothing**.
 */
static void audio_ask(void *ctx, const char *user, uint8_t codec)
{
	struct bridge *p = (struct bridge *)ctx;
	if (!p || !p->f)
		return;
	children_audio(p->f, user, codec);
}

/* The way back: an already encoded block, from the session to the wire.
 *
 * ⛔ And here NOTHING is checked and nothing is chosen: the I3 guard — that the
 *    user who PRODUCED the sound is the one PAM admitted on that session —
 *    sits inside `wt_audio_broadcast`, next to the pixels' one.
 *    ⚠ Redoing it here would mean two places saying the same thing, and one
 *    day one of the two would say it differently. */
static void audio_block(void *ctx, const char *user, uid_t uid, uint8_t codec,
                         uint64_t instant_us, const uint8_t *data, size_t byte)
{
	(void)ctx;
	(void)uid;
	wt_audio_broadcast(user, codec, instant_us, data, byte);
}

/* ⭐⭐ THE CLIPBOARD SEAM — phase 7, and it is the FOURTH of the same family
 *     (video, input, audio, clipboard).
 *
 *     Who knows a session has negotiated `clipboard.text`: `rcp.c` (§4.3).
 *     Who knows which session it belongs to: `webtransport.c`.
 *     ⛔ Who talks to the compositor: the CHILD — the clipboard is Mutter's
 *        (`STUDIES.md` §gnome §10), and Mutter talks to the user's session.
 *     ⇒ `main.c` is the only one that knows all three, and **decides nothing**.
 */
static bool clipboard_offer_to_child(void *ctx, const char *user)
{
	struct bridge *p = (struct bridge *)ctx;
	if (!p || !p->f)
		return false;
	return children_clipboard_offer(p->f, user);
}

static bool clipboard_response_to_child(void *ctx, const char *user,
                                       uint32_t serial, const char *text,
                                       size_t byte)
{
	struct bridge *p = (struct bridge *)ctx;
	if (!p || !p->f)
		return false;
	return children_clipboard_response(p->f, user, serial, text, byte);
}

/* The two ways back, from the desktop to the wire.
 *
 * ⛔ And here too NOTHING is checked: the I3 guard — that the text goes to the
 *    connection of WHOEVER copied it — sits inside `webtransport.c`, next to
 *    the pixels' one and the sound's one. */
static void clipboard_from_session(void *ctx, const char *user, uid_t uid,
                                   const char *text, size_t byte)
{
	(void)ctx;
	(void)uid;
	wt_clipboard_from_session(user, text, byte);
}

static void clipboard_request_from_session(void *ctx, const char *user,
                                             uid_t uid, uint32_t serial)
{
	struct bridge *p = (struct bridge *)ctx;

	(void)uid;
	/* ⛔⛔ AND IF THERE IS NOBODY TO ASK, THE ANSWER GOES OUT AT ONCE, empty-
	 *      handed.  The child has a timeout that would cover it anyway,
	 *      ⚠ but here the answer is ALREADY known: making whoever pastes wait
	 *      four seconds when the answer is certain is a desktop that looks
	 *      frozen for something we had understood at once. */
	if (wt_clipboard_request(user, serial))
		return;
	if (p && p->f)
		children_clipboard_response(p->f, user, serial, NULL, 0);
}

/* ⭐⭐ THE INPUT SEAM — phase 4, and it is the twin of the one above.
 *
 *     Who knows the user has pressed: `rcp.c`, which has validated the message
 *     according to `RCP.md` §7.3 — ranges, surrogates, coordinates on the
 *     canvas, increasing `id`.
 *     Who knows which session it belongs to: `webtransport.c`.
 *     ⛔ Who can really inject it: the CHILD, which runs as the user and is the
 *     only one with the graphical session — that is, another process.
 *     ⇒ `main.c` is the only one that knows all three, and **decides
 *       nothing**: it passes it on.
 *
 * ⛔ AND THIS LINE IS THE REASON PHASE 4 EXISTS.  Without it, all the rest
 *    would be written and not connected: `rcp.c` would validate the messages,
 *    `input.c` would know how to inject, and not one byte would pass between
 *    the two — which is exactly the form of defect phase 3 paid for twice (the
 *    keyframe requested without a caller, and the captured monitor that was
 *    not the one the shell was on).  ⚠ Seams have no owner, and that is why
 *    no bench looks at them: this one has one. */
/* ⛔⛔⭐ THE THIRD CLOCK OF §5.3, AND IT IS NO LONGER THE SIX-HOUR ONE.
 *
 *     ✅ Decided by the user on 16 Aug 2026, on measurements taken for the
 *     purpose:
 *
 *       > *«no 6-hour timeout: if after 60 minutes there is no trace of
 *       > input the session gets killed»*
 *
 *     `SPECS.md` §5.3 said «6 hours without any attach ⇒ the session
 *     closes».  ⚠ TWO things change, not one: the ceiling (6 hours → 60
 *     minutes) and **the criterion** — no longer «nobody has attached», but
 *     «nobody has touched anything».
 *
 * ⭐ And the decision came from a number, not from an idea: `[M]` an abandoned
 *    session costs **477 MB** (PSS) and **~0.017 % of a core**, and in four
 *    minutes of observation it does not grow by one megabyte — 477 · 476 · 476
 *    · 477 · 477 · 477 · 477 · 477 · 477.  ⇒ It is not a leak, it is a fixed
 *    cost; and the user chose not to pay it for one hour instead of six.
 *
 * ⛔ WHAT COUNTS AS «INPUT», and the distinction is all here: the five real
 *    gestures.  ⚠ NOT the release at detach (§7.3), which arrives precisely
 *    when the user leaves and would reset the clock at the wrong instant; not
 *    the canvas resize, which starts on its own at reattach; not the request
 *    to log out.
 *
 * ⚠ And resetting the clock at reattach too was considered — and DISCARDED,
 *   with the user: *«your hypothesis implies that the user does not make even
 *   one mouse click in 10 minutes, rather unlikely»*.  ⇒ Only input counts,
 *   which is also the simplest rule to explain. */
#define DEFAULT_ABANDON_MS 3600000u /* 60 minutes */
static uint64_t abandon_ms = DEFAULT_ABANDON_MS;
/* ⛔ The phase 7 test tone: `0` = off, and it is the value of every normal
 *    installation (invariant I6). */
static uint32_t audio_test_hz;

/* ⛔⭐⭐⭐ THE PHASE 9 SWITCHES — AND ON 24 AUG 2026 THEY WERE FLIPPED.
 *
 *      **The user's decision**: *«the product changes for the better; this
 *      phase was to make remotix work more solidly on degraded networks,
 *      without expecting miracles»*.  ⇒ The five cures of phase 9 are born
 *      ON, and each one can still be turned off with ONE road only.
 *
 * ⛔ WHY THEY WERE OFF BEFORE, and it is not bureaucracy: invariant I6 — *what
 *    changes what the user SEES stays behind a switch that is off until they
 *    have looked at it*.  ⚠ In v1 an entire phase was WIPED OUT for having
 *    delivered improvements the director had never seen.
 * ⭐ AND NOW THE PREREQUISITE IS MET: the user has looked (§19.6, §20.3) and
 *    has decided.  ⇒ I6 is not bypassed, it has been walked to the end — the
 *    switch is still there, it is just flipped the other way.
 *
 * ⛔⛔ AND THE SWITCH'S NAME MATTERS.  With the default on, an option that
 *      means «turn on» means nothing, and an option that does nothing is
 *      worse than an option that does not exist (whoever types it believes
 *      they have tuned something).  ⇒ Each switch names its opposite —
 *      `--no-adaptive-rate`, `--no-dead-line`, `--no-audio-silence`.
 *
 * ⛔ ONE ROAD ONLY FOR EACH CURE: two ways of turning on the same thing are two
 *    numbers that diverge, and it is the reason the bridge via the environment
 *    has already been removed once (23 Aug 2026) and the reason the `-D`
 *    `AUDIO_SILENZIO_PREDEFINITO` was removed today.
 *
 *      Until 23 Aug 2026 the cures existed but **nobody called them**: a
 *      switch that cannot be turned on is not a switch, it is dead code — and
 *      phase 9 could measure neither the before nor the after.
 *
 * ⛔ AND TWO OF THE THREE DO NOT LIVE HERE.  The video queue threshold belongs
 *    to the transport, which is in this process; quality rise and the
 *    bandwidth ceiling belong to the **encoder**, which is in the CHILD —
 *    another program, born with `execve` and an environment built from
 *    scratch.  ⇒ They are not passed with an environment variable (it would
 *    not arrive): they are passed on the child's command line, like
 *    `--verbose` (`child.c`, the box in `become_and_exec()`), and
 *    `children_phase9()` is the door. */
/* ⭐ ON by default at 100 ms (⚠ the number is in `webtransport.h`, single copy).
 * ⚠ THE PRICE, `[M]` 09-b79 23-24 Aug 2026: together with the rate regulator,
 *   up to **+160 ms** of drift on a bad network, and **zero** on the healthy
 *   line — 39.85 / 40.19 / 39.63 frames/s in the three arms, **zero
 *   keyframes** in all three.  ⛔ It is turned off with `--clear-threshold-ms 0`. */
static uint64_t clear_threshold_ms = WT_CLEAR_THRESHOLD_MS;
/* ⚠ These two are NOT among the five that are turned on: they stay off (I6),
 *   because the user has not looked at them yet. */
static bool quality_recovery;         /* --quality-recovery, absent = off */
static uint32_t bandwidth_cap_mbit;   /* --bandwidth-cap-mbit, 0 = off    */
/* ⛔⭐ The FOURTH, and it is the only one that lives in the TRANSPORT like the
 *     first: the rate is decided by whoever sees the output queue.  ⚠ And it
 *     depends on the first — with `--clear-threshold-ms 0` it never triggers,
 *     and the server WRITES it at startup instead of letting a dead link be
 *     measured (`webtransport.c`, `wt_adaptive_rate()`).  ⭐ With the defaults
 *     both are born on, which is the only combination in which this regulator
 *     measures anything.
 * ⚠ THE PRICE is the same as the threshold's, and it is written above: the two
 *   cures were measured together and do not have two separate prices. */
static bool adaptive_rate = true;  /* ⭐ on; --no-adaptive-rate turns off */
/* ⛔⭐⭐ AND THE FIFTH, which is of another kind: the other four change HOW
 *      WELL one sees, this one decides whether the session still EXISTS.
 *      The user's decision of 23 Aug 2026: a line that loses in bursts is not
 *      served, it is declared dead — the wire drops and one gets back in by
 *      hand.
 * ⛔ The two numbers start from the defaults of `webtransport.h`, which are the
 *    only copy; the options needs the bench, which must be able to move them
 *    without recompiling.
 * ⚠⚠ THE PRICE, AND IT IS THE DEAREST OF THE FIVE — `[M]` 23-24 Aug 2026:
 *    margin **>10×** above `casa-cattiva`, the WORST line that holds (ten
 *    minutes, maximum stall < 500 ms, zero triggers), and **2.9×** below the
 *    14.26 s of `raffica-forte`, which serves nobody.  ⛔ IT IS THE CURE THAT
 *    CLOSES A SESSION: if the threshold were badly tuned it would throw out
 *    whoever is working.  ⇒ Whoever touches `WT_LM_STALL_MS` measures those
 *    two margins again, or delivers a product that disconnects people for a
 *    number nobody has verified. */
static bool dead_line = true;     /* ⭐ on; --no-dead-line turns off */
static uint64_t dead_line_stall_ms = WT_LM_STALL_MS;
static uint64_t dead_line_silence_s = WT_LM_SILENCE_S;
/* ⛔⭐⭐ AND THE LAST OF THE FIVE THAT ARE TURNED ON, and it is of yet another
 *      kind: it does not touch the video, it touches the AUDIO.  A block in
 *      which **all** the samples are exactly zero does not become a datagram.
 *
 * ⛔ IT DOES NOT LIVE HERE, and it does not even live in one place: the real
 *    encoder is in the CHILD (`children_phase9()`), but `--audio-test` opens one
 *    in THIS process too (`webtransport.c`).  ⇒ The value is handed to both,
 *    from the same `bool`, or the two benches would measure two different
 *    products.
 * ⚠ `[M]` 24 Aug 2026, 09-b84: **102.1 times** less traffic with a still
 *   screen (557.6 → 5.5 kbit/s), pure test tone **1.000**, coverage
 *   **0.9996**, **1 248 blocks silenced out of 1 248**.  ⚠ The price: the
 *   client's `missed` rise by **2 out of 5 000** — an INTENDED hole leaves
 *   the same `instant` jump as a lost one.
 * ⛔ Until 23 August the switch was a COMPILE-TIME one
 *    (`-DAUDIO_SILENZIO_PREDEFINITO=1`), and that `-D` has been removed: one
 *    road only. */
static bool audio_silence = true;  /* ⭐ on; --no-audio-silence turns off */

/* ⛔⭐⭐⭐ PHASE 10 — THE BUDGET, AND ITS THREE KNOBS (25 Aug 2026).
 *
 *     They are THREE because they are THREE QUANTITIES, and mixing them is the
 *     defect the phase went to cure:
 *
 *       `--budget-mpixel-s`  the **PHYSICAL** limit: how many Mpixel/s of
 *                            COMPOSITION this machine declares it holds.
 *                            ⛔ `0` = OFF, and it is the default (I6).
 *       `--session-cap`   the **ADMINISTRATIVE** cap of §4.6, and the four
 *                            tables are sized from it.  Default 10
 *                            (`SPECS.md` §5.5).
 *       `--reserve`          the rule's knob: how much of the worst case of an
 *                            **idle** tenant is kept aside.  Default 0.5,
 *                            `[M]` §6.9.
 *
 * ⛔ Each one declares in the startup line the value in force, ON AND OFF —
 *    the same rule as the five cures of phase 9, and for the same reason: two
 *    ways of knowing whether a thing is in force are two numbers that diverge.
 * ⛔⛔ AND `--budget-mpixel-s` DOES NOT SELF-TUNE: `[M]` §6.9 — before the
 *      machine has given way **once**, the capacity read is a **lower bound,
 *      not a ceiling**.  ⇒ Either it is given, or there is no budget: a
 *      product that deduced its own ceiling would refuse users for a number
 *      nobody has verified. */
static double budget_mpixel_s;                        /* 0 = OFF (I6) */
static double budget_reserve = BUDGET_DEFAULT_RESERVE;
static int session_cap = RCP_SESSION_CAP;

/* ⛔ One per user, and not per RCP session: the clock MUST survive the client
 *    that leaves — it is precisely the case it exists for.
 * ⭐ And the number comes from `rcp.h` (`RCP_SESSION_CAP`), 25 Aug 2026: it
 *    was the fourth hand-made copy of the same 16, the only one that did not
 *    even declare a link.  ⛔ More users than slots in the session registry
 *    cannot exist, so this table cannot overflow **as long as the two numbers
 *    stay the same**: the box in `rcp.h` is what guarantees it, and the
 *    fallback below is the net if someone unties them. */
/* ⭐⭐ And since the evening of 25 Aug 2026 it is **allocated** on
 *     `rcp_cap()`, which `--session-cap` moves at startup: the
 *     `QUANTI_PRESENTI` that stood here is gone, and was not left alongside as
 *     a «maximum» — it would have been a second number, that is the second
 *     road of `CODER.md` §2-bis. */
static struct is_present {
	char user[257];
	uint64_t last_input_ms;
} *present;
static int how_many_present;

/* ⛔ It is allocated at the first presence to record, once only.  ⚠ If the
 *    memory is not there, the fallback this table already declares further
 *    down applies: the users have no abandonment clock, and it is written. */
static bool present_ready(void)
{
	if (present)
		return true;
	how_many_present = rcp_cap();
	present = (struct is_present *)calloc((size_t)how_many_present,
	                                     sizeof *present);
	if (!present) {
		how_many_present = 0;
		return false;
	}
	return true;
}

/* ⭐ «A gesture happened here just now.»  If the user is not in the table they
 *    are added: the first gesture is also the first sign of presence. */
static void presence_mark(const char *user, uint64_t now_ms)
{
	int free_slot = -1;
	if (!user || !user[0])
		return;
	if (!present_ready()) {
		/* ⛔ Declared fallback: without a table there is no clock, and the
		 *    case is the same as the full table below. */
		static bool no_table_logged;

		if (!no_table_logged) {
			no_table_logged = true;
			registro_dice(LOG_CHILD,
			              "⚠ DECLARED FALLBACK: there is no memory for the "
			              "presence table: NO graphical session "
			              "will expire by abandonment");
		}
		return;
	}
	for (int i = 0; i < how_many_present; i++) {
		if (present[i].user[0] == '\0') {
			if (free_slot < 0)
				free_slot = i;
			continue;
		}
		if (strcmp(present[i].user, user) == 0) {
			present[i].last_input_ms = now_ms;
			return;
		}
	}
	if (free_slot < 0) {
		/* ⛔⭐ THE FALLBACK IS DECLARED — `CODER.md` §4.2, 25 Aug 2026.
		 *
		 *     Here there was a MUTE `return`.  The cost: the seventeenth user
		 *     had no abandonment clock, so their graphical session **would
		 *     never have expired at 60 minutes** — and no line said so.  ⚠ The
		 *     symptom, an hour later, is «that user's stage stays alive
		 *     forever», which nobody connects to this line.
		 *
		 * ⚠ Once only and not once per gesture: we pass here at every mouse
		 *   movement, and it is the defect of the 30.8 GB of log.  ⛔ The fact
		 *   is not «it happened again»: it is «from now on there is a user
		 *   without a clock», and it is said when it starts. */
		static bool attendees_full_logged;

		if (!attendees_full_logged) {
			attendees_full_logged = true;
			registro_dice(LOG_CHILD,
			              "⚠ DECLARED FALLBACK: the presence table is "
			              "full (%d): «%s» does not fit, and their graphical "
			              "session will NOT expire by abandonment.  ⛔ If this "
			              "line exists, the caps of rcp.h and of main.c have come "
			              "untied: it should not be able to happen",
			              how_many_present, user);
		}
		return;
	}
	snprintf(present[free_slot].user, sizeof present[free_slot].user, "%s",
	         user);
	present[free_slot].last_input_ms = now_ms;
}

static void presence_forget(const char *user)
{
	if (!user)
		return;
	for (int i = 0; i < how_many_present; i++)
		if (strcmp(present[i].user, user) == 0)
			present[i].user[0] = '\0';
}

static bool input_to_child(void *ctx, const char *user, uint32_t id,
                            uint8_t action, uint16_t code, int pressed,
                            int32_t a, int32_t b)
{
	struct bridge *p = (struct bridge *)ctx;
	if (!p || !p->f)
		return false;
	/* ⛔ ONLY the five real gestures: the reason is in the box above. */
	if (action == CHILDREN_INPUT_POINTER || action == CHILDREN_INPUT_BUTTON ||
	    action == CHILDREN_INPUT_WHEEL || action == CHILDREN_INPUT_LETTER ||
	    action == CHILDREN_INPUT_POSITION)
		presence_mark(user, log_now_ms());
	return children_input(p->f, user, id, action, code, pressed, a, b);
}

/* ⭐⭐ THE CANVAS SEAM — and it closes the chain that the mandate of phase 4
 *     called by name: `children_recanvas()` → `capture_resize()`.
 *
 *     Who knows the user has asked for another size: `rcp.c`, which has
 *     applied §7.1 and `rcp_size_allowed()` — range, parity, and the ceiling
 *     that keeps the host's compositor alive.
 *     Who knows which session it belongs to: `webtransport.c`.
 *     ⛔ Who can really change it: the CHILD, which has the PipeWire stream.
 *     ⇒ `main.c` is the only one that knows all three, and **decides nothing**.
 *
 * ⛔ And this line is worth four symptoms, not one (`DECISIONS.md`
 *    §5.0-sexies): the black side bands, the interpolated text, the reattach
 *    at a different size, and ⭐ **the four seconds between login and
 *    desktop** — because `pw_stream_update_params()` is a restart of the
 *    stream, and a restart delivers a buffer even with a still scene. */
/*
 * ⭐⭐ §7.6 of `RCP.md` — «THE USER HAS ASKED TO LOG OUT».
 *
 * ⛔ TWO THINGS, AND IN THIS ORDER:
 *
 *   1. **that user's other clients** are sent away with `0x10`.  The graphical
 *      session is ONE (I2): whoever was watching it from a second device would
 *      be left with a frozen screen forever, and no line would tell them why.
 *      ⚠ Whoever asked has already been sent away by `rcp.c`, and indeed is
 *      skipped (`except`);
 *   2. **then** the child is asked to end the session.
 *
 * ⛔ The order is normative and not a preference: when the compositor falls,
 *    the stage falls with it and the channels are no longer needed.  A `0x10`
 *    sent afterwards is a reason that exists and that nobody receives —
 *    finding B-7 under a new name.
 */
static void terminate_in_child(void *ctx, const char *user)
{
	struct bridge *p = (struct bridge *)ctx;
	size_t others;

	if (!p || !p->f || !user)
		return;

	others = wt_dismiss_user(user, RCP_SESSION_TERMINATED,
	                          "another client of this user has closed the "
	                          "session", NULL);
	if (others)
		registro_dice(REG_WT,
		              "⭐ §7.6: also sent away with 0x10 %zu other clients of «%s» "
		              "— the graphical session is one only (I2), and whoever was "
		              "watching it must know now, not in thirty seconds",
		              others, user);

	if (!children_terminate_session(p->f, user, CHILDREN_EXIT_USER))
		registro_dice(LOG_STARTUP,
		              "⛔ §7.6: the request to end the session of «%s» did NOT "
		              "leave towards the child: the clients have been sent away "
		              "with 0x10 and the desktop is still there.  ⚠ Two truths about the "
		              "same fact, and this line is the only place where it shows",
		              user);
}

/* ⛔⛔⭐ §5.3 — ABANDONMENT EXPIRES, and the session closes.
 *
 *     ⚠ And the order is the SAME as §7.6 and for the same normative reason:
 *     first whoever is watching is told WHY, then it closes.  When the
 *     compositor falls the stage falls with it, and a reason sent afterwards
 *     is a reason nobody receives (finding B-7).
 *
 * ⭐ And the reason is `0x03 SESSION_ABANDONED`, which §8.2 already had and
 *    which **no line of code had ever sent** — the same form E1 as `0x02`
 *    until this morning.  ⚠ Usually nobody will receive it: if the clock
 *    expires it is because nobody was there any more.  But «usually» is not
 *    «never», and whoever is there must read a sentence instead of looking at
 *    a frozen screen. */
static void abandon_expired(struct bridge *p, const char *user,
                              uint64_t stalled_ms)
{
	size_t amount;

	registro_dice(LOG_STARTUP,
	              "⭐ §5.3 — ABANDONMENT: «%s» has touched nothing for %llu ms (ceiling "
	              "%llu).  ⛔ I CLOSE the graphical session, and with it its "
	              "programs: it is the user's decision of 16 Aug 2026, "
	              "«if after 60 minutes there is no trace of input the session "
	              "gets killed»",
	              user, (unsigned long long)stalled_ms,
	              (unsigned long long)abandon_ms);

	amount = wt_dismiss_user(user, RCP_SESSION_ABANDONED,
	                           "session abandoned: no input within the "
	                           "ceiling of §5.3",
	                           NULL);
	if (amount)
		registro_dice(REG_WT,
		              "⚠ §5.3: there were STILL %zu clients attached to «%s», "
		              "sent away with 0x03 before closing — they were watching without "
		              "touching anything for %llu ms (ceiling %llu).  ⛔ And the number is "
		              "WRITTEN instead of saying it in words: the ceiling is configurable, "
		              "and «one hour» would be true only with the default value",
		              amount, user, (unsigned long long)stalled_ms,
		              (unsigned long long)abandon_ms);

	/* ⭐ PHASE 17 T7 — a desktop FOUND AGAIN has no child: nobody to ask to
	 *    close it.  ⇒ One is spawned (D1: the child is remade), which sits in
	 *    the user's session bus and knows how to close every desktop
	 *    (`session_terminate()`); the request below waits for it in its socket.
	 *    ⚠ The parent does not close it by itself: as root and outside the bus
	 *    it would only know how to kill, and desktops are closed, not killed. */
	if (children_pid_of(p->f, user) <= 0 && found_again_of(user)) {
		registro_dice(LOG_STARTUP,
		              "⭐ PHASE 17 T7: «%s» has a desktop FOUND AGAIN and no "
		              "child — I spawn one to close it",
		              user);
		if (children_ensure(p->f, user))
			found_again_remove(user);
	}
	if (!children_terminate_session(p->f, user, CHILDREN_EXIT_ABANDON))
		registro_dice(LOG_STARTUP,
		              "⛔ §5.3: the request to close the abandoned session "
		              "of «%s» did NOT leave towards the child: the clients have "
		              "been sent away with 0x03 and the desktop is still there",
		              user);
	/* ⛔ It is forgotten ANYWAY: if the closing did not go through, retrying at
	 *    every round would fill the log with one line per second for a fault
	 *    the first line has already reported.  ⚠ And if a new session is born,
	 *    its first gesture will put it back in the table. */
	presence_forget(user);
}

/* ⭐ The clock's round.  ⚠ Called at every pass of the loop: it costs nothing
 *    (sixteen comparisons) and an expiry that waits for an event is an expiry
 *    that never triggers — the lesson of `rule_heartbeat`. */
static void abandon_round(struct bridge *p, uint64_t now_ms)
{
	if (!abandon_ms || !p || !p->f)
		return;
	for (int i = 0; i < how_many_present; i++) {
		if (present[i].user[0] == '\0')
			continue;
		if (now_ms <= present[i].last_input_ms)
			continue;
		if (now_ms - present[i].last_input_ms > abandon_ms) {
			/* ⛔ A COPY, not the pointer: `abandon_expired()` ends up
			 *    calling `presence_forget()`, which zeroes precisely that
			 *    slot — and the name is needed until the last line.
			 * ⚠ `memcpy` and not `snprintf`: the source has the same size as
			 *   the destination, and the compiler cannot know it. */
			char chi[sizeof present[0].user];
			memcpy(chi, present[i].user, sizeof chi);
			chi[sizeof chi - 1] = '\0';
			abandon_expired(p, chi, now_ms - present[i].last_input_ms);
		}
	}
}

/*
 * ⭐ §7.6, the twin: the graphical session has ended and no client asked for
 *    it — the user logged out from the desktop menu.
 *
 * ⛔ Whoever is watching is sent away with `0x10` NOW.  Staying silent, they
 *    would be left on a frozen screen until the thirty seconds of silence and
 *    then read «network error»: it is finding B-7, and this is the line that
 *    prevents it.
 */
static void session_ended_by_child(void *ctx, const char *user, uid_t uid)
{
	size_t amount;

	(void)ctx;
	(void)uid;
	amount = wt_dismiss_user(user, RCP_SESSION_TERMINATED,
	                           "the graphical session has ended", NULL);
	registro_dice(REG_WT,
	              "⭐ §7.6: the session of «%s» was ended from the desktop — sent away "
	              "%zu clients with 0x10 (⚠ zero is normal: nobody may be "
	              "watching)",
	              user, amount);
}

/* ⭐ §7.1: the stage is not there yet — the bottom is postponed instead of
 *    answering `NOT_NOW` to a question that is about to have a real answer. */
static void canvas_wait_for_child(void *ctx, const char *user, uid_t uid,
                                    uint32_t intended_w, uint32_t intended_h)
{
	(void)ctx;
	(void)uid;
	wt_canvas_resend(user, intended_w, intended_h);
}

/* ⭐ §5-bis.7 — and it delegates to `children_layout()` as
 *    `recanvas_to_child()` delegates to `children_recanvas()`: this file is the
 *    bridge, not the rule. */
static bool layout_to_child(void *ctx, const char *user,
                                   const char *name)
{
	struct bridge *p = (struct bridge *)ctx;
	if (!p || !p->f)
		return false;
	return children_layout(p->f, user, name);
}

static bool recanvas_to_child(void *ctx, const char *user, uint32_t width,
                             uint32_t height)
{
	struct bridge *p = (struct bridge *)ctx;
	if (!p || !p->f)
		return false;
	return children_recanvas(p->f, user, width, height);
}

/* ⛔ The child has gone.  ⚠ There is no longer any depot to empty — it was
 * the cure of phase 2 — but the line stays because the fact is a fact: from
 * now on that user no longer has a stage, and their sessions will no longer
 * see frames arrive.  ⛔ And NOTHING is closed: `SPECS.md` §8.3, «never
 * disconnect» — a session without frames is worth more than a closed session. */
static void dismiss_child(void *ctx, const char *user, uid_t uid)
{
	(void)ctx;
	registro_dice(REG_VIDEO,
	              "⛔ the stage of «%s» (uid %ld) has gone: from now on their "
	              "sessions no longer receive frames.  ⚠ NOTHING is "
	              "closed (I1, SPECS.md §8.3): a still session is worth more "
	              "than a disconnected session, and the stage can be born again",
	              user, (long)uid);
	/* ⛔⭐ AND THE SIZE OF ITS STAGE IS FORGOTTEN — defect found while refuting,
	 *     the night of 15 Aug 2026: that number serves the REATTACH
	 *     (`SESSION` grants the canvas the stage already has), and a number of
	 *     a dead stage is worse than no number — it makes a canvas be granted
	 *     that no frame will ever have. */
	wt_stage_forget(user);
	/* ⭐ D-004 — and its slot in the presence table: without a stage there is
	 *    nothing to expire, and a slot left behind would make the child be
	 *    asked, an hour later, to close a session that no longer exists (the
	 *    line «⛔ §5.3 … did NOT leave towards the child» for a fault that does not exist).  The
	 *    next stage will reopen it at birth. */
	presence_forget(user);

	/*
	 * ⭐⭐⭐ §7.6, THE TWIN — AND IT LIVES HERE, NOT IN THE CHILD.  Defect found
	 *      by the logout bench, 15 Aug 2026.
	 *
	 * ⛔ The child had the code to notice that the graphical session had ended
	 *    («it was there and now it is gone»), and `[M]` it never triggered:
	 *    **at logout the child dies with signal 15**.  It is the LEADER
	 *    process of the logind session — it opens it with `pam_open_session`
	 *    — and when the session ends it takes it away.  ⇒ It cannot report a
	 *    fact that kills it.
	 *
	 * ⭐ But the parent REAPS it, and it is exactly this line.  ⇒ Child dead =
	 *    graphical session over, always: the stage lives in the child, and so
	 *    does the logind session.
	 *
	 * ⚠ And it holds even if the child died of a fault instead of a choice of
	 *   the user: from here they cannot be told apart, ⛔ and the right
	 *   behaviour is the same — saying it to whoever is watching instead of
	 *   leaving them in front of a frozen screen for the thirty seconds of
	 *   silence, which is finding B-7.  The reason `0x10` says «the session has
	 *   ended», which in both cases is true.
	 *
	 * ⛔ BUT NOT WHEN THE SERVER IS SHUTTING DOWN: there the right reason is
	 *    `0x0C SERVER_CLOSING`, and `main()` sends it to all sessions.
	 *    Saying `0x10` to whoever is about to receive `0x0C` would be telling
	 *    them their session is over when instead they will find it again.
	 */
	if (!stop_requested) {
		size_t amount = wt_dismiss_user(user, RCP_SESSION_TERMINATED,
		                                  "the graphical session has ended",
		                                  NULL);
		if (amount)
			registro_dice(REG_WT,
			              "⭐ §7.6: the stage of «%s» has gone ⇒ the graphical "
			              "session is over: sent away %zu clients with 0x10 instead "
			              "of leaving them on a frozen screen",
			              user, amount);
	}
}

/* ⭐⭐ THE STAGE'S ANSWER ON THE CANVAS — §7.1, and it crosses the boundary in
 *     the cursor's direction: the question went out with `children_recanvas()`,
 *     this comes back in.
 *
 * ⛔ And the parent no longer GUESSES it from the frames: the child says which
 *    request it answers (`intended`) and what the stage really has (`got`, with
 *    `0x0` = it did not make it).  ⚠ Without this, two chained `FIT_CANVAS` —
 *    a user dragging the border — made the frame of the first be taken for the
 *    answer to the second. */
/* ⭐ §5.1 — the adapter between the hook of `webtransport.c` and `sentinel.c`.
 *
 * ⛔ It is here and not there because `webtransport.c` does not know logind and
 *    must not: that module knows **which sessions belong to that user**, this
 *    one knows **whom to ask**.  They are two jobs, and keeping them separate
 *    is what allows the bench to graft a fake guard without touching the
 *    transport. */
static bool ask_local_session(void *ctx, const char *user, char *which,
                                   size_t how_much)
{
	return sentinel_local((sentinel *)ctx, user, which, how_much);
}

/* ⭐⭐ §5.1 — the adapter of the CHECK, and it asks for ALL tenants at once.
 *     The why — `[M]` §6.13, `N × D` that becomes `D` — is written out in full
 *     in `sentinel.h` above `sentinel_locals()`.
 *
 * ⛔ It is a second adapter and not one more parameter on the first because
 *    the two questions have two different jobs: the one above is asked by
 *    `rcp.c` at `ATTACH`, once per session, and there the cost does not show;
 *    this one runs every two seconds **inside the loop that delivers frames**.
 * ⭐ And it stays the bench's lever: the fake guard is grafted HERE, and the
 *    transport is not touched. */
static size_t sweep_local_sessions(void *ctx, const char *const *users,
                                      size_t amount, bool *local, char *which_ones,
                                      size_t width)
{
	return sentinel_locals((sentinel *)ctx, users, amount, local, which_ones,
	                         width);
}

static void canvas_from_stage(void *ctx, const char *user, uid_t uid,
                           uint32_t intended_w, uint32_t intended_h, uint32_t got_w,
                           uint32_t got_h)
{
	(void)ctx;
	(void)uid;
	wt_canvas_from_stage(user, intended_w, intended_h, got_w, got_h);
}

int main(int argc, char **argv)
{
	const char *address = "0.0.0.0";
	const char *name = NULL;
	const char *port = DEFAULT_PORT;
	const char *dir_cert = "/var/lib/remotix/certificates";
	const char *file_html = "page.html";
	const char *file_ban = "/var/lib/remotix/ban";
	const char *socket_command = NULL;
	const char *dir_survey = NULL;
	certificates cert;
	SSL_CTX *ctx_quic = NULL, *ctx_page = NULL;
	transport *t = NULL;
	page *p = NULL;
	command *k = NULL;
	helper *pam_help = NULL;  /* ⚠ not «help»: that name already belongs to the function that prints the usage */
	children *offspring = NULL;
	struct bridge bridge;
	sentinel *guardian = NULL;
	time_t last_cert_check;
	uint64_t last_locals_sweep = 0;
	uint64_t last_guardian_count = 0;
	bool journal_requested = false;   /* --journal, phase 16 §12 */
	int outcome = 1;

	/* ⛔⭐ AND THIS IS THE FIRST LINE OF THE PROGRAM, BEFORE ANYTHING ELSE: if
	 *     we are the child, we are not a server.
	 *
	 *     `children_ensure()` has already brought us down to the user's uid and
	 *     has done `exec` of this same binary (`child.c`, box at the top:
	 *     without `exec` the child would have the server's private TLS key in
	 *     memory, and a process's memory belongs to its owner).
	 *     ⛔ Here nothing is opened, no certificate is read and the ban file is
	 *     not touched: we go straight to `child_alive()`, which does not return. */
	if (argc >= 2 && strcmp(argv[1], "--internal-child") == 0) {
		child_alive(argc, argv);
		return 1; /* never reached */
	}
	/* ⭐ PHASE 17 (§6.5-bis) — the encoding test of the certification: on its
	 *    own, before everything else — no certificates, no network, no
	 *    sessions.  The contract is in `child.h`. */
	if (argc >= 2 && strcmp(argv[1], "--encoding-test") == 0)
		return child_test_encoding(argc - 2, argv + 2);
	/* ⭐ 11 Oct 2026 (`DECISIONS.md` §10.40) — the start line of KWin on
	 *    Plasma: labwc without a screen, then KWin nested in it (`kwin.h`).
	 *    It runs as the USER, inside `plasma-kwin_wayland.service`, and it
	 *    becomes the KWin wrapper: nothing of the server is opened here. */
	if (argc >= 2 && strcmp(argv[1], "--kwin-nested") == 0)
		return kwin_nested_alive(argc, argv);

	for (int i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (strcmp(a, "--address") == 0 && v)
			address = argv[++i];
		else if (strcmp(a, "--name") == 0 && v)
			name = argv[++i];
		else if (strcmp(a, "--port") == 0 && v)
			port = argv[++i];
		else if (strcmp(a, "--certificates") == 0 && v)
			dir_cert = argv[++i];
		else if (strcmp(a, "--page") == 0 && v)
			file_html = argv[++i];
		else if (strcmp(a, "--ban-file") == 0 && v)
			file_ban = argv[++i];
		else if (strcmp(a, "--command-socket") == 0 && v)
			socket_command = argv[++i];
		/* ⭐ PHASE 2 — where to write the captured frame and the two streams.
		 *
		 * ⛔ It serves the pixel-judgement bench (F2.6): without it, the
		 *    comparison between CAPTURED and PAINTED lacks the first of its two
		 *    terms, and the only way to get it would be to capture again with
		 *    another program — that is, comparing the painted one with a
		 *    DIFFERENT frame, taken an instant later.
		 * ⚠ It is off by default: without this option the server does not
		 *   write one byte more than before. */
		else if (strcmp(a, "--survey") == 0 && v)
			dir_survey = argv[++i];
		else if (strcmp(a, "--verbose") == 0)
			log_chatter(true);
		/* ⭐ Phase 16 §12 — the box is in `log.h`.  ⚠ If the socket does
		 *   not open it is said at startup (below) and we go on: the log on
		 *   `stderr` does not depend on the journal. */
		else if (strcmp(a, "--journal") == 0)
			journal_requested = true;
		/* ⛔⭐ §5.3 — the second of the three clocks, and the document wants it
		 *     configurable: *«the second and the third are configurable, with
		 *     those values as defaults»*.
		 *
		 * ⚠ IN SECONDS, not in minutes, and the reason is that a half-hour
		 *   ceiling **cannot be tested** if the minimum is one minute: one
		 *   waits half an hour every time, that is one never tests it.  ⭐ With
		 *   seconds the mechanism is exercised in ten, and the default NUMBER
		 *   can be read in the line the server writes at startup.
		 *
		 * ⛔ `0` = off, and it is an allowed and declared value. */
		else if (strcmp(a, "--inactivity-s") == 0 && v)
			rcp_inactivity_set((uint64_t)strtoull(argv[++i], NULL, 10) * 1000);
		/* ⛔⭐ §5.3, the third: «if after 60 minutes there is no trace of input
		 *     the session gets killed» (the user's decision, 16 Aug 2026).
		 *     ⚠ `0` = off, and then no session is ever closed on its own. */
		else if (strcmp(a, "--abandon-s") == 0 && v)
			abandon_ms = (uint64_t)strtoull(argv[++i], NULL, 10) * 1000;
		/* ⛔⭐⭐ PHASE 9 — GHOST EVICTION, and it sits next to the clocks
		 *      because it belongs to their family, but it is NOT a fourth
		 *      clock: it does not trigger on its own, it triggers only when a
		 *      client of the same user is asking for that slot.
		 *
		 * ⚠ IN MILLISECONDS and not in seconds, and for the opposite reason to
		 *   `--inactivity-s`: here the numbers that matter are below one second
		 *   (how long a live client is silent between two keep-alives) and a
		 *   one-second unit could not express them.
		 *
		 * ⛔ `0` = OFF, and it is the only road to turn it off: since 24 Aug 2026
		 *    the default is ON, 15000 ms (`DEFAULT_EVICTION` in rcp.c, half the
		 *    silence clock), as the help text above says. */
		else if (strcmp(a, "--eviction-ms") == 0 && v)
			rcp_eviction_set((uint64_t)strtoull(argv[++i], NULL, 10));
		/* ⭐ PHASE 19 — the card's route (`DECISIONS.md` §10.27).  It applies to
		 *    the test at startup (in the parent, a fork) and to every child (the
		 *    parent repeats it on its command line).  ⛔ A name that is not one
		 *    of the three is a usage error, not a silent «card». */
		else if (strcmp(a, "--encoding-route") == 0 && v) {
			if (!child_encoding_route(argv[++i])) {
				fprintf(stderr, "⛔ --encoding-route «%s»: expected card, vulkan or vaapi\n",
				        argv[i]);
				return 2;
			}
		}
		/* ⛔⭐ BENCH FUNCTION — phase 7: a test tone in place of the session's
		 *     audio.  ⚠ It serves to test the encoder, the datagram and the
		 *     browser with a signal known **sample by sample**, instead of
		 *     turning on five links and being left with five defendants.
		 *
		 * ⛔ Off unless someone turns it on — invariant I6 — and when it is on
		 *    the server WRITES it in the log at every session. */
		else if (strcmp(a, "--audio-test") == 0 && v)
			audio_test_hz = (uint32_t)strtoul(argv[++i], NULL, 10);
		/* ⛔⭐⭐ THE THREE CURES OF PHASE 9, and they all follow the same rule as
		 *      the three clocks above: the MECHANISM is exercised at short values
		 *      from the command line, the NUMBER in force can be read in the line
		 *      the server (or the child) writes at startup.
		 *
		 * ⚠ In MILLISECONDS and not in frames: the threshold is a delay that
		 *   one SEES, and whoever turns it on chooses how old the picture may be
		 *   for a fraction of a second (`webtransport.h`, the box above
		 *   `wt_clear_threshold`).  ⛔ `0` = off, and it is today's behaviour
		 *   byte for byte. */
		else if (strcmp(a, "--clear-threshold-ms") == 0 && v)
			clear_threshold_ms = (uint64_t)strtoull(argv[++i], NULL, 10);
		/* ⛔ Without an argument, like `--verbose`: it is a yes/no, and a
		 *    number next to it would suggest a calibration that does not exist
		 *    (the three numbers of the rise are in `encoder.c` and the
		 *    bench calibrates them). */
		else if (strcmp(a, "--quality-recovery") == 0)
			quality_recovery = true;
		/* ⛔ The argument is the FLOOR in Mbit/s (20, the one of
		 *    `DECISIONS.md` §3.1-bis), not the ceiling: wire, working point and
		 *    reservoir are derived from it in one place only (`encoder.c`).
		 *    ⚠ `0` = off, and then nobody says no to bandwidth. */
		else if (strcmp(a, "--bandwidth-cap-mbit") == 0 && v)
			bandwidth_cap_mbit = (uint32_t)strtoul(argv[++i], NULL, 10);
		/* ⛔⭐⭐ PHASE 9 — THE RATE REGULATOR.  Without an argument, like
		 *      `--quality-recovery`: it is a yes/no, and a number next to it would
		 *      suggest a calibration that does not live here (the slots are
		 *      `WT_RATE_SLOTS` in `webtransport.c`, and the bench calibrates
		 *      them).
		 *
		 * ⛔ IT WAS BORN OFF (I6) because it changes WHAT ONE SEES: fewer frames
		 *    when the line does not carry.  The user judged it on the real
		 *    desktop (§19.6, §20.3) before it became the normal behaviour — it
		 *    is the lesson paid for with the wiping out of phase 10 of v1.  ⭐ On
		 *    24 Aug 2026 they decided, and now it is born ON: only the opposite
		 *    remains here.
		 *
		 * ⚠⚠ AND IT IS NOT ENOUGH ON ITS OWN: without `--clear-threshold-ms N`
		 *    the delta queue empties at every frame, the backlog does not exceed
		 *    1 and this regulator NEVER triggers.  The server WRITES it at
		 *    startup, so nobody measures a dead link believing it alive.  ⭐ With
		 *    the defaults both are born on, so the dead case must be asked for
		 *    on purpose. */
		else if (strcmp(a, "--no-adaptive-rate") == 0)
			adaptive_rate = false;
		/* ⛔⭐⭐⭐ PHASE 9 — THE DEAD LINE, the user's decision of 23 Aug 2026:
		 *      a line that loses in bursts is not served, it is declared dead —
		 *      the wire drops and the user gets back in by hand.
		 *
		 * ⛔ It is the most visible switch of the product: IT THROWS A SESSION
		 *    OUT.  It was born off (I6) and without discussion: the user looked
		 *    at it on the real desktop (§19.6, §20.3) before it became the
		 *    normal behaviour.  ⭐ On 24 Aug 2026 they decided, and now it is
		 *    born ON: only the opposite remains here.  ⚠ The two numbers have
		 *    one option each because the bench must be able to move them
		 *    without recompiling — and they are the ONLY road, no environment
		 *    variables (the reason is next to `wt_clear_threshold()`: two roads
		 *    are two numbers that diverge).
		 * ⚠ And the two `0` are NOT a second road to turn the cure off: they
		 *   turn off one CAUSE at a time, and the startup line says which one
		 *   remains.  Whoever wants yesterday's product types
		 *   `--no-dead-line`. */
		else if (strcmp(a, "--no-dead-line") == 0)
			dead_line = false;
		/* ⛔⛔ THE LOSS FRACTION IS NOT A CAUSE — 23 Aug 2026: it was refuted
		 *      by its bench (`casa-cattiva` declared 512‰ and HELD for ten
		 *      minutes, `raffica-forte` 123‰ and did not hold: the quantity
		 *      orders the two cases the wrong way round).  ⇒ The number stays
		 *      in the log as a WITNESS of the reordering, with no threshold to
		 *      move: an option that accepts a number without using it is worse
		 *      than an option that does not exist. */
		else if (strcmp(a, "--dead-line-stall-ms") == 0 && v)
			dead_line_stall_ms = strtoull(argv[++i], NULL, 10);
		else if (strcmp(a, "--dead-line-silence-s") == 0 && v)
			dead_line_silence_s = strtoull(argv[++i], NULL, 10);
		/* ⛔⭐⭐ THE FIFTH CURE — THE AUDIO SILENCE, and until 23 Aug 2026 its
		 *      switch was a COMPILE-TIME one (`-DAUDIO_SILENZIO_PREDEFINITO=1`).
		 *
		 * ⛔ The `-D` has been REMOVED, not left alongside: two roads for the
		 *    same cure are two numbers that diverge.  ⚠ Whoever rebuilds
		 *    `09-b84-audio-silenzio.py` must know it — that bench paired two
		 *    binaries with a single `-D` of difference, and now the off arm is
		 *    done with this option, on the SAME binary (which is better: one
		 *    defendant fewer).
		 *
		 * ⚠ Without an argument, like `--verbose`: it is a yes/no, and the
		 *   threshold does not exist on purpose — it stays silent only on
		 *   DIGITAL silence (all samples exactly 0), which is the only case in
		 *   which «sent» and «not sent» sound identical.  A threshold («below
		 *   -60 dB») would be a decision on the user's sound taken by the code.
		 *
		 * ⛔⛔ AND IT MUST BE HANDED TO TWO PROCESSES: the real encoder lives in
		 *      the CHILD (`children_phase9()`, which copies it into the child's
		 *      `argv` because the environment there is built from scratch), but
		 *      `--audio-test` opens one in THIS process too.  Handing it to
		 *      only one would make the tone bench measure a product different
		 *      from the real-session bench's. */
		/* ⛔⭐⭐⭐ PHASE 10 — THE COMPOSITION BUDGET.
		 *
		 *     The argument is the **Mpixel/s of COMPOSITION** this machine
		 *     holds, and the quantity is that one and no other: `[M]` §6.11 —
		 *     the bare encoder holds **1.86 Gpixel/s**, composition **0.97**,
		 *     and what saturates `rcs0` is **`gnome-shell` at 99.5 %** while
		 *     `remotix` sits at **0.00 %**.  ⇒ Giving the encoder's number here
		 *     would admit `[M]` ~22 sessions where six fit.
		 *
		 * ⛔⛔ AND THE NUMBER DOES NOT SELF-TUNE, and it is written here because
		 *      it is here that someone will be tempted to have it deduced:
		 *      `[M]` §6.9 — **until the machine has given way at least once,
		 *      the maximum read is a LOWER BOUND**, that is «the point where one
		 *      stopped trying».  A ceiling deduced from a climb that made
		 *      nothing give way would refuse users for nothing.
		 *      ⇒ Whoever types this option **declares** they have measured.
		 *
		 * ⭐ `0` = OFF, and it is the DEFAULT: `CODER.md` I6 — the budget does
		 *    not cure an appearance defect, **it acquires a function**, and a
		 *    rejected user is the most visible thing a server can do. */
		else if (strcmp(a, "--budget-mpixel-s") == 0 && v)
			budget_mpixel_s = strtod(argv[++i], NULL);
		/* ⭐⭐ THE RULE'S KNOB — §6.9, and the scale is measured:
		 *
		 *      `0`     «delivered» rule: whoever is inside costs what it
		 *              delivers now.  `[M]` cap **6 saturated**, ⛔ idle
		 *              **unlimited** — that is, blind to WAKE-UP;
		 *      `0.5`   ⭐ the default: `[M]` **0 false yes and 0 false no**,
		 *              cap **6 saturated / 10 idle** — the ten of
		 *              `SPECS.md` §5.5 found again by MEASUREMENT;
		 *      `1`     «worst» rule: everyone at the maximum. `[M]` 5 and 6,
		 *              with **one false no** (it refuses the sixth, which held).
		 *
		 * ⛔ It serves against WAKE-UP, which is the real hole: `[M]` §6.16 —
		 *    eight idle sessions admitted when they cost 0.01 % each wake up in
		 *    **19 ms** and ask for **130 %** of an engine that has 100; whoever
		 *    was working loses **95.9 %** of the rate.  ⛔ And the rate
		 *    regulator of phase 9 cannot remedy it: it holds back frames
		 *    **already composed and already encoded**. */
		else if (strcmp(a, "--reserve") == 0 && v)
			budget_reserve = strtod(argv[++i], NULL);
		/* ⛔⭐ THE ADMINISTRATIVE CAP — §4.6: *«ten is not the limit: it is the
		 *     administrative cap»*.  ⭐ The FOUR tables that count a served user
		 *     are sized from it — `attached[]` (`rcp.c`), `v[]` (`child.c`),
		 *     `stages[]` (`webtransport.c`) and `present[]` (here): until this
		 *     morning they were four `#define`s copied by hand, and `[M]` §6.4
		 *     had seen them **diverge** (slot table at 2, children table left
		 *     at 16).
		 *
		 * ⛔ It is typed BEFORE the tables exist, and applies once only: the
		 *    startup line says the number in force.
		 * ⚠ And it is NOT the budget: whoever does not fit receives `0x0E`
		 *   («the table is full»), not `0x06` («the machine has no capacity
		 *   left»).  The two are ADDED — §8.1 D5 — and the user's gesture is
		 *   different. */
		else if (strcmp(a, "--session-cap") == 0 && v)
			session_cap = (int)strtol(argv[++i], NULL, 10);
		else if (strcmp(a, "--no-audio-silence") == 0)
			audio_silence = false;
		else {
			help(argv[0]);
			return 2;
		}
	}
	if (!name)
		name = address;

	if (!name[0] || strcmp(name, "0.0.0.0") == 0 || strcmp(name, "::") == 0) {
		/* ⛔ `RCP.md` §4.1: «the certificate MUST carry as `subjectAltName`
		 *    the address on which the server answers».  A SAN `0.0.0.0`
		 *    matches NOTHING, and ⚠ «a browser that finds a SAN that does not
		 *    match shows a DIFFERENT warning, and some do not even offer the
		 *    click to proceed».  No guessing: it is asked for. */
		fprintf(stderr,
		        "⛔ --name is needed: the certificate must carry the address on "
		        "which the server answers (RCP.md §4.1), and «%s» is not an "
		        "address.\n",
		        name);
		return 2;
	}

	signal(SIGINT, on_signal);
	signal(SIGTERM, on_signal);
	signal(SIGPIPE, SIG_IGN);

	/* ⭐ The journal is turned on BEFORE the first line, so that it goes there too. */
	int journal_errno = 0;
	if (journal_requested && !log_journal(true))
		journal_errno = errno;
	registro_dice(LOG_STARTUP, "REMOTIX — phase 1, the bare wire");
	if (journal_requested && !journal_errno)
		registro_dice(LOG_STARTUP,
		              "log also in the systemd journal (--journal): "
		              "SYSLOG_IDENTIFIER=remotix, fields REMOTIX_AREA and "
		              "REMOTIX_TENANT — the line here stays identical");
	else if (journal_requested)
		registro_dice(LOG_STARTUP,
		              "⚠ --journal requested but the socket does not open (%s): the "
		              "log stays ONLY here",
		              strerror(journal_errno));
	/* ⭐⭐ PHASE 18 — WHAT IS OFFERED TO THE BROWSER, MEASURED AT STARTUP.
	 *     `video.codec` of the `HERE_I_AM` (§4.3) says only the codecs this
	 *     machine can do: HEVC and H.264 if the CARD encodes them.  ⛔ Phase 19
	 *     (1 Oct 2026, `DECISIONS.md` §10.27), the user's words: *«no cpu
	 *     without a card»* — the software fallback (OpenH264) is out.  Without
	 *     a capable card it is declared here, with the reason, and every HELLO
	 *     ends in NOTHING_IN_COMMON. */
	{
		char offered[32], explain[1024];
		registro_dice(LOG_STARTUP,
		              "⭐ phase 18 — encoding test at startup, in a separate process: the "
		              "«opened: …» lines at 256x256 below are its own, not a session's");
		bool something = child_video_capabilities(offered, sizeof offered, explain, sizeof explain);
		rcp_video_codec_set(offered);
		if (something)
			registro_dice(LOG_STARTUP,
			              "⭐ phase 18 — video.codec offered in the HERE_I_AM: «%s» — %s",
			              offered, explain);
		else
			registro_dice(LOG_STARTUP,
			              "⛔⛔ THIS SERVER CANNOT ENCODE VIDEO: no capable "
			              "card, no codec in the HERE_I_AM, every HELLO will end in "
			              "NOTHING_IN_COMMON — %s.  ⛔ REMOTIX encodes ONLY on the card "
			              "(phase 19, no software fallback): it needs a card with "
			              "a driver that encodes — Vulkan Video (AMD with RADV, NVIDIA "
			              "with the proprietary driver) or VA-API (Intel, AMD)",
			              explain);
	}

	/* ⭐ PHASE 12 — which desktop this server will start, said at startup: with
	 *    GNOME and KDE together the choice is ambiguous, and it is read here
	 *    instead of discovering it from a desktop that is not the expected one
	 *    (`DECISIONS.md` §4.6-duodetricies). */
	registro_dice(LOG_STARTUP, "the desktop of this machine: %s", session_desktop_explain());
	/* ⭐ D-001 — and the same fact, with the name of §4.5, goes into every
	 *    client's `SESSION`: before it said «unknown» (then `sconosciuto`) to everyone, since
	 *    phase 1. */
	switch (desktop_session()) {
	case SESSION_DESKTOP_GNOME:
		wt_desktop("gnome");
		break;
	case SESSION_DESKTOP_KDE:
		wt_desktop("kde");
		break;
	case SESSION_DESKTOP_XFCE:
		wt_desktop("xfce");
		break;
	case SESSION_DESKTOP_LXQT:
		wt_desktop("lxqt");
		break;
	case SESSION_DESKTOP_NONE:
	default:
		wt_desktop("unknown");
		break;
	}
	/* ⭐ PHASE 12, INCREMENT 2 — on KDE the capture permission is checked HERE,
	 *    before any session is born: KWin shows `zkde_screencast_unstable_v1`
	 *    only to an executable declared in a `.desktop` (`kwin.h`, `[M]` 18 Sep
	 *    2026).  ⭐ PHASE 17: the file belongs to the package, and the server
	 *    no longer writes it — it checks it and, if it is not right, gives the
	 *    code and the remedy.  On GNOME nothing is checked. */
	if (desktop_session() == SESSION_DESKTOP_KDE) {
		char why[768];

		if (kwin_check_permission(why, sizeof why))
			registro_dice(LOG_STARTUP, "⭐ the capture permission for KWin: %s", why);
		else
			registro_dice(LOG_STARTUP,
			              "⛔ the capture permission for KWin is NOT there (%s): "
			              "Plasma sessions will be born but will not be visible",
			              why);
	}

	/* ⛔⭐ THE THREE CLOCKS OF §5.3 ARE WRITTEN AT STARTUP, and it is not
	 *     decoration.
	 *
	 *     A half-hour ceiling is tested in two ways: waiting half an hour, or
	 *     reading the number.  ⚠ Nobody does the first — «it means keeping the
	 *     PC busy», the user's words on 16 Aug 2026 — so without this line the
	 *     value in force is NEVER verified by anyone, and it is exactly form E1
	 *     («written is not in force») that has already cost us dearly.
	 *
	 * ⭐ This way the MECHANISM is tested at short values (`--inactivity-s 10`)
	 *    and the NUMBER is read here.  They are two different checks, and
	 *    neither keeps a machine busy. */
	registro_dice(LOG_STARTUP,
	              "⭐ §5.3, the three clocks in force: client silence 30 s "
	              "(fixed) · user inactivity %llu s%s · ⛔ session "
	              "abandonment %llu s%s — and when it expires the graphical session "
	              "is CLOSED, with the programs open inside it",
	              (unsigned long long)(rcp_inactivity() / 1000),
	              rcp_inactivity() ? "" : " (OFF)",
	              (unsigned long long)(abandon_ms / 1000),
	              abandon_ms ? "" : " (OFF)");

	/* ⛔⭐ AND THE EVICTION IS ALWAYS DECLARED, on AND off — like the video
	 *     queue threshold and unlike the test tone: here «off» is not noise, it
	 *     is the fact that whoever reads the log after a `ALREADY_ACTIVE_REMOTELY`
	 *     must be able to know at once.
	 * ⛔⛔ AND SINCE 24 AUG 2026 THE LINE SAYS THE REAL STATE AND THE REASON: a
	 *      line still saying «OFF (I6)» on a cure that is on is worse than no
	 *      line. */
	if (rcp_eviction())
		registro_dice(LOG_STARTUP,
		              "⭐ phase 9 — ghost eviction: threshold %llu ms, ON. "
		              " The slot of a client silent for longer than the threshold goes to "
		              "a client of the SAME user that asks for it — ⛔ never between "
		              "different users.  ⭐ It is the DEFAULT since 24 Aug 2026 "
		              "(the user's decision; it is half the silence "
		              "clock, %llu ms).  ⚠ `[M]` the ghost goes from 32.13 s "
		              "and 14 refusals to 16.83 s and 7.  ⛔ It is TURNED OFF with "
		              "`--eviction-ms 0`, and that is the only road",
		              (unsigned long long)rcp_eviction(),
		              (unsigned long long)rcp_eviction_recommended());
	else
		registro_dice(LOG_STARTUP,
		              "⛔ phase 9 — ghost eviction: threshold 0 ms, turned OFF by "
		              "hand (`--eviction-ms 0`).  The slot will be freed only "
		              "by the silence clock (30 s), and whoever comes back after a "
		              "drop will be told the slot is taken — by "
		              "themselves.  ⚠ And it is NOT the default: since 24 Aug 2026 "
		              "it is born ON at %llu ms (the user's decision), so "
		              "someone turned it off on purpose",
		              (unsigned long long)rcp_eviction_recommended());

	/* ⛔ And the test tone is declared HERE, before any session: a server that
	 *    played a tone without saying so would be a defect disguised as a
	 *    feature.  ⚠ `wt_audio_test()` writes its line only when it is on, and
	 *    that is intended: a log that repeats «off» at every startup is no
	 *    longer read. */
	wt_audio_test(audio_test_hz);

	/* ⛔⭐⭐ AND THE AUDIO SILENCE IS HANDED TO THIS PROCESS, not only to the
	 *      children.  `--audio-test` opens an `audio_cod` in here
	 *      (`webtransport.c`): without this line the test tone would keep
	 *      sending its zeros while the real session silences them, and the two
	 *      benches would measure two different products with the same md5.
	 * ⚠ The line of the value IN FORCE is written by `audio.c` at the opening
	 *   of every encoder — no second one is written here, or «set» and «in
	 *   force» would become two facts with the same face. */
	audio_silence_hush(audio_silence);

	/* ⛔⭐⭐ PHASE 10 — THE CAP AND THE BUDGET, and the lines are ALWAYS written.
	 *
	 *     The cap is imposed BEFORE anything else: the four tables are allocated
	 *     on it at the first request, and from that moment it no longer moves.
	 *     ⚠ `children_turn_on()` further down reads it: if someone moved this line
	 *     after it, the children table would be born with the default and the
	 *     others with the requested number — which is exactly the divergence
	 *     that `[M]` §6.4 had measured. */
	if (session_cap < 1) {
		registro_dice(LOG_STARTUP,
		              "⛔ --session-cap %d makes no sense: %d stays",
		              session_cap, rcp_cap());
	} else if (!rcp_cap_set(session_cap)) {
		registro_dice(LOG_STARTUP,
		              "⛔ --session-cap %d did NOT come into force (the "
		              "tables were already allocated): %d stays",
		              session_cap, rcp_cap());
	}
	registro_dice(LOG_STARTUP,
	              "⭐ phase 10 — ADMINISTRATIVE session cap: **%d** "
	              "(default %d, `SPECS.md` §5.5)%s.  ⭐ IT IS ONE "
	              "NUMBER ONLY: from here are sized the slots of rcp.c, the stages of "
	              "child.c, the canvases of webtransport.c and the presence of main.c "
	              "— `[M]` §6.4 had seen them diverge (slots 2, children 16). "
	              " ⚠ Whoever does not fit receives 0x0E, which is an "
	              "ADMINISTRATIVE limit: the PHYSICAL limit is `--budget-mpixel-s`, and "
	              "says 0x06",
	              rcp_cap(), RCP_SESSION_CAP,
	              rcp_cap() == RCP_SESSION_CAP ? ""
	                                                : " — moved by hand");

	budget_cells(rcp_cap());
	budget_turn_on(budget_mpixel_s, budget_reserve, CANVAS_W, CANVAS_H);
	budget_startup_line(rcp_cap());

	/* ⛔⭐ AND THE VIDEO QUEUE THRESHOLD IS ALWAYS DECLARED, on **and** off —
	 *     unlike the test tone above, and the difference is not a whim: a tone
	 *     that does not play is looked for by nobody, but a threshold that is
	 *     off and a threshold that never triggered produce the same log (zero
	 *     abandonments by threshold), and whoever rereads a bench would not
	 *     know which of the two it measured.  ⇒ The line is written by
	 *     `webtransport.c`, that is **whoever really uses the number**, and not
	 *     by this file which only read it from the command line. */
	wt_clear_threshold(clear_threshold_ms);

	/* ⛔⭐⭐ AND THE RATE REGULATOR RIGHT AFTER, AND THE ORDER IS NOT CHANCE.
	 *
	 *      `wt_adaptive_rate()` writes its startup line looking at the
	 *      threshold ALREADY IN FORCE: if it is off, it declares that the
	 *      regulator will never be able to trigger — the backlog does not
	 *      exceed 1 and the slots are 2.  Swapping the two calls would make it
	 *      read zero, and that line would say the false precisely in the round
	 *      where it is needed.
	 *
	 * ⛔ And the line goes out ON OR OFF, as for the threshold and for the same
	 *    reason: a regulator that is off and a regulator that never had to
	 *    trigger produce the same log, that is no line. */
	wt_adaptive_rate(adaptive_rate);

	/* ⛔⭐⭐⭐ AND THE DEAD LINE, and it is ALWAYS called — on and off — for the
	 *       same reason as the two above, with one more weight: this one does
	 *       not make the picture look worse, IT CLOSES THE SESSION.  A session
	 *       that disappears without a line saying whether the cure was on and
	 *       with which numbers is indistinguishable from a defect of ours. */
	wt_dead_line(dead_line, dead_line_stall_ms, dead_line_silence_s);

	/* ⛔ §4.4-bis: «the ban survives restart», and it is invariant I7 — the
	 *    protection against a known defect lives in the program, not in a
	 *    configuration line that can be lost. */
	{
		int n = rcp_ban_load(file_ban, log_now_ms());
		if (n < 0) {
			/* ⛔ «zero bans» and «I could not look» are two different facts
			 *    (`rcp.h`, `LESSONS.md` §1.9 rule 1): the second is the
			 *    protection turned off with the air of having nothing to
			 *    protect, that is invariant I7 broken silently.  Not
			 *    starting. */
			registro_dice(LOG_STARTUP,
			              "⛔ the ban file %s exists and could NOT be "
			              "read: it is not «zero bans», it is the protection of "
			              "§4.4-bis turned off.  Not starting.",
			              file_ban);
			return 1;
		}
		registro_dice(LOG_STARTUP, "ban: %s, %d addresses loaded", file_ban, n);
	}

	/* ⭐ «How one gets out: the 12 hours passing, or an unblock command on the
	 *    server — which asks for access to the machine, that is the only key
	 *    that case admits» (`SPECS.md` §4.2, `RCP.md` §4.4-bis).  ⛔ And
	 *    the command talks to the LIVE process, which is the only one holding
	 *    the ban table: see the box in `command.h`, finding R12.1.
	 *
	 * ⚠ `command_open()` returns NULL also when the socket was not requested,
	 *   and in both cases it writes WHY: the server goes on, because without
	 *   the command the protection of §4.4-bis is still there — the only way
	 *   out is the twelve hours. */
	/* ⛔⭐ THE HELPER IS STARTED HERE, AND THE «HERE» IS HALF THE CURE — §1.10.
	 *
	 *     A `fork()` gives the child all the open descriptors.  ⛔ Started after
	 *     `transport_open()` or `page_open()`, the helper would carry along
	 *     the UDP socket and the TCP listener of 7447: the server dies, the port
	 *     stays held by a process that does not use it, and whoever restarts
	 *     reads «address already in use» without seeing any server.
	 *     ⚠ It is the worst form of defect — the symptom does not name the cause.
	 *
	 * ⭐ Started here it inherits: the three standard descriptors and the ban
	 *    file, which is already closed.  And it does NOT inherit the socket of
	 *    the unblock command, which is opened in the line below.
	 *
	 * ⚠ And if it does not start, the server starts anyway and says so: without
	 *   a helper every authentication is a NO (invariant I3), which is
	 *   unpleasant but it is the right direction in which to be wrong. */
	/* ⛔⭐ AND THE STAGE IS NO LONGER TAKEN HERE — §1.10-bis, 12 Aug 2026.
	 *
	 *     Until yesterday, at this point, the server called `session_ensure()`
	 *     and `first_frame()`: it took **the graphical session it was
	 *     running inside**, and showed it to whoever got in.  ⛔ `[M]` on the
	 *     test machine the server ran as `nicfio` and the user got in as
	 *     `prova`: what was seen in the tab was `nicfio`'s desktop — that is,
	 *     the stage belonged to the PROCESS, not to the user.
	 *
	 * ⇒ Now the stage belongs to the **child**, which is born when PAM says yes
	 *   and runs as that user (`child.h`).  ⚠ The table is started here
	 *   because `delivery_verdict()` wants it ready; the children are not:
	 *   they are born one per admitted user.
	 *
	 * ⚠ And the fallback is DECLARED (`CODER.md` §4.2): if the table does not
	 *   start the server starts anyway — page and authentication work — and
	 *   nobody sees a pixel. */
	pam_help = helper_turn_on();
	if (!pam_help)
		registro_dice(LOG_STARTUP,
		              "⛔ no PAM helper: falling back to the SYNCHRONOUS "
		              "check, which stops the loop for 1-2 s at every attempt "
		              "(DECISIONS.md §1.10).  The fallback is declared, not "
		              "silent (CODER.md §4.2).");

	offspring = children_turn_on(CANVAS_W, CANVAS_H, dir_survey, deposit_frame,
	                      dismiss_child, cursor_from_stage, canvas_from_stage,
	                      NULL);
	if (!offspring)
		registro_dice(LOG_STARTUP,
		              "⛔ the children table does not start: NO user "
		              "will have a stage, and phase 2 has no object.  The server "
		              "starts anyway (phase 1 works), and the why is "
		              "in the line above");
	/* ⛔⭐⭐ THE TWO CURES THAT LIVE IN THE CHILD — and this line is the only one
	 *      that makes them exist.  ⚠ NOTHING is turned on here: the children
	 *      table is handed what every child will have to repeat to itself
	 *      after the `execve`, because the encoders are over there.  ⚠ The
	 *      audio silence is a half exception: the encoder of the TEST TONE is
	 *      opened here too, and that is why `audio_silence_hush()` above
	 *      receives the SAME `bool`.  ⛔ And whoever declares the value in force
	 *      will be `encoder.c`, at the opening of every encoder: if the
	 *      option got lost on the way, those lines would say «off» and the
	 *      defect would show at once (form D5). */
	children_phase9(offspring, quality_recovery, bandwidth_cap_mbit, audio_silence);

	/* ⛔ Who owns this process, written once and not deduced by the reader: on
	 *    this depends whether the children can REALLY drop to another user.
	 *    ⚠ An unprivileged server spawns children that stay itself —
	 *    `setuid()` fails, and `children_ensure()` declares it. */
	registro_dice(LOG_STARTUP,
	              "%s this process is uid %ld: %s",
	              geteuid() == 0 ? "⭐" : "⚠", (long)geteuid(),
	              geteuid() == 0
	                      ? "it can check anyone's password with PAM and "
	                        "drop the children to the right user "
	                        "(DECISIONS.md §1.10-bis)"
	                      : "it is NOT root — PAM will be able to check only its own "
	                        "user, and a child will be able to be born only for it");

	k = command_open(socket_command);

	look_pam_service();

	if (!certificates_prepare(&cert, dir_cert, name))
		goto fine;

	ctx_quic = tls_quic_context(cert.session_pem, cert.session_key);
	ctx_page = tls_page_context(cert.page_pem, cert.page_key);
	if (!ctx_quic || !ctx_page)
		goto fine;

	t = transport_open(address, port, ctx_quic, pam_help, dir_cert);
	if (!t)
		goto fine;
	bridge.t = t;
	bridge.f = offspring;
	/* ⛔ The hook is connected HERE, after the children table exists and before
	 *    the first packet arrives: connecting it later would leave the first
	 *    session without the request for its keyframe, that is with the screen
	 *    frozen and no line saying why. */
	wt_video_hook(video_ask, &bridge);
	wt_audio_hook(audio_ask, &bridge);
	/* ⭐ And with it the input one, for the same reason and at the same
	 *    instant: connecting it later would leave the first session with a
	 *    desktop that can be seen and not commanded, and no line saying why. */
	wt_input_hook(input_to_child, &bridge);
	/* ⭐⭐ And the CANVAS one, at the same instant and for one more reason: the
	 *     client asks for its size **at attach**, that is in the first half
	 *     second of every session.  A hook connected after the first packet
	 *     would answer `COMPOSITOR_UNABLE` precisely to the request that
	 *     matters — and the client would show «fit the desktop» as off on a
	 *     server that can do it. */
	wt_recanvas_hook(recanvas_to_child, &bridge);
	wt_layout_hook(layout_to_child, &bridge);

	/* ⭐⭐ §5.1 — THE GUARD OF THE LOCAL SESSIONS, and it is connected BEFORE the
	 *     page for the same reason as the others: the `0x05` question is asked
	 *     at `ATTACH`, that is in the first half second of every session.  A
	 *     hook connected after the first packet would let in **precisely** the
	 *     session this rule must keep out.
	 *
	 * ⛔ And if logind is not there, `sentinel_open()` has already written in
	 *    the log that the rule is NOT in force: nothing is connected here, and
	 *    `rcp.c` will say so at every attach.  ⚠ It is not a reason not to
	 *    start — I1: a session without a rule is worth more than no session. */
	guardian = sentinel_open();
	if (guardian) {
		wt_local_hook(ask_local_session, guardian);
		/* ⭐⭐ AND THE CHECK HAS ITS OWN HOOK, which asks for EVERYONE at once
		 *     — the reason, with the numbers, is in `sentinel.h` above
		 *     `sentinel_locals()`: `[M]` §6.13, the cost goes from `N × D` to
		 *     `D` inside the loop that delivers frames.  ⛔ Both are connected
		 *     or neither: they are the two halves of the same rule, and half a
		 *     rule is worse than none. */
		wt_locals_hook(sweep_local_sessions, guardian);
	}
	/* ⛔⛔ AND THE LINE THAT SAYS WHETHER SURVEILLANCE IS IN FORCE — 25 Aug 2026,
	 *      finding R7 of §5.5, and until this morning NOBODY WROTE IT.
	 *
	 *      `webtransport.c`, above `wt_watch_locals()`, defended itself from
	 *      the silent fallback with these words: *«the defect would come back
	 *      the day someone forgets to connect the hook, without a red line —
	 *      whoever does not connect it does not apply the «watched» half of
	 *      §5.1, and it is `main.c` that writes it in the log at startup»*.
	 *      ⛔ `main.c` did not write it: the comment declared a net that was not
	 *      there, and it is form E1 of `REVIEWER.md` — whoever reads the code
	 *      believes the guard is there.
	 *
	 * ⇒ ⭐ Now it is there, and it says the value in force **on AND off**
	 *      (`CODER.md` §2-bis): «connected» and «NOT connected» are two
	 *      different lines, and the second is the one looked for when §5.1 does
	 *      not bite.
	 * ⚠ And it is written AFTER the `if`, not inside: this way the line goes out
	 *   even when the guard is not there — which is precisely the case where it
	 *   is needed. */
	registro_dice(LOG_SESSION,
	              "§5.1, the WATCHED half (the periodic check of the "
	              "local sessions): %s.  ⚠ The other half — the question "
	              "at `ATTACH` — %s",
	              guardian ? "CONNECTED, one question to logind per check "
	                          "(§6.13: it was `N × D`, now it is `D`)"
	                        : "⛔ NOT connected: nobody will notice that a "
	                          "user has opened a local session while their "
	                          "remote one is working",
	              guardian ? "is connected too"
	                        : "⛔ is not connected: logind does not answer, and the "
	                          "rule is NOT in force on this server");

	/* ⭐ §7.6 — and it is connected here with the others: the `Ctrl+Alt+End`
	 *    shortcut can arrive with the first useful packet of the session, and a
	 *    hook connected later would leave the user pressing a combination that
	 *    does nothing — which is worse than not having it. */
	wt_terminate_hook(terminate_in_child, &bridge);
	/* ⭐ And the twin: the fact that arrives from the desktop instead of the wire. */
	children_hook_session_finished(offspring, session_ended_by_child, &bridge);
	children_hook_canvas_wait(offspring, canvas_wait_for_child, &bridge);
	/* ⭐ PHASE 7: the audio blocks come up this way.  ⚠ AFTER `children_turn_on`,
	 *    like all the other hooks: before, there is no table to hook them to. */
	children_hook_block(offspring, audio_block, NULL);
	/* ⭐⭐ PHASE 7 — THE CLIPBOARD, in both directions, and the two hooks are
	 *     hooked together: `webtransport.c` does not connect the channel if one
	 *     is missing, and `children_hook_clipboard` refuses to hook only one.
	 *     ⚠ Half a channel is seen by the user as «the clipboard does not
	 *     work», which is the same face as «there is no clipboard». */
	wt_clipboard_hook(clipboard_offer_to_child, clipboard_response_to_child,
	                  &bridge);
	children_hook_clipboard(offspring, clipboard_from_session,
	                     clipboard_request_from_session, &bridge);

	/* ⭐⭐ PHASE 17 T7 — BEFORE saying «ready»: the desktops that a previous
	 *     parent left alive enter the counts before the first user can knock. */
	found_again_at_startup(log_now_ms());

	p = page_open(address, port, ctx_page, file_html, &cert);
	if (!p)
		goto fine;

	registro_dice(LOG_STARTUP,
	              "⭐ ready: https://%s:%s  —  the WebTransport session lives "
	              "on /rcp/1 (RCP.md §2.2)",
	              name, port);

	last_cert_check = time(NULL);

	while (!stop_requested) {
		struct pollfd fds[MAX_POLL];
		size_t n = 0, npage, ncommand, nhelp, nchildren;
		uint64_t t_now;
		int wait;

		fds[n].fd = transport_fd(t);
		fds[n].events = POLLIN;
		fds[n].revents = 0;
		n++;

		npage = page_descriptors(p, fds + n, MAX_POLL - n);
		ncommand = command_descriptors(k, fds + n + npage,
		                               MAX_POLL - n - npage);

		/* ⭐ The PAM helper enters the `poll` like all the others, and that is
		 *    all that is needed for the loop to no longer wait for anyone
		 *    (`DECISIONS.md` §1.10).  ⛔ At the end, after the page and the
		 *    command, because their counts are relative and slotting it in
		 *    between would shift the indices of two calls. */
		nhelp = 0;
		if (helper_descriptor(pam_help) >= 0
		    && n + npage + ncommand < MAX_POLL) {
			size_t i = n + npage + ncommand;
			fds[i].fd = helper_descriptor(pam_help);
			fds[i].events = POLLIN;
			fds[i].revents = 0;
			nhelp = 1;
		}

		/* ⭐ And the children after the helper, for the same reason: the counts
		 *    of whoever comes before are relative, and slotting them in between
		 *    would shift the indices of three calls.  ⛔ And they are the last
		 *    block for a reason of truth too: if `MAX_POLL` ran out, those left
		 *    out are the children — that is the video — and not the page or the
		 *    authentication.  An ugly session is worth more than a closed
		 *    session (invariant I1). */
		nchildren = children_descriptors(offspring, fds + n + npage + ncommand + nhelp,
		                           MAX_POLL - n - npage - ncommand - nhelp);

		wait = transport_wait_ms(t);
		if (wait < 0 || wait > 1000)
			wait = 1000;
		/* ⛔ With the test tone on the loop wakes up every 10 ms, because the
		 *    blocks are generated by `wt_beat()` and with a one-second wait
		 *    fifty would come out at once — that is a burst the datagram queue
		 *    would throw away, and the log would say «thrown away» for a defect
		 *    manufactured by the bench.
		 * ⚠ It is NOT needed by real audio: that one is paced by PipeWire, which
		 *   sits in the `poll` with a descriptor of its own.  ⇒ This line dies
		 *   with the test source, and it is not a hidden debt. */
		if (audio_test_hz && wait > 10)
			wait = 10;

		if (poll(fds, n + npage + ncommand + nhelp + nchildren, wait) < 0) {
			if (errno == EINTR)
				continue;
			registro_dice(LOG_STARTUP, "⛔ poll: %s", strerror(errno));
			break;
		}

		if (fds[0].revents & POLLIN)
			transport_read(t);
		/* ⛔ PAM's answers BEFORE `transport_expired()`: the verdict can make an
		 *    `ADMITTED` ripe, and delivering it later would add one loop round
		 *    for whoever authenticates — that is, it would worsen precisely the
		 *    number this cure must not touch.
		 * ⚠ And it is called even when the descriptor is NOT readable: it is in
		 *   there that requests expire, and an expiry that waits for a byte is
		 *   an expiry that never triggers — precisely in the case it was written
		 *   for (the lesson of `rule_heartbeat`, paid on 11 August with B6). */
		t_now = log_now_ms();
		/* ⛔⭐⭐⭐ THE LOOP'S BEAT — and it goes BEFORE everything that judges.
		 *
		 * `wt_parent_round()` measures how much time has passed since the
		 * previous pass, that is **how long we were blind**: in that time no
		 * byte could go out and no client packet could be read.
		 * ⛔ Without this line the dead line reads that gap as *«the line is
		 *    DEAD»* and closes healthy sessions with `lost=0` written next to
		 *    it — `[M]` §6.7: a 5 s `SIGSTOP` on ONE child killed ALL the
		 *    sessions.  The full why is in `webtransport.c`, above
		 *    `WT_EXPECTED_ROUND_MS`.
		 * ⚠ It is here and not inside `poll()` because what counts is the
		 *   distance between two COMPLETE passes: a loop that wakes up and then
		 *   stays blocked inside a synchronous call has delivered nothing, and
		 *   measuring it from the wake-up would say that all went well. */
		wt_parent_round(t_now);
		/* ⛔ §5.3, the third clock: it is checked at EVERY pass, not when
		 *    something arrives.  The case that matters is precisely the one
		 *    where nothing arrives any more. */
		abandon_round(&bridge, t_now);
		/* ⭐ PHASE 17 T7: are the desktops found again still there?  (Every
		 *    10 s, and only if some are waiting for reattach.) */
		found_again_sweep(t_now);
		if (nhelp && (fds[n + npage + ncommand].revents & POLLIN))
			helper_move(pam_help, delivery_verdict, &bridge);
		helper_expired(pam_help, t_now, delivery_verdict, &bridge);
		/* ⛔ The children BEFORE `transport_expired()`, and for the same reason
		 *    as PAM's answers: a frame just arrived from the stage can enter the
		 *    depot **in this round**, and postponing it to the next would cost a
		 *    whole round to whoever is waiting to see their own desktop.
		 * ⚠ And it is ALWAYS called, even when no child is readable: in here
		 *   the dead are reaped (`waitpid(WNOHANG)`) and introductions expire,
		 *   and an expiry that waits for a byte never triggers. */
		children_move(offspring, fds + n + npage + ncommand + nhelp, nchildren, t_now);
		children_recheck(offspring, t_now);
		transport_expired(t);
		page_move(p, fds + 1, npage);
		command_move(k, fds + 1 + npage, ncommand);

		/* ⛔ THE ROTATION, and it is checked once a minute instead of at every
		 *    round: «before it expires», not «when it has expired»
		 *    (§4.1-bis).  ⚠ One minute is plenty for a two-day margin, and it
		 *    costs nothing. */
		/* ⭐⭐ §5.1 — THE CHECK OF THE LOCAL SESSIONS, every LOCAL_SWEEP_MS.
		 *
		 * ⛔ It is not the `ATTACH`: that question is asked by `rcp.c` once and
		 *    that is all.  This is the other half of the rule — «opens a LOCAL
		 *    session while the remote one is alive» — and nobody asks it: either
		 *    it is looked at, or `0x04` stays a code nobody sends.
		 *
		 * ⚠ Two seconds and not every round: the question costs a synchronous
		 *   call to logind, and this is the same loop that delivers frames
		 *   (`LESSONS.md` §6.2-bis).  ⚠ And two seconds are the maximum delay
		 *   between «the user sat down in front of the machine» and «the remote
		 *   session drops»: it is a wait nobody watches with a stopwatch. */
		if (guardian && t_now - last_locals_sweep >= LOCAL_SWEEP_MS) {
			last_locals_sweep = t_now;
			wt_watch_locals();
		}

		/* ⛔⭐⭐ THE FALLBACK'S COUNT, ONCE A MINUTE — and until 25 Aug 2026
		 *      NOBODY emitted it.
		 *
		 * `sentinel.h` declares `sentinel_counts()` with written above it
		 * that it serves *«so that the synchronous choice can be MEASURED AGAIN
		 * instead of believed»* — ⛔ and `sentinel_counts()` **had no caller in
		 * the whole of `src/`**.  A counter nobody emits is worse than a counter
		 * that is missing: whoever reads the code believes the measurement is
		 * there.
		 * ⇒ Here is the caller, and the line carries the loop's gaps next to it,
		 *   because they are the two halves of the same question — *«how much
		 *   does asking logind inside the delivering loop cost us?»*.
		 * ⚠ One minute, not every check: it is a cumulative count, and at two
		 *   seconds it would be 43 200 lines a day saying almost always the same
		 *   thing (the defect of the 30.8 GB of log of phase 8). */
		if (guardian && t_now - last_guardian_count >= GUARDIAN_COUNT_MS) {
			uint64_t calls = 0, worst_ms = 0;
			uint64_t stills = 0, worst_stall = 0;

			last_guardian_count = t_now;
			sentinel_counts(guardian, &calls, &worst_ms);
			wt_stalled_rounds(&stills, &worst_stall);
			/* ⛔⛔ AND `tenants=` CAME IN ON 25 AUG 2026 — finding R7.
			 *
			 *      `sentinel.h` promised these two numbers *«next to the
			 *      number of tenants served»* and ⛔ **it was not in the
			 *      line**.  ⭐ It is the DENOMINATOR: without `N` the sentence at
			 *      the end here — «one call per check, not per tenant» — cannot
			 *      be **refuted**, because with a single tenant `N × D` and `D`
			 *      give the same count.  ⇒ With `tenants=7` and `calls=`
			 *      growing by 1 per check, the cure is read from the line
			 *      instead of from the comment. */
			registro_dice(LOG_SESSION,
			              "guardian: calls=%llu worst_ms=%llu "
			              "tenants=%zu loop_gaps=%llu "
			              "worst_gap_ms=%llu — ⭐ one call per CHECK, "
			              "not per tenant (§6.13: it was `N × D`, now it is `D`)",
			              (unsigned long long)calls,
			              (unsigned long long)worst_ms,
			              wt_tenants_served(),
			              (unsigned long long)stills,
			              (unsigned long long)worst_stall);
		}

		if (time(NULL) - last_cert_check >= 60) {
			last_cert_check = time(NULL);
			if (certificates_rotate_if_needed(&cert)) {
				SSL_CTX *fresh =
					tls_quic_context(cert.session_pem, cert.session_key);
				if (fresh) {
					/* ⚠ The connections already open keep the old context:
					 *   TLS is already done, and changing it underneath
					 *   makes no sense.  ⛔ The NEW ones take this one, and
					 *   the page already publishes the new fingerprint. */
					transport_context(t, fresh);
					SSL_CTX_free(ctx_quic);
					ctx_quic = fresh;
					registro_dice(REG_CERT,
					              "⭐ the QUIC context uses the rotated "
					              "certificate; the page already publishes the "
					              "new fingerprint and /fingerprint serves it");
				} else {
					registro_dice(REG_CERT,
					              "⛔ certificate rotated but the TLS context "
					              "cannot be rebuilt: new sessions "
					              "would use a certificate whose fingerprint the "
					              "page does not publish");
				}
			}
		}
	}

	registro_dice(LOG_STARTUP, "shutdown requested: %zu live QUIC connections",
	              transport_count(t));

	/* ⛔⭐ AND WHOEVER CLOSES SAYS SO — §8.1, §8.2 reason `0x0C SERVER_CLOSING`.
	 *     Finding B-7, night of 10 Aug 2026.
	 *
	 *     Before tonight the loop exited here and `transport_close()` freed
	 *     everything: no `FAREWELL`, no closing code, not even a
	 *     `CONNECTION_CLOSE`.  Whoever was connected waited thirty seconds and
	 *     read «network error» — the defect of `LESSONS.md` §1.7 that §3.1
	 *     exists to remove, and here the server did not even write «farewell».
	 *
	 * ⛔ And we WAIT for the bytes to go out, instead of counting rounds: the
	 *    capsule of §3.1 point 3 ripens half a second after the queue has
	 *    emptied (see `wt_beat`), so leaving at once would be writing the
	 *    farewell and throwing it away.  ⚠ But the wait has a bottom — two
	 *    seconds — or a client that no longer reads would hold up the shutdown
	 *    of the service.  ⛔ The giving up is written: whoever shuts down must
	 *    be able to tell «everyone knew» from «I did not make it in time». */
	{
		size_t remain = transport_dismiss_all(
			t, RCP_SERVER_CLOSING, "the server is shutting down");
		int rounds = 0;
		/* ⛔⭐ THE BUDGET IS COUNTED IN TIME, NOT IN ROUNDS — and on 11 Aug 2026
		 *     it was measured that the difference is a factor of fourteen.
		 *
		 *     Here there was `rounds < 200`, with «two seconds» written next to
		 *     it: the count assumed every round cost the 10 ms of the `poll`.
		 *     ⛔ But `poll` returns AT ONCE when there is something to read, and
		 *     at shutdown there is always something: **400 rounds lasted 293
		 *     ms** — read in the server log, 08:17:08.756 → 08:17:09.049.
		 *
		 * ⛔ Hence the real defect: `close_session()` arms a safety bottom at
		 *    **3 s** for the capsule of §3.1 point 3, and whoever shut down gave
		 *    up after three tenths.  The safety net existed and could not
		 *    trigger **precisely at the moment it had been written for**.
		 *
		 * ⚠ And a round counter that believes itself a clock is not wrong by a
		 *   little: it is wrong by how fast the machine is, that is by a number
		 *   that changes from one piece of hardware to another.  It is the worst
		 *   form, because the bench stays green where the hardware is slow. */
		struct timespec t0, tn;
		clock_gettime(CLOCK_MONOTONIC, &t0);
		while (remain > 0) {
			clock_gettime(CLOCK_MONOTONIC, &tn);
			{
				long long elapsed =
				    (long long)(tn.tv_sec - t0.tv_sec) * 1000
				    + (tn.tv_nsec - t0.tv_nsec) / 1000000;
				if (elapsed >= 4000)
					break;
			}
			struct pollfd fds[MAX_POLL];
			int wait = transport_wait_ms(t);
			fds[0].fd = transport_fd(t);
			fds[0].events = POLLIN;
			fds[0].revents = 0;
			if (wait < 0 || wait > 10)
				wait = 10;
			if (poll(fds, 1, wait) > 0 && (fds[0].revents & POLLIN))
				transport_read(t);
			transport_expired(t);
			remain = transport_dismiss_all(t, RCP_SERVER_CLOSING,
			                                  "the server is shutting down");
			rounds++;
		}
		/* ⛔⭐ AND THEN WE WAIT SOME MORE — measured by bench B7 on 11 Aug 2026,
		 *     case `server-in-chiusura`, and it is the defect the case was born
		 *     to find.
		 *
		 *     `wt_ha_da_dire()` becomes false when the closing capsule of §3.1
		 *     point 3 has been HANDED TO NGTCP2.  ⛔ But «handed to ngtcp2» is
		 *     not «out on the wire» — it is the same distinction `wt_beat`
		 *     makes for the `FAREWELL`, cured there and not here.  The loop
		 *     exited, `transport_close()` tore down QUIC, and those bytes no
		 *     longer left.
		 *
		 * ⛔ What the client saw, measured: the `FAREWELL 0x0c` arrived on the
		 *    channel, and the session closed **without a code** — QUIC
		 *    terminated with `code 0 · no reason`.  That is, the SECOND
		 *    road of §3.1 was missing.
		 *
		 * ⚠ And the second road is the one that matters: `DECISIONS.md` §7.14
		 *   and §7.15, decided today, make it the only one that always arrives
		 *   — on Firefox, which resets the channel and throws those bytes away,
		 *   it was the ONLY one.  A Firefox user would have seen the service
		 *   disappear **without any reason**, which is exactly what §8.1
		 *   forbids.
		 *
		 * ⭐ Half a second, and how long we waited is written: the cure must not
		 *    be able to become «wait and hope» without anyone seeing it. */
		if (remain == 0) {
			int queue = 0;
			while (queue < 50) {
				struct pollfd fds[MAX_POLL];
				fds[0].fd = transport_fd(t);
				fds[0].events = POLLIN;
				fds[0].revents = 0;
				if (poll(fds, 1, 10) > 0 && (fds[0].revents & POLLIN))
					transport_read(t);
				transport_expired(t);
				queue++;
			}
			registro_dice(LOG_STARTUP,
			              "⭐ farewell 0x0c sent to all sessions and out "
			              "on the wire in %d rounds, plus %d rounds of tail so that the "
			              "closing capsule (§3.1 point 3) really goes out "
			              "(§8.1: never with a silence)",
			              rounds, queue);
		}
		else
			registro_dice(LOG_STARTUP,
			              "⛔ %zu sessions did not finish after 4 s (%d rounds) — "
			              "«%s».  The farewell 0x0c was written but it may not "
			              "have gone out, and ⛔ §3.1 point 3 — the reason "
			              "in the closing code — may not have "
			              "left at all.  Closing anyway. "
			              "⚠ B7 `server-in-chiusura` measures exactly this.",
			              remain, rounds, transport_remain_reason(t));
	}
	outcome = 0;

fine:
	/* ⛔ The helper is shut down first: from here on there is nobody left to
	 *    deliver a verdict to, and a child writing on a socket nobody reads is
	 *    a process that stays.  ⚠ And `helper_turn_off()` WAITS for the child
	 *    — but outside the asynchronous loop, which has already ended:
	 *    `CODER.md` §4.4 forbids waiting INSIDE the loop, and this is the line
	 *    after the last round. */
	helper_turn_off(pam_help);
	/* ⚠ The guard before the page and the transport: from here on nobody asks
	 *   questions about who is connected any more, and keeping a system bus
	 *   open while closing serves no purpose. */
	sentinel_close(guardian);
	command_close(k);
	page_close(p);
	transport_close(t);
	/* ⛔ The children are shut down AFTER the transport: as long as a
	 *    connection is alive there may be a frame in the queue, and its bytes
	 *    are in the depot.
	 * ⚠ And they are shut down at the exit of the PROCESS, not of a connection:
	 *   it is invariant I4 — the stage belongs to the session, and whoever dies
	 *   when the network drops is not it.  ⛔ `children_turn_off()` WAITS for them
	 *   to be dead, because the virtual monitor disappears when the consumer
	 *   disappears: leaving earlier would leave a monitor attached to the
	 *   user's session with nobody watching it. */
	children_turn_off(offspring);
	if (ctx_quic)
		SSL_CTX_free(ctx_quic);
	if (ctx_page)
		SSL_CTX_free(ctx_page);
	return outcome;
}
