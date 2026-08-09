# REMOTIX_V2

Desktop remoto per Linux: un **server**, due **client** (Linux e Android), e un protocollo nostro
chiamato **RCP** — *Remotix Control Protocol*. Niente Windows, in nessuno dei due ruoli.

> **Stato al 9 agosto 2026**: specifica, protocollo e piano scritti; **nessuna riga di codice
> ancora scritta**. Il prossimo passo è la **fase 0**.

---

## Da dove si comincia a leggere

⛔ **In quest'ordine.** Chi salta il primo si ritrova a rifare errori già pagati.

| # | Documento | Che cosa contiene |
|---|---|---|
| **1** | [`LEZIONI.md`](LEZIONI.md) | **il fondamento**: come si misura, come si prova, come si impara. Ereditato da v1, che si è arenato ogni volta su una misura che non misurava quel che credevamo |
| **2** | [`SPECIFICHE.md`](SPECIFICHE.md) | **che cosa** fa il prodotto, e che cosa non fa |
| **3** | [`RCP.md`](RCP.md) | **come parlano** i due lati. È l'arbitro: in v1 lo era `mstsc`, ora è questo file |
| **4** | [`PIANO.md`](PIANO.md) | **le fasi**, in ordine, ciascuna col suo banco e il suo criterio di chiusura |
| **5** | [`DECISIONI.md`](DECISIONI.md) | **perché**: ogni decisione con la data, chi l'ha presa, e con che grado di certezza |

E per chi scrive o revisiona, prima di toccare qualcosa:
[`CODER.md`](CODER.md) · [`REVIEWER.md`](REVIEWER.md)

---

## Gli studi dei desktop

Letture del codice dei compositori, fatte prima di scrivere. Rispondono alle **quindici** domande
di `LEZIONI.md` §3.

[`gnome.md`](gnome.md) · [`kde.md`](kde.md) · [`xfce.md`](xfce.md) · [`lxqt.md`](lxqt.md) ·
[`cinnamon.md`](cinnamon.md)

⚠ **`gnome-remote-desktop.md` non è uno di questi** *(chiarito il 9 agosto 2026)*. Studia **il
server RDP di GNOME**, cioè un concorrente sul filo che abbiamo buttato — non il desktop. Con RDP
morto decade quasi per intero, ed è scritto su una versione che Trixie non ha (51.alpha contro
48.1). **Su GNOME si legge [`gnome.md`](gnome.md)**, che parla di Mutter e resta valido.

---

## Le cartelle

| | |
|---|---|
| `fasi/` | un documento per fase, **aperto quando la fase si apre** — vedi `PIANO.md` §0.2 |
| `v1/` | l'eredità di REMOTIX v1: **17.481 righe di C**, 4.563 di banchi, i documenti e le scene di taratura |
| `reference-*/` | cloni dei progetti di riferimento — **non versionati**, si rifanno con `git clone` |

---

## Le convenzioni

**Si scrive in italiano**, documenti e commenti. I nomi nel codice pure: `palco`, `cattura`,
`sentinella`, `appunti`.

**Le marche** dicono quanto vale un'affermazione, e vanno messe sempre:

| | |
|---|---|
| `[M]` | misurato da noi, sul ferro, con la data |
| `[R]` | letto nel codice di un riferimento |
| `[S]` | letto in una specifica |
| `[?]` | ipotizzato, **non ancora misurato** |

⛔ **Una decisione che poggia su una `[?]` va scritta come provvisoria.** Una ragione non misurata
rende la decisione presa a metà (`LEZIONI.md` §2.3-quater).

**Le decisioni stanno in `DECISIONI.md`, una sola volta.** Gli altri documenti rimandano, non
copiano — e le voci portano ✅ (deciso dall'utente), 🔸 (derivato, correggibile senza discussione)
o ❓ (aperto).

⛔ **Quando una misura contraddice un documento, lo si aggiorna nello stesso momento**, con la data
e la fonte. Un riferimento che invecchia in silenzio è peggio di nessun riferimento.

---

## Il metodo

Due tipi di agenti — chi scrive e chi cerca contraddizioni — e la revisione interviene **tre
volte** per fase: sul banco *prima* che il prodotto esista, sul codice prima di misurarlo, sul
documento prima della chiusura (`PIANO.md` §0.4).

⭐ **Perché la revisione qui pesa più del solito**: buttando RDP abbiamo perso l'arbitro esterno —
`mstsc` protestava gratis quando sbagliavamo. Ora client e server sono nostri, e **due programmi
scritti dalla stessa mano che vanno d'accordo non confermano niente**.

---

## La macchina di prova

`192.168.0.2` — i5-13500T, 31 GB, Intel UHD 730 (per REMOTIX) e Radeon RX 6800 (riservata
all'inferenza). Ci si arriva con `v1/strumenti/sshpw.py`, che legge le credenziali da
`~/SERVER.ssh`.

Là vivono il `devroot` per compilare e provare, la VM, e la cache dei pacchetti. **I sorgenti no**:
quelli stanno qui, versionati.
