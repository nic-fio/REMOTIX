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

*Consequences to be written: `SPECIFICHE.md` §5.5 and `FASI.md` §01-filo-nudo, «The phase fallbacks».*

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
colour plus 8 of alpha, and alpha is not transmitted. The user's intention was *«massima
qualità»*, and under that word lay two distinct levers:

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

### 2.5-bis ✅ Mutter's ceiling is accepted: on GNOME the desired is not promised

*9 Aug 2026, at the close of phase 0, looking at the measured numbers.* «Sappiamo che tra tutti i
compositor dei 4 DE Mutter è quello che performa peggio […] GNOME non è in grado di garantire 4K/60
fps, ma va bene. Non sarà adatto per il gaming ma consente comunque una soddisfacente esperienza
desktop e multimedia.»

`[M]` 9 Aug: **36 ± 2 frames per second** over six rounds (33.7-37.8), declared scene,
1080p, zero copy — while the client draws **60**. The ceiling is the compositor's.

| | |
|---|---|
| **the minimum** (`§2.1`) | very far away, never in question |
| **the desired** (`§2.2`) | ⛔ **on GNOME it is not promised**. It stays the target where the compositor allows it — KWin delivers 58.9 `[M]` on the same machine, on the same afternoon |
| gaming | **out**, and it had never been in |

⚠ **Two things this decision does NOT say**, and they must be kept alongside or the ceiling is attributed to the
wrong thing:

1. ⛔ **it is not a 4K limit.** The cost of resolution on Mutter's capture is **zero** up
   to 4K (`LEZIONI.md` §3, question 10): the 36 are at 1080p, and at 4K they are the same. «GNOME delivers
   ~36 at any size» is the right sentence;
2. ⏳ **it does not close M3.** The signature of the intervals measured today — median 33.3 ms, minimum 16.2, never
   intermediate values — is that of two clocks at 60 beating against each other, that is the reading of
   `STUDI.md` §gnome §8.2. The candidate cure costs **zero lines of product** and is in phase 3. If
   it succeeded, this item gets rewritten.

> ### ⚠ 13 Aug 2026 — **M3 succeeds in fact, and this item must be put back into question**
>
> *Point 2 above: «if it succeeded, this item gets rewritten». The fact succeeded — ⛔ but **M3 is not
> closed**: the cause is not measured (`STUDI.md` §gnome §13).*
>
> ⭐ **The ceiling is not the compositor's, and the proof is `[M]`**: at the decoupled cadence GNOME
> delivers **61.4** instead of 31.5, on the same machine and with the same scene.
>
> ⚠ **The why is `[R]`**: in Mutter's code the brake computes
> `min_interval_us = 10⁶/maxFramerate` **truncated to an integer** (16666 for 60) against a tick of
> 16666.67 µs ⇒ whoever falls below would lose a whole tick. Not a beat between two clocks, a
> **quantisation**. ⚠ And the signature «median 33.3, minimum 16.2, never intermediate values» is what a
> grid produces and two beating clocks do not — ⛔ **but it is a consistent clue, not a measured
> law**.
>
> > ⛔ ⚠ *This paragraph said: «it is a **quantisation**, law verified on **13 points** (8
> > confirm it, 0 refute it)». **It is false.** `banchi/03-b14-esiti-griglia.jsonl` has **only two
> > cells**, both with `scena_sul_mio_monitor: false`, and the bench prints «⛔ la legge NON regge
> > su **0 punti su 0**». **Corrected on 13 Aug 2026**, finding of the phase 3 coordinator.*
>
> | monitor | brake | delivered | median | p99 | cell |
> |---|---|---|---|---|---|
> | 60 | 60 | 31.5 | 33.31 ms | 35.53 | **A** |
> | 120 | 120 | 82.9 | 12.12 ms | 18.53 | **B** |
> | 120 | 60 | 46.13 | 24.12 ms | 29.23 | **C** |
> | ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61.4** (60.04) | ⭐ **16.66 ms** | 20.43 | ⭐ **D** |
>
> *The four cells come from `banchi/03-b14-esiti.jsonl`, all with `scena_sul_mio_monitor: true`
> and with the three controls — positive, negative, return — that close.*
>
> ⇒ ⛔ **The «36 ± 2» stays true at the cadence we were asking for, and stops being a wall of the
> compositor.** At the decoupled cadence GNOME delivers **61.4**, that is as much as KWin. ⚠ And the «six
> tenths» **do not reproduce**: the low cell gives **a clean and deterministic 0.50**.
>
> ⛔⛔ **But the user's decision does NOT change today, and the reason is that the product cannot
> ask for that cadence**: `MOVIMENTO_FPS 60` is a compile-time constant (`src/figlio.c` · `MOVIMENTO_FPS`),
> `main.c` has no cadence options, `RecordVirtual` does not take the frequency (`src/mutter.h` · the note on `RecordVirtual`) and
> the four virtual monitors are all **@60**. ⇒ The 61.4 is `[M]` **on the bench** and **zero in
> production**. As long as it stays so, *«on GNOME the desired is not promised»* holds — ⛔ **but the
> reason has changed: it is no longer «Mutter can't make it», it is «we don't ask it to».** They are two
> sentences with opposite cures, and the second is ours.
>
> ⚠ **And rate is not latency**: this item talks about frames per second. Latency is §2.5,
> it overshoots, and 78 % of it is ours (`LEZIONI.md` §6.2).

### 2.7 ✅ ⭐ The server offers the maximum; the client sets the height

*9 Aug 2026, on the web client. «Meglio così, vorrà dire che una parte delle performance non sarà
più nostro compito. Remotix offrirà il massimo, sarà il client a dover essere all'altezza».*

⭐ **It is the rule of §2.4 extended to a second quantity.** There the user had already established that **only
the piece that is ours is promised** — the network is not ours, so it is declared and not promised.
Here the same criterion passes to **decoding**: the browser and the device's silicon are not
ours.

| | Whose it is |
|---|---|
| producing good frames, on time, and pushing them onto the wire | ⭐ **ours, and we measure ourselves on it** |
| decoding them and painting them | the **device's**: it is measured, declared, **not promised** |

⛔ **And this takes away from the browser probe the power to kill the project** (§1.6): if a
phone decoded HEVC in software, it is not a REMOTIX defect and it is a fact to write —
not a wall like v1's, where the slow client **was ours**.

⚠ **The boundary, and it must be written now so that it does not become an alibi**, is three lines:

1. ⛔ **the guaranteed minimum stays a promise of ours** (§2.1: 480p·25·24 bit), but it is a promise about
   what the **server delivers on the line** — not about what a browser manages to paint. A
   client that does not hold the minimum must be **said**, not suffered in silence;
2. ⛔ **a silent fallback stays forbidden** (`CODER.md` §4.2): «the client can't make it» is
   information the user must **see**, with the reason. Two behaviours under the same
   label are error form **E2** even when the fault is someone else's;
3. ⚠ **and it does not exempt us from measuring.** «It is not our job» holds for **promising**, not for
   **knowing**: without the measurement we would not even know what to declare, and `LEZIONI.md` §7.4 says
   that predictions do not count — not even those that suit us.

### 2.6 🔸 The latency bench exists only because the client is ours

Measuring the delay of a remote desktop usually requires **a camera** filming the
screen with a stopwatch on top. Not here: we inject the input **and** we write the client
ourselves.

**The closed loop**: the client sends an input that causes a huge and
unmistakable visual change — the screen changing colour — and then **watches the frames it decodes**
until it sees the new colour. The difference between the two instants is the real latency, measured
**from the receiving side** — the lesson that cost v1 three phases (`LEZIONI.md` §1.7).

Automatic, repeatable, without cameras and without anyone watching. It is the concrete case of what
the user had observed on 8 Aug: owning the client does not only remove lessons, it makes
some of them **much cheaper to respect**.

> ✅ **It survives the web client intact** *(9 Aug 2026, §1.6)*: we write the page, so
> the loop closes as before — it injects the input and watches the frames that `VideoDecoder`
> delivers to it. ⭐ And as a dowry comes something we did not have with two native clients: **the same bench
> runs on every device that has a browser**, phone included, without compiling anything.

### 2.8 ✅ ⛔ The **canvas** does not go into the worker — **decoding** does. *Carried out, measured, kept off*

*13 Aug 2026, phase 3. ⛔ This is not a postponed prescription: it is a prescription **executed**.
`STUDI.md` §web §6.1 said «WebTransport, decoding and canvas all in a dedicated worker», as the best
road. It was written, measured — and ⭐ **the measurement split it in two**, it did not reject it
wholesale.*

*⚠ The table of the stretches before/after the worker (delivery to `decode()`, decoding, callback → drawing,
drawing → glass) is removed: measured on the chain with the software encoder, it no longer holds after
phase 18. What remains is the direction of the effects and the decision.*

> ### ⛔⛔ 14 Aug 2026 — **THE STRETCH «callback → finished drawing» BORE A WRONG NAME**
>
> *Corrected by the user's decision, on two independent measurements of phase 4
> (`fasi/rapporti/F4-A2-pagina-dipinge.md`, `F4-A10-anello-input.md`), which reached the same
> conclusion from two sides without agreeing beforehand.*
>
> ⛔ **The stretch's name was wrong.** The real drawing cost little *(the number, measured on a
> chain that went through `sws_scale`, is removed with phase 18)*: that stretch
> measured **the wait for the frame from the GPU plus the drawing**, because an HEVC frame
> decoded in hardware comes out **opaque** (`format = null`) and reading back the mark triggers its
> GPU→CPU transfer. ⭐ The proof that the boundary was badly placed: with an **identical stage**, changing
> codec, «decoding» and «drawing» move in **opposite directions** and the sum is conserved — but
> `drawImage` **does not know which codec** produced the frame.
>
> ⇒ ⭐ **The lesson, and it holds beyond this stretch**: a breakdown row carries **a number and a
> name**. The number was `[M]`; the name was **deduced** — and no mark distinguished the two halves
> of the same row.

⭐⭐ **The decision, and it is not «no worker»: it is WHERE the boundary goes.**

| | |
|---|---|
| ⭐ **decoding off the main thread** | ✅ **worth it** — the decoder delivers sooner when it does not contend |
| ⛔ **the canvas off the main thread** | ⛔ **sinks the account**: drawing and delivery to the worker cost more than decoding gains |

⛔ **The mechanism, and it is the part that holds beyond this case**: an `OffscreenCanvas` in a worker
**is delivered at the frame-refresh rate** — an implicit `requestAnimationFrame` nobody wrote.
`transferControlToOffscreen` commits to the refresh **by itself**. ⇒ The prohibition of `STUDI.md` §web §6.1 is not about the
word: **it is about the mechanism**. ⛔⛔ And the prescription **contained its own refutation**: it prescribed
the worker and forbade the refresh skip, which the worker silently reintroduces.

⚠ **And the painted frames say the opposite of the delay, so they go alongside** (`LEZIONI.md`
§6.2): on the real chain the worker paints **more**, but at saturation the ceiling **collapses down to ≈ the
60 Hz refresh**. *(The numbers, taken with software encoding, are removed with phase 18.)* *→ redone: `fasi/18-senza-ffmpeg.md` §5.4.*

⇒ **What is decided today**: the code stays in the tree **behind `#video=worker`, off**. ⛔ **And
it is not a final rejection.** ⏳ `[?]` **the biggest limit, and it must be read next to the numbers**:
everything is measured on **Xvfb, in software, without a GPU**, and the penalty is largely synchronisation
to the refresh. ⇒ **On real hardware the account must be redone before burying §6.1** — and that is the reason
why the code was **not** removed: the day of the real GPU the number is redone without
rewriting anything.

---

## 3. The network and degradation

### 3.1 ✅ 30 Mbps is not a floor: it is a scenario

> ⛔ **PARTLY SUPERSEDED by §3.1-bis — 23 Aug 2026.** The line *«the requirement is
> adaptation, not a threshold»* **stays true and intact**; ⛔ **the table of scenarios does not**:
> two rows out of three lie below the floor the user declared. It stays below in full
> because it is the reason why 30 Mbps was never a minimum — and that reason has not
> changed. ⇒ **The table in force is the one of §3.1-bis.**

*8 Aug 2026. «il server deve poter fare il suo meglio per offrire la migliore esperienza
possibile a client che si collegano da connessioni critiche (come da una rete mobile).
Ovviamente non pretendo i miracoli come 4K a 300 kbps».*

Written as «minimum bandwidth 30 mbps» they told the programmer the opposite of the intention — that
below 30 we do not go. The real requirement is **adaptation**, not a threshold.

The scenarios to serve:

| Link | Bandwidth | Delay and loss | What the server does |
|---|---|---|---|
| good fixed line | 30+ Mbps | low | aims for the desired |
| modest fixed line, WiFi | 5–15 Mbps | medium | **spends everything there is** |
| critical mobile | < 2 Mbps, variable | high, with loss | holds the minimum, **and does not disconnect** |

### 3.1-bis ✅⭐⭐ ~~The minimum network is **20 Mbit/s**~~ → **30**, and it is a **declared floor**

> ⛔ **THE NUMBER WAS RAISED THE SAME EVENING → §3.1-sexies.** *«Ho già detto che il pavimento,
> per quanto riguarda la banda, è a 30 mbps»* — 23 Aug 2026, night. ⭐ **All the reasoning of
> this item stays valid to the letter**: the number changes, not the nature of a *declared floor*.
> ⚠ The «20» that follow are to be read as **30**; they have stayed written because the measurements taken that
> day were calibrated on 20, and rewriting them after the fact would make them unreadable.

*23 Aug 2026, opening phase 9. «ho letto nel piano di connessioni fino a 2 mbps. Mi ero
tenuto più largo: ritengo che una connessione minima debba essere 20 mbps: al di sotto di questo
limite l'utente nemmeno riesce a navigare, figuriamoci usare remotix».*

⭐ **The argument is a product one, not a code one**: below 20 Mbit/s it is not REMOTIX that does not
work — it is the web that does not work. A product is not calibrated on a line on which **nothing**
is usable.

| | |
|---|---|
| ⛔ **what it says** | **20 Mbit/s is the minimum on which the product promises anything.** Below, REMOTIX **promises nothing and measures nothing as a requirement** |
| ⭐ **what is measured, then** | the phase 9 bench works **at 20 Mbit/s and above**. The degradation ladder serves to cover the **temporary drops** of a good line — not to serve a poor line |
| ⚠ **what it does NOT become** | it is not a refusal: no code checks the bandwidth to disconnect anyone. **The ban on disconnecting stays whole** (§3.3, I1) — but below 20 it is a behaviour of the program, **not a promise about the line** |
| ⛔ **what leaves** | the row **«critical mobile, below 2 Mbps»** leaves the scenarios to serve — here and in `SPECIFICHE.md` §8.1 |

**The scenarios to serve, rewritten:**

| Link | Bandwidth | Delay and loss | What the server does |
|---|---|---|---|
| good fixed line | **30+ Mbps** | low | aims for the desired |
| ⭐ **the floor** | **20 Mbps** | medium | **spends everything there is**, and holds the declared minimum |
| ⚠ below the floor | < 20 Mbps | any | **outside what is promised.** The program degrades and does not disconnect, but the result **is not a requirement and is not measured** |

**What stays intact**, and it must be said so that nobody believes it swept away:

- **§3.2 (I1)** — intact to the letter: the rate does not drop out of prudence nor with a still scene. ⭐ What changes
  is only **the operating point** from which it starts going down, which must be calibrated afresh in phase 9;
- **§3.3** — intact: **frames** are dropped, never blur, never disconnect. ⚠ What changes is **how
  often it bites**: at 20 Mbit/s the run to the bottom of the scale is a **fault case**, not the normal case;
- **§5-quater.3** (the 250 ms audio cushion) — ⛔ **has nothing to do with this item**: it is a
  *thread* problem, not a bandwidth one. Whoever credited the new network with it would be wrong.

**What it opens, and this item does not close:**

1. ✅ **CLOSED the same day — §2.1, the minimum stays 480p · 25 fps.** *«480p/25fps è il
   pavimento»* — the user, 23 Aug 2026. ⛔ **But the reason has changed**: it is no longer the level to
   which a poor line forces us, it is **the bottom of the degradation ladder** — the point beyond
   which the phase 9 regulator is not allowed to go down on a 20 Mbit/s line.
   ⇒ A rate below 25 per second up there **is a defect**, not a successful degradation.
2. ❓ **a second budget, a network one, next to the GPU one** (§4.6): ten sessions × 20 Mbit/s
   are **200 Mbit/s on the server's wire**. To be named in phase 9, to be measured in **phase 10**.
3. ⚠ **§2.2/§2.3, 4:4:4**: the objection *«~50 % bandwidth»* weakens. ⛔ The refusal however
   **holds all the same**, and for the other reason: no Android decoder in hardware.
4. ⚠ **`SPECIFICHE.md` §6.4**: the declared H.264 level is `avc1.640032` (High **5.0**), while
   above **40 Mbit/s** the High tier with level **5.1** would be needed. A level that is too low does not
   give an error: **it makes the decoder reject the configuration**. With a higher bandwidth cap
   this line starts to bite.

⭐ **And a coincidence to declare, not to lean on**: the encoding measurements of the four
codecs (§1.13-bis) had already been made **«at 20 Mbit/s for all»**. ⚠ It is the bench's number that
coincides with the product's number **by chance**, not because one derives from the other.

*Consequences outside here, already applied on 23 Aug:* `SPECIFICHE.md` §8.1 (the twin table),
`PIANO.md` phase 9 (the bench was written **«at 2 Mbit/s»**), `CODER.md` §1-bis (the project's numbers).

### 3.1-ter ✅⭐⭐⭐ Bandwidth **is not the challenge**: the challenge is the network that **loses, reorders and jitters**

*23 Aug 2026, with phase 9 already open and half measured. «Comunque voglio farti notare una cosa:
30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti che
perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter».*

⛔⭐ **It is a correction of target, and it arrives at the right moment**: phase 9 had spent the
day narrowing the bandwidth, and the product **had held the worst case without degrading and
without any cure switched on** (§16 of the phase: `[M]` 21.5-23.1 Mbit/s on the real path, 7,125
frames delivered → 7,125 painted, **one** keyframe, zero abandonments). ⇒ A bench that cannot
make what it measures give way **is not measuring the right quantity**.

| | |
|---|---|
| ⛔ **what it says** | bandwidth is a **floor already overtaken by reality**: no modern line lies below it. The product must be measured on the line's **imperfections** — loss, out-of-order, jitter — not on its **width** |
| ⭐ **why it is the right quantity** | they are the three things a real line does **even when it is wide**: the distant WiFi, the mobile radio, the home network in the evening. They are also the three our transport reacts to **by itself**, without us knowing |
| ⚠ **what it does NOT cancel** | §3.1-bis stays: 20 Mbit/s stays **the declared floor**. ⭐ Its job changes — it is no longer the question of the phase, it is the **premise** on which the other three are measured |
| ⛔ **what is demoted** | the grid of bandwidth steps (`09-b70-ritmo.py`, 40 → 10 Mbit/s) stays as **outline**, not as the body of the phase: its question is closed |

**The three quantities, and they are not the same thing** — ⛔ and confusing them is the easiest way to
measure badly:

| | what it is | what it touches on our side |
|---|---|---|
| **loss** | the packet does not arrive | **video** goes on QUIC streams, which retransmit ⇒ it is paid in **delay**, not in lost frames. **Audio** goes on datagrams ⇒ it is paid in **holes** |
| **out of order** | it arrives, but after a newer one | ⭐ it is the condition of the **audio reordering cure** of 23 Aug — the only cure of the day whose useful half **has never been verified** |
| **jitter** | it arrives at irregular intervals | `[?]` QUIC may **mistake it for loss** and narrow the congestion window for no reason. If it happens, the drop **is ours** (or the congestion algorithm's, which we never chose — `webtransport.c` ~2730) |

⭐⭐ **And there is an irony the item must record**: the reordering cure had been written and
applied **the same day**, and filed as `[?]` precisely because *«to verify it you have to
dirty the network and I didn't»*. The user's correction **is the missing condition** of
that verification.

**What it entails, and these are operational facts:**

1. the phase bench becomes **`09-b76-rete-cattiva.py`**: `netem` profiles of loss (also in
   **bursts**, which is the real loss of a radio), **explicit** reordering, jitter, duplication,
   and the «bad home» mix. ⛔ With the predicates written **beforehand**, and with the number read from
   `tc -s qdisc show` proving that **the fault was really put in** — without it, you measure a
   hope;
2. **`09-b77-audio-riordino.py`** closes the reordering cure, **paired**: same network, same
   duration, and only the rule changing. ⛔ A single round with the cure on proves nothing;
3. the server log learns to say **whose fault it is** — lost and retransmitted packets
   read from ngtcp2 next to `cwnd` and rtt. ⛔ Today «is it the network or is it us?» has no answer in the
   numbers, and every measurement under loss would end in an argument;
4. the `[M]` of `07-b64` — *«at 10 % loss the session does not open in 25 s»* — **is open again**:
   a QUIC handshake has the PTO precisely to resend what is lost, and twenty-five
   seconds **do not look like loss, they look like something that does not retry**.

⛔ **And `netem` on `lo` becomes a single resource, with a lock** (`banchi/09-lucchetto.py`):
the discipline is put on the interface's **root**, so two benches that inject faults together
do not share the work — **the second erases the first one's fault, and the first keeps
measuring believing it has it**. ⚠ It would not give red: it would give a plausible number.

### 3.1-sexies ✅⭐ The bandwidth floor is **30 Mbit/s**, not 20 — *23 Aug 2026, night*

*«Ho già detto che il pavimento, per quanto riguarda la banda, è a 30 mbps.»*

⚠ **And here the register must be corrected, not smoothed over**: on the morning of 23 Aug the number given was
**20** (*«ritengo che una connessione minima debba essere 20 mbps»*, §3.1-bis), and phase 9 was
calibrated on it for a whole day. ⇒ The number is **30** from this item onwards.

⭐ **What does NOT change, and it must be said so that nobody believes it swept away:**

- **§3.1-bis stays valid to the letter**: the number changes, not the nature of a *declared floor* —
  below it, the product **promises nothing and measures nothing as a requirement**, but it refuses
  nobody and does not disconnect (§3.3, I1);
- ⛔ **§3.1-ter is even truer**: if 20 Mbit/s were not a challenge, 30 are even less so. The
  target of the phase stays **loss, out-of-order and jitter**, and this item **strengthens** that
  correction instead of reopening it;
- ⛔ **the day's measurements are NOT rewritten**: they are calibrated on 20 and must be read for what they
  are. `[M]` The hard case on the real path (§16) asked for **21.5-23.1 Mbit/s**, which with the old
  floor was **107-115 %** and with the new one is **72-77 %**. ⇒ ⭐ **With the floor at 30 the hard case
  fits, comfortably**: the decision on the bandwidth cap gets simpler instead of more complicated;
- ⚠ **§2.1 (480p · 25 fps) does not move**: it is the bottom of the **degradation ladder**, not a
  level that bandwidth imposes. With more bandwidth available, a rate below 25/s is **even more**
  clearly a defect.

*Consequences outside here, applied the same day:* `SPECIFICHE.md` §8.1, `CODER.md` §1-bis,
`PIANO.md` phase 9.

### 3.1-quater ✅⭐⭐⭐ A line that loses in bursts **is declared dead**, and the user comes back in by hand

*23 Aug 2026, night, after seeing the numbers of the bad network. «Se in 10 secondi non arrivano
più pacchetti è chiaro che la connessione è morta. […] se all'interno di un intervallo di 1-2
secondi c'è una perdita di pacchetti piuttosto copiosa direi di trattarla come il caso in cui la
connessione è caduta.»*

⛔ **Where it comes from, and it is a choice between two measured evils.** `[M]` §17.1 and §17.6: with heavy
burst loss (11.10 % real, in bursts of 4.5 packets on average) the product has **two**
possible behaviours, and both are ugly:

| | what it does | what the user sees |
|---|---|---|
| **without** the phase 9 cures | delivery stops: 7 seconds out of 25 saw a frame | ⛔ the screen **frozen for 14.26 s** |
| **with** the cures | it delivers all 25 s, but holding the queue | ⛔ the image moves **with 4.5 s of delay** |

⇒ ⭐ **The user decided that neither should be served**: a line like that **is not a slow line,
it is a broken line**, and it must be called by its name.

| | |
|---|---|
| ⛔ **what it says** | ① **10 seconds without incoming packets** = dead connection. ② **copious loss within a 1-2 s window** = it is treated **as a dropped connection** |
| ⭐ **what the user sees** | ✅ **the wire drops and you come back in by hand.** An explicit choice among three, on 23 Aug: not an automatic reattach, not an invisible restore |
| ⚠ **the objection that was raised and overcome** | *«on a bad network the diagnosis "the line dropped" is frequent, and making the user pay for it with a manual login makes the product unusable precisely where it is needed»*. ⛔ The user chose it all the same, and the decision is his |
| ⛔ **the prerequisite** | ⇒ **§3.1-quinquies**: coming back in, the user finds **his own ghost** denying him the slot. The ghost cure **is no longer an extra: it is the condition for this decision to be usable** |

**What it entails, and the hard part is not the code:**

1. ⛔ **«copious» is a word and must become a number, with the reason and the two margins.** The
   measured boundaries: **1.71 %** (`casa-cattiva`) is a line that **holds** and must not be declared dead;
   **11.10 %** (`raffica-forte`) serves nobody. ⚠ And the rule of the P8→P20 family holds here more
   than anywhere: the quantity must be an **observable fact**, never a clock — and a fraction
   computed on few packets **is not a fraction, it is noise**: below a minimum of packets in the
   window, the code **decides nothing**;
2. ⚠ **the 10 seconds are not set blindly**: QUIC's `IDLE_MS` is **30,000 ms**
   (`SPECIFICHE.md` §5.3) and it is **negotiated with the client**. ⛔ And there is a case not to break — the
   browser tab that has gone to the background, which the system slows down or freezes (`PIANO.md` A5):
   **a client silent for 15 s is not a dead client**;
3. ⛔ **it is born behind a switch that is OFF** (I6): this cure **throws a session out**, which is
   the most visible change one can make. The user decided the **behaviour**, not that it
   be on without having seen it;
4. ⛔ **every trigger is declared in the log** with the numbers on which the decision was taken (I1).
   A session closed without a line explaining why is indistinguishable from a defect of ours.

### 3.1-quinquies ✅⭐⭐ The **ghost** — ten seconds, and the sentence must not lie

*23 Aug 2026, night. «Se in 10 secondi non arrivano più pacchetti è chiaro che la connessione è
morta.»*

⛔ **The fact**, `[M]` measured the same day (§17.5): the wire drops, the user tries to get back in, and
for **30.5 seconds** he is told **«you already have an active session elsewhere»**. ⚠ **For whoever reads it
it is false**: that session is **his own**, and it died a moment earlier. The account closes without
dirtying the network — a **lost** goodbye and a goodbye **never said** are the same fact — and it is
`SILENZIO` (`src/rcp.c` · `SILENZIO`, 30,000 ms).

⛔ And the box of `src/rcp.c:229-233` **declares** that that clock *«makes the case "the
phone died in a tunnel" disappear»*: it does not make it disappear, it makes it **last thirty seconds**.

⛔⛔ **And with §3.1-quater it becomes the prerequisite, not an extra**: if a burst of losses makes the
wire drop and the user must **come back in by hand**, the first thing he finds on coming back is his own
ghost. On a line that loses in bursts **it repeats**.

| | |
|---|---|
| ⭐ **what it says** | ten seconds of silence are enough to declare an occupant dead. ⚠ How it is obtained — lowering `SILENZIO` or adding a tighter rule between clients **of the same user** — is a code matter, and must be chosen looking at **everything** that leans on that number |
| ⛔ **what it does NOT violate** | §8.2, *«no attached and **alive** client is ever ousted»*: the occupant here is attached but **not alive**. The rule does not contradict §8.2, **it applies it** — and it must be written, or the next one will believe it was violated |
| ⛔ **the case that does not break** | it holds **only between clients of the same user**. An eviction between different users would be a security hole, not a convenience |
| ⚠ **and the sentence changes anyway** | *«you already have an active session elsewhere»* is a **diagnosis the server is not able to make**: it does not know whether the other client is another device or the same user who just dropped. ⇒ It must say **what it knows** — that the slot appears occupied, and for how long the occupant has been silent |

### 3.1-septies ✅⭐⭐⭐ The phase 9 cures are **SWITCHED ON** — and the phase's yardstick is *«solidity, not miracles»*

*24 Aug 2026, after watching. «Il prodotto cambia in meglio; questa fase era per rendere più
solido il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli.»*

⭐⭐ **It is the sentence that defines when the phase is finished**, and it must be read as a criterion, not as a comment:
the goal was not to **save** the experience on any network — it was **not to make it worse**, not to
lie, and not to pretend that a broken line is a slow line. ⇒ Measured against this yardstick, the
phase **hit the target**; measured against «works even at 10 % loss», it would never have
hit it, and no amount of work would have.

**The five cures go from off to on by default:**

| cure | new default | what it buys | ⚠ what it costs |
|---|---|---|---|
| **audio silence** | on | `[M]` **102× less traffic** with a still screen (557.6 → 5.5 kbit/s); pure test tone **1.000** | the client's `mancati` +2 out of 5,000 |
| **ghost eviction** | 15,000 ms | `[M]` the ghost from **32.13 s / 14 refusals** to **16.83 s / 7** | nothing visible; ⛔ it does not touch `SILENZIO`, and holds only between clients of the **same** user |
| **dead line** | on (stall 5 s · silence 10 s) | it says the wire is broken instead of leaving a still screen that looks like a dead program | ⛔ **it closes a session**: margin **10×** above the worst line that holds, **2.9×** below the one that serves nobody |
| **queue threshold** + **rate regulator** | 100 ms · on | `[M]` keyframes from **51.7-88.1 %** to **0.0-5.6 %**; rate from **1.7 to 2.8 times** | ⚠ **up to +160 ms** of drift on a bad network; **zero** on the healthy line |

⛔ **Why they were off, and why now they no longer are.** Invariant **I6** — *what changes
what the user sees stays behind a switch that is off until he has looked at it* — served
exactly the purpose it exists for: in v1 the corresponding phase was reset for having delivered improved numbers
that the director had never seen. ⭐ The precondition is now **satisfied**: the user
looked (§19.6 the cures at 10 %, §20.3 the sync) and decided.

⚠ **And part of the wait was ceremony, not process** — it must be written so that it is not repeated: two
of the five **change nothing of what the user sees or hears**. The audio silence is
inaudible *by measurement*; the ghost eviction does not add a message, ⭐ **it removes a false one**.
Keeping off a cure that eliminates a lie is not prudence. ⇒ **I6 holds for what is seen, not for
everything that is touched**, and next time the distinction must be made beforehand.

⛔ **What they do NOT promise**, and it must be written next to the numbers or someone will read them as a
promise: `[M]` §19.6 — **at 10 % loss the cures do not save the experience.** They cure the
mechanism (delivery continues instead of stopping, frames never sent from 27 to 1) and the user
says *«bloccato»* all the same. ⇒ Above a certain loss the degradation ladder **has nothing more
to offer**, and the only honest answer stays §3.1-quater: **declare the line dead**.

### 3.2 🔸 Invariant I1, rewritten

The rate **never drops** out of prudence, to save, or because the scene is still. It drops **only**
when the measurement proves the line does not carry, and every descent is declared in the log.

The wound of v1's phase 10 stays protected — the ban on saving is intact — but it no longer
prevents giving way when giving way is the only sensible thing. The prudent heuristic is forbidden,
measured adaptation is mandatory.

*Applied in `CODER.md` §2 and `REVIEWER.md` §3, which go as a pair.*

### 3.3 ✅ Below the minimum, frames are dropped. Never blur, never disconnect.

*8 Aug 2026. «continuare a calare i fotogrammi, mai staccare».*

On a desktop **degrading in time is better than degrading in space**: at a few frames
per second each one stays sharp and text can be read — it is slow but you can work. Blurring
the image makes text unreadable and you can no longer do anything. And at a low rate more
bits can be spent on each frame: slowness is paid only once.

### 3.4 🔸 «Signs of life» are checked from the receiving side

A client is alive if **its packets arrive**, not if we have not received errors
(`LEZIONI.md` §1.7). QUIC does it by itself, with its own heartbeat and its own idle timeout:
it need not be invented, it must be read from the right side.

---

## 4. The session

### 4.1 ✅ The session outlives the client; it is the user who closes and resumes

*8 Aug 2026. «è l'utente da solo che capisce che è meglio chiudere il client (tenendo la
sessione aperta) e continuare quando la situazione migliora».*

It is v1's invariant I4 (`palco.c`, 1,545 lines, among the code that survives), here promoted
from implementation detail to **behaviour promised to the user**.

### 4.1-bis ✅ ⭐ The server does not throw out a healthy session — and every closure of its own has a reason it can explain

*Decided by the user on **11 Aug 2026**, following decision §7.14: «il server non deve
attaccare. È l'utente che decide di fare il logout oppure chiude il client (la scheda del browser)».*

⛔ **It is the user who closes.** The server **never** terminates a session that is working: whoever
leaves, leaves because they decided to leave — with logout or by closing the tab. It is §4.1 seen
from the other side: there the session **outlives** the client, here the server **does not take it away**.

> ### ⚠ And the strict wording was chosen knowing which one it discarded
>
> *The two readings were put before the user on 11 Aug, and he chose the first.*
>
> | | |
> |---|---|
> | ✅ **chosen** | *the server does not throw out a **healthy** session; it closes only for a reason it can explain* |
> | ❌ **discarded** | *the server **never** closes, in any case* — ⛔ and the ban of §1.9, the refusal of credentials, the rigor rule of `RCP.md` §3 and the three caps of §4.6 would fall, that is four defences of which **three were decided by the user himself** |

⭐ **What this rule really forbids, and it is more than it seems**: it forbids closing **without a
sayable reason**. There is no session that ends «just because», nor one that ends with a
number instead of a sentence. ⛔ Every path in which the server closes **must** carry with it a
reason from `RCP.md` §8.2 **and** the sentence the user reads — and if a path does not have it, that
path is a defect, not an oversight.

**The closures that remain, and each has its sayable reason:**

| who closes | why it stays |
|---|---|
| the ban after three attempts (`§1.9`, `RCP.md` §4.4-bis) | ⭐ **decided by the user on 10 Aug**, and whoever is banned **sees a page that tells them so** |
| wrong credentials — `RESPINTO` | it is the farewell of authentication, `RCP.md` §4.4 |
| the rigor rule — `ERRORE_PROTOCOLLO` | `RCP.md` §3: whoever receives something they do not understand **must** close, or a defect goes unnoticed |
| the three handshake caps — `TEMPO_SCADUTO` | `RCP.md` §4.6, and they come **before** a session exists: there is nothing healthy to throw out yet |
| the user is already connected elsewhere — `GIA_ATTIVA_REMOTA` | invariant I2 |
| ⚠ **the disconnect after 30 minutes without input** (`§4.3`) and **the closure at 6 hours** (`§4.2`) | ⛔ **decided by the user on 8 Aug**, and they are the two that seem to contradict this rule and do not: the first **disconnects the client and leaves the session alive**, the second reclaims the resources of a session that **has given no sign of life for six hours** — that is, it is no longer «healthy», it is abandoned |

⛔ **And this rule is measured, not declared.** The bench that verifies it already exists and it is **B7**:
it provokes every farewell reason and checks that it arrives **on the receiving side**, with a distinct
sentence for each. ⭐ From today B7 no longer counts just *«seven reasons out of seven»*: ⛔ **it is the bench of
this decision**, and its denominator is *«how many closing paths the server has»* — not
*«how many I know»*. A path that closes without a sayable reason **does not appear** in a bench
that starts from the list of reasons: it is found only by starting from the code.

⚠ **It touches `DECISIONI.md` §7.17, which is still ❓**: a WebTransport session that never opens the
control channel today **has no cap on it** and stays there for ever. It is not a healthy
session — it is not a session at all — so this rule does not protect it. **But how long it may stay
there remains to be decided**, and this line does not decide it.

### 4.1-ter ✅ ⭐⭐ The two exits are not the same exit: the wire that drops, and the logout

*Decided by the user on **15 Aug 2026**, at the opening of phase 5: «distinguiamo il comportamento
del PC usato dall'utente rispetto a quello che fa REMOTIX. Se l'utente chiude, spegne o riavvia il
**proprio** PC, questo lo trattiamo come browser chiuso / connessione caduta. Se invece sceglie la
voce «Esci/logout», allora significa che l'utente vuole **terminare la sessione**, il che comporta
la chiusura di tutti i programmi che aveva in esecuzione».*

§4.1-bis said **who** closes — the user, not the server. This one says that that user has **two
gestures**, and that they lead to two different places.

| the gesture | what it is for us | the outcome |
|---|---|---|
| ⭐ **the wire drops** — tab closed, browser closed, **the user's PC switched off or rebooted**, signal lost in a tunnel | ⭐ **one single case**, and there is nothing to distinguish: the user's PC is not an actor of our model | the slot is freed, **the session stays alive** (I4). The `CONGEDO 0x01` goes out if it is in time; if the PC dies suddenly it does not, and what frees the slot is the 30 s silence clock (§4.4) — **same outcome, another road** |
| ⭐ **«Esci/logout» from the desktop menu** | the only gesture that declares *«I'm done»* | ⛔ **the session ends, and the user's programs close**. Nothing to reattach to |

⭐ **The gain of this distinction is that it removes work instead of adding it**: the client side does not
have to detect anything — shutdown, reboot and closing the tab are **the same thing, already
implemented and measured** (`pagehide` → `CONGEDO`, `pagina.html` · `canale_corrente()`).

**And three consequences that were not chosen, they fell out by themselves:**

1. ⛔ **`org.gnome.desktop.lockdown disable-log-out` is FORBIDDEN.** It removed the «Esci…» item **and**
   made `org.gnome.SessionManager.Logout` be refused (`STUDI.md` §gnome §5.1). Now that logout is a
   **promised** function, that key would remove the function. ⇒ to remove Power Off/Restart/
   Suspend **only** the polkit rule on logind remains, and ⭐ the server's farewell
   (`sessione_termina()`) and the user's logout **go through the same door**.
2. **`org.gnome.shell always-show-log-out` must be switched on.** `[R]` `systemActions.js:394-410`: without it,
   on a machine with one user and one session gnome-shell **does not show** the item. ⚠ It reverses
   `reference-gnome/rapporti/02-shell-blocco-voci.md:214` — *«it must be left `false`»* — written when
   the goal was to remove items, not to provide one.
3. **Between the click and the end we touch nothing**: a program with unsaved work makes
   **GNOME's** dialog appear inside the remote desktop, as if the user were at the monitor (I8).

### 4.1-quater ✅ ⭐ After logout the page goes back to the login form — and the reason is new

*Proposed and accepted by the user on **15 Aug 2026**: «concordo, la pagina torna al modulo di
accesso».*

Once logout is finished, the browser is looking at **the last frame of a desktop that no longer exists**.
The page **goes back to the login form**, with the line *«the session has ended»* above it: whoever wanted
to leave is done, whoever clicked by mistake comes back in by typing the password and finds a clean
desktop. ⛔ **Not a closing screen**, which would be a dead end you get out of by reloading.

⛔ **And a new reason is needed — `0x10 SESSIONE_TERMINATA` (`RCP.md` §8.2)**, not the reuse of `0x01`:
`CHIUSO_DALL_UTENTE` carries the promise *«reattach and you find everything»*, which after a logout is
**false**. Two opposite outcomes under the same code are the form of defect that `CODER.md` §4.2
forbids: a silent fallback produces two behaviours under the same label.

⚠ **And the real defect of this path is the ORDER, not the code**: when Mutter falls, the stage
falls with it and the channel is no longer of use. The reason must go out **before**. It is the same form as
finding **B-7** — a reason that exists and that nobody sends in time.

### 4.1-quinquies ✅ ⭐ Logout also has a shortcut — `Ctrl+Alt+Fine`, and the PAGE handles it

*Wanted by the user on **15 Aug 2026**: «vorrei venire incontro all'utente per permettergli di
effettuare il logout anche usando una combinazione di tasti». He chose the combination himself, among
three proposals.*

⛔ **Two combinations were tried and rejected BEFORE writing a line, with one measurement
each** — they must be written here or someone will propose them again:

| rejected | why, with the mark |
|---|---|
| ❌ `Ctrl+Alt+F12` — the user's first idea | `[R]` it is the **default of `switch-to-session-12`** (`org.gnome.mutter.wayland`), and Mutter registers it even headless because the backend stays the **native** one (`keybindings.c:2797`, `NATIVE_KEYBINDINGS`). ⛔ It is **`NON_MASKABLE`**: no application can take it. Injected, it would be swallowed and Mutter would try to switch to a virtual console **that does not exist headless** — a warning in the log and nothing else. ⛔ **And on the user's PC, if it is Linux, it does not even reach the browser**: his compositor takes it, for the very same reason |
| ❌ `Win+F12` — the second | ⭐ `[M]` **measured in house, 14 Aug**: in the catalogue of probe S3 `Super+KeyD` is **`non-consegnata` in all four stages** — window, full screen, full screen **with Keyboard Lock granted**, and installed PWA. Combinations with the Windows key **never reach** the page. ⛔ And on Android and DeX **every** combination with Meta is lost by AOSP rule — that is precisely where it is needed most (`SPECIFICHE.md` §7.3-bis) |

✅ **Chosen: `Ctrl+Alt+Fine`.** ⭐ `[R]` **Nobody binds it**: searched as `<Primary><Alt>End` in
all the GNOME and KDE sources we have in house, zero hits. ⚠ **And the two prices, declared
because the user chose them knowing them**: it has **two** modifiers instead of three, so it is easier
to press by mistake; and it has an **RDP precedent that says something else** — there `Ctrl+Alt+End` sends
`Ctrl+Alt+Canc` to the remote session, so someone coming from RDP might expect that.

**⭐ The PAGE handles it, not the desktop**, and the three reasons carry different weight:

1. **once instead of four times**: bound to the desktop it would have to be redone for GNOME, KDE, XFCE and LXQt,
   each in its own way — that is four configuration lines, which is I7 lying in wait;
2. ⭐ **it works when it is needed**: bound to the desktop, the key would have to cross browser → network →
   `libei` → compositor, and it would not arrive precisely in the case in which one looks for it — with the desktop
   no longer responding;
3. **it ends at the same door as the menu**: `org.gnome.SessionManager.Logout`, that is
   `sessione_termina()`. ⇒ a single exit path, not two that can diverge.

⛔ **And the page swallows it with `preventDefault()`: in the remote session that combination will
never arrive.** It is the price of every REMOTIX shortcut, and `SPECIFICHE.md` §7.3-bis obliges us to
**declare it** instead of letting it be discovered.

**One thing that comes with it, and one that was removed:**

- ⭐ **an on-screen confirmation** — *«end the session?»*. From the menu logout costs three
  deliberate gestures; a combination costs one, and closes **all** open programs. ⚠ The confirmation is
  also the defence against the RDP misunderstanding above: whoever expected `Ctrl+Alt+Canc` reads what
  is about to happen and cancels;
- ⛔ **no on-screen button for logout** — *removed by the user on 15 Aug 2026: «per quello
  basta la voce del menu di sistema»*. ⭐ **And he was right against the argument with which I had
  proposed it**: I had transferred to logout the reasoning of `Ctrl+Alt+Canc` (`SPECIFICHE.md`
  §7.3-bis), which has the button because **it has no menu item**. Logout has one, and
  that item can be reached **with the pointer and with a finger** — so it exists even where the keyboard is
  entirely lost, iPhone included. ⇒ ⚠ **The general rule, not to be paid for again**: an on-screen button is
  justified when **there is no other road**, not when the road that exists goes through a key.

⚠ **And before being promised it must be MEASURED**: probe S3 (`banchi/04-b29-scorciatoie.py`)
tried 42 combinations on two engines and `Ctrl+Alt+Fine` **is not among them**. It is added, measured
on two engines, and if it does not arrive on one the page **declares it** — §7.3-bis: *we do not pretend
they work*.

### 4.2 ✅ After 6 hours without signs of life the session is closed

*8 Aug 2026, proposed by the user.* The value stays, and with §4.3 its job is clarified:
**reclaiming resources**, not defending security — the 30-minute disconnect takes care of that.
On a multi-user server every forgotten session holds memory, GPU and an
encoder.

### 4.3 ✅ The lock is REMOTIX's, not the desktop's — 30 minutes without input, then disconnect

*8 Aug 2026. «Se non arriva input dall'utente per 30 minuti la sessione si blocca:
l'utente dovrà fare il re-attach con user e password».*

After 30 minutes without input, REMOTIX **disconnects the client**. The desktop stays as it was, but nobody
sees it any more: to see it again a new attach is needed, with user and password.

⛔ **The desktops' screen lock stays off**, as it was in v1 — `--no-lockscreen` on KWin and
the equivalents on the other three. It is not an inherited oversight: it is a dependency, and now it has a
written reason. The four roads of «mode A» are these, all `[R]`:

| Desktop | What happens when really locking |
|---|---|
| **GNOME** | ⛔ **the revocation.** On entering the unlock dialog, gnome-shell calls `inhibit_remote_access()` and Mutter **closes ScreenCast, RemoteDesktop and InputCapture, refusing to recreate them** (`STUDI.md` §gnome §4). There is the `is_headless()` exception, which is our case — but it is read in the code and **never measured** |
| **KDE** | ⛔ **the chain that bites its own tail.** With the lock active our inhibition is ignored (`powerdevilpolicyagent.cpp:509`); powerdevil turns the screen off at 10 minutes; with zero outputs KWin mounts a dummy output **with a filter that swallows all input** (`STUDI.md` §kde §10.2-10.3). You get locked and never unlock again |
| **XFCE, LXQt** | their idle daemons, and on LXQt `enableIdlenessWatcher=false` **is rewritten to `true`** by the daemon at first start (`STUDI.md` §lxqt) |

**The three reasons for the choice**, in order of weight:

1. **one behaviour for four desktops**, instead of four fragile cures — and three of
   those cures would be configuration lines, that is what invariant **I7** forbids;
2. **the count is ours and has no unknowns**: we inject the input, so we know
   exactly when the last one passed. With mode A we would have to trust that each desktop's idle
   detector sees `libei` events — on KDE it is `[R]` that it does
   (EIS → `simulateUserActivity`), on the other three it would have to be measured;
3. **security is the same**: the only road to that desktop goes through RCP, and RCP goes
   through PAM. The lock screen would ask for the same password.

> ⚠ **And this decision has an expiry condition, set by the user the same day:**
> *«non escludo che un domani potremmo implementare un metodo di autenticazione molto più forte
> della semplice password, ma per il momento va bene solo questa»*.
>
> The reasoning of point 3 **holds only as long as the PAM password is the only key**. The day
> RCP authenticated with something different — a token on the device, a key, a
> second factor — the desktop lock would stop being redundant and would become a
> real defence, because it would ask for a key **that whoever stole the first one does not have**.
>
> **Whoever implements strong authentication rereads this item**, and does not take it for granted.
>
> ⏳ **And that day has an opening date, decided on 9 Aug 2026**: the evolution with MFA,
> postponed until the project is complete — §1.7, the security-debt box.

### 4.3-bis 🔸 ⛔ Being *headless* on GNOME is a requirement, not luck

*Written on 9 Aug 2026, reading `STUDI.md` §gnome §4 and lesson 3 of its §14.*

§4.3 says the desktops' screen lock stays off, and for GNOME the reason is the **revocation**:
on entering the unlock dialog, Mutter closes capture, control and input **and refuses to
recreate them**. The only exception is `is_headless()` — and that exception is our condition.

⛔ **But it is not a condition we asked for.** Mutter puts itself into headless **by itself** when
the logind session is of type `wayland`, active and **seatless** `[R]`. No line of ours
asks for it, none verifies it, and the day the session were born with a seat — a `gdm3`
configured differently, a test done by hand, an incomplete restore — we would lose capture and
input **without anyone connecting the two things**.

**Hence, and they are three distinct obligations:**

1. the session is composed **declaring** that it must be headless, not hoping it becomes so;
2. the outcome is **verified after start-up**, as for the transparent cursor theme of §5-bis.2 —
   that the precondition is written does not mean it was obtained (`REVIEWER.md` E1: necessary is not
   sufficient);
3. if it is not, the **failure is declared** instead of carrying on: it would be a session that
   works until somebody locks the screen (`CODER.md` §3.9, §4.2).

⭐ **It is invariant I7 in a form we had not foreseen.** I7 says that the protection against a
known defect does not lie in a configuration line that can be lost; here it lies **nowhere** —
it lies in a fallback behaviour of Mutter. `STUDI.md` §gnome §14 puts it better: *a
condition that saves us by accident must be written as a requirement.*

⚠ And the measurement that closes it is **M2** of `STUDI.md` §gnome §13: headless yes/no against
`inhibit_remote_access`. Until then the expiry clause of §4.3 holds here too.

### 4.4 ✅ A client that falls silent is a client that has detached

*8 Aug 2026. «Fantasma: lo trattiamo come nel caso in cui l'utente chiude il client».*

No connection «holds the slot». Whoever is silent is detached, whoever arrives gets in — without a timeout to
wait for, without a takeover to negotiate, without the case «the phone died in a tunnel and now
I can't get back into my session» that v1 had had to patch with tight keepalives.

So the fork *takeover versus waiting* disappears too: it no longer exists, because the
occupied slot does not exist.

> ### ⛔ Clarified on the evening of 9 Aug 2026 — this item spoke only of the **ghost**
>
> *«Se un utente ha già una sessione grafica remota attiva, e ne vuole attivare una seconda da un
> secondo device, la seconda connessione viene rifiutata.»*
>
> The review of `RCP.md` found that the protocol could not express the **remote
> versus remote** case — you are attached from the laptop and you open from the phone — and that the available reasons
> all said «local», that is they would have shown the user a false sentence.
>
> ⭐ **The complete rule is two lines, and the discriminant is the silence clock:**
>
> | The client that was there | What happens to whoever arrives |
> |---|---|
> | **silent for 30 seconds** — the ghost of this item | it is **detached**, it occupies nothing: whoever arrives **gets in** |
> | **is alive and attached** | whoever arrives is **refused**, with `GIA_ATTIVA_REMOTA` (`RCP.md` §8.2) |
>
> ⭐ **The second line is not new: it is invariant I2** — *«the second connection is refused with an
> explicit message»* — which nobody had connected to this item. And the new reason is the remote twin
> of `GIA_ATTIVA_LOCALE`, just as `SPECIFICHE.md` §5.1 already has the local pair.
>
> ⚠ **The price, declared**: if the laptop switches off suddenly without saying farewell, from the phone you
> get in **after thirty seconds**. It is the same clock as §4.5, and nobody has moved it.

### 4.5 🔸 The three clocks of the session

Decisions 4.1-4.4 line up three different times, which must be kept distinct because
they measure different things:

| Clock | How long | What fires | Decided in |
|---|---|---|---|
| **client silence** | **30 seconds** | the client is considered detached | §4.4, value in §7.3-bis |
| **user inactivity** | **30 minutes** without input | REMOTIX disconnects the client | §4.3 |
| **session abandonment** | **6 hours** without any attach | the session is closed, with a clean farewell | §4.2 |

They are in scale: the first is measured in seconds, the second in minutes, the third in hours. A user
who leaves the client open and goes to lunch is disconnected after half an hour and finds everything
on reattaching; if he does not come back within the following six hours, the session is reclaimed.

⚠ **A consequence to keep an eye on**: «input» is what the user sends, not what he
watches. Whoever spends half an hour watching a video without touching anything is disconnected. The cost is
small — reattaching is quick — but if it emerged as an annoyance, the cure is a sign of
presence from the client, not lengthening the threshold.

### 4.6 ✅ Ten graphical sessions as a cap — but the limit is a budget, not a count

*9 Aug 2026. «Quante sessioni grafiche può reggere contemporaneamente il sistema fra locali e
remote? […] credo che 10 potrebbe essere un numero molto comodo». And then: «il mio è un tetto: non
capiterà mai che ci sono 10 utenti contemporaneamente che si collegano con client in 4K».*

> ⚠ **And at phase 1 this cap is not honoured, and it is a declared fallback**: the server runs on **a
> single thread** and the PAM check **blocks** it, so ten users coming in together queue up
> (with the fixed second of `RCP.md` §4.4-bis, the last one waits **ten seconds**); and the table
> of attached sessions is a `#define` at **16**. ⛔ It is not a decision that changes: it is a promise
> **not yet due**, and it is written in `SPECIFICHE.md` §5.5 and in `FASI.md` §01-filo-nudo so that the
> day it is due one knows where to start again. *Brought out of the comment in `src/main.c`
> on 11 Aug 2026, finding **R12C.17**.*

⛔ **Ten is not the limit: it is the administrative cap.** The real limit is set by the
**encoder**, and it is measured in pixels per second — with the same hardware, the same ten sessions
are very easy or impossible depending on the quality each asks for.

> ⛔⛔ **THIS LINE WAS CORRECTED ON 24 AUG 2026, AND BY THE MEASUREMENT: the limit is NOT set by the
> encoder.** It is set by **composition**, which gives way at **half** — and the rest of the section,
> table included, must be read with **§4.6-nonies** in front of it. ⭐ The part that holds is *«the limit is a
> budget, not a count»*: the measurement **confirmed** that. ⛔ What falls is **which
> engine** the budget belongs to.

On the test hardware — i5-13500T, 31 GB, Intel UHD 730 (Alder Lake) `[M]` 9 Aug:

| 10 sessions at… | To encode | On the Intel alone |
|---|---|---|
| 480p · 25 fps *(the minimum)* | ~100 Mpixel/s | ⭐ very wide, fifty or so |
| 1080p · 30 fps | ~620 Mpixel/s | ✅ right at the limit |
| 4K · 60 fps *(the desired)* | ~5 Gpixel/s | ⛔ **a single session** |

> ### ✅ Confirmed `[M]` on 9 Aug 2026 — `vainfo` installed and run on the hardware
>
> *They were `[?]`, derived from the chip's generation. Now they are read from the driver, on the two nodes.*
>
> | | Intel UHD 730 — `renderD128`, iHD 25.2.3 | Radeon RX 6800 — `renderD129`, radeonsi navi21 |
> |---|---|---|
> | **HEVC Main10 encoding** | ✅ **yes** (`EncSliceLP`) | ✅ yes (`EncSlice`) |
> | HEVC Main **4:4:4**, 8 and 10 bit | ⭐ ✅ **yes** — see §2.3 | ⛔ no |
> | H.264, VP9, JPEG encoding | yes | H.264 yes |
> | **AV1** | ⛔ **no profile, not even for decoding** | **decoding** only (`AV1Profile0`, `VLD`) |
>
> ⛔ **The 10-bit desired has its hardware road on both cards**, and it goes through
> HEVC Main10 as `SPECIFICHE.md` §11.4 foresaw. The preference ladder of §11.4 stays valid:
> `hevc_vaapi` is the first entry and the machine has it.
>
> ⚠ **A detail not to lose, which touches phase 8**: on the Intel the only encoding entrypoint is
> `EncSliceLP` — the *low power* path. It is not a fallback, it is the only one that chip exposes; but it is
> a path with bitrate control options of its own, and it is precisely the place where v1
> hurt itself twice (`LEZIONI.md` §1.8: the driver that deduced the control mode from how
> two fields were filled, constant bitrate without anyone having chosen it). **It is asked for by
> name and verified that it obeyed.**
>
> ⭐ And the budget table above stays `[?]` for another reason: `vainfo` says **which
> profiles** there are, not **how many pixels per second**. The number of sessions must be measured by saturating,
> and that is phase 10.

**Hence the design**: no number hard-wired in the program. The server keeps a **budget** — it knows
how much it is already encoding and how much it can — and ten is the default value of a configurable
maximum, like the six hours of §4.2. RAM is not the bottleneck: ten idle GNOME sessions are
~12 GB of the 31, ten LXQt ~5.

### 4.6-bis 🔸 When the budget is full, refuse, declaring the reason

Whoever is already working is not degraded to let the newcomer in. It would be the seemingly
kind choice, but it silently punishes whoever has done nothing — and it is precisely what
I1 forbids: a descent that does not come from a measurement of the line, but from a decision taken
elsewhere and never declared.

The refusal says **why**: «this machine has no more encoding capacity». Not just «try again
later».

### 4.6-ter 🔸 ⛔ The GPU is chosen with a udev rule, and it has a price to know beforehand

*On the user's hardware REMOTIX uses **the Intel**; the Radeon RX 6800 is reserved for inference.*

The mechanism already exists: `fondamenta/banco/gpu-udev.sh`, and its header explains why there are
no simpler ones:

- **KWin takes the first card it manages to open** and looks at no variable
  (`KWIN_DRM_DEVICES` holds only for the `drm` backend). The only way to choose one is to make
  the other **unopenable**;
- ⛔ **and the obvious way is a trap**: `InaccessiblePaths=` in the compositor's unit gives the
  right card and **closes the capture gate** — 0 log lines about permissions against
  13 (`STUDI.md` §kde §3.3-bis). One goes through the **node**'s permissions;
- ⚠ **by PCI id, not by node number**: `renderD128` and `renderD129` swap between one
  boot and another, the PCI address does not.

⚠⚠ **The price, which the script already declared before inference existed**: denying the node
with permissions denies it to **the user's whole session**, not only to the compositor. On the current
hardware this means that **the user doing inference must be put in the group** of the rule, and
the users of remote sessions must not. It works — but if one day inference stopped seeing
the Radeon, the cause is this file, and nobody would connect it on their own.

⭐ And the warning of `LEZIONI.md` §4 trap 6 — *«the compositor must draw on the right
card; a buffer from another card cannot be imported, and the symptom is software composition
without an error»* — stops being theoretical on a machine with **two** GPUs.

> ### ⭐ On Mutter the mechanism is another one, and for now it plays in our favour — `[M]` 9 Aug 2026
>
> This item is written about KWin, which *«takes the first card it manages to open»*. Not Mutter:
> at phase 0, with both nodes visible, it declared by itself
>
> > `Added device '/dev/dri/renderD129' (amdgpu)` · `Added device '/dev/dri/renderD128' (i915)` ·
> > **`Boot VGA GPU /dev/dri/renderD128 selected as primary`**
>
> — that is, it chose **the Intel**, which is the one we want, with a criterion of its own (*Boot VGA*) and
> without anyone asking it. **On the current hardware the udev rule is not needed for GNOME.**
>
> ⛔ **But it is not concluded that it is not needed.** It is again a condition that saves us without our
> having asked for it (§4.3-bis): it depends on which card is the BIOS's *Boot VGA*, which is outside
> our control and changes by moving a cable. The udev rule stays the **declared lever**; this
> measurement only says that today, on GNOME, it is not what decides.
>
> ⚠ And a line to understand, not yet understood: `amdgpu_cs_ctx_create2 failed. (-13)` — the Radeon is
> seen and **not openable** (permission denied). `[?]` Whether it is already this file's udev rule or
> something else has not been established. It does not get in the way: the primary is the right one.

### 4.6-quinquies ✅ ⛔ **Measure on the INTEGRATED GPU**, not on the discrete one

*Constraint set by the user on **15 Aug 2026**, watching the recording of Aquarium at 60 fps:
«i test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco. La solidità del sistema la
si vede su GPU poco potenti, non mostri come la RX 6800».*

⭐ **It is a rule of method, and it is worth more than the measurement that provoked it**: a number taken on the best
hardware does not say whether the product holds — it says how fast that hardware is. `LEZIONI.md` is full of
measurements that looked like a result and were a property of the bench.

`[M]` **The test machine has two cards**, and until tonight **the compositor chose**:

| | PCI address | node | which |
|---|---|---|---|
| ✅ **this one is used** | `0000:00:02.0` | `renderD128` | **Intel UHD 730** (`i915`), the integrated one |
| ❌ excluded | `0000:03:00.0` | `renderD129` | Radeon **RX 6800** (`amdgpu`) |

⛔ **And it was not a choice: it was an accident.** Without the udev rule of §4.6-ter — `[M]` it was not
installed, `/etc/udev/rules.d` was empty — the `video`/`render` groups give access to **both**, and
`[M]` the compositor had taken the **Radeon**. ⇒ The Aquarium measurement of 22:09 —
60 fps nailed — was made **on the wrong card**, and must be redone.

**The cure is the one already decided in §4.6-ter, finally applied**: `fondamenta/banco/gpu-udev.sh` with
the address to **exclude**, which moves the node into a group with no members. ⭐ `[M]` after
restarting the user manager and the session, `gnome-shell` opens **6 descriptors on `renderD128`**:
the integrated one, and only that.

⚠ **And the price stays what §4.6-ter declares**: denying the node denies it to **the user's whole
session**, not only to the compositor. Whoever one day wanted the Radeon for something else — a
transcoder, a game — would find it closed, and nobody would connect the thing to this file.

⏳ **And phase 8 inherits one more question**: hardware encoding chooses its card on its
own (VA-API). ⛔ If the compositor draws on the integrated one and the encoder looks for the discrete one —
which here is closed — the fallback is on the CPU, and it is the case that `LEZIONI.md` §1.8 says to **declare**
instead of suffering.

### 4.6-quater ✅ ⭐ The multi-tenant boundary: phase 5 holds **one user at a time**, the multi-tenant phase the full machine

> ⚠ **The number of that phase changed on 16 Aug 2026 — it was 12, now it is 10** — and the
> **boundary decided here is intact**: see **§4.6-sexies**. The title said *«12 the full
> machine»*, and now it says the thing without the number, which was the fragile part.

*Asked by the user on **15 Aug 2026** at the opening of phase 5 — «poiché qui trattiamo le
sessioni, mi chiedo se il multi-tenant non ricada in questa fase» — and decided by him the same
day: «potremmo anche lasciare in questa fase 1 solo utente, e nella fase 12 il multi-tenant».*

⚠ **The question was good because the two documents said different things**: `SPECIFICHE.md` §5.5 says
*«multi-tenancy belongs to the phases from 5 onwards»*, `PIANO.md` titled **phase 12** «Multi-tenant and the
budget». The boundary, decided:

| | where | why there |
|---|---|---|
| **multi-tenancy as a function** — several remote sessions together, the encoder's **budget**, `BUDGET_PIENO 0x06`, the refusal that does not make whoever is already working worse, `MAX_ATTACCATE` that stops being a `#define` | **phase 10** | ⭐ they need **a real number**, and the real number is given by the hardware encoder of **phase 8**. Measuring them earlier means measuring them twice (`LEZIONI.md` §7.2) |
| **one remote user at a time** | **phase 5** | it is the scene the phase promises, and it is already loaded enough: logout with its new code, the three belts of §4.7, the logind guard, the three clocks, the key release, the suspend inhibition, the declared headless |
| ⛔ **code keyed on the user**, and the logind guard that **discriminates per user** | ⭐ **phase 5, and it cannot be postponed** — see the box | ⛔ not because it is important: because **it cannot be written «for a single user»** |

> ### ⛔⭐ The piece that cannot be postponed, and the reason is that the machine unmasks it by itself
>
> The logind guard that must emit `0x04` and `0x05` (`SPECIFICHE.md` §5.1) answers a
> question that sounds in **two very different ways**:
>
> > *«is there a local graphical session?»* — or — *«is there a local graphical session **of this
> > user**?»*
>
> ⛔ **One line of difference in the code, two different products.** And the test machine is **already**
> in the configuration that unmasks the error: `nicfio` has his **local** graphical session,
> `prova` connects **remotely**. Written the wrong way, `prova` is refused with `0x05`
> — *«there is already a local graphical session»* — **on the first day, at the first test**, because the
> local session really is there: it just belongs to someone else.
>
> ⭐ **There is no need to invent a multi-user scenario: it is the machine's normal state.** ⇒ The bench
> of `0x04`/`0x05` is written on that pair — local `nicfio` and remote `prova`, which **must
> coexist without touching each other** — and it costs what it would cost anyway.

⚠ ~~**And what stays a fallback stays declared**: `MAX_ATTACCATE` is a `#define` at **16**, and
`MAX_FIGLI` at 16, which declares it follows it — where `SPECIFICHE.md` §5.5 promises **ten,
configurable**. Today it does not bite — 16 > 10 — and its deadline is phase 10.~~
> ✅ **PAID on 25 Aug 2026, evening — phase 10** *(realigned to the code on 28 Aug)*. The number
> is now **a single one**: `RCP_TETTO_SESSIONI` in `src/rcp.h`, it is **10**, and it is changed with
> **`--tetto-sessioni N`**. The `#define` is the default; the value in force is given by `rcp_tetto()`.
> ⭐ And the four tables (`MAX_ATTACCATE`, `MAX_FIGLI`, `QUANTI_PRESENTI`, `WT_PALCHI`) are now
> **allocated** on that number instead of being four hand-made copies that diverge silently —
> the defect that `src/rcp.h` recounts at length, and that `[M]` §6.4 had proved in the field.
⚠ *The reference said `rcp.c` · `MAX_ACCUMULO`, and the `#define` is at **568**: corrected on 16 Aug 2026
by rereading the file. ⛔ A line number ages silently — it is the reason why the name of the constant
is next to it too.*

### 4.6-sexies ✅ ⭐⭐ The order changes: multi-tenancy **before** the new desktops

*Decided by the user on **16 Aug 2026**, reviewing the plan before opening phase 6: «PRIMA si
chiude lo sviluppo anche con il multi-tenant, e solo dopo si pensa agli altri DE».*

⛔ **The boundary of §4.6-quater does NOT change**: «one user at a time» stays in phase 5, «the full
machine» stays in the multi-tenant phase, and code keyed on the user stays non-postponable.
⭐ **Only where that phase stands in the queue changes** — and with it its number:

| | before | ⭐ now |
|---|---|---|
| Multi-tenant and the budget | phase **12** | **phase 10** |
| KDE | phase 10 | **phase 11** |
| XFCE and LXQt | phase 11 | **phase 12** |
| Quality and degradation | phase 9 | **phase 9**, unchanged — and now it has a second client: the degradation ladder is **the way** several sessions fit on the same machine |
| The service | phase 13 | **phase 13**, unchanged — ⛔ and it stays last **for a reason**: §7.16 has it **remove from the binary** the bench marks `BANCO_MARCA`/`BANCO_ESITO`, which the desktop phases will use to measure themselves. Putting it earlier would mean removing the yardstick and then testing three new desktops without it |

⭐ **The reason is that of §4.6-quater, applied from the other end.** There it was said: *«measuring the
budget before the hardware encoder means measuring it twice»* (`LEZIONI.md` §7.2). Here:
⛔ **the budget is a GPU budget, and the GPU is one** — `renderD128`, the same iGPU that composes
**every** desktop. It is a property **of the machine**, not of the desktop. Measured first, phases 11 and
12 inherit it; measured after three new desktops, one no longer knows which number belongs to what.
⇒ And if multi-tenancy touches the session or the budget, the change must be reverified **on four
desktops instead of one**.

⚠ **And what this decision does NOT buy, said in full**: the multi-tenant architecture is already there
for the most part — `figlio.c` ⚠ *(the code cited is no longer there: to be reread)* declares *«one user per child»*, one process per session. ⇒ We
are not dodging a structural rewrite; we are avoiding a measurement repeated four times.
It is a weaker argument than it seems, and it pulls in the same direction all the same.

⛔ **The precedence that remains**: multi-tenancy comes **after phase 8**, and the reason is unchanged —
**zero copy** changes how much a session costs in GPU memory and bandwidth, and a budget measured
before zero copy is a budget to redo.

> ### ⚠ And the words of 15 Aug say «phase 12»: they stay
>
> The quotation of §4.6-quater — *«nella fase 12 il multi-tenant»* — **has not been rewritten**, neither
> here nor in `FASI.md` §05-la-sessione: it was the number of the time, and correcting a sentence in quotation marks
> is the fastest way to no longer know what was really said.
> ⇒ **The decision was and is the same; it is the place in the queue that has changed.**

### 4.6-septies ✅ ⭐⭐⭐ **Six sessions on an integrated card are a good result — phase 10 closes**

*The user's judgement, **24 Aug 2026**, in front of the first round of multi-tenant measurements:*

> *«Tenendo conto che siamo su una scheda Intel integrata non particolarmente performante, 6 RDP
> attivi contemporaneamente non mi sembra un cattivo risultato»*

*⭐ **Reconfirmed on 28 Aug 2026** — «confermo quel mio giudizio» — when it was discovered that
this section was cited by five documents and **had never been written**.*

⇒ ⭐ **The measured number is accepted as it is**: no hunt is opened to make it rise, and
phase 10 closes on the judgement instead of on a numerical target. It is the same form as
v1's phase 10 decision on quality — *«va bene così»* — and it holds for the same reason:
⛔ **the yardstick is the user, not the number.**

⚠ **And the judgement is given on the WORST case.** The measurements are in
`fasi/10-multi-tenant-e-il-budget.md` §S.2 and §6.12, and are not copied here:

| scene | how many fit |
|---|---|
| **saturated** — the whole screen changes at every frame | `[M]` **6** ← *the number judged* |
| ⭐ **real desktop** — windows, dragging, normal work | `[M]` **at least 11**, and the ceiling **was not found**: the users ran out, not the machine |

⇒ ⭐⭐ **The judgement comes out strengthened, not refuted**: what users really do costs less
than the worst scene, and eleven is a limit of the measuring instrument, not of the machine.

⛔ **And the hardware must be stated every time** this number is cited: Intel UHD 730 **integrated**, not a
dedicated card. A «six» without the hardware next to it is a number someone will compare with the wrong
hardware.

> ### ⚠ And this section has a history worth keeping
>
> ⛔ It was **cited by five documents — `SPECIFICHE.md` included, and by `DECISIONI.md` itself —
> for four days before it existed.** The numbering jumped from `-sexies` to `-octies` and nobody
> had noticed: the judgement was written in three places, but **not where decisions live**.
> ⇒ ⭐ It is the defect that `C16` now catches, and it is the reason why that mesh exists.

### 4.6-octies ⏳ ✅ **The ban by address is NOT touched in phase 10: it goes into a chapter on security**

*Decided by the user on **25 Aug 2026**, in front of the finding of phase 10: «il discorso del ban
rientrerà in un discorso più generale sulla sicurezza, che farà parte di un capitolo evolutivo».*

⛔ **The finding stays true and measured, and is not closed: it is POSTPONED with a name.**
`fasi/10-multi-tenant-e-il-budget.md` §4.2 (**R10-A2**): `rcp.c` · `posto_prendi()` declares *«IL NOME UTENTE NON
CONTA. Tre nomi diversi contano tre»* — and it is the decision of **§1.9**, taken when the product
served **one tenant**. ⇒ With ten tenants **behind the same NAT** the key is **only one**:
`[M]` three of them getting it wrong **once each** in five minutes ban the address, and the
other seven — **who got nothing wrong** — stay out for **twelve hours**. ⛔ And the only way out is
the command socket, which is `0600` of **root**: a tenant **cannot unblock himself**.

> ### ⭐ Why postponing is the right choice, and not a shelving
>
> ⛔ **The cure touches a defence, not a convenience.** What the ban defends — *«whoever tries
> passwords must not be able to try forever»* — is a decision of the user (§1.9), and ⭐ **a
> defence is not dismantled inside a phase that is measuring capacity**: it is redone when security is
> looked at **as a whole**, with all its items in front.
>
> ⚠ **And the piece of design already found stays written, for whoever opens that chapter**: a key
> `(indirizzo, utente)` with the threshold of §1.9 per pair, **plus** a wider threshold on the address
> alone (many different names failed ⇒ ban of the address), keeps the defence against **the real
> attack** — which tries **many names** — and removes the collective punishment for **the typo**.
> ⛔ It is a design, not a decision: the decision belongs to that chapter.
>
> ⭐ **And one thing that phase 10 has already closed**, and that must not be questioned again there: the defect
> **of the key with the port** — the one for which the counter *«valeva sempre 1»* — is **cured by
> construction**, and the adversarial lens verified it line by line (§4.3, track 2).

⚠ **And the price of the postponement, declared**: until that chapter, ⛔ **an office behind a NAT is a
configuration in which the product can lock itself out for twelve hours**, and phase 10 knows it. ⭐ It is not
a hidden defect: it is a defect **measured, named and dated**.

### 4.6-nonies ✅ ⭐⭐⭐⭐ **The budget is of COMPOSITION, not of encoding — and §4.6 must be corrected, not supplemented**

*Measured in phase 10, on **24 Aug 2026**, after the director's order: «prima si misura, e poi
simuli 10 utenti veri».*

⛔⛔ **§4.6 said that the limit is set by the encoder. The measurement says no.**

| where it is spent | which GPU engine | ceiling `[M]` |
|---|---|---|
| the bare **encoder**, synthetic scene | the two VDBOX (`vcs0`, `vcs1`) | **1.86 Gpixel/s** in H.264 · **2.33** in HEVC |
| ⭐⭐⭐ **the COMPOSITION** | ⛔ **`rcs0`**, the render engine | ⭐ **0.97 Gpixel/s — HALF** |

⇒ ⛔ **The bottleneck is upstream of us.** `[M]` What saturates `rcs0` is **`gnome-shell` at 99.5 %**, while
**`remotix` sits at `0,00 %`**. ⭐ *That is: the product is not slow — the product is waiting for the
compositor*, and no optimisation of the encoder moves that number.

> ### ⭐⭐ The proof that nails it lies in a single line
>
> `[M]` Same population — **eight sessions, eight desktops, eight children** — and **a single
> scene is switched off**. **The rate goes back from 1.6 to 33.4 fps.** Put it back, and the cliff reproduces.
> ⭐ **Reversible and repeatable.**
>
> ⇒ ⛔⛔ **The cliff does not fall on the NUMBER of sessions: it falls on how much is being COMPOSED** — `[M]`
> between **873 and 953 Mpixel/s**, which is **the same ceiling found by another route**.
>
> ⚠ **And the column that gave it away was watched by nobody**: when the compositors take 100 %
> of the render engine, `video-enhance` **collapses from 48.7 % to 0.4 %** ⇒ ⛔ **the encoder has
> nothing left to do. It does not slow down: it stops.**

#### ⭐ What changes in the product, concretely

⭐⭐ **The budget stays computable BEFORE accepting** — and it is the reason why the decision of §4.6
holds even though its physics was wrong: ⭐ **the currency is the COMPOSED pixel**, and the cost of a
session is known from its canvas before the session exists.

⛔ **But the pixel alone is not enough**, and the phase learned this by measuring: one also looks at **the
delay of those already inside** — `[M]` threshold **22.9 ms**, derived from healthy **≤ 13.1** and broken
**≥ 39.9**, ⭐ **with no overlap at all between the two populations**.

```
regge(dentro, nuovo)  ⟺  domanda(dentro) + costo(nuovo)  ≤  C × tolleranza
                          E  il ritardo di chi è dentro sta sotto la soglia
```

#### ⚠ And the numbers of §4.6 that were wrong — all three **too low**

| 10 sessions at… | §4.6 said | ⭐ `[M]` |
|---|---|---|
| 480p · 25 | «about fifty» | the ceiling is at **~180** — and the scale stopped at the **bench's cap**, not at the hardware's |
| 1080p · 30 | «right at the limit» | the number (620 Mpixel/s) was **right**, ⛔ but it is **33.2 %**: **24** fit |
| 4K · 60 | «**one single** session» | ⛔ the 5 Gpixel/s **do not exist**: the ceiling is 1.86. **TWO** fit |

⛔ **But they are numbers of the engine that is NOT the bottleneck**, and they must be read only for what they are: the
capacity of the encoder. ⭐ **The number that governs the product is that of the composition.**

⇒ ⭐ **And for the user the real number is yet another**: on the saturated scene **six** fit; on the
**real desktop** — windows, dragging, tearing — `[M]` **at least eleven, and the ceiling was not
found: the users ran out, not the machine**. The judgement is in **§4.6-septies**.

### 4.6-decies ✅ ⭐⭐⭐⭐ **The yardstick below the specifications: «artefacts yes, smoothness and sync no»**

*Said by the user on **25 Aug 2026**, in front of the real product — a **4K** video inside the
remote desktop, with his tablet's bandwidth throttled to **10 Mbit/s**, that is **below the declared
floor** of 30:*

> *«Il video mostra degli artefatti, ma è normale: siamo sotto le specifiche. Però **audio e video
> fluidi e in sync**.»*

⭐⭐ **It is a decision, not a compliment: it says what can be spent when there is not enough.**

| ⭐ **can be lost** | ⛔ **cannot be lost** |
|---|---|
| **sharpness** — visible compression artefacts | ⛔ **SMOOTHNESS**: jerky motion is noticed at once, and it tires |
| detail in fast scenes | ⛔ **SYNC** between audio and video: out of step, they become unbearable within a few seconds |

⇒ ⭐ **Below the floor the product spends the little it has where the user notices least**, and
does it **in this order**. ⛔ *It is not indulgence: it is the yardstick.* The product never promised 4K
at 10 Mbit/s — it promised **not to lie and not to crumble** (`SPECIFICHE.md` §2, *«degrade, don't
fail»*), and below the specifications that promise is honoured **like this**.

> ### ⭐⭐ And he designed the test himself — with the right correction, twice
>
> 1. To the proposal of going down to **30 Mbit/s** he was put in front of the number — `[M]` that
>    video travelled at **6.0 Mbit/s**, that is thirty is **five times** what is needed — and ⭐ **he
>    went down to 10**;
> 2. ⭐⭐ and he throttled **the tablet**, not the server: that is **the real path**, from the client side
>    — which is the scene a real user produces, and not the one convenient to fabricate.
>
> `[M]` **And the product answered by halving the bandwidth without losing a frame**: 38.5 → **37.4
> fps**, 6.0 → **3.20 Mbit/s**, ⭐ with the **wire queue empty** and the composition engine
> **steady at the same 41-46 %** — that is, the scene moved as before.
> ⇒ **It did not slow down: it compressed more.**

⚠ **And this judgement closes a `[?]` of phase 9**: the **AV** half of the sync, left open
because *«vuole quel browser»* — ⛔ and that browser did not start for a reason that was not its own
(§4.6-undecies).

### 4.6-undecies ✅ ⛔⛔ **The defect of a single tenant that blocks nine — and the cause is NOT a fault**

*Found on **25 Aug 2026**, after the user had said three times «Firefox non funziona».*

> #### ⭐⭐⭐ USER'S CORRECTION — *25 Aug 2026, evening*
>
> ⚠ *The title of this section said `**Il difetto di un inquilino solo che ne blocca nove:
> `~/.cache -> /tmp`**`, and the text below called that link **the defect**. ⛔ It is
> wrong, and the user corrected it:*
>
> > *«`.cache` che punta a `/tmp` è una mia scelta voluta»* — *and it is a decision on how **the
> > operating system of his machine** must work, which **has nothing to do with REMOTIX**.*
>
> ⇒ ⛔ **There is nothing to repair in the system.** That link is not a fault inherited from
> a base image: it is a **chosen** configuration, and on a single-user machine it does
> no harm at all.
>
> ⭐⭐ **And what stays true is OURS, not his**: it is **the product** that creates ten new users
> with `useradd -m`, and it is the product that makes them all born writing **in the same place**.
> ⇒ ⛔ *A harmless choice on one user becomes a block on ten **because we put them there**.*
>
> ⭐ **The cure already written is right as it is, and it must be said why**: `src/provisiona.sh` **does not
> touch `/etc/skel`, does not touch the user's home, does not touch `/tmp/mozilla`** — it gives its own
> `.cache` **only to the users we create**. ⇒ The system stays as the user wants it, and
> our tenants stop treading on each other's toes.
>
> ⛔ **And the target of phase 11 changes accordingly** (§4.6-duodecies): the safety net does **not**
> check that the folders are in the canonical place — it is none of its business, and the user decided
> otherwise **on purpose**. It checks that **the product works on the machine as it is
> configured**: *does the second user open the browser, yes or no?*

`/etc/skel/.cache` is a **link to `/tmp`**, and `src/provisiona.sh` creates the users with
`useradd -m`, which **copies the skeleton**. Firefox keeps the *local* profile under
`$HOME/.cache/mozilla` = **`/tmp/mozilla`** ⇒ ⛔ **the FIRST user who opens the browser takes it in
mode `0700`, and for all the others the profile is not born.**

⭐⭐ **And the decision that follows from it, which holds beyond this case**: ⛔ **a multi-tenant machine does not
inherit only the defects of a single-user one: it WAKES dormant ones.** ⇒ What is *«rare»* with one
tenant can be ***certain*** with ten, and must be looked for **before**, not waited for.

⚠ **The cure lies in `src/provisiona.sh`** — that is **in the machine, not in the product**
(`SPECIFICHE.md` §5.9, part A) — and ⛔ **the predicate that verifies it does not look at the link:
IT TRIES TO WRITE**, because *«written is not in force»* (**E1**).

⛔ **And the cost, declared**: that defect kept the user **two phases** in front of a browser that
did not start, with the explanation *«non è nostro»* — ⇒ ⭐ **the explanation that does not ask to keep
searching.** The lesson of method is `LEZIONI.md` **§1.38**.

### 4.6-duodecies ✅ ⭐⭐⭐⭐⭐ **Before the new desktops: a phase to NOT introduce regressions**

*Decided by the user on **25 Aug 2026**, right after closing phase 10:*

> *«No, prima è necessario mettere in sicurezza tutto quello che abbiamo sviluppato fino a oggi.
> Prima di passare agli altri DE è necessaria una sessione dedicata (magari una fase vera e propria)
> per studiare una modalità che impedisca di introdurre regressioni man mano che verrà implementato
> il supporto ai nuovi DE.»*

⭐ **Phase 11 is no longer KDE: it is the safety net.** KDE, XFCE and LXQt shift by one.

#### ⛔ Why now, and not later — and the argument is not generic prudence

`[M]` **The day of 25 Aug proved it three times**, and every time with the same way of
going wrong:

| the defect | how long it stayed hidden | ⛔ why |
|---|---|---|
| **the session that is born blind** (§7.4) | days | ⛔ **nobody ever opened a NEW session and looked at it**: all the tests reused sessions already open, which had the monitor |
| **the browser that does not start for the second user** (⚠ *not* the `~/.cache` link, which is a **choice** of the user — §4.6-undecies) | **two phases** | ⛔ and the test that *«closed the matter»* ran from a user who **had the same configuration** |
| **five benches that counted zero frames** | one round | ⛔ a cure to the log had broken their expressions, and `resa()` returned **0 instead of None** |

⇒ ⭐⭐ **None of the three was subtle.** All three were invisible for the **same** reason: one
always looked at the same piece of the scene, and ⛔ **one looked at the process instead of the pixel.**

#### ⛔⛔ And the reason why it must be done BEFORE the desktops, which is the same as §4.6-sexies

> *«if multi-tenancy touches the session or the budget, the change must be reverified on **four
> desktops instead of one**»*

⇒ ⭐ **It holds identically for the way of going wrong**: a defect that today is found once, with four
desktops will be found **four times** — and in the worst case on three of them **it will not be found at all**,
because nobody thinks of retesting the first. ⛔ *The net is stretched before walking the wire, not
after.*

#### ⭐ The yardstick of the phase, and it is not «how many tests run»

⛔ **A phase like this can degenerate into ceremony**, and the project knows it (`LEZIONI.md`, a review is
justified by **what survives**). ⇒ ⭐⭐ **The yardstick is only one: what the safety net CATCHES.**

⭐⭐ **And the phase's acceptance test is already written today**: the net must be aimed at **this
morning's code**, and ⛔ **it must turn red on §7.4** — the blind session — **without anyone having
told it where to look.** If it does not catch it, it is not a net: it is a ritual.

⚠ **And the second acceptance test**: it must notice that **for the second user the browser does not open**.
⛔ **Not** «it must find the `~/.cache` link» — that is a **choice of the user**, not a
fault (§4.6-undecies, correction of 25 Aug 2026): the net does not judge how the machine is
configured. ⇒ ⭐ **It looks at the DELIVERY on the machine as it is**, not at the source and not at the configuration.

### 4.6-terdecies ✅ ⭐⭐ **A test box can have up to TEN tenants** — the constraint was on capacity, not on correctness

*Clarified by the user on **26 Aug 2026**, after the night of step 0:*

> *«Per quanto mi riguarda un container può anche avere 10 utenti, è un dato già misurato con
> GNOME.»*

⛔ **It corrects too narrow a reading of §4.6-duodecies**, which this session had summarised as
*«one user per container»*. ⇒ That constraint came from something true — **capacity has already been
measured**, on the worst case, and is not redone at every change — ⛔ **but it had been applied to a
different question.**

| type of test | the question | is it redone? |
|---|---|---|
| **capacity** | *how many tenants fit together before the machine gives in?* | ⛔ **no**: `[M]` six on the saturated scene, at least eleven on the real desktop |
| ⭐ **correctness with several tenants** | *does the second manage to do what he must?* | ✅ **yes, and it is the safety net** |

⭐⭐ **And the finding came from the two external reviewers**, who got there by two different routes: *«C8
è la prova più importante ed è la più fragile»*. ⇒ With this clarification the test of the **second
user who opens the browser** — that is the **acceptance test B** of phase 11 — ⭐ **can live inside a
box**, instead of being the only thing that lives on the real machine and that is therefore run rarely.

⚠ **And what this does NOT authorise**: redoing the campaign of ten at every change. Ten tenants
*can* fit in a box; ⛔ the anti-regression net uses **two**, because the question is *«has something
broken?»* and not *«how many fit?»*.

### 4.6-quaterdecies ✅ ⭐⭐⭐ **The four boxes exist — and they are four boxes with THREE compositors**

*`[M]` **26 Aug 2026**, night. Built and verified the boxes of GNOME, KDE, XFCE and LXQt: ⭐
step 0 gives **18 greens out of 18 in all four**, with the very same list of tests and ⛔ **not one
line changed**. Each box brings to the same path an **adapter** of forty lines.*

⚠ **And an uncomfortable thing, said at once**: XFCE and LXQt do not bring a compositor of their own on Wayland —
they bring a **session** and lean on one of the `wlroots` family. For both the choice is
**labwc**, ⭐ which this document had already measured under the label *«labwc (XFCE, LXQt)»*.

⇒ ⛔ **The fourth box does not put a fourth compositor to the test**: it puts to the test a fourth
session, a fourth recipe and different dependencies. **Whoever reads the results should count three compositors and
four boxes.**

#### ⭐ And the third desktop asked for nothing — *which is a result, not a non-event*

The second had asked for **two** things the first did not ask for (the `render` group, the
`SYS_NICE` permission). The third and the fourth: **zero**. ⚠ It must be read for what it is: **one** desktop that
asked for nothing after **one** that had asked for two things — that is, the reason why the question is asked of
each one instead of generalising from the first.

#### ⛔⛔ And for the THIRD time the environment was generous: `libpci3`

`[M]` Firefox without `libpci3` says `glxtest: libpci missing` and **produces no image at all**. ⛔ In the
XFCE box the defect **could not be seen**: `labwc` drags it in; `kwin-wayland` does not.
⇒ ⭐ **The very same way of going wrong as `libei1`**: a library that was there **by chance**, and a
red that looked like the product's. ⇒ Now it is declared in the recipe, like the others.

### 4.6-quindecies ✅ ⭐⭐⭐ **C8 had to be split in two — and the half that holds caught the defect**

*`[M]` **26 Aug 2026**. Acceptance test B of phase 11 passed:*

> **with the provisioning cure**: `c8u1` ⭐ the page covers **98.7 %** · `c8u2` ⭐ **98.7 %**
> **without the cure** (the code of 25 Aug): `c8u1` ⭐ **98.7 %** · ⛔ `c8u2` **NO** — *profilo: è di
> «c8u1» · sa scrivere in `~/.cache/mozilla`: **NO***

⭐⭐ **And the asymmetry is the right one**: the first opens the browser, the second does not. ⛔ A red on both
would not have been the defect of §4.6-undecies — it would have been the bench.

| | what it looks at | today |
|---|---|---|
| ⭐ **C8a** | Firefox photographs itself, as a user, on the machine as it is configured. The judgement stays **in the pixel** (`#FF00FF`, declared tolerance) | ✅ **is measured** |
| **C8b** | the same page, looked at **through the product** | ⚠ **is not measured today** |

⛔⛔ **Why C8b is not measured**: `[M]` **ten new GNOME sessions out of ten are born without a monitor** —
it is the **open** defect of phase 10 §7.4, which lies **upstream** of C8. ⇒ ⭐ A black desktop does not
bear witness about the browser.

⭐ **And the split has an unforeseen gain**: C8a **does not go through the product**, and so it runs in
**any** box — the acceptance test above ran inside the **PLASMA** one.

### 4.6-sexdecies ⛔⛔⛔ **And this is the fact the user must weigh before phase 12**

`[M]` 26 Aug 2026: **zero new sessions out of ten** are born with a monitor. ⇒ ⛔ **C2, C3, C4, C6 and
half B of C8 cannot measure anything**: there is no pixel to look at.

| ⭐ what the safety net **today** can do | ⛔ what it **cannot** do |
|---|---|
| say that a session **is born blind** (C1) · that the **second tenant** does not open the browser (C8a) · that the **environment** holds on four desktops | say *«and now it can be SEEN»* |

⚠ **And the difference matters**: it is not a hole in the net — a hole is plugged by writing another mesh —
⛔ **it is a defect of the product**, and it is plugged by curing the product. ⇒ The reason why phase 11 comes
**before** the new desktops is *«do not break what worked»*: with blind sessions one cannot
**see** whether GNOME keeps working.

⇒ ❓ **The choice is the user's**, and it is written in `fasi/11-la-rete-di-sicurezza.md` §11.

### 4.6-septendecies ✅ ⭐⭐⭐ **The four boxes do not disturb each other — measured, no longer asserted**

*`[M]` **26 Aug 2026**.* The same test run **one box at a time** and then **all
four together** gives **the very same outcome**, in both modes (with the cure `2 sì · 0 no`;
with the fault injected `1 sì · 1 no`).

⇒ ⭐ **The line that `11-accendi.sh` carried open is closed**: `--network=host` makes the
four boxes share the machine's ports, and the separation **by port** is a **real** separation —
each one recognises as its own only its own.

⚠ **Time is information, not verdict**: `[M]` 6.6 s alone → 7.0 s in parallel (×1.06), and the
total drops from 26.2 s to 7.0 s. ⛔ And one time was **thrown away by the bench itself**: with the fault
injected the four times were equal to a tenth of a second, because almost everything was **fixed waiting
of ours** and not work. ⇒ Calling it «contention» would have been measuring our own cap.

⛔ **And what is NOT measured**: the real contention on the **graphics card**. It would need four sessions
alive, and today sessions are born blind. ⇒ The layer below is measured — the four boxes
**open the encoder at the same instant**, 3 H.264 profiles each.

### 4.6-octodecies ✅ ⭐⭐ **The hook exists — and the 3-minute cap is full**

*`[M]` **26 Aug 2026**.* The net now starts by itself: it looks at **which files have changed** and from
those it derives what runs. ⛔ It does not ask whoever is working — *a hook that asks is a hook that
does not run on the day one is in a hurry, and the days one is in a hurry are the ones when things
break.*

> ### ⛔⛔ AND THE CAP IS FULL, WITH SIX SECONDS OF MARGIN
>
> `[M]` The fast family — **C11 + two rounds of C1** — lasted **174 seconds** against a cap of
> **180**. ⇒ ⭐ **There is no room to add anything.** Any extra mesh must be **swapped** with
> something that goes out, not added.

⇒ The **cut** tests, and the cost of each, are in `fasi/11-la-rete-di-sicurezza.md` §7-bis.16.
⛔ The dearest: **C8 is not looked at on every change** — the most important mesh of the list sits
only in the full round.

⚠ **And it hooks in BEFORE PUSHING**, not at every save: three minutes at every commit are
exactly the thing that gets a hook switched off.

### 4.6-undevicesimo ✅ ⭐⭐⭐ **The safety net can say of itself whether it is still capable of giving red**

*`[M]` **26 Aug 2026**, full round, 28 minutes.*

⛔ The fault this mesh (C13) looks for is the most insidious of the list: *a net that is no longer
capable of giving red **looks exactly like a net that finds nothing**.*

⇒ ⭐ And the moment that matters really happened. **During** the round C13 was **red**, and it told the
truth: *«negli ultimi giri nessun guasto è mai stato innestato»*. **After** the round — which had the injected
fault inside it — it is **green**: *«un guasto è stato innestato ed è stato visto»*.

⚠ **And it says so with its limit attached**: *on the faults it KNOWS*. ⛔ Every new desktop will have to
come in with **a fault of its own**, or this mesh will certify a capability that does not cover the new
terrain.

### 4.6-novemdecies ⛔⛔ **The two halves of the hook live on two different machines**

`[M]` 26 Aug 2026, first real round, and nobody had foreseen it:

| | where it lives |
|---|---|
| **deciding** what to run | needs the git repository ⇒ **the laptop** |
| **running** | needs the boxes and the graphics card ⇒ **the test machine**, ⛔ where the repository **is not** |

⇒ The first draft required git always, and came out «terreno cattivo» **on the only machine able
to run the meshes**. ⭐ Now: if the family is asked for by name there is nothing to decide, and the
repository is not needed.

⚠ **And from it follows a thing the user must decide**: the hook's log — the one on which
C13's memory lives — **is born where the hook runs**. ⇒ Today there is one on the test machine and
none on the laptop. Putting it in git would give it a single memory for all machines; keeping it
out would avoid having that file modified at every round. ⛔ **Not decided.**

### 4.6-vicies ✅ ⭐⭐⭐ **Four new meshes, and the net now also looks at what is not a pixel**

`[M]` 26 Aug 2026, four agents in parallel, one box each.

| mesh | what it looks at | certification | cost |
|---|---|---|---|
| **C5** the sound is not silence | the **RMS** of the samples reaching the client, declared threshold **328/32767** (−40 dBFS), calibrated by crossing the boundary in both directions | **12 out of 12** | `[M]` 38 s |
| **C7** it closes and nothing remains | fingerprint before / session / closing / fingerprint after — processes, sockets, units, card | **13 out of 13** | `[M]` 26 s |
| **C9** the log says whom it is talking about | **two** tenants alive together, and every mandatory line must say which | **16 out of 16** | `[M]` 50 s |
| **C10** the twin copies | the three twin files, byte for byte — ⭐ and the list **read from `src/Makefile`**, not copied out again | **15 out of 15** | `[M]` 0.04 s |

⭐⭐ **And the choice that holds them together**: none of the four judges a **pixel**. ⇒ They are the
four that the defect of the blind sessions **does not block**, and that is why they were made
now and not the others.

⚠ **None enters the fast family**, and the cut is declared instead of suffered: `[M]` the cap
is at **153 s out of 180**, and §5.1 says that an extra mesh is **swapped**, not added. ⇒ C5, C7 and C9
sit in `tutto` and in `desktop-nuovo`, with their injected fault next to them. ⛔ **Only exception:
C10**, which costs less than the stopwatch's resolution.

### 4.6-unetvicies ✅ ⭐⭐ **C10 sits in TWO families, and C10's injected fault keeps C13 alive on the laptop**

Two things that were seen only while wiring, and neither of them was foreseen:

1. ⛔ **The twin lives half in `src/` and half in `banchi/rcp/`.** A change to the bench's copy
   triggers the `rete` family — and it is **exactly** the change that breaks the twin. ⇒ If
   C10 sat only in the fast family, the case that bites hardest would not make it run.
2. ⭐⭐ **The half of the hook that lives on the laptop injected no fault** (§4.6-novemdecies:
   the two halves sit on two machines). ⇒ C13, there, could **never** have turned green:
   it would have said forever *«nessun guasto è mai stato iniettato»*, which from outside looks the same
   as a broken net. ⇒ C10 now has a `--guasto-innestato` that copies the **real** files into
   a temporary folder, changes **one byte** of them and demands red. It costs `[M]` **0.1 s**.

`[M]` And the result is measured: on the laptop the `rete` family gives **C10 green · C12 green · C13
green** in **1 second**, without switching anything on.

### 4.6-duoetvicies ⛔⛔⛔ **The first red the safety net pulls out of the PRODUCT — and it is two lines**

`[M]` 26 Aug 2026. C9, on all the boxes tried: **4 mandatory lines out of 5 490 cannot be
attributed to any tenant**. They are `src/tastiera.c` and `:486`, which write in the **parent** without
`registro_dice_di()`. ⛔ Two lines identical word for word, one per tenant: **with two sessions
alive one cannot tell which is whose.**

⭐ **And this is the net's job, done for the first time on a defect nobody was looking for**:
it is not an injected fault, it is not a bench getting it wrong, it is the product. The cure is two lines. ⛔ **Not
applied**: touching `src/` forces rebuilding and putting the binary back into four boxes, and
the order of the phases is a decision of the user (§4.6-sexdecies).

⚠ **And a finding alongside, which is NOT a red**: `[M]` **1 402 lines (25.5 %)** name the tenant
only in the prose and not in the parenthesis. They are attributable, so C9 counts and prints them without
judging them. ⇒ If the phase wanted them red, C9 would turn red on a quarter of the log: it is a
decision, not a defect.

### 4.6-teretvicies ⛔⛔⛔ **THE STAGE DIES WITH THE CLIENT — and contradicts I4 to its face**

`[M]` 27 Aug 2026, tried in full on an isolated bench with real Mutter:

| | |
|---|---|
| `--headless` alone | ⛔ **zero `wl_output`**, and it is intended: in headless Mutter does not open the cards |
| the virtual monitor | ⭐ is born **only when a PipeWire consumer attaches** to the stream — `[M]` 65–93 ms after attaching, **never before** |
| detaching the **consumer** | ⭐ the monitor **survives** (`[M]` 15 s, it is still there) |
| closing the **D-Bus connection** of whoever called `RecordVirtual` | ⛔ **the monitor DIES** |

⛔⛔ And in the product that connection belongs to the **child**, and **the child dies with the client**.

> ⇒ ⭐⭐⭐ **Today the desktop has a screen only while someone is looking at it.**
> ⛔ And it is the direct contradiction of **I4** — *«the stage belongs to the session and survives
> disconnection»* — which is a declared decision of the project, not a detail.

⭐ **The cure is tried, not hypothesised**: keeping connection and stream open for the life of the
session, with a consumer attached **only once**, `[M]` with the client detached an application
opens its window, the pixels land there, and the client that arrives later sees it (**12 055 distinct
colours**).

⛔ **But it is not one line**: the stream must be taken away from the child (`src/figlio.c:5334-5513`) and given to something
that lives as long as the session. ⇒ ❓ **It is a decision of the director**, and the mesh that watches over it is
**C6**.

⚠ And two routes are **refuted**, not to be redone: `--virtual-monitor` at startup (⇒ two monitors, and no
frame comes out of the wire — the defect of 14 Aug reproduced) and the geometry (1920×1080 and
1268×713 give the same outcome).

### 4.6-quaterque-vicies ✅ ⛔ **The ~97 seconds belonged to the BOX, not to the product**

⇒ `LEZIONI.md` §1.54. In one line: the recipe moved the `polkitd` group from 991 to 1991 to give
991 to the graphics card, ⛔ `groupmod -g` does not carry the files along, `polkitd` could no longer
read its rules and died, and `gnome-shell` took **four 25 000 ms timeouts in a row**.

⭐ Cured in the recipe, **without any new permission** beyond `SYS_ADMIN`: whoever moves the number makes
the files follow, and the groups' unit takes `Before=polkit.service`. `[M]` From **~97 seconds** to
**1.105 · 0.998 · 0.957 s**.

### 4.6-quinquies-vicies ⛔⛔ **The product drives ONE desktop, not four**

`[M]` C1 run ten times per box on KDE, XFCE and LXQt: **0 healthy · 0 blind · 30 «non ho
potuto guardare»**. The log says it: *«Mutter non espone RemoteDesktop»* ⇒ ⛔ `src/sessione.c` · `scrivi_dropin()`
and all of `src/mutter.c` can start **only GNOME**, and in the other three boxes `gnome-shell` is not there.

⭐ **What the other three prove is real but smaller**: the environment (step 0), the sound (C5), the
leftovers (C7), the log (C9), the alignment (C11). ⛔ They do **not** prove that the product holds on those
desktops. ⇒ §3.7 of phase 11 must be read with this correction, and ❓ **it touches the meaning of phase 12**.

⚠ And one thing phase 12 will have to face, measured in passing: ⛔ **KWin cannot be born blind**
— with `--output-count 0` it makes an output all the same. ⇒ The design *«zero monitors of its own»* **does not
carry over the same** to KDE.

### 4.6-sexies-vicies ✅ ⭐⭐ **C15 — «the remote half really runs»**, and the hole is measured

The hook has two halves on two machines (§4.6-novemdecies). ⛔ Until now, **if the test machine had
been switched off forever, C12 and C13 would have stayed green**: the hook ran on the laptop in one
second and nobody noticed that the real meshes no longer ran.

⭐ `[M]` The hole is **demonstrated**, not described: taking the real log and removing the only line run
on the boxes, **C12 green · C13 green · C15 RED** on the same file. Certification **21 out of 21**.

⭐ And the sign is not the machine's name: it is **a mesh that needs a box and reaches a
VERDICT (0/1) instead of a 3**.

⚠ **The `rete` family declared something false** — *«nessuna accende una sessione»* — while C14 costs
`[M]` ~800 s and takes all four boxes. ⇒ Split: **`rete`** (C10, C11, C12, C13, C15 —
`[M]` ~11 s, and it really switches nothing on) and **`rete-intera`** (+ C14), called by `tutto` and
`desktop-nuovo`.

### 4.6-septies-vicies ✅ ⛔ **`VA VELOCE` is not made: §6 is right, §3.4 is wrong**

§3.4 declared two families; §6 declares that the net **is not** a performance net; and in the hook
`VA VELOCE` **never existed**. ⇒ The family **must not be created**: the fourteen meshes are all
yes/no, and a family of numbers would duplicate the ~40 benches of phases 9 and 10 **outside the conditions
in which those numbers hold**. ⇒ §3.4 is rewritten, and the hole — ⛔ *«no bench compares yesterday with
today»* — is **declared in §6**, where the things the net does not catch live.

### 4.6-duodetricies ✅ **One desktop per machine — the choice among several desktops is postponed**

*18 Sep 2026, opening phase 12. To the question «if a machine has GNOME and KDE, who
chooses which one to start?» the user answered:* *«Al momento la funzionalità di scelta di desktop
multipli la lasciamo per una futura implementazione».*

⇒ ✅ The product does **not** offer a choice of desktop: neither to the user, nor as a setting.
The machine has **its** desktop, and the server starts that one.
⇒ 🔸 *Derived, correctable without discussion*: the server recognises the desktop **from what is
installed**. If both are there, **GNOME** stays — that is, what the product already does today, and
no machine served changes behaviour. ⚠ The «both» case is therefore **ambiguous by
construction** and is declared in the log at startup, instead of choosing in silence.
⇒ The postponed feature is in `MASTERPLAN.md` **M5**.
⭐ **Widened on 20 Sep 2026** — §0.6: machines with several desktops installed are
**out of scope**, not merely without a choice.

### 4.7 ✅ ⛔⛔ Nobody switches off the server — and «nobody» includes whoever is in front of the machine

> ### ⭐ 21 SEP 2026 — AND IT HOLDS FOR XFCE TOO, said by the user
>
> *«ricorda che anche in XFCE vanno disabilitate le voci di standby, lockscreen, reset e
> spegnimento»* ⇒ the same four as GNOME and KDE: **suspend, screen lock, reboot,
> power off**. ⛔ **«Esci» stays** — §4.1-ter, it is the only gesture that ends the session.
> ⚠ On XFCE **there is no KIOSK** as on KDE (`STUDI.md` §xfce §10.4): the items are removed
> on every route by which they are reached (menu, panel button, logout dialog, power
> manager), and ⛔ **every key written is read back** (§10.6: `xfconf-query` exits with zero
> even when the daemon has refused). ⭐ **«Cambia utente» goes too** — decided by the user on 21 Sep 2026, evening: *«togli anche «Cambia utente» per rendere omogeneo il comportamento tra tutti i DE: l'unica voce che deve rimanere è logout»*. KDE with the KIOSK (phase 12), GNOME with `org.gnome.desktop.lockdown disable-user-switching`, XFCE from the panel and with `ShowSwitchUser=false`.

> ### ⛔⛔ AND ON 25 AUG 2026 THIS DECISION FOUND A HOLE — **whoever updates**
>
> ⭐⭐ **REFUTED BY THE MEASUREMENT OF 29 SEP 2026** (`fasi/17-l-installatore.md` §5.2, T2): ten
> tests with real Firefox on the four desktops — stopping the unit (`KillMode=mixed`), killing only the
> parent, killing only the child — **no desktop dies**: the parent, the PAM helper and the child die; the
> stage (started with `setsid --fork`, outside the unit), the session and the programs survive, and on
> reattach the same compositor comes back with its windows. The fact of 25 Aug does not reproduce today.
>
> `[M]` Stopping the server's unit to **update it**, at 18:14:29, **all the users' sessions
> died** — windows included; fifteen seconds later a **new and empty** one was born.
> The graphical session lives in the **server's process tree** (`KillMode=mixed`).
>
> ⇒ ⭐⭐ **It is exactly the damage this decision forbids** — *«switching it off is the only gesture that takes
> away all the sessions together»* — ⛔ **obtained, however, by whoever administers, and without any line
> declaring it.** The three belts below defend against switching off the **machine**; ⛔ **none
> defends against restarting the SERVICE.**
>
> ⚠ **The decision is not widened here**: the boundary was drawn in `SPECIFICHE.md` §5.2 (*«the
> session survives the client, NOT the server»*), the finding is in
> `fasi/10-multi-tenant-e-il-budget.md` **§7.5**, and ⭐ **the place where it is cured is phase 15 (it was 14 until 21 Sep 2026), the
> service**: updating without stopping anyone.
>
> ⭐ **And meanwhile the practical rule, which follows from this decision without changing it**: before
> restarting the server **one looks at who is there**.

*Decided by the user on **15 Aug 2026**, at the opening of phase 5: «no, nessuno può spegnere,
riavviare, mettere in standby o sospensione il server, altrimenti si rischia di "buttare fuori"
anche altri eventuali utenti collegati alla macchina».*

⭐ **The reason is the same that holds up the whole of phase 5: the machine belongs to several people.** Switching it off is
the only gesture that takes away **all** the sessions together — and whoever performs it, from a desktop's menu,
**has no way of seeing who is connected**. `SPECIFICHE.md` §11.3 already promised it in one line
(*«power off, reboot, suspend: taken away from the remote session»*); this decision widens it
— ⛔ **not «from the remote session»: from all of them** — and gives it for the first time a way of being
kept.

**Three belts, and they are three because the routes are three:**

| | |
|---|---|
| **1 · the polkit rule**, `no` on `org.freedesktop.login1.power-off`, `reboot`, `suspend`, `hibernate` and the `*-multiple-sessions` / `*-ignore-inhibit` variants | ⭐ **flat, with no discriminant**: no `subject.local`, because the decision is «nobody». ⭐ And it covers **two routes with a single line**, because it looks at the **action** and not at the interface: the desktop's menu **and** `systemctl poweroff` typed in a terminal inside the session. On GNOME `CanShutdown` becomes false and the items **disappear** (`gsm-manager.c`, `systemActions.js:340-359`). ⛔ **`no`, never `auth_admin`**: `challenge` **shows** the item (`STUDI.md` §gnome §5.1, `STUDI.md` §kde §1579) |
| **2 · `logind.conf`**: `HandlePowerKey`, `HandleSuspendKey`, `HandleHibernateKey`, `HandleLidSwitch` = `ignore` | ⛔ the **physical button** and the lid **do not go through polkit**: logind acts on its own, and the first belt does not see them |
| **3 · automatic suspend**: `Inhibit(…, SUSPEND\|IDLE)` **and** `sleep-inactive-ac-type=nothing` | ⚠ the first belt **stops** suspend on inactivity, but the user would still see the notification *«Automatic Suspend — Suspending soon»* `[M]` and then an error. Two belts for **two different symptoms**: one prevents the fact, the other removes the lie from the screen |

> ### ⭐⭐ AND THAT SAME EVENING THE THREE BELTS WERE INSTALLED AND MEASURED — `[M]` 15 Aug 2026
>
> *On the test machine, after the reboot. ⛔ And the measurement corrected **two** things this entry
> said by deduction.*
>
> | | |
> |---|---|
> | ⛔⛔ **v1's rule covered three actions out of twelve, and failed EXACTLY in the case it was written for** | `[M]` `org.freedesktop.login1.policy` also lists `*-multiple-sessions` and `*-ignore-inhibit`. ⛔ When the machine has sessions of **several users**, logind does not ask for `power-off`: it asks for **`power-off-multiple-sessions`**, which v1's rule did not name. ⇒ With one user it worked, with two it did not — and nobody would have seen it. ⚠ And `org.freedesktop.login1.halt` **does not exist** on this systemd: that line was dead |
> | ⭐ **root needs no exception at all** — *and the line below, which promised one, was wrong* | `[M]` with the rule in force: from `nicfio` `CanPowerOff="no"`, **from root `"yes"`**. ⛔ Before querying polkit, logind looks at the **capabilities** of whoever asks: whoever has `CAP_SYS_BOOT` is authorised and polkit **is not consulted at all**. ⇒ `sudo systemctl poweroff` works without the rule providing for anything |
> | ⛔⛔ **and from this follows the real trap: the check CANNOT be done from the server** | the server runs **as root**, so it would always hear `"yes"` — a check that always says yes. ⇒ **The CHILD does it**, after it has become the user. ⚠ A check done from the wrong place is worse than a missing check: the log would say «verified» |
> | ⭐ **the physical button was live** | `[M]` in `/etc/systemd/logind.conf` all the `Handle*` lines were **commented out**, that is the default — and `HandlePowerKey=poweroff`. ⇒ Until this evening the button switched off the server with anyone connected to it. Now `ignore`, `[M]` read back from `systemd-analyze cat-config` |
> | ⭐ **suspend has a belt stronger than polkit** | `sleep.conf.d` with `AllowSuspend=no` makes **systemd** refuse suspend, not polkit: `[M]` `CanSuspend="no"` **even from root**. ⇒ On suspend and hibernate the promise is kept even against the administrator |
>
> ⇒ **The two files are in the repository**, not only on the machine — I7: `src/remotix-niente-spegnimento.rules`
> and `src/remotix-tasti.conf`.

⛔ **And what remains possible must be declared now, not discovered later: root.** ⭐ `[M]` root switches off
because it has `CAP_SYS_BOOT`, and logind authorises it **before** reaching polkit; and in any case
`systemctl --force poweroff` talks directly to PID 1. ⭐ **And it is right that it stays**: the machine
must stay administrable, and switching off for maintenance is a gesture of the **administrator**,
not of a user. ⇒ The exact promise, to be written like this and no wider:

> **No user, from any session — remote or local — switches off, reboots or suspends the server.**
> Not «the server does not switch off».

> ### ⭐⭐ And the user specified it better, the same day
>
> > *«L'utente collegato a REMOTIX può solo fare espressamente il logout o, ovviamente, operare sul
> > PC che sta utilizzando.»*
>
> ⭐ **Put like this, the rule stops being a list of prohibitions and becomes a single rule**, and it is
> the form to keep:
>
> | inside the remote desktop | ⭐ **only one gesture that ends something: logout** (§4.1-ter). Switching off, rebooting, suspending, hibernating **do not belong to him** — not because they are dangerous, but because **they are not his**: others are using that machine too |
> |---|---|
> | on the PC he is connected from | ⭐ **he does what he wants, and it is his business**: he switches it off, reboots it, closes the lid. For us it is **the wire that drops**, that is the case already measured — and there is nothing to detect, to distinguish or to forbid |
>
> ⛔ **Hence the yardstick of the bench of §1.1 of phase 5**, which is stronger than «the items have disappeared»:
> ⇒ *in the remote desktop's system menu «Esci…» remains **and nothing else** of that family.*

> ⛔ *Here there was a line saying to write **root's exception inside the rule**, because
> otherwise «even `sudo systemctl poweroff` would fail». ⭐ The measurement of 15 Aug refuted it:
> the exception is not needed, because it is not polkit that decides for root. The rule stays **flat**, as
> the user wanted it.*

⭐ **And this rule finally gives a job to `0x0C SERVER_IN_CHIUSURA`**: if the only legitimate
switching off is the administrator's, then **that is the only route on which the clients must be
warned**, and the cure of finding B-7 (`main.c` · `main()`, `trasporto_congeda_tutte`) stops being a
repair and becomes **the normal path**.

⚠ **And the three belts are all configuration lines, that is what invariant I7 forbids**: they must be
**installed by us** and **verified after startup**, like the headless of §4.3-bis. ⭐ The check is: one
asks logind `CanPowerOff` / `CanReboot` / `CanSuspend` / `CanHibernate` and demands **`no`** —
if it answers `yes` or `challenge`, the protection is not there and failure is declared. ⛔ **And it is asked
from the CHILD, which is the user**: from the server, which is root, the answer is `yes` by construction, and the
log would say «verified» having looked at the wrong thing.

---

### 4.8 ✅ ⛔ No six hours: **sixty minutes without input and the session closes**

*Decided by the user on **16 Aug 2026**, with these words: «niente timeout delle 6 ore: se dopo 60
minuti non c'è traccia di input la sessione viene killata».*

`SPECIFICHE.md` §5.3 had written **6 hours without any attach**. ⇒ **Two things** change, and they must be
read separately:

| | before | now |
|---|---|---|
| the cap | 6 hours | **60 minutes** |
| ⛔ **the criterion** | «nobody has **attached**» | «nobody has **touched anything**» |

⭐ **The second change is the bigger one**, and it must be said: someone who attaches and just watches no
longer renews anything. The cap feeds on the same gestures as the 30-minute clock — the five
inputs of §7.3 — and not on the fact that a connection exists.

### ⭐ The decision came from a number, and the number was measured on purpose

*The user had asked: «misura la memoria. Potrei anche decidere di diminuire drasticamente questo
intervallo».*

`[M]` 16 Aug 2026, abandoned session, PSS (shared libraries counted only once):

| | |
|---|---|
| the whole session of `prova` | **477 MB** out of 31 851 total ⇒ **1.5 %** |
| of which `gnome-shell` | 182 MB |
| of which **our child** (stage, capture, encoder) | **116 MB** |
| CPU | ~0.017 % of one core |
| ⭐ **growth in 4 minutes** | **none**: 477 · 476 · 476 · 477 · 477 · 477 · 477 · 477 · 477 MB |

⇒ **It is not a leak, it is a fixed cost.** ⚠ And the choice, with that number in front of him, is the user's: one
pays for one hour instead of six.

### ⚠ And a complication was proposed and DISCARDED — by the user, with a common-sense measure

I had proposed resetting the cap on **reattach** too, fearing to kill a session while
someone was watching it. The answer:

> *«la tua ipotesi comporta il fatto che l'utente in 10 minuti non fa nemmeno un clic col mouse,
> alquanto improbabile»*

⭐ **And it is right**: for the damage to happen, someone would have to come back and then touch **nothing** for
the rest of the hour. ⇒ Input is counted and that is all — the simplest rule, and also the easiest to
explain to whoever is subject to it.

### What it means, in code

- the reason `0x03 SESSIONE_ABBANDONATA` of `RCP.md` §8.2 **has always existed and nobody had ever
  sent it**: now it is its own. ⚠ Usually nobody will receive it — if the cap expires it is because
  nobody was there any more — but whoever is there reads a sentence instead of looking at a frozen screen;
- **configurable** (`--abbandono-s`), `0` = off, and the value in force **is written in the log
  at startup** together with the other two: nobody verifies a one-hour cap by waiting an hour.

---

## 5. The geometry — the canvas and the view

### 5.0 ✅ The canvas is born at every attach, and stays still as long as the client stays

*8 Aug 2026, model dictated by the user.*

| Moment | Who decides the size | Who adapts |
|---|---|---|
| **attach** | the client: the session reads its resolution and uses that | nobody — it is 1:1 |
| **during the session** | nobody: the canvas does not move | the **client** rescales the image |
| **reattach** from another device | the new client, with its resolution | nobody — 1:1 again |

It closes the question that was open in §7.1: the canvas has **no** default value nor a
user preference. The client dictates it, at every attach.

**The virtue of the model is the mobile case**, and it comes out right by itself: the phone attaches and the
canvas is born in the phone's shape — real pixels, no bands, no scaling. None
of the alternatives discussed (generous fixed canvas, canvas with a scrolling view) did as
well without additional logic.

**Attach works on all four desktops**, KDE included: the size is written in the
compositor's start line (`--virtual --width W --height H`) **before** the session
starts, and the session starts at the first attach.

### 5.0-bis 🔸 Reattach at a different size on KDE ≤ 6.7.4: declared degradation

> ⚠ *The title said «KDE < 6.8», and §5.0-quater promised that version «in October».*
> ⛔ **Corrected on 14 Aug 2026**: `[R]` checked on invent.kde.org, **`Plasma/6.8` does not
> exist**, the last tag is **v6.7.4**, and the branches from `Plasma/6.3` to `Plasma/6.7` do not have
> hot resizing — it is **only on `master`**, without a release date. ⇒ A
> degradation with a written expiry ages worse than one without: here the expiry **is not
> there**, and it must be said.

It is the only point where the model cannot be served. With the session alive KWin 6.3.6 does not
change size `[M]`, and restarting it would mean killing the session — that is, destroying
exactly the detach that the model offers.

**Fallback: the old canvas is kept and the client rescales.** It does not cost one more line, because it is
the same code as the «during the session» point. On Debian stable, reattaching from a
device of a different shape, one sees the desktop of the previous shape rescaled, until the
session is closed. On GNOME, wlroots and KDE ≥ 6.8 one sees the new shape.

The fallback **is declared in the log** (`CODER.md` §4.2): a silent fallback produces two
behaviours under the same label.

### 5.0-ter 🔸 `[?]` Reduce the encoded size too when the window is small

If the user shrinks the window a lot, the server keeps encoding the whole canvas and the
client shrinks it: those pixels are paid for in bandwidth without being seen. One **could** make
the encoded size drop too below a certain threshold, with settling.

⚠ **It is not in the model, and it is left out on purpose**: first it must be measured whether the problem
really exists, and how much it weighs. An optimisation decided before the measurement is §7.2 of `LEZIONI.md` —
optimising in the wrong direction.

### 5.0-quater 🔸 ⛔ ~~With the browser, «the client's resolution» is two different measures~~ → **the canvas is the WINDOW**

> ## ⛔⛔ SUPERSEDED BY §5.0-sexies, and implemented on 15 Aug 2026
>
> *This item chose **the device's screen** as the canvas, and the window as the view. ⛔ It
> was overturned by §5.0-sexies — decided by the user on 14 Aug — which takes **the window**:
> canvas and view coincide, the scale is 1 and the coordinate conversion disappears.*
>
> ⚠ **And the two reasons of this item were not wrong: they were tied to a constraint that no longer
> exists.** The first said that a small window would give *«a small desktop for the whole
> session»* — true **as long as the canvas could not be changed**. Since `figli_ritela()` →
> `cattura_ridimensiona()` exists (`[M]` 6 ms hot, 15 Aug), the canvas is remade **at every
> attach and at every reattach**. ⛔ *During* the session no, and since 17 Aug 2026 not even behind a
> switch: §5.1-bis removed it. ⚠ But the item stays cured all the same — «small forever»
> meant *for the whole session*, and a session can be reattached.
>
> ⭐ **And the `[?]` about page zoom, which this item left open, closed by itself**: the
> size is no longer read from the screen — it is read from the window, and the zoom factor is already
> inside it. A client with zoom ≠ 100 % no longer declares a wrong canvas: it declares its own.
>
> ⇒ What remains valid below is the **distinction between canvas and view** and why they are two
> different quantities. What falls is **which of the two measures becomes the canvas**.


*9 Aug 2026, at the user's request after the move to the web client: «resta da chiarire il
comportamento della risoluzione avendo adesso come client un browser».*

§5.0 says *«the session reads the client's resolution and uses that»*, and with a program of ours in
full screen there was nothing else to say. ⛔ **A browser is a window inside a screen**, and the two
measures differ — on a phone by a factor of three, because of logical pixels.

| | |
|---|---|
| **the canvas** | 🔸 **the device's screen, in physical pixels** |
| **the view** | the window, in physical pixels |

**The two reasons, and nobody had seen the second one:**

1. the canvas **is the desktop**: taking it from the window, a connection opened by chance in a
   small window would give a small desktop **for the whole session** — and §5.3 has already declared that
   enlarging does not invent detail;
2. ⭐ **the Keyboard Lock exists only in full screen** (`STUDI.md` §web §5). That is, the way this
   product is really used *is* full screen, which is **exactly the condition in which view and
   canvas coincide**. The model does not have a normal case and a degraded case: it has a normal case that
   coincides with the optimal one.

⚠ **No decision taken changes**: §5.0 stays (the client dictates the canvas, at attach), §5.1
stays (resizing the window does not touch the desktop), §5.2 stays as corrected today (the
canvas is encoded, the client rescales). What changes is **what the client reads** to answer.

`[?]` **And three things to measure before believing it**, all in `SPECIFICHE.md` §6.1-bis: that the
page zoom does not falsify the count — ⛔ *the user who pressed `Ctrl +` before connecting
would declare a wrong canvas, and it would stay for the whole session* — what DeX answers, and whether
browser rounding can produce an odd number, which `RCP.md` §4.5 rejects.

> ### ⛔ The first of the three IS MEASURED, and the answer is the worst one — `[M]` 10 Aug 2026
>
> *Bench **S5**, `banchi/01-s5-tela.sh` + `01-s5-pagina.html`, log `banchi/01-s5-esiti.jsonl`
> (two identical rounds, 23:13 and 23:14). Scene: **Xvfb 1920×1080×24** screen, resolution read **outside
> the browser** with `xdpyinfo` = 1920×1080. The detail is in `web/rapporti/S-esiti-sonda.md` §3.*
>
> | Engine | zoom | `screen` | `devicePixelRatio` | **canvas the client would declare** |
> |---|---|---|---|---|
> | **Chrome 151.0.7922.108** | 100 % | 1920×1080 | 1 | 1920×1080 |
> | | 150 % | **1920×1080** | 1.5 | ⛔ **2880×1620** |
> | **Firefox 140.13.0esr** | 100 % | 1920×1080 | 1 | 1920×1080 |
> | | 150 % | **1280×720** | 1.5 | ✅ 1920×1080 |
>
> ⛔ **On Chrome `screen.width` does NOT drop with page zoom**, while `devicePixelRatio` rises:
> the formula of `SPECIFICHE.md` §6.1-bis gives `risoluzione × zoom`. A user on a 1920×1080 laptop
> with zoom at 150 % would declare a canvas **50 % larger than the one that exists** — and it is
> **exactly the defect this decision says it exists to avoid**.
>
> ⛔ **So the reason written next to this decision was `[?]` and now it is FALSE on one engine
> out of two.** `FASI.md` §01-filo-nudo justified it like this: *«`screen.width` drops by a third,
> `devicePixelRatio` rises by a half, **the product stays**»*. It stays on Firefox. On Chrome it does not.
> It is the case of `LEZIONI.md` §2.3-quater caught red-handed: *a decision taken by citing an
> unmeasured behaviour is taken by half* — and this time the behaviour, measured, goes the other
> way.
>
> ⚠ **What does NOT change, and it must be said so as not to suggest a rethink**: the decision stays 🔸
> and stays *«the canvas is the device's screen in physical pixels»*. What falls is **the formula with
> which the client reads it**, not what it must read. ⛔ And it is not fixed with one line: page
> zoom **is not readable from JavaScript in a portable way**. The cure belongs to whoever keeps `SPECIFICHE.md`
> §6.1-bis, and until it exists, a client on Chrome with zoom ≠ 100 % **declares a wrong canvas**.
>
> ⚠ **And half of S5 is not measured**: the **DeX** was not there. *«The laptop's Chrome does it»* says
> nothing about the phone's Chrome — form **E10** — and the second of the three `[?]` stays whole.

### 5.0-quinquies ✅ ⭐ ~~The canvas stays **1920×1080**~~ → **switched on by §5.0-sexies on 14-15 Aug**

> ⭐ **This item closed by itself, as it had foreseen.** It said: *«it stays open, and must be named
> at the phase in which it is switched on, the implementation of `SPECIFICHE.md` §6.1»*. That phase was the **tail
> of phase 4**: §5.0-sexies decided it on 14 Aug and on the 15th the canvas stopped being
> 1920×1080 — it takes the size of the client's window (`[M]` 1264×800 on a 1265×800 window).
> ⚠ The reasoning below **stays valid for its day**, and its last line is the one that
> opened the door.

*13 Aug 2026, at the opening of phase 3, **decided by the user**. It was inherited from the scene of a
bench and had never been decided by anyone: `src/main.c` · `TELA_L` has `TELA_L 1920` written by hand.*

The question was asked with its measured price beside it: on the user's screen the canvas
is painted at **86 %**, that is **912 px of black**. The three alternatives put forward:

| | |
|---|---|
| ⭐ **keep it at 1920×1080** | **chosen** |
| bring it to 2560×1440 (the user's screen) | not chosen |
| switch on `SPECIFICHE.md` §6.1 right away — *the canvas is born from the client's screen* | not chosen: today the product does not do it |

⭐ **The reason is one of method, and it is the reason why the decision was taken on the very day
the phase opened**: phase 3 measures **time**, not geometry. With the canvas still, a
delay that goes past 50 ms accuses the architecture; with the canvas changed underneath, one would not know whether
it accuses the architecture or the pixel count.

⛔ **And the black bands are not the resolution**, or the `[?]` will be reopened in the belief of curing them:
2545×927 of window make a ratio of **2.74** against a 16:9 of **1.7778**. Those bands are the
**shape of the window**, and would disappear only in full screen — changing the canvas does not touch them.

⏳ **It stays open**, and must be named at the phase in which it is switched on, the implementation of `SPECIFICHE.md`
§6.1: today it is a written specification and **not implemented** (§5.0-quater tells its difficult part).

### 5.0-sexies ✅ ⭐⭐ The server's canvas takes the size of the client's canvas — and the coordinate conversion **disappears**

*14 Aug 2026, evening, **decided by the user** after a day in which the mouse on the DeX stayed
unusable through four cures. His words: «abbiamo due tele: quella del server e quella
del client (la dimensione della finestra di rendering del browser). Bisogna solo convertire le
coordinate» — and then, asking for the check: «se questo è possibile, allora non servono più nemmeno
le conversioni».*

⭐ **It does not overturn §5.0-quinquies: it switches it on.** That decision kept the canvas at 1920×1080 for a
reason of **method** («phase 3 measures time, not geometry») and left written ⏳ *«it stays
open, and must be named at the phase in which it is switched on, the implementation of `SPECIFICHE.md` §6.1»*. This is it.

| | |
|---|---|
| **the server's canvas** | is asked for the size of the **client's canvas**, rounded down to **even** |
| **the client's canvas** | shrinks to the **granted** size ⇒ the two coincide |
| **the conversion** | `x_desktop = x_tela`: **the identity** |
| **the black bands** | no longer exist *inside* the image: what is left over (≤1 px per axis) is **page background outside the canvas**, and does not travel on the wire |

> ⚠ **And the warning of §5.0-quinquies was not ignored**, it was read: *«the black bands are not
> the resolution… they are the shape of the window, and changing the canvas does not touch them»*. ⭐ It is true for the
> change that item examined — from 1920×1080 to 2560×1440, **still 16:9**. Here the canvas takes
> the **client's ratio**, so the warning does not apply: the bands disappear because the
> difference in shape that generates them disappears.

#### The measures that made it possible — four benches in parallel, 14 Aug 2026

| | exact size | hot change |
|---|---|---|
| **Mutter** (GNOME) | `[M]` **30 requests out of 30**, from 1×1 to 7680×4320, scale **1.000000**, stride without padding | `[M]` first new frame at **41.6 ms**, no black, session and EIS intact; **20 resizes in 2 s, 20 exact** |
| **labwc** (XFCE, LXQt) | `[M]` exact **even at odd width**; `1×1`, `1919×1079`, `32768×1080` all to the pixel | `[M]` **5.1 ms**, **0 frames lost out of 25** |
| **KWin** (KDE) | `[R]` no validation: neither minimum, nor maximum, nor parity, nor multiples | ⛔ only on `master` — see §5.0-bis |
| **the encoder** | `[M]` the constraint is **even, and that is all** — not a multiple of 8 nor of 16 | — |

⛔ **The even constraint is OURS, not the compositors'**: it is 4:2:0 (`src/codificatore.c` · `croma_flusso` and
`:1512`). `[M]` In 4:4:4 odd passes too. ⇒ It is truncated **down** (2133 → 2132) and **it is
declared** with `TELA(ADATTATA)`: a pixel said is worth more than a pixel hidden in a scale.

#### ⛔ The three guards we must write ourselves — nobody upstream does them

All three discovered by measuring, and all three of the same family: **silence**.

1. **The size cap.** `[M]` Beyond **16384** per side `gnome-shell` dies — and 16386 is
   *inside* the `MAX_SIZE` that Mutter **declares**, so the declared limit lies. `[M]` On
   labwc `32768×32768` kills the compositor **with zero log lines**. ⇒ The cap is set by
   our code, and a client cannot choose it without limits.
2. ⛔⛔ **GNOME's scale.** `[M]` With `org.gnome.desktop.interface scaling-factor = 2` the pixels
   stay the ones asked for but the logical monitor takes **scale 2.0**: the layout becomes
   `roundf(2133/2) = 1067` and **1067×2 = 2134 ≠ 2133**. It is the coordinate space of the **input**
   ⇒ **the pointer goes elsewhere and nobody says so.** Cure: read the scale and **fail** if it is not
   `1.0`.
3. **Asked versus granted.** `[R]` `src/cattura.c` · `chiesta_larghezza`/`chiesta_altezza` never compares the size **asked** of
   PipeWire with the **negotiated** one, and `codificatore_comprimi()` receives the pixels and the stride but
   **not** width and height, so it cannot act as witness. ⛔ Today it is unreachable because
   1920×1080 is always asked: **it is this decision that makes it reachable**, and it must be closed
   together, not after.

#### The shape rule, stolen from neatvnc

⭐ `[M]` Asking labwc for the size **the output already has** answers «succeeded» and **sends
no event**; an old serial answers «cancelled» and does nothing. ⛔ `wayvnc` treats
*succeeded*, *failed* and *cancelled* in the same branch — not to be copied. ⇒ **The truth is told by the
frame, not by the outcome of the request.**

#### ⏳ ⭐ For when the RE-ATTACH is tackled: the solution is already measured, and it is here

*Noted at the user's request, 14 Aug 2026: «il problema della dimensione della finestra
del browser si ripresenterà, ma la soluzione è già bella pronta».*

⛔ **The question will come back, and it is inevitable**: §4.1 promises that **the session survives the
client**, and §5.0 that the canvas **is born at every attach**. ⇒ The day the user detaches from the
DeX and reattaches from the laptop, the browser window has **another size** — and the server's
canvas is yesterday's. It is exactly the case that today would again produce bands, scale and
conversion.

⭐ **And the answer must not be sought on that day: it was measured on 14 Aug 2026**, and it is
**hot** resizing, on the live session, without remaking it:

| | measured cost | what does NOT happen |
|---|---|---|
| **Mutter** (GNOME) | `[M]` first new frame at **41.6 ms** · **20 resizes in 2 s, 20 exact** | no black frame, **session and EIS intact**, no reconnection |
| **labwc** (XFCE, LXQt) | `[M]` **5.1 ms** · **0 frames lost out of 25** | no black frame; the next frame is already at the new size |
| **KWin** (KDE ≤ 6.7.4) | ⛔ does not exist | ⇒ the declared fallback of §5.0-bis applies, and **only there** |

⇒ ⭐ **Re-attach at a different size is not an open problem: it is a case already covered**, on three
desktops out of four, at a cost the user does not perceive. Whoever tackles that topic does not have to
study anything new — they must **call** `cattura_ridimensiona()` and reread this table.

> ### ✅ ⭐⭐ WRITTEN AND MEASURED — the night of 15 Aug 2026
>
> *This item said «`cattura_ridimensiona()` at the date of this item **does not exist yet**: it is
> the only line of work left». Now it exists, and with it the whole chain.*
>
> **The chain, by name**, and every link sits where the thing that knows sits:
>
> | where | what |
> |---|---|
> | `src/pagina.html` | `chiedi_tela()` sends `ADATTA_TELA` with the size of the window, **at attach** |
> | `src/rcp.c` `T_ADATTA_TELA` | applies §4.5 (limits, parity, `video.misura_massima`) and passes the request to the stage. ⛔ **It does not answer right away**: it marks a request «in flight» |
> | `src/webtransport.c` · `src/main.c` | carry the question across the process boundary |
> | `src/figlio.c` `figli_ritela()` | → `MSG_INPUT/RITELA` to the child |
> | `src/cattura.c` `cattura_ridimensiona()` | → `pw_stream_update_params()` |
> | ⭐ and **the answer comes back**: `MSG_TELA` → `rcp_tela_dal_palco()` → `TELA(ADATTATA)` |
>
> ⛔ **The answer comes back, and is not guessed**: tonight's first draft had the parent deduce
> the outcome **from the frames** («if one of a different size arrives, the stage has obeyed»), and four
> agents sent to refute it found three cases in which it deduced wrongly — among them **two
> chained `ADATTA_TELA`**, that is a user dragging the edge of the window. ⇒ The child now
> answers carrying **two** sizes: the *asked* one (to recognise which request it is answering) and
> the *obtained* one (`0x0` = it did not manage).
>
> #### `[M]` The night's measures, on the test machine, user `prova`, headless GNOME
>
> | | before (14 Aug) | now (15 Aug) |
> |---|---|---|
> | ⭐⭐ from the video channel to the first frame | **4.4 s** (659 «empty waits») | **311 ms** |
> | the canvas in force at attach | 1920×1080 fixed | **1264×800** = the browser window |
> | the client's drawing scale | 0.658 (`imageRendering: auto`) | **1.000** (`pixelated`) |
> | the hot resize (1264×800 → 1000×640) | did not exist | ⭐ **6 ms** from the stage's answer to the keyframe sent |
> | frames discarded for size · held back · errors | — | **0 · 0 · 0** |
>
> ⭐ **And the desktop says it by itself**: GNOME *Settings → Displays* inside the remote session
> reports **«Resolution 1264 × 800 (3:2)»** and **«Scale 100%»**. It is not a log line of ours:
> it is the compositor declaring the size we asked of it.
>
> #### The three guards: where they ended up
>
> | guard | state |
> |---|---|
> | 1 · the size cap | ✅ `rcp_misura_ammessa()`, and ⛔ **corrected tonight**: the limits are those of §4.5 **per side** (320..7680 × 240..4320), not the 200..8192 of the first draft — which `ATTACCA` would have rejected on re-attach |
> | 2 · GNOME's scale | ✅ **closed tonight** as §5.0-sexies asked («read the scale and **fail**»): `mutter_scala_nostra()` + the refusal in `prendi_il_palco()`. ⚠ It looks at **our** monitor, not the worst one of the machine: a laptop with the internal screen at 2.0 has no defect. `[M]` on the test machine the scale of our «Meta-0» is **1.000**, and the line is written even when it is good |
> | 3 · asked versus granted | ✅ in `cattura.c` (`su_parametri`), and since tonight also **in the child**: the 28 bytes of §6.2 carry the size of the FRAME, not the one that had been asked |
>
> #### The timings, and the why of each
>
> | | value | why |
> |---|---|---|
> | `RCP_TELA_ATTESA_MS` | **3000 ms** | the floor beyond which `NON_ORA` is answered anyway: §7.1 wants one `TELA` for every `ADATTA_TELA`, and §6.2 makes the client **hold back frames** while it waits |
> | `RCP_TELA_RICHIAMO_MS` | 500 ms, doubling up to 8 s | how often the stage is **asked** to go back to the canvas in force, when it has one of its own |
> | ~~`TELA_FONDO_MS` (client)~~ ⛔ **REMOVED on 17 Aug 2026** *(realigned on the 28th)* | ~~250 ms~~ | whoever drags an edge produces dozens of `resize` per second — ⭐ but the floor went out **with the function it served** (`tela_forse_chiedi()`): `src/pagina.html` keeps its tombstone, because the cure would have to be put back only if someone put back the chasing |
> | `RISVEGLIO_MS` (child) | 400 ms | how often the stream is restarted when **a keyframe is due and the scene is still** — it is the cure for the 4.4 seconds |
>
> ⛔ **And one thing the server does NOT do, because of a line missing from `RCP.md`**: when the stage changes
> size **without anyone having asked it to**, the server **does not adopt** the new size and sends
> no `TELA`. The first draft did — it seemed kind — and it is fatal: §6.2 says that the
> client holds back a never-announced size **only while it has an `ADATTA_TELA` without answer**, and
> without that it is `ERRORE_PROTOCOLLO`. ⇒ The stage **is asked to go back**, with a wait that
> grows, and meanwhile the session shows the last good image (I1: ugly and alive). ⏳ The missing
> line is in `RCP.md` §7.1: *what a server does when the stage changes size by itself*.

⚠ And the three guards above hold **all the more** on re-attach: it is the moment in which the
size really changes, that is the moment in which a silent divergence between asked and granted
would have its consequences.

#### On KDE nothing changes: §5.0-bis applies

⚠ *And §5.0-bis must be corrected on one point*: it said «KDE < 6.8». `[R]` Checked on 14 Aug on
invent.kde.org: **`Plasma/6.8` does not exist**, the last tag is **v6.7.4**, and hot
resizing is **only on `master`**, without a date. ⇒ Read «KDE ≤ 6.7.4, and the version that brings it
has not been released yet».

### 5.0-septies 🔸 At farewell the stage is **NOT** put back to a resting size — *provisional, 22 Aug 2026*

*Brought to the user as one of the two decisions waiting for him. ⛔ **And I had put it to him with
a false premise**: «whoever connects inherits the window of whoever was there before». There is no «whoever
was there before» — multi-tenant is **phase 10** and does not exist, and the graphical session is **one per
user** (invariant **I2**, `sessione.c` · `sessione_assicura()`). ⭐ **The user spotted it**, and the item is here
for that too.*

**What really survives**: not someone else's session, but **the stage size** left
by **the previous connection of the same user**. `RCP.md` §4.5 declares it — *«the canvas
SURVIVES the session»* — and `[M]` on 21 Aug on the real product three attaches in a row with
`ATTACCA(1920×1080)` received `SESSIONE` with **1920×1080**, **1264×800** and **1600×900**: each
time what the previous round had left.

**The decision, for now**: it is left as it is. Three reasons, and the third is the one that counts:

1. ⭐ **it already corrects itself**: the size in `ATTACCA` is a **preference**, but right after
   `SESSIONE` the client sends `ADATTA_TELA` with its true size (§5.0-sexies, since 15 Aug). ⇒
   Only an **instant** remains at attach in which the canvas in force is the old one;
2. ⛔ **a rest at farewell is a second reshuffle of the windows** done while the user is not
   looking: the desktop reshuffles the windows at **every** change of the monitor size, and that
   reshuffle the server cannot undo;
3. ⛔⛔ **and it would not cure the real problem.** The cost the user would see is the scenario
   PC → phone → PC: from the phone the stage shrinks, GNOME **squashes the windows** to
   make them fit, and on return the stage goes back to large **but the windows stay squashed**. A
   resting size does not put them back where they were — it adds a third one.

⏳ **`[?]` And the route that would really cure that scenario is another one**, and it belongs to **phase 9**: not
making the stage change size when attaching from a small screen, and letting the
client **rescale** — which is precisely what the product already knows how to do for the view (§5.1). ⚠ It is not anticipated
here: it needs the working point between quality and bandwidth, which is phase 9.

🔸 **Why it is provisional and not closed**: *«per il momento accetto il tuo suggerimento, ma poi ci
penserò su»* — the user, 22 Aug 2026. ⇒ The item must **not** be marked ✅ until he comes back to it, and
whoever reopens it finds here the reason why it had been left like this.

### 5.1 ✅ If the user resizes the window, the image is rescaled

*8 Aug 2026. «Tagliamo la testa al toro. Anziché correre dietro ai compositor, una scelta
che vale per tutti».*

**Resizing the client's window never touches the desktop.** The view adapts; the user's
windows do not move. The same on GNOME, KDE, XFCE and LXQt.

> ### ⚠ AND SINCE 15 AUG 2026 THIS ITEM HOLDS **DURING** THE SESSION, NOT AT ATTACH
>
> §5.0-sexies decided that **the server's canvas takes the size of the client's canvas**, and that
> size is asked **at the attach of every session**. ⇒ At attach the desktop *changes* size, and it
> is intended: it is the user's decision of 14 Aug.
>
> ⛔ **But the three reasons of this item have not aged**, and the third least of all: on KWin
> resizing an output **rearranges the user's windows**. ⇒ During the live session the
> behaviour stays the one written here — the view is rescaled, the desktop is not touched.
>
> ### ⛔⛔ AND SINCE 17 AUG 2026 THERE IS NOT EVEN THE SWITCH ANY MORE — see **§5.1-bis**
>
> Chasing the window sat behind `?adatta=segui`, off by default (I6). **It went out of the
> product**: *«non voglio mettere delle eccezioni nel progetto»*. ⇒ This item goes back to holding
> as it was written on 8 Aug, **without exceptions**, and the values of `?adatta=` remain two:
>
> | `?adatta=` | what it does |
> |---|---|
> | *absent* (default) | asks for the canvas **at attach and at reattach**, and that is all |
> | `no` | ⛔ never asks for it: it is the page from before 15 Aug, and it serves the **A/B comparison** that the user's judgement requires (`LEZIONI.md` §7.3) |
> | ~~`segui`~~ | ⛔ **removed on 17 Aug 2026**. An old address carrying it counts as the default and switches nothing back on — guarded by `banchi/06-b37-modi.py` |
>
> ⚠ It is read from `?` **and** from `#`, like `video` and `disposizione`.

The three reasons, and the third is the one that decided:

1. on KDE 6.3.6 — that is Debian Trixie — resizing **is not possible**: the size sits in KWin's
   command line (`--virtual --width W --height H`), the mode is `const`, and
   `stream_virtual_output` answers `Could not find output` for every size `[M]` 8 Aug;
2. the upstream fix exists (`kwin!7932`, milestone 6.8, October) but **Debian stable does not
   update Plasma**: 6.3.6 for all of Trixie (Forky, still testing, already has 6.7.2 `[R]` 4 Oct). The fallback is not temporary scaffolding, it is a
   code path to maintain for years;
3. ⛔ **and even where it works, it does something worse**: resizing an output rearranges the
   user's windows `[R]`. On KWin the key of the `PlacementTracker` contains the geometry
   of the output, so going back to a size already seen the windows are **teleported**
   back. The «right» version messes up the work; the «broken» one leaves it still.

**Consequences:** ⛔ *superseded by §5.1-bis (17 Aug 2026), and reconfirmed by the user on 2 Oct 2026 after
his test by hand: hot resizing does not even stay as an optional function; the
new size is taken only by reconnecting. The three lines below stay as a chronicle.*
- compositor resizing leaves the critical path and stays as an optional
  function («fit the desktop to this window»), off where the compositor cannot
  do it, **with the reason declared** (`CODER.md` §4.2);
- when it is written, it will be written **in the form of PipeWire negotiation** — decision already
  taken in `STUDI.md` §kde §8.2 — because it is one single route for GNOME, wlroots and KDE 6.8, and on KDE it
  switches itself on at the update;
- ⚠ and it will include the **mandatory guard** `if (misura_attuale == misura_richiesta) return;`
  (`STUDI.md` §kde §8.2-bis): without it, renegotiation chases its own tail. The defect **does not show on
  Trixie** and appears on the day of the update to 6.8, when nobody is looking for it any more.

### 5.1-bis ✅ ⛔⛔ Hot resizing **goes out of the product** — 17 Aug 2026

*«Ecco la mia decisione. Non voglio mettere delle eccezioni nel progetto. Il dynamic resolution
esce dalle funzionalità di Remotix.»*

**What goes out:** changing the size of the canvas **while the session is alive**. The switch
`?adatta=segui`, the floor `TELA_FONDO_MS`, `tela_forse_chiedi()` and the `resize` branch are removed
from `src/pagina.html`.

**What stays, and it is the logic from before:** ⭐ *the canvas is born with the size of the client's
window, at the moment of the birth **or of the reattach** of the session* — §5.0-sexies, intact. From there
on the desktop is no longer touched: the client rescales (§5.1, which goes back to holding **without exceptions**,
as it was written on 8 Aug).

#### Why — and the reason is not the code, it is the product

⛔ **The exception was measured, not feared.** On Mutter changing the canvas hot costs `[M]` **6 ms**
and works. On KWin ≤ 6.7.4 — that is **Debian Trixie, and up to Forky** — `stream_virtual_output`
answers **`Could not find output` to every size** (`[M]` 8 Aug 2026, five sizes tried,
`VirtualBackend` does not override `createVirtualOutput()`). ⇒ Keeping it would have meant **a
product that does a different thing depending on who hosts it**, with a branch conditioned on the
compositor and a bench for each branch.

⚠ **And waiting for KDE to update is not enough.** `kwin!7932` «Resizable Virtual Monitors» is merged
(29 Jul 2026, milestone 6.8, **14 Oct 2026**) and in our very same form — PipeWire
negotiation — but:

- `[R]` checked on **17 Aug 2026** on invent.kde.org: the last tag is still **v6.7.4**,
  `Plasma/6.8` does not exist;
- Debian stable does not update Plasma ⇒ the exception would have stayed **for years**, not for two months;
- ⛔ and **even where it works it does damage**: resizing an output **rearranges the user's
  windows** (the key of the `PlacementTracker` contains the geometry of the output, so going back
  to a size already seen the windows are teleported). The «right» version messes up the
  work; the «broken» one leaves it still.

✅ **Reconfirmed on 4 Oct 2026, looking at Forky** (Debian 14, Plasma 6.8 expected): a resizable KWin
does not reopen the item. *«il dynamic resize non è una funzionalità così importante,
le cose grosse adesso le abbiamo e funzionano bene, anche su Android»* (the user).

#### ⚠ And the user's request that this decision superseded

*17 Aug 2026, before the decision*: **«l'utente trascina i bordi e rilascia, e solo allora
avviene il ridisegno»**. It was feasible, and the technical note stays because the day someone
proposed it again they would find it unchanged:

> The window edge **is not in the document**: the window manager drags it. The
> page receives neither `mousedown`, nor `mouseup`, nor `pointerup`, and an event «the resize
> is finished» **does not exist in any engine**. ⇒ «It has released» can only be **deduced** — «N ms
> have passed without another `resize`» — and that was exactly what the 250 ms floor did.

**Consequences:**
- ⛔ **black bands remain possible, and they are the declared behaviour**: if after attach the
  window changes shape (resized, or the tablet **rotated**), the proportions no longer match
  and the client rescales with letterboxing — `SPECIFICHE.md` §6.2, «letterbox, do not stretch». It is not a
  defect to cure: it is the choice;
- ⭐ **`ADATTA_TELA` stays in the protocol** (`RCP.md` §7.1) and the server chain stays alive **in
  full** — attach uses it, and **reattach** uses it, where the stage already exists with the size of
  another device. ⚠ Whoever removed it believing it a child of the chasing would break
  reattach;
- `banchi/06-b37-modi.py` changes job: from «the three modes of `?adatta=`» to **guard against the
  return** — 0 requests in all modes, `?adatta=segui` included, which is now only an old
  bookmark;
- `banchi/06-b37-voce.py` V4 changes question: from «does the voice switch off?» to «has the function really
  gone out?». ⚠ V1–V3 stay: the switched-off voice is still needed, because the canvas is asked at every reattach
  and the repetition on `NON_ORA` is alive;
- ⛔ and **phase 11 (KDE) no longer inherits anything to decide here**: the declared fallback of §6.3 —
  `COMPOSITORE_INCAPACE`, the client rescales — becomes the **normal** behaviour of everyone,
  not the poor branch of one.

### 5.2 🔸 ⛔ ~~The encoder works at the window's size~~ → **no: it works at the canvas's size**

> ⛔ **Corrected on 9 Aug 2026, while writing `RCP.md` §6.2.** This item said: *«A gift that
> comes free from 5.1: small window ⇒ fewer pixels to encode ⇒ the same bandwidth yields
> more»*. **It contradicted §5.0-ter**, which is two items away and says the opposite — *«the server
> keeps encoding the whole canvas and the client shrinks it»* — putting the optimisation
> **deliberately outside the model**, as a `[?]` to be measured first.
>
> **§5.0-ter wins**, and not by seniority: it is the one that holds together with the rest. `SPECIFICHE.md`
> §6.1 says that during the session **it is the client that rescales**, and §6.3 says that the fallback on KDE
> *«does not cost one more line, because it is the same code as the during-the-session point»* — that is, the
> rescaling in the client. If the server encoded at the window's size, that code would not
> exist and the fallback would cost plenty.
>
> ⚠ **The gift was not free**: changing the encoded size at every drag of the border
> means renegotiating the encoder — and with `DECISIONI.md` §5-bis.0 the border is dragged
> **ten times a day**, because on DeX the window is resizable. It was a `[?]` disguised
> as a consequence, that is error form **E5** of `REVIEWER.md`.

**What holds now**: the server encodes at the size of the **canvas**, the client rescales. RCP's
`VISTA` message exists all the same and serves to choose **how many bits to spend**, not how many
pixels to produce; and the frame header carries the size as a field, so that the day
§5.0-ter were closed **the protocol does not change** (`RCP.md` §6.2, §7.1).

### 5.3 🔸 The price of 5.1, declared

A 1080p canvas viewed from a 4K screen = an enlarged desktop, hence soft. Enlarging does not
invent detail. The way out is the «fit the desktop» item, and it is the reason why the
initial size of the canvas matters — see the open question §7.1.

---

### 5.4 ✅ ⭐⭐⭐ The visible canvas is painted with **`bitmaprenderer`**, not with the 2D canvas — 17 Aug 2026

**Decided on the user's judgement** — *«NIENTE ARTEFATTI!»* — after two days of hunting the
**64×192 rectangular blocks** he saw in the still areas.

⛔ **The cause was not ours, and it is out of reach of any bench that reads the pixels back**: the
**2D** `<canvas>` receives the right pixels and breaks **on its way to the screen**. The proofs, one per
suspect, are in [`fasi/06-la-tela-e-la-vista.md` §4.9](fasi/06-la-tela-e-la-vista.md) —
clean capture, clean encoder (0 spoiled superblocks out of 600), clean `copyTo`, `getImageData`
**0 out of 180 000** — ⛔ **and the same canvas photographed with the mobile phone showing the rectangles**.

⇒ ⭐ **`getImageData` reads the backing store, not the screen.** A bench that reads the canvas back is green
**by construction**, and for two days it said everything was fine.

**The cure**: `createImageBitmap()` + `transferFromImageBitmap()` on a **`bitmaprenderer`** context,
which does not have the 2D backing store. ⚠ It is not an optimisation and it is not a switch: it is **the** drawing
route of the product (`niente eccezioni`, §0).

**What changes in the product, and what does not:**

| | |
|---|---|
| ⛔ **the two 2D canvases disappear** | today the frame passes through `deposito_p.drawImage(f)` **and then** through `pennello.drawImage(deposito)`: two copies and two backing stores |
| ⭐ **the store canvas is no longer needed** | `transferFromImageBitmap` **sizes the canvas by itself**, and when the window is resized the content **stays**: the reason the store canvas existed (§5.1, black until the next frame) falls by itself |
| ⭐ **the cursor is not touched** | it is a **CSS** cursor, it is not painted on the canvas ⇒ the visible canvas does not have to **composite** anything |
| ⚠ **centring is done with CSS** | when the window is wider than the image. The bands were already **outside** the buffer (§5.0-sexies), so no measure is lost |
| ⚠ **and the cost must be measured** | `createImageBitmap` is **asynchronous**: it enters the delay path, which is the number phase 3 exists for. `[?]` until there is the measurement |
| ⛔ **the fallback is declared** | if `getContext("bitmaprenderer")` is not there, it goes back to the 2D canvas **and writes it in the log** — `CODER.md` §4.2. It is not an exception per compositor: it is a missing capability |


---

## 5-bis. The input

### 5-bis.1 ✅ The pointer is drawn by the client, not by the desktop

*8 Aug 2026, proposed by the user.*

The finger drags a pointer **drawn by the client**; a tap makes the left click at the
pointer's position, a two-finger tap the right one. It is not «direct touch», where the finger
is the pointer: it is the trackpad, and you see where you are about to click **before** clicking.

**Three different problems this choice closes together:**

1. ⭐ **perceived latency.** The pointer moves at the speed of the finger, not at that
   of the network. On a mobile link with 150 ms of delay it is the difference between usable and
   frustrating — and it weighs more than frames per second, which is the quantity people usually
   look at;
2. **the trails and the stale positions** of the pointer, which are born precisely from the
   pointer travelling *inside the video* and arriving late;
3. **precision.** A finger is ~10 mm wide, a desktop's targets measure ~4, and in
   direct touch the finger **covers the target** while looking for it. Moreover the pointer's
   hover — on which tooltips and menus depend — exists only if a pointer really is there.

### 5-bis.2 🔸 The cursor must NEVER be inside the captured image — and it must be verified

It follows from 5-bis.1: if the client draws it and it is also in what arrives, you see
**two**. v1 had met the problem three times without connecting them, and the cure is its own:
*«don't hide it: make it invisible»* — a theme with a 1×1 cursor at zero alpha.

| Desktop | Is the cursor in the capture? | The channel of the cure |
|---|---|---|
| GNOME / Mutter | **no**, it excludes it on its own (`inhibit_cursor_overlay`) | ⚠ and if it were needed, **not** `XCURSOR_THEME`: Mutter does not read it, it reads `org.gnome.desktop.interface cursor-theme` |
| KDE / KWin `--virtual` | **yes** `[M]` — no cursor plane ⇒ painted in the framebuffer | `XCURSOR_THEME` (+ `XCURSOR_SIZE`, which KWin demands) |
| wlroots — XFCE, LXQt | **yes, always** on headless; `overlay_cursor` does not remove it, it **forces it to software** | `XCURSOR_THEME`; on labwc `XCURSOR_SIZE` is not mandatory |

⛔ **The trap, and it must be verified instead of hoped for**: on wlroots a theme that loads **zero**
cursors makes the library fall back on a **built-in, visible** theme — that is two pointers,
through a silent fallback (`REVIEWER.md` E2). At least one valid cursor is needed, `index.theme`
**without `Inherits=`**, and the ten names labwc asks for. And the outcome is **checked after the session
has started**: that the theme was written is not that it was loaded.

*The slot to put it in already exists: the session's environment is composed from scratch, one variable
at a time (`CODER.md` §4.5) — so the cure lives in the program and not in a file, as I7 wants.*

### 5-bis.0 ✅ On Android the primary use is **Samsung DeX**, and touch is the fallback

*9 Aug 2026. «DeX assolutamente. È l'uso primario che faccio quando uso android perché la
verità è che usare certi programmi con il touch anziché nel modo classico è un ripiego di
emergenza, non la normalità.»*

⛔ **It overturns the priority with which the Android input had been designed**, which was all around the
phone in the hand — that is, around the case the user almost never uses.

| | Before | Now |
|---|---|---|
| physical mouse and keyboard (5-bis.8) | a passenger | **the main route** |
| the seven gestures (5-bis.3) | the input model | **the emergency fallback** |
| resizing the window (§5.1) | an edge case | **what is done all the time** |

With DeX the phone drives an external screen with a real mouse and keyboard: the canvas is born
**desktop**-shaped and not phone-shaped, and the window gets dragged.

⭐ **Three decisions come out of it strengthened, not weakened:**

1. **the pointer drawn by the client** (5-bis.1) was right with the finger; with a real mouse it becomes
   non-negotiable — a pointer that chases the hand while working «the classic way» is the
   difference between using it and closing it;
2. **the resizing that does not touch the compositor** (§5.1) goes from a prudent choice to a forced
   choice: if, dragging the border ten times a day, the windows *inside* the session got
   reshuffled, the product would be unusable. It had been decided because of KWin's wall; it
   turns out it was right for real use too;
3. **the rule on command modifiers** (5-bis.6) was a clarification; working the
   classic way it becomes **load-bearing**, because shortcuts are half of the work.

⭐ **And good news on the cost**: if the primary use is DeX, the Android client resembles the Linux
one much more than expected — same interaction model, different only in the decoding
stack. It reduces the risk flagged in §0.3 by moving Android to the end: the protocol was not
designed for the wrong client, because the two clients resemble each other.

> ⭐ **Confirmed and made stronger from 9 Aug 2026 (§1.6).** The decision stays whole — the primary
> use on Android is DeX, touch is the fallback — and all that changes is that the program is **the browser
> on DeX** instead of an application of ours. ⚠ From which a new question that was not there, and that goes
> to the probe: **on DeX, in a resizable window, does the browser give `Pointer Lock` and the
> shortcuts?** Without the first you see two pointers (5-bis.8), without the second half of the work
> goes into the browser instead of into the session.

### 5-bis.0-ter ✅ The Android emulator is a workbench, not a measuring instrument

*9 Aug 2026. «Per android forse dovremmo ricorrere a degli emulatori (che entrerebbero a far
parte dell'ambiente di sviluppo).»*

Accepted: SDK, emulator, `adb` and the link to the phone enter the environment, and they are put
already in **phase 0** because the probe of phase 2 requires them.

⚠ **Corrected the same day, after the user asked to search better.** The first
draft said that DeX «does not exist on the emulator»: **it is false**. There is the **Desktop AVD**
(«13.5" Freeform» profile, from Android 11; the Android 13 version adds keyboard shortcuts
and mouse support), and **Samsung itself documents the emulator for DeX** — *«If you don't have the
DeX Station, you can test your app resize behavior in Android Studio using Android Virtual
Device»*, at 160 dpi and 1080×1920. The interaction model we care about **is testable there**, and
it is a large part of phases A1 and A3. Samsung warns, however, that the emulator **simulates, does not replicate**.

⛔ **The border stays, but it is narrower and sharper**: *on the emulator you develop, you do not measure.*
**No number of this project is declared on an emulator.** What it does not give is
**hardware decoding** — its MediaCodec is not the phone's silicon, and `[?]` it was not
possible to establish that it exposes a hardware HEVC decoder — plus the real delay, the
battery and the changing network.

⚠ It is `REVIEWER.md` **E10**, *a green test on the wrong client*: an emulator that says «it works»
while the phone does not is a green bench with the defect alive — the form that cost v1 the most, with
a correction written on a bench that did not reproduce the defect and shipped to the user, **which made
things worse**.

**The real phone is the measuring instrument; the emulator is the workbench.**

> ⛔ **Lapses almost entirely on 9 Aug 2026, with §1.6**: there is no longer an Android application to
> build, so neither SDK nor APK nor Desktop AVD is needed — **the workbench is the laptop's
> browser**, which is handier than any emulator.
>
> ⭐ **But the line that counts survives word for word, and is worth even more**:
> *«no number of this project is declared on an emulator»* becomes **«no number is
> declared on a browser that is not the one of the real device»**. A Chrome on a laptop that
> decodes HEVC in hardware **says nothing** about the phone's Chrome: it is the same error
> form **E10**, in a new disguise.

### 5-bis.0-bis ✅ RDM is a reference to **draw inspiration** from, not a product to redo

*9 Aug 2026. «Ora noi non dobbiamo rifare RDP e/o RDM, ma secondo me trarne ispirazione sì.»*

⚠ **In v1 RDM had a different role**: it was the **client to serve** — *«if it doesn't work here, it doesn't
work»* (`fondamenta/documenti/client-android.md` §1.2). In V2 we write the client ourselves, so
it changes job: from **constraint** to **reference**.

⛔ **And the border is sharp, because RDM is proprietary** (Devolutions,
`com.devolutions.remotedesktopmanager`): what is studied is **how it behaves and how it feels in use**,
never how it is made inside. The best source is not the code anyway: it is the user, who uses it every
day.

⭐ **What is taken from it, and it comes from a single sentence**: *«funziona bene sia con interfaccia mobile
sia in modalità desktop»*. It is not the video that adapts — they are **two interfaces**, and
the application chooses by itself which one to show.

🔸 From which, for our Android client: **one single application, two interfaces**, and the switch
is **automatic on the context** — external screen and mouse connected, or phone in the hand — not
a setting the user has to go looking for. It is the shape that phases **A3** (the classic
way) and **A4** (touch) have already taken.

> ⭐ **Survives intact past 9 Aug 2026 (§1.6), and becomes easier**: «one application, two
> interfaces» is **one page, two layouts**, and the automatic switch on the context is the thing
> a page does better than any other technology — you look at whether there is a fine pointer
> and how big the window is, not «is it Android or is it Linux». ⚠ The substance however does not change: **two
> real layouts, not one that gets stretched**, and that is the lesson taken from RDM.

**What instead is NOT taken from it:**

| | Why |
|---|---|
| being a **connection manager** — RDP, VNC, ARD, SSH, FTP and fifty-odd more | it is a merit for them and out of scope for us: REMOTIX is a single product, and `SPECIFICHE.md` §12 excludes compatibility with other protocols |
| its **choice of codec** (RemoteFX Progressive) | it was the right engineering *for RDP and for a phone without hardware decoding*. We aim at HEVC in hardware — ⚠ and if the probe of phase 2 said no, **this** is the line to reread |

### 5-bis.3 ✅ The fan of gestures — **the fallback, not the main route**

*9 Aug 2026, all seven confirmed. ⚠ And scaled down the same day by 5-bis.0: on
Android the primary use is DeX, with a real mouse and keyboard. These gestures serve the phone in the
hand, which is the emergency fallback — they remain necessary, but they are not the thing to get right
first.*

| Gesture | Effect |
|---|---|
| 1 finger drag | moves the pointer |
| 1 finger tap | left click |
| 2 finger tap | right click |
| 2 finger drag | wheel / scrolling |
| tap-and-a-half (tap, then press and drag) | dragging and selection |
| 3 finger tap | middle click |
| pinch | enlarges the client's **view**, not the application |

⚠ The *tap-and-a-half* is not a luxury: without it, you cannot move a window or select
text. Tap and two-finger drag are not confused — a tap is short and still.

> ⭐ **And with what reserve they were confirmed**, which is worth more than the table: *«tanto poi sono
> sicuro che su alcune specifiche ci torneremo quando avremo il sistema funzionante sotto
> mano»*. It is `LEZIONI.md` §7.3 applied to gestures, and for gestures it counts double — a gesture is not
> judged by reading it, it is judged by using it. This table is therefore a **declared starting
> point**, not a commitment: whoever finds it different six months from now has not found a defect.

### 5-bis.3-bis ✅ ⭐ The bar carries **a single button**: `Ctrl+Alt+Canc`

*14 Aug 2026, decided by the user in front of the phase 4 measurement.*

⛔ **The fact that produced the question, and it is `[M]`** (`fasi/rapporti/F4-A9-scorciatoie.md`): six
combinations **will never arrive** at the remote desktop — `Super`, `Super+D`, `Alt+Tab`, `Alt+F2`,
`Alt+F4`, `Ctrl+Alt+Canc`. ⚠ And it is not a browser limit: **the client's compositor takes them**,
and **no API will ever take them back**. The only way to provide them is an on-screen button — which however takes
pixels away from the desktop's image.

**Chosen: just one.** ⛔ And the reason it is that one and not another is of a different nature from taste:
without `Ctrl+Alt+Canc`, **in a locked session the user can no longer get in** — it is the only one of the six that,
when missing, leaves him **outside** rather than inconvenienced. `SPECIFICHE.md` §7.3-bis calls it *«a requirement,
not a makeshift fallback»*, and three mature references out of three do it.

⚠ **The other five stay written and switched off**, with their reason beside them: the choice is one of taste and
is revisited **by looking at it**, not by reading it (`LEZIONI.md` §7.3, the same reserve with which the user
confirmed the seven gestures). ⛔ Switching one on costs **one line**.
⛔ **And switched off means NOT DRAWN**, not «drawn and inert»: a button that is there and does nothing
is worse than a button that is not there. The five combinations stay however **in the table of the
declared ones**, where the user reads that his computer keeps that keystroke for itself — ⭐ because
`SPECIFICHE.md` §7.3-bis forbids **pretending** they arrived, not not offering them.

---

### 5-bis.4 🔸 The cursor channel, and its compromise

The client must know **what shape** to draw: the I-beam on text, the double arrow on borders,
the hand on links. So a channel is needed that carries **shape and hotspot** when they
change.

The compromise, accepted: the **position** is immediate because local, the **shape** arrives with
one network round of delay. Moving quickly over a border, the double arrow appears a
moment later. It is the right side of the compromise — the delay of a shape nobody notices,
that of a position everybody notices.

### 5-bis.5 🔸 What the input channel carries

| | |
|---|---|
| **absolute** pointer | yes — and it is **the only** pointer path (see 5-bis.8) |
| ~~relative pointer~~ | ⛔ **removed on 9 Aug**: it was justified by *Pointer Capture*, and the justification was wrong. See 5-bis.8 |
| **scancode** | yes — control keys and physical keyboards |
| **Unicode** | yes, and on Android it is the **main route** (see §7.10-bis) |
| **multi-finger touch** | slot reserved, **not implemented** `[?]` |
| **stylus** (pressure, tilt) | out, for now |

Native touch does not get in because it does not solve precision, desktop applications
handle it badly, and it would have to be verified that the EIS of Mutter and KWin expose the
«touch» capability — `libei` provides for it, that the two offer it is `[?]`. The **reserved slot** costs nothing
now and saves a rewrite if one day it were needed.

### 5-bis.6 ✅ Letters travel as letters, the keys that are not letters as positions

*8 Aug 2026.*

| What | How it travels |
|---|---|
| letters, numbers, signs — everything that is printed | **as letters** (character) |
| Enter, Tab, Esc, arrows, F1-F12, Ctrl, Alt, Shift, Super | **as positions** — they are not letters, and they sit in the same place on every keyboard |

**The problem this choice solves**, and it is the one the user isolated by himself: a
physical keyboard does not send letters, it sends **positions** — the key to the right of L says «key
39», and it is the desktop that decides whether it means «ò» (Italian layout) or «;» (American). If
positions travelled on the wire, a client with an American keyboard attached to an Italian
session would produce **the wrong letters**: it is the classic defect of every remote desktop.

By making letters travel, the *client's* layout is applied by the client's system, and
our session does not have to guess anything. It holds for **both** clients, not only for
Android — where however it is mandatory anyway, because an Android keyboard has no positions:
it is an IME that produces text.

⛔ **The clarification missing from the line above, added on 9 Aug: `Ctrl+C` is not text,
it is a command.** Sent as «letter c», the remote application would receive a c to write
instead of a copy to make. So the complete rule is:

> A keystroke travels **as a letter** when it is writing text. When a **command** modifier
> is held down — Ctrl, Alt, Super — it travels **as a position**, because at that
> moment it is not a letter. Shift and AltGr do not count: those serve to *make* the letter, and
> stay inside the text path.

⭐ **And this gives a second reason to 5-bis.7**, which had been decided for a different motive: the
shortcuts travel as positions, and positions match only if the two layouts
are the same. On a German keyboard the Z is where on ours the Y is — without
renegotiating the layout at attach, `Ctrl+Z` would end up on another key.

⚠ **Only reachability remains.** If in the session's layout a character does not
exist on any key — an emoji, a different alphabet — **nothing** comes out, and the server
**declares it in the log**: never a different letter, never a silence (`LEZIONI.md` §1.8).

**As a dowry**: modifiers were never the problem and are emulated normally (for «A»:
press Shift, press 30, release 30, release Shift); repetition is not ours (wlroots
discards repeated keys, it is the application that repeats); and the layout declared by the client
— v1's «question no. 7» — is no longer needed to *interpret*, only to *choose* (5-bis.7).

### 5-bis.6-bis ✅ ⭐ Composed accents and Asian keyboards stay **out, declared**

*14 Aug 2026, decided by the user in front of the phase 4 measurement
(`fasi/rapporti/F4-A7-pagina-classico.md`).*

**What already works** `[M]`: the Italian `à`, because on the Italian layout **it is a key of
its own** and goes through the `LETTERA` path like all the others.

⛔ **What stays out**: **dead keys** (the `à` composed in two keystrokes of a
French or «US international» keyboard) and the **IME** (Chinese, Japanese, Korean). ⚠ And it stays out
**declared**: the page writes it, and **neither lets a different letter out nor stays silent** — which is the
rule of `RCP.md` §7.3 applied to the client side.

**The price it was chosen not to pay**, and it was foreseen: to have dead keys and IME you need an
**editable element with focus over the canvas** — that is `STUDI.md` §web §1.2 C — and that element sits
**between the pointer and the image**: ⛔ the path by which the page draws the arrow today **would have to be
redone**. ⇒ A certain and visible cost, against a gain that for today's user is **zero**.

⚠ **And it reopens by itself the day a foreign keyboard were needed**: the work is declared, not
lost. `LEZIONI.md` §2.4 — whatever changes what is seen stays behind a switch until
someone has looked at it.

---

### 5-bis.7 ✅ The layout is renegotiated at attach and at reattach, like the resolution

*8 Aug 2026. «Per le tastiere vale il discorso delle risoluzioni: alla creazione della
sessione o re-attach viene rinegoziata anche la tastiera».*

Same shape as §5.0 — the client declares, the session adapts — but **with two differences that
play in our favour**:

1. **it costs nothing visible.** Changing the screen size reshuffles the user's
   windows and on KWin < 6.8 it cannot be done at all; changing the layout moves nothing,
   does not restart the capture, is not seen;
2. **and if it failed, the degradation is soft.** Thanks to 5-bis.6 a stale layout never
   produces wrong characters — at most it makes a couple of accents unreachable. A
   stale size, instead, is seen for the whole session.

`[?]` **To be measured, two things, and neither is urgent:** whether the layout change in a live
session succeeds on all four desktops (birth is certain, the hot change is not); and whether
it is worth giving the session **several layouts together** — the system accepts up to four
— to cover the case of someone moving from an Italian phone to an American laptop, which I
suspect is rare but nobody has measured it.

> ### ⛔⛔ THIS DECISION WAS NEVER IMPLEMENTED — `[M]` 16 Aug 2026, sub-phase 6.2
>
> *Measured on the live product, user `provat6`, port 7721, with a witness inside the graphical
> session: the layout the client declares in `ATTACCA` is **validated**
> (`rcp.c:2013-2027`), **written in the log** (`rcp.c` · `tratta_attacca()`), **and it ends there**. It never reaches
> the keyboard.*
>
> | scene | expected if the decision were implemented | `[M]` measured |
> |---|---|---|
> | session `it`, reattach declaring **`us`** | `è` and `ò` unreachable | **`aèò\@a`** — identical to `it` |
> | session `it`, reattach declaring **`de`** | `z` and `y` swapped | **`it` behaviour** |
> | the **session** goes `it`→`de` with the stage live | keymap reread, `azy\a` | ⭐ **`azy\a`** — this piece works: `ricambi_tastiera` 0→1, keymap fingerprint `8315b8d9`→`d1c54543`, «[German]» |
>
> ⇒ ⭐ **What holds is the hard half**: when the layout **of the session** changes,
> Mutter destroys and recreates the keyboard device and `tastiera.c` rereads the new keymap — the
> letters come out right. ⛔ **What is missing is the easy half**: nobody takes the layout
> *of the client* and gives it to the session. `input.c` · `leggi_regione()` passes `NULL` where the negotiated one should go, and the
> `RIPIEGO DICHIARATO` line of `tastiera.c` · `tastiera_apri_da_keymap()` **does not appear in any round** — that is, whoever looked for
> that line in the log would conclude *«they always match»*, which is different from *«I did not
> look»*.
>
> ### ✅ And on 16 Aug 2026 the user CONFIRMED it, put in front of the three routes
>
> *They were put to him as the scene that is lived — «you connect from a PC with a keyboard different from
> the session's: who decides?» — with the three possible answers: **the session rules** (and
> the promise of `SPECIFICHE.md` §7.3 is corrected), **the client rules** (and the server applies it),
> **the user chooses** with an item in the page. ⇒ He chose the second: **the client rules**.*
>
> ⇒ The decision of 8 Aug **stays standing and is implemented now**, in phase 6.
>
> ⚠ **And the price declared before the choice, which stays a price**: the page **cannot know**
> the physical layout of the keyboard of whoever is looking at it — it guesses it from the browser's interface
> language (`src/pagina.html:2585-2624`, `[?]` declared there by the code itself), and outside the
> known languages **it falls back on `us`**. ⇒ Applying that name to the session changes the real keyboard on
> a **clue**. ⭐ The damage stays soft by §5-bis.6 — letters travel as letters, so
> at most the **shortcuts** and some accent move — ⛔ but the third route (the user
> chooses) stays the real cure of the defect, and the page's code already names it as such.

### 5-bis.8 🔸 Physical mouse and keyboard connected to the phone

*Question asked by the user on 9 Aug. The answer is that the design already chosen absorbs them
both, and in one case simplifies it.*

**The mouse.** Android offers two modes: the normal one shows **the system cursor** and
delivers positions — useless for us, because you would see **two pointers**. The right one
is **Pointer Capture**: the client declares it handles it itself, Android's cursor disappears, and
**movements** arrive plus buttons and wheel.

⭐ And there it closes by itself: **those movements move the same pointer the finger moves.**
A single arrow, two ways of pushing it; you unplug the mouse and carry on with the finger without anything
changing. It is the dividend of 5-bis.1 — having the pointer at home, it does not matter where
the push comes from.

⛔ **And from here the correction to 5-bis.5.** I had put the «relative pointer» among the things the
protocol must carry, **justifying it with Pointer Capture**: it is wrong. If the pointer is
drawn by the client, it is the client that does the arithmetic, and on the wire only the
**position** keeps travelling. One path fewer.

`[?]` Relative will be needed if anything for a different reason — remote applications that
**capture** the pointer (a 3D program, a game) — and that case is signalled by the **server**,
not the client. To be taken up again if and when it shows up.

🔸 **Acceleration is applied by the client**, not the server: it is adjusted where the hand is and it is the
same for any session. Applied by both it would add up, and the pointer
would become unpredictable.

**The keyboard.** Android handles it and delivers **the character** anyway, applying the
layout set in its preferences: the rule of 5-bis.6 holds identically, and it does not matter
whether the keyboard is drawn or made of plastic.

---

## 5-ter. The clipboard

### 5-ter.1 ✅ Text only, in both directions

*9 Aug 2026. «Per la clipboard ho idea precisa: solo testo». «Clipboard bi-direzionale. Dal
server al client e viceversa».*

**Text only**: no images, no files, no rich formats.

**In both directions**: you copy on the remote desktop and paste on the device in your hand, and
vice versa. ⚠ It corrects `SPECIFICHE.md` line 28, which said «**server-client** text clipboard»
and read in one direction only — while the client → server direction (I copy an address on the
phone, I paste it in the remote browser) is the more used of the two.

**Why it is the right choice and not a renunciation**, written so that nobody reopens it out of
distraction: text covers 95 % of uses, costs a handful of bytes, and has no
negotiation — a string is a string. Images instead open a whole box:
which formats, who converts, and above all **who pays the bandwidth** when you copy a screenshot
of 8 MB over a mobile link we are struggling to keep at 480p (§3.1).

### 5-ter.2 🔸 The code is already there, and covers three desktops out of four with a single file

Among the things that survive the death of RDP, the clipboard is the most intact: only the
RDP channel that carried it dies, not the way of talking to the desktop.

| | Lines | Covers |
|---|---|---|
| `fondamenta/remotix-c/src/appunti_wlr.c` | 796 | **KDE, XFCE and LXQt together** — same protocol (`zwlr_data_control_manager_v1`), and `STUDI.md` §xfce §8 gives it as working as it is |
| `fondamenta/remotix-c/src/appunti_mutter.c` | 450 | GNOME, which has a way of its own |

### 5-ter.3 🔸 Whom the clipboard belongs to changes per desktop, and one trap is already defused

`LEZIONI.md` §3, question 14 — *«whose clipboard is it?»*:

| | |
|---|---|
| **GNOME** | ⚠ **here too the compositor's** — see the correction below: it is `MetaSelection`; only **the door** belongs to the remote session (`EnableClipboard` on the RemoteDesktop object) |
| **KDE, wlroots** | the **compositor's**: no permission, and it is there even if REMOTIX is not |

> ⛔ **Corrected on 9 Aug 2026**, reading `STUDI.md` §gnome §10, which had already written it on the 8th and which
> nobody had carried over here. It said: *«the remote session's: it sits on the RemoteDesktop object, it is
> switched on with `EnableClipboard`, and without a session it does not exist»*. `[R]` The first two half-sentences
> describe the **door**, not the ownership; the last is **false**: Mutter's X11 bridge is
> unconditional in both directions, without a single check on focus.
>
> ⭐ **And the consequence is a gift for phase 7**: `xclip` works on GNOME **without** a session of
> ours, so the clipboard bench can use it as an independent side — instead of making two pieces of ours
> talk to each other, which is what `PIANO.md` §0.4 calls confirming nothing.
>
> ⚠ **Three Mutter traps, all `[R]` in `STUDI.md` §gnome §10**, which whoever writes phase 7 reads there and
> not here: `DisableClipboard` is **one-way** (afterwards, the announcements never come back — it is never
> called); the signature of `mime-types` is **asymmetric** between input and output, and whoever reads with the
> wrong type gets `NULL` **without an error**; and the internal clipboard manager keeps **a
> single MIME type**.

⚠ **The GNOME trap, and why it no longer touches us**: *«gnome-shell clears the clipboard at every
screen lock: it snatches the ownership from us in silence»* (`STUDI.md` §gnome). With §4.3 — the lock is
ours and the desktops' one stays off — the case does not arise. **But it comes back the day
someone put the desktop's lock back**, and it is one more reason why that decision must be
reread and not taken for granted.

### 5-ter.4 ✅ «Formatted text» was requested, and the decision of 9 Aug HOLDS

*17 Aug 2026, at the opening of the clipboard work.* The request said *«la copia
server↔client di **testo formattato**»*. ⛔ It contradicted §5-ter.1, which is **the user's word of 9
Aug**: *«solo testo»*, no rich formats.

**Asked before writing a line, and the user chose «solo testo semplice».** ⇒ §5-ter.1 is not
touched.

⚠ **And the cost of the other route was protocol-level, not effort**: `RCP.md` §7.4 built the three
messages **without any field declaring the type**, with the reason written beside it — *«it does not exist
because there is nothing to choose»*. HTML would need that field, and `RCP.md` §9 forbids
adding fields to existing messages within a major version: **the window has been closed since 10
Aug 2026**. ⇒ It would have been **RCP/2**, plus four documents to correct.

⭐ And v1 did carry HTML (`fondamenta/remotix-c/src/scambio.c:56`, the registered format «HTML Format»):
it is not an impossible thing, it is a thing **left out on purpose**.

### 5-ter.5 🔸 The race between `Ctrl+V` and the announcement: the request WAITS, and keys are not delayed

*17 Aug 2026, while writing the channel.* `SPECIFICHE.md` §9 names the race and rejects the reference's
cure with a number: Xpra delays **every keystroke by 100 ms**, and for us *«that is twice the
delay cap»*.

**The race**: the user types `Ctrl+V` in the browser; the keys and the clipboard announcement leave
together on two different channels, and the desktop — having received the `Ctrl+V` — asks for the text **immediately**.
⛔ The first paste of every new text would come back empty, and the second would work.

⭐ **The replacement**: the paste request **is queued** instead of coming back empty, and the
question to the client leaves when the announcement arrives. It costs zero, and **does not touch a single key**.

⏳ Reasoned, **not measured**: the scene that proves it is the user's.

### 5-ter.6 🔸 Two timeouts, and they are two because the debts are two

| where | how much | which debt it pays |
|---|---|---|
| ⛔ **in the child** | **4 s** | the debt towards **Mutter**: a `SelectionTransfer` without an answer leaves the pasting application hanging indefinitely, and the user sees **a frozen desktop** |
| ⚠ **in the parent** | **8 s** | that the **channel** does not stay blocked: without it, a client that fails to answer once queues up all the following pastes |

⭐ **And the timeout towards Mutter lives in the CHILD, not in the parent**: the parent may have no client
(the session survives the client — I4), the client may disappear, the parent itself may die. The
debt towards the compositor stays with whoever holds the session.

⚠ The two numbers are different **on purpose**: if they coincided they would expire together, and a text arriving at
the right millisecond would no longer find anyone to serve on either side.

### 5-ter.7 🔸 One stream per MESSAGE, not per transfer — where §2.5 allowed two readings

`RCP.md` §2.5 says *«one stream **per transfer**»*. ⚠ A transfer on the server side is made of two
messages far apart in time: the announcement now, the text **if and when** someone asks.

⇒ **One stream per message**, because people copy much more often than they paste: keeping a stream open
between the two would mean keeping it open **forever** in most cases, and §2.5 grants the server a finite
number of streams.

⭐ It can be done because what ties the messages of a transfer together **is not the stream**: it is the
`trasferimento` field (finding R1.11). ⭐ And the test client, reading **only `RCP.md`**, made the same
choice — the line is ambiguous, but the ambiguity does not bite.

### 5-ter.8 ✅ Like a local session — and the price Firefox imposes

*21 Aug 2026, from the user, after the cure for pasting with the mouse:*

> *«Voglio che sia chiara una cosa: l'esperienza dell'utente con REMOTIX dev'essere quanto più
> vicina possibile all'esperienza con una sessione grafica locale. Questo vale anche per la gestione
> della clipboard: niente trucchi, pulsanti strani o soluzioni tecniche che si allontanino da questa
> direttiva, quindi ctrl+v o usare il mouse per incollare i contenuti dev'essere assolutamente
> allineata al comportamento reale.»*

⛔ **It is a directive, not a preference**, and it holds beyond the clipboard: where a cure requires the
user to learn something, the cure is wrong.

⇒ Three things follow from it, all measured and all in force:

1. ⭐ **Pasting with the mouse works**, that is right button inside the remote desktop and the «Incolla» item
   of the remote application's menu. `[M]` `banchi/07-b56`, 3 pastes out of 3 per engine.
2. ⭐ **Connecting does not clear the desktop's clipboard.** `[M]` Before, it cleared it: `wl-paste`
   said `TESTO-CHE-ERA-GIA-NEL-DESKTOP` before and `«»` after.
3. ⭐ **There is no button of ours**, no switch, nothing to explain.

### 5-ter.9 🔸 And on Firefox pasting with the mouse costs **one more click** — accepted

*21 Aug 2026: «ok, va bene così».*

⛔ When you paste with the remote desktop's menu, no event is born on the page: that menu is painted in
the video and the one pasting is an application at the other end of the wire. ⇒ The only way the page has
of knowing what you copied is **reading the clipboard at that instant**, and there the browser decides:

| | Chrome | Firefox |
|---|---|---|
| what it asks | the clipboard permission **only once**, as for the microphone | ⛔ its little **«Incolla» button, every time** — `[M]` even when pasting the same text again |

⚠ **That little button is Firefox's, not ours**, and it cannot be removed from the page: the only thing
that turns it off is a testing preference, which does not go into a product.

⇒ **It is accepted and declared**, instead of giving up pasting with the mouse on Firefox. ⏳ And the only
route that would really remove it stays open — **a Firefox add-on** — to be decided at phase 13, when it
is decided how REMOTIX is installed. ⚠ It is not done earlier: it changes *what gets installed*, and
REMOTIX would stop being «open the browser and go».

⭐ **`Ctrl+V` costs nothing on any engine**, and it is the route most people will use.

---

---

## 5-quater. Audio

*Opened on 17 Aug 2026. ⛔ Until that day **this chapter did not exist**: the audio choices were scattered
among `SPECIFICHE.md` §10, `RCP.md` §5.3 and invariant I5 — that is in three places and in none. The
phase document had declared it at the opening.*

### 5-quater.1 🔸 Opus goes through `libavcodec`, not through `libopus`

`[M]` 17 Aug 2026: `libavcodec` 61.19.101 on the test machine **is already linked to `libopus.so.0`** and
declares the `libopus` encoder. ⇒ The `Makefile` **does not change** and no package is added to **two**
build environments (the laptop's container and the server's `devroot`), where `opus.pc` is not present.

⚠ **The price, declared**: one `AVPacket` per block, that is 50 allocations per second. It is less than
the price of a dependency to install twice and remember forever (`LEZIONI.md` §2.5-bis).

### 5-quater.2 🔸 Opus's bitrate: **96 kbit/s**

Derived, not decided by the user. It is the bandwidth at which Opus is transparent for music according to
its documentation `[S]`; `[M]` a 20 ms block measures **241-439 bytes**, which fits in the datagram with a
wide margin. ⏳ **To be reviewed on the day someone judges the quality**, not before.

### 5-quater.3 🔸 The playback cushion: **250 ms**, and it is not a free number

⛔ **It was 60 ms, and it was wrong**: chosen looking at the cap of the **video** (50 ms, `CODER.md`
§1-bis) — that is measuring the audio with the yardstick of something else. The reference
(`gnome-remote-desktop`) keeps **300** (`STUDI.md` §gnome §11).

**The reason why 60 does not hold**: the video is decoded and painted **on the same thread** that schedules
the audio. When that work exceeds the cushion the playback has already emptied, and **every re-arm is a
hole**.

⚠ **The price is declared**: 250 ms between what you see and what you hear. ⛔ And if one day it were
annoying, **the cure is not to tighten it**: it is to take the audio off the main thread with an
`AudioWorklet`. ⏳ The user said *«risolto»*, not *«e il ritardo va bene»*: that judgement is missing.

### 5-quater.4 ✅ ⭐⭐ A block that does not leave is POSTPONED, not thrown away — and the queue decides

*17 Aug 2026, after the user said «fa schifo» seven times on a green bench.*

`RCP.md` §6.3 says *«no retransmission, no reordering»*, ⛔ **and it does not say «thrown away at the first
refusal»**: that was a reading of mine, and it was worth **50 %** of the audio.

| | |
|---|---|
| ⛔ **what is NOT done** | throwing away a block because the pacer said «not now»: that block leaves a few hundred microseconds later, and throwing it away is **a guaranteed hole** |
| ⭐ **what decides** | **the queue**: eight blocks = 160 ms of Opus. Beyond those the oldest is no longer of use to anyone, and **that is where** §6.3 bites |
| ⭐ **and several blocks are sent per packet** | a packet is **1452 bytes**, an Opus block **230**: six fit. ⛔ Sending one per write pass, with ~25 passes per second against 50 blocks produced, lost **exactly half** |

⚠ **And the shape of the number was the clue**: *exactly* half. A network loss is never exactly half; an
arithmetic is (`LEZIONI.md` §2.7).

### 5-quater.5 ✅ ⛔ Real-time priority is granted **by the unit**, and the program VERIFIES it

**v1's R26** (`~/Documenti/REMOTIX/REFERENCE.md`, `[M]` 5 Aug 2026): a process with `RLIMIT_RTPRIO` at
zero **cannot ask for `SCHED_FIFO`**. PipeWire tries, is denied, and its data loop collects the samples at
normal priority ⛔ **while in the same process the video encoder takes a core**. The symptom is not an
error: it is **audio that crackles when the desktop works**, invisible to every check on the wire.

⇒ `LimitRTPRIO=20` and `LimitNICE=-11` **in the systemd unit**. ⭐ And since the code cannot give itself an
rlimit, the child **reads it and writes a line ⛔ if it is missing**: it is invariant **I7** applied where
the protection *must* live in a configuration — a lost line shows instead of staying silent.

---

## 6. The inherited code

### 6.1 ✅ v1's heritage is here, and versioned

*8 Aug 2026.* Brought over from the development server, where it lived without versioning and without a
second copy. Verified by SHA-256 fingerprint, 103 files out of 103.

| | |
|---|---|
| `fondamenta/remotix-c/` | **17,481 lines of C**, 26 modules |
| `fondamenta/remotix-c/prove/` | **4,563 lines of benches**, one script per phase |
| `fondamenta/banchi/` | **262 files** of the investigation on phase 11, `misura-cattura.c` included |
| `fondamenta/remotix-rust/` | 7,163 lines, IronRDP branch closed on 3 Aug |
| `fondamenta/documenti/` | PIANO, SPECIFICA, REFERENCE, protocollo-rdp, client-android, xrdp |
| `fondamenta/calibrazione/` | the three scenes of the calibration of 1 Aug |

> ### ⛔⛔ AND THIS TABLE LEFT OUT THE ONLY TWO PARTS OF `fondamenta/` THAT ARE ALIVE — *corrected on 16 Aug 2026*
>
> *Found by surveying `fondamenta/` file by file, at the user's request. The table above has **six
> rows** and I leave them as they were — ⛔ but `fondamenta/banco/` and `fondamenta/strumenti/` are not
> there, and they are **the project's current equipment**. Whoever read this paragraph to know what
> `fondamenta/` is took home that it was all archive. It is not.*
>
> ## The real map: what is **alive**, what is **archive**, what is of no use to anyone
>
> *`[M]` 16 Aug 2026, citations counted from the ten documents, from `src/`, from `banchi/` and from `web/`.*
>
> | | files | MB | citations | |
> |---|---|---|---|---|
> | ⭐⭐ **`fondamenta/banco/`** | 13 | 0.2 | **enter.sh: 193** | **ALIVE, and it holds everything up**: `enter.sh` is the way one enters the test machine. With `provision.sh`, `provision-server.sh`, `gpu-udev.sh` (applied on 15 Aug, §4.6-ter), `server.sh`, `vm.sh` |
> | ⭐⭐ **`fondamenta/strumenti/sshpw.py`** | 1 | 0.01 | **81** | **ALIVE**: dozens of V2 benches call it |
> | ⭐ `fondamenta/remotix-c/` | 70 | 1.0 | 37 files out of 70 | **archive with value**: it is the mine of reuse — `kwin.c` (822 lines) and `appunti_wlr.c` (796) are in the plan of phases 11 and 12 |
> | ⭐ `fondamenta/banchi/banco-compositori/` | 74 | 0.7 | 4 | **archive with value**: the measurements of KWin, wlroots and Mutter, which phases 11 and 12 will redo |
> | ⭐ `fondamenta/documenti/` | 6 | 0.5 | all six | **archive with value**: the history of the price paid (`LEZIONI.md` §0) |
> | ⚠ `fondamenta/calibrazione/` | 10 | ⛔ **90.2** | the folder 1 time, the files **0** | the three scenes at three resolutions — **96 % of the project's weight**. See the box below |
> | ⚠ `fondamenta/remotix-rust/` | 23 | 0.4 | **1**, and it is this table | the IronRDP branch, **closed on 3 Aug**. The lesson is written here; the code does not add to it |
> | ⛔ `fondamenta/banchi/` *(rest)* | ~190 | 4.1 | 17 | 86 `.log`, 8 `.png`, 10 `.tgz/.gz/.xz` archives, 2 `.so`, the outcomes of runs of 1-8 Aug |
> | ⛔ ~~`fondamenta/tracce/`~~ | 8 | 0.4 | **0** | `.h264` streams and **RDP** provisioning logs — and RDP died with §1.6. ✅ **Removed on 16 Aug 2026** |
> | ⛔ ~~`fondamenta/banco/*.prima*`, `*.rust`~~ | 4 | 0.05 | **0** | **hand copies** of `enter.sh`, `provision.sh`, `provision-server.sh`, `vm.sh`, made before a change. ⚠ A backup copy next to the original is a trap, not a safety net: the safety net is git. ✅ **Removed on 16 Aug 2026** |
>
> ## ⛔⛔ And the thing that changes the reasoning about the 90 MB: **removing them recovers nothing**
>
> `[M]` the `.git` weighs **94.29 MiB** and the ten `.mp4` are **90.2** of it — that is **96 %**. They are
> ten distinct files, entered once and never touched again.
>
> ⛔ **But `git rm` does not remove them from history**: they would stay in the `.git` and the weight would
> not change by one byte. The only route that really recovers is **rewriting history**, and it costs a
> price this project cannot pay:
>
> ⛔⛔ **fifteen commit hashes are cited in the documents as recovery recipes** — `0c85e5c` for the 94
> agent reports, `47bd41c` for the pruned diary of the `README`, and thirteen more in the phase minutes. A
> rewrite changes **all** of them, and every recipe would point to nothing.
>
> ⇒ ⭐ **And there is no need to pay it**: `[M]` the repository **has no remote**, it lives only on this
> disk. Ninety-four megabytes sitting in a folder cost nothing to anyone.
>
> ⇒ **Decision: the `.mp4` stay.** ⚠ And it is written here so that nobody reopens the question by
> counting the megabytes again without counting the hashes.
>
> ⭐ **With a fact that matters for phase 9**: the scenes **can be regenerated**,
> `fondamenta/banco/calibrazione.sh` produces them with `ffmpeg` at the three native resolutions. ⚠ **But
> not byte for byte**: a different `ffmpeg` gives a different file, and the comparison with the numbers of
> 1 Aug would break. ⇒ Whoever at phase 9 wanted to compare with v1's calibration **should use these
> files**, not the ones they would regenerate.

`LEZIONI.md` has been promoted to V2's level: it is the foundation of `CODER.md` and `REVIEWER.md`, which
cite it 29 times across 20 sections.

### 6.2 🔸 About 79 % of the C survives the death of RDP

Measured by counting the occurrences of `freerdp|winpr|rdpContext|RDPGFX|rdpSettings` per file:
7,442 **clean** lines (`palco`, `cattura`, `kwin`, `mutter`, `appunti_wlr`, `superficie`,
`sentinella`, `autenticazione`…), 4,570 with superficial contamination, 1,781 medium, and
**3,688 that die** (`server.c`, 134 occurrences, and `rete.c` which must be replaced by QUIC).

⚠ It is a first-level measurement: counting the `#include` says who *touches* FreeRDP, not who
*depends* on RDP. `scambio.c` and `codificatore.c` must be read before taking the 79 % as good.

### 6.3 ✅ The server is written in C

*8 Aug 2026. «Confermo il C».*

⚠ **It is not an inheritance: it is a new decision that repeats the old one.** v1's constraint
(`fondamenta/documenti/SPECIFICA.md` §8-bis) had a single reason — *«gnome-remote-desktop stops being a
reference to draw inspiration from and becomes a reference to draw code from»* — and **that reason died
with RDP**: there is nothing left to transplant, because nobody wrote RCP before us. The question was
reopened with eyes open and closed again for a different reason.

**The new reason is the count of §6.2**: about 14,000 lines survive, with their benches already
calibrated. The QUIC piece is worth perhaps 2,000. Rewriting fourteen thousand measured lines to gain the
ergonomics of two thousand is a terrible trade — and it is also `LEZIONI.md` §10 in action, because among
the things that would be thrown away there are **4,563 lines of benches**, and this project never died on
the code: it died on the measurements.

**What this decision does NOT decide:** the clients. The Android one is Kotlin anyway, because of
MediaCodec. The Linux one is open — if it is in C it can share `librcp` with the server, which is an
argument in favour but not a conclusion.

### 6.4 🔸 QUIC via `ngtcp2` + `nghttp3` — **closed on 10 Aug 2026, with a bench**

> ⭐ **The decision, in three lines.** Of the four candidates **one** remains: `ngtcp2`+`nghttp3`.
> `lsquic` left because it **demands SNI** and the product is used by address; `libwtf` was last in line
> (second QUIC stack, a licence that contradicts itself); and ⛔ **`quiche`, used from C, cannot declare
> WebTransport** — the measurement is below. `ngtcp2` on the other hand holds: **two real browsers open
> the session**, and the missing layer costs **373 lines of code** of ours (`[M]` 10 Aug 2026, 16:30 —
> the breakdown and the succession of measurements are in the box «How many lines are ours, and at what
> time» further down).
>
> ⚠ **The price, declared**: those lines include the **rewriting of the SETTINGS frame that nghttp3 is
> writing**, because its public API does not allow announcing an arbitrary setting. It is glue that
> depends on the shape of a library's bytes, not on a promise of it: ⛔ **it must be retested at every
> nghttp3 update**, and the bench that retests it exists.
>
> 🔸 *Derived, correctable without discussion: if one day `quiche` exposes `set_additional_settings` in
> the FFI and Debian has `rustc` ≥ 1.88, the choice reopens — and the two benches to redo the comparison
> are written.*

*The text below is the chronicle, and it is read in order: the decision was born as «`quiche`» on paper,
and ended at the opposite with three measurements.*

It was the only serious argument in favour of Rust, and it is solved with a library instead of with a
language: Cloudflare's **`quiche`** has a **C API**, **BSD-2** licence, and has been in production for
years. One takes finished QUIC without stitching ngtcp2 by hand and without touching the licence freedom
(§7.6).

The pure C alternative is `ngtcp2` (MIT), which however requires bringing your own TLS and assembling
more pieces. **To be confirmed when the transport is opened**, not before: it is the kind of choice made
with a bench in front, not on paper.

> ⛔ **The criterion changed on 9 Aug 2026 with §1.6, and must be rewritten before choosing.** It is no
> longer enough for the library to speak QUIC: the client is a browser, so the server must carry
> **HTTP/3 and WebTransport**, plus a **TCP** listener for the first load of the page (`Alt-Svc`). The
> question is no longer «which QUIC», it is **«which of the two gets as far as WebTransport on the server
> side, and how much glue is left to us»**.
>
> `[M]` 9 Aug, on the iron: Trixie has `libngtcp2-dev` 1.11 **and** `libnghttp3-dev` 1.8 as packages,
> `cargo`/`rustc` 1.85 to compile `quiche`, and `python3-aioquic` 1.2 — which serves the test client, not
> the server.
>
> ⚠ **And this choice has become critical instead of secondary**: before, it decided how many lines of
> glue to write, now it decides **whether the product exists**. It must be closed with the browser probe
> in front, not after.

> ### ⭐ The survey of the night of 9 Aug — the candidates were not two, and neither of the two original ones carries WebTransport
>
> *Done before writing a line of B2, as point 0 of the recipe (`LEZIONI.md` §9): **who, in the world,
> already does this thing?** Everything that follows is `[S]` and `[R]` — **read, not measured**. The
> measurement is B2, and it is needed precisely because these lines are not enough.*
>
> | Candidate | Language and API | WebTransport **server side** | What glue is left to us |
> |---|---|---|---|
> | **`quiche`** | Rust with **C API** | ⛔ **no** — but it has `h3::Config::enable_extended_connect()` (`SETTINGS_ENABLE_CONNECT_PROTOCOL`) `[R]` and complete QUIC datagrams (`dgram_send`/`dgram_recv`) `[R]` | **the whole WebTransport layer** |
> | **`ngtcp2` + `nghttp3`** | **C** | ⛔ **no** — but nghttp3 implements **RFC 9220** (HTTP/3's extended CONNECT) `[S]` **and** can send and receive `SETTINGS_H3_DATAGRAM` with the **Capsule Protocol** `[S]` | the WebTransport layer, ⭐ **with the most complete foundations of the four** |
> | ⭐ **`lsquic`** (LiteSpeed) | **C** | ⚠ **partly** — see the box below: the flag is there, the public API is much thinner than the name | **less than the other two, but not «little»** |
> | **`libwtf`** | C, but **on MsQuic** | ⭐ yes, negotiates draft-15/07/02 `[S]` | little, ⚠ but it brings in **a second QUIC stack** |
> | ~~`web-transport-quiche`~~ | ⛔ **pure Rust, no C API** | yes | ⛔ **excluded**: the server is in C (§6.3) |
>
> ⛔ **The fact that reorders everything**: *«which of the two gets as far as WebTransport»* had a single
> answer — **neither of the two**. The two original candidates give the **foundations** (extended CONNECT,
> datagrams, capsules) and not the layer above: the session settings, the unidirectional stream type, the
> signal on the bidirectional ones, the datagram prefix, the close capsule. The real question was always
> the second — **how much glue** — and now it has a listable shape.
>
> ⚠ **And the two newcomers must be looked at with suspicion, not with relief:**
>
> | | |
> |---|---|
> | **`lsquic`** | ⛔ the feature is **off by default** and **does not appear in the documentation of 4.9.3** `[R]`. «Implemented but off and undocumented» is the signature of a piece that **nobody exercises**: it must be tested, not believed |
> | **`libwtf`** | ⚠ 70 stars, 51 commits, one author — and ⛔ **the licence contradicts itself**: the README says MIT, the footer Apache-2.0. On a library that would enter the heart of the product it is a defect in itself (§7.6) |
>
> ### ⛔ And `lsquic` is the textbook case of E1: the flag was necessary, not sufficient
>
> *Read the public header `include/lsquic.h` instead of trusting the `CMakeLists.txt`.* Behind
> `LSQUIC_WEBTRANSPORT_SERVER_SUPPORT` there is **everything that follows, and nothing else** `[R]`:
>
> | | |
> |---|---|
> | two settings | `es_webtransport_server`, `es_max_webtransport_server_streams` |
> | four functions, **all of classification** | `lsquic_stream_set_webtransport_session` · `..._is_webtransport_session` · `..._is_webtransport_client_bidi_stream` · `..._get_webtransport_session_stream_id` |
>
> ⛔ **There is no API to establish a session, to open a WebTransport stream, to send a WebTransport
> datagram.** *«The `CMakeLists` has a flag called `WEBTRANSPORT_SERVER_SUPPORT`»* ⇒ *«lsquic does
> WebTransport»* is **exactly** the shape **E1**, the same that killed v1 and that `STUDI.md` §web §9
> point 1 had already seen reappear disguised as an API (`prefer-hardware`). ⭐ **Third time in three
> days, and this time reading stopped it.**
>
> ⚠ **What those four functions imply, however, is more than what they say**: to answer *«this stream
> belongs to WebTransport session number N»* lsquic **must** already read the headers of the WT streams
> and associate them — which is the boring part. It is a clue in favour, not a proof: **it is measured**.
>
> ### ⭐ And the first measurement is there — `[M]` 9 Aug 2026, `banchi/01-b2-costruisci.sh`
>
> | What | Expected | Measured |
> |---|---|---|
> | BoringSSL compiles in the `devroot` | yes | ✅ yes |
> | `lsquic` **v4.9.3** compiles with `-DLSQUIC_WEBTRANSPORT=ON` | yes | ✅ yes, and the define appears in the `FLAGS` of `build.ninja` |
> | ⛔ **the flag produced the symbols** | 4 out of 4 | ⭐ **4 out of 4** |
>
> ⭐ **And the code is not a stump**: `webtransport` appears in **six files** — `include/lsquic.h`,
> `lsquic_stream.c/.h`, `lsquic_engine.c`, `lsquic_full_conn_ietf.c`, `lsquic_hcso_writer.c` `[R]`.
> That is, it touches the engine, the streams, the IETF connection **and the writer of the HTTP/3 control
> stream** — where the settings live. It is an implementation spread in the right places.
>
> ⛔ **But «the symbols are there» is not «the session opens»**: it is the next step of E1, and the
> measurement that counts remains **a real browser opening a session**.
>
> ### ⛔ And reading beyond the symbols: `lsquic` speaks draft **02**, today's browsers do not
>
> *`[R]` `⟨lsquic⟩ src/liblsquic/lsquic_hcso_writer.c`, where the server writes the settings on the HTTP/3
> control stream.* Here are **all** the ones it emits:
>
> | Setting | Value | |
> |---|---|---|
> | `SETTINGS_ENABLE_WEBTRANSPORT` | `0x2b603742` | ⛔ **it is from draft 02** |
> | `WEBTRANSPORT_MAX_SESSIONS` | `0x2b603743` | ⛔ **ditto** |
> | `H3_DATAGRAM_ENABLED` | `0x33` | ✅ current |
> | `SETTINGS_ENABLE_CONNECT_PROTOCOL` | `0x08` | ✅ current |
>
> ⛔ **And it never emits `SETTINGS_WT_MAX_SESSIONS` (`0xc671706a`)**, which is the setting with which a
> server declares WebTransport from draft 07 on — that is the one Chrome, Firefox and Safari look for
> today.
>
> ⭐ **From which a falsifiable prediction, written BEFORE the measurement** (`LEZIONI.md` §1.11: for every
> indirect test one writes what the opposite would look like):
>
> | | |
> |---|---|
> | **the prediction** | a browser of today **will not establish** the session with `lsquic`: it does not see the declaration it looks for, and the extended `CONNECT` is refused |
> | ⭐ **what the opposite would look like** | the session opens anyway ⇒ **either** browsers still accept the settings of draft 02, **or** I misread this file. In both cases the prediction is wrong and why must be written down |
> | **how it is falsified** | it is the B2 measurement: a real browser against a minimal server. **It costs what writing that server costs** |
>
> ⚠ **Which brings `lsquic` back to the end of the line instead of the head**, and not for the defect
> itself: «implemented, off by default, undocumented, **and stuck at a draft three versions ago**» is the
> portrait of a piece that **nobody exercises**. `CODER.md` §4.1 says to depend instead of rewriting —
> but depending on code nobody exercises is rewriting it **with a delay**.
>
> ### ⛔⭐ `lsquic` is out, and for a reason nobody had foreseen — `[M]` 9 Aug 2026
>
> *The glue written (`banchi/01-b2-lsquic-wt.c`, **333 lines**, of which 236 of code), compiled and put
> listening. The test client connected, and the server logged this:*
>
> ```
> handshake: for QUIC version 00000001, ALPN is h3
> handshake: SNI is not set, but is required in HTTP/3: fail certificate lookup
> handshake failed  ·  sending CONNECTION_CLOSE, error code: 336, reason: TLS alert 80
> ```
>
> `[R]` `lsquic_enc_sess_ietf.c:1326-1336`: in **HTTP/3 mode**, if the client sends no SNI, lsquic
> **fails the certificate lookup and closes**. There is a loophole — `esi_sni_bypass` — ⛔ **but it is
> inside `#ifndef NDEBUG`**, that is it exists only in debug builds.
>
> ⛔ **And this hits the product's primary case, not an edge case.** `SPECIFICHE.md` and §1.7 describe a
> server **without a domain**, which the user reaches by typing `https://<indirizzo>:7447` — that is
> **an IP address**. A client connecting to an IP **sends no SNI**: the TLS specification forbids literal
> addresses in that field. So:
>
> | | |
> |---|---|
> | ⛔ **`lsquic` cannot serve a certificate to whoever connects by address** | and it is the way REMOTIX is used |
> | ⚠ **the prediction about draft 02 stays OPEN** | it was neither confirmed nor refuted: **we never got there**. Writing it down as «I was right» would be confirming a prediction with a proof that speaks of something else |
> | ⭐ **and the model is not in question** | `aioquic`, on the same address and with the same certificate, serves **two browsers** without SNI. The defect is the library's, not the design's |
>
> ⭐ **From which a new criterion for this decision, which nobody had written because nobody imagined it**:
> the library **MUST serve a certificate without SNI**. It must be tested first on every candidate — it
> costs one connection, and here it eliminated a candidate after 333 lines.
>
> ⚠ *And the bench that produced this `4 su 4` **had first said `0 su 4`**, because of a defect of its own
> — `set -o pipefail` plus `grep -q`. The chronicle is in `FASI.md` §01-filo-nudo, «what did NOT work»,
> and it is the reason why this line carries the date and the script's name.*
>
> ⚠ **And a detail that counts as a smell**: the comment of `es_webtransport_server` says *«Enable
> datagram extension for http3 server»* — that is it **documents something else**. A field whose
> documentation speaks of something else is a field nobody has reread.

> ### ⭐⛔ `ngtcp2` passes the new criterion, and it is the first to be tested before the glue — `[M]` 10 Aug 2026
>
> *`banchi/01-b2-sni-ngtcp2.sh` (builds the target) · `01-b2-sonda-sni.py` (the probe) ·
> `01-b2-lancia-sni.sh` (conducts). The target is **their example server**, `bsslserver`, not a server
> of ours: a server of ours would be glue, that is the thing this test must come before writing.
> `ngtcp2` **16.11.0** + `nghttp3` **1.18.90**, on the same BoringSSL as `lsquic`.*
>
> **The prediction, written beforehand** (`LEZIONI.md` §1.11): *it passes*. `[R]` in **109 files** of
> `examples/` and **18** of `crypto/` there is **no** occurrence of `servername`, `SSL_get_servername`,
> `SSL_CTX_set_tlsext_servername_callback`, `select_certificate_cb` — with the positive controls
> answering (`SSL_CTX_use_certificate_chain_file` in 8 files, `alpn_select` in 6, `SSL_` in 10). Nobody
> looks up the certificate by name: it is tied to the `SSL_CTX` and always served. ⭐ **What the opposite
> would have looked like**: the handshake falling as on `lsquic`, and then the candidate would have left
> here instead of after the glue.
>
> | The measurement | Expected | Measured |
> |---|---|---|
> | ⭐ **without SNI on the wire** | the session is established | ⭐ **yes** |
> | ⛔ **and the certificate is THAT one** | the file's fingerprint | ⭐ **`35wqjGTOmKSj…` matches** — the handshake succeeding is not enough, the certificate is compared |
> | with SNI (`remotix.prova`), the control | ditto | ✅ yes |
>
> ⛔ **So the criterion is satisfied, and `ngtcp2` stays in the race with `quiche`.** The price is known:
> the WebTransport layer is all ours (extended CONNECT in 9 files, WebTransport in 0).
>
> ⚠ **And the first number of the «how much glue» column**: their example server weighs **7,041 lines**
> in **13** `.cc` **files** `[M]` — ⛔ **it is a ceiling, not an estimate**: it is their complete HTTP/3,
> with file handling, migration, retry. Ours will be less. The number that counts is that of the minimal
> server, and it will be counted when it exists.
>
> ### ⭐ And the diagnosis of `lsquic` closes, with the other half that was missing — `[M]` 10 Aug 2026
>
> On 9 Aug *«SNI is not set»* had been read in its log and it had been concluded — rightly — that it
> demands SNI. ⛔ **But «fails without» is not «succeeds with»**: until someone tests the second half,
> the diagnosis stays half done and the candidate is eliminated on half a proof. The two lines, from the
> same log and in the same run:
>
> | Leg | What `lsquic` says |
> |---|---|
> | without SNI | `SNI is not set, but is required in HTTP/3: fail certificate lookup` |
> | with SNI | ⭐ `looked up cert for remotix.prova` — **it finds the certificate** |
>
> ⛔ **The defect is SNI and nothing else: the elimination of 9 Aug holds, and now on a whole proof.**
>
> ⚠ **And one thing stays open, declared instead of rounded off**: with SNI the handshake falls all the
> same, but **further on and for another reason** — TLS alert **120**, `no suitable application
> protocol`, after the certificate was found. **It was not investigated**: it is not needed for this
> decision, and `lsquic` is out for a reason that does not depend on it. It is written down so that
> nobody discovers it afresh believing it is new.
>
> ⚠ **And the prediction about draft 02 stays OPEN even after this measurement**: not even this time did
> we get there — the connection with SNI dies before the HTTP/3 settings.

> ### ⭐ `quiche` passes the same criterion, and brings along a cost that has nothing to do with QUIC — `[M]` 10 Aug 2026
>
> *`banchi/01-b2-sni-quiche.sh` (`leggi`, then `costruisci`) · measured by the same conductor and the
> same probe as the other two, in the same run.*
>
> **The prediction, written before building** (`LEZIONI.md` §1.11), on **81 files** of 3 trees with the
> positive control answering (*«quiche»* in 33 files): `select_certificate_cb` in **0** files,
> `servername` in **1**. ⭐ And that one is a **reader**: `quiche/src/tls/mod.rs:510-526` exposes
> `server_name() -> Option<&str>` — which reaches C as `quiche_conn_server_name()` — that is it *says*
> what the peer sent, it does not *choose* anything. **It returns `Option`**: «no SNI» is a state the
> signature can represent, not an error. ⇒ **prediction: it passes**.
>
> | The measurement | Expected | Measured |
> |---|---|---|
> | ⭐ **without SNI on the wire** | the session is established | ⭐ **yes** |
> | ⛔ **and the certificate is THAT one** | the file's fingerprint | ⭐ **`35wqjGTOmKSj…` matches** |
> | with SNI (`remotix.prova`), the control | ditto | ✅ yes |
>
> ⛔ **So the SNI criterion no longer separates the two candidates**: `ngtcp2` and `quiche` both pass it,
> and the choice moves to what remains — **how much glue** and at what price.
>
> ### ⛔ And the price of `quiche` emerged before the measurement, and it is a toolchain
>
> | | |
> |---|---|
> | ⛔ **the latest version does not build** | `quiche` **0.29.3** demands **rustc 1.88**; Trixie has **1.85** `[M]`. It is not an opinion: cargo stops and does not compile |
> | **the latest that builds is 0.28.0** | the bench chooses it by itself, comparing the `rust-version` of each tag with the compiler present, ⭐ **and prints which and why** — the measurement holds for *that* version |
> | ⚠ **and not even 0.28.0 is enough on its own** | their repository is a `workspace`: `tokio-quiche`, `h3i`, `qlog-dancer` pull in `tonic`, `icu`, `time`, `image`, which demand up to 1.88. One builds **`-p quiche`**, that is the only package we would use |
> | ⛔ **the choice that follows from it, and must be made knowingly** | choosing `quiche` means choosing **either** to stay on 0.28.0 until Debian updates `rustc`, **or** to bring a Rust toolchain from outside the packages (`rustup`) into the product's build. `ngtcp2` does not pose the question: it is C, and Trixie has everything |
>
> ⚠ **This does not eliminate `quiche`**: it is a cost, not a defect, and it must be written **next to the
> choice** instead of being discovered by whoever builds the product a month from now.
>
> ### ⚠ The two numbers of «how much glue», and why they are NOT subtracted
>
> | Candidate | Their example | What it is |
> |---|---|---|
> | `ngtcp2`+`nghttp3` | **7,041 lines**, 13 `.cc` files | their **complete HTTP/3** in C++: files, migration, retry, qlog |
> | `quiche` | **614 lines**, 1 `.c` file | a **minimal** example in C, which however already does HTTP/3 |
>
> ⛔ **Comparing them like this would be E1**: they do not measure the same thing. What the comparison
> really says is that `quiche` **exposes HTTP/3 from its C API** and one gets there in 614 lines, while on
> `ngtcp2` HTTP/3 is assembled by `nghttp3` and the example that does it is the big one. ⭐ **The number
> that counts remains that of our minimal server**, and it will be counted when it exists — on both.
>
> ⚠ **And both still lack the same thing**: the **WebTransport** layer, which neither of the two carries
> (survey of 9 Aug, still valid).

> ### ⭐⭐ The minimal server on `ngtcp2` exists, and a real browser opens the session — `[M]` 10 Aug 2026
>
> *`banchi/01-b2-ngtcp2-wt-innesta.py` grafts the WebTransport layer into their example server;
> `01-b2-lancia-wt.sh` measures it with the test client; `01-b2-lancia-sonda.sh` measures it **from a
> browser**. The number of lines is not an estimate: it is `git diff` in their tree.*
>
> | What | Measured |
> |---|---|
> | ⭐ **the session opens from a REAL BROWSER** | **Chrome 151.0.0.0** and **Firefox 140.0**, both `APERTA` on `https://192.168.0.2:7447/rcp/1`, fingerprint published, **no warning**, and `"ciao"` comes back identical |
> | ⛔ **and the wrong path is REFUSED** | `/rcp/9` ⇒ **404**, as `RCP.md` §2.2 imposes with finding R1.24. It is the control that says *no*, and it is in the bench |
> | **the two parameters of §2.2** | `max_idle_timeout` **30,000 ms** and `max_datagram_frame_size` **65,536**, ⛔ **read from the peer** with `01-b2-sonda-trasporto.py` |
> | ⭐ **how many lines are OURS** | see the box «How many lines are ours, and at what time» below: this morning's measurement was **456 added / 329 of code**, and it was redone at 16:30 |
>
> > ⛔ *The first row was corrected on 10 Aug 2026, finding **R11.6**.* It said **«printed by the server
> > at startup»**, that is it carried the wrong provenance written next to the right number: it is the
> > server's **configuration** — what it *asked* of ngtcp2 — not what *arrived* at the peer. ⛔ **It is the
> > corollary of `LEZIONI.md` §1.9 point 5** — *a denominator is read where the thing happens* —
> > contradicted in the document that cites it, and `FASI.md` §01-filo-nudo declares it **the worst defect
> > of the day** (*«I violated it myself, that afternoon, on a measurement of mine»*). ⭐ The cure is not
> > to remove the number: it is to **take it from the right source**, and the right source already
> > existed — the transport probe read the same two values from the peer.
>
> ⛔ **And now it is known what «the layer is not there» consists of, because they are the three points
> the graft touches:**
>
> | | |
> |---|---|
> | **1. WebTransport cannot be announced** | `nghttp3_settings` has `enable_connect_protocol` and `h3_datagram` — the two that are in the RFCs — and the public API offers `submit_request/info/response/trailers/shutdown_notice`. ⛔ **No way to put an arbitrary setting** on the control stream, and `SETTINGS_WT_MAX_SESSIONS` is what browsers look for. nghttp3's `SETTINGS` is rewritten **while it writes it** |
> | **2. WebTransport streams must be taken away from nghttp3** | they begin with frame type `0x41` followed by the session number, and nghttp3 would read that number as a **length** |
> | **3. the return bytes have no route** | nghttp3 does not know those streams, so it will never put them among the vectors to write: the output queue is ours |
>
> ⚠ **None of the three is a defect of the two libraries**: they do HTTP/3, and WebTransport is not
> HTTP/3. It is exactly the price this decision wanted to know before choosing.
>
> ⚠ **And the two drafts really bite.** The server sends **both** declarations — `0x2b603742` (draft 02)
> and `0xc671706a` (draft 07+) — because `aioquic` 1.2, **our test client**, implements **02** `[R]`
> `h3/connection.py:90`, and browsers look for 07. ⛔ A server that sent only one would work with half of
> our tools, and the half that works would be the wrong one to draw conclusions from.
>
> ### ⛔ What this measurement does NOT say
>
> | | |
> |---|---|
> | ⚠ **it is not the comparison with `quiche`** | `quiche`'s number **does not exist yet**: its C example does HTTP/3, not WebTransport. Until the same layer is grafted there too, ours is a number **without its comparison** |
> | ⚠ **two properties out of six**, *at 08:00* | of the six that B2 had to verify here, this measurement carried two — **datagrams enabled** and **`max_idle_timeout` 30 s**. ⭐ **The other four were closed half an hour later**, box below: no `[?]` remain |
> | ⚠ **the milliseconds are not compared** | 118.6 ms (Chrome) and 140.0 ms (Firefox) are **cold starts inside `xvfb`**, and the same engine gave 22.2 ms in another round. B2 measures *whether the session opens*, not how long it takes: whoever puts these numbers next to the 30.2 ms of 9 Aug will compare two different things |

> ### ⭐ The six properties of the transport: **6 out of 6**, read from the peer — `[M]` 10 Aug 2026, morning
>
> *`banchi/01-b2-sonda-trasporto.py`, with a declared spy on `aioquic`'s
> `pull_quic_transport_parameters`. ⛔ **From the peer, not from the server's log**: it is the source the
> box above had got wrong.*
>
> | | |
> |---|---|
> | `max_idle_timeout` | **30,000 ms** |
> | datagrams | enabled, `max_datagram_frame_size` **65,536** |
> | unidirectional stream credit | **16** |
> | migration | **not** disabled |
> | 0-RTT | **not offered** |
> | `allowPooling` | **`false`**, and declared in the recorded outcome |
> | ⛔ **and the seventh, which B3 needs** | the idle cap **can be changed**: with `--timeout=10s` the peer reads **10,000 ms** |
>
> ⛔ **And reading them from the peer found two defects no functional bench saw**: the server **offered
> 0-RTT** (two tickets, `max_early_data_size` `0xffffffff`), which §2.3 forbids because 0-RTT data can be
> replayed and RCP's second message is `CREDENZIALI`; and it granted **3** unidirectional streams instead
> of the 16 that §2.3 imposes. ⚠ *Neither has a symptom: the session opened the same. `FASI.md`
> §01-filo-nudo had foreseen it for the first — «the symptom of 0-RTT switched on does not exist».*
>
> ⚠ *This box was added on 10 Aug 2026, finding **R11.5**: the measurement existed and was in `README.md`
> and in `FASI.md` §01-filo-nudo, but **not here** — and §6.4 went on declaring four out of six still
> `[?]`. Three lines of the same day and the same bench that said different things, and the one a reader
> is entitled to take as good is this one (`README.md`: «the decisions live in `DECISIONI.md`, only
> once»). ⛔ **And it was not symmetric**: with the old line the 0-RTT ban of `RCP.md` §2.3 appeared
> unverified while two documents declared it verified.*

> ### ⭐ How many lines are ours, and at what time — `[M]` 10 Aug 2026
>
> ⛔ **The number grew three times in one day, and the three measurements cannot be compared unless one
> says at what time they were taken.** They are all `git diff` in the `ngtcp2` tree, never estimates.
>
> | Time | What was measured | Added | Code | Comment | Blank |
> |---|---|---|---|---|---|
> | **08:00** | B2's WebTransport layer, before the transport cures | **456** | **329** | 85 | 42 |
> | ~08:30~ | ⚠ `[?]` a number **482 / 333** entered `README.md` with the commit of the six properties, and **no document records its breakdown or the command that produced it**. It is neither promoted nor deleted: it stays here, declared for what is known | ~482~ | ~333~ | — | — |
> | ⭐ **16:30** | B2's WebTransport layer **alone**, after reading the close capsule | **553** | **373** | **134** | **46** |
>
> ⭐ **How the 16:30 one was taken, and it is the point that makes it repeatable**: on a clean tree, after
> `01-b3-rcp-innesta.py --togli` and `01-b2-ngtcp2-wt-innesta.py --togli`, reapplying **only**
> `01-b2-ngtcp2-wt-innesta.py`. It is the sequence that `ricostruisci()` of `banchi/01-b11-guasto.sh`
> already runs.
>
> ⛔ **And a number that does NOT go in this column**: with **both** grafts applied — B2 plus B3's wires —
> the example carries **972 lines added, 618 of code** `[M]`, same time. ⚠ *It is not comparable with the
> three above: it measures two things instead of one, and that is precisely the reason why
> `01-b3-rcp-innesta.py` is a **separate** graft — «growing it with RCP inside would give two different
> measurements under the same label» (shape **E2**).*
>
> ⚠ *The box is from 10 Aug 2026, finding **R11.1**. `README.md` carried 482/333 under the title «What is
> measured `[M]`» — the place where a number without provenance weighs most — while this document and
> `FASI.md` §01-filo-nudo carried 456/329 from the same day. ⛔ And the justification the README gave for
> not remeasuring was false: the measurement can be taken, and now it is taken.*

> ### ⛔⭐ And `quiche` does not reach WebTransport from C: the declaration cannot be made — `[M]` 10 Aug 2026
>
> *The rule of the 333 lines, applied a second time: **the thing that can kill the candidate is tested
> first**. Here it cost reading two files and one connection, instead of a second WebTransport layer
> written in full.*
>
> **The reading, and the prediction written beforehand** `[R]`:
>
> | | |
> |---|---|
> | ⭐ **`quiche` HAS the function `nghttp3` lacks** | `h3::Config::set_additional_settings(Vec<(u64,u64)>)` — `quiche/src/h3/mod.rs:644`. A clean and supported way to put an arbitrary setting into its own SETTINGS |
> | ⛔ **but it does not reach the C API** | **zero** occurrences of `additional_settings` in `h3/ffi.rs` and **zero** in `include/quiche.h`. The `quiche_h3_config` exports **four** setters, and none is that one |
> | ⛔ **and the `ngtcp2` trick does not exist there** | on `ngtcp2` nghttp3 **hands the application** the control stream's bytes to write, and we rewrote them on the fly. `quiche` writes into the connection by itself: a C application **never sees** those bytes |
>
> ⇒ **prediction: `quiche`, from C, will not declare WebTransport.**
>
> **The measurement** — `banchi/01-b2-sonda-impostazioni.py`, which reads `aioquic`'s `received_settings`,
> that is **what arrived on the wire**, not what the configuration says:
>
> | Server | Settings declared |
> |---|---|
> | ⭐ **`ngtcp2` with our layer** *(positive control)* | **7**, among which `ENABLE_WEBTRANSPORT` **and** `WT_MAX_SESSIONS` |
> | ⛔ **`quiche`**, with everything on | **4**: `ENABLE_CONNECT_PROTOCOL`, `H3_DATAGRAM`, `H3_DATAGRAM_00`, and one GREASE. ⛔ **Neither of the two WebTransport declarations** |
>
> ⛔ **So a browser would not open the session, and there is no line of code of ours that can fix it**:
> that frame is written by the library, and from C there is no way to touch it.
>
> ⚠ **And the honest line next to the verdict**: *«impossible»* would be too much. The function **exists**,
> it is just not exposed — that is **a dozen lines of FFI**, to send upstream or to carry along as a
> patch. Added to `rustc` 1.88 against 1.85, however, it becomes: *to use `quiche` you have to touch
> `quiche`*. With `ngtcp2` there is no need to touch anything, and it is C.
>
> ⚠ **And what this measurement does NOT say**: **how many lines** the WebTransport layer would cost on
> `quiche`. It is not known, because we did not get to writing it — the candidate falls at an earlier
> gate. ⭐ And that is exactly the point of the rule: the number we do not have is also the work we did
> not spend.
>
> ⭐ **A detail that counts as a clue of care**: `quiche` sends a **GREASE** (`0x28d3890f99ed6413`), that
> is a setting invented on purpose so that peers do not get used to a fixed list (RFC 9114 §7.2.4.1).
> `ngtcp2`+`nghttp3`, with our layer, does not.
>
> ### ⭐ And the starting point of `ngtcp2`+`nghttp3`, measured — `[M]` 9 Aug 2026
>
> *Bench `banchi/01-b2-costruisci-ngtcp2.sh`. Searched inside **447 files** of the two trees, ⛔ **with the
> positive control of the search**: the word `nghttp3` appears in **110 files**, so the grep is really
> reading.*
>
> | What | Files |
> |---|---|
> | `SETTINGS_WT_MAX_SESSIONS` (`0xc671706a`) | ⛔ **0** |
> | the token `webtransport` | ⛔ **0** |
> | the extended CONNECT (`:protocol`, `ENABLE_CONNECT_PROTOCOL`) | ✅ **9** |
>
> ⭐ **The prediction holds, and now it is measured**: the foundations are there, **the WebTransport layer
> is not there at all**. From which the number B2 must produce — *how many lines of glue* — which is
> **counted**, not estimated.
>
> ⚠ *The first round of this same check had printed «la previsione regge» from a search **never run** —
> two trees passed as a single string, with `2>/dev/null` hiding the error. The number above holds
> because the bench now declares its own denominator. It is the fourth rule of `LEZIONI.md` §1.9, born
> from that error.*
>
> ⛔ **None of the lines of this box is a measurement of the PRODUCT.** They are the lens that says **for
> whom it is worth writing the glue**, and how much of it will be needed.

---

## 7. ❓ The open questions

**They are not decisions.** They are holes, listed so that they are not lost.

### 7.1 ~~The size of the canvas at birth~~ → **closed on 8 Aug, see §5.0**
The client dictates it at every attach. No defaults, no preferences.

### 7.2 ~~Screen lock on disconnection~~ → **closed on 8 Aug, see §4.3**
The lock belongs to REMOTIX, not to the desktop: 30 minutes without input and the client is detached. With
a written expiry condition, to be reread if a stronger authentication arrives.

### 7.3 ~~The ghost: takeover or wait?~~ → **closed on 8 Aug, see §4.4**
Neither: whoever is silent is detached, and nobody holds the slot. The fork no longer
exists. ⚠ What stays out, and was not asked, is the third possibility — **two clients on the same
desktop together**: it would cost little with a persistent stage, but it changes the protocol and would have to be
decided before writing it, not after.

### 7.3-bis ~~After how many seconds of silence is a client detached?~~ → **closed on 9 Aug**
🔸 **30 seconds**, written in `SPECIFICHE.md` §5.3 — my proposal, not pronounced by the user.
The threshold decides **when the encoder is freed**, and has no other costs: being declared
detached loses nothing, because nobody holds the slot (§4.4). With QUIC the switch
WiFi → LTE does not count as silence, so the 30 seconds cover only the real interruptions.

### 7.4 ~~Proportions: bands or stretching?~~ → **closed on 9 Aug**
🔸 **We lay out, we do not stretch** — `SPECIFICHE.md` §6.2. Stretching deforms the text and makes it
unreadable, which is the one thing a desktop cannot afford. The case is rare by
construction: at attach the proportions always match, and it remains only during
resizing and in the fallback on old KDE.

### 7.5 ~~The server's language~~ → **closed on 8 Aug, see §6.3**
C, confirmed. Not by inheritance: v1's reason was FreeRDP and it died with RDP. The new
reason is the reuse count, benches included.

### 7.6 ⏳ The licence — **postponed to the end of the project**, by the user's decision (9 Aug 2026)
It is no longer a question waiting for an answer: it is a **scheduled** decision, and it is taken
when the project is finished. Until then only the constraint that has already emerged holds, and it must be respected
so as not to find it decided by itself: **no x265** (GPL-only) as software fallback. With
SVT-AV1 (BSD-3) and FFmpeg compiled without `--enable-gpl` the choice stays entirely open.


### 7.7 ~~Multi-tenant: how many users together?~~ → **closed on 9 Aug, see §4.6**
Ten as a configurable cap. But the real limit is not a count: it is a budget of pixels per
second, and on a single machine the encoder sets it.

### 7.8 ~~The latency~~ → **closed on 9 Aug, see §2.4-2.6**
50 ms cap, 40 target, and only for the piece that is ours. ⛔ *The warning that stood here —
«the target on GNOME is probably not reached, for the same reason as the 60 frames» — **fell
on 13 Aug 2026**: the delay measured then exceeded even the cap, but the reason was not
that — the big part was ours (the software encoder; the measurement no longer holds after
phase 18), and the wall of 37 does not reproduce (§2.5).*

### 7.9 ~~Trust: who authenticates the server to the user?~~ → **closed on 9 Aug, see §1.3**
Trust on first encounter, remembered silently. No fingerprint to compare: the risk
on the first connection was assessed and accepted for the intended scenario.

### 7.10 ~~Touch from Android~~ → **closed on 8 Aug, see §5-bis**
It was v1's open question no. 1, never closed in a year. Answer: trackpad with a pointer
drawn by the client; native touch with the slot reserved but not implemented.

### 7.10-bis ~~The Android keyboard: Unicode or scancode?~~ → **closed on 8 Aug, see §5-bis.6 and §5-bis.7**
Both, but not as equals: **letters** travel as letters, and only the keys that are not letters
travel as positions. And the question widened from Android to both clients.
What follows is the reasoning that led us there, kept because the conclusion alone cannot
be understood.
Touch's passenger, and it weighs more. *«An Android keyboard is not a physical keyboard: it has
no scancodes, it has an IME that produces text»* (`fondamenta/documenti/client-android.md` §5.2). The client
therefore sends **Unicode** for the printable characters and **scancodes** for the control keys —
Enter, Tab, arrows, modifiers.

**Proposed: both, and Unicode not as a fallback but as the main route.** As a dowry
comes the closing of v1's question no. 7: the keyboard layout declared by the
client, on Android, **is not needed** — what arrives is already the final character.

What remains to be confirmed, and it is the part that costs: the conversion from character to **physical position
in the session's layout**, with the modifiers applied around it.

### 7.11 ~~The clipboard: bidirectional?~~ → **closed on 9 Aug, see §5-ter**
Yes, in both directions, and text only. The question arose because `SPECIFICHE.md` said
«server-client», which reads in one direction only.

### 7.12 ~~The «out of scope»~~ → **closed on 9 Aug**
🔸 Written in `SPECIFICHE.md` §12, ten items, each one excluded **deliberately** and not
forgotten: Windows, the X11 desktops, redirection of disks/printers/ports/smart cards, file
transfer, images and files in the clipboard, multi-monitor as a feature, the stylus,
native touch, session recording, and compatibility with RDP/VNC/SPICE clients.

### 7.13 📖 Cinnamon — it is not decided, **it is studied**

*9 Aug 2026. «Va fatto uno studio simile a quanto fatto per gli altri DE: Cinnamon è in fase
di migrazione verso Wayland ma il processo è iniziato da poco, quindi non conosco lo stato in
cui è».*

⚠ **The proposal to declare it out of scope was rejected**, and the reason is right: in or
out is not decided on an impression. The other four desktops have a study each,
this one does not, and until it does every judgement is `[?]`.

⭐ **But the study costs much less than the other four, and it must be said so that it is not postponed
for fear of its size.** Muffin **is not an independent compositor**: it is a fork of Mutter,
split off in GNOME 3 times, and it inherits its architecture. So `STUDI.md` §cinnamon does not start from
a blank sheet — **it starts from `STUDI.md` §gnome and looks for the differences**. It is a reading in negative:
*is this piece of Mutter still there? has it been renamed? has it stayed stuck five years ago?*

**The two questions that decide, and must be asked first:**

1. **can a virtual screen be created without a monitor?** On GNOME it is `RecordVirtual`; on KDE the
   negative answer was the most expensive result of the whole study (`STUDI.md` §kde §8.1);
2. **how many frames does the capture deliver, with a declared and always moving scene?**
   Mutter 37, KWin 60, wlroots 61 `[M]`.

Then the other twelve of `LEZIONI.md` §3, and the recipe of §9 — starting from point 0, *look for whoever
has already done it*, which on KDE had led to finding `KRdp` in a ninth repository after the study
had given it up as non-existent.

> ## ✅ The study was done on 9 Aug 2026 — it is in [`STUDI.md` §cinnamon](STUDI.md#cinnamon)
>
> On `muffin` and `cinnamon` **6.7.4**, in `reference-cinnamon/`. **All `[R]`, nothing measured.**
>
> **The fork hypothesis is confirmed**: the `cinnamon` binary *is* the compositor, it calls
> `meta_init()` and `meta_run()` like gnome-shell. `ScreenCast` and `RemoteDesktop` are
> Mutter's interfaces renamed, and **there is no gate** on the capture permission.
>
> ⛔ **But three things we take for granted do not exist at all** — checked with the tool
> certified first on Mutter:
>
> | | Muffin 6.7.4 |
> |---|---|
> | `RecordVirtual` and `virtual_monitor` | **0 files** in the whole tree |
> | `ConnectToEIS` — input via libei | **0 files** |
> | `EnableClipboard` — the clipboard | **0 files**, and not even `zwlr_data_control` |
> | a *headless* backend | only in `src/tests/` |
>
> ⭐ **The route that remains**, and it is the reason not to close the item: `META_DUMMY_MONITORS` +
> `MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60` force a **dummy** monitor on any
> backend, with the size decided at startup — the equivalent of KWin's `--virtual --width W`, which
> the canvas model (§5.0) already absorbs.
>
> ⚠ **Whether it really holds is `[?]`, and it is measurement M1 of §9 of `STUDI.md` §cinnamon**: that the monitor
> manager is fake does not say that the renderer is. It can even succeed **by delivering zero
> frames**, which is the worst way because it looks like it works (`REVIEWER.md` E1).
>
> **The provisional judgement**: Cinnamon costs more than all five, and the two difficulties — a
> second input path, and a clipboard that **today has no route** — are not difficulties of
> reading but features missing upstream. **It must be put last**, and the decision is taken on the
> measurements, not on this document.
>
> ⏳ **And it has an expiry date, set by the user on 9 Aug:** *«tanto Cinnamon sarà l'ultimo
> DE ad essere supportato, e le cose potrebbero cambiare»*. It is the right clause: the three absences
> that weigh — `RecordVirtual`, libei, the clipboard — are **features that Mint can bring at
> any moment**, exactly as KDE brought resizing with `kwin!7932`. Whoever
> reopens this item **must reclone `muffin` and redo the four searches** before trusting
> `STUDI.md` §cinnamon: a reference that ages silently is worse than no reference
> (`LEZIONI.md` §9.8).

---

> ## ⛔ The three questions of the night of 10 Aug 2026 — **they are answered with one word**
>
> The three that follow (§7.14, §7.15, §7.16) arose from the review `fasi/rapporti/R11-documenti.md`
> and are **here** because this is where the decisions are, once only: `RCP.md`,
> `FASI.md` §01-filo-nudo and `README.md` **refer**, they do not copy.
>
> ⛔ **None of the three is decided**, and the mark stays ❓ until the user speaks — even where
> I write which one seems most defensible to me. Two of them (§7.14, §7.15) **change the bytes on the wire**,
> and while they are open two implementations conforming to `RCP.md` diverge without either of the
> two being wrong.
>
> ⚠ **And since 11 Aug 2026 they are four**: §7.17 was born the next day, **from a measurement** — bench
> B6 — and not from a reading. Everything written above holds for it.
>
> ---
>
> ## ✅⭐ **ALL FOUR ARE CLOSED — on 11 Aug 2026**, and the user closed them
>
> | | the answer | and what it brought with it |
> |---|---|---|
> | **§7.14** | *«silenzio»* | whoever receives a `FIN` sends nothing more. ⛔ And `RCP.md` §8.1 gains the exception: **whoever has received a `FIN` is not «the one who closes»** |
> | **§7.15** | *«se si può»* | the `CONGEDO` falls when the channel is dead; the reason stays in the close code. ⭐ It closes a **red on correct code** that B5 and B11 would have given |
> | **§7.16** | *«si tiene per i test, nel prodotto si fa pulizia»* | ⭐ and the answer was **wider than the question**: a principle was born — `SPECIFICHE.md` §2 point 6, *on the user's screen there is his desktop and nothing else* — with the cleanup to be measured at phase 13 |
> | **§7.17** | *«5 secondi»* | ⛔ the last way to **occupy a slot without saying who you are** |
>
> ⭐ **And three of them interlock on a single case**: the cap of §7.17 fires when the control
> channel does not exist yet, so §7.15 says the `CONGEDO` is not sent and §7.14 says which way
> the reason travels. ⚠ *Decided separately, within an hour, and none of the three would have been
> defensible alone.*
>
> ⛔ **None of the four is proven on the hardware yet.** §7.17 asks **B6** for a fourth case,
> §7.14 asks for three fixes to `src/pagina.html` (lines 431, 479, 514, where the product today does the
> opposite), §7.16 asks for a bench at phase 13. **Decided ≠ measured**, and until they are the
> distance is declared.

### 7.14 ✅ The `FIN` on the control channel: whoever receives it **stays silent**

> ## ✅ **SILENCE** — decided by the user on **11 Aug 2026**
>
> *«silenzio, anche perché il server non attacca mai di sua iniziativa»*
>
> ⛔ **Whoever receives a `FIN` on the control channel sends nothing more, not even there.** The reason
> travels by the second route of `RCP.md` §3.1 point 3 — the application error code of the
> close — which does not need a live channel.
>
> ### ⛔ The premise was false, and it must be written here because it is the one with which the decision was taken
>
> *«Il server non attacca mai di sua iniziativa»* **does not hold**: closing on its own initiative is the
> **most measured** behaviour of phase 1.
>
> | when the server closes by itself | how far it is proven |
> |---|---|
> | one of the caps of §4.6 expires | `[M]` **B6**: all three seen firing — **5.0 · 60.1 · 10.0 s** — with the farewell `TEMPO_SCADUTO` |
> | a violation arrives | `[M]` **B5**: **36 cases out of 36**, and after each one a new connection reaches `ECCOMI` |
> | credentials, ban, slot occupied | `RESPINTO` (§4.4) · `TROPPI_TENTATIVI` (§4.4-bis) · `GIA_ATTIVA_REMOTA` (§8.2) |
> | and the case the question comes from | ⛔ the **fourth defect of B11** was *«the slot is not freed when the one closing the channel is the SERVER»*, `[M]` on Chrome |
>
> ⭐ **The decision does not change, and the true reason makes it stronger**: precisely because the server
> closes often, what the receiver does matters — and it is the measurement that chooses, not the rarity of the case.
> ⚠ *Written this way, and not «as the user said», because a false reason in a decision
> register lasts longer than the decision: it is form **E5**, a fact that was a deduction never
> measured.*
>
> ⭐ **And the premise did not end there: it became a rule.** Faced with the contradiction,
> the user chose the narrow form — *the server does not throw out a **healthy** session, and every one of its
> closes has a reason it can explain* — and not the wide one, which would have taken away the ban, the
> refusal of credentials and the strictness rule. ⇒ **`DECISIONI.md` §4.1-bis**, ✅ 11 Aug 2026.
> ⚠ *That is: the sentence was false as a description of what the server does **today**, and it was right as a
> description of what the server **must** do. The two things resemble each other enough to pass
> for the same, and in a decision register they are not.*
>
> ### The reason that holds, and it is a measurement
>
> `[M]` **10 Aug 2026**, defect 2 of **B11**: **Chrome throws away a message sent just before
> closing the session.** The `CONGEDO` of reading B would therefore be a **MUST that one engine out of
> two cannot honour** — the form that finding **R1.4** has already declared a defect. The second
> route of §3.1 point 3, instead, ⭐ **worked on both engines**, and on Firefox it is
> **the only one** that carries the reason (the farewell arrives by two different routes, one per engine).
>
> ### Where the decision went, and the price is paid in full
>
> | | |
> |---|---|
> | `RCP.md` §4.2 | the ban goes from *«on the other channels»* to **«on no channel, the control one included»** |
> | ⛔ `RCP.md` §8.1 | **the written exception**: *whoever has received a `FIN` is not «the one who closes»*. ⚠ Without it §4.2 forbids the byte and §8.1 imposes it: the decision would have **moved** the contradiction instead of closing it |
> | ⭐ `banchi/01-b11-lancia.sh` | the case `fin-sul-controllo` already had the expected *«mute»*: ⛔ **the bench applied this reading without any line saying it**, and that is the reason why the question had been asked |
> | ⛔ `src/pagina.html` **lines 431, 479, 514** | ⛔ **the product today does the OPPOSITE**: in all three places, when the server closes the channel without answering, the page calls `congeda(ERRORE_PROTOCOLLO, …)` — that is, it sends the nine bytes. `[M]` 11 Aug 2026, read in the source. **Three defects to cure**, and the cure is to remove the call leaving the `esito(...)` |
>
> ⚠ **And one thing the cure must NOT take away**: those three places call `congeda()` also to
> **write the outcome to the user**. Whoever removes the line without looking also removes the sentence that says
> *«the server closed without answering»*, and the symptom becomes a page that explains nothing —
> which is precisely what §8.2 forbids.

*Asked on the night of 10 Aug 2026, finding **R11.22**. It concerns `RCP.md` §4.2 and §8.1. The two
readings below are left as they were: ⛔ a decision without the alternative it discarded
cannot be called back into question when the facts change.*

**The fact.** §4.2 says: *«a `FIN` on that stream, from either of the two parties, closes the
session. Whoever receives it **MUST** consider it finished; it **MUST NOT** continue to send **on the
other channels**»*. The control channel is a **bidirectional** stream: the server's `FIN` closes
the server's direction, not the page's. And §8.1 requires whoever closes to send `CONGEDO`.
⛔ **The written ban names «the other channels» and does not name the control one**, so the two
readings both conform to today's text.

| | **A — silence** | **B — the farewell** |
|---|---|---|
| **the rule** | the `FIN` closes the session **in both directions**: whoever receives it sends nothing more, not even on the control | the ban is only «on the other channels»: on the control the page **MUST** still send the `CONGEDO` of §8.1, then close |
| ⛔ **the byte on the wire** | **none.** The reason travels only in the application error code of the session close (§3.1 point 3) | **nine bytes** on the control channel, before the close: `00 0C` (`CONGEDO`, §7.1) · `00 00 00 03` · the reason of §8.2 · `00 00` (empty detail). Then the same close as A |
| **who applies it today** | ⛔ **the bench**: the case `fin-sul-controllo` of B11 has as expected *«mute»*, and the page stays silent | nobody |
| **the price** | §8.1 must gain the written exception — *whoever has received a `FIN` is not «the one who closes»* — or it keeps imposing an obligation that §4.2 forbids | the server cannot count on that byte: ⛔ `[M]` 10 Aug, **Chrome throws away a message sent just before closing the session** (defect 2 of B11). A `MUST` that one engine out of two does not honour |

**The concrete case, and it has already happened.** It is the point where on 10 Aug the **fourth defect
of B11** was born: on Chrome, after the server's `FIN` on the control channel, **the slot of §8.2 `0x0F`
was not freed** because from there on no byte capable of freeing it arrived any more, and the user
saw *«mi dice che sono già collegato, e non è vero»*. With reading **B** that byte would exist
— it is the `CONGEDO` — and it would arrive where the server already looks. With reading **A** the slot is freed
by reading the close capsule, which is the cure that was written that evening.

⭐ **Which one seems most defensible to me, and the reason: A — silence.** Not because of the text, which
admits both, but because of two measurements from the same day: the second route of §3.1 point 3 —
the reason inside the close code — **worked on both engines**, while the
`CONGEDO` of reading B **was seen disappearing on Chrome**. ⛔ A `MUST` that one browser out of two
cannot honour is exactly the form that finding R1.4 declared a defect — *«era conforme
al testo quanto il primo»*. ⚠ And the price of A must be paid in full: without the exception written in
§8.1, A leaves the contradiction standing instead of closing it.

**How it is closed:** one word — *«silenzio»* or *«congedo»*. Then §4.2 says whether the received `FIN`
also closes the direction of whoever receives it, and §8.1 takes in the exception or loses it.

### 7.15 ✅ The farewell of §8.1 holds **if the channel is still usable**

> ## ✅ **THE CONDITION** — decided by the user on **11 Aug 2026**
>
> *«la soluzione più logica è "se si può". Se una connessione cade nessuno può dire al server
> "chiudo perché ho finito"»*
>
> ⛔ **The obligation of the `CONGEDO` on the control channel falls when the channel is not usable.**
> What never falls is the reason inside the **application error code of the close**
> (`RCP.md` §3.1 point 3), which travels in the close itself and leaves even with a dead channel.
>
> ⭐ **And the user's reason is the right reason, without corrections**: a `MUST` that cannot be
> respected is not a rule. `RCP.md` §0 says it of itself — *if a line here is ambiguous, it is a defect
> of this file* — and this one was: §8.1 imposed it without conditions, §3.1 point 2 with the
> condition, ⛔ and **an implementation conforming to one was in violation of the other**.
>
> ### Where it went, and what it closed
>
> | | |
> |---|---|
> | `RCP.md` §8.1 | the normative line carries the condition inside, and the box says why |
> | ⭐ **a red on correct code** | **B5** and **B11** already applied the conditional (finding R3.3): a bench written on the absolute form **would have failed a correct server** every time the violation arrives on a unidirectional stream with the control already finished |
> | ⚠ **and it does not weaken §4.1-bis** | *every close of the server has a reason it can explain*, decided the same day: the reason arrives anyway. ⛔ What is lost is **the byte on the dead channel**, that is a byte that did not leave |
>
> ⛔ **The two decisions of 11 Aug do not replace each other**: §7.15 says **when** the obligation falls,
> §7.14 says **who** is not bound at all. After a received `FIN` the channel, in the direction of whoever
> received it, **is still usable** — so without §7.14 the condition of §7.15 would not save it.

*Asked on the night of 10 Aug 2026, finding **R11.23**. It concerns `RCP.md` §8.1 and §3.1 point 2. The
two readings below stay as they were.*

**The fact.** §8.1: *«Whoever closes **MUST** send `CONGEDO` with a reason before closing the
session»*, and the only declared exception is `RESPINTO`. §3.1 point 2, for the same thing:
*«it **MUST** send `CONGEDO` (§8) with the reason, on the control channel, **if the control
channel is still usable**»*. ⛔ An implementation that closes **without** a farewell because the
channel is broken is **conforming to §3.1 and in violation of §8.1**, in the same document.

| | **A — the obligation is unconditional** | **B — the condition of §3.1 holds** |
|---|---|---|
| **the rule** | whoever closes sends `CONGEDO` **always**, except after `RESPINTO` | the obligation falls when the control channel is not usable; the reason passes anyway through point 3 |
| ⛔ **the byte on the wire** | the nine bytes of the `CONGEDO` **even** when the control is already closed or broken — that is, a byte that often cannot leave | **no byte** in that case: only the application error code of the close remains (§3.1 point 3) |
| **who applies it today** | nobody | ⛔ **the bench**: B5 and B11 check the closes *«at the three points of §3.1 with the second conditional»* (`FASI.md` §01-filo-nudo, finding R3.3) |
| **the price** | a bench written on §8.1 **fails a correct server** every time the violation arrives on a unidirectional stream | §8.1 loses the absolute form, and must be rewritten with the condition inside — one sentence |

**The concrete case.** A violation arrives on a **unidirectional stream** after the control
channel has already finished: with **A** the server must send a `CONGEDO` on a channel that no longer exists,
and the bench that demands all three points of §3.1 **gives red on the correct code** — it is finding
R3.3, already paid once on this same bench.

⭐ **Which one seems most defensible to me, and the reason: B — the condition.** A `MUST` that cannot be
respected is not a rule, it is a defect of the document (`RCP.md` §0: *«if a line here is ambiguous,
it is a defect of this file»*), and the second route never fails: the reason travels in the close
code even when the channel is dead. ⛔ **And it costs one sentence in §8.1, zero bytes on the wire.**

⚠ **The two questions touch and do not replace each other.** Answering *«the condition holds»* to §7.15
does **not** close §7.14: after a received `FIN` the control channel, **in the direction of whoever
received it**, is still usable — and it is exactly the point that §7.14 asks.

### 7.16 ✅ The bench function stays 🔸 — and ⭐ **outside the delivered product**

> ## ✅ **TWO DISTINCT CASES** — decided by the user on **11 Aug 2026**
>
> *«Nessun quadratino: l'utente deve vedere il desktop senza artefatti, come se fosse davanti al
> monitor del PC» → and then, faced with the price: «distinguiamo i 2 casi: si tiene quello che
> serve per i test, ma poi nel prodotto finale si fa pulizia».*
>
> ⛔ **The principle, and it is bigger than the question that had been asked**: on the user's screen
> **nothing** that is not his desktop **ever** appears. Not «off by default», not «behind
> a switch»: **absent**. Whoever connects must see what he would see sitting in front of the
> PC's monitor, and nothing else.
>
> ⭐ **And the bench function survives, on the other side of the border**: it serves to **calibrate the
> stopwatch** of the delay at phase 3 — a known delay is injected and one checks that the median
> rises by exactly that. ⛔ *«A bench that does not do it does not know it is measuring»*
> (`web/rapporti/S4-ritardo-disegno.md` §4.2, control P1): removing it entirely would have left
> the most important number of the project — the 50 ms cap — **without a way of knowing whether it is
> true**.
>
> ### What it means, concretely
>
> | | |
> |---|---|
> | **the mark stays 🔸** | it was not a user's decision, and ⛔ **it can be removed without going back to him**. What the user decided is the **border**, not the message |
> | ⛔ **the delivered product does not contain it** | not compiled, not reachable, **not present in the binary**. ⚠ *«Off»* is no longer enough: it was the earlier form, and this decision replaces it |
> | **the bench does** | the test build contains it, and the two types `0x000F`/`0x0010` stay in `RCP.md` §7.5 as a **declared bench function**, not as a product function |
> | ⛔ **and the difference is measured** | *«it is not there»* and *«it is there and it is off»* look the same from outside: they are told apart **by searching for the marks inside the delivered binary**, as `banchi/01-p1-prodotto.sh` already does with its eight marks. Without that proof, this decision is a good intention |
>
> ### ⛔ Where it bites, and it is not today
>
> **Phase 13 — the packaging.** That is where the binary that gets installed is born, and that is where this
> decision is respected or lost. ⚠ *Written also in `PIANO.md` phase 13 and in `RCP.md` §7.5,
> because a rule that holds eleven phases from now and is written in one place only is a rule that nobody
> will find on the day it is needed.*
>
> ⚠ **And one thing this decision does NOT say**: that the bench function was a problem. It is born
> **off**, and `banchi/01-b5-violazioni.py` checks that with the function off the server **refuses**
> declaring `FUNZIONE_SPENTA`. The defect was not there: the user raised the bar from *«it is not
> seen»* to *«it is not there»*.

*Asked on the night of 10 Aug 2026, finding **R11.15**. The row is in §1.5 row 26, and it is 🔸 — not
✅. The question as it was asked stays below.*

**The fact.** `RCP.md` §7.5 adds to the protocol **two message types** — `BANCO_MARCA`
(`0x000F`) and `BANCO_ESITO` (`0x0010`) — and §7.5 declares that it comes from **finding R3.4** of the
bench review, with the motivation from `web/rapporti/S4-ritardo-disegno.md` §5.3. ⛔ **There is
neither a sentence nor an entry**, while the decisions the user really pronounced (§1.6, §1.8,
§1.9) carry here the quoted sentence with the date. `FASI.md` §01-filo-nudo marked it ✅, that is
*«decided by the user»*: corrected to 🔸 on 10 Aug.

| | **A — it was yours (✅)** | **B — it is derived (🔸)** |
|---|---|---|
| **what changes** | it is not touched without going back to you | *«it is corrected without discussion»* |
| ⛔ **the byte** | none **today**: the two types are there in both cases. What changes is **reversibility** — with A the `0x000F`/`0x0010` stay in RCP/1 forever, with B they can be removed | |
| **the weight** | those two types **used up the clause of §9** — *«today no implementation exists»* — which `RCP.md` §12 declares to have been **the last opportunity** to add message types | |

**The concrete case.** The day those two types become a nuisance — an implementation that must
recognise them to be conforming, in an environment where *painting a small square on someone's
desktop* is not acceptable even behind a switch — with **B** they are removed, with **A** they are not. ⚠ And
there is the half that counts even if the answer is *«up to you»*: **your protocol carries two types that
you did not ask for**, and this row exists so that you know it.

⭐ **Which one seems most defensible to me, and the reason: B — 🔸.** The provenance is declared by §7.5
itself and it is not a sentence of yours; marking it ✅ would give it a protection that no measurement gave it
(`LEZIONI.md` §2.3-quater). ⛔ But it is the only one of the three that **only you** can really close, because
the question is *whether you said it*.

**How it is closed:** *«yes, it was mine»* ⇒ it becomes ✅ and §1.5 row 26 receives the sentence with the date.
*«no»* ⇒ it stays 🔸 where it is, and it is not talked about any more.

### 7.18 ✅ **Firefox for Android is NOT SUPPORTED** — and the MSE path stays as proof

*Opened on 21 Aug 2026, and it descends from §0.1-bis without being resolved by it.*

⛔ **The facts, measured**: Firefox for Android does not have WebCodecs — neither `VideoDecoder` nor
`AudioDecoder` — so today REMOTIX there **does not draw a pixel**, and it is not a codec question
(the route to the pixels is a single one in `pagina.html`). ⭐ It does however have WebTransport and decodes H.264
**in hardware** via MSE: the capability is there, what is missing is the way to give it the bytes.

⛔ **The price, measured** (`fasi/06`, bench `07-b57`): MSE costs **+225 ms** on Firefox and
**+415 ms** on Chrome on the median, with a playback queue of 310–715 ms, against the declared
cap of **50 ms**. ⚠ And chasing does not save it: 40 jumps over 150 frames.

| the reading | what work it produces |
|---|---|
| *«l'utente Android deve accettare le scarse performance di Firefox»* presupposes that REMOTIX works there | ⇒ the MSE path **is written** (fMP4 muxer in the client, separate audio path), and the delay of another class is declared |
| *«REMOTIX non può rincorrere i bug dei software»* | ⇒ **nothing is written**: Firefox Android is declared not supported until Mozilla brings WebCodecs, and there Chrome is used |

⇒ **The two readings of the same sentence led to opposite work**, so it was not deduced: it was
asked. ⚠ And there was a fact weighing on the other side: Mozilla declares mobile support
*«still missing, which we're currently working on»*, that is the problem could expire by itself.

> ### ✅ **21 Aug 2026, from the user: the MSE path is built.**
>
> ⚠ And the reason why §0.1-bis does not forbid it lies in the difference between the two cases: that principle
> speaks of an engine that **performs worse**. Here the engine does not perform worse, ⛔ **it does not open at all** —
> the user said it in his own words: *«su Android Chrome funziona bene, è Firefox a non
> funzionare per nulla (non apre il desktop remoto)»*. ⇒ It is not chasing a performance
> defect: it is giving the product a route where it has none.
>
> ⭐ **And the audio does not need writing**: the page already falls back to `pcm` when `AudioDecoder` is missing
> (§4.3 imposes it on both and it is the always available base). ⇒ The work is **only the video**.
>
> ⭐ **And the protocol is not touched**: the same Annex-B frames as always pass on the wire.
> What changes is **how the client draws them**, and the server does not notice.

> ### ⛔⛔ AND THE SAME EVENING THE DECISION CHANGED — ✅ 21 Aug 2026, after trying it
>
> *The user: «Niente da fare, troppi problemi: **disegno del desktop irregolare, input
> imprevedibile**, dichiaro Firefox per Android incompatibile con REMOTIX».*
>
> ⚠ **And the route works**, measured: the desktop is seen alive and the touches reach the server
> (`fasi/06`, bench `07-b59` on an emulator with Firefox 154 for Android). ⛔ But *«works»* was not
> the target. The target is **§0.1-bis**: an experience close to that of a local
> session. A `<video>` that plays a stream cannot be asked to react like a
> decoder driven by hand — the delay is of another class and the rate is not ours.
>
> ⇒ **What changes in the product**: on a browser without WebCodecs the page **declares that it cannot
> be done** instead of giving half an experience. `VIA_MSE` no longer switches on by itself: only with
> `?disegno=mse`, which is a bench switch.
>
> ⭐ **Why the code stays**: it is measurable, and until Mozilla brings WebCodecs to Android it is
> **the only proof that the problem was not ours**. ⛔ At phase 13 it is decided whether to throw it away — §7.16,
> «nel prodotto finale si fa pulizia».
>
> ⚠ **And how much it cost stays written**: six rounds of tests on the user's phone and a day
> of work, for a route that does not enter the product. ⭐ It is not time entirely thrown away — out of it
> came `07-b58`, `07-b59` and §1.19 of `LEZIONI.md` — but the real lesson is that **the question «how much
> will it deliver?» had to be measured before building**, and the number was already there: `07-b57`, hundreds of
> milliseconds against a cap of 50.

### 7.20 ✅ **The supported engines, declared by the user** — 22 Aug 2026

> *«Chrome e Firefox su Linux, e Chrome su Android sono OK. Firefox per Android è uscito dal
> progetto.»* — and right after: *«**Anche Chrome per Windows è OK**.»*

⭐ **It is the list the project did not have yet**, given by the user on the live product and not deduced
from a measurement:

| where | engine | status |
|---|---|---|
| **Linux** | Chrome | ✅ **OK** |
| **Linux** | Firefox | ✅ **OK** |
| **Windows** | Chrome | ✅ **OK** |
| **Android** | Chrome | ✅ **OK** — and §7.19 details it: *«esperienza completa, audio e video perfetti»* |
| **Android** | Firefox | ⛔ **OUT OF THE PROJECT** — §7.18 |

⚠ **And what the list does NOT say, written so that it is not deduced**: **Firefox on Windows** is not
named, and nobody has ever tried it. ⛔ It is not «supported» and it is not «excluded»: it is **not tried**, and
it must be written so until someone opens it.

⭐ **And the border of §0.1-bis holds**: *«fully supported»* means **it works, and you know under what
conditions** — not *the same everywhere*. On Firefox pasting with the mouse costs a click **of Firefox**
(§5-ter.9), and that stays true.

### 7.19 ✅ **Chrome for Android is FULLY SUPPORTED** — user's judgement, 21 Aug 2026 evening

*The user, after using a real session from the phone: «**Chrome su Android offre un'esperienza
completa: audio e video perfetti**».*

⭐ **It is the twin of §7.18, and it is the reason why that one could be taken**: declaring an engine
not supported is sustainable only if on the same platform there is one that performs. On Android
there is, and it is judged — not deduced from the counters.

| | |
|---|---|
| what it closes | ⛔ **the last real defect of phase 7**: the audio queue at 400–420 ms. ⇒ `fasi/07-audio-e-appunti.md` §9.7 and §8 |
| ⚠ the number stays written | 401 → 421 ms, `[M]` on the first Android session. It stops being a **defect**, not being a **measurement**: the yardstick is I8, and for audio I8 is the ear |
| under what conditions | Samsung DeX, Android 16, **home network**, negotiated codec **HEVC in hardware**. ⏳ The datagram on a non-local network stays unmeasured |

⚠ **And this is §0.1-bis applied in full**: *«fully supported»* here means **it works, and
you know under what conditions** — not *the same everywhere*.

> ### ⛔ AND AN HOUR LATER THE USER CLARIFIED, from the Windows PC — the row «what it closes» was too generous
>
> *«Il ritardo di 400 ms tra audio e video in generale te lo confermo.»*
>
> ⛔ **The defect is not closed, and it is not a platform's**: it is `AUDIO_CUSCINO_MS = 250` in
> `pagina.html` (raised from 60 on 17 Aug to remove the gaps, with the price declared in the
> comment) plus the chain of capture, encoding and decoding. ⇒ `fasi/07-audio-e-appunti.md` §8.
>
> ⭐ **What this decision keeps**: on Chrome for Android **every stream is clean** — zero
> losses on every link, `[M]` twice. ⚠ What it does **not** keep is the reading *«and so there is
> nothing more to cure on the audio»*: a **synchronisation** defect does not appear in any counter
> that looks at one stream at a time, and this is the second time in five days that this phase
> produces four green links and a wrong experience (`LEZIONI.md` §2.7).

### 7.17 ✅ The session that never opens the control channel: **5 seconds**

> ## ✅ **FIVE SECONDS** — decided by the user on **11 Aug 2026**
>
> ⛔ **From the opening of the WebTransport session to the opening of the control channel at most
> 5 s pass**, then the server closes with `TEMPO_SCADUTO` `0x0D`. ⇒ `RCP.md` §4.6, the row that
> was missing.
>
> ⭐ **Why 5 s, that is the same number as the first cap**: opening the channel is the **first mandatory
> act** of the session (`RCP.md` §2.5), it does not depend on how fast a person types, and it does not
> depend on the network any more than the `CIAO` does.
>
> ⛔ **What it closes**: it was **the last way, in this phase, to occupy a slot without saying who
> you are**. ⚠ And QUIC's idle timeout did not cover it — that one counts **silence**, and a
> session that writes on another stream is not silent: it held the slot **indefinitely**.
>
> ### ⭐ And here the four decisions of 11 Aug fit together
>
> | | |
> |---|---|
> | **§7.15** | the control channel does not exist yet, so the `CONGEDO` **is not sent**: without the condition decided an hour earlier, this row would require a byte on a channel never born |
> | **§7.14** | and the reason travels where it always travels when the channel is not there: in the **application error code of the close** (§3.1 point 3) |
> | **§4.1-bis** | ⛔ it is a close decided by the server, and **it has its sayable reason**: `TEMPO_SCADUTO`. It is not a healthy session being thrown out — it is a session that never began |
>
> ⚠ **No new message type is needed**, and that matters: the window of §9 has been closed since 10 Aug
> 2026. `TEMPO_SCADUTO` was already there.
>
> ⛔ **And it remains to be measured**: `B6` gains a fourth case — open the session, do not open the channel,
> and check that at 5 s `0x0D` arrives **in the close code**, not on the channel. The bench does not
> have it today: until then this row is **written and not tested**.

*Raised on 11 Aug 2026 by a **measurement**, not by a reading: bench **B6** (finding **R12-A.25**,
and `FASI.md` §01-filo-nudo B6). It concerns `RCP.md` §4.6. The question as it was posed stays below.*

**The fact, and there are two.** B6 closed the `[?]` **R3.27** — *from which instant the first cap starts*
— and the answer is: **from the opening of the control channel**, not from the end of TLS. `RCP.md` §4.6
row 1 was corrected by that word on 11 Aug. ⛔ **But the bench gave a second answer,
and it says that curing the word is not enough**: if the stopwatch starts at the opening of the **channel**, whoever opens
the WebTransport **session** and never opens the channel **has no cap on them at all**. §4.6 has no
row for that state: the table starts from *«`CIAO` received»*, and before the `CIAO` there is a
state in which the server counts nothing.

| | **A — a fourth cap** | **B — no cap, and it is declared** |
|---|---|---|
| **what it says** | from the opening of the **session** to the opening of the **control channel** at most *N* seconds pass, then `CONGEDO(TEMPO_SCADUTO)` | that state is covered only by QUIC's idle timeout (30 s of **silence**), and §4.6 writes it down instead of leaving it implicit |
| ⛔ **what changes on the wire** | a `CONGEDO(0x0D)` arrives — on the channel that is not there, so **only** the code `0x0D` in the session close (§3.1 point 3) — where today nothing arrives | nothing arrives, and it is **what happens today**: the difference is that it stops being an omission |
| **the cost** | one more cap to measure, and a client slow to call the API sees the session closed as soon as it is opened | ⛔ a session that does not send `CIAO` but **keeps the wire busy** on another stream **never** expires: the slot stays taken |

**The concrete case, and it is not a lab one.** A page opens the WebTransport session, then the
browser goes into the background or the network drops between the two steps. With **A** the session dies with a readable
reason; with **B** it stays there until QUIC gets bored — and if something keeps writing on another
stream, it never gets bored. ⚠ It is the connection that *«holds a slot and declares it to
no one»*, that is the sentence §4.6 opens with: the section exists for this case and does not cover it.

⭐ **Which one seems more defensible to me, and the reason: A, with the same number as row 1 — 5 s.**
Not for symmetry: because opening the control channel is **the first mandatory act** of the
session (§2.5), it does not depend on the user, and it does not depend on the network any more than the `CIAO` does.
⛔ But it is a normative row that adds a cap to a conforming implementation, so **it stays ❓**
until you decide it: `RCP.md` §4.6 carries the row marked ❓ and refers here, and §12 lists it among the
things RCP/1 leaves open. ⭐ **No new message type is needed** — the reason is
`TEMPO_SCADUTO`, which is already there — and this matters, because the window of §9 has been closed since 10 Aug.

**How it closes:** a number, or *«no cap»*. With the first, §4.6 gains a row and B6 a case;
with the second, §4.6 still gains **the row that declares the state**, because a declared hole and
a forgotten hole cannot be told apart after three months.

### 7.21 ✅ ⭐ **REMOTIX puts the user in the card's groups** — decided by the user, 20 Sep 2026

*The user's question: «REMOTIX chiede che gli utenti appartengano ai gruppi video e render.
Normalmente le distro non ce li mettono, potrebbe essere un problema?» — and the answer is yes, today
that user **connects and sees nothing**: `[M]` 27 Aug 2026, 0 sessions out of 4 without the groups,
17 out of 17 with them. ⛔ And no error says so: one sees a blank page.*

**The cause, and it is structural:** on a normal desktop the permission on the `/dev/dri` nodes is given by logind
with an ACL (`uaccess`) to whoever occupies a **seat**. ⇒ A remote session has no seat on
purpose, so that ACL never arrives and **only the groups** remain.

**The user's decision, in two pieces:**

| when | who | what |
|---|---|---|
| **at installation** | `src/provisiona.sh` | enrols **all the people already on the machine** — `UID_MIN..UID_MAX` READ from `/etc/login.defs`, and only those with a real shell: service accounts stay out |
| **in operation** | the product (`figlio.c`, `iscrivi_ai_gruppi_della_scheda`) | every new user, **at the first connection**, is enrolled and their user manager reborn |

⛔ **And it changes a division that was written down** (I7: *«the product sets what concerns the SESSION;
accounts, groups, polkit and PAM live in `provisiona.sh`»*). From today the product touches the
groups too. ⇒ The two guarantees that keep the thing honest, and they are in the code:
1. it is done **after** PAM has said yes — nothing is granted to whoever merely knocks;
2. **every enrolment is written to the log**, with name and groups: a permission given in silence is a
   permission nobody remembers having given.

⚠ And the group names are not hard-coded: they are asked of the nodes (`stat -c %g`), because `video` and
`render` are the names of **this** distribution.

`[M]` 20 Sep 2026, box `kde`: user `senzagr` created without groups ⇒ with the previous binary
**zero frames**; with the new binary the log says «PRIMA CONNESSIONE: ce lo metto io»,
`id -nG` goes from `senzagr` to `senzagr video render`, and **105 frames** arrive. On the real
server, `provisiona.sh` enrolled **3 people** and `nicfio` went from `nicfio sudo` to
`nicfio sudo video render`.

⭐ **And IT HOLDS ON ALL DESKTOPS** — asked by the user on 21 Sep 2026 (*«deve funzionare per tutti i
DE, non solo per KDE»*) and measured on the 22nd. ⚠ There was nothing to extend: the enrolment sits in the
**parent**, before the `fork`, and the compositor does not even know about it — it was the **measurement** that stopped at
kde. `[M]` 22 Sep 2026, tenants without groups, **real browsers** with a real window
(`banchi/12-client-veri.py --visibile`):

| box | Firefox 140 | Chrome 153 | what the product did |
|---|---|---|---|
| **gnome** | ⭐ PASS (1st frame 1.6 s) | ⭐ PASS (1.2 s) | `id -nG`: `sgruppig`/`sgruppic` → `… video render` |
| **xfce** | ⭐ PASS (0.6 s) | ⭐ PASS (0.9 s) | `id -nG`: `sgruppix`/`sgruppiy` → `… video render` |

⛔ **And the safety net was not watching it**, because **every mesh gives its tenant the groups by itself**
(`garantisci_i_gruppi`): when the client arrives, the product has nothing left to enrol ⇒ the
safety net could be all green with this piece broken. ⇒ Mesh **C18**
(`banchi/11-scatole/11-c18-i-gruppi-li-mette-il-prodotto.py`), the only one that arrives **without** groups;
injected fault `--senza-usermod`. `[M]` 22 Sep 2026: GREEN and fault SEEN on gnome and xfce.

---

## 8. ✅ The decisions of phase 15 — the functional suite and the clean-up of round 1

*After round 1 of the suite (`fasi/15-suite-funzionale.md`, «Round 1»): 25 Sep 2026, morning.
Plus the KDE exception, decided on the evening of the 24th together with the phase.*

### 8.1 ✅ The KDE session is born empty — unless the user chose otherwise

Decided by the user, 25 Sep 2026 (defect **D-005**: after «Esci» Plasma reopened by itself the program
that was open, while the page promises a NEW session; `[R]` Plasma 6.3's reserve restore
on Wayland, `org.kde.plasma-fallback-session-restore.desktop`).

The remote KDE session starts **empty** by itself: `ksmserverrc` with `loginMode=emptySession` **in the
session's folder**, not in the user's settings. ⭐ But if the user has chosen in Settings
«ripristina la sessione salvata», **their choice wins** (option A of the proposals).
Cure: `aa4014d` on branch `bonifica-15`.

### 8.2 ✅ ⭐ The user's settings are not touched — except lock, reboot, suspend, stand-by

Decided by the user, 25 Sep 2026, in two steps:
- *«le impostazioni utente non si toccano»* — on no desktop;
- refined the same morning: *«Le impostazioni dell'utente non si toccano TRANNE quelle che
  riguardano blocco-schermo, riavvio sistema, sospensione e stand-by: queste sono impostazioni
  pericolose per altri utenti presenti sulla macchina»*.

| | where it is written |
|---|---|
| **screen lock, reboot, suspend, stand-by** | in the **user's** settings, persistent: dangerous for the other people on the machine |
| **everything else** (keyboard layout, menu entries, shortcuts, «Esci» visible, user switching, Ctrl+Alt+F…) | **only in the remote session**, on the four desktops; at the end of the session the user finds theirs again |

⇒ Three class B defects opened by the decision: **D-015** GNOME (the negotiated layout ended up in
`org.gnome.desktop.input-sources` of the user's dconf), **D-017** XFCE (the user's xfconf channels and
`~/.cache/sessions` deleted), **D-018** LXQt (`~/.config/lxqt/*.conf` and `Hidden` entries in
`~/.local/share/applications`). KDE was already fine (the session's `kxkbrc`). Cures: `ddcf28d`,
`85697c9`, `7543c6a`, `e8115e5` on `bonifica-15`; the test that watches over it is **F-031B**
(`banchi/15-suite/15-f031b-impostazioni-intatte.py`: the settings read from disk before login
and after «Esci»).

🔸 Derived (`7543c6a`): on XFCE Suspend, Hibernate and Hybrid Sleep in the «Esci» dialog count as
**suspend** ⇒ they are allowed, and stay in the user's channel.

### 8.3 ✅ The sentence for the dropped line

Decided by the user, 25 Sep 2026 (**D-002**: the line drops and the page stays frozen with the desktop, without
a word). When the transport closes without a CONGEDO, the page goes back to the form and says:

> *«il collegamento con il server si è interrotto: per rientrare scrivi di nuovo la parola d'ordine»*

Cure: `c7a67ea` on `bonifica-15`.

### 8.4 ✅ A server that is off is said at once

Decided by the user, 25 Sep 2026 (**D-009**: with the server off the page took 31 s to say «Non si
collega»). It is said **at once**, ~1 s, from the network refusal of `/impronta`, without waiting for the browser's 30 s
on WebTransport. 🔸 Only the network refusal: an HTTP status or an unreadable body stay as
before, and a slow server has no clocks (its answer is awaited). Cure: `e719d08` on `bonifica-15`.

### 8.5 ✅ ⭐ D-006: an Opus decoder of our own, in WebAssembly, for all browsers

Decided by the user, 25 Sep 2026. The defect: Firefox with a video in the session has short, repeated
sound gaps; Chrome does not. `[M]` 25 Sep, without the bench's ear, 60 s on lxqt and kde: Firefox+video
**3-5 re-arms**, Firefox without video 0, Chrome 0, Firefox+video in PCM 0 ⇒ Firefox's Opus decoder
(WebCodecs `AudioDecoder`). A first page-side cure was removed (`b40856d`): with real browsers
it made things worse.

The user: *«concordo sulla soluzione D [dichiararlo], ma il problema va risolto con la soluzione B
[decodificatore Opus nostro in WebAssembly nella pagina, per TUTTI i browser], che è la scelta che ci
consente di avere un prodotto bugs-free»*.

⇒ It is declared, **and** B is done: the Opus decoder in WebAssembly in the page, **for all**
browsers, not a branch for Firefox.
⛔ **Before round 2.**

### 8.6 ✅ The KDE exception on reattach at a different size

Decided by the user on **24 Sep 2026, evening**, opening phase 15 (`fasi/15-suite-funzionale.md`,
«The user's decisions»). On reattach at a different size (F-018, path C):
- on **GNOME, XFCE, LXQt** the canvas takes the new size and the desktop follows it (wallpaper, panel);
- on **KDE** the canvas stays the old one and **the browser rescales**: it is the **expected**, not a FAIL.

Confirmation by the user, for the suite, of the fallback of §5.0-bis (🔸 until today): KWin in Debian
stable (6.3.6; up to 6.7.4 no released branch has hot resizing) does not change size
with the session live, and restarting it would destroy the session. `[M]` round 1: F-018 and P-C **PASS** on KDE
with both browsers, with this expectation.

## 9. ✅ The decisions of phase 16 — stress and capacity

*Taken by the user on 25 and 26 Sep 2026. The account, the measurements and the evidence are in
`fasi/16-stress-e-capacita.md` (§2, §9, §17); here only the decision.*

### 9.1 ✅ The log goes into the system journal

With `--journal` the product also writes its **events** to the journal (`journalctl -t remotix`), with the
fields `REMOTIX_AREA`, `REMOTIX_INQUILINO`, `CODE_FILE`, `CODE_LINE` and the severity taken from the sign at the
head of the line (⛔ = error, ⚠ = warning). The **chatter** stays only in the file. The file stays for whoever
administers.

### 9.2 ✅ What the user types never enters the log

Neither characters nor key codes: it writes «a character», «key pressed/released». The code stays
only for **modifiers** and **mouse buttons**. It also holds for the non-producible character
(RCP §7.3): it is declared **that** there was one, not **which**.

### 9.3 ✅ The campaign: climb in steps, cap at 17, §9 thresholds

Steps 1 → 4 → 8 → 12 → 16 with bisection (not one user at a time); session cap at
**17** during the campaign, because the 17th is only the short control; §9 thresholds approved, with
video in proportion to its frequency and the browsers' memory recorded but not classifying.

### 9.4 ✅ Firefox draws with WebGL (anomaly A1) — decision of 26 Sep 2026, morning

The campaign measured that in Firefox the default drawing route (`bitmaprenderer`, chosen on 20
Aug 2026 against the 2D canvas squares) reads every frame back from the GPU (~34 ms at 4K) and drops
11–50 % of frames already with one user. The user chose to **cure now** (WebGL2 route)
instead of closing the campaign with the defect declared: short suite + canvas tests + **his own look
for the squares**, then the affected climbs are redone.

### 9.5 ✅ The Radeon's 4K slowdown (A3) is the driver's: it is documented, not worked around — 29 Sep 2026

With frequency, VPP, compositor barrier and EFC ruled out by measurement, the delay sits inside the VCN's
encoding (groups of 5 frames at ~31 ms, one session at a time). The user's word: *«è fuori dal
nostro ambito. Se in futuro il problema dovesse essere risolto allora REMOTIX diverrà più capace di
reggere un maggior carico»*. ⇒ No workaround in the product; the Radeon's 4K is declared limited
by the driver; the defect is documented in every detail in `fasi/16-a3-radeon-vcn.md`, so that
the user can decide to help the driver's developers.
Addition of 29 Sep 2026: Mesa 26.1.6 does not cure it (100 and 102 slow against 100 and 105). The user's word:
*«stiamo andando fuori scope, questo è un problema dei driver AMD, non di REMOTIX. Aprirò a questo scopo
un progetto apposito»*. ⇒ In REMOTIX the work on A3 closes here: no minimal reproduction (§6.2 of the
dossier) nor other experiments; the dossier and the `a3-esperimenti` branch are the starting point of the new project.

---

### 9.6 ✅ REMOTIX's official logo — 29 Sep 2026

The user's word: *«è il logo ufficiale del progetto»*. ⇒ `grafica/logo/remotix-logo.png`
(PNG 2172×724, sha256 `192ce831…384104`), at the top of `README.md`. It is the original: the variants
(icon, favicon, dark version) are derived from it, they do not replace it.


## 10. ✅ REMOTIX on Linux in general, and the installer — 29 Sep 2026

### 10.1 ✅ Not only Debian: first a survey of the distributions

The user's word: *«al momento REMOTIX è stato sviluppato su Debian Trixie, ma l'obiettivo è farlo
girare su Linux in generale. Per ottenere questo risultato, e quindi avere basi solide per costruire
l'installer, è necessario fare un'indagine approfondita sulle principali distro»*. Families:
Debian/Ubuntu (and Mint), Fedora/RHEL (Rocky, Alma), Arch (Manjaro), openSUSE (added in the survey).
⚠ Already seen in the code: `src/remotix.pam` uses `@include common-auth`, which exists only on Debian and Ubuntu.

### 10.2 ✅ The installer is professional, of absolute excellence

The user's word: *«REMOTIX dovrà essere dotato di un sistema di installazione professionale, di
assoluta eccellenza»*. ⇒ It is a product requirement, not a finishing touch: the installer is designed
on the survey of §10.1 and on how the best products install, and it is measured like the rest.

### 10.3 ✅ The installer tests in virtual machines, one per desktop

The user's word: *«stavolta non dobbiamo misurare le performance, ma il corretto funzionamento
dell'installer, quindi la potenza bruta della GPU non serve. Passiamo dai container alle VM»*; and *«4 VM
distinte, esempio Ubuntu/GNOME, Ubuntu/KDE, Ubuntu/XFCE, Ubuntu/LXQt»*. ⇒ `fasi/17-l-installatore.md` §7.

### 10.4 ✅ The installation engine in eight phases

The user's proposal, adopted: PREFLIGHT · COMPATIBILITY · PLANNING · CONSENT & SAFETY · ACQUISITION ·
INSTALLATION & CONFIGURATION · VERIFICATION & CERTIFICATION · COMMIT / ROLLBACK. With three rules: phases
5-6 are carried out by the distribution's package manager; going back is ours (log of
actions); consent can come from a file. Strengthened at the user's request (*«migliorala nei punti
che ritieni deboli»*): phase 0 TRUST, three compatibility outcomes per desktop, the plan as a document
with «do / verify / undo» for each action, nothing is installed before everything is downloaded,
switch-on between static and live verification, resumption of an interrupted operation. ⇒ `fasi/17-l-installatore.md` §6.0.

### 10.5 ⛔ SUPERSEDED by §10.31 (5 Oct 2026), for the GUI — TUI and GUI are indispensable

The user's word: *«su TUI e GUI dico che è un requisito irrinunciabile»*. ⇒ Three interfaces (CLI, TUI,
GUI) on a single engine, no installation logic in the interfaces, the GUI as the user with
polkit. The tool is decision D12. `fasi/17-l-installatore.md` §6.6.1.

### 10.6 ✅ Missing dependencies are brought by REMOTIX — with one exception and one boundary

The user's word (29 Sep 2026): *«usiamo questa regola generale per non impazzire: se ci sono
pacchetti/dipendenze assenti da una particolare distro, REMOTIX le deve includere e/o scaricare»*.

- **The rule**: a library or a tool REMOTIX needs, **missing or too old** in the
  distribution, is brought by REMOTIX (inside the binary or in its package). If the distribution has it
  right, its own is used (security updates are its). ⇒ **D2 closed: yes**, ngtcp2 and nghttp3
  inside, with the security updates our burden.
- ⛔ **The exception: patented codecs** (H.264: x264, full ffmpeg, Mesa with the codecs). REMOTIX neither
  includes them nor downloads them by itself — that would be distributing them; they stay with the recognised external repository (RPM
  Fusion, Packman) added by the engine **with consent** (D5).
- ⛔ **The boundary: the desktops.** A desktop the distribution does not have (XFCE and LXQt on Alma/RHEL) is not
  brought by REMOTIX: that combination stays out of the matrix.

### 10.7 ⛔ *(superseded by §10.36)* Without a desktop: either it is installed (with consent), or REMOTIX does not install

The user's proposal (29 Sep 2026), adopted: *«se REMOTIX non trova nessun desktop installato, o chiede di
installarlo all'utente oppure REMOTIX non si installa»*. The desktop comes from the distribution's
repositories, is installed without a local login screen or graphical boot, and is declared as a
«best effort» action. `fasi/17-l-installatore.md` §6.6 and R38.

### 10.8 ✅ Ubuntu 24.04 out: we start from 26.04

The user's word (29 Sep 2026): *«partiamo dalla 26.04»*. On 24.04 only GNOME would have been possible, at the
price of bringing in OpenSSL 3.5 (and its security updates) and of two adaptations for
ffmpeg 6.1 and libei 1.2. Mint 22 stays out with it. The matrix goes down to 26 machines.

### 10.9 ✅ The principle: a new product, on new-generation technologies

The user's word (30 Sep 2026): *«la scelta di lasciare fuori certe versioni delle distro è coerente con
lo spirito del progetto: si tratta di un prodotto nuovo che adotta tecnologie di nuova generazione, è una
scelta di design netta»*. ⇒ Wayland, QUIC/WebTransport, the desktops in the versions that support them; no
X11 nor fallback libraries to chase old versions.

And the life cycle, so that the choice stays clean over time:
- a new version of a distribution **enters** the matrix when it has the minimum components
  (`fasi/17-l-installatore.md` §3.1) and passes the round on the VMs;
- a version **leaves** when the distribution stops updating it: no support beyond the life given to it
  by whoever makes it.

### 10.10 ✅ The rate: one version a year for new features, maintenance when needed; and automatic updates

User's words (30 Sep 2026): *«la mia intenzione è quella di aggiornare REMOTIX almeno una volta
l'anno»*; and, given the distributions' rates: *«bisognerà pensare per REMOTIX ad una funzione di
auto-aggiornamento in base alla distro su cui è installata»*.

- **Two tracks**: the **annual version** (new features, full suite and full round on the VMs) and the
  **maintenance updates** with no new features, when needed: security fixes for the libraries that
  REMOTIX brings inside (§10.6), rebuilds for the rolling-release distributions (Arch, Tumbleweed:
  every ffmpeg change), and the signed **catalogue** — which updates by itself, without a new REMOTIX, and lets
  the distributions' new versions in mid-year.
- **Automatic updates go through the distribution's package manager**, fed by our
  signed repositories (T8): ⛔ REMOTIX does not download or replace its own binary by itself (two truths about what
  is installed, and a target). A REMOTIX timer checks the repository and the catalogue every day; every
  update goes through the path that does not close the desktops (T7).
- 🔸 **D14, open**: what applies by itself — proposal: security and rebuilds automatic, the annual
  version at the administrator's choice; alternative: notice only.

### 10.11 ✅ Flatpak and AppImage set aside: native packages from our repository

The user's word (30 Sep 2026): *«accantoniamo l'idea flatpak/appimage. Continuiamo sulla strada originale,
alla fine mi sembra quella più semplice e coerente»*. ⇒ REMOTIX is distributed in **native packages** in the
**signed REMOTIX repositories** (all the material from us, installed by the distribution's package
manager); the installer directs, it does not copy files. A study on Flatpak/AppImage had started and was
stopped. ⚠ Still to be looked at, at decision D9 (immutable distributions), the systemd route made for
system services (`systemd-sysext`, portable services).

### 10.12 ✅ The installer is the only way to install REMOTIX

The user's word (30 Sep 2026): *«l'unica via per installare REMOTIX è l'installer»*. Since a package
in a repository can always be installed by hand, the rule is enforced **by construction**:
1. **the package carries only the pieces, inert**: program, page, configuration files; it does not switch on the
   service, does not touch groups or firewall; the three belts are in it **switched off** (in `/usr/share/remotix/`), the
   engine activates them with consent (D4);
2. **the installer assembles the pieces** (groups, belts, firewall, desktop, switch-on) and everything goes through
   **its** log: a single trace, a cleaner uninstall;
3. **only two ways: the installer, or the source code by hand** (download the code, look for the
   dependencies, install them, bring up the services, configure them — at one's own risk). The user's word, 30
   Sep: *«o usa l'installer o deve scaricarsi il codice a mano, andarsi a cercare i pacchetti con le
   dipendenze e installarseli, tirar su i servizi, configurarli»*. ⇒ REMOTIX provides no middle way:
   **neither blocks nor dedicated options** for whoever starts without the installer (corrected twice on 30 Sep: first
   it was a flat refusal, then an explicit option). Only a piece of information for support remains: `remotix
   stato` says whether the installation is **certified by the installer** or not;
4. **automatic updates stay** (§10.10): the package manager updates the pieces, then calls
   the installer, which verifies and switches back on without closing the desktops.

### 10.13 ✅ REMOTIX will be open source

The user's word (30 Sep 2026): *«REMOTIX sarà opensource»*. Consequences to be decided in due course:
🔸 **the licence** (GPL or permissive; it also weighs on the codecs: x264 is GPL, `DECISIONI.md` ~§5113 had already ruled out
x265 as a fallback); **D10** (where the packages are built): with a public project
openSUSE's OBS becomes possible; **D11** (the key): public trust requires a well-guarded root key.

### 10.14 ✅ The installer is a single, monolithic program

The user's word (30 Sep 2026): *«l'installer è un programma che non chiama altri sottoprogrammi strani. È un
sistema complesso e monolitico»*. ⇒
- **a single executable** (`remotix-install`): engine, CLI, TUI and GUI; no scripts or helper programs
  of ours;
- it talks with the system's services (systemd, logind, firewalld, polkit) **from the inside**, through their
  official interfaces (D-Bus), without launching programs;
- **a closed list of system programs** is launched only where there is no stable interface: the distribution's
  package manager (`apt`, `dnf`, `zypper`, `pacman` — engine rule 1) and the group
  commands (`usermod`, `gpasswd`); with the full path, fixed arguments, every call in the log;
- **the GUI** runs as the user (not as root: Wayland), and for administrator operations the same
  executable **relaunches itself** with the permissions asked of polkit — one file, two roles.

### 10.15 ⛔ *(superseded by §10.35)* The installer speaks Italian and English, according to the system language

The user's word (30 Sep 2026): *«l'installer lo rendiamo bilingue: italiano e inglese. La scelta della
lingua la rendiamo coerente con le impostazioni linguistiche dell'OS sottostante (variabili di ambiente)»*.
⇒ the language is read in the standard order `LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`: Italian if the first
one given is Italian, **English in all other cases** (German, French… too); ⚠ when the installer
relaunches itself with the permissions (polkit cleans the environment) the chosen language is **passed explicitly** to the
administrator part; in an unattended installation the answer file can fix it. The `RX-…` **codes**
stay the same in both languages: they are the ones looked up in the manual and in support.

### 10.16 ✅ Uninstalling: the administrator warns, the installer closes the REMOTIX sessions and cleans up

The user's word (30 Sep 2026): *«è un'operazione fatta dall'admin del server. La soluzione più pulita è che
l'admin avverta gli utenti nelle modalità classiche (email, WhatsApp…). Poi, quando avvia la
disinstallazione, l'installer chiude le sessioni REMOTIX degli utenti e i loro processi e avvia la pulizia
del sistema»*. ⇒ No warning system in REMOTIX and **no extra question**: whoever is still connected is
simply closed (*«erano già stati avvertiti prima»*); the plan carries only the row «close the REMOTIX
sessions still open (N)»; the REMOTIX sessions and the programs born inside them are closed, **not** the user's other
processes (a local or ssh session of theirs stays). `fasi/17-l-installatore.md` §6.5-bis, R43.

### 10.17 ✅ A system to warn connected users: a separate project, outside REMOTIX

The user's word (30 Sep 2026): *«la disinstallazione mi ha fatto venire in mente che serve un sistema per
avvisare gli utenti collegati a un sistema. Ma questo è un progetto a parte che non riguarda REMOTIX»*. ⇒ In
REMOTIX no warnings (§10.16). Note for that project: REMOTIX sessions are normal desktops, so a
warning on the user's desktop would reach them without REMOTIX knowing anything about it.

### 10.18 ✅ D3: REMOTIX mirrors the system's authentication (PAM), account lockout included

The user's word (30 Sep 2026): *«non voglio che REMOTIX si disallinei rispetto all'autenticazione di default
del sistema, deve rispecchiare PAM»*. ⇒ REMOTIX's PAM file uses **the same stack as the distribution's standard
remote login** (ssh's: `system-remote-login` on Arch, `password-auth` + `postlogin` on
Fedora/Alma, `common-*` on Debian/Ubuntu/openSUSE), with what it contains: `pam_faillock` where the
distribution has it (the risk of remote account lockout remains, the same as ssh's, governed
by the administrator in `/etc/security/faillock.conf`), and **`pam_selinux` on Fedora/Alma like ssh** ⇒ the
SELinux refusal of the child is cured with a **REMOTIX SELinux rule** (like Cockpit), not by removing the line (T6). REMOTIX's
per-address ban (§1.9: 3 failures in 5 minutes ⇒ 12 hours) stays, in addition. The only intended
difference: **root excluded**, like default ssh (`PermitRootLogin` without password) — ✅ confirmed by the user:
*«che root non entri da REMOTIX è corretto, è lo stesso sistema di sicurezza di ssh»*.

### 10.19 ⛔ SUPERSEDED by §10.31 (5 Oct 2026) — D12: the installer's window is drawn with Gio, inside the same program

The user's choice (30 Sep 2026), among three routes: embedded Chromium (independent, but two programs and a
web engine to maintain), the distribution's WebKitGTK (a dependency, the program no longer single), **Gio**, a
Go library for interfaces that draws everything by itself — *«ok per Gio»*. It comes from a proposal of his: *«schermate
con un motore di rendering integrato, così da rendere l'installer indipendente dai browser dell'utente»*. ⇒ The
GUI lives in the same program as the engine, identical on the four desktops, without a browser; the screens are not
HTML but are rewritten in Go **from the prototype** (colours, fonts, layout, common words, «password»). The
TUI, in the terminal, with a Go library in the same program. ⚠ To be verified during the build: Gio under
Linux uses the system's graphics libraries (Wayland, X11, EGL) — the engine must keep starting even on
a machine without a desktop (where the TUI is used).

### 10.20 ✅ D5, D6, D8, D13 — user's words (30 Sep 2026)

- **D5**: *«si chiede il consenso e si installa. Se l'utente nega il consenso allora REMOTIX non si installa»* ⇒
  where an external repository is needed for encoding (RPM Fusion, Packman, EPEL), consent is required; a «no» ⇒
  BLOCKED, nothing touched.
- **D6**: *«l'installer apre la porta che l'utente ha scelto sul firewall (per il router ovviamente non può essere
  REMOTIX a pensarci, a meno che non vogliamo supportare UPnP)»* ⇒ the port is opened on the machine's firewall;
  the router stays with the administrator (UPnP: see the note below).
- **D8**: *«l'utente vede il desktop originale di Ubuntu (o altrimenti saremo costretti a implementare un nostro
  session manager)»* ⇒ on Ubuntu the **`ubuntu`** session (the one seen in front of the monitor), not «vanilla»
  GNOME: REMOTIX starts the distribution's **default** GNOME session; no extra `gnome-session`.
- **D13**: *«di base sì, ma potremo farci dei piccoli miglioramenti»* ⇒ the prototype is the basis of the GUI.

⚠ Note on UPnP (D6): opening a port on the router by itself would make the server reachable from the internet without
the administrator having decided it, and many routers keep it off for security ⇒ proposal: **no UPnP**; the
welcome says which port to forward on the router, TCP and UDP.

### 10.21 ✅ D11 simplified: a single key, the repository's

User's words (30 Sep 2026): *«stiamo complicando le cose. L'installer originale che l'utente scarica avrà
un codice sha256 che l'utente potrà controllare … per i pacchetti l'installer usa il package manager del
server»*; and *«i dati dell'installer restano su un nostro repository, così siamo al sicuro»*. ⇒
- **a single key**: the one that signs REMOTIX's packages and repository — indispensable, because apt, dnf,
  zypper and pacman refuse an unsigned third-party repository;
- **the second chain goes** (engine and catalogue signed separately, subkeys, revocations): the installer downloaded
  by hand is verified with the published **sha256** (HTTPS); the **catalogue** travels inside the
  `remotix-install` package and updates like every package, from our repository;
- only **where that key is kept** and its backup copy remain to be decided: together with D10.

### 10.22 ⛔ SUPERSEDED by §10.30 (5 Oct 2026) — The licence: PolyForm Noncommercial — companies' internal use is forbidden too (30 Sep 2026)

> ⛔ **Superseded on 5 Oct 2026 (§10.30)**: the code becomes closed, with a trial and a paid full version. What
> concerns ffmpeg here (removed in phase 18) and the choice to proceed without a lawyer stay valid.

✅ **Confirmed by the user**: *«PolyForm Noncommercial mi sembra adatta ai miei obiettivi attuali»*. The
`LICENSE` file is put in at publication time, with the **official text copied without changes** from the
PolyForm project's site. The milestone to remove ffmpeg stays: it is the condition for the licence not to clash with the GPL.

User's words: *«REMOTIX è un prodotto opensource. Si può usare liberamente e redistribuire liberamente.
Il codice si può modificare e redistribuire ma citando progetto/codice originale. È vietato l'uso
commerciale. Il codice non può essere modificato e redistribuito a pagamento»*; *«le aziende non possono
usarlo come strumento di lavoro, ne trarrebbero un vantaggio economico»*; *«non voglio accollarmi le spese per
un legale»*.

- ⚠ A licence with a commercial ban **is not «open source»** according to the official definition (OSI): it is
  «source available». The name to use must be chosen accordingly.
- **The licence**: **PolyForm Noncommercial 1.0.0**, the original text **without changes** (written by
  lawyers, free, made for software): use, modification and redistribution for non-commercial purposes, with
  credit to the original; forbidden to companies as a work tool and sale forbidden.
- ⛔ **The conflict with ffmpeg**: REMOTIX uses the distribution's libavcodec, built under **GPL** on
  Debian, Ubuntu, Arch and with RPM Fusion/Packman; a non-commercial licence is not compatible with the GPL. ⇒
  **New milestone (after the installer is closed): remove ffmpeg from REMOTIX** — encoding on the card
  directly with **libva** (MIT), the software fallback with **OpenH264** (BSD) in place of x264. After that, all the
  dependencies are permissive (MIT, BSD, Apache) and the licence — like a possible sale of the product —
  has no more conflicts.
- **Without a lawyer** (the user's choice): only unmodified standard licences, no GPL dependency, the
  components' licence file generated from the SBOM, and a standard agreement for whoever contributes (to remain
  owner of all the code, a condition for a sale). Low residual risk, declared.
- A **sale** of the product transfers the rights on **our** code; ffmpeg is not ours and, once the
  dependency is removed, it does not touch it. The codec **patents** (H.264, HEVC) remain a separate matter for whoever
  sells.

### 10.23 ✅ D14: REMOTIX updates with the system — no update system of our own

User's words (30 Sep 2026): *«una volta installato sul server un apt upgrade si occupa del resto dei
pacchetti»*; *«resta solo la questione di rigenerare l'installer»*. ⇒
- REMOTIX (and the `remotix-install` package) are updated **when the administrator updates the system**
  (`apt upgrade`, `dnf upgrade`, `zypper up`, `pacman -Syu`), or with the distribution's automatic updates if he
  has turned them on — like every other program on the server. **The timer** `remotix-aggiorna` **goes**, and so
  does the question «what updates by itself» (replaces §10.10, the «automatic update» point).
- What stays in the **package**: the restart that does not close the desktops (T7); on Arch/Tumbleweed the tie to
  ffmpeg's soname that blocks an incompatible update until we rebuild; going back with the package manager's
  commands.
- **At every version**, a single release command: rebuild the packages of the three families, rebuild the
  installer (the two builds) and publish its sha256, update the catalogue (inside `remotix-install`), sign and
  publish the archive (on the VPS, D10).

### 10.24 ✅ Updating belongs to the system, and to the administrator — not a REMOTIX problem

User's words (30 Sep 2026): *«un admin avvisa gli utenti che il giorno X verrà effettuato un
aggiornamento del sistema, quindi gli utenti collegati potrebbero aspettarsi delle interruzioni del servizio.
L'aggiornamento del sistema dev'essere un problema di REMOTIX? Secondo me no»*; *«io parlerei di
aggiornamento del sistema, non di REMOTIX»*. ⇒ When and how to update, and warning the users (also with
**AMS**, the user's separate project: messages from administrators to users with read receipt), belong to the
administrator. All that is left to REMOTIX is **not to close the desktops by itself** when its package is
updated along with the rest (R7, already guaranteed by T7). **R8 (the time threshold) is removed.**

### 10.25 ✅ Priority: remove ffmpeg, before T10 — and the tests with maximum parallelism

User's words (30 Sep 2026): *«se togliere ffmpeg non comporta impatti su REMOTIX leviamolo pure»*; *«con
la sostituzione di ffmpeg dovremo rifare tutti i test: di funzionalità e di performance»*; *«diamo priorità a
ffmpeg, a condizione che i test vengano svolti, dove possibile, con il massimo parallelismo. Per i test
funzionali vanno bene 4 scatole con i 4 DE»*. ⇒ **Phase 18** (`fasi/18-senza-ffmpeg.md`): libva directly for
encoding on the card, OpenH264 and SVT-AV1 for the software fallback, libopus directly, colour conversion
without libswscale. **Condition**: it goes in only if indistinguishable — phase 15's full suite green on the 4
boxes in parallel, phase 16's campaign (one configuration at a time: performance is not measured in
parallel) with latency and quality equal to today; otherwise ffmpeg stays and the licence is reopened. Then
the installer adapted to the new dependencies, and **T10 only once** on the final product.

### 10.26 ✅ Phase 18: the user's choices of 30 Sep

- **Performance measurements leave the documents** (*«con questo cambio architetturale i numeri sono
  completamente invalidati»*): at once from the product documents; from the diary once phase 18 succeeds. The
  thresholds stay as **project targets**, not measured promises (SPECIFICHE §3).
- **D5 stays**: a «no» to the driver repository (RPM Fusion, Packman) blocks the installation even without
  ffmpeg, when video could go in software.
- **No AV1 as last fallback**: without a card and without a real OpenH264 (the installer always puts it
  there) REMOTIX **declares it** at startup with the remedy; the browser does not receive codecs the server
  cannot do.
- ✅ **H.264 stays** (user's word, 30 Sep): the original reason (Firefox for Android) fell with §7.18,
  but **Firefox on Linux** does not decode HEVC and works in H.264; without it, it would have only AV1, which the
  server's Intel cards do not encode. H.264's patents remain a matter for whoever sells (§10.22); OpenH264 is
  BSD and works only without a card.
- ✅ **Only the two measurements the change touched are repeated** (user's word, 30 Sep): the relative
  old/new comparison, same machine and same images, for encoding **without a card** and for the card
  with the pixels **from memory**. Zero copy turned out identical (bytes, quality, encoder times) and
  is not measured again; the rest of the performance tests stay removed.
- ✅ **OpenH264's limits are not product limits** (30 Sep, checked against the SPECIFICHE): no lossless
  and H.264 without a card up to 4096×2304 — the SPECIFICHE ask for 4K and do not mention lossless.
  They are differences from x264, not from the requirements.

### 10.27 ✅ The card is used ALWAYS, NVIDIA included — the user's requirement (1 Oct 2026)

User's words: *«io avevo chiesto una cosa sola: che remotix sfruttasse l'accelerazione hardware della
macchina su cui viene installato»*; *«non è accettabile che un utente abbia una 5070 e si ritrova con remotix
che gira su CPU»*. ⇒ **Requirement**: on a machine with a card able to encode H.264/HEVC, REMOTIX
encodes **on the card**, whatever the vendor. Today Intel and AMD yes (VA-API); **NVIDIA no** (the proprietary
driver does not encode via VA-API: it fell back to the processor, already before phase 18).
- 🔸 Proposal (to be confirmed): **NVENC** for NVIDIA, opened on demand like OpenH264 (MIT headers,
  NVIDIA driver library); VA-API stays for Intel and AMD; the processor only without a capable card.
  Vulkan Video discarded for now: `[M]` 1 Oct, Vulkan encoding is there on the Radeon (RADV, Mesa 25.0) but on the
  Intel UHD 770 only behind `ANV_DEBUG=video-encode` even with Mesa 26.2.3 (experimental).
- ⚠ A real NVIDIA is needed to try it: there is none in the lab.
- ✅ **Vulkan first** (user's word: *«la codifica deve avvenire con strumenti standard, preferibilmente
  con Vulkan, che accomuna tutte e 4 le architetture»*): the route is chosen **by capability**, not by vendor —
  1) Vulkan Video if the card offers it (today AMD, NVIDIA; Intel when Mesa makes it stable), 2) VA-API
  (today Intel, integrated and Arc). NVENC discarded. 🔸 the experimental option `ANV_DEBUG=video-encode` on Intel
  only as a trial, not by default.
- ✅ **No processor** (user's word: *«niente cpu senza scheda. Ad oggi anche le vm possono supportare
  accelerazione hw»*): the software fallback goes (`src/ripiego.c`: OpenH264, SVT-AV1), with its dependencies and
  repositories (Cisco, `noopenh264`, EPEL for SVT-AV1); without a capable card REMOTIX **does not install** — the
  preliminary check says so first, with the reason. VMs with a passed-through or virtual card (passthrough, vGPU)
  work; VMs without a card do not. ⇒ T10's VMs test only the clean refusal; the full tests in the containers
  with the real card (as in §7.5 of phase 17).
- ✅ **The canvas at most 4096 pixels wide** (user's word: *«4096 max di larghezza va benissimo, non ho
  mai preteso di più (è anche superiore al 4K, che ha larghezza massima di 3840)»*): H.264 on the Intel card
  stops there and Firefox receives only H.264. A larger window receives the canvas reduced to the maximum, not a
  refusal. ⛔ 3K as the maximum was proposed and discarded (it removes neither licence nor compatibility problems;
  it makes 4K monitors worse).
- ✅ **The Red Hat family stays** (Red Hat, Alma, Rocky; user's words: *«il problema delle licenze è di chi
  installa remotix, non del progetto»*; *«va bene, ma sarà meglio annotare bene queste limitazioni»*): only **Intel**
  (with RPM Fusion EL and EPEL, with the D5 consent), only **GNOME and KDE**; ⛔ **AMD not supported** (RPM Fusion
  does not have the AMD driver with encoding for EL; on Fedora it does). Tested on Alma. Full table:
  `SPECIFICHE.md` §11.4-bis.
- ⚠ **NVIDIA**: the user cannot buy the card; the Vulkan route stays «untested» until it is tried
  (a rented machine, at his choice, or a user who has one).
- ⭐ **Android**: Chrome on Android joins phase 19's suite (emulator on the server); Firefox Android stays
  out (§7.18).
- ⇒ **Phase 19** (`fasi/19-nvidia.md`). Phase 18's redone measurements stop where they are (user's
  word: *«basta misure»*).

### 10.28 ✅ The phone's keyboard opens only on request — the user's choice (2 Oct 2026)

Words of the choice: *«Tastiera solo a richiesta»*. `[M]` 2 Oct, S23+ with Chrome 154, phone in hand: the
on-screen keyboard opened by itself (the hidden paste field always stays focused) and covered half
of the desktop for 60 % of test F-031; and it typed nothing, because in touch mode nobody listened to the
keys. ⇒ **The keyboard no longer opens by itself; a control opens it when needed**, and what is typed
reaches the desktop as in §7.3 (letters as letters).
- The control is a small **⌨ button at the top right**, only with the phone in hand (touch layout): it can be
  discovered without a manual, and with the trackpad model it covers no desktop targets. A gesture from the table in
  `SPECIFICHE.md` §7.2 was discarded because it cannot be discovered by itself. On the computer and on DeX with a
  mouse nothing changes.

### 10.29 ✅ On DeX pointer capture turns on at the first click — the user's choice (3 Oct 2026)

Words of the choice: *«per migliorare l'usabilità in android la cattura meglio attivarla al primo clic del
mouse»*, and at the end of the test: *«considerando i limiti di Android direi che abbiamo raggiunto un risultato
eccellente»*. `[M]` 3 Oct, S23 (Android 16) on DeX, Chrome 154 and Samsung Internet 30, Radeon and Intel: without
capture the position arrives only on click or with a button held (noVNC #1727, Android's on Samsung) and the double
resize arrow never appears; with capture the movements with buttons up arrive and the edge can be
dragged. ⇒ **The first click on the canvas captures the pointer where hover does not arrive** (no movement with
buttons up before the click, or the last one at least 8 px from the click: no branch per system, Samsung Internet on
DeX declares itself Linux); **you leave by pushing past the edge** (160 CSS px of push, so the hot corners stay)
**or with Esc**, and the next click captures again. On computers hover arrives and it never fires. With capture the
page draws the arrow.
- `[?]` To be retried when Google releases Android's desktop mode (the user's observation, 3 Oct):
  the rule looks at behaviour and not at the system, so it adapts by itself (hover that arrives ⇒ no
  capture); to be measured there: whether Chrome grants `Pointer Lock` and whether shortcuts reach the page.

### 10.30 ⛔ *(superseded by §10.33)* REMOTIX becomes closed source, with a trial and a paid full version (5 Oct 2026)

> ⭐ **The rules in force are in `SPECIFICHE.md` §15** (9 Oct 2026). The history stays here: some items
> below were superseded by later decisions.

User's words: *«voglio rendere il prodotto utilizzabile in versione trial limitata e in versione full solo
dopo aver acquistato una licenza di utilizzo»*; to the question «does only whoever uses it for work pay (A), or does
everyone pay and the code becomes closed (B)?» he answered **B**.

- **Why an either-or**: with public, modifiable code (PolyForm Noncommercial, §10.22), a private person
  could legally remove the trial's limit. A limit that makes people pay holds only if the code is closed.
- ⇒ **§10.22 is superseded**: no public code, no agreement for contributors. The repository
  `github.com/nic-fio/REMOTIX` is already private.
- ✅ **No obstacle from the dependencies**: ffmpeg left in phase 18. The remaining dependencies (MIT, BSD,
  Apache) allow a closed product; they only ask that their licences travel with the product (the file
  generated from the SBOM, already planned).
- ⚠ **What closed code does NOT prevent**: the binary runs on the customer's machine, and someone
  determined can modify it. The licence check keeps honest customers honest, it does not stop those who copy.
- ⚠ **Without a lawyer** (the choice of §10.22): for the trial there is a standard text written by lawyers, the
  **PolyForm Free Trial 1.0.0** (trial for 32 days). For the paid full version there is **no** equivalent
  PolyForm text: the sales contract remains to be chosen.
- ✅ **The trial: 1 user, 30 days** (user, 5 Oct). *«Scaduti i 30 giorni al login compare una finestra di
  licenza scaduta e di acquistare il prodotto»*. ⇒ after expiry **you cannot get in**: the login page, with
  correct credentials, shows «licence expired» and the link to buy. The program enforces the 1-user
  limit.
  - The count starts from the **server's first start**; the date is kept in `/var/lib/remotix`, and the program
    also remembers **the last date seen**: if the clock goes back, the more recent one counts.
  - The window appears **after** correct user and password: whoever has no account does not discover that the
    server is unlicensed.
  - ⚠ Declared: whoever deletes `/var/lib/remotix` and reinstalls starts again from zero. The trial's contract
    (PolyForm Free Trial 1.0.0, 32 days) remains the legal defence.
- ✅ **Unlocking is done from the login page** (user, 5 Oct): *«se la licenza è scaduta sulla stessa
  finestra si apre un secondo campo dove viene inserito il codice di licenza; il sistema verifica la validità
  del codice e passa il controllo al modulo di accesso»*. Sequence: correct user and password ⇒ licence
  expired ⇒ the code field appears ⇒ valid code ⇒ you get in. Claude's additions:
  - the field also opens **during the trial** («Have a licence code?»): whoever buys earlier, or adds
    users, does not wait for the expiry;
  - the code is **signed** and is verified **without a network** (the public key is in the program, the private
    one only with the seller): it is ~100 characters long, **it is pasted** from the email. A short code to type
    would need a verification server of ours, excluded.
- ✅ **What the login page shows, in the three states** (Claude's counter-proposal, accepted by the user on 5 Oct:
  *«uno potrebbe decidere di acquistare il prodotto anche solo dopo 2 giorni di utilizzo»*):
  - **trial**: the caption «Trial version — N days left» (even before the credentials: it is harmless) and the
    link «Have a licence code?», which opens the field;
  - **valid licence**: no caption and no field; only a small link «Change licence», for whoever
    adds users;
  - **licence expired**: the code field already open.
  - ⛔ The greyed-out field was discarded: in the trial it would prevent buying before expiry, with the licence
    it would take space without serving.
- ✅ **The technical cap and the commercial cap are two things** (user, 5 Oct): *«tecnicamente il prodotto ha come
  limite superiore 16 utenti, ma nessuno vieta di usare remotix con un numero di utenti maggiore se dispone di un
  server ultrapotente»*. ⇒ The licence says **N users or «unlimited»**, without tying itself to 16. The number
  of users who actually connect is the lower of the licence and what the machine can carry.
  - ⚠ The technical work that follows: today 16 is **fixed at compile time** (`MAX_ATTACCATE` in
    `src/rcp.c`, §1.11). To go beyond it on a powerful server it must become a limit decided at
    startup, from the card and the configuration.
- ✅ **Capacity is declared, not limited** (user, 5 Oct): *«si documenta che su una certa configurazione
  il sistema garantisce un utilizzo ottimale fino a X utenti, poi comincia la fase di degrado. Chi acquista sa
  cosa aspettarsi … sarebbe impossibile testare ambienti enterprise, dovrei quantomeno affittare un
  datacenter»*. ⇒ A public table, **one row for each machine measured**: users with optimal use, and where
  degradation starts. ⛔ Only machines really measured, with their hardware declared.
  - ⇒ **The plan of performance measurements** (first job after phase 19) also measures **the users
    curve** on Intel and Radeon: they are the table's first two rows.
  - ✅ **The capacity test for the customer is a program of its own, next to the server** (user, 5 Oct: *«remotix
    allo stato attuale è "trasparente" (non dispone di menu o di un'interfaccia per le attività di servizio):
    dovremo realizzare una suite di test da fornire allo scopo, "parallela" al server vero e proprio»*). Whoever
    has a machine we do not have measures it by himself, during the trial, before buying. Claude's
    conditions:
    - **the same encoding code as the server**, built together with it and in the same package:
      an encoder written separately would measure something else;
    - **light**: no browser and no boxes (the lab suites are not shipped). It simulates N desktops
      in motion and measures how many the card encodes without losing smoothness;
    - **only with the server stopped**: with sessions open it refuses and says why, because it would measure only
      the spare capacity and would steal the card from the users;
    - it prints **the same row as the public table** (optimal up to X, then degradation), comparable with
      our numbers.
  - It replaces Claude's counter-proposal «sell up to 16, the rest later»: the licence says N or
    «unlimited» without a cap, and transparency does the rest. The technical work of the limit decided
    at startup remains (above).
- ✅ **The full licence is valid forever** (user, 5 Oct, «1, per sempre»): you pay once, for N users or
  «unlimited». There is no expiry in the signed code; whoever wants more users buys a new code
  («Change licence»).
- ✅ **The code is valid for one machine, physical or virtual** (user, 5 Oct: *«il codice è per macchina (fisica o
  virtuale che sia)»*). The customer, on purchase, sends the machine's identifier (the login page shows it next to
  the code field); the signed code contains it, and on another machine it is not valid.
  - The identifier is `/etc/machine-id`: it exists in the same way on physical and virtual machines, and does not
    depend on the computer's parts.
  - ⚠ Declared: whoever is administrator can copy it to another machine, and a **cloned** virtual machine
    carries it along. The rule above holds: it keeps the honest honest.
  - ⚠ The price: server changed or system reinstalled ⇒ new identifier ⇒ the customer writes to you and
    you generate a new code for him, by hand.
- ✅ **A network licence check is needed** (user, 5 Oct: *«se il prodotto dev'essere venduto allora è
  obbligatorio dotarsi di un software di controllo delle licenze … un sistema forse in stile Microsoft o
  affine»*), after Claude showed that without a network under-the-counter resale (= copying the machine's
  identifier, or a cloned virtual machine) cannot be prevented, only discouraged. ⇒ Supersedes
  «without a network» in the items above; the signed code and the customer's name stay.
  - 🔸 Claude's proposal, to be confirmed: **hybrid like Microsoft** — online activation, periodic
    check with **tolerance** if the network is missing (a customer is not blocked for a fault of our
    service or of his line). ⛔ **No offline activation** (user, 5 Oct: *«un server che non
    abbia un accesso a internet … mi sembra alquanto improbabile, a meno che non si tratti di militari»*):
    one single route, and the signed offline file was the easiest gap to clone. What stays: going
    through a **proxy** (companies get out that way) and **tolerance** of network faults;
  - ✅ **We write the licensing platform ourselves** (user, 5 Oct: *«non voglio appoggiarmi a prodotti a
    pagamento; se serve, la piattaforma di licensing ce la costruiamo noi»*). ⛔ Supersedes Claude's proposal
    of an existing service. The comparison made (5 Oct: Keygen, Cryptlex, Polar, Paddle, Lemon Squeezy,
    Anystack, Gumroad) stays as a reference for the functions: activation tied to the machine, periodic
    check, renewal driven by payment, and for clones a **random identifier for each start**
    plus the periodic check, which sees two live copies on the same code (it is Keygen's «processes»
    technique).
  - ⚠ **Payment cannot be written by us**: cards, refunds and disputes go through a payment
    processor anyway, which keeps a percentage per sale (no fee). Who collects remains to be chosen
    (below).
  - ⚠ To be declared to the customer: the server sends our service the code and the machine's
    identifier (data privacy).
- ✅ **THE FINAL MODEL: annual subscription per machine, unlimited users** (user, 5 Oct: *«dovendo
  realizzare un server di licenze, voglio un sistema semplice: si paga anno per anno senza limite agli utenti
  che remotix gestisce»*). ⛔ **Supersedes** «the full licence is valid forever» and the user tiers
  (Claude's proposal, never confirmed).
  - Why it holds now and not before: the network check is there anyway, so **renewal is automatic**
    (the payment platform drives it) and there is no need to send a new code every year. Claude's
    objections to the annual model fall with the network.
  - The program no longer counts users for the licence: only the machine's technical cap remains,
    declared in the public table. ⇒ The «limit decided at startup» work stays, the «number of
    users in the code» work disappears. The trial stays 1 user, 30 days.
  - ⚠ Declared: the office with 2 people and the school with 60 pay the same. The price is chosen taking
    that into account.
  - ✅ **On a missed renewal: 14 days of tolerance**, warning on the login page from 7 days before the
    expiry, then the same window as the expired trial («subscription expired, renew») (user, 8 Oct).
- ✅ **The seller's «eternal» licences** (user, 5 Oct: *«una versione full di remotix "eterna" che userò io
  personalmente, o dovrò diventare cliente di me stesso»*). Claude's form: ⛔ **no special version of the
  program** (a binary without the check, if it gets out, is the unlocked version for everyone); ⇒ **licences without
  expiry in the licence service**, one per machine, generated by the seller. Same program, same route
  as the customer.
  - They also apply to **the test machines**: the test server and the 4 boxes (each with its own
    identifier), or the suite stops at the 1-user trial.
- ✅ **ALL IN ALL: three licence types, all per machine** (user, 5 Oct: *«per rendere le cose semplici
  prevediamo 3 tipi di licenze»*):

  | type | users | duration | who gets it |
  |---|---|---|---|
  | **trial** | ~~1~~ **unlimited** | ~~30~~ **14 days** | anyone who installs (⭐ changed on 9 Oct, below) |
  | **full** | unlimited | 1 year, automatic renewal | whoever pays |
  | **gold** | unlimited | no expiry | ⛔ **not for sale**: private use of the seller, for his machines and for the test machines |

  - ✅ **The trial changes: 14 days, unlimited users** (user, 9 Oct: *«eliminiamo il limite di 1 utente, così
    un'azienda può effettivamente valutare le vere potenzialità del prodotto»*). ⛔ Supersedes «1 user, 30 days».
    Once expired, REMOTIX stops working and the full is needed. Tied to the **hardware signature**, without duplicates:
    two active copies of the same trial ⇒ the trial is disabled (fine here: nobody has paid). ⇒ The
    program **no longer counts users for any licence**. Details in `fasi/21-la-licenza.md` §11.3.
  - ✅ **The full's renewal is chosen by the customer: manual (default) or automatic** (user, 9 Oct). ⛔ Supersedes
  «1 year, automatic renewal» and «renewal is automatic (the payment platform drives it)». Why:
  *«addebitare centinaia o migliaia di euro automaticamente … non è così simpatico»*. Rules in `SPECIFICHE.md` §15.6.
- ✅ **The third type is called «gold»** (user, 8 Oct: *«si vende solo la full, la gold è per uso privato»*):
    it was «eternal», only the name changes. ⛔ **Only the full** is sold.

  - Claude's addition: with the network check **the trial too is registered on our service**, tied
    to the machine's identifier. A machine that has already had its trial does not receive a second one:
    the «I delete `/var/lib/remotix` and reinstall» gap declared above is closed (only whoever changes the
    identifier remains, as for the full).
- ✅ **The licence service runs on the VPS** (user, 8 Oct: *«il server è sulla VPS»*), the same one that publishes
  the package archive (§10.23, D10): a single machine to keep on and updated, no new cost.
  - ✅ **The tolerance if the network is missing: 14 days**, check ~~every 24 hours~~ **every 60 minutes** (user, 9 Oct), warning to the administrator from the first
    failed check (user, 8 Oct; `fasi/21-la-licenza.md` §10 question 1).
  - ✅ **At expiry only REMOTIX is disabled, never access to the server**; connections closed, desktops alive;
    warnings beforehand in the page (administrator from 7 days, users 3 messages a day in the last 3), with
    RootSpeak's behaviour and part of its code (user, 8 Oct; `fasi/21-la-licenza.md` §10 question 5).
  - ⚠ **A single point**: if the VPS goes down, updates and licence checks stop together. The
    customers do not notice as long as the **tolerance** lasts ⇒ the tolerance must be chosen longer than the time
    it takes to put the VPS back on its feet.
  - 🔸 Claude's proposal: **the key that signs the replies is on the VPS, but it is not the root**. An offline
    root (never on the VPS) certifies the VPS's key, as the installer's chain already does (offline ed25519
    root, subkeys, revocations). If the VPS is breached its key is revoked and a new one is
    certified, without recompiling the product.
- ⏳ **Payment remains on hold** (user, 5 Oct: *«per il momento lasciamo in sospeso l'implementazione dei
  sistemi di pagamento e concentriamoci sul prodotto»*). Open choice: whoever sells in our place (Polar,
  Paddle: ~5% + 0.50 $, VAT and invoices theirs) or Stripe (VAT and invoices ours). ⇒ Our licence service
  exposes **a generic «renew/suspend this licence» entry**, which payment will call when it exists:
  the later choice does not change the product. Full licences are created by hand until payment exists.
- ✅ ~~To be decided: what the full buys; the sales contract~~ — closed on 9 Oct (unlimited users, 1 year,
  updates while active, stops when expired); the contract stays on hold with payment. See `SPECIFICHE.md` §15.

**9 October 2026, evening — the simplification.** At the user's question (*«abbiamo parecchi elementi che fanno
sicurezza: license key, fingerprint, firma, biglietto…»*) and with his principle (*«la complessità di un sistema aumenta
la probabilità di introdurre punti di vulnerabilità e di perdita di controllo del processo»*) these were removed:
`INSTALL_KEY` (signature and ticket sit in the same folder: whoever copies one copies the other; clones are found by the
ticket), `HW_FINGERPRINT` (on VMs it changes with one click; trial «one per account»), the licence number (only
the `LICENSE_KEY` stays, shown masked), recovery by email, the signed move and the upgrade with a new
key. In their place a single mechanism: every installation starts **pending** until the buyer confirms it
in the customer area. ChatGPT (gpt-5.6-sol, with a mandate to refute) confirmed that signature and fingerprint were not needed;
of its corrections, the four without new pieces went in (first ticket to the pending copy, random code
in the requests, key deleted from disk after activation, a single pending per licence), while delegations,
provisional activations, return windows and regeneration of the key by the customer were excluded
by the user as outside REMOTIX's perimeter. The interface between REMOTIX and the service is written as two black
boxes (`SPECIFICHE.md` §15.14). Rules in force: `SPECIFICHE.md` §15, rewritten in full. Right after, the user also removed the
confirmation (*«abbiamo complicato il processo … inserisce lo stesso codice e qui si verifica il caso del doppione»*):
every installation starts at once, and a second one with the same key is a split. Two elements remain
(key and ticket) and one gesture (choosing the copy); on top of that, the server change happens without downtime.

### 10.31 ✅ The installer has no window: only a polished TUI (5 Oct 2026)

User's words: *«niente installer grafico; prevediamo sì un installer con interfaccia professionale, ma
attraverso una TUI sofisticata»*. ⛔ **Supersedes** §10.5 for the GUI part and §10.19 (Gio) entirely.

- ⇒ **Two interfaces, not three**: the CLI and the TUI (bubbletea/lipgloss, already in the program), on the same engine.
  The TUI is the «professional» interface: it must be polished as the window was (colours, layout, the
  prototype's words).
- Why it holds: whoever installs a server does it from a terminal, via ssh or from the console, and even from the desktop
  `install.sh` is launched from a terminal. The most expensive part to build and to test goes:
  the second build with cgo on Debian 12's glibc (`Contenitore.gui`), the graphics libraries, polkit and
  the differences between Wayland and X11.
- ⚠ **The work that follows** (the installer's phase): remove `installatore/interfaccia/gui`,
  `Contenitore.gui`, `remotix-install-gui`, `install.sh --finestra` and the code `RX-UI-001`, and the dependency
  on Gio in `go.mod`; update `fasi/17-l-installatore.md` §6.6.1 and §6.6.14 and `SPECIFICHE.md`. ⛔ The interface
  code contains no installation logic (§6.6.1), so removing it does not touch the engine.
- ✅ **Done on 10 Oct 2026**, commit `129e315`: GUI removed from the code, from the release and from the archive; a single
  build, static (engine, CLI, TUI); `vendor/` from 37 to 14 MB; Go tests green (64 PASS, 0 FAIL, vet clean). Detail
  in `fasi/17-l-installatore.md` §6.6.14. `SPECIFICHE.md` did not mention the installer's window: nothing to change.

### 10.32 ✅ REMOTIX's interface is all in English (5 Oct 2026)

User's words: *«l'interfaccia di remotix sarà tutta in inglese, così come già fatto per la pagina di
login»*. ⇒ Everything read by whoever uses or installs REMOTIX is in English: the page (login, warnings, errors,
licence), the messages the server sends to the page, the TUI and the installer's messages.

- Why it holds: the product is sold outside Italy, and a single interface is written and tested once.
- ⛔ **The project's language does not change**: documents, comments, names in the code and reports stay in
  Italian (the usual conventions). Only what the customer sees changes.
- The texts are gathered in one place for each program (like `installatore/interfaccia/testi.go`), so
  another language can be added later without hunting for them in the code.
- ⚠ **The work that follows**: the login page is translated (5 Oct); what remains is the page's other texts,
  those the server writes into the page (`__AVVISO__` and the ban warnings), the TUI and the installer's
  messages. The suite's tests find elements by `id`, not by text: the translation does not
  touch them (checked on 5 Oct on the login page).

### 10.33 ✅ No licences: REMOTIX is free (10 Oct 2026)

> Supersedes §10.30 and, with it, all of `SPECIFICHE.md` §15 and the plan `fasi/21-la-licenza.md`, which stay as history.

User's words: *«niente licenze. Remotix sarà un progetto freeware. La comunità di Linux apprezzerà il
gesto, poi se qualche azienda volesse acquistare il prodotto si faccia avanti. Quindi allo stato del progetto il
prossimo step sarà l'installer»*.

- **What goes out**: trial and full, `LICENSE_KEY`, hourly ticket, the service on the VPS, the site with customer
  area and panel, the payment entry. ⇒ Phase 21 (~161 hours) is not built.
- **Why it holds**: it is the most complex piece left, and it did not serve to make REMOTIX work but to make it paid.
  Removing it also removes a network-exposed service to keep alive and to defend (*complexity =
  vulnerability*). The installer loses the key step: REMOTIX starts as soon as it is installed.
- **The next step**: close the installer (`fasi/17-l-installatore.md`), that is the real release keys
  in place of the test ones (D10, D11, D14) and the full round with today's binary.
- ✅ **The code opens up, but nobody must profit from it** (user, 10 Oct: *«posso anche aprire il codice, ma
  nessuno deve poterci lucrare sopra. Credo che adotterò una licenza in stile Phonestra»*). Draft in
  `LICENSE.md`, from the Phonestra Freeware Licence with two additions for published code: the sources may be read,
  compiled and modified **for oneself or for one's own organisation**, but modified copies may not be
  distributed; and the **hosted service** (selling others access to desktops served by REMOTIX) is among the
  commercial uses forbidden without a written licence. ⏳ To be approved by the user.
- ⚠ **It is not «open source»** in the OSI sense (it forbids sale and modified redistribution): one says
  «source-visible», not «open source», or the community disputes it.
- ⚠ **Companies use it free even at work**, like Phonestra: it is bought only to resell, include in
  a product or offer as a service. It is the opposite of §10.22 (which also forbade internal use).
- ✅ **The site `remotix.nicfio.it` becomes just a showcase and download** (10 Oct): static files served by Caddy
  on the VPS, no live parts. ✅ **The `.run` is downloaded from the VPS** (user, 10 Oct: *«dalla VPS»*), with its
  `.sha256` next to it. ⚠ The GitHub repository turns out to be **public** (`gh repo view`, 10 Oct evening), not private as believed. Mockup in `grafica/sito-mockup/index.html`.
- The constraint of §11.4 of the SPECIFICHE stays, no GPL dependency: the GPL would ask to distribute everything
  under the GPL.

### 10.34 ✅ The card's driver belongs to the customer: REMOTIX declares and checks, it does not install (10 Oct 2026)

User's words: *«se è un problema di software della macchina non è un problema di remotix. Noi dichiariamo le
esigenze e le specifiche, e chi vuole usare il prodotto installa quello che serve»*.

- **What it means**: the card's driver (proprietary NVIDIA included) and its version are a
  **requirement**, written in the manual (`fasi/17-l-installatore.md` §3.1). An NVIDIA is not rented for every
  distribution: NVIDIA is **certified on Ubuntu 26.04** (phase 19) and, elsewhere, the requirement holds.
- **What stays ours**: saying **clearly and first** what is missing. The engine already does it: the preliminary
  check stops the machine without a driver that encodes (RX-GPU-003…006, with the package to install
  in the remedy), and at the end `remotix --prova-codifica` really encodes on the card. A driver too old
  for Vulkan Video stops there, with a message, and not with an installed REMOTIX that does not work.
- Consistent with §10.27 (no encoding on the processor) and with [*no exceptions per compositor*]: what the
  system does not give, REMOTIX does not patch.

### 10.35 ✅ The installer speaks only English (10 Oct 2026)

> Supersedes §10.15 (the bilingual installer, following the system's language).

User's words: *«solo inglese»*, and then *«usare solo l'inglese non è una rinuncia. remotix è destinato al mondo
dei sysadmin, non agli utenti normali»*.

- **Why it holds**: whoever installs is a system administrator, and for him English is the language of the trade. A
  single text to polish and to test, and no messages that change with the language set on the machine.
- ⭐ **The desktops' language has nothing to do with it** (the user's clarification, 10 Oct: *«remotix mostra i desktop dei PC, e
  dipende dalla macchina su cui è installato il desktop … installo remotix su un sistema che ha la localizzazione
  in italiano. Gli utenti si collegano e vedono i loro programmi e il desktop in italiano»*). The language of the
  desktops and of the programs the users see is the machine's: REMOTIX does not touch it. Only REMOTIX's **own**
  text is in English: the installer, the login page, the warnings (§10.32).
- **What changes**: no language choice (`--lingua` goes, as do the reading of `LANG`/`LANGUAGE` and the
  `lingua` entry of the answers file, which is now an unknown entry and stops the file with RX-RISPOSTE-002 like any
  other); a single catalogue of texts and codes, in English (`motore/codici.go`, `motore/testi.go`,
  `interfaccia/testi.go`; `codici_en.go` goes); `install.sh` in English; the option descriptions in English.
  The benches that read the engine's output (`17-t10.sh` first of all) look for the English words.
- ⚠ **What stays in Italian, for now**: the reasons and notes of the combinations catalogue (they are data: they will
  get their English fields with the next version of the catalogue format) and part of the diagnostic **details** that
  go with the codes (in brackets after the message, and in the log). The message and the remedy of every code
  are in English, and a test (`TestTesti`) stops any accented letter or Italian word that slips back in.
- ✅ **Done on 10 Oct 2026**, commit `a1c31ae`: static build, `go vet` clean, `go test` 208 PASS (subtests included), 0 FAIL.
- ✅ **Completed the same day**, commit `d580561`: in English also the diagnostic details, the results of the
  checks, the notes of the facts, the lines the engine writes into system files and the manual's table
  (`catalogo --tabella`); the catalogue goes to `2026.10.10.12` (seq. 12) with the reasons, the notes and the limits in English.
  `motore/inglese_test.go` looks for Italian in every string of the code and the catalogue: 211 PASS, 0 FAIL.
  ⚠ **What stays Italian, because they are interface names and changing them is a job of its own**: the commands and options
  (`verifica`, `installa`, `approva`, `--archivio`, `--risposte`…), the entries and values of the answers file
  (`consenso.*`, `porta`, `utenti = tutti`, `si`/`no`, `canale = stabile|candidato`), the values of the facts
  (`presente`, `assente`…) and the names of the states (`RILEVATO`, `CONFERMATA`…). To be decided.
- ✅ **This is done too, 10 Oct 2026** (commit `5f802d7`): commands, options, answers file, states, values and
  names of the facts, step types, JSON fields, files in `/var/lib/remotix` and in the published archive, in English. The
  old → new table is in `fasi/17-l-installatore.md` §6.6.15. Formats: `remotix-install/2` and
  `remotix-answers/2`. What remains: the `RX-…` and `C-…` codes (identifiers), the catalogue format and what the
  C product writes. ⚠ The product command `remotix` still has its options in Italian (`--porta`,
  `--indirizzo`, `--certificati`, `--prova-codifica`…): a job of its own.

### 10.36 ✅ The simple installer, and REMOTIX that does not modify the system (10 Oct 2026)

Decisions of the user taken in sequence on 10 Oct, in his words. Supersedes §10.7 (the desktop installed by
REMOTIX) and the parts of §10.12, §10.21 and §10.23 that contradict what follows. ⏳ The work is not done yet:
`fasi/17-l-installatore.md` will say when.

- ⭐ **The principle**: *«la chiave di tutto è che remotix non modifica i sistemi su cui viene installato: dice cosa
  gli serve e poi sta all'admin provvedere»*; *«remotix dice semplicemente cosa manca. Il cosa installare e il come è
  una decisione non di remotix»*. ⇒ Out of the engine go: third-party repositories (RPM Fusion, EPEL, Packman), card
  drivers and Vulkan drivers, desktop components (labwc, fonts…), the desktop itself (*«se manca il desktop non sarà
  certo remotix a installarlo»*), opening the firewall, the system belts (polkit, logind, sleep). `check` says
  what is missing, **without suggesting packages or commands**. The items removed from the menus inside the sessions stay: they are the
  behaviour of REMOTIX's sessions, not the system.
- ⭐ **The wanted exception**: membership of the card groups stays **automatic** (installation and first
  connection, §7.21): *«non si installano pacchetti senza autorizzazione ma si fa in modo che gli utenti possano
  accedere»*. ⚠ Only `render`, if it neither prevents the use of the desktop nor worsens performance (to be tested on the
  four desktops): `video` also gives `/dev/fb*` and the webcams (seen on the tablet). Then a dedicated `remotix` group;
  ACLs only if needed and measured (logind rewrites the `uaccess` ACLs of `renderD*`).
- **Commands**: from 14 to 5 + `tui` — `check`, `install` (shows the plan with the exact packages from the package
  manager's simulation, then *«Proceed? [y/N]»* from stdin, like apt), `uninstall`, `status` (state + checks),
  `prepare-offline`. Gone: plan/approve/apply, dry-run, resume/rollback as commands (*«cerchiamo di semplificare
  la vita»*).
- **No mode without questions** (the answers file is gone): *«chi installa su molte macchine si prepara uno
  script bash»*.
- **Interrupted installation**: it is cancelled and redone from scratch, never resumed half-way (*«non mi piace l'idea di lasciare
  un sistema a metà»*); first the package manager is fixed (e.g. `dpkg --configure -a`); no automatic retry. An
  interrupted uninstallation is carried through to the end.
- **Do not reinvent the package manager** (*«non reinventare la ruota duplicando funzioni già supportate dai gestori dei
  pacchetti»*): resolution, signatures, dependencies and autoremove are done by the package manager; the engine has no cache nor sha256 of its own
  for the packages.
- **The single package, no repository to add** (*«sono più orientato all'idea del pacchetto di
  installazione unico. Questo evita che l'admin debba aggiungere fonti esterne che è sempre un gesto mal visto»*):
  a single file (e.g. `remotix-<versione>.run`, sha256 published) with the installer and the packages of all the
  distributions; the package manager installs from a local folder. Upgrading = downloading the new `.run` and running it again.
  Supersedes the part of §10.23 on upgrading with `apt upgrade` from a repository of ours.
- **Rolling-release distributions stay** (Arch, Tumbleweed; and Fedora): *«chi usa arch è consapevole
  che in qualunque momento la macchina potrebbe avere problemi. Quello che noi possiamo fare al massimo è fare in
  modo che remotix usi librerie piuttosto stabili, ma non possiamo garantire la stabilità su sistemi per loro natura
  soggetti a problemi di affidabilità»*. ⇒ In the manual: certified for production Debian, Ubuntu LTS, Alma (Rocky
  and RHEL compatible), Leap; Fedora, Arch, Tumbleweed tested at every campaign but with no guarantee about
  system updates. To do: the fragile libraries inside the binary (like ngtcp2/nghttp3), and the service that
  at start-up tries encoding and says clearly in `remotix status` if an update broke it.
- ✅ **Done on 10 Oct 2026** (commits `2e16f8f` engine, `8bcb881` the .run, `623ea90` benches):
  `fasi/17-l-installatore.md` §6.6.16. Still to be tested on the hardware (the campaign on the distributions) and two
  open points: only `render` in the card groups, and the licences of the third-party components in the .run.
- ✅ **The desktop pieces are dependencies of REMOTIX, not things missing** (user, 10 Oct 2026: *«trattiamo i 3
  componenti come normali dipendenze di remotix. basta che l'installer li mostri come tali nella sezione piano»*):
  labwc and wlr-randr for XFCE and LXQt, and a scalable font if the machine has none, are added by the engine to the
  packages to install; the package manager takes them from the distribution's repositories like the other dependencies and the
  simulation shows them in the plan, in the group «Dependencies of REMOTIX» with «needed by REMOTIX for XFCE». The same
  holds for the other piece of the catalogue, breeze6-wallpapers (KDE on Tumbleweed). If the distribution does not have the
  package, the simulation fails and stops there (RX-PACCHETTI-005). The font per family comes back into the catalogue
  (`carattere_scalabile`, 2026.10.10.14). Done on 10 Oct, commit `facc27a` (with the TUI redone: fasi/17 §6.6.16).


### 10.37 ✅ The technical manual: in English, on the model of Phonestra (10 Oct 2026)

The user's choices (10 Oct 2026):
- **in English**, like the interface (§10.32, §10.35): messages and `RX-…` codes match word for word;
- **style, structure and kind of content taken from Phonestra's technical manual** (*«solo che questo manuale sarà
  almeno 10 volte più lungo e complesso»*): it speaks to **whoever maintains REMOTIX** (internals, protocol, capture, encoding,
  tests, build, extensions, file map), not to whoever installs it;
- **for now only the technical one is written**; the sysadmin guide (installation, commands, codes) remains to be
  decided.

🔸 Derived by me, correctable: as in Phonestra the manual is **generated** — `docs/sources/technical/chNN_*.py`, one
file per chapter, ⇒ `docs/Technical Manual.html` with `python3 docs/sources/build.py`; `style.css` and `manual.js` are
the **common canon** copied byte for byte from Phonestra (which is not modified in a single project); `--controlla`
checks that the files, functions, `REMOTIX_*` variables and `RX-` codes cited exist in the code, and that no Italian
is left. Performance and capacity wait for the xrdp campaign.

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

## How this document is kept

An ❓ item that gets an answer **is moved** to the section it belongs to and changes mark; it is not
answered at the bottom. A 🔸 item that the user confirms becomes ✅. A ✅ item is reopened only
with a measurement that refutes it — and then it is rewritten **at the same moment**, with the date and
the source (`CODER.md` §5).
