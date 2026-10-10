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
