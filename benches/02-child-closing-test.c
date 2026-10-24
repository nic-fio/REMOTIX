/* 02-child-closing-test.c — a desktop asked to end its session is «closing» for a
 * login, not «already there» (review of eab9623a).
 *
 * In the build container, from src/ (the product's objects, then the test
 * linked against all of them except main.o and child.o), as
 * 02-child-strings-test.c says:
 *
 *   make TWIN=none
 *   gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags gio-2.0 \
 *       libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 \
 *       xkbcommon wayland-client gbm) -o /tmp/ccl \
 *       ../benches/02-child-closing-test.c \
 *       $(ls *.o | grep -v -e '^main.o$' -e '^child.o$') \
 *       -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm \
 *       $(pkg-config --libs gio-2.0 libpipewire-0.3 libva libva-drm \
 *       libei-1.0 xkbcommon wayland-client gbm opus vulkan) -ldl && /tmp/ccl
 *
 * ⛔ `delivery_verdict()` in main.c called «the stage was already there»
 *    `children_pid_of() > 0`, which holds for a child that is closing: a login
 *    in that window was admitted RESUMED onto a desktop about to vanish (black,
 *    then 0x10).  Now `children_alive_of()`, and `children_terminate_session()`
 *    (§7.6 and §5.3) marks the desktop as closing:
 *
 *   1. a live child is alive;
 *   2. once its end is asked, not alive for a login — though its pid is there;
 *   3. a login then finds it «closing» (main.c: 0x0E «retry»), not the desktop;
 *   4. past CLOSING_GRACE_MS without dying it is alive again (no «retry» for ever);
 *   5. a child leaving (`exiting`) is not alive.
 *
 * ⚠ `child.c` is INCLUDED (the seam of 02-child-envelope-test.c); no child is
 *   spawned — the slot is filled by hand, and the «end» goes on a socketpair.
 *
 * Exit status: 0 green, 1 red, 3 not all checks ran. */
#define _GNU_SOURCE
#include "child.c"

#include <stdio.h>
#include <string.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 5

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

int main(void)
{
	struct children f;
	struct child g;
	int sv[2];

	setvbuf(stdout, NULL, _IONBF, 0);
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0) {
		perror("socketpair");
		return 1;
	}
	memset(&f, 0, sizeof f);
	memset(&g, 0, sizeof g);
	f.cap = 1;
	f.v = &g;
	g.used = true;
	snprintf(g.user, sizeof g.user, "anna");
	g.uid = getuid();
	g.gid = getgid();
	g.pid = 999999; /* ⚠ nobody: no signal is sent on these roads */
	g.fd = sv[0];
	g.serial = 7;
	g.showed_up = true;

	require(children_alive_of(&f, "anna"), "a live child: alive");
	require(children_terminate_session(&f, "anna", CHILDREN_EXIT_USER)
	        && !children_alive_of(&f, "anna") && children_pid_of(&f, "anna") > 0,
	        "the end asked (§7.6): not alive for a login, though its pid is there");
	/* the condition main.c's delivery_verdict() tests for «closing» (0x0E, retry) */
	require(!children_alive_of(&f, "anna") && children_pid_of(&f, "anna") > 0,
	        "a login now: «closing» (not alive, pid there) → main.c answers 0x0E «retry»");
	g.closing_asked_ms = log_now_ms() - CLOSING_GRACE_MS - 1;
	require(children_alive_of(&f, "anna"),
	        "past CLOSING_GRACE_MS without dying: alive again (no «retry» for ever)");
	g.exiting = true;
	require(!children_alive_of(&f, "anna"), "a child leaving: not alive");
	close(sv[0]);
	close(sv[1]);

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
