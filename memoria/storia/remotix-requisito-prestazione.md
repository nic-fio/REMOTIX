---
name: remotix-requisito-prestazione
description: "REMOTIX — since 7 Aug 2026 the user sets the NUMBERS and the technique serves them: 30 fps at 1080p minimum, 60 fps at 4K desired. Phase 10 is reset and the approach of phase 9 is judged wrong"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2f8f83b6-a01f-43c3-ac38-668849574507
  modified: 2026-08-07T17:36:59.417Z
---

On **7 Aug 2026, at the end of the day**, the user turned the project's way of working upside down:

> *«Adesso scrivo quello che voglio, tu decidi cosa ci vuole per ottenerlo, e non dirmi i dettagli
> tecnici che non li capisco. Le soluzioni tecniche devono essere prese in funzione di questi
> vincoli, non il contrario.»*

| | |
|---|---|
| **MINIMUM** | **30 frames per second at 1080p, 24 bits of colour** |
| **DESIRED** | **60 frames per second at 4K, 32 bits of colour** |

It is in **§3.1 of `SPECIFICA.md`**, and the feasibility count — what is reachable, on which
clients, at what price — in **§3.1-bis**. A technical choice is justified **by showing that it brings
one of those two numbers closer**; if it does not move them, it is not done.

**Why it happened, and it is the part not to lose.** Phase 9 optimised the **milliseconds of
CPU per frame** (41 → 6) without anybody ever having measured the **frames per second
delivered**. Measured on the evening of 7 Aug: **18**, and it is not the encoder that limits them — the capture
delivers 17.7 and the server sends 17.9, that is **everything the compositor gives is sent**.
A whole phase spent on a piece that was not the bottleneck. The user: *«abbiamo sbagliato
proprio l'approccio sulle performance»*.

**State left on 7 Aug 2026:**

- **phase 10 RESET** at the user's request: code back to the closure of phase 9, benches
  removed, box in `PIANO.md` with the three reasons for the failure. What remains are **the measurements** in
  `REFERENCE.md` (R31, §5.1, §10.2) and **the user's decisions**: adaptive resolution out,
  AVC444 out (it had given him luminance problems), region encoding out, and **the 10 Mbps
  are a floor, not a budget** — «spending less bandwidth» is not a gain for this product;
- **phase 9 under judgment**: not reset, but its approach is the one the user disputes. The three
  roads proposed (remove only zero-copy / reset everything / reset the approach) are
  in the last part of the conversation; the user in fact chose the third, by setting the numbers;
- **the server** (`192.168.0.2:3392`) is in the state of the closure of phase 9: zero-copy **off**,
  constant-bandwidth bitrate, plus only the locale correction (without it, the session's terminal
  does not start).

## ✅ THE TASK WAS CARRIED OUT ON THE EVENING OF 7 AUG 2026

*The full tables are in **R32** of `REFERENCE.md`; the bench in
`/media/REMOTIX/tmp/banco-compositori`, outside the product (own PipeWire meter, client for
KWin's protocol, screencopy client for wlroots).*

**The answer, in one line: the 18 frames were ours.** REMOTIX declares to the capture a maximum
of **30**, and Mutter delivers **18**. Declaring **60** it delivers **37**. One gets about
**six tenths** of what is asked for, and it does not go above 60.

| | |
|---|---|
| the client draws | **60 fps**, on a virtual monitor at **60.000 Hz** |
| **Mutter** delivers | **35–37**, the same from 1080p to 4K |
| **KWin 6.3.6** (DMA-BUF) | **59–60**, at every resolution |
| **sway / labwc** (wlroots) | **61** at 1080p and 1440p, 40 at 4K |

**What fell**, and must not be stood up again: resolution and colour depth **cost
nothing** to the capture (4K performs like 1080p, BGRA like BGRx); zero-copy **does not bring frames**
(36.6 against 34.0), it brings CPU; GPU load does not move the number; with the desktop still the delivery
is **zero**, as per specification.

**The user's minimum is reachable** (37 > 30) by changing one line. **The desired one is not on
GNOME**: the ceiling is Mutter, which loses 40 % of the redraws — and **phase 11 also becomes the road
to 60 fps**, because the other two compositors do not have that ceiling.

## And the whole chain, measured right after

With `--fotogrammi 60` instead of 30, **all the way to the client**: 1080p from **18.7 to 32.4** — the minimum
exceeded. Two things that come out of it and are worth something by themselves:

- ⛔ **zero-copy does not bring frames**: 31.5 against 32.4. It cuts the CPU per frame from 16 to
  3 ms. R29 is picked up again for consumption, not for smoothness;
- ⚠ **4K stays NOT measured**: the bench gives 17, but the cap is the test client which decodes in
  software (`in volo 2 di 2` over 835 samples, server at 0.08 cores). The regulator of phase 7 on a
  fast link grants **2 slots**, so the throughput is the one at which the client acknowledges.
  A client with hardware decoding is needed before saying anything about 4K.

## ✅ Closed on 7 Aug 2026: turned on, judged on the three clients, and put in the code

| Client | Codec | Rhythm from the log | User's judgment |
|---|---|---|---|
| `xfreerdp3` | AVC420 | 32–33 | fine |
| **mstsc** | AVC420 on GPU | **29–33** | «va benissimo» |
| **RDM** Android | RemoteFX Progressive | **23–29** | «performance eccellenti» |

**The 60 is in `main.c`**, not in `/etc/default/remotix` (which lives in RAM and would have been lost at the first
reboot). Binary redeployed and verified with the default configuration only: **33.3 fps at
1080p** on the whole chain.

**The prediction on RDM was wrong** — «neutral, maybe worse on audio» had been predicted because
of RemoteFX Progressive in software — and the reason why it was wrong is the thing to remember: **the
18 frames were a cap of ours upstream of everything**; with that removed, every client took as much as it
could handle, and had some to spare. Neither of the two sides was at its limit: the number we
declared was.

⛔ **Still to do at once**: the 60 lives in `/etc/default/remotix`, that is in RAM. It must be brought **into the
code** (`main.c`, `fotogrammi = 30`), or at the first reboot it is lost — exactly as the
zero-copy line was lost. See [[remotix-prove-sul-banco-non-sull-utente]] rule 6.

See [[remotix-oltre-rdp]] and [[remotix-fase9-ripresa]].
