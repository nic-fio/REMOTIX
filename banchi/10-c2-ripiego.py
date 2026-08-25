#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-c2-ripiego — ⛔⛔⛔ IL RIPIEGO SULLA MEMORIA: il figlio non deve morire, **e
                 deve CONSEGNARE** (incarico 10-c2, fase 10).

    porta 8220 · utenti `provadec1` (1100) e `provadec1b` (1123)
    albero /media/REMOTIX/src/10c2-src · lavoro /media/REMOTIX/tmp/10c2
    unita' remotix-8220 · lucchetto GPU `10-c2`

═══════════════════════════════════════════════════════════════════════════
CHE COSA MISURA, E PERCHE' NON BASTAVA IL BANCO CHE C'ERA
═══════════════════════════════════════════════════════════════════════════

`banchi/10-b2-browser.py --scena finestra` (certificato 59/59) ha TROVATO il
difetto P1 e lo rimisura: `[M]` 3 morti su 3 a larghezza 1268, 0 su 3 a 1280.
⭐ Quello resta il banco del ROSSO e del VERDE, e questo file **non lo
rifa'**: lo chiama chi lancia la campagna.

⛔ Ma «il figlio non e' morto» NON e' «il desktop funziona» (`LEZIONI.md`
   §1.30).  Il banco del browser conta le MORTI; qui si conta **quanto e'
   arrivato**:

  | grandezza | dove si legge | perche' li' |
  |---|---|---|
  | il figlio e' morto, e di che segnale | registro del server, riga «RACCOLTO: l'ha ucciso il segnale N» | ⛔ e' l'unico posto in cui il **segnale** e' scritto |
  | **fotogrammi consegnati** | dal CLIENTE, contati sul filo (`--video-scrivi`) | il registro del server dice quel che LUI ha spedito |
  | **byte per fotogramma** | i byte del file scritto dal cliente / i fotogrammi | ⛔ un flusso di 0 byte «consegna» lo stesso, e non si vede niente |
  | la strada dei pixel in vigore | registro del server | e' il fatto che spiega tutti gli altri numeri |
  | la guardia della copia zero ha morso? | registro del server | ⛔ se non ha morso, **la prova non ha morso**: la scena non e' quella dichiarata |

⛔⛔ E LA TERZA TELA — **854×480**, il minimo dichiarato da `SPECIFICHE.md`
     §5.5 (passo 3416, che non e' multiplo di 64).  `fasi/10-…md` §6.2 l'aveva
     trovata rifiutata dalla guardia della copia zero e nessuno era andato
     oltre: se anche lei adesso consegna, la stessa cura chiude **due**
     difetti.

⚠ IL CLIENTE E' QUELLO DI PROVA, non un browser, ed e' **dichiarato**: quel
  che si misura qui e' la **tela concessa**, e la tela la impone `ADATTA_TELA`
  esattamente come la impone la pagina.  ⛔ Il verdetto «l'utente vede» resta
  del banco del browser.

Uso:
    python3 banchi/10-c2-ripiego.py --certifica
    python3 banchi/10-c2-ripiego.py --giri 3
    python3 banchi/10-c2-ripiego.py --giri 3 --tele 1268x714,1280x714,854x480
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⭐ NON SI RISCRIVE IL BANCO DEL BROWSER: se ne prendono gli attrezzi gia'
#    certificati (`root`, `righe_registro`, `registro_da`, `sgombra_palco`,
#    `segnale_del_figlio`).  ⛔ Cosi' se un giorno cambia il modo di leggere il
#    registro, cambia in un posto solo.
_spec = importlib.util.spec_from_file_location("b2", os.path.join(QUI, "10-b2-browser.py"))
B2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B2)

IND = B2.IND
PORTA = B2.PORTA
DENTRO_ALB = B2.DENTRO_ALB
DENTRO_LAV = B2.DENTRO_LAV
LAV = B2.LAV
UTENTE = B2.UTENTE_A[0]
FUORI = os.environ.get("FUORI", "/tmp/10-c2")

_log, _ok, _ko, _dub, _inf = B2._log, B2._ok, B2._ko, B2._dub, B2._inf


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐ I GIUDIZI — funzioni pure, cosi' i guasti si innestano senza rete
# ═══════════════════════════════════════════════════════════════════════════
VID = re.compile(r"\[vid\]\s+(\d+) fotogrammi \((\d+) chiavi\), (\d+)x(\d+)")
GUARDIA = re.compile(r"il passo del DMA-BUF e' (\d+) su una tela (\d+)x(\d+)")
STRADA = re.compile(r"il palco si monta sulla strada «(SCHEDA|MEMORIA)")
CAMBIO = re.compile(r"la STRADA DEI PIXEL e' cambiata in «(SCHEDA|MEMORIA)")


def fotogrammi_dal_cliente(uscita):
    """⭐ Quanti fotogrammi il CLIENTE ha preso dal filo, e quante chiavi.

    ⛔ `None` se la riga non c'e': «non l'ho letta» e «zero fotogrammi» sono
       due fatti diversi, e il secondo e' proprio il verdetto che si vorrebbe
       trarre.  ⚠ Il cliente scrive «⛔ nessun fotogramma preso dal filo» quando
       sono zero: **quello** e' uno zero misurato, e vale 0.
    """
    if uscita is None:
        return None
    m = VID.search(uscita)
    if m:
        return {"fotogrammi": int(m.group(1)), "chiavi": int(m.group(2)),
                "tela": "%sx%s" % (m.group(3), m.group(4))}
    if "nessun fotogramma preso dal filo" in uscita:
        return {"fotogrammi": 0, "chiavi": 0, "tela": None}
    return None


def byte_per_fotogramma(byte, quanti):
    """⛔ `None` quando non si puo' dividere — e NON zero."""
    if byte is None or quanti is None or quanti <= 0:
        return None
    return byte / float(quanti)


def guardia_ha_morso(testo, larghezza):
    """La guardia della copia zero ha rifiutato il passo di QUESTA tela?

    ⛔ `None` se il registro non l'ho letto.  ⚠ E si controlla che la riga
       parli della tela **giusta**: un rifiuto di un'altra misura direbbe «la
       prova ha morso» su una prova che non ha morso.
    """
    if testo is None:
        return None
    for m in GUARDIA.finditer(testo):
        if int(m.group(2)) == larghezza:
            return True
    return False


def strada_finale(testo):
    """La strada dei pixel in vigore alla fine, `None` se non l'ho letta."""
    if testo is None:
        return None
    ultima = None
    for riga in testo.split("\n"):
        m = STRADA.search(riga) or CAMBIO.search(riga)
        if m:
            ultima = m.group(1)
    return ultima


def rimontaggi_solo_flusso(testo):
    """Quante volte la strada e' cambiata SENZA smontare il palco (la cura).

    ⛔ `None` se il registro non c'e': zero rimontaggi e registro non letto
       sono due cose diverse.
    """
    if testo is None:
        return None
    return len(CAMBIO.findall(testo))


def giudizio(e):
    """⛔⭐ IL VERDETTO DI UN GIRO, e ha QUATTRO esiti, non due.

      `"non-misurato"` ⛔ non ho potuto leggere qualcosa: non giudico;
      `"morto"`        il figlio e' stato ucciso da un segnale;
      `"muto"`         ⛔ vivo e **non ha consegnato NIENTE**: e' il difetto
                       che «il figlio non e' morto» nasconderebbe;
      `"consegna"`     ⭐ vivo e i fotogrammi sono arrivati al cliente.
    """
    if e.get("segnale") is not None:
        return "morto"
    if e.get("registro_letto") is False or e.get("fotogrammi") is None:
        return "non-misurato"
    if e.get("guardia") is None:
        return "non-misurato"
    if e["fotogrammi"] <= 0:
        return "muto"
    if e.get("byte_per_fotogramma") is None:
        return "non-misurato"
    return "consegna"


# ═══════════════════════════════════════════════════════════════════════════
# LA CAMPAGNA
# ═══════════════════════════════════════════════════════════════════════════
def un_giro(largo, alto, resta, n):
    """Un giro solo: palco SGOMBRATO, cliente, e tutto quel che si e' letto.

    ⛔ Lo sgombero e' la CONDIZIONE della prova, non una pulizia: il ripiego
       vale alla NASCITA del palco, e un riattacco non ci passa.
    """
    if not B2.sgombra_palco():
        return {"tela": "%dx%d" % (largo, alto), "giro": n,
                "registro_letto": False, "segnale": None, "fotogrammi": None,
                "perche": "il palco precedente non e' morto: NON MISURO"}
    riga0 = B2.righe_registro()
    dentro = "%s/video-%d-%d.264" % (DENTRO_LAV, largo, n)
    fuori = "%s/video-%d-%d.264" % (LAV, largo, n)
    B2.root("rm -f %s" % fuori)
    rc, out, err = B2.root(
        "bash /media/REMOTIX/enter.sh --root "
        "'python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
        "--utente %s --parola-file %s/parola --audio-codec pcm "
        "--video-codec h264 --adatta %dx%d --resta %d --video-scrivi %s'"
        % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, largo, alto, resta, dentro),
        tetto=180)
    uscita = (out or "") + (err or "")
    testo = B2.registro_da(riga0)

    v = fotogrammi_dal_cliente(uscita)
    rc2, sz, _ = B2.root("stat -c %%s %s 2>/dev/null || echo -" % fuori)
    sz = (sz or "").strip()
    byte = int(sz) if sz.isdigit() else None
    seg = B2.segnale_del_figlio(testo)
    e = {"tela": "%dx%d" % (largo, alto), "giro": n, "passo": largo * 4,
         "multiplo64": (largo * 4) % 64 == 0,
         "registro_letto": testo is not None,
         "segnale": seg,
         "fotogrammi": v["fotogrammi"] if v else None,
         "chiavi": v["chiavi"] if v else None,
         "tela_del_flusso": v["tela"] if v else None,
         "byte": byte,
         "guardia": guardia_ha_morso(testo, largo),
         "strada": strada_finale(testo),
         "rimontaggi_solo_flusso": rimontaggi_solo_flusso(testo),
         "attaccato": "niente e' caduto" in uscita}
    e["byte_per_fotogramma"] = byte_per_fotogramma(byte, e["fotogrammi"])
    e["giudizio"] = giudizio(e)
    return e


def campagna(o):
    tele = []
    for t in o.tele.split(","):
        l, a = t.lower().split("x")
        tele.append((int(l), int(a)))

    _log("IL RIPIEGO SULLA MEMORIA — %d tele × %d giri, palco SGOMBRATO ogni volta"
         % (len(tele), o.giri))
    opz = B2.opzioni_del_server()
    if opz is None:
        _ko("⛔ non ho letto l'`argv` del server: NON MISURO (non so quali cure ha addosso)")
        return 2
    _inf("il server gira con: %s" % opz.strip())

    tutti = []
    for largo, alto in tele:
        for n in range(1, o.giri + 1):
            e = un_giro(largo, alto, o.resta, n)
            tutti.append(e)
            _inf("%s (passo %d, %s) · giro %d/%d · %s · segnale %s · "
                 "fotogrammi %s (%s chiavi) · byte/fot %s · strada %s · "
                 "guardia %s · rimontaggi-solo-flusso %s"
                 % (e["tela"], e["passo"],
                    "multiplo di 64" if e["multiplo64"] else "⛔ NON multiplo di 64",
                    n, o.giri, e["giudizio"],
                    e["segnale"] if e["segnale"] is not None else "nessuno",
                    e["fotogrammi"], e["chiavi"],
                    "?" if e["byte_per_fotogramma"] is None
                    else "%.0f" % e["byte_per_fotogramma"],
                    e["strada"], e["guardia"], e["rimontaggi_solo_flusso"]))

    _log("IL VERDETTO — per tela")
    riassunto = {}
    for largo, alto in tele:
        chiave = "%dx%d" % (largo, alto)
        g = [e for e in tutti if e["tela"] == chiave]
        morti = sum(1 for e in g if e["giudizio"] == "morto")
        muti = sum(1 for e in g if e["giudizio"] == "muto")
        ignoti = sum(1 for e in g if e["giudizio"] == "non-misurato")
        buoni = [e for e in g if e["giudizio"] == "consegna"]
        fot = sorted(e["fotogrammi"] for e in buoni) or None
        bpf = sorted(e["byte_per_fotogramma"] for e in buoni) or None
        morse = sum(1 for e in g if e["guardia"] is True)
        riassunto[chiave] = {
            "passo": largo * 4, "multiplo64": (largo * 4) % 64 == 0,
            "giri": len(g), "morti": morti, "muti": muti,
            "non_misurati": ignoti, "consegnano": len(buoni),
            "guardia_ha_morso": morse,
            "fotogrammi_mediana": fot[len(fot) // 2] if fot else None,
            "byte_per_fotogramma_mediana": bpf[len(bpf) // 2] if bpf else None,
            "strade": sorted({e["strada"] for e in g if e["strada"]}),
        }
        r = riassunto[chiave]
        testo = ("%s ⇒ passo %d (%s): CONSEGNANO %d/%d · morti %d · muti %d · "
                 "non misurati %d · la guardia ha morso %d volte · fotogrammi "
                 "(mediana) %s · byte/fotogramma (mediana) %s · strade %s"
                 % (chiave, r["passo"],
                    "multiplo di 64" if r["multiplo64"] else "⛔ NON multiplo di 64",
                    r["consegnano"], r["giri"], r["morti"], r["muti"],
                    r["non_misurati"], r["guardia_ha_morso"],
                    r["fotogrammi_mediana"],
                    "?" if r["byte_per_fotogramma_mediana"] is None
                    else "%.0f" % r["byte_per_fotogramma_mediana"],
                    r["strade"]))
        if r["non_misurati"]:
            _dub("⚠ " + testo)
        elif r["consegnano"] == r["giri"]:
            _ok(testo)
        else:
            _ko(testo)
        # ⛔ E SE LA GUARDIA NON HA MORSO, LA PROVA NON HA MORSO: si dice, o il
        #    verde varrebbe per una scena che non e' quella dichiarata.
        if not r["multiplo64"] and r["guardia_ha_morso"] < r["giri"]:
            _dub("⚠ %s: la guardia della copia zero ha morso solo %d volte su "
                 "%d — sui giri restanti la strada della memoria NON e' stata "
                 "percorsa, e quei giri non provano niente"
                 % (chiave, r["guardia_ha_morso"], r["giri"]))

    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "ripiego.json"), "w") as fh:
        json.dump({"giri": tutti, "riassunto": riassunto,
                   "server": opz.strip()}, fh, indent=1, ensure_ascii=False)
    _inf("scritto in %s/ripiego.json" % FUORI)
    return 0 if all(r["consegnano"] == r["giri"] for r in riassunto.values()) else 1


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA CERTIFICAZIONE — un banco che non si e' visto dare ROSSO non e' un
#      banco (`LEZIONI.md` §1.29).  Ogni predicato ha il suo guasto, e i guasti
#      si FANNO GIRARE.
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    buoni = malati = 0

    def caso(nome, vero, atteso):
        nonlocal buoni, malati
        if vero == atteso:
            _ok(nome)
            buoni += 1
        else:
            _ko("%s — atteso %r, avuto %r" % (nome, atteso, vero))
            malati += 1

    _log("A · `fotogrammi_dal_cliente` — e lo zero MISURATO non e' il buco")
    sano = "   [vid]  312 fotogrammi (2 chiavi), 1268x714, scritti in /x.264"
    caso("sano · la riga si legge", fotogrammi_dal_cliente(sano),
         {"fotogrammi": 312, "chiavi": 2, "tela": "1268x714"})
    caso("⭐ lo ZERO dichiarato dal cliente vale 0",
         fotogrammi_dal_cliente("   [vid]  ⛔ nessun fotogramma preso dal filo: niente file"),
         {"fotogrammi": 0, "chiavi": 0, "tela": None})
    caso("⛔ nessuna riga ⇒ None, non zero",
         fotogrammi_dal_cliente("   ⭐ ancora attaccato dopo 25.0 s"), None)
    caso("⛔ uscita non letta ⇒ None", fotogrammi_dal_cliente(None), None)

    _log("B · `byte_per_fotogramma` — ⛔ None non e' zero")
    caso("sano · 1 000 000 byte su 250 fotogrammi", byte_per_fotogramma(1000000, 250), 4000.0)
    caso("⛔ zero fotogrammi ⇒ None, non divisione per zero",
         byte_per_fotogramma(1000000, 0), None)
    caso("⛔ byte non letti ⇒ None", byte_per_fotogramma(None, 250), None)
    caso("⛔ fotogrammi non letti ⇒ None", byte_per_fotogramma(1000, None), None)

    _log("C · `guardia_ha_morso` — ⛔ e la tela dev'essere QUELLA")
    reg = ("06:44:53 figlio ⛔⛔ il passo del DMA-BUF e' 5072 su una tela "
           "1268x714, e NON e' multiplo di 64: ...\n")
    caso("sano · la guardia ha morso su 1268", guardia_ha_morso(reg, 1268), True)
    caso("⛔ una riga per UN'ALTRA tela non conta", guardia_ha_morso(reg, 854), False)
    caso("⛔ nessuna riga ⇒ False (letto, e non c'era)",
         guardia_ha_morso("niente di niente", 1268), False)
    caso("⛔ registro non letto ⇒ None, non False", guardia_ha_morso(None, 1268), None)

    _log("D · `strada_finale` — l'ULTIMA parola, non la prima")
    r2 = ("⭐ il palco si monta sulla strada «SCHEDA (DMA-BUF, copia zero)» ...\n"
          "⭐⭐ la STRADA DEI PIXEL e' cambiata in «MEMORIA (i pixel si copiano)» ...\n")
    caso("sano · nasce SCHEDA e finisce MEMORIA", strada_finale(r2), "MEMORIA")
    caso("⭐ senza cambio resta SCHEDA",
         strada_finale("⭐ il palco si monta sulla strada «SCHEDA (DMA-BUF, copia zero)»"),
         "SCHEDA")
    caso("⛔ nessuna riga ⇒ None", strada_finale("niente"), None)
    caso("⛔ registro non letto ⇒ None", strada_finale(None), None)
    caso("sano · i rimontaggi del solo flusso si contano",
         rimontaggi_solo_flusso(r2 + r2), 2)
    caso("⛔ registro non letto ⇒ None, non 0", rimontaggi_solo_flusso(None), None)
    caso("⭐ nessun rimontaggio ⇒ 0 MISURATO", rimontaggi_solo_flusso("niente"), 0)

    _log("E · `giudizio` — ⛔ QUATTRO esiti, e «non e' morto» non e' «funziona»")
    base = {"segnale": None, "registro_letto": True, "fotogrammi": 300,
            "guardia": True, "byte_per_fotogramma": 4000.0}
    caso("sano · vivo e consegna", giudizio(dict(base)), "consegna")
    caso("⛔ ucciso dal segnale 11 ⇒ morto",
         giudizio(dict(base, segnale=11)), "morto")
    caso("⛔⛔ vivo e ZERO fotogrammi ⇒ MUTO, non «consegna»",
         giudizio(dict(base, fotogrammi=0, byte_per_fotogramma=None)), "muto")
    caso("⛔ fotogrammi non letti ⇒ non-misurato",
         giudizio(dict(base, fotogrammi=None)), "non-misurato")
    caso("⛔ registro non letto ⇒ non-misurato",
         giudizio(dict(base, registro_letto=False)), "non-misurato")
    caso("⛔ non so se la guardia ha morso ⇒ non-misurato",
         giudizio(dict(base, guardia=None)), "non-misurato")
    caso("⛔ byte non divisibili ⇒ non-misurato",
         giudizio(dict(base, byte_per_fotogramma=None)), "non-misurato")
    caso("⭐ e il MORTO vince su tutto: anche se aveva consegnato",
         giudizio(dict(base, segnale=11, fotogrammi=300)), "morto")

    print()
    if malati:
        print("  \033[1;31m%d su %d\033[0m" % (buoni, buoni + malati))
    else:
        print("  \033[1m%d su %d\033[0m" % (buoni, buoni))
    return 0 if not malati else 1


def principale():
    a = argparse.ArgumentParser()
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--giri", type=int, default=3)
    a.add_argument("--resta", type=int, default=20,
                   help="quanti secondi il cliente resta attaccato")
    a.add_argument("--tele", default="1268x714,1280x714,854x480",
                   help="⭐ 1268 e' quella che Firefox apre di suo; 1280 e' il "
                        "controllo col passo buono; 854x480 e' il MINIMO "
                        "dichiarato da SPECIFICHE.md §5.5")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    return campagna(o)


if __name__ == "__main__":
    sys.exit(principale())
