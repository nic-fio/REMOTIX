from build import (arrow, box, c, fig, flow, key, note, p, rif, seq, steps, table, text, ul, warn, zone)


A1 = p("The session's sound is the mix of every application in it: REMOTIX creates a virtual sink in the "
       "session's PipeWire, captures its monitor, encodes 48 kHz stereo blocks and sends one per QUIC "
       "datagram. The page decodes Opus with its own WebAssembly decoder and schedules each block at the "
       "time the server stamped on it.", lead=True) + \
    flow([("Applications", "play on the default sink", "navy"),
          ("Sink “remotix”", "null-audio-sink", "blue"),
          ("Monitor capture", "PipeWire RT thread", "blue"),
          ("Ring + encoder", "child loop, Opus or PCM", "blue"),
          ("Datagram 0x0401", "via the parent", "dark"),
          ("Page", "wasm Opus, AudioContext", "light")],
         "«FIG» — The path of a sound, from an application in the session to the speakers of the client") + \
    table(["Piece", "File", "Lives as long as"], [
        ["Virtual sink and monitor capture", c("suono.c"), "Sink: the graphical session. Capture: the "
         "connection (invariant I4: the stage outlives the client)"],
        ["Ring buffer, clock, sending", c("figlio.c") + " (" + c("audio_campioni()") + ", "
         + c("audio_svuota()") + ")", "The connection"],
        ["Opus and PCM encoder", c("audio.c"), "The connection; reopened when the negotiated codec changes"],
        ["Datagram on the wire", c("webtransport.c"), "Each block"],
        ["Decoder and scheduler", c("pagina.html") + " (" + c("avvia_audio()") + ") and "
         + c("decodifica.c") + " compiled to " + c("opus.wasm"), "Each " + c("collega()") + " in the page"],
    ], "«TAB» — Who does what in the audio path") + \
    note("the session volume belongs to the session and is set to maximum at every connection (invariant "
         "I5); RCP carries no volume. Microphone input (client to session) is foreseen by SPECIFICHE §10 as "
         "not urgent and RCP/1 defines no format for it. Not settled yet: the microphone.", "Volume and microphone.")

A2 = p("The audio format is fixed, not negotiated (RCP §5.3): two implementations choosing two sample "
       "rates would produce noise that looks like a network fault. Only the codec is negotiated.", lead=True) + \
    table(["", "Opus (codec 1)", "PCM (codec 2)"], [
        ["Sample rate, channels", "48 000 Hz, 2 interleaved", "48 000 Hz, 2 interleaved"],
        ["Block", "20 ms = 960 frames (" + c("AUDIO_BLOCCO_OPUS") + ")", "5 ms = 240 frames (" + c("AUDIO_BLOCCO_PCM") + ")"],
        ["Payload", "One Opus packet", c("s16") + " little-endian, 960 bytes"],
        ["Datagram", "12-byte header + packet", "12 + 960 = 972 bytes"],
    ], "«TAB» — The two audio codecs") + \
    table(["Offset", "Field", "Meaning"], [
        ["0", c("u16 tipo"), c("0x0401") + ", the only type in RCP/1"],
        ["2", c("u16 codec"), "1 = Opus, 2 = PCM"],
        ["4", c("u64 istante"), "Server monotonic microseconds of the <b>first</b> sample of the block"],
        ["12", "samples", "Up to the end of the datagram"],
    ], "«TAB» — The audio datagram (RCP §6.3)") + \
    p("PCM is 5 ms and not 20 ms because a QUIC datagram cannot be fragmented: 20 ms of PCM would be 3852 "
      "bytes. The largest datagram measured on 17 Aug 2026 (" + c("07-b40") + ", wired LAN) was 1024 bytes "
      "on Chrome 151, and on Firefox 140 1024 bytes at " + c("ready") + " growing to 1214 after 800 ms: PCM "
      "fits by 52 bytes. The little-endian byte order of PCM is the only exception to network order in RCP, "
      "declared because it is payload, not a protocol field. A datagram shorter than 12 bytes or with another "
      "type is discarded and counted, never a reason to close the connection: a datagram is unreliable by "
      "definition.") + \
    p("<b>Negotiation.</b> " + c("audio.codec") + " is a capability that both sides declare in " + c("CIAO")
      + "/" + c("ECCOMI") + "; " + c("pcm") + " is mandatory on both sides as the always-available base and "
      "positive control of Opus. The page declares " + c("opus,pcm") + " only if its WebAssembly decoder "
      "loads, or, failing that, if " + c("AudioDecoder") + " supports Opus; otherwise only " + c("pcm")
      + ": declaring " + c("opus") + " would oblige the server to choose it and nothing would be heard. The "
      "server picks inside the intersection following the client's order and logs the choice; the child "
      "then opens the encoder for that codec (" + c("audio_regola_figlio()") + ") and never falls back to PCM "
      "by itself, which would produce noise instead of an error.") + \
    p("<b>Audio goes before video.</b> In every write pass of the transport the pending datagrams enter the "
      "packet before stream bytes, so on a congestion window of two or three packets audio takes the place "
      "of video (SPECIFICHE §10.1). A late audio block is useless, a late frame is still a frame. The price "
      "is bounded by construction: the datagram queue holds " + c("WT_DGRAM_MAX") + " = 8.")

A3 = p("A server has no sound card, and a headless session has no sink at all: measured in v1 on 5 Aug "
       "2026, " + c("wpctl status") + " showed zero devices, zero sinks, zero sources with PipeWire, "
       "pipewire-pulse and WirePlumber all running. " + c("suono_apri()") + " therefore creates one.",
       lead=True) + \
    table(["Property", "Value", "Why"], [
        [c("factory.name"), c("support.null-audio-sink"), "A sink that plays nowhere; being the only one, it "
         "becomes the default"],
        [c("node.name") + " / description", c("remotix") + " / " + c("REMOTIX"), "The capture finds it by name "
         "(" + c("target.object") + "), never by numeric id, so it cannot catch a second sink"],
        [c("media.class"), c("Audio/Sink"), ""],
        [c("audio.position"), c("[FL,FR]"), ""],
        [c("monitor.channel-volumes"), c("true"), "Without it the volume is applied after the monitor tap and "
         "the capture is at full scale whatever the slider says, mute included"],
        [c("state.restore-props"), c("false"), "WirePlumber restores volume and mute by node name: a new sink "
         "was born at 0.008 and muted"],
        [c("object.linger"), c("false"), "The node dies with our PipeWire connection: a restarted REMOTIX must "
         "not find two"],
    ], "«TAB» — The session sink") + \
    p("The volume measurement that justified " + c("monitor.channel-volumes") + " (8 Aug 2026, a 440 Hz tone "
      "at 25.9 % of full scale read on the monitor): with the sink at 100 %, 25 % and 0 %, the capture read "
      "25.39 %, 25.39 %, 25.39 % without the property, and 25.39 %, 0.40 %, 0.00 % with it, which is exactly "
      "the cubic volume curve. " + c("suono_volume_massimo()") + " sets channel volumes to 1.0 and mute off at "
      "creation, at every connection and at every start of the capture, because whoever restores saved levels "
      "does so when the node appears and wins the race at creation.") + \
    table(["Aspect", "Behaviour"], [
        ["Format", "Requested fixed: " + c("S16") + ", 48 000 Hz, 2 channels. PipeWire resamples between sink "
         "and capture, so no resampler is needed in REMOTIX (libopus has none). If another format is "
         "negotiated, delivery is switched off and declared: reading " + c("f32") + " as " + c("s16") + " gives "
         "a full-scale square wave that a bench counts as audio"],
        ["Capture stream", c("PW_KEY_STREAM_CAPTURE_SINK") + " = true on " + c("remotix") + ", flags "
         + c("AUTOCONNECT | MAP_BUFFERS | RT_PROCESS")],
        ["Quantum", c("node.force-quantum") + " = 256 frames (5.33 ms): the value of v1 and of "
         "gnome-remote-desktop. 240 would be rounder, but changing a field-measured value for an unmeasured "
         "convenience is a debt"],
        ["Real-time callback", "Runs on PipeWire's real-time thread: it copies and returns. No lock, no socket, "
         "no allocation, not even a log line; a wait there would make the whole graph skip a quantum, "
         "desktop capture included, and the symptom would be “video stutters”"],
        ["Block size", "The callback delivers however many frames PipeWire gives; it does not accumulate. The "
         "block size lives in one place, " + c("audio_cod_blocco()")],
        ["Stopping", c("suono_ascolto_ferma()") + " waits on an atomic barrier until no callback is running, "
         "because the caller is then allowed to free what the callback used"],
        ["Diagnosis", c("suono_ascolto_vivo()") + " and " + c("suono_conti()") + " (blocks, frames, discarded) "
         "tell apart “nobody plays”, “the stream is dead” and “format refused”"],
    ], "«TAB» — The monitor capture")

A4 = p("Between PipeWire's real-time thread and the child's loop sits a lock-free single-producer, "
       "single-consumer ring of one second (" + c("AUDIO_ANELLO_FOTOGRAMMI") + " = 48 000 frames, 192 KiB): "
       "the producer moves only the head, the consumer only the tail.", lead=True) + \
    table(["Rule", "Why"], [
        ["When the ring is full, the oldest samples are dropped and <b>counted</b>; the count is logged by the "
         "loop, not by the callback", "Late sound is useless; an overflow that is not counted is a rhythm "
         "fault nobody will see"],
        ["The clock is the sample count: " + c("istante") + " = time of the first captured sample + consumed "
         "frames / 48 000, and on overflow the base moves forward by the lost frames", "RCP wants the time of "
         "the first sample of the block; the wall-clock time of sending would carry our jitter into the "
         "client's reordering"],
        [c("audio_svuota()") + " runs at every loop iteration, before the video part, and also in the loop "
         "branch that waits for the stage", "Video exits early when nobody watches; on 27 Aug 2026 the second "
         "call site was missing and 96 s of audio overflowed while a session was being born"],
        ["A block that cannot be sent to the parent is dropped and counted", "RCP forbids retransmission, and "
         "waiting would stop the desktop capture"],
        ["One detail line per second with blocks sent, lost and waiting", "“The loop does not run”, "
         "“the session is silent” and “blocks do not leave” must look different"],
    ], "«TAB» — From the ring to the parent") + \
    warn("PipeWire collects samples on its real-time thread only if it gets " + c("SCHED_FIFO") + ". "
         + c("dichiara_priorita_audio()") + " checks the threads of the audio path and logs whether they are "
         "FIFO/RR. Measured on 21 Aug 2026: on a kernel with " + c("CONFIG_RT_GROUP_SCHED") + " and cgroup v2, "
         + c("SCHED_FIFO") + " is refused to any process outside the root cgroup, so the "
         + c("LimitRTPRIO") + " of the service is inert, and audio crackles when the desktop works. An "
         "independent " + c("pw-record") + " on the same monitor hears the same crackles: the fault is born "
         "in the session's audio graph, not in the transport.", "Real-time priority is declared, not assumed.")

A5 = p(c("audio.c") + " encodes with libopus directly since 30 Sep 2026: ffmpeg left the product for "
       "licence reasons (DECISIONI §10.22, §10.25), and libavcodec was only a wrapper around the same "
       + c("libopus.so.0") + ". The parameters are the ones that wrapper used, and the packets were verified "
       "identical byte for byte (" + c("18-a1-opus-senza-ffmpeg.c") + ", libopus 1.5.2).", lead=True) + \
    table(["Parameter", "Value", "Note"], [
        ["Application", c("OPUS_APPLICATION_AUDIO"), ""],
        ["Bit rate", c("AUDIO_OPUS_BITRATE") + " = 96 000 bit/s", "Read back after setting; a mismatch is logged"],
        ["Complexity", "10", "Differs from the libopus default"],
        ["VBR", "on, unconstrained", "Differs from the libopus default"],
        ["Expected loss, in-band FEC", "0, off", ""],
        ["Phase inversion", "allowed", ""],
        ["Output buffer", c("AUDIO_OPUS_SPAZIO") + " = 7 657 bytes", "What libavcodec offered; the datagram limit "
         "is " + c("AUDIO_FUORI_MAX") + " = 1200"],
    ], "«TAB» — The Opus encoder") + \
    p("<b>One block in, one packet out.</b> Measured on 17 Aug 2026 (" + c("07-b44") + "): 1000 blocks in, "
      "1000 packets out, no delay. " + c("opus_encode()") + " is synchronous, so " + c("istante") + " always "
      "belongs to the block that leaves. The encoder has a look-ahead of 312 samples (6.5 ms), read with "
      + c("OPUS_GET_LOOKAHEAD") + " and written in the log at open; the decoder removes it, so it cancels end to "
      "end, but anyone using these timestamps for audio/video sync must know about it.") + \
    p("<b>Digital silence is not sent.</b> A block whose samples are all exactly zero produces no datagram: "
      "the receiver places blocks at their absolute " + c("istante") + ", so a gap is silence, which is what "
      "the block contained. Measured on 24 Aug 2026 (" + c("09-b84") + "): on a still desktop with Opus, 50 "
      "datagrams per second of 3 bytes cost 589 kbit/s of padded packets and shared the congestion window "
      "with video. On by default since 24 Aug 2026 (user decision); the only switch is the server option "
      + c("--niente-audio-silenzio") + ", which the parent copies into the child's command line, and which "
      "also applies to the test tone of " + c("--audio-prova") + " opened in the parent.")

A6 = p("The page has its own Opus decoder: libopus 1.5.2 compiled to WebAssembly, decode only, embedded in "
       + c("pagina.html") + " as base64 (D-006, decided 25 Sep 2026). " + c("AudioDecoder") + " remains only "
       "as a declared fallback where WebAssembly is missing; PCM needs no decoder.", lead=True) + \
    p("<b>Why.</b> Firefox with a video playing in the session had short repeated sound gaps (0.1–0.4 s) and "
      "Chrome did not. Measured on 25 Sep 2026, 60 s on LXQt and KDE: Firefox with video 3–5 re-anchors, "
      "Firefox without video 0, Chrome 0, Firefox with video in PCM 0. The only difference was Firefox's "
      + c("AudioDecoder") + ", which under video load returns blocks late and in bunches. A decoder that "
      "answers in the same call has no queue. The user rejected a Firefox-only branch: the same path runs on "
      "every browser. It runs on the main thread, because a block costs about 0.1 ms and the "
      + c("AudioContext") + " lives there anyway.") + \
    table(["File", "Role"], [
        [c("src/opus-wasm/decodifica.c"), "Exports " + c("rx_apri") + ", " + c("rx_pacchetto") + ", "
         + c("rx_pacchetto_max") + ", " + c("rx_uscita") + " and the decode call; static state and buffers, no "
         "malloc, no imports, so the module is instantiated with an empty object. Output buffer for 120 ms, "
         "the Opus maximum"],
        [c("src/opus-wasm/costruisci.sh"), "Downloads the pinned libopus tarball, checks its SHA-256, builds in "
         "a podman container with the emscripten image pinned by digest (4.0.15), with no network, -O3, no "
         "SIMD and no extensions beyond the MVP (old phone browsers), then embeds the result between the "
         "markers " + c("OPUS_WASM_INIZIO") + " and " + c("OPUS_WASM_FINE") + ". " + c("--verifica") + " checks "
         "that the page carries exactly " + c("opus.wasm")],
        [c("src/opus-wasm/opus.wasm.sha256"), "The digest of the module in the repository"],
        [c("src/opus-wasm/prova/prova.sh"), "Decodes the same packets with the embedded module (" + c("node")
         + ", " + c("confronta.mjs") + ") and with native libopus (" + c("riferimento.c") + ") and compares"],
    ], "«TAB» — The WebAssembly decoder") + \
    p("<b>Scheduling.</b> The page never waits for audio: a block that arrives late is dropped. Each block is "
      "an " + c("AudioBufferSourceNode") + " started at " + c("base + istante") + ", where the anchor "
      + c("base") + " maps the server clock onto the " + c("AudioContext") + " clock and is set at the first "
      "block to give a cushion of " + c("AUDIO_CUSCINO_MS") + " = 250 ms. Because playback time depends on "
      "the block's own timestamp and not on how many blocks arrived, a lost datagram no longer shortens the "
      "cushion for ever: before this cure (measured 21 Aug 2026 on a real Windows session) 61 lost blocks in "
      "3½ minutes walked the queue from 419 down to 79 ms and produced three audible gaps.") + \
    table(["Case", "What " + c("suona()") + " does", "Counter"], [
        ["Context suspended (no user gesture yet)", "Drops the block, detaches the anchor, retries "
         + c("resume()") + " every 250 dropped blocks; a passive capture-phase listener on "
         + c("pointerdown") + ", " + c("mousedown") + ", " + c("keydown") + ", " + c("touchstart") + " also "
         "retries and removes itself", c("sospesi") + ", " + c("risvegli")],
        ["Slot already passed on the wire", "Dropped (RCP §6.3)", c("scartati_vecchi")],
        ["Overtaken: its slot passed while decoding, a newer block is scheduled", "Dropped, anchor untouched",
         c("scartati_tardivi")],
        ["The newest block and its slot passed", "The anchor moves forward by a whole cushion: an audible gap",
         "re-anchors"],
        ["Arrived behind a newer one but in time", "Played", c("fuori_ordine")],
        ["Queue beyond " + c("AUDIO_CUSCINO_MAX_MS") + " = 600 ms", "Dropped instead of accumulated",
         c("scartati_pieno")],
        ["Same " + c("istante") + " twice", "Dropped", c("doppioni")],
    ], "«TAB» — The audio scheduler in the page") + \
    p("A new " + c("AudioContext") + " and a fresh decoder are created at each " + c("collega()") + ", and "
      "the old ones are closed first: Chrome refuses a seventh context per document, and the exception used to "
      "stop datagram reading for the rest of the session. " + c("aoff_ms()") + " (playback time of a sample "
      "minus its server timestamp, plus " + c("outputLatency") + ") is the audio half of the audio/video "
      "distance metric; it is updated only by blocks that actually played and expires after 600 ms without "
      "sound.")

C1 = p("The clipboard carries <b>plain text only</b>, in both directions (DECISIONI §5-ter.1, decided by "
       "the user on 9 Aug 2026 and confirmed on the 17th). Text covers almost every use, costs a few bytes and "
       "has no format negotiation; images would open the question of formats and of who pays the bandwidth "
       "when an 8 MB screenshot is copied on a link that is struggling.", lead=True) + \
    seq([("Remote application", "in the session", "dark"), ("Child", "clipboard module", "blue"),
         ("Parent", "rcp.c", "blue"), ("Page", "browser", "navy")],
        [
            ("sep", "copy in the remote desktop, paste on the device"),
            (0, 1, "selection changed (text read at once)"),
            (1, 2, "text kept, limit and UTF-8 checked"),
            (2, 3, "APPUNTI_ANNUNCIO (id, length)"),
            (3, 2, "APPUNTI_CHIEDI (id)", True),
            (2, 3, "APPUNTI_TESTO (id, text)"),
            ("nota", 3, "writeText() into the device clipboard"),
            ("sep", "copy on the device, paste in the remote desktop"),
            (3, 2, "APPUNTI_ANNUNCIO (id, length)", True),
            (0, 1, "paste request (serial)"),
            (1, 2, "ask the client"),
            (2, 3, "APPUNTI_CHIEDI (id)"),
            (3, 2, "APPUNTI_TESTO (id, text)", True),
            (1, 0, "answer the paste request"),
        ],
        "«FIG» — The two directions of the clipboard: announce, then pull") + \
    p("The protocol announces and pulls instead of pushing: whoever copies a whole document sends it to "
      "nobody until somebody pastes. The direction used most is device to session, and it is the harder one, "
      "because on the device side the clipboard belongs to the browser.")

C2 = p("Three messages on the clipboard channel (RCP §7.4), each transfer on its own unidirectional "
       "stream (high byte " + c("0x02") + "), so several transfers can be alive together.", lead=True) + \
    table(["Type", "Name", "Body"], [
        [c("0x0201"), c("APPUNTI_ANNUNCIO"), c("u32 trasferimento · u32 lunghezza")],
        [c("0x0202"), c("APPUNTI_CHIEDI"), c("u32 trasferimento") + " of the announcement being answered"],
        [c("0x0203"), c("APPUNTI_TESTO"), c("u32 trasferimento") + " · UTF-8 text up to the end of the message"],
    ], "«TAB» — The clipboard messages") + \
    table(["Rule", "Detail"], [
        ["Transfer ids", "Each side numbers <b>its own</b> transfers from 1. Without ids, two announcements "
         "open in opposite directions were paired in different orders by the two sides and the texts swapped"],
        ["Limit", c("RCP_APPUNTI_TETTO") + " = " + c("APPUNTI_TETTO") + " = 1 000 000 bytes, not 1 MiB: the "
         "message has 6 framing bytes and 4 of id, and a limit equal to the message limit would make a text "
         "of exactly that size illegal"],
        ["Over the limit", "Not announced at all, and logged. Never truncated: a truncated text pasted in a "
         "terminal is worse than a missing one"],
        ["Content", "Always " + c("text/plain;charset=utf-8") + ", valid UTF-8; there is no type field"],
        ["Stale request", "A " + c("APPUNTI_CHIEDI") + " for an announcement already superseded is served with "
         "the <b>current</b> text and logged: it is the normal race between two people copying"],
        ["Unsolicited text", "An " + c("APPUNTI_TESTO") + " nobody asked for is " + c("ERRORE_PROTOCOLLO")
         + ": the clipboard is pulled, never pushed"],
        ["Capability", c("appunti.testo") + " = " + c("si") + " on both sides; without it the page does not "
         "start the clipboard"],
    ], "«TAB» — Clipboard rules") + \
    p("<b>The Ctrl+V race.</b> When the user pastes in the remote desktop with " + key("Ctrl", "V") + ", the "
      "keys and the announcement of the freshly copied local text travel on different streams, and the remote "
      "application may ask before the announcement arrives. Xpra delays every keystroke by 100 ms; for "
      "REMOTIX that is twice the latency budget, paid on every key. Two cheaper cures instead: the server "
      "<b>queues</b> a paste request while the client has announced nothing yet (" + c("rcp_appunti_chiedi()")
      + ", up to " + c("A_STREAM_MAX") + " = 8 requests, one " + c("APPUNTI_CHIEDI") + " for the whole batch), "
      "and the page holds back the V of " + key("Ctrl", "V") + " until its own announcement has left "
      "(" + rif("Clipboard in the browser") + ").") + \
    p("<b>Always answer the compositor.</b> A paste request from the session that is left unanswered leaves "
      "the pasting application waiting for ever, and the user sees a frozen desktop. The child, which owns the "
      "session, keeps up to " + c("APPUNTI_IN_VOLO") + " = 8 requests in flight and answers “nothing” "
      "after " + c("APPUNTI_ATTESA_MS") + " = 4000 ms, or at once when no client can serve it. The parent may "
      "have no client attached, the client may vanish mid-transfer, and the parent itself may die: the debt "
      "towards the compositor stays where the session is.")

C3 = p("On GNOME the clipboard belongs to Mutter (" + c("MetaSelection") + "); the " + c("RemoteDesktop")
       + " session only owns the door to it (" + c("EnableClipboard") + "). " + c("appunti.c") + " uses that "
       "door on the session that " + c("mutter.c") + " already opened.", lead=True) + \
    table(["Trap of Mutter", "Effect", "What " + c("appunti.c") + " does"], [
        [c("DisableClipboard") + " is one-way (Mutter 48.7)", "It does not reset " + c("is_clipboard_enabled")
         + "; afterwards " + c("EnableClipboard") + " answers “Already enabled” and no announcement "
         "ever comes back", "Never calls it; to let go of the selection it calls " + c("SetSelection")
         + " without " + c("mime-types") + ". The clipboard is enabled once per graphical session"],
        ["Asymmetric signature", c("mime-types") + " is " + c("as") + " in method arguments and " + c("(as)")
         + " in the signal; reading with the wrong type gives NULL without error", "Reads each with its own type"],
        ["One MIME type kept", "When the copying application dies only one type survives", "Tries the whole list "
         "of text types, not only the first"],
        ["Echo", c("SelectionOwnerChanged") + " also follows our own " + c("SetSelection") + ", with "
         + c("session-is-owner") + " true", "Ignores it, or the two sides would chase each other"],
    ], "«TAB» — The clipboard on Mutter") + \
    ul([
        "The text types, in this order and nowhere else: " + c("text/plain;charset=utf-8") + ", "
        + c("UTF8_STRING") + ", " + c("text/plain") + " (" + c("TIPI_TESTO") + ").",
        "The text is read in the module, on the clipboard thread, because the announcement needs its length; "
        "the limit and UTF-8 validity are checked there, where the text is still whole; the last text copied "
        "in the session is remembered (" + c("appunti_ultimo_testo()") + "), so that a client that reconnects "
        "finds it (invariant I4).",
        "The clipboard is enabled with empty options, so Mutter immediately reports who owns the selection; and "
        "at every attach the child reads the current selection with " + c("appunti_leggi_adesso()") + " before "
        "offering anything, because Mutter does not tell a new session who owns it and the clipboard would be "
        "lost.",
        "GDBus delivers signals to the context of the subscribing thread, and no REMOTIX thread runs a GLib "
        "loop: the module runs a private context on its own thread. Its callbacks may write to the socket "
        "towards the parent (a " + c("SOCK_SEQPACKET") + " send is atomic) but must never touch " + c("libei") + ".",
        "Mutter's X11 bridge is unconditional in both directions, so " + c("xclip") + " works without a REMOTIX "
        "session: the clipboard benches have an external referee.",
    ])

C4 = p("On KDE Plasma and on labwc (XFCE and LXQt) the same module, " + c("appunti_kde.c") + ", speaks the "
       "wlroots data-control protocol on the user's Wayland socket: " + c("appunti_apri_kde()") + " and "
       + c("appunti_apri_wlroots()") + " differ only in the compositor name used in log lines. The child "
       "chooses with " + c("sessione_su_wlroots()") + " first, then KDE, then GNOME.", lead=True) + \
    table(["Rule", "Why"], [
        ["Bind " + c("zwlr_data_control_manager_v1") + "; if absent, bind " + c("ext_data_control_manager_v1")
         + " under its own name and drive it with the same functions", "KWin 6.6.6 (Ubuntu 26.04) exposes only "
         "the standard one (measured 6 Oct 2026); the two are identical on the wire (ext v1 = zwlr v2), "
         "children are created by " + c("new_id") + " where the interface name does not travel. The older one is "
         "preferred when both exist"],
        ["At least " + c("PASSO_MINIMO_US") + " = 100 ms between two " + c("set_selection"), "Klipper considers "
         "more than ten changes per second a runaway clipboard and stops following it, without error"],
        ["Offer exactly " + c("TIPI_TESTO") + ", never " + c("application/x-kde-onlyReplaceEmpty"), "KWin would "
         "cancel the selection silently; labwc does not know that type at all"],
        ["An offer is ours if it has the three types and only them", "Echo detection; wlroots drops only "
         "byte-identical duplicates, and our three types differ"],
        ["Transfers wait at most " + c("ATTESA_TRASFERIMENTO_MS") + " = 5000 ms", "The other end of the pipe is "
         "an arbitrary application that may be frozen"],
        [c("POLLHUP") + " counts as readable", "A writer that writes and closes may wake " + c("poll()")
         + " with HUP only, and the data is in the pipe"],
    ], "«TAB» — The data-control clipboard (KWin and labwc)") + \
    note("the LXQt test box excludes " + c("qlipper") + ", which dirties the clipboard; on the user's machine "
         "a clipboard manager can still interfere.", "Clipboard managers.")

C5 = p("In the browser the clipboard is not REMOTIX's: the page gets it only under conditions that differ on "
       "every engine. The rule of SPECIFICHE §9 applies to the letter: what cannot be done is declared, never "
       "faked.", lead=True) + \
    table(["Direction", "Mechanism", "Limits"], [
        ["Session → device", "On " + c("APPUNTI_ANNUNCIO") + " the page asks at once (the user will paste "
         "outside the page, where it cannot be seen) and writes with " + c("navigator.clipboard.writeText()"),
         c("writeText") + " needs focus and, on Firefox, a recent user gesture. If refused, the text waits for "
         "the next click or key on the page, except " + key("Ctrl", "C") + ", " + key("Ctrl", "X") + " and "
         + key("Ctrl", "V") + "; if the user copies something meanwhile, the waiting text is discarded"],
        ["Device → session, Chrome", c("clipboardchange") + " (Chrome 144, 13 Jan 2026; the proposal names remote "
         "desktop clients as its motivation), listened on " + c("navigator.clipboard") + " and on "
         + c("document") + ", then " + c("readText()"), "Needs focus; carries only MIME types"],
        ["Device → session, all engines", "The " + c("paste") + " event of " + key("Ctrl", "V") + ": the page "
         "does not cancel it, and focuses the hidden " + c("TEXTAREA") + " " + c("#incolla-nascosto") + " for "
         + c("INCOLLA_FUOCO_MS") + " = 400 ms so that the event is born", "The event exists only with an "
         "editable target; the canvas is not editable"],
        ["Device → session, fallback", c("readText()") + " if no " + c("paste") + " arrived within "
         + c("APPUNTI_ATTESA_PASTE") + " = 1800 ms", "On Firefox it shows the “Paste” button and waits "
         "for a click: the declared price. On Firefox under Wayland the promise may never settle, and the user "
         "is told"],
        ["Remote paste from a menu", "When the session asks (" + c("APPUNTI_CHIEDI") + ") the page re-reads the "
         "local clipboard with " + c("readText()") + " (skipped if a " + c("paste") + " event delivered in the "
         "last 4 s), waiting at most " + c("APPUNTI_RILETTURA_MS") + " = 3000 ms, then serves what it has",
         "The click on the remote \u201cPaste\u201d entry is a click on the page, so permission is fresh. A "
         "late read still announces, so the next paste is ready. If reading is refused and there is nothing "
         "to serve, the page suggests " + key("Ctrl", "V") + " only if the user made a gesture in the last "
         + c("APPUNTI_GESTO_MS") + " = 2000 ms"],
    ], "«TAB» — The clipboard in the page") + \
    steps([
        "<b>The hidden V.</b> On every " + key("Ctrl", "V") + " with the clipboard on, the V is held ("
        + c("incolla_trattieni()") + ") until the page has read the local clipboard and, if it changed, its "
        "announcement has left; at most " + c("INCOLLA_TRATTIENI_MS") + " = 400 ms. Any key typed meanwhile, "
        "Ctrl's release included, queues behind it, or the desktop would receive a plain v. Only this key "
        "waits.",
        "<b>Why the server queue is not enough.</b> After a copy made <b>in</b> the remote desktop the "
        "clipboard belongs to the remote application, the remote paste does not ask the server, and the first "
        "paste gave the remote text (user test, 2 Oct 2026). And when the client had already announced A, a new "
        "copy of B was served as A because B's announcement was still on its way (measured, F-014D 7 of 8).",
        "<b>Echoes.</b> The page remembers the last text read or written (" + c("ultimo_letto") + ") and does "
        "not announce it again, unless the remote desktop was the last owner: then identical text is announced "
        "anyway, or the next paste would give the remote text.",
        "<b>Size.</b> Over 1 000 000 bytes the page does not announce and says so; an incoming announcement "
        "over the limit is a protocol error.",
    ]) + \
    p("Every step of the clipboard in the page also goes to the server's diary (" + c("/diario") + "), "
      "because with the desktop full screen the page log cannot be read, and the silence of “no "
      "announcement arrived” had six possible causes in the page (measured on Firefox, 17 Aug 2026: the "
      "cause was the page's own " + c("preventDefault()") + " on " + key("Ctrl", "V") + "). With the phone in "
      "hand the paste field must not open the system keyboard (" + rif("The on-screen keyboard on a phone")
      + "). Safari is not tested.")

D1 = p("The decisions of audio and clipboard, with the reason that made each one.", lead=True) + \
    table(["Decision", "Rejected alternative", "Reason"], [
        ["Fixed format, only the codec negotiated", "Negotiate rate and channels", "Two choices make noise that "
         "looks like a network fault"],
        ["PCM in 5 ms blocks", "20 ms like Opus", "3852 bytes do not fit a datagram"],
        ["Create a null sink and capture its monitor", "Capture existing sinks like gnome-remote-desktop",
         "A headless session has none: nothing would arrive, silently"],
        ["Sink per session, capture per connection", "Recreate the sink at each connection", "Applications stay "
         "attached to the node they chose"],
        ["Volume at maximum at every connection", "Leave the session's level", "A low slider is invisible to "
         "the client"],
        ["Clock from the sample count", "Wall clock at sending", "Reordering on our jitter"],
        ["Silence not sent", "Send zero blocks", "589 kbit/s on a still desktop"],
        ["libopus directly", "libavcodec", "ffmpeg left the product; same encoder, same bytes"],
        ["Own WebAssembly Opus decoder for all browsers", "Firefox-only branch, or " + c("AudioDecoder"),
         "Firefox's decoder returns blocks late under video load; no per-browser branches"],
        ["Schedule by timestamp with a 250 ms cushion", "Append after the previous block; 300 ms of "
         "gnome-remote-desktop; 50 ms", "A lost datagram must not shorten the cushion; gaps are heard more "
         "than delay"],
        ["Text only", "Images, files, rich formats", "Bandwidth and format negotiation"],
        ["Announce then pull", "Push on copy", "Copying a document sends nothing until someone pastes"],
        ["Queue the paste on the server and hold the V for 400 ms", "Delay every key by 100 ms", "Paid only on "
         + key("Ctrl", "V")],
        ["Never " + c("DisableClipboard"), "Disable on detach", "One-way in Mutter 48.7"],
    ], "«TAB» — Audio and clipboard decisions")

CHAPTER = ("Audio and clipboard", [
    ("Audio at a glance", A1),
    ("The audio format and its datagram", A2),
    ("The session sink and its capture", A3),
    ("From samples to datagrams", A4),
    ("The Opus encoder", A5),
    ("Playing audio in the page", A6),
    ("Clipboard at a glance", C1),
    ("The clipboard messages and their limits", C2),
    ("Clipboard on GNOME", C3),
    ("Clipboard on KDE and labwc", C4),
    ("Clipboard in the browser", C5),
    ("Audio and clipboard decisions", D1),
])
