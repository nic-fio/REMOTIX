from build import box, c, code, fig, note, p, rif, seq, steps, table, text, tip, ul, warn, zone

# ── 1. How the page is served ─────────────────────────────────────────────
S1 = p("The whole client is one file, " + c("src/page.html") + ": the login page, the RCP/1 client, video "
       "decoding and drawing, audio, clipboard, keyboard, pointer and touch. Nothing is installed on the user's "
       "device and nothing else is downloaded: the page is the product's only client. The package installs it as "
       + c("/usr/share/remotix/page.html") + " and the service starts with " + c("--page") + " pointing at it "
       "(" + c("debian/rules") + ", " + c("debian/remotix.service") + ").", lead=True) + \
    table(["What", "How"], [
        ["Served by", c("src/page.c") + ", a small TLS-over-TCP server inside the network-facing process, on the same port "
         "number as QUIC (7447, " + c("DEFAULT_PORT") + " in " + c("main.c") + ": TCP for the page, UDP for WebTransport). "
         + c("page_open_fd()") + " takes the listener that " + c("page_bind()") + " opened; in the packaged service "
         "(" + c("--split") + ") the process that serves the page is not root, and " + c("page_readable_by()") + " in "
         + c("main.c") + " refuses to start if that user cannot read the file"],
        ["Routes", c("/") + " and " + c("/index.html") + " (the page), " + c("/fingerprint") + " (the certificate "
         "fingerprint as JSON). Everything else is 404. The query string and the fragment are cut before matching, so "
         + c("/?logbook") + " is the page"],
        ["Compression", "When the request's " + c("Accept-Encoding") + " allows it (q-values are parsed, "
         + c("accepts_gzip()") + "), the page goes out gzip-compressed (zlib level 6, " + c("Content-Encoding: gzip")
         + ", " + c("Vary: Accept-Encoding") + "). The not-banned page is built and compressed once per certificate "
         "fingerprint and shared read-only by every client (" + c("gz_page()") + "); a banned visitor gets its own prefix "
         "(the four markers replaced) followed by the shared tail (" + c("banned_respond()") + ")"],
        ["Isolation headers, every answer", c("Cross-Origin-Opener-Policy: same-origin") + ", "
         + c("Cross-Origin-Embedder-Policy: require-corp") + ", " + c("Cross-Origin-Resource-Policy: same-origin")
         + " (the " + c("ISOLATION") + " block), plus " + c("Cache-Control: no-store") + " and "
         + c("X-Content-Type-Options: nosniff")],
        ["Security headers, every answer", c("Content-Security-Policy") + " (with " + c("frame-ancestors 'none'")
         + "), " + c("Referrer-Policy: no-referrer") + " and " + c("Permissions-Policy") + ": the " + c("PAGE_SECURITY")
         + " block of " + c("page.c") + ", on the page, on " + c("/fingerprint") + " and on the 400, 404, 431, 500 and 503 answers. "
         "Described in " + rif("Security model")],
        ["External resources", "None. The Opus decoder (WebAssembly, " + c("OPUS_WASM_B64") + ") and the video probe "
         "streams are embedded in base64"],
        ["Connections", "At most 128 TCP clients at a time (" + c("PAGE_MAX_CLIENTS") + "), 32 from one address or IPv6 /64 ("
         + c("PAGE_PER_ADDRESS") + ") and 64 from one /48 (" + c("PAGE_PER_48") + "); a request header is at most 8 KiB ("
         + c("MAX_REQUEST") + "). Accept rates, deadlines and the fair-share eviction when the table is full are described in "
         + rif("Login and its defences")],
    ], "«TAB» — How the page reaches the browser") + \
    p("Cross-origin isolation is a product requirement (" + c("SPECS.md")
      + " §11.5), not a tuning option: without it Firefox and Safari round the page's timers to 1 ms, against a latency cap of 50 ms, and "
      "shared memory does not exist. With " + c("require-corp") + " every sub-resource would have to declare its "
      "own policy; the simplest cure is to have none, which is why everything is inline. The isolation is "
      "inherited by the optional video worker, born from a " + c("Blob") + " (measured 13 Aug 2026: "
      + c("crossOriginIsolated") + " true inside the worker, timer grain 0.005 ms).") + \
    table(["Marker", "Replaced with", "Read by"], [
        [c("__FINGERPRINT__"), "the base64 SHA-256 of the DER of the current session certificate", "the WebTransport "
         + c("serverCertificateHashes") + " option, as a fallback"],
        [c("__WARNING__"), "empty, or the ban notice (one sentence, “this address or network”) with the hours and minutes left, rounded up to the minute", "the CSS: " + c("#warning:empty")
         + " hides it, so a banned visitor reads the reason even without JavaScript"],
        [c("__BANNED__"), c("yes") + " or " + c("no") + ", on " + c("data-banned") + " of the body", "the script and the ban checks of " + c("prove/")],
        [c("__REMAINING_MS__"), "milliseconds left on the ban", c("data-remaining-ms") + " of the body"],
    ], "«TAB» — The four markers the server fills while serving") + \
    p(c("page_open_fd()") + " in " + c("page.c") + " refuses to start if any marker is missing from the file, or if " + c("data-banned=\"")
      + " or " + c("data-remaining-ms=\"") + " occur more than once (a reader that searches the document for the first occurrence "
      "would read the wrong one). The fingerprint is the only server text that enters a JavaScript string, and "
      "it is base64 written by REMOTIX; the ban sentence never enters the script. A banned visitor is served the page "
      "anyway: the ban is not checked at accept, because the person must read the reason (" + c("SPECS.md")
      + " §4.2). The TLS side, the certificates and the ban are described in " + rif("Transport") + ", " + rif("Login and its defences")
      + " and " + rif("Security model") + ".")

# ── 2. Structure ──────────────────────────────────────────────────────────
S2 = p("The file is about 14 000 lines and 0.9 MB, most of it comments that carry the reason and the measurement behind "
       "each rule, plus the embedded Opus decoder and the probe keyframes. The code is organised in blocks, and the three input blocks are "
       "“anchors”, each written inside its own markers.", lead=True) + \
    table(["Block", "Main names", "Covered in"], [
        ["Style", "the login look (" + c("Satinato") + ", i.e. satin), the desktop styling on " + c("body[data-viewer=\"on\"]") + " (screen on)", "this chapter"],
        ["Diagnostics", c("note()") + " (one log line), " + c("logbook_visible()") + " (show or hide the log), the browser and system " + c("MARK") + " lines", rif("Measurements and the diagnostics mode")],
        ["RCP bytes", c("Writer") + ", " + c("Reader") + ", " + c("Channel") + ", " + c("envelope()") + " (frame a message), tables " + c("TYPE") + " and " + c("REASON_TEXT"), rif("The RCP/1 protocol")],
        ["Video probes", c("PROBES") + ", " + c("MEASURE_PROBES") + " (the size ladder), " + c("probe_all()") + ", " + c("max_size()"), rif("Choosing the codec on the pixel")],
        ["The screen", "class " + c("Viewer") + ": rules of RCP §5.2/§6.2, decoder, drawing paths, counters", rif("Receiving video frames")],
        ["Session", c("connect()") + ", " + c("listen_control()") + " (the control channel), " + c("start_video()") + ", " + c("read_one_stream()"), rif("The connection sequence")],
        ["Audio", c("start_audio()") + ", the Opus WebAssembly decoder", rif("Audio and clipboard")],
        ["Clipboard", c("clipboard_prepare()") + ", " + c("start_clipboard()"), rif("Audio and clipboard")],
        ["Worker", c("WORKER_SHELL") + ", " + c("worker_source()") + ", " + c("start_worker()"), rif("The video worker and the MSE path")],
        ["Exit", c("back_to_form()") + ", " + c("run_logout()"), rif("End of session in the page")],
        ["Input anchors", c("F4-CLASSIC-INPUT") + " (mouse and keyboard), " + c("F4-TOUCH") + " (touch and the layout switch), "
         + c("F4-SHORTCUTS") + " (shortcuts, full screen, keyboard lock)", rif("Input")],
    ], "«TAB» — The blocks of page.html") + \
    p("The page defines one main global, " + c("window.REMOTIX") + ", an object <i>to be read</i> by checks and "
      "diagnostics (" + c("viewer") + " the screen object, " + c("probing") + " the probe results, " + c("stretches()")
      + " the latency stretches, " + c("round_trip") + ", " + c("video") + ", " + c("declarations") + ", "
      + c("logbook()") + ", " + c("shortcuts") + ", " + c("read_one_stream") + "…): nothing in it "
      "changes what the page does. The input anchors meet through " + c("REMOTIX_INPUT") + " (the input stream, "
      "set after " + c("SESSION") + "), " + c("REMOTIX_CLASSIC") + ", " + c("REMOTIX_POINTER") + " and "
      + c("REMOTIX_SHORTCUTS") + ".") + \
    table(["Switch", "Effect", "Purpose"], [
        [c("?logbook") + " (the word anywhere in the query string, not in the fragment)", "shows the diagnostic log and the shortcuts bar (also " + c("REMOTIX.logbook(true)") + ")", "diagnosis"],
        [c("?canvas=gl") + " or no " + c("?canvas="), "the WebGL2 path: it is the default, " + c("gl") + " only names it", "the default"],
        [c("?canvas=bmp"), "draw with " + c("bitmaprenderer") + " instead of WebGL2 (any " + c("?canvas=")
         + " value other than " + c("gl") + " does the same)", "A/B comparison"],
        [c("?canvas=2d"), "draw on the 2D canvas, the path that showed the 64×192 blocks", "A/B comparison"],
        [c("?canvas=desynchronized"), "asks for a 2D context with " + c("desynchronized: true")
         + "; since it is not " + c("gl") + ", " + c("bitmaprenderer")
         + " is taken first, and the 2D context is created only where " + c("createImageBitmap") + " is missing",
         "latency experiment"],
        [c("?video=worker") + " or " + c("#video=worker"), "decode and draw in a dedicated worker, on every browser", "see " + rif("The video worker and the MSE path")],
        [c("?video=main") + " or " + c("#video=main"), "decode and draw on the main thread, even on desktop Firefox", "A/B comparison"],
        [c("?draw=mse"), "draw through MediaSource and a " + c("<video>"), "bench only"],
        [c("?fit=no") + " or " + c("#fit=no"), "do not ask the server for a canvas of the window size", "A/B comparison"],
        [c("?layout=touch|classic"), "force the touch or the classic layout (also as " + c("#layout=…") + ")", "override for tests and diagnosis"],
    ], "«TAB» — URL switches the page reads; none is a user setting") + \
    note("the switches exist so that a comparison changes <b>one</b> variable inside the same page; they are not "
         "per-browser or per-compositor options, and the product has one behaviour without them (the one exception, the video worker "
         "on desktop Firefox, is a documented default, not a switch). The fragment "
         "form (" + c("#…") + ") never reaches the server, so it also works on a page served by any static server.",
         "Test switches, not settings.")

# ── 3. Layouts and body states ────────────────────────────────────────────
S3 = p("The page has one document and two input layouts, <b>classic</b> (mouse and physical keyboard, the desktop use) "
       "and <b>touch</b> (a finger as a trackpad, the phone use). The chapter " + rif("Input") + " describes what each "
       "layout sends; this section lists what the page itself changes in the document, because the style sheet is where "
       "the layout in force is read.", lead=True) + \
    table(["Body attribute", "Values", "Written by", "Effect"], [
        [c("data-viewer"), c("on") + " or absent", "the viewer when frames are shown; removed by " + c("back_to_form()"),
         "the login form, title, outcome and declaration are hidden (" + c("display: none") + "), the body is black with no padding, the canvas becomes the first flex "
         "child of a column as tall as the window and is centred with " + c("margin: auto") + ": any space left over is black, outside the buffer"],
        [c("data-layout"), c("classic") + " or " + c("touch"), c("apply_mode()") + " in the " + c("F4-TOUCH") + " anchor (the only place that writes it)",
         "touch hides the browser cursor over the canvas and shows the on-screen keyboard button " + c("#keyboard-button") + " (only with the session on)"],
        [c("data-pointer"), c("system") + ", " + c("drawn") + ", " + c("both"), c("cl_apply_mode()") + " (default " + c("system") + ", variable " + c("cl_mode") + ")",
         "which pointer is visible in the classic layout; see " + rif("Mouse and pointer in the classic layout")],
        [c("data-hooked"), c("yes") + " or " + c("no") + " (absent until the first pointer-lock change)", "the classic layout, at every " + c("pointerlockchange"), "the browser cursor is hidden while the lock is on"],
        [c("data-banned") + ", " + c("data-remaining-ms"), "the four markers of the table above", "the server", "the ban state; never written by the script"],
        [c("body.diagnostics"), "a class, not an attribute", c("logbook_visible()"), "shows " + c("#logbook") + ", " + c(".note") + ", " + c("#shortcuts") + " and " + c("#shortcuts-open")],
    ], "«TAB» — The body states the style sheet reads") + \
    p("The login page itself is a two-panel grid: a story panel, and a card with " + c("#username") + ", " + c("#password") + " and "
      + c("#signin-button") + " and a footer line that the page fills with " + c("location.hostname") + " (the server does not need to know "
      "under what name it is reached). Under 860 CSS px the two panels stack into one column and the story text and the list of points are hidden (only the logo and one line stay); under 420 px the padding shrinks. All text the user reads "
      "is in English (" + c("DECISIONS.md") + " §10.32). The canvas " + c("#viewer") + " exists from the start as a 16×16 element that is not displayed.") + \
    p("<b>Desktop dress is undone as carefully as it is put on.</b> Whoever puts the desktop dress on must hide what the desktop replaces, and whoever "
      "switches a state on must know how to switch it off. " + c("back_to_form()") + " (" + rif("End of session in the page") + ") removes " + c("data-viewer")
      + ", releases pointer lock and full screen, returns the canvas to 16×16 and gives the focus back to the user name.") + \
    p("Under " + c("body:not(.diagnostics)") + " the log, the footnote " + c(".note") + " and the shortcuts bar are not displayed, even though their text "
      "keeps accumulating. A visitor who has not asked for them sees no bar at the bottom of the desktop: " + rif("Shortcuts the browser keeps")
      + " explains what that means for the one on-screen button the page has.")

# ── 4. Login and connection ───────────────────────────────────────────────
CONNESSIONE = seq(
    [("Page", "page.html", "light"), ("Page server", "page.c, TCP", "dark"), ("RCP server", "WebTransport, UDP", "navy")],
    [(0, 1, "GET /fingerprint"),
     (1, 0, "SHA-256 of the session certificate", True),
     (0, 2, "WebTransport /rcp/1 with the certificate hash"),
     (0, 2, "first bidirectional stream: HELLO (capabilities)"),
     (2, 0, "HERE_I_AM: version and the server's choices", True),
     (0, 2, "CREDENTIALS: user and password"),
     (2, 0, "ADMITTED, or REJECTED, or FAREWELL", True),
     (0, 2, "ATTACH: canvas, view, keyboard layout"),
     (2, 0, "SESSION: new or resumed, granted canvas, desktop", True),
     (0, 2, "input stream · FIT_CANVAS"),
     (2, 0, "CANVAS · one stream per video frame · audio datagrams", True)],
    "«FIG» — From the Connect button to the first frame")

S4 = p("The login form has two fields and a button — " + c("#username") + ", " + c("#password") + ", " + c("#signin-button")
       + " — plus " + c("#outcome") + " for the outcome, " + c("#warning") + " for the ban and " + c("#declaration")
       + " for what the page declares about codecs and video. The ids are stable: the checks of " + c("prove/")
       + " find elements by id, not by text.", lead=True) + CONNESSIONE + \
    steps([
        "<b>Submit.</b> The button is disabled, the outcome cleared; " + c("connect()") + " runs. Whatever "
        "happens, the password field is emptied at the end: it is never kept, and never logged.",
        "<b>WebTransport present?</b> If not, the page says so and stops.",
        "<b>Fingerprint.</b> " + c("fingerprint()") + " fetches " + c("/fingerprint") + " before every attempt, because a "
        "tab left open for two weeks holds the fingerprint of a certificate already rotated. A 503 (server busy) is asked "
        "again up to twice, 1 s apart. If the fetch is "
        "rejected by the network (" + c("TypeError") + ": nobody listens), it is tried once more after 1 s and then the page says that the server "
        "does not answer and does not open WebTransport (Firefox would otherwise wait the 30 s of its "
        "QUIC handshake). Any other failure falls back to the fingerprint served with the page, and says so in the log.",
        "<b>WebTransport</b> to " + c("https://<host>/rcp/1") + " with " + c("allowPooling: false") + " and "
        + c("serverCertificateHashes") + ": the browser checks the fingerprint, not a certificate chain — the only "
        "mechanism browsers offer to a server without a domain (RCP.md §4.1-bis).",
        "<b>Listen first.</b> Video streams, audio datagrams and clipboard streams are listened to <i>before</i> "
        "the handshake ends: a server that opened one before " + c("SESSION") + " violates RCP §2.5, and the "
        "violation is only visible to someone already listening.",
        "<b>" + c("HELLO") + "</b> with the capabilities (" + rif("Capabilities declared by the page") + "), after waiting for the "
        "codec probes. <b>" + c("HERE_I_AM") + "</b>: a version other than 1 is refused with " + c("INCOMPATIBLE_VERSION")
        + " before the password leaves.",
        "<b>" + c("CREDENTIALS") + "</b>. " + c("REJECTED") + " shows the reason and stops (a second attempt needs a new "
        "connection); a " + c("FAREWELL") + " shows its reason and stops; " + c("ADMITTED") + " continues.",
        "<b>" + c("ATTACH") + "</b> carries the canvas to ask for (" + c("canvas_to_request()") + "), the view ("
        + c("view_size()") + ") and the keyboard layout (" + c("layout()") + "). <b>" + c("SESSION") + "</b> says "
        "new or resumed, the granted canvas and the desktop name. A granted canvas different from the requested "
        "one is declared to the user (RCP §4.5 allows it).",
        "<b>After " + c("SESSION") + "</b>: the single input stream is opened, the video is negotiated with the decoder, "
        "the first-frame watch starts, the control channel is read in a loop (" + c("listen_control()")
        + "), and " + c("FIT_CANVAS") + " is sent once for the window size.",
    ]) + \
    p("The keyboard layout is guessed from " + c("navigator.language") + " (" + c("en") + " → " + c("us")
      + ", except " + c("en-GB") + " → " + c("gb") + " and " + c("en-IE") + " → " + c("ie") + "; about thirty languages "
      "whose XKB name equals the ISO code pass through, a few are mapped, such as " + c("sv") + " → " + c("se")
      + " and " + c("da") + " → " + c("dk") + "; the rest falls back to " + c("us") + "); a page cannot know the physical keyboard, and choosing it is described in "
      + rif("Keyboard layout negotiation") + ". The input stream coalesces pointer moves: when the writer's " + c("desiredSize")
      + " is at or below zero, a " + c("POINTER") + " is held aside and replaced by the next one, and any key or "
      "button pushes it out first (measured from Samsung DeX on 14 Aug 2026: median round trip 135 ms but worst 2161 ms, "
      "a queue rather than a slow network). Keys and buttons are never dropped.") + \
    p("The page does not store the user name, the password or any session token: nothing persists after the tab closes "
      "(" + rif("What the page stores and what it declares") + ").")

# ── 5. Capabilities ───────────────────────────────────────────────────────
S5 = p("The HELLO capabilities say what <b>this</b> browser can do, measured where possible. An empty value is a "
       "protocol error (RCP §4.3), so a capability with nothing to say is omitted, and the omission is logged.",
       lead=True) + \
    table(["Capability", "Value", "Where it comes from"], [
        [c("video.codec"), c("hevc,h264") + " or a subset", "only the codecs whose probe was actually painted, in preference order"],
        [c("video.depth"), c("8") + " and/or " + c("10"), "the depths that painted on at least one good codec; 8 must be present"],
        [c("video.level"), c("5.1"), c("DECLARED_LEVEL") + "; not measurable from the page (browsers do not enforce levels): the server checks it"],
        [c("video.max_size"), "e.g. " + c("3840x2160"), "the decoder's ceiling measured on the pixel (" + rif("Measuring the decoder ceiling") + "); omitted when not measured"],
        [c("audio.codec"), c("opus,pcm") + " or " + c("pcm"), "opus only if the WebAssembly decoder loads, or else " + c("AudioDecoder") + " accepts Opus"],
        [c("input.touch"), c("no"), "constant"],
        [c("clipboard.text"), c("yes"), "constant"],
        [c("video.pace"), c("yes") + " (" + c("no") + " on the MSE path)", "the page can tell its decoder is behind; the code comments call the capability PROPOSED and cite RCP.md §13, a section "
         + c("docs/RCP.md") + " does not have (it ends at §12); the server declares it only when started with " + c("--decoder-pace")
         + " (" + rif("The RCP/1 protocol") + ")"],
        [c("client.name"), c("remotix-page 0.1.0"), "constant"],
    ], "«TAB» — The capabilities sent in HELLO") + \
    p("Declaring something the browser cannot do does not give an error; it gives a black canvas or silence, "
      "because the server must choose within the intersection following the client's order. Declaring "
      + c("opus") + " on an engine that cannot decode it makes the server send fifty datagrams a second into a "
      "decoder that cannot read them — and the PCM fallback, which exists to be Opus's positive control, never comes into play.")

# ── 6. Codec probes ───────────────────────────────────────────────────────
S6 = p("The codec is not chosen by asking the browser's APIs. It is chosen by decoding a real keyframe and "
       "reading the pixels back.", lead=True) + \
    p("Measured on 12 August 2026 on Firefox 140 ESR, for all seven HEVC strings: "
      + c("navigator.mediaCapabilities.decodingInfo()") + " said supported, smooth and power-efficient; "
      + c("canPlayType()") + " said “probably”; " + c("VideoDecoder.isConfigSupported()") + " said false; and no "
      "pixel arrived. Three witnesses, two of them false and agreeing with each other. The page never uses the "
      "first two to choose a codec (" + c("decodingInfo()") + " is called once at load, only to write the diagnostic "
      + c("MARK no-webcodecs") + " log line about MSE; " + c("canPlayType()") + " is not called at all). " + c("isConfigSupported") + " is used as a <b>filter</b> only — when it says no the pixel "
      "never arrives, when it says yes it proves nothing (Chrome accepts a level-3.0 declaration on a 5.1 stream "
      "and paints anyway).") + \
    table(["Step", "Detail"], [
        ["Probe frames", c("PROBES") + ": one 64×48 keyframe per codec and depth (" + c("hevc-8") + ", "
         + c("hevc-10") + ", " + c("h264-8") + "; two AV1 probes remain in the table, unused), left half red, right half blue. If the 64×48 frame "
         "does not paint, the same strings are tried once more with the 320×240 first rung of the size ladder ("
         + c("probe_one()") + ", " + c("DECISIONS-11.md") + " §11.55: an AMD hardware decoder refused pictures under 64 rows)"],
        ["Strings tried", "per codec, the declared level first, then a low-level fallback: " + c("hev1.1.6.L153.B0")
         + " / " + c("hev1.1.6.L93.B0") + " (Main), " + c("hev1.2.4.L153.B0") + " (Main10), " + c("avc1.640033")
         + " / " + c("avc1.64001f") + " (High 5.1 / 3.1); " + c("codec_strings()") + " builds them from " + c("DECLARED_LEVEL")],
        ["Decoder config", c("codedWidth") + ", " + c("codedHeight") + ", " + c("optimizeForLatency: true")
         + ", no " + c("description") + " (the stream is Annex B)"],
        ["Verdict", c("paint_probe()") + " fills a canvas with dark magenta, decodes, draws the frame, reads it back with "
         + c("getImageData") + " and requires each half to be closer to its own colour than to the other one. "
         "Black, magenta or a uniform fill cannot pass. Timeout 2.5 s"],
        ["When", "at page load (" + c("PROBING") + ", the promise of " + c("probe_all()") + "; not on the MSE path), so the answer is ready when the user presses Connect; "
         "the cost is tens of ms on a capable engine"],
    ], "«TAB» — The codec probe") + \
    p("The preference is " + c("PREFERENCE") + " = " + c("[\"hevc\", \"h264\"]") + ": HEVC where it paints, "
      "H.264 as the universal fallback; the server makes the final choice within the intersection. AV1 is not offered "
      "(" + c("DECISIONS.md") + " §1.13-ter): Firefox for Android had neither HEVC nor AV1, H.264 is the only codec in hardware at both ends, and Firefox's AV1 decoder painted "
      "rectangular blocks where Chrome and " + c("dav1d") + " were clean on the same bytes. Its RCP number, 2, stays reserved "
      "forever (" + c("CODEC_RCP") + "): reusing it would make an old client paint garbage without an error. "
      "The H.264 string is " + c("avc1.640033") + " (High, level 5.1), the same the server derives from the "
      "SPS; level 5.0 (" + c("avc1.640032") + ") cannot reach 3840×2160.") + \
    table(["Probe result", "What the declaration box tells the user"], [
        ["No " + c("VideoDecoder") + " at all, and no codec declared", "this browser lacks WebCodecs, the only way REMOTIX draws; today that is Firefox for Android, declared unsupported — use Chrome there. "
         "By the code (" + c("probe_one()") + ", " + c("declare()") + ") the sentence is reached only when " + c("MediaSource") + " refuses the H.264 string too: where it accepts it, H.264 is "
         "declared on the engine's word and the user reads the “H.264 only” sentence instead. Not re-tried on a real phone for this package"],
        ["WebCodecs but no codec painted", "the session can open but there will be no image"],
        ["H.264 only", "HEVC is not decoded here; H.264 is used, which costs more bandwidth for the same quality"],
        ["HEVC paints but the server chose H.264", "a one-line note"],
    ], "«TAB» — The codec declarations") + \
    p("If no codec reaches the pixel, " + c("video.codec") + " is omitted and the server answers "
      + c("NOTHING_IN_COMMON") + "; the page writes its own explanation first, because only the page knows which "
      "probe failed and why, and the password does not leave. Whether decoding happens in hardware is not observable from JavaScript, and the page "
      "never claims it. The server side of the choice is in " + rif("Video encoding") + ".")

# ── 7. Decoder ceiling ────────────────────────────────────────────────────
S7 = p(c("video.max_size") + " is the largest frame the browser's <b>decoder</b> can bring to the "
       "pixel. It is not the screen size: a phone's decoder has limits its screen does not declare, and a desktop "
       "screen can be smaller than what its browser decodes.", lead=True) + \
    p("The screen size goes where it belongs, in the " + c("view") + " of " + c("ATTACH") + ". Putting the screen size in "
      + c("video.max_size") + " produced a failure that no test page showed: on a screen 1010 pixels tall the server granted a 1794×1010 canvas "
      "while the stage captured 1920×1080, frames of the wrong size were refused, and the user saw nothing.") + \
    table(["Rule", "Why"], [
        ["A ladder per codec: 320×240, 640×480, 1280×720, 1920×1080, 2560×1440, 3840×2160 (" + c("MEASURE_PROBES") + ")",
         "320×240 is the smallest legal canvas; 3840×2160 is within level 5.1, the level declared in the same HELLO"],
        ["Each step must paint the two colours <b>and</b> the output frame must have exactly that size",
         "A smaller frame, scaled for the read-back, would pass the colour test and lie about the size"],
        ["The read-back canvas is 64×48 (" + c("rl") + "/" + c("ra") + ")", "Reading back a 3840×2160 frame (8.3 Mpixel, 33 MB of RGBA) per step would cost more than decoding"],
        ["Stop at the first failing step", "Capability is assumed monotonic in size; the log names the step where it stopped"],
        ["The value is the minimum across declared codecs", "The server chooses the codec afterwards, so the ceiling must hold for either"],
        ["8-bit ladder frames only", "8 is the depth both sides must support; a 10-bit ladder would double the startup cost without a measured reason"],
        ["Omitted on the MSE path", "The ladder needs " + c("VideoDecoder") + "; a missing value is legal, an invented one breaks phones"],
    ], "«TAB» — How max_size() measures the ceiling") + \
    p("If a codec paints at 64×48 but not even at 320×240, the page declares 320×240 and tells the user the image "
      "may not arrive at all. The cost of the ladder is logged on every load (" + c("probing.size.ms") + ").") + \
    p("<b>The ceiling also limits what the page asks for.</b> The result is kept as " + c("canvas_cap") + " and " + c("canvas_to_request()")
      + " brings the side that overflows it down to the ceiling (a phone 412×915 CSS at ratio 2.625 asks for 1072×2160, not 1072×2304), so that the server has nothing "
      "to reduce. With the ladder as it is, a browser that decodes the whole ladder declares " + c("3840x2160") + " and cannot be granted the 4096×2304 maximum of "
      + rif("Canvas and view") + ": the largest canvas a page can ask for through " + c("canvas_to_request()") + " is the ladder's last rung, 3840×2160.") + \
    warn("whether the ladder should stop at 3840×2160 or reach the protocol maximum of 4096×2304 has not been decided: the last rung was chosen to stay inside the declared "
         "level 5.1 (4096×2176 is its width limit), and the final run of " + c("prove/all.sh") + " of 17 Nov 2026 shows the 3840×2160 ceiling of the test browser as the "
         "reason a check of the maximum size is not green (" + rif("Appendix C — Known issues and open points") + ").", "Open point.")

# ── 8. Canvas and view ────────────────────────────────────────────────────
TELA = fig(
    zone(20, 12, 860, 236, "Browser window: the view, in physical pixels")
    + box(150, 52, 600, 150, "Canvas buffer = the frame", "the granted canvas, width and height multiples of 16", "navy")
    + text(85, 132, "band", 12, "#475569", "600")
    + text(815, 132, "band", 12, "#475569", "600")
    + text(450, 228, "Bands are the parent's black background, outside the buffer: never drawn, never encoded", 11.5, "#334155"),
    900, 250, "«FIG» — The canvas buffer holds exactly the frame; CSS centres it and scales it to at most 1:1")

S8 = p("Two sizes must never be confused. The <b>canvas</b> (" + c("canvas") + " in the code) is the remote desktop's size: it belongs to the "
       "session, is fixed at attach and reattach, and is what the frames carry. The <b>view</b> (" + c("view") + ") is how "
       "much the page has to draw in: it belongs to the connection and changes with the window.", lead=True) + TELA + \
    table(["Function", "Rule"], [
        [c("view_size()"), c("documentElement.clientWidth/clientHeight") + " × " + c("devicePixelRatio")
         + ", <b>truncated</b>. " + c("clientWidth") + " excludes the scrollbar, unlike " + c("innerWidth")
         + "; rounding up at a fractional ratio (Windows at 150 %) would declare one pixel too many, which brings "
         "a scrollbar, a scale of 0.965 and the whole image resampled"],
        [c("canvas_to_request()"), "the view clamped to 320–4096 × 240–2304 (" + c("CANVAS_MIN_W") + ", " + c("CANVAS_MAX_W") + ", " + c("CANVAS_MIN_H") + ", " + c("CANVAS_MAX_H")
         + ") and to the decoder ceiling, truncated to <b>multiples of 16</b> on both sides (" + c("CANVAS_STEP_W") + ", " + c("CANVAS_STEP_H") + ")"],
        [c("Viewer.frame_rect()"), "scale = min(view/frame width, view/frame height, 1): never enlarged; CSS width and "
         "height = frame × scale ÷ " + c("devicePixelRatio") + "; " + c("image-rendering: pixelated")
         + " only at scale exactly 1, otherwise the engine interpolates"],
        [c("Viewer.fit_view()"), "measures twice: the canvas is part of the layout, and a first measure can "
         "include a scrollbar that the resize itself removes"],
        [c("renegotiate_view()"), "on " + c("resize") + ", at the next animation frame: re-measures the view and "
         "rescales. <b>Nothing is sent</b> and the canvas does not change"],
    ], "«TAB» — The geometry functions") + \
    p("The canvas takes the size of the client's window at attach (" + c("DECISIONS.md") + " §5.0-sexies). Scale 1 makes the coordinate conversion the identity, "
      "removes the black bands and the interpolated text, and the request at attach restarts the capture stream, which makes Mutter deliver a frame at once "
      "instead of after a long wait on a still scene. The canvas never changes "
      "while the session lives (§5.1-bis): resizing the window only rescales the image. Resizing an output live could not be "
      "done on every compositor and, where it works, it rearranges the user's windows; the owner did not want a product "
      "that behaves differently depending on the compositor. A new size is taken by reconnecting: the page asks "
      "for its window's size at every attach, and a resumed session takes it too. On KDE the compositor (KWin) runs nested "
      "inside a screenless labwc that REMOTIX starts, and at reattach REMOTIX resizes labwc's output, which KWin follows "
      "(§10.40, " + rif("The four desktops") + "). If the host cannot be resized the session keeps the canvas it was born with, the page rescales it, "
      "centred between black bands, and the server log says so.") + \
    table(["Why multiples of 16", ""], [
        ["Width", "Measured 24 Sep 2026: Firefox 140 does not honour the horizontal cropping declared in the H.264 "
         "SPS. With a width that is not a multiple of 16 it drew the green padding stripe (8 px at 1400, 4 at 3788) "
         "and squeezed the image into the declared width. Chrome 154 was correct"],
        ["Height", "The same evening the owner found the pointer “a few millimetres off” on Firefox: with hardware "
         "decoding it also squeezed vertically (canvas 962, coded 976), so a click landed up to 13–14 px higher "
         "than drawn at the bottom of the screen"],
        ["Cost", "The canvas may be up to 15 px narrower and shorter than the window: two black bands of at most "
         "7–8 px, outside the buffer. Common code for every engine, no branch per browser"],
    ], "«TAB» — The 16-pixel step") + \
    p("The maximum 4096×2304 is a protocol constant (" + c("RCP_CANVAS_MAX_W") + " and its siblings in " + c("src/rcp.h") + "): H.264 on the Intel "
      "card stops at 4096 per side and Firefox on Linux receives only H.264; 2304 is 16:9 at 4096 and the " + c("MaxFS") + " of level 5.1. A larger window gets the maximum on the "
      "side that overflows (5120×2880 → 4096×2304, 5120×1440 → 4096×1440), shown at scale 1 with bands; the "
      "server applies the same rule in " + c("rcp_size_allowed()") + ". Whether a 4096×2304 canvas is actually granted and shown has not been verified: "
      "the decoder ceiling of the browser used in " + c("prove/") + " is 3840×2160 (" + rif("Measuring the decoder ceiling") + "). "
      "Both are technical bounds: the declared limit of the product is 3K (the size actually used depends on the client).") + \
    p("<b>The canvas the server grants is checked.</b> The page does not take the "
      "canvas of " + c("SESSION") + " and " + c("CANVAS") + " as it comes (a u32 per side): a width or height of zero, or "
      "above 4096×2304 (" + c("CANVAS_MAX_W") + " × " + c("CANVAS_MAX_H") + "), closes the session with "
      + c("PROTOCOL_ERROR") + ", the same way the cursor's check does. RCP.md §4.5 and §7.1 never grant such a size, so "
      "the server that does is wrong or hostile, and a canvas of billions of pixels would only bring down the tab.") + \
    p(c("html { overflow-y: scroll }") + " keeps the vertical scrollbar always present, so turning the canvas on "
      "never changes " + c("clientWidth") + ". The canvas has " + c("tabindex=\"-1\"") + ", without which its "
      + c("focus()") + " calls do nothing and the keyboard stays in the password field.") + \
    note("a change of " + c("devicePixelRatio") + " with the window still (page zoom, a window dragged to a screen "
         "with another scale) is not handled: the emulated test delivered no event at all, and a cure needs a "
         "measurement with real zoom. The " + c("VIEW") + " message is never sent after a resize either: no "
         "server component reads it in RCP/1.", "Not settled yet.")

# ── 9. FIT_CANVAS ────────────────────────────────────────────────────────
S9 = p("The canvas is requested once per session, at attach, with " + c("FIT_CANVAS") + ". The server answers "
       "with " + c("CANVAS") + ": adopted, or refused with a reason.", lead=True) + \
    table(["Answer", "What the page does"], [
        [c("CANVAS(FITTED)"), c("canvas_adapted()") + ": opens a tolerance window in which frames at the previous size are "
         "still accepted and drawn; the decoder is <b>not</b> reconfigured on the message but on the first keyframe at the "
         "new size (RCP §5.2), which also closes the window"],
        [c("CANVAS(REFUSED)") + ", reason 1 " + c("COMPOSITOR_UNABLE"), "no further requests in this session; the user "
         "reads that the desktop cannot change size and the browser adapts the image"],
        ["reason 2 " + c("SIZE_OUT_OF_RANGE"), "not repeated"],
        ["reason 3 " + c("NOT_NOW"), "repeated <b>once</b> after " + c("CANVAS_REQUEST_RETRY_MS") + " = 4000 ms, as the flag "
         + c("canvas_request_repeated") + " allows: often it means “not yet” (measured: the stage mounted 2.2 s after a server restart)"],
        ["any refusal", "if it declares a canvas different from the one the page believes, the server wins"],
    ], "«TAB» — The answers to FIT_CANVAS") + \
    p("The control channel and the video streams are independent QUIC streams, so a frame at the new size can "
      "arrive <i>before</i> the " + c("CANVAS") + " that announces it. While an " + c("FIT_CANVAS") + " is "
      "unanswered (" + c("canvas_waits") + ", the pending canvas requests, &gt; 0), a frame at an unannounced size is held ("
      + c("Viewer.hold()") + ") and judged again when the answer arrives. With no request in flight, such a frame is "
      + c("PROTOCOL_ERROR") + " at once: the condition is a request in flight, not a number of frames. The page compares a new request with "
      "the size it is <i>going to</i>, not the one in force (" + c("ask_canvas()") + "): the rule was written when a window resize still "
      "sent a request, and today it serves the attach and the single " + c("NOT_NOW") + " retry.")

# ── 10. Receiving video ───────────────────────────────────────────────────
S10 = p("Each video frame arrives on its own unidirectional stream, opened by the server in frame order. "
        + c("start_video()") + " reads the incoming streams and " + c("read_one_stream()") + " collects each one. The "
        "wire format is in " + rif("The RCP/1 protocol") + "; this is the page's side.", lead=True) + \
    table(["Rule", "Detail"], [
        ["Delivered in opening order", "Reads are chained: stream N is handed over only after N−1. Reading them in parallel and judging each "
         "when it <i>finished</i> turned a large frame that completed after its small successor into a false hole (measured on Firefox 140 at 245 Mbit/s: 173 false holes "
         "out of 173, 347 useless key requests a minute). The price: a large frame holds the ones behind it, which the decoder would do anyway"],
        ["FIN versus RESET", "A " + c("read()") + " that ends with " + c("done") + " is a complete frame; one that "
         "throws is a " + c("RESET_STREAM") + ": the bytes are discarded, never given to the decoder, and treated as a hole"],
        ["16 MiB", "A stream longer than the RCP §6.2 cap closes the session with " + c("PROTOCOL_ERROR")],
        ["Channel byte", "The high byte of the first two bytes says the channel: 0x03 video, 0x02 clipboard; anything else closes"],
    ], "«TAB» — Reading the unidirectional streams") + \
    code("""
offset  size  field
 0      u16   type      0x0301 keyframe, 0x0302 delta
 2      u16   codec     1 hevc, 3 h264 (2 reserved: av1)
 4      u32   width
 8      u32   height
12      u32   number    frame number, 0 reserved, wraps to 1
16      u64   instant   server monotonic clock, microseconds
24      u32   input     last input id applied when captured (0 = none)
28      ...   Annex B data
""", "text", "The 28-byte video header (RCP.md §6.2), big-endian, read by Viewer.read_header()") + \
    p("The reader of these 28 bytes is written from the protocol table, independently of the server's writer: two "
      "implementations of the same bytes are part of the referee, and a disagreement is a gift. "
      + c("Viewer.deliver()") + " then applies the rules in a fixed order:") + \
    steps([
        "type must be key or delta; codec must be the negotiated one; otherwise " + c("PROTOCOL_ERROR") + ";",
        "the " + c("input") + " field closes an input round trip (" + rif("Measurements and the diagnostics mode") + ");",
        "number 0 is a protocol error;",
        "<b>order before size</b>: a number not after the last delivered one (mod 2³²) is dropped without looking "
        "at its size — otherwise the keyframe that closes a tolerance window, overtaking older frames, would close "
        "the session;",
        "size: the canvas in force or a tolerated one; an unannounced size is held if an " + c("FIT_CANVAS")
        + " is pending, a size that was in force and no longer is closes the session;",
        "a jump in numbers is a <b>hole</b>: one " + c("REQUEST_KEY") + " with the last delivered "
        "number, repeated at most once a second while the hole stays open (" + c("Viewer.hole()") + "); the last "
        "good image stays on screen, deltas are not even given to the decoder until a keyframe arrives (RCP §5.2) — "
        "a delta referencing a missing frame does not error, it just decays;",
        "a frame whose size differs from the decoder's configuration is decoded only if it is a keyframe at the "
        "canvas in force (then the decoder is reconfigured); otherwise it is dropped and treated as a hole;",
        "decode, with the server's " + c("instant") + " as timestamp.",
    ])

# ── 11. Decoding ──────────────────────────────────────────────────────────
S11 = p("Decoding uses one " + c("VideoDecoder") + " per session, configured with the string the probe saw paint, "
        "the frame size and " + c("optimizeForLatency: true") + ". Painting happens <b>inside</b> the decoder's "
        "output callback, not on " + c("requestAnimationFrame") + ": an extra animation frame would add up to one "
        "display interval to a latency budget measured in tens of milliseconds.", lead=True) + \
    p(c("Viewer.reconfigure()") + " creates the decoder lazily and recreates it if an error closed it: after an "
      "error a " + c("VideoDecoder") + " is " + c("closed") + " and every " + c("configure()") + " throws, which "
      "would make a session unrecoverable in silence. A decoder error is treated as a hole and asks for a keyframe.") + \
    p("<b>The decoder-queue skip.</b> Measured 14 Aug 2026 with a scene at 58 draws/s: the server sent "
      "39.6 frames/s, the page drew 34.7, nobody dropped the excess, and the delay between " + c("decode()")
      + " and the callback grew by about 108 ms every second. "
      "The cause was a 34 ms " + c("drawImage") + " of the 2D path. The cure skips the <i>drawing</i>, never the "
      "decoding, so the delta chain is intact and no key is needed. The rule is weighted by the "
      "measured drawing cost:") + \
    code("""
skip this frame  if  decodeQueueSize > 2  and  decodeQueueSize * draw_cost() > 16 ms
draw_cost()       = median time the callback holds the main thread
                    (+ median transfer-to-glass on the bitmaprenderer path)
""", "text", "Viewer.paint(): when a decoded frame is not drawn") + \
    p("With a 34 ms drawing cost the rule fires at the old threshold; with WebGL2 at 0.26 ms it practically never "
      "fires, because skipping a 0.26 ms draw gains nothing — when the decoder itself is behind, the cure is the "
      "server's rate regulator. Every skipped frame is counted (" + c("queue_skipped") + "): a rate that falls "
      "without a count would hide the cause.") + \
    table(["Counter", "Meaning"], [
        [c("delivered"), "frames given to " + c("decode()")],
        [c("exited"), "frames out of the decoder (first line of the callback)"],
        [c("painted"), "frames that reached the glass — the measure the first-frame watch reads"],
        [c("queue_skipped"), "decoded and not drawn by the queue rule"],
        [c("late"), c("createImageBitmap") + " results older than one already shown, discarded"],
        [c("in_bmp") + ", " + c("bmp_failed"), "conversions pending, conversions or uploads failed"],
        [c("holes") + ", " + c("keys_requested"), "holes opened, key requests sent"],
        [c("discarded_order") + ", " + c("discarded_measure") + " (dropped for order, for size), " + c("held")
         + ", " + c("tolerated_count"), "the size and order rules at work"],
    ], "«TAB» — The counters of the screen object (" + c("REMOTIX.viewer.counts") + ")") + \
    p("The counters close, within a session: " + c("delivered = exited + inside the decoder") + " and "
      + c("exited = queue_skipped + painted + late + in_bmp + bmp_failed") + ". They were added after a Firefox session showed 8 952 delivered and 6 929 drawn, "
      "with 2 007 frames that no counter named.")

# ── 12. Drawing ───────────────────────────────────────────────────────────
S12 = p("The decoded " + c("VideoFrame") + " reaches the screen by one of three paths, chosen once when "
        + c("Viewer") + " is built: a canvas takes only one context, so the choice cannot change during a "
        "session.", lead=True) + \
    table(["Path", "When", "How", "Why it exists"], [
        ["<b>WebGL2</b> (default)", "unless " + c("?canvas=") + " names another path; if " + c("getContext(\"webgl2\")")
         + " fails, the next path is taken and logged", c("texImage2D(VideoFrame)") + " into a texture and one "
         "full-canvas triangle; the frame is closed right after the upload", "Default (" + c("DECISIONS.md") + " §9.4): the fast path of Firefox, no read-back"],
        [c("bitmaprenderer"), c("?canvas=bmp") + " (or any other value except " + c("gl") + "), or no WebGL2", c("createImageBitmap(frame)") + " then "
         + c("transferFromImageBitmap()") + "; asynchronous, ordered by a serial number and an epoch", "Cure of the blocks (§5.4), kept as the fallback and the A/B reference"],
        ["2D canvas", c("?canvas=2d") + ", or neither of the above", "a hidden 2D staging canvas ("
         + c("staging") + "), then " + c("drawImage") + " to the visible one", "The original path; shows the blocks"],
    ], "«TAB» — The three drawing paths") + \
    p("<b>The blocks.</b> In August 2026 the owner saw rectangular blocks of 64×192 pixels in still areas. They "
      "were hunted suspect by suspect, with a measurement each: the capture was clean, the encoder was clean (0 "
      "damaged superblocks out of 600 through " + c("ffmpeg") + "), " + c("VideoFrame.copyTo") + " was clean, and "
      + c("getImageData") + " after the draw found 0 wrong pixels out of 180 000 — while a phone photo of the same "
      "canvas showed the rectangles. The pixels entered the 2D canvas correctly and broke on the way to the screen, "
      "in a stretch no API can read: " + c("getImageData") + " reads the backing store, not what the compositor "
      "shows. Firefox and Chrome behaved alike, and a " + c("<video>") + " on the same GPU was clean. The "
      + c("bitmaprenderer") + " context has no 2D backing store, and the owner's verdict on it was “no artefacts”.") + \
    p("<b>WebGL2.</b> On Firefox the " + c("bitmaprenderer") + " path reads every frame back from the GPU synchronously — about 34 ms at 4K — and the "
      "page skipped 11–62 % of frames. WebGL2's " + c("texImage2D") + " has a fast path in Firefox (DMA-BUF and a "
      "GPU blit, YUV→RGB without read-back) when level 0, offset 0, " + c("RGBA/UNSIGNED_BYTE") + ", no unpack skip, "
      "default colour space and visible rectangle equal to the coded one. Measured 26 Sep 2026 on Firefox at 4K: "
      "drawing 34 ms → 0.26 ms, skipped frames 60 % → 12 %. The multiple-of-16 canvas keeps the visible rectangle equal to the coded "
      "one; the log says once whether the fast path is possible.") + \
    table(["Event", "WebGL2 path behaviour"], [
        [c("webglcontextlost"), c("preventDefault()") + " to ask the context back; frames are closed and counted in "
         + c("bmp_failed") + "; a log line if it is not back within 3 s"],
        [c("webglcontextrestored"), "program and texture rebuilt; the next frame repaints everything (no key needed)"],
        ["program does not link", "the canvas stays black and says so: a canvas that had WebGL cannot take another "
         "context, and swapping the element would detach every input handler bound to it. The fallback is the next "
         "page load with " + c("?canvas=bmp")],
    ], "«TAB» — Context loss on the WebGL2 path") + \
    p("<b>The last row of the picture.</b> Chrome converts the " + c("VideoFrame") + " to RGB before the shader sees it, "
      "and builds the last visible row from part of the padding chroma row below, which is zero: that row came out tinted "
      "(the check that caught it in the old test bench was called " + c("chroma_bleed") + "; " + c("DECISIONS-11.md") + " §11.41). The page therefore looks at the frame: when its "
      + c("codedHeight") + " is greater than the visible rectangle it sets the uniform " + c("trim") + " and the shader "
      "repeats the row above for the last visible one. Firefox, with no rows below the visible ones, is untouched; the "
      "price is one row of detail at the bottom edge on Chrome. Verified on 24 October 2026 on gnome and xfce, Chrome and Firefox: on Chrome row 2063 equals row 2062.") + \
    p("On every path the buffer is set to the frame size only when it changes (writing " + c("canvas.width")
      + " clears it), explicitly: Chrome, unlike Firefox, does not resize a " + c("bitmaprenderer") + " canvas "
      "on transfer, and a 16×16 buffer stretched by CSS would send every click to the top-left corner. In the classic layout the pointer "
      "is not painted on the canvas; it is a CSS cursor or a separate element (" + rif("Mouse and pointer in the classic layout") + ").") + \
    note("when " + c("Viewer") + " is built on the WebGL2 path, it still writes a log line describing the path as a "
         "candidate “requested with " + c("?canvas=gl") + "”, “not the default”, and the context-loss lines advise "
         "reloading without " + c("?canvas=gl") + ". Those texts predate WebGL2 becoming the default and are stale; " + c("REMOTIX.stretches().route") + " reports "
         + c("webgl2-requested") + " for the same reason. The behaviour is the default one: the code decides, the texts are wrong.", "A stale label.")

# ── 13. Measurements and diagnostics mode ─────────────────────────────────
S13 = p("The page measures its own share of the latency and exposes it, so that checks read the path really "
        "in use instead of a copy of it. Everything it writes goes to one in-memory list, shown only in diagnostics mode.", lead=True) + \
    table(["Name in " + c("REMOTIX.stretches()"), "From → to"], [
        [c("8_decode_callback"), c("decode()") + " → decoder callback"],
        [c("9a_callback_call"), "callback → start of the conversion (should be ~0)"],
        [c("9b_conversion"), "conversion or texture upload"],
        [c("10_glass"), "transfer to the canvas or " + c("drawArrays")],
        [c("9_10_callback_glass"), "callback → canvas changed"],
        [c("11_glass_next_frame"), "canvas changed → next animation frame (one sample in 16): a lower bound of when the pixel <i>can</i> light"],
        [c("queue_deliv") + ", " + c("queue_out") + ", " + c("age_ms") + ", " + c("recv_ms"), "decoder queue at delivery and at output, age of the output frame, main-thread time of the callback"],
    ], "«TAB» — The client-side stretches (median, p05, p95, min, max and n for each)") + \
    p(c("REMOTIX.round_trip") + " is the full input round trip: each input message records when it left, and the "
      + c("input") + " field of a later frame closes it. It is a lower bound — it stops when the frame arrives, not "
      "when it is drawn. " + c("SCENE") + " samples the age of the image at every pointer move, which distinguishes "
      "“the desktop is frozen” from “the hand moved over the wallpaper and nothing changed”. " + c("voff_ms()")
      + " (glass time minus the frame's server instant) is the video half of the audio/video distance; with the "
      "audio's " + c("aoff_ms()") + ", the unknown clock offset cancels out (" + rif("Audio and clipboard") + ").") + \
    table(["Diagnostics mode", "Detail"], [
        ["Default", "Off: " + c("body:not(.diagnostics)") + " hides " + c("#logbook") + ", " + c(".note") + ", " + c("#shortcuts") + " and the " + c("#shortcuts-open")
         + " button (a 26 px button in the bottom-left corner). The text keeps entering the DOM; hiding is a style, not a deletion"],
        ["Turning it on", c("logbook") + " anywhere in the query string of the address (" + c("location.search") + "), or " + c("REMOTIX.logbook(true)") + " from the console (it calls " + c("logbook_visible()") + "); it needs no reload"],
        ["What it shows", "the page log (the " + c("MARK") + " lines that identify the browser, the system and what the engine offers without WebCodecs; the " + c("MEASURE") + " lines of the drawing path; every declared tolerance and fallback), "
         "and the shortcuts bar with the keyboard-lock state, the pointer geometry (both ends of the conversion) and the list of keys that do not reach the desktop"],
        ["Test-only fault injection", c("#video_fault=die|mute|blind") + " in the fragment is read <b>only</b> when " + c("?logbook") + " is also in the address; it breaks the video worker on purpose to prove the fall back of " + rif("The video worker and the MSE path")
         + ". Without " + c("?logbook") + " nothing changes"],
        ["What is never sent", "The log stays in the page. The server does not receive it (" + c("page.c") + " notes that the " + c("__DIARY__") + " marker and the diary endpoint were removed)"],
    ], "«TAB» — The diagnostics mode of the page") + \
    p("The log does not contain what the user types: lines say “a character” or “key pressed”, and codes are written only for modifiers and mouse buttons (" + c("DECISIONS.md") + " §9.2). "
      "The shortcuts bar is the one place where diagnostics hide something a user may want, which is why " + rif("Shortcuts the browser keeps") + " states it.")

# ── 14. What the page stores and declares ─────────────────────────────────
S14 = p("The page keeps nothing on the device and declares what it does and does not do.", lead=True) + \
    table(["Question", "Answer from the code"], [
        ["Browser storage", "The page contains no use of " + c("localStorage") + ", " + c("sessionStorage") + ", IndexedDB, cookies or the Cache API. "
         "Nothing is written to the device by the page itself; closing the tab discards the log, the counters and the probe results"],
        ["Credentials", "The user name and password are read from the two fields when Connect is pressed and sent in " + c("CREDENTIALS")
         + "; the password field is emptied after every attempt, and neither value is logged. The fields carry " + c("autocomplete=\"username\"")
         + " and " + c("autocomplete=\"current-password\"") + ", so a password manager of the browser may offer to store them: that is the browser's feature, not the page's"],
        ["Server state the page holds", "The certificate fingerprint (re-fetched before every attempt), the session's canvas and view, the negotiated codec, the input id counter. "
         "All live in script variables; none survives a reload"],
        ["Clipboard", "Read and written only through the browser's clipboard API, under the " + c("Permissions-Policy") + " that names " + c("clipboard-read=(self)")
         + " and " + c("clipboard-write=(self)") + "; the page keeps the last text read or written in " + c("APPUNTI") + " (clipboard state) to avoid echoes, in memory only"],
        ["Other powers", "Pointer lock, keyboard lock and full screen are requested on user gestures. Camera, microphone, geolocation, USB, serial, HID, MIDI, "
         "motion sensors and screen capture are switched off by " + c("Permissions-Policy") + "; the page does not capture the microphone (audio is output only)"],
    ], "«TAB» — What the page keeps on the device") + \
    p("<b>What the page declares to the user.</b> " + c("DECLARATIONS") + " (also " + c("REMOTIX.declarations") + ") holds the sentences shown in " + c("#declaration")
      + ": the codec situation (" + rif("Choosing the codec on the pixel") + "; the field " + c("DECLARATIONS.codec") + "), and the video situation (" + c("DECLARATIONS.video")
      + ": the desktop is on its way, no frame arrived within the wait, the server granted a canvas different from the one requested, the desktop cannot change size). The rule behind them is that what cannot be done is declared, never faked: a capability the page cannot back is "
      "omitted from " + c("HELLO") + ", and the user reads why.") + \
    p("<b>What the page declares to the server.</b> The " + c("HELLO") + " capabilities (" + rif("Capabilities declared by the page") + "), the keyboard layout and the view in "
      + c("ATTACH") + ", and a " + c("FAREWELL") + " when the page goes away. The page sends nothing about the user's computer beyond that: the user agent and system lines "
      "written by " + c("note()") + " stay in the in-memory log and are not transmitted (the " + c("/diary") + " endpoint no longer exists, see the comment in " + c("page.c") + ").")

# ── 15. End of session ────────────────────────────────────────────────────
S15 = p("A session ends for one of four reasons — a " + c("FAREWELL") + " from the server, the transport closing "
        "without one, the page closing it, or the tab going away — and in each case the page must say what it knows "
        "and go back to a usable login form.", lead=True) + \
    table(["How it ends", "What the page does"], [
        [c("FAREWELL") + " on the control channel", "shows the reason sentence (" + c("REASON_TEXT") + "; " + c("0x10")
         + " in green, it is the user's own logout) and returns to the form, for every reason"],
        ["transport closed without " + c("FAREWELL"), "the close code's reason if any, else "
         "“the connection to the server was interrupted: to get back in, type your password again”, and back to the form; the dead "
         "line usually ends here, because its single " + c("CONNECTION_CLOSE") + " often does not arrive"],
        ["the page closes it", c("dismiss()") + ": " + c("FAREWELL") + " on the control channel and the same reason as "
         "the close code — two roads, because Chrome drops a message written just before closing. After a FIN from the "
         "server it is “mute”: only the close code"],
        [c("pagehide") + " (tab closed, page cached)", c("FAREWELL 0x01") + " immediately, without awaiting, so the seat "
         "is freed at once instead of after the silence clock"],
    ], "«TAB» — The four endings") + \
    p(c("back_to_form()") + " undoes everything the session turned on: the audio context is closed, "
      + c("Viewer.close()") + " closes the decoder and bumps the epoch (frames still in flight from before the "
      "farewell would otherwise put the desktop dress back on), the " + c("data-viewer") + " dress is removed, "
      "pointer lock and full screen are released, the canvas returns to 16×16, the logout dialog is hidden, and focus goes to the user name.") + \
    p("<b>The first-frame watch.</b> After " + c("SESSION") + " the page says at once that the desktop is on its "
      "way — after a logout or a reboot the graphical session is born from scratch, measured 9 s and about 32 s — and "
      "after " + c("FIRST_FRAME_WAIT_S") + " = 6 s without a frame it explains with numbers: if the granted "
      "canvas differs from the requested one, that is the likely cause; otherwise the server log has it.") + \
    p("<b>Logging out.</b> The page keeps no key combination for itself: every combination "
      "reaches the remote desktop, and the user leaves from the desktop's own menu, which REMOTIX keeps available "
      "(" + rif("The four desktops") + "). There was once an exit shortcut, " + c("Ctrl+Alt+End") + ", and it was removed because the "
      "local desktop of the user's computer takes that combination before the browser: it closed the PC's session, not the remote one. "
      + c("TERMINATE_SESSION") + " remains in the protocol and the "
      "confirmation dialog (" + c("#confirm") + ") remains in the page, but no gesture opens it today.")

# ── 16. Optional paths ────────────────────────────────────────────────────
S16 = p("Two other ways of drawing exist in the file. The video worker is the default on desktop Firefox and an option elsewhere; the MSE path is off "
        "and kept because it is measurable.", lead=True) + \
    table(["", "Video worker", "MSE (" + c("?draw=mse") + ")"], [
        ["What", "Video streams are transferred to a dedicated worker, which reads them, applies the RCP rules, "
         "decodes and draws on an " + c("OffscreenCanvas") + "; WebTransport and the control channel stay on the main thread",
         "Frames are packed into fragmented MP4 by the page (" + c("MuxMP4") + ") and played by a " + c("<video>")
         + " behind a transparent canvas that keeps receiving input"],
        ["When it is used", "In this order, the first that answers wins: " + c("video=worker") + " in query or fragment: worker; " + c("video=main") + ": main thread; "
         + c("?draw=mse") + ": main thread; desktop Firefox with " + c("VideoDecoder") + ", " + c("Worker") + " and " + c("transferControlToOffscreen")
         + ": worker; everyone else: main thread. “Desktop Firefox” is the Gecko engine on a user agent without " + c("Android") + ", " + c("Mobile") + " or " + c("Tablet"),
         "Only with " + c("?draw=mse") + " (" + c("VIA_MSE") + "). Since 21 Aug 2026 the page no longer takes it by itself where "
         + c("VideoDecoder") + " is missing: that browser is declared unsupported (" + c("DECISIONS.md") + " §7.18)"],
        ["Why", "On desktop Firefox at 4K the main-thread route stalls the main thread more than half of the time (55–64 %, §11.31) and fails the sound; the worker never stalls it "
         "(" + c("DECISIONS-11.md") + " §11.36, option D, decided 15 Oct 2026)", "Hundreds of ms of extra latency (+225 ms Firefox, +415 ms Chrome median) against a 50 ms cap; "
         "the owner judged the result on Firefox for Android irregular and declared that browser unsupported (§7.18)"],
        ["How it is built", "The worker's source is composed at runtime from " + c("Viewer.toString()") + " and "
         + c("read_one_stream.toString()") + " plus a shell supplying " + c("document") + ", " + c("devicePixelRatio")
         + " and the view: one definition, two contexts", "Its own codec probe on the " + c("<video>") + " (H.264 only), "
         "playback speed 1.25× when the buffer is more than 250 ms behind, never seeking"],
        ["Safety net", "The worker is not trusted blindly (" + c("worker_fall_back()") + "): three failures in 10 s (" + c("WORKER_FAILS") + ", " + c("WORKER_FAILS_S")
         + "), or nothing painted within " + c("WORKER_PAINT_S") + " = 5 s of the first keyframe, " + c("WORKER_KEY_S") + " = 8 s without a keyframe, or " + c("WORKER_SILENT_S") + " = 30 s with no stream reported, "
         "make the page go back to the main thread once, for the rest of the page, with one line in the log and " + c("stretches().video_route.fell_back") + " set",
         "Combined with the worker it cannot work; MSE wins and the worker stays off"],
        ["Pitfall", "Any new global used by " + c("Viewer") + " must cross into the worker or it breaks silently: a missing one once gave zero frames and " + c("ROUND is not defined") + " on every frame", ""],
    ], "«TAB» — The two optional drawing paths") + \
    note("the comment above " + c("VIDEO_ASKED") + " in " + c("page.html") + " still calls the Firefox worker default “PROPOSAL … NOT decided, NOT on main”, and a log line says "
         "“default: desktop Firefox (§11.36 D, proposal)”. The code enables it, and " + c("DECISIONS-11.md") + " §11.36 is marked DECIDED D; "
         "the manual follows the code. A live browser proof of the worker default is noted as still to do in the same decision file; the final run of " + c("prove/all.sh") + " "
         "(Firefox included) does not isolate it.", "Comment behind the code.")

# ── 17. Browsers ──────────────────────────────────────────────────────────
S17 = p("The technical minimum is WebTransport <b>and</b> WebCodecs. The table separates what was exercised by the checks of " + c("prove/")
        + " (Chrome and Firefox on Linux, real browsers driven by DevTools and WebDriver) from what the owner has tried by hand and what has never been tried.", lead=True) + \
    table(["Where", "Browser", "Status", "Notes"], [
        ["Linux", "Chrome", "supported, checked", "HEVC where the GPU decodes it, else H.264; the checks run on the four desktops"],
        ["Linux", "Firefox", "supported, checked", "H.264 only (no HEVC on Linux); the WebGL2 drawing path exists because of its read-back cost; the worker is the default; the clipboard from the browser to the desktop is an open item"],
        ["Windows", "Chrome", "declared OK by the owner", "declared on the product line this code comes from (" + c("DECISIONS.md") + " §7.20); not covered by the checks of " + c("prove/") + " and not re-tried on this package"],
        ["Android", "Chrome", "declared OK by the owner", "declared OK (§7.20, §7.19); Samsung DeX with mouse and keyboard on GNOME was tried by the owner on 17 Nov 2026 (clipboard, audio/video, window resize all regular); touch on a 6-inch phone screen is a low priority and was only emulated"],
        ["Android", "Firefox", "<b>out of the project</b>", "No WebCodecs; the page has a sentence that explains it and points to Chrome (when it is shown: see " + rif("Choosing the codec on the pixel") + ")"],
        ["Windows", "Firefox", "never tried", "neither supported nor excluded"],
        ["macOS, iOS", "Safari", "never tried", "WebTransport and WebCodecs exist from Safari 26 on paper; nothing has been verified"],
    ], "«TAB» — Browsers") + \
    p("The rule behind the list: a page runs on three engines written by three teams who do not know REMOTIX "
      "— Blink, Gecko, WebKit — and testing on at least two of them gives back part of the external referee lost "
      "with native clients. Where two agree and the third does not, the defect names itself.") + \
    warn("on Samsung DeX, Chrome delivers mouse moves with no button pressed only around a click (the known "
         "noVNC issue #1727, also seen in KasmVNC #222 and in the native moonlight-android #573); it is not a REMOTIX "
         "defect. The page copes in two ways: since the canvas equals the window every event carries its own "
         "position, so pointing and clicking hit correctly even without hover; and the first "
         "click on the canvas takes Pointer Lock where hover does not arrive (" + c("DECISIONS.md")
         + " §10.29). Details are in " + rif("Mouse and pointer in the classic layout") + ".", "DeX and the pointer.") + \
    ul([
        "Not verified: a real phone with the on-screen keyboard. " + c("prove/check-phone.py") + " is an emulation (Chrome device emulation with touch events), and its header says what only a real phone can show.",
        "Not verified: Safari on macOS and iOS, and Firefox on Windows, have never been opened against REMOTIX.",
        "Not verified: Android's coming desktop mode, which may change the pointer behaviour; the capture rule looks at behaviour, not at the system, so it should adapt by itself.",
    ])

CHAPTER = ("The browser page", [
    ("How the page is served", S1),
    ("Structure of page.html", S2),
    ("Layouts and the states of the document", S3),
    ("The connection sequence", S4),
    ("Capabilities declared by the page", S5),
    ("Choosing the codec on the pixel", S6),
    ("Measuring the decoder ceiling", S7),
    ("Canvas and view", S8),
    ("Asking for the canvas with FIT_CANVAS", S9),
    ("Receiving video frames", S10),
    ("Decoding with WebCodecs", S11),
    ("Drawing paths: WebGL2, bitmaprenderer, 2D canvas", S12),
    ("Measurements and the diagnostics mode", S13),
    ("What the page stores and what it declares", S14),
    ("End of session in the page", S15),
    ("The video worker and the MSE path", S16),
    ("Browsers supported and untested", S17),
])
