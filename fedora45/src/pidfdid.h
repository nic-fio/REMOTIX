/* pidfdid.h — THE EXACT IDENTITY OF A PROCESS, from two pidfds (1.5, strengthening of the split's wall for the child's messages).
 *
 * ⛔ Why: the network side lives in a PID namespace of its own, and a child born OUTSIDE it is stamped by the kernel with pid 0 on every
 *    message (`SCM_CREDENTIALS`), so the wall in child.c cannot compare the sender's pid with the child's: it relies on the socket, the
 *    uid, the gid and the serial.  On a kernel that has pidfs (6.9) it can be exact: the root side, which forked the child, hands the
 *    network side a PIDFD of it together with the child's socket, and the kernel attaches to each message a pidfd of its SENDER
 *    (`SO_PASSPIDFD` + `SCM_PIDFD`, 6.5/6.9).  A pidfd names a `struct pid`, whatever the namespace; on pidfs two pidfds of the same process
 *    have the same inode, and the inode of another process is different.
 *
 * ⚠ ONLY on pidfs.  Before 6.9 (6.5-6.8 have the pidfd but not pidfs) every pidfd is an anonymous inode and all have the same
 *    `st_ino`: comparing them would say «same» for ANY two — so there the answer is UNKNOWN and the wall keeps today's rule.  The same
 *    when either descriptor is missing.  UNKNOWN is never an error: it is the old behaviour.
 *
 * A header with static inline functions and no dependency but the C library, so that `benches/unit/pidfd-identity` tests it alone. */
#ifndef REMOTIX_PIDFDID_H
#define REMOTIX_PIDFDID_H

#include <stdbool.h>
#include <sys/stat.h>
#include <sys/vfs.h>

#ifndef SO_PASSPIDFD
#define SO_PASSPIDFD 76 /* Linux 6.5 */
#endif
#ifndef SCM_PIDFD
#define SCM_PIDFD 0x04 /* Linux 6.5 */
#endif
#ifndef PID_FS_MAGIC
#define PID_FS_MAGIC 0x50494446 /* "PIDF", Linux 6.9 */
#endif

enum pidfd_same {
	PIDFD_UNKNOWN,  /* one is missing, or the kernel has no pidfs: the rule of today */
	PIDFD_SAME,     /* the same process */
	PIDFD_DIFFERENT /* another process: the message is not the child's */
};

static inline bool pidfd_on_pidfs(int fd)
{
	struct statfs sf;

	return fd >= 0 && fstatfs(fd, &sf) == 0 && (unsigned long)sf.f_type == (unsigned long)PID_FS_MAGIC;
}

static inline enum pidfd_same pidfd_compare(int expected, int sender)
{
	struct stat a, b;

	if (expected < 0 || sender < 0 || !pidfd_on_pidfs(expected) || !pidfd_on_pidfs(sender))
		return PIDFD_UNKNOWN;
	if (fstat(expected, &a) != 0 || fstat(sender, &b) != 0)
		return PIDFD_UNKNOWN;
	return a.st_dev == b.st_dev && a.st_ino == b.st_ino ? PIDFD_SAME : PIDFD_DIFFERENT;
}

#endif
