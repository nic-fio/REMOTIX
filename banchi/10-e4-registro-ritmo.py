#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-e4-registro-ritmo — ⭐ QUANTO SCRIVE IL REGISTRO, **per numero di sessioni**.

⛔⛔ CHE COSA QUESTO ATTREZZO **NON** SA FARE — sta in testa apposta
    (`LEZIONI.md` §1.35: un metro si lascia agli altri **con scritto che cosa
    non sa dire**):

 1. ⛔ **NON classifica l'attribuzione.**  Il conto delle righe «col nome» che
    stampa e' un `regex` grezzo per area, e **non e' la misura di §6.7/§5.2**:
    quella la fa `banchi/10-b96-registro.py --analizza`, che e' certificato
    (31/31) e sa distinguere le famiglie **di diagnosi** da quelle che parlano
    prima che un inquilino esista.  ⚠ `[M]` 25 agosto 2026 i due danno numeri
    diversi **ed e' giusto**: qui 51,7 %, la' 100,0 % delle righe di diagnosi —
    perche' questo conta anche `wt`, che per disegno **non ha un nome da dire**.
    ⇒ **La percentuale che si riferisce e' quella di `10-b96`.**
 2. ⛔ **Non giudica niente**: non ha predicati, non da' rosso, non ha un
    verdetto.  E' un CONTATORE.  Il suo `--certifica` prova solo che il
    contatore **ritrova valori iniettati noti**, che e' tutto quel che un
    contatore puo' promettere (`LEZIONI.md` §1.33).
 3. ⛔ **Non sa a quale gradino sta la salita**: gliel'ho detto un campionatore
    che gli gira accanto (`10-e4-campiona.sh`), leggendo quanti `gnome-shell`
    dei MIEI uid sono vivi.  ⚠ Un ponte fra l'orologio monotono del banco e
    quello di parete del registro sarebbe una **terza** cosa da tarare (§6.4),
    e cosi' non serve.

⭐ A che serve, allora: a rispondere alla domanda 3 dell'incarico E4 — *«il
   registro costa quel che dichiara, a UNDICI sessioni?»*  `[M]` §5.2 l'aveva
   misurato a QUATTRO (+5,4 % di byte per riga, righe/s invariate), e a undici
   quel costo si moltiplica.  Qui esce **righe/s, byte/s e byte/riga per ogni
   numero di sessioni**, che e' la grandezza che si moltiplica.

uso:  10-e4-registro-ritmo.py <registro.log> <campioni.tsv> <hh:mm:ss> <hh:mm:ss>
      10-e4-registro-ritmo.py --certifica      ⛔ non tocca la macchina di prova
"""
import os, re, sys, collections, tempfile

RIGA = re.compile(r'^(\d\d):(\d\d):(\d\d)\.(\d\d\d) (\S+)\s+(.*)$', re.S)
NOME = re.compile(r'^\[(provamt\d+|[a-z0-9_.-]{1,32})\] ')

VERDE, ROSSO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[0m"


def sec(h, m, s):
    return h * 3600 + m * 60 + s


def leggi_campioni(perc):
    """secondo di parete → (clienti, palchi).  ⛔ `None` se il file non c'e':
       «non ho letto» non e' «zero sessioni» (`CODER.md` §3.10)."""
    if not os.path.exists(perc):
        return None
    q = {}
    with open(perc) as f:
        f.readline()
        for r in f:
            p = r.rstrip("\n").split("\t")
            if len(p) < 5:
                continue
            try:
                hh, mm, ss = [int(x) for x in p[1].split(":")]
                q[sec(hh, mm, ss)] = (int(p[3]), int(p[4]))
            except ValueError:
                continue
    return q or None


def conta(reg, quanti, t0, t1):
    """(per_n, per_area, con_nome, totali) — o `None` se non ho letto niente."""
    righe, byte = collections.Counter(), collections.Counter()
    per_area, con_nome, nomi = (collections.Counter(), collections.Counter(),
                                collections.Counter())
    with open(reg, "rb") as f:
        for cru in f:
            m = RIGA.match(cru.decode("utf-8", "replace"))
            if not m:
                continue
            t = sec(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if t < t0 or t > t1:
                continue
            righe[t] += 1
            byte[t] += len(cru)
            per_area[m.group(5)] += 1
            n = NOME.match(m.group(6))
            if n:
                con_nome[m.group(5)] += 1
                nomi[n.group(1)] += 1
    if not righe:
        return None
    per_n = collections.defaultdict(lambda: [0, 0, 0])
    for t in range(t0, t1 + 1):
        if quanti is None or t not in quanti:
            continue
        # ⭐ I PALCHI (un `gnome-shell` per utente): il conto dei processi del
        #    cliente vale TRE per sessione, e sarebbe un numero plausibile e
        #    sbagliato.
        n = quanti[t][1]
        per_n[n][0] += 1
        per_n[n][1] += righe.get(t, 0)
        per_n[n][2] += byte.get(t, 0)
    return per_n, per_area, con_nome, nomi, sum(righe.values()), sum(byte.values())


def stampa(r):
    per_n, per_area, con_nome, nomi, tot_r, tot_b = r
    print("  sessioni | secondi |   righe/s |    byte/s | byte/riga")
    print("  ---------+---------+-----------+-----------+----------")
    for n in sorted(per_n):
        s, rr, bb = per_n[n]
        if s == 0:
            continue
        print("  %8d | %7d | %9.1f | %9.0f | %9.1f"
              % (n, s, rr / s, bb / s, (bb / rr) if rr else float("nan")))
    print("\n  in tutto: %d righe, %d byte, %.1f byte/riga"
          % (tot_r, tot_b, (tot_b / tot_r) if tot_r else float("nan")))
    print("\n  -- righe per area, e quante portano una parentesi col nome --")
    print("  ⛔ NON e' la misura dell'attribuzione: quella la fa 10-b96 --analizza")
    for area, c in per_area.most_common(18):
        q = con_nome.get(area, 0)
        print("  %-13s | %8d | %8d | %6.1f %%" % (area, c, q, 100.0 * q / c))
    print("\n  nomi distinti visti: %d -- %s"
          % (len(nomi), " ".join("%s:%d" % (k, v) for k, v in sorted(nomi.items()))))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL METRO SI TARA PRIMA — `LEZIONI.md` §1.33: si inietta un valore NOTO e
#    si verifica che il metro lo ritrovi.  ⚠ Qui non c'e' niente da giudicare,
#    quindi non c'e' nessun rosso «del prodotto» da innestare: i guasti sono
#    tutti del CONTATORE, ed e' l'unica promessa che un contatore possa fare.
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    print("\n\033[1m== ⛔ TARATURA — valori NOTI iniettati, e il contatore li ritrova\033[0m")
    print("    --  ⚠ non tocca la macchina di prova: il registro e' FABBRICATO")
    esiti = []

    def caso(nome, atteso, visto, ok):
        esiti.append(ok)
        print("    %s%s%s  %-52s atteso %-22s visto %s"
              % (VERDE if ok else ROSSO, "OK" if ok else "NO", GRIGIO,
                 nome, atteso, visto))

    d = tempfile.mkdtemp(prefix="10-e4-tara-")
    reg, camp = os.path.join(d, "r.log"), os.path.join(d, "c.tsv")
    # ⭐ 10 secondi: al secondo `s` scrivo esattamente `s+1` righe, e la meta'
    #    porta il nome.  ⇒ 55 righe in tutto, e il conto e' verificabile a mano.
    with open(reg, "w") as f:
        for s in range(10):
            for k in range(s + 1):
                nome = "[provamt%d] " % (k + 1) if k % 2 == 0 else ""
                f.write("12:00:%02d.000 figlio  %sriga di prova\n" % (s, nome))
        # ⛔ E una riga FUORI dalla finestra: se la contasse, il filtro del
        #    tempo non morderebbe, e ogni numero sarebbe di un'altra fetta.
        # ⚠ E il nome dev'essere uno che DENTRO la finestra non c'e': la prima
        #   stesura usava `provamt9`, che al secondo 8 ci sta per conto suo, e
        #   il caso 3 dava rosso su un contatore giusto.  ⛔ Un guasto innestato
        #   con un valore che il sano produce gia' non prova niente.
        f.write("13:00:00.000 figlio  [provamt42] riga FUORI dalla finestra\n")
    with open(camp, "w") as f:
        f.write("epoch\tore\tbyte\tclienti\tpalchi\n")
        for s in range(10):
            f.write("0\t12:00:%02d\t0\t%d\t%d\n" % (s, 3 * (1 + s // 5), 1 + s // 5))

    t0, t1 = sec(12, 0, 0), sec(12, 0, 9)
    q = leggi_campioni(camp)
    r = conta(reg, q, t0, t1)
    caso("1 sano · le righe DENTRO la finestra, e solo quelle",
         "55 righe", "%d righe" % r[4], r[4] == 55)
    # ⭐ palchi 1 nei secondi 0-4 (1+2+3+4+5 = 15 righe in 5 s), 2 nei 5-9 (40 in 5 s)
    per_n = r[0]
    caso("2 sano · le righe si dividono per NUMERO DI SESSIONI",
         "n=1: 3,0 righe/s · n=2: 8,0",
         "n=1: %.1f · n=2: %.1f" % (per_n[1][1] / per_n[1][0], per_n[2][1] / per_n[2][0]),
         abs(per_n[1][1] / per_n[1][0] - 3.0) < 1e-9
         and abs(per_n[2][1] / per_n[2][0] - 8.0) < 1e-9)
    caso("3 guasto · una riga di un'ALTRA ora non entra nella fetta",
         "la riga delle 13:00 non c'e'",
         "%d nomi di provamt42" % r[3].get("provamt42", 0),
         r[3].get("provamt42", 0) == 0)
    # ⛔ IL GUASTO CHE CONTA: la finestra sbagliata deve dare un numero DIVERSO.
    #    ⚠ Un contatore che desse lo stesso numero su due fette diverse non
    #      starebbe filtrando niente.
    r2 = conta(reg, q, sec(12, 0, 5), sec(12, 0, 9))
    caso("4 guasto · fetta diversa ⇒ numero diverso (il filtro MORDE)",
         "40 righe, non 55", "%d righe" % r2[4], r2[4] == 40)
    caso("5 sano · i byte per riga si ritrovano",
         "%d byte / 55" % os.path.getsize(reg),
         "%.1f byte/riga" % (r[5] / r[4]), r[5] > 0 and r[4] == 55)
    # ⛔ «NON HO LETTO» ≠ «ZERO» — la regola 5 del preambolo.
    caso("6 guasto · campioni che non ci sono ⇒ None, NON zero sessioni",
         "None", repr(leggi_campioni(os.path.join(d, "manca.tsv"))),
         leggi_campioni(os.path.join(d, "manca.tsv")) is None)
    vuoto = os.path.join(d, "vuoto.log")
    open(vuoto, "w").close()
    caso("7 guasto · registro senza righe ⇒ None, NON «zero righe/s»",
         "None", repr(conta(vuoto, q, t0, t1)), conta(vuoto, q, t0, t1) is None)

    ko = len([x for x in esiti if not x])
    print("\n\033[1m== TARATURA: %d casi, %d falliti\033[0m" % (len(esiti), ko))
    return 1 if ko else 0


def main():
    if "--certifica" in sys.argv:
        return certifica()
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    reg, camp, t0s, t1s = sys.argv[1:5]
    q = leggi_campioni(camp)
    if q is None:
        print("    NO  ⛔ NON MISURO: i campioni «%s» non si leggono — e «non ho "
              "letto» non e' «zero sessioni»" % camp)
        return 2
    a = [int(x) for x in t0s.split(":")]
    b = [int(x) for x in t1s.split(":")]
    r = conta(reg, q, sec(*a), sec(*b))
    if r is None:
        print("    NO  ⛔ NON MISURO: nessuna riga nella fetta %s-%s" % (t0s, t1s))
        return 2
    stampa(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
