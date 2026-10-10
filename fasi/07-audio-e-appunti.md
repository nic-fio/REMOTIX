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

### 6.3-bis · And three faults of the real audio bench, found by running it

⭐ None of the three could be seen by reading the code, and the third is worth it on its own:

1. `env $* $SUL_SERVER` put the step's name **before** the command ⇒ `env: 'cancello': No
   such file or directory`, exit 127;
2. a step wrote into a folder not yet created ⇒ *«No such file or directory»* disguised
   as *«I cannot read the graph»*;
3. ⛔ **`timeout 8 <shell function>` exits 127**, because `timeout` runs a program and a
   function is not one. ⚠ For two rounds the outcome was read as *«the sink is not born»* — while the
   sink **had never been asked for**. It is `LEZIONI.md` §1.9 in pure form: the red pinned
   on the wrong suspect, and the real suspect was the ceiling put in the wrong place.

### 6.5 · ⛔⛔ «The audio is silence» was a broken measurement of MINE, and it took a refutation

*17 Aug 2026. It is the costliest fault of the day, and it was not in the product.*

I had measured, and written, that the capture delivered silence: the sink was there, the `monitor_*` ports
were there, `pw-play` reached the sink — ⛔ but «no link consumed the monitor» and «the capture
node did not appear in the graph», while it declared 48 000 frames per second.

⭐ **Three scene faults, all mine**, found by an agent sent to refute:

1. ⛔ **the tone was not playing at all.** `pw-play` said so by name — *«no target node
   available»* — because **the sink is born with the first listener**, and in my rounds it started before.
   A scene that does not play measures nothing;
2. ⛔ **I took the photographs of the graph with the curtain closed**: the wait for the marker did not
   hook and consumed its whole 45 s, so the probe arrived **~1 s after the end of the
   session**. Hence «no node» and «no link»;
3. ⛔ **I had misread `pw-mon`**: `removed: id 47` was not our node, it was a
   **recycled** identifier. PipeWire's global ids are reused.

⇒ ⭐ **And point 6 was true and consistent**: the capture correctly delivered the silence of a
session in which nobody was playing. ⚠ *Two measurements contradicting each other, and the one lying was the one
that seemed more solid*: `CODER.md` §3.11 says exactly to suspect the measurement first.

⭐⭐ **And the cure was not a cure: it is the tool that was missing.** In `suono.c` there is now the
**sample peak** — the loudest in absolute value — printed in the closing line. Without it,
*«nothing can be heard»* has **two causes with an identical face** (48 000 frames/s delivered, 0
discarded, stream in `streaming`): *nobody was playing* or *PipeWire gives us empty buffers*. It is
`CODER.md` §3.10 applied to the **sample** instead of the count, and read first it closes the
diagnosis in one line.

⚠ **And five roads were tried and refuted with a measurement, not with a reasoning**: «it is
another PipeWire instance» (same `client.id`), «WirePlumber suspends the sink after 5 s»
(`suspend-timeout` at 0: rms still 0), «the buffers are not shareable» (added `MemFd`: peak
still 0), «WirePlumber destroys the node» (read the component: it demands flags we do not set),
«a volume saved at zero» (read the state: everything at 1.0).

### 6.6 · ⭐⭐ The 38 % of audio that did not leave — and the written cause was wrong

`[M]` 17 Aug 2026, real audio in **PCM** with video on: **1163 datagrams refused out of
3001**, and the judge read **464 Hz instead of 440** with purity **0.29**. ⚠ The sound was not
«with a few gaps»: concatenating what remains makes the phase jump every two blocks, and **it was
another sound**.

The comment in the code said: *«nel pacchetto non ci stava, quindi non ci starebbe mai»*.
⛔ **The measurement says the opposite**: `cwnd_left` = **12 198 bytes** against 973 requested, `destlen`
1452. ⇒ It is neither the buffer nor congestion: **it is QUIC's pacer**, which says *«not now»*.
And «not now» becomes «never» only if we throw it away.

| the cure, in three steps | refused |
|---|---|
| as it was — thrown away immediately | **1163 out of 3001** (38.5 %) |
| it is POSTPONED instead of thrown away (cap 8) | 1064 out of 2999 — ⛔ **almost nothing** |
| and the postponement is tied to **time**, not to calls | 236 out of 3001 (7.9 %) |
| ⭐ and the postponement cap goes from 8 to **64** | **8 out of 3003** — and 1 thrown away for full queue ⇒ **0.3 %** |

⭐ **And the third step was asked for by the judge, not by me**: at 7.9 % loss it still read
**465 Hz**, ⛔ and that number *is* the loss — concatenating the surviving blocks compresses time,
and 440 / (1 − 0.054) ≈ 465. ⇒ The frequency read was a **loss meter**, not a fault
of the sound.

⚠ **And the low cap protected from nothing**: the delay is already governed by the **queue** (eight
blocks = 40 ms, and beyond that the oldest is thrown away). A cap on postponements threw away a block that
would have left — two mechanisms for the same job, and the wrong one bit first.

⛔ **The middle step is the one that teaches**: `ngtcp2_conn_write_aggregate_pkt2` calls the
write several times to compose a batch, **with the same `ts`**. The eight postponements were all consumed
in there, in a microsecond — without **an instant** passing in which the pacer could
change its mind. ⚠ And the count seemed to say the opposite: *8008 «successful» postponements* next to 1064
blocks thrown away anyway.

### 6.7 · ⛔ The bench declared itself BLIND, and it was right — the scene did not go quiet

*After the cure of §6.6 the product gave **exactly 440 Hz**, ⛔ but the «2-silence» round measured
**440 Hz at 0.3535** — that is the tone at full volume where nothing should have been playing.*

⭐ **And the bench did not give green: it declared itself blind.** *«Doveva vedere SILENZIO e ha detto
VERDE»* — that is it refused to certify the other four rounds, which is exactly its
job: *a blind bench gives green to everything*.

⛔ **The cause was the scene, not the product**: `kill "$PP"` killed the **wrapper** (`setpriv`),
not `pw-play`, which survived and sang **inside the next round**. ⚠ It is the trap that
`LEZIONI.md` §2.3-quinquies names for the clipboard — *«quel che resta dal giro prima va svuotato
all'inizio»* — and it holds for every shared scene: sound is a shared scene.

⭐ **And the cure is not killing: it is verifying.** The bench now reads from the graph that the incoming links
to the sink are **zero** before going on. *«I killed»* and *«nobody is playing any more»*
are two different facts, and the next round needs the second.

⇒ ⭐ **5 rounds out of 5**, and both grafted faults seen.

### 6.8 · ⛔⛔⛔ THE REAL FAULT, AND WHY IT TOOK SEVEN CURES TO GET THERE

*17 Aug 2026. It is the costliest chapter of the phase, and the fault was in one line.*

**The fault**: **a single datagram per write pass** was sent, and the passes are ~25 per
second. The child produces **50**. ⇒ One went through, one stayed in the queue, and half of the audio
died. ⛔ It was not the network, it was not the pacer, it was not the video: **it was the loop, which offered them one
at a time**. And there was space to spare — a packet is **1452 bytes**, an Opus block **230**:
the packet stayed half empty while the audio was thrown away.

⭐ **The precision of the number was the clue**: *exactly* half. A network loss is never
exactly half; arithmetic is.

#### The six cures before the right one, and what they teach

| # | what I cured | the outcome | what it was |
|---|---|---|---|
| 1 | postponing instead of discarding | 38.5 % → 7.9 % | real cure, but downstream |
| 2 | postponing tied to **time** and not to calls | 7.9 % → 0.3 % *locally* | real cure |
| 3 | coalescing with the video packet (`MORE`) | no change for the user | ⛔ wrong diagnosis: *«the video eats the window»* — and its frames were **70-1300 bytes** |
| 4 | real-time priority (**R26**) | no change | ⭐ a **real and necessary** fault, but not this one |
| 5 | GSO padding (`PADDING`) | no change | ⭐ real fault, not this one |
| 6 | the packet I threw away with the acknowledgements inside | no change | ⭐ real and big fault, not this one |
| ⭐ **7** | **several datagrams in the same packet** | 50 % → 18 % | **the cause** |
| ⭐ **8** | and the retransmission cap removed: **the queue decides** | 18 % → **0 %** | the tail of the fault |

⇒ ⛔ **Six cures out of eight were real faults that were not what the user was hearing.** Each one
seemed confirmed by reasoning and none by measurement, because **the measurement that was needed did not
exist**.

#### ⭐⭐⭐ AND THE LESSON IS A SINGLE ONE, AND IT IS NOT ABOUT AUDIO

**I had the numbers of three rings out of four.** The child said how many blocks it produces, the server
how many it sends and how many it refuses, the session how many samples it delivers. ⛔ **Of the page —
that is of the side that LISTENS — nothing was known**: how many arrive, how many are played,
how many gaps playback makes.

⇒ For six cures I cured **the side that speaks**, measuring it, while the fault could be seen only by
putting the two sides on the same line. On the day those counters existed, the diagnosis
took **one step**:

> 50 produced → 40 delivered → deficit 20 % → cushion 250 ms → **one gap every 1.25 s**.
> Measured: **23 gaps in 30 s**.

⭐ **The count closed to the decimal, and acquitted three suspects in one go** (the page, the
cushion, the main thread) pointing to the only culprit left.

⚠ It is `CODER.md` §3.8 — *«si verifica dal lato che deve ricevere»* — and I had applied it to the
**content** (the judge listens to the samples) and **not to the rate**. A bench that listens to *what*
arrives and not *when* it arrives is blind to half the possible faults.

⛔ **And the endpoint that was needed cost thirty lines** (`/diario` in `pagina.c`): the page's
diagnostic box was not enough, because with the desktop on the page is full screen and that
box **cannot be reached** — asking the user to read it was asking him for something that
cannot be done.

### 6.9 · ⛔⛔ THE CLIPBOARD'S EXTERNAL ARBITER DOES NOT EXIST — and §2.4 promised the opposite

*17 Aug 2026, evening, at the first start of bench `07-b45`.*

§2.4 of this document said, in bold: *«il lato indipendente del banco degli appunti c'è
già, ed è gratis»* — `xclip` works without a session of ours, because Mutter's X11 bridge is
unconditional (`STUDI.md` §gnome §10 `[R]`).

⛔ **It is true of Mutter's code and false of our sessions.** `[M]`: the compositor runs as

```
gnome-shell --headless --no-x11
```

⇒ **XWayland does not start at all.** There is no X11 bridge to use.

⚠ **And the trap inside the trap**: `/tmp/.X11-unix` contained `X0` and `X1`, owned by
`prova`. A bench that had believed those sockets would have pointed at a session **dead since 15
Aug** and would have given red to the product. ⛔ Step 0 of `07-b45` looked for them exactly like that: the
first draft of the bench contained the fault the bench existed to avoid.

#### And the fallback did not hold either

The arbiter was redone on **GTK/GDK** — a real Wayland client, which is even *better*: it tests the
road an application travels, not a bridge our users do not have. ⛔ It does not work
anyway, and the causes tested were three:

| attempt | outcome |
|---|---|
| `Gdk.Display.get_default()` | **`None`**: without `Gtk.init()` there is no display. ⚠ And the error message accused **the session** of not existing while the session was alive — `CODER.md` §3.11, suspicion goes to the measurement first |
| `Gdk.Display.open(None)` | **abort**, `gdk_display_open() was called before gtk_init()` |
| `Gtk.init_check()` | ⭐ the display opens, `set()` succeeds, ⛔ **and nothing reaches the compositor** |

⛔ **The real cause is in the protocol**: `wl_data_device.set_selection` needs the *serial* of an
input event, and a client without a focused surface receives no event. ⚠ Presenting
a window was not enough, and neither was having a REMOTIX client attached — that is with libei's virtual
keyboard present, which was the first suspect (`wl-copy` says **«This seat has no
keyboard»**). ⇒ **Two plausible causes for the same symptom, and the first was not it.**

⭐ **And this explains why REMOTIX on the other hand succeeds**: `appunti.c` goes through Mutter's
`RemoteDesktop` session, which is **the privileged road and does not ask for focus**. It is exactly the
reason that road exists — and the bench proved it by contrast.

⏳ **What remains to be decided**: an external arbiter for the `session → device` direction must be
found in a **real application with a focused window**, driven by REMOTIX's input — that is
the user's scene. ⚠ Or one accepts that that direction is judged by **him**, which is invariant I8
and not a fallback.

### 6.10 · ⛔ AND TWO FAULTS OF THE TEST CLIENT, both mine, both disguised

Writing the clipboard channel into the second reader of `RCP.md`.

**1. I expected TWO bytes to recognise a unidirectional stream.** The server's QPACK streams
carry **only one** (the type, `0x02` and `0x03`) and then fall silent: that byte ended up in my
accumulator and never reached `aioquic`. ⇒ Its HTTP/3 layer did not deliver the headers
of the CONNECT, the client kept waiting, ⛔ **and the server said farewell to it with `TEMPO_SCADUTO`
for never having opened the control channel** (§4.6).

⚠ **The red ended up on the server**, which had done exactly what §4.6 tells it to do.
`LEZIONI.md` §2.3: *«una prova che boccia il codice giusto costa quanto una che promuove quello
sbagliato»*. ⭐ The cure is not accumulating better: it is **not accumulating at all** what is not ours —
a WebTransport stream starts with `0x40`, and every other first byte belongs to `aioquic`.

**2. The «other» judgement did not have a branch of its own.** A stream already recognised as video (`0x03`)
fell back into the «I don't know yet what it is» branch at **every packet**, got renamed «h3», ⛔ and the
bytes of a frame ended up inside the HTTP/3 layer. ⚠ The symptom was
`Only one QPACK decoder stream is allowed` — **an HTTP/3 error on a connection where HTTP/3
had nothing to do with it**, and the connection dropped halfway through the round.

⭐ Both are the same form: **a fault of the bench disguised as a fault of the product**, and it is
the reason `PIANO.md` §0.3.4 wants the bench certified before being believed.

---

### 6.4 · ⭐⭐ The adversarial review — **thirteen remarks, and four were serious**

*17 Aug 2026, on `audio.c`, `webtransport.c`, `pagina.html`, `rcp.c`, `main.c`. The reviewer
received **the code and the specification, not the reasoning of whoever wrote it** (`PIANO.md` §0.4).*

| # | the fault | why it was serious |
|---|---|---|
| ⛔⛔ **4** | `wt_battito_ns()` and `tono_passo()` had **two different guards for the same fact** | in every case covered by one and not by the other, the beat came back an instant **in the past** and nobody moved it: `poll()` with timeout 0, **loop at 100 % CPU**. ⚠ And the case is normal — *a browser closes the session and keeps the connection alive*, written in our own file |
| ⛔⛔ **1** | the page declared `opus` **without asking itself whether it could decode it** | §4.3 obliges the server to follow the client's order of preference ⇒ on an engine without `AudioDecoder` the server **had to** choose Opus: 50 datagrams/s into a `continue`, and the PCM — which exists to be the positive control — never came into play. ⭐ The video, in the same file, already filtered with `isConfigSupported` |
| ⛔ **2** | `AudioContext` and `AudioDecoder` **never closed** | at the seventh reattach without reloading, the engine refuses; the exception escaped the datagram reader's `for(;;)` and **killed the audio for the whole session, without a line** |
| ⛔ **3** | `suona()` **overlapped instead of throwing away** | the comment said «I throw away the oldest»; the code did not keep the references and stopped nothing. ⇒ Not a gap: **a doubled signal** |
| ⛔ **5** | `opus_apri()` outside the `try` | a rejected `configure()` killed the reader silently, **and left `a.dec` assigned but not configured** |
| ⛔ **6** | six discard roads out of eight **mute** | and `wt_audio_conti()` **did not have a single caller**: the counters never reached a line. ⇒ «audio thrown away» and «audio never arrived» had the same face |
| ⛔ **8** | *«it writes it in the log at every session»* — **it did not write it** | the I6 switch was there, the declaration that must follow it was not: whoever read the log an hour later could not know that what is heard is a bench tone |
| ⛔ **13** | `dgram_accoda` refused **without counting and without saying so** | unreachable today, ⚠ but with `figlio.c` the second caller was arriving |

⭐ **And remark 7 asked for a measurement, not a discussion** — and it is the one that paid off most:
*«`audio.h` declares that Opus may not produce a packet for every block; §6.3 wants in the instant
the time of the first sample. One of the two is false.»* ⇒ Measured in isolation (`07-b44`): **the first
is false**, and the measurement found in addition the **pre-skip** that nobody had declared.

⚠ **Seven areas declared «I found nothing»**, with those words: the framing of §6.3
counted byte by byte, little-endian, the ring's arithmetic, invariant I3 on audio, the
comparison of instants, stream starvation, memory leaks. ⛔ *It is not an acquittal*, and
it is the form `PIANO.md` §0.4 imposes.

⏳ **`[?]` remain to be measured**: remark 9 (the datagram ahead of the streams may **shrink the
GSO segment** of the whole pass, that is three `sendto` per frame instead of one) and 10
(`nw == 0` has **three** causes and the log names one).

---

## 7 · The decisions produced

*(links to `DECISIONI.md` §x.y — **not copies**)*

⚠ **And one thing to note before starting**: `DECISIONI.md` has a whole chapter for the
clipboard (**§5-ter**) and **none for audio**. The audio choices are scattered in
`SPECIFICHE.md` §10, `RCP.md` §5.3 and invariant **I5**. ⇒ If this phase takes a decision
on audio — the encoder road, the queue depth, how sound is played in the page —
**it must be recorded there**, not left inside a comment in the code.

---

## 8 · What remains `[?]` — **rewritten on 21 Aug 2026**

> ⛔ **This section was lying.** It was stuck at 17 Aug *«after the probe and before the product»* and
> listed as open things closed that same evening by the user's judgement — *«problema audio
> risolto»*, *«clipboard funziona in entrambi i versi»*. ⚠ A phase document that tells a
> state of four days ago is the kind of fault `PIANO.md` §0.1 exists against: whoever reads it
> redoes work already done, or looks for a fault where there is none. ⇒ Here is the **real** state, and the old
> list was removed instead of being left beside it.

### ✅ Real faults, open: **NONE** — closed on 22 Aug 2026 by the user's judgement

> ⭐⭐ *«Le 4 prove che ho eseguito prima davano un audio OK»* (four engines: Linux Chrome, Linux
> Firefox, Windows Chrome, Android Chrome), and to the direct question about the delay: *«**ho già scritto
> prima che il ritardo audio/video è ok**»*. ⇒ §9.8.
>
> ⚠ **What follows stays written**, and it is the story of how we got there — from the first wrong
> diagnosis to the cure. ⛔ It is not deleted: the form of the error is worth more than the conclusion.

#### ⛔ How it was on the evening of 21 Aug — **one, and now it has a name**

> ⛔ **An hour ago it said here «real faults open: none».** It was the judgement *«audio e video
> perfetti»* taken literally, ⚠ and the user clarified it right after, on the Windows PC:
> *«**il ritardo di 400 ms fra audio e video in generale te lo confermo**»*. ⇒ The fault is there, it is
> **general** (not of one platform), and it is **audible**: what is seen and what is heard do not
> go together.

⛔ **THE AUDIO DELAY BEHIND THE VIDEO — ~400 ms, and the cause is ours and written.**

`[M]` **`src/pagina.html`: `AUDIO_CUSCINO_MS = 250`** — not 60. The 60 was raised to 250 on
**17 Aug**, and the code comment says why: *«il video si decodifica e si dipinge sullo
**stesso thread** che programma l'audio; quando quel lavoro supera il cuscino la riproduzione si è
già svuotata e il cuscino si riarma — e ogni riarmo è un BUCO»*. ⚠ It was the cure for the *«jitter
pazzesco»*, and it worked: the gaps disappeared. ⛔ The price was **declared in the comment** —
*«250 ms fra quel che si vede e quel che si sente»* — and now the user has heard it.

**The sum that makes the 400**: 250 of cushion + capture, Opus encoding, the wire, decoding.
⭐ The video, on the same session, stays under the 50 ms of its ceiling ⇒ **the distance between the two is all
in here**, and it is not the network.

#### ⛔⛔ The first reading of this measurement was MINE, and it was WRONG on four points

> *Written by the coordinator on the evening of 21 Aug reading the diary counters; **refuted two hours
> later** by agent A1 with the numbers **of the same log**. It stays written because the form
> of the error is worth more than the correction.*

| I had written | `[M]` it is instead |
|---|---|
| «queue **239-270 ms** for the first two minutes» | ⛔ it is **389-539 ms**. The 239-270 are the queue **after the first re-arm** |
| «**GAPS 4**, all at start-up, the number no longer rises» | ⛔ **1 at start-up and 3 in the middle of the session** (18:00:14, :19, :29), each with a datagram loss in the same window |
| «the count closes and **acquits all the other rings**: nothing is lost» | ⛔ **something is lost**: 61 blocks = **1 226 ms**, 0.58 %. In another session of the same log: **684 blocks, 13.7 s, 9.43 %** — and in 25 s within that one, **47 %** |
| «no datagram **discarded by the server**» | ⛔ the server discarded **2 200**, ⭐ and **it also writes why**: first «the pacer's quantum», then `cwnd_left = 0` |

⚠ **How I went wrong, because it is the lesson**: every ring **counted itself** and told the truth.
The child: «50.00 sent per second, 0 lost» — true. The page: «10 621 received, 10 617 played»
— true. ⛔ **Neither counted what was in between**, and nobody did the
subtraction: 50.00 sent against **49.71** received. I read four green columns and wrote
«acquits everyone»: it is the same form as `LEZIONI.md` §1.20 — **a number nobody compares** — with
the aggravation that the missing number had to be *computed*, not just read.

#### ⭐⭐ And the `[?]` of the falling queue is CLOSED: **the queue is not a cushion, it is a one-way tank**

`a.prossimo` advanced by `n/48000` **for every block that arrives**, never with the time that passes. ⇒

```
coda(n) = coda(n-1) + (ricevuti − attesi) × 20 ms,   riarmata a 250 quando tocca zero
```

⛔ **Every lost datagram takes away 20 ms of cushion for ever**, and the only things that raise it again
are an **audible GAP** or the overflow at 600. The model reproduces the real curve: **39 clean
windows, mean gap 15 ms, maximum 72** ⇒ **it explains**.

⇒ ⛔ **The 70-110 ms were not «a steady state»**: they were the residual margin after the last burst of
losses, sampled 25 s before the end of the session. The same descent, 80 seconds earlier, had
reached 79 ms **and had made a gap**.

⭐⭐ **And this changes the cure.** In these data **there is not a single clue** that the main thread
emptied the playback: the video painted 119-136 frames every 5 s **without skipping
one**. ⇒ The `AudioWorklet` **is not the first cure**, and the *«jitter pazzesco»* of 17 Aug is explained
entirely by **losses + tank**: with a 60 ms cushion **three lost blocks** were enough.

#### ⭐ The cure written: the clock is anchored to the server's `istante`

Instead of queuing (`prossimo += durata`), playback is anchored to the **`istante` the server
already puts in every datagram** (`RCP.md` §6.3). With the anchor, a loss **does not consume cushion**: the
next block goes to its place in time, not to the back of the line. ⛔ `AUDIO_CUSCINO_MS` **was not
lowered**: with the anchor it must cover only the arrival jitter, which nobody has measured yet.

⚠ **And the cure is NOT proven where it counts**: on the home network, in 100 s, `mancati 0` — the scene did not
get a chance to show the fault. What is proven is that **it breaks nothing** (60 s: queue
251-259 flat, GAPS 0, full 0, `usciti 2806 su 2823`) and that the algorithm has the declared properties
(`07-b61-ancora.js`: **22 cases out of 22**, which cuts `suona()` out of `pagina.html` and **runs** it).

#### ⛔ And two new things open up, which could not be seen before

1. ⛔ **The server throws away the audio datagrams** because of the pacer's quantum and the congestion
   window, **while the video streams lose nothing**. It belongs to the transport, not to the
   page, and nobody had ever looked at it;
2. ⏳ **a third term really exists, but it is not the one I suspected**: the **drift between the
   clocks**, `[M]` **0.7-1.4 ms/s** between the server's clock and the client's sound card.
   The anchor does not cure it, and sooner or later it leads to the 600 ms ceiling. It must be decided whether to correct it.

`[?]` **And a sentinel that has never triggered**: if the Opus decoder **reconstructed**
the `istante` instead of carrying it over, the anchor would silently go back to being the old ladder. The
page would now declare it — ⚠ but in the test sessions nothing was lost, so the
sentinel has not yet spoken.

### ⭐ And the choppy audio on Windows was NOT ours

*The user, after the monitored session: «audio a scatti non accaduto, era un problema del mio PC
Windows».* ⚠ It is written anyway, and for two reasons: the monitoring of `07-b60` served to
**exclude** REMOTIX with the numbers, and the suspicion hanging over us — **R26**, PipeWire's `data-loop`
without real time — stays open but **is not this one**.

### ⏳ Open because nobody has measured them yet

- ⏳ **the datagram on a non-local network**: 1024/1214 bytes were taken **on cable**. ⚠ The judgement of
  §9.7 is on the home network, and holds for **that one**;
- ⏳ **the real-time priority of the audio path**: the unit grants `LimitRTPRIO=20`
  (`07-b41`), ⚠ but nobody has looked at what PipeWire does with it inside the child.

### ⭐ Closed from 17 to 21 Aug — and here it is written **how**

| was open | closed by |
|---|---|
| «the clipboard has never run against anything» | the user's judgement of the evening of 17 Aug, and then benches `07-b53`, `07-b54`, `07-b56` |
| ⛔ ~~«the audio queue at 400–420 ms»~~ | **it is NOT closed, and the wrong line lasted an hour**: the user clarified *«il ritardo di 400 ms fra audio e video te lo confermo»* ⇒ it went back to §8, with the cause |
| «nobody has yet listened to the audio from a phone» | ⭐ now someone has listened to it, and it is the user — §9.7 |
| «the Opus bitrate: 🔸 derived, never judged» | ⭐ judged **on the result**: 96 kbit/s produced a listening the user calls clean. ⛔ **The cushion is not**: that is 250, not 60, and it is the fault of §8 |
| «the bench's external arbiter does not exist» | ⭐ true, and **it is not worked around**: §6.9. The benches drive real browsers with Marionette and CDP, and the session with `wl-copy`/`wl-paste` |
| `DISPLAY` of the «prova» session · `xclip` on the test machine | ⛔ no longer needed: the X11 bridge is not there (`gnome-shell --no-x11`), and the benches do not use it |
| pasting with the **mouse** (right button → «Incolla») | §9.5 — four rings, and `07-b56`: 3 out of 3 per engine |
| the desktop clipboard **lost at connection** | §9.6 — the child gives back to the session the text it had |


## 8-bis · ⭐ 21 Aug 2026, night — **the yardstick of the audio↔video distance exists**, and the regressions run on the merged product

*Ten agents in parallel, the coordinator on merging and acceptance testing.*

### ⭐⭐ `AV = aoff − voff`: the distance is measured continuously, on any content

⛔ **The fault the user confirmed had no yardstick**, and that is why four
green rings coexisted with a wrong experience: **no counter looks at two streams
together**. Now there is one, and it did not cost a new bench — it cost **two numbers**:

- `RCP.md` §6.2 and §6.3 put **the same server clock** in the frame header and
  in the audio datagram;
- the page publishes `aoff` (audio) and `voff` (video), taken **at the same boundary**: `voff` right
  after `transferFromImageBitmap`, that is **at the glass**, not at decoding;
- ⇒ `aoff − voff` is the distance, **and the constant between the two clocks cancels out**.

`[M]` 90 s, 178 samples, moving scene, 1588×914 H.264, load 1.09→1.97:

| | min | p05 | **median** | p95 | max |
|---|---|---|---|---|---|
| `AV` | 216 | 223 | **236 ms** | 245 | 247 |

⭐ **Constant offset, not drift**: 233 → 237 → 236 over 90 s. ⭐ And the premise was **verified,
not believed**: the marker coming out of the decoder **really is** the server's `istante`
(excursion 32 ms, drift −0.02 ms/s).

⚠ **And `AV` overestimates, declared**: `aoff` includes `outputLatency` (22-28 ms `[M]`), `voff` cannot
include the equivalent because between the transfer and the lit pixel there are `[?]` **16-40 ms
that no API exposes**. ⇒ The real distance is **~200-220 ms**. ⛔ It was not subtracted: *subtracting
an estimate is fabricating a measurement*.

⭐⭐ **And the number says by itself where it lies**: at the same instant the audio queue is **253 ms** and
`AUDIO_CUSCINO_MS` is **250**. ⇒ The distance is **almost all the cushion plus `outputLatency`**, not
a delay that accumulates.

⛔ **And it is not the number the user experienced**: this is the page with the new audio clock. The
400 ms were from before, and **only he can make the comparison**.

> ### ⛔⭐ 22 Aug — **the yardstick was accused of being a tautology, and it defended itself with a number**
>
> An adversarial review showed **algebraically** that in `aoff_ms()` the instant term
> **cancels out**: `aoff = (perf − ora·1000) + base·1000 + u`. It looked like a constant, and the coordinator
> had **withdrawn the measurement**.
>
> ⛔ **The conclusion does not hold, and it was refuted with a measurement instead of with a reasoning.**
> `base` is not arbitrary: at re-anchoring it is `ora + CUSCINO − ist/1e6`, so
> `aoff = (perf − ist/1000) + CUSCINO + u` — and **`perf − ist/1000` is the real latency of the wire**.
> ⭐ `[M]` new scene: the wire latency grows by **800 ms** halfway through the session ⇒ **`aoff` goes from
> −750 to 50, a jump of exactly 800**. The yardstick sees.
>
> ⚠ **But it has a dead zone one cushion wide, and it goes on the label**: an increase **smaller than the
> residual cushion** does not move `aoff` — ⭐ and it is not a fault of the yardstick: it is that **the sound really comes out
> at the same time**.
>
> ⇒ And *«queue 253, cushion 250»*: ⛔ **it is not a confirmation** — it is the cushion read twice. The term
> that makes `AV` informative is **`voff`**, which observes at the glass.
>
> ⭐ **And the remark had hit three real faults, all cured**: `aoff` updated on blocks
> **scheduled** even if later cut (⇒ now only on `onended`, that is on what **was heard**);
> **it did not expire** — audio stopped, last value for ever, `AV` healthy on a mute session (⇒ it expires
> after the queue ceiling and answers `null`, **without new constants**); and *«it is the exact twin of
> `voff`»* was **false**.
>
> ⏳ The **236** remains to be retaken with the cured `aoff`: it is not invalidated, it is **not reconfirmed**.
> ⭐ And one thing that was missing is now known: `outputLatency` on that Firefox is **50 ms**, and it enters `AV`.

### ⭐ The regressions, on the merged product — port 7781, user `provai6`

| bench | outcome |
|---|---|
| `07-b51` the canvas and the click, **two engines** | ⭐ **4 checks out of 4 per engine**, and the click reaches the exact pixel (gap 0.0) |
| `07-b54` the clipboard **in both directions** | ⭐ session→client, client→session and **the keyboard after pasting**: green on both engines |
| `07-b56` pasting **with the mouse** | ⭐ **3 out of 3 per engine**, and ⭐ **the desktop clipboard survives the connection**. ⚠ Firefox asked for the little «Incolla» button **3 times out of 4**: it is the price of §9.5, and this is the number |
| `07-b53` the race of §7.4 | ⚠ **«la corsa non si è prodotta, questo giro NON prova niente»** — the bench refuses to give itself green, and it is the right behaviour |

⇒ ⭐ **What the user had judged on 17 Aug holds** against all of the night's changes: the
clipboard in both directions, the canvas, the click.

### ⛔ And a fault of the bench that gave RED TO THE PRODUCT — the coordinator's fault

Making the user of the clipboard benches parametric (⛔ they logged in as **`prova`**, which is
the user's: with his session alive it is the single-seat trap) I parametrised **only one
side** — the browser login — leaving `id -u prova` fixed on the **session side**.

`[M]` The result was not a bench error: it was **a red verdict against the product**
on both engines — *«il desktop remoto ha "Failed to connect to a Wayland server" invece del
testo»* — with `XDG_RUNTIME_DIR` pointing to `/run/user/1001`, the user's user.

⭐ **The lesson**: **a half-parametric bench is worse than a fixed one** — the fixed one at least refuses
to start.

## 8-ter · ⛔⛔⭐ 21 Aug 2026, night — **the audio does not lose because of the transport: it loses because of the key-frame spiral**

*It comes from the `[M]` of §8: «the server discarded 2 200 datagrams, and it also writes why». The brief
said to look at **how we treat datagrams compared with streams**. ⛔ It was the wrong suspect.*

### The four doors a datagram does not get out of, and the one that bites

| # | where | who decides |
|---|---|---|
| 1 | the 8-slot queue is full | **us** — `[M]` it almost never matters (0-1 blocks) |
| 2 | one attempt per pass | **us** |
| 3 | `writev_datagram` returns 0 | ngtcp2 |
| 4 | **4 096 postponements in a row → thrown away** | **us** — ⛔ it is this one, and beside it there is always `cwnd_left = 0` |

### ⭐⭐ But the cause is upstream, and the code had already named it as a hypothesis

`[M]` Three rounds, same scene, `netem` on the bench's port only, 30 s:

| scene | audio sent | refused | purity | bandwidth on the wire |
|---|---|---|---|---|
| **3 Mbit, STILL desktop** | **6 009** / 6 000 | 3 | ⭐ **1.000** | 1.82 of 3 |
| 3 Mbit, desktop **that moves** | **397** | 6 061 | ⛔ **0.18** | 3.39 |
| **15 Mbit**, desktop that moves | 5 997 | 15 | ⭐ **1.000** | 3.08 |

⇒ ⭐ **Same bandwidth, same audio, opposite outcomes: it is not the bandwidth, it is the video.** And it is not even what
the audio costs: `[M]` with **Opus** — **1/32** of the PCM, **1.6 %** of the link — at the same
step **58 %** is still lost.

⛔⛔ **The cause is the spiral of §5.2**, and it is written as a *hypothesis* in `webtransport.c` since before
anyone measured it:

- in the tight rounds the video delivers **only key frames** (144/144, 148/148, 107/107, 138/138, 149/149),
  against **2 out of 1 019** at 15 Mbit;
- the log counts **806 key frame requests** and **173 lines** *«la CHIAVE N tiene ancora ~60 000
  byte in coda e §5.2 vieta di abbandonarla: si ASPETTA»*;
- a 60 KB key frame on 3 Mbit occupies the window for **160 ms**, and `WT_CHIAVE_RICHIESTA_MS` grants
  one **every 150** ⇒ ⛔ **a new one is requested before the previous one has left**;
- in those 160 ms 32 PCM blocks are born, and each finds `cwnd_left = 0`.

### ⛔ Why the audio loses and the video does not — and **nobody decided it**

The video is on **streams**: if it does not go through now, ngtcp2 keeps it, splits it and retransmits it — it can
only arrive **late**. The datagram is not split, not retransmitted, cannot wait: **every
scarcity is paid in full by the audio**. ⇒ It is what happens **if nothing is decided**.

⚠ **And as it is, it is not a trade-off, it is an accident**: the audio asks for 1.6 % of the link and
loses 58 % of it, while the video takes 93 % in key frames **that feed themselves**. A deliberate
trade-off would be proportional; this one destroys the small stream in favour of the one that is big
**because it is going badly**.

### ⭐ And four transport variants that change NOTHING are worth as much as a cure

`[M]` at the same step: base **397** · without the early return per pass **278** · without
`PADDING` **406** · without `MORE`, in a packet of its own **514** · with the **reactive reserve** (the video
yields the pass) **371**.

⇒ ⭐⭐ **The window is not contended: it is already full.** Giving up writing more video **does not free
what is already in flight and not yet acknowledged**. It is the reason the cure cannot live in the
pacer, and why the three «our» doors were the wrong suspect.

### The three forms, and the choice

| | price |
|---|---|
| 🔸 **A · the key frame is not requested faster than it takes to get out** — `WT_CHIAVE_RICHIESTA_MS` from a constant to a function of the measured bandwidth | ⭐ **the only one that attacks the cause, and it takes nothing away from the audio**. ⚠ **Visible** price: on a narrow line the image stays broken longer after a loss |
| **B · preventive window reserve** (not reactive, that one is measured at zero) | caps the video at `cwnd − floor`: < 3 % when there is room, bites when it is tight — that is when it is needed. `[?]` **not measured**: it touches the write order of the streams |
| **C · the audio adapts before dying** | ⛔ **alone it is not enough, and it is measured**: 1/32 of the bandwidth still loses 58 %. A complement, not a cure |

> 🔸 **Coordinator's choice: A is written.** The other two move the bill; A removes the cause. ⏳ And
> its price is **visible to the user**, so the line is written so that he judges it.

### ⭐⭐ Cure A is written and measured — and at 1 Mbit the delivered audio goes **×38**

`chiave_intervallo_ms()` in `webtransport.c`, and ⭐ **the bandwidth is measured instead of guessed**:
`cwnd / smoothed_rtt`, that is **the two numbers ngtcp2 itself uses** to decide how much to send. The
size of the last key frame is taken **where it is a fact**, not from a constant. Floor 150 ms, margin
+20 %, ⛔ ceiling **2 s** — *a key frame that is no longer requested is a frozen screen, and frozen is not ugly:
it is half-closed* (I1).

⭐ **And the fallback is declared, not silent**: three distinct cases in the log (no connection ·
no key frame sent yet · ngtcp2 without rtt or window). `[M]` At 15 Mbit it wrote **100 times
out of 101** *«la banda misurata basta: resta il fondo di 150 ms»* — ⭐ **the cure says by itself when it is not
working**.

`[M]` **Alternating** rounds (with the variance seen — 397 against 1 372 between two identical base rounds — two
rounds in a row prove nothing), two binaries that differ by **one line**, 30 s, PCM:

| scene | expected | audio **before** | audio **after** | video before → after |
|---|---|---|---|---|
| 3 Mbit, **still** desktop *(the control)* | 150, inert | 6 009 | 6 002 | 1 → 1 |
| 15 Mbit, moving | 150, inert | 4 076 · 3 944 | 3 984 · 3 830 | 743 → 683 |
| **3 Mbit, moving** | ~171 | 371 · 462 | ⭐ **1 552 · 1 595 · 1 725** | 115 → 89 |
| **1 Mbit, moving** | 600-1000 | **15** | ⭐⭐ **577** | 57 → **47** |

⭐ At 3 Mbit the audio goes **×3.3-×4.2**, and the two groups **do not overlap**. At 1 Mbit it goes **×38**, and
key frame requests collapse **178 → 68**.

⚠ **And the price is measured, not deduced**: at 1 Mbit the video delivers **57 → 47 frames (−18 %)**,
all key frames ⇒ the image updates less often. It is exactly *«on a narrow line the image stays
broken longer»*, in numbers. ⚠ At 15 Mbit the cure is **inert**: the −8 % there is the scene's variance,
not a price.

⛔ **And what the cure does NOT do, declared**: at 3 Mbit the audio stays at **27 %** and the frames are
still **all key frames**. **The spiral is not switched off: it is slower.**

### ⏳ And the real engine is one step further upstream — `video_sgombra()`

⭐ Found **after** writing the cure, and it is the reason the cure helps but is not enough:
`video_sgombra()` runs at **every** frame and abandons the deltas still queued because *«a more recent one
has left»* (§5.1). On a wide line it almost never abandons; **on a narrow line a delta does not
get out in 33 ms, so it is always abandoned** — and every abandonment rekindles the debt of §5.2.
`[M]` The log says so **28 times per second**.

⇒ ⛔ **The debt is re-armed by the abandonment, not by the request**: limiting the requests slows the spiral,
it does not switch it off.

⏳ **The real cure would be there**: abandoning a delta only when it is **truly hopeless** (a
threshold on the queue) instead of at every more recent frame — ⭐ **§5.1 allows it, it does not impose it**.
That way under congestion the video would drop in **rate** while staying made of deltas, instead of becoming a
stream of key frames only. ⛔ **It was not written**: one cure at a time, and this one touches §5.1 — it is a
**product decision**. The reasoning and the numbers sit next to `video_sgombra()` so they are not
lost.

### ⛔ And a bench fault that had moved the diagnosis upstream

`[M]` The line *«vuole una CHIAVE»* appears in **two different messages**: the **request** leaving from
`video_regola()` and the **refusal** that `rcp.c` writes. The «806 key frame requests» of the first report
were mostly **refusals**: counted separately, in the same round, they are **105 requests against 346
refusals**. ⇒ **Two lines that look alike must be counted separately, or the diagnosis points where the
fault is not.**

⏳ `[?]` **And one thing remains unmeasured**: the spiral is proven with the **test client**, not against
a real browser. That test is done by the coordinator on the merged product.

## 8-quater · ⛔⛔ 22 Aug 2026 — **the delay came back by itself**, and «the sound starts at the first click» was an empty promise

### ⛔⛔ The new fault: the queue swells mid-session, and stays swollen

`[M]` A **five-minute round on the iron**, load 2.25: the queue jumped from **266 to 519 ms in a
single window** (`BUCHI 1`, `mancati 4`) and **stayed there** for the rest of the session.

**The mechanism**, and it is not the drift: when the main thread stops for a moment, the datagrams
accumulate in the reader and **arrive all together**. The first of the heap is old ⇒ re-arm, and
the anchor hooks onto **it**; ⛔ but behind it there are twelve more, each with its slot 20 ms further
on ⇒ **the heap ends up in the future and the cushion swells by as much as the heap was long**.
`250 + 13×20 = 510`. ⚠ It is **the attach burst redone mid-session**, where the anchor's
pull window was already closed.

⭐ **The cure is one line**: the pull window reopens at every **re-anchoring** — ⛔ not at every
block, which was the silent fault of 21 Aug (`tirate 4506 su 4508`, silence with all counters
green). In healthy sessions it reopens **zero times**.

| same 5 minutes, load 2.25 | before | after |
|---|---|---|
| queue | 266 → **519**, then 585 | ⭐ **269-289, still** |
| GAPS | 1 | ⭐ **0** |
| losses | `mancati 4` → jump and swelling | `mancati 7` → ⭐ **nothing**, neither jump nor swelling |

### ⛔⛔ And the bench had given **46 out of 46** to the code that still carried the fault

The stall scene was written with a heap of **20 blocks**: `250 + 400 = 650 ms`, that is
**beyond the 600 ceiling**, and the **overflow put things right by itself**. ⇒ The bench acquitted. With
**13 blocks** (510 ms, **below** the ceiling) the fault shows.

⭐⭐ **And it is the reason the fault was invisible: the safety net existed and passed over it.**
⚠ A scene chosen *beyond* the guard limit tests the guard limit, not the fault —
and it is a new form, a cousin of `LEZIONI.md` §1.20.

### ⭐ «The sound starts at the first click on the page» — it was an empty promise

*The page wrote it to the user; in the file there was **a single `resume()`**, at the birth of the context.*

`[M]` `banchi/07-b62-il-primo-clic.py`, **Firefox with a screen** (not headless), load 1.44 — ⭐ and the
positive control **is yesterday's page**, not a synthetic fault:

| | page before | cured page |
|---|---|---|
| how it is born | `suspended` | `suspended` |
| after 25 s without touching | `suspended`, **usciti 0** | `suspended`, **usciti 0** |
| **after a real click** | ⛔ **`suspended`, usciti 0** | ⭐ **`running`, usciti 388**, queue 259 ms |

⛔ **The answer was the worse of the two**: not only was the handler missing, but **it did not wake up by itself
even on a browser with a screen**. ⇒ Cured with four `passive` + capture events (they do not
intercept anything: the click reaches the desktop as before), which remove themselves on wake-up, plus
a `resume()` retried every 5 s of thrown-away blocks.

### ⭐ And the drift between the clocks: **the number was mine and it was wrong**

⛔ The **0.7-1.4 ms/s** declared in §8 were **largely the fault above read as drift**.
With that removed, over five clean minutes: **~0.07 ms/s** (±0.05). ⇒ From the cushion to the 600 ceiling
it would take **~80 minutes**, not four.

⏳ **The form of the cure is there, and the recommendation is not to write it now.** The only *continuous*
correction is making the anchor affine (`quando = base + istante/r`, every block at `playbackRate = r`):
price, a **constant** pitch offset ≤ 0.15 % = **2.6 cents**, below the perceptual
threshold. ⛔ The alternatives are worse, **and they were discarded with a number**: sliding
the anchor in small steps gives ~1.4 samples of step per block = **a 50 Hz hum**; inserting or
removing a block = **a tick**. ⚠ But at 0.07 ms/s **it is not worth the estimator's risk**: it stays
open, and it is re-measured on a real session of the user, where the two sound cards are different.

### ⛔ And the reordering window is OUT — it belongs to phase 9

It was written and certified (`vecchi 0 / riord 400` against `vecchi 400` with the old rule), ⛔ but
the user corrected the scope: *«i problemi di rete non rientrano in questa fase»*. ⇒ Removed from the
product **instead of leaving it inside switched off**, and the work is described in `PIANO.md` phase 9.

## 8-quinquies · ⛔⭐ 22 Aug — **the ear judge gave silence the top mark**, and there was an exact blind spot

*A remark of the review, confirmed **by reproducing it** instead of by reading it.*

`[M]` `picco = max(abs(x)…) or 1.0` ⇒ with samples **all zero** the peak becomes 1.0, the threshold
drops with it, the residuals are 0 ⇒ **`scoppiettii 0`, `resa 1.000`**: the audio judge **gives
silence the top mark**. Four seconds of zeros, verified.

⛔⛔ **And the blind spot is arithmetic, not statistical**: the PCM block is 240 samples = 5.0 ms, so
**5 blocks = 1 200 samples = exactly 11.000 cycles of 440 Hz**. `[M]` cuts of **1 200 and 2 400
samples** ⇒ `scoppiettii 0`; cuts of 240 and **1 201** ⇒ they show. ⇒ A loss in bursts of
five blocks **is stitched back continuous and in phase**, and no algorithm can hear it.

⭐ **The cure has two legs, and the second is the part that counts**: silence no longer gets the top mark
(below a peak of 400 the judge answers **`SILENZIO O QUASI — NON GIUDICO`**, which is an outcome of its own);
and ⭐ **the blind spot is cured by counting, not by listening** — the judge now receives the **expected** samples and
reports the shortfall, *«perché su un seno perfetto un taglio di 11 cicli non lascia traccia nei campioni
e nessun algoritmo può vederlo»*.

⭐ Certification from 4 to **7 cases**, and an eighth closes the diagnosis: **the same cut at 443 Hz
shows** (11.075 cycles) ⇒ **the blind spot belongs to the tone, not to the detector**. ⏳ 443 Hz proposed for future
scenes — not changed today, because it would make yesterday's numbers incomparable.

#### ⭐⭐ And the question that counts: **how many measurements were affected?**

**All 31 kept takes** re-judged with the cured judge:

- ⛔ **six change outcome**, all from the first round with the network broken: now they say *«silenzio o
  quasi — non giudico»* where they said `scoppiettii 0`. ⚠ **R7a was really biting in a
  measurement of ours** — they had already been cancelled and redone, but **by reading them by eye**; now it is the
  judge that **refuses by itself**;
- ⭐⭐ **no reported number changes**: the A/B of R26 is identical line by line, and the second leg
  confirms that **there were no hidden burst losses** (`campioni_mancanti` 0 or 240 in all the
  takes). The network table and the spiral numbers also hold.

#### ⛔ And the watcher printed «on» without having turned anything on

*(The fault was the coordinator's, who had written that file; the cure is the agent's.)* `& echo
acceso` **always** succeeds, the start-up log **was read by nobody**, and the watch file
was a **fixed** path. ⇒ The watcher does not start, the user does the session, and one reads **yesterday's
watch**.
⭐ Cured with four legs — the previous one is killed, the file carries **the time in its name**, one verifies
that the process is alive **and that the file grows** — and tested **in both directions**: *«NON È PARTITA, e
non lo dico da una parola stampata, lo dico da tre fatti»*, exit 2.
⚠ And the cure discovered a second one inside itself: `pgrep -f <script>` found the watcher of
**a previous round** ⇒ *«is it alive?»* answered yes **looking at the wrong process**. Only
the other leg saw it, the file that did not grow.

## 9 · The user's judgement

### 9.8 · ⭐⭐⭐ **«Le quattro prove che ho eseguito davano un audio OK»** — 22 Aug 2026

> *«Le 4 prove che ho eseguito prima davano un audio OK. L'unico piccolo appunto è
> un'ottimizzazione sulle performance grafiche, che credo sia lo scopo della fase 8.»* — the user.

⭐ **The four tests are the four engines declared the same morning** (`DECISIONI.md` §7.20):
Linux Chrome, Linux Firefox, Windows Chrome, Android Chrome. ⇒ It is not a judgement on one
platform: it is **on all those the product declares it serves**.

⭐⭐ **And with this the audio of phase 7 has the judgement it was missing.** The yardstick has always been
**I8** — what the user hears — and now that yardstick has spoken on four engines instead of on
one.

⭐⭐ **And the delay between audio and video IS CLOSED** — asked and confirmed: *«ho già scritto prima che il
ritardo audio/video è ok»*. ⇒ The *«audio OK»* of the four tests included **synchronisation**, not
only the cleanliness of the stream.

⛔ **It was the last real fault of phase 7**, and it is the one the user had confirmed on the evening of the 21st
with *«il ritardo di 400 ms tra audio e video in generale te lo confermo»*. ⇒ Between the two sentences there
are: the **anchor to the server's `istante`** (the queue is no longer a one-way tank), the
**reopening of the pull at every re-anchoring** (the queue no longer swells mid-session), the cure
of the **key-frame spiral** (the audio no longer dies when the line narrows) and the **first click**
that now really turns the sound on.

⚠ **And the `AV` measurement still remains to be retaken** (§8-bis, with the cured `aoff`): it is no longer needed to
decide whether the fault is there — the ear decided that — ⭐ it serves to **notice if one day it
comes back**, which is a different and equally useful job.

⇒ ⭐ **And the only remark left belongs to another phase**: graphics performance, which is
**phase 8** — and the user pointed there himself.



*The phase closes on a measurement judged by the user, not on a complete document.
⛔ A verdict the user did not give is not written.*

### 9.1 · ⭐⭐⭐ AUDIO: **«problema audio risolto»** — 17 Aug 2026

Given on a **YouTube video** played in the remote session, and confirmed by the counters:

| | |
|---|---|
| blocks received by the page | 2184 → 3183 in 20 s = **49.95/s** against 50 produced |
| loss | **zero** |
| **gaps in playback** | **2**, and stopped — no new gap in twenty seconds |
| queue | stable at **311-341 ms** |

### 9.2-bis · ⭐⭐⭐ THE CLIPBOARD: **«clipboard funziona in entrambi i versi»** — 17 Aug 2026

*Given by the user with the browser, on port 7730, session of user `prova`.*

⛔ **It is the I8 yardstick, and nothing replaces it**: no automatic bench has ever seen a
byte of clipboard pass — the external arbiter §2.4 promised **does not exist** (§6.9), and that verdict is
the only proof this half of the phase has.

⭐ **And it covers both directions**, that is also the one `DECISIONI.md` §5-ter.1 declares the most
used: *«copio un indirizzo sul telefono e lo incollo nel browser remoto»*.

⭐ **And with it passes, in passing, the cure of the race with `Ctrl+V`** (§4.5.2): the
`device → session` direction **is** that race: the announcement and the keys leave together, and if the cure had not
worked the first paste would have come back empty.

> ⚠ **What the verdict does NOT say**, and it must be written so that it is not read for more than it is:
>
> - **on which browser**: the page's log line — the one that says whether `clipboardchange`
>   is there and **where it is** — was not reported. ⇒ It stays `[?]` whether the
>   `device → session` direction worked by **watching** (Chrome) or by **`Ctrl+V` on the
>   page** (Firefox and Safari). They are two different roads (§4.5, `pagina.html`), and knowing which one
>   held changes what is declared to the user in §9 of `SPECIFICHE.md`;
> - **no numbers**: no measurement of how much text, how much time, nor of the second round when
>   the browser denies writing to the clipboard;
> - **the DeX and the phone** stay `[?]`, as for audio.

⇒ **Phase 7 now has its two judgements**: *«problema audio risolto»* and *«clipboard funziona in
entrambi i versi»*. ⛔ And **phase 6 stays open**: its §8 still awaits the judgement on two
scenes (dragging the border and the click held down), and what remains of 6 **does not close by
itself**.

### 9.2 · ⛔⛔ AND BEFORE THE «RISOLTO» THERE WERE SEVEN «FA SCHIFO»

*It must be written, because it is the part that teaches.* Bench `07-b43` was **green on five rounds out of
five** — exactly 440 Hz, exact amplitude, volume that governs — and the user heard
*«jitter pazzesco»*. ⇒ **I8 is not a formality**: the yardstick is what the user hears, and five
greens do not replace it.

⭐ **And three steps forward out of four were taken by him, not by me:**

1. *«forse il datagram è troppo piccolo?»* → ngtcp2's manual proves the intuition right in one
   line: a GSO batch is written **only if the first packet is full size**;
2. *«nella cartella REMOTIX l'audio funzionava, esaminala»* → **R26**, the real-time priority
   denied by the unit, measured on 5 Aug 2026 and rewritten by me as `[?]` without ever doing it;
3. *«riproduci un video e monitora byte per byte»* → it is the round that produced **the exact
   number**, and from there the diagnosis stopped being a series of hypotheses.

---

### 9.3 · ⛔⛔⭐ «SI È BLOCCATO FIREFOX CON LA CLIPBOARD» — and it was not Firefox

*20 Aug 2026, fault reported by the user while testing the two browsers. ⚠ It was not the
browser freezing: it was **our page** sending `ERRORE_PROTOCOLLO` and closing the session — and from
outside it looks like an image that stops.*

**`[M]` The server's log, 19:04:06, and the chain fits in four lines:**

```
19:04:06.560  annunciato al client il trasferimento 3 — 1155 byte
19:04:06.560  annunciato al client il trasferimento 4 — 1155 byte   ← stesso millisecondo
19:04:06.569  il client chiede il 3, superato dal 4: lo servo col testo ATTUALE
19:04:06.612  il client si congeda, motivo=0x0b — «i messaggi di trasferimenti
              diversi non si mescolano (§7.4)»
```

⇒ ⭐ **The server was right and the page wrong**, and the arbiter is written: `RCP.md` §7.4 says
*«un `APPUNTI_CHIEDI` che arriva quando l'annuncio è già stato superato si serve **con il testo
attuale** … è la corsa normale fra due che copiano, **non un errore**»* — the **fifth exception
declared in §3**. The page applied the general rule and ignored the exception.

⛔⛔ **And the same mistake was written at BOTH ends**: `rcp.c` closed the session in the mirror
case (the client serving a superseded request). ⚠ The page, on the other hand, applied the exception
**correctly** when it was the one *serving*: the same rule written twice, and the second one
different — it is form **E2** inside a single file.

**The cure, at both ends**: the error is a text **that nobody ever asked for**, not a text with an
old number. ⇒ It is compared with **what was asked for** (`APPUNTI.chiesti` in the page,
`app_chiesto_id` in the server), and the length is demanded **only** on the live transfer — on a
superseded one the text served is the *current* one.

#### ⭐⭐ And the bench found TWO more, both mine, after the cure

*It is the value of `banchi/07-b53-appunti-corsa.py`, and it is the reason it exists.*

| | the fault | how it showed |
|---|---|---|
| 1 | **I deleted the record at first use** | a second answer for the same transfer — legitimate — found the record empty and closed the session. ⇒ The right question is *«did I EVER ask for it?»*, not *«do I have one in flight?»* |
| 2 | ⛔ **I marked the request AFTER the `await`** | and the answer can arrive before the wait resolves: ⭐ **green on Firefox, red on Chrome**, by a tenth of a millisecond. ⇒ The fact is marked **before** delivering, and the identifier put in the message is marked — not the one read back afterwards |

⛔ **The second is the reason a single bench is not enough**: the same cure, on the same
product, in the same minute, **passed on one engine and failed on the other**.

#### ⚙ The bench, and why it reproduces a STATE instead of a coincidence

⚠ `[M]` The real window lasts as long as reading the clipboard from the session: **under a
millisecond** on a local network. Six copies in a burst inside the session (`wl-copy`, 15 ms
apart) **did not open it even once**. ⇒ The bench puts the page **exactly
in the state** that closed the user's session: it requests a transfer and makes a newer announcement arrive — before
the answer. ⛔ It is white-box, it touches `REMOTIX.appunti`, **and it declares it**:
what it verifies is the **rule**, not the timing.

⭐ **And it certifies itself**: with the old line put back, `[M]` the bench sees the session close with
`motivo=0x0b` — the same face as the user's fault. With the cure put back, **4 rounds out of 4 green,
Firefox and Chrome**.

⛔ **And a fault I made while curing**, because it is the part that teaches: to expose the state
to the bench I had hooked `APPUNTI` to the `window.REMOTIX` box, which runs **long before** its
declaration — reading a `const` in its dead zone stops **the whole rest of the script**.
⚠ The symptom named none of this: the login form lost its handler and the
page ended up at `GET /?utente=…&parola=…`, that is **the password in the address bar**.
A declaration-order fault turned, for two minutes, into a privacy fault.

---

### 9.4 · ⛔⛔⭐ «DA SERVER A CLIENT FUNZIONA, IL CONTRARIO NO» — on Firefox, and the causes were THREE

*20 Aug 2026, reported by the user. ⚠ And the direction that did not work is the one no bench
had ever tested **with real keys on a real browser**: `07-b45` measured the protocol, not the
browser's path.*

#### The reproduction, and it is the part that decides

⛔ **In headless the fault does NOT show**: the `paste` event arrives anyway. Not on X11 (Xvfb) either.
⭐ It shows in **a nested Wayland compositor** (`cage`), with the text copied from **another
application** — that is the user's environment. `[M]` The page's diary, three lines:

```
appunti · Ctrl+V visto · sorveglianza=«nessuna»
appunti · evento `paste` arrivato · 0 caratteri          ← VUOTO
appunti · l'evento `paste` è arrivato: strada gratis, nessun permesso
```

and `annunciati: 0`: **nothing ever left**.

#### The three causes, and they are all ours

| | the cause | why it bit |
|---|---|---|
| 1 | ⛔ **an empty `paste` counted as a delivery** | `ultimo_paste_ms` was marked **before** checking whether there was text ⇒ the `readText()` fallback was switched off («free road») and nothing else was tried |
| 2 | ⛔ **nothing editable had focus** | and the `paste` event is born only there. ⚠ The comment of §9 said *«la cura ovvia non si può fare»* because a focused `TEXTAREA` switches off the keyboard (`cl_nel_modulo`) — ⭐ **it was false**: it was enough to **name the exception** instead of giving up |
| 3 | ⛔ **the text «waiting for a gesture» stole the clipboard** | the text coming from the remote desktop waited for a gesture to enter the local clipboard, and the gesture could be **the user's `Ctrl+V`** — that is it was written over his copy exactly while he was pasting it. `[M]` The bench saw it: the remote desktop received **its own text back** |

#### The cures, and they are four

⭐ **The hidden field** (`incolla_campo_prendi`): it takes focus **only for the 400 ms of the `Ctrl+V`**,
the browser's paste has somewhere to go, the `paste` event is born with the text inside, and **no
permission is asked**. ⛔ And `cl_nel_modulo()` exempts it by name: keys keep going to the
remote desktop — the bench verifies it by typing a letter **after** every paste.

⭐ **The second road**: after 120 ms **what the browser really pasted into the
field** is read. It does not depend on `clipboardData`, which may arrive empty. `[M]` On X11 it is the road that
delivered: *«il campo dell'incolla porta 45 caratteri»*.

⭐ **An empty `paste` does not count**, so the `readText()` fallback stays available.

⭐ **And the waiting text is never written on a clipboard gesture** (`Ctrl+V`, `Ctrl+C`,
`Ctrl+X`), ⛔ and **it is thrown away** if the user copies something of his own: *«his clipboard is worth more»*.

⛔ **And the silence is broken**: if `readText()` does not answer within 1.5 s — on Wayland Firefox opens its
little «Incolla» button and **waits**, neither resolving nor failing — the page **tells** the user
instead of leaving him in front of something that «does not work».

#### ⚙ The bench — `banchi/07-b54-appunti-due-versi.py`, and it measures FOUR boxes

*session→client and client→session, for Firefox and for Chrome, ⭐ plus a fifth: **is the keyboard
still alive after the paste?*** — because a cure that fixes the clipboard and switches off the keys would be
a terrible deal.

⛔ **And it uses no special permission**: Firefox's test preferences
(`dom.events.testing.asyncClipboard`) would switch off precisely the fault being looked for. The clipboard is
filled with a **real** `Ctrl+C` and read with a **real** `Ctrl+V`. ⚠ And the gesture that unlocks
writing must be a **click from the driver**: an event fabricated in JavaScript is not
a «user activation», and the browser refuses anyway.

**`[M]` The outcome, 20 Aug 2026 — four environments:**

| environment | firefox | chrome |
|---|---|---|
| headless | ⭐ ⭐ ⭐ | ⭐ ⭐ ⭐ |
| X11 (Xvfb, real browsers) | ⭐ ⭐ ⭐ | ⭐ ⭐ ⭐ |
| Wayland (nested `cage`) | ⭐ ⭐ ⭐ | *(not tested)* |
| copy from **another application** → paste into the product (X11) | ⭐ | — |

⚠ **And what could not be tested, declared**: the case «Wayland **+** clipboard of another
application **+** synthetic keys» stays red, and ⛔ **it is not the product**: Wayland delivers the
clipboard only in response to a **real** input event (the compositor's *serial* is needed), which a fake
key does not have. ⇒ On that path the last word belongs to a real keyboard — that is to the user.

---

### 9.5 · ⛔⛔⭐ «FUNZIONA CON `Ctrl+V`, MA NON COL MOUSE» — 21 Aug 2026, and the broken rings were **four**

> *«Ecco perche'! Funziona l'incolla con ctrl+v, ma non con il mouse e scegliendo dal menu la voce
> "incolla"»* — the user, on the morning of 21 Aug, right after verifying the cure of §9.4.

⭐ **A sentence worth a day of diagnosis**: it says that the previous day's cure went in (the
`Ctrl+V` delivers) and names exactly the road left uncovered.

#### The difference, and why none of the four green benches could see it

| the user does | who touches | what is born on the page |
|---|---|---|
| `Ctrl+V` on the page | **the browser** | the `paste` event, with the text inside — for free |
| right button → «Incolla» **inside the remote desktop** | **the remote desktop** | ⛔ **nothing** |

⇒ That menu is painted in the video, and the «Incolla» item is executed by an application on the other
side of the wire. The only news of it that reaches the page is the server's `APPUNTI_CHIEDI`.
⛔ **And the four green benches of §9.4 all pressed `Ctrl+V`**: they measured the only road that already
worked. The missing bench is `banchi/07-b56-incolla-col-mouse.py`, which never presses a key.

#### The four rings, in order of discovery — and **three were mine**

**1 · The page was not even consulted.** `rcp.c` asks nothing of a client that
has never
announced: it queues the request («*the question WAITS for the announcement*») and the child's bottom
closes it empty-handed after four seconds. ⇒ Until the user had pressed **at least one**
`Ctrl+V`, a paste with the mouse did not get to ask **even one question**: no line, anywhere.
⭐ **Cure**: the page sends a **zero-byte opening announcement** as soon as the session is born.
It costs eight bytes once, opens the question channel, and tells the truth — at that instant it has
no clipboard read.

**2 · ⛔ And that announcement left TOO EARLY, and closed the session.** `[M]` Log of
05:55:42: *«congedo motivo=0x0b — byte sullo stream di appunti (14) prima che `SESSIONE` sia partita
(stato: attesa-verdetto)»*. `avvia_appunti()` runs at ECCOMI, that is **before the credentials**.
⇒ The opening announcement was moved after `SESSIONE` (`appunti_apri_la_domanda`).

**3 · ⛔ The offer to the session fell into the void, and nobody redid it.** `[M]` 06:00:15 —
the announcement at `.868`, the opening of the session's clipboard at `.982`: **114 ms** in between, and
in those 114 ms the child wrote *«gli appunti della sessione non ci sono: l'offerta cade»*.
⇒ The compositor never became owner of the selection, and inside the desktop the «Incolla» item
**had nothing to give**.
⭐ **Cure**: `figlio.c` keeps **one bit** (`appunti_offerta_arretrata`) and redoes the offer as soon as the
clipboard opens. It is the same shape as `rcp.c`'s backlogged question: instead of delaying
something for everyone, one stitches it back.

**4 · ⛔⛔ And the new announcement KILLED the paste that had provoked it.** The fault was told by
Mutter in its own words: `[M]` *«SelectionWrite per la richiesta 2 è stata rifiutata — Transfer serial
2 doesn't match any transfer request»*.
⚠ Offering the selection to the compositor (`SetSelection`) **cancels the transfers in flight**: it is the
compositor that, seeing a new selection, throws away the requests open on the old one. And we
re-offered *exactly while we were serving* — the page re-reads the clipboard, announces the new text, and
that announcement threw away the paste in progress. ⇒ **Whoever pasted saw empty**, which is the symptom
we had started from.
⭐ **Cure**: while there are pending requests the offer is **postponed** (`app_offri_dopo`), and it leaves
once the answer has left.

#### And the cure at the centre: **the clipboard is re-read when the desktop asks**

`appunti_rileggi_prima_di_servire()` — on `APPUNTI_CHIEDI`, before serving, the page re-reads the
device's clipboard. ⭐ The permission is there: **the click on the «Incolla» item of the remote menu is a
click on this page**, so the transient activation is milliseconds fresh.

⛔ **And it is not re-read if the free road has just delivered** (`paste` less than 4 000 ms ago):
without this line one cured mouse pasting **by breaking keyboard pasting**, because on
Firefox every re-read costs the little «Incolla» button.

#### The price, measured — `banchi/07-b56`, 3 pastes per browser

| | Chrome | Firefox |
|---|---|---|
| the mouse paste arrives | ⭐ **3 out of 3** | ⭐ **3 out of 3** |
| the little «Incolla» button appears | **never** | ⚠ **3 times out of 3** |
| pasting the **same** text a second time | — | ⚠ it appears **again** |

⚠ **On Firefox pasting with the mouse costs one more click, every time.** It is not our choice:
`readText()` there always opens the confirmation button, even with an unchanged clipboard (`SPECIFICHE.md`
§9 — «*ogni lettura costa il menu Incolla*»). ⭐ But this time it appears **where the user is already
clicking**, not in a corner nobody looks at. And `Ctrl+V` stays free on both
engines.

#### ⛔ Three faults of the bench, and two would have declared a healthy product broken

1. **Chrome did not go onto the bench's screen.** Without `--ozone-platform=x11` it takes Ozone/Wayland
   and attaches to the **real** graphical session: it read **another** clipboard, and `readText()`
   came back empty while `xclip -o` on the bench's screen showed the text.
2. **The bench clicked too early.** Between the click and `wl-paste` there are `ssh`, `sudo` and `runuser`:
   `[M]` whole seconds, and transient activation lasts five seconds. ⇒ *«lack of user
   activation»* was the bench, not the product. Cure: the remote script says **`PRONTO`** and waits
   a second and a half, so the order of events is the real one.
3. **`xclip` hung the bench**, like `wl-copy` in the session: it forks to *serve* the
   selection and keeps its outputs open. ⇒ It is not waited for.

⭐ And to click Firefox's little button the bench enters the **chrome context**
(`clipboardReadPasteMenuPopup`), with `-remote-allow-system-access`: ⛔ `dom.events.testing.asyncClipboard`
is **not** turned on, since it would switch off precisely the thing to be measured. The bench pays the
price in front of everyone and **reports how many times**.

### 9.6 · ⛔⛔⭐ «COME UNA SESSIONE LOCALE» — the directive, and the fault it brought out

> *«L'esperienza dell'utente con REMOTIX dev'essere quanto più vicina possibile all'esperienza con
> una sessione grafica locale. […] niente trucchi, pulsanti strani o soluzioni tecniche che si
> allontanino da questa direttiva»* — the user, 21 Aug 2026. `DECISIONI.md` §5-ter.8.

⭐ Verifying the cure of §9.5 in the light of that sentence, a question came up that no bench
had ever asked: **if I had already copied something in the desktop and then I connect, is that text
still there?**

⛔ `[M]` **No, and the morning's cure was to blame.** `wl-paste` inside the session said
`TESTO-CHE-ERA-GIA-NEL-DESKTOP` before connecting and **`«»`** after.

⇒ The chain: to be found when someone pastes with the mouse, the page announces itself as soon as it enters
— and announcing itself means **taking the selection**, which is a single one. Taking it empty-handed
erased what the user had copied over there. ⛔ It is exactly the opposite of a local
session, where the clipboard does not vanish because someone came in.

#### And the diagnosis corrected a line of code that asserted something false

`appunti.c` said that `EnableClipboard` with empty options makes a `SelectionOwnerChanged` arrive
**immediately**, *«ed è proprio l'annuncio che fa ritrovare gli appunti a chi si ricollega»*.
⛔ **False, measured**: `wl-copy` alive and owner, `wl-paste` re-reading its text before and
after, and in the child's log **no read line**. Mutter reports **changes** of
owner, not who already is one. ⇒ The clipboard that is there is **asked for** (`appunti_leggi_adesso()`), and
asked for again **at every reattach** — the child survives between one connection and the next, so the
read done at start-up holds only once (`MSG_RIMANDA_PALCO`, which means exactly
«a client has reattached»).

#### The definitive cure lives where the text really is

⭐ **If the client has no clipboard to give, the child gives back to the session the last text the
session itself had given it** (`appunti_rispondi`). The selection changes hands, **the content
does not**. ⇒ Whoever connects loses nothing, and the mouse-paste road stays open.

⚠ **And two intermediate cures were thrown away, with their reason**:

| cure tried | why it fell |
|---|---|
| «an empty announcement does not take the selection away from whoever has something» (in `rcp.c`) | it protected the clipboard **by closing the mouse road**: without the selection, the desktop asks us nothing |
| «the session's first text is learned but not written into the device's clipboard» (in the page) | it could not tell *the initial state* from *the first copy made in the session*, and it turned red the session → client direction on both engines (`07-b54`) |

⇒ ⭐ The lesson, and it is the same as always: **the cure goes where the information is**. Neither the page
nor the protocol knows what the desktop's clipboard contains; the child does.

#### ⛔ And three more faults of the bench, all declaring a healthy product broken

1. **`wl-copy` killed by the bench's `timeout`**: it forks to *serve* the selection, and the
   `timeout 12` wrapping the script took it away along with the group. ⇒ `setsid`, and the copy
   **is verified by reading it back**.
2. **The browser's clipboard was not empty**: the bench asked «has the desktop lost its text?»
   while the device had text of its own — and then the desktop receives **that**, and rightly so.
   ⇒ The question is asked only with the device's clipboard empty, and it is emptied with an owner that
   declares zero bytes (⛔ not by re-reading it with `readText()`: on Firefox that read wants a
   gesture, and one would end up measuring the permission).
3. **From the second browser on one does not measure a connection, one measures a tail**: the child
   survives and carries the previous test's state along. ⇒ The «does it survive?» test is done with the
   **first** browser of the round, and for the other engine the bench is relaunched with a freshly started server.

#### The measured state — 21 Aug 2026

| | Firefox | Chrome |
|---|---|---|
| mouse paste (`07-b56`) | ⭐ 3 out of 3 | ⭐ 3 out of 3 |
| the desktop clipboard survives the connection | ⭐ yes | ⚠ not measurable on its own *(see fault 3; the cure is in the child, not in the engine)* |
| `Ctrl+V` in both directions (`07-b54`) | ⭐ | ⭐ |
| the race of §7.4 (`07-b53`) · the canvas and the click (`07-b51`) | ⭐ · ⭐ 4/4 | ⭐ · ⭐ 4/4 |
| Firefox's little «Incolla» button | ⚠ **every time** | never |


### 9.7 · ⭐⭐⭐ CHROME FOR ANDROID: **«un'esperienza completa, audio e video perfetti»** — 21 Aug 2026, evening

> *«Chrome su Android offre un'esperienza completa: audio e video perfetti.»* — the user.

⭐ **It is the judgement this phase was missing**, and it is what §2.1 demanded from the start:
*one listens, one does not count blocks*. The counters of the first Android session were already green in the
morning — **8 935 blocks received, 8 933 played, 2 gaps in 3 min 30** — but a green counter has
never closed anything in here.

⛔ **And it closes the fault that in the morning was the only real one open**: the audio queue settling
at **401 → 421 ms**. ⚠ The measurement was not wrong, and it was not «explained»: it was **judged**.
Four tenths of a second of queue can be heard in a scene — a metronome, a video with lips in
frame — and in this one they were not heard. ⇒ The number stays written where it is, as a number; it stops
being a fault.

⭐ **With this, phase 7's audio has three user judgements, on three different media**: the
YouTube video from the desktop (§9.1), the clipboard in both directions (§9.2-bis), and now **a phone**.

⚠ **And the boundary is written, because "fully supported" means *it works, and you know under what
conditions*** (`DECISIONI.md` §0.1-bis):

| | |
|---|---|
| the judgement holds for | **Chrome for Android**, Samsung DeX, home network |
| ⛔ it does **not** hold for | **Firefox for Android** — declared incompatible by the user the same day (`DECISIONI.md` §7.18) |
| remains unmeasured | the **datagram on a non-local network**, and the **real-time priority** inside the child |

#### ⛔ 9.7-bis · And an hour later, the clarification that REOPENS the fault — **«400 ms fra audio e video, te lo confermo»**

> *«Su Windows ci siamo quasi, però a un certo punto l'audio è a scatti.»* → monitored session
> with `07-b60` → *«**Audio a scatti non accaduto, era un problema del mio PC Windows. Il ritardo di
> 400 ms tra audio e video in generale te lo confermo.**»* — the user, 21 Aug 2026, evening.

⛔ **Two verdicts in one sentence, and they must be separated**:

| | |
|---|---|
| the **choppy** audio | ⭐ **it is not ours** — it did not recur under monitoring, and it belongs to his PC |
| the delay **between audio and video** | ⛔ **it is ours, it is general, and it is confirmed by the ear**: ~400 ms |

⚠ **And the first judgement was not wrong: it was less precise.** *«Audio e video perfetti»* meant
*each stream is clean* — and it is true, `[M]`: zero losses on every line of every ring. ⛔ What is not
clean is the **distance between the two**, and a synchronisation fault does not show in any counter that
looks at one stream at a time. ⇒ **It must be written here**, because it is the form of fault this phase knows how to
manufacture best: four rings all green, and the wrong experience.

⇒ The cause, the measurement on the Windows session and the named cure are in **§8**.
