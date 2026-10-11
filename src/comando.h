/*
 * comando.h — ⛔⭐ THE UNBLOCK COMMAND OF `RCP.md` §4.4-bis.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY A CONTROL SOCKET, AND NOT A COMMAND-LINE OPTION
 *
 * §4.4-bis wants «an unblock command on the server», «the way out for whoever
 * bans themselves from their own phone», which «asks for the only key that case
 * admits — access to the machine», and which writes every unblock in the log,
 * telling a removed ban from a ban that never triggered.  The possible forms
 * are three and two do not hold:
 *
 *   ⛔ a SECOND PROCESS with an option (`remotix` run again to unblock) — **it does not
 *      work**, and the way it does not work is silent: the ban lives in the
 *      memory of the serving process (`rcp.c`, `static … attempts[]`), and a
 *      second process can only rewrite the file.  The server would keep
 *      answering `TOO_MANY_ATTEMPTS` until restart, and ⛔ the first
 *      `save_ban()` — that is, the first ban of anyone else — would rewrite
 *      the file putting back in it the ban just removed.  ⚠ And whoever gave
 *      the command saw it **exit with zero**;
 *   ⛔ a SIGNAL — it carries no address, and above all it has no answer:
 *      §4.4-bis wants «was not banned» and «I removed it» to be told apart, and
 *      a delivered signal only says that it was delivered;
 *   ⭐ a CONTROL SOCKET — it carries the address, acts on the LIVE process
 *      (memory and file in the same line, by the hand of `rcp_unblock()`), and
 *      **answers**, so the two answers really exist.  The key it asks for is a
 *      file with `0600` permissions on the machine's filesystem, that is
 *      exactly «access to the machine» — and it adds no surface reachable from
 *      the network: a Unix domain socket has no IP address.
 *
 * ⛔ Until the night of 10 Aug 2026 this file did not exist and `main.c`
 *    implemented the FIRST form, the one that does not work: finding R12.1 of
 *    the seam review, and the full analysis is written — by the hand that
 *    grafted the bench host — in `banchi/01-b3-rcp-innesta.py`.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE PROTOCOL IS ONE LINE, AND IT CAN BE READ WITHOUT TOOLS
 *
 *     UNBLOCK <address>    →  REMOVED <key>           the ban was there and is gone
 *                          →  NOT-BANNED <key>     there was nothing to remove
 *     PING                 →  PONG                  «does the command exist?», and
 *                                                   touches nothing
 *     (other)              →  NOT-UNDERSTOOD <line>
 *
 * ⭐ `PING` is not an ornament: it is the denominator of rule B0.3 of
 *    `FASI.md` §01-filo-nudo.  A bench that calls the unblock between one test
 *    and the next must be able to say «the command was there and answered», or
 *    «the ban did not trigger» and «the unblock never reached anyone» look the
 *    same.
 *
 * ⭐ It is the same protocol, byte for byte, spoken by `banchi/01-b8-sblocca.py`
 *    — which is the tool of B0.3 and not a piece of B8.  Having two would have
 *    been form E2 of `REVIEWER.md`: two behaviours under the same label.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ AND `PING` SAYS «SOMEONE ANSWERS», NOT «THE RIGHT ONE ANSWERS»
 *
 * *Observed on 11 Aug 2026, the first time someone pointed `01-b8-sblocca.py`
 * at a server different from the one that had the ban.*
 *
 * On this machine there are **two** servers — the `bsslserver` graft on 7447
 * and this product on 7448 — and each has its own socket.  ⛔ Whoever picks the
 * wrong socket receives `PONG` and then `NOT-BANNED`, that is the two most
 * reassuring answers of the protocol, while the ban they wanted to remove is
 * alive in the other process.  It is the new face of the third outcome: **I
 * talked to a server, but not to THAT one** — and unlike the other three
 * (socket missing, nobody listening, permission denied) this one **answers**,
 * so it cannot be seen.
 *
 * ⛔ NO VERB WAS ADDED, and the reason must be written because it is the
 *    obvious temptation.  A `CHI` → `SONO remotix <pid>` would have put the
 *    identity **inside the protocol**, and there two things go wrong together:
 *
 *      1. `RCP.md` §4.4-bis and `FASI.md` §01-filo-nudo B0.3 promise that the
 *         two servers speak the same protocol **byte for byte**.  A verb that
 *         only one of the two understands breaks it, and it is form E2 of
 *         `REVIEWER.md` precisely at the point this box exists not to repeat;
 *      2. ⛔ and whoever would answer `CHI` would be the server: that is, the
 *         identity would be asked **of the suspect**.  `CODER.md` §3.7 says the
 *         opposite — *«the sender is not deduced: it is asked of the kernel»*.
 *
 * ⭐ The right road is outside the protocol and costs this file not one line:
 *    a Unix domain socket carries the credentials of whoever listens, and
 *    `getsockopt(SO_PEERCRED)` hands them to whoever connects — pid, uid, gid,
 *    from the kernel.  From there `/proc/<pid>/comm` says `remotix` or
 *    `bsslserver`.  `01-b8-sblocca.py` does it: it always prints who answered
 *    and can demand it (`--expect-name`, `--expect-pid`).
 *
 * ⚠ And the other half of the ban — the **file** that survives restart — this
 *   module cannot look at: `rcp_unblock()` calls `save_ban(NULL, …)`, which
 *   with the session at `NULL` stays silent on every fault, and `ban_path`
 *   is `static` inside `rcp.c`.  ⛔ So here it is never declared that the file
 *   was written: it is said that it was **requested**.  Whoever measures looks
 *   at it from outside — `01-b8-sblocca.py --ban-file`, which reads it before
 *   and after.  ⭐ The real cure would be in `rcp.c`: `rcp_unblock()` must be
 *   able to say whether it wrote the file.
 */
#ifndef REMOTIX_COMMAND_H
#define REMOTIX_COMMAND_H

#include <poll.h>
#include <stddef.h>

typedef struct command command;

/* Opens the socket.  ⛔ Returns NULL on any fault, and WRITES it: without the
 * unblock command the protection of §4.4-bis is still there — the only way out
 * is the twelve hours — so whoever starts the server goes on, but the missing
 * half must be readable in the log. */
command *command_open(const char *fpath);
void command_close(command *k);

/* Like `pagina_*`: the descriptor is put in the `poll` and whatever moved is
 * moved. */
size_t command_descriptors(command *k, struct pollfd *dove, size_t cap);
void command_move(command *k, struct pollfd *dove, size_t amount);

#endif
