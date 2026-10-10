<p align="center"><img src="grafica/logo/remotix-logo.png" alt="REMOTIX" width="600"></p>

# REMOTIX

> # ✅ WHERE WE ARE — 25 Sep 2026: PHASE 15 CLOSED, ZERO DEFECTS
>
> The **functional suite** (phase 15) tests REMOTIX with **real** browsers (Firefox 140, Chrome 154, in 4K)
> on the four desktops — GNOME, KDE, XFCE, LXQt — with ~300 tests, each with its own grafted fault.
> **Round 1**: 21 defects (14 of the product, 7 of the tests) ⇒ **clean-up** ⇒ **round 2 with the product
> frozen: 329 PASS out of 329 and 328 faults seen out of 328** (binary `b1443a0b`, page `942f2873`).
>
> ⇒ Everything in `fasi/15-suite-funzionale.md`; the report in `banchi/15-suite/rapporto-giro2.html`;
> the suite is rerun with `bash banchi/11-scatole/11-gancio.sh gira --famiglia suite`.
> ⇒ The next is **phase 16** (stress and capacity).

> # ⏸ THE PROJECT IS ON PAUSE — since 27 Aug 2026
>
> *The user is having surgery. Work resumes in a few weeks.*
>
> ⛔ **There is nothing to recover and nothing left half-done.** This box is for whoever comes back —
> the user himself, or an assistant that remembers nothing of this day — to start again in
> five minutes instead of half a day.
>
> ## ⭐ Where we were, in three lines
>
> **Phase 11 is closed**: there is an anti-regression net of **sixteen checks** that runs on
> four desktops. `[M]` 27 Aug, full round in 2 h 14: **58 green verdicts**, **3 red**, and
> ⭐ **49 grafted faults out of 49 caught**.
>
> ⛔ **The three reds are the same red**: `C1` on kde, xfce and lxqt — the product **can start only
> GNOME** (`src/sessione.c` · `scrivi_dropin()`). ⇒ **It is not a defect to repair: it is the mandate of phase 12.**
> The day `C1(kde)` turns green, KDE is really served.
>
> ## ⭐ The first thing to do when coming back
>
> ⚠ The test machine has its root **in RAM**: a restart takes everything away. ⇒ In this order:
>
> 1. put back the ssh key and **provision** the machine (`src/provisiona.sh`);
> 2. switch the four boxes back on: `bash banchi/11-scatole/11-accendi.sh accendi <gnome|kde|xfce|lxqt>`,
>    then `prodotto` and `server` for each;
> 3. ⭐ **run the net BEFORE touching anything**:
>    `bash banchi/11-scatole/11-gancio.sh gira --famiglia tutto`.
>    ⛔ If the result is not «58 green, 3 red, 49 faults out of 49», **something changed underneath**, and
>    that is looked at before writing a line of KDE. It is exactly the net's job.
>
> ## ⚠ The three things phase 12 inherits, already measured
>
> | | |
> |---|---|
> | ⭐ **a fault of its own** | `fasi/11-…` `fasi/11-la-rete-di-sicurezza.md` §3.6: *every new desktop comes in with at least one fault of its own, invented and run*. Today's acceptance tests are the ones GNOME taught us |
> | ⛔ **KWin cannot be born blind** | `[M]` with `--output-count 0` it makes an output all the same ⇒ the «zero monitors of its own» design **does not carry over unchanged** |
> | ⚠ **the stage dies with the client** | `[M]` the virtual monitor dies with the child's D-Bus connection. On GNOME `C6` measures **green** (the windows are found again); on another compositor it is not a given ⇒ `DECISIONI.md` §4.6-teretvicies |
>
> ## ❓ A question left open, and it is not urgent
>
> The hook is attached to **push** (`pre-push`), ⛔ but the repository **has no remote**: that
> moment never comes, so today the net runs only when someone launches it. ⚠ The proposal on the
> table, not decided: start **at every commit** only the fast part (C10, C12, C13, C15 —
> `[M]` **one second**), leaving the heavy tests on the boxes on command.
>
> ⇒ Everything else is in `fasi/11-la-rete-di-sicurezza.md` §7-bis.19, and the lessons of the day in
> `LEZIONI.md` §1.44–§1.57.

Remote desktop for Linux: a **server**, **no client to install** — a modern browser
is enough — and a protocol of ours called **RCP** — *Remotix Control Protocol*, which travels over
**WebTransport**.

Video is encoded **on the graphics card** with direct libva (H.264, HEVC), with colours also converted
on the card (VA-API VPP). ⛔ **No encoding on the processor**: without a card able to
encode, REMOTIX does not install, and the server declares it at start-up (phase 19,
[`fasi/19-nvidia.md`](fasi/19-nvidia.md), `DECISIONI.md` §10.27). Audio is Opus, with direct
libopus (phase 18, [`fasi/18-senza-ffmpeg.md`](fasi/18-senza-ffmpeg.md)).

> # 📅 HOW IT WAS ON **25 Aug 2026** — *the restart of that time, superseded*
>
> ⚠ ⛔ **Do not start again from here.** The entry point is the box **⏸ THE PROJECT IS ON PAUSE**, at the top of this file. This heading stays because it tells where we were starting from **that day**.
>
> ## ➡️ THE NEXT IS **PHASE 11 — THE SAFETY NET**, and the user decided it
>
> *«Prima è necessario mettere in sicurezza tutto quello che abbiamo sviluppato fino a oggi. Prima di
> passare agli altri DE è necessaria una sessione dedicata per studiare una modalità che impedisca di
> introdurre regressioni.»* — 25 Aug 2026, `DECISIONI.md` §4.6-duodecies.
>
> ⚠ **KDE, XFCE and LXQt shift by one** (phases 12, 13, 14): the phases do not change by a line, their
> place changes.
>
> ## ⭐⭐⭐⭐⭐ AND ON THE NIGHT OF 25-26 AUG 2026 **ACCEPTANCE TEST A PASSED**
>
> `[M]` The net, pointed at the code of 25 Aug inside a box, on **six new users**,
> **turned red by itself** on the session that is born blind: ⛔ **3 out of 6 born BLIND, 0 with a
> monitor**, and nobody had told it where to look.
>
> ⭐ And before that, **step 0** closed the heaviest `[?]` of the design: **the container
> holds the system — 18 green out of 18**, with the **real** graphics card inside (encoder `iHD`,
> 3 H.264 profiles) and **two declared permissions** instead of a `--privileged`.
>
> ⭐⭐ **And the second box already exists, with PLASMA inside**: the **very same checks**, without
> a line changed, give **18 out of 18** there too ⇒ the net **is not made to measure for GNOME**, and
> now it is measured instead of hoped. ⛔ And Plasma immediately asked for **two things GNOME did not
> ask for** — a group that did not exist and a permission without which KWin does not start at all: ten
> minutes now, half a day and a wrong diagnosis inside phase 12.
>
> ⚠ **And four faults came out of the work itself**, all written down: the graphics card group
> that fell back **silently** to software · a library **with the same name and something else
> inside** (the server started and died at the first client) · and **two bench defects**, one of
> which gave **three false reds**. ⇒ `LEZIONI.md` **§1.41, §1.42, §1.43**.
>
> 📖 **The phase document has been open since 25 Aug 2026**:
> **[`fasi/11-la-rete-di-sicurezza.md`](fasi/11-la-rete-di-sicurezza.md)** — the complete design,
> ⭐ written **also for whoever does not know the project**: **§2** the constraints decided by the user, **§4** the
> list of checks with *where it starts* and *what it looks at*, **§7** the work plan (⛔ **a single
> box first, not four**), **§8** the open questions.
>
> ⭐⭐ **And the acceptance test of that phase is already written**: the net must be pointed at today's code and
> ⛔ **must turn red on the «session that is born blind»** — without anyone having told it where to
> look. **If it does not catch it, it is not a net: it is a ritual.**
>
> ---
>
> ## ✅⭐⭐⭐ PHASE 10 IS CLOSED — *multi-tenant and the budget*
>
> **Closed on 25 Aug 2026, on the user's verdict**: *«sono soddisfatto — riprodotto audio e
> video su una connessione del 1990; non credo che si possa chiedere di più»*. ⭐ A **4K video**
> inside the remote desktop, with his tablet's bandwidth throttled to **10 Mbit/s**, that is **a third
> of the declared floor**. ⇒ And the yardstick that came out of it is `DECISIONI.md` **§4.6-decies**: below the
> specifications **sharpness** is lost, ⛔ **not smoothness and not synchronisation**.
>
> 📖 **[`fasi/10-multi-tenant-e-il-budget.md`](fasi/10-multi-tenant-e-il-budget.md)** — the **summary**
> at the top, **§5** the cures, **§6** the measurements, **§8** the two decisions that remain.
>
> ### ⭐⭐⭐ What the phase found — **and it was not what was believed**
>
> ⇒ ⛔⛔ **The budget is not one of encoding: it is one of composition**, and what saturates it is the **desktop's
> compositor**, not `remotix` — that is **something that is not ours**.
> `DECISIONI.md` **§4.6-nonies** corrects §4.6. ⚠ The measurements of the time (and how many sessions the
> test machine held, `DECISIONI.md` §4.6-septies) are in `fasi/10-multi-tenant-e-il-budget.md` §6:
> they apply to that hardware and to the product from before phase 18, and they are not guarantees.
>
> ### ⭐⭐⭐⭐ AND THE MOST USEFUL THING OF THE DAY IS NOT A NUMBER
>
> ⛔ The director tried the product and said three times **«Firefox non funziona»**, until he
> stopped. ⇒ **It was the browser's profile that was not being born**: on his machine `~/.cache` points to
> `/tmp` — ⭐ **a deliberate choice of his**, not a fault (`DECISIONI.md` §4.6-undecies) — and the
> **first** user who opens the browser takes `/tmp/mozilla` with mode `0700`.
> ⭐⭐ *A configuration that on a machine with ONE user does no harm, and that on the **ten
> users we create** blocks nine* — ⛔ **the defect is ours, not his**: it is our
> `useradd -m` that makes them all be born in the same place. And it is exactly the theme of this phase.
> Cured in `src/provisiona.sh`, ⭐ **without touching anything in the system**: a `.cache` of their own
> only for the users we create.
>
> ⛔⛔ **And phase 9 had closed it with a wrong ✅** (`fasi/09-la-qualita-e-la-degradazione.md` §20.1-ter, now **refuted**): the check
> that *«closed the question»* ran from a user **in the same condition**.
> ⇒ `LEZIONI.md` **§1.38** — *a check that shares the factor it must exclude checks
> nothing*.
>
> ⭐ **And now there is the witness that makes you SEE** — `banchi/10-f1-testimone.py`, a PNG of the remote
> desktop, calibrated, with the third outcome **«I did not look»** distinct from «it was black» (`LEZIONI.md`
> §1.37).
>
> ### ⭐⭐ AND THE PRODUCT HALVED THE BANDWIDTH BY ITSELF
>
> Same scene, throttled wire: frames per second **stay the same**, bandwidth **drops**,
> ⭐ **wire queue EMPTY** — that is the scene moved as before. ⇒ ⭐ **It did not slow down: it
> compressed more.**
>
> ### ⛔⛔⛔ AND ONE DEFECT STAYS OPEN, DECLARED — **the session that is born blind**
>
> `[M]` On a **newly born** session Mutter announces no `wl_output` ⇒ ⛔ **no
> application can open a window**: Firefox stays alive and does not paint, the compositor is
> **still**, the stage delivers **zero frames**. ⚠ It is **intermittent**: `provanic3` had the
> monitor **2 times and then 6 times not**. ⇒ `fasi/10-multi-tenant-e-il-budget.md` **§7.4**.
>
> ⭐ **It does not touch the capacity tests** — those were done on sessions that really drew.
> ⛔ **It touches delivery**: today one new session in three or four is born blind.
>
> ### ⚠ AND TWO DECISIONS WERE LEFT UNTAKEN — the defaults apply
>
> ⛔ **QVBR stays OFF** and the factory numbers stay **ceiling 10, reserve 0.5**.
> ⭐ And the phase brought a new argument: **QVBR is not needed for a single user** — the regulator already
> does its job — ⛔ **it is needed when there are ten**, and that round was not done (the clients
> ran on `lo`: the wire is **counted, not tested**).
>
> ---
>
> # ✅ AND BEFORE THIS ONE — **24 Aug 2026**
>
> ## ✅⭐⭐⭐ PHASE 9 IS CLOSED — *quality and degradation*
>
> 📖 **[`fasi/09-la-qualita-e-la-degradazione.md`](fasi/09-la-qualita-e-la-degradazione.md)** — the
> summary at the top, and **§17-§21** the part that counts.
>
> **Closed on the user's verdict**: *«il prodotto cambia in meglio; questa fase era per rendere
> più solido il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli»*.
> ⭐ It is the **criterion**, not a comment: the goal was not to **save** the experience on any
> network — it was **not to make it worse, not to lie, and not to pretend that a broken line is a slow line**.
>
> ## ⭐⭐ HE CORRECTED THE TARGET HIMSELF, WITH THE PHASE OPEN
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti che
> perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter»* (`DECISIONI.md`
> §3.1-ter). ⇒ And it was the right quantity: **on bandwidth the product did not give way; on a dirty wire
> it did.** ⛔ The bandwidth floor moved to **30 Mbit/s** (§3.1-sexies) and counts as a **premise**.
>
> ## ⭐⭐⭐ THE LADDER THAT CLOSES THE PHASE — through his eyes
>
> | real loss | without cures | with cures |
> |---|---|---|
> | 1 % | *«mi sembra ok»* | — |
> | 5.6 % | *«è tutto fluido»* | — |
> | **10 %** | ⛔ *«bloccato»* | ⛔ *«bloccato lo stesso»* |
>
> ⇒ **Above a certain loss the degradation ladder has nothing more to offer**, and the only
> honest answer is **declaring the line dead** (`DECISIONI.md` §3.1-quater) — the decision the user took
> **before** having that number.
>
> ## ⭐ THE FIVE CURES ARE ON — and the healthy line pays nothing
>
> | cure | default | turned off with |
> |---|---|---|
> | audio silence | **on** | `--niente-audio-silenzio` |
> | threshold on the video queue | **100 ms** | `--sgombra-soglia-ms 0` |
> | rate regulator | **on** | `--niente-ritmo-adattivo` |
> | dead line | **on** (stall 5 s · silence 10 s) | `--niente-linea-morta` |
> | eviction of the ghost | **15 000 ms** | `--sfratto-ms 0` |
>
> **The test that could have made us withdraw everything is green**: on a healthy line, with the defaults, the same
> frames as with the cures off, zero keyframes in both. ⭐ It is the wound for which v1
> lost this phase — *the numbers improve and the experience gets worse* — and it was looked for on purpose.
>
> ## ⭐⭐ THE THREE FACTS THAT COUNT BEYOND THE PHASE
>
> 1. **The defect does not start where it is seen.** The keyframe spiral starts at the **first lost
>    packet**; the drop the user **sees** comes **much later**. ⇒ A bench that looks only at
>    frames/s gives **green** well beyond the point where the defect has already started.
> 2. **The trigger has a constant risk**, and once on it does not switch off. ⛔ Benches run for
>    a few tens of seconds, **sessions last hours** ⇒ every measurement taken near the
>    edge **underestimates**, and not by a little.
> 3. **Disorder gets mistaken for loss — and it came back to bite us.** The first «dead line»
>    was tuned on `pkt_lost`, and a line that **holds** declared **more** of it than one that **does not
>    hold**. Redone on the **output stall** (5 s).
>
> ## ⚠ AND THE COUNT OF METHOD ERRORS — the most useful part
>
> `[M]` **Nine defects in the benches**, all of the form *«silence instead of red»* (one made
> a bench read the numbers of the **previous** bench) · **three tests that did not bite**, discovered
> **by counting the packets** · **two conclusions withdrawn** (the applications that «did not arrive» — there
> was nobody watching; and the clapperboard test declared «void» and disproved by the **third**
> judgement) · **two false premises** inherited and corrected (the user was never on **PCM**; the
> audio delay measured then does not reach his ear).
>
> ## ⏳ WHAT REMAINS OPEN
>
> ⛔ ~~**Firefox does not start on the test machine** — `[M]` even outside REMOTIX, headless and
> without Wayland: **it is not ours**, but it blocks the browser tests (`fasi/09-la-qualita-e-la-degradazione.md` §20.1-ter)~~
> ⭐⭐ **CLOSED on 25 Aug 2026, and the cause was another one**: on this machine `~/.cache` is a
> **link to `/tmp`** — ⭐ **a deliberate choice of the user**, `DECISIONI.md` §4.6-undecies — and the
> **first** user who opens the browser takes `/tmp/mozilla` with mode `0700` ⇒ **for all the
> others the profile is not born**. Cured in `src/provisiona.sh`, and `[M]` **Firefox renders a page
> in the remote desktop**.
> ⚠ *And the conclusion «it is not ours» was wrong in the worst direction: the configuration is his and is
> perfectly fine, ⛔ **the defect is ours** — it is our `useradd -m` that makes ten tenants be born
> all in the same place.*
> `fasi/10-multi-tenant-e-il-budget.md` §5.10 ·
> ⭐ ~~the **`AV`** half of synchronisation is not re-measured (it needs that browser)~~ ⇒ **JUDGED on 25
> Aug 2026**, on a **4K** video with bandwidth at **10 Mbit/s**: *«audio e video fluidi e in
> sync»*. ⚠ The audio delay measured then stays `[?]` — that was a number, this is a judgement ·
> ⚠ `rcp.c` still says *«rifiutati da ngtcp2»* where now they are *«buttati perché il filo era muto»* ·
> `[?]` the congestion algorithm is **CUBIC** and **has never been chosen**: the contrast test
> was not done because no option exposes it.
>
> ## ➡️ THE NEXT IS **PHASE 10** — multi-tenant
>
> ⭐ And this phase left it two things: the **degradation ladder**, which is the way to fit
> more people on the same machine (*«yes, smaller»* instead of *«no»*), and ⛔ the **network budget**
> never measured — ten sessions × 30 Mbit/s are **300 Mbit/s on the server's wire** (`DECISIONI.md` §3.1-bis
> point 2).
---

> ## State as of 13 Aug 2026 — ⭐⭐⭐ **PHASE 2 IS CLOSED: the desktop is inside a tab**
>
> ✅ **Closed on 13 Aug 2026, on the user's verdict**, who reopened
> `https://192.168.0.2:7561/` **as himself** after the rescaling cure and decided to
> close **in front of the list of what remains open**.
>
> ⭐⭐ **And this time the verdict is not just a sentence: the pixels were measured.** The server
> declares `vista=2545x927` at 08:45:44 UTC; the screenshot, eight seconds later, has the painted area
> **927 px** high and **1648** wide — ratio **1.7778** against a 16:9 of **1.7778**. ⇒ The page rescales
> to the view **without distorting by a pixel**: `SPECIFICHE.md` §6.1 measured on the glass.
> ⭐ The provenance is in `fasi/rapporti/GIUDIZIO-13-agosto.md`.
>
> ⛔ **And it closes with SEVEN things declared open**, put in front of the user **before** he
> decided — because a verdict given without knowing what is missing is an approval in the dark. They are
> in [`FASI.md` §02-primo-fotogramma](FASI.md#02-primo-fotogramma). ⚠ *They were also in the box
> «RESUME FROM HERE — 13 Aug» of this file, pruned on 16 Aug 2026: see the note at the
> bottom of this box.*
>
> ⭐ **The bench catalogue is full: 15 out of 15**, and it is the **project**'s count — the two copies of the
> register merged and mirrored, 90 rounds, *no line lost, none invented*.
>
> ---
>
> ## State as of 11 Aug 2026 — ⭐⭐ **PHASE 1 IS CLOSED**
>
> ✅ **Closed on the evening of 11 Aug 2026, on the user's verdict**: *«Va bene, la stretta di mano
> funziona: fase 1 approvata»* — after opening `https://192.168.0.2:7448` **from the laptop**, in
> **Chrome**, and reading *«Ammesso, sessione nuova, tela 1920×1080, desktop sconosciuto»*.
> ⭐ The measurement has a **provenance on disk**: `fasi/rapporti/GIUDIZIO-11-agosto.md`
> — the scene, the fingerprints, the server's log verbatim. ⛔ And the phase closes **with some work
> declared open**, which is the honest form: `PIANO.md` §0.2 has it close on *«a measurement judged
> by the user, not a complete document»*.
>
> **The product exists**: `src/`, the server in C that a real browser opens. Bench
> written and **reviewed before the product**: 44 findings — **38 `[R]`, all cured**, and **6 `[?]`,
> of which two still open by name** (R3.25 the sign of the wheel on more than one compositor ·
> R3.26 the PAM stack for a user other than the owner of the process). ⭐ **R3.27 — the instant from
> which the first ceiling starts — has been closed since 11 Aug 2026**, and bench **B6** closed it with two
> answers. ⚠ *This line said «44 findings, 38 `[R]`, all cured», and added the 38 to the 44: a
> `[?]` is not cured, **it is measured** (`REVIEWER.md` §4). Corrected on 10 Aug 2026, finding **R11.19**.*
>
> ⛔ **And a fourth adversarial review, on the night of 10-11 Aug, through four lenses**: the benches
> (**30** findings), the product against the arbiter (**15**), the documents (**17**), the seams between the
> five agents (**10**). ⛔ **None of the four is green**, and the verdicts are in
> `fasi/rapporti/R12-A/B/C/D`. ⚠ *And the verdict on the documents found a process cause that
> is worth more than half of its findings: the `.md` files had been closed at **22:40**, the code went
> on arriving until **00:36** — that is the page that said «start again from here» was already
> false at the moment of delivery. This page was realigned on 11 Aug 2026, **with the code
> still**.*
> ⭐ **Bench B2 closed `DECISIONI.md` §6.4: the QUIC library is
> `ngtcp2`+`nghttp3`** — with a bench, not on paper, and with the other three each eliminated by a
> measurement.
>
> ### What is measured `[M]`
>
> | | |
> |---|---|
> | ⭐ **the trust model holds** | a WebTransport session to a **13-day self-signed P-256** certificate, with the fingerprint published in the page and **no warning**: **Chrome 151** and **Firefox 140**. `RCP.md` §4.1-bis goes from `[S]` to `[M]` on **two engines** |
> | ⭐ **`ngtcp2` and `quiche` pass the SNI criterion** | **10 Aug**: their example servers serve the certificate to whoever **sends no SNI**, and ⛔ **the fingerprint received matches the file's** — a handshake that succeeds is not enough. ⇒ **the criterion no longer separates the two candidates** |
> | ⭐ **the `lsquic` diagnosis closes** | without SNI: *«fail certificate lookup»*; **with** SNI: *«looked up cert for remotix.prova»*. ⛔ The defect is SNI and nothing else — **the elimination holds, now on a whole test**. And it stays at the end of every run as a **negative control**: it proves the probe can see a refusal |
> | ⛔ **and `quiche` brings a cost that has nothing to do with QUIC** | **0.29.3 demands `rustc` 1.88** and Trixie has **1.85**: **0.28.0** is measured, chosen by the bench. Choosing it means staying there until Debian updates, **or** carrying a Rust toolchain outside the packages. `ngtcp2` does not raise the question |
> | ⭐⭐ **the minimal server on `ngtcp2` exists, and a REAL BROWSER opens the session** | **Chrome 151** and **Firefox 140**, both `APERTA` on `https://192.168.0.2:7447/rcp/1`, fingerprint published, **no warning**, `"ciao"` coming back identical. ⛔ And `/rcp/9` **refused with 404**, as `RCP.md` §2.2 requires |
> | ⭐ **and now «how much glue» has a number** | the WebTransport layer on `ngtcp2`+`nghttp3`, **alone**: **553 lines added — 373 of code, 134 of comment, 46 blank** `[M]` **10 Aug, 16:30**, with `git diff` on a clean tree and not estimated. ⚠ The succession of the day's measurements is in `DECISIONI.md` §6.4, box «How many lines are ours, and at what time» — it is not copied here |
> | ⭐ **the six properties of B2: 6 out of 6** | ceiling 30 s · datagram · credit of **16** uni streams · migration **not** disabled · **no 0-RTT** · `allowPooling: false`. ⛔ **Read from the peer**, not from the server's log — and precisely because of this they found **two defects without a symptom**: the server offered 0-RTT (which §2.3 forbids) and granted 3 unidirectional streams instead of 16 |
> | ⭐ **and the ceiling can be changed** | with `--timeout=10s` the peer reads 10 000 ms: **B3** will be able to tell the protocol's ceiling from the transport's |
> | ⛔⭐ **and `quiche` does not reach WebTransport from C** | it declares **4** settings on the wire and **neither of the two WebTransport ones**. `h3::Config::set_additional_settings` **exists in Rust and not in the FFI**, and the trick used on `ngtcp2` is not there: a C application never sees those bytes. ⇒ **§6.4 is closed** |
> | ⭐ **the arbiter does not fall** | `aioquic` 1.2.0 carries WebTransport ⇒ B9's **test client** is possible. ⚠ But it speaks **draft 02**, and the browsers **07**: the server sends both declarations, or half the tools would say yes for the wrong reason |
>
> | ⭐⭐ **RCP speaks, and the arbiter confirms it** | **B3**: `CIAO`→`ECCOMI`→`CREDENZIALI` (PAM)→`AMMESSO`→`ATTACCA`→`SESSIONE`, on **two connections** — and ⛔ **the traces are declared conformant by B4's validator**, a third program written by reading only `RCP.md`. The **fixed second** of §4.4-bis measured on the wire |
> | ⭐ **B4: the validator is certified** | **13 out of 13** `[M]` **10 Aug, evening** — seven broken recordings each accused **on the byte declared in advance**, the conformant one accepted, and ⛔ **the validator's four outcomes all covered**: conformant · non-conformant · broken recording · *nothing to judge*. ⚠ *It said «7 out of 7» with only two outcomes: «I have nothing to judge» and «conformant» had the same exit code, finding **R7.4***. ⭐ And at its first run it found **a contradiction in `RCP.md`**: §4.3 forbade a character that §4.3 itself uses |
>
> | ⭐⭐ **B3: five rounds out of five** | 1st · 2nd after closing · **2nd while the 1st is alive ⇒ `GIA_ATTIVA_REMOTA`** for both roads of §3.1, and the first is not ousted · ⭐ **the 2nd after the silence**, 35 s at `max_idle_timeout` 120 — refused at +6 s, **gets in at +35 s**, and the first one's connection is **still alive**: it was the server that freed the slot, not QUIC · ⭐ **the 3rd with the rotated certificate, now FULL** `[M]` **10 Aug, 18:5x**: the page picks up the new fingerprint and opens on both engines, ⭐ **and the server really answers** — `CIAO` → `ECCOMI` read on the wire — ⛔ and with the old one both **refuse**. ⚠ *The first draft of this round sent the word `ciao` expecting the echo of the WebTransport layer: a test born when the server did not yet speak RCP. With RCP grafted in that word is not a message, the server was waiting for the rest of it and the page stayed hanging — and **that** was the morning's «the stream did not work», not the certificate* |
>
> | ⭐⭐ **B5: forty-four violations out of forty-four** | unknown type · length too long and too short · **4 GiB announced** · over 1 MiB · wrong state · version · capability names and values · credentials out of range · odd and out-of-limits canvas · malformed layout **against** unknown layout (`SESSIONE_NON_SERVIBILE`) · second bidirectional stream · three channels in the wrong direction on unidirectional streams. ⛔ The right reason every time, **for both roads of `RCP.md` §3.1**, and after **each** a new connection reaches `ECCOMI` |
> | ⭐ **and the five cases that MUST pass** | `hevc,vp9` → `hevc` is chosen and **the discard is written** · **view 300×801** and **1×1** (`RCP.md` §7.1) · `BANCO_MARCA` with the feature off → `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` **without closing** · `ritardo_ms = 20000` → `RITARDO_FUORI_LIMITI`. ⛔ Without them, «the server closes on everything» would give **36 green out of 36**. ⚠ *The cases that MUST pass are **eight**, not five, and B5's 44 cases are **36 violations + 8 expected greens**: the final line said «44 out of 44», which is true by construction (finding **R7.14**)* |
> | ⭐⭐ **B5 found a defect no other bench saw** | the **per-address** counter of §4.4-bis was keyed on the origin **with the port**, and with a single attempt per connection the port changes every time: that counter **was always 1**. Code that was there, looked right, and did nothing. Now at the **sixth** attempt `TROPPI_TENTATIVI` triggers — even for the **right** password. ⚠ *The **sixth** was that day's rule: since the evening of 10 Aug the ban triggers at the **fourth** (`DECISIONI.md` §1.9), and the measurement stays written as it was because it carries the date of the rule it measured* |
> | ⭐ **and a second contradiction in `RCP.md`** | §2.2 says that `CIAO(2)` on `/rcp/1` is `VERSIONE_INCOMPATIBILE`; §9 says to choose *«the highest that does not exceed the `CIAO`'s»*. **Different bytes for the same input.** §2.2 wins; §9 now names it. ⚠ *The cure of 10 Aug pointed to §2.4, which is «The port» and names neither paths nor versions: corrected the same day, finding **R11.2*** |
>
> ### ⭐⭐ THE CLOSING — the evening of 11 Aug 2026
>
> #### ⭐⭐ THE CERTIFICATIONS: **12 out of 14**, and this morning they were 3 — on a code that no longer exists
>
> ⚠ *And tonight they are **7 out of 14**: not because any failed, but because the farewell cure
> changed `rcp.c` and `RCP.md` under seven of them. The updated count, with the names, is two boxes
> further down.*
>
> ⛔ **And the denominator changed in the evening, so the two numbers do not subtract.** B12's
> catalogue went from **12 to 14 entries** (**P1** and **P5** came in, the two benches that look at the
> product), and ⚠ **the «14 benches» and the «14 entries» are not the same 14**: the catalogue includes
> **B10** and excludes **B12**, which does not certify itself. Counted properly: the certifiable benches are
> **13** and the entries with a bench behind them are **13** — ⭐ two sets that now **coincide**, whereas
> before tonight they were twelve and twelve **different ones**, that is the count added up by counting different things.
>
> ```
> banchi nel catalogo: 14
> 12  certificati e valgono oggi   B2 B3 B4 B5 B6 B7 B8 B9 B10 B11 B13 C2
>  1  non riverificabile da CHUWI  P1   (its line names a file that lives only on the server)
>  1  provato e NON certificato    P5   (for a single point, and on a single engine)
>  0  mai provati                  —    ⭐ the line that was not there this morning
> ```
>
> ⛔⛔ **AND THIS COUNT EXPIRED A FEW HOURS AFTER BEING WRITTEN — `[M]` the night between 11 and
> 12 Aug 2026, `01-b12-guasti.py --registro`:**
>
> ```
> banchi nel catalogo: 14
>  7  certificati e valgono oggi   B2 B4 B10 B11 C2 P1 P5
>  7  certificazione SCADUTA       B3 B5 B6 B7 B8 B13 (rcp.c è cambiato) · B9 (RCP.md è cambiato)
>  0  non riverificabili           —   ⭐ P1 and P5 can now be re-verified from CHUWI too
>  0  provati e NON certificati    —
>  0  mai provati                  —
> ```
>
> ⭐⭐ **And the seven were RE-RUN the same night — `[M]` 12 Aug 2026, `--registro`:
> 13 out of 14, zero expired, zero not re-verifiable.** Certified again: **B7** (`0→1→0`, 1m11s) ·
> **B9** (`0→3→0`, on CHUWI) · **B3** (`0→2→0`) · **B5** · **B6** · **B8** (`5→1→5`).
> ⛔ **B13 stays out, and it is the only one of the fourteen.**
>
> ⛔⭐ **And the thing worth more than the six lines: the first round REFUSED to start, in half a
> second.** `01-b0-terreno.sh` said *«`examples/rcp.c` NON è `rcp/rcp.c`: il server misura una
> versione che nessuno sta leggendo»*. ⇒ The seven were not only **expired**: they were
> **unrepeatable**. The cure had updated `rcp/rcp.c`, but the **graft**'s server — the one that
> six of those benches query — was still compiled on the morning's code. Re-launching them without
> looking would have written six log lines with tonight's date **on the code from before**.
> ⭐ Cured: `rcp/rcp.c` propagated into `b2/ngtcp2/examples/rcp.c`, `ninja bsslserver`, terrain
> re-measured (14 out of 14). ⚠ **And no tool does that propagation** — the benches only *check*
> it: it is the reason why the misalignment stayed there half a day.
>
> ⭐⭐⭐ **AND THEN B13 CAME BACK IN TOO: `[M]` 12 Aug 2026, `14 su 14`, zero expired, zero not
> re-verifiable, zero never tested.** The cure was not touching a number: it was **changing
> scene**. `01-b13-sera-certifica.sh certifica` redoes the same cycle with the **same fault** but
> against the **PRODUCT** on 7481 — which really serves the page — and there `B13.4` has a defendant:
> **healthy 3 → fault 1 → healed 3**, with the mark «LE IMPRONTE COMBACIANO» counted **0 · 1 · 0**
> on the three output files. ⇒ The healthy round comes out **3**, that is exactly the expected value the catalogue
> declared: **the number was right and the scene was wrong.**
> ⏳ **What remains**: `01-b12-lancia.sh` has no way of being pointed at the product. Until it
> has one, the two tools measure two different scenes and **only one of the two can certify B13**.
>
> ⛔ **B13, why under B12 it does not certify — and the blame is not the product's.** Its healthy round comes out **1** where the catalogue
> declares **3**, and B13's numbers **are not a count**: `0` = six properties out of six pass,
> `1` = **there is at least one RED property**, `3` = no red, but declared `[?]` holes remain.
> The red is **B13.4**, *«la pagina servita in TCP»*, which gives `[?]` if **nobody** listens on TCP and
> **red** if someone listens and the page does not load (`SSLError: WRONG_VERSION_NUMBER`).
> ⚠ **And who was listening has not been established**: once the round ended, there is nobody on TCP 7447 any more, and
> a second probe did not catch it again. ⛔ So B13 stays **NOT CERTIFIED**, and it is certified the
> day `B13.4` is measured where the page **exists** — that is against the **product**, as
> it was already closed (box «B13 — certified», 200 and 31 083 bytes) — not the day someone
> rewrites the number.
> ⚠ *And for half an hour I rewrote that number myself, bringing it to **1**, having read «1» as «a
> single fault» instead of «there is a red». It was put back to **3** and the reason is written beside it
> in the catalogue: with a red already present the fault can no longer change the outcome, and the bench
> would become **uncertifiable by construction** — `[M]` healthy 1 · fault 1 · healed 1.*
>
> ⭐ **And the cause of the expiry is not an oversight: it is the farewell cure.** `DECISIONI.md` §1.12 — the out-of-phase
> cure decided by the user — touched **`rcp.c`** and **`RCP.md`**, that is the files those
> seven certifications rested on. ⇒ **Curing the product makes the certifications that
> looked at it expire, and it is exactly what the register must say**: the line is valid for those bytes, not for
> these. ⛔ *«Expired» is not «failed»*, and it is not «clean» either: those seven **must be re-run**,
> and until they are they count as **not certified**.
>
> ⚠ And the two that were added to the green are not the same thing: **P5** was certified
> tonight with the three rounds; **P1** was already certified since the afternoon, and what changes is that now
> its line **can be re-verified from CHUWI** — before, the file it names could not be read from here.
>
> ⛔ **And it must be said what counts as a guarantee, because it is not the same number.**
> `banchi/01-b0-terreno.sh` — the check that looks **under** the benches, born today because **twice
> in one day** a bench was green on a terrain that was not the one we believed — came
> into the round at **14:14**. Eight of the first nine certifications are from the earlier hours.
> ⇒ **As a count it is 12; as a guarantee «certified on a verified terrain» it is the evening's
> rounds.**
>
> #### The afternoon's count, kept because it explains where we were starting from
>
> ⛔ **The first thing I found this morning is that the count had already expired.** The register carries,
> beside each certification, the fingerprint of the `rcp.c` it was made with: it was `d839839f…`, and
> today's code is `cb7af778…`. ⇒ *«3 out of 12»* were three on a code that no longer exists.
>
> | | |
> |---|---|
> | ⭐ **certified today** | **B2 · B3 · B4 · B5 · B6 · B7 · B9 · B11 · C2** — all on the current code |
> | ⛔ **tested and NOT certified** | **B8** · **B13** — both on gaps with a name |
> | ⛔ **never tested** | **B10** — the bench does not exist, but ⭐ **the second user is there now** |
>
> ⚠ **The number depends on where you ask for it**: the register lived in **two copies**, one per
> machine. Merged in `banchi/01-b12-registro.jsonl` (the versioned one). ⛔ But the server says
> **8** and the laptop **9**, and both are right: on the server `RCP.md` is not there, so B9 cannot
> be *re-verified* there — and the tool writes «non so» instead of rounding.
>
> #### ⭐ WHAT WAS DONE ON THE EVENING OF 11 AUG — the five points of the list
>
> | # | | outcome |
> |---|---|---|
> | **1** | ⭐ **B8 — certified**, `[M]` 13:46 UTC, graft, port 7471: **`5 → 1 → 5`**. The round finally covers the **whole sequence** — two lives of the server (*«ban caricati: 1»* from disk, **I7**), the ban page (200, *«tentativi esauriti»*, 12h 0m), the unblock on **a real ban**. ⛔ **The healthy expected value is 5, not 0, and it is written in the catalogue before the round**: it is the outcome *«il ban passa, ma le mediane si separano»*, and it is granted only because the defendant is **measured** and it is **PAM** | ✅ done |
> | **2** | ⭐ **B13 — certified**, and the fragment cure **holds**: new round of the probe, **zero logs with the password in them**; then **33 files** thrown away with the trace in `banchi/01-b13-buttati.jsonl`. ⭐ **`B13.4` closed against the product** (200, 31 083 bytes, current fingerprint). ⛔ `B13.3` and `B13.5` remain | ✅ done |
> | **3** | ⭐ **B10 — the bench exists, and it certified itself in the same round**: `prova2` reaches `SESSIONE` on the **product**. ⭐⭐ And **it closed the `[?]` R3.26 with a measurement**: the PAM stack judges another user **only if the process is privileged** | ✅ done |
> | **4** | ⭐ **Done where it bit, and stopped on purpose**: `gira()` now **calls** `01-b8-lancia.sh` instead of rewriting its sequence (as it already did with C2). ⛔ Extending it to the others tonight would have **invalidated nine certifications** to redo them in a time that was not there | 🔸 half |
> | **5** | ⭐ **P1 and P5 are in the catalogue**: 12 entries → **14**. **P1 certified**; ⛔ **P5 not** — and see the row below, which is the thing that counts | 🔸 P5 not |
>
> #### ⛔⛔ THE PRODUCT DEFECT FOUND AT THE END OF THE EVENING — and earlier it had been **acquitted by mistake**
>
> **The defect**: when the browser tab is closed, the page **sends no `CONGEDO`**, where
> `RCP.md` §8.1 requires it unconditionally. The slot goes away after **30 seconds of silence**.
> ⛔ **On both engines.** The cause has a name: `src/pagina.html` · `TASTI_ULTIMO()` resets
> `congeda_corrente` **one millisecond after `SESSIONE`**, and the `pagehide` handler (line 331) is
> **dead code**. ⭐ **The cure is three lines and it is written** in `FASI.md` §01-filo-nudo, box
> P5.
>
> ⭐⭐ **And at the end of the same evening it was APPLIED and RE-MEASURED**, `[M]` **two rounds per
> engine**: `pagehide` fires with the guard **PRESENT**, `congeda()` is called, and **both**
> roads of `RCP.md` §3.1 reach the server with reason **`0x01`** — on Firefox **and** on Chrome, where
> the close with code `0x0` that `RCP.md` §3.1 forbids **no longer appears**. The anchor of `congeda_corrente`
> is no longer *«the attempt is over»* but ***«the session is over»***: it is reset by `wt.closed`, and only
> if the reference is still its own. ✅ **And it is a product change after the closing of
> phase 1, so it was put on record**: `DECISIONI.md` §1.12 — the cure is **out of phase**, ⛔
> **phase 1 does not reopen** and the certification stays **12 out of 14**, ⭐ and the cure **is not rolled back**,
> because it is measured with the same rigour as the phase. Phase 2 inherits the **re-certification of P5**.
>
> ⛔⛔ **And the story of how it was almost lost is worth more than the defect.** In order:
>
> 1. **P5 accused the product** of not saying farewell — ⛔ but it pressed `ctrl+w` **on a display that was not
>    the fake screen**: an accusation for **a gesture never made**. A bench defect, a real one.
> 2. **The arbitration that followed ACQUITTED the page** — ⛔ **and it was wrong**: it counted the line
>    *«la pagina ha chiuso la sessione, motivo»* **without looking at the reason**, and the reason was
>    `0x0`, that is **Chrome's teardown, which `RCP.md` §3.1 forbids**. A violation counted as a farewell,
>    and printed as *«⭐⭐ la pagina fa quel che `RCP.md` §8.1 le impone»*.
> 3. ⭐ **The third measurement really attributed it**, with an instrumented copy of the page and a
>    carrier that does not go through WebTransport: `pagehide` **fires**, and there is nothing left to
>    call. **Gecko is cleared by measurement** — the same `congeda()` called from there delivers
>    both roads of `RCP.md` §3.1.
>
> ⇒ ⛔ **The two engines were not opposite: it was the same defect seen through two teardowns**, and on one the
> bench tripped over its own counter. ⚠ **And the server was saying it**: the line
> `⛔ VIOLAZIONE `RCP.md` §3.1 … A verbale va ERRORE_PROTOCOLLO` is written by it, and it was in the log.
>
> #### ⭐ And an accusation against the product that instead really belonged to the bench
>
> **B8** wrote *«la pagina del ban non si carica»* — that is **exactly the silence that `RCP.md` §4.4-bis
> forbids** — on a server that does serve the page: `leggi_pagina()` spoke **TLS to a graft that
> answers in clear**, and the cause was **the cure of the day before**, written for the product.
>
> ⇒ With B3, that makes **three times in this phase** that the red was pointed at the wrong defendant — and once,
> tonight, that the **green** was. ⭐ *The form of `LEZIONI.md` §1.9 applies both ways, and the
> green is the one that does not come back to show itself.*
>
> ⭐ **And there is a new rule worth more than any single point**: *whoever writes a bench certifies it
> in the same round*, or the count never goes down. Today two came in without anyone noticing.
>
> #### ⭐ THE NEW TOOLS, and they serve the next round
>
> - **`banchi/01-b0-terreno.sh`** — ⛔ *is the server the one I believe?* 14 checks, it runs **before**
>   every certification, and B12 refuses if it does not hold. ⭐ Born because **twice today** a bench
>   was green on the wrong terrain, and once I caught it **by chance**.
> - **`banchi/01-b0-chiamate.py`** — *does whoever calls a bench pass it what it demands?* Three times in
>   two days a caller had stayed behind on a mandatory argument.
> - **`banchi/attrezzi-misura-marca.sh`** — grafts a fault, captures **all** the output, and puts things
>   back **by rebuilding** even if the round dies. ⭐ It is what makes a certification take an hour
>   instead of a morning.
>
> #### ⚠ WHAT STAYS CROOKED, said instead of kept quiet
>
> - ⛔ ~~**On Firefox the farewell of `RCP.md` §8.1 does not go out**~~ — **separated, cured and re-measured the same
>   night**. ⚠ *«The page does not send»* and *«Firefox throws away what the page sends inside
>   `pagehide`»* arrived **identical** at the server's log, and what separated them was the log
>   **of the browser**: `banchi/01-p5-ff-*`, with a carrier that does not go through WebTransport. ⇒
>   The defendant was **the page**, on both engines; ⭐ the cure is in the product and the two rounds per
>   engine confirm it. ✅ **And the declaration is there**: `DECISIONI.md` §1.12 — cure **out of phase**, the
>   phase 1 stays closed at **12 out of 14**, and the re-certification of P5 is phase 2's load.
> - ⚠ **And that bench's tracer is BLIND on Chrome inside `pagehide`**: neither
>   `sendBeacon` nor a **synchronous** XHR gets out. On Chrome the attribution rests only on the
>   server's log — which is enough, because between before and after the violation line changes, ⛔ but whoever
>   reused that tracer elsewhere must know it.
> - ⛔ **P5 does not certify** for that single point — the rest of its healthy round is green on Chrome.
>   ⭐ **And now the cause is gone**, but the new round **has not been done**: it is done in phase 2
>   (`DECISIONI.md` §1.12). ⛔ *«Cured»* does not mean *«certified»*: they are two different words, and
>   this phase has already confused them once.
>   ⭐ **P5's scene was cured the same night** — two tabs, so `ctrl+w` closes **the tab** and
>   does not make Firefox quit — and with it the counter that would have made it useless: `01-p5-registro.py`
>   now demands **`motivo 0x01`** instead of *«any close»*, and counts the line of
>   **violation of `RCP.md` §3.1** with expected zero. ⚠ *Tested on real logs: Chrome's pre-cure segment
>   — the one on which the old bench printed «la pagina fa quel che `RCP.md` §8.1 le impone» — is now
>   **red with two faults**.*
>   ⭐⭐ **And while curing the scene a third defect popped up**: on the `CONGEDO` road the server
>   freed the slot **without writing it in the log** (the only one of the four points not to do it). The
>   slot really was freed — ⛔ but the invariant **`RCP.md` §8.2 `0x0F` was no longer observable**, and P5
>   would have given red to a healthy server. Cured and measured (`DECISIONI.md` §1.12): P5's
>   judge goes from **1 false fault** to **0**, two rounds per engine.
> - ⛔ ~~The password in the dirty logs~~ — **closed**: cure verified with a new round,
>   **33 files** thrown away with the trace. ⛔ ~~And the password on the command line remains (so in
>   `ps`)~~ — **closed too on 12 Aug 2026**, defect **D12**: B10's road (file `0600`,
>   `trap`) extended to all benches. ⭐ **Verified with an A/B, not declared**: the decoy in `argv` is
>   seen **30 reads out of 30**, the password **0** and the file path **30 out of 30** — and that «30» is the
>   denominator, without which the zero would be *«I did not look»*. ⛔ And the defect was not theoretical:
>   the container is a **`chroot`, not a PID namespace**, so the processes inside are
>   all seen in the host's `ps`. ⚠ **`01-b12-lancia.sh` remains exposed** (5 calls) — and now
>   **it declares at every round** that its password is in `ps`.
> - ⛔ ~~The certification register still has to be merged by hand~~ — **closed on 12 Aug 2026**,
>   defect **D10**: the merge is **inside the program**, and where it cannot be (from the server the laptop's copy
>   cannot be reached) **not having done it shows in the place where the
>   number is read**, with the verdict downgraded. ⛔ **And the defect had already bitten**: the two copies diverged
>   by **5 lines on this side and 2 on that**, and the manual step had been skipped **seven times**. ⛔⛔ And a
>   conflict — the same certification with different fingerprints — was resolved **silently, by
>   line order in the file**: the same entry read *«vale oggi»* or *«non oggi»* depending on which
>   line happened to be lower. Now it stops and names it. ⭐ **What was NOT cured, because
>   it is not a defect**: that the number depends on where you ask for it — the two machines are
>   both right, and the tool writes *«non so»* instead of rounding.
> - ⚠ ~~7 calls out of 52 remain «IGNOTE»~~ → `[M]` 12 Aug 2026, defect **D9**: **115 calls
>   looked at, 111 approved, 0 broken, 4 unknown** — and each of the four carries written **in the code**
>   why it cannot be judged (three are so **by construction**: `$*`/`$@` would want to run the
>   caller's caller). ⛔ **And the worse half of the defect was not the unknowns: it was the
>   denominator.** Lines split with `\` and launchers that keep the bench in a variable
>   were **out of the count** — among these, four calls to the wire validator and the judges of
>   capture, of the session and of P5. ⭐ And the positive control **was not there**: added, and tested
>   by mutating the real tree in a copy (removing a mandatory one from the shared profile gives **7 reds**).
> - ⚠ ~~`01-b0-terreno.sh prodotto` does not look at the product's binary~~ — **cured on 12 Aug
>   2026**, defect **D5**: the binary is **next to the sources** (`remotix/build/` never
>   existed, and another bench already declared so). ⛔ **And the case that counts is another**: a **stale**
>   binary would have stayed green **even with the correct path**, because only
>   `rcp.c` was compared. Now all the sources plus the `Makefile`, and the tree **declares itself** — under
>   `/media/REMOTIX/src` there are **five** with a `remotix` executable inside. The terrain counts
>   **15 out of 15** on the graft and **4 out of 4** on the product, where it was *«2 controlli, 1 ignoto»*.
> - ⚠ **B8's medians**: ⭐ what is new is that **the defendant is measured**: on the refused ones the
>   delay beyond the fixed second is much longer than on the admitted ones, that is the signature of `pam_faildelay`.
>   ⇒ **PAM, not our code** — and the `[?]` stays open all the same.
>
> #### ⚖️ AND WHAT AWAITS THE USER — now it is **one** thing, not two
>
> ✅ **The verdict is given**: 11 Aug 2026, and the phase is closed (at the top of this page).
>
> ✅ **And the two fallbacks are decided too.** ⚠ *This line gave them as open, and it had expired:
> the user decided them on the evening of 11 Aug. Corrected on 12 Aug 2026.*
>
> 1. **The single thread** ⇒ `DECISIONI.md` **§1.10**: the PAM check **leaves the single thread before
>    phase 2 opens**, and ⭐ **with a helper process, not with a thread** — PAM is not reliably
>    reentrant, and a thread would bring troubles of its own into the cure of a concurrency problem.
>    ⛔ The reason is video: as long as there is no video the symptom is *«the last of the ten waits ten
>    seconds»*, unpleasant and contained; from phase 2 on **the screen of everyone connected
>    freezes every time someone else gets in**, and whoever sees it **will blame the video**.
> 2. **The session ceiling** ⇒ `DECISIONI.md` **§1.11**: it stays **16, fixed at compile time, until
>    phase 3** — because *«the real limit is not a count: it is a budget of pixels per second, and it is
>    set by the encoder»*, and any number put in today would be a placeholder to change twice.
>    ⚠ And the price is declared: for two phases **the code says 16 and the specification says 10**.
>
> ---
>
> ### ⛔ THE DIARY HAS BEEN PRUNED — *16 Aug 2026*
>
> *Decision of the user, reviewing the documents.* This file carried **nine** «RESUME FROM
> HERE» boxes stacked, one per work session. ⛔ **Six of them were already declared dead by the
> file itself**, with the formula *(superseded by the box above)*: **485 lines**, 31 % of the
> document that is opened first.
>
> ⭐ **They went out, and remain whole in the history** — the last commit in which they live is **`47bd41c`**:
>
> ```
> git show 47bd41c:README.md | less        # the README as it was, diary included
> ```
>
> ⚠ **No measurement went away with them**: they were *resume* boxes, that is session state,
> and the numbers they cited are in `FASI.md`. ⛔ If you find one that is not there, it is a defect —
> and the line above says where to reread it.

> ### 📅 HOW IT WAS ON **15 Aug 2026, morning** — *superseded; start again from the box at the top.* ⇒ **THE TAIL OF PHASE 4 IS CLOSED: THE CANVAS IS THE WINDOW**
>
> > ## *«Sia su Linux sia su Android (DeX) è tutto perfetto.»*
> > — the user, 15 Aug 2026, after a night of work and three defects found by him
>
> ⭐⭐ **The remote desktop takes the size of the browser window**, and from this follow
> four things the user saw as separate defects: no black bands, sharp text (drawing
> scale **1.000**), the reattach that finds its size again, and the login that brings the desktop
> **at once** instead of after seconds. ⭐ The confirmation that does not come from us: GNOME *Settings →
> Displays*, **inside** the remote session, declares «Resolution 1264 × 800».
>
> | | |
> |---|---|
> | ⭐ **the phase's number** | the canvas agreed at attach: `[M]` **1264×800** = the window, scale **1.000**, `pixelated` |
> | ⭐ **login → desktop** | the cure is not resizing: it is that **restarting the stream delivers a buffer** when a keyframe is due and the scene is still |
> | ⭐⭐ **click → frame sent** | the link on a STILL scene, which nobody had measured, gets shorter. ⚠ It is not the link of `CODER.md` §1-bis, which is on a moving scene |
> | ⭐ **hot resizing** | ⚠ **since 17 Aug 2026 it is no longer a user feature**: the canvas adapts at attach and at **reattach**, and never with the session live (`DECISIONI.md` §5.1-bis) |
> | ⛔ **and the build block** | untied **without asking the user**: `src/Contenitore` (rootless podman, on the laptop) and the path error in `enter.sh` |
>
> ⛔⛔ **TEN DEFECTS FOUND BY REFUTING** the cure just written (four agents, adversarial
> mandate), and **eight had been born that night together with it**: a read beyond the copied
> memory, a message that made a healthy session close, two chained `ADATTA_TELA`s that
> settled the desktop on the wrong size *with the accounts in order*.
>
> ⛔⛔ **AND THREE WERE FOUND BY THE USER**, not by the benches — among them the biggest of the night: *«su
> Android il mouse non prende più i click»* was **two sessions of his fighting over the stage
> seventeen times a second**, and every round recreated the `libei` devices (`[M]` 640 replacements).
>
> 📖 **The document**: [`FASI.md` §04-si-comanda](FASI.md#04-si-comanda), §«the tail of phase 4» ·
> the technical report `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md`.
>
> ⛔ **AND THIS IS PHASE 4, NOT 6** — corrected by the user on 15 Aug 2026, and his reason
> holds: the phase number is given by **why** the work was done, not by the list of things
> produced. Here it was done to cure **the mouse and the click delay**, that is to finish the mandate
> of phase 4 — and all the night's reports are called `F4-IN-*`, the new one included.
> ⇒ **Phase 6 stays OPEN** with three quarters of its content already done and measured (`PIANO.md` says
> which).
>
> ### ⭐⭐ AND THE NEXT IS **5 — THE SESSION**, in a NEW work session
>
> *Decided by the user on 15 Aug 2026.* The mandate is written, with the machine in order and the server
> on: 📖 **`fasi/rapporti/F5-IN-0-mandato.md`** — inside
> are the state of the machine, **the two roads for building**, what of phase 5 is already alive (and
> must be **tested**, not rewritten), and the four pieces that are really missing.
>
> ⛔ **The first gesture is opening `FASI.md` §05-la-sessione**, before writing a line: the tail of
> phase 4 violated that rule, and carries the reservation at the top.
>
> ---
>
> ### ⭐⭐⭐⭐ The detail of the night of the 13th, and the two defects found by the verdict
>
> > ## ⭐ *«Mi sembra abbastanza fluido, non il massimo ma pur sempre fluido.»*
> > — the user, 14 Aug 2026, and **phase 3 closes here**
>
> ⛔⛔ **But the verdict produced TWO defects no bench had found, and they are the work that
> comes now.** The detail is in [`FASI.md` §03-movimento](FASI.md#03-movimento) §0-ter and
> §0-quater; the night's count in
> `fasi/rapporti/F3-sessione-13-sera.md`.
>
> | | the work, in order | why first |
> |---|---|---|
> | **1** | ⛔⛔ **SHOW THE REAL DESKTOP.** The product **adds** a virtual monitor to the session (`Meta-2`, *«2 before and 3 after»*) and records that one: GNOME puts **the wallpaper** on it, but bar, dock and windows stay on the **primary**. ⇒ **The user sees an empty second screen, not their desktop** | ⭐ it is **the question the user asked** — *«se il server non mostra il desktop, a che serve REMOTIX?»* — and it is `SPECIFICHE.md` §5.1. ⛔ **It stayed hidden for two phases** behind phase 2's verdict, *«è lo sfondo GNOME, è OK»*: **an empty wallpaper taken for a success** |
> | **2** | ⛔⛔ **HEVC DOES NOT PAINT in the user's browser.** `[M]` 1 748 frames delivered, **0 painted**, and the client asks for a keyframe **1 659 times**. ⚠ **The benches said the opposite** (frames painted): that round had a **synthetic scene** and a **bench Chrome** | without it, **hardware encoding cannot be judged** — and the phase already has it inside |
> | **3** | ⚠ ~~**DRAWING as the bottleneck**~~ ⇒ ⛔ **CORRECTED on 14 Aug 2026**: drawing costs little; that stretch was **the wait for the frame from the GPU** plus the drawing | the bottleneck is there, ⭐ but **it is not where it was written** |
>
> ⭐⭐ **And `D1` is CLOSED, at zero cost, by reading the log of the verdict's session** — with an
> answer **worse than the question**: the throttling of the keyframe debt **holds at 1/s when the
> client paints** and ⛔ **opens to 5/s when it does NOT paint**, that is exactly when every keyframe is
> wasted. ⚠ And the feared scenario — *«one legitimate drop generates sixty illegitimate ones»* —
> **did not show up**: `abbandonati 0`. *The symptom observed was a different one from the one feared.*
>
> ---
>
> ### ⭐⭐⭐⭐ The phase's number, and how it was taken — **13 Aug 2026, night**
>
> *Phase 3 has its number **with hardware encoding**, and hardware encoding is **in the
> product**, not on a copy. The full count is in [`FASI.md` §03-movimento](FASI.md#03-movimento).*
>
> ⭐⭐ **THE ARCHITECTURE IS ACQUITTED**: removing the cost of encoding with hardware, **the other
> stretches of the link do not move**, and the keyframe stops being the frame that weighs.
> ⛔ **But the delay ceiling IS EXCEEDED**, and the box below says why the line that explained it
> was wrong.
>
> #### ⛔⛔⛔ 14 Aug 2026 — **A FALSE LABEL ON A TRUE NUMBER**, and it is corrected here
>
> *Corrected by decision of the user on 14 Aug 2026, on two independent measurements of phase 4.*
> The stretch called «drawing» **was not drawing**: it was **the wait for the frame from the GPU, plus
> the drawing** — a HEVC frame decoded in hardware comes out **opaque** and re-reading the bench's
> mark caused its GPU→CPU transfer. ⭐ The proof: changing codec with the stage identical,
> «decoding» and «drawing» moved **in opposite directions** and the sum was conserved. The fact that
> stays true: the cost of the **client after the wire** grows with HEVC, and that is where to look.
>
> ⛔ **And something that looks bad, written so that it is not lost**: the **control cell of that round never existed** — the `con-gpu` round tested HEVC, VP9 and H.264, and **not AV1**. Without AV1 there was nothing to compare with.
>
> ⇒ ⭐ **Why it is corrected instead of annotated**: whoever reads «the bottleneck is drawing» starts optimising the wrong stretch. `LEZIONI.md` §7.2 — *optimising in the wrong direction is worse than not optimising*.
>
> #### ⛔⛔ The three jobs, in this order and not another
>
> | | | why **first** |
> |---|---|---|
> | **1** | ⛔⛔ **THE STAGE**: the browser benches **measure on the user's desktop** believing they are on a fake screen. Chrome ignores `DISPLAY` and goes to Wayland because of `XDG_SESSION_TYPE`. `[M]` `xlsclients` on the Xvfb says **0 clients**, the page says `screen 2560×1080` | until it is done, **every delay number carries inside it the contention with the user's desktop** — and the next «before» would already be born wrong. ⚠ And it has already made **one victim**: the certification of `03-b16` does not re-run, because on a 2560 window the `V3s` case no longer finds the defect |
> | **2** | ⛔ **THE PAGE**: HEVC **is offered and negotiated** but **does not paint in the real session**, and its failure drags `video.misura_massima` to **320×240** ⇒ canvas 320×240 against capture 1920×1080, and the product (correctly, `RCP.md` §6.2) **does not send**. **Zero frames** | without it, **no bench can exercise the hardware encoder**: not a frame reaches it, and the phase does not close |
> | **3** | ⭐ **THE NUMBER**: the link with hardware encoding, `03-b17-ritardo.py`, **same scene** | it is the number the phase closes on, and the two before are its preconditions |
>
> ⚠ **And `/srv/src/03-B-src/` carries the OLD page**: whoever switched on that tree as it is
> would measure the hardware encoder **off**, and would write *«hardware is of no use»*.
>
> #### ⭐ What instead is in the safe
>
> | | |
> |---|---|
> | the phase's number **holds** | re-measured with new bench and page, and software encoding was its biggest part |
> | hardware encoding **works** | on the card the encoding stretch gets much shorter, on an easy scene and on a hard scene |
> | ⛔ but the total does **not** improve | the bottleneck has moved: **colour conversion costs more than encoding** ⇒ ⭐ it must be brought **onto the card** — and since phase 18 VA-API's VPP does it |
> | the client **decodes HEVC** | `VideoDecoder`: **120 frames out of 120**, two packaging roads, 5 rounds out of 5 |
> | ⛔ **AV1 in hardware does NOT exist** on the UHD 730 | staying on AV1 = staying in software **forever** — and since phase 19 AV1 is no longer there: the software fallback went out |
> | ⛔ **Firefox has no HEVC** in WebCodecs | ⇒ moving to HEVC **does not remove AV1: it makes it mandatory** |
>
> ---
>
> ### 📅 HOW IT WAS ON **12 Aug 2026**, night — *superseded; start again from the box at the top of the README.*
>
> **The state**: clean tree (`636f088`), **14 benches out of 14 certified and valid today**, terrain
> of the graft `14 su 14`. ⚠ On NIC-OS **two** servers stay on, and they are meant to: the **home
> product on 7448** (restarted tonight on the right binary) and **P5's target on 7501**.
> Ports **7447** and **7481** are free. No round in progress, on either machine.
>
> ⏳ **The only thing with a deadline**: `bash banchi/01-s1b-eccezione.sh oggi`, **once a
> day until 18 Aug**. The 11th had been skipped and recovered at the last moment (day 1.00 of 7);
> ⛔ `/media/REMOTIX/s1b-certificato/` is not regenerated and `~/.remotix-s1b/` is not deleted.
>
> **What remains, and has not been decided** — points 4-7 of the night's list:
>
> | | | where it ended up |
> |---|---|---|
> | **4** | `01-b12-lancia.sh` has `PORTA=7447` and `bsslserver` hard-coded: it cannot be pointed at the product, and that is why B13 is certified **only** from its «evening» script, while P1 and P5 stay outside the orchestrator | ⏳ **open**, defect **D6** |
> | **5** | P5's fault covers **less** than it promises: the page picks up `/impronta` before every attempt, so the false fingerprint does not kill the session. To really cover **R1.14** a fault that hits **the pick-up** is needed | ✅ **closed** on 12 Aug, defect **D11**: the new fault removes **the pick-up**, and the proof that it looks at something else is that with the fault inside **the old check stays green** |
> | **6** | the **declared** holes: `B13.3` (the certificates are made by a bench, not by the code), `B13.5` (the transport grants all the streams requested), and the `[?]` of **B8** on `pam_faildelay` | ⏳ **open**, and declared as such |
> | **7** | the two phase fallbacks: **a single thread** with the PAM check blocking it, and the ceiling of **16 sessions at compile time** where the rule wants ten configurable | ✅ **decided by the user** on 11 Aug — `DECISIONI.md` §1.10 and §1.11. ⚠ *This line gave them as undecided, and it had already expired when it was written* |
>
> ⚠ **And one thing about method, from whoever held the keyboard**: the trap *«never a redirection
> **around** `enter.sh`, or it eats `sudo`'s password prompt»* — already in the catalogue,
> `FASI.md` §00-ambiente B3.3 — was repeated **twice in the same night**, and the second time
> cost twenty minutes of waiting on a build that was not building anything. ⇒ It is worth
> making it impossible instead of remembering it.
>
> ---
>
> ### ⭐⭐⭐ P5 IS CERTIFIED — the night between 11 and 12 Aug 2026, **0 → 1 → 0**
>
> *The three certification rounds were done in full against the cured copy on **7501**,
> with the browsers on CHUWI and the product on NIC-OS — that is with the wire really crossed.*
>
> | | |
> |---|---|
> | ⭐ **the healthy round: GREEN on both engines** | n1 right/mangled `ok`, `n2-parola-sbagliata` **11 checks 0 faults**, `p-sessione` **15 checks 0 faults**, on Chrome **and** on Firefox |
> | ⭐ **the round with the fault: RED, and it names the right thing** | *«la pagina pubblica «AAAA…=» e l'endpoint dice «PJ03…=»: sono due impronte diverse per lo stesso certificato di sessione»* — defect **R1.14** of `RCP.md` §4.1-bis |
> | ⭐ **and the mark is a mark**: `[M]` it appears **0 times in the healthy one, 1 in the faulty one, 0 in the healed one**, counted on the three rounds of that night — not on a measurement from yesterday |
> | ⭐ **the healed round: GREEN**, and the binary came back **identical byte for byte** | `d69df441…` → `117911ca…` → `d69df441…`: that the fault went in and then out is said by the binary's fingerprint, not by the colour of the verdict |
>
> ⛔ **And the fault proves less than its title says — it must be read before believing the
> line above.** With the false fingerprint in the page, the `p-sessione` legs stay **CONFORMANT**: the
> WebTransport session **opens all the same**. ⭐ The reason is the product's, and it is `RCP.md` §4.1-bis applied:
> `pagina.html` **picks up `/impronta` before every attempt** and uses that, keeping the served
> fingerprint only as a fallback — and when the two diverge **it says so**. ⇒ The fault proves that **P5 sees
> the divergence**, which is what P5 exists for; it does **not** prove that the divergence kills the session,
> because on this product it does not kill it.
>
> ⛔ **And the first attempt at a healthy round came out RED with all four legs CONFORMANT**: the
> server's log had a hole of **37,120 NUL bytes** — `svuota-registro` called with the server
> alive — and `grep`, gone blind, read «NON LETTO» where our address was, sending the
> unblock of `RCP.md` §4.4-bis **onto the server itself**. Three cures, all re-measured; the lesson is in
> `LEZIONI.md` §1.9 point 9.
>
> **How to redo it**, if it needs to be re-run:
>
> ```
> # the target: a COPY of the product, port 7501, its own ban and socket
> bash /media/REMOTIX/enter.sh --root "bash /srv/src/01-p5-accendi.sh accendi"
>
> # the round, FROM CHUWI (the browsers are on this side)
> SSH_ROOT="python3 fondamenta/strumenti/sshpw.py" \
>   IND=192.168.0.2 PORTA=7501 SOCK=/srv/src/tmp/sera-p15.sock \
>   LOG_SERVER=/media/REMOTIX/src/tmp/sera-p15-browser.log \
>   SCHERMO=:79 PORTA_LOC=8859 bash banchi/01-p5-lancia.sh
> ```
>
> ⛔ **Between one step and the next TWO things are needed, not one**: `costruisci.sh` on the copy **and** the
> server switched back on with that binary. P5 does not rebuild by itself — it finds a server on and queries it
> — so skipping one would make it measure the previous binary **while looking as if it had grafted**.
> ⚠ If the copy is missing, `01-p5-accendi.sh copia` redoes it and rebuilds it (`GEMELLO=/srv/src/rcp`);
> ⛔ and **`copia` is not used to remake the binary after a graft**, because it copies again from the product and
> the fault disappears without saying so.
>
> #### ⭐⭐ THE PRODUCT EXISTS: `src/`, the phase 1 server in C
>
> ⚠ *This page, and the phase document, said* «**no line of product written**» *until
> 11 Aug 2026 — while `src/` had been born on the night of the 10th and none of the ten documents
> named it (finding **R12C.1**). Whoever picked up the work read that line and **rewrote from scratch
> a server that exists.***
>
> `[M]` **11 Aug 2026** (`wc -l`, code frozen at 00:36): **22 files**, **9,647 lines**, of which
> **5,248 of code**. ⭐ **The RCP/1 handshake gets as far as `SESSIONE` with a real
> browser** — with the two certificates of §4.1-bis, the ban of `RCP.md` §4.4-bis on file and its unblock
> command. ⛔ No video, no audio, no input: those are the phases from 2 on.
> ⚠ *This line said* «**a real browser opens `https://192.168.0.2:7447`**, the user types name
> and password … **the page served by the server itself**», *and the log of that round does not
> support three pieces of it: the browser was **on the same machine as the server**, the page **was not served
> by the product** (`GET /` zero times in 48 lines), and the port was **7448** — 7447 belongs to
> the graft. Corrected on 11 Aug 2026; the full count is in the table below.*
> **The detail, file by file, is in `FASI.md` §01-filo-nudo §«What was developed».**
>
> ⛔ **And what is NOT proven, which is the half that is not seen:**
>
> | | |
> |---|---|
> | ⛔ **A SINGLE ENGINE** | the only trace of a round with a real browser against this server is a comment inside `src/pagina.html` — `[M]` 10 Aug night, **Firefox** — and that round found a real defect (the page declared `disposizione = en`, which is not an XKB name). ⛔ **Of Chrome against this server there is no trace**, and B2's criterion wants **two engines out of two** |
> | ⛔⛔ **and that round is LESS than what this page said** | `[M]` **11 Aug 2026**, read in `/media/REMOTIX/src/remotix-browser.log` (48 lines) and recounted by hand. ⭐ **What holds**: the handshake really gets as far as `SESSIONE` — `sessione aperta utente=prova … tela=1920x1080 vista=1152x836 disposizione=us`, and the odd view says that a real window was asking. ⛔ **What does NOT hold, and it is two things**: *(1)* all **19** connections come from `[192.168.0.2]`, that is **from the server itself** — the round **did not cross the network**, and this page told it as a browser opening an address from outside; *(2)* **`GET /` appears ZERO times** and `GET /impronta` once: ⛔ **the page was not served by the product**. The second job of the phase 1 server — *serving the page*, `PIANO.md` phase 1 — **is not measured anywhere** |
> | ⚠ **and in that round the client did not say farewell** | the slot went away with `STACCATO per silenzio: 30269 ms … (posti occupati adesso: 0)`. ⛔ What freed it was **the clock**, not a farewell: a bench that waited five seconds would write «the slot was not freed» on a server that was about to free it |
> | ⛔ **and that round cannot be re-verified** | `[M]` 11 Aug: in `src/` there is neither the binary nor a `.o`, no `.jsonl`, and `git status` gives it as **untracked**. ⛔ **None of the 14 launch scripts switches on the product**: `bsslserver` appears in **11** of them, the `remotix` binary in **zero** |
> | ⛔ **no reviewer ran the whole server** | `ngtcp2`, `nghttp3`, `libssl-dev`, `libpam0g-dev` were missing: `trasporto.c`, `webtransport.c`, `pagina.c`, `certificati.c` are **read, not measured**. ⭐ The only execution is `rcp.c` **compiled in isolation**, `-Wall -Wextra`, **zero warnings**, six inputs byte for byte |
> | ⛔ **the transport properties have not been re-measured on it** | B2's six are `[M]` **on the graft**. The product today declares **19** unidirectional streams where the measurement read 16 |
> | ⛔ **two phase fallbacks, declared** | **a single thread**, and the PAM check **blocks** it: ten users signing in together make the last one wait ten seconds (`SPECIFICHE.md` §5.5 promises ten sessions). And **16 attached sessions at compile time**, where the ceiling is ten configurable |
>
> #### The benches: **twelve written**, six green, ⛔ **and THREE certified**
>
> **Twelve benches written** — `[M]` 11 Aug 2026, counting the distinct prefixes in `banchi/`:
> `01-b2 · b3 · b4 · b5 · b6 · b7 · b8 · b9 · b11 · b12 · b13 · c2`. ⚠ *This line said «**eight**
> benches written»: four had been born on the night of the 10th and nobody had added them — finding
> **R12C.13**.*
>
> **Six green**: B2 · B3 (five rounds out of five) · B4 (13 out of 13, four outcomes) · B5 (36 violations
> out of 36 + 8 expected greens) · B7 (**7 provokable reasons out of 7, denominator 15, and 15 distinct sentences**) ·
> B11 (13 cases out of 13 on the two engines).
> ⭐ **B6 is no longer yellow, and not yet green**: it closed R3.27 with **two** answers (see below),
> and it came out **3** — *«the wire behaves as the code says, and the document says something else»*.
> ⛔ Now the document has changed: **it must be re-run**, and that is the only thing that will say whether it is green.
> ⚠ **B8 has not finished**: the three medians remain to be compared.
> ⭐ **And the four born on the night of the 10th**: **B9** (the second reader, which produced **twelve**
> points where `RCP.md` admits two readings), **B12** (the certification), **B13** (the six properties),
> **C2** (the three diagnoses) — plus the **seven pages of the probe**.
>
> ⛔ **And the honest count of certifications is 3 out of 12**, not six and not four: *«green»* means
> that the bench ran without finding anything, *«certified»* that someone **broke the code under
> it** and it turned red on the right mark.
>
> ⚠ **And the two «twelves» are NOT the same twelve, or this line would be a count without a
> denominator**: the twelve *written* are the prefixes in `banchi/`; the twelve of **B12's catalogue**
> include **B10** — which has no script of its own — and exclude **B12**, which does not certify itself.
> The count below is on B12's catalogue.
>
> | | |
> |---|---|
> | ⭐ **certified** | **B4**, **B9** (11 Aug 00:27, with the fingerprints of the participating files) and **C2** (10 Aug 22:32) — ⚠ on B9 with a written reservation: its fault proves it can see **a changed text**, which is the thing B9 declares it can do |
> | ⛔ **tested and NOT certified** | **B13** — and the defect belongs to the **fault**, which the orchestrator cannot graft and which would build a defect B13.1 does not look at |
> | ⚠ **certified and NOT re-verifiable** | **B7** — the mark required was the word `CONGEDO`, which the bench prints in the **healthy** round too: *«a mark that appears in both rounds is not a mark»* |
> | ⛔ **never tested** | **B2 · B3 · B5 · B6 · B8 · B10 · B11** — seven |
>
> ⇒ The register is `banchi/01-b12-registro.jsonl`, and the full count is in `FASI.md` §01-filo-nudo.
>
> #### ⭐ The access rule has changed, and the user decided it — 10 Aug 2026
>
> ⛔ **Three failed authentications from the same address WITHIN 5 MINUTES, and that address is out
> for 12 hours.** The **user name does not count**: three different names count three. A successful sign-in resets
> the count; the ban **is on file** and survives restarts; you get out with the twelve hours **or** with an
> unblock command on the server. Whoever is banned **sees a page that tells them so**, not a silence.
>
> > ⚠ *This line said* «three **consecutive** failed authentications», *without a window —
> «consecutive» was the user's **first** wording, and the five-minute window is a
> **third** sentence of the same day that narrows it. ⛔ The two rules give **opposite outcomes on the
> same input**: three failures at 0:00, 4:00 and 8:00 are consecutive ⇒ banned according to this
> line, and **outside the window** ⇒ not banned according to the code. The window was in `DECISIONI.md`, in
> `RCP.md` §4.4-bis, in `SPECIFICHE.md` §4.2 and in the code, and was missing **in the two documents the bench
> is written from**. Corrected on 11 Aug 2026, finding **R12C.5** — and it happened because the
> decision was **copied** into four documents instead of referred to, which is exactly what the
> conventions below forbid.*
> ⇒ `DECISIONI.md` §1.9 — and with it `RCP.md` §4.4-bis (from 🔸 to ✅), `SPECIFICHE.md` §4.2,
> `FASI.md` §01-filo-nudo B0.3 and B8.
>
> ⭐ **It replaces the form I had written** — 5 in 5 minutes, a window doubling up to 15
> minutes, two counters — and ⛔ **the wire does not gain a byte**: `TROPPI_TENTATIVI` already existed.
> ⚠ **The price is declared in `DECISIONI.md` §1.9** and it is not paid by whoever guesses: behind a NAT three mistakes by one
> person close the door to everyone for twelve hours, and the first to trip over it is whoever types a long
> password on a phone keyboard.
>
> #### ⛔⭐ THE FIRST STEP OF THE NEXT SESSION: **point the benches at the PRODUCT**, and find a second engine
>
> *(B8 was rewritten on the night of 10 Aug on the new rule — three failed with three different
> names, the fourth with the right password that MUST be refused, plus the checks that say *no*.
> That step is done; this is the next one.)*
>
> ⛔ **Today there are two servers, and the benches measure only one.** The product is `src/`; the graft is
> `banchi/01-b3-rcp-innesta.py` inside `bsslserver`, and it is the one all the 14 launch scripts
> switch on. ⛔ **The protocol is the same file** — `src/rcp.c` and `banchi/rcp/rcp.c` are identical
> byte for byte — **but everything around it was written twice**, and at the points where
> the two drafts diverged one carried written the proof that the other did not work.
>
> ⚠ **And the risk is precise, not generic**: the first time someone points a bench at the
> product — which sooner or later will happen, because it is the product — they will get **reds on a server that
> does things**. This project's precedent says that when a bench is red and the code seems to
> work, one searches **in the code for hours** before suspecting the measurement.
>
> **In this order, and each one costs little:**
>
> | # | What | Why before or after |
> |---|---|---|
> | **1** | ~~switch on `src/` once~~ ✅ **done on 15 Aug 2026**, and several times: `src/costruisci.sh` inside `enter.sh` on the test machine, ten rounds | ⭐ And there is a **second** road, born that night: `src/Contenitore` + `src/costruisci-in-contenitore.sh` — **rootless** `podman`, on the laptop, without `sudo`. The two answer two different questions: *«does it compile?»* is asked of the laptop in twenty seconds, *«does it run?»* is asked only of the test machine. See `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md` §1 |
> | **2** | ⛔ **point `01-b8-sblocca.py` at the product**, with the `PING` | it is the tool of rule **B0.3**, that is the one on which the isolation of **all** the other benches depends. Today it talks with the graft's socket and has never talked with the product |
> | **3** | **B8, B6, B7 and B5 against `src/`** | they are the four that touch the ban, the ceilings, the farewell and the violations — that is the four points where the product has code no measurement has seen. ⚠ And there B7 finds **eight** provokable reasons instead of seven: the product has a shutdown path, the graft does not |
> | **4** | ⛔ **B2's transport probe against `src/`** | the product declares **19** unidirectional streams where B2's measurement read 16, and the other five properties (0-RTT, migration, datagram, ceiling, `allowPooling`) **nobody has read** on it |
> | **5** | ⭐ **A SECOND ENGINE** | the only round with a real browser against the product was with **Firefox**. ⛔ B2's criterion wants **two engines out of two**, and the most expensive defects of this phase — B11's three reds, the slot that was not freed — **lived in the difference between the two engines**. With a single engine that difference cannot be seen |
>
> ⚠ **And one thing NOT to do first**: going back to the documents. They were realigned on 11
> Aug on the frozen code; the next misalignment is born from the first new measurement, and it is cured
> **at the same moment** (`CODER.md` §5).
>
> #### ⚠ And two things that go with it
>
> | | |
> |---|---|
> | ⛔ **what governs the timings is not our fixed delay, it is PAM** | `[M]` on the refused attempts the delay is **well beyond** the second `RCP.md` §4.4-bis wants. The prediction (`pam_faildelay`) had been written **before** measuring. ⚠ It matters because that delay **is not constant**: if it varies, it puts back into circulation the information the fixed second serves to hide — that is **whether a user name exists** |
> | ⚠ **B8's full round hangs at the ninth block out of ten** | it stays stuck on something nobody gives it. The short round (`… 01-b8-lancia.sh 2`) gets to the end. ⛔ It must be launched **detached** from the session of whoever commands it, not through it |
> | ⭐ **B6 closed R3.27, and with TWO answers** | **the first**: the stopwatch starts from the **opening of the control channel**, not from the end of TLS ⇒ **`RCP.md` §4.6 line 1 changed by one word**, on 11 Aug 2026. ⛔ **The second, and it says that curing the word is not enough**: whoever opens a WebTransport session and **never opens the channel** has **no ceiling** on them and stays there — §4.6 had no line for that state, now it has one and it is ❓ (`DECISIONI.md` §7.17) |
| ⚠ **B6's three ceilings have no log** | they trigger at **5.0 · 60.1 · 10.0 s** — ⛔ but **no `.jsonl` of B6 exists**, the scene of that round is declared nowhere, and these three numbers **cannot be re-verified**. ⚠ *They were here without a mark, without a date, without a scene and without a device, while `[M]` is defined further down as «measured by us, on the hardware, **with the date**» — finding **R12C.11**. They are redone with the log, or they stay three numbers of which only the order of magnitude is known.* |
>
> #### ⭐ The measurements of the night of 10 Aug, and where they live
>
> ⛔ **The outcomes are in `web/rapporti/S-esiti-sonda.md`** — the fifth file of `web/rapporti/`, which
> is not a study: it is **the only one that carries measured numbers**, with the scene beside each one, the
> `.jsonl` logs and ⛔ **a recount of 11 Aug that declares which numbers have a
> provenance on disk and which do not** (one was false, two were without provenance, one could not be
> found again). ⚠ *Until 11 Aug that report was named by **none** of the ten
> documents — finding **R12C.15**.*
>
> | | |
> |---|---|
> | ⭐⭐ **S7 — the sign of the wheel: MEASURED** | `[M]` 10 Aug, 20:59 UTC. `+120` from `libei` sends the page **towards the end of the document** ⇒ ⛔ **the RCP server must invert the vertical axis**. Full scene: headless GNOME on 192.168.0.2, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**, **Firefox 140.13.0esr** in kiosk; log `banchi/01-s7-esiti.jsonl`. ⇒ **`RCP.md` §7.3 is closed** — ⛔ **on Mutter**: §7.3 binds five desktops, and for the other four it stays `[?]` |
> | ⛔ **S5 — the declared canvas: A PRODUCT DEFECT** | `[M]` 10 Aug, 23:13-23:14. At 150 % zoom **Chrome 151** declares a canvas **50 % larger** (1920×1080 → **2880×1620**) because `screen.width` does not drop; **Firefox 140** does not. ⇒ the formula of `SPECIFICHE.md` §6.1-bis **does not hold on Chrome**, and there it still said *«it must be measured»*. ⚠ The half on **DeX** is missing: the device was not there |
> | ⭐⭐ **S1b — Chrome's exception: ANSWERED, and without waiting the seven days** | `[M]` 11 Aug, `01-s1b-eccezione.sh scavalca`, **6 checks out of 6**. Instead of waiting for the expiry **we brought it to us**, on a **copy** of the profile: Chrome records the click **+ 604 799.99997 s** (it writes both instants itself, in the same file), **honours** that instant — expiry rewritten to yesterday ⇒ the page no longer opens — and **does not renew it** when it is visited. ⛔ The check that says *no*: the **same** tampering with a date of **+30 days** leaves the page open, so above only the sign changed. ⇒ **The user is told «once a week»**. ⛔ The «13.111 s missing» were not Chrome's: they were the distance between **two clocks**. ⏳ 17-18 Aug remains as a passive confirmation, and the real clock is intact |
> | ⛔ **S2 · S3a · S6 — not run** | missing are **the Android phone**, **DeX**, **a real LTE network**. ⭐ They were not deduced (it would be form **E5**): the benches are ready and run the day the hardware is there |
>
> ⚠ **And a discovery that does not belong to this phase**, carried into `PIANO.md` phases 2 and 6: in a GNOME
> session without physical input devices, a client started **before** `libei`'s virtual pointer
> exists **receives nothing** — no wheel, no buttons, no movement. Mutter receives the injection
> and does not deliver it to the window.
>
> ⚠ **And FOUR open decisions, and each one closes with one word**: the reading of `RCP.md` §4.2
> on `FIN` · the condition of §8.1 · whether §7.5 was really its own (meanwhile it is 🔸) · ⭐ **and from today:
> how long a WebTransport session that never opens the control channel can stay there**.
> ⛔ **They are in `DECISIONI.md` §7.14, §7.15, §7.16 and §7.17** — with the two possible readings, **the
> byte that changes on the wire** between one and the other, the concrete case in which the difference shows and
> which one seems more defensible. ⚠ *The first three were named here and in
> `fasi/rapporti/R11-documenti.md` (findings R11.22, R11.23, R11.15) and in no place where things are decided:
> brought to where decisions live on the night of 10 Aug 2026. The fourth was born on 11 Aug **from a
> measurement** — B6 — and not from a reading.* ⛔ **None of the four is decided, and the mark stays ❓
> until the user speaks.**
>
> ---
>
> ### The step just closed
>
> ⭐⭐ **B3, B5 and now B11 are closed. Thirteen cases out of thirteen on BOTH engines** —
> Firefox 140 and Chrome 151 — plus the two negative properties, and ⛔ **the second green witness**.
> *(10 Aug 2026, evening, and repeated)*
>
> ⚠ **And the check that says *no* runs on ONE ENGINE ONLY — Firefox** *(finding **R11.24**,
> closed like this on the night of 10 Aug: the bench declared it by itself, this page did not)*. It is
> `01-b11-lancia.sh`: the page against a **healthy** server must say NON-CONFORMANT, and it says
> NON-CONFORMANT with **9 cases out of 13** failed. ⛔ **The line above listed it within «on both
> engines»**, which is the natural reading and was not true. ⚠ And the difference bites exactly here:
> tonight's three red cases **lived in the difference between the two engines**, that is at the point where
> *«to say no, one engine is enough»* is the premise just disproved. It closes completely
> by running it on Chrome too.
>
> ⭐ **B11 found six real defects, and none was visible to the test client**:
>
> 1. the **slot** (`RCP.md` §8.2 `0x0F`) was freed only on the death of the *connection* — and a browser
>    closes the *session* keeping the connection alive. Now it is freed when the control channel
>    closes;
> 2. a message sent **just before** closing the session, **the browser throws it away**: the
>    page did not see `RESPINTO`, it saw silence. ⭐ It is the proof that point 3 of `RCP.md` §3.1 — *the
>    reason inside the close code* — **is not redundancy**. Cured on both sides;
> 3. ⛔ the page **closed without saying farewell**, and `RCP.md` §8.1 says that whoever closes *MUST* send `CONGEDO`
>    with a reason — even when it is a voluntary close. Added: on Chrome the failures
>    went from 8 to 4;
> 4. ⛔ **the slot was not freed when it was the SERVER closing the channel.** From then on
>    no byte arrived that could free it, and the page could not make up for it: `RCP.md` §4.2 forbids it to
>    send after the end. Seen **only on Chrome** — on Firefox the transport closed the stream in
>    time and the slot went away all the same. ⭐ **The defect lived in the difference between two
>    engines**, and it is the one that closes Chrome's three red cases;
> 5. ⛔ **the server counted as «bytes sent after the end» also the `CONGEDO`** that `RCP.md` §8.1 *imposes*
>    on whoever closes. The red ended up on the page while it was doing what it must. ⭐ Hence the
>    clarification of `RCP.md` §4.4: after `RESPINTO` the ban is on **retrying**, not on
>    saying farewell;
> 6. ⛔ **the slot stayed occupied for the whole teardown of the transport**, and whoever reconnected
>    at once got the answer `GIA_ATTIVA_REMOTA`. ⚠ On the bench it was a red case now and then;
>    for whoever uses the product it is *«it tells me I am already connected, and it is not true»*. Now the server
>    **reads the capsule with which the page closes** and leaves the slot at that instant.
>
> ⭐⭐ **And the farewell arrives by TWO DIFFERENT ROADS, one per engine.** Chrome sends it as bytes on the
> control channel; **Firefox resets the channel and throws those bytes away**, and the reason arrives only
> inside the session's close code. ⛔ Until tonight the server **did not read that
> capsule**: of Firefox one would have said *«it does not say farewell»*, which is false. It is the measured proof that
> point 3 of `RCP.md` §3.1 is not redundancy — **it is the other road**, and without it half the browsers
> would seem rude.
>
> ⛔ **And two new traps in the bench, both on denominators**: the server's log was
> cut at `tail -60`, and **adding a line to the filter made «the faults served» go down from
> 26 to 21** without the server changing anything — a denominator that depends on how much is said.
> And the case `respinto-poi-congedo` made the close of `RCP.md` §3.1 **race** against the page's
> answer: Chrome lost the race in one round out of five. ⭐ Now that fault **does not close**, and the one
> closing is the page — which is exactly the thing the case wants to see.
>
> ⚠ **And one thing B3 does NOT prove, written so that it does not seem proven**: the **automatic** rotation
> of the certificate at fourteen days. Changing it by hand proves that the page can pick up
> the fingerprint; that the server regenerates **before** expiry stays without a bench, and its symptom
> — *«it no longer connects and does not say why»* — arrives two weeks after delivery.
>
> ⭐ **And the aged number was re-measured, not rewritten by eye** — `[M]` **10 Aug,
> 16:30**. The **reading of the close capsule** grew inside the WebTransport layer, and the
> measurement is taken like this: on a clean tree, `01-b3-rcp-innesta.py --togli`, then
> `01-b2-ngtcp2-wt-innesta.py --togli`, then **only** B2's graft is reapplied. Result:
> **553 lines added, 373 of code, 134 of comment, 46 blank**.
> ⛔ **And the 972 / 618 are another thing**: they are the tree with **both** grafts, B2 plus
> B3's threads. They are not lined up with the 553 and do not go where that number is — it is the reason
> why the two grafts are separate (form **E2**).
>
> ⚠ *This paragraph said three false things, and it was rewritten on 10 Aug 2026 — finding
> **R11.7**, with **R11.1**.* It said that `01-b3-rcp-innesta.py --togli` *«removed nothing, it
> said yes and left the graft where it was»*, that *«the measurement of B2 alone now cannot be
> taken»*, and raised an alarm on `ricostruisci`. ⛔ **The command does a partial removal and
> declares it on screen**: it removes our files, puts back `examples/CMakeLists.txt`, and prints *«i file
> .cc/.h toccati da B3 vanno rimessi con `01-b2-ngtcp2-wt-innesta.py --togli` e riapplicati»*. ⛔ And
> `ricostruisci()` in `01-b11-guasto.sh` runs **the two `--togli` in the prescribed order** and then
> reapplies: it does not rely on the first alone.
>
> ⚠ **What stays true, and stays open**: `--togli` **exits with 0 on a tree that in that state
> does not compile** — whoever stopped there would believe they had a healthy tree. It is a finding about the bench, not
> about this document, and it is cured there.
>
> ⚠ **And a maintenance item that has a date**: those lines include the **rewriting of nghttp3's SETTINGS
> frame**, which depends on the shape of its bytes and not on a promise of its own. ⛔ It must be
> re-tested at every nghttp3 update — and the bench that re-tests it exists.
>
> ⚠ **And a prediction stays open after two measurements**: `lsquic` writes the settings of **draft
> 02** and never `SETTINGS_WT_MAX_SESSIONS`. Not even with SNI does one get there — the connection dies
> first. It must be kept open instead of closed with a test that talks about something else.
>
> ### How to put the bench back on its feet
>
> ⚠ *This section listed **only** B2's benches, while the same page declares
> B3, B4, B5 and B11 closed — finding **R11.21**, closed on the night of 10 Aug 2026. ⛔ A bench that is not
> named where it says how to put the benches back on their feet has the same fate as one that needs
> a hand: **it cannot be redone the same**, and redoing it the same is the only way to know whether a measurement
> changed because the server changed.*
> ⚠ *The list was from the evening of 10 Aug 2026 and said:* «the benches born afterwards — **B9, B12,
> B13, C2** — are added here by whoever writes them». *⛔ They were born between 22:54 and 23:20 that night and
> nobody added them — and with them the files of **B6, B7, B8 and B11** were missing, which this same
> page gives as closed or run, and the **seven pages of the probe**. Completed on 11 Aug 2026,
> finding **R12C.13**: **R11.21 had been closed the same night in which a version of it twice
> as big was opening.***
>
> **B2 — the QUIC library and the trust model** *(from the server, except where said)*:
>
> `banchi/01-b2-costruisci.sh` (BoringSSL + lsquic) · `01-b2-costruisci-ngtcp2.sh` ·
> `01-b2-sni-ngtcp2.sh` (builds `bsslserver`) · `01-b2-sni-quiche.sh` (`leggi`, then
> `costruisci`) · `01-b2-lancia-sni.sh` (**the SNI test on the three targets**: `costruisci`, then
> `misura`) · `01-b2-lancia-impostazioni.sh` (**who declares WebTransport on the wire**) ·
> ⭐ `01-b2-ngtcp2-wt-innesta.py` (**the WebTransport layer**) + `01-b2-lancia-wt.sh`
> (the test client, and the refusal of `/rcp/9`) + ⚠ `01-b2-lancia-sonda.sh` — **this last one is
> launched from HERE, not from the server: the browsers are on this side** · `01-b2-certificati.sh` (⚠ **regenerates the fingerprint**: it must be put back in the
> page) · `01-b2-controllo-aioquic.py` (the positive control) · `01-b2-cliente-aioquic.py` ·
> `01-b2-raccogli.py` + `01-b2-sonda.html` (the page, from `localhost`).
> **The wire — the benches that closed something:**
>
> ⭐ `01-b3-rcp-innesta.py` (**RCP on top of B2's WebTransport layer**; `--togli` does a **partial**
> removal and declares it on screen) · `01-b3-lancia.sh` (**B3**, from the server: the first three rounds,
> with `01-b3-terzo-giro.sh` running **inside** the container) · `01-b3-quarto-giro.sh`
> (the silence clock, 35 s at `max_idle_timeout` 120) · ⚠ `01-b3-quinto-giro.sh` (**the
> rotated certificate: launched from HERE, not from the server — the browsers are on this side**) ·
> `01-b3-cliente.py` (**the second reader of `RCP.md`**, and the recorder of §11.1) ·
> `01-b4-lancia.py` + `01-b4-validatore.py` + `01-b4-registrazioni.py` (**B4**: the validator
> against recordings **regenerated now**) · `01-b5-lancia.sh` + `01-b5-violazioni.py` (**B5**,
> from the server: the violations towards the server) · `01-b6-lancia.sh` + `01-b6-tetti.py` (**B6**, the three
> ceilings) · `01-b7-lancia.sh` + `01-b7-congedo.py` (**B7**, the farewell **from the receiving side**) ·
> `01-b8-lancia.sh` + `01-b8-cronometro.py` (**B8**, the fixed second and the ban — ⛔ **it is being rewritten**,
> see above) · ⚠ `01-b11-lancia.sh` (**B11: from HERE**, with the two browsers) + `01-b11-pagina.html` +
> `01-b11-guasto.sh` and `01-b11-guasto-innesta.py` (**the server faulty on purpose**, and
> `ricostruisci()` which puts back the healthy one with the two `--togli` in order).
>
> **And those born on the night of 10 Aug 2026:**
>
> ⭐ `01-b9-letture.py` (**B9**, the second reader against the arbiter: **twelve** points where
> `RCP.md` admits two readings, each one **with the bytes that change on the wire**) ·
> `01-b12-guasti.py` + `01-b12-lancia.sh` + `01-b12-copie/` (**B12**, the certification — one fault
> per bench, and the register `01-b12-registro.jsonl` with the date and the fingerprints) ·
> `01-b13-lancia.sh` + `01-b13-proprieta.py` (**B13**, the six properties) ·
> `01-c2-lancia.sh` + `01-c2-diagnosi.py` (**C2**, the three diagnoses of the faulty connection) ·
> ⭐ `01-b8-sblocca.py` (⛔ **it is not a piece of B8**: it is **the tool of rule B0.3**, and it speaks the
> command socket of `RCP.md` §4.4-bis with `SBLOCCA` and `PING`) · `01-b8-prova-ban.c`.
>
> **And the browser probe** — ⚠ **these run from HERE or from the server according to the line, and the line
> says so**:
>
> ⏳ `01-s1b-eccezione.sh` + `01-s1b-pagina.html` + `01-s1b-sito.sh` + `01-s1b-servi.py` (**S1b**,
> the seven-day clock — ⛔ **`bash banchi/01-s1b-eccezione.sh oggi` once a day until
> 18 Aug**, and ⛔ **`/media/REMOTIX/s1b-certificato/` is not regenerated and
> `~/.remotix-s1b/` is not deleted**, or the clock starts again from scratch without anyone noticing for a
> week) · `01-s5-tela.sh` + `01-s5-pagina.html` + `01-s5-raccogli.py` (**S5**) ·
> `01-s7-rotella.sh` + `01-s7-rotella.c` + `01-s7-pagina.html` + `01-s7-raccogli.py` (**S7** — ⚠ and it
> closes with `--pulisci`, or the drop-in stays and **the next round does not know it was ours**) ·
> `01-s2-pagina.html` · `01-s3a-pagina.html` · `01-s6-pagina.html` · `01-s-telefono.sh` (the three that
> wait for a device).
>
> ⚠ Everything under `/media/REMOTIX` survives a restart; the server's rootfs does not —
> ⛔ **and that is why the benches' servers survive too**: on 10 Aug two of them were holding
> the ports eight hours later. The bench now checks it before starting.
> ⛔ **And since 10 Aug the ban of `RCP.md` §4.4-bis survives too, because it is on file**: between one bench
> and the next the unblock command is called, **never inside B8's round** (`FASI.md` §01-filo-nudo,
> rule B0.3).
>
> ### ⛔ Thirteen traps in two days, and two redone the day after — fifteen occurrences
>
> ⚠ *And the denominator is declared, because before it was not: what is counted is **the entries listed
> below**, and the two marked «redone» count **twice** because they were paid for twice.
> The title said «**Fifteen** traps» on **eleven** entries, and before that «Ten traps in two
> evenings» on eight: the count did not add up even then — finding **R11.20**, closed on the night of 10
> Aug 2026 by declaring what is counted and adding the **two** that were missing.* ⛔ *«A
> count without a denominator is not a measurement: it is a hope with a number in front»*
> (`LEZIONI.md` §1.9 point 4) — and here the number sums up **how much bench work was thrown away**.
>
> `grep -q` with `pipefail` · `| tail` eating the exit status **(redone the day after)** ·
> two paths passed as one string, with `2>/dev/null` hiding the error — **and that one
> printed a green** · `pkill -f` killing whoever runs it **(redone too)** · ports
> held by yesterday's servers · `>/dev/null` swallowing the **password prompt** · `setsid` that
> forks and falsifies the PID · `kill -0` confusing *forbidden* with *dead* · a fingerprint cut by
> **one letter**, which would have failed a candidate · a missing profile folder, and neither
> of the two sides saying so · ⛔ **the log cut at `tail -60`** and ⛔ **the case
> `respinto-poi-congedo` that made** the close race against the page's answer — *the two
> of B11, told in full above, both on **denominators*** · ⛔ **and Python's buffer, which made the bench accuse an innocent
> server**.
>
> ⛔ **This last one is the seventh guise, and it is the worst**: not a false red, but **a red
> pointed at the wrong defendant**. The bench waited for a log line to know when the
> first client was attached, and that line came out of the buffer only when the client **detached**
> — that is it declared «attached» a truth that had just expired. `LEZIONI.md` §1.9 point 7:
> *a file written and closed is a fact; a printed line is a hope about the moment
> someone will see it.*
>
> ⭐ Hence the **fourth rule** of `LEZIONI.md` §1.9 — *a measurement must declare what it
> looked at* — and its **corollary of 10 Aug**, born from the most serious defect so far:
> ⛔ **the probe declared a false denominator**, and its two legs measured the same thing
> while it said they were opposite. *A denominator is read **where the thing happens** — on the wire,
> not in the configuration — and whoever cannot read it there has it confirmed by a program that is not
> theirs.*
>
> ⛔ **And the corollary of the corollary, which applies to verdicts**: a round printed *«OK — i motori
> provati hanno registrato il loro esito»* with **zero engines tested**. *«All those tested went
> well»* is true even when those tested are zero — and it is the emptiest form of green there
> is, because it does not even need something to go wrong. **The denominator of
> an approval is how many things it approved**, and now the bench prints it and refuses to
> conclude if it is zero.
>
> ---
>
> ## Previous state — the evening of 9 Aug 2026
>
> **Phase 0 closed**: the benches reproduce v1's numbers (`FASI.md` §00-ambiente).
> **No line of product code written yet.**
>
> The day changed the product and then checked the change:
>
> | | |
> |---|---|
> | ⭐ **the client is the browser** | the two native clients and five phases of the plan fall — `DECISIONI.md` §1.6 |
> | **security is at two levels** | TLS for the transport, address/port/user/password for access — §1.7 |
> | **the second remote connection is refused** | `RCP.md` §8.2, reason `0x0F` |
> | 📖 **the sixth study** | [`STUDI.md` §web](STUDI.md#web), with four reports in `web/rapporti/` |
> | ⛔ **two adversarial reviews** | **46 numbered findings** — **29** in `web/rapporti/R1-revisione-rcp.md` and **17** in `R2-revisione-web.md` — **plus the 12 omissions** `O1`-`O12` of `R2` §2, and all **before the first byte**. ⚠ *It said «**51** contradictions», and that number cannot be found again with any written criterion: 29 + 17 = 46, and no sum declared anywhere gives 51 (finding **R11.20**, closed on the night of 10 Aug 2026 **by declaring what is counted**). The omissions are counted separately because they are not contradictions: they are lines that **were not there**, and by definition no check of the citations finds them* |
>
> ### The next step
>
> ⭐ **`FASI.md` §01-filo-nudo is open and already reviewed**, with the benches and **no line of
> product written** — the document is opened *before* developing (`PIANO.md` §0.1).
>
> ⛔ **Two adversarial reviews on the bench, before the product: 44 findings — 38 `[R]`, 6 `[?]`.**
> Neither of the two green, and the document was **rewritten**, not patched. The verdicts are
> in `fasi/rapporti/R3-` (the bench as a tool) and `R4-` (consistency with what is written).
> The form that kept repeating: **the check that says *no* always fell**, and three times it had already been
> written by whoever had been through it before.
>
> ⚠ **And the cure came out of that file**: `RCP.md` §4.1-bis still said that WebKit does not implement
> `serverCertificateHashes` — and it is **the arbiter**; `STUDI.md` §web got back the negative controls the
> reports prescribed; `PIANO.md` has the correct order and two benches relocated.
>
> ⭐ **And a decision of the user closed the count of devices**: **Apple is an extra, not a
> goal** — `DECISIONI.md` §1.8. Phone and DeX are there, the Mac is not and will not be obtained: **S1a leaves
> the phase**, the QUIC library is chosen on **two engines out of three**, and the line is written beside
> the choice. ⛔ Safari stays **served**, not **verified**: they are two different things, and the second
> is not written in the documentation until someone has measured it.
>
> ⚠ **The QUIC library stays open** and it is closed by a bench, not by paper (`DECISIONI.md` §6.4) —
> and it is the **first** bench to run, no longer the second.

⭐ **The client is a web page** *(decided on 9 Aug 2026 — `DECISIONI.md` §1.6)*. The two
native clients fall and with them five phases of the plan; **Windows comes back in as a place one
connects from**, without our writing a line for it and without submitting to its rules. It stays out
as a **server**, which was the real lever.

---

## Where to start reading

⛔ **In this order.** Whoever skips the first one ends up repeating mistakes already paid for.

| # | Document | What it contains |
|---|---|---|
| **1** | [`LEZIONI.md`](LEZIONI.md) | **the foundation**: how to measure, how to test, how to learn. Inherited from v1, which got stuck every time on a measurement that did not measure what we believed |
| **2** | [`SPECIFICHE.md`](SPECIFICHE.md) | **what** the product does, and what it does not do |
| **3** | [`RCP.md`](RCP.md) | **how** the two sides **talk**. It is the arbiter: in v1 it was `mstsc`, now it is this file |
| **4** | [`PIANO.md`](PIANO.md) | **the phases**, in order, each with its bench and its closing criterion |
| **5** | [`DECISIONI.md`](DECISIONI.md) | **why**: every decision with the date, who made it, and with what degree of certainty |
| **6** | [`MASTERPLAN.md`](MASTERPLAN.md) | ⭐ **what is done at the END**, and not before — decided by the user on 25 Aug 2026. ⛔ Every entry must say **what it costs never to do it, EVER**: an entry that costs nothing is deleted |

And for whoever writes or reviews, before touching anything:
[`CODER.md`](CODER.md) · [`REVIEWER.md`](REVIEWER.md)

> ### ⭐⭐ And since 27 Aug 2026 there is a net underneath: **`banchi/11-scatole/`**
>
> **Sixteen checks** that run by themselves before every push, on **four desktops**. They say: the
> session is born and **can be seen** · a window opens · the frames **change** · the key arrives
> **all the way to the screen** · the sound is not silence · it detaches and **is found again** · it closes and nothing
> remains · the **second** user opens the browser and the page **is seen from the client** · the log says
> **whom** it is talking about · the twin copies match — plus **five** that watch over the net itself.
>
> ⭐⭐ **And each one can prove it can turn red**: `[M]` full round of 27 Aug,
> **49 grafted faults and 49 caught**, 58 green verdicts, ⛔ no bench red.
>
> ⇒ It is read in [`fasi/11-la-rete-di-sicurezza.md`](fasi/11-la-rete-di-sicurezza.md), and launched with
> `banchi/11-scatole/11-gancio.sh`.

---

## The studies — ⭐ **all in a single document**, [`STUDI.md`](STUDI.md), since 16 Aug 2026

*They were eight files in the root. They became **eight chapters** of a single document, by decision
of the user. ⛔ **Not a summary**: the text is what it was, line by line, with the headings
lowered by one level. ⇒ A reference that said `kde.md` §3.3-bis now says `STUDI.md` §kde
3.3-bis, and **the chapter keys are the names the files had**.*

Readings of the code, done before writing. The five on the desktops answer the **fifteen**
questions of `LEZIONI.md` §3.

[`STUDI.md` §gnome](STUDI.md#gnome) · [`STUDI.md` §kde](STUDI.md#kde) · [`STUDI.md` §xfce](STUDI.md#xfce) · [`STUDI.md` §lxqt](STUDI.md#lxqt) ·
[`STUDI.md` §cinnamon](STUDI.md#cinnamon)

⭐ **And the sixth, which does not talk about a compositor**: [`STUDI.md` §web](STUDI.md#web) — the browser as a client,
with the four detail reports in `web/rapporti/`. ⚠ **It is the one that ages fastest**:
compositors are frozen by Debian, browsers update by themselves.

⭐⭐ **And the seventh, which talks not about a technology but about a PRODUCT**: [`STUDI.md` §xpra](STUDI.md#xpra) — whoever
already does this job, read in its code on 14 Aug 2026. ⛔ It should have been done **before**
the page (`PIANO.md` §1.3) and it was done **after**, at the user's request: ⇒ in the meantime
we had written a specification that contradicted itself, and he was the one who found it in thirty seconds
of use.

⛔ **And beside the four, a fifth file that is not a study**:
`web/rapporti/S-esiti-sonda.md` — **the measured outcomes** of the browser
probe (S7 · S1b · S5 · and the three that wait for a device), with the scene beside every
number and the recount that says which numbers have a provenance on disk. ⚠ *The «four reports»
above stay four: they are the reports of the **studies**, and it is a declared denominator.*

⚠ **`STUDI.md` §gnome-remote-desktop is not one of these** *(clarified on 9 Aug 2026)*. It studies **GNOME's
RDP server**, that is a competitor on the wire we threw away — not the desktop. With RDP
dead it lapses almost entirely, and it is written on a version Trixie does not have (51.alpha against
48.1). **On GNOME read [`STUDI.md` §gnome](STUDI.md#gnome)**, which talks about Mutter and stays valid.

---

## The folders

⚠ *This table listed **three** entries — `fasi/`, `fondamenta/`, `reference-*/` — and had neither `src/` nor
`banchi/` nor `web/`: **the folder that contains the product did not appear in the table that says what
the folders contain**. Completed on 11 Aug 2026, finding **R12C.1**.*

| | |
|---|---|
| ⭐⭐ `src/` | **the product**: the phase 1 server in C — **22 files, 9,647 lines** `[M]` 11 Aug 2026. RCP/1 over WebTransport, the two certificates, the page served by the server, the ban and its unblock command. ⛔ **It is not in git**, and no bench switches it on yet |
| ⭐ `banchi/` | **the phase 1 benches** and the browser probe, plus `banchi/rcp/` — the **twin** copy of `rcp.c`/`rcp.h`/`autenticazione.c`, today identical to the one in `src/` byte for byte. ⚠ Here the target is **the graft** inside `bsslserver`, not `src/` |
| `fasi/` | ⚠ **it exists only while a phase is open**, and contains that phase's document only: at closing it becomes a chapter of [`FASI.md`](FASI.md) and the folder goes back to empty (`PIANO.md` §0.1) |
| ⛔ ~~`web/rapporti/`, `fasi/rapporti/`~~ | **removed on 16 Aug 2026** by decision of the user — 94 files of agents' reports. ⭐ They remain whole in the history: how to reread or recover a report is in **`FASI.md`**, at the top |
| `fondamenta/` | ⚠ **it is not only an archive, and this line said it badly**: REMOTIX v1's heritage — 17,481 lines of C, the benches, the documents, the calibration scenes — ⭐ **but inside there are two LIVE things**, `fondamenta/banco/enter.sh` (the way one enters the test machine, **193 citations**) and `fondamenta/strumenti/sshpw.py` (**81**, called by the V2 benches). The full map — live, archive, dead, with the citations counted — is in **`DECISIONI.md` §6.1** |
| `reference-*/` | clones of the reference projects — **not versioned**, they are redone with `git clone` |

---

## The conventions

**Everything is in English** — code, documents, page, commits (`DECISIONI.md` §10.38, 10 Oct 2026). Some names
in the code are still Italian (`palco`, `cattura`, `sentinella`, `appunti`) until the mechanical rename.

**The marks** say how much a statement is worth, and must always be put:

| | |
|---|---|
| `[M]` | measured by us, on the hardware, with the date |
| `[R]` | read in a reference's code |
| `[S]` | read in a specification |
| `[?]` | hypothesised, **not yet measured** |

⛔ **A decision that rests on a `[?]` must be written as provisional.** An unmeasured reason
makes the decision half-taken (`LEZIONI.md` §2.3-quater).

**Decisions live in `DECISIONI.md`, only once.** The other documents refer, they do not
copy — and the entries carry ✅ (decided by the user), 🔸 (derived, correctable without discussion)
or ❓ (open).

⛔ **When a measurement contradicts a document, it is updated at the same moment**, with the date
and the source. A reference that ages silently is worse than no reference.

---

## The method

Two kinds of agents — whoever writes and whoever looks for contradictions — and review steps in **three
times** per phase: on the bench *before* the product exists, on the code before measuring it, on the
document before closing (`PIANO.md` §0.4).

⭐ **Why review weighs more than usual here**: by throwing away RDP we lost the external arbiter —
`mstsc` protested for free when we got it wrong. Now client and server are ours, and **two programs
written by the same hand that agree confirm nothing**.

⚠ With the web client **a piece** of it comes back: the page runs on three engines written by three
teams that do not know us, and their disagreement is a defect that declares itself. It is not enough,
but it is not nothing.

---

## The test machine

`192.168.0.2` — i5-13500T, 31 GB, Intel UHD 730 (for REMOTIX) and Radeon RX 6800 (reserved
for inference). It is reached with `fondamenta/strumenti/sshpw.py`, which reads the credentials from
`~/SERVER.ssh`.

There live the `devroot` for building and testing, the VM, and the package cache. **The sources do not**:
they are here, versioned.
