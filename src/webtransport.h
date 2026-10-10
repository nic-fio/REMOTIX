/*
 * webtransport.h — ⭐ THE WEBTRANSPORT LAYER, AND RCP ON TOP.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY THIS FILE EXISTS
 *
 * `DECISIONI.md` §6.4: of the four candidates `ngtcp2`+`nghttp3` remains, and
 * ⛔ **neither of the two brings server-side WebTransport**.  They give the
 * foundations — RFC 9220's extended CONNECT, datagrams, the Capsule Protocol —
 * and not the layer above.  This file IS the layer above, and it is the glue
 * §6.4 wanted to know before choosing.
 *
 * The three holes it covers, which are the three points this file touches:
 *
 *   1. ⛔ **WebTransport cannot be announced.**  `nghttp3_settings` has
 *      `enable_connect_protocol` and `h3_datagram` — the two that are in the
 *      RFCs — and nothing else; there is no way to put an arbitrary setting
 *      on the control stream.  `SETTINGS_WT_MAX_SESSIONS`, which is what the
 *      browsers look for, does not go through there.  ⛔ We rewrite the
 *      SETTINGS nghttp3 is writing, while it writes it.
 *
 *   2. ⛔ **WebTransport streams must be taken away from nghttp3.**  They
 *      start with frame type `0x41` followed by the session number, and
 *      nghttp3 would read that number as a LENGTH.
 *
 *   3. ⛔ **And the bytes going back have no road.**  nghttp3 does not know
 *      those streams, so it will never put them among the vectors to write:
 *      the output queue is ours.
 *
 * ⚠ None of the three is a defect of ngtcp2 or of nghttp3: they do HTTP/3,
 *   and WebTransport is not HTTP/3.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE DECLARED PRICE, AND IT MUST BE RE-TESTED AT EVERY NGHTTP3 UPDATE
 *
 * Point 1 depends on the SHAPE OF THE BYTES nghttp3 writes, not on an API
 * promise of its own.  `DECISIONI.md` §6.4 declares it: «must be re-tested at
 * every nghttp3 update».  The guard is in `riscrivi_impostazioni()`: if the
 * bytes are not the expected ones nothing is rewritten, the log says so, and
 * the server stays without WebTransport — a loud fault instead of a control
 * stream out of step.
 *
 * ---------------------------------------------------------------------------
 * ⭐ WHAT CHANGED GOING FROM THE GRAFT TO THE PRODUCT
 *
 * The graft (`banchi/01-b2-ngtcp2-wt-innesta.py`) moved RCP's time forward
 * with **QUIC keep-alive**, that is by putting bytes on the wire every 100 ms:
 * it was the only clock a host example offered it, and its comments declare
 * it — «a real server will arm its own timer and will put nothing on the
 * wire».  ⭐ Here the server is ours and the timer is ours: `wt_battito_ns()`
 * tells the loop when to come back, and nothing goes on the wire to move
 * RCP's time forward.  `RCP.md` §2.2 forbids an application heartbeat, and
 * there is not even a shadow of one.
 *
 * ⛔⭐ AND THIS BOX WAS HALF WRONG — finding B-2, corrected on the night of
 *     10 August 2026.  It presented the TOTAL absence of bytes on the wire as
 *     an improvement over the graft, citing §2.2.  ⛔ But §4.6 — box R1.8,
 *     normative — requires the server to send **transport PINGs** while it
 *     waits for the credentials, and explicitly tells the two apart: PINGs
 *     «carry no information, have no answer to interpret, and do not create
 *     a second truth about silence (§2.2)».  The ban of §2.2 does NOT cover them.
 *
 *     ⚠ Without them, the 60 seconds §4.6 gives to type the password are
 *       UNREACHABLE: at the thirtieth QUIC idleness fires and the connection
 *       dies in silence.  Our clock is not enough because it does not put a
 *       byte on the wire, and what kills the connection looks at bytes.  See
 *       `regola_tienila_viva()` in `webtransport.c`.
 */
#ifndef REMOTIX_WEBTRANSPORT_H
#define REMOTIX_WEBTRANSPORT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "aiutante.h"

#include <nghttp3/nghttp3.h>
#include <ngtcp2/ngtcp2.h>

typedef struct wt wt;

/* ⭐ `aiuto` is the PAM helper (`DECISIONI.md` §1.10): a single one for the
 * whole server, and this layer receives it without owning it.  ⚠ NULL is
 * allowed and means «synchronous check», that is the declared fallback — the
 * server works all the same, with the wire stopping. */
wt *wt_nuovo(ngtcp2_conn *conn, ngtcp2_ccerr *ultimo_errore,
             const char *provenienza, aiutante *aiuto);

/* ⭐ PAM's verdict coming back from the helper.  ⛔ `true` if this connection
 * was the one waiting for that request: the caller hands it to all of them,
 * and only one takes it. */
/* ⭐ D-001: `ripresa` = that user's stage already existed (`SESSIONE` will say
 * `2 = RIPRESA`, §4.5). */
bool wt_verdetto(wt *w, uint64_t pratica, bool ammesso, bool ripresa);
/* ⭐ D-001: the desktop name for `SESSIONE` (`gnome · kde · xfce · lxqt ·
 * sconosciuto`), one per process — `main.c` sets it at startup. */
void wt_desktop(const char *nome);
void wt_libera(wt *w);

/* The calls the transport forwards here.  They return 0 or an ngtcp2 error
 * (negative) to propagate. */
int wt_app_pronta(wt *w); /* the application key is ready: HTTP/3 opens */
int wt_ricevi_stream(wt *w, uint32_t flags, int64_t stream_id,
                     const uint8_t *dati, size_t len);
int wt_stream_chiuso(wt *w, int64_t stream_id, uint64_t codice, bool con_codice);
int wt_stream_reset(wt *w, int64_t stream_id);
int wt_stream_stop_sending(wt *w, int64_t stream_id);
int wt_ack_stream_data(wt *w, int64_t stream_id, uint64_t len);

/* ⭐⭐ The outcome of a DATAGRAM, which until 23 Aug 2026 was mute.
 *
 *    `trasporto.c` calls them from ngtcp2's `lost_datagram` and
 *    `ack_datagram` callbacks.  ⛔ And they are needed as a PAIR, not one
 *    alone: `ngtcp2.h:3442` warns that a datagram loss can be **spurious** —
 *    declared and then acknowledged.  ⇒ The same `id` seen first as lost and
 *    then as acknowledged **is not a loss: it is an out-of-order packet**,
 *    and it is the only number the server can give about reordering (phase 9,
 *    §3.1-ter).  Recording only `lost_datagram` would count those reorderings
 *    as losses, that is it would give a number **higher than the truth** and
 *    without saying so. */
void wt_dgram_perso(wt *w, uint64_t id);
void wt_dgram_riscontrato(wt *w, uint64_t id);
int wt_estendi_max_stream_data(wt *w, int64_t stream_id);
int wt_estendi_max_streams_bidi(wt *w, uint64_t max_streams);

/* ⭐ Writes ONE packet: it is the point where the WebTransport layer does the
 * two things nghttp3 cannot do.  It is called by the callback the transport
 * passes to `ngtcp2_conn_write_aggregate_pkt2`.
 *
 * ⛔ And the `wt *` is passed by the transport, not by ngtcp2: the
 *    `user_data` of that callback is the CONNECTION's, not ours.  ⚠ Taking
 *    one for the other compiles without a word — they are two `void *` — and
 *    produces a server that opens HTTP/3 and then dies at the first write
 *    with `ERR_CALLBACK_FAILURE`, that is a symptom that names neither of the
 *    two pointers.  `[M]` 10 Aug 2026, first power-on against the test
 *    client. */
ngtcp2_ssize wt_scrivi(wt *w, ngtcp2_path *path, ngtcp2_pkt_info *pi,
                       uint8_t *dest, size_t destlen, ngtcp2_tstamp ts);

/* ⭐ OUR OWN CLOCK, in place of the graft's keep-alive.
 * Returns the instant (in ngtcp2's scale, nanoseconds) at which this layer
 * wants to be called back, or UINT64_MAX if it does not need it. */
ngtcp2_tstamp wt_battito_ns(const wt *w);
/* Moves RCP's time forward and matures the deferred close.  To be called
 * when `wt_battito_ns()` has passed. */
void wt_batti(wt *w, ngtcp2_tstamp ts);

/* ⛔⭐ §5.3 — «the client is still there».  `trasporto.c` calls it after every
 *     packet ngtcp2 has ACCEPTED, and it is the only thing that moves when
 *     the user watches and touches nothing. */
void wt_segno_di_vita(wt *w, ngtcp2_tstamp ts);

/* ⛔ §8.1 — whoever closes MUST send `CONGEDO` with the reason and repeat it
 * in the close code, «never with a silence».  The transport calls it when the
 * server shuts down: `RCP_SERVER_IN_CHIUSURA` (§8.2, `0x0C`).  Finding B-7. */
void wt_congeda(wt *w, uint8_t motivo, const char *dettaglio);

/* ⛔ «Does it still have something to say?» — lets whoever shuts down the
 * server know when it has finished sending out the farewells, instead of
 * counting loop turns. */
bool wt_ha_da_dire(const wt *w);
/* ⛔ Why it still has something to say: «capsule not mature» and «queue not
 *    empty» are two different faults, and at shutdown they looked the same. */
const char *wt_perche_ha_da_dire(const wt *w);

/* ⭐⭐ PHASE 3 — THE FRAME LOOP, AND WHERE THE BOUNDARY RUNS.
 *
 * ⛔ `wt_video_deposita()` WAS HERE, AND IT HAS BEEN REMOVED.  It deposited
 *    ONE frame per codec, **per process**, marked keyframe by construction,
 *    and this layer sent it only once per session (`bool video_fatto`).
 *    Three defects in one function, and all three of phase 3: the per-process
 *    deposit handed a session the pixels of another user (`[M]` 12 Aug 2026,
 *    invariant I3); the `chiave = true` by construction would have become
 *    **a lie on the wire** as soon as deltas existed (§6.2, field `tipo`);
 *    and the `bool` stopped the loop at the first frame.
 *
 * ⇒ Now frames ARRIVE, one after the other, from the child of the user that
 *   captures and encodes them (`figlio.h`), and `main.c` forwards them here.
 *
 * ⛔ `utente` is NOT a label: it is invariant I3 on the wire.  The frame goes
 *    **only** to the sessions PAM admitted for that user, and the comparison
 *    is done here because here we know who each session is.
 *
 * `codec` is the one of `RCP.md` §4.3/§6.2 — **1 = HEVC, 2 = AV1**, the same
 * numbers and not a translation.  `chiave` is the TRUE type read from the
 * stream by the encoder, not a guess: §6.2 writes it in the field `tipo`.
 * `istante_us` is the server's MONOTONIC clock at capture (§6.2): it is not
 * a time of day, and the client does not compare it with its own.  `input`
 * is §7.3.
 *
 * ⚠ The bytes are COPIED into each session's queue: whoever captures can
 *   free its buffer right after. */
/* ⭐⭐ PHASE 4 — THE CURSOR SHAPE TO WHOEVER WATCHES (`RCP.md` §7.2).
 *
 * ⚠ The twin of `wt_video_diffondi()`, and for the same reason: the shape is
 *   born in the child of ONE user, and goes to all the sessions of THAT user
 *   — which can be more than one (I4: the stage belongs to the session, not
 *   to the connection).
 * ⛔ `0x0` with `immagine` NULL = hidden cursor, and it is sent: it is the
 *    only way the client has to know the pointer has disappeared. */
void wt_cursore_diffondi(const char *utente, uint16_t larghezza,
                         uint16_t altezza, int16_t attivo_x, int16_t attivo_y,
                         const uint8_t *immagine, size_t byte);

void wt_video_diffondi(const char *utente, uint8_t codec, bool chiave,
                       const uint8_t *dati, size_t byte, uint32_t larghezza,
                       uint32_t altezza, uint64_t istante_us, uint32_t input);

/* ⛔⭐ THE MISSING SEAM — point 4 of phase 3.
 *
 *     `rcp_video_serve_chiave()` was READ and served no purpose, because
 *     `codificatore_chiedi_chiave()` had **no caller in the product**: a
 *     client `RICHIEDI_CHIAVE` set a `bool` and produced no keyframe.  With
 *     `chiavi_ogni = 0` (infinite GOP), after the first keyframe **not one
 *     more ever arrived**, and the screen stayed frozen.
 *
 * ⇒ The stage lives in another process, and this is the hook that crosses
 *   the boundary.  This layer calls it when:
 *     · a session reaches `SESSIONE` and the codec is negotiated
 *       ⇒ `acceso = true`, `chiave = true` (§5.2: the first MUST be a keyframe);
 *     · §5.2 wants a keyframe (requested by the client, delta abandoned,
 *       canvas changed) ⇒ `chiave = true`;
 *     · the last session of that user goes away ⇒ `codec = 0`, that is
 *       «stop capturing».  ⚠ The stage (I4) stays up: only the frame loop
 *       stops. */
/* ⛔⭐⭐ `profondita` ARRIVED ON 17 AUG 2026, and it is not one more field:
 *      it is the cure for a measured defect.  The codec crossed this
 *      boundary and the depth did NOT — the child wrote it by itself (`10`,
 *      a literal), and the stream came out at 10 bits while `ECCOMI`
 *      declared 8.  ⚠ On Chrome+HEVC it did not show (the decoder
 *      reconfigures from the stream); on Firefox+AV1 the desktop FROZE.
 * ⚠ `0` = not negotiated: the receiver must NOT pick one on its own. */
/* ⛔⭐⭐ `livello_x10` ARRIVED ON 23 AUG 2026, and for exactly the same reason
 *      as the depth: `[M]` at 3840x2160 the client declared
 *      `video.livello=5.1` and the server produced **5.2** — §4.3 line 701 is
 *      a MUST, and the symptom of an exceeded level is not an error but a
 *      decoder that REFUSES the configuration.  ⚠ In tenths (`5.1` ⇒
 *      51); `0` = the client did not declare it, that is NO CAP — and it
 *      does not mean «low». */
typedef void (*wt_video_richiesta)(void *ctx, const char *utente, uint8_t codec,
                                   uint8_t profondita, uint8_t livello_x10,
                                   bool chiave);
void wt_video_gancio(wt_video_richiesta f, void *ctx);

/* ⭐⭐ PHASE 4 — THE INPUT BRIDGE, and it crosses a PROCESS boundary.
 *
 * ⛔ Who knows the user pressed: `rcp.c`, which validated the message of
 *    `RCP.md` §7.3.  Who knows which session it belongs to: this module.
 *    ⛔ Who can really inject it: the **child**, which runs as the user and
 *    is the only one holding the graphical session — that is another process.
 *    `main.c` acts as a bridge because it is the only one that knows both sides.
 *
 * ⚠ `true` means «delivered to the stage», NOT «the compositor took it»:
 *   the answer does not come back across the process boundary.  ⭐ Whoever
 *   counts what the compositor really took is the child, which stamps it on
 *   the frame (§6.2, field `input`) — and it is the only place where that
 *   number is the truth instead of a promise.
 *
 * `azione` are the `FIGLI_INPUT_*` of `figlio.h`. */
typedef bool (*wt_input_richiesta)(void *ctx, const char *utente, uint32_t id,
                                   uint8_t azione, uint16_t codice, int premuto,
                                   int32_t a, int32_t b);
void wt_input_gancio(wt_input_richiesta f, void *ctx);

/* ⭐⭐ THE CANVAS BRIDGE — `RCP.md` §7.1, `DECISIONI.md` §5.0-sexies.
 *
 * ⛔ IT IS SEPARATE FROM THE INPUT ONE, and not for symmetry: an input is an
 *    already validated gesture that is injected and forgotten, and its
 *    outcome is of no use to anyone on the wire.  This is a request to
 *    **reconfigure the stage** whose answer arrives **from somewhere else** —
 *    with a frame, tens of milliseconds later or never — and which the client
 *    is waiting for (§7.1: «to every `ADATTA_TELA` the server MUST answer
 *    with a `TELA`»).
 *
 * ⚠ `true` = the request has left towards the child.  ⛔ NOT «the canvas
 *   has changed»: that will be said by `rcp_tela_concessa()`, when the pixels
 *   arrive at the new size. */
typedef bool (*wt_ritela_richiesta)(void *ctx, const char *utente,
                                    uint32_t larghezza, uint32_t altezza);
void wt_ritela_gancio(wt_ritela_richiesta f, void *ctx);

/* ⭐ §5-bis.7 — the layout to the stage of WHOEVER ASKED. */
typedef bool (*wt_disposizione_richiesta)(void *ctx, const char *utente,
                                          const char *nome);
void wt_disposizione_gancio(wt_disposizione_richiesta f, void *ctx);

/* ⭐⭐ §5.1 — THE GUARD OF LOCAL GRAPHICAL SESSIONS, and it serves TWO things
 *     that look like one and are not:
 *
 *   · ⛔ whoever **arrives** and already has a local one ⇒ refused,
 *     `0x05 GIA_ATTIVA_LOCALE` — `rcp.c` asks the question once, at `ATTACCA`;
 *   · ⛔ whoever **is already there** and opens a local one ⇒ the local one
 *     WINS and the remote one drops, `0x04 SESSIONE_LOCALE_PREVALSA` — and
 *     nobody asks this one: it must be **watched over**, and it is
 *     `wt_sorveglia_locali()`.
 *
 * ⚠ The two codes have been in `rcp.h` since 9 Aug 2026 and until the 15th
 *   **no line of any `.c` sent them** (finding B-7, the same shape).
 *
 * `quale` — if not NULL — receives which session it is, **for the server's
 * log**: §8.2 does not allow telling the client the facts of other people's
 * sessions, and indeed it does not end up in the farewell body. */
typedef bool (*wt_locale_richiesta)(void *ctx, const char *utente, char *quale,
                                    size_t quanto);
void wt_locale_gancio(wt_locale_richiesta f, void *ctx);

/* ⭐⭐⭐ THE SWEEP HOOK — **a single question for all tenants**.
 *
 * ⛔⛔ Why it is separate from the one above, and it is not symmetry: the one
 *      above is the `ATTACCA` question, asked **once per session**, and there
 *      the cost does not show.  This is the SWEEP, which runs every two
 *      seconds inside the loop that delivers frames — and there the cost
 *      shows all right: `[M]` §6.13, at **N=7 tenants with logind at 286 ms**
 *      every desktop collapsed to **1.3 frames/s with a p95 of two seconds**,
 *      and nobody was detached, so **not one line was written**.
 *
 * ⭐ The shape is the one the cost imposes: ALL the names are passed and ALL
 *    the answers received, so the layer below can answer with a single call
 *    (`sentinella_locali()`, which does so).  ⛔ A hook per name would not
 *    allow it **to any** implementation, however clever.
 *
 * `quali` — if not NULL, `quanti` slices of `larghezza` bytes, for the LOG.
 * Returns how many tenants have a local graphical session. */
typedef size_t (*wt_locali_ripasso)(void *ctx, const char *const *utenti,
                                    size_t quanti, bool *locale, char *quali,
                                    size_t larghezza);
void wt_locali_gancio(wt_locali_ripasso f, void *ctx);

/* The sweep: asks the guard — **in a single question** — which of the
 * attached users have opened a local graphical session, and sends those a
 * farewell with `0x04`.  Returns how many it sent away.  ⚠ Without the hook
 * it does nothing and does not complain: `rcp.c` already complained at
 * attach, once. */
size_t wt_sorveglia_locali(void);

/* ⛔⭐ HOW MANY SERVED USERS THERE ARE NOW — 25 Aug 2026, finding R7 of §5.5.
 *
 *     `sentinella.h` promised, above `sentinella_conti()`, that `main.c`
 *     would write its two numbers *«next to the number of served
 *     tenants»*.  ⛔ That number **was not** in the line, and it is precisely
 *     the DENOMINATOR: without `N`, «one call per SWEEP and not per tenant»
 *     can be neither verified nor **refuted** — with a single tenant the two
 *     shapes give the same count.
 *
 * ⚠ It is counted here and not in `rcp.c` because the transport is what
 *   knows which connections are alive and authenticated, and it is the same
 *   list the sweep walks: two different counts of the same thing would be
 *   two truths.
 * ⛔ A connection without an RCP session, without a user or closing is NOT
 *    counted: it is not a served tenant, it is someone knocking or leaving. */
size_t wt_inquilini_serviti(void);

/* ⛔⭐⭐⭐ THE SERVICE CLOCK — «the time we did not run is not the client's
 *        silence».  `main.c` calls it at every pass of the loop.
 *
 * ⛔ THE DEFECT IT REMOVES, measured: the dead line judges on two quantities —
 *    the video bytes SENT and the packets RECEIVED from the client — and both
 *    can move **only while the parent's loop runs**.  A stopped loop (a slow
 *    synchronous call, a blocked child leaving bytes stuck in the parent's
 *    queue, `[M]` §6.7: a 5 s `SIGSTOP` to ONE child killed **all four**
 *    sessions) freezes both, and the cure read that freeze as *«the line is
 *    DEAD»* — that is it **blamed the user's network for a blindness of
 *    ours**, with `persi=0` written next to it.
 *
 * ⭐ The remedy is not a parallel clock to keep in agreement with the first:
 *    it is that a gap in the loop counts as PROGRESS — the counts restart,
 *    and the line says so.  ⇒ The price, declared: a really dead client is
 *    recognised at most **one threshold later**.  Erring high costs a few
 *    seconds of frozen screen; erring low throws out someone who is working,
 *    and that cannot be undone (the same asymmetry that chose the 5.0 s of
 *    the stall). */
void wt_giro_del_padre(uint64_t ora_ms);

/* How many times the parent's loop fell behind, and the worst gap in
 * milliseconds.  ⛔ It is the number that makes the cure above FALSIFIABLE:
 * if it were always zero, that cure would never have done anything and it
 * would show; if it is large, the defect is in the loop and must be cured
 * there, not here. */
void wt_giri_fermi(uint64_t *quanti, uint64_t *peggiore_ms);

/* ⭐⭐ §7.6 — «THE USER ASKED TO LOG OUT», and it is not the farewell.
 *
 * ⛔ The farewell leaves the session alive (I4); this ENDS it, and with it
 *    the user's programs close.  Whoever receives it must terminate the
 *    graphical session of THAT user — the name is set by this module, which
 *    knows whom PAM admitted on that connection, and does not come from the
 *    wire (I3). */
typedef void (*wt_termina_richiesta)(void *ctx, const char *utente);
void wt_termina_gancio(wt_termina_richiesta f, void *ctx);

/* Sends a farewell to all the sessions of a user, skipping `tranne` (which
 * is usually the one that has just asked, already sent away by `rcp.c`).
 * Returns how many.  ⛔ It serves §7.6: the graphical session is ONE (I2),
 * so whoever was watching it from a second device would be left with a
 * frozen screen forever. */
size_t wt_congeda_utente(const char *utente, uint8_t motivo, const char *dettaglio,
                         const wt *tranne);

/* ⭐ The canvas cap that the sessions of that user can decode —
 *    `video.misura_massima` of §4.3, the widest if there is more than one.
 * ⛔ It serves the BUDGET (phase 10): at `consegna_verdetto()` the canvas is
 *    not yet decided, but its UPPER BOUND is known from `CIAO` on, and the
 *    budget counts the upper bound.  ⚠ `false` = none declared it — and it
 *    is not «zero»: the caller falls back on the stage's canvas, not on a
 *    zero cost. */
bool wt_misura_massima_di(const char *utente, uint32_t *l, uint32_t *a);

/* ⭐ §7.1 — «the stage is not there YET»: postpones the three-second backstop
 * on that user's sessions that are waiting for exactly that size.  ⛔ It sends
 * nothing on the wire: it moves a deadline, and removes a deduction from the
 * parent (`LEZIONI.md` §7.5). */
void wt_tela_rimanda(const char *utente, uint32_t voluta_l, uint32_t voluta_a);

/* ⭐⭐ AND THE ANSWER COMES BACK THROUGH HERE — §7.1.  The child sends it
 *     (`FiglioTela`) and `main.c` carries it here, because this module is
 *     the one that knows which sessions belong to that user.
 *
 * ⛔ `avuta_l == 0` = the stage did not make it ⇒ `TELA(NON_ORA)` at once,
 *    instead of the three seconds of the §7.1 backstop. */
void wt_tela_dal_palco(const char *utente, uint32_t voluta_l, uint32_t voluta_a,
                       uint32_t avuta_l, uint32_t avuta_a);

/* ⛔ That user's stage is gone: its size is forgotten.
 * ⚠ «I don't know» and «it was 1920x1080» are two different facts, and the
 *   second — when false — makes the reattach grant a canvas no frame will have. */
void wt_palco_dimentica(const char *utente);

/* ⛔ «Is anyone of this user still watching?»  It serves to decide whether
 *    to switch off the stage, and the answer is ASKED of the list of live
 *    sessions instead of keeping a separate counter: two copies of the same
 *    set diverge, and the one that is wrong leaves the stage on forever. */
bool wt_video_qualcuno_guarda(const char *utente, uint8_t *codec);

/* ═══ AUDIO — phase 7, `RCP.md` §5.3 and §6.3 ════════════════════════════════
 *
 * ⛔ Audio lives ONLY on datagrams, and everything that follows derives from
 *    this: a block that does not leave is NOT kept.  §6.3 — «no
 *    retransmission, no reordering» — and the outgoing direction is no
 *    exception to the incoming one.
 */

/*
 * Delivers an audio block to all the sessions of `utente`.
 *
 * `codec`      1 = Opus, 2 = PCM (§6.3).  ⚠ They are NOT the video numbers.
 * `istante_us` the server's monotonic clock, of the FIRST sample of the block.
 * `dati`       the already encoded block: an Opus packet, or interleaved s16
 *              **little-endian** PCM samples (§5.3, the only declared
 *              exception to network byte order).
 *
 * ⛔ The caller must NOT worry about who listens: the I3 guard — that the
 *    user who PRODUCED the sound is the one PAM admitted on that session —
 *    is in here, as for frames.
 */
void wt_audio_diffondi(const char *utente, uint8_t codec, uint64_t istante_us,
                       const uint8_t *dati, size_t byte);

/* Is anyone listening to `utente`, and with which codec?  ⛔ It serves to
 * not make the encoder work for nobody — the same question
 * `wt_video_qualcuno_guarda` asks for pixels. */
bool wt_audio_qualcuno_ascolta(const char *utente, uint8_t *codec);

/* ========================================================================= */
/* ⭐⭐ THE CLIPBOARD — `RCP.md` §7.4, phase 7                                */

/* «The client copied some text: offer it to the session of `utente`.»       */
typedef bool (*wt_appunti_offerta)(void *ctx, const char *utente);
/* «Here is the text for whoever is pasting in the session of `utente`.»
 * ⛔ `testo` NULL = «I don't have it», which is still an answer. */
typedef bool (*wt_appunti_consegna)(void *ctx, const char *utente,
                                    uint32_t serial, const char *testo,
                                    size_t byte);
/* ⚠ The two are hooked together: without both the channel is not connected
 *   at all, and `rcp.c` declares it in the log instead of serving half a wire. */
void wt_appunti_gancio(wt_appunti_offerta offri, wt_appunti_consegna risposta,
                       void *ctx);

/*
 * ⭐ «THE SESSION OF `utente` COPIED THIS TEXT»: it is announced to the client
 *    (§7.4), and the text is kept until someone asks for it.
 *
 * ⛔ The I3 guard — that the text goes to the connection of WHOEVER copied it
 *    — is in here, as for frames and for audio.
 */
void wt_appunti_dalla_sessione(const char *utente, const char *testo,
                               size_t byte);

/*
 * ⭐ «SOMEONE IN THE SESSION OF `utente` IS PASTING»: the client is asked for
 *    the text it had announced.
 *
 * ⛔ `false` = the request did NOT leave — no client attached, no live
 *    announcement, no stream.  ⚠ And then the caller **must answer «I don't
 *    have it» at once** to whoever pastes: the debt towards the compositor
 *    does not settle by itself, and a desktop waiting for an answer that will
 *    not arrive is a desktop the user sees as hung.
 */
bool wt_appunti_richiesta(const char *utente, uint32_t serial);

/*
 * The four numbers that tell a session's audio.
 *
 * ⛔ `buttati` and `rifiutati` are two DIFFERENT facts and are not added:
 *    «buttati» (dropped) = the queue was full or the block was too big, that
 *    is **we** did not make it; «rifiutati» (refused) = ngtcp2 did not put it
 *    in the packet.  ⚠ A single counter for two causes is the error shape
 *    `LEZIONI.md` §2.2 describes: a number that never says where to look.
 */
void wt_audio_conti(const wt *w, uint64_t *spediti, uint64_t *buttati,
                    uint64_t *rifiutati, size_t *in_coda);

/*
 * ⛔ BENCH FUNCTION — switches on a test tone at `hz` Hz on every admitted
 *    session.  `0` = off, and it is the value of every normal installation.
 *
 * ⭐ It serves to put THREE links out of five under test (encoder · datagram ·
 *    browser) with a signal known sample by sample, instead of switching on
 *    five and being left with five suspects.  ⚠ It does not test the RATE:
 *    that will come from capture, which has a clock of its own.
 *
 * ⚠ It is invariant I6, and when it is on it WRITES so in the log.
 */
void wt_audio_prova(uint32_t hz);

/*
 * ⭐⭐ PHASE 9 — THE THRESHOLD beyond which a delta stuck in the queue is
 *     considered «really hopeless» and abandoned (§5.1, which says **MAY**,
 *     not MUST).  Below the threshold the delta is KEPT: streams are
 *     independent (`RCP.md:1155`), so keeping it does not block the later ones.
 *
 * ⭐⭐⭐ ON BY ITSELF AT **100 ms** SINCE 24 AUG 2026 — the user's decision:
 *      *«the product changes for the better; this phase was about making
 *      remotix work more solidly on degraded networks, without claiming to
 *      work miracles»*.  ⛔ `0` = OFF, and it remains the only way to switch
 *      it off (`--sgombra-soglia-ms 0`): the delta is abandoned at every
 *      newer frame, as it was until 23 August — byte for byte.  The
 *      derivation of the 100 ms (four measured constraints) is next to
 *      `WT_SGOMBRA_SOGLIA_MS` in `webtransport.c`.
 *
 * ⚠ THE PRICE, DECLARED — `[M]` 23-24 Aug 2026, bench `09-b79`: together
 *   with the rate regulator it costs **up to +160 ms** of drift on a bad
 *   network, and **zero** on the healthy line (39.85 / 40.19 / 39.63
 *   frames/s in the three arms, zero keyframes in all three).
 *
 * ⛔ WHY IT USED TO BE OFF, and why it no longer is: invariant I6 wants
 *    whatever changes what the user SEES to stay behind a switch that is off
 *    **until they have looked at it**.  They looked at it (§19.6, §20.3) and
 *    decided.  ⇒ The premise of I6 is satisfied, not circumvented.
 *    ⚠ And the server WRITES the value in force at startup **in both
 *    cases**: «off» and «never fired» must not look the same.
 *
 * ⚠ In MILLISECONDS, because it is a delay one sees: whoever tunes it
 *   chooses how old the image may be for a fraction of a second.
 *   The option is `--sgombra-soglia-ms N`, and it is the ONLY way.
 */
void wt_sgombra_soglia(uint64_t ms);

/* ⛔ THE DEFAULT, AND THERE IS A SINGLE COPY OF IT — it is here because
 *    `main.c` initialises its variable with it, as for the two `WT_LM_*`
 *    further below.  The DERIVATION (the four measured constraints) is in the
 *    box above `WT_SGOMBRA_SOGLIA_MS` in `webtransport.c`, and is not
 *    duplicated here. */
#define WT_SGOMBRA_SOGLIA_MS 100u

/*
 * ⛔ The value IN FORCE, and there is a single copy of it — the shape already
 *    used for `rcp_inattivita()`.  Whoever writes it in the startup line
 *    reads it from here instead of keeping a copy of their own, or «written»
 *    and «in force» become two different numbers (shape E1).
 */
uint64_t wt_sgombra_soglia_letta(void);

/*
 * ⛔⭐⭐ PHASE 9 — THE RATE REGULATOR, and since 24 Aug 2026 it is born **ON**
 *      (the user's decision; until the 23rd it was born off because of
 *      invariant I6).
 *
 *      When on, a frame does NOT LEAVE when two deltas already in flight
 *      still have bytes in our output queue.  The rate drops by itself, as
 *      much as the line does not carry, and there is no number to raise back.
 *
 * ⛔ THE QUANTITY IS `arretrato`: how many live DELTA frames still have bytes
 *    in OUR queue, read when a new one arrives and BEFORE `video_sgombra()`.
 *    It is local, it is a fact and not an estimate, and it is the shape of
 *    P20 (`RCP.md:398`) applied to the sender instead of the receiver: no
 *    lost packet, no reordering and no client silence can distort it,
 *    because nothing coming from outside is looked at.
 *
 * ⛔ AND THERE IS NO RISE TO REMEMBER — it is the merit, not a lack: the
 *    quantity is reread at every frame.  A link that keeps a state is a link
 *    that one day stays down, and it has already happened (`codificatore.c`,
 *    `qualita_corrente`, cured on 23 Aug 2026).
 *
 * ⛔⛔ AND IT DEPENDS ON THE THRESHOLD ABOVE — see `wt_ritmo_adattivo()` in
 *      `webtransport.c`: with `--sgombra-soglia-ms 0` the delta queue
 *      empties at every frame, so `arretrato` cannot exceed **1** and this
 *      regulator NEVER fires.  ⇒ The startup line SAYS so, because a dead
 *      link and a healthy line look the same.  ⭐ With the defaults of
 *      24 Aug 2026 BOTH are born ON, which is the only combination in which
 *      this regulator has a quantity to hook onto.
 *
 * ⚠ THE PRICE, DECLARED — `[M]` 23-24 Aug 2026, bench `09-b79`: threshold
 *   plus regulator cost **up to +160 ms** of drift on a bad network, and
 *   **zero** on the healthy line (39.85 / 40.19 / 39.63 frames/s in the
 *   three arms, zero keyframes in all three).
 *
 * ⚠ And the value in force is WRITTEN at startup in both cases, on and off:
 *   without that line «the cure is working» and «the cure is not on» produce
 *   the same log, that is no line.
 *
 * ⛔⭐ THE OPTION IS `--niente-ritmo-adattivo`, without argument, and it
 *     SWITCHES OFF.  ⚠ The old name `--ritmo-adattivo` (which meant «switch
 *     on») **no longer exists**: with the default on it would mean nothing,
 *     and an option that does nothing is worse than an option that is not
 *     there.  ⛔ Whoever types it gets a message explaining the change and an
 *     exit 2, not a silence.  ⇒ ONE WAY ONLY: two ways of switching on the
 *     same cure are two numbers that diverge (it is the reason why the
 *     bridge through the environment has already been removed once, on
 *     23 Aug 2026).
 */
void wt_ritmo_adattivo(bool acceso);

/*
 * ⛔⭐⭐⭐ PHASE 9 — THE DEAD LINE, and since 24 Aug 2026 it is born **ON**
 *       (the user's decision; until the 23rd it was born off because of
 *       invariant I6).
 *
 *       When on, a session is CLOSED — the wire drops and the user comes back
 *       in by hand — when one of two things happens, and each is written in
 *       the log with the numbers it decided on (I1):
 *
 *         · STALL: `stallo_ms` milliseconds without a video byte leaving
 *           WHILE HAVING some to send;
 *         · SILENCE: `silenzio_s` seconds without a packet from the client,
 *           with at least two of our packets sent in the meantime.
 *
 * ⛔⛔ AND LOSS IS NO LONGER A CAUSE — 23 Aug 2026, refuted by its bench.
 *      `casa-cattiva` declared **512‰** loss and HELD for ten minutes
 *      (9.60 frames/s, largest gap 0.50 s); `raffica-forte` declared
 *      **123‰** and did not hold (gap 30.06 s).  ⇒ The fraction orders the
 *      two cases THE WRONG WAY ROUND and no threshold separates them: on a
 *      line that REORDERS, `pkt_lost/pkt_sent` measures reordering and not
 *      loss.  ⭐ The number stays in the firing line as `permille=`, a
 *         WITNESS of reordering and no longer a judge — and
 *         `--linea-morta-permille` NO LONGER EXISTS, because an option that
 *         decides nothing is a fake switch.  The full refutation is in the
 *         box above `WT_LM_STALLO_MS` in `webtransport.c`.
 *
 * ⛔ THE QUANTITY IS AN OBSERVABLE FACT, not a clock: two monotonic and LOCAL
 *    counters — the video bytes handed to ngtcp2 and the frames the stage
 *    gave us — and it is the shape of the P8→P20 family (`RCP.md:398`), the
 *    same as `arretrato`.  Time enters ONLY as the distance between two
 *    samples.  ⛔ And both halves count: «nothing leaves» alone is also the
 *    STILL SCENE, which in this phase is normal — if we have nothing to
 *    send the count does not even start.
 *
 * ⛔⛔ IT IS THE MOST VISIBLE THING THE PRODUCT CAN DO — it throws a session
 *      out.  ⇒ I6 to the letter: it was born off, the user watched it on the
 *      real desktop (§19.6, §20.3) and on 24 Aug 2026 decided it becomes the
 *      normal behaviour.  ⚠ The value in force is written at startup in BOTH
 *      cases, and now it matters more: a session that disappears without a
 *      line saying whether the cure was on and with which numbers is
 *      indistinguishable from a defect of ours.
 *
 * ⚠⚠ THE PRICE, DECLARED, AND IT IS THE DEAREST OF THE FIVE — `[M]` 23 Aug
 *     2026: margin **10×** above the worst line that HOLDS and **2.9×** below
 *     the one that serves nobody.  ⛔ It is the cure that CLOSES A SESSION: if
 *     the threshold were badly tuned it would throw out someone who is
 *     working.  ⇒ Whoever touches `WT_LM_STALLO_MS` touches that margin, and
 *     the two numbers must be measured again.
 *
 * ⚠ The derivation of the 5.0 s — the two margins, 5.0× above the empty
 *   whole second of `raffica-1` (which HOLDS, 23.94 frames/s) and 2.9× below
 *   the 14.26 s of `raffica-forte` — is in full in the box above
 *   `WT_LM_STALLO_MS` in `webtransport.c`, with the measurements of
 *   23 Aug 2026 next to it.
 *
 * ⚠⚠ AND WHEN ON IT ALSO CHANGES THE TRANSPORT PINGS: they go from 10 s to
 *     half the silence threshold (5 s with the defaults), or «the client does
 *     not answer» and «we have not asked the client anything yet» would look
 *     the same.
 *
 * ⛔⭐ THE OPTIONS, AND THEY ARE THE BENCHES' CONTRACT:
 *       `--niente-linea-morta`         without argument, SWITCHES OFF the whole cure;
 *       `--linea-morta-stallo-ms N`    default 5000; 0 = silence only;
 *       `--linea-morta-silenzio-s N`   default 10;   0 = stall only.
 *
 *     ⚠ The old name `--linea-morta` (which meant «switch on») **no longer
 *       exists**: with the default on it would mean nothing.  Whoever types
 *       it gets a message explaining the change and an exit 2.
 *     ⚠ And the two `0` are NOT a second way to switch off the cure: they
 *       switch off one CAUSE at a time, and the startup line says which of
 *       the two remains.  Whoever wants yesterday's product types
 *       `--niente-linea-morta`, which is the only way that switches the
 *       mechanism off.
 */
/* ⛔ THE TWO DEFAULTS, AND THERE IS A SINGLE COPY OF THEM: they are here
 *    because `main.c` initialises its variables with them and passes them to
 *    `wt_linea_morta()`.  With a number written twice «the server's default»
 *    and «the transport's default» become two different things the day one
 *    of the two is tuned.
 * ⚠ The DERIVATION of the 5 000 ms — the two measured margins — is in the
 *   box above the `WT_LM_*` constants in `webtransport.c`, and is not
 *   duplicated here. */
#define WT_LM_STALLO_MS 5000u /* 5.0 s of frozen image with stuff to send */
#define WT_LM_SILENZIO_S 10u  /* the user's 10 s                          */

void wt_linea_morta(bool accesa, uint64_t stallo_ms, uint64_t silenzio_s);

/*
 * ⛔ «This connection must be detached»: `trasporto.c` asks it at every pass
 *    over the expired timers.  ⚠ The decision is taken by `webtransport.c`,
 *    which has the counters; making it happen is the transport, which is the
 *    only one owning the QUIC connection — the WebTransport session has
 *    nothing to do with it, because the road of `RCP.md` §3.1 point 3 waits
 *    for the queue to empty on a line that by hypothesis no longer carries.
 */
bool wt_linea_morta_scattata(const wt *w);

/*
 * ⭐⭐ THE AUDIO SEAM — the twin of `wt_video_gancio`.
 *
 *     Who knows a session has negotiated an audio codec: `rcp.c` (§4.3).
 *     Who knows which session it belongs to: `webtransport.c`.
 *     ⛔ Who can really capture: the CHILD, which has PipeWire — that is
 *     another process.
 *     ⇒ `main.c` is the only one that knows all three, and decides nothing:
 *     it passes.
 *
 * `codec` 1 = Opus, 2 = PCM, **0 = nobody listens any more**.
 */
typedef void (*wt_audio_richiesta)(void *ctx, const char *utente, uint8_t codec);
void wt_audio_gancio(wt_audio_richiesta f, void *ctx);

/* The FIVE video numbers of a session, for the log and for the benches.
 * ⛔ Together, always: «zero abandoned» said alone does not tell a line that
 *    carries from a channel that has never sent anything.
 *
 * ⭐ PHASE 9 — the fifth is `ritmo_scesi`: the frames the rate regulator
 *    did NOT let leave.  ⛔ It is a number OF ITS OWN and does not go into
 *    `saltati`: that one counts inadmissible frames (wrong canvas, credit
 *    exhausted, refusal by rcp), this one counts a RATE DROP decided by us,
 *    and they are two different facts.  Adding them would give a total that
 *    looks healthy and says nothing. */
void wt_video_conti(const wt *w, uint32_t *diffusi, uint32_t *saltati,
                    uint32_t *spediti, uint32_t *abbandonati,
                    uint32_t *ritmo_scesi);

/* For the log and for the benches. */
const char *wt_stato_rcp(const wt *w);

#endif
