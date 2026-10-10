# DECISIONI — the register of what was decided, and by whom

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without the card and colour conversion with swscale; those of encoding on the card and of audio stay, because the new flow is identical (comparison of 30 Sep 2026). User's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

*Opened on 8 Aug 2026, on the first day of REMOTIX.*

This document does not explain and does not persuade: it **records**. What it is for, in one line: a
decision taken by word of mouth and not written down is a decision that in two weeks nobody knows any more
whether it was taken, and that the first doubt reopens from scratch.

Every entry says **what**, **when**, **why** — and above all **with what degree of
certainty**, because the difference between «the user said yes» and «it is a consequence I
drew myself» is precisely the difference that `LEZIONI.md` §2.3-quater says not to lose.

| Mark | Meaning |
|---|---|
| ✅ **Decided** | the user said yes, explicitly. It is not reopened without a measurement that refutes it |
| 🔸 **Derived** | logical consequence of a ✅ decision, written in the documents but never spoken. If I am wrong, it is corrected without discussion |
| ❓ **Open** | question asked, answer not yet given. **It is not a decision**: it is a hole that someone has to close |

And the marks of the *reasons* stay those of `CODER.md` §5: `[M]` measured, `[R]` read in the
code, `[S]` read in a specification, `[?]` hypothesised.

---

## 0. The principle that produced the others

### 0.1 ✅ We depend on the compositor, not on its surroundings

*8 Aug 2026. «Voglio evitare di smettere di correre dietro ai compositor e cominciare a
dover inseguire i display manager».*

It sits at the top because it is not one decision among the others: it is the criterion by which several
are taken, and at least three of those written below descend from this one.

| | |
|---|---|
| **chased** | the **compositor**, because only it delivers the frames and accepts the input. `mutter.c` and `kwin.c` exist for this and will keep existing |
| **not chased** | the **surroundings**: screen lockers, idle daemons, power managers, display managers. They do the same thing in four ways, with four configurations that rewrite themselves |

**The test, before leaning on a mechanism:** *how many different implementations would I have
to chase, and how much does it cost me to do it myself?* Four divergent ones and a small cost ⇒ we do it
ourselves, once.

⚠ **It is not a licence to rewrite.** `logind`, PAM, PipeWire, `libei`, `xkbcommon`, QUIC:
only one each, the same everywhere. There `CODER.md` §4.1 holds with no discount, and writing our own
would be the defect that rule forbids.

**Where it has already decided:** §4.3 (the lock is ours instead of the desktops' one), §5.1
(resizing does not touch the compositor), and in the negative §1.1 — stopping chasing other people's
clients was the same reasoning applied to the wire.

> ### ⛔⭐ AND ON 17 AUG 2026 IT PRODUCED ITS CLEAREST CASE — §5.1-bis
>
> *«Non voglio mettere delle eccezioni nel progetto.»* Live resizing worked on
> Mutter (`[M]` 6 ms) and **could not be done** on KWin ≤ 6.7.4. ⇒ It left the product instead of
> staying behind a switch. ⚠ **The rule drawn from it, and it holds going forward**: if a
> feature can be done on one compositor and not on another, the question to bring to the user is not
> *«how do we hide it»* but *«do we keep it?»* — and the answer so far has been no. We depend on the
> compositor, and precisely for this reason **we do not depend on which one**.

*Also written in `CODER.md` §4.1-bis, with the matching check in `REVIEWER.md` E11 —
the two must stay paired, otherwise it is an unchecked rule.*

---

### 0.1-bis ✅ REMOTIX does not chase browser defects — 21 Aug 2026

> *«REMOTIX non può rincorrere i bug dei software. Se Firefox offre performance scadenti (ma
> comunque REMOTIX funziona) c'è poco da fare, l'utente Android deve accettare le scarse
> performance di Firefox o passare a Chrome.»* — the user.

⭐ **It is the twin of §0.1, moved one level up**: there it says which piece of the system is chased and
which is not; here it says how far we go for an **engine** that does worse than the others.

| | |
|---|---|
| **done** | the product uses the best route that browser offers, and **declares** what it found |
| **not done** | ⛔ no parallel paths are built to make up for what an engine lacks, and the others' latency is not sacrificed to even it out |

⇒ **Latency is not the same on every engine, and that is fine.** If REMOTIX performs worse on one browser,
the user has a choice in front of him — accept it, or use the other browser — and that choice is **his**,
not ours.

⛔ **And the uncomfortable consequence is written down**: «fully supported» stops meaning «the same
everywhere». It means *it works, and you know under what conditions*. ⇒ What the product must guarantee
on every engine is **telling the truth about itself** (§0, and the line of the page that names WebCodecs
when it is missing), not performing the same way.

⚠ **The fact that produced it**: `[M]` Firefox for Android has no WebCodecs — neither `VideoDecoder` nor
`AudioDecoder` — and the only alternative, MSE, costs **+225 ms on Firefox and +415 ms on Chrome** on the
median (`fasi/06`, bench `07-b57`), against a declared cap of 50 ms.

⏳ **And one thing this decision does NOT establish**, so it stays open instead of being deduced:
whether the MSE path should be **written** or not. The sentence presupposes *«ma comunque REMOTIX funziona»*,
and today on Firefox Android it does not work at all; but «do not chase browser defects» cuts
precisely against building it. ⇒ See §7, the open question.

### 0.2 ✅ Agentic development, with adversarial review at three moments

*9 Aug 2026. «Ricorda inoltre il metodo di lavoro: sviluppo agentico e review avversariali».*

The work is done by two kinds of agents — `CODER.md` and `REVIEWER.md` — and **when** the
reviewer steps in is in `PIANO.md` §0.4: on the **bench** before the product exists, on the **code**
before it is measured, on the **phase document** before closure.

⭐ **And here review has one more job than in a normal project.** By throwing away RDP we
lost the external referee: in v1 `mstsc` complained for free when we misunderstood the specification.
Now client and server are ours, and **two programs written by the same hand that agree with each other
confirm nothing**. The three things that replace that referee are `RCP.md` (written), the
wire validator (mechanical) and **adversarial review** — which is the only one of the three able
to notice that the two sides share the **same** misunderstanding.

The four practices that make the adversarial stance a concrete thing instead of a tone: the
reviewer receives the code and the specification **but not the reasoning** of whoever wrote it, which
would otherwise anchor; one tries to **break**, building the input that would violate the invariant; a
finding is closed with **a measurement**, not with a discussion; and a green review is **«I found
nothing»**, never «it is right».

### 0.3 ✅ The Linux client before the Android one — because of the cost of testing

*9 Aug 2026. «Il server lo si sviluppa ovviamente avendo in mente i 2 client, ma resta il
problema dei test: per android è molto più complicato, mentre lo è meno per linux».*

The Android track moves **from after phase 4 to after phase 9**, and can then proceed in
parallel with the phases of the new desktops (11-12), which are server work and do not touch the wire.

⛔ **But the move takes away a defence**, and it must be compensated. Android was not at phase 4 to
finish sooner: it was the **second reader of the protocol**, the only thing able to notice that
server and client share the *same* misunderstanding (§0.2). Without it, everything built
between 4 and 12 would rest on a protocol validated by **a single** implementation.

🔸 **The two compensations:**

1. **the test client**, added to phase 1 — a few hundred lines, **in a language
   different from the server's**, written by reading `RCP.md` and **never** the C. It does the same job at a
   tenth of the cost. The validator says «this byte does not conform»; the test client says
   **«you two agreed on something the specification does not say»**;
2. **the Android probe**, in phase 2 — ~50 lines that give an HEVC Main10 file to MediaCodec and
   say whether the phone decodes it **in hardware**. It is the only Android unknown that cannot
   wait, because it is the wall v1 died against. And it is declared successful only with proof that
   it really is hardware: «it instantiated a decoder ⇒ it is in hardware» is error form **E1**.

⚠ **The residual risk, declared and accepted**: there remain things only Android can reveal and that
no reader replaces — MediaCodec under load, real touch under the fingers, the IME, the
battery, the network changing in the pocket. Those arrive late.

> ⛔ **Superseded on 9 Aug 2026 by §1.6**: there are no longer two clients, so there is no longer
> an order between them. ⭐ **But the two compensations survive, and one is worth more than before**:
>
> - **the test client** stays, and is **more necessary**, not less. Before, it was the second reader
>   next to two implementations; now the client is **only one**, so it is the **only** thing
>   written from the specification instead of from the code;
> - **the probe** stays and changes target: from «does the phone decode HEVC in hardware?» to
>   **«does the phone's browser decode it in hardware?»** — same question, one layer further
>   out, and **without an APK**. The other two browser unknowns are added to it (§1.7 and §1.6).
>
> ⚠ And the residual risk above **does not lapse, it moves**: MediaCodec under load, the IME, the
> battery and the network in the pocket remain things only the real phone reveals. What changes is that now it
> reveals them **by opening a page**, which costs half a day instead of a phase.

---

### 0.4 ✅ ⭐⭐⭐ The things of «later» have a place of their own — `MASTERPLAN.md`

*Decided by the user on **25 Aug 2026**, while phase 11 was opening:*

> *«Per gli altri DE non ci portiamo dietro questo buco, per GNOME potremmo fare una manutenzione
> evolutiva al termine del progetto, insieme all'integrazione di altre funzioni. Potrebbe essere
> utile creare un documento `MASTERPLAN.md` dove annotare tutte queste cose da fare al termine del
> progetto.»*

⭐ **[`MASTERPLAN.md`](MASTERPLAN.md)** is born: the list of the works that are tackled **once the product
is finished** — improvements, choices deliberately postponed, features that were not in the initial pact.

#### ⛔ The real problem it solves, and it is not the order

⛔ **A thing declared and not put on the agenda becomes archaeology.** The case that produced this
decision is §2.5-bis: on 13 Aug 2026 it was discovered that *«the GNOME cap is not Mutter's, it is
ours»*, ⭐ **it was written down honestly the same day**, and then nobody went back to it — because
phases 8, 9 and 10 arrived, each with its own theme. ⇒ **It was not hidden: it had no place.**

#### ⛔⛔ The rule that keeps that document standing

> **Every entry says what it costs NEVER to do it** — and it is the only information needed, because it is
> what separates *«it must be done»* from *«it would be nice»*, and that choice is the user's.
>
> ⚠ And the reverse: **an entry whose cost of «never» is zero is deleted.** A list of «later» that
> grows and never shrinks is the drawer where things go to die.

⚠ **And it does not widen the number of registers**: `MASTERPLAN.md` **decides nothing** and copies nothing.
The decisions stay here, only once (§0 of `README.md`); the plan of the phases stays in
`PIANO.md`; ⛔ **what must happen BEFORE the end does not go into the masterplan**, it goes into a
phase.

### 0.5 ✅ ⭐⭐⭐ The desired target is asked of ALL desktops, the same — and those that do not give it are revisited later

*Decided by the user on **25 Aug 2026**, right after §0.4:*

> *«Rendiamola semplice: il 4K/60 fps è il tetto che chiediamo a tutti (desiderio). Per i prossimi DE
> lo chiediamo, per GNOME dovremo tornarci.»*

⭐ **The target is one and the same for all four**, and it is the **desired target** already decided on 8 Aug 2026
(§2.2): **4K · 60 frames per second · 10 bit**. ⛔ **No target tailored per
compositor** — it is §5.1-bis applied to the numbers: *no exceptions per compositor*.

| | |
|---|---|
| **the new desktops** (KDE, XFCE, LXQt) | ⭐ **nothing to do**: the product already asks anyone for 60. If they deliver it, the hole on them **does not exist**. `[M]` KWin gives **58.9** without being asked for anything special |
| ⛔ **GNOME** | at 60 it halves them (**31.5**), and to get 60 one would have to **ask it for 90** — which the product cannot do (§2.5-bis) ⇒ ⚠ it was `MASTERPLAN.md` **M1**, ⛔ **removed by the user on 21 Sep 2026** (*«M2, M3 e M5 sono gli unici punti da conservare nel masterplan»*): the fact stays, the «later» work does not |

⚠ **What this decision does NOT do**: it does not promise 4K/60 on GNOME and does not remove it from the goals.
§2.5-bis stays in force as it is — *«on GNOME the desired target is not promised»* — ⛔ **with the corrected
reason**, which since 13 Aug 2026 is no longer *«Mutter cannot make it»* but *«we do not ask it of it»*.

⭐⭐ **And the part that does not wait for the end**: at the entry of every new desktop — phases 12, 13, 14 —
**one single question is asked and the number is written down**: *«I ask you for 4K at 60: how many do you give me?»*
⛔ If it gives half, **it is a GNOME too**, and one knows it on the first day instead of discovering it by
chance eleven days later — which is **exactly** how it went on GNOME. ⇒ It is in `PIANO.md`, in the three
phases, and **costs not one line of product**.

⛔ **SUSPENDED on 21 Sep 2026, by the user**, together with M1: *«sì, saltala. Poi una volta che
avremo completato il progetto, penseremo alla sua evoluzione, ma l'obiettivo primario è arrivare ad
avere un prodotto funzionante sui 4 DE principali»*. ⇒ On XFCE and LXQt the question **is not asked**; the
KDE number (58.9) stays written.

### 0.6 ✅ ⭐⭐ One machine, ONE desktop — machines with several desktops together are out of scope

*Decided by the user on **20 Sep 2026**, at the opening of phase 13:*

> *«le' stato attuale remotix e' destinato a sistemi con un solo DE installato. I sistemi con DE
> multipli installato sono per il momento fuori scope»*

⭐ **What is gained, and it is the reason the decision is worth it**: `sessione.c` recognises the
desktop **by looking at the PATH** (`riconosci_desktop()`, `src/sessione.c:275-303`). With one desktop only
per machine that recognition is a **question with only one answer** — there is nothing to
arbitrate, no preference to configure, no `--compositore` option to put back (v1 had it,
`fondamenta/remotix-c/src/main.c:456-459`; v2 removed it and **it is not put back**).

⚠ **The ambiguous case stays, and stays as it is**: if there were two desktops on the machine, the product
picks one and **declares it in the log** (`src/sessione.c:287-291`). ⛔ It is not a cure and must not
become one: it is a **line that tells the truth** about a machine that is out of scope.

⛔⛔ **But what this decision does NOT cover is the fault that opens phase 13**, and it must not be confused
with it: a machine that has **only XFCE** today is not an ambiguous case — it is an **empty** case. It falls
into the last branch of `riconosci_desktop()` (`src/sessione.c:295-299`), the product **silently falls back
to GNOME** and then launches `gnome-session`, which does not exist on that machine. ⇒ One desktop
only, recognised correctly, is **precisely** what this decision demands, and it is the heart
of increment 1.

⭐ **And it is not a new entry: it is the same as §4.6-duodetricies, widened.** On 18 Sep it
was decided that the product **does not offer a choice** between desktops; today more is said — machines
with several desktops **are not a target**. ⇒ §4.6-duodetricies stays in force for the how (one
recognises from what is installed, and the ambiguous case is declared in the log); this one says the **how
far**, and the postponed feature is still in `MASTERPLAN.md` **M5**.

---

## 1. The protocol

### 1.1 ✅ RDP dies. The protocol is ours.

*8 Aug 2026. «Windows e tutto quello lo riguarda muore».*

The line `== NO WINDOWS ==` is not a side note: it is the lever that removes the three walls against
which v1 stopped, and which were all three RDP's and not the problem's — the H.264 cap
(`fondamenta/documenti/SPECIFICA.md` §5.1), the Android client that decoded in software, and
full colour out of reach.

**The price, accepted:** the protocol has to be designed as well as written, and the clients have to be
written from scratch — the Android one is a project of its own, not a feature.

**What lapses with RDP:** EGFX, `MapSurfaceToOutput`, RemoteFX Progressive, AVC444, NLA and
CredSSP, MS-RDPEDISP, `ERRINFO_*`, FreeRDP 3 as a constraint, the matrix of the three third-party clients,
and `fondamenta/documenti/REFERENCE.md` almost entirely.

### 1.2 ✅ The protocol is called RCP — *Remotix Control Protocol*

*8 Aug 2026, chosen by the user.*

```
librcp.so
rcp_frame_t · rcp_connect() · rcp_session_t
stretta di mano:  RCP/1
```

Two provisional names preceded it on the same afternoon and were discarded: **FILO**
(«proprio non si può sentire») and **RXP**. They are cited here only so that whoever finds those names in
a note knows this is what was being talked about, and not something else.

⚠ **A minor collision, to know before naming the binaries**: `rcp` is the name of a
historic Unix command — the remote copy of the `rsh` family — today uninstalled almost everywhere
and never active by itself. It touches neither the protocol nor the library; it only concerns a possible
command-line command, which is better called `remotix` and not `rcp`.

⭐ **And the name says something right**: *Control*, not *Display*. The protocol does not carry only
pixels — it carries input, clipboard, geometry, farewell and session state, and video is one of
its channels. It is the difference between RCP and what RDP made people believe it was.

### 1.3 ✅ Trust in the server: remembered silently, never confirmed by hand

*9 Aug 2026. «Se inserisco i dati fondamentali (ip, porta, userid e password) so che quel
server è mio. La sicurezza va bene, ma qui non stiamo costruendo un sistema basato su standard
militari».*

**No fingerprint comparison, no certificate authority, no domain.** The user
types address, port, user and password, and that is it.

The certificate is needed anyway — QUIC demands TLS, there is no «without» option — so the
server generates a self-signed one for itself at installation. The client, on the first connection,
**accepts it silently and remembers it**; from the following times on, if it changes, it warns. It is what
SSH does, and it is not seen until it is needed: it costs **zero interaction** and covers all connections
except the first.

⚠ **The clarification that was made and rejected, kept so that the decision is understood:** the
risk is not typing the wrong address, it is that someone intercepts the connection to
the right one. The first connection stays exposed. **The risk was assessed and accepted**
by the user for the intended scenario — own server, own network or VPN.

🔸 **Two consequences that cost nothing and are not seen:**

1. **the password does not leave before** the server has proved to be yesterday's one. It is
   invariant I3 — the guard starts from denied — applied to the order of the handshake.
   With RDP the credentials leave early and the certificate warning arrives when you have already
   given them; here it is only a matter of what is written first on the wire;
2. **a real certificate, if there is one, is used and is worth more** — the administrator's business, not
   the user's, and it adds no step for anyone.

⚠ And a trap already paid for by v1, not to be repeated: *«a shared TLS certificate killed the
server at the second connection; a single-connection test stays green forever»*
(`LEZIONI.md` §2.1). The handshake bench is done **with two connections**, not with one.

> ⚠ **Reread on 9 Aug 2026, after §1.6.** The mechanism described here — accept silently the
> first time, remember, warn if it changes — **stays exact and we no longer write it: the
> browser does it**. What changes is the price: the first-time acceptance **is not silent**,
> it is a warning with a click (§1.7). And the *«zero interaction»* promised here still holds only for whoever
> puts in a real certificate, that is for the case this entry already called «the
> administrator's business».

### 1.4 🔸 The session does not know the codec: the connection negotiates it

It descends from 1.1 and from §4. The stage produces frames; each connection attaches its own
encoder to it with the capabilities of **its** client. If the codec were a property of the
session, resuming from a different device — phone in the morning, laptop in the afternoon
— would require redoing the session, which is exactly what persistence must avoid.

### 1.5 🔸 The closures of RCP/1 — twenty-six holes plugged before the first line of code

*9 Aug 2026, at the opening of phase 1. They are consequences written by me reading `RCP.md` with a
single question — **do two people who read it on their own write the same byte?** — and the answer was
no. All 🔸: they are corrected without discussion.*

⛔ **The census in one line**: of the **twenty-two** messages the protocol had in the first
draft, **two** were defined byte by byte — the frame and the audio datagram. The other twenty
had a name and a description in words. The least specified channel was precisely the
**handshake**, that is the one phase 1 has to write. The detail is in `RCP.md` §0-bis;
here are only the choices that could have been made otherwise.

⚠ **And today's total is no longer twenty-two: it is twenty-six**, all defined byte by byte (`RCP.md`
§0-bis, box corrected by finding **R1.29**). The four added on 9 Aug are
`RICHIEDI_CHIAVE` and `TELA` (§5.2, §7.1) and ⭐ **`BANCO_MARCA` and `BANCO_ESITO`** (§7.5, the night of the
9th). *The distinction between the two totals dates from 10 Aug 2026, finding **R11.13**: this line said
«of the twenty-two messages of the protocol» in the present tense, and a reader who checked completeness
by counting from here — as R1.29 declares it did on §0-bis — found four fewer than
those that exist.*

⚠ **And the count in the title, declared so that nobody invents another one** *(night of 10 Aug
2026)*: the numbered rows below are **twenty-six**, of which row **8** has *fallen* — the closures in
force are **twenty-five**. ⛔ And the twenty-six of the title **is not** the twenty-six of the messages in the
paragraph above: they are two different counts that today give the same number, and a number without
its denominator is what `LEZIONI.md` §1.9 point 4 forbids.

| # | The choice | Why so | Where |
|---|---|---|---|
| 1 | **the port is 7447**, and they are ⛔ **two listeners with the same number**: **UDP** for HTTP/3 and WebTransport, **TCP** for the first load of the page | free in Trixie's `/etc/services` `[M]`. `[?]` IANA not checked. ⚠ *This row said «the port is **UDP** 7447» and nothing more, while `RCP.md` §2.4 has declared the two listeners since 9 Aug: whoever implemented from here opened only UDP, and **the page would not have been served at all** — that is the symptom «`https://192.168.0.2:7447` does not answer», which names neither the port nor the transport. Aligned on the night of 10 Aug 2026 by the **rereading of all twenty-six rows** that `R11-documenti.md` §C point 6 prescribes — `[R]` **N1**, and it was not among R11's findings* | `RCP.md` §2.4 |
| 2 | **strings** are a `u16` length plus UTF-8, with no terminator | the terminator invites passing the string to `printf` without copying it, and a null byte in the middle becomes a silent truncation | §6.0 |
| 3 | **the high byte of the `tipo` tells the channel** of a stream | whoever receives a unidirectional stream must know what is inside **before** reading it, and it was not written anywhere | §2.5 |
| 4 | **no 0-RTT** | 0-RTT data is replayed, and the second message is `CREDENZIALI`. The gain is one network round trip on a session that lasts hours | §2.3 |
| 5 | `disable_active_migration` **is not sent** | declaring it silently switches off the reason QUIC was chosen | §2.3 |
| 6 | ⛔ ~~stream credit ≥ 256~~ → **the server grants the client ≥ 16** | *corrected on the evening of 9 Aug (**R1.14**): 256 was a parameter we demanded from the client, and **with a browser it is the browser that chooses it**. Whoever implemented by reading this row wrote 256 where `RCP.md` says 16* | §2.3 |
| 7 | ⛔ ~~the fingerprint is computed on the public key~~ → **on the certificate in DER form** | *corrected on the evening of 9 Aug (**R1.14**): `serverCertificateHashes` compares the fingerprint **of the certificate**. Whoever published that of the key got a comparison that **never matches**, with the symptom «WebTransport does not connect» and no error naming the fingerprint. ⚠ And the reason that stood next to it — «a certificate reissued with the same key must not trigger the warning» — **has lapsed**: with the fingerprint published by the page, every reissue changes it anyway* | §4.1-bis |
| 8 | ⛔ ~~the client switches off the X.509 checks by default~~ | *fallen on the evening of 9 Aug (**R1.14**): the client is a page, and has no X.509 check to switch off. It was a leftover of the draft with a client of our own, remaining in the document that says what was decided* | — |
| 9 | **`RESPINTO` is the farewell of authentication**, and ⛔ **the server** does not send another one | §4.4 and §8.2 overlapped: two implementations could guess differently, or **the same because written by the same hand**. ⚠ *It said «and no other follows», without saying whose: the prohibition is the **server's**, and it applies to `CONGEDO`. **To the client, after `RESPINTO`, there remains one thing it can say, and it is precisely `CONGEDO`** — the prohibition of §4.4 is on **retrying**, not on taking leave (clarification of 10 Aug, bench **B11**, which had put a red on the page while it was doing what §8.1 imposes on it). Whoever implemented the page by reading this row stayed silent, and B11 demands the farewell **once per engine**. Aligned on the night of 10 Aug 2026 by the same rereading — `[R]` **N2**, and it was not among R11's findings* | §4.4 |
| 10 | **a single credentials attempt per connection** | the limiter counts one thing only, and no state machine is needed for repeated attempts | §4.4 |
| 11 | ⛔ ~~**rate limiting: 5 in 5 minutes, then a 30 s wait that doubles up to 15 min**, with two counters~~ → **REPLACED on 10 Aug 2026 by §1.9**, which is ✅ the user's: three failed authentications and the address is banned for **12 hours**, with **one** counter only and without the per-user-name one. ⭐ **The rest of the row survives intact**: **the fixed second of delay on every answer, even when it is «admitted»** | the fixed second closes the `[?]` of `SPECIFICHE.md` §4.2 and removes **timing** as a channel: without it, the distinction between «non-existent user» and «wrong password» that §4.4 forbids writing can be read with a stopwatch. ⚠ And on that second there is a measurement that does not add up: B8 gives a median of **2636 ms**, that is, what governs the timings is **PAM** — `[?]` open, and the ban does **not** close it | §4.4-bis, §1.9 |
| 12 | **the canvas MUST have even sides**, between 320×240 and 7680×4320 | an odd size is rounded **by the encoder, silently**: two sizes under the same label, that is error form **E2** | §4.5 |
| 13 | **three time caps on the handshake** (5 s, 60 s, 10 s) | a connection stuck halfway holds a slot; and QUIC's 30 s measure the **silence of the network**, not a client that is not doing its job | §4.6 |
| 14 | ⛔ **keyframes**: `tipo` `0x0301`/`0x0302` and the message `RICHIEDI_CHIAVE` | **it was not a gap, it was a design defect**: §5.1 allows dropping a frame, and the video is compressed with prediction — dropping one leaves the decoder broken until a keyframe arrives, and there was no way either to say so or to ask for one. It costs **zero bytes**: it goes into the values of a field that already existed | §5.2 |
| 15 | audio is **48 kHz, 2 channels**; ⛔ **the blocks are 20 ms for Opus and 5 ms for PCM**, and PCM is **s16 little-endian** | «Opus, with PCM as the baseline» is not a format. And the endianness of the payload is the only exception to network order: declaring it is what prevents two implementations from silently diverging. ⛔ *This row said «20 ms blocks» for **audio** and reserved only the endianness for PCM: it is the reading that finding **R1.1** — the most serious of the 9 Aug review — declares **lethal**, because 20 ms of PCM make 1920 samples, 3840 bytes, plus 12 = **3852**, and a QUIC datagram cannot be fragmented on a ~1200-byte path. **PCM audio would never have left, on any network** — and PCM is the positive control of Opus. `RCP.md` §5.3 had been corrected on the evening of the 9th; this row had not. Aligned on 10 Aug 2026, finding **R11.12*** | §5.3 |
| 16 | the clipboard stops at **1 000 000 bytes**, and beyond that **it is not announced** | truncating a text and pasting it into a terminal is worse than not having it | §5.4 |
| 17 | the cursor stops at **256×256**, and ⛔ **`larghezza = 0` *and* `altezza = 0` together** mean hidden — only one of the two at zero is `ERRORE_PROTOCOLLO`, and in that case the **hot spot MUST be `0,0`** | a way was needed to say «no cursor» that was not one message less. ⚠ *This row said «`larghezza = 0` means hidden», without the height: whoever implemented from here sent `larghezza=0, altezza=16` and §5.5 declared it `ERRORE_PROTOCOLLO`. Aligned on 10 Aug 2026, finding **R11.11**, together with the exception on the hot spot that §5.5 did not have* | §5.5, §7.2 |
| 18 | **a frame does not exceed 16 MiB**, and the length is checked **before allocating** | without a cap, six bytes written by hand take away the server's memory | §6.1, §6.2 |
| 19 | frames **can arrive out of order**, and the client discards the old ones with arithmetic **modulo 2³²** | the streams are independent: it is a consequence of §5.1 that nobody had written. At 60 per second the counter wraps in two years, and a session can last longer | §6.2 |
| 20 | **key and button codes are evdev's**, the wheel in **units of 120** | it is what `libei` wants, that is the only way we have to inject input. Any other convention adds a translation table that gets things wrong silently. ⚠ *Here there was also «and in v1 that table cost the wheel bench (`LEZIONI.md` §2.3)», and it is **false**: §2.3 tells that the wheel bench looked for `asse dy=-10` while the log wrote `asse dx=0 dy=-10` — **red, with correct code**. It is a string searched for wrongly, not a conversion with the wrong sign. `RCP.md` §7.3 had been corrected on the night of 9 Aug (finding **R4.15**); this row had not, and it is the one the project designates as the source. Aligned on 10 Aug 2026, finding **R11.14** — and it matters because by citing the wrong lesson **one loses it at the point where it would apply**, that is S7, which is still to be measured* | §7.3 |
| 21 | the input `id` is **one only for the whole channel**, not one per type | it is what comes back in the `input` field of the frame: with separate counters nothing would add up | §7.3 |
| 22 | ⛔ **on detach all keys and buttons are released** | a Ctrl left down in a session that survives the client makes the desktop unusable on reattach, and nobody connects the two things | §7.3 |
| 23 | **`TELA` is the mandatory answer to `ADATTA_TELA`** | §7.1 imposed a «reasoned refusal» and there was no message to say it: the client would have kept waiting forever | §7.1 |
| 24 | after a canvas change, **one second of grace** on the old coordinates | it is the only moment when the two sides legitimately have two different truths. Declared as an exception to §3, not left to improvisation | §7.1 |
| 25 | the reason for the farewell travels **also in the application error code of the WebTransport session close** | if the farewell does not arrive — broken stream, unreadable message — the reason gets through anyway. It is the wound of `LEZIONI.md` §1.7 cured with two routes instead of one. ⚠ *It said «QUIC close», and it is the reading that finding **R1.4** declared impossible for the page: the API exposes the close **of the session**, not that of the HTTP/3 connection underneath. Aligned on 10 Aug 2026, finding **R11.8*** | §3.1 |
| 26 | ⭐ **the bench function enters the protocol**: two new types, `BANCO_MARCA` (`0x000F`) and `BANCO_ESITO` (`0x0010`) — the 16×16 rectangle, the colour, and the **injectable delay `N`** | the latency link of §2.6 measures from the receiving side, and for that number to be valid the bench must be able to **inject a known delay** and check that the median rises by exactly that — *«a bench that does not do it does not know it is measuring»* (`web/rapporti/S4-ritardo-disegno.md` §4.2). That command **crosses the wire**: improvising it in the test code would be the silent defect against which `RCP.md` §0 exists. ⛔ **The function is off by default** (invariant I6) and when off it answers `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`, never a silence. ⛔⛔ **13 Aug 2026: the function does NOT give the known delay, and at phase 3 it did not give it** — `BANCO_ACCESO 0` and the `ACCETTATA` branch is **a stub** `[R]`. The known delay was injected **outside the product**, and P1 is `[M]` green (N=25 → +25.08; N=60 → +58.58). ⭐ And outside the product is **better**: the clock anchor does not pass through the injected path, so P1 **can still fail**. ⇒ ⏳ it remains to decide whether to complete the branch or remove the two types (`RCP.md` §7.5) | §7.5 |

> ⭐ *Row 26 is **from the night of 9 Aug 2026** and was only in `RCP.md` §7.5; it is recorded
> here on 10 Aug, findings **R11.13** and **R11.15**.* ⛔ **It is 🔸, not ✅**: the origin declared
> by §7.5 itself is **finding R3.4 of the review of the phase 1 bench**, and the motivation
> comes from `web/rapporti/S4-ritardo-disegno.md` §5.3 — **not from a sentence of the user**. The
> decisions the user really spoke (§1.6, §1.8) carry here the **quoted sentence
> with the date**; this one has neither sentence nor voice, and `FASI.md` §01-filo-nudo marked it ✅.
>
> ⚠ **Why the mark matters precisely on this one**: §7.5 adds **two message types** and with them
> uses up the clause of §9 that `RCP.md` §12 declares to have been *«the last opportunity»*.
> Marked ✅ it would become uncorrectable without going back to the user; marked for what it is — 🔸
> derived from a review — it stays *«correctable without discussion»*, which is the condition in which
> one wants it if one day those two types became a nuisance.

⚠ **And FOUR message types were added** — `RICHIEDI_CHIAVE` and `TELA` on 9 Aug,
⭐ **`BANCO_MARCA` and `BANCO_ESITO` on the night of the 9th** (row 26 above) — plus **three** farewell
reasons (`TEMPO_SCADUTO`, `SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`). §9 forbids it **within** a
major version, and the clause that allowed it was that at the time no
implementation existed.

⛔ **And that clause has been USED UP since 10 Aug 2026**, first byte of code: the implementations of
RCP/1 now exist and are counted in `RCP.md` §0-bis. From here on the rule holds with no discount, and
the **four** types above are all the window let through. ⚠ *This line
said «the clause that allows it is that **today** no implementation exists», in the present tense,
and four other points of `RCP.md` said it in the same words: whoever read them after 10 Aug
found it written that the protocol was still modifiable. Corrected on 11 Aug 2026, finding
**R12C.2**.*

> ⚠ *Corrected on 10 Aug 2026, finding **R11.13**: this line said «two types … plus two reasons»,
> and the two of the bench function did not appear at **any point** of this document — while
> `RCP.md` §12 declares that they entered «under the clause of §9, and **that was the last
> opportunity**». `RCP.md` §0-bis points precisely here for the closures marked 🔸: two types that
> use up an unrepeatable window cannot be missing from the document the project designates
> as the single source.*

⏳ What RCP/1 leaves **deliberately** open — microphone, relative pointer, touch, 4:4:4, multiple
screens — is in `RCP.md` §12, declared instead of forgotten.

### 1.6 ✅ ⭐ No dedicated clients: the client is the browser

*9 Aug 2026. «Perché impazzire a sviluppare 2 client separati quando un client, e in aggiunta
universale, lo abbiamo già bello pronto? il WEB!» — and, on clarification: «Non una seconda: Remotix
funzionerà senza client dedicati, basterà avere un browser moderno».*

⛔ **It is the biggest decision taken after the death of RDP**, and it must be read next to that one: §1.1
removed Windows to remove the three walls of RDP; this one removes **the clients** to remove the cost
of writing them twice and the wall on which v1 really died — a phone that decodes in
software.

| | Before | Now |
|---|---|---|
| the clients | Linux (C) and Android (Kotlin), written by us | **a web page**, served by the server |
| track B | five phases, A1-A5 | ⛔ **no longer exists** |
| who can connect | two systems | **anything that has a modern browser** |

**The facts it rests on, all `[S]` and none measured by us** — verified on 9 Aug because my
knowledge stopped in May and this stuff moves fast:

| | |
|---|---|
| **WebTransport** | ⭐ **on all three engines since March 2026**, with Safari 26.4. It gives a page exactly what RCP uses: independent QUIC streams, `RESET_STREAM`, datagrams, migration. ⚠ *«Baseline» removed on the evening of 9 Aug: it is a technical term with a precise meaning, and it came from none of the four reports (R2)* |
| **WebCodecs** | Chrome 94+, Firefox 130+, Safari 26+, Chrome for Android from **147** |
| **Hardware HEVC on Android** | via WebCodecs: 8 bit from Chrome 107, **10 bit from 108** — that is, v1's wall turns out to be **passable**, and the probe that verifies it is a page instead of an APK |

⭐ **What the protocol gains from it, and it is the reason the idea could be accepted**: RCP
does not change. WebTransport carries the same bricks on which `RCP.md` §5.1 was designed — one
frame per stream, abandonment, datagrams for audio. Had the wire been designed on
TCP, this idea would have cost the whole protocol.

⭐ **And Windows comes back in without submitting to its rules** *(the user's observation)*. §1.1 and
`SPECIFICHE.md` §12 threw Windows out **as a server** and **as a client to be served with RDP** —
not the people who use it. A browser on Windows is not our code, it is not FreeRDP, it is not
`mstsc`: it is the same client as everyone else, and it costs not one line.

⭐⭐ **And it gives us back a piece of the lost referee.** `PIANO.md` §0.4 says that by throwing out RDP
we lost `mstsc`, which complained for free. A page runs on **three engines written by three
teams who do not know us** — Blink, WebKit, Gecko: when two agree and the third does not,
that is a defect that declares itself. ⚠ **The flip side must be written together**: the client
matrix does not disappear, **it changes shape**, and the browsers served must be **declared** and tested on
at least two different engines — `LEZIONI.md` §2.1 does not lapse, it moves.

⛔ **What it costs, and it is not «a small extra burden»:**

1. the server takes on **a second trade**: serving a page. No longer just bare QUIC, but
   **HTTP/3 with WebTransport** — plus a **TCP** listener for the first load, because a
   browser that opens `https://…` starts on TCP and moves to QUIC only if the server announces it
   (`Alt-Svc`). Two ports listening on the same number, one TCP and one UDP;
2. ⛔ **the criterion by which the QUIC library is chosen changes** (§6.4): it is no longer enough that it speaks
   QUIC, it must bring **HTTP/3 and WebTransport on the server side**. It has become the first question, not
   the last;
3. three things that with our own client we decided pass to the browser: **the certificate** (§1.7),
   **keyboard shortcuts** — `Ctrl+W` closes the tab, and Keyboard Lock is `[S]` only on
   Chrome and only in full screen — and **the clipboard**, which requires permission or a user
   gesture precisely in the direction that `§5-ter.1` says is the most used.

⚠ **The residual risk, declared**: we no longer control hardware decoding. With our own
client we looked at **the name of the decoder chosen** (`c2.` versus software); in a
browser that name is not there, and if a device decoded in software **we would have no lever** — it
is measured and declared. That is why the browser probe must be done **before** writing the
wire, not at phase 2.

*Consequences already written where they belong: `SPECIFICHE.md` §1, §4, §7.3, §9; `RCP.md` §2 and §4.1;
`PIANO.md`, where track B disappears and the probe changes nature.*

> ### ⭐ Where the idea came from, and the reference that follows from it: **XPRA**
>
> *9 Aug 2026. «Ti spiego perché mi è venuto in mente il discorso WEB. In passato ho avuto modo
> di usare XPRA, e devo dire di essere rimasto molto sorpreso».*
>
> ⛔ **It is not an anecdote: it is point 0 of the recipe of `LEZIONI.md` §9** — *«look for whoever has already
> done it»*, which on KDE had made us find `KRdp` **after** the study had declared it
> non-existent, and what found it was a question from the user. It happened again, and in the same
> way.
>
> **Xpra has an HTML5 client that has been doing this job for years**, and the user's surprise in using it is
> the most useful datum we have: it says the road **can be travelled**, not that ours will be the same.
>
> 🔸 **Hence a study, before writing the page** — small, in the form of the others:
> `reference-web/`, and the questions are those of the client, not of the transport (Xpra is on WebSocket,
> we are on WebTransport, and that piece is not inherited): **how it paints**, how it handles the keyboard in the
> browser, how it solves the clipboard and the cursor, what it does when the window changes size,
> and how much it costs in delay.
>
> ⚠ **With the boundary of `§5-bis.0-bis`, which applies identically**: we study **how it behaves and how it
> feels in use**, we do not copy the code — the project's licence is postponed to the end of the work (§7.6),
> and a piece taken from someone else's project would decide it in our place.

### 1.7 ✅ The certificate: one click the first time, and the real certificate for those who have a name

*9 Aug 2026. «Per la parte che riguarda certificato, sicurezza, ecc riflettiamo: ribadisco il
principio che qui non dobbiamo rispettare standard militari».*

⛔ **The premise that changes everything**: §1.3 promised **zero interaction** — *«you type
address, port, user and password, and that's it»*. With our own client we decided that line ourselves.
With a browser **it is no longer our choice**: the rule is Chrome's and Safari's, and «no
military standards» does not touch it.

> ## ⛔ Rewritten on the evening of 9 Aug, after measurement S1 — the default I had proposed **does not work**
>
> *The investigation is in `web/rapporti/S1-certificato.md`, and it is code reading with file and line, not
> an impression.*
>
> I had written that the exception granted by the user on the page's certificate would also hold
> for the WebTransport session, and that that click **was** the trust-on-first-encounter of
> `RCP.md` §4.1. **It is false on two engines out of three:**
>
> | | Why |
> |---|---|
> | **Chrome/Edge** | the exception is consulted by **a single point**, fed by the errors of normal requests; the WebTransport client **never queries it** `[R]` — absence verified with a positive control. ⛔ And there is a **second independent wall**: Chrome's QUIC demands a root **built into the browser** |
> | **Firefox** | the exception **is** consulted on HTTP/3 too, and then the session closes if the root is not built in `[R]`. The only exemption written in the code is, literally, `serverCertificateHashes` |
> | **Safari** | `[?]` **the open case**: its exception puts the certificate **in the keychain**, and WebTransport goes through there — it might be the only one where it works. Nobody has documented it |
>
> ⛔ **And the proposal of the authority to install (below) had a third reason not to
> work, harder than the two already written**: on Chrome **it is not even enough to put it in the
> system store**, because that root is not *built into the browser* and does not become so.
>
> ⭐ **One thing falls away and simplifies**: `Alt-Svc` has nothing to do with it — WebTransport opens its connection by
> itself `[S]`. The silent fallback to TCP that I had declared as a danger **cannot happen**.

**What holds, decided by the user on the evening of 9 Aug**: *«Stiamo complicando le cose. Abbiamo 2
livelli per la sicurezza: il trasporto e l'accesso. Per il trasporto usiamo quello che già oggi i
browser supportano senza problemi: tls. Per l'accesso: al momento restiamo fermi su ip:porta con
userid e password»*.

| Level | How |
|---|---|
| **transport** | **TLS**, always. The server makes its own certificate, and ⭐ **the page passes its fingerprint to the browser** (`serverCertificateHashes`) — which is the mechanism browsers expose **precisely for servers without a domain**, not a workaround |
| **access** | **address, port, user and password**. Nothing else |

⭐ **Why this is not the «complicated road» it seemed**: rotating the certificate every
14 days and publishing the fingerprint live **inside the server** — it is the server that serves the page,
so it writes the current fingerprint into it. The user touches nothing and does not know it exists.

⚠ **What remains the user's burden, and it is the declared price of not having a domain**: the
**click on the warning** when the page loads, the first time on each device. `[?]` On
Chrome the exception might last **about a week** and not forever — to be measured, and if
true it is a recurring click, not a single one.

| Who has a domain | puts in a **real certificate** (Let's Encrypt with a DNS challenge, which does not require exposing anything): **one line of configuration, not a different road**, and the warning never appears |
|---|---|

> ### ⭐ And a real certificate buys much more than it seems — found by crossing S1 and S3
>
> Neither of the two reports could see it alone:
>
> - **S1**: behind a certificate exception, on Chrome **the Service Worker does not install**
>   `[R]` ⇒ no installable application;
> - **S3**: in an **installed PWA** Chrome's list of reserved keys is **empty** `[R]` ⇒
>   **all** the shortcuts reach the session.
>
> ⛔ **Put together: whoever has a domain does not buy the absence of a warning, they buy the whole
> keyboard.** It is a **product** difference, not one of convenience, and it must be told to whoever installs — because
> nobody would deduce it by themselves. *(Detail in `STUDI.md` §web §1.2 B.)*

⛔ **Rejected: the «Plex way»** — a domain of ours that resolves to the servers' private addresses,
that is a real certificate and zero effort for the user. It would be **a service to keep running for
ever**, and the day it was gone all installed servers would stop working.
It is the heaviest dependency the project has ever considered, and it was
rejected by the user together with the rest of the complication.

⭐ **Safari and iPhone are NOT a hole: they are served like the other two.** `[R]` WebKit
implemented `serverCertificateHashes` on **2 Oct 2025** (bug 300057,
`NetworkTransportSessionCocoa.mm`) and shipped it in **Safari 26.4**. What remains to be measured is
only **a convenience** — whether there the exception is enough on its own, that is whether publishing
the fingerprint can be skipped: the fingerprint is used anyway (`RCP.md` §4.1-bis).

> ⛔ *Corrected on the night of 9 Aug 2026, finding **R4.4** of the review of the phase 1 bench.*
> Here it said *«`[?]` Safari and iPhone remain the declared hole: WebKit does not implement
> `serverCertificateHashes` `[S]`»*. `STUDI.md` §web §3.1 declared it had corrected **this paragraph**
> on the same 9 Aug — ⛔ **and the correction had never arrived here**, nor in `RCP.md` §4.1-bis.
> Three documents with the same false sentence, one of which is the referee, and a report that gave them as
> cured. It is the form of item 6 of `FASI.md` §00-ambiente: *the lesson was already written, the cure
> stayed a note in a document.*

> ### ⛔ The proposal to have an authority of ours installed, and why it was rejected
>
> *Proposed by the user the same day: «e se Remotix generasse il suo certificato e lo facesse
> installare al client alla prima connessione?». Kept in writing so that it is not proposed again without
> the two reasons.*
>
> It works, and it is the road that **seems** cleanest: you install once and then no warning.
> But:
>
> 1. ⛔ **it does not remove the risk it would like to remove.** To install that certificate you must
>    first **download it from the server**, that is through the first connection — the one that is not
>    trusted yet. Whoever gets in the middle makes you install **their** authority;
> 2. ⛔ **and the damage gets worse instead of smaller.** An exception on a self-signed certificate holds
>    **only for our address**; an installed authority holds for **any site**, on that
>    device, for ever. The road that removes the frightening warning is the one that would deserve the
>    warning most;
> 3. ⚠ plus the real cost: four to seven steps **in the system settings**, different on every
>    operating system, with a permanent warning *«la rete potrebbe essere monitorata»* on Android
>    and two separate screens on iPhone. And the private key of that authority would live **on the
>    server**.
>
> ⭐ **And what the proposal wanted we already have**: «install it once and never think about it again»
> **is the click on the warning** — one click, inside the browser, no administrator, the same on all
> systems, and valid only for us.

⚠ **One thing about security that changes nature, and must be written next to the risk already accepted in
§1.3.** With our own client, whoever gets in the middle of the first connection **intercepts bytes**.
With a web client **the client arrives from the server at every visit**: whoever gets in the middle does not
intercept, **they rewrite the page in which the password is typed**. The risk is the same — *the first
connection on each device* — but **the consequence is bigger**. After the first click the
certificate is pinned and a different one makes the warning reappear; with a real certificate the case does not
arise.

~~`[?]` **The measurement that decides the form**: does the exception the user grants on the loading of the
page (TCP) also cover the WebTransport connection (UDP) to the same address?~~

⛔ **Closed by reading, on 9 Aug 2026, for two engines out of three: the answer is NO.** The exception does not
cover WebTransport either on Chrome or on Firefox `[R]`, for two independent technical reasons
(`STUDI.md` §web §3.1). ⭐ **So `serverCertificateHashes` is not a fallback: it is the road**, on all
three engines. **Only Safari** remains to be measured, and only to know whether there the fingerprint can be
spared — which is a convenience, not a platform.

> ⚠ *Rewritten on the night of 9 Aug 2026, finding **R4.4**. The question was still open on this
> page while `STUDI.md` §web §3.1 had already closed it with two `[R]` read in the code: keeping it open
> made us **plan a measurement already done**, which is the form of finding R1.25 of `RCP.md`.*

> ## ⏳⏳ The security debt, declared by the user and highlighted
>
> *9 Aug 2026. «Il tuo timore del "man in the middle" lo appunto bene in evidenza: prima
> completiamo il progetto, poi svilupperemo una sua evoluzione per mettere in sicurezza il server
> con i sistemi più solidi che la moderna tecnologia offre (es. MFA)».*
>
> ⛔ **It is not an oversight to be reported again in six months: it is a decided postponement, with its date.**
> It goes here, highlighted, so that whoever takes up the project again finds written **what had been accepted
> and in exchange for what** — and does not discover it from a defect.
>
> **What is accepted today**, and holds until the product is complete:
>
> | | |
> |---|---|
> | the first connection on each device | exposed to a man-in-the-middle (§1.3, risk assessed and accepted) |
> | and with the web client | whoever gets in the middle **rewrites the page** instead of intercepting it |
> | the only key | the **PAM password**, with the **address ban** of `RCP.md` §4.4-bis — three failed attempts, twelve hours (§1.9) |
>
> ⭐ **And this note closes a circle that had already been opened**: `DECISIONI.md` §4.3 — the lock is
> REMOTIX's, not the desktop's — has an **expiry clause written on 8 Aug** in these
> words: *«the reasoning holds only as long as the PAM password is the only key. Whoever implements
> strong authentication rereads this item»*. MFA is precisely that event. **When the evolution
> opens, the items to reread are four and they are these**: §1.3 (trust), §1.7
> (this one), §4.3 (the screen lock, which with a second key would go back to defending something) and
> ⭐ **§1.9** — *added on 10 Aug 2026*: the three-attempt ban is the defence that the password
> alone demands, and with a second key its price — the NAT's address closed to everyone for
> twelve hours — becomes dearer than what it buys.

---

### 1.8 ✅ ⭐ Apple is an extra, not a goal — and the turn to the browser is the reason

*9 Aug 2026, from the user, closing the question «do we need to get a Mac to measure Safari?».*

> *«Apple copre il 4-5% dell'utenza; con la sterzata che ho impresso supportando il browser come
> client abbiamo recuperato Windows e la platea di potenziali utilizzatori sale al 95%. Apple è un
> di più: se capiterà l'occasione di testarlo bene, altrimenti pazienza.»*

⭐ **It is §1.6 paying off the third time.** The page-client had already removed two native clients and
five plan phases, and brought back **Windows as a place to connect from**. Here it does
one more thing: **it makes Apple a platform that costs nothing not to measure**, because the code is
the same for all three engines.

⛔ **And the distinction that must be held firm, or this item will be read backwards in six months:**

| | |
|---|---|
| **what does NOT change** | Safari, iPhone and iPad **remain served**: `serverCertificateHashes` shipped in **Safari 26.4** `[R]`, and it is the same road as the other two engines (§1.7, `RCP.md` §4.1-bis). Not one line of code less is written |
| **what changes** | nothing is **spent** to verify it: no Mac to get, no rented devices, no tunnels. Measurement **S1a** leaves phase 1 and stays `[?]` |
| ⛔ **and what cannot be said** | until someone has tried it, *«works on iPhone»* is **a deduction, not a measurement** — form **E5**. The place where it must not appear is the **product documentation** |
| **the price, declared** | the choice of the QUIC library (§6.4) is made on **two engines out of three**, and the line is written next to the choice |

⚠ **The percentages are the user's estimate**, not a measurement of this project: `[?]` 4-5% and
95%. They do not change the decision — which is one of **priority**, not of technique — but the mark is put
anyway, because a decision taken citing an unmeasured number must know it is one
(`LEZIONI.md` §2.3-quater).

⭐ **The door stays open at zero cost**: the three checks of S1a are already written in
`FASI.md` §01-filo-nudo and the probe page is the same. The day a Mac or an
iPhone passes through our hands, **the measurement is an afternoon**.

### 1.9 ✅ ⭐ Three failed attempts, then the address ban for 12 hours

*10 Aug 2026, from the user, in two passes in the same conversation.*

> *«Secondo me la cosa deve funzionare in modo molto semplice: se l'utente sbaglia la password per 3
> volte consecutive, non vengono più accettate connessioni da quell'IP per 12 ore (ban).»*
>
> And then, tightening: *«3 tentativi di connessione fallita (perché user sbagliato o perché password
> sbagliata) causano il ban di quell'IP.»*

⛔ **It replaces the previous form entirely**, which was 🔸 and is in row 11 of §1.5: 5 attempts
in 5 minutes, a 30-second window doubling up to 15 minutes, **two** counters — per user
name and per address — and the reset on a successful login. ⭐ **The per-user-name counter
no longer exists**: the count looks at the address and nothing else, and three different user names count three.

| | |
|---|---|
| **the count** | three failed authentications from the same address (**without the port**), ⛔ **within 5 minutes** — *the user's rule, same day: «i 3 tentativi falliti devono avvenire entro i 5 minuti per far scattare il ban»*. The window is **sliding**: the last three are looked at, it does not restart from the first |
| **the consequence** | that address is out for **12 hours** |
| **what resets** | 🔸 a **successful** authentication from that address. *Derived from «consecutive»: without it, three typos scattered over a year would ban the address one works from every day* |
| **what counts** | ✅ **only** the failed authentication. Not protocol errors, not timeouts, and ⛔ **not `GIA_ATTIVA_REMOTA`** — which is what the **same** user's second device receives, and which would ban the user by himself in three reattaches |
| **what the banned one sees** | ✅ *«viene visualizzata una pagina di login rifiutato (max tries reached)»*: the page is served anyway and **says** that the attempts are exhausted. The WebTransport session is refused with `TROPPI_TENTATIVI` for the tab **already open**, which would otherwise be left waiting |
| **the ban survives the restart** | ✅ **yes, on file.** A ban that resets on restart is a protection that loses itself — invariant **I7** |
| **how you get out** | ✅ *«comando di sblocco oppure il trascorrere delle 12 ore»*. The command requires access to the machine, which is the only key the case admits, and ⛔ **every unblock is written in the log** |

⭐ **Why the new form is better than the one it replaces, as well as harder**: the
doubling disappears, as do the two overlapping windows and the question «what does the per-name counter do
when the per-address one has already fired». ⛔ And by construction the defect that **B5**
found on 10 Aug disappears — the counter's key contained **the port**, which with a single attempt per
connection (§`RCP.md` 4.4) changes every time, so that counter was **always 1**.

⛔ **And `RCP.md` does not gain a byte**: `TROPPI_TENTATIVI` (`0x08`) was already there, no new type,
no exemption from the rule of §9 — which is the rule the project gave itself and which from here on
has no more discounts.

⚠ **The price, accepted knowingly, and it is not paid by whoever guesses:**

| | |
|---|---|
| **behind a NAT** | addresses are shared: three errors by **one** person shut the door on everyone else for twelve hours. It is exactly the case the per-user-name counter existed for |
| **the first to trip over it is the owner** | long password, phone keyboard. Hence the page that **says** what happened and the unblock command: without those two, the rule is indistinguishable from a fault |
| ⛔ **and the password remains the only key** | three attempts per address raise the cost a lot, and do not close the game: ten thousand addresses make thirty thousand attempts on a single account. What closes it is the strong authentication postponed to the end of the project — §1.7, the security-debt box, ⭐ **and this item goes on the list of those to reread that day** |

⭐ **And one thing the ban can NOT do**, written so that nobody attributes it to it: nobody can get
**someone else's** address banned. To reach `CREDENZIALI` you must have completed the
QUIC handshake, which demands that packets really return to that address — the sender
cannot be forged.

⚠ **And a consequence on the work, not on the product**: the benches all start from the same address and
the limiter's one fails on purpose. With twelve hours, «wait for the expiry» is not a cure:
the bench uses the unblock command, and the limiter's one **does not call it inside its own
round** or it no longer proves anything (`FASI.md` §01-filo-nudo, rule B0.3).

*Consequences already written where they belong: `RCP.md` §4.4-bis (rewritten entirely, and from 🔸 it becomes ✅) and
§8.2; `SPECIFICHE.md` §4.2; `FASI.md` §01-filo-nudo B0.3 and B8.*

---

### 1.10 ✅ ⭐ The PAM check leaves the single thread — **before phase 2**, and with a helper process

*11 Aug 2026, evening, from the user, at the close of phase 1. The question was brought to him with
the measured number next to it, not as a hypothesis.*

**The fact.** The phase 1 server runs in **a single `poll` loop** (`src/main.c`), and the PAM
check **blocks that thread**. ⛔ It is not an estimate: **B8 measured it on the evening of 11 Aug** —
`[M]` from **1.0 to 2.2 seconds** per attempt (medians **2123 · 2198 · 1086 ms**), and ⭐ **the delay
is put there by PAM, not by us**: the server waits **+1034 ms** beyond its own fixed second on the rejected ones
against **+84 ms** on the admitted ones, which is the signature of `pam_faildelay`.

**The decision.** ⛔ **It is cured before opening phase 2**, and ⭐ **with a helper process, not with a
thread**: PAM is not reliably reentrant, and a thread would bring troubles of its own into the cure of
a concurrency problem.

> ⭐ **Why before phase 2, and not at 5 as the fallback said.** As long as there is no video, the
> symptom is *«the last of the ten waits ten seconds»*: unpleasant and contained. ⛔ **From phase
> 2 on it becomes another defect**: the screen of **everyone** connected freezes for one or
> two seconds every time **someone else** comes in — and whoever sees it will attribute it to the **video**,
> because that is where it shows. ⚠ It is the «the symptom does not name the cause» form that `LEZIONI.md` §1.6
> describes, and curing it now means **not letting it be born**.

⚠ **And it costs little precisely now**: `rcp.c` is not touched, so **the twelve certifications of 11
Aug remain valid**.

⛔ **The property to prove is not «PAM still works»**: it is **«while one authenticates, the others
do not notice»** — that is, a second client that keeps receiving packets during the
check. Today **there is no bench that looks at it**, and without that bench the cure is a hope.

*Consequences to be written: `SPECIFICHE.md` §5.5 (the fallback box, which today defers to phase
5) and `src/main.c` (the comment «UN SOLO FILO, E VA DETTO»).*

---

### 1.10-bis ✅ ⭐ **One child per user** — and it is not symmetry, it is a fact of the system

*12 Aug 2026, from the user, in front of the measurement of the phase 2 assembly.*

**The fact, `[M]`**: ⛔ **root does not connect to the user's session bus** — and ⛔ **only root can
verify with PAM someone else's password**. ⇒ **The two things do not live in the same
process**, and it is not an implementation detail: without the bus there is no capture, without root there is no
authentication.

**The decision.** The server stays **privileged**, and for each admitted user it spawns a **child that
runs as that user** and holds their session bus, their capture and their devices.

⭐ **It is the helper of §1.10 the other way round, and it is the same rule**: *one trade per process*. There a
child **less** privileged than the parent does the thing that blocks; here a child **differently**
privileged does the thing the parent cannot do. ⇒ The shape of the server was not chosen twice:
it was chosen once and applied twice.

⭐ **And it pays beyond phase 2**: it is the natural road towards the multi-tenancy of **phase 10**, and it isolates
one user from another **by construction** instead of by care.

⚠ **The price, declared**: one process per session. With the cap of §1.11 — 16 — that is sixteen
processes, which is a known and measurable cost, not a surprise.

*Consequences written: `FASI.md` §02-primo-fotogramma, and the product of the phases that touch the
session.*

### 1.10-ter 🔸 ⛔⛔ The user's `/run/user/<uid>` is given to us by **linger**, not by us — and it is a requirement, not luck

*Written on the evening of **15 Aug 2026**, at phase 5, after a desktop that did not show.*

> ### ⛔ And the first draft of this item was WRONG — corrected the same evening
>
> It said: *«the service's PAM stack must call `pam_systemd`, and ours did not»*,
> because `remotix.pam` ends with `common-session-noninteractive` — which on Debian 13 `[M]` does **not**
> contain `pam_systemd`, while `common-session` does.
>
> ⛔ **The premise was false**: the product **opens no PAM session**. `figlio.c` · `codifica_e_manda()`
> declares it at length — *«`sessione_assicura()` would make a session BE BORN … that is the road
> of the real login (`pam_open_session` → `pam_systemd`), and it is not part of this mandate»* — and `grep`
> confirms it: in `src/` there is no call to `pam_open_session`. ⇒ Which session stack
> is in `remotix.pam` today **changes nothing**, because that stack is never executed.
>
> ⚠ The line `session optional pam_systemd.so` stays in the file, but **as a declared open door**,
> not as a cure: the day the product really opened sessions, the «noninteractive» stack
> would create none.

**The real fact, measured.** `/run/user/<uid>` — and with it the session bus socket, without
which the child has nothing to capture — is born because the user has **linger** on
(`loginctl enable-linger`). ⭐ It has always been written in the recipe that produced the first real
desktop (`fasi/rapporti/F5-desktop-vero.md`, step 1: *«user `prova` (uid 1001), password,
`enable-linger`»*) — ⛔ **but it was written nowhere that it is a requirement of the product.**

`[M]` **The price, paid on 15 Aug:** after the machine's reboot — whose rootfs lives in RAM
— the user `prova` no longer existed; the account recreated **without linger**, the child wrote three
times *«runtime `/run/user/1001` ⛔ NON c'è, socket del bus ⛔ non c'è»* and the user saw a
**black screen**. ⚠ The log said exactly what was missing, and it was clear to nobody that
that line was an environment condition and not a code defect.

**Hence, and they are three obligations as for the headless of §4.3-bis:**

1. linger is **declared** among the requirements of the served user, not inherited from how the machine
   was prepared one day;
2. the child, when it does not find the runtime, **names the probable cause** instead of the symptom alone —
   *«`/run/user/<uid>` is missing: does that user have linger on?»*;
3. ⏳ and the question underneath stays open: whether the product should **open the session itself**
   (`pam_open_session`) instead of depending on linger. ⚠ Today it is declared out of mandate, and that is fine
   — ⛔ but then linger is a **dependency of the product**, and as such it must be installed and verified.

> ### ⭐⭐⭐ AND QUESTION 3 CLOSED THE SAME EVENING: **the product opens the session itself**
>
> *15 Aug 2026, phase 5, after the user's go-ahead. ⇒ Linger **is no longer needed**: it was a
> prop, and the prop is removed when the wall stands.*
>
> ⛔ **The reason is not elegance, it is that without a session the compositor does not start at all**: Mutter
> asks `sd_pid_get_session()` and gets the answer **ENXIO**, then dies with *«Failed to find any
> matching session»*. Linger gives `/run/user/<uid>` and the bus, ⛔ but it puts the processes in
> `user@<uid>.service`, which is a scope of class **`manager`** — not a session.
>
> **Where**: `figlio.c`, `diventa_ed_esegui()` step **2-bis** — after closing the descriptors and
> **before** dropping to the uid. With `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`,
> `PAM_RHOST`, and ⛔ **no `XDG_SEAT`**: the session is born **headless by construction**, which is
> what §4.3-bis has asked for since August and which until now we had by accident.
>
> ⚠ `pam_end()` **without** `pam_close_session()`, on purpose: the logind session belongs to the
> **leader** process — this one, after the `exec` — and logind takes it back when it dies. ⭐ It is
> invariant **I4** seen from the system's side: the stage outlives the client because the
> child outlives it.
>
> ⇒ ⭐ **And the XDG variables stop being invented**: `XDG_SESSION_ID` is set by `pam_systemd` and
> we **read** it (`pam_getenvlist`). It is the answer to the user's observation of 15 Aug.
>
> ### ⛔⛔ AND IT COMES WITH A DEPLOYMENT CONSTRAINT THAT DID NOT EXIST BEFORE
>
> `[M]` **The server must not run inside a user session.** `pam_systemd`, when the caller
> is already in a session, **does not create a second one — and does not say so**. ⇒ A server started by hand
> from `ssh` puts its children in the session of whoever started it, and the child is left without runtime,
> without bus and without compositor: **the same black screen, for a new cause**.
>
> `[M]` Measured: with the old `riavvia-7700.sh` (which uses `setsid` — it detaches the terminal but **does not
> change the cgroup**) the server was in `session-127.scope`; with `systemd-run` it is in
> `system.slice/remotix-7700.service`, and the children open their own. ⭐ In production the case does not exist
> — `remotix.service` is a system unit — ⚠ but it must be **written**, because a server started by hand is
> broken in a way that does not show.

### 1.11 ✅ The session cap stays **16, fixed at compile time**, until phase 3

*11 Aug 2026, evening, from the user, at the close of phase 1.*

**The fact.** `src/rcp.c` has `#define MAX_ATTACCATE 16`, while `SPECIFICHE.md` §5.5 wants
**«default cap 10 sessions, configurable»**.

**The decision.** ⛔ **It is not changed now.** The reasoning that holds it up is the one §5.5 writes
about itself: *«the real limit is not a count: it is a **budget** of pixels per second, and it is set by the
encoder»*. ⇒ Any number put in today is **a placeholder**, and bringing it to ten now
would mean changing it **twice**: once to obey the letter, and once when the real
budget arrives.

⛔ **And the price is declared, instead of left implicit**: for two phases **the code says 16 and the
specification says 10**, and whoever reads one of the two believes they know something the other contradicts. ⚠ It is
exactly the form that produced the defect of the **five-minute window** (finding R12C.5):
a rule copied into four documents, and the four copies not equal. ⇒ **The difference must be named
in both places**, or we reach phase 3 believing the cap is ten.

⚠ **And the other half, which holds for whatever number is chosen**: **no bench has ever seen that cap
bite**. Filling it requires ten **different** users (a second connection by the same user
gets `GIA_ATTIVA_REMOTA`, **I2**), and the reason with which the newcomer is refused is among those that
want the encoder. ⛔ Until it is there, it is **code present that nobody has seen work** —
the same form as the per-address counter that **B5** found: it read well, and did
nothing.

*Consequences to be written: `SPECIFICHE.md` §5.5 and `FASI.md` §01-filo-nudo, «I ripieghi di fase».*

### 1.12 ✅ ⭐ The cure for the farewell is **out of phase, and declared** — phase 1 stays closed at 12 out of 14

*11 Aug 2026, late evening, from the user, **after** the close of phase 1.*

**The fact.** The farewell defect of §8.1 — on closing the tab the page sends no
`CONGEDO`, on both engines — was found and **attributed** in phase 1, and **cured after the
close**: `src/pagina.html` no longer resets `congeda_corrente` in the `finally` of `submit`, it is reset by
`wt.closed`. ⛔ And the phase document says, in the user's words, that *«una cura di prodotto
infilata dopo la chiusura non è una cura, è un cambiamento non dichiarato»*.

**The decision, and it is three things together:**

| | |
|---|---|
| ⛔ **phase 1 is not reopened** | the certification stays **12 out of 14** as it was delivered. A verdict already given is not touched for a later fact: were it reopened for this, «closed» would stop meaning anything |
| ⭐ **and the cure is not rolled back** | it is **measured** with the same rigour as the phase — the expected outcome written first, **two rounds per engine**, the log kept in `banchi/01-p5-ff-registro-cura.log`. Removing it from the product to put it back in a week would mean keeping at home a **known and cured** defect for a reason of calendar |
| ⭐ **the cure is a DATED APPENDIX** | it sits in the P5 box of `FASI.md` §01-filo-nudo, under the cure described, and says *«applied and remeasured on the late evening of the 11th»*. ⛔ It does not enter the certification count, and **does not change a number** of that document |

⛔ **What passes to phase 2, and is not lost here**: the **recertification of P5**, which failed
precisely because of this defect. ⚠ And it first wants the cure of its scene — `01-p5-lancia.sh` still closes
`ctrl+w` **on the only tab**, where Firefox **quits** and nothing goes out by any route: without
that cure the new round would be red because of the scene, not the product.

> ### ⭐ And the same night the rule held a SECOND time — the mute slot
>
> *From the user, a few hours later, curing the P5 scene.* ⛔ `src/rcp.c` frees the slot in four
> places and **three** write it in the log: on the `CONGEDO` road — the one that **§8.1 imposes**,
> that is the one the healthy product always takes — the `posto LASCIATO` **was not written**.
>
> ⚠ The slot was really freed (`[M]` twelve sessions, each subsequent `posto PRESO` says
> `occupati adesso: 1`): the defect **was not a leak, it was that invariant §8.2 `0x0F` could
> no longer be observed**. ⇒ P5 judges that number, did not find it, and would have given **a red to a
> healthy server**.
>
> **The decision is the same as §1.12, and for the same three reasons**: it is cured in the product (one log
> line, identical to its three sisters), **out of phase and declared**, and phase 1 stays at 12 out of 14.
> ⭐ The reasons holding it up here are even simpler: it is **additive** — it writes what already
> happens, it does not change a behaviour — and it repairs a hole that makes **unverifiable** an invariant
> that the phase document declares verified.
>
> ⭐ **Measured**: `[M]` two rounds per engine, four out of four `PRESO(1) → si congeda 0x01 →
> LASCIATO(0)`, and the P5 judge goes from **1 false fault** to **0**. ⛔ *And «zero faults» does not
> mean «P5 certified»: what is green is the judge on a real segment, not the P5 round.*
>
> ⚠ **And the declared price**: the product binary was **rebuilt** on the test
> machine, and `RCP.md` §0-bis carries the new numbers of `rcp.c` (2,592 lines, `md5` `1adce15b…`) — that
> box declares that `src/rcp.c` and `banchi/rcp/rcp.c` are identical byte for byte, and what enforces it
> is the `Makefile`, which compares them at every build.

*Consequences written: `FASI.md` §01-filo-nudo (the P5 box and the table of defects), `README.md` and
`RCP.md` §0-bis.*

---

### 1.13 ✅ ⭐ HEVC **with a negotiated fallback**, not a declared requirement

*12 Aug 2026, from the user, in front of the phase 2 measurement. The question was brought to him with the
number next to it, not as a hypothesis.*

**The fact, `[M]` 12 Aug 2026** (sub-phase **F2.5**, `fasi/rapporti/F2-5-pagina.md`):

| | real screen (GPU) | Xvfb (no GPU) |
|---|---|---|
| **Chrome 151** | ⭐ HEVC reaches the pixel, 8 cells out of 8 | ⛔ **zero** |
| **Firefox 140 ESR** | ⛔ **zero**, `NotSupportedError` | ⛔ **zero** |

⭐ **VP9 paints 8 out of 8 in all four cases**: the «no» is HEVC's, not the bench's. And the cause is
measured: with `prefer-software` Chrome says `Unsupported`, with `prefer-hardware` it paints ⇒
**Chrome on Linux has no software HEVC decoder**, HEVC exists **only via VA-API**.
⛔ *Confirmed a second time, on the user's real Chrome, with a positive control (VP9, H.264) and a
negative one (an invented codec).*

**The decision.** ⛔ **No requirement is declared** *«you need Chrome with VA-API»*: **the codec is
negotiated, and the fallback is declared**. It is what `CODER.md` §4.2 imposes — *every missing dependency
has a fallback, the service works anyway with less, and the fallback is declared* — and what
protects the promise of `DECISIONI.md` §1.6: *no client to install, a modern browser is
enough*.

⭐ **And the mechanism already exists**: `RCP.md` §4.3 negotiates `video.codec` and §6.2 carries the `codec` field.
No new line of protocol is needed — that is, **§9 is not touched**.

> ### 🔸 And the second codec is **AV1** — closed the same day, on a measurement
>
> *Consequence written by me, not spoken by the user: he decided **that there be** a fallback;
> **which one** was decided by the number. It is corrected without discussion (§1.5).*
>
> ⛔ **The question was real, and the document had got in its own way**: in RCP/1 the allowed values
> of `video.codec` are **`hevc`** and **`av1`**, and `vp9` appears in §4.3 as **the canonical
> example of a value that an RCP/1 implementation must IGNORE** ⇒ VP9 would have meant **opening
> RCP/2**, while AV1 is already normative and already has its `codec = 2`. ⚠ But «AV1 is supported everywhere»
> was a **deduction**, and here a deduction taken for a measurement has already been paid for three times.
>
> **`[M]` 12 Aug 2026, F2.5** — four boxes out of four, with the bench's six checks green in
> all four rounds:
>
> | | real Chrome | real Firefox | Chrome Xvfb | Firefox Xvfb |
> |---|---|---|---|---|
> | **AV1 8 bit** | ⭐ 8/8 | ⭐ 8/8 | ⭐ 8/8 | ⭐ 8/8 |
> | **AV1 10 bit** | ⭐ 8/8 | ⭐ 8/8 | ⭐ 8/8 | ⭐ 8/8 |
> | *(comparison)* **HEVC Main10** | 8/8 | ⛔ zero | ⛔ zero | ⛔ zero |
>
> ⭐ **AV1 fills exactly the three boxes HEVC leaves empty**, and ⛔ **holds up in software**:
> `prefer-software` paints 8/8 in all four, at 8 and at 10 bit. ⇒ **it is a real fallback, not a
> second requirement in disguise.**
>
> ⭐⭐ **And it keeps the 10 bits, observable for the first time**: on Chrome a true 10-bit stream
> gives `VideoFrame.format` = **`I420P10`**, `copyTo` on three 16-bit planes, **luma maximum 870** —
> impossible at 8 bit. It is the **positive case** that the table of the opposite case had never been able
> to fill: with hardware HEVC the format was `BGRA` and the question stayed mute. ⚠ On Firefox the 10
> bits **arrive** (gradient at 210 levels) but **are not observable**: the format is `BGRX` for
> everything. The question has an answer **engine by engine**.
>
> **The strings**: `av01.0.04M.08` and `av01.0.04M.10`, with the numbers read from the stream. ⚠ `seq_level_idx
> = 4` **is not «level 4»: it is 3.0** — the index goes in the string. ⭐ And **no `description`**:
> AV1 takes OBU temporal units as they are, that is **one seam fewer** than
> HEVC's `hvcC`/Annex-B pair.
>
> ⛔ **The preference ladder is NOT reversed**: the order stays **`hevc,av1`**. This measurement fills
> second place, not first — HEVC stays the main codec because it is the one the phone
> decodes in hardware, and that is question **S2**, still open.
>
> ⇒ ⭐ **`RCP.md` is not touched**: `av1` was already among the allowed values of §4.3 and already has `codec = 2` in
> §6.2. The user's decision is carried out **without a new line of protocol**, that is without
> grazing §9.
>
> **The `[?]` that remain, and they belong to the fallback, not to the choice**: AV1's **rate** in software
> (⛔ *it is the question that decides whether the fallback is usable or merely existing*); the bandwidth cost against
> HEVC; AV1 on Android/DeX and on Safari (the device is missing — form **E10**); and ⚠ why **Firefox
> accepts `prefer-hardware` and paints** where `vainfo` lists no AV1 decode entrypoint
> `[M]` — either it has a road VA-API does not declare, or it **falls back silently** (form **E2**). Which one is not
> measured, and it is not written as if it were.

*Consequences written: `FASI.md` §02-primo-fotogramma. ⭐ `RCP.md` **requires no changes**.*

> ### ⭐⭐⭐ 1.13-bis — **AV1 CANNOT GO IN HARDWARE**, and the preference ladder comes out stronger
>
> *13 Aug 2026, evening, with the code frozen. ⛔ **It is not a decision of the user: it is a constraint of the
> machine**, measured. It is written here because it changes the weight of a decision already taken, not its
> direction.*
>
> **`[M]` on the server, 3 rounds out of 3**, with the outcome read from the **exit code** and not from the prose:
>
> ```
> av1_vaapi   ⛔ USCITA 218   «No usable encoding profile found»
> ```
>
> ⭐ **And the cause is in the hardware, not in `ffmpeg`**: `vainfo` gives `VAProfileAV1Profile0 :
> VAEntrypointVLD` on `renderD129` and **no AV1 at all** on `renderD128` ⇒ **decode only**.
> ⚠ `av1_vaapi` **appears** in `ffmpeg`'s list of encoders: whoever trusted the list
> instead of a round would throw away a delivery. *A list says the code is there, not that the machine
> can do it.*
>
> | encoder, 1920×1080 10 bit, **20 Mbit/s for all**, 120 frames counted at the output | ms/frame |
> |---|---|
> | ⭐ **hevc_vaapi** | **3.16 – 3.24** |
> | h264_vaapi | 3.11 – 3.16 |
> | vp9_vaapi profile 2 | 6.95 – 7.28 |
> | ⛔ **av1_vaapi** | **does not exist** |
>
> *(Here there was also the time of `libsvtav1` in software, as a comparison: removed, the measurement no longer holds
> after phase 18.)* *→ OpenH264's time per frame: `fasi/18-senza-ffmpeg.md` §5.4.*
>
> ⇒ ⛔⛔ **Staying on AV1 means staying in software for ever**, on this machine. The line
> *«the preference ladder is NOT reversed: the order stays `hevc,av1`»* had been written for one
> reason (the phone) and ⭐ **now it has a second, stronger one**: **HEVC is the only road to
> hardware on the server side.**
>
> ⛔ **And the line that made HEVC unreachable is REFUTED.** It was written above: *«Chrome on
> Xvfb: HEVC zero»*. `[M]` **the cause was the bench's `--disable-gpu` flag**, not the stage:
> without it, the same Chrome on the same Xvfb sees the GPU (`ANGLE (Intel, Mesa Intel(R)
> Graphics (ADL-N))`) and ⭐ **paints an HEVC Main10 stream coming out of `hevc_vaapi`: 5 rounds out of 5,
> 1920×1080, 119 frames out of 120, `powerEfficient: true`**.
> ⚠ **What is NOT refuted, and stays true**: *Chrome on Linux has no software HEVC
> decoder* — HEVC exists **only via VA-API**. It is **exactly for this reason** that the AV1 fallback
> **remains necessary** and the user's decision **is not touched**: on a client without VA-API for
> HEVC the fallback is the only thing that keeps the promise of §1.6 standing.
>
> ⭐⭐ **AND THE `[?]` WAS CLOSED THE SAME EVENING, BEFORE THE BIG WORK.** It was: *«the stream was
> painted through the `<video>` road, and the product uses WebCodecs `VideoDecoder`»*.
> `[M]` **120 `VideoFrame` out of 120 access units, 5 rounds out of 5, on both packaging
> roads** (Annex-B without `description`, and `hvcC` demuxed from the mp4) — frames counted
> at the output of the *callback*, not declared. HEVC is also **the fastest of the six streams tried**, and
> returns `VideoFrame.format: null`, that is **opaque frames that live on the GPU**.
> ⭐ The negative control separates sharply: with `--disable-gpu` HEVC gives **zero** 5 times out of 5 and the
> other four streams 120. ⚠ **Headless Firefox** gives a real and different answer: positives green,
> HEVC **`NotSupportedError` 5 out of 5** ⇒ the AV1 fallback **is really needed**, and now it is measured instead
> of feared.
>
> ⛔ **And a correction to the number of two hours earlier**: the *«119 frames out of 120»* of `<video>` was
> **an artefact of the CONTAINER, not of the codec** — the mp4 carries an *edit list* that skips 2.4
> frames at the head. The stream has **120**, and three independent sources say so: `ffmpeg`
> from the mp4 counts **118**, from the same stream in Annex-B **120**, `<video>` **119**,
> `VideoDecoder` — which has no container — **all 120**. ⇒ A second, independent reason why
> the measurement with `<video>` was not enough: **it was not even counting the same thing.**
>
> ⭐⭐ **And THIS one too was closed, an hour later, by lane B**: the packets poured out by
> **our** encoder, with the boundary read from the length — *the product splits nothing, the
> boundary is already written* — give **120 frames out of 120, 3 rounds out of 3**, `format: null`; negative
> control with `--disable-gpu` → **0**.
>
> ---
>
> ### ⛔⛔⛔ AND THE REASON WHY `codec 2` WAS BEING NEGOTIATED WAS NONE OF THOSE LOOKED FOR
>
> *13 Aug 2026, night. **The product encoded in software for days because of one line of a
> bench**, and every piece of the chain answered correctly the question it had been asked.*
>
> `banchi/02-pagina-sonda-codec.py` · `x265-params` passed `-x265-params …:**keyint=1**:…`, and `keyint=1` makes
> libx265 emit **«Main 10 Intra» — Rext, `profile_idc = 4`** — ⛔ **cancelling the
> `-profile:v main10` asked four lines above**. *The profile had been asked for and not applied,
> without an error.* ⚠ And it is the form of error that **the comment of that same file describes**.
>
> The two probes end up **inside `src/pagina.html`**, and the page uses them to decide what to
> put in the `CIAO`:
>
> | piece | what it did | and it was right |
> |---|---|---|
> | the declared **string** | `hev1.1.6…` / `hev1.2.4…` — profiles **1** and **2** | yes, for what it declared |
> | the probe's **bytes** | `profile_idc = **4**` (Rext) | ⛔ no, and nobody read them |
> | `isConfigSupported` | **`true`** | yes: it answers **to the string** |
> | the decoder | `EncodingError` **on the bytes** | yes |
> | `pagina.html` | *«HEVC does not reach the pixel»* ⇒ out of the `CIAO` | yes, given what it saw |
> | `rcp.c` · `prima_comune()` `prima_comune()` | takes the first entry **of the client's list** ⇒ `av1` = **2** | yes |
>
> ⭐ **The cure is two lines** — `keyint=1` removed, probes regenerated — **and the protocol is not
> touched**. `[M]` `ffprobe` now gives `profile=Main` and `profile=Main 10` (they were Rext), and
> `banchi/02-pagina-sonda-verifica.py` — which reads the probes **from the product's file** instead of
> copying them and **counts the frames** — gives **4 out of 4, 3 rounds out of 3**, with the two AV1 ones as positive
> control. Before: **zero frames**.
>
> ⛔ **The line to take away**: *asking is not enough*. The string and the codec agreed **with each
> other** and disagreed **with the stream**, and no check looked at the bytes. ⇒ When a
> format is declared, **what was produced is read back** — it is `CODER.md` §3.9 (*you ask by name and
> verify that it was given*) applied to the **output**, not only to the input.

> ### ⛔⛔⭐ 1.13-ter — **AV1 LEAVES THE PRODUCT, H.264 COMES IN** — ✅ decided by the user on 17 Aug 2026
>
> *The sentence is his: **«la scelta è obbligata: dobbiamo abbandonare AV1»**.*
>
> **The cause, and it is his**: ⛔ **Firefox for Android supports neither HEVC nor AV1.** ⇒ For that
> browser the product **did not exist**, which contradicts the opening line of the `README` —
> *«no client to install, a modern browser is enough»* — that is §1.6.
>
> ⭐ **And the measurement confirms it from both ends** (`vainfo` on the CHUWI + the numbers of §1.13-bis):
>
> | codec | decoding on the tablet | Firefox Android | encoding on the server |
> |---|---|---|---|
> | HEVC | ⭐ hardware | ⛔ **no** | ⭐ hardware, **3.16 ms** |
> | AV1 | ⛔ **no profile** | yes | ⛔ **does not exist**, software only |
> | **H.264** | ⭐ hardware | ⭐ yes | ⭐ hardware, **3.11 ms** — the fastest |
> | VP9 | ⭐ hardware | yes | ⭐ hardware, 6.95-7.28 ms |
>
> ⇒ ⛔ **AV1 was the only codec without hardware anywhere** in this set-up: on the server because of
> §1.13-bis, on the user's tablet because of `vainfo`. The fallback cost CPU **at both ends**.
>
> ⭐ **And the string need not be guessed, it is already `[M]`**: **`avc1.640032`** (High, level 5.0) —
> Firefox accepts it and decodes **300 frames out of 300 with zero errors** (`banchi/07-b48`,
> 17 Aug 2026).
>
> > ⛔⭐ **UPDATE 23 Aug 2026 — the string in force is NO longer that one: it is
> > `avc1.640033`.** `banchi/07-b48` measured **5.0** (`32`); since then
> > `src/pagina.html` · `LIVELLO_DICHIARATO()` declares `LIVELLO_DICHIARATO = "5.1"`, because the ladder of
> > `video.misura_massima` reaches **3840×2160** and 5.0 does not reach it. ⇒ The page composes
> > `avc1.6400` + the level in hexadecimal = **`avc1.640033`** (`0x33` = 51 = 5.1), and that is the one
> > that goes to `configure()`.
> >
> > ⭐ **And now the server says it too**, which until tonight left the string
> > **EMPTY** under H.264: `leggi_sps_h264()` read profile and level and never wrote them together
> > (`src/codificatore.c`). `[M]` 23 Aug 2026, x264 at 3840×2160 with level 5.1 imposed, SPS
> > read byte by byte: `profile_idc=100 · constraints=0x00 · level_idc=51` ⇒ **`avc1.640033`**,
> > that is **both ends say the same thing**.
> >
> > ⚠ **5.0** stays true as the measurement of that day and is not erased: it is the reason why
> > `07-b48` is not the proof of today's value. And today's value has a proof of its own: the line
> > «§4.3 — LIVELLO» of the child, which puts produced and requested on the same line.
>
> ⚠ **Two measurements from the same bench that will be useful when writing the encoder:**
> - the frame WebCodecs delivers on Firefox is **`BGRX`**, not planar: the colour
>   conversion is already done by the decoder;
> - ✅ ~~the **hardware** H.264 decoder converts with **+8 levels on the bright areas**~~
>   ⛔ **FALSE, measured on 21 Aug 2026 — and the `[?]` closes with «it is not true»** (bench
>   `07-b62`, truth scene written by hand into the Y/U/V planes, 343 tiles with all 256 Y
>   levels, expected = the BT.709 **formula** applied to the **decoded** samples):
>
>   | road, same bytes | grey ramp | worst over 847 channels |
>   |---|---|---|
>   | ⭐ **hardware** (`IsHardwareAccelerated=1`, 199 VA-API traces) | gain 1.0002 · offset −0.03 | **0.51 levels** |
>   | software | 0.9998 · −0.02 | 9.41 levels |
>
>   ⇒ On the hardware decoder **there is not even one level of error**, and ⭐ **the highlights are the
>   LEAST wrong band** (−0.08). The real error is on the **software** road, only on the
>   **B** channel and proportional to `|U−128|` (~5 % on the B←U gain): **zero on grey, at any
>   level**.
>
>   ⛔ **And where the «+8» came from**: from bench `07-b48`, which **subtracts the median of the error before
>   judging** — that is, it cancels the very shape of the defect it reported. The «+8» was what
>   remained *outside* the median, read by eye from the first rows of a table. ⚠ Its 27 MB
>   of data no longer exist: the «5 000 superblocks / 30.3 levels» **is not reproducible**.
>
> - ⭐⭐ **And in its place comes a measurement that counts much more: the declared VUI is LOAD-BEARING
>   below 576 lines.** `[M]` same samples encoded bit for bit, **only** the four
>   numbers of the VUI changed:
>
>   | | 1280×720 | ⛔ **768×480** (the minimum of §2.1) |
>   |---|---|---|
>   | VUI **declared** bt709/tv | hardware 709 at **0.42** | hardware 709 at **0.42** |
>   | VUI **«unspecified»** | 709 all the same | ⛔ the hardware reads **BT.601**: 709 wrong by up to **32.41 levels** |
>
>   ⇒ `src/codificatore.c` already writes the four lines, and `[M]` **they really arrive in the stream**
>   (ffprobe on a stream of the real binary: `bt709 / tv / bt709 / bt709`). ⛔ But the **comment** that
>   justified them was false — it said *«709 is what browsers apply by default»*, and at 480p it is
>   not true. Corrected on 21 Aug: **below 576 lines declaring is not prudence, it is load-bearing**.
>
> - ⛔ **And Firefox IGNORES `video_full_range_flag` for H.264** `[M]`: declaring full range gives
>   numbers **identical** to limited ⇒ a wrong image **without an error anywhere**.
>   Limited range is not a choice between two roads: it is the only one the decoder respects.
>
> ⛔⛔⭐ **AND ON 20 AUG 2026 A THIRD ONE WAS ADDED, MEASURED ON THE PRODUCT**: with AV1,
> **Firefox paints rectangular blocks** where Chrome and `ffmpeg/dav1d` — **on the same bytes and
> at the same instant** — are clean. ⇒ Firefox's AV1 decoder was **the defendant of the
> artefact hunt**, and this decision is also its cure. The three images of the same
> instant are in [`fasi/06` §4.9-sexies](fasi/06-la-tela-e-la-vista.md).
>
> ⭐⭐ **CARRIED OUT on 20 Aug 2026**, and measured on the same scene that showed the blocks: Firefox
> **35 delivered = 35 painted**, zero late, zero holes, zero errors, **no blocks**. And the
> two-browser bench (`banchi/07-b51`) gives **4 out of 4 on both**.
>
> **The work that followed, and it is now DONE**: `RCP.md` §4.3 and §6.2 (the codec register,
> today `1` = HEVC and `2` = AV1: the third number **is added**, not reused) · `codificatore.c`
> (`h264_vaapi` **and** the NAL reader that recognises the IDR, because §5.2 wants the real keyframe) ·
> `figlio.c` (the third codec in the per-codec structures) · `pagina.html` (`CODEC_RCP`, the preference
> ladder, and the probe's test stream — which is **really painted** and must be manufactured).
>
> ⚠ **And what this decision does NOT say**: HEVC **stays**, and is still first on the ladder where
> it is available (§1.13). What leaves is **AV1**, which was the universal fallback; the universal fallback becomes H.264.


---

## 2. The numbers

### 2.1 ✅ Minimum: 480p · 25 fps · 24 bit — and it is a guarantee, not a target

*8 Aug 2026.*

It said «30 fps at 1080p», and it was v1's number — which already exceeded it `[M]`: Mutter's capture
delivered 37 frames, KWin 60.

> ⛔ *13 Aug 2026: **the 37 does not reproduce**, and this line cites it as if it were a stable
> fact. At the cadence we asked for, Mutter delivers **31.5** with a median of 33.31 ms; renegotiating
> the cadence alone (monitor 120, brake 90) it delivers `[M]` **61.4** (60.04). The number **is not a
> stable property of Mutter**, and the most likely explanation — the remainder of a truncated division
> — is `[R]`, not `[M]` (§2.5-bis). ⚠ The **minimum** decided here is not touched — it stays very far away in
> both cases.*

The change is one of **nature** more than of value: the minimum stops being a bar to
chase and becomes the **level below which we do not go and do not disconnect**, however bad
the line. It comes from the mobile network case (§3.1), not from giving up on quality.

> ### ⭐ **CONFIRMED ON 23 AUG 2026, and the reason has changed** — *«480p/25fps è il pavimento»*
>
> ⚠ §3.1-bis had taken away from this number its declared reason: *«it comes from the mobile network
> case»*, and that case has left the scenarios to be served. The question was put to the user —
> **raise it or requalify it** — and the answer is that **the number stays 480p · 25 fps**.
>
> ⛔ **What changes is where it comes from.** It is no longer the level a poor line forces on us: it is
> ⭐ **the bottom of the degradation ladder** — the point beyond which phase 9 **is no longer
> allowed to go down**, on a line that the 20 Mbit/s floor declares good.
>
> ⇒ ⭐⭐ **And it is tighter than before, not looser**: before it described an edge case we did not
> promise to serve well; now it is **a constraint on our regulator**. A rate that drops
> below 25 per second on a 20 Mbit/s line **is a defect**, not a successful degradation.
>
> ⚠ And the note of §2.5-bis above stays true for the same reason: *the minimum is not touched —
> it stays very far away* from what the machine delivers.

**Consequence already applied** (`CODER.md` §1): the rule that governs technical choices was
split in two, because a bar that every choice clears no longer filters anything. Upwards it
filters the desired; downwards it constrains the minimum.

### 2.2 ✅ Desired: 4K · 60 fps · 10 bit per channel

*8 Aug 2026. «direi che 10 bit è la scelta giusta».*

It said «colour depth 32 bit», which is not an existing quantity: 32 bpp are 24 bits of
colour plus 8 of alpha, and alpha is not transmitted. The user's intention was *«maximum
quality»*, and under that word lay two distinct levers:

| Lever | Cures | Price |
|---|---|---|
| **10 bit per channel** | banding on gradients | almost nothing, and in hardware everywhere — Android decoder included |
| **4:4:4** | frayed coloured text `[M]` v1 §5.2 | ~50 % bandwidth, **no Android decoder in hardware** |

10 bit chosen: the maximum quality obtainable **on both clients together**, in hardware.

> ### ⭐⭐ 4K IS AN UPPER LIMIT, NOT A PROMISE AT THE FLOOR — *23 Aug 2026*
>
> > *«Il 4K è il limite superiore, e non pretendo di averlo su connessioni a 20 mbps.»*
>
> ⛔ **The question was real and was about to become a debt.** Once the floor of §3.1-bis was opened, an
> agent sent to refute did the sum: a **3840×2160 canvas in motion** asks for
> `[?]` **36 Mbit/s** in the keyframe-only regime and `[?]` **~158 Mbit/s** on a full-screen video
> — while §3.1 promised *«good fixed line, 30+ Mbps ⇒ aim for the desired»*. ⇒ That line
> **promised the desired on a bandwidth that does not carry it**, and nobody had noticed because
> 4K in motion had never been measured.
>
> ⭐ **The user's decision unties the knot without taking anything away from the product:**
>
> | | |
> |---|---|
> | ⭐ **what stays** | 4K · 60 fps · 10 bit is the **ceiling of what the product can do** — the largest size that is encoded and delivered |
> | ⛔ **what it is NO longer** | a promise **at the floor**. At 20 Mbit/s 4K **is not promised in motion**, and it is not a defect: it is the choice |
> | ⚠ **and not even at 30** | the sum says that «good fixed line, 30+» **does not buy** moving 4K. The line of §3.1 that let one believe it was already superseded by §3.1-bis, and this item says so at length |
> | ⭐ **what holds at 20 Mbit/s** | `[?]` 4K **still or slightly moving** (~12 Mbit/s with the rate of real content; the rate measured then, with software encoding, is removed with phase 18) — that is **reading and writing**, not watching a video |
>
> ⇒ ⭐ **The bandwidth at which 4K in motion becomes servable is something to MEASURE and DECLARE,
> not to promise** — it is `SPECIFICHE.md` §2.6 to the letter. The measurement belongs to this phase.
>
> ⚠ **And a technical constraint that adds up, and is not about bandwidth**: `[M]` `h264_vaapi` on this hardware
> stops at **4096 px per side** (3840 passes by a whisker), and the H.264 level in force — 5.1 —
> allows at 3840×2160 `[?]` **30.3 frames per second**, not 60. ⇒ ⛔ **The «60 fps» of the
> desired is not reachable at 4K even with infinite bandwidth**, and this must be measured and written
> before someone discovers it from the wrong side.

### 2.3-bis 🔸 ⛔ The first clue against 10 bits, and it comes from Android

*9 Aug 2026.* The documentation of **mpv** reports that on Android's `mediacodec` path
**10-bit support is limited, and the output is brought back to 8 bit**.

⚠ **It is not a proof**: it is mpv's path, not ours, and MediaCodec in general is not that.
But it is **the first thing that points against the desired of §2.2**, and it comes from the side where we have no
margin.

**Hence the phase 2 probe asks two things instead of one**: that the phone decode HEVC
**Main10** in hardware, **and** that it really return 10 bits. The second can refute §2.2, and
then it is reread there.

### 2.3 🔸 4:4:4 stays a `[?]`, not a promise

It would be an option for the Linux client alone on capable GPUs — ⭐ **and on our hardware the capable GPU
is there**: `[M]` 9 Aug, the Intel UHD 730 encodes **HEVC Main444 and Main444_10**, that is 4:4:4 at 8
**and at 10 bit**, in hardware (the Radeon does not). The «Intel sometimes» this line said was a
`[?]`, and on the reference hardware the answer is **yes**.

⛔ **But it does not reopen the decision, and it must be said why**: 4:4:4 had been set aside for the
**Android** side, where no decoder does it in hardware — and that side has not changed. It stays
what it was: an option for the Linux client alone, behind a switch that is off. What changes is
that now **it can be measured without buying anything**.

But **nobody has measured how much the difference really shows** on the user's desktop:
`LEZIONI.md` §2.3-quater applies. It is decided on a bench that puts the two images side by side, and
the judge is the user (§7.3), behind a switch that is off by default (§2.4).

> ⚠ **Reread on 9 Aug 2026 after §1.6**: «an option for the Linux client alone» no longer has a
> subject — the clients are gone. The substance however does not change, **who decides changes**: 4:4:4
> would remain an option for the **devices whose browser decodes it**, and this is discovered
> **at runtime** instead of on paper. ⭐ It is §2.7 in action: the server offers the maximum, and whoever does not
> reach it receives 4:2:0 — **with the reason declared**, not silently.

### 2.3-ter ⛔⛔ And the second clue is not a clue: **it is a measurement, and it is on our side**

*`[M]` 12 Aug 2026, sub-phase F2.2 of phase 2, on the hardware.*

⛔ **True ten bits do not come out of Mutter's capture by ANY road.** It is not a deduction
from the format we happened to get: **the two roads and the formats by name** were asked for.

| | `[M]` |
|---|---|
| **in memory (MemFd)** | only **BGRx/BGRA** ⇒ 8 bit. Counted on the gradient: **255/256/255 distinct levels**, multiples of 4 at 0.26 |
| **DMA-BUF** | ⭐ Mutter **delivers it** — 388 frames, 4 buffers, modifier **LINEAR**, stride 7680 read from the chunk — ⛔ **but the format is BGRx, 8 bit** |
| **asking for the 10-bit formats alone** | ⛔ `no more input formats`, **on both roads** |
| ⭐ **the positive control** | BGRx asked for in the same way, on the same binary, **succeeds** ⇒ the «no» is the format's, not the tool's |

⇒ ⛔ **The desired of `SPECIFICHE.md` §3.1 — «10 bit per channel» — is not reachable from the
source**, and not because of a choice of ours. `Main10` from here means **eight bits promoted to ten**, and
the label would keep saying it along the whole chain without anyone noticing: the image
comes out fine anyway.

⚠ **And it is not a wall** (§2.7): the server offers the maximum, the client sets the height. ⛔ **But
now the ceiling is upstream**, not downstream — and it must be declared to the user as such, not kept quiet.
⭐ What stays open is no longer *«can our code do 10 bits?»* but **«is there a source that
gives them to us?»**: it is a question for the compositor, and it lives in the phases in which capture is touched.

⭐ *And the prediction had been written beforehand: F2.3 had put on record «if capture gives 8 bits, the whole
chain stays green and the label says Main10 all the same» as a risk to measure. F2.2
answered: **it is a certainty, and the defendant is me**.*

### 2.4 ✅ Latency: a 50 ms cap, a 40 ms target — and only for the piece that is ours

*9 Aug 2026. «Per quello che è sotto il nostro controllo 50 ms (o anche 40) va bene, su
altre cose non possiamo agire».*

It is the **third number**, and before today it did not exist: neither `SPECIFICHE.md` nor v1's specification
named latency, which is the quantity that decides whether a remote desktop is pleasant. Thirty
frames with 40 ms are perfectly usable; sixty with 200 ms are unbearable.

| | From the input that arrives to the frame that leaves |
|---|---|
| **CAP** | 50 ms |
| **TARGET** | 40 ms |

**Only our piece is measured**, and the reason is that a requirement that can be failed without
having done anything wrong — because of a tunnel — is measured by nobody. The total
the user feels is this plus the network: it is declared, not promised.

*Written in `CODER.md` §1-bis, next to the other two numbers.*

⛔ **13 Aug 2026 — the number was measured, and it overshot** (§2.5 and `SPECIFICHE.md` §3.2). ⛔ **And
Mutter's 37-frame wall was not its cause**: the big part was ours, and almost all of it in the
software encoder. *(The measured value, taken with libavcodec's software encoder, is removed:
it no longer holds after phase 18.)* The user's decision stays this; what changes is from whom the
milliseconds are taken.
⛔ **And «the piece that is ours» now has a declared boundary**: the measurement ends at the **finished
drawing**, not at the decoder's callback. They are **11 ms out of 50** that the first draft
gave itself, and it is the part one happily gives away without noticing.

### 2.5 🔸 ⛔⛔ The 40 ms target on GNOME — **MEASURED on 13 Aug, and the cause was NOT Mutter**

*⛔ This item was titled «The 40 ms target is not reachable on GNOME — same wall as
60 fps», and it attributed the delay to the 37-frame wall of capture. **The delay was
measured at phase 3, and it overshoots — but 78 % of it is ours.** The sum below is kept because it was
the estimate on which the decision was taken; the correction is in the box at the bottom, and it counts more than the
estimate.*

The sum, adding up the pieces v1 measured:

| | GNOME (Mutter) | KDE (KWin) |
|---|---|---|
| the desktop reacts and redraws | ~16 ms | ~16 ms |
| **capture delivers the frame to us** | **~27 ms** (37 per second `[M]`) | **~16 ms** (60 per second `[M]`) |
| encoding | 3-6 ms `[M]` phase 9 | 3-6 ms |
| **total** | **~48 ms** — inside the cap, outside the target | **~37 ms** — inside both |

⭐ **It is the same wall as 60 frames at 4K, and for the same reason**: Mutter delivers six
tenths of what it is asked for (`LEZIONI.md` §3, question 6). The latency cap, like that
of the rate, **is largely set by the compositor**.

> ⭐ **And the «no lever of ours moves it» that this item said was removed on 9 Aug
> 2026.** `STUDI.md` §gnome §8.2 found the cause of the six tenths `[R]`: `maxFramerate` does **two
> jobs at once** — brake of the capture and frequency of the virtual monitor — and two clocks at the
> same number beat against each other. Hence a candidate that costs **three cells and zero lines of
> product**: negotiate high and then renegotiate **the cadence alone**, with the monitor still.
>
> ⚠ **It does not change the decision**, which is the user's and rests on the numbers: 50 cap, 40
> target. What changes is that the target **is no longer given up for lost on GNOME before trying**,
> and the test must be done soon — if it succeeds, the whole capture row in this table drops from
> ~27 ms to ~16, and GNOME enters the target like KDE.

⚠⚠ **And this table is an estimate, not a measurement — marked `[?]`.** It is the sum of components
measured separately, which is *precisely* what `LEZIONI.md` §1.7 warns against:
adding up the sender's logs does not say the byte arrived. It serves for orientation, **not for
concluding**. The real number is given by the bench of 2.6, and it can refute it.

> ## ⛔⛔ 13 Aug 2026 — the bench of §2.6 has spoken, and it refuted the table above
>
> *Phase 3, step 5. The estimate said **~48 ms** and blamed Mutter's capture. The measurement
> overshot the cap and blamed us. The prediction was wrong in both ways: in the number
> and in the defendant.*
>
> ⚠ *The total delay capture → glass (bench `banchi/03-b17-ritardo.py`) and the stretch capture → first
> byte in the page were measured with libavcodec's **software encoder** (libsvtav1 / libx265):
> removed, they no longer hold after phase 18. Also removed the browser stretches (stream → `decode()`,
> decoding, drawing), measured on the same chain with the software encoder. What remains are the stretches that
> lie before the encoder or outside it.* It was not input → glass: the input channel is born at phase 4,
> and in its place stood check **P1**.
>
> | where it goes | median | whose it is |
> |---|---|---|
> | drawing → capture (Mutter's `pts`) | 16.66 ms | Mutter |
> | the wire | 0.32 ms | — |
>
> ⛔⛔ **The wall is NOT Mutter's, and the evidence was this**: the scene draws **59.98/s with 0
> waits**; the product's child never waited for Mutter (zero idle waits); the encoder
> was **in software** and the product itself declared it (libsvtav1 / libx265) — the big part of the
> delay lay there, in the stretch capture → wire.
>
> ⛔ **And the 37 wall does not reproduce.** With the monitor at **120** and brake **90**: `[M]` **61.4
> frames delivered per second** (60.04), median interval **16.66 ms**. And the «six tenths» do not
> reproduce either: the low cell gives **a clean 0.50**. ⚠ The box above gave the cause
> of the six tenths as a **beat** between two clocks at the same number: that is wrong too, and
> in its place there is a **quantisation** on the ticks — `min_interval_us = 10⁶/maxFramerate` **truncated
> to an integer** (16666 for 60) against a tick of 16666.67 µs ⇒ whoever falls below loses a whole tick.
> ⛔ **But the quantisation is `[R]`, read in Mutter's code, not `[M]`.**
>
> > ⛔ ⚠ *This paragraph said «Law verified on **13 points**, 8 confirm it, **0
> > refute it**». **It is false**: the file of the grid's outcomes,
> > `banchi/03-b14-esiti-griglia.jsonl`, carries **three lines** — the terrain and **two cells**, both
> > with `scena_sul_mio_monitor: false` ⇒ rejected by the bench itself, which prints «⛔ la legge NON
> > regge su **0 punti su 0**». **Corrected on 13 Aug 2026**, finding of the phase 3
> > coordinator, verified on the two outcome files. ⇒ What remains `[M]` are the **61.4** and the **0.50**, which come
> > from the clean cells of `03-b14-esiti.jsonl`; **the law falls**, and with it the closing of M3
> > (`STUDI.md` §gnome §13).*
>
> ⛔⛔ **But the product today cannot ask for that cure**, and it must be written here or a bench
> measurement is mistaken for a performance: `MOVIMENTO_FPS 60` is a **compile-time constant**
> (`src/figlio.c` · `MOVIMENTO_FPS`), `main.c` has no cadence option, and **`RecordVirtual` does not take
> the frequency** (`src/mutter.h` · the note on `RecordVirtual`) — the four virtual monitors are all **1920×1080@60**. ⇒ The
> «monitor 120 / brake 90» is **`[M]` on the bench and zero in production**.
>
> ⚠ **And 60 is not the 40 ms**: cadence is not latency (`LEZIONI.md` §6.2). The 60 frames
> remove an obstacle; the number is made by the latency, and it is the one above.
>
> ⇒ ⛔ **What changes for the decisions**: the user's decision (50 cap, 40 target,
> and only for our piece) **is not touched** — it is his, and it rests on the numbers. What changes is **the defendant**: the
> delay is not cured by changing compositor, it is cured **on the encoding**, which is phase 8. And the
> sentence *«if the measurement confirmed it, it is not a defect of ours»* falls: the measurement confirmed the overshoot and
> said that **the defect is ours**.

### 2.5-bis ✅ Il tetto di Mutter è accettato: su GNOME il desiderato non si promette

*9 agosto 2026, alla chiusura della fase 0, guardando i numeri misurati.* «Sappiamo che tra tutti i
compositor dei 4 DE Mutter è quello che performa peggio […] GNOME non è in grado di garantire 4K/60
fps, ma va bene. Non sarà adatto per il gaming ma consente comunque una soddisfacente esperienza
desktop e multimedia.»

`[M]` 9 agosto: **36 ± 2 fotogrammi al secondo** su sei giri (33,7-37,8), scena dichiarata,
1080p, copia zero — mentre il client ne disegna **60**. Il tetto è del compositore.

| | |
|---|---|
| **il minimo** (`§2.1`) | lontanissimo, mai in discussione |
| **il desiderato** (`§2.2`) | ⛔ **su GNOME non si promette**. Resta il traguardo dove il compositore lo consente — KWin consegna 58,9 `[M]` sulla stessa macchina, nello stesso pomeriggio |
| il gaming | **fuori**, e non era mai stato dentro |

⚠ **Due cose che questa decisione NON dice**, e vanno tenute accanto o si attribuisce il tetto alla
cosa sbagliata:

1. ⛔ **non è un limite del 4K.** Il costo della risoluzione sulla cattura di Mutter è **zero** fino
   a 4K (`LEZIONI.md` §3, domanda 10): i 36 sono a 1080p, e a 4K sono gli stessi. «GNOME consegna
   ~36 a qualunque misura» è la frase giusta;
2. ⏳ **non chiude M3.** La firma degli intervalli misurata oggi — mediana 33,3 ms, minimo 16,2, mai
   valori intermedi — è quella di due orologi a 60 che battono fra loro, cioè la lettura di
   `STUDI.md` §gnome §8.2. La cura candidata costa **zero righe di prodotto** ed è nella fase 3. Se
   riuscisse, questa voce si riscrive.

> ### ⚠ 13 agosto 2026 — **M3 riesce nel fatto, e questa voce va rimessa in discussione**
>
> *Punto 2 qui sopra: «se riuscisse, questa voce si riscrive». Il fatto è riuscito — ⛔ ma **M3 non
> è chiusa**: la causa non è misurata (`STUDI.md` §gnome §13).*
>
> ⭐ **Il tetto non è del compositore, e la prova è `[M]`**: alla cadenza disaccoppiata GNOME
> consegna **61,4** invece di 31,5, sulla stessa macchina e con la stessa scena.
>
> ⚠ **Il perché è `[R]`**: nel codice di Mutter il freno calcola
> `min_interval_us = 10⁶/maxFramerate` **troncato a intero** (16666 per 60) contro un tick da
> 16666,67 µs ⇒ chi cade sotto perderebbe un tick intero. Non un battimento fra due orologi, una
> **quantizzazione**. ⚠ E la firma «mediana 33,3, minimo 16,2, mai valori intermedi» è quel che una
> griglia produce e due orologi in battimento no — ⛔ **ma è un indizio coerente, non una legge
> misurata**.
>
> > ⛔ ⚠ *Questo capoverso diceva: «è una **quantizzazione**, legge verificata su **13 punti** (8
> > confermano, 0 smentiscono)». **È falso.** `banchi/03-b14-esiti-griglia.jsonl` ha **due sole
> > celle**, tutt'e due con `scena_sul_mio_monitor: false`, e il banco stampa «⛔ la legge NON regge
> > su **0 punti su 0**». **Corretto il 13 agosto 2026**, rilievo del coordinatore della fase 3.*
>
> | monitor | freno | consegnati | mediana | p99 | cella |
> |---|---|---|---|---|---|
> | 60 | 60 | 31,5 | 33,31 ms | 35,53 | **A** |
> | 120 | 120 | 82,9 | 12,12 ms | 18,53 | **B** |
> | 120 | 60 | 46,13 | 24,12 ms | 29,23 | **C** |
> | ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61,4** (60,04) | ⭐ **16,66 ms** | 20,43 | ⭐ **D** |
>
> *Le quattro celle vengono da `banchi/03-b14-esiti.jsonl`, tutte con `scena_sul_mio_monitor: true`
> e coi tre controlli — positivo, negativo, ritorno — che chiudono.*
>
> ⇒ ⛔ **Il «36 ± 2» resta vero alla cadenza che chiedevamo, e smette di essere un muro del
> compositore.** Alla cadenza disaccoppiata GNOME consegna **61,4**, cioè quanto KWin. ⚠ E i «sei
> decimi» **non si riproducono**: la cella bassa dà **0,50 pulito e deterministico**.
>
> ⛔⛔ **Ma la decisione dell'utente NON cambia oggi, e la ragione è che il prodotto non sa
> chiedere quella cadenza**: `MOVIMENTO_FPS 60` è una costante di compilazione (`src/figlio.c` · `MOVIMENTO_FPS`),
> `main.c` non ha opzioni di cadenza, `RecordVirtual` non prende la frequenza (`src/mutter.h` · la nota su `RecordVirtual`) e
> i quattro monitor virtuali sono tutti **@60**. ⇒ Il 61,4 è `[M]` **sul banco** e **zero in
> produzione**. Finché resta così, *«su GNOME il desiderato non si promette»* regge — ⛔ **ma la
> ragione è cambiata: non è più «Mutter non ce la fa», è «noi non gliela chiediamo».** Sono due
> frasi con cure opposte, e la seconda è nostra.
>
> ⚠ **E il ritmo non è il ritardo**: questa voce parla di fotogrammi al secondo. Il ritardo è §2.5,
> sfora, e per il 78 % è nostro (`LEZIONI.md` §6.2).

### 2.7 ✅ ⭐ Il massimo lo offre il server; l'altezza la mette il client

*9 agosto 2026, sul client web. «Meglio così, vorrà dire che una parte delle performance non sarà
più nostro compito. Remotix offrirà il massimo, sarà il client a dover essere all'altezza».*

⭐ **È la regola di §2.4 estesa a una seconda grandezza.** Lì l'utente aveva già stabilito che **si
promette solo il pezzo che è nostro** — la rete non è nostra, quindi si dichiara e non si promette.
Qui lo stesso criterio passa alla **decodifica**: il browser e il silicio del dispositivo non sono
nostri.

| | Di chi è |
|---|---|
| produrre fotogrammi buoni, in tempo, e spingerli sul filo | ⭐ **nostro, e ci si misura** |
| decodificarli e dipingerli | del **dispositivo**: si misura, si dichiara, **non si promette** |

⛔ **E questo toglie alla sonda del browser il potere di uccidere il progetto** (§1.6): se un
telefono decodificasse HEVC in software, non è un difetto di REMOTIX ed è un fatto da scrivere —
non un muro come quello di v1, dove il client lento **era il nostro**.

⚠ **Il confine, e va scritto adesso perché non diventi un alibi**, sono tre righe:

1. ⛔ **il minimo garantito resta una promessa nostra** (§2.1: 480p·25·24 bit), ma è una promessa su
   quel che il **server consegna sulla linea** — non su quel che un browser riesce a dipingere. Un
   client che non tiene il minimo va **detto**, non subìto in silenzio;
2. ⛔ **un ripiego silenzioso resta vietato** (`CODER.md` §4.2): «il client non ce la fa» è
   un'informazione che l'utente deve **vedere**, con la ragione. Due comportamenti sotto la stessa
   etichetta sono la forma d'errore **E2** anche quando la colpa è di qualcun altro;
3. ⚠ **e non ci esonera dal misurare.** «Non è compito nostro» vale per **promettere**, non per
   **sapere**: senza la misura non sapremmo nemmeno che cosa dichiarare, e `LEZIONI.md` §7.4 dice
   che le previsioni non contano — nemmeno quelle che ci fanno comodo.

### 2.6 🔸 Il banco della latenza esiste solo perché il client è nostro

Misurare il ritardo di un desktop remoto richiede di solito **una telecamera** che filma lo
schermo con un cronometro sopra. Qui no: l'input lo iniettiamo noi **e** il client lo scriviamo
noi.

**L'anello chiuso**: il client manda un input che provoca un cambiamento visivo enorme e
inequivocabile — lo schermo che cambia colore — e poi **guarda i fotogrammi che decodifica**
finché non vede il colore nuovo. La differenza fra i due istanti è la latenza vera, misurata
**dal lato che riceve** — la lezione che a v1 è costata tre fasi (`LEZIONI.md` §1.7).

Automatico, ripetibile, senza telecamere e senza nessuno che guardi. È il caso concreto di quel
che l'utente aveva osservato l'8 agosto: possedere il client non toglie solo lezioni, ne rende
alcune **molto più economiche da rispettare**.

> ✅ **Sopravvive intatto al client web** *(9 agosto 2026, §1.6)*: la pagina la scriviamo noi, quindi
> l'anello si chiude come prima — inietta l'input e guarda i fotogrammi che `VideoDecoder` le
> consegna. ⭐ E in dote arriva una cosa che con due client nativi non avevamo: **lo stesso banco
> gira su ogni dispositivo che ha un browser**, telefono compreso, senza compilare niente.

### 2.8 ✅ ⛔ La **tela** non va nel worker — la **decodifica** sì. *Attuato, misurato, tenuto spento*

*13 agosto 2026, fase 3. ⛔ Questa non è una prescrizione rinviata: è una prescrizione **eseguita**.
`STUDI.md` §web §6.1 diceva «WebTransport, decodifica e canvas tutti in un worker dedicato», come strada
migliore. È stata scritta, misurata — e ⭐ **la misura l'ha spaccata in due**, non bocciata in
blocco.*

*⚠ La tabella dei tratti prima/dopo il worker (consegna a `decode()`, decodifica, richiamo → disegno,
disegno → vetro) è tolta: misurata sulla catena col codificatore in software, non vale più dopo la
fase 18. Restano il verso degli effetti e la decisione.*

> ### ⛔⛔ 14 agosto 2026 — **IL TRATTO «richiamo → disegno finito» PORTAVA UN NOME SBAGLIATO**
>
> *Corretto per decisione dell'utente, su due misure indipendenti della fase 4
> (`fasi/rapporti/F4-A2-pagina-dipinge.md`, `F4-A10-anello-input.md`), arrivate alla stessa
> conclusione da due lati senza mettersi d'accordo.*
>
> ⛔ **Il nome del tratto era sbagliato.** Il disegno vero costava poco *(il numero, misurato su una
> catena che passava da `sws_scale`, è tolto con la fase 18)*: quel tratto
> misurava **l'attesa del fotogramma dalla GPU più il disegno**, perché un fotogramma HEVC
> decodificato in hardware esce **opaco** (`format = null`) e la rilettura della marca ne provoca il
> trasferimento GPU→CPU. ⭐ La prova che il confine era messo male: a **palco identico**, cambiando
> codec, «decodifica» e «disegno» si muovono in **versi opposti** e la somma si conserva — ma
> `drawImage` **non sa quale codec** ha prodotto il fotogramma.
>
> ⇒ ⭐ **La lezione, e vale oltre questo tratto**: una riga di scomposizione porta **un numero e un
> nome**. Il numero era `[M]`; il nome era **dedotto** — e nessuna marca distingueva le due metà
> della stessa riga.

⭐⭐ **La decisione, e non è «niente worker»: è DOVE passa il confine.**

| | |
|---|---|
| ⭐ **la decodifica fuori dal thread principale** | ✅ **vale** — il decodificatore consegna prima quando non contende |
| ⛔ **la tela fuori dal thread principale** | ⛔ **affonda il conto**: il disegno e la consegna al worker costano più di quanto la decodifica guadagni |

⛔ **Il meccanismo, ed è la parte che vale oltre questo caso**: una `OffscreenCanvas` in un worker
**si consegna al ritmo del quadro** — un `requestAnimationFrame` implicito che nessuno ha scritto.
`transferControlToOffscreen` impegna al quadro **da sé**. ⇒ Il divieto di `STUDI.md` §web §6.1 non è sulla
parola: **è sul meccanismo**. ⛔⛔ E la prescrizione **conteneva la propria smentita**: prescriveva
il worker e vietava il salto di quadro, che il worker reintroduce in silenzio.

⚠ **E i fotogrammi dipinti dicono il contrario del ritardo, quindi vanno accanto** (`LEZIONI.md`
§6.2): sulla catena vera il worker dipinge **di più**, ma a saturazione il tetto **crolla fino a ≈ il
quadro dei 60 Hz**. *(I numeri, presi con la codifica in software, sono tolti con la fase 18.)* *→ rifatta: `fasi/18-senza-ffmpeg.md` §5.4.*

⇒ **Che cosa si decide oggi**: il codice resta in albero **dietro `#video=worker`, spento**. ⛔ **E
non è una bocciatura definitiva.** ⏳ `[?]` **il limite più grosso, e va letto accanto ai numeri**:
tutto è misurato su **Xvfb, in software, senza GPU**, e la penale è in gran parte sincronizzazione
al quadro. ⇒ **Su hardware vero il conto va rifatto prima di seppellire §6.1** — ed è la ragione
per cui il codice **non** è stato tolto: il giorno della GPU vera il numero si rifà senza
riscrivere niente.

---

## 3. La rete e la degradazione

### 3.1 ✅ I 30 Mbps non sono un pavimento: sono uno scenario

> ⛔ **SUPERATA IN PARTE dal §3.1-bis — 23 agosto 2026.** La riga *«il requisito è
> l'adattamento, non una soglia»* **resta vera e intatta**; ⛔ **la tabella degli scenari no**:
> due righe su tre stanno sotto il pavimento che l'utente ha dichiarato. Sta qui sotto per intero
> perché è la ragione per cui i 30 Mbps non sono mai stati un minimo — e quella ragione non è
> cambiata. ⇒ **La tabella in vigore è quella del §3.1-bis.**

*8 agosto 2026. «il server deve poter fare il suo meglio per offrire la migliore esperienza
possibile a client che si collegano da connessioni critiche (come da una rete mobile).
Ovviamente non pretendo i miracoli come 4K a 300 kbps».*

Scritti come «banda minima 30 mbps» dicevano al programmatore l'opposto dell'intenzione — che
sotto i 30 non si va. Il requisito vero è **l'adattamento**, non una soglia.

Gli scenari da servire:

| Collegamento | Banda | Ritardo e perdita | Che cosa fa il server |
|---|---|---|---|
| fisso buono | 30+ Mbps | bassi | punta al desiderato |
| fisso modesto, WiFi | 5–15 Mbps | medi | **spende tutto quel che c'è** |
| mobile critico | < 2 Mbps, variabile | alti, con perdita | tiene il minimo, **e non stacca** |

### 3.1-bis ✅⭐⭐ ~~La rete minima è **20 Mbit/s**~~ → **30**, ed è un **pavimento dichiarato**

> ⛔ **IL NUMERO È STATO ALZATO LA SERA STESSA → §3.1-sexies.** *«Ho già detto che il pavimento,
> per quanto riguarda la banda, è a 30 mbps»* — 23 agosto 2026, notte. ⭐ **Tutto il ragionamento di
> questa voce resta valido alla lettera**: cambia il numero, non la natura di *pavimento dichiarato*.
> ⚠ I «20» che seguono vanno letti come **30**; sono rimasti scritti perché le misure prese quel
> giorno erano tarate su 20, e riscriverle a posteriori le renderebbe non rileggibili.

*23 agosto 2026, aprendo la fase 9. «ho letto nel piano di connessioni fino a 2 mbps. Mi ero
tenuto più largo: ritengo che una connessione minima debba essere 20 mbps: al di sotto di questo
limite l'utente nemmeno riesce a navigare, figuriamoci usare remotix».*

⭐ **L'argomento è di prodotto, non di codice**: sotto i 20 Mbit/s non è REMOTIX a non
funzionare — è il web a non funzionare. Un prodotto non si tara su una linea su cui **niente**
è usabile.

| | |
|---|---|
| ⛔ **che cosa dice** | **20 Mbit/s è il minimo su cui il prodotto promette qualcosa.** Sotto, REMOTIX **non promette niente e non misura niente come requisito** |
| ⭐ **che cosa si misura, allora** | il banco della fase 9 lavora **a 20 Mbit/s e sopra**. La scala di degradazione serve a coprire i **cali temporanei** di una linea buona — non a servire una linea povera |
| ⚠ **che cosa NON diventa** | non è un rifiuto: nessun codice controlla la banda per staccare qualcuno. **Il divieto di staccare resta intero** (§3.3, I1) — ma sotto i 20 è un comportamento del programma, **non una promessa sulla linea** |
| ⛔ **che cosa esce** | la riga **«mobile critico, sotto i 2 Mbps»** esce dagli scenari da servire — qui e in `SPECIFICHE.md` §8.1 |

**Gli scenari da servire, riscritti:**

| Collegamento | Banda | Ritardo e perdita | Che cosa fa il server |
|---|---|---|---|
| fisso buono | **30+ Mbps** | bassi | punta al desiderato |
| ⭐ **il pavimento** | **20 Mbps** | medi | **spende tutto quel che c'è**, e tiene il minimo dichiarato |
| ⚠ sotto il pavimento | < 20 Mbps | qualsiasi | **fuori dal promesso.** Il programma degrada e non stacca, ma il risultato **non è un requisito e non si misura** |

**Che cosa resta intatto**, e va detto perché non lo si creda travolto:

- **§3.2 (I1)** — intatta alla lettera: il ritmo non cala per prudenza né a scena ferma. ⭐ Cambia
  solo **il punto di lavoro** da cui si comincia a scendere, che va tarato ex novo in fase 9;
- **§3.3** — intatta: si calano i **fotogrammi**, mai sgranare, mai staccare. ⚠ Cambia **quanto
  spesso morde**: a 20 Mbit/s la corsa a fondo scala è un **caso di guasto**, non il caso normale;
- **§5-quater.3** (il cuscino audio di 250 ms) — ⛔ **non c'entra niente con questa voce**: è un
  problema di *thread*, non di banda. Chi attribuisse alla rete nuova quel merito sbaglierebbe.

**Che cosa apre, e non lo chiude questa voce:**

1. ✅ **CHIUSA lo stesso giorno — §2.1, il minimo resta 480p · 25 fps.** *«480p/25fps è il
   pavimento»* — l'utente, 23 agosto 2026. ⛔ **Ma la ragione è cambiata**: non è più il livello a
   cui una linea povera costringe, è **il fondo della scala di degradazione** — il punto oltre il
   quale il regolatore della fase 9 non ha il permesso di scendere su una linea da 20 Mbit/s.
   ⇒ Un ritmo sotto i 25 al secondo lassù **è un difetto**, non una degradazione riuscita.
2. ❓ **un secondo budget, di rete, accanto a quello di GPU** (§4.6): dieci sessioni × 20 Mbit/s
   sono **200 Mbit/s sul filo del server**. Da nominare in fase 9, da misurare in **fase 10**.
3. ⚠ **§2.2/§2.3, il 4:4:4**: l'obiezione *«~50 % di banda»* si indebolisce. ⛔ Il rifiuto però
   **regge lo stesso**, e per l'altra ragione: nessun decoder Android in hardware.
4. ⚠ **`SPECIFICHE.md` §6.4**: il livello H.264 dichiarato è `avc1.640032` (High **5.0**), mentre
   oltre i **40 Mbit/s** servirebbe il tier High con livello **5.1**. Un livello troppo basso non
   dà errore: **fa rifiutare la configurazione dal decodificatore**. Con un tetto di banda più
   alto questa riga diventa mordente.

⭐ **E una coincidenza da dichiarare, non su cui appoggiarsi**: le misure di codifica dei quattro
codec (§1.13-bis) erano già state fatte **«a 20 Mbit/s per tutti»**. ⚠ È il numero del banco che
coincide col numero del prodotto **per caso**, non perché l'uno derivi dall'altro.

*Conseguenze fuori da qui, già applicate il 23 agosto:* `SPECIFICHE.md` §8.1 (la tabella gemella),
`PIANO.md` fase 9 (il banco era scritto **«a 2 Mbit/s»**), `CODER.md` §1-bis (i numeri del progetto).

### 3.1-ter ✅⭐⭐⭐ La banda **non è la sfida**: la sfida è la rete che **perde, riordina e sfarfalla**

*23 agosto 2026, a fase 9 già aperta e mezza misurata. «Comunque voglio farti notare una cosa:
30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti che
perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter».*

⛔⭐ **È una correzione di bersaglio, e arriva al momento giusto**: la fase 9 aveva passato la
giornata a stringere la banda, e il prodotto **aveva retto il caso peggiore senza degradare e
senza nessuna cura accesa** (§16 della fase: `[M]` 21,5-23,1 Mbit/s sul percorso vero, 7 125
fotogrammi consegnati → 7 125 dipinti, **una** chiave, zero abbandoni). ⇒ Un banco che non riesce
a far cedere quel che misura **non sta misurando la grandezza giusta**.

| | |
|---|---|
| ⛔ **che cosa dice** | la banda è un **pavimento già superato dalla realtà**: nessuna linea moderna sta sotto. Il prodotto va misurato sulle **imperfezioni** della linea — perdita, fuori sequenza, jitter — non sulla sua **larghezza** |
| ⭐ **perché è la grandezza giusta** | sono le tre cose che una linea vera fa **anche quando è larga**: il WiFi lontano, la radio mobile, la rete di casa la sera. Sono anche le tre a cui il nostro trasporto reagisce **da solo**, senza che noi lo si sappia |
| ⚠ **che cosa NON annulla** | §3.1-bis resta: i 20 Mbit/s restano **il pavimento dichiarato**. ⭐ Cambia il suo mestiere — non è più la domanda della fase, è la **premessa** su cui si misurano le altre tre |
| ⛔ **che cosa retrocede** | la griglia dei gradini di banda (`09-b70-ritmo.py`, 40 → 10 Mbit/s) resta come **contorno**, non come corpo della fase: la sua domanda è chiusa |

**Le tre grandezze, e non sono la stessa cosa** — ⛔ e confonderle è il modo più facile di
misurare male:

| | che cos'è | che cosa tocca da noi |
|---|---|---|
| **perdita** | il pacchetto non arriva | il **video** va su stream QUIC, che ritrasmettono ⇒ si paga in **ritardo**, non in fotogrammi persi. L'**audio** va su datagram ⇒ si paga in **buchi** |
| **fuori sequenza** | arriva, ma dopo uno più nuovo | ⭐ è la condizione della **cura del riordino dell'audio** del 23 agosto — l'unica cura della giornata la cui metà utile **non è mai stata verificata** |
| **jitter** | arriva a intervalli irregolari | `[?]` QUIC può **scambiarlo per perdita** e stringere la finestra di congestione senza motivo. Se succede, il calo **è nostro** (o dell'algoritmo di congestione, che non abbiamo mai scelto — `webtransport.c` ~2730) |

⭐⭐ **E c'è un'ironia che la voce deve registrare**: la cura del riordino era stata scritta e
applicata **il giorno stesso**, e archiviata come `[?]` proprio perché *«per verificarla bisogna
sporcare la rete e non l'ho fatto»*. La correzione dell'utente **è la condizione mancante** di
quella verifica.

**Che cosa comporta, e sono fatti operativi:**

1. il banco della fase diventa **`09-b76-rete-cattiva.py`**: profili `netem` di perdita (anche a
   **raffica**, che è la perdita vera di una radio), riordino **esplicito**, jitter, duplicazione,
   e il misto «casa cattiva». ⛔ Con i predicati scritti **prima**, e col numero letto da
   `tc -s qdisc show` che dimostra che **il guasto è stato messo davvero** — senza, si misura una
   speranza;
2. **`09-b77-audio-riordino.py`** chiude la cura del riordino, **appaiata**: stessa rete, stessa
   durata, e a cambiare solo la regola. ⛔ Un giro solo con la cura accesa non dimostra niente;
3. il registro del server impara a dire **di chi è la colpa** — pacchetti persi e ritrasmessi
   letti da ngtcp2 accanto a `cwnd` e rtt. ⛔ Oggi «è la rete o siamo noi?» non ha risposta nei
   numeri, e ogni misura sotto perdita finirebbe in una discussione;
4. il `[M]` di `07-b64` — *«al 10 % di perdita la sessione non si apre in 25 s»* — **torna aperto**:
   una stretta di mano QUIC ha il PTO apposta per rimandare quel che si perde, e venticinque
   secondi **non somigliano alla perdita, somigliano a qualcosa che non riprova**.

⛔ **E il `netem` su `lo` diventa una risorsa unica, con un lucchetto** (`banchi/09-lucchetto.py`):
la disciplina si mette sulla **radice** dell'interfaccia, quindi due banchi che guastano insieme
non si dividono il lavoro — **il secondo cancella il guasto del primo, e il primo continua a
misurare credendo di averlo**. ⚠ Non darebbe rosso: darebbe un numero plausibile.

### 3.1-sexies ✅⭐ Il pavimento di banda è **30 Mbit/s**, non 20 — *23 agosto 2026, notte*

*«Ho già detto che il pavimento, per quanto riguarda la banda, è a 30 mbps.»*

⚠ **E qui il registro va corretto, non lisciato**: la mattina del 23 agosto il numero dato era
**20** (*«ritengo che una connessione minima debba essere 20 mbps»*, §3.1-bis), e la fase 9 ci è
stata tarata sopra per una giornata intera. ⇒ Il numero è **30** da questa voce in avanti.

⭐ **Che cosa NON cambia, e va detto perché non si creda travolto:**

- **§3.1-bis resta valida alla lettera**: cambia il numero, non la natura di *pavimento dichiarato* —
  sotto, il prodotto **non promette niente e non misura niente come requisito**, ma non rifiuta
  nessuno e non stacca (§3.3, I1);
- ⛔ **§3.1-ter è ancora più vera**: se 20 Mbit/s non erano una sfida, 30 lo sono ancora meno. Il
  bersaglio della fase resta **perdita, fuori sequenza e jitter**, e questa voce **rafforza** quella
  correzione invece di riaprirla;
- ⛔ **le misure della giornata NON si riscrivono**: sono tarate su 20 e vanno lette per quello che
  sono. `[M]` Il caso duro sul percorso vero (§16) chiedeva **21,5-23,1 Mbit/s**, che col pavimento
  vecchio era il **107-115 %** e col nuovo è il **72-77 %**. ⇒ ⭐ **Col pavimento a 30 il caso duro
  entra, e ci sta comodo**: la decisione sul tetto di banda si semplifica invece di complicarsi;
- ⚠ **§2.1 (480p · 25 fps) non si muove**: è il fondo della **scala di degradazione**, non un
  livello che la banda impone. Con più banda a disposizione, un ritmo sotto i 25/s è **ancora più**
  chiaramente un difetto.

*Conseguenze fuori da qui, applicate lo stesso giorno:* `SPECIFICHE.md` §8.1, `CODER.md` §1-bis,
`PIANO.md` fase 9.

### 3.1-quater ✅⭐⭐⭐ Una linea che perde a raffiche **si dichiara morta**, e l'utente rientra a mano

*23 agosto 2026, notte, dopo aver visto i numeri della rete cattiva. «Se in 10 secondi non arrivano
più pacchetti è chiaro che la connessione è morta. […] se all'interno di un intervallo di 1-2
secondi c'è una perdita di pacchetti piuttosto copiosa direi di trattarla come il caso in cui la
connessione è caduta.»*

⛔ **Da dove nasce, ed è una scelta fra due mali misurati.** `[M]` §17.1 e §17.6: con perdita a
raffiche pesanti (11,10 % vera, in raffiche da 4,5 pacchetti in media) il prodotto ha **due**
comportamenti possibili, e sono brutti tutti e due:

| | che cosa fa | che cosa vede l'utente |
|---|---|---|
| **senza** le cure della fase 9 | la consegna si ferma: 7 secondi su 25 hanno visto un fotogramma | ⛔ lo schermo **congelato per 14,26 s** |
| **con** le cure | consegna tutti i 25 s, ma tenendo la coda | ⛔ l'immagine si muove **con 4,5 s di ritardo** |

⇒ ⭐ **L'utente ha deciso che nessuno dei due va servito**: una linea così **non è una linea lenta,
è una linea rotta**, e va chiamata col suo nome.

| | |
|---|---|
| ⛔ **che cosa dice** | ① **10 secondi senza pacchetti in arrivo** = connessione morta. ② **perdita copiosa dentro una finestra di 1-2 s** = si tratta **come una connessione caduta** |
| ⭐ **che cosa vede l'utente** | ✅ **il filo cade e si rientra a mano.** Scelta esplicita fra tre, il 23 agosto: non un riattacco automatico, non un ripristino invisibile |
| ⚠ **l'obiezione che è stata fatta e superata** | *«su rete cattiva la diagnosi "è caduta la linea" è frequente, e farla pagare con un accesso a mano rende il prodotto inusabile proprio dove serve»*. ⛔ L'utente ha scelto lo stesso, e la decisione è sua |
| ⛔ **il prerequisito** | ⇒ **§3.1-quinquies**: rientrando, l'utente trova **il proprio fantasma** che gli nega il posto. La cura del fantasma **non è più un di più: è la condizione perché questa decisione sia usabile** |

**Che cosa comporta, e la parte difficile non è il codice:**

1. ⛔ **«copiosa» è una parola e deve diventare un numero, con la ragione e i due margini.** I
   confini misurati: **1,71 %** (`casa-cattiva`) è una linea che **regge** e non va dichiarata morta;
   **11,10 %** (`raffica-forte`) non serve nessuno. ⚠ E la regola della famiglia P8→P20 vale qui più
   che altrove: la grandezza dev'essere un **fatto osservabile**, mai un orologio — e una frazione
   calcolata su pochi pacchetti **non è una frazione, è rumore**: sotto un minimo di pacchetti nella
   finestra, il codice **non decide niente**;
2. ⚠ **i 10 secondi non si mettono alla cieca**: `IDLE_MS` di QUIC è **30 000 ms**
   (`SPECIFICHE.md` §5.3) ed è **negoziato col cliente**. ⛔ E c'è un caso da non rompere — la
   scheda del browser finita in secondo piano, che il sistema rallenta o congela (`PIANO.md` A5):
   **un cliente che tace 15 s non è un cliente morto**;
3. ⛔ **nasce dietro un interruttore SPENTO** (I6): questa cura **butta fuori una sessione**, che è
   il cambiamento più visibile che si possa fare. L'utente ha deciso il **comportamento**, non che
   sia acceso senza averlo visto;
4. ⛔ **ogni scatto si dichiara nel registro** con i numeri su cui la decisione è stata presa (I1).
   Una sessione chiusa senza una riga che spieghi perché è indistinguibile da un difetto nostro.

### 3.1-quinquies ✅⭐⭐ Il **fantasma** — dieci secondi, e la frase non deve mentire

*23 agosto 2026, notte. «Se in 10 secondi non arrivano più pacchetti è chiaro che la connessione è
morta.»*

⛔ **Il fatto**, `[M]` misurato lo stesso giorno (§17.5): cade il filo, l'utente riprova a entrare, e
per **30,5 secondi** gli viene detto **«hai già una sessione attiva altrove»**. ⚠ **Per chi la legge
è falsa**: quella sessione è **la sua**, ed è morta un attimo prima. Il conto si chiude senza
sporcare la rete — un addio **perso** e un addio **mai detto** sono lo stesso fatto — ed è
`SILENZIO` (`src/rcp.c` · `SILENZIO`, 30 000 ms).

⛔ E il riquadro di `src/rcp.c:229-233` **dichiara** che quell'orologio *«fa sparire il caso "il
telefono è morto in galleria"»*: non lo fa sparire, lo **dura trenta secondi**.

⛔⛔ **E con §3.1-quater diventa il prerequisito, non un di più**: se una raffica di perdite fa
cadere il filo e l'utente deve **rientrare a mano**, la prima cosa che trova rientrando è il proprio
fantasma. Su una linea che perde a raffiche **si ripete**.

| | |
|---|---|
| ⭐ **che cosa dice** | dieci secondi di silenzio bastano a dichiarare morto un occupante. ⚠ Come si ottenga — abbassare `SILENZIO` o aggiungere una regola più stretta fra client **dello stesso utente** — è di codice, e va scelto guardando **tutto** ciò che si appoggia a quel numero |
| ⛔ **che cosa NON viola** | §8.2, *«nessun client attaccato e **vivo** viene mai spodestato»*: l'occupante qui è attaccato ma **non vivo**. La regola non contraddice §8.2, **la applica** — e va scritto, o il prossimo crederà che sia stata violata |
| ⛔ **il caso che non si rompe** | vale **solo fra client dello stesso utente**. Uno sfratto fra utenti diversi sarebbe un buco di sicurezza, non una comodità |
| ⚠ **e la frase cambia comunque** | *«hai già una sessione attiva altrove»* è una **diagnosi che il server non è in grado di fare**: non sa se l'altro client è un altro dispositivo o lo stesso utente appena caduto. ⇒ Deve dire **quel che sa** — che il posto risulta occupato, e da quanto l'occupante tace |

### 3.1-septies ✅⭐⭐⭐ Le cure della fase 9 si **ACCENDONO** — e il metro della fase è *«solidità, non miracoli»*

*24 agosto 2026, dopo aver guardato. «Il prodotto cambia in meglio; questa fase era per rendere più
solido il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli.»*

⭐⭐ **È la frase che definisce quando la fase è finita**, e va letta come criterio, non come commento:
il traguardo non era **salvare** l'esperienza su qualunque rete — era **non peggiorarla**, non
mentire, e non fingere che una linea rotta sia una linea lenta. ⇒ Misurata contro questo metro, la
fase **ha centrato il bersaglio**; misurata contro «funziona anche al 10 % di perdita», non lo
avrebbe centrato mai, e nessuna quantità di lavoro l'avrebbe fatto.

**Le cinque cure passano da spente ad accese di suo:**

| cura | predefinito nuovo | che cosa compra | ⚠ che cosa costa |
|---|---|---|---|
| **silenzio dell'audio** | acceso | `[M]` **102× meno traffico** a schermo fermo (557,6 → 5,5 kbit/s); tono di prova puro **1,000** | i `mancati` del cliente +2 su 5 000 |
| **sfratto del fantasma** | 15 000 ms | `[M]` il fantasma da **32,13 s / 14 rifiuti** a **16,83 s / 7** | nessuno che si veda; ⛔ non tocca `SILENZIO`, e vale solo fra client dello **stesso** utente |
| **linea morta** | accesa (stallo 5 s · silenzio 10 s) | dice che il filo è rotto invece di lasciare uno schermo fermo che sembra un programma morto | ⛔ **chiude una sessione**: margine **10×** sopra la linea peggiore che regge, **2,9×** sotto quella che non serve |
| **soglia sulla coda** + **regolatore del ritmo** | 100 ms · acceso | `[M]` chiavi da **51,7-88,1 %** a **0,0-5,6 %**; ritmo da **1,7 a 2,8 volte** | ⚠ **fino a +160 ms** di deriva su rete cattiva; **zero** sulla linea sana |

⛔ **Perché erano spente, e perché adesso non lo sono più.** L'invariante **I6** — *ciò che cambia
quel che l'utente vede resta dietro un interruttore spento finché non l'ha guardato* — è servita
esattamente allo scopo per cui esiste: in v1 la fase omologa fu azzerata per aver consegnato numeri
migliorati che il regista non aveva mai visto. ⭐ Il presupposto adesso è **soddisfatto**: l'utente
ha guardato (§19.6 le cure al 10 %, §20.3 il sincronismo) e ha deciso.

⚠ **E una parte dell'attesa era cerimonia, non processo** — va scritto perché non si ripeta: due
delle cinque **non cambiano niente di quel che l'utente vede o sente**. Il silenzio dell'audio è
inudibile *per misura*; lo sfratto del fantasma non aggiunge un messaggio, ⭐ **ne toglie uno falso**.
Tenere spenta una cura che elimina una bugia non è prudenza. ⇒ **I6 vale per ciò che si vede, non per
tutto ciò che si tocca**, e la prossima volta la distinzione va fatta prima.

⛔ **Che cosa NON promettono**, e va scritto accanto ai numeri o qualcuno li leggerà come una
promessa: `[M]` §19.6 — **al 10 % di perdita le cure non salvano l'esperienza.** Curano il
meccanismo (la consegna continua invece di fermarsi, i fotogrammi mai spediti da 27 a 1) e l'utente
dice *«bloccato»* lo stesso. ⇒ Sopra una certa perdita la scala di degradazione **non ha più niente
da offrire**, e l'unica risposta onesta resta §3.1-quater: **dichiarare la linea morta**.

### 3.2 🔸 L'invariante I1, riscritta

Il ritmo **non cala mai** per prudenza, per risparmio o perché la scena è ferma. Cala **solo**
quando la misura dimostra che la linea non porta, e ogni discesa è dichiarata nel registro.

La ferita della fase 10 di v1 resta protetta — il divieto di risparmiare è intatto — ma non
impedisce più di cedere quando cedere è l'unica cosa sensata. Vietata l'euristica prudente,
obbligatorio l'adattamento misurato.

*Applicata in `CODER.md` §2 e `REVIEWER.md` §3, che vanno in coppia.*

### 3.3 ✅ Sotto il minimo si calano i fotogrammi. Mai sgranare, mai staccare.

*8 agosto 2026. «continuare a calare i fotogrammi, mai staccare».*

Su un desktop **degradare nel tempo è meglio che degradare nello spazio**: a pochi fotogrammi
al secondo ognuno resta nitido e il testo si legge — è lento ma ci si lavora. Sgranando
l'immagine il testo diventa illeggibile e non ci si fa più niente. E a ritmo basso si possono
spendere più bit su ciascun fotogramma: la lentezza si paga una volta sola.

### 3.4 🔸 «Segni di vita» si verifica dal lato che riceve

Un client è vivo se **arrivano suoi pacchetti**, non se noi non abbiamo ricevuto errori
(`LEZIONI.md` §1.7). QUIC lo fa di suo, col proprio battito e il proprio tempo di inattività:
non va inventato, va letto dal lato giusto.

---

## 4. La sessione

### 4.1 ✅ La sessione sopravvive al client; è l'utente a chiudere e riprendere

*8 agosto 2026. «è l'utente da solo che capisce che è meglio chiudere il client (tenendo la
sessione aperta) e continuare quando la situazione migliora».*

È l'invariante I4 di v1 (`palco.c`, 1.545 righe, fra il codice che sopravvive), qui promossa
da dettaglio implementativo a **comportamento promesso all'utente**.

### 4.1-bis ✅ ⭐ Il server non butta fuori una sessione sana — e ogni chiusura sua ha un motivo che sa spiegare

*Decisa dall'utente l'**11 agosto 2026**, in coda alla decisione §7.14: «il server non deve
attaccare. È l'utente che decide di fare il logout oppure chiude il client (la scheda del browser)».*

⛔ **A chiudere è l'utente.** Il server non termina **mai** una sessione che sta funzionando: chi se
ne va, se ne va perché ha deciso di andarsene — con il logout o chiudendo la scheda. È §4.1 vista
dall'altro lato: là la sessione **sopravvive** al client, qui il server **non la porta via**.

> ### ⚠ E la formulazione stretta è stata scelta sapendo quale scartava
>
> *Le due letture sono state messe davanti all'utente l'11 agosto, e ha scelto la prima.*
>
> | | |
> |---|---|
> | ✅ **scelta** | *il server non butta fuori una sessione **sana**; chiude solo per un motivo che sa spiegare* |
> | ❌ **scartata** | *il server non chiude **mai**, in nessun caso* — ⛔ e cadrebbero il ban di §1.9, il rifiuto delle credenziali, la regola di rigore di `RCP.md` §3 e i tre tetti di §4.6, cioè quattro difese di cui **tre decise dall'utente stesso** |

⭐ **Che cosa questa regola vieta davvero, ed è più di quanto sembri**: vieta la chiusura **senza
motivo dicibile**. Non esiste una sessione che finisce «perché sì», né una che finisce con un
numero al posto di una frase. ⛔ Ogni percorso in cui il server chiude **deve** portarsi dietro un
motivo di `RCP.md` §8.2 **e** la frase che l'utente legge — e se un percorso non ce l'ha, quel
percorso è un difetto, non una svista.

**Le chiusure che restano, e ciascuna ha il suo motivo dicibile:**

| chi chiude | perché resta |
|---|---|
| il ban dopo tre tentativi (`§1.9`, `RCP.md` §4.4-bis) | ⭐ **deciso dall'utente il 10 agosto**, e chi è bannato **vede una pagina che glielo dice** |
| le credenziali sbagliate — `RESPINTO` | è il congedo dell'autenticazione, `RCP.md` §4.4 |
| la regola di rigore — `ERRORE_PROTOCOLLO` | `RCP.md` §3: chi riceve qualcosa che non capisce **deve** chiudere, o un difetto passa inosservato |
| i tre tetti della stretta di mano — `TEMPO_SCADUTO` | `RCP.md` §4.6, e sono **prima** che una sessione esista: non c'è ancora niente di sano da buttare fuori |
| l'utente è già collegato altrove — `GIA_ATTIVA_REMOTA` | invariante I2 |
| ⚠ **lo stacco a 30 minuti senza input** (`§4.3`) e **la chiusura a 6 ore** (`§4.2`) | ⛔ **decise dall'utente l'8 agosto**, e sono le due che sembrano contraddire questa regola e non la contraddicono: la prima **stacca il client e lascia viva la sessione**, la seconda raccoglie le risorse di una sessione che **non dà segni di vita da sei ore** — cioè non è più «sana», è abbandonata |

⛔ **E questa regola si misura, non si dichiara.** Il banco che la verifica esiste già ed è **B7**:
provoca ogni motivo di congedo e controlla che arrivi **dal lato che lo riceve**, con una frase
distinta per ciascuno. ⭐ Da oggi B7 non conta più solo *«sette motivi su sette»*: ⛔ **è il banco di
questa decisione**, e il suo denominatore è *«quanti percorsi di chiusura ha il server»* — non
*«quanti ne conosco»*. Un percorso che chiude senza un motivo dicibile **non compare** in un banco
che parte dall'elenco dei motivi: si trova solo partendo dal codice.

⚠ **Tocca `DECISIONI.md` §7.17, che è ancora ❓**: una sessione WebTransport che non apre mai il
canale di controllo oggi **non ha addosso nessun tetto** e resta lì per sempre. Non è una sessione
sana — non è una sessione affatto — quindi questa regola non la protegge. **Ma quanto possa restare
lì resta da decidere**, e non lo decide questa riga.

### 4.1-ter ✅ ⭐⭐ Le due uscite non sono la stessa uscita: il filo che cade, e il logout

*Decisa dall'utente il **15 agosto 2026**, all'apertura della fase 5: «distinguiamo il comportamento
del PC usato dall'utente rispetto a quello che fa REMOTIX. Se l'utente chiude, spegne o riavvia il
**proprio** PC, questo lo trattiamo come browser chiuso / connessione caduta. Se invece sceglie la
voce «Esci/logout», allora significa che l'utente vuole **terminare la sessione**, il che comporta
la chiusura di tutti i programmi che aveva in esecuzione».*

§4.1-bis diceva **chi** chiude — l'utente, non il server. Questa dice che quell'utente ha **due
gesti**, e che portano a due posti diversi.

| il gesto | che cos'è per noi | l'esito |
|---|---|---|
| ⭐ **il filo cade** — scheda chiusa, browser chiuso, **il PC dell'utente spento o riavviato**, il campo perso in galleria | ⭐ **un caso solo**, e non c'è niente da distinguere: il PC dell'utente non è un attore del nostro modello | il posto si libera, **la sessione resta viva** (I4). Il `CONGEDO 0x01` parte se fa in tempo; se il PC muore di colpo non parte, e a liberare il posto è l'orologio del silenzio a 30 s (§4.4) — **stesso esito, altra strada** |
| ⭐ **«Esci/logout» dal menu del desktop** | l'unico gesto che dichiara *«ho finito»* | ⛔ **la sessione finisce, e i programmi dell'utente si chiudono**. Niente a cui riattaccarsi |

⭐ **Il guadagno di questa distinzione è che toglie lavoro invece di aggiungerne**: il lato client non
deve rilevare niente — spegnimento, riavvio e chiusura della scheda sono **la stessa cosa già
implementata e misurata** (`pagehide` → `CONGEDO`, `pagina.html` · `canale_corrente()`).

**E tre conseguenze che non sono state scelte, sono cadute da sole:**

1. ⛔ **`org.gnome.desktop.lockdown disable-log-out` è VIETATA.** Toglieva la voce «Esci…» **e**
   faceva rifiutare `org.gnome.SessionManager.Logout` (`STUDI.md` §gnome §5.1). Adesso che il logout è una
   funzione **promessa**, quella chiave toglierebbe la funzione. ⇒ per togliere Spegni/Riavvia/
   Sospendi resta **solo** la regola polkit su logind, e ⭐ il congedo del server
   (`sessione_termina()`) e il logout dell'utente **passano dalla stessa porta**.
2. **`org.gnome.shell always-show-log-out` va acceso.** `[R]` `systemActions.js:394-410`: senza,
   su una macchina con un utente e una sessione sola gnome-shell **non mostra** la voce. ⚠ Rovescia
   `reference-gnome/rapporti/02-shell-blocco-voci.md:214` — *«va lasciata `false`»* — scritta quando
   l'obiettivo era togliere voci, non darne una.
3. **Fra il clic e la fine non tocchiamo niente**: un programma con lavoro non salvato fa comparire
   il dialogo **di GNOME** dentro il desktop remoto, come se l'utente fosse al monitor (I8).

### 4.1-quater ✅ ⭐ Dopo il logout la pagina torna al modulo di accesso — e il motivo è nuovo

*Proposta e accettata dall'utente il **15 agosto 2026**: «concordo, la pagina torna al modulo di
accesso».*

Finito il logout, il browser sta guardando **l'ultimo fotogramma di un desktop che non esiste più**.
La pagina **torna al modulo di accesso**, con sopra la riga *«la sessione è terminata»*: chi voleva
uscire ha finito, chi ha cliccato per sbaglio rientra scrivendo la password e trova un desktop
pulito. ⛔ **Non una schermata di chiusura**, che sarebbe un vicolo cieco da cui si esce ricaricando.

⛔ **E serve un motivo nuovo — `0x10 SESSIONE_TERMINATA` (`RCP.md` §8.2)**, non il riuso di `0x01`:
`CHIUSO_DALL_UTENTE` porta con sé la promessa *«riattacca e ritrovi tutto»*, che dopo un logout è
**falsa**. Due esiti opposti sotto lo stesso codice sono la forma di difetto che `CODER.md` §4.2
vieta: un ripiego silenzioso produce due comportamenti sotto la stessa etichetta.

⚠ **E il difetto vero di questo percorso è l'ORDINE, non il codice**: quando Mutter cade, il palco
cade con lui e il canale non serve più. Il motivo deve partire **prima**. È la stessa forma del
rilievo **B-7** — un motivo che esiste e che nessuno spedisce in tempo.

### 4.1-quinquies ✅ ⭐ Il logout ha anche una scorciatoia — `Ctrl+Alt+Fine`, e la gestisce la PAGINA

*Voluta dall'utente il **15 agosto 2026**: «vorrei venire incontro all'utente per permettergli di
effettuare il logout anche usando una combinazione di tasti». La combinazione l'ha scelta lui, fra
tre proposte.*

⛔ **Due combinazioni sono state provate e scartate PRIMA di scrivere una riga, e con una misura
ciascuna** — vanno scritte qui o qualcuno le riproporrà:

| scartata | perché, con la marca |
|---|---|
| ❌ `Ctrl+Alt+F12` — la prima idea dell'utente | `[R]` è il **predefinito di `switch-to-session-12`** (`org.gnome.mutter.wayland`), e Mutter la registra anche in headless perché il backend resta quello **nativo** (`keybindings.c:2797`, `NATIVE_KEYBINDINGS`). ⛔ È **`NON_MASKABLE`**: nessuna applicazione può prendersela. Iniettata, verrebbe ingoiata e Mutter proverebbe a passare a una console virtuale **che in headless non esiste** — un avviso nel registro e nient'altro. ⛔ **E sul PC dell'utente, se è Linux, non arriva neppure al browser**: la prende il suo compositore, per lo stesso identico motivo |
| ❌ `Win+F12` — la seconda | ⭐ `[M]` **misurato in casa, 14 agosto**: nel catalogo della sonda S3 `Super+KeyD` è **`non-consegnata` in tutti e quattro i palchi** — finestra, schermo intero, schermo intero **con la Keyboard Lock concessa**, e PWA installata. Le combinazioni col tasto Windows **non arrivano mai** alla pagina. ⛔ E su Android e DeX **ogni** combinazione con Meta è persa per regola AOSP — cioè proprio dove serve di più (`SPECIFICHE.md` §7.3-bis) |

✅ **Scelta: `Ctrl+Alt+Fine`.** ⭐ `[R]` **Non la lega nessuno**: cercata come `<Primary><Alt>End` in
tutte le fonti di GNOME e di KDE che abbiamo in casa, zero riscontri. ⚠ **E i due prezzi, dichiarati
perché l'utente li ha scelti sapendoli**: ha **due** modificatori invece di tre, quindi è più facile
premerla per sbaglio; e ha un **precedente RDP che dice un'altra cosa** — lì `Ctrl+Alt+End` manda
`Ctrl+Alt+Canc` alla sessione remota, quindi chi viene da RDP potrebbe aspettarsi quello.

**⭐ La gestisce la PAGINA, non il desktop**, e le tre ragioni sono di peso diverso:

1. **una volta invece di quattro**: legata al desktop andrebbe rifatta per GNOME, KDE, XFCE e LXQt,
   ciascuno col suo modo — cioè quattro righe di configurazione, che è I7 in agguato;
2. ⭐ **funziona quando serve**: legata al desktop, il tasto dovrebbe attraversare browser → rete →
   `libei` → compositore, e non arriverebbe proprio nel caso in cui uno la cerca — col desktop che
   non risponde più;
3. **finisce nella stessa porta del menu**: `org.gnome.SessionManager.Logout`, cioè
   `sessione_termina()`. ⇒ un solo percorso di uscita, non due che possono divergere.

⛔ **E la pagina la ingoia con `preventDefault()`: nella sessione remota quella combinazione non
arriverà mai.** È il prezzo di ogni scorciatoia di REMOTIX, e `SPECIFICHE.md` §7.3-bis obbliga a
**dichiararlo** invece di lasciarlo scoprire.

**Una cosa che viene con lei, e una che è stata tolta:**

- ⭐ **una conferma a schermo** — *«terminare la sessione?»*. Dal menu il logout costa tre gesti
  deliberati; una combinazione ne costa uno, e chiude **tutti** i programmi aperti. ⚠ La conferma è
  anche la difesa dal fraintendimento RDP di qui sopra: chi si aspettava `Ctrl+Alt+Canc` legge che
  cosa sta per succedere e annulla;
- ⛔ **nessun bottone a schermo per il logout** — *tolto dall'utente il 15 agosto 2026: «per quello
  basta la voce del menu di sistema»*. ⭐ **E aveva ragione contro l'argomento con cui gliel'avevo
  proposto**: avevo trasferito al logout il ragionamento di `Ctrl+Alt+Canc` (`SPECIFICHE.md`
  §7.3-bis), che il bottone ce l'ha perché **non ha nessuna voce di menu**. Il logout ce l'ha, e
  quella voce si raggiunge **col puntatore e col dito** — quindi esiste anche dove la tastiera si
  perde tutta, iPhone compreso. ⇒ ⚠ **La regola generale, da non ripagare**: un bottone a schermo si
  giustifica quando **non esiste un'altra strada**, non quando la strada che c'è passa da un tasto.

⚠ **E prima di essere promessa va MISURATA**: la sonda S3 (`banchi/04-b29-scorciatoie.py`) ha
provato 42 combinazioni su due motori e `Ctrl+Alt+Fine` **non è fra quelle**. Si aggiunge, si misura
su due motori, e se su uno non arriva la pagina lo **dichiara** — §7.3-bis: *non si finge che
funzionino*.

### 4.2 ✅ Dopo 6 ore senza segni di vita la sessione viene chiusa

*8 agosto 2026, proposta dall'utente.* Il valore resta, e con §4.3 il suo mestiere è chiarito:
**raccogliere le risorse**, non difendere la sicurezza — di quella si occupa lo stacco a 30
minuti. Su un server multi-utente ogni sessione dimenticata tiene memoria, GPU e un
codificatore.

### 4.3 ✅ Il blocco è di REMOTIX, non del desktop — 30 minuti senza input, poi stacco

*8 agosto 2026. «Se non arriva input dall'utente per 30 minuti la sessione si blocca:
l'utente dovrà fare il re-attach con user e password».*

Dopo 30 minuti senza input, REMOTIX **stacca il client**. Il desktop resta com'era, ma non lo
vede più nessuno: per rivederlo serve un attacco nuovo, con utente e password.

⛔ **Il blocco schermo dei desktop resta spento**, com'era in v1 — `--no-lockscreen` su KWin e
gli equivalenti sugli altri tre. Non è una svista ereditata: è una dipendenza, e ora ha una
ragione scritta. Le quattro strade del «modo A» sono queste, tutte `[R]`:

| Desktop | Che cosa succede bloccando davvero |
|---|---|
| **GNOME** | ⛔ **la revoca.** Entrando nel dialogo di sblocco, gnome-shell chiama `inhibit_remote_access()` e Mutter **chiude ScreenCast, RemoteDesktop e InputCapture, rifiutando di ricrearli** (`STUDI.md` §gnome §4). C'è l'eccezione `is_headless()`, che è il nostro caso — ma è letta nel codice e **mai misurata** |
| **KDE** | ⛔ **la catena che si morde la coda.** A blocco attivo la nostra inibizione è ignorata (`powerdevilpolicyagent.cpp:509`); powerdevil spegne lo schermo a 10 minuti; con zero uscite KWin monta un output fittizio **con un filtro che inghiotte tutto l'input** (`STUDI.md` §kde §10.2-10.3). Ci si blocca e non si sblocca più |
| **XFCE, LXQt** | i loro demoni di inattività, e su LXQt `enableIdlenessWatcher=false` **viene riscritto a `true`** dal demone al primo avvio (`STUDI.md` §lxqt) |

**Le tre ragioni della scelta**, in ordine di peso:

1. **un comportamento solo per quattro desktop**, invece di quattro cure fragili — e tre di
   quelle cure sarebbero righe di configurazione, cioè ciò che l'invariante **I7** vieta;
2. **il conteggio è nostro e non ha incognite**: l'input lo iniettiamo noi, quindi sappiamo
   esattamente quando è passato l'ultimo. Col modo A dovremmo fidarci che il rilevatore di
   inattività di ciascun desktop veda gli eventi di `libei` — su KDE è `[R]` che sì
   (EIS → `simulateUserActivity`), sugli altri tre sarebbe da misurare;
3. **la sicurezza è la stessa**: l'unica strada per quel desktop passa da RCP, e RCP passa
   da PAM. La schermata di blocco chiederebbe la medesima password.

> ⚠ **E questa decisione ha una condizione di scadenza, posta dall'utente lo stesso giorno:**
> *«non escludo che un domani potremmo implementare un metodo di autenticazione molto più forte
> della semplice password, ma per il momento va bene solo questa»*.
>
> Il ragionamento del punto 3 **regge solo finché la password PAM è l'unica chiave**. Il giorno
> in cui RCP autenticasse con qualcosa di diverso — un gettone sul dispositivo, una chiave, un
> secondo fattore — il blocco del desktop smetterebbe di essere ridondante e diventerebbe una
> difesa vera, perché chiederebbe una chiave **che chi ha rubato la prima non ha**.
>
> **Chi implementa l'autenticazione forte rilegge questa voce**, e non la dà per acquisita.
>
> ⏳ **E quel giorno ha una data di apertura, decisa il 9 agosto 2026**: l'evoluzione con l'MFA,
> rinviata a progetto completato — §1.7, il riquadro del debito di sicurezza.

### 4.3-bis 🔸 ⛔ Essere *headless* su GNOME è un requisito, non una fortuna

*Scritta il 9 agosto 2026, leggendo `STUDI.md` §gnome §4 e la lezione 3 del suo §14.*

§4.3 dice che il blocca-schermo dei desktop resta spento, e per GNOME la ragione è la **revoca**:
entrando nel dialogo di sblocco, Mutter chiude cattura, controllo e input **e rifiuta di
ricrearli**. L'unica eccezione è `is_headless()` — e quella eccezione è la nostra condizione.

⛔ **Ma non è una condizione che abbiamo chiesto.** Mutter si mette in headless **da solo** quando
la sessione logind è di tipo `wayland`, attiva e **senza seat** `[R]`. Nessuna nostra riga la
chiede, nessuna la verifica, e il giorno in cui la sessione nascesse con un seat — un `gdm3`
configurato diversamente, una prova fatta a mano, un ripristino incompleto — perderemmo cattura e
input **senza che nessuno colleghi le due cose**.

**Da cui, e sono tre obblighi distinti:**

1. la sessione si compone **dichiarando** che deve essere headless, non sperando che lo diventi;
2. l'esito si **verifica dopo l'avvio**, come per il tema del cursore trasparente di §5-bis.2 —
   che il presupposto sia scritto non è che sia stato ottenuto (`REVIEWER.md` E1: necessario non
   è sufficiente);
3. se non lo è, si **dichiara il fallimento** invece di proseguire: sarebbe una sessione che
   funziona finché nessuno blocca lo schermo (`CODER.md` §3.9, §4.2).

⭐ **È l'invariante I7 in una forma che non avevamo previsto.** I7 dice che la protezione di un
difetto noto non sta in una riga di configurazione che si può perdere; qui non sta **da nessuna
parte** — sta in un comportamento di ripiego di Mutter. `STUDI.md` §gnome §14 lo scrive meglio: *una
condizione che ci salva per accidente va scritta come requisito.*

⚠ E la misura che la chiude è **M2** di `STUDI.md` §gnome §13: headless sì/no contro
`inhibit_remote_access`. Fino ad allora la clausola di scadenza di §4.3 vale anche qui.

### 4.4 ✅ Un client che tace è un client che si è staccato

*8 agosto 2026. «Fantasma: lo trattiamo come nel caso in cui l'utente chiude il client».*

Nessuna connessione «tiene il posto». Chi tace è staccato, chi arriva entra — senza timeout da
aspettare, senza subentro da negoziare, senza il caso «il telefono è morto in galleria e ora
non posso rientrare dalla mia sessione» che v1 aveva dovuto tamponare con keepalive stretti.

Sparisce così anche il bivio *subentro contro attesa*: non esiste più, perché non esiste il
posto occupato.

> ### ⛔ Precisata la sera del 9 agosto 2026 — questa voce parlava solo del **fantasma**
>
> *«Se un utente ha già una sessione grafica remota attiva, e ne vuole attivare una seconda da un
> secondo device, la seconda connessione viene rifiutata.»*
>
> La revisione di `RCP.md` ha trovato che il protocollo non sapeva esprimere il caso **remoto
> contro remoto** — sei attaccato dal portatile e apri dal telefono — e che i motivi disponibili
> dicevano tutti «locale», cioè avrebbero mostrato all'utente una frase falsa.
>
> ⭐ **La regola completa sono due righe, e il discrimine è l'orologio del silenzio:**
>
> | Il client che c'era | Che cosa succede a chi arriva |
> |---|---|
> | **tace da 30 secondi** — il fantasma di questa voce | è **staccato**, non occupa niente: chi arriva **entra** |
> | **è vivo e attaccato** | chi arriva è **rifiutato**, con `GIA_ATTIVA_REMOTA` (`RCP.md` §8.2) |
>
> ⭐ **La seconda riga non è nuova: è l'invariante I2** — *«la seconda connessione è rifiutata con
> messaggio esplicito»* — che nessuno aveva collegato a questa voce. E il nuovo motivo è il gemello
> remoto di `GIA_ATTIVA_LOCALE`, così come `SPECIFICHE.md` §5.1 ha già la coppia locale.
>
> ⚠ **Il prezzo, dichiarato**: se il portatile si spegne di colpo senza congedarsi, dal telefono si
> entra **dopo trenta secondi**. È lo stesso orologio di §4.5, e nessuno l'ha spostato.

### 4.5 🔸 I tre orologi della sessione

Le decisioni 4.1-4.4 mettono in fila tre tempi diversi, che vanno tenuti distinti perché
misurano cose diverse:

| Orologio | Quanto | Che cosa scatta | Deciso in |
|---|---|---|---|
| **silenzio del client** | **30 secondi** | il client si considera staccato | §4.4, valore in §7.3-bis |
| **inattività dell'utente** | **30 minuti** senza input | REMOTIX stacca il client | §4.3 |
| **abbandono della sessione** | **6 ore** senza alcun attacco | la sessione viene chiusa, con congedo pulito | §4.2 |

Sono in scala: il primo si misura in secondi, il secondo in minuti, il terzo in ore. Un utente
che lascia il client aperto e va a pranzo viene staccato dopo mezz'ora e ritrova tutto
riattaccandosi; se non torna entro le sei ore successive, la sessione viene raccolta.

⚠ **Una conseguenza da tenere d'occhio**: «input» è quel che l'utente manda, non quel che
guarda. Chi resta mezz'ora a guardare un video senza toccare nulla viene staccato. Il costo è
piccolo — riattaccarsi è rapido — ma se emergesse come fastidio, la cura è un cenno di
presenza dal client, non l'allungamento della soglia.

### 4.6 ✅ Dieci sessioni grafiche come tetto — ma il limite è un budget, non un conteggio

*9 agosto 2026. «Quante sessioni grafiche può reggere contemporaneamente il sistema fra locali e
remote? […] credo che 10 potrebbe essere un numero molto comodo». E poi: «il mio è un tetto: non
capiterà mai che ci sono 10 utenti contemporaneamente che si collegano con client in 4K».*

> ⚠ **E alla fase 1 questo tetto non è onorato, ed è un ripiego dichiarato**: il server gira su **un
> filo solo** e la verifica PAM lo **blocca**, quindi dieci utenti che entrano insieme si mettono in
> fila (con il secondo fisso di `RCP.md` §4.4-bis, l'ultimo aspetta **dieci secondi**); e la tabella
> delle sessioni attaccate è un `#define` a **16**. ⛔ Non è una decisione che cambia: è una promessa
> **non ancora dovuta**, e sta scritta in `SPECIFICHE.md` §5.5 e in `FASI.md` §01-filo-nudo perché il
> giorno in cui sarà dovuta si sappia da dove ripartire. *Portata fuori dal commento in `src/main.c`
> l'11 agosto 2026, rilievo **R12C.17**.*

⛔ **Dieci non è il limite: è il tetto amministrativo.** Il limite vero lo pone il
**codificatore**, e si misura in pixel al secondo — con lo stesso ferro, le stesse dieci sessioni
sono facilissime o impossibili a seconda della qualità che ciascuna chiede.

> ⛔⛔ **QUESTA RIGA È STATA CORRETTA IL 24 AGOSTO 2026, E DALLA MISURA: il limite NON lo pone il
> codificatore.** Lo pone **la composizione**, che cede alla **metà** — e il resto della sezione,
> tabella compresa, va letto con davanti **§4.6-nonies**. ⭐ La parte che regge è *«il limite è un
> budget, non un conteggio»*: quella la misura l'ha **confermata**. ⛔ Quel che cade è **di quale
> motore** sia il budget.

Sul ferro di prova — i5-13500T, 31 GB, Intel UHD 730 (Alder Lake) `[M]` 9 agosto:

| 10 sessioni a… | Da codificare | Sulla sola Intel |
|---|---|---|
| 480p · 25 fps *(il minimo)* | ~100 Mpixel/s | ⭐ larghissimo, una cinquantina |
| 1080p · 30 fps | ~620 Mpixel/s | ✅ giusto al limite |
| 4K · 60 fps *(il desiderato)* | ~5 Gpixel/s | ⛔ **una sola sessione** |

> ### ✅ Confermate `[M]` il 9 agosto 2026 — `vainfo` installato ed eseguito sul ferro
>
> *Erano `[?]`, ricavate dalla generazione del chip. Ora sono lette dal driver, sui due nodi.*
>
> | | Intel UHD 730 — `renderD128`, iHD 25.2.3 | Radeon RX 6800 — `renderD129`, radeonsi navi21 |
> |---|---|---|
> | **HEVC Main10 in codifica** | ✅ **sì** (`EncSliceLP`) | ✅ sì (`EncSlice`) |
> | HEVC Main **4:4:4**, 8 e 10 bit | ⭐ ✅ **sì** — vedi §2.3 | ⛔ no |
> | H.264, VP9, JPEG in codifica | sì | H.264 sì |
> | **AV1** | ⛔ **nessun profilo, nemmeno in decodifica** | solo **decodifica** (`AV1Profile0`, `VLD`) |
>
> ⛔ **Il desiderato a 10 bit ha la sua strada in hardware su tutt'e due le schede**, e passa da
> HEVC Main10 come `SPECIFICHE.md` §11.4 prevedeva. La scala di preferenza di §11.4 resta valida:
> `hevc_vaapi` è la prima voce e la macchina ce l'ha.
>
> ⚠ **Un dettaglio da non perdere, che tocca la fase 8**: sull'Intel l'unico ingresso di codifica è
> `EncSliceLP` — il percorso *low power*. Non è un ripiego, è il solo che quel chip espone; ma è
> un percorso con opzioni di controllo del bitrate proprie, ed è precisamente il posto dove v1 si
> è fatto male due volte (`LEZIONI.md` §1.8: il driver che deduceva il modo di controllo da come
> erano riempiti due campi, banda costante senza che nessuno l'avesse scelta). **Si chiede per
> nome e si verifica che abbia obbedito.**
>
> ⭐ E la tabella del budget qui sopra resta `[?]` per un'altra ragione: `vainfo` dice **quali
> profili** ci sono, non **quanti pixel al secondo**. Il numero di sessioni va misurato saturando,
> ed è la fase 10.

**Da cui il disegno**: nessun numero cablato nel programma. Il server tiene un **budget** — sa
quanto sta già codificando e quanto può — e il dieci è il valore predefinito di un massimo
configurabile, come le sei ore di §4.2. La RAM non è il collo: dieci sessioni GNOME ferme sono
~12 GB dei 31, dieci LXQt ~5.

### 4.6-bis 🔸 Quando il budget è pieno si rifiuta, dichiarando il motivo

Non si fa degradare chi sta già lavorando per far entrare chi arriva. Sarebbe la scelta
apparentemente gentile, ma punisce in silenzio chi non ha fatto niente — ed è precisamente ciò
che I1 vieta: una discesa che non nasce da una misura della linea, ma da una decisione presa
altrove e mai dichiarata.

Il rifiuto dice **perché**: «questa macchina non ha più capacità di codifica». Non «riprova più
tardi» e basta.

### 4.6-ter 🔸 ⛔ La GPU si sceglie con una regola udev, e ha un prezzo da sapere prima

*Sul ferro dell'utente REMOTIX usa **l'Intel**; la Radeon RX 6800 è riservata all'inferenza.*

Il meccanismo esiste già: `fondamenta/banco/gpu-udev.sh`, e la sua intestazione spiega perché non ce ne
sono di più semplici:

- **KWin prende la prima scheda che riesce ad aprire** e non guarda nessuna variabile
  (`KWIN_DRM_DEVICES` vale solo per il backend `drm`). L'unico modo di sceglierne una è rendere
  l'altra **non apribile**;
- ⛔ **e la via ovvia è una trappola**: `InaccessiblePaths=` nell'unità del compositore dà la
  scheda giusta e **chiude il cancello della cattura** — 0 righe di registro sui permessi contro
  13 (`STUDI.md` §kde §3.3-bis). Si passa dai permessi del **nodo**;
- ⚠ **per id PCI, non per numero di nodo**: `renderD128` e `renderD129` si scambiano fra un
  avvio e l'altro, l'indirizzo PCI no.

⚠⚠ **Il prezzo, che lo script dichiarava già prima che l'inferenza esistesse**: negare il nodo
coi permessi lo nega a **tutta la sessione dell'utente**, non solo al compositore. Sul ferro
attuale questo significa che **l'utente che fa inferenza va messo nel gruppo** della regola, e
gli utenti delle sessioni remote no. Funziona — ma se un giorno l'inferenza smettesse di vedere
la Radeon, la causa è questo file, e nessuno la collegherebbe da solo.

⭐ E l'avvertenza di `LEZIONI.md` §4 trappola 6 — *«il compositore deve disegnare sulla scheda
giusta; un buffer di un'altra scheda non è importabile, e il sintomo è composizione in software
senza un errore»* — su una macchina a **due** GPU smette di essere teorica.

> ### ⭐ Su Mutter il meccanismo è un altro, e per ora gioca a favore — `[M]` 9 agosto 2026
>
> Questa voce è scritta su KWin, che *«prende la prima scheda che riesce ad aprire»*. Mutter no:
> alla fase 0, con tutt'e due i nodi visibili, ha dichiarato da sé
>
> > `Added device '/dev/dri/renderD129' (amdgpu)` · `Added device '/dev/dri/renderD128' (i915)` ·
> > **`Boot VGA GPU /dev/dri/renderD128 selected as primary`**
>
> — cioè ha scelto **l'Intel**, che è quella che vogliamo, con un criterio suo (*Boot VGA*) e
> senza che nessuno gliel'abbia chiesto. **Sul ferro attuale la regola udev non serve a GNOME.**
>
> ⛔ **Ma non si conclude che non serva.** È di nuovo una condizione che ci salva senza che
> l'abbiamo chiesta (§4.3-bis): dipende da quale scheda è la *Boot VGA* del BIOS, che è fuori dal
> nostro controllo e cambia spostando un cavo. La regola udev resta la **leva dichiarata**; questa
> misura dice solo che oggi, su GNOME, non è lei a decidere.
>
> ⚠ E una riga da capire, non ancora capita: `amdgpu_cs_ctx_create2 failed. (-13)` — la Radeon è
> vista e **non apribile** (permesso negato). `[?]` Se sia già la regola udev di questo file o
> altro, non è stato accertato. Non ostacola: il primario è quello giusto.

### 4.6-quinquies ✅ ⛔ **Si misura sulla GPU INTEGRATA**, non sulla discreta

*Vincolo posto dall'utente il **15 agosto 2026**, guardando la registrazione dell'Aquarium a 60 fps:
«i test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco. La solidità del sistema la
si vede su GPU poco potenti, non mostri come la RX 6800».*

⭐ **È una regola di metodo, e vale più della misura che l'ha provocata**: un numero preso sul ferro
migliore non dice se il prodotto regge — dice quanto è veloce quel ferro. `LEZIONI.md` è pieno di
misure che sembravano un risultato e erano una proprietà del banco.

`[M]` **La macchina di prova ha due schede**, e fino a stasera **sceglieva il compositore**:

| | indirizzo PCI | nodo | chi è |
|---|---|---|---|
| ✅ **si usa questa** | `0000:00:02.0` | `renderD128` | **Intel UHD 730** (`i915`), l'integrata |
| ❌ esclusa | `0000:03:00.0` | `renderD129` | Radeon **RX 6800** (`amdgpu`) |

⛔ **E non era una scelta: era un accidente.** Senza la regola udev di §4.6-ter — `[M]` non era
installata, `/etc/udev/rules.d` era vuota — i gruppi `video`/`render` danno accesso a **tutte e
due**, e `[M]` il compositore aveva preso la **Radeon**. ⇒ La misura dell'Aquarium delle 22:09 —
60 fps inchiodati — è stata fatta **sulla scheda sbagliata**, e va rifatta.

**La cura è quella già decisa in §4.6-ter, finalmente applicata**: `fondamenta/banco/gpu-udev.sh` con
l'indirizzo da **escludere**, che sposta il nodo in un gruppo senza membri. ⭐ `[M]` dopo il
riavvio del gestore d'utente e della sessione, `gnome-shell` apre **6 descrittori su `renderD128`**:
l'integrata, e solo quella.

⚠ **E il prezzo resta quello che §4.6-ter dichiara**: negare il nodo lo nega a **tutta la sessione
dell'utente**, non solo al compositore. Chi un giorno volesse la Radeon per altro — un
transcodificatore, un gioco — la troverebbe chiusa, e nessuno collegherebbe la cosa a questo file.

⏳ **E la fase 8 eredita una domanda in più**: la codifica hardware sceglie la sua scheda per conto
proprio (VA-API). ⛔ Se il compositore disegna sull'integrata e il codificatore cerca la discreta —
che qui è chiusa — il ripiego è in CPU, ed è il caso che `LEZIONI.md` §1.8 dice di **dichiarare**
invece di subire.

### 4.6-quater ✅ ⭐ Il confine del multi-tenant: la fase 5 regge **un utente per volta**, la fase del multi-tenant la macchina piena

> ⚠ **Il numero di quella fase è cambiato il 16 agosto 2026 — era la 12, adesso è la 10** — e il
> **confine qui deciso è intatto**: vedi **§4.6-sexies**. Il titolo diceva *«la 12 la macchina
> piena»*, e adesso dice la cosa senza il numero, che era la parte fragile.

*Chiesto dall'utente il **15 agosto 2026** all'apertura della fase 5 — «poiché qui trattiamo le
sessioni, mi chiedo se il multi-tenant non ricada in questa fase» — e deciso da lui lo stesso
giorno: «potremmo anche lasciare in questa fase 1 solo utente, e nella fase 12 il multi-tenant».*

⚠ **La domanda era buona perché i due documenti dicevano cose diverse**: `SPECIFICHE.md` §5.5 dice
*«il multi-tenant è delle fasi da 5 in poi»*, `PIANO.md` intitolava la **fase 12** «Multi-tenant e il
budget». Il confine, deciso:

| | dove | perché lì |
|---|---|---|
| **il multi-tenant come funzione** — più sessioni remote insieme, il **budget** del codificatore, `BUDGET_PIENO 0x06`, il rifiuto che non fa peggiorare chi sta già lavorando, `MAX_ATTACCATE` che smette di essere un `#define` | **fase 10** | ⭐ hanno bisogno di **un numero vero**, e il numero vero lo dà il codificatore hardware della **fase 8**. Misurarle prima vuol dire misurarle due volte (`LEZIONI.md` §7.2) |
| **un utente remoto per volta** | **fase 5** | è la scena che la fase promette, ed è già abbastanza carica: il logout col suo codice nuovo, le tre cinture di §4.7, il guardiano di logind, i tre orologi, il rilascio dei tasti, l'inibizione della sospensione, l'headless dichiarato |
| ⛔ **il codice chiavato sull'utente**, e il guardiano di logind che **discrimina per utente** | ⭐ **fase 5, e non è rinviabile** — vedi il riquadro | ⛔ non perché sia importante: perché **non si può scrivere «per un utente solo»** |

> ### ⛔⭐ Il pezzo che non si può rinviare, e la ragione è che la macchina lo smaschera da sola
>
> Il guardiano di logind che deve emettere `0x04` e `0x05` (`SPECIFICHE.md` §5.1) risponde a una
> domanda che suona in **due modi diversissimi**:
>
> > *«c'è una sessione grafica locale?»* — oppure — *«c'è una sessione grafica locale **di questo
> > utente**?»*
>
> ⛔ **Una riga di differenza nel codice, due prodotti diversi.** E la macchina di prova è **già**
> nella configurazione che smaschera l'errore: `nicfio` ha la sua sessione grafica **locale**,
> `prova` si collega da **remoto**. Scritto nel modo sbagliato, `prova` viene rifiutato con `0x05`
> — *«c'è già una sessione grafica locale»* — **il primo giorno, alla prima prova**, perché la
> sessione locale c'è davvero: è solo di un altro.
>
> ⭐ **Non serve inventare uno scenario multi-utente: è lo stato normale della macchina.** ⇒ Il banco
> di `0x04`/`0x05` si scrive su quella coppia — locale `nicfio` e remota `prova`, che **devono
> convivere senza toccarsi** — e costa quanto costerebbe comunque.

⚠ ~~**E quel che resta ripiego resta dichiarato**: `MAX_ATTACCATE` è un `#define` a **16**, e
`MAX_FIGLI` a 16, che dichiara di seguirlo — dove `SPECIFICHE.md` §5.5 promette **dieci
configurabile**. Oggi non morde — 16 > 10 — e la sua scadenza è la fase 10.~~
> ✅ **PAGATO il 25 agosto 2026, sera — fase 10** *(riallineato al codice il 28 agosto)*. Il numero
> adesso è **uno solo**: `RCP_TETTO_SESSIONI` in `src/rcp.h`, vale **10**, e si cambia con
> **`--tetto-sessioni N`**. Il `#define` è il predefinito; il valore in vigore lo dice `rcp_tetto()`.
> ⭐ E le quattro tabelle (`MAX_ATTACCATE`, `MAX_FIGLI`, `QUANTI_PRESENTI`, `WT_PALCHI`) ora si
> **allocano** su quel numero invece di essere quattro copie a mano che divergono in silenzio —
> il difetto che `src/rcp.h` racconta per esteso, e che `[M]` §6.4 aveva provato sul campo.
⚠ *Il riferimento diceva `rcp.c` · `MAX_ACCUMULO`, e il `#define` sta a **568**: corretto il 16 agosto 2026
rileggendo il file. ⛔ Un numero di riga invecchia in silenzio — è il motivo per cui accanto c'è
anche il nome della costante.*

### 4.6-sexies ✅ ⭐⭐ L'ordine cambia: il multi-tenant **prima** dei desktop nuovi

*Deciso dall'utente il **16 agosto 2026**, rivedendo il piano prima di aprire la fase 6: «PRIMA si
chiude lo sviluppo anche con il multi-tenant, e solo dopo si pensa agli altri DE».*

⛔ **Il confine di §4.6-quater NON cambia**: «un utente per volta» resta della fase 5, «la macchina
piena» resta della fase del multi-tenant, e il codice chiavato sull'utente resta non rinviabile.
⭐ **Cambia solo dove quella fase sta nella fila** — e con lei il suo numero:

| | prima | ⭐ adesso |
|---|---|---|
| Multi-tenant e il budget | fase **12** | **fase 10** |
| KDE | fase 10 | **fase 11** |
| XFCE e LXQt | fase 11 | **fase 12** |
| La qualità e la degradazione | fase 9 | **fase 9**, invariata — e adesso ha un secondo cliente: la scala di degradazione è **il modo** in cui più sessioni stanno sulla stessa macchina |
| Il servizio | fase 13 | **fase 13**, invariata — ⛔ e resta ultima **per una ragione**: §7.16 le fa **togliere dal binario** le marche di banco `BANCO_MARCA`/`BANCO_ESITO`, che le fasi dei desktop useranno per misurarsi. Metterla prima vorrebbe dire togliere il metro e poi provare tre desktop nuovi senza |

⭐ **La ragione è quella di §4.6-quater, applicata dall'altro capo.** Là si diceva: *«misurare il
budget prima del codificatore hardware vuol dire misurarlo due volte»* (`LEZIONI.md` §7.2). Qui:
⛔ **il budget è un budget di GPU, e la GPU è una** — `renderD128`, la stessa iGPU che compone
**ogni** desktop. È una proprietà **della macchina**, non del desktop. Misurata prima, le fasi 11 e
12 la ereditano; misurata dopo tre desktop nuovi, non si sa più quale numero appartenga a che cosa.
⇒ E se il multi-tenant tocca la sessione o il budget, la modifica va riverificata **su quattro
desktop invece che su uno**.

⚠ **E quel che questa decisione NON compra, detto per intero**: l'architettura multi-tenant c'è già
in buona parte — `figlio.c` ⚠ *(il codice citato non c'e' piu': da rileggere)* dichiara *«un utente per figlio»*, un processo per sessione. ⇒ Non
si sta scansando una riscrittura strutturale; si sta evitando una misura ripetuta quattro volte.
È un argomento più debole di quel che sembra, e tira nella stessa direzione lo stesso.

⛔ **La precedenza che resta**: il multi-tenant sta **dopo la fase 8**, e la ragione è invariata —
la **copia zero** cambia quanto costa una sessione in memoria e banda di GPU, e un budget misurato
prima della copia zero è un budget da rifare.

> ### ⚠ E le parole del 15 agosto dicono «fase 12»: restano
>
> La citazione di §4.6-quater — *«nella fase 12 il multi-tenant»* — **non è stata riscritta**, né
> qui né in `FASI.md` §05-la-sessione: era il numero di allora, e correggere una frase fra virgolette
> è il modo più veloce per non sapere più che cosa è stato detto davvero.
> ⇒ **La decisione era ed è la stessa; è il posto in fila ad essere cambiato.**

### 4.6-septies ✅ ⭐⭐⭐ **Sei sessioni su una scheda integrata sono un buon risultato — la fase 10 si chiude**

*Giudizio dell'utente, **24 agosto 2026**, davanti al primo giro di misure del multi-tenant:*

> *«Tenendo conto che siamo su una scheda Intel integrata non particolarmente performante, 6 RDP
> attivi contemporaneamente non mi sembra un cattivo risultato»*

*⭐ **Riconfermato il 28 agosto 2026** — «confermo quel mio giudizio» — quando si è scoperto che
questa sezione era citata da cinque documenti e **non era mai stata scritta**.*

⇒ ⭐ **Il numero misurato è accettato così com'è**: non si apre una caccia per farlo salire, e la
fase 10 si chiude sul giudizio invece che su un bersaglio numerico. È la stessa forma della
decisione della fase 10 di v1 sulla qualità — *«va bene così»* — e vale per la stessa ragione:
⛔ **il metro è l'utente, non il numero.**

⚠ **E il giudizio è dato sul caso PEGGIORE.** Le misure stanno in
`fasi/10-multi-tenant-e-il-budget.md` §S.2 e §6.12, e non si ricopiano qui:

| scena | quante ci stanno |
|---|---|
| **satura** — tutto lo schermo cambia a ogni fotogramma | `[M]` **6** ← *il numero giudicato* |
| ⭐ **desktop vero** — finestre, trascinamenti, lavoro normale | `[M]` **almeno 11**, e il soffitto **non è stato trovato**: sono finiti gli utenti, non la macchina |

⇒ ⭐⭐ **Il giudizio ne esce rafforzato, non smentito**: quel che gli utenti fanno davvero costa meno
della scena peggiore, e undici è un limite dello strumento di misura, non della macchina.

⛔ **E il ferro va detto ogni volta** che si cita questo numero: Intel UHD 730 **integrata**, non una
scheda dedicata. Un «sei» senza il ferro accanto è un numero che qualcuno confronterà con l'hardware
sbagliato.

> ### ⚠ E questa sezione ha una storia che vale la pena tenere
>
> ⛔ È stata **citata da cinque documenti — `SPECIFICHE.md` compresa, e da `DECISIONI.md` stessa —
> per quattro giorni prima di esistere.** La numerazione saltava da `-sexies` a `-octies` e nessuno
> se n'era accorto: il giudizio era scritto in tre posti, ma **non dove le decisioni vivono**.
> ⇒ ⭐ È il difetto che `C16` adesso prende, ed è il motivo per cui quella maglia esiste.

### 4.6-octies ⏳ ✅ **Il ban per indirizzo NON si tocca in fase 10: va in un capitolo sulla sicurezza**

*Deciso dall'utente il **25 agosto 2026**, davanti al rilievo della fase 10: «il discorso del ban
rientrerà in un discorso più generale sulla sicurezza, che farà parte di un capitolo evolutivo».*

⛔ **Il rilievo resta vero e misurato, e non si chiude: si RINVIA con un nome.**
`fasi/10-multi-tenant-e-il-budget.md` §4.2 (**R10-A2**): `rcp.c` · `posto_prendi()` dichiara *«IL NOME UTENTE NON
CONTA. Tre nomi diversi contano tre»* — ed è la decisione di **§1.9**, presa quando il prodotto
serviva **un inquilino**. ⇒ Con dieci inquilini **dietro lo stesso NAT** la chiave è **una sola**:
`[M]` tre di loro che sbagliano **una volta a testa** in cinque minuti bannano l'indirizzo, e gli
altri sette — **che non hanno sbagliato niente** — restano fuori **dodici ore**. ⛔ E l'unica uscita è
il socket di comando, che è `0600` di **root**: un inquilino **non può sbloccarsi**.

> ### ⭐ Perché il rinvio è la scelta giusta, e non un accantonamento
>
> ⛔ **La cura tocca una difesa, non una comodità.** Quel che il ban difende — *«chi prova parole
> d'ordine non deve poter provare all'infinito»* — è una decisione dell'utente (§1.9), e ⭐ **una
> difesa non si smonta dentro una fase che sta misurando la capacità**: si rifà quando si guarda la
> sicurezza **per intero**, con davanti tutte le sue voci.
>
> ⚠ **E il pezzo di disegno già trovato resta scritto, per chi aprirà quel capitolo**: una chiave
> `(indirizzo, utente)` con la soglia di §1.9 per coppia, **più** una soglia più larga sul solo
> indirizzo (molti nomi diversi falliti ⇒ ban dell'indirizzo), conserva la difesa contro **l'attacco
> vero** — che prova **molti nomi** — e toglie la punizione collettiva per **l'errore di battitura**.
> ⛔ È un disegno, non una decisione: la decisione è di quel capitolo.
>
> ⭐ **E una cosa che la fase 10 ha già chiuso**, e che non va rimessa in discussione là: il difetto
> **della chiave con la porta** — quello per cui il contatore *«valeva sempre 1»* — è **curato per
> costruzione**, e la lente avversariale l'ha verificato riga alla mano (§4.3, pista 2).

⚠ **E il prezzo del rinvio, dichiarato**: fino a quel capitolo, ⛔ **un ufficio dietro un NAT è una
configurazione in cui il prodotto può chiudersi da solo per dodici ore**, e la fase 10 lo sa. ⭐ Non è
un difetto nascosto: è un difetto **misurato, nominato e datato**.

### 4.6-nonies ✅ ⭐⭐⭐⭐ **Il budget è di COMPOSIZIONE, non di codifica — e §4.6 va corretta, non integrata**

*Misurato nella fase 10, il **24 agosto 2026**, dopo l'ordine del regista: «prima si misura, e poi
simuli 10 utenti veri».*

⛔⛔ **§4.6 diceva che il limite lo pone il codificatore. La misura dice di no.**

| dove si spende | quale motore della GPU | soffitto `[M]` |
|---|---|---|
| il **codificatore** nudo, scena sintetica | i due VDBOX (`vcs0`, `vcs1`) | **1,86 Gpixel/s** in H.264 · **2,33** in HEVC |
| ⭐⭐⭐ **la COMPOSIZIONE** | ⛔ **`rcs0`**, il motore di disegno | ⭐ **0,97 Gpixel/s — la METÀ** |

⇒ ⛔ **Il collo è a monte di noi.** `[M]` A saturare `rcs0` è **`gnome-shell` al 99,5 %**, mentre
**`remotix` sta a `0,00 %`**. ⭐ *Cioè: il prodotto non è lento — il prodotto sta aspettando il
compositore*, e nessuna ottimizzazione del codificatore sposta quel numero.

> ### ⭐⭐ La prova che lo inchioda sta in una riga sola
>
> `[M]` Stessa popolazione — **otto sessioni, otto desktop, otto figli** — e si **spegne una sola
> scena**. **Il ritmo torna da 1,6 a 33,4 fot/s.** La si rimette, e il dirupo si riproduce.
> ⭐ **Reversibile e ripetibile.**
>
> ⇒ ⛔⛔ **Il dirupo non cade sul NUMERO delle sessioni: cade su quanto si sta COMPONENDO** — `[M]`
> fra **873 e 953 Mpixel/s**, che è **lo stesso soffitto trovato per un'altra strada**.
>
> ⚠ **E la colonna che lo tradiva non la guardava nessuno**: quando i compositori prendono il 100 %
> del motore di disegno, `video-enhance` **crolla da 48,7 % a 0,4 %** ⇒ ⛔ **il codificatore non ha
> più niente da fare. Non rallenta: si ferma.**

#### ⭐ Che cosa cambia nel prodotto, in concreto

⭐⭐ **Il budget resta calcolabile PRIMA di accettare** — ed è la ragione per cui la decisione di §4.6
regge anche se la sua fisica era sbagliata: ⭐ **la moneta è il pixel COMPOSTO**, e il costo di una
sessione si conosce dalla sua tela prima che la sessione esista.

⛔ **Ma il pixel da solo non basta**, e questo la fase l'ha imparato misurando: si guarda **anche il
ritardo di chi è già dentro** — `[M]` soglia **22,9 ms**, ricavata da sano **≤ 13,1** e rotto
**≥ 39,9**, ⭐ **senza nessuna sovrapposizione fra le due popolazioni**.

```
regge(dentro, nuovo)  ⟺  domanda(dentro) + costo(nuovo)  ≤  C × tolleranza
                          E  il ritardo di chi è dentro sta sotto la soglia
```

#### ⚠ E i numeri di §4.6 che erano sbagliati — tutt'e tre **per difetto**

| 10 sessioni a… | §4.6 diceva | ⭐ `[M]` |
|---|---|---|
| 480p · 25 | «una cinquantina» | il soffitto sta a **~180** — e la scala si è fermata al **tetto del banco**, non a quello del ferro |
| 1080p · 30 | «giusto al limite» | il numero (620 Mpixel/s) era **giusto**, ⛔ ma è il **33,2 %**: ne tengono **24** |
| 4K · 60 | «**una sola** sessione» | ⛔ i 5 Gpixel/s **non esistono**: il soffitto è 1,86. Ne tengono **DUE** |

⛔ **Ma sono numeri del motore che NON è il collo**, e vanno letti solo per quello che sono: la
capacità del codificatore. ⭐ **Il numero che governa il prodotto è quello della composizione.**

⇒ ⭐ **E per l'utente il numero vero è un altro ancora**: sulla scena satura ne stanno **sei**; sul
**desktop vero** — finestre, trascinamenti, strappi — `[M]` **almeno undici, e il soffitto non è
stato trovato: sono finiti gli utenti, non la macchina**. Il giudizio è in **§4.6-septies**.

### 4.6-decies ✅ ⭐⭐⭐⭐ **Il metro sotto le specifiche: «artefatti sì, fluidità e sincronismo no»**

*Detto dall'utente il **25 agosto 2026**, davanti al prodotto vero — un video **4K** dentro il
desktop remoto, con la banda del suo tablet strozzata a **10 Mbit/s**, cioè **sotto il pavimento
dichiarato** di 30:*

> *«Il video mostra degli artefatti, ma è normale: siamo sotto le specifiche. Però **audio e video
> fluidi e in sync**.»*

⭐⭐ **È una decisione, non un complimento: dice che cosa si può spendere quando non c'è abbastanza.**

| ⭐ **si può perdere** | ⛔ **non si può perdere** |
|---|---|
| **la nitidezza** — artefatti di compressione visibili | ⛔ **la FLUIDITÀ**: il movimento a scatti si nota subito, e stanca |
| il dettaglio nelle scene veloci | ⛔ **il SINCRONISMO** fra audio e video: sfasati, diventano insopportabili in pochi secondi |

⇒ ⭐ **Sotto il pavimento il prodotto spende il poco che ha dove l'utente se ne accorge di meno**, e
lo fa **in questo ordine**. ⛔ *Non è indulgenza: è il metro.* Il prodotto non ha mai promesso il 4K
a 10 Mbit/s — ha promesso di **non mentire e non sbriciolarsi** (`SPECIFICHE.md` §2, *«degradare, non
fallire»*), e sotto le specifiche quella promessa si onora **così**.

> ### ⭐⭐ E la prova se l'è disegnata lui — con la correzione giusta, due volte
>
> 1. Alla proposta di scendere a **30 Mbit/s** gli è stato messo davanti il numero — `[M]` quel
>    video viaggiava a **6,0 Mbit/s**, cioè trenta sono **cinque volte** quel che serve — e ⭐ **ha
>    sceso a 10**;
> 2. ⭐⭐ e ha strozzato **il tablet**, non il server: cioè **il percorso vero**, dal lato del client
>    — che è la scena che un utente vero produce, e non quella comoda da fabbricare.
>
> `[M]` **E il prodotto ha risposto dimezzando la banda senza perdere un fotogramma**: 38,5 → **37,4
> fot/s**, 6,0 → **3,20 Mbit/s**, ⭐ con la **coda del filo vuota** e il motore di composizione
> **fermo sullo stesso 41-46 %** — cioè la scena si muoveva come prima.
> ⇒ **Non ha rallentato: ha compresso di più.**

⚠ **E questo giudizio chiude un `[?]` della fase 9**: la metà **AV** del sincronismo, rimasta aperta
perché *«vuole quel browser»* — ⛔ e quel browser non partiva per una ragione che non era la sua
(§4.6-undecies).

### 4.6-undecies ✅ ⛔⛔ **Il difetto di un inquilino solo che ne blocca nove — e la causa NON è un guasto**

*Trovato il **25 agosto 2026**, dopo che l'utente aveva detto tre volte «Firefox non funziona».*

> #### ⭐⭐⭐ CORREZIONE DELL'UTENTE — *25 agosto 2026, sera*
>
> ⚠ *Il titolo di questa sezione diceva `**Il difetto di un inquilino solo che ne blocca nove:
> `~/.cache -> /tmp`**`, e il testo qui sotto chiamava quel collegamento **il difetto**. ⛔ È
> sbagliato, e l'ha corretto l'utente:*
>
> > *«`.cache` che punta a `/tmp` è una mia scelta voluta»* — *ed è una decisione su come deve
> > funzionare **il sistema operativo della sua macchina**, che **non c'entra niente con REMOTIX**.*
>
> ⇒ ⛔ **Non c'è niente da riparare nel sistema.** Quel collegamento non è un guasto ereditato da
> un'immagine base: è una configurazione **scelta**, e su una macchina a un utente solo non fa
> nessun danno.
>
> ⭐⭐ **E quel che resta vero è NOSTRO, non suo**: è **il prodotto** che crea dieci utenti nuovi
> con `useradd -m`, ed è il prodotto che li fa nascere tutti a scrivere **nello stesso posto**.
> ⇒ ⛔ *Una scelta innocua su un utente diventa un blocco su dieci **perché ce li mettiamo noi**.*
>
> ⭐ **La cura già scritta è giusta così com'è, e va detto perché**: `src/provisiona.sh` **non
> tocca `/etc/skel`, non tocca la home dell'utente, non tocca `/tmp/mozilla`** — dà una `.cache`
> propria **soltanto agli utenti che creiamo noi**. ⇒ Il sistema resta come l'utente lo vuole, e
> i nostri inquilini smettono di pestarsi i piedi.
>
> ⛔ **E il bersaglio della fase 11 cambia di conseguenza** (§4.6-duodecies): la rete **non**
> controlla che le cartelle siano al posto canonico — non è affar suo, e l'utente ha deciso
> diversamente **apposta**. Controlla che **il prodotto funzioni sulla macchina com'è
> configurata**: *il secondo utente apre il browser, sì o no?*

`/etc/skel/.cache` è un **collegamento a `/tmp`**, e `src/provisiona.sh` crea gli utenti con
`useradd -m`, che **copia lo scheletro**. Firefox tiene il profilo *locale* sotto
`$HOME/.cache/mozilla` = **`/tmp/mozilla`** ⇒ ⛔ **il PRIMO utente che apre il browser se la prende a
modo `0700`, e per tutti gli altri il profilo non nasce.**

⭐⭐ **E la decisione che ne discende, che vale oltre questo caso**: ⛔ **una macchina multi-tenant non
eredita solo i difetti di quella a un utente: ne SVEGLIA di dormienti.** ⇒ Quel che è *«raro»* con un
inquilino può essere ***certo*** con dieci, e va cercato **prima**, non aspettato.

⚠ **La cura sta in `src/provisiona.sh`** — cioè **nella macchina, non nel prodotto**
(`SPECIFICHE.md` §5.9, parte A) — e ⛔ **il predicato che la verifica non guarda il collegamento:
PROVA A SCRIVERE**, perché *«scritto non è in vigore»* (**E1**).

⛔ **E il costo, dichiarato**: quel difetto ha tenuto l'utente **due fasi** davanti a un browser che
non partiva, con la spiegazione *«non è nostro»* — ⇒ ⭐ **la spiegazione che non chiede di continuare
a cercare.** La lezione di metodo è `LEZIONI.md` **§1.38**.

### 4.6-duodecies ✅ ⭐⭐⭐⭐⭐ **Prima dei desktop nuovi: una fase per NON introdurre regressioni**

*Deciso dall'utente il **25 agosto 2026**, subito dopo aver chiuso la fase 10:*

> *«No, prima è necessario mettere in sicurezza tutto quello che abbiamo sviluppato fino a oggi.
> Prima di passare agli altri DE è necessaria una sessione dedicata (magari una fase vera e propria)
> per studiare una modalità che impedisca di introdurre regressioni man mano che verrà implementato
> il supporto ai nuovi DE.»*

⭐ **La fase 11 non è più KDE: è la rete di sicurezza.** KDE, XFCE e LXQt scalano di uno.

#### ⛔ Perché adesso, e non dopo — e l'argomento non è prudenza generica

`[M]` **La giornata del 25 agosto lo ha dimostrato tre volte**, e ogni volta con lo stesso modo di
sbagliare:

| il difetto | quanto è rimasto nascosto | ⛔ perché |
|---|---|---|
| **la sessione che nasce cieca** (§7.4) | giorni | ⛔ **nessuno ha mai aperto una sessione NUOVA e l'ha guardata**: tutte le prove riusavano sessioni già aperte, che il monitor ce l'avevano |
| **il browser che non parte al secondo utente** (⚠ *non* il collegamento `~/.cache`, che è una **scelta** dell'utente — §4.6-undecies) | **due fasi** | ⛔ e la prova che *«chiudeva la questione»* girava da un utente che **aveva la stessa configurazione** |
| **cinque banchi che contavano zero fotogrammi** | un giro | ⛔ una cura al registro aveva rotto le loro espressioni, e `resa()` tornava **0 invece di None** |

⇒ ⭐⭐ **Nessuno dei tre era sottile.** Tutti e tre erano invisibili per la **stessa** ragione: si
guardava sempre lo stesso pezzo di scena, e ⛔ **si guardava il processo invece del pixel.**

#### ⛔⛔ E la ragione per cui va fatto PRIMA dei desktop, che è la stessa di §4.6-sexies

> *«se il multi-tenant tocca la sessione o il budget, la modifica va riverificata su **quattro
> desktop invece che su uno**»*

⇒ ⭐ **Vale identica per il modo di sbagliare**: un difetto che oggi si trova una volta, con quattro
desktop si troverà **quattro volte** — e nel caso peggiore su tre di essi **non si troverà affatto**,
perché nessuno pensa a riprovare il primo. ⛔ *La rete si tende prima di camminare sul filo, non
dopo.*

#### ⭐ Il metro della fase, e non è «quante prove girano»

⛔ **Una fase così può degenerare in cerimonia**, e il progetto lo sa (`LEZIONI.md`, la revisione si
giustifica su **che cosa sopravvive**). ⇒ ⭐⭐ **Il metro è uno solo: che cosa la rete PRENDE.**

⭐⭐ **E il collaudo della fase è già scritto oggi**: la rete va puntata contro **il codice di
stamattina**, e ⛔ **deve diventare rossa su §7.4** — la sessione cieca — **senza che nessuno le
abbia detto dove guardare.** Se non lo prende, non è una rete: è un rituale.

⚠ **E il secondo collaudo**: deve accorgersi che **al secondo utente il browser non si apre**.
⛔ **Non** «deve trovare il collegamento `~/.cache`» — quello è una **scelta dell'utente**, non un
guasto (§4.6-undecies, correzione del 25 agosto 2026): la rete non giudica come è configurata la
macchina. ⇒ ⭐ **Guarda la CONSEGNA sulla macchina com'è**, non il sorgente e non la configurazione.

### 4.6-terdecies ✅ ⭐⭐ **Una scatola di prova può avere fino a DIECI inquilini** — il vincolo era sulla capienza, non sulla correttezza

*Chiarito dall'utente il **26 agosto 2026**, dopo la notte del passo 0:*

> *«Per quanto mi riguarda un container può anche avere 10 utenti, è un dato già misurato con
> GNOME.»*

⛔ **Corregge una lettura troppo stretta di §4.6-duodecies**, che questa sessione aveva riassunto in
*«un utente per contenitore»*. ⇒ Quel vincolo nasceva da una cosa vera — **la capienza è già stata
misurata**, sul caso peggiore, e non si rifà a ogni modifica — ⛔ **ma era stato applicato a una
domanda diversa.**

| tipo di prova | la domanda | si rifà? |
|---|---|---|
| **capienza** | *quanti inquilini ci stanno insieme prima che la macchina ceda?* | ⛔ **no**: `[M]` sei sulla scena satura, almeno undici sul desktop vero |
| ⭐ **correttezza a più inquilini** | *il secondo riesce a fare quel che deve?* | ✅ **sì, ed è la rete** |

⭐⭐ **E il rilievo era dei due revisori esterni**, che ci sono arrivati per due strade diverse: *«C8
è la prova più importante ed è la più fragile»*. ⇒ Con questo chiarimento la prova del **secondo
utente che apre il browser** — cioè il **collaudo B** della fase 11 — ⭐ **può stare dentro una
scatola**, invece di essere l'unica cosa che vive sulla macchina vera e che quindi si esegue di rado.

⚠ **E quel che questo NON autorizza**: rifare la campagna dei dieci a ogni modifica. Dieci inquilini
*possono* stare in una scatola; ⛔ la rete anti-regressione ne usa **due**, perché la domanda è *«si è
rotto qualcosa?»* e non *«quanti ce ne stanno?»*.

### 4.6-quaterdecies ✅ ⭐⭐⭐ **Le quattro scatole esistono — e sono quattro scatole con TRE compositori**

*`[M]` **26 agosto 2026**, notte. Costruite e verificate le scatole di GNOME, KDE, XFCE e LXQt: ⭐ il
passo 0 dà **18 verdi su 18 in tutte e quattro**, con la stessa identica lista di prove e ⛔ **nessuna
riga cambiata**. Ogni scatola porta allo stesso percorso un **adattatore** di quaranta righe.*

⚠ **E una cosa scomoda, detta subito**: XFCE e LXQt non portano un compositore proprio su Wayland —
portano una **sessione** e si appoggiano a uno di famiglia `wlroots`. Per tutt'e due la scelta è
**labwc**, ⭐ che questo documento aveva già misurato sotto l'etichetta *«labwc (XFCE, LXQt)»*.

⇒ ⛔ **La quarta scatola non mette alla prova un quarto compositore**: mette alla prova una quarta
sessione, una quarta ricetta e dipendenze diverse. **Chi legge i risultati conti tre compositori e
quattro scatole.**

#### ⭐ E il terzo desktop non ha chiesto niente — *che è un risultato, non un non-evento*

Il secondo aveva chiesto **due** cose che il primo non chiedeva (il gruppo `render`, il permesso
`SYS_NICE`). Il terzo e il quarto: **zero**. ⚠ Va letto per quel che è: **un** desktop che non ha
chiesto niente dopo **uno** che aveva chiesto due cose — cioè la ragione per cui la domanda si fa a
ciascuno invece di generalizzare dal primo.

#### ⛔⛔ E per la TERZA volta l'ambiente era generoso: `libpci3`

`[M]` Firefox senza `libpci3` dice `glxtest: libpci missing` e **non produce nessuna immagine**. ⛔ Nella
scatola di XFCE il difetto **non si vedeva**: `labwc` se lo tira dietro; `kwin-wayland` no.
⇒ ⭐ **Lo stesso identico modo di sbagliare di `libei1`**: una libreria che c'era **per caso**, e un
rosso che sembrava del prodotto. ⇒ Adesso è dichiarata nella ricetta, come le altre.

### 4.6-quindecies ✅ ⭐⭐⭐ **C8 si è dovuta spezzare in due — e la metà che regge ha preso il difetto**

*`[M]` **26 agosto 2026**. Il collaudo B della fase 11 è passato:*

> **con la cura della provvista**: `c8u1` ⭐ la pagina copre il **98,7 %** · `c8u2` ⭐ **98,7 %**
> **senza la cura** (il codice del 25 agosto): `c8u1` ⭐ **98,7 %** · ⛔ `c8u2` **NO** — *profilo: è di
> «c8u1» · sa scrivere in `~/.cache/mozilla`: **NO***

⭐⭐ **E l'asimmetria è quella giusta**: il primo apre il browser, il secondo no. ⛔ Un rosso su tutt'e
due non sarebbe stato il difetto di §4.6-undecies — sarebbe stato il banco.

| | che cosa guarda | oggi |
|---|---|---|
| ⭐ **C8a** | Firefox si fotografa da sé, da utente, sulla macchina com'è configurata. Il giudizio resta **nel pixel** (`#FF00FF`, tolleranza dichiarata) | ✅ **si misura** |
| **C8b** | la stessa pagina, guardata **attraverso il prodotto** | ⚠ **oggi non si misura** |

⛔⛔ **Perché C8b non si misura**: `[M]` **dieci sessioni GNOME nuove su dieci nascono senza monitor** —
è il difetto **aperto** della fase 10 §7.4, che sta **a monte** di C8. ⇒ ⭐ Un desktop nero non
testimonia sul browser.

⭐ **E la spaccatura ha un guadagno non previsto**: C8a **non passa dal prodotto**, e quindi gira in
**qualunque** scatola — il collaudo qui sopra è girato dentro quella di **PLASMA**.

### 4.6-sexdecies ⛔⛔⛔ **E questo è il fatto che l'utente deve pesare prima della fase 12**

`[M]` 26 agosto 2026: **zero sessioni nuove su dieci** nascono con un monitor. ⇒ ⛔ **C2, C3, C4, C6 e
la metà B di C8 non possono misurare niente**: non c'è nessun pixel da guardare.

| ⭐ quel che la rete **oggi** sa fare | ⛔ quel che **non** sa fare |
|---|---|
| dire che una sessione **nasce cieca** (C1) · che il **secondo inquilino** non apre il browser (C8a) · che l'**ambiente** regge su quattro desktop | dire *«e adesso si VEDE»* |

⚠ **E la differenza conta**: non è un buco della rete — un buco si tura scrivendo un'altra maglia —
⛔ **è un difetto del prodotto**, e si tura curando il prodotto. ⇒ La ragione per cui la fase 11 sta
**prima** dei desktop nuovi è *«non rompere quel che funzionava»*: con le sessioni cieche non si
riesce a **vedere** se GNOME continua a funzionare.

⇒ ❓ **La scelta è dell'utente**, e sta scritta in `fasi/11-la-rete-di-sicurezza.md` §11.

### 4.6-septendecies ✅ ⭐⭐⭐ **Le quattro scatole non si disturbano — misurato, non più affermato**

*`[M]` **26 agosto 2026**.* La stessa prova fatta girare **una scatola per volta** e poi **tutte e
quattro insieme** dà **lo stesso identico esito**, in tutt'e due i modi (con la cura `2 sì · 0 no`;
col guasto innestato `1 sì · 1 no`).

⇒ ⭐ **Si chiude la riga che `11-accendi.sh` portava aperta**: `--network=host` fa condividere alle
quattro scatole le porte della macchina, e la separazione **per porta** è una separazione **vera** —
ciascuna riconosce come propria solo la sua.

⚠ **Il tempo è informazione, non verdetto**: `[M]` 6,6 s da sola → 7,0 s in parallelo (×1,06), e il
totale scende da 26,2 s a 7,0 s. ⛔ E un tempo è stato **buttato dal banco stesso**: col guasto
innestato i quattro tempi erano uguali a un decimo di secondo, perché quasi tutto era **attesa fissa
nostra** e non lavoro. ⇒ Chiamarla «contesa» sarebbe stato misurare il proprio tetto.

⛔ **E che cosa NON è misurato**: la contesa vera sulla **scheda grafica**. Vorrebbe quattro sessioni
vive, e le sessioni oggi nascono cieche. ⇒ È misurato lo strato di sotto — le quattro scatole
**aprono il codificatore nello stesso istante**, 3 profili H.264 ciascuna.

### 4.6-octodecies ✅ ⭐⭐ **Il gancio esiste — e il tetto dei 3 minuti è pieno**

*`[M]` **26 agosto 2026**.* La rete adesso parte da sé: si guarda **quali file sono cambiati** e da
quelli discende che cosa gira. ⛔ Non si chiede a chi lavora — *un gancio che chiede è un gancio che
il giorno in cui si ha fretta non gira, e i giorni in cui si ha fretta sono quelli in cui si rompono
le cose.*

> ### ⛔⛔ E IL TETTO È PIENO, CON SEI SECONDI DI MARGINE
>
> `[M]` La famiglia veloce — **C11 + due giri di C1** — è durata **174 secondi** su un tetto di
> **180**. ⇒ ⭐ **Non c'è spazio per aggiungere niente.** Qualunque maglia in più va **scambiata** con
> qualcosa che esce, non sommata.

⇒ Le prove **tagliate**, e il costo di ciascuna, stanno in `fasi/11-la-rete-di-sicurezza.md` §7-bis.16.
⛔ La più cara: **C8 non viene guardata a ogni modifica** — la maglia più importante della lista sta
solo nel giro completo.

⚠ **E si aggancia PRIMA DI MANDARE**, non a ogni salvataggio: tre minuti a ogni commit sono
esattamente la cosa che fa spegnere un gancio.

### 4.6-undevicesimo ✅ ⭐⭐⭐ **La rete sa dire di sé stessa se è ancora capace di dare rosso**

*`[M]` **26 agosto 2026**, giro completo, 28 minuti.*

⛔ Il guasto che questa maglia (C13) cerca è il più insidioso della lista: *una rete che non è più
capace di dare rosso **ha esattamente l'aspetto di una rete che non trova niente**.*

⇒ ⭐ E il momento che conta è successo davvero. **Durante** il giro C13 era **rossa**, e diceva il
vero: *«negli ultimi giri nessun guasto è mai stato innestato»*. **Dopo** il giro — che il guasto
innestato ce l'aveva dentro — è **verde**: *«un guasto è stato innestato ed è stato visto»*.

⚠ **E lo dice col suo limite attaccato**: *sui guasti che CONOSCE*. ⛔ Ogni desktop nuovo dovrà
entrare con **un guasto suo**, o questa maglia certificherà una capacità che non copre il terreno
nuovo.

### 4.6-novemdecies ⛔⛔ **Le due metà del gancio vivono in due macchine diverse**

`[M]` 26 agosto 2026, primo giro vero, e non l'aveva previsto nessuno:

| | dove sta |
|---|---|
| **decidere** che cosa far girare | vuole il deposito git ⇒ **il portatile** |
| **far girare** | vuole le scatole e la scheda grafica ⇒ **la macchina di prova**, ⛔ dove il deposito **non c'è** |

⇒ La prima stesura pretendeva git sempre, e usciva «terreno cattivo» **sull'unica macchina in grado
di eseguire le maglie**. ⭐ Adesso: se la famiglia è chiesta per nome non c'è niente da decidere, e il
deposito non serve.

⚠ **E ne discende una cosa che va decisa dall'utente**: il registro del gancio — quello su cui vive
la memoria di C13 — **nasce dove il gancio gira**. ⇒ Oggi ce n'è uno sulla macchina di prova e
nessuno sul portatile. Metterlo in git gli darebbe una memoria sola per tutte le macchine; tenerlo
fuori eviterebbe di avere quel file modificato a ogni giro. ⛔ **Non deciso.**

### 4.6-vicies ✅ ⭐⭐⭐ **Quattro maglie nuove, e la rete adesso guarda anche quel che non è un pixel**

`[M]` 26 agosto 2026, quattro agenti in parallelo, una scatola per ciascuno.

| maglia | che cosa guarda | certificazione | costo |
|---|---|---|---|
| **C5** il suono non è silenzio | l'**RMS** dei campioni che arrivano al cliente, soglia dichiarata **328/32767** (−40 dBFS), tarata attraversando il confine nei due versi | **12 su 12** | `[M]` 38 s |
| **C7** si chiude e non resta niente | impronta prima / sessione / chiusura / impronta dopo — processi, socket, unità, scheda | **13 su 13** | `[M]` 26 s |
| **C9** il registro dice di chi parla | **due** inquilini vivi insieme, e ogni riga obbligata deve dire quale | **16 su 16** | `[M]` 50 s |
| **C10** le copie gemelle | i tre file gemelli, byte per byte — ⭐ e l'elenco **letto da `src/Makefile`**, non ricopiato | **15 su 15** | `[M]` 0,04 s |

⭐⭐ **E la scelta che le tiene insieme**: nessuna delle quattro giudica un **pixel**. ⇒ Sono le
quattro che il difetto delle sessioni cieche **non blocca**, ed è per questo che sono state fatte
adesso e non le altre.

⚠ **Nessuna entra nella famiglia veloce**, e il taglio è dichiarato invece che subìto: `[M]` il tetto
è a **153 s su 180**, e §5.1 dice che una maglia in più si **scambia**, non si somma. ⇒ C5, C7 e C9
stanno in `tutto` e in `desktop-nuovo`, col loro guasto innestato accanto. ⛔ **Unica eccezione:
C10**, che costa meno della risoluzione del cronometro.

### 4.6-unetvicies ✅ ⭐⭐ **C10 sta in DUE famiglie, e il guasto innestato di C10 tiene in vita C13 sul portatile**

Due cose che si sono viste solo cablando, e nessuna delle due era prevista:

1. ⛔ **Il gemello vive metà in `src/` e metà in `banchi/rcp/`.** Un cambiamento alla copia del banco
   fa scattare la famiglia `rete` — ed è **esattamente** il cambiamento che rompe il gemello. ⇒ Se
   C10 stesse solo nella famiglia veloce, il caso che morde di più non la farebbe girare.
2. ⭐⭐ **La metà del gancio che vive sul portatile non innestava nessun guasto** (§4.6-novemdecies:
   le due metà stanno su due macchine). ⇒ C13, là, non avrebbe potuto **mai** diventare verde:
   avrebbe detto per sempre *«nessun guasto è mai stato iniettato»*, che dall'esterno ha lo stesso
   aspetto di una rete rotta. ⇒ C10 ha adesso un `--guasto-innestato` che copia i file **veri** in
   una cartella temporanea, ne cambia **un byte** e pretende il rosso. Costa `[M]` **0,1 s**.

`[M]` E il risultato si misura: sul portatile la famiglia `rete` fa **C10 verde · C12 verde · C13
verde** in **1 secondo**, senza accendere niente.

### 4.6-duoetvicies ⛔⛔⛔ **Il primo rosso che la rete tira fuori dal PRODOTTO — e sono due righe**

`[M]` 26 agosto 2026. C9, su tutte le scatole provate: **4 righe obbligate su 5 490 non si possono
attribuire a nessun inquilino**. Sono `src/tastiera.c` e `:486`, che scrivono nel **padre** senza
`registro_dice_di()`. ⛔ Due righe identiche parola per parola, una per inquilino: **con due sessioni
vive non si può dire quale sia di chi.**

⭐ **E questo è il mestiere della rete, fatto per la prima volta su un difetto che nessuno cercava**:
non è un guasto iniettato, non è un banco che sbaglia, è il prodotto. La cura è di due righe. ⛔ **Non
applicata**: toccare `src/` obbliga a ricostruire e a rimettere il binario in quattro scatole, e
l'ordine delle fasi è una decisione dell'utente (§4.6-sexdecies).

⚠ **E un rilievo accanto, che NON è un rosso**: `[M]` **1 402 righe (25,5 %)** nominano l'inquilino
solo nella prosa e non nella parentesi. Sono attribuibili, quindi C9 le conta e le stampa senza
giudicarle. ⇒ Se la fase le volesse rosse, C9 diventerebbe rossa su un quarto del registro: è una
decisione, non un difetto.

### 4.6-teretvicies ⛔⛔⛔ **IL PALCO MUORE COL CLIENTE — e contraddice I4 in faccia**

`[M]` 27 agosto 2026, provato per intero su un banco isolato con Mutter vero:

| | |
|---|---|
| `--headless` da solo | ⛔ **zero `wl_output`**, ed è voluto: in headless Mutter non apre le schede |
| il monitor virtuale | ⭐ nasce **solo quando un consumatore PipeWire si aggancia** al flusso — `[M]` 65–93 ms dopo l'aggancio, **mai prima** |
| lo stacco del **consumatore** | ⭐ il monitor **sopravvive** (`[M]` 15 s, c'è ancora) |
| la chiusura della **connessione D-Bus** di chi ha chiamato `RecordVirtual` | ⛔ **il monitor MUORE** |

⛔⛔ E nel prodotto quella connessione è del **figlio**, e **il figlio muore col client**.

> ⇒ ⭐⭐⭐ **Oggi il desktop ha uno schermo solo mentre qualcuno lo sta guardando.**
> ⛔ Ed è la contraddizione diretta di **I4** — *«il palco appartiene alla sessione e sopravvive alla
> disconnessione»* — che è una decisione dichiarata del progetto, non un dettaglio.

⭐ **La cura è provata, non ipotizzata**: tenendo aperti connessione e flusso per la vita della
sessione, con un consumatore agganciato **una volta sola**, `[M]` a client staccato un'applicazione
apre la finestra, i pixel ci finiscono, e il client che arriva dopo la vede (**12 055 colori
distinti**).

⛔ **Ma non è una riga**: il flusso va tolto al figlio (`src/figlio.c:5334-5513`) e dato a qualcosa
che viva quanto la sessione. ⇒ ❓ **È una decisione del regista**, e la maglia che la sorveglia è
**C6**.

⚠ E due strade sono **refutate**, non da rifare: `--virtual-monitor` all'avvio (⇒ due monitor, e dal
filo non esce nessun fotogramma — il difetto del 14 agosto riprodotto) e la geometria (1920×1080 e
1268×713 danno lo stesso esito).

### 4.6-quaterque-vicies ✅ ⛔ **I ~97 secondi erano della SCATOLA, non del prodotto**

⇒ `LEZIONI.md` §1.54. In una riga: la ricetta spostava il gruppo `polkitd` da 991 a 1991 per dare
991 alla scheda grafica, ⛔ `groupmod -g` non si porta dietro i file, `polkitd` non poteva più
leggere le sue regole e moriva, e `gnome-shell` incassava **quattro scadenze da 25 000 ms in fila**.

⭐ Curato nella ricetta, **senza nessun permesso nuovo** oltre a `SYS_ADMIN`: chi sposta il numero fa
seguire i file, e l'unità dei gruppi prende `Before=polkit.service`. `[M]` Da **~97 secondi** a
**1,105 · 0,998 · 0,957 s**.

### 4.6-quinquies-vicies ⛔⛔ **Il prodotto guida UN desktop, non quattro**

`[M]` C1 fatta girare dieci volte per scatola su KDE, XFCE e LXQt: **0 sane · 0 cieche · 30 «non ho
potuto guardare»**. Il registro lo dice: *«Mutter non espone RemoteDesktop»* ⇒ ⛔ `src/sessione.c` · `scrivi_dropin()`
e tutto `src/mutter.c` sanno avviare **solo GNOME**, e nelle altre tre scatole `gnome-shell` non c'è.

⭐ **Quel che le altre tre provano è reale ma più piccolo**: l'ambiente (passo 0), il suono (C5), i
residui (C7), il registro (C9), l'allineamento (C11). ⛔ **Non** provano che il prodotto regga su quei
desktop. ⇒ §3.7 della fase 11 va letto con questa correzione, e ❓ **tocca il senso della fase 12**.

⚠ E una cosa che la fase 12 dovrà affrontare, misurata di passaggio: ⛔ **KWin non sa nascere cieco**
— con `--output-count 0` un'uscita la fa lo stesso. ⇒ Il disegno *«zero monitor propri»* **non si
trasporta uguale** a KDE.

### 4.6-sexies-vicies ✅ ⭐⭐ **C15 — «la metà remota gira davvero»**, e il buco è misurato

Il gancio ha due metà su due macchine (§4.6-novemdecies). ⛔ Finora, **se la macchina di prova fosse
stata spenta per sempre, C12 e C13 sarebbero restate verdi**: il gancio girava sul portatile in un
secondo e nessuno si accorgeva che le maglie vere non giravano più.

⭐ `[M]` Il buco è **dimostrato**, non descritto: preso il registro vero e tolta l'unica riga eseguita
sulle scatole, **C12 verde · C13 verde · C15 ROSSA** sullo stesso file. Certificazione **21 su 21**.

⭐ E il segno non è il nome della macchina: è **una maglia che vuole una scatola e arriva a un
GIUDIZIO (0/1) invece che a un 3**.

⚠ **La famiglia `rete` dichiarava il falso** — *«nessuna accende una sessione»* — mentre C14 costa
`[M]` ~800 s e prende tutte e quattro le scatole. ⇒ Divisa: **`rete`** (C10, C11, C12, C13, C15 —
`[M]` ~11 s, e davvero non accende niente) e **`rete-intera`** (+ C14), chiamata da `tutto` e
`desktop-nuovo`.

### 4.6-septies-vicies ✅ ⛔ **`VA VELOCE` non si fa: §6 ha ragione, §3.4 è sbagliata**

§3.4 dichiarava due famiglie; §6 dichiara che la rete **non è** una rete di prestazioni; e nel gancio
`VA VELOCE` **non è mai esistita**. ⇒ La famiglia **non va creata**: le quattordici maglie sono tutte
sì/no, e una famiglia di numeri duplicherebbe i ~40 banchi delle fasi 9 e 10 **fuori dalle condizioni
in cui quei numeri valgono**. ⇒ §3.4 si riscrive, e il buco — ⛔ *«nessun banco confronta ieri con
oggi»* — si **dichiara in §6**, dove stanno le cose che la rete non prende.

### 4.6-duodetricies ✅ **Un desktop per macchina — la scelta fra più desktop è rimandata**

*18 settembre 2026, aprendo la fase 12. Alla domanda «se su una macchina ci sono GNOME e KDE, chi
sceglie quale accendere?» l'utente ha risposto:* *«Al momento la funzionalità di scelta di desktop
multipli la lasciamo per una futura implementazione».*

⇒ ✅ Il prodotto **non** offre una scelta del desktop: né all'utente, né come impostazione.
La macchina ha **il** suo desktop, e il server accende quello.
⇒ 🔸 *Derivato, correggibile senza discussione*: il server riconosce il desktop **da quel che è
installato**. Se ci sono tutti e due, resta **GNOME** — cioè quel che il prodotto fa già oggi, e
nessuna macchina servita cambia comportamento. ⚠ Il caso «tutti e due» è quindi **ambiguo per
costruzione** e si dichiara nel registro all'avvio, invece di scegliere in silenzio.
⇒ La funzione rimandata sta in `MASTERPLAN.md` **M5**.
⭐ **Allargata il 20 settembre 2026** — §0.6: le macchine con più desktop installati sono
**fuori scopo**, non soltanto prive di scelta.

### 4.7 ✅ ⛔⛔ Nessuno spegne il server — e «nessuno» comprende chi è davanti alla macchina

> ### ⭐ 21 SETTEMBRE 2026 — E VALE ANCHE PER XFCE, detto dall'utente
>
> *«ricorda che anche in XFCE vanno disabilitate le voci di standby, lockscreen, reset e
> spegnimento»* ⇒ le stesse quattro di GNOME e KDE: **sospensione, blocco schermo, riavvio,
> spegnimento**. ⛔ **«Esci» resta** — §4.1-ter, è l'unico gesto che termina la sessione.
> ⚠ Su XFCE **non esiste un KIOSK** come su KDE (`STUDI.md` §xfce §10.4): le voci si tolgono
> per ogni strada da cui si raggiungono (menu, pulsante del pannello, dialogo di uscita, gestore
> dell'energia), e ⛔ **ogni chiave scritta si rilegge** (§10.6: `xfconf-query` esce con zero
> anche quando il demone ha rifiutato). ⭐ **«Cambia utente» esce anche lui** — deciso dall'utente il 21 set 2026, sera: *«togli anche «Cambia utente» per rendere omogeneo il comportamento tra tutti i DE: l'unica voce che deve rimanere è logout»*. KDE col KIOSK (fase 12), GNOME con `org.gnome.desktop.lockdown disable-user-switching`, XFCE dal pannello e con `ShowSwitchUser=false`.

> ### ⛔⛔ E IL 25 AGOSTO 2026 QUESTA DECISIONE HA TROVATO UN BUCO — **chi aggiorna**
>
> ⭐⭐ **SMENTITO DALLA MISURA DEL 29 SETTEMBRE 2026** (`fasi/17-l-installatore.md` §5.2, T2): dieci
> prove con Firefox vero sui quattro desktop — fermare l'unità (`KillMode=mixed`), uccidere il solo
> padre, uccidere il solo figlio — **nessun desktop muore**: muoiono padre, aiutante PAM e figlio; il
> palco (partito con `setsid --fork`, fuori dall'unità), la sessione e i programmi sopravvivono, e al
> riattacco torna lo stesso compositore con le finestre. Il fatto del 25 agosto oggi non si riproduce.
>
> `[M]` Fermando l'unità del server per **aggiornarlo**, alle 18:14:29, **sono morte tutte le
> sessioni degli utenti** — finestre comprese; quindici secondi dopo ne è nata una **nuova e vuota**.
> La sessione grafica vive nell'**albero di processi del server** (`KillMode=mixed`).
>
> ⇒ ⭐⭐ **È esattamente il danno che questa decisione vieta** — *«spegnerla è l'unico gesto che porta
> via tutte le sessioni insieme»* — ⛔ **ottenuto però da chi amministra, e senza che nessuna riga lo
> dichiarasse.** Le tre cinture di sotto difendono dallo spegnimento della **macchina**; ⛔ **nessuna
> difende dal riavvio del SERVIZIO.**
>
> ⚠ **Non si allarga qui la decisione**: il confine è stato tracciato in `SPECIFICHE.md` §5.2 (*«la
> sessione sopravvive al client, NON al server»*), il rilievo sta in
> `fasi/10-multi-tenant-e-il-budget.md` **§7.5**, e ⭐ **il posto dove si cura è la fase 15 (era la 14 fino al 21 set 2026), il
> servizio**: aggiornare senza fermare nessuno.
>
> ⭐ **E per intanto la regola pratica, che discende da questa decisione senza cambiarla**: prima di
> riavviare il server **si guarda chi c'è**.

*Decisa dall'utente il **15 agosto 2026**, all'apertura della fase 5: «no, nessuno può spegnere,
riavviare, mettere in standby o sospensione il server, altrimenti si rischia di "buttare fuori"
anche altri eventuali utenti collegati alla macchina».*

⭐ **La ragione è la stessa che regge tutta la fase 5: la macchina è di più persone.** Spegnerla è
l'unico gesto che porta via **tutte** le sessioni insieme — e chi lo compie, dal menu di un desktop,
**non ha modo di vedere chi c'è collegato**. `SPECIFICHE.md` §11.3 lo prometteva già in una riga
(*«spegnimento, riavvio, sospensione: tolti alla sessione remota»*); questa decisione la allarga
— ⛔ **non «alla sessione remota»: a tutte** — e le dà per la prima volta un modo di essere
mantenuta.

**Tre cinture, e sono tre perché le strade sono tre:**

| | |
|---|---|
| **1 · la regola polkit**, `no` su `org.freedesktop.login1.power-off`, `reboot`, `suspend`, `hibernate` e le varianti `*-multiple-sessions` / `*-ignore-inhibit` | ⭐ **piatta, senza discriminante**: nessun `subject.local`, perché la decisione è «nessuno». ⭐ E copre **due strade con una riga sola**, perché guarda l'**azione** e non l'interfaccia: il menu del desktop **e** `systemctl poweroff` scritto in un terminale dentro la sessione. Su GNOME `CanShutdown` diventa falso e le voci **spariscono** (`gsm-manager.c`, `systemActions.js:340-359`). ⛔ **`no`, mai `auth_admin`**: `challenge` **mostra** la voce (`STUDI.md` §gnome §5.1, `STUDI.md` §kde §1579) |
| **2 · `logind.conf`**: `HandlePowerKey`, `HandleSuspendKey`, `HandleHibernateKey`, `HandleLidSwitch` = `ignore` | ⛔ il **tasto fisico** e il coperchio **non passano da polkit**: logind agisce per conto proprio, e la prima cintura non li vede |
| **3 · la sospensione automatica**: `Inhibit(…, SUSPEND\|IDLE)` **e** `sleep-inactive-ac-type=nothing` | ⚠ la prima cintura **ferma** la sospensione a inattività, ma l'utente vedrebbe lo stesso la notifica *«Automatic Suspend — Suspending soon»* `[M]` e poi un errore. Due cinture per **due sintomi diversi**: una impedisce il fatto, l'altra toglie la bugia dallo schermo |

> ### ⭐⭐ E LA SERA STESSA LE TRE CINTURE SONO STATE INSTALLATE E MISURATE — `[M]` 15 agosto 2026
>
> *Sulla macchina di prova, dopo il riavvio. ⛔ E la misura ha corretto **due** cose che questa voce
> diceva per deduzione.*
>
> | | |
> |---|---|
> | ⛔⛔ **la regola di v1 copriva tre azioni su dodici, e falliva ESATTAMENTE nel caso per cui era scritta** | `[M]` `org.freedesktop.login1.policy` elenca anche `*-multiple-sessions` e `*-ignore-inhibit`. ⛔ Quando sulla macchina ci sono sessioni di **più utenti**, logind non chiede `power-off`: chiede **`power-off-multiple-sessions`**, che la regola di v1 non nominava. ⇒ Con un utente solo funzionava, con due no — e nessuno l'avrebbe visto. ⚠ E `org.freedesktop.login1.halt` **non esiste** su questo systemd: quella riga era morta |
> | ⭐ **root non ha bisogno di nessuna eccezione** — *e la riga qui sotto, che ne prometteva una, era sbagliata* | `[M]` con la regola in vigore: da `nicfio` `CanPowerOff="no"`, **da root `"yes"`**. ⛔ Prima di interrogare polkit, logind guarda le **capacità** di chi chiede: chi ha `CAP_SYS_BOOT` è autorizzato e polkit **non viene consultato affatto**. ⇒ `sudo systemctl poweroff` funziona senza che la regola preveda niente |
> | ⛔⛔ **e da questo discende la trappola vera: la verifica NON si può fare dal server** | il server gira **da root**, quindi si sentirebbe rispondere `"yes"` sempre — un controllo che dice sempre di sì. ⇒ **La fa il FIGLIO**, dopo che è diventato l'utente. ⚠ Un controllo fatto dal posto sbagliato è peggio di un controllo che manca: il registro direbbe «verificato» |
> | ⭐ **il tasto fisico era vivo** | `[M]` in `/etc/systemd/logind.conf` tutte le righe `Handle*` erano **commentate**, cioè il predefinito — e `HandlePowerKey=poweroff`. ⇒ Fino a stasera il pulsante spegneva il server con chiunque collegato sopra. Adesso `ignore`, `[M]` riletto da `systemd-analyze cat-config` |
> | ⭐ **la sospensione ha una cintura più forte di polkit** | `sleep.conf.d` con `AllowSuspend=no` fa rifiutare la sospensione da **systemd**, non da polkit: `[M]` `CanSuspend="no"` **anche da root**. ⇒ Su suspend e hibernate la promessa è mantenuta anche contro l'amministratore |
>
> ⇒ **I due file stanno nel repository**, non solo sulla macchina — I7: `src/remotix-niente-spegnimento.rules`
> e `src/remotix-tasti.conf`.

⛔ **E quel che resta possibile va dichiarato adesso, non scoperto dopo: root.** ⭐ `[M]` root spegne
perché ha `CAP_SYS_BOOT`, e logind lo autorizza **prima** di arrivare a polkit; e in ogni caso
`systemctl --force poweroff` parla direttamente con PID 1. ⭐ **Ed è giusto che resti**: la macchina
deve restare amministrabile, e lo spegnimento per manutenzione è un gesto dell'**amministratore**,
non di un utente. ⇒ La promessa esatta, da scrivere così e non più larga:

> **Nessun utente, da nessuna sessione — remota o locale — spegne, riavvia o sospende il server.**
> Non «il server non si spegne».

> ### ⭐⭐ E l'utente l'ha specificato meglio, lo stesso giorno
>
> > *«L'utente collegato a REMOTIX può solo fare espressamente il logout o, ovviamente, operare sul
> > PC che sta utilizzando.»*
>
> ⭐ **Detta così, la regola smette di essere un elenco di divieti e diventa una regola sola**, ed è
> la forma da tenere:
>
> | dentro il desktop remoto | ⭐ **un solo gesto che finisce qualcosa: il logout** (§4.1-ter). Spegnere, riavviare, sospendere, ibernare **non gli appartengono** — non perché siano pericolosi, ma perché **non sono suoi**: quella macchina la stanno usando anche altri |
> |---|---|
> | sul PC da cui è collegato | ⭐ **fa quel che vuole, ed è affar suo**: lo spegne, lo riavvia, chiude il coperchio. Per noi è **il filo che cade**, cioè il caso già misurato — e non c'è niente da rilevare, da distinguere o da vietare |
>
> ⛔ **Da cui il metro del banco di §1.1 della fase 5**, che è più forte di «le voci sono sparite»:
> ⇒ *nel menu di sistema del desktop remoto resta «Esci…» **e nient'altro** di quella famiglia.*

> ⛔ *Qui c'era una riga che diceva di scrivere **l'eccezione di root dentro la regola**, perché
> altrimenti «perfino `sudo systemctl poweroff` fallirebbe». ⭐ La misura del 15 agosto l'ha smentita:
> l'eccezione non serve, perché non è polkit a decidere per root. La regola resta **piatta**, come
> l'utente l'ha voluta.*

⭐ **E questa regola dà finalmente un mestiere a `0x0C SERVER_IN_CHIUSURA`**: se l'unico spegnimento
legittimo è quello dell'amministratore, allora **quella è l'unica strada su cui i client vanno
avvisati**, e la cura del rilievo B-7 (`main.c` · `main()`, `trasporto_congeda_tutte`) smette di essere una
riparazione e diventa **il percorso normale**.

⚠ **E le tre cinture sono tutte righe di configurazione, cioè quel che l'invariante I7 vieta**: vanno
**installate da noi** e **verificate dopo l'avvio**, come l'headless di §4.3-bis. ⭐ La verifica è si
chiede a logind `CanPowerOff` / `CanReboot` / `CanSuspend` / `CanHibernate` e si pretende **`no`** —
se risponde `yes` o `challenge`, la protezione non c'è e si dichiara il fallimento. ⛔ **E si chiede
dal FIGLIO, che è l'utente**: dal server, che è root, la risposta è `yes` per costruzione, e il
registro direbbe «verificato» avendo guardato la cosa sbagliata.

---

### 4.8 ✅ ⛔ Niente sei ore: **sessanta minuti senza input e la sessione si chiude**

*Decisa dall'utente il **16 agosto 2026**, con queste parole: «niente timeout delle 6 ore: se dopo 60
minuti non c'è traccia di input la sessione viene killata».*

`SPECIFICHE.md` §5.3 aveva scritto **6 ore senza alcun attacco**. ⇒ Cambiano **due cose**, e vanno
lette separate:

| | prima | adesso |
|---|---|---|
| il tetto | 6 ore | **60 minuti** |
| ⛔ **il criterio** | «nessuno si è **attaccato**» | «nessuno ha **toccato niente**» |

⭐ **Il secondo cambio è il più grosso**, e va detto: uno che si attacca e resta a guardare non
rinnova più niente. Il tetto si nutre degli stessi gesti dell'orologio dei 30 minuti — i cinque
input di §7.3 — e non del fatto che una connessione esista.

### ⭐ La decisione è venuta da un numero, e il numero è stato misurato apposta

*L'utente aveva chiesto: «misura la memoria. Potrei anche decidere di diminuire drasticamente questo
intervallo».*

`[M]` 16 agosto 2026, sessione abbandonata, PSS (le librerie condivise contate una volta sola):

| | |
|---|---|
| la sessione intera di `prova` | **477 MB** su 31 851 totali ⇒ **1,5 %** |
| di cui `gnome-shell` | 182 MB |
| di cui **il nostro figlio** (palco, cattura, codificatore) | **116 MB** |
| CPU | ~0,017 % di un nucleo |
| ⭐ **crescita in 4 minuti** | **nessuna**: 477 · 476 · 476 · 477 · 477 · 477 · 477 · 477 · 477 MB |

⇒ **Non è una perdita, è un costo fisso.** ⚠ E la scelta, con quel numero davanti, è dell'utente: si
paga per un'ora invece che per sei.

### ⚠ E una complicazione è stata proposta e SCARTATA — dall'utente, con una misura di buon senso

Avevo proposto di azzerare il tetto anche al **riaggancio**, temendo di uccidere una sessione mentre
qualcuno la guardava. La risposta:

> *«la tua ipotesi comporta il fatto che l'utente in 10 minuti non fa nemmeno un clic col mouse,
> alquanto improbabile»*

⭐ **Ed è giusta**: perché il danno avvenisse, uno dovrebbe rientrare e poi non toccare **niente** per
il resto dell'ora. ⇒ Si conta l'input e basta — la regola più semplice, e anche la più facile da
spiegare a chi la subisce.

### Che cosa comporta, in codice

- il motivo `0x03 SESSIONE_ABBANDONATA` di `RCP.md` §8.2 **esiste da sempre e non l'aveva mai spedito
  nessuno**: adesso è il suo. ⚠ Di solito non lo riceverà nessuno — se il tetto scade è perché non
  c'era più nessuno — ma chi c'è legge una frase invece di guardare uno schermo fermo;
- **configurabile** (`--abbandono-s`), `0` = spento, e il valore in vigore **si scrive nel registro
  all'avvio** insieme agli altri due: un tetto da un'ora non lo verifica nessuno aspettando un'ora.

---

## 5. La geometria — la tela e la vista

### 5.0 ✅ La tela nasce a ogni attacco, e sta ferma finché il client resta

*8 agosto 2026, modello dettato dall'utente.*

| Momento | Chi decide la misura | Chi adatta |
|---|---|---|
| **attacco** | il client: la sessione legge la sua risoluzione e usa quella | nessuno — è 1:1 |
| **durante la sessione** | nessuno: la tela non si muove | il **client** riscala l'immagine |
| **riattacco** da un altro dispositivo | il nuovo client, con la sua risoluzione | nessuno — di nuovo 1:1 |

Chiude la domanda che era aperta in §7.1: la tela **non** ha un valore predefinito né una
preferenza dell'utente. La detta il client, a ogni attacco.

**La virtù del modello è il caso mobile**, e viene giusto da solo: il telefono si attacca e la
tela nasce della forma del telefono — pixel veri, niente bande, niente scalatura. Nessuna
delle alternative discusse (tela fissa generosa, tela con vista scorrevole) faceva altrettanto
bene senza logica aggiuntiva.

**L'attacco funziona su tutti e quattro i desktop**, KDE compreso: la misura si scrive nella
riga di avvio del compositore (`--virtual --width W --height H`) **prima** che la sessione
parta, e la sessione parte al primo attacco.

### 5.0-bis 🔸 Il riattacco a misura diversa su KDE ≤ 6.7.4: degradazione dichiarata

> ⚠ *Il titolo diceva «KDE < 6.8», e §5.0-quater prometteva quella versione «a ottobre».*
> ⛔ **Corretto il 14 agosto 2026**: `[R]` verificato su invent.kde.org, **`Plasma/6.8` non
> esiste**, l'ultimo tag è **v6.7.4**, e i rami da `Plasma/6.3` a `Plasma/6.7` non hanno il
> ridimensionamento a caldo — c'è **solo su `master`**, senza una data di rilascio. ⇒ Una
> degradazione con una scadenza scritta invecchia peggio di una senza: qui la scadenza **non
> c'è**, e va detto.

È l'unico punto in cui il modello non può essere servito. A sessione viva KWin 6.3.6 non
cambia misura `[M]`, e riavviarlo significherebbe uccidere la sessione — cioè distruggere
proprio il distacco che il modello offre.

**Ripiego: si tiene la tela vecchia e riscala il client.** Non costa una riga in più, perché è
lo stesso codice del punto «durante la sessione». Su Debian stabile, riattaccandosi da un
dispositivo di forma diversa, si vede il desktop della forma precedente riscalato, finché la
sessione non viene chiusa. Su GNOME, wlroots e KDE ≥ 6.8 si vede la forma nuova.

Il ripiego **si dichiara nel registro** (`CODER.md` §4.2): un ripiego silenzioso produce due
comportamenti sotto la stessa etichetta.

### 5.0-ter 🔸 `[?]` Ridurre anche la misura codificata quando la finestra è piccola

Se l'utente restringe molto la finestra, il server continua a codificare la tela intera e il
client la rimpicciolisce: quei pixel si pagano in banda senza vederli. Si **potrebbe** far
scendere anche la misura codificata sotto una certa soglia, con assestamento.

⚠ **Non è nel modello, ed è volutamente fuori**: prima va misurato se il problema esiste
davvero, e quanto pesa. Un'ottimizzazione decisa prima della misura è §7.2 di `LEZIONI.md` —
ottimizzare nella direzione sbagliata.

### 5.0-quater 🔸 ⛔ ~~Con il browser, «la risoluzione del client» sono due misure diverse~~ → **la tela è la FINESTRA**

> ## ⛔⛔ SUPERATA DA §5.0-sexies, e attuata il 15 agosto 2026
>
> *Questa voce sceglieva **lo schermo del dispositivo** come tela, e la finestra come vista. ⛔ È
> stata rovesciata da §5.0-sexies — decisa dall'utente il 14 agosto — che prende **la finestra**:
> tela e vista coincidono, la scala vale 1 e la conversione delle coordinate sparisce.*
>
> ⚠ **E le due ragioni di questa voce non erano sbagliate: erano legate a un vincolo che non c'è
> più.** La prima diceva che una finestra piccola darebbe *«un desktop piccolo per tutta la
> sessione»* — vero **finché la tela non si poteva cambiare**. Da quando `figli_ritela()` →
> `cattura_ridimensiona()` esiste (`[M]` 6 ms a caldo, 15 agosto), la tela si rifà **a ogni
> attacco e a ogni riattacco**. ⛔ *Durante* la sessione no, e dal 17 agosto 2026 nemmeno dietro un
> interruttore: §5.1-bis l'ha tolto. ⚠ Ma la voce resta curata lo stesso — «piccolo per sempre»
> voleva dire *per tutta la sessione*, e una sessione si riattacca.
>
> ⭐ **E la `[?]` dello zoom di pagina, che questa voce lasciava aperta, si è chiusa da sé**: la
> misura non si legge più dallo schermo — si legge dalla finestra, e il fattore di zoom ci è già
> dentro. Un client con zoom ≠ 100 % non dichiara più una tela sbagliata: dichiara la sua.
>
> ⇒ Quel che resta valido qui sotto è la **distinzione fra tela e vista** e il perché sono due
> grandezze diverse. Quel che cade è **quale delle due misure diventa la tela**.


*9 agosto 2026, chiedendolo l'utente dopo il passaggio al client web: «resta da chiarire il
comportamento della risoluzione avendo adesso come client un browser».*

§5.0 dice *«la sessione legge la risoluzione del client e usa quella»*, e con un programma nostro a
schermo intero non c'era altro da dire. ⛔ **Un browser è una finestra dentro uno schermo**, e le due
misure differiscono — su un telefono di un fattore tre, per via dei pixel logici.

| | |
|---|---|
| **la tela** | 🔸 **lo schermo del dispositivo, in pixel fisici** |
| **la vista** | la finestra, in pixel fisici |

**Le due ragioni, e la seconda non l'aveva vista nessuno:**

1. la tela **è il desktop**: prendendola dalla finestra, un collegamento aperto per caso in una
   finestrella darebbe un desktop piccolo **per tutta la sessione** — e §5.3 ha già dichiarato che
   ingrandire non inventa dettaglio;
2. ⭐ **la Keyboard Lock esiste solo a schermo intero** (`STUDI.md` §web §5). Cioè il modo in cui questo
   prodotto si usa davvero *è* lo schermo intero, che è **esattamente la condizione in cui vista e
   tela coincidono**. Il modello non ha un caso normale e un caso degradato: ha un caso normale che
   coincide con quello ottimo.

⚠ **Non cambia nessuna decisione presa**: §5.0 resta (la tela la detta il client, all'attacco), §5.1
resta (ridimensionare la finestra non tocca il desktop), §5.2 resta come corretta oggi (si codifica
la tela, il client riscala). Cambia **che cosa il client legge** per rispondere.

`[?]` **E tre cose da misurare prima di crederci**, tutte in `SPECIFICHE.md` §6.1-bis: che lo zoom
della pagina non falsi il conto — ⛔ *l'utente che ha premuto `Ctrl +` prima di collegarsi
dichiarerebbe una tela sbagliata, e resterebbe per tutta la sessione* — che cosa risponde DeX, e se
l'arrotondamento dei browser possa produrre un numero dispari, che `RCP.md` §4.5 rifiuta.

> ### ⛔ La prima delle tre È MISURATA, e la risposta è la peggiore — `[M]` 10 agosto 2026
>
> *Banco **S5**, `banchi/01-s5-tela.sh` + `01-s5-pagina.html`, registro `banchi/01-s5-esiti.jsonl`
> (due giri identici, 23:13 e 23:14). Scena: schermo **Xvfb 1920×1080×24**, risoluzione letta **fuori
> dal browser** con `xdpyinfo` = 1920×1080. Il dettaglio sta in `web/rapporti/S-esiti-sonda.md` §3.*
>
> | Motore | zoom | `screen` | `devicePixelRatio` | **tela che il client dichiarerebbe** |
> |---|---|---|---|---|
> | **Chrome 151.0.7922.108** | 100 % | 1920×1080 | 1 | 1920×1080 |
> | | 150 % | **1920×1080** | 1,5 | ⛔ **2880×1620** |
> | **Firefox 140.13.0esr** | 100 % | 1920×1080 | 1 | 1920×1080 |
> | | 150 % | **1280×720** | 1,5 | ✅ 1920×1080 |
>
> ⛔ **Su Chrome `screen.width` NON cala con lo zoom di pagina**, mentre `devicePixelRatio` sale:
> la formula di `SPECIFICHE.md` §6.1-bis dà `risoluzione × zoom`. Un utente su un portatile 1920×1080
> con lo zoom al 150 % dichiarerebbe una tela **del 50 % più grande di quella che esiste** — ed è
> **esattamente il difetto che questa decisione dice di esistere per evitare**.
>
> ⛔ **Quindi la ragione scritta accanto a questa decisione era `[?]` e adesso è FALSA su un motore
> su due.** `FASI.md` §01-filo-nudo la giustificava così: *«`screen.width` cala di un terzo,
> `devicePixelRatio` sale di un mezzo, **il prodotto resta**»*. Resta su Firefox. Su Chrome no.
> È il caso di `LEZIONI.md` §2.3-quater preso in flagrante: *una decisione presa citando un
> comportamento non misurato è presa a metà* — e stavolta il comportamento, misurato, va nell'altro
> verso.
>
> ⚠ **Che cosa NON cambia, e va detto per non far credere a un ripensamento**: la decisione resta 🔸
> e resta *«la tela è lo schermo del dispositivo in pixel fisici»*. Quel che cade è **la formula con
> cui il client lo legge**, non che cosa deve leggere. ⛔ E non si aggiusta con una riga: lo zoom di
> pagina **non è leggibile da JavaScript in modo portabile**. La cura è di chi tiene `SPECIFICHE.md`
> §6.1-bis, e finché non c'è, un client su Chrome con zoom ≠ 100 % **dichiara una tela sbagliata**.
>
> ⚠ **E metà di S5 non è misurata**: il **DeX** non c'era. *«Il Chrome del portatile lo fa»* non dice
> niente del Chrome del telefono — forma **E10** — e la seconda delle tre `[?]` resta intera.

### 5.0-quinquies ✅ ⭐ ~~La tela resta **1920×1080**~~ → **accesa da §5.0-sexies il 14-15 agosto**

> ⭐ **Questa voce si è chiusa da sé, come aveva previsto.** Diceva: *«resta aperta, e va nominata
> alla fase in cui si accende, l'attuazione di `SPECIFICHE.md` §6.1»*. Quella fase è stata la **coda
> della fase 4**: §5.0-sexies l'ha decisa il 14 agosto e il 15 la tela ha smesso di essere
> 1920×1080 — prende la misura della finestra del client (`[M]` 1264×800 su una finestra 1265×800).
> ⚠ Il ragionamento qui sotto **resta valido per il suo giorno**, e la sua ultima riga è quella che
> ha aperto la porta.

*13 agosto 2026, all'apertura della fase 3, **decisa dall'utente**. Era ereditata dalla scena di un
banco e non era mai stata decisa da nessuno: `src/main.c` · `TELA_L` ha `TELA_L 1920` scritto a mano.*

La domanda è stata posta con il suo prezzo misurato accanto: sullo schermo dell'utente la tela
viene dipinta all'**86 %**, cioè **912 px di nero**. Le tre alternative messe davanti:

| | |
|---|---|
| ⭐ **tenerla a 1920×1080** | **scelta** |
| portarla a 2560×1440 (lo schermo dell'utente) | non scelta |
| accendere subito `SPECIFICHE.md` §6.1 — *la tela nasce dallo schermo del client* | non scelta: oggi il prodotto non lo fa |

⭐ **La ragione è di metodo, ed è la ragione per cui la decisione è stata presa il giorno stesso in
cui la fase si apriva**: la fase 3 misura il **tempo**, non la geometria. Con la tela ferma, un
ritardo che sfora i 50 ms accusa l'architettura; con la tela cambiata sotto, non si saprebbe se
accusa l'architettura o il conto dei pixel.

⛔ **E le bande nere non sono la risoluzione**, o la `[?]` verrà riaperta credendo di curarle:
2545×927 di finestra fanno un rapporto **2,74** contro un 16:9 di **1,7778**. Quelle bande sono la
**forma della finestra**, e sparirebbero solo a schermo pieno — cambiare la tela non le tocca.

⏳ **Resta aperta**, e va nominata alla fase in cui si accende, l'attuazione di `SPECIFICHE.md`
§6.1: oggi è una specifica scritta e **non attuata** (§5.0-quater ne racconta il pezzo difficile).

### 5.0-sexies ✅ ⭐⭐ La tela del server prende la misura della tela del client — e la conversione delle coordinate **sparisce**

*14 agosto 2026, sera, **decisa dall'utente** dopo una giornata in cui il mouse sul DeX è rimasto
inutilizzabile attraverso quattro cure. Sue parole: «abbiamo due tele: quella del server e quella
del client (la dimensione della finestra di rendering del browser). Bisogna solo convertire le
coordinate» — e poi, chiedendo la verifica: «se questo è possibile, allora non servono più nemmeno
le conversioni».*

⭐ **Non rovescia §5.0-quinquies: la accende.** Quella decisione teneva la tela a 1920×1080 per una
ragione di **metodo** («la fase 3 misura il tempo, non la geometria») e lasciava scritto ⏳ *«resta
aperta, e va nominata alla fase in cui si accende, l'attuazione di `SPECIFICHE.md` §6.1»*. È questa.

| | |
|---|---|
| **la tela del server** | si chiede della misura della **tela del client**, arrotondata in giù al **pari** |
| **la tela del client** | si stringe alla misura **concessa** ⇒ le due coincidono |
| **la conversione** | `x_desktop = x_tela`: **l'identità** |
| **le bande nere** | non esistono più *dentro* l'immagine: quel che avanza (≤1 px per asse) è **sfondo della pagina fuori dalla tela**, e non viaggia sul filo |

> ⚠ **E il monito di §5.0-quinquies non è stato ignorato**, è stato letto: *«le bande nere non sono
> la risoluzione… sono la forma della finestra, e cambiare la tela non le tocca»*. ⭐ È vero per il
> cambio che quella voce esaminava — da 1920×1080 a 2560×1440, **sempre 16:9**. Qui la tela prende
> il **rapporto del client**, quindi il monito non si applica: le bande spariscono perché sparisce
> la differenza di forma che le genera.

#### Le misure che l'hanno resa possibile — quattro banchi in parallelo, 14 agosto 2026

| | misura esatta | cambio a caldo |
|---|---|---|
| **Mutter** (GNOME) | `[M]` **30 richieste su 30**, da 1×1 a 7680×4320, scala **1,000000**, passo senza riempimento | `[M]` primo fotogramma nuovo a **41,6 ms**, nessun nero, sessione ed EIS intatti; **20 ridimensionamenti in 2 s, 20 esatti** |
| **labwc** (XFCE, LXQt) | `[M]` esatta **anche a larghezza dispari**; `1×1`, `1919×1079`, `32768×1080` tutte al pixel | `[M]` **5,1 ms**, **0 fotogrammi persi su 25** |
| **KWin** (KDE) | `[R]` nessuna validazione: né minimo, né massimo, né parità, né multipli | ⛔ solo su `master` — vedi §5.0-bis |
| **il codificatore** | `[M]` il vincolo è **pari, e basta** — non multiplo di 8 né di 16 | — |

⛔ **Il vincolo del pari è NOSTRO, non dei compositori**: è il 4:2:0 (`src/codificatore.c` · `croma_flusso` e
`:1512`). `[M]` In 4:4:4 passa anche il dispari. ⇒ Si tronca in **giù** (2133 → 2132) e **lo si
dichiara** con `TELA(ADATTATA)`: un pixel detto vale più di un pixel nascosto in una scala.

#### ⛔ Le tre guardie che dobbiamo scrivere noi — nessuno le fa a monte

Tutte e tre scoperte misurando, e tutte e tre della stessa famiglia: **il silenzio**.

1. **Il tetto della misura.** `[M]` Oltre **16384** per lato `gnome-shell` muore — e 16386 è
   *dentro* il `MAX_SIZE` che Mutter **dichiara**, quindi il limite dichiarato mente. `[M]` Su
   labwc `32768×32768` uccide il compositore **con zero righe di registro**. ⇒ Il tetto lo mette il
   nostro codice, e un client non può sceglierlo senza limiti.
2. ⛔⛔ **La scala di GNOME.** `[M]` Con `org.gnome.desktop.interface scaling-factor = 2` i pixel
   restano quelli chiesti ma il monitor logico prende **scala 2,0**: il layout diventa
   `roundf(2133/2) = 1067` e **1067×2 = 2134 ≠ 2133**. È lo spazio delle coordinate dell'**input**
   ⇒ **il puntatore va altrove e nessuno lo dice.** Cura: leggere la scala e **fallire** se non è
   `1,0`.
3. **Chiesto contro concesso.** `[R]` `src/cattura.c` · `chiesta_larghezza`/`chiesta_altezza` non confronta mai la misura **chiesta** a
   PipeWire con quella **negoziata**, e `codificatore_comprimi()` riceve i pixel e il passo ma
   **non** larghezza e altezza, quindi non può fare da testimone. ⛔ Oggi è irraggiungibile perché
   si chiede sempre 1920×1080: **è questa decisione a renderlo raggiungibile**, e va chiuso
   insieme, non dopo.

#### La regola di forma, rubata a neatvnc

⭐ `[M]` Chiedere a labwc la misura **che l'output ha già** risponde «riuscito» e **non manda
nessun evento**; un serial vecchio risponde «annullato» e non fa niente. ⛔ `wayvnc` tratta
*riuscito*, *fallito* e *annullato* nello stesso ramo — da non copiare. ⇒ **La verità la dice il
fotogramma, non l'esito della richiesta.**

#### ⏳ ⭐ Per quando si affronterà il RI-ATTACCO: la soluzione è già misurata, e sta qui

*Annotato su richiesta dell'utente, 14 agosto 2026: «il problema della dimensione della finestra
del browser si ripresenterà, ma la soluzione è già bella pronta».*

⛔ **La domanda tornerà, ed è inevitabile**: §4.1 promette che **la sessione sopravvive al
client**, e §5.0 che la tela **nasce a ogni attacco**. ⇒ Il giorno in cui l'utente si stacca dal
DeX e si riattacca dal portatile, la finestra del browser ha **un'altra misura** — e la tela del
server è quella di ieri. È esattamente il caso che oggi produrrebbe di nuovo bande, scala e
conversione.

⭐ **E la risposta non va cercata quel giorno: è stata misurata il 14 agosto 2026**, ed è il
ridimensionamento **a caldo**, sulla sessione viva, senza rifarla:

| | costo misurato | che cosa NON succede |
|---|---|---|
| **Mutter** (GNOME) | `[M]` primo fotogramma nuovo a **41,6 ms** · **20 ridimensionamenti in 2 s, 20 esatti** | nessun fotogramma nero, **sessione ed EIS intatti**, nessuna riconnessione |
| **labwc** (XFCE, LXQt) | `[M]` **5,1 ms** · **0 fotogrammi persi su 25** | nessun fotogramma nero; il fotogramma successivo è già alla misura nuova |
| **KWin** (KDE ≤ 6.7.4) | ⛔ non esiste | ⇒ vale il ripiego dichiarato di §5.0-bis, e **solo lì** |

⇒ ⭐ **Il ri-attacco a misura diversa non è un problema aperto: è un caso già coperto**, su tre
desktop su quattro, a un costo che l'utente non percepisce. Chi affronterà quel tema non deve
studiare niente di nuovo — deve **chiamare** `cattura_ridimensiona()` e rileggere questa tabella.

> ### ✅ ⭐⭐ SCRITTA E MISURATA — la notte del 15 agosto 2026
>
> *Questa voce diceva «`cattura_ridimensiona()` alla data di questa voce **non esiste ancora**: è
> l'unica riga di lavoro rimasta». Adesso esiste, e con lei la catena intera.*
>
> **La catena, per nome**, e ogni anello sta dove sta la cosa che sa:
>
> | dove | che cosa |
> |---|---|
> | `src/pagina.html` | `chiedi_tela()` manda `ADATTA_TELA` con la misura della finestra, **all'attacco** |
> | `src/rcp.c` `T_ADATTA_TELA` | applica §4.5 (limiti, parità, `video.misura_massima`) e gira la richiesta al palco. ⛔ **Non risponde subito**: segna una richiesta «in volo» |
> | `src/webtransport.c` · `src/main.c` | portano la domanda oltre il confine di processo |
> | `src/figlio.c` `figli_ritela()` | → `MSG_INPUT/RITELA` al figlio |
> | `src/cattura.c` `cattura_ridimensiona()` | → `pw_stream_update_params()` |
> | ⭐ e **la risposta torna indietro**: `MSG_TELA` → `rcp_tela_dal_palco()` → `TELA(ADATTATA)` |
>
> ⛔ **La risposta torna, e non si indovina**: la prima stesura di stanotte faceva dedurre al padre
> l'esito **dai fotogrammi** («se ne arriva uno di misura diversa, il palco ha obbedito»), e quattro
> agenti mandati a refutarla hanno trovato tre casi in cui deduceva male — fra cui **due
> `ADATTA_TELA` incatenate**, cioè un utente che trascina il bordo della finestra. ⇒ Il figlio adesso
> risponde portando **due** misure: quella *chiesta* (per riconoscere a quale richiesta risponde) e
> quella *avuta* (`0x0` = non ce l'ha fatta).
>
> #### `[M]` Le misure della notte, sulla macchina di prova, utente `prova`, GNOME headless
>
> | | prima (14 ago) | adesso (15 ago) |
> |---|---|---|
> | ⭐⭐ dal canale video al primo fotogramma | **4,4 s** (659 «attese a vuoto») | **311 ms** |
> | la tela in vigore all'attacco | 1920×1080 fissa | **1264×800** = la finestra del browser |
> | la scala di disegno del client | 0,658 (`imageRendering: auto`) | **1,000** (`pixelated`) |
> | il ridimensionamento a caldo (1264×800 → 1000×640) | non esisteva | ⭐ **6 ms** dalla risposta del palco alla chiave spedita |
> | fotogrammi scartati per misura · trattenuti · errori | — | **0 · 0 · 0** |
>
> ⭐ **E il desktop lo dice da sé**: GNOME *Impostazioni → Displays* dentro la sessione remota
> riporta **«Resolution 1264 × 800 (3:2)»** e **«Scale 100%»**. Non è una nostra riga di registro:
> è il compositore che dichiara la misura che gli abbiamo chiesto.
>
> #### Le tre guardie: dove sono finite
>
> | guardia | stato |
> |---|---|
> | 1 · il tetto della misura | ✅ `rcp_misura_ammessa()`, e ⛔ **corretta stanotte**: i limiti sono quelli di §4.5 **per lato** (320..7680 × 240..4320), non i 200..8192 della prima stesura — che `ATTACCA` avrebbe rifiutato al ri-attacco |
> | 2 · la scala di GNOME | ✅ **chiusa stanotte** come §5.0-sexies chiedeva («leggere la scala e **fallire**»): `mutter_scala_nostra()` + il rifiuto in `prendi_il_palco()`. ⚠ Si guarda il **nostro** monitor, non il peggiore della macchina: un portatile con lo schermo interno a 2,0 non ha nessun difetto. `[M]` sulla macchina di prova la scala del nostro «Meta-0» è **1,000**, e la riga si scrive anche quando è buona |
> | 3 · chiesto contro concesso | ✅ in `cattura.c` (`su_parametri`), e da stanotte anche **nel figlio**: i 28 byte di §6.2 portano la misura del FOTOGRAMMA, non quella che si era chiesta |
>
> #### I tempi, e il perché di ciascuno
>
> | | valore | perché |
> |---|---|---|
> | `RCP_TELA_ATTESA_MS` | **3000 ms** | il fondo oltre cui si risponde `NON_ORA` comunque: §7.1 vuole un `TELA` per ogni `ADATTA_TELA`, e §6.2 fa **trattenere fotogrammi** al client finché aspetta |
> | `RCP_TELA_RICHIAMO_MS` | 500 ms, che raddoppia fino a 8 s | ogni quanto si **richiede** al palco di tornare alla tela in vigore, quando ne ha una sua |
> | ~~`TELA_FONDO_MS` (client)~~ ⛔ **USCITO il 17 agosto 2026** *(riallineato il 28)* | ~~250 ms~~ | chi trascina un bordo produce decine di `resize` al secondo — ⭐ ma il fondo è uscito **con la funzione che serviva** (`tela_forse_chiedi()`): `src/pagina.html` ne tiene la lapide, perché la cura andrebbe rimessa solo se qualcuno rimettesse l'inseguimento |
> | `RISVEGLIO_MS` (figlio) | 400 ms | ogni quanto si riavvia il flusso quando **una chiave è dovuta e la scena è ferma** — è la cura dei 4,4 secondi |
>
> ⛔ **E una cosa che il server NON fa, per una riga che manca a `RCP.md`**: quando il palco cambia
> misura **senza che nessuno gliel'abbia chiesto**, il server **non adotta** la misura nuova e non
> manda nessun `TELA`. La prima stesura lo faceva — sembrava gentile — ed è fatale: §6.2 dice che il
> client trattiene una misura mai annunciata **solo finché ha una `ADATTA_TELA` senza risposta**, e
> senza quella è `ERRORE_PROTOCOLLO`. ⇒ Si **richiede al palco di tornare**, con un'attesa che
> cresce, e nel frattempo la sessione mostra l'ultima immagine buona (I1: brutta e viva). ⏳ La riga
> che manca è in `RCP.md` §7.1: *che cosa fa un server quando il palco cambia misura da sé*.

⚠ E le tre guardie qui sopra valgono **a maggior ragione** al ri-attacco: è il momento in cui la
misura cambia davvero, cioè il momento in cui una divergenza silenziosa fra chiesto e concesso
avrebbe le sue conseguenze.

#### Su KDE non cambia niente: vale §5.0-bis

⚠ *E §5.0-bis va corretta in un punto*: diceva «KDE < 6.8». `[R]` Verificato il 14 agosto su
invent.kde.org: **`Plasma/6.8` non esiste**, l'ultimo tag è **v6.7.4**, e il ridimensionamento a
caldo è **solo su `master`**, senza una data. ⇒ Si legga «KDE ≤ 6.7.4, e la versione che lo porta
non è ancora uscita».

### 5.0-septies 🔸 Al congedo il palco **NON** si rimette a una misura di riposo — *provvisoria, 22 agosto 2026*

*Portata all'utente come una delle due decisioni che aspettavano lui. ⛔ **E gliel'avevo posta con
una premessa falsa**: «chi si collega eredita la finestra di chi c'era prima». Non c'è nessun «chi
c'era prima» — il multi-tenant è la **fase 10** e non esiste, e la sessione grafica è **una per
utente** (invariante **I2**, `sessione.c` · `sessione_assicura()`). ⭐ **L'ha rilevato l'utente**, e la voce sta qui
anche per quello.*

**Che cosa sopravvive davvero**: non la sessione di un altro, ma **la misura del palco** lasciata
dalla **connessione precedente dello stesso utente**. `RCP.md` §4.5 lo dichiara — *«la tela
SOPRAVVIVE alla sessione»* — e `[M]` il 21 agosto sul prodotto vero tre attacchi di fila con
`ATTACCA(1920×1080)` hanno ricevuto `SESSIONE` con **1920×1080**, **1264×800** e **1600×900**: ogni
volta quel che il giro prima aveva lasciato.

**La decisione, per ora**: si lascia com'è. Tre ragioni, e la terza è quella che conta:

1. ⭐ **si corregge già da sola**: la misura di `ATTACCA` è una **preferenza**, ma subito dopo
   `SESSIONE` il client manda `ADATTA_TELA` con la sua misura vera (§5.0-sexies, dal 15 agosto). ⇒
   Resta solo un **istante** all'attacco in cui la tela in vigore è quella vecchia;
2. ⛔ **un riposo al congedo è un secondo riordino delle finestre** fatto mentre l'utente non
   guarda: il desktop rimescola le finestre a **ogni** cambio di misura del monitor, e quel
   rimescolo il server non lo può disfare;
3. ⛔⛔ **e non curerebbe il problema vero.** Il costo che l'utente vedrebbe è lo scenario
   PC → telefono → PC: dal telefono il palco si rimpicciolisce, GNOME **schiaccia le finestre** per
   farcele stare, e al ritorno il palco torna grande **ma le finestre restano schiacciate**. Una
   misura di riposo non le rimette dov'erano — ne aggiunge una terza.

⏳ **`[?]` E la strada che curerebbe davvero quello scenario è un'altra**, ed è di **fase 9**: non
far cambiare misura al palco quando ci si attacca da uno schermo piccolo, e lasciar **riscalare** il
client — che è precisamente quel che il prodotto già sa fare per la vista (§5.1). ⚠ Non si anticipa
qui: ha bisogno del punto di lavoro fra qualità e banda, che è la fase 9.

🔸 **Perché è provvisoria e non chiusa**: *«per il momento accetto il tuo suggerimento, ma poi ci
penserò su»* — l'utente, 22 agosto 2026. ⇒ La voce **non** va marcata ✅ finché non ci ritorna, e
chi la riapre trova qui la ragione per cui era stata lasciata così.

### 5.1 ✅ Se l'utente ridimensiona la finestra, l'immagine si riscala

*8 agosto 2026. «Tagliamo la testa al toro. Anziché correre dietro ai compositor, una scelta
che vale per tutti».*

**Ridimensionare la finestra del client non tocca mai il desktop.** Si adatta la vista; le
finestre dell'utente non si muovono. Uguale su GNOME, KDE, XFCE e LXQt.

> ### ⚠ E DAL 15 AGOSTO 2026 QUESTA VOCE VALE **DURANTE** LA SESSIONE, NON ALL'ATTACCO
>
> §5.0-sexies ha deciso che **la tela del server prende la misura della tela del client**, e quella
> misura la si chiede **all'attacco di ogni sessione**. ⇒ All'attacco il desktop *cambia* misura, ed
> è voluto: è la decisione dell'utente del 14 agosto.
>
> ⛔ **Ma le tre ragioni di questa voce non sono invecchiate**, e la terza meno che mai: su KWin
> ridimensionare un output **ridispone le finestre dell'utente**. ⇒ Durante la sessione viva il
> comportamento resta quello scritto qui — si riscala la vista, il desktop non si tocca.
>
> ### ⛔⛔ E DAL 17 AGOSTO 2026 NON C'È PIÙ NEMMENO L'INTERRUTTORE — vedi **§5.1-bis**
>
> L'inseguimento della finestra stava dietro `?adatta=segui`, spento di suo (I6). **È uscito dal
> prodotto**: *«non voglio mettere delle eccezioni nel progetto»*. ⇒ Questa voce torna a valere
> come fu scritta l'8 agosto, **senza eccezioni**, e i valori di `?adatta=` restano due:
>
> | `?adatta=` | che cosa fa |
> |---|---|
> | *assente* (predefinito) | chiede la tela **all'attacco e al riattacco**, e basta |
> | `no` | ⛔ non la chiede mai: è la pagina di prima del 15 agosto, e serve al **confronto A/B** che il giudizio dell'utente richiede (`LEZIONI.md` §7.3) |
> | ~~`segui`~~ | ⛔ **tolto il 17 agosto 2026**. Un indirizzo vecchio che lo porta vale il predefinito e non riaccende niente — sorvegliato da `banchi/06-b37-modi.py` |
>
> ⚠ Si legge da `?` **e** da `#`, come `video` e `disposizione`.

Le tre ragioni, e la terza è quella che ha deciso:

1. su KDE 6.3.6 — cioè Debian Trixie — **non si può** ridimensionare: la misura sta nella riga
   di comando di KWin (`--virtual --width W --height H`), il modo è `const`, e
   `stream_virtual_output` risponde `Could not find output` per ogni misura `[M]` 8 ago;
2. la correzione a monte esiste (`kwin!7932`, traguardo 6.8, ottobre) ma **Debian stabile non
   aggiorna Plasma**: 6.3.6 per tutta Trixie (Forky, ancora testing, ha già 6.7.2 `[R]` 4 ott). Il ripiego non è un'impalcatura temporanea, è un
   percorso di codice da mantenere per anni;
3. ⛔ **e anche dove funziona, fa una cosa peggiore**: ridimensionare un output ridispone le
   finestre dell'utente `[R]`. Su KWin la chiave del `PlacementTracker` contiene la geometria
   dell'output, quindi tornando a una misura già vista le finestre vengono **teleportate**
   indietro. La versione «giusta» scompiglia il lavoro; quella «rotta» lo lascia fermo.

**Conseguenze:** ⛔ *superate da §5.1-bis (17 ago 2026), e riconfermate dall'utente il 2 ottobre 2026 dopo
la sua prova a mano: il ridimensionamento a caldo non resta nemmeno come funzione facoltativa; la
misura nuova si prende solo ricollegandosi. Le tre righe sotto restano come cronaca.*
- il ridimensionamento del compositore esce dal percorso critico e resta come funzione
  facoltativa («adatta il desktop a questa finestra»), spenta dove il compositore non la sa
  fare, **con la ragione dichiarata** (`CODER.md` §4.2);
- quando si scriverà, si scriverà **nella forma della negoziazione PipeWire** — decisione già
  presa in `STUDI.md` §kde §8.2 — perché è una strada sola per GNOME, wlroots e KDE 6.8, e su KDE si
  accende da sé all'aggiornamento;
- ⚠ e includerà la **guardia obbligatoria** `if (misura_attuale == misura_richiesta) return;`
  (`STUDI.md` §kde §8.2-bis): senza, la rinegoziazione si morde la coda. Il difetto **non si vede su
  Trixie** e compare il giorno dell'aggiornamento a 6.8, quando nessuno lo sta più cercando.

### 5.1-bis ✅ ⛔⛔ Il ridimensionamento a caldo **esce dal prodotto** — 17 agosto 2026

*«Ecco la mia decisione. Non voglio mettere delle eccezioni nel progetto. Il dynamic resolution
esce dalle funzionalità di Remotix.»*

**Quel che esce:** cambiare la misura della tela **mentre la sessione è viva**. L'interruttore
`?adatta=segui`, il fondo `TELA_FONDO_MS`, `tela_forse_chiedi()` e il ramo del `resize` sono tolti
da `src/pagina.html`.

**Quel che resta, ed è la logica di prima:** ⭐ *la tela nasce con la dimensione della finestra del
client, nel momento della nascita **o del riattacco** della sessione* — §5.0-sexies, intatta. Da lì
in poi il desktop non si tocca più: il client riscala (§5.1, che torna a valere **senza eccezioni**,
com'era scritta l'8 agosto).

#### Perché — e la ragione non è il codice, è il prodotto

⛔ **L'eccezione era misurata, non temuta.** Su Mutter cambiare la tela a caldo costa `[M]` **6 ms**
e funziona. Su KWin ≤ 6.7.4 — cioè **Debian Trixie, e fino a Forky** — `stream_virtual_output`
risponde **`Could not find output` a ogni misura** (`[M]` 8 agosto 2026, cinque misure provate,
`VirtualBackend` non ridefinisce `createVirtualOutput()`). ⇒ Tenerla avrebbe voluto dire **un
prodotto che fa una cosa diversa a seconda di chi ci ospita**, con un ramo condizionato al
compositore e un banco per ciascun ramo.

⚠ **E non basta aspettare che KDE si aggiorni.** `kwin!7932` «Resizable Virtual Monitors» è unita
(29 luglio 2026, milestone 6.8, **14 ottobre 2026**) e nella nostra stessa forma — negoziazione
PipeWire — ma:

- `[R]` verificato il **17 agosto 2026** su invent.kde.org: l'ultimo tag è ancora **v6.7.4**,
  `Plasma/6.8` non esiste;
- Debian stabile non aggiorna Plasma ⇒ l'eccezione sarebbe rimasta **per anni**, non per due mesi;
- ⛔ e **anche dove funziona fa un danno**: ridimensionare un output **ridispone le finestre
  dell'utente** (la chiave del `PlacementTracker` contiene la geometria dell'output, quindi tornando
  a una misura già vista le finestre vengono teleportate). La versione «giusta» scompiglia il
  lavoro; quella «rotta» lo lascia fermo.

✅ **Riconfermata il 4 ottobre 2026, guardando Forky** (Debian 14, Plasma 6.8 previsto): KWin
ridimensionabile non riapre la voce. *«il dynamic resize non è una funzionalità così importante,
le cose grosse adesso le abbiamo e funzionano bene, anche su Android»* (l'utente).

#### ⚠ E la richiesta dell'utente che questa decisione ha superato

*17 agosto 2026, prima della decisione*: **«l'utente trascina i bordi e rilascia, e solo allora
avviene il ridisegno»**. Era attuabile, e la nota tecnica resta perché il giorno in cui qualcuno la
riproponesse la ritroverebbe uguale:

> Il bordo della finestra **non è nel documento**: lo trascina il gestore delle finestre. Alla
> pagina non arriva né `mousedown`, né `mouseup`, né `pointerup`, e un evento «il ridimensionamento
> è finito» **non esiste in nessun motore**. ⇒ «Ha rilasciato» si può solo **dedurre** — «sono
> passati N ms senza un altro `resize`» — ed era esattamente ciò che il fondo di 250 ms faceva.

**Conseguenze:**
- ⛔ **le bande nere restano possibili, e sono il comportamento dichiarato**: se dopo l'attacco la
  finestra cambia forma (ridimensionata, o il tablet **ruotato**), le proporzioni non combaciano più
  e il client riscala impaginando — `SPECIFICHE.md` §6.2, «si impagina, non si stira». Non è un
  difetto da curare: è la scelta;
- ⭐ **`ADATTA_TELA` resta nel protocollo** (`RCP.md` §7.1) e la catena server resta viva **per
  intero** — la usa l'attacco, e la usa il **riattacco**, dove il palco esiste già con la misura di
  un altro dispositivo. ⚠ Chi la togliesse credendola figlia dell'inseguimento romperebbe il
  riattacco;
- `banchi/06-b37-modi.py` cambia mestiere: da «i tre modi di `?adatta=`» a **guardia contro il
  ritorno** — 0 richieste in tutti i modi, `?adatta=segui` compreso, che ora è solo un segnalibro
  vecchio;
- `banchi/06-b37-voce.py` V4 cambia domanda: da «la voce si spegne?» a «la funzione è davvero
  uscita?». ⚠ V1–V3 restano: la voce spenta serve ancora, perché la tela si chiede a ogni riattacco
  e la ripetizione su `NON_ORA` è viva;
- ⛔ e **la fase 11 (KDE) non eredita più niente da decidere qui**: il ripiego dichiarato di §6.3 —
  `COMPOSITORE_INCAPACE`, il client riscala — diventa il comportamento **normale** di tutti,
  non il ramo povero di uno.

### 5.2 🔸 ⛔ ~~Il codificatore lavora alla misura della finestra~~ → **no: lavora alla misura della tela**

> ⛔ **Corretta il 9 agosto 2026, scrivendo `RCP.md` §6.2.** Questa voce diceva: *«Regalo che
> arriva gratis da 5.1: finestra piccola ⇒ meno pixel da codificare ⇒ la stessa banda rende di
> più»*. **Contraddiceva §5.0-ter**, che è a due voci di distanza e dice il contrario — *«il server
> continua a codificare la tela intera e il client la rimpicciolisce»* — mettendo l'ottimizzazione
> **volutamente fuori dal modello**, come `[?]` da misurare prima.
>
> **Vince §5.0-ter**, e non per anzianità: è quella che regge insieme al resto. `SPECIFICHE.md`
> §6.1 dice che durante la sessione **è il client a riscalare**, e §6.3 dice che il ripiego su KDE
> *«non costa una riga in più, perché è lo stesso codice del punto durante la sessione»* — cioè la
> riscalatura nel client. Se il server codificasse alla misura della finestra, quel codice non
> esisterebbe e il ripiego costerebbe eccome.
>
> ⚠ **Il regalo non era gratis**: cambiare la misura codificata a ogni trascinamento del bordo
> significa rinegoziare il codificatore — e con `DECISIONI.md` §5-bis.0 il bordo si trascina
> **dieci volte al giorno**, perché su DeX la finestra è ridimensionabile. Era una `[?]` travestita
> da conseguenza, cioè la forma d'errore **E5** di `REVIEWER.md`.

**Quel che vale adesso**: il server codifica alla misura della **tela**, il client riscala. Il
messaggio `VISTA` di RCP esiste lo stesso e serve a scegliere **quanti bit spendere**, non quanti
pixel produrre; e l'intestazione del fotogramma porta la misura come campo, così che il giorno in
cui §5.0-ter venisse chiusa **il protocollo non cambi** (`RCP.md` §6.2, §7.1).

### 5.3 🔸 Il prezzo di 5.1, dichiarato

Tela 1080p vista da uno schermo 4K = desktop ingrandito, quindi morbido. Ingrandire non
inventa dettaglio. La via d'uscita è la voce «adatta il desktop», ed è il motivo per cui la
misura iniziale della tela conta — vedi la domanda aperta §7.1.

---

### 5.4 ✅ ⭐⭐⭐ La tela visibile si dipinge con **`bitmaprenderer`**, non con la tela 2D — 17 agosto 2026

**Deciso sul giudizio dell'utente** — *«NIENTE ARTEFATTI!»* — dopo due giorni di caccia ai
**blocchi rettangolari da 64×192** che vedeva nelle zone ferme.

⛔ **La causa non era nostra, ed è fuori dalla portata di qualunque banco che rilegga i pixel**: la
`<canvas>` **2D** riceve i pixel giusti e si rompe **andando allo schermo**. Le prove, una per
imputato, stanno in [`fasi/06-la-tela-e-la-vista.md` §4.9](fasi/06-la-tela-e-la-vista.md) —
cattura pulita, codificatore pulito (0 superblocchi rovinati su 600), `copyTo` pulito, `getImageData`
**0 su 180 000** — ⛔ **e la stessa tela fotografata col cellulare che mostra i rettangoli**.

⇒ ⭐ **`getImageData` legge il magazzino, non lo schermo.** Un banco che rilegge la tela è verde
**per costruzione**, e per due giorni ha detto che andava tutto bene.

**La cura**: `createImageBitmap()` + `transferFromImageBitmap()` su un contesto **`bitmaprenderer`**,
che il magazzino 2D non ce l'ha. ⚠ Non è un'ottimizzazione e non è un interruttore: è **la** strada
di disegno del prodotto (`niente eccezioni`, §0).

**Che cosa cambia nel prodotto, e che cosa no:**

| | |
|---|---|
| ⛔ **le due tele 2D spariscono** | oggi il fotogramma passa da `deposito_p.drawImage(f)` **e poi** da `pennello.drawImage(deposito)`: due copie e due magazzini |
| ⭐ **il deposito non serve più** | `transferFromImageBitmap` **dimensiona la tela da sé**, e al ridimensionamento della finestra il contenuto **resta**: la ragione per cui il deposito esisteva (§5.1, il nero fino al fotogramma dopo) cade da sola |
| ⭐ **il cursore non è toccato** | è un cursore **CSS**, non è dipinto sulla tela ⇒ la tela visibile non deve **comporre** niente |
| ⚠ **il centraggio si fa col CSS** | quando la finestra è più larga dell'immagine. Le bande erano già **fuori** dal buffer (§5.0-sexies), quindi non si perde una misura |
| ⚠ **e il costo va misurato** | `createImageBitmap` è **asincrona**: entra nel percorso del ritardo, che è il numero per cui esiste la fase 3. `[?]` finché non c'è la misura |
| ⛔ **il ripiego si dichiara** | se `getContext("bitmaprenderer")` non c'è, si torna alla tela 2D **e lo si scrive nel registro** — `CODER.md` §4.2. Non è un'eccezione per compositore: è una capacità che manca |


---

## 5-bis. L'input

### 5-bis.1 ✅ Il puntatore lo disegna il client, non il desktop

*8 agosto 2026, proposta dall'utente.*

Il dito trascina un puntatore **disegnato dal client**; un tap fa il clic sinistro sulla
posizione del puntatore, un tap a due dita il destro. Non è il «tocco diretto», dove il dito
è il puntatore: è il trackpad, e si vede dove si sta per cliccare **prima** di cliccare.

**Tre problemi diversi che questa scelta chiude insieme:**

1. ⭐ **la latenza percepita.** Il puntatore si muove alla velocità del dito, non a quella
   della rete. Su un collegamento mobile con 150 ms di ritardo è la differenza fra usabile e
   frustrante — e pesa più dei fotogrammi al secondo, che è la grandezza che di solito si
   guarda;
2. **le scie e le posizioni vecchie** del puntatore, che nascono proprio dal fatto che il
   puntatore viaggi *dentro il video* e arrivi in ritardo;
3. **la precisione.** Un dito è largo ~10 mm, i bersagli di un desktop ne misurano ~4, e nel
   tocco diretto il dito **copre il bersaglio** mentre lo si cerca. In più il passaggio del
   puntatore — da cui dipendono suggerimenti e menu — esiste solo se un puntatore c'è davvero.

### 5-bis.2 🔸 Il cursore non deve MAI essere dentro l'immagine catturata — e va verificato

Discende da 5-bis.1: se lo disegna il client e c'è anche in quel che arriva, se ne vedono
**due**. v1 aveva incontrato il problema tre volte senza collegarle, e la cura è la sua:
*«non nasconderlo: renderlo invisibile»* — un tema con un cursore 1×1 ad alfa zero.

| Desktop | Il cursore è nella cattura? | Il canale della cura |
|---|---|---|
| GNOME / Mutter | **no**, lo esclude di suo (`inhibit_cursor_overlay`) | ⚠ e se servisse, **non** `XCURSOR_THEME`: Mutter non la legge, legge `org.gnome.desktop.interface cursor-theme` |
| KDE / KWin `--virtual` | **sì** `[M]` — niente piano cursore ⇒ dipinto nel framebuffer | `XCURSOR_THEME` (+ `XCURSOR_SIZE`, che KWin pretende) |
| wlroots — XFCE, LXQt | **sì, sempre** su headless; `overlay_cursor` non lo toglie, lo **forza software** | `XCURSOR_THEME`; su labwc `XCURSOR_SIZE` non è obbligatoria |

⛔ **La trappola, e va verificata invece che sperata**: su wlroots un tema che carica **zero**
cursori fa ripiegare la libreria su un tema **incorporato e visibile** — cioè due puntatori,
per un ripiego silenzioso (`REVIEWER.md` E2). Serve almeno un cursore valido, `index.theme`
**senza `Inherits=`**, e i dieci nomi che labwc chiede. E l'esito si **controlla dopo l'avvio
della sessione**: che il tema sia stato scritto non è che sia stato caricato.

*Il posto dove metterlo c'è già: l'ambiente della sessione si compone da zero, una variabile
per volta (`CODER.md` §4.5) — quindi la cura sta nel programma e non in un file, come vuole I7.*

### 5-bis.0 ✅ Su Android l'uso primario è **Samsung DeX**, e il tocco è il ripiego

*9 agosto 2026. «DeX assolutamente. È l'uso primario che faccio quando uso android perché la
verità è che usare certi programmi con il touch anziché nel modo classico è un ripiego di
emergenza, non la normalità.»*

⛔ **Ribalta la priorità con cui era stato progettato l'input Android**, che era tutto attorno al
telefono in mano — cioè al caso che l'utente quasi non usa.

| | Prima | Adesso |
|---|---|---|
| mouse e tastiera fisici (5-bis.8) | un passeggero | **la strada principale** |
| i sette gesti (5-bis.3) | il modello di input | **il ripiego d'emergenza** |
| ridimensionare la finestra (§5.1) | un caso limite | **quel che si fa di continuo** |

Con DeX il telefono pilota uno schermo esterno con mouse e tastiera veri: la tela nasce di forma
**desktop** e non di forma telefono, e la finestra si trascina.

⭐ **Tre decisioni ne escono rafforzate, non indebolite:**

1. **il puntatore disegnato dal client** (5-bis.1) era giusto col dito; con un mouse vero diventa
   non negoziabile — un puntatore che insegue la mano mentre si lavora «nel modo classico» è la
   differenza fra usarlo e chiuderlo;
2. **il ridimensionamento che non tocca il compositore** (§5.1) passa da scelta prudente a scelta
   obbligata: se trascinando il bordo dieci volte al giorno le finestre *dentro* la sessione si
   rimescolassero, il prodotto sarebbe inservibile. Era stato deciso per il muro di KWin; si
   scopre che era giusto anche per l'uso vero;
3. **la regola sui modificatori di comando** (5-bis.6) era una precisazione; lavorando col
   classico diventa **portante**, perché le scorciatoie sono metà del lavoro.

⭐ **E una buona notizia sul costo**: se l'uso primario è DeX, il client Android somiglia molto più
a quello Linux di quanto previsto — stesso modello di interazione, diverso solo nello stack di
decodifica. Riduce il rischio segnalato in §0.3 spostando Android in fondo: il protocollo non è
stato progettato per il client sbagliato, perché i due client si somigliano.

> ⭐ **Confermata e resa più forte dal 9 agosto 2026 (§1.6).** La decisione resta intera — l'uso
> primario su Android è DeX, il tocco è il ripiego — e cambia solo che il programma è **il browser
> su DeX** invece di un'applicazione nostra. ⚠ Da cui una domanda nuova che non c'era, e che va
> alla sonda: **su DeX, in una finestra ridimensionabile, il browser dà `Pointer Lock` e le
> scorciatoie?** Senza il primo si vedono due puntatori (5-bis.8), senza le seconde metà del lavoro
> se ne va nel browser invece che nella sessione.

### 5-bis.0-ter ✅ L'emulatore Android è banco di lavoro, non strumento di misura

*9 agosto 2026. «Per android forse dovremmo ricorrere a degli emulatori (che entrerebbero a far
parte dell'ambiente di sviluppo).»*

Accettato: SDK, emulatore, `adb` e il collegamento al telefono entrano nell'ambiente, e si mettono
già alla **fase 0** perché la sonda della fase 2 li richiede.

⚠ **Corretto lo stesso giorno, dopo che l'utente ha chiesto di cercare meglio.** La prima
stesura diceva che DeX «sull'emulatore non esiste»: **è falso**. Esiste il **Desktop AVD**
(profilo «13.5" Freeform», da Android 11; la versione Android 13 aggiunge scorciatoie da tastiera
e supporto mouse), e **Samsung stessa documenta l'emulatore per DeX** — *«If you don't have the
DeX Station, you can test your app resize behavior in Android Studio using Android Virtual
Device»*, a 160 dpi e 1080×1920. Il modello di interazione che ci interessa **è testabile lì**, ed
è gran parte delle fasi A1 e A3. Samsung avverte però che l'emulatore **simula, non replica**.

⛔ **Il confine resta, ma è più stretto e più netto**: *sull'emulatore si sviluppa, non si misura.*
**Nessun numero di questo progetto viene dichiarato su un emulatore.** Quel che non dà è la
**decodifica in hardware** — il suo MediaCodec non è il silicio del telefono, e `[?]` non si è
riusciti a stabilire che esponga un decodificatore HEVC hardware — più il ritardo vero, la
batteria e la rete che cambia.

⚠ È `REVIEWER.md` **E10**, *una prova verde sul client sbagliato*: un emulatore che dice «funziona»
mentre il telefono no è un banco verde col difetto vivo — la forma che a v1 è costata di più, con
una correzione scritta su un banco che non riproduceva il difetto e spedita all'utente, **che ha
peggiorato le cose**.

**Il telefono vero è lo strumento di misura; l'emulatore è il banco di lavoro.**

> ⛔ **Decade quasi per intero il 9 agosto 2026, con §1.6**: non c'è più un'applicazione Android da
> costruire, quindi non servono né SDK né APK né Desktop AVD — **il banco di lavoro è il browser
> del portatile**, che è più comodo di qualunque emulatore.
>
> ⭐ **Ma la riga che conta sopravvive parola per parola, e vale ancora di più**:
> *«nessun numero di questo progetto viene dichiarato su un emulatore»* diventa **«nessun numero si
> dichiara su un browser che non sia quello del dispositivo vero»**. Un Chrome su portatile che
> decodifica HEVC in hardware **non dice niente** del Chrome del telefono: è la stessa forma
> d'errore **E10**, con un travestimento nuovo.

### 5-bis.0-bis ✅ RDM è un riferimento da cui **ispirarsi**, non un prodotto da rifare

*9 agosto 2026. «Ora noi non dobbiamo rifare RDP e/o RDM, ma secondo me trarne ispirazione sì.»*

⚠ **In v1 RDM aveva un ruolo diverso**: era il **client da servire** — *«se non funziona qui, non
funziona»* (`fondamenta/documenti/client-android.md` §1.2). In V2 il client lo scriviamo noi, quindi
cambia mestiere: da **vincolo** a **riferimento**.

⛔ **E il confine è netto, perché RDM è proprietario** (Devolutions,
`com.devolutions.remotedesktopmanager`): si studia **come si comporta e come si sente all'uso**,
mai come è fatto dentro. La fonte migliore non è comunque il codice: è l'utente, che lo usa tutti
i giorni.

⭐ **Che cosa se ne prende, e viene da una frase sola**: *«funziona bene sia con interfaccia mobile
sia in modalità desktop»*. Non è il video che si adatta — sono **due interfacce**, e
l'applicazione sceglie da sé quale mostrare.

🔸 Da cui, per il nostro client Android: **una sola applicazione, due interfacce**, e il passaggio
è **automatico sul contesto** — schermo esterno e mouse collegati, oppure telefono in mano — non
un'impostazione che l'utente deve andare a cercare. È la forma che le fasi **A3** (il modo
classico) e **A4** (il tocco) hanno già preso.

> ⭐ **Sopravvive intatta al 9 agosto 2026 (§1.6), e diventa più facile**: «una applicazione, due
> interfacce» è **una pagina, due disposizioni**, e il passaggio automatico sul contesto è la cosa
> che una pagina sa fare meglio di qualunque altra tecnologia — si guarda se c'è un puntatore fine
> e quanto è grande la finestra, non «è Android o è Linux». ⚠ La sostanza però non cambia: **due
> disposizioni vere, non una che si stira**, ed è la lezione che si prende da RDM.

**Che cosa invece NON se ne prende:**

| | Perché |
|---|---|
| l'essere un **gestore di connessioni** — RDP, VNC, ARD, SSH, FTP e una cinquantina d'altro | è un pregio per loro e un fuori scope per noi: REMOTIX è un prodotto solo, e `SPECIFICHE.md` §12 esclude la compatibilità con altri protocolli |
| la sua **scelta di codec** (RemoteFX Progressive) | era ingegneria giusta *per RDP e per un telefono senza decodifica hardware*. Noi puntiamo su HEVC in hardware — ⚠ e se la sonda della fase 2 dicesse no, è **questa** la riga da rileggere |

### 5-bis.3 ✅ Il ventaglio dei gesti — **il ripiego, non la strada principale**

*9 agosto 2026, confermati tutti e sette. ⚠ E ridimensionati lo stesso giorno da 5-bis.0: su
Android l'uso primario è DeX, con mouse e tastiera veri. Questi gesti servono al telefono in
mano, che è il ripiego d'emergenza — restano necessari, ma non sono la cosa da azzeccare per
prima.*

| Gesto | Effetto |
|---|---|
| 1 dito trascina | muove il puntatore |
| 1 dito tap | clic sinistro |
| 2 dita tap | clic destro |
| 2 dita trascina | rotella / scorrimento |
| tap-e-mezzo (tap, poi premi e trascina) | trascinamento e selezione |
| 3 dita tap | clic centrale |
| pizzico | ingrandisce la **vista** del client, non l'applicazione |

⚠ Il *tap-e-mezzo* non è un lusso: senza, non si sposta una finestra e non si seleziona del
testo. Tap e trascinamento a due dita non si confondono — un tap è breve e fermo.

> ⭐ **E con quale riserva sono stati confermati**, che vale più della tabella: *«tanto poi sono
> sicuro che su alcune specifiche ci torneremo quando avremo il sistema funzionante sotto
> mano»*. È `LEZIONI.md` §7.3 applicata ai gesti, e sui gesti vale doppio — un gesto non si
> giudica leggendolo, si giudica usandolo. Questa tabella è quindi un **punto di partenza
> dichiarato**, non un impegno: chi la trova diversa fra sei mesi non ha trovato un difetto.

### 5-bis.3-bis ✅ ⭐ La barra porta **un bottone solo**: `Ctrl+Alt+Canc`

*14 agosto 2026, deciso dall'utente davanti alla misura della fase 4.*

⛔ **Il fatto che ha prodotto la domanda, ed è `[M]`** (`fasi/rapporti/F4-A9-scorciatoie.md`): sei
combinazioni **non arriveranno mai** al desktop remoto — `Super`, `Super+D`, `Alt+Tab`, `Alt+F2`,
`Alt+F4`, `Ctrl+Alt+Canc`. ⚠ E non è un limite del browser: **le prende il compositore del client**,
e **nessuna API le riprenderà mai**. L'unico modo di darle è un bottone a schermo — che però toglie
pixel all'immagine del desktop.

**Scelto: uno solo.** ⛔ E la ragione per cui è quello e non un altro è di natura diversa dal gusto:
senza `Ctrl+Alt+Canc`, **in una sessione bloccata l'utente non entra più** — è l'unica delle sei che,
mancando, lo lascia **fuori** invece che scomodo. `SPECIFICHE.md` §7.3-bis la chiama *«un requisito,
non un ripiego di fortuna»*, e tre riferimenti maturi su tre lo fanno.

⚠ **Gli altri cinque restano scritti e spenti**, con la loro ragione accanto: la scelta è di gusto e
si rivede **guardandola**, non leggendola (`LEZIONI.md` §7.3, la stessa riserva con cui l'utente ha
confermato i sette gesti). ⛔ Accenderne uno costa **una riga**.
⛔ **E spento vuol dire NON DISEGNATO**, non «disegnato e inerte»: un bottone che c'è e non fa niente
è peggio di un bottone che non c'è. Le cinque combinazioni restano però **nella tavola delle
dichiarate**, dove l'utente legge che quella battuta se la tiene il suo computer — ⭐ perché
`SPECIFICHE.md` §7.3-bis vieta di **fingere** che siano arrivate, non di non offrirle.

---

### 5-bis.4 🔸 Il canale del cursore, e il suo compromesso

Il client deve sapere **che forma** disegnare: barretta sul testo, doppia freccia sui bordi,
mano sui collegamenti. Serve quindi un canale che porti **forma e punto attivo** quando
cambiano.

Il compromesso, accettato: la **posizione** è immediata perché locale, la **forma** arriva con
un giro di rete di ritardo. Muovendo in fretta sopra un bordo, la doppia freccia compare un
attimo dopo. È il verso giusto del compromesso — il ritardo di una forma non lo nota nessuno,
quello di una posizione lo notano tutti.

### 5-bis.5 🔸 Che cosa porta il canale di input

| | |
|---|---|
| puntatore **assoluto** | sì — ed è **l'unico** percorso del puntatore (vedi 5-bis.8) |
| ~~puntatore relativo~~ | ⛔ **tolto il 9 agosto**: era motivato con *Pointer Capture*, e la motivazione era sbagliata. Vedi 5-bis.8 |
| **scancode** | sì — tasti di controllo e tastiere fisiche |
| **Unicode** | sì, e su Android è la **strada principale** (vedi §7.10-bis) |
| **tocco multi-dito** | posto riservato, **non implementato** `[?]` |
| **stilo** (pressione, inclinazione) | fuori, per ora |

Il tocco nativo non entra perché non risolve la precisione, le applicazioni desktop lo
gestiscono male, e andrebbe verificato che l'EIS di Mutter e KWin espongano la capacità
«touch» — `libei` la prevede, che i due la offrano è `[?]`. Il **posto riservato** costa niente
adesso e fa risparmiare una riscrittura se un giorno servisse.

### 5-bis.6 ✅ Le lettere viaggiano come lettere, i tasti che non sono lettere come posizioni

*8 agosto 2026.*

| Che cosa | Come viaggia |
|---|---|
| lettere, numeri, segni — tutto ciò che si stampa | **come lettere** (carattere) |
| Invio, Tab, Esc, frecce, F1-F12, Ctrl, Alt, Maiusc, Super | **come posizioni** — non sono lettere, e stanno nello stesso posto su ogni tastiera |

**Il problema che questa scelta scioglie**, ed è quello che l'utente ha isolato da sé: una
tastiera fisica non manda lettere, manda **posizioni** — il tasto a destra della L dice «tasto
39», ed è il desktop a decidere se significa «ò» (disposizione italiana) o «;» (americana). Se
sul filo viaggiassero le posizioni, un client con tastiera americana attaccato a una sessione
italiana produrrebbe **le lettere sbagliate**: è il difetto classico di ogni desktop remoto.

Facendo viaggiare le lettere, la disposizione del *client* la applica il sistema del client, e
la nostra sessione non deve indovinare niente. Vale per **entrambi** i client, non solo per
Android — dove però è obbligatorio comunque, perché una tastiera Android non ha posizioni:
è un IME che produce testo.

⛔ **La precisazione che manca alla riga di sopra, aggiunta il 9 agosto: `Ctrl+C` non è testo,
è un comando.** Mandato come «lettera c», l'applicazione remota riceverebbe una c da scrivere
invece di una copia da fare. Quindi la regola completa è:

> Una battuta viaggia **come lettera** quando sta scrivendo del testo. Quando è tenuto premuto
> un modificatore **di comando** — Ctrl, Alt, Super — viaggia **come posizione**, perché in quel
> momento non è una lettera. Maiusc e AltGr non contano: quelli servono a *fare* la lettera, e
> restano dentro il percorso del testo.

⭐ **E questo dà una seconda ragione a 5-bis.7**, che era stata decisa per un motivo diverso: le
scorciatoie viaggiano come posizioni, e le posizioni combaciano solo se le due disposizioni
sono la stessa. Su una tastiera tedesca la Z sta dove sulla nostra sta la Y — senza
rinegoziare la disposizione all'attacco, `Ctrl+Z` finirebbe su un altro tasto.

⚠ **Resta la sola raggiungibilità.** Se nella disposizione della sessione un carattere non
esiste su nessun tasto — un'emoji, un alfabeto diverso — non esce **niente**, e il server lo
**dichiara nel registro**: mai una lettera diversa, mai un silenzio (`LEZIONI.md` §1.8).

**In dote**: i modificatori non sono mai stati il problema e si emulano normalmente (per «A»:
premi Maiusc, premi 30, rilascia 30, rilascia Maiusc); la ripetizione non è nostra (wlroots
scarta i tasti ripetuti, a ripetere è l'applicazione); e la disposizione dichiarata dal client
— la «questione n.7» di v1 — non serve più per *interpretare*, solo per *scegliere* (5-bis.7).

### 5-bis.6-bis ✅ ⭐ Gli accenti composti e le tastiere asiatiche restano **fuori, dichiarati**

*14 agosto 2026, deciso dall'utente davanti alla misura della fase 4
(`fasi/rapporti/F4-A7-pagina-classico.md`).*

**Che cosa funziona già** `[M]`: la `à` italiana, perché sulla disposizione italiana **è un tasto
suo** e passa dal percorso di `LETTERA` come tutte le altre.

⛔ **Che cosa resta fuori**: i **tasti morti** (la `à` composta in due battute di una tastiera
francese o «US international») e l'**IME** (cinese, giapponese, coreano). ⚠ E resta fuori
**dichiarato**: la pagina lo scrive, e **non fa uscire una lettera diversa né tace** — che è la
regola di `RCP.md` §7.3 applicata al lato del client.

**Il prezzo che si è scelto di non pagare**, ed era previsto: per avere tasti morti e IME serve un
**elemento modificabile col fuoco sopra la tela** — cioè `STUDI.md` §web §1.2 C — e quell'elemento si mette
**fra il puntatore e l'immagine**: ⛔ il percorso con cui la pagina disegna oggi la freccia **andrebbe
rifatto**. ⇒ Costo certo e visibile, contro un guadagno che per l'utente di oggi è **zero**.

⚠ **E si riapre da sé il giorno in cui servisse una tastiera straniera**: il lavoro è dichiarato, non
perso. `LEZIONI.md` §2.4 — quel che cambia ciò che si vede sta dietro un interruttore finché
qualcuno non l'ha guardato.

---

### 5-bis.7 ✅ La disposizione si rinegozia all'attacco e al riattacco, come la risoluzione

*8 agosto 2026. «Per le tastiere vale il discorso delle risoluzioni: alla creazione della
sessione o re-attach viene rinegoziata anche la tastiera».*

Stessa forma di §5.0 — il client dichiara, la sessione si adegua — ma **con due differenze che
giocano a favore**:

1. **non costa niente di visibile.** Cambiare la misura dello schermo rimescola le finestre
   dell'utente e su KWin < 6.8 non si può proprio; cambiare la disposizione non sposta nulla,
   non riavvia la cattura, non si vede;
2. **e se fallisse, la degradazione è morbida.** Grazie a 5-bis.6 una disposizione vecchia non
   produce mai caratteri sbagliati — al massimo rende irraggiungibili un paio di accenti. Una
   misura vecchia, invece, la si vede per tutta la sessione.

`[?]` **Da misurare, due cose, e nessuna è urgente:** se il cambio di disposizione a sessione
viva riesca su tutti e quattro i desktop (la nascita è certa, il cambio a caldo no); e se
convenga dare alla sessione **più disposizioni insieme** — il sistema ne accetta fino a quattro
— per coprire il caso di chi passa da un telefono italiano a un portatile americano, che
sospetto sia raro ma non l'ha misurato nessuno.

> ### ⛔⛔ QUESTA DECISIONE NON È MAI STATA ATTUATA — `[M]` 16 agosto 2026, sottofase 6.2
>
> *Misurato sul prodotto vivo, utente `provat6`, porta 7721, con un testimone dentro la sessione
> grafica: la disposizione che il client dichiara in `ATTACCA` viene **convalidata**
> (`rcp.c:2013-2027`), **scritta nel registro** (`rcp.c` · `tratta_attacca()`), **e lì finisce**. Non arriva mai
> alla tastiera.*
>
> | scena | atteso se la decisione fosse attuata | `[M]` misurato |
> |---|---|---|
> | sessione `it`, riattacco dichiarando **`us`** | `è` e `ò` irraggiungibili | **`aèò\@a`** — identico a `it` |
> | sessione `it`, riattacco dichiarando **`de`** | `z` e `y` scambiate | **comportamento `it`** |
> | la **sessione** passa `it`→`de` a palco vivo | keymap riletta, `azy\a` | ⭐ **`azy\a`** — questo pezzo funziona: `ricambi_tastiera` 0→1, impronta della keymap `8315b8d9`→`d1c54543`, «[German]» |
>
> ⇒ ⭐ **Quel che regge è la metà difficile**: quando la disposizione **della sessione** cambia,
> Mutter distrugge e ricrea il dispositivo tastiera e `tastiera.c` rilegge la keymap nuova — le
> lettere escono giuste. ⛔ **Quel che manca è la metà facile**: nessuno prende la disposizione
> *del client* e la dà alla sessione. `input.c` · `leggi_regione()` passa `NULL` dove andrebbe la negoziata, e la
> riga `RIPIEGO DICHIARATO` di `tastiera.c` · `tastiera_apri_da_keymap()` **non compare in nessun giro** — cioè chi cercasse
> quella riga nel registro concluderebbe *«combaciano sempre»*, che è diverso da *«non ho
> guardato»*.
>
> ### ✅ E il 16 agosto 2026 l'utente l'ha CONFERMATA, messo davanti alle tre strade
>
> *Gli sono state poste come la scena che vive — «ti colleghi da un PC con tastiera diversa da
> quella della sessione: chi decide?» — con le tre risposte possibili: **comanda la sessione** (e
> si corregge la promessa di `SPECIFICHE.md` §7.3), **comanda il client** (e il server la applica),
> **sceglie l'utente** con una voce nella pagina. ⇒ Ha scelto la seconda: **comanda il client**.*
>
> ⇒ La decisione dell'8 agosto **resta in piedi e si attua adesso**, nella fase 6.
>
> ⚠ **E il prezzo dichiarato prima della scelta, che resta un prezzo**: la pagina **non può sapere**
> la disposizione fisica della tastiera di chi la guarda — la indovina dalla lingua dell'interfaccia
> del browser (`src/pagina.html:2585-2624`, `[?]` dichiarata lì dallo stesso codice), e fuori dalle
> lingue note **ripiega su `us`**. ⇒ Applicando quel nome alla sessione si cambia la tastiera vera su
> un **indizio**. ⭐ Il danno resta morbido per §5-bis.6 — le lettere viaggiano come lettere, quindi
> al massimo si spostano le **scorciatoie** e qualche accento — ⛔ ma la terza strada (l'utente
> sceglie) resta la cura vera del difetto, e il codice della pagina la nomina già come tale.

### 5-bis.8 🔸 Mouse e tastiera fisici collegati al telefono

*Domanda posta dall'utente il 9 agosto. La risposta è che il disegno già scelto li assorbe
entrambi, e in un caso lo semplifica.*

**Il mouse.** Android offre due modi: quello normale mostra **il cursore di sistema** e
consegna posizioni — inservibile per noi, perché si vedrebbero **due puntatori**. Quello giusto
è **Pointer Capture**: il client dichiara di gestirlo lui, il cursore di Android sparisce, e
arrivano **spostamenti** più tasti e rotella.

⭐ E lì si chiude da sé: **quegli spostamenti muovono lo stesso puntatore che muove il dito.**
Una freccia sola, due modi di spingerla; si stacca il mouse e si continua col dito senza che
cambi niente. È il dividendo di 5-bis.1 — avendo il puntatore in casa, non importa da dove
arrivi la spinta.

⛔ **E da qui la correzione a 5-bis.5.** Avevo messo il «puntatore relativo» fra le cose che il
protocollo deve portare, **motivandolo con Pointer Capture**: è sbagliato. Se il puntatore lo
disegna il client, è il client a fare i conti, e sul filo continua a viaggiare solo la
**posizione**. Un percorso in meno.

`[?]` Il relativo servirà semmai per un motivo diverso — le applicazioni remote che
**catturano** il puntatore (un programma 3D, un gioco) — e quel caso lo segnala il **server**,
non il client. Da riprendere se e quando si presenta.

🔸 **L'accelerazione la applica il client**, non il server: si regola dove sta la mano ed è la
stessa per qualunque sessione. Applicata da tutt'e due si sommerebbe, e il puntatore
diventerebbe imprevedibile.

**La tastiera.** Android la gestisce e consegna comunque **il carattere**, applicando la
disposizione impostata nelle sue preferenze: la regola di 5-bis.6 vale identica, e non importa
che la tastiera sia disegnata o di plastica.

---

## 5-ter. Gli appunti

### 5-ter.1 ✅ Solo testo, nei due versi

*9 agosto 2026. «Per la clipboard ho idea precisa: solo testo». «Clipboard bi-direzionale. Dal
server al client e viceversa».*

**Solo testo**: niente immagini, niente file, niente formati ricchi.

**Nei due versi**: si copia sul desktop remoto e si incolla sul dispositivo in mano, e
viceversa. ⚠ Corregge `SPECIFICHE.md` riga 28, che diceva «clipboard testuale **server-client**»
e si leggeva in un verso solo — mentre il verso client → server (copio un indirizzo sul
telefono, lo incollo nel browser remoto) è quello che si usa di più dei due.

**Perché è la scelta giusta e non una rinuncia**, scritto perché nessuno la riapra per
distrazione: il testo copre il 95 % degli usi, costa una manciata di byte, e non ha
negoziazione — una stringa è una stringa. Le immagini aprono invece una scatola intera:
quali formati, chi converte, e soprattutto **chi paga la banda** quando si copia una schermata
da 8 MB su un collegamento mobile che stiamo faticando a tenere a 480p (§3.1).

### 5-ter.2 🔸 Il codice c'è già, e copre tre desktop su quattro con un file solo

Fra le cose che sopravvivono alla morte di RDP, gli appunti sono le più intatte: muore solo il
canale RDP che li trasportava, non il modo di parlare col desktop.

| | Righe | Copre |
|---|---|---|
| `fondamenta/remotix-c/src/appunti_wlr.c` | 796 | **KDE, XFCE e LXQt insieme** — stesso protocollo (`zwlr_data_control_manager_v1`), e `STUDI.md` §xfce §8 lo dà per funzionante così com'è |
| `fondamenta/remotix-c/src/appunti_mutter.c` | 450 | GNOME, che ha una via sua |

### 5-ter.3 🔸 Di chi sono gli appunti cambia per desktop, e una trappola è già disinnescata

`LEZIONI.md` §3, domanda 14 — *«la clipboard di chi è?»*:

| | |
|---|---|
| **GNOME** | ⚠ **anche qui del compositore** — vedi la correzione qui sotto: è `MetaSelection`; della sessione remota è solo **la porta** (`EnableClipboard` sull'oggetto RemoteDesktop) |
| **KDE, wlroots** | del **compositore**: nessun permesso, e c'è anche se REMOTIX non c'è |

> ⛔ **Corretta il 9 agosto 2026**, leggendo `STUDI.md` §gnome §10, che lo aveva già scritto l'8 e che
> nessuno aveva riportato qui. Diceva: *«della sessione remota: sta sull'oggetto RemoteDesktop, si
> accende con `EnableClipboard`, e senza sessione non esiste»*. `[R]` Le prime due mezze frasi
> descrivono la **porta**, non la proprietà; l'ultima è **falsa**: la sponda X11 di Mutter è
> incondizionata nei due versi, senza un solo controllo sul fuoco.
>
> ⭐ **E la conseguenza è un regalo per la fase 7**: `xclip` funziona su GNOME **senza** una nostra
> sessione, quindi il banco degli appunti può usarlo come lato indipendente — invece di far
> parlare fra loro due pezzi nostri, che è ciò che `PIANO.md` §0.4 chiama non confermare niente.
>
> ⚠ **Tre trappole di Mutter, tutte `[R]` in `STUDI.md` §gnome §10**, che chi scrive la fase 7 legge lì e
> non qui: `DisableClipboard` è **a senso unico** (dopo, gli annunci non tornano più — non si
> chiama mai); la firma di `mime-types` è **asimmetrica** fra ingresso e uscita, e chi legge col
> tipo sbagliato ottiene `NULL` **senza errore**; e il gestore interno degli appunti tiene **un
> solo tipo MIME**.

⚠ **La trappola di GNOME, e perché non ci tocca più**: *«gnome-shell azzera la clipboard a ogni
blocco schermo: ci strappa la proprietà in silenzio»* (`STUDI.md` §gnome). Con §4.3 — il blocco è
nostro e quello dei desktop resta spento — il caso non si presenta. **Ma torna il giorno in cui
qualcuno rimettesse il blocco del desktop**, ed è un'altra ragione per cui quella decisione va
riletta e non data per scontata.

### 5-ter.4 ✅ «Testo formattato» è stato richiesto, e la decisione del 9 agosto REGGE

*17 agosto 2026, all'apertura del lavoro sugli appunti.* La richiesta diceva *«la copia
server↔client di **testo formattato**»*. ⛔ Contraddiceva §5-ter.1, che è **parola dell'utente del 9
agosto**: *«solo testo»*, niente formati ricchi.

**Chiesto prima di scrivere una riga, e l'utente ha scelto «solo testo semplice».** ⇒ §5-ter.1 non
si tocca.

⚠ **E il costo dell'altra strada era protocollare, non di fatica**: `RCP.md` §7.4 ha costruito i tre
messaggi **senza nessun campo che dichiari il tipo**, con la ragione scritta accanto — *«non esiste
perché non c'è niente da scegliere»*. Per l'HTML servirebbe quel campo, e `RCP.md` §9 vieta di
aggiungere campi a messaggi esistenti dentro una versione maggiore: **la finestra è chiusa dal 10
agosto 2026**. ⇒ Sarebbe stato **RCP/2**, più quattro documenti da correggere.

⭐ E v1 l'HTML lo portava (`fondamenta/remotix-c/src/scambio.c:56`, il formato registrato «HTML Format»):
non è una cosa impossibile, è una cosa **lasciata fuori di proposito**.

### 5-ter.5 🔸 La corsa fra `Ctrl+V` e l'annuncio: la richiesta ASPETTA, e i tasti non si ritardano

*17 agosto 2026, scrivendo il canale.* `SPECIFICHE.md` §9 nomina la corsa e rifiuta la cura del
riferimento con un numero: Xpra ritarda **ogni battuta di 100 ms**, e per noi *«sono due volte il
tetto del ritardo»*.

**La corsa**: l'utente batte `Ctrl+V` nel browser; i tasti e l'annuncio degli appunti partono
insieme su due canali diversi, e il desktop — ricevuto il `Ctrl+V` — chiede il testo **subito**.
⛔ La prima incollata di ogni testo nuovo tornerebbe vuota, e la seconda funzionerebbe.

⭐ **La sostituzione**: la richiesta di incolla **si mette in coda** invece di tornare vuota, e la
domanda al client parte quando l'annuncio arriva. Costa zero, e **non tocca un solo tasto**.

⏳ Ragionata, **non misurata**: la scena che la prova è quella dell'utente.

### 5-ter.6 🔸 Due fondi di tempo, e sono due perché i debiti sono due

| dove | quanto | che debito paga |
|---|---|---|
| ⛔ **nel figlio** | **4 s** | il debito verso **Mutter**: un `SelectionTransfer` senza risposta lascia appesa a tempo indeterminato l'applicazione che incolla, e l'utente vede **un desktop piantato** |
| ⚠ **nel padre** | **8 s** | che il **canale** non resti bloccato: senza, un client che non risponde una volta manda in coda tutte le incollate successive |

⭐ **E il fondo verso Mutter sta nel FIGLIO, non nel padre**: il padre può non avere nessun client
(la sessione sopravvive al client — I4), il client può sparire, il padre stesso può morire. Il
debito verso il compositore resta di chi ha la sessione.

⚠ I due numeri sono diversi **apposta**: coincidendo scadrebbero insieme, e un testo arrivato al
millesimo giusto non troverebbe più nessuno da servire da nessuna delle due parti.

### 5-ter.7 🔸 Uno stream per MESSAGGIO, non per trasferimento — dove §2.5 ammetteva due letture

`RCP.md` §2.5 dice *«uno stream **per trasferimento**»*. ⚠ Un trasferimento dalla parte del server è
fatto di due messaggi lontani nel tempo: l'annuncio adesso, il testo **se e quando** qualcuno chiede.

⇒ **Uno stream per messaggio**, perché si copia molto più spesso di quanto si incolli: tenere aperto
uno stream fra i due vorrebbe dire tenerlo aperto **per sempre** nella maggioranza dei casi, e §2.5
concede al server un numero finito di stream.

⭐ Si può fare perché a legare i messaggi di un trasferimento **non è lo stream**: è il campo
`trasferimento` (rilievo R1.11). ⭐ E il cliente di prova, leggendo **solo `RCP.md`**, ha fatto la
stessa scelta — la riga è ambigua, ma l'ambiguità non morde.

### 5-ter.8 ✅ Come una sessione locale — e il prezzo che Firefox impone

*21 agosto 2026, dall'utente, dopo la cura dell'incolla col mouse:*

> *«Voglio che sia chiara una cosa: l'esperienza dell'utente con REMOTIX dev'essere quanto più
> vicina possibile all'esperienza con una sessione grafica locale. Questo vale anche per la gestione
> della clipboard: niente trucchi, pulsanti strani o soluzioni tecniche che si allontanino da questa
> direttiva, quindi ctrl+v o usare il mouse per incollare i contenuti dev'essere assolutamente
> allineata al comportamento reale.»*

⛔ **È una direttiva, non una preferenza**, e vale oltre gli appunti: dove una cura richiede
all'utente di imparare qualcosa, la cura è sbagliata.

⇒ Da lì discendono tre cose, tutte misurate e tutte in vigore:

1. ⭐ **Incollare col mouse funziona**, cioè tasto destro dentro il desktop remoto e voce «Incolla»
   del menu dell'applicazione remota. `[M]` `banchi/07-b56`, 3 incollate su 3 per motore.
2. ⭐ **Collegarsi non cancella la clipboard del desktop.** `[M]` Prima la cancellava: `wl-paste`
   diceva `TESTO-CHE-ERA-GIA-NEL-DESKTOP` prima e `«»` dopo.
3. ⭐ **Non esiste nessun pulsante nostro**, nessun interruttore, niente da spiegare.

### 5-ter.9 🔸 E su Firefox l'incolla col mouse costa **un clic in più** — accettato

*21 agosto 2026: «ok, va bene così».*

⛔ Quando si incolla col menu del desktop remoto, sulla pagina non nasce nessun evento: quel menu è
dipinto nel video e a incollare è un'applicazione dall'altra parte del filo. ⇒ L'unico modo che la
pagina ha di sapere che cosa hai copiato è **leggere la clipboard in quell'istante**, e lì decide il
browser:

| | Chrome | Firefox |
|---|---|---|
| che cosa chiede | la concessione della clipboard **una volta sola**, come per il microfono | ⛔ il suo bottoncino **«Incolla», ogni volta** — `[M]` anche reincollando lo stesso testo |

⚠ **Quel bottoncino è di Firefox, non nostro**, e dalla pagina non si può togliere: l'unica cosa che
lo spegne è una preferenza di prova, che in un prodotto non entra.

⇒ **Si accetta e si dichiara**, invece di rinunciare all'incolla col mouse su Firefox. ⏳ E resta
aperta la sola strada che lo toglierebbe davvero — **un componente aggiuntivo per Firefox** — da
decidere alla fase 13, quando si decide come REMOTIX si installa. ⚠ Non si fa prima: cambia *che
cosa si installa*, e REMOTIX smetterebbe di essere «apri il browser e vai».

⭐ **Il `Ctrl+V` non costa niente su nessun motore**, ed è la strada che la maggioranza userà.

---

---

## 5-quater. L'audio

*Aperto il 17 agosto 2026. ⛔ Fino a quel giorno **questo capitolo non esisteva**: le scelte
dell'audio stavano sparse fra `SPECIFICHE.md` §10, `RCP.md` §5.3 e l'invariante I5 — cioè in tre
posti e in nessuno. Il documento di fase lo aveva dichiarato all'apertura.*

### 5-quater.1 🔸 Opus passa da `libavcodec`, non da `libopus`

`[M]` 17 agosto 2026: `libavcodec` 61.19.101 sulla macchina di prova **è già collegato a
`libopus.so.0`** e dichiara l'encoder `libopus`. ⇒ Il `Makefile` **non cambia** e non si aggiunge
un pacchetto a **due** ambienti di costruzione (il contenitore del portatile e il `devroot` del
server), dove `opus.pc` non c'è.

⚠ **Il prezzo, dichiarato**: un `AVPacket` per blocco, cioè 50 allocazioni al secondo. È meno del
prezzo di una dipendenza da installare due volte e ricordare per sempre (`LEZIONI.md` §2.5-bis).

### 5-quater.2 🔸 Il bitrate di Opus: **96 kbit/s**

Derivato, non deciso dall'utente. È la banda a cui Opus è trasparente per la musica secondo la sua
documentazione `[S]`; `[M]` un blocco da 20 ms misura **241-439 byte**, che sta nel datagram con
margine largo. ⏳ **Da rivedere il giorno in cui qualcuno giudichi la qualità**, non prima.

### 5-quater.3 🔸 Il cuscino di riproduzione: **250 ms**, e non è un numero libero

⛔ **Era 60 ms, ed era sbagliato**: scelto guardando il tetto del **video** (50 ms, `CODER.md`
§1-bis) — cioè misurando l'audio col metro di un'altra cosa. Il riferimento
(`gnome-remote-desktop`) ne tiene **300** (`STUDI.md` §gnome §11).

**La ragione per cui 60 non regge**: il video si decodifica e si dipinge **sullo stesso thread**
che programma l'audio. Quando quel lavoro supera il cuscino la riproduzione si è già svuotata, e
**ogni riarmo è un buco**.

⚠ **Il prezzo è dichiarato**: 250 ms fra quel che si vede e quel che si sente. ⛔ E se un giorno
desse fastidio, **la cura non è stringerlo**: è togliere l'audio dal thread principale con un
`AudioWorklet`. ⏳ L'utente ha detto *«risolto»*, non *«e il ritardo va bene»*: quel giudizio manca.

### 5-quater.4 ✅ ⭐⭐ Un blocco che non parte si RIMANDA, non si butta — e a decidere è la coda

*17 agosto 2026, dopo che l'utente ha detto sette volte «fa schifo» su un banco verde.*

`RCP.md` §6.3 dice *«nessuna ritrasmissione, nessun riordino»*, ⛔ **e non dice «si butta al primo
rifiuto»**: quella era una lettura mia, e valeva il **50 %** dell'audio.

| | |
|---|---|
| ⛔ **quel che NON si fa** | buttare un blocco perché il pacer ha detto «non adesso»: quel blocco parte qualche centinaio di microsecondi dopo, e buttarlo è **un buco garantito** |
| ⭐ **quel che decide** | **la coda**: otto blocchi = 160 ms di Opus. Oltre quelli il più vecchio non serve più a nessuno, ed **è lì** che §6.3 morde |
| ⭐ **e si spediscono più blocchi per pacchetto** | un pacchetto è **1452 byte**, un blocco di Opus **230**: ce ne stanno sei. ⛔ Spedirne uno per passata di scrittura, con ~25 passate al secondo contro 50 blocchi prodotti, perdeva **esattamente la metà** |

⚠ **E la forma del numero era l'indizio**: *esattamente* la metà. Una perdita di rete non è mai
esattamente la metà; un'aritmetica sì (`LEZIONI.md` §2.7).

### 5-quater.5 ✅ ⛔ La priorità di tempo reale si concede **dall'unità**, e il programma la VERIFICA

**R26 di v1** (`~/Documenti/REMOTIX/REFERENCE.md`, `[M]` 5 agosto 2026): un processo con
`RLIMIT_RTPRIO` a zero **non può chiedere `SCHED_FIFO`**. PipeWire ci prova, gli viene negato, e il
suo anello dei dati raccoglie i campioni a priorità normale ⛔ **mentre nello stesso processo il
codificatore video si prende un core**. Il sintomo non è un errore: è **audio che scoppietta quando
il desktop lavora**, invisibile a ogni controllo sul filo.

⇒ `LimitRTPRIO=20` e `LimitNICE=-11` **nell'unità systemd**. ⭐ E poiché un rlimit il codice non se
lo può dare, il figlio **lo legge e scrive una riga ⛔ se manca**: è l'invariante **I7** applicata
dove la protezione *deve* stare in una configurazione — una riga persa si vede invece di tacere.

---

## 6. Il codice che si eredita

### 6.1 ✅ Il patrimonio di v1 è qui, e versionato

*8 agosto 2026.* Portato dal server di sviluppo, dove viveva senza versionamento e senza una
seconda copia. Verificato per impronta SHA-256, 103 file su 103.

| | |
|---|---|
| `fondamenta/remotix-c/` | **17.481 righe di C**, 26 moduli |
| `fondamenta/remotix-c/prove/` | **4.563 righe di banchi**, uno script per fase |
| `fondamenta/banchi/` | **262 file** dell'indagine sulla fase 11, `misura-cattura.c` compreso |
| `fondamenta/remotix-rust/` | 7.163 righe, ramo IronRDP chiuso il 3 agosto |
| `fondamenta/documenti/` | PIANO, SPECIFICA, REFERENCE, protocollo-rdp, client-android, xrdp |
| `fondamenta/calibrazione/` | le tre scene della taratura del 1 agosto |

> ### ⛔⛔ E QUESTA TABELLA OMETTEVA LE DUE SOLE PARTI DI `fondamenta/` CHE SONO VIVE — *corretto il 16 agosto 2026*
>
> *Trovato censendo `fondamenta/` file per file, su richiesta dell'utente. La tabella qui sopra ha **sei
> righe** e le lascio com'erano — ⛔ ma `fondamenta/banco/` e `fondamenta/strumenti/` non ci sono, e sono
> **l'attrezzatura corrente del progetto**. Chi leggeva questo paragrafo per sapere che cos'è `fondamenta/`
> si portava a casa che era tutto archivio. Non lo è.*
>
> ## La mappa vera: che cosa è **vivo**, che cosa è **archivio**, che cosa non serve a nessuno
>
> *`[M]` 16 agosto 2026, citazioni contate dai dieci documenti, da `src/`, da `banchi/` e da `web/`.*
>
> | | file | MB | citazioni | |
> |---|---|---|---|---|
> | ⭐⭐ **`fondamenta/banco/`** | 13 | 0,2 | **enter.sh: 193** | **VIVO, e regge tutto**: `enter.sh` è il modo in cui si entra nella macchina di prova. Con `provision.sh`, `provision-server.sh`, `gpu-udev.sh` (applicato il 15 agosto, §4.6-ter), `server.sh`, `vm.sh` |
> | ⭐⭐ **`fondamenta/strumenti/sshpw.py`** | 1 | 0,01 | **81** | **VIVO**: lo chiamano decine di banchi di V2 |
> | ⭐ `fondamenta/remotix-c/` | 70 | 1,0 | 37 file su 70 | **archivio con valore**: è la miniera del riuso — `kwin.c` (822 righe) e `appunti_wlr.c` (796) sono nel piano delle fasi 11 e 12 |
> | ⭐ `fondamenta/banchi/banco-compositori/` | 74 | 0,7 | 4 | **archivio con valore**: le misure di KWin, wlroots e Mutter, che le fasi 11 e 12 rifaranno |
> | ⭐ `fondamenta/documenti/` | 6 | 0,5 | tutti e sei | **archivio con valore**: la storia del prezzo pagato (`LEZIONI.md` §0) |
> | ⚠ `fondamenta/calibrazione/` | 10 | ⛔ **90,2** | la cartella 1 volta, i file **0** | le tre scene a tre risoluzioni — **il 96 % del peso del progetto**. Vedi il riquadro sotto |
> | ⚠ `fondamenta/remotix-rust/` | 23 | 0,4 | **1**, ed è questa tabella | il ramo IronRDP, **chiuso il 3 agosto**. La lezione è scritta qui; il codice non la aggiunge |
> | ⛔ `fondamenta/banchi/` *(resto)* | ~190 | 4,1 | 17 | 86 `.log`, 8 `.png`, 10 archivi `.tgz/.gz/.xz`, 2 `.so`, gli esiti di esecuzioni del 1-8 agosto |
> | ⛔ ~~`fondamenta/tracce/`~~ | 8 | 0,4 | **0** | flussi `.h264` e log di provisioning **RDP** — e RDP è morto con §1.6. ✅ **Tolti il 16 agosto 2026** |
> | ⛔ ~~`fondamenta/banco/*.prima*`, `*.rust`~~ | 4 | 0,05 | **0** | **copie a mano** di `enter.sh`, `provision.sh`, `provision-server.sh`, `vm.sh`, fatte prima di una modifica. ⚠ Una copia di riserva accanto all'originale è una trappola, non una rete: la rete è git. ✅ **Tolte il 16 agosto 2026** |
>
> ## ⛔⛔ E la cosa che cambia il ragionamento sui 90 MB: **toglierli non recupera niente**
>
> `[M]` il `.git` pesa **94,29 MiB** e i dieci `.mp4` ne sono **90,2** — cioè **il 96 %**. Sono dieci
> file distinti, entrati una volta sola e mai più toccati.
>
> ⛔ **Ma `git rm` non li toglie dalla storia**: resterebbero nel `.git` e il peso non cambierebbe di
> un byte. L'unica strada che recupera davvero è **riscrivere la storia**, e costa un prezzo che
> questo progetto non può pagare:
>
> ⛔⛔ **quindici hash di commit sono citati nei documenti come ricette di recupero** — `0c85e5c`
> per i 94 rapporti degli agenti, `47bd41c` per il diario potato del `README`, e altri tredici nei
> verbali delle fasi. Una riscrittura li cambia **tutti**, e ogni ricetta punterebbe al nulla.
>
> ⇒ ⭐ **E non serve pagarlo**: `[M]` il repository **non ha un remote**, vive solo su questo disco.
> Novantaquattro megabyte fermi in una cartella non costano niente a nessuno.
>
> ⇒ **Decisione: i `.mp4` restano.** ⚠ E si scrive qui perché nessuno riapra la questione contando
> di nuovo i megabyte senza contare gli hash.
>
> ⭐ **Con un fatto che vale per la fase 9**: le scene **si rigenerano**, `fondamenta/banco/calibrazione.sh`
> le produce con `ffmpeg` alle tre risoluzioni native. ⚠ **Ma non byte per byte**: un `ffmpeg`
> diverso dà un file diverso, e il confronto con i numeri del 1 agosto si romperebbe. ⇒ Chi alla
> fase 9 volesse confrontarsi con la taratura di v1 **usi questi file**, non quelli che si
> rigenererebbe.

`LEZIONI.md` è stato promosso al livello di V2: è il fondamento di `CODER.md` e `REVIEWER.md`,
che lo citano 29 volte su 20 sezioni.

### 6.2 🔸 Circa il 79 % del C sopravvive alla morte di RDP

Misurato contando le occorrenze di `freerdp|winpr|rdpContext|RDPGFX|rdpSettings` per file:
7.442 righe **pulite** (`palco`, `cattura`, `kwin`, `mutter`, `appunti_wlr`, `superficie`,
`sentinella`, `autenticazione`…), 4.570 con contaminazione superficiale, 1.781 media, e
**3.688 che muoiono** (`server.c`, 134 occorrenze, e `rete.c` che va sostituito da QUIC).

⚠ È una misura di primo livello: contare gli `#include` dice chi *tocca* FreeRDP, non chi
*dipende* da RDP. `scambio.c` e `codificatore.c` vanno letti prima di dare il 79 % per buono.

### 6.3 ✅ Il server si scrive in C

*8 agosto 2026. «Confermo il C».*

⚠ **Non è un'eredità: è una decisione nuova che ripete la vecchia.** Il vincolo di v1
(`fondamenta/documenti/SPECIFICA.md` §8-bis) aveva una ragione sola — *«gnome-remote-desktop smette di
essere un riferimento da cui trarre ispirazione e diventa un riferimento da cui trarre
codice»* — e **quella ragione è morta con RDP**: non c'è più niente da trapiantare, perché
nessuno ha scritto RCP prima di noi. La questione è stata riaperta a occhi aperti e richiusa
per un motivo diverso.

**Il motivo nuovo è il conto di §6.2**: circa 14.000 righe sopravvivono, con i loro banchi già
tarati. Il pezzo QUIC ne vale forse 2.000. Riscrivere quattordicimila righe misurate per
guadagnare l'ergonomia di duemila è uno scambio pessimo — ed è anche `LEZIONI.md` §10 in
azione, perché fra le cose che si butterebbero ci sono **4.563 righe di banchi**, e questo
progetto non è mai morto sul codice: è morto sulle misure.

**Che cosa questa decisione NON decide:** i client. Quello Android è Kotlin comunque, per via
di MediaCodec. Quello Linux è aperto — se sarà in C potrà condividere `librcp` col server, che
è un argomento a favore ma non una conclusione.

### 6.4 🔸 QUIC via `ngtcp2` + `nghttp3` — **chiusa il 10 agosto 2026, con un banco**

> ⭐ **La decisione, in tre righe.** Delle quattro candidate ne resta **una**: `ngtcp2`+`nghttp3`.
> `lsquic` è uscita perché **pretende l'SNI** e il prodotto si usa per indirizzo; `libwtf` era
> ultima in fila (seconda pila QUIC, licenza che si contraddice); e ⛔ **`quiche`, usata dal C, non
> riesce a dichiarare WebTransport** — la misura è qui sotto. `ngtcp2` invece regge: **due browser
> veri aprono la sessione**, e lo strato che manca costa **373 righe di codice** nostro
> (`[M]` 10 agosto 2026, ore 16:30 — la scomposizione e la successione delle misure stanno nel
> riquadro «Quante righe sono nostre, e a che ora» più sotto).
>
> ⚠ **Il prezzo, dichiarato**: quelle righe includono la **riscrittura del frame SETTINGS che
> nghttp3 sta scrivendo**, perché la sua API pubblica non permette di annunciare un'impostazione
> arbitraria. È collante che dipende dalla forma dei byte di una libreria, non da una sua promessa:
> ⛔ **va riprovato a ogni aggiornamento di nghttp3**, e il banco che lo riprova esiste.
>
> 🔸 *Derivata, correggibile senza discussione: se un giorno `quiche` esporrà
> `set_additional_settings` nell'FFI e Debian avrà `rustc` ≥ 1.88, la scelta si riapre — e i due
> banchi per rifare il confronto sono scritti.*

*Il testo qui sotto è la cronaca, e si legge in ordine: la decisione è nata come «`quiche`» su
carta, ed è finita all'opposto con tre misure.*

Era l'unico argomento serio a favore di Rust, e si risolve con una libreria invece che con un
linguaggio: **`quiche`** di Cloudflare ha un'**API C**, licenza **BSD-2**, ed è in produzione
da anni. Si prende il QUIC finito senza cucire ngtcp2 a mano e senza toccare la libertà di
licenza (§7.6).

L'alternativa in C puro è `ngtcp2` (MIT), che però richiede di portarsi il TLS e montare più
pezzi. **Da confermare quando si aprirà il trasporto**, non prima: è il tipo di scelta che si
fa con un banco davanti, non su carta.

> ⛔ **Il criterio è cambiato il 9 agosto 2026 con §1.6, e va riscritto prima di scegliere.** Non
> basta più che la libreria parli QUIC: il client è un browser, quindi il server deve portare
> **HTTP/3 e WebTransport**, più un ascoltatore **TCP** per il primo caricamento della pagina
> (`Alt-Svc`). La domanda non è più «quale QUIC», è **«quale delle due arriva fino a
> WebTransport lato server, e quanto collante resta a noi»**.
>
> `[M]` 9 agosto, sul ferro: Trixie ha `libngtcp2-dev` 1.11 **e** `libnghttp3-dev` 1.8 come
> pacchetti, `cargo`/`rustc` 1.85 per compilare `quiche`, e `python3-aioquic` 1.2 — che serve al
> cliente di prova, non al server.
>
> ⚠ **E questa scelta è diventata critica invece che secondaria**: prima decideva quante righe di
> collante scrivere, adesso decide **se il prodotto esiste**. Va chiusa con la sonda del browser
> davanti, non dopo.

> ### ⭐ Il censimento del 9 agosto notte — i candidati non erano due, e nessuno dei due originali porta WebTransport
>
> *Fatto prima di scrivere una riga di B2, come punto 0 della ricetta (`LEZIONI.md` §9): **chi, al
> mondo, fa già questa cosa?** Tutto quel che segue è `[S]` e `[R]` — **letto, non misurato**. La
> misura è B2, e serve proprio perché queste righe non bastano.*
>
> | Candidata | Lingua e API | WebTransport **lato server** | Che collante resta a noi |
> |---|---|---|---|
> | **`quiche`** | Rust con **API C** | ⛔ **no** — ma ha `h3::Config::enable_extended_connect()` (`SETTINGS_ENABLE_CONNECT_PROTOCOL`) `[R]` e i datagram QUIC completi (`dgram_send`/`dgram_recv`) `[R]` | **tutto lo strato WebTransport** |
> | **`ngtcp2` + `nghttp3`** | **C** | ⛔ **no** — ma nghttp3 implementa **RFC 9220** (l'extended CONNECT di HTTP/3) `[S]` **e** sa mandare e ricevere `SETTINGS_H3_DATAGRAM` con il **Capsule Protocol** `[S]` | lo strato WebTransport, ⭐ **con le fondamenta più complete delle quattro** |
> | ⭐ **`lsquic`** (LiteSpeed) | **C** | ⚠ **in parte** — vedi il riquadro qui sotto: il flag c'è, l'API pubblica è molto più magra del nome | **meno delle altre due, ma non «poco»** |
> | **`libwtf`** | C, ma **su MsQuic** | ⭐ sì, negozia draft-15/07/02 `[S]` | poco, ⚠ ma porta dentro **una seconda pila QUIC** |
> | ~~`web-transport-quiche`~~ | ⛔ **Rust puro, nessuna API C** | sì | ⛔ **escluso**: il server è in C (§6.3) |
>
> ⛔ **Il fatto che riordina tutto**: *«quale delle due arriva fino a WebTransport»* aveva una
> risposta sola — **nessuna delle due**. Le due candidate originali danno le **fondamenta**
> (extended CONNECT, datagram, capsule) e non lo strato di sopra: le impostazioni della sessione, il
> tipo di stream unidirezionale, il segnale sui bidirezionali, il prefisso dei datagram, la capsula
> di chiusura. La domanda vera è sempre stata la seconda — **quanto collante** — e adesso ha una
> forma elencabile.
>
> ⚠ **E i due nuovi arrivati vanno guardati con sospetto, non con sollievo:**
>
> | | |
> |---|---|
> | **`lsquic`** | ⛔ la funzione è **spenta per difetto** e **non compare nella documentazione della 4.9.3** `[R]`. «Implementato ma spento e non documentato» è la firma di un pezzo che **nessuno esercita**: va provato, non creduto |
> | **`libwtf`** | ⚠ 70 stelle, 51 commit, un autore — e ⛔ **la licenza si contraddice da sola**: il README dice MIT, il piè di pagina Apache-2.0. Su una libreria che entrerebbe nel cuore del prodotto è un difetto di per sé (§7.6) |
>
> ### ⛔ E `lsquic` è il caso da manuale di E1: il flag era necessario, non sufficiente
>
> *Letta l'intestazione pubblica `include/lsquic.h` invece di fidarsi del `CMakeLists.txt`.* Dietro
> `LSQUIC_WEBTRANSPORT_SERVER_SUPPORT` c'è **tutto quel che segue, e nient'altro** `[R]`:
>
> | | |
> |---|---|
> | due impostazioni | `es_webtransport_server`, `es_max_webtransport_server_streams` |
> | quattro funzioni, **tutte di classificazione** | `lsquic_stream_set_webtransport_session` · `..._is_webtransport_session` · `..._is_webtransport_client_bidi_stream` · `..._get_webtransport_session_stream_id` |
>
> ⛔ **Non c'è nessuna API per stabilire una sessione, per aprire uno stream WebTransport, per
> mandare un datagram WebTransport.** *«Il `CMakeLists` ha un flag che si chiama
> `WEBTRANSPORT_SERVER_SUPPORT`»* ⇒ *«lsquic fa WebTransport»* è **esattamente** la forma **E1**, la
> stessa che ha ucciso v1 e che `STUDI.md` §web §9 punto 1 aveva già visto ricomparire travestita da API
> (`prefer-hardware`). ⭐ **Terza volta in tre giorni, e stavolta l'ha fermata la lettura.**
>
> ⚠ **Quel che quelle quattro funzioni implicano, però, è più di quel che dicono**: per rispondere
> *«questo stream appartiene alla sessione WebTransport numero N»* lsquic **deve** già leggere le
> intestazioni degli stream WT e associarli — che è la parte noiosa. È un indizio a favore, non una
> prova: **si misura**.
>
> ### ⭐ E la prima misura c'è — `[M]` 9 agosto 2026, `banchi/01-b2-costruisci.sh`
>
> | Che cosa | Atteso | Misurato |
> |---|---|---|
> | BoringSSL compila nel `devroot` | sì | ✅ sì |
> | `lsquic` **v4.9.3** compila con `-DLSQUIC_WEBTRANSPORT=ON` | sì | ✅ sì, e la define compare nei `FLAGS` di `build.ninja` |
> | ⛔ **il flag ha prodotto i simboli** | 4 su 4 | ⭐ **4 su 4** |
>
> ⭐ **E il codice non è un moncone**: `webtransport` compare in **sei file** — `include/lsquic.h`,
> `lsquic_stream.c/.h`, `lsquic_engine.c`, `lsquic_full_conn_ietf.c`, `lsquic_hcso_writer.c` `[R]`.
> Cioè tocca il motore, gli stream, la connessione IETF **e lo scrittore dello stream di controllo
> HTTP/3** — dove vivono le impostazioni. È un'implementazione distribuita nei punti giusti.
>
> ⛔ **Ma «i simboli ci sono» non è «la sessione si apre»**: è il gradino successivo di E1, e la
> misura che conta resta **un browser vero che apre una sessione**.
>
> ### ⛔ E leggendo oltre i simboli: `lsquic` parla la bozza **02**, i browser di oggi no
>
> *`[R]` `⟨lsquic⟩ src/liblsquic/lsquic_hcso_writer.c`, dove il server scrive le impostazioni sullo stream di
> controllo HTTP/3.* Ecco **tutte** quelle che emette:
>
> | Impostazione | Valore | |
> |---|---|---|
> | `SETTINGS_ENABLE_WEBTRANSPORT` | `0x2b603742` | ⛔ **è della bozza 02** |
> | `WEBTRANSPORT_MAX_SESSIONS` | `0x2b603743` | ⛔ **idem** |
> | `H3_DATAGRAM_ENABLED` | `0x33` | ✅ corrente |
> | `SETTINGS_ENABLE_CONNECT_PROTOCOL` | `0x08` | ✅ corrente |
>
> ⛔ **E non emette mai `SETTINGS_WT_MAX_SESSIONS` (`0xc671706a`)**, che è l'impostazione con cui un
> server dichiara WebTransport dalla bozza 07 in poi — cioè quella che Chrome, Firefox e Safari
> cercano oggi.
>
> ⭐ **Da cui una previsione falsificabile, scritta PRIMA della misura** (`LEZIONI.md` §1.11: per
> ogni prova indiretta si scrive che aspetto avrebbe il contrario):
>
> | | |
> |---|---|
> | **la previsione** | un browser di oggi **non stabilirà** la sessione con `lsquic`: non vede la dichiarazione che cerca, e la `CONNECT` estesa viene rifiutata |
> | ⭐ **che aspetto avrebbe il contrario** | la sessione si apre lo stesso ⇒ **o** i browser accettano ancora le impostazioni della bozza 02, **o** ho letto male questo file. In tutt'e due i casi la previsione è sbagliata e va scritto perché |
> | **come si falsifica** | è la misura di B2: un browser vero contro un server minimo. **Costa quanto costa scrivere quel server** |
>
> ⚠ **Il che riporta `lsquic` in fondo alla fila invece che in testa**, e non per il difetto in sé:
> «implementato, spento per difetto, non documentato, **e fermo a una bozza di tre versioni fa**» è
> il ritratto di un pezzo che **nessuno esercita**. `CODER.md` §4.1 dice di dipendere invece di
> riscrivere — ma dipendere da codice che nessuno esercita è riscriverlo **con un ritardo**.
>
> ### ⛔⭐ `lsquic` è fuori, e per una ragione che nessuno aveva previsto — `[M]` 9 agosto 2026
>
> *Scritto il collante (`banchi/01-b2-lsquic-wt.c`, **333 righe**, di cui 236 di codice), compilato
> e messo in ascolto. Il cliente di prova si è collegato, e il server ha registrato questo:*
>
> ```
> handshake: for QUIC version 00000001, ALPN is h3
> handshake: SNI is not set, but is required in HTTP/3: fail certificate lookup
> handshake failed  ·  sending CONNECTION_CLOSE, error code: 336, reason: TLS alert 80
> ```
>
> `[R]` `lsquic_enc_sess_ietf.c:1326-1336`: in **modalità HTTP/3**, se il client non manda SNI,
> lsquic **fallisce la ricerca del certificato e chiude**. C'è una scappatoia — `esi_sni_bypass` —
> ⛔ **ma è dentro `#ifndef NDEBUG`**, cioè esiste solo nelle build di debug.
>
> ⛔ **E questo colpisce il caso primario del prodotto, non un caso limite.** `SPECIFICHE.md` e §1.7
> descrivono un server **senza dominio**, a cui l'utente arriva digitando `https://<indirizzo>:7447`
> — cioè **un indirizzo IP**. Un client che si collega a un IP **non manda SNI**: la specifica del
> TLS vieta gli indirizzi letterali in quel campo. Quindi:
>
> | | |
> |---|---|
> | ⛔ **`lsquic` non può servire un certificato a chi si collega per indirizzo** | ed è il modo in cui REMOTIX viene usato |
> | ⚠ **la previsione sulla bozza 02 resta APERTA** | non è stata né confermata né smentita: **non ci siamo mai arrivati**. Scriverla come «avevo ragione» sarebbe confermare una previsione con una prova che parla d'altro |
> | ⭐ **e il modello non è in discussione** | `aioquic`, sullo stesso indirizzo e con lo stesso certificato, serve **due browser** senza SNI. Il difetto è della libreria, non del disegno |
>
> ⭐ **Da cui un criterio nuovo per questa decisione, che nessuno aveva scritto perché nessuno lo
> immaginava**: la libreria **DEVE servire un certificato senza SNI**. Va provato per prima cosa su
> ogni candidata — costa una connessione, e qui ha eliminato una candidata dopo 333 righe.
>
> ⚠ *E il banco che ha prodotto questo `4 su 4` **aveva prima detto `0 su 4`**, per un difetto suo —
> `set -o pipefail` più `grep -q`. La cronaca sta in `FASI.md` §01-filo-nudo, «che cosa NON ha
> funzionato», ed è il motivo per cui questa riga porta la data e il nome dello script.*
>
> ⚠ **E un dettaglio che vale come odore**: il commento di `es_webtransport_server` dice *«Enable
> datagram extension for http3 server»* — cioè **documenta un'altra cosa**. Un campo la cui
> documentazione parla d'altro è un campo che nessuno ha riletto.

> ### ⭐⛔ `ngtcp2` passa il criterio nuovo, ed è il primo a essere provato prima del collante — `[M]` 10 agosto 2026
>
> *`banchi/01-b2-sni-ngtcp2.sh` (costruisce il bersaglio) · `01-b2-sonda-sni.py` (la sonda) ·
> `01-b2-lancia-sni.sh` (conduce). Il bersaglio è **il loro server d'esempio**, `bsslserver`, non un
> server nostro: un server nostro sarebbe collante, cioè la cosa che questa prova deve venire prima
> di scrivere. `ngtcp2` **16.11.0** + `nghttp3` **1.18.90**, sullo stesso BoringSSL di `lsquic`.*
>
> **La previsione, scritta prima** (`LEZIONI.md` §1.11): *passa*. `[R]` in **109 file** di
> `examples/` e **18** di `crypto/` non compare **nessuna** occorrenza di `servername`,
> `SSL_get_servername`, `SSL_CTX_set_tlsext_servername_callback`, `select_certificate_cb` — con i
> controlli positivi che rispondono (`SSL_CTX_use_certificate_chain_file` in 8 file, `alpn_select`
> in 6, `SSL_` in 10). Nessuno cerca il certificato per nome: è legato all'`SSL_CTX` e servito
> sempre. ⭐ **Che aspetto avrebbe avuto il contrario**: la stretta di mano che cade come su
> `lsquic`, e allora la candidata usciva qui invece che dopo il collante.
>
> | La misura | Atteso | Misurato |
> |---|---|---|
> | ⭐ **senza SNI sul filo** | la sessione si stabilisce | ⭐ **sì** |
> | ⛔ **e il certificato è QUELLO** | l'impronta del file | ⭐ **`35wqjGTOmKSj…` combacia** — la stretta che riesce non basta, il certificato si confronta |
> | con SNI (`remotix.prova`), il controllo | idem | ✅ sì |
>
> ⛔ **Quindi il criterio è soddisfatto, e `ngtcp2` resta in gara con `quiche`.** Il prezzo si
> conosce: lo strato WebTransport è tutto nostro (extended CONNECT in 9 file, WebTransport in 0).
>
> ⚠ **E il primo numero della colonna «quanto collante»**: il loro server d'esempio pesa **7.041
> righe** in **13 file** `.cc` `[M]` — ⛔ **è un tetto, non una stima**: è il loro HTTP/3 completo,
> con la gestione dei file, la migrazione, il retry. Il nostro sarà meno. Il numero che conta è
> quello del server minimo, e si conterà quando esisterà.
>
> ### ⭐ E la diagnosi di `lsquic` si chiude, con l'altra metà che mancava — `[M]` 10 agosto 2026
>
> Il 9 agosto si era letto *«SNI is not set»* nel suo registro e si era concluso — giustamente — che
> pretende l'SNI. ⛔ **Ma «fallisce senza» non è «riesce con»**: finché nessuno prova la seconda
> metà, la diagnosi resta a metà e la candidata è eliminata su mezza prova. Le due righe, dallo
> stesso registro e nella stessa esecuzione:
>
> | Gamba | Che cosa dice `lsquic` |
> |---|---|
> | senza SNI | `SNI is not set, but is required in HTTP/3: fail certificate lookup` |
> | con SNI | ⭐ `looked up cert for remotix.prova` — **il certificato lo trova** |
>
> ⛔ **Il difetto è l'SNI e nient'altro: l'eliminazione del 9 agosto regge, e adesso su una prova
> intera.**
>
> ⚠ **E una cosa resta aperta, dichiarata invece che arrotondata**: con l'SNI la stretta di mano
> cade lo stesso, ma **più avanti e per un'altra ragione** — avviso TLS **120**, `no suitable
> application protocol`, dopo che il certificato è stato trovato. **Non è stata indagata**: non
> serve a questa decisione, e `lsquic` è fuori per un motivo che non dipende da lei. Sta scritta
> perché nessuno la scopra da capo credendo che sia nuova.
>
> ⚠ **E la previsione sulla bozza 02 resta APERTA anche dopo questa misura**: nemmeno stavolta ci
> siamo arrivati — la connessione con l'SNI muore prima delle impostazioni HTTP/3.

> ### ⭐ `quiche` passa lo stesso criterio, e porta con sé un costo che non c'entra col QUIC — `[M]` 10 agosto 2026
>
> *`banchi/01-b2-sni-quiche.sh` (`leggi`, poi `costruisci`) · misurata dallo stesso conduttore e
> dalla stessa sonda delle altre due, nella stessa esecuzione.*
>
> **La previsione, scritta prima di costruire** (`LEZIONI.md` §1.11), su **81 file** di 3 alberi con
> il controllo positivo che risponde (*«quiche»* in 33 file): `select_certificate_cb` in **0** file,
> `servername` in **1**. ⭐ E quell'uno è un **lettore**: `quiche/src/tls/mod.rs:510-526` espone
> `server_name() -> Option<&str>` — che al C arriva come `quiche_conn_server_name()` — cioè *dice*
> che cosa ha mandato il pari, non *sceglie* niente. **Restituisce `Option`**: «nessun SNI» è uno
> stato che la firma sa rappresentare, non un errore. ⇒ **previsione: passa**.
>
> | La misura | Atteso | Misurato |
> |---|---|---|
> | ⭐ **senza SNI sul filo** | la sessione si stabilisce | ⭐ **sì** |
> | ⛔ **e il certificato è QUELLO** | l'impronta del file | ⭐ **`35wqjGTOmKSj…` combacia** |
> | con SNI (`remotix.prova`), il controllo | idem | ✅ sì |
>
> ⛔ **Quindi il criterio dell'SNI non separa più le due candidate**: `ngtcp2` e `quiche` lo passano
> tutt'e due, e la scelta si sposta su quel che resta — **quanto collante** e a che prezzo.
>
> ### ⛔ E il prezzo di `quiche` è emerso prima della misura, ed è una catena di strumenti
>
> | | |
> |---|---|
> | ⛔ **la versione più recente non si costruisce** | `quiche` **0.29.3** pretende **rustc 1.88**; Trixie ne ha **1.85** `[M]`. Non è un'opinione: cargo si ferma e non compila |
> | **la più recente che si costruisce è la 0.28.0** | il banco la sceglie da sé, confrontando il `rust-version` di ogni etichetta col compilatore presente, ⭐ **e stampa quale e perché** — la misura vale per *quella* versione |
> | ⚠ **e nemmeno la 0.28.0 basta da sola** | il loro deposito è un `workspace`: `tokio-quiche`, `h3i`, `qlog-dancer` tirano dentro `tonic`, `icu`, `time`, `image`, che pretendono fino a 1.88. Si costruisce **`-p quiche`**, cioè il solo pacchetto che useremmo |
> | ⛔ **la scelta che ne discende, e va fatta consapevolmente** | scegliendo `quiche` si sceglie **o** di restare sulla 0.28.0 finché Debian non aggiorna `rustc`, **o** di portarsi una catena Rust fuori dai pacchetti (`rustup`) dentro la costruzione del prodotto. `ngtcp2` non pone la domanda: è C, e Trixie ha tutto |
>
> ⚠ **Questo non elimina `quiche`**: è un costo, non un difetto, e va scritto **accanto alla
> scelta** invece che scoperto da chi costruirà il prodotto fra un mese.
>
> ### ⚠ I due numeri di «quanto collante», e perché NON si sottraggono
>
> | Candidata | Il loro esempio | Che cos'è |
> |---|---|---|
> | `ngtcp2`+`nghttp3` | **7.041 righe**, 13 file `.cc` | il loro **HTTP/3 completo** in C++: file, migrazione, retry, qlog |
> | `quiche` | **614 righe**, 1 file `.c` | un esempio **minimo** in C, che però fa già HTTP/3 |
>
> ⛔ **Confrontarli così sarebbe E1**: non misurano la stessa cosa. Quel che il confronto dice
> davvero è che `quiche` **espone HTTP/3 dalla sua API C** e ci si arriva in 614 righe, mentre su
> `ngtcp2` l'HTTP/3 lo monta `nghttp3` e l'esempio che lo fa è quello grosso. ⭐ **Il numero che
> conta resta quello del nostro server minimo**, e si conterà quando esisterà — su tutt'e due.
>
> ⚠ **E su tutt'e due manca ancora la stessa cosa**: lo strato **WebTransport**, che nessuna delle
> due porta (censimento del 9 agosto, ancora valido).

> ### ⭐⭐ Il server minimo su `ngtcp2` esiste, e un browser vero apre la sessione — `[M]` 10 agosto 2026
>
> *`banchi/01-b2-ngtcp2-wt-innesta.py` innesta lo strato WebTransport nel loro server d'esempio;
> `01-b2-lancia-wt.sh` lo misura col cliente di prova; `01-b2-lancia-sonda.sh` lo misura **da un
> browser**. Il numero di righe non è una stima: è `git diff` nel loro albero.*
>
> | Che cosa | Misurato |
> |---|---|
> | ⭐ **la sessione si apre da un BROWSER VERO** | **Chrome 151.0.0.0** e **Firefox 140.0**, tutt'e due `APERTA` su `https://192.168.0.2:7447/rcp/1`, impronta pubblicata, **nessun avviso**, e `"ciao"` torna identico |
> | ⛔ **e il percorso sbagliato si RIFIUTA** | `/rcp/9` ⇒ **404**, come impone `RCP.md` §2.2 con il rilievo R1.24. È il controllo che dice *no*, ed è nel banco |
> | **i due parametri di §2.2** | `max_idle_timeout` **30 000 ms** e `max_datagram_frame_size` **65 536**, ⛔ **letti dal pari** con `01-b2-sonda-trasporto.py` |
> | ⭐ **quante righe sono NOSTRE** | vedi il riquadro «Quante righe sono nostre, e a che ora» qui sotto: la misura di questa mattina era **456 aggiunte / 329 di codice**, ed è stata rifatta alle 16:30 |
>
> > ⛔ *La prima riga è stata corretta il 10 agosto 2026, rilievo **R11.6**.* Diceva **«stampati dal
> > server all'avvio»**, cioè portava la provenienza sbagliata scritta accanto al numero giusto: è
> > la **configurazione** del server — che cosa ha *chiesto* a ngtcp2 — non che cosa è *arrivato* al
> > pari. ⛔ **È il corollario di `LEZIONI.md` §1.9 punto 5** — *un denominatore si legge dove la
> > cosa succede* — contraddetto nel documento che lo cita, e `FASI.md` §01-filo-nudo la dichiara
> > **il difetto peggiore della giornata** (*«l'ho violato io, quel pomeriggio, su una misura
> > mia»*). ⭐ La cura non è togliere il numero: è **prenderlo dalla fonte giusta**, e la fonte
> > giusta esisteva già — la sonda del trasporto ha letto gli stessi due valori dal pari.
>
> ⛔ **E adesso si sa in che cosa consiste «lo strato non c'è», perché sono i tre punti che
> l'innesto tocca:**
>
> | | |
> |---|---|
> | **1. non si può annunciare WebTransport** | `nghttp3_settings` ha `enable_connect_protocol` e `h3_datagram` — le due che stanno negli RFC — e l'API pubblica offre `submit_request/info/response/trailers/shutdown_notice`. ⛔ **Nessun modo di mettere un'impostazione arbitraria** sullo stream di controllo, e `SETTINGS_WT_MAX_SESSIONS` è quel che i browser cercano. Si riscrive il `SETTINGS` di nghttp3 **mentre lo scrive** |
> | **2. gli stream WebTransport vanno sottratti a nghttp3** | cominciano col tipo di frame `0x41` seguito dal numero di sessione, e nghttp3 leggerebbe quel numero come una **lunghezza** |
> | **3. i byte di ritorno non hanno una strada** | nghttp3 non conosce quegli stream, quindi non li metterà mai fra i vettori da scrivere: la coda d'uscita è nostra |
>
> ⚠ **Nessuno dei tre è un difetto delle due librerie**: fanno HTTP/3, e WebTransport non è HTTP/3.
> È esattamente il prezzo che questa decisione voleva conoscere prima di scegliere.
>
> ⚠ **E le due bozze mordono davvero.** Il server manda **tutt'e due** le dichiarazioni —
> `0x2b603742` (bozza 02) e `0xc671706a` (bozza 07+) — perché `aioquic` 1.2, il **nostro cliente di
> prova**, implementa la **02** `[R]` `h3/connection.py:90`, e i browser cercano la 07. ⛔ Un server
> che ne mandasse una sola funzionerebbe con metà dei nostri strumenti, e la metà che funziona
> sarebbe quella sbagliata da cui trarre conclusioni.
>
> ### ⛔ Che cosa questa misura NON dice
>
> | | |
> |---|---|
> | ⚠ **non è il confronto con `quiche`** | il numero di `quiche` **non esiste ancora**: il suo esempio in C fa HTTP/3, non WebTransport. Finché non si innesta lo stesso strato anche lì, il nostro è un numero **senza il suo paragone** |
> | ⚠ **due proprietà su sei**, *alle 08:00* | delle sei che B2 doveva verificare qui, questa misura ne portava due — **datagram abilitati** e **`max_idle_timeout` 30 s**. ⭐ **Le altre quattro sono state chiuse mezz'ora dopo**, riquadro qui sotto: non restano `[?]` |
> | ⚠ **i millisecondi non si confrontano** | 118,6 ms (Chrome) e 140,0 ms (Firefox) sono **avvii a freddo dentro `xvfb`**, e lo stesso motore ha dato 22,2 ms in un altro giro. B2 misura *se la sessione si apre*, non quanto ci mette: chi metterà questi numeri accanto ai 30,2 ms del 9 agosto confronterà due cose diverse |

> ### ⭐ Le sei proprietà del trasporto: **6 su 6**, lette dal pari — `[M]` 10 agosto 2026, mattina
>
> *`banchi/01-b2-sonda-trasporto.py`, con una spia dichiarata su `pull_quic_transport_parameters` di
> `aioquic`. ⛔ **Dal pari, non dal registro del server**: è la fonte che il riquadro qui sopra
> aveva sbagliato.*
>
> | | |
> |---|---|
> | `max_idle_timeout` | **30 000 ms** |
> | datagram | abilitati, `max_datagram_frame_size` **65 536** |
> | credito stream unidirezionali | **16** |
> | migrazione | **non** disabilitata |
> | 0-RTT | **non offerto** |
> | `allowPooling` | **`false`**, e dichiarato nell'esito registrato |
> | ⛔ **e la settima, che serve a B3** | il tetto d'inattività **si può cambiare**: con `--timeout=10s` il pari legge **10 000 ms** |
>
> ⛔ **E leggerle dal pari ha trovato due difetti che nessun banco funzionale vedeva**: il server
> **offriva 0-RTT** (due biglietti, `max_early_data_size` `0xffffffff`), che §2.3 vieta perché i
> dati 0-RTT si possono ripetere e il secondo messaggio di RCP è `CREDENZIALI`; e concedeva **3**
> stream unidirezionali invece dei 16 che §2.3 impone. ⚠ *Nessuno dei due ha un sintomo: la
> sessione si apriva uguale. `FASI.md` §01-filo-nudo l'aveva previsto per il primo — «il sintomo di
> 0-RTT acceso non esiste».*
>
> ⚠ *Questo riquadro è stato aggiunto il 10 agosto 2026, rilievo **R11.5**: la misura c'era e stava
> in `README.md` e in `FASI.md` §01-filo-nudo, ma **non qui** — e §6.4 continuava a dichiararne
> quattro su sei ancora `[?]`. Tre righe dello stesso giorno e dello stesso banco che dicevano cose
> diverse, e quella che un lettore ha diritto di prendere per buona è questa (`README.md`: «le
> decisioni stanno in `DECISIONI.md`, una sola volta»). ⛔ **E non era simmetrica**: con la riga
> vecchia il divieto di 0-RTT di `RCP.md` §2.3 risultava non verificato mentre due documenti lo
> dichiaravano verificato.*

> ### ⭐ Quante righe sono nostre, e a che ora — `[M]` 10 agosto 2026
>
> ⛔ **Il numero è cresciuto tre volte in un giorno, e le tre misure non si confrontano se non si
> dice a che ora sono state prese.** Sono tutte `git diff` nell'albero di `ngtcp2`, mai stime.
>
> | Ora | Che cosa è stato misurato | Aggiunte | Codice | Commento | Vuote |
> |---|---|---|---|---|---|
> | **08:00** | lo strato WebTransport di B2, prima delle cure sul trasporto | **456** | **329** | 85 | 42 |
> | ~08:30~ | ⚠ `[?]` un numero **482 / 333** è entrato in `README.md` con il commit delle sei proprietà, e **nessun documento ne registra la scomposizione né il comando che l'ha prodotto**. Non lo si promuove e non lo si cancella: sta qui, dichiarato per quel che si sa | ~482~ | ~333~ | — | — |
> | ⭐ **16:30** | lo strato WebTransport di B2 **da solo**, dopo la lettura della capsula di chiusura | **553** | **373** | **134** | **46** |
>
> ⭐ **Come è stata presa quella delle 16:30, ed è il punto che la rende ripetibile**: su albero
> pulito, dopo `01-b3-rcp-innesta.py --togli` e `01-b2-ngtcp2-wt-innesta.py --togli`, riapplicando
> **il solo** `01-b2-ngtcp2-wt-innesta.py`. È la sequenza che `ricostruisci()` di
> `banchi/01-b11-guasto.sh` esegue già.
>
> ⛔ **E un numero che NON va in questa colonna**: con **tutt'e due** gli innesti applicati — B2 più
> i fili di B3 — l'esempio porta **972 righe aggiunte, 618 di codice** `[M]`, stessa ora. ⚠ *Non è
> confrontabile con i tre di sopra: misura due cose invece che una, ed è precisamente la ragione per
> cui `01-b3-rcp-innesta.py` è un innesto **separato** — «farlo crescere con RCP dentro renderebbe
> due misure diverse sotto la stessa etichetta» (forma **E2**).*
>
> ⚠ *Il riquadro è del 10 agosto 2026, rilievo **R11.1**. `README.md` portava 482/333 sotto il
> titolo «Che cosa è misurato `[M]`» — il posto in cui un numero senza provenienza pesa di più —
> mentre questo documento e `FASI.md` §01-filo-nudo portavano 456/329 dello stesso giorno. ⛔ E la
> giustificazione che il README dava per non rimisurare era falsa: la misura si sa prendere, e
> adesso è presa.*

> ### ⛔⭐ E `quiche` non arriva a WebTransport dal C: la dichiarazione non si può fare — `[M]` 10 agosto 2026
>
> *La regola delle 333 righe, applicata una seconda volta: **si prova per prima la cosa che può
> uccidere la candidata**. Qui è costata la lettura di due file e una connessione, invece di un
> secondo strato WebTransport scritto per intero.*
>
> **La lettura, e la previsione scritta prima** `[R]`:
>
> | | |
> |---|---|
> | ⭐ **`quiche` HA la funzione che a `nghttp3` manca** | `h3::Config::set_additional_settings(Vec<(u64,u64)>)` — `quiche/src/h3/mod.rs:644`. Un modo pulito e sostenuto di mettere un'impostazione arbitraria nel proprio SETTINGS |
> | ⛔ **ma non arriva all'API C** | **zero** occorrenze di `additional_settings` in `h3/ffi.rs` e **zero** in `include/quiche.h`. Il `quiche_h3_config` esporta **quattro** setter, e nessuno è quello |
> | ⛔ **e il trucco di `ngtcp2` lì non esiste** | su `ngtcp2` nghttp3 **consegna all'applicazione** i byte dello stream di controllo da scrivere, e li abbiamo riscritti al volo. `quiche` scrive dentro la connessione da sé: un'applicazione in C quei byte **non li vede mai** |
>
> ⇒ **previsione: `quiche`, dal C, non dichiarerà WebTransport.**
>
> **La misura** — `banchi/01-b2-sonda-impostazioni.py`, che legge `received_settings` di `aioquic`,
> cioè **quel che è arrivato sul filo**, non quel che la configurazione dice:
>
> | Server | Impostazioni dichiarate |
> |---|---|
> | ⭐ **`ngtcp2` col nostro strato** *(controllo positivo)* | **7**, fra cui `ENABLE_WEBTRANSPORT` **e** `WT_MAX_SESSIONS` |
> | ⛔ **`quiche`**, con tutto acceso | **4**: `ENABLE_CONNECT_PROTOCOL`, `H3_DATAGRAM`, `H3_DATAGRAM_00`, e una GREASE. ⛔ **Nessuna delle due dichiarazioni di WebTransport** |
>
> ⛔ **Quindi un browser non aprirebbe la sessione, e non c'è riga di codice nostro che rimedi**:
> quel frame lo scrive la libreria, e dal C non c'è modo di toccarlo.
>
> ⚠ **E la riga onesta accanto al verdetto**: *«impossibile»* sarebbe troppo. La funzione **esiste**,
> è solo non esposta — cioè **una decina di righe di FFI**, da mandare a monte o da portarsi dietro
> come patch. Sommata al `rustc` 1.88 contro 1.85, però, diventa: *per usare `quiche` bisogna
> toccare `quiche`*. Con `ngtcp2` non serve toccare niente, ed è C.
>
> ⚠ **E quel che questa misura NON dice**: **quante righe** costerebbe lo strato WebTransport su
> `quiche`. Non si sa, perché non si è arrivati a scriverlo — la candidata cade a un cancello
> precedente. ⭐ Ed è esattamente il punto della regola: il numero che non abbiamo è anche il
> lavoro che non abbiamo speso.
>
> ⭐ **Un dettaglio che vale come indizio di cura**: `quiche` manda una **GREASE**
> (`0x28d3890f99ed6413`), cioè un'impostazione inventata apposta perché i pari non si abituino a
> un elenco fisso (RFC 9114 §7.2.4.1). `ngtcp2`+`nghttp3`, col nostro strato, no.
>
> ### ⭐ E il punto di partenza di `ngtcp2`+`nghttp3`, misurato — `[M]` 9 agosto 2026
>
> *Banco `banchi/01-b2-costruisci-ngtcp2.sh`. Cercato dentro **447 file** dei due alberi, ⛔ **con il
> controllo positivo della ricerca**: la parola `nghttp3` compare in **110 file**, quindi il grep sta
> leggendo davvero.*
>
> | Che cosa | File |
> |---|---|
> | `SETTINGS_WT_MAX_SESSIONS` (`0xc671706a`) | ⛔ **0** |
> | il token `webtransport` | ⛔ **0** |
> | l'extended CONNECT (`:protocol`, `ENABLE_CONNECT_PROTOCOL`) | ✅ **9** |
>
> ⭐ **La previsione regge, e adesso è misurata**: le fondamenta ci sono, **lo strato WebTransport
> non c'è affatto**. Da cui il numero che B2 deve produrre — *quante righe di collante* — che si
> **conta**, non si stima.
>
> ⚠ *Il primo giro di questo stesso controllo aveva stampato «la previsione regge» da una ricerca
> **mai eseguita** — due alberi passati come una stringa sola, con `2>/dev/null` a nascondere
> l'errore. Il numero qui sopra vale perché il banco adesso dichiara il proprio denominatore. È la
> quarta regola di `LEZIONI.md` §1.9, nata da quell'errore.*
>
> ⛔ **Nessuna delle righe di questo riquadro è una misura del PRODOTTO.** Sono la lente che dice
> **a chi vale la pena scrivere il collante**, e quanto ne servirà.

---

## 7. ❓ Le domande aperte

**Non sono decisioni.** Sono buchi, elencati perché non si perdano.

### 7.1 ~~La misura della tela alla nascita~~ → **chiusa l'8 agosto, vedi §5.0**
La detta il client a ogni attacco. Niente predefiniti, niente preferenze.

### 7.2 ~~Blocco schermo alla disconnessione~~ → **chiusa l'8 agosto, vedi §4.3**
Il blocco è di REMOTIX, non del desktop: 30 minuti senza input e il client viene staccato. Con
una condizione di scadenza scritta, da rileggere se arriverà un'autenticazione più forte.

### 7.3 ~~Il fantasma: subentro o attesa?~~ → **chiusa l'8 agosto, vedi §4.4**
Nessuna delle due: chi tace è staccato, e il posto non lo tiene nessuno. Il bivio non esiste
più. ⚠ Resta fuori, e non è stata chiesta, la terza possibilità — **due client sullo stesso
desktop insieme**: costerebbe poco con un palco persistente, ma cambia il protocollo e andrebbe
decisa prima di scriverlo, non dopo.

### 7.3-bis ~~Dopo quanti secondi di silenzio un client è staccato?~~ → **chiusa il 9 agosto**
🔸 **30 secondi**, scritti in `SPECIFICHE.md` §5.3 — proposta mia, non pronunciata dall'utente.
La soglia decide **quando si libera il codificatore**, e non ha altri costi: essere dichiarati
staccati non fa perdere niente, perché nessuno tiene il posto (§4.4). Con QUIC il passaggio
WiFi → LTE non conta come silenzio, quindi i 30 secondi coprono solo le interruzioni vere.

### 7.4 ~~Proporzioni: bande o allungamento?~~ → **chiusa il 9 agosto**
🔸 **Si impagina, non si stira** — `SPECIFICHE.md` §6.2. Allungare deforma il testo e lo rende
illeggibile, che è l'unica cosa che un desktop non può permettersi. Il caso è raro per
costruzione: all'attacco le proporzioni combaciano sempre, e resta solo durante il
ridimensionamento e nel ripiego su KDE vecchio.

### 7.5 ~~Il linguaggio del server~~ → **chiusa l'8 agosto, vedi §6.3**
C, confermato. Non per eredità: la ragione di v1 era FreeRDP ed è morta con RDP. La ragione
nuova è il conto del riuso, banchi compresi.

### 7.6 ⏳ La licenza — **rinviata a fine progetto**, per decisione dell'utente (9 agosto 2026)
Non è più una domanda in attesa di risposta: è una decisione **programmata**, e la si prende
quando il progetto è finito. Fino ad allora vale il solo vincolo già emerso, che va rispettato
per non trovarsela decisa da sola: **niente x265** (GPL-only) come ripiego software. Con
SVT-AV1 (BSD-3) e FFmpeg compilato senza `--enable-gpl` la scelta resta interamente aperta.


### 7.7 ~~Multi-tenant: quanti utenti insieme?~~ → **chiusa il 9 agosto, vedi §4.6**
Dieci come tetto configurabile. Ma il limite vero non è un conteggio: è un budget di pixel al
secondo, e su una macchina sola lo pone il codificatore.

### 7.8 ~~La latenza~~ → **chiusa il 9 agosto, vedi §2.4-2.6**
50 ms di tetto, 40 di traguardo, e solo per il pezzo che è nostro. ⛔ *L'avvertenza che stava qui —
«il traguardo su GNOME probabilmente non si raggiunge, per lo stesso motivo dei 60 fotogrammi» — è
**caduta il 13 agosto 2026**: il ritardo misurato allora sforava anche il tetto, ma il motivo non
era quello — la parte grossa era nostra (il codificatore in software; la misura non vale più dopo la
fase 18), e il muro dei 37 non si riproduce (§2.5).*

### 7.9 ~~La fiducia: chi autentica il server verso l'utente?~~ → **chiusa il 9 agosto, vedi §1.3**
Fiducia al primo incontro, ricordata in silenzio. Nessuna impronta da confrontare: il rischio
sulla prima connessione è stato valutato e accettato per lo scenario previsto.

### 7.10 ~~Il touch da Android~~ → **chiusa l'8 agosto, vedi §5-bis**
Era la questione aperta n.1 di v1, mai chiusa in un anno. Risposta: trackpad con puntatore
disegnato dal client; tocco nativo con il posto riservato ma non implementato.

### 7.10-bis ~~La tastiera di Android: Unicode o scancode?~~ → **chiusa l'8 agosto, vedi §5-bis.6 e §5-bis.7**
Tutt'e due, ma non come pari: le **lettere** viaggiano come lettere, e solo i tasti che lettere
non sono viaggiano come posizioni. E la domanda si è allargata da Android a entrambi i client.
Quel che segue è il ragionamento che ci ha portati lì, tenuto perché la conclusione da sola non
si capisce.
Il passeggero del touch, e pesa di più. *«Una tastiera Android non è una tastiera fisica: non
ha scancode, ha un IME che produce testo»* (`fondamenta/documenti/client-android.md` §5.2). Il client
manda quindi **Unicode** per i caratteri stampabili e **scancode** per i tasti di controllo —
Invio, Tab, frecce, modificatori.

**Proposto: tutti e due, e l'Unicode non come ripiego ma come strada principale.** In dote
arriva la chiusura della questione n.7 di v1: la disposizione di tastiera dichiarata dal
client, su Android, **non serve** — quello che arriva è già il carattere finale.

Resta da confermare, ed è la parte che costa: la conversione da carattere a **posizione fisica
nella disposizione della sessione**, con i modificatori applicati intorno.

### 7.11 ~~La clipboard: bidirezionale?~~ → **chiusa il 9 agosto, vedi §5-ter**
Sì, nei due versi, e solo testo. La domanda era nata perché `SPECIFICHE.md` diceva
«server-client», che si legge in un verso solo.

### 7.12 ~~Il «fuori scope»~~ → **chiusa il 9 agosto**
🔸 Scritto in `SPECIFICHE.md` §12, dieci voci, ciascuna esclusa **deliberatamente** e non
dimenticata: Windows, i desktop X11, la redirezione di dischi/stampanti/porte/smart card, il
trasferimento file, immagini e file negli appunti, il multi-monitor come funzione, lo stilo, il
tocco nativo, la registrazione della sessione, e la compatibilità con client RDP/VNC/SPICE.

### 7.13 📖 Cinnamon — non si decide, **si studia**

*9 agosto 2026. «Va fatto uno studio simile a quanto fatto per gli altri DE: Cinnamon è in fase
di migrazione verso Wayland ma il processo è iniziato da poco, quindi non conosco lo stato in
cui è».*

⚠ **La proposta di dichiararlo fuori scope è stata respinta**, e la ragione è giusta: dentro o
fuori non si decide su un'impressione. Gli altri quattro desktop hanno uno studio ciascuno,
questo non ce l'ha, e finché non ce l'ha ogni giudizio è `[?]`.

⭐ **Ma lo studio costa molto meno degli altri quattro, e va detto perché non venga rimandato
per paura della mole.** Muffin **non è un compositore indipendente**: è un fork di Mutter,
staccato ai tempi di GNOME 3, e ne eredita l'architettura. Quindi `STUDI.md` §cinnamon non parte dal
foglio bianco — **parte da `STUDI.md` §gnome e cerca le differenze**. È una lettura in negativo:
*questo pezzo di Mutter c'è ancora? è stato rinominato? è rimasto fermo a cinque anni fa?*

**Le due domande che decidono, e vanno fatte per prime:**

1. **si può creare uno schermo virtuale senza monitor?** Su GNOME è `RecordVirtual`; su KDE la
   risposta negativa è stata il risultato più costoso di tutto lo studio (`STUDI.md` §kde §8.1);
2. **quanti fotogrammi consegna la cattura, con una scena dichiarata e sempre in movimento?**
   Mutter 37, KWin 60, wlroots 61 `[M]`.

Poi le altre dodici di `LEZIONI.md` §3, e la ricetta di §9 — a partire dal punto 0, *cercare chi
l'ha già fatto*, che su KDE aveva fatto trovare `KRdp` in un nono repository dopo che lo studio
lo aveva dato per inesistente.

> ## ✅ Lo studio è stato fatto il 9 agosto 2026 — sta in [`STUDI.md` §cinnamon](STUDI.md#cinnamon)
>
> Su `muffin` e `cinnamon` **6.7.4**, in `reference-cinnamon/`. **Tutto `[R]`, niente misurato.**
>
> **L'ipotesi del fork è confermata**: il binario `cinnamon` *è* il compositore, chiama
> `meta_init()` e `meta_run()` come gnome-shell. `ScreenCast` e `RemoteDesktop` sono le
> interfacce di Mutter rinominate, e **non c'è cancello** sul permesso di cattura.
>
> ⛔ **Ma tre cose che diamo per acquisite non esistono affatto** — verificate con lo strumento
> certificato prima su Mutter:
>
> | | Muffin 6.7.4 |
> |---|---|
> | `RecordVirtual` e `virtual_monitor` | **0 file** su tutto l'albero |
> | `ConnectToEIS` — l'input via libei | **0 file** |
> | `EnableClipboard` — gli appunti | **0 file**, e nemmeno `zwlr_data_control` |
> | un backend *headless* | solo in `src/tests/` |
>
> ⭐ **La via che resta**, ed è la ragione per non chiudere la voce: `META_DUMMY_MONITORS` +
> `MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60` forzano un monitor **fittizio** su qualunque
> backend, con la misura decisa all'avvio — l'equivalente del `--virtual --width W` di KWin, che
> il modello della tela (§5.0) già assorbe.
>
> ⚠ **Se regga davvero è `[?]`, ed è la misura M1 del §9 di `STUDI.md` §cinnamon**: che il gestore dei
> monitor sia finto non dice che il renderer lo sia. Può anche riuscire **consegnando zero
> fotogrammi**, che è il modo peggiore perché sembra funzionare (`REVIEWER.md` E1).
>
> **Il giudizio provvisorio**: Cinnamon costa più di tutti e cinque, e le due difficoltà — un
> secondo percorso di input, e appunti che **oggi non hanno strada** — non sono difficoltà di
> lettura ma funzionalità mancanti a monte. **Va messo ultimo**, e la decisione si prende sulle
> misure, non su questo documento.
>
> ⏳ **E ha una data di scadenza, posta dall'utente il 9 agosto:** *«tanto Cinnamon sarà l'ultimo
> DE ad essere supportato, e le cose potrebbero cambiare»*. È la clausola giusta: le tre assenze
> che pesano — `RecordVirtual`, libei, la clipboard — sono **funzionalità che Mint può portare in
> qualunque momento**, esattamente come KDE ha portato il ridimensionamento con `kwin!7932`. Chi
> riapre questa voce **ricloni `muffin` e rifaccia le quattro ricerche** prima di fidarsi di
> `STUDI.md` §cinnamon: un riferimento che invecchia in silenzio è peggio di nessun riferimento
> (`LEZIONI.md` §9.8).

---

> ## ⛔ Le tre domande della notte del 10 agosto 2026 — **si rispondono con una parola**
>
> Le tre che seguono (§7.14, §7.15, §7.16) sono nate dalla revisione `fasi/rapporti/R11-documenti.md`
> e stanno **qui** perché è qui che stanno le decisioni, una sola volta: `RCP.md`,
> `FASI.md` §01-filo-nudo e `README.md` **rimandano**, non copiano.
>
> ⛔ **Nessuna delle tre è decisa**, e la marca resta ❓ finché l'utente non parla — anche dove
> scrivo quale mi sembra più difendibile. Due di esse (§7.14, §7.15) **cambiano i byte sul filo**,
> e finché sono aperte due implementazioni conformi a `RCP.md` divergono senza che nessuna delle
> due abbia torto.
>
> ⚠ **E dall'11 agosto 2026 sono quattro**: §7.17 è nata il giorno dopo, **da una misura** — il banco
> B6 — e non da una lettura. Vale per lei tutto quel che è scritto qui sopra.
>
> ---
>
> ## ✅⭐ **TUTTE E QUATTRO SONO CHIUSE — l'11 agosto 2026**, e le ha chiuse l'utente
>
> | | la risposta | e che cosa ha portato con sé |
> |---|---|---|
> | **§7.14** | *«silenzio»* | chi riceve un `FIN` non spedisce più niente. ⛔ E `RCP.md` §8.1 guadagna l'eccezione: **chi ha ricevuto un `FIN` non è «chi chiude»** |
> | **§7.15** | *«se si può»* | il `CONGEDO` cade quando il canale è morto; il motivo resta nel codice di chiusura. ⭐ Chiude un **rosso su codice giusto** che B5 e B11 avrebbero dato |
> | **§7.16** | *«si tiene per i test, nel prodotto si fa pulizia»* | ⭐ e la risposta è stata **più larga della domanda**: è nato un principio — `SPECIFICHE.md` §2 punto 6, *sullo schermo dell'utente c'è il suo desktop e nient'altro* — con la pulizia da misurare alla fase 13 |
> | **§7.17** | *«5 secondi»* | ⛔ l'ultimo modo di **occupare un posto senza dire chi si è** |
>
> ⭐ **E tre di esse si incastrano su un caso solo**: il tetto di §7.17 scatta quando il canale di
> controllo non esiste ancora, quindi §7.15 dice che il `CONGEDO` non si manda e §7.14 dice per dove
> passa il motivo. ⚠ *Decise separatamente, nell'arco di un'ora, e nessuna delle tre sarebbe stata
> difendibile da sola.*
>
> ⛔ **Nessuna delle quattro è ancora provata sul ferro.** §7.17 chiede a **B6** un quarto caso,
> §7.14 chiede tre correzioni a `src/pagina.html` (righe 431, 479, 514, dove il prodotto fa oggi il
> contrario), §7.16 chiede un banco alla fase 13. **Decise ≠ misurate**, e finché non lo sono la
> distanza si dichiara.

### 7.14 ✅ Il `FIN` sul canale di controllo: chi lo riceve **tace**

> ## ✅ **IL SILENZIO** — deciso dall'utente l'**11 agosto 2026**
>
> *«silenzio, anche perché il server non attacca mai di sua iniziativa»*
>
> ⛔ **Chi riceve un `FIN` sul canale di controllo non spedisce più niente, nemmeno lì.** Il motivo
> viaggia per la seconda strada di `RCP.md` §3.1 punto 3 — il codice d'errore applicativo della
> chiusura — che non ha bisogno di un canale vivo.
>
> ### ⛔ La premessa era falsa, e va scritta qui perché è quella con cui la decisione è stata presa
>
> *«Il server non attacca mai di sua iniziativa»* **non regge**: attaccare di sua iniziativa è il
> comportamento **più misurato** della fase 1.
>
> | quando il server chiude da solo | quanto è provato |
> |---|---|
> | scade uno dei tetti di §4.6 | `[M]` **B6**: tutti e tre visti scattare — **5,0 · 60,1 · 10,0 s** — col congedo `TEMPO_SCADUTO` |
> | arriva una violazione | `[M]` **B5**: **36 casi su 36**, e dopo ciascuno una connessione nuova arriva a `ECCOMI` |
> | credenziali, ban, posto occupato | `RESPINTO` (§4.4) · `TROPPI_TENTATIVI` (§4.4-bis) · `GIA_ATTIVA_REMOTA` (§8.2) |
> | e il caso da cui nasce la domanda | ⛔ il **quarto difetto di B11** era *«il posto non si libera quando a chiudere il canale è il SERVER»*, `[M]` su Chrome |
>
> ⭐ **La decisione non cambia, e la ragione vera la rende più forte**: proprio perché il server
> chiude spesso, quel che fa chi riceve conta — e a scegliere è la misura, non la rarità del caso.
> ⚠ *Scritto così, e non «come ha detto l'utente», perché una ragione falsa in un registro delle
> decisioni vale più a lungo della decisione: è la forma **E5**, un fatto che era una deduzione mai
> misurata.*
>
> ⭐ **E la premessa non è finita lì: è diventata una regola.** Messa davanti alla contraddizione,
> l'utente ha scelto la forma stretta — *il server non butta fuori una sessione **sana**, e ogni sua
> chiusura ha un motivo che sa spiegare* — e non quella larga, che avrebbe portato via il ban, il
> rifiuto delle credenziali e la regola di rigore. ⇒ **`DECISIONI.md` §4.1-bis**, ✅ 11 agosto 2026.
> ⚠ *Cioè: la frase era falsa come descrizione di quel che il server fa **oggi**, ed era giusta come
> descrizione di quel che il server **deve** fare. Le due cose si somigliano abbastanza da passare
> per la stessa, e in un registro delle decisioni non lo sono.*
>
> ### La ragione che regge, ed è una misura
>
> `[M]` **10 agosto 2026**, difetto 2 di **B11**: **Chrome butta un messaggio spedito subito prima
> di chiudere la sessione.** Il `CONGEDO` della lettura B sarebbe dunque un **DEVE che un motore su
> due non può onorare** — la forma che il rilievo **R1.4** ha già dichiarato difetto. La seconda
> strada di §3.1 punto 3, invece, ⭐ **ha funzionato su tutt'e due i motori**, e su Firefox è
> **l'unica** che porti il motivo (il congedo arriva per due strade diverse, una per motore).
>
> ### Dove la decisione è andata, e il prezzo è pagato per intero
>
> | | |
> |---|---|
> | `RCP.md` §4.2 | il divieto passa da *«sugli altri canali»* a **«su nessun canale, compreso quello di controllo»** |
> | ⛔ `RCP.md` §8.1 | **l'eccezione scritta**: *chi ha ricevuto un `FIN` non è «chi chiude»*. ⚠ Senza di lei §4.2 vieta il byte e §8.1 lo impone: la decisione avrebbe **spostato** la contraddizione invece di chiuderla |
> | ⭐ `banchi/01-b11-lancia.sh` | il caso `fin-sul-controllo` aveva già l'atteso *«muta»*: ⛔ **il banco applicava questa lettura senza che nessuna riga la dicesse**, ed è la ragione per cui la domanda era stata posta |
> | ⛔ `src/pagina.html` **righe 431, 479, 514** | ⛔ **il prodotto fa oggi il CONTRARIO**: in tutt'e tre i punti, quando il server chiude il canale senza rispondere, la pagina chiama `congeda(ERRORE_PROTOCOLLO, …)` — cioè manda i nove byte. `[M]` 11 agosto 2026, letto nel sorgente. **Tre difetti da curare**, e la cura è togliere la chiamata lasciando l'`esito(...)` |
>
> ⚠ **E una cosa che la cura NON deve portarsi via**: quei tre punti chiamano `congeda()` anche per
> **scrivere l'esito all'utente**. Chi toglie la riga senza guardare toglie anche la frase che dice
> *«il server ha chiuso senza rispondere»*, e il sintomo diventa una pagina che non spiega niente —
> che è precisamente ciò che §8.2 vieta.

*Posta la notte del 10 agosto 2026, rilievo **R11.22**. Riguarda `RCP.md` §4.2 e §8.1. Le due
letture qui sotto sono lasciate come stavano: ⛔ una decisione senza l'alternativa che ha scartato
non si può rimettere in discussione quando i fatti cambiano.*

**Il fatto.** §4.2 dice: *«un `FIN` su quello stream, da una qualunque delle due parti, chiude la
sessione. Chi lo riceve **DEVE** considerarla finita; **NON DEVE** continuare a spedire **sugli
altri canali**»*. Il canale di controllo è uno stream **bidirezionale**: il `FIN` del server chiude
il verso del server, non quello della pagina. E §8.1 impone a chi chiude di mandare `CONGEDO`.
⛔ **Il divieto scritto nomina «gli altri canali» e non nomina quello di controllo**, quindi le due
letture sono tutt'e due conformi al testo di oggi.

| | **A — il silenzio** | **B — il congedo** |
|---|---|---|
| **la regola** | il `FIN` chiude la sessione **in tutt'e due i versi**: chi lo riceve non spedisce più niente, nemmeno sul controllo | il divieto è solo «sugli altri canali»: sul controllo la pagina **DEVE** ancora mandare il `CONGEDO` di §8.1, poi chiude |
| ⛔ **il byte sul filo** | **nessuno.** Il motivo viaggia solo nel codice d'errore applicativo della chiusura della sessione (§3.1 punto 3) | **nove byte** sul canale di controllo, prima della chiusura: `00 0C` (`CONGEDO`, §7.1) · `00 00 00 03` · il motivo di §8.2 · `00 00` (dettaglio vuoto). Poi la stessa chiusura di A |
| **chi la applica oggi** | ⛔ **il banco**: il caso `fin-sul-controllo` di B11 ha come atteso *«muta»*, e la pagina tace | nessuno |
| **il prezzo** | §8.1 deve guadagnare l'eccezione scritta — *chi ha ricevuto un `FIN` non è «chi chiude»* — o continua a imporre un obbligo che §4.2 vieta | il server non può contare su quel byte: ⛔ `[M]` 10 agosto, **Chrome butta un messaggio spedito subito prima di chiudere la sessione** (difetto 2 di B11). Un `DEVE` che un motore su due non onora |

**Il caso concreto, ed è già successo.** È il punto in cui il 10 agosto è nato il **quarto difetto
di B11**: su Chrome, dopo il `FIN` del server sul canale di controllo, **il posto di §8.2 `0x0F`
non si liberava** perché da lì in poi non arrivava più un byte capace di liberarlo, e l'utente
vedeva *«mi dice che sono già collegato, e non è vero»*. Con la lettura **B** quel byte esisterebbe
— è il `CONGEDO` — e arriverebbe dove il server già guarda. Con la lettura **A** il posto si libera
leggendo la capsula di chiusura, che è la cura che è stata scritta quella sera.

⭐ **Quale mi sembra più difendibile, e la ragione: A — il silenzio.** Non per il testo, che
ammette tutt'e due, ma per due misure dello stesso giorno: la seconda strada di §3.1 punto 3 —
il motivo dentro il codice di chiusura — **ha funzionato su tutt'e due i motori**, mentre il
`CONGEDO` della lettura B **è stato visto sparire su Chrome**. ⛔ Un `DEVE` che un browser su due
non può onorare è esattamente la forma che il rilievo R1.4 ha dichiarato difetto — *«era conforme
al testo quanto il primo»*. ⚠ E il prezzo di A va pagato per intero: senza l'eccezione scritta in
§8.1, A lascia in piedi la contraddizione invece di chiuderla.

**Come si chiude:** una parola — *«silenzio»* o *«congedo»*. Poi §4.2 dice se il `FIN` ricevuto
chiuda anche il verso di chi lo riceve, e §8.1 recepisce l'eccezione o la perde.

### 7.15 ✅ Il congedo di §8.1 vale **se il canale è ancora utilizzabile**

> ## ✅ **LA CONDIZIONE** — decisa dall'utente l'**11 agosto 2026**
>
> *«la soluzione più logica è "se si può". Se una connessione cade nessuno può dire al server
> "chiudo perché ho finito"»*
>
> ⛔ **L'obbligo del `CONGEDO` sul canale di controllo cade quando il canale non è utilizzabile.**
> Quel che non cade mai è il motivo dentro il **codice d'errore applicativo della chiusura**
> (`RCP.md` §3.1 punto 3), che viaggia nella chiusura stessa e parte anche a canale morto.
>
> ⭐ **E la ragione dell'utente è la ragione giusta, senza correzioni**: un `DEVE` che non si può
> rispettare non è una regola. `RCP.md` §0 lo dice di sé — *se una riga qui è ambigua, è un difetto
> di questo file* — e questa lo era: §8.1 lo imponeva senza condizioni, §3.1 punto 2 con la
> condizione, ⛔ e **un'implementazione conforme all'una era in violazione dell'altra**.
>
> ### Dove è andata, e che cosa ha chiuso
>
> | | |
> |---|---|
> | `RCP.md` §8.1 | la riga normativa porta la condizione dentro, e il riquadro dice perché |
> | ⭐ **un rosso su codice giusto** | **B5** e **B11** applicavano già il condizionale (rilievo R3.3): un banco scritto sulla forma assoluta **avrebbe bocciato un server corretto** ogni volta che la violazione arriva su uno stream unidirezionale col controllo già finito |
> | ⚠ **e non indebolisce §4.1-bis** | *ogni chiusura del server ha un motivo che sa spiegare*, decisa lo stesso giorno: il motivo arriva comunque. ⛔ Quel che si perde è **il byte sul canale morto**, cioè un byte che non partiva |
>
> ⛔ **Le due decisioni dell'11 agosto non si sostituiscono**: §7.15 dice **quando** l'obbligo cade,
> §7.14 dice **chi** non è tenuto affatto. Dopo un `FIN` ricevuto il canale, nel verso di chi lo ha
> ricevuto, **è ancora utilizzabile** — quindi senza §7.14 la condizione di §7.15 non lo salverebbe.

*Posta la notte del 10 agosto 2026, rilievo **R11.23**. Riguarda `RCP.md` §8.1 e §3.1 punto 2. Le
due letture qui sotto restano come stavano.*

**Il fatto.** §8.1: *«Chi chiude **DEVE** mandare `CONGEDO` con un motivo prima di chiudere la
sessione»*, e l'unica eccezione dichiarata è `RESPINTO`. §3.1 punto 2, per la stessa cosa:
*«**DEVE** mandare `CONGEDO` (§8) con il motivo, sul canale di controllo, **se il canale di
controllo è ancora utilizzabile**»*. ⛔ Un'implementazione che chiude **senza** congedo perché il
canale è rotto è **conforme a §3.1 e in violazione di §8.1**, nello stesso documento.

| | **A — l'obbligo è incondizionato** | **B — vale la condizione di §3.1** |
|---|---|---|
| **la regola** | chi chiude manda `CONGEDO` **sempre**, tranne dopo `RESPINTO` | l'obbligo cade quando il canale di controllo non è utilizzabile; il motivo passa comunque dal punto 3 |
| ⛔ **il byte sul filo** | i nove byte del `CONGEDO` **anche** quando il controllo è già chiuso o rotto — cioè un byte che spesso non può partire | **nessun byte** in quel caso: resta il solo codice d'errore applicativo della chiusura (§3.1 punto 3) |
| **chi la applica oggi** | nessuno | ⛔ **il banco**: B5 e B11 verificano le chiusure *«nei tre punti di §3.1 col secondo condizionale»* (`FASI.md` §01-filo-nudo, rilievo R3.3) |
| **il prezzo** | un banco scritto su §8.1 **boccia un server corretto** ogni volta che la violazione arriva su uno stream unidirezionale | §8.1 perde la forma assoluta, e va riscritta con la condizione dentro — una frase |

**Il caso concreto.** Una violazione arriva su uno **stream unidirezionale** dopo che il canale di
controllo è già finito: con **A** il server deve mandare un `CONGEDO` su un canale che non c'è più,
e il banco che pretende tutt'e tre i punti di §3.1 **dà rosso sul codice giusto** — è il rilievo
R3.3, già pagato una volta su questo stesso banco.

⭐ **Quale mi sembra più difendibile, e la ragione: B — la condizione.** Un `DEVE` che non si può
rispettare non è una regola, è un difetto del documento (`RCP.md` §0: *«se una riga qui è ambigua,
è un difetto di questo file»*), e la seconda strada non fallisce mai: il motivo viaggia nel codice
di chiusura anche quando il canale è morto. ⛔ **E costa una frase in §8.1, zero byte sul filo.**

⚠ **Le due domande si toccano e non si sostituiscono.** Rispondere *«vale la condizione»* a §7.15
**non** chiude §7.14: dopo un `FIN` ricevuto il canale di controllo, **nel verso di chi lo ha
ricevuto**, è ancora utilizzabile — ed è esattamente il punto che §7.14 chiede.

### 7.16 ✅ La funzione di banco resta 🔸 — e ⭐ **fuori dal prodotto consegnato**

> ## ✅ **DUE CASI DISTINTI** — deciso dall'utente l'**11 agosto 2026**
>
> *«Nessun quadratino: l'utente deve vedere il desktop senza artefatti, come se fosse davanti al
> monitor del PC» → e poi, messo davanti al prezzo: «distinguiamo i 2 casi: si tiene quello che
> serve per i test, ma poi nel prodotto finale si fa pulizia».*
>
> ⛔ **Il principio, ed è più grande della domanda che era stata posta**: sullo schermo dell'utente
> non compare **mai** niente che non sia il suo desktop. Non «spento per predefinito», non «dietro
> un interruttore»: **assente**. Chi si collega deve vedere quel che vedrebbe stando davanti al
> monitor del PC, e nient'altro.
>
> ⭐ **E la funzione di banco sopravvive, dall'altra parte del confine**: serve a **tarare il
> cronometro** del ritardo alla fase 3 — si inietta un ritardo noto e si verifica che la mediana
> salga di esattamente quello. ⛔ *«Un banco che non lo fa non sa di misurare»*
> (`web/rapporti/S4-ritardo-disegno.md` §4.2, controllo P1): toglierla del tutto avrebbe lasciato
> il numero più importante del progetto — il tetto dei 50 ms — **senza un modo di sapere se è
> vero**.
>
> ### Che cosa vuol dire, in concreto
>
> | | |
> |---|---|
> | **la marca resta 🔸** | non era una decisione dell'utente, e ⛔ **si può togliere senza tornare da lui**. Quel che l'utente ha deciso è il **confine**, non il messaggio |
> | ⛔ **il prodotto consegnato non la contiene** | non compilata, non raggiungibile, **non presente nel binario**. ⚠ *«Spenta»* non basta più: era la forma di prima, e questa decisione la sostituisce |
> | **il banco sì** | la costruzione di prova la contiene, e i due tipi `0x000F`/`0x0010` restano in `RCP.md` §7.5 come **funzione di banco dichiarata**, non come funzione del prodotto |
> | ⛔ **e la differenza si misura** | *«non c'è»* e *«c'è ed è spenta»* hanno lo stesso aspetto da fuori: si distinguono **cercando le marche dentro il binario consegnato**, come fa già `banchi/01-p1-prodotto.sh` con le sue otto marche. Senza quella prova, questa decisione è una buona intenzione |
>
> ### ⛔ Dove morde, e non è oggi
>
> **Fase 13 — il confezionamento.** È lì che nasce il binario che si installa, ed è lì che questa
> decisione si rispetta o si perde. ⚠ *Scritta anche in `PIANO.md` fase 13 e in `RCP.md` §7.5,
> perché una regola che vale fra undici fasi e sta scritta in un posto solo è una regola che nessuno
> troverà il giorno che serve.*
>
> ⚠ **E una cosa che questa decisione NON dice**: che la funzione di banco fosse un problema. Nasce
> **spenta**, e `banchi/01-b5-violazioni.py` verifica che a funzione spenta il server **rifiuti**
> dichiarando `FUNZIONE_SPENTA`. Il difetto non c'era: l'utente ha alzato l'asticella da *«non si
> vede»* a *«non c'è»*.

*Posta la notte del 10 agosto 2026, rilievo **R11.15**. La riga sta in §1.5 riga 26, ed è 🔸 — non
✅. La domanda com'era posta resta qui sotto.*

**Il fatto.** `RCP.md` §7.5 aggiunge al protocollo **due tipi di messaggio** — `BANCO_MARCA`
(`0x000F`) e `BANCO_ESITO` (`0x0010`) — e §7.5 dichiara di venire dal **rilievo R3.4** della
revisione del banco, con la motivazione da `web/rapporti/S4-ritardo-disegno.md` §5.3. ⛔ **Non c'è
né una frase né una voce**, mentre le decisioni che l'utente ha pronunciato davvero (§1.6, §1.8,
§1.9) portano qui la frase virgolettata con la data. `FASI.md` §01-filo-nudo la marcava ✅, cioè
*«deciso dall'utente»*: corretta a 🔸 il 10 agosto.

| | **A — era tua (✅)** | **B — è derivata (🔸)** |
|---|---|---|
| **che cosa cambia** | non si tocca senza tornare da te | *«si corregge senza discussione»* |
| ⛔ **il byte** | nessuno **oggi**: i due tipi ci sono in tutt'e due i casi. Cambia **la reversibilità** — con A i `0x000F`/`0x0010` restano in RCP/1 per sempre, con B si possono togliere | |
| **il peso** | quei due tipi hanno **consumato la clausola di §9** — *«oggi non esiste nessuna implementazione»* — che `RCP.md` §12 dichiara essere stata **l'ultima occasione** per aggiungere tipi di messaggio | |

**Il caso concreto.** Il giorno in cui quei due tipi diano fastidio — un'implementazione che deve
riconoscerli per essere conforme, in un ambiente dove *dipingere un quadratino sul desktop di
qualcuno* non è accettabile nemmeno dietro un interruttore — con **B** si tolgono, con **A** no. ⚠ E
c'è la metà che conta anche se la risposta è *«fate voi»*: **il tuo protocollo porta due tipi che
tu non hai chiesto**, e questa riga esiste perché tu lo sappia.

⭐ **Quale mi sembra più difendibile, e la ragione: B — 🔸.** La provenienza è dichiarata da §7.5
stessa e non è una tua frase; marcarla ✅ le darebbe una protezione che nessuna misura le ha dato
(`LEZIONI.md` §2.3-quater). ⛔ Ma è l'unica delle tre che **solo tu** puoi chiudere davvero, perché
la domanda è *se l'hai detta*.

**Come si chiude:** *«sì, era mia»* ⇒ diventa ✅ e §1.5 riga 26 riceve la frase con la data.
*«no»* ⇒ resta 🔸 dov'è, e non se ne parla più.

### 7.18 ✅ **Firefox per Android è NON SUPPORTATO** — e il percorso MSE resta come prova

*Aperta il 21 agosto 2026, e discende da §0.1-bis senza esserne risolta.*

⛔ **I fatti, misurati**: Firefox per Android non ha WebCodecs — né `VideoDecoder` né
`AudioDecoder` — quindi oggi REMOTIX lì **non disegna un pixel**, e non è una questione di codec
(la strada verso i pixel è una sola in `pagina.html`). ⭐ Ha però WebTransport e decodifica H.264
**in hardware** via MSE: la capacità c'è, manca il modo di darle i byte.

⛔ **Il prezzo, misurato** (`fasi/06`, banco `07-b57`): MSE costa **+225 ms** su Firefox e
**+415 ms** su Chrome sulla mediana, con una coda di riproduzione di 310–715 ms, contro il tetto
dichiarato di **50 ms**. ⚠ E l'inseguimento non salva: 40 salti su 150 fotogrammi.

| la lettura | che lavoro produce |
|---|---|
| *«l'utente Android deve accettare le scarse performance di Firefox»* presuppone che lì REMOTIX funzioni | ⇒ **si scrive** il percorso MSE (muxer fMP4 nel client, percorso audio a parte), e si dichiara il ritardo di un'altra classe |
| *«REMOTIX non può rincorrere i bug dei software»* | ⇒ **non si scrive niente**: Firefox Android è dichiarato non supportato finché Mozilla non porta WebCodecs, e lì si usa Chrome |

⇒ **Le due letture della stessa frase portavano a lavori opposti**, quindi non si è dedotto: si è
chiesto. ⚠ E c'era un fatto che pesava dall'altra parte: Mozilla dichiara il supporto mobile
*«still missing, which we're currently working on»*, cioè il problema potrebbe scadere da solo.

> ### ✅ **21 agosto 2026, dall'utente: si costruisce il percorso MSE.**
>
> ⚠ E la ragione per cui §0.1-bis non lo vieta sta nella differenza fra i due casi: quel principio
> parla di un motore che **rende peggio**. Qui il motore non rende peggio, ⛔ **non apre affatto** —
> l'utente lo ha detto con parole sue: *«su Android Chrome funziona bene, è Firefox a non
> funzionare per nulla (non apre il desktop remoto)»*. ⇒ Non è rincorrere un difetto di
> prestazioni: è dare al prodotto una strada dove non ne ha nessuna.
>
> ⭐ **E l'audio non è da scrivere**: la pagina ripiega già su `pcm` quando `AudioDecoder` manca
> (§4.3 lo impone a entrambi ed è la base sempre disponibile). ⇒ Il lavoro è **solo il video**.
>
> ⭐ **E il protocollo non si tocca**: sul filo passano gli stessi fotogrammi Annex-B di sempre.
> Quel che cambia è **come il client li disegna**, e il server non se ne accorge.

> ### ⛔⛔ E LA SERA STESSA LA DECISIONE È CAMBIATA — ✅ 21 agosto 2026, dopo averla provata
>
> *L'utente: «Niente da fare, troppi problemi: **disegno del desktop irregolare, input
> imprevedibile**, dichiaro Firefox per Android incompatibile con REMOTIX».*
>
> ⚠ **E la strada funziona**, misurato: il desktop si vede vivo e i tocchi arrivano al server
> (`fasi/06`, banco `07-b59` su un emulatore con Firefox 154 per Android). ⛔ Ma *«funziona»* non
> era il traguardo. Il traguardo è **§0.1-bis**: un'esperienza vicina a quella di una sessione
> locale. A un `<video>` che riproduce un flusso non si può chiedere di reagire come un
> decodificatore comandato a mano — il ritardo è di un'altra classe e il ritmo non è il nostro.
>
> ⇒ **Che cosa cambia nel prodotto**: su un browser senza WebCodecs la pagina **dichiara che non si
> può** invece di dare mezza esperienza. `VIA_MSE` non si accende più da sola: solo con
> `?disegno=mse`, che è un interruttore da banco.
>
> ⭐ **Perché il codice resta**: è misurabile, e finché Mozilla non porta WebCodecs su Android è
> **l'unica prova che il problema non era nostro**. ⛔ Alla fase 13 si decide se buttarlo — §7.16,
> «nel prodotto finale si fa pulizia».
>
> ⚠ **E resta scritto quanto è costata**: sei giri di prove sul telefono dell'utente e una giornata
> di lavoro, per una strada che non entra nel prodotto. ⭐ Non è tempo buttato del tutto — ne sono
> usciti `07-b58`, `07-b59` e §1.19 di `LEZIONI.md` — ma la lezione vera è che **la domanda «quanto
> renderà?» andava misurata prima di costruire**, e il numero c'era già: `07-b57`, centinaia di
> millisecondi contro un tetto di 50.

### 7.20 ✅ **I motori supportati, dichiarati dall'utente** — 22 agosto 2026

> *«Chrome e Firefox su Linux, e Chrome su Android sono OK. Firefox per Android è uscito dal
> progetto.»* — e subito dopo: *«**Anche Chrome per Windows è OK**.»*

⭐ **È l'elenco che il progetto non aveva ancora**, dato dall'utente sul prodotto vivo e non dedotto
da una misura:

| dove | motore | stato |
|---|---|---|
| **Linux** | Chrome | ✅ **OK** |
| **Linux** | Firefox | ✅ **OK** |
| **Windows** | Chrome | ✅ **OK** |
| **Android** | Chrome | ✅ **OK** — e §7.19 lo dettaglia: *«esperienza completa, audio e video perfetti»* |
| **Android** | Firefox | ⛔ **FUORI DAL PROGETTO** — §7.18 |

⚠ **E quel che l'elenco NON dice, scritto perché non lo si deduca**: **Firefox su Windows** non è
nominato, e nessuno l'ha mai provato. ⛔ Non è «supportato» e non è «escluso»: è **non provato**, e
va scritto così finché qualcuno non lo apre.

⭐ **E il confine di §0.1-bis regge**: *«pienamente supportato»* vuol dire **funziona, e sai in che
condizioni** — non *uguale dappertutto*. Su Firefox l'incolla col mouse costa un clic **di Firefox**
(§5-ter.9), e resta vero.

### 7.19 ✅ **Chrome per Android è PIENAMENTE SUPPORTATO** — giudizio dell'utente, 21 agosto 2026 sera

*L'utente, dopo aver usato una sessione vera dal telefono: «**Chrome su Android offre un'esperienza
completa: audio e video perfetti**».*

⭐ **È il gemello di §7.18, ed è la ragione per cui quella si poteva prendere**: dichiarare un motore
non supportato è sostenibile solo se sulla stessa piattaforma ce n'è uno che rende. Su Android
c'è, ed è giudicato — non dedotto dai contatori.

| | |
|---|---|
| che cosa chiude | ⛔ **l'ultimo difetto vero della fase 7**: la coda dell'audio a 400–420 ms. ⇒ `fasi/07-audio-e-appunti.md` §9.7 e §8 |
| ⚠ il numero resta scritto | 401 → 421 ms, `[M]` sulla prima sessione Android. Smette di essere un **difetto**, non di essere una **misura**: il metro è I8, e per l'audio I8 è l'orecchio |
| in che condizioni | Samsung DeX, Android 16, **rete di casa**, codec negoziato **HEVC in hardware**. ⏳ Il datagram su rete non locale resta non misurato |

⚠ **E questo è §0.1-bis applicato per intero**: *«pienamente supportato»* qui vuol dire **funziona, e
sai in che condizioni** — non *uguale dappertutto*.

> ### ⛔ E UN'ORA DOPO L'UTENTE HA PRECISATO, dal PC Windows — la riga «che cosa chiude» era troppo generosa
>
> *«Il ritardo di 400 ms tra audio e video in generale te lo confermo.»*
>
> ⛔ **Il difetto non è chiuso, e non è di una piattaforma**: è `AUDIO_CUSCINO_MS = 250` in
> `pagina.html` (alzato da 60 il 17 agosto per togliere i buchi, col prezzo dichiarato nel
> commento) più la catena di cattura, codifica e decodifica. ⇒ `fasi/07-audio-e-appunti.md` §8.
>
> ⭐ **Quel che questa decisione conserva**: su Chrome per Android **ogni flusso è pulito** — zero
> perdite su ogni anello, `[M]` due volte. ⚠ Quel che **non** conserva è la lettura *«e quindi non
> c'è più niente da curare sull'audio»*: un difetto di **sincronia** non appare in nessun contatore
> che guardi un flusso per volta, e questa è la seconda volta in cinque giorni che questa fase
> produce quattro anelli verdi e un'esperienza sbagliata (`LEZIONI.md` §2.7).

### 7.17 ✅ La sessione che non apre mai il canale di controllo: **5 secondi**

> ## ✅ **CINQUE SECONDI** — deciso dall'utente l'**11 agosto 2026**
>
> ⛔ **Dall'apertura della sessione WebTransport all'apertura del canale di controllo passano al
> massimo 5 s**, poi il server chiude con `TEMPO_SCADUTO` `0x0D`. ⇒ `RCP.md` §4.6, la riga che
> mancava.
>
> ⭐ **Perché 5 s, cioè lo stesso numero del primo tetto**: aprire il canale è il **primo atto
> obbligatorio** della sessione (`RCP.md` §2.5), non dipende da quanto è veloce a digitare una
> persona, e non dipende dalla rete più di quanto ne dipenda il `CIAO`.
>
> ⛔ **Che cosa chiude**: era **l'ultimo modo, in questa fase, di occupare un posto senza dire chi
> si è**. ⚠ E il tempo di inattività di QUIC non lo copriva — quello conta il **silenzio**, e una
> sessione che scrive su un altro stream non è silenziosa: teneva il posto **a tempo
> indeterminato**.
>
> ### ⭐ E qui le quattro decisioni dell'11 agosto si incastrano
>
> | | |
> |---|---|
> | **§7.15** | il canale di controllo non esiste ancora, quindi il `CONGEDO` **non si manda**: senza la condizione decisa un'ora prima, questa riga imporrebbe un byte su un canale mai nato |
> | **§7.14** | e il motivo viaggia dove viaggia sempre quando il canale non c'è: nel **codice d'errore applicativo della chiusura** (§3.1 punto 3) |
> | **§4.1-bis** | ⛔ è una chiusura decisa dal server, e **ha il suo motivo dicibile**: `TEMPO_SCADUTO`. Non è una sessione sana che viene buttata fuori — è una sessione che non è mai cominciata |
>
> ⚠ **Non serve nessun tipo di messaggio nuovo**, e conta: la finestra di §9 è chiusa dal 10 agosto
> 2026. `TEMPO_SCADUTO` c'era già.
>
> ⛔ **E resta da misurare**: `B6` guadagna un quarto caso — apri la sessione, non aprire il canale,
> e verifica che a 5 s arrivi `0x0D` **nel codice di chiusura**, non sul canale. Il banco oggi non
> ce l'ha: fino ad allora questa riga è **scritta e non provata**.

*Posta l'11 agosto 2026 da una **misura**, non da una lettura: il banco **B6** (rilievo **R12-A.25**,
e `FASI.md` §01-filo-nudo B6). Riguarda `RCP.md` §4.6. La domanda com'era posta resta qui sotto.*

**Il fatto, e sono due.** B6 ha chiuso la `[?]` **R3.27** — *da quale istante parte il primo tetto* —
e la risposta è: **dall'apertura del canale di controllo**, non dalla fine del TLS. `RCP.md` §4.6
riga 1 è stata corretta di quella parola l'11 agosto. ⛔ **Ma il banco ha dato una seconda risposta,
e dice che curare la parola non basta**: se il cronometro parte dall'apertura del **canale**, chi apre
la **sessione** WebTransport e il canale non lo apre mai **non ha addosso nessun tetto**. §4.6 non ha
una riga per quello stato: la tabella comincia da *«`CIAO` ricevuto»*, e prima del `CIAO` c'è uno
stato in cui il server non conta niente.

| | **A — un quarto tetto** | **B — nessun tetto, e si dichiara** |
|---|---|---|
| **che cosa dice** | dall'apertura della **sessione** all'apertura del **canale di controllo** passa al massimo *N* secondi, poi `CONGEDO(TEMPO_SCADUTO)` | quello stato lo copre il solo tempo di inattività di QUIC (30 s di **silenzio**), e §4.6 lo scrive invece di lasciarlo implicito |
| ⛔ **che cosa cambia sul filo** | arriva un `CONGEDO(0x0D)` — sul canale che non c'è, quindi **solo** il codice `0x0D` nella chiusura della sessione (§3.1 punto 3) — dove oggi non arriva niente | niente arriva, ed è **quel che succede oggi**: la differenza è che smette di essere un'omissione |
| **il costo** | un tetto in più da misurare, e un client lento a chiamare l'API si vede chiudere la sessione appena aperta | ⛔ una sessione che non manda `CIAO` ma **tiene il filo occupato** su un altro stream non scade **mai**: il posto resta preso |

**Il caso concreto, e non è di laboratorio.** Una pagina apre la sessione WebTransport, poi il
browser va in secondo piano o la rete cade fra i due passi. Con **A** la sessione muore con un motivo
leggibile; con **B** resta lì finché QUIC non si annoia — e se qualcosa continua a scrivere su un
altro stream, non si annoia mai. ⚠ È la connessione che *«tiene un posto e non lo dichiara a
nessuno»*, cioè la frase con cui §4.6 si apre: la sezione esiste per questo caso e non lo copre.

⭐ **Quale mi sembra più difendibile, e la ragione: A, con lo stesso numero della riga 1 — 5 s.**
Non per simmetria: perché l'apertura del canale di controllo è **il primo atto obbligatorio** della
sessione (§2.5), non dipende dall'utente, e non dipende dalla rete più di quanto ne dipenda il `CIAO`.
⛔ Ma è una riga normativa che aggiunge un tetto a un'implementazione conforme, quindi **resta ❓**
finché non la decidi: `RCP.md` §4.6 porta la riga marcata ❓ e rimanda qui, e §12 la dichiara fra le
cose che RCP/1 lascia aperte. ⭐ **Non serve nessun tipo di messaggio nuovo** — il motivo è
`TEMPO_SCADUTO`, che c'è già — e questo conta, perché la finestra di §9 è chiusa dal 10 agosto.

**Come si chiude:** un numero, o *«nessun tetto»*. Con la prima, §4.6 guadagna una riga e B6 un caso;
con la seconda, §4.6 guadagna comunque **la riga che dichiara lo stato**, perché un buco dichiarato e
un buco dimenticato non si distinguono dopo tre mesi.

### 7.21 ✅ ⭐ **I gruppi della scheda li mette REMOTIX** — deciso dall'utente, 20 settembre 2026

*Domanda dell'utente: «REMOTIX chiede che gli utenti appartengano ai gruppi video e render.
Normalmente le distro non ce li mettono, potrebbe essere un problema?» — e la risposta è sì, oggi
quell'utente **si collega e non vede niente**: `[M]` 27 ago 2026, 0 sessioni su 4 senza i gruppi,
17 su 17 con. ⛔ E nessun errore lo dice: si vede una pagina bianca.*

**La causa, ed è strutturale:** su un desktop normale il permesso sui nodi `/dev/dri` lo dà logind
con un'ACL (`uaccess`) a chi occupa un **seat**. ⇒ Una sessione remota un seat non ce l'ha di
proposito, quindi quell'ACL non arriva mai e restano **solo i gruppi**.

**La decisione dell'utente, in due pezzi:**

| quando | chi | che cosa |
|---|---|---|
| **all'installazione** | `src/provisiona.sh` | iscrive **tutte le persone già sulla macchina** — `UID_MIN..UID_MAX` LETTI da `/etc/login.defs`, e solo chi ha una shell vera: gli account di servizio restano fuori |
| **in esercizio** | il prodotto (`figlio.c`, `iscrivi_ai_gruppi_della_scheda`) | ogni utente nuovo, **alla prima connessione**, viene iscritto e il suo gestore d'utente fatto rinascere |

⛔ **E cambia una divisione che era scritta** (I7: *«il prodotto mette quel che riguarda la SESSIONE;
i conti, i gruppi, polkit e PAM stanno in `provisiona.sh`»*). Da oggi il prodotto tocca anche i
gruppi. ⇒ Le due garanzie che tengono la cosa onesta, e sono nel codice:
1. si fa **dopo** che PAM ha detto di sì — non si concede niente a chi bussa e basta;
2. **ogni iscrizione si scrive nel registro**, con nome e gruppi: un permesso dato in silenzio è un
   permesso che nessuno ricorda di avere dato.

⚠ E i nomi dei gruppi non sono inchiodati: si chiedono ai nodi (`stat -c %g`), perché `video` e
`render` sono i nomi di **questa** distribuzione.

`[M]` 20 set 2026, scatola `kde`: utente `senzagr` creato senza gruppi ⇒ col binario di prima
**zero fotogrammi**; col binario nuovo il registro dice «PRIMA CONNESSIONE: ce lo metto io»,
`id -nG` passa da `senzagr` a `senzagr video render`, e arrivano **105 fotogrammi**. Sul server
vero, `provisiona.sh` ha iscritto **3 persone** e `nicfio` è passato da `nicfio sudo` a
`nicfio sudo video render`.

⭐ **E VALE SU TUTTI I DESKTOP** — chiesto dall'utente il 21 set 2026 (*«deve funzionare per tutti i
DE, non solo per KDE»*) e misurato il 22. ⚠ Non c'era niente da estendere: l'iscrizione sta nel
**padre**, prima del `fork`, e il compositore non lo conosce nemmeno — era la **misura** a fermarsi a
kde. `[M]` 22 set 2026, inquilini senza gruppi, **browser veri** con finestra vera
(`banchi/12-client-veri.py --visibile`):

| scatola | Firefox 140 | Chrome 153 | che cosa ha fatto il prodotto |
|---|---|---|---|
| **gnome** | ⭐ PASS (1° fotogramma 1,6 s) | ⭐ PASS (1,2 s) | `id -nG`: `sgruppig`/`sgruppic` → `… video render` |
| **xfce** | ⭐ PASS (0,6 s) | ⭐ PASS (0,9 s) | `id -nG`: `sgruppix`/`sgruppiy` → `… video render` |

⛔ **E la rete non lo guardava**, perché **ogni maglia mette i gruppi al suo inquilino da sé**
(`garantisci_i_gruppi`): quando il cliente arriva, il prodotto non ha più niente da iscrivere ⇒ la
rete poteva essere tutta verde con questo pezzo rotto. ⇒ Maglia **C18**
(`banchi/11-scatole/11-c18-i-gruppi-li-mette-il-prodotto.py`), l'unica che arriva **senza** gruppi;
guasto innestato `--senza-usermod`. `[M]` 22 set 2026: VERDE e guasto VISTO su gnome e xfce.

---

## 8. ✅ Le decisioni della fase 15 — la suite funzionale e la bonifica del giro 1

*Dopo il giro 1 della suite (`fasi/15-suite-funzionale.md`, «Il giro 1»): 25 settembre 2026, mattina.
Più l'eccezione di KDE, decisa la sera del 24 insieme alla fase.*

### 8.1 ✅ La sessione KDE nasce vuota — salvo la scelta dell'utente

Deciso dall'utente, 25 set 2026 (difetto **D-005**: dopo «Esci» Plasma riapriva da solo il programma
che era aperto, mentre la pagina promette una sessione NUOVA; `[R]` il ripristino di riserva di Plasma
6.3 su Wayland, `org.kde.plasma-fallback-session-restore.desktop`).

La sessione remota KDE parte **vuota** di suo: `ksmserverrc` con `loginMode=emptySession` **nella
cartella della sessione**, non nelle impostazioni dell'utente. ⭐ Ma se l'utente in Impostazioni ha
scelto «ripristina la sessione salvata», **vince la sua scelta** (l'opzione A delle proposte).
Cura: `aa4014d` sul ramo `bonifica-15`.

### 8.2 ✅ ⭐ Le impostazioni dell'utente non si toccano — tranne blocco, riavvio, sospensione, stand-by

Deciso dall'utente, 25 set 2026, in due tempi:
- *«le impostazioni utente non si toccano»* — su nessun desktop;
- precisata la stessa mattina: *«Le impostazioni dell'utente non si toccano TRANNE quelle che
  riguardano blocco-schermo, riavvio sistema, sospensione e stand-by: queste sono impostazioni
  pericolose per altri utenti presenti sulla macchina»*.

| | dove si scrive |
|---|---|
| **blocco dello schermo, riavvio, sospensione, stand-by** | nelle impostazioni **dell'utente**, persistenti: pericolose per le altre persone sulla macchina |
| **tutto il resto** (disposizione della tastiera, voci di menu, scorciatoie, «Esci» visibile, cambio utente, Ctrl+Alt+F…) | **solo nella sessione remota**, sui quattro desktop; alla fine della sessione l'utente ritrova le sue |

⇒ Tre difetti di classe B aperti dalla decisione: **D-015** GNOME (la disposizione negoziata finiva in
`org.gnome.desktop.input-sources` del dconf dell'utente), **D-017** XFCE (canali xfconf dell'utente e
`~/.cache/sessions` cancellata), **D-018** LXQt (`~/.config/lxqt/*.conf` e voci `Hidden` in
`~/.local/share/applications`). KDE era già a posto (`kxkbrc` della sessione). Cure: `ddcf28d`,
`85697c9`, `7543c6a`, `e8115e5` su `bonifica-15`; la prova che sorveglia è **F-031B**
(`banchi/15-suite/15-f031b-impostazioni-intatte.py`: le impostazioni lette dal disco prima dell'accesso
e dopo «Esci»).

🔸 Derivato (`7543c6a`): su XFCE Sospendi, Iberna e Sonno ibrido del dialogo di «Esci» contano come
**sospensione** ⇒ sono permesse, e restano nel canale dell'utente.

### 8.3 ✅ La frase della linea caduta

Deciso dall'utente, 25 set 2026 (**D-002**: la linea cade e la pagina resta congelata col desktop, senza
una parola). Quando il trasporto si chiude senza un CONGEDO, la pagina torna al modulo e dice:

> *«il collegamento con il server si è interrotto: per rientrare scrivi di nuovo la parola d'ordine»*

Cura: `c7a67ea` su `bonifica-15`.

### 8.4 ✅ Il server spento si dice subito

Deciso dall'utente, 25 set 2026 (**D-009**: a server spento la pagina impiegava 31 s a dire «Non si
collega»). Si dice **subito**, ~1 s, dal rifiuto di rete di `/impronta`, senza aspettare i 30 s del
browser su WebTransport. 🔸 Solo il rifiuto di rete: uno stato HTTP o un corpo illeggibile restano come
prima, e un server lento non ha orologi (si aspetta la sua risposta). Cura: `e719d08` su `bonifica-15`.

### 8.5 ✅ ⭐ D-006: un decodificatore Opus nostro, in WebAssembly, per tutti i browser

Deciso dall'utente, 25 set 2026. Il difetto: Firefox con un video nella sessione ha buchi di suono
corti e ripetuti; Chrome no. `[M]` 25 set, senza l'orecchio del banco, 60 s su lxqt e kde: Firefox+video
**3-5 riarmi**, Firefox senza video 0, Chrome 0, Firefox+video in PCM 0 ⇒ il decodificatore Opus di
Firefox (WebCodecs `AudioDecoder`). Una prima cura lato pagina è stata tolta (`b40856d`): coi browser
veri peggiorava.

L'utente: *«concordo sulla soluzione D [dichiararlo], ma il problema va risolto con la soluzione B
[decodificatore Opus nostro in WebAssembly nella pagina, per TUTTI i browser], che è la scelta che ci
consente di avere un prodotto bugs-free»*.

⇒ Si dichiara, **e** si fa la B: il decodificatore Opus in WebAssembly nella pagina, **per tutti** i
browser, non un ramo per Firefox.
⛔ **Prima del giro 2.**

### 8.6 ✅ L'eccezione di KDE al riattacco a misura diversa

Deciso dall'utente il **24 settembre 2026, sera**, aprendo la fase 15 (`fasi/15-suite-funzionale.md`,
«Le decisioni dell'utente»). Al riattacco a misura diversa (F-018, percorso C):
- su **GNOME, XFCE, LXQt** la tela prende la misura nuova e il desktop la segue (sfondo, pannello);
- su **KDE** la tela resta quella vecchia e **il browser riscala**: è l'**atteso**, non un FAIL.

Conferma da parte dell'utente, per la suite, del ripiego di §5.0-bis (🔸 fino a oggi): KWin di Debian
stabile (6.3.6; fino a 6.7.4 nessun ramo rilasciato ha il ridimensionamento a caldo) non cambia misura
a sessione viva, e riavviarlo distruggerebbe la sessione. `[M]` giro 1: F-018 e P-C **PASS** su KDE
coi due browser, con quest'atteso.

## 9. ✅ Le decisioni della fase 16 — stress e capacità

*Prese dall'utente il 25 e 26 settembre 2026. Il racconto, le misure e le evidenze stanno in
`fasi/16-stress-e-capacita.md` (§2, §9, §17); qui la decisione e basta.*

### 9.1 ✅ Il registro va nel journal di sistema

Con `--journal` il prodotto scrive i suoi **eventi** anche nel journal (`journalctl -t remotix`), con i
campi `REMOTIX_AREA`, `REMOTIX_INQUILINO`, `CODE_FILE`, `CODE_LINE` e la gravità presa dal segno in
testa alla riga (⛔ = errore, ⚠ = avviso). La **parlantina** resta solo nel file. Il file resta per chi
amministra.

### 9.2 ✅ Nel registro non entra mai quel che l'utente batte

Né caratteri né codici di tasto: si scrive «un carattere», «tasto premuto/rilasciato». Il codice resta
solo per i **modificatori** e i **pulsanti del mouse**. Vale anche per il carattere non producibile
(RCP §7.3): si dichiara **che** c'è stato, non **quale**.

### 9.3 ✅ La campagna: salita a gradini, tetto a 17, soglie §9

Gradini 1 → 4 → 8 → 12 → 16 con la ricerca a metà (non un utente alla volta); tetto delle sessioni a
**17** durante la campagna, perché il 17° è solo il controllo corto; soglie di §9 approvate, con il
video in proporzione alla sua frequenza e la memoria dei browser che si registra ma non classifica.

### 9.4 ✅ Firefox disegna con WebGL (anomalia A1) — decisione del 26 set 2026, mattina

La campagna ha misurato che in Firefox la strada di disegno di serie (`bitmaprenderer`, scelta il 20
ago 2026 contro i quadrati della tela 2D) rilegge ogni fotogramma dalla GPU (~34 ms a 4K) e fa saltare
l'11–50 % dei fotogrammi già con un utente. L'utente ha scelto di **curare adesso** (strada WebGL2)
invece di chiudere la campagna col difetto dichiarato: suite corta + prove della tela + **suo sguardo
contro i quadrati**, poi si rifanno le salite interessate.

### 9.5 ✅ Il rallentamento della Radeon in 4K (A3) è del driver: si documenta, non si aggira — 29 set 2026

Esclusi con misure frequenza, VPP, barriera del compositore ed EFC, il ritardo sta dentro la codifica
del VCN (gruppi di 5 fotogrammi da ~31 ms, una sessione alla volta). Parola dell'utente: *«è fuori dal
nostro ambito. Se in futuro il problema dovesse essere risolto allora REMOTIX diverrà più capace di
reggere un maggior carico»*. ⇒ Nessun aggiramento nel prodotto; il 4K della Radeon si dichiara limitato
dal driver; il difetto è documentato nei minimi particolari in `fasi/16-a3-radeon-vcn.md`, perché
l'utente possa decidere di aiutare gli sviluppatori del driver.
Aggiunta del 29 set 2026: Mesa 26.1.6 non cura (100 e 102 lenti contro 100 e 105). Parola dell'utente:
*«stiamo andando fuori scope, questo è un problema dei driver AMD, non di REMOTIX. Aprirò a questo scopo
un progetto apposito»*. ⇒ In REMOTIX il lavoro su A3 si chiude qui: niente riproduzione minima (§6.2 del
dossier) né altri esperimenti; il dossier e il ramo `a3-esperimenti` sono il punto di partenza del progetto nuovo.

---

### 9.6 ✅ Il logo ufficiale di REMOTIX — 29 set 2026

Parola dell'utente: *«è il logo ufficiale del progetto»*. ⇒ `grafica/logo/remotix-logo.png`
(PNG 2172×724, sha256 `192ce831…384104`), in testa al `README.md`. È l'originale: le varianti
(icona, favicon, versione scura) si ricavano da questo, non lo sostituiscono.


## 10. ✅ REMOTIX su Linux in generale, e l'installatore — 29 set 2026

### 10.1 ✅ Non solo Debian: prima un'indagine sulle distribuzioni

Parola dell'utente: *«al momento REMOTIX è stato sviluppato su Debian Trixie, ma l'obiettivo è farlo
girare su Linux in generale. Per ottenere questo risultato, e quindi avere basi solide per costruire
l'installer, è necessario fare un'indagine approfondita sulle principali distro»*. Famiglie:
Debian/Ubuntu (e Mint), Fedora/RHEL (Rocky, Alma), Arch (Manjaro), openSUSE (aggiunta nell'indagine).
⚠ Già visto nel codice: `src/remotix.pam` usa `@include common-auth`, che esiste solo su Debian e Ubuntu.

### 10.2 ✅ L'installatore è professionale, di assoluta eccellenza

Parola dell'utente: *«REMOTIX dovrà essere dotato di un sistema di installazione professionale, di
assoluta eccellenza»*. ⇒ È un requisito del prodotto, non una rifinitura: l'installatore si progetta
sull'indagine di §10.1 e su come installano i prodotti migliori, e si misura come il resto.

### 10.3 ✅ Le prove dell'installatore in macchine virtuali, una per desktop

Parola dell'utente: *«stavolta non dobbiamo misurare le performance, ma il corretto funzionamento
dell'installer, quindi la potenza bruta della GPU non serve. Passiamo dai container alle VM»*; e *«4 VM
distinte, esempio Ubuntu/GNOME, Ubuntu/KDE, Ubuntu/XFCE, Ubuntu/LXQt»*. ⇒ `fasi/17-l-installatore.md` §7.

### 10.4 ✅ Il motore d'installazione in otto fasi

Proposta dell'utente, adottata: PREFLIGHT · COMPATIBILITY · PLANNING · CONSENT & SAFETY · ACQUISITION ·
INSTALLATION & CONFIGURATION · VERIFICATION & CERTIFICATION · COMMIT / ROLLBACK. Con tre regole: le fasi
5-6 le esegue il gestore di pacchetti della distribuzione; il ritorno indietro è nostro (registro delle
azioni); il consenso può arrivare da un file. Rafforzata su richiesta dell'utente (*«migliorala nei punti
che ritieni deboli»*): fase 0 TRUST, tre esiti di compatibilità per desktop, il piano come documento
con «fai / verifica / annulla» per ogni azione, niente si installa prima che tutto sia scaricato,
accensione fra verifica statica e dal vivo, ripresa di un'operazione interrotta. ⇒ `fasi/17-l-installatore.md` §6.0.

### 10.5 ⛔ SUPERATA da §10.31 (5 ott 2026), per la GUI — TUI e GUI sono irrinunciabili

Parola dell'utente: *«su TUI e GUI dico che è un requisito irrinunciabile»*. ⇒ Tre interfacce (CLI, TUI,
GUI) su un solo motore, nessuna logica d'installazione nelle interfacce, la GUI come l'utente con
polkit. Lo strumento è la decisione D12. `fasi/17-l-installatore.md` §6.6.1.

### 10.6 ✅ Le dipendenze che mancano le porta REMOTIX — con un'eccezione e un confine

Parola dell'utente (29 set 2026): *«usiamo questa regola generale per non impazzire: se ci sono
pacchetti/dipendenze assenti da una particolare distro, REMOTIX le deve includere e/o scaricare»*.

- **La regola**: una libreria o un attrezzo di cui REMOTIX ha bisogno, **assente o troppo vecchio** nella
  distribuzione, lo porta REMOTIX (dentro il binario o nel suo pacchetto). Se la distribuzione ce l'ha
  giusto, si usa il suo (gli aggiornamenti di sicurezza sono suoi). ⇒ **D2 chiusa: sì**, ngtcp2 e nghttp3
  dentro, con gli aggiornamenti di sicurezza a carico nostro.
- ⛔ **L'eccezione: i codec brevettati** (H.264: x264, ffmpeg completa, Mesa coi codec). REMOTIX non li
  include né li scarica da sé — sarebbe distribuirli; restano all'archivio esterno riconosciuto (RPM
  Fusion, Packman) aggiunto dal motore **col consenso** (D5).
- ⛔ **Il confine: i desktop.** Un desktop che la distribuzione non ha (XFCE e LXQt su Alma/RHEL) non lo
  porta REMOTIX: quella combinazione resta fuori dalla matrice.

### 10.7 ⛔ *(superata da §10.36)* Senza desktop: o lo si installa (col consenso), o REMOTIX non si installa

Proposta dell'utente (29 set 2026), adottata: *«se REMOTIX non trova nessun desktop installato, o chiede di
installarlo all'utente oppure REMOTIX non si installa»*. Il desktop viene dagli archivi della
distribuzione, si installa senza schermata d'accesso locale né avvio in grafica, ed è dichiarato come
azione «al meglio». `fasi/17-l-installatore.md` §6.6 e R38.

### 10.8 ✅ Ubuntu 24.04 fuori: si parte dalla 26.04

Parola dell'utente (29 set 2026): *«partiamo dalla 26.04»*. Su 24.04 solo GNOME sarebbe stato possibile, al
prezzo di portare dentro OpenSSL 3.5 (e i suoi aggiornamenti di sicurezza) e di due adattamenti per
ffmpeg 6.1 e libei 1.2. Con lei resta fuori Mint 22. La matrice scende a 26 macchine.

### 10.9 ✅ Il principio: un prodotto nuovo, su tecnologie di nuova generazione

Parola dell'utente (30 set 2026): *«la scelta di lasciare fuori certe versioni delle distro è coerente con
lo spirito del progetto: si tratta di un prodotto nuovo che adotta tecnologie di nuova generazione, è una
scelta di design netta»*. ⇒ Wayland, QUIC/WebTransport, i desktop nelle versioni che li supportano; niente
X11 né librerie di ripiego per inseguire versioni vecchie.

E il ciclo di vita, perché la scelta resti netta nel tempo:
- una versione nuova di una distribuzione **entra** nella matrice quando ha i componenti minimi
  (`fasi/17-l-installatore.md` §3.1) e passa il giro sulle VM;
- una versione **esce** quando la distribuzione smette di aggiornarla: niente supporto oltre la vita che le
  dà chi la fa.

### 10.10 ✅ Il ritmo: una versione all'anno per le novità, la manutenzione quando serve; e l'aggiornamento automatico

Parole dell'utente (30 set 2026): *«la mia intenzione è quella di aggiornare REMOTIX almeno una volta
l'anno»*; e, visti i ritmi delle distribuzioni: *«bisognerà pensare per REMOTIX ad una funzione di
auto-aggiornamento in base alla distro su cui è installata»*.

- **Due binari**: la **versione annuale** (le novità, suite completa e giro intero sulle VM) e gli
  **aggiornamenti di manutenzione** senza novità, quando servono: correzioni di sicurezza delle librerie che
  REMOTIX porta dentro (§10.6), ricostruzioni per le distribuzioni a rilascio continuo (Arch, Tumbleweed:
  ogni cambio di ffmpeg), e il **catalogo** firmato — che si aggiorna da solo, senza un REMOTIX nuovo, e fa
  entrare le versioni nuove delle distribuzioni a metà anno.
- **L'aggiornamento automatico passa dal gestore di pacchetti della distribuzione**, alimentato dai nostri
  archivi firmati (T8): ⛔ REMOTIX non scarica né sostituisce da sé il proprio binario (due verità su che cosa
  è installato, e un bersaglio). Un timer di REMOTIX controlla ogni giorno l'archivio e il catalogo; ogni
  aggiornamento passa dal percorso che non chiude i desktop (T7).
- 🔸 **D14, aperta**: che cosa si applica da solo — proposta: sicurezza e ricostruzioni automatiche, la versione
  annuale su scelta dell'amministratore; alternativa: solo avviso.

### 10.11 ✅ Flatpak e AppImage accantonati: pacchetti nativi dal nostro archivio

Parola dell'utente (30 set 2026): *«accantoniamo l'idea flatpak/appimage. Continuiamo sulla strada originale,
alla fine mi sembra quella più semplice e coerente»*. ⇒ REMOTIX si distribuisce in **pacchetti nativi** negli
**archivi firmati di REMOTIX** (tutto il materiale da noi, installato dal gestore di pacchetti della
distribuzione); l'installatore dirige, non copia file. Uno studio su Flatpak/AppImage era partito ed è stato
fermato. ⚠ Resta da guardare, alla decisione D9 (distribuzioni immutabili), la strada di systemd fatta per i
servizi di sistema (`systemd-sysext`, portable services).

### 10.12 ✅ L'installatore è l'unica via per installare REMOTIX

Parola dell'utente (30 set 2026): *«l'unica via per installare REMOTIX è l'installer»*. Siccome un pacchetto
in un archivio si può sempre installare a mano, la regola si fa valere **per costruzione**:
1. **il pacchetto porta solo i pezzi, inerti**: programma, pagina, file di configurazione; non accende il
   servizio, non tocca gruppi né firewall; le tre cinture ci stanno **spente** (in `/usr/share/remotix/`), le
   attiva il motore col consenso (D4);
2. **l'installatore monta i pezzi** (gruppi, cinture, firewall, desktop, accensione) e tutto passa dal
   **suo** registro: una sola traccia, una disinstallazione più pulita;
3. **due vie sole: l'installatore, oppure il codice sorgente a mano** (scaricare il codice, cercarsi le
   dipendenze, installarle, tirare su i servizi, configurarli — a proprio rischio). Parola dell'utente, 30
   set: *«o usa l'installer o deve scaricarsi il codice a mano, andarsi a cercare i pacchetti con le
   dipendenze e installarseli, tirar su i servizi, configurarli»*. ⇒ REMOTIX non prevede una via intermedia:
   **né blocchi né opzioni apposta** per chi parte senza installatore (corretto due volte il 30 set: prima
   era un rifiuto secco, poi un'opzione esplicita). Resta solo un'informazione per l'assistenza: `remotix
   stato` dice se l'installazione è **certificata dall'installatore** o no;
4. **gli aggiornamenti automatici restano** (§10.10): il gestore di pacchetti aggiorna i pezzi, poi richiama
   l'installatore, che verifica e riaccende senza chiudere i desktop.

### 10.13 ✅ REMOTIX sarà open source

Parola dell'utente (30 set 2026): *«REMOTIX sarà opensource»*. Conseguenze da decidere a suo tempo:
🔸 **la licenza** (GPL o permissiva; pesa anche sui codec: x264 è GPL, `DECISIONI.md` ~§5113 aveva già escluso
x265 come ripiego); **D10** (dove si costruiscono i pacchetti): con un progetto pubblico diventa possibile
OBS di openSUSE; **D11** (la chiave): la fiducia pubblica richiede una chiave madre custodita bene.

### 10.14 ✅ L'installatore è un programma solo, monolitico

Parola dell'utente (30 set 2026): *«l'installer è un programma che non chiama altri sottoprogrammi strani. È un
sistema complesso e monolitico»*. ⇒
- **un solo eseguibile** (`remotix-install`): motore, CLI, TUI e GUI; niente script né programmi di appoggio
  nostri;
- con i servizi del sistema (systemd, logind, firewalld, polkit) parla **dall'interno**, attraverso le loro
  interfacce ufficiali (D-Bus), senza lanciare programmi;
- **un elenco chiuso di programmi di sistema** si lancia solo dove non c'è un'interfaccia stabile: il gestore
  di pacchetti della distribuzione (`apt`, `dnf`, `zypper`, `pacman` — regola 1 del motore) e i comandi dei
  gruppi (`usermod`, `gpasswd`); col percorso completo, argomenti fissi, ogni chiamata nel registro;
- **la GUI** gira come l'utente (non da root: Wayland), e per le operazioni da amministratore lo stesso
  eseguibile **rilancia sé stesso** con i permessi chiesti a polkit — un file, due ruoli.

### 10.15 ⛔ *(superata da §10.35)* L'installatore parla italiano e inglese, secondo la lingua del sistema

Parola dell'utente (30 set 2026): *«l'installer lo rendiamo bilingue: italiano e inglese. La scelta della
lingua la rendiamo coerente con le impostazioni linguistiche dell'OS sottostante (variabili di ambiente)»*.
⇒ la lingua si legge nell'ordine standard `LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`: italiano se la prima
indicata è italiano, **inglese in tutti gli altri casi** (anche tedesco, francese…); ⚠ quando l'installatore
si rilancia con i permessi (polkit ripulisce l'ambiente) la lingua scelta si **passa esplicitamente** alla
parte da amministratore; nell'installazione senza domande il file di risposte può fissarla. I **codici**
`RX-…` restano uguali nelle due lingue: sono quelli che si cercano nel manuale e nell'assistenza.

### 10.16 ✅ La disinstallazione: l'amministratore avvisa, l'installatore chiude le sessioni REMOTIX e pulisce

Parola dell'utente (30 set 2026): *«è un'operazione fatta dall'admin del server. La soluzione più pulita è che
l'admin avverta gli utenti nelle modalità classiche (email, WhatsApp…). Poi, quando avvia la
disinstallazione, l'installer chiude le sessioni REMOTIX degli utenti e i loro processi e avvia la pulizia
del sistema»*. ⇒ Nessun sistema di avvisi in REMOTIX e **nessuna domanda in più**: chi è ancora collegato viene
chiuso e basta (*«erano già stati avvertiti prima»*); il piano porta solo la riga «chiudo le sessioni
REMOTIX ancora aperte (N)»; si chiudono le sessioni REMOTIX e i programmi nati dentro di esse, **non** gli altri processi
dell'utente (una sua sessione locale o ssh resta). `fasi/17-l-installatore.md` §6.5-bis, R43.

### 10.17 ✅ Un sistema per avvisare gli utenti collegati: progetto a parte, fuori da REMOTIX

Parola dell'utente (30 set 2026): *«la disinstallazione mi ha fatto venire in mente che serve un sistema per
avvisare gli utenti collegati a un sistema. Ma questo è un progetto a parte che non riguarda REMOTIX»*. ⇒ In
REMOTIX niente avvisi (§10.16). Nota per quel progetto: le sessioni REMOTIX sono desktop normali, quindi un
avviso sul desktop dell'utente le raggiungerebbe senza che REMOTIX ne sappia niente.

### 10.18 ✅ D3: REMOTIX rispecchia l'autenticazione del sistema (PAM), blocco dei conti compreso

Parola dell'utente (30 set 2026): *«non voglio che REMOTIX si disallinei rispetto all'autenticazione di default
del sistema, deve rispecchiare PAM»*. ⇒ Il file PAM di REMOTIX usa **la stessa pila dell'accesso remoto
standard** della distribuzione (quella di ssh: `system-remote-login` su Arch, `password-auth` + `postlogin` su
Fedora/Alma, `common-*` su Debian/Ubuntu/openSUSE), con quel che contiene: `pam_faillock` dove la
distribuzione lo ha (resta il rischio del blocco del conto a distanza, lo stesso di ssh, governato
dall'amministratore in `/etc/security/faillock.conf`), e **`pam_selinux` su Fedora/Alma come ssh** ⇒ il rifiuto
SELinux del figlio si cura con una **regola SELinux di REMOTIX** (come Cockpit), non togliendo la riga (T6). Il
ban per indirizzo di REMOTIX (§1.9: 3 fallimenti in 5 minuti ⇒ 12 ore) resta, in aggiunta. Unica differenza
voluta: **root escluso**, come ssh di serie (`PermitRootLogin` senza password) — ✅ confermato dall'utente:
*«che root non entri da REMOTIX è corretto, è lo stesso sistema di sicurezza di ssh»*.

### 10.19 ⛔ SUPERATA da §10.31 (5 ott 2026) — D12: la finestra dell'installatore si disegna con Gio, dentro lo stesso programma

Scelta dell'utente (30 set 2026), fra tre strade: Chromium incorporato (indipendente, ma due programmi e un
motore web da mantenere), WebKitGTK della distribuzione (dipendenza, programma non più unico), **Gio**, una
libreria per interfacce in Go che disegna tutto da sé — *«ok per Gio»*. Nasce da una sua proposta: *«schermate
con un motore di rendering integrato, così da rendere l'installer indipendente dai browser dell'utente»*. ⇒ La
GUI vive nello stesso programma del motore, identica sui quattro desktop, senza browser; le schermate non sono
HTML ma si riscrivono in Go **dal prototipo** (colori, caratteri, disposizione, parole comuni, «password»). La
TUI, nel terminale, con una libreria Go dello stesso programma. ⚠ Da verificare nella costruzione: Gio sotto
Linux usa le librerie grafiche del sistema (Wayland, X11, EGL) — il motore deve continuare a partire anche su
una macchina senza desktop (dove si usa la TUI).

### 10.20 ✅ D5, D6, D8, D13 — parole dell'utente (30 set 2026)

- **D5**: *«si chiede il consenso e si installa. Se l'utente nega il consenso allora REMOTIX non si installa»* ⇒
  dove serve un archivio esterno per la codifica (RPM Fusion, Packman, EPEL), il consenso è richiesto; un «no» ⇒
  BLOCCATA, niente toccato.
- **D6**: *«l'installer apre la porta che l'utente ha scelto sul firewall (per il router ovviamente non può essere
  REMOTIX a pensarci, a meno che non vogliamo supportare UPnP)»* ⇒ la porta si apre sul firewall della macchina;
  il router resta all'amministratore (UPnP: vedi la nota sotto).
- **D8**: *«l'utente vede il desktop originale di Ubuntu (o altrimenti saremo costretti a implementare un nostro
  session manager)»* ⇒ su Ubuntu la sessione **`ubuntu`** (quella che si vede davanti al monitor), non il GNOME
  «vanilla»: REMOTIX avvia la sessione GNOME **di serie della distribuzione**; niente `gnome-session` in più.
- **D13**: *«di base sì, ma potremo farci dei piccoli miglioramenti»* ⇒ il prototipo è la base della GUI.

⚠ Nota su UPnP (D6): aprire da sé una porta sul router renderebbe il server raggiungibile da internet senza che
l'amministratore l'abbia deciso, e molti router lo tengono spento per sicurezza ⇒ proposta: **niente UPnP**; il
benvenuto dice quale porta inoltrare sul router, TCP e UDP.

### 10.21 ✅ D11 semplificata: una chiave sola, quella dell'archivio

Parole dell'utente (30 set 2026): *«stiamo complicando le cose. L'installer originale che l'utente scarica avrà
un codice sha256 che l'utente potrà controllare … per i pacchetti l'installer usa il package manager del
server»*; e *«i dati dell'installer restano su un nostro repository, così siamo al sicuro»*. ⇒
- **una sola chiave**: quella che firma i pacchetti e l'archivio di REMOTIX — indispensabile, perché apt, dnf,
  zypper e pacman rifiutano un archivio di terzi non firmato;
- **via la seconda catena** (motore e catalogo firmati a parte, sottochiavi, revoche): l'installatore scaricato
  a mano si verifica con lo **sha256** pubblicato (HTTPS); il **catalogo** viaggia dentro il pacchetto
  `remotix-install` e si aggiorna come ogni pacchetto, dal nostro archivio;
- resta da decidere solo **dove si custodisce quella chiave** e la sua copia di riserva: insieme a D10.

### 10.22 ⛔ SUPERATA da §10.30 (5 ott 2026) — La licenza: PolyForm Noncommercial — anche l'uso interno delle aziende è vietato (30 set 2026)

> ⛔ **Superata il 5 ott 2026 (§10.30)**: il codice diventa chiuso, con trial e versione full a pagamento. Resta
> valido quel che qui riguarda ffmpeg (tolto nella fase 18) e la scelta di procedere senza legale.

✅ **Confermata dall'utente**: *«PolyForm Noncommercial mi sembra adatta ai miei obiettivi attuali»*. Il file
`LICENSE` si mette al momento della pubblicazione, col **testo ufficiale copiato senza modifiche** dal sito del
progetto PolyForm. La tappa per togliere ffmpeg resta: è la condizione perché la licenza non urti la GPL.

Parole dell'utente: *«REMOTIX è un prodotto opensource. Si può usare liberamente e redistribuire liberamente.
Il codice si può modificare e redistribuire ma citando progetto/codice originale. È vietato l'uso
commerciale. Il codice non può essere modificato e redistribuito a pagamento»*; *«le aziende non possono
usarlo come strumento di lavoro, ne trarrebbero un vantaggio economico»*; *«non voglio accollarmi le spese per
un legale»*.

- ⚠ Una licenza con divieto commerciale **non è «open source»** secondo la definizione ufficiale (OSI): è «a
  codice disponibile». Il nome da usare va scelto di conseguenza.
- **La licenza**: **PolyForm Noncommercial 1.0.0**, il testo originale **senza modifiche** (scritto da
  avvocati, gratuito, fatto per il software): uso, modifica e ridistribuzione per scopi non commerciali, con la
  citazione dell'originale; vietato alle aziende come strumento di lavoro e vietata la vendita.
- ⛔ **Il conflitto con ffmpeg**: REMOTIX usa la libavcodec della distribuzione, costruita sotto **GPL** su
  Debian, Ubuntu, Arch e con RPM Fusion/Packman; una licenza non commerciale non è compatibile con la GPL. ⇒
  **Tappa nuova (dopo la chiusura dell'installatore): togliere ffmpeg da REMOTIX** — la codifica sulla scheda
  direttamente con **libva** (MIT), il ripiego software con **OpenH264** (BSD) al posto di x264. Dopo, tutte le
  dipendenze sono permissive (MIT, BSD, Apache) e la licenza — come un'eventuale vendita del prodotto —
  non ha più conflitti.
- **Senza legale** (scelta dell'utente): solo licenze standard non modificate, nessuna dipendenza GPL, il file
  delle licenze dei componenti generato dallo SBOM, e un accordo standard per chi contribuirà (per restare
  proprietario di tutto il codice, condizione di una vendita). Rischio residuo basso, dichiarato.
- Una **vendita** del prodotto cede i diritti sul **nostro** codice; ffmpeg non è nostro e, tolta la
  dipendenza, non la tocca. I **brevetti** dei codec (H.264, HEVC) restano una questione a parte per chi
  vende.

### 10.23 ✅ D14: REMOTIX si aggiorna col sistema — niente sistema di aggiornamento nostro

Parole dell'utente (30 set 2026): *«una volta installato sul server un apt upgrade si occupa del resto dei
pacchetti»*; *«resta solo la questione di rigenerare l'installer»*. ⇒
- REMOTIX (e il pacchetto `remotix-install`) si aggiornano **quando l'amministratore aggiorna il sistema**
  (`apt upgrade`, `dnf upgrade`, `zypper up`, `pacman -Syu`), o con gli aggiornamenti automatici della
  distribuzione se lui li ha accesi — come ogni altro programma del server. **Via il timer** `remotix-aggiorna`
  e la domanda «che cosa si aggiorna da solo» (sostituisce §10.10, punto «aggiornamento automatico»).
- Restano nel **pacchetto**: il riavvio che non chiude i desktop (T7); su Arch/Tumbleweed il legame al soname di
  ffmpeg che blocca un aggiornamento incompatibile finché non ricostruiamo; il ritorno indietro coi comandi del
  gestore.
- **A ogni versione**, un solo comando di rilascio: ricostruire i pacchetti delle tre famiglie, ricostruire
  l'installatore (le due costruzioni) e pubblicarne lo sha256, aggiornare il catalogo (dentro `remotix-install`),
  firmare e pubblicare l'archivio (sul VPS, D10).

### 10.24 ✅ L'aggiornamento è del sistema, e dell'amministratore — non un problema di REMOTIX

Parole dell'utente (30 set 2026): *«un admin avvisa gli utenti che il giorno X verrà effettuato un
aggiornamento del sistema, quindi gli utenti collegati potrebbero aspettarsi delle interruzioni del servizio.
L'aggiornamento del sistema dev'essere un problema di REMOTIX? Secondo me no»*; *«io parlerei di
aggiornamento del sistema, non di REMOTIX»*. ⇒ Quando e come aggiornare, e l'avviso agli utenti (anche con
**AMS**, il progetto a parte dell'utente: messaggi dagli amministratori agli utenti con conferma di lettura),
sono dell'amministratore. A REMOTIX resta solo di **non chiudere da sé i desktop** quando il suo pacchetto
viene aggiornato insieme al resto (R7, già garantito dalla T7). **R8 (la soglia di tempo) è tolta.**

### 10.25 ✅ Priorità: togliere ffmpeg, prima di T10 — e le prove col massimo parallelismo

Parole dell'utente (30 set 2026): *«se togliere ffmpeg non comporta impatti su REMOTIX leviamolo pure»*; *«con
la sostituzione di ffmpeg dovremo rifare tutti i test: di funzionalità e di performance»*; *«diamo priorità a
ffmpeg, a condizione che i test vengano svolti, dove possibile, con il massimo parallelismo. Per i test
funzionali vanno bene 4 scatole con i 4 DE»*. ⇒ **Fase 18** (`fasi/18-senza-ffmpeg.md`): libva diretta per la
codifica sulla scheda, OpenH264 e SVT-AV1 per il ripiego software, libopus diretta, conversione dei colori
senza libswscale. **Condizione**: entra solo se indistinguibile — suite completa della fase 15 verde sulle 4
scatole in parallelo, campagna della fase 16 (una configurazione alla volta: le prestazioni non si misurano in
parallelo) con ritardo e qualità uguali a oggi; altrimenti resta ffmpeg e si riapre la licenza. Poi
l'installatore adeguato alle nuove dipendenze, e **T10 una volta sola** sul prodotto definitivo.

### 10.26 ✅ Fase 18: le scelte dell'utente del 30 set

- **Le misure di prestazione escono dai documenti** (*«con questo cambio architetturale i numeri sono
  completamente invalidati»*): subito dai documenti del prodotto; dal diario a fase 18 riuscita. Le soglie
  restano come **obiettivi di progetto**, non promesse misurate (SPECIFICHE §3).
- **D5 resta**: un «no» al deposito dei driver (RPM Fusion, Packman) blocca l'installazione anche senza
  ffmpeg, quando il video potrebbe andare in software.
- **Niente AV1 come ultimo ripiego**: senza scheda e senza un OpenH264 vero (l'installatore lo mette
  sempre) REMOTIX **lo dichiara** all'avvio col rimedio; il browser non riceve codec che il server non sa fare.
- ✅ **H.264 resta** (parola dell'utente, 30 set): la ragione d'origine (Firefox per Android) è caduta con §7.18,
  ma **Firefox su Linux** non decodifica HEVC e lavora in H.264; senza, gli resterebbe solo AV1, che le schede
  Intel del server non codificano. I brevetti di H.264 restano una questione di chi vende (§10.22); OpenH264 è
  BSD e lavora solo senza scheda.
- ✅ **Si ripetono solo le due misure che il cambio ha toccato** (parola dell'utente, 30 set): il confronto
  relativo vecchio/nuovo, stessa macchina e stesse immagini, per la codifica **senza scheda** e per la scheda
  con i pixel **dalla memoria**. La copia zero è risultata identica (byte, qualità, tempi del codificatore) e
  non si rimisura; il resto delle prove di prestazione resta tolto.
- ✅ **I limiti di OpenH264 non sono limiti del prodotto** (30 set, verificato sulle SPECIFICHE): niente senza
  perdita e H.264 senza scheda fino a 4096×2304 — le SPECIFICHE chiedono il 4K e non nominano il senza perdita.
  Sono differenze rispetto a x264, non rispetto ai requisiti.

### 10.27 ✅ La scheda si usa SEMPRE, NVIDIA compresa — requisito dell'utente (1 ott 2026)

Parole dell'utente: *«io avevo chiesto una cosa sola: che remotix sfruttasse l'accelerazione hardware della
macchina su cui viene installato»*; *«non è accettabile che un utente abbia una 5070 e si ritrova con remotix
che gira su CPU»*. ⇒ **Requisito**: su una macchina con una scheda capace di codificare H.264/HEVC, REMOTIX
codifica **sulla scheda**, qualunque sia il produttore. Oggi Intel e AMD sì (VA-API); **NVIDIA no** (il driver
proprietario non codifica via VA-API: si ripiegava sul processore, già prima della fase 18).
- 🔸 Proposta (da confermare): **NVENC** per NVIDIA, aperta a richiesta come OpenH264 (intestazioni MIT,
  libreria del driver NVIDIA); VA-API resta per Intel e AMD; il processore solo senza scheda capace.
  Vulkan Video scartato per ora: `[M]` 1 ott, la codifica Vulkan c'è sulla Radeon (RADV, Mesa 25.0) ma sulla
  Intel UHD 770 solo dietro `ANV_DEBUG=video-encode` anche con Mesa 26.2.3 (sperimentale).
- ⚠ Serve una NVIDIA vera per provarla: nel laboratorio non c'è.
- ✅ **Vulkan per primo** (parola dell'utente: *«la codifica deve avvenire con strumenti standard, preferibilmente
  con Vulkan, che accomuna tutte e 4 le architetture»*): la strada si sceglie **per capacità**, non per marca —
  1) Vulkan Video se la scheda lo offre (oggi AMD, NVIDIA; Intel quando Mesa lo rende stabile), 2) VA-API
  (oggi Intel, integrata e Arc). NVENC scartato. 🔸 l'opzione sperimentale `ANV_DEBUG=video-encode` su Intel
  solo come prova, non di serie.
- ✅ **Niente processore** (parola dell'utente: *«niente cpu senza scheda. Ad oggi anche le vm possono supportare
  accelerazione hw»*): via il ripiego software (`src/ripiego.c`: OpenH264, SVT-AV1) e le sue dipendenze e
  depositi (Cisco, `noopenh264`, EPEL per SVT-AV1); senza una scheda capace REMOTIX **non si installa** — il
  controllo preliminare lo dice prima, con la ragione. Le VM con scheda passata o virtuale (passthrough, vGPU)
  vanno; le VM senza scheda no. ⇒ Le VM di T10 provano solo il rifiuto pulito; le prove complete nei contenitori
  con la scheda vera (come §7.5 della fase 17).
- ✅ **La tela al massimo 4096 pixel di larghezza** (parola dell'utente: *«4096 max di larghezza va benissimo, non ho
  mai preteso di più (è anche superiore al 4K, che ha larghezza massima di 3840)»*): H.264 sulla scheda Intel si
  ferma lì e Firefox riceve solo H.264. Una finestra più grande riceve la tela ridotta al massimo, non un rifiuto.
  ⛔ Il 3K come massimo è stato proposto e scartato (non toglie problemi di licenza né di compatibilità; peggiora
  i monitor 4K).
- ✅ **La famiglia Red Hat resta** (Red Hat, Alma, Rocky; parole dell'utente: *«il problema delle licenze è di chi
  installa remotix, non del progetto»*; *«va bene, ma sarà meglio annotare bene queste limitazioni»*): solo **Intel**
  (con RPM Fusion EL ed EPEL, col consenso D5), solo **GNOME e KDE**; ⛔ **AMD non supportata** (RPM Fusion non ha
  il driver AMD con la codifica per EL; su Fedora sì). Si prova su Alma. Tabella completa: `SPECIFICHE.md` §11.4-bis.
- ⚠ **NVIDIA**: l'utente non può comprare la scheda; la strada Vulkan resta «non provata» finché non si prova
  (macchina a noleggio, a sua scelta, o un utente che ce l'ha).
- ⭐ **Android**: Chrome su Android entra nella suite della fase 19 (emulatore sul server); Firefox Android resta
  fuori (§7.18).
- ⇒ **Fase 19** (`fasi/19-nvidia.md`). Le misure rifatte della fase 18 si fermano dove sono (parola
  dell'utente: *«basta misure»*).

### 10.28 ✅ La tastiera del telefono si apre solo a richiesta — scelta dell'utente (2 ott 2026)

Parole della scelta: *«Tastiera solo a richiesta»*. `[M]` 2 ott, S23+ con Chrome 154, telefono in mano: la
tastiera a schermo si apriva da sola (il campo nascosto dell'incolla resta sempre a fuoco) e copriva metà
del desktop per il 60 % della prova F-031; e non scriveva niente, perché nel modo a tocco nessuno ascoltava i
tasti. ⇒ **La tastiera non si apre più da sola; la apre un comando quando serve**, e quel che si scrive
arriva al desktop come §7.3 (lettere come lettere).
- Il comando è un bottoncino **⌨ in alto a destra**, solo col telefono in mano (disposizione a tocco): si
  scopre senza manuale, e col modello a trackpad non copre bersagli del desktop. Un gesto della tabella di
  `SPECIFICHE.md` §7.2 è stato scartato perché non si scopre da solo. Sul computer e sul DeX col mouse non
  cambia niente.

### 10.29 ✅ Sul DeX la cattura del puntatore si accende al primo clic — scelta dell'utente (3 ott 2026)

Parole della scelta: *«per migliorare l'usabilità in android la cattura meglio attivarla al primo clic del
mouse»*, e alla fine della prova: *«considerando i limiti di Android direi che abbiamo raggiunto un risultato
eccellente»*. `[M]` 3 ott, S23 (Android 16) sul DeX, Chrome 154 e Samsung Internet 30, Radeon e Intel: senza
cattura la posizione arriva solo al clic o a tasto premuto (noVNC #1727, di Android sui Samsung) e la freccia
doppia del ridimensionamento non compare mai; con la cattura i movimenti a tasti alzati arrivano e il bordo si
trascina. ⇒ **Il primo clic sulla tela cattura il puntatore dove l'hover non arriva** (nessun passaggio a tasti
alzati prima del clic, o l'ultimo ad almeno 8 px dal clic: nessun ramo per sistema, Samsung Internet sul DeX si dichiara Linux); **si esce
spingendo oltre il bordo** (160 px CSS di spinta, così gli angoli attivi restano) **o con Esc**, e il clic
dopo ricattura. Sui computer l'hover arriva e non scatta mai. Con la cattura la freccia la disegna la pagina.
- `[?]` Da riprovare quando Google rilascia la modalità desktop di Android (osservazione dell'utente, 3 ott):
  la regola guarda il comportamento e non il sistema, quindi si adatta da sé (hover che arriva ⇒ niente
  cattura); da misurare là: se Chrome concede `Pointer Lock` e se le scorciatoie arrivano alla pagina.

### 10.30 ⛔ *(superata da §10.33)* REMOTIX diventa a codice chiuso, con trial e versione full a pagamento (5 ott 2026)

> ⭐ **Le regole in vigore stanno in `SPECIFICHE.md` §15** (9 ott 2026). Qui resta la storia: alcune voci
> sotto sono state superate da decisioni successive.

Parole dell'utente: *«voglio rendere il prodotto utilizzabile in versione trial limitata e in versione full solo
dopo aver acquistato una licenza di utilizzo»*; alla domanda «paga solo chi lo usa per lavoro (A), o paga
chiunque e il codice diventa chiuso (B)?» ha risposto **B**.

- **Perché un aut-aut**: con il codice pubblico e modificabile (PolyForm Noncommercial, §10.22), un privato
  poteva togliere legalmente il limite della trial. Un limite che si fa pagare regge solo se il codice è chiuso.
- ⇒ **§10.22 è superata**: niente codice pubblico, niente accordo per chi contribuisce. Il deposito
  `github.com/nic-fio/REMOTIX` è già privato.
- ✅ **Nessun ostacolo dalle dipendenze**: ffmpeg è uscito nella fase 18. Le dipendenze rimaste (MIT, BSD,
  Apache) permettono un prodotto chiuso; chiedono solo che le loro licenze viaggino col prodotto (il file
  generato dallo SBOM, già previsto).
- ⚠ **Quel che il codice chiuso NON impedisce**: il binario gira sulla macchina del cliente, e chi è
  determinato può modificarlo. Il controllo della licenza tiene onesti i clienti onesti, non ferma chi copia.
- ⚠ **Senza legale** (scelta di §10.22): per la trial esiste un testo standard scritto da avvocati, la
  **PolyForm Free Trial 1.0.0** (prova per 32 giorni). Per la versione full a pagamento **non c'è** un testo
  PolyForm equivalente: il contratto di vendita resta da scegliere.
- ✅ **La trial: 1 utente, 30 giorni** (utente, 5 ott). *«Scaduti i 30 giorni al login compare una finestra di
  licenza scaduta e di acquistare il prodotto»*. ⇒ dopo la scadenza **non si entra**: la pagina d'accesso, a
  credenziali giuste, mostra «licenza scaduta» e il collegamento per acquistare. Il limite di 1 utente lo fa
  rispettare il programma.
  - Il conto parte dal **primo avvio del server**; la data sta in `/var/lib/remotix`, e il programma ricorda
    anche **l'ultima data vista**: se l'orologio torna indietro, vale la più recente.
  - La finestra compare **dopo** utente e parola d'ordine giuste: chi non ha un account non scopre che il
    server è senza licenza.
  - ⚠ Dichiarato: chi cancella `/var/lib/remotix` e reinstalla riparte da zero. Il contratto della trial
    (PolyForm Free Trial 1.0.0, 32 giorni) resta la difesa legale.
- ✅ **Lo sblocco si fa dalla pagina d'accesso** (utente, 5 ott): *«se la licenza è scaduta sulla stessa
  finestra si apre un secondo campo dove viene inserito il codice di licenza; il sistema verifica la validità
  del codice e passa il controllo al modulo di accesso»*. Sequenza: utente e parola d'ordine giuste ⇒ licenza
  scaduta ⇒ compare il campo del codice ⇒ codice valido ⇒ si entra. Aggiunte di Claude:
  - il campo si apre anche **durante la trial** («Hai un codice di licenza?»): chi compra prima, o aggiunge
    utenti, non aspetta la scadenza;
  - il codice è **firmato** e si verifica **senza rete** (la chiave pubblica sta nel programma, quella privata
    solo da chi vende): è lungo ~100 caratteri, **si incolla** dall'email. Un codice corto da battere
    richiederebbe un nostro server di verifica, escluso.
- ✅ **Cosa mostra la pagina d'accesso, nei tre stati** (controproposta di Claude, accettata dall'utente il 5 ott:
  *«uno potrebbe decidere di acquistare il prodotto anche solo dopo 2 giorni di utilizzo»*):
  - **trial**: la scritta «Trial version — restano N giorni» (anche prima delle credenziali: è innocua) e il
    collegamento «Hai un codice di licenza?», che apre il campo;
  - **licenza valida**: niente scritta e niente campo; solo un collegamento piccolo «Cambia licenza», per chi
    aggiunge utenti;
  - **licenza scaduta**: il campo del codice già aperto.
  - ⛔ Scartato il campo in grigio: in trial impedirebbe di comprare prima della scadenza, con la licenza
    occuperebbe spazio senza servire.
- ✅ **Il tetto tecnico e il tetto commerciale sono due cose** (utente, 5 ott): *«tecnicamente il prodotto ha come
  limite superiore 16 utenti, ma nessuno vieta di usare remotix con un numero di utenti maggiore se dispone di un
  server ultrapotente»*. ⇒ La licenza dice **N utenti oppure «illimitati»**, senza legarsi al 16. Il numero
  di utenti che si collegano davvero è il più basso fra la licenza e quel che regge la macchina.
  - ⚠ Il lavoro tecnico che ne viene: oggi il 16 è **fisso in compilazione** (`MAX_ATTACCATE` in
    `src/rcp.c`, §1.11). Per andare oltre su un server potente deve diventare un limite deciso al momento
    dell'avvio, dalla scheda e dalla configurazione.
- ✅ **La capacità si dichiara, non si limita** (utente, 5 ott): *«si documenta che su una certa configurazione
  il sistema garantisce un utilizzo ottimale fino a X utenti, poi comincia la fase di degrado. Chi acquista sa
  cosa aspettarsi … sarebbe impossibile testare ambienti enterprise, dovrei quantomeno affittare un
  datacenter»*. ⇒ Una tabella pubblica, **una riga per ogni macchina misurata**: utenti con uso ottimale, e da
  dove comincia il degrado. ⛔ Solo macchine misurate davvero, col loro ferro dichiarato.
  - ⇒ **Il piano delle misure di prestazione** (primo lavoro dopo la fase 19) misura anche **la curva degli
    utenti** su Intel e Radeon: sono le prime due righe della tabella.
  - ✅ **La prova di capacità per il cliente è un programma a sé, accanto al server** (utente, 5 ott: *«remotix
    allo stato attuale è "trasparente" (non dispone di menu o di un'interfaccia per le attività di servizio):
    dovremo realizzare una suite di test da fornire allo scopo, "parallela" al server vero e proprio»*). Chi
    ha una macchina che noi non abbiamo si misura da solo, durante la trial, prima di comprare. Condizioni
    di Claude:
    - **lo stesso codice di codifica del server**, costruito insieme a lui e nello stesso pacchetto:
      un codificatore scritto a parte misurerebbe un'altra cosa;
    - **leggera**: niente browser né scatole (le suite di laboratorio non si consegnano). Simula N desktop
      in movimento e misura quanti la scheda ne codifica senza perdere fluidità;
    - **solo a server fermo**: con sessioni aperte si rifiuta e dice perché, perché misurerebbe solo la
      capacità che avanza e ruberebbe la scheda agli utenti;
    - stampa **la stessa riga della tabella pubblica** (ottimale fino a X, poi degrado), confrontabile coi
      nostri numeri.
  - Sostituisce la controproposta di Claude «vendere fino a 16, l'oltre dopo»: la licenza dice N o
    «illimitati» senza tetto, e la trasparenza fa il resto. Resta il lavoro tecnico del limite deciso
    all'avvio (sopra).
- ✅ **La licenza full vale per sempre** (utente, 5 ott, «1, per sempre»): si paga una volta, per N utenti o
  «illimitati». Nel codice firmato non c'è nessuna scadenza; chi vuole più utenti compra un codice nuovo
  («Cambia licenza»).
- ✅ **Il codice vale per una macchina, fisica o virtuale** (utente, 5 ott: *«il codice è per macchina (fisica o
  virtuale che sia)»*). Il cliente, all'acquisto, manda l'identificativo della macchina (lo mostra la pagina
  d'accesso accanto al campo del codice); il codice firmato lo contiene, e su un'altra macchina non vale.
  - L'identificativo è `/etc/machine-id`: esiste uguale su macchine fisiche e virtuali, e non dipende dai
    pezzi del computer.
  - ⚠ Dichiarato: chi è amministratore può copiarlo su un'altra macchina, e una macchina virtuale
    **clonata** lo porta con sé. Vale la regola di sopra: tiene onesti gli onesti.
  - ⚠ Il prezzo: server cambiato o sistema reinstallato ⇒ identificativo nuovo ⇒ il cliente ti scrive e
    gli generi un codice nuovo, a mano.
- ✅ **Ci vuole un controllo delle licenze in rete** (utente, 5 ott: *«se il prodotto dev'essere venduto allora è
  obbligatorio dotarsi di un software di controllo delle licenze … un sistema forse in stile Microsoft o
  affine»*), dopo che Claude ha mostrato che senza rete la rivendita sottobanco (= copia dell'identificativo
  della macchina, o macchina virtuale clonata) non si può impedire, ma solo scoraggiare. ⇒ Supera
  «senza rete» delle voci sopra; il codice firmato e il nome del cliente restano.
  - 🔸 Proposta di Claude, da confermare: **ibrido come Microsoft** — attivazione in rete, controllo
    periodico con **tolleranza** se la rete manca (non si blocca un cliente per un guasto del nostro
    servizio o della sua linea). ⛔ **Niente attivazione senza rete** (utente, 5 ott: *«un server che non
    abbia un accesso a internet … mi sembra alquanto improbabile, a meno che non si tratti di militari»*):
    una strada sola, e il file firmato senza rete era il varco più facile da clonare. Restano: il passaggio
    da un **proxy** (le aziende escono così) e la **tolleranza** ai guasti di rete;
  - ✅ **La piattaforma di licenze la scriviamo noi** (utente, 5 ott: *«non voglio appoggiarmi a prodotti a
    pagamento; se serve, la piattaforma di licensing ce la costruiamo noi»*). ⛔ Supera la proposta di Claude
    di un servizio esistente. Il confronto fatto (5 ott: Keygen, Cryptlex, Polar, Paddle, Lemon Squeezy,
    Anystack, Gumroad) resta come riferimento per le funzioni: attivazione legata alla macchina, controllo
    periodico, rinnovo comandato dal pagamento, e per i cloni un **identificativo casuale per ogni avvio**
    più il controllo periodico, che vede due copie vive sullo stesso codice (è la tecnica dei «processes»
    di Keygen).
  - ⚠ **Il pagamento non si può scrivere da noi**: carte, rimborsi e contestazioni passano comunque da un
    processore di pagamento, che trattiene una percentuale a vendita (nessun canone). Resta da scegliere
    chi incassa (sotto).
  - ⚠ Da dichiarare al cliente: il server manda al nostro servizio il codice e l'identificativo della
    macchina (riservatezza dei dati).
- ✅ **IL MODELLO DEFINITIVO: abbonamento annuale per macchina, utenti illimitati** (utente, 5 ott: *«dovendo
  realizzare un server di licenze, voglio un sistema semplice: si paga anno per anno senza limite agli utenti
  che remotix gestisce»*). ⛔ **Supera** «la licenza full vale per sempre» e gli scaglioni di utenti
  (proposta di Claude, mai confermata).
  - Perché regge adesso e non prima: il controllo in rete c'è comunque, quindi **il rinnovo è automatico**
    (lo comanda la piattaforma di pagamento) e non serve mandare un codice nuovo ogni anno. Le obiezioni di
    Claude all'annuale cadono con la rete.
  - Il programma non conta più gli utenti per la licenza: resta solo il tetto tecnico della macchina,
    dichiarato nella tabella pubblica. ⇒ Il lavoro «limite deciso all'avvio» resta, il lavoro «numero di
    utenti nel codice» sparisce. La trial resta 1 utente, 30 giorni.
  - ⚠ Dichiarato: lo studio con 2 persone e la scuola con 60 pagano uguale. Il prezzo si sceglie tenendone
    conto.
  - ✅ **A rinnovo mancato: 14 giorni di tolleranza**, avviso sulla pagina d'accesso da 7 giorni prima della
    scadenza, poi la stessa finestra della trial scaduta («abbonamento scaduto, rinnova») (utente, 8 ott).
- ✅ **Le licenze «eterne» di chi vende** (utente, 5 ott: *«una versione full di remotix "eterna" che userò io
  personalmente, o dovrò diventare cliente di me stesso»*). Forma di Claude: ⛔ **niente versione speciale del
  programma** (un binario senza controllo, se esce, è la versione sbloccata per tutti); ⇒ **licenze senza
  scadenza nel servizio di licenze**, una per macchina, generate da chi vende. Stesso programma, stessa strada
  del cliente.
  - Valgono anche per **le macchine di prova**: il server di prova e le 4 scatole (ognuna col suo
    identificativo), o la suite si ferma alla trial di 1 utente.
- ✅ **IN DEFINITIVA: tre tipi di licenza, tutti per macchina** (utente, 5 ott: *«per rendere le cose semplici
  prevediamo 3 tipi di licenze»*):

  | tipo | utenti | durata | chi la ottiene |
  |---|---|---|---|
  | **trial** | ~~1~~ **illimitati** | ~~30~~ **14 giorni** | chiunque installi (⭐ cambiata il 9 ott, sotto) |
  | **full** | illimitati | 1 anno, rinnovo automatico | chi paga |
  | **gold** | illimitati | nessuna scadenza | ⛔ **non in vendita**: uso privato di chi vende, per le sue macchine e per le macchine di prova |

  - ✅ **La trial cambia: 14 giorni, utenti illimitati** (utente, 9 ott: *«eliminiamo il limite di 1 utente, così
    un'azienda può effettivamente valutare le vere potenzialità del prodotto»*). ⛔ Supera «1 utente, 30 giorni».
    Scaduta, REMOTIX smette di funzionare e serve la full. Legata alla **firma dell'hardware**, senza doppioni:
    due copie attive della stessa trial ⇒ la trial si disabilita (qui va bene: nessuno ha pagato). ⇒ Il
    programma **non conta più gli utenti per nessuna licenza**. Dettagli in `fasi/21-la-licenza.md` §11.3.
  - ✅ **Il rinnovo della full lo sceglie il cliente: manuale (predefinito) o automatico** (utente, 9 ott). ⛔ Supera
  «1 anno, rinnovo automatico» e «il rinnovo è automatico (lo comanda la piattaforma di pagamento)». Perché:
  *«addebitare centinaia o migliaia di euro automaticamente … non è così simpatico»*. Regole in `SPECIFICHE.md` §15.6.
- ✅ **Il terzo tipo si chiama «gold»** (utente, 8 ott: *«si vende solo la full, la gold è per uso privato»*):
    era «eternal», cambia solo il nome. ⛔ Si vende **solo la full**.

  - Aggiunta di Claude: con il controllo in rete **anche la trial si registra sul nostro servizio**, legata
    all'identificativo della macchina. Una macchina che ha già avuto la sua trial non ne riceve una seconda:
    si chiude il varco «cancello `/var/lib/remotix` e reinstallo» dichiarato sopra (resta solo chi cambia
    l'identificativo, come per la full).
- ✅ **Il servizio di licenze gira sul VPS** (utente, 8 ott: *«il server è sulla VPS»*), lo stesso che pubblica
  l'archivio dei pacchetti (§10.23, D10): una macchina sola da tenere accesa e aggiornata, nessun costo nuovo.
  - ✅ **La tolleranza se la rete manca: 14 giorni**, controllo ~~ogni 24 ore~~ **ogni 60 minuti** (utente, 9 ott), avviso all'amministratore dal primo
    controllo fallito (utente, 8 ott; `fasi/21-la-licenza.md` §10 domanda 1).
  - ✅ **Alla scadenza si disabilita solo REMOTIX, mai l'accesso al server**; collegamenti chiusi, desktop vivi;
    avvisi prima nella pagina (amministratore da 7 giorni, utenti 3 messaggi al giorno negli ultimi 3), col
    comportamento e parte del codice di RootSpeak (utente, 8 ott; `fasi/21-la-licenza.md` §10 domanda 5).
  - ⚠ **Un punto solo**: se il VPS cade, si fermano insieme gli aggiornamenti e i controlli di licenza. I
    clienti non se ne accorgono finché dura la **tolleranza** ⇒ la tolleranza va scelta più lunga del tempo
    che serve a rimettere in piedi il VPS.
  - 🔸 Proposta di Claude: **la chiave che firma le risposte sta sul VPS, ma non è la radice**. Una radice
    fuori linea (mai sul VPS) certifica la chiave del VPS, come già fa la catena dell'installatore (radice
    ed25519 fuori linea, sottochiavi, revoche). Se il VPS viene violato si revoca la sua chiave e se ne
    certifica una nuova, senza ricompilare il prodotto.
- ⏳ **Il pagamento resta in sospeso** (utente, 5 ott: *«per il momento lasciamo in sospeso l'implementazione dei
  sistemi di pagamento e concentriamoci sul prodotto»*). Scelta aperta: chi vende al posto nostro (Polar,
  Paddle: ~5% + 0,50 $, IVA e fatture loro) o Stripe (IVA e fatture nostre). ⇒ Il nostro servizio di licenze
  espone **un ingresso generico «rinnova/sospendi questa licenza»**, che il pagamento chiamerà quando ci sarà:
  la scelta di dopo non cambia il prodotto. Le licenze full si creano a mano finché il pagamento non c'è.
- ✅ ~~Da decidere: che cosa compra la full; il contratto di vendita~~ — chiuse il 9 ott (utenti illimitati, 1 anno,
  aggiornamenti finché attiva, scaduta si ferma); il contratto resta sospeso col pagamento. Vedi `SPECIFICHE.md` §15.

**9 ottobre 2026, sera — la semplificazione.** Su domanda dell'utente (*«abbiamo parecchi elementi che fanno
sicurezza: license key, fingerprint, firma, biglietto…»*) e col suo principio (*«la complessità di un sistema aumenta
la probabilità di introdurre punti di vulnerabilità e di perdita di controllo del processo»*) si sono tolti
`INSTALL_KEY` (firma e biglietto stanno nella stessa cartella: chi copia l'uno copia l'altro; i cloni li scopre il
biglietto), `HW_FINGERPRINT` (sulle VM si cambia con un clic; trial «una per account»), il numero di licenza (resta
solo la `LICENSE_KEY`, mostrata mascherata), il recupero via email, lo spostamento firmato e l'upgrade con chiave
nuova. Al loro posto un meccanismo solo: ogni installazione parte **in attesa** finché l'acquirente non la conferma
nell'area cliente. ChatGPT (gpt-5.6-sol, con mandato di smentire) ha confermato che firma e impronta non servivano;
delle sue correzioni sono entrate le quattro senza pezzi nuovi (primo biglietto alla copia in attesa, codice casuale
nelle richieste, chiave cancellata dal disco dopo l'attivazione, una sola attesa per licenza), mentre deleghe,
attivazioni provvisorie, finestre di ritorno e rigenerazione della chiave da parte del cliente sono state escluse
dall'utente come fuori dal perimetro di REMOTIX. L'interfaccia fra REMOTIX e il servizio è scritta come due scatole
nere (`SPECIFICHE.md` §15.14). Regole in vigore: `SPECIFICHE.md` §15, riscritto per intero. Subito dopo l'utente ha tolto anche la
conferma (*«abbiamo complicato il processo … inserisce lo stesso codice e qui si verifica il caso del doppione»*):
ogni installazione parte subito, e una seconda con la stessa chiave è uno sdoppiamento. Restano due elementi
(chiave e biglietto) e un gesto (la scelta della copia); in più il cambio server avviene senza fermo.

### 10.31 ✅ L'installatore non ha la finestra: solo una TUI curata (5 ott 2026)

Parole dell'utente: *«niente installer grafico; prevediamo sì un installer con interfaccia professionale, ma
attraverso una TUI sofisticata»*. ⛔ **Supera** §10.5 per la parte GUI e §10.19 (Gio) per intero.

- ⇒ **Due interfacce, non tre**: la CLI e la TUI (bubbletea/lipgloss, già nel programma), sullo stesso motore.
  La TUI è l'interfaccia «professionale»: va curata come lo era la finestra (colori, disposizione, parole del
  prototipo).
- Perché regge: chi installa un server lo fa da un terminale, via ssh o dalla console, e anche dal desktop
  `install.sh` si lancia da un terminale. Si toglie la parte più costosa da costruire e da provare:
  la seconda costruzione con cgo su glibc di Debian 12 (`Contenitore.gui`), le librerie grafiche, polkit e
  le differenze fra Wayland e X11.
- ⚠ **Il lavoro che ne viene** (fase dell'installatore): togliere `installatore/interfaccia/gui`,
  `Contenitore.gui`, `remotix-install-gui`, `install.sh --finestra` e il codice `RX-UI-001`, e la dipendenza
  da Gio nel `go.mod`; aggiornare `fasi/17-l-installatore.md` §6.6.1 e §6.6.14 e `SPECIFICHE.md`. ⛔ Il codice
  dell'interfaccia non contiene logica d'installazione (§6.6.1), quindi toglierlo non tocca il motore.
- ✅ **Fatto il 10 ott 2026**, commit `129e315`: GUI tolta dal codice, dal rilascio e dall'archivio; una costruzione
  sola, statica (motore, CLI, TUI); `vendor/` da 37 a 14 MB; prove Go verdi (64 PASS, 0 FAIL, vet pulito). Dettaglio
  in `fasi/17-l-installatore.md` §6.6.14. `SPECIFICHE.md` non nominava la finestra dell'installatore: niente da cambiare.

### 10.32 ✅ L'interfaccia di REMOTIX è tutta in inglese (5 ott 2026)

Parole dell'utente: *«l'interfaccia di remotix sarà tutta in inglese, così come già fatto per la pagina di
login»*. ⇒ Tutto quel che legge chi usa o installa REMOTIX è in inglese: la pagina (accesso, avvisi, errori,
licenza), i messaggi che il server manda alla pagina, la TUI e i messaggi dell'installatore.

- Perché regge: il prodotto si vende fuori dall'Italia, e un'interfaccia sola si scrive e si prova una volta.
- ⛔ **Non cambia la lingua del progetto**: documenti, commenti, nomi nel codice e rapporti restano in
  italiano (le convenzioni di sempre). Cambia solo quel che vede il cliente.
- I testi stanno raccolti in un posto per ogni programma (come `installatore/interfaccia/testi.go`), così
  un'altra lingua si potrà aggiungere dopo senza cercarli nel codice.
- ⚠ **Il lavoro che ne viene**: la pagina d'accesso è tradotta (5 ott); restano gli altri testi della pagina,
  quelli che il server scrive nella pagina (`__AVVISO__` e gli avvisi del ban), la TUI e i messaggi
  dell'installatore. Le prove della suite cercano gli elementi per `id`, non per testo: la traduzione non le
  tocca (verificato il 5 ott sulla pagina d'accesso).

### 10.33 ✅ Niente licenze: REMOTIX è gratuito (10 ott 2026)

> Supera §10.30 e, con lei, tutto `SPECIFICHE.md` §15 e il piano `fasi/21-la-licenza.md`, che restano come storia.

Parole dell'utente: *«niente licenze. Remotix sarà un progetto freeware. La comunità di Linux apprezzerà il
gesto, poi se qualche azienda volesse acquistare il prodotto si faccia avanti. Quindi allo stato del progetto il
prossimo step sarà l'installer»*.

- **Che cosa esce**: trial e full, `LICENSE_KEY`, biglietto orario, il servizio sul VPS, il sito con area
  cliente e pannello, l'ingresso del pagamento. ⇒ La fase 21 (~161 ore) non si costruisce.
- **Perché regge**: è il pezzo più complesso rimasto, e non serviva a far funzionare REMOTIX ma a farlo pagare.
  Toglierlo toglie anche un servizio esposto in rete da tenere vivo e da difendere (*complessità =
  vulnerabilità*). L'installatore perde il passo della chiave: REMOTIX parte appena installato.
- **Il prossimo passo**: chiudere l'installatore (`fasi/17-l-installatore.md`), cioè le chiavi vere dei
  rilasci al posto di quelle di prova (D10, D11, D14) e il giro intero col binario di oggi.
- ✅ **Il codice si apre, ma nessuno ci deve lucrare** (utente, 10 ott: *«posso anche aprire il codice, ma
  nessuno deve poterci lucrare sopra. Credo che adotterò una licenza in stile Phonestra»*). Bozza in
  `LICENSE.md`, dalla Phonestra Freeware Licence con due aggiunte per un codice pubblicato: si possono leggere,
  compilare e modificare i sorgenti **per sé o per la propria organizzazione**, ma non distribuire copie
  modificate; e il **servizio ospitato** (vendere ad altri l'accesso a desktop serviti da REMOTIX) è fra gli usi
  commerciali vietati senza licenza scritta. ⏳ Da approvare dall'utente.
- ⚠ **Non è «open source»** nel senso della OSI (vieta la vendita e la redistribuzione modificata): si dice
  «codice visibile», non «open source», o la comunità lo contesta.
- ⚠ **Le aziende la usano gratis anche al lavoro**, come Phonestra: si compra solo per rivendere, includere in
  un prodotto o offrire come servizio. È l'opposto di §10.22 (che vietava anche l'uso interno).
- ✅ **Il sito `remotix.nicfio.it` diventa solo vetrina e scaricamento** (10 ott): file fissi serviti da Caddy
  sulla VPS, niente parti vive. ✅ **Il `.run` si scarica dalla VPS** (utente, 10 ott: *«dalla VPS»*), con accanto
  il suo `.sha256`. ⚠ Il deposito GitHub risulta **pubblico** (`gh repo view`, 10 ott sera), non privato come si credeva. Mockup in `grafica/sito-mockup/index.html`.
- Resta il vincolo di §11.4 delle SPECIFICHE, nessuna dipendenza GPL: la GPL chiederebbe di distribuire tutto
  sotto GPL.

### 10.34 ✅ Il driver della scheda è del cliente: REMOTIX dichiara e verifica, non installa (10 ott 2026)

Parole dell'utente: *«se è un problema di software della macchina non è un problema di remotix. Noi dichiariamo le
esigenze e le specifiche, e chi vuole usare il prodotto installa quello che serve»*.

- **Che cosa vuol dire**: il driver della scheda (NVIDIA proprietario compreso) e la sua versione sono un
  **requisito**, scritto nel manuale (`fasi/17-l-installatore.md` §3.1). Non si noleggia una NVIDIA per ogni
  distribuzione: NVIDIA è **certificata su Ubuntu 26.04** (fase 19) e, altrove, vale il requisito.
- **Che cosa resta nostro**: dire **chiaro e prima** che cosa manca. Lo fa già il motore: il controllo
  preliminare ferma la macchina senza un driver che codifica (RX-GPU-003…006, con il pacchetto da installare
  nel rimedio), e alla fine `remotix --prova-codifica` codifica davvero sulla scheda. Un driver troppo vecchio
  per Vulkan Video si ferma lì, con un messaggio, e non con un REMOTIX installato che non va.
- Coerente con §10.27 (niente codifica sul processore) e con [*niente eccezioni per compositore*]: quel che il
  sistema non dà, REMOTIX non lo rattoppa.

### 10.35 ✅ L'installatore parla solo inglese (10 ott 2026)

> Supera §10.15 (l'installatore bilingue, secondo la lingua del sistema).

Parole dell'utente: *«solo inglese»*, e poi *«usare solo l'inglese non è una rinuncia. remotix è destinato al mondo
dei sysadmin, non agli utenti normali»*.

- **Perché regge**: chi installa è un amministratore di sistema, e per lui l'inglese è la lingua del mestiere. Un
  testo solo da curare e da provare, e niente messaggi che cambiano con la lingua impostata sulla macchina.
- ⭐ **La lingua dei desktop non c'entra** (precisazione dell'utente, 10 ott: *«remotix mostra i desktop dei PC, e
  dipende dalla macchina su cui è installato il desktop … installo remotix su un sistema che ha la localizzazione
  in italiano. Gli utenti si collegano e vedono i loro programmi e il desktop in italiano»*). La lingua dei
  desktop e dei programmi che gli utenti vedono è quella della macchina: REMOTIX non la tocca. In inglese è solo
  il testo **proprio** di REMOTIX: l'installatore, la pagina d'accesso, gli avvisi (§10.32).
- **Che cosa cambia**: niente scelta della lingua (via `--lingua`, la lettura di `LANG`/`LANGUAGE`, la voce
  `lingua` del file di risposte, che ora è una voce sconosciuta e ferma il file con RX-RISPOSTE-002 come ogni
  altra); un catalogo solo di testi e di codici, in inglese (`motore/codici.go`, `motore/testi.go`,
  `interfaccia/testi.go`; via `codici_en.go`); `install.sh` in inglese; le descrizioni delle opzioni in inglese.
  I banchi che leggono l'uscita del motore (`17-t10.sh` in testa) cercano le parole inglesi.
- ⚠ **Resta in italiano, per ora**: i motivi e le note del catalogo delle combinazioni (sono dati: avranno i loro
  campi inglesi con la prossima versione del formato del catalogo) e una parte dei **dettagli** diagnostici che
  accompagnano i codici (fra parentesi dopo il messaggio, e nel registro). Il messaggio e il rimedio di ogni codice
  sono in inglese, e una prova (`TestTesti`) ferma ogni lettera accentata o parola italiana che ci rientri.
- ✅ **Fatto il 10 ott 2026**, commit `a1c31ae`: costruzione statica, `go vet` pulito, `go test` 208 PASS (sottoprove comprese), 0 FAIL.
- ✅ **Completato lo stesso giorno**, commit `d580561`: in inglese anche i dettagli diagnostici, gli esiti delle
  verifiche, le note dei fatti, le righe che il motore scrive nei file di sistema e la tabella del manuale
  (`catalogo --tabella`); il catalogo passa a `2026.10.10.12` (seq. 12) coi motivi, le note e i limiti in inglese.
  `motore/inglese_test.go` cerca l'italiano in ogni stringa del codice e del catalogo: 211 PASS, 0 FAIL.
  ⚠ **Restano italiani, perché sono nomi dell'interfaccia e cambiarli è un lavoro a sé**: i comandi e le opzioni
  (`verifica`, `installa`, `approva`, `--archivio`, `--risposte`…), le voci e i valori del file di risposte
  (`consenso.*`, `porta`, `utenti = tutti`, `si`/`no`, `canale = stabile|candidato`), i valori dei fatti
  (`presente`, `assente`…) e i nomi degli stati (`RILEVATO`, `CONFERMATA`…). Da decidere.
- ✅ **Fatto anche questo, 10 ott 2026** (commit `5f802d7`): comandi, opzioni, file di risposte, stati, valori e
  nomi dei fatti, tipi dei passi, campi JSON, file in `/var/lib/remotix` e nell'archivio pubblicato, in inglese. La
  tabella vecchio → nuovo sta in `fasi/17-l-installatore.md` §6.6.15. Formati: `remotix-install/2` e
  `remotix-answers/2`. Restano i codici `RX-…` e `C-…` (identificativi), il formato del catalogo e quel che scrive
  il prodotto in C. ⚠ Il comando del prodotto `remotix` ha ancora le opzioni in italiano (`--porta`,
  `--indirizzo`, `--certificati`, `--prova-codifica`…): un lavoro a sé.

### 10.36 ✅ L'installatore semplice, e REMOTIX che non modifica il sistema (10 ott 2026)

Decisioni dell'utente prese in sequenza il 10 ottobre, con le sue parole. Supera §10.7 (il desktop installato da
REMOTIX) e le parti di §10.12, §10.21 e §10.23 che contraddicono quel che segue. ⏳ Il lavoro non è ancora fatto:
`fasi/17-l-installatore.md` dirà quando.

- ⭐ **Il principio**: *«la chiave di tutto è che remotix non modifica i sistemi su cui viene installato: dice cosa
  gli serve e poi sta all'admin provvedere»*; *«remotix dice semplicemente cosa manca. Il cosa installare e il come è
  una decisione non di remotix»*. ⇒ Escono dal motore: archivi di terzi (RPM Fusion, EPEL, Packman), driver della
  scheda e driver Vulkan, componenti dei desktop (labwc, caratteri…), il desktop (*«se manca il desktop non sarà
  certo remotix a installarlo»*), l'apertura del firewall, le cinture di sistema (polkit, logind, sleep). `check` dice
  cosa manca, **senza suggerire pacchetti o comandi**. Le voci tolte dai menu dentro le sessioni restano: sono il
  comportamento delle sessioni di REMOTIX, non il sistema.
- ⭐ **L'eccezione voluta**: l'iscrizione ai gruppi della scheda resta **automatica** (installazione e prima
  connessione, §7.21): *«non si installano pacchetti senza autorizzazione ma si fa in modo che gli utenti possano
  accedere»*. ⚠ Solo `render`, se non impedisce l'uso del desktop né peggiora le prestazioni (da provare sui
  quattro desktop): `video` dà anche `/dev/fb*` e le webcam (visto sul tablet). Poi un gruppo apposito `remotix`;
  le ACL solo se servono e misurate (logind riscrive le ACL `uaccess` di `renderD*`).
- **Comandi**: da 14 a 5 + `tui` — `check`, `install` (mostra il piano coi pacchetti esatti dalla simulazione del
  gestore, poi *«Proceed? [y/N]»* dallo stdin, come apt), `uninstall`, `status` (stato + verifiche),
  `prepare-offline`. Via piano/approva/applica, dry-run, resume/rollback come comandi (*«cerchiamo di semplificare
  la vita»*).
- **Niente modalità senza domande** (via il file di risposte): *«chi installa su molte macchine si prepara uno
  script bash»*.
- **Installazione interrotta**: si annulla e si rifà da capo, mai ripresa a metà (*«non mi piace l'idea di lasciare
  un sistema a metà»*); prima si sistema il gestore (es. `dpkg --configure -a`); nessun ritentare automatico. Una
  disinstallazione interrotta si porta a termine.
- **Non reinventare il gestore** (*«non reinventare la ruota duplicando funzioni già supportate dai gestori dei
  pacchetti»*): risoluzione, firme, dipendenze e autoremove li fa il gestore; il motore non ha cache né sha256 propri
  dei pacchetti.
- **Il pacchetto unico, niente archivio da aggiungere** (*«sono più orientato all'idea del pacchetto di
  installazione unico. Questo evita che l'admin debba aggiungere fonti esterne che è sempre un gesto mal visto»*):
  un file solo (es. `remotix-<versione>.run`, sha256 pubblicato) con l'installatore e i pacchetti di tutte le
  distribuzioni; il gestore installa da una cartella locale. Aggiornare = scaricare il `.run` nuovo e rilanciarlo.
  Supera la parte di §10.23 sull'aggiornamento con `apt upgrade` da un archivio nostro.
- **Le distribuzioni ad aggiornamento continuo restano** (Arch, Tumbleweed; e Fedora): *«chi usa arch è consapevole
  che in qualunque momento la macchina potrebbe avere problemi. Quello che noi possiamo fare al massimo è fare in
  modo che remotix usi librerie piuttosto stabili, ma non possiamo garantire la stabilità su sistemi per loro natura
  soggetti a problemi di affidabilità»*. ⇒ Nel manuale: certificate per la produzione Debian, Ubuntu LTS, Alma (Rocky
  e RHEL compatibili), Leap; Fedora, Arch, Tumbleweed provate a ogni campagna ma senza garanzia sugli
  aggiornamenti del sistema. Da fare: le librerie fragili dentro il binario (come ngtcp2/nghttp3), e il servizio che
  all'avvio prova la codifica e lo dice chiaro in `remotix status` se un aggiornamento l'ha rotta.
- ✅ **Fatto il 10 ott 2026** (commit `2e16f8f` motore, `8bcb881` il .run, `623ea90` banchi):
  `fasi/17-l-installatore.md` §6.6.16. Restano da provare sul ferro (la campagna sulle distribuzioni) e due
  punti aperti: solo `render` nei gruppi della scheda, e le licenze dei componenti di terzi nel .run.
- ✅ **I pezzi dei desktop sono dipendenze di REMOTIX, non mancanze** (utente, 10 ott 2026: *«trattiamo i 3
  componenti come normali dipendenze di remotix. basta che l'installer li mostri come tali nella sezione piano»*):
  labwc e wlr-randr per XFCE e LXQt, e un carattere scalabile se la macchina non ne ha, li aggiunge il motore ai
  pacchetti da installare; il gestore li prende dagli archivi della distribuzione come le altre dipendenze e la
  simulazione li mostra nel piano, nel gruppo «Dependencies of REMOTIX» con «needed by REMOTIX for XFCE». Lo stesso
  vale per l'altro pezzo del catalogo, breeze6-wallpapers (KDE su Tumbleweed). Se la distribuzione non ha il
  pacchetto, la simulazione fallisce e lì si ferma (RX-PACCHETTI-005). Il carattere per famiglia torna nel catalogo
  (`carattere_scalabile`, 2026.10.10.14). Fatto il 10 ott, commit `facc27a` (con la TUI rifatta: fasi/17 §6.6.16).


### 10.37 ✅ Il manuale tecnico: in inglese, sul modello di Phonestra (10 ott 2026)

Scelte dell'utente (10 ott 2026):
- **in inglese**, come l'interfaccia (§10.32, §10.35): messaggi e codici `RX-…` combaciano parola per parola;
- **stile, struttura e tipo di contenuti presi dal manuale tecnico di Phonestra** (*«solo che questo manuale sarà
  almeno 10 volte più lungo e complesso»*): parla a **chi mantiene REMOTIX** (interni, protocollo, catture, codifica,
  prove, costruzione, estensioni, mappa dei file), non a chi lo installa;
- **per ora si scrive solo quello tecnico**; la guida per il sysadmin (installazione, comandi, codici) resta da
  decidere.

🔸 Derivato da me, correggibile: come in Phonestra il manuale è **generato** — `docs/sources/technical/chNN_*.py`, un
file per capitolo, ⇒ `docs/Technical Manual.html` con `python3 docs/sources/build.py`; `style.css` e `manual.js` sono
il **canone comune** copiato byte per byte da Phonestra (che non si modifica in un progetto solo); `--controlla`
verifica che file, funzioni, variabili `REMOTIX_*` e codici `RX-` citati esistano nel codice, e che non resti
italiano. Prestazioni e capacità aspettano la campagna xrdp.

### 10.38 ✅ REMOTIX is fully English: code, documents, page, commits (10 Oct 2026)

User's words (10 Oct 2026): *«Va abolita la lingua italiana dal codice e dai documenti, così è tutto coerente»*,
and on the counter-proposal to keep the project diary in Italian: *«no, remotix è full english»*.
- **Code**: identifiers, file and folder names, comments, log lines, command-line options, RCP message and
  capability names, bench names. **Documents**: all of them, the project diary included (decisions, phases,
  lessons, studies, plan). **Page**: every string the user sees (closes what §10.32 left half done).
  **Commits**: English from `be21b85` on.
- The conversation with the user stays in Italian; only the project changes language.

🔸 Derived by me, correctable:
- **No compatibility aliases** for the old Italian option names or wire strings: no product release has been
  published (the only GitHub release holds measurement archives), so there is no installed base to protect, and
  page and server always ship together.
- **One glossary first, then the rename**: every Italian term gets one English name in a single table, so the
  same word never becomes two different English words in two files.
- **Nothing reaches the test server until the xrdp campaign has finished**; the rename is built and checked on the
  laptop, then the whole suite runs on the server.
- The technical manual (§10.37) is regenerated after the rename, and `--controlla` then rejects Italian
  everywhere, `<code>` spans included.

---

### 10.39 ✅ The licence: free for personal and non-profit use, source readable, no modifications, no redistribution (10 Oct 2026)

> Supersedes the licence part of §10.33 (free for everyone, companies included; draft "Phonestra-style" licence).

User's words: *«remotix può essere scaricato e installato da privati, è vietato l'uso in ambienti commerciali
(altrimenti le aziende ne trarrebbero un beneficio economico). Il codice sorgente è consultabile, ma non si può
modificare né redistribuire»*; then *«se la comunità vuole proporre modifiche fa delle richieste su github (ecco il
perché del repo pubblico)»*; *«scuole ed enti pubblici no (ricadono nel caso di uso commerciale)»*; and, on Claude's
proposal of the sharpest rule (free only for natural persons, every organisation asks): *«la tua proposta migliora,
estendo l'uso gratuito ad associazioni no-profit e a chiese e istituti religiosi»*.

- **Free**: Personal Use (a natural person, not connected with any work, even from home) and Non-profit Use
  (non-profit associations and foundations recognised by law — ETS, ONLUS, APS, ASD — and churches, religious
  communities, orders and institutes, **for their non-profit activities**).
- **Commercial Use, written licence needed**: companies, professionals and the self-employed for their work, schools
  and universities, public bodies, healthcare; and the business activities run by non-profit or religious bodies
  (a school, a clinic, a shop, paid courses). The licence can be granted free of charge, case by case.
- **Source code**: readable and buildable **unmodified** (to check it); no modifications, no redistribution
  (not even unmodified: no distro repositories, images, containers). REMOTIX comes only from remotix.nicfio.it.
- **Contributions**: issues on GitHub only; pull requests are closed (`CONTRIBUTING.md`). The repository is public
  on purpose (user, 10 Oct).
- **Why not a standard text**: PolyForm Strict 1.0.0 matched three points out of four, but lets schools and
  government bodies in for free, and PolyForm texts cannot be altered while keeping their name. ⚠ So the text is
  ours, written without a lawyer: the doubtful cases are settled by the Author's written answer (§2 of the licence).
- ⚠ **Not "open source"** and not "freeware for everyone": the site says *free for personal use*.

### 10.40 ✅ KDE too resizes the desktop on reattach (10 Oct 2026)

User's words, after the report «on KDE the desktop sits at half height» (Windows + Chrome, and a friend on Zorin OS
from Trieste, all re-attaching the same session): *«abbiamo già rinunciato al dynamic resize per i limiti di kwin.
ma riprendere una sessione e non avere il resize al reattach non è accettabile»*.

- The cause, measured: the session was born 2544×912 on an ultrawide screen; every later attach from another size
  kept that canvas (SPECIFICHE §6.3, KWin 6.3.6 cannot resize a virtual output), and the page put it at the top with
  white below. The page is fixed (canvas centred, black bands, commit `c10c1e5` merged in `258f752`).
- ⇒ **The rule of §5.0-sexies now holds on KDE without exception**: the canvas takes the window's size at birth AND
  at reattach. Resizing during the session stays out (§5.1-bis).
- 🔸 The way being tried (10 Oct): on reattach to a different size, create a new virtual output of the right size
  and remove the old one, as when a monitor is swapped. To be confirmed on the hardware (branch
  `fix-kde-riattacco`).
- ⚠ Windows being rearranged is **not a KDE price**: every desktop moves and shrinks windows to fit a smaller screen
  on reattach (user: *«accade la stessa cosa anche sugli altri DE»*). The only KDE detail (August note above: KWin
  puts windows back where they were the last time it saw that size) is measured alongside GNOME, not treated as a
  defect.
- ✅ **No migration to Forky to solve KWin** (user's idea, then agreed, 10 Oct): REMOTIX runs on the customer's
  distribution, and KWin < 6.8 stays on Debian 13 (≥ 2028) and Ubuntu 26.04 LTS (≥ 2031). ⇒ One path that works on
  every KWin, no branch per compositor version; Forky joins the test matrix once it carries Plasma 6.8, to check that
  the same path holds there.

### 10.41 ✅ Printing: later, PDF only, server → client; no file transfer (10 Oct 2026)

User's words: *«trovo la condivisione di files piuttosto pericolosa, mentre si potrebbe ragionare sul discorso
stampanti»*, then *«solo pdf, server -> client. La annotiamo nel masterplan»*.

- **File transfer stays out** (SPECIFICHE §12): it is a way for data to leave and enter the server.
- **One technology for every printer** (user: *«niente casi particolari per stampanti locali o stampanti remote:
  usiamo la stessa tecnologia per entrambi i casi»*): a "later" item, `MASTERPLAN.md` **M6** — a virtual printer
  turns the job into a PDF, the page opens the browser's print dialog, and the job goes wherever the client's device
  can print (the home printer, or the office network printers installed on that PC). Only PDF, only server →
  client. Printers an administrator sets up on the server with CUPS are the system's business, not a REMOTIX feature. ⚠ Printing is
  taking a document out (the dialog can save it as PDF): off until the administrator turns it on, every print in
  the log.

### 10.42 ✅ Chrome on Android with DeX: 4K YouTube judged excellent (user, 10 Oct 2026)

User's words: *«Direi eccellente. Ho fatto una prova cattiva riproducendo un video a 2160P da youtube: il video era
fluido e in sync, ha avuto problemi solo quando ho spostato la barra di youtube avanti e indietro e lì l'audio ha
avuto stuttering. A 1440p però i problemi sono spariti e sembrava davvero di essere davanti al PC.»*

| | |
|---|---|
| server | the CHUWI tablet: Intel N100, 4 threads, 7.5 GB, GNOME |
| client | Samsung DeX, Chrome for Android, home network; then Chrome on Windows |
| 2160p | video smooth and in sync; ⚠ **audio stutters only while dragging the YouTube seek bar** |
| 1440p | no problems: *«like sitting at the PC»* |
| register | **tuning, not a defect** — the user called it excellent |

⭐ **The server was the CHUWI tablet itself** (Intel N100, 4 threads, 7.5 GB, GNOME, REMOTIX installed as a
package), not the test machine — which makes the result weigh more, not less.

✅ **Same scene from Chrome on Windows (same evening): same result** — user's words: *«stesso risultato di
android»*: the stutter on seek at 4K, the rest perfect. ⇒ The stutter is **not of the client**: it is born on the
server side (the N100 refetching and redecoding 4K on seek, or REMOTIX's audio under that load) — `[?]` which of
the two, because the tablet's REMOTIX log needs administrator rights and the CPU sampler started after the video. It
follows §7.19.

✅ **Closed by the user, same evening, after the heavy 4K seek test**: *«il limite è proprio il 4K e mi ritengo
soddisfatto, un risultato del genere su questo tablet ha quasi del miracoloso»*. ⇒ 4K seek on an N100 is the
**declared limit**, not a defect to chase. During that test `[M]` (top every ~1 s, 10 Oct 22:37–22:39): the tablet
at 55–80 %, peak 83 %, never saturated; Chrome ≈ 95 % of one thread, REMOTIX ≈ 13 %.

## Come si tiene questo documento

Una voce ❓ che riceve risposta **si sposta** nella sezione che le compete e cambia marca; non
si risponde in fondo. Una voce 🔸 che l'utente conferma diventa ✅. Una voce ✅ si riapre solo
con una misura che la smentisce — e allora si riscrive **nello stesso momento**, con la data e
la fonte (`CODER.md` §5).
