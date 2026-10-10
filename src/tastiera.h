/*
 * tastiera.h — THE SEAM between a LETTER and the KEY POSITIONS that produce it.
 *
 * ⛔ THIS FILE BELONGS TO THE COORDINATOR (see `input.h`, same reason).
 *
 * The problem, in one line (`SPECIFICHE.md` §7.3): on the wire letters
 * travel as letters, but a Wayland compositor does not accept letters —
 * it accepts KEY POSITIONS, and decides itself which letter it is by looking at the layout.
 * ⇒ Someone must make the trip backwards: "to make è come out with
 *   this layout, which key do I press, and with which modifiers?".
 *
 * ⚠ The typewriter: the wire carries the printed LETTER, `libei` wants
 *   the HAMMER to strike.  This file finds the hammer.
 */
#ifndef REMOTIX_TASTIERA_H
#define REMOTIX_TASTIERA_H

#include <stdint.h>
#include <stddef.h>

typedef struct tastiera Tastiera;

/*
 * Opens the session's layout with `xkbcommon`.  `disposizione` is the
 * string negotiated at attach (`RCP.md` §4.5, `DECISIONI.md` §5-bis.7): for
 * example "it" or "us".  NULL = the one in force in the session.
 *
 * ⛔ Returns NULL and fills `*errore` if the layout does not load.  ⛔ It does NOT
 *    fall back to "us" silently: it would be the silent fallback
 *    `CODER.md` §4.2 forbids, and the symptom would be "it types the wrong letters".
 */
Tastiera *tastiera_apri(const char *disposizione, char **errore);

/*
 * ⭐⭐ THE SAME OPENING, BUT SAYING WHOSE IT IS — 27 August 2026, the red of
 *     C9 (`banchi/11-scatole/11-c9-il-registro-dice-di-chi.py`).
 *
 * ⛔ THE DEFECT, `[M]` with TWO tenants alive together: `webtransport.c` calls
 *    `tastiera_apri()` in the PARENT, to answer "does this layout
 *    exist?" during ATTACCA.  The lines coming out of it — «modificatore N:
 *    si preferisce…» and «disposizione in vigore: it [Italian]» — were
 *    **identical word for word, one per tenant**, and there was no way to
 *    tell which was whose.  ⇒ With a single tenant they were attributed by
 *    exclusion; with the second the diagnosis became guessing.
 *
 * ⭐ `chi` is the name PAM admitted on THIS session — in the parent it is
 *    carried by `rcp_utente()`, and it is the same that ends up in the `rcp` line two
 *    milliseconds later.  ⚠ NULL or "" ⇒ the PROCESS identity applies
 *    (`registro.h`), which is the right answer in the child; and if there is not
 *    even that the line comes out bare, ⛔ which is the truth.
 *
 * ⚠ And the old signature STAYS, instead of growing a parameter: it is used by
 *   `banchi/04-b25-tastiera.c`, and in this module by the two internal
 *   comparison openings (`tastiera_apri_da_keymap`, `tastiera_e_questa`) that
 *   run only in the child.  ⇒ Whoever has no tenant to name should not have to
 *   write `NULL` to say so.
 */
Tastiera *tastiera_apri_per(const char *disposizione, const char *chi, char **errore);

/*
 * ⛔⛔ AND THIS IS THE GOOD WAY — added on 14 August 2026, and it is not an
 *      extra: it is the correction of a defect of the contract, raised
 *      by the link that implemented it and accepted.
 *
 * The signature above rests on an assumption nobody had measured: that
 * the layout WE compile is the same with which the compositor
 * will interpret the codes we send it.  ⛔ It is fragile on the worst side,
 * because **we do not choose the session's layout: GNOME
 * chooses it, and `libei` HANDS it to us** with the keyboard device.
 *
 * The damage, concretely — `it` session, client that negotiated `us`, the user
 * types `[`:
 *
 *     on `us`   `[` is on key 26, alone
 *     on `it`   key 26 holds `è`, and `[` wants AltGr
 *
 * ⇒ We send 26 and **`è`** appears on screen.  ⛔ Not a missing character:
 *   **a DIFFERENT character** — exactly what `RCP.md` §7.3 forbids.  And
 *   nobody would ever connect the symptom to the layout.
 *
 * ⚠ And it makes false a line we believed true: `DECISIONI.md` §5-bis.7 says
 *   the degradation is soft — "an old layout never produces
 *   wrong characters".  ⛔ It is true ONLY using the session's keymap.
 *
 * ⭐ And v1 already did it this way (`fondamenta/remotix-c/src/tastiera.c:69`): it is the only
 *    piece of v1 the first V2 contract had not taken over.
 *
 * `testo`/`lunghezza` are the keymap `libei` carries with the keyboard device
 * (`ei_device_keyboard_get_keymap`, `XKB_KEYMAP_FORMAT_TEXT_V1`).
 * `negoziata` is the name declared by the client in `ATTACCA` (`RCP.md` §4.5), or
 * NULL.  ⛔ If it does not match the session's, **the session's** is used
 * — it is the truth, and with the other wrong letters would come out — and
 * the fallback is DECLARED in the log (`CODER.md` §4.2).
 *
 * ⛔ To be called at EVERY `DEVICE_ADDED`, not once at startup: `STUDI.md` §gnome §9
 *    measures that a keymap change destroys and recreates the keyboard device,
 *    and the old one stops working **without an error**.
 */
Tastiera *tastiera_apri_da_keymap(const char *testo, size_t lunghezza,
                                  const char *negoziata, char **errore);

/* How many key positions at most a letter needs (with the modifiers). */
#define TASTIERA_MAX_POSIZIONI 4

/*
 * ⛔ The question this module exists to answer.
 *
 * Searches, across the whole layout, for a key that with some combination of
 * modifiers produces `carattere`.
 *
 *   returns  1  producible: `codici[0..n)` are the EVDEV codes to press in
 *               order (the modifiers first, the key last) and they are
 *               released in reverse; `*n` is how many they are;
 *   returns  0  ⛔ NOT producible with this layout — it is the case that
 *               `RCP.md` §7.3 requires to be written to the log without sending
 *               anything.  The phase bench exercises it on purpose, with a
 *               session with the wrong layout;
 *   returns -1  error.
 *
 * ⚠ Shift and AltGr are NOT commands: they serve to MAKE the letter, and live in
 *   here (`SPECIFICHE.md` §7.3).  Ctrl, Alt and Super never pass through here:
 *   those already travel as key positions on the wire.
 */
int tastiera_posizioni_per(Tastiera *, uint32_t carattere,
                           uint16_t codici[TASTIERA_MAX_POSIZIONI], size_t *n);

/*
 * The name of the layout actually in force, for the log and for
 * the answer to the client.  Never NULL after a successful opening.
 */
const char *tastiera_disposizione(Tastiera *);

/*
 * ⛔⭐ "DOES THIS KEYMAP DO WHAT `nome` WOULD DO?" — and it serves not to ask twice
 *     for the same layout.
 *
 * ⚠ It comes from a defect MEASURED on 16 August 2026, and the defect was **the
 *   wrong memory**: `input_disposizione()` remembered *what it had
 *   asked for* and skipped the request if it matched.  ⛔ But between one request and
 *   the next the session's layout can change **at the hand of
 *   someone else** — the user from GNOME's settings, or `gsd-keyboard`.
 *   ⇒ The bench caught it red-handed: session brought back to `it` from outside,
 *     client reattaching declaring `de`, and the log said
 *     *«layout «de»: already requested, I do not request it again»* — with the session
 *     Italian.  `Ctrl+Z` arrived as `Ctrl+Y`.
 *
 * ⛔ It is form **E1** — *written is not in force* — inside the cure written
 *    for §5-bis.7.  ⇒ The right question is not "what did I ask for?" but
 *    **"what is there now?"**, and this keymap knows the answer.
 *
 * ⚠ And the comparison is the usual one: two layouts are the same if
 *   **they produce the same characters on the same keys**, not if they are called
 *   the same way (see the box of `fanno_la_stessa_cosa` in the `.c`).
 *
 *   returns  1  yes, this keymap does what `nome` would do
 *   returns  0  no
 *   returns -1  ⛔ it could not be said (a name that does not compile, or NULL) —
 *               and it is NOT "no": the caller must be able to tell them apart.
 */
int tastiera_e_questa(Tastiera *, const char *nome);

void tastiera_chiudi(Tastiera *);

#endif /* REMOTIX_TASTIERA_H */
