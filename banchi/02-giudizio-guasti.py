#!/usr/bin/env python3
"""02-giudizio-guasti.py — ⛔ I GUASTI CHE IL METRO DEVE BOCCIARE.

    python3 02-giudizio-guasti.py --elenco
    python3 02-giudizio-guasti.py --applica riga --dentro pagina.rgb48 \\
            --fuori pagina-guasta.rgb48 --scena mira.json
    python3 02-giudizio-guasti.py --riga-catalogo          (per §3.3 del mandato)

===========================================================================
⛔ PERCHE' ESISTE, E PERCHE' E' SCRITTO PRIMA DEL PRODOTTO

`PIANO.md` §0.3 regola 4 e `LEZIONI.md` §1.2: **il banco si certifica prima di
essere creduto**.  E `01-b12-guasti.py` lo dice nella forma piu' dura che
questo progetto abbia prodotto:

    ⛔ *«Un banco che non e' mai diventato rosso non e' pulito: e' NON
       CERTIFICATO.»*

Un metro dei pixel e' il posto dove quella regola morde di piu', perche' la
codifica e' con perdita e **ogni soglia lasca produce un verde**.  Da cui
questo file: il metro non si certifica «girando su un caso sano», si
certifica **innestando uno per uno i guasti che deve bocciare** e
pretendendo che li boccia — ⛔ e che li boccia con lo strumento GIUSTO.

===========================================================================
⛔ LA REGOLA DELLA MARCA, PRESA DA `01-b12-guasti.py` E QUI VALE DOPPIO

Non basta che il metro diventi rosso: deve diventare rosso **per la ragione
che ci si aspettava**.  Ogni guasto qui sotto dichiara lo **strumento** che
lo deve bocciare, e la certificazione vale solo se:

   · il giro guasto boccia, e fra i bocciati c'e' quello strumento;
   · ⛔ **e il giro sano NON lo bocciava gia'.**

La seconda meta' e' quella che ci si dimentica (rilievo R12-A.3, 11 agosto):
uno strumento che dice no sempre non e' uno strumento, e' un modo di
certificare senza guardare.

⚠ E qui c'e' di piu': quattro dei nove guasti **passerebbero il PSNR**.  Se
la certificazione si accontentasse di «e' diventato rosso», un metro che
boccia tutto per un motivo qualunque risulterebbe certificato — e poi in
esercizio boccerebbe anche i giri sani, e verrebbe allargato finche' non
promuove piu' niente.  E' cosi' che una soglia muore.
===========================================================================
"""
import argparse
import json
import sys

import numpy as np

# Ogni voce:  che cosa fa · chi lo deve bocciare · perche' il PSNR non basta
GUASTI = {
    "nero": dict(
        titolo="il fotogramma dipinto e' tutto nero",
        strumento=["M1", "M3"],
        dimostra="il caso facile, ed e' qui per fare da metro ai difficili: se "
                 "il metro non prendesse nemmeno questo, non prenderebbe niente",
    ),
    "nero-doppio": dict(
        titolo="⛔ NERI TUTTI E DUE — la cattura E la pagina",
        strumento=["M-V"],
        # ⛔ E l'atteso e' **2**, non 1: con la cattura nera il metro non ha
        #    piu' un ingresso da giudicare e deve dire «non ho potuto
        #    guardare».  Un metro che bocciasse starebbe accusando il client di
        #    un difetto della SESSIONE.
        stato=2,
        dimostra="⛔ IL GUASTO PIU' PERICOLOSO DELLA FASE.  `PIANO.md` fase 2: "
                 "una sessione GNOME headless senza `--virtual-monitor` parte "
                 "**viva, completa e nera**.  Due fotogrammi neri hanno PSNR "
                 "**infinito**: ogni strumento di somiglianza li promuove.  Solo "
                 "M-V — che guarda se nella scena c'e' qualcosa PRIMA di "
                 "confrontare — puo' dire di no",
    ),
    "riga": dict(
        titolo="il fotogramma spostato di UNA riga",
        strumento=["M0"],
        dimostra="su una scena morbida questo guasto vale un millesimo di LSB e "
                 "il PSNR resta a 60 dB.  Lo prendono i pettini a passo 1 px "
                 "della mira, ed e' M0 — che e' un confronto fra scorrimenti, "
                 "non una soglia in dB",
    ),
    "colonna": dict(
        titolo="il fotogramma spostato di UNA colonna",
        strumento=["M0"],
        dimostra="il gemello del precedente sull'altro asse: un ritaglio "
                 "sbagliato di un pixel in orizzontale e' il difetto tipico di "
                 "un `visibleRect` letto male",
    ),
    "precedente": dict(
        titolo="il fotogramma del GIRO PRECEDENTE",
        strumento=["M6"],
        dimostra="e' un fotogramma perfetto, decodificato bene, con i colori "
                 "giusti e i 10 bit giusti: **tutti** gli strumenti lo "
                 "promuovono tranne M6.  ⚠ E M6 esiste solo se la scena e' "
                 "cambiata fra i due giri — e' `CODER.md` §3.2 che diventa una "
                 "condizione di validita' invece di un consiglio",
    ),
    "otto-bit": dict(
        titolo="10 bit troncati a 8 lungo la catena",
        strumento=["M7"],
        dimostra="⛔ dopo la conversione a 8 bit della tela la differenza e' al "
                 "massimo UN LSB: PSNR ≈ 58 dB, cioe' **sopra ogni soglia "
                 "sana**.  Nessun confronto di pixel puo' vederlo, e chi "
                 "scrivesse «i pixel coincidono ⇒ 10 bit» farebbe la forma "
                 "d'errore E1.  Lo prende M7 sulle DUE rampe, e solo sul lato "
                 "dove la profondita' esiste ancora",
    ),
    "piani": dict(
        titolo="i piani del colore scambiati (R ⟷ B)",
        strumento=["M4"],
        dimostra="⛔ i tre riquadri della mira hanno **la stessa luminanza** "
                 "apposta: scambiare R e B non muove Y di un LSB, e M1a, M2 e M3 "
                 "— che guardano la luminanza — lo promuovono tutti e tre.  Lo "
                 "prende M4, che e' un confronto di correlazioni",
    ),
    "gamma": dict(
        titolo="gamma limitata letta come piena (16-235 steso su 0-255)",
        strumento=["M5"],
        dimostra="e' il guasto che il browser produce da solo quando il "
                 "codificatore **non scrive il VUI**: senza `video_full_range_flag` "
                 "il decodificatore indovina.  Firma: guadagno 255/219 = 1,164. "
                 "⚠ L'immagine resta riconoscibile e «sembra giusta»: e' il "
                 "difetto che un occhio umano non giura",
    ),
    "blocco": dict(
        titolo="un blocco 64×64 azzerato",
        strumento=["M3"],
        dimostra="1/506 dell'immagine: sposta il PSNR globale di **0,03 dB**, "
                 "cioe' dentro il rumore di qualunque soglia.  La media lo "
                 "annega; il blocco peggiore no.  ⛔ E si innesta SUI PIXEL, "
                 "non sul flusso, e non e' una scorciatoia: F2.3 ha misurato "
                 "(12 ago 2026) che girando un byte nell'intestazione di uno "
                 "slice il fotogramma esce **identico bit per bit** — il codec "
                 "non e' un rivelatore di corruzione.  Un guasto innestato sul "
                 "flusso non e' garantito produrre una differenza, e un guasto "
                 "che puo' non esserci non certifica niente",
    ),
    "matrice": dict(
        titolo="⛔ la pagina dichiara BT.601, la cattura BT.709",
        strumento=["M-C"],
        dimostra="cucitura di F2.3: un confronto fatto con la matrice sbagliata "
                 "**misura la matrice**, non la catena.  ⛔ E il guasto non e' "
                 "nei pixel: e' nella DICHIARAZIONE, e va preso prima di "
                 "confrontare — un numero dato in quelle condizioni non e' "
                 "interpretabile, e un numero non interpretabile e' peggio di "
                 "nessun numero perche' entra nei documenti come misura",
    ),
    "dopo-reset": dict(
        titolo="il fotogramma consegnato DOPO un RESET_STREAM",
        strumento=["M8"],
        dimostra="cucitura di F2.4: FIN ⇒ completo, RESET ⇒ si butta.  ⛔ Con i "
                 "pixel giusti questo guasto e' **invisibile a M0..M7**, e lo "
                 "dev'essere: i pixel non portano l'identita' dello stream.  Lo "
                 "prende M8 leggendo quel che la pagina dichiara — un anello "
                 "debole per costruzione, che vale solo insieme al registro di "
                 "F2.4 e non al posto suo",
    ),
    "ribaltato": dict(
        titolo="l'immagine ribaltata in orizzontale",
        strumento=["M-V"],
        dimostra="il PSNR crolla e boccerebbe comunque — ma direbbe «i pixel non "
                 "coincidono», che manda a cercare dalla parte sbagliata.  I "
                 "marcatori d'angolo lo chiamano per nome: **e' ribaltata**",
    ),
}


def applica(nome, img, zone, altro=None):
    """img: float64 [h,w,3] in 0..1.  Ritorna l'immagine guasta."""
    a = img.copy()
    if nome == "nero" or nome == "nero-doppio":
        return np.zeros_like(a)
    if nome == "riga":
        return np.roll(a, 1, axis=0)
    if nome == "colonna":
        return np.roll(a, 1, axis=1)
    if nome == "precedente":
        if altro is None:
            raise SystemExit("⛔ «precedente» vuole --altro: il fotogramma del "
                             "giro prima non si inventa")
        return altro.copy()
    if nome == "otto-bit":
        return np.round(a * 255.0) / 255.0
    if nome == "piani":
        return a[:, :, ::-1].copy()
    if nome == "gamma":
        return np.clip((a - 16.0 / 255.0) * (255.0 / 219.0), 0, 1)
    if nome == "blocco":
        h, w = a.shape[:2]
        y0, x0 = (h // 2) & ~63, (w // 2) & ~63
        a[y0:y0 + 64, x0:x0 + 64, :] = 0.0
        return a
    if nome == "ribaltato":
        return a[:, ::-1, :].copy()
    raise SystemExit("⛔ guasto sconosciuto: %s" % nome)


def guasta_yuv10(dentro, fuori, nome):
    """⛔ Il troncamento a 8 bit si innesta sul YUV a 10 bit, non sull'RGB.

    Sull'RGB a 8 bit della tela il guasto **non esiste piu'**: e' gia' stato
    fatto dalla tela stessa, ed e' legittimo.  Chiedere al metro di vederlo la'
    sarebbe chiedergli di distinguere due cose che a 8 bit sono lo stesso
    numero.  Qui si spengono i due bit bassi di ogni campione, che e' quel che
    fa una catena che passa da un decodificatore a 8 bit e poi ri-espande.
    """
    if nome != "otto-bit":
        raise SystemExit("⛔ sul YUV a 10 bit si innesta solo «otto-bit»")
    a = np.fromfile(dentro, dtype="<u2")
    if a.size == 0:
        raise SystemExit("⛔ il YUV di partenza e' vuoto")
    ((a >> 2) << 2).astype("<u2").tofile(fuori)


def leggi(percorso, w, h):
    d = open(percorso, "rb").read()
    if percorso.endswith(".rgb48"):
        return np.frombuffer(d[:w * h * 6], "<u2").reshape(h, w, 3).astype(np.float64) / 65535.0
    if percorso.endswith(".rgb24"):
        return np.frombuffer(d[:w * h * 3], np.uint8).reshape(h, w, 3).astype(np.float64) / 255.0
    if percorso.endswith(".png"):
        from PIL import Image
        return np.asarray(Image.open(percorso).convert("RGB")).astype(np.float64) / 255.0
    raise SystemExit("⛔ estensione sconosciuta in lettura: %s" % percorso)


def scrivi(percorso, a):
    if percorso.endswith(".rgb48"):
        np.clip(np.round(a * 65535.0), 0, 65535).astype("<u2").tofile(percorso)
    elif percorso.endswith(".rgb24"):
        np.clip(np.round(a * 255.0), 0, 255).astype(np.uint8).tofile(percorso)
    elif percorso.endswith(".png"):
        from PIL import Image
        Image.fromarray(np.clip(np.round(a * 255.0), 0, 255).astype(np.uint8)).save(percorso)
    else:
        raise SystemExit("⛔ estensione sconosciuta in scrittura: %s" % percorso)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--elenco", action="store_true")
    p.add_argument("--riga-catalogo", action="store_true")
    p.add_argument("--applica")
    p.add_argument("--dentro")
    p.add_argument("--fuori")
    p.add_argument("--altro")
    p.add_argument("--scena")
    a = p.parse_args()

    if a.elenco:
        for k, g in GUASTI.items():
            print("\n\033[1m%-12s\033[0m %s" % (k, g["titolo"]))
            print("   lo deve bocciare: %s" % ", ".join(g["strumento"]))
            print("   %s" % g["dimostra"])
        return 0

    if a.riga_catalogo:
        for k, g in GUASTI.items():
            print(json.dumps({
                "nome": "F2.6/" + k,
                "banco": "02-giudizio-confronto.sh",
                "comando": "bash banchi/02-giudizio-confronto.sh certifica " + k,
                "atteso_sano": "stato 0 (PROMOSSO), e %s fra gli OK"
                               % "+".join(g["strumento"]),
                "guasto_da_innestare": g["titolo"],
                "atteso_guasto": "stato %d (%s), e fra i bocciati %s"
                                 % (g.get("stato", 1),
                                    "BOCCIATO" if g.get("stato", 1) == 1
                                    else "NON MISURATO",
                                    "+".join(g["strumento"])),
                "marca": g["strumento"],
            }, ensure_ascii=False))
        return 0

    if not (a.applica and a.dentro and a.fuori and a.scena):
        p.print_help()
        return 2
    meta = json.load(open(a.scena))
    w, h = meta["larghezza"], meta["altezza"]
    if a.dentro.endswith(".yuv"):
        guasta_yuv10(a.dentro, a.fuori, a.applica)
        print("%s → %s  (guasto «%s» sul piano a 10 bit; lo deve bocciare %s)"
              % (a.dentro, a.fuori, a.applica,
                 ", ".join(GUASTI[a.applica]["strumento"])))
        return 0
    img = leggi(a.dentro, w, h)
    altro = leggi(a.altro, w, h) if a.altro else None
    scrivi(a.fuori, applica(a.applica, img, meta["zone"], altro))
    print("%s → %s  (guasto «%s»; lo deve bocciare %s)"
          % (a.dentro, a.fuori, a.applica, ", ".join(GUASTI[a.applica]["strumento"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
