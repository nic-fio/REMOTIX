#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-registro-unisci — ⭐⭐ UNA MEMORIA SOLA, e resta in coda
===========================================================================

    python3 11-registro-unisci.py <registro-che-riceve> <righe-arrivate>
    python3 11-registro-unisci.py --certifica

---------------------------------------------------------------------------
⛔⛔ IL GUAIO CHE RISOLVE — *due registri che non si parlano*
---------------------------------------------------------------------------

`DECISIONI.md` §4.6-novemdecies: le due meta' del gancio vivono su due macchine.
⇒ `11-gancio-registro.jsonl` **nasce dove il gancio gira**, quindi ce n'e' uno
sul portatile e uno sulla macchina di prova.  ⛔ E **C13** — la maglia che dice
se la rete sa ancora dare rosso — legge solo quello della macchina su cui gira.

⇒ ⭐ La memoria sola sta **sul portatile**, e non e' una preferenza: e' l'unico
  posto dove le due maglie che leggono quella memoria sanno giudicare.
  ⛔ **C12** ha bisogno del deposito git per sapere dove stanno i ganci — sulla
  macchina di prova esce **2**, «terreno cattivo» (`fasi/11…` §7-bis.16, e li'
  e' scritto che *e' la risposta giusta*).  ⇒ Il portatile e' dove la rete si
  guarda allo specchio; la macchina di prova e' dove **esegue**.

---------------------------------------------------------------------------
⛔⛔ E LA REGOLA DELL'ORDINE, che e' tutto il mestiere di questo file
---------------------------------------------------------------------------

Il registro e' **in coda e mai riscritto** (`11-gancio.sh`, in testa).  ⇒ Qui
non si riordina niente e non si riscrive niente: ⭐ **si accodano soltanto le
righe piu' NUOVE della piu' recente gia' presente.**

⚠ E la ragione non e' l'eleganza, e' un rosso falso:

  · **C12** guarda `veri[-1]`, cioe' **l'ultima riga del file**, non la piu'
    recente.  ⛔ Se un'unione accodasse una riga vecchia in fondo, C12 direbbe
    *«l'ultimo giro e' di venti giorni fa»* mentre il gancio ha girato un minuto
    fa — un rosso che non si puo' far diventare verde, cioe' `LEZIONI.md` §1.49,
    che e' peggio di nessuna maglia.
  · **C13** guarda gli ultimi N: righe fuori ordine cambiano **quali** N.

⇒ ⭐ Accodando solo il piu' nuovo, il file resta **monotono per istante** per
  costruzione, e nessuna delle due maglie va toccata.

⛔ **IL PREZZO, dichiarato**: una riga remota piu' VECCHIA della piu' recente
   gia' presente **non entra mai piu'**.  ⇒ Se qualcuno fa girare il gancio a mano
   sulla macchina di prova *mentre* il portatile ne scrive uno suo, quel giro e'
   perso per la memoria comune.  ⚠ Non e' grave — resta nel registro della
   macchina di prova, che non si cancella — ma **si dice**: e' il numero
   `perse_perche_vecchie` che questo programma stampa a ogni unione, invece di
   sparire in silenzio.

⚠ E i due orologi devono andare d'accordo, perche' il confronto e' fra istanti.
  `[M]` 27 agosto 2026: portatile `2026-08-27T07:20:03+02:00`, macchina di prova
  `2026-08-27T05:20:03+00:00` ⇒ **lo stesso istante, scarto 0 s**.  ⛔ Il giorno
  che l'orologio della macchina di prova restasse indietro, le sue righe
  sembrerebbero vecchie e non entrerebbero: ⇒ per questo lo scarto **si stampa**
  quando c'e' qualcosa da dire.

---------------------------------------------------------------------------
⚠ E QUEL CHE ARRIVA NON E' PULITO
---------------------------------------------------------------------------

Le righe arrivano da `sshpw.py --get`, cioe' da uno `scp`: ⭐ **mai** dallo
stdout di un `cat` remoto, dove finisce anche la richiesta di password
(`v1/strumenti/sshpw.py`, e c'e' scritto perche').  ⇒ Restano comunque possibili
righe vuote o troncate (un giro interrotto a meta' scrittura).
⛔ Una riga che non si lascia leggere **non si butta in silenzio**: si conta e si
   stampa.  ⚠ E se NON si lascia leggere **nessuna** riga, non e' «zero righe
   nuove»: e' **non ho potuto guardare**, ed esce 3.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  l'unione e' riuscita (anche con zero righe nuove: e' un fatto, non un guaio)
  3  ⛔ non ho potuto guardare — l'arrivato non contiene nessuna riga leggibile
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import datetime
import json
import os
import sys


def istante_di(riga_json):
    """Torna l'istante come secondi, o `None` se non lo sa dire.

    ⛔ Mai zero e mai un numero inventato: «non lo so» ha un valore suo, e
       questo progetto ha gia' pagato per averlo confuso con «vecchissimo».
    """
    q = riga_json.get("istante")
    if not q:
        return None
    try:
        t = datetime.datetime.fromisoformat(q)
    except (ValueError, TypeError):
        return None
    if t.tzinfo is None:
        t = t.astimezone()
    return t.timestamp()


def leggi(percorso):
    """Torna (coppie, storte): coppie e' [(istante_o_None, testo_riga, oggetto)]."""
    if not os.path.exists(percorso):
        return [], 0
    with open(percorso, "r", errors="replace") as f:
        righe = f.read().splitlines()
    coppie, storte = [], 0
    for r in righe:
        r = r.strip()
        if not r:
            continue
        try:
            o = json.loads(r)
        except ValueError:
            storte += 1
            continue
        if not isinstance(o, dict):
            storte += 1
            continue
        coppie.append((istante_di(o), r, o))
    return coppie, storte


def scegli(gia_presenti, arrivate):
    """⭐ Il giudizio, separato dai file — cosi' si puo' certificare.

    Torna (da_accodare, perse_perche_vecchie, gia_c_erano, senza_istante).

    da_accodare e' in ordine di istante crescente.
    """
    testi_presenti = set(t for _, t, _ in gia_presenti)
    istanti_presenti = [i for i, _, _ in gia_presenti if i is not None]
    # ═══════════════════════════════════════════════════════════════════
    # ⛔⛔ IL CONFINE E' IL PIU' RECENTE, **non l'ultima riga del file** — e la
    #     prima stesura aveva scritto l'ultima riga.  ⭐ L'ha presa la
    #     certificazione qui sotto, `[M]` 27 agosto 2026, e non l'avrebbe presa
    #     nessuna lettura.
    #
    # ⚠ Sembrava il contrario: C12 legge `veri[-1]`, cioe' l'ultima riga, ⇒ il
    #   confine «naturale» sembrava quella.  ⛔ Ma se il file fosse GIA' fuori
    #   ordine (istanti 500, poi 100), col confine sull'ultima riga entrerebbe
    #   una riga da 300 e il file finirebbe 500 · 100 · 300: l'ultima riga
    #   **ancora non e' la piu' recente**, e C12 continuerebbe a leggere un
    #   giro che non e' l'ultimo.
    #
    # ⭐ Col MASSIMO invece l'invariante si tiene da sola: entra solo cio' che e'
    #   piu' nuovo di tutto, e in ordine crescente ⇒ **l'ultima riga del file e'
    #   sempre la piu' recente**, che e' esattamente la cosa che serve a C12.
    # ═══════════════════════════════════════════════════════════════════
    confine = max(istanti_presenti) if istanti_presenti else None

    nuove, vecchie, doppie, senza = [], 0, 0, 0
    for i, testo, _ in arrivate:
        if testo in testi_presenti:
            doppie += 1
            continue
        if i is None:
            # ⚠ Una riga senza istante non si sa dove mettere: accodarla
            #   sfonderebbe la monotonia, cioe' il rosso falso di C12.
            senza += 1
            continue
        if confine is not None and i <= confine:
            vecchie += 1
            continue
        nuove.append((i, testo))
    nuove.sort(key=lambda c: c[0])
    return [t for _, t in nuove], vecchie, doppie, senza


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ Si dimostra che il giudizio sa fare le tre cose per cui esiste:
       accodare il nuovo, RIFIUTARE il vecchio, e non ripetere il gia' visto."""

    def r(secondi, nome="x"):
        t = datetime.datetime.fromtimestamp(secondi, datetime.timezone.utc)
        o = {"istante": t.isoformat(), "nome": nome}
        testo = json.dumps(o, sort_keys=True)
        return (secondi, testo, o)

    casi = [
        ("⭐ una riga piu' nuova si accoda",
         [r(100)], [r(200)], (1, 0, 0, 0)),
        ("⛔⛔ una riga piu' VECCHIA non entra — sfonderebbe l'ordine di C12",
         [r(300)], [r(200)], (0, 1, 0, 0)),
        ("⛔ la riga identica gia' presente non si ripete",
         [r(100)], [r(100)], (0, 0, 1, 0)),
        ("⭐ tre nuove entrano tutte, e in ordine",
         [r(100)], [r(400), r(200), r(300)], (3, 0, 0, 0)),
        ("⭐ il registro che riceve e' vuoto: entra tutto",
         [], [r(200), r(100)], (2, 0, 0, 0)),
        ("⚠ una riga senza istante non si sa dove mettere: resta fuori, e si conta",
         [r(100)], [(None, '{"nome":"senza"}', {"nome": "senza"})], (0, 0, 0, 1)),
        # ⭐⭐ IL CASO CHE HA CORRETTO QUESTO FILE — vedi il commento in `scegli`.
        ("⭐⭐ il registro e' gia' fuori ordine: il confine e' il PIU' RECENTE",
         [r(500), r(100)], [r(300)], (0, 1, 0, 0)),
        ("⭐ mescolate: solo quelle oltre il confine, in ordine",
         [r(100)], [r(50), r(150), r(120)], (2, 1, 0, 0)),
    ]

    print("== certificazione del giudizio di 11-registro-unisci ==")
    print("   ⛔ la regola: si accoda SOLO cio' che e' piu' nuovo della riga")
    print("      piu' RECENTE gia' presente — cosi' l'ultima riga del file")
    print("      resta la piu' recente, che e' quel che C12 legge")
    guai = 0
    for nome, presenti, arrivate, atteso in casi:
        nuove, vecchie, doppie, senza = scegli(presenti, arrivate)
        ottenuto = (len(nuove), vecchie, doppie, senza)
        ok = ottenuto == atteso
        # ⭐ e non basta il conto: le nuove devono uscire IN ORDINE.
        if ok and len(nuove) > 1:
            istanti = []
            for t in nuove:
                istanti.append(istante_di(json.loads(t)))
            if istanti != sorted(istanti):
                ok = False
        print("  %s  %-62s ⇒ %s (atteso %s)"
              % ("OK " if ok else "NO ", nome, ottenuto, atteso))
        if not ok:
            guai += 1

    # ⭐⭐ E il caso che vale piu' di tutti: unire DUE VOLTE di fila non deve
    #    aggiungere niente la seconda volta.  ⛔ Un'unione che si ripete e'
    #    un registro che si gonfia di copie, e C13 conterebbe la stessa
    #    certificazione venti volte credendo di averne venti.
    presenti = [r(100)]
    arrivate = [r(200), r(300)]
    nuove, _, _, _ = scegli(presenti, arrivate)
    presenti2 = presenti + [(istante_di(json.loads(t)), t, json.loads(t)) for t in nuove]
    nuove2, _, doppie2, _ = scegli(presenti2, arrivate)
    ok = (len(nuove) == 2 and len(nuove2) == 0 and doppie2 == 2)
    print("  %s  %-62s ⇒ %s"
          % ("OK " if ok else "NO ",
             "⭐⭐ unire due volte di fila non aggiunge niente la seconda",
             (len(nuove), len(nuove2), doppie2)))
    if not ok:
        guai += 1

    print()
    if guai:
        print("⛔ il giudizio NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ accoda il nuovo, rifiuta il vecchio, non ripete il gia' visto,")
    print("   ⭐⭐ e ripetuto due volte non gonfia il registro")
    print("⚠ e questa certificazione copre L'UNIONE, non il trasporto: che le")
    print("  righe arrivino davvero dalla macchina di prova lo dice il giro")
    print("  vero di `11-gancio.sh remoto`, non io")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("locale", nargs="?", help="il registro che riceve")
    p.add_argument("arrivate", nargs="?", help="il file di righe arrivate")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())
    if not a.locale or not a.arrivate:
        p.error("servono il registro che riceve e il file arrivato")

    if not os.path.exists(a.arrivate):
        print("⛔ non c'e' niente da unire: %s non esiste" % a.arrivate)
        print("   ⇒ non ho potuto guardare")
        return 3

    presenti, storte_qui = leggi(a.locale)
    arrivate, storte_la = leggi(a.arrivate)

    if not arrivate:
        print("⛔ nel file arrivato non c'e' nessuna riga leggibile "
              "(%d storte)" % storte_la)
        print("   ⇒ non ho potuto guardare — ⛔ e NON e' «zero righe nuove»")
        return 3

    nuove, vecchie, doppie, senza = scegli(presenti, arrivate)

    with open(a.locale, "a") as f:
        for t in nuove:
            f.write(t + "\n")

    print("== unione dei registri ==")
    print("   qui c'erano       : %d righe (%d storte)" % (len(presenti), storte_qui))
    print("   arrivate          : %d righe (%d storte)" % (len(arrivate), storte_la))
    print("   ⭐ accodate        : %d" % len(nuove))
    print("   gia' c'erano      : %d" % doppie)
    if vecchie:
        print("   ⚠ perse_perche_vecchie : %d — piu' vecchie dell'ultima riga di"
              " qui, e accodarle romperebbe l'ordine che C12 legge" % vecchie)
    if senza:
        print("   ⚠ senza istante   : %d — non si sa dove metterle" % senza)
    return 0


if __name__ == "__main__":
    sys.exit(main())
