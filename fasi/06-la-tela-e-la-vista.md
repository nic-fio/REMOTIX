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

## 5 · ⛔ What did NOT work

*It is filled in even when it looks bad. ⭐ And in this phase the most instructive part is not
the product's faults: it is the **benches that were green without looking**.*

### 5.1 · The two adversarial briefs that were REFUTED by the measurement

| the sentence to refute | outcome |
|---|---|
| *«the reattach re-hooks the devices and everything works»* (6.1) | ⭐ **holds** on normal input: the application opened before the detach receives **everything**, with exact coordinates. ⛔ It is false **only** for the *held down* state — and that is where the fault lay |
| *«the chain `figli_ritela()` → `cattura_ridimensiona()` holds»* (6.3) | ⛔ **FALSE**: with two `ADATTA_TELA` 25-35 ms apart — *«whoever drags a border sends exactly two in a row»*, and the code itself calls it «THE case» — **4 rounds out of 18** (then 2/18) leave the desktop **not fitted**, and the client waits for the **3 s** bottom to receive `NON_ORA`. ⚠ On the other hand *«the discarded frames are zero»* **holds**: 0 in all rounds |
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
none reaches the bottom. ⇒ ⭐ **Contention really moves this scene**, and the *«green holds under
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
> ⭐ **And it is known why, from the source**: the line sits behind a bottom that re-arms **only when
> the pair (canvas in force, frame size) changes** — and under that fault **it never changes**. First
> frame: the line comes out. From the second to the 799th: identical, bottom already armed, **silence**. ⇒ It is **once
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
> round that had opened the case. **4** came out, and that is right: the bottom re-arms at every new pair
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

*The last ring missing for colour: not from the stream to the glass, but **from the desktop to the glass**.*

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

### 5.13 · ⭐⭐ 22 Aug — **the seat ceiling is 30 seconds, not 75** — and the sentence of §5.3 about the frozen tab is false

*The `[?]` that bit every day: «the session's seat is one, and the previous one stays
attached for about twenty seconds» was folklore. `[M]` port 7801, `provar7`, real GNOME headless,
load 0.23-1.40.*

| the client goes away… | seat released | another client gets in |
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
life. ⇒ **The seat is never freed.** `[M]` 26 out of 26 in 745 s. ⚠ The product counts **packets**,
not RCP bytes — and it is a right and documented choice, ⛔ but **it is not what §5.3 tells**.

#### ⭐ The line for whoever writes benches — it is the thing everyone needed

> ⛔ **After a client has gone away badly, do not retry before 35 seconds.**
> ⛔⛔ **And if its process is still alive, 35 s are not enough: the seat stays taken for up to half an hour.**
> It is checked with `pgrep`, not with `pkill`.
> ⭐ **But waiting is almost never needed**: if the server is yours, **restart it** — the seats live in the
> process's memory, the graphical session lives outside: `[M]` the first attach after a restart reaches
> `SESSIONE` in **1.03 s**. ⭐ And if the client is yours, **make it say farewell**: **5-7 ms**.

#### ⛔ And the routes are TWO, with the same number — it is the mechanism behind the false reds

In 4 detaches out of 7 the seat was released by **the silence clock**; in the other 3 by the **death of the
QUIC connection** (30.00 s exactly). ⚠ **Which one arrives first is heads or tails**, and they leave **different log
lines and states**. ⇒ A bench that waits for the line «detached for silence» to know that the
seat is free **is red one time out of two**.

⭐ **And the positive control, without which the 30 s would be worth nothing**: with the inactivity clock
shortened to 25 s the same case released the seat at **19.8 s** with a different farewell ⇒ the bench
**can see** a release at a time other than 30.

⚠ **And what is missing, declared by the author**: no browser. The hypothesis he leaves behind is that
the «~75 s» were **~45 s of Firefox not dying + 30 s of the product**. It closes in a minute, with
a browser in hand.

#### ⏳ Four product things found along the way, not cured

| | |
|---|---|
| ⛔ `2 = RIPRESA` **never comes out** | the byte is a **constant 1** at the only point that builds the message. `[M]` 12 reattaches to the same child: **state 1, always**. It is form **E1** ⇒ whoever writes benches **cannot** use it to know whether they have a new desktop |
| ⛔ the **two routes** with the same number | above: two lines and two states under the same fact, racing |
| ⛔ the **live client holds the seat** | up to the half hour of inactivity — measured ≥ 745 s |
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

