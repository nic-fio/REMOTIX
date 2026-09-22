#!/usr/bin/env python3
"""14-rapporto.py — ⭐⭐ LA TABELLA DELLA NOTTE, quella che legge Nic la mattina.

  python3 14-rapporto.py                    gli esiti che trova (tablet o server)
  python3 14-rapporto.py <percorso.jsonl>   un file preciso
  python3 14-rapporto.py --stretto          senza la parte dei numeri

⛔⛔ E LA REGOLA DI QUESTO FILE: **non giudica**.  Il verdetto lo ha dato lo
    scenario, qui si mette in fila e si mostra la prova accanto.  ⚠ Un rapporto
    che ricalcola i verdetti e' un secondo giudice, e due giudici che non vanno
    d accordo su una misura sono peggio di nessuno.

⭐ TRE COSE, IN QUEST ORDINE — perche' la mattina si guarda dall alto:
   1. la tabella: chi regge e chi no, tutto in uno schermo;
   2. i numeri, riga per riga, per chi vuole vedere DOVE;
   3. i guasti trovati, dal piu' grave, ognuno con la riga di registro che lo
      dimostra.  ⛔ Un guasto senza la sua riga e' un opinione.
"""
import datetime
import json
import os
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
QUI_STATO = os.path.expanduser("~/.local/state/remotix/stress/esiti.jsonl")
SUL_SERVER = "/media/REMOTIX/tmp/stress/esiti.jsonl"

VERDE = "\033[1;32m"
ROSSO = "\033[1;31m"
GIALLO = "\033[1;33m"
BLU = "\033[1;34m"
FINE = "\033[0m"

FACCIA = {0: VERDE + "regge" + FINE,
          1: ROSSO + "NO   " + FINE,
          3: "?    "}
FACCIA_SENZA = {0: "regge", 1: "NO   ", 3: "?    "}


def trova_il_file(argomento):
    """⛔ Il file si CERCA in ordine, e si dice DOVE lo si e' trovato: un
       rapporto su un file vecchio che nessuno sa quale sia e' peggio di niente.
    """
    if argomento:
        return argomento if os.path.exists(argomento) else None
    for p in (QUI_STATO, SUL_SERVER):
        if os.path.exists(p) and os.path.getsize(p) > 0:
            return p
    # ⚠ Ultimo tentativo: la copia sul server, tirata giu' adesso.  Se il server
    #   non risponde non si inventa niente, si dice che non c e'.
    cred = os.path.expanduser("~/SERVER.ssh")
    host = None
    if os.path.exists(cred):
        for riga in open(cred, encoding="utf-8", errors="replace"):
            if riga.startswith("host:"):
                host = riga.split(":", 1)[1].strip()
    if not host:
        return None
    giu = "/tmp/remotix-esiti-dal-server.jsonl"
    r = subprocess.run(["scp", "-q", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        "nicfio@%s:%s" % (host, SUL_SERVER), giu],
                       capture_output=True, text=True)
    return giu if r.returncode == 0 and os.path.exists(giu) else None


def leggi(percorso):
    righe = []
    for n, riga in enumerate(open(percorso, encoding="utf-8", errors="replace"), 1):
        riga = riga.strip()
        if not riga:
            continue
        try:
            righe.append(json.loads(riga))
        except Exception as e:
            print("⚠ riga %d illeggibile e saltata: %s" % (n, e))
    return righe


def chiave(r):
    return (r.get("scenario", "?"), r.get("desktop", "?"),
            r.get("marca", r.get("browser", "?")))


def ultimo_per_giro(righe):
    """⭐ Se un giro e' stato rifatto, vale l ULTIMO: la notte e' ripartibile, e
       una tabella che mostra il vecchio verdetto dopo che si e' rifatto sarebbe
       una bugia."""
    per = {}
    for r in righe:
        per[chiave(r)] = r
    return per


def numero(r, *nomi):
    for n in nomi:
        if r.get(n) is not None:
            return r[n]
    return None


def testo(v):
    return "?" if v is None else str(v)


def crescita(r):
    """Quanto e' cresciuto il server durante il giro — memoria e descrittori.

    ⛔ Si legge dalle due righe di `11-accendi.sh bilancio`; se manca una delle
       due, «non lo so» — non zero.
    """
    prima, dopo = r.get("server_prima"), r.get("server_dopo")
    if not prima or not dopo or "server_pid=" not in str(prima):
        return None
    def valore(riga, campo):
        for pezzo in str(riga).split():
            if pezzo.startswith(campo + "="):
                v = pezzo.split("=", 1)[1]
                return int(v) if v.isdigit() else None
        return None
    fuori = []
    if valore(prima, "server_pid") != valore(dopo, "server_pid"):
        return "il server e' cambiato nel mezzo"
    for campo, nome in (("server_rss_kb", "memoria"), ("server_fd", "descrittori"),
                        ("server_figli", "figli")):
        a, b = valore(prima, campo), valore(dopo, campo)
        if a is None or b is None or b <= a:
            continue
        if campo == "server_rss_kb":
            fuori.append("%s +%.1f MB" % (nome, (b - a) / 1024.0))
        else:
            fuori.append("%s %d→%d" % (nome, a, b))
    return ", ".join(fuori) if fuori else "niente"


def tabella(per, scenari, colonne, colore=True):
    faccia = FACCIA if colore else FACCIA_SENZA
    largo = max([len(s) for s in scenari] + [10])
    # ⚠ Due spazi fra il nome e la prima colonna: senza, uno scenario dal nome
    #   lungo si incolla al suo verdetto e la riga diventa illeggibile.
    testa1 = " " * (largo + 4)
    testa2 = " " * (largo + 4)
    for d, m in colonne:
        testa1 += "%-14s" % (d if m == colonne[0][1] else "")
        testa2 += "%-14s" % m
    print(testa1.rstrip())
    print(testa2.rstrip())
    for s in scenari:
        riga = "  %-*s  " % (largo, s)
        for d, m in colonne:
            r = per.get((s, d, m))
            if r is None:
                riga += "%-14s" % "–"
            else:
                segno = faccia.get(r.get("esito"), "?    ")
                # ⚠ La larghezza si conta SENZA i codici di colore, o la
                #   tabella si sfasa di dieci caratteri per cella.
                riga += segno + " " * (14 - len(faccia_nuda(r.get("esito"))))
        print(riga.rstrip())


def faccia_nuda(esito):
    return FACCIA_SENZA.get(esito, "?    ")


def main():
    argomenti = [a for a in sys.argv[1:] if not a.startswith("--")]
    stretto = "--stretto" in sys.argv
    colore = sys.stdout.isatty() and "--senza-colore" not in sys.argv

    percorso = trova_il_file(argomenti[0] if argomenti else None)
    if not percorso:
        print("⛔ non trovo nessun file di esiti.")
        print("   ⇒ li scrive la notte in ~/.local/state/remotix/stress/esiti.jsonl")
        print("     e li copia sul server in %s" % SUL_SERVER)
        return 2

    righe = leggi(percorso)
    if not righe:
        print("⛔ %s non ha nemmeno un giro dentro." % percorso)
        return 2

    per = ultimo_per_giro(righe)
    scenari = sorted({k[0] for k in per})
    desktop = [d for d in ("gnome", "kde", "xfce", "lxqt")
               if any(k[1] == d for k in per)]
    marche = [m for m in ("firefox", "chrome")
              if any(k[2] == m for k in per)]
    colonne = [(d, m) for d in desktop for m in marche]

    quando = max(r.get("quando_finito", 0) for r in righe) or None
    secondi = sum(int(r.get("secondi") or 0) for r in per.values())
    conta = {0: 0, 1: 0, 3: 0}
    for r in per.values():
        conta[r.get("esito", 3)] = conta.get(r.get("esito", 3), 0) + 1

    print()
    print((BLU if colore else "") + "══ LA NOTTE DI REMOTIX ══" + (FINE if colore else ""))
    if quando:
        print("   ultimo giro finito: %s"
              % datetime.datetime.fromtimestamp(quando).strftime("%d/%m/%Y alle %H:%M"))
    print("   %d giri, %d ore e %d minuti di misura"
          % (len(per), secondi // 3600, (secondi % 3600) // 60))
    print("   %d reggono · %d NON reggono · %d non ho potuto guardare"
          % (conta.get(0, 0), conta.get(1, 0), conta.get(3, 0)))
    print("   dal file: %s" % percorso)

    print()
    print("── 1. CHI REGGE E CHI NO ──")
    tabella(per, scenari, colonne, colore)
    print()
    print("   «–» vuol dire che quel giro non e' mai stato fatto;")
    print("   «?» che il giro e' partito ma non ha potuto giudicare (e non e' un rosso).")

    if not stretto:
        print()
        print("── 2. I NUMERI, GIRO PER GIRO ──")
        print("   %-14s %-6s %-8s %10s %7s %7s %7s  %s"
              % ("scenario", "dove", "browser", "viste→vetro", "buchi", "chiavi",
                 "cadute", "il server e' cresciuto"))
        for s in scenari:
            for d, m in colonne:
                r = per.get((s, d, m))
                if r is None:
                    continue
                cons = numero(r, "consegnati", "video_consegnati")
                dip = numero(r, "dipinti", "video_dipinti")
                viste = "%s→%s" % (testo(cons), testo(dip))
                print("   %-14s %-6s %-8s %10s %7s %7s %7s  %s"
                      % (s, d, m, viste,
                         testo(numero(r, "buchi")),
                         testo(numero(r, "chiavi_chieste")),
                         testo(numero(r, "linee_morte")),
                         testo(crescita(r))))

    # ⭐⭐ I GUASTI, DAL PIU' GRAVE — con la riga che li dimostra accanto.
    guasti = []
    for (s, d, m), r in per.items():
        for g in (r.get("guasti") or []):
            if not isinstance(g, dict):
                g = {"che_cosa": str(g)}
            guasti.append((int(g.get("gravita", 2)), s, d, m, g))
        # ⛔ Un «NON regge» senza guasti dichiarati resta un guasto: il verdetto
        #    lo ha dato lo scenario, e sparirebbe da questo elenco proprio nel
        #    caso peggiore.
        if r.get("esito") == 1 and not (r.get("guasti") or []):
            guasti.append((1, s, d, m,
                           {"che_cosa": r.get("perche") or "lo scenario ha detto NON REGGE",
                            "riga": r.get("registro", "")}))
    print()
    print("── 3. I GUASTI TROVATI ──")
    if not guasti:
        print("   ⭐ nessuno: nessuno scenario ha dato rosso, e nessuno ha")
        print("     dichiarato un guasto a parte.")
    else:
        print("   (gravita 1 = grave · 2 = serio · 3 = da guardare)")
        for gravita, s, d, m, g in sorted(guasti, key=lambda x: (x[0], x[1], x[2])):
            capo = "   %s[%d]%s %s · %s · %s — %s" % (
                (ROSSO if colore and gravita == 1 else GIALLO if colore else ""),
                gravita, (FINE if colore else ""), s, d, m,
                g.get("che_cosa", "senza nome"))
            print(capo)
            riga = (g.get("riga") or "").strip()
            if riga:
                print("        la prova: %s" % riga[:200])
            else:
                print("        ⚠ senza una riga di registro accanto: da verificare a mano")

    # ⚠ E si dice quando la riga l ha scritta la regia invece dello scenario: e'
    #   il segno che il giro e' morto per strada, non che sia andato bene.
    morti = [k for k, r in per.items() if r.get("scritta_dalla_regia")]
    if morti:
        print()
        print("── ⚠ GIRI MORTI PER STRADA (la riga l ha scritta la regia) ──")
        for s, d, m in sorted(morti):
            r = per[(s, d, m)]
            print("   %s · %s · %s — %s" % (s, d, m, r.get("perche", "non lo so")))

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
