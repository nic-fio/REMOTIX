/*
 * trasporto.h — THE UDP LISTENER: QUIC, and the connections that live on it.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE FIRST OF THE TWO LISTENERS (`RCP.md` §2.4)
 *
 * «7447, and they are TWO listeners with the same number: UDP for HTTP/3 and
 * WebTransport, TCP for the first load of the page.»  This file is the UDP
 * one; `pagina.h` is the TCP one.
 *
 * ⚠ And the two things are INDEPENDENT — measurement S1, `RCP.md` §2.4:
 *   WebTransport does not use `Alt-Svc` at all, it opens its connection on its
 *   own.  ⛔ The silent fallback to TCP that the plan declared as a danger
 *   CANNOT happen, because there is no fallback to make.  Whoever reads
 *   `PIANO.md` phase 1 will still find written «and the `Alt-Svc`
 *   announcement that binds them»: that line predates the measurement, and
 *   `RCP.md` §2.4 corrects it with a ⛔.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE TRANSPORT PARAMETERS THAT ARE NORMATIVE, AND WHERE THEY ARE
 *
 * `RCP.md` §2.2 and §2.3 impose on the SERVER — not on the client, which is a
 * browser and chooses its own parameters:
 *
 *   max_idle_timeout          30 s, imposed by the server (§2.2)
 *   datagram                  enabled (§2.2) — and without the transport
 *                             parameter, announcing SETTINGS_H3_DATAGRAM=1 is
 *                             a protocol error
 *   at least 16 uni streams   AVAILABLE AT ALL TIMES to the client (§2.3): their
 *                             example grants 3, and with that credit the
 *                             client would not even open the input stream —
 *                             the symptom would be «the desktop does not
 *                             respond».
 *                             ⛔ **19** are granted: the three unidirectional
 *                             ones of HTTP/3 (control + the two of QPACK) are
 *                             open from the first second and never close, so
 *                             16 as a TOTAL were 13 as availability
 *                             (finding B-12)
 *   no 0-RTT                  (§2.3) — it is in `tls.c`, where it is turned off
 *   migration not disabled    (§2.3) — `disable_active_migration` is not touched
 */
#ifndef REMOTIX_TRASPORTO_H
#define REMOTIX_TRASPORTO_H

#include "aiutante.h"

#include <openssl/ssl.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct trasporto trasporto;

/* Opens the UDP socket and prepares the stack.  `porta` is the same as TCP's.
 *
 * ⭐ `aiuto` is the PAM helper (`DECISIONI.md` §1.10), started by `main.c`
 *    BEFORE this call — so the child process inherits neither the UDP socket
 *    nor the TCP listener.  ⚠ NULL is allowed: the server checks the
 *    credentials synchronously, that is stopping the thread, and it is the
 *    declared fallback of `CODER.md` §4.2. */
trasporto *trasporto_apri(const char *indirizzo, const char *porta, SSL_CTX *ctx,
                          aiutante *aiuto);

/* ⭐ Delivers a PAM verdict to the connection that was waiting for it (§1.10).
 * ⚠ If nobody waits for it any more it writes it in the log and throws it
 *   away: it is what happens when the connection dies while PAM answers. */
/* ⭐ D-001: `ripresa` = that user's stage already existed before this verdict;
 * it travels up to `SESSIONE` (§4.5, `2 = RIPRESA`). */
void trasporto_verdetto(trasporto *t, uint64_t pratica, bool ammesso,
                        bool ripresa);
void trasporto_chiudi(trasporto *t);

int trasporto_fd(const trasporto *t);

/* ⛔ After a rotation of the session certificate the TLS context changes: the
 * connections already open keep theirs, the new ones take this one.  Whoever
 * does not redo it serves for fourteen days a certificate whose fingerprint
 * the page no longer publishes. */
void trasporto_contesto(trasporto *t, SSL_CTX *ctx);

/* The socket is readable: everything there is gets read. */
void trasporto_leggi(trasporto *t);

/* Whatever there is to write is written on all connections. */
void trasporto_scrivi(trasporto *t);

/* Milliseconds from now to the first timer that expires, or -1 if there is none.
 * ⛔ It is not «zero if there is none»: zero means «now», and confusing the two
 *    makes the loop spin idle burning a CPU. */
int trasporto_attesa_ms(const trasporto *t);

/* Expires the ripe timers (QUIC's and ours) and writes again. */
void trasporto_scaduti(trasporto *t);

/* How many connections are alive.  For the log. */
size_t trasporto_quante(const trasporto *t);

/* ⛔ §8.1 — «never with a silence»: sends `CONGEDO` with the reason to all live
 * sessions and closes each one with the reason's code (§3.1 point 3).  It is
 * called by whoever shuts the server down, with `RCP_SERVER_IN_CHIUSURA` (§8.2,
 * `0x0C`).
 *
 * ⭐ Returns how many connections still have bytes to get out: whoever shuts
 *    down runs the loop until it is zero (or until its patience runs out),
 *    because «handed to ngtcp2» is not «out on the wire». */
const char *trasporto_perche_restano(const trasporto *t);
size_t trasporto_congeda_tutte(trasporto *t, uint8_t motivo, const char *perche);

#endif
