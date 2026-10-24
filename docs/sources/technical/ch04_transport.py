from build import arrow, box, c, fig, note, p, rif, seq, steps, table, text, tip, ul, warn, zone

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
    + box(40, 268, 520, 46, "transport.c + ngtcp2 — QUIC v1", "one socket, connection ids, timers, PING", "dark")
    + box(40, 318, 520, 38, "ngtcp2_crypto_ossl + OpenSSL 3.5 — TLS 1.3, ALPN h3", "", "grey", 12)
    + zone(600, 40, 280, 330, "TCP 7447 — the page")
    + box(620, 70, 240, 46, "page.c", "HTTP/1.1, one request per connection", "blue")
    + arrow(740, 118, 740, 134)
    + box(620, 136, 240, 64, "routes", "/ · /index.html · /fingerprint", "light")
    + arrow(740, 202, 740, 218)
    + box(620, 220, 240, 46, "certificates.c", "long-lived + short-lived certificate", "navy")
    + box(620, 318, 240, 38, "OpenSSL — TLS 1.3, ALPN http/1.1", "", "grey", 12)
    + text(740, 300, "tls.c builds one SSL_CTX per listener", 11, "#334155"),
    900, 380, "«FIG» — The two listeners of the server and the layers of each")

FILES = table(["File", "What it does"], [
    [c("src/transport.c"), "The UDP socket, the map of connection ids, one " + c("ngtcp2_conn") + " per client, the QUIC "
     "transport parameters, version negotiation, the stateless reset token; it passes stream data, datagrams and "
     "timer expiries to the WebTransport layer."],
    [c("src/webtransport.c"), "The layer that neither ngtcp2 nor nghttp3 provides: announcing WebTransport, accepting the "
     "extended CONNECT on " + c("/rcp/1") + ", classifying client streams by their preamble, the per-frame send queue, "
     "the audio datagrams, the closing capsule, the keep-alive PINGs and the dead-line detector. It is the host of "
     + c("rcp.c") + " (the " + c("rcp_hooks") + " hooks)."],
    [c("src/rcp.c"), "The protocol itself (" + rif("RCP: the protocol model") + "). It knows nothing about QUIC: it receives "
     "bytes, returns bytes and asks its host to send them."],
    [c("src/tls.c"), "Two " + c("SSL_CTX") + ": the QUIC one (ALPN " + c("h3") + ", 0-RTT off) and the TCP one (ALPN "
     + c("http/1.1") + ")."],
    [c("src/certificates.c"), "Generates, loads and rotates the two ECDSA P-256 certificates, and computes the "
     "SHA-256 fingerprint (" + c("fingerprint") + ") of the session certificate."],
    [c("src/page.c"), "The TCP listener: serves " + c("page.html") + " with the fingerprint written into it, the "
     + c("/fingerprint") + " endpoint, gzip-compressed when the browser accepts it. Since 1.5 it has deadlines, per-address "
     "caps and an eviction of its own (see the chapter on security)."],
    [c("src/main.c"), "Owns the single " + c("poll") + " loop, reads the command-line options (" + c("--port") + ", "
     + c("--name") + ", " + c("--certificates") + ", " + c("--page") + ", " + c("--ban-file") + "), checks the "
     "certificate every 60 s and shuts everything down with " + c("SERVER_CLOSING") + "."],
], "«TAB» — The files of the transport")

S1 = p("REMOTIX has no client program: the client is the browser. A web page cannot open a bare QUIC connection, "
       "but WebTransport over HTTP/3 gives it the same building blocks the protocol was designed on — independent "
       "unidirectional streams, the abandonment of a stream with " + c("RESET_STREAM") + ", unreliable datagrams and "
       "connection migration. The server therefore speaks QUIC version 1 with mandatory TLS 1.3, HTTP/3 and "
       "WebTransport on UDP, and serves the page itself on TCP. There is no clear-text mode, and RCP never runs on "
       "TCP.", lead=True) + STACK + FILES + \
    p("Everything runs in the parent process, in one " + c("poll") + " loop: QUIC, HTTP/3, WebTransport, RCP and the "
      "page server share the thread. The two pieces of work that could block that loop live elsewhere: PAM runs in "
      "a helper process (" + c("helper.c") + ") and everything that touches the user's desktop runs in the per-user "
      "child. The transport only moves bytes between the network and those processes.")

# ── Why ngtcp2 ───────────────────────────────────────────────────────────
S2 = p("The QUIC library was chosen on 10 August 2026 with a bench (" + c("benches/01-b2-*") + "), not on paper. The "
       "question was not «which QUIC» but «which library gets as far as WebTransport on the server side, and how much "
       "glue is left to us». None of the candidates implements server-side WebTransport.", lead=True) + \
    table(["Candidate", "Outcome", "Why"], [
        [c("quiche") + " (Rust, C API)", "rejected", "Used from C it cannot announce WebTransport: the C interface has "
         "no way to add an arbitrary HTTP/3 setting (measured)."],
        [c("lsquic"), "rejected", "Requires SNI, and REMOTIX is reached by IP address; the WebTransport flag is off by "
         "default and undocumented."],
        [c("libwtf"), "rejected", "Brings a second QUIC stack (MsQuic) into the product, and its licence contradicts "
         "itself."],
        [c("ngtcp2") + " + " + c("nghttp3") + " (C)", "chosen",
         "The most complete foundations: RFC 9220 extended CONNECT, HTTP datagrams and the capsule protocol. Two real "
         "browsers opened a session through it, and the missing layer cost 373 lines of our own code."],
    ], "«TAB» — The four candidates of DECISIONS.md §6.4") + \
    p("The price is declared in " + c("webtransport.h") + ": nghttp3 offers no API to put an arbitrary setting on the "
      "HTTP/3 control stream, so the server rewrites the " + c("SETTINGS") + " frame while nghttp3 is writing it (" +
      c("rewrite_settings()") + "). That depends on the shape of the bytes nghttp3 produces, not on a promise of "
      "its API, and must be re-tested at every nghttp3 upgrade. The guard is loud: if the bytes are not the expected "
      "ones nothing is rewritten, the log says so, and the server has no WebTransport — never a misaligned control "
      "stream.") + \
    p("TLS comes from the system OpenSSL 3.5 through " + c("ngtcp2_crypto_ossl") + ", which carries the native QUIC "
      "API. Bench B2 had measured with BoringSSL, the default of the ngtcp2 examples; the product does not bundle a "
      "second cryptographic library, and " + c("tls.h") + " declares the change of stack instead of treating the two as "
      "equivalent.")

# ── Two listeners ───────────────────────────────────────────────────────
S3 = p("The server listens on port 7447 twice: UDP for HTTP/3 and WebTransport, TCP for the first load of the page. "
       "The user types " + c("https://address:7447") + ", accepts the certificate warning once per device, and types "
       "user and password into the page.", lead=True) + \
    table(["", "UDP 7447", "TCP 7447"], [
        ["Carries", "QUIC v1, HTTP/3, the WebTransport session " + c("/rcp/1"), "HTTPS (HTTP/1.1): the page, "
         + c("/fingerprint")],
        ["Certificate", "the short-lived session certificate", "the long-lived page certificate"],
        ["ALPN", c("h3") + " (chosen by the browser)", c("http/1.1")],
        [c("SO_REUSEADDR"), "never", "yes"],
        ["Code", c("transport.c") + ", " + c("webtransport.c"), c("page.c")],
    ], "«TAB» — The two listeners") + \
    p("The two are independent. The first draft of RCP.md required an " + c("Alt-Svc") + " header on the TCP response; "
      "measurement S1 (9 August 2026) showed that WebTransport does not use " + c("Alt-Svc") + " at all — a WebTransport "
      "session opens its own HTTP/3 connection to the address it is given. That also removed a feared failure mode, "
      "the silent fallback to TCP («the page opens and the desktop never arrives»): there is no fallback to make.") + \
    warn("the UDP socket is bound without " + c("SO_REUSEADDR") + ". With that option, on 10 August 2026 the socket "
         "bound to 7447 while another server already held it: two unicast UDP sockets share the port and only one of "
         "them receives the packets, so «the server is on and the page does not connect» with two processes both "
         "convinced they are listening. On TCP the option stays, because there the kernel refuses a second listener "
         "anyway and the option only avoids " + c("TIME_WAIT") + " after a restart.", "No SO_REUSEADDR on UDP.") + \
    p("The port is set with " + c("--port") + " (default " + c("7447") + ", " + c("DEFAULT_PORT") + " in "
      + c("main.c") + "). The packaged unit passes " + c("--port \"$REMOTIX_PORT\"") + ", with " + c("REMOTIX_PORT=7447")
      + " in " + c("/usr/share/remotix/remotix.conf") + " and overrides in " + c("/etc/remotix/remotix.conf.d/") + "; "
      "extra options go in " + c("REMOTIX_OPTIONS") + ". The number was chosen on 9 August 2026 because it is free in "
      + c("/etc/services") + " of Debian Trixie. Not settled yet: whether 7447 is free in the IANA registry — nobody "
      "has checked.")

# ── QUIC parameters ─────────────────────────────────────────────────────
S4 = p("Each connection gets the same transport parameters, set in " + c("transport.c") + " just before "
       + c("ngtcp2_conn_server_new") + ". With a browser as client, RCP can no longer dictate the client's parameters: "
       "what stays normative is what the server announces, and what must be measured instead of assumed.",
       lead=True) + \
    table(["Parameter", "Value", "Why"], [
        [c("max_idle_timeout"), "30 s (" + c("IDLE_MS") + ")", "The silence clock of RCP.md §2.2. It is negotiated (the "
         "minimum of the two sides wins, RFC 9000 §10.1), so lowering it would also make the browser drop us after our "
         "own silences; the 10 s rule asked by the user lives in the dead-line detector instead (" +
         rif("Keep-alive, silence and the dead line") + ")."],
        [c("initial_max_streams_uni"), "19", "RCP.md §2.3: at least 16 unidirectional streams must be available to RCP at "
         "any moment. HTTP/3 takes three as soon as the connection opens (its control stream and the two QPACK "
         "streams) and never closes them, so 16 declared were 13 usable (defect B-12, 10 Aug 2026). 19 = 16 + 3."],
        [c("initial_max_streams_bidi"), "100", "Only one bidirectional stream is ever legal for RCP (the control "
         "channel), plus HTTP/3 request streams."],
        [c("initial_max_stream_data_*"), "256 KiB", "Per-stream flow-control window, both directions."],
        [c("initial_max_data"), "1 MiB", "Connection-level window."],
        [c("max_datagram_frame_size"), "65 536", "Datagrams must be enabled (audio). Without this transport parameter "
         "announcing " + c("SETTINGS_H3_DATAGRAM=1") + " is a protocol error."],
        [c("active_connection_id_limit"), "7", "Each id leads to the same connection through the id map."],
        [c("grease_quic_bit"), "1", "Standard greasing."],
        ["stateless reset", "on", "Token derived from a 32-byte per-process secret."],
        [c("disable_active_migration"), "not sent", "Migration is the reason QUIC was chosen: the phone that moves from "
         "Wi-Fi to mobile keeps its session (SPECS.md §8.4)."],
        ["0-RTT", "refused", c("SSL_CTX_set_max_early_data(ctx, 0)") + ": 0-RTT data can be replayed, and the second "
         "message of RCP is " + c("CREDENTIALS") + ". The gain would be one round trip on a session that lasts hours."],
        ["ALPN", c("h3"), "Chosen by the browser; the server only accepts it (" + c("choose_alpn()") + " rejects a "
         "client that does not offer it)."],
        ["TLS", "1.3 minimum", c("SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION)") + "."],
        ["QUIC versions", "v1 only", "Anything else gets a version negotiation packet listing " + c("NGTCP2_PROTO_VER_V1")
         + "."],
    ], "«TAB» — QUIC transport parameters announced by the server") + \
    p("The stream credit is renewed by " + c("cb_stream_close") + " in " + c("transport.c") + ". Renewal is the peer's "
      "policy, not a consequence of closing a stream: on 2 October 2026 a measurement showed 19 streams and then "
      "nothing, so ngtcp2 does not raise the limit on its own in this configuration. A server that waited for "
      "credit would be counting on someone else's courtesy; the rule instead is that the server must survive a refused "
      "stream (" + rif("Streams versus datagrams") + ").") + \
    ul([
        "No address validation with Retry: the product is meant for an own network or a VPN (SPECS.md §4.1). The "
        "code declares it as something to restore before exposing the server.",
        "No UDP GSO: " + c("transport.c") + " splits each aggregate and sends one packet per " + c("sendto") + " (at "
        "most " + c("MAX_PACKETS_PER_ROUND") + " = 64 packets per pass). It costs system calls, not correctness.",
        "The congestion controller was never chosen: " + c("ngtcp2_settings_default()") + " leaves " + c("cc_algo")
        + " at ngtcp2's default (CUBIC). See " + rif("Congestion and the send queue") + ".",
    ]) + \
    note("the comment above " + c("SILENCE") + " in " + c("rcp.c") + " speaks of a " + c("max_idle_timeout")
         + " of 120 seconds as a hypothesis: even then the server would detach a silent client at 30 s, because the "
         "attach-slot rule runs on RCP's own clock. The value announced is 30 s.", "Two clocks, one number.")

# ── Certificates ────────────────────────────────────────────────────────
S5 = p("There are two certificates, not one, and they are kept apart down to their file names. The page certificate "
       "is the one on which the user grants the browser exception, so it must change as rarely as possible; the "
       "session certificate is checked by fingerprint, and browsers accept that only for certificates valid less than "
       "14 days, so it rotates on its own.", lead=True) + \
    table(["", "Page certificate (long-lived)", "Session certificate (short-lived)"], [
        ["Files in " + c("--certificates") + " (default " + c("/var/lib/remotix/certificates") + ")",
         c("page.pem") + ", " + c("page.key") + ", marker " + c("page.ours") + " (“ours”)",
         c("session.pem") + ", " + c("session.key") + ", marker " + c("session.ours")],
        ["Validity", c("CERT_DAYS_PAGE") + " = 365 days", c("CERT_DAYS_SESSION") + " = 13 days"],
        ["Rotation", "never while running; at startup a certificate REMOTIX generated is regenerated if it has "
         "expired", "when fewer than " + c("CERT_MARGIN_DAYS") + " = 2 days remain; checked every "
         "60 s by " + c("certificates_rotate_if_needed()") + ", which makes the caller rebuild the QUIC " + c("SSL_CTX")],
        ["Presented on", "TCP 7447", "UDP 7447"],
        ["Trusted by the browser through", "the user's one-time exception (or a real CA)", c("serverCertificateHashes")
         + " — the fingerprint written into the page"],
    ], "«TAB» — The two certificates") + \
    ul([
        "<b>Key type.</b> ECDSA P-256 only (" + c("EVP_EC_gen(\"P-256\")") + "): not Ed25519 and never RSA. P-256 is the "
        "only key type that keeps " + c("serverCertificateHashes") + " open, and a key chosen for convenience would close "
        "that road without anyone noticing.",
        "<b>The private key is born 0600</b> (" + c("open(…, 0600)") + "), not " + c("chmod") + "-ed afterwards: between "
        "creation and " + c("chmod") + " there would be a window in which it is readable.",
        "<b>The name.</b> The " + c("subjectAltName") + " is the value of " + c("--name") + " (the packaged unit passes the "
        "host name " + c("%H") + "), written as an IP address entry or a DNS entry according to its form. A browser that "
        "finds a mismatching SAN shows a different warning, and some offer no click-through at all. A user who connects "
        "by IP declares it with " + c("REMOTIX_OPTIONS=--name 192.168.1.10") + ".",
        "<b>The administrator's certificate is never touched.</b> Every certificate written by REMOTIX has a " + c(".ours")
        + " marker file next to it; a " + c("page.pem") + " without the marker belongs to someone else and is never "
        "regenerated, not even when it expires. The test is «did we write it?», not «is it self-signed?»: the second is a "
        "deduction and would be wrong on a private self-signed CA.",
        "<b>The fingerprint</b> is SHA-256 over the DER bytes of the session certificate — not over the public key and "
        "not over the PEM text (" + c("X509_digest(crt, EVP_sha256(), …)") + "). It is kept in base64 for the page and in "
        "hexadecimal for logs and browser error messages; " + c("rotations") + " counts the rotations since start.",
    ]) + \
    warn("serving the page with the short-lived certificate would bring the browser warning back every two weeks, and "
         "nobody would connect the two facts. That is exactly the defect bench B13.1 exists to see; one " + c("SSL_CTX")
         + " for both listeners would be the same defect written where nobody looks for it.",
         "Never one certificate for both.")

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

S6 = p("The page carries the fingerprint of the session certificate, and the browser accepts the WebTransport "
       "connection without a warning when the certificate matches it. The user's exception on the page certificate "
       "does not extend to WebTransport on either Chrome or Firefox (measurement S1, 9 August 2026), so the "
       "fingerprint is the normal road, not a safety net.", lead=True) + TRUST + steps([
    "The server writes the current fingerprint into the page: " + c("page.c") + " replaces " + c("__FINGERPRINT__")
    + " in " + c("page.html") + " on every request for " + c("/") + ".",
    "Before every connection the page fetches " + c("/fingerprint") + " with " + c("cache: \"no-store\"") + ". A tab left "
    "open for two weeks holds the fingerprint of a certificate that has since rotated; without the fresh fetch the "
    "browser would refuse the reconnection and nothing would say why. The fetch does not go through RCP — there is no "
    "session yet on which to ask. If it fails, the page uses the fingerprint it was served with, and says so.",
    "The page opens " + c("new WebTransport(\"https://\" + location.host + \"/rcp/1\", …)") + " with " + c("allowPooling: false")
    + " and " + c("serverCertificateHashes: [{ algorithm: \"sha-256\", value: … }]") + ".",
]) + \
    table(["Browser constraint on hash-pinned certificates", "How REMOTIX meets it"], [
        ["Valid less than 14 days", "13-day certificate, rotated 2 days before expiry"],
        ["ECDSA P-256, no RSA", "the only key type the generator produces"],
        ["SHA-256 of the certificate", "computed over the DER bytes"],
        [c("allowPooling") + " false", "set by the page"],
    ], "«TAB» — The constraints of serverCertificateHashes") + \
    p("Measured on 9 August 2026 on two independent engines: a session to a self-signed ECDSA P-256 certificate valid "
      "13 days, with the fingerprint published in the page and no warning, opened on Chrome 151 and on Firefox 140, and "
      "the bytes came back identical from both. The server on that bench was " + c("aioquic") + ", so it validated the "
      "trust model, not our server. WebKit implemented the same mechanism in October 2025, but REMOTIX has never been "
      "tested on Safari or iOS, and nothing here claims it works there.") + \
    note("the first connection on each device is open to a man in the middle, who would not merely read the page but "
         "rewrite it. The risk is accepted for the intended scenario — own server, own network or VPN — and a real "
         "certificate from a CA removes the warning altogether (SPECS.md §4.1, DECISIONS.md §1.7).",
         "Accepted risk.")

# ── The page server ─────────────────────────────────────────────────────
S7 = p(c("page.c") + " is a small HTTPS/1.1 server: one request per connection, " + c("Connection: close") + ", "
       "non-blocking sockets inside the same " + c("poll") + " loop. It reads " + c("page.html") + " from "
       + c("--page") + " (the packages install it as " + c("/usr/share/remotix/page.html") + ").", lead=True) + \
    table(["Path", "Response", "Purpose"], [
        [c("/") + ", " + c("/index.html"), "200, " + c("text/html"), "The page (gzip when the request's " + c("Accept-Encoding") + " allows it), with four placeholders replaced: "
         + c("__FINGERPRINT__") + " (session fingerprint), " + c("__WARNING__") + " (the ban notice, empty if not banned), "
         + c("__BANNED__") + " (" + c("yes") + "/" + c("no") + ") and " + c("__REMAINING_MS__") + " (milliseconds left "
         "on the ban)."],
        [c("/fingerprint"), "200, " + c("application/json"), c("{\"algorithm\":\"sha-256\",\"fingerprint\":…,\"hex\":…,\"rotations\":N}")
         + " — algorithm, fingerprint in base64, the same in hexadecimal, rotations since start"],
        ["a client over the accept rate that waited in vain", "503, " + c("text/plain") + ", " + c("Retry-After: 1"),
         "«busy: too many connections from this address» — the page tells it apart from «the server is not there» and asks again."],
        ["anything else", "404", "—"],
        ["unreadable request", "400", "—"],
    ], "«TAB» — The routes of the page server") + \
    p("Every response carries " + c("Cache-Control: no-store") + ", " + c("X-Content-Type-Options: nosniff") + " and the "
      "cross-origin isolation headers required by SPECS.md §11.5: " + c("Cross-Origin-Opener-Policy: same-origin") + ", "
      + c("Cross-Origin-Embedder-Policy: require-corp") + " and " + c("Cross-Origin-Resource-Policy: same-origin") + ". "
      "Isolation gives the page full-resolution timers (" + c("performance.now()") + " measured at 5 µs grain on Chrome 151, "
      "14 August 2026) and shared memory. The third header is not optional: with " + c("require-corp") + " the browser "
      "refuses any sub-resource that does not declare it, and the symptom does not mention isolation — the resource "
      "simply does not load. The HTML page alone carries more (CSP, " + c("frame-ancestors 'none'") + ", "
      + c("Referrer-Policy") + ", " + c("Permissions-Policy") + "), described in the chapter on security.") + \
    p("A banned address still gets the page, with HTTP status 200 and a notice that begins " + c("attempts exhausted")
      + " and gives the hours and minutes left; the notice is written in "
      + c("page.c") + ". It is shown for the bans of the key and of the /48; the ban of one user on that key is not "
      "known to the page (it does not know the user), and the same refusal comes through RCP. The notice says that too many "
      "login attempts came from the address or network and that the wait grows if it happens again (it names no number). The page is served even when banned because whoever is banned by mistake is almost always the owner, "
      "and a server that looks dead for hours is the worst diagnosis; 200 rather than a 4xx because an intermediary "
      "or the browser may replace the body of an error response with its own page, and the sentence the owner must read "
      "would vanish. The ban itself is described in " + rif("Credentials, the fixed delay and the address ban") + ".")

# ── The WebTransport layer ──────────────────────────────────────────────
WIRE = table(["Item", "Value on the wire", "Where"], [
    ["Setting " + c("SETTINGS_ENABLE_WEBTRANSPORT") + " (draft 02)", c("0x2b603742") + " = 1",
     c("WT_ENABLE_WEBTRANSPORT")],
    ["Setting " + c("SETTINGS_WT_MAX_SESSIONS") + " (draft 07+)", c("0xc671706a") + " = 1", c("WT_MAX_SESSIONS")],
    ["nghttp3 settings", c("enable_connect_protocol = 1") + ", " + c("h3_datagram = 1") + ", QPACK table 4096, "
     "blocked streams 100", c("open_http3()")],
    ["Session request", c("CONNECT") + " with " + c(":protocol webtransport") + " on " + c("/rcp/1"),
     c("open_session()")],
    ["Wrong path", c(":status 404") + " (logged)", c("open_session()")],
    ["Any other HTTP/3 request", c(":status 404"), c("cb_end_headers()")],
    ["Unidirectional stream preamble", "varint " + c("0x54") + " (on the wire " + c("40 54") + ") + session id", "both directions"],
    ["Bidirectional stream preamble", "varint " + c("0x41") + " (" + c("40 41") + ") + session id", "client's control stream"],
    ["Datagram prefix", "quarter stream id of the session (varint)", c("audio_a_una()")],
    ["Closing capsule", c("CLOSE_WEBTRANSPORT_SESSION") + " " + c("0x2843") + ", u32 code, inside an HTTP/3 "
     + c("DATA") + " frame: " + c("00 07 68 43 04 00 00 00 mm"), c("close_now()")],
    ["Incoming capsule cap", "1024 + 4 bytes", c("WT_CAPSULE_MAX")],
], "«TAB» — WebTransport constants written by webtransport.c")

S8 = p(c("webtransport.c") + " is the layer on top of ngtcp2 and nghttp3. It covers three holes: WebTransport cannot be "
       "announced through the nghttp3 API; WebTransport streams must be taken away from nghttp3, which would read the "
       "session number after " + c("0x41") + " as a frame length; and the bytes going back on those streams have no "
       "road, because nghttp3 never schedules streams it does not know.", lead=True) + WIRE + \
    ul([
        "<b>Both drafts are announced.</b> The test client " + c("aioquic") + " 1.2 implements draft 02, browsers look "
        "for draft 07. A server announcing only one would work with half of the tools — the wrong half to draw "
        "conclusions from. An unknown setting is ignored by the other side.",
        "<b>HTTP/3 needs three unidirectional streams.</b> If the client grants fewer than three, HTTP/3 is not opened "
        "and the connection fails, logged.",
        "<b>One session per connection.</b> " + c("w->session") + " holds the stream id of the CONNECT; " +
        c("WT_CAP_CHANNEL_NS") + " (5 s) starts when the session opens: if the client does not open the control "
        "channel in time, the session is closed with " + c("TIMED_OUT") + " in the closing code (DECISIONS.md §7.17).",
        "<b>Client streams are classified by their first bytes</b> (" + c("enum flavor") + "): undecided, WebTransport "
        "bidirectional (the control channel), HTTP/3 (handed to nghttp3), WebTransport unidirectional for input ("
        + c("0x01") + "), for clipboard (" + c("0x02") + "), lawful but not served, or already judged a violation. "
        "The channel is recognised by the high byte of the first RCP " + c("type") + " after the preamble, never by the "
        "stream number (" + rif("RCP: channels and stream identification") + ").",
        "<b>The closing capsule goes inside a " + c("DATA") + " frame.</b> Written bare, its first byte " + c("0x68")
        + " makes the browser read a two-byte frame type " + c("0x2843") + ", an unknown HTTP/3 frame that RFC 9114 "
        "requires to ignore; the page saw only the FIN behind it, which closes the session with code 0 — the one value "
        "RCP forbids.",
        "<b>The capsule is delayed.</b> It is queued only after the send queue of the session has drained, plus "
        + c("WT_CLOSE_WAIT_NS") + " (500 ms): bench B11 (10 August 2026, real browsers) found that Chrome drops a "
        "message sent immediately before the session is closed.",
        "<b>A capsule from the client</b> is parsed into its code and handed to " + c("rcp_closed_by_client()") + "; a "
        "code outside " + c("0x01") + "–" + c("0x0F") + " is logged as a violation of §3.1 and recorded as "
        + c("PROTOCOL_ERROR") + ".",
    ])

# ── Streams vs datagrams ────────────────────────────────────────────────
S9 = p("Each RCP channel uses the QUIC piece that matches its needs. The single most important design choice is that "
       "a video frame is a stream: a late frame does not hold up the next one, and the server can abandon a frame that "
       "is no longer useful with " + c("RESET_STREAM") + " so that its unsent bytes never leave.", lead=True) + \
    table(["Channel", "QUIC piece", "Opened by", "How many"], [
        ["control", "the first bidirectional stream of the session", "client", "one for the whole session"],
        ["video", "unidirectional stream", "server", "one per frame, none before " + c("SESSION") + " (the server's "
         "answer to the attach)"],
        ["input", "unidirectional stream", "client", "exactly one, opened after " + c("SESSION") + " and kept open"],
        ["clipboard", "unidirectional stream", "both", "one per message (DECISIONS.md §5-ter.7)"],
        ["audio", "datagram", "server", "one block per datagram"],
        ["cursor", "the control stream", "server", "—"],
    ], "«TAB» — Which QUIC piece each channel uses") + \
    p("On a single stream a slow frame would block all the following ones (head-of-line blocking) and on a mobile "
      "network the session would accumulate its own past. On datagrams the server would have to rewrite fragmentation "
      "and retransmission — QUIC inside QUIC. One stream per frame gets independence for free, and abandonment for the "
      "price of a key frame (" + rif("RCP: the video frame") + ").") + \
    p("<b>Audio datagrams.</b> A datagram cannot be fragmented: it must fit in one packet. RCP sizes PCM blocks at 5 ms "
      "(960 bytes + 12 of header = 972) for that reason, and the server caps its datagram at " + c("WT_DGRAM_BYTE")
      + " = 1024 bytes. That number is the one measured on 17 August 2026 with the probe " + c("07-b40")
      + " (since retired with the benches of closed phases)"
      + ": the largest datagram browsers accepted against our server was 1024 bytes on Chrome 151 (fixed) and 1024 "
      "growing to 1214 on Firefox 140esr after about 800 ms. PCM fits by 52 bytes on the stricter engine. At most "
      + c("WT_DGRAM_MAX") + " = 8 blocks wait to be sent; a block that has not left within " + c("WT_DGRAM_QUIET_MAX_MS")
      + " = 10 ms of the queue being blocked is dropped and counted. Losses and acknowledgements of datagrams are tracked "
      "in pairs (" + c("wt_dgram_lost()") + ", " + c("wt_dgram_acked()") + "): ngtcp2 can declare a datagram lost "
      "and later see it acknowledged, which is reordering, not loss.") + \
    p("<b>Stream credit for video.</b> The browser grants unidirectional streams to the server at its own pace. The "
      "server must survive a refused stream instead of treating it as fatal, and when the credit is missing it drops the "
      "frame — but never a key frame, which waits. " + c("WT_UNI_RESERVE") + " = 2 streams are left unused by video so "
      "that the client's own streams are never starved, and at most " + c("WT_INFLIGHT_MAX") + " = 32 frames are in flight "
      "per session. A frame dropped for lack of credit is invisible to the client (no stream, no gap in the numbering), "
      "so the server owes a key frame on its own; that rule exists because of defect B-18, 13 August 2026.") + \
    warn(c("ngtcp2_conn_writev_stream()") + " does not copy the bytes: it keeps our pointer and re-reads it to "
         "retransmit. Until 23 August 2026 a frame was freed once serialised, and a 525 298-byte frame served by "
         + c("mmap") + " crashed the server (SEGV in " + c("memmove") + "); smaller frames silently retransmitted garbage "
         "from the heap. A queue element now has two states: " + c("delivered") + " (all bytes handed to ngtcp2, kept "
         "allocated) and " + c("dead") + " (freed), reached only from an acknowledgement covering the bytes, the closing "
         "of the stream or its reset.", "The send buffer belongs to us until acknowledged.")

# ── Keep-alive and dead line ────────────────────────────────────────────
S10 = p("Three different clocks watch a connection, and they measure different things: QUIC's idle timeout measures "
        "the silence of the network, RCP's 30-second clock decides who holds an attach slot, and the dead-line detector decides "
        "when a line has stopped carrying anything.", lead=True) + \
    table(["Clock", "Value", "Measures", "Effect"], [
        ["QUIC idle timeout", "30 s", "no packet at all", "ngtcp2 drops the connection silently"],
        ["RCP silence (" + c("SILENCE") + ")", "30 s", "no authenticated packet from the client (" + c("rcp_sign_of_life()") + ")",
         "the client is detached: its attach slot is freed, the connection is left open"],
        ["Dead line, silence", c("--dead-line-silence-s") + ", default 10 s", "no packet from the client while at least "
         "two of ours went out", "the connection is closed (" + c("CONNECTION_CLOSE") + ") and the user reconnects by hand"],
        ["Dead line, stall", c("--dead-line-stall-ms") + ", default 5000 ms", "no video byte left while there was "
         "video to send", "same"],
    ], "«TAB» — The clocks of a connection") + \
    p("<b>Transport PINGs.</b> While the RCP state is anything but " + c("finished") + ", the server arms ngtcp2's keep-alive ("
      + c("ngtcp2_conn_set_keep_alive_timeout()") + ") every " + c("WT_KEEPALIVE_NS") + " = 10 s, or half of the dead-line "
      "silence when the detector is on — 5 s with the defaults. They exist for two reasons. RCP.md §4.6 gives the user 60 s "
      "to type the password, but nothing travels while they type and the 30-second QUIC idle timeout would kill the "
      "connection first (finding R1.8). And without our own PINGs the liveness margin belongs to the browser: on an idle "
      "scene packets arrived every 15 002–15 005 ms, Chrome's keep-alive, half the 30 s ceiling. PINGs carry no "
      "information and have no reply to interpret, so they are not the application heartbeat that RCP forbids.") + \
    p("<b>Why the silence clock looks at packets, not RCP bytes.</b> Counting RCP bytes, a user who was only reading lost "
      "their attach slot after 30 s and a second device took it (measured 16 August 2026: detached at 30 013 ms with the connection "
      "alive). The 30-second clock now looks at the last decrypted and authenticated packet; the minutes-long inactivity "
      "clock (" + rif("RCP: session clocks") + ") is the one that looks at what the user sends.") + \
    p("<b>Why the dead line looks at stall, not loss.</b> The first version on 23 August 2026 used ngtcp2's "
      + c("pkt_lost / pkt_sent") + " and ordered the two reference lines backwards: a line that held for ten minutes "
      "declared 512‰ and one that did not hold 123‰, because ngtcp2 counts an overtaken packet as lost and on a "
      "reordering line the ratio measures reordering. Output stall separated the two cases sixtyfold (0.50 s against "
      "30.06 s). The ratio survives only as a witness in the log line. The detector is on by default since 24 August "
      "2026 (" + c("--no-dead-line") + " turns it off).") + \
    p("<b>Why the idle timeout stays at 30 s.</b> The value is negotiated, so 10 s would also make the browser drop us "
      "after 10 s of our own silence, and frozen images up to 14.26 s were measured on 23 August 2026 under heavy bursty "
      "loss; ngtcp2 expires at " + c("max(idle, 3·PTO)") + " anyway; 30 s is normative (DECISIONS.md §4.4); and the "
      "PINGs every 10 s would fire at the same instant as a 10 s timeout.")

# ── Congestion ──────────────────────────────────────────────────────────
S11 = p("QUIC measures the line continuously, which v1 had to do by hand. REMOTIX uses that measurement and adds three "
        "mechanisms of its own on the video queue; the policy built on them — quality, frame-rate reduction, budget — is "
        "the subject of the chapter «Quality, degradation and budget».", lead=True) + \
    table(["Mechanism", "Default", "Option", "What it does"], [
        ["Congestion controller", "CUBIC (ngtcp2 default)", "—", "Never chosen explicitly. A loss-based controller reads "
         "a Wi-Fi radio loss as congestion and halves the window. Not settled yet: an experiment with another algorithm, "
         "behind its own switch."],
        ["Per-stream blocking", "always", "—", "When a stream is flow-blocked only that stream is skipped for the pass, "
         "not the whole queue (up to " + c("WT_BLOCKED_MAX") + " = 64 per pass); otherwise one slow frame would block all "
         "the following ones inside our own queue."],
        ["Stale-delta threshold", c("WT_CLEAR_THRESHOLD_MS") + " = 100 ms", c("--clear-threshold-ms N") + " (0 = off)",
         "A delta frame still in our queue after the threshold is abandoned with " + c("RESET_STREAM") + "; below it the "
         "frame is kept, because streams are independent."],
        ["Pace regulator", "on, " + c("WT_RATE_SLOTS") + " = 2", c("--no-adaptive-rate"), "A new frame does not "
         "start while two delta frames already in flight still have bytes in our queue: the frame rate drops by itself, "
         "exactly as much as the line does not carry."],
        ["Key-frame budget", c("WT_KEY_CAP_MS") + " = 2000, margin 120 %", "—", "Estimates from " + c("cwnd") + " and "
         "RTT whether a key frame can leave; before ngtcp2 has a measurement the floor " + c("WT_FLOOR_BYTE_MS")
         + " = 2500 bytes/ms is assumed."],
    ], "«TAB» — What sits between the encoder and ngtcp2") + \
    p("<b>Pacing is honoured, and a write burst is at most the send quantum.</b> ngtcp2 paces the packets it hands out; "
      "the QUIC write path used to bypass it (present since 1.0, found on 24 October 2026 by the pacing oracle of the "
      + c("quic-conn") + " fuzz): " + c("ngtcp2_conn_write_aggregate_pkt2()") + " with " + c("num_pkts = 0") + " does "
      "not clamp its buffer length, so the 64 KB buffer let a single call put about 45 full packets on the wire at "
      "once. The buffer length is now the send quantum of ngtcp2, never less than one full-size packet (the size ngtcp2 "
      "recommends, PMTUD) and never more than the buffer. With pacing honoured a pacing deadline follows every send "
      "quantum, so the loop timeout is rounded <b>up</b> to the millisecond: rounded down it woke as much as 1 ms early and "
      "spun on " + c("poll(0)") + " until the deadline.") + \
    note("the threshold and the regulator are on together by default since 24 August 2026 (the user's decision after "
         "watching them). With the threshold off the delta queue empties at every frame and the regulator can never "
         "trigger; the start-up log line says so. Their declared price, measured on 23–24 August 2026 with bench "
         + c("09-b79") + " (retired on 11 October 2026, DECISIONS.md §10.44; its results stay in "
         + c("phases/09-quality-and-degradation.md") + "): up to +160 ms of drift on a bad line, zero on a "
         "healthy one.", "Defaults.") + \
    note(c("WT_FLOOR_BYTE_MS") + " assumes 20 Mbit/s, while the declared network floor became 30 Mbit/s on 23 August "
         "2026 (SPECS.md §8.1). It only applies before the first RTT sample.", "Stale floor.")

# ── Connection life ─────────────────────────────────────────────────────
S12 = p("One QUIC connection carries at most one WebTransport session and one RCP session. The figure follows a "
        "connection from its first datagram to its close; the RCP steps inside it are in " + rif("RCP: the handshake")
        + ".", lead=True) + steps([
    "<b>First packet.</b> " + c("transport_read()") + " receives with " + c("recvmsg") + " (with the destination address "
    "from " + c("IP_PKTINFO") + "/" + c("IPV6_RECVPKTINFO") + "), " + c("ngtcp2_accept") + " checks the Initial packet, "
    "and a new " + c("struct connection") + " is created with an 18-byte server connection id. The source address in text "
    "form becomes the " + c("provenance") + " used for the ban and the logs.",
    "<b>Handshake keys ready.</b> " + c("wt_app_ready()") + " opens HTTP/3: three unidirectional streams of our own "
    "(control, QPACK encoder, decoder) with the rewritten " + c("SETTINGS") + ".",
    "<b>CONNECT.</b> The session opens on " + c("/rcp/1") + " and the 5-second deadline for the control channel starts.",
    "<b>Control channel.</b> The first bidirectional WebTransport stream from the client becomes RCP's control channel; "
    + c("rcp_open()") + " creates the " + c("rcp_session") + " with the provenance and the current millisecond clock.",
    "<b>Life.</b> Stream data goes to " + c("rcp_receive()") + ", " + c("rcp_receive_input()") + " or "
    + c("rcp_receive_clipboard()") + " according to the stream's class; frames, audio blocks and cursor shapes from the "
    "child are fanned out by user name (" + c("wt_video_broadcast()") + ", " + c("wt_audio_broadcast()") + ", "
    + c("wt_cursor_broadcast()") + "), each reaching only the connections whose RCP user is that user.",
    "<b>Close.</b> RCP decides why (" + rif("RCP: the farewell") + "); the WebTransport layer sends the capsule. At "
    "shutdown " + c("transport_dismiss_all()") + " says goodbye to every session with " + c("SERVER_CLOSING")
    + " and waits for queues to drain before the process exits.",
]) + tip("the PAM verdict reaches the right connection through " + c("transport_verdict()") + ": the helper returns a "
         "ticket number, the transport offers it to every live session, and exactly one takes it. A ticket that finds "
         "nobody is lost on purpose — the connection died while PAM was answering.", "Verdict routing.")

CHAPTER = ("Transport: QUIC, HTTP/3, WebTransport", [
    ("The transport stack at a glance", S1),
    ("Why ngtcp2 and nghttp3", S2),
    ("Two listeners on port 7447", S3),
    ("QUIC transport parameters", S4),
    ("TLS and the two certificates", S5),
    ("serverCertificateHashes and the fingerprint", S6),
    ("The page server", S7),
    ("The WebTransport layer", S8),
    ("Streams versus datagrams", S9),
    ("Keep-alive, silence and the dead line", S10),
    ("Congestion and the send queue", S11),
    ("A connection from first packet to close", S12),
])
