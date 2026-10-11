from build import c, code, note, p, rif, table

# ── Main C structures ───────────────────────────────────────────────────
S1 = p("This appendix collects the central data structures of the server, with the file that defines them and where "
       "they are covered. They are the contracts that run through REMOTIX. Structures private to one file are listed only "
       "when a maintainer will meet them while following a frame, an input or a farewell; the chapters named in the "
       "last column describe them in depth.", lead=True) + \
    table(["Structure", "Defined in", "Role", "Covered in"], [
        "Transport and protocol",
        [c("struct trasporto") + " (transport)", c("trasporto.c"), "The UDP socket, the list of connections, the connection-id map, the "
         "stateless-reset secret, the PAM helper handed to every session", rif("A connection from first packet to close")],
        [c("connessione") + " (connection)", c("trasporto.c"), "One QUIC connection: " + c("ngtcp2_conn") + ", " + c("SSL") + ", local and "
         "remote address, " + c("provenienza") + " (origin, for the log), its " + c("wt") + ", counters of discarded client "
         "datagrams",
         rif("QUIC transport parameters")],
        [c("entry_cid") + " (CID entry)", c("trasporto.c"), "One entry of the connection-id map: several ids lead to the same connection",
         rif("QUIC transport parameters")],
        [c("struct wt"), c("webtransport.c"), "The WebTransport session of a connection: nghttp3, the session stream id, "
         "stream classification, send queue, datagram queue, clocks, the " + c("rcp_session") + " it hosts",
         rif("The WebTransport layer")],
        [c("stream_judgment") + " (stream verdict)", c("webtransport.c"), "A client stream and its class (" + c("enum genere")
         + ", kind): undecided, "
         "control, HTTP/3, input, clipboard, lawful-unserved, violation", rif("The WebTransport layer")],
        [c("exit") + " (outgoing item)", c("webtransport.c"), "One element of the send queue: bytes, offset, FIN, and the two "
         "states " + c("consegnato") + " (delivered) / " + c("morto") + " (dead)", rif("Streams versus datagrams")],
        [c("richiesta") + " (request)", c("webtransport.c"), "An HTTP/3 request seen by nghttp3: method, " + c(":protocol") + ", path",
         rif("The WebTransport layer")],
        [c("struct rcp_session"), c("rcp.c"), "One RCP/1 session: state, provenance, negotiated codec/depth/audio/level, "
         "canvas, view, attach slot, video counters and key-frame debt, input and clipboard accumulators, clocks",
         rif("Handshake deadlines and session states")],
        [c("rcp_hooks") + " (RCP hooks)", c("rcp.h"), "The hooks through which " + c("rcp.c") + " asks its host to act: send, "
         "close, log, verify (synchronous and asynchronous), four video hooks, six input hooks, canvas, layout (exists, "
         "apply), stage size, local session, five clipboard hooks, logout, resumed/desktop", rif("RCP: the protocol model")],
        [c("scrittore") + ", " + c("lettore") + " (writer, reader)", c("rcp.c"), "Big-endian writer and reader with an overflow flag; every "
         "body is built and parsed through them", rif("RCP: elementary types and framing")],
        [c("certificati") + " (certificates)", c("certificati.h"), "Paths of the two certificates and their marker files, the session fingerprint "
         "in base64 and hex, expiry, rotation count", rif("TLS and the two certificates")],
        [c("struct pagina") + ", " + c("cliente") + " (page, client)", c("pagina.c"), "The TCP listener and one HTTPS client being served",
         rif("The page server")],
        "Processes and sessions",
        [c("struct ponte") + " (bridge)", c("main.c"), "What the parent hands to its callbacks: the transport and the table of "
         "children", "chapter «Overall architecture»"],
        [c("struct figli") + ", " + c("struct figlio") + " (children, child)", c("figlio.c"), "The table of per-user children and one child: uid, "
         "pid, socket, serial number, reassembly buffers for frames, cursor and clipboard", "chapter «Startup and life cycle»"],
        [c("struct aiutante") + " (helper)", c("aiutante.c"), "The PAM helper process and the tickets in flight", rif("Credentials, the fixed delay and the address ban")],
        [c("struct sentinella") + " (sentinel)", c("sentinella.c"), "Watches local graphical sessions on behalf of the users served",
         "chapter «Overall architecture»"],
        [c("struct comando") + " (command)", c("comando.c"), "The 0600 Unix socket of the unlock command", rif("Credentials, the fixed delay and the address ban")],
        [c("FindingAgainDesktop") + " (found-again desktop)", c("ritrovo.h"), "A live REMOTIX desktop found at start-up with no child holding it",
         "chapter «Startup and life cycle»"],
        [c("struct budget_count") + ", " + c("struct inquilino") + " (budget account, tenant)", c("budget.h") + ", "
         + c("budget.c"), "The composition budget: who is inside, and the verdict on a newcomer", "chapter «Quality, degradation and budget»"],
        [c("DesktopSession") + ", " + c("SessionState") + ", " + c("SessionMonitor"), c("sessione.h"), "Which desktop, "
         "the health of a started session, the virtual monitor read back (session desktop, state, monitor)", "chapter «The four desktops»"],
        "Capture, encoding, input, audio",
        [c("Cattura") + ", " + c("CaptureFrameInfo") + ", " + c("CaptureDelivery") + ", " + c("CaptureCounts"),
         c("cattura.h"), "The capture: the PipeWire stream, one captured frame with its damage, the buffer type asked and "
         "declared (delivery), the counters", "chapter «Screen capture per compositor»"],
        [c("MutterSession") + ", " + c("KwinSession") + ", " + c("WlrStage") + ", " + c("WlrFrame"),
         c("mutter.h") + ", " + c("kwin.h") + ", " + c("wlroots.h"), "The stage (" + c("stage") + ") of each compositor family; " + c("WlrFrame") + " is one labwc frame",
         "chapter «Screen capture per compositor»"],
        [c("CursorShape") + ", " + c("Cursore") + " (cursor shape, cursor)", c("cursore.h"), "A cursor shape (size, hotspot, premultiplied BGRA, "
         "series number) on its way to " + c("CURSOR_SHAPE"), rif("Cursor shape and clipboard messages")],
        [c("Codificatore") + ", " + c("CodificatoreRichiesta") + ", " + c("EncoderFrame") + ", "
         + c("EncoderConfession") + ", " + c("EncoderSurface"), c("codificatore.h"), "The encoder ("
         + c("Codificatore") + "), what is asked of it (request), one encoded frame (with re-encodes against the 16 MiB "
         "cap), what it declares about itself (confession), a GPU surface", "chapter «Video encoding»"],
        [c("VaDirect") + ", " + c("VaDirectRequest") + ", " + c("VulkanVideo") + ", " + c("VulkanVideoRequest"),
         c("vadiretta.h") + ", " + c("vulkanvideo.h"), "The two GPU encoders: VA-API used directly (" + c("VaDirect") + ", direct VA), and Vulkan Video",
         "chapter «Video encoding»"],
        [c("BitWriter") + " (bit writer)", c("scrittore_bit.h"), "Bit writer for SPS/PPS/slice headers, remembers an overflow",
         "chapter «Video encoding»"],
        [c("Input") + ", " + c("Tastiera") + ", " + c("WlrInput"), c("input.h") + ", " + c("tastiera.h") + ", "
         + c("wlr_input.h"), "Injection of the five input messages; letters to key positions (" + c("Tastiera") + ", keyboard); the wlroots "
         "transport",
         "chapter «Input»"],
        [c("Appunti") + ", " + c("ClipboardKde"), c("appunti.h") + ", " + c("appunti_kde.h"), "The clipboard ("
         + c("clipboard") + ") seam, and its KDE implementation", "chapter «Audio and clipboard»"],
        [c("suono") + ", " + c("audio_cod"), c("suono.h") + ", " + c("audio.h"), "The virtual sink and its monitor "
         "capture (" + c("sound") + ", sound); the Opus/PCM encoder", "chapter «Audio and clipboard»"],
    ], "«TAB» — The main data structures")

# ── RCP messages ────────────────────────────────────────────────────────
S2 = p("All RCP/1 message types in one table, by number. Bodies use the elementary types of " + rif("RCP: elementary "
       "types and framing") + "; the length column is the body length without the 6 framing bytes.", lead=True) + \
    table(["Type", "Name", "Direction", "Body fields", "Length", "Section"], [
        "Control channel (high byte 0x00) — the first bidirectional stream",
        [c("0x0001"), c("HELLO") + " (hello)", "client → server", c("u16 version") + ", list of (string name, string value)", "variable",
         rif("HELLO and HERE_I_AM: capability negotiation")],
        [c("0x0002"), c("HERE_I_AM") + " (here I am)", "server → client", "same as " + c("HELLO"), "variable", rif("HELLO and HERE_I_AM: capability negotiation")],
        [c("0x0003"), c("CREDENTIALS") + " (credentials)", "client → server", c("string user") + " (1–256), " + c("string password") + " (1–1024)",
         "variable", rif("Credentials, the fixed delay and the address ban")],
        [c("0x0004"), c("ADMITTED") + " (admitted)", "server → client", "—", "0", rif("Credentials, the fixed delay and the address ban")],
        [c("0x0005"), c("REJECTED") + " (refused)", "server → client", c("u8 reason"), "1", rif("Credentials, the fixed delay and the address ban")],
        [c("0x0006"), c("ATTACH") + " (attach)", "client → server", c("u32 canvas_width, canvas_height, view_width, view_height")
         + ", " + c("string layout") + " (1–64, XKB form)", "≥ 19", rif("ATTACH and SESSION: attaching to a desktop")],
        [c("0x0007"), c("SESSION") + " (session)", "server → client", c("u8 state") + " (1 new, 2 resumed), " + c("u32 canvas_width, canvas_height")
         + ", " + c("string desktop"), "≥ 11", rif("ATTACH and SESSION: attaching to a desktop")],
        [c("0x0008"), c("VIEW") + " (view)", "client → server", c("u32 width, altezza"), "8", rif("Canvas changes: FIT_CANVAS, CANVAS and VIEW")],
        [c("0x0009"), c("LAYOUT") + " (layout)", "client → server", c("string layout") + " (1–64)", "≥ 3", rif("Canvas changes: FIT_CANVAS, CANVAS and VIEW")],
        [c("0x000A"), c("CURSOR_SHAPE") + " (cursor shape)", "server → client", c("u16 width, altezza") + ", " + c("i16 hot_x, hot_y")
         + ", image", "8 + w·h·4", rif("Cursor shape and clipboard messages")],
        [c("0x000B"), c("FIT_CANVAS") + " (fit the canvas)", "client → server", c("u32 width, altezza"), "8", rif("Canvas changes: FIT_CANVAS, CANVAS and VIEW")],
        [c("0x000C"), c("FAREWELL") + " (farewell)", "both", c("u8 reason") + ", " + c("string detail"), "≥ 3", rif("RCP: the farewell")],
        [c("0x000D"), c("REQUEST_KEY") + " (request a key frame)", "client → server", c("u32 last_number"), "4", rif("Key frames and abandonment")],
        [c("0x000E"), c("CANVAS") + " (canvas)", "server → client", c("u8 outcome, u8 reason, u32 canvas_width, u32 canvas_height"), "10",
         rif("Canvas changes: FIT_CANVAS, CANVAS and VIEW")],
        [c("0x000F"), c("BENCH_MARK") + " (bench marker)", "client → server", c("u32 id, u32 color, u32 delay_ms"), "12", rif("The bench marker: BENCH_MARK")],
        [c("0x0010"), c("BENCH_OUTCOME") + " (bench outcome)", "server → client", c("u32 id, u8 outcome, u8 reason, u64 instant"), "14", rif("The bench marker: BENCH_MARK")],
        [c("0x0011"), c("TERMINATE_SESSION") + " (end the session)", "client → server", "—", "0", rif("TERMINATE_SESSION: logging out")],
        "Input channel (high byte 0x01) — one unidirectional stream from the client; common prefix " + c("u32 id, u64 instant"),
        [c("0x0101"), c("POINTER") + " (pointer)", "client → server", "prefix + " + c("u32 x, u32 y"), "20", rif("RCP input messages")],
        [c("0x0102"), c("BUTTON") + " (button)", "client → server", "prefix + " + c("u16 code, u8 pressed"), "15", rif("RCP input messages")],
        [c("0x0103"), c("WHEEL") + " (wheel)", "client → server", "prefix + " + c("i32 axis_x, i32 axis_y"), "20", rif("RCP input messages")],
        [c("0x0104"), c("LETTER") + " (letter)", "client → server", "prefix + " + c("u32 character"), "16", rif("RCP input messages")],
        [c("0x0105"), c("KEY_POSITION") + " (key position)", "client → server", "prefix + " + c("u16 code, u8 pressed"), "15", rif("RCP input messages")],
        "Clipboard channel (high byte 0x02) — unidirectional streams, one per message",
        [c("0x0201"), c("CLIPBOARD_ANNOUNCE") + " (clipboard announce)", "both", c("u32 transfer, u32 length"), "8", rif("Cursor shape and clipboard messages")],
        [c("0x0202"), c("CLIPBOARD_ASK") + " (clipboard ask)", "both", c("u32 transfer"), "4", rif("Cursor shape and clipboard messages")],
        [c("0x0203"), c("CLIPBOARD_TEXT") + " (clipboard text)", "both", c("u32 transfer") + ", UTF-8 to the end of the message", "4 + n "
         "(n ≤ 1 000 000)", rif("Cursor shape and clipboard messages")],
        "Video (high byte 0x03) — one unidirectional stream per frame, unframed",
        [c("0x0301"), "key frame", "server → client", "28-byte header + access unit", "to FIN", rif("RCP: the video frame")],
        [c("0x0302"), "delta frame", "server → client", "28-byte header + access unit", "to FIN", rif("RCP: the video frame")],
        "Audio (high byte 0x04) — datagrams only",
        [c("0x0401"), "audio block", "server → client", "12-byte header + one Opus packet or 5 ms of PCM", "datagram",
         rif("Audio datagrams")],
    ], "«TAB» — Index of RCP/1 messages") + \
    p("Field names are those of RCP.md: " + c("version") + " version, " + c("user") + " user, " + c("password")
      + " password, " + c("canvas") + " canvas, " + c("view") + " view, " + c("width") + "/" + c("height")
      + " width/height, " + c("layout") + " keyboard layout, " + c("state") + " state, " + c("reason")
      + " reason, " + c("detail") + " detail (for the log), " + c("hot_x") + "/" + c("hot_y") + " hotspot, "
      + c("last_number") + " last decoded frame number, " + c("outcome") + " outcome, " + c("color") + " colour, "
      + c("delay_ms") + " delay, " + c("instant") + " timestamp in microseconds, " + c("code") + " code, "
      + c("pressed") + " pressed, " + c("axis_x") + "/" + c("axis_y") + " axis, " + c("character")
      + " Unicode character, " + c("transfer") + " transfer id, " + c("length") + " length.") + \
    note("the page never sends " + c("VIEW") + ", " + c("LAYOUT") + " or " + c("BENCH_MARK") + " today; the server "
         "serves all three. " + c("FIT_CANVAS") + " is sent once per attach, and repeated once after a " + c("NOT_NOW")
         + " refusal.", "Defined but unused by the page.")

# ── Sub-codes ───────────────────────────────────────────────────────────
S3 = p("The small enumerations that travel inside message bodies.", lead=True) + \
    table(["Code", "Name", "Meaning"], [
        "Disconnect reasons — " + c("CONGEDO.motivo") + ", " + c("RESPINTO.motivo") + ", WebTransport close code",
        [c("0x01"), c("CLOSED_BY_USER"), "<i>closed by the user</i>: the client was closed; the session stays"],
        [c("0x02"), c("INACTIVITY"), "<i>inactivity</i>: 30 minutes without RCP traffic from the client"],
        [c("0x03"), c("SESSION_ABANDONED"), "<i>session abandoned</i>: 60 minutes without input: the session is closed"],
        [c("0x04"), c("LOCAL_SESSION_PREVAILED"), "<i>local session prevailed</i>: a local graphical session took over"],
        [c("0x05"), c("ALREADY_ACTIVE_LOCALLY"), "<i>already active locally</i>: a local graphical session already exists"],
        [c("0x06"), c("BUDGET_FULL"), "<i>budget full</i>: no composition capacity left"],
        [c("0x07"), c("WRONG_CREDENTIALS"), "<i>wrong credentials</i>: authentication failed"],
        [c("0x08"), c("TOO_MANY_ATTEMPTS"), "<i>too many attempts</i>: address banned"],
        [c("0x09"), c("NOTHING_IN_COMMON"), "<i>nothing in common</i>: no common codec, depth or audio codec"],
        [c("0x0A"), c("INCOMPATIBLE_VERSION"), "<i>incompatible version</i>: version mismatch"],
        [c("0x0B"), c("PROTOCOL_ERROR"), "<i>protocol error</i>: violation of RCP/1"],
        [c("0x0C"), c("SERVER_CLOSING"), "<i>server closing</i>: server shutting down"],
        [c("0x0D"), c("TIMED_OUT"), "<i>time expired</i>: a handshake ceiling expired"],
        [c("0x0E"), c("SESSION_UNSERVABLE"), "<i>session not servable</i>: well-formed attach that cannot be served"],
        [c("0x0F"), c("ALREADY_ACTIVE_REMOTELY"), "<i>already active remotely</i>: another live client of the user is attached to the session"],
        [c("0x10"), c("SESSION_TERMINATED"), "<i>session ended</i>: the user logged out"],
        c("TELA.esito") + " / " + c("TELA.motivo"),
        [c("1") + " / " + c("0"), c("FITTED"), "<i>fitted</i>: the canvas changed (or already had that size)"],
        [c("2") + " / " + c("1"), c("COMPOSITOR_UNABLE"), "<i>compositor incapable</i>: the compositor cannot resize"],
        [c("2") + " / " + c("2"), c("SIZE_OUT_OF_RANGE"), "<i>size out of limits</i>: below 320×240, also when the reduction to the client's decoder cap ("
         + c("video.max_size") + ") would fall below it"],
        [c("2") + " / " + c("3"), c("NOT_NOW"), "<i>not now</i>: the stage did not reach the size in time"],
        c("BANCO_ESITO.esito") + " / " + c("BANCO_ESITO.motivo"),
        [c("1") + " / " + c("0"), c("ACCEPTED"), "<i>accepted</i>: never produced by the current server"],
        [c("2") + " / " + c("1"), c("FEATURE_OFF"), "<i>function off</i>: the bench function is off (always, in the product)"],
        [c("2") + " / " + c("2"), c("DELAY_OUT_OF_RANGE"), "<i>delay out of limits</i>: " + c("delay_ms") + " above 10 000"],
        c("SESSIONE.stato"),
        [c("1"), c("NEW"), "<i>new</i>: the stage was born for this login"],
        [c("2"), c("RESUMED"), "<i>resumed</i>: the stage existed before PAM admitted the user"],
        "Video " + c("codec") + " (frame header)",
        [c("1"), "HEVC", "negotiated as " + c("hevc")],
        [c("2"), "AV1", "retired on 20 August 2026; the number is never reused"],
        [c("3"), "H.264", "negotiated as " + c("h264") + " (" + c("RCP_CODEC_VIDEO_MAX") + ")"],
        "Audio " + c("codec") + " (datagram header)",
        [c("1"), "Opus", "48 kHz stereo, 20 ms"],
        [c("2"), "PCM", "s16 little-endian, 48 kHz stereo, 5 ms"],
    ], "«TAB» — Sub-codes carried in bodies")

# ── Headers ─────────────────────────────────────────────────────────────
S4 = p("Every layout a maintainer can meet on the wire, from the outside in. All RCP integers are big-endian; the "
       "WebTransport prefixes are QUIC variable-length integers.", lead=True) + \
    code("""Server-opened unidirectional stream (video, clipboard)
  varint 0x54 (40 54) · varint session id · RCP payload
Client-opened unidirectional stream (input, clipboard)
  varint 0x54 (40 54) · varint session id · RCP payload
Client-opened bidirectional stream (control)
  varint 0x41 (40 41) · varint session id · RCP payload
HTTP datagram (audio)
  varint quarter stream id of the session · RCP audio datagram""", "text", "WebTransport framing around RCP") + \
    code("""RCP framed message (control, input, clipboard)
 0      2        6
 │ type │ length │ body (length bytes; 6 + length <= 1 MiB)
 │ u16  │ u32    │

RCP video frame (unframed, ends with FIN; RESET_STREAM = incomplete)
 0      2      4      8      12     16      24     28
 │ type │codec │width │height│number│instant│input │ access unit …
 │ u16  │ u16  │ u32  │ u32  │ u32  │ u64   │ u32  │

RCP audio datagram
 0      2      4        12
 │ type │codec │instant │ one Opus packet, or 960 bytes of PCM
 │ u16  │ u16  │ u64    │""", "text", "RCP payloads") + \
    p("In the RCP payloads, " + c("type") + " is the message type, " + c("number") + " the frame number, "
      + c("instant") + " a timestamp in microseconds and " + c("input") + " the id of the last input injected before the "
      "capture (0 if none).") + \
    code("""CLOSE_WEBTRANSPORT_SESSION, as REMOTIX writes it on the CONNECT stream
  00        HTTP/3 frame type DATA
  07        frame length
  68 43     capsule type 0x2843 (2-byte varint)
  04        capsule length
  00 00 00 mm   u32 application error code = RCP reason""", "text", "The closing capsule") + \
    code("""Parent <-> child (SOCK_SEQPACKET, native struct layout, figlio.c)
  struct testa
   ├── u8[4]  magic            'F','I','G','1'
   ├── u16    type             MSG_*
   ├── u16    version         CHILD_VERSION = 1
   ├── u64    matricola        the child's serial number
   ├── u32    declared_uid   who the sender believes the child is
   └── u32    byte             body bytes after this header
  body: one struct corpo_* ; frames, cursors and clipboard text travel in
        pieces of at most MAX_PIECE = 32768 bytes""", "text", "The parent–child envelope") + \
    table(["Type", "Name", "Direction", "Carries"], [
        [c("1"), c("MSG_CHI_SEI") + " (who are you)", "parent → child", "the identity question at birth"],
        [c("2"), c("MSG_SHUT_DOWN") + " (shut down)", "parent → child", "shut down"],
        [c("3"), c("MSG_RESEND_STAGE") + " (resend the stage)", "parent → child", "report the stage again"],
        [c("4"), c("MSG_VIDEO"), "parent → child", "codec, depth, level; «capture, and make it a key frame»"],
        [c("5"), c("MSG_INPUT"), "parent → child", "one input action (" + c("FIGLI_INPUT_*") + ": pointer, button, wheel, "
         "letter, key position, release all, re-canvas, terminate)"],
        [c("6"), c("MSG_LAYOUT") + " (layout)", "parent → child", "the keyboard layout to apply"],
        [c("7"), c("MSG_AUDIO"), "parent → child", "the negotiated audio codec"],
        [c("8"), c("MSG_CLIPBOARD_OFFER") + " (clipboard offer)", "parent → child", "the client has text (without the text)"],
        [c("9"), c("MSG_CLIPBOARD_FROM_CLIENT") + " (clipboard from the client)", "parent → child", "the client's text, in pieces, for a paste"],
        [c("10"), c("MSG_INTRO") + " (I am)", "child → parent", "the child's credentials (uid, gid, …)"],
        [c("11"), c("MSG_STAGE") + " (stage)", "child → parent", "the stage exists"],
        [c("12"), c("MSG_FRAME") + " (frame)", "child → parent", "an encoded frame, in pieces"],
        [c("13"), c("MSG_CURSOR") + " (cursor)", "child → parent", "a cursor shape, in pieces"],
        [c("14"), c("MSG_CANVAS") + " (canvas)", "child → parent", "canvas asked and canvas obtained (0×0 = failed)"],
        [c("15"), c("MSG_SESSION_FINISHED") + " (session over)", "child → parent", "the user logged out from the desktop"],
        [c("16"), c("MSG_BLOCK") + " (block)", "child → parent", "one encoded audio block"],
        [c("17"), c("MSG_CLIPBOARD_FROM_SESSION") + " (clipboard from the session)", "child → parent", "text copied in the session, in pieces"],
        [c("18"), c("MSG_CLIPBOARD_REQUEST") + " (clipboard wanted)", "child → parent", "someone in the session is pasting"],
    ], "«TAB» — Parent–child messages (figlio.c)") + \
    code("""Parent -> helper   struct richiesta { u64 pratica; char utente[257]; char parola[1025]; char rhost[64]; }
Helper -> parent   struct risposta  { u64 pratica; u8 outcome; }      outcome 1 and only 1 = admitted
Unlock socket      one text line:  UNBLOCK <address>  ->  REMOVED <address> | NOT-BANNED <address>
                                   PING               ->  PONG
                                   anything else      ->  NOT-UNDERSTOOD <line>""", "text", "PAM helper and unlock command") + \
    p("In the helper messages, " + c("pratica") + " is the ticket number that pairs answer and request, " + c("user")
      + " the user, " + c("password") + " the password, " + c("rhost") + " the client address for " + c("PAM_RHOST")
      + " and " + c("outcome") + " the outcome. On the unlock socket, " + c("UNBLOCK") + " means unlock, " + c("REMOVED")
      + " lifted, " + c("NOT-BANNED") + " not banned and " + c("NOT-UNDERSTOOD") + " not understood.") + \
    p("The recording format of the benches (" + c("RCPREG") + " magic " + c("0x00 0x03") + ") is in "
      + rif("Testing against the specification") + ".")

# ── Constants ───────────────────────────────────────────────────────────
S5 = p("The protocol and transport constants a maintainer is most likely to look for, with their value and home. "
       "Each lives in one place; where a number was once copied by hand into several files, the copies diverged.",
       lead=True) + \
    table(["Constant", "Value", "File", "Meaning"], [
        "Protocol",
        [c("RCP_VERSION"), "1", c("rcp.h"), "the major version; also in the path " + c("/rcp/1")],
        [c("MAX_MESSAGE") + " / " + c("MAX_BODY"), "1 MiB / 1 MiB − 6", c("rcp.c"), "framed message cap, framing included"],
        [c("V_HEADER"), "28", c("rcp.c"), "video header bytes"],
        [c("V_CAP"), "16 MiB", c("rcp.c"), "largest frame"],
        [c("V_GRACE_KEY"), "200 ms", c("rcp.c"), "duplicate key requests may be ignored"],
        [c("RCP_CODEC_VIDEO_MAX"), "3", c("rcp.h"), "highest video codec number"],
        [c("RCP_CANVAS_MIN_W") + " × " + c("RCP_CANVAS_MIN_H"), "320 × 240", c("rcp.h"), "smallest canvas"],
        [c("RCP_CANVAS_MAX_W") + " × " + c("RCP_CANVAS_MAX_H"), "4096 × 2304", c("rcp.h"), "largest canvas (since 1 Oct 2026)"],
        [c("RCP_CANVAS_WAIT_MS"), "3000", c("rcp.h"), "answer " + c("FIT_CANVAS") + " by then"],
        [c("RCP_CANVAS_RETRY_MS") + " / " + c("RCP_CANVAS_RETRY_MAX_MS"), "500 / 8000", c("rcp.h"), "recall a stray stage, doubling"],
        [c("CANVAS_GRACE"), "1000 ms", c("rcp.c"), "old coordinates accepted after a canvas change"],
        [c("RCP_CLIPBOARD_CAP"), "1 000 000", c("rcp.h"), "clipboard text cap"],
        [c("A_STREAM_MAX") + " / " + c("CLIPBOARD_BACKSTOP"), "8 / 8000 ms", c("rcp.c"), "clipboard streams kept; paste-request deadline"],
        [c("I_ACCUMULATION"), "32", c("rcp.c"), "input accumulator bytes"],
        [c("BANCO_ACCESO") + " / " + c("BENCH_DELAY_MAX"), "0 / 10 000 ms", c("rcp.c"), "bench function off; delay limit"],
        "Handshake, ban and clocks",
        [c("CAP_HELLO") + " / " + c("CAP_CREDENTIALS") + " / " + c("CAP_ATTACH"), "5 / 60 / 10 s", c("rcp.c"), "handshake ceilings"],
        [c("WT_CAP_CHANNEL_NS"), "5 s", c("webtransport.c"), "session open → control channel"],
        [c("FIXED_DELAY"), "1000 ms", c("rcp.c"), "fixed delay before answering credentials"],
        [c("VERDICT_CAP") + " / " + c("EXPIRY_MS"), "12 / 8 s", c("rcp.c") + " / " + c("aiutante.c"), "PAM verdict deadlines"],
        [c("THRESHOLD") + " / " + c("WINDOW") + " / " + c("BAN_DURATION"), "3 / 5 min / 12 h", c("rcp.c"), "address ban"],
        [c("SILENZIO"), "30 000 ms", c("rcp.c"), "silence detaches"],
        [c("DEFAULT_EVICTION"), "15 000 ms", c("rcp.c"), "ghost eviction"],
        [c("DEFAULT_INACTIVITY"), "30 min", c("rcp.c"), "inactivity farewell " + c("0x02")],
        [c("DEFAULT_ABANDON_MS"), "60 min", c("main.c"), "abandonment " + c("0x03")],
        [c("RCP_SESSION_CAP"), "10", c("rcp.h"), "users served, default of " + c("--session-cap")],
        "Transport",
        [c("DEFAULT_PORT"), "7447", c("main.c"), "UDP and TCP"],
        [c("IDLE_MS"), "30 000", c("trasporto.c"), c("max_idle_timeout")],
        [c("SCIDLEN"), "18", c("trasporto.c"), "server connection id bytes"],
        [c("MAX_PACKETS_PER_ROUND"), "64", c("trasporto.c"), "packets written per pass"],
        [c("WT_KEEPALIVE_NS"), "10 s", c("webtransport.c"), "PING interval (half the dead-line silence when on)"],
        [c("WT_LM_STALL_MS") + " / " + c("WT_LM_SILENCE_S"), "5000 ms / 10 s", c("webtransport.h"), "dead-line defaults"],
        [c("WT_CLEAR_THRESHOLD_MS"), "100", c("webtransport.h"), "stale-delta threshold"],
        [c("WT_RATE_SLOTS"), "2", c("webtransport.c"), "pace regulator"],
        [c("WT_UNI_RESERVE") + " / " + c("WT_INFLIGHT_MAX"), "2 / 32", c("webtransport.c"), "streams left to the client; frames in flight"],
        [c("WT_DGRAM_BYTE") + " / " + c("WT_DGRAM_MAX"), "1024 / 8", c("webtransport.c"), "datagram size; queued blocks"],
        [c("WT_CLOSE_WAIT_NS"), "500 ms", c("webtransport.c"), "wait before the closing capsule"],
        [c("WT_CAPSULE_MAX"), "1028", c("webtransport.c"), "incoming capsule cap"],
        [c("CERT_DAYS_PAGE") + " / " + c("CERT_DAYS_SESSION") + " / " + c("CERT_MARGIN_DAYS"), "365 / 13 / 2",
         c("certificati.h"), "certificate validity and rotation margin"],
    ], "«TAB» — Protocol and transport constants")

CHAPTER = ("Appendix A — Data structures and messages", [
    ("The main C structures", S1),
    ("Index of RCP/1 messages", S2),
    ("Sub-codes carried in RCP bodies", S3),
    ("Stream, datagram and IPC layouts", S4),
    ("Protocol and transport constants", S5),
])
