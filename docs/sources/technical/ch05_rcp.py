from build import box, c, code, fig, flow, note, p, rif, seq, steps, table, tip, ul, warn

# ── Model ───────────────────────────────────────────────────────────────
S1 = p("RCP/1 — the Remotix Control Protocol, version 1 — is what the page and the server say to each other inside the "
       "WebTransport session. The name says <i>control</i>, not <i>display</i>: besides pixels it carries input, "
       "clipboard, geometry, the farewell and the state of the session. Its specification is " + c("RCP.md") + ", "
       "written before the first line of code and precise enough to prove an implementation wrong.", lead=True) + \
    flow([("Page", "TCP 7447", "dark"), ("WebTransport", "UDP, /rcp/1", "blue"), ("CIAO/ECCOMI", "capabilities", "navy"),
          ("CREDENZIALI", "PAM, ban, 1 s", "navy"), ("ATTACCA", "canvas, layout", "navy"),
          ("Channels", "media, input", "green")],
         "«FIG» — The steps of a connection, in an order that admits no permutation") + \
    p("Three properties are built into that order. The server proves who it is (TLS with the pinned certificate) before "
      "the password leaves the browser. Authentication comes before attachment: whoever is not admitted cannot even name "
      "a session. And the canvas is agreed at attach time. A message that arrives in a state where it is not expected is "
      + c("ERRORE_PROTOCOLLO") + " (protocol error) — the protocol says «you got the order wrong» instead of punishing each permutation with "
      "a different error, which was trap 1 of the v1 lessons.") + \
    p("The message names are those of the code and of " + c("RCP.md") + ", in Italian: " + c("CIAO") + " (hello) and "
      + c("ECCOMI") + " (here I am) exchange versions and capabilities, " + c("CREDENZIALI") + " (credentials) carries "
      "user and password, " + c("ATTACCA") + " (attach) asks for a desktop and " + c("SESSIONE") + " (session) grants it.") + \
    p("<b>Why the specification is the referee.</b> In v1 the referee was " + c("mstsc") + ": if Microsoft's client drew "
      "it, it was right. In REMOTIX client and server are both ours, and two programs written by the same hand that agree "
      "with each other confirm nothing — they repeat the same assumption. So client and server are never tested against "
      "each other: they are tested against " + c("RCP.md") + ", by programs that were written reading only the "
      "specification (" + rif("Testing against the specification") + ").") + \
    table(["Implementation", "Language", "Role"], [
        [c("src/rcp.c") + ", " + c("src/rcp.h"), "C", "The server side. Knows " + c("RCP.md") + " and nothing else: no "
         "sockets, no clock, no PAM, no compositor. Time comes in as a parameter (" + c("rcp_tempo()") + ", «tempo» = time), bytes go out "
         "through hooks (" + c("rcp_ganci") + ", «ganci» = hooks), so a bench can make time run as it wants."],
        [c("banchi/rcp/rcp.c") + ", " + c("rcp.h") + ", " + c("autenticazione.c"), "C", "A byte-identical twin, grafted "
         "into the ngtcp2 examples by " + c("banchi/01-b3-rcp-innesta.py") + ". The " + c("Makefile") + " variable "
         + c("GEMELLATI") + " (twinned files) compares the copies at every build and stops if they differ."],
        [c("src/pagina.html"), "JavaScript", "The client: the only one users run."],
        [c("banchi/01-b3-cliente.py") + ", " + c("banchi/02-filo-cliente.py"), "Python (" + c("aioquic") + ")", "The test "
         "client — the second reader, in another language."],
        [c("banchi/01-b4-validatore.py") + ", " + c("banchi/02-filo-validatore.py"), "Python", "The wire validator: reads a "
         "recording and says which byte does not conform."],
    ], "«TAB» — The implementations of RCP/1") + \
    note("because the twin is compiled inside the ngtcp2 examples, " + c("rcp.c") + " cannot include " + c("input.h") + ", "
         + c("cursore.h") + ", " + c("gio") + " or " + c("xkbcommon") + ". Everything it needs from the product — PAM, "
         "streams, input injection, keyboard layouts, the stage, local sessions, the clipboard — reaches it through the "
         "function pointers of " + c("rcp_ganci") + ". The pointers are optional; a missing hook is logged, never treated "
         "as a client violation.", "Why hooks and not includes.")

# ── Rigor ───────────────────────────────────────────────────────────────
S2 = p("An implementation that receives something it does not understand must close with " + c("ERRORE_PROTOCOLLO")
       + " and log what it did not understand. It must not ignore it, guess or continue. The rule covers an unknown "
       "message type, a length that does not add up, a field out of range, a message in the wrong state and a channel "
       "used in the wrong direction.", lead=True) + \
    p("It is the first rule of the document, not a footnote, because a lenient parser is convenient on day one and "
      "poisonous forever: if the server starts emitting a wrong field and the client politely ignores it, the defect "
      "stays invisible until it produces a distant, incomprehensible symptom — and with no foreign client left to "
      "complain, nobody sees it.") + \
    table(["#", "Where", "What is tolerated, and why"], [
        ["1", "§4.3", "An unknown capability name or list item is ignored: it is how future versions understand each "
         "other. It ignores an offer, not a command."],
        ["2", "§6.3", "A corrupt or short audio datagram is dropped: datagrams are unreliable by definition."],
        ["3", "§7.1", "For one second after a canvas change, input coordinates valid on the previous canvas are clamped "
         "to the new one."],
        ["4", "§7.1", c("ADATTA_TELA") + " (fit the canvas) below the minimum gets " + c("TELA(RIFIUTATA, MISURA_FUORI_LIMITI)")
         + " (canvas: refused, size out of limits) "
         "instead of closing: a badly dragged window must not cost the session."],
        ["5", "§5.2, §7.4", "A " + c("RICHIEDI_CHIAVE") + " (request a key frame) within 200 ms of the last key frame may be ignored; a late "
         + c("APPUNTI_CHIEDI") + " (clipboard request) is served with the current text."],
        ["6", "§6.2", "After a canvas change, frames at a size in force since the queue started draining are accepted "
         "until the first key frame at the new size."],
        ["7", "§2.5", "A video stream arriving before " + c("SESSIONE") + " when " + c("ATTACCA") + " has already left "
         "is held, not fatal: two QUIC streams are not ordered with respect to each other."],
        ["8", "§6.2", "A frame at a size no canvas ever had is held while an " + c("ADATTA_TELA") + " is unanswered."],
    ], "«TAB» — The eight declared exceptions; there are no others") + \
    p("Every tolerance is logged: a silent tolerance is indistinguishable from a defect. Rows 7 and 8 entered on 13 "
      "August 2026 when it was found that other sections already ordered them while this list claimed six — since then, "
      "whoever writes a tolerance elsewhere adds its row here in the same change.") + \
    steps([
        "<b>Log what was not understood</b>: the type, the length, the state — not «protocol error».",
        "<b>Send " + c("CONGEDO") + "</b> (farewell) with the reason on the control channel, if the control channel is still usable.",
        "<b>Close the WebTransport session</b> with the application error code equal to the reason code (" +
        rif("Disconnect reasons") + "). Not the QUIC connection: a page can only close its session.",
    ]) + \
    p("Step 3 is the one that saves diagnoses: if the farewell cannot arrive — broken stream, unreadable message — the "
      "reason still travels inside the close. In v1 the server logged «dismissing the client» while the client logged "
      "«network error» for three phases. Code 0 means «closed without reason» and must never be used. In " + c("rcp.c")
      + " the three steps are " + c("congeda()") + " (dismiss); the host's " + c("chiudi") + " (close) hook performs step 3.")

# ── Channels ────────────────────────────────────────────────────────────
S3 = p("Whoever receives a stream must know what is inside before reading it. The channel is given by the high byte "
       "of the first " + c("tipo") + " (type) field of the RCP payload — never by the stream number, which WebTransport does not "
       "even expose to a page.", lead=True) + \
    table(["High byte", "Channel", "Lives on", "Direction", "What follows"], [
        [c("0x00"), "control", "the first bidirectional stream of the session", "both", "framed messages (§6.1)"],
        [c("0x01"), "input", "one unidirectional stream", "client → server", "framed messages"],
        [c("0x02"), "clipboard", "unidirectional streams", "both", "framed messages"],
        [c("0x03"), "video", "one unidirectional stream per frame", "server → client", "the 28-byte header, unframed"],
        [c("0x04"), "audio", "datagrams only", "server → client", "the 12-byte header"],
    ], "«TAB» — Channel identification") + \
    ul([
        "Any other high byte is " + c("ERRORE_PROTOCOLLO") + "; so is a channel in the wrong direction (" + c("0x01")
        + " from the server, " + c("0x03") + " from the client), " + c("0x00") + " on a unidirectional stream, " + c("0x03")
        + " on the control stream, and " + c("0x04") + " on any stream.",
        "The client must not open bidirectional streams beyond the control channel, and the server must not open any.",
        "The server opens no video stream before it has sent " + c("SESSIONE") + "; the client opens its input stream "
        "only after receiving " + c("SESSIONE") + ", exactly one, and keeps it open.",
        "In " + c("rcp.c") + " the control channel accepts only high byte " + c("0x00") + " (" + c("drena()") + ", «drain»); a "
        "second input stream while the first is alive, or input bytes before " + c("SESSIONE") + ", are violations ("
        + c("rcp_ricevi_input()") + ").",
    ]) + \
    warn("on WebTransport every stream starts with a preamble — the stream type " + c("0x54") + " (unidirectional) or "
         + c("0x41") + " (bidirectional) as a QUIC variable-length integer, on the wire " + c("40 54") + " and " + c("40 41")
         + ", followed by the session number. The «first two bytes» are the first two bytes of the RCP payload, after "
         "the preamble that the transport consumes. The test client read the first two bytes of the stream literally on "
         "12 August 2026, found channel " + c("0x40") + " and closed every frame; server and page had agreed only because "
         "the same hand wrote both (finding P18).", "The preamble is not RCP.")

# ── Types and framing ───────────────────────────────────────────────────
S4 = p("Byte order is network order (big-endian). No field is aligned and no padding is allowed: fields are read and "
       "written in sequence. An extra byte that «makes the sums work» in a C struct is exactly the defect corrected in the "
       "video header on 9 August 2026, when a drawing gave eight bytes to a " + c("u32") + ".", lead=True) + \
    table(["Type", "Encoding", "Rules"], [
        [c("u8") + ", " + c("u16") + ", " + c("u32") + ", " + c("u64"), "unsigned, big-endian", ""],
        [c("i16") + ", " + c("i32"), "two's complement, big-endian", ""],
        ["string", c("u16 length") + " + exactly that many UTF-8 bytes, no terminator", "Invalid UTF-8 is "
         + c("ERRORE_PROTOCOLLO") + "; empty is length 0. No terminator because a terminator invites passing the string "
         "to " + c("printf") + " without copying it, and a NUL in the middle becomes a silent truncation."],
        ["list", c("u16 count") + " + the items", ""],
    ], "«TAB» — Elementary types (RCP.md §6.0)") + \
    code(""" 0        2        6                    6+length
 ├────────┼────────┼─────────────────────┤
 │ tipo   │ length │ body                │
 │ u16    │ u32    │                     │""", "text", "Framing on the control, input and clipboard channels") + \
    ul([
        c("length") + " is the exact number of body bytes. For every control type whose shape is known, "
        + c("misura_campi()") + " parses the fields and compares: a length that disagrees with the fields is "
        + c("ERRORE_PROTOCOLLO") + ", and the log names both numbers.",
        "No message may exceed 1 MiB <i>including</i> the 6 framing bytes: " + c("MAX_MESSAGGIO") + " = 1 048 576, "
        + c("MAX_CORPO") + " = " + c("MAX_MESSAGGIO - 6") + " (defect B-14, 10 August 2026: the body was compared with the "
        "whole cap, so 1 048 582 bytes on the wire were accepted).",
        "The length is checked before allocating. The control-channel accumulator grows on demand up to " +
        c("MAX_ACCUMULO") + " = 1 MiB; the input accumulator is " + c("I_ACCUMULO") + " = 32 bytes forever, because the "
        "five input types have fixed lengths known from the type alone — whoever announces a megabyte on the input stream "
        "is dismissed after six bytes.",
        "Every integer has a single declared meaning of «absent»; there are no implicit sentinels (" + c("numero = 0")
        + " (number), " + c("id = 0") + " and " + c("istante = 0") + " (instant) are each declared where they are used).",
    ])

# ── Handshake ───────────────────────────────────────────────────────────
HS = seq([("Page", "pagina.html", "dark"), ("Server", "rcp.c", "navy"), ("PAM helper", "aiutante.c", "blue")], [
    ("sep", "WebTransport session open on /rcp/1 — control channel within 5 s"),
    (0, 1, "opens the control channel (first bidi stream)"),
    (0, 1, "CIAO: version 1, capabilities"),
    (1, 0, "ECCOMI: version 1, server capabilities", True),
    ("nota", 1, "negotiated codec, depth, audio written to the log"),
    (0, 1, "CREDENZIALI: user, password"),
    ("nota", 1, "address banned? then no PAM at all"),
    (1, 2, "verify (ticket number)"),
    (2, 1, "verdict for the ticket", True),
    ("nota", 1, "never before 1 s from CREDENZIALI"),
    (1, 0, "AMMESSO  (or RESPINTO + close)", True),
    (0, 1, "ATTACCA: canvas, view, layout"),
    (1, 0, "SESSIONE: new/resumed, granted canvas, desktop", True),
    ("sep", "channels flow"),
    (1, 0, "first video stream: a key frame", True),
    (0, 1, "opens the input stream"),
    (0, 1, "ADATTA_TELA: the size of its own window"),
    (1, 0, "TELA: adapted or refused", True),
], "«FIG» — The RCP/1 handshake as the product runs it", width=900)

S5 = p("The handshake has five steps and runs on the control channel. Every message has a deadline (" +
       rif("Handshake deadlines and session states") + ") and every wrong turn ends in a reason the page can show.",
       lead=True) + HS + steps([
    "<b>Control channel.</b> The page opens the first bidirectional stream. Its closing <i>is</i> the end of the "
    "session.",
    "<b>" + c("CIAO") + " → " + c("ECCOMI") + ".</b> Version and capabilities; the server picks codecs (" +
    rif("CIAO and ECCOMI: capability negotiation") + ").",
    "<b>" + c("CREDENZIALI") + " → " + c("AMMESSO") + " (admitted) / " + c("RESPINTO") + " (rejected).</b> One attempt per connection. The server "
    "asks PAM through the helper process and answers no earlier than one second after receiving the message (" +
    rif("Credentials, the fixed delay and the address ban") + ").",
    "<b>Capacity gate.</b> Between PAM's yes and " + c("AMMESSO") + ", the parent checks that the user can have a stage: "
    "if all stages are taken (" + c("SESSIONE_NON_SERVIBILE") + ", «session cannot be served»), the composition budget "
    "says no (" + c("BUDGET_PIENO") + ", «budget full»), or the stage cannot be started, the page receives " + c("CONGEDO") + " with that reason instead of "
    + c("AMMESSO") + " (" + c("consegna_verdetto()") + ", «deliver the verdict», in " + c("main.c") + "). The child is not spawned for a user "
    "who is about to be dismissed.",
    "<b>" + c("ATTACCA") + " → " + c("SESSIONE") + ".</b> Canvas, view and keyboard layout; the server takes the user's "
    "seat and answers with the granted canvas (" + rif("ATTACCA and SESSIONE: attaching to a desktop") + ").",
    "<b>Channels.</b> The first video frame is a key frame; the page opens its input stream and, since 15 August 2026, "
    "sends one " + c("ADATTA_TELA") + " with the size of its own window (DECISIONI.md §5.0-sexies).",
])

# ── CIAO / ECCOMI ───────────────────────────────────────────────────────
S6 = p(c("CIAO") + " (client → server) carries the highest major version the client speaks and its capabilities; "
       + c("ECCOMI") + " (server → client) carries the version chosen and the server's capabilities. Both bodies have the "
       "same shape.", lead=True) + \
    code("""CIAO / ECCOMI
 ├── u16  versione   (version)
 └── list of capabilities
       u16 count
       for each:  string name · string value""", "text", "Body of CIAO and ECCOMI") + \
    table(["Name", "Declared by", "Values", "In the product"], [
        [c("video.codec"), "both", "comma list of " + c("hevc") + ", " + c("h264") + ", in order of preference", "Page: "
         + c("hevc,h264") + " filtered to the codecs its probe actually saw painted. Server: the codecs the GPU can "
         "encode, measured at start-up by " + c("figlio_capacita_video()") + " (the child's video capabilities) and set "
         "with " + c("rcp_video_codec_imposta()") + " — " + c("hevc,h264") + ", " + c("h264") + " or empty."],
        [c("video.profondita") + " (depth)", "both", c("8") + ", " + c("10"), "Server: " + c("8,10") + "."],
        [c("video.livello") + " (level)", "client", "highest level it decodes, e.g. " + c("5.1"), "Page: " + c("5.1")
         + " (" + c("LIVELLO_DICHIARATO") + ", «declared level»). The server must not emit a higher level; the child imposes it on the "
         "encoder and re-reads it from the SPS."],
        [c("video.misura_massima") + " (maximum size)", "client", c("WIDTHxHEIGHT") + " it can decode", "Page: the largest step of a "
         "ladder its decoder actually painted; omitted if nothing was measured. It caps the granted canvas."],
        [c("audio.codec"), "both", c("opus") + ", " + c("pcm"), "Server: " + c("opus,pcm") + ". Page: " + c("opus,pcm")
         + " only if it can decode Opus, otherwise " + c("pcm") + "."],
        [c("input.tocco") + " (touch)", "client", c("si") + " (yes), " + c("no"), "Reserved; always " + c("no") + " in RCP/1."],
        [c("appunti.testo") + " (clipboard text)", "both", c("si") + ", " + c("no"), "Both " + c("si") + "; the page turns the clipboard on "
         "only if the server declares it."],
        [c("client.nome") + " (client name)", "client", "free text for the log", "Page: " + c("remotix-pagina 0.1.0") + "."],
        [c("banco.marca") + " (bench marker)", "server", c("si") + ", " + c("no"), "Always " + c("no") + " (" + rif("The bench marker: BANCO_MARCA") + ")."],
    ], "«TAB» — The capabilities defined in RCP/1") + \
    p("<b>Form of names and values</b>, enforced in " + c("tratta_ciao()") + " (handle CIAO) so that «ignore what you do not know» does "
      "not become «guess»:") + \
    ul([
        "a name is " + c("a-z") + ", " + c("0-9") + ", " + c(".") + " and " + c("_") + ", 1 to 64 bytes (the underscore was "
        "added on 10 August 2026 when the validator, at its first run, rejected " + c("video.misura_massima") + " — a "
        "name defined by the specification itself);",
        "a value is printable UTF-8, 1 to 256 bytes; empty is " + c("ERRORE_PROTOCOLLO") + " (whoever has nothing to "
        "say omits the capability);",
        "a list is comma-separated without spaces; an unknown item inside a known list is discarded and logged, like an "
        "unknown name;",
        "a name repeated twice is " + c("ERRORE_PROTOCOLLO") + " — «last wins» and «first wins» would be two "
        "implementations of the same text;",
        "a capability from the wrong side (" + c("banco.marca") + " from the client) is " + c("ERRORE_PROTOCOLLO") + ".",
    ]) + \
    p("<b>Negotiation.</b> The server chooses, inside the intersection, following the <i>client's</i> order of "
      "preference (" + c("prima_comune()") + ", «first in common»), and logs the choice. " + c("pcm") + " and depth " + c("8") + " must be "
      "declared by both: a client that omits them is dismissed with " + c("NIENTE_IN_COMUNE") + " (nothing in common), not "
      + c("ERRORE_PROTOCOLLO") + " — it did not write badly, it has nothing in common. An empty intersection, or a "
      "server whose GPU encodes nothing (empty " + c("video.codec") + "), also ends in " + c("NIENTE_IN_COMUNE") + "; the "
      "server never falls back to a codec nobody declared. AV1 left the negotiation on 20 August 2026 (Firefox for "
      "Android had neither HEVC nor AV1, AV1 had no hardware encoder anywhere in the setup, and Firefox painted "
      "rectangular blocks on bytes that Chrome and dav1d decoded cleanly); its number 2 is never reused.") + \
    p("<b>Version.</b> " + c("CIAO") + " must carry exactly " + c("RCP_VERSIONE") + " = 1, the number in the path "
      + c("/rcp/1") + "; anything else is " + c("VERSIONE_INCOMPATIBILE") + " (incompatible version). The page checks the version in "
      + c("ECCOMI") + " the same way and dismisses with the same reason.") + \
    note(c("ECCOMI") + " carries the server's offer (for example " + c("video.codec=hevc,h264") + "), not the single "
         "codec it chose. The page takes the first item of the server's list that it can paint; the server chose the first "
         "item of the page's list that it can encode. The two agree today because both lists are in the order "
         + c("hevc,h264") + " (" + c("PREFERENZA") + ", «preference», in the page, the start-up probe in the server); the codec actually "
         "used is the one carried by each frame header.", "What ECCOMI says.")

# ── Credentials ─────────────────────────────────────────────────────────
S7 = p("A single " + c("CREDENZIALI") + " message carries user and password; the server hands them to PAM (service "
       + c("remotix") + ") and answers " + c("AMMESSO") + " (empty body) or " + c("RESPINTO") + " with a one-byte reason. "
       "There is one attempt per connection: a second attempt needs a new connection.", lead=True) + \
    code("""CREDENZIALI
 ├── string utente     (user) 1..256 bytes, printable UTF-8
 └── string parola     (password) 1..1024 bytes, no NUL byte
AMMESSO                (empty)
RESPINTO
 └── u8 motivo         (reason) CREDENZIALI_ERRATE 0x07 · TROPPI_TENTATIVI 0x08""", "text", "Bodies") + \
    ul([
        "<b>No distinction</b> between «no such user» and «wrong password»: both are " + c("CREDENZIALI_ERRATE") + " (wrong credentials).",
        "<b>" + c("RESPINTO") + " is the farewell of authentication.</b> After it the server closes the session with the "
        "same code and sends no " + c("CONGEDO") + ". The client may still send one " + c("CONGEDO") + " — §8.1 obliges "
        "whoever closes to say why — but anything else, in particular a second " + c("CREDENZIALI") + ", is the violation "
        "§4.4 forbids. " + c("giudica_dopo_la_fine()") + " (judge after the end) tells the two apart in the log.",
        "<b>The password is wiped</b> (" + c("memset") + ") as soon as it has been handed on, and never appears in any log "
        "at any level.",
        "<b>The empty strings</b> are a protocol error, not a PAM attempt: otherwise an attacker sending empty "
        "credentials would never increment the ban counter.",
    ]) + \
    p("<b>PAM runs outside the loop.</b> Until 12 August 2026 PAM blocked the server's single " + c("poll") + " loop for "
      "one to two seconds per attempt (bench B8, 11 August 2026), most of it " + c("pam_faildelay") + "; with video "
      "flowing, every screen would freeze whenever someone else logged in. Now " + c("chiedi_verifica") + " (ask for verification) hands the "
      "question to a helper process (" + c("aiutante.c") + ", «helper») and returns a ticket; the verdict comes back through "
      + c("rcp_verdetto()") + " (verdict). A process, not a thread, because PAM is not reliably re-entrant. Two deadlines guard "
      "the answer: the helper's own at 8 s, and " + c("TETTO_VERDETTO") + " (verdict ceiling) = 12 s in " + c("rcp.c") + ", which counts "
      "as a no. If the question cannot even be sent, the answer is " + c("RESPINTO") + " at once and does not count as a "
      "failed attempt — the fault is ours.") + \
    p("<b>The fixed second.</b> The server never answers " + c("CREDENZIALI") + " earlier than " + c("RITARDO_FISSO")
      + " (fixed delay) = 1000 ms after receiving it, " + c("AMMESSO") + " included; the answer leaves from " + c("rcp_tempo()") + " "
      "once both the delay has passed and the verdict is in. The ban removes whoever guesses; the fixed second removes "
      "timing as a channel — without it «no such user» would answer in a millisecond and «wrong password» in fifty. "
      "Not settled yet: PAM's own delay is not constant (median 2636 ms over 42 rejected attempts, bench B8, 10 August "
      "2026), so the fixed second does not fully hide whether a user name exists.") + \
    table(["Rule", "Value", "Constant"], [
        ["Failures that trigger the ban", "3 from the same address", c("SOGLIA") + " (threshold)"],
        ["Window", "5 minutes, sliding over the last three failures", c("FINESTRA") + " (window) = 300 000 ms"],
        ["Ban duration", "12 hours", c("BAN_DURATA") + " = 43 200 000 ms"],
        ["Addresses tracked", "256", c("MAX_TENTATIVI")],
        ["Key", "the address without the port, always in brackets: " + c("[192.168.0.2]"), c("rcp_chiave_indirizzo()") + " (address key)"],
        ["Reset", "a successful authentication from that address, or time", ""],
        ["Persistence", c("--ban-file") + ", default " + c("/var/lib/remotix/ban") + ", absolute expiry times", c("rcp_ban_carica()") + " (load the bans)"],
    ], "«TAB» — The address ban (DECISIONI.md §1.9, decided by the user on 10 August 2026)") + \
    ul([
        "<b>Only failed authentication counts.</b> Not protocol errors, version or codec mismatches (they can come from a "
        "defect of ours or a stale tab), not timeouts, and not " + c("GIA_ATTIVA_REMOTA") + " (already active remotely): counting the latter would let "
        "a user ban themselves by retrying from the phone while their session is alive. The user name does not matter: three "
        "names count three.",
        "<b>A banned address</b> is answered without asking PAM, but still with " + c("RESPINTO(TROPPI_TENTATIVI)")
        + " (too many attempts) after the fixed second — a ban answered in a millisecond would itself be a timing channel. The page is still "
        "served, with the hours left.",
        "<b>The key has no port</b> because there is one attempt per connection and the port changes at every attempt: "
        "bench B5 found that the earlier counter, keyed with the port, was always 1.",
        "<b>Nobody can get someone else banned:</b> reaching " + c("CREDENZIALI") + " requires a completed QUIC handshake, "
        "so the source address cannot be forged.",
        "<b>Unlocking.</b> The ban lives in the memory of the serving process, so a second process that rewrote the file "
        "would leave the server answering " + c("TROPPI_TENTATIVI") + " and exit 0 as if it had worked; " + c("--sblocca")
        + " (unlock) was removed for that reason and now prints why. The live process answers a one-line protocol on a Unix "
        "socket created 0600 with " + c("--comando-socket PATH") + " (command socket): " + c("SBLOCCA <address>")
        + " → " + c("TOLTO") + " (removed) or " + c("NON-BANNATO") + " (not banned), and " + c("PING") + " → " + c("PONG") + ". Every unlock is logged.",
    ]) + \
    warn("the packaged units do not pass " + c("--comando-socket") + ": it is listed among the bench options that "
         + c("costruisci-rpm.sh") + " refuses in a unit. On an installed system the documented way out of a ban is the "
         "12-hour expiry; editing " + c("/var/lib/remotix/ban") + " only takes effect after a restart. Not settled yet: an "
         "unlock command for installed systems.", "Unlock on installed systems.")

# ── ATTACCA / SESSIONE ──────────────────────────────────────────────────
S8 = p(c("ATTACCA") + " asks for a desktop: the canvas the client would like, the view it will draw into and the "
       "keyboard layout. " + c("SESSIONE") + " answers with the canvas actually granted.", lead=True) + \
    code("""ATTACCA
 ├── u32    tela_larghezza       canvas width requested (a preference)
 ├── u32    tela_altezza         canvas height requested
 ├── u32    vista_larghezza      view width: the size the client will draw at, >= 1x1
 ├── u32    vista_altezza        view height
 └── string disposizione         layout (XKB), e.g. it, us, de(neo); <= 64 bytes
SESSIONE
 ├── u8     stato                state: 1 = NUOVA (new), 2 = RIPRESA (resumed)
 ├── u32    tela_larghezza       the GRANTED canvas width
 ├── u32    tela_altezza         and height
 └── string desktop              gnome · kde · xfce · lxqt · sconosciuto (unknown)""", "text", "Bodies") + \
    p("<b>The canvas</b> is the desktop's resolution; the <b>view</b> is the browser area it is drawn into. The canvas "
      "belongs to the session and survives the client; the view belongs to the connection. " + c("tratta_attacca()")
      + " (handle ATTACCA) applies, in order:") + \
    steps([
        "<b>Above the maximum is not an error.</b> A side over " + c("RCP_TELA_L_MASSIMA") + " = 4096 or "
        + c("RCP_TELA_A_MASSIMA") + " = 2304 (in these names L is the width, A the height) is brought to the maximum, the other side unchanged (5120×2880 → 4096×2304, "
        "5120×1440 → 4096×1440), and logged. The page applies the same rule in " + c("tela_da_chiedere()") + " (canvas to ask for), so both "
        "arrive at the same number.",
        "<b>Below the minimum, or odd, is " + c("ERRORE_PROTOCOLLO") + "</b>: 320×240 minimum (" + c("RCP_TELA_L_MINIMA")
        + ", " + c("RCP_TELA_A_MINIMA") + "), both sides even. A view side of 0 is also an error; any view from 1×1 up, odd "
        "included, is legal.",
        "<b>Layout form</b>: " + c("[A-Za-z0-9_-]+") + " optionally followed by " + c("(variant)") + " of the same "
        "alphabet; out of form (including an empty variant " + c("it()") + ") is " + c("ERRORE_PROTOCOLLO") + ". A "
        "well-formed layout the machine does not know (asked to XKB through the " + c("disposizione_esiste") + " hook, «layout exists») is "
        + c("SESSIONE_NON_SERVIBILE") + ". Upper case and underscore are allowed because the system uses them: of 589 "
        "layout/variant pairs on a Debian machine (21 August 2026), 9 have a capital and 102 an underscore.",
        "<b>A local graphical session</b> of the same user (" + c("sessione_locale") + " hook, «local session») → "
        + c("GIA_ATTIVA_LOCALE") + " (already active locally).",
        "<b>The seat.</b> One remote client per user (invariant I2). If the user's seat is held by a live client, the "
        "newcomer gets " + c("GIA_ATTIVA_REMOTA") + " — whoever arrives is refused, never whoever was there. If the holder "
        "has been silent longer than " + c("--sfratto-ms") + " («sfratto» = eviction; default 15 000 ms, half the silence clock) the seat is "
        "taken from it (the «ghost eviction»). If the server's table is full (" + c("--tetto-sessioni") + ", «session cap», default "
        + c("RCP_TETTO_SESSIONI") + " = 10) → " + c("SESSIONE_NON_SERVIBILE") + ".",
        "<b>The decoder cap.</b> If the canvas exceeds " + c("video.misura_massima") + ", it is reduced keeping the "
        "proportions and parity; if not even 320×240 fits, " + c("SESSIONE_NON_SERVIBILE") + ".",
        "<b>The stage wins.</b> If the user's stage already exists at another lawful size (it survives the client), "
        + c("SESSIONE") + " grants that size, so pixels flow at once; the page then asks for its own with "
        + c("ADATTA_TELA") + ".",
        "<b>" + c("SESSIONE") + "</b> says " + c("RIPRESA") + " when the user's stage existed before PAM admitted them, "
        + c("NUOVA") + " otherwise, and names the desktop of this machine. The client must not change behaviour on the "
        "desktop name: it is for diagnosis only.",
    ]) + \
    p("<b>Why 4096×2304.</b> Until 1 October 2026 the maximum was 7680×4320. The user lowered it (phase 19: «4096 max "
      "width is plenty»), and the reason is video: H.264 on the Intel VA-API low-power entry point accepts 32–4096 px per "
      "side (measured 22 August 2026: 4096×2160 yes, 4112×2160 no), and Firefox on Linux only receives H.264. 2304 is "
      "16:9 at 4096 and 4096×2304 is 36 864 macroblocks, exactly the " + c("MaxFS") + " of H.264 levels 5.1 and 5.2. "
      "The change was compatible: no number added or reused, and a client asking more simply receives less.") + \
    p("<b>Why even sides.</b> Encoders work on blocks and 4:2:0 halves chroma; an odd size would be rounded by the encoder "
      "in silence — two sizes under the same label. Better to refuse it where the reason can be said.") + \
    note("three attaches in a row with " + c("ATTACCA(1920×1080)") + " received 1920×1080, 1264×800 and 1600×900 (21 "
         "August 2026): each time, what the previous connection had left. Asking for a canvas in " + c("ATTACCA") + " does "
         "not obtain it; only " + c("ADATTA_TELA") + " changes the canvas.", "The canvas survives the session.")

# ── Deadlines and states ────────────────────────────────────────────────
S9 = p("A connection stuck halfway through the handshake holds a place and declares it to nobody. Each step therefore "
       "has a ceiling, and an expired ceiling ends with " + c("TEMPO_SCADUTO") + " (time expired) — not with QUIC's 30-second idle "
       "timeout, which measures the network rather than a client that does not do its job.", lead=True) + \
    table(["From", "To", "Ceiling", "Where"], [
        ["WebTransport session open", "control channel open", "5 s", c("WT_TETTO_CANALE_NS") + " (no channel: the reason "
         "travels only in the closing code)"],
        ["control channel open", c("CIAO") + " received", "5 s", c("TETTO_CIAO")],
        [c("ECCOMI") + " sent", c("CREDENZIALI") + " received", "60 s — a person typing a password", c("TETTO_CREDENZIALI")],
        [c("CREDENZIALI") + " received", "PAM verdict", "12 s (helper: 8 s)", c("TETTO_VERDETTO")],
        [c("AMMESSO") + " sent", c("ATTACCA") + " received", "10 s", c("TETTO_ATTACCA")],
    ], "«TAB» — Handshake ceilings («tetto» in the constant names = ceiling)") + \
    p("The first ceiling counts from the opening of the control channel, the instant the server really observes; the end "
      "of TLS is not usable, because a second session on a reused connection would start with its budget already spent. "
      "The ceiling before the channel was the last way to hold a place without saying who you are, and was decided by "
      "the user on 11 August 2026 (DECISIONI.md §7.17). The 60 seconds for the password are reachable only because the "
      "server sends transport PINGs while it waits (" + rif("Keep-alive, silence and the dead line") + "). A 10-second "
      "ceiling after " + c("AMMESSO") + " had been written as 60 000 by copying the line above (finding R9.9).") + \
    table(["State (" + c("rcp_stato_nome()") + ")", "Meaning"], [
        [c("attesa-ciao"), "waiting for CIAO: control channel open, " + c("CIAO") + " not yet received"],
        [c("attesa-credenziali"), "waiting for credentials: " + c("ECCOMI") + " sent"],
        [c("attesa-verdetto"), "waiting for the verdict: " + c("CREDENZIALI") + " received; PAM and the fixed second are running"],
        [c("attesa-attacca"), "waiting for ATTACCA: " + c("AMMESSO") + " sent"],
        [c("attiva"), "active: " + c("SESSIONE") + " sent, the seat is held"],
        [c("staccata-per-silenzio"), "detached for silence: silent for 30 s: the seat is released, the connection is still open; if the client "
         "speaks again and the seat is free it becomes " + c("attiva") + " again, otherwise it gets " + c("GIA_ATTIVA_REMOTA")],
        [c("finita"), "ended: a farewell was sent or received; the structure stays alive to judge bytes that arrive afterwards"],
    ], "«TAB» — The seven states of an RCP session")

# ── Video frame ─────────────────────────────────────────────────────────
S10 = p("One stream, one frame. There is no length: the end of the stream is the end of the frame — but only if the "
        "stream ended with a FIN. A reset stream carries an incomplete frame.", lead=True) + \
    code(""" 0      2      4        8        12       16       24       28
 ├──────┼──────┼────────┼────────┼────────┼────────┼────────┼── data …
 │ tipo │codec │ width  │ height │ numero │istante │ input  │
 │ u16  │ u16  │ u32    │ u32    │ u32    │ u64    │ u32    │""", "text", "Video frame header (28 bytes, no padding; tipo = type, "
    "numero = number, istante = instant)") + \
    table(["Field", "Meaning"], [
        [c("tipo"), c("0x0301") + " key frame, " + c("0x0302") + " delta frame (" + c("V_CHIAVE") + ", «chiave» = key, and " + c("V_DELTA")
         + "). Other values are " + c("ERRORE_PROTOCOLLO") + "."],
        [c("codec"), c("1") + " HEVC, " + c("2") + " AV1 (retired, never reused), " + c("3") + " H.264. Must be the "
         "negotiated codec. The highest defined number lives in one place, " + c("RCP_CODEC_VIDEO_MAX") + " = 3: on 20 "
         "August 2026 three guards held the number by hand, one stayed behind, and every H.264 frame was silently dropped "
         "for half an hour."],
        [c("width") + ", " + c("height"), "The size of this frame: in RCP/1 it must equal the canvas in force (granted by "
         + c("SESSIONE") + " or by the last " + c("TELA") + "). The field exists so that encoding smaller than the canvas "
         "would not change the protocol."],
        [c("numero"), "Counter of the frames the server decides to send, +1 each, including those it later abandons and "
         "excluding those it never sends. The first frame is 1; 0 means «no frame»; arithmetic is modulo 2³² and the "
         "wrap goes from " + c("0xFFFFFFFF") + " to 1 (" + c("numero_prossimo()") + ", «next number»)."],
        [c("istante"), "Microseconds of the server's monotonic clock at capture. Not a time of day: compare only with "
         "other " + c("istante") + " values of the same server."],
        [c("input"), "The " + c("id") + " of the last input <i>injected</i> before the capture, 0 if none. It says which "
         "input was injected, not which was drawn; latency is measured by the closed loop, not by this field."],
    ], "«TAB» — Video header fields") + \
    p(c("rcp_video_apri()") + " (open a video frame) writes the header itself: width, height, codec and number are not parameters, so the "
      "rules on them cannot be broken by a caller. The caller passes " + c("chiave") + ", the data length (declared "
      "first, so the cap is checked before a byte leaves), the capture instant and the input id; " + c("rcp_video_pezzo()")
      + " (piece) writes data, " + c("rcp_video_finisci()") + " (finish) ends with FIN only if every declared byte went "
      "out, and " + c("rcp_video_spedisci()") + " (send) does all three. The server must never produce a frame over 16 MiB ("
      + c("V_TETTO") + ", «tetto» = cap): it re-encodes at lower quality and logs it. Measured on 22 August 2026: at a user canvas of "
      "2560×1080 the largest of 404 real key frames was 21 433 bytes, so the cap is unreachable there; at 7680×4320 "
      "uniform noise exceeded it, which is one more reason the maximum canvas is now 4096×2304.") + \
    table(["Outcome", "Meaning"], [
        [c("RCP_VIDEO_SPEDITO"), "sent"],
        [c("RCP_VIDEO_NIENTE_CANALE"), "the host has no video hooks"],
        [c("RCP_VIDEO_PRIMA_DI_SESSIONE"), c("SESSIONE") + " not sent yet (invariant I3)"],
        [c("RCP_VIDEO_SERVE_UNA_CHIAVE"), "a key frame is owed: first after " + c("SESSIONE") + ", first at a new canvas, "
         "or requested"],
        [c("RCP_VIDEO_TROPPO_GRANDE"), "over 16 MiB: re-encode; nothing left"],
        [c("RCP_VIDEO_STREAM_NON_APERTO"), "no stream credit now: nothing left (logged by " + c("rcp_video_niente_credito()") + ", «no credit»)"],
        [c("RCP_VIDEO_ROTTO_A_META"), "a write failed halfway: the stream was reset"],
        [c("RCP_VIDEO_GIA_APERTO"), "another frame of this session is still open"],
    ], "«TAB» — The outcomes of rcp_video_apri() and rcp_video_spedisci()") + \
    ul([
        "The client discards a frame whose " + c("numero") + " precedes the last one delivered to the decoder "
        "(signed difference modulo 2³²) — and this ordering rule applies before the size rule.",
        "A stream closed with FIN before the 28 bytes is " + c("ERRORE_PROTOCOLLO") + ", not a short frame.",
        "A frame at a size never in force is held while an " + c("ADATTA_TELA") + " sent by the client is unanswered, and "
        "re-judged when the " + c("TELA") + " arrives; with no request in flight it is " + c("ERRORE_PROTOCOLLO") + " at once.",
    ]) + \
    note("RCP.md §6.2 requires the client to cap the frames it holds and to drop the oldest as a gap when the cap is "
         "exceeded. The page has no such cap (it counts held frames but never drops them), and the specification leaves "
         "the number open. Not settled yet: the cap.", "Held frames.")

# ── Key frames ──────────────────────────────────────────────────────────
KEYS = table(["Form", "What the client sees", "When it happens", "What the server owes"], [
    ["A — reset stream", "a stream ending with " + c("RESET_STREAM") + " instead of FIN", "at least one byte of the frame had left",
     "log it; next frame a key"],
    ["B — gap in " + c("numero"), "no stream, and the next " + c("numero") + " skips", "the number was consumed and the "
     "frame abandoned before a byte left", "log it; next frame a key"],
    ["C — never sent", "nothing at all", "dropped before the wire (no credit, pace regulator, canvas mismatch)",
     "a key frame on its own: the client cannot ask (" + c("rcp_video_scartato_prima_del_filo()") + ", «dropped before "
     "the wire»)"],
], "«TAB» — The three forms of a lost frame")

S11 = p("Video is compressed with prediction between frames: losing a delta frame ruins every following frame until a "
        "key frame arrives, and a decoder fed a missing delta raises no error — it paints progressively more broken "
        "images. Abandoning a frame is cheap only if the cure, a key frame, is guaranteed.", lead=True) + KEYS + \
    ul([
        "The first frame after " + c("SESSIONE") + " must be a key frame, and so must the first frame at a new canvas — a "
        "real one, with its parameter sets in front. Measured on 12 August 2026 (Chrome 151, VA-API): an HEVC decoder "
        "given a delta at the new size raises nothing and keeps emitting frames at the old size.",
        "The client reconfigures its decoder on the first <i>key frame</i> at the new size, not on the " + c("TELA") + " "
        "message; a " + c("VideoDecoder") + " reconfigured early demands a key frame anyway.",
        "The server never abandons a key frame (" + c("rcp_video_abbandona()") + ", «abandon», and " + c("rcp_video_abbandonato_a_valle()")
        + ", «abandoned downstream», refuse and log). Abandoning the cure is not a cure.",
        "While a key frame is still in the send queue, the deltas behind it are not abandoned for the queue threshold: "
        "they would not shorten it, and each one would open a gap asking for another key (22 September 2026, the spiral "
        "seen with a 4K video).",
        "The client sends " + c("RICHIEDI_CHIAVE") + " with " + c("ultimo_numero") + " (last number: the last decoded frame, 0 if none) on a "
        "gap or a decoder error — one per gap, and another after 1 s without a key, never one per frame.",
        "The server may ignore a request within " + c("V_GRAZIA_CHIAVE") + " (key grace) = 200 ms of the last key it <i>sent</i> — "
        "counting from requests instead, insistent clients would push the clock forever. But a request whose "
        + c("ultimo_numero") + " is at or after the last key frame says the gap came after it, and is always served (22 "
        "September 2026: ignoring it left the page frozen for good).",
        "Until a key frame arrives the client shows the last good image: a frozen image for a tenth of a second is better "
        "than a broken one.",
    ]) + \
    p("Temporal sub-layers, which would allow dropping frames without breaking anything, were checked on 22 August 2026: "
      "the Intel low-power encoder does not offer them (7 profiles out of 7), and B-frames cost 67 ms of reordering. "
      "So «every abandonment costs a key frame» stands, and the remedy on a line that keeps abandoning is to lower the "
      "frame rate, not to send keys in a loop.")

# ── Canvas changes ──────────────────────────────────────────────────────
S12 = p(c("ADATTA_TELA") + " is the only message that changes the canvas. Since 17 August 2026 the page sends it only at "
        "attach and re-attach, with the size of its own window — live resizing left the product (DECISIONI.md §5.1-bis). "
        "The protocol still admits it at any time, from anyone, and the server must always answer.", lead=True) + \
    code("""ADATTA_TELA                        client → server
 ├── u32 larghezza      width
 └── u32 altezza        height
TELA                               server → client
 ├── u8  esito          outcome: 1 = ADATTATA (adapted), 2 = RIFIUTATA (refused)
 ├── u8  motivo         reason: 0 if adapted; 1 = COMPOSITORE_INCAPACE (compositor
 │                      cannot), 2 = MISURA_FUORI_LIMITI (size out of limits),
 │                      3 = NON_ORA (not now)
 ├── u32 tela_larghezza the canvas in force AFTER this message
 └── u32 tela_altezza
VISTA (view)                       client → server
 ├── u32 larghezza      any size from 1x1, odd included
 └── u32 altezza""", "text", "Bodies") + \
    steps([
        "<b>Admissible size.</b> " + c("rcp_misura_ammessa()") + " (admissible size) brings each side over the maximum to the maximum and "
        "truncates to even; below 320×240 → " + c("TELA(RIFIUTATA, MISURA_FUORI_LIMITI)") + ". The decoder cap of the "
        "client also applies. The guard is mandatory: beyond 16 384 per side " + c("gnome-shell") + " dies, and labwc at "
        "32768×32768 dies with no log line (14 August 2026).",
        "<b>The request goes to the stage</b> through the " + c("ritela") + " hook («re-canvas»). Its " + c("true") + " means only «asked»: "
        "labwc answers success for a size it already has without any event, and a compositor may grant another size. No "
        "hook → " + c("TELA(RIFIUTATA, COMPOSITORE_INCAPACE)") + ".",
        "<b>The proof is a frame.</b> The child answers with the size asked and the size obtained ("
        + c("rcp_tela_dal_palco()") + ", «canvas from the stage»); " + c("TELA(ADATTATA)") + " leaves when a frame at the new size exists, which "
        "opens the key-frame debt and the one-second grace. Zero obtained → " + c("NON_ORA") + " at once.",
        "<b>The answer is never silence.</b> If no proof arrives within " + c("RCP_TELA_ATTESA_MS") + " (wait) = 3000 ms the server "
        "answers " + c("NON_ORA") + "; the child can postpone that deadline while the stage is still being born ("
        + c("rcp_tela_rimanda()") + ", «postpone»), which cured black bands after a logout on 16 August 2026. Resizing itself took 41.6 "
        "ms on Mutter and 5.1 ms on labwc (14 August 2026).",
        "<b>A stage elsewhere on its own</b> is recalled to the canvas in force every " + c("RCP_TELA_RICHIAMO_MS")
        + " (recall) = 500 ms, doubling up to " + c("RCP_TELA_RICHIAMO_MAX_MS") + " = 8000 ms. An unsolicited " + c("TELA")
        + " is forbidden — except one, before the first frame of the session has left (since 22 September 2026): after a "
        "server restart a KWin " + c("--virtual") + " stage that cannot resize would otherwise leave the screen black forever.",
    ]) + \
    p("<b>The grace second.</b> After " + c("TELA(ADATTATA)") + " the server accepts for " + c("TELA_GRAZIA") + " (canvas grace) = 1000 ms "
      "input coordinates valid on the previous canvas, clamping them to the new one and logging it; after that they are "
      "violations. It is the only moment when the two sides legitimately hold two truths. " + c("rcp_tela_adattata_ora()")
      + " («canvas adapted, now») opens it; " + c("rcp_tela_adattata()") + " has no clock and declares that it does not.") + \
    p("<b>" + c("VISTA") + "</b> updates the view and must not change the canvas; in RCP/1 it does not even change what is "
      "encoded — the server sends the whole canvas and the client scales. The server validates it, keeps it for the bit "
      "budget and logs it. " + c("DISPOSIZIONE") + " (layout; " + c("0x0009") + ", one string in the " + c("ATTACCA") + " form) "
      "changes the keyboard layout without detaching; an unknown but well-formed layout is logged and the previous one "
      "stays in force, because the open work is worth more than the fault. The current page sends neither: the layout "
      "and the window size are renegotiated at each attach.")

# ── Input ───────────────────────────────────────────────────────────────
S13 = p("The input channel is one unidirectional stream opened by the client after " + c("SESSIONE") + ". Every "
        "message starts with the same two fields; the five types have fixed lengths.", lead=True) + \
    code("""common:          u32 id        increasing over the whole channel, starts at 1; 0 is reserved
                 u64 istante   microseconds of the CLIENT's monotonic clock
PUNTATORE        + u32 x · u32 y              canvas pixel indices        (20 bytes)
PULSANTE         + u16 codice · u8 premuto    evdev code; 1 down, 0 up    (15 bytes)
ROTELLA          + i32 asse_x · i32 asse_y    120 units per notch         (20 bytes)
LETTERA          + u32 carattere              Unicode scalar value        (16 bytes)
POSIZIONE_TASTO  + u16 codice · u8 premuto    evdev key code              (15 bytes)""", "text",
         "Input bodies (0x0101–0x0105): PUNTATORE = pointer, PULSANTE = button, ROTELLA = wheel, LETTERA = "
         "character, POSIZIONE_TASTO = key position; codice = code, premuto = pressed, asse = axis, carattere = character") + \
    ul([
        "<b>Codes are evdev's</b> (" + c("BTN_LEFT") + " = " + c("0x110") + ", " + c("KEY_A") + " = 30): " + c("libei") + " "
        "works in evdev, and any other convention would add a translation table that fails in silence.",
        "<b>Coordinates are canvas pixel indices</b>: " + c("0 ≤ x < width") + "; on 1920×1080 the bottom-right pixel is "
        "1919, 1079. The client converts from its view rounding down; the server applies no transformation and rejects "
        "out-of-range values, except during the grace second.",
        "<b>The wheel</b> uses 120 units per notch and half notches (60) must not be rounded away. The sign was measured "
        "on 10 August 2026 on Mutter: the client sends +120 when the user turns the wheel up, and the server must invert "
        "the vertical axis before " + c("ei_device_scroll_discrete") + ". The inversion happens once, inside "
        + c("input_rotella()") + " (wheel input) — never in " + c("rcp.c") + ", where a second inversion would cancel it.",
        "<b>" + c("LETTERA") + " for text, " + c("POSIZIONE_TASTO") + " when a command modifier is held</b> (Ctrl, Alt, "
        "Super); Shift and AltGr make letters and stay on the " + c("LETTERA") + " path. A character outside "
        + c("0..0x10FFFF") + " or a surrogate is " + c("ERRORE_PROTOCOLLO") + "; a character the session's layout cannot "
        "produce is logged and never replaced by another.",
        "<b>The " + c("id") + "</b> grows by at least one per message across all five types — it is what comes back in the "
        "frame's " + c("input") + " field — and " + c("premuto") + " other than 0 or 1 is a violation.",
        "<b>The " + c("istante") + "</b> is consumed by no rule; it records when the hand moved, for diagnosis. The page "
        "writes real microseconds (" + c("performance.now()") + " has 5 µs grain when the page is cross-origin isolated).",
    ]) + \
    warn("when a connection ends — farewell, silence or error — the server must release every key and button still down. "
         "A Ctrl left pressed in a session that survives the client makes the desktop unusable at the next attach, and "
         "nobody connects the two. The " + c("input_rilascia_tutto") + " hook («release everything») answers a true "
         "count, " + c("RCP_RILASCIO_SENZA_CONTO") + " (release without a count: asked; the child knows the count and logs "
         "it) or " + c("RCP_RILASCIO_IMPOSSIBILE") + " (release impossible: could not ask: whatever was down stays down). Until 16 August 2026 it answered "
         "0, logged as «nothing was down», while the child released two.", "Release everything at detach.")

# ── Cursor and clipboard ────────────────────────────────────────────────
S14 = p("The pointer position belongs to the client, which draws the pointer itself; only the shape travels, on the "
        "control channel. The clipboard is plain UTF-8 text in both directions, announced first and pulled on demand.",
        lead=True) + \
    code("""CURSORE_FORMA   0x000A   cursor shape; server → client, control channel
 ├── u16 larghezza      width <= 256; 0 with altezza 0 = hidden cursor
 ├── u16 altezza        height <= 256
 ├── i16 attivo_x       hotspot, 0 <= attivo_x < larghezza; 0 when hidden
 ├── i16 attivo_y
 └── image              larghezza x altezza x 4 bytes, premultiplied BGRA, no row padding
                        message length = 8 + larghezza x altezza x 4 exactly""", "text", "Cursor shape") + \
    p(c("rcp_cursore_forma()") + " (cursor shape) takes the number of bytes really available behind the image and refuses to send rather "
      "than read on trust: a malformed message would make the <i>page</i> close the session, and the server's log would "
      "know nothing. The limits themselves are enforced once, in " + c("cursore.c") + ". The function is called from the "
      "loop thread, never from PipeWire's real-time thread.") + \
    code("""APPUNTI_ANNUNCIO  0x0201  ├── u32 trasferimento   chosen by whoever announces, from 1
                          └── u32 lunghezza       bytes of text available
APPUNTI_CHIEDI    0x0202  └── u32 trasferimento   the announcement being answered
APPUNTI_TESTO     0x0203  ├── u32 trasferimento   the request being served
                          └── bytes               to the end of the message, valid UTF-8""", "text", "Clipboard messages "
    "(APPUNTI = clipboard: ANNUNCIO = announcement, CHIEDI = request, TESTO = text; trasferimento = transfer, "
    "lunghezza = length)") + \
    ul([
        "Each side numbers its own transfers; an " + c("APPUNTI_CHIEDI") + " matching no live announcement, or an unrequested "
        + c("APPUNTI_TESTO") + ", is " + c("ERRORE_PROTOCOLLO") + ". A request that arrives after a newer announcement is "
        "served with the current text and logged — two people copying is a race, not an error.",
        "The transfer id exists because the three messages travel in both directions on unidirectional streams: without it "
        "two transfers open at once in opposite directions swapped their texts (finding R1.11).",
        "Cap " + c("RCP_APPUNTI_TETTO") + " (clipboard cap) = 1 000 000 bytes, not 1 MiB, so that a text exactly at the cap still fits in a "
        "1 MiB message with its 10 bytes of overhead. Longer text is not announced at all, and logged: a truncated text "
        "pasted into a terminal is worse than a missing one.",
        "One stream per message (DECISIONI.md §5-ter.7): an announcement and its text can be far apart in time, and a "
        "stream kept open between them would stay open forever in most cases. The server keeps at most " + c("A_STREAM_MAX")
        + " = 8 clipboard streams alive and drops the oldest idle one, logged; pending paste requests time out after "
        + c("APPUNTI_FONDO") + " (clipboard deadline) = 8000 ms.",
    ])

# ── Audio ───────────────────────────────────────────────────────────────
S15 = p("Audio travels only on datagrams, one block per datagram, with no retransmission and no reordering: the "
        "receiver discards blocks that arrive after ones already played.", lead=True) + \
    code(""" 0      2      4                12
 ├──────┼──────┼────────────────┼── samples …
 │ tipo │codec │ istante        │
 │ u16  │ u16  │ u64            │""", "text", "Audio datagram header (12 bytes), after the WebTransport prefix") + \
    table(["", "Value"], [
        [c("tipo"), c("0x0401") + ", the only one defined"],
        [c("codec"), c("1") + " Opus, " + c("2") + " PCM — not the video numbering: 1 is HEVC there and Opus here"],
        [c("istante"), "server monotonic microseconds of the first sample"],
        ["Sample rate, channels", "48 000 Hz, 2 interleaved, for both codecs"],
        ["Opus", "one packet per datagram, 20 ms blocks"],
        ["PCM", "s16 little-endian, 5 ms per datagram: 240 frames (480 samples), 960 bytes, 972 with the header"],
    ], "«TAB» — Audio format (fixed, not negotiated)") + \
    p("PCM is little-endian on purpose: it is payload, like the HEVC bytes, not a protocol field — the only declared "
      "exception to network order. Its 5-ms blocks are a correction of 9 August 2026: at 20 ms a PCM datagram would have "
      "been 3852 bytes and would never have left on any network, and PCM is the positive control for Opus. A datagram "
      "shorter than 12 bytes or with another " + c("tipo") + " is discarded and logged, not fatal (exception 2). Volume "
      "does not travel: it belongs to the session (invariant I5).")

# ── Bench marker ────────────────────────────────────────────────────────
S16 = p(c("BANCO_MARCA") + " (bench marker) and " + c("BANCO_ESITO") + " (bench outcome) were added on the night of 9 August 2026 for the latency bench: "
        "the bench asks the server to paint a 16×16 square of a given colour after a known delay, and checks that the "
        "measured median rises by exactly that delay.", lead=True) + \
    code("""BANCO_MARCA   0x000F   client → server
 ├── u32 id          grows by at least 1; 0 reserved
 ├── u32 colore      colour, 0x00RRGGBB
 └── u32 ritardo_ms  delay, 0..10000
BANCO_ESITO   0x0010   server → client
 ├── u32 id
 ├── u8  esito       outcome: 1 = ACCETTATA (accepted), 2 = RIFIUTATA (refused)
 ├── u8  motivo      reason: 0; 1 = FUNZIONE_SPENTA (function off),
 │                   2 = RITARDO_FUORI_LIMITI (delay out of range)
 └── u64 istante     server microseconds when painted; 0 if refused""", "text", "Bodies") + \
    p("In the product " + c("BANCO_ACCESO") + " (bench on) is 0: " + c("ECCOMI") + " declares " + c("banco.marca=no") + ", and every "
      + c("BANCO_MARCA") + " in state " + c("attiva") + " is answered " + c("BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)") + " — "
      "or " + c("RITARDO_FUORI_LIMITI") + " above 10 000 ms — never silence and never a close. The accepting branch has "
      "never been completed: the known-delay check of phase 3 was done outside the product (N = 25 → +25.08 ms, N = 60 → "
      "+58.58 ms) and is better that way, because the clock anchor does not pass through the injected path.") + \
    warn("DECISIONI.md §7.16 (11 August 2026) says the bench function must be absent from the delivered binary — not "
         "compiled, not findable by searching its marks. The code still compiles it in, switched off. Not settled yet: "
         "whether to complete the accepting branch or to remove the two types, whose only declared reason was met "
         "without them.", "Present, not absent.")

# ── TERMINA_SESSIONE ────────────────────────────────────────────────────
S17 = p(c("TERMINA_SESSIONE") + " (end the session; " + c("0x0011") + ", empty body) is the only message by which the client ends the "
        "<i>session</i>: the graphical session finishes and the user's programs close. " + c("CONGEDO") + " closes only "
        "the connection and leaves the session alive (invariant I4). The two exits are DECISIONI.md §4.1-ter; a client "
        "with a single way out would force the user to choose between never leaving and losing their work.", lead=True) + \
    ul([
        "The page sends it only after an explicit gesture: the " + c("Ctrl+Alt+End") + " shortcut and its confirmation. "
        "«Log out» from the desktop's own menu does not pass through here; the child reports it and the parent dismisses "
        "every client of that user with " + c("SESSIONE_TERMINATA") + " (session ended).",
        "Valid only in states " + c("attiva") + " or " + c("staccata-per-silenzio") + "; elsewhere " + c("ERRORE_PROTOCOLLO") + ".",
        "The answer is " + c("CONGEDO(0x10 SESSIONE_TERMINATA)") + ", sent <i>before</i> the session finishes dying — when "
        "the compositor falls the stage falls with it — and then the " + c("termina_sessione") + " hook is called. All "
        "connections of that user receive it, not just the one that asked. Without the hook the client is still "
        "dismissed with " + c("0x10") + " and the log says the session was not touched.",
        "There is no «terminating» reply: the outcome is the farewell. A client that receives " + c("0x10") + " must not "
        "re-attach; it would open a new session, not find the old one. The page returns to the login form.",
    ])

# ── Farewell ────────────────────────────────────────────────────────────
BYE1 = seq([("Page", "pagina.html", "dark"), ("Server", "rcp.c + webtransport.c", "navy")], [
    ("sep", "the server closes (violation, timeout, shutdown …)"),
    ("nota", 1, "1. log what happened"),
    (1, 0, "CONGEDO(reason, detail)  — if the control channel is usable", True),
    ("nota", 1, "release keys and buttons, free the seat"),
    ("nota", 1, "wait for the queue to drain, then 500 ms"),
    (1, 0, "CLOSE_WEBTRANSPORT_SESSION(code = reason)", True),
    ("nota", 0, "shows the sentence for the reason, never the detail"),
    ("sep", "the page closes (tab closed, protocol error …)"),
    (0, 1, "CONGEDO(reason, detail)"),
    (0, 1, "CLOSE_WEBTRANSPORT_SESSION(code = reason)"),
    ("nota", 1, "codes outside 0x01..0x0F logged as ERRORE_PROTOCOLLO"),
], "«FIG» — The farewell in both directions: two roads for the same reason", width=900)

BYE2 = seq([("Side A", "closes", "navy"), ("Side B", "receives the FIN", "dark")], [
    (0, 1, "FIN on the control channel"),
    ("nota", 1, "the session is over: send nothing more, not even CONGEDO"),
    ("nota", 1, "the reason arrives in A's closing code"),
], "«FIG» — Whoever receives the FIN stays silent (DECISIONI.md §7.14)", width=900)

S18 = p("Whoever closes must send " + c("CONGEDO") + " with a reason before closing the WebTransport session, if the "
        "control channel is still usable, and must repeat the reason in the session's application error code. The "
        "second road has no condition: it travels inside the close itself. The farewell is always verified from the side "
        "that receives it.", lead=True) + \
    code("""CONGEDO   0x000C   both directions
 ├── u8     motivo     a reason of the table below (code 0 is forbidden)
 └── string dettaglio  detail, for the log, never shown to the user; may be empty""", "text", "Body") + BYE1 + BYE2 + \
    ul([
        "<b>The condition</b> (DECISIONI.md §7.15, decided by the user on 11 August 2026): «if a connection drops nobody "
        "can tell the server "
        "<i>I am closing because I have finished</i>». A rule that cannot be obeyed is a defect of the document; what is "
        "lost is only a byte on a dead channel, and the reason still arrives by the second road.",
        "<b>Whoever receives a FIN is not «whoever closes»</b> and sends nothing more on any channel (§7.14). The decision "
        "was made by a measurement: on 10 August 2026 Chrome dropped a message sent just before closing the session, so a "
        "farewell owed by the receiver would have been a rule one engine out of two cannot honour.",
        "<b>The one exception is " + c("RESPINTO") + "</b>, which is itself the farewell of authentication.",
        "<b>The page builds the sentence</b> from the code; " + c("dettaglio") + " is for whoever diagnoses. Every reason "
        "must be expressible to the user as a sentence: " + c("BUDGET_PIENO") + " is not «error 6».",
        "<b>A second farewell is never sent.</b> " + c("rcp_congeda()") + " (dismiss) on a session already ended does nothing: two "
        "reasons for one fact would be two truths. Bytes arriving after the end are judged by " + c("giudica_dopo_la_fine()")
        + ": a single " + c("CONGEDO") + " is a legitimate leave-taking, anything more is logged.",
        "<b>The seat is released immediately</b> on a client close (" + c("rcp_chiusa_dal_client()") + ", «closed by the client»), without waiting "
        "for the transport to finish tearing down — otherwise whoever reconnects at once would find it taken.",
    ])

# ── Reasons ─────────────────────────────────────────────────────────────
S19 = p("The reasons are a single numbering shared by " + c("CONGEDO") + ", " + c("RESPINTO") + " and the WebTransport "
        "closing code (" + c("enum") + " in " + c("rcp.h") + ").", lead=True) + \
    table(["Code", "Name", "When", "Sent by"], [
        [c("0x01"), c("CHIUSO_DALL_UTENTE") + " (closed by the user)", "the user closed the client: the wire falls, the session stays («re-attach and "
         "find everything»)", "page"],
        [c("0x02"), c("INATTIVITA") + " (inactivity)", "30 minutes without input; re-entry needs the password", c("rcp_tempo()") + ", "
         + c("--inattivita-s") + " (0 = off)"],
        [c("0x03"), c("SESSIONE_ABBANDONATA") + " (session abandoned)", "60 minutes without input: the graphical session is closed (was «6 hours "
         "without attaches» until 16 August 2026)", c("main.c") + ", " + c("--abbandono-s") + " («abandonment»)"],
        [c("0x04"), c("SESSIONE_LOCALE_PREVALSA") + " (local session prevailed)", "the user opened a local graphical session", c("webtransport.c") + ", "
         "periodic survey of local sessions"],
        [c("0x05"), c("GIA_ATTIVA_LOCALE"), "a local graphical session of the user already exists", c("tratta_attacca()")],
        [c("0x06"), c("BUDGET_PIENO"), "the machine has no composition capacity left (corrected from «encoding» on 24 "
         "August 2026: the bottleneck measured was the render engine)", "capacity gate in " + c("main.c")],
        [c("0x07"), c("CREDENZIALI_ERRATE"), "authentication failed", c("RESPINTO")],
        [c("0x08"), c("TROPPI_TENTATIVI"), "the address is banned", c("RESPINTO")],
        [c("0x09"), c("NIENTE_IN_COMUNE"), "no shared codec, depth or audio codec", "server or page"],
        [c("0x0A"), c("VERSIONE_INCOMPATIBILE"), "the versions do not match", "server or page"],
        [c("0x0B"), c("ERRORE_PROTOCOLLO"), "§3", "both"],
        [c("0x0C"), c("SERVER_IN_CHIUSURA") + " (server closing)", "the server is shutting down", c("main.c")],
        [c("0x0D"), c("TEMPO_SCADUTO"), "a handshake ceiling expired", c("rcp.c") + ", " + c("webtransport.c")],
        [c("0x0E"), c("SESSIONE_NON_SERVIBILE"), "well-formed attach that cannot be served: unknown layout, table full, all "
         "stages taken, stage failed, decoder cap below 320×240", "server"],
        [c("0x0F"), c("GIA_ATTIVA_REMOTA"), "another live client of the same user holds the seat; the newcomer is refused",
         c("tratta_attacca()")],
        [c("0x10"), c("SESSIONE_TERMINATA"), "the user logged out: nothing to re-attach to, the page returns to the login "
         "form", c("rcp.c") + ", " + c("main.c")],
    ], "«TAB» — Disconnect reasons (RCP.md §8.2)") + \
    p(c("0x01") + " and " + c("0x10") + " describe two gestures with opposite outcomes: the wire that falls carries the "
      "promise «re-attach and you find everything», the logout makes that promise false. " + c("0x0F") + " is the remote "
      "twin of " + c("0x05") + " and applies invariant I2 to the letter: the second connection is refused with an explicit "
      "message. The boundary with «whoever is silent is detached» is the silence clock: a client silent for 30 s holds "
      "nothing, so the newcomer enters; the declared price is that after a laptop dies without a farewell the phone "
      "enters after 30 s — 15 s with the ghost eviction.") + \
    note("the server accepts a " + c("CONGEDO") + " or a closing code from the client only in " + c("0x01") + "–"
         + c("0x0F") + " (" + c("motivo_di_82()") + ", «a reason of §8.2», and the range check in " + c("webtransport.c") + "): a client "
         "sending " + c("0x10") + " would be treated as " + c("ERRORE_PROTOCOLLO") + ", although §8.2 defines it. Harmless "
         "today — only the server sends " + c("0x10") + " — but it is a divergence from the specification.", "Range check.")

# ── Clocks ──────────────────────────────────────────────────────────────
S20 = p("Three clocks govern an attached session (SPECIFICHE.md §5.3), and a fourth rule shortens the first one when "
        "somebody is waiting for the seat. The values in force are written to the log at start-up, because a one-hour "
        "ceiling cannot be verified by waiting an hour.", lead=True) + \
    table(["Clock", "Default", "Looks at", "Effect", "Option"], [
        ["Silence", "30 s (" + c("SILENZIO") + ")", "last authenticated packet from the client", "detached: seat freed, no "
         "farewell, connection left open; keys released", "—"],
        ["Ghost eviction", "15 s (" + c("SFRATTO_PREDEFINITO") + ")", "silence of the seat holder, only while the same "
         "user is asking for the seat", "the seat moves to the newcomer", c("--sfratto-ms") + " (0 = off)"],
        ["Inactivity", "30 min (" + c("INATTIVITA_PREDEFINITA") + ")", "the last RCP byte from the client on control, input or clipboard (" + c("ultimo_byte") + ", «last byte»)", c("CONGEDO(0x02)"),
         c("--inattivita-s") + " (0 = off)"],
        ["Abandonment", "60 min (" + c("ABBANDONO_PREDEFINITO_MS") + ")", "the last of the five input gestures forwarded to the child", "the graphical session is "
         "closed, " + c("0x03"), c("--abbandono-s")],
    ], "«TAB» — The session clocks") + \
    p("The ghost eviction exists because on 23 August 2026 a client killed with " + c("-9") + " kept its seat for 30.5 s "
      "and eleven reconnection attempts were refused with «you already have a session elsewhere» — about the user's own "
      "dead session. Lowering the silence clock to 10 s would have broken a reader who only watches: the browser's "
      "keep-alive was measured at 15 s. The eviction acts only within the same user (across users it would be a security "
      "hole), only when someone is asking, and never below 15 s, the point beyond which no live client was ever "
      "measured. Measured on 23–24 August 2026: the ghost went from 32.13 s and 14 refusals to 16.83 s and 7.") + \
    note("SPECIFICHE.md §5.3 defines inactivity as «what the user sends, not what they watch». The code refreshes the "
         "30-minute clock on any RCP byte from the client, so automatic messages such as " + c("RICHIEDI_CHIAVE")
         + " also keep it alive; the 60-minute abandonment clock counts only the five input gestures.",
         "Inactivity counts more than input.")

# ── Versions ────────────────────────────────────────────────────────────
S21 = p("The major version lives in two places, and they must coincide: the path " + c("/rcp/1") + " and the "
        + c("versione") + " field of " + c("CIAO") + ". A " + c("CIAO(2)") + " on " + c("/rcp/1") + " is "
        + c("VERSIONE_INCOMPATIBILE") + ", not a negotiation.", lead=True) + \
    ul([
        "The path is the most upstream place where the server can say «I do not speak this version», since ALPN is "
        + c("h3") + " and belongs to the browser. An unknown path gets 404. The check in " + c("CIAO") + " remains "
        "mandatory: a path can be typed by hand, and a check that can be bypassed by typing is not a check.",
        "Within a major version RCP grows only through capabilities — never by adding fields to existing messages or new "
        "types the old side would have to ignore, because ignoring is forbidden. A new mandatory type is a new major "
        "version.",
        "The window in which the document could still be completed closed with the first byte of code, 10 August 2026. "
        "It let through four types (" + c("RICHIEDI_CHIAVE") + ", " + c("TELA") + ", " + c("BANCO_MARCA") + ", "
        + c("BANCO_ESITO") + ") and three reasons (" + c("TEMPO_SCADUTO") + ", " + c("SESSIONE_NON_SERVIBILE") + ", "
        + c("GIA_ATTIVA_REMOTA") + ").",
    ]) + \
    warn(c("TERMINA_SESSIONE") + " (" + c("0x0011") + ") and " + c("SESSIONE_TERMINATA") + " (" + c("0x10") + ") entered on 15 "
         "August 2026, after the window had closed, without a version change. Client and server are updated together "
         "today, so nothing breaks; but RCP.md §9 still says the window let through only four types and three reasons, "
         "and does not record this exception.", "A type added after the window closed.")

# ── What RCP does not do ────────────────────────────────────────────────
S22 = p("What RCP/1 deliberately leaves out, so that nobody looks for it on the wire.", lead=True) + \
    table(["RCP does not …", "Where it is said"], [
        ["carry files, disks, printers or ports", "SPECIFICHE.md §12"],
        ["carry images in the clipboard", "RCP.md §7.4"],
        ["have a relative-pointer channel", "reserved; until an application that captures the pointer needs it"],
        ["carry stylus or multi-touch", c("input.tocco") + " exists and is always " + c("no")],
        ["carry the microphone", "the direction is foreseen, the format is not; it would be a new major version"],
        ["compress on its own", "the codec compresses, QUIC encrypts"],
        ["have an application heartbeat", "forbidden: QUIC's idle timeout and PINGs already do it, and a second mechanism "
         "would be two truths about the same fact"],
        ["have a clear-text mode", "RCP.md §2"],
        ["carry the volume", "it belongs to the session (invariant I5)"],
        ["describe more than one screen", "the canvas is one; multi-monitor is out of scope"],
        ["carry 4:4:4 chroma", "would be a capability " + c("video.sottocampionamento") + " (subsampling); the product decision is open"],
    ], "«TAB» — Outside RCP/1")

# ── Testing ─────────────────────────────────────────────────────────────
S23 = p("Client and server are tested against the specification, not against each other. The decisive tool is the wire "
        "validator, a third program that reads a recording of a connection and says which byte does not conform.",
        lead=True) + \
    table(["Bench", "What it proves"], [
        [c("01-b3-cliente.py"), "the handshake written a second time, in Python, from " + c("RCP.md") + " alone; it can "
         "record the wire"],
        [c("01-b4-validatore.py"), "the referee: exit 0 conforming (with the denominator), 1 not conforming (offset and "
         "rule), 2 broken recording, 3 nothing to judge; it is first given a recording with an error in it, to prove it "
         "can see one"],
        [c("01-b5-violazioni.py") + " (violations)", "rigor towards the server: unknown types, wrong "
         "lengths, wrong states — the connection must fall every time"],
        [c("01-b6-tetti.py") + " (ceilings)", "the handshake ceilings, measured by keeping silent"],
        [c("01-b7-congedo.py"), "the farewell, read from the receiving side, reason by reason, including the closing code"],
        [c("01-b8-cronometro.py") + " (stopwatch)", "the fixed second (successful answers too) and the address ban: the fourth attempt is "
         "refused even with the right password, three different user names count, another address still enters, a "
         "success resets, and the ban survives a restart"],
        [c("01-b9-letture.py") + " (readings)", "the places where " + c("RCP.md") + " admitted two readings, with the bytes compared"],
        [c("01-b11-guasto-innesta.py") + " (graft a fault)", "a server broken on purpose, against real browsers"],
        [c("01-b12-guasti.py") + " (faults)", "a hand-built fault for every bench: a bench that cannot go red certifies nothing"],
        [c("02-filo-cliente.py") + ", " + c("02-filo-validatore.py") + " («filo» = wire)", "the video channel: receiving and judging frames"],
    ], "«TAB» — The benches of the protocol (folder banchi/)") + \
    code("""header (16 bytes)
 ├── 8 bytes  magic          "RCPREG" 0x00 0x03
 ├── u32      block count
 ├── u8       clock          1 = client's, 2 = server's
 └── u8[3]    reserved, 0
each block
 ├── u8  direction (1 c→s, 2 s→c) · u8 channel (high byte) · u8 end (0 continues, 1 FIN, 2 RESET_STREAM)
 ├── u32 istante_ms          milliseconds since the first block, recorder's monotonic clock
 ├── u64 stream · u32 length (the TRUE length)
 ├── u16 redacted ranges, each: u32 start · u32 count · 32-byte SHA-256 of the true bytes
 └── payload (redacted bytes replaced by 0x2A)""", "text", "Recording format (RCP.md §11.1)") + \
    p("The format solves one problem: recording the bytes as they were would put the password in a file, and replacing "
      "it while keeping or rewriting the length would make the validator either fail forever or validate a document "
      "rewritten by the bench. So the true length is kept, the secret bytes are replaced by " + c("0x2A") + " (not zeros, "
      "which a field can legitimately contain) and the file declares which ranges are redacted, with their fingerprint. "
      "The " + c("end") + " byte (added 12 August 2026) lets the validator tell an abandoned frame from a truncated one; "
      + c("istante_ms") + " (magic " + c("0x03") + ", 21 August 2026) lets it judge the grace second in one direction: "
      "if a client-side recording shows more than 1000 ms between " + c("TELA") + " and a stale coordinate, the server "
      "should have refused; below that it says «not judgeable», because a referee that stays silent acquits. Old "
      "validators refuse new files instead of reading them askew; all recorders and readers in " + c("banchi/") + " are "
      "now at " + c("0x03") + ".")

CHAPTER = ("The RCP/1 protocol", [
    ("RCP: the protocol model", S1),
    ("RCP: the rigor rule", S2),
    ("RCP: channels and stream identification", S3),
    ("RCP: elementary types and framing", S4),
    ("RCP: the handshake", S5),
    ("CIAO and ECCOMI: capability negotiation", S6),
    ("Credentials, the fixed delay and the address ban", S7),
    ("ATTACCA and SESSIONE: attaching to a desktop", S8),
    ("Handshake deadlines and session states", S9),
    ("RCP: the video frame", S10),
    ("Key frames and abandonment", S11),
    ("Canvas changes: ADATTA_TELA, TELA and VISTA", S12),
    ("RCP input messages", S13),
    ("Cursor shape and clipboard messages", S14),
    ("Audio datagrams", S15),
    ("The bench marker: BANCO_MARCA", S16),
    ("TERMINA_SESSIONE: logging out", S17),
    ("RCP: the farewell", S18),
    ("Disconnect reasons", S19),
    ("RCP: session clocks", S20),
    ("Versions and how RCP grows", S21),
    ("What RCP does not do", S22),
    ("Testing against the specification", S23),
])
