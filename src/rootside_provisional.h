/*
 * rootside_provisional.h — ⚠ LANE 2's STAND-IN FOR `rootside.h` (lane 1), 16 Oct 2026.
 *
 * ⛔ TO BE DELETED AT THE MERGE: it is included only while `rootside.h` does
 *    not exist (`#if __has_include("rootside.h")` in `main.c` and `walls.h`).
 *    It copies the part of lane 1's `rootside.h` (c788d3c6) that main.c and
 *    walls.c use, word for word, PLUS the two fields lane 2 needs and lane 1's
 *    struct lacks — marked «LANE 2 ADDS» below: the walls' two writable
 *    directories (bench runs pass their own, `--network-state-dir`/
 *    `--network-run-dir`).  The wire is `rootside_proto.h`, unchanged.
 */
#ifndef REMOTIX_ROOTSIDE_PROVISIONAL_H
#define REMOTIX_ROOTSIDE_PROVISIONAL_H

/* (the original includes rootside_proto.h; only an opaque pointer to its struct is used here, so the
 * stand-in compiles on its own — the real rootside.h, when it exists, brings the wire header) */
struct rxr_ready;

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

#define ROOTSIDE_FD_CHANNEL 3
#define ROOTSIDE_FD_UDP     4
#define ROOTSIDE_FD_TCP     5

struct rootside_options {
	int udp_fd;
	int tcp_fd;
	uid_t remotix_uid;
	gid_t remotix_gid;
	int cap;
	uint32_t canvas_w, canvas_h;
	const char *dir_survey;
	bool quality_recovery;
	uint32_t bandwidth_cap_mbit;
	bool audio_silence;
	const char *encoding_route;
	const char *render_node;
	char *const *net_argv;
	const char *denied_users_path;
	/* ⭐ LANE 2 ADDS: the only two directories the network side may write
	 *    behind its walls (`walls.h`); absolute, owned by `remotix_uid`. */
	const char *net_state_dir;   /* "/var/lib/remotix/net" */
	const char *net_run_dir;     /* "/run/remotix/net" */
};

int rootside_main(const struct rootside_options *o);
int walls_apply(const struct rootside_options *o, char *why, size_t why_len);
bool rootside_attach(int fd, int timeout_ms, struct rxr_ready *ready);
bool rootside_lost(void);

#endif
