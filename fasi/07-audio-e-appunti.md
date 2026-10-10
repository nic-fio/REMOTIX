# Phase 7 — Audio and clipboard

*⚠ Historical measurements, on the machine of that time. With phase 18 (without ffmpeg) the ones that the change invalidated were removed — encoding without the card and colour conversion with swscale; the ones for encoding on the card and for audio stay, because the new stream is identical (comparison of 30 Sep 2026). User's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

⭐ **Opened on 17 Aug 2026**, with its document and **before a line of code**
(`PIANO.md` §0.1). The plan is `PIANO.md` §«Fase 7 — Audio e appunti»; the model for this
document is `PIANO.md` §0.2.

> **The scene the user will judge**: *«apre un video nel desktop remoto e lo **sente** dal
> portatile; copia un indirizzo sul telefono e lo **incolla** dentro la sessione, e viceversa.»*

⚠ **And one thing to say right away, so that it is not a discovery**: **phase 6 is not closed** — its
§8 awaits the user's judgement on two scenes (dragging the border and the click held down).
Opening 7 is a user decision of 17 Aug 2026 (*«in questa sessione sviluppiamo la
fase 7»*); ⛔ what remains of 6 **stays open and does not close by itself**.

---

> # 📅 HOW IT WAS ON **17 Aug 2026, evening** — *the resume of that time*
>
> ⚠ **Do not restart from here**: the entry point is the **⏸** box at the head of `README.md`.
>
> *Decided by the user: «per gli appunti apriamo una nuova sessione».*
>
> ## ✅ AUDIO IS DONE, and the judgement is there: **«problema audio risolto»**
>
> | | |
> |---|---|
> | **the measurement** | 49.95 blocks/s received against 50 produced — **zero loss**, **2 gaps** (at start-up) and queue stable at 311-341 ms |
> | **the scene** | a **YouTube** video played in the remote session, judged by ear |
> | ⛔ **and before that there were seven «fa schifo»** | §6.8, and it is the chapter that teaches: six cures out of eight were **real** faults that were not what the user was hearing |
>
> ## ⭐⭐ AND THE CLIPBOARD IS DONE — **«clipboard funziona in entrambi i versi»**, 17 Aug 2026 evening
>
> *User's judgement with the browser, port 7730.* ⇒ 📖 §4.5 (what was written), §6.9
> (⛔ the bench's external arbiter **does not exist**, and why), §9.2-bis (the verdict, and what it does not
> say).
>
> ⛔ **No automatic bench has ever seen a byte of clipboard pass**: that judgement is the only
> proof this half of the phase has.
>
> *What follows was the starting plan, and it stayed true except for §2.4:*
>
> The plan is §0 and §2 of this document; everything needed is already written there:
>
> - ⭐ **the independent side is there and it is free**: on GNOME Mutter's X11 bridge is unconditional,
>   so **`xclip` works without a session of ours** — it is the external arbiter (§2.4);
> - ⛔ **three Mutter traps** the bench does not see and the product does (`PIANO.md` §Fase 7):
>   `DisableClipboard` is **one-way** (it is never called); the signature of `mime-types` is
>   **asymmetric** and whoever reads with the wrong type gets `NULL` **without an error**; the internal
>   manager holds **a single MIME type**;
> - `fondamenta/remotix-c/src/appunti_mutter.c` **is reused** (450 lines, GNOME);
> - ⚠ and the clipboard **is emptied at the start of every round**, or what is left from the previous round gets
>   announced and looks like a result (`LEZIONI.md` §2.3-quinquies).
>
> ## ⚙ The state of the machine, so as not to reconstruct it
>
> | | |
> |---|---|
> | **the audio server** | running on **7710** (`banchi/07-b41-accendi.sh --hz 0`), tree `/media/REMOTIX/src/07-audio-src` |
> | ⛔ **the ports taken** | 7448 · **7700** · 7710 — a new bench takes its own (07-b43 uses 7720) |
> | **the password of `prova`/`prova2`** | `prova2026`, from the `chpasswd` line of `src/provisiona.sh`. ⛔ **Not** the one in `credenziali-banchi`, which belongs to the `prova2` **of the container** |
> | ⛔ **nothing has been put in `git`** | ~2300 lines in 13 modified files and 7 new ones. **The user must decide** |
>
> ## ⏳ And what remains open on audio, declared
>
> - ⚠ **the 250 ms cushion** was never judged on its own: the user said «risolto», not
>   «e il ritardo va bene». If one day it gets annoying, the cure is not tightening it but moving the audio
>   off the main thread (`AudioWorklet`);
> - ⏳ **the Opus bitrate (96 kbit/s)** and the cushion must be recorded in `DECISIONI.md`, which for
>   audio **does not yet have a chapter** (§7);
> - ⛔ **bench `07-b43` must be redone after all these cures**: the last green round is from **before**
>   the eight changes to the transport;
> - ⚠ and the two `[?]` of the review (§6.4) and **phase 6 not closed** remain.

---

## 0 · What this phase must produce

| | |
|---|---|
| **audio** | the session's sound on the user's device: **Opus**, with **PCM** as the always-available base (`SPECIFICHE.md` §10, `RCP.md` §5.3) |
| **clipboard** | plain text, **in both directions** (`DECISIONI.md` §5-ter.1) |

⛔ **Out, and declared**: the **microphone** (client → session). `SPECIFICHE.md` §10 calls it
not urgent and `RCP.md` §12 declares that *«il verso è previsto in §5, il formato non è definito»*.
A format is not invented in this phase.

⛔ **Also out**: images and files in the clipboard (`SPECIFICHE.md` §9, `DECISIONI.md` §5-ter.1).

### 0.1 · The work order, decided by the user

**First audio, then clipboard** (*«cominciamo con l'audio»*, 17 Aug 2026). This document
is written in full all the same, because the bench is written first and the two halves share a
piece — the **control channel** and the **negotiation** — but the work is done in this order.

---

## 1 · What already exists, and is not rewritten

### 1.1 · In the V2 product, today

| | state | where |
|---|---|---|
| ✅ the **negotiation** of `audio.codec` | **done and alive**: `opus,pcm` declared by both sides, intersection, discard written in the log, `pcm` mandatory for both | `src/rcp.c:1513-1816`, `src/pagina.html` · `collega()` |
| ✅ the **negotiation** of `appunti.testo` | declared by both sides (`si`) | `src/rcp.c` · `T_APPUNTI_TESTO`, `src/pagina.html` · `MP4_DURATA_MAX()` |
| ✅ the **rejection** of audio on a stream | channel `0x04` on a stream is `ERRORE_PROTOCOLLO`, and the log line names it | `src/webtransport.c`, `src/rcp.c` |
| ✅ the **declared discard** of datagrams | in phase 1 they were discarded writing it in the log, on purpose because *«la differenza fra "l'audio non arriva" e "l'audio arriva e lo butto" si vede solo se questa riga esiste da prima»* | `src/trasporto.c:333-357` |
| ⛔ the **outgoing direction** of datagrams | **DOES NOT EXIST**: no function sends a datagram. `webtransport.h` does not have one, and `wt_scrivi` does not touch them | — |
| ⛔ the **three clipboard messages** | **DO NOT EXIST**: `0x0201/0x0202/0x0203` appear in no product file. The page receives a `0x02` stream and writes *«ricevuto e non usato»* | `src/pagina.html` · `ascolta_controllo()` |
| ⛔ the **sound in the session** | **DOES NOT EXIST**: no sink, no audio capture. `libpipewire` is already linked, but for the **frames** | `src/cattura.c` |

### 1.2 · From v1, and they are the most intact things the project has

| file | lines | what it is worth |
|---|---|---|
| `fondamenta/remotix-c/src/suono.c` + `.h` | 582 + 87 | ⭐⭐ **the most reusable piece of the phase**: it creates the virtual sink (`support.null-audio-sink`) and captures its **monitor**. It does not touch RDP in any line |
| `fondamenta/remotix-c/src/altoparlante.c` + `.h` | 892 + 117 | ⛔ **RDP up to the neck** (`WTSVirtualChannelWrite`, `SendSamples2`, the MS-RDPEA formats). ⭐ **But the shape is inherited**: the queue between the PipeWire thread and the connection loop, throwing away **the oldest samples**, the whole block per round |
| `fondamenta/remotix-c/src/appunti.c` + `.h` | 115 + 136 | the dispatching between the two roads |
| `fondamenta/remotix-c/src/appunti_mutter.c` + `.h` | 450 + 28 | **GNOME**, which is this phase's desktop |
| `fondamenta/remotix-c/src/appunti_wlr.c` | 796 | KDE, XFCE and LXQt — **phases 11 and 12**, not this one |

⛔ **And the division v1 had already found, and which holds identically here**: *«il sink è della
SESSIONE, la cattura è della CONNESSIONE»* (`fondamenta/…/suono.h`). It is the same shape as I4: an
audio device that appears and disappears at every reconnection leaves the applications already open
on a dead device.

---

## 2 · The bench — ⛔ written BEFORE the product

`PIANO.md` §0.3.4: *«il banco si certifica prima di essere creduto»*. And `PIANO.md` §«Fase 7» sets
three rules that come from three real faults of v1, not from prudence.

### 2.1 · ⛔ One LISTENS, one does not count blocks

`LEZIONI.md` §2.2, first line: *«il banco contava fotogrammi spediti e blocchi riscontrati; il
difetto cambiava **i campioni** — l'audio era rumore a fondo scala»*. A bench that counts stays
green for the whole time the fault is alive.

⇒ **The judge measures the signal, not the traffic.**

| the scene | a **pure 440 Hz tone**, known amplitude, played **inside the session** on a real application |
|---|---|
| **what is measured** | the **dominant frequency** and the **amplitude** of the samples received on the client side, after decoding |
| **the expected value** | 440 Hz ± tolerance, and the expected amplitude within the encoder's tolerance |

⛔ **And the four positive controls, written beforehand**, that is the four forms in which this bench
**must** give red — they are the same ones `RCP.md` §11 names:

| the grafted fault | what the judge must see |
|---|---|
| the server sends at **44 100 Hz** declaring 48 000 | the dominant frequency shifts |
| the PCM leaves **big-endian** | the tone disappears: wideband noise, no dominant line |
| the channels **not interleaved** | ⚠ to be decided what it looks like: if the judge does not tell it apart, the case does not go in |
| **silence** (no samples) | ⛔ and it must be told apart from *«I received and could not read»*: `CODER.md` §3.10 — a measurement that can say zero must be able to tell zero from failure |

⚠ **The fourth is the most important and the easiest to write badly**: without it *«I did not
hear anything»* and *«I did not look»* look the same.

> ### ⛔⛔ AND THE JUDGE HAD A FAULT THAT WOULD HAVE FAILED RIGHT CODE
>
> *Found on 17 Aug 2026 by the real audio bench (`07-b43`), while it was being written.*
>
> **Purity depends on the window length.** `[M]` same file, same tone:
>
> | window | 0.25 s | 0.5 s | 1 s | 2 s |
> |---|---|---|---|---|
> | purity | **0.2501** | **0.5001** | **1.000** | **1.000** |
>
> ⛔ The judge's threshold is **0.80**. ⇒ Half a second of analysis would have written *«it is not a
> tone, it is noise — v1's fault»* **on a perfect tone**. It is `LEZIONI.md` §2.3: *«una prova
> che boccia il codice giusto costa quanto una che promuove quello sbagliato»*.
>
> ⭐ The cure is not raising the threshold: it is that the judge **rejects** a window that is not a
> whole number of seconds, instead of judging on a window it does not know how to evaluate.
>
> ⚠ And the reason is arithmetic, not a fault of Goertzel: 440 Hz in half a second is not a
> whole number of periods, and the energy spreads over the neighbouring lines. The judge measured
> well a thing that made no sense to measure that way.

> ### ⭐⭐ THE JUDGE IS CERTIFIED — `[M]` 17 Aug 2026, **six cases out of six**, on two engines
>
> `banchi/07-b40-sonda-audio.html`, function `giudica()`: dominant frequency (Goertzel, step
> 1 Hz, 100-2000 Hz), RMS amplitude, and ⭐ **purity** — how much of the energy is in the
> dominant line, which is what tells **a tone from full-scale noise**, that is the v1 fault
> no block-counter saw (`LEZIONI.md` §2.2).
>
> | # | the case | `hz` | `rms` | purity | verdict |
> |---|---|---|---|---|---|
> | **0** | ⭐ healthy, 48 000 Hz | **440** | 0.3536 | **1.000** | ✅ green |
> | **1** | 44 100 Hz passed off as 48 000 | **479** | 0.3536 | 0.975 | ⛔ **seen** |
> | **2** | big-endian PCM read back as little | 1000 | 0.5644 | **0.142** | ⛔ **seen** |
> | **3** | channels **not** interleaved | 880 | 0.3536 | 0.500 | ⛔ **seen** |
> | **4** | silence (zero samples) | 0 | **0** | — | ⛔ **seen** |
> | **5** | I read nothing | — | — | — | ⭐ **`NIENTE DA GIUDICARE`**, an outcome of its own |
>
> ⛔ **And the expected value of case 1 written above was WRONG, in direction.** This document
> predicted *«440 × 44100/48000 ≈ 404 Hz»*; the measurement gives **479**, which is 440 × 48000/44100. ⚠ A
> **slower** sampling passed off as a faster one makes the tone sound **higher**, not
> lower. ⇒ The prediction was written **before** the measurement, and that is why
> the error shows instead of vanishing: `LEZIONI.md` §1.11.
>
> ⭐ **Case 2 is the one that counts**: big-endian is **not** recognised from the frequency — the
> judge reads 1000 Hz, a perfectly respectable number — ⛔ **it is recognised from the
> purity, 0.142 against 1.000**. A judge looking only at the dominant frequency would have
> given **green to full-scale noise**, which is literally v1's fault.

### 2.2 · ⛔ The two sides synchronise with MARKERS, not with `sleep`

`LEZIONI.md` §2.3-quinquies: at the KDE clipboard bench the two sides were out of step by **thirteen
seconds**, and the check gave **red on code that worked**. A file that the first touches and the
second waits for costs three lines.

### 2.3 · ⚠ The clipboard is EMPTIED at the start of every round

Same §2.3-quinquies, the corollary: what is left from the previous round gets announced at
connection **and looks like a result**.

### 2.4 · ⛔ The independent side of the clipboard is NOT there — *corrected on 17 Aug 2026, by measuring*

> ⛔⛔ **THIS PARAGRAPH SAID THE OPPOSITE, AND THE MEASUREMENT REFUTED IT.**
> It said: *«il lato indipendente c'è già, ed è gratis — `STUDI.md` §gnome §10 `[R]`: la sponda X11
> di Mutter è incondizionata nei due versi ⇒ **`xclip` funziona senza una nostra sessione**. È
> l'arbitro esterno che a questa fase serviva e che non credevamo di avere.»*
>
> ⛔ `[M]` 17 Aug 2026: the compositor runs as **`gnome-shell --headless --no-x11`**, that is
> **XWayland does not start at all**. The line of `STUDI.md` is true of Mutter's **code** and false
> of **our sessions** — and it is an `[R]` read in the source, not an `[M]` taken on the
> machine.
>
> ⚠ And the fallback to a real Wayland client (GTK) does not hold either: owning the selection
> needs the *serial* of an input event, and in a headless session none reaches anyone.
>
> ⇒ 📖 **§6.9**, which is the chapter that teaches: the three attempts, the real cause, and why REMOTIX
> manages anyway.

⇒ **What remains.** The `device → session` direction has an arbiter — the **test
client**, which has read only `RCP.md` (`PIANO.md` §1.1). ⛔ The `session → device` direction does not, and
today it is judged by **the user**: it is invariant I8, not a fallback.

### 2.5 · ⛔ And the second reader remains the test client

`PIANO.md` §1.1: the test client (`banchi/01-b3-cliente.py`, in Python, written reading only
`RCP.md`) **grows with the phases**. This phase's new messages — the `0x0401` datagram and the three
clipboard ones — go into it, or this phase's wire would be validated by **a single**
implementation. And the **validator** (`banchi/01-b4-validatore.py`) learns the same framings.

---

## 3 · The questions to close BEFORE writing the audio

⛔ There are four, and **three change what gets written**. `PIANO.md` §1.2 calls this thing «the
probe», and the rule it carries is from `LEZIONI.md` §1.11: *for every indirect test one writes first
what the opposite would look like*.

| # | The question | What it decides | state |
|---|---|---|---|
| **A1** | ⛔ does the browser **decode Opus**? WebCodecs `AudioDecoder` with `codec: "opus"`, on Chrome and on Firefox | whether Opus is a road or only a declaration. ⚠ If **no on one engine**, `RCP.md` §4.3 already has the answer ready: **`pcm`** is negotiated, which is the mandatory base for both — **it is not an improvised fallback, it is the mechanism** | ✅ **CLOSED** `[M]` 17 Aug — §3.2 |
| **A2** | ⛔ **how many bytes a datagram really carries** on each engine | `RCP.md` §5.3 declares it `[?]` **by name**: the PCM is sized at **5 ms = 972 bytes** on an estimated payload `[S]` of ~1200. ⛔ If the real number were lower, **the PCM goes down further** — and the PCM is Opus's positive control | ✅ **CLOSED** `[M]` 17 Aug — §3.3 |
| **A3** | how to **play** in the page without accumulating delay | `AudioContext` + `AudioWorklet` with a ring, or `decodeAudioData`. ⚠ The reference has a **latency regulator at 300 ms** (`STUDI.md` §gnome §11): for us it is **six times the video ceiling** — it is looked at, not copied | ⏳ **to be designed** |
| **A4** | the **sink** and the **monitor**: the volume trap | ⭐ **already closed by v1, and with a measurement**: `monitor.channel-volumes = "true"` among the sink's properties, or the volume **does not arrive, mute included** (`STUDI.md` §kde §10.5, `LEZIONI.md` §5) | ✅ `[M]` 8 Aug 2026 |

### 3.2 · ⭐⭐ A1 is CLOSED — Opus decodes on both engines, **measured, not declared**

`[M]` 17 Aug 2026, `banchi/07-b40-lancia.py chrome|firefox`.

⛔ **`isConfigSupported` says `true` on both, and it is not the answer**: it is a declaration, and
`CODER.md` §3.9 forbids believing it. ⇒ **The real round** was done: a 440 Hz tone is encoded in
Opus, the **bare packets** are given to the decoder — no container, as
`RCP.md` §6.3 imposes (*«un datagram, un blocco di Opus»*) — and **what comes out** is judged.

| | Chrome 151 | Firefox 140esr |
|---|---|---|
| `AudioDecoder` / `AudioEncoder` / `AudioWorklet` | ✅ all | ✅ all |
| encoded packets (50 blocks of 20 ms) | 51 | 51 |
| ⭐ **decoded dominant frequency** | **440 Hz** | **440 Hz** |
| ⭐ **RMS amplitude** (expected **0.3536**) | **0.3504** | **0.3510** |
| bytes per packet, min-max (96 kbit/s, stereo) | **241 - 376** | **309 - 439** |
| encoding or decoding errors | none | none |

⇒ ⭐ **Opus is a real road, not a declaration**, and the decoder accepts the packets
**without a container** — which is the form in which the protocol sends them.

⚠ **And three things must be said instead of kept quiet:**

1. ⛔ **it is a bench browser, not the user's device**: `HeadlessChrome/151` and
   `Firefox/140` on this laptop. It is error form **E10** (`REVIEWER.md`), and the rule
   of `PIANO.md` §1.2 is *«si sviluppa sull'emulatore, si misura sul telefono»*. ⭐ The round on
   **non-headless Chrome 151** (the user's real browser on this machine) was done and
   gives the same numbers; ⛔ **on Samsung DeX and on the phone it stays `[?]`**, and the phone is with
   the user;
2. ⚠ **the round measures the decoder with OUR browser encoder**, not with the server's
   `libopus`: the two can diverge. The test that closes this point is the phase's bench,
   not the probe;
3. ⚠ **`bytes per packet` is at 96 kbit/s chosen by us**: it is not the product's bitrate, which
   is not decided yet.

### 3.3 · ⛔⭐ A2 is CLOSED, and the number is **lower than the estimate** — but the PCM survives

`[M]` 17 Aug 2026, against the **real server** (`https://192.168.0.2:7700/rcp/1`, live product
on the test machine), published fingerprint, no credentials and no session: it opens, reads
`datagrams.maxDatagramSize` and says farewell.

| | Chrome 151 | Firefox 140esr |
|---|---|---|
| right after `ready` | **1024** bytes | **1024** bytes |
| after 800 ms | **1024** bytes | ⭐ **1214** bytes |
| the PCM of §5.3 asks for (12 + 480×2) | 972 | 972 |
| ⭐ **does it fit?** | **yes**, margin **52 bytes** | **yes**, margin **242 bytes** |

⛔ **`RCP.md` §5.3 estimated `[S]` «~1200 bytes» and the estimate was optimistic by a fifth on Chrome.**
The line of §5.3 that opened the `[?]` — *«if the number were lower than 972, the PCM goes down
further»* — **does not trigger**: 1024 > 972. ⭐ But the margin on Chrome is **52 bytes**, that is the PCM of
this protocol fits inside Chrome's datagram **by less than 6 %**.

⚠ **And the two engines do not give the same number, nor the same number over time**: Firefox starts from
1024 and **grows to 1214** once it has measured the path. ⇒ ⛔ **Whoever sized the blocks
reading `maxDatagramSize` only once, right after `ready`, would take the worst number and
not know it.** The PCM block however is **fixed in the specification**, not negotiated: here the number
serves to know that it fits, not to choose.

`[?]` **What remains open, and is not extrapolated**: this measurement is on a **local network, cable**.
On a mobile network — where `SPECIFICHE.md` §3.1 puts the 30 Mbps scenario — the path may
carry less. ⛔ The PCM at 972 bytes is the road that **has no margin**, and it is exactly the one
fallen back on when Opus is not negotiated.

### 3.4 · ⛔ And a fifth question, which is not the browser's but our architecture's

**Where the samples come from.** The sink and the capture live in the **child** (`src/figlio.h`), which is
the only process that has the session bus and `/run/user/<uid>`; the datagrams are written by the **parent**,
which holds the QUIC connection. ⇒ A new message is needed on the socket between the two — the shape is that
of `FiglioDeposito`, which already carries the frames.

⚠ **And v1's rule holds identically here, and it is the reason there is a queue**: the PipeWire thread
runs **in real time**, and whoever writes a waiting call inside it *«non ferma
soltanto l'audio: fa saltare il quanto a tutto il grafo PipeWire, cattura del desktop compresa»*
(`fondamenta/…/suono.h`). One copies and returns.

⛔ **And the priority belongs to the system, not to the process**: `LEZIONI.md` §5 — *«il percorso audio vuole
tempo reale, e va concesso dall'unità di sistema; un processo senza quel permesso non può
chiederlo, e il sintomo è audio che scoppietta quando il desktop lavora»*.

---

## 4 · What was developed

### 4.1 · The bench, before the product — **17 Aug 2026**

| file | what it is |
|---|---|
| `banchi/07-b40-sonda-audio.html` | the **audio probe**: declared capabilities, the **real** Opus round (encoding → bare packets → decoding → judgement), the **datagram** measurement against the real server, and ⭐ **the judge's positive control** — six cases, five grafted faults |
| `banchi/07-b40-lancia.py` | the launcher: it serves the page on `http://localhost` (secure context on both engines), opens **the engine it is told to**, and waits for the **carrier** instead of reading a snapshot. ⛔ It verifies from the `user agent` that the one that answered is the one called (`CODER.md` §3.9) |

⛔ **Not a line of the product had been written**, and that was intended: `PIANO.md` §0.3.4 — the bench is
certified before being believed. The product is §4.2.

### 4.2 · The product — **17 Aug 2026**, the outgoing direction of datagrams

| file | what it does |
|---|---|
| ⭐ `src/audio.c` + `.h` (new, ~250 lines) | the **encoder**: Opus through `libavcodec` (encoder `libopus`, asked for **by name**), s16 PCM **little-endian written by hand** — not with a `memcpy`, which would give the machine's byte order |
| ⭐⭐ `src/webtransport.c` | the **outgoing direction of datagrams**, which did not exist: the queue (8 blocks, and whoever does not fit is **thrown away** — §6.3 forbids retransmission), the **RFC 9297** prefix, the framing of §6.3, `wt_audio_diffondi()` with the **I3** guard, and `audio_regola()` which turns the channel on |
| `src/rcp.c` + `.h` | `rcp_audio_negoziato()`: from `opus`/`pcm` to the numbers `1`/`2` of §6.3, **in one place only** |
| `src/main.c` | `--audio-prova <hz>`: the test source, **off** if nobody turns it on (I6) |
| ⭐ `src/pagina.html` | the **receiver**: reads the datagrams, applies §6.3 (short · type · **instant not more recent**), decodes Opus with `AudioDecoder` or unrolls the PCM, and plays with a **250 ms** cushion ⛔ *(it was 60: raised on 17 Aug to remove the gaps, and it is the cause of the delay of §8)* |
| `banchi/01-b3-cliente.py` | ⭐ the **second reader grows with the phase** (`PIANO.md` §1.1): it receives the datagrams and keeps **six counters**, one for each rule of §6.3 that can be violated |
| `banchi/07-b41-accendi.sh` · `07-b42-giudice.py` | the bench's server (port, ban-file and socket **of its own**) and the judge that *listens* |
| ⭐ `banchi/07-b43-audio-vero.sh` · `07-b43-giudizio.py` | the **real** audio bench: the session plays, the client collects, the judge listens. Port **7720**, own tree and socket |
| ⭐ `banchi/07-b44-ritardo-opus.c` | the minimal program that asks `libopus` **one thing only**: does it accumulate blocks? (`CODER.md` §3.6) |

### 4.3 · The stitching between parent and child — **17 Aug 2026**

⛔ **Audio crosses a process boundary, and it is the third time this happens for the same
reason** — after `MSG_VIDEO` (phase 3) and `MSG_INPUT` (phase 4). By now it is a law
of the architecture, not a choice: **PipeWire talks to the user's session, and that is in the
child**; the datagrams are written by **the parent**, which holds QUIC.

| | |
|---|---|
| `MSG_AUDIO` (parent → child) | *«capture the audio, and encode it like this»* — `0` = switch off |
| `MSG_BLOCCO` (child → parent) | a block **already encoded**, with its `istante` |

⛔ **And the child encodes BEFORE sending**, instead of shipping the raw samples. It is not
just any optimisation: 20 ms of stereo PCM are **3840 bytes**, the same block in Opus
measures `[M]` **241-439**. Shipping raw would cost **ten times** the socket, fifty times per
second.

⛔⭐ **And the thing that governs the whole design is a constraint, not an architecture**: the samples
callback runs on the **PipeWire thread, in real time**. Whoever writes a waiting call inside it
*«non ferma soltanto l'audio: fa saltare il quanto a tutto il grafo PipeWire, cattura del
desktop compresa»*. ⇒ Between the two there is a **single-producer single-consumer ring**, without
locks — the producer moves only `testa`, the consumer only `coda`, and the two indices are
atomic. ⚠ And in the callback **nothing is written to the log**: the overflow is *counted* there and
*written* from the loop.

⭐ **Three decisions the code carries with their reason beside them:**

1. **the sink belongs to the session, the encoder to the connection** — I4. Switching off stops the
   capture, **not** the sink: making it disappear at every detach would cut the sound for whoever listens
   *inside* the session and would leave the applications on a dead device;
2. **the audio clock is the sample count**, not `CLOCK_MONOTONIC`. §6.3 wants *«the instant
   of the first sample»*; the wall-clock time at the moment of sending would put in the field **when I
   sent it**, and the client would reorder on our jitter instead of on the sound. ⛔ And when
   the ring overflows **the base moves by the lost samples**, or the `istante`s would tell of a continuous
   sound where there was a gap;
3. ⛔ **audio is drained BEFORE the video part**, which exits with `continue` when nobody is watching.
   Otherwise *«audio on, video off»* would not play and **no line would say why** — and
   it is the case of whoever listens to music with the tab in the background. ⚠ For the same reason the
   loop, with audio on, can no longer sleep for a second: the ring fills at 48 000
   frames per second **even with the desktop still**.

### 4.4 · `suono.c` — the sink and the capture, ported from v1 · **17 Aug 2026**

**869 lines**, compiles clean. ⛔ **In the session there is nothing to capture and it must be created**: `[M]`
5 Aug 2026, with `pipewire`, `pipewire-pulse` and `wireplumber` all active, `wpctl status` shows
**zero devices, zero sinks, zero sources** — it is the normal case of a server without a sound card.
⚠ The reference (`gnome-remote-desktop`) opens the capture on the sinks it **finds** and never
creates a sink: with its code, here, not one sample would arrive — and without an error anywhere.

> #### ⛔⛔ AND THE PORT FOUND A FAULT IN v1: **the wait that did not wait**
>
> v1's `suono_ascolto_ferma()` declared *«il lucchetto del ciclo **è** l'attesa»*, and on that
> line rested the permission to free the connection's context.
>
> ⛔ **It is false with `PW_STREAM_FLAG_RT_PROCESS`**: the callback comes from the **data thread**, which
> that lock does not stop `[R]` (`pipewire/stream.h:150` and `:466`). ⇒ Whoever returned from there could
> free the memory **while the real-time thread was still writing into it** — a fault
> that shows up once in a while, at close, that is where nobody looks.
>
> ⭐ **Now the wait is in two steps**: an atomic delivery flag is switched off and one waits until the
> callback has really exited; **then** the stream is destroyed. With a ceiling of 2 s, and if it expires it
> exits **declaring «⛔ NON liberare il contesto»** instead of hanging the session.
>
> ⚠ And a second thing v1 did and is not done here: **printing from the real-time thread**. A
> log line is a `vsnprintf` plus a `write`, that is exactly the call that cannot be
> made there. ⇒ The thread counts, and what v1 printed **is asked from outside**.

⚠ **And what `suono.c` does NOT accumulate, declared**: it delivers frames as PipeWire gives them
(~256 per callback, and the number **varies**). The accumulation into blocks of 960 or 240 is done by the ring in the
child — a second intermediate buffer for the same job would have decided *when* the sound
starts, which belongs to whoever sends, and at switch-off it would have silently thrown away up to 959 frames.

⛔ **Nothing was run**: the agent did not have a graphical session. That the sink appears,
that the monitor delivers samples and that `monitor.channel-volumes` works **on this machine**
are `[?]`, and the bench closes them.

---

### 4.5 · ⭐⭐ THE CLIPBOARD — **17 Aug 2026, evening**, and it is the second half of the phase

*The user's work order: «prima l'audio, poi gli appunti» (§0.1). Audio is closed with its
judgement; this section is what was written afterwards.*

> ### ⛔ AND THE USER'S QUESTION WAS «FORMATTED TEXT» — closed before writing a line
>
> The opening of this session asked for *«la copia server↔client di **testo formattato**»*.
> ⛔ `DECISIONI.md` §5-ter.1 says the opposite, **in his own words of 9 Aug**: *«per la clipboard ho
> idea precisa: solo testo»* — no images, no files, **no rich formats**.
>
> ⚠ And it was not a nuance: `RCP.md` §7.4 built the three messages **without any field that
> declares the type**, and wrote the reason beside it — *«non esiste perché non c'è niente da
> scegliere»*. HTML would need that field, and §9 forbids adding fields to existing messages
> within a major version: **the window has been closed since 10 Aug**.
>
> ⭐ Asked the user before writing code, and **he chose «solo testo semplice»**. ⇒ The
> decision of 9 Aug holds, and this line exists so that the next time someone reads
> «formatted» they know the question has already been asked.

#### 4.5.1 · The six files, and what each one does

| file | what it carries |
|---|---|
| ⭐ `src/appunti.h` + `.c` (**new**, ~640 lines) | the **Mutter** side, ported from `fondamenta/…/appunti_mutter.c` with the four traps defused on the spot. ⛔ Text only: the MIME types live in there and do not come out |
| `src/figlio.c` | four new messages on the parent↔child socket (`APPUNTI_OFFERTA`, `APPUNTI_DAL_CLIENT`, `APPUNTI_DALLA_SESSIONE`, `APPUNTI_VUOLE`), the **third assembly table** and the **time bottom** of whoever pastes |
| `src/rcp.c` + `.h` | the three messages of §7.4, the table of incoming streams, the five new hooks, and the **cure of the race with `Ctrl+V`** |
| `src/webtransport.c` + `.h` | the incoming channel `0x02` (`G_UNI_APPUNTI`) and the three hooks that open a stream towards the client |
| `src/main.c` | the **fourth stitching** of the same family: video, input, audio, clipboard |
| `src/pagina.html` | the browser side: `clipboardchange` where it exists, the `paste` event where it does not, and writing to the local clipboard with the declared fallback |

⭐ **And `mutter.h` has a single new line**: `mutter_bus()`. The clipboard lives on the **same**
`RemoteDesktop` session as the stage, and opening a second connection to the bus would mean a second
name on the bus — that is a sender Mutter does not recognise as the owner of the session.

#### 4.5.2 · ⛔⭐⭐ THE RACE BETWEEN `Ctrl+V` AND THE ANNOUNCEMENT, and the cure is NOT Xpra's

`SPECIFICHE.md` §9 names it and declares it does **not** want to solve it like the reference:

> *«una trappola che tutti e tre i riferimenti letti disinnescano a mano: la corsa fra `Ctrl+V` e la
> lettura degli appunti. Xpra la risolve ritardando **ogni battuta di 100 ms** — ⛔ per noi sono
> **due volte il tetto del ritardo**: quella cura non si copia, si sostituisce.»*

**The race, in full.** The user presses `Ctrl+V` in the browser. The keys leave on the input channel;
the clipboard announcement leaves on the clipboard channel and travels the same road. ⛔ But the desktop, having received
the `Ctrl+V`, asks for the text **immediately** — and the announcement may not have arrived yet. ⇒ **The first
paste of every new text would come back empty**, and the second would work: the worst symptom
there is, because «sometimes it does not work» sends nobody looking anywhere.

⭐ **The replacement costs zero and touches no key**: the paste request **is queued**
instead of returning empty, and the question to the client leaves **when the announcement arrives**
(`rcp.c`, `rcp_appunti_chiedi` and the `T_APPUNTI_ANNUNCIO` branch of `tratta_appunti`).

⚠ And the wait is bounded by someone else, not by one more timer of ours: the **child's 4 s
bottom** answers «I don't have it» to whoever pastes if the announcement never arrives.

#### 4.5.3 · ⛔ THE TWO TIME BOTTOMS, and they are two because the debts are two

This is the part no bench would have asked for and the product did.

| where | how much | which debt it pays |
|---|---|---|
| ⛔ **in the child** (`figlio.c`, `APPUNTI_ATTESA_MS`) | **4000 ms** | the debt towards **Mutter**. A `SelectionTransfer` without an answer leaves the application that is pasting hanging **indefinitely**, and what the user sees is **a frozen desktop** — a fault nobody connects to the clipboard |
| ⚠ **in the parent** (`rcp.c`, `APPUNTI_FONDO`) | **8000 ms** | that the **channel** does not stay blocked. Without it, a client that fails to answer once queues **all subsequent pastes**: «the clipboard worked once and then never again» |

⭐ **And the bottom towards Mutter is in the CHILD, not in the parent**, for a reason that is not convenience:
the parent may have no client attached (the session outlives the client — invariant I4), the
client may vanish halfway through a transfer, and the parent itself may die. ⛔ The debt towards the
compositor on the other hand stays with whoever has the session, **and the session is in the child**.

⚠ And the two numbers are different **on purpose**: tightening them until they coincide would make them expire together,
and a text arriving at exactly the right millisecond would no longer find anyone to serve on either
side.

#### 4.5.4 · 🔸 Where §2.5 allowed two readings, and which was taken

`RCP.md` §2.5 says that the clipboard channel wants a stream *«uno **per trasferimento**»*. ⚠ A
transfer on our side is made of **two messages far apart in time** — `APPUNTI_ANNUNCIO`
now, `APPUNTI_TESTO` **if and when** someone asks.

⇒ The reading **one stream per message** was taken, and the reason is a calculation: one copies much more
often than one pastes, so keeping a stream open between the two messages would mean
keeping it open **for ever** in the vast majority of cases — and §2.5 grants the server a
finite number of streams.

⭐ **And it can be done, because what ties the messages of a transfer together is NOT the stream**: it is the field
`trasferimento`, which exists exactly for this (remark R1.11, 9 Aug 2026).

⚠ The price, declared: a client that counted streams to count transfers would count
double. No line of `RCP.md` tells it to do so, and it has the field it must look at. ⭐ The
test client made **the same choice reading only the document**, which says that the line is
ambiguous but that the ambiguity does not bite.

#### 4.5.5 · ⛔ Two values that were READ AND THROWN AWAY, and the same form as remark B-1

| where | what happened |
|---|---|
| `src/rcp.c` (`CIAO`) | `appunti.testo` was in `NOMI_NOTI` as a lawful name and the **value was thrown away**. ⇒ The server could neither avoid announcing to whoever had not asked, nor refuse bytes on channel `0x02` from a client that had not declared it — that is **a capability used without negotiating it**, which is the case §4.3 exists to make impossible |
| `src/pagina.html` (`ECCOMI`) | same: the page printed it in the `ECCOMI` line and kept it nowhere. ⇒ It could not have turned anything on |

⚠ It is **the same form as remark B-1** on `video.misura_massima` (10 Aug 2026): a protocol
value one declares to have understood and does not have anywhere.

---

## 5 · The measurements

*(filled in along the way — the scene declared beside every number)*

| what | expected | measured | date |
|---|---|---|---|
| ⭐ **the Opus encoder does not cost a new dependency** | — | `libavcodec` **61.19.101** on the test machine **is linked to `libopus.so.0`**, and `ffmpeg -encoders` declares **`libopus`** (besides the native `opus`, experimental). ⇒ `avcodec_find_encoder_by_name("libopus")`, and the `Makefile` **does not change** | `[M]` 17 Aug 2026, inside `enter.sh --root` on the test machine |
| ⚠ **and `opus.pc` is NOT there** | — | no `libopus-dev` in `devroot`: the road of libopus's native API **would cost a package on two build environments** (the laptop's container and the test machine's `devroot`) | `[M]` 17 Aug 2026 |
| ⭐⭐ **the browser decodes Opus** (A1) | ⏳ unknown | **440 Hz**, RMS **0.3504** (Chrome 151) and **0.3510** (Firefox 140esr), against 0.3536 expected — **bare** packets, no errors. Scene: 50 blocks of 20 ms, 440 Hz tone amplitude 0.5, 48 kHz stereo, encode→decode round inside the browser | `[M]` 17 Aug 2026, `07-b40`, **two engines** |
| ⭐⭐ **the judge sees the faults** | 5 out of 5 | ⭐ **6 cases out of 6**: healthy green, four faults seen, and `NIENTE DA GIUDICARE` as an outcome of its own. ⛔ Big-endian is recognised **from the purity (0.142)**, not from the frequency | `[M]` 17 Aug 2026, `07-b40`, two engines |
| ⛔ **how many bytes a datagram carries** (A2) | `[S]` ~1200 | **1024** on Chrome 151 (fixed) · **1024 → 1214** on Firefox 140esr. Scene: **real** server on the test machine, port 7700, wired local network, no session open | `[M]` 17 Aug 2026, `07-b40 --wt` |
| ⭐ **the PCM of §5.3 fits** | it must fit | **yes on both**, margin **52 bytes** on Chrome and **242** on Firefox | `[M]` 17 Aug 2026 |
| ⭐⭐ **the audio wire, PCM** | 200 blocks/s, 440 Hz | **1000 blocks out of 1000** in 5.000 s — **yield 100.0 %**, step between the `istante`s **always 5000 µs**, zero out of step. Signal: **440 Hz**, RMS **0.3535** (expected 0.3536), **purity 0.9963** | `[M]` 17 Aug 2026, `07-b41` + `01-b3-cliente` + `07-b42` |
| ⭐⭐ **the audio wire, Opus** | 50 blocks/s | **251 blocks** in 5 s (50.2/s = the 20 ms of §5.3), **279-439 bytes** per packet at 96 kbit/s | `[M]` 17 Aug 2026 |
| ⭐⭐⭐ **OUR server's packets decoded by the BROWSER** | — | **440 Hz**, RMS **0.3515**, purity **0.997**, on **Chrome 151 and Firefox 140esr**, 251 packets out of 251, zero errors. ⛔ Not the packets the browser had encoded itself: those that came out of `libopus` inside the server, taken **from the wire** | `[M]` 17 Aug 2026, `07-b40 --pacchetti` |
| ⭐⭐ **the REAL chain is alive** (sink → monitor → Opus → socket → datagram) | 50 blocks/s | **397 blocks in 8 s = 49.6/s**, zero lost, zero discarded. The sink appears in `wpctl status` as **default**, `monitor.channel-volumes: true`. Scene: `prova2`'s GNOME session on the server, test tone **off** | `[M]` 17 Aug 2026, port 7710 |
| ⭐⭐⭐ **and the session's sound ARRIVES** | 440 Hz | ⛔ *The first measurement said «silence», and it was the SCENE that was broken — see §6.5.* With the certified scene: `suono.c` delivers **PEAK 16383 out of 32767** (= half full scale, the exact amplitude of the tone) and the contiguous stretches give **440 Hz, rms 0.3535** — identical to what `pw-record` reads on the same monitor | `[M]` 17 Aug 2026, `07-b43` |
| ⭐⭐ **and the volume GOVERNS** | I5 and §kde §10.5 | full volume **0.3536** · at 25 % **0.0078** (expected 0.005525) · mute **0.0**. ⇒ The trap of the monitor upstream of the volume **is not there**: `monitor.channel-volumes` is requested and works | `[M]` 17 Aug 2026, `07-b43`, against the product |
| ⭐⭐⭐ **the real audio bench: 5 rounds out of 5** | the expected value written **beforehand** | **1-healthy** 440 Hz rms 0.3535 (expected 0.3536) · **2-silence** 0 Hz rms 0.0 · **3-frequency** 660 Hz · **4-volume-25** rms **0.0055** (expected 0.0055) · **5-mute** 0.0. ⛔ And rounds 2 and 3 are faults **grafted on purpose**: the bench sees them, so it is not blind | `[M]` 17 Aug 2026, `07-b43`, against the product |
| ⭐⭐ **and REDONE after the eight cures to the transport** | 5 out of 5 | **5 out of 5**, and ⭐ **better than before**: purity is **1.000** on all rounds with signal (it was **0.29** when blocks were being lost), and the judge could look at **96 000 samples** instead of 48 000 — because now there is enough **contiguous** sound to judge. ⛔ Redoing it was not a formality: the other green was from **before** the datagram queue, the retransmission cap, coalescing and padding were touched — that is an old green on new code | `[M]` 17 Aug 2026, evening |
| ⭐ **the datagram that did not leave** | 0 % loss | from **38.5 %** to **0.3 %**: 2994 sent, 8 refused, 1 thrown away for full queue out of ~3003. ⚠ On **Opus** the loss was already **zero** (0 out of 747): the fault bit the **PCM**, which costs 13 times the bandwidth | `[M]` 17 Aug 2026 |
| ⭐ **libopus does not accumulate** | `[?]` | **1000 blocks in, 1000 out, zero EAGAIN** ⇒ the `istante` of §6.3 belongs to the block that leaves | `[M]` 17 Aug 2026, `07-b44` |
| ⚠ **Opus's pre-skip** | declared by nobody | `initial_padding` = **312 samples = 6.50 ms**, **constant** over a thousand packets. The decoder removes it by itself, so end to end it cancels out | `[M]` 17 Aug 2026, `07-b44` |
| ⭐⭐ **the clipboard opens on a REAL GNOME session** | `EnableClipboard` granted | ⭐ `appunti della sessione accesi (solo testo, nei due versi) su /org/gnome/Mutter/RemoteDesktop/Session/u1`. ⛔ It is the first and for now **only** proof that `appunti.c` works against Mutter | `[M]` 17 Aug 2026, port 7730, user `prova` |
| ⛔⛔ **XWayland does NOT exist in our sessions** | `xclip` was supposed to work (§2.4) | `gnome-shell --headless --no-x11` ⇒ **no X11 bridge**. ⚠ The two sockets in `/tmp/.X11-unix` are leftovers from **15 Aug**: a bench that took them as good would have measured a dead session | `[M]` 17 Aug 2026 |
| ⛔ **and no ordinary Wayland client owns the selection in there** | the arbiter was supposed to copy | `wl-copy` says **«This seat has no keyboard»**; a GTK client says `COPIATO` ⛔ **and nothing reaches the compositor** — the product, which is instrumented, records **no** `SelectionOwnerChanged`. ⚠ Not even with a presented window, and not even with a REMOTIX client attached (that is with libei's virtual keyboard present) | `[M]` 17 Aug 2026, three attempts |
| ⭐⭐ **the volume trap, reproduced** | the volume must arrive | two twin sinks, PipeWire **1.4.2**: with `monitor.channel-volumes=true` the monitor reads **0.3535 · 0.0055 · 0.0000** at 100 % · 25 % · mute; ⛔ **without**, it reads **0.3535 always, mute included** | `[M]` 17 Aug 2026, `07-b43` |

---

## 6 · ⛔ What did NOT work

*`PIANO.md` §0.3.2: it is filled in even when it looks bad.*

### 6.1 · Two faults of the bench in the early afternoon, and both lied about the REASON

⭐ **Neither of the two gave a wrong result: they gave the right result with the wrong
reason written beside it** — which is the form that costs half a day when it shows up on a
number that counts.

| # | the fault | how it showed | the cure |
|---|---|---|---|
| **1** | the server compared `self.path` **with the query inside**: `/?wt=…` is not `/`, so **404** | *«no carrier in 45 s»* — that is *«the page did not reach the end»*, while the page **had never been served** | the query is cut before the comparison |
| **2** | `wt.ready` **may never return**, neither resolved nor rejected, and the probe had no ceiling | here too *«no carrier»*: the **launcher's** deadline written in place of the **connection's** deadline | a ceiling of 10 s, with the outcome **`SCADUTA`** distinct from the others |

⇒ ⛔ **Twice in the same afternoon the bench said «I did not measure» when it should have said
«I measured and did not succeed, here is where».** It is `CODER.md` §3.10 — *«una lettura negata non
è una lettura che dice zero»* — found in the tool written to apply it.

⚠ **And the first of the two was seen only because the probe already worked without `--wt`**: the healthy
case existed from before. Without that comparison, the suspect would have been the engine.

### 6.2 · ⛔⛔ A wrong diagnosis that «improved» — and it almost bought me a change

*It is the most instructive fault of the day, and it is not in the product: it is in my reasoning.*

The first round of the tone gave **402 blocks out of 600** in 3 s — yield **67 %** — ⭐ with **zero blocks
lost**: the step between the `istante`s was **always exactly 5000 µs**. I concluded *«the datagram
queue has become the rate ceiling»* and took it from 8 to 32.

⭐ **The yield rose to 80 %.** That is, the number improved, and it looked like a confirmation.

⛔ **It confirmed nothing.** 2.01 s out of 3 and 4.01 out of 5 are not a fraction: they are **T − 1**. The
third point decided it in thirty seconds — **9.01 s out of 10**. ⇒ It was not a yield: it was **a fixed
second at the head of every take**, and the queue had nothing to do with it.

| | |
|---|---|
| **the real cause** | the tone waited for QUIC's **normal beat** before the first block, because `wt_battito_ns()` shortened the wait only *after* the first block had been produced |
| **the cure** | two lines: the first block is **due immediately** |
| **the result** | **1000 blocks out of 1000**, yield **100.0 %** |
| ⛔ **and the 32 went back to 8** | `[M]` at 8 the lost blocks were **already zero**: it was enough. A higher value would have stayed in the code **without a reason**, justified by a false diagnosis |

⇒ ⭐ **The lesson is about method, and it holds beyond audio**: *a number that improves is not a confirmation*.
Two points lie on a straight line by chance; the third cost thirty seconds. ⚠ And the symptom — a
**percentage** — pointed towards the *rate*, while the fault was a **start-up delay**: two
completely different places in the code. The form is that of `LEZIONI.md` §1.9, *the red pinned
on the wrong suspect*, in a new variant: **the partial green that rises**.

### 6.3 · And three minor stumbles, with their cause

1. ⛔ **`printf … | sudo -S` eats the `stdin`** — twice in the same script: the first time it
   made `tar` read the password (*«gzip: stdin: not in gzip format»*), the second it
   gave `bash -s` an empty stdin, ⚠ **and that one gave no error**: the step printed
   its header and did nothing. *«It did nothing» had the same face as «it
   worked»*;
2. ⛔ **I shipped the laptop's `.o` files to the test machine too**, and `make` compiled
   nothing. ⭐ **The `ldd` check rejected it** — that is its job — but without that check
   I would have measured the laptop's code believing it the server's: fault **D5**;
3. ⛔ **I took `prova2`'s password from the wrong file**: `credenziali-banchi` belongs to the
   `prova2` **of the container**, not to the host's one that PAM verifies. ⚠ **It was already written**,
   in `banchi/06-b38-tela.sh`, with the words *«sono due utenti diversi con lo stesso nome, e le due
   parole si somigliano abbastanza da far perdere un'ora»*. Cost: **1 attempt out of 3** before the
   ban of §4.4-bis.

---

### 6.3-bis · E tre difetti del banco dell'audio vero, trovati girandolo

⭐ Nessuno dei tre si vedeva leggendo il codice, e il terzo vale da solo:

1. `env $* $SUL_SERVER` metteva il nome del passo **prima** del comando ⇒ `env: 'cancello': No
   such file or directory`, uscita 127;
2. un passo scriveva in una cartella non ancora creata ⇒ *«No such file or directory»* travestito
   da *«non riesco a leggere il grafo»*;
3. ⛔ **`timeout 8 <funzione di shell>` esce 127**, perché `timeout` esegue un programma e una
   funzione non lo è. ⚠ Per due giri l'esito è stato letto come *«il sink non nasce»* — mentre il
   sink **non era mai stato chiesto**. È `LEZIONI.md` §1.9 in forma pura: il rosso puntato
   sull'imputato sbagliato, e l'imputato vero era il tetto messo nel posto sbagliato.

### 6.5 · ⛔⛔ «L'audio è silenzio» era una MIA misura rotta, e c'è voluta una refutazione

*17 agosto 2026. È il difetto più caro della giornata, e non era nel prodotto.*

Avevo misurato, e scritto, che la cattura consegnava silenzio: il sink c'era, le porte `monitor_*`
c'erano, `pw-play` arrivava al sink — ⛔ ma «nessun collegamento consumava il monitor» e «il nodo
della cattura non compariva nel grafo», mentre dichiarava 48 000 fotogrammi al secondo.

⭐ **Tre difetti di scena, tutti miei**, trovati da un agente mandato a refutare:

1. ⛔ **il tono non suonava affatto.** `pw-play` lo diceva per nome — *«no target node
   available»* — perché **il sink nasce col primo ascoltatore**, e nei miei giri partiva prima.
   Una scena che non suona misura il nulla;
2. ⛔ **le fotografie del grafo le scattavo a sipario chiuso**: l'attesa del marcatore non
   agganciava e consumava i suoi 45 s interi, così la sonda arrivava **~1 s dopo la fine della
   sessione**. Da lì «nessun nodo» e «nessun collegamento»;
3. ⛔ **avevo letto male `pw-mon`**: `removed: id 47` non era il nostro nodo, era un
   identificativo **riciclato**. Gli id globali di PipeWire si riusano.

⇒ ⭐ **E il punto 6 era vero e coerente**: la cattura consegnava correttamente il silenzio di una
sessione in cui non suonava nessuno. ⚠ *Due misure che si contraddicono, e a mentire era quella
che sembrava più solida*: `CODER.md` §3.11 dice esattamente di sospettare prima della misura.

⭐⭐ **E la cura non è stata una cura: è lo strumento che mancava.** In `suono.c` adesso c'è il
**picco del campione** — il più forte in valore assoluto — stampato nella riga di chiusura. Senza,
*«non si sente niente»* ha **due cause con la faccia identica** (48 000 fotogrammi/s consegnati, 0
scartati, flusso in `streaming`): *nessuno suonava* oppure *PipeWire ci dà buffer vuoti*. È
`CODER.md` §3.10 applicata al **campione** invece che al conteggio, e letta per prima chiude la
diagnosi in una riga.

⚠ **E cinque strade sono state provate e refutate con una misura, non con un ragionamento**: «è
un'altra istanza di PipeWire» (stesso `client.id`), «WirePlumber sospende il sink dopo 5 s»
(`suspend-timeout` a 0: rms ancora 0), «i buffer non sono condivisibili» (aggiunto `MemFd`: picco
ancora 0), «WirePlumber distrugge il nodo» (letto il componente: pretende flag che non mettiamo),
«un volume salvato a zero» (letto lo stato: tutto a 1,0).

### 6.6 · ⭐⭐ Il 38 % dell'audio che non partiva — e la causa scritta era sbagliata

`[M]` 17 agosto 2026, audio vero in **PCM** con il video acceso: **1163 datagram rifiutati su
3001**, e il giudice leggeva **464 Hz invece di 440** con purezza **0,29**. ⚠ Il suono non era
«con qualche buco»: concatenare quel che resta fa saltare la fase ogni due blocchi, ed **era un
altro suono**.

Il commento nel codice diceva: *«nel pacchetto non ci stava, quindi non ci starebbe mai»*.
⛔ **La misura dice il contrario**: `cwnd_left` = **12 198 byte** contro 973 chiesti, `destlen`
1452. ⇒ Non è né il buffer né la congestione: **è il pacer di QUIC**, che dice *«non adesso»*.
E «non adesso» diventa «mai» solo se lo buttiamo noi.

| la cura, in tre tempi | rifiutati |
|---|---|
| come stava — si buttava subito | **1163 su 3001** (38,5 %) |
| si RIMANDA invece di buttare (tetto 8) | 1064 su 2999 — ⛔ **quasi niente** |
| e il rimando si lega al **tempo**, non alle chiamate | 236 su 3001 (7,9 %) |
| ⭐ e il tetto dei rimandi sale da 8 a **64** | **8 su 3003** — e 1 buttato per coda piena ⇒ **0,3 %** |

⭐ **E il terzo passo l'ha chiesto il giudice, non io**: a 7,9 % di perdita leggeva ancora
**465 Hz**, ⛔ e quel numero *è* la perdita — concatenare i blocchi superstiti comprime il tempo,
e 440 / (1 − 0,054) ≈ 465. ⇒ La frequenza letta era un **misuratore di perdita**, non un difetto
del suono.

⚠ **E il tetto basso non proteggeva da niente**: il ritardo lo governa già la **coda** (otto
blocchi = 40 ms, e oltre si butta il più vecchio). Un tetto sui rimandi buttava un blocco che
sarebbe partito — due meccanismi per lo stesso mestiere, e quello sbagliato mordeva per primo.

⛔ **Il passo di mezzo è quello che insegna**: `ngtcp2_conn_write_aggregate_pkt2` richiama la
scrittura più volte per comporre un lotto, **con lo stesso `ts`**. Gli otto rimandi si consumavano
tutti lì dentro, in un microsecondo — senza che passasse **un istante** in cui il pacer potesse
cambiare idea. ⚠ E il conto sembrava dire il contrario: *8008 rimandi «riusciti»* accanto a 1064
blocchi buttati lo stesso.

### 6.7 · ⛔ Il banco si dichiarava CIECO, e aveva ragione — la scena non si zittiva

*Dopo la cura di §6.6 il prodotto dava **440 Hz esatti**, ⛔ ma il giro «2-silenzio» misurava
**440 Hz a 0,3535** — cioè il tono a pieno volume dove non doveva suonare niente.*

⭐ **E il banco non ha dato verde: si è dichiarato cieco.** *«Doveva vedere SILENZIO e ha detto
VERDE»* — cioè ha rifiutato di certificare gli altri quattro giri, che è esattamente il suo
mestiere: *un banco cieco dà verde a tutto*.

⛔ **La causa era la scena, non il prodotto**: `kill "$PP"` uccideva l'**involucro** (`setpriv`),
non `pw-play`, che sopravviveva e cantava **dentro il giro dopo**. ⚠ È la trappola che
`LEZIONI.md` §2.3-quinquies nomina per la clipboard — *«quel che resta dal giro prima va svuotato
all'inizio»* — e vale per ogni scena condivisa: il suono è una scena condivisa.

⭐ **E la cura non è uccidere: è verificare.** Il banco adesso legge dal grafo che i legami in
ingresso al sink siano **zero** prima di andare avanti. *«Ho ucciso»* e *«non suona più nessuno»*
sono due fatti diversi, e al giro dopo serve il secondo.

⇒ ⭐ **5 giri su 5**, e i due difetti innestati visti tutti e due.

### 6.8 · ⛔⛔⛔ IL DIFETTO VERO, E PERCHÉ CI SONO VOLUTE SETTE CURE PER ARRIVARCI

*17 agosto 2026. È il capitolo più caro della fase, e il difetto era in una riga.*

**Il difetto**: si spediva **un solo datagram per passata di scrittura**, e le passate sono ~25 al
secondo. Il figlio ne produce **50**. ⇒ Uno passava, uno restava in coda, e la metà dell'audio
moriva. ⛔ Non era la rete, non era il pacer, non era il video: **era il ciclo, che ne offriva uno
per volta**. E lo spazio c'era da vendere — un pacchetto è **1452 byte**, un blocco di Opus **230**:
il pacchetto restava mezzo vuoto mentre l'audio veniva buttato.

⭐ **La precisione del numero era l'indizio**: *esattamente* la metà. Una perdita di rete non è
mai esattamente la metà; un'aritmetica sì.

#### Le sei cure prima di quella giusta, e che cosa insegnano

| # | che cosa ho curato | l'esito | che cosa era |
|---|---|---|---|
| 1 | il rimando invece dello scarto | 38,5 % → 7,9 % | cura vera, ma a valle |
| 2 | il rimando legato al **tempo** e non alle chiamate | 7,9 % → 0,3 % *in locale* | cura vera |
| 3 | la coalescenza col pacchetto video (`MORE`) | nessun cambiamento per l'utente | ⛔ diagnosi sbagliata: *«il video si mangia la finestra»* — e i suoi fotogrammi erano da **70-1300 byte** |
| 4 | la priorità di tempo reale (**R26**) | nessun cambiamento | ⭐ difetto **vero e necessario**, ma non questo |
| 5 | il riempimento GSO (`PADDING`) | nessun cambiamento | ⭐ difetto vero, non questo |
| 6 | il pacchetto che buttavo con dentro i riscontri | nessun cambiamento | ⭐ difetto vero e grosso, non questo |
| ⭐ **7** | **più datagram nello stesso pacchetto** | 50 % → 18 % | **la causa** |
| ⭐ **8** | e il tetto ai rinvii tolto: **decide la coda** | 18 % → **0 %** | la coda del difetto |

⇒ ⛔ **Sei cure su otto erano difetti veri che non erano quello che l'utente sentiva.** Ognuna
sembrava confermata dal ragionamento e nessuna dalla misura, perché **la misura che serviva non
esisteva**.

#### ⭐⭐⭐ E LA LEZIONE È UNA SOLA, E NON È SULL'AUDIO

**Avevo i numeri di tre anelli su quattro.** Il figlio diceva quanti blocchi produce, il server
quanti ne spedisce e quanti ne rifiuta, la sessione quanti campioni consegna. ⛔ **Della pagina —
cioè del lato che ASCOLTA — non si sapeva niente**: quanti ne arrivano, quanti se ne suonano,
quanti buchi fa la riproduzione.

⇒ Per sei cure ho curato **il lato che parla**, misurandolo, mentre il difetto si vedeva solo
mettendo i due lati sulla stessa riga. Il giorno in cui quei contatori sono esistiti, la diagnosi
è durata **un passaggio**:

> 50 prodotti → 40 consegnati → deficit 20 % → cuscino 250 ms → **un buco ogni 1,25 s**.
> Misurati: **23 buchi in 30 s**.

⭐ **Il conto si è chiuso al decimale, e ha assolto tre imputati in un colpo** (la pagina, il
cuscino, il thread principale) indicando l'unico colpevole rimasto.

⚠ È `CODER.md` §3.8 — *«si verifica dal lato che deve ricevere»* — e io l'avevo applicata al
**contenuto** (il giudice ascolta i campioni) e **non al ritmo**. Un banco che ascolta *che cosa*
arriva e non *quando* arriva è cieco su metà dei difetti possibili.

⛔ **E l'endpoint che serviva costava trenta righe** (`/diario` in `pagina.c`): il riquadro di
diagnostica della pagina non bastava, perché col desktop acceso la pagina è a tutto schermo e quel
riquadro **non è raggiungibile** — chiederne la lettura all'utente era chiedergli una cosa che non
si può fare.

### 6.9 · ⛔⛔ L'ARBITRO ESTERNO DEGLI APPUNTI NON ESISTE — e §2.4 prometteva il contrario

*17 agosto 2026, sera, alla prima accensione del banco `07-b45`.*

§2.4 di questo documento diceva, in grassetto: *«il lato indipendente del banco degli appunti c'è
già, ed è gratis»* — `xclip` funziona senza una nostra sessione, perché la sponda X11 di Mutter è
incondizionata (`STUDI.md` §gnome §10 `[R]`).

⛔ **È vero del codice di Mutter e falso delle nostre sessioni.** `[M]`: il compositore gira come

```
gnome-shell --headless --no-x11
```

⇒ **XWayland non parte affatto.** Non c'è nessuna sponda X11 da usare.

⚠ **E la trappola dentro la trappola**: `/tmp/.X11-unix` conteneva `X0` e `X1`, di proprietà di
`prova`. Un banco che avesse creduto a quei socket avrebbe puntato a una sessione **morta dal 15
agosto** e avrebbe dato il rosso al prodotto. ⛔ Il passo 0 di `07-b45` li cercava proprio così: la
prima stesura del banco conteneva il difetto che il banco esisteva per evitare.

#### E il ripiego non ha retto neanche lui

L'arbitro è stato rifatto su **GTK/GDK** — un client Wayland vero, che è anche *meglio*: prova la
strada che percorre un'applicazione, non una sponda che i nostri utenti non hanno. ⛔ Non funziona
lo stesso, e le cause provate sono state tre:

| tentativo | esito |
|---|---|
| `Gdk.Display.get_default()` | **`None`**: senza `Gtk.init()` non c'è display. ⚠ E il messaggio d'errore accusava **la sessione** di non esistere mentre la sessione era viva — `CODER.md` §3.11, il sospetto va prima sulla misura |
| `Gdk.Display.open(None)` | **aborto**, `gdk_display_open() was called before gtk_init()` |
| `Gtk.init_check()` | ⭐ il display si apre, `set()` riesce, ⛔ **e al compositore non arriva niente** |

⛔ **La causa vera è di protocollo**: per `wl_data_device.set_selection` serve il *serial* di un
evento d'ingresso, e a un client senza superficie a fuoco non arriva nessun evento. ⚠ Presentare
una finestra non è bastato, e nemmeno avere un client REMOTIX attaccato — cioè con la tastiera
virtuale di libei presente, che era il primo sospetto (`wl-copy` dice **«This seat has no
keyboard»**). ⇒ **Due cause plausibili per lo stesso sintomo, e la prima non era quella.**

⭐ **E questo spiega perché REMOTIX invece ci riesce**: `appunti.c` passa dalla sessione
`RemoteDesktop` di Mutter, che è **la via privilegiata e non chiede il fuoco**. È esattamente il
motivo per cui quella via esiste — e il banco l'ha dimostrato per contrasto.

⏳ **Che cosa resta da decidere**: un arbitro esterno per il verso `sessione → dispositivo` va
trovato in un'applicazione **vera con una finestra a fuoco**, pilotata dall'input di REMOTIX — cioè
la scena dell'utente. ⚠ Oppure si accetta che quel verso lo giudichi **lui**, che è l'invariante I8
e non un ripiego.

### 6.10 · ⛔ E DUE DIFETTI DEL CLIENTE DI PROVA, tutt'e due miei, tutt'e due travestiti

Scrivendo il canale appunti nel secondo lettore di `RCP.md`.

**1. Aspettavo DUE byte per riconoscere uno stream unidirezionale.** Gli stream QPACK del server
ne portano **uno solo** (il tipo, `0x02` e `0x03`) e poi tacciono: quel byte finiva nel mio
accumulo e non arrivava mai ad `aioquic`. ⇒ Il suo strato HTTP/3 non consegnava le intestazioni
della CONNECT, il cliente restava ad aspettare, ⛔ **e il server lo congedava con `TEMPO_SCADUTO`
per non aver mai aperto il canale di controllo** (§4.6).

⚠ **Il rosso finiva sul server**, che aveva fatto esattamente quel che §4.6 gli dice di fare.
`LEZIONI.md` §2.3: *«una prova che boccia il codice giusto costa quanto una che promuove quello
sbagliato»*. ⭐ La cura non è accumulare meglio: è **non accumulare affatto** quel che non è nostro —
uno stream WebTransport comincia per `0x40`, e ogni altro primo byte è di `aioquic`.

**2. Il giudizio «altro» non aveva un ramo suo.** Uno stream già riconosciuto come video (`0x03`)
ricadeva nel ramo «non so ancora che cos'è» a **ogni pacchetto**, veniva ribattezzato «h3», ⛔ e i
byte di un fotogramma finivano dentro lo strato HTTP/3. ⚠ Il sintomo era
`Only one QPACK decoder stream is allowed` — **un errore di HTTP/3 su una connessione dove HTTP/3
non c'entrava niente**, e la connessione cadeva a metà giro.

⭐ Tutt'e due sono la stessa forma: **un difetto del banco travestito da difetto del prodotto**, ed è
la ragione per cui `PIANO.md` §0.3.4 vuole il banco certificato prima di essere creduto.

---

### 6.4 · ⭐⭐ La revisione avversariale — **tredici rilievi, e quattro erano seri**

*17 agosto 2026, su `audio.c`, `webtransport.c`, `pagina.html`, `rcp.c`, `main.c`. Il revisore ha
ricevuto **il codice e la specifica, non il ragionamento di chi l'aveva scritto** (`PIANO.md` §0.4).*

| # | il difetto | perché era serio |
|---|---|---|
| ⛔⛔ **4** | `wt_battito_ns()` e `tono_passo()` avevano **due guardie diverse per lo stesso fatto** | in ogni caso coperto da una e non dall'altra, il battito tornava un istante **nel passato** e nessuno lo spostava: `poll()` con timeout 0, **ciclo al 100 % di CPU**. ⚠ E il caso è normale — *un browser chiude la sessione e tiene viva la connessione*, scritto nel nostro stesso file |
| ⛔⛔ **1** | la pagina dichiarava `opus` **senza chiedersi se sapeva decodificarlo** | §4.3 obbliga il server a seguire l'ordine di preferenza del client ⇒ su un motore senza `AudioDecoder` il server **doveva** scegliere Opus: 50 datagram/s in un `continue`, e il PCM — che esiste per essere il controllo positivo — non entrava mai in gioco. ⭐ Il video, nello stesso file, filtrava già con `isConfigSupported` |
| ⛔ **2** | `AudioContext` e `AudioDecoder` **mai chiusi** | al settimo riattacco senza ricaricare, il motore rifiuta; l'eccezione usciva dal `for(;;)` del lettore dei datagram e **uccideva l'audio per tutta la sessione, senza una riga** |
| ⛔ **3** | `suona()` **sovrapponeva invece di buttare** | il commento diceva «butto il più vecchio»; il codice non teneva i riferimenti e non fermava niente. ⇒ Non un buco: **un segnale raddoppiato** |
| ⛔ **5** | `opus_apri()` fuori dal `try` | una `configure()` rifiutata uccideva il lettore in silenzio, **e lasciava `a.dec` assegnato ma non configurato** |
| ⛔ **6** | sei strade di scarto su otto **mute** | e `wt_audio_conti()` **non aveva un solo chiamante**: i contatori non raggiungevano mai una riga. ⇒ «l'audio buttato» e «l'audio mai arrivato» avevano la stessa faccia |
| ⛔ **8** | *«lo scrive nel registro a ogni sessione»* — **non lo scriveva** | l'interruttore di I6 c'era, la dichiarazione che deve seguirlo no: chi leggeva il registro un'ora dopo non poteva sapere che quel che si sente è un tono di banco |
| ⛔ **13** | `dgram_accoda` rifiutava **senza contare e senza dirlo** | irraggiungibile oggi, ⚠ ma con `figlio.c` stava arrivando il secondo chiamante |

⭐ **E il rilievo 7 chiedeva una misura, non una discussione** — ed è quello che ha reso di più:
*«`audio.h` dichiara che Opus può non produrre un pacchetto per ogni blocco; §6.3 vuole nell'istante
il tempo del primo campione. Una delle due è falsa.»* ⇒ Misurato in isolamento (`07-b44`): **falsa
la prima**, e la misura ha trovato in più il **pre-skip** che nessuno aveva dichiarato.

⚠ **Sette aree dichiarate «non ho trovato niente»**, con quelle parole: l'inquadratura di §6.3
contata byte per byte, il little-endian, l'aritmetica dell'anello, l'invariante I3 sull'audio, il
confronto degli istanti, la fame degli stream, le perdite di memoria. ⛔ *Non è un'assoluzione*, ed
è la forma che `PIANO.md` §0.4 impone.

⏳ **Restano `[?]` da misurare**: il rilievo 9 (il datagram davanti agli stream può **rimpicciolire
il segmento GSO** di tutta la passata, cioè tre `sendto` per fotogramma invece di uno) e il 10
(`nw == 0` ha **tre** cause e il registro ne nomina una).

---

## 7 · Le decisioni prodotte

*(collegamenti a `DECISIONI.md` §x.y — **non copie**)*

⚠ **E una cosa da notare prima di cominciare**: `DECISIONI.md` ha un capitolo intero per gli
appunti (**§5-ter**) e **nessuno per l'audio**. Le scelte dell'audio stanno sparse in
`SPECIFICHE.md` §10, `RCP.md` §5.3 e l'invariante **I5**. ⇒ Se questa fase prende una decisione
sull'audio — la strada del codificatore, la profondità della coda, come si suona nella pagina —
**va messa a verbale lì**, non lasciata dentro un commento nel codice.

---

## 8 · Che cosa resta `[?]` — **riscritto il 21 agosto 2026**

> ⛔ **Questa sezione mentiva.** Era ferma al 17 agosto *«dopo la sonda e prima del prodotto»* ed
> elencava come aperte cose chiuse quella sera stessa dal giudizio dell'utente — *«problema audio
> risolto»*, *«clipboard funziona in entrambi i versi»*. ⚠ Un documento di fase che racconta uno
> stato di quattro giorni fa è la specie di difetto contro cui `PIANO.md` §0.1 esiste: chi lo legge
> rifà lavoro già fatto, o cerca un guasto dove non c'è. ⇒ Qui c'è lo stato **vero**, e l'elenco
> vecchio è stato tolto invece di essere lasciato accanto.

### ✅ Difetti veri, aperti: **NESSUNO** — chiuso il 22 agosto 2026 dal giudizio dell'utente

> ⭐⭐ *«Le 4 prove che ho eseguito prima davano un audio OK»* (quattro motori: Linux Chrome, Linux
> Firefox, Windows Chrome, Android Chrome), e alla domanda diretta sul ritardo: *«**ho già scritto
> prima che il ritardo audio/video è ok**»*. ⇒ §9.8.
>
> ⚠ **Quel che segue resta scritto**, ed è la storia di come ci si è arrivati — dalla prima diagnosi
> sbagliata alla cura. ⛔ Non si cancella: la forma dell'errore vale più della conclusione.

#### ⛔ Com'era il 21 agosto sera — **uno, e adesso ha un nome**

> ⛔ **Un'ora fa qui c'era scritto «difetti veri aperti: nessuno».** Era il giudizio *«audio e video
> perfetti»* preso alla lettera, ⚠ e l'utente lo ha precisato subito dopo, sul PC Windows:
> *«**il ritardo di 400 ms fra audio e video in generale te lo confermo**»*. ⇒ Il difetto c'è, è
> **generale** (non di una piattaforma), ed è **udibile**: quel che si vede e quel che si sente non
> stanno insieme.

⛔ **IL RITARDO DELL'AUDIO SUL VIDEO — ~400 ms, e la causa è nostra e scritta.**

`[M]` **`src/pagina.html`: `AUDIO_CUSCINO_MS = 250`** — non 60. Il 60 è stato alzato a 250 il
**17 agosto**, e il commento del codice dice perché: *«il video si decodifica e si dipinge sullo
**stesso thread** che programma l'audio; quando quel lavoro supera il cuscino la riproduzione si è
già svuotata e il cuscino si riarma — e ogni riarmo è un BUCO»*. ⚠ Fu la cura del *«jitter
pazzesco»*, e ha funzionato: i buchi sono spariti. ⛔ Il prezzo era **dichiarato nel commento** —
*«250 ms fra quel che si vede e quel che si sente»* — e adesso l'utente lo ha sentito.

**La somma che fa i 400**: 250 di cuscino + la cattura, la codifica Opus, il filo, la decodifica.
⭐ Il video, sulla stessa sessione, sta sotto i 50 ms del suo tetto ⇒ **la distanza fra i due è tutta
qui dentro**, e non è la rete.

#### ⛔⛔ La prima lettura di questa misura era MIA, ed era SBAGLIATA in quattro punti

> *Scritto dal coordinatore la sera del 21 agosto leggendo i contatori del diario; **smentito due ore
> dopo** dall'agente A1 con i numeri **dello stesso registro**. Resta scritto perché la forma
> dell'errore vale più della correzione.*

| avevo scritto | `[M]` è invece |
|---|---|
| «coda **239-270 ms** per i primi due minuti» | ⛔ sono **389-539 ms**. I 239-270 sono la coda **dopo il primo riarmo** |
| «**BUCHI 4**, tutti dell'avvio, il numero non sale più» | ⛔ **1 all'avvio e 3 in mezzo alla sessione** (18:00:14, :19, :29), ognuno con una perdita di datagram nella stessa finestra |
| «il conto chiude e **assolve tutti gli altri anelli**: non si perde niente» | ⛔ **si perde**: 61 blocchi = **1 226 ms**, lo 0,58 %. In un'altra sessione dello stesso registro: **684 blocchi, 13,7 s, il 9,43 %** — e in 25 s dentro quella, **il 47 %** |
| «nessun datagram **scartato dal server**» | ⛔ il server ne ha scartati **2 200**, ⭐ e **scrive anche perché**: prima «il quanto del pacer», poi `cwnd_left = 0` |

⚠ **Come ho sbagliato, perché è la lezione**: ogni anello **contava se stesso** e diceva la verità.
Il figlio: «50,00 spediti al secondo, 0 persi» — vero. La pagina: «10 621 ricevuti, 10 617 suonati»
— vero. ⛔ **Nessuno dei due contava quel che stava in mezzo**, e la sottrazione non l'ha fatta
nessuno: 50,00 spediti contro **49,71** ricevuti. Ho letto quattro colonne verdi e ho scritto
«assolve tutti»: è la stessa forma di `LEZIONI.md` §1.20 — **un numero che nessuno confronta** — con
l'aggravante che il numero mancante andava *calcolato*, non solo letto.

#### ⭐⭐ E la `[?]` della coda che scende è CHIUSA: **la coda non è un cuscino, è un serbatoio a senso unico**

`a.prossimo` avanzava di `n/48000` **per ogni blocco che arriva**, mai col tempo che passa. ⇒

```
coda(n) = coda(n-1) + (ricevuti − attesi) × 20 ms,   riarmata a 250 quando tocca zero
```

⛔ **Ogni datagram perduto toglie 20 ms di cuscino per sempre**, e le uniche cose che lo rialzano
sono un **BUCO udibile** o il traboccamento a 600. Il modello riproduce la curva vera: **39 finestre
pulite, scarto medio 15 ms, massimo 72** ⇒ **spiega**.

⇒ ⛔ **I 70-110 ms non erano «un regime»**: erano il margine residuo dopo l'ultima raffica di
perdite, campionati 25 s prima della fine della sessione. La stessa discesa, 80 secondi prima, era
arrivata a 79 ms **e aveva fatto un buco**.

⭐⭐ **E questo cambia la cura.** In questi dati **non c'è un solo indizio** che il thread principale
abbia svuotato la riproduzione: il video ha dipinto 119-136 fotogrammi ogni 5 s **senza saltarne
uno**. ⇒ L'`AudioWorklet` **non è la prima cura**, e il *«jitter pazzesco»* del 17 agosto è spiegato
per intero da **perdite + serbatoio**: con un cuscino di 60 ms bastavano **tre blocchi persi**.

#### ⭐ La cura scritta: l'orologio si àncora all'`istante` del server

Invece di accodare (`prossimo += durata`), la riproduzione si àncora all'**`istante` che il server
mette già in ogni datagram** (`RCP.md` §6.3). Con l'ancora, una perdita **non consuma cuscino**: il
blocco dopo va al suo posto nel tempo, non in fondo alla fila. ⛔ `AUDIO_CUSCINO_MS` **non è stato
abbassato**: con l'ancora deve coprire solo il jitter d'arrivo, che nessuno ha ancora misurato.

⚠ **E la cura NON è provata dove conta**: sulla rete di casa, in 100 s, `mancati 0` — la scena non ha
avuto occasione di mostrare il difetto. Quel che è provato è che **non rompe niente** (60 s: coda
251-259 piatta, BUCHI 0, pieni 0, `usciti 2806 su 2823`) e che l'algoritmo ha le proprietà dichiarate
(`07-b61-ancora.js`: **22 casi su 22**, che ritaglia `suona()` da `pagina.html` e la **esegue**).

#### ⛔ E si aprono due cose nuove, che prima non si vedevano

1. ⛔ **Il server butta i datagram dell'audio** per il quanto del pacer e per la finestra di
   congestione, **mentre gli stream del video non perdono niente**. È del trasporto, non della
   pagina, e nessuno l'aveva mai guardato;
2. ⏳ **un terzo termine c'è davvero, ma non è quello che sospettavo**: la **deriva fra gli
   orologi**, `[M]` **0,7-1,4 ms/s** fra l'orologio del server e la scheda audio del client.
   L'ancora non la cura, e prima o poi porta al tetto dei 600 ms. Va deciso se correggerla.

`[?]` **E una sentinella che non è mai scattata**: se il decodificatore Opus **ricostruisse**
l'`istante` invece di riportarlo, l'ancora tornerebbe in silenzio a essere la scaletta di prima. La
pagina adesso lo dichiarerebbe — ⚠ ma nelle sessioni di prova non si è perso niente, quindi la
sentinella non ha ancora parlato.

### ⭐ E l'audio a scatti su Windows NON era nostro

*L'utente, dopo la sessione sorvegliata: «audio a scatti non accaduto, era un problema del mio PC
Windows».* ⚠ Si scrive lo stesso, e per due ragioni: la sorveglianza di `07-b60` è servita a
**escludere** REMOTIX con i numeri, e il sospetto che pendeva su di noi — **R26**, il `data-loop` di
PipeWire senza tempo reale — resta aperto ma **non è questo**.

### ⏳ Aperti perché nessuno li ha ancora misurati

- ⏳ **il datagram su rete non locale**: 1024/1214 byte sono presi **su cavo**. ⚠ Il giudizio di
  §9.7 è su rete di casa, e vale per **quella**;
- ⏳ **la priorità in tempo reale del percorso audio**: l'unità concede `LimitRTPRIO=20`
  (`07-b41`), ⚠ ma nessuno ha guardato che cosa ne fa PipeWire dentro il figlio.

### ⭐ Chiusi dal 17 al 21 agosto — e qui c'è scritto **come**

| era aperto | chiuso da |
|---|---|
| «gli appunti non hanno mai girato contro niente» | il giudizio dell'utente del 17 agosto sera, e poi i banchi `07-b53`, `07-b54`, `07-b56` |
| ⛔ ~~«la coda dell'audio a 400–420 ms»~~ | **NON è chiusa, e la riga sbagliata è durata un'ora**: l'utente ha precisato *«il ritardo di 400 ms fra audio e video te lo confermo»* ⇒ è tornata in §8, con la causa |
| «nessuno ha ancora ascoltato l'audio da un telefono» | ⭐ adesso qualcuno l'ha ascoltato, ed è l'utente — §9.7 |
| «il bitrate di Opus: 🔸 derivato, mai giudicato» | ⭐ giudicato **sul risultato**: 96 kbit/s hanno prodotto un ascolto che l'utente chiama pulito. ⛔ **Il cuscino no**: quello è 250, non 60, ed è il difetto di §8 |
| «l'arbitro esterno del banco non esiste» | ⭐ vero, e **non si aggira**: §6.9. I banchi guidano browser veri con Marionette e CDP, e la sessione con `wl-copy`/`wl-paste` |
| `DISPLAY` della sessione di «prova» · `xclip` sulla macchina di prova | ⛔ non servono più: la sponda X11 non c'è (`gnome-shell --no-x11`), e i banchi non la usano |
| l'incolla col **mouse** (tasto destro → «Incolla») | §9.5 — quattro anelli, e `07-b56`: 3 su 3 per motore |
| la clipboard del desktop **persa al collegamento** | §9.6 — il figlio rende alla sessione il testo che aveva lei |


## 8-bis · ⭐ 21 agosto 2026, notte — **il metro della distanza audio↔video esiste**, e le regressioni girano sul prodotto riunito

*Dieci agenti in parallelo, il coordinatore alla fusione e al collaudo.*

### ⭐⭐ `AV = aoff − voff`: la distanza si misura in continuo, su qualunque contenuto

⛔ **Il difetto che l'utente ha confermato non aveva un metro**, ed è la ragione per cui quattro
anelli verdi hanno convissuto con un'esperienza sbagliata: **nessun contatore guarda due flussi
insieme**. Adesso c'è, e non è costato un banco nuovo — è costato **due numeri**:

- `RCP.md` §6.2 e §6.3 mettono **lo stesso orologio del server** nell'intestazione del fotogramma e
  nel datagram audio;
- la pagina pubblica `aoff` (audio) e `voff` (video), presi **allo stesso confine**: `voff` subito
  dopo `transferFromImageBitmap`, cioè **al vetro**, non alla decodifica;
- ⇒ `aoff − voff` è la distanza, **e la costante fra i due orologi si elide**.

`[M]` 90 s, 178 campioni, scena in movimento, 1588×914 H.264, carico 1,09→1,97:

| | min | p05 | **mediana** | p95 | max |
|---|---|---|---|---|---|
| `AV` | 216 | 223 | **236 ms** | 245 | 247 |

⭐ **Offset costante, non deriva**: 233 → 237 → 236 su 90 s. ⭐ E la premessa è stata **verificata,
non creduta**: il marcatore che esce dal decodificatore **è** davvero l'`istante` del server
(escursione 32 ms, deriva −0,02 ms/s).

⚠ **E `AV` sovrastima, dichiarato**: `aoff` comprende `outputLatency` (22-28 ms `[M]`), `voff` non
può comprendere l'equivalente perché fra il trasferimento e il pixel acceso ci sono `[?]` **16-40 ms
che nessuna API espone**. ⇒ La distanza vera è **~200-220 ms**. ⛔ Non è stata sottratta: *sottrarre
una stima è fabbricare una misura*.

⭐⭐ **E il numero dice da sé dove sta**: nello stesso istante la coda audio vale **253 ms** e
`AUDIO_CUSCINO_MS` vale **250**. ⇒ La distanza è **quasi tutta il cuscino più `outputLatency`**, non
un ritardo che si accumula.

⛔ **E non è il numero che l'utente ha provato**: questa è la pagina con l'orologio audio nuovo. I
400 ms erano di prima, e **il confronto lo può fare solo lui**.

> ### ⛔⭐ 22 agosto — **il metro è stato accusato di essere una tautologia, e si è difeso con un numero**
>
> Una revisione avversariale ha mostrato **algebricamente** che in `aoff_ms()` il termine dell'istante
> **si elide**: `aoff = (perf − ora·1000) + base·1000 + u`. Sembrava una costante, e il coordinatore
> aveva **ritirato la misura**.
>
> ⛔ **La conclusione non regge, ed è stata smentita con una misura invece che con un ragionamento.**
> `base` non è arbitraria: al riancoraggio vale `ora + CUSCINO − ist/1e6`, quindi
> `aoff = (perf − ist/1000) + CUSCINO + u` — e **`perf − ist/1000` è la latenza vera del filo**.
> ⭐ `[M]` scena nuova: la latenza del filo cresce di **800 ms** a metà sessione ⇒ **`aoff` passa da
> −750 a 50, salto di 800 esatti**. Il metro vede.
>
> ⚠ **Ma ha una zona morta larga un cuscino, e va sull'etichetta**: un aumento **più piccolo del
> cuscino residuo** non muove `aoff` — ⭐ e non è un difetto del metro: è che **il suono esce davvero
> alla stessa ora**.
>
> ⇒ E *«coda 253, cuscino 250»*: ⛔ **non è una conferma** — è il cuscino letto due volte. Il termine
> che rende `AV` informativo è **`voff`**, che osserva al vetro.
>
> ⭐ **E il rilievo aveva centrato tre difetti veri, tutti curati**: `aoff` si aggiornava sui blocchi
> **programmati** anche se poi tagliati (⇒ ora solo su `onended`, cioè su quel che **si è sentito**);
> **non scadeva** — audio fermo, ultimo valore per sempre, `AV` sano su una sessione muta (⇒ scade
> dopo il tetto della coda e risponde `null`, **senza costanti nuove**); e *«è la gemella esatta di
> `voff`»* era **falso**.
>
> ⏳ Il **236** resta da riprendere con l'`aoff` curato: non è invalidato, è **non riconfermato**.
> ⭐ E si sa una cosa che mancava: `outputLatency` su quel Firefox vale **50 ms**, ed entra in `AV`.

### ⭐ Le regressioni, sul prodotto riunito — porta 7781, utente `provai6`

| banco | esito |
|---|---|
| `07-b51` la tela e il clic, **due motori** | ⭐ **4 controlli su 4 per motore**, e il clic arriva al pixel esatto (scarto 0,0) |
| `07-b54` gli appunti **nei due versi** | ⭐ sessione→client, client→sessione e **la tastiera dopo l'incolla**: verdi su tutt'e due i motori |
| `07-b56` l'incolla **col mouse** | ⭐ **3 su 3 per motore**, e ⭐ **la clipboard del desktop sopravvive al collegamento**. ⚠ Firefox ha chiesto il bottoncino «Incolla» **3 volte su 4**: è il prezzo di §9.5, e questo è il numero |
| `07-b53` la corsa di §7.4 | ⚠ **«la corsa non si è prodotta, questo giro NON prova niente»** — il banco rifiuta di darsi verde, ed è il comportamento giusto |

⇒ ⭐ **Quel che l'utente aveva giudicato il 17 agosto regge** a tutte le modifiche della notte: la
clipboard nei due versi, la tela, il clic.

### ⛔ E un difetto del banco che dava ROSSO AL PRODOTTO — colpa del coordinatore

Rendendo parametrico l'utente dei banchi degli appunti (⛔ entravano come **`prova`**, che è
dell'utente: con la sua sessione viva è la trappola del posto unico) ne ho parametrizzato **un lato
solo** — l'accesso dal browser — lasciando fisso `id -u prova` sul **lato sessione**.

`[M]` Il risultato non è stato un errore del banco: è stato **un verdetto rosso contro il prodotto**
su tutt'e due i motori — *«il desktop remoto ha "Failed to connect to a Wayland server" invece del
testo»* — con `XDG_RUNTIME_DIR` che puntava a `/run/user/1001`, l'utente dell'utente.

⭐ **La lezione**: **un banco parametrico a metà è peggio di uno fisso** — quello fisso almeno si
rifiuta di partire.

## 8-ter · ⛔⛔⭐ 21 agosto 2026, notte — **l'audio non perde per colpa del trasporto: perde per la spirale delle chiavi**

*Nasce dal `[M]` di §8: «il server ha scartato 2 200 datagram, e scrive anche perché». Il mandato
diceva di guardare **come trattiamo i datagram rispetto agli stream**. ⛔ Era l'imputato sbagliato.*

### Le quattro porte da cui un datagram non esce, e quella che morde

| # | dove | chi decide |
|---|---|---|
| 1 | la coda di 8 posti è piena | **noi** — `[M]` non c'entra quasi mai (0-1 blocchi) |
| 2 | un tentativo per passata | **noi** |
| 3 | `writev_datagram` torna 0 | ngtcp2 |
| 4 | **4 096 rimandi di fila → buttato** | **noi** — ⛔ è questa, e accanto c'è sempre `cwnd_left = 0` |

### ⭐⭐ Ma la causa è a monte, e il codice l'aveva già nominata come ipotesi

`[M]` Tre giri, stessa scena, `netem` sulla sola porta del banco, 30 s:

| scena | audio spediti | rifiutati | purezza | banda sul filo |
|---|---|---|---|---|
| **3 Mbit, desktop FERMO** | **6 009** / 6 000 | 3 | ⭐ **1,000** | 1,82 su 3 |
| 3 Mbit, desktop **che si muove** | **397** | 6 061 | ⛔ **0,18** | 3,39 |
| **15 Mbit**, desktop che si muove | 5 997 | 15 | ⭐ **1,000** | 3,08 |

⇒ ⭐ **Stessa banda, stesso audio, esiti opposti: non è la banda, è il video.** E non è nemmeno quanto
costa l'audio: `[M]` con **Opus** — **1/32** del PCM, l'**1,6 %** del collegamento — allo stesso
gradino si perde ancora il **58 %**.

⛔⛔ **La causa è la spirale di §5.2**, e sta scritta come *ipotesi* in `webtransport.c` da prima che
qualcuno la misurasse:

- nei giri stretti il video consegna **solo chiavi** (144/144, 148/148, 107/107, 138/138, 149/149),
  contro **2 su 1 019** a 15 Mbit;
- il registro conta **806 richieste di chiave** e **173 righe** *«la CHIAVE N tiene ancora ~60 000
  byte in coda e §5.2 vieta di abbandonarla: si ASPETTA»*;
- una chiave da 60 KB su 3 Mbit occupa la finestra **160 ms**, e `WT_CHIAVE_RICHIESTA_MS` ne concede
  una **ogni 150** ⇒ ⛔ **se ne chiede una nuova prima che la precedente sia uscita**;
- in quei 160 ms nascono 32 blocchi PCM, e ognuno trova `cwnd_left = 0`.

### ⛔ Perché l'audio perde e il video no — e **nessuno l'ha deciso**

Il video sta su **stream**: se non passa adesso, ngtcp2 lo tiene, lo spezza e lo ritrasmette — può
solo arrivare **tardi**. Il datagram non si spezza, non si ritrasmette, non può aspettare: **ogni
scarsità la paga per intero l'audio**. ⇒ È quel che succede **se non si decide**.

⚠ **E così com'è non è uno scambio, è un incidente**: l'audio chiede l'1,6 % del collegamento e ne
perde il 58 %, mentre il video ne prende il 93 % in chiavi **che si autoalimentano**. Uno scambio
deliberato sarebbe proporzionale; questo distrugge il flusso piccolo a favore di quello che è grande
**perché sta andando male**.

### ⭐ E quattro varianti del trasporto che NON cambiano niente valgono quanto una cura

`[M]` allo stesso gradino: base **397** · senza il ritorno anticipato per passata **278** · senza
`PADDING` **406** · senza `MORE`, in un pacchetto suo **514** · con la **riserva reattiva** (il video
cede la passata) **371**.

⇒ ⭐⭐ **La finestra non è contesa: è già piena.** Rinunciare a scrivere altro video **non libera quel
che è già in volo e non è ancora stato riscontrato**. È la ragione per cui la cura non può stare nel
pacer, e per cui le tre porte «nostre» erano l'imputato sbagliato.

### Le tre forme, e la scelta

| | prezzo |
|---|---|
| 🔸 **A · la chiave non si richiede più in fretta di quanto ci metta a uscire** — `WT_CHIAVE_RICHIESTA_MS` da costante a funzione della banda misurata | ⭐ **l'unica che attacca la causa, e non toglie niente all'audio**. ⚠ Prezzo **visibile**: su linea stretta l'immagine resta rotta più a lungo dopo una perdita |
| **B · riserva di finestra preventiva** (non reattiva, quella è misurata a zero) | cappa il video a `cwnd − pavimento`: < 3 % quando c'è spazio, morde quando è stretta — cioè quando serve. `[?]` **non misurata**: tocca l'ordine di scrittura degli stream |
| **C · l'audio si adatta prima di morire** | ⛔ **da sola non basta, ed è misurato**: 1/32 della banda perde ancora il 58 %. Complemento, non cura |

> 🔸 **Scelta del coordinatore: si scrive A.** Le altre due spostano il conto; A toglie la causa. ⏳ E
> il suo prezzo è **visibile all'utente**, quindi la riga sta scritta perché lo giudichi lui.

### ⭐⭐ La cura A è scritta e misurata — e a 1 Mbit l'audio consegnato fa **×38**

`chiave_intervallo_ms()` in `webtransport.c`, e ⭐ **la banda si misura invece di indovinarla**:
`cwnd / smoothed_rtt`, cioè **i due numeri che ngtcp2 usa lui stesso** per decidere quanto spedire. La
misura dell'ultima chiave è presa **dove è un fatto**, non da una costante. Fondo 150 ms, margine
+20 %, ⛔ tetto **2 s** — *una chiave che non si chiede più è uno schermo fermo, e fermo non è brutto:
è chiuso a metà* (I1).

⭐ **E il ripiego è dichiarato, non silenzioso**: tre casi distinti nel registro (niente connessione ·
nessuna chiave ancora spedita · ngtcp2 senza rtt né finestra). `[M]` A 15 Mbit ha scritto **100 volte
su 101** *«la banda misurata basta: resta il fondo di 150 ms»* — ⭐ **la cura dice da sé quando non
sta lavorando**.

`[M]` Giri **alternati** (con la varianza vista — 397 contro 1 372 fra due giri base identici — due
giri di fila non dimostrano niente), due binari che differiscono per **una riga**, 30 s, PCM:

| scena | attesa | audio **prima** | audio **dopo** | video prima → dopo |
|---|---|---|---|---|
| 3 Mbit, desktop **fermo** *(il controllo)* | 150, inerte | 6 009 | 6 002 | 1 → 1 |
| 15 Mbit, mosso | 150, inerte | 4 076 · 3 944 | 3 984 · 3 830 | 743 → 683 |
| **3 Mbit, mosso** | ~171 | 371 · 462 | ⭐ **1 552 · 1 595 · 1 725** | 115 → 89 |
| **1 Mbit, mosso** | 600-1000 | **15** | ⭐⭐ **577** | 57 → **47** |

⭐ A 3 Mbit l'audio fa **×3,3-×4,2**, e i due gruppi **non si sovrappongono**. A 1 Mbit fa **×38**, e
le richieste di chiave crollano **178 → 68**.

⚠ **E il prezzo è misurato, non dedotto**: a 1 Mbit il video consegna **57 → 47 fotogrammi (−18 %)**,
tutti chiavi ⇒ l'immagine si aggiorna meno spesso. È esattamente *«su linea stretta l'immagine resta
rotta più a lungo»*, in numeri. ⚠ A 15 Mbit la cura è **inerte**: l'−8 % lì è varianza della scena,
non un prezzo.

⛔ **E quel che la cura NON fa, dichiarato**: a 3 Mbit l'audio resta al **27 %** e i fotogrammi sono
ancora **tutti chiavi**. **La spirale non è spenta: è più lenta.**

### ⏳ E il motore vero sta un passo più a monte — `video_sgombra()`

⭐ Trovato **dopo** aver scritto la cura, ed è la ragione per cui la cura aiuta ma non basta:
`video_sgombra()` gira a **ogni** fotogramma e abbandona i delta ancora in coda perché *«ne è partito
uno più recente»* (§5.1). Su linea larga non abbandona quasi mai; **su linea stretta un delta non
esce in 33 ms, quindi viene abbandonato sempre** — e ogni abbandono riaccende il debito di §5.2.
`[M]` Il registro lo dice **28 volte al secondo**.

⇒ ⛔ **Il debito lo riarma l'abbandono, non la richiesta**: limitare le richieste rallenta la spirale,
non la spegne.

⏳ **La cura vera sarebbe lì**: abbandonare un delta solo quando è **davvero senza speranza** (una
soglia sulla coda) invece che a ogni fotogramma più recente — ⭐ **§5.1 lo permette, non lo impone**.
Così sotto congestione il video calerebbe di **ritmo** restando fatto di delta, invece di diventare un
flusso di sole chiavi. ⛔ **Non è stata scritta**: una cura per volta, e questa tocca §5.1 — è una
**decisione di prodotto**. Il ragionamento e i numeri stanno accanto a `video_sgombra()` perché non
si perdano.

### ⛔ E un difetto di banco che aveva spostato la diagnosi a monte

`[M]` La riga *«vuole una CHIAVE»* compare in **due messaggi diversi**: la **richiesta** che parte da
`video_regola()` e il **rifiuto** che scrive `rcp.c`. Le «806 richieste di chiave» del primo rapporto
erano in gran parte **rifiuti**: contate a parte, nello stesso giro, sono **105 richieste contro 346
rifiuti**. ⇒ **Due righe che si somigliano vanno contate separate, o la diagnosi punta dove il
difetto non è.**

⏳ `[?]` **E resta una cosa non misurata**: la spirale è provata col **cliente di prova**, non contro
un browser vero. Quella prova la fa il coordinatore sul prodotto riunito.

## 8-quater · ⛔⛔ 22 agosto 2026 — **il ritardo tornava da solo**, e «il suono parte al primo clic» era una promessa vuota

### ⛔⛔ Il difetto nuovo: la coda si gonfia a metà sessione, e resta gonfia

`[M]` Giro di **cinque minuti sul ferro**, carico 2,25: la coda è saltata da **266 a 519 ms in una
finestra sola** (`BUCHI 1`, `mancati 4`) e **lì è rimasta** per il resto della sessione.

**Il meccanismo**, e non è la deriva: quando il thread principale si ferma un attimo, i datagram si
accumulano nel lettore e **arrivano tutti insieme**. Il primo del mucchio è vecchio ⇒ riarmo, e
l'ancora si aggancia **a lui**; ⛔ ma dietro ce ne sono altri dodici, ognuno col suo posto 20 ms più
in là ⇒ **il mucchio finisce nel futuro e il cuscino si gonfia di quanto era lungo il mucchio**.
`250 + 13×20 = 510`. ⚠ È **la raffica dell'attacco rifatta a metà sessione**, dove la tirata
dell'ancora era già chiusa.

⭐ **La cura è una riga**: la finestra della tirata si riapre a ogni **riancoraggio** — ⛔ non a ogni
blocco, che era il difetto muto del 21 agosto (`tirate 4506 su 4508`, silenzio con tutti i contatori
verdi). Nelle sessioni sane si riapre **zero volte**.

| stessi 5 minuti, carico 2,25 | prima | dopo |
|---|---|---|
| coda | 266 → **519**, poi 585 | ⭐ **269-289, ferma** |
| BUCHI | 1 | ⭐ **0** |
| perdite | `mancati 4` → scatto e gonfiore | `mancati 7` → ⭐ **niente**, né scatto né gonfiore |

### ⛔⛔ E il banco aveva dato **46 su 46** al codice che portava ancora il difetto

La scena dello stallo era scritta con un mucchio di **20 blocchi**: `250 + 400 = 650 ms`, cioè
**oltre il tetto dei 600**, e il **traboccamento rimetteva a posto da sé**. ⇒ Il banco assolveva. Con
**13 blocchi** (510 ms, **sotto** il tetto) il guasto si vede.

⭐⭐ **Ed è la ragione per cui il difetto era invisibile: la rete di sicurezza esisteva e ci passava
sopra.** ⚠ Una scena scelta *oltre* il limite di guardia prova il limite di guardia, non il difetto —
ed è una forma nuova, cugina di `LEZIONI.md` §1.20.

### ⭐ «Il suono parte al primo clic sulla pagina» — era una promessa vuota

*La pagina lo scriveva all'utente; nel file c'era **un solo `resume()`**, alla nascita del contesto.*

`[M]` `banchi/07-b62-il-primo-clic.py`, **Firefox con schermo** (non headless), carico 1,44 — ⭐ e il
controllo positivo **è la pagina di ieri**, non un guasto sintetico:

| | pagina di prima | pagina curata |
|---|---|---|
| come nasce | `suspended` | `suspended` |
| dopo 25 s senza toccare | `suspended`, **usciti 0** | `suspended`, **usciti 0** |
| **dopo un clic vero** | ⛔ **`suspended`, usciti 0** | ⭐ **`running`, usciti 388**, coda 259 ms |

⛔ **La risposta era la peggiore delle due**: non solo mancava il gestore, ma **non si svegliava da sé
nemmeno su un browser con schermo**. ⇒ Curato con quattro eventi in `passive` + cattura (non
intercettano niente: il clic arriva al desktop come prima), che si tolgono da soli al risveglio, più
un `resume()` riprovato ogni 5 s di blocchi buttati.

### ⭐ E la deriva fra gli orologi: **il numero era mio ed era sbagliato**

⛔ I **0,7-1,4 ms/s** dichiarati in §8 erano **in gran parte il difetto qui sopra letto come deriva**.
Tolto quello, su cinque minuti puliti: **~0,07 ms/s** (±0,05). ⇒ Dal cuscino al tetto dei 600
ci vorrebbero **~80 minuti**, non quattro.

⏳ **La forma della cura c'è, e la raccomandazione è di non scriverla adesso.** L'unica correzione
*continua* è rendere l'ancora affine (`quando = base + istante/r`, ogni blocco a `playbackRate = r`):
prezzo, uno scostamento d'intonazione **costante** ≤ 0,15 % = **2,6 cent**, sotto la soglia
percettiva. ⛔ Le alternative sono peggiori, **e sono state scartate con un numero**: far scorrere
l'ancora a passetti dà ~1,4 campioni di gradino per blocco = **un ronzio a 50 Hz**; inserire o
togliere un blocco = **un tic**. ⚠ Ma a 0,07 ms/s **non vale il rischio dello stimatore**: resta
aperta, e si rimisura su una sessione vera dell'utente, dove le due schede audio sono altre.

### ⛔ E la finestra di riordino è USCITA — appartiene alla fase 9

Era scritta e certificata (`vecchi 0 / riord 400` contro `vecchi 400` con la regola vecchia), ⛔ ma
l'utente ha corretto lo scopo: *«i problemi di rete non rientrano in questa fase»*. ⇒ Tolta dal
prodotto **invece di lasciarla dentro spenta**, e il lavoro è descritto in `PIANO.md` fase 9.

## 8-quinquies · ⛔⭐ 22 agosto — **il giudice dell'orecchio dava il voto massimo al silenzio**, e c'era un buco cieco esatto

*Rilievo della revisione, confermato **riproducendolo** invece che leggendolo.*

`[M]` `picco = max(abs(x)…) or 1.0` ⇒ a campioni **tutti zero** il picco diventa 1.0, la soglia si
abbassa con lui, i residui sono 0 ⇒ **`scoppiettii 0`, `resa 1,000`**: il giudice dell'audio **dà il
massimo al silenzio**. Quattro secondi di zeri, verificati.

⛔⛔ **E il buco cieco è aritmetico, non statistico**: il blocco PCM è 240 campioni = 5,0 ms, quindi
**5 blocchi = 1 200 campioni = esattamente 11,000 cicli di 440 Hz**. `[M]` tagli di **1 200 e 2 400
campioni** ⇒ `scoppiettii 0`; tagli di 240 e **1 201** ⇒ si vedono. ⇒ Una perdita a raffiche di
cinque blocchi **si ricuce continua e in fase**, e nessun algoritmo può sentirla.

⭐ **La cura ha due gambe, e la seconda è la parte che conta**: il silenzio non prende più il massimo
(sotto un picco di 400 il giudice risponde **`SILENZIO O QUASI — NON GIUDICO`**, che è un esito suo);
e ⭐ **il buco cieco si cura contando, non ascoltando** — il giudice riceve ora i campioni **attesi** e
riporta l'ammanco, *«perché su un seno perfetto un taglio di 11 cicli non lascia traccia nei campioni
e nessun algoritmo può vederlo»*.

⭐ Certificazione da 4 a **7 casi**, e un ottavo chiude la diagnosi: **lo stesso taglio a 443 Hz si
vede** (11,075 cicli) ⇒ **il buco è del tono, non del rivelatore**. ⏳ Proposto 443 Hz per le scene
future — non cambiato oggi, perché renderebbe incomparabili i numeri di ieri.

#### ⭐⭐ E la domanda che conta: **quante misure ne erano affette?**

Rigiudicate **tutte le 31 prese conservate** col giudice curato:

- ⛔ **sei cambiano esito**, tutte del primo giro con la rete guastata: adesso dicono *«silenzio o
  quasi — non giudico»* dove dicevano `scoppiettii 0`. ⚠ **R7a stava mordendo per davvero in una
  misura nostra** — erano già state annullate e rifatte, ma **leggendole a occhio**; adesso è il
  giudice a **rifiutarsi da solo**;
- ⭐⭐ **nessun numero riportato cambia**: l'A/B di R26 è identico riga per riga, e la seconda gamba
  conferma che **non c'erano perdite a raffica nascoste** (`campioni_mancanti` 0 o 240 in tutte le
  prese). Reggono anche la tabella della rete e i numeri della spirale.

#### ⛔ E il sorvegliante stampava «acceso» senza aver acceso niente

*(Il difetto era del coordinatore, che aveva scritto quel file; la cura è dell'agente.)* `& echo
acceso` riesce **sempre**, il registro d'avvio **non lo leggeva nessuno**, e il file di sorveglianza
era un percorso **fisso**. ⇒ Il sorvegliante non parte, l'utente fa la sessione, e si legge **la
sorveglianza di ieri**.
⭐ Curato con quattro gambe — si uccide il precedente, il file porta **l'ora nel nome**, si verifica
che il processo sia vivo **e che il file cresca** — e provato **nei due versi**: *«NON È PARTITA, e
non lo dico da una parola stampata, lo dico da tre fatti»*, uscita 2.
⚠ E la cura ne ha scoperto un secondo dentro di sé: `pgrep -f <copione>` trovava il sorvegliante di
**un giro precedente** ⇒ *«è vivo?»* rispondeva sì **guardando il processo sbagliato**. L'ha visto
solo l'altra gamba, il file che non cresceva.

## 9 · Il giudizio dell'utente

### 9.8 · ⭐⭐⭐ **«Le quattro prove che ho eseguito davano un audio OK»** — 22 agosto 2026

> *«Le 4 prove che ho eseguito prima davano un audio OK. L'unico piccolo appunto è
> un'ottimizzazione sulle performance grafiche, che credo sia lo scopo della fase 8.»* — l'utente.

⭐ **Le quattro prove sono i quattro motori dichiarati la stessa mattina** (`DECISIONI.md` §7.20):
Linux Chrome, Linux Firefox, Windows Chrome, Android Chrome. ⇒ Non è un giudizio su una
piattaforma: è **su tutte quelle che il prodotto dichiara di servire**.

⭐⭐ **E con questo l'audio della fase 7 ha il giudizio che le mancava.** Il metro è sempre stato
**I8** — quel che l'utente sente — e adesso quel metro ha parlato su quattro motori invece che su
uno.

⭐⭐ **E il ritardo fra audio e video È CHIUSO** — chiesto e confermato: *«ho già scritto prima che il
ritardo audio/video è ok»*. ⇒ Il *«audio OK»* delle quattro prove comprendeva **la sincronia**, non
solo la pulizia del flusso.

⛔ **Era l'ultimo difetto vero della fase 7**, ed è quello che l'utente aveva confermato il 21 sera
con *«il ritardo di 400 ms tra audio e video in generale te lo confermo»*. ⇒ Fra le due frasi ci
sono: l'**ancora all'`istante` del server** (la coda non è più un serbatoio a senso unico), la
**riapertura della tirata a ogni riancoraggio** (la coda non si gonfia più a metà sessione), la cura
della **spirale delle chiavi** (l'audio non muore più quando la linea stringe) e il **primo clic**
che adesso accende davvero il suono.

⚠ **E la misura `AV` resta da riprendere lo stesso** (§8-bis, con l'`aoff` curato): non serve più a
decidere se il difetto c'è — quello l'ha deciso l'orecchio — ⭐ serve a **accorgersi se un giorno
torna**, che è un mestiere diverso e altrettanto utile.

⇒ ⭐ **E l'unico appunto che resta è di un'altra fase**: le prestazioni grafiche, che sono la
**fase 8** — e l'utente l'ha indirizzata da sé.



*La fase si chiude su una misura giudicata dall'utente, non su un documento completo.
⛔ Non si scrive un verdetto che l'utente non ha dato.*

### 9.1 · ⭐⭐⭐ L'AUDIO: **«problema audio risolto»** — 17 agosto 2026

Dato su un **video di YouTube** riprodotto nella sessione remota, e confermato dai contatori:

| | |
|---|---|
| blocchi ricevuti dalla pagina | 2184 → 3183 in 20 s = **49,95/s** contro 50 prodotti |
| perdita | **zero** |
| **buchi nella riproduzione** | **2**, e fermi — nessun nuovo buco in venti secondi |
| coda | stabile a **311-341 ms** |

### 9.2-bis · ⭐⭐⭐ GLI APPUNTI: **«clipboard funziona in entrambi i versi»** — 17 agosto 2026

*Dato dall'utente col browser, sulla porta 7730, sessione dell'utente `prova`.*

⛔ **È il metro I8, e non lo sostituisce niente**: nessun banco automatico ha mai visto passare un
byte di appunti — l'arbitro esterno che §2.4 prometteva **non esiste** (§6.9), e quel verdetto è
l'unica prova che questa metà della fase abbia.

⭐ **E copre tutt'e due i versi**, cioè anche quello che `DECISIONI.md` §5-ter.1 dichiara il più
usato: *«copio un indirizzo sul telefono e lo incollo nel browser remoto»*.

⭐ **E con lui passa, di striscio, la cura della corsa con `Ctrl+V`** (§4.5.2): il verso
`dispositivo → sessione` **è** quella corsa: l'annuncio e i tasti partono insieme, e se la cura non
avesse funzionato la prima incollata sarebbe tornata vuota.

> ⚠ **Quel che il verdetto NON dice**, e va scritto perché non venga letto per più di quel che è:
>
> - **su quale browser**: la riga del registro della pagina — quella che dice se `clipboardchange`
>   c'è e **dove sta** — non è stata riportata. ⇒ Resta `[?]` se il verso
>   `dispositivo → sessione` abbia funzionato per **sorveglianza** (Chrome) o per **`Ctrl+V` sulla
>   pagina** (Firefox e Safari). Sono due strade diverse (§4.5, `pagina.html`), e sapere quale ha
>   retto cambia che cosa si dichiara all'utente in §9 di `SPECIFICHE.md`;
> - **niente numeri**: nessuna misura di quanto testo, di quanto tempo, né del secondo giro quando
>   il browser nega la scrittura negli appunti;
> - **il DeX e il telefono** restano `[?]`, come per l'audio.

⇒ **La fase 7 ha adesso i suoi due giudizi**: *«problema audio risolto»* e *«clipboard funziona in
entrambi i versi»*. ⛔ E la **fase 6 resta aperta**: il suo §8 aspetta ancora il giudizio su due
scene (il trascinamento del bordo e il clic tenuto giù), e quel che resta della 6 **non si chiude da
sé**.

### 9.2 · ⛔⛔ E PRIMA DEL «RISOLTO» CI SONO STATI SETTE «FA SCHIFO»

*Va scritto, perché è la parte che insegna.* Il banco `07-b43` era **verde su cinque giri su
cinque** — 440 Hz esatti, ampiezza esatta, volume che governa — e l'utente sentiva
*«jitter pazzesco»*. ⇒ **I8 non è una formalità**: il metro è quel che l'utente sente, e cinque
verdi non lo sostituiscono.

⭐ **E tre passi avanti su quattro li ha fatti lui, non io:**

1. *«forse il datagram è troppo piccolo?»* → il manuale di ngtcp2 dà ragione all'intuizione in una
   riga: un lotto GSO si scrive **solo se il primo pacchetto è di misura piena**;
2. *«nella cartella REMOTIX l'audio funzionava, esaminala»* → **R26**, la priorità di tempo reale
   negata dall'unità, misurata il 5 agosto 2026 e da me riscritta come `[?]` senza mai farla;
3. *«riproduci un video e monitora byte per byte»* → è il giro che ha prodotto **il numero
   esatto**, e da lì la diagnosi ha smesso di essere una serie di ipotesi.

---

### 9.3 · ⛔⛔⭐ «SI È BLOCCATO FIREFOX CON LA CLIPBOARD» — e non era Firefox

*20 agosto 2026, difetto riferito dall'utente mentre provava i due browser. ⚠ Non era un blocco del
browser: era **la nostra pagina** che mandava `ERRORE_PROTOCOLLO` e chiudeva la sessione — e da
fuori si vede come un'immagine che si ferma.*

**`[M]` Il registro del server, 19:04:06, e la catena sta in quattro righe:**

```
19:04:06.560  annunciato al client il trasferimento 3 — 1155 byte
19:04:06.560  annunciato al client il trasferimento 4 — 1155 byte   ← stesso millisecondo
19:04:06.569  il client chiede il 3, superato dal 4: lo servo col testo ATTUALE
19:04:06.612  il client si congeda, motivo=0x0b — «i messaggi di trasferimenti
              diversi non si mescolano (§7.4)»
```

⇒ ⭐ **Il server aveva ragione e la pagina torto**, e l'arbitro è scritto: `RCP.md` §7.4 dice
*«un `APPUNTI_CHIEDI` che arriva quando l'annuncio è già stato superato si serve **con il testo
attuale** … è la corsa normale fra due che copiano, **non un errore**»* — la **quinta eccezione
dichiarata a §3**. La pagina applicava la regola generale e ignorava l'eccezione.

⛔⛔ **E lo stesso sbaglio era scritto nei DUE capi**: `rcp.c` chiudeva la sessione nel caso
speculare (il client che serve una richiesta superata). ⚠ La pagina, invece, applicava l'eccezione
**correttamente** quando era lei a *servire*: la stessa regola scritta due volte, e la seconda
diversa — è la forma **E2** dentro un solo file.

**La cura, ai due capi**: l'errore è un testo **che nessuno ha mai chiesto**, non un testo con un
numero vecchio. ⇒ Si confronta con **quel che si è chiesto** (`APPUNTI.chiesti` nella pagina,
`app_chiesto_id` nel server), e la lunghezza si pretende **solo** sul trasferimento vivo — su uno
superato il testo servito è quello di *adesso*.

#### ⭐⭐ E il banco ne ha trovati altri DUE, tutti e due miei, dopo la cura

*È il valore di `banchi/07-b53-appunti-corsa.py`, ed è il motivo per cui esiste.*

| | il difetto | come si presentava |
|---|---|---|
| 1 | **cancellavo il ricordo al primo uso** | una seconda risposta per lo stesso trasferimento — legittima — trovava il ricordo vuoto e chiudeva la sessione. ⇒ La domanda giusta è *«l'ho MAI chiesto?»*, non *«ne ho una in volo?»* |
| 2 | ⛔ **segnavo la richiesta DOPO l'`await`** | e la risposta può arrivare prima che l'attesa si sciolga: ⭐ **verde su Firefox, rosso su Chrome**, per un decimo di millisecondo. ⇒ Il fatto si segna **prima** di consegnare, e si segna l'identificatore che si è messo nel messaggio — non quello riletto dopo |

⛔ **Il secondo è la ragione per cui un banco solo non basta**: la stessa cura, sullo stesso
prodotto, nello stesso minuto, **passava su un motore e falliva sull'altro**.

#### ⚙ Il banco, e perché riproduce uno STATO invece di una coincidenza

⚠ `[M]` La finestra vera dura quanto la lettura della clipboard dalla sessione: **sotto il
millisecondo** su rete locale. Sei copie a raffica dentro la sessione (`wl-copy`, 15 ms l'una
dall'altra) **non l'hanno aperta nemmeno una volta**. ⇒ Il banco mette la pagina **esattamente
nello stato** che ha chiuso la sessione dell'utente: chiede un trasferimento e fa arrivare — prima
della risposta — un annuncio più nuovo. ⛔ È bianco, tocca `REMOTIX.appunti`, **e lo dichiara**:
quel che verifica è la **regola**, non il tempismo.

⭐ **E si certifica**: rimessa la riga vecchia, `[M]` il banco vede la sessione chiudersi con
`motivo=0x0b` — la stessa faccia del difetto dell'utente. Rimessa la cura, **4 giri su 4 verdi,
Firefox e Chrome**.

⛔ **E un difetto che ho fatto mentre curavo**, perché è la parte che insegna: per esporre lo stato
al banco avevo agganciato `APPUNTI` al riquadro `window.REMOTIX`, che gira **molto prima** della sua
dichiarazione — leggere un `const` nella sua zona morta ferma **tutto il resto dello script**.
⚠ Il sintomo non nominava niente di tutto questo: il modulo d'accesso perdeva il suo gestore e la
pagina finiva in `GET /?utente=…&parola=…`, cioè **la parola d'ordine nella barra dell'indirizzo**.
Un difetto di ordine di dichiarazione diventato, per due minuti, un difetto di privatezza.

---

### 9.4 · ⛔⛔⭐ «DA SERVER A CLIENT FUNZIONA, IL CONTRARIO NO» — su Firefox, e le cause erano TRE

*20 agosto 2026, riferito dall'utente. ⚠ E il verso che non funzionava è quello che nessun banco
aveva mai provato **con i tasti veri su un browser vero**: `07-b45` misurava il protocollo, non il
percorso del browser.*

#### La riproduzione, ed è la parte che decide

⛔ **In headless il difetto NON si vede**: l'evento `paste` arriva lo stesso. Neanche su X11 (Xvfb).
⭐ Si vede in **un compositore Wayland annidato** (`cage`), con il testo copiato da **un'altra
applicazione** — cioè l'ambiente dell'utente. `[M]` Il diario della pagina, tre righe:

```
appunti · Ctrl+V visto · sorveglianza=«nessuna»
appunti · evento `paste` arrivato · 0 caratteri          ← VUOTO
appunti · l'evento `paste` è arrivato: strada gratis, nessun permesso
```

e `annunciati: 0`: **non è mai partito niente**.

#### Le tre cause, e sono tutte nostre

| | la causa | perché mordeva |
|---|---|---|
| 1 | ⛔ **un `paste` vuoto contava come consegna** | `ultimo_paste_ms` si segnava **prima** di guardare se ci fosse del testo ⇒ il ripiego `readText()` veniva spento («strada gratis») e non si provava più niente |
| 2 | ⛔ **non c'era niente di modificabile a fuoco** | e l'evento `paste` nasce solo lì. ⚠ Il commento di §9 diceva *«la cura ovvia non si può fare»* perché un `TEXTAREA` a fuoco spegne la tastiera (`cl_nel_modulo`) — ⭐ **era falso**: bastava **nominare l'eccezione** invece di rinunciare |
| 3 | ⛔ **il testo «in attesa di gesto» rubava gli appunti** | il testo venuto dal desktop remoto aspettava un gesto per entrare negli appunti locali, e il gesto poteva essere **il `Ctrl+V` dell'utente** — cioè gli si scriveva sopra la copia proprio mentre la incollava. `[M]` Il banco l'ha visto: il desktop remoto riceveva **indietro il proprio testo** |

#### Le cure, e sono quattro

⭐ **Il campo nascosto** (`incolla_campo_prendi`): prende il fuoco **solo per i 400 ms del `Ctrl+V`**,
l'incolla del browser ha dove andare, l'evento `paste` nasce col testo dentro, e **non si chiede
nessun permesso**. ⛔ E `cl_nel_modulo()` lo esenta per nome: i tasti continuano ad andare al
desktop remoto — il banco lo verifica battendo una lettera **dopo** ogni incolla.

⭐ **La seconda strada**: dopo 120 ms si legge **quel che il browser ha davvero incollato nel
campo**. Non dipende da `clipboardData`, che può arrivare vuoto. `[M]` Su X11 è la strada che ha
consegnato: *«il campo dell'incolla porta 45 caratteri»*.

⭐ **Un `paste` vuoto non conta**, quindi il ripiego `readText()` resta disponibile.

⭐ **E il testo in attesa non si scrive mai su un gesto della clipboard** (`Ctrl+V`, `Ctrl+C`,
`Ctrl+X`), ⛔ e **si butta** se l'utente copia qualcosa di suo: *«i suoi appunti valgono di più»*.

⛔ **E il silenzio si rompe**: se `readText()` non risponde entro 1,5 s — su Wayland Firefox apre il
suo bottoncino «Incolla» e **aspetta**, senza risolvere né fallire — la pagina lo **dice** all'utente
invece di lasciarlo davanti a una cosa che «non funziona».

#### ⚙ Il banco — `banchi/07-b54-appunti-due-versi.py`, e misura QUATTRO caselle

*sessione→client e client→sessione, per Firefox e per Chrome, ⭐ più una quinta: **la tastiera è
ancora viva dopo l'incolla?*** — perché una cura che aggiusta gli appunti e spegne i tasti sarebbe
un pessimo affare.

⛔ **E non usa nessun permesso speciale**: le preferenze di prova di Firefox
(`dom.events.testing.asyncClipboard`) spegnerebbero proprio il difetto che si cerca. La clipboard si
riempie con un `Ctrl+C` **vero** e si legge con un `Ctrl+V` **vero**. ⚠ E il gesto che sblocca la
scrittura dev'essere un **clic del guidatore**: un evento fabbricato in JavaScript non è
un'«attivazione dell'utente», e il browser rifiuta lo stesso.

**`[M]` L'esito, 20 agosto 2026 — quattro ambienti:**

| ambiente | firefox | chrome |
|---|---|---|
| headless | ⭐ ⭐ ⭐ | ⭐ ⭐ ⭐ |
| X11 (Xvfb, browser veri) | ⭐ ⭐ ⭐ | ⭐ ⭐ ⭐ |
| Wayland (`cage` annidato) | ⭐ ⭐ ⭐ | *(non provato)* |
| copia da **un'altra applicazione** → incolla nel prodotto (X11) | ⭐ | — |

⚠ **E quel che NON si è potuto provare, dichiarato**: il caso «Wayland **+** clipboard di un'altra
applicazione **+** tasti sintetici» resta rosso, e ⛔ **non è il prodotto**: Wayland consegna gli
appunti solo a fronte di un evento d'input **vero** (serve il *serial* del compositore), che un tasto
finto non ha. ⇒ Su quel percorso l'ultima parola è di una tastiera vera — cioè dell'utente.

---

### 9.5 · ⛔⛔⭐ «FUNZIONA CON `Ctrl+V`, MA NON COL MOUSE» — 21 agosto 2026, e gli anelli rotti erano **quattro**

> *«Ecco perche'! Funziona l'incolla con ctrl+v, ma non con il mouse e scegliendo dal menu la voce
> "incolla"»* — l'utente, la mattina del 21 agosto, subito dopo aver verificato la cura di §9.4.

⭐ **Una frase che vale una giornata di diagnosi**: dice che la cura del giorno prima è entrata (il
`Ctrl+V` consegna) e nomina esattamente la strada rimasta scoperta.

#### La differenza, e perché nessuno dei quattro banchi verdi poteva vederla

| l'utente fa | chi tocca | che cosa nasce sulla pagina |
|---|---|---|
| `Ctrl+V` sulla pagina | **il browser** | l'evento `paste`, con dentro il testo — gratis |
| tasto destro → «Incolla» **dentro il desktop remoto** | **il desktop remoto** | ⛔ **niente** |

⇒ Quel menu è dipinto nel video, e la voce «Incolla» la esegue un'applicazione che sta dall'altra
parte del filo. L'unica notizia che ne arriva alla pagina è l'`APPUNTI_CHIEDI` del server.
⛔ **E i quattro banchi verdi di §9.4 battevano tutti `Ctrl+V`**: misuravano l'unica strada che già
funzionava. Il banco che mancava è `banchi/07-b56-incolla-col-mouse.py`, che non batte mai un tasto.

#### I quattro anelli, in ordine di scoperta — e **tre erano miei**

**1 · La pagina non veniva nemmeno interpellata.** `rcp.c` non chiede niente a un client che non ha
mai annunciato: mette la richiesta in coda («*la domanda ASPETTA l'annuncio*») e il fondo del figlio
la chiude a mani vuote dopo quattro secondi. ⇒ Finché l'utente non aveva battuto **almeno un**
`Ctrl+V`, un incolla col mouse non arrivava a fare **nemmeno una domanda**: nessuna riga, da nessuna
parte.
⭐ **Cura**: la pagina manda un **annuncio d'apertura da zero byte** appena la sessione è nata.
Costa otto byte una volta, apre il canale della domanda, e dice il vero — in quell'istante di
appunti letti non ne ha.

**2 · ⛔ E quell'annuncio partiva TROPPO PRESTO, e chiudeva la sessione.** `[M]` Registro delle
05:55:42: *«congedo motivo=0x0b — byte sullo stream di appunti (14) prima che `SESSIONE` sia partita
(stato: attesa-verdetto)»*. `avvia_appunti()` gira all'ECCOMI, cioè **prima delle credenziali**.
⇒ L'annuncio d'apertura è stato spostato dopo `SESSIONE` (`appunti_apri_la_domanda`).

**3 · ⛔ L'offerta alla sessione cadeva nel vuoto, e nessuno la rifaceva.** `[M]` 06:00:15 —
l'annuncio alle `.868`, l'apertura degli appunti della sessione alle `.982`: **114 ms** in mezzo, e
in quei 114 ms il figlio scriveva *«gli appunti della sessione non ci sono: l'offerta cade»*.
⇒ Il compositore non diventava mai proprietario della selezione, e dentro il desktop la voce
«Incolla» **non aveva niente da dare**.
⭐ **Cura**: `figlio.c` tiene **un bit** (`appunti_offerta_arretrata`) e rifà l'offerta appena gli
appunti si aprono. È la stessa forma della domanda arretrata di `rcp.c`: invece di ritardare
qualcosa per tutti, si ricuce.

**4 · ⛔⛔ E l'annuncio nuovo UCCIDEVA l'incollata che lo aveva provocato.** Il difetto l'ha detto
Mutter con parole sue: `[M]` *«SelectionWrite per la richiesta 2 è stata rifiutata — Transfer serial
2 doesn't match any transfer request»*.
⚠ Offrire la selezione al compositore (`SetSelection`) **annulla i trasferimenti in volo**: è il
compositore che, vedendo una selezione nuova, butta le richieste aperte sulla vecchia. E noi
ri-offrivamo *proprio mentre servivamo* — la pagina rilegge la clipboard, annuncia il testo nuovo, e
quell'annuncio buttava l'incollata in corso. ⇒ **Chi incollava vedeva vuoto**, che è il sintomo da
cui eravamo partiti.
⭐ **Cura**: finché ci sono richieste in attesa l'offerta si **rimanda** (`app_offri_dopo`), e parte
quando la risposta è partita.

#### E la cura che sta al centro: **si rilegge quando il desktop chiede**

`appunti_rileggi_prima_di_servire()` — sull'`APPUNTI_CHIEDI`, prima di servire, la pagina rilegge la
clipboard del dispositivo. ⭐ Il permesso c'è: **il clic sulla voce «Incolla» del menu remoto è un
clic su questa pagina**, quindi l'attivazione transitoria è fresca di millisecondi.

⛔ **E non si rilegge se la strada gratis ha appena consegnato** (`paste` da meno di 4 000 ms):
senza questa riga si curava l'incolla col mouse **rompendo quello con la tastiera**, perché su
Firefox ogni rilettura costa il bottoncino «Incolla».

#### Il prezzo, misurato — `banchi/07-b56`, 3 incollate per browser

| | Chrome | Firefox |
|---|---|---|
| l'incolla col mouse arriva | ⭐ **3 su 3** | ⭐ **3 su 3** |
| il bottoncino «Incolla» compare | **mai** | ⚠ **3 volte su 3** |
| incollando lo **stesso** testo una seconda volta | — | ⚠ compare **di nuovo** |

⚠ **Su Firefox l'incolla col mouse costa un clic in più, ogni volta.** Non è una scelta nostra:
`readText()` lì apre sempre il bottoncino di conferma, anche a clipboard immutata (`SPECIFICHE.md`
§9 — «*ogni lettura costa il menu Incolla*»). ⭐ Ma stavolta compare **dove l'utente sta già
cliccando**, non in un angolo che nessuno guarda. E il `Ctrl+V` resta gratis su tutti e due i
motori.

#### ⛔ Tre difetti del banco, e due avrebbero dichiarato rotto un prodotto sano

1. **Chrome non andava sullo schermo del banco.** Senza `--ozone-platform=x11` prende Ozone/Wayland
   e si attacca alla sessione grafica **vera**: leggeva un'**altra** clipboard, e `readText()`
   tornava vuoto mentre `xclip -o` sullo schermo del banco mostrava il testo.
2. **Il banco cliccava troppo presto.** Fra il clic e `wl-paste` ci sono `ssh`, `sudo` e `runuser`:
   `[M]` secondi interi, e l'attivazione transitoria dura cinque secondi. ⇒ *«lack of user
   activation»* era il banco, non il prodotto. Cura: il copione remoto dice **`PRONTO`** e aspetta
   un secondo e mezzo, così l'ordine dei fatti è quello vero.
3. **`xclip` appendeva il banco**, come `wl-copy` nella sessione: si biforca per *servire* la
   selezione e tiene aperte le sue uscite. ⇒ Non si aspetta.

⭐ E per cliccare il bottoncino di Firefox il banco entra nel **contesto chrome**
(`clipboardReadPasteMenuPopup`), con `-remote-allow-system-access`: ⛔ **non** si accende
`dom.events.testing.asyncClipboard`, che spegnerebbe proprio la cosa da misurare. Il banco paga il
prezzo davanti a tutti e **riferisce quante volte**.

### 9.6 · ⛔⛔⭐ «COME UNA SESSIONE LOCALE» — la direttiva, e il difetto che ha fatto emergere

> *«L'esperienza dell'utente con REMOTIX dev'essere quanto più vicina possibile all'esperienza con
> una sessione grafica locale. […] niente trucchi, pulsanti strani o soluzioni tecniche che si
> allontanino da questa direttiva»* — l'utente, 21 agosto 2026. `DECISIONI.md` §5-ter.8.

⭐ Verificando la cura di §9.5 alla luce di quella frase è saltata fuori una domanda che nessun banco
aveva mai fatto: **se nel desktop avevo già copiato qualcosa e poi mi collego, quel testo c'è
ancora?**

⛔ `[M]` **No, e la colpa era della cura del mattino.** `wl-paste` dentro la sessione diceva
`TESTO-CHE-ERA-GIA-NEL-DESKTOP` prima del collegamento e **`«»`** dopo.

⇒ La catena: per farsi trovare quando qualcuno incolla col mouse, la pagina si annuncia appena entra
— e annunciarsi vuol dire **prendersi la selezione**, che è una sola. Prendendola a mani vuote si
cancellava quel che l'utente aveva copiato di là. ⛔ È esattamente il contrario di una sessione
locale, dove la clipboard non sparisce perché è entrato qualcuno.

#### E la diagnosi ha corretto una riga di codice che affermava il falso

`appunti.c` diceva che `EnableClipboard` con opzioni vuote fa arrivare un `SelectionOwnerChanged`
**subito**, *«ed è proprio l'annuncio che fa ritrovare gli appunti a chi si ricollega»*.
⛔ **Falso, misurato**: `wl-copy` vivo e proprietario, `wl-paste` che rilegge il suo testo prima e
dopo, e nel registro del figlio **nessuna riga di lettura**. Mutter racconta i **cambi** di
proprietario, non chi lo è già. ⇒ La clipboard che c'è si **chiede** (`appunti_leggi_adesso()`), e
si richiede **a ogni riattacco** — il figlio sopravvive fra un collegamento e l'altro, quindi la
lettura fatta all'accensione vale una volta sola (`MSG_RIMANDA_PALCO`, che vuol dire esattamente
«un client si è riattaccato»).

#### La cura definitiva sta dove il testo c'è davvero

⭐ **Se il client non ha appunti da dare, il figlio rende alla sessione l'ultimo testo che la
sessione stessa gli aveva dato** (`appunti_rispondi`). La selezione cambia di mano, **il contenuto
no**. ⇒ Chi si collega non perde niente, e la strada dell'incolla col mouse resta aperta.

⚠ **E due cure intermedie sono state buttate, con la loro ragione**:

| cura provata | perché è caduta |
|---|---|
| «un annuncio vuoto non porta via la selezione a chi ha qualcosa» (in `rcp.c`) | proteggeva la clipboard **chiudendo la strada del mouse**: senza la selezione, il desktop non ci chiede niente |
| «il primo testo della sessione si impara ma non si scrive negli appunti del dispositivo» (nella pagina) | non sapeva distinguere *lo stato iniziale* dalla *prima copia fatta nella sessione*, e ha mandato rosso il verso sessione → client su tutti e due i motori (`07-b54`) |

⇒ ⭐ La lezione, ed è la stessa di sempre: **la cura va messa dove l'informazione c'è**. Né la pagina
né il protocollo sanno che cosa contiene la clipboard del desktop; il figlio sì.

#### ⛔ E tre altri difetti del banco, tutti che dichiaravano rotto un prodotto sano

1. **`wl-copy` ucciso dal `timeout` del banco**: si biforca per *servire* la selezione, e il
   `timeout 12` che avvolge il copione se lo portava via insieme al gruppo. ⇒ `setsid`, e la copia
   **si verifica rileggendola**.
2. **La clipboard del browser non era vuota**: il banco chiedeva «il desktop ha perso il suo testo?»
   mentre il dispositivo aveva del testo suo — e allora il desktop riceve **quello**, ed è giusto.
   ⇒ La domanda si fa solo a clipboard del dispositivo vuota, e la si svuota con un proprietario che
   dichiara zero byte (⛔ non rileggendola con `readText()`: su Firefox quella lettura vuole un
   gesto, e si finirebbe per misurare il permesso).
3. **Dal secondo browser in poi non si misura un collegamento, si misura una coda**: il figlio
   sopravvive e si porta dietro lo stato della prova precedente. ⇒ La prova «sopravvive?» si fa col
   **primo** browser del giro, e per l'altro motore si rilancia il banco a server appena acceso.

#### Lo stato misurato — 21 agosto 2026

| | Firefox | Chrome |
|---|---|---|
| incolla col mouse (`07-b56`) | ⭐ 3 su 3 | ⭐ 3 su 3 |
| la clipboard del desktop sopravvive al collegamento | ⭐ sì | ⚠ non misurabile da solo *(vedi difetto 3; la cura è nel figlio, non nel motore)* |
| `Ctrl+V` nei due versi (`07-b54`) | ⭐ | ⭐ |
| la corsa di §7.4 (`07-b53`) · la tela e il clic (`07-b51`) | ⭐ · ⭐ 4/4 | ⭐ · ⭐ 4/4 |
| il bottoncino «Incolla» di Firefox | ⚠ **ogni volta** | mai |


### 9.7 · ⭐⭐⭐ CHROME PER ANDROID: **«un'esperienza completa, audio e video perfetti»** — 21 agosto 2026, sera

> *«Chrome su Android offre un'esperienza completa: audio e video perfetti.»* — l'utente.

⭐ **È il giudizio che mancava a questa fase**, ed è quello che il §2.1 pretendeva fin dall'inizio:
*si ascolta, non si contano i blocchi*. I contatori della prima sessione Android erano verdi già la
mattina — **8 935 blocchi ricevuti, 8 933 suonati, 2 buchi in 3 min 30** — ma un contatore verde non
ha mai chiuso niente qui dentro.

⛔ **E chiude il difetto che al mattino era l'unico vero aperto**: la coda dell'audio che si assestava
a **401 → 421 ms**. ⚠ La misura non era sbagliata, e non è stata «spiegata»: è stata **giudicata**.
Quattro decimi di secondo di coda si sentono in una scena — un metronomo, un video con le labbra in
campo — e in questa non si sono sentiti. ⇒ Il numero resta scritto dov'è, come numero; smette di
essere un difetto.

⭐ **Con questo, l'audio della fase 7 ha tre giudizi dell'utente, su tre mezzi diversi**: il video di
YouTube da desktop (§9.1), gli appunti nei due versi (§9.2-bis), e adesso **un telefono**.

⚠ **E il confine si scrive, perché "pienamente supportato" vuol dire *funziona, e sai in che
condizioni*** (`DECISIONI.md` §0.1-bis):

| | |
|---|---|
| il giudizio vale per | **Chrome per Android**, Samsung DeX, rete di casa |
| ⛔ **non** vale per | **Firefox per Android** — dichiarato incompatibile dall'utente lo stesso giorno (`DECISIONI.md` §7.18) |
| resta non misurato | il **datagram su rete non locale**, e la **priorità in tempo reale** dentro il figlio |

#### ⛔ 9.7-bis · E un'ora dopo, la precisazione che RIAPRE il difetto — **«400 ms fra audio e video, te lo confermo»**

> *«Su Windows ci siamo quasi, però a un certo punto l'audio è a scatti.»* → sessione sorvegliata
> con `07-b60` → *«**Audio a scatti non accaduto, era un problema del mio PC Windows. Il ritardo di
> 400 ms tra audio e video in generale te lo confermo.**»* — l'utente, 21 agosto 2026, sera.

⛔ **Due verdetti in una frase, e vanno separati**:

| | |
|---|---|
| l'audio **a scatti** | ⭐ **non è nostro** — non si è ripresentato sotto sorveglianza, ed è del suo PC |
| il ritardo **fra audio e video** | ⛔ **è nostro, è generale, ed è confermato dall'orecchio**: ~400 ms |

⚠ **E il primo giudizio non era sbagliato: era meno preciso.** *«Audio e video perfetti»* voleva dire
*ogni flusso è pulito* — ed è vero, `[M]`: zero perdite su ogni riga di ogni anello. ⛔ Quel che non
è pulito è la **distanza fra i due**, e un difetto di sincronia non si vede in nessun contatore che
guardi un flusso alla volta. ⇒ **Va scritto qui**, perché è la forma di difetto che questa fase sa
fabbricare meglio: quattro anelli tutti verdi, e l'esperienza sbagliata.

⇒ La causa, la misura sulla sessione di Windows e la cura nominata stanno in **§8**.
