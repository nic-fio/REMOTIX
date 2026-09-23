#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stress_occhio — ⭐⭐ GLI OCCHI DEL GIUDICE: «quel che e' sullo schermo non e'
quel che il server ha mandato», detto da solo, senza un umano che guardi.

    from stress_occhio import deposita_scena, guarda, giudizio, NOME_SCENA

    python3 stress_occhio.py --certifica        le funzioni pure, e che sappia
                                                dare rosso su un guasto FINTO
    python3 stress_occhio.py --scena > s.html   la scena, per guardarla
    python3 stress_occhio.py --guarda f.png     giudica una fotografia

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ IL PROBLEMA CHE QUESTO FILE ESISTE PER RISOLVERE
═══════════════════════════════════════════════════════════════════════════════

Notte fra il 22 e il 23 settembre 2026.  Lo scenario «due-inquilini» su
`rete11-gnome` da' **verde** due volte di fila, con Firefox e con Chrome:
~7000 fotogrammi consegnati, `dipinti == consegnati`, zero buchi, zero linee
morte.  ⛔ **Nello stesso momento l'utente guardava una finestra REMOTIX con
l'immagine a tessere sfalsate.**

⇒ Il giudice della suite conta i fotogrammi consegnati e dipinti, e **un
  fotogramma SBAGLIATO viene contato come dipinto esattamente come uno giusto.**
  Finche' il giudizio e' solo numerico, questo difetto passa verde quante volte
  si vuole.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ LA STRADA SCELTA — «LA SCENA SI DICHIARA», e perche' non le altre due
═══════════════════════════════════════════════════════════════════════════════

Le tre strade che erano sul tavolo:

 (a) ⭐ **la scena si dichiara** — la scena di banco la scriviamo noi, quindi
     puo' disegnare un contenuto PREVEDIBILE, e la fotografia della tela si
     confronta con quel che DOVEVA esserci.  ⇒ **questa**.
 (b) la firma dell'immagine — il server firma quel che codifica, la pagina
     firma quel che ha dipinto.  ⛔ **Scartata**: la codifica e' con perdita,
     una firma esatta non tornera' mai; servirebbe una grandezza tollerante,
     cioe' un'altra soglia da tarare, **piu'** una modifica al prodotto in C
     **piu'** un canale nuovo per portarla fuori.  Tre cose nuove da certificare
     al posto di una, e la piu' delicata (la tolleranza) resterebbe comunque.
 (c) la struttura — cercare nella tela la firma tipica della corruzione a
     tessere.  ⛔ **Scartata come giudice principale**: esiste gia' in
     `scenari/_comune.py:strisce()` e il suo `[M]` dice quanto e' stretta —
     Firefox col difetto **37,8**, Firefox curato **23,3**, Chrome **16,7**.
     Tre numeri che si accavallano fra browser e fra scene: e' un indizio, non
     un testimone.  ⚠ Resta utile e questo modulo **non la tocca**.

⭐ La ragione di fondo e' la stessa di `11-c3-scena.html` e di C5: **una
  grandezza che dipende da qualcun altro e' una soglia che si sposta senza
  dirlo.**  La scena la scriviamo noi ⇒ la verita' e' nota per costruzione, e
  il confronto e' fra due cose nostre.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LA TRAPPOLA CHE HA DECISO IL DISEGNO DELLA SCENA
═══════════════════════════════════════════════════════════════════════════════

Il primo disegno era: **un campo FISSO** (che non cambia mai) accanto a una
zona di rumore che fa traffico.  Sembra la cosa piu' pulita possibile — niente
tempo, niente cadenze, nessuno strappo da distinguere.

⛔ **E' cieco proprio al guasto che cerchiamo.**  Quando un delta si perde (o il
   server lo abbandona in `video_sgombra`), il decodificatore applica i delta
   che seguono su un riferimento SBAGLIATO.  Ma su un campo che non cambia mai,
   il riferimento sbagliato contiene **lo stesso identico campo** ⇒ i blocchi
   «copia da prima» copiano la cosa giusta, e il campo fisso resta perfetto
   mentre tutto il resto si sfalsa.

⇒ ⭐ **Il campo testimone deve MUOVERSI.**  E allora si muove nell'unico modo
  che si puo' verificare senza sapere che ora e': **tutte le celle avanzano
  INSIEME di un passo nella tavolozza.**  Ad ogni istante l'immagine e' valida
  per UN passo `n`; `n` non si conosce e non serve conoscerlo — **lo si ricava
  dall'immagine stessa, a maggioranza**, e poi si conta **quante celle non sono
  d'accordo con la maggioranza**.  Un pezzo di fotogramma vecchio, o spostato,
  non e' d'accordo.

═══════════════════════════════════════════════════════════════════════════════
⭐ CHE COSA SI MISURA, ESATTAMENTE — due grandezze, e fanno mestieri diversi
═══════════════════════════════════════════════════════════════════════════════

 1. ⭐⭐ **SPORCHE** — celle che dentro non sono di un colore solo.
    Ogni cella e' un rettangolo pieno di UN colore: dopo H.264 resta piatta.
    Un blocco estraneo caduto dentro la cella (una tessera sfalsata) porta un
    colore che non c'entra ⇒ la cella si sporca.  ⛔ **Non dipende dal tempo,
    non dipende da `n`, non dipende dalla cadenza**: e' il testimone piu' solido
    dei due, e vede anche gli spostamenti piu' piccoli di una cella.
 2. ⭐ **DISCORDI** — celle pulite ma del colore SBAGLIATO, cioe' d'accordo con
    un passo `n'` diverso dalla maggioranza.  Vede il pezzo di fotogramma
    VECCHIO rimasto incollato, che e' pulitissimo e completamente falso.

⇒ `guaste = sporche + discordi`, e il verdetto sta su questo.

⚠ E c'e' un terzo numero che NON accusa nessuno: **illeggibili**, le celle il
  cui colore non assomiglia a nessuno dei sei.  Troppe illeggibili vuol dire
  «non sto guardando la mia scena» ⇒ **esito 3**, mai rosso.

═══════════════════════════════════════════════════════════════════════════════
⛔ PERCHE' LA TAVOLOZZA E' QUESTA, E PERCHE' LA TAVOLA E' PSEUDO-CASUALE
═══════════════════════════════════════════════════════════════════════════════

 · **Sei colori ai vertici del cubo RGB.**  La distanza minima fra due qualunque
   di loro e' **255** su 441 possibili: dopo una codifica H.264 in 4:2:0 — che
   sottocampia il croma — restano distinguibili con un raggio di 100, cioe' con
   piu' del doppio di margine.  ⭐ E' la stessa scelta, e la stessa ragione, dei
   due colori agli antipodi di `11-c3-scena.html`.
 · **La tavola delle celle e' pseudo-casuale, non `(riga + colonna)`.**
   ⛔ Con una formula regolare esistono spostamenti INVISIBILI: con
      `(r + 5c) mod 6`, una tessera spostata di una cella in diagonale ricade
      esattamente sullo stesso colore, e la cella sbagliata sembra giusta.  Con
      una tavola pseudo-casuale ogni cella ha un valore suo ⇒ uno spostamento di
      k celle sfugge con probabilita' (1/6)^k, cioe' praticamente mai.
   ⭐ Il generatore e' MINSTD (`s = s*16807 mod 2147483647`), scelto perche' e'
      ESATTO tanto in Python quanto in JavaScript: 2^31 x 16807 ≈ 3,6·10^13 sta
      sotto i 2^53 dei numeri di JavaScript ⇒ le due tavole sono la stessa
      tavola, e non «quasi».  ⛔ Un LCG piu' grosso (1103515245) in JavaScript
      perderebbe i bit bassi in silenzio: due tavole diverse, e il banco
      accuserebbe il prodotto di un difetto suo.

═══════════════════════════════════════════════════════════════════════════════
⭐ LA CORNICE MAGENTA — la scena dice DOVE sta, invece di farselo indovinare
═══════════════════════════════════════════════════════════════════════════════

La tela del cliente mostra lo schermo remoto; il campo testimone ne occupa una
parte.  ⛔ Indovinare quella parte da fuori (il browser e' a schermo pieno? c'e'
una barra? la fotografia e' scalata?) sarebbe un'ipotesi non misurata, e il
giorno che cade il banco accusa il prodotto.

⇒ La scena disegna attorno al campo una **cornice magenta piena** (255,0,255),
  che ⛔ **non e' nessuno dei sei colori della tavolozza**.  Il lettore la trova
  per profilo di riga e di colonna e ne ricava il rettangolo interno, **esatto,
  qualunque sia la scala della fotografia**.
⚠ Se la cornice non si trova ⇒ **esito 3**: «non ho trovato la mia scena».  ⛔
  Mai rosso: un banco che non ha guardato non accusa nessuno (§1.51).

═══════════════════════════════════════════════════════════════════════════════
⭐ E LA SCENA FA ANCHE DA PESO
═══════════════════════════════════════════════════════════════════════════════

Sotto e sopra il campo testimone c'e' **il motore**: rumore casuale a mezza
risoluzione ridisegnato a ogni `requestAnimationFrame`, cioe' esattamente il
generatore di `SCENA_PESANTE` (`[M]` 86-264 Mbit/s, il caso peggiore per un
codificatore).  ⇒ Il guasto si cerca **sotto il carico che lo fa uscire**, non
su un desktop tranquillo.  ⚠ E il campo testimone cambia tutte le sue 240 celle
15 volte al secondo: non e' una zona ferma che il codificatore salta.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ LA CERTIFICAZIONE, e non e' su un guasto inventato
═══════════════════════════════════════════════════════════════════════════════

`[M]` 23 settembre 2026, scatola `rete11-kde`, stessa scena, stessa catena,
      stessi 40 s, un fotogramma ogni 5 guardato a 640 px: **cambia solo il
      binario del prodotto**, prima e dopo la cura del difetto della notte
      (`7e0c0e2` — il fotogramma gia' codificato che non parte adesso paga la
      chiave).

    binario                       fotografie   devastate   peggiore   verdetto
    ─────────────────────────────────────────────────────────────────────────
    PRIMA della cura (22 set)          311          7        53,8 %    ROSSO
    DOPO la cura (9b5df38b)            275          0         0,0 %    VERDE

⭐ E un guasto INNESTATO che si governa, accanto: 83 delta tolti dal flusso
   registrato (un NAL ogni 40, mai una chiave) ⇒ **peggiore 55,0 %, ROSSO**.

⭐⭐ E LA FOTOGRAFIA VERA, che e' il pezzo che chiude il giro.  I due numeri di
   sopra vengono da un decodificatore terzo; questi vengono da `fotografa_tela()`
   di un browser VERO sul tablet, cioe' dalla tela che l'utente guarda.
   `[M]` 23 settembre 2026, `rete11-kde`, binario `9b5df38b`, scena testimone
   col motore, una fotografia **al secondo** per 60 s:

    browser    tela      fotografia   viste  celle    guaste   peggiore  esito
    ──────────────────────────────────────────────────────────────────────────
    Firefox   1448x862   1368 px      35     8 400      0       0,00 %   VERDE
    Chrome    1460x888    609 px      37     8 880      0       0,00 %   VERDE

⛔ Le due strade di `fotografa_tela()` sono diverse davvero — Marionette
   consegna l'elemento a misura piena, Chrome lo riduce a 640 px con `clip` e
   `scala` — e la cornice trovata lo dice: **1368 px contro 609**, un fattore
   2,25.  ⭐ L'occhio non se ne accorge: la geometria se la fa dire dalla scena
   invece di indovinarla.
⚠ E delle 51 e 53 fotografie prese, 14 per parte sono «non ho guardato»: e' il
  browser della scena che deve ancora comparire dentro la sessione (a freddo,
  dentro una scatola, ci mette una ventina di secondi).  ⇒ Chi aggancia questo
  modulo dia alla scena il tempo di salire, o quelle fotografie sono esito 3.

═══════════════════════════════════════════════════════════════════════════════
⭐ E UN SECONDO GIUDICE, sui soli NUMERI, che costa quasi zero
═══════════════════════════════════════════════════════════════════════════════

`giudizio_dei_numeri()`: se il server ha buttato fotogrammi gia' codificati e
non e' uscita nessuna chiave oltre a quella d'apertura, la catena dei
riferimenti e' rotta e nessuno l'ha ricucita ⇒ ROSSO.  ⛔ E' una rete in piu',
**non un sostituto dell'occhio**: il suo punto cieco e' misurato e sta scritto
sopra la funzione.

═══════════════════════════════════════════════════════════════════════════════
⭐ COME SI AGGANCIA ALLA SUITE — e `stress_nucleo.py` NON SI TOCCA
═══════════════════════════════════════════════════════════════════════════════

    import stress_occhio as O
    O.deposita_scena(nucleo, desktop)          # scrive la scena nella scatola
                                               # e la registra in nucleo.SCENE
    ...  nucleo.scena(desktop, O.NOME_SCENA, chi)      # come le altre scene
    ...  rapporti = [O.guarda(C.foto(browser)) for ...]
    esito, perche, misure = O.giudizio(rapporti)
    ...  numeri = O.conti_del_ritmo(nucleo, desktop, da_istante, chi)
    esito2, perche2, misure2 = O.giudizio_dei_numeri(numeri)

⛔ `deposita_scena()` scrive il file **e** infila due voci in `nucleo.SCENE`
   («testimone» e «testimone-scarico»): da quel momento
   `nucleo.scena(desktop, "testimone", chi)` funziona senza che una riga di
   `stress_nucleo.py` sia cambiata.  ⇒ Nessuna firma pubblica toccata, nessun
   conflitto con chi lavora sul nucleo e su `_lancia.py`.

⚠⚠ E UNA COSA CHE CHI USA QUESTO MODULO DEVE SAPERE, perche' e' costata la
   prima lettura di stanotte: **gli episodi di corruzione sono BREVI**.  `[M]`
   23 set 2026, binario rotto: ciascun episodio dura una trentina di fotogrammi,
   cioe' meno di mezzo secondo.  ⇒ Guardando un fotogramma ogni 60 si vede
   **zero**, e si scrive «sano» su un giro che ha sette fotogrammi devastati.
   ⛔ **La cadenza delle fotografie e' parte della misura**: chi ne prende una
      ogni 5 secondi per tre minuti (36 fotografie) ha meno di una probabilita'
      su dieci di cascare dentro un episodio.  ⭐ Chi vuole un giudizio vero
      guardi FITTO, o registri il flusso e lo guardi dopo — che e' come sono
      fatti i due numeri della certificazione qui sopra.
"""
import argparse
import base64
import io
import json
import math
import os
import sys

VERDE, ROSSO, CIECO = 0, 1, 3

NOME_SCENA = "testimone"
DOVE_NELLA_SCATOLA = "/opt/remotix/14-scena-testimone.html"

# ═══════════════════════════════════════════════════════════════════════════
#  LA SCENA, DICHIARATA QUI E UNA VOLTA SOLA
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ Questi numeri sono la scena E il lettore: chi ne cambia uno qui lo cambia
#    per tutti e due, perche' il codice JavaScript li riceve da queste stesse
#    costanti (vedi `scena_html()`).  ⇒ Non possono divergere.
COLONNE = 24
RIGHE = 10
PASSI = 6                     # quanti colori, cioe' il periodo del movimento
SEME = 1                      # il seme di MINSTD: la tavola e' SEMPRE la stessa

# ⭐ I sei vertici del cubo RGB piu' distanti fra loro.  Distanza minima 255.
TAVOLOZZA = [(0, 0, 0), (255, 0, 0), (0, 255, 0),
             (0, 0, 255), (255, 255, 0), (255, 255, 255)]
MAGENTA = (255, 0, 255)       # ⛔ non e' nella tavolozza: e' la cornice

# La geometria del campo, in frazioni dello schermo.  ⭐ Sta in mezzo apposta:
# una barra del desktop in alto o in basso non lo puo' coprire.
CAMPO = (0.04, 0.16, 0.96, 0.76)      # x0, y0, x1, y1
QUADRI_PER_PASSO = 4                  # `n` avanza ogni 4 quadri ⇒ ~15 passi/s


def tavola():
    """⭐ La tavola dei colori base, uguale in Python e in JavaScript.

    MINSTD: `s = (s * 16807) mod 2147483647`, seme 1.  ⛔ Scelto perche' ogni
    prodotto intermedio sta sotto i 2^53 dei numeri di JavaScript: le due
    tavole sono LA STESSA, non «quasi la stessa».
    """
    fuori = []
    s = SEME
    for _ in range(RIGHE * COLONNE):
        s = (s * 16807) % 2147483647
        fuori.append(s % PASSI)
    return fuori


TAVOLA = tavola()


def atteso(r, c, n):
    """Il colore che la cella (r, c) deve avere al passo `n`."""
    return (TAVOLA[r * COLONNE + c] + n) % PASSI


# ⛔ Il corpo della pagina: nessuna risorsa esterna (la scatola non ha rete
#    verso fuori), niente scritte che si muovono da sole, `requestAnimationFrame`
#    e non `setInterval` — le tre regole di `11-c2-finestra.html`.
_SCENA = r"""<!doctype html><meta charset="utf-8"><title>testimone</title>
<style>html,body{margin:0;padding:0;height:100%;overflow:hidden;background:#000}
canvas{width:100vw;height:100vh;display:block}</style>
<canvas id="c"></canvas><script>
// ⭐⭐ LA SCENA TESTIMONE.  I numeri qui sotto arrivano da `stress_occhio.py`:
//    la scena e il lettore leggono le STESSE costanti, e non si possono
//    disallineare senza che qualcuno le cambi in un posto solo.
var COLONNE=__COLONNE__, RIGHE=__RIGHE__, PASSI=__PASSI__, SEME=__SEME__;
var CAMPO=__CAMPO__, QPP=__QPP__;
var TAV=__TAVOLOZZA__, MAG='rgb(255,0,255)';
// ⛔ MINSTD, e non un generatore piu' grosso: ogni prodotto sta sotto 2^53,
//    quindi questa tavola e' BIT PER BIT quella che Python ricostruisce.
var T=[],s=SEME; for(var i=0;i<RIGHE*COLONNE;i++){s=(s*16807)%2147483647;T.push(s%PASSI);}
var c=document.getElementById('c'), x=c.getContext('2d',{alpha:false});
var rum=document.createElement('canvas'), rx=rum.getContext('2d');
var W=0,H=0,cx0=0,cy0=0,cx1=0,cy1=0,B=0,n=0,q=0;
function mis(){
  var d=window.devicePixelRatio||1;
  W=c.width=Math.round(innerWidth*d); H=c.height=Math.round(innerHeight*d);
  // ⚠ il rumore si genera a meta' risoluzione e si stende scalato: e' quel che
  //    fa `SCENA_PESANTE`, ed e' gia' misurato a 86-264 Mbit/s.
  rum.width=Math.max(2,W>>1); rum.height=Math.max(2,H>>1);
  cx0=Math.round(W*CAMPO[0]); cy0=Math.round(H*CAMPO[1]);
  cx1=Math.round(W*CAMPO[2]); cy1=Math.round(H*CAMPO[3]);
  // ⭐ la cornice e' spessa almeno 10 pixel: deve sopravvivere alla scalatura
  //    della fotografia (Chrome la riduce a 640 di larghezza).
  B=Math.max(10,Math.round(H*0.016));
}
mis(); onresize=mis;
function rumore(){
  var w=rum.width,h=rum.height,im=rx.createImageData(w,h),d=im.data;
  for(var i=0;i<d.length;i+=4){var r=Math.random()*255|0;
    d[i]=r; d[i+1]=(r*7+n)&255; d[i+2]=(r*13)&255; d[i+3]=255;}
  rx.putImageData(im,0,0);
}
function campo(){
  x.fillStyle=MAG; x.fillRect(cx0,cy0,cx1-cx0,cy1-cy0);
  var ix0=cx0+B, iy0=cy0+B, iw=(cx1-cx0)-2*B, ih=(cy1-cy0)-2*B;
  for(var r=0;r<RIGHE;r++) for(var k=0;k<COLONNE;k++){
    var a=TAV[(T[r*COLONNE+k]+n)%PASSI];
    x.fillStyle='rgb('+a[0]+','+a[1]+','+a[2]+')';
    // ⛔ i bordi si arrotondano dal PRIMO al PROSSIMO, non con una larghezza
    //    fissa: altrimenti fra una cella e l'altra resterebbero righine del
    //    fondo, e sarebbero «celle sporche» fatte dalla scena, non dal prodotto.
    var X0=ix0+Math.round(k*iw/COLONNE), X1=ix0+Math.round((k+1)*iw/COLONNE);
    var Y0=iy0+Math.round(r*ih/RIGHE),  Y1=iy0+Math.round((r+1)*ih/RIGHE);
    x.fillRect(X0,Y0,X1-X0,Y1-Y0);
  }
}
// ⭐ `?motore=no` spegne il rumore: resta il solo campo testimone, cioe' pochi
//    Mbit/s invece di decine.  ⛔ Non e' un ornamento: e' il CONTROLLO NEGATIVO
//    di `LEZIONI.md` §1.49 — si toglie il carico e si pretende il verde.  Se
//    l'occhio desse rosso anche senza carico, il difetto sarebbe suo.
var MOTORE = (location.search.indexOf('motore=no') < 0);
function giro(){
  if(MOTORE){ rumore(); x.drawImage(rum,0,0,W,H); }
  else if(q===0){ x.fillStyle='#202020'; x.fillRect(0,0,W,H); }
  if(++q>=QPP){q=0;n=(n+1)%PASSI;}
  campo();
  requestAnimationFrame(giro);
}
requestAnimationFrame(giro);
</script>
"""


def scena_html():
    """⭐ La scena, con i numeri di questo file dentro.  ⛔ Non c'e' una seconda
    copia da tenere allineata: il JavaScript riceve le costanti da qui."""
    return (_SCENA
            .replace("__COLONNE__", str(COLONNE))
            .replace("__RIGHE__", str(RIGHE))
            .replace("__PASSI__", str(PASSI))
            .replace("__SEME__", str(SEME))
            .replace("__QPP__", str(QUADRI_PER_PASSO))
            .replace("__CAMPO__", json.dumps(list(CAMPO)))
            .replace("__TAVOLOZZA__", json.dumps([list(c) for c in TAVOLOZZA])))


# ═══════════════════════════════════════════════════════════════════════════
#  LE SOGLIE — ⛔ nessuna e' inventata: sotto ognuna c'e' un `[M]`
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA MISURA CHE LE TARA, e va letta prima dei numeri.
#
# `[M]` 23 settembre 2026, scatola `rete11-kde` (porta 8512), schermo
#       1920x1080, scena testimone col motore acceso, **catena vera**: server
#       REMOTIX → filo QUIC → `01-b3-cliente.py` (`--video-scrivi`, cioe' i
#       fotogrammi PRESI DAL FILO cosi' come sono) → decodificatore H.264.
#       40 s di ripresa per giro, ~3300 fotogrammi; si guarda **un fotogramma
#       ogni 5**, ridotto a 640 px di larghezza (che e' esattamente quel che
#       consegna `fotografa_tela()` di Chrome), 240 celle l'uno.
#
# ⛔⛔ E LA CERTIFICAZIONE NON E' SU UN GUASTO INVENTATO: e' sul prodotto,
#      prima e dopo la cura vera del difetto della notte (`7e0c0e2`, il
#      fotogramma gia' codificato che non parte e adesso PAGA LA CHIAVE).
#      Stessa scatola, stessa scena, stessa catena, stessi 40 s: cambia solo il
#      binario.
#
#   · binario **PRIMA** della cura (22 set) ⇒ **311 fotografie viste**,
#     **7 DEVASTATE**, 26 sopra il 2 %, peggiore **53,8 %** di celle guaste
#     (44 sporche + 85 discordi su 240) ⇒ **ROSSO**.
#   · binario **DOPO** la cura (`9b5df38b`) ⇒ **275 fotografie viste**,
#     **0 devastate, 0 sopra il 2 %, peggiore 0,0 %** — celle guaste **0 su
#     66 000** ⇒ **VERDE**.  E le chiavi spedite passano da 2 a **9**.
#
# ⭐ E accanto, il guasto INNESTATO, che si governa e si ripete a comando: dal
#   flusso registrato si tolgono **83 delta su 3356** (un NAL di tipo 1 ogni 40,
#   mai una chiave) ⇒ il decodificatore applica i delta che seguono su un
#   riferimento che non ha mai visto, la numerazione resta CONTINUA, nessun
#   buco, nessuna `RICHIEDI_CHIAVE` — ⭐ la firma esatta del difetto vero.
#   Esito: **6 fotografie su 23 sopra soglia, peggiore 55,0 %** ⇒ **ROSSO**.
#
# ⇒ Fra **0 celle guaste** (il prodotto curato, su 66 000 celle) e **129 celle**
#   (il peggio del prodotto rotto) la soglia sta a **5 celle (2 %)**.  ⛔ Non e'
#   un numero scelto perche' «sembra giusto»: sta nel mezzo di un vuoto
#   misurato, e il vuoto e' largo venticinque volte.
#
# ⭐ I due raggi vivono nello spazio RGB, dove la distanza fra due colori
#   qualunque della tavolozza e' **almeno 255** ⇒ un raggio di 110 lascia piu'
#   del doppio di margine sia per lo sbavamento del croma in 4:2:0 sia per la
#   riduzione della fotografia.
RAGGIO_CLASSE = 110.0    # oltre questo da ogni colore della tavolozza: illeggibile
RAGGIO_SPORCO = 110.0    # un pixel piu' lontano di cosi' dalla mediana e' estraneo
QUOTA_SPORCA = 0.06      # ⭐ una cella e' SPORCA se piu' del 6% dei suoi pixel
                         #   interni sono estranei
DENTRO = 0.56            # si guarda solo il 56% centrale della cella: i bordi
                         # portano lo sbavamento del codificatore, che non e' un
                         # difetto ⇒ ⛔ guardarli sarebbe un rosso falso sicuro
QUOTA_ILLEGGIBILE = 0.25  # oltre il 25% di celle illeggibili: «non lo so»

# ⭐ Le soglie del VERDETTO, e sono tre perche' fanno tre mestieri diversi.
SOGLIE = {
    "guaste_per_foto": 0.02,   # in UNA fotografia, al piu' il 2% di celle guaste
    "foto_guaste": 0.10,       # e al piu' il 10% delle fotografie puo' sforare
    # ⛔⛔ E LA SECONDA SOGLIA, CHE E' COSTATA UN VERDE FALSO — 23 set 2026.
    #   Con la sola coppia di sopra, il giro del binario di oggi guardato
    #   **fotogramma per fotogramma** (313 fotografie viste) dava **VERDE**:
    #   26 fotografie sopra il 2% sono l'8,3 %, cioe' appena sotto il 10 %.
    #   ⇒ Ventisei fotogrammi rotti, uno al **53,8 % di celle guaste**, e il
    #     giudice diceva di si.  ⛔ E' lo stesso errore del giudice numerico che
    #     questo file esiste per curare: una media che assorbe un disastro.
    # ⭐ Percio' una fotografia DEVASTATA basta da sola.  `[M]` il numero sta
    #   in un vuoto misurato: nelle 311 fotografie, quelle sane hanno **0**
    #   celle guaste, la finestra che si apre ne fa **10,8 %**, e gli episodi
    #   di corruzione veri stanno a **33,3 · 49,6 · 50,0 · 53,8 %**.  Fra
    #   l'11 % e il 33 % non c'e' NIENTE: la soglia si mette in mezzo, a 15 %.
    #   ⭐ E col prodotto CURATO le fotografie sopra il 15 % sono **zero su
    #     275**: la soglia non e' larga per prudenza, e' larga perche' il sano
    #     sta tutto da una parte.
    "devastata": 0.15,
    "minimo_foto": 3,          # sotto tre fotografie non si giudica: esito 3
    # ⛔⛔ E IL RISCALDAMENTO, che e' costato la prima lettura di stanotte.
    #   `[M]` 23 set 2026: nella ripresa SANA, la **seconda** fotografia in cui
    #   la scena si vede da' **10,8 % di celle guaste** — e guardandola non e'
    #   un difetto della misura, e' la finestra del browser che si APRE:
    #   l'animazione di KWin la scala e la sfuma, e per un istante sullo schermo
    #   c'e' davvero mezza scena.  ⇒ Le prime due fotografie dopo che la scena
    #   compare non si giudicano.  ⚠ Dalla terza in poi, nella stessa ripresa,
    #   le celle guaste sono **zero su 5520**: non e' un velo steso sul rumore,
    #   e' il confine fra due regimi diversi.
    "scalda": 2,
}


# ═══════════════════════════════════════════════════════════════════════════
#  IL LETTORE — una funzione PURA: un PNG entra, dei numeri escono
# ═══════════════════════════════════════════════════════════════════════════
def _numpy():
    import numpy as np
    return np


def _immagine(png):
    """Il PNG in un array numpy (altezza, larghezza, 3) di float32."""
    from PIL import Image
    np = _numpy()
    im = Image.open(io.BytesIO(png)).convert("RGB")
    return np.asarray(im, dtype=np.float32)


def trova_cornice(a):
    """⭐ Il rettangolo INTERNO della cornice magenta, o `None`.

    Torna `(x0, y0, x1, y1)` — gli estremi del campo di celle, escluso il
    magenta.  ⛔ `None` non e' un guasto del prodotto: e' «non ho trovato la mia
    scena», e chi chiama lo legge come **3**.

    ⚠ Come: il magenta e' un rettangolo CAVO, quindi nel profilo di riga le
      righe della barra alta e di quella bassa contano quanto e' largo il campo,
      mentre le righe in mezzo contano solo i due montanti laterali — due ordini
      di grandezza di differenza.  ⇒ Una soglia a meta' del massimo separa le
      due cose senza che ci sia niente da tarare.
    """
    np = _numpy()
    if a.ndim != 3 or a.shape[0] < 32 or a.shape[1] < 32:
        return None
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    # ⚠ larghi apposta: dopo H.264 in 4:2:0 il magenta pieno si sbava, e una
    #   soglia stretta perderebbe la cornice proprio sul carico pesante.
    m = (r > 150) & (g < 110) & (b > 150)
    if not m.any():
        return None
    righe = m.sum(axis=1).astype(np.float64)
    colonne = m.sum(axis=0).astype(np.float64)

    def barre(profilo):
        picco = profilo.max()
        if picco < 8:
            return None
        piene = np.nonzero(profilo > 0.5 * picco)[0]
        if piene.size < 2:
            return None
        # due gruppi: la barra di qua e quella di la'.  ⛔ Se sono uno solo, il
        # campo e' tagliato fuori dalla fotografia e non si giudica.
        salti = np.nonzero(np.diff(piene) > 1)[0]
        if salti.size < 1:
            return None
        primo_fine = piene[salti[0]]
        secondo_inizio = piene[salti[0] + 1]
        return int(primo_fine) + 1, int(secondo_inizio)

    v = barre(righe)
    o = barre(colonne)
    if not v or not o:
        return None
    y0, y1 = v
    x0, x1 = o
    if (x1 - x0) < COLONNE * 3 or (y1 - y0) < RIGHE * 3:
        return None
    return x0, y0, x1, y1


def guarda(png, cornice=None):
    """⭐⭐ Giudica UNA fotografia della tela.  Torna un dizionario di numeri.

    `cornice` la si puo' imporre (quella trovata su una foto sana): serve
    quando un guasto grosso mangia anche la cornice magenta.

    Le chiavi:
      `celle`        quante celle si sono guardate (0 ⇒ non ho guardato)
      `sporche`      celle che dentro non sono di un colore solo
      `discordi`     celle pulite ma del colore di un ALTRO passo
      `illeggibili`  celle che non somigliano a nessuno dei sei colori
      `guaste`       `sporche + discordi`
      `quota_guaste` `guaste / celle`
      `passo`        il passo `n` che la maggioranza dichiara
      `accordo`      quota di celle d'accordo con quel passo
      `cornice`      il rettangolo trovato, da riusare
      `visto`        True se si e' potuto guardare
      `perche`       la frase, quando non si e' potuto
    """
    vuoto = {"celle": 0, "sporche": None, "discordi": None, "illeggibili": None,
             "guaste": None, "quota_guaste": None, "passo": None,
             "accordo": None, "cornice": None, "visto": False, "perche": ""}
    if not png:
        return dict(vuoto, perche="nessuna fotografia")
    try:
        a = _immagine(png)
    except Exception as e:                       # noqa: BLE001
        return dict(vuoto, perche="fotografia illeggibile: %s" % str(e)[:120])
    c = cornice or trova_cornice(a)
    if not c:
        return dict(vuoto, perche="la cornice magenta della scena non c'e': "
                                  "non sto guardando la mia scena")
    np = _numpy()
    x0, y0, x1, y1 = c
    h, w = a.shape[0], a.shape[1]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    iw, ih = x1 - x0, y1 - y0
    if iw < COLONNE * 3 or ih < RIGHE * 3:
        return dict(vuoto, cornice=list(c),
                    perche="il campo e' troppo piccolo nella fotografia "
                           "(%dx%d per %dx%d celle)" % (iw, ih, COLONNE, RIGHE))
    tav = np.asarray(TAVOLOZZA, dtype=np.float32)

    sporche = discordi = illeggibili = 0
    classi = []                                  # (r, c, classe) delle leggibili
    for r in range(RIGHE):
        ya = y0 + int(round(r * ih / float(RIGHE)))
        yb = y0 + int(round((r + 1) * ih / float(RIGHE)))
        m = (yb - ya)
        ya2 = ya + int(round(m * (1 - DENTRO) / 2.0))
        yb2 = yb - int(round(m * (1 - DENTRO) / 2.0))
        if yb2 - ya2 < 2:
            ya2, yb2 = ya, yb
        for k in range(COLONNE):
            xa = x0 + int(round(k * iw / float(COLONNE)))
            xb = x0 + int(round((k + 1) * iw / float(COLONNE)))
            n = (xb - xa)
            xa2 = xa + int(round(n * (1 - DENTRO) / 2.0))
            xb2 = xb - int(round(n * (1 - DENTRO) / 2.0))
            if xb2 - xa2 < 2:
                xa2, xb2 = xa, xb
            sub = a[ya2:yb2, xa2:xb2, :]
            if sub.size == 0:
                illeggibili += 1
                continue
            piatto = sub.reshape(-1, 3)
            med = np.median(piatto, axis=0)
            # ⭐ SPORCA: quanti pixel interni sono LONTANI dalla mediana della
            #   cella.  ⛔ Non la deviazione: un blocco estraneo piccolo ma
            #   violento sparisce in una media, e qui e' proprio lui che si cerca.
            d = np.sqrt(((piatto - med) ** 2).sum(axis=1))
            fuori = float((d > RAGGIO_SPORCO).mean())
            if fuori > QUOTA_SPORCA:
                sporche += 1
                continue
            dc = np.sqrt(((tav - med) ** 2).sum(axis=1))
            j = int(dc.argmin())
            if float(dc[j]) > RAGGIO_CLASSE:
                illeggibili += 1
                continue
            classi.append((r, k, j))

    celle = RIGHE * COLONNE
    if illeggibili > QUOTA_ILLEGGIBILE * celle:
        return dict(vuoto, celle=celle, illeggibili=illeggibili, cornice=list(c),
                    perche="%d celle su %d non somigliano a nessuno dei sei "
                           "colori: non sto guardando la mia scena"
                           % (illeggibili, celle))
    # ⭐ Il passo `n` si RICAVA dalla maggioranza: non si sa che ora e', e non
    #   serve saperlo.  ⛔ E' questo che rende la misura indipendente dalla
    #   cadenza del prodotto, del compositore e del browser.
    voti = [0] * PASSI
    for (r, k, j) in classi:
        voti[(j - TAVOLA[r * COLONNE + k]) % PASSI] += 1
    passo = int(max(range(PASSI), key=lambda i: voti[i])) if classi else None
    if passo is not None:
        discordi = len(classi) - voti[passo]
    guaste = sporche + discordi
    return {"celle": celle, "sporche": sporche, "discordi": discordi,
            "illeggibili": illeggibili, "guaste": guaste,
            "quota_guaste": guaste / float(celle),
            "passo": passo,
            "accordo": (voti[passo] / float(celle)) if passo is not None else None,
            "cornice": list(c), "visto": True, "perche": ""}


# ═══════════════════════════════════════════════════════════════════════════
#  IL VERDETTO — ⭐ e sa dire «non lo so»
# ═══════════════════════════════════════════════════════════════════════════
def giudizio(rapporti, soglie=None):
    """⭐⭐ `(esito, perche, misure)` da una serie di fotografie giudicate.

      0  verde   quel che e' sullo schermo e' quel che la scena dichiara
      1  ROSSO   no, e si dice quante celle e in quante fotografie
      3  non lo so  ⛔ **mai rosso** quando non si e' potuto guardare: troppe
                 poche fotografie, la cornice non trovata, la scena non sua

    ⚠ Due soglie e non una, perche' i due guasti hanno due forme:
      · `guaste_per_foto` — quanto puo' essere sbagliata UNA fotografia;
      · `foto_guaste` — quante fotografie possono sforare.  Una sola fotografia
        un po' sporca in venti puo' essere lo strappo di un istante; ⛔ una su
        tre non lo e' piu'.
    """
    s = dict(SOGLIE)
    s.update(soglie or {})
    visti = [r for r in (rapporti or []) if r and r.get("visto")]
    if len(visti) < s["minimo_foto"]:
        non = [r.get("perche") for r in (rapporti or []) if r and not r.get("visto")]
        return CIECO, ("ho potuto guardare solo %d fotografie su %d (ne volevo "
                       "almeno %d): %s"
                       % (len(visti), len(rapporti or []), s["minimo_foto"],
                          ("; ".join(x for x in non if x)[:200] or "nessun motivo"))), {
            "foto_viste": len(visti), "foto_totali": len(rapporti or [])}
    # ⭐ IL RISCALDAMENTO: le prime fotografie in cui la scena compare sono la
    #   FINESTRA CHE SI APRE, non il prodotto (vedi la nota su `scalda`).
    scalda = int(s.get("scalda") or 0)
    if scalda and len(visti) > scalda + s["minimo_foto"]:
        visti = visti[scalda:]
    quote = [r["quota_guaste"] for r in visti]
    sforanti = [q for q in quote if q > s["guaste_per_foto"]]
    devastate = [q for q in quote if q > s["devastata"]]
    peggio = max(visti, key=lambda r: r["quota_guaste"])
    misure = {
        "foto_viste": len(visti),
        "foto_devastate": len(devastate),
        "foto_totali": len(rapporti or []),
        "celle_per_foto": visti[0]["celle"],
        "quota_guaste_media": round(sum(quote) / len(quote), 5),
        "quota_guaste_peggiore": round(max(quote), 5),
        "foto_sopra_soglia": len(sforanti),
        "quota_foto_sopra_soglia": round(len(sforanti) / float(len(visti)), 4),
        "peggiore": {k: peggio[k] for k in
                     ("sporche", "discordi", "illeggibili", "guaste", "accordo")},
        "soglie": s,
    }
    # ⛔ Una sola fotografia devastata basta: nessun meccanismo legittimo — ne'
    #   uno strappo, ne' una finestra che si apre — mette un terzo dello schermo
    #   nel posto sbagliato.
    if devastate:
        return ROSSO, ("l'immagine sullo schermo NON e' quella che la scena "
                       "dichiara: %d fotografie DEVASTATE su %d (sopra il %.0f%% "
                       "di celle guaste); la peggiore %.1f%% — %d celle sporche "
                       "e %d discordi su %d"
                       % (len(devastate), len(visti), 100 * s["devastata"],
                          100 * peggio["quota_guaste"], peggio["sporche"],
                          peggio["discordi"], peggio["celle"])), misure
    if len(sforanti) > s["foto_guaste"] * len(visti):
        return ROSSO, ("l'immagine sullo schermo NON e' quella che la scena "
                       "dichiara: %d fotografie su %d sopra la soglia del %.0f%% "
                       "di celle guaste (la peggiore %.1f%%: %d sporche, %d "
                       "discordi su %d celle)"
                       % (len(sforanti), len(visti), 100 * s["guaste_per_foto"],
                          100 * peggio["quota_guaste"], peggio["sporche"],
                          peggio["discordi"], peggio["celle"])), misure
    return VERDE, ("lo schermo combacia con la scena dichiarata: %d fotografie, "
                   "al peggio %.1f%% di celle guaste su %d (soglia %.0f%%)"
                   % (len(visti), 100 * max(quote), visti[0]["celle"],
                      100 * s["guaste_per_foto"])), misure


# ═══════════════════════════════════════════════════════════════════════════
#  IL SECONDO GIUDICE — quello sui NUMERI, che costa quasi zero
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL FATTO, ed e' del 23 settembre 2026: il difetto della notte era
#   `ritmo_frena()` (`src/webtransport.c`) che buttava un fotogramma **gia'
#   codificato** senza consumare il `numero` e senza accendere il debito della
#   chiave (§5.2).  ⇒ Numerazione continua, nessun buco, nessuna
#   `RICHIEDI_CHIAVE`, e il decodificatore dipinge tutto sopra un riferimento
#   che non ha mai ricevuto.  Curato in `7e0c0e2`.
#
# ⭐ Quel difetto lascia una firma NUMERICA, e leggerla costa zero: sono conti
#   che `conta_dal_server()` gia' porta.  `[M]` lo stesso giro, prima e dopo la
#   cura (misura del 23 set 2026, scatola `rete11-gnome`):
#
#       prima della cura:  consegnati 8902, dipinti 8877, saltati 24, chiavi 1
#       dopo la cura:      consegnati 8978, dipinti 8977, saltati  0, chiavi 8
#
#   ⇒ **Una chiave sola** in tutta la sessione, con 24 fotogrammi buttati: la
#     catena dei riferimenti si e' rotta ventiquattro volte e nessuno l'ha mai
#     ricucita.
#
# ⛔⛔ E DOVE QUESTO GIUDICE E' CIECO, che e' la cosa che va detta per prima.
#   `[M]` 23 set 2026, scatola `rete11-kde`, binario di prima della cura, il
#   giro che sta nel `[M]` delle soglie qui sopra: **47 fotogrammi buttati dal
#   ritmo e 2 chiavi spedite** — cioe' UNA chiave dopo quella d'apertura.  Per
#   la regola numerica quel giro e' **verde**; l'occhio, guardando fotogramma
#   per fotogramma, ci ha trovato **26 fotografie sopra soglia su 313, la
#   peggiore al 53,8 %**.
#   ⇒ ⭐ Il giudice numerico e' una rete in piu', **non un sostituto
#     dell'occhio**: prende il caso in cui NESSUNA chiave ha riparato, e si
#     perde quello in cui una chiave e' passata ma troppo tardi o troppo poche.
#     ⛔ Chi domani lo stringesse per catturare anche quel caso deve tararlo su
#        giri veri, perche' le chiavi crescono anche per ragioni legittime (la
#        prima della sessione, il cambio di tela, la richiesta del client): una
#        soglia a occhio qui fabbrica rossi falsi.
MOTIVI_DEL_RITMO = ["il regolatore del ritmo", "delta TENUTI", "SPEDITO: CHIAVE"]


def conti_del_ritmo(nucleo, desktop, da_istante=None, chi=None):
    """⭐ I conti degli SCARTI del server, letti dal registro della scatola.

    ⚠ `stress_nucleo.MOTIVI_REGISTRO` **non** porta la riga del regolatore del
      ritmo, e questo modulo non la aggiunge la': quel file ce l'ha un altro in
      mano.  ⇒ Qui si fa un `grep` proprio, dichiarato, sui motivi di sopra.
    ⛔ Le righe di riepilogo (`ritmo`, `delta TENUTI`) escono **alla chiusura
       della sessione**: chi legge questi numeri a sessione ancora aperta trova
       `None`, e `None` vuol dire «non lo so», non zero.

    Torna `{ritmo_saltati, soglia_abbandonati, credito_mancato, chiavi}`.
    """
    import shlex
    filtro = (" | awk '$1 >= \"%s\"'" % da_istante) if da_istante else ""
    copione = ("cat /var/lib/rete11/registro.log%s | grep -aF -e %s\n"
               % (filtro, " -e ".join(shlex.quote(m) for m in MOTIVI_DEL_RITMO)))
    _, testo, _ = nucleo.dentro(desktop, copione, secondi=240)
    return conti_del_ritmo_dal_testo(testo, chi)


def conti_del_ritmo_dal_testo(testo, chi=None):
    """La parte PURA di `conti_del_ritmo()` — quella che `--certifica` attraversa."""
    import re as _re
    righe = (testo or "").splitlines()
    if chi:
        righe = [r for r in righe if ("[%s]" % chi) in r]
    u = "\n".join(righe)
    c = {"ritmo_saltati": None, "soglia_abbandonati": None,
         "credito_mancato": None, "chiavi": len(_re.findall(r"SPEDITO: CHIAVE", u))}
    m = None
    for r in righe:
        x = _re.search(r"(\d+) fotogrammi NON PARTITI", r)
        if x:
            m = x
    if m:
        c["ritmo_saltati"] = int(m.group(1))
    m = None
    for r in righe:
        x = _re.search(r"abbandonati per soglia (\d+), e NON ACCETTATI per "
                       r"credito mancato (\d+)", r)
        if x:
            m = x
    if m:
        c["soglia_abbandonati"] = int(m.group(1))
        c["credito_mancato"] = int(m.group(2))
    return c


def giudizio_dei_numeri(conti):
    """⭐ `(esito, perche, misure)` — la catena dei riferimenti, dai soli numeri.

    La regola, e non ce n'e' una seconda:
      **se il server ha buttato fotogrammi gia' codificati e NESSUNA chiave e'
      uscita oltre a quella d'apertura, la catena e' rotta e nessuno l'ha
      ricucita** ⇒ ROSSO.

    ⛔ Non si pretende «una chiave per ogni scarto»: `[M]` dopo la cura, 24
       scarti sono stati pagati con 8 chiavi — una chiave ne ripara piu' d'uno
       quando cadono vicini, e pretendere 1:1 sarebbe un rosso falso sul
       prodotto curato.
    ⚠ Quando i numeri non ci sono (sessione ancora aperta, registro tagliato)
      ⇒ **3**, mai rosso.
    """
    buttati = [conti.get(k) for k in ("ritmo_saltati", "soglia_abbandonati",
                                      "credito_mancato")]
    if all(x is None for x in buttati):
        return CIECO, ("dal registro non esce nessun conto degli scarti: le "
                       "righe di riepilogo escono alla CHIUSURA della sessione, "
                       "e qui non ci sono"), dict(conti)
    tot = sum(x for x in buttati if x is not None)
    chiavi = conti.get("chiavi")
    if chiavi is None:
        return CIECO, "non so quante chiavi sono uscite", dict(conti)
    riparatrici = max(0, chiavi - 1)          # la prima e' obbligatoria (§5.2)
    misure = dict(conti)
    misure.update(buttati_in_tutto=tot, chiavi_riparatrici=riparatrici)
    if tot == 0:
        return VERDE, ("il server non ha buttato nessun fotogramma gia' "
                       "codificato: non c'era niente da ricucire (chiavi %d)"
                       % chiavi), misure
    if riparatrici == 0:
        return ROSSO, ("la catena dei riferimenti e' rotta e nessuno l'ha "
                       "ricucita: %d fotogrammi buttati (ritmo %s, soglia %s, "
                       "credito %s) e UNA SOLA chiave in tutta la sessione — "
                       "quella d'apertura"
                       % (tot, conti.get("ritmo_saltati"),
                          conti.get("soglia_abbandonati"),
                          conti.get("credito_mancato"))), misure
    return VERDE, ("%d fotogrammi buttati e %d chiavi oltre a quella "
                   "d'apertura: qualcuno ha ricucito.  ⚠ Questo giudice non "
                   "sa dire se ha ricucito ABBASTANZA — quello lo dice "
                   "l'occhio" % (tot, riparatrici)), misure


# ═══════════════════════════════════════════════════════════════════════════
#  L'AGGANCIO ALLA SUITE — ⛔ senza toccare `stress_nucleo.py`
# ═══════════════════════════════════════════════════════════════════════════
NOME_SCENA_SCARICA = "testimone-scarico"


def deposita_scena(nucleo, desktop, dove=DOVE_NELLA_SCATOLA):
    """⭐ Scrive la scena DENTRO la scatola e la registra in `nucleo.SCENE`.

    Da qui in poi `nucleo.scena(desktop, "testimone", chi)` funziona come per le
    altre scene.  ⛔ Il file arriva da stdin (`podman exec -i`), non da una copia
    in `/media/REMOTIX/rete11`: le due copie dei banchi sono gia' costate un'ora
    (trappola 1 in testa a `stress_nucleo.py`).

    Torna `(fatto, perche)`.
    """
    b = base64.b64encode(scena_html().encode("utf-8")).decode("ascii")
    _, u, e = nucleo.dentro(desktop,
                            "echo %s | base64 -d > %s && wc -c < %s\n" % (b, dove, dove),
                            secondi=90)
    try:
        byte = int((u or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        return False, "la scena non si e' scritta in %s: %s" % (dove, " ".join(((u or "") + (e or "")).split())[:200])
    nucleo.SCENE[NOME_SCENA] = (dove, "la scena TESTIMONE: campo dichiarato "
                                      "piu' rumore (%d byte)" % byte)
    # ⭐ E il CONTROLLO NEGATIVO accanto: la stessa identica scena senza il
    #   motore.  ⛔ Stesso file, non una seconda copia: cambia solo la domanda.
    nucleo.SCENE[NOME_SCENA_SCARICA] = (dove + "?motore=no",
                                        "la scena TESTIMONE SENZA carico: il "
                                        "controllo negativo di §1.49")
    return True, ("scena testimone in %s (%d byte), registrata come «%s» e «%s»"
                  % (dove, byte, NOME_SCENA, NOME_SCENA_SCARICA))


def foto(browser):
    """⭐ Una fotografia della TELA, in byte, comunque il guidatore la dia.

    ⛔⛔ E QUESTO NON E' UN DOPPIONE DI `_comune.foto()` — 23 set 2026.
       `Browser.fotografa()` gira a `fotografa_tela()` dei due guidatori, e
       tutt'e due tornano una **coppia** `(byte, perche)` (`12-client-veri.py`
       righe ~447 e ~708).  `scenari/_comune.py:foto()` prova `bytes`, prova
       `str`, e per tutto il resto torna `None` ⇒ **su una coppia torna sempre
       `None`**: chi la usa non ha mai una fotografia, e non lo scopre perche'
       `None` e' anche il modo legittimo di dire «non ho potuto guardare».
       ⚠ Segnalato a chi tiene `_comune.py`; qui si scarta la coppia e basta,
         perche' un occhio che non riceve mai un pixel non e' un occhio.
    """
    d = browser.fotografa()
    if isinstance(d, tuple):                     # ⭐ (byte, perche)
        d = d[0]
    if isinstance(d, (bytes, bytearray)):
        return bytes(d)
    if isinstance(d, str):
        if d.startswith("data:"):
            d = d.split(",", 1)[1]
        try:
            return base64.b64decode(d)
        except Exception:                        # noqa: BLE001
            return None
    return None


def guarda_per(foto, quante=None, cornice=None):
    """Giudica una lista di PNG, riusando la cornice della prima foto buona.

    ⭐ Riusare la cornice non e' un'ottimizzazione: quando un guasto e' grosso
       mangia anche il magenta, e senza cornice il lettore direbbe «non lo so»
       proprio sul guasto che deve vedere.  ⇒ La geometria si fissa su una foto
       SANA e non si rimette piu' in discussione.
    """
    fuori = []
    for p in (foto or [])[:quante] if quante else (foto or []):
        r = guarda(p, cornice)
        if cornice is None and r.get("cornice") and r.get("visto"):
            cornice = tuple(r["cornice"])
        fuori.append(r)
    return fuori, cornice


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE — ⛔ prima si prova che sa dire di NO
# ═══════════════════════════════════════════════════════════════════════════
GUAI = 0
QUANTE = 0


def prova(nome, ottenuto, atteso_):
    global GUAI, QUANTE
    QUANTE += 1
    ok = (ottenuto == atteso_)
    if not ok:
        GUAI += 1
    print("   %s %-58s %s%s" % ("⭐" if ok else "⛔", nome, ottenuto,
                                "" if ok else "   (volevo %s)" % (atteso_,)))
    return ok


def _disegna(passo, guasto=None, scala=1.0, rumore=True):
    """⭐ La scena disegnata QUI, in Python, dalle stesse costanti.

    Serve alla certificazione pura: ⛔ non e' una seconda copia della scena — e'
    la LETTURA di quel che la scena dichiara, e se le due divergessero sarebbe
    proprio questo a dirlo.

    `guasto` e' una funzione `(array) -> array` che sporca l'immagine.
    """
    np = _numpy()
    W, H = int(1280 * scala), int(720 * scala)
    a = np.zeros((H, W, 3), dtype=np.float32)
    if rumore:
        rng = np.random.default_rng(7)
        a[:, :, :] = rng.integers(0, 256, size=(H, W, 3)).astype(np.float32)
    cx0, cy0 = int(W * CAMPO[0]), int(H * CAMPO[1])
    cx1, cy1 = int(W * CAMPO[2]), int(H * CAMPO[3])
    B = max(10, int(round(H * 0.016)))
    a[cy0:cy1, cx0:cx1, :] = np.asarray(MAGENTA, dtype=np.float32)
    ix0, iy0 = cx0 + B, cy0 + B
    iw, ih = (cx1 - cx0) - 2 * B, (cy1 - cy0) - 2 * B
    for r in range(RIGHE):
        Y0 = iy0 + int(round(r * ih / float(RIGHE)))
        Y1 = iy0 + int(round((r + 1) * ih / float(RIGHE)))
        for k in range(COLONNE):
            X0 = ix0 + int(round(k * iw / float(COLONNE)))
            X1 = ix0 + int(round((k + 1) * iw / float(COLONNE)))
            a[Y0:Y1, X0:X1, :] = np.asarray(
                TAVOLOZZA[atteso(r, k, passo)], dtype=np.float32)
    if guasto:
        a = guasto(a)
    return a


def _png(a):
    from PIL import Image
    np = _numpy()
    b = io.BytesIO()
    Image.fromarray(np.clip(a, 0, 255).astype("uint8"), "RGB").save(b, "PNG")
    return b.getvalue()


def certifica():
    """⛔ PRIMA si prova che sa dire di NO, e poi lo si usa."""
    print("═" * 78)
    print("  stress_occhio — LA CERTIFICAZIONE")
    print("═" * 78)
    try:
        _numpy()
        from PIL import Image                    # noqa: F401
    except Exception as e:                       # noqa: BLE001
        print("   ⛔ manca numpy o PIL: %s" % e)
        return 2

    print("\n 1 · LA TAVOLA — la stessa in Python e in JavaScript")
    prova("la tavola ha una voce per cella", len(TAVOLA), RIGHE * COLONNE)
    prova("i valori stanno nei %d passi" % PASSI,
          (min(TAVOLA), max(TAVOLA)), (0, PASSI - 1))
    # ⭐ I primi otto valori di MINSTD dal seme 1 — inchiodati qui, cosi' il
    #   giorno che qualcuno tocca il generatore la certificazione lo dice.
    #   `[M]` 23 set 2026: questi OTTO numeri escono identici da `node` con il
    #   codice della scena — `var s=1; s=(s*16807)%2147483647; s%6` — e le due
    #   tavole da 240 voci sono state confrontate voce per voce: la stessa.
    prova("i primi otto valori di MINSTD", TAVOLA[:8], [1, 1, 5, 2, 4, 2, 0, 2])
    # ⛔ E la prova che i due linguaggi non divergono la si rifa' qui, con i
    #    numeri di JavaScript (float64) emulati: se un giorno qualcuno mettesse
    #    un moltiplicatore piu' grosso, JavaScript perderebbe i bit bassi IN
    #    SILENZIO e il banco accuserebbe il prodotto di un difetto suo.
    sf, tf = 1.0, []
    for _ in range(RIGHE * COLONNE):
        sf = float((sf * 16807.0) % 2147483647.0)
        tf.append(int(sf) % PASSI)
    prova("la stessa tavola coi numeri di JavaScript (float64)", tf == TAVOLA, True)
    prova("non e' una formula regolare (i valori non si ripetono a righe)",
          TAVOLA[:COLONNE] == TAVOLA[COLONNE:2 * COLONNE], False)
    prova("la scena porta le stesse costanti", "var COLONNE=%d, RIGHE=%d" % (COLONNE, RIGHE)
          in scena_html(), True)

    print("\n 2 · LA CORNICE — la scena dice DOVE sta")
    sana = _disegna(0)
    c = trova_cornice(sana)
    prova("la cornice si trova", c is not None, True)
    if c:
        W, H = sana.shape[1], sana.shape[0]
        B = max(10, int(round(H * 0.016)))
        atteso_c = (int(W * CAMPO[0]) + B, int(H * CAMPO[1]) + B,
                    int(W * CAMPO[2]) - B, int(H * CAMPO[3]) - B)
        prova("ed e' quella giusta (±2 px)",
              all(abs(c[i] - atteso_c[i]) <= 2 for i in range(4)), True)
    np = _numpy()
    prova("su un'immagine SENZA cornice torna None",
          trova_cornice(np.zeros((400, 600, 3), dtype=np.float32)) is None, True)

    print("\n 3 · LA FOTOGRAFIA SANA — deve dare zero celle guaste")
    for passo in range(PASSI):
        r = guarda(_png(_disegna(passo)))
        prova("passo %d: guaste" % passo, (r["guaste"], r["passo"]), (0, passo))

    print("\n 4 · LA SCALA — la fotografia puo' essere ridotta (Chrome la porta a 640)")
    for s in (0.5, 0.75, 1.5):
        r = guarda(_png(_disegna(2, scala=s)))
        prova("scala %.2f: guaste su %d celle" % (s, RIGHE * COLONNE),
              (r["guaste"], r["passo"]), (0, 2))

    print("\n 5 · ⛔ I GUASTI FINTI — e qui DEVE dire di no")

    def scambia_tessere(a):
        """Due blocchi di 64x64 scambiati fra loro — la «tessera sfalsata»."""
        np = _numpy()
        b = a.copy()
        h, w = a.shape[0], a.shape[1]
        y0, y1 = int(h * 0.25), int(h * 0.55)
        x0, x1 = int(w * 0.20), int(w * 0.70)
        t = b[y0:y0 + 64, x0:x0 + 64, :].copy()
        b[y0:y0 + 64, x0:x0 + 64, :] = b[y1:y1 + 64, x1:x1 + 64, :]
        b[y1:y1 + 64, x1:x1 + 64, :] = t
        return b

    def striscia_vecchia(a, passo_vecchio=3):
        """Una fascia intera rimasta a un fotogramma di prima: pulitissima e
        completamente falsa.  ⛔ E' il guasto che `sporche` NON vede, e per
        questo `discordi` esiste."""
        vecchia = _disegna(passo_vecchio)
        b = a.copy()
        h = a.shape[0]
        y0, y1 = int(h * 0.30), int(h * 0.50)
        b[y0:y1, :, :] = vecchia[y0:y1, :, :]
        return b

    r = guarda(_png(_disegna(0, guasto=scambia_tessere)))
    prova("due tessere 64x64 scambiate ⇒ celle sporche", r["sporche"] > 0, True)
    print("       [M] sporche=%d discordi=%d quota=%.3f"
          % (r["sporche"], r["discordi"], r["quota_guaste"]))
    e, p, _ = giudizio([r] * 3)
    prova("   ⇒ il verdetto e' ROSSO", e, ROSSO)

    r2 = guarda(_png(_disegna(0, guasto=striscia_vecchia)))
    prova("una fascia da un fotogramma vecchio ⇒ celle discordi",
          r2["discordi"] > 0, True)
    print("       [M] sporche=%d discordi=%d quota=%.3f"
          % (r2["sporche"], r2["discordi"], r2["quota_guaste"]))
    e, p, _ = giudizio([r2] * 3)
    prova("   ⇒ il verdetto e' ROSSO", e, ROSSO)

    print("\n 6 · ⭐ E DEVE SAPER DIRE «NON LO SO» invece di un rosso falso")
    e, p, _ = giudizio([])
    prova("nessuna fotografia ⇒ 3", e, CIECO)
    e, p, _ = giudizio([guarda(b"non e' un png")] * 5)
    prova("fotografie illeggibili ⇒ 3", e, CIECO)
    e, p, _ = giudizio([guarda(_png(np.zeros((400, 600, 3), dtype=np.float32)))] * 5)
    prova("una tela nera (non la mia scena) ⇒ 3, non rosso", e, CIECO)
    r = guarda(_png(_disegna(1)))
    e, p, _ = giudizio([r, r])
    prova("due sole fotografie ⇒ 3 (sotto il minimo)", e, CIECO)
    e, p, _ = giudizio([r, r, r])
    prova("tre fotografie sane ⇒ VERDE", e, VERDE)

    print("\n 7 · ⭐ UNA SOLA FOTOGRAFIA GUASTA SU VENTI NON FA UN ROSSO")
    buone = [guarda(_png(_disegna(i % PASSI))) for i in range(19)]
    cattiva = guarda(_png(_disegna(0, guasto=scambia_tessere)))
    e, p, _ = giudizio(buone + [cattiva])
    prova("1 su 20 ⇒ verde (uno strappo d'istante non accusa)", e, VERDE)
    e, p, _ = giudizio(buone[:10] + [cattiva] * 5)
    prova("5 su 15 ⇒ ROSSO", e, ROSSO)

    print("\n 8 · ⭐ E DEVE DIRE DI NO A UNA SOLA FOTOGRAFIA DEVASTATA")
    devastata = guarda(_png(_disegna(0, guasto=striscia_vecchia)))
    buone20 = [guarda(_png(_disegna(i % PASSI))) for i in range(20)]
    e, p, m = giudizio(buone20 + [devastata])
    prova("1 devastata su 21 ⇒ ROSSO (l'8,3%% che era passato verde)", e, ROSSO)
    prova("   e lo dice", "DEVASTATE" in p, True)

    print("\n 9 · ⭐ IL SECONDO GIUDICE, quello sui numeri")
    # ⛔ Le due misure vere del 23 settembre 2026, prima e dopo `7e0c0e2`.
    prima = {"ritmo_saltati": 24, "soglia_abbandonati": 0, "credito_mancato": 0,
             "chiavi": 1}
    dopo = {"ritmo_saltati": 0, "soglia_abbandonati": 0, "credito_mancato": 0,
            "chiavi": 8}
    e, p, _ = giudizio_dei_numeri(prima)
    prova("prima della cura (24 buttati, 1 chiave) ⇒ ROSSO", e, ROSSO)
    e, p, _ = giudizio_dei_numeri(dopo)
    prova("dopo la cura (0 buttati, 8 chiavi) ⇒ VERDE", e, VERDE)
    e, p, _ = giudizio_dei_numeri({"ritmo_saltati": None,
                                   "soglia_abbandonati": None,
                                   "credito_mancato": None, "chiavi": 3})
    prova("numeri che non ci sono ⇒ 3, non rosso", e, CIECO)
    # ⛔ E IL PUNTO CIECO, scritto come prova: il giro di `rete11-kde` prima
    #    della cura — 47 buttati, 2 chiavi — per i numeri e' VERDE, e l'occhio
    #    ci ha trovato 26 fotografie sopra soglia su 313.
    e, p, _ = giudizio_dei_numeri({"ritmo_saltati": 47, "soglia_abbandonati": 0,
                                   "credito_mancato": 0, "chiavi": 2})
    prova("⚠ il punto cieco dichiarato (47 buttati, 2 chiavi) ⇒ verde", e, VERDE)
    testo = ("04:45:57 rcp [occhio1] il regolatore del ritmo: ACCESO — "
             "47 fotogrammi NON PARTITI perche' l'arretrato\n"
             "04:45:57 rcp [occhio1] la soglia della coda video: ACCESA — delta "
             "TENUTI 3, abbandonati per soglia 0, e NON ACCETTATI per credito "
             "mancato 0 (§2.3)\n"
             "04:44:58 rcp [occhio1] fotogramma 1 SPEDITO: CHIAVE 0x0301\n"
             "04:45:50 rcp [occhio1] fotogramma 2951 SPEDITO: CHIAVE 0x0301\n"
             "04:45:50 rcp [altro] fotogramma 7 SPEDITO: CHIAVE 0x0301\n")
    c = conti_del_ritmo_dal_testo(testo, "occhio1")
    prova("il lettore del registro (righe VERE del 23 set)",
          (c["ritmo_saltati"], c["soglia_abbandonati"], c["credito_mancato"],
           c["chiavi"]), (47, 0, 0, 2))
    prova("   e senza `chi` prende anche le righe dell'altro",
          conti_del_ritmo_dal_testo(testo)["chiavi"], 3)

    print("\n" + "═" * 78)
    print("  %d prove, %d guai" % (QUANTE, GUAI))
    print("═" * 78)
    return 1 if GUAI else 0


def main():
    p = argparse.ArgumentParser(description="gli occhi del giudice")
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--scena", action="store_true", help="stampa la scena HTML")
    p.add_argument("--guarda", nargs="*", default=None, metavar="PNG",
                   help="giudica delle fotografie gia' prese")
    p.add_argument("--cartella", default="", metavar="DIR",
                   help="giudica tutti i `*.png` di una cartella, in ordine")
    p.add_argument("--cornice", default="", help="x0,y0,x1,y1 da imporre")
    p.add_argument("--muto", action="store_true",
                   help="solo il verdetto e i numeri, non riga per riga")
    a = p.parse_args()
    if a.cartella:
        import glob
        a.guarda = sorted(glob.glob(os.path.join(a.cartella, "*.png")))
    if a.scena:
        sys.stdout.write(scena_html())
        return 0
    if a.guarda is not None:
        c = tuple(int(x) for x in a.cornice.split(",")) if a.cornice else None
        foto = []
        for n in a.guarda:
            with open(n, "rb") as f:
                foto.append(f.read())
        rapporti, c = guarda_per(foto, cornice=c)
        if not a.muto:
            for n, r in zip(a.guarda, rapporti):
                print("%-22s %s" % (os.path.basename(n),
                                    json.dumps({k: v for k, v in r.items()
                                                if k not in ("cornice", "celle")},
                                               ensure_ascii=False)))
        e, perche, misure = giudizio(rapporti)
        print("\nesito %d — %s" % (e, perche))
        print(json.dumps(misure, ensure_ascii=False, indent=1))
        return e
    if a.certifica:
        return certifica()
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
