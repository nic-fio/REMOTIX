/*
 * registro.h — the lines the server writes, and the only place that writes them.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY A MODULE AND NOT A `printf`
 *
 * `CODER.md` §6: «declare fallbacks and degradations in the log, so that the
 * reviewer can tell an intended behaviour from an accidental one».  A log
 * scattered over twenty `fprintf(stderr, ...)` has neither a timestamp nor an
 * area, and those two things are what make a line readable to whoever hunts a
 * defect six hours later.
 *
 * ⛔ AND B13.2 LOOKS INSIDE THIS FILE: «that the password is in no log».
 *    Going through a single funnel is what makes the check possible — with
 *    twenty print points, «it is not there» would be a hope.
 */
#ifndef REMOTIX_REGISTRO_H
#define REMOTIX_REGISTRO_H

#include <stdbool.h>
#include <stdint.h>

/* The area that writes the line.  It serves to read the log by column when
 * the transport and the protocol speak together. */
#define REG_AVVIO "avvio"
#define REG_QUIC "quic"
#define REG_WT "wt"
#define REG_RCP "rcp"
#define REG_PAGINA "pagina"
#define REG_CERT "cert"
/* ⭐ The two areas of phase 2, grafted on 12 Aug 2026 by the assembly.
 * ⚠ `REG_SESSIONE` stood at the top of `src/sessione.h` with a note next to it
 *   declaring it provisional, because that file was born before entering the
 *   `Makefile` (`P2-1-sessione.md` §6.2 asks for this line). */
#define REG_SESSIONE "sessione"
#define REG_VIDEO "video"
/* ⭐ The area of phase 10 (25 Aug 2026): the composition budget.  ⚠ It has
 *   an area of its own and not `avvio` because it writes at three different
 *   moments — the line of the value in force, the verdict on whoever knocks,
 *   and the refusal — and whoever looks for *«why that user was turned away»*
 *   must be able to read a single column instead of sifting `wt` and `figlio`. */
#define REG_BUDGET "budget"

/* ⭐ The four functions that write are MACROS over four `_in`: the macro adds
 *    `__FILE__` and `__LINE__`, which go to the journal as
 *    `CODE_FILE`/`CODE_LINE` (phase 16 §12).  ⚠ They do not appear on the
 *    `stderr` line: that stays byte for byte as it was. */
void registro_dice_in(const char *file, int linea, const char *area,
                      const char *fmt, ...)
	__attribute__((format(printf, 4, 5)));
#define registro_dice(...) registro_dice_in(__FILE__, __LINE__, __VA_ARGS__)

/* The transport's detail lines: many, and useful only when one is looking for
 * something.  Off by default. */
void registro_parlantina(bool acceso);
bool registro_parla_molto(void);
void registro_dettaglio_in(const char *file, int linea, const char *area,
                           const char *fmt, ...)
	__attribute__((format(printf, 4, 5)));
#define registro_dettaglio(...) \
	registro_dettaglio_in(__FILE__, __LINE__, __VA_ARGS__)

/*
 * ---------------------------------------------------------------------------
 * ⭐⭐ THE SYSTEM JOURNAL — phase 16 §12, 25 Sep 2026.
 *
 * With `--journal` every line ALSO goes to the systemd journal, with the native
 * protocol (one `KEY=value` datagram on `/run/systemd/journal/socket`, without
 * libsystemd), with the fields needed for filtering:
 *
 *      MESSAGE            the line without the time (the journal adds the time)
 *      PRIORITY           3 if the body starts with ⛔, 4 with ⚠, 7 for the
 *                         chatter, 6 everything else
 *      SYSLOG_IDENTIFIER  remotix        (⇒ `journalctl -t remotix`)
 *      REMOTIX_AREA       the area       (⇒ `REMOTIX_AREA=rcp`)
 *      REMOTIX_INQUILINO  the identity, only if the line has one
 *      CODE_FILE/LINE     who wrote it
 *
 * ⛔ The line on `stderr` does NOT change and is NOT turned off: the journal is
 *    ADDED.  The benches read the file, and a journal that does not answer
 *    (full, stuck, absent in a container) must not cost even one line.  ⇒ One
 *    non-blocking `sendmsg` per line, and if it fails it stays silent.
 * ⚠ It does not cross the `exec`: the child receives it as `--journal` on its
 *   command line, like `--parlantina` (`figlio.c`, `diventa_ed_esegui()`).
 * ⚠ And the child, after `pam_systemd`, sits in the SESSION scope and not in
 *   the server's unit: ⇒ `journalctl -t remotix`, not only `-u`.
 *
 * Returns false if the socket does not open (and then the journal stays off).
 */
bool registro_journal(bool acceso);
bool registro_nel_journal(void);

/*
 * ⛔⛔ KEYS IN THE LOG — phase 16 §12: «keystrokes are logged as "key", never
 *      as a character».  An evdev code IS a character, up to the layout: a
 *      row of `evdev code 30, 48, 46` is a word.
 *
 * ⭐ Except the modifiers (Ctrl, Shift, Alt, Meta, CapsLock): they say nothing
 *    about what is being typed, and they are precisely the ones that stay down
 *    and make the desktop unusable (`RCP.md` §11) — whoever investigates needs
 *    to know WHICH.  ⇒ This is the only question a caller must ask before
 *    writing a key code; the answer lives in one place only.
 */
bool registro_tasto_dicibile(unsigned codice_evdev);

/*
 * ---------------------------------------------------------------------------
 * ⛔⛔ WHOSE LINE IS IT — 25 Aug 2026, finding R10-A4, `fasi/10-…md` §6.7.
 *
 * ⛔ THE DEFECT, MEASURED and not deduced: with **four** real GNOME sessions
 *    (57 121 lines, 90 s at steady state) only **4.2 %** of the DIAGNOSTIC
 *    lines said whom they were about; `fotogramma-spedito`, `ciclo-cattura`
 *    and `audio-blocchi` — the three biggest families — **0.0 %**.  With one
 *    scene out of four turned off, one *saw* that a series had stopped 2 times
 *    out of 4, ⛔ but the log said a NAME **0 times out of 4** — and whoever
 *    tried to guess it was wrong **96 times out of 100**, that is sent people
 *    to look at **someone else's desktop**.
 *
 * ⭐ The identity arrives by two roads, and they are two because the processes
 *    are of two kinds — it is the whole reason for the design:
 *
 *      · `registro_identita()` — ⭐ set by the process that serves **ONE**
 *        session only: the child, which knows its own user from the `exec`
 *        on (`figlio.c`, `argv[2]`).  ⇒ From there on **every** line of that
 *        process carries it, including those of `codificatore.c` and of
 *        `audio.c`, which know nothing about sessions.
 *      · `registro_dice_di()` — ⭐ carried by the SINGLE line, in the process
 *        that serves **all** the sessions together: the parent.  There a
 *        process identity would always say the same thing, that is nothing.
 *
 * ⭐ And the identity is composed in ONE PLACE ONLY (`registro.c`, `riga()`),
 *    not by the caller: two places that write the bracket write it
 *    differently, and a reader who found two at the head of the same line
 *    would no longer know where the body begins.
 *
 * ⚠ AND WHOEVER DOES NOT KNOW STAYS SILENT: a line without identity goes out
 *   **without brackets**, not with empty brackets or with the neighbour's name.
 *   `[M]` §6.7: the classifier that guesses is wrong 96.4 % of the time, the
 *   prudent one that abstains is wrong **0 %**.  ⇒ «I do not know» is an
 *   outcome, and it is written by not writing.
 *
 * ⛔ 48 is the ceiling: the bracket sits at the head of the line's BODY, and a
 *    long identifier would eat the message.  Whatever is longer is cut.
 */
#define REG_IDENTITA_MAX 48

/* The identity of THIS process, from here to the end.  `NULL` or "" removes it.
 * ⚠ It does not cross the `exec`: it is a static of the process, and the child
 *   sets it again as soon as it has read its own `argv`. */
void registro_identita(const char *chi);

/* The line of ONE session, written by a process that serves many.
 * ⚠ `chi` NULL or "" ⇒ the process identity applies; if there is not even that,
 *   the line goes out mute, which is the truth. */
void registro_dice_di_in(const char *file, int linea, const char *area,
                         const char *chi, const char *fmt, ...)
	__attribute__((format(printf, 5, 6)));
#define registro_dice_di(...) \
	registro_dice_di_in(__FILE__, __LINE__, __VA_ARGS__)
void registro_dettaglio_di_in(const char *file, int linea, const char *area,
                              const char *chi, const char *fmt, ...)
	__attribute__((format(printf, 5, 6)));
#define registro_dettaglio_di(...) \
	registro_dettaglio_di_in(__FILE__, __LINE__, __VA_ARGS__)

/* Milliseconds from a monotonic clock — the time RCP wants. */
uint64_t registro_ora_ms(void);

#endif
