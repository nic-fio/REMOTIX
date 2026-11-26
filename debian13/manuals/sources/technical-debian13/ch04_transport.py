from build import arrow, box, c, fig, flow, note, p, rif, seq, steps, table, text, tip, ui, ul, warn, zone

# ── The stack at a glance ───────────────────────────────────────────────
STACK = fig(
    zone(20, 40, 560, 330, "UDP 7447 — the session")
    + box(40, 70, 520, 46, "rcp.c — RCP/1", "handshake, video header, input, clipboard, farewell", "navy")
    + arrow(300, 118, 300, 134)
    + box(40, 136, 520, 46, "webtransport.c — the WebTransport layer", "SETTINGS, CONNECT, stream preambles, capsules, send queue", "blue")
    + arrow(300, 184, 300, 200)
    + box(40, 202, 250, 46, "nghttp3", "HTTP/3, QPACK, extended CONNECT", "light")
    + box(310, 202, 250, 46, "datagrams", "RFC 9297, audio only", "light")
    + arrow(165, 250, 165, 266) + arrow(435, 250, 435, 266)
    + box(40, 268, 520, 46, "transport.c + ngtcp2 — QUIC v1", "one socket, Retry, connection ids, admission control, timers", "dark")
    + box(40, 318, 520, 38, "ngtcp2_crypto_ossl + OpenSSL — TLS 1.3, ALPN h3", "", "grey", 12)
    + zone(600, 40, 280, 330, "TCP 7447 — the page")
    + box(620, 70, 240, 46, "page.c", "HTTP/1.1, one request per connection", "blue")
    + arrow(740, 118, 740, 134)
    + box(620, 136, 240, 64, "routes", "/ · /index.html · /fingerprint", "light")
    + arrow(740, 202, 740, 218)
    + box(620, 220, 240, 46, "certificates.c", "long-lived + short-lived certificate", "navy")
    + box(620, 318, 240, 38, "OpenSSL — TLS 1.3, ALPN http/1.1", "", "grey", 12)
    + text(740, 300, "tls.c builds one SSL_CTX per listener", 11, "#334155"),
    900, 380, "«FIG» — The two listeners of the network side and the layers of each")

FILES = table(["File", "What it does"], [
    [c("src/transport.c"), "The UDP socket, the map of connection ids, one " + c("ngtcp2_conn") + " per client, the QUIC "
     "transport parameters, Version Negotiation, Retry, Stateless Reset, the caps and rates that admit new connections. It "
     "passes stream data, datagrams and timer expiries to the WebTransport layer."],
    [c("src/cid.c") + ", " + c("src/cid.h"), "Connection ids that carry their own proof: " + c("CID_NONCE") + " random bytes plus "
     + c("CID_TAG") + " bytes of HMAC-SHA256."],
    [c("src/pktinfo.h"), "The source address of a reply: the datagram is sent from the address the client wrote to."],
    [c("src/hsrate.h") + ", " + c("src/resetcap.h") + ", " + c("src/linebudget.h"), "Header-only helpers with no dependency: "
     "the handshake rate buckets, the per-address cap on Stateless Resets, the budgets of log lines."],
    [c("src/webtransport.c") + ", " + c("src/webtransport.h"), "The layer that neither ngtcp2 nor nghttp3 provides: announcing "
     "WebTransport, accepting the extended CONNECT on " + c("/rcp/1") + ", classifying client streams by their preamble, the "
     "send queue, the audio datagrams, the closing capsule, the keep-alive PINGs and the dead-line detector. It is also the "
     "host of " + c("rcp.c") + " (the " + c("rcp_hooks") + " hooks)."],
    [c("src/rcp.c"), "The protocol itself (" + rif("The RCP/1 protocol") + "). It knows nothing about QUIC: it receives bytes, "
     "returns bytes and asks its host to send them."],
    [c("src/tls.c"), "Two " + c("SSL_CTX") + ": the QUIC one (ALPN " + c("h3") + ", 0-RTT off) and the TCP one (ALPN "
     + c("http/1.1") + ")."],
    [c("src/certificates.c"), "Generates, loads and rotates the two ECDSA P-256 certificates, and computes the SHA-256 "
     "fingerprint of the session certificate."],
    [c("src/page.c"), "The TCP listener: serves " + c("page.html") + " with the fingerprint written into it and the "
     + c("/fingerprint") + " endpoint, gzip-compressed when the browser accepts it, with its own deadlines, per-address caps "
     "and eviction."],
    [c("src/main.c"), "Owns the single " + c("poll") + " loop of the network side, reads the options, prepares the certificates, "
     "checks every 60 s whether the session certificate must rotate and shuts everything down with " + c("SERVER_CLOSING") + "."],
], "«TAB» — The files of the transport")

S1 = p("REMOTIX has no client program: the client is the browser. A web page cannot open a bare QUIC connection, but "
       "WebTransport over HTTP/3 gives it the building blocks the protocol needs: independent unidirectional streams, the "
       "abandonment of a stream with " + c("RESET_STREAM") + ", unreliable datagrams and connection migration. The server "
       "therefore speaks QUIC version 1 with mandatory TLS 1.3, HTTP/3 and WebTransport on UDP, and serves the page itself on "
       "TCP. There is no clear-text mode, and RCP never runs on TCP.", lead=True) + STACK + FILES + \
    p("Both listeners belong to the <i>network side</i>, the unprivileged process that the root side forks (see " +
      rif("Overall architecture") + " and " + rif("Startup and life cycle") + "). The root side binds the two sockets before "
      "the fork and hands them over as descriptors 4 (UDP) and 5 (TCP) (" + c("ROOTSIDE_FD_UDP") + ", " + c("ROOTSIDE_FD_TCP") +
      "); the network side then calls " + c("transport_open_fd()") + " and " + c("page_open_fd()") + " on them. In the "
      "single-process mode (" + c("--no-split") + ") " + c("transport_open()") + " and " + c("page_open()") + " bind and open in "
      "one step. Either way QUIC, HTTP/3, WebTransport, RCP and the page server share one thread and one " + c("poll") + " loop. "
      "Whatever could block that loop lives in other processes: PAM in the helper (" + c("helper.c") + ") and everything that "
      "touches a user's desktop in the per-user child. The transport only moves bytes between the network and those processes.") + \
    note("the QUIC and HTTP/3 libraries are linked statically. " + c("build/quic-static.sh") + " builds ngtcp2 " + c("v1.25.0") +
         " and nghttp3 " + c("v1.18.0") + " from source (the " + c("NGTCP2_VER") + " and " + c("NGHTTP3_VER") + " defaults) and "
         + c("debian/control") + " records them in " + c("Static-Built-Using") + ". OpenSSL is the system library ("
         "libssl-dev 3.5 or later at build time) used through " + c("ngtcp2_crypto_ossl") + ", which carries the native QUIC API "
         "of OpenSSL 3.5. The reasons for choosing ngtcp2 over the other QUIC libraries are in DECISIONS.md §6.4.",
         "Libraries.")

# ── The SETTINGS rewrite ────────────────────────────────────────────────
S2 = p("No QUIC library considered for REMOTIX implements WebTransport on the server side, so " + c("webtransport.c") + " adds "
       "it on top of ngtcp2 and nghttp3. The price is declared in " + c("webtransport.h") + ": nghttp3 has no API to put an "
       "arbitrary setting on the HTTP/3 control stream, so the server rewrites the " + c("SETTINGS") + " frame while nghttp3 is "
       "writing it, in " + c("rewrite_settings()") + ".", lead=True) + \
    p("The rewrite depends on the shape of the bytes nghttp3 produces, not on a promise of its API, and must be re-tested at "
      "every nghttp3 upgrade. The guard is loud. " + c("rewrite_settings()") + " first checks that the bytes handed over fit its "
      "512-byte buffer, that the control stream starts with stream type " + c("0x00") + ", that the first frame is " +
      c("SETTINGS") + " (type " + c("0x04") + ") and that its length covers exactly those bytes. If any check fails nothing is "
      "rewritten, the log says which one, and the server has no WebTransport; it never emits a misaligned control stream.") + \
    note("the benches that compared the QUIC libraries and measured the WebTransport handshake against real browsers are not "
         "part of this tree. This manual repeats their result from code comments, not from a re-run. What was verified for "
         "1.0.0 is in " + rif("What was verified for the transport") + ".", "Provenance.")

# ── Two listeners ───────────────────────────────────────────────────────
S3 = p("The server listens on port 7447 twice: UDP for HTTP/3 and WebTransport, TCP for the first load of the page. The user "
       "types " + c("https://address:7447") + ", accepts the certificate warning once per device, and types user and password "
       "into the page.", lead=True) + \
    table(["", "UDP 7447", "TCP 7447"], [
        ["Carries", "QUIC v1, HTTP/3, the WebTransport session " + c("/rcp/1"), "HTTPS (HTTP/1.1): the page and " + c("/fingerprint")],
        ["Certificate", "the short-lived session certificate", "the long-lived page certificate"],
        ["ALPN", c("h3") + ", required: a client that does not offer it is refused", c("http/1.1") + ", optional: a client that sends none is served"],
        [c("SO_REUSEADDR"), "never set", "set"],
        ["Bound by", c("transport_bind()"), c("page_bind()") + ", backlog " + c("PAGE_BACKLOG") + " = 256"],
        ["Code", c("transport.c") + ", " + c("webtransport.c"), c("page.c")],
    ], "«TAB» — The two listeners") + \
    p("The two are independent. WebTransport does not use " + c("Alt-Svc") + ": a WebTransport session opens its own HTTP/3 "
      "connection to the address it is given, so there is no fallback from UDP to TCP to make. RCP.md §2.4 carries a note "
      "that corrects the earlier requirement of an " + c("Alt-Svc") + " header.") + \
    warn("the UDP socket is bound without " + c("SO_REUSEADDR") + ". With that option two unicast UDP sockets can share the port "
         "and the kernel hands each packet to only one of them, which looks like «the server is on and the page does not "
         "connect» with two processes both convinced they are listening. On TCP the option stays: there the kernel refuses a "
         "second listener anyway, and the option only avoids " + c("TIME_WAIT") + " after a restart.",
         "No SO_REUSEADDR on UDP.") + \
    p("<b>Address and port in the package.</b> " + c("debian/remotix.service") + " starts the binary with " +
      c("--address 0.0.0.0") + ", " + c("--name %H") + " and " + c("--port") + " taken from " + c("REMOTIX_PORT") + ". The "
      "binary's own default for " + c("--address") + " is also " + c("0.0.0.0") + ", an IPv4 wildcard, so the packaged server "
      "does not listen on IPv6. The code supports IPv6 sockets (" + c("transport_bind()") + " resolves with " + c("AF_UNSPEC") +
      " and " + c("pktinfo.h") + " handles " + c("IPV6_PKTINFO") + "), but nothing in the package asks for them and no check in "
      + c("prove/") + " exercised IPv6. The port is " + c("REMOTIX_PORT") + ", " + c("7447") + " in " + c("remotix.conf") +
      " (installed as " + c("/usr/share/remotix/remotix.conf") + "), overridable by files in " +
      c("/etc/remotix/remotix.conf.d/") + ". Extra options go in " + c("REMOTIX_OPTIONS") + ". The compiled-in default is " +
      c("DEFAULT_PORT") + " in " + c("main.c") + ".") + \
    warn("both protocols of the port must be reachable: TCP loads the page and UDP carries the session. With only TCP open the "
         "page loads and the desktop never arrives, because there is no fallback. The package ships a ufw application profile "
         "(" + c("debian/remotix.ufw") + ", installed as " + c("/etc/ufw/applications.d/remotix") + ", 7447/tcp and 7447/udp) "
         "but only defines it. Nothing opens the firewall and this tree has no installer to do it, so the administrator must "
         "run " + c("ufw allow REMOTIX") + " or the equivalent for another firewall; a comment in " + c("debian/rules") +
         " that says an engine does it is stale. A firewall outside the machine (a provider's) needs the same two rules.",
         "TCP and UDP, and nobody opens them.")

# ── QUIC parameters ─────────────────────────────────────────────────────
S4 = p("Every connection gets the same transport parameters, set in " + c("accept_conn()") + " just before " +
       c("ngtcp2_conn_server_new") + ". With a browser as client the server cannot dictate the client's parameters: what is "
       "normative is what the server announces.", lead=True) + \
    table(["Parameter", "Value", "Why"], [
        [c("max_idle_timeout"), "30 s (" + c("IDLE_MS") + ")", "RCP.md §2.2. It is negotiated (the minimum of the two sides "
         "wins, RFC 9000 §10.1), so lowering it would also make the browser drop the server after the server's own silences. "
         "The owner's 10 s rule lives in the dead-line detector instead (" + rif("Idle timeout, keep-alive PINGs and the dead line") + ")."],
        [c("initial_max_streams_uni"), "19", "RCP.md §2.3 requires at least 16 unidirectional streams available to RCP at any "
         "moment. HTTP/3 takes three (control and two QPACK) for the whole connection, so 19 = 16 + 3. The credit is renewed by "
         + c("cb_stream_close()") + ", which calls " + c("ngtcp2_conn_extend_max_streams_uni") + " for every closed client stream."],
        [c("initial_max_streams_bidi"), "100", "One bidirectional stream is legal for RCP (the control channel), plus HTTP/3 request streams."],
        [c("initial_max_stream_data_*"), "256 KiB", "Per-stream flow-control window, bidirectional (both) and unidirectional."],
        [c("initial_max_data"), "1 MiB", "Connection-level window."],
        [c("max_datagram_frame_size"), "65 536", "Datagrams must be enabled (audio). Without this parameter announcing "
         + c("SETTINGS_H3_DATAGRAM=1") + " is a protocol error."],
        [c("active_connection_id_limit"), "7", "Each id leads to the same connection through the id map."],
        [c("grease_quic_bit"), "1", "Standard greasing."],
        ["stateless reset token", "present", "Derived from the static secret and the connection id."],
        [c("original_dcid") + ", " + c("retry_scid"), "set", "Mandatory after a Retry (RFC 9000 §7.3): the destination id of the "
         "first Initial and the id the server chose in the Retry."],
        [c("disable_active_migration"), "not sent", "Migration is why QUIC was chosen: a phone that moves from Wi-Fi to mobile keeps "
         "its session. " + c("cb_path_validation()") + " logs how each path validation ends."],
        ["0-RTT", "refused", c("SSL_CTX_set_max_early_data(ctx, 0)") + " in " + c("tls_quic_context()") + ": 0-RTT data can be "
         "replayed and the second RCP message is " + c("CREDENTIALS") + "."],
        ["QUIC versions", "v1 only", c("nego_version()") + " answers any other version with a Version Negotiation packet listing "
         + c("NGTCP2_PROTO_VER_V1") + "."],
    ], "«TAB» — QUIC transport parameters announced by the server") + \
    ul([
        "No UDP GSO. " + c("write_connection()") + " asks ngtcp2 for an aggregate sized to ngtcp2's send quantum (never less than "
        "one full-size packet, never more than its 64 KiB buffer), splits it and sends one packet per " + c("sendmsg") + " through "
        + c("send_on()") + ". ngtcp2's pacing is honoured.",
        c("MAX_PACKETS_PER_ROUND") + " (64) limits <i>reading</i>: " + c("transport_read()") + " takes at most that many datagrams "
        "per pass of the loop, then " + c("transport_write()") + " runs.",
        "A datagram shorter than 21 bytes is dropped before ngtcp2 sees it (" + c("transport_read()") + ").",
        "The congestion controller was never chosen: " + c("ngtcp2_settings_default()") + " leaves " + c("cc_algo") +
        " at ngtcp2's default (CUBIC). The comment above " + c("wt_adaptive_rate()") + " records the choice of a controller as an experiment still to be made.",
    ])

# ── Admission, Retry, resets ────────────────────────────────────────────
S5 = p("A stranger gets no connection state. " + c("read_packet_1()") + " in " + c("transport.c") + " is the function to read; "
       "the figure shows the order in which a packet whose destination connection id is not in the map is treated.", lead=True) + \
    flow([("Packet", "no connection", "dark"), ("Short header", "Stateless Reset", "grey"),
          ("Initial, no token", "send_retry()", "blue"), ("Token verified", "10 s, address-bound", "blue"),
          ("Token seen before", "INVALID_TOKEN", "amber"), ("Handshake rate", "rate_ok(): 3 buckets", "navy"),
          ("Room", "room_for(): caps, eviction", "navy"), ("Connection", "accept_conn()", "green")],
         "«FIG» — What happens to the first packet of an unknown connection", width=900) + \
    table(["Step", "Function", "Rule"], [
        ["Version Negotiation", c("nego_version()"), "Any version but QUIC v1."],
        ["Retry", c("send_retry()"), "Every Initial without a token gets a Retry and no state. The token comes from " +
         c("ngtcp2_crypto_generate_retry_token2()") + ", is bound to the client address and is good for " + c("RETRY_TOKEN_TIMEOUT") +
         " = 10 s. The Retry's connection id has its own label (see below)."],
        ["Unreadable token", c("send_retry()"), "A token that is not ours or is damaged is ignored as if absent: the client gets a Retry."],
        ["Expired or foreign token", c("send_invalid_token()"), "A " + c("CONNECTION_CLOSE") + " with " + c("INVALID_TOKEN") + "."],
        ["Token used twice", c("token_used()") + ", " + c("token_keep()"), "A Retry token makes one connection. Used tokens are kept in "
         "a ring of " + c("TOKENS_KEPT") + " = 4096 (a keyed 64-bit hash each, until 10 s after use). A repeat gets " +
         c("INVALID_TOKEN") + ", not a second Retry: an honest client whose first connection was evicted fails at once and the page "
         "reconnects, instead of waiting out a handshake that a Retry would have stalled."],
        ["Handshake rate", c("rate_ok()"), "Three token buckets taken together (table below); a refusal is " + c("CONNECTION_REFUSED") +
         " and charges no bucket. The global bucket is charged only for a handshake that goes on, by " + c("hs_charge_all()") + "."],
        ["Room", c("room_for()") + ", " + c("pick_victim()"), "Caps on connections and on connections not yet logged in; when full, "
         "one not-yet-logged-in connection is evicted for the newcomer, after the newcomer's connection exists."],
    ], "«TAB» — The admission pipeline of a new connection") + \
    table(["Limit", "Value", "Constant or option"], [
        ["Handshakes per address (IPv4 or IPv6 /64)", "4 a second, burst 16", c("HS_ADDR_RATE") + ", " + c("HS_ADDR_BURST")],
        ["Handshakes per IPv6 /48", "16 a second, burst 32", c("HS_NET_RATE") + ", " + c("HS_NET_BURST")],
        ["Handshakes for everybody", "200 a second, burst 32", c("HS_ALL_RATE") + ", " + c("HS_ALL_BURST")],
        ["Connections at once", "256", c("MAX_CONNECTIONS") + ", " + c("--max-connections")],
        ["Connections not yet logged in", "128", c("MAX_PENDING") + ", " + c("--max-pending")],
        ["Not yet logged in, per address", "16", c("PENDING_PER_ADDRESS") + ", " + c("--max-pending-per-address")],
        ["Not yet logged in, per IPv6 /48", "64", c("PENDING_PER_48") + ", " + c("--max-pending-per-48")],
        ["Absolute age of a connection that has not logged in", "90 s", c("UNLOGGED_MAX_S") + ", checked in " + c("transport_expired()")],
        ["A connection is «parked» after", "5 s", c("PARKED_S") + ", used by " + c("pick_victim()")],
        ["Stateless Resets for signed ids", "100 a second in all", c("RESET_PER_SECOND")],
        ["Stateless Resets for unsigned ids", "10 a second in all", c("RESET_UNVERIFIED_PER_SECOND")],
        ["Stateless Resets to one address", "5 a second", c("RESET_PER_ADDRESS") + " in resetcap.h"],
        ["Stateless Resets for one signed id", "1 a second", "the " + c("reset_id") + " table in " + c("send_stateless_reset()")],
    ], "«TAB» — The numbers of the admission control") + \
    p("The «address» of every cap is computed by " + c("address_key()") + ": an IPv4-mapped IPv6 address and a NAT64 address become "
      "the IPv4 address inside, " + c("::1") + " is kept whole, any other IPv6 address becomes its /64, and the /48 is the second "
      "key. The login ban applies the same rule through " + c("rcp_key_address()") + " in " + c("rcp.c") + ". A connection is charged to "
      "its birth address even if it migrates (" + c("birth_key") + "). " + c("pick_victim()") + " never evicts a connection in " +
      c("wait-verdict") + " (PAM is judging it) or a logged-in one; it prefers a finished connection, then one from the place that "
      "holds the most pending connections, so a flood evicts itself. The page opens the QUIC connection only after the password "
      "has been typed, so nobody is evicted while typing.") + \
    p("<b>Connection ids that carry a proof.</b> Every id the server issues is " + c("CID_NONCE") + " = 10 random bytes plus " +
      c("CID_TAG") + " = 8 bytes of HMAC-SHA256, 18 bytes in all (" + c("CID_LEN") + ", " + c("SCIDLEN") + "). The HMAC key is derived "
      "from the static secret with the domain string " + c("REMOTIX CID v2") + ", and for a normal id the tag also covers the epoch "
      "(" + c("CID_EPOCH_S") + " = one hour of UTC clock); an id counts as signed for the current and the previous epoch. The tag does "
      "not decide whether a packet finds its connection, because the map is always searched. It decides which Reset budget a packet "
      "for an <i>unknown</i> id may use, so a flood of forged ids cannot use up the Resets that real clients need after a restart. "
      "Retry ids carry a different label and never count as signed. The residual limit is declared in " + c("cid.h") + ": about 100 "
      "collected ids can still use up the signed budget.") + \
    p("<b>The static secret.</b> " + c("secret_load()") + " reads or creates " + c("quic-secret") + " (32 bytes, mode 0600, owned by the "
      "running user, written through a temporary file with " + c("fsync") + " and " + c("rename") + ") in the certificates directory. "
      "Retry tokens, Stateless Reset tokens and the connection-id key all derive from it, so it must survive a restart: otherwise a "
      "client holding an old id would not recognise the Reset. If the file cannot be read or written the secret of the run is used "
      "and the log says so.") + \
    p("<b>The source address of a reply.</b> The UDP socket is bound to the wildcard, so with a plain " + c("sendto") + " the kernel would "
      "choose the source address, and a client drops a reply that does not come from the address it wrote to. " + c("pktinfo_cmsg()") +
      " builds the " + c("IP_PKTINFO") + " or " + c("IPV6_PKTINFO") + " control message that fixes the source, and " +
      c("pktinfo_sendmsg()") + " retries once without it when the kernel refuses that source (" + c("pktinfo_refusal()") + ": " +
      c("EINVAL") + ", " + c("EADDRNOTAVAIL") + ", " + c("ENETUNREACH") + ", " + c("ENODEV") + "), so a temporary address that just "
      "expired does not leave a connection mute. The destination address of an incoming datagram is read from the same control message "
      "in " + c("transport_read()") + " and becomes the local end of the ngtcp2 path.") + \
    note("every refusal and eviction is counted and summed in one log line per 10 s (" + c("REFUSAL_LOG_S") + ") instead of one line each. "
         "The same budgeting protects the «new connection» lines (" + c("BIRTH_LINES") + "), the «packet not sent» lines (" +
         c("SEND_FAIL_LINES") + ") and the lines a stranger can provoke before any login. The reply to a refusal is sent only to an "
         "Initial whose Retry token proved the address, so a forged source is not reflected.", "Refusals do not flood the log.")

# ── TLS and the certificates ────────────────────────────────────────────
S6 = p("Two TLS contexts are built by " + c("tls.c") + " from the two certificates, and they never share one. Both come from a single " +
       c("common()") + " function: " + c("TLS_server_method()") + ", minimum version TLS 1.3, server cipher preference, " +
       c("SSL_OP_NO_ANTI_REPLAY") + " and the key-exchange groups " + c("X25519MLKEM768:X25519:P-256:P-384") + " (" + c("TLS_GROUPS") +
       "). If the installed OpenSSL does not know the ML-KEM group, the list without it (" + c("TLS_GROUPS_CLASSIC") + ") is set and "
       "the log says so. The server never starts on OpenSSL's default list, because a client could then offer only an expensive group "
       "and the single loop that also serves the video would pay for each handshake.", lead=True) + \
    table(["", "QUIC context", "Page context"], [
        ["Function", c("tls_quic_context()"), c("tls_page_context()")],
        ["Certificate", "session certificate", "page certificate"],
        ["ALPN", c("h3") + ", mandatory: " + c("choose_alpn()") + " returns a fatal alert if the client does not offer it", c("http/1.1") + ", optional"],
        ["0-RTT", "off: " + c("SSL_CTX_set_max_early_data(ctx, 0)"), "not offered (TLS 1.3 default)"],
        ["Rebuilt on rotation", "yes: " + c("main.c") + " calls " + c("tls_quic_context()") + " again and " + c("transport_context()") +
         " hands it over; open connections keep the old one", "no"],
    ], "«TAB» — The two TLS contexts") + \
    p("There are two certificates, kept apart down to their file names. The page certificate is the one on which the user grants the "
      "browser exception, so it must change as rarely as possible. The session certificate is checked by fingerprint, and browsers "
      "accept that only for certificates valid less than 14 days, so it rotates on its own.") + \
    table(["", "Page certificate (long-lived)", "Session certificate (short-lived)"], [
        ["Files in the certificates directory", c("page.pem") + ", " + c("page.key") + ", marker " + c("page.ours"),
         c("session.pem") + ", " + c("session.key") + ", marker " + c("session.ours")],
        ["Validity", c("CERT_DAYS_PAGE") + " = 365 days", c("CERT_DAYS_SESSION") + " = 13 days"],
        ["Generated", "when absent; at start if expired and " + c("page.ours") + " exists", "when absent"],
        ["Rotation", "never while running", "when fewer than " + c("CERT_MARGIN_DAYS") + " = 2 days remain; checked at start and every 60 s by " +
         c("certificates_rotate_if_needed()")],
        ["Presented on", "TCP 7447", "UDP 7447"],
        ["Trusted by the browser through", "the user's one-time exception, or a real CA", c("serverCertificateHashes") + ": the fingerprint written into the page"],
    ], "«TAB» — The two certificates") + \
    p("The directory is the value of " + c("--certificates") + ". The binary's own default is " + c("/var/lib/remotix/certificates") +
      ", or the folder " + c("certificates") + " under " + c("--network-state-dir") + " when the server runs split (" + c("main.c") + "); the unit passes " +
      c("/var/lib/remotix/net/certificates") + " explicitly. " + c("debian/remotix.tmpfiles") + " creates " + c("/var/lib/remotix/net") +
      " with mode 0700 for the system user " + c("remotix") + " and keeps the modes of what is inside; the directory itself is created 0700 by " +
      c("certificates_prepare()") + ". It also holds " + c("quic-secret") + " and the log secret. " + c("certificates_prepare()") + " runs at start-up "
      "in the network side.") + \
    ul([
        "<b>Key type.</b> ECDSA P-256 only (" + c("EVP_EC_gen") + "), never Ed25519 or RSA: P-256 is the key type that keeps " +
        c("serverCertificateHashes") + " open.",
        "<b>The private key is born 0600</b> (" + c("write_pem()") + " opens it with mode 0600), not " + c("chmod") + "-ed afterwards, so there is no "
        "window in which it is readable.",
        "<b>Contents.</b> X.509 version 3, a random 128-bit serial, " + c("notBefore") + " one hour in the past, signed with SHA-256, "
        "basic constraints " + c("critical,CA:FALSE") + ", subject " + c("CN") + " equal to the name, and a " + c("subjectAltName") +
        " that " + c("san_di()") + " writes as " + c("IP:") + " or " + c("DNS:") + " according to the form of the name. The name is " + c("--name") +
        " (the unit passes " + c("%H") + ", the host name); " + c("main.c") + " refuses to start with " + c("0.0.0.0") + " or " + c("::") +
        " as the name. A user who connects by IP address declares it with " + c("REMOTIX_OPTIONS=--name 192.0.2.10") + ".",
        "<b>The administrator's certificate is never touched.</b> Every certificate REMOTIX writes has a " + c(".ours") + " marker next to it. "
        "A " + c("page.pem") + " with its key but without the marker belongs to someone else and is used as it is and never regenerated, "
        "even when it expires. The test is «did we write it?», not «is it self-signed?». The session certificate has no such exemption: "
        + c("certificates_rotate_if_needed()") + " regenerates it whatever the marker says.",
        "<b>The two must differ.</b> At start " + c("certificates_prepare()") + " compares the two fingerprints and refuses to start if they "
        "are equal, because one certificate for both listeners would bring the browser warning back every two weeks.",
        "<b>Fingerprint.</b> SHA-256 over the DER bytes of the session certificate, not over the public key and not over the PEM text "
        "(" + c("fingerprint_of()") + ", " + c("X509_digest") + "). It is kept in base64 for the page and in hexadecimal for logs; " +
        c("rotations") + " counts the generations since start (the first generation counts as one).",
    ]) + \
    warn(c("certificates_prepare()") + " never compares the name inside an existing certificate with the current " + c("--name") + ". If the "
         "host name or the option changes, the page certificate keeps its old subject alternative name until it expires or is removed, and "
         "the browser shows a name-mismatch warning. The session certificate follows the new name at its next rotation, but pinned "
         "connections do not depend on the name. Nothing in the package removes the old page certificate.",
         "A changed name is not noticed.")

# ── Pinning ─────────────────────────────────────────────────────────────
TRUST = seq([("Browser", "the page", "dark"), ("TCP 7447", "page.c", "blue"), ("UDP 7447", "webtransport.c", "navy")], [
    (0, 1, "GET /  (TLS with the long-lived certificate)"),
    ("note", 0, "first visit: user accepts the warning"),
    (1, 0, "page.html with __FINGERPRINT__ replaced", True),
    (0, 1, "GET /fingerprint  (before every connection)"),
    (1, 0, "JSON: algorithm, base64, hex, rotations", True),
    (0, 2, "new WebTransport(https://host:7447/rcp/1, serverCertificateHashes)"),
    ("note", 2, "TLS 1.3 with the 13-day certificate"),
    ("note", 0, "SHA-256 of the DER matches: no warning"),
    (0, 2, "extended CONNECT :protocol=webtransport  /rcp/1"),
    (2, 0, ":status 200  (any other path: 404)", True),
], "«FIG» — How the browser comes to trust the session", width=900)

S7 = p("The page carries the fingerprint of the session certificate, and the browser accepts the WebTransport connection without a "
       "warning when the certificate matches it. The exception the user grants on the page certificate does not extend to WebTransport, "
       "so the fingerprint is the normal road, not a safety net (RCP.md §4.1-bis).", lead=True) + TRUST + steps([
    "The server writes the current fingerprint into the page: " + c("page.c") + " replaces " + c("__FINGERPRINT__") + " in " + c("page.html") +
    " on every request for " + c("/") + ".",
    "Before every connection the page fetches " + c("/fingerprint") + " with " + c("cache: \"no-store\"") + " (" + c("page.html") + "). A tab left "
    "open for two weeks holds the fingerprint of a certificate that has since rotated, and without the fresh fetch the browser would refuse "
    "the reconnection without saying why. The fetch does not go through RCP, because there is no session yet. If it fails the page falls back "
    "to the fingerprint it was served with and says so.",
    "The page opens " + c("new WebTransport(\"https://\" + location.host + \"/rcp/1\", …)") + " with " + c("allowPooling: false") + " and " +
    c("serverCertificateHashes: [{ algorithm: \"sha-256\", value: … }]") + ".",
]) + \
    table(["Browser constraint on pinned certificates", "How REMOTIX meets it"], [
        ["Valid less than 14 days", c("CERT_DAYS_SESSION") + " = 13 days, rotated when 2 days remain"],
        ["ECDSA P-256, no RSA", "the only key type the generator produces"],
        ["SHA-256 of the certificate", "computed over the DER bytes by " + c("fingerprint_of()")],
        [c("allowPooling") + " false", "set by the page"],
    ], "«TAB» — The constraints of serverCertificateHashes") + \
    p("Whether this works on a given browser was measured, not assumed: the driving checks in " + c("prove/") + " run Chrome and Firefox against the "
      "server and open the session through this very mechanism (" + rif("What was verified for the transport") + "). Safari and iOS were never tested, "
      "and nothing here claims they work. A rotation of the certificate while a client is connected was not exercised by any check.") + \
    note("the first connection on each device is open to a man in the middle, who would not merely read the page but could rewrite it. The risk is accepted "
         "for the intended scenario, an own server on an own network or a VPN, and a certificate from a real authority removes the warning "
         "(SPECS.md §4.1, DECISIONS.md §1.7).", "Accepted risk.")

# ── The page server ─────────────────────────────────────────────────────
S8 = p(c("page.c") + " is a small HTTPS/1.1 server: one request per connection, " + c("Connection: close") + ", non-blocking sockets inside the same " +
       c("poll") + " loop. It reads " + c("page.html") + " from " + c("--page") + " (the package installs it as " + c("/usr/share/remotix/page.html") +
       ") and treats the request line only for its path: the method is logged, not judged, and the query string is cut off before the path is compared.",
       lead=True) + \
    table(["Path", "Response", "Purpose"], [
        [c("/") + ", " + c("/index.html"), "200, " + c("text/html"), "The page, gzip-compressed when " + c("Accept-Encoding") + " allows it, with four placeholders "
         "replaced: " + c("__FINGERPRINT__") + " (session fingerprint), " + c("__WARNING__") + " (the ban notice, empty if not banned), " + c("__BANNED__") +
         " (" + c("yes") + " or " + c("no") + ") and " + c("__REMAINING_MS__") + " (milliseconds left on the ban, rounded up to whole minutes)."],
        [c("/fingerprint"), "200, " + c("application/json"), "algorithm " + c("sha-256") + ", the fingerprint in base64, the same in hexadecimal and the rotations since start."],
        ["a client over the accept rate that waited in vain", "503, " + c("text/plain") + ", " + c("Retry-After: 1"),
         "«busy», so the page can tell it from «the server is not there» and ask again."],
        ["anything else", "404", "—"],
        ["unreadable or folded request", "400", "—"],
        ["request headers over " + c("MAX_REQUEST") + " = 8192 bytes", "431", "—"],
    ], "«TAB» — The routes of the page server") + \
    p("Every response carries " + c("Cache-Control: no-store") + ", " + c("X-Content-Type-Options: nosniff") + ", the three cross-origin isolation headers "
      "(" + c("Cross-Origin-Opener-Policy: same-origin") + ", " + c("Cross-Origin-Embedder-Policy: require-corp") + ", " +
      c("Cross-Origin-Resource-Policy: same-origin") + ", the macro " + c("ISOLATION") + ") and the macro " + c("PAGE_SECURITY") + ": a " +
      c("Content-Security-Policy") + " with " + c("default-src 'self'") + ", " + c("frame-ancestors 'none'") + ", " + c("connect-src 'self'") + " and the "
      "directives the page really needs, " + c("Referrer-Policy: no-referrer") + ", and a " + c("Permissions-Policy") + " that leaves the clipboard to "
      "the page itself and switches off camera, microphone, location and the other device features. Isolation gives the page full-resolution timers and shared "
      "memory (SPECS.md §11.5). The third isolation header is not optional: with " + c("require-corp") + " the browser refuses any sub-resource that does not "
      "declare it, and the symptom does not mention isolation. The reasons for each CSP directive are in the comment above " + c("PAGE_SECURITY") + ".") + \
    table(["Protection", "Value", "Constant"], [
        ["Whole request must arrive within", "10 s of the accept", c("PAGE_REQUEST_MS")],
        ["A response that stopped moving", "nothing taken for 60 s, or under 2 KiB/s on average after 20 s", c("PAGE_STALL_MS") + ", " + c("PAGE_RATE_GRACE_MS") + ", " + c("PAGE_RATE_FLOOR")],
        ["Clients at once", "128", c("PAGE_MAX_CLIENTS")],
        ["Clients per address / per IPv6 /48", "32 / 64", c("PAGE_PER_ADDRESS") + ", " + c("PAGE_PER_48")],
        ["Accept rate per address / per /48", "8 a second, burst 32 / 16 a second, burst 64", c("PAGE_ACCEPT_RATE") + ", " + c("PAGE_ACCEPT_BURST") + ", " + c("PAGE_ACCEPT_RATE_48") + ", " + c("PAGE_ACCEPT_BURST_48")],
        ["A connection over the rate waits parked, without TLS, up to", "3 s, then 503", c("PAGE_RATE_WAIT_MS")],
        ["Events handled per pass of the main loop", "16", c("PAGE_EVENTS_PER_PASS")],
    ], "«TAB» — How the page listener protects itself") + \
    p("When the table is full, " + c("fair_victim()") + " evicts by groups: clients that never sent a byte first, then clients without a whole request, then slow "
      "writers, then fresh writers, at random among equals; the newcomer is refused only if its own group would then be larger than the largest. Expired "
      "and evicted clients are closed with a reset (" + c("SO_LINGER") + " zero) so the kernel does not hold their data. The price is declared in the code: a "
      "crowd behind one address, a CGNAT or a carrier /48, is one group.") + \
    p("<b>The banned address still gets the page.</b> The ban is not checked at accept. A banned address receives the page with status 200 and a notice "
      "that begins " + c("attempts exhausted") + " and shows the hours and minutes left; the notice is built in " + c("page.c") + " and shown for the ban of the key "
      "and of the /48. The ban of one user on that key is not known to the page, which does not know the user, and the same refusal arrives through RCP. The "
      "status is 200 and not a 4xx because an intermediary or the browser may replace the body of an error response, and the sentence the owner must read "
      "would vanish.") + \
    warn("the ban notice in " + c("page.c") + " ends with «The block ends by itself when that time is up: there is no other way back in». That is the owner's "
         "decision of 17 Nov 2026: the package ships no administrator unblock. The unit passes no " + c("--command-socket") + " and there is no command-line tool; " +
         c("command.c") + " and " + c("rcp_unblock()") + " are still in the binary behind that bench option, which the checks switch on with a drop-in, and " +
         c("prove/check-ban.py") + " (check " + c("unblock-shipped") + ") records that the package gives the administrator no way to unblock, by design. A banned user "
         "waits for the ban to expire. The text of SPECS.md §4.2 still names an unblock command (" + c("UNBLOCK <address>") + ") among the ways out: it is not aligned "
         "with the decision (see " + rif("Appendix C — Known issues and open points") + ").", "No administrator unblock.")

# ── The WebTransport layer ──────────────────────────────────────────────
WIRE = table(["Item", "Value on the wire", "Where"], [
    ["Setting " + c("SETTINGS_ENABLE_WEBTRANSPORT") + " (draft 02)", c("0x2b603742") + " = 1", c("WT_ENABLE_WEBTRANSPORT")],
    ["Setting " + c("SETTINGS_WT_MAX_SESSIONS") + " (draft 07 and later)", c("0xc671706a") + " = 1", c("WT_MAX_SESSIONS")],
    ["nghttp3 settings", c("enable_connect_protocol") + " = 1, " + c("h3_datagram") + " = 1, QPACK table 4096, blocked streams 100", c("open_http3()")],
    ["Session request", c("CONNECT") + " with " + c(":protocol webtransport") + " on " + c("/rcp/1"), c("open_session()")],
    ["Answer to the session request", c(":status 200") + " and " + c("server: remotix"), c("open_session()")],
    ["Wrong path", c(":status 404") + " (logged)", c("open_session()")],
    ["Second session on one connection", c(":status 429") + " (logged)", c("open_session()")],
    ["Unidirectional stream preamble", "varint " + c("0x54") + " (on the wire " + c("40 54") + ") + session id", c("dispatch_uni()")],
    ["Bidirectional stream preamble", "varint " + c("0x41") + " (" + c("40 41") + ") + session id", c("dispatch()")],
    ["Datagram prefix", "quarter stream id of the session (varint), then the RCP datagram", c("audio_a_una()")],
    ["Closing capsule", c("CLOSE_WEBTRANSPORT_SESSION") + " " + c("0x2843") + ", u32 code, inside an HTTP/3 " + c("DATA") + " frame: " +
     c("00 07 68 43 04 00 00 00 mm"), c("close_now()")],
    ["Incoming capsule cap", "1024 + 4 bytes", c("WT_CAPSULE_MAX")],
], "«TAB» — WebTransport constants written by webtransport.c")

S9 = p(c("webtransport.c") + " is the layer on top of ngtcp2 and nghttp3. It covers three holes: WebTransport cannot be announced through the "
       "nghttp3 API; WebTransport streams must be taken away from nghttp3, which would read the session number after " + c("0x41") +
       " as a frame length; and the bytes going back on those streams have no road, because nghttp3 never schedules streams it does not know.",
       lead=True) + WIRE + \
    ul([
        "<b>Both drafts are announced.</b> The setting of draft 02 and the one of draft 07 are both sent: the test client " + c("aioquic") +
        " 1.2 implements the first and browsers look for the second, and an unknown setting is ignored by the other side.",
        "<b>HTTP/3 needs three unidirectional streams.</b> " + c("open_http3()") + " fails the connection, logged, if the client grants fewer than three.",
        "<b>One session per connection.</b> " + c("w->session") + " holds the stream id of the CONNECT. " + c("WT_CAP_CHANNEL_NS") + " (5 s) starts when the "
        "session opens: if the client does not open the control channel in time the session is closed with " + c("TIMED_OUT") + " in the closing code "
        "(DECISIONS.md §7.17).",
        "<b>Client streams are classified by their first bytes</b> (" + c("enum flavor") + "): undecided, WebTransport bidirectional (the control channel), "
        "HTTP/3 (handed back to nghttp3), WebTransport unidirectional for input (" + c("G_UNI_INPUT") + "), for clipboard (" + c("G_UNI_CLIPBOARD") + "), "
        "lawful but not served, or already judged a violation. The channel is recognised by the high byte of the first RCP type after the preamble: "
        + c("0x01") + " is input, " + c("0x02") + " clipboard; " + c("0x00") + " (control), " + c("0x03") + " (video) and " + c("0x04") +
        " (audio) on a client unidirectional stream, or any other byte, are violations of RCP.md §2.5. The first bidirectional WebTransport stream "
        "becomes the control channel and a second one is a violation.",
        "<b>The session number in the preamble is read and logged, not compared</b> with the stream id of the CONNECT (" + c("dispatch()") + ", " +
        c("dispatch_uni()") + "). With one session per connection it cannot name another one.",
        "<b>The closing capsule goes inside a " + c("DATA") + " frame.</b> Written bare, its first byte " + c("0x68") + " makes the browser read a two-byte "
        "HTTP/3 frame type " + c("0x2843") + ", an unknown frame that RFC 9114 requires to ignore; the page would see only the FIN behind it, which closes the "
        "session with code 0, the one value RCP forbids. The code is one byte of the " + c("u32") + " (" + c("mm") + " above).",
        "<b>The capsule is delayed.</b> It is queued only after the send queue of the session has drained, plus " + c("WT_CLOSE_WAIT_NS") + " (500 ms): the code "
        "comment in " + c("close_session()") + " records that browsers process the capsule before the stream bytes sent just ahead of it and throw those away, "
        "so the page never saw " + c("REJECTED") + ". If the queue does not drain, the capsule leaves all the same after a 3 s backstop.",
        "<b>A capsule from the client</b> is accumulated and parsed by " + c("closed_by_client()") + " and handed to " + c("rcp_closed_by_client()") + ". A code "
        "outside " + c("0x01") + "–" + c("0x0F") + " is logged as a violation of RCP.md §3.1 and recorded as " + c("PROTOCOL_ERROR") + ". The range stops at " +
        c("0x0F") + " although RCP.md §8.2 and " + c("reason_for_82()") + " in " + c("rcp.c") + " also accept " + c("0x10") + ": a client closing with " +
        c("0x10") + " would be logged as a violation. A real page never sends it.",
    ]) + \
    p("<b>Before login, a stranger's connection is cheap to keep and cheap to log.</b> A connection that has never logged in may open at most " +
      c("WT_PRELOGIN_SESSIONS_MAX") + " = 2 WebTransport sessions and make " + c("WT_PRELOGIN_REQUESTS_MAX") + " = 8 other HTTP/3 requests before it is closed with " +
      c("H3_EXCESSIVE_LOAD") + "; the counters start again at the moment a login is earned. Its log lines are budgeted per address key (" +
      c("WT_PRELOGIN_BURST") + " = 20 lines per " + c("WT_PRELOGIN_WINDOW_MS") + " = 10 s, " + c("WT_PRELOGIN_KEYS") + " = 128 keys) and for the whole server "
      "(" + c("WT_PRELOGIN_GLOBAL_BURST") + " = 100), so a flood cannot fill the journal of root. The line of a failed attempt that counts towards the ban and "
      "the line of the ban itself are never held back.")

# ── Streams vs datagrams ────────────────────────────────────────────────
S10 = p("Each RCP channel uses the QUIC piece that matches its needs. The design choice that matters most is that a video frame is a stream: a late frame does "
        "not hold up the next one, and the server can abandon a frame that is no longer useful with " + c("RESET_STREAM") + " so that its unsent bytes never "
        "leave.", lead=True) + \
    table(["Channel", "QUIC piece", "Opened by", "How many"], [
        ["control", "the first bidirectional stream of the session", "client", "one for the whole session"],
        ["video", "unidirectional stream", "server", "one per frame, none before " + c("SESSION") + " has been sent"],
        ["input", "unidirectional stream", "client", "exactly one, opened after " + c("SESSION") + " and kept open"],
        ["clipboard", "unidirectional stream", "both", "one per message"],
        ["audio", "datagram", "server", "one block per datagram"],
        ["cursor", "the control channel", "server", "—"],
    ], "«TAB» — Which QUIC piece each channel uses") + \
    p("On a single stream a slow frame would block all the following ones (head-of-line blocking). On datagrams the server would have to rewrite fragmentation "
      "and retransmission, QUIC inside QUIC. One stream per frame gives independence for free, and abandonment for the price of a key frame (see " +
      rif("Quality, degradation and budget") + ").") + \
    p("<b>Audio datagrams.</b> A datagram cannot be fragmented, so it must fit in one packet. " + c("audio_a_una()") + " builds the datagram: the varint "
      "of the session stream id divided by four, then the 12-byte RCP header (type " + c("0x0401") + ", codec, 64-bit instant) and the block. The server caps "
      "its datagram at " + c("WT_DGRAM_BYTE") + " = 1024 bytes and drops, counted and logged, a block larger than the peer announced in " + c("max_datagram_frame_size") +
      " (a peer that announced zero gets no audio at all, said once in the log). The 1024 is recorded in the code as the largest datagram browsers accepted in a measurement "
      "with Chrome and Firefox; the probe is not in this tree. At most " + c("WT_DGRAM_MAX") + " = 8 blocks wait to be sent, and a block that has not left "
      "within " + c("WT_DGRAM_QUIET_MAX_MS") + " = 10 ms of the queue being blocked is dropped and counted. " + c("wt_dgram_lost()") + " and " +
      c("wt_dgram_acked()") + " track losses and acknowledgements in pairs, because ngtcp2 can declare a datagram lost and later see it acknowledged, which is "
      "reordering and not loss.") + \
    p("<b>Stream credit for video.</b> The browser grants unidirectional streams to the server at its own pace. The server must survive a refused stream: when "
      "credit is missing it drops the frame, but never a key frame, which waits. " + c("WT_UNI_RESERVE") + " = 2 streams are left unused by video so the "
      "client's own streams are never starved, and at most " + c("WT_INFLIGHT_MAX") + " = 32 frames are in flight per session. A frame dropped for lack of "
      "credit is invisible to the client (no stream, no gap in the numbering), so the server owes a key frame on its own.") + \
    p("<b>The send queue.</b> Every byte to send on a stream goes through " + c("queue_put()") + ". The queue of a session is capped at " + c("WT_QUEUE_MAX") +
      " = 17 MiB (16 MiB, the largest video frame RCP allows, plus 1 MiB for control messages) and at " + c("WT_QUEUE_ITEMS_MAX") + " = 16384 elements; "
      "touching either cap is logged and the item is not queued. When a stream is flow-blocked only that stream is skipped for the pass, at most " +
      c("WT_BLOCKED_MAX") + " = 64 per pass, so one slow frame does not block the others inside the queue.") + \
    warn(c("ngtcp2_conn_writev_stream()") + " does not copy the bytes: it keeps the caller's pointer and rereads it to retransmit. A queue element therefore has "
         "two states: " + c("delivered") + " (all bytes handed to ngtcp2, memory kept) and " + c("dead") + " (freed), reached only from an acknowledgement "
         "covering the bytes, the closing of the stream or its reset. Freeing a frame once it was serialised would hand garbage to a retransmission, or "
         "crash the server on a large frame.", "The send buffer belongs to us until it is acknowledged.")

# ── Clocks ──────────────────────────────────────────────────────────────
S11 = p("Several clocks watch a connection, and they measure different things. They are listed here so that nobody mistakes one for another.", lead=True) + \
    table(["Clock", "Value", "Measures", "Effect"], [
        ["Channel deadline", c("WT_CAP_CHANNEL_NS") + " = 5 s", "from the WebTransport session to the control channel", "session closed with " + c("TIMED_OUT")],
        ["QUIC idle timeout", "30 s (" + c("IDLE_MS") + ")", "no packet at all", "ngtcp2 drops the connection silently; the log says «thirty seconds of silence»"],
        ["RCP silence", c("SILENCE") + " = 30 s in " + c("rcp.c"), "no authenticated packet from the client (" + c("rcp_sign_of_life()") + ", called by " +
         c("wt_sign_of_life()") + " for every packet that ngtcp2 decrypted and counted as received)", "the attached client is detached: its slot is freed, the connection stays open (state " + c("detached-by-silence") + ")"],
        ["Ghost eviction", c("DEFAULT_EVICTION") + " = 15 s (" + c("--eviction-ms") + ")", "a client that has not been heard for longer than this while a second client of the same user arrives",
         "the silent client loses the slot to the newcomer"],
        ["Dead line, silence", c("WT_LM_SILENCE_S") + " = 10 s (" + c("--dead-line-silence-s") + ")", "no packet from the client while at least " +
         c("WT_LM_MIN_PROVE") + " = 2 of ours went out", "the QUIC connection is closed"],
        ["Dead line, stall", c("WT_LM_STALL_MS") + " = 5000 ms (" + c("--dead-line-stall-ms") + ")", "no video byte left while there was video to send", "the QUIC connection is closed"],
        ["Keep-alive PINGs", c("WT_KEEPALIVE_NS") + " = 10 s, or half the dead-line silence", "—", "ngtcp2 keep-alive timer, armed while the RCP session is not " + c("finished")],
    ], "«TAB» — The clocks of a connection") + \
    p("<b>Transport PINGs.</b> " + c("keepalive_rule()") + " arms " + c("ngtcp2_conn_set_keep_alive_timeout()") + " when the RCP state is anything but " +
      c("finished") + " and switches it off when the session ends. The interval is " + c("keepalive_ns()") + ": half of the dead-line silence when the detector is on, so 5 s "
      "with the defaults, otherwise 10 s. Without them nothing travels while the server waits for the credentials (RCP gives 60 s for them) and the 30 s idle timeout would "
      "kill the connection, and the liveness margin would belong to the browser's own keep-alive. A PING carries no information and has no reply to interpret, so it is "
      "not the application heartbeat that RCP forbids.") + \
    note("the comment in " + c("rcp.c") + " above " + c("rcp_sign_of_life()") + " says the PINGs are on only during the credentials window. The code in " +
         c("keepalive_rule()") + " arms them for every state but " + c("finished") + ", and that is what this manual describes (the code wins).", "Comment and code disagree.") + \
    p("<b>Why the silence clock looks at packets, not at RCP bytes.</b> A user who only reads sends nothing on RCP; counting RCP bytes would detach them after 30 s "
      "while the connection is alive. The 30 s clock looks at the last decrypted and authenticated packet instead. The much longer clocks that watch what the user "
      "does (30 minutes of inactivity, 60 minutes of abandonment) are described in " + rif("The RCP/1 protocol") + ".") + \
    p("<b>The dead line.</b> " + c("dead_line_judge()") + " runs once per round and decides on two causes. <i>Silence</i>: the client showed no packet for the threshold while " +
      "at least two packets of ours went unanswered; the time alone is not enough, because a still desktop in which neither side speaks is legitimately quiet. "
      "<i>Stall</i>: no video byte left for the threshold while there was video to send; the count restarts whenever something goes out or nothing is waiting. "
      "The loss ratio from ngtcp2 is computed but is only a witness in the log, because on a line that reorders it measures reordering. When it fires, " +
      c("dead_line_fires()") + " writes one log line with all the numbers and sets the application error " + c("H3_NO_ERROR") + " with the text " + c("dead line") + ", and " +
      c("transport_expired()") + " sends a single " + c("CONNECTION_CLOSE") + " and marks the connection dead. No RCP " + c("FAREWELL") + " is sent: the line by hypothesis does not carry it, "
      "and the user comes back in by hand. The detector is on by default; " + c("--no-dead-line") + " switches it off and the start-up line says so. It is the one clock that "
      "throws out someone who is working if it is mistuned.")

# ── Congestion ──────────────────────────────────────────────────────────
S12 = p("QUIC measures the line continuously. REMOTIX uses that measurement and adds mechanisms of its own on the video queue; the policy built on them is the subject of "
        "the chapter " + rif("Quality, degradation and budget") + ".", lead=True) + \
    table(["Mechanism", "Default", "Option", "What it does"], [
        ["Congestion controller", "CUBIC (ngtcp2 default)", "—", "Never chosen explicitly (see " + rif("QUIC transport parameters") + ")."],
        ["Per-stream blocking", "always", "—", "A flow-blocked stream is skipped for the pass, not the whole queue (up to " + c("WT_BLOCKED_MAX") + " per pass)."],
        ["Stale-delta threshold", c("WT_CLEAR_THRESHOLD_MS") + " = 100 ms", c("--clear-threshold-ms") + " (0 = off)",
         "A delta frame still in the queue after the threshold is abandoned with " + c("RESET_STREAM") + "; below it the frame is kept, because streams are independent."],
        ["Pace regulator", "on, " + c("WT_RATE_SLOTS") + " = 2", c("--no-adaptive-rate"), "A new frame does not start while two delta frames already in flight still have bytes in the queue, so the frame rate falls "
         "by itself as far as the line does not carry."],
        ["Key-frame budget", c("WT_KEY_CAP_MS") + " = 2000, margin " + c("WT_KEY_MARGIN_PC") + " = 120 %", "—", "Estimates from the congestion window and the round-trip time whether a key frame can leave; "
         "before ngtcp2 has a measurement the floor " + c("WT_FLOOR_BYTE_MS") + " = 3750 bytes/ms (30 Mbit/s, the declared network floor) is assumed."],
        ["Key-frame debt belt", c("WT_KEY_DEBT_CAP_MS") + " = 1000 ms", "—", "If a key frame has been owed for longer than this and nobody has asked, one is requested from the refusals of frames."],
    ], "«TAB» — What sits between the encoder and ngtcp2") + \
    p("The threshold and the regulator are on together by default; with the threshold off the delta queue empties at every frame and the regulator can never trigger, which "
      "the start-up line says. The code comments record a declared price measured with benches that are not in this tree: up to 160 ms of extra delay on a bad line and none on a healthy one. "
      "This manual does not repeat those measurements as verified for 1.0.0.")

# ── Connection life ─────────────────────────────────────────────────────
S13 = p("One QUIC connection carries at most one WebTransport session and one RCP session. The steps follow a connection from its first datagram to its close; the RCP steps "
        "inside are in " + rif("The RCP/1 protocol") + ".", lead=True) + steps([
    "<b>First packets.</b> " + c("transport_read()") + " receives with " + c("recvmsg") + " (with the destination address from " + c("IP_PKTINFO") + " or " + c("IPV6_PKTINFO") +
    "), " + c("ngtcp2_accept") + " checks the Initial, and the admission pipeline of " + rif("Admission of new connections, Retry and Stateless Reset") + " runs. "
    + c("accept_conn()") + " creates a " + c("struct connection") + " with an 18-byte signed server connection id and the textual source address as " + c("provenance") +
    ", the key of the ban and of the logs.",
    "<b>1-RTT keys ready.</b> " + c("cb_recv_tx_key()") + " calls " + c("wt_app_ready()") + ", which runs " + c("open_http3()") + ": three unidirectional streams of the server "
    "(control, QPACK encoder, QPACK decoder) with the rewritten " + c("SETTINGS") + ".",
    "<b>CONNECT.</b> " + c("open_session()") + " accepts the session on " + c("/rcp/1") + " and the 5-second deadline for the control channel starts.",
    "<b>Control channel.</b> The first bidirectional WebTransport stream from the client becomes RCP's control channel; " + c("rcp_open()") + " creates the " + c("rcp_session") +
    " with the provenance, and the transport keep-alive is armed.",
    "<b>Life.</b> Stream data goes to " + c("rcp_receive()") + ", " + c("rcp_receive_input()") + " or " + c("rcp_receive_clipboard()") + " according to the class of the stream. Frames, "
    "audio blocks and cursor shapes coming from the per-user child are fanned out by user name (" + c("wt_video_broadcast()") + ", " + c("wt_audio_broadcast()") + ", " +
    c("wt_cursor_broadcast()") + "), each reaching only the connections whose RCP user is that user.",
    "<b>Close.</b> RCP decides why (" + rif("The RCP/1 protocol") + "), and the WebTransport layer sends the capsule. The farewell "
    "of a graphical session that is over goes through " + c("wt_dismiss_user_session_over()") + ", which chooses which connections "
    "of the user receive it (" + rif("From password to admission") + "). At shutdown " + c("transport_dismiss_all()") + " says goodbye to "
    "every session with " + c("SERVER_CLOSING") + " and the loop runs until the queues drain or a time budget (4 s in " + c("main.c") + ") expires. "
    "The log line of the connection's end, “connection with X closed (n left)”, carries the reason (" + rif("Why a connection closed") + ").",
]) + tip("the PAM verdict reaches the right connection through " + c("transport_verdict_as()") + ": the helper returns a ticket number, the transport offers it to every live session, and exactly "
         "one takes it. A verdict that finds nobody is counted as an orphan and not lost: the connection died while PAM was answering, and " + c("transport_awaits_verdict()") + " lets "
         "the caller skip starting a desktop for nobody.", "Verdict routing.")

# ── Why a connection closed ─────────────────────────────────────────────
S13B = p("A browser that cannot open a session says one thing, “Opening handshake failed”, whatever went wrong. The log says who "
        "closed the connection and why, with one line per connection: " + c("connection with ADDRESS closed (n left) — …") + ". The text is written by " + c("close_why()")
        + " in " + c("transport.c") + ", from what ngtcp2 recorded, and changes no behaviour and keeps no data of the client beyond the address that was already there.", lead=True) + \
    table(["Part of the line", "What it says", "Where it comes from"], [
        ["Who", "“the PEER closed it” (a CONNECTION_CLOSE came from the client: draining period); “WE closed it” (closing period); or “dropped without a CONNECTION_CLOSE”",
         c("ngtcp2_conn_in_draining_period2()") + ", " + c("ngtcp2_conn_in_closing_period2()")],
        ["What", "a transport error with its code and name (" + c("PROTOCOL_VIOLATION") + ", " + c("INVALID_TOKEN") + ", …); an application error with its code; “idle timeout (silence)”; “dropped silently”; "
         "“retry”; “version negotiation”; “no error recorded” when nothing was written", c("transport_error_name()") + ", " + c("e->type")],
        ["A TLS alert", "a transport error in the range 0x100 to 0x1ff is a TLS alert of the handshake and is named: 42 " + c("bad_certificate") + ", 45 " + c("certificate_expired") + ", 46 "
         + c("certificate_unknown") + ", 48 " + c("unknown_ca") + ", and so on", c("tls_alert_name()")],
        ["The peer's sentence", "the reason phrase the peer sent, cleaned (printable ASCII only, a quote turned into a dot, at most 60 characters)", c("close_why()")],
        ["The handshake", "“TLS handshake COMPLETED” or “NOT completed”", c("ngtcp2_conn_get_handshake_completed2()")],
    ], "«TAB» — What the closing line of a connection says") + \
    p("A browser that connected with a wrong fingerprint produces " + c("the PEER closed it: transport error CRYPTO 0x12e = TLS alert 46 certificate_unknown")
      + " and " + c("TLS handshake NOT completed") + ". A browser killed with SIGKILL gives, 30 s later, “dropped without a CONNECTION_CLOSE: idle timeout (silence)”. "
      "Connections that never logged in are limited to the number of lines per window of " + c("BIRTH_LINES") + ": beyond it the line goes to the detail level, with the same text; "
      "the closing of a connection that did log in is always written.") + \
    warn("The certificate of a session is made valid from <b>one hour before</b> the moment it is created (" + c("notBefore") + " = now minus 3600 s, " + c("certificates.c") + "), "
         "and the browser checks that date against <i>its own</i> clock. A client device whose clock is more than an hour behind the server's sees the certificate as “not yet valid”, and the "
         "browser says only " + ui("Opening handshake failed") + ". It is not a defect: a very wrong clock breaks every secure site anyway, and the margin is not widened. "
         "Requirement: <b>the clock of the client device must be right</b>. The closing line above is how the cause is read in the log.", "The client's clock.")

# ── Verification ────────────────────────────────────────────────────────
S14 = p("What is known about the transport at this version comes from three sources, and it helps to keep them apart.", lead=True) + \
    table(["Claim", "Evidence", "Not verified"], [
        ["Chrome and Firefox open the session by certificate pinning, input and video flow", "The browser checks of " + c("prove/all.sh") + " drive a real browser through the page and the session (PIANO.md: 34 checks per desktop, all passing, in the run «pulizia1b», with Chrome and Firefox in the base check; the final run of the wider suite gave 104 to 112 of 118 per desktop, the non-green ones explained there)", "Safari, iOS, real phones over a real network"],
        ["A dropped network is survived", c("prove/check-resilience.py") + ", check " + c("network-drop") + ": all UDP of the port is dropped for longer than the silence clock, then the same user logs in again and finds the session", "Packet loss and reordering profiles (the benches that produced the dead-line numbers are not in this tree)"],
        ["A service restart closes the desktop and the client is told", c("prove/check-resilience.py") + ", check " + c("service-restart")
         + ": after the restart the client is told or returns to the form, nothing of the old desktop is left, and a new login is a NEW session", "—"],
        ["Wrong passwords ban the address; the page still loads", c("prove/check-ban.py"), "—"],
        ["The package installs, starts and removes cleanly", c("prove/check-package.py") + " on the four virtual machines (PIANO.md)", "AppArmor profile in a session on a machine with a graphics card"],
        ["Retry, handshake rate buckets, caps and eviction, signed connection ids, Stateless Reset caps", "Present in the code and exercised implicitly by every connection of the checks (every connection passes the Retry)", "No check in " + c("prove/") + " floods the server. The unit and fuzz harnesses named in the comments of " + c("hsrate.h") + ", " + c("resetcap.h") + " and " + c("cid.h") + " are not in this tree and were not re-run"],
        ["Rotation of the session certificate", "Code path in " + c("certificates_rotate_if_needed()") + " and " + c("main.c"), "No check rotates a certificate or keeps a client connected through a rotation"],
        ["IPv6", "—", "The packaged unit binds an IPv4 wildcard; nothing exercised IPv6"],
    ], "«TAB» — What is verified about the transport and what is not")

CHAPTER = ("Transport", [
    ("The transport stack and the network side", S1),
    ("The WebTransport announcement and the SETTINGS rewrite", S2),
    ("Listeners, sockets and port 7447", S3),
    ("QUIC transport parameters", S4),
    ("Admission of new connections, Retry and Stateless Reset", S5),
    ("TLS contexts and the two certificates", S6),
    ("Certificate pinning and the fingerprint endpoint", S7),
    ("The page server on TCP", S8),
    ("The WebTransport layer: SETTINGS, CONNECT, streams and capsules", S9),
    ("Streams, datagrams and the send queue", S10),
    ("Idle timeout, keep-alive PINGs and the dead line", S11),
    ("Congestion, pacing and the video queue", S12),
    ("One connection from first packet to close", S13),
    ("Why a connection closed", S13B),
    ("What was verified for the transport", S14),
])
