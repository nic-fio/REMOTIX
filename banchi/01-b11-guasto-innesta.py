#!/usr/bin/env python3
"""01-b11-guasto-innesta.py — ⛔ THE SERVER FAULTY ON PURPOSE, for B11.

    python3 01-b11-guasto-innesta.py            grafts the faults
    python3 01-b11-guasto-innesta.py --togli    removes them

⚠ Runs INSIDE the container, AFTER `01-b3-rcp-innesta.py`: it touches the COPY of
  `rcp.c` that sits in `examples/`, not the original in `banchi/rcp/`.

===========================================================================
⛔ WHY A FAULTY SERVER, AND WHY IT IS THROWN AWAY

`FASI.md` §01-filo-nudo, B11, finding **R4.1**: the first draft of the bench had
twelve violations towards the server and **none towards the page**.  But `RCP.md`
§3 is written about "an RCP implementation", and §9 has an **explicit MUST of the
client**.  ⭐ To prove that the page applies §3 one has to **send it something
wrong**, and the only one who can do it is a server that gets it wrong on purpose.

⛔ And these lines **do not stay**: a switch that makes the server lie, if it
   survives the phase, will one day be found turned on by someone who did not know
   it existed.  They are here, in a graft that is removed, and `--togli` takes
   them all away.

===========================================================================
⭐ HOW THE FAULT IS CHOSEN: FROM THE `CIAO`, NOT FROM THE COMMAND LINE

The fault arrives in the **`banco.guasto`** capability of the `CIAO`.  ⭐ This way the
twelve cases run on **a single server turned on** and in **a single load
of the page**: without it, every case would want a restart, and twelve restarts for two
engines are twenty-four chances of measuring a server different from the one
we believe.

⚠ And the name is unknown to RCP/1, so a HEALTHY server ignores it (§4.3,
  the exception for unknown names): the B11 page can be pointed also
  at the real server, and there the twelve cases must all fail — which is the
  check that says **no**.
"""
import os
import subprocess
import sys

ESEMPI = "/srv/src/b2/ngtcp2/examples"
MARCA = "REMOTIX B11 GUASTO"

INNESTI = [
    # ── 1. The field that holds the name of the fault ──────────────────────
    (
        "rcp.c",
        "\tchar audio[32];\n",
        "\tchar audio[32];\n"
        "\t/* ⚠ REMOTIX B11 GUASTO — the fault requested by the client, thrown away with"
        " the graft. */\n"
        "\tchar guasto[64];\n",
        "the fault field",
    ),
    # ── 2. The capture, from the CIAO ──────────────────────────────────────
    (
        "rcp.c",
        '\t\tif (strcmp(nome, "video.codec") == 0)\n',
        '\t\t/* ⚠ REMOTIX B11 GUASTO — `banco.guasto` does not exist in RCP/1: a healthy\n'
        '\t\t * server ignores it like any unknown name (§4.3). */\n'
        '\t\tif (strcmp(nome, "banco.guasto") == 0) {\n'
        '\t\t\tsnprintf(s->guasto, sizeof s->guasto, "%s", valore);\n'
        '\t\t\treg(s, "⚠ B11 GUASTO: fault requested by the client: %s", s->guasto);\n'
        '\t\t}\n'
        '\t\tif (strcmp(nome, "video.codec") == 0)\n',
        "the capture of the fault",
    ),
    # ── 3. ECCOMI, in its three crooked guises ─────────────────────────────
    (
        "rcp.c",
        "\tsc_u16(&w, RCP_VERSIONE);\n\tsc_u16(&w, 5); /* how many capabilities */\n",
        "\t/* ⚠ REMOTIX B11 GUASTO — three faults inside ECCOMI:\n"
        "\t *   eccomi-versione-2         a HIGHER version than the one\n"
        "\t *                             requested: §9 obliges the CLIENT to\n"
        "\t *                             say farewell with VERSIONE_INCOMPATIBILE\n"
        "\t *   capacita-sconosciuta      a name that does not exist: the page\n"
        "\t *                             MUST ignore it and go on\n"
        "\t *   misura-massima-in-eccomi  a CLIENT capability sent by the\n"
        "\t *                             SERVER: known name, wrong\n"
        "\t *                             side, ERRORE_PROTOCOLLO */\n"
        "\tbool g_ver = strcmp(s->guasto, \"eccomi-versione-2\") == 0;\n"
        "\tbool g_ign = strcmp(s->guasto, \"capacita-sconosciuta\") == 0;\n"
        "\tbool g_lato = strcmp(s->guasto, \"misura-massima-in-eccomi\") == 0;\n"
        "\tsc_u16(&w, g_ver ? 2 : RCP_VERSIONE);\n"
        "\tsc_u16(&w, 5 + (g_ign ? 1 : 0) + (g_lato ? 1 : 0));\n",
        "the three faults of ECCOMI",
    ),
    (
        "rcp.c",
        # ⚠ The foothold changed on 10 Aug 2026, with the cure of finding
        #   R9.14: `ECCOMI` no longer declares `banco.marca=no` written by hand,
        #   but reads `BANCO_ACCESO`.  ⛔ And the bench noticed by itself: it
        #   counted ZERO occurrences and refused to build a half-faulty
        #   server — which is exactly what the cure of R5.17 added
        #   so that it would happen.
        '\tsc_str(&w, "banco.marca");\n\tsc_str(&w, BANCO_ACCESO ? "si" : "no");\n',
        '\tsc_str(&w, "banco.marca");\n\tsc_str(&w, BANCO_ACCESO ? "si" : "no");\n'
        '\tif (g_ign) {\n'
        '\t\tsc_str(&w, "questa.non.esiste");\n'
        '\t\tsc_str(&w, "boh");\n'
        '\t}\n'
        '\tif (g_lato) {\n'
        '\t\tsc_str(&w, "video.misura_massima");\n'
        '\t\tsc_str(&w, "3840x2160");\n'
        '\t}\n',
        "the two crooked capabilities",
    ),
    # ── 4. A type that does not exist, right after ECCOMI ──────────────────
    (
        "rcp.c",
        "\tmanda_eccomi(s);\n\ts->stato = S_ATTESA_CREDENZIALI;\n",
        "\tmanda_eccomi(s);\n"
        "\t/* ⚠ REMOTIX B11 GUASTO — an unknown type on the control channel: §3\n"
        "\t *   forbids ignoring it, and the page must close. */\n"
        "\tif (strcmp(s->guasto, \"tipo-sconosciuto\") == 0) {\n"
        "\t\tuint8_t niente[1] = {0};\n"
        "\t\tmanda_messaggio(s, 0x00FF, niente, 0);\n"
        "\t}\n"
        "\ts->stato = S_ATTESA_CREDENZIALI;\n",
        "the unknown type",
    ),
    # ── 5. SESSIONE: odd canvas and lying desktop ──────────────────────────
    (
        "rcp.c",
        '\tsc_byte(&w, 1); /* 1 = NUOVA */\n\tsc_u32(&w, tl);\n\tsc_u32(&w, ta);\n'
        '\tsc_str(&w, "sconosciuto"); /* il desktop: in fase 1 non c\'e\' compositore */\n'
        '\tif (!w.pieno)\n\t\tmanda_messaggio(s, T_SESSIONE, corpo, w.len);\n',
        '\t/* ⚠ REMOTIX B11 GUASTO — two faults inside SESSIONE:\n'
        '\t *   sessione-tela-dispari   the GRANTED canvas is odd: the page\n'
        '\t *                           must REFUSE, not adapt\n'
        '\t *   sessione-desktop-*      a desktop that is not the real one: §4.5\n'
        '\t *                           forbids the page to change\n'
        '\t *                           behaviour based on this field */\n'
        '\tbool g_disp = strcmp(s->guasto, "sessione-tela-dispari") == 0;\n'
        '\tconst char *g_desk = "sconosciuto";\n'
        '\tif (strcmp(s->guasto, "sessione-desktop-kde") == 0)\n'
        '\t\tg_desk = "kde";\n'
        '\telse if (strcmp(s->guasto, "sessione-desktop-gnome") == 0)\n'
        '\t\tg_desk = "gnome";\n'
        '\tsc_byte(&w, 1); /* 1 = NUOVA */\n'
        '\tsc_u32(&w, g_disp ? tl + 1 : tl);\n'
        '\tsc_u32(&w, g_disp ? ta + 1 : ta);\n'
        '\tsc_str(&w, g_desk);\n'
        '\tif (!w.pieno)\n\t\tmanda_messaggio(s, T_SESSIONE, corpo, w.len);\n'
        '\t/* ⚠ REMOTIX B11 GUASTO — a CONGEDO with reason 0x00, which §3.1 forbids. */\n'
        '\tif (strcmp(s->guasto, "congedo-motivo-zero") == 0) {\n'
        '\t\tuint8_t c0[8];\n'
        '\t\tscrittore w0 = {c0, sizeof c0, 0, false};\n'
        '\t\tsc_byte(&w0, 0);\n'
        '\t\tsc_str(&w0, "");\n'
        '\t\tmanda_messaggio(s, T_CONGEDO, c0, w0.len);\n'
        '\t}\n',
        "the faults of SESSIONE",
    ),
    # ── 6. A CONGEDO after RESPINTO, which §4.4 forbids ────────────────────
    (
        "rcp.c",
        "\tmanda_messaggio(s, T_RESPINTO, corpo, 1);\n"
        "\ts->stato = S_FINITA;\n"
        "\ts->g.chiudi(s->g.ctx, motivo);\n",
        "\tmanda_messaggio(s, T_RESPINTO, corpo, 1);\n"
        "\t/* ⚠ REMOTIX B11 GUASTO — §4.4: after RESPINTO nothing else arrives.  Here\n"
        "\t *   something does, and the page must notice. */\n"
        "\tif (strcmp(s->guasto, \"respinto-poi-congedo\") == 0) {\n"
        "\t\tuint8_t c1[8];\n"
        "\t\tscrittore w1 = {c1, sizeof c1, 0, false};\n"
        "\t\tsc_byte(&w1, RCP_ERRORE_PROTOCOLLO);\n"
        "\t\tsc_str(&w1, \"\");\n"
        "\t\tmanda_messaggio(s, T_CONGEDO, c1, w1.len);\n"
        "\t\t/* ⛔⭐ AND HERE THE FAULT DOES NOT CLOSE, AND IT IS THE DIFFERENCE BETWEEN A\n"
        "\t\t *   MEASUREMENT AND A COIN TOSS.\n"
        "\t\t *\n"
        "\t\t *   The closing of §3.1 would start right behind the message, and\n"
        "\t\t *   would race against the page's answer: on 10 Aug 2026\n"
        "\t\t *   Chrome lost that race in one round out of five and\n"
        "\t\t *   declared `congedo:0x00` instead of `0x0b`.  ⚠ A bench that\n"
        "\t\t *   changes verdict between two identical rounds does not measure the page:\n"
        "\t\t *   it measures the load of the machine.\n"
        "\t\t *\n"
        "\t\t * ⭐ What this case wants to see is the page's REACTION\n"
        "\t\t *    to a message that §4.4 forbids — and to see it one must\n"
        "\t\t *    leave it the time to have it.  It will be the page that closes, with its\n"
        "\t\t *    `CONGEDO`; if it does not, the silence of §2.2 remains. */\n"
        "\t\ts->stato = S_FINITA;\n"
        "\t\treturn;\n"
        "\t}\n"
        "\t/* ⛔⭐ AND THE SAME HOLDS FOR `respinto-non-riprovare` — finding\n"
        "\t *   R12-A.47, 11 Aug 2026, and the reason is written two lines\n"
        "\t *   above: the closing starts right behind the RESPINTO and RACES\n"
        "\t *   against the page's reader.\n"
        "\t *\n"
        "\t *   `[M]` 11 Aug, Firefox 140.13.0esr: the page did not even\n"
        "\t *   reach the RESPINTO branch — it saw the stream fall and\n"
        "\t *   declared `canale-rotto` where the expected says `muta`.  ⚠ And the\n"
        "\t *   page was RIGHT: telling a FIN from a fall is the\n"
        "\t *   cure of finding R6.12, and here the server sends no FIN —\n"
        "\t *   it closes the SESSION with CLOSE_WEBTRANSPORT_SESSION.\n"
        "\t *\n"
        "\t * ⭐ What this case wants to see is that after `RESPINTO` the\n"
        "\t *    page DOES NOT RETRY (§4.4).  To see it one must leave it the\n"
        "\t *    time not to do it: we keep quiet, and it will be the page that closes.\n"
        "\t * ⛔ It is not widening the expected: the expected stays `muta`, and the case\n"
        "\t *    can still say no — if the page retried, the extra bytes\n"
        "\t *    would be seen by the SERVER log, which is the witness\n"
        "\t *    this case has always declared (§8.1). */\n"
        "\tif (strcmp(s->guasto, \"respinto-non-riprovare\") == 0) {\n"
        "\t\ts->stato = S_FINITA;\n"
        "\t\treturn;\n"
        "\t}\n"
        "\ts->stato = S_FINITA;\n"
        "\ts->g.chiudi(s->g.ctx, motivo);\n",
        "the farewell after the refusal",
    ),
    # ── 7. The accessor for the host: two faults live in the STREAMS ───────
    (
        "rcp.c",
        "const char *rcp_utente(const rcp_sessione *s) { return s ? s->utente : \"\"; }\n",
        "const char *rcp_utente(const rcp_sessione *s) { return s ? s->utente : \"\"; }\n"
        "/* ⚠ REMOTIX B11 GUASTO — two faults out of twelve are not in the messages but\n"
        " *   in the STREAMS: a FIN on the control channel and a bidirectional\n"
        " *   stream opened by the server.  Only the host can do those,\n"
        " *   and this line is the only thing it needs to know. */\n"
        "const char *rcp_guasto(const rcp_sessione *s) { return s ? s->guasto : \"\"; }\n",
        "the fault accessor",
    ),
    # ── 8. The host: the FIN and the bidirectional stream ──────────────────
    (
        "http3_server_proto_codec.cc",
        "bool rcp_autentica(const char *utente, const char *parola);\n}\n",
        "bool rcp_autentica(const char *utente, const char *parola);\n"
        # ⚠ `const rcp_sessione *`, not `const struct rcp_sessione *`: rcp.h already
        #   declares it with a typedef, and in C++ repeating `struct` on a
        #   typedef is an error.  The first round of 10 Aug 2026 died
        #   here — and ⛔ the bench did not notice, because it checked that the
        #   binary EXISTED instead of that it was NEW.
        "const char *rcp_guasto(const rcp_sessione *s); // REMOTIX B11 GUASTO\n"
        "}\n",
        "the declaration of the fault",
    ),
    (
        "http3_server_proto_codec.cc",
        "  auto stato = std::string_view{rcp_stato_nome(rcp_)};\n",
        "  // ⚠ REMOTIX B11 GUASTO — the two faults that live in the streams, and\n"
        "  //   arm themselves when the session is open.\n"
        "  if (rcp_ && std::string_view{rcp_stato_nome(rcp_)} == \"attiva\" &&\n"
        "      !b11_fatto_) {\n"
        "    auto g = std::string_view{rcp_guasto(rcp_)};\n"
        "    if (g == \"fin-sul-controllo\") {\n"
        "      // ⛔ §4.2: the FIN on the control channel IS the end of the\n"
        "      //    session, and the page must no longer send on ANY\n"
        "      //    channel.  Here the WebTransport session is not closed: only\n"
        "      //    the stream is closed, so the bench measures the rule and\n"
        "      //    not the fall of the transport.\n"
        "      b11_fatto_ = true;\n"
        "      std::println(stderr, \"REMOTIX B11 GUASTO: FIN on the control channel\");\n"
        "      wt_uscita_.push_back(WtUscita{rcp_stream_, {}, 0, true});\n"
        "    } else if (g == \"bidi-dal-server\") {\n"
        "      // ⛔ §2.5: \"the server MUST NOT open bidirectional streams\".\n"
        "      b11_fatto_ = true;\n"
        "      int64_t sid = -1;\n"
        "      if (ngtcp2_conn_open_bidi_stream(conn_, &sid, nullptr) == 0) {\n"
        "        std::println(stderr,\n"
        "                     \"REMOTIX B11 GUASTO: opened a BIDIRECTIONAL stream {} \"\n"
        "                     \"towards the client\", sid);\n"
        "        std::array<uint8_t, 3> t{0x40, 0x41, 0};\n"
        "        t[2] = static_cast<uint8_t>(wt_sessione_);\n"
        "        wt_uscita_.push_back(WtUscita{\n"
        "          sid, std::vector<uint8_t>{t.begin(), t.end()}, 0, false});\n"
        "      }\n"
        "    }\n"
        "  }\n"
        "  auto stato = std::string_view{rcp_stato_nome(rcp_)};\n",
        "the two faults of the streams",
    ),
    (
        "http3_server_proto_codec.h",
        "  std::unordered_map<int64_t, bool> wt_uni_;\n",
        "  std::unordered_map<int64_t, bool> wt_uni_;\n"
        "  bool b11_fatto_{false}; // ⚠ REMOTIX B11 GUASTO — one fault per session\n",
        "the state of the fault",
    ),
]


def leggi(percorso):
    """The text of a file of `examples/`, or `None` if it is not there.

    ⛔ "It is not there" and "I could not read it" are not the same thing.  The
       first is a legitimate fact — `01-b3-rcp-innesta.py --togli` deletes
       `rcp.c` from `examples/` — the second is an error, and must reach the
       bench instead of looking like a zero.
    """
    try:
        with open(os.path.join(ESEMPI, percorso), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def scrivi(percorso, testo):
    with open(os.path.join(ESEMPI, percorso), "w", encoding="utf-8") as f:
        f.write(testo)


def marche_attese():
    """How many times the mark must appear in each file once the graft is done.

    ⭐ The number is COMPUTED by the table, not written by a hand: it is the
       denominator that `01-b11-guasto.sh` compares with the disk after the
       compilation, and a denominator written by hand ages with the first
       graft someone adds.
    """
    conto = {}
    for percorso, _appiglio, sostituto, _nome in INNESTI:
        conto[percorso] = conto.get(percorso, 0) + sostituto.count(MARCA)
    return conto


def togli():
    """⛔ AND IT REALLY REMOVES.

    Until 10 Aug 2026 this branch printed three lines and returned **0**
    without opening a file: `--togli && grep -c 'REMOTIX B11 GUASTO'
    examples/rcp.c` exited 0 and printed 7.  ⚠ It is the defect already paid for on
    `01-b3-rcp-innesta.py --togli` — a command that declares it removes, does not
    remove, and returns success — rewritten here in pure form.  That nobody
    called it did not make it harmless: the usage line at the top of this file is
    what whoever finds it six months from now will read.
    """
    print("== Removing the B11 faults")
    testi, originali, tolti = {}, {}, 0
    # ⛔ In REVERSE order to how they were put in: a substitute can contain
    #    the foothold of another, and undoing backwards is the only order that
    #    leaves no half grafts.
    for percorso, appiglio, sostituto, nome in reversed(INNESTI):
        if percorso not in testi:
            testi[percorso] = originali[percorso] = leggi(percorso)
        if testi[percorso] is None:
            print(f"   --  {nome:32s} {percorso} is not there: nothing to remove")
            continue
        n = testi[percorso].count(sostituto)
        if n == 0:
            print(f"   --  {nome:32s} was not there")
            continue
        testi[percorso] = testi[percorso].replace(sostituto, appiglio)
        tolti += 1
        print(f"   OK  {nome:32s} removed {n} time(s)  [{percorso}]")

    scritti = 0
    for percorso, testo in testi.items():
        if testo is not None and testo != originali[percorso]:
            scrivi(percorso, testo)
            scritti += 1

    # ⛔ AND IT IS VERIFIED FROM THE SIDE THAT COUNTS: the file on disk, not the intention
    #    of whoever wrote the substitution.
    resti = {}
    for percorso in testi:
        testo = leggi(percorso)
        if testo and MARCA in testo:
            resti[percorso] = testo.count(MARCA)
    print(f"\n   {tolti} grafts removed, {scritti} files rewritten")
    if resti:
        for percorso, n in resti.items():
            print(f"   NO  {percorso}: {n} marks «{MARCA}» remain")
        print("   ⛔ a server that lies on purpose must NOT survive")
        print("      the phase: put back the B2 and B3 grafts from scratch.")
        return 1
    print(f"   ⭐ no mark «{MARCA}» in the files of examples/")
    return 0


def innesta():
    print("== The B11 faults — lines that must NOT survive the phase")
    testi = {}
    for percorso in dict.fromkeys(p for p, *_ in INNESTI):
        testi[percorso] = leggi(percorso)
        if testi[percorso] is None:
            print(f"   ⛔ {percorso} is not in {ESEMPI}: the B2 and")
            print("      B3 grafts must be applied BEFORE this one.")
            return 1
    originali = dict(testi)

    applicati, gia, guasti = 0, 0, 0
    for percorso, appiglio, sostituto, nome in INNESTI:
        # ⛔ THE GUARD ASKS WHETHER THIS GRAFT IS THERE, not whether there is A mark.
        #
        #    It was `MARCA in testo and appiglio not in testo`, and three grafts out of
        #    eleven keep their own foothold INSIDE the substitute, by
        #    construction: the fault field, the capture from the `CIAO` and
        #    the `rcp_guasto` accessor.  On an already faulty `rcp.c` the foothold
        #    was still there, the guard was false, `n` was 1 and the graft **was
        #    reapplied**: `char guasto[64];` declared twice (compilation
        #    error, that is a red without a name), or — if it passed — the
        #    line "fault requested by the client" written twice by chance, which
        #    doubles the counts of `01-b11-lancia.sh` and pins on the PAGE
        #    a red that belongs to the graft.
        # ⭐ The substitute is the only thing that can say "this graft is
        #    already there", because it is exactly what was written on disk.
        if sostituto in testi[percorso]:
            gia += 1
            print(f"   ⚠  {nome:32s} already there  [{percorso}]")
            continue
        n = testi[percorso].count(appiglio)
        stato = "OK " if n == 1 else "NO "
        print(f"   {stato} {nome:32s} foothold found {n} time(s)  [{percorso}]")
        if n != 1:
            guasti += 1
            continue
        testi[percorso] = testi[percorso].replace(appiglio, sostituto, 1)
        applicati += 1

    if guasti:
        print(f"\n   ⛔ {guasti} footholds not found: NOTHING is written.")
        print("      A half graft produces a server that gets it wrong in a")
        print("      way different from the one the bench believes it is measuring.")
        return 1

    scritti = [p for p in testi if testi[p] != originali[p]]
    for percorso in scritti:
        scrivi(percorso, testi[percorso])

    # ⛔ AND WHAT IS ON DISK IS COUNTED, not what the table says.
    #
    #    `print(f"OK {len(INNESTI)} guasti innestati in {len(testi)} file")`
    #    printed a CONSTANT (11) and the number of files **read**: on a tree
    #    where all the grafts took the "already there" branch it declared "OK
    #    11 guasti innestati in 3 file" with zero substitutions, and returned 0.
    #    ⚠ A count that cannot be zero is not a count: it is a
    #      caption (`LEZIONI.md` §1.9).
    attese = marche_attese()
    male = 0
    for percorso, atteso in attese.items():
        vero = (leggi(percorso) or "").count(MARCA)
        stato = "OK " if vero == atteso else "NO "
        print(f"   {stato} {percorso:34s} marks on disk: {vero}  (expected {atteso})")
        if vero != atteso:
            male += 1
    print(f"\n   {applicati} grafts applied, {gia} were already there, out of"
          f" {len(INNESTI)}; {len(scritti)} files rewritten")
    if male:
        print("   ⛔ the disk does not say what the table declares: nothing")
        print("      is turned on, or a server is measured different from the one")
        print("      the bench believes it has built.")
        return 1
    # ⭐ The number that `01-b11-guasto.sh` compares with the disk after the
    #    compilation: computed here, printed here, and never written by hand over there.
    print(f"== B11-MARCHE-ATTESE: {sum(attese.values())}")
    print("   ⛔ and they are removed with --togli, or by putting back the B2 and B3 grafts")
    return 0


def main():
    if "--togli" in sys.argv:
        return togli()
    return innesta()


if __name__ == "__main__":
    sys.exit(main())
