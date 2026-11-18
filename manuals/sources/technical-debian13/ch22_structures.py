from build import c, note, p, rif, sysf, table, warn

# ── The main C structures ────────────────────────────────────────────────
S1 = p("The central data structures of the server, with the file that defines them and the chapter that explains them. "
       "They are the contracts that run through REMOTIX. Structures private to one file are listed only when a maintainer "
       "will meet them while following a login, a child or a desktop found again.", lead=True) + \
    table(["Structure", "Defined in", "Role", "Covered in"], [
        "Processes and the closed list",
        [c("struct rootside_options"), c("rootside.h"), "What " + c("main()") + " hands the root side: the two sockets, the "
         "network user's uid and gid, the cap, the birth options of every child, the network side's argv, the two writable "
         "folders, " + c("abandon_s"), rif("Overall architecture")],
        [c("struct rxr_head") + " and the thirteen other " + c("struct rxr_*"), c("rootside_proto.h"), "Every packet of the closed list "
         "between the two sides (sections below)", rif("Overall architecture")],
        [c("struct rootside_bounds"), c("rootside.h"), "The root side's limits: the grant table (" + c("ROOTSIDE_GRANTS_MAX")
         + " = 32), AUTH tokens and in-flight count, the CLOSE_ORPHAN bucket and per-uid hold, the table of last child exits, "
         "and the three failure tables of the pauses (" + c("ROOTSIDE_LOGIN_USERS") + " = 1024, " + c("ROOTSIDE_LOGIN_PAIRS")
         + " = 512, " + c("ROOTSIDE_LOGIN_HOSTS") + " = 128)", rif("Login and its defences")],
        [c("struct rootside_grant"), c("rootside.h"), "One grant: 16 bytes, user, address, expiry in milliseconds",
         rif("Login and its defences")],
        [c("struct rootside_fail"), c("rootside.h"), "One entry of a failure table: the key (the uid, the address, or " + c("<uid>|<rhost>") + ", according to the table), the last "
         + c("ROOTSIDE_LOGIN_TIMES") + " = 20 failure times, in-flight count, pause end, ladder level", rif("Login and its defences")],
        [c("struct own_child"), c("rootside.c"), "The root side's record of a child it forked: serial, pid, uid, gid, user, the "
         "generation of the network side it was born for, the grace deadlines for SIGTERM and SIGKILL, the moment its client "
         "left", rif("Overall architecture")],
        [c("struct pending_auth"), c("rootside.c"), "An AUTH asked of the dispatcher and not yet answered", rif("Overall architecture")],
        [c("struct found_slot") + ", " + c("struct found_gone_note"), c("rootside.c"), "A desktop found again as the root side keeps "
         "it (pidfd, stage pid, start time, uid, session id, name) and a death to announce after " + c("RXR_FOUND_END"),
         rif("Startup and life cycle")],
        [c("RediscoveredDesktop"), c("rediscover.h"), "A live REMOTIX desktop that no child holds: user, uid, logind session id, "
         "stage pid and name, number of REMOTIX sessions of the user, start time", rif("Startup and life cycle")],
        [c("struct helper") + ", " + c("struct request") + ", " + c("struct response") + ", " + c("struct flight"), c("helper.c"),
         "The PAM helper's object, the packet to the dispatcher, the one-byte answer, and the table of requests in flight",
         rif("Overall architecture")],
        [c("struct sentinel"), c("sentinel.c"), "The connection to the system bus and the state of the asynchronous "
         "checks", rif("Overall architecture")],
        [c("struct command"), c("command.c"), "The bench's control socket: a descriptor and a path", "this appendix"],
        [c("struct bridge"), c("main.c"), "What the network side's callbacks need: the transport and the children table",
         rif("Overall architecture")],
        [c("struct is_present"), c("main.c"), "One user's presence record for the abandonment clock: name, last input "
         "time, count of TOO_SOON refusals", rif("Startup and life cycle")],
        "Children and the stage",
        [c("struct children") + ", " + c("struct child"), c("child.c"), "The network side's table of children and one child: "
         "user, uid, gid, pid, socket, pidfd, serial, the introduction and who-are-you clocks, the reassembly buffers for "
         "frames, cursor and clipboard (three tables, because the three arrive interleaved), what has been asked of the "
         "stage", rif("Overall architecture")],
        [c("struct birth_opts") + ", " + c("struct child_born"), c("child.h"), "What the root side gives " + c("child_birth()")
         + " (canvas, survey folder, switches, the binary's path, the network side's uid, close-only) and what comes back "
         "(pid, socket end, uid, gid, whether a card ACL was granted)", rif("Overall architecture")],
        [c("struct head") + " and the " + c("struct body_*"), c("child.c"), "The envelope and bodies between the network side "
         "and a child (below)", "this appendix"],
        "Transport and protocol",
        [c("struct transport"), c("transport.c"), "The UDP socket and every QUIC connection: limits, handshake rate, the "
         "connection-id map keyed with the secret, the stateless-reset limits", rif("Transport")],
        [c("struct wt"), c("webtransport.c"), "The WebTransport state of one connection: nghttp3, the session stream, stream "
         "classification, send queue, the " + c("rcp_session") + " it hosts", rif("Transport")],
        [c("struct rcp_session"), c("rcp.c"), "One RCP/1 session: state, address, user, negotiated codec, depth, audio and "
         "level, canvas and view, attach slot, video counters and key-frame debt, accumulators, the clocks " + c("last_life")
         + " (the client) and " + c("last_input") + " (the user)", rif("The RCP/1 protocol")],
        [c("struct slot"), c("rcp.c"), "One attach slot: the user and the session that holds it; the table is allocated on the "
         "cap", rif("The RCP/1 protocol")],
        [c("rcp_hooks"), c("rcp.h"), "The hooks through which " + c("rcp.c") + " asks its host to act (send, close, log, "
         "verify, video, input, canvas, layout, stage size, local session, clipboard, logout)", rif("The RCP/1 protocol")],
        [c("certificates"), c("certificates.h"), "Paths of the two certificates and their marker files, the session fingerprint in "
         "base64 and hex, expiry, rotation count", rif("Transport")],
        [c("struct page"), c("page.c"), "The TCP listener and the clients being served, with the cached page and its "
         "compressed copy", rif("Transport")],
        "Other",
        [c("struct budget_count") + ", " + c("struct tenant"), c("budget.h") + ", " + c("budget.c"), "The composition budget: who is "
         "inside and the verdict on a newcomer", rif("Quality, degradation and budget")],
        [c("DesktopSession") + ", " + c("SessionState") + ", " + c("SessionMonitor"), c("session.h"), "Which desktop, the health of a "
         "started session, the virtual monitor read back", rif("The four desktops")],
    ], "«TAB» — The main C structures")

# ── Root-side protocol ───────────────────────────────────────────────────
S2 = p("Every packet is one " + c("SOCK_SEQPACKET") + " message of exactly the size of its struct, starting with "
       + c("struct rxr_head") + ": " + c("magic") + " (" + c("RXR_MAGIC") + ", 0x31525852, “RXR1” little-endian, u32), "
       + c("version") + " (" + c("RXR_VERSION") + " = 3, u16), " + c("kind") + " (u16) and " + c("request") + " (u64, chosen by the "
       "network side and echoed in the answer; 0 in events). The sizes below were obtained by compiling "
       + c("rootside_proto.h") + " alone with gcc on x86-64; the file asserts only two of them (" + c("rxr_verdict") + " = 296 and "
       + c("rxr_spawn_refused") + " = 24).", lead=True) + \
    table(["Kind", "Name", "Direction", "Struct (bytes)", "Carries"], [
        ["1", c("RXR_AUTH"), "network → root", c("rxr_auth") + " (1368)", c("user") + " (" + c("RXR_USER_MAX") + " = 257), "
         + c("password") + " (" + c("RXR_PASSWORD_MAX") + " = 1025), " + c("rhost") + " (" + c("RXR_RHOST_MAX") + " = 64)"],
        ["2", c("RXR_SPAWN"), "network → root", c("rxr_spawn") + " (40)", "the 16-byte grant and the canvas width and height"],
        ["3", c("RXR_CLOSE_ORPHAN"), "network → root", c("rxr_close_orphan") + " (280)", "the user whose found-again desktop is to be closed"],
        ["4", c("RXR_SIGNAL"), "network → root", c("rxr_signal_msg") + " (32)", "a child's serial and " + c("RXR_SIG_TERM") + " or " + c("RXR_SIG_KILL")
         + "; no answer"],
        ["101", c("RXR_READY"), "root → network", c("rxr_ready") + " (1080)", "once, first: the network user's uid, whether a codec was "
         "found, whether the root side keeps measuring, the offered codecs (" + c("RXR_CODEC_MAX") + " = 32) and the "
         "explanation (" + c("RXR_EXPLAIN_MAX") + " = 1024)"],
        ["102", c("RXR_VERDICT"), "root → network", c("rxr_verdict") + " (296)", "outcome, grant (zero unless yes), and the system's "
         "canonical name for the typed one (validated by " + c("rxr_canon_valid()") + ")"],
        ["103", c("RXR_SPAWNED"), "root → network", c("rxr_spawned") + " (296) + two descriptors", "serial, pid, uid, gid, user; the "
         "child's socket end and a pidfd by " + c("SCM_RIGHTS")],
        ["104", c("RXR_SPAWN_REFUSED"), "root → network", c("rxr_spawn_refused") + " (24)", "a reason and, for " + c("RXR_REF_TOO_SOON")
         + ", how long to wait (ms)"],
        ["105", c("RXR_CHILD_EXITED"), "root → network", c("rxr_child_exited") + " (32)", "serial and the " + c("waitpid()")
         + " status; sent after the root side has reaped the child and removed its card grant"],
        ["106", c("RXR_FOUND_AGAIN"), "root → network", c("rxr_found_again") + " (344)", "uid, stage pid, session count, user, logind session id, "
         "process name (" + c("RXR_SESSION_MAX") + " = 32, " + c("RXR_COMM_MAX") + " = 20)"],
        ["107", c("RXR_FOUND_END"), "root → network", c("rxr_found_end") + " (24)", "the number N of " + c("FOUND_AGAIN") + " before it, and "
         + c("RXR_FOUND_OK") + " or " + c("RXR_FOUND_UNKNOWN")],
        ["108", c("RXR_FOUND_GONE"), "root → network", c("rxr_found_gone") + " (280)", "uid and user of an announced desktop whose stage "
         "has gone; only after " + c("FOUND_END")],
        ["109", c("RXR_CODEC"), "root → network", c("rxr_codec") + " (1072)", "the codecs and explanation, once, when a repeated probe "
         "finds some after a startup that found none"],
        ["110", c("RXR_LOCAL_COMING"), "root → network", c("rxr_local_coming") + " (280)", "uid and user of a user whose LOCAL login is held "
         "in PAM; the network side sends that user's logged clients 0x04 and asks the child for the full close ("
         + rif("The local-login hold") + ")"],
    ], "«TAB» — The closed list between the root side and the network side") + \
    p("<b>Constants.</b> " + c("RXR_FOUND_MAX") + " = 256 (the most desktops found again, equal to " + c("MAX_FOUND_AGAIN")
      + " in " + c("main.c") + "), " + c("RXR_GRANT_BYTES") + " = 16, " + c("RXR_AUTH_IN_FLIGHT_MAX") + " = 16, " + c("RXR_AUTH_PER_S")
      + " = 3, " + c("RXR_AUTH_BURST") + " = 8, " + c("RXR_GRANT_LIFE_MS") + " = 30 000. The root side's other bounds are in "
      + c("rootside.h") + ": " + c("ROOTSIDE_LOGIN_PAIR_LIMIT") + " = 5, " + c("ROOTSIDE_LOGIN_HOST_LIMIT") + " = 20, "
      + c("ROOTSIDE_LOGIN_USER_LIMIT") + " = 15, " + c("ROOTSIDE_LOGIN_WINDOW_MS") + " = 300 000, " + c("ROOTSIDE_LOGIN_USER_PAUSE_MS")
      + " = 900 000, " + c("ROOTSIDE_LOGIN_FORGET_MS") + " = 86 400 000, " + c("ROOTSIDE_ORPHAN_PER_S") + " = 2, "
      + c("ROOTSIDE_ORPHAN_BURST") + " = 5, " + c("ROOTSIDE_ORPHAN_UID_MS") + " = 30 000, " + c("ROOTSIDE_ABANDON_S_MAX")
      + " = 31 536 000 (one year).") + \
    table(["Enumeration", "Values"], [
        [c("enum rxr_outcome") + " (the verdict)", c("RXR_NO") + " 0 any refusal · " + c("RXR_YES") + " 1 the only yes · " + c("RXR_NO_LOCKED")
         + " 2 PAM's account lock held · " + c("RXR_NOT_CHECKED") + " 3 PAM was not asked (bounds, helper down, timeout; only for facts "
         "about the server, never counted towards the ban) · " + c("RXR_PAUSED") + " 4 the root side's own pause (for the page a "
         "plain refusal, so that nobody can tell by the byte or the time that a name exists)"],
        [c("enum rxr_refusal") + " (a birth refused)", c("RXR_REF_GRANT") + " 1 unknown, used or expired grant · " + c("RXR_REF_FULL")
         + " 2 the cap · " + c("RXR_REF_USER") + " 3 uid 0, denied or no longer resolves · " + c("RXR_REF_NO_ORPHAN") + " 4 no live REMOTIX "
         "session of that uid · " + c("RXR_REF_FAILED") + " 5 socketpair, fork, PAM session or exec failed · " + c("RXR_REF_CLOSING")
         + " 6 a child of that user is still closing · " + c("RXR_REF_MOVED") + " 7 the name now points to another uid · "
         + c("RXR_REF_NAME_UNKNOWN") + " 8 the lookup failed now · " + c("RXR_REF_RATE") + " 9 over a rate bound · " + c("RXR_REF_TOO_SOON")
         + " 10 the desktop is not yet abandoned"],
        [c("enum child_outcome"), c("CHILD_READY") + ", " + c("CHILD_FAILED") + ", " + c("CHILD_CLOSING") + ", " + c("CHILD_NAME_UNKNOWN")
         + ", " + c("CHILD_NAME_MOVED") + " (what " + c("child_birth()") + " returns, mapped to the refusals above)"],
        [c("enum rootside_login_result"), c("RXR_LOGIN_OK") + ", " + c("RXR_LOGIN_PAIR_PAUSED") + ", " + c("RXR_LOGIN_USER_PAUSED") + ", "
         + c("RXR_LOGIN_HOST_PAUSED") + ", " + c("RXR_LOGIN_PAIR_BUSY") + ", " + c("RXR_LOGIN_USER_BUSY") + ", " + c("RXR_LOGIN_HOST_BUSY")
         + ", " + c("RXR_LOGIN_FULL")],
    ], "«TAB» — Enumerations of the closed list") + \
    warn("Three comments in the headers disagree with the code. " + c("rootside_proto.h") + " says the child's socket is “the only fd "
         "that ever crosses” the channel, but " + c("birth()") + " in " + c("rootside.c") + " sends two (the socket and a pidfd, "
         + c("chan_try2()") + "). Its long comment gives the AUTH rate as “10 per second with a burst of 20”, while the constants, and the "
         "later paragraph of the same comment, say 3 and 8. And its list of root-to-network kinds omits " + c("RXR_CODEC") + ". The code is "
         "described in this manual.", "Header comments.")

# ── PAM helper ───────────────────────────────────────────────────────────
S3 = p("The packets between the root side (or, in the single-process mode, the server) and the PAM dispatcher are one "
       + c("SOCK_SEQPACKET") + " pair; the dispatcher's socket is descriptor 3.", lead=True) + \
    table(["Struct", "Fields", "Notes"], [
        [c("struct request"), c("ticket") + " (u64), " + c("user") + " (257), " + c("password") + " (1025), " + c("rhost") + " (64), "
         + c("tag") + " (8)", "the tag is the 6-hex log tag of the user, so that the check never writes a typed name"],
        [c("struct response"), c("ticket") + " (u64), " + c("outcome") + " (u8)", "1 is the only yes; 2 means refused while the account was "
         "locked; every other value is a no"],
        [c("struct flight"), c("ticket") + ", " + c("expires") + ", " + c("user") + ", " + c("rhost"), "kept in the table of up to "
         + c("MAX_IN_FLIGHT") + " = 16 requests; never the password"],
    ], "«TAB» — The PAM helper's packets")

# ── Child messages ───────────────────────────────────────────────────────
S4 = p("The header is the same for all (" + rif("Overall architecture") + "): " + c("magic") + " " + c("FIG1") + ", " + c("kind") + " u16, "
       + c("version") + " u16 (" + c("CHILD_VERSION") + " = 1), " + c("serial") + " u64, " + c("declared_uid") + " u32, " + c("byte") + " u32. "
       "The longest message is " + c("MAX_ENVELOPE") + " (a head, a " + c("struct body_frame") + " and " + c("MAX_PIECE") + " = 32 768 bytes). "
       "A frame is at most " + c("FRAME_MAX") + " = 16 MiB; the clipboard text at most " + c("RCP_CLIPBOARD_CAP") + " = 1 000 000 bytes.",
       lead=True) + \
    table(["Kind", "Name", "Direction", "Body"], [
        ["1", c("MSG_CHI_SEI"), "network → child", "none: “who are you”, every " + c("RECHECK_MS") + " (60 s); the answer is " + c("MSG_INTRO")],
        ["2", c("MSG_SHUT_DOWN"), "network → child", "none: dismantle the stage and exit"],
        ["3", c("MSG_RESEND_STAGE"), "network → child", "none: send again the frames you keep"],
        ["4", c("MSG_VIDEO"), "network → child", c("body_video") + ": codec (1 HEVC, 3 H.264, 0 stop capturing), key due, depth, level × 10 (0 = none declared)"],
        ["5", c("MSG_INPUT"), "network → child", c("body_input") + ": id, action, pressed, evdev code, two int32; the actions include "
         + c("CHILDREN_INPUT_RECANVAS") + " and " + c("CHILDREN_INPUT_TERMINATE")],
        ["6", c("MSG_LAYOUT"), "network → child", c("body_layout") + ": a 64-byte keyboard layout name"],
        ["7", c("MSG_AUDIO"), "network → child", c("body_audio") + ": codec (1 Opus, 2 PCM, 0 off)"],
        ["8", c("MSG_CLIPBOARD_OFFER"), "network → child", "the client announces text; no text yet"],
        ["9", c("MSG_CLIPBOARD_FROM_CLIENT"), "network → child", c("body_clipboard") + ": serial, total, offset, piece, “nothing”; the text in pieces"],
        ["10", c("MSG_INTRO"), "child → network", c("body_whoami") + ": uids, gids, pid, ppid, open descriptors, runtime folder, session bus, user, "
         "and the child's own answer to the name check (" + c("NAME_HOLDS") + ", " + c("NAME_GONE") + ", " + c("NAME_OTHER_UID") + ")"],
        ["11", c("MSG_STAGE"), "child → network", c("body_stage") + ": bus, session state, capture take, monitors before and after, size, streams, fault text"],
        ["12", c("MSG_FRAME"), "child → network", c("body_frame") + ": codec, key, size, instant, total, offset, piece, last input id; in pieces"],
        ["13", c("MSG_CURSOR"), "child → network", c("body_cursor") + ": width, height, hotspot, total, offset, piece; in pieces"],
        ["14", c("MSG_CANVAS"), "child → network", c("body_canvas") + ": intended and got size (0×0 = failed), “should wait”"],
        ["15", c("MSG_SESSION_FINISHED"), "child → network", "none: the graphical session ended and nobody asked"],
        ["16", c("MSG_BLOCK"), "child → network", c("body_block") + ": codec, byte count, instant, then one encoded audio block (never in pieces; dropped if the socket is full)"],
        ["17", c("MSG_CLIPBOARD_FROM_SESSION"), "child → network", "the session copied text; in pieces, already validated"],
        ["18", c("MSG_CLIPBOARD_REQUEST"), "child → network", "something in the session is pasting: the request's serial"],
        ["19", c("MSG_PACE"), "network → child", c("body_pace") + ": a frame-rate ceiling (0 = none); only if the server was started with " + c("--decoder-pace")],
        ["20", c("MSG_LOCAL_FOUND"), "child → network", "none: the child's guard found a local session, did the light close and is leaving"],
    ], "«TAB» — The messages between the network side and a child") + \
    table(["Enumeration", "Values"], [
        [c("CHILDREN_INPUT_*") + " (the " + c("action") + " of " + c("MSG_INPUT") + ")", "1 pointer · 2 button · 3 wheel · 4 letter · 5 position · "
         "6 release all (at detach) · 7 recanvas · 8 terminate (the session)"],
        [c("CHILDREN_EXIT_*") + " (the argument of terminate)", "0 the user asked · 1 abandonment · 2 a local session (light close only) · 3 the service is stopping (same road as abandonment in the child) · 4 a local login is held in PAM (full close, never downgraded to the light one)"],
        [c("NAME_*") + " in " + c("body_whoami"), "0 not asked · 1 the name resolves to this uid · 2 it no longer resolves · 3 it resolves to another uid"],
    ], "«TAB» — Enumerations inside the child's messages")

# ── Command socket ───────────────────────────────────────────────────────
S5 = p("The only text protocol on a local socket is the bench's unblock command in " + c("command.c") + ". It exists only if the "
       "server is started with " + c("--command-socket <path>") + "; the packaged unit does not pass it, and the owner decided on 17 "
       "November 2026 that the administrator has no command to lift a ban (PIANO.md; " + c("prove/check-ban.py")
       + " check “unblock-shipped” reports that the packaged unit has no such option and that there is no command-line tool; as written it cannot fail). When given, the socket is created mode 0600, one "
       "line is read per connection (with a short timeout, so that a silent client holds the loop for two tenths of a second at most) "
       "and one line is answered:", lead=True) + \
    table(["Request", "Answer", "Meaning"], [
        [c("PING"), c("PONG"), "the command exists; nothing is touched"],
        [c("UNBLOCK <address>"), c("REMOVED <key>"), "the address was banned and is now free in memory; the rewrite of the ban file was requested"],
        [c("UNBLOCK <address>"), c("NOT-BANNED <key>"), "there was nothing to remove"],
        ["anything else, or an empty line", c("NOT-UNDERSTOOD <line>"), "a refusal that cannot be taken for an answer to a real request"],
    ], "«TAB» — The unblock socket") + \
    note("With the network side behind its walls the socket would live in " + c("/run/remotix/net") + " (the only writable run folder, "
         "noexec). The file says it cannot tell whether the ban file was rewritten: it reports that the rewrite was requested.",
         "A bench tool.")

# ── RCP index ────────────────────────────────────────────────────────────
S6 = p("All RCP/1 message types by number. The bodies are in " + c("docs/RCP.md") + " at the section given; the constants are the "
       + c("T_*") + " enumerations at the top of " + c("rcp.c") + ". The protocol itself is explained in " + rif("The RCP/1 protocol") + ".",
       lead=True) + \
    table(["Type", "Name", "Direction", "Body", "RCP.md"], [
        "Control channel (the first bidirectional stream), RCP.md §7.1",
        ["0x0001", c("HELLO"), "client → server", "u16 version, list of capabilities (name, value)", "§4.3"],
        ["0x0002", c("HERE_I_AM"), "server → client", "u16 chosen version, list of capabilities", "§4.3"],
        ["0x0003", c("CREDENTIALS"), "client → server", "string user (1–256 bytes), string password (1–1024)", "§4.4"],
        ["0x0004", c("ADMITTED"), "server → client", "empty", "§4.4"],
        ["0x0005", c("REJECTED"), "server → client", "u8 reason", "§4.4"],
        ["0x0006", c("ATTACH"), "client → server", "u32 canvas width and height, u32 view width and height, string layout (≤ 64)", "§4.5"],
        ["0x0007", c("SESSION"), "server → client", "u8 state (1 NEW, 2 RESUMED), u32 canvas width and height, string desktop", "§4.5"],
        ["0x0008", c("VIEW"), "client → server", "u32 width, u32 height", "§7.1"],
        ["0x0009", c("LAYOUT"), "client → server", "string layout", "§7.1"],
        ["0x000A", c("CURSOR_SHAPE"), "server → client", "u16 width, height (≤ 256), i16 hot x and y, premultiplied BGRA image", "§7.2"],
        ["0x000B", c("FIT_CANVAS"), "client → server", "u32 width, u32 height", "§7.1"],
        ["0x000C", c("FAREWELL"), "both", "u8 reason, string detail", "§8"],
        ["0x000D", c("REQUEST_KEY"), "client → server", "u32 last frame number decoded", "§5.2, §7.1"],
        ["0x000E", c("CANVAS"), "server → client", "u8 outcome (1 FITTED, 2 REFUSED), u8 reason (1 COMPOSITOR_UNABLE, 2 SIZE_OUT_OF_RANGE, 3 NOT_NOW), "
         "u32 canvas width and height", "§7.1"],
        ["0x000F", c("BENCH_MARK"), "client → server", "three u32; compiled only with " + c("BENCH=1") + ": in the installed binary it is an unknown type", "§7.5"],
        ["0x0010", c("BENCH_OUTCOME"), "server → client", "the outcome of the above; the same restriction", "§7.5"],
        ["0x0011", c("TERMINATE_SESSION"), "client → server", "empty: end the graphical session", "§7.6"],
        ["0x0012", c("PACE"), "client → server", "u16 max frames per second; lawful only if " + c("video.pace") + " was declared by both sides, which needs "
         + c("--decoder-pace") + " on the server (off in the packaged unit)", "none"],
        "Input channel (type high byte 0x01), RCP.md §7.3",
        ["0x0101", c("POINTER"), "client → server", "u32 id, u64 instant, u32 x, u32 y (canvas coordinates): 20 bytes", "§7.3"],
        ["0x0102", c("BUTTON"), "client → server", "id, instant, u16 evdev code, u8 pressed: 15 bytes", "§7.3"],
        ["0x0103", c("WHEEL"), "client → server", "id, instant, i32 axis x, i32 axis y (120 per notch): 20 bytes", "§7.3"],
        ["0x0104", c("LETTER"), "client → server", "id, instant, u32 Unicode scalar: 16 bytes", "§7.3"],
        ["0x0105", c("KEY_POSITION"), "client → server", "id, instant, u16 evdev code, u8 pressed: 15 bytes", "§7.3"],
        "Clipboard channel (type high byte 0x02), RCP.md §7.4",
        ["0x0201", c("CLIPBOARD_ANNOUNCE"), "both", "u32 transfer, u32 length: 8 bytes", "§7.4"],
        ["0x0202", c("CLIPBOARD_ASK"), "both", "u32 transfer: 4 bytes", "§7.4"],
        ["0x0203", c("CLIPBOARD_TEXT"), "both", "u32 transfer, UTF-8 text to the end of the message (cap " + c("RCP_CLIPBOARD_CAP") + ")", "§7.4"],
        "Video (one unidirectional stream per frame) and audio (datagrams)",
        ["0x0301 · 0x0302", "keyframe · delta frame", "server → client", "a 28-byte header (u16 type, u16 codec, u32 width, u32 height, u32 number, u64 instant, "
         "u32 input) then the data, to the FIN; a reset stream is an incomplete frame", "§6.2"],
        ["0x0401", "audio block", "server → client", "u16 type, u16 codec, u64 instant, then one Opus (or PCM) block in one datagram; 12-byte header", "§6.3"],
    ], "«TAB» — Index of RCP/1 messages") + \
    p("<b>Numbers carried in bodies.</b> Video codec: 1 HEVC, 2 AV1 (never reused, no longer negotiated), 3 H.264 (" + c("RCP_CODEC_VIDEO_MAX")
      + " = 3). Audio codec: 1 Opus, 2 PCM; these are not the video numbers. Framing: the largest message is " + c("MAX_MESSAGE")
      + " = 1 MiB, framing included; a video frame at most 16 MiB; a cursor at most 256×256. Elementary types are big-endian "
      "and unaligned (RCP.md §6.0).") + \
    table(["Code", "Name", "Sent when"], [
        ["0x01", c("RCP_CLOSED_BY_USER"), "the user closed the client"],
        ["0x02", c("RCP_INACTIVITY"), "30 minutes without input (the default)"],
        ["0x03", c("RCP_SESSION_ABANDONED"), "60 minutes without input (the default): the desktop is closed"],
        ["0x04", c("RCP_LOCAL_SESSION_PREVAILED"), "the user opened a local graphical session"],
        ["0x05", c("RCP_ALREADY_ACTIVE_LOCALLY"), "the user already has one"],
        ["0x06", c("RCP_BUDGET_FULL"), "the composition budget has no room"],
        ["0x07", c("RCP_WRONG_CREDENTIALS"), "PAM's no; the same code for a wrong password, an unknown user, a denied user"],
        ["0x08", c("RCP_TOO_MANY_ATTEMPTS"), "the address is banned"],
        ["0x09", c("RCP_NOTHING_IN_COMMON"), "no shared video codec"],
        ["0x0A", c("RCP_INCOMPATIBLE_VERSION"), "the versions do not meet"],
        ["0x0B", c("RCP_PROTOCOL_ERROR"), "a violation of the bytes"],
        ["0x0C", c("RCP_SERVER_CLOSING"), "the service is stopping"],
        ["0x0D", c("RCP_TIMED_OUT"), "a handshake ceiling expired"],
        ["0x0E", c("RCP_SESSION_UNSERVABLE"), "the attach is well formed but cannot be served (cap, closing desktop, no stage, unknown layout)"],
        ["0x0F", c("RCP_ALREADY_ACTIVE_REMOTELY"), "another live client of the user holds the slot"],
        ["0x10", c("RCP_SESSION_TERMINATED"), "the graphical session ended (Log Out)"],
    ], "«TAB» — The farewell reasons (RCP.md §8.2, " + c("rcp.h") + ")")

CHAPTER = ("Appendix A — Data structures and messages", [
    ("The main C structures", S1),
    ("The root-side protocol, message by message", S2),
    ("The PAM helper's packets", S3),
    ("Messages between the network side and a child", S4),
    ("The unblock command socket", S5),
    ("Index of RCP/1 messages and farewell reasons", S6),
])
