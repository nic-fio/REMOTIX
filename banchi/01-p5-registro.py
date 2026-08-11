#!/usr/bin/env python3
"""01-p5-registro.py — l'attrezzo che LEGGE e SCRIVE `01-p5-esiti.jsonl`.

    python3 01-p5-registro.py aggiungi '<json>'
    python3 01-p5-registro.py righe
    python3 01-p5-registro.py elenco   --giro G --da N
    python3 01-p5-registro.py battuta  --giro G --da N
    python3 01-p5-registro.py cerca    --giro G --da N --tipo PRONTA
    python3 01-p5-registro.py passi    --log FILE --marca-inizio A --marca-fine B \\
                                       --utente prova [--atteso sessione|respinto|niente-sessione]

===========================================================================
⛔ PERCHE' UN ATTREZZO E NON TRE `grep` DENTRO LO SCRIPT

`LEZIONI.md` §1.9, e le sue otto vesti: in questo progetto un `grep` dentro un
tubo ha gia' prodotto, in quattro giorni, un «0 su 4» che era un riscontro
riuscito, un «uscita 0» che era lo stato di `tail`, e un verde su una ricerca
mai eseguita.  ⭐ Qui ogni lettura **dichiara il proprio denominatore** — su
quante righe ha guardato — ed esce con uno stato che distingue «non c'e'» da
«non ho potuto leggere».

    0   trovato
    1   NON trovato (e il file c'era, e si dice quante righe aveva)
    3   ⛔ non ho potuto leggere: il file non c'e', o non si apre

===========================================================================
⛔ E IL COMANDO `passi`, CHE E' IL CUORE DEL GIRO CONTRO IL PRODOTTO

Il verdetto del giro col browser vero **non puo'** venire dalla pagina: quella
e' `src/pagina.html`, e' del prodotto, non e' nostra e non si tocca.  Viene dal
**registro del server**, cioe' dal lato che deve ricevere (`CODER.md` §3.8: *«il
registro di chi manda dice che ha chiamato una funzione, non che il byte e'
arrivato»* — e qui a mandare `CREDENZIALI` e' il browser, a riceverle e'
il server, quindi il server e' il lato giusto).

⛔ E l'attribuzione al motore NON si fa a tempo.  Gli orologi delle due
   macchine sono a **due ore di distanza** (`[M]` 11 agosto 2026: qui CEST, la'
   UTC), e un banco che segmenta un registro altrui con il proprio orologio e'
   la settima veste di §1.9 — il rosso puntato sull'imputato sbagliato.

⭐ La cura: **due marcatori scritti nel registro del server dal browser
   stesso**.  Prima e dopo il giro, il motore in prova naviga su

       https://192.168.0.2:7448/p5-<motore>-<giro>-inizio
       https://192.168.0.2:7448/p5-<motore>-<giro>-fine

   che `pagina.c` non riconosce (`strcmp(percorso, "/")`) e serve con un 404 —
   ⛔ ma **prima logga la riga** `GET /p5-… da <indirizzo>`.  Tutto quel che sta
   fra le due righe e' di quel motore, scritto **con l'orologio del server**, e
   nessuna aritmetica fra fusi entra nel verdetto.

⚠ E i marcatori li batte **il browser**, non `curl`: un marcatore di `curl`
  proverebbe che questa macchina raggiunge il server, non che il motore in
  prova ci sia arrivato — e sono due fatti diversi, uno dei quali e' proprio
  quello in prova.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "01-p5-esiti.jsonl"

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


# ===========================================================================
# Scrittura
# ===========================================================================
def marca_il_tempo(dati):
    adesso = datetime.now().astimezone()
    dati["ora"] = adesso.isoformat(timespec="milliseconds")
    dati["ora_utc"] = adesso.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    scarto = adesso.strftime("%z")
    dati["fuso"] = f"{adesso.tzname()} (UTC{scarto[:3]}:{scarto[3:]})"
    return dati


def aggiungi(testo):
    try:
        dati = json.loads(testo)
    except Exception as sbaglio:
        print(f"{ROSSO}NO{GRIGIO}  non e' JSON: {sbaglio}", file=sys.stderr)
        return 3
    marca_il_tempo(dati)
    with REGISTRO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dati, ensure_ascii=False) + "\n")
        f.flush()
    return 0


# ===========================================================================
# Lettura
# ===========================================================================
def leggi():
    """Restituisce (righe, guasto).  ⛔ Uno dei due e' sempre None.

    ⚠ Un registro che non esiste ancora e' **zero righe**, non un guasto: lo
      crea il raccoglitore alla prima riga, e prima di allora la risposta
      onesta a «quante ce ne sono» e' zero.  ⛔ Un file che c'e' e non si legge
      e' un'altra cosa, e sotto ha il suo ramo: e' la distinzione di §1.9 fra
      «vuoto» e «proibito», e va tenuta **anche quando il vuoto e' legittimo**.
    """
    if not REGISTRO.exists():
        return [], None
    try:
        crude = REGISTRO.read_text(encoding="utf-8").splitlines()
    except Exception as sbaglio:
        return None, f"«{REGISTRO}» non si legge: {sbaglio}"
    fuori = []
    for i, r in enumerate(crude):
        if not r.strip():
            continue
        try:
            fuori.append((i + 1, json.loads(r)))
        except Exception:
            fuori.append((i + 1, {"tipo": "RIGA-STORTA", "grezzo": r[:200]}))
    return fuori, None


def cerca(giro, da, tipo, ultima=True):
    righe, guasto = leggi()
    if guasto:
        print(guasto, file=sys.stderr)
        return None, 3, 0
    candidate = [(n, d) for n, d in righe
                 if n > da and d.get("giro") == giro and d.get("tipo") == tipo]
    if not candidate:
        return None, 1, len(righe)
    return (candidate[-1] if ultima else candidate[0]), 0, len(righe)


# ===========================================================================
# `passi` — il registro del server, segmentato per motore
# ===========================================================================
#
# ⛔ Ogni passo dichiara: la riga che lo prova, quante volte l'ha trovata, e
#    quante ne voleva.  Un conteggio senza denominatore non e' una misura
#    (`LEZIONI.md` §1.9, quarta regola).
#
# ⚠ I testi qui sotto sono LETTI da `src/rcp.c` e `src/pagina.c` dell'11 agosto
#   2026, non ricordati.  Se il server cambia una di queste frasi, questo banco
#   deve dare ROSSO su «passo non trovato» — non verde: e' la ragione per cui
#   ogni passo obbligatorio pretende almeno un'occorrenza, e per cui esiste il
#   passo `pagina-servita`, che se manca dice che si sta leggendo il registro
#   sbagliato.
PASSI = [
    ("pagina-servita",   r"GET / da ",                                   1, None),
    ("canale-controllo", r"canale di controllo aperto da ",              1, None),
    ("negoziato",        r"negoziato video\.codec=",                     1, None),
    ("credenziali",      r"CREDENZIALI ricevute utente=",                1, None),
    ("secondo-fisso",    r"il secondo fisso e' passato \((\d+) ms\)",    1, "ms"),
    ("pam",              r"PAM ha risposto: (ammesso|respinto)",         1, "pam"),
    ("ammesso",          r"ammesso utente=",                             1, None),
    ("respinto",         r"respinto motivo=",                            0, None),
    ("posto-preso",      r"posto PRESO da .*occupati adesso: (\d+)",     1, "occupati"),
    ("sessione",         r"sessione aperta utente=",                     1, None),
    ("congedo-canale",   r"il client si congeda, motivo=",               0, None),
    ("congedo-chiusura", r"la pagina ha chiuso la sessione, motivo",     0, None),
    ("posto-lasciato",   r"posto LASCIATO da .*occupati adesso: (\d+)",  1, "occupati"),
    ("byte-dopo-la-fine", r"byte arrivati DOPO la fine",                 0, "zero"),
    ("tentativo-fallito", r"tentativo fallito da ",                      0, None),
    ("bannato",          r"BANNATO l'indirizzo ",                        0, "zero"),
    ("conto-azzerato",   r"il conto dei falliti torna a zero",           0, None),
]

# Che cosa ci si aspetta, scenario per scenario.  ⛔ Non e' una tabella di
# comodo: e' il posto in cui «l'atteso lo confronta il banco, non chi legge»
# (regola B0.4) diventa codice.
ATTESI = {
    # il giro buono: si arriva a SESSIONE, e il posto si libera alla fine
    "sessione": {
        "canale-controllo": 1, "negoziato": 1, "credenziali": 1,
        "pam": "ammesso", "ammesso": 1, "posto-preso": 1, "sessione": 1,
        "posto-lasciato": 1, "byte-dopo-la-fine": 0, "respinto": 0,
        "tentativo-fallito": 0, "bannato": 0,
    },
    # il controllo che dice NO, con la parola sbagliata
    "respinto": {
        "canale-controllo": 1, "negoziato": 1, "credenziali": 1,
        "pam": "respinto", "respinto": 1, "ammesso": 0, "sessione": 0,
        "posto-preso": 0, "tentativo-fallito": 1, "bannato": 0,
    },
    # il controllo che dice NO, con l'impronta storpiata: la sessione
    # WebTransport non deve nemmeno nascere
    "niente-sessione": {
        "pagina-servita": 1, "canale-controllo": 0, "credenziali": 0,
        "sessione": 0, "posto-preso": 0, "tentativo-fallito": 0, "bannato": 0,
    },
}


def passi(percorso, marca_inizio, marca_fine, atteso, utente):
    try:
        testo = Path(percorso).read_text(encoding="utf-8", errors="replace")
    except Exception as sbaglio:
        print(f"{ROSSO}NO{GRIGIO}  ⛔ il registro del server non si legge ({sbaglio}).")
        print("      Non e' «nessun passo»: e' «non ho potuto guardare» — §1.9.")
        return None, 3
    tutte = testo.splitlines()

    # ── Il segmento, e i suoi due denominatori ──────────────────────────────
    inizi = [i for i, r in enumerate(tutte) if marca_inizio in r]
    fini = [i for i, r in enumerate(tutte) if marca_fine in r]
    esito = {
        "righe_nel_registro": len(tutte),
        "marca_inizio": marca_inizio, "marca_inizio_trovata": len(inizi),
        "marca_fine": marca_fine, "marca_fine_trovata": len(fini),
    }
    if not inizi or not fini:
        print(f"{ROSSO}NO{GRIGIO}  ⛔ i marcatori non ci sono tutt'e due "
              f"(inizio {len(inizi)}, fine {len(fini)}) su {len(tutte)} righe.")
        print("      ⛔ E questo NON e' «il motore ha fallito»: e' «il motore non")
        print("         ha nemmeno parlato col server», oppure «sto leggendo un")
        print("         registro che non e' di questo giro».  Due cause opposte,")
        print("         e nessun verdetto si da' su nessuna delle due.")
        esito["verdetto"] = "SENZA-DENOMINATORE"
        return esito, 2
    segmento = tutte[inizi[-1]: fini[-1] + 1]
    esito["righe_nel_segmento"] = len(segmento)
    corpo = "\n".join(segmento)

    # ── I passi ─────────────────────────────────────────────────────────────
    voluti = ATTESI.get(atteso)
    if voluti is None:
        print(f"{ROSSO}NO{GRIGIO}  scenario «{atteso}» sconosciuto: "
              f"i noti sono {', '.join(sorted(ATTESI))}")
        return esito, 3
    esito["scenario"] = atteso
    esito["passi"] = {}
    guasti = 0
    approvati = 0
    for nome, modello, _minimo, extra in PASSI:
        trovate = re.findall(modello, corpo)
        quante = len(trovate)
        voce = {"trovate": quante, "modello": modello}
        if extra == "ms" and trovate:
            voce["ms"] = [int(x) for x in trovate]
        elif extra in ("pam", "occupati") and trovate:
            voce["valori"] = trovate
        if nome in voluti:
            atteso_qui = voluti[nome]
            approvati += 1
            if isinstance(atteso_qui, int):
                voce["atteso"] = atteso_qui
                if atteso_qui == 0:
                    voce["ok"] = (quante == 0)
                else:
                    voce["ok"] = (quante >= atteso_qui)
            else:  # un valore, non un conteggio (PAM)
                voce["atteso"] = atteso_qui
                voce["ok"] = atteso_qui in trovate
            if not voce["ok"]:
                guasti += 1
        else:
            voce["atteso"] = "—  (dichiarato, non giudicato)"
            voce["ok"] = None
        esito["passi"][nome] = voce

    # ── Le due strade del congedo (§3.1 punto 3) ────────────────────────────
    #
    # ⛔ Non e' un di piu': «il congedo arriva per due strade diverse, una per
    #    motore» — Chrome lo manda come byte sul canale di controllo, Firefox
    #    azzera il canale e il motivo arriva dentro il codice di chiusura della
    #    sessione.  ⚠ Pretenderne UNA sola scriverebbe «Firefox non si congeda»,
    #    che e' falso.  Qui si contano tutt'e due e si dichiara QUALE.
    canale = esito["passi"]["congedo-canale"]["trovate"]
    chiusura = esito["passi"]["congedo-chiusura"]["trovate"]
    esito["congedo"] = {
        "sul_canale_di_controllo": canale,
        "nel_codice_di_chiusura": chiusura,
        "strada": ("canale" if canale and not chiusura else
                   "chiusura" if chiusura and not canale else
                   "tutt'e due" if canale and chiusura else "NESSUNA"),
    }
    if atteso == "sessione" and canale + chiusura == 0:
        print(f"{ROSSO}NO{GRIGIO}  ⛔ nessun congedo, per nessuna delle due strade "
              f"di §3.1: §8.1 lo impone senza condizioni")
        guasti += 1
    if atteso == "sessione":
        approvati += 1

    # ── ⛔ IL POSTO, e questo e' il punto che un motore solo non vede ────────
    #
    #    §8.2 `0x0F`: il posto non si liberava quando a chiudere il canale era
    #    il SERVER — visto **solo su Chrome**, perche' su Firefox il trasporto
    #    chiudeva lo stream in tempo e il posto se ne andava lo stesso.  Il
    #    numero che lo dice e' «occupati adesso: N» dell'ultima riga
    #    `posto LASCIATO`.
    lasciato = esito["passi"]["posto-lasciato"].get("valori") or []
    esito["posto_finale_occupati"] = int(lasciato[-1]) if lasciato else None
    if atteso == "sessione":
        approvati += 1
        if esito["posto_finale_occupati"] != 0:
            print(f"{ROSSO}NO{GRIGIO}  ⛔ IL POSTO NON SI E' LIBERATO: "
                  f"«occupati adesso» finisce a {esito['posto_finale_occupati']}")
            print("      §8.2 0x0F — ed e' il difetto che si vede SOLO nella")
            print("      differenza fra i due motori: con un motore solo, questa")
            print("      riga e' verde per il motore sbagliato.")
            guasti += 1

    esito["controlli_approvati"] = approvati
    esito["guasti"] = guasti
    # ⛔ Anche un verdetto ha un denominatore (§1.9, sesta regola): se non ha
    #    giudicato niente, non da' nessun esito.
    if approvati == 0:
        esito["verdetto"] = "NESSUN-CONTROLLO"
        return esito, 2
    esito["verdetto"] = "CONFORME" if guasti == 0 else "NON-CONFORME"
    return esito, (0 if guasti == 0 else 1)


def stampa_passi(esito):
    print(f"    -- registro del server: {esito['righe_nel_registro']} righe, "
          f"il segmento di questo motore ne ha {esito.get('righe_nel_segmento', '—')}")
    print(f"    -- marcatori: inizio ×{esito['marca_inizio_trovata']}, "
          f"fine ×{esito['marca_fine_trovata']}")
    for nome, voce in (esito.get("passi") or {}).items():
        if voce["ok"] is None:
            segno = "  "
        else:
            segno = f"{VERDE}OK{GRIGIO}" if voce["ok"] else f"{ROSSO}NO{GRIGIO}"
        extra = ""
        if "ms" in voce:
            extra = f"  ms={voce['ms']}"
        elif "valori" in voce:
            extra = f"  valori={voce['valori']}"
        print(f"    {segno}  {nome:<20} trovate={voce['trovate']:<3} "
              f"atteso={voce['atteso']}{extra}")
    c = esito.get("congedo") or {}
    print(f"    --  congedo: sul canale {c.get('sul_canale_di_controllo')}, "
          f"nel codice di chiusura {c.get('nel_codice_di_chiusura')} "
          f"⇒ strada «{c.get('strada')}»")
    print(f"    --  posto, «occupati adesso» finale: {esito.get('posto_finale_occupati')}")
    print(f"    --  controlli approvati: {esito.get('controlli_approvati')}, "
          f"guasti: {esito.get('guasti')}")


# ===========================================================================
def principale():
    p = argparse.ArgumentParser(add_help=True)
    sub = p.add_subparsers(dest="comando", required=True)

    a = sub.add_parser("aggiungi"); a.add_argument("json")
    sub.add_parser("righe")
    for nome in ("elenco", "battuta"):
        s = sub.add_parser(nome)
        s.add_argument("--giro", required=True)
        s.add_argument("--da", type=int, default=0)
    c = sub.add_parser("cerca")
    c.add_argument("--giro", required=True)
    c.add_argument("--da", type=int, default=0)
    c.add_argument("--tipo", required=True)
    q = sub.add_parser("passi")
    q.add_argument("--log", required=True)
    q.add_argument("--marca-inizio", required=True)
    q.add_argument("--marca-fine", required=True)
    q.add_argument("--atteso", default="sessione")
    q.add_argument("--utente", default="prova")
    q.add_argument("--registra", default=None,
                   help="json di contorno da unire alla riga scritta nel registro")
    a2 = p.parse_args()

    if a2.comando == "aggiungi":
        return aggiungi(a2.json)

    if a2.comando == "righe":
        righe, guasto = leggi()
        if guasto:
            print(guasto, file=sys.stderr)
            print(0)
            return 3
        print(len(righe))
        return 0

    if a2.comando == "elenco":
        trovata, stato, quante = cerca(a2.giro, a2.da, "ELENCO")
        if stato:
            print(f"⛔ nessun ELENCO per il giro «{a2.giro}» dopo la riga {a2.da} "
                  f"(righe guardate: {quante})", file=sys.stderr)
            return stato
        n, d = trovata
        for i, voce in enumerate(d.get("elenco") or []):
            print(i, voce.get("xdo"), int(bool(voce.get("verdetto"))),
                  int(bool(voce.get("distruttiva"))), voce.get("che", ""), sep="\t")
        return 0

    # ⛔ E QUANDO NON C'E', NON SI STAMPA NIENTE SU STANDARD OUTPUT.
    #
    #    Difetto trovato dal primo giro di certificazione, 11 agosto 2026.
    #    Qui c'era `print("NIENTE")`, e `cerca` stampava `NIENTE\t(righe
    #    guardate: N)`: chi legge con `$(...)` riceveva una **stringa non
    #    vuota** per dire «non c'e'», e il `[ -n "$fuoco" ]` del pilota era vero
    #    **sempre**.  ⛔ Risultato: 26 combinazioni su 26 dichiarate «consegnata
    #    E riservata» — un verdetto uniforme, prodotto da uno strumento che
    #    diceva «qualcosa» ogni volta che non aveva trovato niente.
    #
    # ⭐ Ed e' `LEZIONI.md` §1.9 nella sua forma piu' nuda: «vuoto» e «trovato»
    #    con lo stesso aspetto, stavolta dentro un attrezzo scritto per non
    #    farlo succedere.  La diagnostica va su standard error, dove non
    #    inquina il valore; lo stato d'uscita resta l'unico canale del «c'e'».
    if a2.comando == "battuta":
        trovata, stato, quante = cerca(a2.giro, a2.da, "BATTUTA")
        if stato == 3:
            return 3
        if stato:
            print(f"nessuna BATTUTA dopo la riga {a2.da} "
                  f"(righe guardate: {quante})", file=sys.stderr)
            return 1
        n, d = trovata
        mods = "".join(x for x, v in (("ctrl", d.get("ctrl")), ("alt", d.get("alt")),
                                      ("shift", d.get("shift")), ("meta", d.get("meta")))
                       if v)
        print(n, d.get("key"), d.get("code"), mods or "-", d.get("cancelable"), sep="\t")
        return 0

    if a2.comando == "cerca":
        trovata, stato, quante = cerca(a2.giro, a2.da, a2.tipo)
        if stato == 3:
            return 3
        if stato:
            print(f"nessun «{a2.tipo}» dopo la riga {a2.da} "
                  f"(righe guardate: {quante})", file=sys.stderr)
            return 1
        n, d = trovata
        print(n, json.dumps(d, ensure_ascii=False)[:400], sep="\t")
        return 0

    if a2.comando == "passi":
        esito, stato = passi(a2.log, a2.marca_inizio, a2.marca_fine,
                             a2.atteso, a2.utente)
        if esito is not None:
            stampa_passi(esito)
            contorno = {}
            if a2.registra:
                try:
                    contorno = json.loads(a2.registra)
                except Exception:
                    contorno = {"contorno_non_json": a2.registra}
            contorno.update({"tipo": "PASSI", "esito": esito})
            aggiungi(json.dumps(contorno, ensure_ascii=False))
        return stato
    return 3


if __name__ == "__main__":
    sys.exit(principale())
