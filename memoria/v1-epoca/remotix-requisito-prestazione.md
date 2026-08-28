---
name: remotix-requisito-prestazione
description: "REMOTIX — dal 7 agosto 2026 l'utente pone i NUMERI e la tecnica li serve: 30 fps a 1080p minimo, 60 fps a 4K desiderato. La fase 10 è azzerata e l'approccio della fase 9 è giudicato sbagliato"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2f8f83b6-a01f-43c3-ac38-668849574507
  modified: 2026-08-07T17:36:59.417Z
---

Il **7 agosto 2026, a fine giornata**, l'utente ha capovolto il modo di lavorare del progetto:

> *«Adesso scrivo quello che voglio, tu decidi cosa ci vuole per ottenerlo, e non dirmi i dettagli
> tecnici che non li capisco. Le soluzioni tecniche devono essere prese in funzione di questi
> vincoli, non il contrario.»*

| | |
|---|---|
| **MINIMO** | **30 fotogrammi al secondo a 1080p, 24 bit di colore** |
| **DESIDERATO** | **60 fotogrammi al secondo a 4K, 32 bit di colore** |

Sta in **§3.1 di `SPECIFICA.md`**, e il conto di fattibilità — che cosa è raggiungibile, su quali
client, a che prezzo — in **§3.1-bis**. Una scelta tecnica si giustifica **mostrando che avvicina
uno di quei due numeri**; se non li muove, non si fa.

**Perché è successo, ed è la parte da non perdere.** La fase 9 ha ottimizzato i **millisecondi di
CPU per fotogramma** (41 → 6) senza che nessuno avesse mai misurato i **fotogrammi al secondo
consegnati**. Misurati la sera del 7 agosto: **18**, e non li limita il codificatore — la cattura ne
consegna 17,7 e il server ne spedisce 17,9, cioè **si spedisce tutto quel che il compositore dà**.
Una fase intera spesa su un pezzo che non era il collo di bottiglia. L'utente: *«abbiamo sbagliato
proprio l'approccio sulle performance»*.

**Stato lasciato il 7 agosto 2026:**

- **fase 10 AZZERATA** su richiesta dell'utente: codice tornato alla chiusura della fase 9, banchi
  rimossi, riquadro in `PIANO.md` con i tre motivi del fallimento. Restano **le misure** in
  `REFERENCE.md` (R31, §5.1, §10.2) e **le decisioni dell'utente**: risoluzione adattiva fuori,
  AVC444 fuori (gli aveva dato problemi di luminanza), codifica per regioni fuori, e **i 10 Mbps
  sono un pavimento, non un budget** — «spendere meno banda» non è un guadagno per questo prodotto;
- **fase 9 sotto giudizio**: non azzerata, ma il suo approccio è quello che l'utente contesta. Le tre
  strade proposte (togliere solo la copia zero / azzerare tutto / azzerare l'approccio) sono
  nell'ultima parte della conversazione; l'utente ha scelto la terza di fatto, ponendo i numeri;
- **il server** (`192.168.0.2:3392`) è nello stato di chiusura della fase 9: copia zero **spenta**,
  bitrate a banda costante, più la sola correzione della locale (senza, il terminale della sessione
  non parte).

## ✅ IL COMPITO È STATO ESEGUITO LA SERA DEL 7 AGOSTO 2026

*Le tabelle per intero stanno in **R32** di `REFERENCE.md`; il banco in
`/media/REMOTIX/tmp/banco-compositori`, fuori dal prodotto (misuratore PipeWire proprio, client per
il protocollo di KWin, client screencopy per wlroots).*

**La risposta, in una riga: i 18 fotogrammi erano nostri.** REMOTIX dichiara alla cattura un massimo
di **30**, e Mutter ne consegna **18**. Dichiarandone **60** ne consegna **37**. Si ottengono circa
**sei decimi** di quel che si chiede, e oltre i 60 non si sale.

| | |
|---|---|
| il client disegna | **60 fps**, su monitor virtuale a **60,000 Hz** |
| **Mutter** ne consegna | **35–37**, uguale da 1080p a 4K |
| **KWin 6.3.6** (DMA-BUF) | **59–60**, a ogni risoluzione |
| **sway / labwc** (wlroots) | **61** a 1080p e 1440p, 40 a 4K |

**Quel che è caduto**, e non va rimesso in piedi: risoluzione e profondità di colore **non costano
niente** alla cattura (4K rende come 1080p, BGRA come BGRx); la copia zero **non porta fotogrammi**
(36,6 contro 34,0), porta CPU; il carico della GPU non sposta il numero; a desktop fermo la consegna
è **zero**, come da specifica.

**Il minimo dell'utente è raggiungibile** (37 > 30) cambiando una riga. **Il desiderato non lo è su
GNOME**: il tetto è Mutter, che perde il 40 % dei ridisegni — e **la fase 11 diventa anche la strada
per i 60 fps**, perché gli altri due compositori quel tetto non ce l'hanno.

## E la catena intera, misurata subito dopo

Con `--fotogrammi 60` invece di 30, **fino al client**: 1080p da **18,7 a 32,4** — il minimo
superato. Due cose che ne escono e che valgono da sole:

- ⛔ **la copia zero non porta fotogrammi**: 31,5 contro 32,4. Taglia la CPU per fotogramma da 16 a
  3 ms. R29 si riprende per il consumo, non per la fluidità;
- ⚠ **il 4K resta NON misurato**: il banco dà 17, ma il tappo è il client di prova che decodifica in
  software (`in volo 2 di 2` su 835 campioni, server a 0,08 core). Il regolatore della fase 7 su un
  collegamento veloce concede **2 posti**, quindi la portata è quella con cui il client riscontra.
  Serve un client con decodifica hardware prima di dire qualunque cosa sul 4K.

## ✅ Chiuso il 7 agosto 2026: acceso, giudicato sui tre client, e messo nel codice

| Client | Codec | Ritmo dal registro | Giudizio dell'utente |
|---|---|---|---|
| `xfreerdp3` | AVC420 | 32–33 | a posto |
| **mstsc** | AVC420 in GPU | **29–33** | «va benissimo» |
| **RDM** Android | RemoteFX Progressive | **23–29** | «performance eccellenti» |

**Il 60 sta in `main.c`**, non in `/etc/default/remotix` (che vive in RAM e si sarebbe perso al primo
riavvio). Binario ridistribuito e verificato con la sola configurazione predefinita: **33,3 fps a
1080p** sulla catena intera.

**La previsione su RDM era sbagliata** — era stato previsto «neutro, forse peggio sull'audio» per via
di RemoteFX Progressive in software — e il motivo per cui era sbagliata è la cosa da ricordare: **i
18 fotogrammi erano un tappo nostro a monte di tutto**; tolto quello, ogni client ha preso quanto
sapeva reggere, e ne aveva in avanzo. Nessuno dei due lati era al limite: lo era il numero che
dichiaravamo.

⛔ **Resta da fare subito**: il 60 vive in `/etc/default/remotix`, cioè in RAM. Va portato **nel
codice** (`main.c`, `fotogrammi = 30`), o al primo riavvio si perde — esattamente come si perse la
riga della copia zero. Vedi [[remotix-prove-sul-banco-non-sull-utente]] regola 6.

Vedi [[remotix-oltre-rdp]] e [[remotix-fase9-ripresa]].
