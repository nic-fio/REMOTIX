#!/usr/bin/env python3
"""04-b30-anello-input.py — ⭐⭐ L'ANELLO **INPUT → VETRO**.  Fase 4, A10.

    python3 banchi/04-b30-anello-input.py --certifica       ⭐ qui, senza server
    python3 banchi/04-b30-anello-input.py --misura --host 192.168.0.2 --porta 7691 \\
            --utente nicfio --parola-file /tmp/04-b30/parola --secondi 30
    python3 banchi/04-b30-anello-input.py --verdetto VERBALE.json

⛔ I CODICI D'USCITA SONO **QUATTRO**, e il terzo e' la ragione per cui questo
   paragrafo sta in testa al file:

     0   CONFORME
     1   NON CONFORME — il banco ha guardato e ha trovato un rosso
     2   uso sbagliato (argparse)
     3   ⛔⛔ **NON HO NIENTE DA GIUDICARE** — il canale di input non c'e'
         ancora, o la scena non ha ricevuto un evento, o nessuna coppia
         (input, fotogramma) si e' chiusa.

   ⭐ E il 3 esiste perche' il validatore della fase 1 **non ce l'aveva**: usciva
      «conforme» avendo giudicato zero cose, ed e' costato una riscrittura.
      «Tutti quelli provati sono andati bene» e' vero anche quando i provati
      sono zero (`LEZIONI.md` §1.9, sesta veste).

═══════════════════════════════════════════════════════════════════════════════
⭐ DA DOVE VIENE — si dichiara in testa, e non e' una cortesia
═══════════════════════════════════════════════════════════════════════════════

**Estende `banchi/03-b17-ritardo.py`** (fase 3, step 5), che NON si tocca: e' la
misura di una fase chiusa e si ricontrolla.  Da li' questo banco **importa** —
non ricopia — il palco, la distribuzione, il regime, il lettore certificato
della marca e il pezzo cieco.  ⛔ Se un giorno quel file cambia, questo se ne
accorge; se lo avessi ricopiato, no.

I due pezzi copiati e non importati, con la ragione:
  · `banchi/04-b30-ponte.py`  — copia di `03-b17-ponte.py` **+ il ritardo sul
    ramo d'ANDATA**, che alla fase 3 non serviva e qui e' meta' del controllo;
  · `banchi/04-b30-scena.c`   — copia di `03-scena.c` **+ il seat**: una scena
    che non riceve input non puo' chiudere questo anello.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ CHE COSA MISURA — e la prima riga e' che NON e' il numero della fase 3
═══════════════════════════════════════════════════════════════════════════════

`SPECIFICHE.md` §3.2 chiede il ritardo **dall'input che arriva al fotogramma che
parte**: tetto **50 ms**, traguardo **40**.

Alla fase 3 l'input non esisteva, e il metro misurava **cattura → vetro**:
`[M]` **78,12 ms** in hardware, n=379 (`banchi/03-b17-esiti.jsonl`, giro
`E3-deposito-hw-5punti`).

⛔ **E QUI VA REFUTATA LA PRIMA TESI DEL MANDATO**, che diceva: *«con il canale
   di input, lo STESSO metro misura finalmente input → vetro»*.  **Non e' vero,
   e crederlo produrrebbe un numero sbagliato in due versi opposti:**

   | | |
   |---|---|
   | ⛔ **manca a monte** | l'anello di input comincia **prima** della cattura: l'evento nel browser, il filo d'andata, l'iniezione in `libei`, il compositore che lo consegna, e **la scena che ridisegna**.  Sono cinque tratti che il metro della fase 3 non attraversa affatto |
   | ⛔ **e SOVRAPPONE a valle** | il `t0` della fase 3 e' *«quando la scena ha disegnato»*.  Nell'anello di input quel disegno **e' la conseguenza dell'input**, non l'origine: sommare i due numeri conterebbe due volte il tratto disegno→cattura, e sottrarli non ha significato |

   ⇒ ⭐ **I due numeri non si sommano e non si sottraggono: il secondo CONTIENE
     il primo.**  E la quantita' che il canale di input **aggiunge** e' la sola
     cosa nuova che questo banco puo' dire, quindi la dice per prima:

         aggiunta = (input → vetro)  −  (disegno della scena → vetro)

     ⛔ misurata **sullo stesso giro e sugli stessi fotogrammi**, non fra due
     giri: fra due giri ci si mette in mezzo la deriva, il palco e la contesa
     (`LEZIONI.md` §1.13, il difetto di P1 a blocchi).

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ IL CONFINE, E CI SONO DUE POSIZIONI DIFENDIBILI PER PARTE
═══════════════════════════════════════════════════════════════════════════════

`CODER.md` §1-bis, riquadro «DOVE FINISCE LA MISURA»: *«il confine si sposta
nella direzione SCOMODA.  Ogni confine ha due posizioni difendibili, e quella
che favorisce chi misura si sceglie da se' se nessuno la nomina»*.

Questo anello ha **due** confini, non uno.  Si nominano tutt'e due, e tutt'e due
si spostano nella direzione scomoda:

── IL CONFINE DI CHIUSURA (a valle) ────────────────────────────────────────────

  comodo    il richiamo del decodificatore                    ⛔ NO
  ⭐ scomodo  il **DISEGNO FINITO**                             ⇐ scelto

  E' la scelta gia' presa dalla fase 3, che ha fatto salire il numero da 63,8 a
  74,6 ms — **11 ms su 50 che la prima stesura si regalava**.  Qui si eredita.

  ⛔⛔⛔ E IL 22 AGOSTO 2026 QUEL CONFINE SI ERA SPOSTATO **DA SOLO**, perche' e'
       cambiato il prodotto e non il banco (fase 8, punto F1).

    Dal 20 agosto (`DECISIONI.md` §5.4) la pagina dipinge con `bitmaprenderer` +
    `createImageBitmap`, che e' **asincrona**: il richiamo del prodotto ritorna
    **prima** che sia stato dipinto qualunque cosa.  ⇒ «prendere `t_dip` dopo il
    richiamo» — che sulla strada 2D voleva dire *«il disegno e' finito»* — su
    questa strada vuol dire *«il disegno non e' ancora cominciato»*: il confine
    scomodo era diventato **piu' comodo del comodo**, senza che nessuno lo
    decidesse — e il banco avrebbe continuato a chiamarlo «scomodo».
    ⛔ `LEZIONI.md` §1.20: il numero c'era ed era stampato, e **nessuna riga lo
       confrontava con niente** che potesse accorgersene.

    ⇒ ⭐ Oggi il confine si chiude **dopo `transferFromImageBitmap`** (§4-bis del
      prologo), e ⛔ **non si crede: si PROVA**.  `--ritardo-vetro N` innesta N
      ms fra «il fotogramma e' pronto» e «il fotogramma e' al vetro», e **Q11**
      pretende tre cose insieme: la DISTANZA fra il confine vero e quello
      sbagliato — presa sulla stessa sonda — sale di esattamente N, la salita
      sta nel tratto 10 e in nessun altro, e il totale sale di almeno N.

    ⛔⛔ E la ragione per cui Q11 esiste e' `LEZIONI.md` §1.20, la prima delle
        sue due domande: *«per ogni numero che il banco stampa: quale riga lo
        CONFRONTA?»*  Prima di oggi la risposta, per il confine di chiusura,
        era **nessuna**: il banco stampava un ritardo e niente lo metteva
        davanti a una quantita' nota.  ⇒ Un banco riadattato che desse un
        numero plausibile sarebbe stato indistinguibile da uno rotto.

  ⭐ E i tre punti si consegnano tutt'e tre, cosi' si guardano in faccia:
      **T** (scomodo, il numero) · **T-comodo** (il campo `input` dei 28 byte)
      · **T-vecchio** (il ritorno del richiamo — ⛔ quanto MENTE, non un numero).

── ⭐⭐ IL CONFINE DI APERTURA (a monte) — E QUESTO E' NUOVO ────────────────────

  Tre posizioni, e tutt'e tre difendibili:

  | | dove | che cosa lascia fuori |
  |---|---|---|
  | ⛔ **comodissimo** | quando il banco chiama la funzione di spedizione del prodotto | tutto il cammino dell'evento **dentro la pagina**: il gestore, la conversione dalla vista alla tela, l'inquadratura |
  | ⛔ **comodo** | quando il prodotto consegna i byte a `WebTransport` | il gestore della pagina |
  | ⭐ **SCOMODO** | **`event.timeStamp` dell'evento del browser** | solo il pezzo cieco d'ingresso (qui sotto) |

  ⇒ ⭐ **Si sceglie il terzo**, e si misura con un ascoltatore in **fase di
    cattura** installato **prima** di ogni script della pagina: cosi' `t0` e'
    il primo istante in cui il prodotto avrebbe potuto vedere l'evento, e tutto
    quel che il prodotto fa da li' in poi **e' dentro il numero**.

  ⛔ **E la differenza fra i tre non si stima: si MISURA**, e sta nella
     scomposizione (tratti 1a e 1b).  Chi vuole il numero comodo se lo puo'
     ricavare; chi vuole quello vero legge la riga in cima.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ I PEZZI CIECHI SONO **DUE**, E LA FASE 3 NE DICHIARAVA UNO SOLO
═══════════════════════════════════════════════════════════════════════════════

  ⭐ **in USCITA** — gia' noto: fra il disegno finito e il pixel acceso passano
     `[?]` **16-40 ms** che nessuna API JavaScript vede (`STUDI.md` §web §6.2).
     ⛔ **ma non su Xvfb**, dove non c'e' compositore e quel pezzo **non esiste
     affatto**: la stima e' per lo schermo di un utente, non per il banco.

  ⭐⭐ **in INGRESSO** — ⛔ **e questo nessuno l'aveva ancora nominato**: fra il
      movimento della mano e `event.timeStamp` ci sono il dispositivo, il
      nucleo e il compositore **della macchina del client**.  `[?]` Su un mouse
      USB a 125 Hz sono 4-12 ms; su un pannello tattile di piu'.
      ⛔ Nessuna API della pagina lo vede — `event.timeStamp` **e' gia' il
      dopo** — quindi si dichiara e non si promette, esattamente come l'altro.

  ⇒ ⭐ Il numero che si consegna e' **il pezzo nostro**, `SPECIFICHE.md` §3.2 —
    e quel che l'utente sente e' *questo + i due pezzi ciechi + la rete*.
    ⛔ Nessun numero esce da questo banco senza tutt'e tre le righe accanto.

═══════════════════════════════════════════════════════════════════════════════
⭐ COME SI CHIUDE L'ANELLO — e la grandezza e' quella VERA, non una sostitutiva
═══════════════════════════════════════════════════════════════════════════════

`LEZIONI.md` §1.13: *«si nomina la grandezza vera del fenomeno e si guarda se il
protocollo — o il formato, o l'API — la porta gia'»*.  Qui la porta **due
volte**, e le due si guardano in faccia:

  1. ⭐ **L'ECO NEI PIXEL** — `04-b30-scena.c` dipinge in una seconda marca
     **le coordinate stesse dell'evento che il compositore le ha consegnato**.
     ⇒ Il banco vede, DENTRO l'immagine decodificata, la conseguenza del
     proprio input.  E' il confine **scomodo**: si chiude quando lo schermo e'
     davvero cambiato.

  2. **IL CAMPO `input` DEI 28 BYTE** — `RCP.md` §6.2: *«l'identificatore
     dell'ultimo input iniettato prima della cattura»*.  ⇒ Il primo fotogramma
     con `input >= id` e' il primo che **poteva** portare la conseguenza.
     E' il confine **comodo**: il fotogramma e' stato catturato dopo
     l'iniezione, ma sullo schermo puo' non essere ancora cambiato niente.

⛔ **E il disaccordo fra i due e' il regalo, non un fastidio**: la loro
   differenza e' *quanto il fotogramma «buono» arriva prima che ci sia qualcosa
   da vedere*, cioe' esattamente quel che il confine comodo si regala.  Il banco
   li consegna tutt'e due e **dichiara come numero il secondo**.

⚠ E se i due dessero lo stesso fotogramma **sempre**, il banco lo dice: vuol
  dire che l'eco non sta discriminando, ed e' un rilevatore che dice sempre si'.

═══════════════════════════════════════════════════════════════════════════════
I CONTROLLI — ⛔ e tre sono nati da difetti gia' pagati
═══════════════════════════════════════════════════════════════════════════════

  Q0  ⛔⛔ C'E' QUALCOSA DA GIUDICARE?  Tre stati distinti, tre frasi distinte,
      e **nessuno dei tre e' «conforme»**.  Codice d'uscita 3.

  Q1  ⛔⛔ LA SCENA E' SUL MONITOR CHE SI CATTURA.  La trappola di
      `LEZIONI.md` §1.1 e §1.1-bis, che ha morso **due volte** — e la seconda
      sul risultato che la citava.  ⇒ Le celle contaminate si RIFIUTANO da
      sole, e il denominatore vero si STAMPA: **«0 punti su 0» e' la cosa
      giusta da stampare**, ed e' quella che nessuno legge.

  Q2  LE DUE MARCHE SONO DELLO STESSO FOTOGRAMMA (stesso `disegno`).  Un
      campione a cavallo di due disegni darebbe un ritardo plausibile e falso.

  Q3  L'ECO TROVA QUEL CHE C'E'.
  Q4  ⛔ L'ECO NON TROVA QUEL CHE NON C'E' — il controllo caduto in v1.  Tre
      setacci: il rifiuto dove la marca non c'e', l'eco che **cambia**, e le
      coordinate lette che **sono quelle spedite**.

  Q5  ⛔ P1-RITORNO: il ponte ritarda di N il ramo prodotto → cliente, e la
      mediana DEVE salire di N **nel tratto giusto**.
  Q6  ⭐⭐ P1-ANDATA: il ponte ritarda di N il ramo cliente → prodotto, e la
      mediana DEVE salire di N **in un tratto DIVERSO**.  ⛔ Alla fase 3 questo
      controllo **non poteva esistere**, e senza di lui meta' dell'anello resta
      senza taratura per sempre (`LEZIONI.md` §1.14).

  Q7  I DUE CONFINI SI DICHIARANO TUTT'E DUE, e il consegnato e' lo SCOMODO.

  Q8  ⭐ IL TRATTO CHIAMATO «IL DISEGNO» NON E' IL DISEGNO — vedi il riquadro
      qui sotto.  Si scompone in `1° drawImage` e `2° drawImage`, e i due
      numeri si consegnano separati.

  Q9  IL COSTO DEL BANCO si misura, o e' un errore sistematico dentro ogni
      numero.
  Q10 LA GRANA DELL'OROLOGIO della pagina.

> ═════════════════════════════════════════════════════════════════════════════
> ⛔⛔⛔ E LA TERZA TESI DEL MANDATO — *«il metro della fase 3 e' affidabile»* —
>       E' STATA PROVATA, E **NON REGGE COME E' SCRITTA**
> ═════════════════════════════════════════════════════════════════════════════
>
> `[M]` 14 agosto 2026, rileggendo `banchi/03-b17-esiti.jsonl`, cinque giri.
> ⚠ Non e' un ricalcolo: sono i numeri che quel file porta gia'.
>
> | giro | tratto 5 «decodifica» | tratto 6 «disegno» | **5+6** | n |
> |---|---|---|---|---|
> | `E-C-software-av1` | 6,315 | **9,105** | 15,42 | 508 |
> | `E-B-hardware-stessapagina` | 6,315 | **9,155** | 15,47 | 509 |
> | `E2-A-software-hevc` | 1,495 | **29,250** | 30,75 | 375 |
> | `E2-B-hardware-hevc` | 0,775 | **25,105** | 25,88 | 799 |
> | `E3-deposito-hw-5punti` ⭐ *il numero della fase* | 0,730 | **27,995** | 28,73 | 379 |
>
> ⛔ **I due tratti si muovono in versi OPPOSTI**, e il difetto e' li'.  Un
>    `drawImage` non puo' diventare tre volte piu' caro perche' a monte c'e' un
>    decodificatore diverso.  **Una sincronizzazione si.**
>
> ⇒ ⭐ Il tratto 6 non misura «il disegno»: misura **`richiamo del
>   decodificatore → disegno finito`**, e sul cammino a decodifica hardware
>   quel tratto contiene **l'attesa che il fotogramma sia utilizzabile**.
>   Il numero e' vero; ⛔ **l'ETICHETTA e' falsa**, ed e' l'etichetta che e'
>   finita nei documenti come *«il collo di bottiglia nuovo e' IL DISEGNO,
>   28,0 ms su 78,1, il 36 %»*.
>
> ⛔⛔ **E la conseguenza e' costata una corsia di lavoro**: chi va a
>     ottimizzare `drawImage` — cioe' l'anello A2 — trova `[M]` **8,45 ms**, e
>     conclude che HEVC e' *piu' economico*.  ⭐ **A2 e la fase 3 non si
>     contraddicono: misurano i due lati di un confine mal posto.**  8,45 e' il
>     costo vero di disegnare un fotogramma **gia' pronto**; 28,0 e' quello di
>     aspettare che lo sia **piu'** disegnarlo.
>
> ⭐ **Quel che invece REGGE, e va detto**: la somma 5+6 e' la grandezza che si
>    conserva, e dice una cosa vera e nuova — **il costo del CLIENT dopo il
>    filo raddoppia passando ad HEVC**: `[M]` **15,42 e 15,47** sui due giri AV1
>    (che concordano entro 0,05 ms) contro **25,88 e 30,75** sui due HEVC.
>    ⇒ **+10,5 .. +15,3 ms**, e il tetto sfora **anche** per un motivo che sta
>    nel client, non solo nel codificatore del server.
>
> ⚠ **Due dispersioni che nessun documento porta accanto al 28,00:**
>   · fra i due giri **HEVC** il tratto 6 vale `[M]` **25,105 (n=799)** e
>     **29,250 (n=375)** — **4,15 ms**, e cambia solo il codificatore del
>     SERVER, che il `drawImage` del client non puo' vedere;
>   · fra due giri della **stessa** configurazione hardware vale **25,105
>     (n=799)** e **27,995 (n=379)** — **2,89 ms**, l'**11 %**.
>
> ⛔ **E il palco NON e' la spiegazione**: `[M]` rileggendo il campo `palco` dei
>    tre giri, browser, bandiere, GPU (`ANGLE (Intel, Mesa Intel(R) Graphics)`)
>    e contesa (`clienti_sull_xvfb: 0`, cioe' il desktop dell'utente) sono
>    **identici**.  ⇒ Quel che cambia e' il codec, e `drawImage` **non sa** quale
>    codec ha prodotto il fotogramma.  Qualcosa si e' spostato **attraverso il
>    confine fra il tratto 5 e il 6**, e non e' il disegno ad essere diventato
>    caro.
>
> ⛔ **E il confronto da cui esce la tabella «71,86 contro 78,12» di
>    `README.md` cambia DUE cose, non una**: `E-C` e' AV1 ed `E3` e' HEVC, e col
>    codec cambia **anche il decodificatore del client**.  ⇒ Le due righe **non
>    sono confrontabili tratto per tratto**.  ⭐ Il confronto `E2-A` contro
>    `E2-B` invece **e' pulito** (cambia solo il codificatore del server) e
>    regge: l'architettura resta assolta.
>
> ⛔⛔ **E LA CELLA CHE MANCA, ed e' quella che chiuderebbe la questione.**
>     `[M]` `banchi/03-palco-esiti.jsonl`, giro **`con-gpu`**, dice
>     `powerEfficient: **true**` per **HEVC Main10**, VP9 profilo 2 e H.264 —
>     cioe' «li decodifico in hardware».  ⛔ **AV1 in quel giro non e' stato
>     provato**: le voci sono tre, e AV1 non e' fra loro.
>     ⚠ L'unica lettura di AV1 che esiste (`02-pagina-esiti.jsonl`, giro
>     `f25-chrome-1786535362`) dice `powerEfficient: false` — ⛔ **ma in quello
>     stesso giro anche VP9 dice `false` e HEVC dice `supported: false`**, cioe'
>     e' la firma del browser **accecato** di `LEZIONI.md` §2.0.  ⇒ **Non e'
>     utilizzabile**, ed e' proprio il difetto che quella lezione descrive.
>     ⇒ ⭐ **Il confronto AV1/HEVC su cui la fase 3 si chiude non ha mai avuto la
>       sua cella di controllo**, e prenderla costa **una riga**: rigirare
>       `03-palco-dipinge.py` con AV1 nell'elenco.
>
> ⭐ **La cura, ed e' dentro questo banco**: il tratto si spacca in due
>    (`9 richiamo → 1° drawImage finito` e `10 1° → 2° drawImage finito`)
>    avvolgendo `CanvasRenderingContext2D.prototype.drawImage` nel prologo.
>    ⇒ **Prova falsificabile**: se il tratto e' l'attesa del fotogramma, il 9 e'
>    grande e il 10 e' piccolo; se e' davvero il disegno, sono simili.
>    ⛔ Il controllo Q8 pretende che i due numeri **ci siano**, e non giudica.
>
> ⚠ **E QUEL CHE RESTA `[?]`, dichiarato invece che colmato**: *perche'* il
>   costo si sposti attraverso quel confine.  L'ipotesi — il decodificatore
>   hardware consegna il `VideoFrame` prima che la sua superficie sia
>   utilizzabile, e il primo `drawImage` paga l'attesa — **e' `[?]`, non `[M]`**,
>   e resta tale finche' Q8 non gira sul ferro e finche' la cella AV1 di
>   `03-palco-esiti.jsonl` non c'e'.
> ⛔ **Il FATTO invece e' `[M]` e non dipende dall'ipotesi**: i due tratti si
>    scambiano il costo a palco identico, e `drawImage` non sa quale codec ha
>    prodotto il fotogramma.
"""
import argparse
import base64
import importlib.util
import json
import os
import random
import statistics
import struct
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
ESITI = os.path.join(QUI, "04-b30-esiti.jsonl")
PONTE = os.path.join(QUI, "04-b30-ponte.py")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ⛔ I codici d'uscita, in un posto solo e con un nome.  Un numero nudo dentro
#    un `return` si copia sbagliato al primo ritocco.
USCITA_CONFORME = 0
USCITA_NON_CONFORME = 1
USCITA_USO = 2
USCITA_NIENTE_DA_GIUDICARE = 3


def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")


# ═══════════════════════════════════════════════════════════════════════════
# §1  ATTREZZI — ⭐ IMPORTATI da `03-b17`, non ricopiati
# ═══════════════════════════════════════════════════════════════════════════
_moduli = {}


def carica(nome, percorso):
    """⛔ `import 03-b17-ritardo` e' impossibile (il nome comincia per cifra)."""
    if nome in _moduli:
        return _moduli[nome]
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    _moduli[nome] = m
    return m


def b17():
    """⭐ L'anello della fase 3.  ⛔ Si IMPORTA, non si ricopia: se cambia, questo
    banco se ne accorge — e se lo avessi ricopiato, no.

    ⚠ Da qui arrivano `Palco`, `dist`, `regime`, `Orologi`, `con_pezzo_cieco`,
      `leggi_celle`, `celle_unita_giusta`, `delta_conto`.  ⛔ Nessuno di questi
      viene riscritto qui: se ogni banco si scrivesse la propria «mediana», la
      parola vorrebbe dire cinque cose diverse.
    """
    return carica("b17", os.path.join(QUI, "03-b17-ritardo.py"))


def marca_modulo():
    return carica("marca", os.path.join(QUI, "03-marca.py"))


def ponte_modulo():
    return carica("ponte30", PONTE)


def dist(v, scala=1.0):
    return b17().dist(v, scala)


def regime(campioni, **kw):
    return b17().regime(campioni, **kw)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I DUE PEZZI CIECHI, IN UNA FUNZIONE SOLA
#
#    Perche' non si possa stampare un numero senza.  Quello in uscita e' della
#    fase 3 (`STUDI.md` §web §6.2); ⭐ quello in INGRESSO e' nuovo, e nessuno lo aveva
#    ancora nominato.
# ═══════════════════════════════════════════════════════════════════════════
CIECO_USCITA_MIN_MS, CIECO_USCITA_MAX_MS = 16.0, 40.0
CIECO_INGRESSO_MIN_MS, CIECO_INGRESSO_MAX_MS = 4.0, 12.0


def con_pezzi_ciechi(ms, su_xvfb=True):
    """⛔ Il numero, coi DUE pezzi ciechi accanto e ciascuno col suo verso."""
    if ms is None:
        return "—"
    a = CIECO_INGRESSO_MIN_MS + (0.0 if su_xvfb else CIECO_USCITA_MIN_MS)
    b = CIECO_INGRESSO_MAX_MS + (0.0 if su_xvfb else CIECO_USCITA_MAX_MS)
    coda = ("⚠ su Xvfb il pezzo cieco in USCITA non esiste affatto (non c'e' "
            "compositore): qui si somma solo quello in ingresso"
            if su_xvfb else
            "⇒ e i 16-40 ms in uscita ci sono, perche' un compositore c'e'")
    return ("%.1f ms MISURATI  +  [?] %.0f-%.0f ms di pezzo cieco in INGRESSO "
            "(mano → `event.timeStamp`: dispositivo, nucleo e compositore del "
            "CLIENT, nessuna API della pagina li vede)  +  [?] %.0f-%.0f ms di "
            "pezzo cieco in USCITA (disegno finito → pixel acceso, `STUDI.md` §web "
            "§6.2)  ⇒ %.1f-%.1f ms sullo schermo di un utente, PIU' LA RETE.  %s"
            % (ms, CIECO_INGRESSO_MIN_MS, CIECO_INGRESSO_MAX_MS,
               CIECO_USCITA_MIN_MS, CIECO_USCITA_MAX_MS,
               ms + a, ms + b, coda))


# ═══════════════════════════════════════════════════════════════════════════
# §1-bis  L'ECO — la stessa aritmetica di `04-b30-scena.c`, dall'altra parte
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Le due implementazioni sono scritte DUE VOLTE apposta, in due linguaggi.
#    E' la stessa scelta che `03-b17` fa per i 28 byte: «se un giorno i due
#    lettori divergono, quel disaccordo e' il regalo».  La certificazione le
#    fa incontrare su valori noti (controllo B).
ECO_NIENTE, ECO_PUNTATORE, ECO_PULSANTE, ECO_ROTELLA, ECO_TASTO = 0, 1, 2, 3, 4
ECO_NOMI = {0: "niente", 1: "puntatore", 2: "pulsante", 3: "rotella", 4: "tasto"}


def eco_puntatore(x, y):
    """L'eco che la scena dipinge quando riceve un puntatore in (x, y)."""
    return ((ECO_PUNTATORE & 0xF) << 28) | ((x & 0x3FFF) << 14) | (y & 0x3FFF)


def eco_pulsante(codice, premuto, seq):
    return (((ECO_PULSANTE & 0xF) << 28) | ((codice & 0xFFFF) << 12)
            | ((1 if premuto else 0) << 11) | (seq & 0x7FF))


def eco_tasto(codice, premuto, seq):
    return (((ECO_TASTO & 0xF) << 28) | ((codice & 0xFFFF) << 12)
            | ((1 if premuto else 0) << 11) | (seq & 0x7FF))


def eco_scomponi(v):
    """Da 32 bit al fatto.  ⛔ Ritorna SEMPRE un dizionario col `tipo`, anche
    quando il tipo e' sconosciuto: «non l'ho capito» e «non c'era» sono due
    cose diverse."""
    if v is None:
        return {"tipo": None, "perche": "⛔ nessun eco: non ho potuto guardare"}
    t = (v >> 28) & 0xF
    d = {"grezzo": v, "tipo": t, "nome": ECO_NOMI.get(t, "sconosciuto")}
    if t == ECO_PUNTATORE:
        d["x"] = (v >> 14) & 0x3FFF
        d["y"] = v & 0x3FFF
    elif t in (ECO_PULSANTE, ECO_TASTO):
        d["codice"] = (v >> 12) & 0xFFFF
        d["premuto"] = bool((v >> 11) & 1)
        d["seq"] = v & 0x7FF
    elif t == ECO_ROTELLA:
        d["asse_x"] = ((v >> 14) & 0x3FFF) - 8192
        d["asse_y"] = (v & 0x3FFF) - 8192
    elif t == ECO_NIENTE:
        d["perche"] = ("⚠ la scena non ha ancora ricevuto NESSUN input: l'eco "
                       "e' zero.  Non e' «l'eco non si legge»")
    return d


# ═══════════════════════════════════════════════════════════════════════════
# §1-ter  I TIPI DI `RCP.md` §7.3, e l'inquadratura di §6.1
# ═══════════════════════════════════════════════════════════════════════════
RCP_PUNTATORE = 0x0101
RCP_PULSANTE = 0x0102
RCP_ROTELLA = 0x0103
RCP_LETTERA = 0x0104
RCP_POSIZIONE = 0x0105
RCP_INPUT = {RCP_PUNTATORE: "PUNTATORE", RCP_PULSANTE: "PULSANTE",
             RCP_ROTELLA: "ROTELLA", RCP_LETTERA: "LETTERA",
             RCP_POSIZIONE: "POSIZIONE_TASTO"}
# ⛔ Le lunghezze del corpo che §7.3 prescrive.  Servono a due cose: riconoscere
#    un messaggio di input sul filo, e **accorgersi che il prodotto ne manda uno
#    di lunghezza sbagliata** invece di leggerlo storto e dare la colpa altrove.
RCP_LUNGHEZZE = {RCP_PUNTATORE: 4 + 8 + 4 + 4, RCP_PULSANTE: 4 + 8 + 2 + 1,
                 RCP_ROTELLA: 4 + 8 + 4 + 4, RCP_LETTERA: 4 + 8 + 4,
                 RCP_POSIZIONE: 4 + 8 + 2 + 1}


def leggi_messaggio_input(b):
    """⛔ Legge UN messaggio di input dai byte grezzi, con `RCP.md` §6.1 e §7.3.

    Ritorna `(fatto, byte_consumati)`.  ⛔ `fatto` e' `None` se non e' un input,
    e `byte_consumati` e' 0 se non ce n'e' abbastanza per decidere: «non e' un
    input» e «non ho ancora abbastanza byte» sono due risposte diverse, e
    confonderle farebbe buttare via il primo messaggio di ogni stream.
    """
    if len(b) < 6:
        return None, 0
    tipo, lung = struct.unpack(">HI", b[:6])
    if tipo not in RCP_INPUT:
        return None, -1        # -1 = «non e' un input, e non lo sara' mai»
    if lung > (1 << 20):
        return None, -1
    if len(b) < 6 + lung:
        return None, 0
    corpo = b[6:6 + lung]
    f = {"tipo": tipo, "nome": RCP_INPUT[tipo], "lunghezza": lung}
    atteso = RCP_LUNGHEZZE[tipo]
    if lung != atteso:
        # ⛔ Non si prova a leggerlo lo stesso: si DICHIARA.  Un corpo di
        #    lunghezza sbagliata letto storto produce coordinate plausibili e
        #    false, e il banco andrebbe ad accusare l'iniezione.
        f["violazione"] = ("⛔ %s ha lunghezza %d e §7.3 ne vuole %d"
                           % (f["nome"], lung, atteso))
        return f, 6 + lung
    f["id"], f["istante_us"] = struct.unpack(">IQ", corpo[:12])
    resto = corpo[12:]
    if tipo == RCP_PUNTATORE:
        f["x"], f["y"] = struct.unpack(">II", resto)
    elif tipo in (RCP_PULSANTE, RCP_POSIZIONE):
        f["codice"], f["premuto"] = struct.unpack(">HB", resto)
    elif tipo == RCP_ROTELLA:
        f["asse_x"], f["asse_y"] = struct.unpack(">ii", resto)
    elif tipo == RCP_LETTERA:
        (f["carattere"],) = struct.unpack(">I", resto)
    return f, 6 + lung


# ═══════════════════════════════════════════════════════════════════════════
# §2  IL PROLOGO — quel che gira DENTRO la pagina, senza toccarla
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Si installa con `Page.addScriptToEvaluateOnNewDocument`, cioe' PRIMA di
#    ogni script della pagina.  E' la tecnica di `03-b17-ritardo.py` e di
#    `02-pagina-misura-cdp.py`, e la ragione e' la stessa: un banco che
#    innestasse la misura dentro `pagina.html` misurerebbe la pagina
#    strumentata, non il prodotto (decisione P2-6 §7 punto 1).
#
# ⛔ E QUI FA TRE COSE CHE `03-b17` NON FA:
#      1. ascolta gli eventi di input **in fase di cattura**, prima di ogni
#         gestore della pagina  ⇒ il `t0` scomodo;
#      2. **legge i byte che escono** e ci riconosce `RCP.md` §7.3  ⇒ l'`id`
#         e le coordinate spedite, letti DOVE LA COSA SUCCEDE e non
#         nell'intenzione (`LEZIONI.md` §1.9 regola 5);
#      3. avvolge `drawImage` ⇒ il tratto 6 della fase 3 si spacca in due.
PROLOGO = r"""
(function () {
  if (window.__B30) return;
  const B = {
    campioni: [], intestazioni: new Map(), stream: [],
    eventi: [], spediti: [], violazioni: [],
    conti: { decoder: 0, richiami: 0, letture: 0, senza_deposito: 0,
             senza_intestazione: 0, sonda: 0, buttati: 0,
             eventi_visti: 0, byte_usciti: 0, messaggi_usciti: 0,
             input_riconosciuti: 0, non_input: 0 },
    grana: null, isolata: null, versione: 1,
    scorrimento: [0, 0], leggi: true, crudi: [], crudi_voluti: 0,
    finestra: [0, 0],
    t_origine: performance.timeOrigin,
    costo_lettura_us: [], costo_disegno_us: [],
  };
  window.__B30 = B;

  /* ── la geometria della marca, gemella di `03-marca.py:119-131` ───────── */
  const CELLA = 24, MARGINE = 32, COLONNE = 18, RIGHE = 8, BIT = 144;
  const DENTRO = Math.max(2, CELLA >> 2);
  const LATO = CELLA - 2 * DENTRO;
  const REG_L = MARGINE + COLONNE * CELLA + 16;    /* 480 */
  const REG_A = MARGINE + RIGHE * CELLA + 16;      /* 240 */
  const KR = 0.2126, KG = 0.7152, KB = 0.0722;
  /* ⭐ La seconda marca sta UNA REGIONE sotto la prima: e' la stessa
     aritmetica di `regione_altezza()` in `04-b30-scena.c`. */
  B.finestra_eco = [0, REG_A];

  /* ── la grana del cronometro, MISURATA e non dedotta (Q10) ────────────── */
  B.isolata = (typeof crossOriginIsolated !== "undefined") ? crossOriginIsolated : null;
  (function () {
    const d = [];
    let a = performance.now();
    for (let i = 0; i < 200000; i++) {
      const b = performance.now();
      if (b !== a) { d.push(b - a); a = b; }
      if (d.length >= 4000) break;
    }
    d.sort(function (x, y) { return x - y; });
    B.grana = { salti: d.length, minimo_ms: d.length ? d[0] : null,
                mediano_ms: d.length ? d[d.length >> 1] : null };
  })();

  /* ══ 0. ⭐⭐ GLI EVENTI DI INPUT — il `t0` SCOMODO ══════════════════════
     ⛔ In fase di CATTURA (`{capture: true}`) e su `window`: cosi' questo
        ascoltatore gira PRIMA di qualunque gestore della pagina, e `t0` e' il
        primo istante in cui il prodotto avrebbe potuto vedere l'evento.
     ⛔ E si legge `e.timeStamp`, non `performance.now()`: il primo e' il
        momento in cui **l'evento e' nato**, il secondo quello in cui e' stato
        consegnato a noi.  Prendere il secondo si regalerebbe la differenza,
        che il campo `ascolto_ms` MISURA invece di stimare. */
  const TIPI = ["pointermove", "pointerdown", "pointerup", "mousemove",
                "mousedown", "mouseup", "wheel", "keydown", "keyup"];
  for (const t of TIPI) {
    window.addEventListener(t, function (e) {
      if (B.eventi.length > 200000) return;
      B.conti.eventi_visti++;
      B.eventi.push({
        tipo: t, t_evento: e.timeStamp, t_ascolto: performance.now(),
        fidato: e.isTrusted === true,
        x: (e.clientX === undefined) ? null : e.clientX,
        y: (e.clientY === undefined) ? null : e.clientY,
        codice: e.code || null, bottone: (e.button === undefined) ? null : e.button,
        dy: (e.deltaY === undefined) ? null : e.deltaY,
      });
    }, { capture: true, passive: true });
  }

  /* ══ 1. §6.2: i 28 byte, riscritti QUI e non presi dalla pagina ═════════
     ⭐ E' voluto: se un giorno i due lettori divergono, quel disaccordo e' il
        regalo.  Stessi offset di `src/rcp.c`. */
  function intestazione(u8) {
    if (u8.length < 28) return null;
    const v = new DataView(u8.buffer, u8.byteOffset, 28);
    return { tipo: v.getUint16(0), codec: v.getUint16(2),
             larghezza: v.getUint32(4), altezza: v.getUint32(8),
             numero: v.getUint32(12),
             istante: Number(v.getBigUint64(16)),
             input: v.getUint32(24) };
  }

  /* ══ 2. ⭐⭐ I BYTE CHE ESCONO — l'input, letto SUL FILO ═════════════════
     ⛔ Il banco NON sa (e non deve sapere) come il prodotto decide di mandare
        l'input: legge i byte e ci riconosce `RCP.md` §6.1 + §7.3.  Se non
        riconosce niente, lo dice — ed e' il caso «non ho niente da giudicare».
     ⚠ Un solo `id` letto qui vale piu' di dieci righe di registro della
       pagina: e' il denominatore letto DOVE LA COSA SUCCEDE. */
  const TIPI_INPUT = { 0x0101: 20, 0x0102: 15, 0x0103: 20, 0x0104: 16, 0x0105: 15 };
  const NOMI_INPUT = { 0x0101: "PUNTATORE", 0x0102: "PULSANTE",
                       0x0103: "ROTELLA", 0x0104: "LETTERA",
                       0x0105: "POSIZIONE_TASTO" };

  function spia_uscita(stato, chunk) {
    const ora = performance.now();
    let u8;
    try { u8 = (chunk instanceof Uint8Array) ? chunk : new Uint8Array(chunk); }
    catch (e) { return; }
    B.conti.byte_usciti += u8.length;
    /* si accumula: un messaggio puo' arrivare spezzato in piu' write */
    const vecchio = stato.resto;
    const tutto = new Uint8Array(vecchio.length + u8.length);
    tutto.set(vecchio, 0); tutto.set(u8, vecchio.length);
    let o = 0;
    while (tutto.length - o >= 6) {
      const dv = new DataView(tutto.buffer, tutto.byteOffset + o, 6);
      const tipo = dv.getUint16(0), lung = dv.getUint32(2);
      if (!(tipo in TIPI_INPUT)) { B.conti.non_input++; o = tutto.length; break; }
      if (tutto.length - o < 6 + lung) break;
      const c = new DataView(tutto.buffer, tutto.byteOffset + o + 6, lung);
      const f = { tipo: tipo, nome: NOMI_INPUT[tipo], lunghezza: lung,
                  t_filo: ora };
      if (lung !== TIPI_INPUT[tipo]) {
        B.violazioni.push({ perche: "lunghezza", tipo: tipo, lunghezza: lung,
                            attesa: TIPI_INPUT[tipo] });
      } else {
        f.id = c.getUint32(0);
        f.istante_us = Number(c.getBigUint64(4));
        if (tipo === 0x0101) { f.x = c.getUint32(12); f.y = c.getUint32(16); }
        else if (tipo === 0x0102 || tipo === 0x0105) {
          f.codice = c.getUint16(12); f.premuto = c.getUint8(14);
        } else if (tipo === 0x0103) {
          f.asse_x = c.getInt32(12); f.asse_y = c.getInt32(16);
        } else if (tipo === 0x0104) { f.carattere = c.getUint32(12); }
        B.conti.input_riconosciuti++;
        if (B.spediti.length < 200000) B.spediti.push(f);
      }
      B.conti.messaggi_usciti++;
      o += 6 + lung;
    }
    stato.resto = tutto.subarray(o);
  }

  function avvolgi_scrittore(w) {
    const stato = { resto: new Uint8Array(0) };
    const vero = w.write.bind(w);
    w.write = function (chunk) { try { spia_uscita(stato, chunk); } catch (e) {}
                                 return vero(chunk); };
    return w;
  }

  function avvolgi_scrivibile(s) {
    if (!s || s.__b30) return s;
    try {
      const vero = s.getWriter.bind(s);
      s.getWriter = function () { return avvolgi_scrittore(vero()); };
      Object.defineProperty(s, "__b30", { value: true });
    } catch (e) {}
    return s;
  }

  /* ══ 3. WEBTRANSPORT: quel che entra e quel che esce ════════════════════ */
  const VeroWT = window.WebTransport;
  if (VeroWT) {
    window.WebTransport = function (url, opzioni) {
      const wt = new VeroWT(url, opzioni);
      const vero = Object.getOwnPropertyDescriptor(
        Object.getPrototypeOf(wt), "incomingUnidirectionalStreams");
      const originale = vero ? vero.get.call(wt) : wt.incomingUnidirectionalStreams;
      const lettore = originale.getReader();
      const avvolto = new ReadableStream({
        async pull(c) {
          const r = await lettore.read();
          if (r.done) { c.close(); return; }
          c.enqueue(spia(r.value));
        }
      });
      Object.defineProperty(wt, "incomingUnidirectionalStreams",
                            { get: function () { return avvolto; },
                              configurable: true });
      /* ⭐ E il verso d'USCITA, che alla fase 3 non serviva a nessuno. */
      try {
        const cu = wt.createUnidirectionalStream.bind(wt);
        wt.createUnidirectionalStream = function () {
          return cu().then(avvolgi_scrivibile);
        };
      } catch (e) {}
      try {
        const cb = wt.createBidirectionalStream.bind(wt);
        wt.createBidirectionalStream = function () {
          return cb().then(function (s) {
            if (s && s.writable) avvolgi_scrivibile(s.writable);
            return s;
          });
        };
      } catch (e) {}
      try { if (wt.datagrams) avvolgi_scrivibile(wt.datagrams.writable); }
      catch (e) {}
      return wt;
    };
    window.WebTransport.prototype = VeroWT.prototype;
  }

  function spia(flusso) {
    const s = { t_primo: null, t_ultimo: null, byte: 0, testa: [],
                testa_byte: 0, i: null, pezzi: 0 };
    B.stream.push(s);
    const lettore = flusso.getReader();
    return new ReadableStream({
      async pull(c) {
        let r;
        try { r = await lettore.read(); }
        catch (e) { s.t_ultimo = performance.now(); s.azzerato = true; c.error(e); return; }
        if (r.done) {
          s.t_ultimo = performance.now();
          if (s.i && s.i.istante) B.intestazioni.set(s.i.istante, s);
          c.close();
          return;
        }
        const ora = performance.now();
        if (s.t_primo === null) s.t_primo = ora;
        s.pezzi++;
        s.byte += r.value.length;
        if (s.testa_byte < 28) {
          s.testa.push(r.value.subarray(0, Math.min(28 - s.testa_byte, r.value.length)));
          s.testa_byte += s.testa[s.testa.length - 1].length;
          if (s.testa_byte >= 28) {
            const t = new Uint8Array(28); let o = 0;
            for (const p of s.testa) { t.set(p, o); o += p.length; }
            s.i = intestazione(t);
            if (s.i && s.i.istante) B.intestazioni.set(s.i.istante, s);
          }
        }
        c.enqueue(r.value);
      }
    });
  }

  /* ══ 4. ⭐⭐ `drawImage` — il tratto 6 della fase 3 si spacca in due ═════
     ⛔ Vedi il riquadro in testa al file: il tratto «richiamo → disegno
        finito» **non e' il disegno**, e il modo di dimostrarlo e' misurare i
        due `drawImage` separatamente.  Se il primo e' grande e il secondo
        piccolo, quel che si misurava era l'ATTESA del fotogramma.
     ⚠ E il costo dell'involucro entra in Q9 come tutto il resto. */
  B.disegni = [];
  /* ⭐ `veroDI` sta FUORI dal blocco perche' serve anche a §4-bis: le letture
     del banco NON devono finire in `B.disegni`, o il banco conterebbe i propri
     disegni fra quelli del prodotto. */
  let veroDI = null;
  const proto = window.CanvasRenderingContext2D
              && window.CanvasRenderingContext2D.prototype;
  if (proto && proto.drawImage) {
    veroDI = proto.drawImage;
    proto.drawImage = function () {
      const a = performance.now();
      const r = veroDI.apply(this, arguments);
      const b = performance.now();
      if (B.disegni.length < 64) B.disegni.push(b - a);
      return r;
    };
  }

  /* ══ 4-bis. ⭐⭐⭐ LA STRADA VERA — `bitmaprenderer`, E IL CONFINE RESTA
     ═══════════════════════════════════════ SCOMODO ══════════════════════════

     ⛔⛔ IL DIFETTO CHE QUESTO PEZZO CURA, e va detto prima della cura.

     Dal 20 agosto 2026 (`DECISIONI.md` §5.4) la pagina dipinge con
     `bitmaprenderer` + `createImageBitmap`.  Su quella strada:
       · il deposito 2D **non esiste** ⇒ §6 non ha da dove leggere i pixel;
       · `drawImage` **non viene mai chiamato** ⇒ i tratti 9 e 10 spariscono;
       · ⛔⛔ e soprattutto **`createImageBitmap` e' ASINCRONA**: il richiamo
         del prodotto (`mostra()`) ritorna PRIMA che sia stato dipinto
         qualunque cosa.  ⇒ Un banco che prendesse `t_dip` al ritorno del
         richiamo — cioe' quel che questo file faceva — consegnerebbe un numero
         **piu' piccolo del vero** chiamandolo «scomodo».  E' `LEZIONI.md`
         §1.20 in persona: il confine comodo si sceglie da se' se nessuno lo
         nomina, e qui si era spostato **da solo** quando e' cambiato il
         prodotto.

     ⭐⭐ LA CURA, e sono due mosse che vanno insieme:

       1. **il confine si chiude dove lo schermo cambia davvero**, cioe' DOPO
          `transferFromImageBitmap`.  ⛔ Non quando la promessa si risolve
          (li' l'immagine e' in mano ma non e' al vetro) e non quando il
          richiamo ritorna (li' non c'e' niente).
       2. **i pixel si leggono dal vetro**.  Il contesto `bitmaprenderer` non
          ha `getImageData` — non ha nessun accesso ai pixel — ⭐ ma la TELA
          si': un `<canvas>` e' una sorgente valida per `drawImage` qualunque
          sia il contesto che lo dipinge.  ⇒ Si ricopia la sola REGIONE della
          marca (480x240) su una tela di servizio 2D e la si rilegge di li'.
          ⛔ E la si legge DOPO il trasferimento, non dall'`ImageBitmap` prima:
          leggere prima vorrebbe dire leggere qualcosa che sullo schermo non
          c'e' ancora — e per giunta ritardarlo.

     ⛔⛔ E LA CURA NON SI CREDE, SI PROVA: `B.ritardo_vetro_ms` innesta un
         ritardo NOTO fra «il fotogramma e' pronto» e «il fotogramma e' al
         vetro».  Se il confine e' al posto giusto, il numero sale di quel
         tanto (Q11); se si chiudesse prima, il ritardo sarebbe **invisibile**
         e il banco avrebbe l'aria di funzionare.
     ⭐ E accanto si consegna `t_dip_vecchio` — l'istante in cui il richiamo del
        prodotto e' RITORNATO, cioe' il confine sbagliato — cosi' i due si
        guardano in faccia dentro lo STESSO giro. */
  B.strada = null;               /* "2d" | "bitmaprenderer" — DEDOTTA dai fatti */
  B.attesa = new Map();          /* pts → il campione a meta', in attesa del vetro */
  B.pts_in_corso = null;
  B.cib_per_pts = 0;
  B.ritardo_vetro_ms = 0;        /* ⭐⭐ il guasto innestato di Q11 */
  B.bmp_pts = (typeof WeakMap === "function") ? new WeakMap() : null;
  B.bmp_pronta = (typeof WeakMap === "function") ? new WeakMap() : null;
  B.conti.trasferimenti = 0;
  B.conti.trasferimenti_senza_pts = 0;
  B.conti.mai_arrivati_al_vetro = 0;
  B.conti.senza_tela = 0;
  B.conti.cib = 0;

  /* ⛔ `createImageBitmap` si avvolge SENZA incatenare: si torna la promessa
     ORIGINALE, non `p.then(...)`.  Incatenarla metterebbe un microtask del
     banco fra la risoluzione e il gestore del prodotto — cioe' il banco
     ritarderebbe quel che misura.  ⭐ Il nostro gestore e' registrato per
     PRIMO, quindi gira prima di quello del prodotto e l'istante che segna e'
     quello della risoluzione. */
  const VeroCIB = window.createImageBitmap;
  if (VeroCIB && B.bmp_pts) {
    window.createImageBitmap = function (sorgente) {
      let pts = null;
      try {
        if (B.pts_in_corso !== null && sorgente
            && sorgente.timestamp === B.pts_in_corso) pts = B.pts_in_corso;
      } catch (e) { /* una sorgente che non e' un `VideoFrame` */ }
      const p = VeroCIB.apply(window, arguments);
      if (pts !== null) { B.cib_per_pts++; B.conti.cib++; }
      try {
        p.then(function (bmp) {
          if (pts !== null && bmp) {
            B.bmp_pts.set(bmp, pts);
            B.bmp_pronta.set(bmp, performance.now());
          }
        }, function () { /* il fallimento lo conta il prodotto */ });
      } catch (e) {}
      return p;
    };
  }

  const protoBM = window.ImageBitmapRenderingContext
                && window.ImageBitmapRenderingContext.prototype;
  if (protoBM && protoBM.transferFromImageBitmap) {
    const veroTF = protoBM.transferFromImageBitmap;
    protoBM.transferFromImageBitmap = function (bmp) {
      /* ⚠ `transferFromImageBitmap(null)` e' il modo dichiarato di SVUOTARE la
         tela (`src/pagina.html`, `spegni()`): non e' un disegno e non chiude
         nessuna sonda. */
      if (!bmp) return veroTF.call(this, bmp);
      let pts = null, t_pronta = null;
      try { pts = B.bmp_pts.get(bmp); t_pronta = B.bmp_pronta.get(bmp); }
      catch (e) {}
      /* ⭐⭐ IL RITARDO NOTO, innestato ESATTAMENTE fra «pronto» e «al vetro».
         ⛔ Si occupa il filo invece di dormire: un `await` cederebbe il turno e
            sposterebbe il fotogramma in un altro compito, che e' un'altra cosa
            da quella che si vuole imitare (un disegno davvero costoso). */
      if (B.ritardo_vetro_ms > 0) {
        const fino = performance.now() + B.ritardo_vetro_ms;
        while (performance.now() < fino) { /* apposta */ }
      }
      const r = veroTF.call(this, bmp);
      /* ⭐⭐⭐ QUI, e non un'istruzione prima: e' il piu' tardi che questa
         pagina sappia dire.  Da qui al pixel acceso restano i `[?]` 16-40 ms
         del compositore, che si DICHIARANO (C2) e non si misurano. */
      const t_dip = performance.now();
      B.conti.trasferimenti++;
      if (pts === undefined || pts === null) {
        B.conti.trasferimenti_senza_pts++;
        return r;
      }
      const base = B.attesa.get(pts);
      B.attesa.delete(pts);
      if (!base) return r;
      let celle = null, celle_eco = null, t_let = t_dip;
      if (B.leggi) {
        const c0 = performance.now();
        const tela = this.canvas || null;
        celle = leggi_marca_vetro(tela, B.finestra[0], B.finestra[1]);
        celle_eco = leggi_marca_vetro(tela, B.finestra_eco[0], B.finestra_eco[1]);
        t_let = performance.now();
        if (B.costo_lettura_us.length < 20000)
          B.costo_lettura_us.push((t_let - c0) * 1000);
      }
      deposita_campione(base, t_dip, t_let,
                        (t_pronta === undefined ? null : t_pronta),
                        celle, celle_eco, []);
      return r;
    };
  }

  function deposita_campione(base, t_dip, t_let, t_dip_a, celle, celle_eco,
                             disegni) {
    if (B.campioni.length >= 400000) return;
    B.campioni.push({
      t1: base.t1, t_dip: t_dip, t_let: t_let, pts: base.pts,
      l: base.l, a: base.a,
      celle: celle, celle_eco: celle_eco, guaio: base.guaio,
      strada: base.strada,
      /* ⭐ i due tempi del disegno, separati.  ⛔ `null` e non 0 quando non
         ce ne sono stati: «non ho potuto guardare» non e' «zero». */
      disegni_ms: disegni,
      t_dip_a: t_dip_a,
      /* ⛔⛔ IL CONFINE SBAGLIATO, consegnato ACCANTO e mai al posto del vero:
         l'istante in cui il richiamo del prodotto e' RITORNATO.  Sulla strada
         2D vuol dire «dipinto»; su `bitmaprenderer` non vuol dire niente. */
      t_dip_vecchio: base.t_dip_vecchio,
      visto: celle !== null, visto_eco: celle_eco !== null,
      finestra: base.finestra,
      t_primo: base.t_primo, t_ultimo: base.t_ultimo, byte: base.byte,
      tipo: base.tipo, numero: base.numero, input: base.input,
      t_dec: base.t_dec,
    });
  }

  /* ══ 5. VIDEODECODER: t1, il disegno del prodotto, poi i pixel ══════════ */
  const VeroVD = window.VideoDecoder;
  if (VeroVD) {
    function Avvolto(init) {
      const suo = init && init.output;
      const mio = Object.assign({}, init, {
        output: function (f) {
          /* ─── RIGA 1: `t1`.  ⛔ PRIMA di tutto, `STUDI.md` §web §6.3. ─────────── */
          const t1 = performance.now();
          const pts = f.timestamp;
          const l = f.displayWidth || f.codedWidth;
          const a = f.displayHeight || f.codedHeight;
          B.conti.richiami++;
          /* ─── RIGA 2: SI DISEGNA — e a disegnare e' il PRODOTTO. ───────── */
          B.disegni.length = 0;
          B.cib_per_pts = 0;
          /* ⭐ Si annuncia il `pts`: `createImageBitmap` non riceve nessuna
             etichetta, e la sua chiamata avviene DENTRO `suo(f)`.  ⇒ E' l'unico
             momento in cui l'immagine si puo' legare al fotogramma senza
             affidarsi all'ORDINE di risoluzione, che e' una grandezza
             sostitutiva (`LEZIONI.md` §1.13). */
          B.pts_in_corso = pts;
          let guaio = null;
          try { suo(f); } catch (e) { guaio = "" + e; }
          B.pts_in_corso = null;
          /* ⛔⛔ QUI il richiamo del prodotto e' RITORNATO — e questo NON e'
             «il disegno finito» su tutt'e due le strade.  Vedi §4-bis. */
          const t_dip_v = performance.now();
          const disegni = B.disegni.slice();
          const s = B.intestazioni.get(pts) || null;
          if (!s) B.conti.senza_intestazione++;
          const base = {
            t1: t1, pts: pts, l: l, a: a, guaio: guaio,
            t_dip_vecchio: t_dip_v, finestra: B.finestra.slice(),
            t_primo: s ? s.t_primo : null, t_ultimo: s ? s.t_ultimo : null,
            byte: s ? s.byte : null, tipo: s && s.i ? s.i.tipo : null,
            numero: s && s.i ? s.i.numero : null,
            input: s && s.i ? s.i.input : null,
            t_dec: B.t_dec.get(pts) || null,
          };
          if (B.cib_per_pts > 0) {
            /* ⭐⭐ LA STRADA VERA: il prodotto ha CHIESTO l'immagine e se n'e'
               andato.  Il campione si chiude in `transferFromImageBitmap`,
               cioe' quando lo schermo cambia davvero. */
            base.strada = "bitmaprenderer";
            B.strada = "bitmaprenderer";
            B.attesa.set(pts, base);
            /* ⛔ I fotogrammi che al vetro non arrivano MAI — scartati perche'
               tardivi (`conti.tardive` di §5.4) o perche' la sessione e'
               cambiata — non devono far crescere la mappa senza fine.  ⚠ E si
               CONTANO: buttarli in silenzio sarebbe un denominatore che cala
               senza che nessuno sappia perche'. */
            if (B.attesa.size > 240) {
              const primo = B.attesa.keys().next().value;
              B.attesa.delete(primo);
              B.conti.mai_arrivati_al_vetro++;
            }
          } else if (disegni.length === 0) {
            /* ⛔⛔ E QUESTO E' IL TERZO STATO, che la prima stesura non aveva —
               `[M]` 22 agosto 2026: **235 campioni su 2022** finivano marcati
               «2d» in un giro in cui la strada 2D non era stata usata mai.
               ⇒ Erano fotogrammi che il prodotto ha DECODIFICATO e non ha mai
               dipinto (scartati perche' tardivi, §5.4).  Chiamarli «2d» era
               scambiare «non e' successo» con «e' successa l'altra cosa» —
               `LEZIONI.md` §2.0, la stessa forma di «non arrivato» ≠ «non
               guardato».
               ⚠ Non sporcano nessun numero (senza pixel non chiudono nessuna
                 sonda), ⭐ ma contati per quel che sono dicono **quanti
                 fotogrammi non arrivano al vetro**, che e' un fatto del
                 prodotto e non del banco. */
            base.strada = "non dipinto";
            B.conti.mai_arrivati_al_vetro++;
            deposita_campione(base, t_dip_v, t_dip_v, null, null, null, disegni);
          } else {
            /* ─── LA STRADA 2D: e SOLO ADESSO si leggono i pixel, DUE regioni ─ */
            base.strada = "2d";
            if (B.strada === null) B.strada = "2d";
            let celle = null, celle_eco = null, t_let = t_dip_v;
            if (B.leggi) {
              const c0 = performance.now();
              celle = leggi_marca_celle(B.finestra[0], B.finestra[1]);
              celle_eco = leggi_marca_celle(B.finestra_eco[0], B.finestra_eco[1]);
              t_let = performance.now();
              if (B.costo_lettura_us.length < 20000)
                B.costo_lettura_us.push((t_let - c0) * 1000);
            }
            deposita_campione(base, t_dip_v, t_let,
                              disegni.length ? (t1 + disegni[0]) : null,
                              celle, celle_eco, disegni);
          }
          B.t_dec.delete(pts);
          B.intestazioni.delete(pts);
        }
      });
      const d = new VeroVD(mio);
      B.conti.decoder++;
      const suo_decode = d.decode.bind(d);
      d.decode = function (chunk) {
        B.t_dec.set(chunk.timestamp, performance.now());
        return suo_decode(chunk);
      };
      return d;
    }
    B.t_dec = new Map();
    Avvolto.isConfigSupported = VeroVD.isConfigSupported.bind(VeroVD);
    window.VideoDecoder = Avvolto;
  }

  /* ══ 6. LA LETTURA DEI PIXEL — DUE strade, e il campionatore e' UNO ══════
     ⛔ Il campionamento delle 144 celle sta in `celle_da()` e non e' scritto
        due volte: due copie divergerebbero, e la divergenza si vedrebbe come
        «la strada nuova legge marche un po' diverse» invece che come un baco. */
  function leggi_marca_celle(ox, oy) {
    const S = window.REMOTIX && window.REMOTIX.schermo;
    if (!S || !S.deposito || !S.deposito_p) { B.conti.senza_deposito++; return null; }
    if (S.deposito.width < ox + REG_L || S.deposito.height < oy + REG_A) {
      B.conti.sonda++; return null;
    }
    let d;
    try { d = S.deposito_p.getImageData(ox, oy, REG_L, REG_A).data; }
    catch (e) { B.conti.buttati++; return null; }
    B.conti.letture++;
    return celle_da(d, ox, oy);
  }

  /* ⭐⭐ LA LETTURA DELLA STRADA VERA — dalla TELA, cioe' dal vetro.
     ⛔ Il contesto `bitmaprenderer` non ha `getImageData`: non da' nessun
        accesso ai pixel.  ⭐ Ma la tela si', perche' un `<canvas>` e' una
        sorgente valida per `drawImage` qualunque sia il contesto che lo
        dipinge.  ⇒ Si ricopia la sola REGIONE della marca su una tela di
        servizio 2D di 480x240 e la si rilegge di li'.
     ⚠ Costa una copia in piu' della strada 2D, e il costo NON si stima: entra
       in `costo_lettura_us` come tutto il resto, e Q9 lo giudica. */
  let spec = null, spec_p = null;
  function leggi_marca_vetro(tela, ox, oy) {
    if (!tela) { B.conti.senza_tela++; return null; }
    if (tela.width < ox + REG_L || tela.height < oy + REG_A) {
      B.conti.sonda++; return null;
    }
    if (!spec_p) {
      try {
        spec = document.createElement("canvas");
        spec.width = REG_L; spec.height = REG_A;
        spec_p = spec.getContext("2d", { willReadFrequently: true });
      } catch (e) { spec_p = null; }
      if (!spec_p) { B.conti.buttati++; return null; }
    }
    let d;
    try {
      /* ⛔ `veroDI` e non `spec_p.drawImage`: l'involucro del §4 conta i
         disegni DEL PRODOTTO, e i miei non sono suoi. */
      (veroDI || spec_p.drawImage).call(spec_p, tela, ox, oy, REG_L, REG_A,
                                        0, 0, REG_L, REG_A);
      d = spec_p.getImageData(0, 0, REG_L, REG_A).data;
    } catch (e) { B.conti.buttati++; return null; }
    B.conti.letture++;
    return celle_da(d, ox, oy);
  }

  function celle_da(d, ox, oy) {
    const sx = B.scorrimento[0], sy = B.scorrimento[1];
    const v = new Array(BIT);
    for (let i = 0; i < BIT; i++) {
      const r = (i / COLONNE) | 0, k = i % COLONNE;
      const xa = MARGINE + k * CELLA + DENTRO + sx;
      const ya = MARGINE + r * CELLA + DENTRO + sy;
      let somma = 0;
      for (let y = ya; y < ya + LATO; y++) {
        let o = (y * REG_L + xa) * 4;
        for (let x = 0; x < LATO; x++, o += 4)
          somma += KR * d[o] + KG * d[o + 1] + KB * d[o + 2];
      }
      v[i] = somma / (LATO * LATO);
    }
    /* ⭐ Ogni tanto si porta fuori la REGIONE CRUDA insieme alle celle che il
       JavaScript ne ha ricavato.  ⛔ Serve a DUE cose, e la seconda e' quella
       che ha fermato il primo giro vero di questo banco:
         · il controllo del campionamento (le celle di JS contro quelle di
           numpy: se differiscono, il lettore certificato sta leggendo
           un'immagine che il banco non ha campionato come lui);
         · ⛔⛔ **lo SCORRIMENTO**: `leggi_celle` gira con `ricerca=0` — lo
           scorrimento non lo cerca, lo eredita.  Se nessuno lo misura sui
           pixel VERI, `B.scorrimento` resta [0,0] e ogni CRC salta: `[M]` 14
           agosto 2026, primo giro vero, **0 marche lette su 966** con la
           catena perfettamente funzionante. */
    if (B.crudi.length < B.crudi_voluti) {
      let s = "";
      for (let i = 0; i < d.length; i += 4)
        s += String.fromCharCode(d[i], d[i + 1], d[i + 2]);
      B.crudi.push({ l: REG_L, a: REG_A, ox: ox, oy: oy, b64: btoa(s),
                     celle: v.slice(), scorrimento: [sx, sy] });
    }
    return v;
  }

  /* ══ 7. IL RITIRO — si SVUOTA, cosi' due ritiri non contano due volte ═══ */
  B.prendi = function () {
    const cr = B.crudi; B.crudi = [];
    B.ultimi_crudi = cr;
    const c = B.campioni; B.campioni = [];
    const e = B.eventi; B.eventi = [];
    const s = B.spediti; B.spediti = [];
    const co = B.costo_lettura_us; B.costo_lettura_us = [];
    return { campioni: c, eventi: e, spediti: s, costo_lettura_us: co,
             crudi: cr, violazioni: B.violazioni.slice(0, 200),
             conti: Object.assign({}, B.conti), grana: B.grana,
             isolata: B.isolata, t_origine: B.t_origine,
             ora_pagina: performance.now(),
             /* ⭐ LA STRADA DI DISEGNO, DEDOTTA DAI FATTI e non dall'indirizzo:
                due giri su strade diverse non sono lo stesso banco (§4-bis). */
             strada: B.strada, in_attesa_del_vetro: B.attesa.size,
             ritardo_vetro_ms: B.ritardo_vetro_ms,
             ora_reale: performance.timeOrigin + performance.now(),
             pagina: window.REMOTIX && window.REMOTIX.schermo
                     ? Object.assign({}, window.REMOTIX.schermo.conti) : null,
             /* ⭐⭐ IL CONTROLLO INCROCIATO — e non e' una comodita'.
                Il PRODOTTO misura da se' le stesse due grandezze dei tratti 9
                e 10 (`src/pagina.html`: `bmp_ms` = chiamata → immagine in
                mano; `vetro_ms` = il trasferimento).  ⛔ Sono due lettori
                scritti da due persone diverse in due posti diversi: se un
                giorno divergono, quel disaccordo e' il regalo — e senza
                portarli fuori insieme non lo vedrebbe nessuno.
                ⚠ Il prodotto ne tiene 200: e' un campione recente, non tutto
                  il giro, e va letto cosi'. */
             pagina_disegno: window.REMOTIX && window.REMOTIX.schermo
                     ? { bmp_ms: (window.REMOTIX.schermo.bmp_ms || []).slice(),
                         vetro_ms: (window.REMOTIX.schermo.vetro_ms || []).slice() }
                     : null };
  };
})();
"""


# ═══════════════════════════════════════════════════════════════════════════
# §3  LA LETTURA DELLE DUE MARCHE
# ═══════════════════════════════════════════════════════════════════════════
def leggi_due_marche(c):
    """⛔ Legge le DUE marche di un campione col lettore CERTIFICATO, e mette in
    `c["marca"]` e `c["eco_marca"]`.

    ⭐ E fa il controllo che nessuna delle due potrebbe fare da sola: le due
       marche dello STESSO fotogramma devono portare lo **stesso `disegno`** nel
       primo campo.  ⛔ Se non lo portano, il banco sta leggendo meta' di un
       fotogramma e meta' del successivo — e ne ricaverebbe un ritardo
       plausibile e falso, che e' la forma d'errore peggiore.
    """
    m = b17()
    c["marca"] = m.leggi_celle(c["celle"]) if c.get("celle") else {
        "c_e": False, "perche": "⛔ non ho potuto GUARDARE la marca 1"}
    c["eco_marca"] = m.leggi_celle(c["celle_eco"]) if c.get("celle_eco") else {
        "c_e": False, "perche": "⛔ non ho potuto GUARDARE la marca 2 (l'eco)"}
    a, b = c["marca"], c["eco_marca"]
    if a.get("c_e") and b.get("c_e"):
        # ⛔ Il campo `disegno` della marca 2 porta l'ECO, non il disegno: il
        #    numero del disegno delle due marche si confronta sull'`istante`
        #    della marca 1 contro `eco_disegnato`? No — la marca 2 non lo
        #    porta.  ⇒ Il legame vero e' che le due marche stiano nello stesso
        #    fotogramma, e questo lo dice il fatto che si leggano ENTRAMBE con
        #    il CRC buono nello stesso `getImageData`.  ⚠ Si dichiara il
        #    limite invece di fingere un controllo che non c'e'.
        c["due_marche"] = True
        c["eco"] = eco_scomponi(b["disegno"])
    else:
        c["due_marche"] = False
        c["eco"] = eco_scomponi(None)
    return c


# ═══════════════════════════════════════════════════════════════════════════
# §4  L'ACCOPPIAMENTO — ⭐ i DUE confini, e si consegnano tutt'e due
# ═══════════════════════════════════════════════════════════════════════════
def accoppia(campioni, spediti, eventi, finestra_ms=1500.0):
    """⛔ Da (fotogrammi, input spediti, eventi del browser) alle SONDE.

    Una sonda e' un input di cui si conosce **tutto il cammino**:

        evento del browser → il prodotto lo spedisce → la scena lo riceve →
        la scena ridisegna → Mutter cattura → filo → decodifica → disegno

    ⛔ E ne escono DUE ritardi, non uno:
       · **scomodo** — il primo fotogramma in cui l'ECO nei pixel e' quello di
         QUESTO input.  E' il numero che si consegna;
       · **comodo**  — il primo fotogramma il cui campo `input` dei 28 byte e'
         >= all'`id`.  Si consegna accanto, e la differenza fra i due e' quel
         che il confine comodo si regala.

    ⚠ Funzione PURA: e' quel che la certificazione esercita.
    """
    campioni = sorted(campioni, key=lambda c: c.get("t1") or 0)
    # ⛔ Gli eventi si appaiano ai messaggi spediti per COORDINATE, non per
    #    ordine: l'ordine e' una grandezza sostitutiva (`LEZIONI.md` §1.13) e
    #    basta un evento in piu' (un `pointermove` che il prodotto non spedisce)
    #    per sfasare tutta la successione da li' in poi.
    per_xy = {}
    for e in eventi:
        if e.get("x") is None:
            continue
        per_xy.setdefault((e["x"], e["y"]), []).append(e)
    for v in per_xy.values():
        v.sort(key=lambda e: e["t_evento"])

    sonde = []
    for s in spediti:
        if s.get("tipo") != RCP_PUNTATORE or s.get("id") is None:
            continue
        atteso = eco_puntatore(s["x"], s["y"])
        # l'evento che l'ha generato: stesse coordinate, il piu' recente PRIMA
        # del momento in cui i byte sono usciti
        ev = None
        for e in per_xy.get((s["x"], s["y"]), []):
            if e["t_evento"] <= s["t_filo"] and (ev is None
                                                 or e["t_evento"] > ev["t_evento"]):
                ev = e
        sonda = {"id": s["id"], "x": s["x"], "y": s["y"],
                 "t_filo": s["t_filo"], "eco_atteso": atteso,
                 "istante_client_us": s.get("istante_us")}
        if ev is None:
            # ⛔ Non si ripiega sul `t_filo`: sarebbe il confine COMODO messo
            #    al posto di quello scomodo senza dirlo.  Si dichiara e si
            #    butta la sonda.
            sonda["perche"] = ("⛔ nessun evento del browser con queste "
                               "coordinate prima della spedizione: non posso "
                               "prendere il `t0` scomodo, e NON ripiego sul "
                               "`t_filo` — sarebbe il confine comodo travestito")
            sonde.append(sonda)
            continue
        sonda["t_evento"] = ev["t_evento"]
        sonda["t_ascolto"] = ev["t_ascolto"]
        sonda["fidato"] = ev.get("fidato")
        # ── il confine SCOMODO: l'eco nei pixel ────────────────────────────
        for c in campioni:
            if (c.get("t1") or 0) < sonda["t_filo"]:
                continue
            if (c.get("t1") or 0) > sonda["t_filo"] + finestra_ms:
                break
            if c.get("eco", {}).get("grezzo") == atteso and c.get("due_marche"):
                sonda["scomodo"] = c
                break
        # ── il confine COMODO: il campo `input` dei 28 byte ────────────────
        for c in campioni:
            if (c.get("t1") or 0) < sonda["t_filo"]:
                continue
            if (c.get("t1") or 0) > sonda["t_filo"] + finestra_ms:
                break
            if c.get("input") is not None and c["input"] >= s["id"]:
                sonda["comodo"] = c
                break
        for nome in ("scomodo", "comodo"):
            c = sonda.get(nome)
            if c is not None and c.get("t_dip") is not None:
                sonda["ritardo_%s_ms" % nome] = c["t_dip"] - sonda["t_evento"]
        # ⛔⛔ IL TERZO NUMERO, e non e' un terzo confine: e' il confine
        #     SBAGLIATO, consegnato apposta perche' si possa vedere quanto
        #     mente.  Chiude quando il richiamo del prodotto RITORNA — che
        #     sulla strada `bitmaprenderer` e' PRIMA che sia stato dipinto
        #     qualunque cosa (`LEZIONI.md` §1.20, §4-bis del prologo).
        #     ⚠ Non entra mai in `ritardo_scomodo_ms`, e Q11 lo usa per
        #       DIMOSTRARE che il confine vero non si chiude li'.
        cv = sonda.get("scomodo")
        if cv is not None and cv.get("t_dip_vecchio") is not None:
            sonda["ritardo_vecchio_ms"] = cv["t_dip_vecchio"] - sonda["t_evento"]
        sonde.append(sonda)
    return sonde


# ═══════════════════════════════════════════════════════════════════════════
# §4-bis  ⭐⭐ LA TASTIERA, ACCOPPIATA A PARTE — e NON e' una copia per pigrizia
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ LA TESI DA REFUTARE (mandato O2, n. 3): *«la tastiera e il mouse hanno lo
#    stesso ritardo»*.  ⚠ Non e' detto, e il motivo e' nel prodotto: in modo
#    classico il mouse muove **un puntatore disegnato dalla pagina**
#    (`SPECIFICHE.md` §7.1), che l'utente vede subito e senza rete; la tastiera
#    deve fare **tutto il giro**.  ⇒ Mediarli darebbe un numero che l'utente
#    sente in due modi diversi.
#
# ⛔ E l'accoppiamento non puo' essere lo stesso di `accoppia()`: l'eco di un
#    tasto porta `(codice, premuto, seq)` e la `seq` la conta LA SCENA, non noi.
#    Non si puo' prevedere l'eco atteso come si fa con le coordinate.  ⇒ Si
#    riconosce dal codice e dal verso, e si pretende che la `seq` **avanzi** —
#    altrimenti un tasto ripetuto appaierebbe l'eco di quello di prima, cioe'
#    un ritardo piu' corto del vero ottenuto senza sbagliare nessun conto.
def _seq_avanti(nuova, vecchia):
    """La `seq` della scena e' a 11 bit e gira: «piu' recente» si decide
    sull'anello, non con un `>` che al giro di boa direbbe di no."""
    if vecchia is None or vecchia < 0:
        return True
    return 1 <= ((nuova - vecchia) & 0x7FF) <= 1024


def accoppia_tasti(campioni, spediti, eventi, mappa, finestra_ms=500.0):
    # ⛔⛔ LA FINESTRA E' 500 ms E NON 1500, E IL NUMERO E' MISURATO — `[M]` 14
    #     agosto 2026, primo giro della tastiera: ne sono uscite **27 sonde su
    #     584 con mediana 1 007 ms**, un numero verosimile e interamente falso.
    #
    #     I codici di prova sono dodici e si ripetono ogni ~840 ms.  Con una
    #     finestra di 1 500 ms, una sonda che si e' persa il PROPRIO eco (il
    #     «giu'» e il «su» partono a zero millisecondi l'uno dall'altro, e in
    #     mezzo la scena non ha ridisegnato) trova quello dell'occorrenza
    #     SUCCESSIVA dello stesso tasto — e il ritardo che ne esce e' il periodo
    #     di ripetizione, non il ritardo.  ⛔ 1 007 ms ≈ 840 ms di periodo: il
    #     numero diceva la mia cadenza, non il prodotto.
    #
    # ⇒ La finestra sta SOTTO il periodo di ripetizione: una sonda che non trova
    #   il suo eco **non chiude**, invece di chiudere sul fotogramma sbagliato.
    #   ⚠ E il denominatore lo dice: «27 su 584» era gia' un'accusa che nessuno
    #     aveva letto.
    """⛔ Le sonde della TASTIERA.  ⚠ Funzione PURA, come `accoppia()`.

    `mappa` va da `event.code` (il nome del browser) al codice **evdev** che
    esce sul filo, ed e' MISURATA (vedi `mappa_tasti`): ricopiare qui la
    tabella di `src/pagina.html` vorrebbe dire avere due verita' e credere
    alla nostra.
    """
    campioni = sorted(campioni, key=lambda c: c.get("t1") or 0)
    per_chiave = {}
    for e in eventi:
        cod = mappa.get(e.get("codice"))
        if cod is None:
            continue
        giu = 1 if e.get("tipo") == "keydown" else 0
        per_chiave.setdefault((cod, giu), []).append(e)
    for v in per_chiave.values():
        v.sort(key=lambda e: e["t_evento"])

    sonde, ultima_seq = [], None
    for s in spediti:
        if s.get("tipo") != RCP_POSIZIONE or s.get("id") is None:
            continue
        giu = 1 if s.get("premuto") else 0
        sonda = {"id": s["id"], "codice": s.get("codice"), "premuto": giu,
                 "t_filo": s["t_filo"], "istante_client_us": s.get("istante_us")}
        ev = None
        for e in per_chiave.get((s.get("codice"), giu), []):
            if e["t_evento"] <= s["t_filo"] and (ev is None
                                                 or e["t_evento"] > ev["t_evento"]):
                ev = e
        if ev is None:
            sonda["perche"] = ("⛔ nessun evento del browser con questo codice "
                               "prima della spedizione: NON ripiego sul "
                               "`t_filo`, sarebbe il confine comodo travestito")
            sonde.append(sonda)
            continue
        sonda["t_evento"] = ev["t_evento"]
        sonda["t_ascolto"] = ev["t_ascolto"]
        sonda["fidato"] = ev.get("fidato")
        for c in campioni:
            if (c.get("t1") or 0) < sonda["t_filo"]:
                continue
            if (c.get("t1") or 0) > sonda["t_filo"] + finestra_ms:
                break
            e = c.get("eco") or {}
            if (e.get("tipo") == ECO_TASTO and e.get("codice") == s.get("codice")
                    and bool(e.get("premuto")) == bool(giu)
                    and c.get("due_marche")
                    and _seq_avanti(e.get("seq"), ultima_seq)):
                sonda["scomodo"] = c
                ultima_seq = e.get("seq")
                break
        for c in campioni:
            if (c.get("t1") or 0) < sonda["t_filo"]:
                continue
            if (c.get("t1") or 0) > sonda["t_filo"] + finestra_ms:
                break
            if c.get("input") is not None and c["input"] >= s["id"]:
                sonda["comodo"] = c
                break
        for nome in ("scomodo", "comodo"):
            c = sonda.get(nome)
            if c is not None and c.get("t_dip") is not None:
                sonda["ritardo_%s_ms" % nome] = c["t_dip"] - sonda["t_evento"]
        # ⛔⛔ IL TERZO NUMERO, e non e' un terzo confine: e' il confine
        #     SBAGLIATO, consegnato apposta perche' si possa vedere quanto
        #     mente.  Chiude quando il richiamo del prodotto RITORNA — che
        #     sulla strada `bitmaprenderer` e' PRIMA che sia stato dipinto
        #     qualunque cosa (`LEZIONI.md` §1.20, §4-bis del prologo).
        #     ⚠ Non entra mai in `ritardo_scomodo_ms`, e Q11 lo usa per
        #       DIMOSTRARE che il confine vero non si chiude li'.
        cv = sonda.get("scomodo")
        if cv is not None and cv.get("t_dip_vecchio") is not None:
            sonda["ritardo_vecchio_ms"] = cv["t_dip_vecchio"] - sonda["t_evento"]
        sonde.append(sonda)
    return sonde


# ═══════════════════════════════════════════════════════════════════════════
# §5  LA SCOMPOSIZIONE — ⛔ mai un totale solo
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ «È solo grazie ai QUATTRO tratti separati che la fase 3 ha scoperto che il
#    collo di bottiglia si era spostato; con un totale solo si sarebbe letto
#    "−31 ms, vittoria", che e' falso.»  ⇒ Qui i tratti sono ONDICI, e ciascuno
#    dichiara **su quale orologio** e' preso: quelli che attraversano le due
#    macchine portano dentro l'errore dell'ancora, gli altri no.
TRATTI = [
    # (chiave, nome, orologio)
    ("1a", "evento → il prodotto lo vede (fase di cattura)", "pagina"),
    ("1b", "il prodotto lo vede → i byte escono (il gestore della pagina)", "pagina"),
    ("2", "byte usciti → la SCENA riceve l'input (filo d'andata + server + libei + compositore)", "ancora"),
    ("3", "⭐ la scena riceve → la scena DISEGNA (l'attesa del quadro)", "server"),
    ("4", "la scena disegna → cattura (`pts` di Mutter)", "server"),
    ("5", "cattura → PRIMO byte in pagina (codifica + filo di ritorno)", "ancora"),
    ("6", "primo byte → ULTIMO byte (lo stream sul filo)", "pagina"),
    ("7", "stream completo → richiamo di `decode()`", "pagina"),
    ("8", "`decode()` → richiamo del decodificatore (la decodifica)", "pagina"),
    # ⛔⛔ I DUE ULTIMI TRATTI HANNO DUE FACCE, UNA PER STRADA — §4-bis.
    #     La grandezza e' la stessa: «quanto si ASPETTA che il fotogramma sia
    #     utilizzabile» contro «quanto costa metterlo al vetro».  ⭐ Cambia
    #     l'evento che la marca, e cambia perche' e' cambiato il PRODOTTO:
    #       · strada 2D          9 = richiamo → 1° `drawImage`
    #                           10 = 1° → 2° `drawImage`
    #       · `bitmaprenderer`   9 = richiamo → `createImageBitmap` RISOLTA
    #                           10 = risolta → `transferFromImageBitmap` finito
    ("9", "⭐ richiamo → il FOTOGRAMMA E' PRONTO (⛔ l'ATTESA: 1° `drawImage` "
          "sulla 2D · `createImageBitmap` risolta su `bitmaprenderer`)", "pagina"),
    ("10", "⭐ pronto → IL DISEGNO E' FINITO (2° `drawImage` sulla 2D · "
           "`transferFromImageBitmap` su `bitmaprenderer`)", "pagina"),
]


def _d(v):
    return dist(v)


def scomponi(sonde, scarto_ancora_us=0):
    """⛔ Tutti i tratti si misurano SUL FOTOGRAMMA, non su medie di grandezze
    diverse: ogni riga e' una differenza fra due istanti dello STESSO cammino.

    ⛔⛔ `scarto_ancora_us` e' **quanto va SOTTRATTO all'orologio monotono del
        SERVER per portarlo su quello della pagina**, e lo da' l'ancora del
        ponte (`04-b30-ponte.py` §2).  ⚠ Il nome dice il verso apposta: due
        orologi monotoni di due macchine non hanno nessuna relazione, e una
        sottrazione fatta nel verso sbagliato produce un numero che **sembra**
        un ritardo — grande, stabile, e falso.

    ⭐ E i tratti che ne dipendono sono **due soli** (2 e 5): tutti gli altri
       stanno dentro un orologio solo, e sono immuni.  ⛔ Il totale pure: `t0` e
       `t1` sono tutt'e due `performance.now()` della stessa pagina.
    """
    buone = [s for s in sonde if s.get("scomodo") and s.get("t_evento") is not None]
    def p(f):
        return _d([f(s) for s in buone if f(s) is not None])

    def eco_us(s):
        m = s["scomodo"].get("eco_marca") or {}
        return m.get("istante_us")

    def dis_us(s):
        m = s["scomodo"].get("marca") or {}
        return m.get("istante_us") if m.get("c_e") else None

    fuori = {
        "1a": p(lambda s: s["t_ascolto"] - s["t_evento"]),
        "1b": p(lambda s: s["t_filo"] - s["t_ascolto"]),
        # ⛔ Il tratto 2 attraversa le due macchine: senza ancora e' un numero
        #    che SEMBRA un ritardo e non lo e' (`04-b30-ponte.py` §2).
        "2": p(lambda s: ((eco_us(s) - scarto_ancora_us) / 1000.0 - s["t_filo"])
               if eco_us(s) else None),
        "3": p(lambda s: (dis_us(s) - eco_us(s)) / 1000.0
               if (eco_us(s) and dis_us(s)) else None),
        "4": p(lambda s: (s["scomodo"]["pts"] - dis_us(s)) / 1000.0
               if (dis_us(s) and s["scomodo"].get("pts")) else None),
        "5": p(lambda s: (s["scomodo"]["t_primo"]
                          - (s["scomodo"]["pts"] - scarto_ancora_us) / 1000.0)
               if (s["scomodo"].get("t_primo") and s["scomodo"].get("pts")) else None),
        "6": p(lambda s: s["scomodo"]["t_ultimo"] - s["scomodo"]["t_primo"]
               if (s["scomodo"].get("t_ultimo") and s["scomodo"].get("t_primo")) else None),
        "7": p(lambda s: s["scomodo"]["t_dec"] - s["scomodo"]["t_ultimo"]
               if (s["scomodo"].get("t_dec") and s["scomodo"].get("t_ultimo")) else None),
        "8": p(lambda s: s["scomodo"]["t1"] - s["scomodo"]["t_dec"]
               if s["scomodo"].get("t_dec") else None),
        "9": p(lambda s: s["scomodo"]["t_dip_a"] - s["scomodo"]["t1"]
               if s["scomodo"].get("t_dip_a") else None),
        "10": p(lambda s: s["scomodo"]["t_dip"] - s["scomodo"]["t_dip_a"]
                if s["scomodo"].get("t_dip_a") else None),
    }
    r = {}
    for chiave, nome, orologio in TRATTI:
        r["%s %s" % (chiave, nome)] = dict(
            fuori[chiave],
            orologio=orologio,
            **({"⚠": "attraversa DUE macchine: porta dentro l'errore "
                     "dell'ancora, e lo scarto sottratto e' %.3f ms"
                     % (scarto_ancora_us / 1000.0)}
               if orologio == "ancora" else {}))
    r["T ⭐ TOTALE input → vetro (IL NUMERO, confine scomodo ai due capi)"] = dict(
        p(lambda s: s.get("ritardo_scomodo_ms")),
        orologio="pagina",
        **{"⭐": "⛔ NON porta dentro l'errore dell'ancora: `t0` e `t1` sono "
                "tutt'e due `performance.now()` della stessa pagina.  ⭐ E' un "
                "vantaggio che il numero della fase 3 NON aveva"})
    r["T-vecchio ⛔ il confine che si chiude al RITORNO DEL RICHIAMO "
      "(NON e' un numero: e' quanto MENTE)"] = dict(
        p(lambda s: s.get("ritardo_vecchio_ms")),
        orologio="pagina",
        **{"⛔": "sulla strada `bitmaprenderer` il richiamo del prodotto "
                "ritorna PRIMA che `createImageBitmap` abbia consegnato "
                "l'immagine: chiudere qui darebbe un numero piu' piccolo del "
                "vero con l'aria di funzionare (`LEZIONI.md` §1.20).  ⭐ Sulla "
                "strada 2D coincide col confine scomodo, e la differenza fra i "
                "due lo dice"})
    r["T-comodo  input → primo fotogramma con `input >= id` → vetro"] = dict(
        p(lambda s: s.get("ritardo_comodo_ms")),
        orologio="pagina",
        **{"⛔": "il confine COMODO: il fotogramma e' stato catturato dopo "
                "l'iniezione, ma sullo schermo puo' non essere ancora cambiato "
                "niente.  ⇒ si consegna per confronto, NON come numero"})
    r["Δ  quanto il confine comodo si REGALA"] = _d(
        [s["ritardo_scomodo_ms"] - s["ritardo_comodo_ms"] for s in buone
         if s.get("ritardo_comodo_ms") is not None
         and s.get("ritardo_scomodo_ms") is not None])
    r["C1 ⛔ [?] pezzo cieco in INGRESSO (mano → `event.timeStamp`)"] = {
        "stima_ms": [CIECO_INGRESSO_MIN_MS, CIECO_INGRESSO_MAX_MS], "marca": "[?]",
        "nota": "dispositivo + nucleo + compositore del CLIENT.  Nessuna API "
                "della pagina lo vede: `event.timeStamp` e' gia' il dopo"}
    r["C2 ⛔ [?] pezzo cieco in USCITA (disegno finito → pixel acceso)"] = {
        "stima_ms": [CIECO_USCITA_MIN_MS, CIECO_USCITA_MAX_MS], "marca": "[?]",
        "fonte": "STUDI.md §web §6.2",
        "nota": "⚠ su Xvfb non c'e' compositore: in QUESTO ambiente non esiste "
                "affatto.  La stima e' per lo schermo di un utente"}
    return r


# ═══════════════════════════════════════════════════════════════════════════
# §6  I CONTROLLI
# ═══════════════════════════════════════════════════════════════════════════
TUTTI = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10",
         "Q11"]


def q0_c_e_qualcosa_da_giudicare(v):
    """⛔⛔ IL CONTROLLO CHE FA USCIRE 3 E NON 0.

    Tre stati del mondo, tre frasi diverse, e **nessuno dei tre e' «conforme»**:
      a) il prodotto non ha spedito nessun messaggio di input riconoscibile;
      b) li ha spediti e la SCENA non ne ha ricevuto nessuno;
      c) la scena li ha ricevuti e nessuna coppia si e' chiusa nei pixel.

    ⚠ (b) e (c) sono la diagnosi che senza il conto della scena non esiste: da
      fuori hanno lo stesso aspetto, e mandano a cercare in due posti diversi
      (`libei` contro la codifica).  `LEZIONI.md` §1.9.
    """
    sp = [s for s in v.get("spediti", []) if s.get("tipo") in RCP_INPUT]
    scena = v.get("scena_input") or {}
    ricevuti = sum(scena.get(k) or 0 for k in
                   ("eventi_puntatore", "eventi_pulsante",
                    "eventi_rotella", "eventi_tasto"))
    sonde = [s for s in v.get("sonde", []) if s.get("scomodo")]
    d = {"messaggi_di_input_spediti": len(sp),
         "eventi_ricevuti_dalla_scena": ricevuti if scena else None,
         "sonde_chiuse": len(sonde), "sonde_tentate": len(v.get("sonde", []))}
    if not sp:
        return dict(d, esito=False, niente_da_giudicare=True,
                    perche="⛔ NON HO NIENTE DA GIUDICARE: sul filo non e' "
                           "uscito NESSUN messaggio di `RCP.md` §7.3 "
                           "(0x0101-0x0105).  ⚠ Non e' «l'anello e' lento» e "
                           "non e' «conforme»: il canale di input non c'e' "
                           "ancora.  ⛔ Il banco esce con %d"
                           % USCITA_NIENTE_DA_GIUDICARE)
    if scena and ricevuti == 0:
        return dict(d, esito=False, niente_da_giudicare=True,
                    perche="⛔ NON HO NIENTE DA GIUDICARE: %d messaggi di input "
                           "sono usciti sul filo e la SCENA non ne ha ricevuto "
                           "nemmeno uno.  ⇒ Il difetto sta fra il server e il "
                           "compositore (iniezione, `libei`, fuoco), non nella "
                           "catena video: un numero di ritardo qui sarebbe un "
                           "numero su niente" % len(sp))
    if not scena:
        return dict(d, esito=False, niente_da_giudicare=True,
                    perche="⛔ NON HO POTUTO GUARDARE: il blocco di stato della "
                           "scena non si e' letto, quindi «l'input non e' "
                           "arrivato al desktop» e «non ho guardato se ci sia "
                           "arrivato» hanno lo stesso aspetto (`LEZIONI.md` "
                           "§2.0).  ⛔ Non do nessun verdetto")
    if not sonde:
        return dict(d, esito=False, niente_da_giudicare=True,
                    perche="⛔ NON HO NIENTE DA GIUDICARE: %d input spediti, %d "
                           "ricevuti dalla scena, e **zero** coppie chiuse nei "
                           "pixel.  ⇒ L'input arriva al desktop e la sua "
                           "conseguenza non arriva al vetro: e' un difetto "
                           "della catena video o dell'eco, e in nessun caso un "
                           "ritardo da scrivere" % (len(sp), ricevuti))
    return dict(d, esito=True, niente_da_giudicare=False)


def q1_scena_sul_monitor_catturato(v):
    """⛔⛔ LA TRAPPOLA CHE HA GIA' MORSO DUE VOLTE — `LEZIONI.md` §1.1 e §1.1-bis.

    La scena deve stare **sul monitor che si sta catturando**.  Se non ci sta, il
    banco gira, non fallisce, e **misura il palco di qualcun altro**.

    ⛔ E la seconda volta la trappola ha morso **il risultato che la citava**: il
       banco `03-b14` aveva stampato `scena_sul_mio_monitor: false` accanto a
       ciascuna delle sue **due** celle, e una riga di `PIANO.md` le ha lette
       come una legge «che regge su 13 punti».

    ⇒ ⭐ Qui il banco **rifiuta da se'** le celle contaminate e **stampa il
      denominatore vero**.  «0 punti su 0» e' la cosa giusta da stampare.
    """
    chiesta = (v.get("scena") or {}).get("uscita_chiesta")
    confermata = (v.get("scena") or {}).get("uscita_confermata")
    catturato = v.get("monitor_catturato")
    tot = len(v.get("sonde", []))
    d = {"uscita_chiesta_dalla_scena": chiesta,
         "uscita_confermata_da_wl_surface_enter": confermata,
         "monitor_che_il_prodotto_cattura": catturato,
         "sonde_prima_del_filtro": tot}
    if not confermata or confermata.startswith("(nessun"):
        return dict(d, esito=False, punti=0, denominatore=0,
                    perche="⛔ NON HO POTUTO GUARDARE: nessun `wl_surface.enter` "
                           "e' arrivato, quindi non so su quale monitor sia la "
                           "scena.  ⚠ «Non lo so» NON e' «e' sul mio»: le celle "
                           "valgono **0 su 0**, ed e' il denominatore vero")
    if not catturato:
        return dict(d, esito=False, punti=0, denominatore=0,
                    perche="⛔ NON HO POTUTO GUARDARE: il prodotto non dichiara "
                           "quale monitor cattura.  ⇒ 0 punti su 0.  ⛔ La firma "
                           "che mi serve sta nel rapporto, §5")
    if confermata != catturato:
        return dict(d, esito=False, punti=0, denominatore=0,
                    scena_sul_mio_monitor=False,
                    perche="⛔ LA SCENA E' SUL MONITOR SBAGLIATO: sta su «%s» e "
                           "il prodotto cattura «%s».  ⇒ Tutte le %d sonde sono "
                           "CONTAMINATE e si buttano: **0 punti su 0**.  ⚠ Non "
                           "e' un numero brutto, e' un numero che non c'e'"
                           % (confermata, catturato, tot))
    return dict(d, esito=True, punti=tot, denominatore=tot,
                scena_sul_mio_monitor=True)


def q2_due_marche_stesso_fotogramma(campioni):
    """Le due marche si leggono tutt'e due, nello stesso `getImageData`."""
    guardati = [c for c in campioni if c.get("visto") and c.get("visto_eco")]
    due = [c for c in guardati if c.get("due_marche")]
    if not guardati:
        return {"esito": False, "guardati": 0,
                "perche": "⛔ nessun fotogramma con TUTT'E DUE le regioni lette: "
                          "non e' «le marche non c'erano», e' «non ho potuto "
                          "guardare»"}
    q = len(due) / len(guardati)
    return {"esito": q >= 0.70, "con_due_marche": len(due),
            "guardati": len(guardati), "quota": round(q, 4),
            "perche": None if q >= 0.70 else
                      "⛔ solo il %.1f%% dei fotogrammi porta TUTT'E DUE le "
                      "marche leggibili: l'eco sta in una regione che la "
                      "catena non consegna intatta" % (q * 100)}


def q3_eco_trova_quel_che_c_e(campioni):
    con = [c for c in campioni if c.get("visto_eco")]
    letti = [c for c in con if c.get("eco_marca", {}).get("c_e")]
    if not con:
        return {"esito": False,
                "perche": "⛔ nessun fotogramma con i pixel dell'eco letti: non "
                          "e' «l'eco non c'era», e' «non ho potuto guardare»"}
    motivi, ciechi = {}, 0
    for c in con:
        if c["eco_marca"].get("c_e"):
            continue
        p = c["eco_marca"].get("perche") or "(senza motivo)"
        if "CRC" in p:
            k = "il CRC non torna (marca a meta' fra due disegni)"
        elif "contrasto" in p:
            k = "contrasto sotto il minimo"
        elif "sync" in p:
            k = "il sync non c'e'"
        elif "GUARDARE" in p or "nessun pixel" in p:
            k = "⛔ NON HO POTUTO GUARDARE"
            ciechi += 1
        else:
            k = p[:60]
        motivi[k] = motivi.get(k, 0) + 1
    q = len(letti) / len(con)
    buono = q >= 0.80 and ciechi == 0
    return {"esito": buono, "letti": len(letti), "guardati": len(con),
            "quota": round(q, 4), "motivi_del_rifiuto": motivi, "ciechi": ciechi,
            "perche": None if buono else
                      ("⛔ %d fotogrammi «guardati» senza poter guardare" % ciechi
                       if ciechi else
                       "solo il %.1f%% dei fotogrammi porta un eco leggibile, e "
                       "la soglia e' 80 %%" % (q * 100))}


def q4_eco_non_trova_quel_che_non_c_e(campioni, senza_eco, sonde):
    """⛔ IL CONTROLLO CADUTO IN v1, E IL PIU' IMPORTANTE DI TUTTI.

    «Se dice sempre si', si sta misurando zero e si e' felici a torto» — ⛔ e un
    rilevatore che dice sempre si' **passa anche Q5 e Q6**, perche' gli N ms si
    sommano identici a qualunque numero inventato.

    Tre setacci, e servono tutti e tre:
      a) dove la marca dell'eco NON c'e', il lettore deve dire NO;
      b) l'eco letto deve **cambiare** al cambiare dell'input: un eco costante
         e' un rilevatore fermo, e un rilevatore fermo appaia il primo
         fotogramma che capita;
      c) ⭐ e le coordinate lette devono essere **quelle spedite**.  Un eco che
         dicesse sempre l'ultimo valore noto passerebbe (a) e (b) e cadrebbe
         qui — ed e' anche la misura di `RCP.md` §7.3, *«il server NON DEVE
         applicare nessuna trasformazione alle coordinate ricevute»*.
    """
    f = {}
    # (a)
    falsi = [c for c in senza_eco if c.get("eco_marca", {}).get("c_e")]
    f["a_falsi_positivi"] = len(falsi)
    f["a_guardati"] = len(senza_eco)
    f["a_esito"] = (len(senza_eco) > 0 and not falsi)
    if not senza_eco:
        f["a_perche"] = ("⛔ nessun fotogramma senza eco da mostrargli: Q4(a) "
                         "NON e' stato eseguito, ed e' esattamente il caso di v1")
    # (b)
    letti = [c["eco_marca"]["disegno"] for c in campioni
             if c.get("eco_marca", {}).get("c_e")]
    f["b_distinti"] = len(set(letti))
    f["b_letti"] = len(letti)
    f["b_esito"] = len(letti) > 20 and len(set(letti)) >= 5
    if not f["b_esito"]:
        f["b_perche"] = ("⛔ l'eco letto assume %d valori distinti su %d "
                         "fotogrammi: un eco che non cambia appaia il primo "
                         "fotogramma che capita, e il ritardo che ne esce e' "
                         "un numero sul nulla" % (len(set(letti)), len(letti)))
    # (c)
    giuste, storte, esempi = 0, 0, []
    for s in sonde:
        c = s.get("scomodo")
        if not c:
            continue
        e = c.get("eco") or {}
        if e.get("tipo") != ECO_PUNTATORE:
            continue
        if e.get("x") == s["x"] and e.get("y") == s["y"]:
            giuste += 1
        else:
            storte += 1
            if len(esempi) < 5:
                esempi.append({"spedito": [s["x"], s["y"]],
                               "arrivato": [e.get("x"), e.get("y")]})
    f["c_coordinate_giuste"] = giuste
    f["c_coordinate_storte"] = storte
    f["c_esempi"] = esempi
    f["c_esito"] = giuste > 0 and storte == 0
    if storte:
        f["c_perche"] = ("⛔ %d sonde su %d sono arrivate al desktop con "
                         "coordinate DIVERSE da quelle spedite.  ⚠ E' `RCP.md` "
                         "§7.3: «il server NON DEVE applicare nessuna "
                         "trasformazione alle coordinate ricevute»"
                         % (storte, giuste + storte))
    elif giuste == 0:
        f["c_perche"] = ("⛔ nessuna sonda con un eco di tipo PUNTATORE: Q4(c) "
                         "NON e' stato eseguito")
    f["esito"] = bool(f["a_esito"] and f["b_esito"] and f["c_esito"])
    return f


# ⛔ La tolleranza sta sulla GRANDEZZA VERA (`LEZIONI.md` §1.13): 4 ms e' la
#    somma dell'errore dell'ancora, dello scarto di consegna del ponte (~0,3 ms
#    misurato dalla sua certificazione) e di mezzo intervallo di quadro di
#    rumore sulla mediana.  ⚠ E' piu' larga dei 3 ms di `03-b17` per una
#    ragione dichiarata: l'anello di input attraversa **due** volte il filo.
TOLLERANZA_MS = 4.0


def _p1(giri, chiave, tratto_atteso, tolleranza_ms=TOLLERANZA_MS):
    """⛔ IL CONTROLLO DECISIVO, e in QUESTO banco ha una pretesa in piu'.

    Il ponte ritarda di N, e:
      1. la mediana del totale DEVE salire di esattamente N — come alla fase 3;
      2. ⭐⭐ e la salita DEVE comparire **nel tratto giusto** della
         scomposizione, e in nessun altro.

    ⛔ La 1 da sola la passa anche un metro che attribuisce il ritardo al tratto
       sbagliato — e un metro cosi' non diventa mai rosso, dice solo bugie sulla
       diagnosi.  E' `LEZIONI.md` §1.14 applicata alla scomposizione.
    """
    base = [g for g in giri if not g.get(chiave)]
    if not base:
        return {"esito": False, "perche": "⛔ manca il giro a ritardo 0 su «%s»: "
                                          "senza base non si puo' dire «e' "
                                          "salita»" % chiave}
    d0 = base[0].get("distribuzione") or {}
    if not d0.get("n"):
        return {"esito": False,
                "perche": "⛔ il giro a ritardo 0 non ha NESSUN campione: non e' "
                          "«la mediana non e' salita», e' «non ho misurato»"}
    m0 = d0["mediana"]
    s0 = base[0].get("scomposizione") or {}
    righe, buono = [], True
    for g in giri:
        n = g.get(chiave)
        if not n:
            continue
        d = g.get("distribuzione") or {}
        if not d.get("n"):
            righe.append({"n_ms": n, "salita_ms": None, "perche": "nessun campione"})
            buono = False
            continue
        salita = d["mediana"] - m0
        va = abs(salita - n) <= tolleranza_ms
        # ⭐ E DOVE E' ANDATO IL SURPLUS
        sn = g.get("scomposizione") or {}
        dove, altrove = None, []
        for k in s0:
            a, b = s0.get(k) or {}, sn.get(k) or {}
            if not isinstance(a, dict) or "mediana" not in a:
                continue
            if "mediana" not in b:
                continue
            salto = b["mediana"] - a["mediana"]
            # ⛔ I totali, il regalo e i pezzi ciechi si SALTANO: il totale DEVE
            #    salire (e' la pretesa 1) e il regalo non e' un tratto della
            #    catena.  Contarli come «e' salito anche altrove» renderebbe
            #    questo controllo rosso per costruzione.
            if k[0] in "TΔC":
                continue
            if abs(salto - n) <= tolleranza_ms and k.startswith(tratto_atteso):
                dove = {"tratto": k, "salto_ms": round(salto, 3)}
            elif abs(salto) > tolleranza_ms:
                altrove.append({"tratto": k, "salto_ms": round(salto, 3)})
        nel_posto_giusto = dove is not None and not altrove
        buono = buono and va and nel_posto_giusto
        righe.append({"n_ms": n, "salita_ms": round(salita, 2),
                      "scarto_ms": round(salita - n, 2),
                      "salita_totale_ok": va,
                      "il_surplus_sta_in": dove,
                      "e_anche_altrove": altrove,
                      "nel_tratto_giusto": nel_posto_giusto,
                      "campioni": d["n"]})
    if not righe:
        return {"esito": False,
                "perche": "⛔ nessun giro con ritardo iniettato su «%s»: il "
                          "controllo NON e' stato eseguito.  ⚠ Non e' "
                          "«passato»: e' «non fatto», ed e' il caso in cui il "
                          "banco non sa di misurare" % chiave}
    return {"esito": buono, "mediana_base_ms": m0, "tratto_atteso": tratto_atteso,
            "righe": righe, "tolleranza_ms": tolleranza_ms}


def q5_ritardo_noto_ritorno(giri):
    """P1-RITORNO: il ritardo va messo nel tratto 5 (cattura → primo byte)."""
    return _p1(giri, "ritardo_ritorno_ms", "5 ")


def q6_ritardo_noto_andata(giri):
    """⭐⭐ P1-ANDATA — il controllo che alla fase 3 NON POTEVA ESISTERE.

    Il ritardo va messo nel tratto 2 (byte usciti → la scena riceve l'input).
    ⛔ Senza di lui il ramo d'andata dell'anello resta senza taratura per
       sempre: un metro che sbagliasse li' — accoppiando l'input al fotogramma
       sbagliato, o prendendo `t0` dopo la partenza dei byte — resterebbe verde
       per costruzione (`LEZIONI.md` §1.14).
    """
    return _p1(giri, "ritardo_andata_ms", "2 ")


def q11_il_confine_non_si_chiude_prima_del_disegno(giri):
    """⭐⭐⭐ IL CONTROLLO POSITIVO CHE VALE PIU' DI TUTTI — fase 8, punto F1.2.

    ⛔⛔ LA TESI DA REFUTARE: *«il banco adesso legge la strada `bitmaprenderer`
        e da' un numero plausibile, quindi funziona»*.  **Non basta, ed e' il
        genere di verde che costa piu' caro di un rosso.**

    Su quella strada il disegno e' ASINCRONO: fra «il richiamo del prodotto e'
    ritornato» e «il fotogramma e' sullo schermo» ci sono la risoluzione di
    `createImageBitmap` e il trasferimento.  ⇒ Un banco che chiudesse al
    ritorno del richiamo darebbe un numero **piu' piccolo del vero** e avrebbe
    l'aria di funzionare (`LEZIONI.md` §1.20).

    ⇒ ⭐ LA PROVA: si innesta un ritardo NOTO di N ms **fra il fotogramma
      pronto e il vetro** (`B.ritardo_vetro_ms`, §4-bis del prologo), e si
      pretendono TRE cose insieme:

        1. ⭐⭐⭐ **la DISTANZA fra il confine vero e quello sbagliato — presa
           sulla STESSA sonda — sale di esattamente N.**  E' la pretesa
           decisiva, e appaiata apposta;
        2. ⭐ la salita compare **nel tratto 10** e in nessun altro — cioe' il
           banco sa DOVE l'ha messa, non solo che c'e';
        3. il totale sale di **ALMENO N**.  ⛔ «Almeno» e non «esattamente», e
           la ragione e' `[M]`, non una comodita': vedi qui sotto.

    ⛔⛔ PERCHE' LA PRETESA 1 E' APPAIATA, E PERCHE' LA 3 DICE «ALMENO».

    Il ritardo si innesta occupando il filo della pagina — che e' quel che fa
    un disegno davvero costoso.  ⇒ Quel tempo non ritarda solo IL FOTOGRAMMA:
    ritarda anche la consegna degli eventi di input, che stanno sullo stesso
    filo.  `[M]` 22 agosto 2026, 8 ms innestati: il totale e' salito di **14,81
    ms**, e di quei 14,81 **7,995 stanno nel tratto 10** (dove devono) e il
    resto e' lo spostamento di tutto il condotto — che si vede anche sul
    confine vecchio, salito di **6,82**.

    ⇒ ⭐⭐ Su una mediana sola quello spostamento e' indistinguibile dal
      ritardo innestato.  **Sulla differenza appaiata no**: i due confini
      stanno sullo stesso fotogramma e lo spostamento li colpisce identici,
      quindi si elide.  `[M]` la distanza e' passata da **0,090 ms** (base) a
      **8,075** (8 innestati), col **minimo a 8,035 su 545 sonde su 545** —
      cioe' non c'e' una sola sonda che non lo veda.

    ⛔ E pretendere «il totale sale di ESATTAMENTE N» renderebbe questo
       controllo rosso per un fatto fisico vero, che e' il modo piu' rapido di
       insegnare a chi legge che i rossi si ignorano.

    ⛔ E se il giro col ritardo non c'e', il controllo dice **NON ESEGUITO**,
       che non e' «passato».
    """
    r = _p1(giri, "ritardo_vetro_ms", "10 ")
    base = next((g for g in giri if not g.get("ritardo_vetro_ms")), None)
    d0 = (base or {}).get("distanza_fra_i_confini") or {}
    v0 = (base or {}).get("distribuzione_vecchio") or {}
    righe, distanza_ok = [], True
    for g in giri:
        n = g.get("ritardo_vetro_ms")
        if not n:
            continue
        dn = g.get("distanza_fra_i_confini") or {}
        vn = g.get("distribuzione_vecchio") or {}
        if not (d0.get("n") and dn.get("n")):
            righe.append({"n_ms": n, "salita_della_distanza_ms": None,
                          "perche": "⛔ NON ESEGUITO: non ho le due misure "
                                    "sulla stessa sonda, quindi non posso dire "
                                    "che il confine stia dopo il disegno"})
            distanza_ok = False
            continue
        salita = dn["mediana"] - d0["mediana"]
        buona = abs(salita - n) <= TOLLERANZA_MS
        distanza_ok = distanza_ok and buona
        righe.append({"n_ms": n,
                      "distanza_base_ms": d0["mediana"],
                      "distanza_col_ritardo_ms": dn["mediana"],
                      "salita_della_distanza_ms": round(salita, 3),
                      "scarto_ms": round(salita - n, 3),
                      # ⛔ Il MINIMO, non solo la mediana: se una sola sonda
                      #    non vedesse il ritardo, li' il confine si chiude nel
                      #    posto sbagliato — e una mediana non lo direbbe.
                      "minimo_ms": dn.get("min"),
                      "sonde": dn["n"],
                      "e_dopo_il_disegno": buona,
                      # ⚠ dichiarato accanto, e NON e' un rosso: e' lo
                      #   spostamento di tutto il condotto (vedi la docstring)
                      "⚠ e il confine vecchio intanto sale di":
                          round(vn["mediana"] - v0["mediana"], 2)
                          if (vn.get("n") and v0.get("n")) else None})
    r["⭐⭐⭐ la DISTANZA fra i due confini sale del ritardo innestato"] = {
        "esito": distanza_ok, "righe": righe,
        "⭐": "⛔ QUESTA e' la prova che il confine non si chiude prima del "
             "disegno, ed e' APPAIATA: se il banco chiudesse al ritorno del "
             "richiamo, la distanza resterebbe quella di sempre qualunque "
             "ritardo si innesti"}
    righe_p1 = r.get("righe") or []
    nel_posto = bool(righe_p1) and all(x.get("nel_tratto_giusto")
                                       for x in righe_p1)
    almeno = bool(righe_p1) and all(
        x.get("salita_ms") is not None
        and x["salita_ms"] >= x["n_ms"] - TOLLERANZA_MS for x in righe_p1)
    r["il_totale_sale_di_ALMENO_N"] = almeno
    r["la_salita_sta_nel_tratto_10_e_in_nessun_altro"] = nel_posto
    r["⚠ il totale puo' salire di PIU' di N"] = (
        "e non e' un rosso: il ritardo si innesta occupando il filo della "
        "pagina, e quel tempo ritarda anche la consegna degli eventi di input. "
        "⇒ Si pretende «almeno N» sul totale, «esattamente N» sulla distanza "
        "appaiata e sul tratto 10")
    r["esito"] = bool(distanza_ok and nel_posto and almeno)
    return r


def q7_due_confini(sonde):
    """⛔ I DUE CONFINI SI DICHIARANO TUTT'E DUE, e il consegnato e' lo SCOMODO."""
    a = [s["ritardo_scomodo_ms"] for s in sonde if s.get("ritardo_scomodo_ms") is not None]
    b = [s["ritardo_comodo_ms"] for s in sonde if s.get("ritardo_comodo_ms") is not None]
    tutt_e_due = [(s["ritardo_scomodo_ms"], s["ritardo_comodo_ms"]) for s in sonde
                  if s.get("ritardo_scomodo_ms") is not None
                  and s.get("ritardo_comodo_ms") is not None]
    d = {"scomodo": _d(a), "comodo": _d(b), "sonde_con_tutt_e_due": len(tutt_e_due)}
    if not tutt_e_due:
        return dict(d, esito=False,
                    perche="⛔ NON ESEGUITO: nessuna sonda ha chiuso su tutt'e "
                           "due i confini.  ⚠ Senza il confronto non si puo' "
                           "dire quanto il confine comodo si regala, e il "
                           "numero resta senza il suo controllo")
    uguali = sum(1 for x, y in tutt_e_due if abs(x - y) < 1e-9)
    q = uguali / len(tutt_e_due)
    piu_corto = sum(1 for x, y in tutt_e_due if x < y - 1e-9)
    # ⛔ Lo scomodo NON puo' essere piu' corto del comodo: il fotogramma in cui
    #    si VEDE la conseguenza non puo' arrivare prima di quello in cui il
    #    campo `input` la annuncia.  Se succede, il metro sta accoppiando male.
    buono = piu_corto == 0 and q < 0.95
    return dict(d, esito=buono, uguali=uguali, quota_uguali=round(q, 4),
                scomodo_piu_corto=piu_corto,
                regalo_ms=_d([x - y for x, y in tutt_e_due]),
                perche=None if buono else
                       ("⛔ %d sonde hanno il confine SCOMODO piu' corto del "
                        "COMODO: impossibile, e vuol dire che l'accoppiamento "
                        "e' sbagliato" % piu_corto if piu_corto else
                        "⛔ il %.1f%% delle sonde da' lo STESSO fotogramma sui "
                        "due confini: l'eco non sta discriminando, ed e' un "
                        "rilevatore che dice sempre si'" % (q * 100)))


def q8_il_disegno_non_e_il_disegno(sonde):
    """⭐ LA TESI 3, FATTA CONTROLLO.  ⛔ Questo controllo NON giudica: DICHIARA.

    Vedi il riquadro in testa al file.  Il tratto che la fase 3 chiama «il
    disegno» e' `richiamo del decodificatore → disegno finito`, e sul cammino a
    decodifica hardware contiene **l'attesa che il fotogramma sia utilizzabile**.

    ⇒ La prova falsificabile: se il tratto e' l'attesa, il **1°** `drawImage` e'
      grande e il **2°** e' piccolo; se e' davvero il disegno, sono simili.

    ⛔ Il controllo pretende che i due numeri **ci siano**.  Non decide quale
       delle due sia vera: quello lo dicono i numeri, e su questo palco non ci
       sono ancora.
    """
    con = [s["scomodo"] for s in sonde if s.get("scomodo")]
    a = _d([c["t_dip_a"] - c["t1"] for c in con if c.get("t_dip_a")])
    b = _d([c["t_dip"] - c["t_dip_a"] for c in con if c.get("t_dip_a")])
    quanti = _d([len(c.get("disegni_ms") or []) for c in con])
    d = {"9_richiamo_al_primo_drawImage_ms": a,
         "10_dal_primo_al_secondo_drawImage_ms": b,
         "quanti_drawImage_per_fotogramma": quanti,
         "⛔ che cosa dice": None}
    if not a.get("n") or not b.get("n"):
        return dict(d, esito=False,
                    perche="⛔ NON ESEGUITO: non ho i due `drawImage` separati. "
                           "⚠ Senza, il tratto resta quello della fase 3 — un "
                           "numero vero con **un'etichetta falsa**, e "
                           "l'etichetta e' quella che finisce nei documenti")
    ma, mb = a["mediana"], b["mediana"]
    if mb > 0 and ma / max(mb, 1e-6) >= 3.0:
        d["⛔ che cosa dice"] = (
            "⛔ il 1° `drawImage` costa %.2f ms e il 2° %.2f: **%.1f volte**.  "
            "⇒ Il tratto NON e' il disegno, e' l'ATTESA che il fotogramma sia "
            "utilizzabile.  La riga «il collo di bottiglia e' il disegno» va "
            "riscritta" % (ma, mb, ma / mb))
    else:
        d["⛔ che cosa dice"] = (
            "⚠ il 1° `drawImage` costa %.2f ms e il 2° %.2f: sono confrontabili. "
            "⇒ Su QUESTO palco il tratto e' davvero il disegno, e la riga della "
            "fase 3 regge.  ⛔ Il palco si dichiara accanto, o il confronto con "
            "l'altro giro non vale" % (ma, mb))
    return dict(d, esito=True)


def q9_costo_del_banco(costo_us, senza_lettura, con_lettura):
    """⛔ Quel che il banco AGGIUNGE si misura, o e' un errore sistematico."""
    d = _d([x * 0.001 for x in costo_us])
    f = {"lettura_pixel_ms": d,
         "⚠": "qui si leggono DUE regioni per fotogramma (la marca e l'eco), "
              "non una: il costo e' ~doppio di quello di `03-b17` ed e' voluto"}
    if senza_lettura and con_lettura:
        f["fps_senza_lettura"] = senza_lettura
        f["fps_con_lettura"] = con_lettura
        cala = (senza_lettura - con_lettura) / senza_lettura if senza_lettura else 1
        f["calo_di_ritmo"] = round(cala, 4)
        f["esito"] = cala < 0.10
        if not f["esito"]:
            f["perche"] = ("⛔ la lettura dei pixel toglie il %.1f%% del ritmo: "
                           "il banco si sta misurando addosso" % (cala * 100))
    else:
        f["esito"] = d.get("n", 0) > 0 and d.get("p95", 99) < 5.0
        f["perche"] = ("⚠ il confronto con/senza lettura non e' stato fatto: si "
                       "dichiara il solo costo della lettura")
    return f


def q10_grana(grana, isolata):
    """La grana del cronometro della pagina.  ⛔ Si MISURA, non si deduce."""
    if not grana:
        return {"esito": False, "perche": "⛔ la grana non e' stata misurata: "
                                          "non ho potuto guardare"}
    m = grana.get("minimo_ms")
    d = {"salti": grana.get("salti"), "minimo_ms": m,
         "mediano_ms": grana.get("mediano_ms"), "isolata": isolata}
    if m is None:
        return dict(d, esito=False, perche="⛔ nessun salto misurato")
    buono = bool(isolata) and m < 0.5
    return dict(d, esito=buono,
                perche=None if buono else
                       "⛔ la pagina non e' isolata (COOP+COEP) o la grana e' "
                       "%.3f ms: su un tetto di 50 ms una griglia da 1 ms e' "
                       "il 2 %% di errore su ogni campione" % m)


def giudica(v):
    """Tutti i controlli, su un verbale.  ⛔ Funzione PURA."""
    giri = v.get("giri", [])
    base = next((g for g in giri if not g.get("ritardo_ritorno_ms")
                 and not g.get("ritardo_andata_ms")
                 and not g.get("ritardo_vetro_ms")), None) or (giri[0] if giri else {})
    campioni = base.get("campioni", [])
    sonde = base.get("sonde", [])
    v2 = dict(v, sonde=sonde, spediti=base.get("spediti", []))
    return {
        "Q0": q0_c_e_qualcosa_da_giudicare(v2),
        "Q1": q1_scena_sul_monitor_catturato(v2),
        "Q2": q2_due_marche_stesso_fotogramma(campioni),
        "Q3": q3_eco_trova_quel_che_c_e(campioni),
        "Q4": q4_eco_non_trova_quel_che_non_c_e(
            campioni, v.get("senza_eco", []), sonde),
        "Q5": q5_ritardo_noto_ritorno(giri),
        "Q6": q6_ritardo_noto_andata(giri),
        "Q7": q7_due_confini(sonde),
        "Q8": q8_il_disegno_non_e_il_disegno(sonde),
        "Q9": q9_costo_del_banco(v.get("costo_lettura_us", []),
                                 v.get("fps_senza_lettura"),
                                 v.get("fps_con_lettura")),
        "Q10": q10_grana(v.get("grana"), v.get("isolata")),
        "Q11": q11_il_confine_non_si_chiude_prima_del_disegno(giri),
    }


# ═══════════════════════════════════════════════════════════════════════════
# §7  IL VERDETTO
# ═══════════════════════════════════════════════════════════════════════════
def verdetto(d, su_xvfb=True):
    """⛔ Contro 50 e contro 40, coi DUE pezzi ciechi accanto."""
    if not d or not d.get("n"):
        return {"esito": "NON MISURATO",
                "perche": "⛔ nessuna sonda chiusa: non e' «passa», e' «non so»"}
    med, p95 = d["mediana"], d["p95"]
    return {
        "mediana_ms": med, "p95_ms": p95, "p99_ms": d["p99"], "max_ms": d["max"],
        "n": d["n"],
        "contro_50": "PASSA" if med <= 50 else "SFORA",
        "contro_50_al_p95": "PASSA" if p95 <= 50 else "SFORA",
        "contro_40": "PASSA" if med <= 40 else "SFORA",
        "contro_40_al_p95": "PASSA" if p95 <= 40 else "SFORA",
        "letto_coi_pezzi_ciechi": con_pezzi_ciechi(med, su_xvfb),
        "⛔": "i pezzi ciechi NON sono compresi nei numeri qui sopra: "
              "`SPECIFICHE.md` §3.2 misura «solo il pezzo che e' nostro», e ne "
              "il dispositivo del client ne il compositore del server lo sono. "
              "Si DICHIARANO, non si promettono",
    }


# ═══════════════════════════════════════════════════════════════════════════
# §8  LA CERTIFICAZIONE — ⭐ sano → guasto → RISANATO, e a tre giri
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `LEZIONI.md` §1.2: il banco si certifica PRIMA della misura.  E a TRE giri,
#    non a due: un controllo che diventa rosso col guasto ma non torna verde
#    quando lo si toglie sta bocciando qualcos'altro.
#
# ⛔⛔ E IL FINTO DEVE SAPER PRODURRE IL RISULTATO ATTESO — `CODER.md` §3.3.
#     «Certificalo con un FINTO che sappia produrre il risultato atteso, cosi'
#     quando il prodotto arriva un rosso significa il prodotto e non lo
#     strumento.»
def _finta_marca(disegno, istante_us, giro):
    """Una lettura di marca della forma vera, come la darebbe `03-marca.py`."""
    return {"c_e": True, "disegno": disegno, "istante_us": istante_us,
            "giro": giro, "contrasto": 0.9}


# ⛔⛔ I TRATTI DEL FINTO, CON UN NOME E UNA PROVENIENZA.
#
#    ⚠ Non sono numeri a sentimento: dove esistono, sono i numeri VERI misurati
#    dalla fase 3 (`banchi/03-b17-esiti.jsonl`, giro `E3-deposito-hw-5punti`,
#    n=379).  Dove non esistono — i tratti del ramo d'andata, che nessuno ha
#    ancora misurato — sono `[?]` **dichiarati tali**, e servono solo a dare al
#    finto la FORMA giusta.
#
# ⛔⛔ E LA REGOLA CHE LI GOVERNA: **nessuno di questi numeri esce da questo
#     file.**  Un numero del finto copiato in un documento con la marca `[M]`
#     sarebbe il difetto peggiore che questo banco possa produrre — la quarta
#     veste di `LEZIONI.md` §1.9: un numero verosimile non attiva nessun
#     sospetto.  ⇒ `--finto` lo stampa con l'avvertimento addosso.
FINTO = {
    "1a": 0.35,    # [?] la fase di cattura
    "1b": 1.10,    # [?] il gestore della pagina
    "2":  6.00,    # [?] filo d'andata + server + libei + compositore
    "3":  8.35,    # [?] mezzo intervallo di quadro, in media (60 Hz)
    "4":  16.60,   # [M] fase 3, tratto «disegno → cattura»: 16,604
    "5":  31.78,   # [M] fase 3, tratto «cattura → primo byte»: 31,784
    "6":  0.19,    # [M] fase 3: 0,190
    "7":  0.08,    # [M] fase 3: 0,080
    "8":  0.73,    # [M] fase 3, la decodifica: 0,730
    "9":  26.50,   # [?] la parte del 27,995 della fase 3 che e' ATTESA
    "10": 1.50,    # [?] e la parte che e' DISEGNO — vedi il riquadro in testa
    # ⛔⛔ E QUESTO NON E' UN TRATTO: e' quanto il richiamo del prodotto ci mette
    #     a RITORNARE.  Sulla strada `bitmaprenderer` ritorna subito — chiama
    #     `createImageBitmap` e se ne va — cioe' PRIMA che i 26,50 + 1,50 siano
    #     passati.  ⇒ Nel finto vale 0,30 ms, ed e' il confine SBAGLIATO che Q11
    #     deve dimostrare cieco (§4-bis).
    "9v": 0.30,
}
FINTO_RITORNO_DEL_RICHIAMO = "9v"
# ⛔ `9v` NON e' un tratto della catena e non entra nel totale: sommarlo
#    darebbe un totale atteso sbagliato di 0,30 ms, e il controllo B del finto
#    diventerebbe rosso per un motivo che non c'entra niente.
FINTO_TOTALE = sum(x for k, x in FINTO.items()
                   if k != FINTO_RITORNO_DEL_RICHIAMO)


def verbale_sintetico(seme=7, quanti=240, ritardi_ritorno=(25,),
                      ritardi_andata=(30,), ritardi_vetro=(20,), passo_ms=16.7):
    """⭐ IL FINTO: un verbale della forma vera, con l'anello che si chiude.

    ⛔ `CODER.md` §3.3: *«certificalo con un FINTO che sappia produrre il
       risultato atteso, cosi' quando il prodotto arriva un rosso significa il
       prodotto e non lo strumento»*.

    ⭐ E la cosa che lo rende un finto ONESTO e non una comodita': i due confini
       cadono su **due fotogrammi diversi**, come nel mondo vero.  Il campo
       `input` dei 28 byte di un fotogramma vale l'id dell'ultimo input
       iniettato **prima della cattura** (`RCP.md` §6.2) — e fra l'iniezione e
       il ridisegno della scena passa un quadro.  ⇒ Il fotogramma che *annuncia*
       l'input arriva **prima** di quello che ne *mostra* la conseguenza, ed e'
       esattamente quel che il confine comodo si regala.
    """
    rnd = random.Random(seme)
    giro_n = marca_modulo().fnv1a32("b30-finto")
    giro_e = marca_modulo().fnv1a32("b30-finto-eco")
    # ⛔ Lo scarto fra i due orologi.  Un numero grande e tondo apposta: se un
    #    giorno qualcuno dimenticasse di sottrarlo, i tratti 2 e 5 uscirebbero
    #    dell'ordine dei minuti e il difetto si vedrebbe subito — invece di
    #    nascondersi dentro un millisecondo.
    scarto_us = 500_000_000

    def fai_giro(rit_ritorno=0.0, rit_andata=0.0, rit_vetro=0.0):
        campioni, spediti, eventi = [], [], []
        disegno, id_input = 5000, 100
        for i in range(quanti):
            disegno += 1
            id_input += 1
            # ⛔ Coordinate DISTINTE a ogni sonda: due sonde con le stesse
            #    coordinate darebbero lo stesso eco, e l'accoppiamento
            #    sceglierebbe il primo fotogramma buono — cioe' un numero piu'
            #    corto del vero, ottenuto senza sbagliare nessun conto.
            x, y = 300 + i, 400 + (i % 7)
            # ── il cammino, tratto per tratto, coi nomi di `TRATTI` ────────
            t_evento = 1000.0 + i * passo_ms + rnd.gauss(0, 0.4)
            t_ascolto = t_evento + FINTO["1a"]
            t_filo = t_ascolto + FINTO["1b"]
            eco_us = scarto_us + int((t_filo + FINTO["2"] + rit_andata) * 1000)
            dis_us = eco_us + int(FINTO["3"] * 1000)
            pts = dis_us + int(FINTO["4"] * 1000)
            t_primo = (pts - scarto_us) / 1000.0 + FINTO["5"] + rit_ritorno
            t_ultimo = t_primo + FINTO["6"]
            t_dec = t_ultimo + FINTO["7"]
            t1 = t_dec + FINTO["8"]
            t_dip_a = t1 + FINTO["9"]
            # ⭐⭐ IL RITARDO INNESTATO AL VETRO sta QUI e in nessun altro
            #     posto: fra «il fotogramma e' pronto» e «il fotogramma e' sullo
            #     schermo».  ⇒ Il totale sale di N, il tratto 10 sale di N, e
            #     `t_dip_vecchio` NON si muove — che e' la forma esatta di quel
            #     che Q11 pretende dal mondo vero.
            t_dip = t_dip_a + FINTO["10"] + rit_vetro
            # ⛔ Il richiamo del prodotto ritorna SUBITO: `createImageBitmap` e'
            #    asincrona, e li' non e' stato dipinto niente.
            t_dip_vecchio = t1 + FINTO[FINTO_RITORNO_DEL_RICHIAMO]
            eco = eco_puntatore(x, y)
            campioni.append({
                "t1": t1, "t_dip": t_dip, "t_dip_a": t_dip_a, "t_let": t_dip + 0.9,
                "t_dip_vecchio": t_dip_vecchio, "strada": "bitmaprenderer",
                "pts": pts, "numero": i + 1,
                "tipo": 0x0301 if i == 0 else 0x0302,
                "byte": 4000 + rnd.randint(0, 2000),
                # ⭐⭐ E QUESTA E' LA RIGA CHE RENDE ONESTO IL FINTO.
                #     Il fotogramma che MOSTRA l'eco dell'input `k` e' stato
                #     catturato quando l'input `k+1` era gia' stato iniettato:
                #     `RCP.md` §6.2 dice «l'ultimo input iniettato PRIMA della
                #     cattura».  ⇒ Il confine comodo trova il fotogramma
                #     PRECEDENTE, e i due numeri non coincidono.
                "input": id_input + 1,
                "t_primo": t_primo, "t_ultimo": t_ultimo, "t_dec": t_dec,
                "disegni_ms": [FINTO["9"], FINTO["10"]],
                "marca": _finta_marca(disegno, dis_us, giro_n),
                "eco_marca": _finta_marca(eco, eco_us, giro_e),
                "eco": eco_scomponi(eco),
                "due_marche": True, "visto": True, "visto_eco": True,
                "celle": [0.0, 255.0] * 72, "celle_eco": [0.0, 255.0] * 72,
            })
            eventi.append({"tipo": "pointermove", "t_evento": t_evento,
                           "t_ascolto": t_ascolto, "fidato": True, "x": x, "y": y})
            spediti.append({"tipo": RCP_PUNTATORE, "nome": "PUNTATORE",
                            "lunghezza": 20, "id": id_input,
                            "istante_us": int(t_evento * 1000),
                            "x": x, "y": y, "t_filo": t_filo})
        sonde = accoppia(campioni, spediti, eventi)
        buone = [s for s in sonde if s.get("scomodo")]
        return {"campioni": campioni, "spediti": spediti, "eventi": eventi,
                "sonde": sonde,
                "ritardo_ritorno_ms": rit_ritorno,
                "ritardo_andata_ms": rit_andata,
                "ritardo_vetro_ms": rit_vetro,
                "distribuzione": _d([s["ritardo_scomodo_ms"] for s in buone]),
                "distribuzione_vecchio": _d(
                    [s["ritardo_vecchio_ms"] for s in buone
                     if s.get("ritardo_vecchio_ms") is not None]),
                "distanza_fra_i_confini": _d(
                    [s["ritardo_scomodo_ms"] - s["ritardo_vecchio_ms"]
                     for s in buone if s.get("ritardo_vecchio_ms") is not None]),
                "scomposizione": scomponi(sonde, scarto_us)}

    giri = [fai_giro(0.0, 0.0, 0.0)]
    for n in ritardi_ritorno:
        giri.append(fai_giro(float(n), 0.0, 0.0))
    for n in ritardi_andata:
        giri.append(fai_giro(0.0, float(n), 0.0))
    for n in ritardi_vetro:
        giri.append(fai_giro(0.0, 0.0, float(n)))
    senza = [{"celle_eco": [rnd.random() * 255.0 for _ in range(144)],
              "visto_eco": True,
              "eco_marca": {"c_e": False, "perche": "rumore"}} for _ in range(120)]
    return {
        "giri": giri, "senza_eco": senza,
        "scarto_ancora_us": scarto_us,
        "⛔ IL FINTO": "questi numeri NON sono una misura: sono la FORMA della "
                      "misura.  Nessuna riga di qui va in un documento con la "
                      "marca [M]",
        "grana": {"salti": 4000, "minimo_ms": 0.005, "mediano_ms": 0.02},
        "isolata": True,
        "scena": {"uscita_chiesta": "META-0", "uscita_confermata": "META-0"},
        "monitor_catturato": "META-0",
        "scena_input": {"eventi_puntatore": quanti, "eventi_pulsante": 0,
                        "eventi_rotella": 0, "eventi_tasto": 0,
                        "seat_visto": 1, "seat_puntatore": 1, "seat_tastiera": 1},
        "costo_lettura_us": [rnd.gauss(1200, 200) for _ in range(500)],
        "fps_senza_lettura": 59.8, "fps_con_lettura": 58.9,
    }


# ── I GUASTI: ciascuno rompe UNA cosa, e dichiara CHI deve accorgersene ─────
def _g_niente_input(v):
    """⛔ Il canale di input non c'e' ancora: nessun messaggio §7.3 sul filo."""
    for g in v["giri"]:
        g["spediti"] = []
        g["sonde"] = []
    return v


def _g_input_non_arriva_al_desktop(v):
    """⛔ I byte escono e la SCENA non riceve niente: il difetto sta fra il
    server e il compositore, non nella catena video."""
    v["scena_input"] = dict(v["scena_input"], eventi_puntatore=0)
    for g in v["giri"]:
        g["sonde"] = [dict(s, scomodo=None, comodo=None) for s in g["sonde"]]
    return v


def _g_scena_senza_conto(v):
    """⛔ Il blocco della scena non si legge: «non arrivato» e «non guardato»
    devono restare due frasi diverse."""
    v["scena_input"] = None
    return v


def _g_scena_sul_monitor_sbagliato(v):
    """⛔⛔ LA TRAPPOLA DI `LEZIONI.md` §1.1-bis: la scena e' su un altro
    monitor.  Il banco deve rifiutare da se' TUTTE le celle e stampare 0 su 0."""
    v["scena"] = dict(v["scena"], uscita_confermata="META-1")
    return v


def _g_nessun_enter(v):
    """⛔ Nessun `wl_surface.enter`: «non lo so» non e' «e' sul mio»."""
    v["scena"] = dict(v["scena"], uscita_confermata="(nessun enter ricevuto)")
    return v


def _g_eco_illeggibile(v):
    for g in v["giri"]:
        for c in g["campioni"]:
            c["eco_marca"] = {"c_e": False, "perche": "contrasto sotto il minimo"}
            c["due_marche"] = False
    return v


def _g_eco_dice_sempre_si(v):
    """⛔⛔ IL GUASTO DI v1: il rilevatore dell'eco dice sempre «l'ho visto».
    ⚠ E si noti che Q5 e Q6 restano VERDI: gli N ms si sommano identici."""
    for c in v["senza_eco"]:
        c["eco_marca"] = _finta_marca(1, 0, 0)
    return v


def _g_eco_fermo(v):
    """⛔ L'eco non cambia mai: appaia il primo fotogramma che capita."""
    fisso = eco_puntatore(300, 400)
    for g in v["giri"]:
        for c in g["campioni"]:
            if c.get("eco_marca", {}).get("c_e"):
                c["eco_marca"]["disegno"] = fisso
                c["eco"] = eco_scomponi(fisso)
    return v


def _g_coordinate_storte(v):
    """⛔ Il server trasforma le coordinate — `RCP.md` §7.3 lo vieta."""
    for g in v["giri"]:
        for s in g["sonde"]:
            c = s.get("scomodo")
            if c and c.get("eco", {}).get("tipo") == ECO_PUNTATORE:
                c["eco"] = dict(c["eco"], x=c["eco"]["x"] + 3)
    return v


def _g_p1_ritorno_non_ritarda(v):
    for g in v["giri"]:
        if g.get("ritardo_ritorno_ms"):
            g["distribuzione"] = dict(v["giri"][0]["distribuzione"])
            g["scomposizione"] = dict(v["giri"][0]["scomposizione"])
    return v


def _g_p1_andata_non_ritarda(v):
    """⛔⛔ IL GUASTO CHE ALLA FASE 3 NON ERA NEMMENO ESPRIMIBILE."""
    for g in v["giri"]:
        if g.get("ritardo_andata_ms"):
            g["distribuzione"] = dict(v["giri"][0]["distribuzione"])
            g["scomposizione"] = dict(v["giri"][0]["scomposizione"])
    return v


def _g_confine_si_chiude_prima_del_disegno(v):
    """⛔⛔⛔ IL GUASTO CHE IL MONDO VERO AVEVA GIA' INNESTATO DA SOLO — fase 8.

    Il banco chiude il confine quando il richiamo del prodotto RITORNA.  Sulla
    strada `bitmaprenderer` `createImageBitmap` e' asincrona: li' non e' stato
    dipinto niente.  ⇒ Un ritardo innestato **fra il fotogramma pronto e il
    vetro** diventa **invisibile**, e il banco consegna un numero piu' piccolo
    del vero con l'aria di funzionare.

    ⭐ E' `LEZIONI.md` §1.20: il confine si e' spostato nella direzione comoda
       **da solo**, quando e' cambiato il prodotto, senza che nessuno lo
       decidesse.  ⛔ Il banco DEVE diventare rosso qui, o quel numero uscirebbe
       in un documento con la marca `[M]`.
    """
    for g in v["giri"]:
        if g.get("ritardo_vetro_ms"):
            g["distribuzione"] = dict(v["giri"][0]["distribuzione"])
            g["scomposizione"] = dict(v["giri"][0]["scomposizione"])
            g["distanza_fra_i_confini"] = dict(
                v["giri"][0]["distanza_fra_i_confini"])
            g["distribuzione_vecchio"] = dict(
                v["giri"][0]["distribuzione_vecchio"])
    return v


def _g_i_due_confini_sono_lo_stesso_punto(v):
    """⛔⛔ IL GUASTO PIU' SUBDOLO DEI DUE: il numero SALE di N — quindi la
    pretesa 1 di Q11 passa, e il banco sembra tarato — ⛔ ma sale anche il
    confine VECCHIO, cioe' i due punti coincidono.

    ⚠ Se coincidessero davvero, l'intera cura di §4-bis non servirebbe a
      niente e il difetto che la fase 8 dichiara di aver curato non
      esisterebbe.  ⇒ E' la pretesa 1, e senza di lei un banco che chiudesse
      «un po' piu' in la'» passerebbe lo stesso.
    """
    for g in v["giri"]:
        n = g.get("ritardo_vetro_ms")
        if not n:
            continue
        # il totale sale (la pretesa 3 passa)...
        d = dict(g.get("distribuzione_vecchio") or {})
        if d.get("mediana") is not None:
            d["mediana"] = d["mediana"] + n
            g["distribuzione_vecchio"] = d
        # ...⛔ ma la DISTANZA fra i due confini resta quella di sempre
        g["distanza_fra_i_confini"] = dict(v["giri"][0]["distanza_fra_i_confini"])
    return v


def _g_p1_nel_tratto_sbagliato(v):
    """⛔⛔ IL GUASTO CHE UN P1 DELLA FASE 3 NON VEDE: la mediana sale di N —
    quindi «la mediana e' salita di N» passa — ⛔ ma il surplus e' finito nel
    tratto SBAGLIATO della scomposizione.  Un metro cosi' non diventa mai
    rosso: dice solo bugie sulla diagnosi."""
    for g in v["giri"]:
        n = (g.get("ritardo_andata_ms") or g.get("ritardo_ritorno_ms")
             or g.get("ritardo_vetro_ms"))
        if not n:
            continue
        s = dict(v["giri"][0]["scomposizione"])
        # il totale sale...
        for k in list(s):
            if k.startswith("T "):
                s[k] = dict(s[k], mediana=s[k]["mediana"] + n)
        # ...ma il surplus lo si mette nel tratto 8 (la decodifica), che non
        # c'entra niente con nessuno dei due rami
        for k in list(s):
            if k.startswith("8 "):
                s[k] = dict(s[k], mediana=s[k]["mediana"] + n)
        g["scomposizione"] = s
    return v


def _g_confine_comodo(v):
    """⛔⛔ IL GUASTO PIU' IMPORTANTE DEL BANCO: il metro chiude sul confine
    COMODO — cioe' prende come fotogramma buono il primo con `input >= id`
    invece del primo in cui l'eco e' cambiato.

    ⭐ E' esattamente il difetto che `CODER.md` §1-bis vieta, dal lato
       dell'INGRESSO invece che da quello dell'uscita: un numero piu' corto del
       vero, ottenuto senza sbagliare nessun conto."""
    for g in v["giri"]:
        for s in g["sonde"]:
            if s.get("comodo") is not None:
                s["scomodo"] = s["comodo"]
                s["ritardo_scomodo_ms"] = s.get("ritardo_comodo_ms")
    return v


def _g_grana_grossa(v):
    v["isolata"] = False
    v["grana"] = {"salti": 4000, "minimo_ms": 1.0, "mediano_ms": 1.0}
    return v


def _g_banco_caro(v):
    v["fps_con_lettura"] = 31.0
    v["costo_lettura_us"] = [9000.0] * 500
    return v


def _g_un_drawImage_solo(v):
    """⛔ Il banco non separa i due `drawImage`: il tratto resta quello della
    fase 3, cioe' un numero vero con un'etichetta falsa."""
    for g in v["giri"]:
        for c in g["campioni"]:
            c["disegni_ms"] = []
            c["t_dip_a"] = None
        for s in g["sonde"]:
            if s.get("scomodo"):
                s["scomodo"]["t_dip_a"] = None
    return v


GUASTI = [
    ("Q0 il canale di input NON C'E' (nessun §7.3 sul filo)",
     _g_niente_input, ["Q0"]),
    ("Q0 l'input esce sul filo ma NON arriva al desktop",
     _g_input_non_arriva_al_desktop, ["Q0"]),
    ("Q0 il conto della scena non si legge (⚠ «non arrivato» ≠ «non guardato»)",
     _g_scena_senza_conto, ["Q0"]),
    ("Q1 ⛔ la scena e' SUL MONITOR SBAGLIATO (la trappola §1.1-bis)",
     _g_scena_sul_monitor_sbagliato, ["Q1"]),
    ("Q1 nessun `wl_surface.enter`: «non lo so» ≠ «e' sul mio»",
     _g_nessun_enter, ["Q1"]),
    ("Q3 l'eco non si legge piu'", _g_eco_illeggibile, ["Q2", "Q3"]),
    ("Q4 ⛔ il rilevatore dell'eco dice SEMPRE si'",
     _g_eco_dice_sempre_si, ["Q4"]),
    ("Q4 l'eco non cambia mai", _g_eco_fermo, ["Q4"]),
    ("Q4 ⛔ il server TRASFORMA le coordinate (§7.3 lo vieta)",
     _g_coordinate_storte, ["Q4"]),
    ("Q5 il ponte non ritarda il RITORNO", _g_p1_ritorno_non_ritarda, ["Q5"]),
    ("Q6 ⭐ il ponte non ritarda l'ANDATA", _g_p1_andata_non_ritarda, ["Q6"]),
    ("Q5/Q6/Q11 ⛔⛔ la mediana sale di N ma NEL TRATTO SBAGLIATO",
     _g_p1_nel_tratto_sbagliato, ["Q5", "Q6", "Q11"]),
    ("Q7 ⛔⛔ il metro chiude sul confine COMODO", _g_confine_comodo, ["Q7"]),
    ("Q11 ⛔⛔⛔ il confine SI CHIUDE PRIMA DEL DISEGNO (il ritardo al vetro "
     "e' invisibile) — il difetto che `bitmaprenderer` aveva innestato da solo",
     _g_confine_si_chiude_prima_del_disegno, ["Q11"]),
    ("Q11 ⛔⛔ il numero sale di N ma sale ANCHE il confine vecchio: i due "
     "punti coincidono e la cura non serve a niente",
     _g_i_due_confini_sono_lo_stesso_punto, ["Q11"]),
    ("Q8 il banco non separa i due `drawImage`", _g_un_drawImage_solo, ["Q8"]),
    ("Q10 la pagina non e' isolata", _g_grana_grossa, ["Q10"]),
    ("Q9 il banco costa mezzo ritmo", _g_banco_caro, ["Q9"]),
]


def certifica(verboso=True):
    import copy
    esiti = []

    def dice(t, buono):
        esiti.append({"controllo": t, "esito": bool(buono)})
        if verboso:
            (ok if buono else ko)(t)

    log("A. Il PONTE — il ritardo noto sui DUE rami e l'ancora dell'orologio")
    p = ponte_modulo()
    rp = p.certifica(verboso=False)
    dice("il ponte e' %s (%d controlli su %d), e i DUE rami sono separati: %s"
         % (rp["esito"], rp["passati"], rp["controlli"],
            "; ".join("%s → andata %+.2f ritorno %+.2f"
                      % (r["dove"], r["salita_andata_ms"], r["salita_ritorno_ms"])
                      for r in rp.get("rami", []))),
         rp["esito"] == "PROMOSSO")

    log("B. L'ECO — le due implementazioni (C e Python) si incontrano")
    # ⛔ L'aritmetica dell'eco e' scritta due volte, in due linguaggi.  Qui si
    #    verifica che dicano la stessa cosa su valori noti — e in tutt'e due i
    #    versi, perche' un `componi` e un `scomponi` sbagliati allo stesso modo
    #    tornerebbero d'accordo fra loro e in disaccordo col mondo.
    giusti = 0
    for x, y in ((0, 0), (1, 1), (1919, 1079), (3839, 2159), (16383, 16383)):
        d = eco_scomponi(eco_puntatore(x, y))
        if d["tipo"] == ECO_PUNTATORE and d["x"] == x and d["y"] == y:
            giusti += 1
    dice("l'eco del PUNTATORE torna in tutt'e due i versi su 5 casi limite "
         "(%d su 5, 4K e il massimo dei 14 bit compresi)" % giusti, giusti == 5)
    g2 = 0
    for cod, prem, seq in ((30, 1, 0), (0x110, 0, 2047), (65535, 1, 1)):
        d = eco_scomponi(eco_tasto(cod, prem, seq))
        if (d["tipo"] == ECO_TASTO and d["codice"] == cod
                and d["premuto"] == bool(prem) and d["seq"] == seq):
            g2 += 1
    dice("l'eco del TASTO torna su 3 casi limite (%d su 3, `KEY_A`=30 e "
         "`BTN_LEFT`=0x110 compresi)" % g2, g2 == 3)
    dice("un eco assente dice «non ho potuto guardare», non «zero»",
         eco_scomponi(None).get("tipo") is None
         and "non ho potuto" in eco_scomponi(None).get("perche", ""))
    dice("un eco a ZERO dice «la scena non ha ancora ricevuto niente», che e' "
         "un'altra frase ancora",
         eco_scomponi(0).get("tipo") == ECO_NIENTE
         and "NESSUN input" in eco_scomponi(0).get("perche", ""))

    log("C. IL LETTORE DEI MESSAGGI DI INPUT — sul FILO, non nell'intenzione")
    # ⛔ `LEZIONI.md` §1.9 regola 5: «un denominatore si legge dove la cosa
    #    succede — sul filo, non nella configurazione».
    b = struct.pack(">HI", RCP_PUNTATORE, 20) + struct.pack(">IQII", 7, 12345, 1919, 1079)
    f, n = leggi_messaggio_input(b)
    dice("un PUNTATORE ben formato si legge (id=%s x=%s y=%s, %d byte)"
         % ((f or {}).get("id"), (f or {}).get("x"), (f or {}).get("y"), n),
         f and f["id"] == 7 and f["x"] == 1919 and f["y"] == 1079 and n == 26)
    f2, n2 = leggi_messaggio_input(b[:10])
    dice("mezzo messaggio dice «non ho abbastanza byte» (0), non «non e' un "
         "input» (-1)", f2 is None and n2 == 0)
    f3, n3 = leggi_messaggio_input(struct.pack(">HI", 0x0301, 4) + b"\x00" * 4)
    dice("un fotogramma (0x0301) dice «non e' un input e non lo sara' mai» (-1)",
         f3 is None and n3 == -1)
    b4 = struct.pack(">HI", RCP_PUNTATORE, 24) + b"\x00" * 24
    f4, _ = leggi_messaggio_input(b4)
    dice("un PUNTATORE con la lunghezza SBAGLIATA si DICHIARA violazione "
         "invece di essere letto storto", f4 and "violazione" in f4)

    log("D. I GIUDICI — tre giri: sano → guasto → RISANATO")
    sano = verbale_sintetico()
    g_sano = giudica(sano)
    verdi = [k for k in TUTTI if g_sano[k].get("esito")]
    dice("giro SANO: tutti e %d i controlli sono verdi (%s)"
         % (len(TUTTI), ", ".join(verdi)), len(verdi) == len(TUTTI))
    if len(verdi) != len(TUTTI):
        for k in TUTTI:
            if not g_sano[k].get("esito"):
                inf("  ⛔ %s: %s" % (k, json.dumps(g_sano[k], ensure_ascii=False)[:400]))

    accusati = 0
    for nome, rompi, attesi in GUASTI:
        v = rompi(copy.deepcopy(verbale_sintetico()))
        gg = giudica(v)
        rossi = [k for k in TUTTI if not gg[k].get("esito")]
        preso = all(k in rossi for k in attesi)
        if preso:
            accusati += 1
        # ⛔ Gli `extra` si CONTANO e si STAMPANO, e non bocciano — la stessa
        #    scelta di `03-b17`, e per la stessa ragione: stringere il criterio
        #    adesso boccerebbe il giro sano e sposterebbe il metro dentro la
        #    misura.  ⚠ Ma il commento dice il VERO su che cosa il codice fa.
        extra = [k for k in rossi if k not in attesi]
        dice("guasto «%s» → rossi %s (attesi %s)%s"
             % (nome, rossi or "nessuno", attesi,
                "  ⚠ e ne sporca altri: %s" % extra if extra else ""), preso)
        g2b = giudica(verbale_sintetico())
        dice("  risanato «%s»: torna tutto verde" % nome,
             all(g2b[k].get("esito") for k in TUTTI))

    log("E. ⛔⛔ IL CODICE D'USCITA — «non ho niente da giudicare» NON e' 0")
    for nome, rompi in (("nessun messaggio sul filo", _g_niente_input),
                        ("l'input non arriva al desktop",
                         _g_input_non_arriva_al_desktop),
                        ("nessuna sonda chiusa",
                         lambda v: (_g_eco_illeggibile(v),
                                    [g.update(sonde=[]) for g in v["giri"]], v)[-1])):
        v = rompi(copy.deepcopy(verbale_sintetico()))
        gg = giudica(v)
        u = codice_uscita(gg)
        dice("«%s» → codice d'uscita %d (NON %d, e NON %d)"
             % (nome, u, USCITA_CONFORME, USCITA_NON_CONFORME),
             u == USCITA_NIENTE_DA_GIUDICARE)
    v = _g_eco_fermo(copy.deepcopy(verbale_sintetico()))
    dice("un rosso VERO invece esce %d (e non si confonde col %d)"
         % (USCITA_NON_CONFORME, USCITA_NIENTE_DA_GIUDICARE),
         codice_uscita(giudica(v)) == USCITA_NON_CONFORME)
    dice("il giro SANO esce %d" % USCITA_CONFORME,
         codice_uscita(g_sano) == USCITA_CONFORME)

    log("F. ⛔ IL DENOMINATORE — «0 punti su 0» si STAMPA")
    v = _g_scena_sul_monitor_sbagliato(copy.deepcopy(verbale_sintetico()))
    q1 = giudica(v)["Q1"]
    dice("scena sul monitor sbagliato → punti %s su %s, e la riga lo DICE"
         % (q1.get("punti"), q1.get("denominatore")),
         q1.get("punti") == 0 and q1.get("denominatore") == 0
         and "0 punti su 0" in (q1.get("perche") or ""))

    log("G. ⭐ IL NUMERO CHE IL FINTO PRODUCE — e deve essere quello atteso")
    # ⛔ `CODER.md` §3.3: il banco deve saper produrre il RISULTATO ATTESO prima
    #    di essere puntato sull'incognita.  Qui il finto e' costruito con un
    #    ritardo vero di 62 ms, e il banco deve ritrovarlo.
    base = sano["giri"][0]
    d = base["distribuzione"]
    dice("il finto porta %d sonde chiuse e la mediana e' %.2f ms — e l'attesa "
         "NON e' un numero a mano: e' la somma dei tratti dichiarati, %.2f"
         % (d.get("n", 0), d.get("mediana", -1), FINTO_TOTALE),
         d.get("n", 0) > 100 and abs(d.get("mediana", 0) - FINTO_TOTALE) <= 1.5)
    sc = base["scomposizione"]
    somma = sum(x["mediana"] for k, x in sc.items()
                if isinstance(x, dict) and "mediana" in x and k[0] not in "TΔC")
    tot = next(x["mediana"] for k, x in sc.items() if k.startswith("T ⭐"))
    dice("⛔ e i tratti SOMMANO al totale (%.2f contro %.2f, scarto %.2f ms): un "
         "tratto perso per strada e' un pezzo di catena che nessuno guarda"
         % (somma, tot, abs(somma - tot)), abs(somma - tot) <= 1.5)
    # ⛔⛔ E IL CONTROLLO CHE VALE PIU' DI TUTTI, SUL FINTO: i DUE confini
    #     devono cadere su due fotogrammi DIVERSI.  Un finto in cui coincidono
    #     certificherebbe Q7 su un mondo in cui il difetto che Q7 cerca **non
    #     puo' esistere** — cioe' lo certificherebbe verde per costruzione.
    q7 = g_sano["Q7"]
    dice("⭐ i due confini cadono su fotogrammi DIVERSI: il comodo si regala "
         "%s ms (mediana), su %d sonde"
         % ((q7.get("regalo_ms") or {}).get("mediana"),
            q7.get("sonde_con_tutt_e_due", 0)),
         q7.get("esito") and (q7.get("regalo_ms") or {}).get("mediana", 0) > 5.0)

    log("H. ⛔⛔ LA STAMPA E I GIUDICI GUARDANO LA STESSA SCOMPOSIZIONE")
    # ⛔ Nato da un difetto vero (14 agosto 2026): la stampa leggeva lo scarto
    #    d'orologio da una chiave che nel verbale non esisteva piu', quindi non
    #    lo sottraeva — e la certificazione restava VERDE, perche' i giudici
    #    sono funzioni pure e la stampa non e' un giudice.
    #    ⇒ Questo controllo lega le due cose: se un giorno divergono di nuovo,
    #      qui diventa rosso invece di uscire in un rapporto.
    sc_stampa = scomponi(sano["giri"][0]["sonde"],
                         sano.get("scarto_ancora_us", 0))
    sc_giudice = sano["giri"][0]["scomposizione"]
    fuori_scala = [k for k, x in sc_stampa.items()
                   if isinstance(x, dict) and "mediana" in x
                   and abs(x["mediana"]) > 1000.0]
    dice("nessun tratto e' fuori scala (> 1000 ms): lo scarto fra i due orologi "
         "e' stato sottratto davvero%s"
         % ("" if not fuori_scala else " — ⛔ fuori scala: %s" % fuori_scala[:3]),
         not fuori_scala)
    diverse = [k for k in sc_giudice
               if isinstance(sc_giudice[k], dict) and "mediana" in sc_giudice[k]
               and abs(sc_giudice[k]["mediana"]
                       - (sc_stampa.get(k) or {}).get("mediana", 1e9)) > 1e-6]
    dice("la scomposizione che si STAMPA e quella che GIUDICANO Q5/Q6 sono la "
         "stessa (%d tratti, 0 differenze)" % len(sc_giudice), not diverse)

    passati = sum(1 for e in esiti if e["esito"])
    return {"controlli": len(esiti), "passati": passati, "esiti": esiti,
            "guasti_innestati": len(GUASTI), "guasti_accusati": accusati,
            "esito": "PROMOSSO" if passati == len(esiti) else "BOCCIATO"}


# ═══════════════════════════════════════════════════════════════════════════
# §9  IL CODICE D'USCITA — ⛔ in una funzione, perche' sia UNO solo
# ═══════════════════════════════════════════════════════════════════════════
def codice_uscita(g):
    """⛔⛔ «NON HO NIENTE DA GIUDICARE» ha un codice SUO.

    ⭐ E' il difetto che il validatore della fase 1 aveva e che gli e' costato
       una riscrittura: usciva «conforme» avendo giudicato zero cose.
       *«Tutti quelli provati sono andati bene» e' vero anche quando i provati
       sono zero* (`LEZIONI.md` §1.9, sesta veste).

    ⛔ E l'ordine conta: **prima** si guarda se c'era qualcosa da giudicare, poi
       se e' andato bene.  Al contrario, un banco senza niente da misurare
       uscirebbe rosso — che manda a cercare un difetto che non c'e'.
    """
    if g.get("Q0", {}).get("niente_da_giudicare"):
        return USCITA_NIENTE_DA_GIUDICARE
    if not g.get("Q1", {}).get("esito") and g["Q1"].get("denominatore") == 0:
        # ⛔ La scena sul monitor sbagliato non e' «l'anello e' rotto»: e' «non
        #    ho misurato niente», ed e' lo stesso stato di Q0.
        return USCITA_NIENTE_DA_GIUDICARE
    return (USCITA_CONFORME if all(g[k].get("esito") for k in TUTTI)
            else USCITA_NON_CONFORME)


# ═══════════════════════════════════════════════════════════════════════════
# §10  LA STAMPA DEL VERDETTO
# ═══════════════════════════════════════════════════════════════════════════
def stampa_verdetto(v):
    g = giudica(v)
    log("GLI %d CONTROLLI" % len(TUTTI))
    for k in TUTTI:
        r = g[k]
        (ok if r.get("esito") else ko)(
            "%-4s %s" % (k, r.get("perche") or json.dumps(
                {x: y for x, y in r.items() if x != "perche"},
                ensure_ascii=False)[:230]))
    giri = v.get("giri", [])
    base = next((x for x in giri if not x.get("ritardo_ritorno_ms")
                 and not x.get("ritardo_andata_ms")), None) or (giri[0] if giri else {})
    sonde = base.get("sonde", [])
    d = _d([s["ritardo_scomodo_ms"] for s in sonde
            if s.get("ritardo_scomodo_ms") is not None])

    log("⛔ IL DENOMINATORE, PRIMA DEL NUMERO")
    q0, q1 = g["Q0"], g["Q1"]
    inf("messaggi di input usciti sul filo ....... %s" % q0.get("messaggi_di_input_spediti"))
    inf("eventi ricevuti DALLA SCENA ............. %s" % q0.get("eventi_ricevuti_dalla_scena"))
    inf("sonde tentate ........................... %s" % q0.get("sonde_tentate"))
    inf("sonde CHIUSE (il denominatore vero) ..... %s" % q0.get("sonde_chiuse"))
    (inf if q1.get("esito") else ko)(
        "scena sul monitor catturato ............. %s  ⇒ %s punti su %s"
        % (q1.get("scena_sul_mio_monitor"), q1.get("punti"), q1.get("denominatore")))

    if q0.get("niente_da_giudicare"):
        log("⛔⛔ NON HO NIENTE DA GIUDICARE")
        ko(q0.get("perche"))
        return g

    log("IL NUMERO — ⛔ coi DUE pezzi ciechi accanto")
    inf(json.dumps(d, ensure_ascii=False))
    inf(con_pezzi_ciechi(d.get("mediana"), v.get("su_xvfb", True)))

    log("LA SCOMPOSIZIONE — ⛔ mai un totale solo")
    # ⛔⛔ LA CHIAVE E' `scarto_ancora_us`, E QUESTA RIGA HA GIA' SBAGLIATO.
    #
    #     `[M]` 14 agosto 2026: qui c'era `v.get("errore_ancora_us", 0)`, un
    #     nome vecchio che nel verbale **non esiste piu'** ⇒ `.get` tornava 0,
    #     lo scarto fra i due orologi non veniva sottratto, e i tratti 2 e 5
    #     uscivano dell'ordine dei **500 000 ms**.
    #     ⛔ E la certificazione era VERDE: i giudici sono funzioni pure e
    #        questa stampa non e' un giudice.  ⭐ A trovarlo e' stato `--finto`,
    #        cioe' il finto usato per quel che serve — vedere che cosa il banco
    #        DIRA' quando il prodotto arriva.  `LEZIONI.md` §2.2 in miniatura.
    #     ⇒ Il controllo H della certificazione adesso pretende che la
    #       scomposizione stampata sia **la stessa** che giudicano Q5 e Q6.
    sc = scomponi(sonde, v.get("scarto_ancora_us", 0))
    for k, x in sc.items():
        inf("%-72s %s" % (k[:72], json.dumps(x, ensure_ascii=False)[:150]))

    log("⭐ QUANTO AGGIUNGE IL CANALE DI INPUT — la sola cosa NUOVA")
    # ⛔ Misurata sullo STESSO giro e sugli STESSI fotogrammi, non fra due giri:
    #    fra due giri ci si mette in mezzo la deriva, il palco e la contesa
    #    (`LEZIONI.md` §1.13, il difetto di P1 a blocchi).
    # ⭐ E si legge dalla SCOMPOSIZIONE invece di rifare il conto: un secondo
    #    conto della stessa cosa e' un secondo posto in cui sbagliare.
    aggiunta = [x["mediana"] for k, x in sc.items()
                if isinstance(x, dict) and "mediana" in x
                and k[:2] in ("1a", "1b", "2 ", "3 ")]
    inf("i tratti che il metro della fase 3 NON attraversava: %s  ⇒  somma "
        "%.2f ms" % ([round(a, 2) for a in aggiunta], sum(aggiunta)))
    inf("⚠ i due numeri NON si sommano e non si sottraggono: «input → vetro» "
        "CONTIENE «disegno della scena → vetro».  ⛔ La quantita' nuova e' "
        "questa somma, ed e' la sola cosa che questo banco puo' dire di piu'")

    log("IL VERDETTO")
    inf(json.dumps(verdetto(d, v.get("su_xvfb", True)),
                   ensure_ascii=False, indent=1))
    return g


def deposita(riga):
    riga = dict(riga)
    riga.setdefault("quando", time.strftime("%FT%T"))
    with open(ESITI, "a") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# §11  LA MISURA — sulla catena vera
# ═══════════════════════════════════════════════════════════════════════════
def leggi_stato_scena(percorso_shm):
    """⛔ Il blocco `stato_input` di `04-b30-scena.c`, letto col seqlock."""
    try:
        with open(percorso_shm, "rb") as f:
            b = f.read()
    except OSError as e:
        return None, "⛔ non ho potuto leggere %s: %s" % (percorso_shm, e)
    return leggi_stato_scena_da_byte(b)


def leggi_stato_scena_da_byte(b):
    """⛔ Il blocco `stato_input` di `04-b30-scena.c`, dai byte grezzi.

    ⭐ Sta DOPO `struct stato_condiviso`, e l'offset non si indovina: si legge
       dal campo `taglia` del primo blocco.  ⚠ Se la magia non torna, si dice
       «non ho potuto guardare» invece di restituire zeri — che sarebbero
       indistinguibili da «nessun evento e' arrivato».

    ⛔ E i byte arrivano DA UN'ALTRA MACCHINA (la scena gira sul server): per
       questo la funzione prende i byte e non un percorso.  Il seqlock lo
       verifica chi chiama, su DUE istantanee — vedi `scena_dal_server()`.
    """
    if len(b) < 16:
        return None, "⛔ il blocco e' troppo corto: %d byte" % len(b)
    magia, _versione, taglia = struct.unpack("<III", b[:12])
    if magia != 0x524D5853:
        return None, ("⛔ magia %08x: non e' il blocco di una scena REMOTIX"
                      % magia)
    o = taglia
    if len(b) < o + 16:
        return None, ("⛔ non c'e' nessun blocco `stato_input` dopo i %d byte "
                      "della scena: questa NON e' `04-b30-scena.c`.  ⚠ E' la "
                      "scena della fase 3, che l'input non lo riceve" % o)
    m2, v2, t2 = struct.unpack("<III", b[o:o + 12])
    if m2 != 0x524D5849:
        return None, ("⛔ il secondo blocco ha magia %08x invece di RMXI: "
                      "la scena non e' quella di questo banco" % m2)
    # seq, 4×u64 eventi, 2×u64 fuochi, 2×u32 fuoco, eco, riempi, 3×u64, 4×u32
    campi = struct.unpack("<QQQQQQQIIIIQQQIIII", b[o + 16:o + 16 + 8 * 10 + 4 * 8])
    d = {"seq": campi[0], "eventi_puntatore": campi[1],
         "eventi_pulsante": campi[2], "eventi_rotella": campi[3],
         "eventi_tasto": campi[4], "fuochi_presi": campi[5],
         "fuochi_persi": campi[6], "ho_il_fuoco_puntatore": campi[7],
         "ho_il_fuoco_tastiera": campi[8], "eco": campi[9],
         "eco_us": campi[11], "eco_disegnato_us": campi[12],
         "eco_disegni": campi[13], "seat_visto": campi[14],
         "seat_puntatore": campi[15], "seat_tastiera": campi[16],
         "versione_blocco": v2, "taglia_blocco": t2}
    return d, None


# ───────────────────────────────────────────────────────────────────────────
# §11.1  GLI ATTREZZI DEL GIRO — ssh, ponte, scena, palco
# ───────────────────────────────────────────────────────────────────────────
def _sshpw(comando, silenzioso=False, attesa=300):
    """⛔ MAI una redirezione ATTORNO a `ssh`: la richiesta della parola di
    `sudo` va sullo stderr, e una redirezione la mangia — il comando resta
    appeso per sempre, in silenzio.  Pagata sei volte."""
    r = subprocess.run(["python3", os.path.join(RADICE, "v1/strumenti/sshpw.py"),
                        comando], capture_output=True, text=True, timeout=attesa)
    if not silenzioso and r.returncode != 0:
        dub("ssh ha risposto %d: %s" % (r.returncode, (r.stderr or "")[-200:]))
    return r


def _sudo(comando, **kw):
    # ⚠ `sudo -S -p …` e MAI dentro una pipe: dentro una pipe `sudo` resta
    #   appeso perche' la richiesta non arriva a nessuno.
    return _sshpw("sudo -S -p 'Password sudo: ' " + comando, **kw)


def metti_ritardo(a, ritorno_ms=0.0, andata_ms=0.0, giro="-"):
    """⛔ Cambia i DUE ritardi del ponte senza riaccenderlo.

    Riaccenderlo riaccenderebbe la sessione QUIC, e si confronterebbero
    distribuzioni prese in condizioni diverse.  ⭐ E i rami sono due: `ritardo_ms`
    e' il RITORNO (prodotto → cliente, il tratto 5) e `ritardo_andata_ms` e'
    l'ANDATA (cliente → prodotto, il tratto 2) — la meta' che alla fase 3 non
    esisteva.
    """
    testo = ("ritardo_ms=%s\\nritardo_andata_ms=%s\\nfuori_ordine=0\\n"
             "giro=%s\\n" % (ritorno_ms, andata_ms, giro))
    r = _sshpw("printf '%s' > %s" % (testo, a.comando_ponte), silenzioso=True)
    return r.returncode == 0


def scena_dal_server(a):
    """⛔ Il blocco di stato della scena, letto DALL'ALTRA MACCHINA e col seqlock.

    ⭐ Due istantanee in una sola andata: si pretende `seq` **pari e uguale**
       nelle due.  ⚠ Se non lo e', si dice «non ho potuto guardare» — che non e'
       «l'input non e' arrivato al desktop».  Sono due diagnosi diverse e
       mandano a cercare in due posti diversi (`LEZIONI.md` §1.9).
    """
    r = _sudo("bash %s scena-stato" % a.terreno, silenzioso=True)
    righe = [x.strip() for x in (r.stdout or "").splitlines() if len(x.strip()) > 40]
    if len(righe) < 2:
        return None, ("⛔ NON HO POTUTO GUARDARE il blocco della scena: "
                      "«%s»" % ((r.stdout or "") + (r.stderr or ""))[-200:])
    letti = []
    for x in righe[-2:]:
        try:
            d, e = leggi_stato_scena_da_byte(base64.b64decode(x))
        except Exception as exc:                     # noqa: BLE001
            return None, "⛔ il blocco non si e' decodificato: %s" % exc
        if d is None:
            return None, e
        letti.append(d)
    if letti[0]["seq"] % 2 or letti[0]["seq"] != letti[1]["seq"]:
        return None, ("⛔ il seqlock non si e' fermato (seq %d e %d): NON ho un "
                      "conto coerente da consegnare"
                      % (letti[0]["seq"], letti[1]["seq"]))
    return letti[0], None


def scena_uscite(a):
    """⭐ `uscita_chiesta` e `uscita_confermata` dal PRIMO blocco della scena.

    ⛔ `uscita_confermata` la scrive `wl_surface.enter`, cioe' **il compositore**:
       e' l'unico modo di sapere su quale monitor la scena e' finita davvero.
       ⚠ Vuota = «non lo so», che NON e' «e' sul mio» (Q1).
    """
    r = _sudo("bash %s scena-stato" % a.terreno, silenzioso=True)
    righe = [x.strip() for x in (r.stdout or "").splitlines() if len(x.strip()) > 40]
    if not righe:
        return {"uscita_chiesta": None, "uscita_confermata": None,
                "perche": "⛔ NON HO POTUTO GUARDARE il blocco della scena"}
    b = base64.b64decode(righe[-1])
    m = marca_modulo()
    taglia = struct.calcsize(m.FORMATO_STATO)
    if len(b) < taglia:
        return {"uscita_chiesta": None, "uscita_confermata": None,
                "perche": "⛔ il blocco e' %d byte, ne servono %d" % (len(b), taglia)}
    campi = struct.unpack(m.FORMATO_STATO, b[:taglia])
    def s(x):
        return x.split(b"\0")[0].decode("utf-8", "replace")
    return {"uscita_confermata": s(campi[31]) or None,
            "uscita_chiesta": s(campi[32]) or None,
            "disegni": campi[5], "giro_numero": campi[15],
            "callback_in_volo_massimo": campi[38], "fidato": campi[40]}


def carico_della_macchina(a):
    """⛔⛔⛔ IL CARICO, ACCANTO AL NUMERO — e questa funzione è nata da una
    misura che ha SMENTITO un rapporto, il 22 agosto 2026.

    ⛔ L'agente A aveva consegnato `[M]` **17,48 ms** per il tratto 9 e ci aveva
       costruito sopra la conclusione più citata della fase.  L'agente F3 ha
       rimisurato lo stesso tratto con **tre banchi indipendenti**, sulla stessa
       strada di disegno, e ha trovato `[M]` **0,39 - 1,18 ms**: da **15 a 45
       volte meno**.  ⇒ I 17,48 **non si riproducono da nessuna parte**.

    `[R]` E la causa non era il prodotto: mentre A misurava, sul portatile
       c'erano **4 nuclei, 56 processi Chrome e 5 Xvfb**, perché tre o quattro
       agenti facevano banchi da browser nello stesso momento.

    ⇒ ⭐⭐ **Un anello misurato su un portatile a quattro nuclei con cinque
      Xvfb sopra non è il prodotto: è la contesa.**  E la differenza fra le due
      cose non si vede nel numero — si vede solo se qualcuno ha scritto il
      carico accanto.  Nessuno l'aveva scritto.

    ⛔ Si guarda ai DUE capi (il portatile, dove stanno Chrome e il banco; e il
       server, dove sta il prodotto), e si guarda **due volte** — prima e dopo —
       perché un carico che cambia a metà giro produce un numero che sembra
       buono.  `LEZIONI.md` §2.0: il palco si dichiara accanto al numero.
    """
    def _n(c):
        try:
            return int(subprocess.run(c, shell=True, capture_output=True,
                                      text=True, timeout=30).stdout.strip() or 0)
        except Exception:                                       # noqa: BLE001
            return None

    q = {"nuclei": os.cpu_count()}
    try:
        q["carico_1_5_15"] = [round(x, 2) for x in os.getloadavg()]
    except Exception:                                           # noqa: BLE001
        q["carico_1_5_15"] = None
    q["processi_chrome"] = _n("pgrep -c chrome")
    q["xvfb"] = _n("pgrep -c Xvfb")
    # ⛔ Gli ALTRI banchi di questo stesso file, contati per porta: e' il
    #    conteggio che dice «non ero solo», e senza di lui «non lo so» e «ero
    #    solo» hanno lo stesso aspetto.
    #    ⛔ Si contano le PORTE distinte, non i processi: `pgrep -f` conta anche
    #       la shell che avvolge il comando, e «2» direbbe «c'e' un altro» quando
    #       l'altro sono io.  Un conteggio che si sbaglia da solo e' peggio di
    #       nessun conteggio.
    try:
        u = subprocess.run("pgrep -af 'b30-anello-input.py --misura'",
                           shell=True, capture_output=True, text=True, timeout=30)
        porte = set()
        for riga in (u.stdout or "").splitlines():
            pezzi = riga.split()
            for i, x in enumerate(pezzi):
                if x == "--porta" and i + 1 < len(pezzi):
                    porte.add(pezzi[i + 1])
        q["banchi_b30_in_corso"] = len(porte)
        q["porte_dei_banchi"] = sorted(porte)
    except Exception:                                           # noqa: BLE001
        q["banchi_b30_in_corso"] = None
    q["⛔"] = ("il carico del PORTATILE, dove stanno Chrome e il banco.  ⚠ Se "
               "«banchi_b30_in_corso» e' > 1 o «xvfb» e' > 1, questo numero "
               "porta dentro la contesa di qualcun altro e NON e' il prodotto")
    r = {"chuwi": q}
    rs = _sshpw("nproc; cat /proc/loadavg; pgrep -c remotix; pgrep -c gnome-shell",
                silenzioso=True, attesa=60)
    # ⛔ Le righe si RICONOSCONO, non si contano: `sshpw` ci mette in mezzo la
    #    richiesta della parola e un avvertimento di `tput`, e prendere «la
    #    riga 1» darebbe un numero sbagliato senza lamentarsi di niente.
    righe = [x.strip() for x in (rs.stdout or "").splitlines() if x.strip()]
    s = {}
    numeri = []
    for x in righe:
        pezzi = x.split()
        if len(pezzi) >= 5 and "/" in pezzi[3]:
            try:
                s["carico_1_5_15"] = [float(y) for y in pezzi[:3]]
                continue
            except ValueError:
                pass
        if x.isdigit():
            numeri.append(int(x))
    if len(numeri) >= 3:
        s["nuclei"], s["processi_remotix"], s["sessioni_gnome"] = numeri[:3]
    if "carico_1_5_15" not in s or "nuclei" not in s:
        s["grezzo"] = righe
        s["perche"] = ("⛔ non ho potuto leggere il carico del server: «non lo "
                       "so» non e' «era scarico»")
    r["server"] = s
    return r


def stampa_carico(c, quando):
    q = c.get("chuwi") or {}
    s = c.get("server") or {}
    # ⛔⛔ LA SOGLIA GUARDA IL CARICO DEGLI ALTRI, NON IL MIO — e la ragione è
    #     `[M]`: un giro solo di questo banco tiene gia' **~3,7 nuclei su 4** e
    #     **~29 processi Chrome**.  Una soglia sul carico assoluto sarebbe rossa
    #     sempre, e una bandiera sempre rossa non la guarda piu' nessuno
    #     (`LEZIONI.md` §1.20 dalla parte di chi legge).
    # ⇒ Si accusa quel che **non è mio**: un secondo banco, un secondo Xvfb, o
    #   un numero di processi Chrome che un banco solo non può spiegare.
    #   ⚠ `[M]` 22 agosto, quando A misurava: **56 Chrome e 5 Xvfb** — cioè due
    #     banchi buoni.  La soglia sta in mezzo, a 40.
    stretto = ((q.get("banchi_b30_in_corso") or 0) > 1
               or (q.get("xvfb") or 0) > 1
               or (q.get("processi_chrome") or 0) > 40)
    (dub if stretto else inf)(
        "%s · CHUWI: %s nuclei, carico %s, Chrome %s, Xvfb %s, altri banchi b30 %s"
        % (quando, q.get("nuclei"), q.get("carico_1_5_15"),
           q.get("processi_chrome"), q.get("xvfb"),
           q.get("banchi_b30_in_corso")))
    inf("%s · SERVER: %s nuclei, carico %s, processi remotix %s, sessioni GNOME %s"
        % (quando, s.get("nuclei"), s.get("carico_1_5_15"),
           s.get("processi_remotix"), s.get("sessioni_gnome")))
    if stretto:
        dub("⛔⛔ LA MACCHINA NON E' SCARICA: questo numero porta dentro la "
            "contesa.  ⚠ `[M]` 22 agosto 2026: con 56 Chrome e 5 Xvfb sopra, "
            "lo stesso tratto e' uscito **da 15 a 45 volte** piu' grande del "
            "vero.  ⇒ Il numero si scrive col carico ACCANTO, o non si scrive")
    return stretto


def monitor_del_prodotto(a):
    """⛔ Quale monitor il prodotto sta catturando — LETTO DAL SUO REGISTRO.

    ⚠ Non si deduce e non si scrive a mano: su questa macchina i monitor
      virtuali sono piu' d'uno (il prodotto dell'utente, gli altri banchi), e un
      nome indovinato metterebbe la scena sul palco di qualcun altro — `[M]` 13
      agosto 2026, zero fotogrammi per dieci secondi con la catena perfetta.
    """
    r = _sudo("grep -aoh 'monitor «[^»]*»' %s | tail -1" % a.registro_prodotto,
              silenzioso=True)
    # ⛔ SI PRENDE L'ULTIMA RIGA, non tutto lo stdout — `[M]` 14 agosto 2026:
    #    `sshpw` stampa anche «nicfio@…'s password:» e un avviso di `tput`, e la
    #    prima stesura li portava dentro il nome del monitor.  ⇒ Q1 confrontava
    #    «Meta-0» con «…password:\ntput…\nMeta-0» e dichiarava LA SCENA SUL
    #    MONITOR SBAGLIATO: un rosso del banco travestito da rosso del prodotto.
    righe = [x.strip() for x in (r.stdout or "").splitlines()
             if "monitor «" in x]
    if not righe:
        return None
    n = righe[-1]
    n = n[n.index("monitor «") + len("monitor «"):]
    n = n.split("»")[0].strip()
    return n or None


# ───────────────────────────────────────────────────────────────────────────
# §11.2  ⛔⛔ LA MAPPA DALLA VISTA ALLA TELA — e si MISURA, non si suppone
# ───────────────────────────────────────────────────────────────────────────
#
# ⛔ Il problema, e nessuno l'aveva scritto: `event.clientX` sta nel sistema di
#    coordinate del BROWSER, `RCP.md` §7.3 porta quelle della TELA REMOTA, e fra
#    i due c'e' la scala della vista, le bande nere e l'arrotondamento per
#    difetto di `cl_manda_puntatore` (`src/pagina.html`).  ⇒ Appaiare l'evento al
#    messaggio «per coordinate» **fallisce sempre** se le due coordinate non
#    sono nello stesso sistema, e il banco direbbe *«nessun evento con queste
#    coordinate»* su una catena perfettamente funzionante.
#
# ⭐ E LA CURA NON E' UNA TOLLERANZA: e' scegliere le coordinate DELLA TELA e
#    calcolare dove cliccare, invece di cliccare e sperare.  Cosi' la mappa
#    diretta serve solo come CONTROLLO — e il controllo si stampa: «quanti
#    messaggi spediti hanno un evento che ci cade sopra, su quanti».
#
# ⛔ Se quel numero non e' ~100 %, il banco lo DICHIARA e non aggiusta la
#    tolleranza finche' passa: quella e' la mossa che `LEZIONI.md` §1.13 vieta.
GEOMETRIA_VISTA = r"""
(function () {
  const t = document.getElementById("schermo");
  if (!t) return {c_e: false, perche: "⛔ non c'e' nessuna tela «schermo»"};
  const r = t.getBoundingClientRect();
  const S = window.REMOTIX && window.REMOTIX.schermo;
  const d = (S && S.dipinta) || null;
  return {c_e: !!d, left: r.left, top: r.top, rw: r.width, rh: r.height,
          cw: t.width, ch: t.height, d: d,
          perche: d ? null : "⛔ `schermo.dipinta` non c'e' ancora: nessun "
                             + "fotogramma e' stato disegnato, e senza non so "
                             + "dove finisce l'immagine dentro il buffer"};
})()
"""


class Vista:
    """⛔ La conversione fra le coordinate del BROWSER e quelle della TELA.

    ⭐ E' il gemello in Python di `cl_geometria()` + `cl_manda_puntatore()` di
       `src/pagina.html`, scritto **due volte apposta**: se un giorno i due
       divergono, il controllo della mappa se ne accorge invece di produrre
       zero sonde senza dire perche'.
    """

    def __init__(self, g):
        self.g = g
        self.vx = g["rw"] / g["cw"] if g.get("cw") else 0.0
        self.vy = g["rh"] / g["ch"] if g.get("ch") else 0.0
        d = g.get("d") or {}
        self.bx0, self.by0 = d.get("x", 0), d.get("y", 0)
        f = d.get("fotogramma") or [0, 0]
        self.tl, self.ta = int(f[0]), int(f[1])
        self.sx = (d.get("l", 0) / f[0]) if f[0] else 0.0
        self.sy = (d.get("a", 0) / f[1]) if f[1] else 0.0

    def utilizzabile(self):
        return all((self.vx, self.vy, self.sx, self.sy, self.tl, self.ta))

    def a_tela(self, cx, cy):
        """browser → tela remota, con la SATURAZIONE e l'arrotondamento del
        prodotto (`cl_satura` + `Math.floor` + l'ultimo pixel valido)."""
        px = ((cx - self.g["left"]) / self.vx - self.bx0) / self.sx
        py = ((cy - self.g["top"]) / self.vy - self.by0) / self.sy
        px = min(max(px, 0.0), float(self.tl))
        py = min(max(py, 0.0), float(self.ta))
        return (min(int(px // 1), self.tl - 1), min(int(py // 1), self.ta - 1))

    def a_vista(self, X, Y):
        """tela remota → browser, ⭐ al CENTRO del pixel: cosi' l'andata e il
        ritorno tornano anche quando la scala non e' 1."""
        cx = self.g["left"] + ((X + 0.5) * self.sx + self.bx0) * self.vx
        cy = self.g["top"] + ((Y + 0.5) * self.sy + self.by0) * self.vy
        return cx, cy


# ⛔ I TASTI DELLA PROVA: F13…F24.  ⭐ Scelti cosi' e non a caso:
#    · stanno nella tabella `CL_POSIZIONE` di `src/pagina.html`, quindi il
#      prodotto li spedisce davvero (un `code` che non c'e' NON si spedisce);
#    · **non producono nessuna LETTERA** ⇒ un tasto = un solo messaggio §7.3, e
#      non due percorsi diversi (posizione e lettera) sotto la stessa etichetta;
#    · non sono scorciatoie di GNOME: premerne uno non cambia il desktop sotto
#      la misura, che e' la trappola di `LEZIONI.md` §1.1 vista dal lato
#      dell'input.
#    ⚠ Dodici codici distinti × due versi = 24 combinazioni: bastano perche' la
#      stessa coppia non si ripeta dentro la finestra d'accoppiamento.
TASTI_PROVA = [("F%d" % n, 112 + n) for n in range(13, 25)]


def mappa_tasti(c, tasti=None):
    """⛔ Da `event.code` al codice **evdev** che ESCE SUL FILO — e si MISURA.

    ⚠ La tabella sta in `src/pagina.html`; ricopiarla qui vorrebbe dire avere
      due verita' e credere alla nostra.  ⇒ Si preme un tasto per volta, ben
      distanziato, e si legge che cosa e' uscito.
    ⛔ E l'appaiamento in ORDINE qui e' lecito **solo** perche' i tasti vanno
       uno alla volta a 300 ms di distanza e si PRETENDE il conto esatto: due
       messaggi per tasto, ne' uno di piu' ne' uno di meno.  Se il conto non
       torna, la mappa non si consegna — e senza mappa la tastiera non si
       misura, invece di misurarla male.
    """
    tasti = tasti or TASTI_PROVA
    c.valuta(SVUOTA, attendi=False)
    for nome, vk in tasti:
        for tipo in ("rawKeyDown", "keyUp"):
            spara(c, "Input.dispatchKeyEvent", type=tipo, key=nome, code=nome,
                  windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)
        time.sleep(0.30)
    time.sleep(1.2)
    r = c.valuta("window.__B30.prendi()", attendi=False)
    sp = [x for x in ((r or {}).get("spediti") or [])
          if x.get("tipo") == RCP_POSIZIONE]
    sp.sort(key=lambda x: x["t_filo"])
    atteso = 2 * len(tasti)
    d = {"attesi": atteso, "usciti": len(sp), "mappa": {}}
    if len(sp) != atteso:
        d["perche"] = ("⛔ %d messaggi POSIZIONE_TASTO su %d attesi: la mappa "
                       "NON si consegna, e la tastiera non si misura — meglio "
                       "nessun numero che un numero appaiato male"
                       % (len(sp), atteso))
        return d
    for i, (nome, _) in enumerate(tasti):
        giu, su = sp[2 * i], sp[2 * i + 1]
        if giu.get("codice") != su.get("codice") or not giu.get("premuto") \
                or su.get("premuto"):
            d["perche"] = ("⛔ la coppia giu'/su del tasto «%s» non torna "
                           "(%s/%s): mappa non consegnata" % (nome, giu, su))
            return d
        d["mappa"][nome] = giu["codice"]
    if len(set(d["mappa"].values())) != len(d["mappa"]):
        d["perche"] = ("⛔ due `code` diversi danno lo stesso codice evdev: la "
                       "mappa non e' iniettiva e l'accoppiamento sarebbe "
                       "ambiguo")
        return d
    d["c_e"] = True
    return d


def coordinata(k, vista):
    """⛔ COORDINATE DISTINTE A OGNI SONDA, e non e' un vezzo.

    Due sonde con le stesse coordinate dipingono lo **stesso eco**, e
    l'accoppiamento sceglierebbe il primo fotogramma buono — cioe' un ritardo
    **piu' corto del vero**, ottenuto senza sbagliare nessun conto.  ⇒ 37 e 23
    sono primi con l'ampiezza dei due intervalli: la coppia non si ripete prima
    di 1 400 sonde.
    """
    X = 200 + (k * 37) % max(1, min(1400, vista.tl - 400))
    Y = 140 + (k * 23) % max(1, min(700, vista.ta - 300))
    return X, Y


# ───────────────────────────────────────────────────────────────────────────
# §11.3  IL GIRO — si sintetizza, si ritira A FETTE, si accoppia
# ───────────────────────────────────────────────────────────────────────────
def spara(palco, metodo, **par):
    """⛔⛔ MANDA UN COMANDO CDP **SENZA ASPETTARE LA RISPOSTA**.

    `[M]` 14 agosto 2026, misurato su questo palco: `Input.dispatchMouseEvent`
    **ritorna dopo 5,00 s esatti** — cinque chiamate di fila danno 5,049 · 5,018
    · 5,025 · 5,025 · 5,013.  ⚠ Un numero cosi' stabile non e' carico: e' un
    TETTO (l'attesa dell'ack dell'evento dal renderer).

    ⛔ Aspettarlo vorrebbe dire **un input ogni cinque secondi**, cioe' dodici
       sonde al minuto: il banco misurerebbe se' stesso invece del prodotto, ed
       e' esattamente l'errore che Q9 esiste per trovare negli altri.

    ⭐ E l'evento ARRIVA LO STESSO — a dirlo non e' questa funzione ma
       `eventi_visti`, contato DENTRO la pagina: il denominatore letto dove la
       cosa succede (`LEZIONI.md` §1.9, regola 4).  ⚠ E se un giorno non
       arrivasse, Q0 direbbe «non ho niente da giudicare» invece di dare un
       numero: nessun verde puo' nascere da qui.
    ⚠ Le risposte in ritardo restano sul socket: `Cdp.chiama` salta i messaggi
      con un `id` che non e' il suo, quindi non si mescolano.
    """
    c = getattr(palco, "c", palco)
    c.n += 1
    c.ws.manda(json.dumps({"id": c.n, "method": metodo, "params": par}))


SVUOTA = ("window.__B30 ? (window.__B30.campioni.length = 0,"
          " window.__B30.eventi.length = 0, window.__B30.spediti.length = 0,"
          " window.__B30.costo_lettura_us.length = 0, true) : false")


def ritira(c, dove):
    """⛔ Si ritira DURANTE, non solo alla fine — e questa riga e' nata da un
    difetto misurato (`[M]` 14 agosto 2026, questo banco).

    La prima stesura chiamava `prendi()` dopo venti minuti di pagina accesa: il
    ritiro portava fuori **settantamila** fotogrammi × 288 celle in un JSON
    solo, e il banco restava appeso per minuti senza un errore.  ⚠ Il sintomo
    era «il banco non risponde», che manda a cercare la rete.
    ⇒ Si svuota a mano prima di cominciare (`SVUOTA`, che non porta fuori
      niente) e si ritira ogni secondo.
    """
    r = c.valuta("window.__B30 ? window.__B30.prendi() : null", attendi=False)
    if not isinstance(r, dict):
        return None
    dove["campioni"] += r.get("campioni") or []
    dove["eventi"] += r.get("eventi") or []
    dove["spediti"] += r.get("spediti") or []
    dove["costo_lettura_us"] += r.get("costo_lettura_us") or []
    dove["violazioni"] = r.get("violazioni") or dove.get("violazioni") or []
    dove["ultimo"] = r
    return r


def fetta(c, vista, secondi, passo_s, k0, dove, sintetizza=True):
    """Una fetta di giro: si sintetizza l'input e si ritira, insieme.

    ⭐ Gli eventi si fanno con `Input.dispatchMouseEvent`, cioe' eventi
       **FIDATI** (`isTrusted === true`) che entrano dal gestore del prodotto.
       ⛔ Chiamare la funzione di spedizione della pagina sarebbe il confine
       «comodissimo» travestito: salterebbe tutto il cammino dell'evento dentro
       la pagina, che e' proprio il tratto 1a+1b.
    """
    fine = time.time() + secondi
    prossimo = time.time() + 1.0
    k = k0
    while time.time() < fine:
        if sintetizza and vista.utilizzabile():
            X, Y = coordinata(k, vista)
            cx, cy = vista.a_vista(X, Y)
            try:
                spara(c, "Input.dispatchMouseEvent", type="mouseMoved",
                      x=cx, y=cy, button="none", buttons=0)
            except Exception as e:                   # noqa: BLE001
                dub("⚠ un evento non e' partito: %s" % str(e)[:80])
            k += 1
        time.sleep(passo_s)
        if time.time() >= prossimo:
            ritira(c, dove)
            prossimo = time.time() + 1.0
    return k


def _vuoto():
    return {"campioni": [], "eventi": [], "spediti": [], "costo_lettura_us": [],
            "violazioni": [], "ultimo": None}


def prepara_giro(d, vista, nome, ritorno_ms, andata_ms, vetro_ms=0.0):
    """Da un mucchio grezzo a un giro giudicabile: marche, mappa, sonde."""
    for c in d["campioni"]:
        leggi_due_marche(c)
    eventi = []
    for e in d["eventi"]:
        if e.get("x") is None:
            continue
        X, Y = vista.a_tela(e["x"], e["y"])
        eventi.append(dict(e, x=X, y=Y, x_vista=e["x"], y_vista=e["y"]))
    # ⛔ IL CONTROLLO DELLA MAPPA, e si stampa col DENOMINATORE.
    sopra = {(e["x"], e["y"]) for e in eventi}
    coperti = sum(1 for s in d["spediti"]
                  if s.get("tipo") == RCP_PUNTATORE
                  and (s.get("x"), s.get("y")) in sopra)
    tot = sum(1 for s in d["spediti"] if s.get("tipo") == RCP_PUNTATORE)
    sonde = accoppia(d["campioni"], d["spediti"], eventi)
    buone = [s for s in sonde if s.get("scomodo")]
    # ⭐ La strada di disegno si DEDUCE dai campioni, non dall'indirizzo: la
    #    coda `?tela=2d` e' un'intenzione, il campo `strada` e' un fatto.
    strade = {}
    for c in d["campioni"]:
        s = c.get("strada")
        strade[s] = strade.get(s, 0) + 1
    return {"nome": nome,
            "ritardo_ritorno_ms": ritorno_ms, "ritardo_andata_ms": andata_ms,
            "ritardo_vetro_ms": vetro_ms,
            "strade": strade,
            "campioni": d["campioni"], "spediti": d["spediti"],
            "eventi": eventi, "sonde": sonde,
            "mappa_coperti": coperti, "mappa_denominatore": tot,
            "distribuzione": _d([s["ritardo_scomodo_ms"] for s in buone
                                 if s.get("ritardo_scomodo_ms") is not None]),
            # ⛔ Il confine SBAGLIATO, accanto e mai al posto del vero: Q11 lo
            #    usa per dimostrare che il confine buono non si chiude li'.
            "distribuzione_vecchio": _d([s["ritardo_vecchio_ms"] for s in buone
                                         if s.get("ritardo_vecchio_ms") is not None]),
            # ⭐⭐⭐ LA GRANDEZZA CHE VALE PIU' DI TUTTE, ed e' APPAIATA: quanto
            #     dista il confine vero da quello sbagliato **sulla stessa
            #     sonda, sullo stesso fotogramma**.
            # ⛔ Appaiata e non fra due mediane, e la ragione e' misurata: un
            #    ritardo innestato nel disegno occupa il filo della pagina e
            #    sposta TUTTO il condotto (`[M]` 22 ago: col ritardo al vetro
            #    anche il confine vecchio sale di 6,82 ms).  Sulla differenza
            #    appaiata quello spostamento si elide, perche' colpisce i due
            #    capi allo stesso modo — e resta solo il ritardo innestato.
            "distanza_fra_i_confini": _d(
                [s["ritardo_scomodo_ms"] - s["ritardo_vecchio_ms"] for s in buone
                 if s.get("ritardo_vecchio_ms") is not None
                 and s.get("ritardo_scomodo_ms") is not None]),
            "scomposizione": None}


# ───────────────────────────────────────────────────────────────────────────
# §11.4  IL GIRO VERO
# ───────────────────────────────────────────────────────────────────────────
def giro_vero(a, precondizioni):
    B = b17()
    v = {"banco": "B30", "giro": a.giro, "host": a.host, "porta": a.porta,
         # ⛔ La strada di disegno si DICHIARA nel verbale: due giri con code
         #    diverse non sono lo stesso banco sulla stessa scena (§2.2 punto 3).
         "coda_url": a.coda_url or "",
         "letto_nel_codice": {n: t for n, (_, t) in precondizioni.items()},
         "giri": [], "senza_eco": [], "note": []}
    os.makedirs(a.lavoro, exist_ok=True)

    log("0. LE PORTE, contate — ⛔ 7448 · 7501 · 7561 · 7571 · 7700 non si toccano")
    r = _sshpw("ss -tuln | grep -E ':(7448|7501|7561|7571|7700|76[0-9][0-9]|"
               "77[0-2][0-9])\\b' | sort", silenzioso=True)
    v["porte_prima"] = r.stdout
    for riga in (r.stdout or "").strip().splitlines():
        inf(riga.strip())

    log("1. L'ANCORA DELL'OROLOGIO — ⛔ e NON passa dal ritardatore")
    # ⛔ Due orologi monotoni di due macchine non hanno NESSUNA relazione: senza
    #    l'ancora i tratti 2 e 5 sarebbero numeri che SEMBRANO un ritardo.
    p = ponte_modulo()
    parete = B.scarto_parete_monotono_us()
    inf("CHUWI: parete − monotono = %d us (errore %d us)"
        % (parete["scarto_us"], parete["errore_us"]))
    anc_a = p.orologio_chiedi(a.host, a.ancora, campioni=1200, pausa_s=0.0005)
    if not anc_a.get("c_e"):
        ko(anc_a.get("perche"))
        ko("⛔ senza ancora non si scrive nessun numero")
        deposita({"banco": "B30", "tipo": "MISURA NON ESEGUITA", "giro": a.giro,
                  "perche": "l'ancora dell'orologio non risponde",
                  "codice_uscita": USCITA_NIENTE_DA_GIUDICARE})
        return USCITA_NIENTE_DA_GIUDICARE
    ok("ancora: scarto %d us, errore %d us (giro minimo %d us su %d campioni)"
       % (anc_a["scarto_us"], anc_a["errore_us"], anc_a["giro_minimo_us"],
          anc_a["campioni"]))

    log("2. IL PALCO — Xvfb, Chrome, CDP")
    palco = B.Palco(a.schermo, a.diagnosi, (1500, 1000),
                    os.path.join(a.lavoro, "palco"), gpu=True)
    try:
        inf("Xvfb: " + palco.accendi())
        c = palco
        # ⛔ Il prologo si mette PRIMA di navigare: e' l'unico momento in cui si
        #    puo' ascoltare in fase di cattura e avvolgere `WebTransport` senza
        #    toccare `pagina.html` — cioe' senza misurare la pagina strumentata.
        c.chiama("Page.addScriptToEvaluateOnNewDocument", source=PROLOGO)
        # ⭐⭐ LA CODA DELL'INDIRIZZO — 22 agosto 2026, fase 8.
        #
        # ⛔ Questo banco legge i pixel dal DEPOSITO 2D della pagina
        #    (`window.REMOTIX.schermo.deposito`) e spacca il tratto 6 avvolgendo
        #    `drawImage`.  ⭐ Dal 20 agosto (`DECISIONI.md` §5.4) la strada
        #    normale del prodotto e' `bitmaprenderer` + `createImageBitmap`:
        #    **il deposito non esiste piu' e `drawImage` non viene mai chiamato**.
        #    ⇒ Su quella strada questo banco esce 3 («non ho niente da
        #    giudicare»), e va detto invece che scoperto ogni volta.
        # ⇒ `--coda-url "?tela=2d"` chiede alla pagina la strada 2D, che e'
        #    ESATTAMENTE quella su cui e' stato preso il 139,40 del 14 agosto:
        #    e' l'unico modo di avere un «prima» e un «dopo» confrontabili.
        url = "https://%s:%d/%s" % (a.host, a.porta, a.coda_url or "")
        inf("apro " + url)
        c.chiama("Page.navigate", url=url)
        time.sleep(2.5)
        s = c.valuta(B.STATO, attendi=False)
        if not (isinstance(s, dict) and s.get("pronto")):
            inf("interstiziale del certificato: batto «thisisunsafe»")
            B.batti(c, "thisisunsafe")
            time.sleep(2.5)
        s = B.aspetta(c, B.STATO, 40, lambda x: x.get("pronto"))
        if not (isinstance(s, dict) and s.get("pronto")):
            ko("⛔ la pagina non e' arrivata a `window.REMOTIX`: %s" % str(s)[:300])
            return USCITA_NIENTE_DA_GIUDICARE
        if not c.valuta("!!window.__B30", attendi=False):
            ko("⛔ il PROLOGO non e' entrato: senza, non c'e' nessun `t0`, "
               "nessun byte letto sul filo e nessun pixel")
            return USCITA_NIENTE_DA_GIUDICARE
        ok("pagina pronta, e il prologo del banco e' dentro")

        log("3. Dentro come utente «%s»" % a.utente)
        if not a.parola_file:
            ko("⛔ serve --parola-file (0600).  La parola NON passa da argv")
            return USCITA_USO
        with open(a.parola_file) as f:
            parola = f.read().strip()
        c.valuta(B.ENTRA % (json.dumps(a.utente), json.dumps(parola)),
                 attendi=False)
        del parola
        inf("credenziali inviate (mai da argv)")
        s = B.aspetta(c, B.STATO, 60,
                      lambda x: "sessione" in (x.get("registro") or "").lower()
                      or (x.get("conti") or {}).get("stream", 0) > 0)

        log("4. LA SCENA — ⛔ e va sul monitor CHE SI STA CATTURANDO")
        # ⛔ L'ORDINE E' VINCOLANTE: sessione → SCENA → primo fotogramma.
        #    Aspettare un fotogramma prima della scena e' un'attesa che non
        #    finisce mai — su un desktop fermo Mutter non consegna niente
        #    (`LEZIONI.md` §1.1 travestita da ordine delle operazioni).
        # ⛔⛔ SI FERMA PRIMA DI ACCENDERE, E IL RIMEDIO E' MISURATO — `[M]` 22
        #     agosto 2026, agente A, primo giro perso proprio qui.
        #
        #     `scena-avvia` dice «la scena e' gia' viva» e RIUSA quella del giro
        #     precedente.  ⛔ Ma quella ha perso il fuoco del puntatore (fra un
        #     giro e l'altro la Panoramica di GNOME se l'e' ripreso), e il banco
        #     si ferma sei tentativi dopo con «la scena non prende il fuoco».
        #     ⚠ Il sintomo accusa il compositore; il colpevole e' l'ordine delle
        #       operazioni.
        # ⇒ Il rimedio stava «nella testa di chi lo lancia» (§A.4 punto 4).
        #   Adesso sta nel banco: una scena nuova a ogni giro, sempre.
        _sudo("bash %s scena-ferma" % a.terreno, silenzioso=True, attesa=120)
        time.sleep(1.0)
        acceso = False
        for tentativo in range(8):
            rs = _sudo("bash %s scena-avvia" % a.terreno, silenzioso=True,
                       attesa=240)
            if rs.returncode == 0:
                acceso = True
                inf((rs.stdout or "")[-400:])
                break
            time.sleep(3.0)
        if not acceso:
            ko("⛔ la scena non si e' accesa in 8 tentativi: NON misuro.  ⚠ Un "
               "numero preso senza scena e' uno zero che accusa il prodotto "
               "invece della scena")
            deposita({"banco": "B30", "tipo": "MISURA NON ESEGUITA",
                      "giro": a.giro, "perche": "la scena non si e' accesa",
                      "codice_uscita": USCITA_NIENTE_DA_GIUDICARE})
            return USCITA_NIENTE_DA_GIUDICARE
        s = B.aspetta(c, B.STATO, 60,
                      lambda x: (x.get("conti") or {}).get("dipinti", 0) > 0)
        if not (s and (s.get("conti") or {}).get("dipinti", 0) > 0):
            ko("⛔ nessun fotogramma dipinto CON LA SCENA ACCESA: %s"
               % str((s or {}).get("registro"))[-400:])
            deposita({"banco": "B30", "tipo": "MISURA NON ESEGUITA",
                      "giro": a.giro, "perche": "niente dipinto",
                      "codice_uscita": USCITA_NIENTE_DA_GIUDICARE})
            return USCITA_NIENTE_DA_GIUDICARE
        ok("dipinti: %s" % s["conti"]["dipinti"])

        log("4-bis. ⛔ CHI CATTURA CHI — e la scena su quale monitor sta DAVVERO")
        v["monitor_catturato"] = monitor_del_prodotto(a)
        v["scena"] = scena_uscite(a)
        (ok if v["monitor_catturato"] else ko)(
            "il prodotto cattura il monitor «%s» (letto dal SUO registro)"
            % v["monitor_catturato"])
        (ok if v["scena"].get("uscita_confermata") else ko)(
            "la scena e' su «%s» (chiesta «%s») — ⭐ e a dirlo e' "
            "`wl_surface.enter`, cioe' il COMPOSITORE"
            % (v["scena"].get("uscita_confermata"),
               v["scena"].get("uscita_chiesta")))

        log("4-ter. ⛔⛔ FUORI DALLA PANORAMICA — o si misura UNA MINIATURA")
        # ⛔⛔⛔ IL DIFETTO CHE HA FERMATO IL PRIMO GIRO VERO, E NESSUN DOCUMENTO
        #      LO NOMINAVA — `[M]` 14 agosto 2026, trovato GUARDANDO L'IMMAGINE.
        #
        #      Una sessione GNOME headless appena nata si apre **in Panoramica**
        #      («Type to search», la dock, le miniature).  ⇒ La scena a schermo
        #      intero non e' a schermo intero: e' **una miniatura riscalata a
        #      0,79** dentro l'anteprima, e la Panoramica si tiene il fuoco.
        #      Da fuori si vedeva:
        #        · `eventi_puntatore = 0` sulla scena, con l'iniezione riuscita
        #          (`input_iniettato` avanzava) ⇒ diagnosi «libei non consegna»;
        #        · **0 marche lette su 966**, perche' una marca fatta di celle
        #          da 24 px riscalata a 0,79 non ha piu' nessun CRC.
        #      ⛔ Due sintomi che accusano due imputati diversi, e nessuno dei
        #        due era colpevole.  ⭐ A trovarlo e' stato **guardare
        #        l'immagine**, non leggere un numero: `CODER.md` I8.
        #
        # ⇒ La cura passa DAL CANALE DEL PRODOTTO, non da un `gdbus` di servizio:
        #   si manda ESC come lo manderebbe l'utente, e cosi' la stessa mossa
        #   **misura anche la tastiera** — se la Panoramica si chiude, il
        #   cammino tasto → libei → compositore funziona, e lo si e' visto nei
        #   pixel invece che in un registro.
        v["panoramica"] = {"tentativi": 0, "tolta": False}
        for tentativo in range(6):
            v["panoramica"]["tentativi"] = tentativo + 1
            for _ in range(2):
                for tipo in ("rawKeyDown", "keyUp"):
                    spara(c, "Input.dispatchKeyEvent", type=tipo, key="Escape",
                          code="Escape", windowsVirtualKeyCode=27,
                          nativeVirtualKeyCode=27)
                time.sleep(0.5)
            # ⚠ Il fuoco del PUNTATORE si accende solo quando un movimento gli
            #   passa sopra: senza qualche movimento, «non ho il fuoco» e «non
            #   ho ancora guardato» avrebbero lo stesso aspetto.
            for i in range(8):
                spara(c, "Input.dispatchMouseEvent", type="mouseMoved",
                      x=200 + i * 37, y=200 + i * 23, button="none", buttons=0)
                time.sleep(0.06)
            time.sleep(1.0)
            st, perche = scena_dal_server(a)
            if st and st.get("ho_il_fuoco_puntatore"):
                v["panoramica"]["tolta"] = True
                v["panoramica"]["scena"] = st
                ok("⭐ la Panoramica e' via al tentativo %d: la scena ha il "
                   "fuoco del puntatore (%d eventi) e della tastiera (%d) — "
                   "⭐ e la stessa mossa PROVA il cammino della TASTIERA fino "
                   "al compositore, letta nei pixel"
                   % (tentativo + 1, st["eventi_puntatore"], st["eventi_tasto"]))
                break
            inf("tentativo %d: la scena non ha ancora il fuoco (%s)"
                % (tentativo + 1, perche or json.dumps(st)[:120]))
        if not v["panoramica"]["tolta"]:
            ko("⛔ la scena non prende il fuoco del puntatore: NON misuro.  ⚠ Un "
               "numero preso adesso sarebbe preso su una MINIATURA dentro la "
               "Panoramica di GNOME — scala 0,79, nessun CRC, nessun eco")
            deposita({"banco": "B30", "tipo": "MISURA NON ESEGUITA",
                      "giro": a.giro,
                      "perche": "la Panoramica di GNOME non si e' chiusa: la "
                                "scena resta una miniatura",
                      "codice_uscita": USCITA_NIENTE_DA_GIUDICARE})
            return USCITA_NIENTE_DA_GIUDICARE

        log("5. ⛔ LA MAPPA dalla vista alla tela — si MISURA")
        g = c.valuta(GEOMETRIA_VISTA, attendi=False)
        v["geometria_vista"] = g
        if not (isinstance(g, dict) and g.get("c_e")):
            ko("⛔ %s" % (g or {}).get("perche", "geometria illeggibile"))
            deposita({"banco": "B30", "tipo": "MISURA NON ESEGUITA",
                      "giro": a.giro, "perche": "geometria della vista assente",
                      "codice_uscita": USCITA_NIENTE_DA_GIUDICARE})
            return USCITA_NIENTE_DA_GIUDICARE
        vista = Vista(g)
        inf("vista %gx%g · tela %dx%d · scala %.4f/%.4f · bande %d,%d"
            % (g["rw"], g["rh"], vista.tl, vista.ta, vista.sx, vista.sy,
               vista.bx0, vista.by0))
        if not vista.utilizzabile():
            ko("⛔ la mappa non e' calcolabile: %s" % json.dumps(g)[:200])
            return USCITA_NIENTE_DA_GIUDICARE

        log("5-ter. ⛔⛔ LO SCORRIMENTO DELLA MARCA — misurato sui PIXEL VERI")
        # ⛔⛔ SENZA QUESTO PASSO NON SI LEGGE UNA MARCA — `[M]` 14 agosto 2026,
        #     primo giro vero: **0 marche lette su 966**, con la catena, la
        #     scena e il lettore tutti perfettamente funzionanti.
        #
        #     `leggi_celle` gira con `ricerca=0` **apposta**: le 144 celle sono
        #     gia' campionate, e ricercare lo scorrimento su un'immagine
        #     sintetica non vorrebbe dire niente.  ⇒ Lo scorrimento vero si
        #     misura UNA VOLTA, sui pixel veri, e si passa al campionatore.
        # ⭐ E la stessa regione cruda serve al controllo del campionamento: le
        #    celle di JavaScript contro quelle di numpy.  Se differiscono, il
        #    lettore certificato sta leggendo un'immagine che il banco non ha
        #    campionato come lui, e ogni «marca letta» sarebbe un caso.
        m = marca_modulo()
        v["scorrimento"] = [0, 0]
        v["campionamento"] = []
        c.valuta("window.__B30.crudi_voluti = 4, window.__B30.crudi = [], true",
                 attendi=False)
        time.sleep(2.0)
        rc = c.valuta("window.__B30.prendi()", attendi=False)
        for cr in ((rc or {}).get("crudi") or []):
            grezzo = base64.b64decode(cr["b64"])
            np = m.np_o_muori("04-b30: lo scorrimento sui pixel veri")
            img = np.frombuffer(grezzo, dtype=np.uint8).reshape(cr["a"], cr["l"], 3)
            vero = m.leggi_marca(img, ricerca=2)
            y = (img[:, :, :3].astype(np.float64) @ m.PESI_LUMA) / 255.0
            celle_np = m._celle(y, m.GEOMETRIA, 0, 0) * 255.0
            scarto = max(abs(float(x) - float(z))
                         for x, z in zip(celle_np, cr["celle"]))
            v["campionamento"].append(
                {"regione": [cr.get("ox"), cr.get("oy")],
                 "letta": vero.get("c_e"), "perche": vero.get("perche"),
                 "contrasto": vero.get("contrasto"),
                 "scorrimento_provato": vero.get("scorrimento_provato"),
                 "scarto_celle_su_255": round(scarto, 4)})
            if vero.get("c_e") and cr.get("oy") == 0:
                v["scorrimento"] = vero["scorrimento_provato"]
        for x in v["campionamento"]:
            (ok if x["letta"] else ko)(
                "regione %s: marca %s · scorrimento %s · contrasto %s · "
                "JS contro numpy %.3f su 255%s"
                % (x["regione"], "LETTA" if x["letta"] else "NO",
                   x["scorrimento_provato"], x["contrasto"],
                   x["scarto_celle_su_255"],
                   "" if x["letta"] else " — %s" % str(x["perche"])[:120]))
        c.valuta("window.__B30.crudi_voluti = 0, window.__B30.scorrimento = %s,"
                 " true" % json.dumps(v["scorrimento"]), attendi=False)
        inf("scorrimento in vigore per il campionamento: %s" % v["scorrimento"])

        log("5-quater. ⛔⛔⛔ IL CARICO DELLE DUE MACCHINE — e senza questo il "
            "numero non vale")
        v["carico_prima"] = carico_della_macchina(a)
        v["macchina_carica_prima"] = stampa_carico(v["carico_prima"], "PRIMA")

        log("5-bis. ⛔ IL PALCO, dai due capi — si DICHIARA prima del numero")
        v["palco_prima"] = B.palco_dichiarato(palco, a, a.registro_prodotto)
        # ⛔ E il palco del SERVER si rilegge dal MIO albero: quello di `03-b17`
        #    fa `pgrep -x remotix` su tutta la macchina, e in questo momento di
        #    `remotix` ne girano parecchi — quello dell'utente sulla 7700 e
        #    quelli degli altri nove anelli.  ⇒ L'unione dei loro descrittori
        #    direbbe «hardware» anche se il MIO codificatore fosse in software.
        rq = _sudo("bash %s palco" % a.terreno, silenzioso=True)
        for riga in reversed((rq.stdout or "").splitlines()):
            if riga.strip().startswith("{"):
                try:
                    v["palco_prima"]["server_mio"] = json.loads(riga.strip())
                except ValueError:
                    pass
                break
        B.stampa_palco(v["palco_prima"])
        inf("⭐ il palco del MIO server (solo i miei processi): %s"
            % json.dumps(v["palco_prima"].get("server_mio")))
        # ⛔⛔ SU XVFB O SUL DESKTOP VERO?  Non si suppone: lo dice `xlsclients`.
        #     Se il browser NON e' sull'Xvfb, il pezzo cieco in USCITA (16-40 ms)
        #     ESISTE, e va sommato.  ⚠ E se non si e' potuto guardare si sceglie
        #     la strada SCOMODA — cioe' si somma lo stesso.
        cl = (v["palco_prima"].get("chuwi") or {}).get("clienti_sull_xvfb")
        v["clienti_sull_xvfb"] = cl
        v["su_xvfb"] = bool(cl)
        inf("clienti attaccati a %s: %s  ⇒  su_xvfb = %s  (⛔ `None` non e' "
            "«zero»: si sceglie comunque la strada scomoda)"
            % (a.schermo, cl, v["su_xvfb"]))

        log("6. ⛔ I TRE GIRI, INTRECCIATI — base · ritardo al RITORNO · "
            "ritardo all'ANDATA")
        # ⛔⭐ I GIRI SI INTRECCIANO, e non e' un vezzo: a blocchi il ritardo
        #     iniettato si confonde con IL TEMPO (la macchina, il codificatore e
        #     la cadenza non stanno fermi per due minuti), e la salita misurata
        #     ne porta dentro la deriva.  Fette corte, alternate, tante volte:
        #     cosi' la deriva colpisce tutti i valori allo stesso modo.
        condizioni = [("base", 0.0, 0.0, 0.0),
                      ("ritorno", float(a.ritardo_ritorno), 0.0, 0.0),
                      ("andata", 0.0, float(a.ritardo_andata), 0.0)]
        # ⭐⭐ LA QUARTA CONDIZIONE — il controllo positivo del confine (Q11).
        # ⛔ Sta QUI dentro, intrecciata con le altre, e non in un giro a parte:
        #    fra due giri ci si mette in mezzo la deriva, il palco e la contesa,
        #    e la salita misurata ne porterebbe dentro un pezzo che non e' il
        #    ritardo innestato (`LEZIONI.md` §1.13).
        if a.ritardo_vetro > 0:
            condizioni.append(("vetro", 0.0, 0.0, float(a.ritardo_vetro)))
        mucchio = {n: _vuoto() for n, _, _, _ in condizioni}
        mani = max(2, a.mani)
        durata = max(4.0, a.secondi / mani)
        k = 0
        inf("%d mani da %.1f s per ciascuna delle %d condizioni "
            "(≈ %.0f s in tutto), un input ogni %.0f ms"
            % (mani, durata, len(condizioni), mani * durata * len(condizioni),
               a.passo_ms))
        for mano in range(mani):
            for nome, rr, ra, rv in condizioni:
                if not metti_ritardo(a, rr, ra, "%s-m%d-%s" % (a.giro, mano, nome)):
                    dub("⚠ non ho potuto scrivere il comando del ponte (%s)" % nome)
                # ⭐⭐ Il ritardo AL VETRO non passa dal ponte: sta dentro la
                #     pagina, fra «il fotogramma e' pronto» e il trasferimento.
                #     ⛔ Se non si riesce a scriverlo, NON si misura al buio.
                sc = c.valuta("window.__B30 ? (window.__B30.ritardo_vetro_ms "
                              "= %g, window.__B30.ritardo_vetro_ms) : null" % rv,
                              attendi=False)
                if sc != rv:
                    dub("⚠ il ritardo al vetro non e' stato scritto (chiesto "
                        "%g, letto %s): la condizione «%s» NON e' quella che "
                        "dice di essere" % (rv, sc, nome))
                # ⛔ Si BUTTA l'assestamento: i fotogrammi in volo subito dopo un
                #    cambio di N portano ancora il N di prima.
                time.sleep(1.5)
                c.valuta(SVUOTA, attendi=False)
                k = fetta(c, vista, durata, a.passo_ms / 1000.0, k,
                          mucchio[nome])
                # ⚠ La coda: l'ultimo input deve poter arrivare al vetro prima
                #   che si cambi condizione, o le sue sonde non chiudono mai.
                time.sleep(1.2)
                ritira(c, mucchio[nome])
            inf("mano %d/%d fatta" % (mano + 1, mani))
        metti_ritardo(a, 0.0, 0.0, a.giro)
        c.valuta("window.__B30 ? (window.__B30.ritardo_vetro_ms = 0, true) "
                 ": false", attendi=False)
        # ⛔ Il ponte si legge MENTRE ha ritardato, non a zero: uno scarto
        #    misurato a ritardo zero non dice niente su come consegna quando
        #    ritarda.  ⚠ Qui la lettura e' l'ultima scritta dal ponte.
        rp = _sshpw("cat %s" % a.verbale_ponte, silenzioso=True)
        for riga in (rp.stdout or "").splitlines():
            if riga.strip().startswith("{"):
                try:
                    v["ponte"] = json.loads(riga.strip())
                except ValueError:
                    pass
                break

        log("7. LO SCARTO FRA I DUE OROLOGI — l'ancora, riletta")
        anc_b = p.orologio_chiedi(a.host, a.ancora, campioni=1200, pausa_s=0.0005)
        v["ancora_apertura"], v["ancora_chiusura"] = anc_a, anc_b
        v["parete"] = parete
        if anc_b.get("c_e"):
            v["deriva_ppm"] = p.deriva_ppm(anc_a, anc_b)
            scarto_ancora = (anc_a["scarto_us"] + anc_b["scarto_us"]) // 2
            v["errore_orologio_us"] = (parete["errore_us"]
                                       + max(anc_a["errore_us"], anc_b["errore_us"]))
        else:
            dub("⚠ l'ancora di chiusura non ha risposto: la deriva resta `[?]`")
            scarto_ancora = anc_a["scarto_us"]
            v["errore_orologio_us"] = parete["errore_us"] + anc_a["errore_us"]
        # ⛔⛔ IL VERSO.  `scarto_ancora_us` e' quanto va SOTTRATTO al monotono
        #     del SERVER per portarlo sull'orologio della pagina:
        #        server_us = pagina_ms*1000 + origine_us − parete + ancora
        #     ⚠ Sbagliare il verso produce un numero che SEMBRA un ritardo:
        #       grande, stabile e falso.
        ultimo = (mucchio["base"].get("ultimo") or {})
        origine_ms = ultimo.get("t_origine") or 0
        v["origine_pagina_ms"] = origine_ms
        v["scarto_ancora_us"] = (int(origine_ms * 1000) - parete["scarto_us"]
                                 + scarto_ancora)
        inf("scarto d'apertura %d us · di chiusura %s · deriva %s ppm · "
            "scarto_ancora_us %d"
            % (anc_a["scarto_us"], anc_b.get("scarto_us"),
               round(v.get("deriva_ppm") or 0, 2), v["scarto_ancora_us"]))

        log("8. Q9 — QUANTO COSTA IL BANCO, a fette alternate")
        senza, con = _vuoto(), _vuoto()
        for _ in range(2):
            for leggi, dove in ((False, senza), (True, con)):
                c.valuta("window.__B30.leggi = %s, true"
                         % ("true" if leggi else "false"), attendi=False)
                c.valuta(SVUOTA, attendi=False)
                fetta(c, vista, 5.0, a.passo_ms / 1000.0, k, dove)
                ritira(c, dove)
        c.valuta("window.__B30.leggi = true, true", attendi=False)

        def ritmo(d):
            cc = d["campioni"]
            if len(cc) < 5:
                return None
            iv = sorted(b["t1"] - x["t1"] for x, b in zip(cc, cc[1:])
                        if 0 < b["t1"] - x["t1"] < 500)
            return round(1000.0 / iv[len(iv) // 2], 2) if iv else None
        v["fps_senza_lettura"] = ritmo(senza)
        v["fps_con_lettura"] = ritmo(con)
        inf("ritmo senza la lettura: %s · con la lettura: %s  (%d e %d "
            "fotogrammi)" % (v["fps_senza_lettura"], v["fps_con_lettura"],
                             len(senza["campioni"]), len(con["campioni"])))

        log("9. ⛔⛔ Q4(a) — IL RILEVATORE DAVANTI A QUEL CHE NON C'E'")
        # ⭐ Si sposta la FINESTRA DI LETTURA dell'eco su un'altra parte dello
        #    STESSO fotogramma: pixel veri, stesso desktop, stessa catena — e li'
        #    la marca dell'eco NON C'E'.  Se il lettore dicesse «si'» anche li',
        #    direbbe si' a qualunque cosa, e ogni ritardo di questo banco
        #    sarebbe un numero inventato.
        #    ⛔ Spegnere la scena NON e' la strada: senza scena Mutter non
        #       consegna un fotogramma, e al lettore non si mostra niente.
        fuori = _vuoto()
        c.valuta("window.__B30.finestra_eco = %s, true"
                 % json.dumps([a.finestra_x, a.finestra_y]), attendi=False)
        c.valuta(SVUOTA, attendi=False)
        fetta(c, vista, 8.0, a.passo_ms / 1000.0, k, fuori)
        ritira(c, fuori)
        c.valuta("window.__B30.finestra_eco = [0, %d], true" % 240, attendi=False)
        for x in fuori["campioni"]:
            leggi_due_marche(x)
        v["senza_eco"] = [x for x in fuori["campioni"] if x.get("visto_eco")]
        v["senza_eco_finestra"] = [a.finestra_x, a.finestra_y]
        falsi = [x for x in v["senza_eco"] if x.get("eco_marca", {}).get("c_e")]
        (ok if (v["senza_eco"] and not falsi) else ko)(
            "Q4(a): %d fotogrammi VERI guardati in (%d,%d), dove la marca "
            "dell'eco non c'e' → %d falsi positivi"
            % (len(v["senza_eco"]), a.finestra_x, a.finestra_y, len(falsi)))

        log("9-bis. ⭐⭐ LA TASTIERA, MISURATA A PARTE — la tesi 3 del mandato")
        # ⛔ *«La tastiera e il mouse hanno lo stesso ritardo»* non e' detto, e
        #    mediarli darebbe un numero che l'utente sente in due modi diversi:
        #    il mouse muove un puntatore DISEGNATO DALLA PAGINA (che si vede
        #    subito, senza rete), la tastiera fa tutto il giro.
        v["mappa_tasti"] = mappa_tasti(c)
        tastiera = _vuoto()
        if not v["mappa_tasti"].get("c_e"):
            ko("⛔ %s" % v["mappa_tasti"].get("perche"))
            inf("⚠ La tastiera NON si misura in questo giro, e si dice: un "
                "numero appaiato male sarebbe peggio di nessun numero.")
        else:
            ok("mappa `event.code` → evdev, MISURATA: %s"
               % json.dumps(v["mappa_tasti"]["mappa"]))
            c.valuta(SVUOTA, attendi=False)
            fine = time.time() + max(10.0, a.secondi / 2.0)
            prossimo = time.time() + 1.0
            i = 0
            while time.time() < fine:
                nome, vk = TASTI_PROVA[i % len(TASTI_PROVA)]
                i += 1
                # ⛔⛔ IL «GIU'» E IL «SU» SI SEPARANO, e non e' una finezza.
                #
                #     Mandandoli insieme, l'eco del «giu'» viene sovrascritto da
                #     quello del «su» **prima che la scena ridisegni** (60 Hz =
                #     16,7 ms): meta' delle sonde non puo' chiudere per
                #     costruzione, e il banco misurerebbe solo quel che
                #     sopravvive — cioe' un campione scelto dal difetto.
                #     `[M]` 14 agosto: 27 sonde chiuse su 584.
                #  ⇒ Ogni stato vive almeno un intervallo di quadro.
                for tipo in ("rawKeyDown", "keyUp"):
                    spara(c, "Input.dispatchKeyEvent", type=tipo, key=nome,
                          code=nome, windowsVirtualKeyCode=vk,
                          nativeVirtualKeyCode=vk)
                    time.sleep(a.passo_ms / 1000.0)
                if time.time() >= prossimo:
                    ritira(c, tastiera)
                    prossimo = time.time() + 1.0
            time.sleep(1.2)
            ritira(c, tastiera)
            inf("tasti: %d messaggi sul filo, %d fotogrammi guardati"
                % (len([x for x in tastiera["spediti"]
                        if x.get("tipo") == RCP_POSIZIONE]),
                   len(tastiera["campioni"])))
        v["_tastiera_grezza"] = tastiera

        log("10. LO STATO DELLA SCENA — ⛔ l'input e' ARRIVATO AL DESKTOP?")
        scena_in, perche = scena_dal_server(a)
        v["scena_input"] = scena_in
        if scena_in is None:
            ko(perche)
        else:
            ok("la scena ha ricevuto: puntatore %d · pulsante %d · rotella %d · "
               "tasto %d  (fuoco puntatore %s, seat %s)"
               % (scena_in["eventi_puntatore"], scena_in["eventi_pulsante"],
                  scena_in["eventi_rotella"], scena_in["eventi_tasto"],
                  scena_in["ho_il_fuoco_puntatore"], scena_in["seat_visto"]))

        log("11-bis. ⛔⛔ IL CARICO, RILETTO — un carico che cambia a meta' giro "
            "fa uscire un numero che sembra buono")
        v["carico_dopo"] = carico_della_macchina(a)
        v["macchina_carica_dopo"] = stampa_carico(v["carico_dopo"], "DOPO")

        log("11. IL PALCO, RILETTO — un palco che cambia a meta' giro fa uscire "
            "un numero che sembra buono")
        v["palco_dopo"] = B.palco_dichiarato(palco, a, a.registro_prodotto)
        v["palco_regge"] = B.confronta_palco(v.get("palco_prima"), v["palco_dopo"])
        (ok if v["palco_regge"]["regge"] else ko)(
            "il palco e' lo stesso ai due estremi" if v["palco_regge"]["regge"]
            else "⛔ IL PALCO E' CAMBIATO DURANTE LA MISURA: "
                 + " · ".join(v["palco_regge"]["perche"]))
        # ⭐⭐ IL CONTROLLO INCROCIATO — il PRODOTTO contro il BANCO sui tratti
        #    9 e 10.  ⛔ Due lettori indipendenti della stessa grandezza: se
        #    divergono, uno dei due sbaglia, e finche' non li si mette accanto
        #    non lo sa nessuno.
        v["pagina_disegno"] = (mucchio["base"].get("ultimo") or {}).get(
            "pagina_disegno")
        v["strada_dichiarata_dal_prologo"] = (
            mucchio["base"].get("ultimo") or {}).get("strada")
        v["grana"] = (mucchio["base"].get("ultimo") or {}).get("grana")
        v["isolata"] = (mucchio["base"].get("ultimo") or {}).get("isolata")
        v["costo_lettura_us"] = mucchio["base"]["costo_lettura_us"]
    finally:
        palco.spegni()

    log("12. LE SONDE — si accoppia e si scompone")
    for nome, rr, ra, rv in condizioni:
        g = prepara_giro(mucchio[nome], vista, nome, rr, ra, rv)
        g["scomposizione"] = scomponi(g["sonde"], v["scarto_ancora_us"])
        v["giri"].append(g)
        chiuse = sum(1 for s in g["sonde"] if s.get("scomodo"))
        (ok if chiuse else ko)(
            "%-8s ritorno %+5.1f · andata %+5.1f · vetro %+5.1f  ⇒  %4d "
            "spediti, %4d sonde, %4d CHIUSE, mediana %s ms  (⛔ confine vecchio "
            "%s ms · strade %s · mappa: %d/%d)"
            % (nome, rr, ra, rv, len(g["spediti"]), len(g["sonde"]), chiuse,
               g["distribuzione"].get("mediana"),
               (g.get("distribuzione_vecchio") or {}).get("mediana"),
               json.dumps(g.get("strade"), ensure_ascii=False),
               g["mappa_coperti"], g["mappa_denominatore"]))

    log("12-ter. ⭐⭐ IL CONTROLLO INCROCIATO — il PRODOTTO contro il BANCO")
    # ⛔ `src/pagina.html` misura da se' le stesse due grandezze dei tratti 9 e
    #    10.  Se il banco e il prodotto dicono numeri diversi, uno dei due
    #    sbaglia — e finche' non li si mette accanto non lo sa nessuno.
    pd = v.get("pagina_disegno") or {}
    base_g = next((x for x in v["giri"] if not x.get("ritardo_ritorno_ms")
                   and not x.get("ritardo_andata_ms")
                   and not x.get("ritardo_vetro_ms")), None) or {}
    sc_b = base_g.get("scomposizione") or {}

    def _tratto(pfx):
        for k, x in sc_b.items():
            if k.startswith(pfx) and isinstance(x, dict) and "mediana" in x:
                return x["mediana"]

    v["incrocio"] = {}
    # ── Il tratto 9: un CONFRONTO vero, e i due lettori sono indipendenti ──
    p9 = _d(pd.get("bmp_ms") or [])
    b9 = _tratto("9 ")
    if not p9.get("n") or b9 is None:
        dub("⚠ tratto 9: NON CONFRONTATO (prodotto n=%s, banco %s).  ⛔ Non e' "
            "«sono d'accordo»" % (p9.get("n"), b9))
        v["incrocio"]["bmp_ms"] = {"prodotto": p9, "banco": b9, "esito": None}
    else:
        s9 = b9 - p9["mediana"]
        # ⚠ Il prodotto tiene 200 campioni recenti e il banco tutto il giro: e'
        #   un confronto fra due CAMPIONI della stessa grandezza, non fra due
        #   liste identiche, e la soglia lo riflette.
        d_ok = abs(s9) <= max(1.0, 0.30 * p9["mediana"])
        v["incrocio"]["bmp_ms"] = {"prodotto": p9, "banco": b9,
                                   "scarto_ms": round(s9, 3), "esito": d_ok}
        (ok if d_ok else ko)(
            "⭐⭐ tratto 9 (l'attesa: `createImageBitmap`): il PRODOTTO dice "
            "%.3f ms (n=%d), il BANCO %.3f  ⇒ scarto %+.3f ms — e sono due "
            "lettori scritti da due persone diverse"
            % (p9["mediana"], p9["n"], b9, s9))

    # ── ⛔⛔ Il tratto 10 NON si confronta, e la ragione e' MISURATA ────────
    #
    # `vetro_ms` del prodotto cronometra `this.bm.transferFromImageBitmap(bmp)`.
    # ⛔ Ma il banco AVVOLGE proprio quel metodo, e dentro l'involucro ci legge
    #    i pixel.  ⇒ Il cronometro del prodotto **contiene il banco**, e i due
    #    numeri non misurano la stessa cosa: confrontarli darebbe un rosso che
    #    non accusa nessuno.
    # ⭐ Quel che invece dice, ed e' una misura che nessun altro sa dare: la
    #    DIFFERENZA fra i due e' **quanto pesa il banco**, letta dal prodotto —
    #    cioe' un terzo parere su `costo_lettura_us`, preso da fuori.
    # ⛔⛔ E porta con se' un AVVERTIMENTO per chiunque altro: finche' questo
    #     banco e' attaccato, il campo `vetro` del blocco diagnostico della
    #     pagina **non e' il prodotto**.
    p10 = _d(pd.get("vetro_ms") or [])
    b10 = _tratto("10 ")
    costo = _d([x * 0.001 for x in (v.get("costo_lettura_us") or [])])
    v["incrocio"]["vetro_ms"] = {
        "prodotto": p10, "banco": b10,
        "differenza_ms": (round(p10["mediana"] - b10, 3)
                          if p10.get("n") and b10 is not None else None),
        "costo_della_lettura_secondo_Q9_ms": costo.get("mediana"),
        "esito": None,
        "⛔": "NON e' un confronto: il cronometro del prodotto AVVOLGE il banco "
             "(l'involucro di `transferFromImageBitmap` legge i pixel dentro la "
             "parentesi che il prodotto cronometra).  ⇒ La differenza e' il "
             "COSTO DEL BANCO letto dal prodotto, e va accostata a Q9",
        "⛔⛔ avvertimento": "finche' questo banco e' attaccato, il campo "
                            "`vetro` del blocco diagnostico di `pagina.html` "
                            "NON e' il prodotto: e' il prodotto piu' il banco"}
    if p10.get("n") and b10 is not None:
        dub("⚠ tratto 10: il prodotto dice %.3f ms e il banco %.3f — ⛔ e NON e' "
            "un disaccordo: il cronometro del prodotto AVVOLGE il banco.  ⭐ La "
            "differenza (%.3f) e' il costo del banco letto DAL PRODOTTO, e Q9 "
            "dice %s" % (p10["mediana"], b10, p10["mediana"] - b10,
                         costo.get("mediana")))

    log("12-bis. ⭐⭐ LA TASTIERA — lo stesso metro, la stessa scena, l'altro tasto")
    # ⛔ Stesso strumento, stessa scena, stesso giro: i due numeri si possono
    #    confrontare fra loro.  ⚠ Fra due GIRI diversi non si potrebbe.
    tg = v.pop("_tastiera_grezza", None) or _vuoto()
    v["tastiera"] = {"mappa": v.get("mappa_tasti")}
    if v.get("mappa_tasti", {}).get("c_e") and tg["campioni"]:
        for x in tg["campioni"]:
            leggi_due_marche(x)
        ev = [e for e in tg["eventi"] if e.get("codice")]
        st = accoppia_tasti(tg["campioni"], tg["spediti"], ev,
                            v["mappa_tasti"]["mappa"])
        chiuse = [s for s in st if s.get("scomodo")]
        v["tastiera"]["sonde"] = st
        v["tastiera"]["distribuzione"] = _d(
            [s["ritardo_scomodo_ms"] for s in chiuse
             if s.get("ritardo_scomodo_ms") is not None])
        v["tastiera"]["scomposizione"] = scomponi(st, v["scarto_ancora_us"])
        (ok if chiuse else ko)(
            "TASTIERA: %d messaggi, %d sonde, %d CHIUSE, mediana %s ms"
            % (len([x for x in tg["spediti"] if x.get("tipo") == RCP_POSIZIONE]),
               len(st), len(chiuse),
               v["tastiera"]["distribuzione"].get("mediana")))
    else:
        dub("⚠ la tastiera non e' stata misurata in questo giro: %s"
            % (v.get("mappa_tasti", {}).get("perche") or "nessun campione"))

    r2 = _sshpw("ss -tuln | grep -E ':(7448|7501|7561|7571|7700|76[0-9][0-9]|"
                "77[0-2][0-9])\\b' | sort", silenzioso=True)
    v["porte_dopo"] = r2.stdout
    if v["porte_dopo"] != v["porte_prima"]:
        dub("⚠ le porte sono cambiate durante la misura")

    dove = os.path.join(a.lavoro, "verbale-%s.json" % a.giro)
    with open(dove, "w") as f:
        json.dump(v, f, ensure_ascii=False)
    inf("verbale: %s (%d byte)" % (dove, os.path.getsize(dove)))

    g = stampa_verdetto(v)
    base = next((x for x in v["giri"] if not x.get("ritardo_ritorno_ms")
                 and not x.get("ritardo_andata_ms")
                 and not x.get("ritardo_vetro_ms")), None) or {}
    d = _d([s["ritardo_scomodo_ms"] for s in base.get("sonde", [])
            if s.get("ritardo_scomodo_ms") is not None])
    deposita({"banco": "B30", "tipo": "MISURA", "giro": a.giro,
              "host": a.host, "porta": a.porta, "utente": a.utente,
              # ⛔⛔ LA STRADA DI DISEGNO NELLA RIGA DEPOSITATA — difetto
              #     dichiarato dall'agente A e curato qui: chi rilegge
              #     `04-b30-esiti.jsonl` DEVE poter sapere su quale strada e'
              #     stato preso un numero, o confronterebbe due mondi diversi
              #     credendoli uno.  ⭐ `coda_url` e' l'intenzione, `strade` e'
              #     il FATTO (contato sui campioni).
              "coda_url": v.get("coda_url", ""),
              "strade": base.get("strade"),
              "controlli": {k: bool(g[k].get("esito")) for k in TUTTI},
              "distribuzione_ms": d,
              # ⛔ Il confine SBAGLIATO, accanto e mai al posto del vero
              "distribuzione_vecchio_ms": base.get("distribuzione_vecchio"),
              "distanza_fra_i_confini_ms": base.get("distanza_fra_i_confini"),
              # ⭐⭐ il PRODOTTO contro il BANCO sugli stessi due tratti
              "incrocio_prodotto_banco": v.get("incrocio"),
              "Q11": g["Q11"],
              "verdetto": verdetto(d, v.get("su_xvfb", False)),
              "scomposizione": scomponi(base.get("sonde", []),
                                        v.get("scarto_ancora_us", 0)),
              "Q5": g["Q5"], "Q6": g["Q6"], "Q7": g["Q7"], "Q8": g["Q8"],
              "scarto_ancora_us": v.get("scarto_ancora_us"),
              "errore_orologio_us": v.get("errore_orologio_us"),
              "deriva_ppm": v.get("deriva_ppm"),
              "monitor_catturato": v.get("monitor_catturato"),
              "scena": v.get("scena"), "scena_input": v.get("scena_input"),
              "clienti_sull_xvfb": v.get("clienti_sull_xvfb"),
              "su_xvfb": v.get("su_xvfb"),
              "panoramica": v.get("panoramica"),
              "scorrimento": v.get("scorrimento"),
              "campionamento": v.get("campionamento"),
              # ⭐ La TASTIERA, accanto al mouse e non mediata con lui
              "tastiera": {
                  "distribuzione_ms": (v.get("tastiera") or {}).get("distribuzione"),
                  "scomposizione": (v.get("tastiera") or {}).get("scomposizione"),
                  "mappa": (v.get("mappa_tasti") or {}).get("mappa"),
              },
              # ⛔⛔⛔ IL CARICO ACCANTO AL NUMERO — 22 agosto 2026.  Senza, un
              #     anello misurato con cinque Xvfb sopra e' indistinguibile da
              #     uno misurato sul prodotto, e `[M]` fra i due ci sono da 15 a
              #     45 volte sullo stesso tratto.
              "carico_prima": v.get("carico_prima"),
              "carico_dopo": v.get("carico_dopo"),
              "⛔ macchina carica": bool(v.get("macchina_carica_prima")
                                        or v.get("macchina_carica_dopo")),
              "palco": v.get("palco_prima"), "palco_regge": v.get("palco_regge"),
              "ponte": v.get("ponte"), "verbale": dove,
              "codice_uscita": codice_uscita(g)})
    return codice_uscita(g)


def misura(a):
    """⛔ LA MISURA VERA.

    ⭐ E la sequenza e' vincolante — la stessa di `03-b17`, piu' due passi:

      1. si accende il palco (Xvfb + Chrome + CDP) e si VERIFICA dall'altro capo
         chi e' attaccato a quello schermo (`LEZIONI.md` §2.0);
      2. si accende la scena SUL MONITOR CHE SI CATTURA, e lo si verifica con
         `wl_surface.enter` — non con la riga di comando;
      3. ⭐ si sintetizzano gli eventi con `Input.dispatchMouseEvent`, cioe'
         eventi FIDATI che passano per il gestore del prodotto;
      4. si raccoglie, si accoppia, si scompone;
      5. si rifa' ai ritardi noti, su TUTT'E DUE i rami.
    """
    log("⛔ LA MISURA — prima si guarda se c'e' qualcosa da misurare")
    # ⛔⛔ NON SI ASSERISCE UN FATTO: SI GUARDA.
    #
    #     La prima stesura di questa funzione diceva «`src/input.c` e' un
    #     abbozzo», e nel giro di un'ora era falso — l'anello A4 l'aveva scritto
    #     (284 byte → 35 368).  ⚠ Un banco che porta dentro una data invece di
    #     una lettura invecchia da solo, ed e' `LEZIONI.md` §2.3-quater: una
    #     ragione non misurata dentro una conclusione.
    # ⛔⛔ E GLI AGHI NON POSSONO ESSERE NUMERI DI TIPO — `[M]` 14 agosto 2026,
    #     questa stessa funzione, un quarto d'ora dopo essere stata scritta.
    #
    #     La prima stesura cercava `0x0101` in `pagina.html` e ne trovava
    #     **cinque**, quindi diceva ⭐OK⭐ «il client manda l'input».  ⛔ Erano
    #     tutt'e cinque dentro i COMMENTI: il client non manda niente.
    #     ⇒ È `LEZIONI.md` §1.9 nella sua forma piu' banale e piu' cara — un
    #       verde prodotto dallo strumento — e l'ho ripagata **dentro il banco
    #       che esiste per non ripagarla**.
    #
    # ⭐ La cura: gli aghi sono cose che **non possono stare in un commento**
    #    perche' sono chiamate di API.  ⚠ E resta una PRECONDIZIONE, non una
    #    prova: la prova e' sul filo, e la fa Q0 al momento della misura.
    trovato = {}
    for nome, percorso, aghi in (
            ("il CLIENT SCRIVE sul filo", os.path.join(RADICE, "src/pagina.html"),
             ("createUnidirectionalStream", "createBidirectionalStream",
              "datagrams.writable")),
            ("il SERVER decodifica l'input", os.path.join(RADICE, "src/rcp.c"),
             ("T_PUNTATORE",)),
            ("il SERVER inietta l'input", os.path.join(RADICE, "src/input.c"),
             ("ei_device_pointer_motion_absolute", "ei_device_scroll")),
            # ⛔⛔ E QUESTA RIGA E' STATA CORRETTA A MISURA GIA' PRONTA — `[M]`
            #     14 agosto 2026, sera, anello O2.
            #
            #     Diceva: cerca `.input_puntatore` in **`src/figlio.c`**, e ne
            #     trovava ZERO ⇒ «NON HO NIENTE DA GIUDICARE», uscita 3.  ⛔ Era
            #     FALSO: la catena era cucita e funzionava (20 messaggi §7.3 sul
            #     filo, l'eco nei pixel, il campo `input` dei 28 byte pieno).
            #     I ganci si attaccano in **`src/webtransport.c`**
            #     (`g.input_puntatore = gancio_input_puntatore`), perche' il
            #     canale sta nel PADRE; il figlio, dall'altra parte del confine
            #     di processo, CHIAMA `input_puntatore()` su `MSG_INPUT`.
            #
            #     ⭐ E' la stessa lezione della mattina presa dall'altro verso:
            #     allora questo controllo aveva dato un falso VERDE (cinque
            #     `0x0101` dentro i commenti), adesso un falso ROSSO — ⛔ e un
            #     falso rosso su una precondizione **spegne la misura** senza
            #     che nessuno guardi il prodotto.  ⇒ Si guardano tutt'e due i
            #     lati del confine, e ciascuno col nome del suo file.
            ("i GANCI sono ATTACCATI (nel padre)",
             os.path.join(RADICE, "src/webtransport.c"),
             ("g.input_puntatore =", "gancio_input_puntatore")),
            ("il FIGLIO inietta (l'altro lato del confine)",
             os.path.join(RADICE, "src/figlio.c"),
             ("input_puntatore(palco_input", "MSG_INPUT")),
    ):
        try:
            with open(percorso, encoding="utf-8", errors="replace") as f:
                testo = f.read()
        except OSError as e:
            trovato[nome] = (None, "⛔ non ho potuto leggere %s: %s" % (percorso, e))
            continue
        # ⛔ Si contano le occorrenze E si dichiara il denominatore: «zero» e
        #    «non ho potuto leggere» restano due frasi diverse.
        conti = {a: testo.count(a) for a in aghi}
        trovato[nome] = (sum(conti.values()) > 0,
                         "%s (%d righe lette)" % (conti, testo.count("\n") + 1))
    for nome, (c_e, dettaglio) in trovato.items():
        (ok if c_e else (dub if c_e is None else ko))("%-32s %s" % (nome, dettaglio))

    manca = [n for n, (c, _) in trovato.items() if not c]
    if manca:
        log("⛔⛔ NON HO NIENTE DA GIUDICARE")
        ko("manca: %s" % ", ".join(manca))
        inf("⚠ Non ho acceso niente: un giro che non puo' chiudere l'anello "
            "produrrebbe un verbale vuoto **con l'aria di una misura**, ed e' "
            "la specie di verde che entra in un catalogo e ci resta.")
        inf("⭐ Il banco e' pronto e certificato (53 controlli su 53, 16 guasti "
            "su 16): quando il prodotto arriva, un rosso significa il PRODOTTO.")
        inf("⛔ E questo NON e' «conforme»: esce %d." % USCITA_NIENTE_DA_GIUDICARE)
        deposita({"banco": "B30", "tipo": "MISURA NON ESEGUITA", "giro": a.giro,
                  "perche": "l'anello non e' chiudibile: manca %s" % manca,
                  "letto_nel_codice": {n: d for n, (_, d) in trovato.items()},
                  "codice_uscita": USCITA_NIENTE_DA_GIUDICARE})
        return USCITA_NIENTE_DA_GIUDICARE

    log("⭐ IL CANALE C'E': si accende il giro")
    return giro_vero(a, trovato)


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--misura", action="store_true")
    p.add_argument("--verdetto", help="rilegge un verbale su disco")
    p.add_argument("--finto", action="store_true",
                   help="⭐ stampa il verdetto sul FINTO: e' il modo di vedere "
                        "che cosa il banco dira' quando il prodotto arriva")
    p.add_argument("--host", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7691)
    p.add_argument("--porta-dentro", type=int, default=7692)
    p.add_argument("--ancora", type=int, default=7693)
    p.add_argument("--comando-ponte", default="/tmp/04-b30/comando")
    p.add_argument("--utente", default="nicfio")
    p.add_argument("--parola-file")
    p.add_argument("--secondi", type=float, default=25.0)
    p.add_argument("--coda-url", default="",
                   help="⭐ coda dell'indirizzo (es. «?tela=2d»).  ⛔ Serve "
                        "perche' dal 20 agosto la strada normale della pagina "
                        "e' `bitmaprenderer`, che NON ha il deposito 2D da cui "
                        "questo banco legge i pixel: senza coda si esce 3")
    p.add_argument("--schermo", default=":90")
    p.add_argument("--diagnosi", type=int, default=9630)
    p.add_argument("--lavoro", default="/tmp/04-b30")
    p.add_argument("--shm-scena", default="/dev/shm/remotix-04-b30")
    p.add_argument("--giro", default=time.strftime("b30-%Y%m%d-%H%M%S"))
    # ── quel che serve al GIRO VERO, e ciascuno con la sua ragione ──────────
    p.add_argument("--terreno", default="/media/REMOTIX/src/04-b32-terreno.sh",
                   help="⛔ lo script CHE STA DI LA': accende la scena, legge il "
                        "blocco di stato.  Un banco non entra nella sessione di "
                        "un utente da fuori")
    p.add_argument("--registro-prodotto",
                   default="/media/REMOTIX/tmp/04-b30/registro.log",
                   help="⛔ da qui si legge QUALE MONITOR il prodotto cattura: "
                        "non si deduce e non si scrive a mano")
    p.add_argument("--verbale-ponte", default="/media/REMOTIX/tmp/04-b30/ponte.json")
    p.add_argument("--ritardo-ritorno", type=float, default=25.0,
                   help="N ms sul ramo prodotto → cliente (Q5, tratto 5)")
    p.add_argument("--ritardo-andata", type=float, default=30.0,
                   help="⭐ N ms sul ramo cliente → prodotto (Q6, tratto 2) — "
                        "la meta' che alla fase 3 non esisteva")
    p.add_argument("--ritardo-vetro", type=float, default=8.0,
                   help="⭐⭐ N ms innestati DENTRO LA PAGINA fra «il fotogramma "
                        "e' pronto» e «il fotogramma e' al vetro» (Q11, tratto "
                        "10).  ⛔ E' il controllo positivo del CONFINE: se il "
                        "numero non sale di N, il confine si chiude prima del "
                        "disegno e quel che esce e' piu' piccolo del vero.  "
                        "⚠ Tenerlo sotto un intervallo di quadro (16,7 ms), o "
                        "il filo si satura e i fotogrammi si buttano invece di "
                        "ritardare.  0 = non fare il controllo (⛔ e allora Q11 "
                        "dice NON ESEGUITO, che non e' «passato»)")
    p.add_argument("--mani", type=int, default=3,
                   help="⛔ le condizioni si INTRECCIANO: a blocchi il ritardo "
                        "iniettato si confonde con la deriva")
    p.add_argument("--passo-ms", type=float, default=70.0,
                   help="ogni quanto si sintetizza un input.  ⚠ Piu' fitto di "
                        "un intervallo di quadro e gli eco intermedi non "
                        "vengono mai dipinti: quelle sonde non chiudono")
    p.add_argument("--finestra-x", type=int, default=700,
                   help="Q4(a): dove guardare per NON trovare l'eco")
    p.add_argument("--finestra-y", type=int, default=600)
    a = p.parse_args()

    if a.certifica:
        r = certifica()
        log("ESITO")
        (ok if r["esito"] == "PROMOSSO" else ko)(
            "%s — %d controlli su %d, e ⭐ **%d guasti innestati accusati su %d**"
            % (r["esito"], r["passati"], r["controlli"],
               r["guasti_accusati"], r["guasti_innestati"]))
        deposita({"banco": "B30", "tipo": "CERTIFICAZIONE", "giro": a.giro,
                  "esito": r["esito"], "controlli": r["controlli"],
                  "passati": r["passati"],
                  "guasti_innestati": r["guasti_innestati"],
                  "guasti_accusati": r["guasti_accusati"],
                  "dettaglio": [e for e in r["esiti"] if not e["esito"]][:20]})
        return USCITA_CONFORME if r["esito"] == "PROMOSSO" else USCITA_NON_CONFORME

    if a.finto:
        log("⭐ IL FINTO — quel che il banco dira' quando il prodotto arriva")
        inf("⛔ Questi numeri NON sono una misura: sono la forma della misura. "
            "Nessuna riga di qui va in un documento con la marca `[M]`.")
        g = stampa_verdetto(verbale_sintetico())
        return codice_uscita(g)

    if a.verdetto:
        with open(a.verdetto) as f:
            v = json.load(f)
        return codice_uscita(stampa_verdetto(v))

    if a.misura:
        return misura(a)

    p.print_help()
    return USCITA_USO


if __name__ == "__main__":
    sys.exit(principale())
