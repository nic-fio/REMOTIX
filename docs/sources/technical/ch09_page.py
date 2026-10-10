from build import box, c, code, fig, note, p, rif, seq, steps, table, text, tip, ul, warn, zone

# ── 1. One file ───────────────────────────────────────────────────────────
S1 = p("The whole client is one file, " + c("src/pagina.html") + ": the login page, the RCP/1 client, video "
       "decoding and drawing, audio, clipboard, keyboard, pointer and touch. Nothing is installed on the user's "
       "device and nothing else is downloaded: the page is the product's only client.", lead=True) + \
    table(["What", "How"], [
        ["Served by", c("src/pagina.c") + ", a small TLS-over-TCP server inside the parent process, on the same port "
         "number as QUIC (7447 in the packages: TCP for the page, UDP for WebTransport)"],
        ["Routes", c("/") + " and " + c("/index.html") + " (the page), " + c("/impronta") + " (fingerprint: the certificate "
         "fingerprint as JSON), " + c("/diario") + " (diary: the page's own log lines, carried in the query string, "
         "written into the server log, answer 204). Everything else is 404; the query string and fragment are cut before matching"],
        ["Headers on every answer", c("Cross-Origin-Opener-Policy: same-origin") + ", "
         + c("Cross-Origin-Embedder-Policy: require-corp") + ", " + c("Cross-Origin-Resource-Policy: same-origin")
         + ", " + c("Cache-Control: no-store") + ", " + c("X-Content-Type-Options: nosniff")],
        ["External resources", "None. The Opus decoder (WebAssembly, " + c("OPUS_WASM_B64") + ") and the video probe "
         "streams are embedded in base64"],
        ["Connections", "At most 32 TCP clients at a time (" + c("MAX_CLIENTI") + "); a request header is at most 8 KiB"],
    ], "«TAB» — How the page reaches the browser") + \
    p("Cross-origin isolation is a product requirement, not a bench detail (" + c("SPECIFICHE.md")
      + " §11.5): without it Firefox and Safari round the page's timers to 1 ms, on a latency cap of 50 ms, and "
      "shared memory does not exist. With " + c("require-corp") + " every sub-resource would have to declare its "
      "own policy; the simplest cure is to have none, which is why everything is inline. The isolation is "
      "inherited by the optional video worker, born from a " + c("Blob") + " (measured 13 Aug 2026: "
      + c("crossOriginIsolated") + " true inside the worker, timer grain 0.005 ms).") + \
    table(["Marker", "Replaced with", "Read by"], [
        [c("__IMPRONTA__") + " (fingerprint)", "the base64 SHA-256 of the DER of the current session certificate", "the WebTransport "
         + c("serverCertificateHashes") + " option, as a fallback"],
        [c("__AVVISO__") + " (notice)", "empty, or the ban notice with the hours and minutes left", "the CSS: " + c("#avviso:empty")
         + " hides it, so a banned visitor reads the reason even without JavaScript"],
        [c("__BANNATO__") + " (banned)", c("si") + " (yes) or " + c("no") + ", on " + c("data-bannato") + " of the body", "the script and the ban benches"],
        [c("__RESTANO_MS__") + " (milliseconds left)", "milliseconds left on the ban", c("data-restano-ms") + " of the body"],
    ], "«TAB» — The four markers the server fills while serving") + \
    p(c("pagina_apri()") + " (open the page server) refuses to start if any marker is missing, or if " + c("data-bannato=\"")
      + " or " + c("data-restano-ms=\"") + " occur more than once (a bench that greps the first occurrence "
      "would read the wrong one). The fingerprint is the only server text that enters a JavaScript string, and "
      "it is base64 written by REMOTIX; the ban sentence never enters the script. The TLS side, the certificates "
      "and the ban are described in " + rif("The page server") + ", "
      + rif("serverCertificateHashes and the fingerprint") + " and " + rif("Security model") + ".")

# ── 2. Structure ──────────────────────────────────────────────────────────
S2 = p("The file is about 13 000 lines, most of them comments that carry the reason and the measurement behind "
       "each rule. The code is organised in blocks, and several input blocks are “anchors” owned by different "
       "authors, each writing only inside its own markers.", lead=True) + \
    table(["Block", "Main names", "Covered in"], [
        ["Style", "the login look (" + c("Satinato") + ", i.e. satin, chosen 4 Oct 2026), the desktop styling on " + c("body[data-schermo=\"acceso\"]") + " (screen on)", "this chapter"],
        ["Diagnostics", c("nota()") + " (note: one log line), " + c("registro_visibile()") + " (show the log), the browser and system " + c("MARCA") + " (marker) lines", rif("Measurements made by the page")],
        ["RCP bytes", c("Scrittore") + " (writer), " + c("Lettore") + " (reader), " + c("Canale") + " (channel), " + c("inquadra()") + " (frame a message), tables " + c("TIPO") + " (type), " + c("MOTIVO") + " (reason)", rif("The RCP/1 protocol")],
        ["Video probes", c("SONDE") + " (probes), " + c("SONDE_MISURA") + " (size probes), " + c("sonda_tutto()") + " (probe everything), " + c("misura_massima()") + " (maximum size)", rif("Choosing the codec on the pixel")],
        ["The screen", "class " + c("Schermo") + " (screen): rules of RCP §5.2/§6.2, decoder, drawing paths, counters", rif("Receiving video frames")],
        ["Session", c("collega()") + " (connect), " + c("ascolta_controllo()") + " (listen to the control channel), " + c("avvia_video()") + ", " + c("leggi_uno_stream()") + " (read one stream)", rif("The connection sequence")],
        ["Audio", c("avvia_audio()") + ", the Opus WebAssembly decoder", rif("Audio and clipboard")],
        ["Clipboard", c("appunti_prepara()") + " (prepare the clipboard), " + c("avvia_appunti()"), rif("Audio and clipboard")],
        ["Worker", c("GUSCIO_WORKER") + " (worker shell), " + c("sorgente_worker()") + " (worker source), " + c("accendi_worker()") + " (start the worker)", rif("The optional paths: video worker and MSE")],
        ["Exit", c("torna_al_modulo()") + " (back to the form), " + c("logout_esegui()") + " (perform the logout)", rif("End of session in the page")],
        ["Input anchors", c("F4-INPUT-CLASSICO") + " (mouse and keyboard), " + c("F4-TOCCO") + " (touch), "
         + c("F4-SCORCIATOIE") + " (shortcuts, full screen, keyboard lock)", rif("Input")],
    ], "«TAB» — The blocks of pagina.html") + \
    p("The page defines one main global, " + c("window.REMOTIX") + ", an object <i>to be read</i> by benches and "
      "diagnostics (" + c("schermo") + " the screen, " + c("sondaggio") + " the probe results, " + c("tratti")
      + " the latency stretches, " + c("giro") + " the round trip, " + c("video") + ", " + c("dichiarazioni")
      + " the declarations, " + c("registro") + " the log, " + c("scorciatoie") + " the shortcuts…): nothing in it "
      "changes what the page does. The input anchors meet through " + c("REMOTIX_INPUT") + " (the input stream, "
      "set after " + c("SESSIONE") + "), " + c("REMOTIX_CLASSICO") + ", " + c("REMOTIX_PUNTATORE") + " and "
      + c("REMOTIX_SCORCIATOIE") + ".") + \
    table(["Switch", "Effect", "Purpose"], [
        [c("?registro") + " (log)", "shows the diagnostic log under the page (also " + c("REMOTIX.registro(true)") + ")", "diagnosis"],
        [c("?tela=gl") + " (canvas)", "the WebGL2 path, named explicitly; it is also what no " + c("?tela=") + " gives", "the default"],
        [c("?tela=bmp"), "draw with " + c("bitmaprenderer") + " instead of WebGL2 (any " + c("?tela=")
         + " value other than " + c("gl") + " and " + c("2d") + " does the same)", "A/B comparison"],
        [c("?tela=2d"), "draw on the 2D canvas, the path that showed the 64×192 blocks", "A/B comparison"],
        [c("?tela=desincronizzata") + " (desynchronized)", "asks for a 2D context with " + c("desynchronized: true")
         + "; since it is neither " + c("gl") + " nor " + c("2d") + ", " + c("bitmaprenderer")
         + " is taken first, and the 2D context is created only where " + c("createImageBitmap") + " is missing",
         "latency experiment"],
        [c("?video=worker") + " or " + c("#video=worker"), "decode and draw in a dedicated worker", "experiment, no gain measured"],
        [c("?disegno=mse") + " (drawing)", "draw through MediaSource and a " + c("<video>"), "bench only"],
        [c("?adatta=no") + " or " + c("#adatta=no") + " (fit)", "do not ask the server for a canvas of the window size", "A/B comparison with the pre-15-Aug page"],
        [c("?disposizione=tocco|classico") + " (layout: touch or classic)", "force the touch or the classic layout (also as " + c("#disposizione=…") + ")", "override for benches and diagnosis"],
    ], "«TAB» — URL switches the page reads; none is a user setting") + \
    note("the switches exist so that a comparison changes <b>one</b> variable inside the same page; they are not "
         "per-browser or per-compositor options, and the product has one behaviour without them. The fragment "
         "form (" + c("#…") + ") never reaches the server, so it works on a page served by any static server.",
         "Bench switches, not settings.")

# ── 3. Login and connection ───────────────────────────────────────────────
CONNESSIONE = seq(
    [("Page", "pagina.html", "light"), ("Page server", "pagina.c, TCP", "dark"), ("RCP server", "WebTransport, UDP", "navy")],
    [(0, 1, "GET /impronta"),
     (1, 0, "SHA-256 of the session certificate", True),
     (0, 2, "WebTransport /rcp/1 with the certificate hash"),
     (0, 2, "first bidirectional stream: CIAO (capabilities)"),
     (2, 0, "ECCOMI: version and the server's choices", True),
     (0, 2, "CREDENZIALI: user and password"),
     (2, 0, "AMMESSO, or RESPINTO, or CONGEDO", True),
     (0, 2, "ATTACCA: canvas, view, keyboard layout"),
     (2, 0, "SESSIONE: new or resumed, granted canvas, desktop", True),
     (0, 2, "input stream · ADATTA_TELA"),
     (2, 0, "TELA · one stream per video frame · audio datagrams", True)],
    "«FIG» — From the Connect button to the first frame")

S3 = p("The login form has two fields and a button — " + c("#utente") + ", " + c("#parola") + ", " + c("#vai")
       + " — plus " + c("#esito") + " for the outcome, " + c("#avviso") + " for the ban and " + c("#dichiarazione")
       + " for what the page declares about codecs and video. The ids are stable: the functional suite finds "
       "elements by id, not by text.", lead=True) + CONNESSIONE + \
    steps([
        "<b>Submit.</b> The button is disabled, the outcome cleared; " + c("collega()") + " runs. Whatever "
        "happens, the password field is emptied at the end: it is never kept, and never logged.",
        "<b>WebTransport present?</b> If not, the page says so and stops.",
        "<b>Fingerprint.</b> " + c("impronta()") + " fetches " + c("/impronta") + " before every attempt, because a "
        "tab left open for two weeks holds the fingerprint of a certificate already rotated. If the fetch is "
        "rejected by the network (" + c("TypeError") + ": nobody listens), the page says at once that the server "
        "does not answer and does not open WebTransport — before this rule (D-009) Firefox waited the 30 s of its "
        "QUIC handshake. Any other failure falls back to the fingerprint served with the page, and says so.",
        "<b>WebTransport</b> to " + c("https://<host>/rcp/1") + " with " + c("allowPooling: false") + " and "
        + c("serverCertificateHashes") + ": the browser checks the fingerprint, not a certificate chain — the only "
        "mechanism browsers offer to a server without a domain (RCP.md §4.1-bis).",
        "<b>Listen first.</b> Video streams, audio datagrams and clipboard streams are listened to <i>before</i> "
        "the handshake ends: a server that opened one before " + c("SESSIONE") + " violates RCP §2.5, and the "
        "violation is only visible to someone already listening.",
        "<b>" + c("CIAO") + "</b> (hello) with the capabilities (" + rif("Capabilities declared by the page") + "), after waiting for the "
        "codec probes. <b>" + c("ECCOMI") + "</b> (here I am): a version other than 1 is refused with " + c("VERSIONE_INCOMPATIBILE")
        + " before the password leaves.",
        "<b>" + c("CREDENZIALI") + "</b> (credentials). " + c("RESPINTO") + " (rejected) shows the reason and stops (a second attempt needs a new "
        "connection); a " + c("CONGEDO") + " (goodbye) shows its reason and stops; " + c("AMMESSO") + " (admitted) continues.",
        "<b>" + c("ATTACCA") + "</b> (attach) carries the canvas to ask for (" + c("tela_da_chiedere()") + "), the view ("
        + c("misura_vista()") + ") and the keyboard layout (" + c("disposizione()") + "). <b>" + c("SESSIONE") + "</b> says "
        "new or resumed, the granted canvas and the desktop name. A granted canvas different from the requested "
        "one is declared to the user (RCP §4.5 allows it).",
        "<b>After " + c("SESSIONE") + "</b>: the single input stream is opened, the video is negotiated with the decoder, "
        "the first-frame watch starts, the control channel is read in a loop (" + c("ascolta_controllo()")
        + "), and " + c("ADATTA_TELA") + " (fit the canvas) is sent once for the window size.",
    ]) + \
    p("The keyboard layout is guessed from " + c("navigator.language") + " (" + c("en") + " → " + c("us")
      + ", except " + c("en-GB") + " → " + c("gb") + " and " + c("en-IE") + " → " + c("ie") + "; about thirty languages "
      "whose XKB name equals the ISO code pass through, a few are mapped, such as " + c("sv") + " → " + c("se")
      + " and " + c("da") + " → " + c("dk") + "; the rest falls back to " + c("us") + "); a page cannot know the physical keyboard, and choosing it is described in "
      + rif("Keyboard layout negotiation") + ". The input stream coalesces pointer moves: when the writer's " + c("desiredSize")
      + " is at or below zero, a " + c("PUNTATORE") + " (pointer move) is held aside and replaced by the next one, and any key or "
      "button pushes it out first — measured from DeX on 14 Aug 2026, median round trip 135 ms but worst 2161 ms, "
      "a queue rather than a slow network. Keys and buttons are never dropped.") + \
    p("Some user-facing texts of the page — the reason sentences, the declarations, the logout dialog — are "
      "still in Italian, while the login page is in English; " + c("DECISIONI.md") + " §10.32 lists their "
      "translation as pending work.")

# ── 4. Capabilities ───────────────────────────────────────────────────────
S4 = p("The CIAO capabilities say what <b>this</b> browser can do, measured where possible. An empty value is a "
       "protocol error (RCP §4.3), so a capability with nothing to say is omitted, and the omission is logged.",
       lead=True) + \
    table(["Capability", "Value", "Where it comes from"], [
        [c("video.codec"), c("hevc,h264") + " or a subset", "only the codecs whose probe was actually painted, in preference order"],
        [c("video.profondita") + " (depth)", c("8") + " and/or " + c("10"), "the depths that painted on at least one good codec; 8 must be present"],
        [c("video.livello") + " (level)", c("5.1"), c("LIVELLO_DICHIARATO") + "; not measurable from the page (browsers do not enforce levels): the server checks it"],
        [c("video.misura_massima") + " (maximum size)", "e.g. " + c("3840x2160"), "the decoder's ceiling measured on the pixel (" + rif("Measuring the decoder ceiling") + "); omitted when not measured"],
        [c("audio.codec"), c("opus,pcm") + " or " + c("pcm"), "opus only if the WebAssembly decoder loads, or else " + c("AudioDecoder") + " accepts Opus"],
        [c("input.tocco") + " (touch)", c("no"), "constant"],
        [c("appunti.testo") + " (clipboard text)", c("si"), "constant"],
        [c("client.nome"), c("remotix-pagina 0.1.0"), "constant"],
    ], "«TAB» — The capabilities sent in CIAO") + \
    p("Declaring something the browser cannot do does not give an error; it gives a black canvas or silence, "
      "because the server must choose within the intersection following the client's order. Declaring "
      + c("opus") + " on an engine that cannot decode it once made the server send fifty datagrams a second into a "
      + c("continue") + " — and the PCM fallback, which exists to be Opus's positive control, never came into play.")

# ── 5. Codec probes ───────────────────────────────────────────────────────
S5 = p("The codec is not chosen by asking the browser's APIs. It is chosen by decoding a real keyframe and "
       "reading the pixels back.", lead=True) + \
    p("Measured on 12 August 2026 on Firefox 140 ESR, for all seven HEVC strings: "
      + c("navigator.mediaCapabilities.decodingInfo()") + " said supported, smooth and power-efficient; "
      + c("canPlayType()") + " said “probably”; " + c("VideoDecoder.isConfigSupported()") + " said false; and no "
      "pixel arrived. Three witnesses, two of them false and agreeing with each other. The page never calls the "
      "first two. " + c("isConfigSupported") + " is used as a <b>filter</b> only — when it says no the pixel "
      "never arrives, when it says yes it proves nothing (Chrome accepts a level-3.0 declaration on a 5.1 stream "
      "and paints anyway).") + \
    table(["Step", "Detail"], [
        ["Probe frames", c("SONDE") + ": one 64×48 keyframe per codec and depth (" + c("hevc-8") + ", "
         + c("hevc-10") + ", " + c("h264-8") + "; two AV1 probes remain in the table, unused), left half red, right half blue, "
         "generated by " + c("banchi/02-pagina-sonda-codec.py")],
        ["Strings tried", "per codec, the declared level first, then a low-level fallback: " + c("hev1.1.6.L153.B0")
         + " / " + c("hev1.1.6.L93.B0") + " (Main), " + c("hev1.2.4.L153.B0") + " (Main10), " + c("avc1.640033")
         + " / " + c("avc1.64001f") + " (High 5.1 / 3.1)"],
        ["Decoder config", c("codedWidth") + ", " + c("codedHeight") + ", " + c("optimizeForLatency: true")
         + ", no " + c("description") + " (the stream is Annex B)"],
        ["Verdict", c("dipingi_sonda()") + " (paint the probe) fills a canvas with dark magenta, decodes, draws the frame, reads it back with "
         + c("getImageData") + " and requires each half to be closer to its own colour than to the other one. "
         "Black, magenta or a uniform fill cannot pass. Timeout 2.5 s"],
        ["When", "at page load (" + c("SONDAGGIO") + ", the probe survey; not on the MSE path), so the answer is ready when the user presses Connect; "
         "the cost is tens of ms on a capable engine"],
    ], "«TAB» — The codec probe") + \
    p("The preference is " + c("PREFERENZA") + " = " + c("[\"hevc\", \"h264\"]") + ": HEVC where it paints, "
      "H.264 as the universal fallback; the server makes the final choice within the intersection. AV1 left the "
      "product in August 2026 (decided by the user on 17 August, removed from the page on 20 August; " + c("DECISIONI.md") + " §1.13-ter): Firefox for Android had neither HEVC nor "
      "AV1, H.264 is the only codec in hardware at both ends, and Firefox's AV1 decoder painted rectangular blocks "
      "where Chrome and " + c("dav1d") + " were clean on the same bytes. Its RCP number, 2, stays reserved "
      "forever (" + c("CODEC_RCP") + "): reusing it would make an old client paint garbage without an error. "
      "The H.264 string is " + c("avc1.640033") + " (High, level 5.1), the same the server now derives from the "
      "SPS; the earlier " + c("avc1.640032") + " (5.0) cannot reach 3840×2160.") + \
    table(["Probe result", "What the declaration box tells the user"], [
        ["No " + c("VideoDecoder") + " at all", "this browser lacks WebCodecs, the only way REMOTIX draws; today that is Firefox for Android, declared unsupported — use Chrome there"],
        ["WebCodecs but no codec painted", "the session can open but there will be no image"],
        ["H.264 only", "HEVC is not decoded here; H.264 is used, which costs more bandwidth for the same quality"],
        ["HEVC paints but the server chose H.264", "a one-line note"],
    ], "«TAB» — The codec declarations") + \
    p("If no codec reaches the pixel, " + c("video.codec") + " is omitted and the server answers "
      + c("NIENTE_IN_COMUNE") + " (nothing in common); the page writes its own explanation first, because only the page knows which "
      "probe failed and why. Whether decoding happens in hardware is not observable from JavaScript, and the page "
      "never claims it.")

# ── 6. Decoder ceiling ────────────────────────────────────────────────────
S6 = p(c("video.misura_massima") + " is the largest frame the browser's <b>decoder</b> can bring to the "
       "pixel. It is not the screen size: a phone's decoder has limits its screen does not declare, and a desktop "
       "screen can be smaller than what its browser decodes.", lead=True) + \
    p("Until 13 August 2026 the page put " + c("screen.width × devicePixelRatio") + " in this field. On a screen "
      "1010 pixels tall the server granted a 1794×1010 canvas while the stage captured 1920×1080, refused to send "
      "frames of the wrong size, and the user saw nothing — even in full screen, since " + c("screen.height")
      + " does not change with F11. The test pages had hand-written 3840×2160 and never showed it.") + \
    table(["Rule", "Why"], [
        ["A ladder per codec: 320×240, 640×480, 1280×720, 1920×1080, 2560×1440, 3840×2160 (" + c("SONDE_MISURA") + ")",
         "320×240 is the smallest legal canvas; 3840×2160 is within level 5.1, the level declared in the same CIAO"],
        ["Each step must paint the two colours <b>and</b> the output frame must have exactly that size",
         "A smaller frame, scaled for the read-back, would pass the colour test and lie about the size"],
        ["The read-back canvas is 64×48 (" + c("rl") + "/" + c("ra") + ")", "Reading back 33 Mpixel per step would cost more than decoding"],
        ["Stop at the first failing step", "Capability is assumed monotonic in size; the log names the step where it stopped"],
        ["The value is the minimum across declared codecs", "The server chooses the codec afterwards, so the ceiling must hold for either"],
        ["8-bit ladder frames only", "8 is the depth both sides must support; a 10-bit ladder would double the startup cost without a measured reason"],
        ["Omitted on the MSE path", "The ladder needs " + c("VideoDecoder") + "; a missing value is legal, an invented one breaks phones"],
    ], "«TAB» — How misura_massima() measures the ceiling") + \
    p("If a codec paints at 64×48 but not even at 320×240, the page declares 320×240 and tells the user the image "
      "may not arrive at all. The cost of the ladder is logged on every load (" + c("sondaggio.misura.ms") + ").")

# ── 7. Canvas and view ────────────────────────────────────────────────────
TELA = fig(
    zone(20, 12, 860, 236, "Browser window: the view, in physical pixels")
    + box(150, 52, 600, 150, "Canvas buffer = the frame", "the granted canvas, width and height multiples of 16", "navy")
    + text(85, 132, "band", 12, "#475569", "600")
    + text(815, 132, "band", 12, "#475569", "600")
    + text(450, 228, "Bands are the parent's black background, outside the buffer: never drawn, never encoded", 11.5, "#334155"),
    900, 250, "«FIG» — The canvas buffer holds exactly the frame; CSS centres it and scales it to at most 1:1")

S7 = p("Two sizes must never be confused. The <b>canvas</b> (" + c("tela") + " in the code) is the remote desktop's size: it belongs to the "
       "session, is fixed at attach and reattach, and is what the frames carry. The <b>view</b> (" + c("vista") + ") is how "
       "much the page has to draw in: it belongs to the connection and changes with the window.", lead=True) + TELA + \
    table(["Function", "Rule"], [
        [c("misura_vista()"), c("documentElement.clientWidth/clientHeight") + " × " + c("devicePixelRatio")
         + ", <b>truncated</b>. " + c("clientWidth") + " excludes the scrollbar, unlike " + c("innerWidth")
         + "; rounding up at a fractional ratio (Windows at 150 %) declared one pixel too many, which brought "
         "a scrollbar, a scale of 0.965 and the whole image resampled"],
        [c("tela_da_chiedere()") + " (canvas to ask for)", "the view clamped to 320–4096 × 240–2304 and truncated to <b>multiples of 16</b> on both sides"],
        [c("Schermo.cornice()") + " (frame)", "scale = min(view/frame width, view/frame height, 1): never enlarged; CSS width and "
         "height = frame × scale ÷ " + c("devicePixelRatio") + "; " + c("image-rendering: pixelated")
         + " only at scale exactly 1, otherwise the engine interpolates"],
        [c("Schermo.adatta_vista()") + " (fit the view)", "measures twice: the canvas is part of the layout, and a first measure can "
         "include a scrollbar that the resize itself removes"],
        [c("rinegozia_vista()") + " (renegotiate the view)", "on " + c("resize") + ", at the next animation frame: re-measures the view and "
         "rescales. <b>Nothing is sent</b> and the canvas does not change"],
    ], "«TAB» — The geometry functions") + \
    p("Since 15 August 2026 (" + c("DECISIONI.md") + " §5.0-sexies) the canvas takes the size of the client's "
      "window. Scale 1 makes coordinate conversion the identity, removes the black bands and the interpolated "
      "text, and the request at attach restarts the capture stream, which makes Mutter deliver a frame at once "
      "instead of after 4.4 s of waiting on a still scene. Since 17 August (§5.1-bis) the canvas never changes "
      "while the session lives: resizing the window only rescales the image. Resizing an output could not be done "
      "on KWin ≤ 6.7.4 and, where it works, it rearranges the user's windows; the user did not want a product that "
      "behaves differently depending on the compositor. A new size is taken by reconnecting.") + \
    table(["Why multiples of 16", ""], [
        ["Width", "Measured 24 Sep 2026: Firefox 140 does not honour the horizontal cropping declared in the H.264 "
         "SPS. With a width that is not a multiple of 16 it drew the green padding stripe (8 px at 1400, 4 at 3788) "
         "and squeezed the image into the declared width. Chrome 154 was correct"],
        ["Height", "The same evening the user found the pointer “a few millimetres off” on Firefox: with hardware "
         "decoding it also squeezed vertically (canvas 962, coded 976), so a click landed up to 13–14 px higher "
         "than drawn at the bottom of the screen"],
        ["Cost", "The canvas may be up to 15 px narrower and shorter than the window: two black bands of at most "
         "7–8 px, outside the buffer. Common code for every engine, no branch per browser"],
    ], "«TAB» — The 16-pixel step") + \
    p("The maximum 4096×2304 dates from 1 October 2026 (the user: 4096 maximum width is fine): H.264 on the Intel "
      "card stops at 4096 per side and Firefox on Linux receives only H.264. A larger window gets the maximum on the "
      "side that overflows (5120×2880 → 4096×2304, 5120×1440 → 4096×1440), shown at scale 1 with bands. The limits "
      "are protocol constants (" + c("RCP_TELA_L_MASSIMA") + " and its siblings in " + c("src/rcp.h") + "); the "
      "server applies the same rule in " + c("rcp_misura_ammessa()") + " (size allowed).") + \
    p(c("html { overflow-y: scroll }") + " keeps the vertical scrollbar always present, so turning the canvas on "
      "never changes " + c("clientWidth") + ". The canvas has " + c("tabindex=\"-1\"") + ", without which its "
      + c("focus()") + " calls do nothing and the keyboard stays in the password field.") + \
    note("a change of " + c("devicePixelRatio") + " with the window still (page zoom, a window dragged to a screen "
         "with another scale) is not handled: the emulated test delivered no event at all, and a cure needs a "
         "measurement with real zoom. The " + c("VISTA") + " (view) message is never sent after a resize either: no "
         "server component reads it in RCP/1.", "Not settled yet.")

# ── 8. ADATTA_TELA ────────────────────────────────────────────────────────
S8 = p("The canvas is requested once per session, at attach, with " + c("ADATTA_TELA") + ". The server answers "
       "with " + c("TELA") + " (canvas): adopted, or refused with a reason.", lead=True) + \
    table(["Answer", "What the page does"], [
        [c("TELA(ADATTATA)") + " (canvas adopted)", c("tela_adattata()") + ": opens a tolerance window in which frames at the previous size are "
         "still accepted and drawn; the decoder is <b>not</b> reconfigured on the message but on the first keyframe at the "
         "new size (RCP §5.2), which also closes the window"],
        [c("TELA(RIFIUTATA)") + " (refused), reason 1 " + c("COMPOSITORE_INCAPACE") + " (compositor incapable)", "no further requests in this session; the user "
         "reads that the desktop cannot change size and the browser adapts the image"],
        ["reason 2 " + c("MISURA_FUORI_LIMITI") + " (size out of limits)", "not repeated"],
        ["reason 3 " + c("NON_ORA") + " (not now)", "repeated <b>once</b> after " + c("TELA_RICHIESTA_RIPETI_MS") + " = 4 s — once per page load, since the flag "
         + c("tela_richiesta_ripetuta") + " is never reset, so a second session in the same tab does not retry: often it "
         "means “not yet” (measured: the stage mounted 2.2 s after a server restart)"],
        ["any refusal", "if it declares a canvas different from the one the page believes, the server wins"],
    ], "«TAB» — The answers to ADATTA_TELA") + \
    p("The control channel and the video streams are independent QUIC streams, so a frame at the new size can "
      "arrive <i>before</i> the " + c("TELA") + " that announces it. While an " + c("ADATTA_TELA") + " is "
      "unanswered (" + c("attese_tela") + ", the pending canvas requests, &gt; 0), a frame at an unannounced size is held (" + c("trattieni()")
      + ", hold) and judged again when the answer arrives. With no request in flight, such a frame is "
      + c("ERRORE_PROTOCOLLO") + " at once — the condition is a request in flight, not a number of frames "
      "(finding P21, 13 Aug 2026, which replaced an earlier limit of eight frames). The page compares a new request with "
      "the size it is <i>going to</i>, not the one in force, so a window moved and moved back before the answer "
      "is not left at the wrong size.")

# ── 9. Receiving video ────────────────────────────────────────────────────
S9 = p("Each video frame arrives on its own unidirectional stream, opened by the server in frame order. "
       + c("avvia_video()") + " reads the incoming streams and " + c("leggi_uno_stream()") + " collects each one.",
       lead=True) + \
    table(["Rule", "Detail"], [
        ["Delivered in opening order", "Reads are chained: stream N is handed over only after N−1. Until 22 Sep 2026 "
         "they were read in parallel and judged when they <i>finished</i>; on Firefox 140 at 245 Mbit/s a 512 876-byte "
         "frame completed 2 ms after its 3 763-byte successor, 173 false holes out of 173, 347 useless key requests a "
         "minute. The price: a large frame holds the ones behind it, which the decoder would do anyway"],
        ["FIN versus RESET", "A " + c("read()") + " that ends with " + c("done") + " is a complete frame; one that "
         "throws is a " + c("RESET_STREAM") + ": the bytes are discarded, never given to the decoder, and treated as a hole"],
        ["16 MiB", "A stream longer than the RCP §6.2 cap closes the session with " + c("ERRORE_PROTOCOLLO")],
        ["Channel byte", "The high byte of the first two bytes says the channel: 0x03 video, 0x02 clipboard; anything else closes"],
    ], "«TAB» — Reading the unidirectional streams") + \
    code("""
offset  size  field
 0      u16   tipo      type: 0x0301 keyframe, 0x0302 delta
 2      u16   codec     1 hevc, 3 h264 (2 reserved: av1)
 4      u32   larghezza width
 8      u32   altezza   height
12      u32   numero    frame number, 0 reserved, wraps to 1
16      u64   istante   instant: server monotonic clock, microseconds
24      u32   input     last input id applied when captured (0 = none)
28      ...   Annex B data
""", "text", "The 28-byte video header (RCP.md §6.2), big-endian, read by Schermo.leggi_intestazione() (read the header)") + \
    p("The reader of these 28 bytes is written from the protocol table, not copied from the bench's reader: two "
      "independent implementations of the same bytes are part of the referee, and a disagreement is a gift. "
      + c("Schermo.consegna()") + " (deliver) then applies the rules in a fixed order:") + \
    steps([
        "type must be key or delta; codec must be the negotiated one; otherwise " + c("ERRORE_PROTOCOLLO") + ";",
        "the " + c("input") + " field closes an input round trip (" + rif("Measurements made by the page") + ");",
        "number 0 is a protocol error;",
        "<b>order before size</b>: a number not after the last delivered one (mod 2³²) is dropped without looking "
        "at its size — otherwise the keyframe that closes a tolerance window, overtaking older frames, would close "
        "the session;",
        "size: the canvas in force or a tolerated one; an unannounced size is held if an " + c("ADATTA_TELA")
        + " is pending, a size that was in force and no longer is closes the session;",
        "a jump in numbers is a <b>hole</b>: one " + c("RICHIEDI_CHIAVE") + " (request a keyframe) with the last delivered "
        "number, repeated at most once a second while the hole stays open (" + c("Schermo.buco()") + "); the last "
        "good image stays on screen, deltas are not even given to the decoder until a keyframe arrives (RCP §5.2) — "
        "a delta referencing a missing frame does not error, it just decays;",
        "a frame whose size differs from the decoder's configuration is decoded only if it is a keyframe at the "
        "canvas in force (then the decoder is reconfigured); otherwise it is dropped and treated as a hole;",
        "decode, with the server's " + c("istante") + " as timestamp.",
    ])

# ── 10. Decoding ──────────────────────────────────────────────────────────
S10 = p("Decoding uses one " + c("VideoDecoder") + " per session, configured with the string the probe saw paint, "
        "the frame size and " + c("optimizeForLatency: true") + ". Painting happens <b>inside</b> the decoder's "
        "output callback, not on " + c("requestAnimationFrame") + ": an extra animation frame would add up to one "
        "display interval to a budget worth two and a half.", lead=True) + \
    p(c("Schermo.riconfigura()") + " (reconfigure) creates the decoder lazily and recreates it if an error closed it: after an "
      "error a " + c("VideoDecoder") + " is " + c("closed") + " and every " + c("configure()") + " throws, which "
      "once made a session unrecoverable in silence. A decoder error is treated as a hole and asks for a keyframe.") + \
    p("<b>The decoder-queue skip.</b> Measured 14 Aug 2026 (bench 04-b30, scene at 58 draws/s): the server sent "
      "39.6 frames/s, the page drew 34.7, nobody dropped the excess, and the delay between " + c("decode()")
      + " and the callback grew by ~108 ms every second — 4 650 ms after 43 s, with every frame counter green. "
      "The cause was a 34 ms " + c("drawImage") + " of the 2D path. The cure skips the <i>drawing</i>, never the "
      "decoding, so the delta chain is intact and no key is needed. Since 26 Sep 2026 the rule is weighted by the "
      "measured drawing cost:") + \
    code("""
skip this frame  if  decodeQueueSize > 2  and  decodeQueueSize * costo_disegno() > 16 ms
costo_disegno()   = drawing cost: median time the callback holds the main thread
                    (+ median transfer-to-glass on the bitmaprenderer path)
""", "text", "Schermo.dipingi(): when a decoded frame is not drawn") + \
    p("With a 34 ms drawing cost the rule fires at the old threshold; with WebGL2 at 0.26 ms it practically never "
      "fires, because skipping a 0.26 ms draw gains nothing — when the decoder itself is behind, the cure is the "
      "server's rate regulator. Every skipped frame is counted (" + c("saltati_coda") + ", skipped by the queue): a rate that falls "
      "without a count would violate I1.") + \
    table(["Counter", "Meaning"], [
        [c("consegnati") + " (delivered)", "frames given to " + c("decode()")],
        [c("usciti") + " (out)", "frames out of the decoder (first line of the callback)"],
        [c("dipinti") + " (painted)", "frames that reached the glass — the measure the first-frame watch reads"],
        [c("saltati_coda"), "decoded and not drawn by the queue rule"],
        [c("tardive") + " (late)", c("createImageBitmap") + " results older than one already shown, discarded"],
        [c("in_bmp") + ", " + c("bmp_falliti") + " (failed)", "conversions pending, conversions or uploads failed"],
        [c("buchi") + " (holes), " + c("chiavi_chieste") + " (keys requested)", "holes opened, key requests sent"],
        [c("scartati_ordine") + ", " + c("scartati_misura") + " (dropped for order, for size), " + c("trattenuti")
         + " (held), " + c("tollerati") + " (tolerated)", "the size and order rules at work"],
    ], "«TAB» — The counters of the screen object (" + c("REMOTIX.schermo.conti") + ")") + \
    p("The counters close, within a session: " + c("consegnati = usciti + inside the decoder") + " and "
      + c("usciti = saltati_coda + dipinti + tardive + in_bmp + bmp_falliti") + ". They were added on 23 Sep 2026 "
      "after a Firefox session showed 8 952 delivered and 6 929 drawn, with 2 007 frames that no counter named.")

# ── 11. Drawing ───────────────────────────────────────────────────────────
S11 = p("The decoded " + c("VideoFrame") + " reaches the screen by one of three paths, chosen once when "
        + c("Schermo") + " is built: a canvas takes only one context, so the choice cannot change during a "
        "session.", lead=True) + \
    table(["Path", "When", "How", "History"], [
        ["<b>WebGL2</b> (default)", "unless " + c("?tela=") + " names another path; if " + c("getContext(\"webgl2\")")
         + " fails, the next path is taken and logged", c("texImage2D(VideoFrame)") + " into a texture and one "
         "full-canvas triangle; the frame is closed right after the upload", "Default since 26 Sep 2026 "
         "(" + c("DECISIONI.md") + " §9.4)"],
        [c("bitmaprenderer"), c("?tela=bmp") + " (or any other value except " + c("gl") + " and " + c("2d")
         + "), or no WebGL2", c("createImageBitmap(frame)") + " then "
         + c("transferFromImageBitmap()") + "; asynchronous, ordered by a serial number and an epoch", "The cure of the blocks, 17–20 Aug 2026 (§5.4)"],
        ["2D canvas", c("?tela=2d") + ", or neither of the above", "a hidden 2D staging canvas ("
         + c("deposito") + "), then " + c("drawImage") + " to the visible one", "The original path; shows the blocks"],
    ], "«TAB» — The three drawing paths") + \
    p("<b>The blocks.</b> In August 2026 the user saw rectangular blocks of 64×192 pixels in still areas. They "
      "were hunted suspect by suspect, with a measurement each: the capture was clean, the encoder was clean (0 "
      "damaged superblocks out of 600 through " + c("ffmpeg") + "), " + c("VideoFrame.copyTo") + " was clean, and "
      + c("getImageData") + " after the draw found 0 wrong pixels out of 180 000 — while a phone photo of the same "
      "canvas showed the rectangles. The pixels entered the 2D canvas correctly and broke on the way to the screen, "
      "in a stretch no API can read: " + c("getImageData") + " reads the backing store, not what the compositor "
      "shows. Firefox and Chrome behaved alike, and a " + c("<video>") + " on the same GPU was clean. The "
      + c("bitmaprenderer") + " context has no 2D backing store, and the user's verdict on it was “NO ARTEFACTS!”. "
      "A second, overlapping defect on Firefox was its AV1 decoder, cured by the move to H.264.") + \
    p("<b>WebGL2.</b> The stress campaign of phase 16 (anomaly A1) found that on Firefox the "
      + c("bitmaprenderer") + " path reads every frame back from the GPU synchronously — about 34 ms at 4K — and the "
      "page skipped 11–62 % of frames. WebGL2's " + c("texImage2D") + " has a fast path in Firefox (DMA-BUF and a "
      "GPU blit, YUV→RGB without read-back) when level 0, offset 0, " + c("RGBA/UNSIGNED_BYTE") + ", no unpack skip, "
      "default colour space and visible rectangle equal to the coded one. Measured 26 Sep 2026 on Firefox at 4K: "
      "drawing 34 ms → 0.26 ms, skipped frames 60 % → 12 % (the rest was the old skip rule, then weighted by the "
      "drawing cost); the user, with a 4K video and a 30 000-fish WebGL aquarium: “the image is perfect, 45 fps "
      "steady, no stutter”, and no blocks. The multiple-of-16 canvas keeps the visible rectangle equal to the coded "
      "one; the log says once whether the fast path is possible.") + \
    table(["Event", "WebGL2 path behaviour"], [
        [c("webglcontextlost"), c("preventDefault()") + " to ask the context back; frames are closed and counted in "
         + c("bmp_falliti") + "; a log line if it is not back within 3 s"],
        [c("webglcontextrestored"), "program and texture rebuilt; the next frame repaints everything (no key needed)"],
        ["program does not link", "the canvas stays black and says so: a canvas that had WebGL cannot take another "
         "context, and swapping the element would detach every input handler bound to it. The fallback is the next "
         "page load with " + c("?tela=bmp")],
    ], "«TAB» — Context loss on the WebGL2 path") + \
    p("On every path the buffer is set to the frame size only when it changes (writing " + c("canvas.width")
      + " clears it), explicitly: Chrome, unlike Firefox, does not resize a " + c("bitmaprenderer") + " canvas "
      "on transfer, and a 16×16 buffer stretched by CSS once sent every click to the top-left corner. The pointer "
      "is never painted on the canvas; it is a CSS cursor or a separate element (" + rif("Mouse and pointer in the classic layout") + ").") + \
    note("when " + c("Schermo") + " is built on the WebGL2 path, it writes a log line describing that path as a "
         "candidate “requested with " + c("?tela=gl") + "”, “not the default”; the context-loss lines likewise advise "
         "reloading without " + c("?tela=gl") + ". Those texts predate 26 September and are stale. " + c("REMOTIX.tratti().strada") + " reports "
         + c("webgl2-a-richiesta") + " (WebGL2 on request) for the same reason.", "A stale label.")

# ── 12. Measurements ──────────────────────────────────────────────────────
S12 = p("The page measures its own share of the latency and exposes it, so that benches read the path really "
        "in use instead of a copy of it.", lead=True) + \
    table(["Name in " + c("REMOTIX.tratti()"), "From → to"], [
        [c("8_decode_richiamo"), c("decode()") + " → decoder callback (" + c("richiamo") + " = callback, " + c("vetro") + " = glass)"],
        [c("9a_richiamo_chiamata"), "callback → start of the conversion (should be ~0)"],
        [c("9b_conversione"), "conversion or texture upload"],
        [c("10_vetro"), "transfer to the canvas or " + c("drawArrays")],
        [c("9_10_richiamo_vetro"), "callback → canvas changed"],
        [c("11_vetro_prossimo_quadro"), "canvas changed → next animation frame (one sample in 16): a lower bound of when the pixel <i>can</i> light"],
        [c("coda_cons") + ", " + c("coda_usc") + ", " + c("eta_ms") + ", " + c("ric_ms"), "decoder queue at delivery and at output, age of the output frame, main-thread time of the callback"],
    ], "«TAB» — The client-side stretches (median, p05, p95, min, max and n for each)") + \
    p(c("REMOTIX.giro") + " (round trip) is the full input round trip: each input message records when it left, and the "
      + c("input") + " field of a later frame closes it. It is a lower bound — it stops when the frame arrives, not "
      "when it is drawn. " + c("SCENA") + " (scene) samples the age of the image at every pointer move, which distinguishes "
      "“the desktop is frozen” from “the hand moved over the wallpaper and nothing changed”. " + c("voff_ms()")
      + " (glass time minus the frame's server instant) is the video half of the audio/video distance; with the "
      "audio's " + c("aoff_ms()") + ", the unknown clock offset cancels out (" + rif("Audio and clipboard") + ").") + \
    p("Lines passed to " + c("nota()") + " that contain " + c("MISURA") + " (measurement), " + c("MARCA") + " or ⛔ are also "
      "sent to the server with " + c("fetch(\"/diario?…\")") + " and appear in its log as "
      + c("📄 la pagina di <address> dice: PAGINA …") + " (the page of &lt;address&gt; says): with the desktop at full screen the page's own log is unreachable. The first lines identify the "
      "browser (user agent, screen, ratio, WebCodecs), the system (" + c("userAgentData") + " on Chromium, "
      + c("navigator.oscpu") + " on Firefox, each value labelled with its source) and what the engine offers "
      "without WebCodecs.") + \
    tip("open the page with " + c("?registro") + " to see the log under the desktop, or call "
        + c("REMOTIX.registro(true)") + " from the console; " + c("REMOTIX.tratti()") + " and "
        + c("REMOTIX.schermo.conti") + " can be read at any time.", "Reading the page.")

# ── 13. End of session ────────────────────────────────────────────────────
S13 = p("A session ends for one of four reasons — a " + c("CONGEDO") + " from the server, the transport closing "
        "without one, the page closing it, or the tab going away — and in each case the page must say what it knows "
        "and go back to a usable login form.", lead=True) + \
    table(["How it ends", "What the page does"], [
        [c("CONGEDO") + " on the control channel", "shows the reason sentence (" + c("MOTIVO") + "; " + c("0x10")
         + " in green, it is the user's own logout) and returns to the form — for <b>every</b> reason, not only two "
         "of fifteen as until 16 Aug 2026"],
        ["transport closed without " + c("CONGEDO"), "D-002 (25 Sep 2026): the close code's reason if any, else "
         "“the connection with the server was interrupted, type the password again”, and back to the form; the dead "
         "line usually ends here, because its single " + c("CONNECTION_CLOSE") + " often does not arrive"],
        ["the page closes it", c("congeda()") + " (send the goodbye): " + c("CONGEDO") + " on the control channel and the same reason as "
         "the close code — two roads, because Chrome drops a message written just before closing. After a FIN from the "
         "server it is “mute”: only the close code"],
        [c("pagehide") + " (tab closed, page cached)", c("CONGEDO 0x01") + " immediately, without awaiting, so the seat "
         "is freed at once instead of after the 30 s silence clock"],
    ], "«TAB» — The four endings") + \
    p(c("torna_al_modulo()") + " undoes everything the session turned on: the audio context is closed, "
      + c("Schermo.chiudi()") + " closes the decoder and bumps the epoch (frames still in flight from before the "
      "farewell would otherwise put the desktop dress back on), the " + c("data-schermo") + " dress is removed, "
      "pointer lock and full screen are released, the canvas returns to 16×16, the logout dialog is hidden, and focus goes to the user name. "
      "The rule written on it: whoever switches a state on must know how to switch it off.") + \
    p("<b>The first-frame watch.</b> After " + c("SESSIONE") + " the page says at once that the desktop is on its "
      "way — after a logout or a reboot the graphical session is born from scratch, measured 9 s and ~32 s — and "
      "after " + c("ATTESA_PRIMO_FOTOGRAMMA_S") + " (first-frame wait) = 6 s without a frame it explains with numbers: if the granted "
      "canvas differs from the requested one, that is the likely cause; otherwise the server log has it.") + \
    p("<b>Logging out.</b> The page keeps no key combination for itself since 17 August 2026: every combination "
      "reaches the remote desktop, and the user leaves from the desktop's own menu, which REMOTIX keeps available "
      "(" + rif("The four desktops") + "). " + c("TERMINA_SESSIONE") + " (end the session) remains in the protocol and the "
      "confirmation dialog remains in the page, but no gesture opens it today.")

# ── 14. Optional paths ────────────────────────────────────────────────────
S14 = p("Two other ways of drawing exist in the file and are off: they are kept because they are measurable, "
        "and because each documents a decision.", lead=True) + \
    table(["", "Video worker (" + c("?video=worker") + ")", "MSE (" + c("?disegno=mse") + ")"], [
        ["What", "Video streams are transferred to a dedicated worker, which reads them, applies the RCP rules, "
         "decodes and draws on an " + c("OffscreenCanvas") + "; WebTransport and the control channel stay on the main thread",
         "Frames are packed into fragmented MP4 by the page (" + c("MuxMP4") + ") and played by a " + c("<video>")
         + " behind a transparent canvas that keeps receiving input"],
        ["Why off", "Measured 13 Aug 2026 (bench 03-b17): no latency gained", "Hundreds of ms of extra latency "
         "(+225 ms Firefox, +415 ms Chrome median, bench 07-b57) against a 50 ms cap; the user judged the result on "
         "Firefox for Android irregular and declared that browser unsupported (21 Aug 2026, §7.18)"],
        ["How it is built", "The worker's source is composed at runtime from " + c("Schermo.toString()") + " and "
         + c("leggi_uno_stream.toString()") + " plus a shell supplying " + c("document") + ", " + c("devicePixelRatio")
         + " and the view: one definition, two contexts", "Its own codec probe on the " + c("<video>") + " (H.264 only), "
         "playback speed 1.25× when the buffer is more than 250 ms behind, never seeking"],
        ["Pitfall", "Any new global used by " + c("Schermo") + " must cross into the worker or it breaks silently "
         "(it stayed that way for eight days, until 21 Aug 2026: zero frames, and " + c("GIRO is not defined") + " on every frame). After 60 streams with nothing drawn, the page says so",
         "Combined with the worker it cannot work; MSE wins and the worker stays off"],
    ], "«TAB» — The two optional drawing paths") + \
    p("Whether to delete them is a cleanup decision for the end of the project (" + c("DECISIONI.md") + " §7.16).")

# ── 15. Browsers ──────────────────────────────────────────────────────────
S15 = p("The technical minimum is WebTransport <b>and</b> WebCodecs. The list below is the user's declaration "
        "of 22 August 2026 (" + c("DECISIONI.md") + " §7.20), on the live product, plus what has never been "
        "tried.", lead=True) + \
    table(["Where", "Browser", "Status", "Notes"], [
        ["Linux", "Chrome", "supported", "HEVC where the GPU decodes it, else H.264"],
        ["Linux", "Firefox", "supported", "H.264 only (no HEVC on Linux); the WebGL2 drawing path exists because of its read-back cost; pasting with the mouse costs one extra click"],
        ["Windows", "Chrome", "supported", ""],
        ["Android", "Chrome", "supported", "Samsung DeX with mouse and keyboard is the primary use; touch is the fallback. Judged “a complete experience” on 21 Aug 2026"],
        ["Android", "Firefox", "<b>out of the project</b>", "No WebCodecs; the page explains it and points to Chrome"],
        ["Windows", "Firefox", "never tried", "neither supported nor excluded"],
        ["macOS, iOS", "Safari", "never tried", "WebTransport and WebCodecs exist from Safari 26 on paper; nothing has been verified"],
    ], "«TAB» — Browsers") + \
    p("The rule behind the list: a page runs on three engines written by three teams who do not know REMOTIX "
      "— Blink, Gecko, WebKit — and testing on at least two of them gives back part of the external referee lost "
      "with native clients. Where two agree and the third does not, the defect names itself.") + \
    warn("on Samsung DeX, Chrome delivers mouse moves with no button pressed only around a click — the known "
         "noVNC issue #1727, also seen in KasmVNC #222 and in the native moonlight-android #573; it is not a REMOTIX "
         "defect. The page copes in two ways: since the canvas equals the window every event carries its own "
         "position, so pointing and clicking hit correctly even without hover; and since 3 October 2026 the first "
         "click on the canvas captures the pointer where hover does not arrive (" + c("DECISIONI.md")
         + " §10.29). Details are in " + rif("Mouse and pointer in the classic layout") + ".", "DeX and the pointer.") + \
    ul([
        "Not settled yet: Safari on macOS and iOS has never been opened against REMOTIX.",
        "Not settled yet: Firefox on Windows has never been opened against REMOTIX.",
        "Not settled yet: Android's coming desktop mode, which may change the pointer behaviour; the capture rule "
        "looks at behaviour, not at the system, so it should adapt by itself.",
    ])

CHAPTER = ("The browser page", [
    ("How the page is served", S1),
    ("Structure of pagina.html", S2),
    ("The connection sequence", S3),
    ("Capabilities declared by the page", S4),
    ("Choosing the codec on the pixel", S5),
    ("Measuring the decoder ceiling", S6),
    ("Canvas and view", S7),
    ("Asking for the canvas with ADATTA_TELA", S8),
    ("Receiving video frames", S9),
    ("Decoding with WebCodecs", S10),
    ("Drawing paths: WebGL2, bitmaprenderer, 2D canvas", S11),
    ("Measurements made by the page", S12),
    ("End of session in the page", S13),
    ("The optional paths: video worker and MSE", S14),
    ("Browsers supported and untested", S15),
])
