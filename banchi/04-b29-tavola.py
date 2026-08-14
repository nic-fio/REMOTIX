#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04-b29 — dagli esiti alla tavola, e al catalogo che la pagina si porta dentro.

⛔ NON RIASSUME: **conta**.  Ogni cella della tavola nasce dalle righe di
   `04-b29-esiti.jsonl`, e una cella senza righe si scrive `[?]`, non si deduce
   dalla cella accanto.  (Il rilievo A30 della fase 1: un numero che un revisore
   non puo' ritrovare non e' un numero.)

⛔ E le righe di un palco NON CERTIFICATO non entrano in nessuna cella: sono
   numeri senza banco.  Si contano a parte, e si dice quanti sono.

uso:  python3 banchi/04-b29-tavola.py [--esiti FILE] [--js]
"""
import argparse
import collections
import json
import os

QUI = os.path.dirname(os.path.abspath(__file__))

# palco del banco → nome corto nel catalogo della pagina
CORTO = {
    'finestra': 'finestra',
    'schermo-intero-api': 'intero',
    'schermo-intero-api+lock-vecchia': 'intero+lock',
    'schermo-intero-api+lock-nuova': 'intero+lock-nuova',
    'schermo-intero-F11+lock': 'F11',
}
FAMIGLIA = {'chrome': 'blink', 'firefox': 'gecko', 'chrome-app': 'blink-app'}
SIMBOLO = {'consegnata': '✅ consegnata',
           'consegnata-E-RISERVATA': '⛔ consegnata E RISERVATA',
           'non-consegnata': '⚠ non consegnata',
           'NON-MISURATA': '— non misurata'}


def leggi(percorso):
    righe, palchi, certificati = [], [], {}
    with open(percorso) as f:
        for l in f:
            l = l.strip()
            if not l:
                continue
            r = json.loads(l)
            t = r.get('tipo')
            if t == 'certificazione':
                certificati[(r['motore'], r['palco'])] = r['certificato']
            elif t == 'palco':
                palchi.append(r)
            elif t in ('palco-fallito',):
                certificati.setdefault((r['motore'], r['palco']), False)
            elif t is None:
                righe.append(r)
    return righe, palchi, certificati


def principale():
    p = argparse.ArgumentParser()
    p.add_argument('--esiti', default=os.path.join(QUI, '04-b29-esiti.jsonl'))
    p.add_argument('--js', action='store_true', help='stampa il catalogo per la pagina')
    a = p.parse_args()
    righe, palchi, cert = leggi(a.esiti)

    # ── ⛔ LA REGOLA DI CREDIBILITA', e vale per tutt'e due i motori ────────
    #
    # Una riga e' una misura solo se si puo' dimostrare che **la battuta e'
    # arrivata da qualche parte**.  Le prove ammesse sono tre, e ne basta una:
    #
    #   · la pagina ha visto la combinazione            (`consegnata`)
    #   · il browser ha fatto qualcosa di visibile      (`browser_ha_agito`)
    #   · la pagina ha visto almeno un MODIFICATORE     (`modificatori_visti`)
    #
    # ⛔ Una riga senza nessuna delle tre non distingue «se la tiene il
    #    browser» da «l'iniezione non e' partita» — e sono due fatti opposti.
    #    Non si sceglie il piu' comodo: si butta la riga e si conta quante se ne
    #    sono buttate.  `[M]` 14 agosto 2026 questa regola ha salvato un giro
    #    intero di Firefox che sarebbe stato pubblicato come «Firefox si tiene
    #    tutto, compreso Ctrl+C».
    def credibile(r):
        if r['stato'] == 'NON-MISURATA':
            return False
        if r.get('consegnata_alla_pagina') or r.get('browser_ha_agito'):
            return True
        return bool(r.get('modificatori_visti'))

    buttate = [r for r in righe
               if not cert.get((r['motore'], r.get('palco')), False)
               or r.get('palco_scaduto') or not credibile(r)]
    buone = [r for r in righe if r not in buttate]

    print('== 04-b29 · %d righe lette · %d buone · %d buttate' %
          (len(righe), len(buone), len(buttate)))
    per_motore = collections.Counter((r['motore'], r.get('palco')) for r in buttate)
    for k, v in sorted(per_motore.items()):
        print('   ⛔ buttate %2d righe di %s / %s' % (v, k[0], k[1]))
    for m in palchi:
        print('   %-8s %s · lock vecchia presente=%s · opzione keyboardLock letta=%s'
              % (m['motore'], m['versione'], m.get('lock_vecchia_presente'),
                 m.get('opzione_keyboardLock_letta')))
    print('   palchi certificati:')
    for k, v in sorted(cert.items()):
        print('     %-9s %-34s %s' % (k[0], k[1], 'sì' if v else '⛔ NO'))

    # ── la tavola: combinazione × (motore, palco) × stato ──────────────────
    tavola = collections.defaultdict(dict)
    for r in buone:
        tavola[r['combinazione']][(r['motore'], CORTO.get(r['palco'], r['palco']))] = r['stato']
    colonne = sorted({k for v in tavola.values() for k in v},
                     key=lambda c: (c[0], list(CORTO.values()).index(c[1])
                                    if c[1] in CORTO.values() else 9))
    print('\n== TAVOLA — combinazione × motore/palco × stato (dei tre)')
    print('| combinazione | ' + ' | '.join('%s %s' % c for c in colonne) + ' |')
    print('|---|' + '---|' * len(colonne))
    for comb in sorted(tavola):
        celle = []
        for c in colonne:
            s = tavola[comb].get(c)
            celle.append(SIMBOLO.get(s, '`[?]` non provato') if s else '`[?]` non provato')
        print('| `%s` | %s |' % (comb, ' | '.join(celle)))

    # ── il conto per palco: quante perse, quante nel caso peggiore ─────────
    print('\n== IL CONTO, palco per palco')
    print('| motore | palco | consegnate | ⛔ consegnate E RISERVATE | non consegnate |')
    print('|---|---|---|---|---|')
    conto = collections.Counter()
    for r in buone:
        conto[(r['motore'], CORTO.get(r['palco'], r['palco']), r['stato'])] += 1
    for c in colonne:
        print('| %s | %s | %d | **%d** | %d |'
              % (c[0], c[1], conto[(c[0], c[1], 'consegnata')],
                 conto[(c[0], c[1], 'consegnata-E-RISERVATA')],
                 conto[(c[0], c[1], 'non-consegnata')]))

    if a.js:
        # ⛔ Il catalogo che la pagina si porta dentro NON contiene i controlli:
        #    quelli servono al banco, non all'utente.
        # ⛔ IL CATALOGO DELLA PAGINA SI COSTRUISCE SUL GIRO CON
        #    `preventDefault()`, non sull'altro — e non e' una scelta di comodo:
        #    il prodotto lo chiama (l'ancora `F4-INPUT-CLASSICO` lo chiama su
        #    ogni battuta che spedisce).  ⇒ Il giro SENZA e' la misura di che
        #    cosa fa il browser da solo; il giro CON e' **quel che l'utente
        #    vedra'**.  Dichiarare all'utente il primo sarebbe dirgli che perde
        #    diciotto scorciatoie che invece non perde.
        # ⚠ Dove il giro con `preventDefault` non c'e', si usa l'altro e **lo si
        #   scrive nella cella** (`prevenuto: false`), invece di lasciar credere
        #   che i due giri siano la stessa cosa.
        migliori = {}
        for r in buone:
            k = (r['motore'], r.get('palco'), r['combinazione'])
            vecchia = migliori.get(k)
            if vecchia is None or (r.get('preventDefault') and not vecchia.get('preventDefault')):
                migliori[k] = r
        buone = list(migliori.values())
        cat = {}
        for r in buone:
            if r['combinazione'].startswith('CONTROLLO'):
                continue
            fam = FAMIGLIA.get(r['motore'], r['motore'])
            palco = CORTO.get(r['palco'], r['palco'])
            # ⛔ Il palco «lock nuova» NON entra nel catalogo della pagina, e non
            #    e' una perdita: la pagina non sa dire QUALE forma di lock ha in
            #    mano quando la lock c'e' — sa solo che c'e'.  ⇒ La riga
            #    `intero+lock` deve venire dal palco in cui la lock e' stata
            #    davvero **concessa**, altrimenti sotto quel nome ci finirebbe
            #    un palco SENZA lock, che e' la bugia che questa ancora esiste
            #    per non dire.  ⚠ Nella tavola del rapporto invece ci resta: li'
            #    serve a mostrare che il motore l'opzione l'ha ignorata.
            if palco == 'intero+lock-nuova':
                if not r.get('lock_concessa'):
                    continue
                palco = 'intero+lock'
            # ⚠ E una riga in cui la lock era chiesta ma NON viva alla battuta
            #   non descrive il palco che dichiara: si scarta invece di mediarla.
            if palco == 'intero+lock' and r.get('lock_viva_alla_battuta') is False:
                continue
            # ⛔ Nel catalogo entra SOLO quel che si perde: una voce
            #    «consegnata» sarebbe rumore in un avviso che l'utente deve
            #    leggere in fretta, sopra il suo desktop.
            if r['stato'] == 'consegnata':
                continue
            cat.setdefault(fam, {}).setdefault(palco, {})[r['combinazione']] = (
                r['stato'] if r.get('preventDefault') or r['stato'] != 'consegnata-E-RISERVATA'
                else r['stato'] + '-non-prevenuta')
        print('\n== CATALOGO per `src/pagina.html` ==')
        print(json.dumps(cat, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    principale()
