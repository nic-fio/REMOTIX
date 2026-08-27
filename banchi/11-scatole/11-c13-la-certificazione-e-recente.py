#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c13 — ⭐⭐ «LA CERTIFICAZIONE E' RECENTE» — la maglia che guarda LA RETE
===========================================================================

    python3 11-c13-la-certificazione-e-recente.py
    python3 11-c13-la-certificazione-e-recente.py --certifica
    python3 11-c13-la-certificazione-e-recente.py --ultimi 40

---------------------------------------------------------------------------
⛔⛔ IL GUASTO CHE PRENDE — e `fasi/11…` §4.2 lo dice meglio di come lo direi io
---------------------------------------------------------------------------

  ⛔ *«una rete che non e' piu' capace di dare rosso HA ESATTAMENTE L'ASPETTO
       di una rete che non trova niente.»*

⚠ Ed e' il guasto piu' difficile da vedere di tutta la fase, perche' **non ha
  sintomi**.  Tutto verde, ogni giorno, per settimane.  ⇒ E la differenza fra
  *«non c'e' niente che non va»* e *«non guardo piu'»* non si legge da fuori: si
  legge **solo** innestando un guasto e pretendendo che venga visto.

⭐ §3.6 lo dichiara come parte della rete, non come cortesia:
  ⛔ *«ogni prova della lista ha, obbligatoriamente, il suo guasto innestato, e
     quel caso va fatto girare, NON IMMAGINATO»* — e ⇒ *«il registro di quel che
     e' stato iniettato, quando, e con che esito, e' parte della rete (C13)»*.

---------------------------------------------------------------------------
⭐ CHE COSA GUARDA — e i tre esiti che sa distinguere
---------------------------------------------------------------------------

Legge il registro del gancio e, negli ultimi **N giri veri**, cerca **almeno una
maglia** che porti tutt'e due le cose:

    "guasto_innestato": true    ⇒ le e' stato innestato un guasto
    "ha_visto_il_guasto": true  ⇒ e lei lo ha VISTO

⛔⛔ E LE DUE COSE DEVONO STARE NELLA STESSA MAGLIA, non nello stesso giro.
   ⚠ Se bastasse *«in questo giro c'era un guasto innestato E qualcuno ha dato
     rosso»*, il rosso potrebbe venire da **un'altra maglia** — per esempio da
     C1, che un guasto vero ce l'ha davvero — ⇒ e questa maglia direbbe *«la
     rete sa dare rosso»* avendo guardato una prova che non c'entra niente.
     ⛔ Sarebbe un controllo che non puo' dare rosso: la forma d'errore di
     `LEZIONI.md` §1.44.

⚠ E il campo si chiama `ha_visto_il_guasto` e non `esito` per una ragione: su un
  giro innestato **l'esito si legge al contrario** (C8 `--senza-cura` esce **0**
  quando il guasto e' stato visto).  ⭐ Quell'inversione sta in un posto solo —
  dentro il gancio — e qui non serve saperla.

I tre casi distinti, e sono davvero tre cose diverse:

  ⛔ **mai innestato niente**    la rete gira e nessuno la mette alla prova
  ⛔⛔ **innestato e NON visto**  il caso peggiore: la rete ha avuto un guasto
                                sotto il naso e ha detto verde
  ⭐ **innestato e visto**       la rete e' ancora capace di dare rosso

---------------------------------------------------------------------------
⚠ IL METRO, dichiarato e stampato in ogni esito
---------------------------------------------------------------------------

  `[?]` **ultimi 20 giri veri.**  ⛔ Scelto, non misurato.
  ⚠ I giri a VUOTO (`--secco`) non contano: un giro che non ha eseguito niente
    non puo' aver visto niente.

⛔ E il criterio e' **a CONTI, non a giorni** — perche' cosi' lo chiede §4.2
   (*«negli ultimi N giri»*).  ⚠ Ha un buco dichiarato: se il gancio girasse una
   volta al mese, «gli ultimi venti giri» coprirebbero due anni.  ⇒ L'eta'
   dell'ultima certificazione si **stampa sempre**, e con `--giorni N` diventa
   anche un giudizio.  ⭐ Predefinito spento: questa maglia fa quel che il
   documento le chiede, e non inventa politica per conto suo.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ negli ultimi N giri un guasto e' stato innestato ed E' STATO VISTO
  1  ⛔ nessun guasto innestato, oppure innestato e non visto ⇒ rosso
  3  ⛔ non ho potuto guardare — nessun giro vero da esaminare, o il registro
     non si lascia leggere.  ⛔ E NON e' un rosso: che il gancio non abbia mai
     girato lo dice **C12**, e due maglie che danno rosso per lo stesso fatto
     fanno sembrare grave il doppio quel che e' successo una volta sola
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import json
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
REGISTRO = os.path.join(QUI, "11-gancio-registro.jsonl")

ULTIMI_PREDEFINITI = 20


def leggi_il_registro(percorso):
    """Torna (giri, guaio) — ⛔ e i tre casi sono tre, come in C12.

       (None, "assente")     il file non c'e'
       (None, "illeggibile") c'e' e non si apre, o e' tutto storto
       ([...], None)         i giri, in ordine di scrittura
    """
    if not os.path.exists(percorso):
        return None, "assente"
    try:
        with open(percorso, "r", errors="replace") as f:
            righe = f.read().splitlines()
    except OSError:
        return None, "illeggibile"
    giri, storte = [], 0
    for r in righe:
        r = r.strip()
        if not r:
            continue
        try:
            giri.append(json.loads(r))
        except ValueError:
            storte += 1
    if not giri and storte:
        return None, "illeggibile"
    return giri, None


def giudica(giri, ultimi):
    """Dice se la rete e' ancora capace di dare rosso.

    ⛔ Torna `None` per «non ho potuto guardare» (nessun giro vero da guardare),
       altrimenti un dizionario:

         esaminati       quanti giri veri ha guardato
         innestati       quante maglie hanno avuto un guasto innestato
         viste           quante di quelle lo hanno VISTO
         mancate         l'elenco (giro, maglia) di quelle che NON lo hanno visto
         ultima          il giro in cui l'ultima certificazione e' riuscita
    """
    if giri is None:
        return None
    # ⛔ I giri a vuoto si buttano PRIMA di contare gli ultimi N: contarli
    #    vorrebbe dire che venti `--secco` di fila spingono fuori dalla finestra
    #    l'ultima certificazione vera, e la maglia diventa rossa per niente.
    veri = [g for g in giri if not g.get("secco")]
    if not veri:
        return None
    fetta = veri[-ultimi:]

    innestati = 0
    viste = 0
    mancate = []
    ultima = None
    for g in fetta:
        for m in g.get("maglie") or []:
            if not m.get("guasto_innestato"):
                continue
            innestati += 1
            # ⛔ La chiave dev'esserci ED essere vera.  ⚠ Una chiave ASSENTE non
            #   e' «visto»: e' un registro piu' vecchio del campo, cioe' «non lo
            #   so» — e qui vale come «non visto», perche' una certificazione di
            #   cui non si sa l'esito non certifica niente.
            if m.get("ha_visto_il_guasto") is True:
                viste += 1
                ultima = g
            else:
                mancate.append((g.get("istante"), m.get("nome"),
                                m.get("ha_visto_il_guasto")))
    return {"esaminati": len(fetta), "innestati": innestati, "viste": viste,
            "mancate": mancate, "ultima": ultima, "totali": len(veri),
            "a_vuoto": len(giri) - len(veri)}


def eta_in_giorni(istante, adesso):
    """⛔ Torna `None` se non sa dirlo — mai zero, mai un numero inventato."""
    if not istante:
        return None
    try:
        import datetime
        t = datetime.datetime.fromisoformat(istante)
        if t.tzinfo is None:
            t = t.astimezone()
        return (adesso - t.timestamp()) / 86400.0
    except (ValueError, TypeError, OverflowError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ Si dimostra che il giudice SA dare rosso, verde, e «non lo so»."""

    def giro(maglie, secco=False, istante="2026-08-26T05:00:00+02:00"):
        return {"istante": istante, "secco": secco, "maglie": maglie}

    def m(nome, guasto=False, visto=None, esito=0):
        d = {"nome": nome, "esito": esito, "guasto_innestato": guasto}
        if visto is not None:
            d["ha_visto_il_guasto"] = visto
        return d

    casi = [
        ("⭐ un guasto innestato, e la rete lo ha VISTO",
         [giro([m("C1"), m("C8 guasto", guasto=True, visto=True)])], "verde"),

        ("⛔ venti giri e nessun guasto mai innestato",
         [giro([m("C1"), m("C11")]) for _ in range(20)], "ROSSO"),

        ("⛔⛔ innestato e NON visto — il caso peggiore",
         [giro([m("C8 guasto", guasto=True, visto=False, esito=1)])], "ROSSO"),

        # ⭐⭐ IL CASO CHE TIENE IN PIEDI TUTTA LA MAGLIA.
        ("⭐⭐ rosso da un'ALTRA maglia non certifica niente",
         [giro([m("C1", esito=1),
                m("C8 guasto", guasto=True, visto=False, esito=1)])], "ROSSO"),

        ("⚠ innestato, e del suo esito non si sa niente (campo assente)",
         [giro([m("C8 guasto", guasto=True)])], "ROSSO"),

        ("una certificazione riuscita fra venti giri normali ⇒ verde",
         [giro([m("C1")]) for _ in range(19)]
         + [giro([m("C8 guasto", guasto=True, visto=True)])], "verde"),

        ("⛔ la certificazione e' scivolata FUORI dalla finestra dei venti",
         [giro([m("C8 guasto", guasto=True, visto=True)])]
         + [giro([m("C1")]) for _ in range(20)], "ROSSO"),

        # ⛔ E i giri a vuoto non devono spingere fuori una certificazione vera.
        ("⭐ venti giri A VUOTO non spingono fuori la certificazione vera",
         [giro([m("C8 guasto", guasto=True, visto=True)])]
         + [giro([m("C1")], secco=True) for _ in range(20)], "verde"),

        ("⛔ tutti i giri sono a vuoto ⇒ «non lo so», non rosso",
         [giro([m("C8 guasto", guasto=True, visto=True)], secco=True)], "non lo so"),

        ("⛔ nessun giro ⇒ «non lo so» — che non abbia mai girato lo dice C12",
         [], "non lo so"),

        ("⛔ registro illeggibile ⇒ «non lo so», non rosso",
         None, "non lo so"),
    ]

    print("== certificazione del giudice di C13 ==")
    print("   finestra in vigore: ultimi %d giri VERI · i giri a vuoto non contano"
          % ULTIMI_PREDEFINITI)
    guai = 0
    for nome, giri, atteso in casi:
        r = giudica(giri, ULTIMI_PREDEFINITI)
        if r is None:
            ottenuto = "non lo so"
        elif r["viste"] >= 1:
            ottenuto = "verde"
        else:
            ottenuto = "ROSSO"
        ok = ottenuto == atteso
        print("  %s  %-58s  ⇒ %-9s (atteso %s)"
              % ("OK " if ok else "NO ", nome, ottenuto, atteso))
        if not ok:
            guai += 1
            print("        (il giudice ha detto: %r)" % (r,))

    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ il giudice distingue le tre cose che contano: mai innestato ·")
    print("   innestato e non visto · innestato e visto")
    print("⭐⭐ e ⛔ NON si lascia certificare da un rosso venuto da un'altra maglia")
    print("⚠ e questa certificazione copre IL GIUDIZIO, non i guasti innestati:")
    print("  che siano quelli GIUSTI lo decide §3.6, non io")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--ultimi", type=int, default=ULTIMI_PREDEFINITI,
                   help="quanti giri veri guardare indietro. `[?]` scelto, non misurato")
    p.add_argument("--giorni", type=int, default=0,
                   help="⚠ se > 0, l'eta' dell'ultima certificazione diventa "
                        "anche un GIUDIZIO. Predefinito spento: §4.2 chiede un "
                        "criterio a conti, non a giorni")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    giri, guaio = leggi_il_registro(a.registro)

    print("== C13 — la certificazione e' recente? ==")
    print("   ⛔ il guasto che cerca: una rete che non e' piu' capace di dare")
    print("      rosso HA LO STESSO ASPETTO di una rete che non trova niente")
    print("   metro: ultimi %d giri VERI  `[?]`  ·  i giri a vuoto non contano"
          % a.ultimi)
    if a.giorni:
        print("   ⚠ e in piu': l'ultima certificazione entro %d giorni" % a.giorni)
    print()

    if guaio == "assente":
        print("⛔ il registro non c'e': %s" % a.registro)
        print("   ⇒ non ho potuto guardare — ⛔ e NON e' un rosso.")
        print("     Che il gancio non abbia mai girato lo dice C12, ed e' giusto")
        print("     che lo dica UNA maglia sola.")
        return 3
    if guaio == "illeggibile":
        print("⛔ il registro c'e' e non si lascia leggere: %s" % a.registro)
        print("   ⇒ non ho potuto guardare")
        return 3

    r = giudica(giri, a.ultimi)
    if r is None:
        print("⛔ nessun giro VERO da guardare (%d righe, tutte a vuoto o nessuna)"
              % len(giri or []))
        print("   ⇒ non ho potuto guardare — ⛔ e NON e' un rosso")
        return 3

    print("   giri nel registro : %d veri, %d a vuoto" % (r["totali"], r["a_vuoto"]))
    print("   guardati          : gli ultimi %d" % r["esaminati"])
    print("   guasti innestati  : %d" % r["innestati"])
    print("   ⭐ visti           : %d" % r["viste"])
    adesso = time.time()
    if r["ultima"]:
        eta = eta_in_giorni(r["ultima"].get("istante"), adesso)
        print("   ultima riuscita   : %s  (%s)"
              % (r["ultima"].get("istante"),
                 "eta ignota" if eta is None else "%.1f giorni fa" % eta))
    print()

    if r["mancate"]:
        print("⛔⛔ E QUESTE MAGLIE HANNO AVUTO UN GUASTO SOTTO IL NASO E NON LO")
        print("    HANNO VISTO:")
        for quando, nome, visto in r["mancate"]:
            print("   · %s  ·  %s  (ha_visto_il_guasto=%r)" % (quando, nome, visto))
        print()

    if r["viste"] >= 1:
        vecchia = False
        if a.giorni and r["ultima"]:
            eta = eta_in_giorni(r["ultima"].get("istante"), adesso)
            if eta is not None and eta > a.giorni:
                vecchia = True
                print("⛔ ROSSO — l'ultima certificazione riuscita e' di %.1f giorni"
                      " fa, e la soglia chiesta e' %d" % (eta, a.giorni))
        if not vecchia:
            print("⭐ negli ultimi %d giri un guasto e' stato innestato ed E' STATO"
                  " VISTO %d volte" % (r["esaminati"], r["viste"]))
            print("⚠ e questo dice che la rete sa ancora dare rosso SUI GUASTI CHE")
            print("  CONOSCE. ⛔ §3.6: i guasti innestati sono guasti gia' noti, e")
            print("  ogni desktop nuovo deve entrare con **un guasto suo**.")
            if r["mancate"]:
                print("⚠ ⛔ ma sopra c'e' un elenco di certificazioni MANCATE: vanno")
                print("  guardate, anche se questa maglia e' verde.")
            return 0
        return 1

    if r["innestati"] == 0:
        print("⛔⛔ ROSSO — negli ultimi %d giri **nessun guasto e' mai stato"
              " innestato**." % r["esaminati"])
        print("   ⇒ la rete gira, e nessuno la mette alla prova. ⛔ Da fuori e'")
        print("     indistinguibile da una rete che funziona benissimo.")
        print("   ⚠ E la cura non e' toccare questa maglia: e' far girare la")
        print("     famiglia `tutto`, che il guasto innestato ce l'ha dentro.")
        return 1

    print("⛔⛔ ROSSO — %d guasti sono stati innestati e **nessuno e' stato visto**."
          % r["innestati"])
    print("   ⇒ ⛔ e' il caso peggiore dei tre: la rete non e' piu' capace di")
    print("     dare rosso, e continua a dire verde con la stessa faccia.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
