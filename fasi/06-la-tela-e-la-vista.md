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
7448 · 7501 · 7561 · 7571 · 7601 · 7691       other rings': they are COUNTED, not touched
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
| **6.4** | **The canvas on the wire** | points **4** and **5** arbiter side, on **bare** `rcp.c` with a fake stage: `COMPOSITORE_INCAPACE` **declared in the log**, the bottom of §7.1, `NON_ORA`, `MISURA_FUORI_LIMITI`, and ⛔ **the coordinates in flight** in the second after `TELA(ADATTATA)` — which nobody had ever tested | `src/rcp.c` · `src/rcp.h` (+ the twin `banchi/rcp/`) | `06-b36-*`, extends `04-b31-tela.c` |
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

| ring | how it is looked at | outcome |
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

## 5 · ⛔ Che cosa NON ha funzionato

*Si riempie anche quando fa una brutta figura. ⭐ E in questa fase la parte più istruttiva non sono
i difetti del prodotto: sono i **banchi che erano verdi senza guardare**.*

### 5.1 · I due mandati avversariali che sono stati SMENTITI dalla misura

| la frase da refutare | esito |
|---|---|
| *«il riattacco riaggancia i dispositivi e tutto funziona»* (6.1) | ⭐ **regge** sull'input normale: l'applicazione aperta prima dello stacco riceve **tutto**, con le coordinate esatte. ⛔ È falsa **solo** per lo stato *tenuto giù* — ed è lì che stava il difetto |
| *«la catena `figli_ritela()` → `cattura_ridimensiona()` regge»* (6.3) | ⛔ **FALSA**: con due `ADATTA_TELA` a 25-35 ms — *«chi trascina un bordo ne manda proprio due di fila»*, e il codice stesso lo chiama «IL caso» — **4 giri su 18** (poi 2/18) lasciano il desktop **non adattato**, e il client aspetta il fondo di **3 s** per ricevere `NON_ORA`. ⚠ Invece *«i fotogrammi scartati sono zero»* **regge**: 0 in tutti i giri |
| *«da quando la tela è la finestra, lo zoom non falsa più niente»* (6.5) | ⭐ **vera** — ⛔ ma nel posto sbagliato: a rompere la nitidezza era l'**arrotondamento**, non lo zoom |
| *«il prodotto viola §7.1 in almeno un caso della tela»* (6.6) | **non confermata** sui cinque casi esercitati contro il prodotto |

### 5.2 · ⛔ I banchi che erano verdi senza guardare — sei, e nessuno se n'era accorto

1. ⛔⛔ **`04-b31-certifica.sh`, guasto G8**: l'ancora era **scaduta** dal 16 agosto (una funzione nuova
   si era interposta fra le due che nominava) ⇒ **il più grave dei dodici guasti non si innestava
   più**. Il certificatore lo dichiarava con `??`, e nessuno lo lanciava;
2. ⛔⛔ **`01-b3` e `01-b4` parlavano formati diversi** dal 12 agosto (`RCPREG 0x00 0x01` contro
   `0x02`): **ogni** traccia del cliente usciva «registrazione rotta» e cinque verifiche fallivano.
   ⭐ *Nessuno dei due file era rotto da solo: il difetto stava fra i due*;
3. ⛔ **il validatore chiudeva sessioni sane**: la grazia di §6.2 era scritta, importata e
   **irraggiungibile**, perché nessuno diceva al giudice del fotogramma che una `ADATTA_TELA` era in
   volo;
4. ⛔ **`06-b34`, controllo positivo B**: rompendo il rilascio, il conto diventa `0` **ma il
   carattere arriva lo stesso** ⇒ `[M]` **Mutter rilascia da sé i tasti su un dispositivo che
   distrugge**, e il compositore ci copriva il guasto. Il verdetto è stato **spostato di grandezza**
   invece di essere lasciato verde;
5. ⛔ **`06-b35`, guasto G4**: dichiarato **VERDE prima del giro**, perché su Mutter «chiesto» e
   «concesso» coincidono sempre ⇒ quel banco **non copre** il difetto n° 5 dei dieci del 15 agosto,
   e lo scrive;
6. ⛔ **`06-b33`, guasto G1**: rompendo *un solo* meccanismo del ricambio non cambia niente — la
   robustezza è **ridondante** (tre riletture della regione). ⭐ Diventato un **non-guasto misurato**,
   ⚠ col limite dichiarato: *nessun caso protegge il singolo meccanismo*.

### 5.3 · Le figure peggiori degli agenti, tenute perché sono il metodo

- ⛔ un giro ha mandato l'input **sul canale di controllo** e il server ha congedato: difetto **del
  banco**, e il registro lo diceva in una riga (`CODER.md` §3.11 in atto);
- ⛔ tre giri col **testimone vuoto**: i caratteri finivano nella **casella di ricerca di GNOME**
  perché nessuna finestra aveva il fuoco, e un `Invio` ha lanciato Nautilus. Scoperto
  **fotografando il desktop**, non ragionandoci ⇒ da lì il preludio e i **canarini**;
- ⛔ `umask 077` rendeva il binario guasto `0700 root`: il figlio usciva con **37**, e il banco stava
  per scrivere cinque *«SMENTITO»* accusando il prodotto **dei propri permessi**;
- ⛔ un `grep` ha estratto **`1002`** — un uid — credendo di estrarre una parola d'ordine: cinque
  `RESPINTO` e **il ban di §4.4-bis fatto scattare da un difetto del banco**. ⚠ Il colore non lo
  diceva: l'ha detto **il denominatore nuovo** (*«0 coppie chiuse»*);
- ⛔ una **pipe attorno a `enter.sh`** si è mangiata la richiesta di `sudo`: dieci minuti appesi in
  silenzio — è la trappola **8** del §0-bis di questo documento, scritta e poi calpestata;
- ⛔ e due attesi **corretti sulla misura**, con la ragione scritta accanto invece che allargati per
  farli tornare.

### 5.4 · ⛔ E un errore del coordinatore che ha rischiato di sviare quattro banchi

Ho spedito a quattro agenti un allarme su `LEZIONI.md` §1.15 — *«su Xvfb `requestAnimationFrame` non
gira MAI, e in Blink il `resize` non arriva»* — ⛔ **e non si è riprodotto**: `[M]` 16 agosto 2026,
sonda `06-b37`, **184 quadri in 3 s e 6 `resize` su 6**, su tutti e due i motori.
⚠ *Non si tocca §1.15*: quella misura è del 13 agosto ed è vera per la scena che descriveva. ⭐ Ma la
**guardia** che ho preteso resta, e ha reso: `giudica_palco()` ha **fermato un giro** in cui la scena
non stava producendo quel che il banco credeva (4 `resize` su 6, per passi da 1 px che non cambiano
la vista in pixel CSS). ⇒ *Un allarme sbagliato che lascia dietro uno strumento giusto.*

---

### 5.5 · ⛔⛔⛔ LA REVISIONE AVVERSARIALE DEI SEI BANCHI — 21 agosto 2026, e **cinque su sei non reggono**

*È il momento che `PIANO.md` §0.4 chiedeva e che questa fase non aveva mai avuto: il revisore **sul
banco**. I sei agenti avevano scritto il proprio banco e **certificato se stessi**. ⛔ Adesso li ha
letti qualcuno che non li aveva scritti — sola lettura, nessun banco lanciato — e il conto è questo.*

| banco | verdetto | perché |
|---|---|---|
| `06-b33` riattacco | ⛔ **non regge come certificazione** | il giro `tenuto` — l'unico che porta il difetto vero — **non ha una riga sana di riferimento**, e il suo unico guasto si certifica da solo |
| `06-b34` tastiera | ⛔⛔ **non regge** | 3 casi su 7 non possono fallire, 2 calcolano il verdetto e lo buttano, e l'ancora del guasto principale **è nata scaduta** |
| `06-b35` palco | ⛔ **non regge come certificazione** | il marcatore del registro si prende **prima** che `accendi` azzeri il registro ⇒ i due conti che vengono dal registro sono **zero per costruzione** |
| `06-b36` tela sul filo | ⚠ **il banco regge, il certificatore no** | ⭐ è il migliore dei sei: orologio iniettato, registro troncato, attesi esterni, confine 1000/1001 ms. Ma il certificatore esce **0** anche se non innesta niente, e 3 casi su 23 non hanno guasto |
| `06-b37` pagina | ⛔⛔ **non regge** | ⛔ **l'unico dei sei senza NESSUN guasto innestato**, e quattro falsi verdi indipendenti |
| `06-b38` arbitro | ⚠ **le 49 e le 19 reggono, i cinque giri vivi no** | ⭐ la metà offline è la meglio costruita del deposito. `06-b38-tela.sh` è verde **contro un server che non risponde mai** |

⭐ **E il rifiuto motivato vale quanto le accuse**: di **43 ancore di guasto** verificate materialmente
sui sorgenti di oggi, **42 sono vive con molteplicità esattamente 1**. Il caso `04-b31` G8 — l'ancora
scaduta — **non si è ripetuto**, tranne una volta in `06-b34`.

#### ⛔ I quattro rilievi che tolgono il pavimento

1. **`06-b33`: il controllo positivo è morto e dichiara successo.** Il certificatore manda in modo
   `tenuto` **solo** il guasto G3; il giro sano e il risanato girano solo in modo `comanda`. ⇒ R1
   oggi è rosso perché col tasto già rilasciato non c'è più niente di premuto — non per il guasto — e
   lo script stampa lo stesso *«⭐ G3 ha acceso il caso dichiarato»*;
2. **`06-b33`: un giro completamente fallito certifica OGNI guasto.** Il confronto è
   un'**appartenenza** (`case " $R " in *" $CASO "*`), non un'uguaglianza d'insieme: se il client non
   regge la stretta di mano, tutti i casi vanno rossi, l'insieme contiene quello dichiarato, e il
   guasto risulta confermato. ⚠ Il giudice **sa** dire *«IL BANCO, NON IL PRODOTTO»*, e quel testo
   **non lo legge nessuno**;
3. **`06-b35`: il marcatore del registro precede la troncatura di UNA RIGA.** `registro-da` salva la
   lunghezza del registro, e la riga dopo `accendi` fa `: > "$LOG"`. ⇒ La regione dove stanno le
   righe della tela **viene saltata sistematicamente**: `tela_nuova_dal_palco == 0` è vero **gratis**
   (ed è la clausola che *«distingue il palco non ha obbedito da non gli è stato chiesto»*), e
   `non_spediti > 0` è **irraggiungibile** — cioè proprio l'attribuzione sbagliata che il banco
   dichiara di aver curato;
4. **`06-b34`: l'ancora del guasto B è nata scaduta**, e il ramo verde del caso 4b **è la firma della
   scena mancata**: se il ricambio avviene davvero, il contatore che il banco pretende `>= 1` vale
   **sempre 0** ⇒ il verde si ottiene **solo se la scena non è successa**. ⚠ La cura e il guasto che
   doveva provarla sono entrati **nello stesso commit**, e il guasto non è mai stato rilanciato.

#### ⛔⛔ E `06-b37`, che è un caso a sé: quattro falsi verdi, ciascuno sufficiente da solo

- **nessuna scena ha un limite INFERIORE sulla tela**: una tela 30 px più stretta della finestra —
  banda nera permanente, 30 colonne perse — lascia **12 combinazioni su 12 verdi**;
- **il ramo che attua «la voce spenta» non viene mai eseguito**: la spia sostituisce `chiedi_tela`
  **prima** di misurare, e la guardia vera sta **dentro** la funzione sostituita ⇒ il banco prova che
  *un booleano cambia valore*;
- **la «domanda vera» è un'identità algebrica**: il banco ricostruisce l'ingresso e lo confronta con
  l'uscita della funzione che quell'ingresso l'ha prodotto — scarto 0 in 93 righe su 126, per
  costruzione;
- ⛔⛔ **le coordinate: l'origine è cancellata per costruzione.** Lo scostamento fra dove l'immagine
  sta e dove la pagina crede che stia viene **sottratto** prima del confronto. ⇒ Il difetto del DeX —
  la tela dipinta 50 px a destra di dove `getBoundingClientRect()` la dichiara — **dà scarto 0 su 20
  punti su due motori**. È esattamente il difetto che quella scena nomina come propria ragione d'essere.

#### ⛔ Le misure di questa fase che CADONO, e vanno rifatte o riscritte

| dichiarazione | stato |
|---|---|
| §2 · `06-b33` «5 guasti: G2→C2 · G3→R1,R2 · G4→C6 · G5→C3,C4» | ⛔ **G3 non è certificato**; gli altri restano condizionati al rilievo 2 |
| §2 · `06-b35` «**5 guasti su 5 confermati**» | ⛔ **da rifare** dopo che la riga del marcatore è al suo posto |
| §2 · `06-b34` «6 casi · 2 guasti» | ⛔ **cade quasi tutta**: reggono il caso 1 e il caso 6. *«Un cambio di keymap distrugge e ricrea il dispositivo, e il tasto non resta giù»* **non è misurata** |
| §2 · `06-b36` «**23** casi · 19 guasti su 19» | ⛔ da riscrivere in **«20 casi su 23 certificati da 19 guasti»** |
| §2 · `06-b37` «7 scene», «20 punti · 2 523 colonne · 4 resize» | ⛔ **le scene eseguite sono 6**; il 2 523 viene da una scena mai girata sui due motori; **i 20 punti sono zeri per costruzione** |
| §2 · `06-b38` «49 accusate sul byte» | ⛔ **28 sul byte e sulla regola, 49 sull'esito**. ⭐ «19 mutazioni su 19» **regge** |
| §4.3-bis · «12 combinazioni su 12 verdi» | ⛔ **non conservata**: gli esiti nel deposito precedono di un giorno il codice di banco che l'avrebbe prodotta |
| §4.3 e §0 punto 7 · «le tre `[?]` di §6.1-bis, chiuse» | ⛔ **nessuna delle tre è chiusa**: lo zoom è assolto da una tolleranza di 2 px mentre lo scarto peggiore misurato è **esattamente 2**; il lato dispari è reso impossibile per costruzione e mai provocato; il mezzo pixel è osservato e non incrementa nessun conto |
| §0 punto 4 · «il ripiego su KWin dichiarato nel registro» | ⭐ **regge** (`06-b36` casi 1-2, ancora viva) |
| §0 punto 5 · «le coordinate in volo del secondo dopo `TELA(ADATTATA)`» | ⭐ **regge, ed è la parte più solida dei sei banchi** |
| §2 · `06-b34` «l'atteso lo calcola il prodotto» | ⛔ **non è implementato**: `06-b34-tabella.c` non è costruito né eseguito da nessuno script. ⭐ Ma l'accusa «la prova certifica se stessa» **cade lo stesso**, perché l'atteso vero è una **stringa di caratteri arbitrata da xkbcommon dentro la sessione** |

#### ⭐⭐ E la lettura che vale più dell'elenco

⚠ Dei ventidue rilievi, **uno solo** è un'ancora scaduta — la forma che §5.2 temeva e che tutti
cercavano. **Tutti gli altri hanno la stessa forma nuova, e nessuno l'aveva mai nominata:**

> ⛔ **la misura è buona, e il giudizio è staccato da lei.**

Un esito d'uscita catturato e non guardato (`b34`, `b35`, `b36`, `b38`), un atteso stampato e mai
confrontato (`b38`), un denominatore stampato e mai letto (`b38`), un contatore stampato con `inf`
invece che con `ko` (`b34`), un `case` di appartenenza invece che di uguaglianza (`b33`).

⇒ **La caccia della prossima volta non è alle ancore: è a ogni numero che un banco stampa e non
confronta.** 📖 `LEZIONI.md` §1.20.

### 5.6 · ⛔⭐ 21 agosto 2026 — **il registro mentiva sotto carico**, e ci sono voluti un attrezzo morto e un giro di banco per scoprirlo

*Nato dalla riparazione dei due attrezzi di `06-b35` chiesta da §7.1. ⭐ Il sintomo dichiarato era
«`06-b35-lancia.sh tempi` muore con `ValueError`». La causa non era nell'attrezzo.*

#### ⛔ Il difetto di PRODOTTO: tre `write()` per riga, e padre e figlio scrivono sullo stesso file

`src/registro.c` componeva ogni riga con **tre chiamate distinte** su uno `stderr` non bufferizzato
— intestazione, corpo, a-capo. ⚠ Il padre e il figlio appendono allo **stesso** registro: quando le
scritture si accavallano, un corpo finisce dopo l'a-capo altrui e nasce **una riga senza marca
temporale**.

`[M]` su un registro vero da 3,0 MB (28 035 righe): **23 righe orfane**, di cui **3 su 80** delle
«tela CHIESTA al produttore» — il **3,8 %** di una famiglia di righe su cui un attrezzo contava.

⭐ **E il controllo positivo della cura, `[M]` il 21 agosto**: sei processi che appendono allo stesso
registro, 800 righe ciascuno.

| | righe | orfane | «tela CHIESTA» trovate su 4 800 |
|---|---|---|---|
| ⛔ prima | 4 800 | **2 464** | **2 789** — cioè **il 42 % del conto era perduto** |
| ⭐ dopo | 4 800 | **0** | **4 800** |

⇒ **La cura**: la riga si compone in un buffer e si scrive con **una sola `write(2)`**. Sotto
`PIPE_BUF` (4096 byte) una `write` su un file in append è atomica rispetto alle altre; chi supera il
buffer viene **troncato con un segno**, perché *una riga tagliata si vede, una riga intrecciata no*.
⭐ In più `write(2)` è async-signal-safe, che `fprintf` non è, e il `fflush` non serve più.

⛔⛔ **E la lezione non è sul registro**: è che **lo strumento di diagnosi principale di questo
progetto si rompeva proprio sotto carico** — cioè esattamente nella scena in cui lo si interroga.
📖 `LEZIONI.md` §1.21.

#### ⛔ Un ottavo difetto del banco, e questo faceva peggio che rompere

`accendi` fa `: > "$LOG"` e **non azzera la marca** da cui gli attrezzi contano. `[M]` trovata una
marca da **825 758 byte** su un registro da **45 373**. ⚠ Non dava «zero sistematico» — dava **una
finestra arbitraria**, che è peggio: un conto plausibile e falso. L'unico esito superstite dichiara
`tela_nuova_dal_palco = 258` per un giro che cambia tela **9** volte.

#### ⛔ I numeri **D** di §4.8 non sono ricalcolabili — la finestra è perduta

⚠ Va scritto invece di essere aggirato: **4 ms · 39,5 · 44,5 · n=10** vennero da una finestra di
registro che **è stata cancellata**, e nessun file superstite la contiene. ⇒ Quel che si ricava oggi
dai registri che restano, **a macchina ferma**, con gli attrezzi riparati:

| | `[M]` 21 agosto, dagli attrezzi riparati |
|---|---|
| **la tela girata al palco** | **4,0 ms** (0-18, n=30) |
| Mutter | **35,0 ms** (29-45, n=20) |
| giro intero lato server, `ADATTATA` | **43,5 ms** (38-57, n=20) — contro i 44,5 scritti: **finestra vicina, non la stessa** |
| `NON_ORA` | **6,0 ms** (5-7, n=10) — ⛔ e prima stava sotto la stessa etichetta dell'`ADATTATA`, che è la forma E2 |

⭐ **E un numero del documento torna esatto**: §4.2, *«4 ms di mediana su 9 cambi (3-13)»*, esce
identico dagli attrezzi nuovi sullo stesso registro. ⇒ Non è tutto da rifare: è **quel** riquadro.

#### ⭐⭐ E un indizio NUOVO, a favore della tesi della contesa

`[M]` sul registro del **16 agosto**, con cinque banchi accesi: `NON_ORA` ha mediana **22 ms** e
**due casi a 3 000 ms** — la scadenza intera di §7.1. Sul **17**, a macchina ferma: **6 ms**, e
nessuno arriva al fondo. ⇒ ⭐ **La contesa muove davvero questa scena**, e il *«il verde vale sotto
carico CPU, non sotto contesa GPU»* di §7.1 ha adesso un secondo appoggio prima ancora che la scena
di contesa venga lanciata.

#### ⭐ E come sono stati certificati gli attrezzi riparati

Il calcolo a mano **riscritto in `awk`** — altro linguaggio, altro algoritmo — e confrontato
**campione per campione** su tre registri veri: **235 campioni, tutte e cinque le misure coincidono
esattamente**. ⚠ Una divergenza c'è stata, ed era **l'`awk` a sbagliare**: consumava una risposta
oltre il tetto. ⭐ Il controllo positivo di `06-b35-tempi.py` verifica anche che **l'attrezzo
vecchio, sullo stesso ingresso, muoia o sbagli** — altrimenti non controllerebbe niente.

⏳ **E il «5 guasti su 5» di §2 resta sospeso**: i cinque rilievi della revisione sul certificatore
sono chiusi (il giro sano come metro, la marca dopo l'accensione, lo stato d'uscita di
`costruisci.sh`, lo strumento che dichiara «cieco» invece di dire zero), ⛔ ma **il giro non è ancora
stato rifatto**. La scena di contesa (`06-b39-*`) è **pronta e non lanciata**: aspetta la finestra,
perché sposterebbe i millisecondi di tutti gli altri banchi accesi.

### 5.7 · ⭐⭐ 21 agosto 2026 — **la seconda porta del clic che muore, misurata**, e la cura che NON si può fare

*Banco nuovo `banchi/06-b33-risveglio.*`: collega `cattura.c` e `input.c` del **prodotto** e li chiama
da riga di comando, col testimone Wayland dentro la sessione di `provai6`. Tela 1264×800,
`MUTTER_DEBUG=eis,input`.*

| scena | `[M]` | carico |
|---|---|---|
| **S0** controllo zero, clic senza ricambi | il testimone lo vede: giù e su | 5,67 |
| **S1** tre `cattura_risveglia()`, mano alzata | ⭐ **3 risvegli → 3 ricambi** (delta `[1,1,1]`) con **0** `cattura_ridimensiona()` ⇒ **§7.1 è vera** | 1,86-2,19 |
| **S2** `BTN_LEFT` giù, **un** risveglio | ⛔ il rilascio **non arriva mai**, e **il clic fresco successivo nemmeno** ⇒ desktop morto ai clic. ⭐ La **tastiera** continua a funzionare | 1,58→10,68 |
| **S3** la stessa scena con `cattura_ridimensiona()` | **esito identico**: sono due porte sulla stessa stanza | 3,76 |
| **S4** si rompe, poi si stacca il cliente EIS | ⭐ **i clic tornano**, con lo **stesso `gnome-shell`** (pid verificato prima e dopo) | 1,39 |

#### ⭐ La catena `[R]` di §7.1-bis diventa `[M]` — e per un pelo non veniva smentita a torto

Dal giornale di Mutter, al millisecondo: `EIS: Updating viewports` **senza** nessun «Releasing
pressed buttons» accanto; poi `Dropping repeated press of button 0x110, count 2` e
`Dropping repeated release of button 0x110, count 1`. Il rilascio del pulsante tenuto **non compare
affatto**: `handle_button` lo ingoia prima che il posto lo veda.

⚠⭐ **E la precisazione vale quanto la misura**: la riga «Releasing pressed buttons» **c'è**, sei
volte — ma **al distacco**. ⛔ Una ricerca di assenza sull'intero giornale avrebbe **smentito §7.1-bis
a torto**. La lettura regge nella forma precisa: assente *accanto a `Updating viewports`*, presente
al disconnect.

#### ⛔ E l'ipotesi «la cura è più piccola di quanto sembri» è SMENTITA

*(Era del coordinatore: `button_count[]` è del **posto**, non del dispositivo, quindi un rilascio da
un dispositivo nuovo potrebbe far scendere il conto.)* ⛔ **No**: `handle_button`
(`meta-eis-client.c:612-621`) guarda `device->button_state`, che **sul dispositivo nuovo è pulito**,
e un rilascio da lì non arriva mai a `meta_seat_impl_notify_button_in_impl`. L'invariante è
`count = Σ bit vivi + trapelati`, e per consegnare un rilascio serve `count == 1` con un bit vivo,
che ha già incrementato ⇒ **irrecuperabile**. L'unica strada resta `drop_device()`.

#### Le quattro forme della cura, col prezzo — e la scelta

| | dove | prezzo |
|---|---|---|
| **A · prevenzione**: non ci si risveglia con qualcosa premuto | guardia in `figlio.c` + una finestra in `input.c/.h` | ⭐ **nessun trascinamento rotto**. ⚠ Su desktop fermo con un tasto giù la chiave non parte ⇒ **un client appena attaccato può restare bianco finché non si rilascia**. Si sana da sé, e la scena è rara: un trascinamento *muove* la scena |
| **B · si rilascia prima del risveglio** | una riga in `figlio.c` | ⛔ **taglia OGNI trascinamento su desktop fermo** — è la «cura ovvia vietata» di §7.1. Citata solo per il confronto |
| **C · recupero**: si riattacca il canale EIS quando il danno c'è | `input.c` (vede già `quanti_orfani > 0`) + `mutter_eis_riattacca()` in `mutter.c` | `[M]` funziona (S4). ⚠ Taglia il trascinamento in corso — **che però era già morto**. ⭐ Copre **le porte che non controlliamo**: `monitors-changed` (due giri), il cambio di keymap, e quel che Mutter aggiungerà |
| **D · si toglie il risveglio**: la chiave si rifà dall'ultimo fotogramma | `figlio.c` + `codificatore.c` | toglie la porta alla radice, ⛔ ma **non sostituisce** il risveglio: al login non c'è nessun fotogramma da rifare, e i 4,4 secondi tornano. E costa ~9,8 MB di copia a 2560×962 |

> ### 🔸 **Scelta del coordinatore: A + C** — derivata, non decisa dall'utente
>
> **A da sola non basta**, e la ragione è in §7.1-bis: le porte non sono una. `cattura_risveglia()`
> è quella che controlliamo; `monitors-changed` ne fa **due giri**, il cambio di keymap è un'altra, e
> la funzione che le apre tutte è entrata in **Mutter 48.5** — cioè è **nuova**, e ne arriveranno.
> ⇒ Una cura che copre solo la porta di casa nostra **scade al prossimo aggiornamento di GNOME**.
> ⚠ E il prezzo di **C** non è un prezzo: il trascinamento che taglia **era già morto** (S2).
> ⏳ **Il prezzo di A invece è visibile all'utente** — la finestra bianca finché non si rilascia — e
> i prezzi visibili li giudica lui: la riga sta qui perché la veda, non per essere già decisa.

⛔ **E un vincolo trovato misurando, che cambia il preventivo di C**: `input_apri()` **riusa il
descrittore** che `mutter.c` tiene da parte, e finché quello resta aperto Mutter non vede nessun
distacco e `drop_device()` non gira. ⇒ **La cura non sta dentro `input.c`.** `[R]`
`meta-remote-desktop-session.c:1943-1969`: `session->eis` si riusa e ogni `ConnectToEIS` aggiunge un
cliente, quindi sessione e palco non si toccano.

#### ⛔ Un fatto nuovo che tocca la certificazione di `06-b33`

Con la cura di `figlio.c` · `codificatore_di()`, `segna_orfani()` **non gira nemmeno nel prodotto sano** ⇒ **G3 non è
più certificabile in `06-b33`**: la sua scena vive adesso in `06-b33-risveglio.sh tenuto` (caso T1).
⏳ Quel banco **non ha ancora una certificazione con guasto innestato**, ed è il buco più grosso di
questa consegna — dichiarato dall'autore per primo.

#### ⭐ E i cinque rilievi della revisione su `06-b33`: chiusi

Il mondo si **legge** dal registro; R1/R2 sono pretese **solo col difetto vivo**; **T4 nuovo** — il
clic fresco, che è il danno vero e **non lo misurava nessuno**; R1 cerca il marcatore **dei
pulsanti**; C6 conta **nella finestra del ridimensionamento** (prima `rp >= 1` era soddisfatto dai
risvegli); giro sano e risanato **in tutt'e due i modi**; **uguaglianza dell'insieme** invece di
appartenenza; l'esito del giudice propagato. ⭐ Col certificatore nuovo, **G3 accende zero casi** — e
il vecchio avrebbe stampato *«⭐ G3 ha acceso R1»*.

⛔ **E cinque difetti del banco nuovo, dichiarati dall'autore**, di cui il più grave: il rilascio del
pulsante tenuto e quello del clic fresco **non si distinguono** per posizione rispetto al `RITELA` —
l'ordine con cui Wayland consegna `configure` e `button` è **una corsa**. Il confine giusto è il
**press fresco**. Prima della correzione, T4 usciva giallo su un giro sano.

### 5.8 · ⭐⭐ 21 agosto 2026, notte — **la contesa GPU misurata, e il verdetto RIFIUTATO dal banco stesso**

*La scena che §7.1 chiedeva da giorni, girata in una finestra dedicata con tutti gli altri banchi
fermi. `[M]` Impronte dei sorgenti nel rapporto; ferro: **Intel UHD 730 integrata**.*

#### La scena è vera — certificata prima di misurare

`[M]` Un codificatore da solo fa **382 fotogrammi/s** a 1920×1080; **cinque insieme, 184 ciascuno**
⇒ la contesa sull'iGPU **c'è**, ed è **2,08×**.

#### ⛔ Ma il prodotto non se n'è accorto, e il banco **si è rifiutato di dare il verdetto**

`[M]` 18 giri sotto contesa (carico **2,57**) contro 18 a riposo (**0,41**), nella stessa ora:

| | sotto contesa | a riposo |
|---|---|---|
| **rotti** | **0 su 18** | **0 su 18** |
| ritmo fotogrammi | 51,2 ms | 55,3 ms |
| ① girata→chiesta | 4,0 ms | 5,5 ms |
| ② **Mutter** | 28,0 (22-48), ⛔ **13 oltre il tetto** | 32,0 (18-47), ⛔ **17 oltre il tetto** |
| ③ palco→spedita | 4,0 | 4,0 |
| ④ `ADATTATA` | 37,0 | 40,0 |

⇒ **Niente si è mosso**: ogni latenza è uguale o **più veloce** sotto contesa. Il testimone (che
pretende una dilatazione ≥ 15 % del ritmo visto dal client) **non è scattato**, e
`06-b41-verdetto.py` **ha rifiutato il verdetto**. ⭐ *«Non scrivo "0/18 sotto contesa GPU": sarebbe
l'etichetta senza la cosa»* — ed è esattamente il motivo per cui quel testimone è stato scritto.

⭐ **E si sa perché**: a riposo il ritmo è 55 ms ≈ **18 fotogrammi/s**, e lo detta **la scena** (un
terminale che scrive l'ora ogni 50 ms), non il codificatore. A 18/s di 1280×800 il prodotto chiede
all'iGPU circa **un cinquantesimo** di quel che chiedono i cinque carichi. ⇒ **La contesa è vera
sull'iGPU, ma in questa scena il prodotto l'iGPU quasi non lo usa.**

#### ⛔ Che cosa cambia per §7.1: **una causa è ESCLUSA con la misura**

Il **4/18 del 16 agosto** resta **non riprodotto**, ⛔ e adesso si sa che **non è la sola contesa
sull'iGPU**. Non si promuove a «curato», e non si promuove a «spiegato».

⭐ **E dove il segnale c'è, indica un altro imputato**: la latenza ② ha **13 e 17 campioni oltre il
tetto** su ~57 in **tutt'e due** le metà — cioè un quarto delle richieste al produttore **senza
risposta da Mutter entro un secondo**. È la stessa firma del 16 agosto (`NON_ORA` mediana 22 ms e due
casi a 3 000). ⇒ ⏳ **La prossima ipotesi è la contesa sul COMPOSITORE e su PipeWire — cinque
sessioni — non sull'iGPU.** Quella scena non è stata costruita.

#### ⛔ E col metro sano, il «5 guasti su 5» non regge

`[M]` Certificatore rifatto sotto contesa, carico 2,78, col **giro sano come metro** e la marca dopo
l'accensione:

```
SANO   adattate=10 non_ora=0 ms_mediano=47,45 fotogrammi=169 tela_nuova=10 non_spediti=0
G1 · G2 · G5   ATTESO-CONFERMATO      (regola sul sano = False)
G3  ⛔ ATTESO-SMENTITO      tela_nuova_dal_palco = 1, e la regola ne pretende 0
G4  ⛔ NON-DISCRIMINANTE    la regola è vera ANCHE sul sano
⇒ CONFERMATI 3 · SMENTITI 1 · NON DISCRIMINANTI 1
```

- **G3** è il difetto previsto: la terza clausola era vera **gratis** perché la marca scaduta
  rendeva vuota la finestra del registro. ✅ **Chiuso il 22 agosto, e la strada era una sola**: vedi
  §5.9;
- **G4**: §5.2 lo diceva già a parole («atteso verde per costruzione»); ⭐ adesso **lo dice il banco**,
  invece di contarlo fra i confermati;
- ⭐ **e G1 distingue ancora** col carico acceso (`regola sul sano = False`), che era il dubbio del
  coordinatore. ⚠ Col limite dichiarato: **questa** contesa al prodotto non arriva.

#### ⭐ E il rimedio a `registro.c` è verificato da un terzo

`[M]` sul giro sotto contesa: **18 righe senza marca su 12 882**, e **tutte e 18 sono di `libopus`**,
cioè di ffmpeg — **zero righe nostre spezzate**. Contro **23 su 28 035** (di cui 3 diventavano eventi)
sul registro del 16 col codice vecchio.

⛔ **E ha smascherato un difetto dell'attrezzo che conta**: chiamava quel numero *«intestazione persa
nell'intreccio»* — una **causa**, su un attrezzo che vede solo un **effetto**. ⇒ Avrebbe accusato
`registro.c` di un intreccio che non c'è più: **il rosso all'imputato sbagliato, dentro l'attrezzo
che dovrebbe smascherarlo.** Adesso separa «righe senza marca» da «**eventi** che ne arrivano», che è
l'unico numero che sposta una latenza.

#### ⛔ E il difetto peggiore della finestra è dell'autore, che l'ha dichiarato per primo

`misura` copiava i file JSON **del 16 agosto** come se fossero il giro appena fatto: sei giri nati da
**tre file di cinque giorni prima**, con dentro un ritmo perfettamente plausibile. ⭐ È stato visto
**solo** perché le due metà erano identiche **byte per byte**. ⇒ Curato: si cancella prima, si
raccoglie solo quel che è **più nuovo di una marca presa un istante prima**, e **zero giri raccolti
= ci si ferma**.

### 5.9 · ⭐⭐ 22 agosto 2026 — **G3 chiuso, e i numeri «non ricalcolabili» rifatti da capo**

#### ⛔ La terza clausola di G3 non era sbagliata di uno: **era irraggiungibile da un giro che misura**

`tela_nuova_dal_palco == 0` poteva diventare vero **solo se lo strumento non aveva guardato** — un
giro senza fotogrammi non si misura affatto (esce 5), e un giro con almeno un fotogramma ha
**sempre** la riga di nascita. ⇒ ⛔ **Era la macchina del falso verde scritta dentro l'atteso**, e
c'era **dal primo giorno del banco**: il difetto della marca scaduta (§5.6) non la creava, la
**realizzava**.

`[M]` La riga «TELA NUOVA DAL PALCO» del giro di G3 è la **riconciliazione di nascita**, e **precede**
il primo `ADATTA_TELA` — riprodotto due volte, a otto ore e a carichi diversi: **476 ms prima** il
21 agosto (carico 2,78), **461 ms prima** il 22 (carico ~0,7). Il figlio nasce al ripiego
1920×1080 e il palco **nasce** — non si ridimensiona — a 1280×800.

⭐ **E «completare il guasto» è ESCLUSO con la prova, non scartato a gusto**: quella riga non passa da
`cattura_ridimensiona()`, quindi spegnerla vorrebbe dire un secondo guasto sotto un nome solo (che
l'innestatore **vieta**), nel punto che è già di G5, e toglierebbe a G3 la scena. ⇒ **Le due strade
non portavano a lavori diversi: una delle due non esisteva.**

⭐⭐ **E la distinzione che la clausola serve REGGE**, che era la domanda vera: senza di essa G3 e G1
avrebbero la **stessa** regola, e il controllo positivo direbbe che il banco vede *un* problema
invece di *quel* problema. `[M]` stessa ora: **G1 = 8** (il palco obbedisce, la risposta si perde) ·
**G3 = 1** (al palco non arriva niente) · **SANO = 10**.

⭐ **E il `== 1` cade dalla parte giusta**: uno strumento cieco conta 0 ⇒ regola **falsa** ⇒ **rosso**.
Il vecchio `== 0` cadeva dalla parte del verde. ⇒ **Ogni modo di fallire della regola nuova è rosso**
— ed è la forma che `LEZIONI.md` §1.20 chiede.

#### ⭐ Il numero vero: **4 confermati · 0 smentiti · 1 non discriminante**

`[M]` 22 agosto, carico **0,49-1,12** (⚠ **la contesa non c'è più**: il 2,78 di ieri notte era in
buona parte del banco stesso — va letto come *«a macchina quasi ferma»*), sorgenti di prodotto
**identici byte per byte** al deposito.

#### ⭐⭐ E i numeri **D** di §4.8, dichiarati «non ricalcolabili», sono stati **RIFATTI**

⛔ Non ricostruiti dai file vecchi — *quelli sono la trappola da cui nasce il problema* — ma presi da
**tre giri nuovi** sul codice sano, con gli attrezzi riparati e il loro controllo positivo superato
prima. Carico 0,30-0,48.

| | §4.8 (17 ago) | §5.6 (dai superstiti) | ⭐ **giro nuovo, 22 ago** |
|---|---|---|---|
| ① **la tela girata al palco** | 4 ms (n=10) | 4,0 (n=30) | **6,0 ms** (0-21, **n=27**) |
| ② Mutter | 39,5 ms | 35,0 (n=20) | **32,0 ms** (15-49, n=27) |
| ③ palco → spedita | — | — | **4,0 ms** (3-39, n=28) |
| ④ giro intero, `ADATTATA` | 44,5 · 10/10 | 43,5 (n=20) | **42,0 ms** (25-59, n=27) · **27/27** |
| `SESSIONE` → 1° fotogramma | 25 ms · 203-220 da montare | — | **14 e 26 ms** · **141 ms** da montare |
| scartati · fuori misura | 0 · 0 | — | **0 · 0** (30/30 `ADATTATA`, 9/9 primo alla misura nuova = chiave) |

⇒ ⭐ **Le tre latenze del riquadro D si riconfermano tutte entro pochi millisecondi, con n quasi
triplo.** Il buco di §4.8 si chiude: quel riquadro non è più un numero perduto.

⭐ **E la cura di `registro.c` regge anche qui**: 3 righe senza marca su 3 242, **nessuna nostra**.

#### ⛔ E il 22 agosto sera il numero è sceso ancora: **3, non 4** — e l'ha abbassato chi l'aveva scritto

*Chiusi anche i due rilievi della revisione (`R5` il sentinella, `R14` l'attrezzo che butta i conti),
e con la colonna nuova è saltato fuori un fatto che prima non si vedeva.*

⛔ **G5 è intermittente**: la sua regola vuole `non_spediti > 0`, e quel numero vale **1** — un solo
fotogramma scartato. Nel terzo giro è uscito **0** con lo strumento **non** cieco (67 righe della tela
viste) ⇒ `NON MISURATO`. ⚠ Prima sarebbe **sparito da tutte e tre le colonne senza una riga che lo
dicesse**: è la ragione per cui esiste la **quarta** colonna e la riconciliazione
`CONFERMATI + SMENTITI + ND + NON GIUDICATI = guasti chiesti`.

| | 05:44 | 06:16 | 06:21, scena verificata **singola** |
|---|---|---|---|
| G1 · G2 · G3 | confermati | confermati | **confermati** |
| G4 | non discriminante | non discriminante | **non discriminante** |
| G5 | confermato | confermato | ⛔ **NON MISURATO** |
| ⇒ | 4 · 0 · 1 · 0 | 4 · 0 · 1 · 0 | **3 · 0 · 1 · 1** |

⭐ *«Non scrivo 4: sarebbe scegliere i due giri che mi piacciono.»*

> 🔸 **Decisione del coordinatore su G5: si allunga il giro, NON si riscrive l'atteso.** L'atteso non
> è sbagliato — è **la scena a essere sotto-potenza**: una scena che produce *esattamente un* evento
> non prova niente in modo ripetibile. ⛔ Riscrivere l'atteso sarebbe **adattare il metro al
> risultato**, che è la strada che questa notte ha insegnato a non prendere.
>
> ### ⭐⭐ E allungando il giro è venuto fuori che **l'evento non si moltiplica**, e il perché vale più del guasto
>
> `[M]` Sei giri, dalla scena corta a una **cinque volte più lunga**: **799 fotogrammi, tutti
> inammissibili, e un solo annuncio**. Cinque volte l'attività nel registro, **lo stesso identico 1**.
>
> ⭐ **E si sa perché, dal sorgente**: la riga sta dietro un fondo che si riarma **solo quando cambia
> la coppia (tela in vigore, misura del fotogramma)** — e sotto quel guasto **non cambia mai**. Primo
> fotogramma: la riga esce. Dal secondo al 799°: identici, fondo già armato, **silenzio**. ⇒ È **una
> volta per sessione, per costruzione**.
>
> ⛔⛔ **Quindi il numero non è quel che il suo nome promette**: `non_spediti` non è *«quanti
> fotogrammi non sono partiti»*, è *«quanti annunci distinti di disaccordo»*. Il nome dice 799, il
> valore è **1** — la forma **E2**, e ⚠ **non l'aveva vista nessuno perché 1 è un numero che sembra
> sano**.
>
> ⛔ **E il conto vero il prodotto ce l'ha e non lo dice**: `w->video_saltati` si incrementa a ogni
> fotogramma, e `wt_video_conti()` saprebbe leggerlo — ⛔ ma **quella funzione non la chiama nessuno**
> (verificato: zero chiamanti in tutto `src/`). ⇒ È `LEZIONI.md` §1.20 **dentro il prodotto**: un
> contatore che nessuno confronta.
>
> 🔸 **Decisione: si fa uscire il conto vero.** Le altre due strade sono state scartate con la
> ragione: contare un'altra riga darebbe il numero giusto nel giro buono ⛔ **e un falso rosso** nel
> giro in cui il palco non parte; lasciare com'è costa zero ⛔ e lascia in giro **un nome che promette
> una cosa e ne dice un'altra**.
>
> ### ✅ **FATTO il 22 agosto — sedici righe di codice, e il fattore è 254**
>
> `wt_video_conti()` ha finalmente un chiamante, **accanto a quello dell'audio**. ⭐ E la scoperta che
> vale più della cura sta nel commento che l'accompagna: la riga dell'audio fu scritta il **17
> agosto** per la funzione **gemella**, **con queste stesse parole**. ⇒ La cura era stata applicata a
> **uno dei due gemelli**, e nessuno aveva guardato l'altro. 📖 `LEZIONI.md` §1.25.
>
> `[M]` Stessa scena, due binari, il guasto innestato solo nell'albero di costruzione:
>
> | | consegnati | **NON SPEDITI** | **ANNUNCI** |
> |---|---|---|---|
> | sano | 1 016 | **0** | **0** |
> | col guasto | 0 | **1 017** | **4** |
>
> ⇒ ⛔ **1 017 contro 4: un fattore 254.** Prima, il solo numero leggibile era quello degli annunci —
> e lo si chiamava «non spediti».
>
> ⭐ **E l'atteso scritto prima era sbagliato, ed è rimasto scritto**: diceva «annunci = 1», come nel
> giro che aveva aperto il caso. Ne sono usciti **4**, ed è giusto: il fondo si riarma a ogni coppia
> (tela, misura) nuova, e quella scena la cambia tre volte. ⇒ **Il numero degli annunci segue le
> misure distinte, non i fotogrammi** — che è esattamente la ragione per cui non poteva fare da conto.
>
> ⚠ Dichiarato e non fatto: «non spediti» somma **tre** cause. Spezzarlo sarebbe una seconda cura —
> ⭐ ma il nome **non mente**: sono davvero i fotogrammi che non sono partiti.

#### ⛔⛔ E la scena si raddoppiava in silenzio — **per la seconda volta stanotte, la stessa forma**

`pkill -f 'banco-P6-scena'` uccide **il terminale**, non il ciclo che scrive l'ora: il titolo **non è
nella riga di comando** del processo che sopravvive. ⇒ Ogni `scena-via` lasciava un ciclo vivo e ogni
`scena` ne aggiungeva uno — `[M]` **due cicli** dopo un solo spegni/riaccendi. ⚠ Su un banco che
misura millisecondi, **una scena doppia non è la scena dichiarata**.

⭐ Curato con la guardia giusta: `scena-via` pretende **zero** superstiti e `scena` pretende
**esattamente uno** — la guardia vecchia era `> 0`, **che lasciava passare il due**. E i numeri D
erano su **un** ciclo: verificato, non sperato.

⚠ **La stessa forma è stata trovata indipendentemente in `06-b42`**: è un modo di sbagliare del
deposito, non di un banco.

#### ⭐ E i numeri D **non cambiano** dopo la cura dell'accoppiamento

① accoppia ora **per chiave**; ④ resta per ordine, ⭐ **ed è una scelta dichiarata**: la chiave non
esiste (la riga della risposta porta la tela *in vigore*, che su un `NON_ORA` è quella **vecchia**, e
accoppiare per misura butterebbe via proprio i `NON_ORA` che i guasti cercano). ⇒ La protezione è a
monte. `[M]` Ricalcolati sugli stessi registri: **identici campione per campione**, e si sa **perché**
— in quel giro `GIRATA 27 = CHIESTA 27`, zero spaiate, quindi chiave e ordine coincidevano.
⛔ **Ma è una proprietà di quella scena, non del codice vecchio**: gli altri due giri non hanno quella
garanzia.

#### ⏳ E due cose dichiarate invece che curate

- ⚠ **il valore «1» è legato alla scena, e nessuno l'aveva detto**: esiste perché il figlio nasce al
  ripiego 1920×1080 mentre la sessione del giro è 1280×800. Una scena che aprisse **proprio** a
  1920×1080 non avrebbe la riga di nascita, e l'atteso non varrebbe. ⇒ Adesso l'atteso **nomina il
  giro e la ragione**, invece di portare un numero nudo;
- ⚠ `parlantina-c-e` dà un **falso rosso sul primo giro dopo un `accendi`**: legge il registro intero,
  che `accendi` azzera. ⛔ Falso rosso, quindi direzione sicura — **dichiarato, non curato**.

### 5.10 · ⛔⛔⭐ 22 agosto — **il secondo di grazia contro il prodotto, e l'arbitro da solo NON vede l'indulgenza**

*I giri 6 e 7 di `06-b38-tela.sh`, mai puntati contro il server. `[M]` porta 7721, **quattro giri
interi 7/7 verdi**, carichi 1,16 · 1,51 · 1,57 · 2,58.*

| | giro 6 — **oltre** | giro 7 — **dentro** |
|---|---|---|
| `dt` registrato | **1 501 ms** | **251 ms** |
| il server | `CONGEDO 0x0b ERRORE_PROTOCOLLO` | ⭐ la sessione **regge** |
| l'arbitro | «oltre il secondo — e il server ha **congedato**» | ⭐ «**NON è giudicabile** da questa registrazione» |
| ⭐ **dove è finito il puntatore** | **da nessuna parte** | **(799,599)**, l'ultimo pixel della tela nuova |
| il filo | — | **`input = 1`** nel fotogramma (§6.2) |

⭐ La coordinata **non è scelta a mano**: si manda l'ultimo pixel della tela *precedente*, che **deve**
saturare esattamente su `(799,599)`.

#### ⭐ L'asimmetria degli orologi non è più un ragionamento: è una tabella

> **9 coppie su 9: il server misura di più, fra +11 e +25 ms** (LAN, carico 1,0-1,6).

⇒ Un caso «dentro» a 0,99 s sarebbe stato **1,01 s per il server**: rosso su un prodotto che ha
ragione. ⛔ La tabella sta nel banco **col divieto di usarla per avvicinarsi al confine**.

#### ⛔⛔ «L'arbitro dice conforme» non è una misura

Con un **server guasto apposta** (`TELA_GRAZIA` 1 000 → **60 000 ms**): il puntatore a 1 501 ms viene
**iniettato**, e ⛔⛔ **il validatore esce 0 e dichiara CONFORME** — onestamente, perché §7.1 lo fa
concludere **solo** se il server parla ancora sul canale di controllo, e **un server indulgente che
tace non gliene dà l'occasione**. ⭐ Il banco invece esce **1 su cinque righe rosse**, e il settimo
giro contro lo stesso server guasto resta **verde**, com'è giusto: **specifico, non paranoico**.

⇒ È la forma più forte di *«conforme non è funziona»* che questa fase abbia prodotto.

⛔ **E un difetto del banco della specie peggiore**: confrontava il puntatore con l'**ultimo**
`TELA(ADATTATA)` del file invece che con **quello che lo precede** ⇒ `dt` **negativo**, che cade sotto
il secondo, cioè nel ramo «non giudicabile». **Un puntatore oltre la grazia sarebbe stato dichiarato
dentro.** L'ha trovato il controllo positivo.

### 5.11 · ⛔⛔⭐ 22 agosto — **la «firma di Mutter» di §5.8 era un artefatto della scena**

*Il seguito della contesa: costruita la scena a cinque sessioni, ⛔ e la premessa è caduta prima della
finestra.*

`[M]` **18 giri incatenati, ZERO contesa**, carico 1,57 → 2,91: la latenza ② dà **17 campioni oltre il
tetto su 62**. ⛔ §5.8 ne aveva **13 e 17 su ~57** e li leggeva come *«un quarto delle richieste senza
risposta da Mutter entro un secondo, la stessa firma del 16 agosto»*.

⭐ **Il meccanismo, e chiude il caso**: ② accoppia **per misura chiesta**; la prima di due richieste
incatenate riceve `NON_ORA` (§7.1), quindi **il produttore non consegna mai una tela a quella
misura**, e la richiesta si accoppia con quella di un giro **successivo** — oltre il secondo. **Una
per giro.** ⭐ Controprova su 5 giri: **15 richieste, esattamente 5 spaiate ed esattamente 5
`NON_ORA`**. ⇒ Ed è anche il motivo per cui §5.8 la trovava **identica nelle due metà**: è quel che la
scena fa **per costruzione**.

#### ⭐⭐ E gli stessi 18 giri quieti danno **0 rotti su 18 — a carico PIÙ ALTO del 16 agosto**

Carico **1,57-2,91** contro lo **0,90** che §4.8 registra per il giorno del 4/18. ⇒ Si misura
«quieto» **sopra** il carico del giorno che produsse il difetto, e si ottiene **0/18**.

#### ⭐ E un contendente rende il compositore **più veloce**, non più lento

`[M]` sonda indipendente sul ciclo principale di Mutter, con client attaccato in tutt'e due i casi:
mediana **1,47 → 0,64 ms (0,44×)**, p95 **5,56 → 2,59**. ⇒ La certificazione a cinque sessioni
**fallirebbe**, e il banco rifiuterebbe il verdetto — come ha già fatto quello della GPU.

⇒ 🔸 **Scelta del coordinatore: la finestra a cinque sessioni NON si spende.** Su raccomandazione
avversariale dell'autore stesso: il 4/18 è una differenza di **esito**, e `NON_ORA` è **una corsa con
`cattura_ridimensiona()`** — la finestra in cui si ribalta si misura in **millisecondi, non in
carico**, e i 18 giri erano **tutti a 30 ms**. ⏳ La strada che resta è **setacciare l'intervallo**
(10-60 ms, molti giri per punto): costa la CPU di una sessione sola e **non disturba nessuno**.

⭐ **E la sonda del compositore è certificata**: `SIGSTOP` di 300 ms a `gnome-shell` ⇒ la sonda
registra **290,6 ms**. Prova che guarda **il compositore** e non altro.

### 5.12 · ⭐⭐ 22 agosto — **il colore dentro la sessione: sono gli STESSI PIXEL, byte per byte**

*L'ultimo anello che mancava al colore: non dal flusso al vetro, ma **dal desktop al vetro**.*

⭐⭐ **Zero canali diversi su 2 704 104**, confronto **byte per byte** fra quel che l'applicazione
dipinge e quel che il codificatore riceve.

| punto | che cosa aggiunge | medio | peggiore |
|---|---|---|---|
| dipinto → **catturato** | la cattura di Mutter | **0,000** | ⭐ **0,000** |
| dipinto → **flusso** | + conversione nostra + H.264 QP 26 + 4:2:0 | 0,334 | 3,005 |
| dipinto → **vetro** | + decodificatore hardware di Firefox | 0,342 | 2,981 |

⭐ `vetro − flusso ≤ 0,03`: **il decodificatore del browser non aggiunge nulla di misurabile** —
conferma indipendente dello 0,51 di §1.13-ter, presa **dall'altro capo**. E il residuo di ~3 livelli
non è nelle luci: **17 canali su 1 029 oltre 2,0, tutti sulle rampe di croma**, cioè il giro
RGB→YUV 4:2:0→RGB.

#### ⭐ E le tre trasformazioni sospettate, separate una per una

| | esito |
|---|---|
| **Night Light** a 1700 K, verificato attivo dal demone | ⭐ `[M]` **non entra**: 0 byte diversi |
| **effetti dello shell** | ⛔ **entrano eccome**: la *lente* dà **255 livelli**, e ⛔⛔ **la panoramica delle attività** ne dà **221,75** — un banco meno attento l'avrebbe messa in tabella come «difetto di colore» |
| **profilo ICC del compositore** | ⏳ `[?]` **non misurato**: `colord` non parte su questa macchina, quindi non c'è niente da accendere. `[R]` viaggia sulla stessa strada di Night Light, ma è **deduzione** |

⭐⭐ **E lo zero di Night Light vale perché la lente è passata**: senza quel controllo, uno zero sarebbe
indistinguibile da un banco cieco.

⭐ **E per il prodotto la questione è chiusa strutturalmente**: `sessione.c` toglie `--virtual-monitor`
e l'unico monitor della sessione è quello che monta la nostra cattura ⇒ non c'è scanout, non c'è
monitor fisico, non c'è dispositivo colore: **lo «schermo» della sessione È lo stage composto, e lo
stage composto è quel che catturiamo.**

⛔ **E il difetto del banco, dichiarato per primo**: il controllo positivo della lente **non si
accendeva** — un `echo` con apici dentro rompeva il comando remoto e **nessun `gsettings` girava**. Il
giro ha misurato «nessuna differenza» **credendo di avere l'ingranditore acceso**, cioè esattamente la
cecità che quel controllo doveva escludere. ⇒ Adesso il banco **muore** se la rilettura dal dconf non
dice quel che ha chiesto.

### 5.13 · ⭐⭐ 22 agosto — **il tetto del posto è 30 secondi, non 75** — e la frase di §5.3 sulla scheda congelata è falsa

*La `[?]` che mordeva tutti i giorni: «il posto della sessione è uno, e quello di prima resta
attaccato per una ventina di secondi» era folklore. `[M]` porta 7801, `provar7`, GNOME headless vero,
carico 0,23-1,40.*

| il client se ne va… | posto lasciato | un altro client entra |
|---|---|---|
| **congedo pulito** | ⭐ **5 ms** | subito |
| connessione chiusa senza congedo | **7 ms** | subito |
| **ammazzato** (presa chiusa) ×4 | 30,0 · 30,5 · 30,0 · **31,1 s** | idem |
| **congelato** (buco nero) ×3 | 31,1 · 31,2 · 30,0 s | idem |
| ⛔ **vivo sul filo, muto su RCP** | ⛔ **mai** | ⛔ **26 bussate su 26 respinte in 745 s** |

**Peggiore misurato: 31,2 s.** ⛔ E morire «male» non cambia niente: presa chiusa (con ICMP) e presa
muta danno gli stessi numeri — **ngtcp2 non reagisce all'ICMP**.

#### ⛔⛔ E la frase di `SPECIFICHE.md` §5.3 sulla scheda congelata è **falsa sul filo**

*«Una scheda congelata tace, quindi si stacca»* — ⛔ no: il server accende un **PING ogni 10 s**, lo
stack QUIC del client **risponde da solo** senza che la pagina esista, e ogni risposta rinnova la
vita. ⇒ **Il posto non si libera mai.** `[M]` 26 su 26 in 745 s. ⚠ Il prodotto conta i **pacchetti**,
non i byte di RCP — ed è una scelta giusta e documentata, ⛔ ma **non è quel che §5.3 racconta**.

#### ⭐ La riga per chi scrive banchi — è la cosa che serviva a tutti

> ⛔ **Dopo che un client se n'è andato male, prima di 35 secondi non riprovare.**
> ⛔⛔ **E se il suo processo è ancora vivo, 35 s non bastano: il posto resta occupato fino a mezz'ora.**
> Si verifica con `pgrep`, non con `pkill`.
> ⭐ **Ma quasi mai serve aspettare**: se il server è tuo, **riaccendilo** — i posti stanno nella
> memoria del processo, la sessione grafica vive fuori: `[M]` il primo attacco dopo un riavvio arriva
> a `SESSIONE` in **1,03 s**. ⭐ E se il client è tuo, **fallo congedare**: **5-7 ms**.

#### ⛔ E le strade sono DUE, con lo stesso numero — è il meccanismo dietro i falsi rossi

In 4 distacchi su 7 il posto l'ha lasciato **l'orologio del silenzio**; negli altri 3 la **morte della
connessione QUIC** (30,00 s esatti). ⚠ **Quale arrivi prima è testa o croce**, e lasciano **righe di
registro e stati diversi**. ⇒ Un banco che aspetta la riga «staccato per silenzio» per sapere che il
posto è libero **è rosso una volta su due**.

⭐ **E il controllo positivo, senza cui i 30 s non varrebbero niente**: con l'orologio dell'inattività
accorciato a 25 s lo stesso caso ha lasciato il posto a **19,8 s** con un congedo diverso ⇒ il banco
**sa vedere** un rilascio a un'ora diversa da 30.

⚠ **E quel che manca, dichiarato dall'autore**: nessun browser. L'ipotesi che lascia in eredità è che
i «~75 s» fossero **~45 s di Firefox che non muore + 30 s del prodotto**. Si chiude in un minuto, con
un browser in mano.

#### ⏳ Quattro cose del prodotto trovate per strada, non curate

| | |
|---|---|
| ⛔ `2 = RIPRESA` **non esce mai** | il byte è una **costante 1** nell'unico punto che costruisce il messaggio. `[M]` 12 riattacchi sullo stesso figlio: **stato 1, sempre**. È la forma **E1** ⇒ chi scrive banchi **non può** usarlo per sapere se ha un desktop nuovo |
| ⛔ le **due strade** con lo stesso numero | sopra: due righe e due stati sotto lo stesso fatto, in gara |
| ⛔ il **client vivo tiene il posto** | fino alla mezz'ora dell'inattività — misurato ≥ 745 s |
| ⏳ `[?]` **il desktop immortale** | `presenza_segna()` è chiamata **da un posto solo**, quello che riceve l'input ⇒ chi si attacca e **non tocca niente** non entra fra i presenti e **l'orologio dell'abbandono non parte**. Se è vero, ogni banco che si attacca senza digitare lascia un desktop da **477 MB** che non muore mai — ed è così che una macchina con otto banchi si riempie. ⛔ **È una lettura del codice, non una misura**: il giro che doveva provarla è saltato |

### 5.14 · ⛔ 22 agosto — **un'etichetta sbagliata ha fatto credere all'utente che una funzione tolta fosse tornata**

> *«Avevo già detto che il ridimensionamento dinamico era fuori dal progetto, e tu lo hai
> reintrodotto.»* — l'utente, leggendo un rapporto del coordinatore.

⭐ **Nel prodotto non è tornato**, verificato: il codice lo dichiara uscito in **otto punti**
(*«uscito»*, *«il fondo non c'è più»*, *«qui non parte»*), e il pezzo è stato **tolto**, non messo
dietro un interruttore. L'unica cosa che accade ridimensionando la finestra è che **l'immagine si
riscala**, che è il comportamento approvato.

⛔ **Ma il NOME è tornato**, e nei rapporti al posto peggiore: la prima delle quattro latenze di §5.6
e §5.9 era etichettata **«ridimensionamento a caldo»** e misura tutt'altro — il tempo fra la
richiesta **girata al palco** e la richiesta **arrivata al produttore**, sul cammino di `ADATTA_TELA`,
cioè quello che ogni client percorre **attaccandosi**. Una cosa che c'è, e deve esserci.

⇒ Chi leggeva *«ridimensionamento a caldo: 6 ms»* concludeva che la funzione fosse tornata.

⚠ **Ed è la stessa forma di difetto che questa notte ha corretto sei volte nei banchi** — *un nome
che promette una cosa e ne dice un'altra* — commessa dal coordinatore **nei documenti**. ⛔ Che sia
un'etichetta e non del codice non la rende meno grave: **i documenti sono quel che resta**, e un
nome sbagliato in una tabella di misure sopravvive a tutti noi.

⭐ **E a trovarla è stato l'utente leggendo, non un banco.** Nessuno dei controlli automatici poteva
vederla: nessun banco confronta il **nome** di una misura con quel che la misura fa.

⇒ **Corretta ovunque**: nel banco (`06-b35-tempi.py`, col racconto accanto) e nelle tre tabelle di
questo documento. La misura si chiama adesso **«la tela girata al palco»**.

#### ⭐ E il vocabolario, dato dall'utente

> *«Si chiama **re-scaling**.»*

⇒ **Sono due cose diverse e vanno chiamate con due nomi diversi**, sempre:

| | |
|---|---|
| ⛔ **ridimensionamento dinamico** | il desktop remoto **cambia misura** mentre l'utente trascina il bordo. **Fuori dal progetto dal 17 agosto**, e non si riapre |
| ⭐ **re-scaling** | l'immagine si **riscala** dentro la finestra, e **le finestre del desktop non si muovono**. È quel che il prodotto fa, ed è approvato |

⚠ Chiunque scriva «ridimensionamento» senza specificare quale dei due **sta per rifare questo
errore**.

### 5.15 · ⛔⛔⭐ 22 agosto 2026 — **`06-b37` rifatto: i quattro falsi verdi curati, e cinque guasti che li accendono**

*Il banco della sottofase 6.5 era l'unico dei sei **senza nessun guasto innestato** (§5.5). ⇒ Adesso
ce l'ha: `banchi/06-b37-guasti.py` + `banchi/06-b37-guasti.sh`, **7 casi su 7 su Chrome 151 e 7 su 7
su Firefox 140esr — 14 su 14** — ogni guasto rosso **nel caso dichiarato prima**, e la stessa scena
verde sul prodotto. Carico della macchina durante le certificazioni: `load average` **0,34 → 2,10**,
un giro intero **9 min 52 s** (Chrome) e **12 min 40 s** (Firefox).*

#### ⭐ I cinque guasti, e che cosa accendono

| | il guasto, in una copia di `src/pagina.html` | la scena che lo accusa | il falso verde che smaschera |
|---|---|---|---|
| **G1** | la tela chiesta è **30 px più stretta** della finestra | `numeri` A5 · `sfora` · `pixel` X1-bis | ⛔ nessuna scena aveva un **limite inferiore**: 12 combinazioni su 12 restavano verdi |
| **G2** | la guardia `if (tela_spenta)` è **aggirata** | `voce` **V5** | ⛔ la spia **sostituiva** `chiedi_tela`, e la guardia sta **dentro** la funzione sostituita |
| **G3** | `misura_vista()` torna al **`Math.round`** di prima della cura | `sfora` a dpr 1,5 (**«TAGLIATO 979 px su 980»**) | ⛔ A6 era un'**identità**: la «verità esterna» si semplificava in `round(cw·dpr)`, cioè nello stesso arrotondamento del guasto ⇒ **il difetto vero che questa fase ha curato passava sotto A6 senza toccarlo** |
| **G4** | l'immagine è dipinta **50 px fuori posto** nel buffer, e `dipinta.x` dice ancora 0 | `coordinate` **C0** | ⛔ l'origine era **sottratta per costruzione** |
| **G5** | la **parità** di `tela_da_chiedere()` è tolta | `numeri` A3 (63 tele su 63) | ⛔ il lato dispari era impossibile **per costruzione** e non veniva mai provocato |

#### ⭐⭐ E la controprova di G4 sta dentro il banco, per sempre

`06-b37-coordinate.py` misura **ogni punto due volte** — con l'origine vera e con la formula
vecchia — e stampa i due scarti accanto. `[M]` con G4 innestato, Chrome, 9 punti su 3 scene:

| | alto-sinistro | centro | basso-destro |
|---|---|---|---|
| **metodo nuovo** | **+51** · **+50** · **+51** | **+50** · **+50** · **+51** | +0 · +0 · +0 *(satura al bordo)* |
| ⛔ **metodo vecchio** (che sottraeva l'origine) | **+0** · +0 · +0 | **−1** · +0 · +0 | −1 · −1 · +0 |

⇒ ⛔ **Il metodo vecchio, con l'immagine spostata di 50 pixel, sarebbe stato VERDE su tutti e nove i
punti.** Non è più un'ipotesi della revisione: è misurato.

#### ⛔⛔ E TRE DIFETTI NUOVI DEL BANCO, che nessuno aveva ancora nominato

1. ⛔⛔ **Le quattro scene sui pixel non misuravano più NIENTE.** Mettevano il fotogramma con
   `schermo.deposito = c; schermo.componi()`, ⛔ ma `componi()` comincia con
   `if (this.bm) { … return false; }` e `this.bm` c'è su tutt'e due i motori da quando la tela è
   passata a **`bitmaprenderer`** (`DECISIONI.md` §5.4). ⇒ `[M]` 22 agosto: `sfora` su Chrome,
   **12 fotografie su 12 senza nessun marcatore**. ⭐ I banchi si sono comportati bene — dicevano «i
   marcatori non si trovano» invece di uno zero — ⚠ ma **gli esiti del 16 agosto nel deposito sono di
   prima di quel cambiamento**, e §4.3-bis li dichiarava ancora buoni. ⇒ Curato: il fotogramma passa
   da **`schermo.mostra()`**, la funzione che riceve i fotogrammi veri, e ogni riga di esito dichiara
   la **`strada`**;
2. ⛔ **`numeri` era ROSSO PER SEMPRE con un fattore del dispositivo forzato**: A1 confronta due
   zoom, con `FATTORE=` ce n'è uno solo, e quel caso faceva `guasti += 1`. ⇒ Per questo la scena non
   l'aveva mai lanciata nessuno a dpr 1,25 o 1,5. Una domanda **non posta** adesso si dichiara e non
   conta come risposta sbagliata;
3. ⛔⛔ **il banco riempiva il disco della macchina — e il disco è di tutti.** `[M]` un giro intero
   scriveva **1,5 GB** di fotogrammi grezzi (1600×1000×3 = 4,8 MB l'uno, **63 calibrazioni nella sola
   scena `numeri`**) in `/tmp`, che qui è un **tmpfs da 3,8 GB condiviso con altri otto agenti**.
   L'ha portato al **100 %**, e il giro dopo è morto con *«No space left on device»* — ⚠ su un banco
   altrui sarebbe morto **senza che nessuno capisse perché**. ⇒ Curato: i pixel si leggono da una
   **pipe**, su disco ci finiscono solo con `B37_FOTO=tieni`, e la riga di esito porta `null` invece
   di un percorso che non esiste;
4. ⚠ **e una quarta cosa, che non era un difetto ma una flaky, e valeva tre guasti**: `voce` su
   Firefox lanciata subito dopo un'altra scena moriva perché **il primo comando scadeva a 20 s** —
   la pagina si era annunciata, ⛔ ma il ciclo che chiede i comandi non era ancora partito. Il
   certificatore l'ha letta come *«il giro SANO è rosso»* e ha **rifiutato di certificare tre
   guasti**: `[M]` primo giro su Firefox **4 confermati su 7**, secondo giro **7 su 7**.
   ⇒ Curato: `aspetta_canale()` — la pagina che si annuncia e il ciclo che risponde sono **due cose
   diverse**, e adesso si aspetta la seconda. ⭐ E il certificatore si è comportato bene: ha detto
   «non certifico» invece di contare quei tre come confermati.

#### ⭐⭐ E adesso `bash banchi/06-b37-lancia.sh tutti tutte` gira davvero

`[M]` 22 agosto 2026, 09:48, carico `0,57 → 0,64`: **14 giri di scena in una sola invocazione**
(sette scene × due motori), **80 verdetti verdi e zero rossi**, `windows` compresa — che si porta
dietro il suo schermo 2600×1000 e il suo fattore 1,25 senza toccare le altre sei.
⇒ ⛔ Cade la riga *«finché non è curato, si lancia una scena per volta»*.

#### ⚠ E su Gecko c'è una riga in più da scartare, dichiarata invece che scartata in silenzio

Sotto il suo minimo **Firefox non stringe il riquadro di impaginazione**: `clientWidth` resta
grande, la finestra X si stringe lo stesso, e quel che c'è dentro **lo taglia il bordo della
finestra**. `[M]` la striscia di calibrazione esce fino a **210 px** più corta di
`clientWidth × dpr`. ⇒ **12 righe su 63** non sono una scena e si scartano — ⛔ ma il confronto che
le scarta è fra **due numeri del browser** (`clientWidth × dpr` e i pixel), non fra il banco e il
prodotto: nessun difetto della pagina può nascondersi lì, perché `misura_vista()` non entra in
nessuno dei due membri. ⇒ Su Firefox il denominatore di `numeri` è **48 righe su 63**, e le 12
scartate si stampano una per una.

#### ⚙ Che cosa è cambiato nel banco, file per file

| | |
|---|---|
| ⭐ `06-b37-guasti.py` · `.sh` | **nuovi**: i cinque guasti con l'ancora verificata (7 ancore su 7 vive, molteplicità 1) e il certificatore, che pretende **il sano verde**, **il guasto rosso** e **la frase dichiarata prima** — ⛔ non un rosso qualunque (è il rilievo 2 di §5.5 su `06-b33`) |
| `06-b37-comune.py` | la **calibrazione sui pixel** (due strisce a posizione fissa, `ox`/`oy` e la vista in pixel del dispositivo, con **due maschere** perché a dpr non intero il bordo cade a mezzo pixel) · `mostra()` per la strada del prodotto · la **marca del giro** su ogni riga di esito |
| `06-b37-numeri.py` | A2 e A6 **riscritte** su quella verità esterna, A5 **bidirezionale**, la tolleranza di A1 **derivata** invece che scelta |
| `06-b37-sfora.py` · `-pixel.py` · `-windows.py` | il **limite inferiore** (`W − ceil(dpr) ≤ disegno`), la strada del prodotto, il mezzo pixel **contato** |
| `06-b37-coordinate.py` | **C0 · l'origine** e la controprova col metodo vecchio |
| `06-b37-voce.py` · `-modi.py` | il **testo vero** di `chiedi_tela` estratto dal prodotto e installato con una `eval` diretta su un canale finto ⇒ la guardia si attraversa, e l'osservabile è `canale.manda(TIPO.ADATTA_TELA, …)` |
| `06-b37-lancia.sh` | la **settima scena** in «tutte» (con il suo schermo 2600×1000 e il suo fattore 1,25) · il difetto dichiarato in §4.3-bis — *«dopo la prima scena il browser non si riapre»* — **curato**: si aspetta che tutto quel che tiene il profilo sia morto |
| `06-b37-strumenta.py` | estrae e verifica il testo di `chiedi_tela` (58 righe), e **fallisce rumorosamente** se l'ancora non c'è |

### 5.16 · ⭐⭐ 22 agosto — **tre proposte al prodotto: due RIFIUTATE con la misura, una smentita al contrario**

*Le proposte venivano da chi aveva esercitato `cattura.c` col palco finto. ⭐ Tutte e tre sono state
messe alla prova invece che attuate, e il risultato è più utile di tre cure.*

| la proposta | l'esito |
|---|---|
| *«`cattura_ridimensiona()` dichiara successo su un flusso che muore, e `figlio.c` non ha modo di saperlo»* | ⛔ **RIFIUTATA**: la premessa è falsa. `[M]` col ciclo vero del figlio, il guasto arriva a **8,1 ms** con **stato e causa dal produttore** — non è un timeout. ⭐ E un esito «morto» restituito dalla funzione sarebbe **verde per costruzione**: la morte arriva 2 ms dopo il ritorno |
| *«serve un accessore per la divergenza»* | ⛔ **RIFIUTATA**, e con tre misure: la sola scena che accende il campo dà un **falso allarme** (i «concessi» erano la richiesta di prima, non una concessione); i due accessori che esistono **bastano** e in più sanno dire «non ancora negoziato»; e la via del contatore **non regge** — due richieste incatenate producono **una sola** risposta, quindi i conti divergono per sempre |
| *«il ramo "concesso diverso da chiesto" non si raggiunge»* | ⭐⭐ **SMENTITA AL CONTRARIO**: si raggiunge, **43 colpi su 480 catene** |

⭐⭐ **E la smentita ha trovato un difetto di prodotto**: la riga di registro diceva *«la conversione
delle coordinate nasce sbagliata e il puntatore andrà altrove»* — ⛔ e nella **sola** scena che la
accende è **falso**. ⇒ *Un registro che attribuisce la causa sbagliata costa più di un registro
muto.* Riscritta: dice il fatto, nomina i **due** moventi possibili, e manda dove il verdetto si dà
davvero.

⚠ **E la guardia della divergenza resta un commento con un `gboolean` attaccato — ma adesso il codice
lo dice**, invece di lasciar credere che qualcuno la legga.

⛔ **E un difetto del banco che l'autore ha dichiarato per primo**: il suo caso 6 *«stampava un numero
che non aveva letto»* — due zeri scritti a mano nella riga al posto della misura. ⭐ *«È esattamente
il difetto che avrei segnalato a un altro.»*

⏳ **E un guasto vero lasciato aperto, non suo da curare**: `[M]` il rimontaggio chiede al palco **la
misura che l'ha appena ucciso**, e la chiamata **riesce 3 volte su 3** mentre il palco muore 300 ms
dopo — con l'attesa corta si sceglie un **cappio**, e nessuno se ne accorge. ⚠ Sul prodotto vero è
`[?]`, perché Mutter concede tutto sotto il tetto. È **dichiarato nel codice** accanto al ramo.

## 6 · Le decisioni prodotte

- ✅ **`DECISIONI.md` §5-bis.7** — *la disposizione di tastiera la comanda il client, e il server la
  applica*: **confermata dall'utente il 16 agosto 2026**, messo davanti alle tre strade. ⛔ E il
  riquadro nuovo di quella voce porta la misura che l'ha resa necessaria: era una decisione **✅ dell'8
  agosto mai attuata**;
- ⏳ **`RCP.md` §7.1** — la riga mancante sul **palco che cambia misura da sé** ha adesso **due
  stesure proposte e misurate** (dalla 6.4 sul filo, dalla 6.3 sul compositore vero), da fondere:
  nessun `TELA` non sollecitato · non adottare · non spedire fotogrammi di misura diversa ·
  richiedere la tela in vigore con un'attesa che cresce · scriverlo nel registro · ⛔ **e non
  richiamare mai il palco mentre una richiesta del client è in volo**;
- ⏳ **`RCP.md`**, altre sei righe consegnate dagli agenti e non ancora scritte: il confine del
  secondo di grazia (`<` o `<=`), le due tele dentro lo stesso secondo, i limiti della **vista** che
  §4.5 non nomina, che cosa risponde il server a `VISTA` (⛔ *niente*, e perché un `TELA` di cortesia
  ucciderebbe la sessione), `COMPOSITORE_INCAPACE` non dichiarato **permanente**, e ⛔ **la
  contraddizione §7.1 contro §4.2** su `ADATTA_TELA` seguito dal FIN del client;
- ⏳ **`SPECIFICHE.md` §6** — cinque righe proposte dalla 6.5, fra cui la chiusura delle tre `[?]` di
  §6.1-bis e il **numero di guardia** della nitidezza;
- ⏳ **`SPECIFICHE.md` §11.5** — Windows non è dichiarato fra i client (la sezione nomina i **motori**,
  non i sistemi).

---

## 7 · Che cosa resta `[?]`

### 7.1 · ⛔ Aperto e con una misura in mano — il lavoro che viene

| | |
|---|---|
| ⛔⛔ **il ricambio dei dispositivi che NON dipende dalla tela** | `[M]` ogni `cattura_risveglia()` (400 ms, scena ferma, chiave dovuta) ricrea i dispositivi di `libei`: **3 risvegli, 3 ricambi**, con **zero `ADATTA_TELA`**. ⇒ Il clic che muore ha una **seconda porta**, aperta proprio quando l'utente tiene premuto il mouse su un desktop fermo, e la cura ovvia distruggerebbe ogni trascinamento. ⏳ **La forma giusta va decisa**, e non è di una sottofase sola |
| ✅ ~~⛔ **il difetto è a monte, in Mutter**~~ · ⛔ **e la risposta è peggio della domanda** | **CHIUSA il 21 agosto 2026** `[R]`: il difetto è vero, **nessuno l'ha mai aperto**, e **non è corretto nemmeno nel `main` di oggi** — `remove_viewport_devices()` è identica carattere per carattere fra la 48.7 che gira qui e il ramo principale di agosto 2026. ⇒ Non c'è versione da aspettare: **la cura è nostra, su ogni Mutter**. Il seguito sta in §7.1-bis |
| ✅ ~~**le richieste incatenate, da rimisurare**~~ · ⛔ **e resta un buco peggiore** | rimisurate il 17 agosto: **0 rotti su 18** (§4.8). ⛔⛔ **Ma il controllo positivo non ha reso**: togliendo la cura sospetta escono **ancora 0/18** ⇒ *non si sa che cosa tenga questa scena*, e i **4/18** della 6.3 **non sono riproducibili** a macchina ferma. ⚠ L'unica differenza rimasta è la **contesa sulla GPU** (cinque codificatori sullo stesso iGPU): finché non si ricrea, ⛔ **il verde vale «sotto carico CPU», non «sotto contesa GPU»** |
| ✅ ~~**la cura del clic non è mai stata verificata dove vive**~~ | verificata il 17 agosto su un albero solo: il rilascio è dichiarato nel registro e **tutti i clic del secondo giro arrivano**, ⭐ col controllo positivo che riproduce il difetto **a comando** |
| ✅ ~~**tutti i millisecondi sono sotto carico**~~ | ripresi a macchina ferma (load 0,07-0,13): §4.8 |
| ⛔ **tre attesi di `06-b33` sono scritti per il mondo COL DIFETTO VIVO** | T3, R1 e R2 restano **rossi con la cura** e erano **verdi senza**: con il tasto già rilasciato prima del ricambio, le righe di dichiarazione non si scrivono perché non c'è più niente di premuto. ⇒ **Va corretto l'atteso del banco, non il prodotto** — ed è un banco nato ieri, quindi il difetto è di ieri |
| ✅ ~~⚠ **due attrezzi del banco 6.3 si rompono**~~ | **CURATI il 21 agosto** e certificati contro un calcolo a mano in `awk` (235 campioni, tutti coincidenti). ⭐ La causa non era negli attrezzi: era il **registro che si intrecciava** fra padre e figlio. 📖 §5.6 |

### 7.1-bis · ⭐⭐ 21 agosto 2026 — **la catena completa del clic che muore**, letta nel sorgente di Mutter

*Tutto `[R]`, dal sorgente di `reference-gnome/mutter` (tag **48.7**, commit `f4abb824`) — ⭐ e
`[M]` la macchina di prova monta **esattamente quella**: GNOME Shell 48.7, `libmutter-16-0`
48.7-0+deb13u1, `libei1`/`libeis1` 1.3.901-1. Nessuno scarto di versione da scontare.*

#### ⭐ PERCHÉ i dispositivi si ricreano anche senza `ADATTA_TELA` — il `[?]` del §4.6 ha una causa

`meta_screen_cast_virtual_stream_src_enable()`
(`⟨mutter⟩ src/backends/meta-screen-cast-virtual-stream-src.c` · `meta_screen_cast_virtual_stream_src_*`) chiama
`meta_eis_viewport_notify_changed()`. ⇒ **Ogni riabilitazione dello stream ricrea i dispositivi**,
cioè **ogni `cattura_risveglia()`** — ed è il «3 risvegli, 3 ricambi, zero `ADATTA_TELA`» di §7.1,
che non era un mistero ma quella riga. ⚠ Viene dalla **MR !4622**, entrata in **Mutter 48.5**: è
recente, e noi siamo dentro la finestra.

⚠ **E c'è un secondo moltiplicatore**: `add_logical_monitor_viewports()`
(`meta-remote-desktop-session.c:388`) fa `remove_all_viewports` **poi** `take_viewports`, e
**tutt'e due** emettono `viewports-changed` ⇒ **due giri di ricambio per ogni cambio di monitor**.

#### ⛔ Il difetto è PERMANENTE, non una corsa — e Mutter ha una rete che qui NON si può raggiungere

⚠ **Questa è la parte che rende la riga di §7.1 refutabile, e per cui prima non reggeva.** Chi legge
solo *«`remove_viewport_devices()` non passa da `drop_device()`»* può rispondere: *«ma Mutter
rilascia lo stesso in `dispose`»* — e ha l'aria di avere ragione, perché
`meta_virtual_input_device_native_dispose()` chiama `release_device_in_impl()`, che rilascia **tutti**
i bottoni e i tasti tenuti giù, con tanto di riga di diagnostica.

⛔ **Su questo cammino quella rete è irraggiungibile**, e la catena è di tre anelli:

1. il `ClutterVirtualInputDevice` muore **solo** con `meta_eis_device_free()`, distruttore della
   tabella `client->eis_devices`;
2. fuori dal disconnect, l'unico che toglie una voce da quella tabella è il ramo
   **`EIS_EVENT_DEVICE_CLOSED`** (`meta-eis-client.c:987`);
3. ⭐ `[R]` **su libei 1.3.901-1, che è la versione installata**: quell'evento lo genera **soltanto**
   una `release` mandata **dal client** (`eis_device_closed_by_client()` ← `client_msg_release()`).
   `eis_device_remove()` non lo genera **mai**: mette lo stato a `DEAD` e manda `destroyed`. E il
   client non deve nemmeno chiamare `ei_device_close()` su un dispositivo rimosso dal server — lo
   dice l'intestazione pubblica di libei, e il client di prova di Mutter infatti non la chiama.

⇒ ⛔⛔ **La voce resta nella tabella per sempre**, `release_device_in_impl()` non gira mai, e
`seat_impl->button_count[BTN_LEFT]` resta **1 per sempre**. Si sana **solo al disconnect**, che è
l'unico posto da cui passa `drop_device()` — ⭐ ed è esattamente il *«si guarisce solo riaccendendo
il server»* che §4.6 aveva misurato senza sapere perché.

⚠ **E `button_count[]` è del POSTO, non del dispositivo**: è la ragione per cui la cura potrebbe
essere molto più piccola di quanto sembri — un rilascio mandato da un dispositivo **nuovo** può
ancora far scendere il conto. ⏳ Da misurare, non da dedurre.

#### ⛔ La nostra cura di oggi copre l'altro cammino

`input_rilascia_tutto()` prima di `cattura_ridimensiona()` (`figlio.c` · `codificatore_di()`) copre il **cambio di
geometria**. ⛔ **Non** copre `cattura_risveglia()`. ⇒ La «seconda porta» di §7.1 è aperta proprio
dove la cura non arriva.

#### ⛔ A monte: nessuno l'ha mai aperto, e non è corretto nel `main` di oggi

`[R]` cercato il 21 agosto 2026 sull'API di `gitlab.gnome.org/GNOME/mutter`: le issue con `eis` e
`libei`, le **15** merge request con `eis` nel titolo dal 2023 a oggi, e una ricerca su
`remove_viewport_devices` ⇒ **niente**. Idem `gnome-remote-desktop`.

⭐ **L'unico precedente è la prova migliore che l'asimmetria non è voluta**: la MR **!3809**,
*«backends/eis-client: Release buttons on device remove»*, fusa il 14 giugno 2024, corregge una riga
sola **dentro `drop_device` e solo lì**. ⇒ L'intento a monte è dichiarato nel titolo, e il cammino
del viewport lo viola.

⛔ **E non è corretto oggi**: scaricato `meta-eis-client.c` dal ramo **`main`** (agosto 2026, serie
50/51), `remove_viewport_devices()`, `drop_device()`, `update_viewports()` e `remove_device()` sono
**identici carattere per carattere** alla 48.7. ⇒ Non c'è una versione da aspettare né una
distribuzione già a posto: **la nostra cura serve su tutte**.

⭐ *(In più, a carico di Mutter e non nostro: è anche una **perdita di memoria** — la tabella tiene
un `eis_device_unref` come distruttore, quindi `struct eis_device` e `MetaEisDevice` restano vivi a
ogni ricambio, per tutta la sessione. Lo stesso vizio ce l'hanno `remove_abs_devices()` e
`remove_touch_devices()`.)*

#### ⏳ Che cosa resta, e costa poco

⛔ **Tutta questa catena è `[R]`, non `[M]`**: è codice letto, non misurato. La conferma decisiva è
una riga di diagnostica: con `MUTTER_DEBUG=eis,input`, dopo un ricambio di viewport **a bottone
premuto**, ci si aspetta `Dropping repeated press of button 0x110, count 2` **e l'assenza** di
`Releasing pressed buttons while destroying virtual input device`. ⚠ **Se comparisse la seconda
riga, tutta la lettura cade** — ed è per questo che sta scritta qui: una catena che non sa come
essere smentita non è una diagnosi.

`[?]` Se i manutentori lo considerino un difetto di Mutter o «cosa che deve gestire il client»: non
è deducibile dal codice. ⛔ **E non è stato aperto niente a monte**: è un'azione verso l'esterno, e
la decide l'utente.

### 7.2 · Le `[?]` di misura, dichiarate invece che estrapolate

- **il DeX e la GPU vera**: il mezzo pixel non arriva ai pixel su Xvfb ⇒ `[?]` **su GPU vera e su
  Samsung DeX**. ⛔ Il telefono ce l'ha l'utente: si chiede a lui, non si aggira;
- ⛔⛔ **E una delle tre `[?]` di `SPECIFICHE.md` §6.1-bis era stata SOSTITUITA in silenzio.** Le tre
  vere sono lo **zoom** (✅ chiusa il 22 agosto, con la tolleranza *derivata* invece che scelta), il
  **lato dispari** (✅ chiusa, con un guasto innestato come controllo positivo) e ⛔⛔ **«su DeX
  `screen` risponde con lo schermo esterno o col telefono?»** — che **non l'ha mai toccata nessuno**,
  perché il telefono è dell'utente. ⚠ Al suo posto il documento aveva messo **«il mezzo pixel»**, che
  è un'altra domanda: ⇒ una `[?]` sparita e una comparsa, senza che nessuno se ne accorgesse. 📖 §5.15;
- ⛔ **«conforme» non è «funziona»**: l'arbitro certifica i byte — *«un server che rispondesse
  `TELA(ADATTATA)` senza toccare il palco passerebbe tutti e cinque i giri»*. I pixel li misura
  un altro banco, e la distinzione va tenuta;
- ✅ ~~**il secondo di grazia curato e non misurato**~~ — **CHIUSO il 22 agosto**, e ⛔ **la ragione
  per cui sembrava impossibile era sbagliata**: la grazia parte dal `TELA`, **non dalla connessione**,
  quindi i 1500 ms della stretta di mano non c'entrano. 📖 §5.10;
- ✅ ~~**codice mai esercitato su Mutter**: il ramo «concesso diverso da chiesto» e
  `MISURA DIVERGENTE`~~ — **SMENTITO il 22 agosto**: ⭐ `MISURA DIVERGENTE` (oggi `cattura.c` · `su_parametri()`)
  **si raggiunge dall'esterno** — `[M]` **43 colpi su 480 catene**, tre spazzolate su tre. ⛔ La porta
  non è il produttore, **è il tempo**: due ridimensionamenti incatenati — *l'utente che trascina il
  bordo* — e la risposta del primo torna quando la richiesta porta già la seconda. Finestra: fra
  **200 e 800 µs**. ⇒ È una corsa, ⭐ **ma una corsa che un banco programma**: si spazzola la distanza
  fra le due chiamate. ⚠ Resta non esercitato quello di `figlio.c` (oggi `:6764`): servirebbe un
  fotogramma vero, e il palco finto non ne accoda. 📖 §5.16;
- ✅ ~~**il posto si lascia dopo ~75 s** di silenzio, non i 30 di §5.3~~ — **MISURATO il 22 agosto:
  sono 30, e il «~75» non si riproduce.** 📖 §5.13;
- ✅ ~~**le coordinate in volo sono inarbitrabili da una registrazione**~~: dal 21 agosto `RCP.md`
  §11.1 registra il **tempo**, e la regola è collaudabile — ⛔ **in un verso solo**, e §5.10 racconta
  perché quel verso non basta;
- **`?video=worker` non esercitato**; **`aioquic` non è installato sul portatile** (il cliente si
  prova in locale solo con surrogati, e il banco lo dichiara);
- ⛔ **il ripiego su KWin resta non verificabile sul vero**: KDE è la fase 11. Il percorso di codice
  è provato **sull'ospite finto**, e la **riga di registro** che lo dichiara adesso è pretesa da un
  banco (`06-b36` casi 1-2) — che è quel che `SPECIFICHE.md` §6.3 chiedeva.

### 7.3 · ✅ ~~E i tre difetti che la decisione dell'utente rende urgenti~~ — **erano già chiusi, e il documento mentiva da cinque giorni**

> ⛔ **Questa sezione elencava tre difetti che il prodotto non ha.** Misurati sul vivo il 21 agosto
> 2026 (porta 7721, utente `provat6`, sessione GNOME vera con testimone dentro, carico 0,20-0,60):

| il documento diceva | `[M]` il prodotto fa |
|---|---|
| `hu` `tr` `gr` `ua` ricevono `SESSIONE_NON_SERVIBILE` | ⭐ **aprono la sessione**, tutte e quattro |
| `it(nonesiste)` apre la sessione | ⭐ **`0x0E SESSIONE_NON_SERVIBILE`** |
| `DISPOSIZIONE` a sessione aperta chiude la connessione | ⭐ **connessione viva**, `KEYMAP CAMBIATA → de [German]`, nessun messaggio sul filo |

⇒ Li aveva chiusi la cucitura del **16 agosto**: la domanda «esiste?» va a XKB
(`webtransport.c` · `gancio_disposizione_esiste()` → `tastiera.c`), la variante ci entra perché `it(nonesiste)` non compila, e
`T_DISPOSIZIONE` ha il suo `case` (`rcp.c` · `drena()`). ⚠ Nessuno aveva riletto questa sezione, ed è la
stessa specie di difetto di `fasi/07` §8: **un documento fermo a quattro giorni fa manda a cercare un
guasto dove non c'è**.

⭐ **E non ci si è fermati a «la sessione si apre»**, che è il metro che questa fase vieta: il
testimone dentro la sessione ha registrato **il carattere**, con l'atteso calcolato da `tastiera.c`
chiamato da fuori — `hu`→`ű`,`ő` · `tr`→`ğ` · `gr`→`α` · `ua`→`ї` · `de(T3)`→`‑`, **tutti arrivati**,
più il negativo (`it` non produce `ű`, e la riga che lo dichiara c'è).

#### ⛔⭐ Ma al loro posto ce n'era uno VERO: **la forma D1 sopravvissuta alla propria cura**

La cura del 16 agosto ha tolto l'elenco fisso di venti nomi, ⛔ **e davanti al gancio è rimasto un
secondo elenco scritto a mano: l'alfabeto ammesso nel nome**, che accettava solo `[a-z0-9]`.

`[M]` Chiedendolo al sistema **attraverso il prodotto**, su tutte le **590** coppie
disposizione/variante di `evdev.lst`: **589 si compilano**, e **nove hanno una maiuscola** —
`de(T3)`, `ie(CloGaelach)`, `ie(UnicodeExpert)`, `in(tamilnet_TAB)`, `in(tamilnet_TSCII)`,
`jp(OADG109A)`, `lk(tam_TAB)`, `ru(phonetic_YAZHERTY)`, `ua(macOS)`. ⛔ Sul filo ricevevano
**`0x0B ERRORE_PROTOCOLLO`** — che è **peggio** di `SESSIONE_NON_SERVIBILE`, perché dice *«il tuo
client è rotto»* e manda a cercare il guasto dall'altra parte del filo. E `it()` (variante vuota)
prendeva `0x0E` su una stringa **fuori forma**: i due guasti di §4.5 uniti.

⇒ **Curato** (`rcp.c` · `tratta_credenziali()`, e il gemello allineato byte per byte): un solo
`disposizione_carattere_ammesso()` con l'alfabeto **identico** a quello di `tastiera.c`, più il
rifiuto della variante vuota. ⚠ Due controlli di forma scritti due volte davano due risposte sotto
la stessa etichetta: è la forma **E2**. La difesa non si allenta — punto, barra, virgola e
`../../etc/passwd` restano fuori. ⭐ Prezzo dichiarato: `IT` adesso passa la forma e riceve `0x0E`
invece di `0x0B`, ed è la risposta giusta (XKB distingue le maiuscole).

⭐ **Rosso→verde certificato** sulla stessa macchina: caso 8, **7 righe rosse su 17** col binario di
prima → **17 su 17** col curato; e quattro guasti innestati che accendono il caso dichiarato.



---

## 8 · Il giudizio dell'utente

*La fase si chiude su una misura giudicata dall'utente, non su un documento completo.
⛔ Non si scrive un verdetto che l'utente non ha dato.*

✅ **Uno c'è già, ed è del 16 agosto 2026**: **«il test su Windows lo dichiaro superato al 100 %»**
— dato sul prodotto vivo, da un terzo sistema client mai provato prima, con `dpr 1,25` e la finestra
dispari su tutt'e due i lati (§4.1 e §4.1-bis).

✅ **E il 22 agosto 2026 sono arrivati anche gli altri due**, cioè le due scene che questa fase
aveva aperto:

| la scena | il giudizio |
|---|---|
| ⭐ **il clic tenuto giù** | *«Sto tenendo il clic premuto ed è tutto ok.»* ⇒ **La seconda porta del clic che muore non si sente più.** Era il difetto che questa fase ha inseguito per tre giorni: da §4.6 (*«il clic che muore»*) a §7.1-bis (la catena letta nel sorgente di Mutter) a §5.7 (le cure A+C) |
| ⭐ **il trascinamento del bordo** | *«Riscala con la comparsa di bande nere, ma immagino sia normale per mantenere le proporzioni.»* ⇒ **Il re-scaling è accettato**, bande comprese: è il prezzo dichiarato quando il ridimensionamento dinamico è uscito (`DECISIONI.md` §5.1-bis) |

⚠ **E una precisazione dell'utente che è entrata nel vocabolario**: *«lo scaling è opera del browser,
non di REMOTIX»* — ⭐ ed è esatto: noi scriviamo **due misure in CSS**, il riscalamento lo fa il
browser con la sua accelerazione. L'unica cosa che gli imponiamo è **come** riscalare
(`image-rendering: pixelated`), perché il testo resti netto invece di essere impastato. 📖 §5.14.

⛔ **E quel che il giudizio NON copre, scritto perché non lo si deduca**: la **guardia della cura A**
(la riga «TENUTI GIU'») **non è ancora scattata in nessuna misura**. ⇒ L'utente dice che il difetto
non si sente più — e questo chiude il **difetto**. ⚠ Ma *«non si sente»* non è *«la guardia ha
funzionato»*: potrebbe essere la cura **C** a coprire tutto, e la **A** a non essere mai stata
esercitata. Resta una `[?]` di diagnosi, non di prodotto.

## ⛔⛔ 21 agosto 2026 — **Firefox per Android non ha WebCodecs**, e il messaggio nostro mentiva

*Prima prova su un telefono vero (Samsung DeX, Android 16). L'utente: «credo che abbiamo introdotto
una regressione per quanto riguarda Firefox su Android».*

⛔ **Non era una regressione.** `[M]` Dal registro del server, parole della pagina:

```
browser: Mozilla/5.0 (Android 16; Mobile; rv:154.0) Firefox/154.0
         · schermo 2560x1080 · dpr 1 · WebCodecs NON c'e'
sonda video · ⛔ HEVC: NON arriva al pixel — questo browser non ha WebCodecs
sonda video · ⛔ H264: NON arriva al pixel — questo browser non ha WebCodecs
congedo motivo=0x09 dettaglio=nessun codec condiviso
```

⇒ `VideoDecoder` **non esiste** su quel browser, e in `pagina.html` la strada verso i pixel è
**una sola**: zero occorrenze di `MediaSource` in tutto il file. ⚠ Con AV1 sarebbe finita identica —
il passaggio a H.264 (§1.13-ter) non c'entra, e la riga di `DECISIONI.md` che diceva «così Firefox
Android funziona» era una **premessa sbagliata**, corretta qui.

### ⛔ E la cosa nostra c'era: la scritta mandava a cercare nel posto sbagliato

Il riquadro diceva *«questo browser non porta nessuno dei due codec video fino ai pixel: né HEVC né
H.264 … su Linux il decodificatore HEVC di Chrome è quello della scheda grafica»* — una spiegazione
su codec e schede grafiche, mentre la causa vera stava una riga più su ed era di un'altra specie.

⇒ Adesso la casella **«WebCodecs non c'è»** viene **prima** e si nomina: *«questo browser non ha
WebCodecs, cioè l'unico modo che REMOTIX ha di disegnare il desktop: non è una questione di codec»*.
⭐ Una scritta che manda nel posto sbagliato è peggio di nessuna scritta.

### ⏳ Che cosa resta aperto

⚠ Se Firefox per Android deve essere un motore supportato, serve un **secondo percorso di disegno**
(MSE con un `<video>`): è lavoro vero, cambia le proprietà di ritardo, e va deciso — non è un
interruttore. ⭐ Chrome per Android ha WebCodecs, e lì la strada c'è.

## ⏳ 21 agosto 2026 — **quanto costerebbe MSE**, misurato prima di scrivere il percorso

*Il vincolo dell'utente: «supportare pienamente Chrome e Firefox in Linux, Windows e Android».
⛔ Firefox per Android non ha WebCodecs, quindi coprirlo vuol dire un **secondo percorso di
disegno**: `MediaSource` con un `<video>`, a MP4 frammentato invece che ad Annex-B. ⇒ Il prezzo si
misura prima, non dopo — banco `banchi/07-b57-quanto-costa-mse.py`.*

### La misura — stesso ferro, stesso flusso (i nostri 150 fotogrammi, 2560×962, H.264 High 5.0)

| | Firefox | Chrome |
|---|---|---|
| WebCodecs, 60/s | **60,5 ms** | **50,9 ms** |
| MSE, 60/s | 285,4 ms — ⛔ **+225 ms** | 465,6 ms — ⛔ **+415 ms** |
| MSE, 10/s | 246 ms — ⚠ **+17 ms** | 570 ms — **+348 ms** |
| coda di riproduzione | 310–650 ms | 520–715 ms |

⛔ **Il tetto dichiarato è 50 ms** (`SPECIFICHE.md` §3.2). ⇒ A ritmo utile MSE lo sfonda di un
ordine di grandezza, e non per lentezza del decodificatore: il `<video>` **tiene una coda apposta**,
perché il suo mestiere è la riproduzione fluida, non il ritardo basso.

⚠ **Il limite della misura, dichiarato**: lo schermo del banco è un `Xvfb` **senza GPU**, quindi tutte
e due le strade decodificano in software. ⭐ Ma la coda di presentazione non è una proprietà della
scheda video, e il confronto è fra due strade **nello stesso identico posto**.

⚠ **E l'inseguimento non salva**: saltare al bordo vivo porta la mediana di Firefox a 265 ms con
**40 salti** su 150 fotogrammi — cioè un'immagine che scatta. Si scambia ritardo con scatti.

### ⛔ Cinque difetti del banco, e ognuno avrebbe prodotto un numero falso

Questo banco ha mentito **cinque volte** prima di misurare, e vale la pena elencarle perché sono
tutte della stessa famiglia — *lo strumento misurava se stesso*:

1. `"null"` letto come un esito: Chrome dava tre righe rosse **e funzionava**;
2. alimentare a 10/s un MP4 che si dichiara a 60 fps: il `<video>` corre a 60, resta a secco, e
   `requestVideoFrameCallback` vede **due** fotogrammi su cento;
3. misurare **l'avvio** invece del regime: mediana 2,7 s con una coda di 160 ms;
4. ⛔ **nessun gesto dell'utente**: senza un tocco il `<video>` non parte affatto — coda 3,5 s,
   *zero* fotogrammi buttati, e sembrava «MSE bufferizza» mentre era «non è mai partito»;
5. ⛔ **`ffmpeg -framerate` non vale per il demuxer H.264**: il file usciva a **25 fps** mentre lo
   alimentavo a 60, e la coda che chiamavo «di MSE» era la mia differenza di ritmo. Si vede da
   `currentTime = 5,98 s` con 150 fotogrammi: 150/25 = 6 s. ⇒ Si usa `-r`, e **si verifica con
   `ffprobe`** invece di credere alla riga di comando.

⭐ Il difetto 4 è stato trovato **da un numero incoerente**, non da un errore: «coda 3,5 s **e zero
fotogrammi buttati**» non può descrivere un decodificatore in affanno. Un banco che avesse
riportato solo la mediana non l'avrebbe mai fatto vedere.

### ⏳ Che cosa resta da decidere — e non si decide qui

⛔ Con questi numeri, «Firefox per Android pienamente supportato» e «ritardo sotto i 50 ms» **non
stanno insieme**. ⇒ La scelta è dell'utente, e le opzioni sono nominate: accettare su quel motore un
ritardo di un'altra classe, oppure dichiararlo non supportato finché Mozilla non porta WebCodecs su
Android. ⚠ La misura definitiva è sul telefono, che l'hardware ce l'ha; il banco si serve alla rete
di casa con `banchi/07-b57-servi-al-telefono.py`.

## ⭐⭐ 21 agosto 2026 — **la prima sessione Android**, e l'utente: «Chrome è un missile»

*Chrome per Android, Samsung DeX, 2560×1080. Tre minuti e mezzo di sessione vera, `[M]` dal registro
del server e dal diario della pagina.*

| | |
|---|---|
| codec negoziato | ⭐ **HEVC** (codec 1) — **non** il ripiego H.264 |
| tela | 2558×926 |
| fotogrammi | **3 178 arrivati, 3 178 dipinti** |
| saltati · buchi · fuori ordine · tardivi · errori del decodificatore | ⭐ **0 · 0 · 0 · 0 · 0** |
| input | 45 tasti, tutti arrivati |
| audio | 8 935 blocchi ricevuti, 8 933 suonati, **2 buchi** in 3 min 30 |

⭐ **Zero perdite su ogni riga che il diario conta.** È la prima volta che questo codice tocca un
telefono, e il verso video → schermo non ha un difetto da nominare.

⭐ **E la sorpresa è il codec**: il telefono ha negoziato **HEVC in hardware**, cioè la prima scelta
di `PREFERENZA` — non il ripiego. ⚠ L'H.264 di §1.13-ter resta necessario (Firefox desktop non fa
HEVC), ma su questo telefono non è servito.

### ⛔ E l'unico numero che non è buono: **la coda dell'audio, 401 → 421 ms** — ⭐ e la sera stessa l'orecchio dell'utente lo ha CONFERMATO

Il diario la riporta a ogni giro e **cresce**: 401 ms a 10:37:39, 421 ms a 10:37:49, e lì resta.
Il video, nella stessa sessione, non ha un fotogramma tardivo ⇒ non è la rete: è la coda del
percorso audio.

⛔⭐ **E la sera del 21 agosto l'utente ha ascoltato, due volte.** La prima: *«Chrome su Android
offre un'esperienza completa: audio e video perfetti»*. La seconda, un'ora dopo, su Windows:
*«**il ritardo di 400 ms tra audio e video in generale te lo confermo**»*. ⇒ Il numero **non è un
caso e non è di Android**: è `AUDIO_CUSCINO_MS = 250` in `pagina.html`, più la catena, e si sente
come **sincronia sbagliata** — non come audio sporco. 📖 La diagnosi e la cura nominata stanno in
`fasi/07-audio-e-appunti.md` §8 e §9.7-bis.

## ⭐⭐ 21 agosto 2026 — **il secondo percorso di disegno**: MP4 frammentato su MSE

*`DECISIONI.md` §7.18, dall'utente: «si costruisce». ⛔ E la ragione per cui §0.1-bis non lo vieta:
quel principio parla di un motore che **rende peggio**; qui il motore **non apre affatto**.*

⭐ **Il protocollo non si tocca**: sul filo passano gli stessi fotogrammi Annex-B di §6.2. Cambia
solo **come il client li disegna**, e il server non se ne accorge.

⭐ **E l'audio non è stato scritto**: la pagina ripiegava già su `pcm` quando manca `AudioDecoder`
(§4.3 lo impone a entrambi ed è la base sempre disponibile). ⇒ Il lavoro era **solo il video**.

### I tre pezzi

| pezzo | che cosa fa |
|---|---|
| `MuxMP4` | i fotogrammi Annex-B diventano un segmento d'inizio (`ftyp`+`moov` con l'`avcC` costruito dall'SPS/PPS visti) e un `moof`+`mdat` per fotogramma |
| `sonda_mse_una()` | la sonda **dipinge anche su questa strada** e si giudicano i pixel — ⭐ non si crede a `isTypeSupported` (`LEZIONI.md` §1.9) |
| `Schermo.mse_*` | il `<video>` prende il posto della tela, eredita classe e stile, e i fotogrammi si contano con `requestVideoFrameCallback` — l'unico posto, lì, in cui si sappia che un pixel è arrivato |

⚠ **La durata di ogni fotogramma è quella VERA**, misurata all'arrivo: un desktop non ha un ritmo
fisso — sta fermo per secondi e poi si muove — e dichiarare 60/s a un `<video>` che ne riceve tre al
secondo lo manderebbe a secco a ogni pausa. `[M]` È esattamente l'errore che il banco `07-b57` ha
fatto per primo, con `ffmpeg -framerate` che per il demuxer H.264 non vale.

### ⛔ Due errori di byte, trovati rileggendo prima di provare

1. **`trun`: versione (1 byte) e poi bandiere (3)**, non il contrario. Scritte al rovescio il
   `<video>` legge `flags = 0x030500`, cioè campi che non ci sono: ⚠ **non dà errore e non
   dipinge**.
2. **`tkhd`: mancavano quattro byte** (volume + riservato) prima della matrice, e tutto quel che
   segue scivolava.

⭐ E il muxer è stato **verificato da fuori prima di collegarlo**: i nostri 150 fotogrammi passati
dal muxer e dati a `ffprobe` → `h264, High, 2560×962, level 50, 2,372 s`, e `ffmpeg` li decodifica.
⚠ Un muxer provato solo dentro il browser avrebbe confuso «il mio MP4 è sbagliato» con «questo
motore non lo accetta».

### Lo stato misurato

| | |
|---|---|
| la strada si accende e dipinge (Firefox, `?disegno=mse`) | ⭐ sì — `<video>` 1190×704, 4 dipinti, **0 buchi**, ritardo 50 ms, 1 salto |
| la strada normale (WebCodecs) | ⭐ intatta: `07-b51` 4 controlli su 4 per motore |
| Firefox per Android | ⏳ **da provare sul telefono** — è il motore per cui esiste |

### ⛔ E il primo giro su Firefox Android è fallito — **«caricato» non vuol dire «dipinto»**

*L'utente, 21 agosto 2026: «non funziona». `[M]` E la pagina aveva già scritto il perché nel
registro del server:*

```
sonda video · ⛔ H264: NON arriva al pixel — il `<video>` ha caricato ma i pixel
              non sono quelli della sonda (sinistra 0,0,0, destra 0,0,0)
```

⭐ **Zero-zero-zero su tutti e due i lati è nero, non «un colore sbagliato».** ⇒ Il flusso era
giusto — il `<video>` lo aveva **caricato**, quindi il muxer funziona anche sul telefono — e a
sbagliare era **il momento della lettura**: `loadeddata` dice che il fotogramma è stato
*decodificato*, non che sia stato **presentato**, e `drawImage` da un `<video>` che non ha ancora
presentato niente copia nero.

⛔ La sonda accusava il flusso di un difetto del proprio cronometro. ⇒ Adesso fa presentare il
fotogramma (`play()` muto + `requestVideoFrameCallback` dove c'è) e **rilegge fino a dodici volte**,
e ⭐ **riconosce il nero** invece di trasformarlo in un verdetto.

⚠ È la stessa famiglia dei cinque difetti del banco `07-b57`: *lo strumento misurava se stesso*.

#### ⛔ E la seconda volta la tela era ancora nera — **due cause, tutte e due dei motori mobili**

`[M]` La riga nuova della sonda: *«il `<video>` non aveva ancora presentato niente: la tela è
tornata nera»* — dopo **dodici** riletture in un secondo e mezzo. ⇒ Non era lentezza: quel
`<video>` non presentava **mai**.

| causa | perché |
|---|---|
| il `<video>` della sonda stava **fuori dallo schermo** (`left:-9999px`) | i motori mobili non presentano quel che nessuno guarda: risparmiano batteria. ⇒ Adesso sta dentro la vista, **due pixel per due**, quasi trasparente — visibile quanto basta al motore, non all'utente |
| la sonda partiva **al caricamento della pagina** | presentare vuol dire suonare, e nessuno aveva ancora toccato niente. ⇒ Su questa strada il sondaggio si fa nel `CIAO`, cioè **dopo che l'utente ha premuto «Collegati»** |

⚠ E la seconda cura ha un effetto laterale dichiarato: su MSE la sonda costa il suo tempo **a chi si
collega** invece che al caricamento. Sulla strada di WebCodecs non cambia niente.

#### ⛔⛔ E al terzo «non è cambiato nulla» il difetto era **altrove** — banco `07-b58`

*L'utente, 21 agosto 2026: «Non è cambiato assolutamente nulla, e mi stai facendo perdere tempo con
test inutili». ⭐ Aveva ragione su tutta la riga: gli ho fatto provare tre volte **la mia sonda**,
non il prodotto — e per tre volte quel che si rompeva non era quel che gli chiedevo di guardare.*

⭐ **La cura del metodo, prima di quella del codice**: `dom.media.webcodecs.enabled = false` toglie
`VideoDecoder` **e** `AudioDecoder` a un Firefox da tavolo. `[M]` `typeof VideoDecoder ===
"undefined"` — esattamente quel che dichiara Firefox per Android. ⇒ La strada si prova **qui**, e
sul telefono ci si va una volta sola, alla fine. È il banco `07-b58`.

⚠ E quel che quel banco NON riproduce si dichiara: le regole di risparmio dei motori mobili — un
`<video>` piccolo o fuori dalla vista che non viene presentato. Per quelle l'ultima parola resta del
telefono.

**Alla prima esecuzione ha trovato in un colpo tre difetti che nessun giro sul telefono aveva
nominato:**

1. ⛔⛔ **La scala delle misure chiamava `VideoDecoder` e lanciava `ReferenceError` su ogni
   gradino** — il primo compreso — e `video.misura_massima` usciva **320×240**, la tela minima di
   §4.5. ⇒ Il server concedeva 320×240 e il desktop sarebbe apparso **in un francobollo**, senza una
   riga che lo spiegasse. Adesso su questa strada la capacità si **omette** (§4.3 lo permette): non
   si dichiara quel che non si è misurato.
2. ⛔ **`document.body.dataset.schermo = "acceso"` non veniva mai scritto**, perché su questa strada
   non si passa da `dipingi()`: la pagina sarebbe rimasta «in attesa del primo fotogramma» con il
   desktop già sullo schermo.
3. ⛔⛔ **Il risveglio del `<video>` era appeso ai fotogrammi presentati.** Un desktop sta fermo per
   secondi; il `<video>` finisce i dati, si mette in pausa, e `requestVideoFrameCallback` **smette
   di scattare** — perché scatta sui fotogrammi presentati. ⇒ La prima pausa del desktop avrebbe
   fermato l'immagine **per sempre**. Adesso si insegue anche quando arrivano dati nuovi.

⭐ **E la regola «si dichiara solo quel che dipinge» ha qui la sua prima eccezione dichiarata**
(`DECISIONI.md` §1.13, `LEZIONI.md` §1.9): su questa strada la sonda dovrebbe far *presentare* un
fotogramma a un `<video>` di prova, e sui motori mobili un `<video>` di prova **non presenta**.
⇒ Si dichiara sulla parola del motore, e il controllo si sposta dove il `<video>` è **vero**:
`Schermo.mse_veglia()` scrive in chiaro se dopo quattro secondi non è stato presentato nemmeno un
fotogramma. ⚠ La tela nera resta **spiegata**, che è l'unica cosa che la regola serviva a impedire.

#### La misura, su un browser senza WebCodecs — 25 secondi di desktop vivo

| | |
|---|---|
| fotogrammi consegnati → **dipinti** | 291 → ⭐ **250** |
| buchi | ⭐ **0** |
| coda del `<video>` | ⚠ 212 ms — coerente con il prezzo misurato in `07-b57` |
| tela | ⭐ 1270×704, **non** i 320×240 di prima |

⚠ E il banco ha avuto anche il suo difetto, dichiarato: muovere il puntatore **non fa fotogrammi**
— il cursore viaggia su un canale suo e i pixel del desktop non cambiano. `[M]` Un giro intero con
**un** fotogramma, e stava per dichiarare «non dipinge» di una strada che dipingeva quel che c'era.
⇒ Adesso apre un terminale che scorre.

#### ⛔ «Vedo il desktop ma non funziona l'input» — la tela non si nasconde

*L'utente, 21 agosto 2026, ed è la prima volta che su Firefox per Android il desktop **si vede**.*

⛔ **Tutto** l'input di questa pagina è agganciato alla `<canvas>` — `pointermove`, `mousedown`,
`wheel`, `contextmenu` e i quattro eventi del tocco — e le coordinate escono dal suo
`getBoundingClientRect()`. ⇒ Nascondendola con `display:none` per far posto al `<video>`, gli
eventi non arrivavano a nessuno e il rettangolo valeva zero: **il desktop si vede e non si
comanda**.

⭐ **La cura**: la tela resta **dov'è e com'è** — è la superficie che riceve i gesti — e diventa
**trasparente**; il `<video>` le sta **dietro**, incollato al suo rettangolo (`mse_posiziona()`, che
segue `cornice()`). ⇒ Su questa strada, per chi tocca lo schermo, non cambia niente: tocca la stessa
cosa di sempre.

⚠ E il banco ha avuto il suo difetto anche qui: cliccava a una coordinata scelta a occhio, che
cadeva fuori dalla tela — e avrebbe detto «il clic non arriva» di un clic mai dato. ⇒ Adesso il
centro della tela lo **chiede alla pagina**.

#### La misura finale, browser senza WebCodecs, desktop vivo

| | |
|---|---|
| immagine | ⭐ 351 consegnati → **196 dipinti**, **0 buchi**, tela 1270×704 |
| input | ⭐ **4 eventi al server**: la lettera, il movimento, e `PULSANTE evdev 272` premuto e rilasciato |
| coda | 50 ms |

⚠ Un fotogramma su due non viene presentato: è il `<video>` che scarta sotto un terminale che
scorre, **in software e senza GPU**. Sul telefono, che decodifica H.264 in hardware, il rapporto è
un'altra cosa — e lì la misura la fa l'utente.

#### ⛔ «Non si vede il desktop» — la cornice non veniva mai chiamata

*Subito dopo la cura dell'input: il desktop era sparito.*

⛔ `cornice()` è quel che dà alla tela la sua **misura sul vetro**, e sulla strada di WebCodecs la
chiama il disegno (`componi()`). ⇒ Su questa strada il disegno non passa di lì: la tela restava
larga **sedici pixel** — la misura con cui la `<canvas>` nasce nel documento — e il `<video>`, che
adesso le sta incollato dietro, la seguiva fedelmente **in un francobollo invisibile**.

⭐ La misura del fotogramma su questa strada si sa (è la tela concessa): si scrive in `f_l`/`f_a`,
dove le due strade la tengono, e si incornicia.

#### ⚠ E il banco era **verde** mentre l'utente non vedeva niente

`07-b58` contava i fotogrammi e leggeva i contatori: tutti buoni. ⛔ Non guardava **dove finisce
l'immagine sul vetro**, che è l'unica cosa che l'utente vede. ⇒ Adesso lo misura, e boccia due casi
distinti:

| controllo | che difetto prende |
|---|---|
| il `<video>` occupa una frazione ragionevole della finestra | il francobollo |
| il `<video>` è **incollato** al rettangolo della tela (±2 px) | i gesti che finirebbero nel posto sbagliato, perché la superficie che li riceve non sta dove si vede l'immagine |

`[M]` Adesso: `tela [1270, 704] · video [1270, 704] · finestra [1270, 705]`, 6 eventi di input al
server, 499 fotogrammi consegnati e 123 presentati, 0 buchi.

## ⭐⭐⭐ 21 agosto 2026, sera — **REMOTIX gira su Firefox per Android**

*L'utente, dopo sei giri di prove sul suo telefono: «non sei in grado di far funzionare Firefox per
android con remotix». Poi: **«Installa la suite android sdk, usa quella»**. ⭐ Aveva ragione due
volte — sul risultato e sul metodo.*

⭐ **La fotografia dell'emulatore**: dentro Firefox 154 per Android — la stessa versione del suo
telefono — c'è lo sfondo di GNOME, la barra in alto con l'ora `Aug 21 16:01`, e i due terminali
`REMOTIX-SCENA` che scorrono timestamp **vivi**. Desktop remoto, in movimento, su un browser senza
WebCodecs.

### ⛔ I tre difetti che solo Android poteva mostrare

`07-b58` (Firefox da tavolo con `dom.media.webcodecs.enabled=false`) prende quasi tutto, ma **non**
prende quel che è proprio del motore mobile. Questi tre sono usciti solo qui:

1. ⛔⛔ **La ricerca che non finisce mai.** L'inseguimento del bordo vivo scriveva `currentTime`,
   cioè una **ricerca** — e una ricerca vuole un punto di accesso casuale, cioè una chiave, che lì
   non c'è. `[M]` `cerca=true · pronto=1 · tempo=34,41 · buffer=0,00→40,34 · errore=no`, e
   **19 fotogrammi dipinti su 727**. ⇒ Non si salta più: si insegue con la **velocità**
   (`playbackRate` 1,25 finché la coda rientra). Costa un filo di accelerazione invece di uno
   scatto, e non chiede una chiave a nessuno.
2. ⛔ **La potatura del passato svuotava tutto.** `sb.remove()` per non tenere in memoria il già
   visto lasciava `buffer=nessuno` con 817 fotogrammi consegnati. ⇒ Tolta: qualche secondo di video
   in memoria è un prezzo che si paga volentieri, una pagina nera no.
3. ⛔⛔ **E `dipinti` non è «quanti se ne vedono».** `requestVideoFrameCallback` sui motori mobili è
   **strozzato**: `[M]` 46 scatti in 35 secondi mentre il desktop si muoveva. ⇒ Per due volte quel
   numero mi ha fatto credere che l'immagine fosse ferma. Il giudice, lì, è **lo schermo** — una
   fotografia — non il contatore.

### ⭐ E lo strumento resta: `banchi/07-b59-firefox-android.py`

Emulatore Android 14 con KVM, Firefox **154.0** per Android, e il giro completo da solo: accetta il
certificato, entra come «prova», lascia girare, e legge nel registro del **server** la riga che la
pagina racconta di sé — `MISURA §7.18 MSE: consegnati … dipinti … fermo= cerca= pronto= buffer=`.

⚠ E quel che **non** riproduce si dichiara: l'emulatore non ha la decodifica in hardware. ⇒ I
**numeri** del ritardo non valgono; vale il **comportamento** — dipinge o no, si ferma o no, e
perché.

⛔ **La lezione di metodo, e l'ha insegnata l'utente**: quando una prova richiede sei giri di una
persona, lo strumento sbagliato non è il prodotto — è il banco. Sei ore prima avrei potuto
installarlo.

### ⭐ Il giro completo, fatto da me — 21 agosto 2026, sera

*L'utente: «prova tu».*

| prova | esito |
|---|---|
| **Firefox 154 per Android** (emulatore, `07-b59`) | ⭐ desktop **vivo** — orologio `16:52`, terminali che scorrono; `fermo=false cerca=false pronto=3`, il tempo del video **avanza di 4,43 s in 5** |
| input da Android | ⭐ il tocco arriva: `PULSANTE codice evdev 272 rilasciato` nel registro del server |
| ritardo su Android (emulatore) | ⚠ **2,3 s** dal bordo vivo — ⛔ e il numero **non vale**: decodifica in software, scena pesante, tela 1080×2040 |
| **senza WebCodecs, da tavolo** (`07-b58`) | ⭐ **0,21 s** dal bordo vivo, 277 dipinti su 444, input e geometria verdi |
| **strada normale**, WebCodecs (`07-b51`) | ⭐ 4 controlli su 4 per motore, **intatta** |

⛔ **E il giudizio del banco è stato riscritto**, perché sbagliava: dava rosso sul contatore
`dipinti`, che su mobile è strozzato. ⇒ Adesso guarda quel che descrive davvero lo stato del
`<video>` — *sta suonando? sta cercando? ha dati? quanto è indietro?* — e ⭐ **confronta due
letture**, perché un'immagine che avanza e una ferma hanno lo stesso aspetto in una fotografia sola.

## ⛔ 21 agosto 2026, sera — **il giudizio dell'utente: Firefox per Android è incompatibile**

> *«Niente da fare, troppi problemi: disegno del desktop irregolare, input imprevedibile, dichiaro
> Firefox per Android incompatibile con REMOTIX.»*

⚠ **E la strada funziona**: il desktop si vede vivo e i tocchi arrivano — misurato poche ore prima
sullo stesso emulatore. ⛔ Ma *«funziona»* non era il traguardo: il traguardo è §0.1-bis, cioè
un'esperienza vicina a una sessione locale. A un `<video>` che **riproduce** non si può chiedere di
reagire come un decodificatore comandato a mano.

⇒ **Nel prodotto**: `VIA_MSE` non si accende più da sola. Su un browser senza WebCodecs la pagina
**dichiara che non si può**, e nomina l'alternativa (Chrome per Android). ⭐ Mezza esperienza è
peggio di un rifiuto spiegato.

⇒ **Il codice resta dietro `?disegno=mse`**, perché finché Mozilla non porta WebCodecs su Android è
l'unica prova che il problema non è nostro. Alla fase 13 si decide se buttarlo.

### ⭐ Che cosa resta di buono, e non è poco

| | |
|---|---|
| `07-b58` | REMOTIX su un browser **senza WebCodecs**, riprodotto da tavolo con una preferenza |
| `07-b59` | **Firefox per Android vero**, in un emulatore: certificato, accesso, misura e fotografia — da solo |
| `LEZIONI.md` §1.19 | chi apre chiude: i banchi lavorano sul desktop di una persona |
| la sonda che riconosce il nero, la cornice, l'input agganciato alla tela | difetti veri, curati, che valgono anche fuori da questa strada |

⛔ **E il costo si scrive**: sei giri di prove sul telefono dell'utente e una giornata, per una
strada che non entra nel prodotto. ⚠ La lezione non è «non andava fatto»: è che **la domanda "quanto
renderà?" andava misurata prima di costruire** — e il numero c'era già, dal banco `07-b57`:
centinaia di millisecondi contro un tetto di 50.

