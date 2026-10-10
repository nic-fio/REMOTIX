#!/usr/bin/env python3
"""01-b3-rcp-innesta.py — grafts RCP on top of the WebTransport layer of B2.

    python3 01-b3-rcp-innesta.py            grafts
    python3 01-b3-rcp-innesta.py --togli    puts the example back as it was

---------------------------------------------------------------------------
⛔ WHY IT IS A SECOND GRAFT AND NOT A GROWTH OF THE FIRST

`01-b2-ngtcp2-wt-innesta.py` measures one thing only: **how much glue
WebTransport costs on ngtcp2+nghttp3**, and it is the number on which `DECISIONI.md` §6.4
chose the library.  Growing it with RCP inside would make that number
incomprehensible six months from now: two different measurements under the same label,
that is form **E2**.

⭐ Here the glue is almost zero on purpose: **RCP lives in `banchi/rcp/`, in C, and
   does not know there is QUIC underneath**.  What this graft adds to the example
   is only the wires — and the fact that they are few is the proof that the module
   can be carried into the real server without rewriting it.

---------------------------------------------------------------------------
⛔ THE FIXED DELAY AND THE TIME THAT PASSES

`RCP.md` §4.4-bis imposes one second before answering `CREDENZIALI`,
**even when the answer is AMMESSO**.  A second in which the server has
nothing to send: if no timer fires, the answer never leaves.

⚠ That is why the host turns on the **QUIC keep-alive at 100 ms**: so the
  write path is walked anyway, and `rcp_tempo()` gets the chance to
  make delays and caps expire.  It is a wire of the host, not a rule of the
  protocol — that is why it is here and not in `rcp.c`.

⛔ And it is turned on in `rcp_avvia`, that is **when the RCP session is born**, not at the
   first byte that arrives.  `[M]` 10 Aug 2026, B6: armed only inside
   `rcp_passa`, the cap of the `CIAO` (§4.6 line 1) never expired — in the
   «attesa-ciao» state no byte has arrived yet, so
   nobody armed anything, so nobody called `rcp_tempo()` any more.

---------------------------------------------------------------------------
⛔⭐ AND SINCE 11 AUG 2026 IT ALSO GRAFTS THE HOST-SIDE BAN — `RCP.md` §4.4-bis

`rcp.c` can count failures, ban, save to file, say whether an address
is banned and remove a ban.  ⛔ But it opens no socket, does not read the command
line and serves no page: **the three things §4.4-bis asks of the
host did not exist**, and without them the user's rule was half
written.  Now they are in `server.cc`, in `CORPO_OSPITE`:

    --ban-file=<PATH>        the bans are reread at startup, and ⛔ "zero bans" and
                             "I could not read the file" are printed
                             DIFFERENTLY — on the second the server does not start
    the page over TCP        same port as the UDP (SPECIFICHE.md §4): whoever is
                             banned is served ALL THE SAME, with "attempts
                             exhausted" and the hours that are left
    --comando-socket=<PATH>  "SBLOCCA <address>" on a 0600 Unix socket —
                             the other way out besides the twelve hours

⚠ Whoever turns on this server **without** those two options does not lose the ban: they lose
  persistence and the command.  The server says so at startup, in two lines.
"""
import os
import shutil
import subprocess
import sys

ALBERO = "/srv/src/b2/ngtcp2"
ESEMPI = "/srv/src/b2/ngtcp2/examples"
SORGENTI = "/srv/src/rcp"
MARCA = "REMOTIX B3"
MARCA_B2 = "REMOTIX B2"
MARCA_B11 = "REMOTIX B11 GUASTO"

FILE_NOSTRI = ["rcp.c", "rcp.h", "autenticazione.c"]

# The files of the example this graft touches: `--togli` needs them to
# VERIFY it has removed, instead of returning 0 anyway.
#
# ⛔ `server.cc` came in on 11 Aug 2026 with the host-side ban: the three things
#    §4.4-bis asks of the HOST — loading the bans at startup, serving
#    the page to whoever is banned, removing a ban on command — live in `main`
#    and in the event loop, not in the codec.  ⚠ Whoever forgets it here leaves
#    `--togli` declaring "no trace" on a file that has a hundred.
FILE_TOCCATI = [
    "http3_server_proto_codec.cc",
    "http3_server_proto_codec.h",
    "CMakeLists.txt",
    "server.cc",
]

INNESTI = [
    # ── 0. ⛔ The RCP header, AT THE TOP ─────────────────────────────────────
    #    The first round of 10 Aug put it together with the body of the hooks, which
    #    sits halfway down the file: `rcp_tempo` was used at line 120 and declared
    #    at 1100.  A header goes where headers go.
    (
        "http3_server_proto_codec.cc",
        '#include "http3_server_proto_codec.h"\n',
        '#include "http3_server_proto_codec.h"\n'
        "\n"
        "// ⭐ REMOTIX B3 — the protocol is in C, and lives in banchi/rcp/.\n"
        'extern "C" {\n'
        '#include "rcp.h"\n'
        "bool rcp_autentica(const char *utente, const char *parola);\n"
        "}\n",
        "the RCP header",
    ),
    # ── 1. Our files in the build ───────────────────────────────────────────
    (
        "CMakeLists.txt",
        "  set(bsslserver_SOURCES\n",
        "  set(bsslserver_SOURCES\n"
        "    # ⭐ REMOTIX B3 — RCP and PAM.  They are OURS and are in C: the example\n"
        "    #    hosts them, it does not own them.\n"
        "    rcp.c\n"
        "    autenticazione.c\n",
        "the RCP files in the build",
    ),
    (
        "CMakeLists.txt",
        "  target_link_libraries(bsslserver ${bssl_LIBS})\n",
        "  target_link_libraries(bsslserver ${bssl_LIBS} pam)\n",
        "PAM among the libraries",
    ),
    # ── 2. The RCP state in the codec ───────────────────────────────────────
    (
        "http3_server_proto_codec.h",
        "  std::deque<WtUscita> wt_uscita_;\n"
        "  int64_t wt_sessione_{-1};\n",
        "  std::deque<WtUscita> wt_uscita_;\n"
        "  int64_t wt_sessione_{-1};\n"
        "\n"
        "  // ═══ ⭐ REMOTIX B3 — RCP on top of WebTransport ═══════════════════\n"
        "  // ⛔ The control channel is the FIRST bidirectional stream the\n"
        "  //    client opens inside the session (RCP.md §4.2), and its\n"
        "  //    closing IS the end of the session.\n"
        "  struct rcp_sessione *rcp_{nullptr};\n"
        "  int64_t rcp_stream_{-1};\n"
        "  void rcp_avvia(int64_t stream_id);\n"
        "  void rcp_passa(int64_t stream_id, std::span<const uint8_t> dati);\n"
        "\n"
        "  // ⛔ RCP.md §2.5 — the unidirectional streams opened by the CLIENT.  The\n"
        "  //    channel is read from the first two bytes, and three of the five values\n"
        "  //    are violations: 0x00 (control lives only on stream 0),\n"
        "  //    0x03 (video goes from server to client), 0x04 (audio lives\n"
        "  //    only on datagrams).\n"
        "  std::unordered_map<int64_t, bool> wt_uni_;\n"
        "\n"
        "  // ⛔ REMOTIX B11 — the closing of the session WAITS for the output\n"
        "  //    queue to have emptied: see `wt_chiudi_sessione`.\n"
        "  int wt_chiusura_{-1};\n"
        "  int wt_chiusura_attesa_{0};\n"
        "  WtEsito wt_smista_uni(int64_t stream_id, std::span<const uint8_t> data,\n"
        "                        std::vector<uint8_t> &riunito);\n",
        "the RCP state",
    ),
    # ── 3. The FIN in the output queue ──────────────────────────────────────
    (
        "http3_server_proto_codec.h",
        "  struct WtUscita {\n"
        "    int64_t stream_id;\n"
        "    std::vector<uint8_t> dati;\n"
        "    size_t off;\n"
        "  };\n",
        "  struct WtUscita {\n"
        "    int64_t stream_id;\n"
        "    std::vector<uint8_t> dati;\n"
        "    size_t off;\n"
        "    // ⭐ REMOTIX B3 — the capsule that closes the session must be sent with\n"
        "    //    the FIN: without it, the client keeps waiting for more bytes.\n"
        "    bool fin;\n"
        "  };\n",
        "the FIN in the output queue",
    ),
    # ── 4. The dispatch: the first WT stream is the control channel ─────────
    (
        "http3_server_proto_codec.cc",
        "    if (!data.empty()) {\n"
        "      wt_accoda(stream_id, data);\n"
        "      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());\n"
        "      ngtcp2_conn_extend_max_offset(conn_, data.size());\n"
        "    }\n",
        "    if (!data.empty()) {\n"
        "      // ⭐ REMOTIX B3 — on the control channel the bytes go to RCP.\n"
        "      //\n"
        "      // ⚠ On the other streams the B2 echo remains, which served the\n"
        "      //   transport bench — but with THIS graft on top, a second\n"
        "      //   bidirectional stream from the client is a violation of §2.5\n"
        "      //   that dismisses (see further down).  So the echo only applies to the\n"
        "      //   bytes already in flight while the session is falling: ⛔ the B2\n"
        "      //   transport bench is measured WITHOUT B3 grafted.\n"
        "      if (stream_id == rcp_stream_) {\n"
        "        rcp_passa(stream_id, data);\n"
        "      } else {\n"
        "        wt_accoda(stream_id, data);\n"
        "      }\n"
        "      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());\n"
        "      ngtcp2_conn_extend_max_offset(conn_, data.size());\n"
        "    }\n",
        "the control bytes towards RCP",
    ),
    (
        "http3_server_proto_codec.cc",
        "    wt_streams_[stream_id] = static_cast<int64_t>(sessione);\n"
        "    wt_incerti_.erase(stream_id);\n",
        "    wt_streams_[stream_id] = static_cast<int64_t>(sessione);\n"
        "    wt_incerti_.erase(stream_id);\n"
        "    // ⭐ REMOTIX B3 — RCP.md §4.2: the FIRST bidirectional stream the\n"
        "    //    client opens in the session is the control channel.\n"
        "    //\n"
        "    // ⚠ And \"the first\" HERE is the first RECOGNISED, not the first\n"
        "    //   OPENED: the two streams travel in different packets, and between\n"
        "    //   different streams the network promises no order.  The stream\n"
        "    //   number instead carries the order inside it — QUIC numbers them\n"
        "    //   in order of opening — and it is what is looked at to say\n"
        "    //   which of the two was the first (see the branch below).\n"
        "    if (rcp_stream_ == -1) {\n"
        "      rcp_avvia(stream_id);\n"
        "    } else {\n"
        "      // ⛔ REMOTIX B5 — RCP.md §2.5: \"the client MUST NOT open\n"
        "      //    bidirectional streams beyond 0\".  The control channel is ONE\n"
        "      //    ONLY for the whole session, and a second bidirectional one is not\n"
        "      //    a new channel: it is a violation.\n"
        "      //\n"
        "      // ⚠ Without this line the second stream ended up in the B2 ECHO and\n"
        "      //   the bytes came back: the client would have seen a server\n"
        "      //   answering it, and the violation would have passed for a\n"
        "      //   feature.\n"
        "      //\n"
        "      // ⛔ AND THE DIAGNOSIS MUST NOT BLAME THE ORDER OF ARRIVAL.  If\n"
        "      //    this stream has a LOWER number than the elected one, the\n"
        "      //    first opened was this one, and the network swapped them: the\n"
        "      //    bidirectional streams are still two — and two is the violation,\n"
        "      //    however they arrived — but \"a second stream\" said of the\n"
        "      //    lower number sends people looking for the defect in the client,\n"
        "      //    which got nothing wrong there.\n"
        "      if (stream_id < rcp_stream_) {\n"
        "        std::println(stderr,\n"
        "                     \"REMOTIX B5: ⛔ two bidirectional streams from the \"\n"
        "                     \"client inside the session: {} and {} — and the FIRST \"\n"
        "                     \"OPENED was {}, which arrived second: the \"\n"
        "                     \"control channel was elected by order of \"\n"
        "                     \"arrival, not by number\",\n"
        "                     rcp_stream_, stream_id, stream_id);\n"
        "      } else {\n"
        "        std::println(stderr,\n"
        "                     \"REMOTIX B5: ⛔ two bidirectional streams from the \"\n"
        "                     \"client inside the session: control is \"\n"
        "                     \"{}, and {} is one too many\",\n"
        "                     rcp_stream_, stream_id);\n"
        "      }\n"
        "      rcp_violazione(rcp_,\n"
        "                     \"two bidirectional streams from the client inside the \"\n"
        "                     \"session (§2.5)\");\n"
        "    }\n",
        "the first stream is the control",
    ),
    # ── 4-quater. ⛔ THE CLIENT'S UNIDIRECTIONAL STREAMS — §2.5 ──────────────
    #    B2 sent to nghttp3 everything that was not a bidirectional stream of the
    #    client, and nghttp3 has no use for a stream of type 0x54: it
    #    discards it silently.  ⛔ The result was that a client could send
    #    the control channel, the video or the audio on a unidirectional
    #    stream and **nothing happened** — that is, exactly
    #    the leniency §3 forbids, at a point where no bench was looking.
    (
        "http3_server_proto_codec.cc",
        # ⚠ The two comment lines of this foothold are text left by B2
        #   (`01-b2-ngtcp2-wt-innesta.py`), not by ngtcp2: they stay exactly as
        #   B2 writes them, here and in the copy below.
        "  // Only the bidirectional streams opened by the client: the extended CONNECT and the\n"
        "  // WebTransport streams all arrive from there.\n"
        "  if ((stream_id & 0x03) != 0x00) {\n"
        "    return WtEsito::HTTP3;\n"
        "  }\n",
        "  // ⛔ REMOTIX B5 — the unidirectional streams OPENED BY THE CLIENT (§2.5) pass\n"
        "  //    through here before anything else: among them are the HTTP/3 control\n"
        "  //    channel and the two QPACK ones, which belong to nghttp3, not to us.\n"
        "  if ((stream_id & 0x03) == 0x02) {\n"
        "    return wt_smista_uni(stream_id, data, riunito);\n"
        "  }\n"
        "  // Only the bidirectional streams opened by the client: the extended CONNECT and the\n"
        "  // WebTransport streams all arrive from there.\n"
        "  if ((stream_id & 0x03) != 0x00) {\n"
        "    return WtEsito::HTTP3;\n"
        "  }\n",
        "the client's unidirectional streams",
    ),
    (
        "http3_server_proto_codec.cc",
        "    if (!resto.empty()) {\n      wt_accoda(stream_id, resto);\n    }\n",
        "    if (!resto.empty()) {\n"
        "      if (stream_id == rcp_stream_) {\n"
        "        rcp_passa(stream_id, resto);\n"
        "      } else {\n"
        "        wt_accoda(stream_id, resto);\n"
        "      }\n"
        "    }\n",
        "the first bytes of the control",
    ),
    # ── 4-bis. ⛔ THE TIME THAT FLOWS ────────────────────────────────────────
    #    Without this call nobody invokes `rcp_tempo()`, and the
    #    fixed delay of §4.4-bis NEVER expires: the handshake stops
    #    after ECCOMI and the client times out.  ⚠ Seen at the first round of
    #    10 Aug 2026 — the module was right, the wire was missing.
    (
        "http3_server_proto_codec.cc",
        # ⚠ The foothold is no longer ngtcp2's bare text: it is what B2
        #   left us, which between the declaration of `vec` and the loop resets
        #   `wt_coda_bloccata_`.  ⛔ A foothold shared between two grafts must be
        #   reread every time the first of the two changes, or the second counts
        #   zero and stops blaming ngtcp2.
        # ⚠ And the B2 comment inside it stays exactly as B2 writes it, here and
        #   in the copy below.
        "  std::array<nghttp3_vec, 16> vec;\n"
        "\n"
        "  // ⭐ REMOTIX B2 — a write pass starts here, and our queue\n"
        "  //    restarts UNBLOCKED: `wt_coda_bloccata_` holds for one\n"
        "  //    pass only.  ⚠ It is outside the loop on purpose — resetting it\n"
        "  //    inside would put the same element back in play at every round,\n"
        "  //    which is precisely the loop that does not advance.\n"
        "  wt_coda_bloccata_ = false;\n"
        "\n"
        "  for (;;) {\n",
        "  std::array<nghttp3_vec, 16> vec;\n"
        "\n"
        "  // ⭐ REMOTIX B2 — a write pass starts here, and our queue\n"
        "  //    restarts UNBLOCKED: `wt_coda_bloccata_` holds for one\n"
        "  //    pass only.  ⚠ It is outside the loop on purpose — resetting it\n"
        "  //    inside would put the same element back in play at every round,\n"
        "  //    which is precisely the loop that does not advance.\n"
        "  wt_coda_bloccata_ = false;\n"
        "\n"
        "  // ⭐ REMOTIX B3 — RCP's time flows from here: it is the only point\n"
        "  //    walked anyway, even when there is nothing to send.\n"
        "  if (rcp_) {\n"
        "    rcp_tempo(rcp_, ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS);\n"
        "  }\n"
        "  // ⛔ REMOTIX B11 — the closing capsule leaves ONLY when the output\n"
        "  //    queue is empty: the `CONGEDO` must already have left, or the\n"
        "  //    browser throws it away together with the session.\n"
        "  if (wt_chiusura_ >= 0) {\n"
        "    // ⚠ It is not enough that the queue is empty ONCE: \"handed to\n"
        "    //   ngtcp2\" is not \"out on the wire\".  We wait five write\n"
        "    //   passes, which with the keep-alive at 100 ms are half a second —\n"
        "    //   nothing, for a bench, and it removes the race between the\n"
        "    //   CONGEDO and the capsule that closes the session.\n"
        "    //\n"
        "    // ⛔ AND THAT THE FIVE PASSES HAPPEN is guaranteed by the keep-alive\n"
        "    //    that `wt_chiudi_sessione` arms at the same instant in which it\n"
        "    //    writes `wt_chiusura_`: without it, on a violation found at the\n"
        "    //    first message the client goes quiet, nobody walks this\n"
        "    //    point any more and the counter stops at one or two forever.  ⚠ It is\n"
        "    //    the defect measured by B5 on 10 Aug 2026 — 22 of 36 —, and\n"
        "    //    the server log said it in full: the `congedo`\n"
        "    //    was there, the \"closed the WebTransport session\" was not.\n"
        "    wt_chiusura_attesa_ = wt_uscita_.empty() ? wt_chiusura_attesa_ + 1 : 0;\n"
        "    if (wt_chiusura_attesa_ >= 5) {\n"
        "      auto m = static_cast<uint8_t>(wt_chiusura_);\n"
        "      wt_chiusura_ = -1;\n"
        "      wt_chiudi_adesso(m);\n"
        "    }\n"
        "  }\n"
        "\n  for (;;) {\n",
        "the time that flows",
    ),
    # ── 4-ter. ⛔ THE SLOT IS FREED ──────────────────────────────────────────
    #    `rcp_libera()` frees the slot in the session register (§8.2
    #    reason 0x0F).  Without this call the slot stays occupied
    #    forever, and ⛔ **the handshake works ONCE and never again**:
    #    from the second connection on the server answers
    #    GIA_ATTIVA_REMOTA to anyone, including whoever is alone.
    #
    # ⭐ Found by B3 at the first round, 10 Aug 2026 — and it is exactly the
    #    defect B3 exists to find: `LEZIONI.md` §2.1 says that in v1
    #    a shared certificate killed the server AT THE SECOND connection,
    #    and that a single-connection test **stays green forever**.
    #    This one is the same form, at another point.
    (
        "http3_server_proto_codec.cc",
        "ProtoCodec::~ProtoCodec() {\n",
        "ProtoCodec::~ProtoCodec() {\n"
        "  // ⭐ REMOTIX B3 — the slot in the session register is freed HERE.\n"
        "  if (rcp_) {\n"
        "    rcp_libera(rcp_);\n"
        "    rcp_ = nullptr;\n"
        "  }\n",
        "the slot that is freed",
    ),
    # ── 4-quinquies. ⛔⭐ THE SLOT IS FREED WHEN THE SESSION ENDS,
    #                     NOT WHEN THE CONNECTION DIES — found by B11
    (
        "http3_server_proto_codec.cc",
        "ProtoCodec::on_stream_close(int64_t stream_id,\n"
        "                            std::optional<uint64_t> rx_app_error_code,\n"
        "                            std::optional<uint64_t> tx_app_error_code) {\n"
        "  if (!httpconn_) {\n    return {};\n  }\n",
        "ProtoCodec::on_stream_close(int64_t stream_id,\n"
        "                            std::optional<uint64_t> rx_app_error_code,\n"
        "                            std::optional<uint64_t> tx_app_error_code) {\n"
        "  // ⛔⭐ REMOTIX B3 — RCP.md §4.2: the control channel closes, and\n"
        "  //    **its closing IS the end of the session**.  The slot in the\n"
        "  //    register (§8.2 reason 0x0F) must be freed HERE — and also when\n"
        "  //    what closes is the stream of the extended CONNECT, which carries the\n"
        "  //    WebTransport session.\n"
        "  //\n"
        "  // ⚠ Before, the slot was freed only in `~ProtoCodec`, which is the\n"
        "  //   destructor of the CONNECTION.  With `aioquic` the two instants\n"
        "  //   coincide — the test client closes everything — and B3 stayed\n"
        "  //   green for five rounds.  ⛔ A BROWSER does not: it closes the session and\n"
        "  //   **keeps the connection alive**, and from that moment the slot stays\n"
        "  //   occupied by a session that no longer exists.\n"
        "  //\n"
        "  // ⭐ Found by B11 on 10 Aug 2026: with Chrome, SEVEN `posto\n"
        "  //    NEGATO` out of nine attempts, and the page saw nothing but\n"
        "  //    silence.  It is the same form as the defect B3 had found\n"
        "  //    the day before — the slot that is not freed — at another\n"
        "  //    point, and ⛔ **a test with a single kind of client could not\n"
        "  //    see it**: the defect lives in the difference between the two.\n"
        "  if (rcp_ && (stream_id == rcp_stream_ || stream_id == wt_sessione_)) {\n"
        "    std::println(stderr,\n"
        "                 \"REMOTIX B3: closed stream {}: the session is over, \"\n"
        "                 \"the slot is freed\",\n"
        "                 stream_id);\n"
        "    rcp_libera(rcp_);\n"
        "    rcp_ = nullptr;\n"
        "    rcp_stream_ = -1;\n"
        "  }\n"
        "  if (!httpconn_) {\n    return {};\n  }\n",
        "the slot that is freed with the session",
    ),
    # ── 5. wt_accoda with the FIN ───────────────────────────────────────────
    (
        "http3_server_proto_codec.cc",
        "  wt_uscita_.push_back(\n"
        "    WtUscita{stream_id, std::vector<uint8_t>{dati.begin(), dati.end()}, 0});\n",
        "  wt_uscita_.push_back(\n"
        "    WtUscita{stream_id, std::vector<uint8_t>{dati.begin(), dati.end()}, 0,\n"
        "             false});\n",
        "wt_accoda with the FIN",
    ),
    (
        "http3_server_proto_codec.cc",
        "      wt_vec[0].base = u.dati.data() + u.off;\n"
        "      wt_vec[0].len = u.dati.size() - u.off;\n"
        "      wt_mio = true;\n",
        "      wt_vec[0].base = u.dati.data() + u.off;\n"
        "      wt_vec[0].len = u.dati.size() - u.off;\n"
        "      wt_mio = true;\n"
        "      // ⭐ REMOTIX B3\n"
        "      fin = u.fin ? 1 : 0;\n",
        "the FIN when writing",
    ),
    # ── 6. ⛔⭐ THE SLOT IS FREED ALSO WHEN IT IS THE SERVER THAT CLOSES ──────
    #    `RCP.md` §4.2: the control channel that closes IS the end of the
    #    session.  The direction in which it is closed does not change the rule — but the
    #    code knew only one direction, because nobody had ever walked
    #    the other.
    #
    # ⭐ Found by B11 on 10 Aug 2026, and ONLY on Chrome: after the case in
    #    which the server closes the channel with a FIN, the next three cases
    #    received `GIA_ATTIVA_REMOTA`.  On Firefox the transport closed the
    #    stream in time and `on_stream_close` freed the slot anyway: the
    #    defect lived in the DIFFERENCE between the two engines.
    #
    # ⚠ And the page could not make up for it: §4.2 forbids it to send after the
    #   end of the channel, so the `CONGEDO` that frees the slot — the cure of the
    #   third defect of B11 — there is precisely what it must not send.
    (
        "http3_server_proto_codec.cc",
        "        if (u.off >= u.dati.size()) {\n"
        "          wt_uscita_.pop_front();\n"
        "        }\n",
        "        if (u.off >= u.dati.size()) {\n"
        "          // ⛔⭐ REMOTIX B3 — RCP.md §4.2: the control channel that\n"
        "          //    closes is the end of the session, ALSO from our side.\n"
        "          //    The slot (§8.2 reason 0x0F) must be released HERE, because from\n"
        "          //    now on no byte will arrive any more to free it.\n"
        "          //\n"
        "          // ⛔ AND IT ALSO APPLIES TO THE SESSION STREAM.  With only the\n"
        "          //    condition on `rcp_stream_` this line was reachable\n"
        "          //    ONLY with the faulty B11 server grafted: it is the only one\n"
        "          //    that puts a FIN on the control channel.  On the real\n"
        "          //    server our FIN goes on the stream of the CONNECT — which\n"
        "          //    CARRIES the session — and the two cases are the same pair\n"
        "          //    that `on_stream_close` already looks at twenty lines above.\n"
        "          //\n"
        "          // ⚠ `congeda()` releases the slot on its own at every farewell\n"
        "          //   (`banchi/rcp/rcp.c`), so here there is usually nothing\n"
        "          //   left to do: this is the net for the closings that have no\n"
        "          //   farewell, and it is idempotent.\n"
        "          if (u.fin && rcp_ &&\n"
        "              (u.stream_id == rcp_stream_ || u.stream_id == wt_sessione_)) {\n"
        "            rcp_canale_chiuso(rcp_);\n"
        "          }\n"
        "          wt_uscita_.pop_front();\n"
        "        }\n",
        "the slot that is freed when the server closes",
    ),
    # ── 7. ⛔⭐ THE SECOND ROAD OF §3.1, WHICH UNTIL TODAY NOBODY LOOKED AT ──
    #    §3.1 point 3: the reason of the farewell travels **also** in the closing
    #    code.  B2 now reads the capsule that carries it; here we say what
    #    it means — and it is the only place that knows, because "it was already
    #    over" is an RCP state, not a transport one.
    #
    # ⭐ Without this line, Firefox would have been said "not to say farewell":
    #    it resets the control stream and throws away the `CONGEDO` already queued — the
    #    second defect found by B11 — and the reason reaches it **only** from
    #    here.  ⚠ Two engines, two roads, and one single rule respected by
    #    both: it is the reason §3.1 point 3 is not redundancy.
    (
        "http3_server_proto_codec.cc",
        "void ProtoCodec::wt_chiusa_dal_client(uint32_t codice) { (void)codice; }\n",
        "void ProtoCodec::wt_chiusa_dal_client(uint32_t codice) {\n"
        "  // ⛔⭐ REMOTIX B3 — AND FIRST OF ALL WE LOOK AT WHETHER THAT CODE EXISTS.\n"
        "  //\n"
        "  //    RCP.md §3.1: code **0** means \"closing without a reason\"\n"
        "  //    and MUST NOT be used — every closing has a reason from §8.2.\n"
        "  //    And §3 — the rule of rigour — asks to write IN THE LOG\n"
        "  //    what was not understood, not to make up for it silently.\n"
        "  //\n"
        "  // ⚠ Before, the code arrived truncated to 8 bits: a page that\n"
        "  //   closed with `0x0100` made RCP write \"reason 0x00\" —\n"
        "  //   that is the only value §3.1 forbids — and the two logs of the\n"
        "  //   SAME closing contradicted each other two lines apart.\n"
        "  //   ⛔ And `close()` without a code, which is 0, was indistinguishable from\n"
        "  //     a regular closing.\n"
        "  bool motivo_valido = codice >= uint32_t{RCP_CHIUSO_DALL_UTENTE} &&\n"
        "                       codice <= uint32_t{RCP_GIA_ATTIVA_REMOTA};\n"
        "  if (!motivo_valido) {\n"
        "    std::println(stderr,\n"
        "                 \"REMOTIX B3: ⛔ VIOLATION §3.1 — the page closed \"\n"
        "                 \"the session with code {:#x}, which is not a reason of \"\n"
        "                 \"§8.2 (0 = «no reason», and it is forbidden).  On record \"\n"
        "                 \"goes ERRORE_PROTOCOLLO, and this line says the real \"\n"
        "                 \"code: the session is already closed by the client, so \"\n"
        "                 \"there is nothing left to dismiss\",\n"
        "                 codice);\n"
        "  }\n"
        "  auto motivo = static_cast<uint8_t>(\n"
        "    motivo_valido ? codice : uint32_t{RCP_ERRORE_PROTOCOLLO});\n"
        "  // ⭐ REMOTIX B3 — RCP.md §3.1 point 3: the reason in the closing\n"
        "  //    code is the second road, and applies when the first is closed.\n"
        "  if (rcp_ && rcp_e_finita(rcp_)) {\n"
        "    std::println(stderr,\n"
        "                 \"REMOTIX B3: ⭐ parting CONGEDO by the second \"\n"
        "                 \"road of §3.1 (the closing code): reason {:#04x} \"\n"
        "                 \"— the bytes on the channel could no longer be sent\",\n"
        "                 motivo);\n"
        "  }\n"
        "  // ⛔ And the SLOT is released now: §4.2, the session is over because\n"
        "  //    the client says so.  Waiting for the transport to be torn down means\n"
        "  //    keeping it occupied against whoever reconnects right away.\n"
        "  if (rcp_) {\n"
        "    rcp_chiusa_dal_client(rcp_, motivo);\n"
        "  }\n"
        "}\n",
        "the parting that travels in the closing code",
    ),
    # ── 8. ⛔⭐ THE CLIENT'S FIN ON THE CONTROL CHANNEL — §4.2, the other
    #          direction, which nobody had walked.
    #
    #    §4.2: "a FIN on that stream, **from either of the two sides**,
    #    closes the session.  Whoever receives it **MUST** consider it over".  The
    #    server→client direction was cured (B11, the slot that is freed); this is
    #    the client→server direction, and it is the **same form** of the defect: the
    #    page closes the writing side of the channel — `writable.close()` — and
    #    keeps the session and the connection alive.  ⛔ The slot stayed occupied
    #    until the connection died, and a browser keeps a connection
    #    alive.
    (
        "http3_server_proto_codec.cc",
        "void ProtoCodec::wt_fin_dal_client(int64_t stream_id) { (void)stream_id; }\n",
        "void ProtoCodec::wt_fin_dal_client(int64_t stream_id) {\n"
        "  if (!rcp_ || stream_id != rcp_stream_) {\n"
        "    return;\n"
        "  }\n"
        "  // ⚠ We write the line HERE and not in rcp.c, because `rcp.c` does not know\n"
        "  //   which side the FIN came from: its log says \"from the\n"
        "  //   server side\", which here would be false.  The fact is the same —\n"
        "  //   §4.2, the session is over — and so is the effect: the slot is\n"
        "  //   released and we stay watching whether the client still sends, which is\n"
        "  //   the MUST that can only be observed from here.\n"
        "  std::println(stderr,\n"
        "               \"REMOTIX B3: ⛔ FIN from the CLIENT on the control channel \"\n"
        "               \"(stream {}): §4.2, the session is over\",\n"
        "               stream_id);\n"
        "  rcp_canale_chiuso(rcp_);\n"
        "}\n",
        "the client's FIN on the control channel",
    ),
]


CORPO = r'''namespace {
// ⭐ REMOTIX B3 — the four hooks of `rcp_ganci`, which are the only thing
//    RCP knows about the world below.  They pass through here and nothing else: if one day
//    the module goes into a real server, these four are rewritten and the
//    protocol is not.
void rcp_gancio_manda(void *ctx, const uint8_t *dati, size_t len);
void rcp_gancio_chiudi(void *ctx, uint8_t motivo);
void rcp_gancio_registra(void *ctx, const char *riga);
bool rcp_gancio_verifica(void *ctx, const char *utente, const char *parola);
} // namespace

void ProtoCodec::rcp_avvia(int64_t stream_id) {
  rcp_stream_ = stream_id;

  static const rcp_ganci ganci = {
    nullptr, rcp_gancio_manda, rcp_gancio_chiudi, rcp_gancio_registra,
    rcp_gancio_verifica,
  };
  auto g = ganci;
  g.ctx = this;

  // The origin is needed by the per-address counter of §4.4-bis and by the log.
  std::array<char, 64> da{};
  auto path = ngtcp2_conn_get_path(conn_);
  if (path && path->remote.addr) {
    util::straddr(path->remote.addr, path->remote.addrlen).copy(da.data(),
                                                               da.size() - 1);
  }

  rcp_ = rcp_apri(&g, da.data(),
                  ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS);

  // ══ ⛔⭐ AND HERE THE CLOCK OF THE FIRST CAP IS ARMED — §4.6 line 1 ═══════
  //
  //    `[M]` 10 Aug 2026, bench B6: `ciao-tetto` gave "nothing
  //    happened for 20 s".  The other two caps fired — 60 s and 10 s, with
  //    `TEMPO_SCADUTO` — and the first did not: a client that opens the control
  //    channel and then goes quiet stayed hung forever.
  //
  // ⛔ And the defect was not in `rcp.c`: it has the cap of the `CIAO`, in
  //    `rcp_tempo()`, next to the other two.  It was that NOBODY called
  //    `rcp_tempo()` ANY MORE.  It flows from the write path, and the
  //    write path in silence is only made to pass by the keep-alive:
  //    which was armed only inside `rcp_passa`, that is **only when
  //    bytes arrive**.  In the `attesa-ciao` state no byte has
  //    arrived yet — opening the channel carries the header of
  //    the WebTransport stream and nothing else, and with an empty `resto` `rcp_passa`
  //    is not invoked at all — so nobody armed it.
  //
  // ⚠ It is the SAME FORM as the defect cured a few hours earlier in
  //   `wt_chiudi_sessione`: the signal that makes time flow was armed at
  //   a point that case does not cross.  ⛔ Whoever sets a cap must
  //   also turn on what will make it expire, and at the instant the
  //   cap begins — not at the first useful occasion that comes along afterwards.
  //
  // ⭐ The instant is THIS one: `rcp_apri` sets the state to `attesa-ciao` and
  //    `s->da_quando` to now.  The server's stopwatch and the clock that makes
  //    it run thus start from the same line.
  //
  // ⚠ It is NOT turned off here, nor at the arrival of the `CIAO`: the other two
  //   caps of the handshake want the same beat, and `rcp_passa`
  //   resets it at every message — 100 ms for the whole handshake, 5 s once
  //   `attiva`, which is the only point where it widens.  Turning it off
  //   earlier would redo the defect just cured, one cap further on.
  //
  // ⚠ And it stays a wire of the HOST, like the others: it is the keep-alive of the
  //   TRANSPORT, not an application heartbeat (§2.2 forbids that, and this is not
  //   one), and a real server will arm its own timer without putting anything on
  //   the wire.
  if (rcp_) {
    ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  }
  std::println(stderr, "REMOTIX B3: control channel = stream {}", stream_id);
}

void ProtoCodec::rcp_passa(int64_t stream_id, std::span<const uint8_t> dati) {
  if (!rcp_) {
    return;
  }
  auto ora = ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS;
  if (!rcp_ricevi(rcp_, dati.data(), dati.size(), ora)) {
    return;
  }
  // ⛔ The fixed delay of §4.4-bis lasts one second, and in that second the
  //    server has nothing to send: without a timer the answer would never
  //    leave.  The QUIC keep-alive makes the write path pass
  //    every 100 ms — it is a wire of the host, not a rule of the
  //    protocol, and that is why it is here and not in rcp.c.
  // ⛔ Two states want a beat, and for two different reasons:
  //
  //   attesa-verdetto  the fixed delay of §4.4-bis lasts one second, and in
  //                    that second there is nothing to send;
  //   attiva           the SILENCE CLOCK of §5.3 must be evaluated while the
  //                    client is quiet — and while it is quiet nobody walks the
  //                    write path.
  //
  // ⛔ AND THE FIRST ARMING IS NOT HERE: it is in `rcp_avvia`, where the RCP session
  //    is born.  We get here only when some bytes have arrived, and in the
  //    `attesa-ciao` state none has arrived yet: arming it only from
  //    here left the cap of the `CIAO` with nobody to make it expire
  //    (`[M]` 10 Aug 2026, B6).  These lines do not TURN ON the beat:
  //    they ADJUST it as the state changes.
  //
  // ⚠ It is a TRANSPORT beat (the QUIC keep-alive), not an application
  //   heartbeat: §2.2 forbids the second, and this is not one.  ⛔ It does remain
  //   a wire of the HOST, though: a real server will arm its own timer and will not
  //   put anything on the wire.  It is written down so that it is not inherited by
  //   distraction.
  auto stato = std::string_view{rcp_stato_nome(rcp_)};
  if (stato == "attesa-verdetto") {
    ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  } else if (stato == "attiva") {
    ngtcp2_conn_set_keep_alive_timeout(conn_, 5 * NGTCP2_SECONDS);
  } else {
    // ⚠ The middle states of the handshake — `attesa-attacca` and the like:
    //   the beat stays dense because the handshake is not over yet.
    //
    // ⛔ AND HERE IT USED TO SAY "even after the end the write path must
    //    keep passing: the capsule that closes the session leaves from
    //    there".  ⚠ It was FALSE, and it cost the fourteen cases of B5 of 10
    //    Aug 2026: after the end this line is NOT reached, because
    //    twenty lines above `rcp_ricevi` returns false — "the session is
    //    over" — and we exit.  The beat that makes the wait for the
    //    capsule mature is armed by `wt_chiudi_sessione`, which is the only point
    //    crossed by ALL the roads of the closing, including the two that
    //    do not pass through here at all.
    ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  }
}

namespace {
void rcp_gancio_manda(void *ctx, const uint8_t *dati, size_t len) {
  auto pc = static_cast<ProtoCodec *>(ctx);
  pc->wt_manda_controllo(dati, len);
}

void rcp_gancio_chiudi(void *ctx, uint8_t motivo) {
  auto pc = static_cast<ProtoCodec *>(ctx);
  pc->wt_chiudi_sessione(motivo);
}

void rcp_gancio_registra(void *ctx, const char *riga) {
  (void)ctx;
  std::println(stderr, "REMOTIX B3: {}", riga);
}

bool rcp_gancio_verifica(void *ctx, const char *utente, const char *parola) {
  (void)ctx;
  // ⚠ PAM blocks.  In a bench that is fine and it is declared; in a real server the
  //   verification will go on a separate thread, or one user's handshake
  //   stops everyone else's.
  return rcp_autentica(utente, parola);
}
} // namespace

// ⛔ REMOTIX B5 — RCP.md §2.5: the unidirectional streams opened by the CLIENT.
//
// ⭐ How the channel is recognised: "the first two bytes of the stream are read,
//    which are in any case a `tipo` field".  The high byte says the channel, and
//    of five legitimate values **three are violations when they arrive from here**:
//
//    0x00  control    ⛔ "control lives only on stream 0"
//    0x01  input      ✓  legal: it is the only unidirectional stream the client opens
//    0x02  clipboard  ✓  legal, one per transfer
//    0x03  video      ⛔ wrong direction: video goes from server to client
//    0x04  audio      ⛔ "only on datagrams.  On a stream it is ERRORE_PROTOCOLLO"
//
// ⚠ And even before that we must know whether the stream is OURS: among the
//   client's unidirectional streams there are the HTTP/3 control channel and the two
//   QPACK ones, which belong to nghttp3.  A WebTransport stream is recognised by its
//   type, 0x54 — which like 0x41 does not fit in one byte: on the wire they are 0x40 0x54.
ProtoCodec::WtEsito ProtoCodec::wt_smista_uni(int64_t stream_id,
                                              std::span<const uint8_t> data,
                                              std::vector<uint8_t> &riunito) {
  if (wt_nonwt_.contains(stream_id)) {
    return WtEsito::HTTP3;
  }
  if (auto giudizio = wt_uni_.find(stream_id); giudizio != wt_uni_.end()) {
    // Already judged — ⚠ but the two judgements are NOT the same thing, and the
    // previous comment named only one of them ("the session has already fallen"), which
    // for the two legitimate channels is false:
    //
    //   true   violation: the session has already fallen, and there is nothing left
    //          to serve;
    //   false  LEGITIMATE channel of §2.5 — `0x01` input, `0x02` clipboard — that
    //          this phase does not serve yet: input arrives with phase 4, the
    //          clipboard with phase 7.
    //
    // ⛔ Before, `wt_uni_` was written to `true` for all five values of
    //    `canale`, so also for the two legitimate ones: a conforming client opened the
    //    input channel, was told "legitimate" — and from that moment
    //    EVERY byte of it ended up in here, discarded forever and without a line
    //    of log, under a comment that asserted a fall that was not there.
    //
    // ⚠ The leniency is declared ONCE, when the stream is
    //   recognised (RCP.md §3, last line: "every leniency must be written in the
    //   log"), not at every packet: one line per packet would make the
    //   log unreadable, and the log is B11's witness.
    //
    // In both cases the bytes are counted in the credit: not counting them
    // would leave the client without credit on a live connection (§2.3).
    if (!data.empty()) {
      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());
      ngtcp2_conn_extend_max_offset(conn_, data.size());
    }
    return WtEsito::MIO;
  }

  auto &pref = wt_incerti_[stream_id];
  pref.insert(pref.end(), data.begin(), data.end());
  if (pref.size() < 2) {
    return WtEsito::ATTENDI;
  }
  if (!(pref[0] == 0x40 && pref[1] == 0x54)) {
    // It is not WebTransport: it belongs to nghttp3, and the bytes must be delivered whole.
    riunito = pref;
    wt_incerti_.erase(stream_id);
    wt_nonwt_[stream_id] = true;
    return WtEsito::HTTP3;
  }
  uint64_t sessione = 0;
  auto n = wt_leggi_varint(&sessione, pref.data() + 2, pref.size() - 2);
  if (n == 0 || pref.size() < 2 + n + 2) {
    return WtEsito::ATTENDI; // the `tipo` field has not all arrived yet
  }
  auto consumati = pref.size();
  uint16_t tipo = static_cast<uint16_t>(pref[2 + n] << 8 | pref[2 + n + 1]);
  auto canale = static_cast<uint8_t>(tipo >> 8);
  wt_incerti_.erase(stream_id);
  ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, consumati);
  ngtcp2_conn_extend_max_offset(conn_, consumati);

  const char *guasto = nullptr;
  switch (canale) {
  case 0x00:
    guasto = "the CONTROL channel on a unidirectional stream: "
             "control lives only on stream 0 (§2.5)";
    break;
  case 0x03:
    guasto = "the VIDEO channel from the client: it belongs to the server, wrong direction (§2.5)";
    break;
  case 0x04:
    guasto = "the AUDIO channel on a stream: audio lives only on datagrams "
             "(§2.5, §6.3)";
    break;
  case 0x01:
  case 0x02:
    break;
  default:
    guasto = "unknown high byte of the type on a unidirectional stream (§2.5)";
    break;
  }
  // ⛔ And the judgement is recorded AFTER it has been issued, not before: `true` means
  //    "violation, the session has fallen", and writing it for all the
  //    channels was what made the bytes of the two legitimate ones vanish.
  wt_uni_[stream_id] = guasto != nullptr;
  std::println(stderr,
               "REMOTIX B5: unidirectional stream {} from the client, session {}, "
               "type {:#06x}, channel {:#04x} — {}",
               stream_id, sessione, tipo, canale,
               guasto ? "VIOLAZIONE"
                      : "legitimate (§2.5).  ⚠ But this phase does not serve it: the bytes "
                        "are counted in the credit and discarded, and this line "
                        "is the declared leniency (§3)");
  if (guasto) {
    if (rcp_) {
      rcp_violazione(rcp_, guasto);
    } else {
      // ⚠ No control channel opened yet: the `CONGEDO` has no
      //   road, and what remains is point 3 of §3.1 — the reason inside the closing
      //   of the session.  ⭐ It is the second conditional of §3.1 at work:
      //   demanding all three points always would give red on the right
      //   code (finding R3.3).
      std::println(stderr, "REMOTIX B5: ⚠ no control channel: the reason "
                           "travels only in the closing of the session");
      wt_chiudi_sessione(0x0B);
    }
  }
  return WtEsito::MIO;
}

void ProtoCodec::wt_manda_controllo(const uint8_t *dati, size_t len) {
  if (rcp_stream_ == -1) {
    return;
  }
  wt_accoda(rcp_stream_, std::span<const uint8_t>{dati, len});
}

void ProtoCodec::wt_chiudi_sessione(uint8_t motivo) {
  // ⛔ RCP.md §3.1 point 3: the WebTransport SESSION is closed with the
  //    application error code equal to the code of the reason — not the QUIC
  //    connection, which can carry other things.
  //
  // In bytes it is the CLOSE_WEBTRANSPORT_SESSION capsule (type 0x2843) on the
  // stream of the extended CONNECT, followed by the FIN.
  if (wt_sessione_ == -1) {
    return;
  }
  // ⛔⭐ AND THE CAPSULE IS POSTPONED, instead of queuing it now — found by B11
  //    on 10 Aug 2026, with real browsers.
  //
  //    `respingi()` sends `RESPINTO` on the control channel and closes the
  //    session **on the next line**.  The two ended up in the same write
  //    pass, that is often in the same flight of packets — and the browser
  //    processes the `CLOSE_WEBTRANSPORT_SESSION` capsule **before** the bytes
  //    of the stream, which at that point it throws away.  ⛔ The page never saw
  //    `RESPINTO`: it saw **silence**.
  //
  // ⚠ And point 3 of §3.1 did its job — the reason arrived
  //   anyway, inside the closing code — but point 2 was lost, and
  //   §3.1 wants both when the channel is usable.
  //
  // ⛔ AND QUEUING THE CAPSULE BEHIND THE `CONGEDO`, IN THE SAME QUEUE, IS NOT
  //    THE CURE: IT IS EXACTLY THE CODE B11 FOUND BROKEN.  The queue
  //    is ordered and serves one element per pass, so the order on the wire
  //    would be there — ⚠ but the order on the wire is not what is missing.  The two
  //    still end up in the same flight, the browser processes the capsule
  //    before delivering the bytes of the stream to the page, and the page does not
  //    see the `CONGEDO`.  What is needed is TIME between the two, and that is what
  //    the wait buys.
  //
  // ⭐ Here only the intention is marked: the write loop queues the capsule
  //    when the queue is empty, that is when the bytes of the `CONGEDO`
  //    have already been handed to ngtcp2.
  wt_chiusura_ = motivo;
  // ⛔ And the wait restarts from ZERO: the five passes are counted from THIS
  //    closing.  Without it, a second closing on the same connection
  //    would find the counter already beyond five and would send the capsule
  //    in the same pass as its `CONGEDO` — that is the defect the wait
  //    exists to remove, reappearing at the second round.
  wt_chiusura_attesa_ = 0;
  // ══ ⛔⭐ REMOTIX B5 — AND HERE THE CLOCK THAT MAKES THE WAIT MATURE IS ARMED ══
  //
  //    `[M]` 10 Aug 2026: "§3.1 point 3 — reason in the WT closing" gave
  //    22 of 36, and the fourteen missing were ALL violations found at the
  //    first message.  In the server log, for `versione-2`, there was
  //    `congedo motivo=0x0a` and there was NOT "closed the WebTransport session":
  //    the capsule never left.
  //
  // ⛔ And the defect was not the wait: it was the passes, which did not come.
  //    The keep-alive was armed only by `rcp_passa`, and only AFTER
  //    `rcp_ricevi` — which on a violation returns false, because the
  //    session is over.  On a violation at the FIRST message that point
  //    was never reached even once: the client did not send
  //    anything more, the write path was no longer walked, and
  //    `wt_chiusura_attesa_` stayed stuck at one or two forever.  ⚠ And the
  //    other two roads of the closing — `wt_smista` for the second bidirectional
  //    stream, `wt_smista_uni` when there is no control channel
  //    yet — do not pass through `rcp_passa` at all.
  //
  // ⭐ That is why the clock is armed HERE, where the intention is marked:
  //    it is the only point all the roads cross, and ⛔ whoever postpones a
  //    job must also turn on what will make it mature — a job
  //    postponed to a condition that nobody makes happen any more is not
  //    postponed, it is lost, and in the log it looks like a job never
  //    asked for.
  //
  // ⚠ The order between the `CONGEDO` and the capsule does NOT change: the five
  //   passes with an empty queue remain, which at 100 ms are half a second.  Here nothing is
  //   shortened and nothing is removed — we only make exist the time that
  //   the wait already demanded.
  //
  // ⚠ And it stays a wire of the HOST, like the other three: a real server will arm
  //   its own timer and will not put anything on the wire (§2.2).
  ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  std::println(stderr,
               "REMOTIX B3: closing of the session POSTPONED, code {:#04x} "
               "(queued: {}; keep-alive at 100 ms so that the five passes "
               "mature)",
               motivo, wt_uscita_.size());
}

void ProtoCodec::wt_chiudi_adesso(uint8_t motivo) {
  // ⛔⭐ THE CAPSULE GOES INSIDE A `DATA` FRAME, AND UNTIL 10 AUG IT WENT OUT BARE.
  //
  //    The body of an extended CONNECT is a stream of capsules (RFC 9297), but
  //    in HTTP/3 the body of a message travels inside `DATA` frames: the
  //    capsule does NOT sit bare on the stream.  ⭐ And that the client wraps them
  //    is proven by our own READ side: `wt_capsula` is called by
  //    `http_recv_data`, which nghttp3 invokes only on the payload of a
  //    `DATA`.  If the capsules were not inside, that function would
  //    never have been called — and on Firefox it was called `[M]`.
  //
  // ⛔ The two directions could not both be right, and the wrong one
  //    was this.  Written bare, the seven bytes `68 43 04 00 00 00 mm` are read by the
  //    browser with its own HTTP/3 layer: `0x68` has the two high bits at
  //    `01`, so it is a two-byte variable-length integer, and the frame type
  //    becomes `0x2843` — which **is not a known HTTP/3 frame type**, and RFC
  //    9114 §9 requires IGNORING it.  The page saw no capsule:
  //    it saw only the FIN that arrives right behind, and a FIN on the stream
  //    of the CONNECT without `CLOSE_WEBTRANSPORT_SESSION` closes the session with
  //    code **0**.
  //
  // ⚠ That is, it is the `congedo:0x00` that B11 saw and that had been attributed to
  //   a race between events: this road produces it **at every round**, not one
  //   in five.  ⭐ The measurement that tells the two explanations apart is written in the
  //   report: make the server close with `0x0b` with no `RESPINTO` in the
  //   queue, and read `wt.closed` from the page.
  std::array<uint8_t, 64> b{};
  size_t n = 0;
  // the envelope: an HTTP/3 DATA frame, type 0x00, as long as the capsule
  b[n++] = 0x00; // DATA
  b[n++] = 7;    // 2 bytes of type + 1 of length + 4 of code
  // the CLOSE_WEBTRANSPORT_SESSION capsule
  b[n++] = 0x68; // 0x2843 as a variable-length integer, first byte
  b[n++] = 0x43;
  b[n++] = 4;    // length of the capsule: only the code
  b[n++] = 0;
  b[n++] = 0;
  b[n++] = 0;
  b[n++] = motivo;
  wt_uscita_.push_back(WtUscita{
    wt_sessione_, std::vector<uint8_t>{b.data(), b.data() + n}, 0, true});
  std::println(stderr,
               "REMOTIX B3: closed the WebTransport session, code {:#04x} "
               "({} bytes: 2 of DATA frame + 7 of capsule)",
               motivo, n);
}

'''

# ===========================================================================
# ⛔⭐ THE HOST-SIDE BAN — the three things §4.4-bis asks of the HOST
# ===========================================================================
#
# `rcp.c` can count failures, ban, save to file, answer "is it
# banned?" and remove a ban.  ⛔ But it opens no socket, does not read the command
# line and serves no page: the three things that follow **did not exist**
# until 11 Aug 2026, and without them the user's rule was half
# written.
#
#   1. the bans are REREAD at startup         §4.4-bis, "the ban survives the
#                                            restart of the server" — invariant I7
#   2. the PAGE is served all the same to     §4.4-bis, "a page of refused
#      whoever is banned, and says how many   login is displayed"
#      hours are left
#   3. the UNBLOCK COMMAND                    §4.4-bis, "there are two ways out"
#
CORPO_OSPITE = r'''// ═══════════════════════════════════════════════════════════
// ⛔⭐ REMOTIX B3 — THE HOST-SIDE BAN (RCP.md §4.4-bis, DECISIONI.md §1.9)
//
// ⛔ WHY IT IS HERE AND NOT IN `rcp.c`.  That file "knows RCP.md and nothing else:
//    it does not know there is QUIC underneath, opens no socket and does not look at the clock".  The
//    three things below are all three socket, command line and clock —
//    that is, all three belong to the host.  ⭐ `rcp.c` exposes `rcp_ban_carica`,
//    `rcp_bannato` and `rcp_sblocca` and does not know **who** calls them: it is the same
//    line that will allow carrying the protocol into the real server without
//    rewriting it.
//
// ⛔ AND THE CLOCK MUST BE THE SAME.  `rcp_apri`/`rcp_ricevi` receive
//    `ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS`, and ngtcp2 takes that
//    value from `util::timestamp()`.  Here there is no
//    connection, so `util::timestamp()` is called directly: ⚠ a
//    second clock with another origin would make the ban expiries
//    meaningless numbers — "4 billion hours left" — and nobody would see it
//    until someone really got banned.
// ═══════════════════════════════════════════════════════════════════════════
#include <sys/un.h>
#include <cerrno>

extern "C" {
#include "rcp.h"
}

namespace {

// The monotonic clock in milliseconds: THE SAME one the session sees.
uint64_t remotix_ora_ms() { return util::timestamp() / NGTCP2_MILLISECONDS; }

// The two roads of the host, from the command line.
const char *remotix_ban_file = nullptr;
const char *remotix_comando_socket = nullptr;

ev_io remotix_pagina_ev;
ev_io remotix_comando_ev;
bool remotix_pagina_accesa = false;
bool remotix_comando_acceso = false;

// ⛔ 200 ms, and the price is declared instead of hidden.  Here the page and the
//    command are served INSIDE the QUIC event loop, with a blocking read and
//    write with a timeout: a TCP client that opens and goes quiet stops the
//    server for two tenths of a second.  ⚠ It is acceptable in a bench and must be
//    written here: a real server will put an `ev_io` for every accepted
//    connection, or a separate thread.  ⭐ The reason it is NOT done today is
//    that `rcp.c` keeps the ban table in static memory without any
//    lock: a separate thread would be a race between two writers, that is a
//    real defect bought to avoid a fake delay.
const timeval REMOTIX_TETTO{0, 200000};

// ── What is read and written, with a cap and without ever blocking
//    forever.  They return false on any fault: the caller closes and goes
//    on — a lost TCP connection must not carry off the server.
bool remotix_scrivi_tutto(int fd, std::string_view dati) {
  while (!dati.empty()) {
    auto n = send(fd, dati.data(), dati.size(), MSG_NOSIGNAL);
    if (n <= 0) {
      return false;
    }
    dati.remove_prefix(static_cast<size_t>(n));
  }
  return true;
}

// ═══ 1. THE PAGE ════════════════════════════════════════════════════════════
//
// ⛔ §4.4-bis, and the reason is the user's: "the page is served all the same, and
//    shows the refusal — *attempts exhausted*.  Not a network error, not a
//    silence: whoever was banned by mistake is almost always the owner,
//    and must be able to understand what happened to them instead of facing a
//    server that seems dead for half a day".
//
// ⛔ AND THE STATUS IS 200, EVEN FOR WHOEVER IS BANNED — a choice, not a distraction.
//    §4.4-bis says "the page is served all the same" and does not say with which HTTP
//    status.  With a 403 the document would be served anyway, ⚠ but a proxy,
//    an extension or the browser itself can replace the body of an
//    error response with a screen of its own — and then the sentence the
//    user MUST read disappears, which is exactly the case this
//    rule exists to prevent.  ⭐ The refusal is of the ACCESS, not of the
//    page: the page did its job.
std::string remotix_pagina_html(bool bannato, const std::string &chiave,
                                uint64_t restano_ms) {
  if (!bannato) {
    return std::format(
      "<!doctype html>\n<html lang=\"en\">\n<head><meta charset=\"utf-8\">\n"
      "<title>REMOTIX — access</title></head>\n"
      "<body data-bannato=\"no\" data-restano-ms=\"0\">\n"
      "<h1 id=\"esito\">access</h1>\n"
      "<p id=\"quanto\">This address ({}) may try to log in.</p>\n"
      "<p>⚠ Minimal bench page: the real RCP page arrives with the next "
      "phase.  Here there is the only thing §4.4-bis demands of the "
      "host — saying whether the address is out, and for how long.</p>\n"
      "</body>\n</html>\n",
      chiave);
  }
  // ⚠ The minutes are rounded UP: saying "0 hours left" to whoever still
  //   has 59 minutes to wait is worse than saying nothing.
  auto minuti = (restano_ms + 59999) / 60000;
  auto ore = minuti / 60;
  auto resto = minuti % 60;
  return std::format(
    "<!doctype html>\n<html lang=\"en\">\n<head><meta charset=\"utf-8\">\n"
    "<title>REMOTIX — attempts exhausted</title></head>\n"
    "<body data-bannato=\"si\" data-restano-ms=\"{}\">\n"
    "<h1 id=\"esito\">attempts exhausted</h1>\n"
    "<p id=\"quanto\">Three failed login attempts arrived from this address "
    "({}), and for this reason it stays out.  There are still "
    "<b id=\"ore\">{}</b> hours and <b id=\"minuti\">{}</b> minutes left.</p>\n"
    "<p id=\"uscite\">There are two ways back in: waiting for the expiry, or "
    "with the unblock command on the serving machine — which requires access to "
    "that machine, and is the way out for whoever banned themselves from their own "
    "phone.</p>\n"
    "</body>\n</html>\n",
    restano_ms, chiave, ore, resto);
}

void remotix_pagina_servi(int fd, const sockaddr *sa, socklen_t salen) {
  setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &REMOTIX_TETTO, sizeof REMOTIX_TETTO);
  setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &REMOTIX_TETTO, sizeof REMOTIX_TETTO);

  // ⛔ The request is READ even if we do not need it, and it is not courtesy: closing
  //    a socket with unread bytes in the buffer sends an RST, and the RST makes
  //    the client throw away the response we have just written to it.  Whoever is
  //    banned would see "connection reset" — that is the network error that
  //    §4.4-bis forbids — and the server would say in the log that it answered.
  std::array<char, 4096> richiesta;
  auto letti = recv(fd, richiesta.data(), richiesta.size(), 0);

  // ⛔ AND THE ADDRESS IS ASKED OF THE KERNEL, IN THE SAME FORM AS THE SESSION.
  //    `util::straddr()` writes `[127.0.0.1]:55680` — with brackets even for
  //    IPv4 — and that is the key `rcp.c` counts and that ends up in the ban
  //    file.  ⚠ Building it here in another way (bare `inet_ntop`) would give
  //    `127.0.0.1`, which is NOT `[127.0.0.1]`: the page would say "you may log in"
  //    to a banned address, and the server log would say the opposite.
  //    `[M]` the form with brackets is read in the log, not deduced.
  auto provenienza = util::straddr(sa, salen);
  std::array<char, 64> chiave{};
  rcp_chiave_indirizzo(provenienza.c_str(), chiave.data(), chiave.size());

  uint64_t restano = 0;
  auto fuori = rcp_bannato(provenienza.c_str(), remotix_ora_ms(), &restano);
  auto corpo = remotix_pagina_html(fuori, std::string{chiave.data()}, restano);
  auto testa = std::format("HTTP/1.1 200 OK\r\n"
                           "Content-Type: text/html; charset=utf-8\r\n"
                           "Content-Length: {}\r\n"
                           "Cache-Control: no-store\r\n"
                           "Connection: close\r\n"
                           "\r\n",
                           corpo.size());
  auto scritta = remotix_scrivi_tutto(fd, testa) && remotix_scrivi_tutto(fd, corpo);
  std::println(stderr,
               "REMOTIX B3: TCP page at {} (key {}) — {} · request {} "
               "bytes · response {} bytes {}",
               provenienza, chiave.data(),
               fuori ? std::format("BANNED, {} ms left", restano)
                     : std::string{"not banned"},
               letti, corpo.size(),
               scritta ? "sent" : "⛔ NOT sent in full");
}

void remotix_pagina_cb(struct ev_loop *loop, ev_io *w, int revents) {
  (void)loop;
  (void)revents;
  sockaddr_storage chi{};
  socklen_t quanto = sizeof chi;
  auto fd = accept(w->fd, reinterpret_cast<sockaddr *>(&chi), &quanto);
  if (fd == -1) {
    return;
  }
  remotix_pagina_servi(fd, reinterpret_cast<sockaddr *>(&chi), quanto);
  close(fd);
}

// ═══ 2. THE UNBLOCK COMMAND ═════════════════════════════════════════════════
//
// ⛔ WHY A CONTROL SOCKET, AND NOT THE OTHER TWO FORMS.  §4.4-bis asks for
//    "an unblock command on the server", "the way out for whoever bans themselves from
//    their own phone", which "asks for the only key that case admits —
//    access to the machine", and which **writes every unblock in the log**
//    distinguishing a removed ban from a ban that never fired.  Three forms were
//    possible and two do not hold:
//
//    ⛔ a SECOND PROCESS with an option (`bsslserver --sblocca X`) —
//       **does not work**, and the way it does not work is silent: the ban
//       lives in the memory of the serving process, and a second process can
//       only rewrite the file.  The server would keep answering
//       `TROPPI_TENTATIVI` until the restart, and ⛔ the first `salva_ban()` — that is
//       the first ban of anyone else — would rewrite the file putting
//       back into it the ban just removed.  Whoever gave the command saw it exit
//       with zero;
//    ⛔ a SIGNAL — does not carry an address.  `SIGUSR1` could remove
//       *all* the bans, which is a different command from the one asked, and
//       above all **has no answer**: §4.4-bis wants "it was not
//       banned" and "I removed it" to be told apart, and a delivered signal only says
//       that it was delivered;
//    ⭐ a CONTROL SOCKET — carries the address, acts on the LIVE process
//       (memory and file on the same line, by the hand of `rcp_sblocca()`), and
//       **answers**, so the two answers really exist.  The key it
//       asks for is a file with `0600` permissions in the machine's filesystem,
//       that is exactly "access to the machine" — and it adds no
//       surface reachable from the network: a Unix domain socket has no
//       IP address.
//
// The protocol is one line, and can be read without tools:
//
//     SBLOCCA <address>     →   TOLTO <key>         the ban was there and is no longer
//                           →   NON-BANNATO <key>   there was nothing to remove
//     PING                  →   PONG                "does the command exist?", and it
//                                                    touches nothing
//
// ⭐ `PING` is not an ornament: it is the denominator of B0.3.  A bench that
//    calls the unblock between one bench and the next must be able to say "the command was there
//    and answered", or "the ban did not fire" and "the unblock never
//    reached anyone" look the same.
void remotix_comando_servi(int fd) {
  setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &REMOTIX_TETTO, sizeof REMOTIX_TETTO);
  setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &REMOTIX_TETTO, sizeof REMOTIX_TETTO);
  std::array<char, 256> buf{};
  auto letti = recv(fd, buf.data(), buf.size() - 1, 0);
  if (letti <= 0) {
    std::println(stderr, "REMOTIX B3: ⚠ empty command on the control socket "
                         "({} bytes read): I removed nothing",
                 letti);
    remotix_scrivi_tutto(fd, "NON-CAPITO riga vuota\n");
    return;
  }
  std::string riga{buf.data(), static_cast<size_t>(letti)};
  while (!riga.empty() && (riga.back() == '\n' || riga.back() == '\r')) {
    riga.pop_back();
  }
  if (riga == "PING") {
    std::println(stderr, "REMOTIX B3: PING command — the unblock socket is "
                         "alive, and I touched no ban");
    remotix_scrivi_tutto(fd, "PONG\n");
    return;
  }
  constexpr std::string_view verbo = "SBLOCCA ";
  if (!riga.starts_with(verbo)) {
    std::println(stderr, "REMOTIX B3: ⚠ unknown command «{}»: I removed "
                         "nothing (the forms are «SBLOCCA <address>» and «PING»)",
                 riga);
    remotix_scrivi_tutto(fd, std::format("NON-CAPITO {}\n", riga));
    return;
  }
  auto chiesto = riga.substr(verbo.size());
  // ⛔ The key is built by `rcp.c`, not by this file: whoever commands types
  //    `192.168.0.2`, and in the ban file it says `[192.168.0.2]`.
  std::array<char, 64> chiave{};
  rcp_chiave_indirizzo(chiesto.c_str(), chiave.data(), chiave.size());
  auto era = rcp_sblocca(chiave.data(), remotix_ora_ms());
  // ⛔ "Every unblock is written in the log, or a removed ban and a ban that never
  //    fired look the same" (§4.4-bis).  The two lines are
  //    different, and so is the answer to whoever commands.
  if (era) {
    std::println(stderr,
                 "REMOTIX B3: ⛔ UNBLOCKED on command the address {} (asked "
                 "«{}»): the ban was there and has been removed, and the ban file has "
                 "been rewritten (§4.4-bis)",
                 chiave.data(), chiesto);
  } else {
    std::println(stderr,
                 "REMOTIX B3: unblock asked for {} (asked «{}»): it was NOT "
                 "banned, I removed nothing (§4.4-bis) — ⚠ and the count of "
                 "attempts of that address restarts from zero anyway",
                 chiave.data(), chiesto);
  }
  remotix_scrivi_tutto(fd, std::format("{} {}\n", era ? "TOLTO" : "NON-BANNATO",
                                       chiave.data()));
}

void remotix_comando_cb(struct ev_loop *loop, ev_io *w, int revents) {
  (void)loop;
  (void)revents;
  auto fd = accept(w->fd, nullptr, nullptr);
  if (fd == -1) {
    return;
  }
  remotix_comando_servi(fd);
  close(fd);
}

// ═══ 3. THE STARTUP ═════════════════════════════════════════════════════════
//
// ⛔ "ZERO BANS" AND "I COULD NOT READ THE FILE" ARE TWO DIFFERENT FACTS, and
//    this is the function in which the defect of `LEZIONI.md` §1.9 would be the
//    most costly of all: an error read as a zero is **the protection turned off with
//    the air of having nothing to protect**, that is invariant I7 lost
//    silently.  Here the printed facts are THREE, and they are told apart by looking at the
//    file before opening it:
//
//      the file is not there yet      no ban, and it is not an error
//      the file is there and says zero no ban, and I read it
//      the file is there and cannot be read ⛔ I do NOT start
//
// ⛔ And on the third the server EXITS, which is the only defensible choice: serving with
//    the protection off looks in every way like serving with it on, and whoever
//    restarted for another reason would not know they had lost it.  ⚠ On the other
//    two faults — the page port, the command socket — the server goes
//    on: without page and without command the protection **is still there**, and
//    turning off the QUIC server on which five other benches rest would put the
//    red on the wrong suspect.  In all cases the line is printed.
bool remotix_ospite_avvia(const char *addr, const char *port) {
  auto ora = remotix_ora_ms();

  if (remotix_ban_file == nullptr) {
    std::println(stderr,
                 "REMOTIX B3: ⛔ no --ban-file: the ban of §4.4-bis lives ONLY "
                 "IN MEMORY, and the first restart takes it away (invariant I7). "
                 "The attempt count works all the same, persistence does not.");
  } else {
    struct stat st;
    auto c_era = stat(remotix_ban_file, &st) == 0;
    errno = 0;
    auto quanti = rcp_ban_carica(remotix_ban_file, ora);
    if (quanti < 0) {
      std::println(stderr,
                   "REMOTIX B3: ⛔ COULD NOT READ the ban file «{}»: "
                   "{}.  It is not «zero bans»: it is «I could not look», and "
                   "serving like this would turn off the protection of §4.4-bis "
                   "while making it look on.  Not starting.",
                   remotix_ban_file, strerror(errno));
      return false;
    }
    if (!c_era) {
      std::println(stderr,
                   "REMOTIX B3: bans loaded: 0 — the file «{}» does not exist "
                   "yet, so no address is out.  ⚠ It is not an "
                   "error: the first ban will write it.",
                   remotix_ban_file);
    } else {
      std::println(stderr,
                   "REMOTIX B3: bans loaded: {} — from the file «{}», read "
                   "in full.  {}",
                   quanti, remotix_ban_file,
                   quanti == 0
                     ? "⚠ zero addresses out, and this is a measured fact: "
                       "the file was there and I read it"
                     : "These addresses stay out until they expire or "
                       "until the unblock command removes them (§4.4-bis).");
    }
  }

  // ── the TCP port of the page, the SAME NUMBER as the UDP one (SPECIFICHE.md §4)
  addrinfo suggerimenti{};
  suggerimenti.ai_flags = AI_PASSIVE;
  suggerimenti.ai_family = AF_UNSPEC;
  suggerimenti.ai_socktype = SOCK_STREAM;
  addrinfo *elenco = nullptr;
  if (auto rv = getaddrinfo(addr, port, &suggerimenti, &elenco); rv != 0) {
    std::println(stderr,
                 "REMOTIX B3: ⛔ the TCP page does not start: getaddrinfo({}, {}) "
                 "says «{}».  Whoever gets banned will read no sentence "
                 "(§4.4-bis), and the QUIC server goes on all the same.",
                 addr, port, gai_strerror(rv));
  } else {
    auto fd = -1;
    for (auto p = elenco; p; p = p->ai_next) {
      fd = socket(p->ai_family, p->ai_socktype | SOCK_NONBLOCK, p->ai_protocol);
      if (fd == -1) {
        continue;
      }
      auto uno = 1;
      setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &uno, sizeof uno);
      if (bind(fd, p->ai_addr, p->ai_addrlen) == 0 && listen(fd, 16) == 0) {
        break;
      }
      close(fd);
      fd = -1;
    }
    freeaddrinfo(elenco);
    if (fd == -1) {
      std::println(stderr,
                   "REMOTIX B3: ⛔ the TCP page does not start: no address of "
                   "{}:{} let itself be bound ({}).  Whoever gets banned will "
                   "read no sentence (§4.4-bis), and the QUIC server goes "
                   "on all the same.",
                   addr, port, strerror(errno));
    } else {
      ev_io_init(&remotix_pagina_ev, remotix_pagina_cb, fd, EV_READ);
      ev_io_start(EV_DEFAULT, &remotix_pagina_ev);
      remotix_pagina_accesa = true;
      std::println(stderr,
                   "REMOTIX B3: the page is served over TCP on {}:{} — ⛔ and a "
                   "banned address is served ALL THE SAME, with «attempts "
                   "exhausted» and the hours that are left (§4.4-bis)",
                   addr, port);
    }
  }

  // ── the socket of the unblock command
  if (remotix_comando_socket == nullptr) {
    std::println(stderr,
                 "REMOTIX B3: ⛔ no --comando-socket: the ban is removed ONLY "
                 "by the passing of the 12 hours.  §4.4-bis wants two roads, "
                 "and this half is not there.");
  } else {
    // ⚠ The old file is removed: a socket left there by a previous
    //   run makes `bind` fail with EADDRINUSE, and the symptom — "the command
    //   does not answer" — looks in every way like a dead server.
    unlink(remotix_comando_socket);
    sockaddr_un dove{};
    dove.sun_family = AF_UNIX;
    if (strlen(remotix_comando_socket) >= sizeof dove.sun_path) {
      std::println(stderr,
                   "REMOTIX B3: ⛔ the path of the command socket is too "
                   "long ({} bytes, the maximum is {}): the unblock command "
                   "will not be there",
                   strlen(remotix_comando_socket), sizeof dove.sun_path - 1);
    } else {
      strcpy(dove.sun_path, remotix_comando_socket);
      auto fd = socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK, 0);
      if (fd == -1 ||
          bind(fd, reinterpret_cast<sockaddr *>(&dove), sizeof dove) != 0 ||
          listen(fd, 4) != 0) {
        std::println(stderr,
                     "REMOTIX B3: ⛔ the socket of the unblock command does not start "
                     "on «{}»: {}.  The ban can be removed only by waiting "
                     "12 hours (§4.4-bis).",
                     remotix_comando_socket, strerror(errno));
        if (fd != -1) {
          close(fd);
        }
      } else {
        // ⛔ 0600, and the reason is the rule: the key this command
        //    asks for is "access to the machine".  A socket readable by
        //    anyone would make it "access to any user of the
        //    machine", which is a different and easier key.
        if (chmod(remotix_comando_socket, 0600) != 0) {
          std::println(stderr,
                       "REMOTIX B3: ⚠ I could not set 0600 on «{}»: {} — "
                       "the unblock command is there, but the key it asks for is "
                       "wider than what §4.4-bis assumes",
                       remotix_comando_socket, strerror(errno));
        }
        ev_io_init(&remotix_comando_ev, remotix_comando_cb, fd, EV_READ);
        ev_io_start(EV_DEFAULT, &remotix_comando_ev);
        remotix_comando_acceso = true;
        std::println(stderr,
                     "REMOTIX B3: the unblock command listens on «{}» (0600) "
                     "— «SBLOCCA <address>» or «PING»",
                     remotix_comando_socket);
      }
    }
  }

  // ⛔ AND THE SUMMARY IS PRINTED ON ONE SINGLE LINE, with the three facts inside: it is the
  //    line a bench reads to know FROM WHICH STATE it starts (B0.1), and without
  //    which "the ban did not fire" and "the ban was not even on" look
  //    the same.
  std::println(stderr,
               "REMOTIX B3: host-side ban — persistence {} · TCP page {} · "
               "unblock command {}",
               remotix_ban_file ? remotix_ban_file : "OFF",
               remotix_pagina_accesa ? "on" : "OFF",
               remotix_comando_acceso ? remotix_comando_socket : "OFF");
  return true;
}

} // namespace

'''

# ⛔ The grafts in `server.cc`, and they are four points because four are the
#    places in which a `main` written by others lets itself be widened: the table
#    of long options, the `switch` that reads them, the help, and the line between
#    "the server is ready" and "it runs".
INNESTI_OSPITE = [
    # ── the body, right before `main` ───────────────────────────────────────
    (
        "server.cc",
        "int main(int argc, char **argv) {\n",
        None,  # ⚠ filled in `main()` with CORPO_OSPITE + the foothold
        "the host-side ban (the body)",
    ),
    # ── the two long options ────────────────────────────────────────────────
    #    ⚠ The numbers 100 and 101 are far from the example's 37 on purpose: the
    #      day ngtcp2 adds its option number 38, two cases
    #      with the same number would be an option that runs another one —
    #      and the compiler would only say "duplicate case value", if all goes well.
    (
        "server.cc",
        '      {"gso-burst", required_argument, &flag, 37},\n',
        '      {"gso-burst", required_argument, &flag, 37},\n'
        "      // ⭐ REMOTIX B3 — RCP.md §4.4-bis, the two roads of the\n"
        "      //    host: where the bans are kept between one restart and the next, and from where\n"
        "      //    removing one is commanded.\n"
        '      {"ban-file", required_argument, &flag, 100},\n'
        '      {"comando-socket", required_argument, &flag, 101},\n',
        "the two ban options",
    ),
    # ── the two cases that read them ────────────────────────────────────────
    (
        "server.cc",
        "      case 36:\n"
        "        // --show-stat\n"
        "        config.show_stat = true;\n"
        "        break;\n",
        "      case 100:\n"
        "        // ⭐ REMOTIX B3 — --ban-file (RCP.md §4.4-bis)\n"
        "        remotix_ban_file = optarg;\n"
        "        break;\n"
        "      case 101:\n"
        "        // ⭐ REMOTIX B3 — --comando-socket (RCP.md §4.4-bis)\n"
        "        remotix_comando_socket = optarg;\n"
        "        break;\n"
        "      case 36:\n"
        "        // --show-stat\n"
        "        config.show_stat = true;\n"
        "        break;\n",
        "the two ban cases",
    ),
    # ── the help ───────────────────────────────────────────────────────────
    (
        "server.cc",
        "  -h, --help  Display this help and exit.\n",
        "  --ban-file=<PATH>\n"
        "              REMOTIX B3 (RCP.md 4.4-bis): where the bans are kept between\n"
        "              one restart and the next.  Without it, the ban lives only in\n"
        "              memory.  If the file exists and cannot be read, the server does NOT\n"
        "              start: «zero bans» and «I could not look» are two\n"
        "              different facts.\n"
        "  --comando-socket=<PATH>\n"
        "              REMOTIX B3 (RCP.md 4.4-bis): the Unix domain socket\n"
        "              (0600) from which «SBLOCCA <address>» is commanded.  It is\n"
        "              the other way out besides the twelve hours.\n"
        "  -h, --help  Display this help and exit.\n",
        "the help of the two options",
    ),
    # ── and the call, between "the server is ready" and "it runs" ───────────
    #    ⛔ AFTER `s.init`: before, a failure of the server would leave open the
    #       page port and the command socket of a server that is not there.
    #    ⛔ And BEFORE `ev_run`: the two `ev_io` must be put in the loop while the
    #       loop is not running yet.
    (
        "server.cc",
        "  ev_run(EV_DEFAULT, 0);\n",
        "  // ⭐ REMOTIX B3 — RCP.md §4.4-bis: the bans from disk, the page over TCP\n"
        "  //    and the unblock command.  All three things of the HOST:\n"
        "  //    `rcp.c` opens no socket and does not read the command line.\n"
        "  if (!remotix_ospite_avvia(addr, port)) {\n"
        "    exit(EXIT_FAILURE);\n"
        "  }\n"
        "\n"
        "  ev_run(EV_DEFAULT, 0);\n",
        "the call at startup",
    ),
]


def leggi(percorso):
    with open(percorso, encoding="utf-8") as f:
        return f.read()


def righe_di_commento(righe):
    """⛔ ONE SINGLE RULE FOR COMMENTS, AND THE SAME IN THE THREE GRAFTS.

    Here the rule was "starts with //, /* or *", and it classified as
    COMMENT two lines of real C++ that are in the body grafted by B2:

        *v = src[0] & 0x3f;
        *v = (*v << 8) | src[i];

    ⚠ They are dereferences.  ⛔ The "code" number printed from here was
      therefore strictly lower than the one B2 prints on the same lines, and
      the two presented themselves with the same label.  The asterisk counts as a
      comment only when it continues or closes a `/* … */` block.
    """
    return sum(1 for r in righe
               if r.strip().startswith(("//", "/*", "* ", "*/"))
               or r.strip() == "*")


def togli():
    # ⛔ AND THE TRUTH IS TOLD ABOUT WHAT IS TAKEN AWAY.
    #
    #    Here it used to say "(the B2 graft remains)", and it was true only for
    #    `CMakeLists.txt`.  In the two files that matter — `http3_server_proto_codec`
    #    `.cc` and `.h` — the two grafts are INTERWOVEN, and removing only
    #    one's own left a tree that ⛔ **does not compile**: the `.cc` kept
    #    calling `rcp_apri`, `examples/rcp.h` had been deleted and the
    #    CMakeLists was back without `rcp.c` — with `exit 0` printed by the
    #    script that had just produced that state.
    #
    # ⭐ So the WHOLE example is put back, and we say so: they are reapplied in
    #    order, first B2 and then this one.  A `--togli` that leaves less than what
    #    the name promises is better than one that leaves rubble and keeps quiet.
    print("== Putting the example back as it was")
    print("   ⛔ the B2 graft goes away TOO (and the B11 faults, if any):")
    print("      the two live in the same two files, and a tree with half a")
    print("      graft DOES NOT COMPILE.  They are reapplied in order —")
    print("      01-b2-ngtcp2-wt-innesta.py, then this one.")
    r = subprocess.run(["git", "-C", ALBERO, "checkout", "--", "examples"])
    if r.returncode != 0:
        print(f"   ⛔ git checkout failed (exit {r.returncode}):"
              " nothing was removed.")
        return r.returncode
    for f in FILE_NOSTRI:
        try:
            os.remove(os.path.join(ESEMPI, f))
        except FileNotFoundError:
            pass

    # ⛔ AND IT IS VERIFIED THAT IT HAS REMOVED — here before `0` was returned ALWAYS,
    #    whatever had happened.  `LEZIONI.md` §1.9, fourth rule: a
    #    measurement that can say "zero" must be able to say "I failed".
    guai = 0
    for percorso in FILE_TOCCATI:
        testo = leggi(os.path.join(ESEMPI, percorso))
        for marca in (MARCA, MARCA_B2, MARCA_B11):
            n = testo.count(marca)
            if n:
                print(f"   NO  {n} lines with «{marca}» remain in {percorso}")
                guai += n
    for f in FILE_NOSTRI:
        if os.path.exists(os.path.join(ESEMPI, f)):
            print(f"   NO  examples/{f} is still there")
            guai += 1
    if guai:
        print("   ⛔ the example is NOT as it was.")
        return 3
    print("   OK  no trace of B2, B3 or B11, and our files are gone")
    return 0


def main():
    if "--togli" in sys.argv:
        return togli()

    print("== The RCP graft in the ngtcp2 example")
    testo_cc = leggi(os.path.join(ESEMPI, "http3_server_proto_codec.cc"))
    if MARCA in testo_cc:
        print("   ⚠ the graft is already there: nothing is touched.")
        return 0

    # ⛔ AND FIRST OF ALL WE ASK WHETHER B2 IS THERE.
    #
    #    Six of our footholds come from text that B2 introduced: without
    #    that graft they all count zero, and the diagnosis that came out was
    #    "the footholds are not ONE" — that is, it sent people to reread the grafts
    #    while the defect was that the denominator was missing.  ⚠ It is form E6,
    #    the sender deduced instead of asked (`CODER.md` §3.7).
    if MARCA_B2 not in testo_cc:
        print(f"   ⛔ the B2 graft is missing: «{MARCA_B2}» does not appear in")
        print("      http3_server_proto_codec.cc.")
        print("      This graft rests on it: apply first")
        print("      01-b2-ngtcp2-wt-innesta.py, then this command again.")
        return 2

    lista = list(INNESTI) + [
        ("http3_server_proto_codec.cc",
         "std::expected<void, Error> ProtoCodec::wt_apri_sessione(Stream *stream) {\n",
         None, "the body of the hooks"),
    ] + list(INNESTI_OSPITE)
    testi, guasti = {}, 0
    for percorso, appiglio, sostituto, nome in lista:
        if sostituto is None:
            # ⚠ Two bodies, and each has its own file: the hooks one goes into the
            #   codec, the host-side ban one goes into `main`.  Before, here
            #   there was a single `CORPO` and the choice did not exist.
            corpo = CORPO_OSPITE if percorso == "server.cc" else CORPO
            sostituto = corpo + appiglio
        if percorso not in testi:
            with open(os.path.join(ESEMPI, percorso), encoding="utf-8") as f:
                testi[percorso] = f.read()
        n = testi[percorso].count(appiglio)
        stato = "OK " if n == 1 else "NO "
        print(f"   {stato} {nome:34s} foothold found {n} time(s)  [{percorso}]")
        if n != 1:
            guasti += 1
            continue
        testi[percorso] = testi[percorso].replace(appiglio, sostituto, 1)

    # the two public declarations of the hooks, in the class
    a = ("  void wt_accoda(int64_t stream_id, std::span<const uint8_t> dati);\n")
    if testi["http3_server_proto_codec.h"].count(a) == 1:
        testi["http3_server_proto_codec.h"] = testi["http3_server_proto_codec.h"].replace(
            a, a + "\n"
                   " public:\n"
                   "  // ⭐ REMOTIX B3 — public because the hooks call them, which\n"
                   "  //    sit in an anonymous namespace outside the class: it is the\n"
                   "  //    price of keeping `rcp.c` in C, and it is paid in two lines.\n"
                   "  void wt_manda_controllo(const uint8_t *dati, size_t len);\n"
                   "  void wt_chiudi_adesso(uint8_t motivo);\n"
                   "  void wt_chiudi_sessione(uint8_t motivo);\n"
                   "\n"
                   " private:\n", 1)
        print("   OK  the two public hooks               foothold found 1 time(s)")
    else:
        print("   NO  the two public hooks               foothold NOT unique")
        guasti += 1

    if guasti:
        print(f"\n   ⛔ {guasti} footholds are not ONE: nothing is written,")
        print("      and no file has been copied.")
        return 2

    # ⛔ AND OUR FILES ARE COPIED ONLY NOW.
    #
    #    Before, they were copied at the top, BEFORE looking at the footholds: the exit
    #    with 2 printed "nothing is written" on a tree in which `rcp.c`,
    #    `rcp.h` and `autenticazione.c` had already been written — that is, the error
    #    outcome left the tree in a state the error outcome denied
    #    (`LEZIONI.md` §1.9).
    #
    # ⛔ Our files are COPIED, not linked: the ngtcp2 tree belongs to
    #    someone else, and a symbolic link pointing outside breaks
    #    silently the day someone reclones it.
    for f in FILE_NOSTRI:
        shutil.copyfile(os.path.join(SORGENTI, f), os.path.join(ESEMPI, f))
    print(f"\n   OK  {len(FILE_NOSTRI)} of our files copied into examples/")

    for percorso, testo in testi.items():
        with open(os.path.join(ESEMPI, percorso), "w", encoding="utf-8") as f:
            f.write(testo)
    print(f"   OK  {len(lista) + 1} grafts, in {len(testi)} files")

    print("\n== How many lines changed — and they are TWO different numbers")
    d = subprocess.run(["git", "-C", ALBERO, "diff", "-U0", "--",
                        "examples"], capture_output=True, text=True).stdout.splitlines()
    agg = [r[1:] for r in d if r.startswith("+") and not r.startswith("+++")]
    vuote = sum(1 for r in agg if not r.strip())
    cod = len(agg) - vuote - righe_di_commento(agg)
    print(f"   inside the example (B2 + the wires of B3): {len(agg)} lines, {cod} of code")
    for f in FILE_NOSTRI:
        righe = leggi(os.path.join(SORGENTI, f)).splitlines()
        vuote = sum(1 for r in righe if not r.strip())
        cod = len(righe) - vuote - righe_di_commento(righe)
        # ⚠ And the name of the place is the REAL one: here it used to print
        #   `banchi/rcp/<file>` while reading `/srv/src/rcp/<file>` — the
        #   count was right and the place was not, which is the most convenient way of
        #   looking at the wrong file for half an hour.
        print(f"   {SORGENTI}/{f:<20s} {len(righe):>4} lines, {cod:>4} of code")
    print("\n   ⭐ The second group is the PROTOCOL, and it does not depend on ngtcp2:")
    print("      it is what is carried away if one day the library changes.")
    print("\n   ⚠ And the rule for saying what a comment is is ONE SINGLE one, the")
    print("     same as the three grafts: until 10 Aug there were three different ones, and")
    print("     this one counted the dereferences `*v = …` as comments.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
