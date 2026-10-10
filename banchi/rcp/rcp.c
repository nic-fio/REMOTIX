/*
 * rcp.c — the RCP/1 handshake, server side.
 *
 * Every rule below carries a paragraph number next to it: whoever changes one
 * must change `RCP.md` first, or the two drift apart in silence.
 */
#include "rcp.h"

#include <errno.h> /* §4.4-bis: «there is no file yet» and «I could not
                    * read it» are two different facts, and what tells them
                    * apart is `errno` alone (`LEZIONI.md` §1.9 rule 1) */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h> /* §4.4-bis: the ban file carries an ABSOLUTE time,
                    * because `ora` is monotonic and restarts with every process */

/* ------------------------------------------------------------------------ */
/* The control channel types — §7.1                                          */
enum {
	T_CIAO = 0x0001,
	T_ECCOMI = 0x0002,
	T_CREDENZIALI = 0x0003,
	T_AMMESSO = 0x0004,
	T_RESPINTO = 0x0005,
	T_ATTACCA = 0x0006,
	T_SESSIONE = 0x0007,
	/* §7.2 — the cursor SHAPE, server → client, on the control channel
	 * (§5).  ⚠ The POSITION never travels in this direction: it belongs to the
	 * client, which draws the pointer itself (`SPECIFICHE.md` §7.1). */
	T_CURSORE_FORMA = 0x000A,
	T_CONGEDO = 0x000C,
	/* ⭐ §5.2, §7.1: «the client asks for a keyframe».  Served since 12 Aug
	 * 2026, together with the video channel: while there was no video, this type
	 * fell into the `default` and made a conforming client that had seen a gap
	 * **lose the session** — the price the log declared
	 * («phase 1 does not serve it yet»). */
	T_RICHIEDI_CHIAVE = 0x000D,
	/* ⭐ §7.6, 15 Aug 2026: «the user wants to leave».  ⛔ It is not the
	 * `CONGEDO`, which leaves the session alive: this one ENDS it. */
	T_TERMINA_SESSIONE = 0x0011,
	/* ⭐ §7.1 — «the client asks for a canvas of another size», and the answer
	 * `TELA` that declares the outcome.  ⛔ Served since 14 Aug 2026: before,
	 * `ADATTA_TELA` fell into the `default` and made a conforming client **lose
	 * the session**, and `TELA` was sent **by no line at all** —
	 * `rcp_tela_adattata_ora()` changed the state and wrote to the log, but
	 * nothing went out on the wire.  It is the pair that `DECISIONI.md` §5.0-sexies
	 * switches on. */
	T_ADATTA_TELA = 0x000B,
	T_TELA = 0x000E,
	/* ⛔⭐ §7.1 — «the view has changed: new width and height».  Served
	 *     since 16 Aug 2026 (phase 6, sub-phase 6.4): before, it fell into the
	 *     `default` with the line «phase 1 does not serve it yet», and the price
	 *     was written there in full — **a conforming client that narrows the
	 *     window loses the session**, that is, literally the symptom that finding
	 *     R1.17 of §7.1 was written to make impossible.
	 *
	 * ⚠ And what it does is little for a declared reason, not out of laziness:
	 *   §7.1 says the view **MUST NOT** change the canvas and that «in RCP/1 not
	 *   even the size of what is encoded changes».  ⇒ It is validated, kept and
	 *   logged.  The canvas belongs to the SESSION, the view to the
	 *   CONNECTION. */
	T_VISTA = 0x0008,
	/* ⭐ §7.1 `0x0009` — «the keyboard layout has changed».  ⛔ Served
	 *    since 16 Aug 2026: before, it fell into the `default` and CLOSED the
	 *    session of a conforming client, which is the exact twin of the `VISTA`
	 *    defect.  It carries out `DECISIONI.md` §5-bis.7, and it is the message
	 *    with which the keyboard is changed **without detaching**. */
	T_DISPOSIZIONE = 0x0009,
	T_BANCO_MARCA = 0x000F,
	T_BANCO_ESITO = 0x0010,
};

/* ------------------------------------------------------------------------ */
/* ⭐ THE INPUT CHANNEL TYPES — §7.3, and the high byte is 0x01 (§2.5)        */
enum {
	T_PUNTATORE = 0x0101,
	T_PULSANTE = 0x0102,
	T_ROTELLA = 0x0103,
	T_LETTERA = 0x0104,
	T_POSIZIONE_TASTO = 0x0105,
};

/* ⛔ HOW LONG EACH BODY IS — §7.3, with the two common fields in front.
 *
 *   u32 id + u64 istante                              = 12  (all)
 *   PUNTATORE       + u32 x + u32 y                   = 20
 *   PULSANTE        + u16 codice + u8 premuto         = 15
 *   ROTELLA         + i32 asse_x + i32 asse_y         = 20
 *   LETTERA         + u32 carattere                   = 16
 *   POSIZIONE_TASTO + u16 codice + u8 premuto         = 15
 *
 * ⛔ §6.0: no field is aligned and no padding is allowed — so
 *    15 is fifteen, not sixteen.  It is exactly the shape of the defect fixed
 *    in §6.2 on 9 Aug 2026 (the «four bytes that make the numbers add up»), and
 *    on a fifteen-byte message a C `struct` would hold sixteen on
 *    every compiler this project uses. */
/* ------------------------------------------------------------------------ */
/* ⭐ THE CLIPBOARD CHANNEL TYPES — §7.4, and the high byte is 0x02 (§2.5)    */
enum {
	T_APPUNTI_ANNUNCIO = 0x0201, /* «I have new text» */
	T_APPUNTI_CHIEDI = 0x0202,   /* «send it to me» */
	T_APPUNTI_TESTO = 0x0203,    /* UTF-8 */
};

/* ⛔ HOW LONG EACH BODY IS — §7.4.
 *
 *   ANNUNCIO  u32 trasferimento + u32 lunghezza        = 8, FIXED
 *   CHIEDI    u32 trasferimento                        = 4, FIXED
 *   TESTO     u32 trasferimento + bytes to the end     = 4 + n, VARIABLE
 *
 * ⛔⭐ AND THE SECOND LENGTH IS NOT THERE, and it is a fix of 9 Aug 2026
 *     (finding R1.20): `APPUNTI_TESTO` carried a `u32 lunghezza` **inside** a
 *     message that already has its length in the framing of §6.1 — two
 *     truths about the same fact, which is the defect §2.2 forbids in those
 *     words.  ⇒ The text is read **up to the end of the message**, and the
 *     ceiling is the one of §5.4. */
#define A_ANNUNCIO 8u
#define A_CHIEDI 4u
#define A_TESTO_MINIMO 4u

/* ⛔ How many clipboard channel streams are kept open at once.
 *
 * §2.5 wants «one **per transfer**», and sets no ceiling on the number of
 * transfers: the ceiling is set by this module, because every open stream is
 * a buffer that lives in the session.  ⚠ Eight is generous: in the client →
 * session direction a transfer is one announcement and one text, and more than
 * two or three at once means someone is holding the copy key down.
 *
 * ⛔ And when the table is full the session is NOT closed: the oldest one
 *    WITHOUT pending bytes is thrown away, and ⛔ **it is written to the log**
 *    (§3: «every tolerance must be written to the log; a silent tolerance is
 *    indistinguishable from a defect»).  ⚠ If they are all halfway through a
 *    message, then that is a real violation and the client is sent away: it
 *    means the client opens streams and does not finish them. */
#define A_STREAM_MAX 8

/* ⛔ The backstop for paste requests, in milliseconds — see the box in
 *    `rcp_tempo()`.  ⚠ WIDER than the child's 4000 ms, and the reason is
 *    written there: the two backstops pay two different debts. */
#define APPUNTI_FONDO 8000

#define I_COMUNI 12u
#define I_PUNTATORE (I_COMUNI + 8u)
#define I_PULSANTE (I_COMUNI + 3u)
#define I_ROTELLA (I_COMUNI + 8u)
#define I_LETTERA (I_COMUNI + 4u)
#define I_POSIZIONE (I_COMUNI + 3u)

/* ⛔⭐ THE INPUT BUFFER IS SMALL **BY CONSTRUCTION**, and it is not a
 *     shortcut: it is §6.1 applied before allocating, taken to the extreme this
 *     channel allows.
 *
 *     On the control channel the declared length can only be known by
 *     reading the body (the capabilities of `CIAO` are a list), so the
 *     buffer grows up to 1 MiB.  ⛔ Not here: the five types of §7.3 all
 *     have a FIXED length known from the `tipo` alone.  ⇒ As soon as the six
 *     header bytes have arrived it is already known whether the length is the
 *     right one, and a wrong length is `ERRORE_PROTOCOLLO` BEFORE a
 *     single byte of body is buffered (§6.1: «the length is checked
 *     before allocating»).
 *
 * ⭐ Hence: 6 + 20 = 26 bytes are enough forever, and they fit in the session
 *    without a `malloc`.  Whoever announces a megabyte on this stream does not
 *    get a megabyte: they get a farewell after six bytes. */
#define I_ACCUMULO 32u

/* §7.1 — the second of grace after a canvas change, in milliseconds.
 * ⚠ The comparison is `<=`: «for one second» includes millisecond 1000. */
#define TELA_GRAZIA 1000

/* §7.5 — the outcome of the bench function. */
enum {
	BANCO_ACCETTATA = 1,
	BANCO_RIFIUTATA = 2,
	BANCO_FUNZIONE_SPENTA = 1,
	BANCO_RITARDO_FUORI_LIMITI = 2,
};

/* ⛔ §7.5 rule 1: the bench function is OFF unless the administrator
 * switches it on — invariant I6, and here it literally paints over someone's
 * desktop.  In phase 1 there is no configuration yet, so it is
 * simply off: it is the default state of every server, and it is what B5
 * puts to the test. */
#define BANCO_ACCESO 0
/* §7.5 rule 4: `ritardo_ms` MUST be between 0 and 10 000. */
#define BANCO_RITARDO_MAX 10000

/* The ceilings of §4.6, in milliseconds. */
#define TETTO_CIAO 5000
#define TETTO_CREDENZIALI 60000
/* ⛔ TEN seconds, not sixty — finding R9.9, 10 Aug 2026.
 *
 * §4.6, table, third row: «`AMMESSO` sent → `ATTACCA` received → 10 s».
 * Here there was 60 000, that is the same number as the row above: the shape
 * of the defect that is copied from the previous row and not reread.
 *
 * ⚠ The ceiling exists because «a connection that stops halfway through the
 *   handshake holds a slot and declares it to no one» (§4.6): at 60 000 that
 *   slot — the one of §4.4-bis and the one of the registry of sessions not yet
 *   taken — was held SIX TIMES longer than the document allows.
 *
 * ⛔ And no bench saw it: B6 (the three ceilings) is not written yet, and in
 *    `01-b5-violazioni.py` there is no case on the ceilings.  The defect sat
 *    exactly where the bench does not look. */
#define TETTO_ATTACCA 10000
/* §4.4-bis: the fixed delay, and it applies to AMMESSO TOO. */
#define RITARDO_FISSO 1000

/* ⛔⭐ THE VERDICT CEILING — 12 Aug 2026, `DECISIONI.md` §1.10.
 *
 * It is not a ceiling of `RCP.md` §4.6: those three measure the CLIENT, and this
 * one measures US.  ⛔ It exists because since 12 August the PAM answer comes
 * from another process, and another process can die: without this number a
 * session would stay in `attesa-verdetto` forever, that is a client hanging
 * on a silence — precisely what §8.1 forbids.
 *
 * ⚠ It is the SECOND net, not the first: the helper already has its own
 *   deadline at 8 s (`aiutante.c`).  ⛔ There are two on purpose, and they live
 *   in two different processes: the first cannot fire if the one at fault is
 *   precisely the one holding it.  Twelve seconds, that is more than its own,
 *   so in the normal case the no comes from there — with its log line — and
 *   this ceiling stays the last word instead of the first.
 *
 * ⛔ And the deadline counts as NO: `cred_buone` is not touched, and it starts
 *    from false. */
#define TETTO_VERDETTO 12000

/* ⛔ THE SILENCE CLOCK — `SPECIFICHE.md` §5.3, `DECISIONI.md` §4.4.
 *
 * Thirty seconds without a byte FROM THE CLIENT and the client «is considered
 * detached»: it no longer holds the slot, and whoever arrives gets in.  It is
 * the rule that makes the case «the phone died in a tunnel and now I cannot
 * get back in» disappear.
 *
 * ⛔⛔⭐ AND HERE BELOW IT SAID THE OPPOSITE OF WHAT THE CODE DOES — 16
 *      Aug 2026, fixed together with the repair of the clock.
 *
 *      It said: ~~«it is measured on RCP bytes, not on QUIC ones: the
 *      transport sends acknowledgements and heartbeats on its own, and a clock
 *      resting on those would say "alive" of a client that has not spoken for
 *      an hour»~~.  ⚠ The fear was real and must be faced, not erased:
 *      **a client alive on the wire but with a dead page now holds the slot.**
 *
 * ⭐ But the choice was reversed on a measurement, not on an opinion: counting
 *    RCP bytes, **a user who was READING lost the slot after thirty
 *    seconds** — touches nothing, sends nothing — and a second device
 *    took it away.  `[M]` 16 August: `DETACHED for silence` at 30013 ms
 *    with the connection alive, and then `slot TAKEN` by a second tab while
 *    the first was watching.  ⇒ Counting bytes did not measure «the client is
 *    there»: it measured «the user is typing», which is the OTHER clock of
 *    §5.3, the thirty-MINUTE one.
 *
 * ⭐ And finding R3.19 stays satisfied, because the clock was not outsourced
 *    to QUIC: the thirty-second ceiling stays OURS, and what is looked at is
 *    the last packet **decrypted and authenticated** (`ultima_vita`).  With
 *    `max_idle_timeout` at 120 seconds this server still detaches at 30.
 *
 * ⚠ And what happens to the connection of whoever is silent, the document does
 *   NOT say.  Here the choice is to **leave it open** and free only the slot:
 *   closing it would be a farewell, and §8.2 has no reason meaning «you have
 *   been quiet for a while».  The choice is declared in `FASI.md`
 *   §01-filo-nudo, because it is a point where RCP.md allows two readings. */
#define SILENZIO 30000

/* ⛔⛔⭐⭐ THE GHOST EVICTION — 23 Aug 2026, phase 9, and it is NOT a
 *        new clock of §5.3: it is a shortcut inside the first.
 *
 * ⛔ THE FACT, measured.  `[M]` 23 August (`banchi/09-b78-apertura.py`): the only
 *    way a session opening really fails under loss is
 *    `ATTACCA` → `CONGEDO(0x0F)`.  With the client killed by `-9` — that is a
 *    goodbye NEVER SAID, which to the server is identical to a goodbye LOST —
 *    one counts **eleven refusals in a row, and the slot is free again at
 *    +30.5 s**: that is `SILENZIO`.  ⛔ And the box above DECLARES that that
 *    clock «makes the case "the phone died in a tunnel" disappear».  It does
 *    not make it disappear: it **lasts thirty seconds**, and in those thirty
 *    seconds the sentence the user reads — «you already have an active session
 *    elsewhere» — speaks of THEIR session, dead a moment before.
 *
 * ⛔⛔ AND THE DIRECTOR'S DECISION OF 23 AUGUST MAKES IT THE NORMAL CASE, no
 *      longer the accident: on a bad network **the wire drops and the user
 *      reconnects by hand**.  Whoever reconnects by hand finds their own ghost
 *      denying them the slot, and on a line that loses in bursts they find it
 *      every time. ⇒ This cure is the prerequisite of that decision, not an extra.
 *
 * ⛔ WHY `SILENZIO` WAS NOT LOWERED — road (a), discarded on a
 *    measurement and not on an opinion.  At 10 s it would break the case that
 *    on 16 Aug 2026 cost the repair of the two clocks: `[M]` on a still
 *    scene, between two authenticated packets of the BROWSER there are
 *    **15004, 15005, 15002 ms** — its keep-alive, which is not ours.  A ceiling
 *    at 10 s would detach **every** client that watches and does not touch, at
 *    every keep-alive round, and the line of `rcp_segno_di_vita()` that warns at
 *    `SILENZIO/2` would go from 15 s to 5 s, that is it would shout on every
 *    healthy session.  ⇒ It is not a number with a single job: it governs three
 *    (the slot, the §7.3 release on detach, and the warning threshold).  It
 *    stays 30.
 *
 * ⭐ THE ROAD CHOSEN, (b): the slot can be TAKEN AWAY EARLIER, but only from
 *    whoever has all three of these things together —
 *      1. it is the slot **of the same user** who is asking to get in
 *         (⛔ between different users it would be a security hole, not a
 *         convenience: see the explicit check in `tratta_attacca()`);
 *      2. it has been silent for more than `sfratto_ms`;
 *      3. and someone **is asking** for that slot — it does not fire on its own,
 *         so a lone session is never touched by this rule.
 *
 * ⭐ AND IT DOES NOT CONTRADICT `RCP.md` §8.2 — *«no attached and alive client is
 *    ever ousted»* — it APPLIES it: the occupant here is attached but **not
 *    alive**, and until today the only clock that could tell the two apart
 *    was the thirty-second one.  ⚠ It must be written here, or the next reader
 *    will believe §8.2 was violated.
 *
 * ⚠⚠ THE PRICE, AND IT IS THE REASON FOR THE DEFAULT VALUE.  The only thing that
 *    tells «dead» from «alive and still» is how long it is silent, and how long
 *    an ALIVE client is silent is not up to us: it is up to its browser's
 *    keep-alive, `[M]` 15 s.  ⇒ A threshold below 15 s would let the second
 *    device win almost always — that is it would switch off invariant I2 on
 *    every idle desk, and would give whoever stole the password the means to
 *    throw out the real user, which today `0x0F` prevents.  That is why the
 *    default is `SILENZIO / 2`: it is the point beyond which we have NEVER
 *    measured an alive client, and it is the same number at which
 *    `rcp_segno_di_vita()` already writes «the margin is getting thin».  One
 *    number, one meaning.
 *
 * ⭐ THE REAL CURE LIES ELSEWHERE, and it must be said: if the server sent PINGs
 *    even during an active session (`FASI.md` §05-la-sessione §6-bis,
 *    `src/webtransport.c` — NOT this file), the `ultima_vita` of an alive client
 *    would never again be older than a couple of seconds, and this threshold
 *    could go down to 3.  With that in place the ghost lasts a breath; without
 *    it, it lasts half as long as before.
 *
 * ⛔ IT WAS BORN OFF — invariant I6.  ⚠ And the switch was NOT for the false
 *    sentence (that one is always fixed, further below): it was for the
 *    EVICTION, which is a new way in which the server takes something away
 *    from a session, and
 *    `DECISIONI.md` §4.1-bis says the server does not throw out a healthy
 *    session.  If the threshold were badly tuned it would throw out a live one,
 *    which is much worse than a wrong message. ⇒ It is switched on by whoever
 *    has looked.
 *
 * ⭐⭐⭐ AND WHOEVER LOOKED HAS DECIDED — 24 Aug 2026.  Since 24 August the
 *      default is **15 000 ms** (`SILENZIO / 2`, the number of the box
 *      above), and `0` remains the only way to switch it off (`--sfratto-ms 0`).
 *      ⇒ The premise of I6 is satisfied, not bypassed: the switch is still
 *      there, it is just turned the other way.
 *
 * ⚠ THE PRICE AND THE GAIN, DECLARED — `[M]` 23-24 Aug 2026: the ghost
 *   goes from **32.13 s and 14 refusals** to **16.83 s and 7 refusals**.  ⛔ That
 *   is exactly half, and it is exactly what the number promises: one does not go
 *   below 15 s, because the browser's keep-alive is silent for `[M]` 15 s and an
 *   ALIVE and still client would be evicted (⇒ I2 off on every idle desk).
 *
 * ⛔ The value in force is WRITTEN at startup, on or off, like the three
 *    clocks of §5.3 — a ceiling nobody can read is the E1 shape. */
#define SFRATTO_PREDEFINITO (SILENZIO / 2) /* 15 s: see the box */
static uint64_t sfratto_ms = SFRATTO_PREDEFINITO; /* 0 = off, ⭐ since 24 Aug
                                                   *    2026 it is born ON */

void rcp_sfratto_imposta(uint64_t ms)
{
	sfratto_ms = ms;
}

uint64_t rcp_sfratto(void) { return sfratto_ms; }
uint64_t rcp_sfratto_consigliato(void) { return SFRATTO_PREDEFINITO; }

/* ⛔⭐ THE SECOND CLOCK OF §5.3 — «user inactivity», and until 16
 *     Aug 2026 IT DID NOT EXIST.
 *
 *     `SPECIFICHE.md` §5.3: *«30 minutes without input ⇒ REMOTIX **detaches**
 *     the client: getting back in takes user and password»*, and *«"input" is
 *     what the user sends, not what they watch: whoever spends half an hour
 *     watching a video without touching anything is detached.  The cost is
 *     small — reattaching is quick»*.  `RCP.md` §8.2 already gives it reason `0x02`.
 *
 * ⛔ And `RCP_INATTIVITA = 0x02` sat in `rcp.h` **without a line using it**:
 *    the E1 shape, «written is not in force».  A farewell reason declared
 *    in the protocol and never sent is a promise that another implementation
 *    would have had to handle for nothing.
 *
 * ⭐ THIS one is measured on RCP bytes (`ultimo_byte`), and it is the job that
 *    field exists for — freed the same day from the one that was not its own.
 *
 * ⚠ CONFIGURABLE, and §5.3 demands it: *«the second and the third are
 *   configurable, with those values as defaults»*.  ⛔ And the value in force
 *   is WRITTEN to the log at startup: so the number is read instead of being
 *   waited for half an hour — which is also the only way to test it without
 *   tying up a machine. */
#define INATTIVITA_PREDEFINITA 1800000u /* 30 minutes */
static uint64_t inattivita_ms = INATTIVITA_PREDEFINITA;

void rcp_inattivita_imposta(uint64_t ms)
{
	/* ⛔ Zero means OFF, and it is a legitimate value: whoever watches a video
	 *    for hours on their own machine does not want to be thrown out.  ⚠ It is
	 *    declared to whoever sews things together, who writes it to the log. */
	inattivita_ms = ms;
}

uint64_t rcp_inattivita(void) { return inattivita_ms; }

/* ⛔⭐ THE CEILING OF §6.1 BELONGS TO THE **MESSAGE**, NOT TO THE BODY — finding
 *     B-14, night of 10 Aug 2026.
 *
 *     §6.1 says «no **message** MUST exceed 1 MiB», and that «message»
 *     includes the six framing bytes is established by §5.4, which for the
 *     clipboard chooses 1 000 000 and not 1 MiB **precisely because** «the
 *     message carrying it has six framing bytes and four of length, and a
 *     ceiling equal to the message's (§6.1) would make illegal the text
 *     exactly as large as the ceiling».
 *
 * ⛔ Until tonight the comparison was `lung > MAX_MESSAGGIO` with `lung` =
 *    length of the **body**: a `CIAO` with a 1 048 576-byte body was
 *    accepted, that is **1 048 582 bytes on the wire**, six over the ceiling.
 *    ⚠ Six bytes do no harm; two readings that give different bytes for the
 *    same input do: a validator written by reading §6.1 would mark red a
 *    message this server accepts, and that is what §0 exists to prevent.
 *
 * ⭐ Hence the two names, instead of one: `MAX_MESSAGGIO` is the ceiling of the
 *    document, `MAX_CORPO` is what is left of it for the body.  The number of
 *    the document stays written only once. */
#define MAX_MESSAGGIO (1024u * 1024u) /* §6.1, FRAMING INCLUDED */
#define MAX_CORPO (MAX_MESSAGGIO - 6u)

/* ⛔ THE BUFFER IS THE CEILING OF §6.1, NOT A NUMBER OF ITS OWN — finding R9.13.
 *
 * Here there were 64 KiB, and §6.1 says «no message MUST exceed 1 MiB» —
 * that is **up to 1 MiB is conforming**.  The two numbers sat two lines
 * apart and did not agree: every message between 64 KiB and 1 MiB died with
 * `ERRORE_PROTOCOLLO` and the detail «too many bytes waiting for a body»,
 * before its header was even looked at.  ⚠ A `CIAO` with
 * four hundred capabilities with a legitimate and unknown name (≈ 82 KiB) is
 * conforming to §6.1 and §4.3 in every part, and §3 exception 1 requires
 * ignoring unknown names and **carrying on**: the server sent it away.
 *
 * ⚠ And there was a second effect: the check `lung > MAX_MESSAGGIO` was
 *   reachable ONLY from the length declared in the header, never from the
 *   bytes — the ceiling of §6.1 was not the ceiling of this server.
 *
 * ⭐ But a megabyte per connection taken at opening would be a gift to whoever
 *    opens a thousand connections: the buffer **grows on demand** and only up to
 *    this ceiling (see `accumula()`).
 *
 * ⚠ And since the night of 10 Aug 2026 it is `MAX_MESSAGGIO` **exactly**, not
 *   `6 + MAX_MESSAGGIO`: the longest message this server accepts is
 *   1 MiB framing included (finding B-14), so there is nothing to
 *   buffer beyond that number. */
#define MAX_ACCUMULO MAX_MESSAGGIO

enum stato {
	S_ATTESA_CIAO,
	S_ATTESA_CREDENZIALI,
	S_ATTESA_VERDETTO, /* CREDENZIALI received, the fixed delay is running */
	S_ATTESA_ATTACCA,
	S_ATTIVA,
	/* ⛔ ACTIVE BUT WITHOUT A SLOT: it has been silent for thirty seconds —
	 * finding R9.2.  The state exists because «no longer holds the slot» and
	 * «is still active» are two different things, and keeping them under the
	 * same label left TWO `attiva` sessions for the same user — what I2
	 * forbids.  See the box above `rcp_tempo()`. */
	S_STACCATA,
	S_FINITA,
};

static const char *NOMI_STATO[] = {"attesa-ciao",   "attesa-credenziali",
                                   "attesa-verdetto", "attesa-attacca",
                                   "attiva", "staccata-per-silenzio",
                                   "finita"};

struct rcp_sessione {
	rcp_ganci g;
	enum stato stato;
	char provenienza[64];
	/* ⛔ THE ADDRESS WITHOUT THE PORT, and it is not a detail: see the box
	 * above `rcp_chiave_indirizzo()`. */
	char indirizzo[64];
	char utente[257];
	/* ⭐ The layout the client DECLARED in `ATTACCA` (§4.5),
	 *    kept for two things: applying it when the session is open
	 *    (`DECISIONI.md` §5-bis.7), and recognising at `DISPOSIZIONE` (0x0009)
	 *    whether it has really changed.  ⚠ 64 bytes plus the NUL: it is the
	 *    ceiling of §4.5. */
	char disposizione[65];
	uint64_t da_quando;   /* when the current state began */
	/* ⛔⛔⭐ TWO CLOCKS, NOT ONE — and until 16 Aug 2026 there was only one
	 *      doing the job of both.
	 *
	 *      `SPECIFICHE.md` §5.3 keeps TWO, with two different meanings:
	 *
	 *        · «CLIENT silence», 30 SECONDS — «a client that is silent is a
	 *          client that has detached», and the paragraph says why: *«the 30
	 *          seconds cover only real interruptions»*;
	 *        · «USER inactivity», 30 MINUTES — «whoever spends half an hour
	 *          watching a video without touching anything is detached».
	 *
	 *      ⛔ `ultimo_byte` measures the SECOND and was used for the FIRST: a
	 *         client that watches and does not touch sends nothing, and thirty
	 *         seconds without touching the keyboard counted as «the client is gone».
	 *
	 *      `[M]` 16 August, with the browser: session open, no input, and at
	 *      30013 ms «DETACHED for silence, slots taken: 0» — while the
	 *      connection was alive (QUIC did not make a sound for 111 s, and a
	 *      single key took the slot back on the SAME connection).  ⛔ And the
	 *      price was paid: a second tab got in and took the desktop of the
	 *      first, which froze.  It is I2 broken in the case that `RCP.md` §8.2
	 *      names in writing — *«an alive client holds the slot, and the new one
	 *      is refused»*. */
	uint64_t ultimo_byte; /* the last RCP byte from the client: the USER (§5.3) */
	uint64_t ultima_vita; /* the last authenticated packet: the CLIENT (§5.3) */
	uint64_t cred_arrivo; /* when CREDENZIALI arrived */
	bool cred_buone;      /* the verdict, already computed but not yet told */
	uint8_t cred_motivo;  /* if not good */
	/* ⭐ THE CHECK ASKED OF ANOTHER PROCESS — `DECISIONI.md` §1.10.
	 *
	 * ⛔ `verdetto_atteso` is true between the question and the answer, and it
	 *    is the reason why `cred_buone` is no longer enough on its own: before
	 *    12 Aug 2026 the verdict was already ready when the state became
	 *    `attesa-verdetto`, because PAM had blocked the thread.  ⚠ Now
	 *    `attesa-verdetto` waits for TWO things: the fixed second of §4.4-bis
	 *    and the helper's answer — and the order between the two is not
	 *    guaranteed.
	 *
	 * ⛔ And while `verdetto_atteso` is true, `cred_buone` is **false**: if
	 *    something went wrong in the middle, what is read is a no
	 *    (invariant I3). */
	bool verdetto_atteso;
	uint64_t pratica;     /* the number by which the answer is recognised */
	/* ⛔ `true` when the no does NOT come from PAM but from us (helper off,
	 * request expired): it does not count as a failed attempt of §4.4-bis.  A
	 * server defect that banned the user for twelve hours would be «the
	 * worst diagnosis this project could produce» (§4.4-bis). */
	bool no_e_nostro;
	bool attaccata;       /* holds a slot in the registry of sessions */
	/* ⛔ The buffer is allocated on demand, and zeroed before being freed:
	 * `CREDENZIALI` passes through it, that is the password in clear (§4.4).
	 * See `accumula()` and `rcp_libera()` — findings R9.8 and R9.13. */
	uint8_t *acc;
	size_t acc_len, acc_cap;
	/* the negotiated capabilities, for the log (§4.3: the choice is written) */
	char codec[32];
	char profondita[32];
	char audio[32];
	/* ⛔ THE DECODER CEILING — `video.misura_massima` of §4.3.
	 *
	 * `0` means «the client did not declare it», and it is not the same thing
	 * as «declared it zero»: §4.5 constrains the granted canvas **only if the
	 * client declared it**.  ⚠ Before the night of 10 Aug 2026 these two
	 * fields did not exist: the name was recognised as legitimate in
	 * `NOMI_NOTI` and the value was thrown away — finding B-1. */
	uint32_t max_l, max_a;
	/* ⛔⭐ THE DECODER LEVEL — `video.livello` of §4.3, and until
	 *     23 Aug 2026 it was the UNCURED TWIN of `max_l/max_a`: the name
	 *     was in `NOMI_NOTI` and the value was **thrown away**, exactly
	 *     finding B-1 one field further on.
	 *
	 * ⛔ It is in TENTHS: `5.1` ⇒ `51`, `5` ⇒ `50`.  A `float` for a number that
	 *    comes out of a string and ends up in a comparison would be two ways of
	 *    writing `5.1` that are not equal — and the comparison is all this
	 *    field exists for.
	 * ⚠ `0` means «the client did not declare it», and it does NOT mean «low»:
	 *   whoever reads this field must not pick one on their own.  §4.3
	 *   requires the server not to EXCEED what the client declares, and on a
	 *   client that declares nothing there is nothing not to exceed. */
	uint32_t livello_x10;

	/* ==================================================================== */
	/* ⭐ THE VIDEO CHANNEL — §2.5, §5.1, §5.2, §6.2                        */

	/* ⛔⭐ «`SESSIONE` HAS BEEN SENT», AND NOT «THE STATE IS ACTIVE».
	 *
	 * §2.5 writes the rule with these words: «no video stream before having
	 * sent `SESSIONE`».  ⚠ The `attiva` state is very close and is NOT the
	 * same thing — it is a **proxy quantity**: it changes with
	 * `S_STACCATA` (a session that has been silent for thirty seconds sent
	 * `SESSIONE` long ago), and it would not change at all if one day the state
	 * were set to `attiva` one line before sending the message.
	 *
	 * ⛔ This flag is switched on IN THE SAME line that sends `SESSIONE`, and
	 *    only if the message really went out (`if (!w.pieno)`).
	 *
	 * ⭐ `LEZIONI.md` §1.13, applied while writing: *«one names the real
	 *    quantity of the phenomenon, and looks whether the protocol already
	 *    carries it»*.  Here the phenomenon is «the client knows the canvas and
	 *    the codec», and the fact that tells it is `SESSIONE` — not a server state. */
	bool sessione_spedita;

	/* ⛔ §6.2: THE CANVAS **IN FORCE**, which is the one granted in `SESSIONE`
	 * (§4.5) **or** the last one granted by `TELA(ADATTATA)` (§7.1).  ⚠ `0`
	 * here is not a size: it is «there is no canvas yet», and `sessione_
	 * spedita` is the fact that says so. */
	uint32_t tela_l, tela_a;
	/* ⛔⭐ THE VIEW — §7.1, and it sits **next to** the canvas on purpose: they
	 *     are two different quantities and the line separating them is normative.
	 *
	 *   · the **canvas** belongs to the SESSION: it outlives the client (I4),
	 *     only `ADATTA_TELA` changes it, and it constrains the frame size (§6.2);
	 *   · the **view** belongs to the CONNECTION: it is «the size at which the
	 *     client will draw», it arrives with `ATTACCA` (§4.5) and `VISTA`
	 *     updates it (§7.1).  ⛔ It **MUST NOT** change the canvas, and in RCP/1
	 *     it does not even change the size of what is encoded: the server sends
	 *     the whole canvas and the client rescales (`SPECIFICHE.md` §6.1).
	 *
	 * ⚠ And the limits are OTHERS: §7.1, finding R1.17 — «any size from 1x1
	 *   up is legal, odd included».  The canvas limits exist for the encoder's
	 *   blocks, and they do not apply to the view because in RCP/1 the view
	 *   touches no encoder.
	 *
	 * ⚠ Today this number decides nothing, and that is declared: it serves «to
	 *   choose how many bits to spend» (§7.1), and the choice of bits belongs to
	 *   the encoder phase.  ⛔ But it is KEPT all the same, because the
	 *   alternative is reading it and throwing it away — that is a protocol
	 *   field the server declares it understood and does not hold anywhere. */
	uint32_t vista_l, vista_a;

	/* ⛔ §6.2: the frame counter.  `0` = **none sent**, and it is the meaning
	 * §7.1 gives to zero in `RICHIEDI_CHIAVE`: here it is not an implicit
	 * sentinel (§6.0), it is the declared one. */
	uint32_t video_numero;

	/* ⛔ §5.2: «the next frame MUST be a keyframe».  True:
	 *   · as soon as `SESSIONE` has gone out            (first point of the rules)
	 *   · after a `TELA(ADATTATA)` that CHANGES the size  (second point)
	 *   · when the client sends `RICHIEDI_CHIAVE`         (§5.2, §7.1) */
	bool serve_chiave;
	/* Why it is needed, for the log: the three reasons are not the same thing
	 * and whoever diagnoses must be able to tell them apart. */
	const char *serve_chiave_perche;

	/* ⛔ §5.2, exception 5 of §3: «the server MAY ignore a
	 * `RICHIEDI_CHIAVE` that arrives within 200 ms **of the last keyframe it
	 * sent**» — ⛔ not of the last request received, and the difference is
	 * not a nuance: counting from requests, two insistent clients push the
	 * clock forward forever and the keyframe never leaves. */
	uint64_t ultima_chiave_ms;
	bool mai_spedita_una_chiave;
	/* ⛔ 22 Sep 2026 — the `numero` of the last keyframe sent: the 200 ms grace
	 *    applies only to whoever has NOT yet seen that keyframe
	 *    (`tratta_richiedi_chiave()`). */
	uint32_t ultima_chiave_numero;

	/* The frame open right now — §5.1, one stream per frame.
	 * ⛔ `video_aperto` and not «`stream` is -1»: `0` is a legitimate stream
	 *    identifier, and a sentinel taken from a valid value is what §6.0
	 *    forbids for protocol fields.  It is not done here either. */
	bool video_aperto;
	int64_t video_stream;
	bool video_e_chiave;      /* §5.2: a keyframe is NOT abandoned */
	uint32_t video_suo_numero;
	size_t video_da_scrivere; /* the data bytes DECLARED in `apri` */
	size_t video_scritti;     /* those gone out so far */
	uint64_t video_aperto_ms; /* the session time when it was opened */
	/* The count of abandonments, for the log: §5.1 wants every
	 * abandonment to be visible, and a count without a denominator is not a
	 * measurement (`LEZIONI.md` §1.9). */
	uint32_t video_spediti, video_abbandonati;

	/* ==================================================================== */
	/* ⭐ THE INPUT CHANNEL — §2.5, §7.1, §7.3                              */

	/* §2.5: the input stream is **only one**.  ⛔ `inp_stream_noto` and not
	 * «`inp_stream` is -1»: a stream 0 is a legitimate identifier, and a
	 * sentinel taken from a valid value is what §6.0 forbids. */
	bool inp_stream_noto;
	int64_t inp_stream;
	/* The buffer, fixed: see the box of `I_ACCUMULO`. */
	uint8_t inp_acc[I_ACCUMULO];
	size_t inp_acc_len;

	/* ⛔ §7.3: «the `id` grows by **at least one** with every message, **across
	 *    the whole input channel** — not one per type».  ⇒ ONE counter, and only
	 *    one: five per-type counters would accept
	 *    `PUNTATORE(4)` after `PULSANTE(9)`, and then the `input` field of the
	 *    frames (§6.2) would no longer come back consistent with anything.
	 * ⚠ `0` = none yet, and it is the value §7.3 reserves. */
	uint32_t inp_ultimo_id;
	/* ⛔ §6.2: what comes back in the `input` field of the frames — and it moves
	 * forward ONLY when the hook has answered 0.  See `rcp_input_ultimo_iniettato()`. */
	uint32_t inp_ultimo_iniettato;
	/* The count, and they are THREE numbers because the facts are three: how
	 * many arrived, how many injected, how many refused by the injector.
	 * ⛔ «Zero injected» on its own does not tell a mute compositor from a
	 * still client. */
	uint32_t inp_arrivati, inp_iniettati, inp_non_iniettati;

	/* ==================================================================== */
	/* ⭐ THE CLIPBOARD CHANNEL — §7.4, §5.4, §2.5                          */

	/* ⛔⭐ EACH SIDE NUMBERS ITS OWN TRANSFERS, from 1 upwards (§7.4,
	 *     finding R1.11).  ⇒ Two counters, and they have two different owners:
	 *     ⛔ confusing them is exactly the defect the identifier was born
	 *     to remove — «with two announcements open in the two directions, the
	 *     user copies here while pasting there, and the two implementations pair
	 *     the requests with the announcements in a different order and **swap the
	 *     texts**».
	 *
	 * ⚠ `0` = «no announcement yet», and §7.4 reserves zero: transfers
	 *   start from 1.  It is not an implicit sentinel (§6.0), it is the one
	 *   declared by the protocol. */
	uint32_t app_mio_id;  /* the last one *I* announced */
	/* ⛔ How many bytes the last text the SESSION gave us had: it serves to
	 *    know whether the session has something to lose.  See the rule
	 *    of the empty announcement, further below. */
	size_t app_mio_len;
	uint32_t app_suo_id;  /* the last one the CLIENT announced */
	uint32_t app_suo_len; /* how many bytes that announcement said */

	/* ⛔ The text the SESSION copied, kept here waiting for someone to
	 *    ask for it.  §7.4: «one announces and asks, instead of pushing».
	 *
	 * ⚠ There is ONLY ONE, and it is the current one: §7.4 says that an
	 *   `APPUNTI_CHIEDI` arriving when the announcement has already been
	 *   superseded by a more recent one **is served with the current text**,
	 *   and the sender writes it to the log.  ⇒ Keeping the old ones would serve
	 *   no purpose and would be memory growing with every copy. */
	char *app_testo;
	size_t app_testo_n;
	/* ⛔ The text above arrived BEFORE `SESSIONE` and has not yet been
	 *    announced: it is announced as soon as the session is open
	 *    (`annuncia_il_tenuto`). */
	bool app_tenuto;

	/* ⛔ The serials of the SESSION's requests waiting for the client's text.
	 *
	 * ⚠ There can be more than one: two programs pasting together are
	 *   two `SelectionTransfer`, and the wire carries a single `APPUNTI_CHIEDI` —
	 *   the answer serves **all** of them, because they ask for the same
	 *   transfer identifier, that is the same text. */
	uint32_t app_serial[A_STREAM_MAX];
	int app_serial_n;
	/* ⛔ Has an `APPUNTI_CHIEDI` for the queued batch already gone out?  ⚠ It is
	 *    needed because requests can arrive BEFORE the announcement (see
	 *    `rcp_appunti_chiedi`), and then the question leaves when the
	 *    announcement arrives: without this flag one would leave for every
	 *    request already queued, and the client would receive three `CHIEDI`
	 *    for a single text. */
	bool app_chiesto;
	/* ⛔⭐ AND WHICH ONE, not only «whether».  §7.4 says two things that look
	 *     like one: an `APPUNTI_TESTO` that NOBODY asked for is
	 *     `ERRORE_PROTOCOLLO`, but a request served when the announcement has
	 *     already been superseded is served **with the current text** and is not
	 *     an error (the fifth exception of §3).  ⇒ The comparison must be made
	 *     with what I ASKED FOR, not with the live announcement: between the
	 *     question and the answer the client may have announced again, and then
	 *     the number is old by construction.
	 * ⚠ `[M]` 20 Aug 2026: it really happened, in the opposite direction — the
	 *   PAGE closed the session because of this, and the user saw «Firefox got
	 *   stuck with the clipboard». */
	uint32_t app_chiesto_id;

	/* ⛔⛔⭐ THE OFFER THAT WAITS FOR THE END OF THE TRANSFER — 21 Aug 2026,
	 *      and Mutter stated the defect in its own words: *«Transfer serial 2
	 *      doesn't match any transfer request»* (bench `07-b56`).
	 *
	 * ⚠ Offering the selection to the compositor (`SetSelection`) CANCELS the
	 *   transfers in flight: it is the compositor that, seeing a new selection,
	 *   throws away the requests open on the old one.  ⛔ And we were re-offering
	 *   precisely while serving — the client rereads the clipboard when asked,
	 *   announces the new text, and that announcement killed the paste
	 *   that had caused it.  ⇒ Whoever was pasting saw **empty**.
	 *
	 * ⭐ So the offer is POSTPONED: while someone is waiting, the
	 *    compositor stays the owner of what it has, and the new offer leaves
	 *    when the answer has gone out. */
	bool app_offri_dopo;

	/* The incoming streams, one per transfer (§2.5).  ⛔ The buffer is
	 * allocated on demand and **after** validating the declared length:
	 * §6.1 — «a receiver that allocates `lunghezza` bytes and then checks has
	 * already given a megabyte to anyone who can write six bytes». */
	struct {
		bool usato;
		int64_t stream;
		uint8_t testa[6];
		size_t testa_n;
		uint16_t tipo;
		uint32_t lung;
		uint8_t *corpo;
		size_t corpo_n;
	} app_in[A_STREAM_MAX];

	/* The count, and the facts are four because they are diagnosed separately:
	 * how many announcements I made, how many were asked of me, how many I
	 * received from the client, how many I asked of it. */
	uint32_t app_annunciati, app_serviti, app_ricevuti, app_chiesti;
	/* When the FIRST request of the batch was queued: the backstop of
	 * `rcp_tempo()` counts from here. */
	uint64_t app_chiesto_ms;

	/* ⛔ §4.3: did the client declare `appunti.testo = si`?  ⚠ `false` is the
	 *    initial state and it is the right value: a `CIAO` without that
	 *    capability is a client that does not want the clipboard, not a client
	 *    that wants it by default. */
	bool negozia_appunti;
	/* ⚠ §7.3: the client's `istante`, in microseconds.  ⛔ And NO RULE of this
	 *   module CONSUMES IT: «in a page the monotonic clock is in milliseconds
	 *   and its grain is deliberately coarsened — the client writes
	 *   `milliseconds × 1000` and MUST NOT suggest a precision it does not
	 *   have» (finding R1.27).  It is here for the log and for diagnosis —
	 *   «when the user moved their hand» instead of «when the byte arrived» —
	 *   and ⛔ no measurement is built on it: the delay is measured by the closed
	 *   loop of `DECISIONI.md` §2.6, and the frame carries back the `id`, not
	 *   the instant. */
	uint64_t inp_ultimo_istante_us;

	/* ⛔ §7.1 / §3 exception 3 — THE SECOND OF GRACE.  The PREVIOUS canvas and
	 * the moment it was replaced: for one second a coordinate valid on that one
	 * is CLAMPED to the new one instead of closing the session.
	 * ⚠ `tela_prec_l == 0` means «no grace in progress», and it is legitimate
	 *   because a canvas of zero width has never been granted (§4.5). */
	uint32_t tela_prec_l, tela_prec_a;
	uint64_t tela_grazia_da;
	/* How many coordinates the grace has saved: §3 wants «every tolerance to be
	 * written to the log», and a count makes it possible to notice that a
	 * tolerance has started covering the normal case. */
	uint32_t inp_grazie;
	/* ⛔ §7.3, last paragraph: the release on detach is done **only
	 * once**.  The three roads that end a connection — farewell, silence,
	 * error — can be travelled in a row, and calling the hook twice does no
	 * harm but writes two lines that say different things about the same
	 * fact. */
	bool inp_rilasciato;

	/* ⛔⭐⭐ THE `ADATTA_TELA` PASSED TO THE STAGE AND NOT YET ANSWERED — §7.1,
	 *     and the chain `figli_ritela()` → `cattura_ridimensiona()`
	 *     (`DECISIONI.md` §5.0-sexies).
	 *
	 * ⛔ IT EXISTS BECAUSE THE ANSWER DOES NOT COME BACK FROM WHERE THE QUESTION
	 *    LEAVES.  The stage lives in another process, and the only way of knowing
	 *    that the compositor has obeyed is **to see a frame arrive at the new
	 *    size**: it can take a few tens of milliseconds (`[M]` Mutter 41.6
	 *    ms, labwc 5.1 ms), one of a size DIFFERENT from the one asked for can
	 *    arrive (§4.5 allows it), and none may arrive at all.
	 *
	 * ⛔ AND THIS IS PRECISELY WHY A WAIT WITH A BACKSTOP IS NEEDED: §7.1
	 *    requires that *«to every `ADATTA_TELA` the server MUST answer with a
	 *    `TELA`, successful or not.  A silence leaves the client waiting
	 *    forever»* — and on the client that silence is not just a wait: §6.2
	 *    makes it HOLD BACK frames while a request is unanswered, that is it
	 *    makes its queue grow in memory.
	 *
	 * ⚠ `tela_volo_da == 0` together with `tela_volo` false: no request in
	 *   flight.  And if a second one arrives while the first is in flight, the
	 *   second REPLACES the first and the `TELA` that goes out counts for both:
	 *   the count on the client would go down by one only — ⛔ that is why the
	 *   first is ANSWERED before accepting the second (see `T_ADATTA_TELA`). */
	bool tela_volo;
	uint32_t tela_volo_l, tela_volo_a;
	uint64_t tela_volo_da;
	/* ⛔ SINCE WHEN the stage delivers a size different from the canvas in force
	 *    WITHOUT anyone having asked for it.  ⚠ Zero = they agree.
	 *
	 * ⛔ It is not a duplicate of `tela_volo_da`, and it is the other case of
	 *    the same family: there the disagreement was wanted by us and one waits
	 *    for it to end; here nobody wanted it, and the first move is **asking
	 *    the stage to go back** to the canvas in force.  If after
	 *    `RCP_TELA_ATTESA_MS` it has not gone back, its size is adopted: a
	 *    session with an unexpected canvas is worth more than a session that
	 *    does not see a pixel (`SPECIFICHE.md` §8.3, and I1 — «an ugly session
	 *    is worth more than a closed session»). */
	uint64_t tela_disaccordo_da;
	/* How long to wait before asking the stage again to go back: it doubles at
	 * every attempt that came to nothing, up to `RCP_TELA_RICHIAMO_MAX_MS`. */
	uint64_t tela_disaccordo_attesa;
};

/* Declared here because the attempt limiter, below, MUST be able to
 * write to the log: a limit reached in silence is a limit that does not
 * exist (§3, and finding R9.1). */
static void reg(rcp_sessione *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));
/* ⛔⭐ §7.3 — «On detach everything is released».  Declared here because
 *     THREE roads call it that sit higher up than where it is defined — the
 *     farewell, the silence of §5.3 and the end of the session — and the three
 *     are exactly the three that §7.3 names: «by farewell, by silence, by
 *     error».  Defined in the input channel section, where the rest is. */
static void rilascia_al_distacco(rcp_sessione *s, const char *perche);

/* ⛔ §5.3 / finding R9.2 — the slot taken back by whoever speaks again.
 * Declared here because the client's bytes come in through TWO doors
 * (`rcp_ricevi()` and `rcp_ricevi_input()`) and the second sits higher up
 * than the definition. */
static bool torna_a_parlare(rcp_sessione *s);

/* ⛔⭐⭐ THE KEYFRAME DEBT IS SWITCHED ON AND OFF BY TWO FUNCTIONS ONLY — 23
 *      Aug 2026, and the reason is a comment that had already lied TWICE.
 *      The box of the video channel said «switched on in THREE places», and the
 *      places were four; corrected to «FIVE», and the places were nine.
 *      ⇒ A list kept by hand ages at the first new branch, and it ages in
 *      silence: no bench can notice, because the number is not a
 *      behaviour.  ⛔ The cure is not counting better: it is removing the
 *      count.  From here on the list is made by the compiler — `grep -n
 *      'chiave_serve(' src/rcp.c` is the list, always and by construction.
 * ⚠ Defined in the video channel section, where the rest is; declared here
 *   because the first switch-on (`SESSIONE` sent, §5.2) sits higher up. */
static void chiave_serve(rcp_sessione *s, const char *perche);
static void annuncia_il_tenuto(rcp_sessione *s);
static void chiave_pagata(rcp_sessione *s);

/* ------------------------------------------------------------------------ */
/* ⛔ THE REGISTRY OF ATTACHED SESSIONS — §8.2 reason 0x0F
 *
 * «The one refused is whoever arrives, not whoever was there»: no attached
 * and alive client is ever ousted.  A small list is enough here: the bench
 * opens two or three, and a real server will replace it with its session
 * table — but the RULE lives here, not there.                              */
/* ⛔⭐ THE NUMBER IS NO LONGER HERE — 25 Aug 2026.  It lives in `rcp.h`
 *     (`RCP_TETTO_SESSIONI`), together with the box that explains why it was
 *     written by hand in four places and why now it is only one.
 *
 * ⭐⭐ AND SINCE THE EVENING OF 25 AUGUST IT IS NOT EVEN A FIXED SIZE: the
 *     table is **allocated** on the cap in force (`--tetto-sessioni`).  ⛔ The
 *     `MAX_ATTACCATE` that was here **has disappeared**, and it was not left
 *     alongside as a «maximum»: it would have been a second number, that is the
 *     second road of `CODER.md` §2-bis.
 * ⭐ `[M]` §3.3 had verified that the five functions below do **only
 *    linear scans with `strcmp`** — no index arithmetic, no invariant resting
 *    on the 16 — and that is why the change costs a `calloc` and a counter. */
static int tetto_in_vigore = RCP_TETTO_SESSIONI;
static int quanti_posti;   /* ⛔ 0 until the table is allocated */
static struct posto {
	char utente[257];
	bool usato;
	/* ⛔⭐ WHO holds the slot, and it is not a duplicate of the name — 23 Aug
	 *    2026, the ghost eviction.  The name says THAT the slot is taken; to
	 *    know whether the occupant is still ALIVE one needs its `ultima_vita`,
	 *    which lives in its session and could not be reached from here.
	 *
	 * ⚠ And it cannot be left dangling: ALL the roads that free the slot
	 *   pass through `posto_lascia()` — `congeda()`, `rcp_libera()`,
	 *   `rcp_chiusa_dal_client()`, `rcp_canale_chiuso()`, the client's
	 *   `CONGEDO` and the silence of `rcp_tempo()` — and that one zeroes it.
	 *   ⛔ Whoever adds a sixth road makes it pass through there, or this
	 *   pointer becomes a read of freed memory. */
	rcp_sessione *chi;
} *attaccate;

int rcp_tetto(void)
{
	return tetto_in_vigore;
}

bool rcp_tetto_imposta(int quante)
{
	if (quante < 1)
		return false;
	/* ⛔ Only once, and before a session exists: if the table is already
	 *    there, moving its number would leave TWO caps in force in the same
	 *    process — the allocated size and the declared number — which is
	 *    precisely the defect the four `#define`s at 16 had. */
	if (attaccate)
		return false;
	tetto_in_vigore = quante;
	return true;
}

/* ⛔ The table is allocated at the first slot request, and **only once**.
 * ⚠ If `calloc` fails, the caller treats it as «no more slots»: it is a
 *   declared fallback, and the no arrives on the wire with a reason instead of
 *   with a segmentation fault. */
static bool posti_pronti(void)
{
	if (attaccate)
		return true;
	attaccate = (struct posto *)calloc((size_t)tetto_in_vigore,
	                                   sizeof *attaccate);
	if (!attaccate)
		return false;
	quanti_posti = tetto_in_vigore;
	return true;
}

static bool posto_occupato(const char *utente)
{
	for (int i = 0; i < quanti_posti; i++)
		if (attaccate[i].usato && strcmp(attaccate[i].utente, utente) == 0)
			return true;
	return false;
}

/* The session holding that user's slot, or NULL. */
static rcp_sessione *posto_chi(const char *utente)
{
	for (int i = 0; i < quanti_posti; i++)
		if (attaccate[i].usato && strcmp(attaccate[i].utente, utente) == 0)
			return attaccate[i].chi;
	return NULL;
}

/* ⛔⭐ TWO DIFFERENT FACTS CANNOT HAVE THE SAME OUTCOME — finding R9.3.
 *
 * `posto_prendi()` returned `false` for two things that do not even resemble
 * each other: «this user's slot is taken» and «the table is full».
 * The caller deduced only one of them, and sent the client away with
 * `GIA_ATTIVA_REMOTA`.
 *
 * ⛔ The seventeenth user of a multi-tenant machine (`SPECIFICHE.md`
 *    §5.5) — who never opened anything anywhere — received
 *    `CONGEDO(0x0F)`, and the client, as §8.2 requires, built from it the
 *    sentence «you already have an active session elsewhere».  **It is
 *    false.**  It is literally the symptom that the box above
 *    `rcp_chiusa_dal_client()` declares it went to cure: «it tells me I am
 *    already connected, and it is not true».  The cure back then removed one
 *    of the two roads; this was the other.
 *
 * ⭐ The right reason for the full table is §8.2 `0x0E`
 *    SESSIONE_NON_SERVIBILE: «the attach is well formed but cannot be
 *    served», and it MUST carry the detail in the body — which is exactly
 *    this case. */
enum esito_posto {
	POSTO_PRESO,
	POSTO_OCCUPATO,       /* there is already a client attached to THIS session */
	POSTO_NIENTE_PIU_POSTI /* the registry of sessions is full */
};

/* ⚠ It takes the SESSION and no longer just the name: the registry must know
 *   WHO holds the slot, for the ghost eviction (see `SFRATTO_PREDEFINITO`). */
static enum esito_posto posto_prendi(rcp_sessione *s)
{
	const char *utente = s->utente;

	if (posto_occupato(utente))
		return POSTO_OCCUPATO;
	/* ⛔ Here — and only here — the table is born: it is the only place that ADDS. */
	if (!posti_pronti())
		return POSTO_NIENTE_PIU_POSTI;
	for (int i = 0; i < quanti_posti; i++) {
		if (!attaccate[i].usato) {
			attaccate[i].usato = true;
			attaccate[i].chi = s;
			snprintf(attaccate[i].utente, sizeof attaccate[i].utente, "%s",
			         utente);
			return POSTO_PRESO;
		}
	}
	return POSTO_NIENTE_PIU_POSTI;
}

static int posti_occupati(void)
{
	int n = 0;
	for (int i = 0; i < quanti_posti; i++)
		if (attaccate[i].usato)
			n++;
	return n;
}

static void posto_lascia(const char *utente)
{
	for (int i = 0; i < quanti_posti; i++)
		if (attaccate[i].usato && strcmp(attaccate[i].utente, utente) == 0) {
			attaccate[i].usato = false;
			/* ⛔ And the pointer is zeroed HERE, together with the slot: it is
			 * the only point from which one can guarantee that a session about
			 * to be freed does not stay attached to the registry. */
			attaccate[i].chi = NULL;
		}
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐ THE ADDRESS BAN — §4.4-bis, rewritten on 10 Aug 2026
 *
 * `DECISIONI.md` §1.9, decided by the user: **three consecutive failed
 * authentications from the same address, and that address is out for 12 hours.**
 *
 * ⛔ WHAT HAS DISAPPEARED, AND IT MUST BE KNOWN WHEN READING THIS FILE.  The
 *    previous form — 5 attempts in 5 minutes, a 30 s window doubling up to
 *    15 minutes, **two** counters (one per user name and one per
 *    address), expiry after 30 minutes of quiet — was 🔸, that is written by us
 *    and never spoken.  What remains is **a single counter**, on the address.
 *
 *    ⭐ And with it disappears by construction the defect B5 found: the
 *       key contained the PORT, and with a single attempt per connection
 *       (§4.4) the port changes every time — that counter was always 1.
 *       Here the key is `s->indirizzo`, which `rcp_chiave_indirizzo()` has
 *       already normalised.
 *
 * ⛔ THE USER NAME DOES NOT COUNT.  Three different names count three: it is
 *    the decision, and it is also the only form a per-address counter can have
 *    without lying.  Whoever looks here for the per-name counter does not find
 *    it because it is not there.
 *
 * ⛔ THE THREE FAILURES MUST FALL WITHIN FIVE MINUTES, or the ban does not fire
 *    (the user's rule, 10 Aug 2026).  Two mistakes on Monday and one on
 *    Friday do NOT ban: whoever mistypes now and then is not whoever tries
 *    passwords.  And a **successful** authentication resets everything anyway.
 *
 *    ⚠ The window is SLIDING, and not anchored to the first failure: one keeps
 *      **the time of the last three**, and looks whether all three fall within
 *      five minutes.  With the window anchored to the first, three failures at
 *      0:00, 4:59 and 5:01 would restart the count from ONE — throwing away
 *      also the one at 4:59, which is two seconds from the last.  ⛔ Whoever
 *      tries passwords at a pace just slower than the window would never be
 *      stopped, and it is exactly the shape of defect that «the code was there
 *      and did nothing» has already produced once in this file.
 *
 * ⛔ THE BAN SURVIVES A RESTART (`DECISIONI.md` §1.9, invariant I7): a ban
 *    that resets on restart is a protection that loses itself, and whoever
 *    restarts for another reason does not know they removed it.  The file is
 *    written by `salva_ban()`; `rcp_ban_carica()` reads it back at startup.
 *
 *    ⚠ And the file carries an **absolute** time, not `ora`: `ora` is a
 *      MONOTONIC clock that restarts from an arbitrary point with every
 *      process, so writing it to disk would produce meaningless expiries after
 *      a restart.  The epoch in seconds is written and converted back at load.
 *
 * ⛔ AND THERE ARE TWO WAYS OUT (`DECISIONI.md` §1.9): the 12 hours passing, or
 *    `rcp_sblocca()` — which is the unblock command, and requires access to
 *    the machine.  ⭐ **It is also what makes B8 possible**: without it, a bench
 *    measuring the timing of authentication would have three samples and then
 *    half a day of silence.  Every unblock is written to the log.
 *
 * ⚠ THE TABLE HAS A BOTTOM, and finding R9.1 applies identically: if
 *   `trova_o_crea()` could fail, an uncounted failure would be a limiter that
 *   is not there.  So it does not fail: it evicts, and declares it.  ⛔ The
 *   victim is never a BANNED entry if there is one that is not — otherwise
 *   filling the table with invented addresses would be the way to erase one's
 *   own ban.
 *   ⚠ With twelve hours the slots free up much more slowly than before: hence
 *     the 256 slots instead of 64.  `[?]` That they are enough is not measured —
 *     an attacker with more than 256 addresses pushes the bans out alone, and
 *     the log line of the eviction is the only place where one would see it.
 *
 * ⛔ AND THERE IS NO LONGER ANY EXPIRY FOR QUIET.  The old form had one
 *    (30 minutes) and it served to give slots back to the table; here it would
 *    also give back the **attempts**, that is it would contradict
 *    «consecutive».  The slots are given back by the expiry of the ban and by
 *    the eviction.                                                           */
#define SOGLIA 3
#define FINESTRA 300000u     /* 5 minutes: the three failures must fit inside */
#define BAN_DURATA 43200000u /* 12 hours, in milliseconds */
#define MAX_TENTATIVI 256

static struct {
	char indirizzo[64];
	bool usato;
	/* ⛔ The time of the LAST THREE failures, not their number: it is what is
	 * needed to answer «three within five minutes» without anchoring the
	 * window to the first.  `quanti` says how many slots are full. */
	uint64_t falliti_t[SOGLIA];
	int quanti;
	uint64_t bannato_fino; /* monotonic, like `ora`; 0 = not banned */
	uint64_t ultimo_tocco;
} tentativi[MAX_TENTATIVI];

static char percorso_ban[512]; /* empty = not persisted (the bench, usually) */
/* ⛔⭐ THE ADDRESS WITHOUT THE PORT — found by B5 on 10 Aug 2026
 *
 * §4.4-bis wants «a counter per **source address**».  The first draft of this
 * module passed it `s->provenienza`, which is `192.168.0.2:44661` — **with the
 * port**.  And §4.4 allows **a single attempt per connection**, so the port
 * changes at every attempt: that counter was **always 1**, and it never
 * blocked anyone.
 *
 * ⚠ It is the worst shape of defect: the code was there, it looked right, it
 *   read well, and **it did nothing**.  No single-connection test sees it; no
 *   log names it; the symptom — «a password can be tried forever» — never
 *   shows up on its own.
 *
 * ⭐ It was found by the B5 check that tries SEVEN failed attempts with
 *    SEVEN DIFFERENT NAMES from the same address: with equal names the
 *    **per-name** counter covered the hole, and the bench would have been green.
 *    ⛔ From today that counter no longer exists, so the seven-name test is the
 *    only possible form — and it is what B8 demands.
 *
 * ⚠ It is cut at the LAST colon, not the first: an IPv6 address is
 *   `[fe80::1]:44661`, and cutting at the first would produce `[fe80`.
 *
 * ⛔ AND THE KEY CARRIES SQUARE BRACKETS EVEN FOR IPv4 — `[M]` 10 Aug
 *    2026, read in the server log and not deduced: `util::straddr()` of the
 *    ngtcp2 example **always** writes `[127.0.0.1]:55680`, so the key this
 *    module counts is `[127.0.0.1]`, with the brackets, and it is the one that
 *    ends up in the ban file.  ⚠ Whoever calls from outside — the unblock
 *    command, which receives an address typed by a person — must go through
 *    `rcp_chiave_indirizzo()`, or it will look for `192.168.0.2` where
 *    `[192.168.0.2]` is written and will be told «it was not banned».
 *
 * ⛔ AND HERE THERE WAS AN ASSUMPTION THAT THE UNBLOCK COMMAND BREAKS: that the
 *    port is always there.  Until today the only caller was the session, which
 *    carries `[fe80::1]:44661`; the unblock command carries `[fe80::1]` and
 *    nothing else, and cutting at the last colon reduced it to `[fe80:`.
 *    ⭐ The guard is one line: if it ends with `]` the port is not there, so
 *    there is nothing to cut.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ AND ON 10 AUG 2026 (NIGHT) THIS FUNCTION WAS REMOVED — finding B-8
 *
 * It was called `solo_indirizzo()` and removed the port **without adding the
 * brackets**.  Three places called it: `rcp_apri()`, `rcp_bannato()` and
 * `rcp_sblocca()`.  On the first ones it did no harm **by chance** — the host
 * already added the brackets itself — but on the two PUBLIC functions the
 * harm was measurable:
 *
 *     rcp_bannato("192.168.0.2")   = 0     ⛔ «it is not banned»
 *     rcp_bannato("[192.168.0.2]") = 1
 *
 * ⚠ And the form that answered **false** is exactly the one that
 *   `pagina.c` builds for IPv4 (`getnameinfo` + `"%s:%s"`).  Today it does no
 *   harm only because the caller normalises **first**, that is because the
 *   normalisation belonged to **the caller** — which is precisely what
 *   §4.4-bis forbids with a ⛔ and what `rcp.h` promises to do **in
 *   here**.
 *
 * ⭐ The cure is not adding the brackets to `solo_indirizzo()`: it is not having
 *    **two** functions that make the key.  One remains — the one below —
 *    and all three places use it.  ⚠ It is idempotent by construction, so
 *    whoever normalises twice gets the same key and no existing caller
 *    changes behaviour.
 * ------------------------------------------------------------------------ */

/* ⛔ The ban KEY, in the exact form in which §4.4-bis counts it — and the
 * reason why it is public lies entirely in one measurement.
 *
 * The host has two roads that arrive here, and they carry the address in two
 * different forms:
 *
 *   the session        `util::straddr()`, that is `[127.0.0.1]:55680` — brackets
 *                      and port, and this is the form that made the key;
 *   the command        what a person types: `127.0.0.1`, with nothing.
 *
 * ⛔ If the host built it itself, the day `straddr()` changed form the unblock
 *    command would start answering «it was not banned» to every address,
 *    forever and in silence: a command that always says the same thing has no
 *    symptom.  The format of the key is known by this file, and it is the
 *    only one that must know it.
 *
 * ⚠ The rule on colons, and it is worth the line it costs: with brackets the
 *   port is always recognisable; without, `127.0.0.1:53` has ONE colon (host
 *   and port) and `fe80::1` has two or more (and it is all address).  It is
 *   exactly the reason brackets exist.
 *
 * ⭐ AND SINCE 10 AUG 2026 (NIGHT) IT IS THE ONLY ONE that makes the key, inside
 *    and outside: `rcp_apri()`, `rcp_bannato()` and `rcp_sblocca()` call it.
 *    See the box above, finding B-8. */
void rcp_chiave_indirizzo(const char *testo, char *fuori, size_t cap)
{
	char nudo[64];
	if (!testo)
		testo = "?";
	if (testo[0] == '[') {
		const char *fine = strchr(testo, ']');
		size_t n = fine ? (size_t)(fine - testo) - 1 : strlen(testo) - 1;
		if (n >= sizeof nudo)
			n = sizeof nudo - 1;
		memcpy(nudo, testo + 1, n);
		nudo[n] = 0;
	} else {
		const char *primo = strchr(testo, ':');
		const char *ultimo = strrchr(testo, ':');
		/* a single colon = host:port; two or more = bare IPv6 */
		size_t n = (primo && primo == ultimo) ? (size_t)(primo - testo)
		                                      : strlen(testo);
		if (n >= sizeof nudo)
			n = sizeof nudo - 1;
		memcpy(nudo, testo, n);
		nudo[n] = 0;
	}
	snprintf(fuori, cap, "[%s]", nudo);
}

/* Only looks: ⛔ querying the guard MUST NOT consume a slot. */
static int trova(const char *indirizzo)
{
	for (int i = 0; i < MAX_TENTATIVI; i++)
		if (tentativi[i].usato &&
		    strcmp(tentativi[i].indirizzo, indirizzo) == 0)
			return i;
	return -1;
}

/* Returns the entry, creating it if needed.  ⛔ It never fails (R9.1): if the
 * table is full it evicts, and in `*sfrattata` it leaves the name of the entry
 * thrown away so that the caller WRITES it to the log. */
static int trova_o_crea(const char *indirizzo, uint64_t ora, const char **sfrattata)
{
	static char nome_sfrattato[64];
	*sfrattata = NULL;
	int i = trova(indirizzo);
	if (i >= 0)
		return i;
	int libero = -1, vittima = -1;
	for (int k = 0; k < MAX_TENTATIVI; k++) {
		if (!tentativi[k].usato) {
			libero = k;
			break;
		}
		bool k_bannata = ora < tentativi[k].bannato_fino;
		if (vittima < 0) {
			vittima = k;
			continue;
		}
		bool v_bannata = ora < tentativi[vittima].bannato_fino;
		if (v_bannata && !k_bannata) {
			vittima = k;
		} else if (v_bannata == k_bannata &&
		           tentativi[k].ultimo_tocco < tentativi[vittima].ultimo_tocco) {
			vittima = k;
		}
	}
	if (libero < 0) {
		libero = vittima; /* there always is one: MAX_TENTATIVI > 0 */
		snprintf(nome_sfrattato, sizeof nome_sfrattato, "%s",
		         tentativi[libero].indirizzo);
		*sfrattata = nome_sfrattato;
	}
	memset(&tentativi[libero], 0, sizeof tentativi[libero]);
	tentativi[libero].usato = true;
	tentativi[libero].ultimo_tocco = ora;
	snprintf(tentativi[libero].indirizzo, sizeof tentativi[libero].indirizzo,
	         "%s", indirizzo);
	return libero;
}

/* ⛔ Writes to file only the BANNED addresses, with the expiry in seconds
 * since the epoch.  It is called at every change — new ban, unblock — because a
 * ban that lives only in memory until the next periodic save is a ban that a
 * sudden restart takes away (I7).
 *
 * ⚠ It writes to a temporary file and renames: a `rename()` is atomic, and
 *   a ban file truncated halfway by a restart would be worse than no
 *   file — it would say «these addresses were not banned». */
static void salva_ban(rcp_sessione *s, uint64_t ora)
{
	if (percorso_ban[0] == 0)
		return;
	char tmp[sizeof percorso_ban + 8];
	snprintf(tmp, sizeof tmp, "%s.nuovo", percorso_ban);
	FILE *f = fopen(tmp, "w");
	if (!f) {
		if (s)
			reg(s, "⛔ could not write the ban file «%s»: the ban "
			       "lives only in memory and a restart removes it (§4.4-bis)",
			    tmp);
		return;
	}
	time_t adesso = time(NULL);
	int quanti = 0;
	for (int i = 0; i < MAX_TENTATIVI; i++) {
		if (!tentativi[i].usato || ora >= tentativi[i].bannato_fino)
			continue;
		uint64_t restano = tentativi[i].bannato_fino - ora;
		fprintf(f, "%s %lld\n", tentativi[i].indirizzo,
		        (long long)(adesso + (time_t)(restano / 1000)));
		quanti++;
	}
	fclose(f);
	if (rename(tmp, percorso_ban) != 0 && s)
		reg(s, "⛔ could not rename the ban file to «%s»",
		    percorso_ban);
	else if (s)
		reg(s, "the ban file is up to date: %d addresses in «%s»", quanti,
		    percorso_ban);
}

static bool bannato(const char *indirizzo, uint64_t ora, uint64_t *restano)
{
	if (restano)
		*restano = 0;
	int i = trova(indirizzo);
	if (i < 0)
		return false; /* never failed anything: it is a fact, not a slot run out */
	if (ora >= tentativi[i].bannato_fino)
		return false;
	if (restano)
		*restano = tentativi[i].bannato_fino - ora;
	return true;
}

static void segna_fallito(rcp_sessione *s, const char *indirizzo, uint64_t ora)
{
	const char *sfrattata = NULL;
	int i = trova_o_crea(indirizzo, ora, &sfrattata);
	if (sfrattata)
		reg(s, "⚠ attempt table full (%d entries): evicted the entry "
		       "«%s» to make room for «%s» — §4.4-bis",
		    MAX_TENTATIVI, sfrattata, indirizzo);
	tentativi[i].ultimo_tocco = ora;
	/* The ring of the last SOGLIA failures: it shifts by one and writes at the
	 * tail.  ⚠ Older than that they serve no question. */
	if (tentativi[i].quanti < SOGLIA) {
		tentativi[i].falliti_t[tentativi[i].quanti++] = ora;
	} else {
		memmove(tentativi[i].falliti_t, tentativi[i].falliti_t + 1,
		        (SOGLIA - 1) * sizeof tentativi[i].falliti_t[0]);
		tentativi[i].falliti_t[SOGLIA - 1] = ora;
	}
	int dentro = 0;
	for (int k = 0; k < tentativi[i].quanti; k++)
		if (ora - tentativi[i].falliti_t[k] <= FINESTRA)
			dentro++;
	reg(s, "failed attempt from %s: %d of %d within the %u minutes (§4.4-bis)",
	    indirizzo, dentro, SOGLIA, FINESTRA / 60000u);
	if (dentro >= SOGLIA) {
		tentativi[i].bannato_fino = ora + BAN_DURATA;
		reg(s, "⛔ BANNED address %s for %u hours: %d authentications "
		       "failed within %u minutes (§4.4-bis, DECISIONI.md §1.9)",
		    indirizzo, BAN_DURATA / 3600000u, dentro, FINESTRA / 60000u);
		salva_ban(s, ora);
	}
}

/* ⛔ Only a SUCCESSFUL authentication resets, and it is what «consecutive»
 * means.  The whole entry is reset: an address that gets in has no more history. */
static void azzera_falliti(rcp_sessione *s, const char *indirizzo, uint64_t ora)
{
	int i = trova(indirizzo);
	if (i < 0)
		return;
	if (tentativi[i].quanti > 0)
		reg(s, "successful login from %s: the count of failures goes back to "
		       "zero (there were %d) — §4.4-bis",
		    indirizzo, tentativi[i].quanti);
	memset(&tentativi[i], 0, sizeof tentativi[i]);
	(void)ora;
}
/* ------------------------------------------------------------------------ */
/* What the HOST calls: the page over TCP and the unblock command.
 *
 * ⛔ The page is served ALL THE SAME to a banned address, and says the attempts
 *    are used up (`DECISIONI.md` §1.9): whoever is banned by mistake is almost
 *    always the owner, and a network error would tell them nothing.  Whoever
 *    serves the page calls `rcp_bannato()` and writes the sentence.          */
bool rcp_bannato(const char *provenienza, uint64_t ora, uint64_t *restano_ms)
{
	char ind[64];
	/* ⛔ The key is made by `rcp_chiave_indirizzo()`, not by cutting the port:
	 *    `rcp.h` promises that «`provenienza` may carry the port: it is cut
	 *    in here», and whoever believes the header passes
	 *    `192.168.0.2` without brackets — finding B-8. */
	rcp_chiave_indirizzo(provenienza, ind, sizeof ind);
	return bannato(ind, ora, restano_ms);
}

/* ⛔ The unblock command.  Returns `true` if something was removed:
 * «it was not banned» and «I unblocked it» are two different facts, and whoever
 * commands must be able to tell them apart.  ⚠ And the unblock is written to
 * the log by the caller, which has the context: here there is no session to
 * hang it on. */
bool rcp_sblocca(const char *indirizzo, uint64_t ora)
{
	char ind[64];
	/* ⛔ §4.4-bis: «whoever types `192.168.0.2` at the unblock command MUST
	 *    reach the same key: normalisation belongs to the server, not to
	 *    whoever commands» — finding B-8. */
	rcp_chiave_indirizzo(indirizzo, ind, sizeof ind);
	int i = trova(ind);
	if (i < 0)
		return false;
	bool era_bannato = ora < tentativi[i].bannato_fino;
	memset(&tentativi[i], 0, sizeof tentativi[i]);
	salva_ban(NULL, ora);
	return era_bannato;
}

/* ⛔ Declares where the ban file lives and reads it back: a ban that does not
 * survive a restart is a protection that gets lost (I7).  Returns how many it
 * loaded, or -1 if the file was there and could not be read —
 * ⚠ «zero bans» and «I could not look» are two different facts
 * (`LEZIONI.md` §1.9 rule 1), and the caller must print them differently. */
int rcp_ban_carica(const char *percorso, uint64_t ora)
{
	percorso_ban[0] = 0;
	if (!percorso || !*percorso)
		return 0;
	snprintf(percorso_ban, sizeof percorso_ban, "%s", percorso);
	FILE *f = fopen(percorso_ban, "r");
	if (!f) {
		/* ⛔ HERE LAY THE SEVENTH GUISE OF THE DEFECT, INSIDE THE FUNCTION THE
		 *    HEADER DECLARES IMMUNE.  `rcp.h` promises «-1 if the file was
		 *    there and could not be read», and this line returned `0` on
		 *    ANY failure of `fopen()`: a file without permissions, a path whose
		 *    parent is not a directory, a disk that does not answer — all
		 *    «zero bans», that is **the protection switched off with the air
		 *    of having nothing to protect** (`LEZIONI.md` §1.9 rule 1, and I7).
		 *
		 * ⭐ Only one datum tells the two facts apart, and it is `errno`:
		 *    `ENOENT` means the file has not been born yet — no bans, and it is
		 *    not an error — and any other value means the file is there (or it
		 *    could not even be asked) and could not be looked at.  ⚠ The caller
		 *    MUST treat `-1` as a fault and not as a zero: whoever serves the
		 *    page says so, and whoever starts the server stops. */
		return errno == ENOENT ? 0 : -1;
	}
	time_t adesso = time(NULL);
	char riga[128];
	int quanti = 0;
	while (fgets(riga, sizeof riga, f)) {
		char ind[64];
		long long scad = 0;
		if (sscanf(riga, "%63s %lld", ind, &scad) != 2)
			continue;
		if (scad <= (long long)adesso)
			continue; /* expired while the server was off */
		const char *sfrattata = NULL;
		int i = trova_o_crea(ind, ora, &sfrattata);
		/* ⛔ No count is rebuilt: what survives the restart is the BAN, not
		 * the attempts that produced it. */
		tentativi[i].bannato_fino =
		    ora + (uint64_t)(scad - (long long)adesso) * 1000u;
		quanti++;
	}
	/* ⚠ And a read that stops halfway is also «I could not look»: `fgets`
	 *   returns NULL both at end of file and on an error, and the two are told
	 *   apart only with `ferror()`.  A ban file read halfway would say «these
	 *   addresses were not banned». */
	int rotto = ferror(f);
	fclose(f);
	return rotto ? -1 : quanti;
}

/* ⛔ For the bench only: between one test and the next one starts from zero.
 * In a real server nobody calls it, and it is written in the header. */
void rcp_azzera_registro_sessioni(void)
{
	/* ⚠ The table is allocated (phase 10): the cells that exist are zeroed,
	 *   and if it is not there yet there is nothing to zero. */
	if (attaccate)
		memset(attaccate, 0, (size_t)quanti_posti * sizeof *attaccate);
	memset(tentativi, 0, sizeof tentativi);
}

/* ------------------------------------------------------------------------ */
/* Writing the types of §6.0, big-endian, without alignment and without
 * padding.                                                                  */
typedef struct {
	uint8_t *b;
	size_t cap, len;
	bool pieno;
} scrittore;

static void sc_byte(scrittore *s, uint8_t v)
{
	if (s->len + 1 > s->cap) {
		s->pieno = true;
		return;
	}
	s->b[s->len++] = v;
}
static void sc_u16(scrittore *s, uint16_t v)
{
	sc_byte(s, (uint8_t)(v >> 8));
	sc_byte(s, (uint8_t)v);
}
static void sc_u32(scrittore *s, uint32_t v)
{
	sc_byte(s, (uint8_t)(v >> 24));
	sc_byte(s, (uint8_t)(v >> 16));
	sc_byte(s, (uint8_t)(v >> 8));
	sc_byte(s, (uint8_t)v);
}
/* ⛔ §6.0: `u64` big-endian, and it serves only the `istante` field of §6.2 —
 * the only eight-byte integer RCP/1 puts on the wire. */
static void sc_u64(scrittore *s, uint64_t v)
{
	for (int i = 7; i >= 0; i--)
		sc_byte(s, (uint8_t)(v >> (i * 8)));
}
static void sc_str(scrittore *s, const char *t)
{
	size_t n = strlen(t);
	sc_u16(s, (uint16_t)n);
	for (size_t i = 0; i < n; i++)
		sc_byte(s, (uint8_t)t[i]);
}

/* Reading, with the bounds check BEFORE taking the bytes. */
typedef struct {
	const uint8_t *b;
	size_t len, i;
	bool corto;
} lettore;

static uint8_t le_u8(lettore *l)
{
	if (l->i + 1 > l->len) {
		l->corto = true;
		return 0;
	}
	return l->b[l->i++];
}
static uint16_t le_u16(lettore *l)
{
	uint16_t a = le_u8(l);
	return (uint16_t)((a << 8) | le_u8(l));
}
static uint32_t le_u32(lettore *l)
{
	uint32_t a = le_u16(l);
	return (a << 16) | le_u16(l);
}
/* Copies a string into `fuori` (which must have room for n+1 bytes).
 * ⛔ It does not validate UTF-8: that is done by `utf8_valido`, called where needed. */
static size_t le_str(lettore *l, char *fuori, size_t cap)
{
	uint16_t n = le_u16(l);
	if (l->corto || l->i + n > l->len) {
		l->corto = true;
		return 0;
	}
	if (n + 1u > cap) {
		/* longer than the field allows: the caller will say so */
		l->i += n;
		return (size_t)n;
	}
	memcpy(fuori, l->b + l->i, n);
	fuori[n] = 0;
	l->i += n;
	return n;
}

/* §6.0: invalid UTF-8 is ERRORE_PROTOCOLLO. */
static bool utf8_valido(const char *s, size_t n)
{
	size_t i = 0;
	while (i < n) {
		uint8_t c = (uint8_t)s[i];
		size_t extra;
		if (c < 0x80)
			extra = 0;
		else if ((c & 0xE0) == 0xC0 && c >= 0xC2)
			extra = 1;
		else if ((c & 0xF0) == 0xE0)
			extra = 2;
		else if ((c & 0xF8) == 0xF0 && c <= 0xF4)
			extra = 3;
		else
			return false;
		/* ⚠ The continuation bytes must ALL BE THERE: without this
		 * check a sequence truncated at the end of the string would pass. */
		if (i + extra >= n)
			return false;
		for (size_t k = 1; k <= extra; k++)
			if ((((uint8_t)s[i + k]) & 0xC0) != 0x80)
				return false;
		i += extra + 1;
	}
	return true;
}

/* ⛔⭐ A NUL BYTE IN THE MIDDLE OF A STRING — finding R9.11.
 *
 * §6.0 says a string is «exactly `lunghezza` bytes».  All the validations of
 * this module work on the DECLARED LENGTH; all the uses work on the C STRING
 * that `le_str` terminates with a zero (`%s`, `strcmp`, `voce_presente`,
 * `strchr`, and PAM).  A `0x00` in the middle separates the two readings, and
 * `utf8_valido()` accepts it because `c < 0x80`:
 *
 *   `audio.codec` with value `opus\0pcm` — eight bytes, within the limit —
 *   sent away with `NIENTE_IN_COMUNE` a client that had declared
 *   `pcm`, that is it denied the fallback to whoever had not refused it;
 *   a user `root\0nemo` — nine bytes on the wire — sent `root` to PAM, and the
 *   log and the key of §4.4-bis said `root`.  What arrived and what was judged
 *   were two different strings, and no line said so.
 *
 * ⭐ §4.3 already closes it for capabilities: «a value is **printable** UTF-8
 *    text».  Here it is applied to the letter — and it also applies to the user
 *    name, for a second reason: the log is a file that is kept (§11.1), and a
 *    newline inside a name writes lines into it that nobody sent. */
static bool testo_stampabile(const char *s, size_t n)
{
	if (!utf8_valido(s, n))
		return false;
	for (size_t i = 0; i < n; i++) {
		uint8_t c = (uint8_t)s[i];
		if (c < 0x20 || c == 0x7F) /* the C0 controls and DEL: 0x00 included */
			return false;
	}
	return true;
}

/* §8.2: the reasons are fifteen, from 0x01 to 0x0F.  ⛔ And §3.1: «code 0
 * means closing without a reason and MUST NOT be used». */
static bool motivo_di_82(uint8_t m) { return m >= 0x01 && m <= 0x0F; }

/* ------------------------------------------------------------------------ */
/* (the declaration is at the top, above the attempt limiter) */
static void reg(rcp_sessione *s, const char *fmt, ...)
{
	char riga[512];
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(riga, sizeof riga, fmt, ap);
	va_end(ap);
	if (s->g.registra)
		s->g.registra(s->g.ctx, riga);
}

static void manda_messaggio(rcp_sessione *s, uint16_t tipo, const uint8_t *corpo,
                            size_t n)
{
	uint8_t testa[6];
	scrittore w = {testa, sizeof testa, 0, false};
	sc_u16(&w, tipo);
	sc_u32(&w, (uint32_t)n);
	uint8_t *tutto = (uint8_t *)malloc(6 + n);
	if (!tutto)
		return;
	memcpy(tutto, testa, 6);
	if (n)
		memcpy(tutto + 6, corpo, n);
	s->g.manda(s->g.ctx, tutto, 6 + n);
	free(tutto);
}

/* ⛔ §3.1, in order: one writes to the log WHAT happened, sends CONGEDO if
 * the channel is still usable, closes the session with the reason code.
 * The two roads exist because if one breaks the other still carries the
 * reason — in v1 the server wrote «farewell» and the client read
 * «network error» for three phases.                                         */
static void congeda(rcp_sessione *s, uint8_t motivo, const char *dettaglio)
{
	if (s->stato == S_FINITA)
		return;
	reg(s, "congedo motivo=%#04x dettaglio=%s stato=%s", motivo, dettaglio,
	    NOMI_STATO[s->stato]);
	/* ⛔⭐ §7.3 — AND BEFORE ANYTHING ELSE WHAT IS PRESSED IS RELEASED.
	 *
	 *     «When a connection ends — by farewell, by silence, by
	 *     error — the server MUST release every key and every button that
	 *     are pressed».  ⛔ It sits HERE, inside `congeda()`, and not next to
	 *     each of its thirty calls: `RCP.md` §11 calls it «the rule
	 *     with the highest harm/cost ratio of the document», and a rule with
	 *     that ratio is not entrusted to the discipline of whoever writes the
	 *     thirty-first.  It is invariant I7 read from inside — the protection
	 *     lives in the program, not in a line that can get lost.
	 *
	 * ⚠ The symptom one buys: a Ctrl left down in a session that
	 *   outlives the client makes the desktop unusable on reattach, and
	 *   nobody connects the two things. */
	rilascia_al_distacco(s, "farewell");
	uint8_t corpo[512];
	scrittore w = {corpo, sizeof corpo, 0, false};
	sc_byte(&w, motivo);
	sc_str(&w, dettaglio);
	if (!w.pieno)
		manda_messaggio(s, T_CONGEDO, corpo, w.len);
	if (s->attaccata) {
		posto_lascia(s->utente);
		s->attaccata = false;
	}
	s->stato = S_FINITA;
	s->g.chiudi(s->g.ctx, motivo);
}

/* ⛔ `RESPINTO` is the farewell of authentication: after it one closes with
 * the same reason, and does NOT also send CONGEDO (§4.4).                   */
static void respingi(rcp_sessione *s, uint8_t motivo)
{
	reg(s, "respinto motivo=%#04x utente=%s da=%s", motivo, s->utente,
	    s->provenienza);
	uint8_t corpo[1];
	corpo[0] = motivo;
	manda_messaggio(s, T_RESPINTO, corpo, 1);
	s->stato = S_FINITA;
	s->g.chiudi(s->g.ctx, motivo);
}

/* ------------------------------------------------------------------------ */
/* §4.3 — the capabilities                                                   */
static bool nome_lecito(const char *n, size_t len)
{
	if (len < 1 || len > 64)
		return false;
	for (size_t i = 0; i < len; i++) {
		char c = n[i];
		if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '.' ||
		      c == '_'))
			return false;
	}
	return true;
}

/* An entry inside a comma-separated list. */
static bool voce_presente(const char *elenco, const char *voce)
{
	size_t n = strlen(voce);
	const char *p = elenco;
	while (*p) {
		const char *virgola = strchr(p, ',');
		size_t m = virgola ? (size_t)(virgola - p) : strlen(p);
		if (m == n && strncmp(p, voce, n) == 0)
			return true;
		p = virgola ? virgola + 1 : p + m;
	}
	return false;
}

/* Intersects two comma-separated lists, in the CLIENT's order (§4.3:
 * «the one who chooses is the server, within the intersection, following the
 * client's order of preference»).  Returns the first common entry, or NULL.
 *
 * ⛔ `scarti` collects the entries thrown away because we do not know them.
 *    §4.3 says they are discarded; ⚠ but a discard that is not written is a
 *    successful negotiation with the opposite of what was wanted inside it —
 *    trap 4 of `LEZIONI.md` §4 — and the symptom arrives months later, in the
 *    form of «it is slow and nobody understands why».
 *
 * ⛔⭐ AND THREE DISCARDS DID NOT GO THROUGH `scarti` — finding R9.12, that is
 *    three silent tolerances inside the very function that takes care of the
 *    log:
 *
 *      an entry ≥ 31 bytes long: `n + 1 < cap` was false, because `cap` is
 *      `sizeof s->codec` = 32 — and that condition governed the
 *      CLASSIFICATION, not only the choice.  The entry was not compared,
 *      was not chosen and did not end up among the discards;
 *      an empty entry (`hevc,,av1`): same;
 *      the entries that did not fit in the discard buffer: discarded twice,
 *      and the second time in silence.
 *
 *    `video.codec = av1,questo.codec.ha.un.nome.lunghissimo` chose `av1` and
 *    wrote `negoziato video.codec=av1` **without** the discard line: the
 *    day a client of tomorrow offers a codec with a long name, the
 *    log — which §4.3 declares «the only place where that fact appears» —
 *    would not contain it.  §3: «a silent tolerance is indistinguishable from
 *    a defect».
 *
 * ⭐ `*quanti` counts ALL the discards, even those that do not fit in the
 *    buffer: the number tells the truth even when the list is truncated. */
static const char *prima_comune(const char *elenco_client, const char *nostro,
                                char *fuori, size_t cap, char *scarti,
                                size_t cap_scarti, int *quanti)
{
	if (scarti && cap_scarti)
		scarti[0] = 0;
	*quanti = 0;
	const char *scelta = NULL;
	const char *p = elenco_client;
	while (*p) {
		const char *virgola = strchr(p, ',');
		size_t n = virgola ? (size_t)(virgola - p) : strlen(p);
		/* ⚠ 257 and not 64: a capability value goes up to 256 bytes (§4.3),
		 *   and an entry that does not fit in the comparison buffer is
		 *   precisely the entry that used to vanish. */
		char voce[257];
		const char *da_scartare = NULL;
		if (n == 0) {
			/* `hevc,,av1`: §4.3 wants entries separated by commas, and an empty
			 * entry is not an entry.  It is not closed — it changes nothing of
			 * what is negotiated — but it is WRITTEN. */
			da_scartare = "(empty)";
		} else if (n >= sizeof voce) {
			da_scartare = "(entry longer than the allowed value)";
		} else {
			memcpy(voce, p, n);
			voce[n] = 0;
			/* ⛔ An unknown entry INSIDE a list is discarded, as an unknown
			 * name is discarded: it is the mechanism by which a client of
			 * tomorrow will talk to a server of today. */
			if (voce_presente(nostro, voce)) {
				/* ⚠ The FIRST common one is kept, but one does not leave: the
				 *   entries after it must still be classified, or the discard
				 *   that gets written would be only the one preceding the choice. */
				if (!scelta) {
					if (n + 1 > cap) {
						/* ⚠ It cannot happen: `nostro` is one of our constants
						 *   and our entries are short.  If it happened, the
						 *   entry is not lost in silence — it is discarded and
						 *   written, which is the point of this finding. */
						da_scartare = voce;
					} else {
						/* ⚠ `%.*s` and not `%s`: to the compiler the length of
						 *   `voce` is unknown, and with `%s` it warns about a
						 *   truncation that the guard above has already
						 *   excluded.  A warning known to be harmless is a
						 *   warning one stops reading the next day. */
						snprintf(fuori, cap, "%.*s", (int)n, voce);
						scelta = fuori;
					}
				}
			} else {
				da_scartare = voce;
			}
		}
		if (da_scartare) {
			(*quanti)++;
			if (scarti && cap_scarti) {
				size_t g = strlen(scarti);
				size_t m = strlen(da_scartare);
				if (g + m + 2 < cap_scarti)
					snprintf(scarti + g, cap_scarti - g, "%s%s", g ? "," : "",
					         da_scartare);
			}
		}
		p = virgola ? virgola + 1 : p + n;
	}
	return scelta;
}

/* What this server declares. */
/* ⛔⭐⭐ AV1 HAS GONE — 20 Aug 2026, `DECISIONI.md` §1.13-ter, decided
 *     by the user: «the choice is forced: we must abandon AV1».
 *
 * The three reasons, and the third arrived last:
 *   1. **Firefox for Android** has neither HEVC nor AV1 ⇒ for that browser the
 *      product did not exist, against the promise of §1.6;
 *   2. `[M]` AV1 was the only codec **without hardware anywhere** in
 *      this setup — software at both ends;
 *   3. ⛔ `[M]` 20 August: with AV1 **Firefox paints rectangular blocks**
 *      where Chrome and `ffmpeg/dav1d`, **on the same bytes and at the same
 *      instant**, are clean.  It was the suspect of the artefact hunt.
 *
 * ⚠ Number 2 of §6.2 stays AV1 forever: it is not reused (an old client
 *   that heard «2» would paint garbage without an error).  Here it leaves the
 *   NEGOTIATION, not the register of numbers. */
#define NOSTRO_CODEC_PREDEFINITO "hevc,h264"
#define NOSTRA_PROFONDITA "8,10"

/* ⭐⭐ PHASE 18 (30 Sep 2026) — THE CODEC LIST IS MEASURED, NOT WRITTEN.
 *
 * The parent SETS it at startup after the probe of `figlio_capacita_video()`:
 * «hevc» only if the card encodes HEVC, «h264» only if the card encodes
 * H.264, «» if nothing — ⛔ phase 19 (1 Oct 2026, `DECISIONI.md` §10.27): the
 * software fallback (OpenH264) has gone, no processor without a card.
 * ⛔ The browser must not
 * receive an offer the server cannot keep: negotiating «hevc» and
 * then not opening it was a black screen without a line naming it.
 * ⚠ The default stays yesterday's for the bench harness
 *   (`banchi/rcp/`), which has no card to probe; the product ALWAYS writes it
 *   (`main.c`), and with the list empty every CIAO ends in
 *   NIENTE_IN_COMUNE — declared at startup and in the farewell. */
static char nostro_codec[64] = NOSTRO_CODEC_PREDEFINITO;

void rcp_video_codec_imposta(const char *elenco)
{
	snprintf(nostro_codec, sizeof nostro_codec, "%s", elenco ? elenco : "");
}

const char *rcp_video_codec(void)
{
	return nostro_codec;
}
#define NOSTRO_AUDIO "opus,pcm"

static void manda_eccomi(rcp_sessione *s)
{
	uint8_t corpo[1024];
	scrittore w = {corpo, sizeof corpo, 0, false};
	sc_u16(&w, RCP_VERSIONE);
	sc_u16(&w, 5); /* how many capabilities */
	sc_str(&w, "video.codec");
	sc_str(&w, nostro_codec);
	sc_str(&w, "video.profondita");
	sc_str(&w, NOSTRA_PROFONDITA);
	sc_str(&w, "audio.codec");
	sc_str(&w, NOSTRO_AUDIO);
	sc_str(&w, "appunti.testo");
	sc_str(&w, "si");
	/* ⛔ §4.3: `banco.marca` is `no` in every normal installation, and a
	 * server that declared it `si` by mistake writes it to the log at every
	 * startup.
	 *
	 * ⛔⭐ AND THE DECLARATION IS READ FROM THE SWITCH, NOT FROM A CONSTANT —
	 *    finding R9.14.  Here there was the string `"no"` written by hand:
	 *    bringing `BANCO_ACCESO` to 1 — the only way foreseen today to switch
	 *    the function on — the server ACCEPTED `BANCO_MARCA` and painted on
	 *    someone's desktop while its `ECCOMI` kept declaring `no`.  Two
	 *    places that must change together and no link between them: §7.5
	 *    rule 3 («the server MUST declare it»), and invariant I6.
	 *    ⚠ The log line of the switch-on is in `rcp_apri()`, which is
	 *      the only «startup» this module knows. */
	sc_str(&w, "banco.marca");
	sc_str(&w, BANCO_ACCESO ? "si" : "no");
	if (!w.pieno)
		manda_messaggio(s, T_ECCOMI, corpo, w.len);
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐ `video.misura_massima` — THE DECODER CEILING (§4.3, §4.5)
 *
 * Reads `WIDTHxHEIGHT` in **pixels**, that is two decimal integers separated
 * by a lowercase `x` and nothing else.  Returns `false` if the string does not
 * have that form.
 *
 * ⛔ And the form is checked in full, digit by digit, instead of trusting
 *    `sscanf("%ux%u")`: that accepts `1080.75x2340.25` reading `1080` and
 *    stopping at the dot, that is it would take as good a ceiling the client
 *    did not declare.  ⚠ It is exactly the value our page sent before the
 *    night of 10 Aug 2026 (finding B-6): a phone at factor 2.75 sends
 *    `1080.75x2340.25`.
 *
 * ⚠ Zero is not a size: a ceiling of 0 pixels cannot be respected by any
 *   legal canvas, and treating it as a number would send away every `ATTACCA`
 *   with `SESSIONE_NON_SERVIBILE` without anything naming the field. */
static bool misura_massima_legge(const char *v, uint32_t *l, uint32_t *a)
{
	unsigned long long n[2] = {0, 0};
	int quante[2] = {0, 0};
	int i = 0;

	for (const char *p = v; *p; p++) {
		if (*p == 'x' && i == 0) {
			i = 1;
			continue;
		}
		if (*p < '0' || *p > '9')
			return false;
		if (quante[i] > 9) /* more than ten digits: beyond any screen */
			return false;
		n[i] = n[i] * 10u + (unsigned)(*p - '0');
		quante[i]++;
	}
	if (i != 1 || quante[0] == 0 || quante[1] == 0)
		return false;
	if (n[0] == 0 || n[1] == 0 || n[0] > 0xffffffffull || n[1] > 0xffffffffull)
		return false;
	*l = (uint32_t)n[0];
	*a = (uint32_t)n[1];
	return true;
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐ `video.livello` — THE DECODER LEVEL (§4.3)
 *
 * Reads `MAJOR` or `MAJOR.MINOR` — `5`, `5.1`, `3.0` — and returns the
 * number in TENTHS: `5.1` ⇒ `51`, `5` ⇒ `50`.  ⚠ `false` if the string does not
 * have that form.
 *
 * ⛔ Why tenths and not a `double`: because the value serves a
 *    COMPARISON, and two roads that write `5.1` in floating point can give
 *    two numbers that are not equal.  ⭐ And tenths are also the alphabet in
 *    which the level is written in decoder strings: H.264 carries
 *    `level_idc = major*10 + minor` (`51` = `0x33`, the tail of
 *    `avc1.640033`), HEVC carries `general_level_idc = (major*10 +
 *    minor) * 3` (`153` = `L153`).  ⇒ A level read here and one read
 *    from the SPS on the other side compare without tables.
 *
 * ⚠ The form is checked digit by digit, and for the same reason as
 *   `misura_massima_legge()`: `sscanf("%u.%u")` would take as good
 *   `5.1.2` stopping at the second dot, that is a level the client did not
 *   declare.  ⛔ And the minor part is ONE digit: `5.10` is not a form
 *   that §4.3 defines, and reading it as `5.1` would be guessing.
 *
 * ⚠ Zero is not a level: no stream can respect it, and taking it as good
 *   would make every session write «produced 4.0 > asked 0.0». */
static bool livello_legge(const char *v, uint32_t *x10)
{
	unsigned maggiore = 0, minore = 0;
	int cifre_ma = 0, cifre_mi = 0;
	bool dopo_il_punto = false;

	for (const char *p = v; *p; p++) {
		if (*p == '.' && !dopo_il_punto) {
			dopo_il_punto = true;
			continue;
		}
		if (*p < '0' || *p > '9')
			return false;
		if (dopo_il_punto) {
			if (cifre_mi > 0) /* `5.10`: §4.3 does not define this form */
				return false;
			minore = (unsigned)(*p - '0');
			cifre_mi++;
		} else {
			if (cifre_ma > 2) /* more than three digits: no such level exists */
				return false;
			maggiore = maggiore * 10u + (unsigned)(*p - '0');
			cifre_ma++;
		}
	}
	if (cifre_ma == 0 || (dopo_il_punto && cifre_mi == 0))
		return false;
	if (maggiore == 0)
		return false;
	*x10 = maggiore * 10u + minore;
	return true;
}

/* ------------------------------------------------------------------------ */
/* How many UNKNOWN capability names this server can remember for the
 * duplicate check of §4.3 — see the box inside `tratta_ciao()`. */
#define MAX_VISTI 64

static bool tratta_ciao(rcp_sessione *s, lettore *l)
{
	uint16_t versione = le_u16(l);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "CIAO without version");
		return false;
	}
	/* ⛔ §2.4: «the two MUST match» — the path `/rcp/1` says 1, and a
	 * `CIAO(2)` on that path is VERSIONE_INCOMPATIBILE, **not a
	 * negotiation to resolve**.
	 *
	 * ⚠ And here `RCP.md` contradicts itself, and it is the second contradiction
	 *   found in this document by a bench (the first was the underscore of §4.3,
	 *   found by the B4 validator).  §9 says: *«the server chooses the highest
	 *   it can speak that does not exceed the one of the CIAO»* — that is 1, and
	 *   an `ECCOMI(1)`.  §2.4 says `VERSIONE_INCOMPATIBILE`.  The two rules give
	 *   **different bytes on the wire for the same input**, and neither of the
	 *   two cites the other.
	 *
	 * ⭐ §2.4 wins, because it is the more specific and because it is the one
	 *    written to resolve precisely this case (finding R1.24).  ⚠ The first
	 *    round of this module had applied §9 to the letter and ACCEPTED a
	 *    CIAO(2): B5 found it.  It is in `FASI.md` §01-filo-nudo.
	 *
	 * ⚠ And the comparison is with the version of the PATH, which here is the
	 *   only one the server serves.  A server that served `/rcp/1` and `/rcp/2`
	 *   would pass here the version of the path, not a constant. */
	if (versione != RCP_VERSIONE) {
		congeda(s, RCP_VERSIONE_INCOMPATIBILE,
		        "the CIAO version is not the one of the path");
		return false;
	}
	uint16_t quante = le_u16(l);
	/* ⛔⭐ THE MEMORY OF NAMES ALREADY SEEN HAD A BOTTOM, AND BEYOND THE BOTTOM
	 *    «THE LAST ONE WON» — finding R9.6.
	 *
	 *    §4.3: «a name repeated twice is ERRORE_PROTOCOLLO.  "The last one
	 *    wins" and "the first one wins" are two different implementations of
	 *    the same document».  `quante` is a `u16`: the client can declare up
	 *    to 65 535 capabilities, and here 32 were remembered — with an `if`
	 *    without `else` and without a log line.  A `CIAO` with 32 capabilities
	 *    with a legitimate and unknown name followed by `video.codec=hevc` and
	 *    `video.codec=av1` was not sent away: `snprintf` ran twice and
	 *    **the second won**.  ⚠ The `capacita-ripetuta` case of B5 uses THREE
	 *    capabilities: it stays green forever.
	 *
	 * ⭐ The cure has two halves, because the two cases do not weigh the same:
	 *
	 *    the KNOWN names — the nine of §4.3 — are remembered **all, always**,
	 *    in a bit mask.  They are the ones that change the behaviour, and
	 *    the duplicate that does harm is theirs;
	 *
	 *    the UNKNOWN names are remembered up to `MAX_VISTI`, and beyond that
	 *    number ⛔ **it is written to the log** that from there on the
	 *    repetition of an unknown name is no longer detectable.  §3: «every
	 *    tolerance must be written to the log; a silent tolerance is
	 *    indistinguishable from a defect».
	 *
	 * ⚠ Why one does not simply close when the memory runs out: a `CIAO` with
	 *   four hundred unknown capabilities is CONFORMING (§6.1), and §3 exception 1
	 *   requires ignoring them and carrying on.  Closing would be a red on the
	 *   right code of tomorrow's client — the opposite defect, and it costs more. */
	static const char *const NOMI_NOTI[] = {
	    "video.codec",   "video.profondita", "video.livello",
	    "video.misura_massima", "audio.codec", "input.tocco",
	    "appunti.testo", "client.nome",      "banco.marca",
	    NULL};
	char visti[MAX_VISTI][65];
	int n_visti = 0;
	uint16_t visti_noti = 0;
	bool detta_la_memoria_finita = false;
	char c_codec[257] = "", c_prof[257] = "", c_audio[257] = "";
	char c_misura[257] = "", c_livello[257] = "";
	for (uint16_t k = 0; k < quante; k++) {
		char nome[65], valore[257];
		size_t ln = le_str(l, nome, sizeof nome);
		size_t lv = le_str(l, valore, sizeof valore);
		if (l->corto) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "capability list truncated");
			return false;
		}
		if (!nome_lecito(nome, ln)) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "malformed capability name");
			return false;
		}
		if (lv == 0) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "capability with an empty value");
			return false;
		}
		/* ⚠ The order of the two terms of the `||` is not indifferent and is not
		 *   to be touched: `lv > 256` FIRST prevents `testo_stampabile` from
		 *   reading beyond the buffer when the string does not fit (see the
		 *   comment of `le_str`, and suspicion R9.18 which stays open). */
		if (lv > 256 || !testo_stampabile(valore, lv)) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "invalid capability value");
			return false;
		}
		/* ⛔ A repeated name is ERRORE_PROTOCOLLO: «the last one wins» and «the
		 * first one wins» are two implementations of the same document. */
		bool ripetuto = false;
		int noto = -1;
		for (int i = 0; NOMI_NOTI[i]; i++)
			if (strcmp(NOMI_NOTI[i], nome) == 0) {
				noto = i;
				break;
			}
		if (noto >= 0) {
			ripetuto = (visti_noti >> noto) & 1u;
			visti_noti |= (uint16_t)(1u << noto);
		} else {
			for (int i = 0; i < n_visti; i++)
				if (strcmp(visti[i], nome) == 0) {
					ripetuto = true;
					break;
				}
			if (n_visti < MAX_VISTI) {
				snprintf(visti[n_visti++], sizeof visti[0], "%s", nome);
			} else if (!detta_la_memoria_finita) {
				detta_la_memoria_finita = true;
				reg(s, "⚠ more than %d capabilities with an unknown name: from "
				       "here on the REPETITION of an unknown name is no longer "
				       "detectable (§4.3), and the names of §4.3 all remain so",
				    MAX_VISTI);
			}
		}
		if (ripetuto) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "repeated capability");
			return false;
		}
		/* ⛔ A capability from the wrong side is ERRORE_PROTOCOLLO: the name is
		 * known, so the exception for unknown names does not cover it. */
		if (strcmp(nome, "banco.marca") == 0) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "banco.marca does not come from the client");
			return false;
		}
		if (strcmp(nome, "video.codec") == 0)
			snprintf(c_codec, sizeof c_codec, "%s", valore);
		else if (strcmp(nome, "video.profondita") == 0)
			snprintf(c_prof, sizeof c_prof, "%s", valore);
		else if (strcmp(nome, "audio.codec") == 0)
			snprintf(c_audio, sizeof c_audio, "%s", valore);
		else if (strcmp(nome, "video.misura_massima") == 0)
			snprintf(c_misura, sizeof c_misura, "%s", valore);
		/* ⛔⭐ `video.livello` — AND UNTIL TODAY THIS LINE WAS NOT THERE.  The
		 *     name was in `NOMI_NOTI` (that is the server knew it was
		 *     REPEATED), the value went through the loop and nobody kept it:
		 *     the exact same shape as B-1 on `video.misura_massima`, and with
		 *     the same mute symptom of §4.3 — «the browser does not open the
		 *     stream». */
		else if (strcmp(nome, "video.livello") == 0)
			snprintf(c_livello, sizeof c_livello, "%s", valore);
		/* ⭐⭐ §7.4 — `appunti.testo`, and until 17 Aug 2026 this value
		 *     was recognised as a legitimate name and then **thrown away**: it
		 *     was exactly the shape of finding B-1 on `video.misura_massima`.
		 *
		 * ⛔ And it serves two things that cannot be done without it: NOT
		 *    announcing clipboard to a client that did not ask for it, and
		 *    REFUSING bytes on channel `0x02` from a client that did not declare
		 *    it — that is a capability used without negotiating it, which is the
		 *    case §4.3 exists to make impossible.
		 * ⚠ Any value other than `si` counts as `no`: §4.3 says the values
		 *   of this capability are two, and a third value is a client that
		 *   declares something the document does not define — it is treated as
		 *   the no, and the negotiation line writes it. */
		else if (strcmp(nome, "appunti.testo") == 0)
			s->negozia_appunti = strcmp(valore, "si") == 0;
	}
	/* ⛔⭐ THE DECODER CEILING IS KEPT — finding B-1, night of 10 Aug
	 *     2026.  §4.5: «the granted canvas MUST respect
	 *     `video.misura_massima` if the client declared it», and §4.3: «it does
	 *     not change the canvas: it is a ceiling […] because the decoder of a
	 *     phone has limits its screen does not declare».
	 *
	 * ⛔ Before today this value was recognised as a legitimate name and then
	 *    **thrown away**: the server granted exactly what the client
	 *    asked for, even twice what it had declared it could
	 *    decode.  ⚠ And the symptom is not a network error: it is «the browser
	 *    does not open the stream» in phase 2, with the diagnosis aimed at the
	 *    encoder.
	 *
	 * ⛔ And a MALFORMED value is not taken as good and not thrown away in
	 *    silence: §3 exception 1 allows ignoring a value one does not
	 *    understand, and the line below that table requires **writing it to the
	 *    log** — «a silent tolerance is indistinguishable from a
	 *    defect». */
	if (c_misura[0]) {
		if (misura_massima_legge(c_misura, &s->max_l, &s->max_a)) {
			reg(s, "the client declares video.misura_massima=%ux%u: it is the "
			       "ceiling the granted canvas MUST respect (§4.5)",
			    s->max_l, s->max_a);
		} else {
			s->max_l = s->max_a = 0;
			reg(s, "⚠ TOLERANCE (§3 exception 1): video.misura_massima=«%s» "
			       "does not have the WIDTHxHEIGHT form of §4.3 (whole pixels) — "
			       "the value is ignored, and the canvas will have NO ceiling",
			    c_misura);
		}
	}

	/* ⛔⭐⭐ `video.livello` — THE SECOND DECODER CEILING, and until
	 *      23 Aug 2026 the server DID NOT READ IT.
	 *
	 * `RCP.md` §4.3, row 701 of the capability table: *«the maximum level it
	 * can decode, e.g. `5.1`.  ⛔ The server **MUST** emit a stream of a level
	 * not higher, and **does not guess it**: a level declared too low does not
	 * give a network error, **it makes the decoder refuse the configuration**
	 * and the symptom is "the browser does not open the stream" (finding O12)»*.
	 *
	 * ⛔ AND IT IS PRECISELY BECAUSE THE SYMPTOM IS MUTE THAT THE NUMBER IS
	 *    WRITTEN.  A wrong level produces a red nowhere: it produces a black
	 *    screen, and a hunt that starts from the encoder or from the network —
	 *    that is from the wrong side.  These lines are the only place where
	 *    the REQUESTED number appears, and without them there is nothing to
	 *    compare with the one produced.
	 *
	 * ⛔⚠ AND THE COMPARISON IS NOT MADE HERE, but since tonight IT IS MADE — in
	 *     the child.  This module does not see a byte of stream:
	 *     `rcp_video_spedisci()` receives opaque data, and §4.3 is the only
	 *     document rcp.c knows (see the box of `rcp.h`).  ⇒ Here the requested
	 *     number is read and HANDED OVER (`rcp_livello_negoziato()`); the
	 *     produced level is read from the SPS (`codificatore.c`,
	 *     `leggi_sps_h264`/`leggi_sps_hevc`) and the comparison is made by
	 *     whoever has both numbers in hand, that is the child.
	 *     ⛔ Until 23 Aug 2026 the chain was not there, and the defect was
	 *       MEASURED: `video.livello=5.1` requested, **5.2** produced at
	 *       3840x2160.  The chain is `rcp.h` → `webtransport.c` (the hook
	 *       `wt_video_richiesta`) → `main.c` → `figlio.h` (`figli_video`) →
	 *       `figlio.c` (`struct corpo_video`, which kept its `riempi` byte
	 *       free on purpose).  It is the same chain the negotiated DEPTH
	 *       travelled on 17 Aug 2026 — and that day the defect was
	 *       identical: two true numbers in two processes, and nobody putting
	 *       them side by side.
	 *
	 * ⛔ A MALFORMED value is not taken as good and not thrown away in
	 *    silence, as for `video.misura_massima`: §3 exception 1 allows
	 *    ignoring it, and the line below that table requires writing it. */
	if (c_livello[0]) {
		if (livello_legge(c_livello, &s->livello_x10)) {
			reg(s, "the client declares video.livello=%s (= %u.%u, that is "
			       "level_idc %u in H.264 and L%u in HEVC): §4.3 forbids the "
			       "server to emit a stream HIGHER than this",
			    c_livello, s->livello_x10 / 10u, s->livello_x10 % 10u,
			    s->livello_x10, s->livello_x10 * 3u);
			reg(s, "⭐ and since tonight this number CROSSES the process "
			       "boundary: `rcp_livello_negoziato()` → `webtransport` → "
			       "`main` → `figli_video()` → the child, which IMPOSES it on "
			       "the encoder and then reads it back from the SPS (R31).  ⚠ The "
			       "verdict is in the child's «§4.3 — LIVELLO» line, not "
			       "here: here there is only the requested number");
		} else {
			s->livello_x10 = 0;
			reg(s, "⚠ TOLERANCE (§3 exception 1): video.livello=«%s» does not "
			       "have the MAJOR.MINOR form of §4.3 (e.g. «5.1») — the value is "
			       "ignored, and §4.3 will have no level to enforce",
			    c_livello);
		}
	} else {
		/* ⚠ §4.3 does not OBLIGE the client to declare it, and the absence is
		 *   written all the same: «not declared» and «declared and thrown away»
		 *   look the same in yesterday's log, and they are two different things. */
		reg(s, "the client does NOT declare video.livello: §4.3 does not "
		       "require it, and the server does not guess one — no level ceiling");
	}

	/* ⛔ §4.3: `pcm` and `8` MUST be declared by BOTH — `pcm` is the
	 * base always available, and it serves as a positive control when Opus is
	 * not negotiated.  ⚠ And whoever does not declare them is sent away with
	 * NIENTE_IN_COMUNE, **not** with ERRORE_PROTOCOLLO: it did not write
	 * wrongly, it has nothing to talk about.  Without this check the
	 * intersection is enough on its own — a client that offers only `opus`
	 * passes — and nobody applies the line of §4.3. */
	if (!voce_presente(c_audio, "pcm")) {
		congeda(s, RCP_NIENTE_IN_COMUNE,
		        "the client does not declare pcm in audio.codec");
		return false;
	}
	if (!voce_presente(c_prof, "8")) {
		congeda(s, RCP_NIENTE_IN_COMUNE,
		        "the client does not declare 8 in video.profondita");
		return false;
	}
	/* ⛔ If the intersection is empty the client is sent away with
	 * NIENTE_IN_COMUNE, not with ERRORE_PROTOCOLLO: it did not write wrongly,
	 * it has nothing to talk about. */
	char sc_codec[257], sc_prof[257], sc_audio[257];
	int n_codec = 0, n_prof = 0, n_audio = 0;
	if (!nostro_codec[0]) {
		/* ⛔ Phase 18-19: the server cannot encode anything, and says so with
		 *    the name of the cause — the startup log carries the reason. */
		congeda(s, RCP_NIENTE_IN_COMUNE,
		        "this server cannot encode video: no capable card, "
		        "no codec in ECCOMI (REMOTIX encodes only on the card — "
		        "see the startup log)");
		return false;
	}
	if (!prima_comune(c_codec, nostro_codec, s->codec, sizeof s->codec,
	                  sc_codec, sizeof sc_codec, &n_codec) ||
	    !prima_comune(c_prof, NOSTRA_PROFONDITA, s->profondita,
	                  sizeof s->profondita, sc_prof, sizeof sc_prof, &n_prof) ||
	    !prima_comune(c_audio, NOSTRO_AUDIO, s->audio, sizeof s->audio,
	                  sc_audio, sizeof sc_audio, &n_audio)) {
		congeda(s, RCP_NIENTE_IN_COMUNE, "no shared codec");
		return false;
	}
	/* ⛔ The choice is WRITTEN: a successful negotiation with the opposite
	 * of what was wanted inside it is seen only if someone writes it. */
	reg(s, "negoziato video.codec=%s video.profondita=%s audio.codec=%s",
	    s->codec, s->profondita, s->audio);
	/* ⛔ And the DISCARD is written in turn: «I chose hevc» does not say that
	 * vp9 was thrown away, and the day tomorrow's client offers a codec this
	 * server does not know, the log is the only place where that fact
	 * appears. */
	/* ⚠ And HOW MANY there are is written too, not only which: the list can be
	 *   truncated by the buffer, the number cannot (finding R9.12). */
	if (n_codec || n_prof || n_audio)
		reg(s, "discarded unknown entries: video.codec=[%s] (%d) "
		       "video.profondita=[%s] (%d) audio.codec=[%s] (%d)",
		    sc_codec, n_codec, sc_prof, n_prof, sc_audio, n_audio);
	manda_eccomi(s);
	s->stato = S_ATTESA_CREDENZIALI;
	return true;
}

static bool tratta_credenziali(rcp_sessione *s, lettore *l, uint64_t ora)
{
	char utente[257], parola[1025];
	size_t lu = le_str(l, utente, sizeof utente);
	size_t lp = le_str(l, parola, sizeof parola);
	/* ⛔ THE LOCAL COPY IS ZEROED ON EVERY ROAD, NOT ONLY ON THE GOOD ONE —
	 * finding R9.8.  The `memset` sat at the bottom, after the PAM answer: on
	 * every error path that sends the client away below — user not UTF-8, user
	 * or password out of range — the password stayed on the stack.  The
	 * `utente-vuoto` case of B5 is exactly this: a 1024-byte password, a user
	 * of zero, and one leaves from here.  ⚠ The three repeated lines are
	 * deliberate: a common exit `goto` reads worse than three lines that say
	 * the same thing where one happens to look. */
	if (l->corto) {
		memset(parola, 0, sizeof parola);
		congeda(s, RCP_ERRORE_PROTOCOLLO, "CREDENZIALI truncated");
		return false;
	}
	/* §4.4: the ranges.  An empty string is legal by §6.0, and without
	 * these limits a `CREDENZIALI` with two zero-byte strings would be
	 * conforming — and an attacker would increment no counter. */
	if (lu < 1 || lu > 256 || lp < 1 || lp > 1024) {
		memset(parola, 0, sizeof parola);
		congeda(s, RCP_ERRORE_PROTOCOLLO, "user or password out of range");
		return false;
	}
	/* ⛔ §4.3 applies to capabilities, but the reason for `testo_stampabile`
	 * applies here more than anywhere (finding R9.11): a nine-byte `root\0nemo`
	 * passed the ranges, passed `utf8_valido`, and sent `root` to PAM.
	 * What arrived and what is judged must be the same string, or the log and
	 * the key of §4.4-bis name a user that was not on the wire. */
	if (!testo_stampabile(utente, lu)) {
		memset(parola, 0, sizeof parola);
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "the user is not printable UTF-8 text");
		return false;
	}
	/* ⚠ Of the password ONLY the NUL byte is checked, and the reason is the
	 *   same: with a zero in the middle PAM would judge a prefix of what
	 *   arrived.  ⛔ It is not required to be printable: §4.4 does not ask it,
	 *   and a password can contain whatever it wants. */
	if (strlen(parola) != lp) {
		memset(parola, 0, sizeof parola);
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "the password contains a null byte: what arrives and what "
		        "would be judged would be two different things");
		return false;
	}
	snprintf(s->utente, sizeof s->utente, "%s", utente);
	/* ⛔ Three lines of instrumentation, and they are not incidental: on 10 Aug
	 * 2026 the handshake stopped here and «CREDENZIALI did not arrive»
	 * and «PAM does not answer» looked the same — that is like nothing.
	 * ⚠ The password does NOT appear, at any level (§4.4) — and since today
	 *   neither does its EXACT LENGTH, which was here: §11.1 treats the log as a
	 *   file that is kept, and the length of every password tried,
	 *   successful or not, is not something to keep (finding R9.8).  To tell
	 *   «it did not arrive» from «PAM does not answer» this line is
	 *   enough. */
	reg(s, "CREDENZIALI received utente=%s (with password)", s->utente);

	/* ⛔ The limiter BEFORE PAM, and the refusal is immediate: §4.4-bis says
	 * the wait is a WINDOW in which one refuses, not a delay — with a single
	 * attempt per connection, a server that delayed by fifteen minutes
	 * would never deliver the refusal. */
	uint64_t restano = 0;
	/* ⛔⭐ AND FROM HERE DOWN ONE STARTS FROM DENIED, ALWAYS — invariant I3.
	 *
	 * Before 12 Aug 2026 `cred_buone` took its value inside the only `else`
	 * below, and there was no other road: PAM had already answered when this
	 * function returned.  ⚠ Now the roads are four — banned, helper that does
	 * not take the question, synchronous fallback check, and the good road
	 * that WAITS — and three of them leave here without any verdict in hand.
	 * A field left at its previous value on one of those roads would be a
	 * «yes» arrived by inertia. */
	s->cred_buone = false;
	s->cred_motivo = RCP_CREDENZIALI_ERRATE;
	s->verdetto_atteso = false;
	s->no_e_nostro = false;
	if (bannato(s->indirizzo, ora, &restano)) {
		/* ⛔ The ban refuses WITHOUT querying PAM, and it must be known from
		 * reading the reason on the wire: `TROPPI_TENTATIVI` and
		 * `CREDENZIALI_ERRATE` cannot come from the same road.  ⭐ It is the
		 * byte that on 10 Aug 2026 separated the two suspects of B8 — whoever
		 * reads a `CREDENZIALI_ERRATE` is looking at PAM, not at this line. */
		s->cred_buone = false;
		s->cred_motivo = RCP_TROPPI_TENTATIVI;
		reg(s, "⛔ address %s BANNED: %llu minutes remain, PAM is not "
		       "queried (§4.4-bis)",
		    s->indirizzo, (unsigned long long)(restano / 60000u));
	} else if (s->g.chiedi_verifica) {
		/* ⭐⭐ THE GOOD ROAD — `DECISIONI.md` §1.10, 12 Aug 2026.
		 *
		 * ⛔ Here one does NOT wait for PAM.  One asks a helper process and
		 *    returns at once to the host, which returns to its `poll`: it is the
		 *    only way in which «while one authenticates, the others do not
		 *    notice» can be true on a single-threaded server.
		 *
		 * ⚠ And the count of §4.4-bis does NOT move here: now one knows that
		 *   one asked, not what was answered.  It moves in `rcp_verdetto()`,
		 *   which is the point where the fact exists. */
		if (s->g.chiedi_verifica(s->g.ctx, utente, parola, &s->pratica)) {
			s->verdetto_atteso = true;
			reg(s, "PAM asked of the helper, request %llu: the thread stays "
			       "free (DECISIONI.md §1.10)",
			    (unsigned long long)s->pratica);
		} else {
			/* ⛔ THE QUESTION DID NOT LEAVE ⇒ NO, at once.  It is I3 to the
			 *    letter: «design so that failure is a no, not a maybe».
			 * ⚠ And it does not count as a failed attempt: the defect is OURS,
			 *   and §4.4-bis lists among the things that do not ban precisely
			 *   those that «would ban someone who did nothing wrong». */
			s->no_e_nostro = true;
			reg(s, "⛔ the question to PAM did not leave: RESPINTO without appeal "
			       "(invariant I3).  ⚠ And it does NOT count as a failed attempt "
			       "of §4.4-bis: the defect is ours, and a ban for a defect of "
			       "ours would be the worst possible diagnosis");
		}
	} else {
		/* ⚠ THE DECLARED FALLBACK (`CODER.md` §4.2), and it blocks whoever
		 *   calls it: it is the road of the in-process benches, where there is
		 *   no loop to free — and the FAULT that `banchi/02-pam-*` injects to
		 *   certify itself, because it is exactly how the server was before. */
		bool ok = s->g.verifica && s->g.verifica(s->g.ctx, utente, parola);
		reg(s, "PAM answered: %s  ⚠ (SYNCHRONOUSLY: no asynchronous "
		       "hook connected — the thread stood still)",
		    ok ? "admitted" : "refused");
		s->cred_buone = ok;
		s->cred_motivo = RCP_CREDENZIALI_ERRATE;
		/* ⛔ The count is on the ADDRESS alone: the user name does not count
		 * (`DECISIONI.md` §1.9).  Three different names count three. */
		if (ok)
			azzera_falliti(s, s->indirizzo, ora);
		else
			segna_fallito(s, s->indirizzo, ora);
	}
	/* ⛔ The password is zeroed as soon as PAM has answered, and does not appear
	 * in any log at any level (§4.4).
	 * ⚠ This zeroes the local COPY.  The original arrived inside `s->acc`
	 *   and stays there until the message is consumed: the tail of the
	 *   buffer is zeroed in `drena()`, and whatever is left over in
	 *   `rcp_libera()`.  Both were uncovered (finding R9.8).
	 * `[?]` ⚠ And an optimising compiler is ALLOWED to remove this
	 *   `memset`, because `parola` is no longer read: the known cure is
	 *   `explicit_bzero()`, but first one looks at the assembly of the binary
	 *   that runs (suspicion R9.20 — it is a measurement, not a rewrite on
	 *   faith). */
	memset(parola, 0, sizeof parola);

	s->cred_arrivo = ora;
	s->stato = S_ATTESA_VERDETTO;
	s->da_quando = ora;
	return true;
}

/* ⛔⛔⭐ THE ALPHABET OF THE NAME — 21 Aug 2026, bench `06-b34` case 8, and
 *      ⚠ IT IS THE D1 SHAPE THAT SURVIVED ITS OWN CURE.
 *
 *      On 16 August the fixed list of 20 layouts was removed and the
 *      question «does this machine have it?» went to XKB (the hook
 *      `disposizione_esiste`, `webtransport.c:1626` → `tastiera.c`).  ⛔ But
 *      IN FRONT OF that hook a SECOND hand-written list had remained, and
 *      nobody had looked at it: **which characters are allowed in the name**.
 *
 * `[M]` Measured by asking the system through the product itself
 *   (`06-b34-tabella.c elenco`, that is `src/tastiera.c`), on all the **590**
 *   layout/variant pairs that `/usr/share/X11/xkb/rules/evdev.lst`
 *   declares on the test machine: **589 compile**, that is the machine
 *   has them.  ⛔ And **9 of those 589 have an uppercase letter in the name**:
 *
 *     de(T3)   ie(CloGaelach)   ie(UnicodeExpert)   in(tamilnet_TAB)
 *     in(tamilnet_TSCII)   jp(OADG109A)   lk(tam_TAB)
 *     ru(phonetic_YAZHERTY)   ua(macOS)
 *
 *   `[M]` On the wire, before this cure: `de(T3)`, `jp(OADG109A)` and
 *   `ua(macOS)` received **`0x0b ERRORE_PROTOCOLLO`** — which is WORSE than
 *   `SESSIONE_NON_SERVIBILE`, because it says «your client is broken» and sends
 *   people looking for the fault on the other side of the wire.
 *
 * ⛔ And the other direction, also measured: `it()` — EMPTY variant — was well
 *    formed for this function and malformed for `tastiera.c:forma_valida`,
 *    ⇒ `0x0e` went out on a **malformed** string.  §4.5 wants the two faults
 *    DISTINCT, and there they were merged.
 *
 * ⇒ ⭐ THE CURE IS THAT THE FORM BE ONE ONLY: here the same alphabet as
 *   `tastiera.c:carattere_ammesso()` is used — `[A-Za-z0-9_-]` — and the same
 *   rule on the empty variant.  ⛔ Two form checks written twice give
 *   two answers under the same label, which is the **E2** error shape.
 *
 * ⚠ And the defence this function carries is NOT loosened: the dot, the slash
 *   and the comma stay out of the alphabet, so `../../etc/passwd` and `it,`
 *   are refused as before — and it is the only thing this function
 *   protects, because the string ends up inside the XKB `include`
 *   machinery, which opens files by name (`tastiera.c:172`).
 *
 * ⚠ The declared price: `IT` passes the form and goes to the hook, which
 *   answers «I do not have it» ⇒ `0x0e` instead of `0x0b`.  XKB distinguishes
 *   case and `symbols/IT` does not exist: «well formed, unknown» IS the right
 *   answer.
 */
static bool disposizione_carattere_ammesso(char c)
{
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
	       (c >= '0' && c <= '9') || c == '_' || c == '-';
}

static bool disposizione_ben_formata(const char *d, size_t n)
{
	/* §4.5: an XKB name, possibly with the variant in parentheses. */
	if (n < 1 || n > 64)
		return false;
	size_t i = 0;
	while (i < n && disposizione_carattere_ammesso(d[i]))
		i++;
	if (i == 0)
		return false;
	if (i == n)
		return true;
	/* ⛔ `n < i + 3` = the variant is EMPTY (`it()`): malformed, not unknown. */
	if (d[i] != '(' || d[n - 1] != ')' || n < i + 3)
		return false;
	for (size_t k = i + 1; k + 1 < n; k++)
		if (!disposizione_carattere_ammesso(d[k]))
			return false;
	return true;
}

/* ⛔ §4.5 distinguishes TWO faults, and wants two different reasons:
 *
 *   malformed              ERRORE_PROTOCOLLO     — it wrote wrongly
 *   well formed, unknown   SESSIONE_NON_SERVIBILE — it wrote correctly something
 *                                                   this machine does not have
 *
 * ⚠ A server that merged them would give `ERRORE_PROTOCOLLO` to whoever has a
 *   Swedish keyboard on a machine without the Swedish XKB package, and the
 *   symptom would be «the client is broken» instead of «the machine lacks a
 *   layout».
 *
 * `[?]` ⚠ **And the list below is from phase 1, and it must be declared.**
 *   «What the system knows» is known by the system, not by RCP: a real server
 *   asks XKB.  In phase 1 there is no compositor (`SESSIONE` declares
 *   `desktop=unknown`), so there is nobody to ask, and the choice is a
 *   fixed list.  ⛔ What the bench tests is **that the two faults are
 *   distinct**, not which layouts exist: the day the question goes to XKB,
 *   this function changes and B5 stays as it is. */
static bool disposizione_nell_elenco(const char *d)
{
	static const char *NOTE[] = {"it", "us", "gb", "de", "fr", "es", "pt",
	                             "ru", "se", "no", "dk", "fi", "pl", "cz",
	                             "ch", "at", "be", "nl", "br", "jp", NULL};
	/* The variant in parentheses does not change the layout: `de(neo)` is `de`
	 * with another map, and whoever has `de` has both. */
	size_t n = 0;
	while (d[n] && d[n] != '(')
		n++;
	for (int i = 0; NOTE[i]; i++)
		if (strlen(NOTE[i]) == n && strncmp(NOTE[i], d, n) == 0)
			return true;
	return false;
}

/* ⛔⛔⭐ AND NOW THE QUESTION GOES TO XKB — 16 Aug 2026, bench `06-b34` case 5.
 *
 *      The list above was from phase 1, and its own note said that «a real
 *      server asks XKB».  ⛔ `[M]` as long as it decided:
 *      **`hu`, `tr`, `gr` and `ua` exist in `/usr/share/X11/xkb/symbols/` on
 *      this machine and were refused** with `SESSIONE_NON_SERVIBILE`.
 *      ⇒ A Hungarian user was denied the session by a hand-written list, and
 *        the log told them «layout unknown to this machine» — a
 *        FALSE sentence, which is the worst way of being wrong.
 *
 *      ⚠ And as long as the declared layout touched nothing the defect was
 *        invisible: it just refused.  With §5-bis.7 carried out, it becomes the
 *        difference between «the Hungarian works» and «the Hungarian does not
 *        get in».
 *
 * ⛔ THE THREE OUTCOMES STAY THREE, and the third is the one that costs: if the
 *    hook is not there (the twin of `banchi/rcp/`, the bare-QUIC harnesses)
 *    **it could not be asked**, and «I did not look» is not «it does not exist»
 *    (`LEZIONI.md` §1.9 rule 1).  ⇒ There one falls back on the phase 1 list
 *    **declaring it**, instead of accepting everything or refusing everything
 *    in silence.
 *
 *   `1` known · `0` no · `-1` could not be asked (already declared) */
static int disposizione_conosciuta(rcp_sessione *s, const char *d)
{
	if (s->g.disposizione_esiste) {
		int r = s->g.disposizione_esiste(s->g.ctx, d);
		if (r >= 0)
			return r;
		reg(s, "⚠ DECLARED FALLBACK (§4.5): the «disposizione_esiste» hook "
		       "could not answer for «%s» — falling back on the phase 1 "
		       "list, which is NOT what this machine really has",
		    d);
	} else {
		reg(s, "⚠ DECLARED FALLBACK (§4.5): no «disposizione_esiste» hook "
		       "on this server — the question «does %s exist?» did NOT go to XKB, "
		       "and the answer comes from the fixed phase 1 list",
		    d);
	}
	return disposizione_nell_elenco(d) ? 1 : 0;
}

/* ⛔⭐ THE STAGE IS ASKED TO SET THE LAYOUT, AND THE OUTCOME IS DECLARED.
 *
 * `perche` says where the request comes from — «the attach» or «DISPOSIZIONE
 * (0x0009)» — and ends up in the log: six hours later, whoever reads must be
 * able to tell a layout set on reattach from one changed by hand by the user,
 * because the two faults that follow them are different.
 *
 * ⛔ The fallback is DECLARED (`CODER.md` §4.2): without the hook the layout
 *    is NOT applied, and keeping quiet would mean leaving the user with
 *    `Ctrl+Z` on the wrong key and no line explaining it.
 *
 * ⚠ `true` = the request has LEFT, not «is in force»: who knows that is the
 *   child, and it is the child that writes the line with the name of the keymap
 *   `libei` really hands it.  Same rule as the release on detach — a number (or
 *   an outcome) invented here would be worse than none. */
static void applica_disposizione(rcp_sessione *s, const char *perche)
{
	if (!s->disposizione[0])
		return;
	if (!s->g.disposizione) {
		reg(s, "⚠ DECLARED FALLBACK (§5-bis.7): %s declared the "
		       "layout «%s», but this server does NOT have the hook to "
		       "apply it — the session keeps the one it has.  ⛔ The LETTERS "
		       "will come out right all the same (they are translated on the "
		       "session's keymap), but the SHORTCUTS will not: `Ctrl+Z` will land "
		       "on the key that position has in the OTHER layout (§7.3)",
		    perche, s->disposizione);
		return;
	}
	if (s->g.disposizione(s->g.ctx, s->disposizione))
		reg(s, "⭐ §5-bis.7: %s declared «%s» — request SENT to the "
		       "stage.  ⚠ This line does NOT say it is in force: who knows that is "
		       "the child, and it writes it with the name `libei` hands it",
		    perche, s->disposizione);
	else
		reg(s, "⛔ §5-bis.7: %s declared «%s» and the request did NOT "
		       "leave: the session keeps the layout it has, and the "
		       "shortcuts will stay out of step",
		    perche, s->disposizione);
}

/* ⛔⭐⭐ THE GHOST EVICTION — the rule is in the box above
 *      `SFRATTO_PREDEFINITO`, here is the how.
 *
 * Returns `true` if the slot has been freed (and then whoever arrives can
 * ask for it again), `false` if the occupant stays where it is.  ⚠ `*muto`
 * ALWAYS comes out set with the occupant's milliseconds of silence — it serves
 * the log line and the sentence, even when eviction is off.
 *
 * ⛔⛔ THE CHECK THAT CANNOT BE REMOVED IS THE USER ONE.  The rule
 *      applies **only between clients of the same user**: evicting the client
 *      of another user would not be a convenience, it would be a security hole —
 *      anyone could bring down someone else's desktop simply by
 *      knocking.  ⚠ Today the registry of slots is indexed BY NAME, so
 *      `POSTO_OCCUPATO` already implies «same user»; the check below is
 *      redundant **by construction, not by design**, and the day the
 *      registry became the session table of a real server
 *      (the session cap, §4.6) it would be the only thing holding.  It is
 *      not removed.
 *
 * ⛔ And the occupant is NOT sent away: it is put exactly in the state in
 *    which the silence of §5.3 puts it in `rcp_tempo()` — slot left,
 *    `S_STACCATA`, and whatever was pressed released (§7.3).  ⭐ From there
 *    `torna_a_parlare()` already knows what to do with it should the wire come
 *    back to life: the slot is no longer its own, and it gets `0x0F` with the
 *    sentence «the slot of this session was taken by another client
 *    while this one was silent» — which in that case is TRUE.  ⚠ Verified by reading
 *    it, not taken for granted: that function restarts **only** from
 *    `S_STACCATA`, and that is why the state is changed here and one does not
 *    just remove the slot (finding R9.2). */
static bool sfratta_il_fantasma(rcp_sessione *arrivo, uint64_t ora,
                                uint64_t *muto)
{
	rcp_sessione *o = posto_chi(arrivo->utente);

	*muto = 0;
	/* ⚠ A slot taken without an owner should not exist; if it did,
	 *   it is not the case to evict in the dark — one denies, and the log will
	 *   say the occupant's silence was zero. */
	if (!o || o == arrivo)
		return false;
	*muto = ora > o->ultima_vita ? ora - o->ultima_vita : 0;
	if (!sfratto_ms)
		return false;
	/* ⛔ The user check — see the box above. */
	if (strcmp(o->utente, arrivo->utente) != 0) {
		reg(arrivo, "⛔ EVICTION DENIED: the slot belongs to «%s» and the one "
		            "asking is «%s» — between different users there is NEVER an "
		            "eviction, and this registry should not even be able to "
		            "propose it",
		    o->utente, arrivo->utente);
		return false;
	}
	/* ⚠ Only an ACTIVE occupant holding the slot is evicted: anyone
	 *   else is not the case this rule describes. */
	if (o->stato != S_ATTIVA || !o->attaccata)
		return false;
	if (*muto <= sfratto_ms)
		return false;

	reg(o, "⭐ EVICTION for silence: %llu ms without a PACKET from %s (threshold "
	       "%llu ms) — the slot of %s goes to the client arriving from %s "
	       "(§4.4: whoever is silent is detached; §8.2 is NOT violated, this "
	       "occupant was attached but not alive) (slots taken now: %d)",
	    (unsigned long long)*muto, o->provenienza,
	    (unsigned long long)sfratto_ms, o->utente, arrivo->provenienza,
	    posti_occupati() - 1);
	posto_lascia(o->utente);
	o->attaccata = false;
	o->stato = S_STACCATA;
	/* ⛔ §7.3: on detach everything is released.  A Ctrl left down in the
	 * ghost would make the desktop unusable for whoever gets in now — and it
	 * is precisely whoever gets in now who must find it clean. */
	rilascia_al_distacco(o, "eviction for silence");
	return true;
}

/* ⚠ `ora` serves the ghost eviction, which compares the occupant's
 *   `ultima_vita` with now.  It comes from `drena()`, as for
 *   `tratta_credenziali()`: it is the instant of the packet carrying the `ATTACCA`. */
static bool tratta_attacca(rcp_sessione *s, lettore *l, uint64_t ora)
{
	uint32_t tl = le_u32(l), ta = le_u32(l);
	/* ⛔ §7.1: the view does NOT have the constraints of the canvas — «any size
	 * from 1x1 up is legal, odd included» (finding R1.17).  Here NOTHING is
	 * checked, and it is deliberate.
	 *
	 * ⚠ Whoever writes `ATTACCA` in C writes ONE `valida_misura()` and calls it
	 *   four times: it is the natural thing to do, and it produces a server that
	 *   **closes the session because the user narrowed the window**.  On a
	 *   phone at factor 2.75 the view is odd almost always — 393 logical
	 *   pixels are 1080.75 physical (finding R4.10).  B5 tests it with
	 *   `300x801` and `1x1`, which MUST pass. */
	uint32_t vl = le_u32(l), va = le_u32(l);
	char disp[65];
	/* ⛔ …NOTHING except one thing, and it is the only one §7.1 demands: **from
	 *    1x1 up**.  A zero is not a small view, it is the absence of a view, and
	 *    §6.0 forbids implicit sentinel values — a client that sends 0 has a
	 *    defect, and letting it pass would hide it together with the log line
	 *    that would say so.  The real check is further below, after
	 *    truncation has been ruled out. */
	size_t ld = le_str(l, disp, sizeof disp);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "ATTACCA truncated");
		return false;
	}
	/* ⛔⭐ ABOVE THE MAXIMUM IT IS REDUCED, THE CLIENT IS NOT SENT AWAY — 1 Oct
	 *     2026, canvas at most 4096x2304 (the user's decision, box in `rcp.h`).
	 *     Until that day a canvas beyond 7680x4320 was `ERRORE_PROTOCOLLO`.
	 *
	 * ⚠ A browser on a 5K or ultrawide monitor asks for its window, and it
	 *   did nothing wrong: §4.5 already allows a granted canvas different from
	 *   the one requested.  ⇒ The side that overflows goes to the maximum and
	 *   the other stays — the rule of `rcp_misura_ammessa()` and of
	 *   `tela_da_chiedere()` in the page, so `ATTACCA` and `ADATTA_TELA` grant
	 *   the same number.
	 * ⛔ It is done BEFORE the parity check: the maximum is even, and a
	 *    5121 that becomes 4096 is no longer an odd number to refuse. */
	if (tl > RCP_TELA_L_MASSIMA || ta > RCP_TELA_A_MASSIMA) {
		uint32_t chiesta_l = tl, chiesta_a = ta;
		if (tl > RCP_TELA_L_MASSIMA)
			tl = RCP_TELA_L_MASSIMA;
		if (ta > RCP_TELA_A_MASSIMA)
			ta = RCP_TELA_A_MASSIMA;
		reg(s, "⚠ DECLARED FALLBACK (§4.5): ATTACCA asks for the canvas %ux%u, "
		       "beyond the maximum %ux%u — I reduce it to %ux%u (the side that "
		       "overflows to the maximum, the other as it is)",
		    chiesta_l, chiesta_a, RCP_TELA_L_MASSIMA, RCP_TELA_A_MASSIMA, tl,
		    ta);
	}
	/* ⛔ The minimum and parity stay normative: an odd size is rounded by the
	 * encoder, in silence — two different sizes under the same label, which is
	 * the E2 shape. */
	if (tl < RCP_TELA_L_MINIMA || ta < RCP_TELA_A_MINIMA || (tl % 2) || (ta % 2)) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "canvas below the minimum or odd");
		return false;
	}
	/* ⛔ And the ONLY limit of the view, §7.1: «any size **from 1x1 up**».
	 *    ⚠ Above it says nothing is checked here, and this line does not
	 *    contradict it: «from 1x1 up» is the range the arbiter DECLARES, and a
	 *    zero lies outside it just as 100000 lies outside the canvas.  Whoever
	 *    let it pass would have a `u32` field with a value that means nothing,
	 *    and the defect would show further on — when someone divided by it. */
	if (!vl || !va) {
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "view with a zero side: §7.1 admits any size from "
		        "1x1 up, and zero is not a size");
		return false;
	}
	if (!disposizione_ben_formata(disp, ld)) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "malformed layout");
		return false;
	}
	if (!disposizione_conosciuta(s, disp)) {
		/* ⛔ §8.2: SESSIONE_NON_SERVIBILE «MUST carry the detail in the
		 * body», and `congeda()` puts it there.  The detail is NOT shown to the
		 * user (§8.2): the client builds the sentence from the code. */
		char d[128];
		snprintf(d, sizeof d, "layout unknown to this machine: %s",
		         disp);
		congeda(s, RCP_SESSIONE_NON_SERVIBILE, d);
		return false;
	}
	/* ⛔ And it is kept: it is needed further below, when the session is open
	 *    and it can finally be APPLIED (§5-bis.7).  ⚠ Not before `SESSIONE`: if
	 *    the attach is refused (slot taken, local session) we would have
	 *    changed the layout for a user who did not get in. */
	snprintf(s->disposizione, sizeof s->disposizione, "%s", disp);

	/* ⛔⭐ §5.1 of `SPECIFICHE.md`, reason `0x05 GIA_ATTIVA_LOCALE` — and it comes
	 *     BEFORE the slot, on purpose.
	 *
	 * ⛔ Asking for the slot and then releasing it would have the same outcome
	 *    for this client and a DIFFERENT one for the registry: for an instant the
	 *    slot would appear taken by whoever is about to be refused, and another
	 *    client of the same user arriving at that instant would read
	 *    `0x0F` — «you already have an attached session» — which is false.
	 *
	 * ⚠ And the hook is optional: if it is not there, the rule is NOT applied,
	 *   and the log line says so.  «No local session» and «nobody
	 *   looked» are two different facts (`LEZIONI.md` §1.9 rule 1). */
	if (s->g.sessione_locale) {
		char quale[160];

		quale[0] = '\0';
		if (s->g.sessione_locale(s->g.ctx, s->utente, quale, sizeof quale)) {
			reg(s, "⛔ attach DENIED to %s from %s: they already have a LOCAL "
			       "graphical session (%s) — §5.1, reason 0x05",
			    s->utente, s->provenienza,
			    quale[0] ? quale : "without detail");
			/* ⛔ The detail in the body does NOT name the other session:
			 * §8.2 says what the client may know. */
			congeda(s, RCP_GIA_ATTIVA_LOCALE,
			        "this user already has a local graphical "
			        "session");
			return false;
		}
	} else {
		reg(s, "⚠ no «sessione_locale» hook: the rule of §5.1 (reason "
		       "0x05) is NOT applied on this server");
	}

	/* ⛔ §8.2 reason 0x0F: the one refused is whoever ARRIVES, not whoever was there. */
	/* ⛔ The slot is ASKED for, and the outcome is written with how many were taken.
	 * ⚠ On 10 Aug 2026 the third round of B3 could not tell «the
	 *   server does not look at the registry» from «the slot had already been
	 *   freed»: they are two opposite defects, and without this line they give
	 *   the same red. */
	/* ⛔ And the two ways of not having a slot do NOT have the same reason — see
	 * the box above `posto_prendi()`, finding R9.3. */
	switch (posto_prendi(s)) {
	case POSTO_PRESO:
		break;
	case POSTO_OCCUPATO: {
		/* ⭐ BEFORE DENYING ONE LOOKS WHETHER THE OCCUPANT IS ALIVE — 23 Aug
		 *    2026, the ghost eviction (the box above `SFRATTO_PREDEFINITO`).
		 * ⚠ `muto` is ALWAYS computed, even with eviction off: it is the number
		 *   that whoever reads the log was missing to know whether that slot
		 *   belonged to an alive client or to a corpse. */
		uint64_t muto = 0;
		char dett[192];

		if (sfratta_il_fantasma(s, ora, &muto) && posto_prendi(s) == POSTO_PRESO)
			break;
		reg(s, "slot DENIED to %s from %s: another client of this same user "
		       "holds it (taken: %d) — that occupant gave a sign of life "
		       "%llu ms ago, and the eviction %s",
		    s->utente, s->provenienza, posti_occupati(),
		    (unsigned long long)muto,
		    sfratto_ms ? "did NOT fire (threshold in force)"
		               : "is switched OFF by hand (--sfratto-ms 0; since 24 Aug "
		                 "2026 the default is 15000)");
		/* ⛔⛔ AND THE SENTENCE NO LONGER DIAGNOSES — 23 Aug 2026.
		 *
		 * It said «there is already a client attached to this session», and the
		 * client built from it **«you already have an active session
		 * elsewhere»**.  ⛔ For whoever reads it after their wire dropped that
		 * sentence is FALSE: that session is theirs, and it died a moment
		 * before.  ⚠ And the server has no way of knowing which of the two it
		 * is: it does not tell a second device from the user themselves who
		 * dropped an instant ago.
		 *
		 * ⇒ One says **only what the server really knows**: that the slot
		 *    appears taken, and how long that occupant has been silent.  The
		 *    number carries with it the answer to the real question of whoever
		 *    reads — «was it me?» — without asserting it: 300 ms means there
		 *    really is someone else, 4000 ms that it almost certainly was them.
		 *
		 * ⚠ The sentence the user SEES is not this one: the page does not read
		 *   the detail, it has its own table (`src/pagina.html`, `MOTIVO[0x0F]`).
		 *   That line changes only if the director chooses the sentence — it is
		 *   the only thing in this cure that is not decided alone. */
		snprintf(dett, sizeof dett,
		         "the slot of this session is held by a client that "
		         "gave a sign of life %llu ms ago",
		         (unsigned long long)muto);
		congeda(s, RCP_GIA_ATTIVA_REMOTA, dett);
		return false;
	}
	case POSTO_NIENTE_PIU_POSTI:
		/* ⛔ §8.2 `0x0E`: «well formed but cannot be served», and it MUST carry
		 * the detail in the body — which `congeda()` puts there.  ⚠ Saying `0x0F`
		 * to this user would be telling them «you already have a session
		 * elsewhere», which is false: they have none, it is the server that has
		 * no more slots. */
		reg(s, "⛔ slot DENIED to %s from %s: the session registry of "
		       "this server is FULL (%d of %d) — it is NOT 0x0F, this user "
		       "has no session elsewhere",
		    s->utente, s->provenienza, posti_occupati(), tetto_in_vigore);
		congeda(s, RCP_SESSIONE_NON_SERVIBILE,
		        "the session registry of this server is full");
		return false;
	}
	s->attaccata = true;
	reg(s, "slot TAKEN by %s via %s (taken now: %d)", s->utente,
	    s->provenienza, posti_occupati());

	/* ⛔⭐ THE GRANTED CANVAS RESPECTS `video.misura_massima` — §4.5, finding B-1
	 *
	 *     «The granted canvas MUST respect `video.misura_massima` if the client
	 *     declared it, and respect in any case the limits and the parity
	 *     above.»  They are two constraints, and both must be satisfied: dividing
	 *     is not enough.
	 *
	 * ⚠ It is reduced keeping the PROPORTIONS, and each side is not cut to its
	 *   ceiling: cutting the sides independently would change the ratio of the
	 *   canvas and the remote desktop would arrive squashed — a defect one
	 *   SEES and that no error code names.  §4.5 allows it
	 *   explicitly: «the granted canvas may differ from the one
	 *   requested […] the client MUST adapt by rescaling».
	 *
	 * ⛔ And the fallback IS WRITTEN TO THE LOG — the same line of §4.5 requires
	 *    it for the KDE fallback, and it applies identically here: a canvas
	 *    different from the one requested, without a line saying why, is
	 *    indistinguishable from a calculation error.
	 *
	 * ⚠ And if not even the MINIMUM legal canvas (320x240) fits under the
	 *   ceiling, an illegal canvas is not granted and one does not keep quiet:
	 *   §4.5 «if the attach cannot be served, the server sends the client away
	 *   with one of the reasons of §8.2 — never with a silence». */
	if (s->max_l && (tl > s->max_l || ta > s->max_a)) {
		uint32_t cl = tl, ca = ta;
		uint32_t chiesta_l = tl, chiesta_a = ta;
		/* The side that limits most: cross comparison, without floating-point
		 * divisions. */
		if ((uint64_t)tl * s->max_a <= (uint64_t)ta * s->max_l) {
			ca = s->max_a;
			cl = (uint32_t)(((uint64_t)tl * s->max_a) / ta);
		} else {
			cl = s->max_l;
			ca = (uint32_t)(((uint64_t)ta * s->max_l) / tl);
		}
		cl -= cl % 2; /* §4.5: both EVEN */
		ca -= ca % 2;
		if (cl < 320)
			cl = 320;
		if (ca < 240)
			ca = 240;
		if (cl > s->max_l || ca > s->max_a) {
			char d[160];
			snprintf(d, sizeof d,
			         "video.misura_massima=%ux%u is below the minimum legal "
			         "canvas of 320x240 (§4.5)",
			         s->max_l, s->max_a);
			reg(s, "⛔ canvas NOT granted to %s: requested %ux%u, ceiling %ux%u — "
			       "not even 320x240 fits under it",
			    s->utente, chiesta_l, chiesta_a, s->max_l, s->max_a);
			congeda(s, RCP_SESSIONE_NON_SERVIBILE, d);
			return false;
		}
		tl = cl;
		ta = ca;
		reg(s, "⚠ DECLARED FALLBACK (§4.5): canvas requested %ux%u, decoder "
		       "ceiling %ux%u (video.misura_massima) — GRANTED %ux%u, "
		       "proportions kept, both even",
		    chiesta_l, chiesta_a, s->max_l, s->max_a, tl, ta);
	}

	/* ⛔⭐⭐ AND BEFORE GRANTING, THE STAGE IS ASKED WHAT SIZE IT HAS — the cure
	 *     for the RE-ATTACH, `DECISIONI.md` §5.0-sexies («⏳ for when the
	 *     re-attach is tackled: the solution is already measured»).
	 *
	 * ⛔ The case: the stage outlives the client (invariant I4), the canvas is born at
	 *    every attach (§5.0).  Whoever detaches from the DeX with the canvas at
	 *    1912x1044 and reattaches from the laptop asks for 1920x1080 — and the
	 *    stage keeps delivering 1912x1044.  §6.2 forbids sending a frame whose
	 *    size is not the canvas in force ⇒ **zero pixels**, and the only line
	 *    that would say so would be «canvas in force X but the frame is Y», said
	 *    once.
	 *
	 * ⇒ What the stage HAS is granted, and §4.5 allows it in writing: «the
	 *   granted canvas may differ from the one requested».  ⭐ Then the page
	 *   sends its `ADATTA_TELA` and one gets where one wanted — but passing
	 *   through a state in which pixels arrive instead of one in which they do
	 *   not.
	 *
	 * ⚠ And the limits are ALL checked again, because the stage's size did not
	 *   go through this gate: §4.5 (320..4096 x 240..2304, even) and the decoder
	 *   ceiling of THIS client.  ⛔ If it does not pass them it is not granted
	 *   and one does not keep quiet: `rcp_tela_concessa()` takes care of it, and
	 *   at the first frame it will ask the stage to come back. */
	if (s->g.tela_del_palco) {
		uint32_t pl = 0, pa = 0;
		if (s->g.tela_del_palco(s->g.ctx, &pl, &pa) && pl && pa
		    && (pl != tl || pa != ta)) {
			if (pl < RCP_TELA_L_MINIMA || pl > RCP_TELA_L_MASSIMA
			    || pa < RCP_TELA_A_MINIMA || pa > RCP_TELA_A_MASSIMA
			    || (pl % 2) || (pa % 2))
				reg(s, "⚠ the stage has the canvas %ux%u, which §4.5 does not "
				       "allow in `SESSIONE` (%u..%u x %u..%u, even): I grant %ux%u "
				       "as requested, and at the first frame the stage will be "
				       "asked to come here",
				    pl, pa, RCP_TELA_L_MINIMA, RCP_TELA_L_MASSIMA,
				    RCP_TELA_A_MINIMA, RCP_TELA_A_MASSIMA, tl, ta);
			else if (s->max_l && (pl > s->max_l || pa > s->max_a))
				reg(s, "⚠ the stage has the canvas %ux%u, beyond the "
				       "video.misura_massima of this client (%ux%u): I grant "
				       "%ux%u, and at the first frame the stage will be asked "
				       "to come here",
				    pl, pa, s->max_l, s->max_a, tl, ta);
			else {
				reg(s, "⚠ DECLARED FALLBACK (§4.5): canvas %ux%u requested, but "
				       "the stage of %s already has one — %ux%u — and it outlives "
				       "the client (I4).  GRANTED the stage's: so the "
				       "frames arrive at once, and the page can ask for "
				       "its size with `ADATTA_TELA`",
				    tl, ta, s->utente, pl, pa);
				tl = pl;
				ta = pa;
			}
		}
	}

	uint8_t corpo[128];
	scrittore w = {corpo, sizeof corpo, 0, false};
	/* ⭐ D-001 (phase 15): the REAL state and desktop, if the host knows them —
	 *    the why is on the two hooks in `rcp.h`.  ⚠ Without hooks it stays what
	 *    it was: `NUOVA` and `unknown`. */
	bool ripresa = s->g.sessione_ripresa && s->g.sessione_ripresa(s->g.ctx);
	const char *desktop = s->g.desktop ? s->g.desktop(s->g.ctx) : NULL;

	if (!desktop || !desktop[0])
		desktop = "unknown";
	sc_byte(&w, ripresa ? 2 : 1); /* §4.5: 1 = NUOVA, 2 = RIPRESA */
	sc_u32(&w, tl);
	sc_u32(&w, ta);
	sc_str(&w, desktop);
	reg(s, "SESSIONE to %s: %s, canvas %ux%u, desktop %s", s->utente,
	    ripresa ? "RESUMED (the stage was already there)" : "NEW", tl, ta, desktop);
	if (!w.pieno) {
		manda_messaggio(s, T_SESSIONE, corpo, w.len);
		/* ⛔⭐ THE VIDEO CHANNEL OPENS **HERE**, AND NOT ONE LINE HIGHER.
		 *
		 * §2.5: «one per frame, ⛔ and **none before having sent
		 * `SESSIONE`**: whoever receives one before closes with
		 * `ERRORE_PROTOCOLLO`».  It is invariant **I3** on the wire — *whoever
		 * does not pass the validator does not receive a pixel*.
		 *
		 * ⛔ The three lines sit INSIDE the `if`: if the body had not fit
		 *    in the buffer, `SESSIONE` would not have left, and a video channel
		 *    opened all the same would send frames to a client that knows
		 *    neither the canvas nor the codec.  ⚠ Outside the `if` they would
		 *    look the same and they are not. */
		s->tela_l = tl;
		s->tela_a = ta;
		/* ⛔ And the view of the `ATTACCA` IS KEPT, instead of being read and
		 *    thrown away: §4.5 defines it as «the size at which the client
		 *    will draw», and `VISTA` (§7.1) is the message that CHANGES it — if
		 *    there were no starting value, the first `VISTA` would change
		 *    a field that has never been anything. */
		s->vista_l = vl;
		s->vista_a = va;
		s->sessione_spedita = true;
		/* ⛔ §5.2, first point: «the first frame the server sends
		 * after `SESSIONE` MUST be a keyframe». */
		chiave_serve(s, "it is the first after SESSIONE (§5.2)");
		s->mai_spedita_una_chiave = true;
	}
	reg(s, "session open utente=%s via=%s tela=%ux%u vista=%ux%u "
	       "disposizione=%s",
	    s->utente, s->provenienza, tl, ta, vl, va, disp);
	s->stato = S_ATTIVA;
	annuncia_il_tenuto(s);

	/* ⛔⭐⭐ AND NOW THE LAYOUT IS APPLIED — `DECISIONI.md` §5-bis.7,
	 *      decided on 8 Aug 2026 and CONFIRMED by the user on the 16th.
	 *
	 * ⛔ Until tonight this line was not there, and the message above —
	 *    «disposizione=%s» — was **all the server did** with the
	 *    string: it validated it and wrote it.  `[M]` bench `06-b34` case 2:
	 *    reattaching to an `it` session declaring `us`, `è` and `ò` arrived,
	 *    which on `us` exist on no key.
	 *
	 * ⭐ And it is done HERE, after `SESSIONE`, not up there at validation: if
	 *    the attach had been refused (slot taken, local session, canvas out of
	 *    limits) we would have changed the layout for a user who did not get
	 *    in — and the session outlives the client (I4), so the harm would stay
	 *    there even afterwards.
	 *
	 * ⚠ And it applies to the attach AND to the reattach, because `ATTACCA` is
	 *   the same message for both: it is precisely what §5-bis.7 asks —
	 *   *«at session creation or re-attach the keyboard is renegotiated
	 *   too»*. */
	applica_disposizione(s, "the attach");

	/*
	 * ⭐⭐⭐ AND THE STAGE KNOWS AT ONCE — 16 Aug 2026, and without this line
	 *      the stage was born at a size nobody had asked for.
	 *
	 * ⛔ THE DEFECT, and it has three faces that looked like three defects: the
	 *    child is born with a default canvas (1920x1080) and changes it only
	 *    when an `ADATTA_TELA` arrives.  As long as the page asked for 1920x1080
	 *    at `ATTACCA` and corrected itself right after, that message always
	 *    arrived — ⛔ but it was a dance: every session was born wrong and
	 *    resized, and resizing is a race (the backstop of §7.1, the stage being
	 *    mounted, `libei` recreating the devices).  `[M]` it was lost one time
	 *    in three.
	 *
	 * ⇒ Once the page was cured — it now asks for the window from `ATTACCA`
	 *   on, as §5.0-sexies has said since 14 August — the dance disappeared
	 *   **and with it the message**: there is nothing left to correct, so nobody
	 *   told the child any more how big the canvas is.  ⭐ The stage was born at
	 *   1920x1080 and the frames were all thrown away.
	 *
	 * ⇒ ⭐ The SERVER says it, here, at the instant the canvas is decided.  It is
	 *   the right place for a reason that holds beyond this case: **whoever
	 *   decides a number is whoever must tell it to whoever uses it**.  Before,
	 *   the client said it on the rebound, and it worked by accident.
	 *
	 * ⚠ And it is not a disguised `ADATTA_TELA`: it answers no message and
	 *   sends nothing on the wire.  If the stage already has that size — the
	 *   re-attach — the child answers «I already have it» and nothing happens.
	 */
	if (s->g.ritela) {
		reg(s, "⭐ §4.5: I tell the stage that the canvas of this session is %ux%u — "
		       "so it is born that way instead of being born at a size of its own "
		       "and having to change it (and the change is a race)",
		    tl, ta);
		s->g.ritela(s->g.ctx, tl, ta);
	}
	return true;
}

/* ========================================================================= */
/* ⭐⛔ THE VIDEO CHANNEL — §2.5, §5.1, §5.2, §6.2                            */
/*                                                                           */
/* ⛔ THE ELEVEN RULES, AND WHERE EACH ONE LIVES IN THESE LINES               */
/*                                                                           */
/*  P1  §2.5   no video stream before having SENT `SESSIONE`                  */
/*             ⇒ `s->sessione_spedita`, switched on by the line that sends it */
/*  P2  §6.2   `numero` starts from 1, 0 is reserved, and AT WRAPAROUND it is */
/*             skipped ⇒ `numero_prossimo()`                                  */
/*  P3  §2.5   video lives ONLY on a unidirectional stream of the server      */
/*             ⇒ `g.video_apri`, and never `g.manda` (which is control)       */
/*  P4  §6.2   FIN before the 28 bytes is `ERRORE_PROTOCOLLO`                 */
/*             ⇒ the 28 bytes go out in ONE write, and if not it is RESET     */
/*  P5  §6.2   `largh.`/`altezza` are the canvas IN FORCE                     */
/*             ⇒ `s->tela_l/tela_a`, which the caller cannot pass             */
/*  P6  §5.2   the first frame after `SESSIONE` MUST be a keyframe            */
/*  P9  §5.2   and the same at every canvas change                            */
/*             ⇒ `s->serve_chiave`, switched on ONLY by `chiave_serve()`      */
/*               and off ONLY by `chiave_pagata()` — see the box of           */
/*               the two functions below, which carries the list of causes    */
/*  §6.2       the 16 MiB ceiling binds the sender FIRST                      */
/*             ⇒ the check is before opening the stream: not a byte leaves    */
/*  §6.2       FIN ⇒ complete · `RESET_STREAM` ⇒ thrown away                  */
/*             ⇒ `rcp_video_finisci()` versus `rcp_video_abbandona()`         */
/*  §6.2       `codec` MUST be the one negotiated in §4.3                     */
/*             ⇒ `rcp_codec_negoziato()`, and not even this is a parameter    */
/*  §5.1/§5.2  every abandonment in the log, and a KEYFRAME is not abandoned  */
/*                                                                           */
/* ⛔ AND THE SHAPE OF ALL THREE RULES «BY CONSTRUCTION»: `largh.`,           */
/*    `altezza`, `codec` and `numero` **are not parameters of any public      */
/*    function**.  Whoever encodes cannot get them wrong because they cannot  */
/*    touch them.  ⚠ The alternative road — passing them and checking them —  */
/*    would have been shorter and would have put the protection where it can  */
/*    get lost (invariant I7, read from inside the program).                  */

/* ⛔⭐⭐⭐ THE KEYFRAME DEBT — AND THE COMMENT THAT HAD LIED TWICE.
 *
 * This box said *«switched on in THREE places and off in one»*, and the places
 * were FOUR.  Corrected, it said *«FIVE»*, and the lines that switch it on
 * are NINE, for SEVEN causes.  ⛔ Two corrections by hand, two lies: the third
 * was already bought, because the number is not a behaviour — no bench
 * can see that a list has fallen behind, and neither can the compiler.
 *
 * ⭐ ⇒ THE CURE IS NOT COUNTING BETTER, IT IS REMOVING THE COUNT.  The field is
 *      switched on ONLY by `chiave_serve()` and off ONLY by `chiave_pagata()`.
 *      The authoritative list is therefore `grep -n 'chiave_serve(' src/rcp.c`,
 *      which cannot age: a new branch that switched on the debt without
 *      passing through here would have to assign the field by hand, and that
 *      shows in a review — while a wrong number inside a comment shows in
 *      none.
 *
 * ⚠ AND WHAT A BENCH CAN VERIFY, if one day one wants it written:
 *   not «how many there are» — which is what ages — but that **the field is
 *   not touched outside the two functions**.  They are two `grep` lines on this
 *   file, and they sit next to the `GEMELLATI` check of the `Makefile`, which
 *   already compares two copies of the same module:
 *
 *     grep -n 'serve_chiave *=' src/rcp.c   ⇒ MUST give 2 lines only, and they
 *                                             are the two inside the functions
 *                                             below
 *     grep -n 'serve_chiave_perche *=' src/rcp.c   ⇒ the same 2
 *
 *   ⛔ This check does NOT age with the addition of a cause: it is precisely
 *      the addition of a cause that leaves it green, provided it goes through
 *      the funnel.
 *
 * ⛔ THE SEVEN CAUSES, and the line of each as of 23 Aug 2026 (⚠ the lines are
 *    a courtesy for whoever reads today, NOT the authoritative list — that is
 *    the `grep` above):
 *
 *   1. §5.2  `SESSIONE` has been sent: the first frame after it
 *            MUST be a keyframe                                     line 2774
 *   2. §5.2  the canvas has changed (`TELA` adapted): the first at the new
 *            size MUST be a keyframe                                 line 3234
 *   3. §5.1  a delta was abandoned IN THE QUEUE downstream          line 3601
 *   4. §2.3  a delta was SKIPPED for lack of room — defect B-18,
 *            and it is the cause the old comment did not have       line 3663
 *   5. §5.2  a delta was abandoned by `rcp_video_abbandona()`       line 3699
 *   6. §5.2  a frame BROKE HALFWAY — and it is ONE cause on THREE
 *            lines, which is precisely the way the count went wrong:
 *            the 28-byte header did not go out whole (line 3871), a
 *            piece did not go out (line 3883), the FIN arrived with fewer
 *            bytes than declared (line 3908)
 *   7. §5.2  the client sent `RICHIEDI_CHIAVE`                      line 5689
 *
 * ⛔ AND IT IS SWITCHED OFF IN ONE PLACE ONLY: the keyframe has GONE OUT whole
 *    (line 3919).
 *    ⚠ And it is switched off there and not at the opening of the stream: a
 *      frame opened and then broken has paid nothing, and switching off the
 *      debt at opening would leave the client without a keyframe with the
 *      server convinced of the opposite.
 */
static void chiave_serve(rcp_sessione *s, const char *perche)
{
	s->serve_chiave = true;
	s->serve_chiave_perche = perche;
}

static void chiave_pagata(rcp_sessione *s)
{
	s->serve_chiave = false;
	s->serve_chiave_perche = NULL;
}

/* §6.2 — the two values of the `tipo` field. */
#define V_CHIAVE 0x0301
#define V_DELTA 0x0302
/* §6.2 — the header is exactly 28 bytes, without padding. */
#define V_INTESTAZIONE 28
/* ⛔ §6.2 — «the server MUST NOT produce a frame longer than 16 MiB».
 * ⚠ And the ceiling belongs to the FRAME, that is header included: that is how
 *   the receiver counts it, seeing a single stream and not knowing where our
 *   structure ends.  A ceiling counted on the data alone would let through 28
 *   bytes too many, and the difference shows only at the limit — where the
 *   benches put their cases on purpose. */
#define V_TETTO (16u * 1024u * 1024u)
/* ⛔ §5.2, exception 5 of §3: 200 ms from the last keyframe SENT. */
#define V_GRAZIA_CHIAVE 200

/* ⛔ §6.2 — THE COUNTER, AND THE TWO LINES THAT GOVERN IT.
 *
 *   «The first frame of a session carries `numero = 1`, and `0` is
 *    reserved»  —  «And at counter wraparound `0` is skipped: the arithmetic is
 *    modulo 2^32 […] and from `0xFFFFFFFF` one goes to `1`».
 *
 * ⚠ The second line came in two hours after the first, on 12 Aug 2026,
 *   because without it the reserved value came back into circulation on its own
 *   after two years and two months of session — only once in a lifetime, and
 *   nobody would have connected it to `RICHIEDI_CHIAVE`.  ⛔ The two lines are
 *   here one under the other on purpose: separating them is how the second
 *   gets lost. */
static uint32_t numero_prossimo(uint32_t ultimo)
{
	uint32_t n = ultimo + 1; /* modulo 2^32, by definition of the type */
	if (n == 0)
		n = 1;
	return n;
}

uint8_t rcp_profondita_negoziata(const rcp_sessione *s)
{
	/* ⛔⭐⭐ AND THIS READER WAS NOT THERE, and its absence cost the most
	 *      expensive defect found so far — 17 Aug 2026, evening, on Firefox.
	 *
	 *      §4.3 has `video.profondita` negotiated and the choice ends up in here.
	 *      ⛔ But **nobody read it**: the child wrote `r.profondita = 10`
	 *      by hand, for every codec, and the stream went out at 10 bits **while
	 *      `ECCOMI` declared 8**.
	 *
	 * ⚠ On Chrome it did not show: HEVC carries its parameters inside the stream
	 *   (VPS/SPS) and the decoder reconfigures itself.  ⛔ On Firefox +
	 *   AV1 no: the page configures `av01.0.12M.08` — the NEGOTIATED depth —
	 *   and dav1d trusts the string.  `[M]` first artefacts, then the
	 *   decoder gets stuck and the desktop freezes.
	 *
	 * ⭐ And it is the same shape as `LEZIONI.md` §7.5: **two truths about the
	 *    same fact, and no line binding them**.  The codec crossed the process
	 *    boundary, the depth did not — and no bench could see it, because the
	 *    two numbers live in two different processes.
	 *
	 * ⚠ `0` = not yet negotiated, and it is NOT «8»: whoever has not negotiated
	 *   has no depth, and picking one for them would redo by hand the defect
	 *   this function exists to remove. */
	if (!s || !s->profondita[0])
		return 0;
	if (strcmp(s->profondita, "8") == 0)
		return 8;
	if (strcmp(s->profondita, "10") == 0)
		return 10;
	return 0;
}

uint8_t rcp_livello_negoziato(const rcp_sessione *s)
{
	/* ⛔⭐⭐ AND THIS READER IS FROM 23 AUG 2026, and it is born from a
	 *      MEASUREMENT: canvas 3840x2160, H.264, the client declares
	 *      `video.livello=5.1` and the server produces a stream of level
	 *      **5.2**.  §4.3 row 701 is a MUST — *«the server MUST emit a stream
	 *      of a level not higher, and does not guess it»* — and the server
	 *      overshot.
	 *
	 * ⛔ Until tonight the REQUESTED number stopped in here: it was written
	 *    to the log and nobody read it.  The PRODUCED number lives in the
	 *    child (`codificatore.c`, from the SPS), which is another process — two
	 *    truths about the same fact, `LEZIONI.md` §7.5, exactly the shape of
	 *    the depth of 17 August.  ⇒ Now it crosses the boundary by the same
	 *    road as that one: `rcp.h` → `webtransport.c` → `main.c` →
	 *    `figli_video()` → `struct corpo_video`.
	 *
	 * ⚠ In TENTHS, which is the alphabet of §4.3 (`5.1` ⇒ `51`) and the one the
	 *   child converts back from for each codec — H.264 uses it as is
	 *   (`level_idc`), HEVC triples it (`general_level_idc`).  ⛔ A `uint8_t`
	 *   is more than enough: `6.2` is 62, and §4.3 defines nothing above.
	 *
	 * ⚠ `0` = the client did not declare it (§4.3 does not require it) or wrote
	 *   it malformed, and it does NOT mean «low»: it means «no ceiling», and
	 *   the receiver must not invent one. */
	if (!s || !s->livello_x10 || s->livello_x10 > 255u)
		return 0;
	return (uint8_t) s->livello_x10;
}

uint8_t rcp_codec_negoziato(const rcp_sessione *s)
{
	if (!s)
		return 0;
	/* §6.2: «`codec`: 1 = HEVC, 2 = AV1.  MUST be the one negotiated in
	 * §4.3».  ⛔ The string is chosen by `prima_comune()` on the client's `CIAO`,
	 * and the translation lives HERE and nowhere else: two tables that
	 * map the same names diverge, and it is the same shape of the defect that
	 * §0 of `RCP.md` exists to remove. */
	if (strcmp(s->codec, "hevc") == 0)
		return 1;
	/* ⚠ `av1` stays HERE and not in `nostro_codec`: the number is assigned
	 *   forever (§6.2), and this line is its declared tomb — it is no longer
	 *   negotiated, but if it appeared it would be translated right. */
	if (strcmp(s->codec, "av1") == 0)
		return 2;
	if (strcmp(s->codec, "h264") == 0)
		return 3;
	return 0; /* not yet negotiated, or a name RCP/1 does not define */
}

uint8_t rcp_audio_negoziato(const rcp_sessione *s)
{
	if (!s)
		return 0;
	/* §6.3: «`codec`: 1 = Opus, 2 = PCM (§5.3)».  ⛔ As for video, the
	 * translation from the negotiated name to the number on the wire lives HERE
	 * and nowhere else. */
	if (strcmp(s->audio, "opus") == 0)
		return 1;
	if (strcmp(s->audio, "pcm") == 0)
		return 2;
	return 0; /* not yet negotiated, or a name RCP/1 does not define */
}

bool rcp_tela_in_vigore(const rcp_sessione *s, uint32_t *lar, uint32_t *alt)
{
	if (!s || !s->sessione_spedita)
		return false;
	if (lar)
		*lar = s->tela_l;
	if (alt)
		*alt = s->tela_a;
	return true;
}

/* The declaration, and why the view is NOT the canvas, are in `rcp.h`. */
bool rcp_vista(const rcp_sessione *s, uint32_t *lar, uint32_t *alt)
{
	if (!s || !s->sessione_spedita)
		return false;
	if (lar)
		*lar = s->vista_l;
	if (alt)
		*alt = s->vista_a;
	return true;
}

bool rcp_video_serve_chiave(const rcp_sessione *s)
{
	return s && s->serve_chiave;
}

uint32_t rcp_video_ultimo_numero(const rcp_sessione *s)
{
	return s ? s->video_numero : 0;
}

/* ⛔ §7.1 — the canvas has changed, and §5.2 opens the debt ONLY if it really
 * changed.  See the box in `rcp.h`.
 *
 * ⚠ DECLARED FALLBACK (`CODER.md` §4.2): this form has no clock,
 *   so it CANNOT open the second of grace of §7.1 on the coordinates in
 *   flight — and a silent fallback produces two behaviours under the same
 *   label.  The log line says so; whoever serves `ADATTA_TELA` on the wire
 *   uses `rcp_tela_adattata_ora()`. */
void rcp_tela_adattata(rcp_sessione *s, uint32_t lar, uint32_t alt)
{
	if (!s || !s->sessione_spedita)
		return;
	if (lar != s->tela_l || alt != s->tela_a)
		reg(s, "⚠ DECLARED FALLBACK: `rcp_tela_adattata()` without the time — the "
		       "SECOND OF GRACE of §7.1 on the coordinates of the old canvas "
		       "does NOT open, and a `PUNTATORE` in flight will be refused with "
		       "`ERRORE_PROTOCOLLO`.  Whoever serves `ADATTA_TELA` on the wire should "
		       "call `rcp_tela_adattata_ora()`");
	rcp_tela_adattata_ora(s, lar, alt, 0);
	/* ⛔⭐ AND THE GRACE REALLY CLOSES, instead of opening with date ZERO —
	 *     16 Aug 2026, sub-phase 6.4, found by reading.
	 *
	 * ⚠ Without these two lines the line above **said something false**:
	 *   `rcp_tela_adattata_ora(…, 0)` sets `tela_grazia_da = 0` and fills
	 *   `tela_prec_*`, and the grace appears OPEN for all instants smaller than
	 *   `TELA_GRAZIA` — that is the first second of the clock.  ⛔ With a
	 *   monotonic system clock one never gets there and the defect does not
	 *   show; ⚠ with the artificial clock of a bench starting from zero it does,
	 *   and it is precisely the place where this module is mounted bare.
	 *
	 * ⇒ A fallback that declares one thing and does another is worse than the
	 *   fallback: it is the E2 shape, two behaviours under the same label, and
	 *   it is what the `reg()` above exists NOT to be.
	 *
	 * ⛔ And it is NOT measured by any bench, declared instead of kept quiet: to
	 *    test it one would need a clock starting below one second, and the
	 *    handshake of §4.4-bis already consumes fifteen hundred milliseconds. */
	s->tela_prec_l = 0;
	s->tela_prec_a = 0;
	s->tela_grazia_da = 0;
}

/* The declaration, the why and the two sizes that kill are in `rcp.h`:
 * here there is only the rule. */
bool rcp_misura_ammessa(uint32_t larghezza, uint32_t altezza, uint32_t *fuori_l,
                        uint32_t *fuori_a)
{
	uint32_t l, a;

	if (fuori_l)
		*fuori_l = 0;
	if (fuori_a)
		*fuori_a = 0;
	/* ⛔ The ceiling is checked BEFORE truncating: truncating 100000 to even would
	 * give 100000, that is a number still able to kill the compositor.
	 *
	 * ⛔⭐ AND THE LIMITS ARE THOSE OF §4.5, PER SIDE — corrected on the night of
	 *     15 Aug 2026, while refuting.  The first draft used 200..8192 **on
	 *     both sides**, and `RCP.md` §4.5 is normative: *«width and height
	 *     of the canvas MUST be between 320x240 and 7680x4320»* (the maximum of
	 *     the time; today 4096x2304).  ⚠ The two rules
	 *     already diverged — `ATTACCA` applied §4.5 and `ADATTA_TELA` did not —
	 *     and it was **unreachable** as long as `ADATTA_TELA` always answered
	 *     `COMPOSITORE_INCAPACE`.  ⛔ The concrete case: one narrows the bottom
	 *     edge of the window, `ADATTA_TELA(1600, 230)` was granted, and
	 *     at RE-ATTACH the same size was refused by `ATTACCA` — the
	 *     server not granting in `SESSIONE` a canvas it had granted itself
	 *     in `TELA`.
	 *
	 * ⚠ And the real ceiling of the compositor stays below: `[M]` beyond 16384 per
	 *   side `gnome-shell` dies, and 4096 is well below — see the box in `rcp.h`.
	 *
	 * ⛔⭐ SINCE 1 OCT 2026 ABOVE THE MAXIMUM IT IS REDUCED, NOT REFUSED
	 *     (box in `rcp.h`): the side that overflows goes TO THE MAXIMUM, the
	 *     other stays.  ⚠ And the ceiling is always applied BEFORE truncating:
	 *     100000 becomes 4096, not a number still able to kill the compositor. */
	if (larghezza < RCP_TELA_L_MINIMA || altezza < RCP_TELA_A_MINIMA)
		return false;
	if (larghezza > RCP_TELA_L_MASSIMA)
		larghezza = RCP_TELA_L_MASSIMA;
	if (altezza > RCP_TELA_A_MASSIMA)
		altezza = RCP_TELA_A_MASSIMA;
	/* ⚠ DOWNWARDS, always: upwards one would go out of the browser window, and
	 * the extra pixel would come back as a band or as a scale — that is as the
	 * thing this decision removes. */
	l = larghezza & ~1u;
	a = altezza & ~1u;
	/* ⛔ And truncation cannot bring it below the minimum: 321 -> 320 is
	 * still allowed, but the rule is written instead of trusting that the
	 * numbers add up. */
	if (l < RCP_TELA_L_MINIMA || a < RCP_TELA_A_MINIMA)
		return false;
	if (fuori_l)
		*fuori_l = l;
	if (fuori_a)
		*fuori_a = a;
	return true;
}

/* ⛔⭐ THE `TELA` MESSAGE ON THE WIRE — §7.1.
 *
 * ⚠ Until 14 Aug 2026 this piece did NOT exist: `rcp_tela_adattata_ora()`
 *   changed the canvas in force, opened the grace and wrote to the log, but the
 *   client received **nothing**.  ⇒ A client that had asked for a size would
 *   have been left waiting for an answer nobody sent, and the defect would
 *   have looked like «adaptation does not work» instead of «it is not
 *   written».  It is the shape of fault this project pays for most often: the
 *   piece missing **between** two pieces that are there.
 *
 * `esito`  1 = ADATTATA, 2 = RIFIUTATA
 * `motivo` 0 if adapted; 1 = COMPOSITORE_INCAPACE, 2 = MISURA_FUORI_LIMITI,
 *          3 = NON_ORA
 * ⛔ And the two size fields are **the canvas IN FORCE AFTER this message**,
 *    not the one requested: on a refusal they are the previous one, and it is
 *    the only line that tells the client what to continue with. */
static void manda_tela(rcp_sessione *s, uint8_t esito, uint8_t motivo,
                       uint32_t lar, uint32_t alt)
{
	uint8_t corpo[10];
	scrittore w = {corpo, sizeof corpo, 0, false};

	sc_byte(&w, esito);
	sc_byte(&w, motivo);
	sc_u32(&w, lar);
	sc_u32(&w, alt);
	if (w.pieno) {
		reg(s, "⛔ TELA not sent: the body does not fit (our defect)");
		return;
	}
	manda_messaggio(s, T_TELA, corpo, w.len);
	reg(s, "TELA sent: outcome %u, reason %u, canvas in force %ux%u (§7.1)",
	    esito, motivo, lar, alt);
}

/* ⛔ §7.1 / §3 exception 3 — the form that knows WHEN, and opens the grace. */
void rcp_tela_adattata_ora(rcp_sessione *s, uint32_t lar, uint32_t alt,
                           uint64_t ora_ms)
{
	if (!s || !s->sessione_spedita)
		return;
	if (lar == s->tela_l && alt == s->tela_a) {
		/* ⛔ §7.1 answers `TELA` even to an `ADATTA_TELA` asking for the
		 * size that is already there: there is no «new size» there, and opening
		 * the keyframe debt would stop the video on a healthy session —
		 * the red to the wrong suspect that this family of rules has
		 * already paid for four times (P8 → P11 → P13 → P14). */
		reg(s, "TELA(ADATTATA) at the size that was already there (%ux%u): the "
		       "canvas in force does not change and §5.2 does NOT open the keyframe debt",
		    lar, alt);
		/* ⛔ One answers ALL THE SAME: §7.1 wants one `TELA` for every
		 *    `ADATTA_TELA`, and a client that received nothing would wait forever. */
		manda_tela(s, 1 /* ADATTATA */, 0, s->tela_l, s->tela_a);
		return;
	}
	reg(s, "canvas IN FORCE changed from %ux%u to %ux%u (§7.1): from here §6.2 binds "
	       "width/height to the new one, and §5.2 wants a KEYFRAME at the new "
	       "size",
	    s->tela_l, s->tela_a, lar, alt);
	/* ⛔ §7.1, third exception of §3 — THE GRACE OPENS HERE, and the previous
	 * canvas is kept BEFORE replacing it: «inputs that left before the answer
	 * arrived are not a defect of the client».  ⚠ One second, and no more:
	 * beyond it, the MUST of §7.3 is whole again. */
	s->tela_prec_l = s->tela_l;
	s->tela_prec_a = s->tela_a;
	s->tela_grazia_da = ora_ms;
	s->tela_l = lar;
	s->tela_a = alt;
	chiave_serve(s, "it is the first at the new size after TELA (§5.2)");
	/* ⛔ And the message goes out AFTER the state has changed, not before: the two
	 *    size fields must state the canvas **in force after**, and it is the only
	 *    order in which they can state it without copying it into a separate
	 *    variable. */
	manda_tela(s, 1 /* ADATTATA */, 0, s->tela_l, s->tela_a);
}

/* ⛔⭐⭐ «THE STAGE MUST SERVE THE CANVAS IN FORCE» — and when it does not, it is
 *     ASKED AGAIN, with a growing wait.
 *
 * ⛔ It is the only honest way out of the disagreement, and the reason lies in
 *    the protocol: §6.2 forbids sending a frame whose size is not the canvas in
 *    force, and §7.1 gives the server no way to change the canvas **on its own
 *    initiative** — an unrequested `TELA` is `ERRORE_PROTOCOLLO` for the
 *    client.  ⇒ Of the two parties in disagreement, the one that must move is
 *    the stage, which is ours.
 *
 * ⚠ And the wait grows because the case in which it does not move exists (a
 *   compositor that cannot resize): without it, this line would ask the same
 *   thing at every frame — sixty renegotiations per second, which is the shape
 *   of the 30.8 GB of log of 14 August at another point of the chain.
 *
 * ⚠ Meanwhile the session shows the last good image: ugly and alive
 *   (I1).  The log says so at every attempt, so whoever watches tells «the
 *   desktop is still» from «the desktop is no longer there». */
static void tela_richiama_il_palco(rcp_sessione *s, uint64_t ora_ms)
{
	/* ⛔⛔⛔ WHOEVER DOES NOT HOLD THE SLOT DOES NOT COMMAND THE STAGE — and
	 *      without this line two sessions of the same user FIGHT OVER the
	 *      canvas, forever.
	 *
	 * `[M]` 15 Aug 2026, morning, the user's REAL session — and it is a defect
	 * I introduced myself last night, found from their «on Android the mouse no
	 * longer takes clicks»:
	 *
	 *   05:10  the laptop attaches, canvas 2544x926
	 *   05:12  silent for thirty seconds ⇒ DETACHED for silence, leaves the slot —
	 *          ⛔ but the session stays alive, with its video channel on and
	 *          its canvas in force
	 *   05:14  the phone attaches, canvas 2560x926
	 *   05:14  from here **seventeen requests per second**: the laptop asks for
	 *          2544, the phone 2560, the laptop 2544 … forever
	 *
	 * ⇒ And every round **restarts the PipeWire stream**, which on Mutter destroys
	 *   and recreates the `libei` devices: `[M]` 640 pointer «replacements», and
	 *   the input region never in agreement with the canvas («⚠ the region
	 *   2560x926 is NOT as big as the canvas 2544x926: I scale the
	 *   coordinates»).  ⛔ The symptom for the user names none of this: **clicks
	 *   no longer take**.
	 *
	 * ⛔ And the growing wait was NOT enough, for a reason that must be said: it
	 *    resets when the stage arrives where this session wants it — which in
	 *    the ping-pong happens at every round.  A time backstop does not cure two
	 *    masters: it cures one insistent master.
	 *
	 * ⇒ ⭐ The cure is the invariant that was already there: I2 says **a single
	 *   graphical session per user**, and the slot (§8.2 `0x0F`) is the way this
	 *   module enforces it.  Whoever does not hold the slot **watches** — does
	 *   not command.  ⚠ And when it speaks again it takes the slot back, and from
	 *   that moment it is the one in command. */
	if (!s->attaccata) {
		if (!s->tela_disaccordo_da) {
			s->tela_disaccordo_da = ora_ms;
			reg(s, "⚠ the stage is not at the canvas in force %ux%u, but this "
			       "session does NOT hold the slot (I2): I ask it nothing — "
			       "whoever is attached commands.  ⛔ Two sessions commanding "
			       "the same stage would fight over it at every frame",
			    s->tela_l, s->tela_a);
		}
		return;
	}
	if (!s->g.ritela) {
		if (!s->tela_disaccordo_da) {
			s->tela_disaccordo_da = ora_ms;
			reg(s, "⛔ the stage is not at the canvas in force %ux%u and I have no "
			       "hook to ask it to come there: from here all frames are "
			       "discarded (§6.2), and this line is the only one that says so",
			    s->tela_l, s->tela_a);
		}
		return;
	}
	if (s->tela_disaccordo_da
	    && ora_ms - s->tela_disaccordo_da < s->tela_disaccordo_attesa)
		return; /* asked only recently: one does not insist at every frame */

	/* ⛔⭐⭐ TO WHICH SIZE THE STAGE IS CALLED BACK, AND IT IS NOT ALWAYS THE CANVAS
	 *      IN FORCE — cure of 16 Aug 2026, bench `06-b36` case 13.
	 *
	 * ⛔ THE SCENE, and it is the one the box of §7.1 names first: *«a
	 *    remount of the graphical session after a crash»*.  The user narrows
	 *    the window, the server passes `ADATTA_TELA(1600x900)` to the stage, and
	 *    an instant later the stage remounts at 1024x768 on its own — that is NOT
	 *    in response to anything.  Branch 3 of `rcp_tela_dal_palco()` does not
	 *    recognise the request and ends up here.
	 *
	 * ⛔ Calling it back to the canvas IN FORCE (1920x1080) the server contradicts
	 *    the request it passed on itself an instant before, and **condemns to
	 *    `NON_ORA` an `ADATTA_TELA` that was about to succeed**: the stage goes
	 *    back to 1920x1080, the backstop of §7.1 expires, and the user sees their
	 *    window refused by a server that itself asked the stage to go back.
	 *    ⚠ No bench saw it, because the count of `TELA`s adds up: only one,
	 *    and it is the `NON_ORA` — the green to the wrong suspect.
	 *
	 * ⇒ If a request is IN FLIGHT the stage is called back to **that** size.
	 *   ⛔ And it is not a disguised unsolicited `TELA`, which is the thing never
	 *   to do: nothing goes out on the wire.  §3, exception 8: as long as there
	 *   is an unanswered `ADATTA_TELA` the client HOLDS BACK frames of a size
	 *   never announced, so asking the stage for the size in flight is exactly
	 *   the size the client is ready to receive.
	 *
	 * ⚠ And if the stage gets there, `rcp_tela_dal_palco()` recognises it as an
	 *   answer (`voluta` = what was asked for) and the `TELA(ADATTATA)` goes out
	 *   by the normal road: the user's request SUCCEEDS instead of
	 *   expiring. */
	uint32_t verso_l = s->tela_volo ? s->tela_volo_l : s->tela_l;
	uint32_t verso_a = s->tela_volo ? s->tela_volo_a : s->tela_a;

	if (!s->tela_disaccordo_da) {
		s->tela_disaccordo_attesa = RCP_TELA_RICHIAMO_MS;
		if (s->tela_volo)
			reg(s, "⛔ the stage went its own way WHILE %ux%u was in flight: "
			       "I ask it for %ux%u — the size IN FLIGHT, not the canvas in force "
			       "%ux%u.  ⚠ Calling it back would condemn to NON_ORA an "
			       "`ADATTA_TELA` that is about to succeed, and §3 exception 8 says "
			       "the client HOLDS BACK frames while it waits for the answer",
			    s->tela_volo_l, s->tela_volo_a, verso_l, verso_a, s->tela_l,
			    s->tela_a);
		else
			reg(s, "⛔ the stage is not at the canvas in force %ux%u: §6.2 forbids "
			       "sending a frame of a different size, so from here nothing "
			       "leaves any more.  I ask it for %ux%u — and I will insist with "
			       "a growing wait, because a `TELA` nobody "
			       "asked for would make the client close the session (§6.2)",
			    s->tela_l, s->tela_a, verso_l, verso_a);
	} else {
		s->tela_disaccordo_attesa *= 2;
		if (s->tela_disaccordo_attesa > RCP_TELA_RICHIAMO_MAX_MS)
			s->tela_disaccordo_attesa = RCP_TELA_RICHIAMO_MAX_MS;
		reg(s, "⛔ the stage is not yet at %ux%u (canvas in force %ux%u%s): "
		       "request repeated, next in %llu ms",
		    verso_l, verso_a, s->tela_l, s->tela_a,
		    s->tela_volo ? ", with a request in flight" : "",
		    (unsigned long long)s->tela_disaccordo_attesa);
	}
	s->tela_disaccordo_da = ora_ms;
	s->g.ritela(s->g.ctx, verso_l, verso_a);
}

/* ⭐⭐ THE STAGE'S ANSWER — see `rcp.h`, and the three cases are three.
 *
 * ⛔⛔ AND WHAT THIS FUNCTION **NO LONGER DOES**, because it was the most
 *     serious defect of the first draft: **it never sends a `TELA` nobody
 *     asked for.**
 *
 *     The first draft, when the stage changed size on its own, adopted its size
 *     and sent `TELA` so as not to leave the session without pixels.  ⚠ It
 *     looked like the kind choice and ⛔ it was fatal: §6.2 says the client
 *     holds back a size never announced **only while it has an unanswered
 *     `ADATTA_TELA`**, and there it has none ⇒ `ERRORE_PROTOCOLLO`, session
 *     closed.  And the frame travels on a stream of its own, so it can arrive
 *     **before** the `TELA` that would justify it: half the time.
 *
 * ⇒ The stage must serve the canvas in force, and if it is not there it is
 *   ASKED AGAIN, with a growing wait.  ⚠ Meanwhile the session shows the last
 *   good image: it is ugly and alive, which is what I1 requires. */
void rcp_tela_dal_palco(rcp_sessione *s, uint32_t voluta_l, uint32_t voluta_a,
                        uint32_t avuta_l, uint32_t avuta_a, uint64_t ora_ms)
{
	if (!s || !s->sessione_spedita)
		return;

	/* --- 1. the stage did not make it ---------------------------------- */
	/* ⛔ `0x0` is not a size: it is «I did not make it», and it must be told
	 *    apart from silence (`CODER.md` §3.10).  ⇒ If it was answering a request
	 *    of OURS, `NON_ORA` is answered **now** instead of letting the backstop
	 *    expire: three seconds of waiting for news that is already there. */
	if (!avuta_l || !avuta_a) {
		if (s->tela_volo && voluta_l == s->tela_volo_l
		    && voluta_a == s->tela_volo_a) {
			reg(s, "the stage could not give the canvas %ux%u: NON_ORA at once, "
			       "without waiting for the %u ms backstop (§7.1).  The canvas stays "
			       "%ux%u",
			    voluta_l, voluta_a, (unsigned)RCP_TELA_ATTESA_MS, s->tela_l,
			    s->tela_a);
			s->tela_volo = false;
			manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,
			           s->tela_a);
		}
		return;
	}

	/* --- 2. the stage is where it must be ------------------------------ */
	if (avuta_l == s->tela_l && avuta_a == s->tela_a) {
		if (s->tela_disaccordo_da) {
			reg(s, "⭐ the stage is back at the canvas in force %ux%u: the "
			       "disagreement is over",
			    avuta_l, avuta_a);
			s->tela_disaccordo_da = 0;
			s->tela_disaccordo_attesa = 0;
		}
		/* ⛔ And if the request in flight asked for PRECISELY this size, it is
		 *    an answer: the stage already had it.  ⚠ Without this line, asking
		 *    for the size that is already there while another is in flight would
		 *    close with no frame — and one would end up on the three-second
		 *    backstop. */
		if (s->tela_volo && voluta_l == s->tela_volo_l
		    && voluta_a == s->tela_volo_a) {
			s->tela_volo = false;
			reg(s, "TELA(ADATTATA) %ux%u: the stage already had that size",
			    avuta_l, avuta_a);
			manda_tela(s, 1 /* ADATTATA */, 0, s->tela_l, s->tela_a);
		}
		return;
	}
	/* --- 3. the stage is elsewhere ------------------------------------- */
	/* ⛔⭐ AND IT IS ADOPTED **ONLY** IF IT ANSWERS OUR REQUEST, that is if
	 *     `voluta` is the one we asked for.  ⚠ The size OBTAINED may be yet
	 *     another — §4.5 allows it, and on KWin < 6.8 it is the normal road —
	 *     but the RECOGNITION is made on the question, not on the answer.
	 *     ⛔ Recognising on the answer was the defect of the two chained
	 *     requests: the frame of the first was taken as the answer to the
	 *     second, and the desktop settled on the wrong size. */
	if (s->tela_volo && voluta_l == s->tela_volo_l
	    && voluta_a == s->tela_volo_a) {
		if (avuta_l != voluta_l || avuta_a != voluta_a)
			reg(s, "⚠ the stage granted %ux%u where %ux%u was asked: §4.5 "
			       "allows it, and the `TELA` leaving now carries the REAL "
			       "size",
			    avuta_l, avuta_a, voluta_l, voluta_a);
		/* ⛔ The decoder ceiling is NOT overridden here either (§4.5): a
		 *    canvas the client cannot decode is a black screen declared
		 *    instead of kept quiet — but black all the same. */
		if (s->max_l && (avuta_l > s->max_l || avuta_a > s->max_a)) {
			reg(s, "⛔ the stage gave %ux%u, beyond the video.misura_massima of "
			       "this client (%ux%u): I do NOT adopt it, and I answer NON_ORA.  "
			       "The canvas stays %ux%u and the stage is asked for that one",
			    avuta_l, avuta_a, s->max_l, s->max_a, s->tela_l, s->tela_a);
			s->tela_volo = false;
			manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,
			           s->tela_a);
			tela_richiama_il_palco(s, ora_ms);
			return;
		}
		s->tela_volo = false;
		s->tela_disaccordo_da = 0;
		s->tela_disaccordo_attesa = 0;
		/* ⛔ And the rest is done by the function that was already there: it
		 *    changes the canvas in force, opens the second of grace on the
		 *    coordinates, marks the keyframe debt (§5.2) and sends `TELA(ADATTATA)`. */
		rcp_tela_adattata_ora(s, avuta_l, avuta_a, ora_ms);
		return;
	}

	/* ═══════════════════════════════════════════════════════════════════
	 * ⛔⛔ 4. THE STAGE WAS ALREADY THERE AND DOES NOT MOVE — and the video never
	 *      started.  22 Sep 2026, the user's manual test on KDE.
	 *
	 * ⛔ THE SCENE, and they found it: the server restarts, the Plasma session
	 *    OUTLIVES it (invariant I4) with its stage at 2544x926, and the
	 *    client comes back in from a window of another size asking for
	 *    2560x962.  ⚠ The table of the stages' canvases lives in the PROCESS:
	 *    with the restart it resets, so the `ATTACCA` fallback — «what the
	 *    stage HAS is granted» — has nothing to grant and passes the client's
	 *    size.  ⇒ Canvas in force 2560x962, stage 2544x926, and §6.2 forbids
	 *    sending a frame of a different size: **black screen forever**,
	 *    while the log repeats «I ask it for 2560x962» with a wait that
	 *    doubles.  ⛔ And KWin `--virtual` does not resize: the request
	 *    cannot succeed either today or in an hour.  `[M]` cured by hand by
	 *    closing the user's session, which is the opposite of what I4 promises.
	 *
	 * ⭐ THE CURE: the stage's size is adopted, exactly as `ATTACCA` does
	 *    when it knows it — ⛔ but ONLY as long as not even one frame has gone out.
	 *    Before the first frame the client has not seen a pixel at this
	 *    canvas, has none in flight, and there is no race between streams
	 *    to arbitrate: the `TELA` leaving now is the only truth it will
	 *    ever have had.  ⚠ After the first frame NOTHING is touched and one
	 *    keeps asking, because there an unsolicited `TELA` would contradict
	 *    frames already delivered (§6.2) — and the rule is written in
	 *    `RCP.md` §7.1 instead of only here.
	 *
	 * ⚠ And the limits are checked again, as in branch 3: §4.5 and the decoder
	 *   ceiling of THIS client.  A stage out of limits is not adopted
	 *   — one keeps asking, and the black screen stays declared. */
	if (!s->video_spediti && !s->tela_volo
	    && (avuta_l != s->tela_l || avuta_a != s->tela_a)) {
		uint32_t pl = 0, pa = 0;
		if (!rcp_misura_ammessa(avuta_l, avuta_a, &pl, &pa)
		    || pl != avuta_l || pa != avuta_a) {
			reg(s, "⚠ the stage is at %ux%u, which §4.5 does not allow: I do NOT "
			       "adopt it and keep asking for the canvas in force %ux%u",
			    avuta_l, avuta_a, s->tela_l, s->tela_a);
		} else if (s->max_l && (avuta_l > s->max_l || avuta_a > s->max_a)) {
			reg(s, "⚠ the stage is at %ux%u, beyond the video.misura_massima of "
			       "this client (%ux%u): I do NOT adopt it and keep "
			       "asking for the canvas in force %ux%u",
			    avuta_l, avuta_a, s->max_l, s->max_a, s->tela_l, s->tela_a);
		} else {
			reg(s, "⭐ §7.1: the stage was already at %ux%u when this session was "
			       "born (canvas in force %ux%u) and NO frame has gone out "
			       "yet: I ADOPT its size instead of asking it for one "
			       "it cannot give.  ⛔ Without this line a compositor that "
			       "does not resize (KWin --virtual) leaves the screen black "
			       "forever after a server restart",
			    avuta_l, avuta_a, s->tela_l, s->tela_a);
			s->tela_disaccordo_da = 0;
			s->tela_disaccordo_attesa = 0;
			rcp_tela_adattata_ora(s, avuta_l, avuta_a, ora_ms);
			return;
		}
	}

	/* ⛔ No request of ours, or a different request: the stage is elsewhere
	 *    on its own.  ⚠ It may be a remount after a crash of the graphical
	 *    session, or the late frame of a request that has already expired.  ⇒
	 *    The canvas in force is ASKED FOR AGAIN, and nothing is adopted. */
	tela_richiama_il_palco(s, ora_ms);
}

bool rcp_tela_rimanda(rcp_sessione *s, uint32_t voluta_l, uint32_t voluta_a,
                      uint64_t ora_ms)
{
	if (!s || !s->tela_volo)
		return false;
	if (voluta_l != s->tela_volo_l || voluta_a != s->tela_volo_a)
		return false;
	/* ⭐ The start is moved, the backstop is not lengthened: so the ceiling of
	 *    §7.1 stays what it is, and counts from when someone is really trying. */
	s->tela_volo_da = ora_ms;
	reg(s, "§7.1: the stage is NOT there YET for the canvas %ux%u — the %u ms "
	       "backstop is POSTPONED instead of answering NON_ORA to a question about "
	       "to get a real answer",
	    voluta_l, voluta_a, (unsigned)RCP_TELA_ATTESA_MS);
	return true;
}

bool rcp_tela_in_volo(const rcp_sessione *s, uint32_t *lar, uint32_t *alt)
{
	if (!s || !s->tela_volo)
		return false;
	if (lar)
		*lar = s->tela_volo_l;
	if (alt)
		*alt = s->tela_volo_a;
	return true;
}

/* ⛔ §7.1 — THE BACKSTOP OF THE WAIT: «to every `ADATTA_TELA` the server MUST
 *    answer with a `TELA`, successful or not».  Called by `rcp_tempo()`, that is
 *    by the only place that sees time pass even when no byte arrives.
 *
 * ⚠ And the delay is NOT measured from when the message arrived but from when
 *   the question LEFT for the stage: they are the same instant today, and the
 *   day a queue sat in between they would no longer be. */
static void tela_scade(rcp_sessione *s, uint64_t ora_ms)
{
	if (!s->tela_volo)
		return;
	if (ora_ms - s->tela_volo_da < RCP_TELA_ATTESA_MS)
		return;
	reg(s, "⛔ ADATTA_TELA %ux%u: the stage did not deliver a frame at "
	       "that size within %u ms — I answer NON_ORA (§7.1: a silence "
	       "would leave the client waiting forever, and §6.2 makes it "
	       "HOLD BACK frames while it waits).  The canvas stays %ux%u",
	    s->tela_volo_l, s->tela_volo_a, (unsigned)RCP_TELA_ATTESA_MS, s->tela_l,
	    s->tela_a);
	s->tela_volo = false;
	manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l, s->tela_a);
}

void rcp_video_conti(const rcp_sessione *s, uint32_t *spediti,
                     uint32_t *abbandonati)
{
	if (spediti)
		*spediti = s ? s->video_spediti : 0;
	if (abbandonati)
		*abbandonati = s ? s->video_abbandonati : 0;
}

/* ⛔⭐ §5.1 — THE ABANDONMENT DECIDED DOWNSTREAM, AND WHY THE ONE ABOVE WAS NOT
 * ENOUGH.
 *
 * `rcp_video_abbandona()` below can abandon **the open frame**, that is one
 * still missing a piece to write.  ⛔ But the scene §5.1 describes in its own
 * words — «the server MAY call `RESET_STREAM` on a frame that is no longer
 * needed, **because a more recent one has already left**» — is not that one:
 * there the old frame was written WHOLE and closed with FIN, and it sits still
 * in the transport's output queue because the line does not carry it away.
 * For RCP that frame is already finished (`video_aperto` is false), and
 * `rcp_video_abbandona()` would return `false` without writing a line.
 *
 * ⇒ Whoever holds the queue — `webtransport.c` — is the only one that knows
 *   which frames are still **on the wire or before the wire**, and therefore
 *   the only one that can decide the abandonment of §5.1.  ⛔ But the three
 *   consequences of that abandonment belong to RCP and not to it: the mandatory
 *   log line (§5.1), the count of the abandoned, and ⛔ **the keyframe debt**
 *   (§5.2 — «when the server abandons a delta it MUST send a keyframe as soon
 *   as it can»).  Leaving them to whoever holds the queue would mean two copies
 *   of the same state, which is the shape `RCP.md` §0 exists to remove.
 *
 * ⛔ AND THE KEYFRAME IS NOT ABANDONED EVEN DOWNSTREAM: §5.2 forbids it without
 *    distinguishing who decides.  Here it is REFUSED and written, as above —
 *    otherwise the rule would apply to one road and not to the other, and
 *    which of the two is travelled would depend on how fast the line is. */
bool rcp_video_abbandonato_a_valle(rcp_sessione *s, uint32_t numero, bool chiave,
                                   size_t byte_non_usciti, const char *perche)
{
	if (!s)
		return false;
	if (chiave) {
		reg(s, "⛔ I do NOT abandon frame %u in the queue: it is a KEYFRAME, and "
		       "§5.2 forbids it downstream too (reason asked: %s) — %zu bytes "
		       "were left to go out",
		    numero, perche ? perche : "undeclared", byte_non_usciti);
		return false;
	}
	s->video_abbandonati++;
	/* ⛔ §5.1: «every abandonment MUST be written to the log: a frame lost in
	 * silence and one abandoned on purpose look the same from the receiving
	 * side».  ⚠ And it says how many bytes did NOT go out: it is the
	 * difference between «I threw it away before spending bandwidth» and «I had
	 * almost sent it already», which are two different facts for whoever
	 * regulates the rate. */
	reg(s, "frame %u ABANDONED IN THE QUEUE (§5.1, RESET_STREAM): %zu bytes "
	       "did not go out, why: %s — sent %u, abandoned %u",
	    numero, byte_non_usciti, perche ? perche : "undeclared",
	    s->video_spediti, s->video_abbandonati);
	/* ⛔ §5.2: «when the server abandons a delta, it MUST send a keyframe
	 * as soon as it can — without waiting for the client to ask». */
	chiave_serve(s, "a delta was abandoned in the queue (§5.1)");
	return true;
}

/* ⛔ §2.3 — THE MISSING STREAM CREDIT, WRITTEN TO THE LOG FROM ONE PLACE ONLY.
 *
 * §2.3 ends like this: «and in both cases **it is written to the log**», where
 * the two cases are the delta thrown away and the keyframe that waits.  ⛔ The
 * line exists because without it the symptom is *«screen frozen, and no line in
 * the log saying why»* — finding R1.9 names it word for word.
 *
 * ⚠ And the counter of the abandoned is NOT touched: here the stream was never
 *   born, so there is nothing to reset on the wire and the `numero` has not
 *   been consumed (§6.2: «NOT for those it does not send at all»).  They are
 *   two different quantities and keeping them together would confuse whoever
 *   diagnoses. */
void rcp_video_niente_credito(rcp_sessione *s, bool chiave, uint64_t restano)
{
	if (!s)
		return;
	if (chiave) {
		reg(s, "⛔ §2.3: no unidirectional stream for a KEYFRAME (the client "
		       "still grants %llu).  ⚠ The keyframe is NOT thrown away: §5.2 "
		       "wants it, the debt stays on and it is retried at the next "
		       "frame — «waiting for a free slot» is exactly what "
		       "§2.3 prescribes for keyframes",
		    (unsigned long long)restano);
		return;
	}
	reg(s, "⚠ §2.3: no unidirectional stream for the delta that came after "
	       "%u (the client still grants %llu): the delta is THROWN AWAY — «an "
	       "old delta is no longer needed, a new one is already arriving».  ⛔ "
	       "And it is not a fatal error: the session holds (§2.3)",
	    s->video_numero, (unsigned long long)restano);
	/* ⛔⭐ AND THE KEYFRAME DEBT IS SWITCHED ON — it was missing, and it is defect
	 *     B-18.
	 *
	 *   §5.2: «when the server abandons a delta, it MUST send a keyframe as
	 *   soon as it can, without waiting for the client to ask».  The two
	 *   twins that abandon a delta already do so — the abandonment in the queue
	 *   (above, §5.1) and `rcp_video_abbandona()` (below, §5.2) — and HERE the
	 *   harm seen from the receiving side is the same: the decoder is missing a
	 *   delta, and from there on it produces images more and more broken.
	 *
	 * ⛔ AND HERE IT IS NEEDED MORE THAN IN THE TWO TWINS, because the client
	 *    NEVER notices on its own:
	 *      · the `numero` has NOT been consumed (the box above, §6.2),
	 *        so in the numbers there remains **no gap** — and it is the only signal
	 *        on which §5.2 has the client ask for a keyframe;
	 *      · the encoder runs with an infinite GOP (`chiavi_ogni = 0`, in
	 *        `codificatore_di()` of `src/figlio.c` — line 4220 as of 23 Aug
	 *        2026; ⚠ the reference said `src/figlio.c:1568`, which is a point
	 *        of the file that code has not lived in for a while: it is the same
	 *        disease as the count of switch-ons below, and that is why here
	 *        there is the NAME of the function, which does not drift with the
	 *        lines), so another keyframe would **never again** arrive on its own.
	 *    ⇒ Without this line, ONE SINGLE delta skipped for lack of room
	 *      wrecks the image **forever and in silence**: no error,
	 *      no line, and the client has no way of asking for the cure.
	 *
	 * ⚠ And if room is still missing when the keyframe is ready, one does not fall
	 *   back into the case forbidden by R1.9: the `chiave` branch above does NOT
	 *   throw it away — it keeps the debt on and retries at the next frame, which
	 *   is what §2.3 prescribes for keyframes. */
	chiave_serve(s, "a delta was skipped for lack of room (§2.3), and "
	                "no gap remains in the numbers");
}

/* ⛔ §5.1 — the abandonment, and §5.2 forbids abandoning a KEYFRAME. */
bool rcp_video_abbandona(rcp_sessione *s, const char *perche)
{
	if (!s || !s->video_aperto)
		return false;
	if (s->video_e_chiave) {
		/* ⛔ §5.2: «the server MUST NOT abandon a keyframe.
		 * Abandoning the cure is not a cure».  ⚠ And the refusal is WRITTEN: a
		 * prohibition enforced in silence is indistinguishable from a
		 * prohibition nobody applied. */
		reg(s, "⛔ I do NOT abandon frame %u: it is a KEYFRAME, and §5.2 "
		       "forbids it (reason asked: %s)",
		    s->video_suo_numero, perche ? perche : "undeclared");
		return false;
	}
	s->g.video_azzera(s->g.ctx, s->video_stream);
	s->video_aperto = false;
	s->video_abbandonati++;
	/* ⛔ §5.1: «every abandonment MUST be written to the log: a frame lost in
	 * silence and one abandoned on purpose look the same from the receiving
	 * side». */
	reg(s, "frame %u ABANDONED (§5.1) after %zu bytes of %zu, stream %lld, "
	       "why: %s — sent %u, abandoned %u",
	    s->video_suo_numero, s->video_scritti, s->video_da_scrivere,
	    (long long)s->video_stream, perche ? perche : "undeclared",
	    s->video_spediti, s->video_abbandonati);
	/* ⛔ §5.2: «when the server abandons a delta, it MUST send a
	 * keyframe as soon as it can — without waiting for the client to
	 * ask, because the client notices one network round trip later».
	 * ⭐ It is the only cure we have: at a missing delta the decoder raises
	 * no error, it just produces images more and more broken. */
	chiave_serve(s, "a delta was abandoned (§5.2)");
	return true;
}

/* ⛔⭐⭐⭐ THE FRAME THROWN AWAY **BEFORE THE WIRE** — the form the receiver
 *        does not see, and that until 23 Sep 2026 DID NOT PAY THE KEYFRAME.
 *
 * `RCP.md` §5.1 lists TWO observable forms of abandonment — the stream
 * reset (A) and the gap in the `numero`s (B) — and then names a third that
 * «is not observable at all», the delta thrown away for lack of credit
 * (§2.3, cause 4).  ⛔ Of that third form there were **three instances**, and
 * only one paid the debt:
 *
 *   | who throws away                    | number consumed | debt paid |
 *   |---|---|---|
 *   | §2.3, the credit run out           | no | ✅ `rcp_video_niente_credito()` |
 *   | ⛔ the RATE REGULATOR (phase 9)     | no | ⛔ **none** |
 *   | ⛔ the CANVAS THAT DOES NOT MATCH (§6.2) | no | ⛔ **none** |
 *
 * ⭐⭐ It is §1.20 once more: *«a cure is sought wherever it applies, not where
 *     it was found»*.  The cure of cause 4 was written for the credit, and the
 *     two branches born later — the phase 9 regulator and the canvas check —
 *     throw away an **already encoded** frame in the very same way
 *     without anyone noticing.
 *
 * ⛔⛔ THE HARM, AND WHY NO COUNTER SEES IT — `[M]` 23 Sep 2026,
 *      box `rete11-gnome`, scenario `due-inquilini`, 180 s, two rounds:
 *
 *      | | Firefox (H.264) | Chrome (HEVC) |
 *      |---|---|---|
 *      | frames sent | 6938, numbered 1…6938 | 7351, numbered 1…7351 |
 *      | **gaps in the numbering** | **0** | **0** |
 *      | frames never sent because of the rate | **27** | **38** |
 *      | KEYFRAMES sent in the whole session | **1** | **1** |
 *      | `RICHIEDI_CHIAVE` received | **0** | **0** |
 *
 *      ⇒ 65 encoded frames thrown away, and the client could not notice
 *        in any way: the numbering that reaches it is CONTINUOUS, because the
 *        `numero` is born in `rcp_video_apri()` and those frames never get
 *        there.  ⛔ And the encoder runs with an infinite GOP
 *        (`chiavi_ogni = 0`, `codificatore_di()` in `src/figlio.c`): after
 *        keyframe 1 another keyframe **never again** arrives on its own.
 *      ⇒ The user saw the image IN TILES — the still areas (the icons)
 *        stayed the wrong mosaic, the moving ones were repainted
 *        and looked healthy — with **all counters green**.  It is exactly
 *        what §5.2 describes: *«at a missing delta the decoder raises no
 *        error, it just produces images more and more broken until the
 *        next keyframe»*.
 *
 * ⚠ WHY A NEW FUNCTION AND NOT `rcp_video_abbandonato_a_valle()`: that one
 *   is form **A**, and its line says «ABANDONED IN THE QUEUE (§5.1,
 *   RESET_STREAM): N bytes did not go out».  Here no stream was ever born
 *   and no byte went out: using it would write into the log one form in place
 *   of another — the E8 shape that `RCP.md` §11.1 (finding P7) exists to
 *   remove — and would make `video_abbandonati` grow, which the box of
 *   `rcp_video_niente_credito()` above expressly forbids («here the stream
 *   was never born, so there is nothing to reset on the wire and the `numero`
 *   has not been consumed»).
 *
 * ⚠ And the debt is ALWAYS switched on, even if what is thrown away was a
 *   KEYFRAME: a keyframe thrown away before the wire is not an «abandoned»
 *   keyframe in the sense of §5.2 — nothing was denied to it, it simply could
 *   not leave with those numbers (wrong canvas).  ⛔ Leaving the debt off there
 *   would mean no keyframe ever again, which is the worse fault of the two.
 *
 * ⭐ And it goes through the funnel: `chiave_serve()`.  The `serve_chiave` field
 *    is not touched by hand — see the box of the two functions, and the check
 *    `grep -n 'serve_chiave *=' src/rcp.c` which must give TWO lines only. */
void rcp_video_scartato_prima_del_filo(rcp_sessione *s, bool chiave,
                                       const char *perche)
{
	if (!s)
		return;
	/* ⛔ §5.1: «every abandonment MUST be written to the log: a frame lost in
	 * silence and one abandoned on purpose look the same from the receiving
	 * side».  ⭐ AND HERE IT COUNTS DOUBLE, because from the receiving side
	 * this has **no** look at all: the log line is the only place in the world
	 * where this fact exists.
	 *
	 * ⚠ BUT ONE LINE PER EPISODE, NOT PER FRAME: under congestion this
	 *   branch is travelled at 60/s, and sixty lines per second are the defect of
	 *   the 30.8 GB of log — the one that `chiave_intervallo_ms()` and the line
	 *   «the rate GOES DOWN» already exist not to redo.  ⭐ And the episode has a
	 *   NATURAL boundary and not a clock: as long as the debt is on the cure
	 *   is already travelling and the fact has not changed; when it goes off it
	 *   means a keyframe has GONE OUT WHOLE (`chiave_pagata()`), and the next
	 *   discard is a new fact that deserves its own line.
	 * ⛔ AND THE COUNT IS NOT LOST: how many frames were thrown away is
	 *    already known by the counters of `webtransport.c` — `video_ritmo_scesi`
	 *    for the regulator and `video_saltati` for the canvas — and they are
	 *    written by the «rate of …» line (one per second) and by the session's
	 *    «conto finale».
	 *    ⇒ Here the line carries the CAUSE, which is not there; the number is
	 *      there, which does not fit here. */
	if (!s->serve_chiave)
		reg(s, "⛔ %s frame THROWN AWAY BEFORE THE WIRE (the third form of §5.1, "
		       "the one the receiver does not see): %s.  ⚠ No stream opened, "
		       "no byte gone out, and the `numero` has NOT been consumed — after "
		       "%u the next in sequence will arrive, so no gap remains in the "
		       "numbers and the client cannot ask for anything.  ⭐ §5.2: the "
		       "KEYFRAME debt is switched on here, or the image stays broken "
		       "forever.  ⚠ One line per debt EPISODE: how many were "
		       "thrown away is said by `video_ritmo_scesi` and `video_saltati` "
		       "in the «rate of …» line and in the final count",
		    chiave ? "KEYFRAME" : "delta", perche ? perche : "undeclared",
		    s->video_numero);
	/* ⛔ AND THE DEBT IS ALWAYS SWITCHED ON, line or no line: it is a boolean, it
	 *    costs nothing to switch it on again, and tying it to the line would mean
	 *    tying a cure to a decision about log volume — which is the way to lose
	 *    the cure the day someone touches the backstop. */
	chiave_serve(s, "a frame was thrown away before the wire, and no gap "
	                "remains in the numbers (§5.1 third form, §5.2)");
}

int rcp_video_apri(rcp_sessione *s, bool chiave, size_t lunghezza,
                   uint64_t istante_us, uint32_t input, uint64_t ora_ms)
{
	if (!s)
		return RCP_VIDEO_NIENTE_CANALE;

	/* ⛔ ALL FOUR HOOKS OR NONE.  A host that could open and not
	 * reset could not honour §5.1, and would notice halfway through a
	 * frame: here the thing is said before opening anything. */
	if (!s->g.video_apri || !s->g.video_scrivi || !s->g.video_fin ||
	    !s->g.video_azzera)
		return RCP_VIDEO_NIENTE_CANALE;

	if (s->video_aperto)
		return RCP_VIDEO_GIA_APERTO;

	/* ⛔ P1 / §2.5 / invariant I3 — «none before having sent
	 * `SESSIONE`».  ⚠ And the FINISHED session counts as «no longer»: after a
	 * farewell the control channel is no longer there, and a frame that
	 * left now would reach nobody. */
	if (!s->sessione_spedita || s->stato == S_FINITA) {
		reg(s, "⛔ NO VIDEO: `SESSIONE` has not been sent (state %s) — "
		       "§2.5 forbids opening a video stream before, and it is "
		       "invariant I3 on the wire",
		    NOMI_STATO[s->stato]);
		return RCP_VIDEO_PRIMA_DI_SESSIONE;
	}

	/* ⛔ P6 and P9 / §5.2 — the first after `SESSIONE`, and the first at the new
	 * size after a `TELA`, MUST be a keyframe.  ⚠ Here one REFUSES
	 * instead of promoting the delta to keyframe: promoting it would be lying
	 * about the `tipo` field, and the frame would not become decodable on its own.
	 * The encoder has the right answer — `rcp_video_serve_chiave()` — and can
	 * ask it BEFORE encoding. */
	if (!chiave && s->serve_chiave) {
		reg(s, "⛔ FRAME NOT SENT: it is a delta and §5.2 wants a KEYFRAME "
		       "(%s).  ⚠ Asking `rcp_video_serve_chiave()` before "
		       "encoding costs nothing; here the frame is thrown away",
		    s->serve_chiave_perche ? s->serve_chiave_perche : "§5.2");
		return RCP_VIDEO_SERVE_UNA_CHIAVE;
	}

	/* ⛔ §6.2 — THE CEILING BINDS THE SENDER BEFORE ANYTHING ELSE, and that is
	 * why the check sits HERE: before opening the stream, before a byte leaves.
	 * «If encoding produced a larger one, it MUST re-encode it at lower
	 * quality and write it to the log — never send it».
	 *
	 * ⚠ And the comparison is `>` and not `>=`: exactly 16 MiB is legal, the
	 *   ceiling is a maximum.  The difference shows on one case only, and it is
	 *   the case the benches put there on purpose. */
	if (lunghezza > (size_t)(V_TETTO - V_INTESTAZIONE)) {
		reg(s, "⛔ FRAME NOT SENT: %zu data bytes + %d of "
		       "header exceed the %u of the §6.2 ceiling — it is RE-ENCODED at "
		       "lower quality, not sent",
		    lunghezza, V_INTESTAZIONE, V_TETTO);
		return RCP_VIDEO_TROPPO_GRANDE;
	}

	uint8_t codec = rcp_codec_negoziato(s);
	if (codec == 0) {
		/* §6.2: «MUST be the one negotiated in §4.3».  If there is no
		 * negotiation there is no legitimate value to write, and inventing one
		 * would be the E2 shape — two behaviours under the same label. */
		reg(s, "⛔ NO VIDEO: no codec negotiated in §4.3 (codec=«%s»), and "
		       "§6.2 wants the negotiated one",
		    s->codec);
		return RCP_VIDEO_NIENTE_CANALE;
	}

	int64_t stream = 0;
	/* ⛔ P3 / §2.5 — «only on a unidirectional stream opened by the server: a
	 * `0x03` on the control channel is `ERRORE_PROTOCOLLO`».  ⭐ The control
	 * channel in this module is written with `s->g.manda`, and from here down
	 * that function does not appear: it is the only way of making the rule
	 * impossible to violate instead of easy to respect. */
	uint64_t restano = 0;
	if (!s->g.video_apri(s->g.ctx, &stream, &restano)) {
		/* ⛔ §2.3 — and the two cases are NOT the same case: a delta is thrown
		 * away, a keyframe waits.  The line is written by one function only,
		 * because two lines written in two places diverge. */
		rcp_video_niente_credito(s, chiave, restano);
		return RCP_VIDEO_STREAM_NON_APERTO;
	}

	uint32_t num = numero_prossimo(s->video_numero);

	/* ⛔ §6.2 — THE 28 BYTES, IN THIS ORDER AND WITHOUT A BYTE OF PADDING.
	 *
	 *   0  tipo u16 · 2 codec u16 · 4 largh. u32 · 8 altezza u32 ·
	 *   12 numero u32 · 16 istante u64 · 24 input u32 · 28 dati
	 *
	 * ⚠ The drawing said «… 24 │ 32» until 9 Aug 2026: four bytes of
	 *   padding never declared, which two implementations could guess
	 *   the same without anyone noticing.  ⛔ `scrittore` writes byte
	 *   by byte in network order on purpose: a C `struct` with `memcpy` here
	 *   would bring that defect back, and not even a bench would see it until the
	 *   two sides ran on two different architectures. */
	uint8_t testa[V_INTESTAZIONE];
	scrittore w = {testa, sizeof testa, 0, false};
	sc_u16(&w, chiave ? V_CHIAVE : V_DELTA);
	sc_u16(&w, codec);
	/* ⛔ P5 / §6.2: the canvas IN FORCE — the one of `SESSIONE` (§4.5) or
	 * the last one granted by `TELA` (§7.1).  Not a parameter. */
	sc_u32(&w, s->tela_l);
	sc_u32(&w, s->tela_a);
	sc_u32(&w, num);
	/* ⚠ §6.2: microseconds of the server's MONOTONIC clock at capture.
	 *   It is not a time of day, and the client MUST NOT compare it with its own. */
	sc_u64(&w, istante_us);
	/* §6.2, §7.3: the last input injected before capture, 0 if none. */
	sc_u32(&w, input);

	/* ⛔ P4 / §6.2 — «a stream closed with FIN before the 28 bytes
	 * of the header is `ERRORE_PROTOCOLLO`: it is not a short frame, it is
	 * a length that does not add up».
	 *
	 * ⭐ Hence the form of these six lines: the 28 bytes go out in **a single**
	 *    write, and if they do not, it is RESET.  A stream reset at zero
	 *    bytes is an abandoned frame — §5.1, legal, the session holds —
	 *    while a FIN at zero bytes would be `ERRORE_PROTOCOLLO` and would bring
	 *    down a session in which the one at fault was us.
	 *    ⛔ The two closures are NOT interchangeable, and that is all of §6.2. */
	if (w.pieno || !s->g.video_scrivi(s->g.ctx, stream, testa, sizeof testa)) {
		s->g.video_azzera(s->g.ctx, stream);
		reg(s, "⛔ the 28 header bytes of frame %u did not "
		       "go out: stream %lld RESET (§6.2) — ⚠ never closed with FIN, or "
		       "it would have been «a length that does not add up»",
		    num, (long long)stream);
		/* The number has been consumed: §6.2 says the counter grows
		 * «including those it then abandons», and a gap «means something». */
		s->video_numero = num;
		return RCP_VIDEO_ROTTO_A_META;
	}

	s->video_aperto = true;
	s->video_stream = stream;
	s->video_e_chiave = chiave;
	s->video_suo_numero = num;
	s->video_da_scrivere = lunghezza;
	s->video_scritti = 0;
	s->video_numero = num;
	/* ⛔ The time is kept FROM HERE, and one does not go and ask the `istante`
	 * field for it: `istante` is the CAPTURE clock in microseconds (§6.2) and
	 * `ora_ms` the session clock in milliseconds.  That they are the same clock
	 * is likely and is written nowhere — and deriving one from the other
	 * would be indexing the 200 ms of §5.2 on a proxy quantity
	 * (`LEZIONI.md` §1.13). */
	s->video_aperto_ms = ora_ms;
	return RCP_VIDEO_SPEDITO;
}

int rcp_video_pezzo(rcp_sessione *s, const uint8_t *dati, size_t len)
{
	if (!s || !s->video_aperto)
		return RCP_VIDEO_STREAM_NON_APERTO;
	if (len == 0)
		return RCP_VIDEO_SPEDITO;
	/* ⛔ More bytes than were declared would mean that the ceiling of §6.2
	 * was checked on one number and the wire carries another:
	 * the check would become a formality.  It is reset. */
	if (len > s->video_da_scrivere - s->video_scritti) {
		reg(s, "⛔ frame %u wants to write %zu bytes beyond the %zu "
		       "declared: stream RESET — the ceiling of §6.2 had been "
		       "checked on the declared bytes",
		    s->video_suo_numero, len, s->video_da_scrivere);
		s->g.video_azzera(s->g.ctx, s->video_stream);
		s->video_aperto = false;
		s->video_abbandonati++;
		chiave_serve(s, "a frame broke halfway (§5.2)");
		return RCP_VIDEO_ROTTO_A_META;
	}
	if (!s->g.video_scrivi(s->g.ctx, s->video_stream, dati, len)) {
		s->g.video_azzera(s->g.ctx, s->video_stream);
		s->video_aperto = false;
		s->video_abbandonati++;
		reg(s, "⛔ frame %u broke at %zu bytes of %zu: stream "
		       "RESET (§6.2) — the client throws it away and treats it as a gap, "
		       "which is true; with a FIN it would have handed it to the "
		       "decoder, which is false",
		    s->video_suo_numero, s->video_scritti, s->video_da_scrivere);
		chiave_serve(s, "a frame broke halfway (§5.2)");
		return RCP_VIDEO_ROTTO_A_META;
	}
	s->video_scritti += len;
	return RCP_VIDEO_SPEDITO;
}

int rcp_video_finisci(rcp_sessione *s)
{
	if (!s || !s->video_aperto)
		return RCP_VIDEO_STREAM_NON_APERTO;
	/* ⛔ §6.2 — «a stream closed with FIN carries a COMPLETE frame».  The
	 * FIN is a statement, not a way of closing: if bytes are missing it is
	 * reset, and the client will treat the frame as a gap instead of
	 * handing half an image to the decoder (finding R1.7, 9 Aug
	 * 2026 — «an abandoned frame and a complete one looked the
	 * same», the E8 error shape). */
	if (s->video_scritti != s->video_da_scrivere) {
		reg(s, "⛔ frame %u has %zu bytes of the %zu declared: stream "
		       "RESET instead of closed with FIN — FIN means COMPLETE "
		       "(§6.2)",
		    s->video_suo_numero, s->video_scritti, s->video_da_scrivere);
		s->g.video_azzera(s->g.ctx, s->video_stream);
		s->video_aperto = false;
		s->video_abbandonati++;
		chiave_serve(s, "a frame broke halfway (§5.2)");
		return RCP_VIDEO_ROTTO_A_META;
	}
	s->g.video_fin(s->g.ctx, s->video_stream);
	s->video_aperto = false;
	s->video_spediti++;
	if (s->video_e_chiave) {
		/* ⛔ §5.2: the debt is paid ONCE.  ⚠ And it is switched off HERE and not
		 * at opening: a frame opened and then broken has paid nothing,
		 * and switching off the debt there would have left the client without a
		 * keyframe with the server convinced it had sent one. */
		chiave_pagata(s);
		s->mai_spedita_una_chiave = false;
		/* ⛔ §5.2 / §3 exception 5 — the 200 ms clock starts from HERE, that is
		 * from the keyframe SENT.  ⚠ And «sent» means «the bytes left
		 * us», not «it arrived»: see finding P17 in the report, which
		 * declares the difference instead of correcting it on its own initiative. */
		s->ultima_chiave_ms = s->video_aperto_ms;
		s->ultima_chiave_numero = s->video_suo_numero;
	}
	reg(s, "frame %u SENT: %s, codec %u, %ux%u, %zu data bytes, "
	       "stream %lld, FIN (§6.2: complete) — sent %u, abandoned %u",
	    s->video_suo_numero, s->video_e_chiave ? "KEYFRAME 0x0301" : "delta 0x0302",
	    rcp_codec_negoziato(s), s->tela_l, s->tela_a, s->video_scritti,
	    (long long)s->video_stream, s->video_spediti, s->video_abbandonati);
	return RCP_VIDEO_SPEDITO;
}

int rcp_video_spedisci(rcp_sessione *s, bool chiave, const uint8_t *dati,
                       size_t len, uint64_t istante_us, uint32_t input,
                       uint64_t ora_ms)
{
	int e = rcp_video_apri(s, chiave, len, istante_us, input, ora_ms);
	if (e != RCP_VIDEO_SPEDITO)
		return e;
	if (len) {
		e = rcp_video_pezzo(s, dati, len);
		if (e != RCP_VIDEO_SPEDITO)
			return e;
	}
	return rcp_video_finisci(s);
}

/* ========================================================================= */
/* ⭐ THE INPUT CHANNEL — `RCP.md` §2.5, §3, §3.1, §6.0, §6.1, §7.1, §7.3    */
/*                                                                           */
/* ⛔ WHAT THIS SECTION DOES NOT KNOW, AND IT IS HALF ITS JOB:                */
/*    it does not know what `libei` is, it does not know what a keyboard      */
/*    layout is, it does not know what a device is.  It reads bytes, judges   */
/*    them against §7.3 line by line, and calls one of the five hooks.  The   */
/*    other half — the one that touches the real desktop — is in `src/input.c`. */
/*                                                                           */
/* ⛔ AND THE RIGOR RULE (§3) APPLIES HERE AS ELSEWHERE: an unknown type, a   */
/*    length that does not add up, a field out of range, a message in the     */
/*    wrong state ⇒ `ERRORE_PROTOCOLLO`, with the reason, by both roads of    */
/*    §3.1.  ⚠ With ONE declared exception, and it is the third of the list   */
/*    of §3: the second of grace of §7.1.                                     */

/* ⛔⭐ §7.3 — «On detach everything is released», and the four roads that
 *     end a connection all pass through here.
 *
 * ⚠ And the fallback is DECLARED (`CODER.md` §4.2): if the hook is not there,
 *   this function writes that it is not there instead of keeping quiet —
 *   because «no key was pressed» and «I could not release anything» look the
 *   same, and it is `LEZIONI.md` §1.9 rule 1 in the field where it costs most:
 *   the symptom of both is a desktop that does not respond on reattach. */
static void rilascia_al_distacco(rcp_sessione *s, const char *perche)
{
	if (!s || s->inp_rilasciato)
		return;
	s->inp_rilasciato = true;
	if (!s->g.input_rilascia_tutto) {
		/* ⛔ It is written ONLY if this channel has seen something pass: on a
		 * session without input — the in-process benches, the ngtcp2 harness —
		 * the line would be noise at every farewell, and noise makes people stop
		 * reading the log precisely where it is needed. */
		if (s->inp_arrivati)
			reg(s, "⚠ DECLARED FALLBACK (§7.3): the connection ends (%s) and "
			       "this server does NOT have the release hook — %u inputs had "
			       "arrived and %u injected.  If something was left pressed, "
			       "it stays pressed",
			    perche, s->inp_arrivati, s->inp_iniettati);
		return;
	}
	int quanti = s->g.input_rilascia_tutto(s->g.ctx);
	/* ⛔⛔⭐ THREE OUTCOMES, THREE DIFFERENT LINES — 16 Aug 2026, and before there
	 *      was only one that printed `quanti` as if it were always a count.
	 *
	 *      In the real product it NEVER is: the one holding the map of pressed
	 *      keys is the child, and its answer does not come back.  ⇒ The
	 *      line said «0 were pressed» at every detach, including the four
	 *      in which the child, just below, wrote `2`.
	 *
	 *      ⚠ An invented number is worse than no number, and here it was the
	 *        worst possible: a ZERO on a rule whose only way of failing is
	 *        releasing nothing.  `LEZIONI.md` §1.9 — «empty» and
	 *        «right» with the same face. */
	if (quanti == RCP_RILASCIO_IMPOSSIBILE) {
		reg(s, "⛔ §7.3 — RELEASE ON DETACH (%s): the release could NOT be "
		       "requested from the stage.  ⚠ If something was pressed, it STAYS "
		       "pressed: on reattach the desktop may be unusable, and "
		       "this is the line that connects the two",
		    perche);
		return;
	}
	if (quanti == RCP_RILASCIO_SENZA_CONTO) {
		reg(s, "⭐ §7.3 — RELEASE ON DETACH (%s): request SENT to the stage. "
		       " ⚠ This line does NOT carry the number, because the one who knows "
		       "it is the child: the real count is the line «rilascio al distacco: "
		       "N fra tasti e pulsanti», a few milliseconds further down",
		    perche);
		return;
	}
	reg(s, "⭐ §7.3 — RELEASE ON DETACH (%s): %d keys and buttons were "
	       "pressed and have been released.  ⚠ Zero is a normal outcome and is NOT "
	       "a failure: it means nothing was down",
	    perche, quanti);
}

/* ⛔ §3.1 applied to this channel: one writes WHAT — the type, the field, the
 * value, the state — and then sends the farewell by both roads.  ⭐ The `CONGEDO`
 * goes out on the CONTROL channel even when the violation arrived on the
 * input stream, and it is §3.1 point 2 to the letter: «on the control channel,
 * **if the control channel is still usable**» — and here it usually is. */
static void viola_input(rcp_sessione *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));

/* ⭐ THE MODIFIERS, the only keys whose code goes into the log (phase 16
 *    §12): Ctrl 29/97, Shift 42/54, Alt 56/100, CapsLock 58, Meta 125/126.
 * ⚠ Twin of `registro_tasto_dicibile()` (`src/registro.c`): this module
 *   is also mounted without the server's log (`banchi/rcp/`), and so it
 *   carries the list with it. */
static bool tasto_dicibile(unsigned c)
{
	switch (c) {
	case 29: case 42: case 54: case 56: case 58:
	case 97: case 100: case 125: case 126:
		return true;
	default:
		return false;
	}
}
static void viola_input(rcp_sessione *s, const char *fmt, ...)
{
	char d[224];
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(d, sizeof d, fmt, ap);
	va_end(ap);
	congeda(s, RCP_ERRORE_PROTOCOLLO, d);
}

/* How many body bytes this type of §7.3 expects.  ⛔ `0` = a type this
 * channel does not know, and then it is `ERRORE_PROTOCOLLO` (§3): none of the five
 * has an empty body, so zero is not ambiguous. */
static uint32_t misura_input(uint16_t tipo)
{
	switch (tipo) {
	case T_PUNTATORE:
		return I_PUNTATORE;
	case T_PULSANTE:
		return I_PULSANTE;
	case T_ROTELLA:
		return I_ROTELLA;
	case T_LETTERA:
		return I_LETTERA;
	case T_POSIZIONE_TASTO:
		return I_POSIZIONE;
	default:
		return 0;
	}
}

static const char *nome_input(uint16_t tipo)
{
	switch (tipo) {
	case T_PUNTATORE:
		return "PUNTATORE";
	case T_PULSANTE:
		return "PULSANTE";
	case T_ROTELLA:
		return "ROTELLA";
	case T_LETTERA:
		return "LETTERA";
	case T_POSIZIONE_TASTO:
		return "POSIZIONE_TASTO";
	default:
		return "?";
	}
}

/* ⛔ All five hooks or none — the same rule as the four of video, and for the
 * same reason: a channel that could move the pointer and could not
 * release a button would leave the desktop worse than it found it. */
static bool ha_canale_input(const rcp_sessione *s)
{
	return s->g.input_puntatore && s->g.input_pulsante && s->g.input_rotella &&
	       s->g.input_lettera && s->g.input_posizione;
}

/* ⛔⭐ THE INJECTION SCOREKEEPER — and the outcomes are THREE, not two.
 *
 *   0  delivered to the compositor  ⇒ the `id` advances in the `input` field of §6.2
 *  -1  not delivered                ⇒ it does NOT advance, and it is written
 *   1  (`LETTERA` only) the character cannot be produced with the session's
 *      layout ⇒ it does NOT advance, and §7.3 REQUIRES writing it: «the server MUST
 *      write it to the log and MUST NOT send a different character nor
 *      keep quiet».
 *
 * ⛔ None of the three is a violation by the CLIENT: the message was valid, and
 *    closing the session because our compositor said no
 *    would punish whoever did nothing wrong — «an ugly session is worth more than
 *    a closed session» (`CODER.md` §1). */
static void segna_iniezione(rcp_sessione *s, uint16_t tipo, uint32_t id,
                            int esito, const char *cosa)
{
	if (esito == 0) {
		s->inp_iniettati++;
		/* ⛔ §6.2: it is HERE that the number that will come back in the frames
		 * advances — at the only point where «injected» is a fact and not a hope. */
		s->inp_ultimo_iniettato = id;
		return;
	}
	s->inp_non_iniettati++;
	if (esito == 1 && tipo == T_LETTERA)
		reg(s, "⛔ §7.3: the LETTERA %s (input id=%u) CANNOT be produced with the "
		       "layout of this session.  ⚠ No different character is sent "
		       "and one does not keep quiet: this is the line, and the `input` field "
		       "of the frames stays at %u because nothing was injected",
		    cosa, id, s->inp_ultimo_iniettato);
	else
		reg(s, "⚠ %s (input id=%u, %s) was NOT delivered to the compositor "
		       "(outcome %d): the session HOLDS — the client did nothing "
		       "wrong — and the `input` field of §6.2 stays at %u",
		    nome_input(tipo), id, cosa, esito, s->inp_ultimo_iniettato);
}

/* ⛔ §7.3 — THE COORDINATES, and this is the function that already has a finding
 *    (R1.16) written against it.
 *
 *   «`0 ≤ x < tela_larghezza`, `0 ≤ y < tela_altezza`.  On a 1920×1080 canvas
 *    the bottom-right corner is **1919, 1079**.»
 *
 * ⭐ Hence the two cases that must be kept apart, and getting them wrong cost a
 *    finding: **1919 on a 1920 canvas PASSES** — it is the last pixel, not an
 *    error — while **1920 on a 1920 canvas does NOT pass**.  The first of the two
 *    is the one a check written with `>` instead of `>=` ruins in silence,
 *    and the symptom would be a column of pixels on the right that cannot be
 *    clicked.
 *
 * ⛔ AND THE SECOND OF GRACE (§7.1, third exception of §3) is the other half:
 *    «a page that divides the mouse position by the scale factor and
 *    rounds up produces 1920 on a canvas of 1920: one reading
 *    injects it, the other CLOSES THE SESSION — and closing the session for a
 *    rounding is the thing `SPECIFICHE.md` §8.3 forbids».  ⇒ For one
 *    second after a canvas change a coordinate valid on the PREVIOUS one is
 *    CLAMPED to the last valid pixel instead of killing the session.
 *
 * ⚠ Outside that second, and outside a canvas change, the MUST of §7.3 stays
 *   whole: close.  ⛔ The grace is NOT a general tolerance on the
 *   coordinates — it would be the indulgence §3 exists to remove — and that is
 *   why it has a start date and a duration.
 *
 * Returns `true` if it can be injected; fills `*sx`/`*sy` with what must be
 * injected (equal to the input, save for clamping). */
static bool coordinate_ammesse(rcp_sessione *s, uint32_t id, uint32_t x,
                               uint32_t y, uint64_t ora, uint32_t *sx,
                               uint32_t *sy)
{
	*sx = x;
	*sy = y;
	/* ⛔ The normal case, and the comparison is `<` because they are PIXEL INDICES. */
	if (x < s->tela_l && y < s->tela_a)
		return true;

	bool grazia_aperta = s->tela_prec_l != 0 && s->tela_prec_a != 0 &&
	                     ora >= s->tela_grazia_da &&
	                     ora - s->tela_grazia_da <= TELA_GRAZIA;
	if (grazia_aperta && x < s->tela_prec_l && y < s->tela_prec_a) {
		*sx = x < s->tela_l ? x : s->tela_l - 1;
		*sy = y < s->tela_a ? y : s->tela_a - 1;
		s->inp_grazie++;
		/* ⛔ §3: «every tolerance must be written to the log.  A silent
		 * tolerance is indistinguishable from a defect». */
		reg(s, "⭐ §7.1 SECOND OF GRACE (time no. %u): input id=%u carries "
		       "(%u,%u), valid on the previous canvas %ux%u and outside the canvas "
		       "in force %ux%u — CLAMPED to (%u,%u) instead of closing.  %llu ms "
		       "of %d have passed since the canvas change",
		    s->inp_grazie, id, x, y, s->tela_prec_l, s->tela_prec_a, s->tela_l,
		    s->tela_a, *sx, *sy,
		    (unsigned long long)(ora - s->tela_grazia_da), TELA_GRAZIA);
		return true;
	}

	/* ⛔ §3.1 point 1: one says WHAT, and one also says why the grace did not
	 * cover — «out of range» alone would send people looking for the defect in
	 * the client even when the defect is a second expired by one millisecond. */
	if (s->tela_prec_l && !grazia_aperta)
		viola_input(s, "PUNTATORE id=%u at (%u,%u): outside the canvas in "
		               "force %ux%u (§7.3: 0<=x<%u, 0<=y<%u), and the grace second "
		               "of §7.1 expired %llu ms ago",
		            id, x, y, s->tela_l, s->tela_a, s->tela_l, s->tela_a,
		            (unsigned long long)(ora > s->tela_grazia_da + TELA_GRAZIA
		                                     ? ora - s->tela_grazia_da -
		                                           TELA_GRAZIA
		                                     : 0));
	else if (grazia_aperta)
		viola_input(s, "PUNTATORE id=%u at (%u,%u): outside the canvas in "
		               "force %ux%u AND outside the previous %ux%u — the grace of "
		               "§7.1 covers the coordinates of the old canvas, "
		               "not wrong coordinates",
		            id, x, y, s->tela_l, s->tela_a, s->tela_prec_l,
		            s->tela_prec_a);
	else
		viola_input(s, "PUNTATORE id=%u at (%u,%u): outside the canvas %ux%u "
		               "— §7.3 wants 0<=x<%u and 0<=y<%u, and the bottom right "
		               "corner is (%u,%u)",
		            id, x, y, s->tela_l, s->tela_a, s->tela_l, s->tela_a,
		            s->tela_l - 1, s->tela_a - 1);
	return false;
}

/* A whole input message, already framed.  `false` = session finished. */
static bool tratta_input(rcp_sessione *s, uint16_t tipo, const uint8_t *corpo,
                         uint32_t lung, uint64_t ora)
{
	lettore l = {corpo, lung, 0, false};
	uint32_t id = le_u32(&l);
	uint64_t istante = 0;
	for (int i = 0; i < 8; i++)
		istante = (istante << 8) | le_u8(&l);

	/* ⛔ §7.3: «⛔ 0 is reserved and means "no input"».  It is the value that
	 * §6.2 puts in the `input` field of frames when there has been nothing:
	 * accepting it here would mean that a frame could no longer say «nothing
	 * was injected» without also saying «the first was injected» —
	 * that is the implicit sentinel value §6.0 forbids. */
	if (id == 0) {
		viola_input(s, "%s with id=0: §7.3 reserves zero and gives it "
		               "the meaning «no input» in the `input` field of "
		               "the frames (§6.2)",
		            nome_input(tipo));
		return false;
	}
	/* ⛔⭐ §7.3: «it grows by AT LEAST ONE with every message, ACROSS THE WHOLE
	 *     INPUT CHANNEL — not one per type.  It is what comes back in the `input`
	 *     field of frames (§6.2), and with separate counters nothing would add up».
	 *
	 * ⚠ «At least one» and not «exactly one»: jumps are legitimate — a client
	 *   that discards an event of its own must not lie about the number — and what
	 *   is not legitimate is going back or repeating.
	 *
	 * ⛔ And the case that unmasks separate counters is only one, and it must go in
	 *    the bench: `PULSANTE(9)` and then `PUNTATORE(4)`.  With one counter per
	 *    type that 4 is a legitimate «first PUNTATORE» and passes; with the written
	 *    rule it is a violation.  A bench that sent only increasing ids within
	 *    each type would not tell the two implementations apart. */
	if (id <= s->inp_ultimo_id) {
		viola_input(s, "%s with id=%u, and the last id of THIS CHANNEL was %u: "
		               "§7.3 wants it to grow by at least one over the whole channel, "
		               "not one per type",
		            nome_input(tipo), id, s->inp_ultimo_id);
		return false;
	}

	uint32_t precedente = s->inp_ultimo_id;
	int esito = -1;
	char cosa[96];

	switch (tipo) {
	case T_PUNTATORE: {
		uint32_t x = le_u32(&l), y = le_u32(&l);
		uint32_t sx = 0, sy = 0;
		if (!coordinate_ammesse(s, id, x, y, ora, &sx, &sy))
			return false;
		s->inp_ultimo_id = id;
		s->inp_ultimo_istante_us = istante;
		snprintf(cosa, sizeof cosa, "(%u,%u)", sx, sy);
		esito = ha_canale_input(s) ? s->g.input_puntatore(s->g.ctx, sx, sy) : -1;
		break;
	}
	case T_PULSANTE:
	case T_POSIZIONE_TASTO: {
		uint16_t codice = le_u16(&l);
		uint8_t premuto = le_u8(&l);
		/* ⛔ §7.3: «1 = pressed, 0 = released», and §3 closes on «a field out of
		 * range».  ⚠ A 2 read as «true» would be the exact shape of the
		 * lenient parser: two implementations that behave the same
		 * until one of the two sends 2 by mistake, and then the key stays
		 * down forever and nobody knows why. */
		if (premuto > 1) {
			viola_input(s, "%s id=%u codice=%u with premuto=%u: §7.3 admits 1 "
			               "(pressed) and 0 (released), and nothing else",
			            nome_input(tipo), id, codice, premuto);
			return false;
		}
		s->inp_ultimo_id = id;
		s->inp_ultimo_istante_us = istante;
		/* ⛔⛔ PHASE 16 §12: «keystrokes are logged as "key", never as a
		 *      character» — and an evdev code IS a character, up to the
		 *      layout: this line, one per keystroke, turned the
		 *      log into a keylogger.  ⭐ The code stays for
		 *      BUTTONS and for MODIFIERS (`tasto_dicibile()`), which
		 *      say nothing about what is being typed and are the ones that stay
		 *      down (§11). */
		if (tipo == T_PULSANTE || tasto_dicibile(codice))
			snprintf(cosa, sizeof cosa, "evdev code %u (%#x) %s", codice,
			         codice, premuto ? "pressed" : "released");
		else
			snprintf(cosa, sizeof cosa, "key %s",
			         premuto ? "pressed" : "released");
		if (!ha_canale_input(s))
			esito = -1;
		else if (tipo == T_PULSANTE)
			esito = s->g.input_pulsante(s->g.ctx, codice, premuto);
		else
			esito = s->g.input_posizione(s->g.ctx, codice, premuto);
		break;
	}
	case T_ROTELLA: {
		/* ⛔ §6.0: `i32` in two's complement.  The cast from `uint32_t` to
		 * `int32_t` is implementation-defined up to C17; here it is done by
		 * hand, so the value does not depend on the compiler. */
		uint32_t ux = le_u32(&l), uy = le_u32(&l);
		int32_t ax = (int32_t)(ux <= 0x7FFFFFFFu ? (int64_t)ux
		                                         : (int64_t)ux - 4294967296LL);
		int32_t ay = (int32_t)(uy <= 0x7FFFFFFFu ? (int64_t)uy
		                                         : (int64_t)uy - 4294967296LL);
		s->inp_ultimo_id = id;
		s->inp_ultimo_istante_us = istante;
		/* ⛔⛔ AND HERE NOTHING IS TOUCHED: neither the sign, nor the rounding.
		 *
		 *     The sign of the vertical axis is inverted by `input_rotella()`, ONLY
		 *     ONCE and in one place only — it is written in `src/input.h` and in
		 *     `RCP.md` §7.3, box «The sign of the wheel», `[M]` 10 Aug
		 *     2026.  ⛔ Inverting it here too CANCELS it, and the symptom — «the
		 *     wheel goes backwards» — is the E11 error shape that that
		 *     box exists to avoid.
		 *
		 * ⚠ And half notches exist: 120 is one notch, **60 is half a notch and
		 *   is NOT rounded to zero**.  `STUDI.md` §gnome §9 says that
		 *   `ei_device_scroll_discrete` does an integer division by 120 and
		 *   eats them — but that is a choice of `input.c`, not of here: on this
		 *   side the number passes whole, as it arrived. */
		snprintf(cosa, sizeof cosa, "asse_x=%ld asse_y=%ld (120 = one notch)",
		         (long)ax, (long)ay);
		esito = ha_canale_input(s) ? s->g.input_rotella(s->g.ctx, ax, ay) : -1;
		break;
	}
	case T_LETTERA: {
		uint32_t car = le_u32(&l);
		/* ⛔ §7.3: «a UNICODE SCALAR VALUE: from 0 to 0x10FFFF, excluding the
		 * surrogates 0xD800-0xDFFF.  Out of range is `ERRORE_PROTOCOLLO`».
		 *
		 * ⚠ «Scalar value» is the technical term, and the surrogates are
		 *   precisely what distinguishes it from «code point»: a
		 *   check that stopped at `car > 0x10FFFF` would let through
		 *   0xD800, which cannot even be written in UTF-8.  ⛔ It is the case
		 *   a page produces on its own: JavaScript counts in UTF-16, and
		 *   `charCodeAt` on an emoji returns **half a surrogate pair**.
		 *   Whoever writes the client with `charCodeAt` instead of `codePointAt` sends
		 *   0xD83D, and the defect must be seen here — not injected as if it were a
		 *   letter.
		 *
		 * ⚠ And ZERO IS LEGITIMATE: U+0000 is a valid scalar value, and §7.3 says
		 *   «from 0».  ⛔ It is not a duplicate of the rule on the `id`, where zero is
		 *   reserved: they are two different fields with two different rules, and
		 *   copying the first onto the second would refuse a character that
		 *   the arbiter allows. */
		if (car > 0x10FFFFu) {
			viola_input(s, "LETTERA id=%u with character U+%X: §7.3 wants a "
			               "Unicode scalar value, from 0 to 0x10FFFF",
			            id, car);
			return false;
		}
		if (car >= 0xD800u && car <= 0xDFFFu) {
			viola_input(s, "LETTERA id=%u with character U+%04X: it is half of a "
			               "surrogate pair, and §7.3 excludes them — a Unicode "
			               "scalar value does not include 0xD800-0xDFFF",
			            id, car);
			return false;
		}
		s->inp_ultimo_id = id;
		s->inp_ultimo_istante_us = istante;
		/* ⛔ PHASE 16 §12: the character is NOT written (see POSIZIONE_TASTO
		 *    above).  ⚠ The two `viola_input` above still quote it:
		 *    they are values a letter cannot be, not keystrokes. */
		snprintf(cosa, sizeof cosa, "«a character»");
		esito = ha_canale_input(s) ? s->g.input_lettera(s->g.ctx, car) : -1;
		break;
	}
	default:
		/* Never reached: `misura_input()` has already refused the types it does
		 * not know, before buffering a byte.  The line is here so that the
		 * day the two lists drifted apart someone would say so. */
		viola_input(s, "type %#06x on the input channel: §7.3 defines five, from "
		               "0x0101 to 0x0105",
		            tipo);
		return false;
	}

	s->inp_arrivati++;
	if (!ha_canale_input(s)) {
		/* ⛔ «I have no input channel» is NOT «the client got it wrong».  The
		 * message was valid in every part — we have just judged it —
		 * and closing here would punish whoever did nothing wrong.  ⚠ It is the same
		 * distinction as `RCP_VIDEO_NIENTE_CANALE`, and the fallback is DECLARED
		 * (`CODER.md` §4.2): this is the line. */
		s->inp_non_iniettati++;
		reg(s, "⚠ %s id=%u %s: VALID and NOT injected — this server does not have the "
		       "five hooks of the input channel (§7.3).  The session HOLDS",
		    nome_input(tipo), id, cosa);
	} else {
		segna_iniezione(s, tipo, id, esito, cosa);
	}

	/* ⚠ The `istante` appears in the log and in no count: §7.3 says that
	 *   «no rule of this document consumes it», and that in a page the
	 *   grain is deliberately coarsened — `milliseconds × 1000` (finding
	 *   R1.27).  ⛔ Whoever derived a delay from it would measure the grain of a
	 *   browser's `performance.now()`, not our loop. */
	reg(s, "input id=%u (was %u) %s %s · client instant %llu us ⚠ coarsened "
	       "grain, §7.3: no measurement is built on it",
	    id, precedente, nome_input(tipo), cosa,
	    (unsigned long long)istante);
	return true;
}

/* ========================================================================= */
/* ⭐ THE CURSOR — `RCP.md` §7.2, §5.5, §5, §6.1                             */
/*                                                                           */
/* ⛔ WHO CHECKS WHAT, and the line is read only once:                        */
/*                                                                           */
/*    · the limits of **§5.5** — 256 per side, the hotspot inside             */
/*      the image, `0×0` with `0,0` for the hidden one — are enforced by      */
/*      `src/cursore.c` (A6), and HERE THEY ARE NOT CHECKED AGAIN.  Two checks */
/*      on the same rule in two places become two different rules the        */
/*      day one changes, and it is the shape of defect `RCP.md` §0            */
/*      exists to prevent;                                                    */
/*    · the **length of the message** belongs to this module, and §7.2 writes */
/*      it with a MUST: «the length of the message MUST be exactly            */
/*      `8 + larghezza × altezza × 4`».                                       */
/*                                                                           */
/* ⛔⭐ AND THE CONSEQUENCE OF GETTING IT WRONG IS OURS, NOT THE CLIENT'S: §7.2 */
/*     says a length that does not add up is `ERRORE_PROTOCOLLO` — but the    */
/*     one detecting it is THE RECEIVER.  ⇒ A crooked message sent from here  */
/*     makes **the page** close the session, and the server log would know    */
/*     nothing about it.  «A cursor made of someone else's memory» is the     */
/*     symptom §7.2 names; the lost session is what the user sees.            */
/*                                                                           */
/* ⇒ Hence the rule of this function: **when in doubt it is not sent**, and   */
/*   one writes why (`CODER.md` §4.2 — the fallback is DECLARED).  A cursor   */
/*   that does not update is ugly; a session that drops is broken.            */

int rcp_cursore_forma(rcp_sessione *s, uint16_t larghezza, uint16_t altezza,
                      int16_t attivo_x, int16_t attivo_y,
                      const uint8_t *immagine, size_t immagine_n)
{
	if (!s)
		return -1;
	/* §5: the cursor lives on the CONTROL channel, and before `SESSIONE` there
	 * is nobody to draw it — the client is not yet attached (§4.5).
	 * ⚠ It is nobody's violation: it is a shape arriving too early
	 *   from capture, which starts before the client attaches. */
	if (s->stato == S_FINITA || !s->sessione_spedita) {
		reg(s, "⚠ CURSORE_FORMA %ux%u NOT sent: `SESSIONE` has not gone out "
		       "(state %s) — §5, and it is nobody's error: capture "
		       "begins before the client attaches",
		    larghezza, altezza, NOMI_STATO[s->stato]);
		return -1;
	}

	/* ⛔⭐ §5.5 — «ONLY ONE OF THE TWO AT ZERO IS `ERRORE_PROTOCOLLO`», and this
	 *     check sits HERE EVEN THOUGH IT IS ALREADY IN `cursore.c` — decided by the
	 *     coordinator on 14 Aug 2026, after this report had
	 *     flagged it as an open hole.
	 *
	 * ⛔ And it is NOT going back to duplicating the limits of §5.5: the split is
	 *    another one, and it must be read because it is the reason this line does
	 *    not contradict the box above —
	 *
	 *      `cursore.c` decides **what** that cursor is: how big it is,
	 *                  where the hotspot is, whether it is hidden or not received;
	 *      `rcp.c`     ⛔ must not **EMIT** a message the specification
	 *                  forbids, EVER, by any road.
	 *
	 * ⛔⭐ AND THIS IS THE ONLY CASE IN WHICH THE LENGTH CHECK — which is
	 *     right — **IS NOT ENOUGH**: `0×5` gives `0 × 5 × 4 = 0` image bytes,
	 *     that is a message of **eight bytes** whose length **ADDS UP**.  The
	 *     malformed value passes precisely the check that should stop it, and
	 *     none of the other lines of this function looks at it.
	 *
	 * ⚠ The price of not having it: if one day someone called this function
	 *   from a road that does not pass through `cursore.c`, the client would receive a
	 *   message that §5.5 ORDERS it to refuse ⇒ **the session would drop
	 *   through our fault**, and the server log would know nothing about it.
	 *
	 * ⛔ And the pair is told apart only with both cases in the bench: `0×0` is
	 *    the HIDDEN cursor and **must pass**, `0×5` and `5×0` must not.  A check
	 *    that refused all zeros would be green with `0×0` alone — and would make
	 *    the hidden cursor disappear forever, that is the symptom «the pointer
	 *    stays still when I enter a text field». */
	if ((larghezza == 0) != (altezza == 0)) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NOT sent: §5.5 wants both sizes at "
		       "zero TOGETHER for the hidden cursor, and «only one of the two at "
		       "zero is ERRORE_PROTOCOLLO».  ⚠ The length WOULD ADD UP (8 bytes, "
		       "no pixel): it is the only case in which the length check "
		       "is not enough, and sending it would make THE PAGE close the session",
		    larghezza, altezza);
		return -1;
	}

	/* ⛔ §7.2 — THE LENGTH, and it is COMPUTED in one place only.
	 *
	 * ⚠ `(size_t)` on the factors, and it is not pedantry: `larghezza` and `altezza`
	 *   are `uint16_t` and in C they promote to `int`.  `65535 * 65535 * 4` in
	 *   `int` is **signed overflow**, that is undefined behaviour —
	 *   the compiler is free to give anything, and with `-O2` it usually
	 *   gives a small number.  It is the same defect the bench certification
	 *   found on 14 Aug 2026 on `6u + lung`, in another field and
	 *   with the same mechanism: the narrow arithmetic nobody looks at. */
	size_t pixel = (size_t)larghezza * (size_t)altezza;
	size_t byte_immagine = pixel * 4u;

	/* ⛔ The length declared by the caller and the one §7.2 imposes must
	 * match.  ⭐ And the comparison is NOT a formality: without `immagine_n`
	 * this function would read `larghezza × altezza × 4` bytes **on trust**
	 * — that is it would do exactly what §7.2 describes as «I read what is
	 * there and go on», only on the sender's side, where we would be the ones
	 * packaging the cursor made of someone else's memory. */
	if (byte_immagine != immagine_n) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NOT sent: §7.2 wants %zu image "
		       "bytes (8 + %ux%ux4 in the message) and the caller brings "
		       "%zu.  ⚠ Sending it would make THE PAGE close the session for "
		       "ERRORE_PROTOCOLLO, and this log would not know it",
		    larghezza, altezza, byte_immagine, larghezza, altezza, immagine_n);
		return -1;
	}
	/* ⛔ «Zero bytes» and «no pointer» are two different facts: the HIDDEN
	 * cursor of §5.5 is `0×0` **and** no byte, and there `NULL` is right.  With
	 * a size on it, instead, a `NULL` is a defect of the caller — and
	 * reading it would be the end of the process. */
	if (byte_immagine && !immagine) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NOT sent: the size wants %zu bytes and "
		       "the image pointer is NULL",
		    larghezza, altezza, byte_immagine);
		return -1;
	}

	/* ⛔ §6.1 — «no message MUST exceed 1 MiB», framing included
	 * (finding B-14).  ⭐ THIS rule belongs to this module, not to `cursore.c`:
	 * there lives §5.5 (256 per side), here §6.1 — and they are two different
	 * paragraphs with two different numbers.  ⚠ At the maximum §5.5 allows,
	 * 256×256, the message weighs 262 158 bytes: **it passes**, and must pass.
	 * A ceiling set wrongly here would kill the largest cursor the arbiter allows. */
	if (byte_immagine + 8u + 6u > MAX_MESSAGGIO) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NOT sent: the message would weigh %zu "
		       "bytes and §6.1 allows %u, framing included.  ⚠ §5.5 stops "
		       "at 256 per side and at that size it is 262 158: if we get here, "
		       "the limit of §5.5 was not enforced upstream",
		    larghezza, altezza, byte_immagine + 8u + 6u, MAX_MESSAGGIO);
		return -1;
	}

	/* ⛔ §7.2 — THE EIGHT BYTES, IN THIS ORDER AND WITHOUT PADDING (§6.0):
	 *   0 larghezza u16 · 2 altezza u16 · 4 attivo_x i16 · 6 attivo_y i16 · 8 …
	 *
	 * ⚠ `serie` of `CursoreForma` does NOT travel: it is the number by which
	 *   `cursore.c` recognises that the shape has not changed, and §7.2 does not
	 *   provide for it.  Putting it on the wire would be a field two implementations
	 *   guess differently.
	 * ⚠ And the POSITION is not there, because §7.2 says it «never travels in
	 *   this direction»: here only the shape travels. */
	size_t n = 8u + byte_immagine;
	uint8_t *corpo = (uint8_t *)malloc(n);
	if (!corpo) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NOT sent: out of memory (%zu bytes)",
		    larghezza, altezza, n);
		return -1;
	}
	scrittore w = {corpo, n, 0, false};
	sc_u16(&w, larghezza);
	sc_u16(&w, altezza);
	/* §6.0: `i16` in two's complement, big-endian.  The conversion to
	 * `uint16_t` is defined by the language and gives exactly those bits. */
	sc_u16(&w, (uint16_t)attivo_x);
	sc_u16(&w, (uint16_t)attivo_y);
	if (byte_immagine)
		memcpy(corpo + 8, immagine, byte_immagine);
	/* ⛔⭐ AND `n` IS SENT, NOT `w.len` — found by the bench at the first round,
	 *     14 Aug 2026.
	 *
	 *     `scrittore` counts the bytes that went through IT, and the image gets
	 *     there with a `memcpy` that `w.len` does not see: after the four `sc_u16`
	 *     it is **8**, and sending `w.len` sent a `CURSORE_FORMA` declaring
	 *     `larghezza=16, altezza=16` with **eight bytes of body**.
	 *
	 * ⛔ That is exactly the length that does not add up, produced by us: the page
	 *    would have closed with `ERRORE_PROTOCOLLO` at every cursor shape change,
	 *    and the symptom for the user would have been «the session drops
	 *    when I move the mouse over an edge».  ⚠ The server log wrote
	 *    the right line — «%zu bytes of body = 8 + 16x16x4» — because it
	 *    computed it from `n`: **the log told the truth and the wire something
	 *    else**, which is the shape of defect for which `CODER.md` §3.8 wants
	 *    verification from the receiving side.
	 *
	 * ⭐ What saw it was not a rereading: it was the judge, which reopens the
	 *    bytes that went out and redoes the count of §7.2 on them. */
	if (w.pieno || w.len != 8u) {
		/* Never reached: `corpo` is `n` big and the fields are eight bytes.  The
		 * line is there so that the day it were no longer true someone would
		 * say so, instead of sending a crooked message. */
		reg(s, "⛔ CURSORE_FORMA NOT sent: the eight bytes of the fields did not "
		       "go out (written %zu)",
		    w.len);
		free(corpo);
		return -1;
	}

	/* ⛔⭐ THE IMAGE IS COPIED IN HERE, AND THE CALL DOES NOT KEEP IT.
	 *
	 *     `src/cursore.h` says so: «it lives until the next callback: whoever
	 *     wants to keep it copies it».  ⇒ When this function returns, this module
	 *     no longer has any pointer to those bytes.
	 *
	 * ⚠ The price, declared: the bytes are copied TWICE — here into
	 *   `corpo`, and then in `manda_messaggio()` which puts the six framing
	 *   bytes in front.  ⛔ It is paid on purpose: the framing of §6.1 is written
	 *   in ONE place only, and copying it here to save a `memcpy` would put
	 *   two readers on the same field.  At the maximum of §5.5 it is 256 KiB on an
	 *   event that happens when the SHAPE changes — not at every frame, because
	 *   `cursore.c` removes the repeats. */
	manda_messaggio(s, T_CURSORE_FORMA, corpo, n);
	free(corpo);

	if (larghezza == 0 && altezza == 0)
		reg(s, "⭐ CURSORE_FORMA: HIDDEN cursor (§5.5), 8 bytes of body");
	else
		reg(s, "⭐ CURSORE_FORMA %ux%u sent, hotspot (%d,%d): %zu bytes "
		       "of body = 8 + %ux%ux4 (§7.2)",
		    larghezza, altezza, attivo_x, attivo_y, n, larghezza, altezza);
	return 0;
}

uint32_t rcp_input_ultimo_iniettato(const rcp_sessione *s)
{
	return s ? s->inp_ultimo_iniettato : 0;
}

uint32_t rcp_input_ultimo_id(const rcp_sessione *s)
{
	return s ? s->inp_ultimo_id : 0;
}

bool rcp_ricevi_input(rcp_sessione *s, int64_t stream, const uint8_t *dati,
                      size_t len, uint64_t ora)
{
	if (!s)
		return false;
	if (s->stato == S_FINITA) {
		/* ⚠ As in `rcp_ricevi()`: it is the only place from which one observes a
		 *   client that sends after the end (§4.2), and keeping quiet would make
		 *   whoever insists indistinguishable from whoever stopped.  ⛔ But here one
		 *   does not judge «farewell or attempt»: §8.1 wants the farewell on the
		 *   CONTROL channel, and a `CONGEDO` on this stream would anyway be a
		 *   channel in the wrong direction. */
		reg(s, "⛔ %zu bytes on input stream %lld AFTER the end of the "
		       "session from %s: §4.2 forbids sending on any channel",
		    len, (long long)stream, s->provenienza);
		return false;
	}

	/* ⛔⭐ §2.5 — «the input stream is opened AFTER receiving `SESSIONE`».
	 *
	 *     ⚠ And the quantity to look at is «`SESSIONE` HAS GONE OUT», not «the
	 *       state is active»: it is the same choice already made for video, and for
	 *       the same reason (see the `sessione_spedita` field).
	 *
	 * ⛔⭐ AND THIS TIME THE JUDGEMENT IS LEGITIMATE, while the twin of P20 was
	 *     not, and it is worth saying why: there the CLIENT could not measure
	 *     the order between two independent streams; here the SERVER measures
	 *     something IT did — whether it sent `SESSIONE` or not.  It is the «local,
	 *     monotonic quantity independent of delivery» of P20, from the right
	 *     side: if `SESSIONE` has not gone out, the client has not received it,
	 *     and no packet loss can change that. */
	if (!s->sessione_spedita) {
		viola_input(s, "bytes on the input stream (%lld) before `SESSIONE` "
		               "has gone out: §2.5 opens it AFTER receiving it (state: "
		               "%s)",
		            (long long)stream, NOMI_STATO[s->stato]);
		return false;
	}

	/* ⛔ §2.5: «**only one**, and kept open». */
	if (!s->inp_stream_noto) {
		s->inp_stream_noto = true;
		s->inp_stream = stream;
		reg(s, "⭐ INPUT channel open on stream %lld (§2.5: only one, "
		       "after `SESSIONE`, and kept open).  The injection hooks: %s",
		    (long long)stream,
		    ha_canale_input(s) ? "connected" : "⚠ NOT connected");
	} else if (stream != s->inp_stream) {
		viola_input(s, "a SECOND input stream (%lld) while the first (%lld) "
		               "is still the one: §2.5 admits only one",
		            (long long)stream, (long long)s->inp_stream);
		return false;
	}

	/* ⛔ The silence clock (§5.3) is also reset on input bytes, and it is not a
	 * convenience: without this line whoever uses the desktop **without
	 * writing anything on the control channel** — that is anyone just
	 * moving the mouse — loses the slot after thirty seconds while
	 * working.  §5.3 says «without a byte FROM THE CLIENT», and these are bytes
	 * of the client. */
	s->ultimo_byte = ora;
	/* ⛔⭐ AND THE SIGN OF LIFE TOO, for a reason that comes before
	 *     convenience: **an RCP byte arrived inside a packet**.  If
	 *     the byte is there, the packet was there — saying it here is not a
	 *     shortcut, it is the same thing said where it is seen.
	 *
	 * ⚠ And it makes `rcp_segno_di_vita()` a PURE ADDITION: it covers the case in
	 *   which packets arrive WITHOUT RCP bytes — that is the user who watches and
	 *   does not touch, which is the case it was born for.  ⛔ Without this line
	 *   the in-process benches (`04-b31`, `01-b12`) would have no sign of life:
	 *   they do not go through the transport, and they would detach thirty seconds
	 *   after opening whatever they did. */
	s->ultima_vita = ora;
	if (!torna_a_parlare(s))
		return false;

	while (len) {
		/* ⛔⭐ THE LENGTH IS CHECKED ON THE SIX HEADER BYTES, BEFORE
		 *     BUFFERING A BYTE OF BODY — §6.1: «the length is checked
		 *     before allocating.  A receiver that allocates `lunghezza` bytes and
		 *     then checks has already given a megabyte to anyone who can write
		 *     six bytes».
		 *
		 * ⭐ On this channel it can be done all the way, and on control it cannot:
		 *    the five types of §7.3 have a FIXED length, known from the `tipo`
		 *    alone.  ⇒ The buffer never exceeds 26 bytes, and whoever announces a
		 *    megabyte gets six and a farewell. */
		size_t spazio = I_ACCUMULO - s->inp_acc_len;
		size_t quanti = len < spazio ? len : spazio;
		if (quanti == 0) {
			/* Never reached as long as the pruning below works: the line
			 * is there so that the day it did not work someone would say so,
			 * instead of going round in circles. */
			viola_input(s, "input stream accumulation full (%zu bytes) "
			               "without a whole message: it is OUR defect",
			            s->inp_acc_len);
			return false;
		}
		memcpy(s->inp_acc + s->inp_acc_len, dati, quanti);
		s->inp_acc_len += quanti;
		dati += quanti;
		len -= quanti;

		for (;;) {
			if (s->inp_acc_len < 6)
				break;
			lettore intest = {s->inp_acc, s->inp_acc_len, 0, false};
			uint16_t tipo = le_u16(&intest);
			uint32_t lung = le_u32(&intest);

			/* ⛔ §2.5: on this stream the high byte is 0x01.  A `0x00` here is
			 * «the control channel on a unidirectional stream», a `0x03`
			 * is «video from the client»: they are violations with different names,
			 * and §3.1 point 1 wants the name. */
			if ((tipo >> 8) != 0x01) {
				const char *chi = (tipo >> 8) == 0x00   ? "CONTROL, which lives "
				                                          "only on the first "
				                                          "bidirectional stream"
				                  : (tipo >> 8) == 0x02 ? "the CLIPBOARD, "
				                                          "which wants a stream "
				                                          "of its own per transfer"
				                  : (tipo >> 8) == 0x03 ? "VIDEO, which belongs to "
				                                          "the server and goes the "
				                                          "other way"
				                  : (tipo >> 8) == 0x04 ? "AUDIO, which lives only "
				                                          "on datagrams"
				                                        : "a channel that §2.5 does "
				                                          "not define";
				/* ⚠ `0x%02x` and not `%#04x`: the latter, on the value ZERO, does
				 *   not print the prefix — it writes `0000` — and the control
				 *   channel is precisely `0x00`.  The most important high byte
				 *   of all would have been the only unreadable one. */
				viola_input(s, "type %#06x on the input stream: the high byte "
				               "0x%02x is %s (§2.5)",
				            tipo, (unsigned)(tipo >> 8), chi);
				return false;
			}

			uint32_t attesa = misura_input(tipo);
			if (attesa == 0) {
				viola_input(s, "type %#06x on the input channel: §7.3 "
				               "defines FIVE — 0x0101 PUNTATORE, 0x0102 "
				               "PULSANTE, 0x0103 ROTELLA, 0x0104 LETTERA, 0x0105 "
				               "POSIZIONE_TASTO",
				            tipo);
				return false;
			}
			/* ⛔ §6.1: «`lunghezza` MUST be the exact number of body bytes.  A
			 * receiver that reads a length inconsistent with what the type
			 * expects MUST close».  ⚠ And one says in which direction it is
			 * wrong: «more» and «fewer» send people looking for two different
			 * defects in the client. */
			if (lung != attesa) {
				if (lung > MAX_CORPO)
					viola_input(s, "%s (%#06x) announces %u body bytes: beyond "
					               "the 1 MiB ceiling of §6.1, and §7.3 wants "
					               "exactly %u",
					            nome_input(tipo), tipo, lung, attesa);
				else
					viola_input(s, "%s (%#06x) announces %u body bytes and §7.3 "
					               "expects %u (%u of id+istante plus %u of its "
					               "own): %s",
					            nome_input(tipo), tipo, lung, attesa, I_COMUNI,
					            attesa - I_COMUNI,
					            lung > attesa ? "EXTRA bytes, and §6.0 admits "
					                            "no padding"
					                          : "MISSING bytes");
				return false;
			}
			/* ⛔⭐ `(size_t)6u`, AND NOT `6u` — found by the bench certification
			 *     on 14 Aug 2026, injecting the `lunghezza-tardiva`
			 *     fault.
			 *
			 *     `lung` is `uint32_t`: `6u + lung` is computed at **32 bits**, and
			 *     with `lung = 0xFFFFFFFF` the result is not 4 294 967 301 —
			 *     it is **5**.  ⇒ A comparison `inp_acc_len < 6u + lung` would say
			 *     «the body has all arrived» after six bytes, and four gigabytes
			 *     of someone else's memory would be read starting from a buffer
			 *     of 32.
			 *
			 * ⚠ Here it is NOT reachable — the check `lung != attesa` sits
			 *   above and closes first — but «not reachable today» and «not
			 *   dangerous» are two different facts: whoever tomorrow moved that
			 *   check by three lines would put the out-of-bounds read back
			 *   without anything changing colour.  ⭐ It is invariant I7 read
			 *   from inside: the protection lives in the program, not in the order
			 *   in which someone left two `if`s. */
			if (s->inp_acc_len < (size_t)6u + lung)
				break; /* the body has not all arrived */

			if (!tratta_input(s, tipo, s->inp_acc + 6, lung, ora))
				return false;

			size_t consumati = (size_t)6u + lung;
			memmove(s->inp_acc, s->inp_acc + consumati,
			        s->inp_acc_len - consumati);
			s->inp_acc_len -= consumati;
		}
	}
	return true;
}

/* ========================================================================== */
/* ⭐⭐ THE CLIPBOARD — §7.4, §5.4, §2.5                                      */
/*                                                                            */
/* ⛔ AND THE DIRECTION USED MOST IS THE ONE THAT COSTS MOST WORK: «I copy an */
/*    address on the phone and paste it into the session» (`DECISIONI.md`    */
/*    §5-ter.1).  Over there we already have the text; over here it has to be */
/*    asked for **while someone is waiting with a finger on Ctrl+V**.         */

static bool ha_canale_appunti(const rcp_sessione *s)
{
	return s->g.appunti_apri && s->g.appunti_scrivi && s->g.appunti_fin
	       && s->g.appunti_offri && s->g.appunti_risposta;
}

static void viola_appunti(rcp_sessione *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));
static void viola_appunti(rcp_sessione *s, const char *fmt, ...)
{
	char d[224];
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(d, sizeof d, fmt, ap);
	va_end(ap);
	congeda(s, RCP_ERRORE_PROTOCOLLO, d);
}

/*
 * Sends ONE clipboard channel message, on its own stream, and closes it.
 *
 * ⛔⭐ ONE STREAM PER MESSAGE, AND NOT PER TRANSFER — and it is a point where
 *     §2.5 allows two readings, so the choice is written here instead of
 *     staying implicit (`PIANO.md` §0.4).
 *
 *     §2.5 says «one **per transfer**».  A transfer on our side is made of two
 *     messages far apart in time — `APPUNTI_ANNUNCIO` now, `APPUNTI_TESTO`
 *     **if and when** someone asks — and keeping a stream open between the two
 *     would mean keeping it open **forever** in the vast majority of cases:
 *     one copies much more often than one pastes, and §2.5 grants the server a
 *     finite number of streams.
 *
 * ⭐ And it can be done, because what binds the messages of a transfer is NOT
 *    the stream: it is the `trasferimento` field, which exists exactly for this
 *    (finding R1.11, 9 Aug 2026).  The receiver pairs by identifier, and which
 *    stream it arrived on nobody looks at.
 *
 * ⚠ The price, declared: a client that counted streams to count transfers
 *   would count double.  No line of `RCP.md` tells it to do so, and it has the
 *   field it must look at.
 */
static bool manda_appunti(rcp_sessione *s, uint16_t tipo, const uint8_t *corpo,
                          size_t corpo_n, const char *coda, size_t coda_n)
{
	uint8_t testa[6];
	int64_t stream = 0;
	uint64_t restano = 0;

	if (!ha_canale_appunti(s))
		return false;

	if (!s->g.appunti_apri(s->g.ctx, &stream, &restano)) {
		/* ⛔ Not a byte has left, and that is better than half a message.  ⚠ The
		 *    line says **how many streams remain**, asked of whoever holds the
		 *    transport: without that number «it could not be done» points
		 *    nowhere — it is the same reason as the video's `restano` (§2.3). */
		reg(s, "⛔ APPUNTI: no unidirectional stream for message "
		       "%#06x — the client still grants %llu (§2.5 wants one per "
		       "transfer)",
		    tipo, (unsigned long long)restano);
		return false;
	}

	testa[0] = (uint8_t)(tipo >> 8);
	testa[1] = (uint8_t)(tipo & 0xFF);
	{
		uint32_t lung = (uint32_t)(corpo_n + coda_n);
		testa[2] = (uint8_t)(lung >> 24);
		testa[3] = (uint8_t)(lung >> 16);
		testa[4] = (uint8_t)(lung >> 8);
		testa[5] = (uint8_t)lung;
	}

	if (!s->g.appunti_scrivi(s->g.ctx, stream, testa, sizeof testa)
	    || (corpo_n && !s->g.appunti_scrivi(s->g.ctx, stream, corpo, corpo_n))
	    || (coda_n
	        && !s->g.appunti_scrivi(s->g.ctx, stream, (const uint8_t *)coda,
	                                coda_n))) {
		/* ⛔ The stream is closed all the same: an open and mute stream holds a
		 *    slot in the client's count and never becomes a message — «empty
		 *    and forbidden with the same face», from the side of whoever waits.
		 * ⚠ The FIN on a half message is less bad than no FIN: the receiver
		 *   finds an incomplete framing and says so, instead of waiting for
		 *   bytes that will not arrive. */
		reg(s, "⛔ APPUNTI: message %#06x did not get into the queue on "
		       "stream %lld: I close the stream halfway",
		    tipo, (long long)stream);
		s->g.appunti_fin(s->g.ctx, stream);
		return false;
	}
	s->g.appunti_fin(s->g.ctx, stream);
	return true;
}

/*
 * ⛔⭐ THE HELD TEXT IS ANNOUNCED WHEN THE SESSION OPENS — 19 Sep 2026.
 *
 * `[M]` phase 12, `kde` box: a client that REATTACHES to a live child makes
 * the desktop clipboard be reread (`figlio.c`, the reattach branch), and the
 * read arrives while the RCP session is still in `attesa-verdetto`.  The
 * text was held — «for whoever will attach» — ⛔ but nobody ever announced it
 * afterwards: the client got in and did not know what was in the clipboard.
 * ⇒ It is announced here, after `SESSIONE` (§2.5: no stream before).
 */
static void annuncia_il_tenuto(rcp_sessione *s)
{
	uint8_t corpo[A_ANNUNCIO];
	scrittore w = {corpo, sizeof corpo, 0, false};

	if (!s->app_tenuto || !s->app_testo || !s->sessione_spedita)
		return;
	s->app_tenuto = false;
	sc_u32(&w, s->app_mio_id);
	sc_u32(&w, (uint32_t)s->app_testo_n);
	if (w.pieno || !manda_appunti(s, T_APPUNTI_ANNUNCIO, corpo, w.len, NULL, 0))
		return;
	s->app_annunciati++;
	reg(s, "⭐ APPUNTI §7.4: announced transfer %u to the client — %zu bytes "
	       "copied in the session BEFORE it opened, and held until now",
	    s->app_mio_id, s->app_testo_n);
}

bool rcp_appunti_dalla_sessione(rcp_sessione *s, const char *testo, size_t byte)
{
	uint8_t corpo[A_ANNUNCIO];
	scrittore w = {corpo, sizeof corpo, 0, false};
	char *copia;

	if (!s || !testo)
		return false;

	/* ⛔ §5.4 — «larger text: it is not announced at all, and the sender writes
	 *    it to the log.  It MUST NOT be truncated».  ⚠ And the comparison is
	 *    `>`: a text **exactly** as large as the ceiling is legitimate, and it is
	 *    the limit case for which §5.4 chose 1 000 000 instead of 1 MiB. */
	if (byte > RCP_APPUNTI_TETTO) {
		reg(s, "⛔ APPUNTI: the session copied %zu bytes, beyond the ceiling of "
		       "§5.4 (%u): it is NOT announced, and NOT truncated — a cut text "
		       "pasted into a terminal is worse than a missing text",
		    byte, RCP_APPUNTI_TETTO);
		return false;
	}

	if (!s->sessione_spedita || s->stato == S_FINITA) {
		/* ⚠ It is nobody's error: the graphical session outlives the
		 *   client (I4), so one can copy when there is not yet — or no longer —
		 *   anyone to announce it to.  ⛔ But the text is KEPT: whoever attaches
		 *   later finds it again, and it is the case that `STUDI.md`
		 *   §gnome §10 calls «whoever reconnects». */
		reg(s, "APPUNTI: the session copied %zu bytes and there is nobody to "
		       "announce them to (state %s): the text is kept for whoever "
		       "attaches",
		    byte, NOMI_STATO[s->stato]);
	}

	if (!s->negozia_appunti) {
		reg(s, "APPUNTI: the session copied %zu bytes and the client did not "
		       "declare `appunti.testo` (§4.3): nothing is announced",
		    byte);
		return false;
	}

	copia = (char *)malloc(byte + 1u);
	if (!copia) {
		reg(s, "⛔ APPUNTI: %zu bytes copied from the session do not fit in "
		       "memory: no announcement",
		    byte);
		return false;
	}
	memcpy(copia, testo, byte);
	copia[byte] = 0;
	free(s->app_testo);
	s->app_testo = copia;
	s->app_testo_n = byte;

	/* ⛔ §7.4: «each side numbers **its own** transfers, from 1
	 *    upwards».  ⚠ Zero is reserved — it means «no announcement» —
	 *    so at counter wraparound it is skipped, as the `numero` of the
	 *    frames of §6.2 does for the same reason. */
	s->app_mio_id = s->app_mio_id == 0xFFFFFFFFu ? 1u : s->app_mio_id + 1u;
	s->app_mio_len = byte;

	if (!s->sessione_spedita || s->stato == S_FINITA) {
		s->app_tenuto = s->stato != S_FINITA;
		return false;
	}
	s->app_tenuto = false;

	sc_u32(&w, s->app_mio_id);
	sc_u32(&w, (uint32_t)byte);
	if (w.pieno)
		return false;

	if (!manda_appunti(s, T_APPUNTI_ANNUNCIO, corpo, w.len, NULL, 0))
		return false;

	s->app_annunciati++;
	reg(s, "⭐ APPUNTI §7.4: announced transfer %u to the client — %zu bytes "
	       "of text copied in the session.  ⚠ Nothing is sent until "
	       "it asks for them",
	    s->app_mio_id, byte);
	return true;
}

bool rcp_appunti_chiedi(rcp_sessione *s, uint32_t serial, uint64_t ora_ms)
{
	uint8_t corpo[A_CHIEDI];
	scrittore w = {corpo, sizeof corpo, 0, false};

	if (!s)
		return false;

	if (!s->sessione_spedita || s->stato == S_FINITA) {
		reg(s, "APPUNTI: someone in the session is pasting (request %u) and "
		       "there is no client attached (state %s)",
		    serial, NOMI_STATO[s->stato]);
		return false;
	}

	/* ⛔ The request is queued BEFORE sending: if the text arrived
	 *    between the sending and the note — impossible today, the module is
	 *    single-threaded — the answer would find nobody to serve.  ⚠ It is the
	 *    same shape as the rule «first the credit is counted, then delivered»
	 *    of `webtransport.c`: the order costs nothing and removes a class of
	 *    defects. */
	if (s->app_serial_n >= A_STREAM_MAX) {
		reg(s, "⛔ APPUNTI: already %d paste requests waiting for the client's "
		       "text: request %u does not fit.  ⚠ The host must answer «I do not "
		       "have it» to this one, or the pasting application stays hanging",
		    s->app_serial_n, serial);
		return false;
	}
	s->app_serial[s->app_serial_n++] = serial;
	/* ⛔ The backstop clock starts from the FIRST request of the batch, not
	 *    from the last: it is the first that is waiting, and it is its wait
	 *    that must be limited. */
	if (s->app_serial_n == 1)
		s->app_chiesto_ms = ora_ms;

	/* ⛔⭐⭐ AND IF THE CLIENT HAS NOT YET ANNOUNCED ANYTHING, ONE WAITS — and
	 *      this is the cure for the race between `Ctrl+V` and the reading of the
	 *      clipboard, which `SPECIFICHE.md` §9 names and declares it does NOT
	 *      want to solve like Xpra.
	 *
	 *      The race, in full: the user hits `Ctrl+V` in the browser.  The keys
	 *      leave on the input channel and arrive at the desktop; the clipboard
	 *      announcement leaves on the clipboard channel and travels the same
	 *      road.  ⛔ But the desktop, having received the `Ctrl+V`, asks for the
	 *      text **at once** — and the announcement may not have arrived yet.
	 *      ⇒ The FIRST paste of every new text would come back empty.
	 *
	 * ⛔ Xpra's cure is delaying **every keystroke by 100 ms**: §9 refuses it
	 *    with a number — «for us it is twice the delay ceiling», that is one
	 *    would pay on every key of every session for something that happens
	 *    when pasting.
	 *
	 * ⭐ The replacement costs nothing and touches no key: the request is
	 *    QUEUED and the question leaves when the announcement arrives (see
	 *    `T_APPUNTI_ANNUNCIO` in `tratta_appunti`).  ⚠ And the wait is already
	 *    limited by someone else: the child's time backstop answers «I do not
	 *    have it» to whoever pastes if the announcement never arrives — ⛔ and
	 *    that backstop is there because the debt towards the compositor is the
	 *    child's, not ours. */
	if (s->app_suo_id == 0) {
		reg(s, "⭐ APPUNTI: someone in the session is pasting (request %u) and "
		       "the client's announcement has not arrived yet: the question WAITS "
		       "for the announcement instead of coming back empty (§9 — the race "
		       "with `Ctrl+V`, cured without delaying keys)",
		    serial);
		return true;
	}
	/* ⚠ One `CHIEDI` for the batch, not one per request: two programs that
	 *   paste together ask for the same transfer, that is the same text, and
	 *   the answer serves them all. */
	if (s->app_chiesto) {
		reg(s, "APPUNTI: request %u joins transfer %u already "
		       "asked for: a single question, and the answer serves them all",
		    serial, s->app_suo_id);
		return true;
	}

	sc_u32(&w, s->app_suo_id);
	if (w.pieno || !manda_appunti(s, T_APPUNTI_CHIEDI, corpo, w.len, NULL, 0)) {
		s->app_serial_n--;
		return false;
	}

	s->app_chiesto = true;
	s->app_chiesto_id = s->app_suo_id;
	s->app_chiesti++;
	reg(s, "⭐ APPUNTI §7.4: asked the client for transfer %u (%u bytes "
	       "announced) — someone in the session is pasting (request %u)",
	    s->app_suo_id, s->app_suo_len, serial);
	return true;
}

/* The question that had been left waiting for the announcement: now it is here.
 * ⛔ `false` = it did not leave, and then the queued requests stay hanging on
 *    the child's time backstop. */
static bool appunti_chiedi_l_arretrato(rcp_sessione *s)
{
	uint8_t corpo[A_CHIEDI];
	scrittore w = {corpo, sizeof corpo, 0, false};

	if (s->app_serial_n == 0 || s->app_chiesto || s->app_suo_id == 0)
		return false;

	sc_u32(&w, s->app_suo_id);
	if (w.pieno || !manda_appunti(s, T_APPUNTI_CHIEDI, corpo, w.len, NULL, 0))
		return false;

	s->app_chiesto = true;
	s->app_chiesto_id = s->app_suo_id;
	s->app_chiesti++;
	reg(s, "⭐ APPUNTI §9: announcement %u has arrived, and there were already %d "
	       "paste requests waiting for it: the question leaves NOW.  It is the "
	       "race with `Ctrl+V`, won without delaying a single key",
	    s->app_suo_id, s->app_serial_n);
	return true;
}

/* Serves ALL the waiting requests with the same text: they ask for the same
 * transfer identifier, that is the same content.  ⛔ And the queue is emptied
 * **before** answering: an answer that re-entered here must not find again the
 * requests it is already serving. */
static void appunti_servi_in_attesa(rcp_sessione *s, const char *testo,
                                    size_t byte)
{
	uint32_t serial[A_STREAM_MAX];
	int quanti = s->app_serial_n;

	memcpy(serial, s->app_serial, sizeof serial);
	s->app_serial_n = 0;
	s->app_chiesto = false;

	if (!s->g.appunti_risposta) {
		reg(s, "⛔ APPUNTI: %d paste requests without any hook to "
		       "answer: whoever pastes stays hanging until the backstop expires "
		       "on the other side of the boundary",
		    quanti);
		return;
	}
	for (int i = 0; i < quanti; i++)
		s->g.appunti_risposta(s->g.ctx, serial[i], testo, byte);
	if (quanti)
		reg(s, "⭐ APPUNTI: %zu bytes from the client delivered to %d paste "
		       "requests",
		    byte, quanti);

	/* ⭐ And NOW the offer that had been postponed: the transfer is over,
	 *    and the compositor can take the new selection without throwing
	 *    anything away. */
	if (s->app_offri_dopo && s->g.appunti_offri) {
		s->app_offri_dopo = false;
		if (!s->g.appunti_offri(s->g.ctx))
			reg(s, "⛔ APPUNTI: the postponed offer did not succeed: inside the "
			       "desktop the next paste will not find the new text");
		else
			reg(s, "⭐ APPUNTI: the paste served, the postponed offer has "
			       "left: the desktop has the client's NEW text");
	}
}

/* A whole message of the clipboard channel.  `false` = the session is over. */
static bool tratta_appunti(rcp_sessione *s, uint16_t tipo, const uint8_t *corpo,
                           uint32_t lung)
{
	lettore l = {corpo, lung, 0, false};
	uint32_t trasf;

	switch (tipo) {
	case T_APPUNTI_ANNUNCIO: {
		uint32_t quanti;

		trasf = le_u32(&l);
		quanti = le_u32(&l);
		if (l.corto)
			return true; /* the fixed size has already been validated */

		/* ⛔ §7.4: transfers are numbered «from 1 upwards», and zero is
		 *    reserved.  An announcement with `trasferimento = 0` is not a poor
		 *    announcement: it is an identifier that can never be asked for. */
		if (trasf == 0) {
			viola_appunti(s, "APPUNTI_ANNUNCIO with transfer 0: §7.4 numbers "
			                 "them from 1, and 0 means «no announcement»");
			return false;
		}
		/* ⛔ §5.4: the ceiling binds the sender first of all, but whoever
		 *    receives a larger announcement must not get ready to take it in: it
		 *    is a client that has violated §5.4, and §3 makes no discounts. */
		if (quanti > RCP_APPUNTI_TETTO) {
			viola_appunti(s, "APPUNTI_ANNUNCIO of %u bytes: §5.4 stops at %u, and beyond "
			                 "the ceiling NOTHING is announced at all",
			              quanti, RCP_APPUNTI_TETTO);
			return false;
		}

		s->app_suo_id = trasf;
		s->app_suo_len = quanti;
		reg(s, "⭐ APPUNTI §7.4: the client announces transfer %u — %u "
		       "bytes.  ⚠ Nothing is pulled until someone in the session "
		       "pastes",
		    trasf, quanti);

		/* ⛔ And it is OFFERED to the session, at once: without this step the
		 *    compositor does not own the selection, and inside the desktop
		 *    **one cannot even try to paste** — the key does nothing, and there
		 *    is no error anywhere. */
		if (!s->g.appunti_offri) {
			reg(s, "⚠ APPUNTI: no hook to offer to the session — the "
			       "client copied some text and inside the desktop it will not "
			       "be possible to paste.  ⛔ It is not an error of the client: it "
			       "is this server that does not have that channel");
			return true;
		}
		/* ⛔⛔⭐ AND AN EMPTY ANNOUNCEMENT IS OFFERED ALL THE SAME, and it is a
		 *      choice.
		 *
		 * ⚠ The client sends a zero-byte announcement as soon as the session is
		 *   born, to be found when someone on this side pastes with the mouse:
		 *   without it, the server would never ask it anything (see
		 *   `rcp_appunti_chiedi`).
		 *   ⛔ And offering means taking the selection, which is ONE: the
		 *     desktop clipboard changes hands.
		 * ⭐ It changes hands but is NOT lost: if the client has nothing to give,
		 *   `appunti.c` gives back to the session the last text the session
		 *   itself had given us.  ⇒ The content is safe, and the road of
		 *   pasting with the mouse stays open.
		 * ⚠ Here there was a rule that did NOT offer on empty announcements: it
		 *   protected the clipboard but closed the mouse road, and the protection
		 *   sits better where it is now — where the text really is. */

		/* ⛔ But NOT while someone is pasting: see `app_offri_dopo`. */
		if (s->app_serial_n > 0) {
			s->app_offri_dopo = true;
			reg(s, "⚠ APPUNTI: announcement %u arrives while %d paste "
			       "requests are waiting for the text: the offer to the session is "
			       "POSTPONED, or the compositor would throw away precisely "
			       "the paste in progress",
			    trasf, s->app_serial_n);
			appunti_chiedi_l_arretrato(s);
			return true;
		}
		if (!s->g.appunti_offri(s->g.ctx))
			reg(s, "⛔ APPUNTI: the offer of transfer %u to the session did not "
			       "succeed: inside the desktop it will not be possible to paste "
			       "what the client copied",
			    trasf);

		/* ⭐⭐ AND HERE THE RACE WITH `Ctrl+V` IS WON: if someone was already
		 *     pasting when the announcement arrived, the question leaves now
		 *     instead of having come back empty a moment ago (§9, and the box of
		 *     `rcp_appunti_chiedi`). */
		appunti_chiedi_l_arretrato(s);
		return true;
	}

	case T_APPUNTI_CHIEDI: {
		trasf = le_u32(&l);
		if (l.corto)
			return true;

		/* ⛔ §7.4: «an `APPUNTI_CHIEDI` with an identifier that does not
		 *    match any live announcement is `ERRORE_PROTOCOLLO`».  ⚠ And
		 *    «live» includes superseded ones: see the case just below, which is
		 *    the FIFTH exception declared in §3. */
		if (trasf == 0 || trasf > s->app_mio_id) {
			viola_appunti(s, "APPUNTI_CHIEDI for transfer %u, which "
			                 "matches no announcement: I have made %u "
			                 "(§7.4)",
			              trasf, s->app_mio_id);
			return false;
		}
		if (!s->app_testo) {
			/* ⚠ It can happen: one announced, and then the stage was taken down
			 *   carrying the text away.  It is not the client's fault, and §3.1
			 *   wants it said instead of kept quiet. */
			reg(s, "⛔ APPUNTI: the client asks for transfer %u and the text "
			       "is no longer there: nothing will reach it",
			    trasf);
			return true;
		}
		/* ⛔⭐ THE FIFTH EXCEPTION DECLARED IN §3 — §7.4: «an `APPUNTI_CHIEDI`
		 *     arriving when the announcement has already been superseded by a
		 *     more recent one **is served with the current text**, and the
		 *     sender writes it to the log: it is the normal race between two
		 *     people copying, not an error».
		 * ⚠ And one ANSWERS with the identifier ASKED FOR, not the current one:
		 *   the client expects an answer to its question, and changing the
		 *   number under it would be an answer it cannot pair. */
		if (trasf != s->app_mio_id)
			reg(s, "⚠ APPUNTI §7.4: the client asks for transfer %u, which has "
			       "already been superseded by %u: I serve it with the CURRENT text "
			       "(%zu bytes).  It is the normal race between two people copying, "
			       "not an error",
			    trasf, s->app_mio_id, s->app_testo_n);

		{
			uint8_t testa_corpo[A_TESTO_MINIMO];
			scrittore w = {testa_corpo, sizeof testa_corpo, 0, false};

			sc_u32(&w, trasf);
			if (w.pieno)
				return true;
			if (manda_appunti(s, T_APPUNTI_TESTO, testa_corpo, w.len,
			                  s->app_testo, s->app_testo_n)) {
				s->app_serviti++;
				reg(s, "⭐ APPUNTI §7.4: sent %zu bytes to the client "
				       "(transfer %u)",
				    s->app_testo_n, trasf);
			}
		}
		return true;
	}
	case T_APPUNTI_TESTO: {
		const char *testo;
		size_t byte;

		trasf = le_u32(&l);
		if (l.corto)
			return true;
		testo = (const char *)corpo + A_TESTO_MINIMO;
		byte = lung - A_TESTO_MINIMO;

		/* ⛔ §7.4: «an `APPUNTI_TESTO` nobody asked for is
		 *    `ERRORE_PROTOCOLLO`: the clipboard is pulled, not pushed». */
		if (s->app_serial_n == 0) {
			viola_appunti(s, "APPUNTI_TESTO (transfer %u, %zu bytes) that "
			                 "nobody asked for: §7.4 — the clipboard is "
			                 "pulled, not pushed",
			              trasf, byte);
			return false;
		}
		/* ⛔⛔⭐ AND HERE THE SESSION WAS CLOSED FOR A NORMAL RACE — the same
		 *      line, with the same mistake, that on 20 Aug 2026 in the PAGE
		 *      produced «Firefox got stuck with the clipboard».
		 *
		 * ⚠ The comparison was with the LIVE announcement: if between our
		 *   question and its answer the client announced again (two copies in a
		 *   millisecond — `[M]`, it happens), the answer carries the OLD number
		 *   by construction, and §7.4 says it is served with the current text and
		 *   **is not an error**.  ⇒ One compares with what one ASKED FOR. */
		if (trasf != s->app_chiesto_id && trasf != s->app_suo_id) {
			viola_appunti(s, "APPUNTI_TESTO for transfer %u, which I never "
			                 "asked for (I asked for %u, the live announcement "
			                 "is %u): §7.4 — the clipboard is pulled, "
			                 "not pushed",
			              trasf, s->app_chiesto_id, s->app_suo_id);
			return false;
		}
		if (trasf != s->app_suo_id)
			reg(s, "⚠ APPUNTI §7.4: the text of transfer %u arrives when "
			       "the live announcement is %u: it is the normal race between two "
			       "people copying, and the text is the CURRENT one",
			    trasf, s->app_suo_id);
		/* ⛔ And the announcement said how many bytes: if the text carries a
		 *    different number, one of the two messages lies.  §6.1 — «a length
		 *    inconsistent with what the type foresees».  ⚠ Here the expected
		 *    length does not come from the type, it comes from the announcement
		 *    of the same side: it is the same rule applied to a promise the
		 *    client made itself. */
		/* ⚠ And the size is demanded ONLY on the live transfer: on a
		 *   superseded one the client served the text of NOW, which is not the
		 *   one announced back then — demanding the old length would refuse
		 *   precisely what the exception allows. */
		if (trasf == s->app_suo_id && byte != s->app_suo_len) {
			viola_appunti(s, "APPUNTI_TESTO carries %zu bytes and announcement "
			                 "%u declared %u (§7.4)",
			              byte, trasf, s->app_suo_len);
			return false;
		}
		/* ⛔ §5.4: «the text MUST be valid UTF-8».  ⚠ And it is validated HERE,
		 *    before letting it cross the process boundary: an invalid text
		 *    delivered to the compositor is a defect of OURS with the face of a
		 *    defect of the desktop. */
		if (!utf8_valido(testo, byte)) {
			viola_appunti(s, "APPUNTI_TESTO (transfer %u, %zu bytes) is not "
			                 "valid UTF-8, and §5.4 demands it",
			              trasf, byte);
			return false;
		}
		/* ⛔⭐ AND NO ZEROS IN THE MIDDLE — finding R9.11 applied to this channel.
		 *
		 *     `utf8_valido()` accepts it (`c < 0x80`), ⛔ but from here on the
		 *     text crosses a process boundary and reaches `appunti.c`, which
		 *     delivers it to the compositor.  ⚠ And the OPPOSITE direction
		 *     already refuses it (`appunti.c`, `leggi_il_testo`): accepting it
		 *     here would mean two different rules for the same quantity in the
		 *     two directions, that is a text that can be pasted into the desktop
		 *     and cannot be copied from inside.
		 * ⚠ And `testo_stampabile()` is NOT used, which would be the «ready
		 *   made» function: it also refuses `\n` and `\t`, ⛔ that is it would
		 *   refuse **any text copied from an editor**.  The right rule is
		 *   stricter than UTF-8 and wider than «printable». */
		if (memchr(testo, 0, byte)) {
			viola_appunti(s, "APPUNTI_TESTO (transfer %u, %zu bytes) carries "
			                 "a zero in the middle: what would be pasted "
			                 "would be shorter than what the announcement promised",
			              trasf, byte);
			return false;
		}

		s->app_ricevuti++;
		appunti_servi_in_attesa(s, testo, byte);
		return true;
	}

	default:
		/* ⛔ §7.4 defines THREE, and the high byte has already been recognised
		 *    as `0x02`: here we are on a clipboard channel type that does not
		 *    exist.  §3: it is not ignored. */
		viola_appunti(s, "type %#06x on the clipboard channel: §7.4 defines THREE "
		                 "— 0x0201 ANNUNCIO, 0x0202 CHIEDI, 0x0203 TESTO",
		              tipo);
		return false;
	}
}

/* The slot of this stream in the table, creating it if needed.  NULL = there
 * is no slot, and the caller has already sent the client away. */
static int appunti_posto(rcp_sessione *s, int64_t stream)
{
	int libero = -1;

	for (int i = 0; i < A_STREAM_MAX; i++)
		if (s->app_in[i].usato && s->app_in[i].stream == stream)
			return i;
	for (int i = 0; i < A_STREAM_MAX; i++)
		if (!s->app_in[i].usato) {
			libero = i;
			break;
		}
	/* ⛔ Full: the first one WITHOUT pending bytes is thrown away — an open and
	 *    empty stream takes nothing away from anyone — and ⛔ it is written to
	 *    the log, because §3 wants every tolerance to be visible. */
	if (libero < 0)
		for (int i = 0; i < A_STREAM_MAX; i++)
			if (s->app_in[i].testa_n == 0 && !s->app_in[i].corpo) {
				reg(s, "⚠ APPUNTI: %d streams open at once (§2.5 wants one "
				       "per transfer): I let go of %lld, which had no "
				       "pending bytes",
				    A_STREAM_MAX, (long long)s->app_in[i].stream);
				libero = i;
				break;
			}
	if (libero < 0) {
		/* ⛔ All halfway through a message: it is a client that opens streams and
		 *    does not finish them, and it is no longer a tolerance — it is §3. */
		viola_appunti(s, "%d clipboard streams open together and all halfway "
		                 "through a message: §2.5 wants one per transfer",
		              A_STREAM_MAX);
		return -1;
	}

	free(s->app_in[libero].corpo);
	memset(&s->app_in[libero], 0, sizeof s->app_in[libero]);
	s->app_in[libero].usato = true;
	s->app_in[libero].stream = stream;
	return libero;
}

static void appunti_posto_libera(rcp_sessione *s, int i)
{
	free(s->app_in[i].corpo);
	memset(&s->app_in[i], 0, sizeof s->app_in[i]);
}

bool rcp_ricevi_appunti(rcp_sessione *s, int64_t stream, const uint8_t *dati,
                        size_t len, bool fin, uint64_t ora)
{
	int i;

	if (!s)
		return false;
	if (s->stato == S_FINITA) {
		reg(s, "⛔ %zu bytes on clipboard stream %lld AFTER the end of the "
		       "session from %s: §4.2 forbids sending on any channel",
		    len, (long long)stream, s->provenienza);
		return false;
	}

	/* ⛔ §2.5, like input: nothing before `SESSIONE` has gone out. */
	if (!s->sessione_spedita) {
		viola_appunti(s, "bytes on the clipboard stream (%lld) before "
		                 "`SESSIONE` has gone out (state: %s)",
		              (long long)stream, NOMI_STATO[s->stato]);
		return false;
	}

	/* ⛔ §4.3: the client did not declare `appunti.testo`, and now it sends some.
	 *    ⚠ It is NOT a tolerance: it is a non-negotiated capability used all
	 *    the same, that is the case §4.3 exists to make impossible. */
	if (!s->negozia_appunti) {
		viola_appunti(s, "bytes on the clipboard channel from a client that "
		                 "did not declare `appunti.testo` in `CIAO` (§4.3)");
		return false;
	}

	s->ultimo_byte = ora;
	s->ultima_vita = ora;
	if (!torna_a_parlare(s))
		return false;

	i = appunti_posto(s, stream);
	if (i < 0)
		return false;

	while (len) {
		/* First the six framing bytes (§6.1), and one at a time if needed:
		 * a packet can cut them in the middle. */
		if (s->app_in[i].testa_n < 6) {
			size_t manca = 6 - s->app_in[i].testa_n;
			size_t quanti = len < manca ? len : manca;

			memcpy(s->app_in[i].testa + s->app_in[i].testa_n, dati, quanti);
			s->app_in[i].testa_n += quanti;
			dati += quanti;
			len -= quanti;
			if (s->app_in[i].testa_n < 6)
				break;

			{
				lettore intest = {s->app_in[i].testa, 6, 0, false};
				uint16_t tipo = le_u16(&intest);
				uint32_t lung = le_u32(&intest);
				uint32_t attesa_min, attesa_max;

				/* ⛔ §2.5: on this stream the high byte is 0x02. */
				if ((tipo >> 8) != 0x02) {
					viola_appunti(s, "type %#06x on the clipboard stream: the "
					                 "high byte 0x%02x is not the clipboard channel "
					                 "(§2.5)",
					              tipo, (unsigned)(tipo >> 8));
					return false;
				}
				/* ⛔ The length is validated BEFORE allocating — §6.1, and on the
				 *    three types of §7.4 one already knows what to expect: two have
				 *    a fixed size and the third has a minimum and a ceiling.
				 * ⭐ So whoever announces a megabyte on a `CHIEDI` does not get
				 *    a megabyte: it gets six bytes and a farewell. */
				switch (tipo) {
				case T_APPUNTI_ANNUNCIO:
					attesa_min = attesa_max = A_ANNUNCIO;
					break;
				case T_APPUNTI_CHIEDI:
					attesa_min = attesa_max = A_CHIEDI;
					break;
				case T_APPUNTI_TESTO:
					attesa_min = A_TESTO_MINIMO;
					attesa_max = A_TESTO_MINIMO + RCP_APPUNTI_TETTO;
					break;
				default:
					viola_appunti(s, "type %#06x on the clipboard channel: §7.4 "
					                 "defines THREE — 0x0201 ANNUNCIO, 0x0202 "
					                 "CHIEDI, 0x0203 TESTO",
					              tipo);
					return false;
				}
				if (lung < attesa_min || lung > attesa_max) {
					viola_appunti(s, "message %#06x announces %u body bytes "
					                 "and §7.4 wants between %u and %u: %s",
					              tipo, lung, attesa_min, attesa_max,
					              lung < attesa_min
					                  ? "MISSING bytes"
					                  : "EXTRA bytes — and beyond the ceiling of §5.4 "
					                    "the text is not announced at all");
					return false;
				}
				s->app_in[i].tipo = tipo;
				s->app_in[i].lung = lung;
				s->app_in[i].corpo_n = 0;
				if (lung) {
					s->app_in[i].corpo = (uint8_t *)malloc(lung);
					if (!s->app_in[i].corpo) {
						reg(s, "⛔ APPUNTI: %u bytes of body do not fit in "
						       "memory: I throw the message away and close the stream",
						    lung);
						appunti_posto_libera(s, i);
						return true;
					}
				}
			}
		}

		/* Then the body. */
		{
			size_t manca = s->app_in[i].lung - s->app_in[i].corpo_n;
			size_t quanti = len < manca ? len : manca;

			if (quanti) {
				memcpy(s->app_in[i].corpo + s->app_in[i].corpo_n, dati, quanti);
				s->app_in[i].corpo_n += quanti;
				dati += quanti;
				len -= quanti;
			}
			if (s->app_in[i].corpo_n < s->app_in[i].lung)
				break;
		}

		{
			uint16_t tipo = s->app_in[i].tipo;
			uint32_t lung = s->app_in[i].lung;
			uint8_t *corpo = s->app_in[i].corpo;
			bool vivo;

			/* ⛔ The slot is reset BEFORE handling the message: `tratta_
			 *    appunti` can send (and so re-enter this module), and a slot
			 *    left half full would be a state nobody knows any more whom it
			 *    belongs to.  ⚠ `corpo` stays valid: the memory is ours until
			 *    we free it three lines further down. */
			s->app_in[i].corpo = NULL;
			s->app_in[i].corpo_n = 0;
			s->app_in[i].testa_n = 0;
			s->app_in[i].lung = 0;

			vivo = tratta_appunti(s, tipo, corpo, lung);
			free(corpo);
			if (!vivo)
				return false;
		}
	}

	/* ⛔ §6.1 and §2.5: a stream that ends halfway through a message does not
	 *    carry a short message — it carries a length that does not add up.
	 *    ⚠ And here the client is NOT sent away: the half message has not done
	 *    anything yet, and closing the session for a truncated stream would also
	 *    punish the client whose network dropped halfway through a transfer.
	 *    ⇒ It is declared and thrown away — and it is a WRITTEN tolerance (§3). */
	if (fin) {
		if (s->app_in[i].testa_n || s->app_in[i].corpo)
			reg(s, "⚠ APPUNTI: stream %lld ended with a message halfway "
			       "(%zu header bytes, %zu of body out of %u): it is thrown away.  "
			       "I do not send the client away — a truncated transfer is not a "
			       "client making a mistake",
			    (long long)stream, s->app_in[i].testa_n, s->app_in[i].corpo_n,
			    s->app_in[i].lung);
		appunti_posto_libera(s, i);
	}
	return true;
}

/* ⛔ §5.2 and §7.1 — `RICHIEDI_CHIAVE`, served since 12 Aug 2026.
 *
 * ⚠ Until today this type fell into the `default` of the switch and made a
 *   conforming client that had seen a gap **lose the session**: the log
 *   declared it («phase 1 does not serve it yet»), and the price was
 *   declared but real.  With the video channel that price can no longer be
 *   paid, because §5.2 obliges the client to send it.
 *
 * ⛔ And the CLOCK COUNTS FROM THE LAST KEYFRAME SENT, not from the last request
 *    received: «counting from requests, two insistent clients push the clock
 *    forward forever and the keyframe never leaves».                        */
static bool tratta_richiedi_chiave(rcp_sessione *s, lettore *l, uint64_t ora)
{
	uint32_t ultimo = le_u32(l);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "RICHIEDI_CHIAVE without `ultimo_numero`");
		return false;
	}
	/* §5.2: it is served only with the session open — before there are no
	 * frames to notice anything about. */
	if (!s->sessione_spedita) {
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "RICHIEDI_CHIAVE before SESSIONE: there is no frame");
		return false;
	}
	/* ⛔ §7.1: «`ultimo_numero`: the last decoded frame, **0 if
	 * none**».  It is the meaning P2 reserved for zero in §6.2: here it is
	 * read, not guessed. */
	/* ⛔⛔ 22 Sep 2026 — THE GRACE IS FOR DUPLICATES, not for new gaps.
	 *     A request with `ultimo_numero` equal to or newer than the last
	 *     keyframe sent says the client has ALREADY decoded that keyframe: the
	 *     gap came afterwards, and ignoring it leaves it frozen forever (the
	 *     page does not ask for a second one for the same gap).
	 *     `[M]` Firefox on KDE, heavy video: «ignored — 157 ms» with
	 *     `ultimo_numero` = the keyframe just arrived, and the page frozen
	 *     until the line died.  ⚠ Comparison in serial-number arithmetic: the
	 *     `numero` of §6.2 wraps around. */
	bool gia_vista = (int32_t)(ultimo - s->ultima_chiave_numero) >= 0;
	if (!s->mai_spedita_una_chiave && !gia_vista &&
	    ora - s->ultima_chiave_ms < V_GRAZIA_CHIAVE) {
		/* ⛔ §3: «every tolerance must be written to the log.  A silent
		 * tolerance is indistinguishable from a defect».  It is exception 5. */
		reg(s, "⚠ DECLARED TOLERANCE (§3 exception 5, §5.2): "
		       "RICHIEDI_CHIAVE(ultimo_numero=%u) ignored — %llu ms have "
		       "passed since the last KEYFRAME sent, fewer than the %d allowed",
		    ultimo, (unsigned long long)(ora - s->ultima_chiave_ms),
		    V_GRAZIA_CHIAVE);
		return true;
	}
	reg(s, "RICHIEDI_CHIAVE(ultimo_numero=%u) accepted (§5.2): the next "
	       "frame will be a KEYFRAME — last one sent by us: %u",
	    ultimo, s->video_numero);
	chiave_serve(s, "the client asked for one (§5.2)");
	return true;
}

/* ------------------------------------------------------------------------ */
/* ⭐ §7.5 — THE BENCH FUNCTION, AND THE CASE THAT MUST NOT BRING ANYTHING DOWN
 *
 * ⛔ This is the only control channel message to which a conforming server
 *    answers **by refusing without closing**.  The two rules:
 *
 *    rule 2    off -> `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`.  ⛔ It MUST
 *              NOT stay silent and MUST NOT close: «a client asking for a
 *              function that is off has violated nothing», and a silence leaves
 *              the phase 3 bench waiting forever — the symptom would be
 *              «the bench got stuck», which names neither the function nor
 *              the switch;
 *    rule 4    `ritardo_ms` outside 0..10 000 -> `RITARDO_FUORI_LIMITI`, and
 *              ⛔ **not** `ERRORE_PROTOCOLLO`: bringing down the session of the
 *              bench being calibrated is the same bad idea §7.1 avoids for
 *              out-of-limit sizes.
 *
 * ⚠ And the ORDER between the two `RCP.md` does not say: with the function off
 *   AND the delay out of limits, the defensible reasons are two.  ⭐ Here the
 *   parameter is checked FIRST, because it is the one the bench can correct:
 *   telling it «off» when it also got the number wrong makes it switch the
 *   function on and find the same refusal, with a different reason, at the
 *   second round.  The choice is declared in `FASI.md` §01-filo-nudo.
 *
 * ⛔ Rule 5: every `BANCO_MARCA` is written to the log — refusals too.
 *    «A session that paints coloured squares on a person's desktop must be
 *    able to prove it from the log.» */
static bool tratta_banco_marca(rcp_sessione *s, lettore *l)
{
	uint32_t id = le_u32(l), colore = le_u32(l), ritardo = le_u32(l);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "BANCO_MARCA truncated");
		return false;
	}
	/* ⛔ §7.5: «0 is reserved».  A zero id is not a wrong bench parameter,
	 * it is a malformed message: here the session drops.
	 * ⚠ Our choice — the document says «reserved» and does not say the outcome. */
	if (id == 0) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "BANCO_MARCA with id 0, which is reserved");
		return false;
	}

	uint8_t esito = BANCO_RIFIUTATA, motivo;
	if (ritardo > BANCO_RITARDO_MAX) {
		motivo = BANCO_RITARDO_FUORI_LIMITI;
	} else if (!BANCO_ACCESO) {
		motivo = BANCO_FUNZIONE_SPENTA;
	} else {
		/* In phase 1 there is no frame to paint on: the function stays off,
		 * and this branch exists so as not to forget that switching it on
		 * must be written to the log (rule 5). */
		esito = BANCO_ACCETTATA;
		motivo = 0;
	}
	reg(s, "BANCO_MARCA id=%u colore=%#08x ritardo=%u ms -> %s motivo=%u",
	    id, colore, ritardo,
	    esito == BANCO_ACCETTATA ? "ACCETTATA" : "RIFIUTATA", motivo);

	uint8_t corpo[32];
	scrittore w = {corpo, sizeof corpo, 0, false};
	sc_u32(&w, id);
	sc_byte(&w, esito);
	sc_byte(&w, motivo);
	/* ⛔ `istante`: 0 if refused, «and it is the only meaning of *absent*
	 * for this field» (§6.0). */
	for (int i = 0; i < 8; i++)
		sc_byte(&w, 0);
	if (!w.pieno)
		manda_messaggio(s, T_BANCO_ESITO, corpo, w.len);
	/* ⭐ And the session STAYS OPEN. */
	return true;
}

/* ------------------------------------------------------------------------ */
rcp_sessione *rcp_apri(const rcp_ganci *g, const char *provenienza,
                       uint64_t ora_ms)
{
	rcp_sessione *s = (rcp_sessione *)calloc(1, sizeof *s);
	if (!s)
		return NULL;
	s->g = *g;
	s->stato = S_ATTESA_CIAO;
	s->da_quando = ora_ms;
	s->ultimo_byte = ora_ms;
	/* ⛔ And THIS too starts from now, not from zero: a session just
	 *    opened has not yet seen a packet pass through the hands of this
	 *    module, and a zero would make it detach for silence at the first round. */
	s->ultima_vita = ora_ms;
	snprintf(s->provenienza, sizeof s->provenienza, "%s",
	         provenienza ? provenienza : "?");
	rcp_chiave_indirizzo(s->provenienza, s->indirizzo, sizeof s->indirizzo);
	reg(s, "control channel opened from %s (address for §4.4-bis: %s)",
	    s->provenienza, s->indirizzo);
	/* ⛔ §7.5 rule 5 and §4.3: «a server that declared it `si` by mistake
	 * writes it to the log at every startup».  This module has no startup — it
	 * opens no socket and reads no configuration — and the first moment it sees
	 * is the opening of a channel: the line sits here (finding R9.14).  ⚠ Whoever
	 * diagnoses a coloured square on someone's desktop must be able to trace
	 * back to the line saying the function was on. */
	if (BANCO_ACCESO)
		reg(s, "⛔ the BENCH FUNCTION is ON (§7.5): this server accepts "
		       "BANCO_MARCA and paints over the desktop, and `ECCOMI` declares "
		       "banco.marca=si");
	return s;
}

void rcp_libera(rcp_sessione *s)
{
	if (!s)
		return;
	/* ⛔ §7.3 — the last of the roads, and the safety net of all the others:
	 * whatever happened, one passes through here.  ⚠ `inp_rilasciato` alone
	 * prevents releasing twice. */
	rilascia_al_distacco(s, "the session is being freed");
	/* ⛔ §6.2 — A VIDEO STREAM LEFT HALFWAY IS RESET, NOT ABANDONED TO THE
	 * TRANSPORT.  A frame open when the session ends is by definition
	 * incomplete: resetting it says so, and it is the only closing that means
	 * «throw it away».  ⚠ And one goes through the hook, not through
	 * `rcp_video_abbandona()`: that one refuses keyframes (§5.2) and is right
	 * while the session lives — here there is nothing left to protect, and a
	 * keyframe left open would stay open forever. */
	if (s->video_aperto && s->g.video_azzera) {
		s->g.video_azzera(s->g.ctx, s->video_stream);
		s->video_aperto = false;
		reg(s, "⚠ frame %u was still open at the end of the session: "
		       "stream %lld RESET (§6.2), %zu bytes out of %zu",
		    s->video_suo_numero, (long long)s->video_stream, s->video_scritti,
		    s->video_da_scrivere);
	}
	if (s->attaccata) {
		posto_lascia(s->utente);
		reg(s, "slot LEFT by %s via %s (taken now: %d)", s->utente,
		    s->provenienza, posti_occupati());
	}
	/* ⛔ The buffer is zeroed BEFORE freeing it — finding R9.8.  The
	 * `CREDENZIALI` passed through it, and on every road that sends the client
	 * away before consuming the message the password in clear is still there.
	 * `free()` zeroes nothing: those bytes ended up in the freed heap,
	 * available to any later allocation of a process that serves ALL the
	 * users of the machine (`SPECIFICHE.md` §5.5). */
	if (s->acc) {
		memset(s->acc, 0, s->acc_cap);
		free(s->acc);
	}
	/* ⛔⭐ AND THE CLIPBOARD IS FREED HERE, both sides.
	 *
	 * ⛔ And it is ZEROED first, like the buffer and for a reason of the same
	 *    family: what the user copies is often precisely what they would not
	 *    want to leave lying around — a password pasted from a credential
	 *    manager passes **whole** through this buffer.  ⚠ `free()` zeroes
	 *    nothing, and this process serves ALL the users of the machine
	 *    (`SPECIFICHE.md` §5.5). */
	if (s->app_testo) {
		memset(s->app_testo, 0, s->app_testo_n);
		free(s->app_testo);
	}
	for (int i = 0; i < A_STREAM_MAX; i++)
		if (s->app_in[i].corpo) {
			memset(s->app_in[i].corpo, 0, s->app_in[i].lung);
			free(s->app_in[i].corpo);
		}
	memset(s, 0, sizeof *s);
	free(s);
}

bool rcp_e_finita(const rcp_sessione *s) { return s && s->stato == S_FINITA; }

/* ⛔⭐ §4.2 — THE SESSION IS OVER BECAUSE THE CLIENT SAYS SO, AND THE SLOT IS
 * LEFT NOW, NOT WHEN THE TRANSPORT HAS FINISHED TAKING ITSELF DOWN.
 *
 * The client closes the WebTransport session with a capsule carrying the
 * reason (§3.1 point 3).  ⚠ Waiting for the streams to close before freeing the
 * slot (§8.2 reason 0x0F) means keeping it taken for the whole time of the
 * teardown — and whoever reconnects **at once** is told there is already a
 * session.
 *
 * ⭐ Found by B11 on 10 Aug 2026: two consecutive cases, the second
 *    refused with `GIA_ATTIVA_REMOTA` because the first had not yet finished
 *    leaving.  ⛔ On the bench it is a red case now and then; for whoever uses
 *    the product it is «it tells me I am already connected, and it is not true». */
void rcp_chiusa_dal_client(rcp_sessione *s, uint8_t codice)
{
	/* ⚠ No guard on the state: the slot is left even if the session had
	 *   already ended by another road — `attaccata` alone prevents leaving it
	 *   twice, and it is the only thing that matters. */
	if (!s)
		return;
	reg(s, "the page closed the session, reason %#04x: §4.2, the session "
	       "is over (state: %s)",
	    codice, NOMI_STATO[s->stato]);
	/* ⛔ §7.3: the third road — the page leaves without going through
	 * `congeda()`.  A browser closed with the little cross arrives here. */
	rilascia_al_distacco(s, "the page closed the session");
	if (s->attaccata) {
		posto_lascia(s->utente);
		s->attaccata = false;
		reg(s, "slot LEFT by %s via %s (taken now: %d)", s->utente,
		    s->provenienza, posti_occupati());
	}
	s->stato = S_FINITA;
}

const char *rcp_stato_nome(const rcp_sessione *s)
{
	return s ? NOMI_STATO[s->stato] : "?";
}

const char *rcp_utente(const rcp_sessione *s) { return s ? s->utente : ""; }

/* ⛔⭐ THE DECODER CEILING, BROUGHT OUTSIDE — phase 10, 25 Aug 2026.
 *
 *     `max_l`/`max_a` had existed since 10 August (finding B-1) and served ONE
 *     thing only: not granting a canvas the client cannot decode
 *     (§4.5).  ⭐ The budget needs them for another: it is the **upper bound of
 *     the cost** of whoever is knocking, and it is known from `CIAO` on — that
 *     is long before the canvas is decided.  ⇒ No new field, no new channel:
 *     only an accessor.
 *
 * ⚠ `false` = «the client did not declare it», and it is a fact different from
 *   «zero» (§4.5 constrains the granted canvas **only if the client declared it**). */
bool rcp_misura_massima(const rcp_sessione *s, uint32_t *l, uint32_t *a)
{
	if (!s || !s->max_l || !s->max_a)
		return false;
	if (l)
		*l = s->max_l;
	if (a)
		*a = s->max_a;
	return true;
}

/* ⛔⭐ §5.3 — «THE CLIENT IS STILL THERE», and the TRANSPORT says so, not RCP.
 *
 *     `trasporto.c` calls it after every packet `ngtcp2_conn_read_pkt()`
 *     has accepted: that is **decrypted and authenticated**.  ⛔ It is not
 *     enough for a UDP datagram to arrive — anyone can send one with someone
 *     else's address, and would keep someone else's slot taken.
 *
 * ⭐ It is the only sign of life that exists when the user watches and does not
 *    touch, and it is the RIGHT one: in the test of 16 August the wire was cut at
 *    13:33:13 and this clock declared it at 13:33:43 — **thirty seconds
 *    flat**, while the RCP bytes clock had declared it 36 seconds EARLIER, and
 *    wrongly.
 *
 * ⚠ No new message, no heartbeat to add to the page: the signal was already
 *   there and nobody passed it through here. */
void rcp_segno_di_vita(rcp_sessione *s, uint64_t ora_ms)
{
	if (!s || s->stato == S_FINITA)
		return;
	/* ⛔⭐⭐ AND THE GAP BETWEEN TWO PACKETS IS WATCHED, because this repair
	 *      RESTS ON AN ASSUMPTION: that between one packet and the next less
	 *      than the ceiling of §5.3 passes.
	 *
	 * ⛔ Nobody guarantees it.  The transport PINGs are on ONLY in the
	 *    credentials window, and for a written reason (`webtransport.c`,
	 *    `regola_tienila_viva()`: keeping them always on would change the
	 *    meaning of the 30 s of §2.2).  ⇒ During the session packets arrive
	 *    because SOMETHING moves — frames, cursor, acknowledgements — and on a
	 *    still scene with nobody touching anything it is not certain that
	 *    something moves often enough.
	 *
	 * ⚠ So when the gap exceeds HALF the ceiling it is WRITTEN.  It is the only
	 *   way to see the day COMING when it is no longer enough, instead of
	 *   discovering it from a user thrown out while reading — that is not to
	 *   redo, in the cure, the defect the cure came to remove: a protection
	 *   resting on something nobody can look at.
	 *
	 * ⛔⭐ `[M]` AND AT THE FIRST RUN THIS LINE ALREADY SPOKE, 16 Aug 2026:
	 *      session still for 260 s, the slot held — ⛔ but the gap between two
	 *      packets is **15004, 15005, 15002 ms**, that is EXACTLY FIFTEEN
	 *      SECONDS, a clean half of the ceiling.
	 *
	 *      ⇒ The margin is 2x, and it is very regular because it is NOT OURS: it
	 *      is the browser's keep-alive.  ⚠ A different browser, or Chrome
	 *      changing that number, and slots start dropping again.  ⛔ The real
	 *      cure — sending PINGs even with the session active — is a DECISION,
	 *      not a repair: it changes the meaning of the 30 s of §2.2 for the
	 *      FROZEN tab, which `SPECIFICHE.md` §5.3 says must be detached.  It is
	 *      written in `FASI.md` §05-la-sessione §6-bis and waits for the user. */
	if (ora_ms > s->ultima_vita && ora_ms - s->ultima_vita > SILENZIO / 2)
		reg(s, "⚠ §5.3: between two packets from %s %llu ms have passed, and the "
		       "silence ceiling is %u — the margin is getting thin",
		    s->provenienza, (unsigned long long)(ora_ms - s->ultima_vita),
		    (unsigned)SILENZIO);
	s->ultima_vita = ora_ms;
}

/* ⛔ The buffer grows on demand up to the ceiling of §6.1 (see MAX_ACCUMULO).
 *
 * ⚠ And `realloc` is NOT used: that buffer contains the `CREDENZIALI` in clear,
 *   and a `realloc` that moves leaves the old copy in the heap without zeroing
 *   it — that is it would put back the defect R9.8 came to remove.  One
 *   allocates, copies, ZEROES the old one, frees.
 *
 * Returns: 1 done · 0 does not fit (the caller sends the client away) · -1 memory. */
static int accumula(rcp_sessione *s, const uint8_t *dati, size_t n)
{
	if (s->acc_len + n > MAX_ACCUMULO)
		return 0;
	if (s->acc_len + n > s->acc_cap) {
		size_t nuova = s->acc_cap ? s->acc_cap : 8192u;
		while (nuova < s->acc_len + n)
			nuova *= 2;
		if (nuova > MAX_ACCUMULO)
			nuova = MAX_ACCUMULO;
		uint8_t *p = (uint8_t *)malloc(nuova);
		if (!p)
			return -1;
		if (s->acc) {
			memcpy(p, s->acc, s->acc_len);
			memset(s->acc, 0, s->acc_cap);
			free(s->acc);
		}
		s->acc = p;
		s->acc_cap = nuova;
	}
	memcpy(s->acc + s->acc_len, dati, n);
	s->acc_len += n;
	return 1;
}
/* ⛔⭐ HOW LONG THE FIELDS OF THIS TYPE ARE — finding R9.4, and the defect was
 *    the ORDER, not the check.
 *
 * §6.1: «a receiver that reads a length inconsistent with what the type
 * foresees MUST close with `ERRORE_PROTOCOLLO`», and §3: «MUST NOT carry on».
 * The check `l.i != lung` was there, and it was written right — but it sat AFTER
 * `avanti = tratta_*()`, that is after the message had been executed in
 * full, with all its effects on the wire and on the state:
 *
 *   a `CIAO` with four padding bytes at the tail — the
 *   `lunghezza-in-piu` case of B5 — received `ECCOMI` and ONLY THEN the farewell;
 *   an `ATTACCA` with one byte at the tail took the slot, sent `SESSIONE`,
 *   wrote «session open» and then sent the client away: on the wire, in this
 *   order, `SESSIONE` and `CONGEDO(0x0B)`.  ⛔ A client that has received
 *   `SESSIONE` is authorised by §2.5 to open its input stream, and it opened it
 *   on a session that was dying;
 *   a `CREDENZIALI` with one byte at the tail made PAM be queried and MOVED the
 *   counters of §4.4-bis — that is precisely the property B5 checks with
 *   `malformati-non-contano`, and it checked it on the other half of the
 *   malformed ones.
 *
 * ⚠ This function is a SECOND reader of the same fields, and the two can
 *   drift apart: whoever changes a body in `tratta_*()` changes it here too.  The
 *   check that remains AFTER the switch is not a duplicate — it is what
 *   notices.
 *
 * ⭐ And it returns `false` when the body is SHORTER than the fields: that case
 *    it leaves to `tratta_*()`, which can say which field was missing.  §3.1
 *    point 1 wants «what» was not understood, and «CIAO senza versione» is worth
 *    more than «the length does not add up». */
static bool misura_campi(uint16_t tipo, const uint8_t *corpo, uint32_t lung,
                         size_t *quanti)
{
	lettore l = {corpo, lung, 0, false};
	char buf[1025];
	switch (tipo) {
	case T_CIAO: {
		le_u16(&l);
		uint16_t quante = le_u16(&l);
		for (uint16_t k = 0; k < quante && !l.corto; k++) {
			le_str(&l, buf, sizeof buf);
			le_str(&l, buf, sizeof buf);
		}
		break;
	}
	case T_CREDENZIALI:
		le_str(&l, buf, sizeof buf);
		le_str(&l, buf, sizeof buf);
		break;
	case T_ATTACCA:
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		le_str(&l, buf, sizeof buf);
		break;
	case T_BANCO_MARCA:
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		break;
	case T_CONGEDO:
		le_u8(&l);
		le_str(&l, buf, sizeof buf);
		break;
	/* §7.1: `RICHIEDI_CHIAVE` ├── u32 ultimo_numero.  Four bytes, and not one
	 * more: a longer body is `ERRORE_PROTOCOLLO` as for the others
	 * (§6.1), and this line is what makes it happen. */
	case T_RICHIEDI_CHIAVE:
		le_u32(&l);
		break;
	/* ⭐ §7.6: `TERMINA_SESSIONE` has an EMPTY body — there is nothing to say
	 * beyond the fact.  ⚠ And a longer body is `ERRORE_PROTOCOLLO` as for
	 * all the others (§6.1): not «whatever is left over is ignored». */
	case T_TERMINA_SESSIONE:
		break;
	/* ⛔⭐⭐ `ADATTA_TELA` AND `VISTA` — two `u32` each (§7.1), and BOTH were
	 *      MISSING: 16 Aug 2026, bench `06-b36` case 20.
	 *
	 * ⚠ It is **R9.4 again**, on the most recent message: the comment at the top
	 *   of this function tells the defect — «an `ATTACCA` with one byte at the
	 *   tail took the slot, sent `SESSIONE` and THEN sent the client away» — and
	 *   `ADATTA_TELA`, served on 14 August, never entered the list.
	 *
	 * ⛔ The price `[M]`: a 12-byte `ADATTA_TELA` fell into the `default`,
	 *    this function returned `false` (that is «I do not judge it»), the
	 *    `T_ADATTA_TELA` branch passed the request to the stage **in full** and
	 *    only the check `l.i != lung` AFTER the switch sent the client away.  ⇒
	 *    On the wire a `TELA` and then a `CONGEDO`, and on the compositor a real
	 *    resize — which restarts the PipeWire stream and on Mutter destroys and
	 *    recreates the `libei` devices.  §3: «MUST NOT carry on».
	 *
	 * ⚠ `VISTA` comes in here together because it comes into the switch
	 *   together: whoever adds a type and does not add its line here reopens the
	 *   same hole. */
	case T_ADATTA_TELA:
	case T_VISTA:
		le_u32(&l);
		le_u32(&l);
		break;
	default:
		/* a type we will not get to handle anyway: the switch decides, and
		 * its log line is more precise than this one */
		return false;
	}
	if (l.corto)
		return false;
	*quanti = l.i;
	return true;
}

/* Has the wire stopped at the boundary between two messages?  It serves
 * `giudica_dopo_la_fine()`: if the server closed while a body was halfway,
 * the bytes arriving afterwards do NOT start with a header, and reading them
 * as such means giving a name to two body bytes. */
static bool a_confine(const rcp_sessione *s)
{
	if (s->acc_len == 0)
		return true;
	if (s->acc_len < 6)
		return false;
	lettore l = {s->acc, s->acc_len, 0, false};
	le_u16(&l);
	uint32_t lung = le_u32(&l);
	return s->acc_len >= 6u + (size_t)lung;
}

/* ⛔⭐ AFTER THE END ONE JUDGES ON MESSAGES, NOT ON THE FIRST SIX BYTES OF THE
 *    PIECE — finding R9.15.
 *
 * §4.4 forbids the client ONE thing: **retrying**.  §8.1 imposes another:
 * whoever closes MUST send `CONGEDO` with the reason.  ⭐ The two meet when
 * the server errs AFTER `RESPINTO` — the `respinto-poi-congedo` case of B11: the
 * page sees a message that should not have arrived, closes as §3 requires, and
 * its `CONGEDO` leaves when for us the session is already over.
 *
 * ⚠ On 10 Aug 2026 that 69-byte `CONGEDO` was counted as «sent after the
 *   end», and the red went to the page that was doing exactly what §8.1
 *   requires of it.  ⛔ The cure of that day however read **the first two bytes
 *   of `dati`** and acquitted the WHOLE piece: whoever wrote in a single go
 *   `CONGEDO` **plus** a second `CREDENZIALI` walked away with the
 *   acquittal, and the violation B11 exists to accuse appeared in no line.
 *   The false red had become a false green, which is the same shape — and the
 *   document one relies on, §4.4, speaks of MESSAGES. */
static void giudica_dopo_la_fine(rcp_sessione *s, const uint8_t *dati,
                                 size_t len)
{
	if (!a_confine(s)) {
		reg(s, "⚠ %zu bytes arrived AFTER the end of the session from %s, and they "
		       "CANNOT be judged: the wire had stopped halfway through a body, "
		       "so these bytes do not start with a header",
		    len, s->provenienza);
		return;
	}
	size_t off = 0;
	int quanti = 0;
	uint16_t primo = 0;
	while (off + 6 <= len) {
		lettore l = {dati + off, len - off, 0, false};
		uint16_t tipo = le_u16(&l);
		uint32_t lung = le_u32(&l);
		if (lung > MAX_CORPO || (size_t)6 + lung > len - off)
			break; /* the last one is truncated: `off < len` will say so */
		if (quanti == 0)
			primo = tipo;
		quanti++;
		off += 6 + lung;
	}
	if (quanti == 1 && primo == T_CONGEDO && off == len) {
		reg(s, "⭐ parting CONGEDO from %s with the session already over: §8.1 "
		       "REQUIRES it of whoever closes, and §4.4 forbids attempts, not partings "
		       "— %zu bytes, a single message, and they are not too many",
		    s->provenienza, len);
		return;
	}
	if (quanti >= 1 && primo == T_CONGEDO) {
		reg(s, "⛔ from %s a parting CONGEDO AND THEN something else: %d messages "
		       "in %zu bytes (%zu bytes beyond the last whole one).  §8.1 requires "
		       "the parting, §4.4 forbids everything else",
		    s->provenienza, quanti, len, len - off);
		return;
	}
	reg(s, "⛔ %zu bytes arrived AFTER the end of the session from %s: %d whole "
	       "messages, the first of type %#06x",
	    len, s->provenienza, quanti, primo);
}

/* Extracts from the buffer all the whole messages that are there.  `false` = the
 * session is over, and the caller must not buffer anything else. */
static bool drena(rcp_sessione *s, uint64_t ora)
{
	for (;;) {
		if (s->acc_len < 6)
			return true;
		lettore intest = {s->acc, s->acc_len, 0, false};
		uint16_t tipo = le_u16(&intest);
		uint32_t lung = le_u32(&intest);
		/* ⛔ The length is checked BEFORE allocating: whoever allocates and then
		 * checks has already given a megabyte to anyone who can write six bytes. */
		/* ⛔ And the ceiling belongs to the MESSAGE, framing included (§6.1 read
		 * together with §5.4) — finding B-14: here `lung` is the BODY, and the
		 * longest body allowed is `MAX_MESSAGGIO - 6`. */
		if (lung > MAX_CORPO) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "message over 1 MiB");
			return false;
		}
		if (s->acc_len < 6u + lung)
			return true; /* the body has not all arrived */

		/* §2.5: on the control channel the high byte of the type is 0x00. */
		if ((tipo >> 8) != 0x00) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "high byte of the type is not control");
			return false;
		}
		/* ⛔ AND HERE, BEFORE ANY EFFECT: the declared length must be the one of
		 * the type's fields (§6.1).  See `misura_campi()`. */
		size_t attesa = 0;
		if (misura_campi(tipo, s->acc + 6, lung, &attesa) && attesa != lung) {
			char d[128];
			snprintf(d, sizeof d,
			         "type %#06x: the length declares %u bytes and the "
			         "fields the type expects take %zu",
			         tipo, lung, attesa);
			congeda(s, RCP_ERRORE_PROTOCOLLO, d);
			return false;
		}
		lettore l = {s->acc + 6, lung, 0, false};
		bool avanti = true;
		switch (tipo) {
		case T_CIAO:
			if (s->stato != S_ATTESA_CIAO) {
				congeda(s, RCP_ERRORE_PROTOCOLLO, "CIAO in the wrong state");
				return false;
			}
			avanti = tratta_ciao(s, &l);
			break;
		case T_CREDENZIALI:
			if (s->stato != S_ATTESA_CREDENZIALI) {
				congeda(s, RCP_ERRORE_PROTOCOLLO, "CREDENZIALI in the wrong state");
				return false;
			}
			avanti = tratta_credenziali(s, &l, ora);
			break;
		case T_ATTACCA:
			if (s->stato != S_ATTESA_ATTACCA) {
				congeda(s, RCP_ERRORE_PROTOCOLLO, "ATTACCA in the wrong state");
				return false;
			}
			avanti = tratta_attacca(s, &l, ora);
			break;
		case T_BANCO_MARCA:
			/* §7.5: the mark is painted on a frame, and frames
			 * start with `SESSIONE`.  Before, it is a message in the wrong
			 * state like all the others. */
			if (s->stato != S_ATTIVA) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "BANCO_MARCA in the wrong state");
				return false;
			}
			avanti = tratta_banco_marca(s, &l);
			break;
		case T_RICHIEDI_CHIAVE:
			/* ⛔ §5.2: a keyframe is asked for because there is a gap between
			 * frames, and frames start with `SESSIONE`.  Before, it is a
			 * message in the wrong state like all the others (§1, §3).
			 * ⚠ `S_STACCATA` is fine: that session sent `SESSIONE` long
			 *   ago, it only left the slot for silence (R9.2) — and refusing
			 *   it a keyframe would be punishing the client for a ceiling
			 *   of the server. */
			if (s->stato != S_ATTIVA && s->stato != S_STACCATA) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "RICHIEDI_CHIAVE in the wrong state");
				return false;
			}
			avanti = tratta_richiedi_chiave(s, &l, ora);
			break;
		case T_TERMINA_SESSIONE:
			/*
			 * ⭐⭐ §7.6 — «I AM DONE», and it is the other exit of
			 *     `DECISIONI.md` §4.1-ter.
			 *
			 * ⛔ ONLY WITH THE SESSION ATTACHED: before `ATTACCA` there is no
			 *    graphical session to end, and §3 makes no allowances.
			 * ⚠ `S_STACCATA` is fine for the same reason as
			 *   `RICHIEDI_CHIAVE`: that client has the session, it only
			 *   left the slot for silence.
			 */
			if (s->stato != S_ATTIVA && s->stato != S_STACCATA) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "TERMINA_SESSIONE in the wrong state");
				return false;
			}
			reg(s, "⭐ §7.6: %s asked to LEAVE — the graphical session "
			       "ends and its programs close.  ⛔ It is NOT a "
			       "detach: at the next attach a NEW one will be born",
			    s->utente);
			/*
			 * ⛔⛔ THE ORDER IS NORMATIVE, and it is not a preference: the farewell
			 *     FIRST, the request to end AFTER.  When the compositor falls
			 *     the stage falls with it and the channel is no longer
			 *     needed — a `0x10` sent afterwards is a reason that exists
			 *     and that nobody receives, that is finding B-7.
			 */
			congeda(s, RCP_SESSIONE_TERMINATA,
			        "the user asked to leave the session");
			if (s->g.termina_sessione)
				s->g.termina_sessione(s->g.ctx);
			else
				reg(s, "⚠ no «termina_sessione» hook: the client was "
				       "sent away with 0x10 but the graphical session was NOT "
				       "touched.  ⛔ The two truths do not match, "
				       "and this line is the only place where it shows");
			return false;
		case T_CONGEDO: {
			/* ⛔⭐ FOUR THINGS IN NINE LINES — finding R9.5.
			 *
			 *   1. `lung` was never looked at: `le_u8()` on an empty body
			 *      sets `corto` and returns 0, and nobody read `corto`;
			 *   2. that zero was PLUGGED (`motivo ? motivo : 0x01`): the
			 *      server INVENTED `CHIUSO_DALL_UTENTE` for a reason the
			 *      client had not sent.  ⛔ The log wrote
			 *      `motivo=0x00` and the session closed with `0x01`: two
			 *      truths about the same fact, which is the shape §3.1
			 *      point 3 exists for;
			 *   3. the `dettaglio` was not read — neither as a string, nor as
			 *      UTF-8, nor as a length — and it is exactly what §8.2
			 *      assigns to the LOG;
			 *   4. the reason was sent back without validation inside the
			 *      session close code, where §3.1 point 3 wants «the code
			 *      of the reason OF §8.2».
			 *
			 * ⛔ And §3.1: «code 0 means closing without a reason and MUST
			 *    NOT be used».  A `CONGEDO(0x00)` is a violation by the
			 *    client, not a reason to guess — and it is the same case that
			 *    B11 demands of the PAGE when the one at fault is the server. */
			uint8_t motivo = le_u8(&l);
			size_t p = l.i;
			char dett[257];
			size_t ld = le_str(&l, dett, sizeof dett);
			if (l.corto) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "CONGEDO without reason or without detail");
				return false;
			}
			/* ⚠ The detail is validated on the BYTES THAT ARRIVED, not on the
			 *   copy: §7.1 puts no ceiling on it and `le_str` does not copy what
			 *   does not fit (see its comment).  So even a detail longer than
			 *   our field is judged instead of ignored. */
			if (!utf8_valido((const char *)(l.b + p + 2), ld)) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "the CONGEDO detail is not valid UTF-8 (§6.0)");
				return false;
			}
			if (!motivo_di_82(motivo)) {
				char d[96];
				snprintf(d, sizeof d,
				         "CONGEDO with reason %#04x, which is not a reason "
				         "of §8.2 (and §3.1 forbids code 0)",
				         motivo);
				congeda(s, RCP_ERRORE_PROTOCOLLO, d);
				return false;
			}
			reg(s, "the client takes its farewell, motivo=%#04x dettaglio=%s", motivo,
			    ld < sizeof dett ? dett
			                     : "(longer than the field: not reported)");
			/* ⛔ §7.3: and this is the MOST TRAVELLED road of all when the
			 * product is healthy — the client leaving properly.  If the
			 * release lived only in `congeda()` it would be missing right here. */
			rilascia_al_distacco(s, "client farewell");
			s->stato = S_FINITA;
			/* ⛔⭐ AND THE SLOT LEFT IS WRITTEN, as in the other three places —
			 * cure of the late evening of 11 Aug 2026.
			 *
			 * This was the only one of the four places that free the slot NOT
			 * to call `reg()`: `rcp_libera`, `rcp_pagina_ha_chiuso` and
			 * `rcp_canale_chiuso` all write it.  ⛔ And the hole lay
			 * precisely on the road §8.1 REQUIRES — the client taking its
			 * farewell — that is the most travelled of all when the product is
			 * healthy.
			 *
			 * ⚠ The slot was really freed: `[M]` 11 Aug 2026, twelve
			 *   sessions in a row in the logs of `01-p5-ff-*`, and every later
			 *   «slot TAKEN» says «taken now: 1».  The defect was not
			 *   a leak, it was that **invariant §8.2 `0x0F` could no longer
			 *   be observed**: P5 judges the final number of «taken
			 *   now», and on this road no line carried it. ⇒ The bench
			 *   would have written «THE SLOT WAS NOT FREED» on a server that
			 *   had done its job — a red to the wrong suspect,
			 *   which is the seventh guise of `LEZIONI.md` §1.9.
			 *
			 * ⛔ And before the cure of the farewell it was INVISIBLE: the client
			 *    never took its farewell, so this line was never travelled and
			 *    the slot always went away through the inactivity ceiling, which
			 *    writes its own line. */
			if (s->attaccata) {
				posto_lascia(s->utente);
				s->attaccata = false;
				reg(s, "slot LEFT by %s via %s (taken now: %d)",
				    s->utente, s->provenienza, posti_occupati());
			}
			/* ⭐ The same number the log has just written: a single
			 * truth about the fact, on both roads of §3.1. */
			s->g.chiudi(s->g.ctx, motivo);
			return false;
		}
		case T_VISTA: {
			/* ⛔⭐⭐ §7.1 — «the view has changed», and it is the message this
			 *      server made pay most dearly without serving it.
			 *
			 * ⚠ Until 16 Aug 2026 it fell into the `default` with the line «it
			 *   belongs to the client and §7.1 defines it, but phase 1 does not
			 *   serve it yet», and the price was declared there in full: **a
			 *   conforming client that narrows the window loses the session**.
			 *   ⛔ And it is literally the symptom that finding R1.17 of §7.1 was
			 *   written to make impossible: *«the user narrows the browser
			 *   window to 300 pixels […] with the old line the client had three
			 *   choices, all bad — send `VISTA(300x800)` and have the session
			 *   closed because it resized a window»*.
			 *   The document removed the bad line from the client side; the
			 *   server applied it all the same.
			 *
			 * ⛔⭐ AND WHAT THIS BRANCH **DOES NOT DO** IS THE NORMATIVE HALF:
			 *
			 *   · **it does not touch the canvas**.  §7.1: «`VISTA` MUST NOT
			 *     change the canvas […] The only message that changes the canvas
			 *     is `ADATTA_TELA`».  ⚠ The wrong form here is not «closes», it
			 *     is «works too much»: a server that took the view for a canvas
			 *     request would shrink the desktop of whoever only narrowed the
			 *     window, and **without sending any `TELA`** — that is the two
			 *     sides drifting apart in silence (E2);
			 *   · **it does not touch the encoder**.  §7.1: «in RCP/1 not even
			 *     the size of what is encoded changes»; §6.2 binds
			 *     `largh.`/`altezza` to the canvas in force, and whoever receives
			 *     others closes.  ⇒ Encoding at the view would make the client close;
			 *   · **it answers nothing on the wire**.  §7.1 foresees no
			 *     answer to `VISTA`, and §6.2 makes the client close the session
			 *     in front of a `TELA` it did not ask for: a «thanks, received»
			 *     written as `TELA` would kill the session;
			 *   · **it does not apply the canvas limits**.  §7.1 after R1.17:
			 *     «any size from 1x1 up is legal, odd included».
			 *
			 * ⇒ Validate, keep, write.  It is little, and it is what the arbiter
			 *   asks: the canvas belongs to the SESSION, the view to the CONNECTION. */
			uint32_t nuova_l = le_u32(&l);
			uint32_t nuova_a = le_u32(&l);

			if (l.corto) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "VISTA short: §7.1 wants two u32");
				return false;
			}
			/* ⛔ The state: §7.1 puts `VISTA` among the messages of the session,
			 *    and a view without a session has nothing to describe.
			 *    Same guard as `ADATTA_TELA`, and for the same reason. */
			if (!s->sessione_spedita) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "VISTA before SESSIONE: §7.1 admits it only with "
				        "the session open");
				return false;
			}
			/* ⛔ The only limit, and zero lies outside it — as in `ATTACCA`, and
			 *    the rule is written in the two places because the two messages
			 *    arrive by different roads.  ⚠ If one day they became three,
			 *    it becomes a function. */
			if (!nuova_l || !nuova_a) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "VISTA with a zero side: §7.1 admits any "
				        "size from 1x1 up, and zero is not a size");
				return false;
			}
			reg(s, "VISTA: the client's window goes from %ux%u to %ux%u (§7.1) "
			       "— ⛔ the canvas does NOT change and stays %ux%u, and in RCP/1 not "
			       "even the size of what is encoded changes: the client "
			       "rescales.  The limits of §4.5 do not apply to the view "
			       "(R1.17): any size from 1x1 up, odd included",
			    s->vista_l, s->vista_a, nuova_l, nuova_a, s->tela_l, s->tela_a);
			s->vista_l = nuova_l;
			s->vista_a = nuova_a;
			break;
		}

		case T_DISPOSIZIONE: {
			/* ⛔⭐⭐ §7.1 `0x0009` — «the keyboard layout has changed»,
			 *      and it is the exact twin of `VISTA`: until 16 Aug 2026
			 *      it fell into the same `default` and **closed the session of a
			 *      conforming client**.  `[M]` bench `06-b34` case 3: farewell
			 *      `0x0b ERRORE_PROTOCOLLO`, connection dropped.
			 *
			 * ⚠ The symptom, in one line: *the user changes keyboard layout
			 *   while working, and the session drops.*  It is the same
			 *   shape that finding R1.17 of §7.1 exists to make
			 *   impossible — punishing whoever does what the arbiter defines.
			 *
			 * ⭐ And now it is REALLY needed: with §5-bis.7 carried out, this is the
			 *    message with which the layout is changed **without
			 *    detaching**.  Without it, the only way of changing keyboard
			 *    would be closing the session and reattaching.
			 *
			 * ⛔⛔ AND HERE THE ARBITER DOES NOT SAY SOMETHING THE PRODUCT MUST
			 *     DECIDE: what is done if the layout is well formed but
			 *     **unknown**.  At `ATTACCA` §4.5 says it (farewell
			 *     `SESSIONE_NON_SERVIBILE`); with the session open it does not.
			 *
			 *     ⇒ Here the CHOICE is **not to close**: the one in force is
			 *       kept and the reason is written.  The reason is `SPECIFICHE.md`
			 *       §8.3 — *«never detach»* — and I1: closing the session of whoever
			 *       chose a keyboard this machine does not have means taking
			 *       away their work for a fault that costs them nothing, since
			 *       the previous keyboard still works.  ⚠ At `ATTACCA` it is
			 *       different, and rightly so: there is no session there to save.
			 *     ⚠ It is a PRODUCT rule the arbiter does not name: it must be
			 *       carried into `RCP.md` §7.1, and the report delivers it. */
			char nuova[65];
			size_t ln = le_str(&l, nuova, sizeof nuova);

			if (l.corto) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "DISPOSIZIONE short: §7.1 wants a string");
				return false;
			}
			/* ⛔ The state, as for `VISTA`: §7.1 puts `DISPOSIZIONE` among the
			 *    messages of the session, and a layout without a session has
			 *    nothing to change. */
			if (!s->sessione_spedita) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "DISPOSIZIONE before SESSIONE: §7.1 admits it only with "
				        "the session open");
				return false;
			}
			/* ⛔ The FORM stays `ERRORE_PROTOCOLLO` here too, and it is not an
			 *    inconsistency with the line above: §4.5 keeps the two faults
			 *    distinct because they are two different defects — whoever sends
			 *    «../../etc/passwd» has a broken (or hostile) client, whoever sends
			 *    «hu» only has a keyboard this machine does not have. */
			if (!disposizione_ben_formata(nuova, ln)) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "DISPOSIZIONE malformed");
				return false;
			}
			if (!disposizione_conosciuta(s, nuova)) {
				reg(s, "⚠ DISPOSIZIONE «%s»: this machine does not have it.  ⛔ The "
				       "session is NOT closed (§8.3, «never detach») and keeps "
				       "«%s»: the previous keyboard still works, and taking away "
				       "the work for a missing keyboard would cost more than the "
				       "fault.  ⚠ At `ATTACCA` §4.5 wants the farewell, and there it is "
				       "right: there is no session to save",
				    nuova, s->disposizione[0] ? s->disposizione : "the session's own");
				break;
			}
			if (strcmp(nuova, s->disposizione) == 0) {
				/* ⚠ It is written all the same: a client that sends the same
				 *   layout again is not a fault, but a keymap replacement
				 *   costs Mutter the DESTRUCTION of the keyboard device
				 *   (`STUDI.md` §gnome §9) — and not doing it for nothing is a
				 *   saving one sees. */
				reg(s, "DISPOSIZIONE «%s»: it is already the one in force, I ask "
				       "nothing of the stage (a useless replacement would cost the "
				       "destruction of the keyboard device)",
				    nuova);
				break;
			}
			reg(s, "DISPOSIZIONE: from «%s» to «%s», with the session OPEN (§7.1 0x0009)",
			    s->disposizione[0] ? s->disposizione : "(none)", nuova);
			snprintf(s->disposizione, sizeof s->disposizione, "%s", nuova);
			applica_disposizione(s, "DISPOSIZIONE (0x0009)");
			/* ⛔ And NOTHING is answered on the wire: §7.1 foresees no
			 *    answer to `DISPOSIZIONE`, exactly as for `VISTA`.  A
			 *    «thanks, received» invented here would be an unsolicited
			 *    message, and §6.2 makes the client close the session in front
			 *    of a message it did not ask for. */
			break;
		}
		case T_ADATTA_TELA: {
			/* ⛔⭐⭐ §7.1 — «the client asks for a canvas of another size».
			 *
			 * ⚠ Until 14 Aug 2026 this type fell into the `default` and made a
			 *   conforming client **lose the session**, with the line «phase 1
			 *   does not serve it yet».  ⛔ And it was a violation of ours:
			 *   `RCP.md:483` point 4 says an out-of-limits size is refused
			 *   with `TELA(MISURA_FUORI_LIMITI)` **instead of closing**, and the
			 *   reason is written next to it — «the user who drags a window
			 *   badly must not lose the session».
			 *
			 * ⇒ Now one always answers, and the client knows **what to
			 *   continue with**: the two fields of `TELA` carry the canvas in
			 *   force AFTER the answer, which on a refusal is the previous one. */
			uint32_t chiesta_l = le_u32(&l);
			uint32_t chiesta_a = le_u32(&l);
			uint32_t buona_l = 0, buona_a = 0;

			if (l.corto) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "ADATTA_TELA short: §7.1 wants two u32");
				return false;
			}
			if (!s->sessione_spedita) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "ADATTA_TELA before SESSIONE: §7.1 admits it only with "
				        "the session open");
				return false;
			}
			/* ⛔⭐ AND HERE NO GUARD ON THE SLOT IS NEEDED, and it must be said
			 *     because the first draft of this cure had put one: it would have
			 *     been **dead code that looks alive**.
			 *
			 * `torna_a_parlare()` runs at the top of `rcp_ricevi()`, before
			 * any message: a session detached for silence either takes the slot
			 * back (and then commands by full right) or is sent away with §8.2
			 * `0x0F`.  ⇒ Whoever gets this far ALWAYS holds the slot, and an
			 * `if` that cannot be false is worse than nothing: the day that rule
			 * changed, nobody would know this line was duplicating it.
			 * ⚠ The LIVE guard is the other one, in `tela_richiama_il_palco()`:
			 * there the session without a slot really gets there, because the
			 * FRAMES reach it even when it is silent (bench `04-b31`, case 18). */
			/* ⛔ The ceiling and parity live in ONE place only, and not here:
			 *    `rcp_misura_ammessa()` (`rcp.h`).  Rewriting the same rule here
			 *    would mean having two, and the day one changes the defect is
			 *    «the server accepts a size the compositor cannot take» — that
			 *    is the session of whoever hosts us dying in silence. */
			if (!rcp_misura_ammessa(chiesta_l, chiesta_a, &buona_l, &buona_a)) {
				reg(s, "ADATTA_TELA %ux%u REFUSED: below the minimum of §4.5 "
				       "(%ux%u .. %ux%u) — the canvas stays %ux%u",
				    chiesta_l, chiesta_a, RCP_TELA_L_MINIMA, RCP_TELA_A_MINIMA,
				    RCP_TELA_L_MASSIMA, RCP_TELA_A_MASSIMA, s->tela_l, s->tela_a);
				manda_tela(s, 2 /* RIFIUTATA */, 2 /* MISURA_FUORI_LIMITI */,
				           s->tela_l, s->tela_a);
				break;
			}
			/* ⛔⭐ ABOVE THE MAXIMUM IT IS REDUCED AND SAID — 1 Oct 2026, canvas at
			 *     most 4096x2304 (box in `rcp.h`).  A 5K monitor is not an
			 *     error of the client: `TELA(ADATTATA)` will tell it the real size,
			 *     and this line says why it is not the one requested. */
			if (chiesta_l > RCP_TELA_L_MASSIMA || chiesta_a > RCP_TELA_A_MASSIMA)
				reg(s, "⚠ DECLARED FALLBACK (§4.5): ADATTA_TELA %ux%u beyond the "
				       "canvas maximum %ux%u — reduced to %ux%u (the side that "
				       "overflows to the maximum, the other as it is)",
				    chiesta_l, chiesta_a, RCP_TELA_L_MASSIMA,
				    RCP_TELA_A_MASSIMA, buona_l, buona_a);
			/* ⛔⛔ AND THE DECODER CEILING IS RESPECTED HERE TOO — §4.5:
			 *     *«the granted canvas MUST respect `video.misura_massima` if the
			 *     client declared it»*.  ⚠ Defect found while refuting: this
			 *     check was in `ATTACCA` — where it reduces in proportion, with
			 *     even sides, and declares it — and **not** here.  ⇒ A hi-dpi
			 *     client asking for the size of its own window in physical pixels
			 *     could get a canvas granted that its decoder cannot take, and
			 *     from there there was no going back: the screen stops and does
			 *     not restart.
			 *
			 * ⚠ It is REDUCED instead of refused, because the client did nothing
			 *   wrong — it asked for the size of its window — and `TELA` will
			 *   tell it what it got.  It is the same choice as §4.5 in
			 *   `ATTACCA`, with the same arithmetic. */
			if (s->max_l && (buona_l > s->max_l || buona_a > s->max_a)) {
				uint32_t prima_l = buona_l, prima_a = buona_a;
				uint32_t cl, ca;
				/* The side that limits most: cross comparison, without
				 * floating-point divisions. */
				if ((uint64_t)buona_l * s->max_a <= (uint64_t)buona_a * s->max_l) {
					ca = s->max_a;
					cl = (uint32_t)(((uint64_t)buona_l * s->max_a) / buona_a);
				} else {
					cl = s->max_l;
					ca = (uint32_t)(((uint64_t)buona_a * s->max_l) / buona_l);
				}
				/* ⛔ And the result goes back through the same rule: the reduction
				 *    may have produced an odd number or one below the minimum, and
				 *    rewriting parity here would mean having it in two
				 *    places. */
				if (!rcp_misura_ammessa(cl, ca, &buona_l, &buona_a)) {
					reg(s, "ADATTA_TELA %ux%u REFUSED: reduced to the "
					       "video.misura_massima (%ux%u) it would give %ux%u, which §4.5 "
					       "does not allow — the canvas stays %ux%u",
					    chiesta_l, chiesta_a, s->max_l, s->max_a, cl, ca,
					    s->tela_l, s->tela_a);
					manda_tela(s, 2 /* RIFIUTATA */, 2 /* MISURA_FUORI_LIMITI */,
					           s->tela_l, s->tela_a);
					break;
				}
				reg(s, "⚠ DECLARED FALLBACK (§4.5): ADATTA_TELA %ux%u exceeds the "
				       "video.misura_massima of this client (%ux%u) — reduced to "
				       "%ux%u, proportions kept, both even",
				    prima_l, prima_a, s->max_l, s->max_a, buona_l, buona_a);
			}
			/* ⭐⭐ AND HERE STARTS THE CHAIN THAT WAS MISSING ON 14 AUG 2026.
			 *
			 * ⚠ Until yesterday this point answered `COMPOSITORE_INCAPACE`
			 *   NAMING the missing piece — *«`figli_ritela()` →
			 *   `cattura_ridimensiona()` is missing»* — and it was true.  Now the
			 *   two pieces are there, and the answer is no longer a line: it is a
			 *   round trip to the compositor and back.
			 *
			 * ⛔ THE FIRST CASE IS THE ONE THAT MUST MOVE NOTHING: the size
			 *    requested is already the one in force.  ⚠ It is not a textbook
			 *    case — it is the most frequent of all: the client sends the size
			 *    of its window at every resize, and whoever drags an edge
			 *    sends twenty per second.  Passing it to the stage would mean
			 *    restarting the stream for nothing, that is **losing a frame at
			 *    every useless request** (`STUDI.md` §kde §8.2-bis).
			 *
			 * ⚠ But only if there is no request already in flight: if there is one,
			 *   the stage is going ELSEWHERE, and this is a change of mind that
			 *   must really be passed on. */
			if (buona_l == s->tela_l && buona_a == s->tela_a && !s->tela_volo) {
				/* ⛔ It answers `TELA(ADATTATA)` and does NOT open the keyframe
				 *    debt: the «size that was already there» form of
				 *    `rcp_tela_adattata_ora()` does it, and exists for this. */
				rcp_tela_adattata_ora(s, buona_l, buona_a, ora);
				break;
			}

			/* ⛔ NO HOOK = COMPOSITORE_INCAPACE, and it is the TRUE answer for
			 *    whoever hosts us without a stage: the in-process benches of phase 1
			 *    and the harness of `banchi/01-b3-rcp-innesta.py`.  §7.1: «if the
			 *    compositor cannot resize, the server MUST answer with
			 *    `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`, and the client MUST
			 *    show the entry as off.  It MUST NOT pretend it
			 *    succeeded». */
			if (!s->g.ritela) {
				reg(s, "ADATTA_TELA %ux%u → %ux%u allowed, but this host has no "
				       "stage to resize (hook `ritela` not "
				       "connected): COMPOSITORE_INCAPACE, and the canvas stays %ux%u",
				    chiesta_l, chiesta_a, buona_l, buona_a, s->tela_l, s->tela_a);
				manda_tela(s, 2 /* RIFIUTATA */, 1 /* COMPOSITORE_INCAPACE */,
				           s->tela_l, s->tela_a);
				break;
			}

			/* ⛔⭐ A REQUEST IN FLIGHT IS ANSWERED BEFORE ACCEPTING ANOTHER
			 *     — §7.1: «the n-th `TELA` answers the n-th `ADATTA_TELA`».
			 *
			 * ⚠ The client KEEPS COUNT of the unanswered requests (§6.2, and
			 *   from it decides whether to hold back a frame or close the session).
			 *   If two `ADATTA_TELA` received only one `TELA`, that count would
			 *   never return to zero and the client would hold back frames
			 *   forever — that is its memory.  ⛔ Whoever drags an edge sends
			 *   exactly two in a row: it is not a rare case, it is THE case. */
			if (s->tela_volo) {
				reg(s, "ADATTA_TELA %ux%u arrived while %ux%u was still in flight "
				       "to the stage: I answer NON_ORA to the FIRST (§7.1 wants one "
				       "TELA for each) and pass on the second",
				    buona_l, buona_a, s->tela_volo_l, s->tela_volo_a);
				manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,
				           s->tela_a);
				s->tela_volo = false;
			}

			/* ⛔ And the hook says whether the QUESTION left, not whether the canvas
			 *    changed: the proof arrives with a frame, and
			 *    `rcp_tela_concessa()` brings it in here. */
			if (!s->g.ritela(s->g.ctx, buona_l, buona_a)) {
				reg(s, "⛔ ADATTA_TELA %ux%u → %ux%u: the request did NOT leave "
				       "for the stage (no child, or the socket did not "
				       "take it).  NON_ORA, and the canvas stays %ux%u",
				    chiesta_l, chiesta_a, buona_l, buona_a, s->tela_l, s->tela_a);
				manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,
				           s->tela_a);
				break;
			}
			s->tela_volo = true;
			s->tela_volo_l = buona_l;
			s->tela_volo_a = buona_a;
			s->tela_volo_da = ora;
			/* ⛔ And the previous disagreement is CLOSED: from now the stage has a
			 *    new request, and dating the backstop on an old disagreement would
			 *    make it expire backwards. */
			s->tela_disaccordo_da = 0;
			s->tela_disaccordo_attesa = 0;
			reg(s, "⭐ ADATTA_TELA %ux%u → %ux%u PASSED to the stage (`figli_ritela()` "
			       "→ `cattura_ridimensiona()`).  ⚠ No `TELA` now: the "
			       "answer is the first frame at the new size, and if it does not "
			       "arrive within %u ms NON_ORA is answered (§7.1)",
			    chiesta_l, chiesta_a, buona_l, buona_a,
			    (unsigned)RCP_TELA_ATTESA_MS);
			break;
		}
		default: {
			/* §7.1 + §3: an unknown type on the control channel is not
			 * ignored — the connection drops.
			 *
			 * ⛔ But §3.1 point 1 asks to write WHAT was not understood,
			 * and «unknown» would be false for half the cases: `ECCOMI`,
			 * `AMMESSO`, `RESPINTO`, `SESSIONE`, `CURSORE_FORMA`, `TELA` and
			 * `BANCO_ESITO` are KNOWN types that travel in the other direction
			 * (§7.1).  A client sending one has a different defect from one
			 * that invents a type, and the log must tell them apart.
			 *
			 * ⛔⭐ AND THE FOUR THAT REMAIN ARE NOT «UNKNOWN» — finding
			 *    R9.7.  §7.1 numbers them and assigns them to the CLIENT: `0x0008 VISTA`,
			 *    `0x0009 DISPOSIZIONE`, `0x000B ADATTA_TELA`,
			 *    `0x000D RICHIEDI_CHIAVE`.  Writing «unknown» on a type
			 *    the arbiter defines is saying something false in the log, and it is
			 *    the same defect the paragraph above declares it
			 *    corrected for the server's types.
			 *
			 * ⭐ AND SINCE 16 AUG 2026 **ONE** REMAINS: `0x0009 DISPOSIZIONE`.
			 *    The other three went away one at a time, and each one
			 *    took away the same price — a session lost to a conforming
			 *    client:
			 *      · `0x000D RICHIEDI_CHIAVE` on 12 August, with the video channel:
			 *        §5.2 obliges the client to send it as soon as it sees a gap;
			 *      · `0x000B ADATTA_TELA` on 14 August, with the stage able to
			 *        resize: §7.1 requires a `TELA` for it with a MUST;
			 *      · `0x0008 VISTA` on 16 August, sub-phase 6.4: it is the most
			 *        expensive of the three, because it required **nothing** — the
			 *        view does not touch the canvas, does not touch the encoder and
			 *        has no answer.  ⛔ Keeping it was enough, and for two phases it
			 *        closed the session of whoever narrowed the browser window.
			 *
			 * ⚠ And `0x0009 DISPOSIZIONE` stays out with a REAL price, not through
			 *   forgetfulness: renegotiating a keymap destroys and recreates the
			 *   `libei` keyboard device (`STUDI.md` §gnome §9), and that
			 *   chain belongs to sub-phase 6.2.  ⛔ As long as it stays out, a
			 *   conforming client that changes layout **loses the session**, and
			 *   this line is what says so: whoever reads «not yet served in phase
			 *   1» knows the defect is ours and knows where it disappears; whoever
			 *   read «unknown» went looking for a defect of the client. */
			bool del_server = tipo == T_ECCOMI || tipo == T_AMMESSO ||
			                  tipo == T_RESPINTO || tipo == T_SESSIONE ||
			                  tipo == T_CURSORE_FORMA ||
			                  tipo == 0x000E /* TELA */ ||
			                  tipo == T_BANCO_ESITO;
			const char *del_client = NULL;
			switch (tipo) {
			/* ⚠ `0x0008 VISTA` no longer appears here: since 16 Aug 2026 it has
			 *   a case of its own and never reaches the `default` — like `0x000B`
			 *   on the 14th.  Removed instead of left «for safety»: an
			 *   unreachable branch naming a served type is a line that
			 *   lies to whoever reads the log, and it is the defect this
			 *   same paragraph declares it corrected for the others. */
			/* ⚠ `0x000B ADATTA_TELA` no longer appears here: since 14 Aug 2026 it
			 *   has a case of its own and never reaches the `default`.  Removed
			 *   instead of left «for safety»: an unreachable branch naming a
			 *   served type is a line that lies to whoever reads. */
			default:
				break;
			}
			char d[160];
			if (del_server)
				snprintf(d, sizeof d, "type %#06x: it belongs to the server, not to the client",
				         tipo);
			else if (del_client)
				snprintf(d, sizeof d,
				         "type %#06x %s: it belongs to the client and §7.1 defines it, "
				         "but phase 1 does not serve it yet",
				         tipo, del_client);
			else
				snprintf(d, sizeof d, "unknown type %#06x on control",
				         tipo);
			congeda(s, RCP_ERRORE_PROTOCOLLO, d);
			return false;
		}
		}
		if (!avanti)
			return false;
		/* ⛔ §6.0: one advances by the DECLARED length, not by how much was
		 * read.  ⚠ The check here is not a duplicate of the one before
		 * the switch: that one speaks BEFORE the effects and is the check of
		 * §6.1; this one fires only if `misura_campi()` and `tratta_*()` have
		 * drifted apart, that is if someone changed a body in one place only. */
		if (l.i != lung) {
			congeda(s, RCP_ERRORE_PROTOCOLLO,
			        "the body has more bytes than the expected fields");
			return false;
		}
		size_t prima = s->acc_len;
		memmove(s->acc, s->acc + 6 + lung, s->acc_len - 6 - lung);
		s->acc_len -= 6 + lung;
		/* ⛔ AND THE TAIL IS ZEROED — finding R9.8.  The `memmove` slid the
		 * remainder down and left the bytes of the message just consumed where
		 * they were: those of a `CREDENZIALI` are the password in clear, and
		 * they stayed in the session until the end of the connection.
		 * §4.4: «it must be zeroed as soon as PAM has answered». */
		memset(s->acc + s->acc_len, 0, prima - s->acc_len);
		s->da_quando = ora;
	}
}

/* ⛔⭐ WHOEVER HAS BEEN SILENT FOR THIRTY SECONDS IS NO LONGER ATTACHED, AND WHEN
 *    THEY SPEAK AGAIN THEY MUST KNOW IT — finding R9.2.
 *
 *    The silence branch of `rcp_tempo()` left the slot and set
 *    `attaccata = false`, but the state stayed `S_ATTIVA`: from there on the
 *    server had TWO «active» sessions for the same user — what I2
 *    forbids — and the first kept being served as if nothing had happened,
 *    without ever having received a `CONGEDO`, a reason or a close code.  §8.2:
 *    «no attached and alive client is ever ousted», and that one was
 *    ousted in silence.
 *
 * ⭐ The slot can be TAKEN BACK, and it is not a concession: §8.2 says that «the
 *    criterion is the silence clock, not the intention of whoever arrives», and
 *    the case the clock exists to serve is the phone back from the
 *    tunnel.  If nobody has taken the slot, that client resumes
 *    exactly from where it was.
 *
 * ⛔ If instead the slot has been taken, the farewell is `GIA_ATTIVA_REMOTA` and
 *    the sentence the client will build from it — «you already have an active
 *    session elsewhere» — this time is TRUE.  ⚠ And it stays true that «the one
 *    refused is whoever arrives»: here whoever arrives is them, whoever was
 *    there is the other.
 *
 * ⛔⭐ AND IT IS A FUNCTION, since 14 Aug 2026, because now the client's bytes
 *     come in through TWO doors — `rcp_ricevi()` and `rcp_ricevi_input()`.
 *     ⚠ Leaving it written by hand inside the first would have meant that
 *     whoever speaks again **by moving the mouse** does not take back the slot,
 *     and the symptom would have been: the video restarts if you type, not if
 *     you move your hand.  Two copies of a state diverge, and this is the copy
 *     that was not made.
 *
 * Returns `false` if the session has been sent away. */
static bool torna_a_parlare(rcp_sessione *s)
{
	if (s->stato != S_STACCATA)
		return true;
	if (posto_prendi(s) == POSTO_PRESO) {
		s->attaccata = true;
		s->stato = S_ATTIVA;
		/* ⛔ §7.3: the release on detach has already happened (the silence
		 * triggered it), and this session starts again with free hands: if it
		 * fell silent a second time, the release must be able to fire again. */
		s->inp_rilasciato = false;
		reg(s, "⭐ slot TAKEN BACK by %s via %s after the silence: nobody "
		       "else had taken it (taken now: %d)",
		    s->utente, s->provenienza, posti_occupati());
		return true;
	}
	reg(s, "⛔ %s speaks again after the silence, but their slot belongs "
	       "to another client: §8.2 0x0F, and this time it is true",
	    s->utente);
	congeda(s, RCP_GIA_ATTIVA_REMOTA,
	        "the slot of this session was taken by another client "
	        "while this one was silent");
	return false;
}

bool rcp_ricevi(rcp_sessione *s, const uint8_t *dati, size_t len, uint64_t ora)
{
	if (s->stato == S_FINITA) {
		/* ⛔ And it is WRITTEN.  §4.4 says that after `RESPINTO` the client must
		 * not retry on the same connection, and §4.2 that after the end of the
		 * session nothing more is sent: they are two MUSTs of the CLIENT, and
		 * the only place from which they can be observed is here.  ⚠ Without
		 * this line a client that retries is indistinguishable from one that
		 * stopped — B11 would measure the server's silence instead of the
		 * page's behaviour.
		 *
		 * ⛔⭐ BUT NOT EVERYTHING THAT ARRIVES AFTER THE END IS A VIOLATION, and
		 *    counting it all together pointed a red at the wrong
		 *    suspect — the seventh guise of `LEZIONI.md` §1.9.
		 *
		 * §4.4 forbids the client ONE thing: **retrying**.  §8.1 imposes
		 * another: whoever closes **MUST** send `CONGEDO` with the reason.  ⭐ The
		 * two meet when the server errs AFTER `RESPINTO` — the
		 * `respinto-poi-congedo` case of B11: the page sees a message that should
		 * not have arrived, closes as §3 requires, and its `CONGEDO` leaves
		 * when for us the session is already over.
		 *
		 * ⚠ On 10 Aug 2026 that 69-byte `CONGEDO` was counted as
		 *   «sent after the end», and the red went to the page that was
		 *   doing **exactly** what §8.1 requires of it.  ⛔ The control
		 *   channel had no FIN: §4.2 had nothing to do with it, and the only
		 *   rule in play — §4.4 — speaks of attempts, not of partings.
		 *
		 * ⭐ So one distinguishes, and distinguishes **on messages**, not on the
		 *    first six bytes of the piece: see `giudica_dopo_la_fine()`, finding R9.15. */
		giudica_dopo_la_fine(s, dati, len);
		return false;
	}
	/* ⭐ The user's INACTIVITY clock is reset here, on RCP bytes
	 *    — and with it the sign of life, because a byte that arrived is a packet
	 *    that arrived.  ⚠ The long reason is on the other of the two calls, in
	 *    `rcp_ricevi_input()`. */
	s->ultimo_byte = ora;
	s->ultima_vita = ora;

	/* ⚠ The connection is not closed for silence alone — that choice is
	 *   declared in the box at the top and does not change.  What changes is
	 *   that the STATE tells the truth.  See `torna_a_parlare()`, finding R9.2. */
	if (!torna_a_parlare(s))
		return false;

	/* ⛔ It is buffered IN PIECES and drained after each one: so the ceiling is
	 * the one of §6.1 and not that of a buffer, and a big piece does not die
	 * because more messages fit inside it (finding R9.13). */
	while (len) {
		size_t spazio = MAX_ACCUMULO - s->acc_len;
		if (spazio == 0) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "too many bytes waiting for a body");
			return false;
		}
		size_t quanti = len < spazio ? len : spazio;
		int esito = accumula(s, dati, quanti);
		if (esito == 0) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "too many bytes waiting for a body");
			return false;
		}
		if (esito < 0) {
			/* ⚠ §8.2 has no reason meaning «memory is exhausted»:
			 *   `SESSIONE_NON_SERVIBILE` is the closest — «cannot be
			 *   served» — and carries the detail in the body.  Our choice, and
			 *   declared here so that it is not read as a rule. */
			congeda(s, RCP_SESSIONE_NON_SERVIBILE,
			        "out of memory in the control channel accumulation");
			return false;
		}
		dati += quanti;
		len -= quanti;
		if (!drena(s, ora))
			return false;
	}
	return true;
}

/* ⛔ §2.5 — the violation that does NOT come from the control channel.
 *
 * Whoever opens one stream too many, or puts the wrong channel inside it, has
 * sent no control message: the violation is detected by the HOST, which
 * is the only one that sees the streams.  ⛔ But the closing must stay that of
 * §3.1 — log, `CONGEDO` on the control channel if it is still usable,
 * and the reason code in the closing of the session — and those three things
 * only this module knows how to do.
 *
 * ⚠ It is the **second conditional of §3.1** that makes the case interesting:
 *   here the control channel is usually still good, so the `CONGEDO`
 *   really leaves.  A bench that demanded all three points ALWAYS would give
 *   red on the right code the day it was not (finding R3.3).
 *
 * ⛔⭐ AND WITH THE SESSION OVER ONE DOES NOT KEEP QUIET — finding R9.16.  This
 *    function went entirely and only through `congeda()`, which if the state is
 *    `S_FINITA` leaves at the first line: no log, no `CONGEDO`, no close code.
 *    A client that takes its farewell properly and THEN opens a stream in the
 *    wrong direction (§2.5) left **no** trace — and the host, which saw that
 *    stream, has no other place to say it.
 *
 * ⚠ The comparison is internal to this file: `rcp_ricevi()` writes «bytes
 *   arrived AFTER the end of the session» precisely because «the only place
 *   from which they can be observed is here».  For STREAMS that place is this
 *   function. */
/* ⛔⭐ THE FAREWELL THAT COMES FROM OUTSIDE — §8.1, and the case it was written
 *     for is `SERVER_IN_CHIUSURA` (§8.2, `0x0C`).  Finding B-7, night of
 *     10 Aug 2026.
 *
 *     `0x0C` was defined in `rcp.h` and **no line of the product emitted it**:
 *     at a `systemctl stop` with an active session the server freed everything
 *     and kept quiet.  The client stayed waiting for the 30 s of inactivity
 *     and showed «network error» — that is literally the defect of
 *     `LEZIONI.md` §1.7 that §3.1 exists to remove.
 *
 * ⚠ Whoever closes MUST send `CONGEDO` with the reason **and** repeat the reason
 *   in the close code: both roads are travelled by `congeda()`, and that is
 *   why this function does nothing but call it.  ⛔ The reason is chosen
 *   by the host, because only it knows why it is closing. */
void rcp_congeda(rcp_sessione *s, uint8_t motivo, const char *dettaglio)
{
	if (!s || s->stato == S_FINITA)
		return;
	congeda(s, motivo, dettaglio ? dettaglio : "");
}

void rcp_violazione(rcp_sessione *s, const char *dettaglio)
{
	if (!s)
		return;
	if (s->stato == S_FINITA) {
		/* ⛔ §3.1 point 1 applies all the same: one writes WHAT.  Points 2 and
		 * 3 do not, and rightly — the session is already closed with its
		 * reason, and sending a second one would state two truths about the
		 * same fact. */
		reg(s, "⛔ violation detected AFTER the end of the session from %s: %s "
		       "— the session was already closed, so no CONGEDO and no "
		       "close code (§3.1), but the log names it",
		    s->provenienza, dettaglio);
		return;
	}
	congeda(s, RCP_ERRORE_PROTOCOLLO, dettaglio);
}

/* ⛔⭐ §4.2 — THE CONTROL CHANNEL CLOSING IS THE END OF THE SESSION,
 * AND IT HOLDS EVEN WHEN THE ONE CLOSING IT IS THE SERVER.
 *
 * From that instant no client message can arrive any more — §4.2 forbids it
 * to send on any channel — so the slot (§8.2 reason 0x0F) would be freed by
 * NOBODY until the death of the connection.  And a connection, a browser keeps
 * it alive.
 *
 * ⭐ Found by B11 on 10 Aug 2026, and only on Chrome: after the case in which
 *    the server closes the channel with a FIN, the three following cases received
 *    `GIA_ATTIVA_REMOTA`.  Not on Firefox — there the transport closed the stream
 *    in time and `rcp_libera()` arrived all the same.  ⛔ The defect lived in the
 *    difference between two engines, and no test client could see it.
 *
 * ⚠ The session is not freed and not sent away: sending a `CONGEDO` on a
 *   channel we have just closed makes no sense, and the reason — if there was
 *   one — has already travelled in the close code (§3.1 point 3).  It stays alive
 *   because it is the only point from which one observes a client sending after
 *   the end, which is the MUST of §4.2.                                      */
void rcp_canale_chiuso(rcp_sessione *s)
{
	if (!s || s->stato == S_FINITA)
		return;
	reg(s, "the control channel closed on the server side: "
	       "§4.2, the session is over (state: %s)",
	    NOMI_STATO[s->stato]);
	/* ⛔ §7.3: the fourth road — the channel dies and does not go through `congeda()`. */
	rilascia_al_distacco(s, "the control channel closed");
	if (s->attaccata) {
		posto_lascia(s->utente);
		s->attaccata = false;
		reg(s, "slot LEFT by %s via %s (taken now: %d)", s->utente,
		    s->provenienza, posti_occupati());
	}
	s->stato = S_FINITA;
}

/* ⭐ THE OUTCOME OF THE ASYNCHRONOUS CHECK COMES BACK IN HERE — `DECISIONI.md` §1.10.
 *
 * ⛔ AND THERE ARE FOUR WALLS BEFORE TOUCHING `cred_buone`, one for each
 *    road by which a «yes» could get in where it must not (invariant I3):
 *
 *   1. the session must be alive and in `attesa-verdetto` — a verdict that
 *      arrives on a session already `attiva` cannot reopen it;
 *   2. it must HAVE BEEN ASKED (`verdetto_atteso`) — so an invented request
 *      finds nobody waiting for it;
 *   3. the number must be ITS OWN — the request belongs to the process, not to
 *      the session, and without this comparison one user's answer could
 *      admit another.  ⛔ It is the wall that counts most;
 *   4. `verdetto_atteso` is switched off HERE: a second answer for the same
 *      request does not get in, and «I received two verdicts» does not become
 *      «the last one wins».
 *
 * ⚠ And it sends nothing on the wire: `rcp_tempo()` takes care of that, when
 *   the fixed second of §4.4-bis has passed too. */
bool rcp_verdetto(rcp_sessione *s, uint64_t pratica, bool ammesso,
                  uint64_t ora)
{
	if (!s || s->stato != S_ATTESA_VERDETTO || !s->verdetto_atteso)
		return false;
	if (s->pratica != pratica)
		return false;

	s->verdetto_atteso = false;
	s->cred_buone = ammesso;
	s->cred_motivo = RCP_CREDENZIALI_ERRATE;
	reg(s, "PAM answered (request %llu): %s  ⭐ and the thread never "
	       "stopped (DECISIONI.md §1.10)",
	    (unsigned long long)pratica, ammesso ? "admitted" : "refused");

	/* ⛔ THE COUNT OF §4.4-bis MOVES HERE, and it is the only place where the
	 *    fact «an attempt failed» now exists.  ⚠ Bringing it here is the only
	 *    thing the ban had to undergo from this cure: the rule does not
	 *    change — three failures from the same address in five minutes, twelve
	 *    hours — the moment at which it is known changes. */
	if (ammesso)
		azzera_falliti(s, s->indirizzo, ora);
	else
		segna_fallito(s, s->indirizzo, ora);
	return true;
}

bool rcp_tempo(rcp_sessione *s, uint64_t ora)
{
	if (s->stato == S_FINITA)
		return false;

	/* ⛔⛔ THE BACKSTOP OF PASTE REQUESTS, and without it the clipboard
	 *      channel works only once.
	 *
	 *      The case: the text is asked of the client (`APPUNTI_CHIEDI`) and the
	 *      client never answers — it has detached, or cannot serve that
	 *      transfer.  ⛔ The queue does not empty, `app_chiesto` stays true, and
	 *      from there on **every later paste queues behind a question that
	 *      will never have an answer**: the symptom is «the clipboard worked
	 *      once and then never again», which nobody connects to a client that
	 *      did not answer half an hour ago.
	 *
	 * ⚠ And this backstop is WIDER than the child's (4 s) on purpose: there
	 *   the debt towards the compositor is paid — whoever pastes has already had
	 *   their empty answer — here the channel is put back on its feet.  ⛔ Narrowing
	 *   it until they coincide would make the two things expire together, and a
	 *   text arriving at just the right millisecond would no longer find anyone
	 *   to serve on either side. */
	if (s->app_serial_n > 0 && ora - s->app_chiesto_ms > APPUNTI_FONDO) {
		reg(s, "⚠ APPUNTI: %d paste requests without an answer from the client "
		       "after %llu ms (backstop %d): the queue is emptied.  ⛔ Whoever was "
		       "pasting has already had their empty answer from the child; this "
		       "backstop serves not to leave the channel blocked for the pastes AFTER",
		    s->app_serial_n, (unsigned long long)(ora - s->app_chiesto_ms),
		    APPUNTI_FONDO);
		s->app_serial_n = 0;
		s->app_chiesto = false;
	}

	/* ⛔ §4.4-bis: the fixed delay applies to AMMESSO TOO.  Applying it only
	 * to refusals would put the timing back on the other side, and the
	 * distinction §4.4 forbids writing in the reason would be read with a stopwatch. */
	if (s->stato == S_ATTESA_VERDETTO) {
		/* ⛔⭐ NOW TWO THINGS ARE AWAITED, AND THE ORDER IS NOT GUARANTEED —
		 *     `DECISIONI.md` §1.10, 12 Aug 2026.
		 *
		 *     The fixed second of §4.4-bis and the helper's answer.  Until
		 *     yesterday the second had already arrived when this state
		 *     began — PAM had blocked the thread — and here it was enough to
		 *     look at the clock.
		 *
		 * ⭐ And the time of whoever authenticates does NOT change: PAM takes
		 *    from 1.0 to 2.2 s (`[M]` B8), so the verdict almost always arrives
		 *    AFTER the fixed second and it is the verdict that sets the pace —
		 *    exactly as before.  What changes is that meanwhile the thread works.
		 *
		 * ⛔ And the fixed second stays a FLOOR, not a ceiling: an
		 *    answer arrived in 10 ms does not make `AMMESSO` go out in 10 ms,
		 *    because §4.4-bis wants the stopwatch not to distinguish what
		 *    the reason does not distinguish. */
		if (s->verdetto_atteso && ora - s->cred_arrivo > TETTO_VERDETTO) {
			/* ⛔ The safety net, and it counts as NO.  `cred_buone` has been false
			 *    since `CREDENZIALI` arrived: here nothing is touched,
			 *    one stops waiting. */
			s->verdetto_atteso = false;
			s->no_e_nostro = true;
			reg(s, "⛔ no verdict from the helper after %llu ms (ceiling %d): "
			       "RESPINTO.  ⚠ It is OUR defect, not a wrong "
			       "password — and that is why it does NOT count as a failed attempt "
			       "of §4.4-bis",
			    (unsigned long long)(ora - s->cred_arrivo), TETTO_VERDETTO);
		}
		if (s->verdetto_atteso)
			return true; /* PAM is still answering, and meanwhile the thread turns */
		/* ⛔ `<=` and not `<`: `ora` and `cred_arrivo` are TRUNCATED milliseconds,
		 *    so a difference of 1000 can be 999.x real ms.  `[M]` 23
		 *    Sep 2026: 15 admitted out of 50 at 999 ms on gnome, 16 out of 50 on kde —
		 *    and the test client, which watches §4.4-bis, left saying
		 *    «less than a second» (C20 «I could not look» on gnome and kde).
		 *    The fixed second is a FLOOR: at most 1 ms more is paid. */
		if (ora - s->cred_arrivo <= RITARDO_FISSO)
			return true;
		reg(s, "the fixed second has passed (%llu ms)",
		    (unsigned long long)(ora - s->cred_arrivo));
		if (s->cred_buone) {
			manda_messaggio(s, T_AMMESSO, NULL, 0);
			s->stato = S_ATTESA_ATTACCA;
			s->da_quando = ora;
			reg(s, "admitted utente=%s da=%s", s->utente, s->provenienza);
			return true;
		}
		/* ⛔⭐ AND ON THE WIRE THE REASON IS THE SAME, but not in the log — it is
		 *     the same distinction `autenticazione.c` makes between «PAM
		 *     refused» and «PAM could not judge».  §4.4 forbids telling the
		 *     client why, because it would be an oracle; ⛔ but whoever
		 *     diagnoses must be able to tell a thousand wrong passwords from a
		 *     dead helper, or they will search in the password for hours. */
		if (s->no_e_nostro)
			reg(s, "⛔ and this RESPINTO is OURS, not PAM's: the check was "
			       "not made.  ⚠ On the wire the reason is the same (§4.4 "
			       "forbids distinguishing them), and the count of §4.4-bis was NOT "
			       "touched");
		respingi(s, s->cred_motivo);
		return false;
	}

	/* ⛔ The silence: whoever has been silent for thirty seconds no longer holds the slot.
	 * ⚠ The connection stays open — see the box at the top.
	 *
	 * ⛔⭐ AND THE STATE CHANGES WITH THE SLOT — finding R9.2.  Here the slot was
	 *    left and `attaccata = false` was set, but the state stayed
	 *    `S_ATTIVA`: `rcp_stato_nome()` kept answering «attiva» — and
	 *    it is what the host queries — and `s->stato != S_ATTIVA` is the only
	 *    guard of `BANCO_MARCA`.  After a second client had got in,
	 *    the server had TWO «attiva» sessions for the same user, which is
	 *    precisely what I2 forbids.
	 *
	 *    ⚠ The box at the top declares a choice — leaving the connection
	 *      open — and it is defensible.  ⛔ But «not closing the connection» and
	 *      «staying active» are two different things, and the second was not
	 *      declared anywhere.  The way back from here is in
	 *      `rcp_ricevi()`: the slot is taken back if it is free. */
	/* ⛔⭐ AND `ultima_vita` IS LOOKED AT, NOT `ultimo_byte` — the repair of 16
	 *     Aug 2026, and the long reason is on the field, at the top of the file.
	 *
	 * ⚠ `ultimo_byte` does not disappear: it is the clock of USER INACTIVITY
	 *   (30 minutes, §5.3), which this module does not have yet and which now has
	 *   its field ready and right.  ⛔ Keeping one only for two jobs is the
	 *   defect we have just paid for: it is not done again. */
	if (s->stato == S_ATTIVA && s->attaccata &&
	    ora - s->ultima_vita > SILENZIO) {
		posto_lascia(s->utente);
		s->attaccata = false;
		s->stato = S_STACCATA;
		reg(s, "DETACHED for silence: %llu ms without a PACKET from %s — and "
		       "the last RCP byte is from %llu ms ago (§5.3: here what counts is the "
		       "client that is silent, not the user who does not touch) "
		       "(slots taken now: %d; state: %s)",
		    (unsigned long long)(ora - s->ultima_vita), s->provenienza,
		    (unsigned long long)(ora - s->ultimo_byte),
		    posti_occupati(), NOMI_STATO[s->stato]);
		/* ⛔⭐ §7.3 NAMES SILENCE FIRST among the three ways in which «a
		 *     connection ends», and it is the worst case of the three: here the
		 *     client has said nothing and will say nothing more — it is the
		 *     phone dead in the tunnel — while the GRAPHICAL SESSION
		 *     survives (invariant I4).  A Ctrl pressed a moment before
		 *     the line dropped would stay pressed on the real desktop, and
		 *     the user would find it so on reattach.
		 * ⚠ And the RCP session is not over: here only the slot has been
		 *   left.  If it speaks again, `inp_rilasciato` is switched back on in
		 *   `rcp_ricevi()`/`rcp_ricevi_input()` together with the slot taken back. */
		rilascia_al_distacco(s, "silence of §5.3");
	}

	/* ⛔⭐ §5.3 — USER INACTIVITY, the second of the three clocks.
	 *
	 *     «30 minutes without input ⇒ REMOTIX detaches the client: getting back
	 *     in takes user and password.»  ⇒ It is a CONGEDO, not a detach for
	 *     silence: the connection closes with reason `0x02`, and the page
	 *     goes back to the login form.
	 *
	 * ⛔ And the order with the clock above is NOT indifferent: silence first.
	 *    A client that has stopped answering on the wire must be
	 *    declared detached — so whoever arrives gets in (§8.2) — and not
	 *    sent away for inactivity, which would mean «the user was there and
	 *    touched nothing».  ⚠ They are two different things and produce two
	 *    different sentences for whoever reads.
	 *
	 * ⚠ And `s->attaccata` is looked at: a session that does not hold the slot
	 *   has no user to declare inactive.  ⭐ The GRAPHICAL SESSION survives
	 *   anyway (I4): this farewell detaches the client, it does not close the
	 *   desktop — that is the THIRD clock, and it is another thing. */
	if (inattivita_ms && s->stato == S_ATTIVA && s->attaccata &&
	    ora - s->ultimo_byte > inattivita_ms) {
		char d[192];
		snprintf(d, sizeof d,
		         "%llu ms without user input (ceiling %llu): §5.3, and "
		         "getting back in takes user and password",
		         (unsigned long long)(ora - s->ultimo_byte),
		         (unsigned long long)inattivita_ms);
		reg(s, "⭐ §5.3 — INACTIVITY: %s.  ⚠ The graphical session STAYS (I4): "
		       "the client is detached, the desktop is not closed",
		    d);
		congeda(s, RCP_INATTIVITA, d);
		/* ⛔ `false` as for the other ceilings: the session is over, and the
		 *    caller must not keep working on it. */
		return false;
	}

	/* ⛔ §7.1 — the backstop of the `ADATTA_TELA` wait.  ⚠ It sits HERE, and not
	 *    where the frames arrive, for the lesson of `regola_battito` (paid for
	 *    on 11 August with B6): a deadline that fires only when something
	 *    arrives is a deadline that never fires — and the case that matters is
	 *    precisely the one in which nothing arrives. */
	tela_scade(s, ora);

	uint64_t tetto = 0;
	const char *quale = NULL;
	if (s->stato == S_ATTESA_CIAO) {
		tetto = TETTO_CIAO;
		quale = "CIAO";
	} else if (s->stato == S_ATTESA_CREDENZIALI) {
		tetto = TETTO_CREDENZIALI;
		quale = "CREDENZIALI";
	} else if (s->stato == S_ATTESA_ATTACCA) {
		tetto = TETTO_ATTACCA;
		quale = "ATTACCA";
	}
	if (tetto && ora - s->da_quando > tetto) {
		char d[64];
		snprintf(d, sizeof d, "ceiling expired for %s", quale);
		congeda(s, RCP_TEMPO_SCADUTO, d);
		return false;
	}
	return true;
}
