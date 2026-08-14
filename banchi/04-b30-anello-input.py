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
     `[?]` **16-40 ms** che nessuna API JavaScript vede (`web.md` §6.2).
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
#    fase 3 (`web.md` §6.2); ⭐ quello in INGRESSO e' nuovo, e nessuno lo aveva
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
            "pezzo cieco in USCITA (disegno finito → pixel acceso, `web.md` "
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
  const proto = window.CanvasRenderingContext2D
              && window.CanvasRenderingContext2D.prototype;
  if (proto && proto.drawImage) {
    const veroDI = proto.drawImage;
    proto.drawImage = function () {
      const a = performance.now();
      const r = veroDI.apply(this, arguments);
      const b = performance.now();
      if (B.disegni.length < 64) B.disegni.push(b - a);
      return r;
    };
  }

  /* ══ 5. VIDEODECODER: t1, il disegno del prodotto, poi i pixel ══════════ */
  const VeroVD = window.VideoDecoder;
  if (VeroVD) {
    function Avvolto(init) {
      const suo = init && init.output;
      const mio = Object.assign({}, init, {
        output: function (f) {
          /* ─── RIGA 1: `t1`.  ⛔ PRIMA di tutto, `web.md` §6.3. ─────────── */
          const t1 = performance.now();
          const pts = f.timestamp;
          const l = f.displayWidth || f.codedWidth;
          const a = f.displayHeight || f.codedHeight;
          B.conti.richiami++;
          /* ─── RIGA 2: SI DISEGNA — e a disegnare e' il PRODOTTO. ───────── */
          B.disegni.length = 0;
          let guaio = null;
          try { suo(f); } catch (e) { guaio = "" + e; }
          const t_dip = performance.now();
          const disegni = B.disegni.slice();
          /* ─── RIGA 3: e SOLO ADESSO si leggono i pixel, DUE regioni. ──── */
          let celle = null, celle_eco = null, t_let = t_dip;
          if (B.leggi) {
            const c0 = performance.now();
            celle = leggi_marca_celle(B.finestra[0], B.finestra[1]);
            celle_eco = leggi_marca_celle(B.finestra_eco[0], B.finestra_eco[1]);
            t_let = performance.now();
            if (B.costo_lettura_us.length < 20000)
              B.costo_lettura_us.push((t_let - c0) * 1000);
          }
          const s = B.intestazioni.get(pts) || null;
          if (!s) B.conti.senza_intestazione++;
          if (B.campioni.length < 400000) {
            B.campioni.push({
              t1: t1, t_dip: t_dip, t_let: t_let, pts: pts, l: l, a: a,
              celle: celle, celle_eco: celle_eco, guaio: guaio,
              /* ⭐ i due `drawImage`, separati.  ⛔ `null` e non 0 quando non
                 ce ne sono stati: «non ho potuto guardare» non e' «zero». */
              disegni_ms: disegni,
              t_dip_a: disegni.length ? (t1 + disegni[0]) : null,
              visto: celle !== null, visto_eco: celle_eco !== null,
              finestra: B.finestra.slice(),
              t_primo: s ? s.t_primo : null, t_ultimo: s ? s.t_ultimo : null,
              byte: s ? s.byte : null, tipo: s && s.i ? s.i.tipo : null,
              numero: s && s.i ? s.i.numero : null,
              input: s && s.i ? s.i.input : null,
              t_dec: B.t_dec.get(pts) || null,
            });
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

  /* ══ 6. LA LETTURA DEI PIXEL — dal DEPOSITO, non dalla vista ════════════ */
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
    return v;
  }

  /* ══ 7. IL RITIRO — si SVUOTA, cosi' due ritiri non contano due volte ═══ */
  B.prendi = function () {
    const c = B.campioni; B.campioni = [];
    const e = B.eventi; B.eventi = [];
    const s = B.spediti; B.spediti = [];
    const co = B.costo_lettura_us; B.costo_lettura_us = [];
    return { campioni: c, eventi: e, spediti: s, costo_lettura_us: co,
             violazioni: B.violazioni.slice(0, 200),
             conti: Object.assign({}, B.conti), grana: B.grana,
             isolata: B.isolata, t_origine: B.t_origine,
             ora_pagina: performance.now(),
             ora_reale: performance.timeOrigin + performance.now(),
             pagina: window.REMOTIX && window.REMOTIX.schermo
                     ? Object.assign({}, window.REMOTIX.schermo.conti) : null };
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
    ("9", "⭐ richiamo → 1° `drawImage` finito (⛔ l'ATTESA del fotogramma)", "pagina"),
    ("10", "⭐ 1° → 2° `drawImage` finito (⛔ il disegno VERO)", "pagina"),
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
        "fonte": "web.md §6.2",
        "nota": "⚠ su Xvfb non c'e' compositore: in QUESTO ambiente non esiste "
                "affatto.  La stima e' per lo schermo di un utente"}
    return r


# ═══════════════════════════════════════════════════════════════════════════
# §6  I CONTROLLI
# ═══════════════════════════════════════════════════════════════════════════
TUTTI = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"]


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
                 and not g.get("ritardo_andata_ms")), None) or (giri[0] if giri else {})
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
}
FINTO_TOTALE = sum(FINTO.values())


def verbale_sintetico(seme=7, quanti=240, ritardi_ritorno=(25,),
                      ritardi_andata=(30,), passo_ms=16.7):
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

    def fai_giro(rit_ritorno=0.0, rit_andata=0.0):
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
            t_dip = t_dip_a + FINTO["10"]
            eco = eco_puntatore(x, y)
            campioni.append({
                "t1": t1, "t_dip": t_dip, "t_dip_a": t_dip_a, "t_let": t_dip + 0.9,
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
                "distribuzione": _d([s["ritardo_scomodo_ms"] for s in buone]),
                "scomposizione": scomponi(sonde, scarto_us)}

    giri = [fai_giro(0.0, 0.0)]
    for n in ritardi_ritorno:
        giri.append(fai_giro(float(n), 0.0))
    for n in ritardi_andata:
        giri.append(fai_giro(0.0, float(n)))
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


def _g_p1_nel_tratto_sbagliato(v):
    """⛔⛔ IL GUASTO CHE UN P1 DELLA FASE 3 NON VEDE: la mediana sale di N —
    quindi «la mediana e' salita di N» passa — ⛔ ma il surplus e' finito nel
    tratto SBAGLIATO della scomposizione.  Un metro cosi' non diventa mai
    rosso: dice solo bugie sulla diagnosi."""
    for g in v["giri"]:
        n = g.get("ritardo_andata_ms") or g.get("ritardo_ritorno_ms")
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
    ("Q5/Q6 ⛔⛔ la mediana sale di N ma NEL TRATTO SBAGLIATO",
     _g_p1_nel_tratto_sbagliato, ["Q5", "Q6"]),
    ("Q7 ⛔⛔ il metro chiude sul confine COMODO", _g_confine_comodo, ["Q7"]),
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
    """⛔ Il blocco `stato_input` di `04-b30-scena.c`, letto col seqlock.

    ⭐ Sta DOPO `struct stato_condiviso`, e l'offset non si indovina: si legge
       dal campo `taglia` del primo blocco.  ⚠ Se la magia non torna, si dice
       «non ho potuto guardare» invece di restituire zeri — che sarebbero
       indistinguibili da «nessun evento e' arrivato».
    """
    try:
        with open(percorso_shm, "rb") as f:
            b = f.read()
    except OSError as e:
        return None, "⛔ non ho potuto leggere %s: %s" % (percorso_shm, e)
    if len(b) < 16:
        return None, "⛔ il blocco e' troppo corto: %d byte" % len(b)
    magia, versione, taglia = struct.unpack("<III", b[:12])
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


def misura(a):
    """⛔ LA MISURA VERA.  Oggi non gira: il canale di input nasce mentre questo
    banco si scrive, e il banco lo dice invece di fingere.

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
            ("i GANCI sono cuciti", os.path.join(RADICE, "src/figlio.c"),
             (".input_puntatore", "input_puntatore =")),
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
    ko("⛔ ma il giro vero non e' ancora stato scritto in questa funzione: "
       "l'ordine dei passi sta nella docstring qui sopra, e va steso quando "
       "l'anello si chiude per la prima volta.")
    inf("⚠ Lo dico invece di fingere un giro: un banco che dichiara di aver "
        "misurato e non ha misurato e' il difetto peggiore di tutti.")
    deposita({"banco": "B30", "tipo": "MISURA NON ESEGUITA", "giro": a.giro,
              "perche": "il canale c'e' ma il giro non e' steso",
              "letto_nel_codice": {n: d for n, (_, d) in trovato.items()},
              "codice_uscita": USCITA_NIENTE_DA_GIUDICARE})
    return USCITA_NIENTE_DA_GIUDICARE


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
    p.add_argument("--schermo", default=":90")
    p.add_argument("--diagnosi", type=int, default=9630)
    p.add_argument("--lavoro", default="/tmp/04-b30")
    p.add_argument("--shm-scena", default="/dev/shm/remotix-04-b30")
    p.add_argument("--giro", default=time.strftime("b30-%Y%m%d-%H%M%S"))
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
