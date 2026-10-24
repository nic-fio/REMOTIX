/*
 * rootside_provisional.h — ⚠ LANE 2's STAND-IN FOR `rootside.h` (lane 1), 16 Oct 2026.
 *
 * ⛔ TO BE DELETED AT THE MERGE: it is included only while `rootside.h` does
 *    not exist (`#if __has_include("rootside.h")` in `main.c` and `walls.h`).
 *    It says what the network side's code (main.c, walls.c) needs of the root
 *    side, so that lane 1's header can be aligned to it — or this code to
 *    lane 1's — in one place.  The wire is `rootside_proto.h` (DECISIONS.md
 *    §11.50), and nothing here changes it.
 */
#ifndef REMOTIX_ROOTSIDE_PROVISIONAL_H
#define REMOTIX_ROOTSIDE_PROVISIONAL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "rootside_proto.h"

/* What `main.c` hands the root side after parsing argv and binding the port. */
struct rootside_options {
	int argc;                   /* the root side's own argv: the network side is */
	char **argv;                /* re-executed with `--network-side` + argv[1..] */
	int udp_fd;                 /* bound by `transport_bind()`: fd 4 over there */
	int tcp_fd;                 /* bound by `page_bind()`: fd 5 over there */
	/* ⭐ The network side's walls (`walls.h`). */
	const char *net_user;       /* "remotix" (--network-user) */
	const char *net_state_dir;  /* "/var/lib/remotix/net" (--network-state-dir) */
	const char *net_run_dir;    /* "/run/remotix/net" (--network-run-dir) */
	bool journal;               /* --journal */
	/* What the children get from the root side's argv, never from a request. */
	uint32_t canvas_w, canvas_h;
	const char *dir_survey;
	bool quality_recovery;
	uint32_t bandwidth_cap_mbit;
	bool audio_silence;
};

struct rootside_link;

/* The root side: the unit's main PID.  Returns the process's exit code. */
int rootside_main(const struct rootside_options *o);

/* The network side's end of the channel (fd 3): waits for READY (the first
 * packet, checked as the contract says), fills `ready`, NULL on failure with
 * the reason in `why`. */
struct rootside_link *rootside_attach(int fd, struct rxr_ready *ready, char *why,
                                      size_t why_len);

#endif
