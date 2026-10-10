#!/usr/bin/env python3
"""01-b2-ngtcp2-wt-innesta.py — grafts the WebTransport layer into the ngtcp2 example.

    python3 01-b2-ngtcp2-wt-innesta.py            grafts (or says it is already there)
    python3 01-b2-ngtcp2-wt-innesta.py --togli    puts the example back as it was

---------------------------------------------------------------------------
⛔ WHY A GRAFT AND NOT A SERVER OF OUR OWN

`banchi/01-b2-costruisci-ngtcp2.sh` has already written it, and it is the rule of B2:
**we start where anyone starts**, that is from the project's example server.
A server of our own from a blank page would measure our patience — the UDP
loop, the TLS, the retransmission timers — and not the library.  What B2 must
measure is **how much glue is left to us FOR WEBTRANSPORT**, and the way to
measure it is to add that layer to an HTTP/3 that already works and count
the lines.

⭐ And the count comes by itself: after the graft, `git diff --stat` in the
   ngtcp2 tree says how many lines changed under `examples/`.

⚠ **"Changed" is not "ours", and here it used to say it was not an estimate.**
  `git diff` cannot attribute a line: it measures everything that changed in
  that folder, **by anyone**.  It counts as OUR count only if the tree
  was clean before — and that is why the script now **looks and says so**,
  instead of taking it for granted (`LEZIONI.md` §1.9, fourth rule: a
  denominator is read where the thing happens).
  ⚠ And a **modified** line shows up among the additions: "added" is an upper
  bound of "ours", not their exact number.

---------------------------------------------------------------------------
⛔ WHAT `ngtcp2`+`nghttp3` LACK, IN CONCRETE TERMS

The survey of 9 Aug said "the foundations yes, the layer no".  Now
we know **which** the three holes are, because they are the three points this file
touches:

  1. ⛔ **WebTransport cannot be announced.**  `nghttp3_settings` has
     `enable_connect_protocol` and `h3_datagram` — the two that are in the RFCs —
     and nothing else; the public API offers `submit_request`, `submit_info`,
     `submit_response`, `submit_trailers`, `submit_shutdown_notice`, and
     **no way of putting an arbitrary setting** on the control
     stream.  `SETTINGS_WT_MAX_SESSIONS`, which is what browsers
     look for, does not go through there.  We rewrite the SETTINGS that nghttp3 is
     writing, while it writes it.

  2. ⛔ **The WebTransport streams must be taken away from nghttp3.**  They start with
     frame type `0x41` followed by the session number, and nghttp3
     would read that number as a LENGTH.

  3. ⛔ **And the bytes going back have no road.**  nghttp3 does not
     know those streams, so it will never put them among the vectors to
     write: the output queue is ours.

⚠ None of the three is a defect of ngtcp2 or of nghttp3: they do HTTP/3, and
  WebTransport is not HTTP/3.  It is exactly the price §6.4 wanted
  to know before choosing.

---------------------------------------------------------------------------
⛔ HOW THIS SCRIPT AVOIDS LYING

Every graft has a **foothold**, that is a piece of their code that must
appear **once only**.  If it appears zero times or twice, the script stops
and says how many it found: it is the fourth rule of `LEZIONI.md` §1.9 — a
denominator, not only a result.  ⚠ A graft that "does not find the foothold"
and carries on would produce a server that compiles, does not do WebTransport, and does not
say so.
"""
import os
import subprocess
import sys

ALBERO = "/srv/src/b2/ngtcp2"
ESEMPI = "/srv/src/b2/ngtcp2/examples"
MARCA = "REMOTIX B2"
MARCA_B3 = "REMOTIX B3"
MARCA_B11 = "REMOTIX B11 GUASTO"

# ⛔ The files this graft touches.  `--togli` needs them to VERIFY that it
#    removed: the exit status of `git` says git did not complain, not
#    that the mark is gone.
FILE_TOCCATI = [
    "http3_server_proto_codec.h",
    "http3_server_proto_codec.cc",
    "server.h",
    "server.cc",
    "tls_server_session_boringssl.cc",
]

# ⛔ The files B3 copies into `examples/`.  Git does not touch untracked
#    files, so after `--togli` they stay there and nobody says so.
FILE_DI_B3 = ["rcp.c", "rcp.h", "autenticazione.c"]

# ---------------------------------------------------------------------------
# The pieces of code, at the bottom of the file so as not to break the reading.
# Every entry is: (file, foothold, replacement, readable name)
# ---------------------------------------------------------------------------


def innesti():
    return [
        # ── 1. The headers the new types need ───────────────────────────────
        (
            "http3_server_proto_codec.h",
            "#include <vector>\n#include <expected>\n#include <optional>\n",
            "#include <vector>\n#include <expected>\n#include <optional>\n"
            "// ⭐ REMOTIX B2 — for the output queue and the classification of streams\n"
            "#include <array>\n#include <deque>\n#include <span>\n"
            "#include <string>\n#include <unordered_map>\n",
            "codec headers",
        ),
        # ── 2. The state of the WebTransport layer ──────────────────────────
        (
            "http3_server_proto_codec.h",
            "  Handler *handler_;\n"
            "  ngtcp2_conn *conn_;\n"
            "  ngtcp2_ccerr &last_error_;\n"
            "  nghttp3_conn *httpconn_{};\n"
            "};\n",
            """  // ═══ ⭐ REMOTIX B2 — the WebTransport layer ═════════════════════════
  //
  // ⛔ It is here and not in the library because nghttp3 has no place to
  //    put it: it does HTTP/3, and WebTransport is not HTTP/3.  The lines from here
  //    down are the glue of `DECISIONI.md` §6.4, and they are counted.
  enum class WtEsito {
    MIO,     // it is WebTransport stuff: I handled it
    ATTENDI, // I do not have enough bytes yet to decide
    HTTP3,   // it is not WebTransport: pass it to nghttp3
  };

  struct WtUscita {
    int64_t stream_id;
    std::vector<uint8_t> dati;
    size_t off;
  };

  std::expected<void, Error> wt_apri_sessione(Stream *stream);
  size_t wt_riscrivi_impostazioni(const nghttp3_vec *vec, size_t veccnt);
  // ⛔ `fin` is not an extra: RCP.md §4.2 says that "a FIN on that stream,
  //    from either side, closes the session", and without this
  //    parameter the information does not get in here in any way — for the streams
  //    we recognise not even nghttp3 sees it, because we return first.
  WtEsito wt_smista(int64_t stream_id, std::span<const uint8_t> data, bool fin,
                    std::vector<uint8_t> &riunito);
  void wt_accoda(int64_t stream_id, std::span<const uint8_t> dati);

 public:
  // ⛔⭐ THE CAPSULE WITH WHICH THE CLIENT CLOSES THE SESSION.
  //
  //    A WebTransport session does not end only when the connection
  //    dies: the client closes it by sending `CLOSE_WEBTRANSPORT_SESSION`
  //    (capsule 0x2843) on the CONNECT stream, **with a code and a
  //    reason inside**.  ⚠ Until 10 Aug 2026 this server did not read
  //    it: those bytes ended up in the HTTP body and nobody looked at them.
  //
  // ⭐ It is public because `http_recv_data` calls it, and that sits in an
  //    anonymous namespace outside the class.
  void wt_capsula(int64_t stream_id, std::span<const uint8_t> dati);

 private:
  // ⚠ What the client's closing MEANS is not decided by this layer:
  //   here the body is empty, and B3 grafts the RCP line into it.
  //
  // ⛔ AND THE CODE ARRIVES ON 32 BITS, NOT ON 8.  The capsule carries four
  //    bytes of it, and truncating it to the low byte entered `0x0100` in the record as
  //    `0x00` — that is as the **only** value RCP.md §3.1 explicitly
  //    forbids ("closing without a reason … MUST NOT be used").  Whoever
  //    receives it checks that it is one of the reasons of §8.2, and if it is not
  //    says so: §3 asks to write what was not understood, not to fill in.
  void wt_chiusa_dal_client(uint32_t codice);

  // ⛔ THE CLIENT'S FIN ON THE CONTROL CHANNEL.  RCP.md §4.2: "a FIN on
  //    that stream, from either side, closes the session.
  //    Whoever receives it MUST consider it ended".  ⚠ It was the only one of the two
  //    directions nobody had walked: the page that closes the writing side
  //    of the channel and keeps the connection alive left the slot in the
  //    register occupied until the connection died — and a connection
  //    a browser keeps alive.
  //
  // ⚠ Empty here for the same reason as above: what "ended" is, RCP
  //   knows, not the transport.  B3 grafts the line into it.
  void wt_fin_dal_client(int64_t stream_id);

  Handler *handler_;
  ngtcp2_conn *conn_;
  ngtcp2_ccerr &last_error_;
  nghttp3_conn *httpconn_{};
  // the HTTP/3 control stream: needed to recognise it when writing, which is
  // the only instant in which the browser can be told we speak WebTransport
  int64_t wt_ctrl_id_{-1};
  bool wt_impostazioni_scritte_{false};
  bool wt_guasto_{false};
  std::array<uint8_t, 256> wt_impbuf_;
  size_t wt_impbuf_len_{0};
  // ⛔ How many bytes of the rewritten SETTINGS have ALREADY LEFT, and how many bytes of
  //    nghttp3 that buffer replaces.  They are needed because a **partial**
  //    write is a normal outcome of `ngtcp2_conn_writev_stream` — not
  //    a fault — and it used to kill the connection: now we resume from the
  //    point we had reached, as has always been done for `wt_uscita_`.
  size_t wt_impbuf_off_{0};
  size_t wt_impbuf_orig_{0};
  // the client's bidirectional streams: those of which we do not know yet what
  // they are, those that are WebTransport, those that are not
  std::unordered_map<int64_t, std::vector<uint8_t>> wt_incerti_;
  std::unordered_map<int64_t, int64_t> wt_streams_;
  std::unordered_map<int64_t, bool> wt_nonwt_;
  std::deque<WtUscita> wt_uscita_;
  int64_t wt_sessione_{-1};
  // ⛔ Our queue is blocked for THIS write pass: ngtcp2 has
  //    said STREAM_DATA_BLOCKED, and retrying inside the same pass
  //    would be a loop that does not advance.  It is reset at the top of `write_pkt`.
  bool wt_coda_bloccata_{false};
  // the bytes of the CONNECT that do not make up a whole capsule yet
  std::vector<uint8_t> wt_capsbuf_;
  // ⛔ How many bytes of a capsule already judged TOO BIG are still to be
  //    thrown away as they pass.  RCP.md §6.1: "the length is checked before
  //    allocating" — and waiting for the bytes instead of allocating them is the same
  //    gift, given more slowly.
  uint64_t wt_capsalta_{0};
};
""",
            "the state of the WebTransport layer",
        ),
        # ── 3. The two settings nghttp3 can do by itself ────────────────────
        (
            "http3_server_proto_codec.cc",
            "  settings.qpack_max_dtable_capacity = 4096;\n"
            "  settings.qpack_blocked_streams = 100;\n",
            "  settings.qpack_max_dtable_capacity = 4096;\n"
            "  settings.qpack_blocked_streams = 100;\n"
            "\n"
            "  // ⭐ REMOTIX B2 — the two nghttp3 can do by itself, and they are in the RFCs.\n"
            "  settings.enable_connect_protocol = 1; // RFC 9220, the extended CONNECT\n"
            "  settings.h3_datagram = 1;             // RFC 9297 (RCP.md §2.2)\n",
            "the settings nghttp3 knows",
        ),
        # ── 4. The number of the control stream ─────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "  if (auto rv = nghttp3_conn_bind_control_stream(httpconn_, ctrl_stream_id);\n",
            "  // ⭐ REMOTIX B2 — the number is kept: when nghttp3 writes its\n"
            "  //    SETTINGS on this stream it will be the only chance to add\n"
            "  //    the two WebTransport declarations to it.\n"
            "  wt_ctrl_id_ = ctrl_stream_id;\n"
            "\n"
            "  if (auto rv = nghttp3_conn_bind_control_stream(httpconn_, ctrl_stream_id);\n",
            "the number of the control stream",
        ),
        # ── 5. The guard at the top of the write loop ───────────────────────
        (
            "http3_server_proto_codec.cc",
            "  std::array<nghttp3_vec, 16> vec;\n\n  for (;;) {\n",
            "  std::array<nghttp3_vec, 16> vec;\n"
            "\n"
            "  // ⭐ REMOTIX B2 — a write pass starts here, and our queue\n"
            "  //    restarts UNBLOCKED: `wt_coda_bloccata_` holds for one\n"
            "  //    pass only.  ⚠ It is outside the loop on purpose — resetting it\n"
            "  //    inside would put the same element back in play at every round,\n"
            "  //    which is precisely the loop that does not advance.\n"
            "  wt_coda_bloccata_ = false;\n"
            "\n"
            "  for (;;) {\n"
            "    // ⭐ REMOTIX B2 — if the rewriting of the settings has lost\n"
            "    //    count, we stop: an out-of-step control stream is worse\n"
            "    //    than a closed connection.\n"
            "    // ⚠ It is NOT the case of the PARTIAL write, which is a normal\n"
            "    //   outcome and is resumed at the next pass: see `wt_conta`.\n"
            "    if (wt_guasto_) {\n"
            "      return NGTCP2_ERR_CALLBACK_FAILURE;\n"
            "    }\n"
            "\n",
            "the guard of the write loop",
        ),
        # ── 6. The choice of what to write ──────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "    ngtcp2_ssize ndatalen;\n"
            "    auto v = vec.data();\n"
            "    auto vcnt = static_cast<size_t>(sveccnt);\n",
            """    // ═══ ⭐ REMOTIX B2 ═══════════════════════════════════════════════════
    // Two things nghttp3 cannot do, and they must be done right here:
    //   1. adding the WebTransport settings to the SETTINGS that it is
    //      writing itself — there is no other moment;
    //   2. sending bytes on a stream it DOES NOT KNOW, which otherwise
    //      would never leave the machine.
    std::array<nghttp3_vec, 1> wt_vec;
    size_t wt_orig = 0;
    bool wt_mio = false;

    if (sveccnt > 0 && stream_id == wt_ctrl_id_ && !wt_impostazioni_scritte_) {
      // ⛔ The rewriting is done ONCE ONLY.  If the previous pass sent
      //    only a piece of it (`wt_impbuf_off_ > 0`), nghttp3 offers us again
      //    the same bytes — we have not told it yet that we consumed them
      //    — and rebuilding the buffer from scratch would resend the piece already gone.
      if (wt_impbuf_off_ == 0) {
        wt_impbuf_orig_ =
          wt_riscrivi_impostazioni(vec.data(), static_cast<size_t>(sveccnt));
      }
      wt_orig = wt_impbuf_orig_;
    }
    // ⛔ And our queue is SKIPPED for this whole pass if ngtcp2 has already
    //    said "blocked" on it: see the STREAM_DATA_BLOCKED branch further
    //    down.  Retrying now would not make the loop advance.
    if (sveccnt <= 0 && !wt_coda_bloccata_ && !wt_uscita_.empty()) {
      auto &u = wt_uscita_.front();
      stream_id = u.stream_id;
      fin = 0;
      wt_vec[0].base = u.dati.data() + u.off;
      wt_vec[0].len = u.dati.size() - u.off;
      wt_mio = true;
    }

    ngtcp2_ssize ndatalen;
    auto v = vec.data();
    auto vcnt = static_cast<size_t>(sveccnt);

    if (wt_orig) {
      wt_vec[0].base = wt_impbuf_.data() + wt_impbuf_off_;
      wt_vec[0].len = wt_impbuf_len_ - wt_impbuf_off_;
      v = wt_vec.data();
      vcnt = 1;
    } else if (wt_mio) {
      v = wt_vec.data();
      vcnt = 1;
    }

    // How many bytes OF NGHTTP3 were consumed.  If its buffer was
    // replaced, the number ngtcp2 returns is OURS, and telling it
    // would put its accounts out of step.
    auto wt_conta = [&](ngtcp2_ssize n) -> uint64_t {
      auto c = as_unsigned(n);
      if (!wt_orig) {
        return c;
      }
      // ⛔⭐ AND A PARTIAL WRITE IS NOT A FAULT.
      //
      //    `ndatalen` smaller than the offered length is a NORMAL outcome of
      //    `ngtcp2_conn_writev_stream`: into the stream frame goes whatever
      //    is left in the packet.  The ~24 bytes of the rewritten SETTINGS travel
      //    in the first flight after the handshake, the one that also carries
      //    HANDSHAKE_DONE, the NEW_CONNECTION_IDs and any NEW_TOKEN: with a
      //    client that announces `max_udp_payload_size` close to 1200 and a
      //    20-byte connection id, 24 bytes do not fit in there.
      //
      // ⛔ Before, here THE CONNECTION DIED, while ten lines further down
      //    our queue handled the same partial write with `u.off`.
      //    Two opposite policies for the same outcome, in the same module.
      if (c > wt_impbuf_len_ - wt_impbuf_off_) {
        // ⛔ This yes: ngtcp2 declares it took MORE than what it was
        //    offered.  It is not recoverable and cannot be told apart from a
        //    wrong count of ours: the control stream would be out of step.
        std::println(stderr,
                     "REMOTIX B2: settings, impossible count ({} taken of "
                     "{} offered)",
                     c, wt_impbuf_len_ - wt_impbuf_off_);
        wt_guasto_ = true;
        return 0;
      }
      wt_impbuf_off_ += static_cast<size_t>(c);
      if (wt_impbuf_off_ < wt_impbuf_len_) {
        // We resume at the next pass, and nghttp3 is not told anything
        // yet: it will have consumed its bytes only when the rewritten
        // buffer has gone out entirely.
        std::println(stderr,
                     "REMOTIX B2: settings, {} bytes of {} — the rest at the "
                     "next pass",
                     wt_impbuf_off_, wt_impbuf_len_);
        return 0;
      }
      wt_impostazioni_scritte_ = true;
      return wt_orig;
    };

    auto wt_avanza = [&](ngtcp2_ssize n) -> int {
      if (wt_mio) {
        auto &u = wt_uscita_.front();
        u.off += static_cast<size_t>(n);
        if (u.off >= u.dati.size()) {
          wt_uscita_.pop_front();
        }
        return 0;
      }
      return nghttp3_conn_add_write_offset(httpconn_, stream_id, wt_conta(n));
    };
""",
            "the choice of what to write",
        ),
        # ── 7. The two blocking branches, which do not apply to our streams ─
        (
            "http3_server_proto_codec.cc",
            "      case NGTCP2_ERR_STREAM_DATA_BLOCKED:\n"
            "        assert(ndatalen == -1);\n"
            "        nghttp3_conn_block_stream(httpconn_, stream_id);\n"
            "        continue;\n"
            "      case NGTCP2_ERR_STREAM_SHUT_WR:\n"
            "        assert(ndatalen == -1);\n"
            "        nghttp3_conn_shutdown_stream_write(httpconn_, stream_id);\n"
            "        continue;\n",
            "      case NGTCP2_ERR_STREAM_DATA_BLOCKED:\n"
            "        assert(ndatalen == -1);\n"
            "        // ⭐ REMOTIX B2 — nghttp3 does not know the WebTransport streams:\n"
            "        //    telling it to block one would be an error on a stream that\n"
            "        //    for it does not exist.\n"
            "        //\n"
            "        // ⛔⭐ AND THE BYTES ARE NOT THROWN AWAY: THIS IS A RELIABLE CHANNEL.\n"
            "        //\n"
            "        //    Here there was `pop_front()`, which discarded the WHOLE element —\n"
            "        //    including the case `u.off > 0`, that is when a part had\n"
            "        //    already gone out on the wire.  The next message welded itself to those\n"
            "        //    truncated bytes, and the client read an invented\n"
            "        //    `tipo`/`lunghezza`: RCP.md §6.1 requires it to close with\n"
            "        //    ERRORE_PROTOCOLLO.  ⛔ It was the SERVER fabricating the\n"
            "        //    client's violation, and the log said \"bytes\n"
            "        //    thrown away\" — which described the loss without saying it had\n"
            "        //    corrupted the stream, and without warning RCP of anything.\n"
            "        //\n"
            "        // ⚠ And STREAM_DATA_BLOCKED is not a fault: it is the normal\n"
            "        //   and transient condition that dissolves with the first\n"
            "        //   MAX_STREAM_DATA.  Our queue is skipped for this\n"
            "        //   pass and retried at the next — which comes with the\n"
            "        //   packet that carries the credit.\n"
            "        if (wt_mio) {\n"
            "          auto &u = wt_uscita_.front();\n"
            "          std::println(stderr,\n"
            "                       \"REMOTIX B2: stream {} blocked: {} bytes STAY \"\n"
            "                       \"queued ({} already gone), retrying at the \"\n"
            "                       \"next pass\",\n"
            "                       stream_id, u.dati.size() - u.off, u.off);\n"
            "          wt_coda_bloccata_ = true;\n"
            "          continue;\n"
            "        }\n"
            "        nghttp3_conn_block_stream(httpconn_, stream_id);\n"
            "        continue;\n"
            "      case NGTCP2_ERR_STREAM_SHUT_WR:\n"
            "        assert(ndatalen == -1);\n"
            "        if (wt_mio) {\n"
            "          wt_uscita_.pop_front();\n"
            "          continue;\n"
            "        }\n"
            "        nghttp3_conn_shutdown_stream_write(httpconn_, stream_id);\n"
            "        continue;\n",
            "the two blocking branches",
        ),
        # ── 8. The two points that advance the offset ───────────────────────
        (
            "http3_server_proto_codec.cc",
            "      case NGTCP2_ERR_WRITE_MORE:\n"
            "        assert(ndatalen >= 0);\n"
            "        if (auto rv = nghttp3_conn_add_write_offset(httpconn_, stream_id,\n"
            "                                                    as_unsigned(ndatalen));\n"
            "            rv != 0) {\n",
            "      case NGTCP2_ERR_WRITE_MORE:\n"
            "        assert(ndatalen >= 0);\n"
            "        // ⭐ REMOTIX B2 — goes through wt_avanza: see above\n"
            "        if (auto rv = wt_avanza(ndatalen); rv != 0) {\n",
            "the advance in the WRITE_MORE branch",
        ),
        (
            "http3_server_proto_codec.cc",
            "    if (ndatalen >= 0) {\n"
            "      if (auto rv = nghttp3_conn_add_write_offset(httpconn_, stream_id,\n"
            "                                                  as_unsigned(ndatalen));\n"
            "          rv != 0) {\n",
            "    if (ndatalen >= 0) {\n"
            "      // ⭐ REMOTIX B2 — ditto\n"
            "      if (auto rv = wt_avanza(ndatalen); rv != 0) {\n",
            "the final advance",
        ),
        # ── 9. The sorting on read ──────────────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "  if (!httpconn_) {\n    return {};\n  }\n\n"
            "  auto nconsumed = nghttp3_conn_read_stream2(\n",
            "  if (!httpconn_) {\n    return {};\n  }\n\n"
            "  // ⭐ REMOTIX B2 — the WebTransport streams are none of nghttp3's business:\n"
            "  //    it would read 0x41 as an unknown frame type and then the number\n"
            "  //    of the session as a LENGTH, throwing off all the rest.\n"
            "  //    ⛔ And the FIN travels with them: RCP.md §4.2 makes it the end\n"
            "  //       of the session, and for a stream we handle ourselves this is\n"
            "  //       the LAST place where it can be seen — below we return\n"
            "  //       before `nghttp3_conn_read_stream2`, so not even\n"
            "  //       nghttp3 meets it.\n"
            "  std::vector<uint8_t> wt_riunito;\n"
            "  switch (wt_smista(stream_id, data,\n"
            "                    (flags & NGTCP2_STREAM_DATA_FLAG_FIN) != 0,\n"
            "                    wt_riunito)) {\n"
            "  case WtEsito::MIO:\n"
            "  case WtEsito::ATTENDI:\n"
            "    return {};\n"
            "  case WtEsito::HTTP3:\n"
            "    if (!wt_riunito.empty()) {\n"
            "      data = std::span<const uint8_t>{wt_riunito};\n"
            "    }\n"
            "    break;\n"
            "  }\n"
            "\n"
            "  auto nconsumed = nghttp3_conn_read_stream2(\n",
            "the sorting on read",
        ),
        # ── 9-bis. ⛔⭐ THE CAPSULE WITH WHICH THE CLIENT CLOSES THE SESSION ──
        #    The body of the CONNECT is not a body: it is a flow of capsules
        #    (RFC 9297), and inside it travels `CLOSE_WEBTRANSPORT_SESSION` with
        #    the code and the reason.  ⚠ Here it ended up in the debug log and
        #    nothing else — that is, the server did not know **why** the client
        #    had gone away, and `RCP.md` §3.1 point 3 makes the reason travel
        #    precisely from there.
        #
        # ⭐ Found by bench B11 on 10 Aug 2026: Firefox **resets** the
        #    control stream throwing away the `CONGEDO` already queued, and the
        #    reason arrives only inside the capsule.  Without reading it, of that
        #    engine one would have said "it does not say farewell" — which is false.
        (
            "http3_server_proto_codec.cc",
            "  auto pc = static_cast<ProtoCodec *>(user_data);\n"
            "  pc->http_consume(stream_id, datalen);\n",
            "  auto pc = static_cast<ProtoCodec *>(user_data);\n"
            "  // ⭐ REMOTIX B2 — the body of the CONNECT is a flow of capsules.\n"
            "  pc->wt_capsula(stream_id, {data, datalen});\n"
            "  pc->http_consume(stream_id, datalen);\n",
            "the closing capsule on read",
        ),
        # ── 10. The :protocol header ────────────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "  case NGHTTP3_QPACK_TOKEN__AUTHORITY:\n"
            "    stream->authority = std::string{v.base, v.base + v.len};\n"
            "    break;\n"
            "  }\n",
            "  case NGHTTP3_QPACK_TOKEN__AUTHORITY:\n"
            "    stream->authority = std::string{v.base, v.base + v.len};\n"
            "    break;\n"
            "  // ⭐ REMOTIX B2 — the header that tells an extended CONNECT from\n"
            "  //    a normal CONNECT (RFC 9220).\n"
            "  case NGHTTP3_QPACK_TOKEN__PROTOCOL:\n"
            "    stream->protocol = std::string{v.base, v.base + v.len};\n"
            "    break;\n"
            "  }\n",
            "the :protocol header",
        ),
        # ── 11. The extended CONNECT ────────────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "ProtoCodec::http_end_request_headers(Stream *stream) {\n"
            "  if (config.early_response) {\n",
            "ProtoCodec::http_end_request_headers(Stream *stream) {\n"
            "  // ⭐ REMOTIX B2 — this is where the WebTransport session is born.\n"
            "  if (stream->method == \"CONNECT\" && stream->protocol == \"webtransport\") {\n"
            "    return wt_apri_sessione(stream);\n"
            "  }\n"
            "\n"
            "  if (config.early_response) {\n",
            "the extended CONNECT",
        ),
        # ── 12. The body of the layer ───────────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "std::expected<void, Error> ProtoCodec::setup_httpconn() {\n",
            None,  # filled below from CORPO
            "the body of the WebTransport layer",
        ),
        # ── 13. The :protocol field in the Stream ───────────────────────────
        (
            "server.h",
            "  std::string authority;\n  std::string status_resp_body;\n",
            "  std::string authority;\n"
            "  // ⭐ REMOTIX B2 — the :protocol of the extended CONNECT, and the sign that\n"
            "  //    this stream IS the session (it does not close like a request)\n"
            "  std::string protocol;\n"
            "  bool wt_session{};\n"
            "  std::string status_resp_body;\n",
            "the :protocol field",
        ),
        # ── 14. The transport parameters ────────────────────────────────────
        (
            "server.cc",
            "  params.max_idle_timeout = config.timeout;\n",
            "  params.max_idle_timeout = config.timeout;\n"
            "  // ⛔ REMOTIX B2 — RCP.md §2.3: the server MUST grant the client\n"
            "  //    at least **16** unidirectional streams \"at any moment\".  Their\n"
            "  //    example grants 3 — as many as HTTP/3 wants for the\n"
            "  //    control and QPACK — and with that credit the client would not\n"
            "  //    even open the input stream: the symptom would be\n"
            "  //    \"the desktop does not respond\", not \"credit exhausted\".\n"
            "  //    ⚠ Found on 10 Aug while measuring the properties that remained,\n"
            "  //      and NOT from the session, which opened all the same: the session\n"
            "  //      opens perfectly well with 3.\n"
            "  // ⛔⭐ NINETEEN, NOT SIXTEEN — finding R12-A.42, 11 Aug\n"
            "  //    2026, and B12 found it while certifying B2.\n"
            "  //    `RCP.md` §2.3: \"at least 16 AVAILABLE at any moment,\n"
            "  //    that is at least 19 DECLARED at the QUIC level\" — because HTTP/3\n"
            "  //    takes 3 of them for itself (control + the two QPACK tables)\n"
            "  //    before RCP sees one.\n"
            "  //    ⛔ With 16 declared the transport probe measures 13\n"
            "  //    available, and B2 is red ON THE HEALTHY CODE. ⚠ The product\n"
            "  //    server (`src/trasporto.c:584`) already declared 19: the\n"
            "  //    box of §2.3 had reached there and not here.\n"
            "  if (params.initial_max_streams_uni < 19) {\n"
            "    params.initial_max_streams_uni = 19;\n"
            "  }\n"
            "  // ⭐ REMOTIX B2 — RCP.md §2.2: datagrams MUST be enabled\n"
            "  //    on the HTTP/3 connection (it is the audio).  ⛔ And without THIS\n"
            "  //    transport parameter, announcing SETTINGS_H3_DATAGRAM=1 is a\n"
            "  //    protocol error: the test client refuses it with\n"
            "  //    \"H3_DATAGRAM requires max_datagram_frame_size\".\n"
            "  params.max_datagram_frame_size = 65536;\n"
            "  std::println(stderr,\n"
            "               \"REMOTIX B2: max_idle_timeout={}ms max_datagram_frame_size={} \"\n"
            "               \"streams_bidi={} streams_uni={}\",\n"
            "               params.max_idle_timeout / NGTCP2_MILLISECONDS,\n"
            "               params.max_datagram_frame_size,\n"
            "               params.initial_max_streams_bidi,\n"
            "               params.initial_max_streams_uni);\n",
            "the transport parameters",
        ),
        # ── 15. ⛔ 0-RTT, which their example turns on ───────────────────────
        (
            "tls_server_session_boringssl.cc",
            "  SSL_set_early_data_enabled(ssl_, 1);\n",
            "  // ⛔ REMOTIX B2 — RCP.md §2.3: the server MUST NOT offer 0-RTT.\n"
            "  //\n"
            "  //    0-RTT data can be REPLAYED, and the second message of\n"
            "  //    RCP is `CREDENZIALI`.  The gain would be one network round trip on\n"
            "  //    a session that lasts hours.\n"
            "  //\n"
            "  // ⚠ Their example turns it on, and it is the norm: `FASI.md` §01-filo-nudo\n"
            "  //   had FORESEEN it — \"QUIC libraries offer it by default\"\n"
            "  //   — and had also written why no functional bench\n"
            "  //   would notice: **the symptom does not exist**.  The\n"
            "  //   session opens the same, the bytes come back the same.  It is seen only\n"
            "  //   by looking at the session tickets on the wire, and that is how it\n"
            "  //   came out on 10 Aug 2026 `[M]`.\n"
            "  SSL_set_early_data_enabled(ssl_, 0);\n",
            "0-RTT, turned off",
        ),
    ]


CORPO = r'''namespace {
// ⭐ REMOTIX B2 — a QUIC variable-length integer (RFC 9000 §16).  It is needed three times
//    and is in neither of the two libraries: nghttp3 keeps its own for
//    itself.  Sixteen lines that are already glue.
size_t wt_scrivi_varint(uint8_t *dest, uint64_t v) {
  if (v < 64) {
    dest[0] = static_cast<uint8_t>(v);
    return 1;
  }
  if (v < 16384) {
    dest[0] = static_cast<uint8_t>(0x40 | (v >> 8));
    dest[1] = static_cast<uint8_t>(v & 0xff);
    return 2;
  }
  if (v < 1073741824) {
    dest[0] = static_cast<uint8_t>(0x80 | (v >> 24));
    dest[1] = static_cast<uint8_t>((v >> 16) & 0xff);
    dest[2] = static_cast<uint8_t>((v >> 8) & 0xff);
    dest[3] = static_cast<uint8_t>(v & 0xff);
    return 4;
  }
  dest[0] = static_cast<uint8_t>(0xc0 | (v >> 56));
  for (size_t i = 1; i < 8; ++i) {
    dest[i] = static_cast<uint8_t>((v >> (8 * (7 - i))) & 0xff);
  }
  return 8;
}

// Returns 0 if the bytes are not enough: "I do not know yet" and "zero" are two
// different things, and confusing them is `LEZIONI.md` §1.9.
size_t wt_leggi_varint(uint64_t *v, const uint8_t *src, size_t len) {
  if (len == 0) {
    return 0;
  }
  size_t n = static_cast<size_t>(1) << (src[0] >> 6);
  if (len < n) {
    return 0;
  }
  *v = src[0] & 0x3f;
  for (size_t i = 1; i < n; ++i) {
    *v = (*v << 8) | src[i];
  }
  return n;
}

// ⛔ The two numbers with which a server declares WebTransport, and they are TWO because
//    there are two drafts in circulation:
//
//      0x2b603742  SETTINGS_ENABLE_WEBTRANSPORT   draft 02
//      0xc671706a  SETTINGS_WT_MAX_SESSIONS       draft 07 and later
//
// ⚠ And the difference is not academic: `aioquic` 1.2 — our test
//   client — implements **02** [R] `h3/connection.py:90`, while today's browsers
//   look for **07**.  A server that sent only one of them
//   would work with half of our tools and not with the other half, and
//   the half that works would be the wrong one to draw conclusions from.
//   Both are sent: an unknown setting is ignored.
constexpr uint64_t WT_ENABLE_WEBTRANSPORT = 0x2b603742ULL;
constexpr uint64_t WT_MAX_SESSIONS = 0xc671706aULL;

// ⛔⭐ THE CAP OF A CAPSULE, AND IT IS CHECKED BEFORE KEEPING THE BYTES.
//
// `RCP.md` §6.1: "a receiver that allocates `lunghezza` bytes and then checks has
// already given away a megabyte to anyone who can write six bytes".  ⚠ Here nothing
// was allocated: it **waited** — which is the same gift given more
// slowly, and without even a cap.
//
// ⭐ The number is what the only capsule that concerns us needs:
// `CLOSE_WEBTRANSPORT_SESSION` carries a 32-bit code and a reason that
// WebTransport limits to **1024 bytes**.  Plus the two variable-length integers at the head,
// which are at most eight each.
constexpr uint64_t WT_CAPSULA_MAX = 1024 + 4;

nghttp3_ssize wt_niente_dati(nghttp3_conn *conn, int64_t stream_id,
                             nghttp3_vec *vec, size_t veccnt, uint32_t *pflags,
                             void *user_data, void *stream_user_data) {
  (void)conn;
  (void)stream_id;
  (void)vec;
  (void)veccnt;
  (void)pflags;
  (void)user_data;
  (void)stream_user_data;
  // ⛔ The stream of the extended CONNECT does NOT close: it IS the session.  A
  //    reader that said "I am done" would put the FIN on it, and the
  //    session would die the instant it opens.
  return NGHTTP3_ERR_WOULDBLOCK;
}
} // namespace

size_t ProtoCodec::wt_riscrivi_impostazioni(const nghttp3_vec *vec,
                                            size_t veccnt) {
  // What nghttp3 wants to write: the type of the control stream (0x00)
  // followed by the SETTINGS frame.
  std::vector<uint8_t> orig;
  for (size_t i = 0; i < veccnt; ++i) {
    orig.insert(orig.end(), vec[i].base, vec[i].base + vec[i].len);
  }
  if (orig.size() < 3) {
    return 0;
  }

  uint64_t tipo_stream = 0;
  auto n = wt_leggi_varint(&tipo_stream, orig.data(), orig.size());
  if (n == 0 || tipo_stream != 0x00) {
    std::println(stderr,
                 "REMOTIX B2: the control stream does not start with 0x00 "
                 "(it is {}): touching nothing",
                 tipo_stream);
    return 0;
  }
  auto p = n;

  uint64_t tipo_frame = 0;
  n = wt_leggi_varint(&tipo_frame, orig.data() + p, orig.size() - p);
  if (n == 0 || tipo_frame != 0x04) {
    std::println(stderr, "REMOTIX B2: the first frame is not SETTINGS (it is {})",
                 tipo_frame);
    return 0;
  }
  p += n;

  uint64_t lung = 0;
  n = wt_leggi_varint(&lung, orig.data() + p, orig.size() - p);
  if (n == 0) {
    return 0;
  }
  p += n;

  if (p + lung != orig.size()) {
    // ⛔ There is something else after SETTINGS, or SETTINGS arrived in pieces.  It is not
    //    rewritten blindly: we say so, and leave it alone.  The server
    //    will stay without WebTransport, and the measurement will see it at once.
    std::println(stderr,
                 "REMOTIX B2: SETTINGS is not all here ({} + {} != {})", p,
                 lung, orig.size());
    return 0;
  }

  std::array<uint8_t, 64> aggiunta;
  size_t a = 0;
  a += wt_scrivi_varint(aggiunta.data() + a, WT_ENABLE_WEBTRANSPORT);
  a += wt_scrivi_varint(aggiunta.data() + a, 1);
  a += wt_scrivi_varint(aggiunta.data() + a, WT_MAX_SESSIONS);
  a += wt_scrivi_varint(aggiunta.data() + a, 1);

  std::array<uint8_t, 16> testa;
  size_t t = 0;
  t += wt_scrivi_varint(testa.data() + t, 0x00); // type of the stream
  t += wt_scrivi_varint(testa.data() + t, 0x04); // SETTINGS
  t += wt_scrivi_varint(testa.data() + t, lung + a);

  if (t + lung + a > wt_impbuf_.size()) {
    std::println(stderr, "REMOTIX B2: SETTINGS too big for the buffer");
    return 0;
  }

  size_t o = 0;
  for (size_t i = 0; i < t; ++i) {
    wt_impbuf_[o++] = testa[i];
  }
  for (size_t i = 0; i < lung; ++i) {
    wt_impbuf_[o++] = orig[p + i];
  }
  for (size_t i = 0; i < a; ++i) {
    wt_impbuf_[o++] = aggiunta[i];
  }
  wt_impbuf_len_ = o;

  std::println(stderr,
               "REMOTIX B2: SETTINGS rewritten — {} bytes from nghttp3 + {} "
               "of ours (ENABLE_WEBTRANSPORT and WT_MAX_SESSIONS)",
               orig.size(), a);

  return orig.size();
}

// ⛔⭐ THE CAPSULES OF THE CONNECT, AND THE ONLY ONE THAT CONCERNS US.
//
// The body of an extended CONNECT is a flow of capsules (RFC 9297): varint
// type, varint length, body.  Of all of them, only **one** is looked at here:
// `CLOSE_WEBTRANSPORT_SESSION` (0x2843), which carries a 32-bit code and a
// reason in UTF-8 — and it is the SECOND ROAD of `RCP.md` §3.1 point 3, the one
// by which the reason arrives even when the bytes of the channel do not leave.
//
// ⚠ It accumulates, because a capsule can arrive in pieces; and the
//   rest is discarded without noise, because a flow of unknown capsules is not an
//   error (RFC 9297 §3.2 says to ignore them).
void ProtoCodec::wt_capsula(int64_t stream_id, std::span<const uint8_t> dati) {
  if (stream_id != wt_sessione_ || dati.empty()) {
    return;
  }
  // ⛔ The bytes of a capsule already judged too big are thrown away AS THEY
  //    PASS, without keeping them: it is the only way not to let the memory be
  //    filled by whoever can write two variable-length integers.
  if (wt_capsalta_ > 0) {
    uint64_t n = wt_capsalta_ < dati.size()
                   ? wt_capsalta_
                   : static_cast<uint64_t>(dati.size());
    wt_capsalta_ -= n;
    dati = dati.subspan(static_cast<size_t>(n));
    if (dati.empty()) {
      return;
    }
  }
  wt_capsbuf_.insert(wt_capsbuf_.end(), dati.begin(), dati.end());
  for (;;) {
    uint64_t tipo = 0, lung = 0;
    // ⚠ Here the buffer cannot grow without end: a variable-length integer is at
    //   most 8 bytes, so with 8 bytes the type can always be read and with 16
    //   the length can always be read too.
    auto a = wt_leggi_varint(&tipo, wt_capsbuf_.data(), wt_capsbuf_.size());
    if (a == 0) {
      return;
    }
    auto b = wt_leggi_varint(&lung, wt_capsbuf_.data() + a,
                             wt_capsbuf_.size() - a);
    if (b == 0) {
      return;
    }
    // ⛔⭐ AND THE LENGTH IS CHECKED HERE, BEFORE WAITING FOR THE BYTES.
    //
    //    The input this closes: the page sends, on the CONNECT
    //    stream, an unknown capsule type and a length of 2^62-1;
    //    then it sends data, forever.  No capsule was ever completed,
    //    so `erase` was never called, `wt_capsbuf_` grew by
    //    every byte that arrived — and `http_consume` kept widening the
    //    credit, so the client could send without end.  ⛔ On a
    //    connection that has not yet passed the RCP handshake.
    //
    // ⚠ And the non-hostile variant is just as true: a legitimate
    //   but unknown capsule of half a gigabyte was buffered ENTIRELY only to
    //   be discarded.  RFC 9297 §3.2 allows skipping it without keeping it, and
    //   that is what is done now.
    if (lung > WT_CAPSULA_MAX) {
      std::println(stderr,
                   "REMOTIX B2: capsule {:#x} {} bytes long, beyond the cap of "
                   "{}: SKIPPED without keeping it (RFC 9297 §3.2; RCP.md §6.1, the "
                   "length is checked before allocating)",
                   tipo, lung, WT_CAPSULA_MAX);
      uint64_t qui = wt_capsbuf_.size() - a - b;
      uint64_t presi = qui < lung ? qui : lung;
      wt_capsalta_ = lung - presi;
      wt_capsbuf_.erase(wt_capsbuf_.begin(),
                        wt_capsbuf_.begin() +
                          static_cast<long>(a + b + static_cast<size_t>(presi)));
      if (wt_capsalta_ > 0) {
        return;
      }
      continue;
    }
    if (wt_capsbuf_.size() < a + b + lung) {
      return; // it is below the cap: we can wait for all of it to arrive
    }
    const uint8_t *corpo = wt_capsbuf_.data() + a + b;
    if (tipo == 0x2843 && lung >= 4) {
      uint32_t codice = (static_cast<uint32_t>(corpo[0]) << 24) |
                        (static_cast<uint32_t>(corpo[1]) << 16) |
                        (static_cast<uint32_t>(corpo[2]) << 8) |
                        static_cast<uint32_t>(corpo[3]);
      std::string ragione{corpo + 4, corpo + lung};
      std::println(stderr,
                   "REMOTIX B2: the page CLOSED the WebTransport session: "
                   "code {:#x} «{}»",
                   codice, ragione);
      // ⛔ The code is delivered WHOLE.  Truncating it to the low byte made
      //    `0x0100` enter the record as `0x00`, that is as the only value
      //    RCP.md §3.1 forbids — and the two logs of the same closing
      //    contradicted each other two lines apart.
      wt_chiusa_dal_client(codice);
    }
    wt_capsbuf_.erase(wt_capsbuf_.begin(),
                      wt_capsbuf_.begin() + static_cast<long>(a + b + lung));
  }
}

// ⚠ Empty on purpose: what the client's closing and the end of the channel
//   MEAN the WebTransport layer does not know — the protocol knows, and RCP
//   arrives with B3.
void ProtoCodec::wt_chiusa_dal_client(uint32_t codice) { (void)codice; }

void ProtoCodec::wt_fin_dal_client(int64_t stream_id) { (void)stream_id; }

void ProtoCodec::wt_accoda(int64_t stream_id, std::span<const uint8_t> dati) {
  wt_uscita_.push_back(
    WtUscita{stream_id, std::vector<uint8_t>{dati.begin(), dati.end()}, 0});
}

ProtoCodec::WtEsito ProtoCodec::wt_smista(int64_t stream_id,
                                          std::span<const uint8_t> data,
                                          bool fin,
                                          std::vector<uint8_t> &riunito) {
  // Only the bidirectional streams opened by the client: the extended CONNECT and the
  // WebTransport streams all arrive from there.
  if ((stream_id & 0x03) != 0x00) {
    return WtEsito::HTTP3;
  }

  if (wt_nonwt_.contains(stream_id)) {
    return WtEsito::HTTP3;
  }

  if (wt_streams_.contains(stream_id)) {
    // ⭐ A WebTransport stream already recognised: the payload goes back
    //    on the same stream.  It is the "byte that comes back" of B2 — and
    //    "the session opens" without "the bytes come back" is the kind of green
    //    this bench exists not to produce.
    if (!data.empty()) {
      wt_accoda(stream_id, data);
      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());
      ngtcp2_conn_extend_max_offset(conn_, data.size());
    }
    // ⛔ AND THE FIN IS LOOKED AT AFTER THE BYTES, not before: the last bytes
    //    arrived **together** with it and must be delivered while the session is
    //    still alive, or whoever receives them would read them as bytes sent after the
    //    end — that is as a client violation that did not happen.
    if (fin) {
      wt_fin_dal_client(stream_id);
    }
    return WtEsito::MIO;
  }

  auto &pref = wt_incerti_[stream_id];
  pref.insert(pref.end(), data.begin(), data.end());
  if (pref.size() < 2) {
    // ⚠ And the window is NOT widened: nobody has taken those bytes
    //    yet, and counting them now and then again would falsify the credit.
    return WtEsito::ATTENDI;
  }

  // ⛔ The WEBTRANSPORT_STREAM frame type is 0x41 — but a variable-length integer
  //    does not write it in one byte: 0x41 is 65, and one byte holds 63.
  //    On the wire they are TWO bytes, 0x40 0x41, and that is why two are enough to
  //    decide.  A HEADERS frame starts with 0x01, a DATA one with 0x00.
  if (pref[0] == 0x40 && pref[1] == 0x41) {
    uint64_t sessione = 0;
    auto n = wt_leggi_varint(&sessione, pref.data() + 2, pref.size() - 2);
    if (n == 0) {
      return WtEsito::ATTENDI;
    }
    auto consumati = pref.size();
    std::vector<uint8_t> resto{pref.begin() + 2 + static_cast<long>(n),
                               pref.end()};
    wt_streams_[stream_id] = static_cast<int64_t>(sessione);
    wt_incerti_.erase(stream_id);
    std::println(stderr, "REMOTIX B2: stream {} is WebTransport, session {}",
                 stream_id, sessione);
    if (!resto.empty()) {
      wt_accoda(stream_id, resto);
    }
    ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, consumati);
    ngtcp2_conn_extend_max_offset(conn_, consumati);
    // ⛔ Here too: the stream can be recognised and finished in the same
    //    packet (RCP.md §4.2, the FIN from either side).
    if (fin) {
      wt_fin_dal_client(stream_id);
    }
    return WtEsito::MIO;
  }

  riunito = pref;
  wt_incerti_.erase(stream_id);
  wt_nonwt_[stream_id] = true;
  return WtEsito::HTTP3;
}

std::expected<void, Error> ProtoCodec::wt_apri_sessione(Stream *stream) {
  // ⛔ RCP.md §2.2: the server MUST NOT accept a WebTransport session on
  //    a different path, and the refusal is **404** (finding R1.24, which
  //    chose one of the three statuses that were all legitimate).  And it is written in the
  //    log: it is §3 applied to the first byte.
  if (stream->uri != "/rcp/1") {
    std::println(stderr,
                 "REMOTIX B2: ⛔ WebTransport session REFUSED, path {}",
                 stream->uri);
    return send_status_response(stream, 404);
  }

  auto nva = std::to_array({
    util::make_nv_nn(":status"sv, "200"sv),
    util::make_nv_nn("server"sv, NGTCP2_SERVER),
  });

  nghttp3_data_reader dr{
    .read_data = wt_niente_dati,
  };

  if (auto rv = nghttp3_conn_submit_response(httpconn_, stream->stream_id,
                                             nva.data(), nva.size(), &dr);
      rv != 0) {
    std::println(stderr, "nghttp3_conn_submit_response: {}",
                 nghttp3_strerror(rv));
    return std::unexpected{Error::HTTP3};
  }

  wt_sessione_ = stream->stream_id;
  stream->wt_session = true;
  std::println(stderr,
               "REMOTIX B2: ⭐ WebTransport session OPEN on {} (stream {})",
               stream->uri, stream->stream_id);

  return {};
}

'''


def leggi(percorso):
    with open(percorso, encoding="utf-8") as f:
        return f.read()


def scrivi(percorso, testo):
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(testo)


def righe_di_commento(righe):
    """⛔ A SINGLE RULE FOR COMMENTS, AND THE SAME IN THE THREE GRAFTS.

    On 10 Aug 2026 the three scripts had three different ones for the same
    quantity — `//` here, `//`+`/*`+`*` in B3, `*`+`/*` in the quiche one —
    and the second classified as a COMMENT two lines of real C++ that are
    in the body grafted by this file:

        *v = src[0] & 0x3f;
        *v = (*v << 8) | src[i];

    ⚠ They are dereferences, and they start with `*`.  Here the asterisk counts as
      a comment only when it is the continuation of a `/* … */` block, that is
      when it is followed by a space or when it closes the block.
    """
    return sum(1 for r in righe
               if r.strip().startswith(("//", "/*", "* ", "*/"))
               or r.strip() == "*")


def togli():
    # ⛔ AND WE SAY WHAT WE TAKE AWAY.
    #
    #    `git checkout -- examples` puts back the WHOLE folder: if on top
    #    there is the B3 graft, or the B11 faults, or a test done by hand,
    #    those disappear too.  The message before said only "the example
    #    is put back as it was", that is less than what the command does.
    print("== Putting the example back as it was")
    prima = ""
    for f in FILE_TOCCATI:
        try:
            prima += leggi(f"{ESEMPI}/{f}")
        except FileNotFoundError:
            pass
    for marca, chi in ((MARCA_B3, "the B3 graft"),
                       (MARCA_B11, "the B11 faults")):
        if marca in prima:
            print(f"   ⚠ {chi} is there too: it disappears together with this one.")
    r = subprocess.run(["git", "-C", ALBERO, "checkout", "--", "examples"])
    if r.returncode != 0:
        print(f"   ⛔ git checkout failed (exit {r.returncode}):"
              " nothing was removed.")
        return r.returncode

    # ⛔ AND WE VERIFY THAT WE REMOVED.
    #
    #    The exit status of git says git did not complain, not that the
    #    mark is gone: it is the fourth rule of `LEZIONI.md` §1.9 — "zero" and
    #    "I failed" must not have the same face.  The only reading that
    #    counts is rereading the files.  `01-b11-guasto.sh` already does this check
    #    for its own mark; here it was missing.
    resta = 0
    for f in FILE_TOCCATI:
        try:
            n = leggi(f"{ESEMPI}/{f}").count(MARCA)
        except FileNotFoundError:
            n = 0
        if n:
            print(f"   NO  {n} lines with «{MARCA}» remain in {f}")
            resta += n
    if resta:
        print(f"   ⛔ {resta} traces of «{MARCA}» survive:"
              " the example is NOT as it was.")
        return 3
    print(f"   OK  no trace of «{MARCA}» in the {len(FILE_TOCCATI)}"
          " files touched")

    # ⚠ And git does not touch UNTRACKED files: if B3 has been here, its
    #   three files stay orphaned inside an example "as it was".
    orfani = [f for f in FILE_DI_B3 if os.path.exists(f"{ESEMPI}/{f}")]
    if orfani:
        print(f"   ⚠ the B3 files remain in examples/: {', '.join(orfani)}")
        print("     git checkout does not touch untracked files;"
              " 01-b3-rcp-innesta.py --togli takes them away")
    return 0


def main():
    if "--togli" in sys.argv:
        return togli()

    lista = innesti()
    # Piece 12 is the body, which is in a separate constant for readability.
    lista = [
        (f, a, (CORPO + a) if s is None else s, n) for (f, a, s, n) in lista
    ]

    print("== Grafting the WebTransport layer into the ngtcp2 example")
    print(f"   tree: {ESEMPI}")
    print(f"   {len(lista)} grafts to apply\n")

    # Already done?
    if MARCA in leggi(f"{ESEMPI}/http3_server_proto_codec.cc"):
        print("   ⚠ the graft is already there: touching nothing.")
        print("     to redo it from scratch: --togli, then this command again")
        return 0

    # ⛔ THE DENOMINATOR OF THE LINE COUNT, READ BEFORE TOUCHING ANYTHING.
    #
    #    `git diff -- examples` measures everything that changed in that
    #    folder, by anyone: it is OUR count only if there was
    #    nothing else before.  We look now, not afterwards, because after our
    #    change it is in there and can no longer be told apart.
    #    ⚠ Untracked files (`??`) do not enter the diff, so they do not
    #      dirty the count: they are ignored here.
    sporchi = [
        r for r in subprocess.run(
            ["git", "-C", ALBERO, "status", "--porcelain", "--", "examples"],
            capture_output=True, text=True).stdout.splitlines()
        if not r.startswith("??")
    ]

    testi = {}
    guasti = 0
    for percorso, appiglio, sostituto, nome in lista:
        if percorso not in testi:
            testi[percorso] = leggi(f"{ESEMPI}/{percorso}")
        # ⛔ THE CHECK THAT MAKES ALL THE REST HONEST: the foothold must
        #    appear ONCE ONLY.  Zero means their example has
        #    changed under us; two, that we are grafting blindly.
        n = testi[percorso].count(appiglio)
        stato = "OK " if n == 1 else "NO "
        print(f"   {stato} {nome:38s} foothold found {n} time(s)  [{percorso}]")
        if n != 1:
            guasti += 1
            continue
        testi[percorso] = testi[percorso].replace(appiglio, sostituto, 1)

    if guasti:
        print(f"\n   ⛔ {guasti} footholds of {len(lista)} are not ONE: writing nothing.")
        print("      The ngtcp2 example has changed: the grafts must be reread.")
        return 2

    for percorso, testo in testi.items():
        scrivi(f"{ESEMPI}/{percorso}", testo)
    print(f"\n   OK  {len(lista)} grafts of {len(lista)}, in {len(testi)} files")

    # ⭐ The line count, which is the datum of §6.4 and not an estimate.
    #
    # ⚠ The count is done HERE, in Python, and not with a shell pipeline: the
    #   first attempt of 10 Aug passed `grep -c` through three nested
    #   shells, the quotes broke, and it printed "0 comments, 0
    #   blank lines" on a file that has 85 and 42.  Another false zero.
    print("\n== How many lines changed under examples/ — the datum of §6.4")
    subprocess.run(
        ["git", "-C", ALBERO, "diff", "--stat", "--", "examples"],
    )
    d = subprocess.run(
        ["git", "-C", ALBERO, "diff", "-U0", "--", "examples"],
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    agg = [r[1:] for r in d if r.startswith("+") and not r.startswith("+++")]
    vuote = sum(1 for r in agg if not r.strip())
    comm = righe_di_commento(agg)
    print(f"\n   added lines    : {len(agg)}")
    print(f"     blank        : {vuote}")
    print(f"     comment      : {comm}")
    print(f"     ⭐ CODE       : {len(agg) - vuote - comm}")

    # ⛔ AND THE DENOMINATOR IS PRINTED NEXT TO THE NUMBER, not implied.
    if sporchi:
        print("\n   ⛔ AND THIS COUNT CANNOT BE ATTRIBUTED TO US: before")
        print("      the graft these files were already modified —")
        for r in sporchi:
            print(f"        {r}")
        print("      git diff does not know whose a line is: it measures the folder.")
    else:
        print("\n   ⭐ and the tree was CLEAN before the graft (git status)")
        print("      — which is the only thing that makes \"changed\" = \"ours\".")
    print("\n   ⚠ \"added\" remains an upper bound: a MODIFIED line")
    print("     (for example SSL_set_early_data_enabled to 0) shows up among the")
    print("     additions, and its old line among the removed ones.")
    print("\n   ⚠ It is the WebTransport layer, NOT a server: underneath there is their")
    print("     complete HTTP/3.  The number answers \"how much glue is left to")
    print("     us\", which is the question of §6.4 — not \"how much the server weighs\".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
