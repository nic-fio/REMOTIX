/*
 * 06-b33-wakeup.c — ⛔⛔ THE SECOND DOOR OF THE DYING CLICK.
 *
 * Sub-phase 6.1, §7.1 of the phase document: *"every `capture_wake()`
 * recreates the `libei` devices: 3 wake-ups, 3 replacements, with ZERO
 * `FIT_CANVAS`"*.  ⇒ The dying click has a door that **does not depend on the
 * canvas**, and it opens precisely while the user holds the mouse pressed on a
 * still desktop.
 *
 *   ./06-b33-wakeup [--canvas 1264x800]     opens, and waits for commands on stdin
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT THIS PROGRAM IS, AND WHAT IT IS NOT
 *
 * ⭐ It is `CODER.md` §3.6 to the letter — *"isolate ONE function, and call it
 *    from outside"*.  It links the PRODUCT modules (`src/capture.c`,
 *    `src/input.c`, `src/mutter.c`, `src/keyboard.c`) and calls
 *    `capture_wake()` — **the same function the child calls when the
 *    scene is still and a key is owed** (`child.c:6365`).  ⛔ There is no
 *    QUIC, no `rcp.c`, no message format.
 *
 * ⛔⛔ **AND IT IS NOT THE MEASUREMENT.**  What this program prints is the log
 *      of THE SENDER, and `CODER.md` §3.8 says it is worth nothing: it says
 *      we called a function, not that the desktop received anything.
 *      ⇒ The verdict is given by the **witness inside the session**
 *      (`06-b33-witness.c`), and read by `06-b33-risveglio.py`.
 *
 * ⚠ The only thing this program measures by itself — and it measures it, it
 *   does not deduce it — is `pointer_replacements`, read from `input_count()`,
 *   which is a window on the internal state of `input.c` and not a log line.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT USES `capture.c` AND NOT A CONSUMER WRITTEN HERE
 *
 * `04-b24-iniezione.c` writes its own PipeWire consumer by hand, and that is
 * right for what it measures (input, where the capture is only the pretext
 * that makes the viewport be born).  ⛔ Not here: **the defendant IS
 * `capture_wake()`**.  A wake-up written by hand in the bench would
 * measure my idea of how it works, not what the product does — and the two
 * diverge exactly on the day `capture.c` changes.
 *
 * ⚠ And `capture_start()` brings along the four consumption parameters
 *   (`ParamBuffers` and the three `ParamMeta`), which a hand-written consumer
 *   does not have: that difference changes the renegotiation, that is,
 *   precisely the thing being looked at.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE CONSUMER MUST CONSUME, OR THE VIEWPORT IS NOT BORN
 *
 * `[R]` `meta-screen-cast-virtual-stream-src.c:279-283`: the stream becomes
 * *configured* — and only then does Mutter add the viewport from which the
 * absolute device is born — inside `..._src_enable`, that is, **when someone
 * really starts reading the frames**.  ⇒ The command loop calls
 * `capture_take()` at every turn, with zero wait.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ AND THE CHAIN THIS BENCH TRIES TO REFUTE, all `[R]` in Mutter 48.7
 *
 *   1. `capture_wake()` calls `pw_stream_update_params()` on the already
 *      open stream (`src/capture.c:1392`);
 *   2. the producer renegotiates: `MetaScreenCastStreamSrc` turns off and on
 *      again, and `meta_screen_cast_virtual_stream_src_enable()`
 *      (`:263-290`) calls `meta_eis_viewport_notify_changed()`;
 *   3. `on_viewport_changed` (`meta-eis.c:319-323`) emits **`viewports-changed`**;
 *   4. `update_viewports` (`meta-eis-client.c:1049-1062`) calls
 *      `remove_viewport_devices` — which ⛔ **does NOT go through
 *      `drop_device()`** — and then `add_abs_pointer_devices`.
 *
 * ⇒ If the chain is true, a `risveglia` with `BTN_LEFT` down brings
 *   `pointer_replacements` to +1 **without anybody touching the canvas**, and from
 *   there on the button is an ORPHAN: its release reaches nobody and the
 *   desktop no longer takes a click (`meta-seat-impl.c:899-908`).
 *
 * ⛔ The hypothesis to refute is the one written in §7.1.  If
 *   `pointer_replacements` does NOT go up, §7.1 is false and must be corrected —
 *   and this bench must be able to say so.
 *
 * ---------------------------------------------------------------------------
 * THE COMMANDS (one per line; every answer starts with "B33R: ")
 *
 *   punta X Y            input_pointer
 *   pulsante C P         input_button        (C evdev: BTN_LEFT = 272)
 *   position C P        input_position       (C evdev: KEY_LEFTCTRL = 29)
 *   letter N            input_letter
 *   risveglia            ⭐⭐ `capture_wake()`, THE PRODUCT'S FUNCTION
 *   resize L A     `capture_resize()` — the ALREADY KNOWN case (§4.6),
 *                        which serves as a comparison: the door we knew about
 *   recanvas L A           input_recanvas
 *   rilascia             input_release_all  → prints HOW MANY it released
 *   dormi MS             ⛔ sleeps WHILE KEEPING libei running and consuming
 *   state                the count, the replacements, the orphans, the frames
 *   fine                 exits cleanly
 */
#include <errno.h>
#include <gio/gio.h>
#include <poll.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "capture.h"
#include "input.h"
#include "mutter.h"
#include "log.h"
#include "keyboard.h"

/* ⛔ The two bench windows of `src/input.c`: they are NOT in `input.h`, which
 *    is the PRODUCT contract and belongs to the coordinator.  They are
 *    declared here, with the same signature — changing it under them would
 *    break `04-b24`. */
extern void input_count(const Input *, unsigned *keys, unsigned *mouse_buttons,
                        unsigned *pointer_replacements, unsigned *keyboard_replacements, int *ready);
extern unsigned input_orphans(const Input *);

static MutterSession *session;
static Capture *cat;
static Input *channel;
static uint32_t canvas_w = 1264, canvas_h = 800;
static unsigned long frames;
static unsigned long wakeups;

static void tell(const char *shape, ...)
{
	va_list call_args;

	fputs("B33R: ", stdout);
	va_start(call_args, shape);
	vfprintf(stdout, shape, call_args);
	va_end(call_args);
	fputc('\n', stdout);
	fflush(stdout);
}

/*
 * ⛔ ONE TURN OF THE LOOP, and the two things it must do sit together on
 *    purpose: run `libei` (or the `DEVICE_ADDED` are never seen) and CONSUME
 *    (or the viewport is not born, `[R]` above).  ⚠ Calling only one of them is
 *    the defect that makes one measure a silence and call it a fault.
 *
 * Returns FALSE if the input channel has dropped.
 */
static gboolean run_once(void)
{
	CaptureStopped stopped;
	g_autoptr(GError) mistake = NULL;

	if (channel && input_run(channel) < 0)
		return FALSE;
	if (cat)
	{
		/* ⛔ ZERO wait: whoever consumes here must not slow the loop down, it
		 *    must only be there.  ⚠ And zero is NOT a fault: on Wayland a
		 *    still desktop delivers nothing, and that is precisely the scene
		 *    this bench wants. */
		if (capture_take(cat, 0.0, &stopped, &mistake) == CAPTURE_TAKE_DONE)
		{
			frames++;
			capture_stopped_free(&stopped);
		}
	}
	return TRUE;
}

static void print_state(const char *when)
{
	unsigned keys = 0, mouse_buttons = 0, rp = 0, rt = 0;
	uint32_t nl = 0, na = 0;
	int ready = 0;

	input_count(channel, &keys, &mouse_buttons, &rp, &rt, &ready);
	capture_negotiated_size(cat, &nl, &na);
	tell("STATE %s pronto=%d tasti_premuti=%u pulsanti_premuti=%u orfani=%u "
	     "ricambi_puntatore=%u ricambi_tastiera=%u wakeups=%lu frames=%lu "
	     "negoziata=%ux%u",
	     when, ready, keys, mouse_buttons, input_orphans(channel), rp, rt, wakeups, frames, nl,
	     na);
}

/* ⛔ Sleeps WHILE KEEPING the loop running: a plain `g_usleep` would lose the
 *    `DEVICE_REMOVED`/`DEVICE_ADDED` that arrive 8-24 ms after the wake-up, and
 *    the bench would say "no replacement" while measuring its own deafness. */
static gboolean spin_sleep(int ms)
{
	gint64 expiry = g_get_monotonic_time() + (gint64) ms * 1000;

	while (g_get_monotonic_time() < expiry)
	{
		if (!run_once())
			return FALSE;
		g_usleep(5 * 1000);
	}
	return TRUE;
}

static void command(char *line)
{
	long a1, a2;

	g_strstrip(line);
	if (!*line || line[0] == '#')
		return;

	if (g_str_equal(line, "end"))
	{
		tell("end");
		input_close(channel);
		capture_stop(cat);
		mutter_close(session);
		exit(0);
	}
	if (g_str_equal(line, "state"))
	{
		print_state("");
		return;
	}
	if (g_str_equal(line, "rilascia"))
	{
		int amount = input_release_all(channel);

		/* ⛔ THE NUMBER, so that the bench can count it — `RCP.md` §11.  ⚠ And
		 *    the orphan is printed too: "released 0" and "there was one that
		 *    could not be released" are two different facts. */
		tell("RELEASED %d (orphans left %u)", amount, input_orphans(channel));
		return;
	}
	if (g_str_equal(line, "risveglia"))
	{
		unsigned before = 0, after = 0;
		gboolean outcome;

		/*
		 * ⛔⛔ THE HEART OF THE BENCH.  The count is read BEFORE, the product
		 *      function is called, the loop runs for 400 ms — which is the
		 *      floor `child.c` puts between one wake-up and the next — and it
		 *      is read again.
		 *
		 * ⚠ The 400 ms are not a cautious wait: `[M]` §4.6 says the
		 *   replacement arrives **8-24 ms later**, and 400 is twenty times as
		 *   much.  A bench that waited 10 ms would measure its own haste.
		 */
		input_count(channel, NULL, NULL, &before, NULL, NULL);
		outcome = capture_wake(cat);
		wakeups++;
		if (!spin_sleep(400))
		{
			tell("ERRORE: the input channel dropped during the wake-up");
			exit(4);
		}
		input_count(channel, NULL, NULL, &after, NULL, NULL);
		tell("WAKE-UP n.%lu outcome=%d ricambi_puntatore %u → %u (delta %d) "
		     "⛔ and NOBODY touched the canvas",
		     wakeups, (int) outcome, before, after, (int) after - (int) before);
		return;
	}
	if (sscanf(line, "dormi %ld", &a1) == 1)
	{
		if (!spin_sleep((int) a1))
		{
			tell("ERRORE: the input channel dropped during the wait");
			exit(4);
		}
		tell("slept %ld ms", a1);
		return;
	}
	if (sscanf(line, "punta %ld %ld", &a1, &a2) == 2)
	{
		tell("punta %ld %ld -> %d", a1, a2, input_pointer(channel, (uint32_t) a1, (uint32_t) a2));
		return;
	}
	if (sscanf(line, "pulsante %ld %ld", &a1, &a2) == 2)
	{
		tell("pulsante %ld %ld -> %d", a1, a2, input_button(channel, (uint16_t) a1, (int) a2));
		return;
	}
	if (sscanf(line, "posizione %ld %ld", &a1, &a2) == 2)
	{
		tell("posizione %ld %ld -> %d", a1, a2, input_position(channel, (uint16_t) a1, (int) a2));
		return;
	}
	if (sscanf(line, "lettera %ld", &a1) == 1)
	{
		tell("lettera %ld -> %d", a1, input_letter(channel, (uint32_t) a1));
		return;
	}
	if (sscanf(line, "ritela %ld %ld", &a1, &a2) == 2)
	{
		tell("ritela %ld %ld -> %d", a1, a2,
		     input_recanvas(channel, (uint32_t) a1, (uint32_t) a2));
		canvas_w = (uint32_t) a1;
		canvas_h = (uint32_t) a2;
		return;
	}
	if (sscanf(line, "ridimensiona %ld %ld", &a1, &a2) == 2)
	{
		unsigned before = 0, after = 0;
		CaptureRecanvas outcome;

		/* ⛔ THE ALREADY KNOWN DOOR, §4.6: it serves as a comparison.  If the
		 *    replacement arrived ONLY from here, §7.1 would be false — and it is
		 *    the only way to know, because a number without its comparison does
		 *    not tell "the wake-up replaces" from "everything always replaces". */
		input_count(channel, NULL, NULL, &before, NULL, NULL);
		outcome = capture_resize(cat, (uint32_t) a1, (uint32_t) a2);
		if (!spin_sleep(400))
		{
			tell("ERRORE: the input channel dropped during the resize");
			exit(4);
		}
		input_count(channel, NULL, NULL, &after, NULL, NULL);
		tell("RESIZED to %ldx%ld outcome=%d ricambi_puntatore %u → %u (delta %d)", a1, a2,
		     (int) outcome, before, after, (int) after - (int) before);
		return;
	}
	tell("unknown command: «%s»", line);
}

int main(int argc, char **argv)
{
	g_autoptr(GError) mistake = NULL;
	g_autofree char *error = NULL;
	struct pollfd probe;
	char line[256];

	setvbuf(stdout, NULL, _IOLBF, 0);
	log_chatter(TRUE);

	for (int i = 1; i < argc; i++)
		if (!strcmp(argv[i], "--canvas") && i + 1 < argc)
			sscanf(argv[++i], "%ux%u", &canvas_w, &canvas_h);

	/* --- 1. the PRODUCT session, ConnectToEIS included -------------------- */
	session = mutter_open(&mistake);
	if (!session)
	{
		tell("ERRORE: mutter_apri: %s", mistake->message);
		return 2;
	}
	tell("session open: node %u, EIS descriptor %d", mutter_node(session),
	     mutter_eis_fd(session));

	/* --- 2. the PRODUCT CAPTURE: it is the defendant ----------------------- */
	cat = capture_start(mutter_node(session), canvas_w, canvas_h, 60, CAPTURE_ROUTE_MEMORY,
	                    CAPTURE_COLOR_BGRX, NULL, NULL, NULL, &mistake);
	if (!cat)
	{
		tell("ERRORE: cattura_avvia: %s", mistake ? mistake->message : "no reason declared");
		return 2;
	}
	{
		/* ⛔ We wait for the stream to be ACTIVE before going on: before that
		 *    moment there is no viewport, hence no absolute device, and a
		 *    wake-up would have nothing to replace. */
		gint64 expiry = g_get_monotonic_time() + 20 * G_USEC_PER_SEC;

		while (g_get_monotonic_time() < expiry && !capture_active(cat))
			g_usleep(50 * 1000);
		if (!capture_active(cat))
		{
			tell("ERRORE: the stream is not active after 20 s (%s)",
			     capture_fault(cat) ?: "no explanation");
			return 2;
		}
	}
	tell("capture active at %ux%u on node %u", canvas_w, canvas_h, mutter_node(session));

	if (mutter_find_monitor(session))
		tell("MONITOR %s («%s»)", mutter_our_monitor(session),
		     mutter_monitor_product(session));
	else
		tell("⚠ our monitor is not known by name: I do NOT say which one it is");

	/* --- 3. the input channel -------------------------------------------- */
	channel = input_open(session, canvas_w, canvas_h, &error);
	if (!channel)
	{
		tell("ERRORE: input_apri: %s", error ?: "no reason declared");
		return 3;
	}

	/*
	 * ⛔ WE WAIT FOR THE DEVICE TO BE READY, and say when it is.  Injecting
	 *    before "READY" would mean measuring a silence that is not a defect
	 *    (`04-b24-iniezione.c`, same trap).
	 */
	{
		gint64 expiry = g_get_monotonic_time() + 20 * G_USEC_PER_SEC;
		int ready = 0;

		while (g_get_monotonic_time() < expiry && !ready)
		{
			if (!run_once())
			{
				tell("ERRORE: the input channel dropped");
				return 3;
			}
			input_count(channel, NULL, NULL, NULL, NULL, &ready);
			if (!ready)
				g_usleep(50 * 1000);
		}
		if (!ready)
		{
			tell("ERRORE: no ABSOLUTE device with a region after 20 s");
			print_state("mai-pronto");
			return 3;
		}
	}
	print_state("all-avvio");
	tell("PRONTO");

	/* --- 4. the commands ---------------------------------------------------- */
	probe.fd = STDIN_FILENO;
	probe.events = POLLIN;
	for (;;)
	{
		probe.revents = 0;
		if (poll(&probe, 1, 20) < 0 && errno != EINTR)
			break;
		if (!run_once())
		{
			tell("ERRORE: the compositor closed the input channel");
			return 4;
		}
		if (probe.revents & POLLIN)
		{
			if (!fgets(line, sizeof line, stdin))
			{
				/* ⛔ A closed stdin is NOT "fine": it is the driver that went
				 *    away, and the count of what is pressed stays full.  It is
				 *    said, and we exit with a different code. */
				print_state("stdin-chiuso");
				tell("⛔ stdin closed without «fine»: I exit WITHOUT releasing");
				return 5;
			}
			command(line);
		}
	}
	tell("ERRORE: poll: %s", g_strerror(errno));
	return 4;
}
