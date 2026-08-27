#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c12 — ⭐⭐ «IL GANCIO E' VIVO» — la maglia che guarda LA RETE
===========================================================================

    python3 11-c12-il-gancio-e-vivo.py
    python3 11-c12-il-gancio-e-vivo.py --certifica
    python3 11-c12-il-gancio-e-vivo.py --giorni 3

⛔ Questa maglia **non prova il prodotto**.  Non prova nemmeno la rete: prova
   che la rete **stia ancora girando**.

---------------------------------------------------------------------------
⛔⛔ IL GUASTO CHE PRENDE — *il gancio spento in silenzio*
---------------------------------------------------------------------------

`fasi/11…` §4.2 lo chiama con nome e cognome: ⛔ **«il modo in cui muoiono
queste reti»**.

E vale la pena di dire come muore davvero, perche' non muore con un errore:

  · qualcuno rifa' il deposito, e la cartella dei ganci di git **non si copia**;
  · qualcuno ha una giornata storta, commenta la riga e si dimentica;
  · il gancio c'e', e' installato, ⛔ **e non gira da tre settimane** perche' il
    file installato punta a un percorso che non esiste piu'.

⇒ ⭐ In tutt'e tre i casi la rete **ha esattamente lo stesso aspetto di prima**:
  i file ci sono, le maglie sono scritte, `--certifica` passa.  ⛔ E non gira
  piu' niente.

---------------------------------------------------------------------------
⭐ LE CINQUE COSE CHE GUARDA — e nessuna e' «il file c'e'» e basta
---------------------------------------------------------------------------

  1  il gancio **esiste** al percorso dichiarato
  2  il gancio si puo' **eseguire**
  3  e' **installato** come gancio di git — ⛔ e il file installato NOMINA il
     gancio: un gancio installato che punta altrove e' peggio di nessuno
  4  c'e' **traccia** che abbia girato: il registro esiste e ha almeno un giro
  5  ⛔⛔ e l'ultimo giro **NON e' un giro a vuoto**

⚠⚠ Il quinto merita due righe, perche' senza di lui questa maglia sarebbe una
   di quelle che non danno mai rosso.  Il gancio sa girare `--secco`, cioe' dire
   che cosa farebbe senza farlo.  ⛔ Se un giro a vuoto contasse come traccia,
   **basterebbe un `--secco` a far dire a questa maglia «il gancio e' vivo» per
   una settimana** — mentre non gira niente.  ⇒ Le righe con `"secco": true` si
   buttano, e ⭐ **quel caso e' dentro `--certifica`**: e' provato, non promesso.

---------------------------------------------------------------------------
⚠ LA SOGLIA, dichiarata e stampata in ogni esito
---------------------------------------------------------------------------

`[?]` **7 giorni.**  ⛔ E' scelta, non misurata: nessuno ha ancora osservato
ogni quanto questo deposito viene toccato.  ⇒ Va sostituita con un `[M]` appena
il registro avra' abbastanza righe per dire ogni quanto il gancio scatta
davvero.  ⚠ Fino ad allora, un rosso su questa soglia va **letto** prima di
essere creduto.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ il gancio c'e', e' installato, ed e' girato davvero e di recente
  1  ⛔ una delle cinque cose non regge ⇒ rosso
  3  ⛔ non ho potuto guardare — il registro c'e' ma non si lascia leggere
     (⛔ e NON e' un rosso: «il registro non c'e'» invece **lo e'**, perche'
      vuol dire che il gancio non ha mai girato)
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ I percorsi sono DICHIARATI qui: il gancio e' «definito per percorso, non
#    per buona volonta'» (§5.1), e questa maglia guarda esattamente quel
#    percorso — non uno che si va a cercare.
GANCIO = os.path.join(QUI, "11-gancio.sh")
REGISTRO = os.path.join(QUI, "11-gancio-registro.jsonl")

GIORNI_PREDEFINITI = 7


def leggi_il_registro(percorso):
    """Torna (giri, guaio).

    ⛔ E i tre casi sono TRE, non due, ed e' tutta la differenza:
       (None, "assente")     il file non c'e'   ⇒ ⛔ e' un ROSSO: mai girato
       (None, "illeggibile") c'e' e non si apre ⇒ «non ho potuto guardare»
       ([...], None)         i giri, in ordine di scrittura
    """
    if not os.path.exists(percorso):
        return None, "assente"
    try:
        with open(percorso, "r", errors="replace") as f:
            righe = f.read().splitlines()
    except OSError:
        return None, "illeggibile"
    giri = []
    storte = 0
    for r in righe:
        r = r.strip()
        if not r:
            continue
        try:
            giri.append(json.loads(r))
        except ValueError:
            storte += 1
    # ⚠ Qualche riga storta capita (un giro interrotto a meta' scrittura) e non
    #   e' un guasto.  ⛔ TUTTE storte invece vuol dire che non sto leggendo un
    #   registro: e' «non ho potuto guardare», non «non e' mai girato».
    if not giri and storte:
        return None, "illeggibile"
    return giri, None


def giudica(stato, giorni):
    """Dato lo stato, dice che cosa NON regge.

    `stato` e' un dizionario:
       c_e            il file del gancio esiste
       eseguibile     lo si puo' eseguire
       installato     l'elenco dei ganci di git che NOMINANO il nostro gancio
       giri           l'elenco dei giri letti dal registro, o None
       guaio          «assente» · «illeggibile» · None
       adesso         l'istante, in secondi

    ⛔ Torna `None` per «non ho potuto guardare», e una LISTA (magari vuota)
       quando ha guardato.  ⚠ `None` non e' la lista vuota: «non ho guardato» e
       «ho guardato e va tutto bene» sono due cose diverse, e questo progetto ha
       gia' pagato per averle confuse.
    """
    if stato.get("guaio") == "illeggibile":
        return None

    guai = []
    if not stato.get("c_e"):
        guai.append("il gancio non c'e' al percorso dichiarato")
        # ⛔ E si torna subito: senza il file, «non e' eseguibile» e «non e'
        #    installato» sono conseguenze, non guasti in piu'.  Un elenco che
        #    conta tre volte lo stesso guasto fa sembrare grave quel che e'
        #    semplice, e viceversa.
        return guai
    if not stato.get("eseguibile"):
        guai.append("il gancio c'e' ma non si puo' eseguire")
    if not stato.get("installato"):
        guai.append("il gancio NON e' installato fra i ganci di git: "
                    "non lo fara' partire nessuno")

    giri = stato.get("giri")
    if giri is None or not giri:
        guai.append("nessuna traccia: il gancio non ha MAI girato")
        return guai

    # ⛔⛔ E QUI SI BUTTANO I GIRI A VUOTO.  Un `--secco` non e' un giro: se
    #    contasse, questa maglia direbbe «vivo» mentre non gira niente.
    veri = [g for g in giri if not g.get("secco")]
    if not veri:
        guai.append("ci sono %d giri, ⛔ ma sono TUTTI a vuoto (--secco): "
                    "il gancio non ha mai misurato niente" % len(giri))
        return guai

    ultimo = veri[-1]
    quando = ultimo.get("istante")
    eta = eta_in_giorni(quando, stato.get("adesso"))
    if eta is None:
        # ⚠ Un istante che non si lascia leggere non e' «vecchio»: e' «non lo
        #   so».  ⛔ E qui si sceglie di dirlo come guasto del REGISTRO, non
        #   come gancio morto — perche' non e' la stessa cosa.
        guai.append("l'ultimo giro non porta un istante leggibile (%r): "
                    "il registro e' storto" % (quando,))
    elif eta > giorni:
        guai.append("l'ultimo giro vero e' di %.1f giorni fa, e la soglia "
                    "dichiarata e' %d" % (eta, giorni))
    return guai


def eta_in_giorni(istante, adesso):
    """⛔ Torna `None` se non sa dirlo — mai zero, mai un numero inventato."""
    if not istante or adesso is None:
        return None
    try:
        import datetime
        t = datetime.datetime.fromisoformat(istante)
        if t.tzinfo is None:
            t = t.astimezone()
        return (adesso - t.timestamp()) / 86400.0
    except (ValueError, TypeError, OverflowError):
        return None


def ganci_installati():
    """Quali ganci di git NOMINANO il nostro gancio.

    ⛔ Non basta che il file `pre-push` esista: dev'essere il NOSTRO.  Un gancio
       di qualcun altro allo stesso nome farebbe dire «installato» a questa
       maglia mentre la rete non parte.
    """
    try:
        p = subprocess.run(["git", "-C", QUI, "rev-parse", "--git-path", "hooks"],
                           capture_output=True, text=True, timeout=30)
    except OSError:
        return None
    if p.returncode != 0:
        return None
    cartella = p.stdout.strip()
    # ⛔⛔ E QUI C'ERA UN DIFETTO CHE AVREBBE RESO QUESTA MAGLIA INUTILE PER
    #    SEMPRE — `[M]` 26 agosto 2026, preso dal banco di prova.
    #
    # `git --git-path` torna un percorso **relativo alla cartella data a `-C`**,
    # non alla radice del deposito: da `banchi/11-scatole` risponde
    # `../../.git/hooks`.  ⚠ La prima stesura lo incollava alla RADICE, e ne
    # usciva un percorso che non esiste ⇒ ⛔ **«il gancio NON e' installato»,
    # sempre, qualunque cosa si facesse.**
    # ⇒ E un rosso che non si puo' far diventare verde e' peggio di nessuna
    #   maglia: §1.3 — «una rete che da' rosso a vuoto viene spenta da chi
    #   lavora».
    if not os.path.isabs(cartella):
        cartella = os.path.normpath(os.path.join(QUI, cartella))
    trovati = []
    for quale in ("pre-commit", "pre-push"):
        d = os.path.join(cartella, quale)
        if not os.path.isfile(d):
            continue
        try:
            with open(d, "r", errors="replace") as f:
                testo = f.read()
        except OSError:
            continue
        if "11-gancio.sh" in testo:
            trovati.append((quale, d, os.access(d, os.X_OK)))
    return trovati


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ Si dimostra che il giudice SA dare rosso, verde, e «non lo so»."""
    import datetime
    adesso = time.time()

    def istante(giorni_fa):
        t = datetime.datetime.now().astimezone() - datetime.timedelta(days=giorni_fa)
        return t.isoformat()

    def sano(**cambia):
        s = {"c_e": True, "eseguibile": True, "installato": [("pre-push", "/x", True)],
             "giri": [{"istante": istante(0.5), "secco": False}],
             "guaio": None, "adesso": adesso}
        s.update(cambia)
        return s

    casi = [
        ("il gancio c'e', e' installato, ed e' girato ieri",
         sano(), 0),
        ("⛔ il gancio non c'e'",
         sano(c_e=False, eseguibile=False, installato=[]), 1),
        ("⛔ c'e' ma non e' eseguibile",
         sano(eseguibile=False), 1),
        ("⛔⛔ c'e' ed e' girato, ma NON e' installato — il gancio spento in silenzio",
         sano(installato=[]), 1),
        ("⛔ nessun registro: non ha mai girato",
         sano(giri=None, guaio="assente"), 1),
        ("⛔ registro vuoto: non ha mai girato",
         sano(giri=[]), 1),
        # ⭐⭐ IL CASO CHE VALE PIU' DI TUTTI: la traccia c'e' ma non conta.
        ("⭐⭐ l'unico giro e' A VUOTO (--secco) ⇒ deve dare ROSSO",
         sano(giri=[{"istante": istante(0.1), "secco": True}]), 1),
        ("⭐ un giro a vuoto DOPO uno vero e recente ⇒ resta VERDE",
         sano(giri=[{"istante": istante(0.5), "secco": False},
                    {"istante": istante(0.1), "secco": True}]), 0),
        ("⛔ l'ultimo giro vero e' di venti giorni fa (soglia 7)",
         sano(giri=[{"istante": istante(20), "secco": False}]), 1),
        ("⚠ l'istante non si lascia leggere: e' il registro a essere storto",
         sano(giri=[{"istante": "ieri mattina", "secco": False}]), 1),
        # ⛔ E il terzo esito, che non e' un rosso.
        ("⛔ il registro c'e' e non si lascia leggere ⇒ «non lo so», non rosso",
         sano(guaio="illeggibile"), None),
    ]

    print("== certificazione del giudice di C12 ==")
    print("   soglia in vigore: %d giorni · e i giri a vuoto NON contano"
          % GIORNI_PREDEFINITI)
    guai = 0
    for nome, stato, atteso in casi:
        r = giudica(stato, GIORNI_PREDEFINITI)
        # atteso: 0 = verde · 1 = almeno un guasto · None = non lo so
        if atteso is None:
            ottenuto = None
        else:
            ottenuto = 0 if (r is not None and not r) else (1 if r else 0)
            if r is None:
                ottenuto = None
        ok = ottenuto == atteso
        print("  %s  %-62s  ⇒ %s (atteso %s)"
              % ("OK " if ok else "NO ", nome,
                 "non lo so" if ottenuto is None
                 else ("verde" if ottenuto == 0 else "ROSSO"),
                 "non lo so" if atteso is None
                 else ("verde" if atteso == 0 else "ROSSO")))
        if not ok:
            guai += 1
            print("        (il giudice ha detto: %r)" % (r,))

    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ il giudice vede il gancio morto, vede il gancio scollegato,")
    print("   ⭐⭐ e ⛔ NON si lascia ingannare da un giro a vuoto")
    print("⚠ e questa certificazione copre IL GIUDIZIO, non il gancio: che il")
    print("  gancio faccia davvero girare le maglie lo dice C13, non io")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gancio", default=GANCIO)
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--giorni", type=int, default=GIORNI_PREDEFINITI,
                   help="da quanti giorni al massimo il gancio puo' non aver "
                        "girato. `[?]` scelta, non misurata")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    installati = ganci_installati()
    if installati is None:
        print("⛔ non sono dentro un deposito git: non so nemmeno dove")
        print("   guardare i ganci")
        print("   ⇒ il terreno non regge")
        sys.exit(2)

    giri, guaio = leggi_il_registro(a.registro)
    stato = {
        "c_e": os.path.isfile(a.gancio),
        # ⚠ «eseguibile» qui vuol dire due cose insieme: il bit sul file OPPURE
        #   la possibilita' di leggerlo (il progetto lo chiama con `bash …`).
        #   ⛔ Quel che DEVE avere il bit e' il file installato dentro `.git`,
        #   e quello si guarda a parte, sotto.
        "eseguibile": os.access(a.gancio, os.X_OK) or os.access(a.gancio, os.R_OK),
        "installato": installati,
        "giri": giri,
        "guaio": guaio,
        "adesso": time.time(),
    }

    print("== C12 — il gancio e' vivo? ==")
    print("   ⛔ il guasto che cerca: il gancio spento in silenzio — il modo in")
    print("      cui muoiono queste reti (§4.2)")
    print("   soglia dichiarata: ultimo giro entro %d giorni  `[?]`" % a.giorni)
    print("   ⛔ e i giri a VUOTO (--secco) non contano come traccia\n")

    print("   gancio      : %s  %s" % (a.gancio, "c'e'" if stato["c_e"] else "⛔ NON C'E'"))
    if installati:
        for quale, dove, esec in installati:
            print("   installato  : %-11s %s%s"
                  % (quale, dove, "" if esec else "  ⛔ non eseguibile"))
    else:
        print("   installato  : ⛔ da nessuna parte")
    if guaio == "assente":
        print("   registro    : ⛔ NON C'E' — il gancio non ha mai girato")
    elif guaio == "illeggibile":
        print("   registro    : ⚠ c'e' e non si lascia leggere")
    else:
        veri = [g for g in giri if not g.get("secco")]
        print("   registro    : %d giri (%d veri, %d a vuoto)"
              % (len(giri), len(veri), len(giri) - len(veri)))
        if veri:
            eta = eta_in_giorni(veri[-1].get("istante"), stato["adesso"])
            print("   ultimo giro : %s  (%s)"
                  % (veri[-1].get("istante"),
                     "eta ignota" if eta is None else "%.1f giorni fa" % eta))
    print()

    r = giudica(stato, a.giorni)
    if r is None:
        print("⛔ il registro c'e' e non si lascia leggere.")
        print("   ⇒ non ho potuto guardare — ⛔ e NON e' un rosso")
        return 3
    if r:
        print("⛔⛔ ROSSO — il gancio non e' vivo:")
        for g in r:
            print("   · %s" % g)
        print()
        print("   ⇒ ⛔ e finche' e' cosi', **tutto il resto della rete non serve**:")
        print("     le maglie possono essere perfette, se non le fa partire")
        print("     nessuno non prendono niente.")
        return 1
    print("⭐ il gancio c'e', e' installato, ed e' girato davvero entro %d giorni"
          % a.giorni)
    print("⚠ e questa maglia dice che il gancio GIRA, ⛔ non che la rete sappia")
    print("  ancora dare rosso: quello e' C13.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
