#!/usr/bin/env python3
"""02-giudizio-metro.py — ⛔ IL METRO DELLA FASE 2: i pixel a confronto.

    python3 02-giudizio-metro.py --scena mira-g1.json \\
        --cattura cattura-g1.rgb48 --riferimento rif-g1.rgb48 \\
        --pagina pagina-g1.png [--cattura-precedente cattura-g0.rgb48] \\
        [--riferimento-10 rif-g1.rgb48] [--profondita-dispositivo prof.json] \\
        --giro g1 --esiti 02-giudizio-esiti.jsonl

Stati d'uscita — ⛔ e sono QUATTRO, non due:
    0  PROMOSSO     tutti gli strumenti applicabili hanno detto di si'
    1  BOCCIATO     almeno uno ha detto di no, e il rapporto dice quale
    2  NON MISURATO ⛔ non ho potuto guardare: manca un ingresso, la scena non
                    e' quella dichiarata, il canale di lettura non risponde.
                    ⛔ NON e' un promosso e NON e' un bocciato: e' la
                    distinzione fra zero e fallimento (`LEZIONI.md` §1.9)
    3  METRO ROTTO  il controllo positivo in coda non ha bocciato un guasto
                    innestato apposta: **il verdetto di questo giro non vale**

===========================================================================
⛔ IL PROBLEMA CHE QUESTO FILE DEVE RISOLVERE, SCRITTO PRIMA DELLA SOLUZIONE

`PIANO.md` fase 2 vuole *«il fotogramma decodificato confrontato con quello
catturato.  Non "il programma non e' crollato": **i pixel**»*.

Ma la codifica e' **con perdita**, e questo mette il metro fra due criteri che
sono tutti e due inutili:

  · **«identici»** — fallisce **sempre**, anche a catena perfetta.  Un metro
    che boccia sempre non viene guardato da nessuno dopo la seconda volta;
  · **«si somigliano»** — non fallisce **mai**.  Un metro che promuove tutto
    non e' un metro: e' un verde che da' fiducia, cioe' precisamente la cosa
    che `REVIEWER.md` §1 dichiara peggiore di nessuna misura.

===========================================================================
⭐ LA SOLUZIONE: IL METRO HA DUE PIANI, E LA PERDITA STA TUTTA IN UNO SOLO

La perdita e' del **codificatore**, ed e' un anello che questa fase non sta
giudicando.  Quel che la fase 2 giudica e' la catena **dal byte al pixel
dipinto**: filo, `VideoDecoder`, tela.  E su quella catena la perdita ammessa
non e' «poca»: e' **zero**, perche' la decodifica HEVC e' **normativa** — due
decodificatori conformi, dato lo stesso flusso, producono lo stesso YUV.

Da cui i due piani, e un terzo lettore che v1 non aveva:

  PIANO 1 — LA CATENA SENZA PERDITA.   pagina  ⟷  riferimento
      Il `riferimento` e' **lo stesso flusso decodificato da ffmpeg**, cioe'
      da un'implementazione scritta da gente che non ci conosce.  ⭐ E' il
      «secondo lettore» di `PIANO.md` §0.4: se il nostro server e la nostra
      pagina condividessero lo stesso fraintendimento, questo confronto lo
      vedrebbe e nessun altro banco della fase lo vedrebbe.
      Qui non c'e' perdita da codifica.  Le uniche differenze legittime sono
      la conversione YUV→RGB e l'arrotondamento a 8 bit della tela: ⇒ SOGLIA
      STRETTA, e la si sa giustificare (vedi «LE SOGLIE» qui sotto).

  PIANO 2 — LA CATENA INTERA.          pagina  ⟷  cattura
      Qui la perdita del codificatore c'e'.  ⛔ Ma la soglia NON e' un numero
      in dB scelto a occhio: e' **relativa al riferimento**.
          M2 = PSNR(pagina, cattura) − PSNR(riferimento, cattura)
      cioe' *«quanto la catena del client AGGIUNGE alla perdita che il
      codificatore ha gia' fatto»*.  ⭐ Cosi' la soglia si tara da se' sul QP
      che sceglie F2.3, e non va riscritta ogni volta che qualcuno tocca il
      codificatore — che e' il modo in cui una soglia assoluta muore.

===========================================================================
⛔ E UN NUMERO SOLO NON BASTA, PERCHE' QUATTRO GUASTI SU CINQUE LO PASSANO

Questo e' il cuore, ed e' scritto **prima** delle soglie apposta.  Ecco che
aspetto ha il caso opposto, guasto per guasto, e chi lo prende:

 | il guasto                        | il PSNR globale lo vede? | chi lo prende |
 |----------------------------------|--------------------------|---------------|
 | fotogramma **nero**              | si', crolla              | M1, M3        |
 | ⛔ **cattura E pagina nere**      | ⛔ **NO — PSNR infinito** | **M-V**       |
 | spostato di **una riga**         | ⛔ solo se la scena ha alta frequenza | M0 |
 | del **giro precedente**          | ⛔ solo se la scena e' cambiata | M6      |
 | **8 bit** al posto di 10         | ⛔ **NO — resta sopra 55 dB** | **M7**   |
 | **piani del colore scambiati**   | ⛔ **NO sulla luminanza**  | **M4**      |
 | gamma limitata letta come piena  | in parte                 | M5            |
 | un **blocco** corrotto           | ⛔ **NO — la media lo annega** | **M3**  |
 | immagine **ribaltata**           | si', ma senza dire perche' | M-V (marcatori) |

⛔ Le tre righe con «NO» in grassetto sono il motivo per cui questo file e'
lungo.  Un metro fatto del solo PSNR **promuoverebbe tre dei cinque guasti
che il mandato mi chiede di bocciare**, e lo farebbe in verde.

⛔ E la riga «cattura E pagina nere» e' la peggiore di tutte, perche' e' il
guasto che questa fase produce da se': `PIANO.md` fase 2 avverte che una
sessione GNOME headless senza `--virtual-monitor` parte **viva, completa e
nera** (`gnome.md` §13, M9).  Due fotogrammi neri hanno PSNR **infinito**:
il metro darebbe verde pieno su un desktop che non c'e'.  ⇒ **M-V viene
prima di tutti gli altri, ed e' una porta: senza scena viva non si misura.**

===========================================================================
LE SOGLIE, UNA PER UNA, CON LA RAGIONE — e quali sono `[?]`

  M-C  la dichiarazione del colore: cattura, codifica, riferimento e pagina
       devono dichiarare matrice, gamma e primarie, e chi legge deve leggere
       come e' stato scritto.  ⛔ Senza, il confronto MISURA LA MATRICE.
       Cucitura di F2.3.  Nessuna soglia: e' un confronto di dichiarazioni.

  M8   l'identita' del fotogramma dichiarata dalla pagina.  Cucitura di F2.4.
       Tre controlli, e **ognuno si conta a parte**: `dipinto_dopo_reset`
       (⭐ sulla catena vera e' `consegnati > completi` dei contatori della
       pagina), `fin_ricevuto` (⭐ `completi > 0`) e `giro` (⛔ NON
       APPLICABILE dalla catena vera: e' il nome del giro DEL BANCO, che il
       prodotto non conosce — lo copre M6 sui pixel).  Nessuna soglia.
       ⛔ Se **nessuno** dei tre e' eseguibile, M8 esce `ok: None` e non e'
       uno strumento vivo: fino al 13 agosto 2026 usciva verde su zero
       controlli, e il «12 guasti su 12» della catena vera erano 11.
       ⛔ Anello DEBOLE per costruzione: crede a chi e' sotto esame, e vale
       solo insieme al registro di F2.4.

  M-V  vitalita' della scena.  deviazione standard di Y ≥ 0,02 (su 0..1) e
       ≥ 32 livelli distinti, **e i quattro marcatori al posto giusto**.
       RAGIONE: un desktop nero ha deviazione 0; una tinta unita ha 1
       livello.  ⛔ La soglia qui non deve essere fine: deve solo separare
       «c'e' un'immagine» da «non c'e' niente».  I marcatori sono la parte
       che conta, e sono un confronto (ognuno somiglia al proprio, non a
       quello del vicino), quindi **non hanno soglia**.

  M0   allineamento.  Fra i 25 scorrimenti (dx,dy) in [-2..+2] il migliore
       dev'essere **(0,0)**, con ≥ 3 dB sul secondo.
       RAGIONE: ⭐ e' un criterio **relativo**, senza nessun numero magico
       sul valore assoluto del PSNR — e per questo regge a qualunque QP.  I
       3 dB di margine ci sono perche' su una scena con i pettini a passo 1
       il divario vero e' di decine di dB: 3 e' un margine, non un limite.

  M1a  PSNR-Y(pagina, riferimento) ≥ **45 dB**.
       RAGIONE, e si sa fare il conto: la decodifica HEVC e' normativa, il
       piano Y non e' toccato dal ricampionamento della crominanza, quindi
       l'unica differenza legittima e' l'arrotondamento a 8 bit della tela.
       Un errore uniforme di ±0,5 LSB su 255 da' RMSE ≈ 0,29 ⇒ PSNR ≈ 59 dB.
       Con un LSB pieno di scarto ⇒ ≈ 48 dB.  45 dB lascia margine a un
       arrotondamento fatto in un altro ordine, e **boccia tutto il resto**.
       ⚠ `[?]` finche' non gira sul ferro: il valore sano atteso e' ≥ 55 dB,
       e se il misurato cadesse fra 45 e 55 **e' un difetto da guardare**,
       non un promosso comodo.  Il banco lo stampa sempre, non solo quando
       fallisce.

  M1b  PSNR-RGB(pagina, riferimento) ≥ **38 dB**.
       RAGIONE: qui entra il ricampionamento della crominanza 4:2:0, che i
       decodificatori fanno con filtri **legittimamente diversi** (nearest,
       bilineare).  Sui bordi colorati la differenza e' vera e non e' un
       difetto.  38 dB e' sotto M1a apposta: e' la soglia piu' lasca del
       metro, e non e' quella che porta il verdetto.

  M2   PSNR-Y(pagina, cattura) − PSNR-Y(riferimento, cattura) ≥ **−0,5 dB**.
       RAGIONE: e' una differenza, quindi la perdita del codificatore si
       cancella.  Zero e' il valore giusto; −0,5 dB e' il rumore di misura.
       ⭐ E' la soglia che NON invecchia quando F2.3 cambia il QP.

  M3   PSNR-Y del **blocco 64×64 peggiore** (pagina, riferimento) ≥ **30 dB**.
       RAGIONE: la media annega un guasto locale.  Un blocco di 64×64 su
       1920×1080 e' 1/506 dell'immagine: puo' essere spazzatura pura e
       spostare il PSNR globale di **0,03 dB**.  30 dB su un blocco che
       dovrebbe stare a 55 e' un margine largo, ed e' voluto: qui si cerca
       la spazzatura, non la sfumatura.

  M4   identita' dei canali, misurata **solo sui tre riquadri a luminanza
       uguale**: l'errore quadratico fra il canale c della pagina e il canale
       c del riferimento dev'essere ≥ **4 volte** minore che verso il migliore
       degli altri due.
       RAGIONE: nessuna soglia assoluta — e' un rapporto.  ⛔ Serve perche' i
       tre riquadri hanno **la stessa luminanza**: scambiare R e B non muove Y
       di un LSB, e M1a/M2/M3 promuovono il guasto.  ⛔ E si misura solo li'
       perche' su una scena naturale R, G e B sono correlati fra loro a 0,978
       `[M]`: fuori dai riquadri il segnale non c'e' e ogni soglia e' rumore.

  M5   guadagno e scarto per canale (minimi quadrati pagina↔riferimento):
       guadagno in **[0,98 ; 1,02]**, scarto in **[−2 ; +2]** su 255.
       RAGIONE: prende la gamma limitata letta come piena, che e' un
       guadagno di 255/219 = **1,164** — dodici volte fuori soglia — e la
       matrice sbagliata (BT.601 letta come BT.709), che sposta gli scarti
       dei canali in versi diversi.  ⚠ E' anche il posto dove si vede se
       F2.3 ha scritto il VUI: senza, il browser **indovina**, e la firma
       dell'indovinato sbagliato e' esattamente questa.

  M6   freschezza.  PSNR-Y(pagina, cattura_N) − PSNR-Y(pagina, cattura_N−1)
       ≥ **+3 dB**.
       RAGIONE: relativo di nuovo.  ⛔ E ha un prezzo dichiarato: pretende
       che **la scena sia cambiata fra i due giri**, ed e' il motivo per cui
       la mira ha un riquadro di rumore seminato sul nome del giro.  Se la
       cattura precedente non c'e', M6 dice **«non misurata»** e il giro
       esce con stato 2 — non con un promosso.

  M7   profondita'.  Sulla decodifica di riferimento in `yuv420p10le`, e
       ⛔ **solo sulle zone SFUMATE dichiarate**: la distribuzione dei due bit
       bassi del piano Y.  Casella piu' piena ≤ **0,50** e tutte e quattro
       ≥ 0,05.
       RAGIONE: 0,50 e' il confine esatto fra «almeno tre caselle portano
       informazione» e «al massimo due», che e' la firma aritmetica del
       troncamento.  Misurato: sano [0,26 0,25 0,25 0,24] · troncato [1 0 0 0]
       · troncato e riscalato [0,63 0 0 0,37].  ⛔ E la prova delle BANDE
       proposta da S2 §3.7 e' stata provata e **scartata**: non sopravvive
       alla codifica con perdita (rapporto 4,13 → 1,31 a QP 20).
       ⛔ E in fase 2 l'atteso e' **8 bit promossi**, non 10 bit veri: la
       sorgente e' BGRx (F2.2, misurato).  Vedi la nota lunga su `m7_profondita`.
       ⛔⛔ E LA COSA PIU' IMPORTANTE DI TUTTO IL FILE: **sul lato pagina,
       con una tela a 8 bit, questa domanda NON HA RISPOSTA.**  Un valore a
       10 bit e uno a 8 differiscono al massimo di un LSB dopo la conversione
       a 8 bit: nessun confronto di pixel su `getImageData` puo' distinguerli.
       ⇒ il metro, sul lato dispositivo, dichiara **«non misurabile»** e NON
       promuove.  Chiamare «10 bit ok» il fatto che i pixel coincidano
       sarebbe la forma d'errore **E1** — necessario preso per sufficiente —
       cioe' quella che ha ucciso v1.  I due canali che rispondono davvero
       sono `VideoFrame.format`/`copyTo()` dove esiste, e la decodifica di
       riferimento fuori dal browser: si passano con `--riferimento-10` e
       `--profondita-dispositivo`, oppure il metro **dice che non lo sa**.

===========================================================================
⛔ I DUE CONTROLLI POSITIVI, IN CODA A OGNI GIRO

  C1 — IL CANALE DI LETTURA.  Per ogni ingresso si stampano percorso,
       dimensione, impronta e ora.  ⛔ E se due ingressi hanno **la stessa
       impronta** il metro si ferma: confrontare un file con se stesso da'
       PSNR infinito, cioe' un verde regalato.  E' un errore che si fa da
       soli passando due volte lo stesso nome sulla riga di comando, e senza
       questo controllo nessuno se ne accorgerebbe mai.
       *(La forma e' quella del controllo n. 4 di `01-s1b-eccezione.sh`:
       dimostrare che «NO» vuol dire «non e' arrivato» e non «non ho potuto
       guardare».)*

  C2 — LO STRUMENTO SA BOCCIARE.  Alla fine di ogni giro il metro prende la
       pagina che ha appena giudicato, le innesta **in memoria** due guasti
       noti — uno scorrimento di una riga e un blocco 64×64 azzerato — e si
       rimisura addosso.  Se M0 e M3 non li bocciano, il metro si dichiara
       **rotto** (stato 3) e il verdetto di questo giro **non vale**.
       ⛔ E' `LEZIONI.md` §1.2 applicata al singolo giro invece che una volta
       sola: un metro certificato ieri, su file cambiati stanotte, oggi non
       e' certificato.
===========================================================================
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import sys

import numpy as np

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# BT.709, la stessa matrice che si chiede a ffmpeg e che il VUI deve dichiarare.
KR, KG, KB = 0.2126, 0.7152, 0.0722

SOGLIE = {
    "MV_dev":        0.02,
    "MV_livelli":    32,
    "M0_margine_db": 3.0,
    "M1a_db":        45.0,
    "M1b_db":        38.0,
    "M2_db":        -0.5,
    "M3_db":         30.0,
    "M4_rapporto":   4.0,
    "M5_guadagno":  (0.98, 1.02),
    "M5_scarto":     2.0 / 255.0,
    "M6_db":         3.0,
    "M7_bit_bassi_max": 0.50,
    "M7_bit_bassi_min": 0.05,
}


# ───────────────────────────────────────────────────────────────────────────
# La lettura.  ⛔ Un ingresso che non si legge non e' un ingresso nero.
# ───────────────────────────────────────────────────────────────────────────
def carica(percorso, larghezza, altezza, quale):
    """Ritorna (array float 0..1 [h,w,3], profondita_letta, impronta)."""
    if percorso is None:
        return None, None, None
    if not os.path.exists(percorso):
        raise Mancante("%s: il file non esiste — «%s»" % (quale, percorso))
    dati = open(percorso, "rb").read()
    if len(dati) == 0:
        raise Mancante("%s: il file e' VUOTO — «%s».  ⛔ Vuoto e nero non "
                       "sono la stessa cosa" % (quale, percorso))
    impronta = hashlib.sha256(dati).hexdigest()[:16]
    est = os.path.splitext(percorso)[1].lower()
    if est in (".rgb48", ".raw48"):
        atteso = larghezza * altezza * 6
        if len(dati) < atteso:
            raise Mancante("%s: %d byte, ne servivano %d per %dx%d rgb48le"
                           % (quale, len(dati), atteso, larghezza, altezza))
        a = np.frombuffer(dati[:atteso], dtype="<u2").reshape(altezza, larghezza, 3)
        return a.astype(np.float64) / 65535.0, 16, impronta
    if est in (".rgb24", ".rgb", ".raw"):
        atteso = larghezza * altezza * 3
        if len(dati) < atteso:
            raise Mancante("%s: %d byte, ne servivano %d per %dx%d rgb24"
                           % (quale, len(dati), atteso, larghezza, altezza))
        a = np.frombuffer(dati[:atteso], dtype=np.uint8).reshape(altezza, larghezza, 3)
        return a.astype(np.float64) / 255.0, 8, impronta
    if est == ".png":
        try:
            from PIL import Image
        except ImportError:
            raise Mancante("%s e' un PNG e Pillow non c'e': o si installa, o "
                           "si passa il raw" % quale)
        im = Image.open(percorso).convert("RGB")
        if im.size != (larghezza, altezza):
            raise Mancante("%s: e' %dx%d, la scena dichiara %dx%d.  ⛔ Non lo "
                           "ridimensiono: ridimensionare un ingresso significa "
                           "confrontare due immagini che nessuno ha prodotto"
                           % (quale, im.size[0], im.size[1], larghezza, altezza))
        return np.asarray(im).astype(np.float64) / 255.0, 8, impronta
    raise Mancante("%s: estensione «%s» sconosciuta" % (quale, est))


class Mancante(Exception):
    """⛔ Non ho potuto guardare — stato 2.  Diverso da «non coincide»."""


# ───────────────────────────────────────────────────────────────────────────
# M-C — LA DICHIARAZIONE DEL COLORE.  ⛔ Seconda porta, e viene da F2.3.
# ───────────────────────────────────────────────────────────────────────────
def mc_colore(percorso):
    """⛔ Senza matrice e gamma dichiarate, il confronto MISURA LA MATRICE.

    Cucitura rientrata da F2.3 il 12 agosto 2026, e chiude un buco che questo
    metro aveva: M5 sa **accorgersi** che la trasformazione non e' l'identita',
    ma non sa dire se la colpa e' del client o del fatto che i due lati stanno
    leggendo lo stesso YUV con due matrici diverse.  Un numero dato in quelle
    condizioni non e' interpretabile, e un numero non interpretabile e' peggio
    di nessun numero perche' entra nei documenti come misura.

    ⇒ Le tre parti — cattura, riferimento, pagina — devono **dichiarare**
      matrice, gamma e primarie, e le tre dichiarazioni devono coincidere.
      · file assente        ⇒ stato 2, NON MISURATO;
      · dichiarazioni diverse ⇒ BOCCIATO, e la ragione dice quale.
    ⚠ E la dichiarazione non e' una prova che il lato abbia obbedito: e' M5
      che lo verifica sui pixel.  Le due cose stanno insieme — `LEZIONI.md`
      §1.11 punto 2: si chiede al componente, **e si verifica che abbia
      obbedito**.
    """
    if percorso is None:
        raise Mancante(
            "⛔ manca --colore: nessuno ha dichiarato matrice e gamma della "
            "cattura, del riferimento e della pagina.  Un confronto di pixel "
            "fatto con la matrice sbagliata (601 contro 709) o con la gamma "
            "sbagliata (limitata contro piena) misura LA MATRICE, non la "
            "catena.  ⇒ qui non si da' nessun numero (cucitura di F2.3)")
    try:
        d = json.load(open(percorso))
    except Exception as e:                       # noqa: BLE001
        raise Mancante("--colore non si legge: %s" % e)
    # ⛔ E LA CATTURA NON HA UNA MATRICE — cucitura di F2.2, 12 agosto 2026.
    #    Mutter consegna **BGRx/BGRA**: alla cattura i pixel sono **RGB**, e
    #    l'RGB non ha matrice di conversione, ce l'ha chi converte.  La prima
    #    stesura pretendeva che tutt'e tre dichiarassero la STESSA matrice, e
    #    su una cattura RGB onesta sarebbe uscita rossa.
    # ⇒ le parti sono QUATTRO, e ognuna dichiara quel che le compete:
    #      cattura     lo spazio (RGB o YUV) e la gamma
    #      codifica    ⭐ la matrice che F2.3 ha SCELTO nel convertire
    #      riferimento e pagina  la matrice con cui hanno letto
    #    e la regola e': chi legge deve leggere con la matrice con cui e'
    #    stato scritto.  ⛔ Pretesa dichiarata, mai dedotta.
    if "cattura" not in d:
        raise Mancante("--colore non dichiara «cattura»")
    cat = d["cattura"]
    if not cat.get("spazio"):
        raise Mancante("--colore: la cattura non dichiara lo «spazio» (RGB o "
                       "YUV).  ⛔ Mutter consegna BGRx, cioe' RGB, e un RGB "
                       "letto come YUV non e' un'immagine sbagliata: e' "
                       "un'immagine di un'altra cosa")
    if not cat.get("gamma"):
        raise Mancante("--colore: la cattura non dichiara la «gamma».  ⚠ F2.2 "
                       "avverte che Mutter NON la dichiara e che va MISURATA "
                       "(misurata 0-255): «non dichiarata da Mutter» e «non "
                       "dichiarata da noi» sono due cose diverse")
    rgb = str(cat["spazio"]).upper().startswith("RGB")
    if rgb and str(cat.get("matrice", "nessuna")).lower() not in ("nessuna", "none", ""):
        return {"ok": False, "dichiarato": d,
                "ragione": ("⛔ la cattura dichiara spazio RGB **e** una "
                            "matrice («%s»): l'RGB non ha matrice, ce l'ha chi "
                            "converte.  Una delle due dichiarazioni e' falsa"
                            % cat.get("matrice"))}
    campi = ("matrice", "gamma", "primarie")
    parti = ("codifica", "riferimento", "pagina")
    for p in parti:
        if p not in d:
            raise Mancante(
                "--colore non dichiara «%s».  ⛔ Senza «codifica» non si sa con "
                "quale matrice il flusso e' stato SCRITTO, e «letto con la "
                "stessa» diventa una speranza" % p)
        for c in campi:
            if not d[p].get(c):
                raise Mancante("--colore: «%s» non dichiara «%s».  ⛔ «non "
                               "dichiarato» e «bt709» non sono la stessa cosa: "
                               "il decodificatore che non trova il VUI "
                               "INDOVINA" % (p, c))
    disaccordi = []
    for c in campi:
        v = {p: str(d[p][c]).lower() for p in parti}
        if len(set(v.values())) > 1:
            disaccordi.append("%s: %s" % (c, v))
    # ⛔⭐ E LA CODIFICA HA **DUE** GAMME, NON UNA — 13 agosto 2026, trovato al
    #    primo giro sulla catena vera.
    #
    #    La prima stesura confrontava `cattura.gamma` con `codifica.gamma`, cioe'
    #    pretendeva che la codifica SCRIVESSE nella gamma in cui aveva RICEVUTO.
    #    ⛔ Sul prodotto vero non e' cosi', ed e' legittimo: Mutter consegna RGB
    #    **pieno** (0-255, misurato da F2.2) e il codificatore scrive YUV
    #    bt709 a gamma **limitata**, dichiarandolo nel VUI
    #    (`color_range = tv`, letto con `ffprobe`).  Il browser legge il VUI e
    #    riespande: la catena e' coerente, e questo controllo l'avrebbe
    #    **bocciata** — un rosso su una conversione dichiarata e corretta.
    #
    # ⇒ Le due domande si separano, e restano tutt'e due:
    #      1. la codifica ha LETTO la cattura nella gamma in cui e' arrivata?
    #         (`gamma_ingresso` contro `cattura.gamma`)
    #      2. chi legge il flusso legge nella gamma in cui e' stato SCRITTO?
    #         (`gamma` di codifica, riferimento e pagina — gia' sopra)
    # ⚠ `gamma_ingresso` assente ⇒ si torna alla domanda vecchia: una catena
    #   che non dichiara la conversione non se ne compra il permesso col
    #   silenzio.
    ing = d["codifica"].get("gamma_ingresso")
    g = {"cattura": str(cat["gamma"]).lower(),
         "codifica": str(ing if ing else d["codifica"]["gamma"]).lower()}
    if len(set(g.values())) > 1:
        disaccordi.append(
            ("gamma con cui la codifica HA LETTO la cattura: %s" % g) if ing else
            ("gamma fra cattura e codifica: %s — ⚠ e la codifica non dichiara "
             "«gamma_ingresso»: una conversione di gamma e' legittima, ma va "
             "DICHIARATA, o «ha convertito» e «ha letto male» hanno la stessa "
             "faccia" % g))
    if disaccordi:
        return {"ok": False, "dichiarato": d,
                "ragione": ("⛔ CHI LEGGE NON LEGGE COME E' STATO SCRITTO: "
                            + " · ".join(disaccordi) + ".  Il confronto "
                            "misurerebbe la conversione, non la catena — e il "
                            "numero non sarebbe interpretabile")}
    return {"ok": True, "dichiarato": d["codifica"],
            "cattura": {"spazio": cat["spazio"], "gamma": cat["gamma"]}}


def luma(a):
    return KR * a[:, :, 0] + KG * a[:, :, 1] + KB * a[:, :, 2]


def psnr(a, b):
    """PSNR con MAX=1.  Ritorna None se identici — ⛔ e None NON e' «ottimo»."""
    d = (a.astype(np.float64) - b.astype(np.float64))
    mse = float(np.mean(d * d))
    if mse <= 0:
        return None
    return 10.0 * math.log10(1.0 / mse)


def psnr_num(a, b, se_identici=99.0):
    v = psnr(a, b)
    return se_identici if v is None else v


# ───────────────────────────────────────────────────────────────────────────
# Gli strumenti
# ───────────────────────────────────────────────────────────────────────────
def mv_vitalita(img, zone, quale, mira=True):
    """M-V — la porta.  Senza scena viva non si misura niente.

    ⛔⭐ E `mira=False` NON SPEGNE QUESTA PORTA, ne spegne META' — 13 agosto 2026.

    La scena della catena vera e' **il desktop dell'utente**, non la mira: sul
    desktop non ci sono ne' i quattro marcatori d'angolo, ne' i tre riquadri a
    luminanza uguale, ne' le rampe.  ⇒ Su una scena cosi' il metro ha due strade
    e una sola e' onesta:

      · pretendere i marcatori ⇒ **rosso su una catena sana**, cioe' uno
        strumento che dice no sempre, che `F2-6` §3.3 dichiara non essere uno
        strumento;
      · ⛔ **promuovere in silenzio** ⇒ un verde che si porta dietro tre guasti
        che questo giro NON avrebbe visto.  E' la cosa peggiore delle due.

    ⇒ La terza: la meta' che **non dipende dalla scena** — deviazione e livelli,
      cioe' la guardia contro i due neri con PSNR infinito — resta in vigore e
      boccia; la meta' che dipende dalla mira si dichiara NON APPLICABILE con
      scritto **che cosa smette di vedere**: un'immagine ribaltata dira' «i
      pixel non coincidono» invece di «e' ribaltata».
    """
    y = luma(img)
    dev = float(np.std(y))
    livelli = int(len(np.unique(np.round(y * 255).astype(np.int32))))
    esito = {"dove": quale, "deviazione": round(dev, 5), "livelli": livelli,
             "marcatori": None}
    if dev < SOGLIE["MV_dev"] or livelli < SOGLIE["MV_livelli"]:
        esito["ok"] = False
        esito["ragione"] = ("⛔ la scena in «%s» e' PIATTA: deviazione %.5f "
                            "(serve ≥ %.2f), %d livelli (servono ≥ %d).  Un "
                            "desktop nero e un desktop che non c'e' hanno lo "
                            "stesso aspetto, e due neri a confronto danno PSNR "
                            "infinito: qui il metro si ferma invece di "
                            "promuovere" % (quale, dev, SOGLIE["MV_dev"],
                                            livelli, SOGLIE["MV_livelli"]))
        return esito

    if not mira:
        # ⛔ E il limite si scrive QUI, non nel rapporto: chi legge questa riga
        #    sa che il giro non puo' dire «ribaltata».
        esito["ok"] = True
        esito["applicabile_marcatori"] = False
        esito["marcatori"] = ("⚠ NON APPLICABILE: la scena dichiara «mira»: "
                              "false, cioe' non e' la mira di F2.6 e non ha i "
                              "quattro marcatori d'angolo.  ⇒ questo giro NON "
                              "vede il guasto «ribaltato»: un'immagine "
                              "specchiata direbbe «i pixel non coincidono» "
                              "invece di «e' ribaltata», e manderebbe a cercare "
                              "dalla parte sbagliata.  ⭐ La meta' che conta di "
                              "piu' — due neri con PSNR infinito — e' stata "
                              "misurata lo stesso, qui sopra")
        return esito

    # I quattro marcatori: ognuno deve somigliare AL PROPRIO, non a quello
    # del vicino.  ⛔ Confronto, non soglia.
    attesi, visti, nomi = [], [], []
    for nome, z in zone["marcatori"].items():
        m = z["lato"] // 2
        blocco = y[z["y"]:z["y"] + z["lato"], z["x"]:z["x"] + z["lato"]]
        if blocco.shape != (z["lato"], z["lato"]):
            esito["ok"] = False
            esito["ragione"] = "⛔ il marcatore «%s» cade fuori dall'immagine" % nome
            return esito
        q = [float(np.mean(blocco[(i // 2) * m:(i // 2) * m + m,
                                  (i % 2) * m:(i % 2) * m + m])) for i in range(4)]
        visti.append(q)
        attesi.append([1.0 if v else 0.0 for v in z["quadranti"]])
        nomi.append(nome)
    V = np.array(visti)
    # normalizzo ogni marcatore visto sul proprio min/max, cosi' il confronto
    # non dipende dalla luminosita' assoluta ma solo dal DISEGNO
    for i in range(V.shape[0]):
        lo, hi = V[i].min(), V[i].max()
        V[i] = (V[i] - lo) / (hi - lo) if hi > lo else 0.5
    A = np.array(attesi)
    dist = np.abs(V[:, None, :] - A[None, :, :]).sum(axis=2)   # [visto, atteso]
    scelta = dist.argmin(axis=1)
    esito["marcatori"] = {nomi[i]: nomi[int(scelta[i])] for i in range(len(nomi))}
    if any(scelta[i] != i for i in range(len(nomi))):
        esito["ok"] = False
        esito["ragione"] = ("⛔ i marcatori d'angolo di «%s» non sono al loro "
                            "posto: %s.  L'immagine e' ribaltata, ruotata, "
                            "ritagliata, o non e' la scena dichiarata — e in "
                            "tutti e quattro i casi il confronto dei pixel "
                            "misurerebbe un'altra cosa" % (quale, esito["marcatori"]))
        return esito
    esito["ok"] = True
    return esito


def m0_allineamento(pag, rif):
    """M0 — il migliore fra i 25 scorrimenti dev'essere (0,0)."""
    b = 2
    base = rif[b:-b, b:-b]
    tab = {}
    for dy in range(-b, b + 1):
        for dx in range(-b, b + 1):
            sp = pag[b + dy:pag.shape[0] - b + dy, b + dx:pag.shape[1] - b + dx]
            tab[(dy, dx)] = psnr_num(luma(sp), luma(base))
    zero = tab[(0, 0)]
    altri = max(v for k, v in tab.items() if k != (0, 0))
    migliore = max(tab, key=tab.get)
    ok = migliore == (0, 0) and (zero - altri) >= SOGLIE["M0_margine_db"]
    return {"ok": bool(ok), "psnr_zero": round(zero, 2),
            "migliore": list(migliore), "psnr_migliore": round(tab[migliore], 2),
            "margine_db": round(zero - altri, 2),
            "ragione": None if ok else
            ("⛔ il fotogramma e' SPOSTATO: lo scorrimento migliore e' %s "
             "(%.2f dB) contro (0,0) a %.2f dB, margine %.2f dB.  Su una scena "
             "morbida questo guasto non si vedrebbe: lo prendono i pettini a "
             "passo 1 px della mira" % (migliore, tab[migliore], zero, zero - altri))}


def m1_catena_pulita(pag, rif):
    ya, yb = luma(pag), luma(rif)
    a = psnr_num(ya, yb)
    b = psnr_num(pag, rif)
    ok = a >= SOGLIE["M1a_db"] and b >= SOGLIE["M1b_db"]
    return {"ok": bool(ok), "psnr_y_db": round(a, 2), "psnr_rgb_db": round(b, 2),
            "ragione": None if ok else
            ("⛔ fra la pagina e la decodifica di riferimento la perdita "
             "ammessa e' ZERO (la decodifica HEVC e' normativa): Y %.2f dB "
             "(serve ≥ %.1f), RGB %.2f dB (serve ≥ %.1f)"
             % (a, SOGLIE["M1a_db"], b, SOGLIE["M1b_db"]))}


def m2_catena_intera(pag, rif, cat, prof_pagina=8):
    # ⛔ TROVATO FACENDO GIRARE IL BANCO, 12 agosto 2026 — e il primo giro sano
    #    era ROSSO per colpa di questa riga mancante.
    #    La pagina esce da una tela a 8 bit; il riferimento e' a 16.  Sottraendo
    #    i due PSNR senza portarli alla stessa profondita' si accusa il client
    #    di una perdita che e' **della tela**, non sua: misurato Δ = −6,23 dB su
    #    una catena perfetta.  ⇒ il riferimento si porta alla profondita' con
    #    cui la pagina e' stata letta, e solo dopo si sottrae.
    fondo = psnr_num(luma(pag), luma(rif))
    if prof_pagina and prof_pagina <= 8:
        rif = np.round(rif * 255.0) / 255.0
    a = psnr_num(luma(pag), luma(cat))
    r = psnr_num(luma(rif), luma(cat))
    d = a - r
    # ⛔ IL DOMINIO DI VALIDITA', E IL METRO LO DICHIARA INVECE DI BOCCIARE.
    #    Trovato girando, 12 agosto 2026: con una codifica quasi senza perdita
    #    (QP 20 sulla mira: il riferimento sta a 60,4 dB dalla cattura) il
    #    rumore della TELA a 8 bit — che sta a 55,6 dB — pesa piu' della
    #    perdita del codificatore, e la sottrazione misura la tela invece del
    #    client: Δ = −3,18 dB su una catena perfetta.
    #    ⇒ M2 ha senso solo quando la perdita del codificatore DOMINA.  Quando
    #    non domina il metro non boccia e non promuove: dice **non applicabile**
    #    e stampa i due numeri, che sono un'informazione per F2.3 (sta
    #    codificando quasi senza perdita) e non un difetto del client.
    # ⛔ I 10 dB non sono scelti a occhio: sono LEGATI alla soglia di −0,5 dB.
    #    Se il fondo della tela sta m dB sopra la perdita del codificatore, e i
    #    due errori sono indipendenti, il Δ atteso su una catena PERFETTA vale
    #        Δ = −10·log10(1 + 10^(−m/10))
    #    che a m = 6 dB fa −0,97 dB — cioe' un ROSSO su una catena sana.  A
    #    m = 10 dB fa −0,41 dB, dentro la soglia con margine.  ⇒ margine 10 dB.
    #    (Prima stesura: 6 dB.  Il giro sano a QP 34 usciva a −0,34 dB, cioe' a
    #    un soffio dal rosso per una ragione puramente aritmetica.)
    applicabile = r <= fondo - 10.0
    if not applicabile:
        return {"ok": None, "applicabile": False,
                "psnr_pagina_cattura_db": round(a, 2),
                "psnr_riferimento_cattura_db": round(r, 2),
                "fondo_tela_db": round(fondo, 2), "delta_db": round(d, 2),
                "ragione": ("⚠ NON APPLICABILE su questo giro: il riferimento "
                            "dista %.2f dB dalla cattura (la perdita del "
                            "codificatore) e la pagina dista %.2f dB dal "
                            "riferimento (il rumore della tela a 8 bit).  La "
                            "seconda non e' almeno 6 dB sotto la prima: la "
                            "sottrazione misurerebbe la tela, non il client.  "
                            "⛔ Non e' un promosso ed e' scritto, non taciuto"
                            % (r, fondo))}
    ok = d >= SOGLIE["M2_db"]
    return {"ok": bool(ok), "applicabile": True,
            "psnr_pagina_cattura_db": round(a, 2),
            "psnr_riferimento_cattura_db": round(r, 2),
            "fondo_tela_db": round(fondo, 2), "delta_db": round(d, 2),
            "ragione": None if ok else
            ("⛔ la catena del client AGGIUNGE perdita: la pagina sta %.2f dB "
             "sotto la decodifica di riferimento sullo stesso flusso (ammessi "
             "%.1f).  ⚠ La perdita del codificatore e' in tutt'e due i termini "
             "e si cancella: questo numero non giudica F2.3"
             % (d, SOGLIE["M2_db"]))}


def m3_blocco_peggiore(pag, rif, lato=64):
    ya, yb = luma(pag), luma(rif)
    h, w = ya.shape
    peggio, dove = 1e9, None
    for y0 in range(0, h - lato + 1, lato):
        for x0 in range(0, w - lato + 1, lato):
            v = psnr_num(ya[y0:y0 + lato, x0:x0 + lato],
                         yb[y0:y0 + lato, x0:x0 + lato])
            if v < peggio:
                peggio, dove = v, (y0, x0)
    ok = peggio >= SOGLIE["M3_db"]
    return {"ok": bool(ok), "psnr_db": round(peggio, 2), "blocco": list(dove or ()),
            "ragione": None if ok else
            ("⛔ il blocco 64×64 in %s sta a %.2f dB (serve ≥ %.1f).  Un blocco "
             "cosi' e' 1/506 dell'immagine: puo' essere spazzatura pura e "
             "spostare il PSNR globale di 0,03 dB — la media lo annega, questo "
             "strumento no" % (dove, peggio, SOGLIE["M3_db"]))}


def m4_canali(pag, rif, zone, mira=True):
    """M4 — SOLO sui tre riquadri a luminanza uguale della mira.

    ⛔ La prima stesura correlava i canali su TUTTA l'immagine, e il primo giro
       sano e' uscito rosso: su una scena naturale R, G e B sono correlati fra
       loro a 0,978, e nessun margine sensato separa 1,000 da 0,978.  E' la
       forma dell'errore che `LEZIONI.md` §1.9 chiama «lo strumento che non sa
       trovare quel che c'e' di sicuro»: uno strumento tarato su una zona dove
       il segnale non esiste.
    ⇒ M4 guarda dove il segnale c'e' **per costruzione**: i tre riquadri
       (87,0,0) · (0,26,0) · (0,0,255) della mira, dove i canali sono spenti a
       turno.  La grandezza e' l'errore quadratico medio, e il criterio e' che
       ogni canale somigli al PROPRIO almeno 4 volte meglio (6 dB) che al
       migliore degli altri due.  Se i piani sono scambiati il rapporto va a 1.
    """
    if not mira:
        # ⛔ E NON si ripiega sull'immagine intera: e' esattamente la prima
        #    stesura, quella che il primo giro sano ha smascherato (R, G e B
        #    correlati a 0,978 su una scena naturale ⇒ rosso su catena sana).
        #    Uno strumento tarato dove il segnale non esiste non misura «un po'
        #    meno»: misura un'altra cosa.  ⇒ si dichiara assente.
        return {"ok": None, "applicabile": False, "rapporti": None,
                "ragione": ("⚠ NON APPLICABILE: la scena non e' la mira, quindi "
                            "non ha i tre riquadri a luminanza uguale "
                            "((87,0,0)·(0,26,0)·(0,0,255)) su cui questo "
                            "strumento e' tarato.  ⛔ E la conseguenza va letta: "
                            "questo giro NON vede il guasto «piani del colore "
                            "scambiati» — che non muove la luminanza di un LSB, "
                            "quindi M1a, M2 e M3 lo PROMUOVEREBBERO tutti e "
                            "tre.  ⛔ Su una scena naturale non si ripiega "
                            "sull'immagine intera: li' R, G e B sono gia' "
                            "correlati a 0,978 e lo strumento direbbe rosso su "
                            "una catena sana")}
    idx = []
    for z in zone["colori"].values():
        yy, xx = np.mgrid[z["y"]:z["y"] + z["h"], z["x"]:z["x"] + z["w"]]
        idx.append((yy.ravel(), xx.ravel()))
    ys = np.concatenate([a for a, _ in idx])
    xs = np.concatenate([b for _, b in idx])
    M = np.zeros((3, 3))
    for i in range(3):
        a = pag[ys, xs, i]
        for j in range(3):
            d = a - rif[ys, xs, j]
            M[i, j] = float(np.mean(d * d)) + 1e-12
    nomi = "RGB"
    guasti = []
    rapporti = []
    for i in range(3):
        riga = M[i].copy()
        mio = riga[i]
        riga[i] = 1e9
        migliore = int(riga.argmin())
        r = riga[migliore] / mio
        rapporti.append(round(float(r), 2))
        if r < 4.0:
            guasti.append("il canale %s della pagina non e' piu' vicino al "
                          "proprio (errore %.3g) che al canale %s del "
                          "riferimento (%.3g): rapporto %.2f, serve ≥ 4"
                          % (nomi[i], mio, nomi[migliore], riga[migliore], r))
    ok = not guasti
    return {"ok": ok, "rapporti": rapporti,
            "ragione": None if ok else
            ("⛔ I PIANI DEL COLORE SONO SCAMBIATI: " + " · ".join(guasti) +
             ".  ⚠ E questo guasto NON muove la luminanza: i tre riquadri della "
             "mira hanno la stessa Y apposta, quindi M1a, M2 e M3 lo "
             "promuoverebbero tutti e tre")}


def m5_gamma(pag, rif):
    fuori = []
    det = []
    lo, hi = SOGLIE["M5_guadagno"]
    for i, nome in enumerate("RGB"):
        x = rif[:, :, i].ravel()
        y = pag[:, :, i].ravel()
        vx = float(np.var(x))
        if vx < 1e-9:
            det.append({"canale": nome, "guadagno": None, "scarto": None})
            continue
        g = float(np.cov(x, y, bias=True)[0, 1] / vx)
        s = float(y.mean() - g * x.mean())
        det.append({"canale": nome, "guadagno": round(g, 4),
                    "scarto_su255": round(s * 255, 2)})
        if not (lo <= g <= hi) or abs(s) > SOGLIE["M5_scarto"]:
            fuori.append("%s: guadagno %.4f, scarto %.2f/255" % (nome, g, s * 255))
    ok = not fuori
    return {"ok": ok, "canali": det,
            "ragione": None if ok else
            ("⛔ la trasformazione fra riferimento e pagina non e' l'identita': "
             + " · ".join(fuori) + ".  Firme note: guadagno ≈ 1,164 = gamma "
             "LIMITATA letta come piena (255/219); scarti di segno opposto sui "
             "canali = matrice BT.601 letta come BT.709.  ⚠ In tutt'e due i casi "
             "la causa probabile e' un VUI non scritto dal codificatore: il "
             "browser allora INDOVINA")}


def m6_freschezza(pag, cat, cat_prec):
    if cat_prec is None:
        return {"ok": None, "ragione": "⛔ non misurata: manca la cattura del "
                "giro precedente.  ⚠ E senza, «il fotogramma e' del giro "
                "prima» e' un guasto che NESSUN altro strumento vede"}
    a = psnr_num(luma(pag), luma(cat))
    b = psnr_num(luma(pag), luma(cat_prec))
    d = a - b
    ok = d >= SOGLIE["M6_db"]
    return {"ok": bool(ok), "psnr_ora_db": round(a, 2), "psnr_prima_db": round(b, 2),
            "delta_db": round(d, 2),
            "ragione": None if ok else
            ("⛔ IL FOTOGRAMMA E' VECCHIO: somiglia alla cattura di ADESSO per "
             "%.2f dB e a quella di PRIMA per %.2f dB (margine %.2f, serve "
             "≥ %.1f).  ⚠ Se i due numeri sono quasi uguali il guasto puo' non "
             "esserci: puo' essere la SCENA che non si e' mossa fra i due giri, "
             "e allora e' il banco a essere rotto, non il prodotto"
             % (a, b, d, SOGLIE["M6_db"]))}


def carica_y10(percorso, larghezza, altezza):
    """Il piano Y di un `yuv420p10le` grezzo, in codici 0..1023."""
    dati = open(percorso, "rb").read()
    atteso = larghezza * altezza * 2
    if len(dati) < atteso:
        raise Mancante("riferimento-10: %d byte, ne servivano almeno %d per il "
                       "piano Y di un %dx%d yuv420p10le"
                       % (len(dati), atteso, larghezza, altezza))
    return np.frombuffer(dati[:atteso], "<u2").reshape(altezza, larghezza)


def residuo_rampa(y10, z):
    """RMS dello scarto dalla retta, sulle medie di riga.  ⚠ INDICATIVO."""
    blk = y10[z["y"]:z["y"] + z["h"], z["x"]:z["x"] + z["w"]].astype(np.float64)
    rm = blk.mean(axis=1)
    t = np.arange(len(rm))
    A = np.polyfit(t, rm, 1)
    return float(np.std(rm - np.polyval(A, t)))


def m7_profondita(percorso_y10, larghezza, altezza, zone, prof_disp, mira=True):
    """⛔ La profondita' NON si legge dal confronto dei pixel su una tela a 8 bit.

    ⭐ LO STRUMENTO DECISIVO SONO **I DUE BIT BASSI**, e non era quello che il
       rapporto S2 proponeva.

    `web/rapporti/S2-decodifica.md` §3.7 punto 2 propone di contare le **bande**
    su due rampe, una a 10 bit e una gia' quantizzata a 8.  ⛔ Misurato il 12
    agosto 2026: **quella prova non sopravvive alla codifica con perdita.**
    Prima di codificare, lo scarto dalla retta vale 0,289 sulla rampa a 10 bit
    e 1,193 su quella a 8 — rapporto **4,13**, cioe' quel che S2 si aspetta.
    Dopo un `libx265` Main10 a QP 20 diventano 0,604 e 0,792: rapporto **1,31**.
    Il codificatore **liscia la scaletta**, cioe' cancella proprio il segnale su
    cui la prova poggia.  Una soglia a 2,5 boccerebbe ogni giro sano.

    ⇒ Qui la domanda si fa in un altro modo, che il codificatore non cancella:
      **la distribuzione dei due bit bassi del piano Y decodificato.**
      · una catena a 10 bit li usa tutti e quattro, ≈ un quarto ciascuno;
      · una catena che tronca a 8 e ri-espande li concentra in **uno o due**
        valori, per costruzione.
      Misurato lo stesso giorno: sano [0,260 0,245 0,254 0,241] · troncato con
      `>>2<<2` → [1 0 0 0] · troncato e riscalato → [0,629 0 0 0,371].
      ⇒ SOGLIE: frazione massima ≤ **0,50** e tutte e quattro le caselle ≥ 0,05.
      Lo 0,50 non e' scelto a occhio: e' **il confine esatto** fra «almeno tre
      caselle portano informazione» e «al massimo due», che e' la firma
      aritmetica del troncamento.

    ⚠ E si legge sul **piano Y in YUV**, non sull'RGB: la conversione di colore
      rimescola i bit bassi e cancellerebbe la firma.

    ===================================================================
    ⛔⛔ E CHE COSA QUESTO STRUMENTO **NON** DIMOSTRA IN FASE 2 — cucitura
        di F2.2, 12 agosto 2026, e cambia l'atteso alla radice.

    **La sorgente da' OTTO bit, misurati.**  Mutter consegna solo BGRx/BGRA:
    1920×1080, stride 7680, 8 294 400 byte, e il conto anti-8-bit fatto alla
    cattura da' 255/256/255 livelli distinti e multipli di 4 a 0,259/0,259/0,249
    ⇒ otto bit veri, senza dubbio.

    ⇒ **In fase 2 il Main10 porta 8 bit PROMOSSI**, e l'atteso di M7 e'
      esattamente quello.  Da cui due conseguenze che vanno scritte o il
      prossimo che legge questo numero lo capisce al contrario:

      1. ⛔ M7 **non dimostra i 10 bit veri**, e non puo': non ci sono nella
         sorgente.  Serve a smascherare una **perdita in PIU'** lungo la
         catena — un anello che tronca a 8 quel che gli e' arrivato a 10.
         L'assenza dei 10 bit veri sta **a monte**, ha gia' un nome (la
         cattura BGRx) e non e' un difetto di questa catena;
      2. ⛔ un rosso di M7 in fase 2 **ha un imputato preciso**: non «mancano
         i 10 bit», ma «qualcuno fra il codificatore e la tela ha buttato via
         i due bit bassi».

    ⭐ E il fatto che questo regga e' `[M]`, non dedotto: 12 agosto 2026,
      sorgente a 8 bit → libx265 Main10 → decodifica, i due bit bassi del
      piano Y sulla sfumatura danno **0,249 a gamma piena e 0,259 a gamma
      limitata** — uniformi.  La conversione RGB→YUV e il rumore di codifica
      li rimescolano, quindi una catena sana con sorgente a 8 bit **passa**,
      e solo un troncamento vero li concentra.

    ⇒ La domanda «10 bit VERI» resta viva in due soli posti, e nessuno dei due
      e' questo banco: **il telefono** (S2, `02-giudizio-telefono.sh`) e la
      strada **DMA-BUF**, che F2.2 dichiara non provata.
    """
    e = {"lato_nostro": None, "lato_dispositivo": None}
    if not mira:
        # ⛔ La nota misurata qui sopra dice perche' non si ripiega su una zona
        #    qualunque: su una zona PIATTA i due bit bassi si concentrano al
        #    95 % e M7 direbbe «troncato» su una catena sana (`[M]` 0,954).  Una
        #    scena naturale non garantisce nessuna zona sfumata dichiarata.
        e["lato_nostro"] = {"ok": None, "applicabile": False, "ragione":
                            "⚠ NON APPLICABILE: la scena non e' la mira e non "
                            "dichiara nessuna zona sfumata.  ⛔ E non si ripiega "
                            "su una zona qualunque: su una zona piatta i due "
                            "bit bassi si concentrano al 95 % e questo "
                            "strumento direbbe «troncato» su una catena sana "
                            "(`[M]` 0,954, 12 agosto 2026).  ⇒ questo giro NON "
                            "vede il guasto «8 bit al posto di 10», che il PSNR "
                            "da solo promuove restando sopra i 55 dB"}
    elif percorso_y10 is None:
        e["lato_nostro"] = {"ok": None, "ragione":
                            "⛔ non misurata: manca --riferimento-10, cioe' il "
                            "piano Y `yuv420p10le` grezzo della decodifica di "
                            "riferimento.  Senza, «i 10 bit ci sono» non e' una "
                            "misura: e' una speranza"}
    else:
        y10 = carica_y10(percorso_y10, larghezza, altezza)
        # ⛔ SOLO SULLE ZONE SFUMATE, e non e' un dettaglio: vedi la nota
        #    misurata nell'intestazione della funzione.  Su una zona piatta i
        #    due bit bassi si concentrano al 95 %, e M7 direbbe «troncato» su
        #    una catena sana.
        campioni = []
        for nome in ("sfumatura", "rampa10"):
            z = zone.get(nome)
            if not z:
                continue
            campioni.append(y10[z["y"]:z["y"] + z["h"],
                                z["x"]:z["x"] + z["w"]].ravel())
        if not campioni:
            raise Mancante(
                "⛔ la scena non dichiara nessuna zona sfumata («sfumatura» o "
                "«rampa10»).  La profondita' NON si conta sulle zone piatte: "
                "li' i livelli distinti sono una ventina per costruzione e il "
                "controllo direbbe «8 bit» su qualunque cosa (cucitura F2.2)")
        campione = np.concatenate(campioni)
        bassi = np.bincount((campione & 3).ravel(), minlength=4) / campione.size
        massima = float(bassi.max())
        minima = float(bassi.min())
        # ⭐ CONVERGENZA CON F2.3, 12 agosto 2026.  La codifica ha misurato, sul
        #    suo lato e senza sapere che cosa facevo qui, gli stessi due numeri:
        #      10 bit veri     → 877 livelli distinti · 0,25 di multipli di 4
        #      passato per 8   → 220 livelli distinti · 1,000 di multipli di 4
        #    «multipli di 4» e' esattamente la prima casella dei due bit bassi.
        #    ⇒ la soglia di 0,50 sta a meta' fra i due valori MISURATI da due
        #      strumenti diversi, non fra due valori dedotti.  E i livelli
        #      distinti si riportano accanto, come secondo numero indipendente.
        livelli = int(len(np.unique(campione)))
        ok = massima <= SOGLIE["M7_bit_bassi_max"] and minima >= SOGLIE["M7_bit_bassi_min"]
        r10 = residuo_rampa(y10, zone["rampa10"])
        r8 = residuo_rampa(y10, zone["rampa8"])
        e["lato_nostro"] = {
            "ok": bool(ok),
            "bit_bassi": [round(float(v), 4) for v in bassi],
            "multipli_di_4": round(float(bassi[0]), 4),
            "livelli_distinti_y": livelli,
            "frazione_massima": round(massima, 4),
            "rampa_residuo10": round(r10, 3), "rampa_residuo8": round(r8, 3),
            "rampa_rapporto": round(r8 / max(r10, 1e-9), 2),
            "ragione": None if ok else
            ("⛔ I 10 BIT SONO STATI TRONCATI: i due bit bassi del piano Y "
             "decodificato valgono %s — la casella piu' piena e' al %.1f %% "
             "(ammesso ≤ %.0f %%) e la piu' vuota al %.1f %% (serve ≥ %.0f %%). "
             "Una catena a 10 bit li usa tutti e quattro a un quarto ciascuno; "
             "una che tronca a 8 li concentra in una o due caselle"
             % (list(np.round(bassi, 3)), massima * 100,
                SOGLIE["M7_bit_bassi_max"] * 100, minima * 100,
                SOGLIE["M7_bit_bassi_min"] * 100))}
    if prof_disp is None:
        e["lato_dispositivo"] = {"ok": None, "ragione":
            "⛔ NON MISURABILE su questo dispositivo, e non e' una "
            "dimenticanza: la tela 2D e' a 8 bit per canale, e fra un valore "
            "a 10 bit e lo stesso troncato a 8 ci passa al massimo UN LSB "
            "dopo la conversione — nessun confronto di pixel su getImageData "
            "puo' distinguerli.  ⛔ Dire «10 bit ok» perche' i pixel "
            "coincidono sarebbe la forma E1.  I canali che rispondono sono "
            "VideoFrame.format/copyTo() dove esiste, e la decodifica di "
            "riferimento fuori dal browser"}
    else:
        f = prof_disp.get("format")
        ok = f in ("I420P10", "I422P10", "I444P10", "P010")
        e["lato_dispositivo"] = {
            "ok": bool(ok) if f is not None else None,
            "format": f, "copyTo": prof_disp.get("copyTo"),
            "ragione": None if ok else
            ("⛔ VideoFrame.format vale «%s»: %s" % (
                f, "su Chrome il fotogramma decodificato in HARDWARE espone "
                   "format = null e nega copyTo() [S] — da qui non si sa se i "
                   "10 bit ci sono, e il metro NON promuove" if f in (None, "null")
                else "non e' un formato a 10 bit"))}
    # ⛔ L'aggregato non e' un `and` fra due booleani: `None` vuol dire «non ho
    #    potuto guardare», e un `and` lo tratterebbe come un si'.  La prima
    #    stesura faceva `is not False`, cioe' PROMUOVEVA un giro senza
    #    `--riferimento-10` — il modo piu' silenzioso di perdere la domanda
    #    dei 10 bit.
    ln, ld = e["lato_nostro"].get("ok"), e["lato_dispositivo"].get("ok")
    if ln is False or ld is False:
        e["ok"] = False
    elif not mira:
        # ⛔ «non applicabile per costruzione» e «manca l'ingresso» sono due
        #    cose diverse, e il metro le tiene separate apposta: la prima si
        #    DICHIARA, la seconda SOSPENDE il verdetto.  Confonderle e' il modo
        #    in cui una misura mancante diventa un promosso.
        e["ok"] = None
        e["applicabile"] = False
        e["ragione"] = e["lato_nostro"]["ragione"]
    elif ln is None:
        e["ok"] = None          # manca l'ingresso: sospeso, non promosso
    else:
        e["ok"] = True
        # ⚠ il lato dispositivo puo' restare None: e' un limite dichiarato del
        #   browser, non un ingresso mancante.  Sta scritto nel rapporto.
        e["applicabile_dispositivo"] = ld is not None
    return e


def m8_identita(percorso, giro):
    """M8 — il fotogramma dipinto e' quello che il filo ha CONSEGNATO?

    ⛔ CUCITURA DI F2.4, E VA LETTA INSIEME AL SUO LIMITE.
    F2.4: *«FIN ⇒ fotogramma completo, RESET ⇒ si butta e non si consegna.  Un
    fotogramma consegnato dopo un RESET e' un guasto.»*

    ⛔ **Questo guasto il confronto dei pixel NON LO VEDE, e va detto invece di
    lasciarlo credere.**  I pixel non portano l'identita' dello stream da cui
    vengono: un fotogramma abbandonato con `RESET_STREAM` e dipinto lo stesso
    puo' avere **i pixel giusti**, e allora M0..M7 lo promuovono tutti — a
    ragione, perche' stanno rispondendo a un'altra domanda.

    Delle due forme in cui quel guasto si presenta:
      · il fotogramma abbandonato e' quello di **un giro diverso** ⇒ lo prende
        **M6** (freschezza), ed e' l'unico caso in cui i pixel bastano;
      · il fotogramma abbandonato ha **lo stesso contenuto** ⇒ ⛔ nessun metro
        di pixel puo' obiettare.  Lo deve vedere il validatore di F2.4, e qui
        si legge la sua dichiarazione.

    ⇒ M8 non misura pixel: **legge quel che la pagina dichiara di aver
      dipinto** e lo confronta con il giro in corso.  E' un anello debole per
      costruzione — crede a chi e' sotto esame — e per questo vale solo
      insieme al registro di F2.4, non al posto suo.  Senza il file, M8 si
      dichiara non misurato e stampa di chi e' la cucitura.

    ⛔⭐ E OGNI CONTROLLO SI CONTA UNO PER UNO — la cura del 13 agosto 2026.

    Prima, i tre controlli stavano in fila e l'esito era `ok = not guasti`.
    ⛔ Un controllo che **non poteva scattare** era indistinguibile da un
    controllo passato: `giro = None` saltava il confronto, `fin_ricevuto`
    aveva `True` come valore di ripiego, e `reset_ricevuto` arrivava da un
    contatore che non esisteva.  Tre controlli spenti facevano `ok = True`, e
    il metro contava M8 fra gli **strumenti vivi** (`ok is not None`),
    portandosi dietro il «12 guasti su 12» della catena vera.  I vivi erano 11.

    ⇒ Adesso ogni controllo ha tre stati — **passato / scattato / non
      eseguito** — e sono tenuti separati:
        · se nessuno dei tre si e' potuto eseguire, M8 esce `ok: None,
          applicabile: False` ⇒ NON e' vivo, e il guasto `dopo-reset` si conta
          fra i CIECHI di quel giro invece di sparire in un verde;
        · quali sono stati eseguiti sta scritto nel rapporto, sempre, anche
          nei giri verdi.
    """
    if percorso is None:
        return {"ok": None, "applicabile": False,
                "ragione": ("⚠ non misurata: manca --identita-pagina.  ⛔ Il "
                            "confronto dei pixel NON vede un fotogramma "
                            "consegnato dopo un RESET quando i pixel sono "
                            "giusti: quella meta' e' del validatore di F2.4, e "
                            "qui resta un buco DICHIARATO invece che un verde")}
    try:
        d = json.load(open(percorso))
    except Exception as e:                       # noqa: BLE001
        return {"ok": None, "applicabile": False,
                "ragione": "--identita-pagina non si legge: %s" % e}

    # ⛔⛔ IL NOME RITIRATO, RIFIUTATO A VOCE ALTA.  `reset_ricevuto` voleva
    #     dire «e' arrivato un RESET_STREAM» (cioe' `conti.azzerati`), e M8 lo
    #     leggeva come «un fotogramma e' stato dipinto DOPO un RESET»: due
    #     grandezze sotto un nome solo, che e' la forma esatta del difetto
    #     pagato due volte il 13 agosto 2026.  ⇒ Chi scrive ancora quel nome
    #     non riceve un verde e non riceve un rosso: riceve un rifiuto che dice
    #     come si chiama adesso.  ⚠ Tacere e leggere il campo nuovo mancante
    #     come «non applicabile» avrebbe fatto scivolare un chiamante rimasto
    #     indietro dentro un giro con M8 spento e nessuno che se ne accorge.
    if "reset_ricevuto" in d:
        return {"ok": None, "applicabile": False, "dichiarato": d,
                "ragione": ("⛔ «%s» porta il campo RITIRATO `reset_ricevuto`.  "
                            "Quel nome diceva «e' arrivato un RESET» (= "
                            "`conti.azzerati`, che su una catena SANA e' > 0 "
                            "ogni volta che il server azzera uno stream e la "
                            "pagina lo butta bene), mentre M8 chiede «un "
                            "fotogramma e' stato DIPINTO dopo un RESET».  Il "
                            "campo si chiama adesso `dipinto_dopo_reset` e la "
                            "grandezza vera e' `consegnati > completi`.  ⇒ Chi "
                            "ha scritto questo file va aggiornato: qui non si "
                            "indovina." % percorso)}

    # nome -> True (passato) · False (scattato) · None (non eseguibile)
    controlli = {}
    perche = dict(d.get("non_applicabile") or {})
    guasti = []

    def salta(nome, ragione):
        controlli[nome] = None
        perche.setdefault(nome, ragione)

    # ── 1. il fotogramma DIPINTO DOPO UN RESET ────────────────────────────
    v = d.get("dipinto_dopo_reset")
    if v is None:
        salta("dipinto_dopo_reset",
              "⛔ non dichiarato da chi ha scritto il file: M8 non finge di "
              "averlo guardato.")
    elif v:
        controlli["dipinto_dopo_reset"] = False
        guasti.append("un fotogramma e' stato CONSEGNATO al decodificatore "
                      "senza che il suo stream fosse completo: F2.4 dice che "
                      "uno stream azzerato si butta e NON si consegna (§6.2)"
                      + (" — i conti della pagina: %s"
                         % {k: (d.get("conti") or {}).get(k)
                            for k in ("stream", "completi", "azzerati",
                                      "consegnati", "dipinti")}
                         if d.get("conti") else ""))
    else:
        controlli["dipinto_dopo_reset"] = True

    # ── 2. il FIN ─────────────────────────────────────────────────────────
    # ⚠ Il controllo e' «ha DIPINTO senza aver visto il FIN»: senza `dipinto`
    #   non e' la stessa domanda, e un `fin_ricevuto` falso su una pagina che
    #   non ha dipinto niente sarebbe un rosso di un guasto che non c'e'.
    fin = d.get("fin_ricevuto")
    if fin is None:
        salta("fin_ricevuto",
              "⛔ non dichiarato da chi ha scritto il file.  ⚠ E il valore di "
              "ripiego `True` che c'era qui era una costante che faceva "
              "passare: e' stato tolto.")
    elif d.get("dipinto") and not fin:
        controlli["fin_ricevuto"] = False
        guasti.append("la pagina ha dipinto senza aver visto il FIN: il "
                      "fotogramma non era dichiarato completo")
    else:
        controlli["fin_ricevuto"] = True

    # ── 3. il giro ────────────────────────────────────────────────────────
    if d.get("giro") is None:
        salta("giro",
              "⛔ chi ha scritto il file non dichiara nessun giro.  ⚠ E «None» "
              "non vuol dire «coincide»: il confronto NON e' stato fatto.")
    elif str(d["giro"]) != str(giro):
        controlli["giro"] = False
        guasti.append("la pagina dichiara il giro «%s», il banco sta girando "
                      "«%s»" % (d["giro"], giro))
    else:
        controlli["giro"] = True

    fatti = [k for k, v in controlli.items() if v is not None]
    if not fatti:
        return {"ok": None, "applicabile": False, "controlli": controlli,
                "dichiarato": d, "non_applicabile": perche,
                "ragione": ("⛔ NESSUNO dei tre controlli di M8 e' eseguibile "
                            "su questo giro ⇒ M8 non e' uno strumento vivo qui, "
                            "e il guasto «dopo-reset» va contato fra i CIECHI. "
                            "⚠ Un M8 verde su zero controlli e' esattamente il "
                            "falso verde del 13 agosto 2026.  · "
                            + " · ".join("%s: %s" % (k, perche.get(k))
                                         for k in sorted(controlli)))}
    ok = not guasti
    return {"ok": ok, "controlli": controlli, "dichiarato": d,
            "non_applicabile": {k: perche.get(k) for k in sorted(controlli)
                                if controlli[k] is None},
            "ragione": None if ok else "⛔ " + " · ".join(guasti)}


# ───────────────────────────────────────────────────────────────────────────
# ⛔ C2 — il controllo positivo in coda: lo strumento sa bocciare?
# ───────────────────────────────────────────────────────────────────────────
def controllo_positivo(pag, rif, zone, mira=True):
    """⛔ Il guasto si innesta sul RIFERIMENTO, non sulla pagina.

    La prima stesura lo innestava sulla **pagina**, ed e' stata smascherata
    dalla certificazione stessa (12 agosto 2026): sul guasto «piani scambiati»
    il controllo scambiava di nuovo i piani di una pagina gia' scambiata, li
    **rimetteva a posto**, e il metro si dichiarava rotto (stato 3) su un giro
    in cui stava facendo esattamente il suo mestiere.  ⛔ Un controllo che
    poggia sull'imputato non e' un controllo.

    ⚠ E si dichiara che cosa questo controllo NON prova: gira su una coppia
      pulita (riferimento contro riferimento guasto), quindi dimostra che lo
      strumento **sa bocciare**, non che sappia bocciare a quel livello di
      rumore di codifica.  La sensibilita' al rumore vero la dimostra la
      certificazione con i guasti — che gira sulla coppia vera — e le due
      cose stanno insieme, non una al posto dell'altra.
    """
    esiti = {}
    finta = np.roll(rif, 1, axis=0)
    esiti["scorrimento_di_una_riga"] = not m0_allineamento(finta, rif)["ok"]
    finta = rif.copy()
    h, w = finta.shape[:2]
    y0, x0 = h // 2 & ~63, w // 2 & ~63
    finta[y0:y0 + 64, x0:x0 + 64, :] = 0.0
    esiti["blocco_64_azzerato"] = not m3_blocco_peggiore(finta, rif)["ok"]
    # ⛔⭐ E LA TERZA PROVA NON SI DICHIARA PASSATA QUANDO NON PUO' GIRARE.
    #    Con `mira=False` M4 non esiste (non ci sono i tre riquadri), e un
    #    `not None` avrebbe fatto risultare la prova **superata**: il controllo
    #    che deve dimostrare che il metro sa bocciare si sarebbe promosso da
    #    solo, sullo strumento che in quel giro e' spento.  ⇒ si toglie
    #    dall'elenco delle prove e si dichiara.
    if mira:
        finta = rif[:, :, ::-1].copy()
        esiti["piani_scambiati"] = not m4_canali(finta, rif, zone)["ok"]
    # ⛔ e il rovescio, che e' l'altra meta' del controllo: sulla coppia SANA
    #    (riferimento contro se stesso) gli stessi strumenti devono dire di si'.
    #    Uno strumento che dice no sempre non e' uno strumento.
    esiti["e_sul_sano_dicono_si"] = bool(
        m0_allineamento(rif, rif)["ok"] and
        m3_blocco_peggiore(rif, rif)["ok"] and
        (m4_canali(rif, rif, zone)["ok"] if mira else True))
    ok = all(esiti.values())
    fuori = {"ok": ok, "prove": esiti,
             "ragione": None if ok else
             ("⛔⛔ IL METRO E' ROTTO: gli sono stati innestati in memoria dei "
              "guasti che DEVE vedere, e non li ha visti: %s.  Il verdetto di "
              "questo giro NON VALE — non e' un promosso, non e' un bocciato"
              % [k for k, v in esiti.items() if not v])}
    if not mira:
        fuori["non_provati"] = {
            "piani_scambiati": "⚠ non provato: M4 e' spento su una scena che "
                               "non e' la mira, e una prova che non gira non "
                               "e' una prova passata"}
    return fuori


# ───────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scena", required=True, help="il JSON della mira")
    p.add_argument("--cattura", required=True)
    p.add_argument("--riferimento", required=True)
    p.add_argument("--pagina", required=True)
    p.add_argument("--cattura-precedente")
    p.add_argument("--riferimento-10")
    p.add_argument("--profondita-dispositivo")
    p.add_argument("--colore", help="⛔ il JSON che dichiara matrice, gamma e "
                                    "primarie delle tre parti (cucitura F2.3)")
    p.add_argument("--identita-pagina", help="⚠ quel che la pagina dichiara di "
                                             "aver dipinto (cucitura F2.4)")
    p.add_argument("--giro", default="senza-nome")
    p.add_argument("--scena-nome", default="mira-remotix-f2.6")
    p.add_argument("--esiti")
    p.add_argument("--senza-freschezza", action="store_true",
                   help="⚠ dichiara di NON misurare M6.  Il giro esce con "
                        "stato 2, non con un promosso")
    a = p.parse_args()

    # ⛔⭐ UNA FACOLTATIVA PASSATA VUOTA E' UNA FACOLTATIVA NON PASSATA — e la
    #     riga che lo dichiara vale, perche' senza di lei chi chiama e'
    #     costretto a costruire la riga di comando a pezzi.
    #
    # `[M]` 12 agosto 2026, lacuna L3.  `02-giudizio-confronto.sh giudica`
    # inoltrava `"$@"` al metro, e nessun file del deposito diceva che cosa ci
    # fosse dentro: `01-b0-chiamate.py` non poteva giudicare quella chiamata, e
    # la stessa cucitura era gia' costata un rosso su B6 (10 agosto) e uno su
    # B7 (11 agosto).  ⇒ Adesso quel ramo scrive **tutte** le opzioni per nome,
    # e quelle che l'utente non ha dato le scrive vuote.
    #
    # ⚠ E vale SOLO per le facoltative.  I quattro obbligatori restano
    #   `required=True`: `--cattura ""` non diventa «non passato», arriva a
    #   `carica()` e si ferma con «il file non esiste — «»».  ⛔ Se «vuoto»
    #   valesse «non passato» anche li', un ingresso perso in una variabile di
    #   shell mai assegnata avrebbe la faccia di una scelta — che e' la forma
    #   E8 (`REVIEWER.md` §2), rimessa dentro dalla porta di servizio.
    for _facoltativa in ("cattura_precedente", "riferimento_10",
                         "profondita_dispositivo", "colore",
                         "identita_pagina", "esiti"):
        if getattr(a, _facoltativa) == "":
            setattr(a, _facoltativa, None)

    def log(s=""):
        print(s)

    R = {"ora": datetime.datetime.now().isoformat(timespec="seconds"),
         "giro": a.giro, "scena": a.scena_nome, "strumento": "02-giudizio-metro.py",
         "soglie": {k: v for k, v in SOGLIE.items()}}

    try:
        meta = json.load(open(a.scena))
    except Exception as e:                       # noqa: BLE001
        print("%s⛔ la scena non si legge: %s%s" % (ROSSO, e, GRIGIO))
        return 2
    W, H = meta["larghezza"], meta["altezza"]
    zone = meta["zone"]
    # ⛔⭐ LA SCENA DICHIARA SE E' LA MIRA — e il valore di riposo e' `true`.
    #    Una scena che non lo dice e' la mira: cosi' una scena naturale deve
    #    dichiararsi, e nessun giro perde tre strumenti per una chiave
    #    dimenticata.  ⚠ E' la stessa forma di `--senza-freschezza`: il limite
    #    lo chiede chi misura, non lo concede il metro da solo.
    mira = bool(meta.get("mira", True))
    R["larghezza"], R["altezza"] = W, H
    R["mira"] = mira

    # ── C1: il canale di lettura ────────────────────────────────────────
    log("\n\033[1m== C1 · il canale di lettura — che cosa sto guardando davvero\033[0m")
    ingressi = {"cattura": a.cattura, "riferimento": a.riferimento,
                "pagina": a.pagina, "cattura_precedente": a.cattura_precedente}
    letti, impronte = {}, {}
    profondita_pagina = 8
    try:
        # ⛔ `--riferimento-10` non passa di qui: e' un `yuv420p10le` grezzo, e
        #    va letto come piano Y a 10 bit, non come RGB.  Ma la sua esistenza
        #    e la sua impronta si stampano lo stesso, perche' un ingresso che
        #    non si vede non e' un ingresso.
        if a.riferimento_10:
            if not os.path.exists(a.riferimento_10):
                raise Mancante("riferimento_10: il file non esiste — «%s»"
                               % a.riferimento_10)
            st = os.stat(a.riferimento_10)
            imp = hashlib.sha256(open(a.riferimento_10, "rb").read()).hexdigest()[:16]
            log("    --  %-20s %8d B  sha %s  %s  (yuv420p10le)"
                % ("riferimento_10", st.st_size, imp,
                   os.path.basename(a.riferimento_10)))
        for nome, perc in ingressi.items():
            img, prof, imp = carica(perc, W, H, nome)
            letti[nome] = img
            if nome == "pagina" and prof is not None:
                profondita_pagina = prof
            if img is not None:
                impronte[nome] = imp
                st = os.stat(perc)
                log("    --  %-20s %8d B  sha %s  %s  (%d bit)"
                    % (nome, st.st_size, imp, os.path.basename(perc), prof))
            else:
                log("    --  %-20s ⚠ non passato" % nome)
    except Mancante as e:
        log("    %sNO%s  %s" % (ROSSO, GRIGIO, e))
        log("    ⛔ stato 2: NON MISURATO.  Non e' un bocciato.")
        R["esito"] = "non-misurato"
        R["ragione"] = str(e)
        scrivi(a.esiti, R)
        return 2

    # ⛔ Il controllo vale fra gli ingressi che vengono CONFRONTATI fra loro.
    #    `riferimento_10` non e' confrontato con nessuno — e' letto solo per
    #    contare i livelli delle due rampe — e nella catena normale **e'
    #    legittimamente lo stesso file** del riferimento: metterlo qui dentro
    #    fermerebbe ogni giro sano, che e' il modo piu' rapido di far
    #    disattivare un controllo.
    doppi = {}
    for n, i in impronte.items():
        if n == "riferimento_10":
            continue
        doppi.setdefault(i, []).append(n)
    dupl = [v for v in doppi.values() if len(v) > 1]
    if dupl:
        log("    %sNO%s  ⛔ due ingressi sono LO STESSO FILE: %s" % (ROSSO, GRIGIO, dupl))
        log("        Confrontare un file con se stesso da' PSNR infinito, cioe'")
        log("        un verde regalato.  Il metro si ferma: stato 2.")
        R["esito"] = "non-misurato"
        R["ragione"] = "ingressi duplicati: %s" % dupl
        scrivi(a.esiti, R)
        return 2
    log("    %sOK%s  %d ingressi distinti, letti e con l'impronta stampata"
        % (VERDE, GRIGIO, len(impronte)))

    # ── M-C: la seconda porta — il colore dichiarato ────────────────────
    log("\n\033[1m== M-C · matrice e gamma dichiarate (⛔ senza, si misura la matrice)\033[0m")
    try:
        R["MC"] = mc_colore(a.colore)
    except Mancante as e:
        log("    %sNO%s  %s" % (ROSSO, GRIGIO, e))
        log("    ⛔ stato 2: NON MISURATO.  Non e' un bocciato.")
        R["esito"] = "non-misurato"
        R["ragione"] = str(e)
        scrivi(a.esiti, R)
        return 2
    if not R["MC"]["ok"]:
        log("    %sNO%s  %s" % (ROSSO, GRIGIO, R["MC"]["ragione"]))
        R["esito"] = "bocciato"
        R["bocciati"] = ["M-C"]
        scrivi(a.esiti, R)
        return 1
    log("    %sOK%s  tutte e tre dichiarano %s"
        % (VERDE, GRIGIO, R["MC"]["dichiarato"]))

    cat, rif, pag = letti["cattura"], letti["riferimento"], letti["pagina"]
    prof_disp = None
    if a.profondita_dispositivo:
        try:
            prof_disp = json.load(open(a.profondita_dispositivo))
        except Exception as e:                   # noqa: BLE001
            log("    %sNO%s  la profondita' del dispositivo non si legge: %s"
                % (ROSSO, GRIGIO, e))
            R["esito"] = "non-misurato"
            scrivi(a.esiti, R)
            return 2

    # ── M-V: la porta ───────────────────────────────────────────────────
    log("\n\033[1m== M-V · la scena e' viva? (⛔ la porta: due neri hanno PSNR infinito)\033[0m")
    R["MV"] = {}
    if not mira:
        log("    %s—%s   ⚠ la scena dichiara «mira»: false — il desktop vero, non "
            "la mira di F2.6." % (GIALLO, GRIGIO))
        log("        ⛔ Restano in vigore deviazione e livelli (la guardia contro i")
        log("           due neri con PSNR infinito); i marcatori d'angolo NO.")
    for nome, img in (("cattura", cat), ("pagina", pag), ("riferimento", rif)):
        e = mv_vitalita(img, zone, nome, mira)
        R["MV"][nome] = e
        if e["ok"]:
            log("    %sOK%s  %-12s deviazione %.4f · %d livelli · marcatori al posto"
                % (VERDE, GRIGIO, nome, e["deviazione"], e["livelli"]))
        else:
            log("    %sNO%s  %s" % (ROSSO, GRIGIO, e["ragione"]))
    # ⛔ E QUI C'E' UNA DISTINZIONE CHE LA PRIMA STESURA NON FACEVA, e la
    #    faceva sbagliare di un grado: una scena morta **a monte** e una scena
    #    morta **a valle** non sono lo stesso esito.
    #
    #      · cattura o riferimento non vivi ⇒ ⛔ NON MISURATO (stato 2).  Non
    #        si puo' giudicare il client se quel che gli e' arrivato non c'e':
    #        e' il banco a essere rotto, non il prodotto.  E' il caso della
    #        sessione GNOME nera senza `--virtual-monitor`;
    #      · ⛔ **pagina non viva mentre la cattura lo e' ⇒ BOCCIATO** (stato 1).
    #        Qui la misura c'e' stata, e dice che il client ha dipinto il
    #        nulla — o l'ha dipinto ribaltato.  Chiamarlo «non misurato»
    #        sarebbe assolvere il difetto piu' grosso che questa fase possa
    #        avere.
    monte = [n for n in ("cattura", "riferimento") if not R["MV"][n]["ok"]]
    if monte:
        log("\n    ⛔ stato 2: NON MISURATO — la scena NON e' viva a MONTE (%s)."
            % ", ".join(monte))
        log("       Non si giudica il client su un ingresso che non c'e'.")
        R["esito"] = "non-misurato"
        R["ragione"] = "M-V a monte: %s" % ", ".join(monte)
        scrivi(a.esiti, R)
        return 2
    pagina_morta = not R["MV"]["pagina"]["ok"]

    # ── gli strumenti ───────────────────────────────────────────────────
    log("\n\033[1m== Gli strumenti\033[0m")
    R["M0"] = m0_allineamento(pag, rif)
    R["M1"] = m1_catena_pulita(pag, rif)
    R["M2"] = m2_catena_intera(pag, rif, cat, profondita_pagina)
    R["M3"] = m3_blocco_peggiore(pag, rif)
    R["M4"] = m4_canali(pag, rif, zone, mira)
    R["M5"] = m5_gamma(pag, rif)
    R["M6"] = m6_freschezza(pag, cat, letti["cattura_precedente"])
    try:
        R["M7"] = m7_profondita(a.riferimento_10, W, H, zone, prof_disp, mira)
    except Mancante as e:
        log("    %sNO%s  %s" % (ROSSO, GRIGIO, e))
        R["esito"] = "non-misurato"
        R["ragione"] = str(e)
        scrivi(a.esiti, R)
        return 2

    R["M8"] = m8_identita(a.identita_pagina, a.giro)
    etichette = {
        "M8": "identita' del fotogramma  cucitura F2.4",
        "M0": "allineamento           (0,0) il migliore",
        "M1": "catena senza perdita   pagina ⟷ riferimento",
        "M2": "catena intera          Δ sul riferimento",
        "M3": "blocco peggiore        64×64",
        "M4": "identita' dei canali   R,G,B",
        "M5": "guadagno e scarto      gamma e matrice",
        "M6": "freschezza             non e' il giro prima",
        "M7": "profondita'            10 bit, non 8",
    }
    bocciati, sospesi, dichiarati = [], [], []
    if pagina_morta:
        bocciati.append("M-V")
        log("    %sNO%s  M-V  la PAGINA non e' viva mentre la cattura lo e'"
            % (ROSSO, GRIGIO))
    for k in ("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"):
        e = R[k]
        ok = e.get("ok")
        misure = " ".join("%s=%s" % (kk, vv) for kk, vv in e.items()
                          if kk not in ("ok", "ragione", "correlazioni",
                                        "canali", "lato_nostro",
                                        "lato_dispositivo", "prove",
                                        # ⚠ M8: i suoi campi hanno una riga
                                        #   loro qui sotto, per esteso.
                                        "dichiarato", "controlli",
                                        "non_applicabile"))
        if ok is True:
            log("    %sOK%s  %s  %s  %s" % (VERDE, GRIGIO, k, etichette[k], misure))
        elif ok is False:
            log("    %sNO%s  %s  %s" % (ROSSO, GRIGIO, k, etichette[k]))
            bocciati.append(k)
        elif e.get("applicabile") is False:
            # ⛔ «non applicabile per costruzione» e «non ho l'ingresso» sono
            #    due cose diverse, e confonderle e' il modo in cui una misura
            #    mancante diventa un promosso.
            log("    %s—%s   %s  %s  ⚠ NON APPLICABILE  %s"
                % (GIALLO, GRIGIO, k, etichette[k], misure))
            dichiarati.append(k)
        else:
            log("    %s??%s  %s  %s  ⛔ NON MISURATO" % (GIALLO, GRIGIO, k, etichette[k]))
            sospesi.append(k)
        # ⛔⭐ M8 STAMPA I SUOI TRE CONTROLLI UNO PER UNO, ANCHE QUANDO E'
        #    VERDE.  E' la riga che il 13 agosto 2026 non c'era: con tre
        #    controlli spenti M8 stampava «OK» esattamente come con tre
        #    controlli passati, e da fuori le due cose erano lo stesso verde.
        #    ⇒ Un verde di M8 adesso dice **su che cosa** e' verde.
        if k == "M8" and e.get("controlli") is not None:
            for nome in sorted(e["controlli"]):
                v = e["controlli"][nome]
                seg = {True: VERDE + "OK" + GRIGIO,
                       False: ROSSO + "NO" + GRIGIO}.get(
                           v, GIALLO + "—" + GRIGIO + " ")
                coda = ("" if v is not None
                        else "  ⚠ NON ESEGUITO — %s"
                             % (e.get("non_applicabile") or {}).get(nome))
                log("          %s %s%s" % (seg, nome, coda))
        if k == "M7":
            for lato in ("lato_nostro", "lato_dispositivo"):
                sub = e[lato]
                seg = {True: VERDE + "OK" + GRIGIO, False: ROSSO + "NO" + GRIGIO}.get(
                    sub.get("ok"), GIALLO + "??" + GRIGIO)
                log("          %s %s: %s" % (seg, lato,
                    sub.get("ragione") or
                    ("i due bit bassi %s · ⚠ la prova delle bande di S2 §3.7 "
                     "dice %s (residui %s / %s) e NON e' un criterio: la "
                     "codifica con perdita liscia la scaletta"
                     % (sub.get("bit_bassi"), sub.get("rampa_rapporto"),
                        sub.get("rampa_residuo10"), sub.get("rampa_residuo8")))
                    if lato == "lato_nostro" else str(sub)))
            if e["lato_nostro"].get("ok") is False:
                bocciati.append("M7")

    for k in bocciati:
        if k == "M-V":
            log("\n    %sM-V%s  %s" % (ROSSO, GRIGIO, R["MV"]["pagina"]["ragione"]))
            continue
        r = R[k].get("ragione") or (R[k].get("lato_nostro") or {}).get("ragione")
        if r:
            log("\n    %s%s%s  %s" % (ROSSO, k, GRIGIO, r))

    # ⛔ SEMPRE stampato, anche nei giri verdi: che cosa questo giro NON ha
    #    giudicato.  Un limite che si legge solo quando fa comodo non e' un
    #    limite dichiarato.
    if dichiarati or sospesi or R["M7"]["lato_dispositivo"].get("ok") is None:
        log("\n\033[1m== ⛔ Che cosa questo giro NON ha potuto giudicare\033[0m")
        for k in dichiarati + sospesi:
            log("    ⚠ %s — %s" % (k, R[k].get("ragione")))
        if R["M7"]["lato_dispositivo"].get("ok") is None:
            log("    ⚠ M7/dispositivo — %s"
                % R["M7"]["lato_dispositivo"].get("ragione"))
    R["dichiarati"] = dichiarati

    # ── C2: il controllo positivo in coda ───────────────────────────────
    log("\n\033[1m== C2 · il controllo positivo — questo strumento sa BOCCIARE?\033[0m")
    R["C2"] = controllo_positivo(pag, rif, zone, mira)
    for nome, r in (R["C2"].get("non_provati") or {}).items():
        log("    %s—%s   guasto «%s» → %s" % (GIALLO, GRIGIO, nome, r))
    for nome, v in R["C2"]["prove"].items():
        log("    %s  guasto innestato in memoria «%s» → %s"
            % (VERDE + "OK" + GRIGIO if v else ROSSO + "NO" + GRIGIO, nome,
               "bocciato" if v else "⛔ PROMOSSO"))
    if not R["C2"]["ok"]:
        log("\n    %s" % R["C2"]["ragione"])
        R["esito"] = "metro-rotto"
        scrivi(a.esiti, R)
        return 3

    # ── ⛔⭐ I DODICI GUASTI, E QUANTI QUESTO GIRO NON AVREBBE VISTO ──────
    #
    # ⛔ Nato il 13 agosto 2026, col primo giro sulla catena VERA.  Il metro e'
    #    certificato «12 guasti su 12» — ⚠ ma quella cifra vale sulla MIRA.  Su
    #    una scena naturale tre strumenti sono spenti, e senza questa tabella il
    #    verdetto «PROMOSSO» si sarebbe portato dietro la cifra 12 di un giro
    #    che ne poteva vedere nove.  ⇒ Il conto si rifa' A OGNI GIRO, sugli
    #    strumenti VIVI in quel giro, invece di ricopiare un numero di ieri.
    CHI_PRENDE = {
        "nero":         ("M1", "M3"),
        "nero-doppio":  ("M-V",),
        "riga":         ("M0",),
        "colonna":      ("M0",),
        "precedente":   ("M6",),
        "otto-bit":     ("M7",),
        "piani":        ("M4",),
        "gamma":        ("M5",),
        "blocco":       ("M3",),
        "matrice":      ("M-C",),
        "dopo-reset":   ("M8",),
        "ribaltato":    ("M-V/marcatori",),
    }
    vivi = set()
    if R["MC"]["ok"]:
        vivi.add("M-C")
    vivi.add("M-V")                       # deviazione e livelli: sempre in vigore
    if R["MV"]["cattura"].get("applicabile_marcatori") is not False:
        vivi.add("M-V/marcatori")
    for k in ("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"):
        if R[k].get("ok") is not None:
            vivi.add(k)
    ciechi = [g for g, s in CHI_PRENDE.items() if not (set(s) & vivi)]
    R["guasti_visibili"] = len(CHI_PRENDE) - len(ciechi)
    R["guasti_ciechi"] = ciechi
    log("\n\033[1m== ⛔ I dodici guasti: quanti questo giro ne avrebbe visti\033[0m")
    log("    %s%d su %d%s — con gli strumenti VIVI in QUESTO giro, non con la"
        % (VERDE if not ciechi else GIALLO, R["guasti_visibili"],
           len(CHI_PRENDE), GRIGIO))
    log("    cifra della certificazione, che vale sulla mira.")
    for g in ciechi:
        log("    %s—%s   «%s» — cieco: lo prende solo %s, spento in questo giro"
            % (GIALLO, GRIGIO, g, "/".join(CHI_PRENDE[g])))

    # ── il verdetto ─────────────────────────────────────────────────────
    log("\n\033[1m== Il verdetto\033[0m")
    if bocciati:
        R["esito"] = "bocciato"
        R["bocciati"] = bocciati
        log("    %sBOCCIATO%s  strumenti che hanno detto no: %s"
            % (ROSSO, GRIGIO, ", ".join(sorted(set(bocciati)))))
        scrivi(a.esiti, R)
        return 1
    if sospesi and not a.senza_freschezza:
        R["esito"] = "non-misurato"
        R["sospesi"] = sospesi
        log("    %sNON MISURATO%s  strumenti senza ingresso: %s"
            % (GIALLO, GRIGIO, ", ".join(sospesi)))
        log("    ⛔ Questo NON e' un promosso.  «Non ho potuto guardare» e «va")
        log("       bene» sono due cose diverse, ed e' la regola che tiene in")
        log("       piedi tutte le altre (LEZIONI.md §1.9).")
        scrivi(a.esiti, R)
        return 2
    R["esito"] = "promosso"
    R["sospesi"] = sospesi
    log("    %sPROMOSSO%s  i pixel della pagina sono quelli del flusso, e il"
        % (VERDE, GRIGIO))
    log("    flusso e' quello della cattura.")
    if sospesi:
        log("    ⚠ ma con %s dichiarati NON MISURATI su richiesta esplicita."
            % ", ".join(sospesi))
    if ciechi:
        # ⛔ La riga non e' un contorno: un promosso che non dichiara quanti
        #    guasti non poteva vedere e' esattamente il verde che da' fiducia.
        log("    ⛔ E questo promosso vale su %d guasti su %d: %s NON li avrebbe"
            % (R["guasti_visibili"], len(CHI_PRENDE),
               ", ".join("«%s»" % g for g in ciechi)))
        log("       visti, e il rimedio non e' una soglia: e' la MIRA sul "
            "monitor virtuale.")
    scrivi(a.esiti, R)
    return 0


def scrivi(percorso, R):
    if not percorso:
        return
    with open(percorso, "a") as f:
        f.write(json.dumps(R, ensure_ascii=False, default=str) + "\n")


if __name__ == "__main__":
    sys.exit(main())
