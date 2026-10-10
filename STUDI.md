# STUDI — other people's code, read before writing ours

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without the card and colour conversion with swscale; those of encoding on the card and of audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

*Sewn into a single document on **16 August 2026**, by the user's decision: they were eight files
scattered in the project root. ⛔ **It is not a summary**: the text is what it was, line by
line, with the headings lowered by one level to fit under the chapters. In the sewing no
measurement, no mark and no date was touched; later, with phase 18, only the measurements
the change invalidated were removed (see the ⚠ line above).*

> ⚠ **HOW TO READ THE PATHS IN HERE** *(convention added on 28 August 2026)*
>
> This document cites **other people's** files, and for years wrote them with the same notation as
> ours — `grd-session.c`, `include/lsquic.h`, even `src/backends/...` with **our** prefix
> `src/`. ⛔ The reader could not tell a file they can open from one that isn't there.
>
> ⇒ From here on: a path **marked ⟨name⟩** (`⟨mutter⟩`, `⟨gnome⟩`, `⟨lsquic⟩`) lives
> in the tree of **that project**, which is re-cloned with `git clone` and **is not in the repository**
> (`reference-gnome/`, `reference-kde/`… are in `.gitignore`: they weigh 682 MB and are versioned
> upstream). A path **without a mark** is ours and opens here.

> ## ⛔ What this document is, and what it is NOT
>
> **It is not REMOTIX documentation.** It is the study of **other people's** code — compositors, browsers,
> products that do our same job — done **before** writing ours, so as not to
> pay again for what someone had already paid for.
>
> ⇒ What REMOTIX **is** lives in `SPECIFICHE.md`; what it **does** in `PIANO.md`; what has been
> **decided** in `DECISIONI.md`; what has been **paid for** in `LEZIONI.md`. Here there is only material
> that was read.
>
> ⚠ **And dates matter more than elsewhere.** Six of these eight studies are from **7-9 August 2026**,
> that is **before the V2 plan existed** — they were written for **v1**. ⛔ Where they say *«per
> la fase 11»* or *«per la fase 10»* they mean **the phases of v1**, not those of `PIANO.md`. The
> reference stayed as it was written, and it is this line that says how to read it.

## How to find something in here

Each chapter keeps **the section numbering it had as a separate file**. ⇒ A cross-reference that
used to say §kde §3.3-bis now says **`STUDI.md` §kde 3.3-bis**, and the section has the same
number as before: **the chapter keys are the names the files had**.

| chapter | what it studies | written on | lines |
|---|---|---|---|
| **§web** | the browser as client — W3C/WHATWG, Chromium, Gecko, WebKit, Guacamole, noVNC | 9 Aug 2026 | 566 |
| **§gnome** | GNOME and Mutter — the first desktop | 9 Aug 2026 | 587 |
| **§kde** | KDE Plasma and KWin 6.3.6 — the second desktop | 7 Aug 2026 | 2 213 |
| **§xfce** | XFCE, labwc and wlroots — the third | 8 Aug 2026 | 857 |
| **§lxqt** | LXQt on Wayland — the fourth | 8 Aug 2026 | 511 |
| **§cinnamon** | Cinnamon and Muffin 6.7.4 — the fifth | 9 Aug 2026 | 321 |
| **§gnome-remote-desktop** | GNOME's product that does our job | — | 1 018 |
| **§xpra** | XPRA — the study that arrived late, and says so itself | 14 Aug 2026 | 222 |

⚠ **Each chapter carries its own legend of marks** — `[R]` read in the code, `[M]` measured,
`[?]` not verified — because it had one as a separate file. **They are eight almost identical copies and
they agree**: none was removed, for the same reason nothing else was removed.

⛔ **And one thing this document does NOT solve**: the studies are **snapshots of a version**.
§kde read KWin **v6.3.6**, §cinnamon muffin **6.7.4**. What they say was true of that
tag — and on the day of the update it must be re-read, not remembered.


---

# Part I — The client


<a id="web"></a>

## The browser as client — study, for phase 1

*Written on 9 August 2026, with four parallel investigations into the W3C/WHATWG specifications and the
source code of Chromium, Gecko, WebKit, Guacamole, noVNC and Xpra. It is the project's **sixth study**, and
the first that does not talk about a compositor.*

> ### ⚠ Why this study exists
>
> On 9 August 2026 the user decided that **REMOTIX will have no dedicated clients**: the client is a
> web page (`DECISIONI.md` §1.6). The other five studies answered the question *«questo
> desktop ci lascia lavorare?»*; this one answers *«il browser ci lascia lavorare?»*, and it is the
> same question put to a component that **we cannot modify, cannot choose and
> cannot query**.
>
> ⭐ **And it is the first study done before writing the code instead of after** — which is
> precisely point 1 of the recipe in `LEZIONI.md` §9.

> **The marks:** **[R]** read in the source code, with file and line — it is not a measurement · **[S]**
> read in a specification or in official documentation, with the URL · **[?]** deduced or not
> verified · **[M]** measured by us — ⛔ **in this document it never appears**, and it is not an
> oversight: nobody has switched on a browser yet.
>
> The detail is in the four reports in `web/rapporti/`: **S1** certificate (920 lines), **S2**
> decoding (730), **S3** keyboard and clipboard (1.391), **S4** drawing delay.
>
> ⭐ **And since the night of 10 August 2026 there is a fifth file in that folder that is not a study**:
> `web/rapporti/S-esiti-sonda.md`, **the measured outcomes** of the browser probe — S7, S1b, S5 — with
> the scene next to every number, the `.jsonl` logs to trace back to, and ⛔ **the recount of 11
> August that declares which numbers have a provenance on disk and which do not**. ⚠ It is there that the `[M]`
> of this study begins to exist; in here it still does not appear.

---

### 1. In two minutes

#### 1.1 ⭐ The five things this study changed

| # | | |
|---|---|---|
| 1 | ⛔ **The certificate exception does NOT cover WebTransport** | neither on Chrome nor on Firefox `[R]`. The «one click and go» default that had been proposed **does not work**, and the road becomes `serverCertificateHashes` — §3 |
| 2 | ⛔ **`prefer-hardware` proves nothing on Android** | Chromium **deliberately** picks a software HEVC decoder when it does not find a hardware one `[R]`. It is error shape **E1**, that is v1's wall, **reappearing one level higher** — §4 |
| 3 | ⭐ **Much less keyboard is lost than feared** | in full screen Chrome's reserved list drops from twelve commands to **two** `[R]` — §5. ⚠ But what the **operating system** keeps for itself no browser recovers |
| 4 | ⭐ **The clipboard can be watched, since January 2026** | `clipboardchange` is in Chrome 144, and was motivated **explicitly by remote desktop clients** `[S]` — §5 |
| 5 | ⛔ **The browser's compositor costs 25-42 ms at 60 Hz** | `[?]` 1.5-2.5 frame intervals between the draw and the lit pixel — **more than our whole cap**. And no JavaScript API sees it — §6 |

#### 1.2 ⛔ And the four convergences between reports, which none of the four could see on its own

They are the reason this document exists beyond the four reports.

> ⚠ **And they are the most fragile part, by construction**: neither of the two authors validated them.
> *Reviewed on 9 August 2026 by review **R2** (`web/rapporti/R2-revisione-web.md`), which
> weakened one, scaled down another, added two that were missing, and established that a third
> **was not from the reports**: it was a thesis of mine presented as derived.*

**A. 10 bits has three contrary clues, and none is a measurement.**

| Where from | What it says |
|---|---|
| `DECISIONI.md` §2.3-bis | on Android's `mediacodec` path 10-bit support is limited and **the output goes back to 8** `[S]` |
| **S2** | ⚠ `[S]` **not `[R]`, and not verified**: that on hardware-decoded frames `VideoFrame.format` is **null** comes from a W3C discussion of **January 2023**, and S2 §3.7 declares it **could not establish the state of Chromium in August 2026**. *Mark corrected by R2: it had been promoted to `[R]`* |
| **S4** | WebGPU's zero-copy condition is literally `format == PIXEL_FORMAT_NV12` `[R]`: **P010 does not pass**. And the 2D canvas has a helper called `DownShiftHighbitVideoFrame` `[R]` |

⚠ **They are three different chains** — the codec, the API, the drawing — and R2 tried to collapse them into
one without succeeding. ⛔ **But they stand on two and a half legs, not on three**: the middle clue is
a source from three years ago.

**Hence, and the form matters**: `DECISIONI.md` §2.2 — the 10-bit wish, decided by the user
on 8 August — **is flagged as to be verified**, and the verification is the first thing the bench of
phase 2 establishes. ⛔ It is not rewritten as provisional on this basis: R2 is right to say that *«una
decisione dell'utente si sposta con tre indizi, non con due indizi e una fonte di tre anni fa
promossa di marca»* — and it is the very `LEZIONI.md` §2.3-quater I had cited in support.

⚠ And the difficulty closes on itself: **from the browser 10 bits are not readable**, so the
final proof is **looking at a gradient**, that is `LEZIONI.md` §2.4 — the yardstick is what you see.

**B. The PWA ties S1 and S3 — and it is worth less than I had written.**

| | |
|---|---|
| **S1** | behind a certificate exception, on Chrome **the Service Worker does not install** `[R]` ⇒ no PWA |
| **S3** | in an **installed PWA** Chrome's list of reserved keys is **empty** `[R]` |

> ⛔ **I had concluded «compra la tastiera intera». It is too strong, on four points** *(R2)*:
>
> 1. the empty list is **the browser's**, not the system's: on macOS `⌘Spazio` and `⌘Tab`, on
>    Android and DeX **every combination with Meta**, remain lost on any configuration `[R]`;
> 2. the marginal gain is **small**: in full screen Chrome's reserved ones are already only two,
>    and one of the two — exiting — the **specification requires** to reserve. Between «full screen + lock»
>    and «PWA» what changes is `F11` and little else;
> 3. it holds **only on Chrome**: on Firefox the six reserved ones remain, on Safari the PWA does not come into it;
> 4. ⛔ **and on the primary use it is a `[?]`**: whether it also holds for Chrome for Android nobody knows
>    — §5.5 of this very document declares it, and in §1.2 I had taken it as given.
>
> **What remains true**: the real certificate removes the warning **and** opens the road to the PWA, which
> on desktop Chrome recovers a few more shortcuts. It is an advantage, not a different category.

**C. ⛔ The shape of the page is decided by two constraints that collide** *(added by R2)*.

| Where from | The constraint |
|---|---|
| **S3** | the letters must come out of `beforeinput`, and this forces the page to have **an editable element with focus** — on desktop too, not only on Android. Without it, **accents and dead keys are not produced** `[R]` |
| **S4** | ⛔ **no elements over the canvas**, or the overlay path and the desynchronized canvas fall `[S]` `[R]` |

**The concrete case**: the page is written with the canvas alone, you reach phase 4, you discover that
`^`+`e` does not produce `ê` on any engine, you add the hidden field over the canvas — and **you
lose the drawing road on which all of §6 is built**. ⭐ It is precisely the rewrite that §6.1
says it wants to avoid, and **the synthesis was the only place where it could be seen**.

**D. ⛔ The background tab freezes after five minutes** *(added by R2; it was in S2 §3.8
and I had not reported it)*.

A group of pages is **frozen** if it stays hidden and silent for more than **five minutes**,
and the documented exemption requires an open WebRTC channel or a live media track `[S]`.
⛔ **The architecture of §6.1 — WebTransport and nothing else — does not fall within the exemption.** S2 marks it as
*«decisione di architettura da prendere adesso, non quando ci accorgeremo che la sessione muore
dopo cinque minuti»*.

⚠ **And it touches a promise**: `SPECIFICHE.md` §5.3 says that a client silent for 30 seconds **is
detached**. A frozen tab is silent — so the phone in the pocket detaches by itself. It is not a
defect (the session survives, `DECISIONI.md` §4.1), **but it is a behaviour to be declared**, and
today it is not written anywhere.

**And a thesis of mine, which must be attributed instead of passed off as a conclusion of the reports** *(R17)*:
`DECISIONI.md` §2.7 requires declaring a fallback, and S2 shows that from JavaScript the truth about the
decoder is not readable `[R]` — **from which I propose** that the diagnosis live **in the product**,
because the user's device is the only place where the question has an answer. ⚠ In S2
self-diagnosis appears **inside just one outcome out of five**, not as a general conclusion: the thesis is
defensible, but it is mine, and it is error shape **E5** applied to reasoning instead of to data.

---

### 2. The map

| What | Version it was read on |
|---|---|
| **Chromium / Blink** | 151 |
| **Gecko / Firefox** | 151-153 |
| **WebKit / Safari** | 26.4 |
| WebTransport | Safari 26.4, **24 March 2026** — with it all three engines are there. ⚠ *The word «Baseline» this row carried does not come from any of the four reports: it was from the search of 9 August, and was removed because it is a technical term with a precise meaning (R2)* |
| WebCodecs `VideoDecoder` | Chrome **94+** on all platforms, **Android included** · Firefox 130+ · Safari 26+. ⚠ *The figure «Chrome per Android 147» was a contamination between two reports: 147 is the version of something else (R2)* |
| ⛔ **Firefox on Android** | `VideoDecoder` **absent in release** (Nightly only), HEVC absent `[S]` ⇒ **it cannot be a client**. It is missing from all the rest of this document, which elsewhere treats Firefox as one of the three engines served |
| Fullscreen Standard, `keyboardLock` | entered the WHATWG standard on **8 May 2026** |
| `clipboardchange` | **Chrome 144**, 13 January 2026 |
| The references read | Guacamole, noVNC, Xpra html5, Selkies, moonlight-web |

⚠ **This chapter ages faster than all the other five.** Compositors move in
six-month cycles and Debian freezes them; browsers update themselves, on the user's
device, and **two of the five most important things in this study are from 2026**. Whoever re-reads
this file in six months **should redo the searches before trusting it**.

---

### 3. S1 — The certificate: the exception does not cover the session

*Detail: `web/rapporti/S1-certificato.md`.*

#### 3.1 The answer, engine by engine

| | |
|---|---|
| **Chrome/Edge** | ⛔ **no**, and for two independent reasons. The user's exception lives in the browser process and is consulted by **a single point**, fed by the errors of normal requests: the WebTransport client **never queries it** `[R]` — absence verified **with a positive control** on a point where that mechanism is instead present. And Chrome's QUIC demands a root **built into the browser**: `ERR_QUIC_CERT_ROOT_NOT_KNOWN` |
| **Firefox** | ⛔ **no**, for a different reason: the exception **is** consulted on HTTP/3 too, and right afterwards the session closes if the root is not built in `[R]`. The only waiver written in the code is, literally, `serverCertificateHashes` |
| **Safari** | `[?]` **the open case**: its exception bypasses nothing, it puts the certificate **in the keychain**, and WebTransport goes through there. It could be the only one where the answer is yes. **Nobody has documented it** |

> ### ⛔ And Safari **has** `serverCertificateHashes` — the correction I had lost along the way
>
> *Finding R2, and it is the costliest of the seventeen because it had already gone into a
> decision document.* WebKit implemented it on **2 October 2025** (bug 300057, `RESOLVED FIXED`),
> the implementation is in `NetworkTransportSessionCocoa.mm` `[R]`, and it ships in **Safari 26.4**.
>
> ⛔ Report S1 devoted a box specifically to correcting the contrary claim — *«vera nel
> 2024, ripetuta nel 2026»* — and I **did not report it**, writing instead in `DECISIONI.md` §1.7
> that *«WebKit non implementa `serverCertificateHashes`»*. Corrected there the same day.
>
> **The two consequences:**
>
> 1. ⭐ **iPhone and iPad already have a road without a domain**, and it is **the same** as the other two
>    engines. It is not a platform to be rescued: it is a platform served;
> 2. measurement **S1a** loses first place. It no longer decides *«se iPhone ha una strada»* — it decides
>    **a convenience**: whether on Safari the exception is enough by itself, that is whether there one can do without
>    publishing the fingerprint. S1 §5.8 writes it: the fingerprint is used **always**, and a possible
>    tolerance from Safari would be **one more fallback, not a different path**.

⛔ **And this closes, with a hard technical reason, the proposal of having an authority of ours
installed** (`DECISIONI.md` §1.7): on Chrome **not even the system store is enough**, because
that root is not *built into the browser*.

#### 3.2 What was derived from it

| | |
|---|---|
| **the road** | `serverCertificateHashes`, promoted from safety net to **normal road** (`RCP.md` §4.1-bis) — ⭐ **and it holds on all three engines**, Safari 26.4 included |
| ⛔ **two certificates, not one** | a **long-lived** one for the page — it is the one the user's exception lives on — and a **short one, ≤14 days**, for the session, which rotates by itself. ⚠ Confusing them makes the warning reappear every two weeks |
| ⛔ **and the warning comes back anyway every seven days** | `[R]` `kCertErrorBypassExpirationInSeconds = 604800`, with the comment *«Certificate error bypasses are remembered for one week»*. ⚠ *This row was missing, and with it the consequence: **even keeping the page certificate fixed, on Chrome the click is redone every week**. It changes the sentence said to the user (R2)* |
| ⭐ **one thing that falls away and simplifies** | `Alt-Svc` **has nothing to do with it**: WebTransport opens its connection by itself `[S]`. The silent fallback to TCP that had been declared as a danger **cannot happen** |
| ⛔ **the price of the exception** | behind it, on Chrome, **the Service Worker does not install** `[R]` — and see §1.2 B |
| ⏳ **two things S1 leaves to be decided, and that I had kept quiet about** | **(1)** Safari is the only engine with WebTransport also over **HTTP/2 and TCP**: our server does not speak it, so its fallback would end in an error — *it must be decided* whether to implement it or declare Safari out of the fallback. **(2)** an already open page holds **a fingerprint that ages**: on reconnection after rotation it must be reloaded or the current fingerprint must be requested — *it must be decided where this update lives in `RCP.md`* |

#### 3.3 The bench

⛔ **The positive control I had written was blind, and it is the most serious finding of the review**
(R2, finding R1). It said: *«la stessa prova su Chrome deve fallire»*. With **UDP port 7447
closed in the firewall**, the test fails on Safari *and* fails on Chrome — that is **the control is
green** — and the bench concludes «Safari's exception does not cover», which is the wrong conclusion on
missing data. It is «empty» and «forbidden» looking the same (`LEZIONI.md` §1.9), put in first
place in the project.

**The right control, which S1 had written and which I had replaced**: on the **same browser**,
on the **same page**, in the **same round** — the exception is tested alone *and* the
connection with the published fingerprint is tested. The second **must succeed**: if that one fails too, you
are not measuring the exception, **you are measuring a server that does not answer**.

> #### ⛔ And the controls are three, not one — the cure had stayed half done
>
> *Added on the night of 9 August 2026, finding **R3.1** of the review of the phase 1 bench.
> The cure for finding R1 had put back the control that says **yes** (P2) and not those that say
> **no** — and it is the same shape, one level lower.*
>
> | | |
> |---|---|
> | **P2** | the connection with **the published fingerprint** must **succeed** |
> | ⛔ **P3** | the connection with the fingerprint **wrong by one byte** must **fail** |
> | ⛔ **P4** | a certificate regenerated at **30 days**, with its right fingerprint, must fail **because of its duration** |
>
> S1 §4.4, literally: *«**solo con P2 verde e P3 rosso** il risultato di P1 significa
> qualcosa»*, and on P3: *«**se riesce, il banco non distingue nulla**»*.
>
> ⛔ **The concrete case only P3 closes**: a page that considers «successful» the construction
> of the `WebTransport` object instead of waiting for `ready` — or that watches the wrong promise —
> makes **even** the test with the mangled fingerprint succeed. The bench writes `[M]` *«su Safari
> l'eccezione copre WebTransport»*, which is a **false** `[M]` against two `[R]` read in the code of
> Chromium and Gecko. P2 alone does not see it: it is green in both worlds.

⚠ **And the measurement has lost first place**: with Safari having `serverCertificateHashes` (§3.1), S1a
no longer decides whether a platform can be served — it decides whether there the fingerprint can be spared.

---

### 4. S2 — Decoding: v1's trap disguised as an API

*Detail: `web/rapporti/S2-decodifica.md`.*

#### 4.1 ⛔ The fact that matters most

| | |
|---|---|
| **on desktop** | `hardwareAcceleration: "prefer-hardware"` is a real proof: the broker **throws away entirely** the factory of software decoders `[R]` |
| ⛔ **on Android it is not** | when it does not find a hardware HEVC decoder, Chromium **deliberately** picks a software one from MediaCodec `[R]`, because it does not package one of its own |

**Hence**: a successful `prefer-hardware`, `powerEfficient: true` and correct frames are **all
compatible with the CPU**. It is error shape **E1** — necessary taken for sufficient — that is
exactly what killed v1.

⭐ **And the investigation did not stop at «I didn't find it»**: the datum **exists** inside Chromium
(`IsPlatformDecoder()`) and **appears in no JavaScript interface** `[R]`. It is not a
search that went badly: it is a fact.

#### 4.2 Support, and the stream format

| | |
|---|---|
| **HEVC Main10 in WebCodecs** | Chrome for Android since **108.0.5343.0** · Chrome on Linux only via VA-API since **108.0.5354.0** · Safari since 16.4 (video only) and fully since **26.0** `[S]` |
| field coverage 2026 | ≈ **85 %** in Main10 decoding — ⚠ and the author of the figure declares that it **does not distinguish hardware from software** |
| ⭐ **the stream format** | **Annex-B without `description`**: it is legal, it is **what `hevc_vaapi` already produces**, and in Chromium it **saves an allocation and a copy per frame** `[R]`. Three projects out of three do so; moonlight-web tries Annex-B **first** precisely on HEVC |
| ⚠ the hvcC trap | Chromium re-parses the SPS and **rejects the configuration** if the emulation prevention bytes fall in the wrong field `[R]` — one more reason not to take that road |

⭐ **The lazy road is also the right one**, and that is rare: no packager is written, nothing is
converted, and a copy is saved.

#### 4.3 The bench

A software decoder **passes the first five tests** and fails only on three:

| | |
|---|---|
| **throughput at saturation** | 4K60 Main10, and you watch where it stops |
| **a CPU canary** | a known job inside a worker, which slows down if the CPU is decoding |
| **the decay over ten minutes** | silicon holds, the CPU heats up and drops |
| ⛔ **control A** | VP9 forced **in software** — software by construction. If the bench does not declare it as such, its verdict on HEVC must be thrown away |
| ⛔ **control B** | ⭐ VP9 in **`prefer-hardware`** — **must be declared hardware**. *It was missing, and it is the one that says **no**: without it, a loosely tuned threshold lets MediaCodec's **software** HEVC pass as hardware, that is precisely what Chromium deliberately picks on Android (§4.1). S2 §4.4: «il banco è valido se, sullo stesso telefono, dichiara **software** il controllo A **e hardware** il controllo B. Finché non lo fa, **non pubblica verdetti**». Restored by finding **R3.1***, 9 Aug |
| ⭐ **control C** | **`is_software_codec` read via `chrome://inspect`**, in parallel to the indirect tests. ⛔ The datum **exists** in `media_codec_video_decoder.cc`, with the name coming from `MediaCodec.getName()`: *«il browser sa e non risponde»* is true **from JavaScript**, and the bench is not JavaScript. Giving it up on the primary use was an undeclared choice (**R3.13**) |
| ⛔ **and the outcomes are THREE** | ≥ 90 fps ⇒ hardware · ≤ 30 ⇒ software · **in between: verdict suspended**. A two-outcome bench promotes the uncertain band to certainty |

⚠ **And this bench does not stay in the lab** (§1.2 C): the same measurement, reduced, lives **in the
product**, because the user's device is the only place where the question has an answer.

---

### 5. S3 — Keyboard and clipboard: 2026 overturned the premises

*Detail: `web/rapporti/S3-tastiera-appunti.md` — 96 `[R]`, 103 `[S]`, 23 `[?]`, zero `[M]`.*

#### 5.1 ⛔ A line of `SPECIFICHE.md` §7.3-bis was wrong, and I wrote it

It said: *«la Keyboard Lock esiste solo su Chrome ed Edge, e solo a schermo intero»*, and that
`Ctrl+W`, `F11` and `Ctrl+Shift+I` are lost. **False on three points:**

| | |
|---|---|
| **it is no longer only Chrome** | `requestFullscreen({keyboardLock:"browser"})` entered the WHATWG Fullscreen Standard on **8 May 2026**, and **Safari 26.4** and **Firefox 151** shipped it `[S]`. Chrome/Edge stay on the old `navigator.keyboard.lock()`: ⚠ **the page must know both** |
| **much less is lost** | Chrome's reserved list is **twelve** commands; **in full screen it drops to two** — `F11` and exit — **without calling any API** `[R]`. Firefox has **six**, Safari **zero** (but it filters in full screen, and ⭐ **this explains noVNC's old comment about Safari**) |
| ⭐ **in an installed PWA it is empty** | `// In Apps mode, no keys are reserved` `[R]` |

#### 5.2 What is really lost

| | |
|---|---|
| `Ctrl+Alt+Canc` | everywhere, and it is not recoverable |
| exiting full screen | by construction: it is the user's escape route |
| ⛔ **on macOS, all system shortcuts** | there is no hook — the function that should provide it **returns `nullptr`** `[R]`, and the system check precedes the lock |
| ⛔ **on Android and DeX, any combination with Meta** | by AOSP rule — ⚠ and **DeX is the declared primary use** (`DECISIONI.md` §5-bis.0) |

#### 5.3 The clipboard: the «cannot be watched» hypothesis is outdated

| | |
|---|---|
| ⭐ `clipboardchange` | **Chrome 144, 13 January 2026** — and the motivation written in the proposal is **remote desktop clients** `[S]`. It carries only the MIME types, it wants focus |
| ⛔ **it does not exist on Firefox and Safari** | verified, not deduced. There every read costs the «Paste» menu with **one second of waiting** |

#### 5.4 ⭐ Three gifts from reading other people's code

1. ⛔ **The cure for the modifier left down**, which for us is the most serious defect because **the
   session survives the connection**: Guacamole resynchronises the modifier state
   **from mouse events** `[R]`. There is no other way, and nobody would have invented it;
2. Chromium's `KeyboardEvent.code` → **evdev** table, canonical and **without gaps from 1 to 94**
   `[R]` — that is the conversion `RCP.md` §7.3 requires, already written and verifiable;
3. the race between `Ctrl+V` and the clipboard read, which **all three** references defuse
   by hand — Xpra delays **every keystroke by 100 ms** `[R]`. ⚠ For us 100 ms is **twice the
   delay cap**: that cure is not copied, it is replaced.

#### 5.5 The two `[?]` that matter most

Both on DeX, which is the primary use: **whether the lock works on DeX** (it exists only since Android 16
QPR1) and **whether the PWA also holds on Chrome for Android**.

---

### 6. S4 — The drawing delay

*Detail: `web/rapporti/S4-ritardo-disegno.md`.*

#### 6.1 The road — ⛔ **no longer a prescription: a measured decision** *(13 August 2026)*

*⛔ This paragraph was written before any line of the page, and it prescribed. In phase 3 it was
**implemented and measured**, and the measurement split the prescription into two halves with opposite outcomes.
The original text is kept below because the part that holds is still that one.*

`drawImage(videoFrame)` **inside the decoder callback** — ⛔ **not** on
`requestAnimationFrame`. Zero copies in CPU if the frame is 8-bit NV12; one colour
conversion in GPU `[R]`. It is also the only one that works on all three engines.

| the prescription said | outcome `[M]` 13 August |
|---|---|
| ⭐ paint **inside the decoder callback**, not on `requestAnimationFrame` | ✅ **it holds, and it is the half that counts** |
| ⭐ **decoding** off the main thread | ✅ **IT COUNTS, and it is measured**: `[M]` **−3.44 ms** (7.17 → 3.73) |
| ⛔ the **canvas** off the main thread | ⛔⛔ **IT SINKS THE BILL**: `[M]` **+17.6 ms** on drawing, plus **+10.2** on stream delivery |
| the **desynchronized** 2D canvas | ⚠ **it was never switched on in the product**: `src/pagina.html` has `desynchronized` **off** `[R]`, and the road to switch it on (`?tela=desincronizzata`) **does not exist** — it is not a switch turned off, it is a switch that isn't there. ⇒ It is not a rejected prescription: it is a prescription **never carried out**, and the gain remains `[?]` |

> #### ⛔⛔ The worker: implemented, measured — and **wrong BY HALF, not entirely**
>
> *`[M]` same machine, same session, **same page** (only the switch changes), same
> instrument re-run for the «before» and for the «after». Two rounds of «before», to know how much the
> noise is worth: **5.9 ms**, and the effect exceeds it **five times over**. Clock error ±0.63-0.65 ms.*
>
> | delay draw → glass | n | p05 | **median** | p95 | p99 |
> |---|---|---|---|---|---|
> | BEFORE-A (main thread) | 432 | 58.85 | **73.66** | 99.53 | 218.46 |
> | BEFORE-B (repeated) | 492 | 53.93 | **67.79** | 88.51 | 98.16 |
> | ⛔ **AFTER (worker)** | 483 | 84.48 | ⛔ **101.30** | 126.13 | 157.82 |
>
> ⇒ **+27.6 / +33.5 ms of median.** ⛔ But the total hides the thing that is needed, and the breakdown
> shows it:
>
> | stretch (median, ms) | BEFORE-A | BEFORE-B | AFTER | Δ |
> |---|---|---|---|---|
> | stream complete → `decode()` | 0.07 | 0.06 | **10.23** | ⛔ **+10.2** |
> | ⭐ **decoding** | **7.17** | 6.13 | ⭐ **3.73** | ⭐ **−3.44 / −2.40** |
> | callback → drawing finished (`drawImage` ×2) | 9.63 | 9.11 | **27.19** | ⛔ **+17.6** |
> | **sum of the three** | 16.87 | 15.30 | **41.15** | **+24.3 / +25.9** |
>
> ⭐⭐ **⇒ §6.1 is not wrong entirely: it is wrong by half. DECODING counts, not the CANVAS.**
> The decoder **delivers sooner when it does not contend** — `[M]` **−3.44 ms**, and it is a real
> gain, not a rounding. It is the **canvas** that sinks the bill, and on its own it is worth **+17.6**.
> ⇒ ⛔ **The usable line is not *«the worker is wrong»***, which would only be a closed door:
> it is ***«decoding yes, canvas no»***, which tells whoever comes next where to put the boundary.
>
> #### And the painted frames, mandatory alongside (`LEZIONI.md` §6.2)
>
> | | real chain (P7) | saturation 1080p | saturation 480p |
> |---|---|---|---|
> | main thread | 22.8-24.2 /s | **127.6** /s | **230.6** /s |
> | worker | **26.3** /s | **33.9** /s (−73.4 %) | **56.4** /s (−75.5 %) |
>
> ⚠⚠ **The two quantities say OPPOSITE things**: on the real chain the worker paints **more** (it is the
> queue), but at saturation the cap **collapses by three quarters**. Whoever looked at only one would read
> half of the fact — and **which half depends on which quantity they chose first**.
>
> #### ⭐⭐ The mechanism, and it is the discovery that changes a RULE
>
> Extra cost per frame **13.4 ms at 480p** and **21.7 ms at 1080p**; and at 480p the worker stops at
> **56.4 paints/s ≈ the 60 Hz frame**, while the main thread does **230.6**.
> ⇒ ⛔ **`transferControlToOffscreen` commits the canvas to the frame rhythm: it is an
> implicit `requestAnimationFrame`.** The worker prescribed by this paragraph reintroduces **in
> silence** precisely the frame skip that the paragraph forbids out loud.
> ⛔⛔ **The prescription contained its own refutation, and no re-reading of the document could
> notice it without measuring it.**
>
> ⇒ ⛔ **The ban extends TO THE MECHANISM, not to the word.** It is not enough to «not call
> `requestAnimationFrame`»: **any road that delivers at the frame rhythm is forbidden in the
> same way**, and whoever takes it pays the frame without ever having named it.
>
> #### ⏳ `[?]` And this must be read NEXT TO the numbers, not at the bottom
>
> ⛔⛔ **Everything is measured on Xvfb, in software, WITHOUT a GPU**, and the penalty is largely
> **synchronisation to the frame**. ⇒ **On real hardware the bill must be redone BEFORE burying
> §6.1**: these numbers close the road for today, **not forever**.
> ⏳ `[?]` And a `WebTransport` opened **inside** the worker would remove the **+10.2** of the delivery
> stretch, ⛔ **not** the **+17.6** of drawing — which are the ones that decide.
>
> ⇒ ⭐ **The code stays in the tree behind `#video=worker`, OFF**, precisely so that on the day of the
> real GPU the number is redone without rewriting anything (`DECISIONI.md` §2.8).
> ⚠ **And the switch reads the FRAGMENT, not the query string**, and it is a consequence of a
> defect: `?video=worker` gets **404** (`src/pagina.c` · `servi()`). The syntax with `?` will become valid again
> when that defect is cured.

⚠ *The line «e impone la forma della pagina: il video vive nel worker, l'input nel thread
principale» **falls with the worker**: today video and input are both on the main thread, and
the boundary this paragraph said had to be decided at once no longer exists. ⛔ If the worker
came back, that boundary comes back too — but it will have to come back with a new measurement, not with this line.*

#### 6.2 The piece that is not ours and is felt all the same

`[?]` Between the draw and the lit pixel pass **1.5-2.5 frame intervals: 16-40 ms at 60 Hz**,
that is **as much as our whole cap**. The cap «only for the piece that is ours» remains legitimate
(`DECISIONI.md` §2.4), but **that line must be written next to the cap** or one thing is promised and
the user feels another.

⭐ **The lever, if it were needed**: Selkies and moonlight-web do not paint on a canvas — they send the frames
to a `<video>` element to take the **overlay** path, which skips the compositor `[R]`. It goes
behind a switch that is off, not written first. ⚠ Xpra and noVNC stay on the canvas, and **neither
of the two declares a delay figure**.

> ⛔⛔ **And on Xvfb this blind piece DOES NOT EXIST** — *13 August 2026, and it holds for every browser bench
> of the project.* The 16-40 ms are the time between the draw and the **pixel lit on a screen**. On
> Xvfb there is no screen, there is no scanout, and **`requestAnimationFrame` never runs**: `[M]` **0
> frames in 3 seconds**, with and without a GPU, with `visibilityState` at «visible».
> ⇒ ⛔ **The 16-40 ms estimate is declared next to the numbers meant for the user, and NOT next to the
> bench numbers.** Adding it to a measurement taken on Xvfb inflates the total by a piece that is not
> there; removing it from a number promised to the user deflates it by the same piece. It is the same
> number, and the two errors have opposite signs.

#### 6.3 The bench, and its blind piece

The loop of `DECISIONI.md` §2.6 is built like this: `t0` before sending, `t1` as the **first line**
of the decoder callback, then you draw, and **only afterwards** you read the mark with a
read of 16×16 pixels. ⛔ **That order is binding**: reading first would be a readback from the
GPU, and would distort the measurement it is taking.

| | |
|---|---|
| ⛔ **P1, the decisive control** | the server delays by **N known milliseconds**, and the median **must rise by exactly N**. A bench that does not do this does not know it is measuring |
| ⛔ **P2 and P3, and P3 had fallen** | **P2**: the detector finds the colour **that is there**. ⛔ **P3**: it does **not** find the one that **is not there**. *S4 §4.2: «se dice sempre sì, si sta misurando zero e si è felici a torto» — and a detector that always says «I saw the mark» **passes P1 too**, because the N ms add up identically. Restored by finding **R3.1***, 9 Aug |
| ⛔ **P5, out of order** | frames arrive on independent streams: a loop that does not cope with it measures the queue instead of the delay. ⛔ **13 August: P5 WAS NOT RUN, and now it says so.** After three injectors `scavalcati = 0` — and *«zero fuori ordine»* is not «the loop holds», it is **«the phenomenon did not show up»** (`LEZIONI.md` §1.9). Before, the bench declared it **green** |
| ⭐ **P5 — and the cause of out-of-order is measured** | ⛔ **it does not arise (only) from the network: it arises from the SIZE of the frame.** `stream_video` fires on **completion** of the stream ⇒ the arrival order is **the order of sizes**, not that of departure, and **a big keyframe is overtaken by the deltas** that leave after it. ⚠ And the protocol pays the bill: an overtaking **costs a keyframe** (`RCP.md` §5.2, §6.2 — «la regola dell'ordine si applica prima di quella della misura»). ⇒ An injector that delays packets does not reproduce the phenomenon: **whoever changes the sizes reproduces it** |
| ⛔ **P6, the clock grain** | without the two cross-origin isolation headers, on Firefox and Safari the timers fall on a **1 ms** grid — on a cap of **50**. ⚠ And `SPECIFICHE.md` §11.5 makes it a **product constraint**, not a bench tuning (O11) |
| ⛔ **P7, the rate as a path control** | the delivered rate says whether you are measuring the road you think |
| ⛔ **where the measurement ends** | ⛔ **at the finished drawing, not at the decoder callback.** *Corrected on 13 August 2026: the first draft closed at the callback, giving itself **~11 ms** of ours, measurable, on a cap of 50. The number rose from **63.8 to 74.6** and it was let rise.* ⇒ The boundary moves **in the uncomfortable direction**, or the yardstick works for whoever holds it |
| ⛔ **the blind piece** | the measurement ends at the drawing; the pixel lights up `[?]` 16-40 ms later, and **no JavaScript API sees it**. It is estimated, and **the estimate is declared next to every number** instead of pretending the number is the total. ⛔⛔ **But on Xvfb that piece does NOT exist** (§6.2): the estimate holds for the user's screen, **not for the bench** |
| ⚠ **and a single measurement is worth nothing** | one works **with distributions**, not with samples |

---


### 7. The measurement plan

In order, and each with its positive control. **None requires a line of product code.**

| # | The measurement | Why first or later |
|---|---|---|
| **S1a** | does the exception on **Safari** let WebTransport through? (macOS and iOS separately) | ⛔ **the first**: it decides whether iPhone and iPad have a road without a domain |
| **S1b** | how long the exception lasts on Chrome | it changes the sentence told to the user: «una volta» or «una volta a settimana» |
| **S2** | HEVC Main10 in hardware **on the real phone** — saturation, canary, decay | it decides what the page declares, not whether the project exists (`DECISIONI.md` §2.7) |
| **S3a** | the Keyboard Lock on **DeX** | it is the primary use, and it is a `[?]` |
| **S3b** | the PWA on Chrome for Android | it is worth the whole keyboard (§1.2 B) |
| **S4** | the delay loop, with the known delay as control | it gives the number, and **the measurement of the blind piece** |

> ⛔ **And three probe labels were NOT born here**, contrary to what `FASI.md` §01-filo-nudo
> declared: **S5** (the canvas the client declares), **S6** (the payload of a datagram) and
> **S7** (the sign of the wheel) do not appear in **any line** of this document — `[M]` 11
> August 2026, `grep -cE '\bS5\b|\bS6\b|\bS7\b' web.md` → **0**, with the positive control beside it
> (the six labels of the table above appear **24** times). They were born in the document of
> phase 1, from the questions of `SPECIFICHE.md` §6.1-bis, `RCP.md` §5.3 and `RCP.md` §7.3, and **refer back
> there**. ⚠ *Written here on 11 August 2026, finding **R12C.10**: the wrong sentence was the one that
> sets the cross-reference convention, and whoever looked for the procedure of S5, S6 or S7 in this §7 would not
> have found it.*
>
> ⭐ **And the outcomes of what was executed are in `web/rapporti/S-esiti-sonda.md`** — the
> fifth file of that folder, which is not a study report but **the only one carrying measured
> numbers**: S7 complete, S1b started, S5 halfway, and the recount that says which numbers have a
> provenance on disk.

⛔ **And all on the real device.** «Il Chrome del portatile lo fa» says nothing about the Chrome of the
phone: it is error form **E10** in a new disguise (`DECISIONI.md` §5-bis.0-ter).

---

### 8. ⏳ What this study does NOT know

*Listed so that it is not rediscovered as closed. Each report has its own list; these are the
items that touch a decision.*

| | |
|---|---|
| `[?]` Safari and WebTransport behind an exception | §3.1 — **and Apple does not even document whether the exception can be granted on iOS** |
| ⏳ ~~`[?]` the duration of the exception on Chrome~~ — **the measurement is STARTED** | ⛔ **it was not `[?]`, and this document contradicted itself**: §3.2 gives it as `[R]` from `kCertErrorBypassExpirationInSeconds = 604800`, that is **seven days**. *Corrected on the night of 9 August 2026, finding **R4.14**: whoever read §8 planned a measurement to **learn** the number, whoever read §3.2 to **confirm** it, and for a bench that must wait a week the difference changes the patience threshold.* What remained to measure was **how well that `[R]` holds in the field** — ⭐ **and the measurement has been running since 10 August 2026, 21:10:01 UTC**, on **Chrome 151.0.7922.108** with a persistent profile: `banchi/01-s1b-eccezione.sh`, log `banchi/01-s1b-stato.jsonl`, outcomes in `web/rapporti/S-esiti-sonda.md` §2. ⭐ **And on 11 August 2026 the measurement answered, without waiting for the verdict of the 17th**: `01-s1b-eccezione.sh scavalca`, **6 checks out of 6**. ⚠ The objection written above was right — *«la contabilità di Chrome non è il comportamento»* — and it is **exactly that** which the new round closes: on a **copy** of the profile the expiry was rewritten **to yesterday**, and the page **no longer opens**; rewritten to **+30 days** (same tampering, opposite sign) it still opens. ⇒ Chrome **honours** the instant it records. And the expiry read back **after a visit** is identical: **it does not renew** — the question the seven-day clock could not ask, because the page visits it every day. ⇒ **The user is told «una volta a settimana»**. ⏳ The 17-18 August remains as independent confirmation: the real profile was not touched |
| `[?]` the 10 bits all the way to the screen | §1.2 A — and **it is not verifiable from JavaScript** |
| `[?]` the Keyboard Lock on DeX, and the PWA on Android | §5.5 |
| ⛔ ~~`[?]` the 16-40 ms of the compositor~~ — **it stays open, but NOT where it was believed** | §6.2 — no API exposes them, and this has not changed. ⛔ **What changed is where they apply**: `[M]` 13 August, **on Xvfb `requestAnimationFrame` never runs** — **0 frames in 3 seconds**, with and without GPU, `visibilityState` «visible». Without a screen there is no scanout ⇒ **on Xvfb the blind piece does not exist**. The estimate is declared beside the **user's** numbers, not beside the bench's |
| ⏳ ~~`[?]` how many streams per second each browser sustains~~ — ⭐ **there is a number, for one browser only** | `RCP.md` §2.3 — video consumes one per frame. `[M]` 13 August, **Chrome 151 on Linux**: **60.0** frames painted per second when offered 60 (that is 60 streams/s, without losses), and **127.6/s** as **cap at saturation**. ⛔ **It stays `[?]` on Firefox and on Safari**, and it is the same `[?]` as `SPECIFICHE.md` §11.5: the bricks stand on two engines, the numbers on one |

---

### 8-bis. ⛔ The twelve things the reports said and this synthesis kept quiet

*Brought over on the evening of 9 August 2026, findings **O1-O12** of review R2. ⭐ It is the part that
no citation check finds, because there is nothing to check: the line was not there.*

| # | What | Where it goes, and what it changes |
|---|---|---|
| **O1** | ⛔ **the background tab freezes after 5 minutes**, and the exemption wants a WebRTC channel or a live media track `[S]` — which WebTransport alone is not | §1.2 D, and `SPECIFICHE.md` §5.3: **a frozen client goes silent, so it gets detached**. It must be declared, not discovered |
| **O2** | ⛔ **AV1 is a dead end from both sides** — our hardware does not encode it `[M]`, and in decoding it adds nothing HEVC does not give | `SPECIFICHE.md` §11.4: it stays in the preference ladder **as a door for tomorrow's hardware**, not as a road to try. ⚠ A dead end not written down is a dead end walked again (`LEZIONI.md` §8) |
| **O3** | ⚠ **HDR is not promised**: BT.2020/PQ makes zero-copy fall, and the one-copy path converts with a washed-out result `[S]` | `SPECIFICHE.md` §11.4: ⛔ **we encode BT.709**, and it is a choice of the server, not of the client |
| **O4** | ⛔ **dropping a delta gives no error to the decoder**: the corruption propagates silently until the next keyframe, and abandoning without breaking would need **temporal sub-layers** `[?]` — to be verified on Intel's `EncSliceLP` | `RCP.md` §5.2, which already imposes the keyframe after an abandonment: the new line is **why** that obligation is not optional |
| **O5** | Safari is the only engine with WebTransport also over **HTTP/2 and TCP**, and our server does not speak it: its fallback would end in an error | §3.2 — **it must be decided** whether to implement it or declare Safari out of the fallback ✅ *brought over* |
| **O6** | the page already open holds **a fingerprint that ages**: after rotation it must be reloaded, or the current fingerprint must be requested | §3.2, and a line is needed in `RCP.md` on **where that update lives** ✅ *brought over* |
| **O7** | ⭐ **on-screen buttons are a requirement, not a makeshift fallback**: three mature references out of three give the user a way to send what the browser does not let through | `SPECIFICHE.md` §7.3-bis: `Ctrl+Alt+Canc` is not «non recuperabile», it is **recoverable another way** |
| **O8** | ⛔ **the states are three, not two**: delivered · **delivered *and* reserved** · not delivered. The second is the worst — the session receives the keystroke **and** the tab closes | §5.2, and it reformulates measurement **S3**: the question is not «arriva?» but «arriva **e basta**?» |
| **O9** | ⛔ **on iPhone fullscreen is partial in all versions** `[S]`, and without fullscreen **there is no keyboard lock** | §5.2: on iPhone the **whole** keyboard game is lost, not a few shortcuts |
| **O10** | ⚠ the lock **does not exist if fullscreen was entered with `F11`**, and **switches itself off on loss of focus** — that is exactly at the instant the modifiers stay down | §5.4: ⭐ and the cure **requires no protocol** — the client sends the release of everything it has pressed when it loses focus, and on reattach `RCP.md` §7.3 takes care of it |
| **O11** | cross-origin isolation (COOP+COEP) is a **product rule**, not a bench calibration: it changes how resources are served | §6.3 demoted it to «tarare il righello». It goes into `SPECIFICHE.md` as a constraint on how the server serves the page |
| **O12** | the correct level string for the target is **5.1**, not 5.0 — and above 40 Mbit/s the **High** tier is needed | it is the parameter **the server must emit**: `RCP.md` §4.3, beside the codec |

⛔ **And the lesson that holds them together**: a faithful synthesis in ninety points that keeps quiet a constraint
produces **a plan that discovers it halfway through the work**. It is not a defect of accuracy — the twelve lines
above contradict nothing of what was written: **they were not there**.

### 9. The lessons this study adds

1. ⭐ **An old lesson reappeared one level higher.** `LEZIONI.md` §1.11 says that a
   **necessary** condition is not **sufficient** — and it was born on «il processo ha aperto un render
   node ⇒ rende in GPU». Here the same form returns dressed as an official API:
   `hardwareAcceleration: "prefer-hardware"` **succeeding** does not say the decoder is
   hardware. ⛔ **Changing layer grants no immunity**: an API's promise must be treated like the
   declaration of a compositor.
2. ⛔ **The component we cannot query must be diagnosed by the product.** With the
   compositors, when indirect proof was not enough, we asked them (`LEZIONI.md` §1.11,
   second rule: *«se il componente sa rispondere, gli si chiede»*). **The browser knows and does not
   answer** `[R]`. When that happens, the measurement cannot stay in the lab: **it must live in the
   product**, on the user's device, which is the only place where the question has an answer.
3. ⚠ **A chapter that ages in months, not years.** Compositors are frozen by Debian; browsers
   update themselves, and **two of the five most important things in this study are from
   2026** — one from May, one from January. `LEZIONI.md` §9 point 8 says to update documents when
   a measurement contradicts them; here it must be added that **even without measurements, this file expires**.
4. ⭐ **Whoever reads other people's code finds cures nobody would invent.** Resynchronising the
   modifiers **from mouse events** (§5.4) cannot be deduced: it is found only by looking at how
   those who came before solved it. It is point 0 of the recipe that keeps paying — and for the
   second time in two days **it was triggered by a sentence of the user**, not by a search of ours.


---

# Part II — The five desktops


<a id="gnome"></a>

## GNOME as a desktop — study of the code, for phase 11

*Written on 8 August 2026, with ten parallel searches on the sources cloned at the versions of Debian
Trixie. It is the eighth study of the project, and it closes the round of the four desktops.*

> ### ⚠ Why this study exists, and why it comes last
>
> GNOME is the desktop REMOTIX has served **in production for ten phases**. But the document we had —
> §gnome-remote-desktop — studies **GNOME's RDP server**, that is a competitor, **not the
> desktop**. Session, lock screen, power, dangerous entries, configuration: on KDE, XFCE and
> LXQt we studied them all; on GNOME **never**, because nobody had forced us to.
>
> ⭐ **The result is that this study finds more defects of ours than the other three
> put together** — and all on the desktop we considered finished.

> **The marks:** **[R]** read in the code, with `file:riga` — it is not a measurement · **[R-pkg]** read in the
> Debian package · **[M]** measured · **[?]** deduced · **[✗]** verified absent, with positive
> control · **`[≠]`** ⚠ **the code contradicts one of our documents**.
>
> Detail in the ten reports in `reference-gnome/rapporti/`.

---

### 1. In two minutes

#### 1.1 ⛔ The seven things we have never done on GNOME

*Read in the product code on the server, read only.*

| # | | |
|---|---|---|
| 1 | **the drop-in of the Shell's unit** | `scrivi_dropin()` is called **only** `if (tipo == COMPOSITORE_KWIN)` (`src/sessione.c` · `scrivi_dropin()`). On GNOME the Shell starts with a bare `ExecStart=/usr/bin/gnome-shell`, **without `--headless`** |
| 2 | **power inhibition** | `energia_inibisci()` **returns NULL** on Mutter (`src/energia.c:112-113`) |
| 3 | **the lock screen** | zero keys, zero recovery |
| 4 | **the dangerous entries** | no lockdown — on KDE the user had asked for it and had got it |
| 5 | **the configuration** | **zero occurrences** of `gsettings`/`dconf`/`org.gnome.desktop` in the whole of `src/` |
| 6 | **`SPA_META_Cursor`** | we ask for `cursor-mode=2` (metadata) but we do not ask for the metadata ⇒ **the cursor does not arrive at all** |
| 7 | **`SPA_META_SyncTimeline`** | and **Mutter offers it** — it is the missing *release* of zero copy, that is the hunt of phase 9 in the right place |

⭐ **A single move pays for three**: a dconf profile in `$XDG_RUNTIME_DIR` closes together the lock
screen, the dangerous entries and the configuration (§6).

#### 1.2 ⛔ And the thing that keeps us standing today is an accident

**On GNOME the lock screen does not show a lock screen: it detaches the RDP session.**
Entering `unlock-dialog`, gnome-shell calls `inhibit_remote_access()` and Mutter — verbatim —
*«Any active remote access session will be terminated»*: it closes ScreenCast, RemoteDesktop and
InputCapture, **and refuses to recreate them**.

✅ **The exception is `is_headless()`.** And we are headless — **but not because we asked for it**: Mutter
degrades by itself when the logind session has no seat, with a `g_message`
(`meta-backend-native.c:759-764`). ⛔ **The precondition that saves us is not written in any line
of ours.**

#### 1.3 ⭐ And the discovery that reopens a hunt closed badly

**R29 is wrong: Mutter's DMA-BUF is not a «diff».** Two independent proofs in the code — the blit
copies **the whole** view framebuffer, and Cogl **deliberately empties the clip stack** before
`glBlitFramebuffer`; and for a virtual CRTC the view is a **single, persistent `CoglOffscreen`**,
not a swapchain, so partial redraw **accumulates** in it.

⭐ **Which explains why the cure made things worse**: the accumulation surface copied only the
damaged rectangles from a buffer that **already contained the whole frame**.

⭐ **And the real defect is the *release***: `can_reuse_pw_buffer` — the only point where Mutter waits for
us — **gives up at the first line** if `SPA_META_SyncTimeline` is missing, and reuses the buffer **while
VA-API is still reading it**. Two screens alternating is exactly the symptom one would
expect from that. And the reference does the opposite of what we had concluded: it **holds** the
`pw_buffer` until reading is done.

⚠ **It is a reading of code, not a measurement** — but it is consistent with all the symptoms, and the two candidate
cures are both small.

---

### 2. The map

| What | Where | Trixie version |
|---|---|---|
| the compositor | `reference-gnome/mutter/` | **48.7** |
| the shell | `gnome-shell/` | **48.7** |
| the session | `gnome-session/` | **48.0** |
| power, media keys, xsettings | `gnome-settings-daemon/` | **48.1** |
| the schemas | `gsettings-desktop-schemas/` | **48.0** |
| the display manager | `gdm/` | **48.0** |
| the competitor | `gnome-remote-desktop/` | **48.1** |
| the portal, the settings, dconf | `xdg-desktop-portal-gnome/` 48.0, `gnome-control-center/` 48.4, `dconf/` 0.40.0 | |

⚠ **[M] On the server GNOME is no longer installed** (`dpkg-query` → not-installed, no
`gnome.desktop`): **nothing in this study is verifiable on our machine today**, and the
restoration must be redone before any measurement.

---

### 3. The session without a monitor

*Detail: `rapporti/01-sessione-gnome.md`, `08-gdm-remote-login.md`.*

#### 3.1 ⭐ The simplest of the three families

| | |
|---|---|
| **Mutter** | ⭐ **no option needed**: if the logind session is of type `wayland`, active and **without a seat**, it goes headless **by itself** (`meta-backend-native.c:759-764`) |
| KWin | `--virtual --width/--height` mandatory; `--drm` from SSH **exits with status 1** |
| labwc | `WLR_BACKENDS=headless` mandatory |

⚠ **But the logind session must exist**, and `XDG_SESSION_ID` must be exported, or Mutter may
hook onto the wrong session. ⛔ **And `--virtual-monitor` is not optional**: in headless
`needs_outputs=false`, so without that option the session starts **alive, complete and black**.

**The form**: environment from scratch + drop-in on `org.gnome.Shell@wayland.service` with
`gnome-shell --headless --virtual-monitor WxH`, then `gnome-session --session=gnome`.

⛔ **`SHELL` must be set empty**: `gnome-session.in:3-14` re-executes itself inside a **login** shell if
`$SHELL` is in `/etc/shells` — that is it brings itself back inside `~/.profile`. It is `LEZIONI.md` §5 lying in wait.

#### 3.2 ⭐ Logout: a free sentinel, and a signal that does not exist

`gnome-session` **does not exit** after starting the target: it opens a fifo and sleeps, exiting exactly when the
session is torn down (`main.c:447-487`). It is the form of `labwc --session`: **it is watched with a
`SIGCHLD`**, without `RegisterClient`.

⛔ **[✗] `SessionOver` is declared in the XML and is NEVER emitted** — a single hit in all the
repositories, the line of the XML itself (positive control: `SessionRunning` is also there in the
implementation). Whoever had designed on top of it would have waited forever.

⛔ **`Logout(1)` is not enough**: it shows the dialog if an inhibitor exists. The farewell goes on **`Logout(2)`**.

**Readiness**: `SessionRunning` **plus** `IsSessionRunning()`, which exists precisely for the race between
subscription and event. ⛔ The name `org.gnome.Shell` is **not** an indicator: it is taken before
`meta_context_start()`.

✅ **[✗] No equivalent of XFCE's 8 s**: the chain is event-driven. ✅ **[✗] No
`loginctl terminate-session`, no subreaper.**

#### 3.3 ⭐ Found the line of the historic bus defect

The «session bus that gives no error, gives silence» of `LEZIONI.md` §5 has a culprit with a name and a
line: `gnome-session-shutdown.target` pulls `gnome-session-restart-dbus.service`, which does
`StopUnit("dbus.service")` on the user manager (`tools/gnome-session-ctl.c:130-133`). **The daemon
dies, the socket stays.**

⚠ And the reasoning that saves KDE — «user bus ⇒ it survives» — **is false here**, even though the
premise is true. **[?] Countermeasure to try**: mask that service (the link is `Wants=`, weak).

#### 3.4 ✅ GDM does not get in our way

All its manoeuvring on the VT is inside `if (seat_id == "seat0" && seat0_has_vts)`, and the only «kill» it
has acts only on sessions created by it. **A session without a seat it does not see: `gdm3` can
stay on.** It needs to be switched off only if one day we want a real seat.

---

### 4. ⛔ Revocation: the state GNOME has and the others do not

*It is the most important fact of the desktop chapter, and it has no analogues.*

| | |
|---|---|
| **what happens** | entering `unlock-dialog`, gnome-shell calls `inhibit_remote_access()` (`js/ui/main.js:136-145`); Mutter closes **ScreenCast, RemoteDesktop and InputCapture** and **refuses to recreate them** (`meta-remote-access-controller.c:146-164`, `meta-backend.c:1454-1468`, `meta-dbus-session-manager.c:349-353`) |
| **the exception** | ✅ `is_headless()` — true **only** with the headless backend (`meta-backend-native.c:361-369`) |
| **the recovery** | ⭐ it exists and **asks for no password**: `org.gnome.ScreenSaver.SetActive(false)`, or logind's `Unlock` signal. ⚠ It must be executed **by the REMOTIX process**, not by the client |

**The three defences, in order of strength:**

1. ⭐⭐ **do not run `gdm.service`**: the ScreenShield is created only if `canLock()`, which queries
   `org.gnome.DisplayManager` — **[✗] name not activatable via D-Bus**. Without GDM locking is
   **impossible**. ⚠ But on Trixie GDM **is active**, so on its own it is not enough;
2. **a session mode of our own**: the mode excludes `unlockDialog` ⇒ gnome-shell refuses to lock.
   ⛔ `parentMode:"user"` **puts it back**: it must be copied out in full;
3. **the lockdown** (§5).

⭐ **Hence question 16 for `LEZIONI.md`**: *«c'è uno stato in cui il compositore ci REVOCA quel che
ci ha già concesso, e chi ha il dito su quel pulsante?»* Question 3 asks whether there is a permission; this one
asks whether the permission **can be withdrawn while running**, and it is a different thing. On GNOME there is an API
dedicated to doing it.

---

### 5. The lockdown, the entries, the cursor

*Detail: `rapporti/02-shell-blocco-voci.md`.*

#### 5.1 ⭐ The lockdown is worth more than KDE's KIOSK

Of the eleven keys of `org.gnome.desktop.lockdown`, **four** are read by gnome-shell 48.7 and one
by gnome-session — and **the entry disappears**, it is not greyed out (`system.js:218-226` binds `can-*` to
`visible`), with the whole button hidden if they all disappear.

| key | effect |
|---|---|
| `disable-lock-screen` | removes «Blocca». ⛔ **It does not cover `SetActive(true)`** — known hole |
| `disable-user-switching` | removes «Cambia utente». ⛔ To be removed **always**: the action **locks before failing** |
| `disable-log-out` | ⭐ the most powerful: gnome-session answers `false` to `CanShutdown` ⇒ **Power Off and Restart disappear too**. ⛔ But it also refuses `SessionManager.Logout`: **our farewell must be redone passive** |
| `disable-command-line` | removes the Run dialog |

⛔ **[✗] Two keys not to set**: `user-administration-disabled` **is read by nobody**, and
`idle-activation-enabled` is deprecated and ignored.

⚠ **The lock shortcut is not `Ctrl+Alt+L`**: it is `<Super>l` plus `screensaver-static`, and **the two
lists are concatenated** — both must be emptied. ⚠ And as on KDE, the polkit rule for Suspend must be
written **`no`, not `auth_admin`**: `challenge` **shows** the entry.

#### 5.2 ⭐ The cursor: KDE's cure is not needed, and there is something better

On Mutter the cursor is not in the image **because we ask for that**: we declare `metadata` and Mutter
answers with `inhibit_cursor_overlay`. With `cursor-mode=1` it would be inside, as on KWin and wlroots.

⭐ **The right choice is `cursor-mode=2` (METADATA)**: clean pixels **and** shape, position and hotspot in a
side band, to be forwarded as a **native RDP cursor** — that is the thing we had had to give up on
KDE. ⛔ **But today we do not ask for `SPA_META_Cursor`, so that data does not arrive at all.**

⛔ And if one day the transparent theme were needed, **the channel is not `XCURSOR_THEME`**: Mutter does not
read it (the only relevant `getenv` is `XCURSOR_PATH`), it reads `org.gnome.desktop.interface cursor-theme`.
A worse trap than wlroots: an empty theme gives a **grey square**.

#### 5.3 ⚠ The dialogs that appear by themselves

Eight, and three really concern us: gnome-session's **fail-whale** (concrete trigger for us: the
failed GL check), the **welcome dialog** (switched off by setting a key, not by locking it),
and ⭐ the **accessibility dialog that our own input can trigger** (Shift pressed five times):
the gate is `org.gnome.desktop.a11y.keyboard enable`, which is already `false` on its own but **must be locked**.

✅ **[✗] And KWin's trap without outputs has no twins**: no placeholder, the pointer
constraint is a no-op, the keyboard is not touched. The virtual screen on GNOME is a precondition of
*drawing*, not of survival.

---

### 6. ⭐ dconf: the only configuration of the four desktops that holds

*Detail: `rapporti/04-dconf-configurazione.md` — and it is the only report with `[M]` measurements of its own.*

| | |
|---|---|
| **the locks hold** | `gsettings set` on a locked key **exits with 1** and says so: the check is **synchronous and local**, before the D-Bus message leaves. ⭐ Where xfconf exited successfully and restored silently |
| **they win over the user's value** | **[M]** user `true`, lock and db `false` ⇒ `gsettings get` answers `false`: the value at home is **skipped on reading** |
| ⭐ **no root needed** | `$XDG_RUNTIME_DIR/dconf/profile` is the third loading priority. **[M]** with the file written the session sees values and locks; deleted, everything goes back as it was; **zero bytes written in `~`** |

**The three traps, all measured:**

1. ⛔ **`.gschema.override` is not an alternative**: it changes the *default*, which sits **below** the
   user's value — and the user already has `lock-enabled=true`, which is always the real case;
2. ⛔ **an ephemeral `XDG_CONFIG_HOME` fails silently**: `dconf-service` is a separate process with
   **its own** environment ⇒ the write succeeds and ends up **in the real home**;
3. ⛔ **a lock without a value does not freeze: it resets to the vendor default** (600 → 300). Every
   locked key must **also** be given a value.

⚠ And two details that cost an afternoon: a lock line **without a leading `/` is silently
discarded** (the only check is `gsettings writable` key by key), and **`file-db:` never re-reads**
while running — if live reloading is needed then `system-db:` is needed, and therefore root.

⭐ **The precedent to copy is GDM, not `gnome-remote-desktop`**: GDM does exactly this — profile
in the launch environment, `file-db:`, **28 locked keys** **[R-pkg]** — and from there we steal two lines
we would not have thought of: clearing the lock shortcut **as well as** disabling it, and neutralising
the default terminal.

⛔ **[✗] `gnome-remote-desktop` does not configure the session at all**: no profile, no lock,
no inhibition. **The void is ours, we are not duplicating anything.**

---

### 7. ⛔ Power: the server falls asleep

*Detail: `rapporti/03-energia-inibizioni.md`.*

**The upstream *and* Debian default of `sleep-inactive-ac-type` is `suspend`, with a 900 s timeout**, and
`gsd-power` calls `logind Suspend(false)`.

⚠ **Today it does not bite us, but by accident**: `SessionIsActive` is false because no graphical logind
session exists, so gsd-power disarms itself. **A gain we did not choose and that a
measurement can overturn** — measured: a logind session **without a seat** still shows `Active=yes`.

⭐ **The cure is a single call**: `org.gnome.SessionManager.Inhibit(app_id, 0, reason, 12)` — that is
`SUSPEND(4) | IDLE(8)` **together**. With `IDLE` alone, if the screensaver came on before
the inhibition, the only defence left asks for the `SUSPEND` bit: it is the attenuated form of the defect
paid for on KDE. ⛔ **Never the `LOGOUT(1)` bit**: it would make us hostage to the user's logout.

✅ **The precondition hardly arises**: `Inhibit` sits on the **same object** as `RegisterClient`,
which REMOTIX already calls (⚠ **the cited file, `src/uscita.c`, does not exist and never has** — reference to be redone) — if registration succeeds, the name is there.

⭐ **Two pieces of good news:**

- **the input we inject really resets the idle time** — neither via D-Bus nor via libei is the event marked
  `SYNTHETIC` (`core/events.c:126-138`): a remote user who is working keeps the session awake by himself.
  But a passive client does not;
- ✅ **if we lost the race, the image does not die**: `PowerSaveMode` **does not stop** the frames of a
  virtual monitor, because virtual views are offscreen. labwc's defect does not reappear, and
  **wayvnc's cure is not needed**. The lock screen would however be seen — that is §4.

⚠ And three configuration traps: `idle-delay=0` does **not** stop suspend (the sleep timer has
its own timeout); `idle-delay=0` with `idle-dim=true` turns on a dim at 60 s; `disable-lock-screen`
stops `lock()` but **not** `activate()` — the real lever is `lock-enabled=false`.

---

### 8. Capture, re-read in the code

*Detail: `rapporti/05-mutter-cattura.md`. Seven `[≠]`.*

#### 8.1 The corrections to R29

| What we said | What the code says |
|---|---|
| the DMA-BUF is a **diff** over four recycled buffers | ⛔ **false**: blit of the whole framebuffer, clip stack **deliberately emptied**, and the virtual view is a **persistent** `CoglOffscreen` |
| the cure is an **accumulation surface** | ⛔ that is why it made things worse: we copied the damaged rectangles from a buffer **already whole** |
| «the implicit fence is the wrong one» | ⚠ it covers half the contract — the *acquire*. What is missing is the **release** |
| «holding the buffer is not needed» | ⛔ the reference does **the opposite**, and it is the only protection without a timeline |
| «the timeline when there is one» | ⛔ `gnome-remote-desktop` 48.1 **never names** `SPA_META_SyncTimeline` |
| «`cattura.c` does not ask for a single `SPA_PARAM_Meta`» | ⚠ superseded: today it asks for Header and VideoDamage |

**The timeline contract, for whoever will write it**: `blocks=3`, the two `SyncObj` `spa_data` at the **tail**
(same fd), first `SPA_PARAM_Buffers` with `metaType` MANDATORY; and the buffers must be raised (Mutter
proposes up to 16; our four are the ones we ask for).

#### 8.2 ⭐ Cadence: the fact is `[M]`, ⚠ **the cause is `[R]`**. *Measured on 13 August 2026, and corrected the same evening*

`framerate` is a **fixed value `0/1`** — that is why a fixed cadence does not negotiate. And
`maxFramerate` does **two things at once**: it is the brake of capture **and it is the frequency of the virtual
monitor**.

⛔ *This paragraph said: «Same number ⇒ **beating** ⇒ 0.61». **It is wrong**, and the measurement
of phase 3 (step 1, M3) refutes it in both halves: neither the beating nor the 0.61.*

⭐ **THE FACT, which is `[M]` and is not to be touched**: negotiating the monitor at **120 Hz** and renegotiating
**only** the cadence at **90**, GNOME delivers **61.4 frames per second** (60.04 from the median), with
median interval **16.66 ms** and p99 **20.43**. It is cell **D** of `banchi/03-b14-esiti.jsonl`.

⚠ **THE CAUSE, which is `[R]` and must be stated for what it is**: read in Mutter's code, `maxFramerate`
does not seem a continuous cap but a **grid** — the brake computes
`min_interval_us = 10⁶/maxFramerate` **truncated to integer** (16666 for 60) and sets it against a tick
of **16666.67 µs**, and whoever falls below **loses a whole tick**. ⭐ **It remains the best explanation we
have**, and it is **consistent with cell D**, which is clean. ⛔ **But it is a reading of the code, not a
measured law**, and it must not be written as if it were.

> ⛔⛔ ⚠ *Here it was written, and in eight other documents along with it: «`[M]` law verified on **13
> points**: 8 confirm it, **0 refute it**». **IT IS FALSE.** The outcomes file of the grid —
> `banchi/03-b14-esiti-griglia.jsonl` — carries **three lines in all**: the terrain and **two cells**
> (`griglia-apertura-120` and `griglia-freno-90`), and **both carry `scena_sul_mio_monitor:
> false`** ⇒ they are **rejected by the bench itself**, which on its own verdict prints «⛔ la legge NON
> regge su **0 punti su 0**». The thirteen points are in no outcomes file. ⇒ The
> quantisation **goes back to `[R]`**. **Corrected on 13 August 2026**, finding of the coordinator of
> phase 3, verified line by line on the two outcomes files.*
>
> ⭐⭐ **And the reason for the rejection is trap number one of `LEZIONI.md` §1.1**: *the scene must
> be on the monitor being captured*. The bench **had written it in its own file**, field by
> field, and nobody looked at that field: the number was read and not the line beside it.

**The table below comes ENTIRELY from `banchi/03-b14-esiti.jsonl`** — seven cells, **all** with
`scena_sul_mio_monitor: true`, with the three controls (positive: collapse to 9.57 asking for 10; negative:
60→60 stays at 46.07; return: 83.03, that is it goes back to B) that close:

| monitor | brake | delivered | median | p99 | cell |
|---|---|---|---|---|---|
| 60 | 60 | 31.5 | 33.31 ms | 35.53 | **A** |
| 120 | 120 | 82.9 | 12.12 ms | 18.53 | **B** |
| 120 | 60 | 46.13 | 24.12 ms | 29.23 | **C** |
| ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61.4** (60.04) | ⭐ **16.66 ms** | 20.43 | ⭐ **D** |

⛔ **And the «six tenths» do not reproduce**: the low cell gives **a clean, deterministic 0.50**, which is
what a grid produces and a beating does not. ⭐ **This cell is clean** — it is **A**, and it holds.

> ⛔ ⚠ *And the cross-check falls too.* Here it was written: «Cross-check with a
> second independent scene: they agree **within 4 %**, waits **0** everywhere». ⛔ **It does not hold**, and
> the file itself says so, `banchi/03-b14-esiti-scena2.jsonl`: its **cell D** — that is exactly the
> result to be confirmed — carries `scena_sul_mio_monitor: false`, `palco_stabile: false` and **1
> frame in 25 s (0.04/s)**, and it does not even have the count of waits, because its step 2 is not
> there. And its **RETURN control** gives **52.84** against the **80.28** of its own cell B:
> **it does not return**, so the chain of controls of that scene **does not close**. Within 4 %
> only cell A agrees (31.28 against 31.5), B (3.2 %) and the positive control; C is at
> **5.4 %** and the negative control at **7 %**. ⇒ ⛔ **The 61.4 today has ONE scene only.** Corrected on
> 13 August 2026, same finding.

⭐ **`ensure_virtual_monitor` exits early if the size does not change**, and the decoupling
**works**: negotiating high (monitor 120) and renegotiating only the cadence (brake 90) brings GNOME to
**61.4**, that is as much as KWin. It cost three cells and **zero product lines**, as expected.

⛔⛔ **But the product today cannot ask for it, and it must be written here**: `MOVIMENTO_FPS 60` is a
compile-time constant (`src/figlio.c` · `MOVIMENTO_FPS`), `main.c` has no cadence option, and **`RecordVirtual`
does not take the frequency** (`src/mutter.h` · the note on `RecordVirtual`) — the four virtual monitors are all
**1920×1080@60**. ⇒ The result is `[M]` **on the bench** and **zero in production**.

⛔⛔ **And on the real chain the bottleneck is NOT `maxFramerate`: it is the software encoder.** The delay
capture → glass was largely ours, in the stretch capture → first byte in the page dominated by the
software encoder, and the product's child **never waited for Mutter**: raising the capture cadence
would not move the delay. *(The numbers of this measurement — made with the software encoder of the
time, libsvtav1 / libx265 via libavcodec — no longer hold after phase 18 and have been removed.)* *→ redone: `fasi/18-senza-ffmpeg.md` §5.4.*

#### 8.3 The rest

**[✗] A whole frame on request does not exist** (no property, no flag, no parameter)
— **and it is not needed**, given §8.1. **[✗] Only `BGRx` and `BGRA`**: R32 confirmed line by line. ⛔ **Stale
cursor-only buffers exist on Mutter too**, the exact analogue of §kde §4.7 — already handled in
our code since 7 August.

---

### 9. Input, reread in the code

*Detail: `rapporti/06-mutter-input.md`. Four `[≠]`.*

⛔ **`EI_EVENT_KEYBOARD_MODIFIERS` does not arrive on GNOME either**: `eis_device_keyboard_send_xkb_modifiers`
has **zero occurrences** in Mutter 48.7 (positive control: 25 other `eis_device_*` used). The sentence we
had in **two** documents — on KWin it does not arrive, *unlike GNOME* — **is false: they are even**.

✅ **The real source on GNOME is two D-Bus properties** (`CapsLockState`/`NumLockState`) with
`SYNC_CREATE`, which also give the **initial state** — something we do not have on labwc.

| Other `[≠]` | |
|---|---|
| the `mapping-id` | **we do not declare it**: Mutter generates it as a UUID and publishes it to us in the `Parameters`. The direction is **Mutter → us**, and `compositore_mapping_id` is inverted |
| the Pause key | the reference demands the E1 flag: our «riconoscibile anche senza» is **a choice**, not a fact |
| touch/RDPEI | **[✗] does not exist in 48.1**: three sections of our document describe **49+** |

⭐ **The wheel `/120 → ×10` is right, but not for the reason written**: with `scroll_delta` Mutter forces
`SOURCE_WHEEL` and **skips** the accumulator. The real threshold of one notch is **60**, i.e. half. ⚠ And
`ei_device_scroll_discrete` does an **integer division by 120**: half notches vanish.

⛔ **Two replacements that touch phase 6**: a **keymap** change destroys and recreates the keyboard
device; a **geometry** change destroys and recreates all absolute devices. The pointer to the
old device stops working **without an error**: keymap and regions must be reread **at every
`DEVICE_ADDED`**.

⚠ And a silent failure to know about: `transform_position` failing **is not an error** — one
log line and the D-Bus method **returns successfully**.

---

### 10. The clipboard

*Detail: `rapporti/07-clipboard-portale.md`. Six `[≠]`.*

⛔ **GNOME's clipboard does not belong to the RemoteDesktop session.** It is `MetaSelection`, i.e. it belongs **to the
compositor**, as on KDE and wlroots; only the **door** belongs to the session. The line for question 14 in
`LEZIONI.md` must be rewritten.

| What we said | What the code says |
|---|---|
| «chi si ricollega non riceve un annuncio, e ci è costato» | ⛔ **false**: `EnableClipboard` with **empty** options emits `SelectionOwnerChanged` at once. It was our recipe that lost it |
| «l'eco va distinta con un'euristica» | ✅ it is **labelled** (`session-is-owner`), and `SelectionRead` on one's own selection is **refused**: the KWin stall is impossible here |
| «la clipboard non sopravvive alla morte di chi ha copiato» | ⛔ **on GNOME it survives**: Mutter has an **internal clipboard manager**, started unconditionally — but **in a single MIME type**, with caps of 4 MiB / 200 MiB |
| «senza sessione la clipboard non esiste» | ⛔ **the X11 bridge is unconditional in both directions** (zero checks on focus): `xclip` works without a session, **and the bench on GNOME can use it** |

**Three operational traps:**

1. ⛔ **`DisableClipboard` is one-way**, because of a Mutter defect: the flag has **a single
   assignment in the whole file**, to `TRUE`. After the Disable, `Enable` answers «Already enabled» and
   announcements no longer arrive. **Rule: never call it** — to let go of the clipboard use
   `SetSelection` without `mime-types`;
2. ⛔ **asymmetric signature**: `mime-types` is **`as`** on input and **`(as)`** on output. Whoever reads the
   signal with the wrong type gets `NULL` **without an error** — confirmed by three independent
   implementations;
3. ⛔ **gnome-shell clears the clipboard at every screen lock**: it silently snatches ownership from us.

⚠ And `POLLHUP` counts as «ready» here too, but the `SelectionWrite` fd we receive is **blocking**,
while the `SelectionRead` one arrives already non-blocking.

---

### 11. The competitor, looked in the face

*Detail: `rapporti/09-chi-lo-fa.md`.*

> ⭐ **`gnome-remote-desktop` is an excellent RDP backend and an incomplete product; REMOTIX is a more
> complete product with a less polished backend.**

**What we do that it does not** — and the eight that matter all sit between «turn on a Debian
without a monitor» and «see a desktop»:

| | |
|---|---|
| ⭐ **we start the session** | its README says the headless session must be *«independently set up»*. **[✗]** no code that starts a compositor |
| ⭐ **real authentication** | it imposes NLA with a **fabricated SAM file**, credentials disconnected from the account. **[✗] Kerberos does not exist in 48.1** |
| **pure TLS** | its refusal of the fallback is the cause of a row of reports closed as «Not GNOME» |
| ⭐ **H.264 on GPU by default** | ⛔ in it VA-API is **behind a debug variable**: without NVIDIA the normal path is **RemoteFX Progressive on CPU** |
| **bitrate control** | it is fixed QP 22, no target |
| ⛔ **refusal of the second connection** | **[✗]** in headless 48.1 **no policy**: unlimited parallel sessions |
| **the rest** | certificate generated by us, logout/detach distinction, audio sink created from nothing, inhibitions, more compositors, our own numbers |

**Where it is ahead** — almost all **hours of work**, not structural advantages: the **cursor**
(572 lines, LRU cache — we do not send it at all), **files in the clipboard** via FUSE, the
**microphone**, **AAC/Opus**, an **audio latency regulator at 300 ms**, **handling of
ack suspension**, resizing without redoing the capture, multi-monitor, the
**instrumentation** (metrics with skipped frames and a telemetry channel that reads the
client's timings), **Remote Login**, and the **packaging**.

> #### ⛔ One thing to verify in our code **now**, not at the end of the study
>
> The RDP client can **suspend acks** by sending `queueDepth == 0xFFFFFFFF`, and a regulator that
> does not handle it **stops forever**. Ours grants `MAX(2, rtt·fps/10⁶+2)` slots: if that
> value is treated as a number, the queue closes and the desktop freezes.

⚠ **The §gnome-remote-desktop document is written on 51.alpha**, not on Trixie's 48.1: six
sections need correcting (no Kerberos, no touch, no throttler, `CURSOR_MODE_EMBEDDED`
never used, VA-API behind debug, two slot formulas instead of one). ⛔ And Debian declares **trixie
48.1-4 vulnerable to CVE-2025-5024**, an unauthenticated DoS.

#### 11.1 ⭐ GNOME 48's handover, which is portable

The TCP socket **is never closed**: it travels as a **file descriptor over D-Bus**, and whoever routes it
had read in **`MSG_PEEK`**, so the recipient redoes the RDP negotiation from scratch. Plus the **Server
Redirection PDU** with routing token, which is pure RDP and FreeRDP exposes it.

**Six things to copy, all portable to KDE, XFCE and LXQt**: the socket by fd; `MSG_PEEK` to
route without consuming; the Redirection PDU; authorising **per logind session** instead of via
polkit; `Inhibit("sleep","block")` as long as there is a client; the greeter's self-dismissal.

⛔ **But it does not pay to lean on Remote Login**: it would mean **ceasing to be the RDP server**
(it the server, us at most a client), it would work **only on GNOME** — so the «I start it
myself» road would still have to be written for the other three, and there would be **two products**. Plus a
field datum: the handover **fails at random in about two starts out of three** on Fedora 42, and it is five processes
in three security contexts synchronised on a 30 s timeout.

---

### 12. The matrix, redone with the right denominator

*§lxqt §4.1 counted 9 combinations. They were **10**.*

**Cinnamon 6.4.10 and muffin 6.4.1 are in Trixie** with a `cinnamon-wayland.desktop` session
**[R-pkg]**. ⛔ But muffin **renames the bus to `org.cinnamon.Muffin.*`** and is a fork of the 3.38 line,
~10 cycles from Mutter: **it is free neither from the wlroots phase nor from the GNOME work**.

| | |
|---|---|
| realistic combinations on Trixie | **10** |
| covered today | **2** (20 %) |
| after the wlroots phase alone | **8 of 10 — 80 %** |
| the next cheapest | **LXQt on labwc: zero lines** |

⭐ **But what really costs least is not a new combination: it is the five debt items of
§1.1**, on the desktop we already serve.

---

### 13. The measurement plan

⚠ **Step zero: put GNOME back on the server**, which is not installed today.

| # | The measurement | Why |
|---|---|---|
| **M1** | ⛔ our regulator withstands `queueDepth == 0xFFFFFFFF` | §11: a desktop that freezes forever. Tested with an instrumented client, not by waiting |
| **M2** | headless yes/no against `inhibit_remote_access` | §4: it is the precondition we have today **by accident** |
| ⚠ **M3** | decoupled cadence — ⭐ **the fact is obtained**, ⛔ **but the measurement is HALF and is not closed** | §8.2: `[M]` monitor 120 + brake 90 ⇒ **61.4 delivered** (60.04), median **16.66 ms** — cell **D**, clean, with the three controls that close. ⛔ **But the cause is `[R]`, not `[M]`**: the «grid law» on 13 points **does not exist** (see the box in §8.2), and ⛔ **the confirmation on a second scene is missing**: cell D of `03-b14-esiti-scena2.jsonl` is rejected by the bench. ⚠ **Not actionable by the product today** (`RecordVirtual` does not take the refresh rate), and ⛔ **it is not the cure for the delay**: on the real chain the bottleneck is the software encoder |
| **M4** | `SPA_META_SyncTimeline` with acquire/release, **or** holding the `pw_buffer` | §8.1: it is phase 9's hunt in the right place |
| **M5** | `SPA_META_Cursor` + `cursor-mode=2` → native RDP cursor | §5.2: today the pointer arrives nowhere |
| **M6** | the dconf profile in `$XDG_RUNTIME_DIR` with the locks, and **every key reread** | §6: pays §1.1 items 3, 4 and 5 together |
| **M7** | `Inhibit(…, 12)` holds for 20 minutes, and the machine does not suspend | §7 |
| **M8** | the clipboard: announcement on reconnection, and the screen lock that clears it | §10 |
| **M9** | **deliberately faulty** test: non-empty `SHELL`, and `--virtual-monitor` missing | ⭐ learn how the fault reads: session **alive, complete and black** |

> #### ⚠ M3 — **the true state**, written on 13 August 2026 after the finding
>
> *This morning this line said **✅ CLOSED on 13 August 2026**, and it said so **on the basis of the
> grid**. The grid has fallen — its two cells are rejected by the bench itself, §8.2. ⇒ **M3 is not
> closed and not open: it is half**, and must be kept half until the two missing halves are done.
> ⛔ It is not forced to «closed» because the number is nice, nor to «open» because one line was false.*
>
> | | |
> |---|---|
> | ✅ **what M3 HAS obtained** | `[M]` **61.4** at monitor 120 and brake 90 — cell **D** of `banchi/03-b14-esiti.jsonl`, `scena_sul_mio_monitor: true`, with positive control (collapse to 9.57), negative (steady at 46.07) and return (83.03) that close. **This is a fact, and it stays** |
> | ⛔ **what M3 does NOT have** | the **cause**. The quantisation is `[R]`: read in Mutter's code, consistent with cell D, **never measured on a grid of points** |
> | ⛔ **nor** | the **confirmation on a second scene**: cell D of `banchi/03-b14-esiti-scena2.jsonl` carries `scena_sul_mio_monitor: false` and **1 frame in 25 s** ⇒ the 61.4 has **one scene only** |
> | ⇒ **what would close it** | redo the **grid** with the scene on the monitor being captured, and redo **cell D** on the second scene. It is the same bench `banchi/03-b14-cadenza.py`, and ⭐ **it already has the field to notice it**: it is `scena_sul_mio_monitor`, and this morning nobody looked at it |

---

### 14. The lessons this study adds

1. ⭐ **Question 16**: *«is there a state in which the compositor REVOKES what it has already granted us, and
   who has a finger on that button?»* Question 3 asks whether a permission exists; this one asks whether it can be
   **withdrawn live**. On GNOME there is an API that *«terminates every active remote access
   session»*, and none of the fifteen questions covered it.
2. ⛔ **The desktop we serve best is the one we studied worst.** Ten phases on GNOME
   produced deep knowledge of *capture* and none of the *desktop*: seven items never
   tackled, and two of them (§4 and §7) are defects the user would hit **by leaving the session
   idle for twenty minutes**.
3. ⭐ **A condition that saves us by accident must be written down as a requirement.** We are headless because
   Mutter degrades by itself without a seat, not because we asked for it — and on that condition depends
   the fact that a screen lock does not detach us. It is the general form of `LEZIONI.md` §2.5: *the
   protection against a known defect is not entrusted to something that can be lost.*
4. ⚠ **Measurements age worse than readings.** R29 was written from correct measurements and from a
   **wrong diagnosis**, and stayed standing for two phases because nobody had read the code
   underneath them. Lesson §1.9 said «quando codice e misura si contraddicono, sospetta la misura»;
   this study adds the opposite case — **a right measurement with an invented explanation is more
   dangerous than a wrong measurement**, because nobody questions it again.


<a id="kde"></a>

## KDE Plasma and KWin — code study, for phase 11

*Analysis carried out on KDE's original source code, cloned from `invent.kde.org` on 7 August 2026
and kept in `reference-kde/`, with the same convention as `reference/xrdp`.*

| Repository | Version cloned | Why |
|---|---|---|
| `plasma/kwin` | tag **v6.3.6** | the compositor: it is **it** that owns screen and input |
| `plasma/plasma-workspace` | tag **v6.3.6** | the session: startup, logout, ksmserver, klipper |
| `plasma/kpipewire` | tag **v6.3.6** | consumes PipeWire and **encodes in H.264**: it does our very same work |
| `plasma/xdg-desktop-portal-kde` | tag **v6.3.6** | the «official» road to capture, and consent |
| `plasma/libkscreen` | tag **v6.3.6** | screen configuration from outside |
| `plasma/powerdevil` | tag **v6.3.6** | power, inhibitions, shutdown |
| **`plasma/krdp`** | tag **v6.3.6** *and* master `1dd52ba` (6.7.80) | ⭐ **KDE's RDP server**: same RDP library, same compositor, same clients. **It is the main reference of the phase**, the equivalent of `gnome-remote-desktop` |
| `network/krfb` | master `6b2832b` (KDE Gear 26.11.70) | KDE's VNC remote desktop |
| `libraries/plasma-wayland-protocols` | master | the XML of KDE's protocols |

**6.3.6 is Debian Trixie's version** (§3.8 of `SPECIFICA.md`), i.e. the one running on the
runtime machine: the lines quoted here are the ones the user really has installed.

Together with KDE's sources **our bench code** was reread — `banco/nodo-kwin.c` (the
KWin protocol client), `banco/misura-cattura.c` (the PipeWire consumer),
`banco/banco-altri.sh`, `banco/zkde-screencast-unstable-v1.xml` — because half the value of this
study lies in the comparison between what KDE does and what we have already written.

Every statement carries a mark, as in `REFERENCE.md`:

| Mark | Meaning |
|---|---|
| **[R]** | **read in the code**, with `file:riga`. It is the bulk of this document |
| **[M]** | measured by us, in the field, with a date |
| **[?]** | **not decided by the code**: must be measured on the bench. The `[?]` are listed in §14 |
| **[✗]** | **searched for and not found**: a negative statement, worth as much as a positive one |

> ⚠ **This document is about reading, not measuring.** `LEZIONI.md` §1 says the project has
> never stalled on a hard problem but on a measurement that did not measure what we believed: here there
> is no new measurement, not even one line executed. What there is is the code, which says **what
> is possible** — and in three places it says that **one of our measurements of 7 August was looking at the wrong thing**
> (§5.1 and §15). Before moving a number into the documents the measurement is redone.

---

### 1. In two minutes

The **four questions** that `PIANO.md` phase 11 and the project memory asked to close before
designing anything at all, with the answer the code gives:

| # | The question | The answer |
|---|---|---|
| **1** | **How is capture permission obtained, for an unattended service?** | ✅ **A `.desktop` file with `X-KDE-Wayland-Interfaces`.** No dialog, not even the first time; survives reboot and logout; no patch. It is the mechanism by which KDE's portal and `krfb-virtualmonitor` are authorised (§3). ✅ **MEASURED on 7 August — it works**, and with one more requirement the code did not show: **`XDG_MENU_PREFIX=plasma-`** in the environment, or the service index stays empty and the gate does not open (§3.3-bis) |
| **2** | **Can KWin without a monitor draw on the GPU?** | ✅ **Yes**, and now **measured**, not just read: `renderD129` opened, `libEGL_mesa`+`libgbm` loaded, `zwp_linux_dmabuf_v1` v4 announced. **Our measurement of 7 August («zero nodi DRM, nessuna libreria GL») was wrong in its label: R32 must be corrected** (§5.1) |
| **3** | **How is a Plasma session started without a monitor?** | ✅ Environment from scratch with **two** mandatory variables (**plus `XDG_MENU_PREFIX`, see question 1**), compositor unit overridden, `startplasma-wayland`. Simpler than GNOME. With **two hard constraints**: `--xwayland` is not optional, and `--virtual` cannot create outputs on demand (§6). ⛔ **And `--virtual` is no longer a choice**: `--drm` from a session without a seat does not start [M] (§5.2) |
| **4** | **Which road does input take?** | ✅ **libei**, with a single D-Bus call to KWin and **without any permission check**. `SPECIFICA.md` §3.8 («protocollo `kde-fake-input`») is superseded by the code: `fake_input` is the old road (§7). ✅ **MEASURED**: `connectToEIS(7)` from any SSH shell → `(handle 0, 1)` |

And the **eleven questions to the new compositor** of `LEZIONI.md` §3, with KWin's column filled in
by this study. The cells marked `[?]` are the ones the code does not decide.

| # | The question | Mutter 48.7 | **KWin 6.3.6** |
|---|---|---|---|
| 1 | How is capture requested without a portal? | D-Bus `org.gnome.Mutter.ScreenCast` | Wayland protocol `zkde_screencast_unstable_v1` **v5** [R] |
| 2 | Does it push frames or have them pulled? | pushes (PipeWire) | **pushes** (PipeWire), and brakes by itself on `maxFramerate` [R] |
| 3 | Is the protocol behind a permission? | no | **yes**, and the permission is **a field of a `.desktop` file** [R] — **+ `XDG_MENU_PREFIX`** [M, 7 Aug] |
| 4 | Without a monitor, does it draw on the GPU? | yes | **yes** [R] **and measured** [M, 7 Aug]: render node opened, EGL/gbm, dmabuf v4 |
| 5 | Can one request a virtual screen of the desired size? | yes, `RecordVirtual` | **yes**, `stream_virtual_output` — but **only with the `--drm` backend** [R] |
| 6 | How much does it deliver, with a scene that changes at every redraw? | ~37 of 60 | **59–60** [M, 7 August] — measured however with `--virtual` + `stream_output`, not in the product configuration |
| 7 | How does the declared cadence behave? | six tenths, above 60 does not rise, **fixed refused** | `framerate` **must** be `0/1`; the cap is `maxFramerate`, **honoured server-side** with integer arithmetic in ms [R] |
| 8 | Does it deliver whole frames or «diffs»? | **at zero copy it is a diff** | **whole, always** [R] — R29's defect does not recur |
| 9 | Does the buffer arrive already drawn? | **no**: 100 % with drawing in progress | **yes**: KWin does `glFlush()`, or `glFinish()` on NVidia and llvmpipe [R] |
| 10 | What does resolution cost? | nothing up to 4K | nothing [M] |
| 11 | What does colour depth cost? | nothing | nothing; `BGRx` is negotiable [R] |

> #### ⭐ And on KDE **a `gnome-remote-desktop` exists**: it is called `KRdp`
>
> *Found on the evening of 7 August, after a question from the user. The first draft of this document
> said there was no trace of RDP in KDE, and it was wrong (§12.0).*
>
> KDE's RDP server, **C++ on FreeRDP + kpipewire**, 4 222 lines in the Trixie version. It confirms
> in full the answer to question 1 — its `.desktop` declares
> `X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input,zkde_screencast_unstable_v1` — and confirms **the two
> codecs**, **the in-flight frame regulator from RTT**, **the exclusive region borders** and
> **pure TLS when authenticating with PAM**. It does not solve, however, the two things that remain ours:
> **it does not start the session** (it lives inside Plasma) and **it does not resize the virtual screen**.
>
> ⛔ **And `xrdp` has nothing to do with it**: it has no Wayland path at all — it launches an `Xorg` or an `Xvnc` and inside
> it runs Plasma's **X11** session (§12.3). It did not solve our problem: it avoided it.

**The picture in one line**: on KDE capture is **simpler and healthier** than on GNOME (whole
frames, synchronisation done by the compositor), input is **shorter** (one D-Bus call,
no permission), the session is **more predictable** (no `ConditionEnvironment`, the bus does not die)
— and in exchange **dynamic resolution is missing**: a KWin virtual output cannot be resized, and
must be closed and remade (§8).

> #### ⛔ «CURSOR OUTSIDE THE ENCODER PATH» WAS WRITTEN HERE, AND IT IS FALSE WITH `--virtual`
>
> *[M, 8 August 2026, and the user saw it on first use: «non c'è la scia, ma è quello di KDE che
> segue quello vero» — i.e. **two pointers**.]*
>
> The `Metadata` cursor mode governs whether the screencast **adds** a cursor, not whether the scene already
> contains one. And with the `--virtual` backend it always contains one:
>
> | | |
> |---|---|
> | `compositor_wayland.cpp:573-608` | if the backend has no cursor plane, `hardwareCursor` stays false and the **software cursorLayer** is made visible |
> | `backends/virtual/` | ⛔ **does not define `cursorLayer()`** [✗]: the virtual backend has no cursor plane |
> | `virtual_egl_backend.cpp:187-194` | `textureForOutput` returns the **output's framebuffer**, i.e. the one the cursorLayer was painted into |
> | `pointer_input.cpp:99-108` | and KWin shows it as soon as a pointing device exists on the seat — ours, from libei |
>
> **There is no lever to prevent it**: `Cursors::hideCursor()` is internal and is called only by
> `pointer_input` and `hide_cursor_spy`; no protocol, no D-Bus. Requesting `Hidden` mode would not
> change anything. With the `--drm` backend — which §5.2 ruled out — there would be a cursor plane and the
> problem would not exist.
>
> ✅ **The only cure is on the other side**: the **client** is told to hide its own pointer,
> with `SYSPTR_NULL`, which is basic RDP. The price is that the pointer moves at the latency of the
> **video** instead of that of the network — on a LAN it is one frame.
>
> ⚠ **And on Mutter it is NOT done**: there the cursor really is outside the image, and hiding the
> client's would leave the user with no pointer at all. It is a difference between compositors, not a
> preference.
>
> #### ⛔ And the cure works on two clients out of three — not on all
>
> *[M, 8 August 2026, the user's judgement on xfreerdp and on RDM]*
>
> | client | outcome |
> |---|---|
> | **xfreerdp** | ✅ one pointer only, KDE's |
> | **RDM (Android)** | ⛔ **two remain**, even though the server declared and the client **accepted** the PDU (`14:02:28 puntatore del client nascosto`, i.e. `PointerSystem()` answered true) |
>
> The explanation is that RDM's second pointer **is not the RDP pointer**: it is the *touch pointer*
> the application draws over its own window to make a desktop usable with a finger.
> It lives outside the protocol, and **no server can remove it** — it is switched off only from the client's
> settings, by moving to mouse mode.
>
> ⚠ Hence the general rule: `SYSPTR_NULL` removes the pointer the client draws **on behalf
> of the protocol**, not every arrow-shaped pixel. It is yet another form of the three-client
> rule (`LEZIONI.md` §2.1): the same line of code gives three outcomes.
>
> #### ⭐ And so the right cure is the opposite: KDE's cursor is made TRANSPARENT
>
> *[M, 8 August 2026, after the user asked to close the point for real]*
>
> The reasoning above is right and the conclusion was short. True, with `--virtual` KWin
> draws the cursor inside the image and there is no lever to prevent it — **but there is no need to
> prevent it: it is enough that what it draws cannot be seen.**
>
> KWin takes the cursor theme from **`XCURSOR_THEME`, and looks at it only if there is also
> `XCURSOR_SIZE`** (`cursor.cpp:134-145`: `if (!themeName.isEmpty() && ok)`). We compose the
> session's environment ourselves. Therefore: a theme with a **1×1 zero-alpha** cursor, written in
> `$XDG_RUNTIME_DIR/remotix/icons/` and pointed to with `XCURSOR_PATH`, and the pointer goes back to being
> **the one the client draws by itself — as on Mutter**, at network latency instead of
> video latency, and **only one on every client**, including those that draw one on their own.
>
> ✅ **Measured**: `XCURSOR_THEME=remotix-invisibile`, `XCURSOR_SIZE=24` and `XCURSOR_PATH` present
> in `kwin_wayland`'s environment (read from `/proc/<pid>/environ` with `sudo`, §of the non-dumpable
> binary), **68 shapes written**, file `Xcur v1.0 1×1 alfa 0` of 68 bytes, and **no
> «Failed to load cursor theme» line** in the compositor unit's journal.
>
> ⛔ **The theme must really load.** If `CursorTheme` turns out empty KWin **falls back to the default
> theme** (`pointer_input.cpp:1183-1196`), i.e. to the visible cursor: a theme with zero shapes
> hides nothing, it *puts it back*. That is why all shapes are written, and why the check
> that counts is the absence of the fallback, not the presence of the files.
>
> ⚠ **The price**: the shape change is lost — the I-beam over text, the resize arrows —
> exactly as on GNOME today. Giving it back means sending the real shape on RDP's **pointer
> channel**, taking it from the PipeWire metadata we already request (`Metadata` mode): it is a job of its own,
> and it applies to both compositors.
>
> Hence `compositore_cursore_nell_immagine()` **has gone back to false on KWin too**, and `SYSPTR_NULL`
> is no longer sent. The function stays written: the day a compositor draws the cursor
> into the image **without** letting us change the theme, the answer is there and need not be found again from scratch.

---

### 2. The map: where each thing lives

| What | Where, in `reference-kde/` |
|---|---|
| The capture protocol, Wayland side | `kwin/src/wayland/screencast_v1.{h,cpp}` — Qt signals only |
| The capture engine | `kwin/src/plugins/screencast/` — `screencastmanager.cpp`, `screencaststream.cpp` (1000 lines), `outputscreencastsource.cpp`, `regionscreencastsource.cpp`, `screencastbuffer.cpp` |
| The permission filter | `kwin/src/wayland_server.cpp:127-193`, `kwin/src/utils/serviceutils.h`, `kwin/src/utils/executable_path_proc.cpp` |
| Modern input (libei) | `kwin/src/plugins/eis/` — `eisbackend.cpp`, `eiscontext.cpp`, `eisdevice.cpp` (1829 lines) |
| Old input | `kwin/src/backends/fakeinput/fakeinputbackend.cpp` |
| The output backends | `kwin/src/backends/{drm,virtual,wayland,x11}/` |
| Outputs and their configuration | `kwin/src/core/output.{h,cpp}`, `kwin/src/wayland/outputmanagement_v2.cpp`, `kwin/src/core/outputconfigurationstore.cpp` |
| The clipboard | `kwin/src/wayland/datacontrol*_v1.cpp`, `kwin/src/wayland/seat.cpp`, `kwin/src/xwayland/clipboard.cpp`, `plasma-workspace/klipper/` |
| Session startup | `plasma-workspace/startkde/startplasma{,-wayland}.cpp`, `startkde/systemd/*.target`, `kwin/plasma-kwin_wayland.service.in`, `kwin/src/helpers/wayland_wrapper/kwin_wrapper.cpp` |
| Logout | `plasma-workspace/startkde/plasma-shutdown/shutdown.cpp`, `plasma-workspace/ksmserver/{logout,server}.cpp`, `kwin/src/sm.cpp` |
| Power and inhibitions | `powerdevil/daemon/powerdevilpolicyagent.cpp`, `powerdevil/daemon/powerdevilsettingsdefaults.cpp` |
| KDE's PipeWire consumer, with encoder | `kpipewire/src/` — `pipewiresourcestream.cpp`, `pipewireproduce.cpp`, `h264vaapiencoder.cpp`, `vaapiutils.cpp` |
| KDE's remote desktop | `krfb/framebuffers/pipewire/pw_framebuffer.cpp`, `krfb/events/xdp/xdpevents.cpp` |

---

### 3. ⛔ The gate: how KWin decides who may capture

It is the answer to the phase's **first** question, and it is worth putting before everything else because it
conditions every test: **as long as the gate is closed, the symptom is «this compositor does not expose the
protocol», and no error arrives.**

#### 3.1 The mechanism, in full

**[R]** KWin installs a global libwayland filter — `wl_display_set_global_filter`
(`kwin/src/wayland/filtered_display.cpp:44`) — and `KWinDisplay::allowInterface()`
(`kwin/src/wayland_server.cpp:146-192`) denies the bind of **six** interfaces to whoever does not declare them.
The blacklist, `wayland_server.cpp:129-136`:

```cpp
const QSet<QByteArray> interfacesBlackList = {
    QByteArrayLiteral("org_kde_plasma_window_management"),
    QByteArrayLiteral("org_kde_kwin_fake_input"),
    QByteArrayLiteral("org_kde_kwin_keystate"),
    QByteArrayLiteral("zkde_screencast_unstable_v1"),      // ← the capture
    QByteArrayLiteral("org_kde_plasma_activation_feedback"),
    QByteArrayLiteral("kde_lockscreen_overlay_v1"),
};
```

If the filter denies, **the global is not even announced in the registry**: the client sees a
compositor without that protocol. The diagnostic exists but it is `qCDebug`, off by default
(`wayland_server.cpp:184`).

The criterion is **not** uid, not pid, not polkit, not a list in `kwinrc`. It is a chain of
three steps, all **[R]**:

1. `SO_PEERCRED` on the client's socket → pid;
2. pid → `/proc/<pid>/exe`, resolved canonically (`kwin/src/utils/executable_path_proc.cpp:11-14`);
3. **all** installed applications are searched and the one is taken whose **first token of
   `Exec=`**, canonicalised, matches that path (`kwin/src/utils/serviceutils.h:27-49`,
   via `KApplicationTrader::query`); of that one the field
   **`X-KDE-Wayland-Interfaces`** is read (`serviceutils.h:24`).

Authorised **only** if that field contains the exact name of the interface.

The two shortcuts: the client is KWin itself (`client->processId() == getpid()`,
`wayland_server.cpp:152`), or `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` **in KWin's environment**
(`:168`, read into a `static`), which opens **all six** interfaces to **all** clients.

#### 3.2 The precedents, i.e. the model to copy

**[R]** All in the real system, all with the same mechanism:

| `.desktop` file | Declared interfaces |
|---|---|
| `xdg-desktop-portal-kde/data/org.freedesktop.impl.portal.desktop.kde.desktop.in:49-51` | `org_kde_kwin_fake_input,org_kde_plasma_window_management,zkde_screencast_unstable_v1` |
| **`krfb/krfb/org.kde.krfb.virtualmonitor.desktop.cmake:84`** | `zkde_screencast_unstable_v1`, with `NoDisplay=true` — **it is exactly our case** |
| `plasma-workspace/shell/org.kde.plasmashell.desktop.cmake:76` | `…,zkde_screencast_unstable_v1,…` |
| `kpipewire/tests/org.kde.kpipewireheadlesstest.desktop.cmake:6` | `zkde_screencast_unstable_v1` |

And the message kpipewire prints to itself when the global is missing says exactly where
to look: *«Remember requesting the interface on your desktop file:
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1»*
(`kpipewire/tests/screencasting.cpp:79`, `plasma-workspace/libtaskmanager/screencasting.cpp:44`).

#### 3.3 The three fragile points, all about packaging

1. ⛔ **REMOTIX must not run as root.** `/proc/<pid>/exe` of a process of **another uid** is not
   readable, `executablePath()` returns empty, and `wayland_server.cpp:170-173` **denies**. It must run
   as a user service — which is anyway what §3.4 of `SPECIFICA.md` prescribes.
2. ⛔ **`Exec=` must name the executable that opens the socket**, not a shell launcher: the
   comparison is on the canonical path of the real binary.
3. ✅ **`kbuildsycoca6` is not needed, and restarting KWin is not needed.** [R, `kf6-kservice 6.13.0-1`, the
   Trixie version] `ensureCacheValid()` rebuilds the cache **inside the KWin process**, with
   a rate limit of **1 500 ms** (`ksycoca_ms_between_checks`). So an installed `.desktop`
   is visible within a second and a half — and *Sunshine*, which writes it at runtime, waits
   **3 000 ms** to be safe (§12.4).
4. ⛔ **The fourth fragile point, and it breaks everything silently**: `serviceutils.h:35` takes
   `servicesFound.first()`, and KDE bug **446628** (confirmed since 2021) shows that **a same-named user
   `.desktop` shadows the system one** — if the one that wins lacks the field, permission
   is denied without an error. And what counts are **KWin's** `XDG_DATA_DIRS`, not ours: §6.1
   prescribes composing the environment from scratch, so the file must be installed where **the compositor**
   looks.

#### 3.3-bis ⭐ MEASURED — the gate opens, but depends on `XDG_MENU_PREFIX`

> **[M] Measurement M1, bench of 7 August 2026, KWin 6.3.6-1 and kf6-kservice 6.13.0-1.**
>
> **The mechanism of §3.1 works**: with a `.desktop` declaring
> `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1` and `NoDisplay=true` — the form of KRdp and of
> krfb — KWin announces the global and capture starts. No dialog, no portal, as expected.
>
> **But before working it denied five times, and the cause is nothing of what §3.3
> lists.** The denial was this, and the document must be read with this addition:
>
> ⛔ **`kbuildsycoca6` indexes nothing if `XDG_MENU_PREFIX` is not set.** The service
> index is built starting from `${XDG_MENU_PREFIX}applications.menu`, and Debian **does not install
> `/etc/xdg/menus/applications.menu`**: it installs `plasma-applications.menu` and
> `kf5-applications.menu`. Without the prefix, `kbuildsycoca6` exits with **status 0** saying only
> `"applications.menu" not found in QList("/etc/xdg/menus")`, and `KApplicationTrader::query` finds
> **no** application — not even the 133 system ones.
>
> The proof, in the size of the cache: **226 275 bytes** without the prefix, **379 292** with
> `XDG_MENU_PREFIX=plasma-`. And KWin's verdict goes from
>
> ```
> KWIN_UTILS: Could not find the desktop file for "…/nodo-kwin"
> kwin_core:  Interface "zkde_screencast_unstable_v1" not in X-KDE-Wayland-Interfaces of "…/nodo-kwin"
> ```
> to
> ```
> KWIN_UTILS: Interfaces found for "…/nodo-kwin" "X-KDE-Wayland-Interfaces" : QList("zkde_screencast_unstable_v1")
> ```
>
> ✅ **In a real Plasma session the problem is not seen**, because `startplasma` sets the
> variable by itself: `qputenv("XDG_MENU_PREFIX", "plasma-")`
> (`plasma-workspace/startkde/startplasma.cpp:366`). **It concerns us** because §6.1 prescribes
> composing the environment from scratch: if we compose it without that variable, the gate stays closed and
> the symptom is that of §3 — «the compositor does not expose the protocol».
>
> ⛔ **And there is a fragility that must be written down**: the cache file name does **not** depend on the prefix
> (`ksycoca6_<locale>_<hash>`, and the hash is the same in both cases). So any process that
> rebuilds the index **without** the prefix overwrites the good one, and the permission goes back to being
> denied **with KWin already running** — an intermittent fault, without messages. Whoever packages the
> service exports `XDG_MENU_PREFIX=plasma-` into the environment of the **whole** session tree.
>
> **How to diagnose it in three seconds**, which is the thing to remember: the line that states the cause is
> in the **`KWIN_UTILS`** category, not in `kwin_core` (`kwin/src/utils/serviceutils.h:40,46`), and it is
> switched on with `QT_LOGGING_RULES='KWIN_UTILS.debug=true'`. The two lines have opposite cures:
> *«Could not find the desktop file»* = the index does not associate (this case); *«Interfaces found … :
> ()»* = it associates, and the field is missing.
>
> Two other measured facts, which rule out the convenient explanations: the denial was identical for a
> client in **`/usr/bin`** (`wayland-info`) and for ours on `/media` — so it was **not** the
> mount, and it was **not** `NoDisplay`, nor the quotes in `Exec`, nor an argument in `Exec`: all
> five variants denied, all with the same line.

> #### ✅✅ And the gate also opens INSIDE a real Plasma session
>
> **[M] 8 August 2026.** The test of §3.3-bis was on a bare `kwin_wayland`. Repeated inside a
> session started with `startplasma-wayland` (the recipe of §6.1), with the same `.desktop`:
>
> ```
> KWIN_UTILS: Interfaces found for "…/nodo-kwin" "X-KDE-Wayland-Interfaces" : QList("zkde_screencast_unstable_v1")
> ⇒ zkde_screencast announced, and a real stream: PipeWire node 55
> ```
>
> So the whole chain — Plasma session, permission, capture, PipeWire stream — **is verified in the
> field**. In the same session KWin writes 13 `Interfaces found for …` lines, among them those of
> KDE's portal with its three interfaces: i.e. one sees the mechanism working for the others too.
>
> ⛔ **BUT one thing breaks it, and it must be written down because one meets it precisely when packaging the service:
> `InaccessiblePaths=` in the compositor unit closes the gate.** It was there to choose the GPU
> (§5.6) and has this side effect: with that line the global is **not** announced, and KWin
> **does not even get to query the index** — **0 `KWIN_UTILS` lines against 13** in the same
> environment. It is not file visibility: inside the namespace, `nsenter` shows the `.desktop` and the
> `ksycoca6_en_…` cache present and readable; and it is not `/proc`, which is mounted normally and shows the
> other processes. The exact mechanism **has not been demonstrated** (the residual hypothesis is the first
> condition of `allowInterface()`: empty `executablePath()` ⇒ deny, `wayland_server.cpp:170-173`).
>
> **The rule that follows is clear-cut anyway**: the compositor unit **is not hardened with
> mount namespaces** (`InaccessiblePaths`, and to be safe anything implying `PrivateMounts`).
> What is needed is obtained otherwise — for the GPU, with the node's permissions (§5.6).

#### 3.4 Who is protected and who is not — the table that counts

**[R]** KWin 6.3.6's permission model is **incomplete**, and for us that is a stroke of luck. Summary
for everything we need:

| We need it for | Interface / object | Protected? |
|---|---|---|
| capture + virtual output | `zkde_screencast_unstable_v1` | **yes** — `.desktop` with `X-KDE-Wayland-Interfaces` |
| **input** | `org.kde.KWin.EIS.RemoteDesktop` (D-Bus) | **NO, no check** (`kwin/src/plugins/eis/eisbackend.cpp:70`, `ExportAllInvokables`) |
| input, old road | `org_kde_kwin_fake_input` | **yes**, same `.desktop` route — and its `authenticate` authenticates nothing (`fakeinputbackend.cpp:107-113`, `// TODO: make secure`) |
| **clipboard** | `zwlr_data_control_manager_v1` | **NO** (`wayland_server.cpp:386`, not in the blacklist) |
| reading/writing the screen layout | `kde_output_device_v2`, `kde_output_management_v2` | **NO** |
| state of the lock keys | `org_kde_kwin_keystate` | **yes**, same `.desktop` route |
| single screenshots | `org.kde.KWin.ScreenShot2` | **yes**, via `X-KDE-DBUS-Restricted-Interfaces` (`screenshotdbusinterface2.cpp:331-355`) — **the only protected D-Bus object in all of KWin** |

**Hence the packaging recipe**: a single `.desktop`, declaring
`zkde_screencast_unstable_v1` (for capture) and — if and when they are needed — `org_kde_kwin_keystate`
and `org_kde_kwin_fake_input`. Input via EIS does not need it.

> ⚠ **A hole we will not use, but which tells how the model is made.** [R]
> `wp_security_context_manager_v1` **is not in the blacklist** (`wayland_server.cpp:378`): any
> client can declare as `app_id` the name of someone else's `.desktop` and reconnect
> obtaining authorisation (`wayland_server.cpp:121-127` + `display.cpp:282-297`, and
> `serviceutils.h:51-58` which for sandboxed clients uses `KService::serviceByDesktopName`).
> The model is **declarative**, not enforcing. The *legitimate* variant of this route — declaring
> one's **own** app-id — is the only way out if one day the constraint on `Exec=` became awkward for us.

#### 3.5 The roads we do NOT take, and why it must be written down

| Road | Outcome |
|---|---|
| **The portal with `restore_token`** | implemented (`xdg-desktop-portal-kde/src/screencast.cpp:222-279`), but **the first consent is a modal dialog** (`:272`), the token identifies the monitor by **position** (`outputsmodel.cpp:93-94`) and if it does not resolve **the dialog reappears**. For an unattended service: **no** |
| **KDE's «mega-authorisation»** | it exists and is documented in the comment: *«Particularly useful for headless setups and when the user is not physically at the machine»* (`xdg-desktop-portal-kde/src/remotedesktop.cpp:34-71`, used at `:227` to **skip the dialog entirely**). ✅ **And it can be written**, contrary to what the first draft of this document said: `flatpak permission-set kde-authorized remote-desktop <app-id> yes` — documented in `xdg-desktop-portal-kde!326`, merged in **January 2025, milestone 6.3: it is already in Trixie** [I]. For a non-sandboxed application the `app-id` comes from the **systemd unit name** (`app-<app-id>.service`), so REMOTIX can have one. It remains **plan B** — it goes through the portal anyway — but now it is verified, not conjectured |
| `zwlr_screencopy_manager_v1`, `ext_image_copy_capture_v1` | ⛔ **do not exist in KWin 6.3.6**: they are not filtered, they are **absent** [✗]. Of the wlroots family KWin implements only `wlr-layer-shell` and **`wlr-data-control`** |
| `org.kde.KWin.ScreenShot2` | **one shot per call**, raw image on a pipe. No continuity, no virtual output: not useful |
| `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` | it is the shortcut with which we measured (`banco/banco-altri.sh:33`). For the bench, not for the product — and it also opens `fake_input` to anyone |

---

### 4. Capture: `zkde_screencast_unstable_v1`

#### 4.1 The two halves, and the version

**[R]** The protocol is a shell of Qt signals (`kwin/src/wayland/screencast_v1.cpp`), the engine is
a **plugin** (`kwin/src/plugins/screencast/`, `EnabledByDefault: true`, loaded only in Wayland
mode, `main.cpp:28-35`).

**KWin 6.3.6 announces version 5** (`screencast_v1.cpp:18`, `static int s_version = 5`), even
though it is compiled against a `plasma-wayland-protocols` that declares 6. Our
`banco/zkde-screencast-unstable-v1.xml` **is the right copy**: it is v5, and the only difference from
master is the `serial` event added in 6.

#### 4.2 The requests

**[R]** `screencast_v1.cpp:89-142`:

| Request | `since` | Arguments | Notes |
|---|---|---|---|
| `stream_output` | 1 | `new_id`, `wl_output`, `pointer` | captures an existing output |
| `stream_window` | 1 | `new_id`, `window_uuid`, `pointer` | a window |
| **`stream_virtual_output`** | 2 | `new_id`, `name`, `width`, `height`, `scale`, `pointer` | **has the output created** — the analogue of `RecordVirtual` |
| `stream_region` | 3 | `new_id`, `x`, `y`, `width`, `height`, `scale`, `pointer` | a rectangle of the workspace |
| `stream_virtual_output_with_description` | 4 | as above + `description` | the description shows up in kscreen |

`pointer` is the cursor enum, and it **is not validated** (bare cast, `screencast_v1.cpp:91`):

| Value | Mode | Effect |
|---|---|---|
| 1 | `Hidden` | no cursor |
| 2 | `Embedded` | drawn into the buffer |
| **4** | **`Metadata`** | as `SPA_META_Cursor`, outside the image |

Send exactly 1, 2 or 4: with 0 or 3 no `case` matches, but the content flag is
raised anyway — inconsistent state.

#### 4.3 `stream_virtual_output`, in detail

**[R]** `screencastmanager.cpp:56-68`:

```cpp
auto output = kwinApp()->outputBackend()->createVirtualOutput(name, description, size, scale);
streamOutput(stream, output, mode);
connect(stream, &ScreencastStreamV1Interface::finished, output, [output] {
    kwinApp()->outputBackend()->removeVirtualOutput(output);
});
```

That is: **the output lives as long as the stream**. On the DRM backend it becomes a `DrmVirtualOutput`
(`drm_backend.cpp:340-347`), and from there follow five facts that weigh on everything else:

| | **[R]** |
|---|---|
| The output's name becomes **`"Virtual-" + name`** | `drm_virtual_output.cpp:32`. It is the **only** way to find your own `wl_output` again: the protocol does not tell the client which output it created. `wl_output` is announced at **v4**, which has `name` (`kwin/src/wayland/output.cpp:24,159`) |
| **A single mode**, of the requested size, at a **fixed 60000 mHz** | `drm_virtual_output.cpp:28`. Hence the impossibility of resizing (§8) |
| `width`/`height` are the mode's **pixels** | the XML calls them «logical»; `scale` ends up only in the logical geometry (`core/output.cpp:457-459`). **Pass `scale = 1` and the size in pixels**: `DrmVirtualOutput` uses the size as is, while the nested backend does `size * scale` (`wayland_backend.cpp:567`) — two different interpretations in the same protocol |
| The pacing is a **`SoftwareVsyncMonitor`**, i.e. a `QTimer` with millisecond granularity | `drm_virtual_output.cpp:24,51-56`; `softwarevsyncmonitor.cpp:44-56`. **It is the structural cap at ~60 fps**, and its irregularity |
| **No validation of the size** | `screencast_v1.cpp:98-112` passes two raw `int32`: no minimum, no maximum, no rejection of negatives (`stream_region`, by comparison, at least checks `isValid()`). **[?]** what it does with 0×0 or 16384² must be measured |

#### 4.4 The PipeWire node, and why Mutter's trap does not exist here

**[R]** The chain: request → `integrateStreams()` connects the three signals **first** and **then** calls
`init()` (`screencastmanager.cpp:131-145`) → `pw_stream_connect(... PW_DIRECTION_OUTPUT,
PW_STREAM_FLAG_DRIVER | PW_STREAM_FLAG_ALLOC_BUFFERS ...)` → at the `PAUSED` state KWin reads the
node id and announces it once only (`screencaststream.cpp:126-131`) → `created` event.

**Trap number 2 of `LEZIONI.md` §4 — «ci si iscrive all'annuncio del nodo prima di avviare
il flusso» — cannot arise on KDE.** On Mutter the announcement is a D-Bus broadcast on an object
created by the server, and whoever subscribes late misses something already gone by. Here the
`zkde_screencast_stream_unstable_v1` object has an **id allocated by the client in the same request**: the
events land in the connection's queue and arrive at the first dispatch. It is enough to register the
listener before `wl_display_dispatch` — and `banco/nodo-kwin.c:142-143` already does.

⚠ **But `failed` is synchronous** (`screencastmanager.cpp:82,141-144`): whoever does not have the listener active
misses it and waits forever. **A timeout is needed anyway.**

**[R]** The node id **does not change** for the whole life of the stream, including format
renegotiations and size changes.

#### 4.5 The format, line by line

**[R]** `screencaststream.cpp:735-783`. KWin offers **up to three** `SPA_PARAM_EnumFormat`:
DMA-BUF with a single modifier (after fixation), DMA-BUF with the whole list
(`MANDATORY | DONT_FIXATE`), and **shared memory** without the `modifier` property.

| Field | Value | Note |
|---|---|---|
| pixel format | 11 DRM↔SPA mappings; for output and region the DMA-BUF format is **always `DRM_FORMAT_ARGB8888`** | and for BGRA/RGBA KWin also announces the variant without alpha: **`BGRx` is negotiable**, and it is what RDP needs (`:775-783`) |
| `VIDEO_size` | single rectangle of the current size | `resize()` updates it in-band (§8.3) |
| **`VIDEO_framerate`** | **`SPA_FRACTION(0,1)` fixed** | ⛔ whoever proposes a different **fixed** rate finds no intersection: the same shape as Mutter's dead end, and our bench's `--fissa` option **is unusable on KWin** |
| `VIDEO_maxFramerate` | `RANGE(default = refreshRate/1000, 1/1, refreshRate)` | **it is the server-side brake**: KWin coalesces the damage and blits at that rate (`:507-516`) |
| buffers | **`RANGE(3, 2, 4)`** | the consumer can narrow, not widen. Our bench asks for `RANGE(4,2,8)`: they intersect on 2..4 |
| data type | `1 << SPA_DATA_DmaBuf` **or** `1 << SPA_DATA_MemFd` | never a union; **`MemPtr` is never offered**: the consumer does the `mmap` |

⚠ **The brake's arithmetic is integer, in milliseconds** (`:507-516`): asking for 60 you get an
interval of 16 ms (≈62 fps), asking for 30 you get 33 ms (≈30.3). The accumulated damage is not
lost.

⛔ **And if a modifier fails, it is removed for good.** `onStreamParamChanged` tries to actually
allocate a buffer (`testCreateDmaBuf`, `:920-951`); if it fails, those modifiers
drop out of future offers (`:260-264`): a client that insists will not get DMA-BUF a second
time.

**The metadata offered**, always (`:196-217`):

| Meta | Size |
|---|---|
| `SPA_META_Header` | `sizeof(spa_meta_header)` |
| `SPA_META_VideoDamage` | `RANGE(16 regioni, 1, 16)` |
| `SPA_META_Cursor` | bitmap up to **256×256** |
| `SPA_META_SyncTimeline` | **only with DMA-BUF** |

#### 4.6 ✅ Whole frames, not a «diff» — the difference that matters

**[R]** `screencaststream.cpp:618` → `outputscreencastsource.cpp:63-80`:

```cpp
GLFramebuffer::pushFramebuffer(target);
outputTexture->render(textureSize());   // the WHOLE texture, always
GLFramebuffer::popFramebuffer();
```

No scissoring, no use of the damaged region. The same for the in-memory branch
(`screencastutils.h:42-77`) and for the region. And the source texture is itself complete: the
output's layer recycles a swapchain with a *damage journal* and **repairs each slot according to its
age** before redrawing it (`drm_virtual_egl_layer.cpp:76-88`,
`drm_egl_layer_surface.cpp:192-199`).

| | Mutter (measured, R29) | **KWin 6.3.6** [R] |
|---|---|---|
| Content of the lent buffer | **a *diff*** on the recycled buffer | **whole frame** |
| Recycled buffers | 4 | 2–4, default 3 |
| Declared damage | yes | yes, up to 16 rectangles, then the *bounding rect* |

> ✅ **Direct consequence for the defect that keeps zero-copy off on GNOME.** R29's accumulation
> surface **is not needed on KWin**: the damage serves to avoid re-encoding what has not changed,
> not to rebuild the frame. Whoever brings capture to KDE does not inherit that debt.

The damage already arrives **in pixels** (`outputscreencastsource.cpp:92-97`), and the list is closed by a
sentinel region `SPA_REGION(0,0,0,0)` (`:703-728`).

#### 4.7 ⛔ The real trap: the cursor's «corrupted» buffers

**[R]** `screencaststream.cpp:659-664`:

```cpp
if (effectiveContents & Content::Video) {
    spa_data->chunk->flags = SPA_CHUNK_FLAG_NONE;
} else {
    // in pipewire terms, corrupted means "do not look at the frame contents" and here they're empty.
    spa_data->chunk->flags = SPA_CHUNK_FLAG_CORRUPTED;
}
```

In `Metadata` cursor mode, **every pointer movement** produces a buffer without
`m_source->render()` (`:447-451`, `:590-596`): inside are the **stale** pixels from two to four
frames earlier, and the only indication is that flag.

> ⛔ **It is the functional analogue of Mutter's trap, in a new guise**: a consumer that
> ignores `chunk->flags` shows an old frame **at every mouse movement**. kpipewire
> handles it (`kpipewire/src/pipewiresourcestream.cpp:618-621`); **`banco/misura-cattura.c` does not**, and
> counts them as delivered frames — i.e. our fps measurement on KWin can be inflated by moving the
> mouse. On an unattended desktop the mouse is still and the 7 August measurements probably
> hold, but the count must be made honest before measuring again.

#### 4.8 ✅ Synchronisation: **KWin does it**, and it explains one of our dead ends

**[R]** `screencaststream.cpp:637-655`. With explicit sync active KWin **does not wait** for
GPU completion and puts the points in `acquire_point`/`release_point`; without it, it does **`glFlush()`** — and
**`glFinish()` on NVidia and llvmpipe**, with the comment *«Implicit sync is broken on Nvidia and with
llvmpipe»*.

> ⛔ **`LEZIONI.md` §8 records as a dead end «aspettare la *fence* implicita del DMA-BUF: non
> cambia niente, è quella sbagliata».** KWin's code says why in general: **there is no
> implicit fence to wait for if whoever draws did not set one.** The right question to ask
> Mutter is not «la fence è pronta?» but «Mutter fa il flush?». It is a new hypothesis on a defect we
> had left open, and checking it costs nothing.

**The contract of `SPA_META_SyncTimeline`, which was not written down anywhere** [R]
(`screencastbuffer.cpp:86-107`, `screencaststream.cpp:534-537`, `606-613`, `639-647`):

- two extra `spa_data`, of type `SPA_DATA_SyncObj`, at indices `planeCount` and `planeCount+1`,
  **with the same fd**; `blocks = planeCount + 2`;
- `acquire_point` and `release_point` in the metadata;
- the producer **does not reuse the buffer** until the `release_point` has materialised;
- KWin offers **two** `SPA_PARAM_Buffers`: the first with `metaType` `SPA_META_SyncTimeline` marked
  `MANDATORY`, the second a fallback «per implicit sync o MemFd». **Asking for the timeline is a
  deliberate choice of the consumer**, not an accident.

For REMOTIX: implicit sync is the short road and is enough, because KWin does the flush. Explicit is
a later optimisation.

> #### ⚠ MEASURED — «la fa KWin» must be taken literally: **flush is not finish**
>
> **[M] 8 August 2026, with a moving scene** (`weston-simple-egl` full screen) and the
> meter querying the implicit fence with `poll(POLLIN, 0)` on the DMA-BUF descriptor —
> **the same method with which we measured Mutter**, so the two numbers are comparable:
>
> | path | frames | «disegno non finito» |
> |---|---|---|
> | **DMA-BUF** | 594 in 10.03 s | **830 of 830** |
> | in memory (MemFd) | 435 in 10.03 s | **0** |
>
> ⛔ That is, **on this machine 100 % of DMA-BUF buffers arrive with drawing still in progress.** It does not
> contradict §4.8: KWin does `glFlush()`, which **submits** the work to the GPU and does not wait for it to be
> finished (`glFinish()` does that **only** on NVidia and llvmpipe — i.e. exactly where the implicit fence is
> broken). On AMD and on Intel, therefore, **the fence is there and it is the consumer that must wait for it.**
>
> ✅ **The good news stays intact, and it is a different one**: the frames are **whole** (§4.6), so
> R29's defect — the «diff» on recycled buffers, which made us switch off zero-copy on GNOME —
> **does not recur**. On KDE zero-copy requires *one* thing: waiting for the fence before
> encoding, which is the correct behaviour of any consumer.
>
> ⚠ And the buffer count: 830 buffers against 594 frames counted, with «danno parziale 829,
> pieno 1». The ~236 difference are most likely the **cursor-only** buffers of §4.7, which the
> meter discards: one more reason to make that count honest before quoting it.

#### 4.9 Lifecycle — and the two ways of losing the stream

**[R]** `screencaststream.cpp`, `screencastmanager.cpp`, `outputscreencastsource.cpp`:

| Event | What KWin does |
|---|---|
| the Wayland client disconnects | `finished()` → `close()`; for a virtual output, `removeVirtualOutput()` |
| **the PipeWire consumer detaches** (`UNCONNECTED`) | ⛔ **`close()`**: the stream does not survive, and with it **the virtual output dies** (`:142-144`) |
| the consumer pauses | `m_source->pause()`: it disconnects from the damage |
| the consumer restarts (`STREAMING`) | ✅ `resume()` → **a full frame immediately** (`outputscreencastsource.cpp:99-109`) |
| **the output is disabled** (`enabled=false`, for example by kscreen) | ⛔ `closed()` → stream dead (`outputscreencastsource.cpp:27-32`) |
| PipeWire goes down (`-EPIPE`) | `close()` |

> ⛔ **Rule for the stage on KDE**: between two RDP clients **the `pw_stream` is not destroyed** — you do
> `pw_stream_set_active(false)`. An `UNCONNECTED` tears down the virtual output, and whoever reconnects
> finds nothing left. It is the same shape as the stage rule of §7.3 of `REFERENCE.md`, with a
> different mechanism.

**No «mandami un fotogramma pieno adesso» request** exists in the protocol [✗]: the full
frame arrives only on resume from pause. **R9 holds identically on KDE**: the last frame must be
kept and resent by us.

**Inactive session (VT switch) — good news to be confirmed.** `DrmGpu::setActive(false)`
inhibits the render loops **only** of the `m_drmOutputs`, and the virtual outputs live in another list
(`drm_gpu.cpp:710-723`, `drm_backend.cpp:340-347`); `present()` of a virtual output does no
KMS commit. **On paper capture continues with the session in the background** — exactly what
an unattended service needs. **[?]** to be measured with a `chvt`. The same for DPMS:
`DrmVirtualOutput::setDpmsMode()` only writes the state, it does not inhibit the render loop
(`drm_virtual_output.cpp:66-71`).

#### 4.10 The cursor

**[R]** The mode is decided **once only**, before `init()`, and **cannot be changed on a live
stream** (`setCursorMode`, `:915-918`).

With `Metadata` (`addCursorMetadata`, `:801-860`): position and hotspot **already scaled** and mapped
into the output, at every movement; **the bitmap only when the shape changes** (`bitmap_offset = 0`
otherwise — the consumer must **remember** the last shape); premultiplied RGBA format,
**truncated** to 256×256, not scaled; `id = 0` when the cursor is not visible.

Three constraints **[R]**:

1. the cursor is there **only if it is over our output** (`cursor->isOnOutput`,
   `outputscreencastsource.cpp:124-131`): with a virtual output you have to bring the pointer there, and
   provide for the «è andato altrove» case — the client is left without a cursor, without an error;
2. cursor updates go through the **same brake** as the video: negotiating a
   low `maxFramerate` **throttles the cursor too** (`:501-517`). Better to negotiate high and
   limit the encoding ourselves;
3. `Cursors::isCursorHidden()` zeroes it wholesale.

> **For RDP the right mode is `Metadata` (4)**: RDP has its own pointer channel, and so the cursor
> does not cost a re-encode. The price is §4.7. If one wanted to start simple, `Embedded` (2) is
> foolproof but pays a whole frame for every mouse movement.
>
> And a note worth more: **we already know the cursor position**, because we are the ones
> injecting the movement. The metadata is needed for the **shape** and for the movements we do not generate.

---

### 5. Without a monitor: the backends, and the GPU

#### 5.1 ⛔ Our measurement of 7 August is contradicted by the code

`REFERENCE.md` R32 and `LEZIONI.md` §3 say: *«KWin senza monitor disegna in software: col backend
`--virtual` non apre alcun nodo DRM e non carica alcuna libreria GL»*. The code says the opposite.

**[R]** `kwin/src/backends/virtual/virtual_backend.cpp:23-56`: the backend's constructor enumerates the
DRM devices with `drmGetDevices2()` and opens a **render node** (`DRM_NODE_RENDER`,
`renderD*`) with a direct `::open(O_RDWR)` — **without logind**. And `:73-81`:
`OpenGLCompositing` is declared **only if** that node opened; otherwise only
`QPainterCompositing` remains. The OpenGL renderer is **EGL on gbm** (`virtual_egl_backend.cpp:108-115`,
`EGL_PLATFORM_GBM_KHR`), with a swapchain of gbm buffers.

And the proof is **in our own table**: `banco/tabella-altri.txt` reports for KWin
`tipo=DMA-BUF`, `fence=1010`, 59.50 fps. But a screencast stream **can be DMA-BUF only if the
compositor is an `AbstractEglBackend`** (`screencaststream.cpp:920-925`, and `:154-155` for the choice
of buffer type). That is: **in that measurement KWin was already compositing on the GPU.**

The only causes of a `findRenderDevice() == nullptr`, from the code: no `/dev/dri` visible;
**permissions** on the render node (`render` group) — and then `Failed to open drm node: <path>` appears
(`core/drmdevice.cpp:77`, `qCWarning`, **visible by default**); gbm/Mesa missing.

> ⛔ **What must be done, and in which order.** The document is not corrected on a code reading:
> the measurement is redone, with the two proofs that do not depend on what KWin declares (§5.3). Then
> R32 is corrected with date and source. Until then, **the number «KWin: 60 fps a 4K» stays valid
> as a measurement and suspect as to its label**: what is in doubt is not the 60, it is the «in
> software».

> #### ✅ MEASURED — and the «in software» label was wrong
>
> **[M] Measurement M3, bench of 7 August 2026, `kwin_wayland --virtual` 6.3.6-1, Mesa 25.0.7.**
> The three proofs, all in agreement:
>
> | Proof | Outcome |
> |---|---|
> | DRM nodes opened by the compositor | **`/dev/dri/renderD129`** — a render node, open |
> | rendering libraries loaded | `libEGL.so.1.1.0`, **`libEGL_mesa.so.0.0.0`**, `libgbm.so.1.0.0`, `libgallium-25.0.7` |
> | global `zwp_linux_dmabuf_v1` | **announced, version 4** — and it is born only from `AbstractEglBackend::initWayland()` |
>
> **Verdict: KWin without a monitor composites on the GPU.** The code reading was right and our
> label was wrong: **R32 must be corrected**, the «60 fps a 4K» stays but it is not «in software».
>
> ⚠ **A trap in the proof, for whoever redoes it.** On Mesa 25 all gallium drivers — llvmpipe
> included — live in **a single** `libgallium-*.so`: so *«non vedo llvmpipe fra le librerie»*
> **proves nothing**, and the old search for `swrast_dri`/`llvmpipe` by name no longer works.
>
> ⛔ **And the proof I had taken as good on 7 August — «il render node aperto» — does NOT prove the GPU.**
> [M, 8 August] With `KWIN_COMPOSE=Q`, i.e. KWin **in QPainter**, `/dev/dri/renderD129` shows up as
> **open anyway**: the node is opened by `VirtualBackend`'s *constructor*, before the
> compositor is chosen. So that line says «il backend ha trovato un device», not «sta rendendo in GPU».
>
> ✅ **The proof that holds is only one, and KWin gives it away** (§5.3-bis): the renderer string, via
> `org.kde.KWin.supportInformation` on D-Bus. On the bench:
> `OpenGL renderer string: AMD Radeon RX 6800 (radeonsi, navi21, LLVM 19.1.7, DRM 3.64, 7.0)`,
> `Mesa 25.0.7`. No interpretation possible.
>
> The hierarchy of proofs, after the bench, from strongest to weakest:
>
> | Proof | What it really demonstrates |
> |---|---|
> | **renderer string** (`supportInformation`) | ✅ the exact driver and chip: **GPU or llvmpipe** |
> | `zwp_linux_dmabuf_v1` announced | **EGL yes/no** — with `KWIN_COMPOSE=Q` it disappears (0), with OpenGL it is there (1). It does **not** distinguish GPU from llvmpipe |
> | render node open | ⛔ **nothing**: open in QPainter too |
>
> ⚠ **And reading that `/proc` takes `sudo`, for a precise reason**: `/usr/bin/kwin_wayland`
> carries the extended attribute **`security.capability`** (verified: `cap_sys_nice`), and a binary with
> file capabilities is **not dumpable** — the kernel denies `/proc/<pid>/fd` and `/proc/<pid>/maps` even
> to the user who started it. It is not a defect of the bench. (Copying the binary to lose the xattr
> is **not** a viable shortcut: the copy does not load the QPA plugin `wayland-org.kde.kwin.qpa`
> and dies with `Aborted`.)
>
> 🟡 **What does remain open is the buffer type (M3d).** The stream negotiated on the bench is
> `1280x720 BGRx, modificatore 0x0, memoria` — i.e. **MemFd**, not DMA-BUF. But this does **not**
> contradict the verdict: it is *our* client that does not offer DMA-BUF (zero-copy has been postponed
> since phase 9). The criterion of §5.3 point 1 holds only the other way round: if the client offers
> DMA-BUF and KWin denies it, then KWin is in QPainter. To be redone when the client can offer it.

#### 5.2 The backends, and the choice between `--virtual` and `--drm`

**[R]** The selection is in `main_wayland.cpp:428-463`, and the order matters: `--drm` → `--x11-display` →
`--wayland-display` → `--virtual` → **then** the heuristic on the environment (`WAYLAND_DISPLAY` → nested
Wayland, `DISPLAY` → nested X11, **otherwise drm**).

> ⛔ **Hence an operating rule**: the backend is **always** passed explicitly. If REMOTIX runs
> inside a session where `WAYLAND_DISPLAY` or `DISPLAY` are set, without the option KWin picks
> the nested backend; with a clean environment it picks **drm** and without logind it dies.

| | `--virtual` | `--drm` with zero physical outputs |
|---|---|---|
| GPU | **yes**, on a render node, by default [R] | yes, on the primary node `card*` [R] |
| Prerequisites | **only r/w on `/dev/dri/renderD*`**; no logind, no seat, no DRM master (`Session::Type::Noop`, `main_wayland.cpp:513`) | **logind session activatable on a seat**, with `Activate` + `TakeControl` + `TakeDevice` (`session_logind.cpp:109-131`, `161-188`) |
| `stream_virtual_output` | ⛔ **does NOT work**: `VirtualBackend` does not override `createVirtualOutput()`, the base returns `nullptr` (`core/outputbackend.cpp:80-83`) → `sendFailed("Could not find output")` | ✅ works (`drm_backend.cpp:340-347`) |
| Outputs | fixed, decided at startup (`--output-count`, `--width`, `--height`, `--scale`) | none at startup; created at runtime |
| Direct scanout | no | yes (`drm_virtual_egl_layer.cpp:140-153`) |
| DRM modifiers | no: swapchain forced to `DRM_FORMAT_MOD_INVALID` | yes |
| GPU choice | **none**: takes the first one that opens, no variable [R] | `KWIN_DRM_DEVICES` |
| libinput / `/dev/input` | not needed: `createInputBackend()` is not overridden, no libinput | needed |
| If it fails | composites in software with two `qCWarning` | ⛔ `std::exit(1)`, **noisy** |

**[R]** `--drm` **starts with zero connectors plugged in**: `DrmGpu::updateOutputs()` creates nothing and
returns `true`, the primary GPU survives, `EglGbmBackend::init()` does not touch the outputs, and the
Workspace puts in a 1920×1080 `PlaceholderOutput` **not composited and not exposed as `wl_output`**
(`workspace.cpp:1217-1231`). At the first `stream_virtual_output` the placeholder is destroyed and
a real `wl_output` is born. And it **never accepts a render node**: `drmIsKMS()` discards it
(`drm_backend.cpp:216-220`), the udev enumeration looks only for `card[0-9]`.

⛔ **`--drm` with a Noop session is impossible by construction**: `NoopSession::openRestricted()`
always returns `-1` (`session_noop.cpp:41-44`), so every `addGpu` fails and KWin exits.

> #### ⛔ MEASURED — `--drm` is **not** viable without a seat, and so the choice is already made
>
> **[M] Measurement M2, bench of 7 August 2026.** It was «la domanda che decide», and the answer is **no**.
> From a session without a seat (`loginctl show-session`: `Seat=` empty, `Remote=yes`, `VTNr=0`, with
> `seat0` existing and the console on tty1), `kwin_wayland --drm` **exits with status 1** saying:
>
> ```
> kwin_core:        Failed to activate /org/freedesktop/login1/session/_351 session.
>                   Maybe another compositor is running?
> kwin_wayland_drm: failed to open drm device at "/dev/dri/card0"
> kwin_wayland_drm: failed to open drm device at "/dev/dri/card1"
> kwin_wayland_drm: No suitable DRM devices have been found
> ```
>
> ⚠ **And it is not a Unix permissions problem**, which is the convenient explanation to rule out: in the same
> environment and with the same groups, the `--virtual` round **opens `renderD129` without difficulty**. The
> breaking point is `Activate()`, i.e. exactly the line of `session_logind.cpp:109-131` that the
> table above gives as a prerequisite.
>
> **Consequence for the phase**: the only way to have `--drm` would be a session **on `seat0`**,
> i.e. imitating a display manager and **occupying the physical console** — and then it is no longer a remote
> service living alongside the local user. So **the «scelta fra `--virtual` e `--drm`» (§13.4,
> decision 1) is not a choice**: it is `--virtual`, and with it the price of §8.1 (no
> `stream_virtual_output`, no resizing before KWin 6.8).
>
> ⚠ **Bench note**: every SSH command opens a **new** logind session (49, 50, 51…), all without a
> seat. A session identifier read in one command is not valid in the next one — «No
> session '49' known» — and whoever writes tests on logind must re-read it every time.

#### 5.3 How to establish whether KWin is on the GPU or in software

**[R]** The two proofs that do not depend on what KWin declares:

1. **The buffer type the screencast stream offers.** DMA-BUF ⇒ EGL/gbm on a real DRM node;
   only MemFd ⇒ QPainter, i.e. CPU (`screencaststream.cpp:920-925`, `154-155`). No way to
   simulate one with the other.
2. **The presence of the `zwp_linux_dmabuf_v1` global**, created lazily and **only** by
   `AbstractEglBackend::initWayland()` (`abstract_egl_backend.cpp:118-196`,
   `wayland_server.cpp:516-530`). If `wayland-info` on KWin's socket does not list it, KWin is in
   QPainter.

Plus, from the operating system: `ls -l /proc/$(pidof kwin_wayland)/fd | grep dri`.

⚠ **What instead is not enough**: `compositingType` distinguishes OpenGL from QPainter, **not GPU from
software**; and `supportInformation` must be read **together with** the `OpenGL renderer string` line, because
llvmpipe and softpipe do **not** make KWin fall back to QPainter (`m_recommendedCompositor` stays
`OpenGLCompositing`, `glplatform.h:331`, `glplatform.cpp:876-886`). *«Compositing Type: OpenGL»* on
llvmpipe is possible, and it is the worst case: software rendering disguised as GPU.

#### 5.4 ⛔ `KWIN_COMPOSE` does not protect at startup

**[R]** The enforcement of `KWIN_COMPOSE` is `qApp->quit()` (`compositor_wayland.cpp:164`), but
`createRenderer()` runs inside `performStartup()`, called **synchronously** by
`Application::start()` **before** `a.exec()` (`main.cpp:144`, `main_wayland.cpp:620-622`). Without an
event loop, `quit()` is inert: the candidate loop goes on, QPainter succeeds, and **KWin starts
in software despite `KWIN_COMPOSE=O2`**, with a single `qCCritical` to bear witness.

> It is lesson 1.8 of `LEZIONI.md` in someone else's house: **when a component can decide by itself,
> you have to tell it what to do — and check that it obeyed.** All the measurements taken with
> `KWIN_COMPOSE=O2` assume that switch works.

> #### ⛔ MEASURED — `KWIN_COMPOSE=O2` **does not protect**, and the code reading was right
>
> **[M] Measurement M4, 8 August 2026.** To answer, OpenGL had to be made *impossible*, and making it
> *slow* was not enough: `LIBGL_ALWAYS_SOFTWARE=1`, `GALLIUM_DRIVER`, `MESA_LOADER_DRIVER_OVERRIDE`
> and `__EGL_VENDOR_LIBRARY_DIRS` **have no effect at all** on KWin (the renderer stays
> `AMD Radeon RX 6800 (radeonsi)`: verified with `supportInformation`). The condition is obtained
> by removing access to the render nodes — on the bench with a private mount namespace.
>
> Then, with all render nodes inaccessible:
>
> | | outcome |
> |---|---|
> | without `KWIN_COMPOSE` *(control)* | `Configured compositor not supported by Platform. Falling back to defaults` → **QPainter**, and KWin starts |
> | **with `KWIN_COMPOSE=O2`** | `Compositing forced to OpenGL mode by environment variable` → **`Falling back to defaults`** → **`QPainter compositing has been successfully initialized`**, and **KWin starts** |
>
> ⛔ **So the switch is inert**, exactly as §5.4 said: the `qApp->quit()` runs before the
> event loop. **Operational consequence**: `KWIN_COMPOSE=O2` must not be used as a guarantee in any
> recipe of ours nor in any bench; the only way to know how KWin is rendering is to **ask it**
> (the renderer string, §5.1). And capture stays available in QPainter too: `zkde_screencast`
> is announced and the `zwp_linux_dmabuf_v1` global disappears — the only visible sign of the fallback.

#### 5.3-bis ✅ The direct proof: asking KWin which renderer it uses

**[M, 8 August 2026]** The measurement that settles every doubt about GPU-or-software, and that needs neither
`/proc` nor `sudo`:

```sh
gdbus call --session --dest org.kde.KWin --object-path /KWin \
    --method org.kde.KWin.supportInformation | grep -oE 'OpenGL renderer string: [^\\]*'
```

It works on bare KWin and inside a Plasma session. In QPainter the line **is not there** — which is
itself an answer.

#### 5.6 ⚙ Choosing WHICH GPU the compositor uses — decided by the user

> **User's decision, 8 August 2026: «non usare la Radeon, usa la Intel integrata».**
> The test machine has two GPUs: Intel AlderLake-S (i915) on `renderD128` and Radeon RX 6800
> (amdgpu) on `renderD129`.

**[R]** With `--virtual` **there is no lever at all**: `findRenderDevice()`
(`virtual_backend.cpp:23-56`) iterates `drmGetDevices2()` and takes **the first one that opens**, without
looking at any variable — `KWIN_DRM_DEVICES` applies only to the `drm` backend. On the bench the order
puts the Radeon first, and KWin takes that one.

**[M]** So the Intel is obtained in one way only: **making the other GPU not openable by that
process**. Two roads tried, and only one is good:

| Road | GPU | Capture gate |
|---|---|---|
| `InaccessiblePaths=/dev/dri/renderD129` in the unit | ✅ Intel | ⛔ **closed** (§3.3-bis, box) |
| `DeviceAllow=` + `DevicePolicy=closed` | ⛔ no effect: the Radeon stays (in a **user** unit device control is not delegated) | ✅ open |
| ✅ **node permissions** (`renderD129` out of the `render` group) | ✅ **Intel** | ✅ **open**, and PipeWire stream obtained |

✅ **The good road is the third**, and for the product it is written as a **udev rule** that assigns the node
of the GPU not to be used to a group the service's user does not have — identifying the card by
**PCI id** (`/dev/dri/by-path/pci-0000:03:00.0-render`), because the node number is not stable.

⚠ **And the price must be stated**: denying the node via permissions denies it **to the user's whole session**,
not just to the compositor. If one day the Radeon were needed for something else in the same session, the
right road becomes a different one (for example having *us* choose the device and not KWin, which today
is not possible without touching KWin).

#### 5.7 📊 How much capture delivers **on the integrated Intel** — the table that matters for the product

**[M] 8 August 2026.** The tables in `REFERENCE.md` R32 are from the Radeon; these are from the GPU the
product will use. Measurement of **capture alone**, declared and moving scene
(`weston-simple-egl` full screen, synchronised to redraw), declared cap 60 fps, 10
seconds per cell, `kwin_wayland --virtual` with the Radeon denied:

| Resolution | zero-copy (DMA-BUF) | in memory (MemFd) |
|---|---|---|
| 1280×720 | **59.4** *(median 16.5 ms)* | 49.6 *(20.2 ms)* |
| 1920×1080 | **59.2** *(17.2 ms)* | 43.3 *(23.2 ms)* |
| 2560×1440 | **59.3** *(17.2 ms)* | 37.0 *(27.0 ms)* |
| **3840×2160** | **59.0** *(17.2 ms)* | **27.0** *(37.4 ms)* |

⭐ **Two readings, and they are the most important of the whole phase:**

1. ✅ **At zero-copy resolution costs nothing**: 59 frames per second **from 720p to 4K**, with
   the median of the intervals holding at 17 ms. The user's requirement — *«30 a 1080p, 60 a 4K»*
   (`REFERENCE.md` R32, and the project memory) — **is reachable on an integrated Intel**.
2. ⛔ **In memory resolution costs everything**: from 49.6 to **27.0** going up to 4K, i.e. less than half
   of what is needed. **The bottleneck is the copy**, not the compositor and not the GPU.

> **Hence the consequence for the plan**: on KDE zero-copy is not an optimisation, it is **the
> condition** for 60 at 4K. And on KDE it is also easier than on GNOME, because the frames are
> whole (§4.6) and all that remains is waiting for the fence (§4.8). Phase 9, postponed on GNOME because of the
> «diff», must be taken up again here with a different perspective.

And the fallback is silent almost everywhere: the lines that tell of it are `qCDebug`, off by
default. The only visible one is *«Configured compositor not supported by Platform. Falling back to
defaults»* (`:139`) — which fires precisely in the «il render node non si è aperto» case. On the
`drm` backend not even that: `supportedCompositors()` always declares `{OpenGL, QPainter}`.

#### 5.5 Xwayland — better than on GNOME

**[R]** `--xwayland` is optional on the command line and at build time; startup is **lazy** (it starts
only when a client touches the X11 socket, `xwaylandlauncher.cpp:95-99`) and **non-blocking**
(`-displayfd` + `QSocketNotifier`); a failure produces a `qCWarning` and **the compositor
carries on**; a crash has a restart policy with a counter.

> Open question no.8 of `SPECIFICA.md` — «Xwayland non completa l'avvio e a volte si porta
> dietro il compositore» — **has no equivalent on KWin**: here an absent or stuck Xwayland does not
> hang the compositor. But see §6.4: on Plasma, X11 is needed **by ksmserver**, and therefore
> `--xwayland` becomes mandatory for another reason.

---

### 6. The Plasma session without a monitor

#### 6.1 The recipe

**[R]**, and the mandatory variables are only two:

```sh
# 1. environment built from scratch (env_clear), with:
XDG_RUNTIME_DIR=/run/user/1000                         # mandatory: without it, wl_socket_create()
                                                       # returns NULL and the wrapper does qFatal
                                                       #   [R] wl-socket.c:132-136
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus  # mandatory: without it, return 1
                                                       #   [R] startplasma-wayland.cpp:58-61
HOME= USER= PATH= SHELL=
LANG=it_IT.UTF-8                                       # recommended [R] startplasma.cpp:213-216

# ⛔ do NOT set DISPLAY, WAYLAND_DISPLAY, QT_QPA_PLATFORM
#    [R] main_wayland.cpp:452-463, ksmserver/main.cpp:106-117

# 2. override of the compositor unit — on Wayland it is the only lever
#    $XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d/remotix.conf
[Service]
ExecStart=
ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width W --height H --no-lockscreen
#    then: systemctl --user daemon-reload

# 3. start
exec /usr/bin/startplasma-wayland
```

**What Plasma sets by itself**, and which therefore need not be declared (`startplasma.cpp:353-414`,
`startplasma-wayland.cpp:64`): `XDG_CURRENT_DESKTOP=KDE`, `XDG_SESSION_TYPE=wayland`,
`KDE_FULL_SESSION`, `KDE_SESSION_VERSION=6`, `KDE_SESSION_UID`, `XDG_MENU_PREFIX`,
`XDG_CONFIG_DIRS`, the `XKB_DEFAULT_*` from locale1, `LANG`/`LC_*` from `plasma-localerc`. And
`WAYLAND_DISPLAY`/`DISPLAY`/`XAUTHORITY` are exported by the compositor wrapper
(`kwin_wrapper.cpp:157-163`).

> ⛔ **And among those that «mette Plasma da sé» there is one that is not a detail: `XDG_MENU_PREFIX`.**
> [M, 7 August 2026] Without it **the capture permission does not work**, for the reason
> explained in §3.3-bis: the service index stays empty and KWin finds no `.desktop`. In
> this recipe it is covered, because `startplasma` sets it
> (`startplasma.cpp:366` — and it does **not** run `kbuildsycoca6`: the index builds itself in the first
> KDE process that uses it, which inside the session already has the right prefix).
>
> **The danger is for whoever does not go through `startplasma-wayland`**: a bench that starts `kwin_wayland` by
> hand, a maintenance script or a `kbuildsycoca6` launched from an SSH shell **without** the
> prefix overwrite the good index and close the gate with the compositor already running, without a
> message. Whoever writes tests exports `XDG_MENU_PREFIX=plasma-` **always**.

> #### ✅ MEASURED — the recipe works, with three clarifications
>
> **[M] 8 August 2026.** `startplasma-wayland` started from an SSH shell with the environment above and the
> unit drop-in: **plasmashell appears in 1 second**, the socket is `wayland-0`, KWin answers on
> D-Bus, the capture is authorised and a PipeWire stream comes up (§3.3-bis). The three clarifications:
>
> 1. ⛔ **no `InaccessiblePaths=` (nor anything else implying a mount namespace) in the drop-in**:
>    it closes the capture gate (§3.3-bis, box). For the GPU the node permissions are used
>    (§5.6).
> 2. ⚠ **`ksmserver` and `Xwayland` did not start at all** (zero processes), and the session
>    worked anyway: plasmashell, kwin_wayland and kded6 up. On this, §6.4 must be re-read — the
>    constraint «`--xwayland` è obbligatorio per ksmserver» **did not show up** in this test, and
>    Xwayland starts lazily (§5.5). It remains to be understood whether ksmserver is needed for the *orderly logout* or
>    for session restore: **do not remove `--xwayland` before having verified it.**
> 3. ⚠ The session **creates 23 configuration files** in `~/.config` on first start (`kdeglobals`,
>    `plasmashellrc`, `plasma-localerc`, `kwinrc`…). It is normal, but worth knowing: the first session
>    writes into the user's home, and `plasma-localerc` fixes the locale (on the bench: `LANG=C.UTF-8`).

> ✅ **The silent defect paid for on GNOME is not here.** `ConditionEnvironment=` **does not exist in
> any unit** of the seven repos [R]: on GNOME the Shell unit carried
> `ConditionEnvironment=XDG_SESSION_TYPE=wayland` and without that variable the compositor did not
> start at all, without anyone explaining it (§5.9-bis of `SPECIFICA.md`).
>
> ✅ **And Plasma does by itself the cleanup we do by hand.** `dropSessionVarsFromSystemdEnvironment()`
> (`startplasma.cpp:445-473`) removes at **every start** from the systemd manager's environment the session
> variables (`DISPLAY`, `XAUTHORITY`, `WAYLAND_DISPLAY`, `WAYLAND_SOCKET`, all the `XDG_*`), with
> the comment: *«Those can be leftovers from previous sessions … e.g. `$DISPLAY` might break
> kwin_wayland»*. It is our lesson «chi sopravvive al logout non riusa niente della sessione
> morta», applied by the desktop itself.

#### 6.2 The chain, and who launches the compositor

**[R]** `startplasma-wayland` **does not launch KWin**: it does `StartUnit("plasma-workspace-wayland.target")`
(`startplasma.cpp:726`), and the unit is

```ini
# kwin/plasma-kwin_wayland.service.in
ExecStart=<bindir>/kwin_wayland_wrapper --xwayland
BusName=org.kde.KWinWrapper
PartOf=graphical-session.target
```

The wrapper **passes all its own arguments on** to `kwin_wayland` (`kwin_wrapper.cpp:128-130`): it is enough to
add them to the `ExecStart`. The recipe for doing so without touching `$HOME` is KDE's own —
a copy in `$XDG_RUNTIME_DIR/systemd/user.control` plus `daemon-reload`
(`login-sessions/startplasma-dev.sh.cmake:8-13`).

The actual order that results: `plasma-kwin_wayland` → `kcminit` → `kded6` →
**`ksmserver`** → `plasmashell` → `plasma-core.target` → `plasma-workspace.target`
(powerdevil, kglobalaccel, kwallet-pam, …) → `graphical-session.target` → autostart.

⚠ **Two fragilities to know** [R]: the compositor unit declares `BusName=` **without
`Type=dbus`**, so the ordering of ksmserver rests only on `After=`, that is on the *exec* of the
wrapper and not on the export of `DISPLAY` — in the classic path the comment is explicit: *«This must
block until started as it sets the WAYLAND_DISPLAY/DISPLAY env variables needed for the rest of the
boot»* (`plasma-session/startup.cpp:162-165`). And `plasma-core.target` /
`plasma-workspace.target` have `RefuseManualStart=yes`: **only**
`plasma-workspace-wayland.target` is started.

#### 6.3 ✅ No logind session on a seat is needed — with `--virtual`

**[R]** `--virtual` forces `Session::Type::Noop` (`main_wayland.cpp:513`): **no logind, no
seat, no `/dev/dri` via `TakeDevice`, no `/dev/input`**. `XDG_SEAT` and `XDG_VTNR` **are not
read by any of the seven repos** [✗]. It is the exact equivalent of our finding on
`gnome-session` (§5.9-bis of `SPECIFICA.md`).

With `--drm`, instead, an **activatable** logind session on a seat is needed: that is, what a
login manager does, and which by definition we do not have. **It is the central compromise of the phase**
(§13).

#### 6.4 ⛔ `--xwayland` is not optional, and the reason is ksmserver

**[R]** `plasma-workspace/ksmserver/main.cpp`: it forces `QT_QPA_PLATFORM=xcb` (`:106-107`, *«force xcb
QPA plugin as ksmserver is very X11 specific»*), builds a `QGuiApplication`, and at `:124`
dereferences the X11 display **without any null check**. And `ksmserver` is `Requires=` of
`plasma-core.target`, which is `Requires=` of the chain up to the session target: **a fault in it
brings down the whole session.**

> That is: KWin does not need Xwayland, **Plasma does**. And our bench line
> (`banco/banco-altri.sh:33`) starts KWin **without** `--xwayland`: with that line a **Plasma
> session does not start**. The 59–60 fps measured hold for **bare KWin**, not for a complete Plasma
> session — and this is the second label to correct on the measurements of 7 August.

#### 6.5 Logout: there is no `RegisterClient`, and the good path is passive

**[R]** There are four actors: `plasma-shutdown` (`org.kde.Shutdown`), `ksmserver-logout-greeter`
(`org.kde.LogoutPrompt`), `ksmserver` (`org.kde.ksmserver`), KWin (`org.kde.KWin` `/Session`).

| How to notice it | When | Risk |
|---|---|---|
| ✅ **`NameOwnerChanged` on `org.kde.Shutdown`** (activatable name: it appears when the logout begins, `plasma-shutdown/shutdown.cpp:20-23`) | **at the start** | none: we are spectators |
| ✅ **`NameOwnerChanged` on `org.kde.KWinWrapper`** (disappears when the session is over) | at the end | none |
| ⚠ **XSMP** registration with ksmserver (`$SESSION_MANAGER`, libSM/libICE) | at the start, with an obligation to answer | **the hostage rule applies identically**: whoever registers and does not answer holds up the logout by **15 s** (`ksmserver/logout.cpp:293-303`), then is ignored |

The first two are exactly what `startplasma` does to decide to exit
(`startplasma.cpp:673-689`). **It is the path to take**: it costs two subscriptions on the bus and does not
put the user's session at stake. The true equivalent of `RegisterClient` exists — but it is XSMP over
ICE, it requires `libSM`/`libICE` and a `DISPLAY`, and `org.kde.KSMServerInterface` **has no
«la sessione sta finendo» signal** [R].

**Commanding the logout from outside** [R]:

| What is wanted | Call |
|---|---|
| without confirmation (= GNOME's `Logout(1)`) | `org.kde.Shutdown` `/Shutdown` `logout()` |
| with confirmation | `org.kde.LogoutPrompt` `/LogoutPrompt` `promptLogout()` |
| **forced** (`Logout(2)` **does not exist** [✗]) | `StopUnit("plasma-workspace.target", "fail")` — it is what `plasma-shutdown` does at the end (`shutdown.cpp:151-157`) |
| brutal | `org.kde.KWin` `/Session` `quit()` |

⛔ **And the orderly path can cancel itself.** `KWin::SessionManager::closeWaylandWindows()`
(`kwin/src/sm.cpp:422-508`): after **10 s** it shows a persistent notification with *Cancel Logout* /
*Log Out Anyway*, and if **nobody answers** it waits up to **2 minutes** before proceeding. In an
unattended session nobody ever answers: the second half of our `sgombera` (§5.10 of
`SPECIFICA.md`, `Logout(1)` and then `Logout(2)`) **must be redesigned on KDE** — the second step is
`StopUnit`.

And to keep windows nobody will see from appearing: `ksmserverrc [General] confirmLogout=false`
(`sessionmanagementbackend.cpp:49-52`).

#### 6.6 ✅ The session bus does not die — if it is the user one

**[R]** In all seven repos **there is no reference to `dbus.service`, `dbus-launch` or
`dbus --exit-with-session`** outside the tests: Plasma **does not manage the bus lifecycle**. It
expects it up, or it gets wrapped by `plasma-dbus-run-session-if-needed`, which puts
`dbus-run-session` in front **only if** `DBUS_SESSION_BUS_ADDRESS` is empty.

> ✅ **Consequence**: if we use the **user** bus (`/run/user/UID/bus`) and declare it
> in the environment, **it survives the logout** and the connection stays valid. The two defects paid for on
> GNOME — the connection to throw away and reopen, and `exit-on-close` calling `raise(SIGTERM)` on
> our behalf (§7.4 of `REFERENCE.md`) — **do not show up**, as long as `dbus-run-session` is not left
> to do its work. **It is our choice, and it must be made for the user bus.**

> #### ✅ MEASURED — measurement M9: the logout takes away nothing of ours
>
> **[M] 8 August 2026.** Real Plasma session, closed with `org.kde.Shutdown.logout()` — the passive
> sentinel of §6.5, called as the product would call it:
>
> | After the logout | |
> |---|---|
> | `plasmashell`, `kwin_wayland`, `kded6` | **all gone** (0 processes) |
> | the `wayland-0` socket | **gone** |
> | **the user bus** | ✅ **still answers** (`GetId` succeeds on the same connection) |
> | `systemd --user` | ✅ alive (`degraded`, because of terminated session units) |
>
> So the «bus d'utente» choice is confirmed in the field, and the GNOME defect **does not reappear**.
> ⚠ A detail not to forget: after the logout the socket is `wayland-0` *free again*, and on
> session restart the number **may change** — it must be re-read, as the paragraph below says.

**Restarting the session from the same process works** [R], and Plasma provides for it: `ResetFailed` and
`Reload` at every start (`startplasma.cpp:648-649`). `WAYLAND_DISPLAY` changes (the socket is the first
free `wayland-N`), as do `DISPLAY` and `SESSION_MANAGER`: **they must be re-read, not remembered.**

#### 6.7 The keyboard layout

**[R]** On Wayland it is imposed by **KWin**, which reads `kxkbrc [Layout]` by itself (a separate `kxkb`
no longer exists). Three ways for us:

1. **`XKB_DEFAULT_LAYOUT`/`_VARIANT`/`_MODEL`/`_OPTIONS` in the environment of `kwin_wayland`**, which
   `applyEnvironmentRules()` uses as fill-in (`xkb.cpp:557-575`); with
   **`KWIN_XKB_DEFAULT_KEYMAP=1`** the use of the environment alone is **forced**, ignoring `kxkbrc` and
   locale1 (`xkb.cpp:522-545`). **It is the clean lever**: the layout comes from the client and is put
   in the environment before starting the compositor;
2. D-Bus `org.kde.keyboard` `/Layouts`: `getLayout`, **`setLayout(index)`**, `getLayoutsList`,
   `switchToNextLayout` (`keyboard_layout.cpp:186-245`), without permissions — but it **only chooses among the
   layouts already loaded**;
3. write `kxkbrc` and make KWin reload (`org.kde.KWin` `/KWin` `reconfigure()`). **[?]** which
   of the two suffices.

And in any case: **we read the session keymap from libei** (§7.4), as on GNOME. This section
is for the case where one wants to *impose* it.

#### 6.8 Animations: no per-capture hook

**[R]** Mutter offers `disable-animations` as an option of the capture session; KWin's
protocol has **a single** option per stream — the cursor mode — and in the capture plugin there is not one
line about animations [✗]. On KDE they are switched off **per session**:

| Lever | Where | Notes |
|---|---|---|
| `KWIN_EFFECTS_FORCE_ANIMATIONS=0` | environment of `kwin_wayland` | declares animations **unsupported** (`effecthandler.cpp:1425-1433`); read into a `static`, **not changeable live** |
| `AnimationDurationFactor=0` in the `[KDE]` group | `kwinrc` **and** `kdeglobals` | applies **live**, a `KConfigWatcher` watches it (`options.cpp:96-101`); ⚠ `0` does not zero the times, it brings them to **1 ms** (`effect/effect.cpp:447-457`) |

---

### 7. Input: KWin speaks libei

#### 7.1 ✅ A real EIS backend, and it opens with a D-Bus call

**[R]** `kwin/src/plugins/eis/`, 1829 lines, plugin **active by default**, loaded only in
Wayland mode. The descriptor is obtained like this:

```
service      org.kde.KWin
object       /org/kde/KWin/EIS/RemoteDesktop
interface    org.kde.KWin.EIS.RemoteDesktop
method       connectToEIS(i capabilities) → (h fd, i cookie)
             disconnect(i cookie)
```

(`eisbackend.h:39-40`, `eisbackend.cpp:70-104`; signature confirmed from the other side,
`xdg-desktop-portal-kde/src/remotedesktop.cpp:457-460`). The mask is the xdg portal's:
**keyboard 1, pointer 2, touch 4** → for us **7**. The `cookie` is used to close.

> ⛔ **No check on the caller.** `registerObject` is `ExportAllInvokables` without a filter, and
> `message().service()` is used **only** for the lifetime (if the caller dies, the context
> drops). No pid, no `.desktop`, no `X-KDE-DBUS-Restricted-Interfaces`, no dialog:
> the mechanism exists in KWin but **in all of 6.3.6 only `ScreenShot2` uses it**.
>
> For an unattended service it is **better than GNOME**: no session to create, no portal.
> It must however be treated as **a door that can close**: the D-Bus error is a normal case, not a
> bug, and the fallback is `fake_input` (which instead does require the `.desktop`).

⚠ **Distribution trap** [R]: `libeis-1.0` is **optional** at build time
(`kwin/CMakeLists.txt:319-320`, `431`). If the distribution builds KWin without it, the plugin **does not
exist** and the D-Bus object does not appear: it is not a runtime error, it is an absence. **[?]** the state of
Debian Trixie must be measured.

**The devices** (`eiscontext.cpp:155-174`, `eisbackend.cpp:116-171`): up to three per seat —
«eis pointer» (relative), **«eis absolute device»** (absolute **+ touch**), «eis keyboard». The seat
announces only the capabilities granted by the mask. Our context must be a **sender**: a
receiver gets torn down (`eiscontext.cpp:127-131`).

#### 7.2 What is reused from our `input.c`, and what changes

The comparison with the four things libei gives us on GNOME:

| | via **EIS** on KWin | via `fake_input` |
|---|---|---|
| **session keymap** | ✅ **yes**, XKB text v1 on a sealed memfd (`eisbackend.cpp:159-171`) | no |
| **state of the locking modifiers** | ⛔ **no**: `eis_device_keyboard_send_xkb_modifiers` **is not called anywhere in KWin** [✗] | no |
| **ping / synchronisation** | ✅ yes — but by an accidental property: there is no `case EIS_EVENT_SYNC`, and the pong goes out because the `unref` is outside the `switch` (`eiscontext.cpp:333`) | no |
| **screen regions** | ✅ yes, one per output — ⚠ **without `mapping_id`** (`eis_region_set_mapping_id` is not called) [✗] | no |

**The four things to touch, all contained:**

1. ⛔ **The wheel must be changed.** Our `/120 → ×10` uses `ei_device_scroll_delta`, which on KWin
   gives `deltaV120 = 0` (`eiscontext.cpp:246-258`) → a smooth `wl_pointer.axis` **without
   `axis_value120` or `axis_discrete`** (`pointer.cpp:281-358`): whoever counts the clicks sees
   none, and Xwayland has to guess buttons 4/5. **`ei_device_scroll_discrete(±120)`** must be used,
   which KWin converts into `delta = 15` + `deltaV120 = ±120` (`eiscontext.cpp:272-286`), that is the
   real wheel. **The RDP value is passed almost as it is: simpler than today.** Vertical negated
   (the `wl_pointer` convention is positive = down).

   > **✅ Measurement M10, closed on 8 August 2026 — by reading, and the reading is conclusive.**
   > `eiscontext.cpp:272-285`: KWin **inverts nothing** and treats the two axes **with the same
   > formula**, without special cases:
   > ```cpp
   > constexpr auto anglePer120Step = 15 / 120.0;
   > if (x != 0) Q_EMIT device->pointerAxisChanged(PointerAxis::Horizontal, x * anglePer120Step, x, …);
   > if (y != 0) Q_EMIT device->pointerAxisChanged(PointerAxis::Vertical,   y * anglePer120Step, y, …);
   > ```
   > The sign passes **unchanged** both in the angular delta and in the raw `v120`. So the direction that
   > reaches applications is libinput's, **identical for vertical and horizontal**, and
   > the adaptation from RDP is **entirely ours** — as already on GNOME. There is no KWin asymmetry
   > to compensate, which was the suspicion. ⚠ It remains to be checked **by eye** in the phase, because the
   > direction is one of those things judged by seeing them (`LEZIONI.md` §7.3).
2. ⛔ **The locking modifiers do not arrive.** The reconciliation of CapsLock/NumLock after a
   ping — the one we did well on GNOME — **is not done along this path**. The fallback is
   `org_kde_kwin_keystate` v5 (`kwin/src/wayland/keystate.cpp`), which gives `unlocked/latched/locked/pressed`
   **with spontaneous notification**, but it is **on the blacklist**: it requires also being a Wayland client and
   declaring it in the `.desktop`. **It is a choice to put before the user** (§13.4).
3. **Regions are looked up by geometry**, not by key: they are already in logical global coordinates,
   so `transform_position` simplifies — the search criterion changes, not the formula. And
   `libei` discards an absolute position **outside every region**.
4. **Devices get replaced.** At every change of output or layout KWin does
   `eis_device_remove` + `eis_device_add` (`eisdevice.cpp:42-53`, via `updateScreens`/`updateKeymap`):
   on our side the device **disappears and reappears**. The replacement must be handled, re-reading keymap
   and regions at every `DEVICE_ADDED`.

**What instead stays identical** [R]:

| | |
|---|---|
| keys | **evdev code without the −8**: KWin adds the offset itself, in one place only (`xkb.cpp:45`, `772`). Our RDP scancode → `WINPR_KEYCODE_TYPE_EVDEV` conversion holds as it is |
| buttons | evdev codes intact (`BTN_LEFT` 0x110 …) |
| absolute motion | **logical global** coordinates, reusable formula |
| touch | same coordinates, on the absolute device |
| `ei_device_frame()` | **mandatory**: without it, Wayland clients do not apply the motion (`eiscontext.cpp:190-200` → `wl_pointer.frame`) |
| repeated presses and unpaired releases | **KWin discards them silently** (`eiscontext.cpp:287-303`): we are not *forced* to keep count as on Mutter, but our tables remain useful — they serve us to know what to release |
| release at end of connection | ✅ **KWin acts as a safety net**: in the device destructor it releases every pressed key and button and cancels touches (`eisdevice.cpp:27-40`), and the context drops when the calling D-Bus service disappears |
| Xwayland | ✅ injected input **reaches it** through the normal `wl_seat` path (`xwayland.cpp:240-330`): no XTEST, no separate path |

⚠ **A KWin defect found along the way** [R]: four `continue` inside the `switch` of
`eiscontext.cpp` (lines 236, 241, 294, 300) skip the final `eis_event_unref` — every repeated
press and every unpaired release **leaks a reference**. It changes nothing for us
functionally, but it is a reason not to bombard KWin with redundant events.

#### 7.3 `fake_input`, the old path

**[R]** `org_kde_kwin_fake_input` (not `zkde_fake_input`), implemented in
`kwin/src/backends/fakeinput/fakeinputbackend.cpp`, **version 5** while the XML declares 6
(`keyboard_keysym` **is not implemented**). It is one-way: **zero events**. Its `authenticate`
ignores the arguments and authenticates nothing (`:107-113`, `// TODO: make secure`), but the real
permission is the globals filter.

And its serious limit: `axis` forces **`deltaV120 = 0` always** (`:179`) — **fake_input cannot
produce a discrete click**. It is the technical reason why krfb scrolls badly on Wayland.

---

### 8. Output, geometry and dynamic resolution

#### 8.1 ⛔ A virtual output cannot be resized

It is the costliest result of this study. Four barriers, all **[R]**:

1. **the mode is immutable**: `OutputMode::m_size` and `m_refreshRate` are `const`
   (`core/output.h:127-128`);
2. **the mode list is never rewritten** for a virtual output: `DrmVirtualOutput` fixes it
   in the constructor (`drm_virtual_output.cpp:37-40`), `VirtualOutput` in `init()`. The only
   runtime rewrites are in the nested backends and in real DRM connectors;
3. **`kde_output_management_v2` can only *choose* an existing mode**: the request takes a
   `wl_resource` of `kde_output_device_mode_v2`, that is an object already announced
   (`outputmanagement_v2.cpp:122-142`). There is no «misura arbitraria» request — and libkscreen
   is the same protocol with a coat on, so it is not an alternative path;
4. and even if there were a second mode, **on DRM it would be ignored**: `Output::applyChanges()` never
   touches `currentMode` (`core/output.cpp:517-543`).

**Do not exist** [✗]: `org.kde.KWin.VirtualOutputs` (it was in KWin 5), a `KWIN_*` variable that
creates outputs, a resize request in the screencast protocol. `VirtualBackend::setVirtualOutputs()`
exists but its **only callers are the autotests**.

> #### ✅ MEASURED — measurements M7 and M11
>
> **[M] 8 August 2026.**
>
> **M7a — `stream_virtual_output` with `--virtual` does not work**, as the code reading said:
> `KWin ha rifiutato: Could not find output`. Verified, and without surprises.
>
> **M11 — the absurd sizes**: `0x0`, `-1x-1`, `1x1`, `16384x16384`, `99999x99999` → **all
> refused with the same line** (`Could not find output`) and **KWin stays alive after all five**.
> ⚠ But the refusal comes because *the virtual output is missing*, not because KWin **validates** the sizes:
> so **validation remains unmeasured**, and it cannot be measured with `--virtual` — it would need
> `--drm`, which §5.2 excluded. Whoever one day runs on KWin ≥ 6.8 should redo it.
>
> **M7b — how much it costs to set up a stream**: from connecting to the socket to the PipeWire node
> announced, **65, 65 and 67 ms** over three consecutive rounds. It is the fixed component of the «buco» of the
> «chiudi e rifai» fallback (§8.3); to it must be added the time to recreate the output, which on
> `--virtual` cannot be measured because the output is not created at all.

#### 8.2 The paradox: everything else is already there, and it is identical to Mutter

**[R]** `ScreenCastStream::resize()` (`screencaststream.cpp:672-682`) does
**`pw_stream_update_params`** on the same node, and it is called **at the end of every frame**
comparing `m_source->textureSize()` (`:669`). The consumer sees only a
`param_changed(SPA_PARAM_Format)`, then the new buffers. **If the output could change mode, the
stream would follow it by itself** — it is precisely the mechanism phase 6 gave us on GNOME. And
it already works today for **real outputs**: if the user changes resolution on a monitor while we
capture it, the stream adapts.

A tiny piece is missing: a `DrmVirtualOutput::resize()` modelled on `WaylandOutput::resize()`
(`wayland_output.cpp:293-303`) plus a request in the protocol. **A dozen lines upstream.**

> ### ✅ AND THOSE LINES HAVE ALREADY BEEN WRITTEN — nine days before this study
>
> *[I] `kwin!7932` «screencast: Resizable Virtual Monitors», **merged on 29 July 2026** (commit
> `452707eb`, milestone **6.8**), with `kpipewire!205` and `krdp!113`.*
>
> **And the way they did it is the one we need.** Not a new request in the protocol —
> that one was **proposed and rejected** (`plasma-wayland-protocols!138` + `kwin!9519`, 1–2 July
> 2026, closed within a day) with this reasoning from David Edmundson: *«We have this over pipewire
> […] Which is better because: things work the same in gnome; sandboxed clients using the portal can
> resize it»*. The chosen mechanism is **PipeWire negotiation**: the consumer proposes a
> `SPA_POD_CHOICE_RANGE_Rectangle` and **KWin follows the stream size**, with limits 200×200 …
> 10000×10000.
>
> **That is: it is exactly the code of our phase 6**, and the consumer side is three lines.
>
> ⚠ **But it is 6.8, that is October 2026**: on Trixie (6.3.6) it is not there, and not even on sid. Hence the
> operational consequence, which is worth more than the fact: **resizing on KDE is not a lost
> feature, it is one that is coming** — and our code must be written **in the form of the negotiation**, which
> is the one that becomes right by itself when the user upgrades. Strategy (A) remains the fallback for
> the versions that do not have it, not the main path.
>
> To keep an eye on, because it is the table at which to ask for what we lack:
> `plasma-wayland-protocols!130`, **a version 2 of the capture protocol**, in draft since March 2026.

#### 8.2-bis ⛔ The mandatory guard: without it, the renegotiation chases its own tail

*From report 16 §1.5, and it is not our deduction: it is a defect **found by others** during the
review of `kwin!7932`, that is the very work that will bring resizing in 6.8.*

**[I]** Nick Haghiri, 3 July 2026, on the KWin merge request:

> *«Resizing re-emits `outputsQueried()`, which triggers a full output reconfiguration, which can
> cause the stream to renegotiate again and call back into `resize()`. … this results in repeatedly
> tearing down and recreating the capture pipeline. Symptoms: the `ScreencastLayer` gets
> destroyed/recreated many times per session, PipeWire toggles `streaming ↔ paused` repeatedly, and
> video freezes intermittently.»*

The cure, in the merged code ([C] `outputscreencastsource.cpp:170-181`), is **one line**:

```cpp
void OutputScreenCastSource::resize(const QSize &size)
{
    if (m_output->pixelSize() == size) {   // ← without this, infinite loop
        return;
    }
    m_output->resize(size);
}
```

> #### ✅ AND THE INPUT HAS BEEN WRITTEN AND TESTED — 8 August 2026, item 2
>
> *The four differences of §7.2 are all in the code, and all four have a bench line.*
>
> | | Outcome |
> |---|---|
> | `connectToEIS(7)` from REMOTIX | ✅ **granted**, token 1, no permission asked. ⚠ The descriptor travels in a **separate list**: the `h` type carries only an index, and whoever reads the message body gets a **zero** — that is standard input, a perfectly valid fd pointing to the wrong thing |
> | the keymap | ✅ read from libei: `English (US)`, as on GNOME |
> | the wheel | ✅ **discrete clicks in both directions**, measured. The RDP value is passed almost as it is |
> | the regions | ✅ found by **geometry**: `0,0 1920x1080`, with `mapping-id «assente»` — that is, the by-key criterion could not have worked, and it is exactly what this document predicted |
> | `org_kde_kwin_keystate` | ✅ **speaks**, and `fetchStates` gives the initial state. The same `.desktop` as the capture authorises it: it is one more name, as predicted |
>
> ⛔ **And the confirmation worth the most is negative**: `EI_EVENT_KEYBOARD_MODIFIERS` never arrived,
> in any test. The lock reconciliation written for GNOME, on KDE, **would not run** — and
> without `keystate` it would have stayed there, written and dead, without any bench noticing.

⛔ **And the mirror applies to us, who are the consumer.** kpipewire applies the same guard
([C] `pipewiresourcestream.cpp:467-475`): if the requested size is **equal** to the one already requested,
**nothing is signalled**. Without that condition, every format change of the stream calls back
our size request, which calls back a format change: video that freezes intermittently and a
stream that flickers between `streaming` and `paused`.

> ⚠ **Why it matters now**: the user decided (8 August) that resizing is written **in the
> form of the negotiation**, so as to switch on by itself on KWin 6.8. That form **includes this
> guard**: it is the first line of the function, not an optimisation. Whoever forgets it does not see the
> defect on Trixie (where resize does not work) and discovers it **on the day of the upgrade to 6.8**.

#### 8.3 The remaining strategies, and their price

| | What it is | Price |
|---|---|---|
| **(A)** close the stream and redo it with the new size | the only complete path today | ✅ **on KDE it does not drag input along**: EIS and `fake_input` are independent of the screencast, so **the state of pressed keys is not lost** — the price that §5.8 of `SPECIFICA.md` reluctantly accepted on GNOME is not paid here. What remains: a video gap of a few frames, a **new PipeWire node**, and the repositioning of windows |
| **(B)** large virtual output + recreated `stream_region` | cheap: it does not touch the outputs | gives a **crop**, not a resized desktop: maximised windows stay large. And the region is `const`: it must be recreated. It serves *letterboxing*, not MS-RDPEDISP |
| **(C)** `kde_output_management_v2` on one of the 15 common sizes | only for physical monitors | out of the question on a live session |
| **(D)** upstream patch | the missing piece | the right path if phase 11 becomes a long commitment |

⛔ **And there is a price none of the four avoids**: **resizing an output rearranges the user's
windows**, in two ways [R] — `desktopResized()` → `rearrange()` →
`Window::checkWorkspacePosition()` (maximised, fullscreen, edge-keeping, off-screen correction,
`window.cpp:4052-4253`), and the `PlacementTracker`, whose key **contains the output
geometry** (`workspace.cpp:296-297`): every size is a key, and **returning to an already-seen size
the windows are teleported back**. Moreover `updateOutputs()` **cancels a
drag in progress**. KWin itself, when it undergoes resizes, coalesces them into one frame
with the comment *«Output resizing is a resource intensive task»* (`wayland_output.cpp:342-349`).

> It is the same price that on GNOME made us discard automatic resolution adaptation (§3.1 of
> `SPECIFICA.md`, phase 7 box in `PIANO.md`). On KDE therefore **MS-RDPEDISP is a choice to
> re-weigh**, not work to redo: the size requested can be served **at connection time** and
> changes coalesced with the R10-bis settling, which we already have.

#### 8.4 The output protocols, and the constraints on geometry

**[R]** None of the output protocols is behind a permission:

| Protocol | Version | What it gives |
|---|---|---|
| `kde_output_device_v2` | **11** | read everything: geometry, physical size, modes, scale, EDID, `enabled`, uuid, VRR, HDR |
| `kde_output_management_v2` | **12** | write: `enable`, `mode` (existing only), `transform`, `position`, `scale`, `overscan`, … |
| `wl_output` | **4** | has `name`/`description`: **this is how `"Virtual-remotix"` is found again** |
| `zxdg_output_manager_v1` | 3 | logical position and size |
| `wlr-output-management` | **absent** [✗] | — |

Constraints and traps [R]:

- ⛔ **on DRM `width`/`height` are pixels**, not logical units — the XML says «logical» and krfb falls
  for it. **Pass `scale = 1`**;
- ⛔ **the requested scale is thrown away**: `generateConfig` replaces it with `chooseScale()`
  (`outputconfigurationstore.cpp:507`, `607-656`), which on a `physicalSize` equal to the pixels always gives
  1.0;
- **even** width and height are not required by KWin, but the 4:2:0 encoder requires them:
  our constraint;
- ✅ **the metre declared by the Android client cannot reach KWin**: `stream_virtual_output` has no
  physical-size argument, and `DrmVirtualOutput` imposes `physicalSize = size`. Even if it
  arrived, `chooseScale()` is defended (`< 3 mm` → scale 1, with the comment *«these are all caused by
  the screen mis-reporting its size»*) and the scale is limited to `[1.0, 3.0]`. The DPI filter of
  `misura.c` remains necessary all the same **for our side** (the EGFX surface and the encoder).

---

### 9. The clipboard: easier than on GNOME

**[R]** The way is **`zwlr_data_control_manager_v1` version 2** (`wayland_server.cpp:386`), and
**it is not blacklisted**: no permission, no `.desktop`. `ext_data_control_v1` does not exist in
6.3.6 [✗], and the KDE RemoteDesktop portal declares `clipboard_enabled: false`
(`remotedesktop.cpp:264`) — the GNOME way (the clipboard inside the control session) **has no
equivalent**, and is not needed.

**Reading**: `get_data_device(seat)` → the server sends **immediately** `data_offer` + the `offer(mime)` +
`selection`; then `receive(mime, fd)` and you read until EOF, while the owner writes.
⚠ An `offer(mime)` can arrive **after** `selection`: the list of types is not complete at the instant
of the event.

**Writing**: `create_data_source()` → `offer(mime)` → `set_selection(source)`. ⚠ **A source is used
only once** (`error_used_source`), and when someone reads we receive `send(mime, fd)` with KWin
**immediately closing its own copy of the fd**: writing and closing are up to us, and **without
blocking** the loop (a 64 KB pipe with a slow consumer blocks us).

**Mutter's three asymmetries, put to KWin** [R]:

| The question | Mutter | **KWin** |
|---|---|---|
| Does whoever reconnects receive an announcement? | **no**, and it cost us | ✅ **yes**: `registerDataControlDevice()` immediately sends selection and primary selection (`seat.cpp:228-229`) — ⚠ if there is no selection it sends an **empty** announcement, not the absence of an announcement |
| Does the announcement come back after one of our writes (echo)? | yes | ⛔ **yes**: `setSelection()` loops over **all** data control devices, **including the originator** (`seat.cpp:1257-1259`), and the «stessa selezione» filter does not help because every source is new |
| Is there an irreversible switch (`DisableClipboard`)? | **yes**, and it killed our clipboard | ✅ **no** [✗]: the clipboard does not belong to a session |

⛔ **Two echo traps**, to be avoided by construction: reading the echo means being asked for the
data **by our own source** (deadlock, if the read is synchronous); forwarding it to the RDP client means
entering the loop. The robust criterion: **ignore the first `selection` that arrives after one of our
`set_selection`**, also comparing the list of types. **[?]** The protocol has neither a serial nor
an attribution.

**The two roommates** [R]:

- **klipper** *puts back* the last item when the clipboard becomes empty, marking it
  `application/x-kde-onlyReplaceEmpty` (`klipper/systemclipboard.cpp:403-411`): if we destroy our
  source without replacing it, **the previous content comes back**. And it defends itself from loops with
  **10 changes per second** (`:50`): do not exceed them. ⚠ And KWin has a dedicated workaround
  (`seat.cpp:200-226`) that **silently cancels** a `set_selection` that declares that mime type:
  **never use it**;
- **the Xwayland side**: X11 → Wayland is unconditional; **Wayland → X11 only when an Xwayland
  window is active** (`xwayland/clipboard.cpp:88-100`, with the comment *«shield against snooping X
  windows»*), and it catches up at the first `windowActivated`. ⛔ **A test with `xclip` fails without
  an error**: it is the green-bench-on-a-live-defect form that `LEZIONI.md` §2.2 lists.

#### 9.1 ✅ WRITTEN AND TESTED — 8 August 2026, `prove/fase11-appunti.sh`

```
OK  the session copied something: 6 types
OK  the client has «SESSIONE-VERSO-CLIENT-àèìòù-ok»
OK  the session pastes «CLIENT-VERSO-SESSIONE-àèìòù-ok»
OK  no loop (2 real announcements, 1 echo discarded)
OK  the echo arrived and was recognised
faults: 0
```

It lives in **`fondamenta/remotix-c/src/appunti_wlr.c`**, and the name says `wlr` not `kwin` on purpose: the protocol is
wlroots', so the file already serves the XFCE and LXQt compositors too (§3.8 of `SPECIFICA.md`). The
port `appunti.h` stayed a single one, with `appunti.c` reduced to dispatching and the Mutter path moved
into `appunti_mutter.c` — the same shape as `compositore.c`.

> #### ⛔ The guard against the echo: the criterion of §9 was weaker than necessary
>
> «Ignorare il **primo** `selection` dopo un nostro `set_selection`» is a timing rule, and
> timing rules go wrong when two things happen together. The criterion written is instead a **state**
> one: an announcement is ignored if **the source is still ours** *and* the types match.
>
> It holds because KWin guarantees the order: when someone else copies, it is the same `setSelection` that
> sends first `cancelled` to the old source and then the announcement to the devices. At that point «la
> sorgente è nostra» is already false and the announcement goes through. No counter, no time window.

> #### ⛔ `POLLHUP` counts as «ready», and treating it as a fault costs a wrong diagnosis
>
> *[M, 8 August 2026 — the first round of the bench]*
>
> Whoever owns the clipboard writes and closes. With short data the `poll` can return with **`POLLHUP` and
> nothing else**: the bytes are in the pipe, but nobody has read them yet. The code looked only at `POLLIN` and
> concluded «non ha risposto» — **immediately**, writing to the log a five-second timeout
> *that had never elapsed*. The log said `entro 5000 ms` three seconds after the announcement, and that
> impossible number was the only clue.
>
> On reading, `POLLHUP` is an outcome (the following `read` will say zero); on writing it is not, there it means that
> whoever was pasting has gone away.

⚠ **And the announcement is not delivered when `selection` arrives**: an `offer(mime)` can arrive later, and
a truncated list makes the wrong thing get pasted without anyone noticing. The pump does a full
round trip — `wl_display_roundtrip` — and *then* delivers.

---

### 10. The system around it: power, lock, credentials, audio

#### 10.1 ✅ The cure of §3.4-bis works, and Plasma **hides**

**[R]** `sessionmanagementbackend.cpp:108-121` turns on the menu item only if logind answers
`"yes"` or `"challenge"`; the default values are `false`, and the consumers use `visible:` /
`addIfValid`. So `sleep.conf` + the polkit rule of §3.4-bis of `SPECIFICA.md` **apply
identically on KDE**, and as a bonus `canSuspend=false` brings powerdevil's auto-suspend to
`NoAction` by itself.

⛔ **But the polkit rule must be written `no`, not *auth_admin***: `"challenge"` **shows** the item.

#### 10.2 ⛔ On KDE there is a second commander of inactivity, and the lock turns itself on

Two configuration defects that a remote session meets after a few minutes, both **[R]**:

| | |
|---|---|
| powerdevil has **«spegni lo schermo dopo 10 minuti» on by default**, independent of the logind cure | `powerdevilsettingsdefaults.cpp:61-80` |
| `kscreenlockerrc [Daemon] Autolock` is **`true`** with `Timeout=5` minutes | `kscreenlockersettings.kcfg:8-18` |

**The precise way to inhibit**: `org.kde.Solid.PowerManagement.PolicyAgent.AddInhibition(types=4, …)`
— where `4` is `ChangeScreenSettings` and **implies** `InterruptSession`
(`powerdevilpolicyagent.cpp:737-745`); no permission check, effect after **5 s**, it
releases itself when the D-Bus name drops. ⚠ The freedesktop way
(`org.freedesktop.PowerManagement.Inhibit`) maps **only** to `InterruptSession`
(`powerdevilfdoconnector.cpp:84-93`): **it does not stop the screen.**

⛔ **And with the lock active our inhibition is ignored** (`powerdevilpolicyagent.cpp:509`):
turning off the locker is not a convenience, it is **a dependency**. The lever is
`kwin_wayland --no-lockscreen` (`main_wayland.cpp:550-556`) — which the stock systemd units **do not
pass**, because on Wayland the lock belongs to KWin (`ksmserver/main.cpp:171-175`).

Two notes that scale the problem down, both **[R]**: capture **does not stop** at the lock (but
the scene renders the lockscreen, so you would see **the lock image**), and **injected input
reaches the greeter** — i.e. the remote user can unlock by typing. The lock is a nuisance,
not an exclusion. And injected input **resets the inactivity timers** (EIS →
`simulateUserActivity`), so a session in use does not lock.

#### 10.3 ⛔ With no output at all, KWin locks itself up

**[R]** `workspace.cpp:1216-1223`: with zero enabled outputs the Workspace mounts a
`PlaceholderOutput` with the render loop inhibited **and a filter that swallows all input**. **The virtual
screen is a precondition, not a result**: between the death of one stream and the creation of the
next (strategy (A) of §8.3) you pass through there.

#### 10.4 The other items, in brief

| | **[R]** |
|---|---|
| **kwallet** | nobody starts it in this tree; the risk of a credentials dialog in an unattended session remains to be measured **[?]** |
| **The audio sink** | **zero lines of Plasma touch the audio devices**, and Phonon's preference list has been emptied (`kdeplatformplugin.cpp:128-149`). The choice of §7.5 of `REFERENCE.md` — we create the virtual sink ourselves and capture its monitor — **is reused identically**. Final confirmation: a measurement, not a job |
| **Notifications that appear by themselves** | ⛔ the kded module `devicenotifications` (autoload `true`) makes *«Display Detected/Removed»* appear **at every virtual screen we create or destroy** (`devicenotifications.cpp:290-351`) — i.e., with strategy (A), **at every resolution change** |
| **D-Bus permissions** | **no check** on any system interface of KWin/Plasma/powerdevil, except `ScreenShot2` and `PlasmaShell.evaluateScript` |
| ~~**Risk to close first**~~ **measurement M12, corrected on 8 August** | the modal `QMessageBox` *«Plasma Failed To Start»* is there (`shell/main.cpp:176-179`), **but it is not the first risk, and it does not fire at the first failure.** Rereading `shell/main.cpp:160-181`: at the first OpenGL context error plasmashell **writes `SceneGraphBackend=software` into `kdeglobals` — `Global | Persistent` — and restarts itself** (`QProcess::startDetached`); the dialog appears **only on the second round**, if the software fallback fails too. ⛔ **So the real risk is something else: a session started without a GPU leaves a permanent configuration** that makes rendering software even when the GPU comes back. [M] In the measured session, **with** the GPU: zero `Open GL context could not be created` lines and **no `SceneGraphBackend` written**, as it should be. ⚠ The reproduction of the «senza GPU» case was not done: denying the GPU to the compositor alone is not enough (plasmashell is another unit), it would need to be denied to the whole session |
| **The session rules** (the nine combinations of §3.4) | do not depend on the desktop: logind is the same. **Nothing to redo**, except verifying that the session *type* behaves as on GNOME **[?]** |

#### 10.5 ⛔ The volume slider governed nothing — and it was not KDE's fault

*[M, 8 August 2026, opened by the user: «se abbasso il volume l'audio resta sempre alto; in pratica
audio del server e del client sono scollegati»]*

We create the virtual sink ourselves (§7.5 of `REFERENCE.md`) and capture its monitor. **In PipeWire
a node's volume is applied downstream of the monitor tap**, and the property that moves the
tap — `monitor.channel-volumes` — is **`false`** unless you ask for it. Whoever creates the sink with
`pactl load-module module-null-sink` never notices, because `pipewire-pulse` sets it by itself
for compatibility with PulseAudio, where the monitor has always been downstream of the volume. We create the sink
by hand, with `pw_core_create_object`, and we forgot it.

The measurement, a 440 Hz tone of known amplitude (25.9 % of full scale), read on the monitor:

| sink volume | `monitor.channel-volumes` **not requested** (as it was) | requested (`pactl` sink) |
|---|---|---|
| 100 % | 25.39 % | 25.39 % |
| 25 % | **25.39 %** | 0.40 % |
| 10 % | — | 0.03 % |
| 0 % | **25.39 %** | 0.00 % |

The numbers in the right column are not «quasi giusti»: they are **exactly** PulseAudio's cubic
curve (0.25³ = 1.56 %, and 25.9 × 0.0156 = 0.40). The left column is flat: the volume does not
get through, **mute included**. In the live session the node was at `channelVolumes 0.0` and `mute true`
while the client received the full signal.

✅ **Cure**: `"monitor.channel-volumes", "true"` among the sink's properties, in `suono.c`.

> ⚠ **The direction matters, and it is the reason this slider is the only one that can work.** RDP has
> a single volume PDU, `SNDC_SETVOLUME`, and it goes **from the server to the client** — we send it at full
> scale when the format is chosen (`altoparlante.c`). **The opposite direction does not exist**: a client has
> no way to tell the server «abbassa». So the only slider that really governs the level is
> the one visible **inside** the session, and it has to be made to work.

#### 10.6 The menu items that cannot work, removed from the menu

*[asked by the user, 8 August 2026: «sarebbe meglio nascondere le voci di *switch user* e *lock*
(anche se non funzionano, ed è il comportamento corretto)»]*

In a session served by REMOTIX **«Blocca schermo» and «Cambia utente» cannot work**, and
rightly so: we turn off the locker ourselves with `--no-lockscreen`, because with the lock active powerdevil
ignores inhibitions (§10.2), and switching user would mean a display manager that is not here. But
**an item that does nothing is worse than an item that is missing**: whoever presses it concludes that the server is
broken.

The lever is **KIOSK**, i.e. `KAuthorized`. The action names are not to be guessed, they are the ones
Plasma actually queries:

| what it governs | action | where |
|---|---|---|
| `SessionManagement::canLock()` | `lock_screen` | `libkworkspace/sessionmanagement.cpp:126-129` |
| `SessionManagement::canSwitchUser()` | `start_new_session` | `libkworkspace/sessionmanagement.cpp:121-124` |
| `SessionsModel::canSwitchUser()` | `switch_user` | `components/sessionsprivate/sessionsmodel.cpp:45` |

⚠ **`switch_user` and `start_new_session` are both needed**: the first governs the list of
sessions, the second the button. Removing only one leaves half an interface.

The file is written in `$XDG_RUNTIME_DIR/remotix/xdg/kdeglobals` and the folder is put **at the head of
`XDG_CONFIG_DIRS`**, where KConfig reads it as *system* configuration:

```ini
[KDE Action Restrictions][$i]
action/lock_screen=false
action/start_new_session=false
action/switch_user=false
```

> ⚠ `[$i]` is not decorative: without it, the user's `kdeglobals` — which sits higher — puts the
> items back in place.
>
> ⚠ `/etc/xdg` **is kept at the tail, not replaced**: from there comes `menus/plasma-applications.menu`,
> i.e. precisely the file that `XDG_MENU_PREFIX` goes looking for. Replacing it would switch off capture via the
> path of §3.3-bis.
>
> ⛔ And **`logout` is not touched**: it is the way the session is closed, and the one the exit
> sentinel rests on.

It is not written in `~/.config`: what we impose applies to the served session, and must not change
the configuration the user chose nor outlive the machine. Consequence: **it takes effect
from the next session start**, not on a session already alive.

---

### 11. `kpipewire`: the code that does our very job

It is the most directly transferable piece of all of KDE: it consumes PipeWire and **encodes in H.264**.

#### 11.1 Damage and synchronisation: **it does not do them**, and the why is the answer

**[R]** `SPA_META_VideoDamage` is requested **only** if someone calls `setDamageEnabled(true)`, and
**nobody calls it** in the whole tree (`pipewiresourcestream.cpp:68`, `369-379`; zero callers in
`src/` and `tests/`). When it arrives, the only consumer is a **debug overlay** that draws the
rectangles in red (`pipewiresourceitem.cpp:295-310`). Of synchronisation **there is nothing**: zero
`SPA_META_SyncTimeline`, zero `poll()` on a buffer fd, zero ioctl, zero `eglCreateSyncKHR`, zero
`glFinish` [✗].

**And it is not an oversight**: it is the consumer side of what §4.6 and §4.8 say about the producer — KWin
redraws the whole frame and synchronises by itself. Damage, on KDE, **is a hint**.

> ✅ **Conclusion that holds for the whole project**: the alternating-screens defect (R29) **is
> Mutter's, not the PipeWire model's**. And the cure we wrote — the accumulation surface — is not
> needed on KWin.

#### 11.2 The three things to copy

1. ⛔ **For GPU encoding only `DRM_FORMAT_MOD_LINEAR` is requested** (`vaapiutils.cpp:119-135`):
   RadeonSI **refuses** buffers with DCC, iHD **accepts them and then forces LINEAR internally** — i.e.
   it accepts and goes wrong silently, our favourite form of fault (R27, R30). Days saved.
2. **The VAAPI context is not created: you let the filter graph create it.**
   `hwmap=mode=direct:derive_device=vaapi,scale_vaapi=format=nv12:mode=fast`, `hw_device_ctx`
   assigned to **every** filter *before* `avfilter_graph_config()`, and then taken from the
   buffersink with `av_buffersink_get_hw_frames_ctx()` (`h264vaapiencoder.cpp:89-97`, `151`). It
   pre-emptively cures the third case of R30 — the `h264_vaapi` that opened with a context of its own.
3. **When a modifier fails DMA-BUF is not turned off**: *that* modifier is removed and
   renegotiated, re-entering the right thread with `pw_loop_add_event`/`pw_loop_signal_event`
   (`pipewiresourcestream.cpp:261-273`). It is also the mechanism to change path on the fly without
   redoing the capture — i.e. our R30, written by others.

A gift measured by others, two hours to try it: `flags +mv4` and `-flags +loop` on **all**
encoders, with the comment *«disable motion estimation … speeds up encoding by an order of
magnitude»*.

#### 11.3 What kpipewire does **not** do

| | |
|---|---|
| **bitrate control** | ⛔ **absent** for H.264: never `bit_rate`, never `rc_mode`. It is **the same gap as `gnome-remote-desktop`** (§9.1) and as R31: on that point REMOTIX stays alone, and now the loneliness is confirmed by two references instead of one |
| live resizing | absent |
| cursor on DMA-BUF | not composited |
| `max_b_frames` | **0 in every encoder** — independent confirmation of R11 |

**Four defects not to copy** [R]: `stride*height*4`, a `ceil` on an integer division, the
cadence in integer arithmetic with division by zero, `mapoffset` ignored.

**Reusable from a C program**, rewriting only the Qt types: `queryDmaBufModifiers`,
`buildFormat`, the construction of the `AVDRMFrameDescriptor`, and all of `vaapiutils.cpp`. **To
rewrite**: the software path (three copies per frame), the bitrate, the damage, the cursor.

---

### 12. KDE's references, and what they are worth

#### 12.0 ⭐ `KRdp` — the real reference, and the study had missed it

> ⛔ **Correction of 7 August 2026, evening.** The first draft of this document said
> *«altre tracce di RDP in KDE: nessuna»*. **It was false**, and because of a method error worth
> recording: the search had been done **inside the cloned repositories**, and `krdp` was not among them.
> Searching in your own house is not searching. It was found by a question from the user — *«su KDE qualcuno ha
> affrontato i problemi prima di noi: xrdp. Come fa con KWin?»* — and the answer is that xrdp has
> nothing to do with it (§12.3), but **someone else does**.

**What it is.** `KRdp` is KDE's RDP server: **C++ on FreeRDP**, with `kpipewire` for the pixels, and it is
what Plasma 6.2+ presents as *«Condivisione del desktop (RDP)»* in System Settings.
**4 222 lines** in Trixie's 6.3.6, 5 877 in master. That is: same RDP library, same
compositor, same clients, and an order of magnitude less than `gnome-remote-desktop` — which makes it
readable in full in one session.

**The confirmation that weighs most of all** — its `.desktop` file, `server/org.kde.krdpserver.desktop.cmake`:

```ini
[Desktop Entry]
Type=Application
Exec=@CMAKE_INSTALL_PREFIX@/bin/krdpserver
NoDisplay=true
X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input,zkde_screencast_unstable_v1
```

**The permission way of §3 is not a deduction of ours: it is what KDE's RDP server does**, for
capture *and* for input, in three lines and without a dialog.

**How it is made** — all **[R]**, on master except where indicated:

| | |
|---|---|
| **Where it runs** | `server/app-org.kde.krdpserver.service.in`: `Type=exec`, `After=plasma-core.target`, **`WantedBy=plasma-workspace.target`** — i.e. **inside** a Plasma session already up, as a user service. ⛔ **It does not start the session**: that is the structural difference from REMOTIX, and the reason why KRdp does not solve our §6 |
| **Capture** | two paths, and ⛔ **the default one is the portal**, not Plasma's protocols: the direct one is chosen with **`--plasma`** (`server/main.cpp:128`), and **the systemd unit does not pass it**. The direct one is `PlasmaScreencastV1Session.cpp:173-199` (`createVirtualMonitorStream`, `createOutputStream`, `createWorkspaceStream`, all with `Metadata` cursor) |
| **The size** | `server/main.cpp:49-52`: **`--virtual-monitor 1920x1080@1`**, a command-line option. The size is decided by **whoever starts the service**, not the client. ⛔ **And without `--plasma` it cannot work**: KRdp asks the portal for the «virtual» source type (4), which `xdg-desktop-portal-kde` **does not announce**, and whose dialog builds no list at all (`screenchooserdialog.cpp:148-231`) — empty page. That is: **the virtual screen exists only on the direct path** |
| **Input** | ⛔ **`fake_input`, not EIS**: `PlasmaScreencastV1Session.cpp:26-35, 164-165` binds `org_kde_kwin_fake_input` **v4** and calls `authenticate("krdpserver", "")`. It does not use KWin's EIS backend |
| **The keymap** | ✅ **it reads it from the `wl_seat`**, being a Wayland client: `wl_keyboard.keymap` → `xkb_keymap_new_from_string` (`:121-143`). Then `keycodeFromKeysym()` looks for the key that produces the symbol and **applies the levels** — level 1 → `KEY_LEFTSHIFT`, level 2 → `KEY_RIGHTALT` (`:68-89`, `:265-278`), with `EVDEV_OFFSET = 8`. It is **our Unicode path**, written by them without libei |
| **The two codecs** | ✅ **our very structure** (R3): `VideoStream.cpp:635-656` — H.264 if the client declares AVC **and** YUV420, otherwise **RemoteFX Progressive** (`progressive_context_new(TRUE)`). `KRDP_DISABLE_H264` forces the fallback. ⚠ The profile is **`H264Baseline`** (`:273`), not *Constrained High* like R11 |
| **Encoding** | delegated to `kpipewire`: `PipeWireEncodedStream` with `EncodingPreference::Speed`, `ColorRange::Full`, `quality` 0–100 (`--quality`), `maxFramerate`, `maxPendingFrames`. No declared bitrate — consistent with §11.3 |
| **The regulator** | ✅ **the same as our phase 7**: `NetworkDetection::rttChanged` → `updateInFlightWindow()`, `hasInFlightCapacity()`, a frame queue and a sending thread (`VideoStream.cpp:376-398`). The last commit on master is *«smooth the RTT used for the in-flight window»* |
| **Damage** | ✅ **it uses it**, unlike krfb: `setDamageEnabled(true)` on the Progressive path (`:299`), damage accumulation across queued frames (`:456-466`) and conversion to FreeRDP's `REGION16` (`:201-238`) — with **exclusive** edges, `right = rect.right() + 1`: our R5, confirmed by a third party |
| **Resizing** | ⚠ `DisplayControl.cpp` **exists only in master**: `MaxNumMonitors = 1`, factor 8192 (identical to ours), accepts **only** `NumMonitors == 1`, and the incoming layout goes to **`VideoStream::setRequestedSize`** (`server/SessionController.cpp:58`) → i.e. **to the encoder**, not to the output. ⛔ **Not even KRdp resizes the virtual screen**, and in Trixie's 6.3.6 **it has no resizing at all** (`kpipewire` 6.3.6 does not even have `setRequestedSize` [✗]) |
| **Security** | `RdpConnection.cpp:426-428`: `NlaSecurity = !usePam`, **`TlsSecurity = usePam`** — i.e. **NLA by default, and pure TLS when authenticating with PAM**, which is our choice (§3.6). And PAM really is there (`pam_appl.h`, `:88-134`) |
| **Capabilities** | `ColorDepth = 32`, `SupportGraphicsPipeline`, `NetworkAutoDetect = true`, and explicit refusals if the graphics pipeline or pointer cache are missing (`:573-584`): our §3.2 and §3.3 |
| **A trap we did not have** | `VideoStream.cpp:575-588`: *«Windows clients (mstsc) send CapsAdvertise **twice**»* — and KRdp treats the second as a **channel reset**, destroying the surfaces and recreating them. Our R2 says a second `CapsAdvertise` is legitimate only from 10.3; this says **what to do with it** |

**What it does not solve for us**, and it must be said: **it does not start the session** (it lives inside Plasma, so
our §6 remains entirely ours), **it does not resize** (§8 remains open), and it uses the **old** input
path — where we have already written the new one. I have not yet read in detail
`Clipboard.cpp`, `Cursor.cpp`, `NetworkDetection.cpp` and `PortalSession.cpp`: they are **the next
reading**, and they are all pieces we need.

#### 12.0-bis ⛔ KRdp's defects not to repeat — the list that is worth more than the code

*Poured in from reports 12 §6.4, 14 §2.2 and 15 §8.1-8.2 on 8 August 2026 (step 0 of the work plan).
KRdp's development branch fixed eighteen of them compared with Trixie's 6.3.6: **every fixed
line is a defect we must not write**. Here are the fourteen that concern us,
in order of how hard they would bite us.*

| ⛔ | The defect | Where, in 6.3.6 | What it teaches us |
|---|---|---|---|
| **1** | **The client without AVC420+YUV420 was *disconnected***: `qCWarning("Client does not support H.264…"); return CHANNEL_RC_INITIALIZATION_ERROR` | `VideoStream.cpp:308-313` | ⭐ **confirms our R3 as a necessity, not a luxury**: without RemoteFX Progressive our Android client would not connect at all |
| **2** | **`RDPGFX_SURFACE_COMMAND` half filled**: 10 fields out of 13, the others **stack garbage** — `contextId` included, which for AVC420 must be 0 | `:377-392` vs `freerdp/channels/rdpgfx.h:195-210` | **zero the structure** (`= {}`) before filling it. It is of the same family as our defect on the `MONITOR_DEF` (R5) |
| **3** | **No return code checked**: `ResetGraphics`, `CreateSurface`, `MapSurfaceToOutput`, `StartFrame`, `SurfaceCommand`, `EndFrame` — all called and ignored | `:367`, `:376`, `:385`, `:411-414` | ⭐ *«un errore su `CreateSurface` diventa uno schermo nero senza una riga di log»* — **it is the way we lost time ourselves** |
| **4** | **No `DeleteSurface`, ever**, and `ResetGraphics` called with live surfaces | `:349-385` | the surfaces **pile up in the client**. It is precisely what our **R6** forbids |
| **5** | **`pendingFrames` (a `QSet`) used by two threads without a lock** | `:118`, `:333`, `:344`, `:397` | hash table corruption and `erase` of an invalid iterator: a crash that comes at random |
| **6** | **No backpressure**: everything in the queue was sent | `:174-188` | on a slow network the TCP buffer swells: **seconds** of latency that never recover |
| **7** | **`queueDepth`/`SUSPEND_FRAME_ACKNOWLEDGEMENT` ignored** with the in-flight window active | `:677-692` (**also in master**) | **eternal block**: if the client says «non aspettare i miei riscontri» and we wait, nothing leaves any more. When it is suspended, **the window is disabled** |
| **8** | **No recovery from lost acknowledgements** | same | `totalFramesDecoded` **as a floor**, and a timeout for pending frames |
| **9** | **`close()` closed the channel *before* stopping the sending thread**; the destructor was **empty** | `:194-207`, `:143-145` | the right order is: **stop the streams → wait for the threads → drain the queues → destroy the surfaces → close the channel** |
| **10** | **The cadence estimator with an always-false condition**: `(estimate.timeStamp - now) > periodo` with `timeStamp <= now`, i.e. a **negative** difference | `:427-433` | unbounded memory leak **and** an average computed over the whole session, which therefore no longer adapts to anything. ⭐ A defect that **no functional test finds**: the program works, it just no longer regulates |
| **11** | **Bandwidth measurement opened and closed around *every* frame** | `:353`, `:416` | bandwidth measurement is a request/response round trip: doing it 60 times a second **turns it into noise** |
| **12** | **`uint32` sequence number in a 16-bit field**: the RTT dies after **~76 minutes** and the request hash grows without limit | `NetworkDetection.cpp:69`, `:75`, `:244-252` | a **`uint16_t`** counter with explicit wraparound, and **expiry** of unanswered requests. ⚠ And it is a test that must be done **at 90 minutes**, not at five |
| **13** | **Probe cadence hung on socket wake-ups**: with the desktop still the measurement **switches off** | `RdpConnection.cpp:563` | a real timer, or a wait with a **timeout** equal to the cadence |
| **14** | **The wheel with `angleDelta/120`**, **integer** division | `PortalSession.cpp:161` | any step below a notch **is lost**. Confirms §7.2: use `ei_device_scroll_discrete(±120)` and pass the value almost as it is |

> ⭐ **And the most instructive defect of all is in report 14 §2.2**: in 6.3.6 **the direction of
> key press and release was inverted**. It is the same point that in our `input.c` · `manda_bottone()`
> we verified to be right (`gboolean premuto = !(flags & KBD_FLAGS_RELEASE)`). A mature RDP
> server, inside KDE, shipped for one release a defect that shows at the first word typed:
> **the test on the three clients is not bureaucracy.**

#### 12.1 `krfb` — half useful, and not the half one hopes for

`gnome-remote-desktop` was a full reference: same language, same RDP library, same
compositor, 68 730 lines. **krfb is ~5 000 lines of C++ and speaks VNC**, and on this branch
⛔ **it does not even open the port**: `RfbServer::start()` wraps `rfbInitServer` in
`if (passwordSet())` and returns `true` anyway, and in the normal path nobody calls `setPasswordSet`
(`rfbserver.cpp:114`). It is to be read as an **archive**, not as a yardstick.

**The three things it is worth** [R]:

1. ✅ **it confirms our stage model**: one framebuffer per process, alive from start to
   close, indifferent to clients connecting (`rfbservermanager.cpp:113-133`;
   `startMonitor`/`stopMonitor` **empty**);
2. **the pixel sequence on KWin in a single file** (`pw_framebuffer.cpp:125-346`), translatable into
   C almost line by line if one day we went through the portal — and the key choice: opening a
   **RemoteDesktop** session and grafting `ScreenCast.SelectSources` onto it, which on KDE buys **a single
   dialog** for screen and input and access to the mega-authorisation;
3. **eight real defects we can avoid paying for**, and two are of the family that has already bitten us:
   the **damage never negotiated** (`setDamageEnabled` is not called in the whole tree, so krfb
   queues **the whole screen at every frame**), and a 50 ms `QTimer` that imposes **20 fps** —
   i.e. a cap written in-house, exactly the defect of our 18 (R32). The others:
   `buttonMask` passed where the portal wants a 0/1 `state` (`xdpevents.cpp:78` → stuck
   buttons), a double wheel event per step, a step arriving as `delta=±1 px`,
   `||` instead of `&&` in the cursor, physical pixels where logical units are needed, and no listening for the
   end of the session.

*(The first draft wrote here «altre tracce di RDP in KDE: nessuna». It was false: see §12.0.)*

#### 12.4 The other two, found by searching outside the house

*[I]/[C], 7 August 2026. They are the proof that step zero of `LEZIONI.md` §9 is needed: neither of them
was in the repositories I had chosen.*

| | |
|---|---|
| **Sunshine** | since May 2026 has a `kwingrab.cpp` (772 lines) that speaks **our very direct protocol**, and that **writes its own `.desktop` file** with `X-KDE-Wayland-Interfaces` at runtime, waiting 3 000 ms for KWin to see it. It is the **third independent implementation** of the gate of §3, after KRdp and krfb: the permission way is no longer an interpretation |
| **Chrome Remote Desktop** | KDE bug **512620** was opened by a Google engineer who is porting CRD to KDE Wayland. It is a fourth serious reference, and worth keeping an eye on |

**And one thing nobody does** [✗]: **`kwin_wayland --drm` without a monitor**. Searched for in the code, in the
bugs, in the wikis and in the forums: no precedent. The measurement remains entirely ours. Two bugs
confirm however that **we are not getting around an official way, because there is none**: **492285**
says that `startplasma` does not forward the backend choice to the compositor (no merge request), and
**523735**, opened six days before this study, **asks precisely for the headless session** — and
nobody has solved it.

**Two gifts from the input front** [I]: `krdp!217` is moving KRdp **to libei, making it
mandatory** — i.e. the path we chose is the direction KDE is moving in, and their
conversion to `fake_input` will become dead code. And in the discussion of that merge request
there is the partial answer to one of our open measurements: **with libei the wheel direction is Wayland's**,
without the inversion the portal carries along. Plus, in KWin's master,
`EIS_DEVICE_CAP_TEXT` (requires libeis ≥ 1.6, not yet available): the day it arrives, our
«carattere → keysym → tasto → livelli» round becomes superfluous.

⚠ **And a clarification on versions**: Debian Trixie has **krdp 6.3.5-1**, not 6.3.6 — the tag we
cloned is a version that is not on the user's machine. For the differences between 6.3.5 and
6.3.6 I have no material [?].

#### 12.3 `xrdp` — it does not face KWin: it avoids it

*Verified on the source on 7 August 2026 (clone of `neutrinolabs/xrdp` master).*

The question «come fa xrdp con KWin?» has a blunt answer: **it does not talk to it**. In all of xrdp's C code
the word *wayland* appears **11 times**, and none concerns capture or input: they are display
names (`"wayland-n"`), a comment, and **a line that declares the session type to `pam_systemd`**
(`sesman/libsesman/verify_user_pam.c:405-413`) when the display is not X11 — i.e. a label
provision, not an implementation.

What it does instead: `sesman/sesexec/session.c` launches **`Xorg`** (with `xorgxrdp`) or **`Xvnc`**, and
inside that X server runs `sesman/startwm.sh`, which in turn calls the desktop session —
for KDE, `startplasma-x11`. That is, xrdp runs **Plasma in an X11 session**, where the compositor is
`kwin_x11` and capture is an X11 capture: no Wayland protocol, no PipeWire, no
permission to ask.

**Three things follow for us:**

1. ⛔ **xrdp is not a reference for phase 11.** The problems we are studying — the capture
   permission, the virtual output, input on Wayland — **do not exist** in its model. The
   reference is `KRdp` (§12.0);
2. **that path still exists, and works today**: Plasma 6.3.6 still has the X11 session
   (`plasma-workspace/login-sessions/plasmax11.desktop.cmake`, `startkde/startplasma-x11.cpp`,
   `kwin/src/main_x11.cpp`) [R]. It is **the reason why xrdp on KDE works**, and it is also the reason
   why we do not need it: §4.5 of `SPECIFICA.md` excluded X11 sessions — a second complete path
   of capture and input — and KDE is closing that session;
3. and it is worth recording as a **confirmation of the project's basic choice**: the most
   widespread competitor has not yet faced Wayland, while REMOTIX on Wayland already has a desktop that
   works.

#### 12.2 The portal — to be known in order to discard it knowingly

**[R]** Seven facts that decide:

| | |
|---|---|
| `ConnectToEIS` **exists** in 6.3.6 | and it is **a forward of six useful lines** to `org.kde.KWin.EIS.RemoteDesktop`: going through the portal **adds nothing** compared with calling KWin, except the dialog |
| the virtual output **is not announced** among the sources | `AvailableSourceTypes = Monitor\|Window` (`screencast.h:53-56`): only the user can choose «schermo virtuale» in the dialog |
| and its size is **hard-wired to 1920×1080** | `screencast.cpp:299` — no way to ask for 4K, i.e. the number the user wants |
| the PipeWire node is created and owned by **KWin** | `screencastmanager.cpp:84-90`; the portal waits for `created` in a blocking event loop with a **3 s timeout** (`waylandintegration.cpp:354`) |
| the `Notify*` go through `fake_input` | and carry two defects: `NotifyPointerAxis` **inverts the sign of y** (`:434`) while `NotifyPointerAxisDiscrete` does not, and `NotifyKeyboardKeysym` **never releases** the modifier it pressed (`:579-592`) |
| ⛔ `XDG_CURRENT_DESKTOP` must be **exactly `KDE`** | otherwise ScreenCast and RemoteDesktop **are not even registered** (`desktopportal.cpp:43-44`). **First line of any diagnosis** |
| the mega-authorisation | §3.5: the documented loophole for the unattended case, but **no interface writes** that entry |

---

### 13. The bill for REMOTIX

#### 13.1 What it confirms

| REMOTIX decision | Confirmation in KDE's code |
|---|---|
| **Talk to the compositor, not to the portal** | KDE's portal is **a client** of the same protocol, and adds only the dialog (§12.2) |
| **The stage belongs to the session, not to the connection** | krfb practises it by construction (§12.1); and on KWin it is mandatory: an `UNCONNECTED` tears down the virtual output (§4.9) |
| **R9** — the last frame is kept and resent | no «mandami un fotogramma pieno» request exists [✗]; the full frame arrives only on resuming from pause |
| **Cadence declared «quando cambia»** | `framerate` **must** be `0/1`; the cap is `maxFramerate` (§4.5) |
| **The stride is read from the chunk** | `SPA_ROUND_UP_N(width*bpp, 4)`: it is not `width × 4` |
| **The encoder without B-frames** | `max_b_frames = 0` in every kpipewire encoder (§11.3) |
| **We create the audio sink ourselves** | zero lines of Plasma touch the audio devices (§10.4) |
| **`libavcodec` instead of the vendors' APIs** | kpipewire writes against libav, not against libva by hand — and **it does not have** bitrate control **either** (§11.3) |
| **The nine combinations of §3.4** | logind is the same: nothing to redo |
| **The count of pressed keys** | KWin discards repeats and unpaired releases, and releases everything when the client dies (§7.2) |
| ⭐ **The `.desktop` as the path to permission** | **it is what `KRdp` does**, KDE's RDP server, for capture *and* for input (§12.0) |
| ⭐ **The two codecs on the same pipeline** (R3) | `KRdp` makes the same choice: H.264 if the client declares AVC **and** YUV420, otherwise RemoteFX Progressive |
| ⭐ **The frames-in-flight regulator with an RTT-derived threshold** (phase 7) | `KRdp` has the same mechanism, and in master has just refined it by smoothing the RTT |
| ⭐ **The exclusive edges of regions** (R5) | `KRdp` writes `right = rect.right() + 1`: a third agreeing source |
| ⭐ **Pure TLS with PAM** (§3.6) | `KRdp`: `TlsSecurity = usePam`, `NlaSecurity = !usePam` — our choice is also its own, when it authenticates as we do |

#### 13.2 What it refutes, or corrects

1. ⛔ **`SPECIFICA.md` §3.8 must be corrected**: it says *«KWin: cattura PipeWire via **portale**, input
   interfacce KWin, protocollo `kde-fake-input`»*. The code says: capture **via the Wayland protocol
   directly** (the portal is a client like us), input **via libei/EIS over D-Bus** (`fake_input` is the
   old path).
2. ⛔ **`REFERENCE.md` R32 and `LEZIONI.md` §3 row 4**: *«KWin senza monitor disegna in software»* is
   contradicted by the code, and our own table (DMA-BUF with fence) confirms it. **To be
   re-measured before correcting** (§5.1, §15).
3. ⛔ **The 59–60 fps measurements have two labels to review**: they were taken with
   `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` (that is, bypassing the gate) and with `--virtual` +
   `stream_output` **without `--xwayland`** — that is, on **bare KWin**, not on a Plasma session, and not
   in the product's configuration (`stream_virtual_output`, which with `--virtual` **does not work**).
   The number remains a fact; its label does not.
4. ⛔ **Dynamic resolution is not done as on GNOME** (§8): a virtual output cannot be
   resized. The price that phase 6 had paid off comes back, in a different form — and on KDE **it does not
   drag input along**.
5. ✅ **Two of GNOME's debts do not show up**: the session-bus connection that does not
   survive logout (§6.6), and the defect of alternating screens with zero-copy (§4.6).
6. ⚠ **`banco/misura-cattura.c` must be corrected before re-measuring on KWin**: `--fissa` cannot
   negotiate (§4.5), and the cursor's `SPA_CHUNK_FLAG_CORRUPTED` buffers are counted as
   frames (§4.7).

#### 13.3 What is worth copying, in order of yield

0. ⭐ **Read `KRdp` in full** — 4 222 lines, that is one reading session: it is an RDP server
   on the same compositor, with the same library, and each of its choices is an answer to a question
   we have (§12.0). Still to read: `Clipboard.cpp`, `Cursor.cpp`, `NetworkDetection.cpp` and
   `PortalSession.cpp`.
1. **The `.desktop` with `X-KDE-Wayland-Interfaces`**, on the model of
   `org.kde.krdpserver.desktop` (§12.0) or of `org.kde.krfb.virtualmonitor.desktop` (§3.2). It is the
   key of the phase, and it is three lines.
2. **`ei_device_scroll_discrete(±120)`** instead of our `/120 → ×10` (§7.2): simpler than
   what we do, and it produces a real wheel.
3. **Only `DRM_FORMAT_MOD_LINEAR` for GPU encoding** and **the VAAPI context created by the
   filter graph** (§11.2): two silent defects already paid for by others.
4. **Renegotiating the modifiers instead of switching DMA-BUF off** (§11.2).
5. **powerdevil's `AddInhibition(types=4)`** so the screen is not switched off under our feet
   (§10.2).
6. **`org.kde.Shutdown` as the passive logout sentinel** (§6.5): two subscriptions, zero
   risk of holding the user's session hostage.
7. **`KWIN_XKB_DEFAULT_KEYMAP` + `XKB_DEFAULT_*` in the compositor's environment** (§6.7), if one
   day we needed to *impose* the layout instead of reading it.

#### 13.4 The choices to put before the user, before writing

They are product decisions, not technical ones, and `LEZIONI.md` §2.6 says to put them forward **at once**.

> ⚠ **There were three; after the bench of 7 August 2026 two remain**, and that is an improvement: **the first
> was decided by the measurement, not by the user** (M2, §5.2). The rule of
> `remotix-prove-sul-banco-non-sull-utente` applies: what can be measured is not asked.

> #### ✅ DECIDED BY THE USER on 8 August 2026 — all three, and in the best direction
>
> | The question | The decision |
> |---|---|
> | **Zero-copy: now or later?** *(a new question, born from the measurements of §5.7)* | ✅ **now, inside the KDE work.** So **capture is written zero-copy from the start**, with the wait on the fence (§4.8) — it is not written in memory only to go back over it later. It is the condition for 60 fps at 4K |
| **Resizing on Trixie** | ✅ **size fixed at connection**: no video gap, no repositioned window, no system notification. ⛔ **And it is written in the form of PipeWire negotiation** (§8.2), which is phase 6's code: so on **KWin 6.8** real resizing switches on by itself, without anyone rewriting anything |

> #### ⛔ «L'IMMAGINE SI SCALA NEL CLIENT» WAS FALSE — and the user found it
>
> *[M, 8 August 2026: «non riesco a vedere tutto lo schermo, la risoluzione sembra ignorata».]*
>
> The decision above was written with the sentence «l'immagine si scala nel client» beside it, and
> that sentence **had never been measured**. `xfreerdp3` scales nothing: it opens a window
> **as large as the declared canvas**. With the desktop at 1920×1080 and a smaller screen, the
> window does not fit — and whoever looks sees «la risoluzione che ho chiesto viene ignorata», which is
> exactly what happens.
>
> **Client-side scaling exists, and goes through `MAPSURFACETOSCALEDOUTPUT`** — which on **7 August**
> we had already measured as honoured by **one client in three**: `xfreerdp3` yes, mstsc no, RDM declares it
> off (§10.2 of `REFERENCE.md`). That is: the refutation was already in the house, on another page, and the
> decision of 8 August ignored it.
>
> ⭐ **What really holds of the decision, and it is stronger than was thought**: the desktop's
> size is fixed by **the first connection**, and on KDE it is REMOTIX that starts the session — so the
> desktop is born *exactly* at the requested size. The price is not a scaled image: it is that **to
> change size the session has to end**. Now the log says so, instead of letting people
> believe in a scaling that does not happen.
>
> **The lesson, which is not about KDE**: a product decision taken by citing an unmeasured
> behaviour is a decision taken halfway. `LEZIONI.md` §1.11 says it for tests; it applies identically to
> premises.
| **CapsLock and NumLock** | ✅ **the true state is read from KWin**, with `org_kde_kwin_keystate` v5. It costs little **because on KDE we are already a Wayland client** for capture: it is enough to add the interface name to the same `.desktop` (`X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1,org_kde_kwin_keystate`) and a listener. ⚠ In the assessment of 7 August I had given it as «una seconda strada nel codice»: **it was wrong**, the Wayland connection is there anyway |

| | The choice | The price of each path |
|---|---|---|
| ~~**1**~~ | ~~**`--virtual` or `--drm`?**~~ ⛔ **It is NO LONGER a choice: measurement M2 of 7 August 2026 closed it.** `--drm` from a session without a seat exits with status 1 (`Failed to activate … session`, then `No suitable DRM devices have been found`), and the only way to have it would be to occupy `seat0`, that is the physical console. **We go with `--virtual`**, paying §8.1: resolution fixed at startup and no `stream_virtual_output` before KWin 6.8. There is nothing to ask the user | (box in §5.2) |
| **2** | ~~**Dynamic resolution on KDE**~~ ✅ **the choice shrank by itself**: resizing arrives in **KWin 6.8** through **PipeWire negotiation**, that is with the code phase 6 has already written (§8.2). So it is written **in that form** — which becomes right by itself when the user upgrades — and for the versions that do not have it (Trixie included) the **small** question remains: fallback «chiudi e rifai lo stream», or size fixed at connection? | The fallback costs a video gap, rearranged windows and a system notification every round; the fixed size costs nothing and shows only as a scaled image. **To be decided by looking**, and it blocks nothing |
| **3** | **CapsLock and NumLock**: open **also** a Wayland connection (for `org_kde_kwin_keystate`, which requires the `.desktop`), keep the approximate count, or postpone? | The first costs a second path in the code; the second is what we did on GNOME before libei |

---

### 14. The questions the code does not close — the measurement plan

In order of weight. They are the `[?]` of this document, and they are the content of the first
bench day of phase 11.

> #### The state after the bench of 7 August 2026
>
> **Five closed out of twelve, and they are the five that weigh most**: the two «decisive» ones (M1, M2) plus
> M3, M5, M6. None refuted the code; **one refuted us** (R32, the «in software»), and one
> added a requirement that no code reading had shown (`XDG_MENU_PREFIX`, §3.3-bis).
> The bench scripts are in `reference-kde/banco/` (`misure-kde.sh`, `permesso-kde.sh` …
> `permesso6-kde.sh`) and on the server in `/media/REMOTIX/tmp/banco-compositori/`.

| # | What | Why it weighs |
|---|---|---|
| ~~**1**~~ | ✅ **CLOSED: yes, it authorises** — with `NoDisplay=true`, KRdp's form. ⛔ **But on a condition the code did not show: `XDG_MENU_PREFIX=plasma-`**, without which `kbuildsycoca6` indexes **nothing** and KWin says `Could not find the desktop file for …`. Five variants of the file denied before finding it. §3.3-bis | it is the gate: if it does not pass, everything else is theory (§3) |
| ~~**2**~~ | ⛔ **CLOSED: no.** `--drm` without a seat exits with 1 (`Failed to activate … session` → `No suitable DRM devices`), and **not** because of Unix permissions: in the same environment `--virtual` opens `renderD129`. So **`--virtual`**, and decision 1 of §13.4 is no longer asked of the user. §5.2 | decides choice no. 1 of §13.4 (§5.2, §6.3) |
| ~~**3**~~ | ✅ **CLOSED: GPU.** `renderD129` open, `libEGL_mesa` + `libgbm` loaded, `zwp_linux_dmabuf_v1` **v4** announced. **R32 must be corrected.** ⚠ Two traps found: on Mesa 25 llvmpipe lives inside `libgallium-*.so` (searching for it by name proves nothing), and `kwin_wayland` is **non-dumpable** because of the `security.capability` xattr (`/proc` must be read with `sudo`). 🟡 **M3d** remains, the buffer type: `MemFd/BGRx/LINEAR` negotiated, but because of a limit of **our** client. §5.1 | corrects R32 (§5.1, §5.3) |
| ~~**4**~~ | ⛔ **CLOSED: it starts in software.** With the render nodes inaccessible and `KWIN_COMPOSE=O2`: `forced to OpenGL` → `Falling back to defaults` → `QPainter … successfully initialized`, **and KWin starts**. The switch is **inert**: it must be struck from the recipes and from every bench, and the only way to know how KWin renders is **to ask it** (§5.3-bis). ⚠ Note: `LIBGL_ALWAYS_SOFTWARE` and the other Mesa variables **have no effect** on KWin. §5.4 | if it starts, it must be struck from our recipes, and all measurements taken with that variable must be re-read (§5.4) |
| ~~**5**~~ | ✅ **CLOSED: yes, with nothing.** `gdbus … org.kde.KWin.EIS.RemoteDesktop.connectToEIS 7` from any SSH shell → **`(handle 0, 1)`**: a descriptor and a cookie, **without a session, without a portal, without a dialog and without a `.desktop`**. Input via libei on KDE is confirmed in the field | it is the fourth question of the phase, and the code says yes (§7.1) |
| ~~**6**~~ | ✅ **CLOSED: yes.** `libeis-dev` is in the `Build-Depends` of `kwin 4:6.3.6-1`, and — proof that does not lie — **`eis.so` is inside the `kwin-common` package** (`/usr/lib/<triplet>/qt6/plugins/kwin/plugins/eis.so`), libei 1.3.901. ⚠ `kwin-wayland` does **not** depend on `libeis1`: looking there would have given the wrong answer | the premise for input is there (§7.1) |
| ~~**7**~~ | ✅ **PARTLY CLOSED.** Setting up a stream costs **65–67 ms** (three rounds), and it is the fixed component of the gap. The time to *recreate the output* cannot be measured on `--virtual`, where `stream_virtual_output` is refused (`Could not find output`, verified). §8.1 | decides choice no. 2 of §13.4 (§8.3) |
| ~~**8**~~ | ✅ **CLOSED: capture is independent of the VT.** The `--virtual` compositor **opens no tty/console** (verified on `/proc/<pid>/fd`), its session has `VTNr=0` and an empty `Seat=`; switching VT (tty1 → tty2 → tty1 with `VT_ACTIVATE`, because `chvt` is not installed) **compositor, stream and protocol all stay alive**. §4.9 | it is the condition for an unattended service (§4.9) |
| ~~**9**~~ | ✅ **CLOSED: yes.** After `org.kde.Shutdown.logout()` all Plasma processes vanish and the Wayland socket with them, **but the user bus still answers on the same connection** and `systemd --user` is alive. GNOME's defect does not recur. §6.6 | if yes, a GNOME defect does not recur (§6.6) |
| ~~**10**~~ | ✅ **CLOSED by reading, and the reading is conclusive**: `eiscontext.cpp:272-285` **does not invert** and uses **the same formula for both axes** (`delta = v120 × 15/120`, raw `v120` downstream). No KWin asymmetry to compensate: the adaptation is all ours. The by-eye check in the phase remains. §7.2 | §7.2 |
| ~~**11**~~ | 🟡 **CLOSED as far as possible**: `0x0`, `-1x-1`, `1x1`, `16384²`, `99999²` **all refused** and **KWin survives all of them**. But the refusal is due to the absence of a virtual output, not to validation: **validation remains unmeasurable with `--virtual`**. §8.1 | no validation in the code (§4.3) |
| ~~**12**~~ | 🟡 **CORRECTED**: the dialog is **not** the first risk. At the first OpenGL failure plasmashell writes **`SceneGraphBackend=software` persistently** and restarts; the `QMessageBox` comes only on the second round. The real risk is **the permanent configuration left in the user's home**. With the GPU: none of this (verified). §10.4 | ten seconds, and it blocks a session (§10.4) |
| **13** *(new, from the bench)* | **`InaccessiblePaths=` in the compositor's unit closes the capture gate** — 0 `KWIN_UTILS` lines against 13. The mechanism is not proven; the operating rule is: **no mount namespaces in KWin's unit**. §3.3-bis | it was the obvious way to choose the GPU, and it is a trap |

**The method, which is worth more than the list**: measurements 3 and 4 must be done **before** the others and with
tests that do not depend on what KWin declares. It is lesson 1.8 of `LEZIONI.md`, and on KWin the
code shows two points where the fallback is silent by construction.

> #### The state after the second bench day (8 August 2026)
>
> **Twelve out of twelve have an answer**, plus a thirteenth found along the way. Seven were
> closed on this day (M3d, M4, M7, M8, M9, M10, M11, M12), and the results that change the
> plan are three:
>
> 1. ⭐ **zero-copy is the condition for 60 fps at 4K** on the GPU chosen by the user (§5.7);
> 2. ⛔ **`KWIN_COMPOSE=O2` does not protect** (M4), so every measurement must be accompanied by the
>    renderer string (§5.3-bis);
> 3. ⛔ **the obvious way to choose the GPU breaks the capture permission** (§5.6, §3.3-bis).
>
> ⚠ **And two structural proofs we had taken as good do not hold**: «render node aperto» does not prove the
> GPU (open in QPainter too), and «il flusso è MemFd» does not prove the compositor is in software
> (it depends on what the *client* asks for). The lessons are in `LEZIONI.md` §1.9 and §1.11.

> #### ✅ AND ON 8 AUGUST 2026 ITEM 1 PUT THE WHOLE DOCUMENT TO THE TEST
>
> *Bench `prove/fase11.sh`, with the real REMOTIX in place of `nodo-kwin`. The account is in `PIANO.md`
> phase 11; here is what changes in this document.*
>
> **Nothing written here was refuted.** The four things the field added:
>
> | | |
> |---|---|
> | ✅ **the gate opens for us too** (§3) | `.desktop` with `Exec=` on the canonical binary and `NoDisplay=true`, plus `XDG_MENU_PREFIX=plasma-` in KWin's environment: the global appears, no dialog. With `--installa-desktop` REMOTIX writes the file itself, from `/proc/self/exe` |
> | ✅ **the fence is waited on, and that is all** (§4.8) | **2 400 buffers out of 2 400** with drawing in progress — the 8 August measurement confirmed on a sample eight times larger — and **zero expired waits** with a 50 ms cap. R29's defect does not recur: the frames are whole |
> | ✅ **the modifier obtained is `0x0`, linear** (§11.2) | it is the one the encoder wants, and to get it it was enough to put it **first** in the proposal's enum. `INVALID` stays as second choice |
> | ✅ **the pace holds, on the real chain** (§5.7) | **58.1 fps at 1080p and 58.4 at 4K** on the Intel, against the 59.2 and 59.0 measured with `misura-cattura` alone. The difference is the conversion on the card, which the bench did not do |
>
> ⛔ **And a new trap, which is not KDE's but belongs to benches that redo the session**: killing
> `kwin_wayland` queues on systemd a *stop* job for its unit, and a
> `StartUnit("plasma-workspace-wayland.target")` that arrives before that job has finished is
> **rejected wholesale** — *«Transaction … is destructive»* — with `startplasma-wayland` saying
> only «Could not start Plasma session». Whoever redoes the session twice in a row fails the
> second time: stop the target and **wait** for the unit to be `inactive`.

---

### 14-bis. ✅ The study is closed — what was learned by WRITING, not by reading

*8 August 2026, with phase 11 concluded for KDE.*

The twelve measurements are closed (§14), and their yield is high: **eleven questions out of eleven had an
answer before a line was written**. But four defects appeared only when the code was put
in front of a user, and they are worth listing because **they are the kind of thing re-reading the code
does not find** — and so it will recur on XFCE:

| Found by | What | Where it is now |
|---|---|---|
| **the user, at first glance** | two mouse pointers | box at the top: the cursor is inside the image, and the cure is a transparent theme |
| **the user** | the volume slider governed nothing | §10.5 — and the defect was **on GNOME too**, all along |
| **the user** | «Blocca» and «Cambia utente» inert in the menu | §10.6 — KIOSK, three actions and not two |
| **the bench, but only after strengthening it** | «una via audio nuova parte al massimo» does not work | `REFERENCE.md` §7.5, **open** |

⭐ **Three out of four were in the shared path**, that is they were GNOME defects that nobody had
seen in ten phases. Opening a second compositor did not just add a desktop: it acted as a
bench for the first.

⛔ **And the method lesson, which is the most costly**: the volume defect stayed invisible because
the test had been done on **an equivalent sink created with `pactl`** instead of on ours — and
`pipewire-pulse` sets by itself the property we were missing. A bench that tests *something similar*
acquits the code (`LEZIONI.md` §1.11 and §5).

---

### 15. The corrections to make to the documents

As §7.0 of `SPECIFICA.md` prescribes, when a measurement contradicts a document it is updated
**at the same moment**. The first three rows were born from a **code reading** and were noted
as tensions to resolve; **the bench of 7 August 2026 resolved them**, and now they are real refutations:

| Document | What it says today | What the bench says |
|---|---|---|
| `SPECIFICA.md` §3.8 | «KWin: cattura via **portale**, input `kde-fake-input`» | capture via **direct Wayland protocol**, input via **libei/EIS** (§13.2 no. 1) — **correction applied**, with the date. And now **measured**: `connectToEIS(7)` → `(handle 0, 1)`, and the `.desktop` opens the global |
| `REFERENCE.md` **R32** | «KWin senza monitor disegna in software: zero nodi DRM, nessuna libreria GL» | ⛔ **refuted, with three proofs** [M]: `renderD129` open, `libEGL_mesa`+`libgbm` loaded, `zwp_linux_dmabuf_v1` v4 announced. **It must be corrected**: the «60 fps a 4K» stays, the «in software» label does not (§5.1) |
| `LEZIONI.md` §3, row 4 and row «KWin tiene la cattura dietro un controllo di permessi» | «NO, in software»; «serve il permesso per la via che KDE prevede» | the first as above; the second now has **a measured answer**: the `.desktop` **plus `XDG_MENU_PREFIX=plasma-`** (§3.3-bis) |
| `PIANO.md` phase 11 | the four opening questions | **four out of four have a bench answer**, and the «`--virtual` o `--drm`» decision was closed by a measurement instead of by the user (§5.2) |

> ✅ **All applied**, the last on 8 August 2026 with the closing of the phase. Two corrections were
> added along the way, and they should be read together with the first ones because they are born from the same mistake —
> **having believed a code reading without measuring it**:
>
> | Document | What it said | What the bench says |
> |---|---|---|
> | `LEZIONI.md` §3, question 5 | «KWin: sì, `stream_virtual_output`» | ⛔ **no**: with the `--virtual` backend it answers `Could not find output`, for every size. **Corrected** |
> | this document, at the top | «il cursore è fuori dal percorso del codificatore» | ⛔ **it is inside the image**, and the user saw it before we did. **Corrected**, with the cure |

---

### 16. What is not there, so as not to look for it

All negative statements verified by grep over all eight repositories [✗]:

| Feature | State in KDE 6.3.6 |
|---|---|
| `zwlr_screencopy_manager_v1`, `ext_image_copy_capture_v1` | **absent** in KWin |
| A D-Bus screencast interface (the analogue of `org.gnome.Mutter.ScreenCast`) | **absent**: capture goes through the Wayland protocol, full stop |
| `org.kde.KWin.VirtualOutputs` | **absent** (it was in KWin 5) |
| A **resize** request in the screencast protocol | **proposed and rejected** (`plasma-wayland-protocols!138`), because the chosen path is **PipeWire negotiation**: merged in `kwin!7932`, milestone **6.8** — not in Trixie, but it is coming (§8.2) |
| `wlr-output-management`, `ext-data-control-v1`, `kde_primary_output_v1` (global) | **absent** |
| `eis_device_keyboard_send_xkb_modifiers` in KWin | **absent**: no `KEYBOARD_MODIFIERS` |
| `eis_region_set_mapping_id` in KWin | **absent**: regions without a key |
| `keyboard_keysym` of `fake_input` v6 | **not implemented** (KWin stops at v5) |
| A permission check on `org.kde.KWin.EIS.RemoteDesktop` | **absent** |
| `EnableClipboard`/`DisableClipboard` | **absent**: the clipboard does not belong to a session |
| A forced `Logout(2)` | **absent**: forcing is `StopUnit` |
| `RegisterClient`/`EndSession` on D-Bus | **absent**: the equivalent is XSMP over ICE |
| `ConditionEnvironment=` in KDE's units | **absent** |
| A **Vulkan** renderer in KWin | **absent** |
| `libseat`/`seatd` | **absent**: only logind, ConsoleKit, Noop |
| H.264 bitrate control in kpipewire | **absent**, as in `gnome-remote-desktop` |
| ~~An RDP backend in KDE~~ | ⛔ **wrong**: there is **`KRdp`** (§12.0), which is the phase's reference |
| A `disable-animations` per capture session | **absent**: they are switched off per session |


<a id="xfce"></a>

## XFCE, labwc and wlroots — code study, for phase 11

*Written on 8 August 2026, opening the third desktop, with ten parallel searches over the sources cloned
at Debian Trixie's versions. It is the project's sixth study, after `protocollo-rdp.md`,
§gnome-remote-desktop, `client-android.md`, `xrdp-funzionalita.md` and §kde.*

> **How to read this document.** Every statement carries a mark, and the mark counts more than the
> sentence:
>
> | | |
> |---|---|
> | **[R]** | read in the code, with `file:riga`. **It is not a measurement**: it says what the program *can* do, not what it *does* on our machine |
> | **[M]** | measured. Where present, it says on which machine and when |
> | **[?]** | deduction or hypothesis. To be treated as an open question, not as a fact |
> | **[✗]** | verified **absent**, saying how it was searched for and with which positive control |
>
> The detail with the `file:riga` references is in the **ten reports** in `reference-xfce/rapporti/`
> (~9 000 lines). Here is what is needed to decide and to write.

---

### 1. In two minutes

**XFCE has no compositor of its own.** On Wayland it starts **labwc**, and labwc is **wlroots** — the third and
last family of the landscape. With GNOME (Mutter) and KDE (KWin) served, this one completes the round.

**The difference that changes the shape of the code**, and that was already written in `LEZIONI.md` §3: wlroots
**makes you pull** frames instead of pushing them. There is no PipeWire in between, there is no D-Bus: there is a
Wayland protocol, `zwlr_screencopy_manager_v1`, and for every frame one does
`capture_output → frame → copy → ready`. The stream is not «set up»: it is requested, one at a time.

**The six answers that matter, all better than on KDE:**

| | |
|---|---|
| **The capture permission** | ✅ **does not exist**. [M, laptop, 8 Aug] A bare client (`env -i`, only `XDG_RUNTIME_DIR` and `WAYLAND_DISPLAY`) sees 45 globals and captures at the first attempt. No `.desktop`, no dialog, no portal. The only gate is the UID: `/run/user/1000` is `drwx------` |
| **The seat** | ✅ **not needed**. With `WLR_BACKENDS=headless` a `wlr_session` is never created and libseat is not even touched: the wall on which `kwin_wayland --drm` died **does not exist here** |
| **The GPU** | ✅ **one variable**: `WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128`. No udev rule, no node permissions denied to the user's whole session |
| **Hot resizing** | ✅ **yes**: `set_custom_mode` on a headless output has no cap at all. The «misura fissa alla connessione» fallback KDE imposed on us **is not needed** |
| **The cadence** | ⭐ **it is our own parameter**: on headless the output's refresh *is* the period of the frame timer |
| **The clipboard** | ✅ **`appunti_wlr.c` works as it is**: it is written against a wlroots protocol, and here we are on its home ground |

**And the five that cost:**

| | |
|---|---|
| ⛔ **No protocol creates an output** | `wlr-virtual-output` **does not exist** [✗]. A headless output is born **1280×720 hard-wired**, and labwc has neither IPC nor `<output>` in its configuration: the size is given **only** through the protocol, **after** startup |
| ⛔ **The cursor is always inside the image** | the headless backend has no `set_cursor`, so no hardware cursor exists; and `overlay_cursor` **does not remove it** — it *forces* it to software. It is the same shape as `KWIN_COMPOSE=O2`: a lever that seems to be there and does nothing |
| ⛔ **libei does not exist on wlroots** | [✗] searched in wlroots, labwc, sway, wayfire, weston, xdpw, wayvnc: zero. `input.c` **becomes a Wayland client**: the tables are reused, not the transport |
| ⛔ **`xfce4-power-manager` switches our output off** | it speaks native Wayland and after **10 minutes** on mains power sends `zwlr_output_power_v1(OFF)`; output off ⇒ no frames ⇒ `failed` on capture |
| ⛔ **At logout XFCE can kill our session** | if the compositor's command line does not contain *both* `labwc` *and* `--session`, `xfce4-session` runs `loginctl terminate-session ''` |

**And step zero — *«chi, al mondo, fa questa cosa su questo desktop?»* — has an answer that must be
stated in full**: **nobody does RDP on wlroots without a monitor**. Only one RDP server in the world talks
to wlroots (Rust, BSL licence) and **declares that it requires an already-running desktop**; `xrdp` has had no
Wayland since 2017; `freerdp-shadow` has no Wayland backend and the maintainers wrote that it is
unlikely to arrive; and whoever goes through the portal on wlroots is **video-only**, because
`xdg-desktop-portal-wlr` does not implement `RemoteDesktop`.

> ⭐ **But there is a precedent, and it is on our side.** wlroots **did have** an RDP backend, and it was
> removed in 0.10 *«interamente in favore di wayvnc»* after five crash issues. The
> community has already ruled that the right place for this thing is **an external client of the
> compositor** — that is exactly where we are. And labwc **quotes wayvnc verbatim in its own
> documentation**, anticipating the virtual output resizable by the remote client.

---

### 2. The map: where each thing lives

| What | Where | Trixie version |
|---|---|---|
| the compositor | `reference-xfce/labwc/` | **0.8.3** |
| the compositor's library | `reference-xfce/wlroots/` | **0.18.2** |
| the wlroots protocols | `reference-xfce/wlr-protocols/` | (screencopy, data-control, virtual-pointer, output-management…) |
| the standard protocols | `reference-xfce/wayland-protocols/` | **1.38** |
| the session | `reference-xfce/xfce4-session/` | **4.20.2** |
| panel, desktop, settings | `xfce4-panel/` 4.20.4, `xfdesktop/` 4.20.1, `xfce4-settings/` 4.20.1 | |
| XFCE's X11/Wayland abstraction | `libxfce4windowing/` | **4.20.2** |
| the common libraries | `libxfce4ui/` 4.20.1, `libxfce4util/` 4.20.1, `xfconf/` 4.20.0, `garcon/` 4.20.0 | |
| power and locking | `xfce4-power-manager/` 4.20.0, `xfce4-screensaver/` 4.18.4 | |
| **who already does it** | `wayvnc/` 0.9.1 + `neatvnc/` 0.9.1, `weston/` 14.0.2 (RDP backend), `xdg-desktop-portal-wlr/` 0.7.1 | |
| the points of comparison | `sway/` 1.10.1, `wayfire/` 0.9.0 | |

⚠ **The versions installed on the server match the cloned ones exactly** [M, 8 Aug]: labwc
0.8.3-1, xfce4-session 4.20.2-2, xfce4-panel 4.20.4-1, xfdesktop4 4.20.1-1, xfce4-settings 4.20.1-1,
sway 1.10.1-2, weston 14.0.2-1. The study and the bench speak of the same machine.

⚠ **Wayfire is not in the same code family**: `meson.build:45,49` asks for wlroots
`>=0.17.0, <0.18.0` and vendors it. Everything that follows holds for **labwc** (our target) and
for **sway** (the point of comparison). Wayfire must be re-read on 0.17 if and when it is needed.

---

### 3. ✅ The gate that isn't there

On KWin this section is the longest in the document and took five bench tests. Here it
closes in three lines, and it is **measured** [M, laptop with labwc 0.8.3, 8 August 2026] even before
being deduced.

| | |
|---|---|
| **What a bare client sees** | 45 globals, among them `zwlr_screencopy_manager_v1` **v3**, `zwlr_virtual_pointer_manager_v1` **v2**, `zwp_virtual_keyboard_manager_v1` **v1**, `zwlr_data_control_manager_v1` **v2**, `zwlr_layer_shell_v1` v4 |
| **What is needed in the environment** | `XDG_RUNTIME_DIR` and `WAYLAND_DISPLAY`. Nothing else: the capture succeeded at the first attempt (`buffer(1280×720, stride 5120)` → `copy()` → `ready`, non-zero checksum) |
| **The code that explains it** | `labwc/src/server.c:344` — `return true` for every client **without** a security context; `wlroots/types/wlr_security_context_v1.c:435-437` — whoever comes in through the normal socket has no context |

**[✗] wlroots 0.18.2 filters nothing**: zero calls to `wl_display_set_global_filter` in the whole
tree. The filter that labwc and sway have fires **only** on clients that came in through someone
else's `listen_fd`, i.e. Flatpak and bwrap — and we will never be there. Wayfire does not filter at all.

⛔ **And the opposite direction does not exist**: labwc's `rc.xml` **has no protocol switch at all**
[✗], on none of the three compositors. An administrator who wanted to *close* capture has no
configuration lever — information that concerns us because it means that **nobody can shut the
door on us by mistake**.

#### 3.1 ⚠ Where the risk lies instead: diagnosis

The permission is not the danger; the danger is **not seeing why something fails**.

| | |
|---|---|
| ⛔ **labwc does not log** | neither the connection nor the `bind`, not even with `-d`. On an illegal request it only writes `error in client communication (pid N)`, at **INFO** level (invisible without `-V`): the PID, not the interface nor the code |
| ⛔ **`WLR_DEBUG` does not exist** [✗] | `wlroots/util/log.c` has not a single `getenv`. The level is decided by the compositor, with `-d`/`-V` on the command line |
| ✅ **Diagnosis is done from the client side, and it is excellent** | libwayland prints by itself on stderr `zwlr_screencopy_frame_v1#3: error 1: invalid buffer dimensions`, and `wl_display_get_protocol_error()` returns **interface and code**. `WAYLAND_DEBUG=1` gives the full trace |

⭐ **Hence a rule for our code**: after *every* failure, call
`wl_display_get_protocol_error()` and write out its result. It is the equivalent of lesson §1.10 — *before
trying variants, get told the cause* — with the difference that here the component that denies does not speak, and
our client does.

#### 3.2 ⛔ A protocol error kills the connection

It is not a lost frame: it is the connection. [M] `roundtrip = -1`, `EPROTO`, no recovery — everything must
be redone from `wl_display_connect`.

**The three rules that follow from it, and that hold for all the new code:**

1. **Format, dimensions and stride are copied *exactly* from the `buffer` event.** No alignment
   of our own (`wlroots/types/wlr_screencopy_v1.c:384-432`);
2. **a single `copy()` per frame**, then a new `capture_output()` (`:391`);
3. **the keymap before the first key**, or `no_keymap` (`wlroots/types/wlr_virtual_keyboard_v1.c:84,107`).

---

### 4. Capture: `zwlr_screencopy_manager_v1`

*Detail: `reference-xfce/rapporti/01-cattura-screencopy.md`.*

#### 4.1 ✅ Whole frames, always — and the GNOME defect does not come back

`frame_shm_copy`/`frame_dma_copy` use `frame->box`, i.e. **the whole output**, and never consult
the damage (`wlr_screencopy_v1.c:214-219`, `:255-268`). The source buffer is in turn complete thanks
to the damage ring's *buffer age* (`types/scene/wlr_scene.c:1910-1911`).

⭐ **That is, the trap that keeps zero-copy off on GNOME — the buffer that is a «diff» over four
recycled buffers, R29 — does not exist here.** A pool of reused buffers is fine without precautions, and the
accumulation surface is not needed.

#### 4.2 ⛔ The pull model, and its two traps

| | |
|---|---|
| **`copy_with_damage` on a still screen** | ⛔ **`ready` never arrives**, and there is no timeout at all: the listener stays attached (`:297-303`). We need **a timer of our own** that, on expiry, destroys the frame and reopens with plain `copy` |
| **plain `copy`** | ⛔ calls `wlr_output_update_needs_frame()` (`:448`), i.e. **forces rendering** even on a motionless screen. A naive loop at 30 fps makes the compositor render 30 frames per second of nothing |

⭐ **The right form is shown by wayvnc**, and it is the structural correction to the 18 fps problem of
7 August: `copy_with_damage` as a rule, whole `copy` only when a frame is needed at once (first
client, output change, size change, wake-up) — and **the cadence subtracts the measured latency of the
compositor**: `time_left = 1/rate − dt − delay`, with `delay` measured at every `ready` and low-pass
filtered at 0.5 s (`wayvnc/src/screencopy.c:308`, `:214-215`).

#### 4.3 ⭐ The double ledger of damage — mandatory, not an optimisation

Every buffer carries **two** damages: `frame_damage` (which goes to the encoder) and `buffer_damage` (which goes to the
compositor). When a frame is ready with damage D, D is added to the `buffer_damage` of **all** the
buffers in the pool (`wayvnc/src/buffer.c:693-704`).

⛔ **Without it, frames are sent with old pieces, and no frames-per-second measurement
reveals it** — it is the R29 defect in general form, and the reason it must be written now and not later.

⚠ And wlroots' damage is **a single rectangle** (the extents, with an explicit `// TODO` at
`:168-178`), in the output's pixel coordinates, **not** translated for `capture_output_region`. It must be
**clipped** to the buffer rectangle before trusting it, as wayvnc does (`main.c:1145-1146`).

#### 4.4 Zero-copy: possible, and in a better form than Mutter's

| Road | What it delivers | Verdict |
|---|---|---|
| **`copy` onto a DMA-BUF buffer** | a **GPU blit** into a buffer **owned by the client** (`wlr_renderer_begin_buffer_pass` + `add_texture` + `submit`, `wlr_screencopy_v1.c:249-270`) | ✅ **our road**: no CPU read, stable buffer, format for VA-API |
| `copy` onto an shm buffer | `glFinish()` + `glReadPixels` (`render/gles2/texture.c:206,218`) | ⛔ **blocks the compositor's main loop** |
| `zwlr_export_dmabuf_v1` | the *compositor's* buffer, but with the **TRANSIENT** flag always raised (`wlr_export_dmabuf_v1.c:75`) | ⛔ it is the GNOME trap in pure form. To be discarded |

⚠ **It is not zero-copy in the strict sense** — there is a blit — but it is **a single copy, on the card**, and the
buffer is ours: it is precisely the form that phases 8 and 9 learned to consume.

⚠ **Synchronisation**: with GLES2 the DMA-BUF branch only does `glFlush()` (`render/gles2/pass.c:39`),
**no explicit fence**: it relies on implicit sync. The Vulkan renderer instead correctly imports
a sync file into the DMA-BUF (`render/vulkan/renderer.c:1025-1029`) — but in `auto` Vulkan
**is never attempted** in 0.18.2 (`wlr_renderer.c:244`). It is the same point that on Mutter cost
phase 9, and it must be **measured** before believing it.

⚠ **The modifiers do not come from the `linux_dmabuf` event**, which carries only format/width/height
(xml:214-223) and is not checked by wlroots: they must be taken from the `zwp_linux_dmabuf_v1` feedback, as
wayvnc and the portal do.

#### 4.5 Formats and depth

The shm format is chosen by the renderer via `GL_IMPLEMENTATION_COLOR_READ_FORMAT` and **cannot be
requested**; the field must be treated as a **fourcc**, not as an enum (`render/pixel_format.c:215-224`).
24-bit `BGR888` exists in the table but **[?]** will never come out of the GL query: one receives 32 bits and
converts downstream — as on Mutter, where R32 had already established that a packed 24-bit path
does not exist.

#### 4.6 The successor, and why the code must be written with two implementations

**[✗] `ext-image-copy-capture-v1` does not exist** in wlroots 0.18.2, labwc 0.8.3, wayfire 0.9.0 nor sway
1.10.1 (grep at zero on all four, with a positive control on `screencopy`). On Trixie **the only
way is `zwlr_screencopy`**.

But **wayvnc 0.9.1 already speaks it**, and chooses at runtime in twelve lines
(`wayvnc/src/screencopy-interface.c:29-45`), with the differing capabilities in a bit mask and **a
single point** where the code branches. ⭐ **It is the form to copy**, because the new protocol
brings two things we need: the **modifiers**, and a **cursor session** with position and hotspot —
i.e. the definitive cure for the double pointer.

⚠ And it also brings a change of model to know now: **the new protocol is diff-based** («at least
the union of the region passed by the client and the region advertised by `damage`»), with full damage
only on the first frame. Whoever writes it without knowing this pays for R29 a third time.

---

### 5. Without a monitor: headless, GPU, cadence

*Detail: `reference-xfce/rapporti/03-output-headless-gpu.md`.*

#### 5.1 ✅ No seat, no libseat

`grep session|libseat|drm backend/headless/` → **empty** [✗]. With `WLR_BACKENDS=headless` a
`wlr_session` is never created (`backend/backend.c:308-316`). The wall against which `kwin_wayland --drm` exited with
status 1 from an SSH shell **does not exist here**, and no logind `Activate()` is needed.

#### 5.2 ⭐ The GPU is chosen with a variable — and the fallback is the trap

| | |
|---|---|
| **How it is chosen** | `WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128` (`render/wlr_renderer.c:147-158`, accepts only `renderD*`) |
| **The default** | the **first** render node from `drmGetDevices2()`, with an immediate `break` |
| ⛔ **The fallback** | **does not exist**: if the `open` fails, wlroots **does not try the other card** — it falls into **pixman**, i.e. software, without an error |

⭐ **Hence: KDE's udev rule is not needed, and denying a node would be counterproductive.** On KWin
denying the node was the only way to choose the card, and the price was denying it to the user's whole
session. Here an environment variable is enough.

⚠ **And lesson §1.11 holds identically**: «render node aperto» does not prove the GPU here either, and
«DMA-BUF offerto» proves **the allocator**, not the drawing. **[✗] There is no API nor IPC to ask for the
renderer** in 0.18.2 (`struct wlr_renderer` has no `name`): nothing equivalent to KWin's
`supportInformation`. Two roads remain, both to be used: **`-V` at compositor
startup** (labwc and sway start at `WLR_ERROR` and do not print `GL renderer:` without it), and the
**mandatory positive control** — redo the measurement with `WLR_RENDERER=pixman` and see that it
**changes**.

With headless and the default: **GLES2 + GBM allocator** (`allocator.c:101-103`), so zero-copy is
available. With pixman the allocator is shm and screencopy **does not offer** the DMA-BUF format at all
(`wlr_screencopy_v1.c:574-577`) — which, noted in passing, is a useful *negative* proof: if
DMA-BUF is not offered, we are in software.

#### 5.3 ⭐ The cadence is our parameter

On a headless output `frame_delay = 1 000 000 / refresh_mHz` ms (`backend/headless/output.c:25-32`):
**the third argument of `set_custom_mode` becomes the period of the frame timer.**

| declared refresh | period | cap |
|---|---|---|
| 60 Hz | 16 ms | **62.5 fps** |
| 30 Hz | 33 ms | 30 fps |

No other compositor ever gave us this lever: on Mutter the cadence was declared to PipeWire and
we got six tenths of it; on KWin the cap was `maxFramerate` and the server honoured it. ⚠ wayvnc
leaves it at 0 with a TODO, so here **we have no precedent to copy**.

⛔ **And frames really are pulled**: no damage ⇒ no commit
(`types/scene/wlr_scene.c:1705-1709`) ⇒ the timer is not re-armed (`headless/output.c:76`). What wakes it
again is the capture itself, with `wlr_output_update_needs_frame()` inside `copy`.

#### 5.4 ⛔ Two silences to know before writing

1. **Never touch adaptive sync**: `ADAPTIVE_SYNC_ENABLED` is **outside** the headless mask
   (`headless/output.c:10-14`) and makes **the entire** commit fail with `Unsupported output state fields:
   0x40` — which looks like a rejection of the size. `false` instead is a silent no-op;
2. **Asking for the size the output already has** does not produce a modeset: `output_compare_state` removes the
   `MODE` field and the commit succeeds **without doing anything** (labwc works around it by raising the width by 1,
   `labwc/src/output.c:1084-1104`).

And a third, on the configuration protocol: **old serial ⇒ `cancelled`, not `failed`**
(`wlr_output_management_v1.c:446-455`). Whoever listens only for `succeeded`/`failed` stays hanging forever.

---

### 6. ✅ Hot resizing: it can be done — and KDE's fallback is not needed

*It is question 13 of `LEZIONI.md` §3, the one that on KWin decided half the plan.*

`zwlr_output_configuration_head_v1::set_custom_mode` resizes a headless output hot.
**The only validation along the whole path** is `width<=0 || height<=0 || refresh<0`
(`wlr_output_management_v1.c:216-241`) plus `pending_width==0` (`types/output/output.c:593-596`).
**[✗] No cap**, searched with grep on wlroots and on the three compositors.

**The precedent exists and it is not ours**: wayvnc resizes the output to the client's resolution
(`wayvnc/src/main.c:802-826` → `output-management.c:230-287`), and from there we also copy the discipline —
**enumerate all the heads** with enable/disable, or wayfire refuses.

#### 6.1 ⛔ But the output is NOT created, and not destroyed

| | |
|---|---|
| **[✗] `wlr-virtual-output` does not exist** | ten protocols in `wlr-protocols/unstable/`, none creates outputs. `wlr-output-management` *configures* them: *«Heads cannot be created nor destroyed by the client»* |
| **[✗] No variable gives the initial size** | ⚠ *refined on 8 August, studying LXQt*: the hard-wired sizes are **two, different depending on the route** — `WLR_HEADLESS_OUTPUTS` creates **1280×720** outputs (`wlroots/backend/backend.c:237`), while **labwc's** virtual outputs are born **1920×1080** (`labwc/src/output-virtual.c:52-53`). Neither carries the size: `WLR_HEADLESS_OUTPUTS` carries only the **number** |
| **[✗] labwc has no IPC** | `grep -rli ipc labwc/src` → nothing, and `rc.xml` has no `<output>` at all. `VirtualOutputAdd` accepts the **name** but not the size and is reachable **only from a keybind**. ⚠ There is, however, **`LABWC_FALLBACK_OUTPUT`** (`output-virtual.c:109-135`): with an **empty** layout labwc creates by itself a virtual output with the given name — and it is the mechanism upstream documents so that a `NOOP-…` name makes wayvnc recognise a resizable output. It fires **only** with an empty layout, so it wants `WLR_HEADLESS_OUTPUTS=0` [?, to be tested] |

⭐ **Hence the forced form**: start the compositor headless, connect, and **resize the
existing output**. Not «si crea l'output della misura chiesta», which is what we did on KWin with
`--virtual --width/--height`.

⛔ **And destroying and recreating is forbidden from three different sides**, all in XFCE:

| | |
|---|---|
| `xfsettingsd` | if a **new** output appears it **disables** it and launches `xfce4-display-settings` (`displays-wayland.c:524-528`, `:541-546`). ⚠ And mind the direction: `action <= SHOW_DIALOG` means that **`/Notify=0` disables too** — 2 or 3 are needed |
| `xfce4-panel` | exits without doing anything if `n_monitors == 0` (`panel-window.c:2640-2642`, comment «temporary state on Wayland») |
| `xfdesktop` | loses the wallpaper settings if the connector name changes: **the xfconf key *is* the connector** (`xfdesktop-backdrop-manager.c:169`) |

⚠ And a detail to keep for the bench: the panel **does not use** the monitor API of
`libxfce4windowing` [✗], it listens to `GdkScreen::monitors-changed`. What we have to trigger is GDK.

---

### 7. Input: `input.c` becomes a Wayland client

*Detail: `reference-xfce/rapporti/04-input.md`.*

**[✗] libei does not exist on wlroots** — searched `libei|EIS|ei_device|ei_seat|ei_new` in wlroots, labwc,
sway, wayfire, weston, xdg-desktop-portal-wlr and wayvnc: zero, with a positive control on
`virtual_keyboard` giving 67/15/16/10 lines. And **[✗] `xdg-desktop-portal-wlr` has no `RemoteDesktop`**
(`wlr.portal:3`: only Screenshot and ScreenCast).

So: `zwp_virtual_keyboard_manager_v1` **v1** and `zwlr_virtual_pointer_manager_v1` **v2**, without
any permission (wlroots does not filter; labwc and sway filter only sandboxed clients).

#### 7.1 What is reused, and what is rewritten

| | |
|---|---|
| ✅ **reused** | the scancode set 1 → VK → evdev tables, the button map, the Pause-key state machine, the session logic. The evdev↔X11 offset is **8** in both directions |
| ⛔ **rewritten** | the transport (D-Bus/EIS → `wl_registry`) and **all the modifier handling**, which did not exist with libei |

**[?] About half the file.** ⚠ And a decision to take **before** writing: if capture too
is a Wayland protocol, **a single `wl_display` connection serves both**.

#### 7.2 ⛔ The five silent traps

| # | | |
|---|---|---|
| 1 | **The wheel wants ±1 clicks**, not ±120 | `axis_discrete(t, axis, value, discrete)` with `discrete` **in whole clicks**; wlroots multiplies by 120 **itself** (`wlr_virtual_pointer_v1.c:183-184`). KWin's convention here would give **120 clicks** |
| 2 | **`value` must never be 0** | with `value == 0` an `axis_stop` goes out and the click vanishes (`wlr_seat_pointer.c:369-391`). wayvnc uses **15.0**, «valore magico misurato con `wev`» |
| 3 | **Without `frame` nothing arrives** | the axes stay in the buffer (`wlr_virtual_pointer_v1.c:109-122`), and `frame` is needed for **all** events, not just the wheel |
| 4 | **We send the modifiers ourselves, always** | wlroots builds the event with `update_state = false` (`:92`) and does not update `xkb_state`: **without `modifiers`, Shift+A gives `a`**. We need an `xkb_state` of our own |
| 5 | **`wlr_pointer_finish()` does not release the buttons** (`types/wlr_pointer.c:38-42`) | on disconnection we must send `button(release)` + `frame` ourselves before `destroy`, or **the desktop stays with the left button pressed**. The keyboard instead releases them by itself. ⚠ `[M]` 21 Sep 2026, laptop, labwc headless: the keyboard yes (Shift released when our socket dropped); and with **ours as the only pointer** the seat loses the capability and a fresh click after reattaching arrives whole **even without** the release — the trap bites only if there is another pointer in the seat `[?]` |

⚠ **The wheel direction**: vertical **inverted** with respect to Wayland, horizontal not — and **nobody
corrects it for us**, because on a virtual device labwc skips libinput (`scroll_factor = 1.0`,
no natural scrolling nor acceleration). On sway and wayfire instead `scroll_factor` **applies
to us too**. Weston confirms the conversion line by line, and it is the most precious piece of its
RDP backend: value in the low 8 bits of the flags, negative = `(0xff - v) * -1`, **two accumulators per
axis** (`≥ 12` smooth step, `/120` discrete click, with `%=` keeping the remainder).

#### 7.3 ⭐ The locks can be read — but only because the compositor is labwc

wlroots sends `wl_keyboard.modifiers` **only to the client with focus**
(`seat/wlr_seat_keyboard.c:191-213`). We have no surface, so we should see nothing.

**But labwc broadcasts it to everyone, without a surface** (`input/keyboard.c:106-133`, called at `:186-193`),
with a comment saying that **sway used to do it and stopped**. So `mods_locked` gives **real** CapsLock and
NumLock, and `group` gives the layout.

| | |
|---|---|
| ✅ | on KDE this answer had cost a dedicated protocol (`org_kde_kwin_keystate`) |
| ⚠ | **it is labwc behaviour, not protocol**: on sway the same read is `[✗]` |
| ⚠ | **the initial state never arrives** — one knows the first change, not the starting situation |
| ⚠ | beware of the **feedback loop** with our own `modifiers` |

#### 7.4 The keymap: we present it, but copied from the wire

Mandatory before every `key` (`no_keymap`, `wlr_virtual_keyboard_v1.c:83-88`). ⭐ **The right
form**: do `wl_seat.get_keyboard` — wlroots sends `keymap` at once, without focus
(`seat/wlr_seat_keyboard.c:412-417`) — and **pass that content on**. It is better than wayvnc, which
generates it from configuration, and there is a strong reason: on labwc **every key** does
`wlr_seat_set_keyboard`, which **resends the keymap to all clients**.

⛔ **`[M]` 21 September 2026, on the laptop (labwc 0.8.3 headless, phase 13 increment 3): on a
session WITHOUT a real keyboard the copy from the wire cannot be done.** The seat declares capability **0**
until a keyboard exists, so `get_keyboard` has nothing to deliver. ⇒ `wlr_input.c`
attempts it and, if it does not arrive, presents the **environment's** one, declaring so; the right layout
comes right after with the one **negotiated** with the client, which on wlroots becomes the keymap of our
keyboard (labwc passes it on to the applications together with our keys — `[M]` the witness receives it).

✅ **Repetition is not ours to do**: nobody repeats on the compositor side, RDP's repeated `key down`s
are **discarded** by wlroots anyway (`wlr_keyboard.c:68-83`), and repetition is done by
the application via `repeat_info`.

#### 7.5 ⚠ labwc eats our shortcuts

`match_keybinding(..., is_virtual)` skips the keycode comparison but **still applies the
shortcuts** (`input/keyboard.c:225-228`, `:548-560`), and the scroll mousebinds swallow the
click using **our** modifiers too (`keyboard_get_all_modifiers`, `:57-79` — with a
comment that names wayvnc). To be taken into account: part of what we send does not reach the
applications.

#### 7.6 The seat: we inject into the existing one

**[✗] labwc does not create `ext_transient_seat_v1`** (sway does, wlroots has it). On XFCE **there is no choice**:
we inject into the user's seat. ⭐ And since REMOTIX runs **with no user present**, it is also the best
case — it is precisely what gives us the reading of the real locks in §7.3.

---

### 8. ✅ The clipboard: `appunti_wlr.c` works as it is

*Detail: `reference-xfce/rapporti/05-appunti.md`.*

`zwlr_data_control_manager_v1` **v2** on all three compositors, without permissions. We wrote the file
for KWin but **against the wlroots protocol**: here we are in its home.

**The two lessons paid for on KWin hold, and for the same mechanical reason:**

| | |
|---|---|
| **The echo is certain, not probable** | every device subscribes to `seat->events.set_selection` **without a filter on the originator** (`wlr_data_control_v1.c:620-622`) |
| **`cancelled` precedes `selection`** | and more solidly than on KWin: it is all inside `wlr_seat_set_selection` — line 196 destroys the old source, line 211 emits the signal. **Two lines of the same function, no asynchronous re-entry in between.** The state guard **does not need revisiting** |
| **`POLLHUP` counts as «pronto»** | `client_source_send` does `close(fd)` right after the event (`:131`): with short data the `poll` returns with only `POLLHUP` |

**The three reservations, all ours and all small:**

1. **[?] `kwin_display_apri`** (`appunti_wlr.c:441`): if it filters the socket by name, on labwc nothing
   opens. It is the only thing that can stop the file from working;
2. **wlroots silently discards duplicate MIMEs** (`:47-54`) and our `tipi_uguali` fails on
   differing length: a duplicate in the client's list ⇒ guard skipped ⇒ **infinite loop**;
3. the `onlyReplaceEmpty` workaround is useless here: **[✗]** absent from the whole tree.

⭐ **And there is a better guard than ours, to be evaluated**: wayvnc offers a **second synthetic MIME**
`x-wayvnc-client-%08x` and, if it sees it again in an offer, knows it is its own and ignores it
(`wayvnc/src/data-control.c:196-199`). It is more solid than a comparison of types, and in RDP the problem is
identical.

**The rest, in brief**: **[✗] `ext-data-control-v1` does not exist** in wlroots 0.18.2 nor in
wayland-protocols 1.38 — on Trixie `zwlr` is the only door, even though upstream it is already marked deprecated.
The Xwayland bridge works **in both directions for free**, going through the same seat state.
The clipboard **does not survive the death of whoever copied**, and in XFCE on Wayland **there is no
manager** (`xfsettingsd` starts it only under X11): i.e. the housemate that on KDE was klipper is not
here.

---

### 9. The XFCE session without a monitor

*Detail: `reference-xfce/rapporti/06-sessione-xfce.md`.*

#### 9.1 The compositor is hard-wired in a script

`default_compositor="labwc"` in `xfce4-session/scripts/startxfce4.in:121` — **it is not a
configuration, it is a script line**. It is replaced only by passing the command line to
`startxfce4 --wayland <cmd>` (`:37-40`, `:164`), or with `XFCE4_SESSION_COMPOSITOR`, which is
`exec`-ed as is (`xinitrc.in:147`).

⭐ **The line to copy**: `labwc --config-dir … --config … --session xfce4-session`. The `--session`
makes `xfce4-session` the *primary client*: when it exits, **labwc terminates**
(`labwc/src/main.c:43`, `:96-104`; `server.c:167-170`). Logout comes for free.

#### 9.2 ⛔ The trap that can kill our session

If `XFCE4_SESSION_COMPOSITOR` does not contain **both** `labwc` **and** `--session`, at logout
`xfce4-session` runs **`loginctl terminate-session ''`** (`xfce4-session/main.c:257-273`) — i.e. the
REMOTIX logind session.

**Double defence**, and both must be put in place: xfconf `xfce4-session` `/general/WaylandLogoutCommand`
= `/bin/true` (it takes precedence, `:259`) **plus** the environment variable written properly.

⚠ **It is the first thing to test on the bench**, and never on the user (`LEZIONI.md` §2.6).

#### 9.3 The environment: what to put in and what to take out

| Put in | Why |
|---|---|
| `XDG_RUNTIME_DIR` | labwc exits without it (`main.c:201-204`) |
| `XDG_CURRENT_DESKTOP=XFCE` | **before** labwc, which otherwise sets it to `labwc:wlroots` with `overwrite=0` (`config/session.c:249`) |
| `XDG_MENU_PREFIX=xfce-` | ⚠ **not because it is missing** — garcon falls back on `xfce-` by itself (`garcon-private.h:37-39`, with a comment that says explicitly «so garcon doesn't break when xfce is not started with startxfce4»). The danger is **inheriting a wrong one** (`plasma-`, `gnome-`) **or an empty one**: the test is `prefix != NULL`, not `*prefix`, and then `garcon_menu_load()` fails with `G_FILE_ERROR_NOENT` **with no fallback at all**. It is lesson §1.10 in reversed form: not «metti la variabile», but **«componi l'ambiente da zero, o ti porti dietro quella di un altro desktop»** |
| `WLR_BACKENDS=headless` | and `WLR_LIBINPUT_NO_DEVICES=1`, which is the recipe declared by wayvnc (`FAQ.md:3-8`) and **[M]** tested on the laptop |
| `WLR_RENDER_DRM_DEVICE` | the card, §5.2 |
| `LABWC_UPDATE_ACTIVATION_ENV=1` | ⚠ **mandatory**: labwc propagates `WAYLAND_DISPLAY` to the bus and to systemd **only if the backend is DRM** (`config/session.c:186-207`). On headless it does not, **silently** |
| `XCURSOR_THEME` (+ `XCURSOR_SIZE`) | §10.1 |

| Take out | Why |
|---|---|
| `WAYLAND_DISPLAY`, `WAYLAND_SOCKET` | nested backend (`wlroots/backend/backend.c:375-402`) |
| `DISPLAY` | X11 backend — and on GTK it makes it fall back to X11 **silently**, re-enabling XSETTINGS, keyboard grabs and XEmbed systray: **two behaviours under the same label**, i.e. lesson §1.8 |
| `SESSION_MANAGER` | `xfce4-session` exits (`main.c:97-102`) |
| `GDK_BACKEND` | must be set to **plain `wayland`**, not `wayland,x11` |

⚠ **`~/.ICEauthority` must be writable**: `xfce4-session` exits even on Wayland if it cannot
open it (`main.c:114-127`).

#### 9.4 ⚠ Eight seconds per priority group, and they are structural

On Wayland **no client registers with the session manager**, so every priority group is
unblocked **by timeout**: `STARTUP_TIMEOUT_WAYLAND = 8000` (`xfsm-manager.h:43`).

And the reason is definitive, not an edge case: `xfce-sm-client.c` is compiled **only inside
`if ENABLE_X11`** (`libxfce4ui/Makefile.am:73-82`), `configure` forces `enable_libsm=no` without X11, the
connection is pure XSMP and requires `$SESSION_MANAGER`, which `xfce4-session` exports only in the
X11 layer. **[✗] Nobody can register on Wayland, and no xfconf key shortens the timeout** — the
constants are hard-wired.

⭐ **Hence: REMOTIX's timeout for «il desktop è su» must be set ≥ 8 s**, and a saved session with
different priorities multiplies it.

#### 9.5 Logout: passive watch, as on KDE

| | |
|---|---|
| **bus** | `org.xfce.SessionManager` |
| **path** | `/org/xfce/SessionManager` |
| **interface** | `org.xfce.Session.Manager` ⚠ **name ≠ interface**, mind the dot |
| **signal** | `StateChanged(u old, u new)` — 0 Startup, 1 Idle, 2 Checkpoint, 3 Shutdown, 4 Phase2 |
| **«il desktop è su»** | `StateChanged(old=0, new=1)` (`xfsm-manager.c:861-867`). ⚠ Use `old==0`: Checkpoint produces 1→2→1 |

✅ **Do not register and do not inhibit**: `Logout` **does not consult the inhibitor**
(`xfsm-manager.c:2409-2431`), and a `RegisterClient` would make us wait until `DIE_TIMEOUT` — the
same mistake that on KDE would have slowed logout by fifteen seconds.

#### 9.6 ⚠ The saved session is tied to the socket name

`~/.cache/sessions/xfce4-session-<display>` with `display` = `wayland-0`… A different socket is a
different session, and **a wrong saved session rises again with the priorities and geometries of another
screen**. `SaveOnExit` is already `false` by default, but the cache must be **deleted at every start**.

It is the same shape as the KDE defect, where plasmashell wrote `SceneGraphBackend=software`
persistently: **a session started badly leaves a mark in the user's home**.

#### 9.7 The session bus — a decision to take

`startxfce4 --wayland` uses **`dbus-run-session`**: a private bus that is born with the compositor and dies with
logout. ⚠ If we use it, **the REMOTIX watcher does not see `StateChanged`**.

On Trixie `dbus-user-session` is installed, so **[?] the recommended road is the systemd user
bus** (`$XDG_RUNTIME_DIR/bus`) without `dbus-run-session`. It is a design choice, to be tested.

---

### 10. The system around it: cursor, power, menu entries

*Detail: `reference-xfce/rapporti/07-componenti-xfce.md` and `06-sessione-xfce.md` §13.*

#### 10.1 ⭐ The cursor: the KDE cure carries over, with one constraint fewer

**The fact**: on a headless output the cursor is **always** inside the captured image. The headless
backend does not implement `set_cursor` [✗], so there is no hardware cursor, so the scene
paints it into the framebuffer (`types/output/cursor.c:285-289`, `types/scene/wlr_scene.c:1998`). And
`overlay_cursor` **removes nothing**: it *forces* software cursors (`wlr_screencopy_v1.c:451-454`).

⭐ **The cure is the same as on KDE — make the cursor invisible, not hidden**: an
`XCURSOR_THEME` theme with a 1×1 cursor at zero alpha, and the pointer goes back to being the client's.

| | |
|---|---|
| ✅ **one constraint fewer** | on labwc the theme comes from `XCURSOR_THEME`/`XCURSOR_SIZE` **in the environment** (`labwc/src/input/cursor.c:1405-1414`), and **`XCURSOR_SIZE` is not mandatory** (default 24 on the same line) — unlike KWin, which looked at the theme only if the size was there too |
| ⛔ **the same trap** | if the theme loads **zero** cursors, wlroots falls back to a **built-in, visible** theme (`wlr_xcursor.c:219-221`). It needs at least one valid cursor, `index.theme` **without `Inherits=`**, and the ten names labwc asks for (`cursor.c:39-64`) |
| ⚠ **two levers, not one** | the environment covers the compositor and non-GTK clients; **GTK3** clients use their own theme, which on Wayland comes from xfconf `xsettings /Gtk/CursorThemeName` via a **GTK module announced on D-Bus** (`org.gtk.Settings`), no longer via XSETTINGS |
| ✅ **the insertion point already exists** | XFCE ships `xfce4-session/labwc/labwc-environment:7` with `XCURSOR_THEME=Adwaita`, and `startxfce4.in:141-146` copies it **only if it is missing** |

#### 10.2 ⛔ `xfce4-power-manager` turns the output off, and must be inhibited

It speaks native Wayland: `zwlr_output_power_v1_set_mode(OFF)` (`xfpm-dpms-wayland.c:233`), with default
`DPMS_ENABLED TRUE` and **10 minutes on mains power** (`common/xfpm-config.h:50-60`). labwc exposes the
protocol (`server.c:683-688`) and on `MODE_OFF` it **disables the output** (`output.c:1063-1078`) ⇒
timer never re-armed ⇒ **`failed` on the capture**.

| Way | How |
|---|---|
| **D-Bus** | `org.freedesktop.PowerManagement.Inhibit` on `/org/freedesktop/PowerManagement/Inhibit`, signature `(ss)→u` (`xfpm-inhibit.c:349-353`). Covers DPMS + idle + screensaver in one go. ⚠ **Precondition**: xfce4-power-manager **has no D-Bus activation** [✗] — if it is not running, the call fails (it is the shape of the powerdevil defect on KDE, where the error was `ServiceUnknown`) |
| **xfconf** | `dpms-enabled=false`, `inactivity-on-{ac,battery}=0`, `presentation-mode=true` |
| ⭐ **the wayvnc cure** | `set_mode(MODE_ON)` **before** capturing, plus a retry at 100 ms (`wayvnc/src/main.c:1022-1045`, `:1055-1063`) — that is, do not trust the inhibition, **turn it back on** |

✅ **`xfce4-screensaver`, on the other hand, is not a risk**: it is pure X11 and exits with `EXIT_FAILURE` if the GDK
display is not X11. ⚠ But with `GDK_BACKEND=wayland,x11` it could come back to life on Xwayland: **plain `wayland`**.

#### 10.3 ⭐ The screen lock is switched off with a single key

On KDE this part was KIOSK; here the lever is simpler and stronger: xfconf channel
`xfce4-session`, key **`/general/LockCommand`**. If it is set, `xfce_screensaver_lock()`
runs it and **returns its result without trying anything else** — no D-Bus, no `xdg-screensaver`,
no fallbacks (`libxfce4ui/xfce-screensaver.c:570-596`).

Setting it to `/bin/false` neutralises **in one go** `xflock4`, the D-Bus method
`org.xfce.Session.Manager.Lock` and every panel button.

⚠ **The empty string counts as «not set»** (`:299-305`): the Debian default `LockCommand=""` is
normalised to NULL, so today the D-Bus chain carries on. A **real** value must be written.

⚠ And two details that explain why it is worth it: the D-Bus chain can **activate** `xfce4-screensaver`
(which on Wayland exits at once), and the three fallbacks are `g_spawn_command_line_sync`, that is they **block the
main loop of `xfce4-session`**.

#### 10.4 ⛔ In XFCE there is no KIOSK — and the entries must be removed, not locked

Confirmed definitively: in the whole cloned tree, libraries included, `xfce_kiosk_query`
appears **only** in `xfsm-shutdown.c:137-138`, with only two capabilities: **`Shutdown`** and
**`SaveSession`**. [✗] No use in panel, desktop, settings, power, screensaver,
libxfce4ui. **KIOSK cannot remove the screen lock nor touch the panel.**

| | |
|---|---|
| **The xfconf lock** | prevents **changing** an entry, **does not remove it** |
| **The real lever** | the panel's `actions` plugin: `xfce4-panel /plugins/plugin-<N>/items`, **array of strings** with a `+`/`-` prefix; the `-` does `continue`, that is **the entry is not created** (`actions.c:1318`, `:1518`). A `+` entry that is not allowed instead stays **visible and greyed out** |
| ⚠ **two pitfalls** | the names `logout`/`logout-dialog` are **swapped** with respect to the enums; and the stock default already has `+lock-screen` and `+switch-user` |
| ⛔ **removing `xflock4` is not enough** | the plugin falls back to `loginctl lock-session`, `dm-tool`, `gdmflexiserver`, `shutdown`, `systemctl` (`actions.c:1049-1085`) |
| **[✗] the logout dialog** | no key removes «Log Out/Restart/Shut Down»: only polkit and logind remain |

⭐ **The way to preset the panel**: `xfce4/panel/default.xml` looked up along `XDG_CONFIG_DIRS`
(`migrate/main.c:36-37`, `:63-101`), applied **silently** if it is not the stock one. For the other
channels the system defaults live in `/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/<canale>.xml`.

#### 10.6 xfconf: the lock, and the write that succeeds without succeeding

| | |
|---|---|
| **The lock is an XML attribute**, not a separate file | `locked="utente"` (or `unlocked=`) on `<channel>` or `<property>` (`xfconf/docs/spec/perchannel-xml.txt:44-53`). Allowed **only in system files**: in a user file it is a **parsing error** |
| ⭐ **With the channel locked, the user's file is not even read** | (`xfconf-backend-perchannel-xml.c:1710`) — it is the strongest form, and it is the one we need |
| ⛔ **Two traps of the lock** | **`locked="*"` locks nobody** (no wildcard: only `strcmp`), and **`@gruppo` looks only at `gr_mem[]`**, so it **ignores the primary group** — on Debian `@<nomeutente>` does not work. Write **the bare user name** |

⛔ **And the point that changes the way provisioning is written**: **a write to a locked property
gives no error to the writer.** The daemon refuses with `XFCONF_ERROR_PERMISSION_DENIED`, but
`xfconf_channel_set_property()` is **asynchronous**: it updates the local cache, emits `property-changed`,
**returns TRUE**; on the reply the value is restored and a `g_warning` is left on stderr. ⇒
**`xfconf-query` exits with `EXIT_SUCCESS`.**

⭐ **Hence the rule, which is `LEZIONI.md` §1.9 applied to configuration: after writing a
value, read it back.** A bench that settles for the exit status of `xfconf-query` is green on
a configuration that was not applied.

⚠ And three details of the daemon: `xfconfd` **has** D-Bus activation and channels are loaded lazily
(so writing the defaults *before* it starts works); but **[✗] it has no `GFileMonitor`** — a
channel already loaded **does not re-read** a file changed underneath it; and the write to disk is **delayed by
5 seconds**, with an orderly flush on `SIGTERM` and **lost** on `SIGKILL`.

⛔ **Correction to what one might have hoped**: the system defaults avoid *writing* into the user's
home, **not** leaving a trace there. `xfconfd` **always creates**
`~/.config/xfce4/xfconf/xfce-perchannel-xml/` at startup — and **does not start** if it cannot — and on the
first write it dumps **the whole channel tree** there. **[?] The only way to leave no trace
is an ephemeral `XDG_CONFIG_HOME`**, which is a project decision, not a detail.

#### 10.7 ✅ The menu: garcon does not have the KDE trap

**[✗] garcon builds no index on disk** (grep for `g_file_set_contents|fopen|g_mkdir…` →
zero, with a positive control): the cache is **in memory only**. That is, the defect that on KDE
denied us a permission — *an index built empty that stays empty* — **cannot happen here on
disk**.

⛔ **But the same shape exists in memory**: `garcon_menu_start_monitoring()` is called **after** a
successful load (`garcon-menu.c:817-819`). If the first load fails, **no monitor exists
at all**, so `reload-required` never arrives and the menu stays empty **for the life of the
process** — and the failure is **a modal window in the remote user's face**. On XFCE you do not
delete a file: **you restart the process**.

⚠ And `XDG_CURRENT_DESKTOP` must be **plain `XFCE`, upper case, with no suffixes**: for submenus garcon
**does not split on `:`** (while for entries it does), so with `XFCE:qualcosa` the
`OnlyShowIn=XFCE;` directories **disappear**. With the variable *empty* the filter switches off and you see **more**,
not less.

✅ Finally, read in the shipped menu: **«Esci» is an entry in the file**, while **«Blocca schermo» and «Cambia
utente» are not menu entries** [✗] — they live only in the panel (§10.4).

#### 10.5 XFCE's hard requirements on the compositor

| Protocol | Who demands it | What happens without it |
|---|---|---|
| `zwlr_layer_shell_v1` | xfdesktop, xfce4-panel | ⛔ **xfdesktop exits with `exit(1)`** (`xfdesktop-application.c:1017-1027`); the panel degrades and does not load external plugins |
| `zxdg_output_manager_v1` | libxfce4windowing | the **logical** geometry comes only from there: without it, it stays `{0,0,0,0}` and so does the workarea |
| `wl_output` **v4** | libxfce4windowing | the `name` is the identifier |
| `ext_workspace_manager_v1` | the pager | ✅ labwc has it; **[✗]** sway and wayfire do not |

✅ All present in labwc 0.8.3. ⚠ And `xfsettingsd` on Wayland **registers no shortcut at all**
(six modules behind `#ifdef ENABLE_X11`): the `xfce4-keyboard-shortcuts` channel is **inert**, and no
key combination can launch `xflock4`. Side effect: XSettings not propagated, hence themes and fonts
different from those expected.

---

### 11. Who already does it, and what we steal from them

*Detail: `reference-xfce/rapporti/08-wayvnc.md`, `09-weston-rdp.md`, `10-portale-e-chi-lo-fa.md`.*

#### 11.1 wayvnc — the practical reference of the family

**The five things to copy:**

1. ⭐ **the cadence that subtracts the compositor's latency** (§4.2): it is the structural correction to
   the 18 fps problem;
2. ⭐ **the double damage ledger** (§4.3): mandatory, not an optimisation;
3. ⭐ **the abstract interface with two capture implementations** and the capabilities in a bit
   mask, with **a single point** of branching;
4. **the anti-echo MIME mark** on the clipboard (§8);
5. **`--show-performance`**: frames per second **and average percentage of damaged area**, every
   second. The second number is the one our benches have never had.

**The three not to copy:** DMA-BUF **off by default** (`--gpu`); no per-client scaler — a client that
cannot resize itself **gets disconnected**, and with our 4K/60 requirement that does not hold; and the creation
of the output **delegated to `swaymsg`**, which does not exist on labwc.

⚠ And two of its defects, useful as a warning: the bandwidth regulator **is voluntary** (if the client
does not announce `FENCE` the brake is never armed — ours must stay mandatory), and the cursor
comes **only** from the new protocol: with `wlr-screencopy` alone wayvnc **sends no cursor at all**.

#### 11.2 Weston — the oldest RDP backend in the Wayland world

**Its video is behind and there is nothing to copy there**: [✗] no MS-RDPEGFX, no H.264,
no GPU (even with the GL renderer the buffer is read back into RAM and compressed by the CPU), the damage
becomes a bounding box, and **[✗] the flow regulator does not exist** — it announces
`SurfaceFrameMarkerEnabled=TRUE` and then does not listen to the acks. **Our formula is more advanced than the
reference project.**

**But three things are worth it, and all are accessible to us:**

| | |
|---|---|
| ⭐ **the RDP→Wayland wheel** | line by line (§7.2) |
| ⭐ **the thread → event loop bridge** | `eventfd(EFD_SEMAPHORE)` + list with mutex + `assert_compositor_thread()` at the top of every callback (`rdputil.c:79-226`). Needed right away: our `cliprdr` also runs on a FreeRDP thread |
| ⭐ **the certificate per peer, never shared** | the backend keeps only the **paths**; each peer does `freerdp_certificate_new_from_file()` and hands ownership to FreeRDP (`rdp.c:1755-1764`). **It is the direct antidote to the defect that on KDE killed the server on the second connection** |

And two gifts for input conversion: the chain
`GetVirtualKeyCodeFromVirtualScanCode → KBDEXT → GetKeycodeFromVirtualKeyCode(XKB) → scan_code - 8`
(no hand-made table: it is delegated to WinPR), and ⚠ **the FreeRDP 3 trap**: `KBD_FLAGS_DOWN` is
never set — **the absence of `KBD_FLAGS_RELEASE` *is* the press**.

⚠ **And a §1.11 lesson in pure form**: Weston's lock keys **do not work**, and nobody
says so. `weston_keyboard_set_locks()` exits with `-1` on the first line if `!seat->led_update`, and the
RDP seat never sets it. The idea is right, the implementation is dead: **the first `return`
of every API we call must be checked**.

On resizing: **[✗] MS-RDPEDISP is not there**, but there is one thing to steal — at the new size
Weston **copies the old content into the new buffer** (`PIXMAN_OP_SRC`) so as not to show black on the
first frame.

#### 11.3 The PipeWire bridge: free on copies, expensive on everything else

`xdg-desktop-portal-wlr` allocates the buffers itself and **passes the same `wl_buffer` to screencopy**: DMA-BUF =
**one GPU blit**, which is the protocol's intrinsic copy and would be identical if we spoke screencopy
ourselves. **On copies the bridge costs nothing.**

**The price is elsewhere, and it is four structural facts:**

| | |
|---|---|
| ⛔ **we cannot request a frame** | no `.process`, no `PW_STREAM_FLAG_DRIVER`, and **always `copy_with_damage`** — with a still screen `ready` does not arrive |
| ⛔ **we cannot negotiate the size** | [✗] `SPA_POD_CHOICE_RANGE_Rectangle` does not exist: the size is a fixed `SPA_POD_Rectangle`. Resizing goes through a **separate** protocol |
| ⛔ **no separate cursor** | `METADATA` is refused, `SPA_META_Cursor` never mentioned. RDP wants the *Pointer Update* separately |
| ⚠ **four processes, ≥3 IPC hops** | on a budget of **16.6 ms** per frame |

**The opposite account**: speaking screencopy directly costs **[R] ≈1 200 new lines** — but the
DMA-BUF stays a `gbm_bo` allocated by us, so **the import and the fence wait of phases
8 and 9 are reused whole**: only the `pw_stream` layer is lost.

---

### 12. The fourteen questions of `LEZIONI.md` §3, with the wlroots column filled in

*All **[R]** except where marked: it is a reading of code, not a measurement, and §14 says which ones must be
measured first.*

| # | The question | wlroots 0.18.2 / labwc 0.8.3 |
|---|---|---|
| 1 | **How is capture requested without a portal?** | `zwlr_screencopy_manager_v1` **v3**, direct Wayland protocol |
| 2 | **Does it push or make us pull?** | ⛔ **it makes us pull**: `capture_output → frame → copy → ready`, one per frame |
| 3 | **Is it behind a permission?** | ✅ **no** [M]. No filter, no `.desktop`, no dialog |
| 4 | **Without a monitor, does it draw on the GPU?** | ✅ **yes** with headless + default (GLES2 + GBM). ⚠ but the fallback to pixman is **silent**, and there is no way to ask the compositor which renderer it uses [✗] |
| 5 | **Can a virtual screen of the desired size be requested?** | ⛔ **not at startup** (1280×720 hard-wired), ✅ **yes afterwards**, with `set_custom_mode` |
| 6 | **How much does it deliver?** | **61** at 1080p and 1440p, **40.3** at 4K [M, 7 Aug, sway, `wl_shm`] — at 4K the cost is the copy in memory |
| 7 | **How does the declared cadence behave?** | ⭐ **there is no cadence to declare**: the refresh of the headless output *is* the timer period, and the pace is set by our loop |
| 8 | **Whole frames or «diff»?** | ✅ **whole, always** — the damage is never consulted in the copy |
| 9 | **Does the buffer arrive already drawn?** | ⚠ **[?]**: GLES2 only does `glFlush()`, no explicit fence. **To be measured** |
| 10 | **What does resolution cost?** | at 4K **yes** in memory (61 → 40); **[?]** in DMA-BUF, to be measured |
| 11 | **What does colour depth cost?** | nothing; no packed 24-bit path |
| 12 | **Can the size change while capture is live?** | ✅ **yes** — but **[?]** what happens to the capture in progress must be measured |
| **12-bis** | ⭐ **Is the cursor inside the image?** | ⛔ **yes, always**, on headless. And `overlay_cursor` does not remove it |
| **13** | ⭐ **Does a virtual screen resize live?** | ✅ **yes, with no cap** — the best answer of the three families |
| **14** | ⭐ **Whose is the clipboard?** | **the compositor's**, `zwlr_data_control_manager_v1` v2, no permission — and **no clipboard manager** in XFCE on Wayland |

⭐ **And the fifteenth, which this desktop adds to the list for the next one**: **«chi possiede il
ciclo dei fotogrammi?»** On Mutter and KWin the compositor owns it and we consume; here
**we** own it, and with it the pace, the cost and the responsibility of not making the
compositor render for nothing. It is question 2 carried to its consequences, and it must be asked **before** 6:
because on a pull compositor, *«quanto eroga»* is not a property of the compositor — **it is a
property of our loop**.

---

### 13. The choices to put before the user

| # | The choice | The terms |
|---|---|---|
| **1** | **Direct screencopy or PipeWire bridge?** | direct: ~1 200 new lines, but control of the pace, of the cursor and of the size, and whole reuse of the DMA-BUF consumer of phases 8-9. Bridge: fewer lines, but ⛔ none of the three things above, and four processes on the 16.6 ms budget |
| **2** | **Is live resizing switched on right away?** | on KDE the fixed size was chosen **because KWin could do nothing else**. Here **it can be done**, and the precedent (wayvnc) exists. It remains to decide whether to do it in phase 11 or later |
| **3** | **The cursor: inside the image or on the RDP channel?** | today the transparent theme is the ready cure (§10.1). The *real* cursor — shape and hotspot on the RDP pointer channel — comes **only with the new protocol**, which Trixie does not have: it would be work that today cannot even be tested |
| **4** | **The session bus: private or the user's?** | `dbus-run-session` is what XFCE does on its own, but **it hides `StateChanged` from us**. The systemd user bus is the recommended road **[?]**, and must be tried |
| **5** | **The dangerous entries: how many do we remove?** | «Blocca schermo» has a clean cure (§10.3). «Cambia utente» and shutdown require rewriting the panel layout — which is a change to the user's home, and he is the one who pays its price |

---

### 14. The measurement plan that opens the phase

*In order, and every measurement has a positive control, because «zero» and «forbidden» look the
same (`LEZIONI.md` §1.9).*

| # | The measurement | Why it is there |
|---|---|---|
| **M1** | the two input globals really appear from an **SSH shell**, and the devices get created | it is the premise of the whole of chapter 7. The capture permission is already measured, the input one is not |
| **M2** | ⛔ **`WaylandLogoutCommand` prevents `loginctl terminate-session ''`** | it is the only measurement that, done wrong, **kills the session of whoever runs it**. On the bench, never on the user |
| **M3** | screencopy on **DMA-BUF**: is the buffer whole? is the fence ready or must it be waited for? | these are questions 8 and 9, and they decide whether zero-copy is born switched on as on KDE |
| **M4** | the **cadence at 1080p and 4K** with the declared scene, also counting how much the client draws | R32 redone for this family — and here the number depends **on our loop**, not on the compositor |
| **M5** | GPU or pixman: **positive control** with `WLR_RENDERER=pixman` and with the wrong card | §5.2. The fallback is silent by construction |
| **M6** | `set_custom_mode` with capture live: does the capture survive? does the panel rearrange itself? | §6, and the way `xfsettingsd` disables new outputs |
| **M7** | the full XFCE session starts headless, and in how many seconds | §9.4: the eight seconds per priority group are structural |
| **M8** | the DPMS inhibition holds for ten minutes | §10.2, and the precondition that xfce4-power-manager is alive |
| **M9** | the transparent cursor theme **does not make wlroots fall back** to the visible theme | §10.1, and it is the trap already paid for on KDE |
| **M10** | `appunti_wlr.c` as it is, against labwc | §8, and the three reservations |
| **M11** | every xfconf value written by provisioning **is read back** | §10.6: a successful write proves nothing, and it is a green that costs an afternoon |

---

### 15. The lessons this study adds, even before measuring

1. ⭐ **On a pull compositor, «quanto eroga» is not a question about the compositor.** The R32
   tables for Mutter and KWin measured *them*; here they will measure **our loop**. Whoever quotes the number
   must also quote the cadence we asked of it and the way we asked it.
2. ⭐ **The lever that seems to be there and does nothing comes back, under another name.** On KWin it was
   `KWIN_COMPOSE=O2`; here it is `overlay_cursor`, which *forces* software cursors instead of removing the
   cursor. **For every switch we find, we must write down what the opposite case would show**
   (§1.11) — and this time we know it before measuring, not after.
3. ⭐ **The most useful precedent can be a removal.** wlroots *removed* its own RDP backend
   in favour of an external client: it is the strongest confirmation that the REMOTIX architecture is the
   right one, and we would not have found it by reading the present code — only by looking for **who does it, and who has
   stopped**.
4. ⚠ **Bind to the protocols, not to the library.** XFCE is writing its own compositor in Rust
   on smithay, not on wlroots. Everything we write against `zwlr_screencopy`,
   `zwlr_virtual_pointer` and `zwlr_data_control` survives that change; everything that assumes
   *wlroots* does not.
5. ⭐ **A write that succeeds is not an applied configuration.** `xfconf-query` exits with zero
   even when the daemon has refused and restored the value, because the API is asynchronous and the local
   cache answers first. It is `LEZIONI.md` §1.9 moved from measurement to configuration: **a
   write that can be refused must be read back**, and this holds for every value that
   provisioning sets.
6. ⚠ **The dangerous environment variables are not the ones that are missing, but the ones that are inherited.**
   Garcon has a fallback for a missing `XDG_MENU_PREFIX`, and none for a wrong one; `XDG_CURRENT_DESKTOP`
   with a suffix makes the submenus disappear; `DISPLAY` makes GTK fall back to X11 silently. It is lesson
   §5 of `LEZIONI.md` — *whoever starts a session gives it their whole environment* — and on this
   desktop it bites in three different places.


<a id="lxqt"></a>

## LXQt on Wayland — code study, for phase 11

*Written on 8 August 2026, with ten parallel searches over the sources cloned at the Debian
Trixie versions. It is the project's seventh study, and the **fourth desktop** after GNOME, KDE and XFCE.*

> **The marks, and they count more than the sentences:**
>
> | | |
> |---|---|
> | **[R]** | read in the code, with `file:riga`. **It is not a measurement** |
> | **[R-pkg]** | read in the Debian package (`apt-cache`, `dpkg-deb -c`): it says what the distribution *ships*, which is a different thing from what the project *writes* |
> | **[M]** | measured |
> | **[?]** | deduction or hypothesis |
> | **[✗]** | verified absent, with the way it was searched for and a positive control |
>
> The detail is in the **ten reports** in `reference-lxqt/rapporti/`. Here is what is needed to
> decide.

---

### 1. In two minutes, and the line that counts more than any other

> ### ⛔ **On Debian Trixie, LXQt on Wayland does not exist as an installable session.**
>
> **[R-pkg]**, three independent proofs with a positive control:
>
> | | |
> |---|---|
> | `lxqt-wayland-session` **is not in Trixie** | `apt-cache policy` → no candidate; the `Packages` index lists **37** `lxqt-*` packages and not it (positive control: `lxqt-session` → 2.1.1-1, `labwc` → 0.8.3-1) |
> | **no LXQt package** installs a file in `/usr/share/wayland-sessions/` | the whole `wayland-sessions` of trixie/main has **10 entries** — labwc, phosh, plasma, sway, weston, **xfce-wayland**… **no LXQt**. LXQt appears only in `xsessions/` |
> | and the code itself says so | `lxqt-config-session` creates the «Wayland Settings» page **only if it finds the `startlxqtwayland` executable** (`sessionconfigwindow.cpp:65`), which is not on Trixie; and `lxqt-session` starts the window manager **only on xcb** (`lxqtmodman.cpp:82-83`) |
>
> It is not a refusal by Debian: it is a **delay**. The package exists in forky/sid at **0.3.1-1**,
> uploaded after the Trixie freeze.
>
> ⭐ **But the Wayland code is already shipped and working**: `lxqt-panel` 2.1.4 contains
> `libwmbackend_wlroots.so` **and** `libwmbackend_kwin_wayland.so` **[R-pkg]**. **Only the
> launcher is missing** — which is precisely the thing REMOTIX writes for itself, because we
> start the session. The missing piece is **a script**, not a feature.

**The compositor is `labwc`** — the same as XFCE — and the structure is **reversed with respect to X11**: it is
the compositor that launches the session (`labwc -C <dir> -S lxqt-session`), not the other way round
(`lxqt-wayland-session/startlxqtwayland.in:116` **[R]**). Logout comes for free from `-S`, as on
XFCE.

#### 1.1 The reuse account, which is the reason this study exists

| | Items | What |
|---|---|---|
| ✅ **full reuse** | **5 of 9** | capture, input, clipboard, resizing, audio |
| ⚙ **adaptation** | **3** | exit/logout (the D-Bus target changes), cursor (the cure is there but goes through another channel), power and lock (**none** of the levers paid for on GNOME/KDE/XFCE exists here) |
| ✍ **to be written** | **1, and it is not technical** | starting the session — because the package is not there |

⭐ **What LXQt adds on the compositor is almost nothing**, and it must be said clearly because it changes the
size of the phase: in the base case it is **the same labwc as XFCE**, and the pixels/keys/clipboard chapter is
§xfce **without changes**. In fact, **minus three traps**:

| XFCE trap | On LXQt |
|---|---|
| `xfsettingsd` **disables** new outputs and opens a dialog | **[✗]** no component speaks `zwlr_output_manager_v1` (only 2 lines in the whole tree, and they are strings recommending `kanshi`) |
| the panel **exits** if there are zero monitors | **[✗]** QtWayland always creates a **placeholder screen** (`qwaylanddisplay.cpp:402-412`): `screens().at(0)` is never out of range |
| the wallpaper key **is the connector name** | **[✗]** `[Desktop] Wallpaper` is single and global (`pcmanfm-qt/settings.cpp:243`): the output name is free |

⭐ **It is the easiest desktop of the four for live resizing** — and on resizing
**we are the only commander**, which was true neither on GNOME nor on KDE.

#### 1.2 And the five things that cost

| | |
|---|---|
| ⛔ **the session must be assembled by hand** | and with it `XDG_CURRENT_DESKTOP`, `XDG_SESSION_TYPE`, `XDG_MENU_PREFIX`, `XDG_CONFIG_DIRS`, `QT_QPA_PLATFORM`, labwc's `rc.xml` and the autostart |
| ⛔ **`XDG_CURRENT_DESKTOP` decides half of the panel** | the WM backend is chosen **by the variable's tokens**, case-sensitive, by score. Getting it wrong gives a desktop that is **alive and inert**, with a single `qWarning` |
| ⛔ **the autostart LXQt proposes turns the output off** | `swayidle -w timeout 300 "wlopm --off *"` (`configurations/labwc/autostart:31`): the twin of `xfce4-power-manager`, but at **5 minutes instead of 10** |
| ⛔ **the three cures already paid for do not apply** | `PowerManagement.Inhibit` **[✗] does not exist**; `LockCommand=/bin/false` here opens a **modal window**; `enableIdlenessWatcher=false` **is rewritten to `true`** by the daemon on first start |
| ⚠ **there is a clipboard roommate** | `qlipper`, a dependency of the `lxqt` metapackage, which **puts back the last item when the clipboard empties** — like klipper, but **with no marking and no frequency cap** |

#### 1.3 Step zero: who already does it

**[✗] Nobody does RDP on LXQt-Wayland, on any compositor.** Sharper than on XFCE, because on top of it
comes the fact that the session is not packaged. The competitor is **`xrdp` on X11**
(`/etc/xrdp/startwm.sh` → `Xsession` → `startlxqt`; `grep -ri wayland /etc/xrdp/` → **zero**
**[R-pkg]**).

⭐ **And LXQt appears in xrdp guides more than any other desktop for a reason that concerns us: it is
the one recommended when the remote machine is small.** That is, exactly our field.

⭐ **An unexpected, and important, precedent**: `lxqt-panel_wayland.desktop.in:14` declares
`X-KDE-Wayland-Interfaces=org_kde_plasma_window_management` under the comment *«Make KWin recognize
us as priviledged client»* **[R]**. It is the **fourth independent precedent** of the permission mechanism
we found on KDE — after KRdp, krfb and the portal — **and the only one outside Plasma**.

---

### 2. The map

| What | Where | Trixie version |
|---|---|---|
| the session | `reference-lxqt/lxqt-session/` | **2.1.1** |
| the panel | `lxqt-panel/` | **2.1.4** |
| settings, appearance, monitors | `lxqt-config/` | **2.1.1** |
| the desktop | `pcmanfm-qt/` 2.1.0, `libfm-qt/` 2.1.0 | |
| power, shortcuts, notifications, policykit | `lxqt-powermanagement/` 2.1.0, `lxqt-globalkeys/` 2.1.0, `lxqt-notificationd/` 2.1.1, `lxqt-policykit/` 2.1.0 | |
| libraries and Qt theme | `liblxqt/` 2.1.0, `libqtxdg/` 4.1.0, `lxqt-qtplugin/` 2.1.0, `lxqt-themes/` 2.1.0 | |
| the menu | `lxqt-menu-data/` 2.1.0 | |
| ⚠ **the Wayland launcher** | `lxqt-wayland-session/` | **0.4.1 — it is NOT the Trixie version** |
| the compositor and the protocols | `../REMOTIX/reference-xfce/` (labwc 0.8.3, wlroots 0.18.2, wlr-protocols, wayland-protocols 1.38) | |

⛔ **Beware of the `lxqt-wayland-session` clone**: it is **0.4.1** (May 2026) and requires **LXQt ≥
2.4.0** and a much newer labwc. **It is read as a statement of intentions, not copied**: its
configuration files are for compositors Trixie does not have. It is the only repository in the study
that does not match the machine.

---

### 3. The session: how to assemble what Debian does not ship

*Detail: `rapporti/01-sessione-lxqt.md`.*

#### 3.1 The shape

```
labwc -C <our dir> -S lxqt-session
```

The compositor is the parent; `lxqt-session` is the *primary client*: when it exits, labwc terminates. It is the
same shape as XFCE (`labwc --session xfce4-session`), so **the startup code is the same**.

#### 3.2 The environment — and this is where the risk concentrates

| Variable | Value | Why, and what happens if you get it wrong |
|---|---|---|
| ⭐ `XDG_CURRENT_DESKTOP` | **`LXQt:labwc:wlroots`** | the panel picks the WM backend **from the tokens, case-sensitive, by score** (`wlroots` 50, `labwc` 30 — `lxqtpanelapplication.cpp:206-270`). With bare `LXQt` it falls onto the **`dummy`** backend: empty taskbar, pager at one, everything inert, **a single `qWarning`**. ⛔ And the modules have `OnlyShowIn=LXQt;`: without the `LXQt` token the session is **alive with a black screen and zero messages** |
| `XDG_SESSION_TYPE` | `wayland` | it is not cosmetic: the panel picks the backend from there, **not** from `platformName()` (`:206-209`) |
| ⭐ `QT_QPA_PLATFORM` | **bare `wayland`** | **[✗]** no LXQt component sets it. With the list `wayland;xcb` Qt takes «il primo che carica» with **a single `qCWarning`**; with a single element, if the plugin is missing you get to `qFatal`. It is `LEZIONI.md` §1.8 closed in code |
| `XDG_CONFIG_DIRS` | **must contain `/usr/share`** | the LXQt defaults live in `/usr/share/lxqt/*.conf`. With the Debian default they are not found — and they vanish **silently** |
| `XDG_MENU_PREFIX` | `lxqt-` | **[✗] no hard-wired fallback** in libqtxdg, unlike garcon on XFCE. ✅ But the file `/etc/xdg/menus/lxqt-applications.menu` **exists** in `lxqt-menu-data` **[R-pkg]** |
| `LABWC_UPDATE_ACTIVATION_ENV` | `1` | as on XFCE: on the headless backend labwc **does not propagate** `WAYLAND_DISPLAY` to the bus |
| `XCURSOR_THEME` (+ `XCURSOR_SIZE`) | the transparent theme | §6.1 |
| ⛔ **NOT to be passed** | inherited `DISPLAY`, `WAYLAND_DISPLAY`, `QT_QPA_PLATFORM`, `SESSION_MANAGER` | see below |

⛔ **The fallback to `xcb` is worse than on KDE, and not «a bit worse»: it is a different session.** If Qt
picks xcb, `lxqt-session` **starts a second window manager**, may open a **modal dialog** for
choosing the WM and block the event loop for **30 seconds** (`lxqtmodman.cpp:82-83`, `:209-214`, `:237`);
it stops filtering the `X-LXQt-X11-Only` modules, turns on `setxkbmap`, `xrdb`, the udev watcher for
inputs **and the DRM one that launches `lxqt-config-monitor -l` at every display change** — that is **a
second commander of the resolution**.

#### 3.3 What is NOT needed, and they are three debts we do not pay

| | |
|---|---|
| ✅ **[✗] no `loginctl terminate-session`** | grep over `lxqt-session` and `liblxqt`, with a positive control that finds the XFCE one. **The double defence of §xfce §9.2 is not needed** |
| ✅ **[✗] no session client registration** | neither XSMP nor D-Bus: the «hostage of the logout» risk paid on KDE **does not exist**. And the logout consults no inhibitors, shows nothing, cannot be cancelled |
| ✅ **[✗] no session saving** | the XFCE `~/.cache/sessions/…` trap has no equivalent: there is nothing to delete |
| ✅ **[✗] no seat required** | `XDG_SEAT`/`XDG_VTNR`/`libsystemd` absent from all 17 repositories |
| ✅ **[✗] no priority groups** | the structural **eight seconds** of XFCE have no equivalent: the «desktop up» cap can be short |
| ✅ **the session bus** | **[✗] `dbus-run-session` appears nowhere**: `$XDG_RUNTIME_DIR/bus` is used. ⭐ **The decision left open in §xfce §9.7 closes itself here** |

⛔ **But `lxqt-session` is a subreaper** (`procreaper.cpp:56`) and at logout it sends `SIGTERM` to everything that
has its ppid (`:129`, `:191-198`). We are *above* it and we are safe — **but nothing of REMOTIX must be
started under `lxqt-session`**, because every orphan is reassigned to it.

#### 3.4 ⭐ Readiness can be read, better than on the other three

Signal **`moduleStateChanged(QString, bool)`** on `org.lxqt.session`, object `/LXQtSession`
(`sessiondbusadaptor.h:53`, `:57`): wait for `("lxqt-panel.desktop", true)`.

⚠ The **name on the bus** appears in the constructor (`sessionapplication.cpp:48`), so «the name is there» **does not
mean «desktop up»** — it is the same distinction that fooled us on KDE.

**The logout**: service, object and interface are all `org.lxqt.session` / `/LXQtSession`.
**[✗] No «I am leaving» signal** — the passive watch is `SIGCHLD` on labwc (the truth) plus
`NameOwnerChanged` (the early warning). To command it: `logout()`, **or `SIGTERM` to `lxqt-session`**,
which is the same thing. ⛔ Never `lxqt-leave --logout`: it opens a modal confirmation.

#### 3.5 ⚠ Three modal windows can stop an unattended session

1. `QMessageBox` if `dbus-update-activation-environment` does not start within 2 s (`sessionapplication.cpp:81-84`);
2. «Crash Report» after 5 crashes in 60 s (`lxqtmodman.cpp:330`);
3. ⛔ **the worst case**: an empty `compositor=` — **which is the stock default** — makes it start
   `lxqt-config-session` instead of the desktop. Socket, globals, capture and input would **all be
   green**, and on the screen there would be a configuration wizard.

⭐ **Hence the readiness check must be done on the bus, not on the pixels**: `org.lxqt.session` + the
panel signal. It is lesson §2.2 — *a bench that counts is not enough* — in preventive form.

---

### 4. The compositor: the matrix, and why there is no new code

*Detail: `rapporti/02-compositori-matrice.md`.*

LXQt declares **seven** compositors (`lxqt-wayland-session/README.md:5-14`); **Trixie packages
four**: labwc 0.8.3, kwin-wayland 6.3.6, wayfire 0.9.0, sway 1.10.1. Hyprland, niri and river
**[✗]** are not there.

| | labwc / sway / wayfire | kwin_wayland 6.3.6 |
|---|---|---|
| **Capture** | `zwlr_screencopy` v3 | `zkde_screencast` v5 |
| **Permission** | **none** | `.desktop` + `X-KDE-Wayland-Interfaces` |
| **Input** | `zwlr_virtual_pointer` v2 + `zwp_virtual_keyboard` v1 | libei (EIS over D-Bus) |
| **Clipboard** | `zwlr_data_control` **v2** | `zwlr_data_control` **v2** ✅ |
| **Resizing** | `set_custom_mode`, **no cap** | ⛔ **fixed** size with `--virtual` |

**One row out of eight in common between the two families** — and it is the clipboard, that is the file we already had.

⭐ **Verdict: zero new code, for all four.** Six compositors out of seven fall onto the wlroots module
of the XFCE phase; the seventh onto the KDE module.

**On the KWin case**, which would be «nothing to write»: the claim **holds but does not pay**, for
four reservations — the LXQt script plants `XDG_MENU_PREFIX=lxqt-` and the KWin branch **does not correct it**
(`startlxqtwayland.in:66`, `:125-142`), which according to §kde §3.3-bis could leave the service index
empty and **close the permission gate** [?, to be measured — ⚠ and a second reading
overturns it: `/etc/xdg/menus/lxqt-applications.menu` **exists** in `lxqt-menu-data` **[R-pkg]**,
so the index **should** get built]; it inherits the **fixed size** that labwc does not have; our
`.desktop` is needed anyway; and KWin without Plasma has never been measured.

⭐ **The indicated choice is labwc**: it is LXQt's own fallback, the first in the upstream `Depends`,
it has resizing without a cap and no permission.

#### 4.1 ⭐ The matrix, and the number that changes the meaning of the phase

If a desktop no longer implies a compositor, the product does not have «five desktops»: it has a **matrix**.

| | |
|---|---|
| realistic combinations on Trixie | **9** |
| covered today | **2** (22 %) |
| covered **for free** by the wlroots phase alone | **+5** |
| **total after the wlroots phase** | ⭐ **8 out of 9 — 89 %** |

**And LXQt brings four of them, all free.** ⚠ Reservation: wayfire vendors wlroots **0.17**, so its
«free» is **[?]** until that version is read.

#### 4.2 Detection: do not ask the desktop, look at the globals

`XDG_CURRENT_DESKTOP` **is written and not read**: the LXQt script builds it in **three different
forms** in the same file, says `wlroots` even for compositors that are not, and already gets the
capitalisation wrong in its own house.

⭐ **The solid criterion is to enumerate the globals** with a `wl_display_roundtrip` on the registry: there is no
ambiguity, because `zwlr_screencopy_manager_v1` and `zkde_screencast_unstable_v1` are **mutually
exclusive** across all of Trixie. It costs zero new lines — the registry connection already exists in
`kwin.c:451-495` — and it also serves a compositor not on the list.

---

### 5. What is reused without touching anything

| | |
|---|---|
| **Capture** | `zwlr_screencopy` on labwc: §xfce §4 **in full** |
| **Input** | `virtual-keyboard` + `virtual-pointer`: §xfce §7 **in full**, including the five traps |
| **Clipboard** | ✅ **`appunti_wlr.c` as it is**, and the reservation of §xfce §8 **falls**: `kwin_display_apri` **does not filter the socket by name** (`src/kwin.c:451-484`) — it takes `WAYLAND_DISPLAY` and failing that tries `wayland-0`…`wayland-9` |
| **Resizing** | `set_custom_mode`: **in full, and easier than on XFCE** (§7) |
| **Audio** | the PipeWire path does not depend on the desktop |

⭐ **The shortcuts do not bother us**: `lxqt-globalkeys` **[✗] does not run at all on Wayland** — it is not
the ambiguous case of the daemon that swallows keys without using them: `lxqt-session` **skips it by
construction** (`X-LXQt-X11-Only=true` + `lxqtmodman.cpp:106-112`), and it is pure Xlib, **zero
Wayland branches in 3 414 lines** (positive control: 60+ X11 lines). All its clients go through it via
D-Bus, so they are dead too.

⛔ **The compositor keybinds remain**, which are a **complete** list in a file we write
ourselves — and `W-l → lxqt-leave --lockscreen` is among the stock ones (`rc.xml:295-297`): it must be removed, or labwc
eats the key anyway (§xfce §7.5).

⚠ **Two input details that LXQt adds:**

1. **NumLock starts off** (`enableNumlock()` is behind the X11 gate, and `<numlock>` is commented out in
   `rc.xml`): the keypad comes out in arrow mode. Our remedy, by putting it in `mods_locked`;
2. the **keyboard layout**: `lxqt-config-input` **refuses to start on Wayland**, and in the
   code there is a `// FIXME: how to set keyboard layout in Wayland?`. The only way is
   `XKB_DEFAULT_LAYOUT` read by labwc, and **[✗] nobody reads `/etc/vconsole.conf`** on Trixie: **we
   write it ourselves, or `us` comes out**;
3. ✅ **repeat** is decided by labwc (25 Hz / 600 ms) and it applies it **explicitly to virtual
   keyboards too**: LXQt's `[Keyboard]` **[✗] does not reach the compositor**. Nothing to do;
4. ⚠ but `wheelScrollLines=3` in `lxqt.conf [Qt]` is applied **by Qt inside every application**: one
   notch of ours becomes **three lines**. The knob is there, not in our accumulator.

---

### 6. What is adapted

#### 6.1 ⭐ The cursor: the cure exists, but the channel is another one

**The good news**: on labwc the cursor of **Qt** applications is drawn by **the compositor**.
labwc exposes `wp_cursor_shape_manager_v1` and Qt 6.8 uses it **before** loading any theme
(`qwaylandinputdevice.cpp:230-236`), and on `set_shape` labwc uses its own `xcursor_manager`, that is the
theme of **`XCURSOR_THEME`**. ⇒ **a single lever covers compositor and Qt clients.**

⛔ **The three traps, all paid elsewhere in a different form:**

| | |
|---|---|
| `session.conf [Environment]` **is no use** | on Wayland labwc is the **parent**: `lxqt-session`'s variables arrive too late. And LXQt **deliberately removes** `XCURSOR_THEME` from there (`selectwnd.cpp:188-192`) |
| `~/.icons/default/index.theme` | `lxqt-config-appearance` writes `Inherits=<tema>` into it, and it is **Xcursor's fallback**: if our 1×1 theme does not load, a visible cursor reappears from there |
| Qt's fallback to the theme hint | outside labwc, Qt reads **only** `QPlatformTheme::MouseCursorTheme`, which `lxqt-qtplugin` takes from `session.conf [Mouse]` — with a **hard-wired `cursor_size` 16** that overrides `XCURSOR_SIZE`. ⇒ set **that key too**, which costs one line |

✅ And a difference in our favour compared with wlroots: if the theme fails **on the Qt side**, Qt does **not**
fall back to a visible theme (`qwaylanddisplay.cpp:1054-1064`). The only visible fallback left is the
wlroots one, already known.

#### 6.2 ⛔ Power and locking: none of the levers already paid for works here

| Lever paid for elsewhere | On LXQt |
|---|---|
| powerdevil's `AddInhibition` (KDE) | **[✗]** does not exist |
| `PowerManagement.Inhibit` (XFCE) | **[✗]** LXQt neither exposes nor consumes it: **zero occurrences**. The question «does the service have D-Bus activation?» **does not arise: there is no service** |
| `LockCommand=/bin/false` (XFCE) | ⛔ **here it opens a modal `QMessageBox`**: an exit ≠ 0 calls `reportLockProcessError()`. The only safe choices are **key absent/empty** or **`/bin/true`** |
| KIOSK (KDE) | **[✗]** does not exist |

✅ **But the danger is much smaller, because LXQt on Wayland is almost disarmed:**

- **[✗] `lxqt-powermanagement` has no lever that turns off an output**: the only one it knows is DPMS
  via XCB, locked inside two `if (platformName()=="xcb")` **with no `else` branch**;
- **[✗] the server does not go to sleep**: the idle actions are `-1` (nothing) and `doAction(-1)` is
  an empty branch;
- **[✗] «Switch user» does not exist in LXQt** (grep with positive control): **half of the requirement is already
  satisfied by the desktop**;
- ✅ the screen lock **is already inert**: `lock_command_wayland` is read **with no default** and no shipped
  file sets it.

⛔ **Two real dangers remain, and the first is not LXQt's:**

1. **the autostart that LXQt proposes for labwc** launches `swayidle -w timeout 300 "wlopm --off *"` — and
   `~/.config/labwc/` is copied **only once** (`if [ ! -d … ]`), so a wrong
   configuration is **permanent**;
2. ⛔ **if a locker is installed, the lock really succeeds**, because labwc implements
   `ext-session-lock-v1`. **New requirement: no `swaylock`/`waylock`/`hyprlock` in the image.**

⭐ **And there is a lever that does not depend on the desktop, and it is the best one**: labwc creates
`zwp_idle_inhibit_manager_v1` **unconditionally** (`idle.c:81`), and an inhibitor does
`wlr_idle_notifier_v1_set_inhibited(true)`, which **disarms every `ext-idle-notify` timer**. That is,
we turn off the watcher at the source, **whatever LXQt's configuration says**, without
asking anyone for anything. ⛔ It does not, however, stop a direct `set_mode(OFF)`: wayvnc's cure
(turn it back on before capturing) stays.

⚠ **And a configuration trap that is pure `LEZIONI.md` §1.9**: writing
`enableIdlenessWatcher=false` **is not enough** — the daemon **rewrites it to `true`** at first start
(`powermanagementd.cpp:112-113`). `runCheckLevel=1` is **also** needed.

#### 6.3 The dangerous entries

**[✗] No KIOSK, no `locked=`**: the entries must be **removed**, not locked. Three levers, all without
patches:

1. same-name `.desktop` files with `Hidden=true`/`NoDisplay=true` in `$XDG_DATA_HOME/applications/` for the seven
   `lxqt-leave` files;
2. **remove `fancymenu`** from the `plugins` key of `panel.conf` — it is the «Leave» button, and it is
   **unconditional, keyless, clickable even when the menu is not loaded** — or replace it with
   `mainmenu`, which in 2.1.4 has no power entries;
3. polkit `no` on logind, which **greys out** Suspend/Hibernate/Shutdown. ⛔ Exception: **«Lock screen» is
   never greyed out** — there is no `canLock()`.

⛔ **And the Debian default already has a dangerous stock entry**: `lxqt-branding-debian` ships a
`/etc/xdg/lxqt/panel.conf` with **`lxqt-leave.desktop` pinned in the quicklaunch** **[R-pkg]**.

⚠ `lxqt-policykit-agent` **starts on Wayland too** and does `show()` + `activateWindow()`: an
authentication dialog in an unattended session. It is **[?] a decision for the user**, for consistency with
the judgement given on KDE («le operazioni privilegiate nel terminale funzionano»).

✅ **Notifications** do not steal focus (`KeyboardInteractivityNone`) and are silenced with
`doNotDisturb=true`. ⛔ But `lxqt-leave` uses `KeyboardInteractivityExclusive`: **while it is open,
it grabs the keyboard exclusively**.

---

### 7. ✅ Hot resizing: here we are the only commander

*It is the item where LXQt is **better** than all three previous desktops.*

| | |
|---|---|
| **[✗] no component speaks `zwlr_output_manager_v1`** | only 2 lines in the whole tree, and they are strings recommending `kanshi` |
| `lxqt-config-monitor` goes through **KScreen** | which on Wayland picks the KWayland backend, which demands **KWin's** protocols — **[✗] absent in labwc**. `isReady()` false ⇒ plugin discarded |
| the only visible effect | a `QMessageBox` «Platform Unsupported… use kanshi» + `exit(1)` — **but only if the user opens the tool by hand**. It is hidden with a same-name `.desktop` `NoDisplay=true` |
| the DRM watcher that would relaunch the tool | is inside `if (isX11)`: **inert** |
| ⛔ **not to do** | setting `KSCREEN_BACKEND=QScreen`: the backend is valid but **read-only**, and `setConfig` **returns success** — that is an «Apply» that does not apply |

**And the Qt chain holds, verified line by line**: wlroots sends `logical_size` + `done`, Qt emits
`handleScreenGeometryChange`, and ⭐ **`QWaylandWindow::reset()` has only four callers, and
geometry is not among them**: no surface recreation, no flicker, no black
window. Windows are repositioned by **labwc**, which remembers the previous geometry; the panel listens to
`QScreen::geometryChanged` and puts itself back in place.

⛔ **But the prohibition of §xfce §6.1 gets stronger**: **destroying** the output makes Qt mount a
`QPlatformPlaceholderScreen` — and this applies to **all** applications, not only to the pieces of the
desktop. You resize; you do not destroy.

⚠ A single reservation, **[?] to be measured**: that labwc really generates an `output_layout.change` on
`set_custom_mode`, which is what starts the whole chain. And a defect declared upstream
(`lxqt-panel#2432`) says that **the panel does not follow the resize**: it is the first defect the user
would see.

✅ **Scale and DPI: no trap.** LXQt **[✗]** does not handle DPI; at `scale=1` text is 1:1 and
the 0×0 `physical_size` of our headless output is irrelevant, because Qt on Wayland returns
**a fixed 96 dpi**. At 4K the text is sharp but **small**: the clean lever is the **font** in
`lxqt.conf [Qt]`, not `QT_SCALE_FACTOR` (which does not touch GTK).

✅ **Decorations**: a single bar and no flash — Qt sends `unset_mode`, labwc decides per
`rc.xml`, and LXQt ships `<decoration>server</decoration>`. **Touch neither that key nor
`QT_WAYLAND_DISABLE_WINDOWDECORATION`.**

---

### 8. The clipboard, and the roommate

*Detail: `rapporti/06-appunti-qt.md`.*

✅ **`appunti_wlr.c` works as it is, on labwc and on KWin.** The reservation opened by §xfce §8 is
closed **positively**.

⚠ **But LXQt has a roommate that XFCE did not have: `qlipper`**, which the `lxqt` metapackage pulls in as a
dependency (`qlipper | clipit | xfce4-clipman`) and `lxqt-core` recommends. It autostarts from
`/etc/xdg/autostart/`, does **not** have `X-LXQt-X11-Only`, and **puts back the last item when the clipboard
is emptied** — like klipper, but **without marking and without a rate cap** (klipper at least had
10/s).

⭐ **On Wayland it is almost inert, and the «almost» depends on a `Recommends`**: qlipper is Qt5 and uses only
`QClipboard`, so without focus it neither sees nor writes. **But** in an image built with
`--no-install-recommends` the `qtwayland5` plugin is missing, qlipper falls back to xcb, and **via Xwayland
it is reborn as a full roommate**. ⚠ **The bench must declare which of the two cases it is measuring** — it is
exactly the shape of lesson §2.3-bis.

**Three things about Qt6 that change our clipboard code:**

| | |
|---|---|
| ⛔ **never `text/markdown` first** | Qt6 **pastes markdown** if it is the first format offered (`qwidgettextcontrol.cpp:2721-2726`) |
| `text/plain;charset=utf-8` | is presented to the application **as `text/plain`**: we offer only UTF-8 |
| ⚠ **Qt's read cap is 1 second** | against our 5: on a slow network the user sees **a silent paste** while our log declares a successful transfer. It is lesson §1.7 — *verify from the side that must receive* |

✅ **The primary selection can be ignored** (a single use in the whole tree, and **[✗]** no
configuration that merges it with the clipboard). ✅ The **Xwayland** bridge is identical to XFCE, free in both
directions. ✅ And on LXQt+KWin **klipper is not there**: its `.desktop` is `Exec=/usr/bin/false`, it is a
library of plasmashell.

---

### 9. The configuration: where it is written, and the tension to close on the bench

⛔ **`LXQt::Settings` writes into the user's home merely on construction** (`__userfile__=true` +
`sync()`, `lxqtsettings.cpp:53-59`), and **[✗] there exists** neither a `SystemScope` nor an equivalent of
xfconf's `locked=`. ✅ On the other hand there is a `QFileSystemWatcher`: unlike `xfconfd`, LXQt
**reloads hot**.

> #### ⚠ A tension between the reports, left open on purpose
>
> | Who | What it says |
> |---|---|
> | `rapporti/03` | system defaults in **`/etc/xdg/lxqt/*.conf`** work: `QSettings("lxqt", modulo)` falls back key by key, **and it is the mechanism by which Debian customises LXQt** (`lxqt-branding-debian`) |
> | `rapporti/04` and `rapporti/05` | the system path is **only one**, the one fixed when Qt was compiled, and the LXQt files are installed in **`/usr/share/lxqt/`** — so `XDG_CONFIG_DIRS` is needed, and the only safe way is an **ephemeral `XDG_CONFIG_HOME`** |
>
> **The two things can coexist** — `QSettings` reads `XDG_CONFIG_DIRS`, whose default is
> `/etc/xdg`, and Debian can install in both places. ⛔ **But which path wins on our
> machine is a measurement, not a reading**, and it is one of those that, if taken for granted, cost an
> afternoon: it is precisely the shape of `LEZIONI.md` §1.9. **Measurement M6.**

⭐ **The menu has the same defect as garcon, made worse**: if the `.menu` file does not exist,
`addWatchPath()` is **never** called ⇒ dead menu **for the life of the process**, the plugin does not
retry, and the remote user gets a **modal `QMessageBox`** during panel startup. ✅ But
**[✗] no on-disk cache** (`USE_MENU_CACHE=OFF`) — the KDE defect, the index built empty
that stays empty, **cannot happen on disk here**; and **[✗]** the XFCE submenu defect is not
there, because directories are never filtered on the environment.

⚠ **Two fragile dependencies to keep an eye on**: `qt6-wayland` is only a `Recommends` of `libqt6gui6`
— while **the library** `libqt6waylandclient6` is a hard dependency of `lxqt-panel`, so **you can
have the library without the plugin, with apt happy**; and `lxqt-qtplugin` depends on
`qt6-base-private-abi (= 6.8.2)`, **exact equality**: a Qt update turns it off, and the
session starts anyway **with a different look**.

---

### 10. The measurement plan

*The first two decide whether the phase exists; the others are in the order in which they bite.*

| # | The measurement | Why it is there |
|---|---|---|
| **M1** | ⭐ an LXQt-Wayland session **assembled by hand** really starts: `labwc -S lxqt-session` + the six variables of §3.2 | it is the «to be written» item, and on Trixie it has no precedent: nobody has ever installed it from a package |
| **M2** | the readiness check is **on the bus** (`org.lxqt.session` + `moduleStateChanged`) and tells the desktop from the **wizard** of §3.5 | the case where everything is green and on the screen there is something else |
| **M3** | ⭐ `set_custom_mode` with live capture: do panel, desktop and Qt applications follow? | §7, and the `lxqt-panel#2432` defect says no |
| **M4** | the transparent cursor theme covers **compositor and Qt clients**, and `~/.icons/default/index.theme` does not override it | §6.1: three channels, and it takes only one left open |
| **M5** | the `zwp_idle_inhibit` inhibition holds, and **nobody** turns off the output in 10 minutes | §6.2, autostart included |
| **M6** | ⭐ **which configuration path wins**: `/etc/xdg/lxqt/` or `/usr/share/lxqt/` — and every value written **reads back** | the box of §9, and lesson §1.9 |
| **M7** | `appunti_wlr.c` against labwc, **with and without** qlipper alive | §8: two cases, and both must be declared |
| **M8** | **deliberately broken** test: wrong `XDG_CURRENT_DESKTOP`, and then inherited `DISPLAY` | ⭐ learn **how to read the fault** before meeting it at the user's. They are the two defects that give «session alive and inert» with a single `qWarning` |

---

### 11. The lessons this desktop adds

1. ⭐ **The recipe lacks a step zero-bis**: *«does this desktop, on this distribution, have a
   Wayland session?»* — two commands (`apt-cache policy`, and looking in `/usr/share/wayland-sessions/`).
   Here they would have changed the phase **before it began**, and instead we discovered it at the second
   report out of ten. The existing step zero asks *«who does it in the world?»*; this one asks **«does it exist
   on the machine we have?»**, and it is further upstream.
2. ⭐ **And a question 0 to the fourteen**: *«does this desktop have a compositor, or a list of them?»*
   For Mutter, KWin and labwc the answer was a single one; for LXQt there are **seven**, and it changes the shape of the
   answer to all the others — because the questions must be asked to the compositor, not to the desktop.
3. ⚠ **An absent package is not an absent feature.** LXQt's Wayland code is compiled and
   shipped: what is missing is **the launcher**. Had we deduced «LXQt does not do Wayland» from `apt-cache policy`
   we would have skipped a desktop that is instead **the easiest of the four**.
4. ⚠ **The cloned version must be compared with the installed one, always.** Our
   `lxqt-wayland-session` is **0.4.1** and requires LXQt 2.4: we were about to study code that does not run
   on Trixie. For the other sixteen repositories the versions match, and this is the only one that would have
   lied.
5. ⭐ **The fourth desktop confirms that the right axis is the compositor, not the desktop** — which
   `SPECIFICA.md` §3.8 already said, but now it has a number: **8 combinations out of 9 covered after the wlroots
   phase alone**, and four of those LXQt brings without a line.


<a id="cinnamon"></a>

## Cinnamon and Muffin — code study, for the fifth desktop

*Written on 9 August 2026, on `muffin` and `cinnamon` **6.7.4** (clones from the same day).*

> ### ⛔ Everything that follows is `[R]`. Nothing is measured.
>
> This study was done **by reading the code**, and it is worth what a reading is worth: it says what
> the compositor *can* do, not what it *does* on our machine. It is the lesson that
> `LEZIONI.md` §1.11 and the box of §3 already paid for on KDE — where the reading said GPU and
> the first measurement said software, and the code was right **but only after the measurement
> had been redone**.
>
> The negative searches in this document (*«X non esiste»*) were done with the tool
> **certified on Mutter before use**: the first search looked in `src/`, did not find
> `RecordVirtual` even in Mutter — where it is — because recent Mutter keeps the XMLs in
> `data/dbus-interfaces/`. With the correct path the positive control passes, and only then does
> the absence in Muffin mean something. It is `LEZIONI.md` §1.9, caught in the act.

---

### 1. In two minutes

**Cinnamon is to Muffin exactly what gnome-shell is to Mutter**: the `cinnamon` binary *is* the
compositor — it calls `meta_get_option_context()`, `meta_plugin_manager_set_plugin_type()`,
`meta_init()` and `meta_run()` (`cinnamon/src/main.c:327-418`). It is not an analogy: it is the same
architecture, with the names changed.

Hence the good news and the bad, which are the same thing seen from two sides.

⭐ **The good**: half of §gnome transfers without translating. `org.cinnamon.Muffin.ScreenCast`
and `org.cinnamon.Muffin.RemoteDesktop` are Mutter's interfaces renamed, capture goes through
PipeWire as there, and **there is no permission gate** — `check_permission()` only checks
that the caller is the same one that created the session (`meta-screen-cast-session.c:196-201`),
exactly like Mutter and unlike KWin.

⛔ **The bad**: the fork split from Mutter's *backend* quite a few years ago, and three things that
REMOTIX takes for granted **are not there at all**.

| We look for | In Mutter | In Muffin 6.7.4 |
|---|---|---|
| `RecordVirtual` — creating a virtual screen | ✅ `data/dbus-interfaces/…ScreenCast.xml` | ⛔ **0 files** in the whole tree |
| `virtual_monitor` — the virtual monitor in the backend | ✅ 22 occurrences in `meta-monitor-manager.c` | ⛔ **0 files** |
| `ConnectToEIS` — input via libei | ✅ `…RemoteDesktop.xml`, `…InputCapture.xml` | ⛔ **0 files** |
| `EnableClipboard` — the remote session's clipboard | ✅ `…RemoteDesktop.xml` | ⛔ **0 files** |
| a *headless* backend | ✅ mode of the native backend | ⛔ `headless` appears **only in `src/tests/`** |

And the paradox that explains everything: **Muffin's Wayland protocols are thoroughly up to date** —
`cursor-shape`, `single-pixel-buffer`, `xdg-dialog`, `xdg-toplevel-icon`, `xdg-toplevel-tag`,
`pointer-warp`, stuff from 2024-2025. Mint keeps pace on the *client* side of Wayland and **has never
ported the evolution of Mutter's remote backend**. The result is a modern compositor
with a remote desktop API frozen at roughly Mutter 41.

**The provisional verdict**: Cinnamon is not excluded, but **it cannot be served with the code we
have**, and its feasibility depends on a single measurement, described in §3.3. Until that one is
done, every judgement is `[?]`.

---

### 2. The map

| Where | What |
|---|---|
| `muffin/src/backends/` | the part we care about, twin of Mutter's |
| `muffin/src/org.cinnamon.Muffin.{ScreenCast,RemoteDesktop,DisplayConfig,IdleMonitor}.xml` | the D-Bus interfaces — ⚠ still in `src/`, whereas Mutter moved them to `data/dbus-interfaces/` |
| `muffin/src/backends/meta-monitor-manager-dummy.c` | ⭐ **the piece that decides everything**, see §3 |
| `muffin/src/backends/native/` | the KMS backend |
| `muffin/src/backends/x11/nested/` | the backend nested in X11 |
| `cinnamon/src/main.c` | the plugin that *is* the desktop |
| `cinnamon/cinnamon-wayland.session.in` | the session |

---

### 3. ⛔ The deciding question: the virtual screen

It is question 5 of `LEZIONI.md` §3, and it is the one that cost the most of all on KDE.

#### 3.1 Mutter's way does not exist

`org.cinnamon.Muffin.ScreenCast` exposes **only two recording methods**:

```
RecordMonitor (connector, properties) → stream_path
RecordWindow  (properties)            → stream_path
```

No `RecordVirtual`, no `RecordArea`. And it is not an XML that lagged behind the code:
`virtual_monitor` appears in **no file** of the tree, XML included.

So the `gnome-remote-desktop` road — *I create a screen that does not exist and capture on it*
— **is not there** on Cinnamon.

#### 3.2 The three backends, and why none is headless

`calculate_compositor_configuration()` (`muffin/src/core/main.c:434-496`) picks one of three:

| Option | Backend | What it needs |
|---|---|---|
| `--wayland` / `--display-server` | `META_TYPE_BACKEND_NATIVE` | a DRM device with a **real** output |
| `--nested` | `META_TYPE_BACKEND_X11_NESTED` | an X server to nest in |
| (none) | X11 compositing manager | an X server |

**There is no `--headless` and there is no `--virtual-monitor`.** The native backend does not even have
the mode enumeration that in Mutter distinguishes `DEFAULT` from `HEADLESS`.

#### 3.3 ⭐ But there is a dummy monitor, and two environment variables that drive it

It is the piece that saves the study, and it is the reason Cinnamon must not be declared out of scope.

`meta_backend_create_monitor_manager()` (`muffin/src/backends/meta-backend.c:804-812`):

```c
static MetaMonitorManager *
meta_backend_create_monitor_manager (MetaBackend *backend, GError **error)
{
  if (g_getenv ("META_DUMMY_MONITORS"))
    return g_object_new (META_TYPE_MONITOR_MANAGER_DUMMY, NULL);

  return META_BACKEND_GET_CLASS (backend)->create_monitor_manager (backend, error);
}
```

⭐ **That check sits in the base class, before the virtual call**: `META_DUMMY_MONITORS`
overrides the choice of **any** backend, native included.

And the size of that fake screen is dictated from outside
(`meta-monitor-manager-dummy.c:148-175`, `:403-431`):

| Variable | Effect |
|---|---|
| `MUFFIN_DEBUG_DUMMY_MODE_SPECS` | the modes, like `1920x1080@60`, several separated by `:` |
| `MUFFIN_DEBUG_NUM_DUMMY_MONITORS` | how many screens |
| `MUFFIN_DEBUG_DUMMY_MONITOR_SCALES` | the scales |
| `MUFFIN_DEBUG_TILED_DUMMY_MONITORS` | tiled screens |

**It is the functional equivalent of KWin's `--virtual --width W --height H`**: the desktop size
is decided **at compositor start** and no longer changes in a live session — which is exactly the
KDE constraint, and which the canvas model of `DECISIONI.md` §5.0 already absorbs.

#### 3.4 ⛔ The two roads, and which one to measure first

**Road (A) — native + dummy monitor.** `META_DUMMY_MONITORS=1
MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60 cinnamon --wayland --replace`.
If it holds, Cinnamon runs **without X and without a monitor**, and the cost for REMOTIX collapses.

⚠ **But it is precisely the kind of deduction that `LEZIONI.md` §1.11 forbids taking for granted.** That
the monitor manager is fake does not say the *renderer* is: the native backend draws via
KMS and wants CRTCs to present on, and with invented screens those CRTCs are not there. It may
work, it may fail at startup, and **it may work while delivering zero frames** — which is the
worst way, because it looks like a success.

**Road (B) — nested in Xvfb.** `--nested` uses the dummy monitor **by construction**
(`meta-backend-x11-nested.c:57-60`): it is its only implementation of `create_monitor_manager`.
So (B) almost certainly works, at the price of one more X server in the stack and,
probably, of **software GL** (llvmpipe) — that is, the whole desktop drawn on the CPU, which
`LEZIONI.md` §3 question 4 considers decisive for saying whether a desktop is servable on a
server machine.

> ### The plan: (A) is measured, and (B) is the fallback
>
> (A) is the prize and (B) is the safety net. **The measurement is done in the order
> (A) → (B)**, and (A) is not declared successful because the process stays up: it is declared
> successful when `misura-cattura` (in `fondamenta/banchi/banco-compositori/`) counts frames on a
> declared, always-moving scene. It is `LEZIONI.md` §1.1 and §3.2 of `CODER.md`.

---

### 4. Capture: the part that works

**Fully implemented**, and with the same structure as Mutter:
`meta-screen-cast-monitor-stream-src.c`, `meta-screen-cast-window-stream-src.c`,
`handle_record_monitor()` at `meta-screen-cast-session.c:299`.

✅ **No gate.** `check_permission()` compares the D-Bus name of the caller with the one that
created the session — it is an ownership check, not an authorisation check. No polkit, no
portal, no field in a `.desktop` file. On this Cinnamon sides with GNOME and wlroots, **not**
with KDE.

`[?]` **What cannot be read**: how many frames it delivers, whether the buffer arrives already
drawn, whether the cursor ends up inside the image, what resolution costs. On Mutter it was
37 per second `[M]`; on Muffin **there is no reason to assume the same number**, because the
rendering path is what changed the most between the two — and that is exactly the deduction
that §1.11 forbids.

---

### 5. Input: a step back of two years

`org.cinnamon.Muffin.RemoteDesktop` exposes the old notify methods:

```
NotifyKeyboardKeycode · NotifyKeyboardKeysym
NotifyPointerButton · NotifyPointerAxis · NotifyPointerAxisDiscrete
NotifyPointerMotionRelative · NotifyPointerMotionAbsolute
NotifyTouchDown · NotifyTouchMotion · NotifyTouchUp
```

⛔ **No `ConnectToEIS`**, hence **no libei** — and `fondamenta/remotix-c/src/input.c` (906 lines) is
written for libei, decided on 4 August 2025 when closing phase 3 of v1.

The three consequences:

1. **a second input path is needed**, the D-Bus one, which v1 had written *before* moving
   to libei and which did not survive in the current code;
2. ⭐ **`NotifyKeyboardKeysym` exists**, and it is worth noting in light of `DECISIONI.md`
   §5-bis.6: here the *symbol* can be injected directly, without looking for which key
   produces it. It does not change the decision — the rule stays «le lettere viaggiano come lettere» — but on
   Cinnamon the server side costs less;
3. ⚠ **and there is `zwp_virtual_keyboard_v1`** among the Wayland protocols, which would be a third road.
   `[?]` To be evaluated only if the second proved insufficient: §0.1 of `DECISIONI.md` says not
   to collect paths.

`[?]` **Not read, and it must be read before writing**: whether `NotifyPointerMotionAbsolute` accepts a
reference to the *stream* as on Mutter, and how it behaves with the dummy monitor.

---

### 6. ⛔ The clipboard: here there is no road at all

It is the worst hole, and it has no obvious fallback.

| Way | On Cinnamon |
|---|---|
| `EnableClipboard` on the RemoteDesktop object (GNOME's way) | ⛔ **0 occurrences**: the API predates the addition of the clipboard in Mutter |
| `zwlr_data_control_manager_v1` (the way of KDE, XFCE and LXQt) | ⛔ **absent** from Muffin's protocols |
| `ext_data_control_v1` | ⛔ absent |

So **neither of the two files we have is of use**: neither `appunti_mutter.c` (450 lines), nor
`appunti_wlr.c` (796), which together cover all four other desktops.

`[?]` **The remaining ways, all to be verified and none pleasant**: write the ordinary `wl_data_device`
client — but the Wayland clipboard requires focus, and an unattended session does not
have it; go through XWayland; or contribute upstream. **The third is probably the only sensible one**, and
it is the same conclusion that §kde §8.2 had reached for resizing.

⚠ To be taken into account in the «Cinnamon dentro o fuori» decision: `DECISIONI.md` §5-ter puts the
bidirectional clipboard among the promised features. **On Cinnamon today it is not servable.**

---

### 7. What transfers from §gnome, and what does not

| Topic | Does it transfer? |
|---|---|
| the ScreenCast/PipeWire architecture | ✅ **yes, almost literally** |
| the absence of a permission gate | ✅ yes |
| the D-Bus session life cycle | ✅ probably `[?]` |
| **revocation on screen lock** (`inhibit_remote_access`) | `[?]` **to be verified**, and it matters: if it is there, the same cure as `DECISIONI.md` §4.3 applies |
| `RecordVirtual` and the virtual monitor | ⛔ no, they do not exist |
| libei and `ConnectToEIS` | ⛔ no |
| the clipboard | ⛔ no |
| lockdown via `org.gnome.desktop.lockdown` | `[?]` Cinnamon has its own settings tree |

---

### 8. The fourteen questions of `LEZIONI.md` §3, Cinnamon column

| # | Question | Cinnamon / Muffin 6.7.4 |
|---|---|---|
| 1 | How is capture requested without a portal? | ✅ D-Bus `org.cinnamon.Muffin.ScreenCast` — twin of Mutter `[R]` |
| 2 | Does it push frames or have them pulled? | ✅ pushes, PipeWire `[R]` |
| 3 | Is it behind a permission? | ✅ **no** — only an ownership check `[R]` |
| 4 | Without a monitor, does it draw on the GPU? | ⛔ `[?]` **the deciding question** — see §3.4. On road (B) almost certainly **no** |
| 5 | Can a virtual screen of the wanted size be requested? | ⛔ **no** via protocol; ⭐ **yes** via `META_DUMMY_MONITORS` + `MUFFIN_DEBUG_DUMMY_MODE_SPECS`, at startup `[R]` |
| 6 | How many frames does it deliver? | `[?]` **not deducible from Mutter** |
| 7 | How does the declared rate behave? | `[?]` |
| 8 | Whole frames or «diff»? | `[?]` |
| 9 | Does the buffer arrive already drawn? | `[?]` |
| 10 | What does resolution cost? | `[?]` |
| 11 | What does colour depth cost? | `[?]` |
| 12-bis | Is the cursor inside the captured image? | `[?]` — and with `DECISIONI.md` §5-bis.2 knowing it is **mandatory** |
| 13 | Can a virtual screen be resized live? | ⛔ **no** `[R]`: the size is in the environment at startup, as on KDE |
| 14 | Whose is the clipboard? | ⛔ **nobody reachable's** — see §6 |

**Eleven questions out of fourteen remain `[?]`**, against the eleven out of eleven that the KDE study
had closed by reading. It is not laziness in the study: it is that on KDE the answers were in the code,
and here the three that matter are in an execution.

---

### 9. The measurement plan, in order

The minimum to decide «dentro o fuori». It needs a machine with Cinnamon 6.7 and the benches of
`fondamenta/banchi/banco-compositori/`.

| # | What | How it is declared successful |
|---|---|---|
| **M1** | road (A): `META_DUMMY_MONITORS=1 MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60 cinnamon --wayland` from SSH, without a monitor | the compositor stays up **and** `RecordMonitor` opens a stream **and** `misura-cattura` counts frames > 0 on a moving scene. Three conditions, not one |
| **M2** | if M1 fails: road (B), `--nested` inside Xvfb | same |
| **M3** | the frames per second delivered, with a declared scene | the number, comparable with Mutter 37 / KWin 60 / wlroots 61 |
| **M4** | does it render on the GPU or in software? | ⚠ **not** «it opened a render node» (§1.11): look at the buffer type the stream manages to offer, **after** having asked for DMA-BUF |
| **M5** | is the cursor inside the image? | look at a frame |
| **M6** | does screen lock revoke the capture, as on GNOME? | lock and watch whether the stream dies |

⛔ **M1 is not declared successful because the process did not die.** It is error form E1: a
necessary condition taken as sufficient.

---

### 10. The bill for REMOTIX

**What is reused**, if M1 or M2 pass: the capture structure (`cattura.c`), the D-Bus session
cycle, and the canvas model of `DECISIONI.md` §5.0 — which already absorbs the constraint
«la misura si decide all'avvio», because it absorbed it for KDE.

**What must be written new**, and it is not little:

| | Cost |
|---|---|
| a `cinnamon.c` next to `mutter.c` and `kwin.c` | medium — it is Mutter with other names |
| **a second input path**, D-Bus instead of libei | ⚠ **high**: it is phase 4 of v1 redone |
| **the clipboard**, which today has no road | ⛔ **open** — see §6 |

**The verdict, declared as provisional:** Cinnamon is the desktop that costs **the most of all** among
the five, and its two difficulties — input and clipboard — are not reading difficulties but
features missing upstream. It must not be declared out of scope, because M1 could change the
bill; but it must be put **last**, after the other four work, and the decision must be taken
on the measurements of §9 and not on this document.

⚠ **And if M1 and M2 both failed**, Cinnamon is not servable at all — not through a shortcoming of ours,
but because a compositor that cannot draw without a screen cannot serve a
remote session. In that case the entry is closed, with the measurement next to it.


---

# Part III — Those who do our same job


<a id="gnome-remote-desktop"></a>

## gnome-remote-desktop — study of the code and the features

Analysis carried out on the original source code, cloned from `gitlab.gnome.org/GNOME/gnome-remote-desktop`:

- **51.alpha** (commit `038caa60`, 9 July 2026) — development branch, used as the main reference
- **48.2** — the version that comes with GNOME 48, that is the one of **Debian Trixie**, the runtime
  platform of REMOTIX. The differences from 51 are in §17

Size: **68 730 lines of C** in ~200 files, plus the D-Bus interface XMLs and the shaders.

Why this document exists: the REMOTIX specification cites `gnome-remote-desktop` every time a
problem was solved (§5.4, §5.8, §5.10, open question no.9), and every time it consulted it in pieces.
The method lesson written in §5.4 — *«studiare il riferimento viene prima di ipotizzare»* — asks
that the reference be studied **once and in full**. §18 gathers the bill: what it
confirms of REMOTIX's decisions, what it contradicts, and what is worth copying.

> **And since 3 August 2026 it matters much more.** With the constraints set by the user — **C language** and
> **FreeRDP 3** (§8-bis of `SPECIFICA.md`) — REMOTIX and `gnome-remote-desktop` share language,
> RDP library, compositor and client. What follows is no longer comparison material: it is code
> that is readable and, where needed, transferable.

---

### 1. What it is

The remote desktop server of the GNOME project. It is not a desktop and it is not a compositor: **it talks to the
compositor**, exactly like REMOTIX. Two protocol backends, **RDP** (default, on FreeRDP 3)
and **VNC** (optional, on LibVNCServer, disabled by default in the build).

The building blocks are the same ones REMOTIX chose: **PipeWire** for the pixels, **libei** for input,
**Mutter's RemoteDesktop API** for high-level management.

Licence GPL v2 or later. Main authors: Jonas Ådahl (architecture, session) and Pascal Nowack
(all the bulk of the RDP backend).

---

### 2. The four operating modes

They are the load-bearing structure of the whole program: a single executable, four `GrdRuntimeMode`
(`grd-daemon.c:1198`), each with its own daemon class and its own settings class.

| Mode | Option | Class | Bus | What it is for |
|---|---|---|---|---|
| `SCREEN_SHARE` | *(none)* | `GrdDaemonUser` | session | Remote assistance: attaches to the already active session of whoever sits in front |
| `HEADLESS` | `--headless` | `GrdDaemonUser` | session | Single user, screenless graphical session started separately |
| `SYSTEM` | `--system` | `GrdDaemonSystem` | **system** | Multi-user remote access: acts as doorkeeper in front of GDM |
| `HANDOVER` | `--handover` | `GrdDaemonHandover` | session | The process that receives the connection handed over by `SYSTEM` mode |

Corresponding systemd units: `gnome-remote-desktop.service` (user, for screen share),
`gnome-remote-desktop-headless.service` (user), `gnome-remote-desktop.service` (system).

**The mode that resembles REMOTIX is `HEADLESS`**: a single session, a single user, the server runs
inside the session. The other three solve problems that REMOTIX put out of scope (§4.2 of the
specification: multi-tenancy and administration).

#### 2.1 The handover with GDM (`SYSTEM` → `HANDOVER`)

It is the mechanism that the REMOTIX specification cites in §5.6 as *«quel passaggio esiste perché
gnome-remote-desktop deve agganciarsi alla schermata di accesso»*. The code confirms it: it all lives in
`grd-daemon-system.c` (1520 lines) and `grd-daemon-handover.c` (911 lines), and it is the most
complicated part of the whole program.

How it works, in short:

1. the system daemon runs as the dedicated user `gnome-remote-desktop`, on the **system bus**, and
   listens on 3389;
2. when a connection arrives it **peeks at the first bytes of the socket** (`grd-rdp-routing-token.c`)
   looking for the `Cookie: msts=` prefix of the Routing Token, without consuming them — with a cap of 2
   seconds;
3. if the token is not there, it is a new client: it authenticates against a system credential, and through
   `org.gnome.DisplayManager.RemoteDisplayFactory` asks GDM to create a login session;
4. that session starts a second `gnome-remote-desktop --handover`, which exposes
   `org.gnome.RemoteDesktop.Rdp.Handover` on the session bus;
5. the system daemon sends the client a **Server Redirection PDU** (`grd_session_rdp_send_server_redirection`)
   with routing token, credentials and certificate of the target;
6. the client reconnects, this time with the token; the system daemon recognises the token and **hands
   the socket** to the handover process, which serves the session.

The security level of the second connection is **RDSTLS** (`FreeRDP_RdstlsSecurity = TRUE`,
`grd-session-rdp.c:1547`) — that is, precisely the one xrdp has in its table but does not implement.

For REMOTIX this chapter is **entirely out of scope**, but it should be read once because it explains why
the rest of the program is made the way it is.

---

### 3. Process architecture

A single main executable, `gnome-remote-desktop-daemon` (in `libexecdir`), plus three utilities:

| Binary | Role |
|---|---|
| `gnome-remote-desktop-daemon` | The real server, in all four modes |
| `grdctl` | Command-line configuration (gsettings + credentials) |
| `gnome-remote-desktop-configuration-daemon` | Exposes the configuration on D-Bus for the Settings panel |
| `gnome-remote-desktop-enable-service` | Enables the system unit going through polkit |

**Names on the bus** (`grd-private.h`): `org.gnome.RemoteDesktop.User`, `.Headless`, `.Handover` on the session
bus; `org.gnome.RemoteDesktop` on the system bus.

**Threads** — there are four families, and the split matters because it is the same one REMOTIX had to
invent (§5.7 rule 7, §5.8 rule 3):

| Thread | Who creates it | What it does |
|---|---|---|
| main (default `GMainContext`) | GLib | D-Bus, logind, session life cycle, layout manager |
| **socket** (one per RDP session) | `grd_session_rdp_new` | `WaitForMultipleObjects` on the FreeRDP handles, reads the protocol |
| **graphics** (one per session) | `grd_rdp_renderer_start` | private `GMainContext`: encoding, sending EGFX frames |
| **EGL** (one per process) | `GrdContext` | All GL/EGL operations, which must stay on a single thread |
| PipeWire (one per stream) | `pw_context` | Capture |

The graphics thread has **its own `GMainContext`** (`renderer->graphics_context`) and all graphics
sources attach to it explicitly. It is the disciplined equivalent of what REMOTIX obtains with
Tokio tasks.

---

### 4. Dependencies

Always mandatory: glib ≥ 2.75, gio, **libpipewire ≥ 1.2**, **libei ≥ 1.3.901**, cairo, libdrm,
epoxy, xkbcommon ≥ 1.0, libnotify, libsecret, **krb5**, **tss2** (TPM 2.0), libsystemd (optional but
necessary for `SYSTEM`/`HANDOVER`).

For the RDP backend: **freerdp3 ≥ 3.22**, winpr3, freerdp-server3, **libva** + libva-drm, **vulkan ≥ 1.2**,
**ffnvcodec ≥ 11.1.5** (NVENC), **fdk-aac**, **opus**, **fuse3 ≥ 3.9.1**, polkit ≥ 122, and at build time
`glslc` + `spirv-opt` for the SPIR-V shaders.

Worth noting for REMOTIX: **no ffmpeg**, **no x264**. The encoding is written by hand against libva and
against the NVENC API. See §9.

---

### 5. The life cycle of a session — the exact sequence

It is the part of greatest immediate value for REMOTIX, because it is the same dance that §5.8 rule 1 of the
specification reconstructed by trial and error. Here is the reference's version, read in
`grd-session.c`.

```
grd_session_start()
 │
 ├─ 1. org.gnome.Mutter.RemoteDesktop.CreateSession()          → session path
 │
 ├─ 2. Session.ConnectToEIS(options={})                        → fd
 │      └─ ei_new_sender() + ei_setup_backend_fd(fd)
 │         GSource on ei_get_fd(), ei_configure_name("gnome-remote-desktop")
 │
 ├─ 3. connecting the signals: "closed", "selection-owner-changed",
 │      "selection-transfer"
 │
 ├─ 4. org.gnome.Mutter.ScreenCast.CreateSession({
 │        "remote-desktop-session-id": <SessionId from step 1>,
 │        "disable-animations": true })
 │
 ├─ 5. org.gnome.Mutter.RemoteDesktop.Session.Start()      ← NOW, not before
 │
 └─ 6. ScreenCast.Session.RecordVirtual({cursor-mode, is-platform:true})
        └─ Stream proxy → Stream.Start()                   ← the stream, not the session
```

**The two stakes are identical to the ones REMOTIX paid for** (§5.8 rule 1): the capture session
is created by declaring `remote-desktop-session-id` *before* starting the control, and what is started
at the end is the **Stream**, not the ScreenCast Session.

Two details REMOTIX does not have:

- **`disable-animations: true`** in the capture session options. GNOME's animations over a
  remote link cost bandwidth and add nothing. One line, to copy.
- **`is-platform: true`** in `RecordVirtual`. It declares the virtual monitor «di piattaforma»,
  that is, treated as a real screen from the point of view of the monitor configuration.

**Shutdown** is symmetrical and has the same constraint: `grd_session_stop` calls
`RemoteDesktop.Session.Stop`, and the capture dies with it. The ScreenCast session is **not**
stopped directly.

**How it notices the session has ended**: the `closed` signal on Mutter's session
(`on_remote_desktop_session_closed`). There is no registration with `gnome-session`: that is
a REMOTIX invention (§5.9 of `SPECIFICA.md`, `uscita.rs`), and — given the timings measured there — it is
a *better* invention, because Mutter's `closed` signal arrives when teardown has already started.

The only point where `gnome-remote-desktop` talks to `gnome-session` is
`grd_session_manager_call_logout_sync()` (`grd-daemon-utils.c:207`), and it does so in the opposite direction:
it calls `Logout(NO_CONFIRMATION)` to **close** the greeter session when the client leaves in
handover mode.

---

### 6. The RDP path

#### 6.1 What the server demands from the client

In `rdp_peer_capabilities` and `rdp_peer_post_connect` (`grd-session-rdp.c`). Whoever does not meet one of
these conditions **is disconnected**:

| Requirement | Line | Reason stated in the code |
|---|---|---|
| **Graphics Pipeline (EGFX)** | 1162 | *"Client did not advertise support for the Graphics Pipeline, closing connection"* |
| **32 bpp** | 1177 | Protocol violation if it declares codecs but not 32 bit |
| **Desktop resize** | 1193 | *"Client doesn't support desktop resizing"* |
| **DRDYNVC channel** | 1199 | Without dynamic channels there is no EGFX |
| **Pointer cache > 0** | 1286 | *"Client doesn't have a pointer cache"* |
| **Fastpath output** | 1291 | *"Client does not support fastpath output"* |

**This is the fact that matters most for REMOTIX**: the reference took *exactly* the decision of
§3.7 of the specification — **EGFX only, no legacy fallback** — and enforces it by closing the connection.
The reservation about Android clients («va verificato provandoli») finds an indirect answer here: GNOME
serves the same Android clients REMOTIX has on its list, and serves them only via EGFX.

Two interesting degradations, both on audio:

- if the client **cannot do network autodetect**, outgoing audio is **turned off**
  (`grd-session-rdp.c:1316`): without a bandwidth measurement, sending audio makes the video worse;
- if the client is **iOS or Android**, outgoing audio is **turned off anyway**
  (`grd-session-rdp.c:1323`), with the reason: *«Client cannot handle graphics and audio
  simultaneously»*. To keep in mind: REMOTIX has Android among the reference clients **and** AAC
  audio in §3.2.

#### 6.2 How the server configures FreeRDP

Significant excerpt of `init_rdp_session` (`grd-session-rdp.c:1539` onwards):

```c
RdpSecurity   = FALSE;      TlsSecurity = FALSE;      NlaSecurity = TRUE;
ColorDepth    = 32;
SupportGraphicsPipeline = TRUE;
GfxAVC444v2   = FALSE;   GfxAVC444 = FALSE;   GfxH264 = FALSE;   /* turned on later, in CapsAdvertise */
GfxSmallCache = FALSE;   GfxThinClient = FALSE;
RemoteFxCodec = TRUE;    RemoteFxImageCodec = TRUE;   NSCodec = TRUE;
SurfaceFrameMarkerEnabled = TRUE;   FrameMarkerCommandEnabled = TRUE;
PointerCacheSize = 100;
FastPathOutput = TRUE;   NetworkAutoDetect = TRUE;   RefreshRect = FALSE;
SupportMultitransport = FALSE;                       /* no UDP */
VCFlags = VCCAPS_COMPR_SC;   VCChunkSize = 16256;
HasExtendedMouseEvent = TRUE;  HasHorizontalWheel = TRUE;  HasRelativeMouseEvent = TRUE;
HasQoeEvent = FALSE;           UnicodeInput = TRUE;
AudioCapture = TRUE;   AudioPlayback = TRUE;   RemoteConsoleAudio = TRUE;
OsMajorType = UNIX;    OsMinorType = PSEUDO_XSERVER;
```

**`NlaSecurity = TRUE` with the other two at `FALSE` means NLA is mandatory.** It is the biggest
divergence from REMOTIX, which chose pure TLS (§3.6). See §7.

#### 6.3 Client recognition

`grd_session_rdp_is_client_mstsc()` (`grd-session-rdp.c:251`) recognises mstsc by looking at
`OsMajorType == WINDOWS && OsMinorType == WINDOWS_NT`. So the reference **openly admits that
clients must be told apart**, and it is the confirmation of the three-client rule of §5.7 of `SPECIFICA.md`.

---

### 7. Authentication

#### 7.1 NLA mandatory, with two mechanisms

`GrdRdpAuthMethods` is a set of flags (default: `['credentials']`):

- **`credentials`** — NTLM. The server **fabricates a temporary SAM file** with the configured account
  (`grd-rdp-sam.c`) and passes it to FreeRDP as `NtlmSamFile`. The credentials are not the system
  ones: they are a user/password pair specific to the remote desktop, kept in the keyring;
- **`kerberos`** — requires a keytab with the `TERMSRV` principal. After the handshake, `rdp_peer_logon`
  queries the NLA context (`SECPKG_ATTR_AUTH_IDENTITY`), converts the principal to a local name with
  `krb5_aname_to_localname` and **checks that the uid matches that of the process**
  (`is_auth_identity_current_user`, `grd-session-rdp.c:991`).

This last check is **the same rule REMOTIX had to discover on 3 August** — «entra un
solo utente: quello di cui il server serve la sessione», §3.4 of `SPECIFICA.md`. The reference applies it
on the effective uid, exactly as the REMOTIX note prescribes. With NTLM instead it applies no
additional policy (`"Authenticated using NTLM, not applying any additional policy"`) — and it does not
need to, because the NTLM credential is already specific to that session.

#### 7.2 Where the credentials live

Three interchangeable implementations of `GrdCredentials`:

| Backend | File | Use |
|---|---|---|
| **libsecret** | `grd-credentials-libsecret.c` | User mode: GNOME keyring |
| **TPM 2.0** | `grd-credentials-tpm.c` + `grd-tpm.c` (809 lines) | System mode: seals the secret in the TPM |
| **file** | `grd-credentials-file.c` | Fallback when there is no TPM |
| **one-time** | `grd-credentials-one-time.c` | Handover: throwaway credential |

The TPM variant is meant for the system service, which runs without a user session and therefore without
an unlocked keyring.

#### 7.3 TLS

Certificate and key are configured as **paths to PEM files** (`tls-cert`, `tls-key`); the server
reads them and passes them to FreeRDP with `freerdp_certificate_new_from_pem` / `freerdp_key_new_from_pem`.
No automatic generation: the README refers to `winpr-makecert`, `certtool` or `openssl`.
The certificate fingerprint is exposed on D-Bus (`tls-fingerprint`) so that the Settings panel
can show it.

---

### 8. The EGFX graphics pipeline

`grd-rdp-dvc-graphics-pipeline.c`, 2287 lines. It is the file the REMOTIX specification cites in §5.4.

#### 8.1 Capability negotiation

The list of versions tried, **in descending order** (`cap_list`, line 1567):

```
10.7, 10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 8.1, 8.0
```

The **first version in the list that the client declares** is chosen, and only that one is confirmed with a
`CapsConfirm`. The version decides whether AVC is available:

| Version | AVC420 | AVC444 |
|---|---|---|
| 10.0 … 10.7 | yes, unless `RDPGFX_CAPS_FLAG_AVC_DISABLED` | same |
| 8.1 | only if `RDPGFX_CAPS_FLAG_AVC420_ENABLED` | no |
| 8.0 | **no** | no |

**It is exactly the defect REMOTIX paid for** (§5.4: *«elenco delle versioni EGFX troppo rado:
mancava la famiglia 10.x intermedia, e mstsc si ferma alla 10.6»*). This table is the
authoritative version: ten entries, no gaps.

Other protocol rules applied:

- **10-second timeout** (`PROTOCOL_TIMEOUT_MS`) from the opening of the channel: if no
  `CapsAdvertise` arrives, the session is closed with `ERRINFO_BAD_CAPABILITIES`;
- a **repeated** `CapsAdvertise` is legal only if the initial version was ≥ 10.3 (it is the *protocol
  reset* foreseen by the Microsoft specification); otherwise it is a violation;
- a repeated `CapsAdvertise` that **would turn off AVC** is refused by closing the session;
- `CacheImportOffer` receives an **empty** `CacheImportReply` — that is, the cache is never used, as
  in xrdp;
- `QoeFrameAcknowledge` is accepted and ignored.

#### 8.2 Surfaces

`grd_rdp_dvc_graphics_pipeline_acquire_gfx_surface` (line 439) does, in this order:

1. `grd_rdp_gfx_surface_new` → **`CreateSurface`** (format `GFX_PIXEL_FORMAT_XRGB_8888`);
2. creates the *frame controller*;
3. **`map_surface`** → **`MapSurfaceToOutput`** with `outputOriginX/Y`.

**The two calls are adjacent and neither of them is optional.** It is the direct confirmation of the cause
found by REMOTIX on 2 August (§5.4): creating the surface and hooking it to the output are two
distinct operations.

The only mapping type implemented is `MAP_TO_OUTPUT`. `MapSurfaceToWindow` and the *scaled* variants
do not exist, as in xrdp.

**Separate rendering surface**: if the alignment required by the encoder does not match
the 16 alignment, a *second* EGFX surface is created, encoding is done on that one, and it is copied
to the visible surface with `SurfaceToSurface`. It is the only use of `SurfaceToSurface` in the program.

#### 8.3 Alignment and geometries — the two conventions

In the NVENC path (`refresh_gfx_surface_avc420`, line 1084):

```c
aligned_width  = surface_width  + (surface_width  % 16 ? 16 - surface_width  % 16 : 0);
aligned_height = surface_height + (surface_height % 64 ? 64 - surface_height % 64 : 0);
```

**Width a multiple of 16, height a multiple of 64** — identical to what REMOTIX established in §5.4.

On geometries the code uses **two different conventions, and this must be read carefully** because the
REMOTIX specification records only one:

| Structure | Where | Convention |
|---|---|---|
| `RECTANGLE_16` of the AVC420 meta | `set_region_rects`, line 559 | `right = x + width`, `bottom = y + height` → **exclusive** |
| `RDPGFX_SURFACE_COMMAND` (`cmd.right/bottom`) | line 686 | `right = extents.x + extents.width` → **exclusive** |
| `MONITOR_DEF` of `ResetGraphics` | `maybe_reset_graphics`, line 438 | `right = left + width - 1` → **inclusive** |

> ⚠ **To be re-verified in REMOTIX.** §5.4 of `SPECIFICA.md` notes *«bordi della regione AVC420
> fuori-di-uno: sono inclusivi»*. The reference does the opposite on the AVC420 region and is inclusive
> only on the `MONITOR_DEF`s. The two can coexist if IronRDP's API already applies a
> conversion, but it is a point where a ±1 error produces exactly the described symptom
> (renegotiation and disconnection), and it must be established by looking at the bytes, not at the Rust code.

#### 8.4 ResetGraphics

`grd_rdp_dvc_graphics_pipeline_reset_graphics` (line 462) opens with:

```c
g_assert (g_hash_table_size (graphics_pipeline->surface_table) == 0);
```

**All surfaces must have been deleted before redeclaring the canvas.** And the monitor
list is never empty: `maybe_reset_graphics` builds the array from the current monitors, with
`g_assert (n_monitors > 0)`. It confirms the fourth fix of §5.4 of `SPECIFICA.md`.

#### 8.5 Sending a frame

```
StartFrame(frameId, timestamp)      ← timestamp = hour<<22 | min<<16 | sec<<10 | ms
SurfaceCommand(surfaceId, codecId, ...)
[SurfaceToSurface, only if there is a separate rendering surface]
EndFrame(frameId)
```

For RemoteFX Progressive there is the `SurfaceFrameCommand` shortcut, which sends the three PDUs together.

The `frameId` is recorded in `frame_serial_table` together with the surface *serial*, so that
a late ack referring to an already destroyed surface does no harm: the serial is
counted separately with `surface_serial_ref` / `unref`. It is a refinement needed only with
frequent resizes.

---

### 9. Codecs and encoders — the surprise

**`gnome-remote-desktop` has no software H.264 encoder.** It does not use ffmpeg, it does not use x264, it does not use
OpenH264. The selection, in `grd-rdp-render-context.c:561`:

```
the client can do AVC (420 or 444)  ∧  there is VAAPI  →  AVC444v2 if the client knows it, otherwise AVC420
otherwise                                              →  RemoteFX Progressive (software)
```

Plus a separate, older path for **NVENC** (CUDA), which lives inside the graphics pipeline and
bypasses the rest (`refresh_gfx_surface_avc420`).

| Path | File | Notes |
|---|---|---|
| **VAAPI** | `grd-encode-session-vaapi.c` (1915 lines) | Written **directly against libva**: SPS/PPS/slice generated by hand in `grd-nal-writer.c` (886 lines) |
| **NVENC** | `grd-hwaccel-nvidia.c` + `.cu` | Includes two CUDA kernels (`grd-cuda-avc-utils.cu`, `grd-cuda-damage-utils.cu`) |
| **Vulkan** | `grd-hwaccel-vulkan.c` (1022 lines) | **It is not an encoder**: it serves to import the DMA-BUFs and convert colour. Encoding stays VAAPI |
| **RFX Progressive** | `grd-rdp-sw-encoder-ca.c` | Software fallback: uses FreeRDP's `rfx_encode_message` and rewrites the message in the RDPEGFX format |

#### 9.1 Bitrate control: there is none

`grd-encode-session-vaapi.c:1696`:

```c
config_attributes[1].type  = VAConfigAttribRateControl;
config_attributes[1].value = VA_RC_CQP;
```

**Constant quantisation, QP 22** (`picture_param->pic_init_qp = 22`, line 923), **H.264
High** profile, no bitrate measurement, no VBV, no target. In the NVENC path too the values
declared in the meta are fixed: `qp = 22`, `qualityVal = 100`.

> **This directly touches §3.1 of `SPECIFICA.md`.** The REMOTIX specification motivates the choice of
> `libavcodec` like this: *«Vulkan Video delivers the encoder without bitrate control, which
> we would have to write ourselves… VA-API and NVENC provide it already tuned by the manufacturer»*. The
> reference shows that **bare VA-API gives nothing for free**: bitrate control is a
> configuration attribute that must be chosen and fed, and GNOME chose **not to use it at all**.
>
> The conclusion does not overturn REMOTIX's decision — `libavcodec` really does give the convenience, because
> it wraps VBV, GOP and presets behind a single API — but it corrects the premise: the merit is ffmpeg's, not
> VA-API's. And above all: **at the 10 Mbps working point the reference has nothing to
> teach**, because it does not even try. There REMOTIX is on its own.

#### 9.2 How it adapts, then

Not by adapting the quality, but **the number of frames**. See §10.

#### 9.3 AVC444

Really implemented, unlike xrdp. `prepare_avc444_bitstream` (line 604) handles the three cases
of the `LC` field: dual view (`LC=0`, two streams), luma only (`LC=1`), chroma only (`LC=2`). The
`render_state` decides frame by frame whether to send the auxiliary view, and there is a delayed
*upgrade* logic (`FRAME_UPGRADE_DELAY_US = 60 ms`, `TRANSITION_TIME_US = 200 ms`,
`grd-rdp-surface-renderer.c`): when the link is quiet, the «luma only» frame already
sent is **completed** with the chroma shortly after.

It is a concrete answer to the strategy sketched in §5.2 of `SPECIFICA.md` (*«AVC420 as the base, AVC444
enabled on better connections»*): the reference does it per frame, not per session, and pays
for the chroma only when there is headroom.

---

### 10. Flow control and adaptation

#### 10.1 Measuring the network (`grd-rdp-network-autodetection.c`)

It uses the MS-RDPBCGR autodetect mechanism:

- **RTT**: `RTTMeasureRequest` with tracked sequence numbers. Two cadences — **70 ms** when
  someone needs a precise RTT (that is, when the graphics pipeline is working), **700 ms**
  otherwise. Averaged over a 500 ms window;
- **bandwidth**: `BandwidthMeasureStart/Stop`, hooked to the sending of frames. It is measured **only on
  frames ≥ 10 KB** (`MIN_BW_MEASURE_SIZE`), so as not to skew the measurement with tiny packets;
- detection of clients that do not answer: if more than 16 384 requests remain unanswered, the
  code writes *«Protocol violation: Client leaves requests unanswered»* and resets.

There is also an autodetect **at connection time** (`grd-rdp-connect-time-autodetection.c`, 643
lines), triggered by the `OnConnectTimeAutoDetectBegin` hook.

#### 10.2 The regulator (`grd-rdp-gfx-frame-controller.c`)

Three states: `INACTIVE`, `ACTIVE`, `ACTIVE_LOWERING_LATENCY`. The regulated quantity is the number of
**«frame slots»** (`total_frame_slots`) granted to the renderer: `0` means stopped,
`UINT32_MAX` means no limit.

The activation threshold is derived **from the RTT**:

```c
delayed_frames = rtt_us * refresh_rate / 1e6;
activate_throttling_th = MAX (2, MIN (delayed_frames + 2, refresh_rate));
```

That is: how many frames are «in flight» within a round trip, plus two. Once that threshold
of unacknowledged frames is exceeded, production stops; once down to ≤ 1, it restarts with no limits. In between,
the granted slots are `ack_rate + 1 − enc_rate`, that is, it produces at the rate at which the client acknowledges.

**There is no adaptation of resolution, nor of bitrate, nor of nominal frame rate.** The reference
refresh rate is fixed: `TARGET_SURFACE_REFRESH_RATE = 60` (`grd-rdp-layout-manager.c:36`).

> For REMOTIX: §3.1 of `SPECIFICA.md` foresees *«automatic adaptation of resolution and frame rate to
> bandwidth»*, reusing the dynamic-resolution machinery. The reference **does not do it that way**: it regulates only
> the production cadence, and does so against the ack backlog rather than against the measured bandwidth (which
> it does measure, and uses only to inform the client). It is a simpler and more robust choice, and it is worth
> as a starting point: feedback on acks costs almost nothing and must be implemented anyway,
> resolution adaptation is the safety net on top.

#### 10.3 Output suppression

`SuppressOutput` (MS-RDPBCGR) is handled: when the client minimises the window, the renderer stops and
the RTT consumer is removed, so the probes slow down from 70 to 700 ms.

---

### 11. Capture

`grd-rdp-pipewire-stream.c`, 1326 lines.

#### 11.1 The proposed format

```c
SPA_FORMAT_VIDEO_format      = SPA_VIDEO_FORMAT_BGRx
SPA_FORMAT_VIDEO_size        = FIXED rectangle (width, height of the virtual monitor)
SPA_FORMAT_VIDEO_framerate   = 0/1                    ← «only when it changes»
SPA_FORMAT_VIDEO_maxFramerate= range [1/1 … refresh_rate/1]
```

The cadence declared as zero with a ranged maximum is **exactly** what REMOTIX established
in §5.6 of `SPECIFICA.md`.

> ✅ **The divergence is closed: the reference is right.** [M, 4 August 2026] With the C chain,
> against Mutter 48.7, the **single `SPA_POD_Rectangle` works** and negotiates exactly the size
> asked for — tried at 1282×802, with `is-platform: true` declared in `RecordVirtual`. The
> closed range (min = pref = max) was tried too: **that works as well**, with the same outcome.
>
> The `no more input formats` measured by REMOTIX on 2 August was therefore a fact of *its* chain
> back then — the Rust PipeWire package — or of the absence of `is-platform`. Among the three
> explanations hypothesised here, the Mutter version is excluded (it is the same); between the other two no
> discrimination was made, and it is not worth it: the clean form works and that is the one used. §5.6 of
> `SPECIFICA.md` was corrected accordingly.
>
> It remains true that an **open** range lets Mutter choose, and it chooses 1280×720.

#### 11.2 DMA-BUF

Modifiers are declared only if there is an EGL thread **and there is no NVENC**, with the property marked
`MANDATORY | DONT_FIXATE` and closed by `DRM_FORMAT_MOD_INVALID`. When modifiers are declared,
**a second fallback format without modifiers** is always added, so if the DMA-BUF negotiation
fails shared memory remains.

It confirms by contrast the REMOTIX rule (§5.6): *«to stay in ordinary memory the `modifier` field
is not declared»*. The reference does the opposite because it wants DMA-BUF; the mechanics are the
same.

Accepted buffer types: `MemFd` always, `DmaBuf` if there is EGL. From 2 to 8 buffers. With DMA-BUF and
**explicit sync** available, the `SPA_META_SyncTimeline` meta is also requested.

Metas always requested: `SPA_META_Header` and **`SPA_META_Cursor`** (up to 384×384) — the cursor arrives
as metadata and is rendered separately, not drawn into the image, except in screen-share mode where
`CURSOR_MODE_EMBEDDED` is used.

#### 11.3 Resizing — the difference that matters

`grd_rdp_pipewire_stream_resize()` (line 402) does **one thing only**:

```c
add_format_params (stream, virtual_monitor, ...);   /* con la misura nuova */
pw_stream_update_params (stream->pipewire_stream, params, n);
```

**No new capture session, no new virtual monitor, no new `RecordVirtual`.**
Mutter reconfigures the virtual monitor and answers with `on_stream_param_changed`, where the server
resizes the damage detector and the buffer pool, and emits `video-resized`.

> **It is the answer to the open question of §5.8 of `SPECIFICA.md`.** REMOTIX today redoes the capture at every
> size change, and since a new capture does not register on an already started control, **it redoes
> the control too** — paying the price of losing the state of pressed keys. The specification notes
> *«it will disappear with phase 6, if resizing stops redoing the capture»*. The reference
> shows that it can be done, and how: the PipeWire stream parameter is updated, and that is it.

#### 11.4 The stride

The code computes `stride = width * 4` in `on_stream_param_changed`, but it is only to size the
pool; the real data are always read from the chunk (`grd-rdp-pw-buffer.c`). The REMOTIX rule — *«the
stride is read from the buffer's chunk, never computed»* — stays valid and applies here too.

---

### 12. Layout and resizing

`grd-rdp-layout-manager.c`, 1043 lines. It is an explicit state machine, and deserves to be copied
almost as it is.

```
AWAIT_CONFIG ──(a monitor configuration arrives)──► inhibit_rendering()
                                                       │
                                              AWAIT_INHIBITION_DONE
                                                       │ (no render context in use)
                                              PREPARE_SURFACES
                                                       │ create/update the streams
                                    ┌──────────────────┴──────────────────┐
                              AWAIT_STREAMS                        AWAIT_VIDEO_SIZES
                                    └──────────────────┬──────────────────┘
                                              START_RENDERING
                                                       │ uninhibit_rendering()
                                                  AWAIT_CONFIG
```

The points that solve problems known to REMOTIX:

- **rendering is inhibited before touching anything** and switched back on only when *all* the
  streams have confirmed the new size. It is the disciplined form of rule 3-bis of §5.7 of
  `SPECIFICA.md` («after a size change, wait for the desktop to have redrawn itself»): instead of
  waiting for a 300 ms silence, it waits for an **event**;
- inhibition is not a flag but a **count of resources in use**: `inhibition-done` is emitted
  when `acquired_render_contexts` is empty, that is, when no frame is halfway;
- during `AWAIT_CONFIG` — and only then — `grd_rdp_layout_manager_transform_position` accepts the
  pointer coordinates. In every other state **input is discarded**, because the geometry is not
  stable;
- a configuration that arrives while another is being applied **replaces** the queued one
  (`pending_monitor_config`), it is not queued. It is the answer to the bursts of resizing that
  clients send while dragging the window edge;
- if a «physical monitor» stream closes by itself, a **50 ms** timer starts
  (`LAYOUT_RECREATION_TIMEOUT_MS`) that tries to rebuild the last good configuration.

#### 12.1 Validation of the monitor configuration

`grd-rdp-monitor-config.c`. The rules, applied identically to the three possible sources (Client Core
Data, Client Monitor Data, MS-RDPEDISP):

| Constraint | Value |
|---|---|
| Width and height | **200 … 8192** |
| Physical size (mm) | 10 … 10000, otherwise zeroed |
| Scale factor | 100 … 500, otherwise zeroed |
| Primary monitor | must be at **(0, 0)**; if none declares it, one that is there is elected |
| Overlaps | **forbidden** (checked with `cairo_region`) |
| `DeviceScaleFactor` | **ignored** — deprecated, Windows 8.1 only |

The overall desktop is the extent of the union of the regions; the layout offset serves to
bring everything back to non-negative coordinates.

On MS-RDPEDISP the server declares `MaxMonitorAreaFactorA = MaxMonitorAreaFactorB = 8192` and the maximum
number of monitors: **16** in headless/system modes, **1** in screen share.

---

### 13. Input

#### 13.1 libei, not the `Notify*` methods

`gnome-remote-desktop` uses `ConnectToEIS` and speaks libei, as the REMOTIX specification already notes in
§5.8. It is worth recording **what is gained from it**, because they are things the `Notify*` methods do not give:

| What | How |
|---|---|
| **The session's keyboard layout** | `ei_device_keyboard_get_keymap()` → fd → `xkb_keymap_new_from_string` |
| **The real state of Caps Lock and Num Lock** | event `EI_EVENT_KEYBOARD_MODIFIERS` |
| **The regions of the screens** | `ei_device_get_region()` with `mapping_id` |
| **A synchronisation point** | `ei_ping` / `EI_EVENT_PONG` |

The first point is the **answer to REMOTIX open question no.7** (§5.8: the keyboard
layout is not agreed). The reference imposes nothing and asks the client nothing: **it reads
the keymap from the session**, and for Unicode events it looks for which physical key produces that symbol
in the current layout, applying the level modifiers:

```c
pick_keycode_for_keysym_in_current_group()   /* scorre keycode × livelli */
apply_level_modifiers()                      /* Shift per il livello 1, ISO_Level3_Shift per il 2 */
ei_device_keyboard_key (evcode, state)
evcode = xkb_keycode - 8                     /* XKB → evdev */
```

Scancode events instead pass straight through: RDP scancode → `GetVirtualKeyCodeFromVirtualScanCode`
→ `GetKeycodeFromVirtualKeyCode(..., WINPR_KEYCODE_TYPE_EVDEV)`. That is: **physical positions stay
physical positions**, and the session decides the symbol — exactly the situation REMOTIX describes.
The difference is that the reference, having the keymap in hand, can translate Unicode events with
precision, while REMOTIX today has to declare `REMOTIX_TASTIERA`.

> Practical note: with FreeRDP the client's KLID is available (it is in `rdpSettings`), so
> question no.7 can be closed in two ways — declaring the layout from the KLID, or reading it
> from the session with libei as the reference does. The second is more solid, because it does not trust how
> the client's operating system describes its own keyboard.

#### 13.2 Devices and capabilities

When the seat appears: `ei_seat_bind_capabilities(POINTER, KEYBOARD, POINTER_ABSOLUTE, BUTTON,
SCROLL, TOUCH)`. The devices then arrive with `EI_EVENT_DEVICE_ADDED`, and on
`EI_EVENT_DEVICE_RESUMED` `ei_device_start_emulating` is called with an increasing sequence number.

**The absolute pointer works by regions**: each region has a `mapping_id`, and the capture
stream's `mapping_id` acts as the key. `transform_position` (`grd-session.c:703`) rescales the client's
coordinates onto the region:

```c
scale_x = input_rect_width / ei_region_get_width (region);
x = ei_region_get_x (region) + motion_abs->x / scale_x;
```

It is the elegant replacement for the D-Bus stream path that REMOTIX passes to
`NotifyPointerMotionAbsolute`.

#### 13.3 The wheel

`grd-session-rdp.c:639`:

```c
axis_value = flags & WheelRotationMask;        /* complemento a due se negativo */
axis_step  = -axis_value / 120.0;              /* RDP conta 120 per scatto */
if (flags & PTR_FLAGS_WHEEL_NEGATIVE) axis_step = -axis_step;

vertical:    axis (0,  axis_step * 10.0)
horizontal:  axis (-axis_step * 10.0,  0)
```

`DISCRETE_SCROLL_STEP = 10.0`. **The vertical is negated, the horizontal is negated in the opposite sense** —
an exact confirmation of rule 6 of §5.8 of `SPECIFICA.md`, including the factor 120 → 10.

There is also `grd_session_notify_pointer_axis_discrete`, which multiplies back by 120 towards libei.

#### 13.4 The Pause key

Implemented with a four-state machine (`is_pause_key_sequence`, line 738): it recognises the
sequence `Ctrl↓(E1) → NumLock↓ → Ctrl↑(E1) → NumLock↑` and translates it into `XKB_KEY_Pause` pressed and
released.

> For REMOTIX: §5.8 gives up the Pause key as lost, because IronRDP does not deliver the `KBDFLAGS_EXTENDED1` flag.
> The reference shows that **the E1 flag only serves to disambiguate**: the sequence is recognisable
> from the succession of Ctrl and NumLock alone. If the flag is missing, the state machine works
> all the same with a negligible risk of false positive.

#### 13.5 Pressed keys and lock keys

- two tables, `pressed_keys` (by keycode) and `pressed_unicode_keys` (by keysym), which **discard** the
  repeated press and the unpaired release — identical to REMOTIX rule 4;
- when the session closes, both are emptied by releasing everything, and the queue is
  **forcibly flushed** (`grd_rdp_event_queue_flush`);
- the RDP synchronisation event (`rdp_input_synchronize_event`) releases everything and records the expected
  state of Caps Lock/Num Lock;
- reconciliation happens **after a libei ping**: it waits for the input in flight to have been
  digested (`grd_session_flush_input_async` → `EI_EVENT_PONG`), then compares the expected state with
  the real one read from `EI_EVENT_KEYBOARD_MODIFIERS` and, if it diverges, **presses and releases the key**.

This last point is the well-done version of what §5.8 of `SPECIFICA.md` describes as an
approximation (*«there is no way to impose it… the count starts from all off»*): with libei the
real state is read, and the ping avoids comparing it while events are still queued.

#### 13.6 Event queue

`grd-rdp-event-queue.c`: events arrive from the socket thread and are queued; a `GSource` on the
main thread drains them. **No blocking call from the protocol loop** — rule 3 of
§5.8 of REMOTIX, applied identically.

#### 13.7 Touch and pen (MS-RDPEI)

`grd-rdp-dvc-input.c` (764 lines) implements the `RDPEI` channel: up to **256 contacts**, with one
state machine per contact, plus the pen events. Contacts map onto `ei_touch` with the same
regions as the absolute pointer.

> It is **REMOTIX open question no.1** (touch input, relevant since Android is among the clients). The
> reference solves it natively, not by emulating the mouse.

---

### 14. Virtual channels

| Channel | File | State |
|---|---|---|
| **RDPGFX** (EGFX) | `grd-rdp-dvc-graphics-pipeline.c` | Mandatory |
| **DISP** (MS-RDPEDISP) | `grd-rdp-dvc-display-control.c` | Only in `extend` mode |
| **RDPEI** (touch/pen) | `grd-rdp-dvc-input.c` | Always |
| **CLIPRDR** | `grd-clipboard-rdp.c` (2674 lines!) | If the client joins the channel |
| **AUDIO_PLAYBACK** | `grd-rdp-dvc-audio-playback.c` | If `AudioPlayback` and not `RemoteConsoleAudio` |
| **AUDIO_INPUT** | `grd-rdp-dvc-audio-input.c` | If `AudioCapture` |
| **RDPECAM** (camera) | `grd-rdp-dvc-camera-*.c` | Always (new in 49+) |
| **TELEMETRY** | `grd-rdp-dvc-telemetry.c` | Always |

They all derive from `GrdRdpDvc`, which handles opening, `ChannelIdAssigned`, subscription to the creation
state and teardown. Initialisation happens in the socket thread when `DRDYNVC` goes to
`DRDYNVC_STATE_READY`.

#### 14.1 Clipboard

`grd-clipboard-rdp.c` is the largest file of the project. It covers text (UTF-8 and UTF-16), HTML,
images (BMP, TIFF, GIF, JPEG, PNG) and **files**, the latter through a FUSE filesystem
(`grd-rdp-fuse-clipboard.c`, 1591 lines) that exposes the client's files inside the session. Formats
declared in `grd-mime-type.c`.

REMOTIX has the clipboard in §3.5 («bidirectional», one line). The real count is this: **text is
a few hundred lines, files are a project of their own**. It is worth writing it into the plan.

#### 14.2 Audio

Output: the best format among those offered by the client is negotiated, in the order **AAC → Opus → PCM**.
Fixed stereo. AAC via fdk-aac, Opus at 48 kHz, PCM 16 bit. `grd-rdp-dsp.c` wraps the three encoders and
also implements A-law decoding for input.

Source and sink are **PipeWire** (`grd-rdp-audio-output-stream.c`), not PulseAudio modules
compiled separately as in xrdp. It is the same choice as §3.2 of `SPECIFICA.md`.

The client's volume is applied server-side by multiplying the PCM samples.

#### 14.3 Camera

`grd-rdp-dvc-camera-device.c` (1783 lines) + `grd-rdp-camera-stream.c`: redirection of the client's webcam
**into** the session, exposed as a PipeWire source. It supports H.264 with a software
decoder (`grd-decode-session-sw-avc.c`). It is out of scope for REMOTIX, but it is the feature xrdp does not
have and that GNOME added first.

---

### 15. Configuration

All in GSettings, under `org.gnome.desktop.remote-desktop`, with separate schemas for
`rdp`, `rdp.headless`, `vnc`, `vnc.headless`. Not the credentials: those are in the keyring or in the TPM.

| RDP key | Default | Notes |
|---|---|---|
| `port` | 3389 | |
| `negotiate-port` | `true` | Tries the next 10 ports if busy |
| `enable` | `false` | |
| `screen-share-mode` | `mirror-primary` | or `extend` (virtual monitor) |
| `tls-cert`, `tls-key` | `''` | Paths to PEM files |
| `view-only` | **`true`** | Prudent default: you only look |
| `auth-methods` | `['credentials']` | `credentials` (NTLM) and/or `kerberos` |
| `kerberos-keytab` | `''` | |

Daemon command-line options: `--headless`, `--system`, `--handover`, `--rdp-port`,
`--vnc-port`, `--max-parallel-connections` (default **10**, `0` = unlimited).

`grdctl` has the form `grdctl [--system|--headless] rdp <comando>`, with `set-credentials`,
`set-tls-cert`, `set-tls-key`, `enable`/`disable`, `enable-view-only`/`disable-view-only`,
`set-auth-methods`, `set-kerberos-keytab`, `--show-credentials`.

---

### 16. Concurrent connections and limits

Two distinct mechanisms, and it is better not to confuse them.

**The throttler** (`grd-throttler.c`) acts *before* creating the session, against abuse:

| Limit | Default |
|---|---|
| Connections per peer | 5 |
| Pending connections | 5 |
| Attempts per second (per peer) | 10 |
| Total connections | `--max-parallel-connections`, 10 |

Whoever exceeds is **refused**; whoever arrives too fast is queued and served when the
rate allows.

**The policy on the second session** is instead in `on_session_post_connect` (`grd-rdp-server.c:176`):

```c
if (runtime_mode == HANDOVER || runtime_mode == HEADLESS)
  g_list_foreach (rdp_server->sessions, maybe_stop_session, nuova_sessione);
```

That is: in the single-user modes, **the new connection supplants the old one**, and does so after
`PostConnect`, that is, after the new client has authenticated.

> **It is the third option of the table of §5.9 of `SPECIFICA.md`, the one the user discarded** on 2
> August («soppiantare: comodo per riagganciarsi, ma chiunque si autentichi butta fuori chi sta
> lavorando»). It is worth recording that the reference chose differently from REMOTIX, and why
> it can afford it: the RDP credentials of `gnome-remote-desktop` are a pair dedicated to remote
> desktop, not the system credentials, so «whoever authenticates» is in practice always the same
> person coming back. In REMOTIX, where one authenticates with PAM against the real account, the reasoning does not
> hold in the same way, and refusal remains the right choice.

Note also: **the accept loop is a `GSocketService`**, so connections are accepted
in parallel by construction. The defect of §5.9 of `SPECIFICA.md` — the sequential loop of
`ironrdp-server` — is specific to IronRDP and does not exist here.

#### 16.1 The farewell

`grd_session_rdp_stop` (line 1847) sets the RDP error information before closing:

```c
if (!has_session_close_queued (session_rdp))
  freerdp_set_error_info (peer->context->rdp, ERRINFO_RPC_INITIATED_DISCONNECT);
else if (session_rdp->rdp_error_info)
  freerdp_set_error_info (peer->context->rdp, session_rdp->rdp_error_info);
```

The codes used elsewhere: `ERRINFO_BAD_CAPABILITIES`, `ERRINFO_BAD_MONITOR_DATA`,
`ERRINFO_CLOSE_STACK_ON_DRIVER_FAILURE`, `ERRINFO_GRAPHICS_SUBSYSTEM_FAILED`,
`ERRINFO_CB_CONNECTION_CANCELLED`.

> **It was the «declared farewell» REMOTIX owed** (§5.9 of `SPECIFICA.md`). With FreeRDP the
> debt does not exist: `freerdp_set_error_info` is public API. The reference uses
> `RPC_INITIATED_DISCONNECT` for the orderly close, not `LogoffByUser` — and the choice is sensible,
> because it describes who closed, not why.

---

### 17. What changes between 48 (Debian Trixie) and 51

The architecture is the same: **48 already uses libei**, it already has the layout manager, the VAAPI encoder, the
frame controller and the EGFX pipeline in the form described here. The differences:

**Added after 48:**

- **camera** redirection (MS-RDPECAM): `grd-rdp-dvc-camera-*`, `grd-rdp-camera-stream`
- software H.264 **decoding** (needed by the camera): `grd-decode-session-sw-avc`
- the connection **throttler**: `grd-throttler`
- `grd-frame-clock`, `grd-sample-buffer`, `grd-vk-physical-device`, `grd-vk-sync-file` (explicit sync)
- `grd-settings-headless` as a class of its own
- renamed with the `dvc` prefix: `grd-rdp-graphics-pipeline` → `grd-rdp-dvc-graphics-pipeline`, and likewise
  for audio, display control and telemetry; `grd-rdp-dvc-handler` introduced

**Different requirements:** FreeRDP ≥ 3.1 (48) against ≥ 3.22 (51); libei ≥ 1.2 against ≥ 1.3.901.

For REMOTIX it means that **everything useful here is already in the 48.x that runs on Trixie**, and that the
measurements made against Mutter 48.7 stay comparable.

---

### 18. The account for REMOTIX

#### 18.1 What it confirms

| REMOTIX decision | Confirmation in the reference |
|---|---|
| **EGFX only**, no legacy fallback | `rdp_peer_capabilities` closes the connection if it is missing (§6.1) |
| Direct Mutter interfaces, not the portal | Same, and for the same reason |
| `RecordVirtual` instead of `RecordMonitor` | Same in `extend` mode |
| `CreateSurface` + `MapSurfaceToOutput` | Adjacent and mandatory (§8.2) |
| Width ×16, height ×64 | Identical (§8.3) |
| `ResetGraphics` with the monitor definition | `g_assert (n_monitors > 0)` (§8.4) |
| PipeWire cadence declared at 0 + ranged maximum | Identical (§11.1) |
| Last frame kept and resent | `invalidate_surface` re-offers `last_buffer` |
| Count of pressed keys, release at end of connection | Identical (§13.5) |
| Wheel: /120 → ×10, vertical negated | Identical (§13.3) |
| No D-Bus inside the protocol loop | Event queue + `GSource` (§13.6) |
| PipeWire for audio | Identical (§14.2) |
| Remote session only for the user who owns it | Check on the uid in `rdp_peer_logon` (§7.1) |
| The declared farewell is needed | `freerdp_set_error_info` before closing (§16.1) |

#### 18.2 What it contradicts, or corrects

1. **NLA mandatory.** The reference does not offer pure TLS: `NlaSecurity = TRUE`, the other two
   `FALSE`. REMOTIX chose TLS + PAM. It is not a mistake — it is a different choice with different
   consequences: with NLA the credentials are verified *before* allocating the session, and mstsc shows
   its own credentials window; with pure TLS authentication happens inside the RDP protocol and the
   defect found on 3 August (§3.4: «whoever sends no credentials is not validated») **could not
   exist**. To put on record: the guard that starts from *denied* is the price of pure TLS.

2. **Bitrate control is not given by VA-API.** §9.1. The motivation of §3.1 of `SPECIFICA.md` must be
   corrected in its premise; the conclusion (using `libavcodec`) holds all the same, indeed it gets stronger.

3. **There is no software H.264 encoder.** GNOME's fallback is RemoteFX Progressive. REMOTIX
   foresees `libx264` as an always-available base and the starting point of development: it is a
   reasonable and simpler choice, but one should know that **the reference does not validate it** — nobody has ever
   tried that road with these clients.

4. **The second connection supplants, it is not refused.** §16. REMOTIX decided differently and
   with reason, but the reason must be written: it depends on the fact that REMOTIX authenticates against the real account.

5. **Resizing does not redo the capture.** §11.3. This is the most useful correction: it cancels the
   price that §5.8 of `SPECIFICA.md` accepts reluctantly.

6. ~~**Single PipeWire rectangle instead of a closed range.**~~ §11.1. **CLOSED on 4 August: the
   reference is right**, the single rectangle works and is the form REMOTIX uses. [M]

7. **Edge convention of the AVC420 region.** §8.3. To be re-verified on the bytes.

#### 18.3 What is worth copying, in order of return

1. **The layout manager's state machine** (§12). It solves together rule 3-bis, the resizing
   bursts and the discarding of input during the geometry change. It is the most precious thing in the
   file.
2. **Resizing via `pw_stream_update_params`** (§11.3). It removes a complete redo of
   capture and control at every size change.
3. **The frame-slot regulator with a threshold from the RTT** (§10.2). A few dozen lines, and it gives
   basic adaptation for free.
4. **The complete list of EGFX versions** (§8.1), to be kept aligned.
5. **`disable-animations: true`** when creating the capture session (§5). One line.
6. **The validation of the monitor configuration** (§12.1): limits, primary at (0,0), no
   overlaps.
7. **The reconciliation of lock keys after a ping** (§13.5), if and when we move to libei.

#### 18.4 The REMOTIX open questions on which the reference says something

| Question | What the reference says |
|---|---|
| **no.1** — touch input | Implemented natively via MS-RDPEI + `ei_touch`, 256 contacts (§13.7) |
| **no.6** — middle button and horizontal wheel | **Dropped**: it was an IronRDP limit. FreeRDP delivers distinct `MouseEvent`, `ExtendedMouseEvent` and `RelMouseEvent` (§6.2, §13.3) |
| **no.7** — keyboard layout | It is not agreed: **it is read from the session** via `ei_device_keyboard_get_keymap` (§13.1). Alternatively the KLID is in `rdpSettings` |
| **no.9** — mstsc, background at 75% after a size change | No direct correspondence, but §12 suggests where to look: the reference **sends nothing** between the inhibition and the confirmation of all the streams. If REMOTIX sends the kept frame before the stage is consistent, that is the symptom |
| **no.10** — session not registered in logind | The reference uses `sd_session_get_class` and `sd_session_is_remote` (`grd-daemon-utils.c:195`), so it **assumes** that the session is registered. In headless modes it is whoever starts the session who must guarantee it, not the server |

---

### 19. What is not there

For completeness, and so as not to go looking for it:

| Feature | State |
|---|---|
| Software H.264 encoder | **Absent** — the fallback is RemoteFX Progressive |
| Bitrate control | **Absent** — fixed CQP, QP 22 |
| Resolution adaptation to bandwidth | **Absent** — only the cadence is adjusted |
| UDP multitransport (MS-RDPEUDP) | `SupportMultitransport = FALSE` |
| RDP gateway (MS-TSGU) | Absent |
| Client drive redirection | Absent (the FUSE serves only the clipboard files) |
| Printer, serial, USB redirection | Absent |
| RemoteApp (RAIL) | Absent |
| Smartcard | Absent |
| EGFX surface cache | Declared and always refused (empty `CacheImportReply`) |
| X11 backend | Absent — Wayland only, like REMOTIX |
| HEVC, AV1 | Impossible: they are not in MS-RDPEGFX |


<a id="xpra"></a>

## XPRA — the study, done on 14 August 2026

*The project's seventh study. ⛔ It was planned by `PIANO.md` §1.3 **before writing the page**
and was never done: it is written now, with the page already written, and it is late — ⭐ but not too late, because
half of what is in here changed the product **this very day**.*

> ### ⭐⭐⭐ Why this study exists, and who asked for it
>
> **The user asked for it, twice.** The first time on 9 August, and it is the origin of the whole web
> track: *«ti spiego perché mi è venuto in mente il discorso WEB: in passato ho avuto modo di usare
> XPRA, e devo dire di essere rimasto molto sorpreso»* (`DECISIONI.md` §1.6).
>
> The second **on 14 August**, in front of the product that could finally be used, and with a defect in
> hand: *«un piccolo difetto è la cattura del puntatore del mouse… per questa funzionalità puoi
> studiare la soluzione che ha adottato il progetto XPRA»*.
>
> ⇒ ⛔ **And he was right within half an hour**: Xpra's solution for the pointer took apart a line of our
> specifications that contradicted another one. It is `LEZIONI.md` §9 point 0 — *«look for whoever has
> already done it»* — for the third time, and for the third time it was the user who asked.

### How it was done, and what it is worth

⛔ **Read in the code**, not in the documentation: `Xpra-org/xpra-html5`, the files `html5/js/Client.js`
and `html5/js/Window.js`, plus the server's `docs/Usage/Encodings.md`. ⇒ What follows is `[R]`, except
where `[S]` is written.

⚠ **And the boundary is declared**: Xpra is on **WebSocket** and we are on **WebTransport**; its server was
born around the X11 *damage* model and ours talks to a Wayland compositor. ⛔ **The
transport is not inherited, and neither is the update model.** What is inherited is the **shape
of the questions** the client asks the server — and that is where we are behind.

⚠ **And one thing I could NOT measure**: the `README` does not list the limits of the HTML5 client
(clipboard, audio, keyboard layouts, IME, full screen). ⇒ `[?]` — I do not deduce them from code
read by sampling.

---

### ⭐⭐⭐ 1. The thing worth most, and we needed it TODAY: **the first frame is ASKED FOR**

```javascript
request_refresh(wid) {
  this.send([PACKET_TYPES.buffer_refresh, wid, 0, 100,
            {"refresh-now": true, batch: {reset: true}}, {}]);
}
```

⛔⛔ **Xpra's client does not WAIT for the screen to change: it tells the server «repaint now».**

⇒ And this is **exactly** the defect the user felt today as *«il tempo fra il login e
la comparsa del desktop è troppo lungo»*: `[M]` 14 August 2026, from the log of his real
session, between the video channel switched on and the first pixel **4.10 seconds out of 5.21** pass, and the log
says why — *«still scene: Mutter delivers only when something changes»*.

| | |
|---|---|
| ⛔ **what we are missing** | in `RCP.md` **there is no message that asks for the image**. There is `RICHIEDI_CHIAVE` (§7.1), but it asks for a **keyframe** of what has already been captured: if nothing arrives from the compositor, it produces nothing |
| ⚠ **and it is not copied literally** | Xpra's `buffer_refresh` is cheap because their server owns the X11 damage model. ⛔ On Wayland **Mutter cannot be ordered to repaint**: the equivalent lever is **restarting the stream**, which delivers a buffer — `[M]` that is how our `+325 ms` frame is born |
| ⇒ ⭐ **what is inherited** | **the shape**: the client must be able to say «give me the screen now», and the server must have *a* way to obey. Who carries it out is our business |

---

### ⭐⭐ 2. The cursor: **the browser draws it, not the page** — and no capture

```javascript
function set_cursor_url(url, x, y, w, h) {
  window_element.css("cursor", `url('${url}') ${x} ${y}, auto`);
}
```

⭐ **The browser's cursor WEARS the shape of the remote one**, hotspot included, from a
`data:image/png;base64`. ⛔ **No element drawn over the canvas, no `cursor: none`.** And it
does the scaling itself when `devicePixelRatio ≠ 1`, adjusting the hotspot too.

**And pointer capture?** It is there, ⛔ **but it is a user option**, not an automatism:

```javascript
if (window.cursor_lock && win.canvas) { win.canvas.requestPointerLock(); }
```

⇒ a button (`#cursor-lock-button`) that you press. Coordinates are **absolute by default**; with
the lock on they switch to movements (`e.movementX`).

> #### ⛔⛔ And here the study took apart one of our lines with another of our lines
>
> | where | what it said |
> |---|---|
> | `SPECIFICHE.md` §7.1 | *«the physical mouse comes from **Pointer Lock**… without it, two would be seen»* |
> | `SPECIFICHE.md` §7.5 | *«**absolute** pointer — it is the **only** pointer path»* |
>
> ⇒ The lock serves to give **relative movements**. We send **absolute positions**. ⛔ It
> bought nothing, and it cost the seizure of the pointer — which is precisely what the user
> saw.
> ⭐ **And the reason it had been put there** — *«otherwise two are seen»* — is solved better
> the other way, **with the piece we had built that same morning and were not using**:
> `CURSORE_FORMA` (`RCP.md` §7.2).
>
> ✅ **Adopted on 14 August 2026**: the browser's cursor wears the remote shape, the drawn
> arrow gets out of the way in the classic manner, capture stays switchable by hand. The
> **touch** mode keeps the drawn pointer, and must: ⭐ **the finger has no cursor to dress.**

---

### ⭐⭐ 3. The window size: **the client states it, the server carries it out**

```javascript
_screen_resized(event) {
  const packet = [PACKET_TYPES.configure_display,
                  {"desktop-size": [this.desktop_width, this.desktop_height],
                   "monitors": this._get_monitors(), …}];
  this.send(packet);
}
```

⭐ **The client communicates its own size and the server RESIZES the desktop.** Local CSS
scaling (`transform: scale(1/scale)`) stays as a fallback, not as the main road.

⇒ ⛔ **It is our `RCP.md` §4.5, «the granted canvas» — and today nobody keeps it**: `[M]` 14 August
(link A1), a client that asks for **1280×720** gets the grant, but the stage captures
**1920×1080** (a compile-time constant) and `rcp` refuses **every** frame: *145 produced, 0
sent, black client without errors*.

⚠ **And the price shows on the user's screen**: his is **21:9** (2560×1080), the remote
desktop **16:9** ⇒ `[M]` from his video, **36 % of the pixels are black band**.

---

### 4. How it paints — and here **we are ahead**

| Xpra HTML5 `[R]` | us |
|---|---|
| **2D canvas** with an *offscreen canvas* and `swap_buffers()` | canvas + **WebCodecs** |
| accepted encodings: `rgb32`, `rgb24`, `jpeg`, `png`, `webp`, `scroll`, `void` | **HEVC/AV1 in hardware** |
| ⛔ `h264` **refused on the main path**: *«h264 decoding is only supported via the decode workers»* | video is the normal road, not the exception |

⇒ ⭐ **Their reference road is still image-based** (jpeg/png/webp) with video as a special
case in a worker. Ours is born on video. ⚠ And this explains the sentence of the web study:
*«Xpra and noVNC stay on the canvas, and **neither of the two declares a latency number**»* (§web).

#### ⭐ One thing they have and we do not: the `scroll` encoding

`[S]` *«tries harder to send screen updates using motion vectors»* — instead of the pixels one sends
**«this area moved by N»**. It is the case of someone scrolling a page or a terminal, that is
**what the user does all day**.
⚠ **It is not something to take now**: with HEVC in hardware the motion vectors are found by the
encoder, and it is its job. ⭐ But the line must be kept for the day bandwidth gets tight:
`SPECIFICHE.md` §8.

---

### 5. The keyboard: **they send positions, we send letters** — and the difference is intended

```javascript
[PACKET_TYPES.key_action, wid, keyname, pressed, modifiers, keyval, keystring, keycode, group]
```

⛔ Xpra sends **the code and the name of the key**, plus `keyval`, `keystring` and the `group`. ⇒ It is the
road that `SPECIFICHE.md` §7.3 discarded **with a written reason**: *«a client with an American
keyboard attached to an Italian session would produce the wrong letters»*, and on Android a
keyboard **has no positions at all**.

⭐ **And they handle dead keys, we do not** — explicitly:

```javascript
const dead = keystring.toLowerCase() === "dead";
if (dead && ((this.last_keycode_pressed !== keycode && !pressed) || pressed)) { … }
```

⇒ ✅ **And it is consistent with the decision the user took today** (`DECISIONI.md` §5-bis.6-bis): dead
keys and the IME stay **out, declared**. ⚠ The study confirms that the price exists — Xpra
pays it with dedicated code — and that **our road is a different choice, not an oversight**.
`[?]` And the **IME** does not appear at theirs either: someone writing Chinese inside a browser, in Xpra,
`[?]` I did not find served.

---

### 6. Latency: **they measure it, and we do not**

```javascript
this.server_ping_latency = 0;
this.client_ping_latency = 0;
PING_FREQUENCY = 5000;   // ms
```

⭐ A `ping` every five seconds, and **two** distinct numbers: how long the server takes and how long the
client takes. ⇒ ⛔ We measure latency **at the bench** (`DECISIONI.md` §2.6) and **never show it
to the user**: when he says *«mi sembra lento»* he has no number to give us, and we do not have his.

⚠ **It is not the same measurement as our 50 ms cap** — theirs is the network round trip, ours is
input → glass. ⭐ But the lesson is one of shape: **a number the user sees is a number the user
can dispute**, and it is more useful than ten in our outcome files.

---

### ⛔ What is NOT taken from Xpra

| | why |
|---|---|
| the **transport** (WebSocket) | `DECISIONI.md` §6.4: we are on WebTransport, and that piece is not inherited |
| the **image road** (jpeg/png/webp with video in a worker) | it is the opposite of our starting point: `SPECIFICHE.md` §3.1 wants 4K at 60 with hardware encoding |
| **key positions** as the main road | §7.3, with the reason already written and already paid for in v1 |
| the **X11 damage** model | our compositor is Wayland: the same question is asked, the answer comes from another mechanism |

---

### ⭐ What this study has already changed, and what it opens

| | state |
|---|---|
| ⭐ **the cursor dressed by the browser, and no capture** | ✅ **done on 14 August 2026** |
| ⛔ **the client must be able to ask for the image** («repaint now») | ⏳ **open** — and it is the work on the desktop's time to appear |
| ⛔ **the canvas at the client's size** | ⏳ **open**: `RCP.md` §4.5 exists and is not kept. On the user's 21:9 **36 %** of the screen is black |
| ⚠ **a latency number shown to the user** | 🔸 to be weighed: it costs little and changes the way judgements come back |
| the `scroll` encoding | 📖 kept aside for when bandwidth gets tight |

> #### ⭐⭐ And the line to take away, which is not technical
>
> The study was planned **before** writing the page, and was done **after**. ⛔ In between
> we wrote a specification that contradicted itself (§7.1 against §7.5), we implemented it, and the
> defect was found by **the user in thirty seconds of use** — also telling us where to look.
>
> ⇒ ⚠ *The cost of skipping point 0 of `LEZIONI.md` §9 is not the time of the study: it is the code
> written in the meantime, and the trust spent defending it.*


---

## REMOTIX «autonomo»? Inventory of third-party components

*Read-only study, 10 October 2026. Sources: the repository on the `full-english` branch (commit `e24c303`), the
binary built on the server (`/media/REMOTIX/src/full-english-uscite/server-c/nuovo/src/remotix`, read with
`ldd`), the packages in `packaging/`, the installer in `installatore/vendor/`.*

---

### In half a page: what to decide

**A REMOTIX without third-party components cannot exist.** REMOTIX shows in the browser a desktop that is not its own
(GNOME, KDE, XFCE, LXQt), captures it with a graphics card that speaks only through its drivers, and delivers it
to a browser that is not its own. These three pieces stay someone else's forever. What can be chosen is **how many
pieces of others we carry inside ourselves**, and **how many we ask the distribution for**.

**Where we are today** (the picture is already good):
- Inside what we distribute there are **only pieces with permissive licences** (MIT, BSD, Apache), plus **one
  small LGPL piece** (the description of a KDE protocol). **No GPL.** The only obligation is
  **to ship the licence texts**, and the script that collects them already exists.
- Everything else (some thirty libraries, the desktops, the drivers, systemd, PipeWire, the browsers) is given by the
  distribution or the user: **no legal obligation for us**.

**Recommendation:**
1. ⛔ **Do not replace any large component with our own code.** The «big» candidates (the QUIC transport,
   cryptography, the system login, PipeWire, the drivers) are exactly those where a mistake of ours becomes
   a hole reachable from the Internet, and where today thousands of other people's eyes protect us. By the rule
   *complexity = vulnerability*, redoing them in house **increases** the risk, it does not remove it.
2. ✅ **One thing to do at once, small (hours, not weeks)**: put back into the `.run` the file with the licence
   texts (today it is not there: `packaging/rilascio.sh` marks it as an open point) and **complete it** with three entries
   that are missing today: the audio library inside the page, the descriptions of the Wayland protocols, the pieces of
   emscripten. The REMOTIX licence (§8) **already promises** that those texts accompany the product: today the
   promise is not kept.
3. 🔸 **A possible but not urgent replacement**: GLib (used only to talk via D-Bus with GNOME, KDE and
   systemd). Removing it would take away ~9 indirect libraries. It costs 2-4 weeks and a full suite on the 4 desktops;
   it brings nothing legal nor of security. To keep in the drawer, not to do.
4. Correct a sentence of the SPECIFICHE (§11.4): it says «tutte le librerie del server sono permissive», but
   some of the distribution's are **LGPL** (glibc, GLib, and others). It is **lawful** (linked dynamically,
   the LGPL allows it), but the sentence must be made true: «nessuna GPL; le LGPL della distribuzione, collegate
   dinamicamente, sono ammesse».

**In one line**: **legal** autonomy is within reach of a few hours of work; **technical** autonomy is not bought
by rewriting, it is bought by choosing a few solid suppliers (already done); **distribution** autonomy is a product
choice, and its price is carrying the security updates along.

---

### 1. The complete inventory

Legend of the last column: **yes** = the licence asks something of us (usually shipping the text and the names
of the authors); **no** = it is a piece installed by the distribution or the user, with its own texts.

### 1a. Embedded in what we distribute

They are the pieces of others that end up **inside our files**: in the `remotix` program, in the web page the
program serves, in the `remotix-install` installer.

| component | what it is for in REMOTIX | licence | who maintains it | our obligation |
|---|---|---|---|---|
| **ngtcp2** 1.25.0 | **QUIC**: the fast network «pipe» on which images, audio and commands travel to the browser | MIT | ngtcp2 project (Tatsuhiro Tsujikawa and contributors; the same author as nghttp2, used by curl) | **yes** — MIT text. Already in `debian/copyright` and in `licenze.py` |
| **nghttp3** 1.18.0 | **HTTP/3** on top of QUIC, on which WebTransport rests | MIT | same project | **yes** — as above |
| **libopus** 1.5.2, compiled to WebAssembly **inside the page** (`src/opus-wasm/`) | **decodes the audio in the browser**. A measured choice (D-006, 25 Sep): Firefox's decoder, under video load, made 3-5 holes a minute; this one zero | BSD-3 | Xiph.Org | **yes** — BSD text. ⚠ **Today it is not in the licence file** (`licenze.py` does not know it) |
| **pieces of the emscripten C library** inside the same `opus.wasm` (memory, copies: the tool puts them in to make libopus run in the browser) | none visible: they serve libopus | MIT / UIUC (emscripten), MIT (musl) | Emscripten project | **yes**, strictly. ⚠ **Not listed** |
| **8 Wayland protocol descriptions** (`src/protocolli/*.xml`): from these, code is generated that goes into the binary | they are the «modules» to talk to the compositors: capturing the screen (wlroots, KDE), virtual keyboard and pointer, clipboard, monitor size | 7 MIT or similar (wlroots, Collabora, Purism, Simon Ser); **1 LGPL-2.1+**: `zkde-screencast` (KDE) | freedesktop / wlroots / KDE | **yes**. ⚠ **Not listed**. For the LGPL piece see §2 |
| **Go** (the language: runtime and standard library) | the installer's engine | BSD-3 | Google | **yes** — already in `licenze.py` |
| **golang.org/x/sys, x/text, x/exp** | system calls, text | BSD-3 | Google (Go project) | **yes** — already |
| **Charm**: bubbletea, lipgloss, x/ansi, x/term, x/cellbuf, colorprofile | the installer's **TUI** (windows, colours, keys in the terminal) | MIT | Charmbracelet Inc. (a company, widely used) | **yes** — already |
| **godbus/dbus** | the installer queries systemd and the system via D-Bus | BSD-2 | volunteers (Georg Reinke and others) | **yes** — already |
| muesli/termenv, ansi, cancelreader · mattn/go-isatty, go-runewidth, go-localereader · rivo/uniseg · lucasb-eyer/go-colorful · xo/terminfo · aymanbagabas/go-osc52 · erikgeiser/coninput | support pieces for the TUI: character width, colours, terminal capabilities | all MIT | individual volunteers | **yes** — already (go-localereader with the exception written in `licenze.py`) |

*Note: the development binary on the server links ngtcp2 and nghttp3 **dynamically** (from `rete11/prodotto/lib`);
in the release packages they are **static**, inside the binary (DECISIONI §10.6, D2). For the licence, the
release is what counts.*

*Note: the rest of the web page is all ours: no JavaScript library, no embedded font (the system's are
used), the icons are hand-written SVG.*

### 1b. Distribution libraries linked to the program

From the `ldd` of the built binary (10 Oct) and from the dependencies of the `.deb`, `.rpm`, Arch packages. They are installed by the
package manager; the licence texts are carried by the distribution.

| library | what it is for in REMOTIX | licence | who maintains it | obligation |
|---|---|---|---|---|
| **OpenSSL 3** (libssl, libcrypto) ≥ 3.5 | **encryption**: the TLS inside QUIC, the certificates, the page over HTTPS | Apache-2.0 | OpenSSL Foundation | no |
| **Linux-PAM** (libpam) | the **login**: checks name and password exactly like the machine (lockouts, SELinux, LDAP included: DECISIONI §10.18) | BSD-3 (or GPL, at choice: we use the BSD) | Linux-PAM (volunteers, Red Hat) | no |
| **GLib / GIO / GObject** | talking via **D-Bus** with GNOME (Mutter), KDE, logind, KDE's clipboard | LGPL-2.1+ | GNOME | no (linked dynamically: the LGPL allows it) |
| **libpipewire** | receiving the **screen** from GNOME and KDE, and the **audio** of all desktops | MIT | PipeWire (Collabora, Red Hat) | no |
| **libva**, libva-drm | **video encoding on the card**, Intel (and AMD where needed) | MIT | Intel | no |
| **libvulkan** (the Khronos loader) | **video encoding on the card**, AMD and NVIDIA (Vulkan Video, phase 19) | Apache-2.0 | Khronos / LunarG | no |
| **libei** | **keyboard and mouse** on GNOME and KDE | MIT | freedesktop (Red Hat) | no |
| **libxkbcommon** | the **keyboard maps** (Italian, American…) | MIT | freedesktop | no |
| **libwayland-client** | talking to the **compositors** (wlroots, labwc, KWin) | MIT | freedesktop | no |
| **libgbm** (Mesa), **libdrm** | the **card's memory sheets** (the «zero copy») | MIT | Mesa / freedesktop | no |
| **libopus** | **audio encoding** on the server | BSD-3 | Xiph.Org | no |
| **glibc** (libc, libm) | the base of every C program | LGPL-2.1+ | GNU | no |
| indirect (pulled in by GLib, PAM, etc.): zlib, zstd, pcre2, expat, libffi, libselinux, libcap-ng, libaudit, libmount, libblkid, libgmodule, libatomic | none directly | zlib, BSD/GPLv2 at choice, BSD-3, MIT, MIT, public domain, LGPL-2.1, LGPL-2.1, LGPL-2.1+, LGPL-2.1+, LGPL-2.1+, GPL-3 **with the exception** that makes it free for any program | various | no |

### 1c. Programs and services used while REMOTIX runs

They are not linked to our program: REMOTIX **starts** them or **talks** to them. Between separate programs the licence
of one does not touch the other. **No obligation.**

| program / service | what it is for | licence | who maintains it |
|---|---|---|---|
| **Linux kernel** | the graphics card (DRM), shared memory, the network | GPL-2 (calls to the kernel do not count as a «derivative work») | Linux Foundation and everyone |
| **systemd** (logind, user session manager, tmpfiles), `loginctl`, `systemctl` | opening and closing users' sessions | LGPL-2.1+ | systemd (Red Hat and others) |
| PAM modules `pam_systemd`, `pam_listfile`, `pam_selinux`; `usermod` | the complete login, the list of denied users | various permissive / GPL | distribution |
| **D-Bus** (system and user bus) | the channel to talk to desktops and systemd | AFL/GPL | freedesktop |
| **GNOME**: gnome-shell, Mutter, gnome-session | the GNOME desktop; Mutter gives screen and input to REMOTIX | GPL | GNOME |
| **KDE Plasma**: KWin, startplasma-wayland | the KDE desktop | GPL | KDE |
| **XFCE** (xfce4-session), **LXQt** | the two «light» desktops | GPL / LGPL | XFCE, LXQt |
| **labwc** | the compositor under which REMOTIX runs XFCE and LXQt | GPL-2 | volunteers (Johan Malm and others) |
| **wlr-randr**, **Xwayland**, a scalable font | monitor size/cut on XFCE and LXQt; X11 programs (XFCE's panel) | MIT, MIT, various | volunteers, freedesktop |
| **PipeWire** (the service), **WirePlumber**, pipewire-pulse | the screen stream (GNOME, KDE) and the audio | MIT | PipeWire (Collabora, Red Hat) |
| **card drivers**: Intel `intel-media-driver`, Mesa (radeonsi, RADV), proprietary NVIDIA | they really do the H.264/HEVC encoding | MIT/BSD; NVIDIA closed | Intel, Mesa, NVIDIA |
| **package managers**: apt, dpkg, dnf, rpm, zypper, pacman | the installer drives them | GPL (separate programs) | distributions |
| **ufw / firewalld**, **SELinux** (module `remotix-selinux`) | opening the port, allowing the hand-over to the user | GPL | distributions |
| **build tools** (they do not reach the user): gcc, Go, emscripten, podman, wayland-scanner, glslang | compiling | various | various |

### 1d. The browsers

| browser | what REMOTIX uses | licence | who maintains it |
|---|---|---|---|
| **Chrome / Chromium** (and Edge) | **WebTransport** (the QUIC pipe on the browser side), **WebCodecs** `VideoDecoder` (H.264/HEVC decoding with the client's card), WebAssembly (the audio), the `bitmaprenderer` canvas | BSD-3 (Chromium) | Google |
| **Firefox** | the same things, only H.264 on Linux | MPL-2.0 | Mozilla |
| Safari | never tried | — | Apple |

No obligation: the browser is the user's. But it is the **strongest** dependency of all: WebTransport is still an
evolving draft, and when the browsers change it, REMOTIX must follow them (it does so today through ngtcp2/nghttp3 and
our 9 000 lines of `webtransport.c`).

---

### 2. Replacing them with our own code: what it would cost, what it would risk

The criterion is the project's rule: **every extra piece of our own code must show what it protects**.
A replaced component is worth it if it removes a **real risk** (legal, security, abandonment) larger
than the risk our new code adds.

### The precedent: ffmpeg, removed in phase 18 (30 September)

It is the only case already done, and it teaches a lot.
- **Why**: ffmpeg (libavcodec) in the distributions is **GPL**, incompatible with a non-commercial licence
  (DECISIONI §10.22, §10.25). A **real legal** risk, not a theoretical one.
- **What it cost**: ~2 250 new lines of ours (`vadiretta.c` 1 782: talking to the card and **writing the H.264/HEVC
  headers by hand bit by bit**; `scrittore_bit.c` 132; `colori709.c` 330), one intense
  day of work in parallel, the full suite on the 4 boxes (673 tests, 135 minutes), and old/new comparison
  measurements. A regression found halfway (colour conversion «from memory» had
  worsened, down to −6 dB on the Radeon) and corrected before closing.
- **What it returned**: the licence is free; fewer libraries; preparing images «from memory» became
  **twice as fast**.
- **And the lesson**: ffmpeg **was not simply replaced by our own code**: it was replaced by **libva**,
  another third-party component, thinner and permissive. We wrote the easy and stable part ourselves (the
  stream headers, which are a fixed standard), and left the hard part to others (talking to every
  card). This is the good form of «autonomia». The price that remains: the 2 250 lines are now **ours to
  maintain** — if a browser or a card expects a different detail in the headers, the fault is ours.

### Component by component

**Feasibility**: *impossible* = it cannot be done without changing what REMOTIX is; *unreasonable* = it can, but the
cost or the risk are disproportionate; *possible* = it can, with a measurable effort.

| component | feasibility | rough effort | risk if we do it ourselves | verdict |
|---|---|---|---|---|
| **ngtcp2 + nghttp3** (QUIC, HTTP/3) | unreasonable | 6-12 months of an expert; then **forever** (the browsers change WebTransport) | ⛔ **the highest of all**: it is the first code that reads the packets of **anyone** on the Internet, **before** the login. ngtcp2 is continuously checked by automatic defect-finding tools (OSS-Fuzz) and used by curl; ours would not be. A hole here is an open door on the server | ⛔ **never** |
| ↳ alternative: the QUIC that **OpenSSL 3.5** already has inside | to be verified | a test bench, days | it would remove ngtcp2 but not nghttp3; as far as I know it does not handle the QUIC «datagrams» REMOTIX uses (81 places in `webtransport.c`), and choice §6.4 already weighed it against 4 candidates | not now; only if ngtcp2 were abandoned |
| **OpenSSL** (cryptography) | unreasonable | years | ⛔ «never write your own cryptography» is the oldest rule of security | ⛔ **never** |
| **PAM** (login) | impossible | — | ⛔ reading the system passwords by ourselves would mean **losing** account lockouts, SELinux, LDAP, and bypassing the machine's policy (§10.18 says the opposite: REMOTIX **mirrors** the system) | ⛔ **never** |
| **GLib/GIO** (only for D-Bus) | possible | 2-4 weeks (a small D-Bus client of our own, or systemd's `sd-bus`, which is third-party anyway) + suite on the 4 desktops | medium: D-Bus is local (it does not come from the Internet), but it is a format with traps; getting it wrong breaks GNOME or KDE. Gain: −1 direct library and ~9 indirect, no legal gain | 🔸 in the drawer |
| **libpipewire** | unreasonable | months, and to redo at every version | PipeWire's internal protocol **is not stable**: a client of ours would break at every distro update. It is the only door to the screen of GNOME and KDE | ⛔ no |
| **libva** | impossible | — | under libva there is the driver of every card: replacing it would mean writing drivers | ⛔ no |
| **Vulkan loader** | possible | days | the driver could be opened directly; handling of multiple cards and of layers is lost. Zero gain | ⛔ no |
| **libei, libxkbcommon, libwayland-client, libgbm, libdrm** | unreasonable | weeks each | protocols and formats that change with the desktops; xkbcommon alone is a keyboard-map compiler. Zero gain (they are in every distro, MIT) | ⛔ no |
| **libopus** (server) | unreasonable | a quality audio encoder = years of research | worse audio quality, guaranteed | ⛔ no |
| **libopus in the page** (WebAssembly) | possible to go back to the **browser's** decoder | hours | ⛔ the audio holes measured on Firefox come back (D-006). The piece is there **because of a measurement**, that is, it shows what it protects | ⛔ no: the BSD text is shipped and that is it |
| **Wayland protocol descriptions** | impossible | — | they are the «contract» with the compositor: they must be identical to its own | the licence is respected (see below) |
| **Go** and **x/** modules | impossible / unreasonable | — | it is the language | no |
| **Charm** (TUI) and the 12 support modules | possible | 3-6 weeks for a «polished» TUI of our own (§10.31) | medium-low: terminals are a minefield (character widths, colours, keys, Unicode). Today the modules are **copied into the repository and pinned to the version** (`vendor/`): the risk «a malicious update arrives by itself» is already nil | ⛔ no: only a cosmetic gain on the licence list |
| **godbus** | possible | 1 week | low, but no gain | ⛔ no |
| **desktops, labwc, PipeWire service, systemd, D-Bus, kernel, drivers** | impossible | — | they are the **object** of the product. A compositor of our own in place of labwc would also break the rule «niente eccezioni per compositore» | ⛔ no. (Removing labwc/wlr-randr/Xwayland can only be done **by removing XFCE and LXQt**: it is a product decision, not an autonomy one) |
| **browser** | impossible | — | the browser as client is the founding choice (§1.6); the alternative is a program of our own to install on PCs and phones, that is **more** dependencies, not fewer | ⛔ no |

### The LGPL piece: `zkde-screencast` (KDE)

It is the only protocol description licensed LGPL-2.1+ (the other 7 are MIT or similar). From its file a small
table is generated (the names of the protocol's functions) that goes into our binary. The LGPL in a non-free
program asks for two things: **ship the text** and **not prevent** whoever receives the program from modifying and
reassembling that piece. Our licence (§10.39) forbids modifications, **but** its §8 already says that *«nulla
in questa licenza limita i diritti che le licenze dei componenti di terzi danno»*, and the source is public and
buildable. So, in my non-lawyer's judgement, **shipping the LGPL text with the note** of which piece it
concerns **is enough**. There is no need to replace it (and it could not be done: it is the contract with KWin). ⚠ It is the only point of the document
that deserves a «da verificare» on the legal side.

---

### 3. What «autonomo» really means

They are three different things, and each has its price.

### Legal autonomy — «non dover allegare testi di licenza di altri»

- **What achieves it, 100%**: having **no** piece of anyone else's inside our files. That is, rewriting
  QUIC, HTTP/3, the page's Opus decoder, the installer's TUI, and giving up Go. ⛔ Impossible
  at a reasonable cost (see §2).
- **What achieves it, in substance (recommended)**: having **only permissive licences** (already so, except the
  LGPL piece, which is solved by shipping the text) and a **complete, automatic licence file** inside every
  release. Shipping a text file **limits nothing**: none of these licences asks us to open our
  code, nor to allow redistribution, nor to change our licence. MIT, BSD and Apache only ask
  «cita chi l'ha scritto».
- **Price**: a few hours to complete `licenze.py` (libopus-wasm, emscripten, Wayland protocols, LGPL text)
  and put it back into the `.run`. Then zero: the machine generates it at every release, and if a text is missing the release
  stops (the script already exits with an error).
- ⚠ The file `licenze.py` still has «PolyForm Noncommercial (§10.22)» in its header: it must be updated to the
  licence of §10.39.

### Technical autonomy — «non dipendere da progetti che possono cambiare o morire»

- **The truth**: the dependencies that **can** really change under our feet (the desktops, PipeWire, the drivers, the
  browsers and WebTransport) are exactly the ones **impossible** to replace. The replaceable ones (TUI, godbus,
  GLib) are also the most stable and least risky.
- **What really achieves it**:
  1. **few suppliers, solid and permissive** — already done: ffmpeg out, OpenH264 and SVT-AV1 out, libyuv never
     got in;
  2. **pinned versions** where we carry the piece ourselves (ngtcp2/nghttp3 at a fixed version with a checked fingerprint;
     Go modules in the repository) — already done;
  3. **benches that notice at once** when a supplier changes (e.g. the bench that retries the rewrite of the
     nghttp3 settings at every update, DECISIONI §6.4) — already done in part;
  4. **knowing which alternative exists** if a supplier dies: for QUIC, quiche, lsquic, OpenSSL are documented.
- **Price**: low, it is maintenance. The **high** price would be the opposite: every line we write in place of
  a library is one **we** have to follow, forever, alone.

### Distribution autonomy — «non dipendere da quello che la distro ha o non ha»

- **What achieves it**: carrying inside our package (static, like ngtcp2) the libraries we need,
  instead of asking the distribution for them. It is already the rule of DECISIONI §10.6: *if the distro does not have it, or has it
  too old, REMOTIX carries it*.
- **Price**: every library carried inside is a library whose **security updates become ours**.
  If a hole comes out in ngtcp2, the distribution does not save us: we have to rebuild and publish ourselves. Carrying
  OpenSSL, GLib or PipeWire inside would mean chasing their holes (OpenSSL has several a year) and
  risking **not matching** the version the desktop uses (PipeWire and libei must speak the same
  language as the installed service).
- **Insurmountable limit**: the desktops, the drivers with the codecs (patents: §10.6 forbids distributing them) and the
  PipeWire service **cannot be carried inside**. So distribution autonomy never reaches 100%.
- **Recommendation**: stay where we are — inside only what is really missing (today ngtcp2 and nghttp3); all the
  rest from the distribution, which updates it for free for us.

---

### 4. Recommendation

**To do (worth it):**
1. **The licence file, complete, inside every `.run`** — hours. Add: libopus 1.5.2 in WebAssembly
   (BSD-3), the pieces of emscripten (MIT), the 8 descriptions of the Wayland protocols (7 MIT/similar + 1 LGPL-2.1 with
   its text), update the header to the §10.39 licence. It keeps the promise of §8 of our licence.
2. **Correct SPECIFICHE §11.4**: «nessuna GPL; le LGPL della distribuzione collegate dinamicamente sono
   ammesse». Today the sentence «tutte permissive» is not true, and a false rule sooner or later leads to a
   wrong decision.
3. **Keep the watch alive** on ngtcp2/nghttp3: they are the only two pieces whose security updates are
   our burden. We need a way to notice their security releases (even just following their advisories on
   GitHub) and the bench that retries the rewrite of the settings.

**Possible later, not now:**
4. GLib → a small D-Bus client (2-4 weeks). Only if one day GLib gave concrete problems.

**Never to do:**
- rewrite **QUIC/HTTP/3**, the **cryptography**, the **login (PAM)**: they are the server's defences, and there our
  own code would be the weakest point of the whole product;
- rewrite the **PipeWire** client, the **drivers** (via libva/Vulkan), the **input and keyboard** libraries:
  they are contracts with other projects that change, and chasing them is endless work;
- remove the **page's Opus decoder**: it is there because of a measurement, and it shows what it protects;
- carry **OpenSSL, GLib, PipeWire** inside our packages: their holes would become ours.

**In short**: REMOTIX is already «autonomo» in the sense that matters — no licence of anyone else imposes anything on our
code, and the suppliers are few, solid and permissive. The rest of the dependencies is not a debt: it is the work of
thousands of people that defends us for free.
