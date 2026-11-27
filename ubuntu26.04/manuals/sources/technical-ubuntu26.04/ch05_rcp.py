from build import c, flow, note, p, rif, seq, steps, table, tip, ul, warn

# ── Where RCP lives ─────────────────────────────────────────────────────
S1 = p("RCP/1, the Remotix Control Protocol, is what the page and the server say to each other inside the WebTransport session. "
       "Its specification is " + c("docs/RCP.md") + ", written before the code and precise enough to prove an implementation wrong; this "
       "chapter does not copy it. It records what " + c("src/rcp.c") + " does at each message, so that a maintainer can go from a "
       "message name to the function that handles it, and says where the code and the specification differ.", lead=True) + \
    table(["RCP.md section", "Subject", "Where it is implemented"], [
        ["§2", "The transport: QUIC parameters, streams, who opens what, the port", c("transport.c") + ", " + c("webtransport.c") + " (" + rif("Transport") + ")"],
        ["§3", "The rigor rule and what «close» means in bytes", c("dismiss()") + ", " + c("rcp_violation()") + " in " + c("rcp.c")],
        ["§4.1, §4.1-bis", "The certificate and certificate pinning", c("certificates.c") + ", " + c("page.c") + " (" + rif("Transport") + ")"],
        ["§4.2–§4.6", "Control channel, HELLO, credentials, the address ban, ATTACH, deadlines", c("handle_hello()") + ", " + c("handle_credentials()") + ", " + c("handle_attach()") + ", " + c("rcp_time()")],
        ["§5", "The channel map: frames, audio, clipboard, cursor limits", c("rcp_video_open()") + " and related, " + c("webtransport.c")],
        ["§6", "Message format: elementary types, framing, video header, audio datagram", c("drain_at()") + ", " + c("rcp_video_open()") + ", " + c("audio_a_una()")],
        ["§7", "The messages: control, cursor, input, clipboard, bench, TERMINATE_SESSION", "the table in " + rif("Message map: every type and the function that handles it")],
        ["§8", "The farewell and the reasons", c("dismiss()") + ", " + c("reject()") + ", " + rif("FAREWELL, REJECTED and the sixteen reasons")],
        ["§9", "Versions", c("handle_hello()") + " and the path check in " + c("open_session()")],
        ["§10, §11", "What RCP does not do; how to test against the specification", rif("Testing")],
    ], "«TAB» — Where each part of RCP.md is implemented") + \
    p("<b>What the module knows.</b> " + c("rcp.c") + " knows RCP and nothing else: no sockets, no QUIC, no clock of its own, no PAM, no compositor. Time arrives as a "
      "parameter (" + c("rcp_time()") + " and the " + c("now") + " argument of each call), bytes leave through hooks, so a test can make time run as it wants. "
      "Everything it needs from the product reaches it through the function pointers of " + c("rcp_hooks") + " in " + c("rcp.h") + ": sending on the control channel, "
      "closing the session, the log, the PAM question, opening and writing video and clipboard streams, the five input injections, resizing the stage, keyboard layouts, "
      "the local-session test, terminating the session and a few more. A missing hook is logged and never treated as a client violation. The host of the hooks is "
      + c("webtransport.c") + " (the stream ones) and " + c("main.c") + " (the ones that reach the child, PAM and the budget). The comment in " + c("rcp.h") + " that says "
      "the hooks are «three, and no more» is stale: there are twenty-nine.") + \
    p("<b>The client.</b> The only client is the page, " + c("src/page.html") + ", which speaks RCP in JavaScript. The server and the page are two readings of the same "
      "specification written by the same people; the document " + c("RCP.md") + " is the referee, and a test that wants to prove either wrong should read the "
      "document and not the other program. The test programs that did this in the earlier work are not part of this tree.")

# ── The message map ─────────────────────────────────────────────────────
S2 = p("Every message has a 16-bit type. The high byte is the channel: " + c("0x00") + " control, " + c("0x01") + " input, " + c("0x02") + " clipboard, " + c("0x03") + " video, " +
       c("0x04") + " audio. The table gives, for every type the code knows, who sends it, in which RCP state it is legal, and the function to read. Control messages "
       "are all dispatched by one " + c("switch") + " in " + c("drain_at()") + "; the state is the enum " + c("enum state") + " (" + c("wait-hello") + ", " +
       c("wait-credentials") + ", " + c("wait-verdict") + ", " + c("wait-attach") + ", " + c("active") + ", " + c("detached-by-silence") + ", " + c("finished") + ").", lead=True) + \
    table(["Type", "Name", "From", "Legal in state", "Handler and what it does"], [
        "Control channel (the first bidirectional stream)",
        [c("0x0001"), c("HELLO"), "client", c("wait-hello"), c("handle_hello()") + ": version, capabilities, negotiation; answers " + c("HERE_I_AM")],
        [c("0x0002"), c("HERE_I_AM"), "server", "—", c("send_here_i_am()") + ": version and four capabilities (five with " + c("video.pace") + ")"],
        [c("0x0003"), c("CREDENTIALS"), "client", c("wait-credentials"), c("handle_credentials()") + ": user and password, limiter, asks PAM through the " + c("ask_verify") + " hook"],
        [c("0x0004"), c("ADMITTED"), "server", "—", "sent by " + c("rcp_time()") + " once the verdict is in and the fixed second has passed"],
        [c("0x0005"), c("REJECTED"), "server", "—", c("reject()") + ": one byte, the reason; the session ends"],
        [c("0x0006"), c("ATTACH"), "client", c("wait-attach"), c("handle_attach()") + ": canvas, view, layout; answers " + c("SESSION")],
        [c("0x0007"), c("SESSION"), "server", "—", "written inside " + c("handle_attach()")],
        [c("0x0008"), c("VIEW"), "client", c("active") + ", after " + c("SESSION"), "case " + c("T_VIEW") + " in " + c("drain_at()") + ": validates and stores the new view size; the canvas does not change"],
        [c("0x0009"), c("LAYOUT"), "client", c("active") + ", after " + c("SESSION"), "case " + c("T_LAYOUT") + ": validates the name, asks the stage through " + c("apply_layout()")],
        [c("0x000A"), c("CURSOR_SHAPE"), "server", "—", c("rcp_cursor_shape()") + ": " + c("u16") + " width, height, " + c("i16") + " hot spot x, y, then RGBA; width and height both zero means hidden"],
        [c("0x000B"), c("FIT_CANVAS"), "client", c("active") + ", after " + c("SESSION"), "case " + c("T_FIT_CANVAS") + ": clamps, asks the stage, answers " + c("CANVAS")],
        [c("0x000C"), c("FAREWELL"), "both", "any", "client: case " + c("T_FAREWELL") + "; server: " + c("dismiss()")],
        [c("0x000D"), c("REQUEST_KEY"), "client", c("active") + ", " + c("detached-by-silence"), c("handle_key_request()") + ": " + c("u32") + " last frame number"],
        [c("0x000E"), c("CANVAS"), "server", "—", c("send_canvas()") + ": outcome, reason, canvas in force; also " + c("rcp_canvas_adapted_now()")],
        [c("0x000F"), c("BENCH_MARK"), "client", "test build only", c("handle_bench_mark()") + ", compiled only with " + c("REMOTIX_BENCH") + "; in the installed binary it is an unknown type"],
        [c("0x0010"), c("BENCH_OUTCOME"), "server", "—", "test build only"],
        [c("0x0011"), c("TERMINATE_SESSION"), "client", c("active") + ", " + c("detached-by-silence"), "case " + c("T_TERMINATE_SESSION") + ": farewell " + c("0x10") + " first, then the " + c("terminate_session") + " hook"],
        [c("0x0012"), c("PACE"), "client", c("active") + ", only if " + c("video.pace") + " was negotiated", c("handle_pace()") + ": " + c("u16") + " max frames per second: a value below 5 becomes 5, while 0 or 60 and above lifts the ceiling (" + c("rcp_pace_clamp()") + "); off by default (see below)"],
        "Input channel (one client unidirectional stream, high byte 0x01)",
        [c("0x0101"), c("POINTER"), "client", "after " + c("SESSION"), c("handle_input()") + " via " + c("rcp_receive_input()") + ": id, instant, x, y (20-byte body)"],
        [c("0x0102"), c("BUTTON"), "client", "idem", "id, instant, evdev code, pressed (15 bytes)"],
        [c("0x0103"), c("WHEEL"), "client", "idem", "id, instant, signed axis x, y; 120 is one notch (20 bytes)"],
        [c("0x0104"), c("LETTER"), "client", "idem", "id, instant, one Unicode scalar value; surrogates and values above U+10FFFF are violations (16 bytes)"],
        [c("0x0105"), c("KEY_POSITION"), "client", "idem", "id, instant, evdev code, pressed (15 bytes)"],
        "Clipboard channel (one unidirectional stream per transfer, either direction, high byte 0x02)",
        [c("0x0201"), c("CLIPBOARD_ANNOUNCE"), "both", "after " + c("SESSION"), c("handle_clipboard()") + " via " + c("rcp_receive_clipboard()") + ": transfer number and byte length, 8 bytes; length over " + c("RCP_CLIPBOARD_CAP") + " = 1 000 000 is a violation"],
        [c("0x0202"), c("CLIPBOARD_ASK"), "both", "idem", "transfer number, 4 bytes"],
        [c("0x0203"), c("CLIPBOARD_TEXT"), "both", "idem", "transfer number then UTF-8 up to the end of the message"],
        "Video (one server unidirectional stream per frame) and audio (datagrams)",
        [c("0x0301"), "key frame", "server", "after " + c("SESSION"), c("rcp_video_open()") + ", " + c("rcp_video_piece()") + ", " + c("rcp_video_finish()") + "; 28-byte header (" + c("V_HEADER") + ")"],
        [c("0x0302"), "delta frame", "server", "after " + c("SESSION"), "same; refused while a key frame is owed"],
        [c("0x0401"), "audio block", "server", "negotiated codec", c("audio_a_una()") + " in " + c("webtransport.c") + ": type, codec, 64-bit instant, samples"],
    ], "«TAB» — The messages of RCP/1 and the code that handles each") + \
    p("All integers are big-endian, no field is aligned and nothing is padded. A string is a 16-bit length followed by that many bytes. The reader helpers of " + c("rcp.c") +
      " are named " + c("le_u8()") + ", " + c("le_u16()") + ", " + c("le_u32()") + " and " + c("le_str()") + "; the " + c("le") + " is the Italian " + c("legge") +
      " («reads») and not «little-endian», which is easy to misread. The writers are " + c("sc_byte()") + ", " + c("sc_u16()") + ", " + c("sc_u32()") + ", " + c("sc_u64()") + " and " + c("sc_str()") + ".") + \
    p("The frame header, written by " + c("rcp_video_open()") + ", is 28 bytes: " + c("u16") + " type, " + c("u16") + " codec (1 = HEVC, 2 = AV1, 3 = H.264, see " + c("rcp_codec_negotiated()") +
      "; the server never negotiates AV1), " + c("u32") + " canvas width and height, " + c("u32") + " frame number (it starts at 1 and skips 0 on wrap, " + c("next_number()") +
      "), " + c("u64") + " instant in microseconds and " + c("u32") + " id of the last input injected (" + c("0") + " means none). There is no length: the end of the stream is the end of the frame. "
      "The frame is capped at " + c("V_CAP") + " = 16 MiB including the header; a larger one is refused with " + c("RCP_VIDEO_TOO_LARGE") + " and the caller re-encodes at lower quality. "
      "A stream that cannot be completed is ended with " + c("RESET_STREAM") + " and never with a FIN, because a FIN would make a short frame look valid.")

# ── Framing and the rigor rule ──────────────────────────────────────────
S3 = p("The first rule of RCP is that an implementation that receives something it does not understand closes with " + c("PROTOCOL_ERROR") + " and writes in the log what "
       "it did not understand. It does not ignore, guess or carry on. In " + c("rcp.c") + " that rule is concentrated in a few functions.", lead=True) + \
    steps([
        "<b>Accumulate, bounded.</b> " + c("rcp_receive()") + " appends the bytes to a per-session buffer through " + c("accumulate()") + ". The buffer grows on demand and only up to " +
        c("MAX_ACCUMULATION") + ", equal to " + c("MAX_MESSAGE") + " = 1 MiB, framing included (" + c("MAX_BODY") + " = 1 MiB minus the 6-byte header). A body above it is " +
        c("PROTOCOL_ERROR") + " before any allocation.",
        "<b>Header.</b> " + c("drain_at()") + " reads the 6-byte header: " + c("u16") + " type, " + c("u32") + " body length. On the control channel the high byte of the type must be " + c("0x00") +
        ". The length is checked before the body is waited for.",
        "<b>Length against the fields, before any effect.</b> " + c("measure_fields()") + " reads the body a second time just to measure the fields that type must have; if the declared "
        "length differs, the connection is closed before the message has any effect on the wire or the state. It is a second reader of the same layouts: whoever changes a body in a handler "
        "changes it here too, and the check after the " + c("switch") + " (" + c("l.i != lung") + ") is what notices when they do not. A body that is too short is left to the handler, which "
        "can say which field was missing.",
        "<b>The rate gate</b> for the control messages that have one (below), then the " + c("switch") + " on the type with the state check of each case: a message in the wrong state is " +
        c("PROTOCOL_ERROR") + " with the text «X in the wrong state».",
        "<b>Text rules.</b> Names are lower-case letters, digits, " + c(".") + " and " + c("_") + " (" + c("valid_name()") + "); values are printable (" + c("printable_text()") + "); a " +
        c("FAREWELL") + " detail must be valid UTF-8 (" + c("valid_utf8()") + "); a password with an embedded zero byte is refused because what arrives and what would be judged would differ.",
    ]) + \
    p("<b>What closing means in bytes.</b> " + c("dismiss()") + " is the one road: it logs the reason, state and detail, releases the held keys and buttons (" + c("release_on_detach()") +
      "), sends " + c("FAREWELL") + " (reason byte and detail string) if the channel is still usable, frees the attach slot, sets the state " + c("finished") + " and calls the " + c("close") +
      " hook, which makes " + c("webtransport.c") + " close the WebTransport session with the application error code equal to the reason (see " + rif("Transport") + "). The reason therefore "
      "travels twice: in the message, and in the close code, so it arrives even when the control channel is broken. Code 0 is never used. " + c("reject()") + " does the same for " +
      c("REJECTED") + ", which carries the reason itself and is not followed by a " + c("FAREWELL") + ". " + c("rcp_violation()") + " is for faults the host sees (a stream in the wrong "
      "direction, two bidirectional streams): the same close, with the control channel still usable in most cases.") + \
    p("<b>After the end.</b> Bytes that arrive on the control channel when the state is already " + c("finished") + " are judged by " + c("judge_after_end()") + ", on messages and not "
      "on the first bytes of the piece: a " + c("FAREWELL") + " that crossed the server's own close is the client doing what the specification demands and is not a violation, while any other "
      "message after the end (for example a second " + c("CREDENTIALS") + " after " + c("REJECTED") + ") is logged as a violation. Nothing is sent back.") + \
    table(["Where in rcp.c", "What the code tolerates or reduces, and logs", "Instead of closing"], [
        [c("handle_hello()"), "a " + c("video.max_size") + " or " + c("video.level") + " that is not in its form is ignored", "the canvas then has no ceiling, or no level is enforced"],
        [c("handle_hello()"), "unknown capability names are ignored and counted; discarded codec entries are listed", "negotiation goes on with the known ones"],
        [c("handle_attach()"), "a canvas above 4096 by 2304 is reduced side by side", "SESSION grants the reduced size"],
        [c("handle_attach()"), "a canvas above the client's decoder ceiling is reduced keeping proportions, both sides even", "SESSION grants it; below 320 by 240 after reduction is " + c("SESSION_UNSERVABLE")],
        [c("handle_attach()"), "the stage already has a canvas and it outlives the client", "SESSION grants the stage's canvas"],
        [c("drain_at()") + ", " + c("T_FIT_CANVAS"), "a size below the minimum, or one the budget or compositor cannot serve", c("CANVAS") + " with outcome REFUSED"],
        [c("drain_at()") + ", " + c("T_LAYOUT"), "a layout the machine does not have, after the session is open", "the old layout is kept, logged"],
        [c("handle_key_request()"), "a " + c("REQUEST_KEY") + " within " + c("V_GRACE_KEY") + " = 200 ms of the last key frame, or within " + c("V_KEY_ASK_GAP_MS") + " = 100 ms of the last accepted one", "ignored or deferred"],
        ["the rate gates", "input and control messages over the rate", "consumed without effect, counted"],
        [c("rcp_receive_clipboard()"), "a full table of clipboard streams", "a stream with no message in progress is dropped, logged; if all eight are halfway it is a violation"],
    ], "«TAB» — Places in rcp.c where a fault is answered without closing") + \
    p("RCP.md §3 carries the list of declared exceptions to the rigor rule. The table above is the list of places in the code that write «TOLERANCE» or «DECLARED FALLBACK» and does not "
      "claim to equal it exactly; a maintainer who adds a tolerance is expected to add its row to RCP.md §3 in the same change.")

# ── The handshake ───────────────────────────────────────────────────────
HAND = seq([("Page", "browser", "dark"), ("rcp.c", "RCP session", "navy"), ("PAM helper", "root side", "blue")], [
    ("sep", "WebTransport session open on /rcp/1; control channel within 5 s"),
    (0, 1, "HELLO  (version, capabilities)"),
    (1, 0, "HERE_I_AM  (version, capabilities)", True),
    (0, 1, "CREDENTIALS  (user, password)"),
    (1, 2, "ask_verify: user, password, ticket"),
    ("note", 1, "fixed second: never before 1 s from CREDENTIALS"),
    (2, 1, "verdict for the ticket", True),
    (1, 0, "ADMITTED  (or REJECTED with the reason)", True),
    (0, 1, "ATTACH  (canvas, view, layout)"),
    (1, 0, "SESSION  (state, canvas, desktop)", True),
    ("sep", "channels flow: video streams, audio datagrams, input stream, clipboard streams"),
], "«FIG» — The messages of a connection, in an order that admits no permutation", width=900)

S4 = p("The handshake has five steps and runs on the control channel. Every message that arrives in a state that does not expect it is a " + c("PROTOCOL_ERROR") + ". Three properties follow from "
       "the order: the server proves who it is (TLS with the pinned certificate) before the password leaves the browser; authentication comes before attachment, so whoever is not admitted cannot "
       "even name a session; and the canvas is agreed at attach time.", lead=True) + HAND + \
    table(["State", "Entered when", "Leaves when", "Deadline", "On expiry"], [
        [c("wait-hello"), c("rcp_open()") + " (the control channel opened)", c("HELLO") + " accepted", c("CAP_HELLO") + " = 5000 ms", c("TIMED_OUT")],
        [c("wait-credentials"), c("HERE_I_AM") + " sent", c("CREDENTIALS") + " received", c("CAP_CREDENTIALS") + " = 60 000 ms (a person typing)", c("TIMED_OUT")],
        [c("wait-verdict"), c("CREDENTIALS") + " received", "verdict in and the floor passed", c("VERDICT_CAP") + " = 12 000 ms for the helper's answer", "refused, and it counts as a failed attempt"],
        [c("wait-attach"), c("ADMITTED") + " sent", c("ATTACH") + " received", c("CAP_ATTACH") + " = 10 000 ms", c("TIMED_OUT")],
        [c("active"), c("SESSION") + " sent", "farewell, close, silence, inactivity", "see " + rif("Clocks of an attached session"), "see below"],
        [c("detached-by-silence"), "30 s without a packet while active", "the client speaks again, or the session ends", "—", "the slot is taken back if still free, else " + c("ALREADY_ACTIVE_REMOTELY")],
        [c("finished"), "any close", "—", "—", "—"],
    ], "«TAB» — The states of an RCP session and their deadlines") + \
    p("The clock " + c("s->since") + " restarts after each message that is fully processed, and " + rif("Transport") + " adds a fifth deadline in front of these: " + c("WT_CAP_CHANNEL_NS") +
      " = 5 s from the WebTransport session to the opening of the control channel, which closes the session with " + c("TIMED_OUT") + " without a " + c("FAREWELL") + ", because the control channel "
      "does not exist.")

# ── HELLO ───────────────────────────────────────────────────────────────
S5 = p(c("HELLO") + " carries the highest major version the client speaks and its capabilities: a count and pairs of name and value strings. " + c("handle_hello()") + " is the function. "
       "A version other than " + c("RCP_VERSION") + " = 1 closes with " + c("INCOMPATIBLE_VERSION") + ". The version lives in two places that must coincide, the path " + c("/rcp/1") +
       " (checked by " + c("open_session()") + ", wrong path: HTTP 404) and this field.", lead=True) + \
    table(["Capability", "Client sends", "What the server does"], [
        [c("video.codec"), "list in the client's order of preference", "picks the first entry that is also in the server's list " + c("our_codec") + " (set at start-up from what the graphics card really encodes; the built-in default " + c("hevc,h264") + " serves only tests); none in common is " + c("NOTHING_IN_COMMON")],
        [c("video.depth"), "list", "must contain " + c("8") + " (the server offers " + c("OUR_DEPTH") + " = " + c("8,10") + "); otherwise " + c("NOTHING_IN_COMMON")],
        [c("audio.codec"), "list", "must contain " + c("pcm") + " (the server offers " + c("OUR_AUDIO") + " = " + c("opus,pcm") + " and picks the client's first common one); otherwise " + c("NOTHING_IN_COMMON")],
        [c("video.max_size"), c("WIDTHxHEIGHT") + " in whole pixels", "the decoder ceiling the granted canvas must respect (" + c("parse_max_size()") + ")"],
        [c("video.level"), c("MAJOR.MINOR") + ", for example 5.1", "stored as tenths (" + c("parse_level()") + "), imposed on the encoder through " + c("rcp_level_negotiated()") + "; absent means no ceiling"],
        [c("clipboard.text"), c("yes") + " or " + c("no"), "enables the clipboard messages for the session"],
        [c("video.pace"), c("yes"), "only meaningful when the server declared it too"],
        [c("input.touch") + ", " + c("client.name"), "free", "known names: accepted, not acted on in " + c("rcp.c")],
    ], "«TAB» — Capabilities of HELLO and what handle_hello() does with them") + \
    p("A name that appears twice is a violation, a name that is not lower-case-and-digits is a violation, an empty value is a violation, and so is a value above 256 bytes or not printable. An "
      "unknown name is ignored (that is how future versions will talk) but the repetition of unknown names is tracked up to " + c("MAX_SEEN") + " = 64 of them. " + c("HERE_I_AM") + " declares the server's "
      "lists, not the choice: " + c("video.codec") + ", " + c("video.depth") + ", " + c("audio.codec") + ", " + c("clipboard.text") + " = yes, and " + c("video.pace") + " = yes only when the "
      "server runs with " + c("--decoder-pace") + " and the session's host connected the " + c("pace") + " hook. If the codec list is empty because no card can encode, the server calls the codec-retry "
      "hook once (the card may have appeared after start-up) and then answers " + c("NOTHING_IN_COMMON") + "; the package also refuses a new installation on a machine without a render node.") + \
    note("the bench function (" + c("BENCH_MARK") + ", " + c("bench.mark") + ") is compiled only with " + c("REMOTIX_BENCH") + ". " + c("debian/rules") + " refuses to package if " + c("BENCH_ON") +
         " in " + c("rcp.c") + " is not 0, and " + c("build/build-deb.sh") + " has a check that the installed binary does not contain it. In the installed server " + c("bench.mark") + " is an unknown capability and " +
         c("0x000F") + " is an unknown message type, so it closes the session with " + c("PROTOCOL_ERROR") + ".", "No bench function in the product.")

# ── Credentials ─────────────────────────────────────────────────────────
S6 = p(c("handle_credentials()") + " receives user and password in one message. Both are length-checked (user 1 to 256, password 1 to 1024 bytes), the user must be printable UTF-8, and the "
       "password must contain no zero byte. The password is wiped with " + c("explicit_bzero") + " on every path. Nothing is judged by the server itself: the verdict comes from PAM, through the "
       "helper process, and arrives asynchronously.", lead=True) + \
    steps([
        "<b>The limiter first.</b> " + c("login_reserve()") + " books the attempt against the three levels (below). If the address or the user is banned, or too many attempts are in flight, the reason is set to " +
        c("TOO_MANY_ATTEMPTS") + " and PAM is not asked at all. The table has a bottom: a full table, or a quota of bans, refuses without evicting a ban; only for a key that logged in within the last 30 days is the least valuable ban dropped as a last resort (" + c("lcreate()") + ", logged).",
        "<b>PAM.</b> Otherwise the " + c("ask_verify") + " hook sends the question to the helper and the session waits in " + c("wait-verdict") + ". If the question could not be sent, or there is no helper, "
        "the answer is a refusal that is the server's own (" + c("refusal_is_ours") + "): it goes out as " + c("SESSION_UNSERVABLE") + ", the booking is given back, and it does not count towards a ban, because a ban "
        "for a defect of the server would be the worst possible diagnosis.",
        "<b>The verdict.</b> " + c("rcp_verdict_as()") + " checks four things before it touches " + c("cred_good") + ": the session is in " + c("wait-verdict") + ", a verdict was asked for, the ticket is this "
        "session's own, and it is consumed once. It resolves the attempt in the limiter and, on success, replaces the typed user name by the system's canonical spelling. " + c("rcp_verdict_lost()") +
        " handles the helper dying before it answers.",
        "<b>The wait.</b> " + c("rcp_time()") + " sends the answer only after a floor measured from the arrival of " + c("CREDENTIALS") + ": " + c("FIXED_DELAY") + " = 1000 ms for a success and for refusals "
        "whose reason is not " + c("WRONG_CREDENTIALS") + ", and " + c("REJECT_FLOOR") + " = 2500 ms for a " + c("WRONG_CREDENTIALS") + " refusal, so that a name in the denied list (refused at once) cannot be told "
        "from a wrong password (PAM's own failure delay) by timing. If PAM answers later than the floor, PAM paces the answer.",
        "<b>The answer.</b> Success sends " + c("ADMITTED") + " (empty body) and enters " + c("wait-attach") + ". Failure calls " + c("reject()") + " with the reason: " + c("WRONG_CREDENTIALS") + " for every refusal "
        "of PAM (wrong password, no such user, locked account, denied list), " + c("TOO_MANY_ATTEMPTS") + " for the limiter, " + c("SESSION_UNSERVABLE") + " for a refusal that is the server's. A refusal the host "
        "decides after a PAM yes (the budget, a local session, the desktop that cannot start, including a compositor that is not installed: " + c("session_missing_component()") + ") is kept by " + c("rcp_dismiss_login()") + " until the same floor has passed, then sent as a " + c("FAREWELL") + ". "
        "A connection that was already ADMITTED but is still inside the fixed second (" + c("rcp_admitted_waiting()") + ", state " + c("wait-verdict") + " with no verdict expected, good credentials and no farewell held) can also be given a held " + c("0x10") + " or " + c("0x0E") + " by " + c("wt_dismiss_user_session_over()") + ": it leaves in the place of " + c("ADMITTED") + ".",
    ]) + \
    table(["Level", "Limit of failures", "Window", "Ban", "Constant"], [
        ["user on this key", "5", "5 min", "that user on that key", c("LIMIT") + ", " + c("WINDOW_MS") + " in rcp.c"],
        ["key (IPv4 address, or IPv6 /64)", "20", "5 min", "the key", "idem"],
        ["IPv6 /48", "30", "10 min", "the /48", "idem"],
    ], "«TAB» — The three levels of the login limiter") + \
    p("The ban is progressive per level: " + c("LADDER_MS") + " = 15 minutes, then 1 hour, then 12 hours, and the memory of earlier bans is forgotten after " + c("FORGET_MS") + " = 24 hours without one. A "
      "successful login resets only the failures of that user on that key. At most " + c("MAX_PER_USER_IN_FLIGHT") + " = 2 attempts per user and key are in flight. The table holds " + c("MAX_ATTEMPTS") + " = 256 "
      "entries, of which " + c("BAN_QUOTA") + " = 160 are for bans; once the quota is full, keys that never logged in share a common counter of " + c("UNKNOWN_LIMIT") + " = 5 failures in " +
      c("UNKNOWN_WINDOW_MS") + " = 5 minutes, and keys that logged in within 30 days (" + c("GOOD_KEYS") + " = 64, " + c("GOOD_AGE") + ") always find a place. The ban survives a restart: " + c("save_ban()") +
      " writes it to the file given by " + c("--ban-file") + " and " + c("rcp_ban_load()") + " reads it back, with an absolute time because the process clock is monotonic. The file never holds a typed user name "
      "(an HMAC) and the log writes a name that is not a user of the machine as a short tag. The full description of these defences is the subject of " + rif("Login and its defences") + ".") + \
    warn("RCP.md §4.4 and §4.4-bis speak of a fixed second before the answer; the code's floor for a refused " + c("WRONG_CREDENTIALS") + " is 2.5 s (" + c("REJECT_FLOOR") + "). A client that times the answer "
         "against one second will not see the refusal in time. " + c("prove/check-ban.py") + " judges the code's number and says so in its header.", "The floor of a refusal is 2.5 s.")

# ── ATTACH ──────────────────────────────────────────────────────────────
S7 = p(c("ATTACH") + " asks for a desktop: the canvas the client would like (width, height), the view it will draw into (width, height) and the keyboard layout name. " + c("handle_attach()") +
       " is a sequence of checks, in this order; the first failure ends the session.", lead=True) + \
    table(["#", "Check", "Outcome on failure"], [
        ["1", "Canvas wider than 4096 or taller than 2304 (" + c("RCP_CANVAS_MAX_W") + ", " + c("RCP_CANVAS_MAX_H") + ")", "reduced, logged, not a failure (the declared limit of the product is 3K)"],
        ["2", "Canvas below 320 by 240 (" + c("RCP_CANVAS_MIN_W") + ", " + c("RCP_CANVAS_MIN_H") + ") or an odd side", c("PROTOCOL_ERROR")],
        ["3", "A view with a zero side", c("PROTOCOL_ERROR")],
        ["4", "Layout name malformed (" + c("layout_well_formed()") + ": letters, digits, " + c("_") + ", " + c("-") + ", optionally a parenthesised variant, up to 64 bytes)", c("PROTOCOL_ERROR")],
        ["5", "Layout the machine does not have (" + c("layout_known()") + ": the " + c("layout_exists") + " hook asks XKB; without it a fixed list of twenty is used, logged)", c("SESSION_UNSERVABLE")],
        ["6", "The user already has a local graphical session (" + c("session_local") + " hook)", c("ALREADY_ACTIVE_LOCALLY")],
        ["7", "The slot of this user (" + c("slot_take()") + "): held by another live client", "ghost eviction (" + c("evict_ghost()") + ") if the holder is silent more than " + c("DEFAULT_EVICTION") + " = 15 s, else " + c("ALREADY_ACTIVE_REMOTELY")],
        ["8", "The registry of sessions is full (" + c("RCP_SESSION_CAP") + " = 10 by default, " + c("--session-cap") + "; the declared limit is 8 users)", c("SESSION_UNSERVABLE")],
        ["9", "Canvas against the client's decoder ceiling, then against the stage's own canvas", "reduced or replaced, logged; below 320 by 240 after the ceiling is " + c("SESSION_UNSERVABLE")],
    ], "«TAB» — The order of the checks in handle_attach()") + \
    p("Then " + c("SESSION") + " goes out: one state byte (1 = a new desktop, 2 = the stage was already there, from the " + c("session_resumed") + " hook), the granted canvas (two " + c("u32") + ") and the "
      "desktop name string from the " + c("desktop") + " hook (" + c("unknown") + " if none). The session becomes " + c("active") + ", the first frame is owed as a key frame, " + c("apply_layout()") + " asks the stage "
      "for the layout and the " + c("recanvas") + " hook tells the stage the canvas. The video stream may only open after " + c("SESSION") + ", and the client may open its input stream only after receiving it; "
      "a video stream arriving before " + c("SESSION") + " would be a refused frame with " + c("RCP_VIDEO_BEFORE_SESSION") + ".")

# ── Video, canvas, view, layout ─────────────────────────────────────────
S8 = p("Video is compressed with prediction between frames, so losing a delta frame ruins every following frame until a key frame arrives. The protocol never retransmits a frame; it abandons one "
       "and owes a key frame. The state that decides is " + c("needs_key") + " in the session, set by " + c("key_needed()") + " and cleared by " + c("key_paid()") + ".", lead=True) + \
    table(["Event", "Function", "Effect"], [
        ["First frame after SESSION", c("handle_attach()"), "a key frame is owed"],
        ["A delta frame is abandoned", c("rcp_video_abandon()"), "the stream is reset; a key frame is owed. A key frame is never abandoned"],
        ["A frame is dropped before the wire (no credit, queue rule)", c("rcp_video_discarded_before_wire()") + ", " + c("rcp_video_no_credit()"), "no stream was opened and the frame number was not consumed, so the client sees no gap; the server owes the key frame on its own"],
        ["The client asks", c("handle_key_request()"), "accepted, ignored or deferred by the two gaps (200 ms after a key frame, 100 ms between two accepted requests); a deferred one is served by " + c("rcp_time()")],
        ["Canvas changed", c("rcp_canvas_adapted_now()"), "the next frame must be a key frame at the new size"],
    ], "«TAB» — What makes the server owe a key frame") + \
    p("A delta is refused by " + c("rcp_video_open()") + " with " + c("RCP_VIDEO_NEEDS_KEY") + " while a key frame is owed; asking " + c("rcp_video_needs_key()") + " before encoding avoids the wasted work. "
      "The numbers 1 and above grow by one per frame, so a gap in numbering is what a client reads as loss and answers with " + c("REQUEST_KEY") + " carrying the last number it decoded.") + \
    p("<b>Canvas.</b> " + c("FIT_CANVAS") + " is the only message that changes the canvas. In the " + c("T_FIT_CANVAS") + " case of " + c("drain_at()") + " the request is clamped by " + c("rcp_size_allowed()") +
      " and by the client's " + c("video.max_size") + ", refused if it falls below the minimum, checked against the budget (" + c("canvas_fits") + " hook), passed to the stage (" + c("recanvas") +
      " hook) and left in flight. There is no answer yet: the answer is the first frame at the new size, and if it does not arrive within " + c("RCP_CANVAS_WAIT_MS") + " = 3000 ms the answer is " +
      c("NOT_NOW") + " (" + c("canvas_expires()") + "). " + c("CANVAS") + " carries an outcome (1 = FITTED, 2 = REFUSED), a reason and the canvas in force after the message; one " + c("CANVAS") +
      " is sent for every " + c("FIT_CANVAS") + ".") + \
    table(["Situation", "CANVAS", "Reason code"], [
        ["Below the minimum, or after reduction not allowed", "REFUSED", "2 " + c("SIZE_OUT_OF_RANGE")],
        ["No stage to resize (no " + c("recanvas") + " hook)", "REFUSED", "1 " + c("COMPOSITOR_UNABLE")],
        ["Does not fit the budget; request did not leave; a newer request arrived while this one was still in flight (the newer one goes on); rate over " + c("MC_FIT_CANVAS"), "REFUSED", "3 " + c("NOT_NOW")],
        ["The size is the one already in force", "FITTED", "0"],
        ["The stage adapted, the first frame at the new size arrived", "FITTED", "0"],
    ], "«TAB» — The answers to FIT_CANVAS") + \
    p("<b>View and layout.</b> " + c("VIEW") + " stores the new size of the client's window and logs it; the canvas does not change and nothing is encoded differently, the client rescales. "
      "Any size from 1 by 1 up is legal, odd included; a zero side is a violation. " + c("LAYOUT") + " changes the keyboard layout with the session open: a malformed name is a violation, the layout already in force "
      "asks nothing of the stage, and a layout the machine does not know keeps the old one and does not close the session (at ATTACH it does, because there is no session to save yet).")

# ── Input, clipboard, cursor ────────────────────────────────────────────
S9 = p("The input channel is one client unidirectional stream, opened after " + c("SESSION") + " and kept open. Every message has the common 12 bytes (" + c("u32") + " id and " + c("u64") + " instant, " +
       c("I_COMMON") + ") and a fixed length per type, so a wrong length is known as soon as the 6-byte header has arrived; the buffer is " + c("I_ACCUMULATION") + " = 32 bytes and a megabyte "
       "announced here gets a farewell after six bytes. " + c("rcp_receive_input()") + " refuses bytes before " + c("SESSION") + ", a second input stream, and a type whose high byte is not " + c("0x01") + ".", lead=True) + \
    ul([
        "The id of an input message must be above the last id of the whole channel, not per type. Zero is reserved (it means no input in the frame header). A gap is legitimate because messages over the rate are dropped.",
        "Each type is validated (button and key state must be 0 or 1, a letter must be a Unicode scalar value, a pointer outside the canvas is a violation, except for " + c("CANVAS_GRACE") + " = 1000 ms after a canvas change, when it is clamped to the new canvas), then injected through the five hooks " +
        c("input_pointer") + ", " + c("input_button") + ", " + c("input_wheel") + ", " + c("input_letter") + " and " + c("input_position") + ". Without the hooks the message is valid and not injected, and the session holds.",
        "A valid input message sets the time of the last gesture (" + c("last_input") + "), which is what the 30-minute inactivity clock measures. The control messages " + c("REQUEST_KEY") + " and " + c("PACE") + " do not count as gestures.",
        "A release of a button or key that the server saw pressed is never dropped by the rate gate (" + c("input_admit()") + "), so a key cannot stay stuck down because of a rate limit. When a session ends, held keys and buttons are released (" + c("release_on_detach()") + ").",
        "Details of the injection are in " + rif("Input") + ".",
    ]) + \
    p("<b>Clipboard.</b> Each transfer is a short-lived unidirectional stream opened by the side that sends. " + c("CLIPBOARD_ANNOUNCE") + " says «I have new text» with its byte length (at most " + c("RCP_CLIPBOARD_CAP") +
      " = 1 000 000), " + c("CLIPBOARD_ASK") + " asks for it, " + c("CLIPBOARD_TEXT") + " carries it. " + c("handle_clipboard()") + " rejects a transfer number of 0, a text that was never announced or asked, a length "
      "that does not match the announcement and invalid UTF-8; at most " + c("A_STREAM_MAX") + " = 8 clipboard streams may be open together, and a pending paste request that the client never answers is dropped after " +
      c("CLIPBOARD_BACKSTOP") + " = 8000 ms (" + c("rcp_time()") + "). The first " + c("CLIPBOARD_ASK_FREE") + " = 2 requests for the same announcement are served whatever the rate, because a lost ask would make the next one "
      "a violation. See " + rif("Audio and clipboard") + ".") + \
    p("<b>Cursor.</b> The position of the pointer belongs to the client, which draws the pointer itself; only the shape travels, from the server on the control channel (" + c("rcp_cursor_shape()") + "). It is not sent "
      "before " + c("SESSION") + ". The caller must bring exactly width times height times 4 bytes, and the two sizes are zero together or not at all; both would otherwise make the page close the session, so the server refuses "
      "to send them and logs why.")

# ── Rate limits ─────────────────────────────────────────────────────────
S10 = p("After login every message that passes the checks does work on the single thread of the main loop, shared by all users. A client with a valid password, or a modified page, could send them as fast as "
        "the link carries them, so each kind has a token bucket per session (" + c("msgrate.h") + "). A message over its bucket is consumed without effect and counted; one summary line per " +
        c("MSG_WINDOW_MS") + " = 10 s says how many were dropped, and at most " + c("MSG_LINES_PER_WINDOW") + " = 10 lines of one kind are written per window.", lead=True) + \
    table(["Class", "Messages", "Sustained per second", "Burst"], [
        [c("MC_POINTER"), c("POINTER"), "2000", "4000"],
        [c("MC_BUTTON"), c("BUTTON"), "1000", "2000"],
        [c("MC_WHEEL"), c("WHEEL"), "1000", "2000"],
        [c("MC_LETTER"), c("LETTER"), "2000", "4000"],
        [c("MC_KEY_POSITION"), c("KEY_POSITION"), "2000", "4000"],
        [c("MC_REQUEST_KEY"), c("REQUEST_KEY"), "50", "100"],
        [c("MC_PACE"), c("PACE"), "100", "200"],
        [c("MC_VIEW"), c("VIEW"), "100", "200"],
        [c("MC_LAYOUT"), c("LAYOUT"), "5", "20"],
        [c("MC_FIT_CANVAS"), c("FIT_CANVAS"), "60", "180"],
    ], "«TAB» — The token buckets of a connected client (msg_class_rate())") + \
    ul([
        "The rates are wide on purpose: far above a gaming mouse at 1000 Hz or the automatic typing of a password manager, so no person meets them.",
        "<b>Last one wins.</b> " + c("VIEW") + ", " + c("LAYOUT") + " and " + c("PACE") + " over the rate are not lost: the newest of each kind is kept and applied when the bucket has a token (" + c("lww_apply()") + "), so a stale layout never comes back over a newer one.",
        c("FIT_CANVAS") + " over the rate is answered " + c("CANVAS") + " REFUSED with " + c("NOT_NOW") + ", because the specification wants one answer per request.",
        "Not limited: the handshake messages, " + c("FAREWELL") + " and " + c("TERMINATE_SESSION") + ". The clipboard is outside " + c("msgrate.h") + " classes but has a bucket of its own in " + c("rcp.c") + " (" + c("CLIPBOARD_PER_SECOND") + " = 10, " + c("CLIPBOARD_BURST") + " = 20, " + c("clipboard_over_rate()") + "): a " + c("CLIPBOARD_ANNOUNCE") + " over it is consumed without effect, and so is a " + c("CLIPBOARD_ASK") + " after the first two for the same announcement. The header comment of " + c("msgrate.h") + " still says the clipboard is not limited; the code wins.",
        "The gates are active only in " + c("active") + ", and a kept message that is being applied again is not charged twice (" + c("replaying") + ").",
    ]) + \
    p("<b>Other ceilings.</b> A message is at most 1 MiB; a frame at most 16 MiB; a clipboard transfer 1 000 000 bytes; a cursor shape 256 pixels a side (enforced upstream, and double-checked against the message cap). "
      "Before login the limits of the transport apply (" + rif("Transport") + "): connection caps, handshake rates, the budget of log lines, and the deadlines above. A client that opens more than " + c("A_STREAM_MAX") +
      " clipboard streams loses one that has no message in progress (logged); only when all eight are halfway through a message is it a violation (" + c("clipboard_slot()") + ").")

# ── Clocks ──────────────────────────────────────────────────────────────
S11 = p("Four clocks govern an attached session on the RCP side; the clocks of the transport (idle timeout, PINGs, the dead line) are in " + rif("Transport") + ". Silence and inactivity measure different "
        "things: the first asks whether the client is there, the second whether the user is.", lead=True) + \
    table(["Clock", "Value", "Measured on", "Effect"], [
        ["Silence", c("SILENCE") + " = 30 s", "the last packet decrypted and authenticated from the client (" + c("last_life") + ", set by " + c("rcp_receive()") + " and " + c("rcp_sign_of_life()") + ")",
         "the attached client is detached (state " + c("detached-by-silence") + "): the slot is freed, the held keys released, the connection stays open. If the client speaks again before anyone took the slot it gets it back; otherwise " + c("ALREADY_ACTIVE_REMOTELY")],
        ["Ghost eviction", c("DEFAULT_EVICTION") + " = 15 s (" + c("--eviction-ms") + ")", "the same last packet", "a second client of the same user may take the slot of a holder that has been silent longer than this (never between different users)"],
        ["Inactivity", c("DEFAULT_INACTIVITY") + " = 30 min (" + c("--inactivity-s") + ")", "the last input message (" + c("last_input") + ")", c("INACTIVITY") + ": the client is sent away with a farewell, the desktop stays"],
        ["Abandonment", c("DEFAULT_ABANDON_MS") + " = 60 min (" + c("--abandon-s") + ")", "input, tracked per user in " + c("main.c"), c("SESSION_ABANDONED") + ": the graphical session is closed with its programs, a new login is a new desktop"],
    ], "«TAB» — The clocks of an attached session") + \
    p("The silence clock looks at packets and not at RCP bytes because a user who only reads sends nothing on RCP; counting RCP bytes detached them after thirty seconds while the connection was alive. The clock "
      "stays RCP's own: it does not rely on QUIC's idle timeout, which is negotiated. The price is that a client alive on the wire with a dead page keeps the slot, and the ghost eviction exists to shorten the case of a "
      "client that really vanished. The transport PINGs make the packets arrive on a still scene.") + \
    note("the " + c("rcp_sign_of_life()") + " comment says the PINGs are on only in the credentials window; " + c("keepalive_rule()") + " arms them for every state but " + c("finished") + ". The code wins.", "Comment and code disagree.")

# ── Farewell and reasons ────────────────────────────────────────────────
S12 = p("Whoever closes sends " + c("FAREWELL") + " with a reason before closing the WebTransport session, if the control channel is usable, and repeats the reason as the close code. The reasons are one numbering "
        "shared by " + c("FAREWELL") + ", " + c("REJECTED") + " and the close code (" + c("enum") + " in " + c("rcp.h") + ", RCP.md §8.2). The table says which code in this tree sends each one.", lead=True) + \
    table(["Code", "Name", "Sent from", "When"], [
        [c("0x01"), c("CLOSED_BY_USER"), "client side; recorded by " + c("closed_by_client()"), "the page closed (tab, browser); the server sends no reason of this kind itself"],
        [c("0x02"), c("INACTIVITY"), c("rcp_time()"), "30 minutes without input"],
        [c("0x03"), c("SESSION_ABANDONED"), c("main.c") + " via " + c("wt_dismiss_user()"), "60 minutes without input: the graphical session is closed"],
        [c("0x04"), c("LOCAL_SESSION_PREVAILED"), c("main.c") + ", " + c("wt_watch_locals()"), "the user opened a local graphical session; the remote one is sent away. The child's message that it found a local session (" + c("local_found_by_child()") + ") now arrives <i>before</i> its light close, so the page is told at once"],
        [c("0x05"), c("ALREADY_ACTIVE_LOCALLY"), c("handle_attach()") + ", " + c("main.c"), "a local graphical session already exists (checked at ATTACH, and before the desktop is born)"],
        [c("0x06"), c("BUDGET_FULL"), c("main.c"), "the machine has no composition capacity for another desktop (the budget check after a PAM yes)"],
        [c("0x07"), c("WRONG_CREDENTIALS"), c("reject()"), "PAM refused: wrong password, no such user, locked, denied; always the same sentence in the page"],
        [c("0x08"), c("TOO_MANY_ATTEMPTS"), c("reject()"), "the limiter: the address, the /48 or the user on that key is banned"],
        [c("0x09"), c("NOTHING_IN_COMMON"), c("handle_hello()"), "no codec, depth or audio format in common, or the server cannot encode at all"],
        [c("0x0A"), c("INCOMPATIBLE_VERSION"), c("handle_hello()"), "HELLO version is not 1"],
        [c("0x0B"), c("PROTOCOL_ERROR"), c("dismiss()") + " (50 sites in " + c("rcp.c") + "), " + c("rcp_violation()"), "any breach of RCP; also a client close code outside the range"],
        [c("0x0C"), c("SERVER_CLOSING"), c("main.c") + " via " + c("transport_dismiss_all()"), "the service stops; sent to every session"],
        [c("0x0D"), c("TIMED_OUT"), c("rcp_time()") + ", " + c("webtransport.c"), "a handshake ceiling expired; the control channel did not open in 5 s"],
        [c("0x0E"), c("SESSION_UNSERVABLE"), c("handle_attach()") + ", " + c("main.c") + ", " + c("rcp_receive()"), "the attach is well formed but cannot be served (unknown layout, full registry, compositor or desktop that does not start, out of memory); the detail is in the body. The page counts six routes (" + c("page.html") + ", the comment above its sentence for this reason): unknown layout, slot register full, a canvas not grantable, memory exhausted on the control channel, all stages busy, and, since 18 Nov 2026, the compositor not installed (" + c("delivery_verdict()") + ", XFCE or LXQt without " + c("labwc") + "). " + c("main.c") + " also uses " + c("0x0E") + " for the previous desktop of the user still closing, for a refusal made because logind could not say whether a local session exists (fail-closed), for a failed birth and, since 19 Nov 2026, for a stage refused for the screen scale (" + c("stage_refused_by_child()") + "). The page's sentence stays generic for all of them"],
        [c("0x0F"), c("ALREADY_ACTIVE_REMOTELY"), c("handle_attach()") + ", " + c("speak_again()"), "another live client of the same user holds the slot"],
        [c("0x10"), c("SESSION_TERMINATED"), c("main.c") + " via " + c("wt_dismiss_user_session_over()") + " (in " + c("session_ended_by_child()") + " and " + c("dismiss_child()") + "), " + c("drain_at()") + " for " + c("TERMINATE_SESSION"), "the user logged out of the desktop (or the graphical session ended); the page must not reattach. Connections still waiting for PAM, or whose refusal is held, do not receive it; a connection ADMITTED but inside its fixed second gets it held until the second has passed (" + rif("From password to admission") + ")"],
    ], "«TAB» — The sixteen reasons and who sends them") + \
    p("<b>The two ends of the closing.</b> The WebTransport layer sends the closing capsule after the send queue has drained and a further 500 ms, so the farewell is not lost (" + rif("Transport") + "). A page that closes "
      "sends the code in its own closing capsule, which " + c("closed_by_client()") + " validates (codes " + c("0x01") + " to " + c("0x0F") + ") and passes to " + c("rcp_closed_by_client()") + ", which frees the slot at once rather than waiting for "
      "the transport to finish. A page that sends " + c("FAREWELL") + " first is handled in the " + c("T_FAREWELL") + " case: reason and detail are validated (reason between " + c("0x01") + " and " + c("0x10") + ", detail valid UTF-8), the keys are released, "
      "the slot freed and the session closed with the same reason.") + \
    p("<b>Order for logout.</b> " + c("TERMINATE_SESSION") + " is the only message with which the client ends the graphical session. The server sends " + c("FAREWELL") + " " + c("0x10") + " first and only then calls the " +
      c("terminate_session") + " hook, because when the compositor dies the stage dies with it and a farewell sent afterwards would reach nobody. The same code is sent to the other clients of that user when the desktop's own logout ends the session "
      "(" + c("main.c") + ", through " + c("wt_dismiss_user_session_over()") + ", which skips connections that are still waiting for PAM).") + \
    p("<b>What each kind of fault gets.</b> All the faults below end the RCP session; they differ in what the client is told.", ) + \
    table(["Fault", "Client receives", "Code"], [
        ["Unknown type, server-only type from a client, high byte wrong for the channel", c("FAREWELL"), c("PROTOCOL_ERROR")],
        ["Length that does not match the fields, body above 1 MiB, bad UTF-8, repeated or malformed capability", c("FAREWELL"), c("PROTOCOL_ERROR")],
        ["Message in the wrong state, input before SESSION, a second input stream", c("FAREWELL"), c("PROTOCOL_ERROR")],
        ["A ceiling expired in the handshake", c("FAREWELL"), c("TIMED_OUT")],
        ["A refused login", c("REJECTED"), c("WRONG_CREDENTIALS") + ", " + c("TOO_MANY_ATTEMPTS") + ", " + c("SESSION_UNSERVABLE")],
        ["Out of memory in the control accumulation", c("FAREWELL"), c("SESSION_UNSERVABLE")],
        ["The control channel never opened", "only the close code", c("TIMED_OUT")],
        ["The line is dead (dead line)", "only a QUIC close, no RCP message", "—"],
        ["The service stops", c("FAREWELL"), c("SERVER_CLOSING")],
    ], "«TAB» — What a client is told for each kind of fault")

# ── Departures from RCP.md ──────────────────────────────────────────────
S13 = p("RCP.md is the referee and, where the code differs, the difference is recorded here instead of being hidden. None of the following changes the message formats on the wire.", lead=True) + \
    table(["Subject", "RCP.md and related text", "The code", "Where"], [
        ["Time before a refusal", "a fixed second", c("REJECT_FLOOR") + " = 2.5 s for " + c("WRONG_CREDENTIALS") + " refusals", c("rcp.c")],
        ["Unblocking a banned address", "SPECS.md §4.2 and RCP.md §4.4-bis: an unblock command on the machine", "no command in the package, by the owner's decision of 17 November 2026 (" + c("docs/DECISIONS-11.md") + ": no unblock for the administrator; a ban ends only by time): " + c("command.c") + " and " + c("rcp_unblock()") + " exist, but the unit passes no " + c("--command-socket"), c("debian/remotix.service") + ", " + c("command.c")],
        ["PACE", "code comments cite RCP.md §13; RCP.md has no §13; DECISIONS-11 §11.32 has «ON by default» in its title", "off by default (" + c("decoder_pace") + " false, " + c("rcp_pace_offer()") + "), the unit does not pass " + c("--decoder-pace") + ", so " + c("HERE_I_AM") + " does not declare " + c("video.pace") + " and a " + c("PACE") + " message is a violation", c("main.c") + ", " + c("rcp.c")],
        ["Close code range from the page", "RCP.md §8.2 lists " + c("0x01") + " to " + c("0x10"), c("closed_by_client()") + " accepts " + c("0x01") + " to " + c("0x0F"), c("webtransport.c")],
        ["Number of hooks", c("rcp.h") + ": «three, and no more»", "twenty-nine function pointers in " + c("rcp_hooks"), c("rcp.h")],
        ["Keep-alive PINGs", c("rcp_sign_of_life()") + " comment: only during credentials", "all states except " + c("finished"), c("webtransport.c")],
        ["Limit for the key level of the ban", "the table of RCP.md §4.4-bis still says 12 failed in 5 minutes (and so do comments of " + c("prove/check-ban.py") + ")", "the table of SPECS.md §4.2 and the code say 20 failures in 5 minutes (" + c("LIMIT") + " = 5, 20, 30)", c("rcp.c") + ", " + c("docs/SPECS.md")],
    ], "«TAB» — Where the code departs from RCP.md or its neighbours") + \
    p("RCP.md also contains text that describes the earlier versions of the rules next to the current ones (for example the three-attempt twelve-hour ban of the first form beside the progressive ban of the second). "
      "Read §4.4-bis together with DECISIONS-11 §11.53; when they disagree with " + c("rcp.c") + " the code wins.")

# ── Testing ─────────────────────────────────────────────────────────────
S14 = p("What is known about RCP in this version comes from the checks in " + c("prove/") + ", which drive real browsers through the page, and from the source. The checks were run on Ubuntu 26.04 in the round of 26 and 27 November 2026 on the four virtual machines (GNOME 125 PASS and the known pkexec FAIL, KDE, XFCE and LXQt 126 PASS; " + rif("What was verified and what was not") + "). They exercise the handshake with a real login, attach and reattach, the second connection of the same user (" + c("ALREADY_ACTIVE_REMOTELY") + "), logout (" + c("SESSION_TERMINATED") + "), several users at once, "
        "input, clipboard, the ban (" + c("prove/check-ban.py") + ") and a dropped network.", lead=True) + \
    table(["Area", "Verified by", "Not verified"], [
        ["Handshake, attach, reattach, logout, second device, several users", c("prove/check-base.py") + ", " + c("prove/check-lifecycle.py") + ", " + c("prove/check-multiuser.py") + ", " + c("prove/check-resilience.py") + "; all passed in that round (its only non-green line, on GNOME, was " + c("desktop/users-shell-and-environment") + ", which is not about RCP)", "Messages forged by hand: no check in " + c("prove/") + " sends malformed RCP bytes"],
        ["The address ban, the fixed answer time, the same sentence for wrong password and unknown user, the ban across a restart", c("prove/check-ban.py") + " (on the virtual machine every client is " + c("10.0.2.2") + ", so only that address is banned and unblocked)", "The 12-hour step of the ladder, the quota of bans, the unknown-keys counter, the table full"],
        ["Input and clipboard", c("prove/check-input.py") + ", " + c("prove/check-clipboard.py") + " (Chrome)", "The rate gates under load; the clipboard with Firefox"],
        ["Reasons " + c("0x03") + ", " + c("0x04") + ", " + c("0x06") + ", " + c("0x0E"), "partly: the abandonment and inactivity mechanisms at short values in " + c("check-resilience.py") + " (check " + c("clocks") + "); " + c("0x04") + " by " + c("prove/check-prelocal.py") + " (the page is told " + c("0x04") + " when the local-login hook closes the desktop, the login simulated; by the owner at the real login screen of the four live images, 27 Nov 2026); " + c("0x0E") + " for a full cap by " + c("session-cap") + " in " + c("prove/check-desktop.py"), "No check is written to provoke the budget refusal (" + c("BUDGET_FULL") + "); " + c("prove/check-media.py") + " only reads the journal for one. The routes of " + c("0x0E") + " added on 18-19 Nov 2026 (compositor not installed, stage refused for the scale) have no check of their own; " + c("0x05") + " was not established"],
        ["Strictness: every wrong length, state or channel", "—", "The fuzz harnesses and the wire validator named in code comments are not in this tree"],
    ], "«TAB» — What was verified about RCP and what was not") + \
    p("A consequence for a maintainer: the strict parser has been read carefully for this manual and run only against the page, which sends well-formed messages. Changing a message body means changing the handler, the entry in " +
      c("measure_fields()") + ", the page, and RCP.md together.")

CHAPTER = ("The RCP/1 protocol", [
    ("RCP/1 in one page and where its specification lives", S1),
    ("Message map: every type and the function that handles it", S2),
    ("Framing and the rigor rule as implemented", S3),
    ("The handshake step by step", S4),
    ("HELLO, HERE_I_AM and capability negotiation", S5),
    ("CREDENTIALS, the verdict and the fixed second", S6),
    ("ATTACH and SESSION as implemented", S7),
    ("Key frames, canvas, view and layout messages", S8),
    ("Input, clipboard and cursor messages", S9),
    ("Rate limits on a connected client", S10),
    ("Clocks of an attached session", S11),
    ("FAREWELL, REJECTED and the sixteen reasons", S12),
    ("Where the code departs from RCP.md", S13),
    ("What was verified about RCP", S14),
])
