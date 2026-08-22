#!/usr/bin/env python3
"""06-b37-guasti.py — ⛔⛔⭐ I GUASTI DELLA SOTTOFASE 6.5, INNESTATI IN UNA COPIA.

    python3 banchi/06-b37-guasti.py --elenco
    python3 banchi/06-b37-guasti.py src/pagina.html /tmp/pagina-G1.html G1
    python3 banchi/06-b37-guasti.py --ancore src/pagina.html

═══════════════════════════════════════════════════════════════════════════
⛔⛔ PERCHE' ESISTE, e la data conta: **22 agosto 2026**.

`06-b37` e' stato **l'unico dei sei banchi della fase 6 senza NESSUN guasto
innestato** (`fasi/06` §5.5).  Il meccanismo c'era — `06-b37-lancia.sh` legge
`SORGENTE=` — e non lo usava nessuno script.  ⇒ **Nessuno dei suoi verdi era mai
stato messo alla prova**, e la revisione avversariale del 21 agosto ne ha trovati
**quattro falsi**, ciascuno sufficiente da solo a togliere il pavimento.

⭐ *«Un banco che non sa diventare rosso non e' un banco»*: qui c'e' un guasto
per **ciascuno** dei quattro falsi verdi, piu' uno che serve a chiudere una `[?]`.
Ogni guasto dichiara **prima** quale scena deve accusarlo e con quale frase.

┌────┬────────────────────────────────────────────┬──────────────────────────┐
│ G1 │ la tela chiesta e' 30 px piu' STRETTA della│ `numeri` A5/A6 ·         │
│    │ finestra ⇒ banda nera permanente           │ `sfora` · `pixel`        │
│ G2 │ la guardia della voce spenta e' aggirata   │ `voce` V5                │
│ G3 │ `misura_vista()` torna al `Math.round` di  │ `numeri` A2/A6           │
│    │ prima della cura (il difetto VERO del 16   │ a FATTORE=1.5            │
│    │ agosto) ⇒ tela piu' larga della finestra   │                          │
│ G4 │ l'immagine e' dipinta 50 px fuori posto    │ `coordinate` C0          │
│    │ dentro il buffer, e la pagina non lo sa    │                          │
│ G5 │ la tela puo' uscire con un lato DISPARI    │ `numeri` A3              │
└────┴────────────────────────────────────────────┴──────────────────────────┘

⛔ LE REGOLE DI QUESTO FILE, e sono le stesse che hanno salvato `04-b31`:

  1. **l'ancora e' una riga intera, e deve comparire ESATTAMENTE UNA VOLTA.**
     Zero volte o due volte ⇒ si esce con errore e NON si scrive niente.
     ⚠ E' la forma d'errore che il progetto ha gia' pagato: l'ancora di G8 in
     `04-b31` era scaduta da cinque giorni, il piu' grave dei dodici guasti non
     si innestava piu', e il certificatore stampava `??` che non leggeva nessuno;
  2. ⛔ **il prodotto non si tocca**: si scrive una COPIA, e chi la usa la passa
     al banco con `SORGENTE=`;
  3. ⛔ **ogni guasto dichiara la scena e la frase che deve accendere**, prima di
     girare.  Un guasto che facesse diventare rosso *qualcosa* non proverebbe
     niente: `06-b33` e' caduto proprio li' (un giro fallito confermava OGNI
     guasto perche' il confronto era un'appartenenza).
"""
import sys

# ---------------------------------------------------------------------------
# ⛔ Ogni guasto: nome · che cosa rompe · la scena che DEVE accusarlo · la frase
#    che deve comparire · le sostituzioni (ancora → guasto), riga intera.
GUASTI = {

    # ═══════════════════════════════════════════════════════════════════════
    "G1": {
        "che_cosa":
            "la tela chiesta e' 30 px piu' STRETTA della finestra: banda nera "
            "permanente su tutta l'altezza, 30 colonne di desktop che l'utente "
            "non vede mai",
        "falso_verde":
            "nessuna scena aveva un limite INFERIORE sulla tela: tutte le "
            "verifiche erano unilaterali (tela > vista, tela > finestra), e "
            "questa tela lasciava 12 combinazioni su 12 VERDI",
        "casi": [
            ("numeri", "", "NO  A5:"),
            ("sfora", "", "PIU' STRETTA della finestra"),
            ("pixel", "", "BANDA NERA PERMANENTE"),
        ],
        "cambi": [(
            "  return [p(v[0], TELA_L_MINIMA, TELA_L_MASSIMA),",
            "  return [p(v[0] - 30, TELA_L_MINIMA, TELA_L_MASSIMA),  /* GUASTO G1 */",
        )],
    },

    # ═══════════════════════════════════════════════════════════════════════
    "G2": {
        "che_cosa":
            "la guardia della VOCE SPENTA e' aggirata: dopo un "
            "`TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` la pagina continua a "
            "mandare `ADATTA_TELA` a un compositore che ha gia' detto di non "
            "saperlo fare (`RCP.md` §7.1 lo vieta)",
        "falso_verde":
            "`06-b37-voce.py` e `06-b37-modi.py` SOSTITUIVANO `chiedi_tela` con "
            "una spia prima di misurare, e la guardia sta DENTRO la funzione "
            "sostituita: il banco provava che un booleano cambia valore",
        "casi": [
            ("voce", "", "la guardia di §7.1 NON tiene"),
        ],
        "cambi": [(
            "        if (tela_spenta) {",
            "        if (false && tela_spenta) {  /* GUASTO G2 */",
        )],
    },

    # ═══════════════════════════════════════════════════════════════════════
    "G3": {
        "che_cosa":
            "`misura_vista()` torna al `Math.round` di prima della cura del 16 "
            "agosto 2026 ⇒ a `devicePixelRatio` non intero la pagina dichiara "
            "una vista di un pixel PIU' GRANDE di quella che esiste, chiede "
            "una tela che non ci sta, e da li' vengono la barra di scorrimento, "
            "la scala 0,9651 e il testo interpolato che l'utente ha giudicato",
        "falso_verde":
            "la «domanda vera» (A6) era un'identita' algebrica: la «verita' "
            "esterna» era `xwininfo − BORDO − barra` con `BORDO` calibrato "
            "sulle stesse righe, e si semplificava in `round(cw·dpr)` — cioe' "
            "nello STESSO arrotondamento che il guasto introduce.  ⇒ Il difetto "
            "VERO che questa fase ha curato passava sotto A6 senza toccarlo",
        # ⛔ Si certifica sui PIXEL e non sull'aritmetica di `numeri`, e la
        #    ragione e' misurata: a `dpr 1,5` la scena `numeri` e' rossa anche
        #    sul prodotto SANO (Chrome impagina una riga piu' di quanto dipinga),
        #    quindi li' il rosso c'e' gia' senza il guasto.  ⭐ Sui pixel il sano
        #    e' verde e il guasto si vede: «TAGLIATO 979 px su 980».
        "casi": [
            ("sfora", "1.5", "TAGLIATO"),
        ],
        "cambi": [(
            "  return [Math.max(1, Math.floor(l * r)), Math.max(1, Math.floor(a * r))];",
            "  return [Math.max(1, Math.round(l * r)), Math.max(1, Math.round(a * r))];  /* GUASTO G3 */",
        )],
    },

    # ═══════════════════════════════════════════════════════════════════════
    "G4": {
        "che_cosa":
            "l'immagine e' dipinta 50 pixel FUORI POSTO dentro il buffer della "
            "tela, e la pagina non lo sa: `dipinta.x` continua a dire 0.  ⇒ Ogni "
            "clic finisce 50 px a fianco di dove l'utente ha puntato.  ⚠ E' la "
            "famiglia del difetto del DeX, quello che ha reso il mouse "
            "inutilizzabile per due giorni: una geometria data per scontata",
        "falso_verde":
            "`06-b37-coordinate.py` definiva l'origine come lo scostamento fra "
            "dove l'immagine STA e dove la pagina CREDE che stia, e poi la "
            "sottraeva: il termine si semplificava e restava un'algebra fra "
            "`getBoundingClientRect()` e la conversione della pagina.  ⇒ Scarto "
            "0 su 20 punti su due motori, con l'immagine spostata",
        "casi": [
            ("coordinate", "", "L'IMMAGINE NON STA DOVE LA PAGINA CREDE"),
        ],
        "cambi": [
            (
                "      this.mostrata = n;",
                "      this.mostrata = n;\n"
                "      /* ⛔ GUASTO G4: il buffer nasce 100 px piu' largo e "
                "l'immagine ci sta\n"
                "         dentro a x=50, ma `dipinta.x` resta 0 — cioe' la "
                "pagina crede che\n"
                "         l'immagine cominci dove comincia il buffer. */\n"
                "      const __g4_fl = fl;\n"
                "      const __g4_oc = new OffscreenCanvas(fl + 100, fa);\n"
                "      __g4_oc.getContext(\"2d\").drawImage(bmp, 50, 0);\n"
                "      bmp = __g4_oc.transferToImageBitmap();\n"
                "      fl = fl + 100;",
            ),
            (
                "      this.dipinta = { l: fl, a: fa, x: 0, y: 0,",
                "      this.dipinta = { l: __g4_fl, a: fa, x: 0, y: 0,  "
                "/* GUASTO G4 */",
            ),
            (
                "                       fotogramma: [fl, fa], scala: 1 };\n"
                "      document.body.dataset.schermo = \"acceso\";",
                "                       fotogramma: [__g4_fl, fa], scala: 1 };\n"
                "      document.body.dataset.schermo = \"acceso\";",
            ),
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════
    "G5": {
        "che_cosa":
            "la tela puo' uscire con un lato DISPARI — la misura che `RCP.md` "
            "§4.5 rifiuta, e che `SPECIFICHE.md` §6.1-bis nomina nella terza "
            "`[?]`: «l'arrotondamento puo' produrre un numero dispari?»",
        "falso_verde":
            "il lato dispari era reso impossibile PER COSTRUZIONE dal `n − (n % "
            "2)` della pagina, e non veniva mai provocato: `fasi/06` §4.3 "
            "dichiarava la `[?]` CHIUSA su una condizione che nessuno aveva mai "
            "messo alla prova",
        "casi": [
            ("numeri", "", "NO  A3:"),
        ],
        "cambi": [(
            "    return n - (n % 2);",
            "    return n;  /* GUASTO G5 */",
        )],
    },
}


def innesta(dentro, fuori, quale):
    if quale not in GUASTI:
        raise SystemExit("06-b37-guasti: guasto sconosciuto «%s» (ce ne sono: "
                         "%s)" % (quale, ", ".join(sorted(GUASTI))))
    g = GUASTI[quale]
    with open(dentro, encoding="utf-8") as f:
        t = f.read()
    fatti = []
    for ancora, guasto in g["cambi"]:
        # ⛔ L'ANCORA DEVE ESSERE UNICA.  Zero volte = ancora scaduta; due volte
        #    = si innesta nel posto sbagliato.  In tutt'e due i casi si esce.
        n = t.count(ancora)
        if n != 1:
            raise SystemExit(
                "06-b37-guasti: ⛔ l'ancora di %s compare %d volte invece di 1 "
                "in %s.\n    ancora: %s\n⇒ Il guasto NON si innesta, e non si "
                "scrive niente.  E' la forma d'errore di `04-b31` G8 (ancora "
                "scaduta): si cura QUI, prima che un certificatore stampi un "
                "verde che non prova niente." % (quale, n, dentro, ancora[:90]))
        t = t.replace(ancora, guasto, 1)
        fatti.append(ancora.strip()[:60])
    with open(fuori, "w", encoding="utf-8") as f:
        f.write(t)
    print("06-b37-guasti: %s innestato in %s (%d ancore: %s)"
          % (quale, fuori, len(fatti), " | ".join(fatti)))
    return g


def ancore(dentro):
    """⛔ Tutte le ancore, verificate materialmente sul sorgente di oggi.  ⚠ Si
       lancia PRIMA di credere a un certificatore: un'ancora scaduta si vede
       qui, non nel verde che ne esce."""
    with open(dentro, encoding="utf-8") as f:
        t = f.read()
    male = 0
    for nome in sorted(GUASTI):
        for ancora, _ in GUASTI[nome]["cambi"]:
            n = t.count(ancora)
            print("    %-3s %-3s  %s" % (nome, "OK" if n == 1 else "⛔%d" % n,
                                         ancora.strip()[:78]))
            if n != 1:
                male += 1
    print("\n    %d ancore su %d vive con molteplicita' esattamente 1"
          % (sum(len(GUASTI[k]["cambi"]) for k in GUASTI) - male,
             sum(len(GUASTI[k]["cambi"]) for k in GUASTI)))
    return male


def casi():
    """⛔ I casi in forma leggibile da `06-b37-guasti.sh`, e stanno in UN POSTO
       SOLO: due elenchi dei casi sono due elenchi che prima o poi divergono —
       e il certificatore finirebbe a pretendere una frase che il guasto non
       dichiara piu' (la forma d'errore E2, due autorita' sullo stesso dato)."""
    for nome in sorted(GUASTI):
        for scena, fattore, frase in GUASTI[nome]["casi"]:
            print("%s|%s|%s|%s" % (nome, scena, fattore, frase))


def elenco():
    for nome in sorted(GUASTI):
        g = GUASTI[nome]
        print("\n%s — %s" % (nome, g["che_cosa"]))
        print("   ⛔ il falso verde che smaschera: %s" % g["falso_verde"])
        for scena, fattore, frase in g["casi"]:
            print("   ⇒ scena «%s»%s deve dire: «%s»"
                  % (scena, " a FATTORE=%s" % fattore if fattore else "", frase))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--elenco":
        elenco()
    elif len(sys.argv) >= 2 and sys.argv[1] == "--casi":
        casi()
    elif len(sys.argv) >= 3 and sys.argv[1] == "--ancore":
        sys.exit(1 if ancore(sys.argv[2]) else 0)
    elif len(sys.argv) >= 4:
        innesta(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__.split("\n\n")[0])
