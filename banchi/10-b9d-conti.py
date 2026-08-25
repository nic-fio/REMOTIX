#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b9d-conti — il registro del server letto IN UNA PASSATA, per il DIRUPO.

⛔ NON rifa' `10-b92-conti.py`: quello conta i byte sul filo, i posti negati e
   la spirale delle chiavi.  Questo conta le SEI grandezze che servono a dire
   **che cosa si rompe** fra la sesta sessione e l'ottava, e nessuna delle sei
   sta li' dentro:

   1. ⛔⛔ `RIPIEGO DICHIARATO` — quante volte un figlio e' sceso in software
      (`figlio.c:4470`).  ⚠ E' la `[?]` numero 11 di §3.6: se al gradino del
      dirupo qualcuno codifica con `libx264`, il quadro somiglia a questo per
      una ragione che non c'entra col numero di sessioni.
   2. ⭐⭐ `ritmo di <prov>: arretrato LETTO N volte in quest'ultimo secondo`
      (`webtransport.c:4480`) — ed e' la riga PIU' PREZIOSA del registro per
      questa domanda, perche' e' **per sessione** e dice quanti fotogrammi il
      PALCO ha consegnato al padre in quel secondo.  ⇒ Distingue «il padre non
      spedisce» da «al padre non arriva piu' niente», che e' esattamente il
      bivio del dirupo.  ⚠ Esce solo col regolatore acceso.
   3. il ritmo `SCENDE` / `RISALE`, per sessione (`webtransport.c:4419`, `:4445`).
   4. la coda del video `SOPRA` / `SOTTO` la soglia, e gli abbandoni
      (`webtransport.c:3794`, `:3808`) — la cura `--sgombra-soglia-ms`.
   5. le righe `ciclo:` dei figli (`figlio.c:7343`): fotogrammi consegnati,
      **attese a vuoto** e guasti.  ⛔⛔ Quelle righe NON dicono di chi sono
      (rilievo R10-A4), e qui si fa l'unica cosa onesta: si ricostruiscono le
      serie per INSEGUIMENTO (i contatori sono monotoni e per processo), e ⛔ se
      il numero di serie trovate non e' quello atteso si torna `None` invece di
      un numero plausibile.
   6. `NON potra' essere abbandonato` — l'elenco dei fotogrammi in volo pieno.

⛔ `None` non e' zero, ovunque.  Una grandezza che non si e' potuta leggere
   porta `"esito"`, non uno zero.

uso:  10-b9d-conti.py <registro> <byte0> <byte1> [figli_attesi]
"""
import json
import re
import sys

percorso = sys.argv[1]
r0, r1 = int(sys.argv[2]), int(sys.argv[3])
FIGLI_ATTESI = int(sys.argv[4]) if len(sys.argv) > 4 else 0

RIPIEGO = "RIPIEGO DICHIARATO"
# ⛔ Il nome del componente che NON si e' aperto e quello su cui si e' sceso:
#    senza, la riga dice «e' successo» e non dice **a chi**.
RE_RIPIEGO = re.compile(r"RIPIEGO DICHIARATO: «([^»]+)» su (\S+) non si e' "
                        r"aperto .* si scende su «([^»]+)»")
# ⛔⛔ E «RIPIEGO DICHIARATO» NON E' UNO SOLO: la stessa marca apre anche la riga
#     della tabella delle tele dei palchi (`webtransport.c:5264`, il `WT_PALCHI
#     8` che morde al NONO utente).  ⚠ Un rivelatore che contasse `in riga` e
#     basta direbbe «una sessione codifica in software» ogni volta che il nono
#     utente arriva — un numero plausibile per un fatto che non e' successo.
#     ⇒ Si distinguono per il seguito della riga, e si contano a parte.
PALCHI_PIENA = "la tabella delle tele dei palchi"
# ⭐⭐ La riga che dice, PER SESSIONE, ogni quanto si potra' chiedere una CHIAVE:
#     e' `chiave_byte · rtt / cwnd · 1,2` limitata fra 150 e 2000 ms
#     (`webtransport.c:4037`).  ⛔ Se il regolatore del ritmo blocca tutti i
#     delta, e' QUESTO numero a fissare i fotogrammi al secondo, e allora
#     l'aggregato e' costante per costruzione.  ⚠ Ma il primo giro ha misurato
#     ZERO chiavi su 8 741 fotogrammi: se questa riga dice 660 ms e le chiavi
#     restano zero, quella spiegazione cade — ed e' il genere di refutazione che
#     vale quanto una scoperta.
RE_CHIAVE_OGNI = re.compile(r"(\S+): la CHIAVE si potra' richiedere ogni "
                            r"(\d+) ms invece di (\d+)")
# ⭐ La sentinella: N chiamate SINCRONE a logind dentro il ciclo che consegna i
#    fotogrammi (`main.c:1752`, `sentinella.c:29` ATTESA_MS 300).
RE_LOGIND = re.compile(r"logind ha impiegato (\d+) ms")
LOGIND_MUTO = "logind non ha risposto entro"
SPEDITO = " SPEDITO:"
# ⭐⭐⭐ I BUFFER DI PIPEWIRE — e sono la grandezza su cui l'ipotesi migliore del
#     dirupo si gioca.  `cattura.c:586` ne chiede **6** sulla strada della
#     scheda (minimo 4, massimo 8), e noi ne TRATTENIAMO al massimo due —
#     «uno fermo nel posto e uno in mano a chi legge» — finche' `vaSyncSurface`
#     (`codificatore.c:3335`) non torna.  ⇒ Se un fotogramma resta in mano
#     nostra piu' a lungo di (buffer liberi × periodo del fotogramma), il
#     compositore resta senza buffer da riempire e SMETTE DI COMPORRE: senza
#     composizione non arriva niente da codificare, e l'anello si morde la coda.
#     ⛔ E' una SOGLIA su una grandezza continua, non un numero di sessioni.
# ⚠ La riga esce una volta ogni 300 fotogrammi ARRIVATI (`cattura.c:1258`, ed e'
#   `registro_dettaglio`: serve `--parlantina`).  A 38 fot/s e' una ogni 8 s; al
#   gradino del dirupo, a 1,5 fot/s, sarebbe una ogni 200 s ⇒ **la sua assenza
#   al gradino del dirupo e' attesa, e non e' una lettura mancata**: si dichiara.
RE_BUFFER = re.compile(r"su (\d+) fotogrammi: (\d+) buffer distinti, danno "
                       r"pieno (\d+) parziale (\d+) assente (\d+)")
RE_SOSTITUITI = re.compile(r"sostituiti nel posto (\d+)")
RE_RITMO = re.compile(r"ritmo di (\S+): arretrato LETTO (\d+) volte in "
                      r"quest'ultimo secondo, massimo (\d+), ultimo (\d+), "
                      r"posti (\d+) — (\d+) fotogrammi non partiti in questo "
                      r"secondo, (\d+) in tutto")
RE_SCENDE = re.compile(r"(\S+): il ritmo SCENDE — arretrato (\d+) delta contro "
                       r"(\d+) posti, (\d+) byte fermi")
RE_RISALE = re.compile(r"(\S+): il ritmo RISALE — l'episodio e' durato (\d+) ms")
RE_SOPRA = re.compile(r"(\S+): la coda del video passa SOPRA la soglia "
                      r"\((\d+) byte = (\d+) ms, soglia (\d+) ms")
RE_SOTTO = re.compile(r"(\S+): la coda del video torna SOTTO la soglia")
RE_CICLO = re.compile(r"ciclo: (\d+) fotogrammi consegnati \((\d+) chiavi\), "
                      r"(\d+) attese a vuoto .*?, (\d+) guasti — codec (\d+), "
                      r"(\d+)/s chiesti, attesa ([0-9.]+) s")
ABBANDONO = "ABBANDONATO NELLA CODA"
INVOLO_PIENO = "NON potra' essere abbandonato"

# ⭐⭐ IL TRATTO — la riga che dice DOVE se ne va il tempo di un fotogramma
#     dentro il figlio (`figlio.c:4748`, `registro_dice`, una al secondo per
#     figlio).  ⛔ E' la sola misura che distingue le tre spiegazioni del
#     dirupo, perche' le tre attese stanno in tre voci DIVERSE:
#       · `nel posto`   — il fotogramma e' invecchiato aspettando che il ciclo
#                         tornasse a prenderlo ⇒ il CONSUMATORE e' lento;
#       · `conversione` — dentro c'e' il `vaSyncSurface` del VPP, cioe' l'attesa
#                         BLOCCANTE sul motore RENDER (`codificatore.c:3335`);
#       · `spedizione`  — il `send()` BLOCCANTE verso il padre
#                         (`figlio.c:2741`) ⇒ contropressione del padre.
#     ⚠ La riga non dice di quale figlio e': si riferiscono la mediana, il minimo
#       e il massimo SU TUTTE le righe della finestra, e si dichiara.
RE_TRATTO = re.compile(r"TRATTO cattura → byte fuori: mediana ([0-9.]+) ms "
                       r"\(max ([0-9.]+)\)")
RE_VOCE = re.compile(r"(produttore|allocazione|copia|nel posto|misura|"
                     r"conversione|caricamento|codifica|spedizione|resto) "
                     r"([0-9.]+) \(max ([0-9.]+)\)")
# ⛔ Le riaperture del contesto VA-API costano `[M]` 91-108 ms l'una
#    (`codificatore.c:3787`): tre su un fotogramma sono trecento millisecondi, ed
#    e' un moltiplicatore A GRADINO.  Si contano tutte e tre le strade.
RICODIFICA = "si RICODIFICA a qualita' inferiore"
QUALITA_SU = "QUALITA' SU"
RIAPERTO = "riaperto dopo lo scarico"
SUPERFICI = "nessuna superficie libera nel magazzino"
TRATTENUTO = "ha trattenuto il fotogramma invece di consegnarlo"

ripieghi = []
ritmo = {}          # provenienza → lista di letture al secondo
scende = {}
risale = {}
sopra = {}
sotto = {}
cicli = []          # (fotogrammi, chiavi, zero, guasti, fps_chiesti)
abbandoni = 0
involo_pieno = 0
righe = 0
tratti = []         # mediana totale per riga
voci = {}           # nome della voce → lista delle mediane
altri = {"ricodifica": 0, "qualita_su": 0, "riaperto": 0,
         "superfici_finite": 0, "trattenuto": 0, "palchi_pieni": 0,
         "spediti": 0}
chiave_ogni = {}
logind_ms = []
logind_muto = 0
buffer_righe = []

try:
    with open(percorso, "rb") as f:
        f.seek(r0)
        tratto = f.read(max(0, r1 - r0))
except FileNotFoundError:
    print(json.dumps({"esito": "⛔ NON HO LETTO — il registro «%s» non c'e'"
                               % percorso}))
    sys.exit(0)

for riga in tratto.decode("utf-8", "replace").splitlines():
    righe += 1
    if RIPIEGO in riga:
        m = RE_RIPIEGO.search(riga)
        if m:
            ripieghi.append({"chiesto": m.group(1), "nodo": m.group(2),
                             "ripiego": m.group(3)})
        elif PALCHI_PIENA in riga:
            altri["palchi_pieni"] += 1      # ⛔ un ALTRO fatto, sotto la stessa marca
        else:
            ripieghi.append({"⚠ riga con la marca ma non la forma":
                             riga.strip()[-200:]})
        continue
    if "la CHIAVE si potra' richiedere ogni" in riga:
        m = RE_CHIAVE_OGNI.search(riga)
        if m:
            chiave_ogni.setdefault(m.group(1), []).append(int(m.group(2)))
        continue
    if "logind ha impiegato" in riga:
        m = RE_LOGIND.search(riga)
        if m:
            logind_ms.append(int(m.group(1)))
        continue
    if LOGIND_MUTO in riga:
        logind_muto += 1
        continue
    if SPEDITO in riga:
        altri["spediti"] += 1
        continue
    if "buffer distinti, danno" in riga:
        m = RE_BUFFER.search(riga)
        if m:
            s2 = RE_SOSTITUITI.search(riga)
            buffer_righe.append({"arrivati": int(m.group(1)),
                                 "buffer_distinti": int(m.group(2)),
                                 "danno_pieno": int(m.group(3)),
                                 "danno_parziale": int(m.group(4)),
                                 "danno_assente": int(m.group(5)),
                                 "sostituiti_nel_posto":
                                     int(s2.group(1)) if s2 else None})
        continue
    if "ritmo di " in riga:
        m = RE_RITMO.search(riga)
        if m:
            d = ritmo.setdefault(m.group(1), {"letture": [], "non_partiti": []})
            d["letture"].append(int(m.group(2)))
            d["non_partiti"].append(int(m.group(6)))
        continue
    if "il ritmo SCENDE" in riga:
        m = RE_SCENDE.search(riga)
        if m:
            scende[m.group(1)] = scende.get(m.group(1), 0) + 1
        continue
    if "il ritmo RISALE" in riga:
        m = RE_RISALE.search(riga)
        if m:
            risale[m.group(1)] = risale.get(m.group(1), 0) + 1
        continue
    if "passa SOPRA la soglia" in riga:
        m = RE_SOPRA.search(riga)
        if m:
            sopra[m.group(1)] = sopra.get(m.group(1), 0) + 1
        continue
    if "torna SOTTO la soglia" in riga:
        m = RE_SOTTO.search(riga)
        if m:
            sotto[m.group(1)] = sotto.get(m.group(1), 0) + 1
        continue
    if "ciclo: " in riga:
        m = RE_CICLO.search(riga)
        if m:
            cicli.append(tuple(int(x) for x in m.groups()[:6]))
        continue
    if "TRATTO cattura" in riga:
        m = RE_TRATTO.search(riga)
        if m:
            tratti.append(float(m.group(1)))
            for v in RE_VOCE.finditer(riga):
                voci.setdefault(v.group(1), []).append(float(v.group(2)))
        continue
    if ABBANDONO in riga:
        abbandoni += 1
        continue
    if INVOLO_PIENO in riga:
        involo_pieno += 1
        continue
    if RICODIFICA in riga:
        altri["ricodifica"] += 1
    elif QUALITA_SU in riga:
        altri["qualita_su"] += 1
    elif RIAPERTO in riga:
        altri["riaperto"] += 1
    elif SUPERFICI in riga:
        altri["superfici_finite"] += 1
    elif TRATTENUTO in riga:
        altri["trattenuto"] += 1

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LE SERIE DEI FIGLI, PER INSEGUIMENTO — e il rifiuto quando non torna
# ═══════════════════════════════════════════════════════════════════════════
#
# Le righe `ciclo:` non portano il nome del figlio (`figlio.c:7343`, rilievo
# R10-A4): con otto figli che appendono allo stesso file, otto serie si
# mescolano.  ⭐ Ma ogni serie e' MONOTONA e per processo, e in una finestra di
# quaranta secondi due figli hanno quasi sempre contatori diversi.
#
# ⇒ Si insegue: ogni riga si attacca alla serie il cui ultimo valore e' <= il
#   nuovo su TUTTE le componenti, scegliendo la piu' vicina.  Chi non si attacca
#   a nessuna apre una serie nuova.
#
# ⛔ E POI SI CONTROLLA: se le serie non sono quante i figli attesi, il numero
#    NON si dichiara.  ⚠ Un inseguimento che sbaglia da' un numero plausibile,
#    ed e' esattamente la forma che questo progetto ha pagato due volte.
def insegui(righe_ciclo, quanti):
    """⛔ E LE SERIE SI SEMINANO, non si aprono strada facendo.

    ⚠ La prima stesura apriva una serie nuova ogni volta che una riga non si
      attaccava a nessuna, e **si e' vista dare rosso in `--certifica`**: i
      contatori di un figlio piu' avanti DOMINANO quelli di un figlio piu'
      indietro (2 000 > 1 000 su tutte le componenti), quindi la seconda riga
      si attaccava alla prima e otto figli diventavano una serie sola.
      ⛔ Non dava un errore: dava **una serie** e un numero plausibile.

    ⭐ La cura usa quel che si sa: i figli sono `quanti`, e ciascuno scrive una
       riga al secondo ⇒ le prime `quanti` righe sono una per figlio.  Si
       seminano quelle, e da li' in poi ogni riga si attacca alla serie che
       cresce di MENO — e ⛔ non si aprono serie nuove: una riga che non si
       attacca a nessuna e' un'ORFANA, e le orfane fanno rifiutare il conto.
    """
    if quanti <= 0 or len(righe_ciclo) < quanti:
        return None, len(righe_ciclo)
    serie = [[v] for v in righe_ciclo[:quanti]]
    orfane = 0
    for v in righe_ciclo[quanti:]:
        migliore, distanza = None, None
        for s in serie:
            u = s[-1]
            if all(v[k] >= u[k] for k in range(4)):
                d = sum(v[k] - u[k] for k in range(4))
                if distanza is None or d < distanza:
                    migliore, distanza = s, d
        if migliore is None:
            orfane += 1
        else:
            migliore.append(v)
    return serie, orfane


cattura = {"esito": "⛔ NON HO LETTO — meno di due righe «ciclo:» nella finestra"}
if len(cicli) >= 2 and FIGLI_ATTESI:
    serie, orfane = insegui(cicli, FIGLI_ATTESI)
    utili = [s for s in serie if len(s) >= 2] if serie else []
    lunghe = sorted(len(s) for s in serie) if serie else []
    mediana_l = lunghe[len(lunghe) // 2] if lunghe else 0
    if serie is None:
        cattura = {"esito": "⛔ NON DICHIARO — %d righe «ciclo:» per %d figli: "
                            "meno di una a testa, non c'e' da cosa seminare"
                            % (len(cicli), FIGLI_ATTESI),
                   "righe_ciclo": len(cicli)}
    elif orfane:
        cattura = {"esito": "⛔ NON DICHIARO — %d righe «ciclo:» non si "
                            "attaccano a nessuna delle %d serie: o un figlio e' "
                            "nato dentro la finestra, o l'inseguimento non "
                            "torna.  ⚠ Un numero plausibile qui sarebbe peggio "
                            "di un buco" % (orfane, FIGLI_ATTESI),
                   "orfane": orfane, "righe_ciclo": len(cicli)}
    elif mediana_l and lunghe[0] * 2 < mediana_l:
        cattura = {"esito": "⛔ NON DICHIARO — le serie sono sbilanciate (la "
                            "piu' corta ha %d righe, la mediana %d): due righe "
                            "dello stesso figlio sono finite fra i semi"
                            % (lunghe[0], mediana_l),
                   "lunghezze": lunghe, "righe_ciclo": len(cicli)}
    elif len(utili) != FIGLI_ATTESI:
        cattura = {"esito": "⛔ NON DICHIARO — solo %d serie su %d hanno almeno "
                            "due righe: qualche figlio non ha scritto, o due "
                            "righe dello stesso sono finite fra i semi"
                            % (len(utili), FIGLI_ATTESI),
                   "lunghezze": lunghe, "righe_ciclo": len(cicli)}
    elif not utili:
        cattura = {"esito": "⛔ NON HO LETTO — nessuna serie «ciclo:» con due "
                            "righe"}
    else:
        fot = sum(s[-1][0] - s[0][0] for s in utili)
        chi = sum(s[-1][1] - s[0][1] for s in utili)
        zer = sum(s[-1][2] - s[0][2] for s in utili)
        gua = sum(s[-1][3] - s[0][3] for s in utili)
        cattura = {"serie": len(serie), "serie_usate": len(utili),
                   "righe_ciclo": len(cicli),
                   "fotogrammi_catturati": fot, "chiavi": chi,
                   "attese_a_vuoto": zer, "guasti": gua,
                   "fps_chiesti": cicli[0][5],
                   "per_serie": [{"righe": len(s),
                                  "fotogrammi": s[-1][0] - s[0][0],
                                  "attese_a_vuoto": s[-1][2] - s[0][2],
                                  "guasti": s[-1][3] - s[0][3]}
                                 for s in utili]}

per_prov = {}
for p, d in ritmo.items():
    l = d["letture"]
    per_prov[p] = {
        "secondi_di_riga": len(l),
        "consegne_al_secondo_mediana": sorted(l)[len(l) // 2],
        "consegne_al_secondo_min": min(l), "consegne_al_secondo_max": max(l),
        "secondi_a_zero_consegne": sum(1 for x in l if x == 0),
        "non_partiti_in_tutto": sum(d["non_partiti"]),
        "scende": scende.get(p, 0), "risale": risale.get(p, 0),
        "sopra_soglia": sopra.get(p, 0), "sotto_soglia": sotto.get(p, 0),
        "chiave_ogni_ms": (sorted(chiave_ogni[p])[len(chiave_ogni[p]) // 2]
                           if p in chiave_ogni else None)}
for p, v in chiave_ogni.items():
    if p not in per_prov:
        per_prov[p] = {"esito": "⚠ solo la riga della CHIAVE, nessuna riga "
                                "«ritmo di»: il regolatore e' spento?",
                       "chiave_ogni_ms": sorted(v)[len(v) // 2]}

def _riassunto(v):
    if not v:
        return None
    s = sorted(v)
    return {"righe": len(s), "mediana_ms": s[len(s) // 2],
            "min_ms": s[0], "max_ms": s[-1]}


tratto = {"esito": "⛔ NON HO LETTO — nessuna riga «TRATTO cattura» nella "
                   "finestra.  ⚠ E l'ASSENZA e' un dato: quella riga si scrive "
                   "dopo ogni spedizione riuscita, una al secondo per figlio "
                   "(figlio.c:4748) — se manca, o non si spedisce piu' niente o "
                   "il ciclo del figlio e' fermo dentro una chiamata"}
if tratti:
    tratto = {"righe": len(tratti), "totale": _riassunto(tratti),
              "voci": dict((k, _riassunto(v)) for k, v in voci.items()),
              "avvertenza": "⚠ le righe «TRATTO» non dicono di quale figlio "
                            "sono (figlio.c:4748): mediana, minimo e massimo "
                            "sono SU TUTTE le righe della finestra"}

print(json.dumps({
    "esito": "letto", "byte0": r0, "byte1": r1, "righe_lette": righe,
    "tratto_dei_figli": tratto, "altri_conti": altri,
    "buffer_di_pipewire": (
        {"righe": len(buffer_righe),
         "buffer_distinti": sorted(set(d["buffer_distinti"]
                                       for d in buffer_righe)),
         "arrivati_min": min(d["arrivati"] for d in buffer_righe),
         "arrivati_max": max(d["arrivati"] for d in buffer_righe),
         "sostituiti_nel_posto": [d["sostituiti_nel_posto"]
                                  for d in buffer_righe][-3:],
         "nota": "⭐ «buffer distinti» e' quanti ne ricicla DAVVERO il "
                 "compositore: cattura.c:586 ne chiede 6 (min 4, max 8) e il "
                 "produttore risponde quel che puo'"}
        if buffer_righe else
        {"esito": "⛔ NON HO LETTO — nessuna riga «buffer distinti» nella "
                  "finestra.  ⚠ Esce una ogni 300 fotogrammi ARRIVATI "
                  "(cattura.c:1258): a 1,5 fot/s sarebbe una ogni 200 s, "
                  "quindi al gradino del dirupo la sua assenza e' ATTESA e "
                  "non e' una lettura mancata"}),
    "logind": ({"chiamate_lente": len(logind_ms),
                "ms_mediano": sorted(logind_ms)[len(logind_ms) // 2],
                "ms_massimo": max(logind_ms), "in_timeout": logind_muto}
               if logind_ms else
               {"chiamate_lente": 0, "in_timeout": logind_muto,
                "nota": "⭐ nessuna riga «logind ha impiegato»: sotto i 20 ms "
                        "di LENTA_MS (sentinella.c:32) non se ne scrive "
                        "nessuna ⇒ la sentinella NON e' dentro al ciclo per "
                        "centinaia di ms"}),
    "ripieghi_software": ripieghi, "quanti_ripieghi": len(ripieghi),
    "per_provenienza": per_prov,
    "ritmo_scende_in_tutto": sum(scende.values()),
    "ritmo_risale_in_tutto": sum(risale.values()),
    "sopra_soglia_in_tutto": sum(sopra.values()),
    "sotto_soglia_in_tutto": sum(sotto.values()),
    "abbandoni_in_coda": abbandoni, "involo_pieno": involo_pieno,
    "cattura_dei_figli": cattura}, ensure_ascii=False))
