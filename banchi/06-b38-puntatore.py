#!/usr/bin/env python3
"""06-b38-puntatore.py — ⭐ IL DENOMINATORE del secondo di grazia, letto dal filo.

    python3 06-b38-puntatore.py traccia.rcpreg

---------------------------------------------------------------------------
⛔ CHE COSA E', E SOPRATTUTTO CHE COSA **NON** E'

⛔ **Non e' un secondo giudice del protocollo.**  Il verdetto su `RCP.md` §7.1
   e' di `01-b4-validatore.py`, e resta suo: qui non si dice mai «conforme» ne'
   «non conforme».  Questo file risponde a tre domande che l'arbitro **non
   fa**, ed e' la stessa distinzione che `06-b38-tela.sh` chiama *«il
   denominatore»*:

     1. **la scena e' avvenuta?**  Un `PUNTATORE` c'e' stato, sulla tela
        vecchia, dopo un `TELA(ADATTATA)`?  ⚠ Senza questo numero «conforme»
        vuol dire «non ho guardato» — e' il difetto delle cinque tracce del 16
        agosto 2026, dove la tela non veniva esercitata affatto e il banco
        stampava verde;
     2. **a che distanza dal confine?**  Il `dt` letto *come lo legge
        l'arbitro*, cioe' fra due `istante_ms` di §11.1 — cosi' un ritardo
        scelto male si vede prima di produrre un verdetto;
     3. ⭐⛔ **DOVE E' FINITO IL PUNTATORE**, e questa e' quella che conta.

---------------------------------------------------------------------------
⭐⛔ LA TERZA DOMANDA, E PERCHE' L'ARBITRO NON PUO' RISPONDERE

*«Un server che rifiutasse la coordinata **dicendolo nel registro** ma la
applicasse lo stesso passerebbe l'arbitro.»*  E' vero, e non e' teorico: §7.1
parla di byte sul filo, e i byte non sanno niente del compositore.

⛔ Ma **il filo lo dice lo stesso**, e in un campo che nessuno guardava: §6.2
   mette in ogni intestazione di fotogramma il campo `input` — *«l'identificatore
   dell'ultimo input **iniettato** prima della cattura; 0 se nessuno»*.  ⇒

   · se dopo un `PUNTATORE id=N` **rifiutato** un fotogramma dichiarasse
     `input = N`, il server avrebbe rifiutato a parole e iniettato nei fatti;
   · se dopo un `PUNTATORE id=N` **graziato** nessun fotogramma arrivasse mai a
     `input = N`, la grazia sarebbe stata scritta nel registro e non fatta.

⚠ E il campo dice **che** e' stato iniettato, non **dove**: il punto d'arrivo
  sta nel registro del server (`06-b38-tela.sh`, passo 7), e i due testimoni
  vanno letti insieme.  ⛔ Nessuno dei due da solo chiude la domanda, e dire il
  contrario sarebbe la forma E7 — verificare dal lato che manda.

---------------------------------------------------------------------------
⛔ IL FORMATO SI IMPORTA, NON SI RISCRIVE

`RCP.md` §11.1: *«due registratori che scrivessero lo stesso fatto in due modi
sarebbero il difetto muto»* — e un **lettore** in piu' e' esattamente lo stesso
rischio dal capo opposto.  ⇒ La magia e la forma del blocco si prendono da
`01-b4-registrazioni.py`, che e' il posto in cui il formato e' gia' scritto.
⚠ Il giorno in cui la magia passera' a `0x04`, questo file segue **da solo**.

Uscita: `0` letto, `2` la registrazione e' rotta o di un formato che non
conosco (⛔ e non e' «niente da dire»: e' un guasto, e i due si distinguono —
`LEZIONI.md` §1.9), `3` non si legge il file.
"""
import importlib.util
import os
import struct
import sys

CONTROLLO, INPUT, APPUNTI, VIDEO, AUDIO = 0x00, 0x01, 0x02, 0x03, 0x04
CLIENT, SERVER = 1, 2
T_SESSIONE = 0x0007
T_TELA = 0x000E
T_CONGEDO = 0x000C
T_PUNTATORE = 0x0101
GRAZIA_MS = 1000                 # §7.1
MOTIVI = {0x0B: "ERRORE_PROTOCOLLO", 0x0D: "TEMPO_SCADUTO",
          0x0E: "SESSIONE_NON_SERVIBILE", 0x0F: "GIA_ATTIVA_REMOTA"}


def formato():
    """Magia e forma del blocco, dal file che li definisce gia'."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "01-b4-registrazioni.py")
    spec = importlib.util.spec_from_file_location("b4reg_b38", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.MAGIA, m.BLOCCO, m.BLOCCO_BYTE


class Rotta(Exception):
    pass


def blocchi(d, magia, blocco, blocco_byte):
    if len(d) < 16 or d[:8] != magia:
        raise Rotta(f"la magia non e' {magia!r}: e' {d[:8]!r}")
    (quanti,) = struct.unpack("!I", d[8:12])
    p = 16
    for nb in range(quanti):
        if p + blocco_byte > len(d):
            raise Rotta(f"blocco {nb}: l'intestazione non ci sta")
        verso, canale, fine, istante, stream, lung, nosc = struct.unpack(
            blocco, d[p:p + blocco_byte])
        p += blocco_byte
        p += nosc * 40
        if p + lung > len(d):
            raise Rotta(f"blocco {nb}: il carico e' troncato")
        yield nb, verso, canale, fine, istante, stream, d[p:p + lung]
        p += lung


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[0])
        return 3
    try:
        with open(sys.argv[1], "rb") as f:
            d = f.read()
    except OSError as e:
        print(f"⛔ non si legge «{sys.argv[1]}»: {e}")
        return 3
    magia, blocco, blocco_byte = formato()
    if len(d) < 16 or d[:8] != magia:
        print(f"⛔ REGISTRAZIONE ROTTA (o di un altro formato): magia "
              f"{d[:8]!r}, attesa {magia!r}")
        return 2
    orologio = d[12]

    tela = None                  # la tela in vigore
    tela_prec = None
    adattata_ms = None           # l'istante dell'ultimo TELA(ADATTATA)
    adattata_nb = None
    # ⛔⛔ IL PUNTATORE SI GIUDICA CONTRO LA TELA DI **QUEL MOMENTO**, e questo
    #     file l'ha sbagliato al primo giro — 22 agosto 2026.
    #
    #     La prima stesura teneva un `adattata_ms` solo e lo leggeva **alla
    #     fine**: con una registrazione in cui dopo il `PUNTATORE` passa un
    #     ALTRO `TELA(ADATTATA)` — che e' precisamente la forma dei casi
    #     `49-grazia-scaduta` e `50-grazia-dentro-il-secondo`, dove il secondo
    #     adattamento serve a provare che il server continua a servire — il
    #     `dt` usciva **−150 ms** e le due tele erano quelle sbagliate.
    #
    # ⛔ Il difetto e' della specie peggiore: `dt` negativo finisce sotto il
    #    secondo, cioe' nel ramo «non giudicabile» ⇒ un `PUNTATORE` **oltre la
    #    grazia** sarebbe stato dichiarato dentro.  Il denominatore avrebbe
    #    assolto la scena che esiste per accusare.
    #
    # ⭐ E a trovarlo e' stato il controllo positivo, non una rilettura: le due
    #    registrazioni costruite hanno l'atteso scritto nel manifesto, e i
    #    numeri non tornavano.  `PIANO.md` §0.3 punto 4.
    punt = []                    # [(nb, istante, id, x, y, tela, tela_prec, ms)]
    congedo = None               # (nb, istante, motivo)
    parole_server = 0            # blocchi di controllo dal server DOPO il puntatore
    fot = []                     # [(istante, numero, input, larghezza, altezza)]
    visti_video = set()

    try:
        for nb, verso, canale, fine, istante, stream, carico in blocchi(
                d, magia, blocco, blocco_byte):
            if canale == VIDEO:
                # ⛔ L'intestazione di §6.2 sta nei PRIMI 28 byte dello stream,
                #    e una sola volta: uno stream, un fotogramma.  ⚠ Un blocco
                #    successivo dello stesso stream porta dati, non
                #    un'intestazione — leggerlo come tale conterebbe fotogrammi
                #    che non esistono.
                if stream in visti_video or len(carico) < 28:
                    continue
                visti_video.add(stream)
                tipo_f, codec, lf, af, num, ist_us, inp = struct.unpack(
                    "!HHIIIQI", carico[:28])
                fot.append((istante, num, inp, lf, af))
                continue
            if canale == INPUT and verso == CLIENT:
                if len(carico) >= 26 and struct.unpack("!H", carico[:2])[0] \
                        == T_PUNTATORE:
                    pid = struct.unpack("!I", carico[6:10])[0]
                    x, y = struct.unpack("!II", carico[18:26])
                    punt.append((nb, istante, pid, x, y, tela, tela_prec,
                                 adattata_ms))
                continue
            if canale != CONTROLLO:
                continue
            i = 0
            while i + 6 <= len(carico):
                tipo, lung = struct.unpack("!HI", carico[i:i + 6])
                if i + 6 + lung > len(carico):
                    break
                corpo = carico[i + 6:i + 6 + lung]
                i += 6 + lung
                if punt and verso == SERVER and tipo != T_CONGEDO:
                    parole_server += 1
                # ⛔ LA PRIMA TELA VIENE DA `SESSIONE`, NON DA `TELA` — §4.5.
                #    Saltarla lascerebbe `tela_prec` a `None` al primo
                #    adattamento, e allora «valido sulla tela precedente»
                #    uscirebbe NO su una scena che invece c'e': il
                #    denominatore direbbe «non e' successo niente» proprio nel
                #    caso piu' comune, che e' un `ADATTA_TELA` all'attacco.
                if tipo == T_SESSIONE and verso == SERVER and lung >= 9:
                    tela = struct.unpack("!II", corpo[1:9])
                elif tipo == T_TELA and lung >= 10:
                    es = corpo[0]
                    lar, alt = struct.unpack("!II", corpo[2:10])
                    tela_prec = tela
                    tela = (lar, alt)
                    if es == 1:
                        adattata_ms, adattata_nb = istante, nb
                elif tipo == T_CONGEDO and verso == SERVER and congedo is None:
                    congedo = (nb, istante, corpo[0] if lung >= 1 else None)
    except Rotta as e:
        print(f"⛔ REGISTRAZIONE ROTTA: {e}")
        return 2

    oro = "client" if orologio == CLIENT else "server"
    print(f"== 06-b38-puntatore — «{sys.argv[1]}», tempi del {oro.upper()}")
    if adattata_ms is None:
        print("   ⛔ nessun TELA(ADATTATA) in questa traccia: la scena di §7.1 "
              "non puo' esserci stata")
        print("PUNT_SCENA no")
        return 0
    print(f"   l'ULTIMO TELA(ADATTATA) e' al blocco {adattata_nb}, istante "
          f"{adattata_ms} ms — tela {tela[0]}x{tela[1]}, precedente "
          + (f"{tela_prec[0]}x{tela_prec[1]}" if tela_prec else "(nessuna)")
          + "   ⚠ ma ogni PUNTATORE si giudica contro il TELA che precede LUI")
    if not punt:
        print("   ⛔ NESSUN PUNTATORE in questa traccia: la regola del secondo "
              "di grazia NON e' stata esercitata — «conforme» qui vuol dire "
              "«non ho guardato»")
        print("PUNT_SCENA no")
        return 0

    print(f"PUNT_SCENA si")
    for nb, ist, pid, x, y, tela, tela_prec, adattata_ms in punt:
        if adattata_ms is None:
            print(f"   blocco {nb}: PUNTATORE id={pid} ({x},{y}) — ⛔ e prima "
                  f"di lui non c'e' nessun TELA(ADATTATA): non e' la scena di "
                  f"§7.1")
            print("PUNT_DT nessuno")
            continue
        dt = ist - adattata_ms
        fuori = tela is not None and (x >= tela[0] or y >= tela[1])
        dentro_prima = (tela_prec is not None and x < tela_prec[0]
                        and y < tela_prec[1])
        sx = x if tela is None or x < tela[0] else tela[0] - 1
        sy = y if tela is None or y < tela[1] else tela[1] - 1
        print(f"   blocco {nb}: PUNTATORE id={pid} ({x},{y}) a {dt} ms dal "
              f"TELA(ADATTATA) che lo precede — tela in vigore "
              + (f"{tela[0]}x{tela[1]}" if tela else "(nessuna)")
              + ", precedente "
              + (f"{tela_prec[0]}x{tela_prec[1]}" if tela_prec else "(nessuna)"))
        print(f"      valido sulla tela precedente: "
              f"{'SI' if dentro_prima else 'NO'} · fuori da quella in vigore: "
              f"{'SI' if fuori else 'NO'}")
        if not (fuori and dentro_prima):
            print("      ⛔ ⇒ QUESTA NON E' LA SCENA DI §7.1: e' un'altra "
                  "regola (§7.3, «fuori dalla tela»), e un banco che le "
                  "confondesse misurerebbe la cosa sbagliata")
        # ⛔ Il margine si dichiara, e in millisecondi: la regola vive su un
        #    confine e il tempo qui e' quello del CLIENT — quello del server e'
        #    piu' LUNGO, mai piu' corto (§11.1).
        if dt > GRAZIA_MS:
            print(f"      margine OLTRE il secondo: +{dt - GRAZIA_MS} ms — e "
                  f"quello del server e' ancora piu' grande")
        else:
            print(f"      margine DENTRO il secondo: -{GRAZIA_MS - dt} ms — "
                  f"⚠ ci vorrebbe un giro di rete di {GRAZIA_MS - dt} ms per "
                  f"portarlo oltre dal lato del server")
        print(f"PUNT_ID {pid}")
        print(f"PUNT_DT {dt}")
        print(f"PUNT_XY {x},{y}")
        print(f"PUNT_SATURAZIONE_ATTESA {sx},{sy}")

    if congedo is not None:
        nb_c, ist_c, mot = congedo
        print(f"   CONGEDO dal server al blocco {nb_c}, istante {ist_c} ms, "
              f"motivo {mot:#04x} = {MOTIVI.get(mot, '?')}")
        print(f"CONGEDO_MOTIVO {mot:#04x}")
        print(f"CONGEDO_DT {ist_c - punt[0][1]}")
    else:
        print("   nessun CONGEDO dal server in questa traccia")
        print("CONGEDO_MOTIVO nessuno")
    print(f"CONTROLLO_DAL_SERVER_DOPO {parole_server}")

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⛔ IL CAMPO `input` DI §6.2 — il testimone che sta sul FILO
    # ═══════════════════════════════════════════════════════════════════════
    ids = {p[2] for p in punt}
    dopo = [f for f in fot if f[0] >= punt[0][1]]
    visti = sorted({f[2] for f in dopo})
    print(f"   fotogrammi nella traccia: {len(fot)} · dopo il PUNTATORE: "
          f"{len(dopo)} · campo `input` visto in quelli dopo: "
          + (", ".join(str(v) for v in visti) if visti else "(nessuno)"))
    riconosciuti = sorted(ids & set(visti))
    if riconosciuti:
        print(f"   ⭐ §6.2: il server dichiara INIETTATO l'input "
              f"{', '.join(str(v) for v in riconosciuti)} — e lo dice sul "
              f"filo, non nel suo registro")
    elif dopo:
        print(f"   ⚠ nessun fotogramma dichiara l'input "
              f"{', '.join(str(v) for v in sorted(ids))}: o non e' stato "
              f"iniettato, o non e' passato nessun fotogramma dopo "
              f"l'iniezione")
    else:
        print("   ⚠ nessun fotogramma DOPO il PUNTATORE: il campo `input` non "
              "puo' dire niente, e si dichiara invece di tacere")
    print("FOT_DOPO %d" % len(dopo))
    print("FOT_INPUT %s" % (",".join(str(v) for v in visti) if visti
                            else "nessuno"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
