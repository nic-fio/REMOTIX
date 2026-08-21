#!/usr/bin/env python3
"""06-b35-tempi.py — ⭐ le latenze del giro, dal registro, SENZA morire.

    python3 06-b35-tempi.py <giro.log>          le quattro latenze
    python3 06-b35-tempi.py --controllo         ⭐ il controllo positivo dello
                                                STRUMENTO, su un registro finto
                                                di cui si conosce la risposta

⛔ QUESTO FILE NASCE DA UN ATTREZZO CHE MORIVA, e i tre difetti che aveva
   valgono piu' del codice che li sostituisce.

   1. ⛔⛔ `ValueError: not enough values to unpack`.  ⚠ **Non era un difetto
      di python: era il registro.**  `src/registro.c` scrive ogni riga con
      TRE chiamate — `fprintf` dell'intestazione, `vfprintf` del corpo,
      `fputc('\\n')` — su uno `stderr` non bufferizzato, cioe' **tre write()
      separate**.  Padre e figlio appendono allo STESSO file: quando le
      write() di due processi si accavallano, il corpo di uno finisce dopo
      l'a-capo dell'altro e nasce una riga **senza marca temporale**.
      `[M]` 21 agosto 2026, `06-p/registro.log` (3,0 MB): **3 righe orfane su
      80** «tela CHIESTA al produttore» — il 3,8 %.
      ⇒ Qui le orfane si **recuperano** (l'ora e' quella della riga
      precedente: l'intestazione persa e' dello stesso millisecondo) e si
      **contano ad alta voce**.  ⛔ Buttarle in silenzio sarebbe `LEZIONI.md`
      §1.9: un campione che sparisce senza dirlo.

   2. ⛔ «il primo `b` dopo `a`» accoppiava lo STESSO evento a DUE richieste.
      `[M]` sullo stesso registro: `ADATTA_TELA girata → TELA spedita` dava
      **mediana 6,0 ms (0-57)** su n=30 — un numero **plausibile e falso**,
      perche' mescolava tre cose:
        · il giro pieno che finisce in `TELA(ADATTATA)`   ~44 ms
        · il rifiuto immediato `TELA(RIFIUTATA/NON_ORA)`  ~6 ms
        · uno **0** puro, dove la seconda `ADATTA_TELA` si prendeva la
          risposta della PRIMA, arrivata nello stesso millisecondo.
      ⇒ Qui ogni risposta si **consuma una volta sola**, e le due famiglie
      (`ADATTATA` e `NON_ORA`) si dichiarano **separate**: metterle sotto la
      stessa etichetta e' la forma **E2** del catalogo di `REVIEWER.md` §2.

   3. ⛔ `tela CHIESTA → TELA NUOVA` non si puo' accoppiare per ordine: quando
      la prima delle due richieste incatenate viene rifiutata, la sua
      `CHIESTA` resta **senza** risposta e si prenderebbe quella della
      seconda.  ⚠ Il registro pero' lo **dice**: la riga della tela nuova
      porta «chiesti al produttore LxA».  ⇒ Si accoppia su quel campo — un
      messaggio invece di una deduzione (forma **E12**).

⚠ Il TETTO.  Nessuna coppia oltre `--tetto` ms (difetto 1000) e' una coppia:
   e' l'evento del giro dopo.  ⛔ E quelle scartate si contano, non
   spariscono.

⚠ Ogni numero qui dentro e' preso su una **Intel UHD 730 integrata**, non su
   una scheda potente, e va letto col carico accanto (`06-b35-terreno.sh
   carico`).
"""
import argparse
import os
import re
import statistics
import sys

# ⛔ La marca temporale di `src/registro.c`: "%H:%M:%S.%03ld " e poi l'area.
#    Si pretende ESATTA: un `split()[0]` accettava qualunque cosa e moriva sul
#    primo intruso.
MARCA = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s")

GIRATA = "GIRATA al palco"
CHIESTA = "tela CHIESTA al produttore"
NUOVA = "TELA NUOVA DAL PALCO"
SPEDITA = "TELA spedita"

RE_MISURA = re.compile(r"(\d+)x(\d+)")
RE_CHIESTI = re.compile(r"chiesti al produttore (\d+)x(\d+)")
RE_ESITO = re.compile(r"TELA spedita: esito (\d+), motivo (\d+)")

# RCP.md §7.1 e `rcp.c:2906`.
ESITI = {(1, 0): "ADATTATA", (2, 3): "NON_ORA"}


def nome_esito(esito, motivo):
    return ESITI.get((esito, motivo), f"esito{esito}/motivo{motivo}")


class Registro:
    """Le righe del registro, con l'ora — e le orfane dichiarate."""

    def __init__(self):
        self.righe = []          # (ms, testo, orfana)
        self.orfane = 0
        self.senza_ora = 0       # orfane che nemmeno si recuperano

    def leggi(self, sorgente):
        ultima = None
        giorni = 0
        precedente = None
        for testo in sorgente:
            testo = testo.rstrip("\n")
            m = MARCA.match(testo)
            if m:
                t = ((int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])) * 1000
                     + int(m[4]))
                # ⚠ La mezzanotte: il registro porta solo %H:%M:%S, e senza
                #   questo un giro a cavallo delle 24 darebbe latenze
                #   NEGATIVE di 86 400 000 ms.
                if precedente is not None and t + 3600_000 < precedente:
                    giorni += 1
                precedente = t
                ultima = t + giorni * 86_400_000
                self.righe.append((ultima, testo, False))
            else:
                # ⛔ Riga orfana: l'intestazione se l'e' presa un altro
                #    processo.  Si recupera con l'ora dell'ultima riga
                #    buona — l'intestazione perduta era dello stesso
                #    millisecondo — e SI CONTA.
                self.orfane += 1
                if ultima is None:
                    self.senza_ora += 1
                    continue
                self.righe.append((ultima, testo, True))
        return self

    def eventi(self, sotto):
        return [(t, testo, orfana) for t, testo, orfana in self.righe
                if sotto in testo]


def misura_chiesta(testo):
    """La misura girata al palco: il SECONDO `LxA` della riga (quella buona).

    `rcp.c:6486` scrive «ADATTA_TELA <chiesta> → <buona> GIRATA al palco», e
    `cattura_ridimensiona()` riceve la **buona**.
    """
    tutte = RE_MISURA.findall(testo)
    if len(tutte) >= 2:
        return (int(tutte[1][0]), int(tutte[1][1]))
    if tutte:
        return (int(tutte[0][0]), int(tutte[0][1]))
    return None


def misura_chiesta_al_produttore(testo):
    tutte = RE_MISURA.findall(testo)
    return (int(tutte[0][0]), int(tutte[0][1])) if tutte else None


def accoppia(a, b, tetto, chiave_a=None, chiave_b=None):
    """Per ogni `a`, la prima `b` **non ancora consumata** che viene dopo.

    ⛔ Consumo unico: senza, due `a` nello stesso millisecondo si prendono la
       STESSA `b` e nasce un campione da 0 ms che non e' mai esistito.
    ⛔ Tetto: oltre `tetto` ms non e' una risposta, e' il giro dopo.
    ⛔ Se `chiave_a`/`chiave_b` ci sono, si accoppia solo a parita' di chiave
       — cioe' su quel che il registro DICE, non sull'ordine.

    Torna (campioni, spaiate, oltre_il_tetto, coppie).
    """
    presa = [False] * len(b)
    campioni, coppie = [], []
    spaiate = oltre = 0
    for ta, testo_a, _ in a:
        ka = chiave_a(testo_a) if chiave_a else None
        trovata = None
        for j, (tb, testo_b, _) in enumerate(b):
            if presa[j] or tb < ta:
                continue
            if chiave_b is not None and chiave_b(testo_b) != ka:
                continue
            trovata = j
            break
        if trovata is None:
            spaiate += 1
            continue
        d = b[trovata][0] - ta
        if d > tetto:
            oltre += 1
            continue
        presa[trovata] = True
        campioni.append(d)
        coppie.append((ta, b[trovata][0], b[trovata][1]))
    return campioni, spaiate, oltre, coppie


def dillo(nome, campioni, tentativi, spaiate, oltre, regola, dettaglio=False):
    if not campioni:
        print(f"    {nome}: NESSUN CAMPIONE ⛔ "
              f"(su {tentativi} tentativi · {spaiate} spaiate · "
              f"{oltre} oltre il tetto) — e «nessuno» non e' «zero»")
        return
    v = sorted(campioni)
    print(f"    {nome}:")
    print(f"        n={len(v)}/{tentativi}  mediana={statistics.median(v):.1f} ms"
          f"  min={min(v):.1f}  max={max(v):.1f}"
          + (f"  ⛔ spaiate {spaiate}" if spaiate else "")
          + (f"  ⛔ oltre il tetto {oltre}" if oltre else ""))
    print(f"        [{regola}]")
    if dettaglio:
        print(f"        campioni: {[round(x, 1) for x in v]}")


def conta(giro, tetto, dettaglio):
    girata = giro.eventi(GIRATA)
    chiesta = giro.eventi(CHIESTA)
    nuova = giro.eventi(NUOVA)
    spedita = giro.eventi(SPEDITA)

    print()
    # ⛔ DIFETTO DEL MIO ATTREZZO, TROVATO MISURANDO — 21 agosto 2026, sera.
    #    Qui c'era scritto «orfane (intestazione persa nell'intreccio)», cioe'
    #    una CAUSA, su un conto che sa vedere solo un EFFETTO: «questa riga non
    #    comincia con la marca».  ⚠ Sul giro sotto contesa il conto diceva 18,
    #    e tutte e 18 erano `[libopus @ 0x...] 1 frames left in the queue on
    #    closing` — di ffmpeg, non nostre.  ⇒ Il numero accusava `registro.c`
    #    di un intreccio che non c'era piu': e' il rosso all'imputato
    #    sbagliato, dentro l'attrezzo che dovrebbe smascherarlo.
    # ⇒ Adesso si dichiara l'effetto, e si separa quel che conta davvero: le
    #   righe senza marca **che diventano un evento**.  Solo quelle influenzano
    #   una latenza; le altre sono rumore di terzi nello stesso file.
    orf = sum(1 for _, _, o in girata + chiesta + nuova + spedita if o)
    print(f"    righe lette: {len(giro.righe)}"
          f"  ·  righe senza marca temporale: {giro.orfane}"
          + (f"  (⛔ {giro.senza_ora} prima di qualunque riga buona)"
             if giro.senza_ora else "")
          + f"  ·  tetto {tetto} ms")
    print(f"    eventi: GIRATA {len(girata)} · CHIESTA {len(chiesta)} · "
          f"NUOVA {len(nuova)} · SPEDITA {len(spedita)}")
    if orf:
        print(f"    ⛔ {orf} EVENTI arrivano da righe senza marca: l'ora e'"
              f" quella della riga precedente, non e' letta.")
        print(f"       ⚠ E' il segno che una riga NOSTRA e' stata spezzata"
              f" (tre `write()` per riga, padre e figlio sullo stesso file):"
              f" quelle latenze valgono meno.")
    elif giro.orfane:
        print(f"    ⚠ nessun evento arriva da righe senza marca: quelle"
              f" {giro.orfane} righe sono di ALTRI programmi che scrivono nello"
              f" stesso file (ffmpeg, libva, GLib), non righe nostre spezzate.")
    print()

    # 1 · il ridimensionamento a caldo, dentro il nostro server.
    c, sp, ol, _ = accoppia(girata, chiesta, tetto)
    dillo("① ADATTA_TELA girata → tela chiesta al produttore  "
          "(il RIDIMENSIONAMENTO A CALDO, tutto nostro)",
          c, len(girata), sp, ol, "rcp.c → figlio.c → cattura.c", dettaglio)

    # 2 · il compositore.  ⛔ per chiave: la richiesta rifiutata non ha risposta.
    c, sp, ol, _ = accoppia(
        chiesta, nuova, tetto,
        chiave_a=misura_chiesta_al_produttore,
        chiave_b=lambda t: ((int(RE_CHIESTI.search(t)[1]),
                             int(RE_CHIESTI.search(t)[2]))
                            if RE_CHIESTI.search(t) else None))
    dillo("② tela chiesta al produttore → TELA NUOVA DAL PALCO  "
          "(il COMPOSITORE, non noi)",
          c, len(chiesta), sp, ol,
          "Mutter · [M] 41,6 ms il 14 ago · accoppiate per «chiesti al produttore»",
          dettaglio)

    # 3 · da quando il palco risponde a quando il client lo sa.
    c, sp, ol, _ = accoppia(nuova, spedita, tetto)
    dillo("③ TELA NUOVA DAL PALCO → TELA spedita al client",
          c, len(nuova), sp, ol, "e' il «6 ms» del 15 agosto 2026", dettaglio)

    # 4 · il giro intero, SPACCATO PER ESITO.  ⛔ E2: `ADATTATA` e `NON_ORA`
    #     sotto la stessa etichetta sono due misure con un nome solo.
    c, sp, ol, coppie = accoppia(girata, spedita, tetto)
    famiglie = {}
    for (ta, tb, testo) in coppie:
        m = RE_ESITO.search(testo)
        nome = nome_esito(int(m[1]), int(m[2])) if m else "SENZA ESITO LEGGIBILE"
        famiglie.setdefault(nome, []).append(tb - ta)
    print(f"    ④ ADATTA_TELA girata → TELA spedita (IL GIRO INTERO, lato server)"
          f" — {len(c)}/{len(girata)} accoppiate"
          + (f"  ⛔ spaiate {sp}" if sp else "")
          + (f"  ⛔ oltre il tetto {ol}" if ol else ""))
    if not famiglie:
        print("        NESSUN CAMPIONE ⛔")
    for nome in sorted(famiglie):
        v = sorted(famiglie[nome])
        print(f"        {nome:<10s} n={len(v)}  mediana={statistics.median(v):.1f} ms"
              f"  min={min(v):.1f}  max={max(v):.1f}")
        if dettaglio:
            print(f"                   campioni: {[round(x, 1) for x in v]}")
    print()
    return {"girata": len(girata), "chiesta": len(chiesta),
            "nuova": len(nuova), "spedita": len(spedita),
            "orfane": giro.orfane,
            "famiglie": {k: sorted(v) for k, v in famiglie.items()}}


# ===========================================================================
# ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO — `LEZIONI.md` §1.9, seconda regola
# ===========================================================================
#
# ⛔ Un attrezzo che non sa trovare quel che c'e' di sicuro non puo' concludere
#    che qualcosa non c'e'.  Qui il registro e' **finto e noto**: due giri
#    interi con le latenze scritte a mano, piu' i tre veleni che hanno rotto
#    l'attrezzo vecchio — una riga ORFANA, due richieste nello STESSO
#    millisecondo, e una `CHIESTA` senza risposta.
FINTO = """\
10:00:00.000 rcp     ⭐ ADATTA_TELA 1280x800 → 1280x800 GIRATA al palco
10:00:00.003 cattura ⭐ tela CHIESTA al produttore: 1280x800 (`pw_stream_update_params`)
10:00:00.043 figlio  ⭐⭐ TELA NUOVA DAL PALCO: 640x480 → 1280x800 (chiesti al produttore 1280x800)
10:00:00.048 rcp     TELA spedita: esito 1, motivo 0, tela in vigore 1280x800 (§7.1)
10:00:01.000 rcp     ⭐ ADATTA_TELA 1600x900 → 1600x900 GIRATA al palco
10:00:01.006 rcp     TELA spedita: esito 2, motivo 3, tela in vigore 1280x800 (§7.1)
10:00:01.006 rcp     ⭐ ADATTA_TELA 1024x640 → 1024x640 GIRATA al palco
10:00:01.008 cattura ⭐ tela CHIESTA al produttore: 1600x900 (`pw_stream_update_params`)
10:00:01.009 wt      un pezzo di riga che ha perso l'intestazione:
⭐ tela CHIESTA al produttore: 1024x640 (`pw_stream_update_params`)
10:00:01.039 figlio  ⭐⭐ TELA NUOVA DAL PALCO: 1280x800 → 1024x640 (chiesti al produttore 1024x640)
10:00:01.045 rcp     TELA spedita: esito 1, motivo 0, tela in vigore 1024x640 (§7.1)
"""

# Quel che DEVE uscire, contato a mano sul registro qui sopra.
ATTESO = {
    "girata": 3, "chiesta": 3, "nuova": 2, "spedita": 3, "orfane": 1,
    # ① 0→3, 1000→1008, 1006→1009
    "uno": [3, 8, 3],
    # ② 1280x800: 3→43 = 40 · 1024x640: 1009→1039 = 30 · 1600x900: SPAIATA
    "due": [40, 30], "due_spaiate": 1,
    # ③ 43→48 = 5 · 1039→1045 = 6
    "tre": [5, 6],
    # ④ ADATTATA: 0→48 = 48 e 1006→1045 = 39 · NON_ORA: 1000→1006 = 6
    "adattata": [39, 48], "non_ora": [6],
}


def controllo():
    print(__doc__.split("\n")[0])
    print("\n⭐ CONTROLLO POSITIVO DELLO STRUMENTO — registro finto, risposta nota\n")
    giro = Registro().leggi(FINTO.splitlines())
    girata = giro.eventi(GIRATA)
    chiesta = giro.eventi(CHIESTA)
    nuova = giro.eventi(NUOVA)
    spedita = giro.eventi(SPEDITA)
    guai = []

    def verifica(nome, avuto, atteso):
        segno = "OK " if avuto == atteso else "⛔ "
        print(f"    {segno} {nome}: atteso {atteso} · avuto {avuto}")
        if avuto != atteso:
            guai.append(nome)

    verifica("righe orfane recuperate", giro.orfane, ATTESO["orfane"])
    verifica("eventi GIRATA", len(girata), ATTESO["girata"])
    verifica("eventi CHIESTA (⭐ una arriva da una riga ORFANA)",
             len(chiesta), ATTESO["chiesta"])
    verifica("eventi NUOVA", len(nuova), ATTESO["nuova"])
    verifica("eventi SPEDITA", len(spedita), ATTESO["spedita"])

    c, sp, ol, _ = accoppia(girata, chiesta, 1000)
    verifica("① girata → chiesta", sorted(c), sorted(ATTESO["uno"]))

    c, sp, ol, _ = accoppia(
        chiesta, nuova, 1000,
        chiave_a=misura_chiesta_al_produttore,
        chiave_b=lambda t: ((int(RE_CHIESTI.search(t)[1]),
                             int(RE_CHIESTI.search(t)[2]))
                            if RE_CHIESTI.search(t) else None))
    verifica("② chiesta → nuova (per chiave)", sorted(c), sorted(ATTESO["due"]))
    verifica("② richieste rimaste SENZA risposta", sp, ATTESO["due_spaiate"])

    c, sp, ol, _ = accoppia(nuova, spedita, 1000)
    verifica("③ nuova → spedita", sorted(c), sorted(ATTESO["tre"]))

    c, sp, ol, coppie = accoppia(girata, spedita, 1000)
    fam = {}
    for (ta, tb, testo) in coppie:
        m = RE_ESITO.search(testo)
        fam.setdefault(nome_esito(int(m[1]), int(m[2])), []).append(tb - ta)
    verifica("④ giro intero · ADATTATA",
             sorted(fam.get("ADATTATA", [])), ATTESO["adattata"])
    verifica("④ giro intero · NON_ORA",
             sorted(fam.get("NON_ORA", [])), ATTESO["non_ora"])

    # ⭐⭐ E IL CONTROLLO CHE CONTA DAVVERO: lo strumento vecchio, sullo stesso
    #     registro, sbagliava.  Se non sbaglia piu', il registro finto non
    #     contiene il veleno e questo controllo non prova niente.
    print()
    print("    ⭐ E il veleno c'e' davvero?  Lo strumento VECCHIO, sullo stesso")
    print("      registro finto, deve ROMPERSI o SBAGLIARE — se non lo fa, il")
    print("      controllo positivo non sta controllando niente:")
    try:
        vecchio = [((lambda t: (int(t.split(":")[0]) * 3600
                                + int(t.split(":")[1]) * 60
                                + float(t.split(":")[2])) * 1000)(l.split()[0]), l)
                   for l in FINTO.splitlines() if GIRATA in l]
        sped = [((lambda t: (int(t.split(":")[0]) * 3600
                             + int(t.split(":")[1]) * 60
                             + float(t.split(":")[2])) * 1000)(l.split()[0]), l)
                for l in FINTO.splitlines() if SPEDITA in l]
        fuori, j = [], 0
        for t, _ in vecchio:
            while j < len(sped) and sped[j][0] < t:
                j += 1
            if j < len(sped):
                fuori.append(sped[j][0] - t)
        print(f"       il vecchio ④ (senza consumo unico): {fuori} "
              f"⛔ — c'e' lo 0 che non e' mai esistito"
              if 0 in fuori else
              f"       ⛔ il vecchio ④ NON ha sbagliato: {fuori}")
        if 0 not in fuori:
            guai.append("il registro finto non contiene il veleno del doppio consumo")
    except ValueError as e:
        print(f"       ⭐ il vecchio e' MORTO come il 17 agosto: ValueError — {e}")

    try:
        [((lambda t: t.split(":"))(l.split()[0]))
         for l in FINTO.splitlines() if CHIESTA in l]
        vecchio_chiesta = [l.split()[0].split(":") for l in FINTO.splitlines()
                           if CHIESTA in l]
        rotte = [p for p in vecchio_chiesta if len(p) != 3]
        if rotte:
            print(f"       ⭐ e sul «tela CHIESTA» il vecchio trova {len(rotte)} "
                  f"riga/e che NON si spacchettano in h:m:s ⇒ ValueError: "
                  f"e' il difetto del 17 agosto, riprodotto")
        else:
            print("       ⛔ nessuna riga orfana nel finto: il ValueError non "
                  "si riproduce e questo controllo non prova niente")
            guai.append("il registro finto non contiene la riga orfana")
    except Exception as e:  # noqa: BLE001
        print(f"       {e}")

    print()
    if guai:
        print(f"⛔ CONTROLLO POSITIVO FALLITO su {len(guai)}: {guai}")
        return 1
    print("⭐ CONTROLLO POSITIVO SUPERATO: lo strumento vede quel che c'e' "
          "di sicuro,\n   e vede il veleno che rompeva quello vecchio.")
    return 0


def main():
    p = argparse.ArgumentParser(description="06-b35 — le latenze, dal registro")
    p.add_argument("registro", nargs="?", help="il giro.log da leggere")
    p.add_argument("--tetto", type=int, default=1000,
                   help="ms oltre i quali una coppia non e' una coppia (1000)")
    p.add_argument("--dettaglio", action="store_true",
                   help="stampa ogni campione, per il ricalcolo a mano")
    p.add_argument("--controllo", action="store_true",
                   help="⭐ il controllo positivo dello STRUMENTO")
    a = p.parse_args()

    if a.controllo:
        return controllo()
    if not a.registro:
        p.error("serve un registro, oppure --controllo")

    # ⛔ Lo zero si distingue dal fallimento (`LEZIONI.md` §1.9): un registro
    #    che non c'e' o vuoto NON e' «zero latenze».
    if not os.path.exists(a.registro):
        print(f"⛔ il registro «{a.registro}» NON ESISTE — e non e' uno zero")
        return 3
    if os.path.getsize(a.registro) == 0:
        print(f"⛔ il registro «{a.registro}» e' VUOTO (0 byte) — e non e' uno "
              f"zero.\n   ⚠ Il caso tipico: `terreno.sh accendi` azzera il "
              f"registro e la MARCA\n     resta quella di prima ⇒ "
              f"`tail -c +marca` non prende niente.")
        return 3
    with open(a.registro, errors="replace") as f:
        giro = Registro().leggi(f)
    conta(giro, a.tetto, a.dettaglio)
    return 0


if __name__ == "__main__":
    sys.exit(main())
