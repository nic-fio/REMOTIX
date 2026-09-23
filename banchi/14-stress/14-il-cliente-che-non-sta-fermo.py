#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""14-il-cliente-che-non-sta-fermo — ⭐⭐ UN CLIENTE CHE TOCCA LE COSE.

    python3 14-il-cliente-che-non-sta-fermo.py --certifica
    python3 14-il-cliente-che-non-sta-fermo.py --minuti 8 --desktop kde

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ PERCHE' QUESTO BANCO ESISTE — ed e' la lezione, non il codice
═══════════════════════════════════════════════════════════════════════════════
⛔⛔ **Tutti i nostri banchi avevano un cliente EDUCATO.**  Aprivano la pagina,
    entravano nella sessione, e poi stavano fermi a guardare: nessun
    movimento del mouse, nessun tasto, nessuna rotella.  Un utente vero non
    sta mai cosi'.

⇒ E per questo un difetto grosso e' stato invisibile **da sempre**: il 23
  settembre 2026 si e' scoperto che `batti_fra()` RIMANDAVA il battito del
  server a ogni chiamata, e `regola_battito()` gira a ogni messaggio di input
  del client.  ⚠ Un browser che manda ~40 messaggi di input al secondo teneva
  il battito da 1 s **in eterno**, e con lui `video_regola()`, cioe' l'unico
  posto da cui la CHIAVE si richiede al palco (§5.2).  ⇒ Lo schermo si fermava
  per minuti interi, e nessuna misura della notte lo vedeva, perche' nessuna
  misura della notte muoveva il mouse.

⭐ QUESTO BANCO FA LA COSA CHE ROMPE: muove il mouse di continuo (20
  `pointerMove` al secondo, in una sola `PerformActions`) per tutta la
  sessione, con Firefox VERO e VISIBILE sul tablet.  ⛔ Senza quel movimento la
  stessa misura e' verde e non dice niente.

═══════════════════════════════════════════════════════════════════════════════
`[M]` I DUE NUMERI CHE HA PRODOTTO — 23 settembre 2026, scatola `rete11-kde`
═══════════════════════════════════════════════════════════════════════════════
    PRIMA della cura       22 battiti in 3 minuti · il `da_ms` piu' lungo
                           **46 192 ms** — il battito si poteva rimandare
                           all'infinito, e il 58 % dei secondi aveva lo schermo
                           fermo, con blocchi fino a 6 minuti.
    DOPO la cura          508 battiti in 8 minuti · il `da_ms` piu' lungo
                           **1 102 ms** · 0 secondi fermi su 340.

⚠ E il numero che conta non e' la percentuale: e' **il blocco PIU' LUNGO**.
  Una media si puo' guardare e dire «va bene»; sei minuti di schermo fermo no.

═══════════════════════════════════════════════════════════════════════════════
⛔ COME SI LEGGE IL RISULTATO
═══════════════════════════════════════════════════════════════════════════════
Il banco guarda `consegnati` della pagina UNA VOLTA AL SECONDO e conta i
secondi in cui non e' cresciuto.  ⚠ Non e' un verdetto automatico: questo non
e' una maglia della rete (niente guasto innestato, niente 0/1/3) — e' uno
**strumento di misura**, e il giudizio lo da' chi lo legge.  ⛔ La ragione sta
in fondo a questo file, sotto «PERCHE' NON E' UNA MAGLIA DELLA RETE».

⚠ E NON REIMPLEMENTA NIENTE: l'inquilino, la scena, il browser vero e i
  contatori vengono da `stress_nucleo`; la scena testimone da `stress_occhio`.
"""
import argparse
import importlib.util
import json
import os
import sys
import time

BANCHI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUI = os.path.dirname(os.path.abspath(__file__))


def carica(nome, percorso):
    s = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(s)
    sys.modules[nome] = m
    s.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
#  LA PARTE PURA — ⛔ si certifica senza toccare niente
# ═══════════════════════════════════════════════════════════════════════════
def fermi(serie, chiave="consegnati"):
    """⭐⭐ La FORMA del blocco, non solo quanto.

    Da una serie di letture al secondo torna
    `(secondi_fermi, secondi_guardati, blocco_piu_lungo_s)`.

    ⛔ Il numero che decide e' **il blocco piu' lungo**: `[M]` 23 set 2026, il
       58 % di secondi fermi non ha convinto nessuno finche' non si e' detto
       che il piu' lungo durava **sei minuti**.  Una percentuale si negozia,
       sei minuti di schermo fermo no.

    ⚠ Le letture senza numero (`None`) non contano ne' come ferme ne' come
      vive: «non lo so» non e' «fermo», ed e' la regola di tutto il progetto.
    """
    buoni = [r for r in (serie or []) if r.get(chiave) is not None]
    fermi_n, piu_lungo, corrente = 0, 0, 0
    for i in range(1, len(buoni)):
        if buoni[i][chiave] == buoni[i - 1][chiave]:
            fermi_n += 1
            corrente += 1
            piu_lungo = max(piu_lungo, corrente)
        else:
            corrente = 0
    return fermi_n, max(0, len(buoni) - 1), piu_lungo


def gesti_di_un_secondo(passo, x0=300, y0=300, quanti=20, durata_ms=50):
    """⭐ Un secondo di movimento VERO, in una sola andata e ritorno.

    ⛔ Venti `pointerMove` da 50 ms l'uno: e' il ritmo con cui un utente che
       muove il mouse riempie il canale di input, ed e' esattamente la cosa che
       teneva fermo il battito del server.
    ⚠ Una sola `PerformActions` per secondo, non venti chiamate: venti andate e
      ritorni di Marionette misurerebbero Marionette, non il prodotto.
    """
    return [{"type": "pointerMove",
             "x": int(x0 + 200 * ((i + passo) % 5) / 4.0),
             "y": int(y0 + 150 * ((i + passo) % 3) / 2.0),
             "origin": "viewport", "duration": durata_ms}
            for i in range(quanti)]


# ⭐ I due passaggi del decodificatore che la pagina non mette su `window`:
#   `fuori` (quanti ne ha consegnati il decodificatore) e `dentro` (quanti
#   gliene abbiamo dato e non sono usciti).  ⛔ Sono la meta' del conto che dice
#   DOVE si ferma l'immagine (`src/pagina.html`, `4a06829`).
JS_DOVE = r"""
const R = window.REMOTIX, s = R && R.schermo, c = s && s.conti;
if (!c) return {};
return {fuori: c.usciti, dentro: (c.consegnati - c.usciti)};
"""


# ═══════════════════════════════════════════════════════════════════════════
#  LA MISURA VIVA
# ═══════════════════════════════════════════════════════════════════════════
def muovi(browser, passo):
    """Il gesto, mandato al browser vero.

    ⚠ Si passa dal guidatore Marionette di `12-client-veri.py`
      (`browser.g.m.chiama`): ⛔ `Browser.muovi()` sposta il puntatore UNA
      volta, e una volta al secondo non riempie niente.
    """
    browser.g.m.chiama("WebDriver:PerformActions",
                       {"actions": [{"type": "pointer", "id": "topo",
                                     "parameters": {"pointerType": "mouse"},
                                     "actions": gesti_di_un_secondo(passo)}]})


def gira(o):
    nucleo = carica("stress_nucleo", os.path.join(QUI, "stress_nucleo.py"))
    occhio = carica("stress_occhio", os.path.join(QUI, "stress_occhio.py"))
    porta = nucleo.PORTE[o.desktop]
    os.makedirs(o.uscita, exist_ok=True)
    chi = "%s%d" % (o.inquilino, 1 if o.browser == "firefox" else 2)

    print("== l'inquilino ==", flush=True)
    fatto, perche = nucleo.crea_inquilino(o.desktop, chi, o.parola)
    print("   %s — %s" % (fatto, perche), flush=True)
    if not fatto:
        return 3

    print("== la scena DICHIARATA ==", flush=True)
    fatto, perche = occhio.deposita_scena(nucleo, o.desktop)
    print("   %s — %s" % (fatto, perche), flush=True)
    if not fatto:
        return 3

    t_box = nucleo.istante_nella_scatola(o.desktop)
    print("   orologio della scatola: %s (UTC)" % t_box, flush=True)

    serie, b, codice = [], None, 3
    try:
        print("== il browser VERO e VISIBILE ==", flush=True)
        b = nucleo.avvia_browser(o.browser, porta)
        ok, perche = b.apri()
        print("   apri: %s — %s" % (ok, perche), flush=True)
        if not ok:
            return 3
        esito, perche = b.entra(chi, o.parola)
        print("   entra: esito %s — %s" % (esito, perche), flush=True)
        if esito != 0:
            return 3

        # ⛔⛔ LA CORSA COL COMPOSITORE: la sessione grafica dell'inquilino
        #     NASCE ADESSO, e nell'istante in cui il client e' ammesso il
        #     socket wayland non c'e' ancora.  ⇒ Si aspetta (12 × 5 s), e se
        #     non si accende **si dice e si smette**: misurare un desktop fermo
        #     credendo di misurare una scena in movimento e' il modo peggiore
        #     in cui questo banco potrebbe sbagliare (`stress_nucleo.scena`).
        accesa, perche = nucleo.scena(o.desktop, o.scena, chi, giri=12, passo=5.0)
        print("   scena: %s — %s" % ("ACCESA" if accesa else "⛔ SPENTA", perche),
              flush=True)
        if not accesa:
            print("   ⛔ non misuro: senza scena questi numeri non direbbero "
                  "niente e sembrerebbero buoni.", flush=True)
            return 3
        time.sleep(o.attesa_scena)

        print("== %g minuti · MOUSE CHE SI MUOVE DI CONTINUO ==" % o.minuti,
              flush=True)
        t0 = time.time()
        fine, prossimo, passo, mosse = t0 + o.minuti * 60, t0, 0, 0
        while time.time() < fine:
            prossimo += 1.0
            c = nucleo.conta_dalla_pagina(b)
            try:
                x = b.js(JS_DOVE)
            except Exception:                                # noqa: BLE001
                x = None
            if isinstance(x, dict):
                c.update(x)
            c["t"] = time.time()
            c["ora"] = time.strftime("%H:%M:%S")
            serie.append(c)
            if len(serie) % 30 == 0:
                print("   %s  consegnati=%s dipinti=%s mosse=%d"
                      % (c["ora"], c.get("consegnati"), c.get("dipinti"), mosse),
                      flush=True)
            # ⭐ E il movimento riempie il resto del secondo: e' la cosa che
            #   rompe, e va fatta SEMPRE, non ogni tanto.
            try:
                passo += 1
                muovi(b, passo)
                mosse += 20
            except Exception as e:                           # noqa: BLE001
                print("   ⚠ mouse: %s" % e, flush=True)
            resta = prossimo - time.time()
            if resta > 0:
                time.sleep(resta)
        codice = 0

        print("== chiudo la SCHEDA (congedo 0x01) ==", flush=True)
        b.vai("about:blank")
        time.sleep(4)
    finally:
        if b is not None:
            try:
                b.chiudi()
            except Exception:                            # noqa: BLE001
                pass
        # ⛔ E L'INQUILINO SI TOGLIE: `[M]` 22 set 2026, i residui di sessioni
        #    di prova hanno fatto smettere di rispondere `WebDriver:NewSession`.
        #    ⚠ `--lascia-l-inquilino` serve a chi vuole guardare la scatola dopo.
        if not o.lascia_l_inquilino:
            tolto, dice = nucleo.sgombera(o.desktop, chi)
            print("   sgombero: %s (%s)"
                  % ("pulito" if tolto else "⚠ resta roba", dice), flush=True)

    print("\n== I NUMERI DELLA PAGINA ==", flush=True)
    buoni = [r for r in serie if r.get("consegnati") is not None]
    riass = {}
    if buoni:
        u = buoni[-1]
        manc = (u["consegnati"] or 0) - (u["dipinti"] or 0)
        print("   consegnati %s · dipinti %s · MANCANO %d (%.1f %%)"
              % (u["consegnati"], u["dipinti"], manc,
                 100.0 * manc / max(1, u["consegnati"] or 1)), flush=True)
        print("   buchi %s · chiavi chieste %s"
              % (u.get("buchi"), u.get("chiavi_chieste")), flush=True)
        f, quanti, piu_lungo = fermi(serie)
        print("   ⚠ secondi in cui `consegnati` NON e' cresciuto: %d su %d "
              "(%.1f %%) — il blocco PIU' LUNGO: %d s"
              % (f, quanti, 100.0 * f / max(1, quanti), piu_lungo), flush=True)
        riass = {"consegnati": u["consegnati"], "dipinti": u["dipinti"],
                 "secondi_fermi": f, "secondi": quanti,
                 "blocco_piu_lungo_s": piu_lungo,
                 "chiavi_chieste": u.get("chiavi_chieste")}
    dove = os.path.join(o.uscita, "serie.json")
    with open(dove, "w", encoding="utf-8") as f:
        json.dump({"riassunto": riass, "serie": serie, "t_box": t_box,
                   "chi": chi, "desktop": o.desktop, "browser": o.browser,
                   "minuti": o.minuti}, f, ensure_ascii=False)
    print("   t_box=%s chi=%s · serie in %s" % (t_box, chi, dove), flush=True)
    return codice


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE — ⛔ prima si prova che sa dire di NO
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    guai = [0]

    def p(nome, ottenuto, atteso):
        bene = ottenuto == atteso
        if not bene:
            guai[0] += 1
        print("  %s  %-60s %s" % ("OK " if bene else "NO ", nome,
                                  "" if bene else "⇒ %r (volevo %r)" % (ottenuto, atteso)))

    print("\n══ il cliente che non sta fermo — la certificazione ═════════════")
    print("\n── il conto dei secondi fermi ──")
    vivo = [{"consegnati": i} for i in range(11)]
    p("⭐ undici letture che crescono: zero secondi fermi", fermi(vivo), (0, 10, 0))
    fermo = [{"consegnati": 5} for _ in range(11)]
    p("⛔ undici letture uguali: dieci secondi fermi, blocco lungo dieci",
      fermi(fermo), (10, 10, 10))
    misto = [{"consegnati": n} for n in (1, 1, 1, 2, 3, 3, 4)]
    p("⭐⭐ e la FORMA: sei fermi… no, tre fermi e il blocco piu' lungo e' due",
      fermi(misto), (3, 6, 2))
    p("⛔ due blocchi corti non fanno un blocco lungo",
      fermi([{"consegnati": n} for n in (1, 1, 2, 2, 3)]), (2, 4, 1))
    p("⚠ una serie vuota non fa cadere niente", fermi([]), (0, 0, 0))
    p("⚠ una lettura sola non ha intervalli", fermi([{"consegnati": 1}]), (0, 0, 0))
    p("⛔ le letture «non lo so» non contano come ferme",
      fermi([{"consegnati": 1}, {"consegnati": None}, {"consegnati": 2}]),
      (0, 1, 0))
    p("⛔ e non contano nemmeno come vive",
      fermi([{"consegnati": None}, {"consegnati": None}]), (0, 0, 0))

    print("\n── i gesti del mouse ──")
    g = gesti_di_un_secondo(0)
    p("⭐ venti movimenti in un secondo", len(g), 20)
    p("⭐ da 50 ms l'uno ⇒ un secondo pieno", sum(a["duration"] for a in g), 1000)
    p("⛔ e si MUOVONO davvero (non venti volte lo stesso punto)",
      len({(a["x"], a["y"]) for a in g}) > 1, True)
    p("⚠ e restano dentro la finestra (origine «viewport», mai negativi)",
      all(a["origin"] == "viewport" and a["x"] >= 0 and a["y"] >= 0 for a in g), True)
    p("⭐ il passo sposta la figura (due secondi non sono identici)",
      gesti_di_un_secondo(0) != gesti_di_un_secondo(1), True)

    print("\n%s  %d guai" % ("⭐ LA PARTE PURA REGGE." if guai[0] == 0
                             else "⛔ QUALCOSA NON TORNA.", guai[0]))
    print("⚠ il resto lo prova il ferro: questo banco vale quando gira contro "
          "una scatola vera, con un Firefox vero e visibile.")
    return 1 if guai[0] else 0


def main():
    a = argparse.ArgumentParser(
        description="un cliente che muove il mouse di continuo, e misura se "
                    "lo schermo si ferma")
    a.add_argument("--certifica", action="store_true",
                   help="le funzioni pure, senza toccare niente")
    a.add_argument("--desktop", default="kde")
    a.add_argument("--browser", default="firefox")
    a.add_argument("--minuti", type=float, default=8.0)
    a.add_argument("--inquilino", default="c43u")
    a.add_argument("--parola", default="prova-lunga-2026")
    a.add_argument("--scena", default="testimone")
    a.add_argument("--attesa-scena", type=float, default=25.0)
    a.add_argument("--lascia-l-inquilino", action="store_true",
                   help="⚠ non sgombera: per guardare la scatola dopo")
    # ⛔ Su questo tablet `/tmp` sta in RAM: le serie vanno su disco vero.
    a.add_argument("--uscita", default="/home/nicfio/REMOTIX-misure/battito")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    return gira(o)


if __name__ == "__main__":
    sys.exit(main())


# ═══════════════════════════════════════════════════════════════════════════
# ⚠⚠ PERCHE' NON E' (ANCORA) UNA MAGLIA DELLA RETE
# ═══════════════════════════════════════════════════════════════════════════
# La rete delle maglie ha tre regole che questo banco oggi non rispetta:
#   · ogni maglia ha un GUASTO INNESTATO che la fa diventare rossa — qui il
#     guasto sarebbe «rimetti `batti_fra()` com'era», cioe' una modifica al
#     prodotto in C, non un interruttore;
#   · ogni maglia da' un verdetto 0/1/3 — qui servirebbe una SOGLIA sul blocco
#     piu' lungo, e una soglia che non si e' tarata e' un numero inventato;
#   · ogni maglia sta dentro il tetto di tempo della notte — qui la misura che
#     ha trovato il difetto e' durata OTTO MINUTI, e sotto i tre non si vedeva.
#
# ⭐ Il parere di chi l'ha portato dentro: **si', dovrebbe diventarlo**, ma la
#   decisione e' del regista e la strada e' questa, in quest'ordine:
#     1. il movimento del mouse entra negli scenari che gia' esistono (una riga
#        in `scenari/_comune.py`: un cliente che tocca le cose e' il
#        comportamento NORMALE, non uno scenario a parte);
#     2. si tara la soglia sul blocco piu' lungo con tre o quattro giri sani
#        (`[M]` col difetto 46 192 ms, curato 1 102 ms: fra i due c'e' un
#        fattore quaranta, quindi la soglia non e' delicata);
#     3. il guasto innestato arriva per ultimo, quando c'e' un modo di
#        rimettere il difetto senza ricompilare.
# ⛔ Finche' i tre punti non ci sono, farne una maglia significherebbe metterne
#    in rete una che non sa diventare rossa: la rete si fiderebbe di una
#    guardia cieca, ed e' peggio di non averla.
