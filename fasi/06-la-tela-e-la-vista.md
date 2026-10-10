# Phase 6 — The canvas and the view

*⚠ Historical measurements, on the machine of that time. With phase 18 (without ffmpeg) the ones that the change invalidated were removed — encoding without the card and colour conversion with swscale; the ones for encoding on the card and for audio stay, because the new stream is identical (comparison of 30 Sep 2026). User's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

⭐ **Opened on 16 Aug 2026, evening**, with its document and **before a line of code**
(`PIANO.md` §0.1). The plan is `PIANO.md` §«Fase 6 — La tela e la vista»; the model for this
document is `PIANO.md` §0.2.

> **The scene the user will judge**: *«ridimensiona la finestra e l'immagine si adatta senza che
> le finestre dentro si muovano. Poi si riattacca da una macchina con un altro schermo e ritrova la
> sessione adattata — e ci scrive dentro.»*

---

## 0 · What this phase must produce, and what it must NOT redo

⛔ **Three quarters of this phase's work is already done and measured**, in the **tail of phase 4**
(`FASI.md` §04-si-comanda, 15 Aug 2026). ⇒ Those four rows **are re-measured, not
redone**:

| | state arriving from phase 4 |
|---|---|
| the **canvas agreed at attach** | ✅ `[M]` 1264×800 in a 1265×800 window, scale **1.000** |
| the **reattach at a different size** | ✅ `[M]` `SESSIONE` grants the canvas the stage already has, **0** frames discarded |
| the **view that rescales** | ✅ it was there since phase 2; the scale is 1 when the two canvases match |
| ~~the **live resize**~~ | ⛔ **OUT of the product on 17 Aug 2026** (`DECISIONI.md` §5.1-bis). It was `[M]` 6 ms on Mutter and **impossible** on KWin ≤ 6.7.4: the user removed the exception instead of maintaining it |

⛔ **And what stays OPEN, which is the real work of this phase:**

1. ⛔ **the reattach bench that PRESSES A KEY and MOVES THE POINTER afterwards** — `[M]` on 15 Aug
   the log showed that on a geometry change `libei` **recreates** the absolute devices and
   that `input.c` re-hooks them, ⛔ **but there is no bench that proves it**. `PIANO.md` asks for it with
   these words: *«è la forma "una prova verde col difetto vivo" esattamente dove si presenta»*;
2. ⛔ **the keyboard layout renegotiated at reattach** (`SPECIFICHE.md` §7.3): on Mutter a
   keymap change **destroys and recreates** the keyboard device, and the pointer to the old
   device stops working **without an error** `[R]` (`STUDI.md` §gnome §9);
3. ⛔ **the order between the birth of the devices and the applications already open**: a Wayland
   client started **before** the input devices exist **receives nothing** `[M]` 10 Aug —
   and at reattach the devices are destroyed and recreated **under applications that nobody
   will restart**;
4. ⛔ **the fallback on KWin ≤ 6.7.4 DECLARED IN THE LOG** (`SPECIFICHE.md` §6.3): what is verified is
   **that the line is there**, not that «it works anyway». KDE is phase 11 and it is not on this
   machine: it is tested on the fake host, like case 11 of `banchi/04-b31`;
5. ⏳ **the line missing from `RCP.md` §7.1**: what the server does when **the stage changes size
   by itself**, without any `ADATTA_TELA` having asked it to. Today the server re-reads the stage and
   **sends no `TELA`** — it works, but it is a product rule that the arbiter does not name;
6. ⚠ **the RCP/1 benches do not exercise the new route**: `01-b3-cliente.py` and `01-b4-validatore.py`
   stay green because the wire has not changed, ⛔ but **neither of them sends an `ADATTA_TELA`**;
7. `[?]` **the three things nobody has measured on the browser's numbers** (`SPECIFICHE.md` §6.1-bis):
   the **page zoom** (on Chrome `screen.width` does not change with zoom — but since the canvas is
   the **window**, is that calculation still wrong?), the **rounding** that can produce an **odd**
   side that `RCP.md` §4.5 rejects, and the **half pixel** of `margin: 0 auto`;
> ### ⛔ AND AN EIGHTH POINT WAS REMOVED — *user's remark, 16 Aug 2026*
>
> This list carried **multi-monitor** (`SPECIFICHE.md` §6.5), with a sub-phase of its own — the
> **6.7**, «the parametric multi-monitor» — which was to verify that the implementation stayed
> *«parametrica su N»*.
>
> ⛔ **The user stopped it**: *«il multimonitor non è previsto dal progetto. Sei andato fuori
> strada»*. And it is the right reading of §6.5, which declares it **out of scope as a feature**: a bench
> spent on a feature that is not being built is process that serves no purpose.
>
> ⭐ **What remains of that brief, and remains because it is phase 6 and not multi-monitor**: the
> **coordinates when the scale is not 1** (canvas and view different, `?adatta=no`, and the instant of
> resizing). ⇒ Moved to sub-phase **6.5**, which already owns `pagina.html` and the
> proportions of §6.2. ⚠ It is the same fault that made the mouse unusable on the DeX for two
> days: it comes from a scale taken for granted, and today it does not show because the scale is 1 by
> construction.

---

## 0-bis · ⛔ HOW WORK IS DONE IN THIS PHASE — the rules for the six benches in parallel

*The work is split into **six sub-phases**, each entrusted to an agent that does **all
four** steps: **development → test with measurements → debug → verification test with measurements**. The number
is not six by taste: the binding constraint is **`SPECIFICHE.md` §5.1 — a single graphical session per
user**, and every sub-phase that touches a real desktop brings one of its own.*

> ### ⛔ TWO MISTAKES OF THE COORDINATOR, WRITTEN HERE SO THEY ARE NOT LOST — *16 Aug 2026, evening*
>
> | | |
> |---|---|
> | ⛔ **one sub-phase was born off track** | the **6.7**, on the multi-monitor «parametric on N». The user stopped it: *«il multimonitor non è previsto dal progetto»*. ⇒ Seven agents become **six**, and the part that remains (the coordinates when the scale is not 1) moves to **6.5** |
> | ⛔⛔ **and four briefs left without `LEZIONI.md` §1.15** | *«Su Xvfb `requestAnimationFrame` non gira MAI»*, `[M]` 13 Aug 2026 — and in **Blink** the `resize` event is delivered **inside** the rendering round, so without frames it **never arrives**. ⇒ I had sent agents to measure **the path that follows the window** on a stage where that path **is not executed**, and the bench would have been **green**. Corrected on the fly, with the three cures of §1.15: the frame is beaten on purpose · **the stage is judged first** (*«IL PALCO, NON IL PRODOTTO»*, and one stops) · the limit is written **at the head of the bench** |
>
> ⚠ **The cause is a single one, and it is worth more than the two mistakes**: the briefs cited `LEZIONI.md`,
> `REVIEWER.md` and `STUDI.md` **taking the citations from other documents**, without opening them. The
> citations all held — ⛔ but what was in none of them, that is §1.15, could not
> appear. *A second-hand citation carries what someone has already found useful, and never what
> they did not know to look for.*

### The five rules of isolation

| | |
|---|---|
| ⛔ **a user and a port of one's own** | whoever starts a server starts **their own**: their own `--porta`, `--ban-file`, `--comando-socket`, `--certificati`. Without them, the ban of `RCP.md` §4.4-bis triggered by one bench puts **all** the others out of action, because they come from the same address |
| ⛔ **`prova` and 7700 ARE NOT TOUCHED** | they are the **user's** bench, the only place where today the real desktop can be seen. The recipe for making one of your own is `banchi/04-b31-terreno.sh` (own user · GNOME headless **without** `--virtual-monitor` · `render` group) |
| ⛔ **files are owned, and only those are touched** | the sub-phase table says which. A product file that is not yours **is not edited**: the fault is reported and one moves on |
| ⛔ **no agent writes `.md` and nobody does `git`** | the documents are written at the end, with the code frozen (remark **R12C**); `git` with many hands tramples the index. ⇒ ⛔ **and no report files are produced**: what a sub-phase measures comes back **into this document**, by the coordinator's hand |
| ⚠ **the tree on the test machine is a COPY** | you bring it when you start. If another agent cures a file you do not own, their cure **is not in your tree** — and that is intended: integration is done at the end, in a joint verification |

### The ports and the users — ⛔ taken, and not to be touched

```
7448 · 7501 · 7561 · 7571 · 7601 · 7691       other links': they are COUNTED, not touched
7700   the live product, user `prova`         ⛔ it is the USER's bench
7711-7715  bench 04-b31, user `provao1`
```

| sub-phase | machine | user | ports | tree on the server |
|---|---|---|---|---|
| **6.1** the reattach that commands | NIC-OS | `provai6` | **7781-7785** | `06-i-src` |
| **6.2** the keyboard that is reborn | NIC-OS | `provat6` | **7721-7725** | `06-t-src` |
| **6.3** the stage that changes size | NIC-OS | `provap6` | **7731-7735** | `06-p-src` |
| **6.4** the canvas on the wire | laptop | — | 7741-7745 *(local)* | local copy |
| **6.5** the page and the browser's numbers | laptop + NIC-OS | `provaw6` | **7751-7755** | `06-w-src` |
| **6.6** the arbiter exercises the canvas | NIC-OS | `prova2` | **7761-7765** | `06-a-src` / graft `b2` |

### ⚠ TIME measurements, with five benches running

⛔ Five graphical sessions and five encoders on the same iGPU **shift the milliseconds**. ⇒
Every time measurement carries the **load** (`uptime`) beside it, and the numbers that count — the
canvas passed to the stage, click → frame, login — **are repeated with the benches stopped** before
being declared. A number taken under load and not declared as such is a false number.

### The traps already paid for, which are not paid again

1. ⛔ **the child without `--parlantina` is silent**: `registro_dettaglio()` of `figlio.c`
   ends in nothing and the branches look «not triggered». *A diagnostic that is silent is not neutral:
   it lies*;
2. ⛔ **the silence clock steals 30 seconds from the tests**: if 30 s pass between preparing and provoking,
   `SPECIFICHE.md` §5.3 has already released everything and something else is measured;
3. ⛔ **the page releases by itself** on `blur`, `visibilitychange` and `pagehide`
   (`cl_rilascia_tutto`): from the browser the server almost never has anything to release, and **one
   certifies the page believing one is certifying the server**. To test the server, `window.cl_rilascia_tutto`
   is replaced with a stub;
4. ⛔ **the browser pilot cannot HOLD DOWN** a key: `javascript_tool` is used with
   `window.dispatchEvent(new KeyboardEvent("keydown", {code:"Enter"}))`, and only **non-letter** keys
   are held down;
5. ⛔ **every test user goes into the `render` group** — without it, the encoder falls back to software
   **declaring it**: `[M]` 100 ms per frame instead of 4.8;
6. ⚠ **the test machine's clock is TWO HOURS behind** the laptop;
7. ⛔ **the password never passes through the command line** (fault **D12**): a `0600` file
   written with `printf`, `--parola-file`, and a `trap` that deletes it;
8. ⛔ **never a redirection AROUND `ssh` or `enter.sh`**: the `sudo` prompt goes to
   stderr and a redirection eats it — the command stays hung forever, silently;
9. ⛔ **the witness of the real desktop**: inside the graphical session, a terminal with
   `while IFS= read -r _; do date +%s%N >> /tmp/testimone.txt; done` — every `Enter` that **reaches
   the desktop** writes a line in nanoseconds. An **empty** desktop witnesses nothing.

### The two routes for building

| question | route |
|---|---|
| **«compila?»** — twenty seconds | `bash src/costruisci-in-contenitore.sh` on the laptop (`podman` as user) |
| **«gira?»** — only on the test machine | `tar` of the sources into one's own tree, then `bash /media/REMOTIX/enter.sh --root 'bash /srv/src/<albero>/src/costruisci.sh'` |

⛔ **The container's binary is NOT copied to the test machine**: it is tied to
ngtcp2/nghttp3 of `/usr/local` **inside the image**.

---

## 1 · The seven sub-phases

*Each one does the four steps: **development · test with measurements · debug · verification test with measurements**.
⭐ And each one starts from an **adversarial brief**: «start from the hypothesis that what is written is
false, and look for the proof». Refusing the brief is allowed, as long as it is justified with a
concrete scenario.*

| # | title | what it closes | product files OWNED | benches |
|---|---|---|---|---|
| **6.1** | **The reattach that commands** | points **1** and **3** of §0: detach, reattach **at a different size**, and then **press a key**, **move the pointer** and **click** — with an application **opened before**. Plus the re-measurement of the four rows of phase 4 | `src/input.c` · `src/input.h` | `06-b33-*` |
| **6.2** | **The keyboard that is reborn** | point **2**: `DISPOSIZIONE` (0x0009) at reattach, the keymap that destroys and recreates the device, and the **right character** reaching the witness | `src/tastiera.c` · `src/tastiera.h` | `06-b34-*` |
| **6.3** | **The stage that changes size** | the chain `figli_ritela()` → `cattura_ridimensiona()` on the **real compositor**: repeated resizes, the limits of §4.5, and the case **«the stage changes by itself»** (point 5, product side) | `src/figlio.c` · `.h` · `src/cattura.c` · `.h` · `src/mutter.c` · `.h` | `06-b35-*` |
| **6.4** | **The canvas on the wire** | points **4** and **5** arbiter side, on **bare** `rcp.c` with a fake stage: `COMPOSITORE_INCAPACE` **declared in the log**, the backstop of §7.1, `NON_ORA`, `MISURA_FUORI_LIMITI`, and ⛔ **the coordinates in flight** in the second after `TELA(ADATTATA)` — which nobody had ever tested | `src/rcp.c` · `src/rcp.h` (+ the twin `banchi/rcp/`) | `06-b36-*`, extends `04-b31-tela.c` |
| **6.5** | **The page and the browser's numbers** | point **7**: page zoom on two engines, roundings and odd sides, the half pixel of `margin: 0 auto`, the scale and `pixelated`, the bands of §6.2, `?adatta=no\|segui`, and the **item switched off** on `COMPOSITORE_INCAPACE` | `src/pagina.html` | `06-b37-*` |
| **6.6** | **The arbiter exercises the canvas** | point **6**: the test client sends `ADATTA_TELA` and `VISTA`, and the validator **can accuse** a missing or unsolicited `TELA` — certified with faulty recordings, each accused on the byte declared beforehand | *none* — benches only | `01-b3-cliente.py`, `01-b4-validatore.py`, `01-b4-registrazioni.py`, `06-b38-*` |
| ~~6.7~~ | ~~the parametric multi-monitor~~ | ⛔ **removed by the user on 16 Aug 2026** — see the box in §0 | — | — |

⛔ **And a third moment that this phase does NOT have yet**: `PIANO.md` §0.4 wants the reviewer **at three
moments**, and the first is **on the bench, before the product** — *«il banco è il primo imputato: un
difetto nel banco non lo trova niente, perché dà fiducia»* (`REVIEWER.md` §1). Here the six agents
write their own bench and certify it **by themselves** (with the grafted fault, which is the part that
holds). ⏳ The adversarial review **restricted to the six new benches** is proposed to the user when the
reports arrive: what survives this phase is the benches, not the measurements.

---

## 2 · The bench

> ## ⛔⛔ THE NUMBERS IN THIS SECTION WERE REVIEWED ON 21 AUG 2026, AND MANY DO NOT HOLD
>
> *«Chi scrive un banco lo certifica nello stesso giro»* is not enough: **whoever certifies it alone
> absolves themselves**. The adversarial review — the moment that `PIANO.md` §0.4 asked for and that this phase
> had not had — says that **five benches out of six do not hold as certification**, and which
> measurements fall with them. ⇒ **Read §5.5 before trusting a number below.**

*Six new benches, one per sub-phase, each **certified by its author in the same round** with
faults grafted into a **copy** — the rule born on 11 Aug (*«chi scrive un banco lo certifica
nello stesso giro, o il conto non cala mai»*).*

| bench | what it mounts | cases | the positive control |
|---|---|---|---|
| `06-b33-*` (6.1) | ground `provai6`/7781 · **Wayland witness** and `gnome-terminal` **opened before** the detach · client that detaches, reattaches at a different size and **only then** types, points and clicks | 7 | **5 faults** in a copy of `input.c`: G2→C2 · G3→R1,R2 · G4→C6 · G5→C3,C4 · ⭐ **G1 lights up nothing**, and see §5 |
| `06-b34-*` (6.2) | ground `provat6`/7721 · ⭐ **the expected value is computed by the product** (`tastiera_posizioni_per()` called from outside) · witness that records **the character**, not the count | 6 | **2 faults**: «the keymap is read only once» → red on the declared case · «the keys go away with the device» → ⛔ **green anyway**, and see §5 |
| `06-b35-*` (6.3) | ground `provap6`/7731 · scene that moves at **50 ms** · client that sends `ADATTA_TELA` and counts the `TELA`s | 5 rounds | ⛔ ~~5 faults out of 5~~ → **3 confirmed stable (G1 G2 G3, 3 rounds out of 3) · 1 non-discriminating (G4) · 1 INTERMITTENT (G5, 2 out of 3)**, `[M]` 22 Aug. ⭐ And the fourth count — «not judged» — exists on purpose: before, G5 would have **vanished from all three columns** without a line saying so. 📖 §5.9 |
| `06-b36-*` (6.4) | **bare** `rcp.c` with a fake stage **plus** the input channel and **the captured log** — the half that `04-b31` does not look at | **23** | **19 faults out of 19**, each red **in the case declared beforehand** |
| `06-b37-*` (6.5) | HTTP collector with a probe inside the page, **on the two engines** (no CDP, which is Chrome only) · external truth `xwininfo` · verdicts **on the pixels** (`ffmpeg x11grab`) | 7 scenes | the zoom verified on `devicePixelRatio` **and not on the key pressed**; every zero with its denominator (20 points · 2 523 columns · 4 resizes) |
| `06-b38-*` (6.6) | the test client and **the arbiter** exercising the canvas; mutations of the arbiter itself | **49** recordings | **49 accused on the byte declared beforehand** · 4 outcomes covered · **19 mutations out of 19** seen |

⭐ **And two old benches were repaired, not just extended**:

| | |
|---|---|
| ⛔ `04-b31-certifica.sh` | **G8's anchor had expired**: on 16 Aug `rcp_tela_rimanda()` was born between the two functions the anchor named, and since then **the most serious of the twelve faults was no longer grafted**. The certifier said so (`??`) and nobody ran it. ⇒ Again **12 out of 12** |
| ⛔⛔ `01-b3-cliente.py` ↔ `01-b4-validatore.py` | the client wrote `RCPREG 0x00 0x01`, the arbiter demanded `0x02`: **since 12 Aug every B3 trace came out «broken recording»** and the five checks of `01-b3-lancia.sh` failed. ⭐ **Neither of the two files was broken on its own: the fault lay between the two** |

## 3 · What was developed

⛔ **Nine product cures, and none was planned**: this phase was meant to **re-measure** three
quarters of work already done, and it found nine real faults under that work.

| file | what, and who |
|---|---|
| `src/rcp.c` · `.h` (6.4) | ⛔ **`VISTA` (`0x0008`) fell into the `default`**: a conforming client that declares it has resized **lost the session** — literally the symptom that remark R1.17 exists to make impossible. Now there is `case T_VISTA` (~4950), which validates, keeps and writes, **without touching the canvas or the encoder** · an `ADATTA_TELA` of **false length** passed the resize to the stage **before** saying farewell (`misura_campi()`, R9.4 reopened) · the stage recalled to the **old** canvas while a request was **in flight** (`tela_richiama_il_palco()`, ~2847) · the grace second that opened **with date zero** · the view of `ATTACCA` read and thrown away, now kept (`rcp_vista()`) and zero rejected |
| `src/figlio.c` (6.3) | ⛔ `GIA_COSI` with the format not yet negotiated answered **`TELA(RIFIUTATA, NON_ORA)` on a healthy session** (`:3973-4032`): `cattura_misura_negoziata()` returns `FALSE` **without writing anything**, and for `rispondi_tela()` zero means «I did not make it» · ⭐ **`input_rilascia_tutto()` before `cattura_ridimensiona()`** (`:3964`), the cure asked for by 6.1 |
| `src/input.c` (6.1) | ⛔ the fault **declared instead of silent**: `segna_orfani()` (`:630-648`) writes **at the instant the damage occurs**; a release that Mutter swallows **no longer counts as sent** (returns −1, `:256-336`); `input_rilascia_tutto()` separates «released» from «**not releasable**», which before ended up in the same number **and absolved it**; `input_orfani()` for the bench. ⛔ And the comment that said *«al ricambio si rilascia sul dispositivo nuovo, che è l'unico posto dove il rilascio arriva»* was **refuted and rewritten** |
| `src/pagina.html` (6.5) | ⛔⛔ **`Math.round` → `Math.floor`** in `misura_vista()` (`:1450`): at a **non-integer** `devicePixelRatio` the product `clientWidth × dpr` asked for **a pixel that does not exist** ⇒ canvas wider than the window ⇒ scrollbar ⇒ −22 px of height ⇒ **scale 0.9651** ⇒ `auto` ⇒ **interpolated text** · the «fit the desktop» item now **really switches off** after `COMPOSITORE_INCAPACE` (`:2823, 3581, 3587, 3727`), where before one was sent at every resize · repeating the request applies **only to `NON_ORA`** (`:3784`) |
| `banchi/rcp/` | the twin kept **identical byte for byte**, verified with `cmp` |

⏳ **And a user decision being implemented** (sub-phase 6.2, second round):
`DECISIONI.md` §5-bis.7 — **the keyboard layout is commanded by the client**.

## 4 · The measurements

*Filled in along the way. Each row: what · the scene · the expected value declared BEFORE · the measured value ·
date and time · the machine's load.*

### ⭐⭐ 4.1 · THE THIRD CLIENT: WINDOWS — and the user tested it, on 16 Aug 2026

> **«Ho fatto un test con Windows: anche in questo caso funziona tutto e con performance
> eccellenti.»** — the user, 16 Aug 2026, evening, on the live product (port 7700)
>
> ## ✅ **«Il test su Windows lo dichiaro superato al 100 %.»** — the user, 16 Aug 2026
>
> ⛔ *A verdict the user did not give is not written: this is his sentence, with the date. And it is
> a judgement, that is the yardstick of **I8** — «the yardstick is what the user sees, not the number that comes
> out of the bench».*
>
> ## ⭐⭐ AND ON WHAT IRON — *«ricordiamoci sempre che otteniamo performance eccellenti su una Intel integrata»*
>
> *The user, 16 Aug 2026, right after the judgement. ⛔ And it is not a compliment to the iron: it is the
> **qualification of the measurement**, and without it the number does not say what it is worth.*
>
> `[M]` The card is the **Intel UHD 730** (`i915`, `0000:00:02.0`, `renderD128`) — an office
> integrated GPU. ⛔ The **Radeon RX 6800** of the same machine is **excluded on purpose** with a udev rule
> (`DECISIONI.md` §4.6-ter and §4.6-quinquies), by the method rule the user set on 15
> Aug: *«i test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco. La solidità
> del sistema la si vede su GPU poco potenti»*.
>
> ⇒ ⭐ **From here on, in this project, a performance number is reported together with the
> iron it was taken on.** Three client systems — Linux, Android/DeX and now Windows — judged
> «tutto perfetto» / «eccellenti», and behind them there is a UHD 730.

⛔ **It is a client operating system that had never been tested**: until tonight the measured clients
were the **Linux** laptop and **Android/DeX**. `SPECIFICHE.md` §11.5 declares the **engines** (Blink ·
Gecko · WebKit) and not the systems: ⏳ the line about Windows must be added at the close of the phase.

⭐ **And the measurement is not his sentence: it is the server's log**, `[M]` 16 Aug 2026, 20:43
(test machine time, two hours behind):

| | |
|---|---|
| the decoder ceiling declared by the client | `video.misura_massima=3840x2160` |
| the session | `tela=2540x868 vista=2541x869 disposizione=it`, from `[192.168.0.21]` |
| the invariant **I2** | *««prova» è già servito dal figlio pid 588775: NON ne nasce un secondo»* — the stage is the same because it belongs to the **session** (I4) |
| the stream | `3829 fotogrammi consegnati (10 chiavi), 0 guasti`, codec 1, 60/s requested; `1197 spediti, 7 abbandonati` |

⛔⛔ **And the fact that matters for this phase: his window was ODD on both sides —
2541×869 — and the granted canvas is 2540×868**, truncated down by one pixel per side. ⇒ The two `[?]` of
`SPECIFICHE.md` §6.1-bis (the rounding that produces an odd side · **the half pixel of
`margin: 0 auto`**) showed up **together, on a real user**, and produced no visible
symptom. ⚠ *«He saw nothing» is not a measurement*: the measurement is the job of sub-phase
**6.5**, which now knows **which number** to reproduce.

### ⭐⭐ 4.1-bis · And the scale of that PC is **125 %** — the first NON-INTEGER `devicePixelRatio` in the project's history

*Declared by the user on 16 Aug 2026. Until tonight every measurement of this project — Linux and
Android/DeX — had been taken with an **integer** factor.*

⇒ The case is completely determined, and `[R]` reading `src/pagina.html` (`cornice()`, ~1889)
explains **why it holds**:

| | |
|---|---|
| dpr | **1.25** ⇒ window `2541×869` physical = `2032.8 × 695.2` CSS |
| the drawing scale | `s = min(2541/2540, 869/868, **1**)` ⇒ ⭐ **the third term wins: `s` is exactly 1** ⇒ `image-rendering: pixelated` **on**, no resampling ⇒ **the text stays sharp** |
| the grid | `2540 / 1.25 = 2032` CSS px **exactly** ⇒ the canvas falls on the device pixel grid, without fractions |
| ⛔ the remainder | `2032.8 − 2032 = 0.8` CSS px split by `margin: 0 auto` ⇒ **0.4 CSS px per side = half a PHYSICAL pixel** |

⇒ ⭐ **The half-pixel `[?]` is no longer hypothetical: it was the user's configuration, and the user
judged.** With **I8** in hand that `[?]` is **closed by the judgement**. ⚠ The measurement on the pixels remains
the job of **6.5**, and now it answers another question — not *«is it fine?»*, which is decided, but
***«why it is fine»*** — which is what prevents breaking it tomorrow without noticing.

⏳ What remains unmeasured is **150 %** (where the third term of the `min` might no longer save it) and
any non-integer dpr **with an even window**.

### 4.2 · The four rows of phase 4, RE-MEASURED under this phase

⚠ **All under load** (load 0.2-2.1, up to five benches running together): ⛔ they must be **repeated with
the benches stopped** before becoming the phase's numbers.

| what | expected *declared beforehand* | `[M]` measured | who |
|---|---|---|---|
| canvas agreed at attach | the size requested, even sides | **1264×800**, three rounds out of three | 6.1 |
| reattach at a different size | `SESSIONE` grants **the stage's one** (I4) | **1264×800** + line `RIPIEGO DICHIARATO (§4.5)` | 6.1 |
| frames discarded for size | **0** | **0** in all rounds of all sub-phases | 6.1 · 6.3 |
| **the canvas passed to the stage** *(⛔ it was labelled «live resize»: see §5.14)* | ~6 ms (`[M]` 15 Aug) | **5 ms** · **4 ms** median over 9 changes (3-13) | 6.1 · 6.3 |
| `SESSIONE` → first frame, stage **to be mounted** | ~311 ms (`[M]` 15 Aug) | **335 ms** | 6.3 |
| ⭐ same, stage **already up** (I4) | — | **11 · 13 · 17 · 24 · 28 · 37 · 106 ms** | 6.3 |
| full round `ADATTA_TELA`→`TELA` server side | — | **40 ms** (31-60); Mutter takes **32** of them | 6.3 |
| **monitor** scale (server side) | 1.000 | **1.000** on «Meta-0», and the line is written **even when it is good** | 6.1 |
| ⛔ **drawing** scale (page side) | 1.000 and `pixelated` | **1.000** on the pixels (986 out of 986) — ⚠ and see §4.3 | 6.5 |

### 4.3 · ⭐⭐ The page, the pixels and the browser's numbers — the three `[?]` of §6.1-bis, closed

| `[?]` of `SPECIFICHE.md` §6.1-bis | outcome | `[M]` |
|---|---|---|
| **page zoom falsifies the canvas** | ⭐ **CLOSED — it no longer falsifies** | same canvas requested at **100 · 150 · 50 %**, on Chrome 151 and Firefox 140esr, 21 widths, gap **2 px**. ⛔ But the sentence was false **for another reason**: not the zoom, the **rounding** |
| **rounding can produce an odd side** | ⭐ **CLOSED, with a fault found and cured** | ⛔ at `dpr 1.5`: **4 widths out of 12** (Chrome) and **2 out of 12** (Firefox) asked for a canvas **wider than the window** ⇒ scale **0.9651**, `auto`, interpolated text, and in Firefox **one desktop column cut off**. ⇒ After the cure (`Math.floor`): **0 out of 48** and **0 out of 36** |
| **the half pixel of `margin: 0 auto`** | ⭐ **CLOSED** | it **exists** (`rect.left` = **0.500 physical px**, reproduced in the user's exact configuration) and ⭐ **does not reach the pixels**: **0 grey columns out of 2 523** — the engine snaps to the grid. It stays `[?]` **only on a real GPU and on DeX** |

⭐ **The Windows user's case, reproduced in the lab**: `dpr 1.25`, window `2559×977`, view
`2541×869`, canvas `2540×868` ⇒ **s = 1.000000** (the ratios are 1.000394 and 1.001152: ⛔ **what
holds the scale is the cap of `Math.min`, not the ratios**), `pixelated`, drawing **2540 px**,
**0 grey columns out of 2 523**.
⇒ ⭐ **The phase's guard number**: *if `image-rendering` reads `auto`, the text has gone back to
interpolated*.

| and the page's other scenes | `[M]` |
|---|---|
| «it is laid out, not stretched» (§6.2) | proportion gap **0.00-0.07 %**; bands **black and outside the buffer**; at scale 0.70 the price of non-1 shows: **52.5 %** (Chrome) and **29.7 %** (FF) of blurred columns |
| ⭐ **coordinates at scale ≠ 1** | **20 points on two engines, worst gap 1 px** (Firefox only, bottom-right corner at s=0.707); with resizing **0 px after settling**, ⚠ and a transient of **97 px** while the image changes size under the finger |
| the three modes of `?adatta=` | `no` **0** · off by itself **0** · `segui` **4 out of 4**, with the 4 `resize`s arrived in all three — ⇒ **I6 respected** |
| the item switched off on `COMPOSITORE_INCAPACE` | ⛔ before: **it never faked success, but it did not switch off** (5 `ADATTA_TELA` after the refusal) ⇒ after the cure **0 and 0**, guard active 4/4 |

### 4.3-bis · ⛔⭐ 17 AUG 2026 — the same page **without** live resizing

*`DECISIONI.md` §5.1-bis: the feature has left the product. The two rows above are yesterday's
measurement and stay as history; these are today's measurement, on the page the phase delivers.*

⛔ **Why re-measure everything and not only the two scenes touched**: **code was removed** from the page,
and the other four scenes read it. A regression there would have been seen by nobody.

| | `[M]` 17 Aug 2026, `06-b37`, each scene in an invocation of its own |
|---|---|
| ⭐ **the whole battery** | **12 combinations out of 12 green** — six scenes (`numeri` · `pixel` · `sfora` · `coordinate` · `modi` · `voce`) for two engines (Chrome, Firefox), **zero red lines** |
| ⭐ the modes of `?adatta=`, **with their meaning reversed** | `no` **0** · default **0** · `segui` **0**, with **4 `resize` out of 4** arrived in all three ⇒ the canvas **is not touched in a live session**, not even with the old address |
| ⭐⭐ **the positive controls**, which were not there yesterday | **spy SEES** in all rounds (a `chiedi_tela` called by hand is counted) and `typeof tela_forse_chiedi` = **`undefined`**. ⛔ Without them those three zeros would have been green **even with the spy broken** |
| the item switched off, V4 with the new question | after an injected `COMPOSITORE_INCAPACE`: **4 resizes arrived, 0 arrivals at `chiedi_tela`**, `tela_spenta` = `True`, and the declaration to the user comes out: *«Questo desktop non sa cambiare misura: l'immagine viene adattata alla finestra dal browser»* |
| the stage, judged before the product | **183-184 frames in 3 s · 6 `resize` beaten → 6 arrived** (`LEZIONI.md` §1.15 does not reproduce here) |
| ⏱ **what it costs to redo it** | **~35 s per scene** · ~3 min 30 s one engine · **~7 minutes** the whole battery on two engines |

> ### ⛔ AND A FAULT OF THE BENCH, NOT OF THE PRODUCT — to be cured, not cured
>
> `bash banchi/06-b37-lancia.sh tutti tutte` gives **twelve fake reds**: after the first scene the
> browser does not reopen («nessuna finestra X per il pid …») because `spegni_motore` kills the pid
> of the wrapper and not the one holding the window. ⭐ **The benches behaved well** — they
> stopped instead of measuring, that is they told «zero» apart from «I did not look» — ⚠ but whoever runs
> that line next time loses half an hour looking for a fault that is not there.
> ⇒ **Until it is cured, one scene at a time is run.**

### 4.4 · The canvas on the wire, and the arbiter

| | `[M]` |
|---|---|
| `06-b36` on bare `rcp.c` | first round **15/20 · 5 red** ⇒ after the cures **23/23**, and **19 faults out of 19** |
| `04-b31`, the phase 4 bench | **19/19** and **12/12** (it was 11/12 because of the expired anchor) |
| the arbiter against the **product** | **5 rounds out of 5 conforming**, 6 `ADATTA_TELA`/`TELA` pairs closed — `rcp.c` `8ce10fe5…`. ⭐ And the most promising case gave the opposite: `ADATTA_TELA(1281×800)` receives **`TELA(ADATTATA, 1280×800)`** — the server rounds to even **and declares it in the field** |
| the certified validator | **49 recordings out of 49** accused on the byte declared beforehand · 4 outcomes covered (conforming 13 · non-conforming 28 · broken 7 · nothing to judge 1) · **19 mutations out of 19** |
| the limits of §4.5 on the real stage | 320×240 **ADATTATA** · 318×240 **RIFIUTATA** · 1281×801 → **1280×800** · 7682×4320 **RIFIUTATA** · with the client's ceiling 3842×2160 → **3840×2158**, fallback declared |
| the **coordinates in flight** (§7.1, never tested before) | within the second: **saturated and written** · **1000 ms inside, 1001 ms `ERRORE_PROTOCOLLO`** · the real error is not covered by the grace |
| the stage that changes **by itself** | **zero unsolicited `TELA`, ever** (wire: 3 changes in a row; product: recalled, **back in 37 ms**, 0 frames of wrong size to the client) |

### 4.5 · The keyboard at reattach

| scene | expected *declared beforehand* | `[M]` measured |
|---|---|---|
| session `it`, reattach declaring `it` | `aèò\@a` twice | ✅ identical (positive control) |
| session `it`, reattach declaring **`us`** / **`de`** | if §7.3 is true, the characters change | ⛔ **identical to `it`** ⇒ §7.3 **refuted**: see `DECISIONI.md` §5-bis.7 |
| ⭐ the **session** goes `it`→`de` with a live stage | keymap re-read ⇒ `azy\a` | ✅ **`azy\a`**, `ricambi_tastiera` 0→1, fingerprint `8315b8d9`→`d1c54543` |
| detach with **Shift really pressed**, reattach | released ⇒ lowercase | ✅ `rilascio al distacco: 1`, witness **`az`** |
| same, but **the device dies with the key down** | release on the **new** device | ✅ `ricambi_tastiera` 4→5, `az` |
| malformed · unknown · with-variant layouts | `ERRORE_PROTOCOLLO` · `SESSIONE_NON_SERVIBILE` · — | ✅ `0x0b` × 4 · `0x0e` × 3 · ⛔ **`it(nonesiste)` opens the session** |

### 4.6 · ⛔⛔ The fault that no log declared — the click that dies

| | `[M]` 16 Aug 2026, bench `06-b33` |
|---|---|
| the scene | `BTN_LEFT` **held down** → `ADATTA_TELA` → the devices are recreated → it is released |
| what happens | the release of the **key** arrives, that of the **button** does not ⇒ ⛔ **and the next round, identical to one that had been green on everything, no longer delivers ANY click — forever** |
| how it heals | ⭐ only by restarting the server (which forces `drop_device`) |
| the chain, all `[R]` **inside Mutter** | `remove_viewport_devices()` (`meta-eis-client.c:197-206`) **does not go through `drop_device()`** · `handle_button()` (`:612-621`) **silently swallows** the release for a button not pressed *on that* device · `update_button_count()` (`meta-seat-impl.c:899-908`) belongs **to the seat**: the press of the dead device keeps it at 1, and it **never goes down to zero** |
| ⇒ | ⭐ It is *«su Android il mouse non prende più i click»* (the user, 15 Aug) **for a cause different from the one cured then** |
| the cure | **one line**: `input_rilascia_tutto()` **before** `cattura_ridimensiona()` — applied, `figlio.c` · `codificatore_di()` |
| ⛔ **and it is not enough** | `[M]` the devices are recreated **even without a size change**: every `cattura_risveglia()` (400 ms, still scene and key due) is followed 8-24 ms later by a swap — **3 wake-ups, 3 swaps**, with **zero `ADATTA_TELA`**. ⇒ That is **exactly while the user holds the mouse down on a still desktop**, and the obvious cure (releasing at every wake-up) **would destroy every drag** |

### 4.7 · ⭐⭐ The user's decision IMPLEMENTED — `Ctrl+Z` from a German keyboard

*`DECISIONI.md` §5-bis.7, confirmed by the user on 16 Aug 2026 and implemented the same night.
⛔ The scene's number is not a character: it is a **shortcut**, because letters travel as
letters (§5-bis.6) and what moves are the **positions**.*

| scene | expected *declared beforehand* | `[M]` |
|---|---|---|
| client declares `de`, session `it`, the `Ctrl+Z` of a German keyboard is pressed (evdev **21**) | renegotiated ⇒ **`1a`** (undo) · not renegotiated ⇒ **`19`** (redo) | ⭐ **`1a`** |
| ⛔ the same scene **with the cure removed** | **`19`** | **`19`** — and the server **predicts the symptom by itself**: *«RIPIEGO DICHIARATO (§5-bis.7): … le SCORCIATOIE no: `Ctrl+Z` finirà sul tasto che quella posizione ha nell'ALTRA disposizione»* |
| reattach declaring `us` on session `it` | `a\@a` (`è`/`ò` do not exist on `us`) | **`a\@a`** — ⚠ yesterday it was `aèò\@a` |
| `DISPOSIZIONE` (`0x0009`) with the session open | connection **alive**, keymap changed | **alive**, `KEYMAP CAMBIATA → de [German]` — ⚠ yesterday: farewell `0x0b` |
| `hu` · `tr` (which the machine **has**) | now **accepted** | session opened — ⚠ yesterday `SESSIONE_NON_SERVIBILE` |
| `it(qwertz)` · `it(nonesiste)` | now **rejected** | `0x0e` — ⚠ yesterday they **opened** |
| `de(neo)` | accepted and loaded | `de+neo` → **`[German (Neo 2)]`** |

⛔ **And the chain crosses a process boundary**: the client's bytes are in the **parent**, `libei`
is in the **child**. ⇒ Five files out of eight did not belong to whoever wrote the cure, and the missing
part was **delivered as a patch** (`banchi/06-b34-cucitura.py`, 13 pieces with verbatim
anchors) instead of being applied on the sly while another agent was working on the same files.
⭐ **Applied by the coordinator on 17 Aug 2026, with the benches stopped**: the product compiles **without
warnings** and `04-b31` stays **19 out of 19**.

⚠ **Two declared limits**: `input_disposizione()` is **GNOME's** (`libei` has no
client→server direction for the keymap, and Mutter offers no setter: the lever is `input-sources`) ⇒ **on KWin
it will not work**, and the right place is `mutter.c` with the twin `kwin.c` — it is phase 11 work. And
`gsd-keyboard` can overwrite us again: it is not prevented (it is *«il contorno»* of `CODER.md` §4.1-bis), **it is
measured**.

⛔ **And the question this decision promotes to main question**: the page **guesses** the
layout from the browser's language (`src/pagina.html:2585-2624`, `[?]` declared there by the code
itself). As long as the server threw it away it did no harm; now that it **obeys**, a badly guessed
layout **really changes the user's keyboard**.

### 4.8 · ⭐⭐⭐ THE JOINT VERIFICATION — 17 Aug 2026, **with the machine idle**

*Six agents worked in parallel, each in its own tree: ⛔ **nobody had ever measured the
product with the others' cures inside**. This is the only measurement that looks at them all together, and on
a silent machine — because all of last night's milliseconds were taken with **five benches
and five encoders** on the same iGPU.*

| | |
|---|---|
| the silence | load **0.90 → 0.12** (0.07-0.13 during the measurements): servers 7721 and 7731 and three GNOME sessions switched off |
| the tree | a single one, `06-i-src`, built on the test machine. Fingerprints **identical to the repository**: `rcp.c 283ffe7b` · `figlio.c ca7b6a97` · `input.c 51a8ef08` · `tastiera.c e7590d32` · `pagina.html 55bc9e77` |
| ⛔ `prova` and 7700 | **never touched**: the same two pids from start to end, and the port still answers |

| scene | expected *declared beforehand* | `[M]` measured |
|---|---|---|
| ⭐ **A · dragging the border** | **0 broken out of 18** | ⭐ **0 out of 18** — the 1st request `NON_ORA` **immediately**, the 2nd `ADATTATA`, final canvas = that of the **second** in **31.7 ms** median (23.8-45.3) · **0** wrong size · **0** discarded · ⛔ **no wait of 3 s**. And **0 out of 10** even at 5 ms apart, and **0 out of 10** under CPU load **10.9** |
| ⭐ **B · the click held down** | the release arrives, and the clicks of the **second round** all arrive | ⭐ log: *«RILASCIATI 2 fra tasti e pulsanti PRIMA di ridimensionare»* · and in the second round, **without restarting the server**, the witness sees **all nine acts, click included** |
| ⭐ **C · the keyboard that commands** | **`1a`** | ⭐ **`1a`**, with the whole chain in the log: `§5-bis.7 «de» chiesta` → `tastiera TOLTA (ricambio 1)` → `KEYMAP CAMBIATA → de [German]` |
| ⛔ **D · the milliseconds, with the machine idle** — ⚠ **NOT RECOMPUTABLE, see §5.6** | retake the five numbers | the canvas passed to the stage **4 ms** median (3-7, n=10) · Mutter **39.5 ms** · full round server side **44.5 ms**, **10/10 ADATTATA** · `SESSIONE`→1st frame **25 ms** with the stage up and **203-220 ms** to be mounted (it was 335) · **0** discarded, **0** wrong size |

⭐ **And the positive control paid off where it counted**: with the line in `figlio.c` · `codificatore_di()` switched off and recompiled,
the click case goes back to **DIFETTO_VIVO** — in the second round **no button arrives any more**, only the
keys, that is §4.6 to the letter. Switched back on, everything returns.

⛔⛔ **But on dragging the positive control did NOT pay off, and it must be said loudly**: removing 6.4's cure
(`rcp.c` · `tela_richiama_il_palco()`, the recall to the size **in flight**) still gives **0 out of 18**. ⇒ **It is not
that cure that holds this scene**, and the **4 out of 18** measured by 6.3 **were not
reproduced** — neither at 10-35 ms, nor at 5 ms, nor under CPU load 10.9. ⚠ The difference that remains between the
two measurements is **GPU contention**: that day there were five encoders on the same iGPU, and
with the machine idle that condition is not recreated. ⇒ ⛔ **A's green holds «with the machine idle and
under CPU load», not «under GPU contention»**, and that is how it must be read until someone reproduces
the original scene.

| the wire benches, redone on the current code | |
|---|---|
| `04-b31` · `06-b36` · `01-b4` · `06-b38` | **19/19 + 12/12** · **23/23 + 19/19** · **49/49** · **19/19** ⇒ ⭐ **no integration regression**, and the build from scratch emits **not a single warning** |

---

### 4.9 · ⭐⭐⭐ THE HUNT FOR ARTEFACTS IS CLOSED — 17 Aug 2026 evening, and **the fault was not ours**

*For two days the user saw **rectangular blocks** in the still areas of the desktop, and the
hunt killed seven hypotheses one at a time (the list was in the resume box of
`PIANO.md`). ⛔ The eighth was not on the list, because **it lay after the last point that a program
can read**.*

**The symptom, with its measurement**: blocks of **64×192** that move with the content. `[M]` The
user's real session, **while he was seeing them**, said `dipinti 23 · video 23→23 · salt 0 · buchi
0 · ord 0 · mis 0 · err 0`. ⇒ No frame was missing: **the pixels inside the frames that arrived
were corrupted**, and no counter could see it.

#### The suspects, cleared one by one and with the measurement beside them

| suspect | the proof |
|---|---|
| the capture / Mutter | ⭐ `scatto-ingresso.bgrx`, taken **while the blocks were in view**: **clean** |
| the encoder, 300 deltas in a chain | the same bytes given back to `ffmpeg`: **0 superblocks spoiled out of 600**, mean gap **1.68** levels |
| the shape of the pieces on the wire | **300** temporal units, **1** frame each, none hidden |
| the browser's `VideoDecoder` | `copyTo()` against the truth: **0 out of place** over 300 frames, worst **2.9** levels |
| the canvas **read back** | `getImageData()` after the `drawImage`, **same canvas and same instants**: **0 out of 180 000** superblocks |
| ⛔⛔ the canvas **PAINTED on the screen** | **photographed with the phone: the rectangles are there** |

⇒ ⭐⭐ **The pixels enter the canvas correct and break when the canvas goes to the screen.** No
program can read them there: `getImageData` reads the canvas's **store**, not what the
compositor has **lit**. It is the worst form of blind spot, because every bench that re-reads the
canvas is green **by construction**.

⛔ **And it is not the browser**: Firefox **and** Chrome do the same. ⛔ **And it is not the GPU in general**:
`ffplay` and YouTube — which paint into a **`<video>`** — are **clean** on the same machine and
at the same moment. ⇒ It is the route of the **2D `<canvas>`**.

#### ⭐⭐ The cure, measured before being believed

Painting with **`createImageBitmap()` + `transferFromImageBitmap()`** on a
**`bitmaprenderer`** context, which does not have the 2D store. **The user's judgement on the same
scene**: *«NIENTE ARTEFATTI!»*

⚠ **What it entails in the product**, and it is not one line: today the frame passes through **two** 2D canvases
(`deposito_p.drawImage(f)` and then `componi()` → `pennello.drawImage(deposito)`). ⭐ The **cursor is not
painted on the canvas** — it is a CSS cursor — so the visible canvas need not compose anything and
`bitmaprenderer` is enough for it. ⚠ The **centring inside the buffer** is lost, which is redone with CSS, and
**the cost must be measured**: `createImageBitmap` is asynchronous, and delay is the number for which phase 3
exists.

#### ⚙ The three tools born in this hunt, and they stay

| | |
|---|---|
| ⭐ **the snapshot on command** (`src/figlio.c`, `SIGUSR1`/`SIGUSR2`) | the child asks for a **key** and puts on disk, from the same instant, `scatto-ingresso.bgrx` (the pixels the encoder has in hand), `scatto-flusso.obu` (the bytes sent) and `scatto-uscita.bgrx`. ⛔ It is not a product switch: it writes only with `--rilievo`. ⚠ The signal arrives at the **parent** and must be **forwarded**, because `systemctl kill --kill-whom=main` delivers only to it — and `--kill-whom=all` would say «die» to `gnome-shell` |
| ⭐ **`banchi/07-b48-tela-contro-verita.html`** | manufactures a synthetic truth, encodes it with `ffmpeg`, gives it back to the browser's `VideoDecoder` and compares **`copyTo` against the truth** *and* **`getImageData` against the truth**. ⛔ **It does not have a line of REMOTIX inside**, and that is why its green is worth something |
| ⭐ **`banchi/07-b49-occhi-sulla-tela.py`** | it does not measure: it keeps the scene in view with **one** variable changed (`gfx.webrender.software`) and has **the user look at it**. It is the only tool that sees where `getImageData` is blind |

⛔ **And the bench certified itself before being believed** (`PIANO.md` §0.3.4): with the faults
**injected** — `certifica AV1` and `certifica H264` — it says *«è la decodifica: la tela ha ricevuto
pixel già rotti e li ha dipinti fedelmente»*, that is it **can see the fault it is looking for**.

#### ⚠ And a measurement that had nothing to do with the hunt, but must be kept

`[M]` With H.264 in **hardware** on this machine the decoder converts colour with a
different scale from `ffmpeg`: **5 000 superblocks «out of place» over 126 frames**, worst **30.3**
levels — ⚠ but **smooth and uniform**, **+8 levels on the light areas**: it is *not* a block
fault. ⇒ It is not the suspect of this hunt, but **it is a wrong colour for the user**, and it must be
taken up again when H.264 enters the product (`DECISIONI.md` §1.13-ter).

---

#### ⭐⭐ 4.9-bis · THE CURE IS IN THE PRODUCT — 20 Aug 2026, and it awaits the judgement

`src/pagina.html`: the visible canvas takes the **`bitmaprenderer`** context and the frame reaches it
with **a single** conversion (`createImageBitmap`) instead of the **two `drawImage`** of before.
⛔ **Both 2D canvases disappear**: the store's one — `[M]` **34.03 ms** median per
frame, the cost that phase 4 had measured — and the view's one.

| what changes | and why it breaks nothing |
|---|---|
| **the store is gone** | `transferFromImageBitmap` sizes the canvas by itself, and nobody rewrites `width` ⇒ when the window is resized the frame **stays**. The reason the store existed (§5.1, the black during a gap) falls by itself |
| **the frame border is redone only at the new size** | it is CSS, and doing it at every frame would be the stylesheet reflow that `adatta_vista()` avoids on purpose |
| ⛔ **`createImageBitmap` is asynchronous** | ⇒ every frame carries a **sequence number** and an **epoch**: whoever arrives after a newer one is thrown away and **counted** (`tardive`), and whoever arrives from a dead session does not paint over the live one |
| ⛔ **and the fallback is declared** | without `bitmaprenderer` or `createImageBitmap` it goes back to the 2D canvas **and the line says so**. ⭐ And `?tela=2d` turns on the old route on request: it serves to **compare**, and it is the only way to redo that comparison on the day the symptom came back |

**`[M]` Today's measurement, with the Marionette witness on the real Firefox** (port 7730, canvas
1588×914, session `prova`): `dipinti == consegnati` (11→11, 12→12) · `salt 0` · `buchi 0` ·
`ord 0` · `mis 0` · ⭐ **`tard 0`** · `err 0` · canvas pulled down as PNG, **sharp at 1:1**.
⭐ **And the check of the two routes, a single variable**: on `/` the canvas answers
`getContext("2d") → null` (that is the 2D store **is not there**) and the log line declares
`bitmaprenderer`; on `/?tela=2d` it answers `2d`, `ricomposizioni 1`, and paints as before.
⛔ **And a bench was corrected because its reading no longer exists**: `02-giudizio-catena.py`
read the pixels with `t.getContext("2d")` **on the product's canvas** — now it copies into a canvas
of its own. ⚠ What it reads back is still the store, not the screen (§1.16).

⛔⛔ **And the number that is still NOT there**: `[?]` **how much `createImageBitmap` costs**. The figure to
beat is that of the `drawImage` it replaced (34.03 ms), and until it is measured **no gain
is declared**. ⚠ A moving scene is needed, that is the phase 3 apparatus.

⏳ **And the judgement is missing, which is the only thing that closes this hunt**: no bench sees this
fault (§1.16), so 4.9 stays open until the user looks at **the product** — not the
bench — on his scene.

---

#### ⛔⛔ 4.9-ter · AND THE CURE BROKE CHROME — 20 Aug 2026, two symptoms and a single cause

*⭐ The cure of §5.4 had been measured **on Firefox only**. The user opened it on Chrome, and
within ten minutes two faults came out that seemed to belong to two different families.*

**The cause, `[M]` in twelve lines of isolated bench:**

| | |
|---|---|
| the specification | `transferFromImageBitmap` brings the canvas to the size of the image |
| **Firefox** | ⭐ it does: canvas 16×16 → **1588×914** (Marionette witness) |
| ⛔ **Chrome** | **NO**: `prima=[16,16] dopo=[16,16]` with a 2544×926 image |

**And the two symptoms, both its own:**

1. the image ended up **shrunk into a 16×16 buffer** and stretched by CSS ⇒ *«non si vede più
   bene, mancano gli elementi della shell»*;
2. ⛔ **input died**: `cl_geometria()` computes `vx = width on the glass / tela.width`, that is
   **~124 instead of ~0.8** ⇒ every click ended at a point between 0 and 16, in the top-left
   corner. The server's log said it literally: `PUNTATORE (5,5) · (4,5) · (3,5)`.
   The user: *«se clicco il quadrato del dash non compare il drawer»*.

⭐ **The cure**: the size **is written**, before the transfer, and the **real** one is looked at
(`this.tela.width`) instead of trusting. ⇒ The line corrects itself on any engine, without
asking anyone who they are — `CODER.md` §3.9, *one asks by name and verifies that it was given*,
applied to the **output**.

⛔ **The line to take away**: **a single engine is not a proof, it is half a proof.** And that is why
from today there is `banchi/07-b51-due-browser.py`, which does the two rounds by itself.

#### ⛔⛔⭐ 4.9-quater · THE DESKTOP WITHOUT A SHELL — and it was neither ours nor the page's

*Then the shell disappeared on Firefox too, with **all counters green**: `dipinti == consegnati`,
zero gaps, zero errors, zero late. The page painted faithfully what reached it — and what
reached it was **only the background**.*

`[M]` Mutter, queried with `GetCurrentState`, said the thing that no log said:

| monitor | size | position | primary |
|---|---|---|---|
| `Meta-1` | 2544×926 | (0,0) | ⭐ **yes** — here GNOME keeps bar and dock |
| `Meta-0` | 2532×840 | (2544,0) | ⛔ no — **and it is the one we were capturing** |

⇒ ⛔ **Two children of two servers of ours on the same session of `prova`** — ports 7700 and 7730 —
each with its own virtual monitor. On GNOME **bar and dock are only on the primary**: the secondary
carries the background and that is all. It is the «two servers of ours on the same session» fault of phase 4,
come back to bite, ⚠ **and this time disguised as a fault of the cure just put in**.

⭐⭐ **And now the product SAYS it** — `src/mutter.c`, `mutter_monitor_cerca()`: if a monitor
was already there, a line comes out that names the symptom *and* the cure (*«l'utente vedrà solo lo sfondo, con
tutti i contatori verdi… quasi sempre è un altro server nostro sulla stessa sessione»*).
⛔ **And the guard was tested, not believed**: the fault was redone on purpose with a second server
on 7740, `[M]` the line came out — *«C'ERANO GIÀ 1 monitor su questa sessione (Meta-0)»*.

⚠ **It does not fail**: a monitor that was already there can be legitimate (a real screen). It is declared.

#### ⭐⭐ 4.9-quinquies · THE BENCH THAT DOES THE TWO ROUNDS BY ITSELF — `banchi/07-b51-due-browser.py`

*Born from a sentence of the user: «non voglio fare più test: hai il controllo del PC, sistema tutto e
fai le prove su chrome e firefox».*

For each browser — Firefox with the **Marionette** protocol, Chrome with the **debugging
(CDP)** protocol — four different questions: the canvas **size** (`t.width` must equal the canvas in
force: it is Chrome's fault), the **counters**, the **input** *read from the receiving end* (a known point
is clicked and one reads in the **server's** log where it arrived), and the **image** as PNG.

⭐ **And it has two targets, not one**: the corner *and* the centre. With the corner alone, a conversion that
collapsed everything into the corner — that is the real fault — would give **green**.

⛔⛔ **And its first draft was wrong, which is worth writing down**: it compared the input's **sequence
number**, which **restarts from 1 at every session** ⇒ it said *«no new input»* while
the server's log carried the click **arrived correctly**. A bench red pinned on a
healthy product — `LEZIONI.md` §1.2. Now it compares the **new lines**.

⚠ **And it waits for the stage to be free between one browser and the other**: `[M]` a killed browser does not close
the session, QUIC's idle timeout closes it — **over 20 seconds** — and the second round found the
stage busy, accusing the page of a fault of the bench.

**`[M]` The outcome, 20 Aug 2026, port 7730:**

| | firefox | chrome |
|---|---|---|
| canvas size | ⭐ buffer = canvas | ⭐ buffer = canvas (1584×856) |
| counters | ⭐ `dipinti == consegnati`, zero late/errors | ⭐ same |
| click at (40,12) | ⭐ arrived at **(40,12)** | ⭐ **(40,12)** |
| click in the centre | ⭐ arrived at **(794,457)**, gap **0** | ⭐ **(792,428)**, gap **0** |
| image | ⭐ whole desktop, bar included | ⭐ same |

⚠ **And what this bench does NOT say**: it runs **headless**, that is **without a GPU** ⇒ the negotiated codec
may not be that of the real session. **It does not see the artefacts of §4.9 and does not look for them**: their
tool remains the user's eye.

---

#### ⭐⭐⭐ 4.9-sexies · THE REAL SUSPECT WAS FIREFOX'S AV1 DECODER — 20 Aug 2026

*⛔ And §4.9 was half right: the 2D canvas **was** a fault, and curing it cleaned up Chrome. But
on Firefox the blocks remained, and their cause was another. **They were two overlapping faults**, and
that is why every single hypothesis seemed refuted.*

**The bench that separated them** (`banchi/07-b52`, driven by me, not by the user): the
scene is moved — the GNOME overview opening and closing twenty times — and **three images
of the same instant** are taken.

| link | how it is looked at | outcome |
|---|---|---|
| the **capture** | `SIGUSR1` → `scatto-ingresso.bgrx`, the pixels the encoder has in hand | ⭐ **clean**: overview, dock, sharp text |
| the **sent stream** | `scatto-flusso.obu` given back to `ffmpeg/dav1d` — **22 deltas of the same chain** | ⭐ **clean** |
| **Chrome**, same bytes | 32 frames, moving scene | ⭐ **clean** |
| ⛔ **Firefox**, same bytes | 31 frames, `dipinti == consegnati`, zero gaps, zero errors | ⛔ **rectangular blocks** |

⇒ ⭐ **A single variable separates the clean from the broken, and it is the decoder.** The bytes are good —
two independent decoders say so — and Firefox paints them wrong **without declaring
any error**: `err 0`, `buchi 0`, `ord 0`, `mis 0`.

⚠ **And before accusing it, our own thing was checked**: `ffprobe` on the stream gives `Main`,
`yuv420p`, `bt709`, `tv` — that is **8 bit**, exactly what the page had asked for
(`av01.0.13M.08`). The hypothesis «10 bit declared as 8» stays dead as on 17 Aug.

#### ⭐⭐ AND THE CURE WAS ALREADY DECIDED: H.264 — implemented the same day

*The user's decision of 17 Aug (§1.13-ter) was born for another reason — Firefox for
Android has neither HEVC nor AV1 — and turned out to be **also** the cure for this fault.*

**`[M]` The measurement, same scene and same bench, with H.264:** Firefox, **35 delivered = 35
painted**, zero late, zero gaps, zero errors — ⭐ **and no blocks**. The same image that
an hour earlier was in pieces.

**What was written** (the work that §1.13-ter declared «not yet done»):

| where | what |
|---|---|
| `RCP.md` §4.3, §6.2 | `h264` in the negotiable list, `3` in the number registry. ⛔ `2` stays AV1 **forever** |
| `rcp.h` | ⭐ `RCP_CODEC_VIDEO_MAX`, so that the highest number lives in **one place only** |
| `rcp.c` | `NOSTRO_CODEC` becomes `hevc,h264` — AV1 leaves the negotiation |
| `codificatore.c` | `h264_vaapi` in hardware (`[M]` **1.6 ms** per frame) and `libx264` as declared fallback; the **H.264 Annex-B** reader (the IDR is in the *five* low bits, not in the six of HEVC) and the **SPS** read up to the cropping, which is what allows telling the REAL depth and size |
| `figlio.c` | the third slot in **four** per-codec arrays, and the number → codec map in a single function |
| `pagina.html` | the `h264-8` probe and the scale of sizes, **generated** by the two programs of `banchi/` and not written by hand; `avc1.6400<level in hexadecimal>`; and the sentences to the user that named AV1 |

⛔⛔ **And the three faults it uncovered on the way in, all of the same family — «a new number in
five places, and one stays behind»:**

1. ⛔⛔ **four per-codec arrays were 3 long** (indices 0-2): codec **3** wrote **out of
   bounds** and dirtied the variable next to it. The symptom was a line saying *«§4.3: il padre ha
   negoziato 8 bit (prima **1**)»* at every key request — **a memory fault disguised
   as a negotiation fault**, with zero frames and no line naming the cause;
2. ⛔ **the child rejected codec 3** with a hand-written ceiling (*«che §6.2 non definisce»*) —
   and at least this one *said so*;
3. ⛔⛔ **`wt_video_diffondi()` threw away every H.264 frame SILENTLY**: the child encoded
   (5 940 bytes, KEY, 1.6 ms), the parent received, and there the frame vanished **without a line**.
   ⇒ Now the ceiling comes from `RCP_CODEC_VIDEO_MAX` and the rejection **is declared** (one line per
   number, not per frame).

---

## 5 · ⛔ What did NOT work

*It is filled in even when it looks bad. ⭐ And in this phase the most instructive part is not
the product's faults: it is the **benches that were green without looking**.*

### 5.1 · The two adversarial briefs that were REFUTED by the measurement

| the sentence to refute | outcome |
|---|---|
| *«the reattach re-hooks the devices and everything works»* (6.1) | ⭐ **holds** on normal input: the application opened before the detach receives **everything**, with exact coordinates. ⛔ It is false **only** for the *held down* state — and that is where the fault lay |
| *«the chain `figli_ritela()` → `cattura_ridimensiona()` holds»* (6.3) | ⛔ **FALSE**: with two `ADATTA_TELA` 25-35 ms apart — *«whoever drags a border sends exactly two in a row»*, and the code itself calls it «THE case» — **4 rounds out of 18** (then 2/18) leave the desktop **not fitted**, and the client waits for the **3 s** backstop to receive `NON_ORA`. ⚠ On the other hand *«the discarded frames are zero»* **holds**: 0 in all rounds |
| *«since the canvas is the window, zoom no longer falsifies anything»* (6.5) | ⭐ **true** — ⛔ but in the wrong place: what broke sharpness was the **rounding**, not the zoom |
| *«the product violates §7.1 in at least one canvas case»* (6.6) | **not confirmed** on the five cases exercised against the product |

### 5.2 · ⛔ The benches that were green without looking — six, and nobody had noticed

1. ⛔⛔ **`04-b31-certifica.sh`, fault G8**: the anchor had **expired** since 16 Aug (a new function
   had come between the two it named) ⇒ **the most serious of the twelve faults was no longer
   grafted**. The certifier declared it with `??`, and nobody ran it;
2. ⛔⛔ **`01-b3` and `01-b4` spoke different formats** since 12 Aug (`RCPREG 0x00 0x01` against
   `0x02`): **every** trace of the client came out «broken recording» and five checks failed.
   ⭐ *Neither of the two files was broken on its own: the fault lay between the two*;
3. ⛔ **the validator closed healthy sessions**: the grace of §6.2 was written, imported and
   **unreachable**, because nobody told the frame judge that an `ADATTA_TELA` was in
   flight;
4. ⛔ **`06-b34`, positive control B**: breaking the release, the count becomes `0` **but the
   character arrives anyway** ⇒ `[M]` **Mutter releases by itself the keys on a device it
   destroys**, and the compositor was covering the fault for us. The verdict was **moved to another quantity**
   instead of being left green;
5. ⛔ **`06-b35`, fault G4**: declared **GREEN before the round**, because on Mutter «requested» and
   «granted» always coincide ⇒ that bench **does not cover** fault no. 5 of the ten of 15 Aug,
   and writes so;
6. ⛔ **`06-b33`, fault G1**: breaking *a single* mechanism of the swap changes nothing — the
   robustness is **redundant** (three re-reads of the region). ⭐ It became a **measured non-fault**,
   ⚠ with the declared limit: *no case protects the single mechanism*.

### 5.3 · The agents' worst showings, kept because they are the method

- ⛔ one round sent the input **on the control channel** and the server said farewell: a fault **of the
  bench**, and the log said so in one line (`CODER.md` §3.11 in action);
- ⛔ three rounds with an **empty witness**: the characters ended up in **GNOME's search box**
  because no window had focus, and an `Enter` launched Nautilus. Discovered
  **by photographing the desktop**, not by reasoning about it ⇒ hence the prelude and the **canaries**;
- ⛔ `umask 077` made the faulty binary `0700 root`: the child exited with **37**, and the bench was about
  to write five *«SMENTITO»* accusing the product **of its own permissions**;
- ⛔ a `grep` extracted **`1002`** — a uid — believing it was extracting a password: five
  `RESPINTO` and **the ban of §4.4-bis triggered by a fault of the bench**. ⚠ The colour did not
  say it: **the new denominator** said it (*«0 pairs closed»*);
- ⛔ a **pipe around `enter.sh`** ate the `sudo` prompt: ten minutes hung
  silently — it is trap **8** of §0-bis of this document, written and then trampled;
- ⛔ and two expected values **corrected on the measurement**, with the reason written beside them instead of widened to
  make them come out.

### 5.4 · ⛔ And a coordinator's mistake that risked misleading four benches

I sent four agents an alarm about `LEZIONI.md` §1.15 — *«su Xvfb `requestAnimationFrame` non
gira MAI, e in Blink il `resize` non arriva»* — ⛔ **and it did not reproduce**: `[M]` 16 Aug 2026,
probe `06-b37`, **184 frames in 3 s and 6 `resize` out of 6**, on both engines.
⚠ *§1.15 is not touched*: that measurement is from 13 Aug and is true for the scene it described. ⭐ But the
**guard** I demanded stays, and it paid off: `giudica_palco()` **stopped a round** in which the scene
was not producing what the bench believed (4 `resize` out of 6, by 1 px steps that do not change
the view in CSS pixels). ⇒ *A wrong alarm that leaves behind a right tool.*

---

### 5.5 · ⛔⛔⛔ THE ADVERSARIAL REVIEW OF THE SIX BENCHES — 21 Aug 2026, and **five out of six do not hold**

*It is the moment that `PIANO.md` §0.4 asked for and that this phase had never had: the reviewer **on the
bench**. The six agents had written their own bench and **certified themselves**. ⛔ Now someone who had not
written them read them — read only, no bench run — and the count is this.*

| bench | verdict | why |
|---|---|---|
| `06-b33` reattach | ⛔ **does not hold as certification** | the `tenuto` round — the only one carrying the real fault — **has no healthy reference line**, and its only fault certifies itself |
| `06-b34` keyboard | ⛔⛔ **does not hold** | 3 cases out of 7 cannot fail, 2 compute the verdict and throw it away, and the anchor of the main fault **was born expired** |
| `06-b35` stage | ⛔ **does not hold as certification** | the log marker is taken **before** `accendi` clears the log ⇒ the two counts coming from the log are **zero by construction** |
| `06-b36` canvas on the wire | ⚠ **the bench holds, the certifier does not** | ⭐ it is the best of the six: injected clock, truncated log, external expected values, 1000/1001 ms boundary. But the certifier exits **0** even if it grafts nothing, and 3 cases out of 23 have no fault |
| `06-b37` page | ⛔⛔ **does not hold** | ⛔ **the only one of the six without ANY grafted fault**, and four independent false greens |
| `06-b38` arbiter | ⚠ **the 49 and the 19 hold, the five live rounds do not** | ⭐ the offline half is the best built in the repository. `06-b38-tela.sh` is green **against a server that never answers** |

⭐ **And the justified refusal is worth as much as the accusations**: of **43 fault anchors** materially verified
on today's sources, **42 are alive with multiplicity exactly 1**. The case `04-b31` G8 — the expired
anchor — **did not repeat**, except once in `06-b34`.

#### ⛔ The four remarks that pull the floor away

1. **`06-b33`: the positive control is dead and declares success.** The certifier sends in `tenuto`
   mode **only** fault G3; the healthy round and the healed one run only in `comanda` mode. ⇒ R1
   today is red because with the key already released nothing is pressed any more — not because of the fault — and
   the script prints anyway *«⭐ G3 ha acceso il caso dichiarato»*;
2. **`06-b33`: a completely failed round certifies EVERY fault.** The comparison is a
   **membership** (`case " $R " in *" $CASO "*`), not a set equality: if the client does not
   survive the handshake, all cases go red, the set contains the declared one, and the
   fault comes out confirmed. ⚠ The judge **can** say *«IL BANCO, NON IL PRODOTTO»*, and that text
   **nobody reads**;
3. **`06-b35`: the log marker precedes the truncation by ONE LINE.** `registro-da` saves the
   length of the log, and the line after `accendi` does `: > "$LOG"`. ⇒ The region where the
   canvas lines are **is skipped systematically**: `tela_nuova_dal_palco == 0` is true **for free**
   (and it is the clause that *«distinguishes the stage did not obey from it was not asked»*), and
   `non_spediti > 0` is **unreachable** — that is precisely the wrong attribution the bench
   declares it has cured;
4. **`06-b34`: the anchor of fault B was born expired**, and the green branch of case 4b **is the signature of the
   missed scene**: if the swap really happens, the counter the bench demands `>= 1` is
   **always 0** ⇒ green is obtained **only if the scene did not happen**. ⚠ The cure and the fault that
   was to prove it entered **in the same commit**, and the fault was never re-run.

#### ⛔⛔ And `06-b37`, which is a case of its own: four false greens, each sufficient on its own

- **no scene has a LOWER limit on the canvas**: a canvas 30 px narrower than the window —
  permanent black band, 30 columns lost — leaves **12 combinations out of 12 green**;
- **the branch that implements «the item switched off» is never executed**: the spy replaces `chiedi_tela`
  **before** measuring, and the real guard is **inside** the replaced function ⇒ the bench proves that
  *a boolean changes value*;
- **the «real question» is an algebraic identity**: the bench reconstructs the input and compares it with
  the output of the function that produced that input — gap 0 in 93 lines out of 126, by
  construction;
- ⛔⛔ **the coordinates: the origin is cancelled by construction.** The offset between where the image
  is and where the page believes it is gets **subtracted** before the comparison. ⇒ The DeX fault —
  the canvas painted 50 px to the right of where `getBoundingClientRect()` declares it — **gives gap 0 on 20
  points on two engines**. It is exactly the fault that scene names as its own reason for being.

#### ⛔ This phase's measurements that FALL, and must be redone or rewritten

| statement | state |
|---|---|
| §2 · `06-b33` «5 faults: G2→C2 · G3→R1,R2 · G4→C6 · G5→C3,C4» | ⛔ **G3 is not certified**; the others remain conditional on remark 2 |
| §2 · `06-b35` «**5 faults out of 5 confirmed**» | ⛔ **to be redone** after the marker line is in its place |
| §2 · `06-b34` «6 cases · 2 faults» | ⛔ **almost all of it falls**: case 1 and case 6 hold. *«A keymap change destroys and recreates the device, and the key does not stay down»* **is not measured** |
| §2 · `06-b36` «**23** cases · 19 faults out of 19» | ⛔ to be rewritten as **«20 cases out of 23 certified by 19 faults»** |
| §2 · `06-b37` «7 scenes», «20 points · 2 523 columns · 4 resizes» | ⛔ **the scenes run are 6**; the 2 523 comes from a scene never run on the two engines; **the 20 points are zeros by construction** |
| §2 · `06-b38` «49 accused on the byte» | ⛔ **28 on the byte and on the rule, 49 on the outcome**. ⭐ «19 mutations out of 19» **holds** |
| §4.3-bis · «12 combinations out of 12 green» | ⛔ **not kept**: the outcomes in the repository precede by a day the bench code that would have produced them |
| §4.3 and §0 point 7 · «the three `[?]` of §6.1-bis, closed» | ⛔ **none of the three is closed**: zoom is acquitted by a 2 px tolerance while the worst gap measured is **exactly 2**; the odd side is made impossible by construction and never provoked; the half pixel is observed and increments no count |
| §0 point 4 · «the fallback on KWin declared in the log» | ⭐ **holds** (`06-b36` cases 1-2, anchor alive) |
| §0 point 5 · «the coordinates in flight in the second after `TELA(ADATTATA)`» | ⭐ **holds, and it is the most solid part of the six benches** |
| §2 · `06-b34` «the expected value is computed by the product» | ⛔ **it is not implemented**: `06-b34-tabella.c` is neither built nor run by any script. ⭐ But the accusation «the test certifies itself» **falls anyway**, because the real expected value is a **string of characters arbitrated by xkbcommon inside the session** |

#### ⭐⭐ And the reading that is worth more than the list

⚠ Of the twenty-two remarks, **only one** is an expired anchor — the form that §5.2 feared and that everyone
was looking for. **All the others have the same new form, and nobody had ever named it:**

> ⛔ **the measurement is good, and the judgement is detached from it.**

An exit status captured and not looked at (`b34`, `b35`, `b36`, `b38`), an expected value printed and never
compared (`b38`), a denominator printed and never read (`b38`), a counter printed with `inf`
instead of with `ko` (`b34`), a membership `case` instead of an equality one (`b33`).

⇒ **The hunt next time is not for anchors: it is for every number a bench prints and does not
compare.** 📖 `LEZIONI.md` §1.20.

### 5.6 · ⛔⭐ 21 Aug 2026 — **the log lied under load**, and it took a dead tool and a bench round to discover it

*Born from the repair of the two tools of `06-b35` asked for by §7.1. ⭐ The declared symptom was
«`06-b35-lancia.sh tempi` dies with `ValueError`». The cause was not in the tool.*

#### ⛔ The PRODUCT fault: three `write()` per line, and parent and child write to the same file

`src/registro.c` composed every line with **three distinct calls** on an unbuffered `stderr`
— header, body, newline. ⚠ The parent and the child append to the **same** log: when the
writes overlap, a body ends up after someone else's newline and **a line without a
timestamp** is born.

`[M]` on a real 3.0 MB log (28 035 lines): **23 orphan lines**, of which **3 out of 80** of the
«tela CHIESTA al produttore» — **3.8 %** of a family of lines a tool was counting on.

⭐ **And the positive control of the cure, `[M]` on 21 Aug**: six processes appending to the same
log, 800 lines each.

| | lines | orphans | «tela CHIESTA» found out of 4 800 |
|---|---|---|---|
| ⛔ before | 4 800 | **2 464** | **2 789** — that is **42 % of the count was lost** |
| ⭐ after | 4 800 | **0** | **4 800** |

⇒ **The cure**: the line is composed in a buffer and written with **a single `write(2)`**. Under
`PIPE_BUF` (4096 bytes) a `write` on a file in append mode is atomic with respect to the others; whatever exceeds the
buffer is **truncated with a mark**, because *a cut line can be seen, an interleaved line cannot*.
⭐ In addition `write(2)` is async-signal-safe, which `fprintf` is not, and the `fflush` is no longer needed.

⛔⛔ **And the lesson is not about the log**: it is that **this project's main diagnostic tool
broke precisely under load** — that is exactly in the scene in which it is questioned.
📖 `LEZIONI.md` §1.21.

#### ⛔ An eighth fault of the bench, and this one did worse than break

`accendi` does `: > "$LOG"` and **does not reset the mark** from which the tools count. `[M]` a
mark of **825 758 bytes** was found on a log of **45 373**. ⚠ It did not give «systematic zero» — it gave **an
arbitrary window**, which is worse: a plausible and false count. The only surviving outcome declares
`tela_nuova_dal_palco = 258` for a round that changes canvas **9** times.

#### ⛔ The **D** numbers of §4.8 cannot be recomputed — the window is lost

⚠ It must be written instead of worked around: **4 ms · 39.5 · 44.5 · n=10** came from a log
window that **was deleted**, and no surviving file contains it. ⇒ What can be obtained today
from the logs that remain, **with the machine idle**, with the repaired tools:

| | `[M]` 21 Aug, from the repaired tools |
|---|---|
| **the canvas passed to the stage** | **4.0 ms** (0-18, n=30) |
| Mutter | **35.0 ms** (29-45, n=20) |
| full round server side, `ADATTATA` | **43.5 ms** (38-57, n=20) — against the 44.5 written: **a nearby window, not the same one** |
| `NON_ORA` | **6.0 ms** (5-7, n=10) — ⛔ and before it was under the same label as `ADATTATA`, which is form E2 |

⭐ **And one number of the document comes back exact**: §4.2, *«4 ms median over 9 changes (3-13)»*, comes out
identical from the new tools on the same log. ⇒ Not everything is to be redone: it is **that** box.

#### ⭐⭐ And a NEW clue, in favour of the contention thesis

`[M]` on the log of **16 Aug**, with five benches running: `NON_ORA` has a median of **22 ms** and
**two cases at 3 000 ms** — the whole deadline of §7.1. On the **17th**, with the machine idle: **6 ms**, and
none reaches the backstop. ⇒ ⭐ **Contention really moves this scene**, and the *«green holds under
CPU load, not under GPU contention»* of §7.1 now has a second support even before the contention
scene is launched.

#### ⭐ And how the repaired tools were certified

The hand calculation **rewritten in `awk`** — another language, another algorithm — and compared
**sample by sample** on three real logs: **235 samples, all five measurements coincide
exactly**. ⚠ There was one divergence, and it was **the `awk` that was wrong**: it consumed one answer
beyond the ceiling. ⭐ The positive control of `06-b35-tempi.py` also verifies that **the old
tool, on the same input, dies or gets it wrong** — otherwise it would check nothing.

⏳ **And the «5 faults out of 5» of §2 stays suspended**: the five remarks of the review on the certifier
are closed (the healthy round as yardstick, the mark after start-up, the exit status of
`costruisci.sh`, the tool that declares «blind» instead of saying zero), ⛔ but **the round has not yet
been redone**. The contention scene (`06-b39-*`) is **ready and not launched**: it waits for the window,
because it would shift the milliseconds of all the other benches running.

### 5.7 · ⭐⭐ 21 Aug 2026 — **the second door of the dying click, measured**, and the cure that CANNOT be done

*New bench `banchi/06-b33-risveglio.*`: it links `cattura.c` and `input.c` of the **product** and calls them
from the command line, with the Wayland witness inside the session of `provai6`. Canvas 1264×800,
`MUTTER_DEBUG=eis,input`.*

| scene | `[M]` | load |
|---|---|---|
| **S0** zero control, click without swaps | the witness sees it: down and up | 5.67 |
| **S1** three `cattura_risveglia()`, hand lifted | ⭐ **3 wake-ups → 3 swaps** (delta `[1,1,1]`) with **0** `cattura_ridimensiona()` ⇒ **§7.1 is true** | 1.86-2.19 |
| **S2** `BTN_LEFT` down, **one** wake-up | ⛔ the release **never arrives**, and **neither does the next fresh click** ⇒ desktop dead to clicks. ⭐ The **keyboard** keeps working | 1.58→10.68 |
| **S3** the same scene with `cattura_ridimensiona()` | **identical outcome**: they are two doors into the same room | 3.76 |
| **S4** it breaks, then the EIS client is detached | ⭐ **the clicks come back**, with the **same `gnome-shell`** (pid verified before and after) | 1.39 |

#### ⭐ The `[R]` chain of §7.1-bis becomes `[M]` — and it was nearly refuted wrongly

From Mutter's journal, to the millisecond: `EIS: Updating viewports` **without** any «Releasing
pressed buttons» beside it; then `Dropping repeated press of button 0x110, count 2` and
`Dropping repeated release of button 0x110, count 1`. The release of the held button **does not appear
at all**: `handle_button` swallows it before the seat sees it.

⚠⭐ **And the clarification is worth as much as the measurement**: the line «Releasing pressed buttons» **is there**, six
times — but **at detach**. ⛔ A search for absence over the whole journal would have **refuted §7.1-bis
wrongly**. The reading holds in the precise form: absent *beside `Updating viewports`*, present
at disconnect.

#### ⛔ And the hypothesis «the cure is smaller than it seems» is REFUTED

*(It was the coordinator's: `button_count[]` belongs to the **seat**, not to the device, so a release from
a new device could bring the count down.)* ⛔ **No**: `handle_button`
(`meta-eis-client.c:612-621`) looks at `device->button_state`, which **on the new device is clean**,
and a release from there never reaches `meta_seat_impl_notify_button_in_impl`. The invariant is
`count = Σ live bits + leaked`, and delivering a release needs `count == 1` with a live bit,
which has already incremented ⇒ **unrecoverable**. The only route remains `drop_device()`.

#### The four forms of the cure, with the price — and the choice

| | where | price |
|---|---|---|
| **A · prevention**: no wake-up with something pressed | guard in `figlio.c` + a window in `input.c/.h` | ⭐ **no broken drag**. ⚠ On a still desktop with a key down the key frame does not start ⇒ **a just-attached client may stay white until release**. It heals by itself, and the scene is rare: a drag *moves* the scene |
| **B · release before the wake-up** | one line in `figlio.c` | ⛔ **cuts EVERY drag on a still desktop** — it is the «forbidden obvious cure» of §7.1. Cited only for comparison |
| **C · recovery**: the EIS channel is reattached when the damage is there | `input.c` (already sees `quanti_orfani > 0`) + `mutter_eis_riattacca()` in `mutter.c` | `[M]` it works (S4). ⚠ It cuts the drag in progress — **which however was already dead**. ⭐ It covers **the doors we do not control**: `monitors-changed` (two rounds), the keymap change, and whatever Mutter will add |
| **D · the wake-up is removed**: the key frame is redone from the last frame | `figlio.c` + `codificatore.c` | removes the door at the root, ⛔ but **does not replace** the wake-up: at login there is no frame to redo, and the 4.4 seconds come back. And it costs ~9.8 MB of copy at 2560×962 |

> ### 🔸 **Coordinator's choice: A + C** — derived, not decided by the user
>
> **A alone is not enough**, and the reason is in §7.1-bis: the doors are not one. `cattura_risveglia()`
> is the one we control; `monitors-changed` does **two rounds** of it, the keymap change is another, and
> the function that opens them all came in with **Mutter 48.5** — that is, it is **new**, and more will come.
> ⇒ A cure that covers only our own front door **expires at the next GNOME update**.
> ⚠ And the price of **C** is not a price: the drag it cuts **was already dead** (S2).
> ⏳ **The price of A, on the other hand, is visible to the user** — the white window until release — and
> visible prices are his to judge: the line is here so he sees it, not because it is already decided.

⛔ **And a constraint found by measuring, which changes the estimate for C**: `input_apri()` **reuses the
descriptor** that `mutter.c` keeps aside, and as long as that stays open Mutter sees no
detach and `drop_device()` does not run. ⇒ **The cure does not live inside `input.c`.** `[R]`
`meta-remote-desktop-session.c:1943-1969`: `session->eis` is reused and every `ConnectToEIS` adds a
client, so session and stage are not touched.

#### ⛔ A new fact that touches the certification of `06-b33`

With the cure in `figlio.c` · `codificatore_di()`, `segna_orfani()` **does not run even in the healthy product** ⇒ **G3 is
no longer certifiable in `06-b33`**: its scene now lives in `06-b33-risveglio.sh tenuto` (case T1).
⏳ That bench **does not yet have a certification with a grafted fault**, and it is the biggest hole of
this delivery — declared by the author first.

#### ⭐ And the five remarks of the review on `06-b33`: closed

The world is **read** from the log; R1/R2 are demanded **only with the fault alive**; **new T4** — the
fresh click, which is the real damage and **nobody measured**; R1 looks for the marker **of the
buttons**; C6 counts **in the resize window** (before, `rp >= 1` was satisfied by the
wake-ups); healthy and healed round **in both modes**; **set equality** instead of
membership; the judge's outcome propagated. ⭐ With the new certifier, **G3 lights up zero cases** — and
the old one would have printed *«⭐ G3 ha acceso R1»*.

⛔ **And five faults of the new bench, declared by the author**, the most serious of which: the release of the
held button and that of the fresh click **cannot be told apart** by position relative to the `RITELA` —
the order in which Wayland delivers `configure` and `button` is **a race**. The right boundary is the
**fresh press**. Before the correction, T4 came out yellow on a healthy round.

### 5.8 · ⭐⭐ 21 Aug 2026, night — **GPU contention measured, and the verdict REFUSED by the bench itself**

*The scene that §7.1 had been asking for for days, run in a dedicated window with all the other benches
stopped. `[M]` Source fingerprints in the report; iron: **integrated Intel UHD 730**.*

#### The scene is real — certified before measuring

`[M]` One encoder alone does **382 frames/s** at 1920×1080; **five together, 184 each**
⇒ contention on the iGPU **is there**, and it is **2.08×**.

#### ⛔ But the product did not notice, and the bench **refused to give the verdict**

`[M]` 18 rounds under contention (load **2.57**) against 18 at rest (**0.41**), in the same hour:

| | under contention | at rest |
|---|---|---|
| **broken** | **0 out of 18** | **0 out of 18** |
| frame rate | 51.2 ms | 55.3 ms |
| ① passed→requested | 4.0 ms | 5.5 ms |
| ② **Mutter** | 28.0 (22-48), ⛔ **13 beyond the ceiling** | 32.0 (18-47), ⛔ **17 beyond the ceiling** |
| ③ stage→sent | 4.0 | 4.0 |
| ④ `ADATTATA` | 37.0 | 40.0 |

⇒ **Nothing moved**: every latency is equal or **faster** under contention. The witness (which
demands a dilation ≥ 15 % of the rate seen by the client) **did not trigger**, and
`06-b41-verdetto.py` **refused the verdict**. ⭐ *«Non scrivo "0/18 sotto contesa GPU": sarebbe
l'etichetta senza la cosa»* — and that is exactly why that witness was written.

⭐ **And it is known why**: at rest the rate is 55 ms ≈ **18 frames/s**, and it is dictated by **the scene** (a
terminal that writes the time every 50 ms), not by the encoder. At 18/s of 1280×800 the product asks
the iGPU for about **one fiftieth** of what the five loads ask for. ⇒ **The contention is real
on the iGPU, but in this scene the product hardly uses the iGPU.**

#### ⛔ What changes for §7.1: **one cause is EXCLUDED by measurement**

The **4/18 of 16 Aug** remains **not reproduced**, ⛔ and now it is known that **it is not contention
on the iGPU alone**. It is not promoted to «cured», and it is not promoted to «explained».

⭐ **And where the signal is there, it points to another suspect**: latency ② has **13 and 17 samples beyond the
ceiling** out of ~57 in **both** halves — that is a quarter of the requests to the producer **without
an answer from Mutter within one second**. It is the same signature as 16 Aug (`NON_ORA` median 22 ms and two
cases at 3 000). ⇒ ⏳ **The next hypothesis is contention on the COMPOSITOR and on PipeWire — five
sessions — not on the iGPU.** That scene has not been built.

#### ⛔ And with the healthy yardstick, the «5 faults out of 5» does not hold

`[M]` Certifier redone under contention, load 2.78, with the **healthy round as yardstick** and the mark after
start-up:

```
SANO   adattate=10 non_ora=0 ms_mediano=47,45 fotogrammi=169 tela_nuova=10 non_spediti=0
G1 · G2 · G5   ATTESO-CONFERMATO      (regola sul sano = False)
G3  ⛔ ATTESO-SMENTITO      tela_nuova_dal_palco = 1, e la regola ne pretende 0
G4  ⛔ NON-DISCRIMINANTE    la regola è vera ANCHE sul sano
⇒ CONFERMATI 3 · SMENTITI 1 · NON DISCRIMINANTI 1
```

- **G3** is the predicted fault: the third clause was true **for free** because the expired mark
  made the log window empty. ✅ **Closed on 22 Aug, and there was only one route**: see
  §5.9;
- **G4**: §5.2 already said it in words («expected green by construction»); ⭐ now **the bench says it**,
  instead of counting it among the confirmed;
- ⭐ **and G1 still discriminates** with the load on (`regola sul sano = False`), which was the coordinator's
  doubt. ⚠ With the declared limit: **this** contention does not reach the product.

#### ⭐ And the remedy to `registro.c` is verified by a third party

`[M]` on the round under contention: **18 lines without a mark out of 12 882**, and **all 18 are from `libopus`**,
that is from ffmpeg — **zero lines of ours broken**. Against **23 out of 28 035** (of which 3 became events)
on the log of the 16th with the old code.

⛔ **And it unmasked a fault of the counting tool**: it called that number *«header lost
in the interleaving»* — a **cause**, on a tool that sees only an **effect**. ⇒ It would have accused
`registro.c` of an interleaving that no longer exists: **the red on the wrong suspect, inside the tool
that should unmask it.** Now it separates «lines without a mark» from «**events** that come of them», which is
the only number that moves a latency.

#### ⛔ And the window's worst fault is the author's, who declared it first

`misura` copied the JSON files **of 16 Aug** as if they were the round just done: six rounds born from
**three files five days old**, with a perfectly plausible rate inside. ⭐ It was seen
**only** because the two halves were identical **byte for byte**. ⇒ Cured: first delete, then
collect only what is **newer than a mark taken an instant before**, and **zero rounds collected
= stop**.

### 5.9 · ⭐⭐ 22 Aug 2026 — **G3 closed, and the «non-recomputable» numbers redone from scratch**

#### ⛔ G3's third clause was not off by one: **it was unreachable by a round that measures**

`tela_nuova_dal_palco == 0` could become true **only if the tool had not looked** — a
round without frames is not measured at all (it exits 5), and a round with at least one frame
**always** has the birth line. ⇒ ⛔ **It was the false-green machine written inside the expected value**, and
it had been there **since the bench's first day**: the expired-mark fault (§5.6) did not create it, it
**realised** it.

`[M]` The line «TELA NUOVA DAL PALCO» of G3's round is the **birth reconciliation**, and it **precedes**
the first `ADATTA_TELA` — reproduced twice, eight hours apart and at different loads: **476 ms before** on
21 Aug (load 2.78), **461 ms before** on the 22nd (load ~0.7). The child is born at the fallback
1920×1080 and the stage is **born** — not resized — at 1280×800.

⭐ **And «completing the fault» is EXCLUDED with proof, not discarded by taste**: that line does not go through
`cattura_ridimensiona()`, so switching it off would mean a second fault under a single name (which
the grafter **forbids**), at the point that already belongs to G5, and it would take the scene away from G3. ⇒ **The two routes
did not lead to different work: one of the two did not exist.**

⭐⭐ **And the distinction the clause serves HOLDS**, which was the real question: without it G3 and G1
would have the **same** rule, and the positive control would say that the bench sees *a* problem
instead of *that* problem. `[M]` same hour: **G1 = 8** (the stage obeys, the answer gets lost) ·
**G3 = 1** (nothing reaches the stage) · **SANO = 10**.

⭐ **And the `== 1` falls on the right side**: a blind tool counts 0 ⇒ rule **false** ⇒ **red**.
The old `== 0` fell on the green side. ⇒ **Every way the new rule can fail is red**
— and it is the form that `LEZIONI.md` §1.20 asks for.

#### ⭐ The real number: **4 confirmed · 0 refuted · 1 non-discriminating**

`[M]` 22 Aug, load **0.49-1.12** (⚠ **the contention is no longer there**: last night's 2.78 was largely
the bench itself — it should be read as *«with the machine almost idle»*), product sources
**identical byte for byte** to the repository.

#### ⭐⭐ And the **D** numbers of §4.8, declared «non-recomputable», have been **REDONE**

⛔ Not reconstructed from the old files — *those are the trap the problem comes from* — but taken from
**three new rounds** on the healthy code, with the repaired tools and their positive control passed
first. Load 0.30-0.48.

| | §4.8 (17 Aug) | §5.6 (from the survivors) | ⭐ **new round, 22 Aug** |
|---|---|---|---|
| ① **the canvas passed to the stage** | 4 ms (n=10) | 4.0 (n=30) | **6.0 ms** (0-21, **n=27**) |
| ② Mutter | 39.5 ms | 35.0 (n=20) | **32.0 ms** (15-49, n=27) |
| ③ stage → sent | — | — | **4.0 ms** (3-39, n=28) |
| ④ full round, `ADATTATA` | 44.5 · 10/10 | 43.5 (n=20) | **42.0 ms** (25-59, n=27) · **27/27** |
| `SESSIONE` → 1st frame | 25 ms · 203-220 to be mounted | — | **14 and 26 ms** · **141 ms** to be mounted |
| discarded · wrong size | 0 · 0 | — | **0 · 0** (30/30 `ADATTATA`, 9/9 first at the new size = key) |

⇒ ⭐ **The three latencies of box D are all reconfirmed within a few milliseconds, with n almost
tripled.** The hole of §4.8 closes: that box is no longer a lost number.

⭐ **And the cure of `registro.c` holds here too**: 3 lines without a mark out of 3 242, **none of ours**.

#### ⛔ And on the evening of 22 Aug the number went down again: **3, not 4** — and it was lowered by whoever had written it

*Also closed the two remarks of the review (`R5` the sentinel, `R14` the tool that throws away counts),
and with the new column a fact came out that could not be seen before.*

⛔ **G5 is intermittent**: its rule wants `non_spediti > 0`, and that number is **1** — a single
frame discarded. In the third round it came out **0** with the tool **not** blind (67 canvas lines
seen) ⇒ `NON MISURATO`. ⚠ Before, it would have **vanished from all three columns without a line saying
so**: that is the reason the **fourth** column exists, and the reconciliation
`CONFERMATI + SMENTITI + ND + NON GIUDICATI = guasti chiesti`.

| | 05:44 | 06:16 | 06:21, scene verified **single** |
|---|---|---|---|
| G1 · G2 · G3 | confirmed | confirmed | **confirmed** |
| G4 | non-discriminating | non-discriminating | **non-discriminating** |
| G5 | confirmed | confirmed | ⛔ **NOT MEASURED** |
| ⇒ | 4 · 0 · 1 · 0 | 4 · 0 · 1 · 0 | **3 · 0 · 1 · 1** |

⭐ *«Non scrivo 4: sarebbe scegliere i due giri che mi piacciono.»*

> 🔸 **Coordinator's decision on G5: the round is lengthened, the expected value is NOT rewritten.** The expected value is not
> wrong — it is **the scene that is under-powered**: a scene that produces *exactly one* event
> proves nothing in a repeatable way. ⛔ Rewriting the expected value would be **fitting the yardstick to the
> result**, which is the road this night taught not to take.
>
> ### ⭐⭐ And lengthening the round it came out that **the event does not multiply**, and the why is worth more than the fault
>
> `[M]` Six rounds, from the short scene to one **five times longer**: **799 frames, all
> inadmissible, and a single announcement**. Five times the activity in the log, **the very same 1**.
>
> ⭐ **And it is known why, from the source**: the line sits behind a backstop that re-arms **only when
> the pair (canvas in force, frame size) changes** — and under that fault **it never changes**. First
> frame: the line comes out. From the second to the 799th: identical, backstop already armed, **silence**. ⇒ It is **once
> per session, by construction**.
>
> ⛔⛔ **So the number is not what its name promises**: `non_spediti` is not *«how many
> frames did not leave»*, it is *«how many distinct announcements of disagreement»*. The name says 799, the
> value is **1** — form **E2**, and ⚠ **nobody had seen it because 1 is a number that looks
> healthy**.
>
> ⛔ **And the product has the real count and does not say it**: `w->video_saltati` is incremented at every
> frame, and `wt_video_conti()` could read it — ⛔ but **nobody calls that function**
> (verified: zero callers in all of `src/`). ⇒ It is `LEZIONI.md` §1.20 **inside the product**: a
> counter nobody compares.
>
> 🔸 **Decision: the real count is brought out.** The other two routes were discarded with the
> reason: counting another line would give the right number in the good round ⛔ **and a false red** in the
> round where the stage does not start; leaving it as it is costs zero ⛔ and leaves around **a name that promises
> one thing and says another**.
>
> ### ✅ **DONE on 22 Aug — sixteen lines of code, and the factor is 254**
>
> `wt_video_conti()` finally has a caller, **next to the audio one**. ⭐ And the discovery that
> is worth more than the cure is in the comment that goes with it: the audio line was written on **17
> Aug** for the **twin** function, **with these very words**. ⇒ The cure had been applied to
> **one of the two twins**, and nobody had looked at the other. 📖 `LEZIONI.md` §1.25.
>
> `[M]` Same scene, two binaries, the fault grafted only in the build tree:
>
> | | delivered | **NOT SENT** | **ANNOUNCEMENTS** |
> |---|---|---|---|
> | healthy | 1 016 | **0** | **0** |
> | with the fault | 0 | **1 017** | **4** |
>
> ⇒ ⛔ **1 017 against 4: a factor of 254.** Before, the only readable number was the announcements' —
> and it was called «not sent».
>
> ⭐ **And the expected value written beforehand was wrong, and it stayed written**: it said «announcements = 1», as in the
> round that had opened the case. **4** came out, and that is right: the backstop re-arms at every new pair
> (canvas, size), and that scene changes it three times. ⇒ **The number of announcements follows the
> distinct sizes, not the frames** — which is exactly the reason it could not act as a count.
>
> ⚠ Declared and not done: «not sent» sums **three** causes. Splitting it would be a second cure —
> ⭐ but the name **does not lie**: they really are the frames that did not leave.

#### ⛔⛔ And the scene was doubling silently — **for the second time tonight, the same form**

`pkill -f 'banco-P6-scena'` kills **the terminal**, not the loop that writes the time: the title **is not
in the command line** of the surviving process. ⇒ Every `scena-via` left a loop alive and every
`scena` added one — `[M]` **two loops** after a single off/on. ⚠ On a bench that
measures milliseconds, **a doubled scene is not the declared scene**.

⭐ Cured with the right guard: `scena-via` demands **zero** survivors and `scena` demands
**exactly one** — the old guard was `> 0`, **which let two through**. And the D numbers
were on **one** loop: verified, not hoped.

⚠ **The same form was found independently in `06-b42`**: it is a way of going wrong of the
repository, not of a bench.

#### ⭐ And the D numbers **do not change** after the pairing cure

① now pairs **by key**; ④ stays by order, ⭐ **and it is a declared choice**: the key does not
exist (the answer line carries the canvas *in force*, which on a `NON_ORA` is the **old** one, and
pairing by size would throw away precisely the `NON_ORA`s the faults look for). ⇒ The protection is
upstream. `[M]` Recomputed on the same logs: **identical sample by sample**, and it is known **why**
— in that round `GIRATA 27 = CHIESTA 27`, zero unpaired, so key and order coincided.
⛔ **But it is a property of that scene, not of the old code**: the other two rounds do not have that
guarantee.

#### ⏳ And two things declared instead of cured

- ⚠ **the value «1» is tied to the scene, and nobody had said so**: it exists because the child is born at the
  fallback 1920×1080 while the round's session is 1280×800. A scene that opened **exactly** at
  1920×1080 would not have the birth line, and the expected value would not hold. ⇒ Now the expected value **names the
  round and the reason**, instead of carrying a bare number;
- ⚠ `parlantina-c-e` gives a **false red on the first round after an `accendi`**: it reads the whole log,
  which `accendi` clears. ⛔ False red, so a safe direction — **declared, not cured**.

### 5.10 · ⛔⛔⭐ 22 Aug — **the grace second against the product, and the arbiter alone does NOT see the leniency**

*Rounds 6 and 7 of `06-b38-tela.sh`, never pointed at the server. `[M]` port 7721, **four whole
rounds 7/7 green**, loads 1.16 · 1.51 · 1.57 · 2.58.*

| | round 6 — **beyond** | round 7 — **inside** |
|---|---|---|
| recorded `dt` | **1 501 ms** | **251 ms** |
| the server | `CONGEDO 0x0b ERRORE_PROTOCOLLO` | ⭐ the session **holds** |
| the arbiter | «beyond the second — and the server **said farewell**» | ⭐ «**NOT judgeable** from this recording» |
| ⭐ **where the pointer ended up** | **nowhere** | **(799,599)**, the last pixel of the new canvas |
| the wire | — | **`input = 1`** in the frame (§6.2) |

⭐ The coordinate **is not chosen by hand**: the last pixel of the *previous* canvas is sent, which **must**
saturate exactly at `(799,599)`.

#### ⭐ The clock asymmetry is no longer a reasoning: it is a table

> **9 pairs out of 9: the server measures more, between +11 and +25 ms** (LAN, load 1.0-1.6).

⇒ An «inside» case at 0.99 s would have been **1.01 s for the server**: red on a product that is
right. ⛔ The table is in the bench **with the prohibition of using it to get closer to the boundary**.

#### ⛔⛔ «The arbiter says conforming» is not a measurement

With a **server faulty on purpose** (`TELA_GRAZIA` 1 000 → **60 000 ms**): the pointer at 1 501 ms gets
**injected**, and ⛔⛔ **the validator exits 0 and declares CONFORMING** — honestly, because §7.1 lets it
conclude **only** if the server still speaks on the control channel, and **a lenient server that
keeps quiet does not give it the chance**. ⭐ The bench instead exits **1 with five red lines**, and the seventh
round against the same faulty server stays **green**, as it should: **specific, not paranoid**.

⇒ It is the strongest form of *«conforming is not working»* this phase has produced.

⛔ **And a fault of the bench of the worst kind**: it compared the pointer with the **last**
`TELA(ADATTATA)` of the file instead of with **the one preceding it** ⇒ **negative** `dt`, which falls below
the second, that is into the «not judgeable» branch. **A pointer beyond the grace would have been declared
inside.** The positive control found it.

### 5.11 · ⛔⛔⭐ 22 Aug — **the «Mutter signature» of §5.8 was an artefact of the scene**

*The follow-up of the contention: the five-session scene was built, ⛔ and the premise fell before the
window.*

`[M]` **18 chained rounds, ZERO contention**, load 1.57 → 2.91: latency ② gives **17 samples beyond the
ceiling out of 62**. ⛔ §5.8 had **13 and 17 out of ~57** and read them as *«a quarter of the requests without
an answer from Mutter within one second, the same signature as 16 Aug»*.

⭐ **The mechanism, and it closes the case**: ② pairs **by requested size**; the first of two chained
requests receives `NON_ORA` (§7.1), so **the producer never delivers a canvas at that
size**, and the request gets paired with that of a **later** round — beyond the second. **One
per round.** ⭐ Counter-proof over 5 rounds: **15 requests, exactly 5 unpaired and exactly 5
`NON_ORA`**. ⇒ And it is also why §5.8 found it **identical in the two halves**: it is what the
scene does **by construction**.

#### ⭐⭐ And the same 18 quiet rounds give **0 broken out of 18 — at a HIGHER load than 16 Aug**

Load **1.57-2.91** against the **0.90** that §4.8 records for the day of the 4/18. ⇒ «Quiet» is measured
**above** the load of the day that produced the fault, and **0/18** is obtained.

#### ⭐ And a contender makes the compositor **faster**, not slower

`[M]` independent probe on Mutter's main loop, with a client attached in both cases:
median **1.47 → 0.64 ms (0.44×)**, p95 **5.56 → 2.59**. ⇒ The five-session certification
**would fail**, and the bench would refuse the verdict — as the GPU one already did.

⇒ 🔸 **Coordinator's choice: the five-session window is NOT spent.** On the adversarial
recommendation of the author himself: the 4/18 is a difference of **outcome**, and `NON_ORA` is **a race with
`cattura_ridimensiona()`** — the window in which it flips is measured in **milliseconds, not in
load**, and the 18 rounds were **all at 30 ms**. ⏳ The road that remains is **sweeping the interval**
(10-60 ms, many rounds per point): it costs the CPU of a single session and **disturbs nobody**.

⭐ **And the compositor probe is certified**: `SIGSTOP` of 300 ms to `gnome-shell` ⇒ the probe
records **290.6 ms**. Proof that it looks at **the compositor** and nothing else.

### 5.12 · ⭐⭐ 22 Aug — **the colour inside the session: they are the SAME PIXELS, byte for byte**

*The last link missing for colour: not from the stream to the glass, but **from the desktop to the glass**.*

⭐⭐ **Zero different channels out of 2 704 104**, comparison **byte for byte** between what the application
paints and what the encoder receives.

| point | what it adds | mean | worst |
|---|---|---|---|
| painted → **captured** | Mutter's capture | **0.000** | ⭐ **0.000** |
| painted → **stream** | + our conversion + H.264 QP 26 + 4:2:0 | 0.334 | 3.005 |
| painted → **glass** | + Firefox's hardware decoder | 0.342 | 2.981 |

⭐ `glass − stream ≤ 0.03`: **the browser's decoder adds nothing measurable** —
independent confirmation of the 0.51 of §1.13-ter, taken **from the other end**. And the residue of ~3 levels
is not in the lights: **17 channels out of 1 029 above 2.0, all on the chroma ramps**, that is the round
RGB→YUV 4:2:0→RGB.

#### ⭐ And the three suspected transformations, separated one by one

| | outcome |
|---|---|
| **Night Light** at 1700 K, verified active by the daemon | ⭐ `[M]` **does not come in**: 0 bytes different |
| **shell effects** | ⛔ **they come in all right**: the *magnifier* gives **255 levels**, and ⛔⛔ **the activities overview** gives **221.75** — a less careful bench would have put it in the table as a «colour fault» |
| **compositor's ICC profile** | ⏳ `[?]` **not measured**: `colord` does not start on this machine, so there is nothing to turn on. `[R]` it travels the same road as Night Light, but it is **deduction** |

⭐⭐ **And the zero of Night Light holds because the magnifier passed**: without that control, a zero would be
indistinguishable from a blind bench.

⭐ **And for the product the question is closed structurally**: `sessione.c` removes `--virtual-monitor`
and the only monitor of the session is the one our capture mounts ⇒ there is no scanout, no
physical monitor, no colour device: **the session's «screen» IS the composited stage, and the
composited stage is what we capture.**

⛔ **And the fault of the bench, declared first**: the positive control of the magnifier **did not
turn on** — an `echo` with quotes inside broke the remote command and **no `gsettings` ran**. The
round measured «no difference» **believing it had the magnifier on**, that is exactly the
blindness that control was meant to exclude. ⇒ Now the bench **dies** if the read-back from dconf does not
say what it asked for.

### 5.13 · ⭐⭐ 22 Aug — **the slot ceiling is 30 seconds, not 75** — and the sentence of §5.3 about the frozen tab is false

*The `[?]` that bit every day: «the session's slot is one, and the previous one stays
attached for about twenty seconds» was folklore. `[M]` port 7801, `provar7`, real GNOME headless,
load 0.23-1.40.*

| the client goes away… | slot released | another client gets in |
|---|---|---|
| **clean farewell** | ⭐ **5 ms** | immediately |
| connection closed without farewell | **7 ms** | immediately |
| **killed** (socket closed) ×4 | 30.0 · 30.5 · 30.0 · **31.1 s** | same |
| **frozen** (black hole) ×3 | 31.1 · 31.2 · 30.0 s | same |
| ⛔ **alive on the wire, mute on RCP** | ⛔ **never** | ⛔ **26 knocks out of 26 rejected in 745 s** |

**Worst measured: 31.2 s.** ⛔ And dying «badly» changes nothing: closed socket (with ICMP) and mute
socket give the same numbers — **ngtcp2 does not react to ICMP**.

#### ⛔⛔ And the sentence of `SPECIFICHE.md` §5.3 about the frozen tab is **false on the wire**

*«A frozen tab is silent, so it gets detached»* — ⛔ no: the server fires a **PING every 10 s**, the
client's QUIC stack **answers by itself** without the page existing, and every answer renews the
life. ⇒ **The slot is never freed.** `[M]` 26 out of 26 in 745 s. ⚠ The product counts **packets**,
not RCP bytes — and it is a right and documented choice, ⛔ but **it is not what §5.3 tells**.

#### ⭐ The line for whoever writes benches — it is the thing everyone needed

> ⛔ **After a client has gone away badly, do not retry before 35 seconds.**
> ⛔⛔ **And if its process is still alive, 35 s are not enough: the slot stays taken for up to half an hour.**
> It is checked with `pgrep`, not with `pkill`.
> ⭐ **But waiting is almost never needed**: if the server is yours, **restart it** — the slots live in the
> process's memory, the graphical session lives outside: `[M]` the first attach after a restart reaches
> `SESSIONE` in **1.03 s**. ⭐ And if the client is yours, **make it say farewell**: **5-7 ms**.

#### ⛔ And the routes are TWO, with the same number — it is the mechanism behind the false reds

In 4 detaches out of 7 the slot was released by **the silence clock**; in the other 3 by the **death of the
QUIC connection** (30.00 s exactly). ⚠ **Which one arrives first is heads or tails**, and they leave **different log
lines and states**. ⇒ A bench that waits for the line «detached for silence» to know that the
slot is free **is red one time out of two**.

⭐ **And the positive control, without which the 30 s would be worth nothing**: with the inactivity clock
shortened to 25 s the same case released the slot at **19.8 s** with a different farewell ⇒ the bench
**can see** a release at a time other than 30.

⚠ **And what is missing, declared by the author**: no browser. The hypothesis he leaves behind is that
the «~75 s» were **~45 s of Firefox not dying + 30 s of the product**. It closes in a minute, with
a browser in hand.

#### ⏳ Four product things found along the way, not cured

| | |
|---|---|
| ⛔ `2 = RIPRESA` **never comes out** | the byte is a **constant 1** at the only point that builds the message. `[M]` 12 reattaches to the same child: **state 1, always**. It is form **E1** ⇒ whoever writes benches **cannot** use it to know whether they have a new desktop |
| ⛔ the **two routes** with the same number | above: two lines and two states under the same fact, racing |
| ⛔ the **live client holds the slot** | up to the half hour of inactivity — measured ≥ 745 s |
| ⏳ `[?]` **the immortal desktop** | `presenza_segna()` is called **from one place only**, the one that receives input ⇒ whoever attaches and **touches nothing** does not enter the present ones and **the abandonment clock does not start**. If true, every bench that attaches without typing leaves a desktop of **477 MB** that never dies — and that is how a machine with eight benches fills up. ⛔ **It is a reading of the code, not a measurement**: the round that was to prove it was skipped |

### 5.14 · ⛔ 22 Aug — **a wrong label made the user believe that a removed feature had come back**

> *«Avevo già detto che il ridimensionamento dinamico era fuori dal progetto, e tu lo hai
> reintrodotto.»* — the user, reading a report by the coordinator.

⭐ **In the product it has not come back**, verified: the code declares it out at **eight points**
(*«uscito»*, *«il fondo non c'è più»*, *«qui non parte»*), and the piece was **removed**, not put
behind a switch. The only thing that happens when resizing the window is that **the image
rescales**, which is the approved behaviour.

⛔ **But the NAME came back**, and in the reports in the worst place: the first of the four latencies of §5.6
and §5.9 was labelled **«live resize»** and measures something else entirely — the time between the
request **passed to the stage** and the request **arrived at the producer**, on the path of `ADATTA_TELA`,
that is the one every client walks **when attaching**. A thing that is there, and must be.

⇒ Whoever read *«live resize: 6 ms»* concluded that the feature had come back.

⚠ **And it is the same form of fault this night corrected six times in the benches** — *a name
that promises one thing and says another* — committed by the coordinator **in the documents**. ⛔ That it is
a label and not code does not make it less serious: **the documents are what remains**, and a
wrong name in a table of measurements outlives all of us.

⭐ **And it was the user who found it while reading, not a bench.** None of the automatic checks could
see it: no bench compares the **name** of a measurement with what the measurement does.

⇒ **Corrected everywhere**: in the bench (`06-b35-tempi.py`, with the story beside it) and in the three tables of
this document. The measurement is now called **«the canvas passed to the stage»**.

#### ⭐ And the vocabulary, given by the user

> *«Si chiama **re-scaling**.»*

⇒ **They are two different things and must be called by two different names**, always:

| | |
|---|---|
| ⛔ **dynamic resizing** | the remote desktop **changes size** while the user drags the border. **Out of the project since 17 Aug**, and it is not reopened |
| ⭐ **re-scaling** | the image **rescales** inside the window, and **the desktop's windows do not move**. It is what the product does, and it is approved |

⚠ Anyone who writes «resizing» without specifying which of the two **is about to repeat this
mistake**.

### 5.15 · ⛔⛔⭐ 22 Aug 2026 — **`06-b37` redone: the four false greens cured, and five faults that light them up**

*The bench of sub-phase 6.5 was the only one of the six **without any grafted fault** (§5.5). ⇒ Now
it has one: `banchi/06-b37-guasti.py` + `banchi/06-b37-guasti.sh`, **7 cases out of 7 on Chrome 151 and 7 out of 7
on Firefox 140esr — 14 out of 14** — each fault red **in the case declared beforehand**, and the same scene
green on the product. Machine load during the certifications: `load average` **0.34 → 2.10**,
a whole round **9 min 52 s** (Chrome) and **12 min 40 s** (Firefox).*

#### ⭐ The five faults, and what they light up

| | the fault, in a copy of `src/pagina.html` | the scene that accuses it | the false green it unmasks |
|---|---|---|---|
| **G1** | the requested canvas is **30 px narrower** than the window | `numeri` A5 · `sfora` · `pixel` X1-bis | ⛔ no scene had a **lower limit**: 12 combinations out of 12 stayed green |
| **G2** | the `if (tela_spenta)` guard is **bypassed** | `voce` **V5** | ⛔ the spy **replaced** `chiedi_tela`, and the guard is **inside** the replaced function |
| **G3** | `misura_vista()` goes back to the **`Math.round`** of before the cure | `sfora` at dpr 1.5 (**«TAGLIATO 979 px su 980»**) | ⛔ A6 was an **identity**: the «external truth» simplified to `round(cw·dpr)`, that is to the same rounding as the fault ⇒ **the real fault that this phase cured passed under A6 without touching it** |
| **G4** | the image is painted **50 px out of place** in the buffer, and `dipinta.x` still says 0 | `coordinate` **C0** | ⛔ the origin was **subtracted by construction** |
| **G5** | the **parity** of `tela_da_chiedere()` is removed | `numeri` A3 (63 canvases out of 63) | ⛔ the odd side was impossible **by construction** and was never provoked |

#### ⭐⭐ And G4's counter-proof lives inside the bench, for ever

`06-b37-coordinate.py` measures **every point twice** — with the real origin and with the old
formula — and prints the two gaps side by side. `[M]` with G4 grafted, Chrome, 9 points over 3 scenes:

| | top-left | centre | bottom-right |
|---|---|---|---|
| **new method** | **+51** · **+50** · **+51** | **+50** · **+50** · **+51** | +0 · +0 · +0 *(saturates at the border)* |
| ⛔ **old method** (which subtracted the origin) | **+0** · +0 · +0 | **−1** · +0 · +0 | −1 · −1 · +0 |

⇒ ⛔ **The old method, with the image shifted by 50 pixels, would have been GREEN on all nine
points.** It is no longer a hypothesis of the review: it is measured.

#### ⛔⛔ And THREE NEW FAULTS OF THE BENCH, which nobody had named yet

1. ⛔⛔ **The four scenes on the pixels no longer measured ANYTHING.** They put the frame in with
   `schermo.deposito = c; schermo.componi()`, ⛔ but `componi()` begins with
   `if (this.bm) { … return false; }` and `this.bm` is there on both engines since the canvas
   moved to **`bitmaprenderer`** (`DECISIONI.md` §5.4). ⇒ `[M]` 22 Aug: `sfora` on Chrome,
   **12 photographs out of 12 without any marker**. ⭐ The benches behaved well — they said «the
   markers cannot be found» instead of a zero — ⚠ but **the outcomes of 16 Aug in the repository are from
   before that change**, and §4.3-bis still declared them good. ⇒ Cured: the frame goes
   through **`schermo.mostra()`**, the function that receives the real frames, and every outcome line declares
   the **`strada`**;
2. ⛔ **`numeri` was RED FOR EVER with a forced device factor**: A1 compares two
   zooms, with `FATTORE=` there is only one, and that case did `guasti += 1`. ⇒ That is why nobody had ever
   launched the scene at dpr 1.25 or 1.5. A question **not asked** is now declared and does not
   count as a wrong answer;
3. ⛔⛔ **the bench filled the machine's disk — and the disk belongs to everyone.** `[M]` a whole round
   wrote **1.5 GB** of raw frames (1600×1000×3 = 4.8 MB each, **63 calibrations in the
   `numeri` scene alone**) into `/tmp`, which here is a **3.8 GB tmpfs shared with eight other agents**.
   It brought it to **100 %**, and the next round died with *«No space left on device»* — ⚠ on someone
   else's bench it would have died **without anyone understanding why**. ⇒ Cured: the pixels are read from a
   **pipe**, they end up on disk only with `B37_FOTO=tieni`, and the outcome line carries `null` instead
   of a path that does not exist;
4. ⚠ **and a fourth thing, which was not a fault but a flaky, and was worth three faults**: `voce` on
   Firefox launched right after another scene died because **the first command timed out at 20 s** —
   the page had announced itself, ⛔ but the loop that asks for the commands had not yet started. The
   certifier read it as *«the HEALTHY round is red»* and **refused to certify three
   faults**: `[M]` first round on Firefox **4 confirmed out of 7**, second round **7 out of 7**.
   ⇒ Cured: `aspetta_canale()` — the page announcing itself and the loop that answers are **two different
   things**, and now one waits for the second. ⭐ And the certifier behaved well: it said
   «I do not certify» instead of counting those three as confirmed.

#### ⭐⭐ And now `bash banchi/06-b37-lancia.sh tutti tutte` really runs

`[M]` 22 Aug 2026, 09:48, load `0.57 → 0.64`: **14 scene rounds in a single invocation**
(seven scenes × two engines), **80 green verdicts and zero red**, `windows` included — which brings
along its 2600×1000 screen and its 1.25 factor without touching the other six.
⇒ ⛔ The line *«until it is cured, one scene at a time is run»* falls.

#### ⚠ And on Gecko there is one more line to discard, declared instead of discarded silently

Below its minimum **Firefox does not shrink the layout box**: `clientWidth` stays
large, the X window shrinks anyway, and what is inside **gets cut by the window's
border**. `[M]` the calibration strip comes out up to **210 px** shorter than
`clientWidth × dpr`. ⇒ **12 lines out of 63** are not a scene and are discarded — ⛔ but the comparison that
discards them is between **two numbers of the browser** (`clientWidth × dpr` and the pixels), not between the bench and the
product: no fault of the page can hide there, because `misura_vista()` enters
neither of the two sides. ⇒ On Firefox the denominator of `numeri` is **48 lines out of 63**, and the 12
discarded are printed one by one.

#### ⚙ What changed in the bench, file by file

| | |
|---|---|
| ⭐ `06-b37-guasti.py` · `.sh` | **new**: the five faults with the verified anchor (7 anchors out of 7 alive, multiplicity 1) and the certifier, which demands **the healthy one green**, **the fault red** and **the sentence declared beforehand** — ⛔ not just any red (it is remark 2 of §5.5 on `06-b33`) |
| `06-b37-comune.py` | the **calibration on the pixels** (two strips at a fixed position, `ox`/`oy` and the view in device pixels, with **two masks** because at a non-integer dpr the border falls at half a pixel) · `mostra()` for the product's route · the **round's mark** on every outcome line |
| `06-b37-numeri.py` | A2 and A6 **rewritten** on that external truth, A5 **bidirectional**, A1's tolerance **derived** instead of chosen |
| `06-b37-sfora.py` · `-pixel.py` · `-windows.py` | the **lower limit** (`W − ceil(dpr) ≤ disegno`), the product's route, the half pixel **counted** |
| `06-b37-coordinate.py` | **C0 · the origin** and the counter-proof with the old method |
| `06-b37-voce.py` · `-modi.py` | the **real text** of `chiedi_tela` extracted from the product and installed with a direct `eval` on a fake channel ⇒ the guard is crossed, and the observable is `canale.manda(TIPO.ADATTA_TELA, …)` |
| `06-b37-lancia.sh` | the **seventh scene** in «tutte» (with its 2600×1000 screen and its 1.25 factor) · the fault declared in §4.3-bis — *«after the first scene the browser does not reopen»* — **cured**: it waits until everything holding the profile is dead |
| `06-b37-strumenta.py` | extracts and verifies the text of `chiedi_tela` (58 lines), and **fails loudly** if the anchor is not there |

### 5.16 · ⭐⭐ 22 Aug — **three proposals to the product: two REJECTED by measurement, one refuted the other way round**

*The proposals came from whoever had exercised `cattura.c` with the fake stage. ⭐ All three were
put to the test instead of implemented, and the result is more useful than three cures.*

| the proposal | the outcome |
|---|---|
| *«`cattura_ridimensiona()` declares success on a stream that dies, and `figlio.c` has no way of knowing»* | ⛔ **REJECTED**: the premise is false. `[M]` with the child's real loop, the fault arrives at **8.1 ms** with **state and cause from the producer** — it is not a timeout. ⭐ And a «dead» outcome returned by the function would be **green by construction**: the death arrives 2 ms after the return |
| *«an accessor for the divergence is needed»* | ⛔ **REJECTED**, and with three measurements: the only scene that lights up the field gives a **false alarm** (the «granted» were the previous request, not a grant); the two accessors that exist **are enough** and can also say «not yet negotiated»; and the counter route **does not hold** — two chained requests produce **a single** answer, so the counts diverge for ever |
| *«the branch "granted different from requested" is not reached»* | ⭐⭐ **REFUTED THE OTHER WAY ROUND**: it is reached, **43 hits out of 480 chains** |

⭐⭐ **And the refutation found a product fault**: the log line said *«the coordinate
conversion is born wrong and the pointer will go elsewhere»* — ⛔ and in the **only** scene that
lights it up it is **false**. ⇒ *A log that attributes the wrong cause costs more than a silent
log.* Rewritten: it says the fact, names the **two** possible motives, and points to where the verdict is really
given.

⚠ **And the divergence guard remains a comment with a `gboolean` attached — but now the code
says so**, instead of letting people believe someone reads it.

⛔ **And a fault of the bench that the author declared first**: his case 6 *«printed a number
it had not read»* — two zeros written by hand in the line in place of the measurement. ⭐ *«È esattamente
il difetto che avrei segnalato a un altro.»*

⏳ **And a real fault left open, not his to cure**: `[M]` the remount asks the stage for **the
size that has just killed it**, and the call **succeeds 3 times out of 3** while the stage dies 300 ms
later — with the short wait a **noose** is chosen, and nobody notices. ⚠ On the real product it is
`[?]`, because Mutter grants everything under the ceiling. It is **declared in the code** next to the branch.

## 6 · The decisions produced

- ✅ **`DECISIONI.md` §5-bis.7** — *the keyboard layout is commanded by the client, and the server
  applies it*: **confirmed by the user on 16 Aug 2026**, when put in front of the three routes. ⛔ And the
  new box of that entry carries the measurement that made it necessary: it was a **✅ decision of 8
  Aug never implemented**;
- ⏳ **`RCP.md` §7.1** — the missing line about the **stage that changes size by itself** now has **two
  drafts proposed and measured** (by 6.4 on the wire, by 6.3 on the real compositor), to be merged:
  no unsolicited `TELA` · do not adopt · do not send frames of a different size ·
  request the canvas in force with a growing wait · write it in the log · ⛔ **and never
  recall the stage while a client request is in flight**;
- ⏳ **`RCP.md`**, six more lines delivered by the agents and not yet written: the boundary of the
  grace second (`<` or `<=`), the two canvases within the same second, the limits of the **view** that
  §4.5 does not name, what the server answers to `VISTA` (⛔ *nothing*, and why a courtesy `TELA`
  would kill the session), `COMPOSITORE_INCAPACE` not declared **permanent**, and ⛔ **the
  contradiction §7.1 against §4.2** on `ADATTA_TELA` followed by the client's FIN;
- ⏳ **`SPECIFICHE.md` §6** — five lines proposed by 6.5, among them the closing of the three `[?]` of
  §6.1-bis and the **guard number** of sharpness;
- ⏳ **`SPECIFICHE.md` §11.5** — Windows is not declared among the clients (the section names the **engines**,
  not the systems).

---

## 7 · What remains `[?]`

### 7.1 · ⛔ Open and with a measurement in hand — the work to come

| | |
|---|---|
| ⛔⛔ **the device swap that does NOT depend on the canvas** | `[M]` every `cattura_risveglia()` (400 ms, still scene, key due) recreates the `libei` devices: **3 wake-ups, 3 swaps**, with **zero `ADATTA_TELA`**. ⇒ The dying click has a **second door**, open exactly when the user holds the mouse down on a still desktop, and the obvious cure would destroy every drag. ⏳ **The right form must be decided**, and it does not belong to a single sub-phase |
| ✅ ~~⛔ **the fault is upstream, in Mutter**~~ · ⛔ **and the answer is worse than the question** | **CLOSED on 21 Aug 2026** `[R]`: the fault is real, **nobody ever opened it**, and **it is not fixed even in today's `main`** — `remove_viewport_devices()` is identical character for character between the 48.7 running here and the main branch of August 2026. ⇒ There is no version to wait for: **the cure is ours, on every Mutter**. The follow-up is in §7.1-bis |
| ✅ ~~**the chained requests, to be re-measured**~~ · ⛔ **and a worse hole remains** | re-measured on 17 Aug: **0 broken out of 18** (§4.8). ⛔⛔ **But the positive control did not pay off**: removing the suspected cure still gives **0/18** ⇒ *it is not known what holds this scene*, and the **4/18** of 6.3 **cannot be reproduced** with the machine idle. ⚠ The only difference left is **GPU contention** (five encoders on the same iGPU): until it is recreated, ⛔ **the green holds «under CPU load», not «under GPU contention»** |
| ✅ ~~**the click cure was never verified where it lives**~~ | verified on 17 Aug on a single tree: the release is declared in the log and **all the clicks of the second round arrive**, ⭐ with the positive control reproducing the fault **on command** |
| ✅ ~~**all the milliseconds are under load**~~ | retaken with the machine idle (load 0.07-0.13): §4.8 |
| ⛔ **three expected values of `06-b33` are written for the world WITH THE FAULT ALIVE** | T3, R1 and R2 stay **red with the cure** and were **green without**: with the key already released before the swap, the declaration lines are not written because nothing is pressed any more. ⇒ **The bench's expected value must be corrected, not the product** — and it is a bench born yesterday, so the fault is from yesterday |
| ✅ ~~⚠ **two tools of bench 6.3 break**~~ | **CURED on 21 Aug** and certified against a hand calculation in `awk` (235 samples, all matching). ⭐ The cause was not in the tools: it was the **log interleaving** between parent and child. 📖 §5.6 |

### 7.1-bis · ⭐⭐ 21 Aug 2026 — **the complete chain of the dying click**, read in Mutter's source

*All `[R]`, from the source of `reference-gnome/mutter` (tag **48.7**, commit `f4abb824`) — ⭐ and
`[M]` the test machine runs **exactly that one**: GNOME Shell 48.7, `libmutter-16-0`
48.7-0+deb13u1, `libei1`/`libeis1` 1.3.901-1. No version gap to discount.*

#### ⭐ WHY the devices are recreated even without `ADATTA_TELA` — the `[?]` of §4.6 has a cause

`meta_screen_cast_virtual_stream_src_enable()`
(`⟨mutter⟩ src/backends/meta-screen-cast-virtual-stream-src.c` · `meta_screen_cast_virtual_stream_src_*`) calls
`meta_eis_viewport_notify_changed()`. ⇒ **Every re-enabling of the stream recreates the devices**,
that is **every `cattura_risveglia()`** — and it is the «3 wake-ups, 3 swaps, zero `ADATTA_TELA`» of §7.1,
which was not a mystery but that line. ⚠ It comes from **MR !4622**, which went into **Mutter 48.5**: it is
recent, and we are inside the window.

⚠ **And there is a second multiplier**: `add_logical_monitor_viewports()`
(`meta-remote-desktop-session.c:388`) does `remove_all_viewports` **then** `take_viewports`, and
**both** emit `viewports-changed` ⇒ **two swap rounds for every monitor change**.

#### ⛔ The fault is PERMANENT, not a race — and Mutter has a safety net that CANNOT be reached here

⚠ **This is the part that makes the line of §7.1 refutable, and why before it did not hold.** Whoever reads
only *«`remove_viewport_devices()` does not go through `drop_device()`»* can answer: *«but Mutter
releases anyway in `dispose`»* — and seems to be right, because
`meta_virtual_input_device_native_dispose()` calls `release_device_in_impl()`, which releases **all**
the buttons and keys held down, complete with a diagnostic line.

⛔ **On this path that net is unreachable**, and the chain has three links:

1. the `ClutterVirtualInputDevice` dies **only** with `meta_eis_device_free()`, destructor of the
   table `client->eis_devices`;
2. outside the disconnect, the only one that removes an entry from that table is the
   **`EIS_EVENT_DEVICE_CLOSED`** branch (`meta-eis-client.c:987`);
3. ⭐ `[R]` **on libei 1.3.901-1, which is the installed version**: that event is generated **only**
   by a `release` sent **by the client** (`eis_device_closed_by_client()` ← `client_msg_release()`).
   `eis_device_remove()` **never** generates it: it sets the state to `DEAD` and sends `destroyed`. And the
   client must not even call `ei_device_close()` on a device removed by the server — libei's
   public header says so, and indeed Mutter's test client does not call it.

⇒ ⛔⛔ **The entry stays in the table for ever**, `release_device_in_impl()` never runs, and
`seat_impl->button_count[BTN_LEFT]` stays **1 for ever**. It heals **only at disconnect**, which is
the only place `drop_device()` goes through — ⭐ and it is exactly the *«it heals only by restarting
the server»* that §4.6 had measured without knowing why.

⚠ **And `button_count[]` belongs to the SEAT, not to the device**: it is the reason why the cure could
be much smaller than it seems — a release sent from a **new** device can
still bring the count down. ⏳ To be measured, not deduced.

#### ⛔ Our cure of today covers the other path

`input_rilascia_tutto()` before `cattura_ridimensiona()` (`figlio.c` · `codificatore_di()`) covers the **geometry
change**. ⛔ It does **not** cover `cattura_risveglia()`. ⇒ The «second door» of §7.1 is open precisely
where the cure does not reach.

#### ⛔ Upstream: nobody ever opened it, and it is not fixed in today's `main`

`[R]` searched on 21 Aug 2026 on the API of `gitlab.gnome.org/GNOME/mutter`: the issues with `eis` and
`libei`, the **15** merge requests with `eis` in the title from 2023 to today, and a search for
`remove_viewport_devices` ⇒ **nothing**. Same for `gnome-remote-desktop`.

⭐ **The only precedent is the best proof that the asymmetry is not intended**: MR **!3809**,
*«backends/eis-client: Release buttons on device remove»*, merged on 14 Jun 2024, fixes a single
line **inside `drop_device` and only there**. ⇒ The upstream intent is declared in the title, and the viewport
path violates it.

⛔ **And it is not fixed today**: downloading `meta-eis-client.c` from the **`main`** branch (August 2026, series
50/51), `remove_viewport_devices()`, `drop_device()`, `update_viewports()` and `remove_device()` are
**identical character for character** to 48.7. ⇒ There is no version to wait for nor a
distribution already fixed: **our cure is needed on all of them**.

⭐ *(In addition, Mutter's burden and not ours: it is also a **memory leak** — the table holds
an `eis_device_unref` as destructor, so `struct eis_device` and `MetaEisDevice` stay alive at
every swap, for the whole session. `remove_abs_devices()` and
`remove_touch_devices()` have the same vice.)*

#### ⏳ What remains, and costs little

⛔ **This whole chain is `[R]`, not `[M]`**: it is code read, not measured. The decisive confirmation is
a diagnostic line: with `MUTTER_DEBUG=eis,input`, after a viewport swap **with the button
pressed**, one expects `Dropping repeated press of button 0x110, count 2` **and the absence** of
`Releasing pressed buttons while destroying virtual input device`. ⚠ **If the second
line appeared, the whole reading falls** — and that is why it is written here: a chain that does not know how
to be refuted is not a diagnosis.

`[?]` Whether the maintainers consider it a Mutter fault or «something the client must handle»: it
cannot be deduced from the code. ⛔ **And nothing has been opened upstream**: it is an outward action, and
the user decides it.

### 7.2 · The measurement `[?]`, declared instead of extrapolated

- **the DeX and the real GPU**: the half pixel does not reach the pixels on Xvfb ⇒ `[?]` **on a real GPU and on
  Samsung DeX**. ⛔ The phone is the user's: one asks him, one does not work around it;
- ⛔⛔ **And one of the three `[?]` of `SPECIFICHE.md` §6.1-bis had been REPLACED silently.** The three
  real ones are the **zoom** (✅ closed on 22 Aug, with the tolerance *derived* instead of chosen), the
  **odd side** (✅ closed, with a grafted fault as positive control) and ⛔⛔ **«on DeX does
  `screen` answer with the external screen or with the phone?»** — which **nobody ever touched**,
  because the phone is the user's. ⚠ In its place the document had put **«the half pixel»**, which
  is another question: ⇒ one `[?]` vanished and one appeared, without anyone noticing. 📖 §5.15;
- ⛔ **«conforming» is not «works»**: the arbiter certifies the bytes — *«a server that answered
  `TELA(ADATTATA)` without touching the stage would pass all five rounds»*. The pixels are measured by
  another bench, and the distinction must be kept;
- ✅ ~~**the grace second cured and not measured**~~ — **CLOSED on 22 Aug**, and ⛔ **the reason
  it seemed impossible was wrong**: the grace starts from the `TELA`, **not from the connection**,
  so the 1500 ms of the handshake have nothing to do with it. 📖 §5.10;
- ✅ ~~**code never exercised on Mutter**: the branch «granted different from requested» and
  `MISURA DIVERGENTE`~~ — **REFUTED on 22 Aug**: ⭐ `MISURA DIVERGENTE` (today `cattura.c` · `su_parametri()`)
  **is reached from outside** — `[M]` **43 hits out of 480 chains**, three sweeps out of three. ⛔ The door
  is not the producer, **it is time**: two chained resizes — *the user dragging the
  border* — and the answer to the first comes back when the request already carries the second. Window: between
  **200 and 800 µs**. ⇒ It is a race, ⭐ **but a race a bench can program**: one sweeps the distance
  between the two calls. ⚠ The one in `figlio.c` (today `:6764`) remains unexercised: it would need a real
  frame, and the fake stage does not queue any. 📖 §5.16;
- ✅ ~~**the slot is released after ~75 s** of silence, not the 30 of §5.3~~ — **MEASURED on 22 Aug:
  it is 30, and the «~75» does not reproduce.** 📖 §5.13;
- ✅ ~~**the coordinates in flight cannot be arbitrated from a recording**~~: since 21 Aug `RCP.md`
  §11.1 records the **time**, and the rule is testable — ⛔ **in one direction only**, and §5.10 tells
  why that direction is not enough;
- **`?video=worker` not exercised**; **`aioquic` is not installed on the laptop** (the client is
  tested locally only with surrogates, and the bench declares it);
- ⛔ **the fallback on KWin remains unverifiable for real**: KDE is phase 11. The code path
  is tested **on the fake host**, and the **log line** that declares it is now demanded by a
  bench (`06-b36` cases 1-2) — which is what `SPECIFICHE.md` §6.3 asked for.

### 7.3 · ✅ ~~And the three faults that the user's decision makes urgent~~ — **they were already closed, and the document had been lying for five days**

> ⛔ **This section listed three faults the product does not have.** Measured live on 21 Aug
> 2026 (port 7721, user `provat6`, real GNOME session with a witness inside, load 0.20-0.60):

| the document said | `[M]` the product does |
|---|---|
| `hu` `tr` `gr` `ua` receive `SESSIONE_NON_SERVIBILE` | ⭐ **they open the session**, all four |
| `it(nonesiste)` opens the session | ⭐ **`0x0E SESSIONE_NON_SERVIBILE`** |
| `DISPOSIZIONE` with the session open closes the connection | ⭐ **connection alive**, `KEYMAP CAMBIATA → de [German]`, no message on the wire |

⇒ They had been closed by the stitching of **16 Aug**: the question «does it exist?» goes to XKB
(`webtransport.c` · `gancio_disposizione_esiste()` → `tastiera.c`), the variant enters it because `it(nonesiste)` does not compile, and
`T_DISPOSIZIONE` has its `case` (`rcp.c` · `drena()`). ⚠ Nobody had re-read this section, and it is the
same kind of fault as `fasi/07` §8: **a document stuck at four days ago sends people looking for a
fault where there is none**.

⭐ **And it did not stop at «the session opens»**, which is the yardstick this phase forbids: the
witness inside the session recorded **the character**, with the expected value computed by `tastiera.c`
called from outside — `hu`→`ű`,`ő` · `tr`→`ğ` · `gr`→`α` · `ua`→`ї` · `de(T3)`→`‑`, **all arrived**,
plus the negative (`it` does not produce `ű`, and the line declaring it is there).

#### ⛔⭐ But in their place there was a REAL one: **form D1 survived its own cure**

The cure of 16 Aug removed the fixed list of twenty names, ⛔ **and in front of the hook a
second hand-written list remained: the alphabet allowed in the name**, which accepted only `[a-z0-9]`.

`[M]` Asking the system **through the product**, on all **590**
layout/variant pairs of `evdev.lst`: **589 compile**, and **nine have an uppercase letter** —
`de(T3)`, `ie(CloGaelach)`, `ie(UnicodeExpert)`, `in(tamilnet_TAB)`, `in(tamilnet_TSCII)`,
`jp(OADG109A)`, `lk(tam_TAB)`, `ru(phonetic_YAZHERTY)`, `ua(macOS)`. ⛔ On the wire they received
**`0x0B ERRORE_PROTOCOLLO`** — which is **worse** than `SESSIONE_NON_SERVIBILE`, because it says *«your
client is broken»* and sends people looking for the fault on the other side of the wire. And `it()` (empty variant)
got `0x0E` on a **malformed** string: the two faults of §4.5 together.

⇒ **Cured** (`rcp.c` · `tratta_credenziali()`, and the twin aligned byte for byte): a single
`disposizione_carattere_ammesso()` with the alphabet **identical** to that of `tastiera.c`, plus the
rejection of the empty variant. ⚠ Two form checks written twice gave two answers under
the same label: it is form **E2**. The defence is not loosened — dot, slash, comma and
`../../etc/passwd` stay out. ⭐ Declared price: `IT` now passes the form and receives `0x0E`
instead of `0x0B`, and it is the right answer (XKB distinguishes uppercase).

⭐ **Red→green certified** on the same machine: case 8, **7 red lines out of 17** with the binary of
before → **17 out of 17** with the cured one; and four grafted faults that light up the declared case.



---

## 8 · The user's judgement

*The phase closes on a measurement judged by the user, not on a complete document.
⛔ A verdict the user did not give is not written.*

✅ **One is already there, and it is from 16 Aug 2026**: **«il test su Windows lo dichiaro superato al 100 %»**
— given on the live product, from a third client system never tested before, with `dpr 1.25` and the window
odd on both sides (§4.1 and §4.1-bis).

✅ **And on 22 Aug 2026 the other two arrived too**, that is the two scenes this phase
had opened:

| the scene | the judgement |
|---|---|
| ⭐ **the click held down** | *«Sto tenendo il clic premuto ed è tutto ok.»* ⇒ **The second door of the dying click can no longer be felt.** It was the fault this phase chased for three days: from §4.6 (*«the click that dies»*) to §7.1-bis (the chain read in Mutter's source) to §5.7 (cures A+C) |
| ⭐ **dragging the border** | *«Riscala con la comparsa di bande nere, ma immagino sia normale per mantenere le proporzioni.»* ⇒ **Re-scaling is accepted**, bands included: it is the price declared when dynamic resizing left (`DECISIONI.md` §5.1-bis) |

⚠ **And a clarification by the user that has entered the vocabulary**: *«lo scaling è opera del browser,
non di REMOTIX»* — ⭐ and it is exact: we write **two sizes in CSS**, the rescaling is done by the
browser with its acceleration. The only thing we impose on it is **how** to rescale
(`image-rendering: pixelated`), so that the text stays crisp instead of being smeared. 📖 §5.14.

⛔ **And what the judgement does NOT cover, written so that it is not deduced**: the **guard of cure A**
(the line «TENUTI GIU'») **has not yet triggered in any measurement**. ⇒ The user says the fault
can no longer be felt — and that closes the **fault**. ⚠ But *«it cannot be felt»* is not *«the guard
worked»*: it could be cure **C** covering everything, and **A** never having been
exercised. A diagnostic `[?]` remains, not a product one.

## ⛔⛔ 21 Aug 2026 — **Firefox for Android does not have WebCodecs**, and our message lied

*First test on a real phone (Samsung DeX, Android 16). The user: «credo che abbiamo introdotto
una regressione per quanto riguarda Firefox su Android».*

⛔ **It was not a regression.** `[M]` From the server's log, the page's words:

```
browser: Mozilla/5.0 (Android 16; Mobile; rv:154.0) Firefox/154.0
         · schermo 2560x1080 · dpr 1 · WebCodecs NON c'e'
sonda video · ⛔ HEVC: NON arriva al pixel — questo browser non ha WebCodecs
sonda video · ⛔ H264: NON arriva al pixel — questo browser non ha WebCodecs
congedo motivo=0x09 dettaglio=nessun codec condiviso
```

⇒ `VideoDecoder` **does not exist** on that browser, and in `pagina.html` the road to the pixels is
**a single one**: zero occurrences of `MediaSource` in the whole file. ⚠ With AV1 it would have ended identically —
the switch to H.264 (§1.13-ter) has nothing to do with it, and the line of `DECISIONI.md` that said «that way Firefox
Android works» was a **wrong premise**, corrected here.

### ⛔ And our own thing was there: the message sent people looking in the wrong place

The box said *«questo browser non porta nessuno dei due codec video fino ai pixel: né HEVC né
H.264 … su Linux il decodificatore HEVC di Chrome è quello della scheda grafica»* — an explanation
about codecs and graphics cards, while the real cause was one line above and of another kind.

⇒ Now the **«WebCodecs non c'è»** box comes **first** and names itself: *«questo browser non ha
WebCodecs, cioè l'unico modo che REMOTIX ha di disegnare il desktop: non è una questione di codec»*.
⭐ A message that sends people to the wrong place is worse than no message.

### ⏳ What remains open

⚠ If Firefox for Android must be a supported engine, a **second drawing path** is needed
(MSE with a `<video>`): it is real work, it changes the delay properties, and it must be decided — it is not a
switch. ⭐ Chrome for Android has WebCodecs, and there the road exists.

## ⏳ 21 Aug 2026 — **what MSE would cost**, measured before writing the path

*The user's constraint: «supportare pienamente Chrome e Firefox in Linux, Windows e Android».
⛔ Firefox for Android does not have WebCodecs, so covering it means a **second drawing
path**: `MediaSource` with a `<video>`, with fragmented MP4 instead of Annex-B. ⇒ The price is
measured before, not after — bench `banchi/07-b57-quanto-costa-mse.py`.*

### The measurement — same iron, same stream (our 150 frames, 2560×962, H.264 High 5.0)

| | Firefox | Chrome |
|---|---|---|
| WebCodecs, 60/s | **60.5 ms** | **50.9 ms** |
| MSE, 60/s | 285.4 ms — ⛔ **+225 ms** | 465.6 ms — ⛔ **+415 ms** |
| MSE, 10/s | 246 ms — ⚠ **+17 ms** | 570 ms — **+348 ms** |
| playback queue | 310–650 ms | 520–715 ms |

⛔ **The declared ceiling is 50 ms** (`SPECIFICHE.md` §3.2). ⇒ At a useful rate MSE breaks it by an
order of magnitude, and not because of decoder slowness: the `<video>` **keeps a queue on purpose**,
because its job is smooth playback, not low delay.

⚠ **The limit of the measurement, declared**: the bench's screen is an `Xvfb` **without a GPU**, so both
roads decode in software. ⭐ But the presentation queue is not a property of the
video card, and the comparison is between two roads **in the very same place**.

⚠ **And chasing does not save it**: jumping to the live edge brings Firefox's median to 265 ms with
**40 jumps** over 150 frames — that is an image that stutters. Delay is traded for stutter.

### ⛔ Five faults of the bench, and each would have produced a false number

This bench lied **five times** before measuring, and it is worth listing them because they are
all of the same family — *the tool was measuring itself*:

1. `"null"` read as an outcome: Chrome gave three red lines **and worked**;
2. feeding at 10/s an MP4 that declares itself at 60 fps: the `<video>` runs at 60, runs dry, and
   `requestVideoFrameCallback` sees **two** frames out of a hundred;
3. measuring **start-up** instead of steady state: median 2.7 s with a queue of 160 ms;
4. ⛔ **no user gesture**: without a tap the `<video>` does not start at all — queue 3.5 s,
   *zero* frames dropped, and it looked like «MSE buffers» while it was «it never started»;
5. ⛔ **`ffmpeg -framerate` does not apply to the H.264 demuxer**: the file came out at **25 fps** while I
   fed it at 60, and the queue I called «MSE's» was my rate difference. It shows from
   `currentTime = 5.98 s` with 150 frames: 150/25 = 6 s. ⇒ `-r` is used, and **it is verified with
   `ffprobe`** instead of believing the command line.

⭐ Fault 4 was found **from an inconsistent number**, not from an error: «queue 3.5 s **and zero
frames dropped**» cannot describe a struggling decoder. A bench that had
reported only the median would never have shown it.

### ⏳ What remains to be decided — and is not decided here

⛔ With these numbers, «Firefox for Android fully supported» and «delay under 50 ms» **do not
go together**. ⇒ The choice is the user's, and the options are named: accept on that engine a
delay of another class, or declare it unsupported until Mozilla brings WebCodecs to
Android. ⚠ The definitive measurement is on the phone, which has the hardware; the bench is served on the home
network with `banchi/07-b57-servi-al-telefono.py`.

## ⭐⭐ 21 Aug 2026 — **the first Android session**, and the user: «Chrome è un missile»

*Chrome for Android, Samsung DeX, 2560×1080. Three and a half minutes of real session, `[M]` from the server's
log and from the page's diary.*

| | |
|---|---|
| negotiated codec | ⭐ **HEVC** (codec 1) — **not** the H.264 fallback |
| canvas | 2558×926 |
| frames | **3 178 arrived, 3 178 painted** |
| skipped · gaps · out of order · late · decoder errors | ⭐ **0 · 0 · 0 · 0 · 0** |
| input | 45 keys, all arrived |
| audio | 8 935 blocks received, 8 933 played, **2 gaps** in 3 min 30 |

⭐ **Zero losses on every row the diary counts.** It is the first time this code touches a
phone, and the video → screen direction has no fault to name.

⭐ **And the surprise is the codec**: the phone negotiated **HEVC in hardware**, that is the first choice
of `PREFERENZA` — not the fallback. ⚠ The H.264 of §1.13-ter remains necessary (desktop Firefox does not do
HEVC), but on this phone it was not needed.

### ⛔ And the only number that is not good: **the audio queue, 401 → 421 ms** — ⭐ and the same evening the user's ear CONFIRMED it

The diary reports it at every round and **it grows**: 401 ms at 10:37:39, 421 ms at 10:37:49, and there it stays.
The video, in the same session, has not one late frame ⇒ it is not the network: it is the queue of the
audio path.

⛔⭐ **And on the evening of 21 Aug the user listened, twice.** The first: *«Chrome su Android
offre un'esperienza completa: audio e video perfetti»*. The second, an hour later, on Windows:
*«**il ritardo di 400 ms tra audio e video in generale te lo confermo**»*. ⇒ The number **is not a
coincidence and is not Android's**: it is `AUDIO_CUSCINO_MS = 250` in `pagina.html`, plus the chain, and it is heard
as **wrong synchronisation** — not as dirty audio. 📖 The diagnosis and the named cure are in
`fasi/07-audio-e-appunti.md` §8 and §9.7-bis.

## ⭐⭐ 21 Aug 2026 — **the second drawing path**: fragmented MP4 on MSE

*`DECISIONI.md` §7.18, from the user: «si costruisce». ⛔ And the reason §0.1-bis does not forbid it:
that principle speaks of an engine that **renders worse**; here the engine **does not open at all**.*

⭐ **The protocol is not touched**: the same Annex-B frames of §6.2 pass on the wire. Only
**how the client draws them** changes, and the server does not notice.

⭐ **And the audio was not written**: the page already fell back to `pcm` when `AudioDecoder` is missing
(§4.3 imposes it on both and it is the always-available base). ⇒ The work was **only the video**.

### The three pieces

| piece | what it does |
|---|---|
| `MuxMP4` | the Annex-B frames become an initialisation segment (`ftyp`+`moov` with the `avcC` built from the SPS/PPS seen) and a `moof`+`mdat` per frame |
| `sonda_mse_una()` | the probe **paints on this road too** and the pixels are judged — ⭐ `isTypeSupported` is not believed (`LEZIONI.md` §1.9) |
| `Schermo.mse_*` | the `<video>` takes the place of the canvas, inherits class and style, and frames are counted with `requestVideoFrameCallback` — the only place, there, where one knows a pixel has arrived |

⚠ **The duration of each frame is the REAL one**, measured on arrival: a desktop does not have a
fixed rate — it stays still for seconds and then moves — and declaring 60/s to a `<video>` that receives three per
second would run it dry at every pause. `[M]` It is exactly the mistake that bench `07-b57`
made first, with `ffmpeg -framerate` which does not apply to the H.264 demuxer.

### ⛔ Two byte errors, found by re-reading before testing

1. **`trun`: version (1 byte) and then flags (3)**, not the other way round. Written reversed, the
   `<video>` reads `flags = 0x030500`, that is fields that are not there: ⚠ **it gives no error and does not
   paint**.
2. **`tkhd`: four bytes were missing** (volume + reserved) before the matrix, and everything that
   follows slipped.

⭐ And the muxer was **verified from outside before being connected**: our 150 frames passed
through the muxer and given to `ffprobe` → `h264, High, 2560×962, level 50, 2.372 s`, and `ffmpeg` decodes them.
⚠ A muxer tested only inside the browser would have confused «my MP4 is wrong» with «this
engine does not accept it».

### The measured state

| | |
|---|---|
| the road turns on and paints (Firefox, `?disegno=mse`) | ⭐ yes — `<video>` 1190×704, 4 painted, **0 gaps**, delay 50 ms, 1 jump |
| the normal road (WebCodecs) | ⭐ intact: `07-b51` 4 checks out of 4 per engine |
| Firefox for Android | ⏳ **to be tested on the phone** — it is the engine it exists for |

### ⛔ And the first round on Firefox Android failed — **«loaded» does not mean «painted»**

*The user, 21 Aug 2026: «non funziona». `[M]` And the page had already written why in the
server's log:*

```
sonda video · ⛔ H264: NON arriva al pixel — il `<video>` ha caricato ma i pixel
              non sono quelli della sonda (sinistra 0,0,0, destra 0,0,0)
```

⭐ **Zero-zero-zero on both sides is black, not «a wrong colour».** ⇒ The stream was
right — the `<video>` had **loaded** it, so the muxer works on the phone too — and what was
wrong was **the moment of the reading**: `loadeddata` says the frame was
*decoded*, not that it was **presented**, and `drawImage` from a `<video>` that has not yet
presented anything copies black.

⛔ The probe accused the stream of a fault of its own stopwatch. ⇒ Now it has the frame presented
(muted `play()` + `requestVideoFrameCallback` where available) and **re-reads up to twelve times**,
and ⭐ **recognises black** instead of turning it into a verdict.

⚠ It is the same family as the five faults of bench `07-b57`: *the tool was measuring itself*.

#### ⛔ And the second time the canvas was still black — **two causes, both from mobile engines**

`[M]` The probe's new line: *«il `<video>` non aveva ancora presentato niente: la tela è
tornata nera»* — after **twelve** re-reads in a second and a half. ⇒ It was not slowness: that
`<video>` **never** presented.

| cause | why |
|---|---|
| the probe's `<video>` was **off screen** (`left:-9999px`) | mobile engines do not present what nobody looks at: they save battery. ⇒ Now it is inside the view, **two pixels by two**, almost transparent — visible enough for the engine, not for the user |
| the probe started **at page load** | presenting means playing, and nobody had touched anything yet. ⇒ On this road the probing is done in `CIAO`, that is **after the user has pressed «Collegati»** |

⚠ And the second cure has a declared side effect: on MSE the probe costs its time **to whoever
connects** instead of at load. On the WebCodecs road nothing changes.

#### ⛔⛔ And at the third «nothing has changed» the fault was **elsewhere** — bench `07-b58`

*The user, 21 Aug 2026: «Non è cambiato assolutamente nulla, e mi stai facendo perdere tempo con
test inutili». ⭐ He was right on the whole line: I had him test **my probe** three times,
not the product — and three times what broke was not what I was asking him to look at.*

⭐ **The cure of the method, before that of the code**: `dom.media.webcodecs.enabled = false` removes
`VideoDecoder` **and** `AudioDecoder` from a desktop Firefox. `[M]` `typeof VideoDecoder ===
"undefined"` — exactly what Firefox for Android declares. ⇒ The road is tested **here**, and
one goes to the phone only once, at the end. It is bench `07-b58`.

⚠ And what that bench does NOT reproduce is declared: the power-saving rules of mobile engines — a
small or off-view `<video>` that is not presented. For those the last word remains with the
phone.

**At its first run it found in one go three faults that no round on the phone had
named:**

1. ⛔⛔ **The size scale called `VideoDecoder` and threw `ReferenceError` on every
   step** — the first included — and `video.misura_massima` came out as **320×240**, the minimum canvas of
   §4.5. ⇒ The server granted 320×240 and the desktop would have appeared **in a postage stamp**, without a
   line explaining it. Now on this road the capability is **omitted** (§4.3 allows it): what
   was not measured is not declared.
2. ⛔ **`document.body.dataset.schermo = "acceso"` was never written**, because on this road
   `dipingi()` is not passed through: the page would have stayed «waiting for the first frame» with the
   desktop already on the screen.
3. ⛔⛔ **The `<video>`'s wake-up hung on the presented frames.** A desktop stays still for
   seconds; the `<video>` runs out of data, pauses, and `requestVideoFrameCallback` **stops
   firing** — because it fires on presented frames. ⇒ The desktop's first pause would have
   frozen the image **for ever**. Now it also chases when new data arrives.

⭐ **And the rule «only what paints is declared» has here its first declared exception**
(`DECISIONI.md` §1.13, `LEZIONI.md` §1.9): on this road the probe would have to make a test `<video>`
*present* a frame, and on mobile engines a test `<video>` **does not present**.
⇒ It is declared on the engine's word, and the check moves to where the `<video>` is **real**:
`Schermo.mse_veglia()` writes in plain words if after four seconds not even one frame has been
presented. ⚠ The black canvas stays **explained**, which is the only thing the rule was meant to prevent.

#### The measurement, on a browser without WebCodecs — 25 seconds of live desktop

| | |
|---|---|
| frames delivered → **painted** | 291 → ⭐ **250** |
| gaps | ⭐ **0** |
| `<video>` queue | ⚠ 212 ms — consistent with the price measured in `07-b57` |
| canvas | ⭐ 1270×704, **not** the 320×240 of before |

⚠ And the bench too had its fault, declared: moving the pointer **does not make frames**
— the cursor travels on a channel of its own and the desktop's pixels do not change. `[M]` A whole round with
**one** frame, and it was about to declare «does not paint» of a road that painted what there was.
⇒ Now it opens a scrolling terminal.

#### ⛔ «Vedo il desktop ma non funziona l'input» — the canvas is not hidden

*The user, 21 Aug 2026, and it is the first time the desktop **can be seen** on Firefox for Android.*

⛔ **All** the input of this page is hooked to the `<canvas>` — `pointermove`, `mousedown`,
`wheel`, `contextmenu` and the four touch events — and the coordinates come out of its
`getBoundingClientRect()`. ⇒ Hiding it with `display:none` to make room for the `<video>`, the
events reached nobody and the rectangle was zero: **the desktop can be seen and cannot be
commanded**.

⭐ **The cure**: the canvas stays **where and as it is** — it is the surface that receives the gestures — and becomes
**transparent**; the `<video>` sits **behind** it, glued to its rectangle (`mse_posiziona()`, which
follows `cornice()`). ⇒ On this road, for whoever touches the screen, nothing changes: they touch the same
thing as always.

⚠ And the bench had its fault here too: it clicked at a coordinate chosen by eye, which
fell outside the canvas — and it would have said «the click does not arrive» of a click never given. ⇒ Now it
**asks the page** for the centre of the canvas.

#### The final measurement, browser without WebCodecs, live desktop

| | |
|---|---|
| image | ⭐ 351 delivered → **196 painted**, **0 gaps**, canvas 1270×704 |
| input | ⭐ **4 events to the server**: the letter, the movement, and `PULSANTE evdev 272` pressed and released |
| queue | 50 ms |

⚠ One frame out of two is not presented: it is the `<video>` discarding under a scrolling
terminal, **in software and without a GPU**. On the phone, which decodes H.264 in hardware, the ratio is
another matter — and there the user takes the measurement.

#### ⛔ «Non si vede il desktop» — the frame border was never called

*Right after the input cure: the desktop had disappeared.*

⛔ `cornice()` is what gives the canvas its **size on the glass**, and on the WebCodecs road it is
called by the drawing (`componi()`). ⇒ On this road the drawing does not pass through there: the canvas stayed
**sixteen pixels** wide — the size the `<canvas>` is born with in the document — and the `<video>`, which
now is glued behind it, followed it faithfully **in an invisible postage stamp**.

⭐ The frame size on this road is known (it is the granted canvas): it is written into `f_l`/`f_a`,
where both roads keep it, and the border is framed.

#### ⚠ And the bench was **green** while the user saw nothing

`07-b58` counted the frames and read the counters: all good. ⛔ It did not look at **where the
image ends up on the glass**, which is the only thing the user sees. ⇒ Now it measures it, and fails two
distinct cases:

| check | which fault it catches |
|---|---|
| the `<video>` occupies a reasonable fraction of the window | the postage stamp |
| the `<video>` is **glued** to the canvas rectangle (±2 px) | gestures that would end up in the wrong place, because the surface receiving them is not where the image is seen |

`[M]` Now: `tela [1270, 704] · video [1270, 704] · finestra [1270, 705]`, 6 input events to the
server, 499 frames delivered and 123 presented, 0 gaps.

## ⭐⭐⭐ 21 Aug 2026, evening — **REMOTIX runs on Firefox for Android**

*The user, after six rounds of tests on his phone: «non sei in grado di far funzionare Firefox per
android con remotix». Then: **«Installa la suite android sdk, usa quella»**. ⭐ He was right twice
— on the result and on the method.*

⭐ **The emulator's photograph**: inside Firefox 154 for Android — the same version as his
phone — there is the GNOME background, the top bar with the time `Aug 21 16:01`, and the two
`REMOTIX-SCENA` terminals scrolling **live** timestamps. Remote desktop, moving, on a browser without
WebCodecs.

### ⛔ The three faults only Android could show

`07-b58` (desktop Firefox with `dom.media.webcodecs.enabled=false`) catches almost everything, but it does **not**
catch what is specific to the mobile engine. These three came out only here:

1. ⛔⛔ **The seek that never ends.** Chasing the live edge wrote `currentTime`,
   that is a **seek** — and a seek wants a random access point, that is a key frame, which there
   is not there. `[M]` `cerca=true · pronto=1 · tempo=34,41 · buffer=0,00→40,34 · errore=no`, and
   **19 frames painted out of 727**. ⇒ No more jumping: it chases with **speed**
   (`playbackRate` 1.25 until the queue comes back). It costs a touch of acceleration instead of a
   stutter, and asks nobody for a key frame.
2. ⛔ **Pruning the past emptied everything.** `sb.remove()` to avoid keeping in memory what had been
   seen left `buffer=nessuno` with 817 frames delivered. ⇒ Removed: a few seconds of video
   in memory is a price gladly paid, a black page is not.
3. ⛔⛔ **And `dipinti` is not «how many are seen».** `requestVideoFrameCallback` on mobile engines is
   **throttled**: `[M]` 46 firings in 35 seconds while the desktop was moving. ⇒ Twice that
   number made me believe the image was still. The judge, there, is **the screen** — a
   photograph — not the counter.

### ⭐ And the tool stays: `banchi/07-b59-firefox-android.py`

Android 14 emulator with KVM, Firefox **154.0** for Android, and the full round by itself: it accepts the
certificate, logs in as «prova», lets it run, and reads in the **server's** log the line the
page tells about itself — `MISURA §7.18 MSE: consegnati … dipinti … fermo= cerca= pronto= buffer=`.

⚠ And what it does **not** reproduce is declared: the emulator does not have hardware decoding. ⇒ The delay
**numbers** do not hold; the **behaviour** holds — does it paint or not, does it stop or not, and
why.

⛔ **The method lesson, and the user taught it**: when a test requires six rounds from a
person, the wrong tool is not the product — it is the bench. Six hours earlier I could have
installed it.

### ⭐ The full round, done by me — 21 Aug 2026, evening

*The user: «prova tu».*

| test | outcome |
|---|---|
| **Firefox 154 for Android** (emulator, `07-b59`) | ⭐ desktop **alive** — clock `16:52`, terminals scrolling; `fermo=false cerca=false pronto=3`, the video time **advances by 4.43 s in 5** |
| input from Android | ⭐ the touch arrives: `PULSANTE codice evdev 272 rilasciato` in the server's log |
| delay on Android (emulator) | ⚠ **2.3 s** from the live edge — ⛔ and the number **does not hold**: software decoding, heavy scene, canvas 1080×2040 |
| **without WebCodecs, desktop** (`07-b58`) | ⭐ **0.21 s** from the live edge, 277 painted out of 444, input and geometry green |
| **normal road**, WebCodecs (`07-b51`) | ⭐ 4 checks out of 4 per engine, **intact** |

⛔ **And the bench's judgement was rewritten**, because it was wrong: it gave red on the counter
`dipinti`, which on mobile is throttled. ⇒ Now it looks at what really describes the state of the
`<video>` — *is it playing? is it seeking? does it have data? how far behind is it?* — and ⭐ **compares two
readings**, because an image that advances and a still one look the same in a single photograph.

## ⛔ 21 Aug 2026, evening — **the user's judgement: Firefox for Android is incompatible**

> *«Niente da fare, troppi problemi: disegno del desktop irregolare, input imprevedibile, dichiaro
> Firefox per Android incompatibile con REMOTIX.»*

⚠ **And the road works**: the desktop is seen alive and the touches arrive — measured a few hours earlier
on the same emulator. ⛔ But *«it works»* was not the goal: the goal is §0.1-bis, that is
an experience close to a local session. A `<video>` that **plays back** cannot be asked to
react like a decoder commanded by hand.

⇒ **In the product**: `VIA_MSE` no longer turns on by itself. On a browser without WebCodecs the page
**declares that it cannot**, and names the alternative (Chrome for Android). ⭐ Half an experience is
worse than an explained refusal.

⇒ **The code stays behind `?disegno=mse`**, because until Mozilla brings WebCodecs to Android it is
the only proof that the problem is not ours. At phase 13 it is decided whether to throw it away.

### ⭐ What good remains, and it is not little

| | |
|---|---|
| `07-b58` | REMOTIX on a browser **without WebCodecs**, reproduced on the desktop with one preference |
| `07-b59` | **real Firefox for Android**, in an emulator: certificate, login, measurement and photograph — by itself |
| `LEZIONI.md` §1.19 | whoever opens closes: the benches work on a person's desktop |
| the probe that recognises black, the frame border, the input hooked to the canvas | real faults, cured, that hold outside this road too |

⛔ **And the cost is written**: six rounds of tests on the user's phone and a day, for a
road that does not enter the product. ⚠ The lesson is not «it should not have been done»: it is that **the question "how
well will it perform?" should have been measured before building** — and the number was already there, from bench `07-b57`:
hundreds of milliseconds against a ceiling of 50.

