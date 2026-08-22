#!/usr/bin/env python3
"""06-b35-guasti.py — ⛔ IL CONTROLLO POSITIVO: si innesta un guasto su una
COPIA dell'albero e si pretende che il banco diventi rosso **nel caso
dichiarato prima**, non «che diventi rosso qualcosa».

    python3 06-b35-guasti.py elenca
    python3 06-b35-guasti.py innesta G1 /media/REMOTIX/src/06-p-guasto/src
    python3 06-b35-guasti.py ritira  G1 /media/REMOTIX/src/06-p-guasto/src

===========================================================================
⛔ PERCHE' L'ATTESO SI DICHIARA PRIMA, E CASO PER CASO
===========================================================================

`CODER.md` §3.3-§3.4: un banco che non riproduce non e' una prova di
correttezza, ed e' piu' insidioso di uno rotto **perche' e' verde**.  ⭐ Ma
«diventa rosso» non basta: il modello e' `banchi/04-b31-certifica.sh`, che
innesta 12 guasti e pretende che si accendano **i casi attesi**.  Un guasto che
accende il caso sbagliato dice che il banco vede *un* problema, non *quel*
problema — e il giorno in cui la cura arriva, non sapremmo che cosa ha curato.

⚠ E l'atteso di **G4 e' VERDE**, di proposito: e' il modo in cui questo banco
  dichiara quel che NON copre.  Un controllo positivo in cui tutti i guasti
  diventano rossi non ha mai misurato il proprio limite.

===========================================================================
⛔ I GUASTI STANNO TUTTI NEI FILE DELLA SOTTOFASE 6.3
===========================================================================

`src/figlio.c` e `src/cattura.c`.  ⚠ Non e' una comodita': un controllo
positivo che innestasse un guasto in `rcp.c` misurerebbe la sensibilita' del
banco al codice di **un altro** agente, e quel codice puo' cambiare sotto di
noi mentre giriamo (le cinque regole dell'isolamento).
"""
import os
import sys

# ⛔⭐ LE SOGLIE SONO STATE CORRETTE DALLA MISURA, E SI DICHIARA — 16 agosto
#     2026, primo giro del controllo positivo.
#
#     La prima stesura pretendeva `adattate <= 1`, cioe' «col guasto addosso
#     quasi nessuna richiesta riesce».  ⛔ Ne riescono **tre**, e la ragione e'
#     del prodotto e non del guasto: nel giro «dieci» tre richieste su dieci
#     (#1, #7, #10) chiedono **1280x800**, e col guasto addosso la tela non
#     cambia mai ⇒ quelle tre chiedono la misura **che e' gia' in vigore**, e
#     `rcp.c` risponde `TELA(ADATTATA)` **da se'**, senza girare niente al
#     palco.  ⇒ La soglia guardava la grandezza sbagliata.
#
# ⚠ E si corregge il BANCO, non l'atteso: le tre righe descrittive erano giuste
#   in tutto il resto — il fondo di 3000 ms, il «subito», i fotogrammi che si
#   fermano o continuano, la riga del palco assente — e sono quelle che
#   distinguono un guasto dall'altro.  ⛔ Un banco corretto in silenzio dopo
#   aver visto il risultato non e' piu' un controllo: e' una conferma.
#
# ===========================================================================
# ⛔⭐ E LA TERZA CLAUSOLA DI G3 E' STATA CORRETTA DALLA MISURA — 22 agosto
#     2026, dopo il primo giro col metro sano e la marca al posto giusto
#     (`fasi/06` §5.8).
# ===========================================================================
#
#     Pretendeva `tela_nuova_dal_palco == 0`.  ⛔ Col registro finalmente
#     leggibile ne esce **1** — e quell'uno non e' un residuo del guasto: e' la
#     RICONCILIAZIONE DI NASCITA.
#
#     `[M]` 21 agosto, giro G3, `certifica-G3-tela.txt` — la riga e' UNA sola:
#         21:07:18.262 figlio ⭐⭐ TELA NUOVA DAL PALCO: 1920x1080 → 1280x800
#     e il PRIMO `ADATTA_TELA` del giro parte alle **21:07:18.738**, mezzo
#     secondo DOPO.  ⇒ Quella riga non puo' venire da `cattura_ridimensiona()`:
#     viene dal figlio che nasce al ripiego `TELA_L x TELA_A` = 1920x1080
#     (`src/main.c:112`, e `src/figlio.c:3239` lo dichiara come RIPIEGO) e che
#     riceve il primo fotogramma alla tela di sessione, 1280x800.  La riga la
#     scrive `figlio.c:6706` per QUALUNQUE fotogramma di misura diversa da
#     `tela_l`/`tela_a` — richiesto o no.
#
# ⛔⛔ E il vecchio `== 0` era PEGGIO che sbagliato: era **irraggiungibile da un
#      giro che misura davvero**.  Un giro senza nemmeno un fotogramma non si
#      misura (esce 5, «IL PALCO, NON IL PRODOTTO»); un giro con almeno un
#      fotogramma ha SEMPRE la riga di nascita.  ⇒ Quello zero poteva diventare
#      vero **solo con lo strumento cieco** — cioe' era esattamente la macchina
#      del falso verde smontata in §5.6, scritta dentro l'atteso.
#      ⭐ Il `== 1` invece cade dalla parte giusta: uno strumento cieco conta 0,
#      la regola diventa FALSA, e il caso esce ROSSO invece che verde.
#
# ⛔ E L'ALTRA STRADA E' ESCLUSA CON LA PROVA, non scartata a gusto.
#    «Completare il guasto» perche' produca lo zero vorrebbe dire spegnere anche
#    la riconciliazione di nascita — ma quella non passa da
#    `cattura_ridimensiona()`: e' il palco che NASCE alla misura nuova.  ⇒ (a)
#    sarebbe un secondo guasto sotto un nome solo, che le righe qui sotto
#    vietano; (b) starebbe nel punto che e' gia' G5; (c) e toglierebbe a G3 la
#    scena, perche' un giro senza fotogrammi non si misura affatto.
#
# ⭐ E LA DISTINZIONE CHE LA CLAUSOLA SERVE **RESTA IN PIEDI** — che era la
#    domanda vera, non «quale numero scriviamo».  Senza terza clausola G3 e G1
#    avrebbero la STESSA regola (`non_ora >= 6 and ms_mediano > 2500`), e il
#    controllo positivo direbbe che il banco vede *un* problema invece di *quel*
#    problema.  `[M]` 21 agosto, i tre giri della stessa ora:
#        G1   tela_nuova_dal_palco = 8   il palco OBBEDISCE, la risposta si perde
#        G3   tela_nuova_dal_palco = 1   al palco non arriva niente: solo la nascita
#        SANO tela_nuova_dal_palco = 10  1 di nascita + 9 cambi su 10 richieste
#    ⇒ Il numero separa G3 da G1 di sette unita' e dal sano di nove.
#
# ⚠ E il valore 1 e' legato ALLA SCENA, e va detto: vale per il giro «dieci», la
#   cui tela di sessione e' 1280x800 ≠ 1920x1080.  Una scena che aprisse la
#   sessione **proprio** a 1920x1080 non avrebbe riga di nascita e questo atteso
#   non varrebbe: e' per questo che l'atteso di G3 nomina il giro.
#
# Ogni guasto: file · quel che si cerca · quel che si mette · l'ATTESO.
# ⛔ La ricerca e' una stringa ESATTA e deve comparire **una volta sola**: una
#    sostituzione che colpisce due punti innesta due guasti sotto un nome solo,
#    e l'atteso non varrebbe piu' per nessuno dei due.
GUASTI = {
    "G1": {
        "file": "figlio.c",
        "che_cosa": "la riconciliazione sul fotogramma NON risponde piu' al "
                    "padre (`rispondi_tela()` tolta)",
        "cerca": "\t\t\t\trispondi_tela(tela_voluta_l, tela_voluta_a, tela_l, tela_a);",
        "metti": "\t\t\t\t(void)0; /* GUASTO G1 */",
        "atteso": "giro «dieci»: i 9 cambi di misura ricevono "
                  "TELA(RIFIUTATA, NON_ORA) **al fondo di §7.1** (ms > 2500), e "
                  "il client SMETTE di ricevere fotogrammi dopo il primo cambio "
                  "(la tela in vigore resta la vecchia e i fotogrammi portano "
                  "la nuova ⇒ §6.2 li fa scartare)",
        "regola": "non_ora >= 6 and ms_mediano > 2500 and fotogrammi < 100",
    },
    "G2": {
        "file": "figlio.c",
        "che_cosa": "il ramo `CHIESTA` risponde SUBITO «non ce l'ho fatta» "
                    "invece di tacere e lasciar parlare il fotogramma",
        "cerca": "\t\t\t\t\t\t              \"fotogramma, non da questa riga\",\n"
                 "\t\t\t\t\t\t              (unsigned)ci.a, (unsigned)ci.b);\n"
                 "\t\t\t\t\t\tcontinue;",
        "metti": "\t\t\t\t\t\t              \"fotogramma, non da questa riga\",\n"
                 "\t\t\t\t\t\t              (unsigned)ci.a, (unsigned)ci.b);\n"
                 "\t\t\t\t\t\trispondi_tela(tela_voluta_l, tela_voluta_a, 0, 0); /* G2 */\n"
                 "\t\t\t\t\t\tcontinue;",
        "atteso": "giro «dieci»: i 9 cambi ricevono TELA(RIFIUTATA, NON_ORA) "
                  "**SUBITO** (ms < 200) — ⭐ e' il caso che distingue «non ce "
                  "l'ho fatta» da «non ancora», cioe' la ragione per cui "
                  "`MSG_TELA` porta due misure e non una",
        "regola": "non_ora >= 6 and ms_mediano < 200",
    },
    "G3": {
        "file": "cattura.c",
        "che_cosa": "`cattura_ridimensiona()` NON chiama "
                    "`pw_stream_update_params()`: la richiesta non parte, e "
                    "l'esito dice lo stesso «chiesta»",
        "cerca": "\tquanti = 1 + parametri_di_consumo(cattura, &costruttore, parametri + 1);\n"
                 "\tesito = pw_stream_update_params(cattura->flusso, parametri, quanti);\n"
                 "\tpw_thread_loop_unlock(cattura->ciclo);\n"
                 "\n"
                 "\tif (esito < 0)\n"
                 "\t{\n"
                 "\t\tregistro_dice(AREA, \"⛔ `pw_stream_update_params()` a %ux%u ha risposto %d (%s)\",",
        "metti": "\tquanti = 1 + parametri_di_consumo(cattura, &costruttore, parametri + 1);\n"
                 "\tesito = 0; (void)quanti; /* GUASTO G3: la richiesta NON parte */\n"
                 "\tpw_thread_loop_unlock(cattura->ciclo);\n"
                 "\n"
                 "\tif (esito < 0)\n"
                 "\t{\n"
                 "\t\tregistro_dice(AREA, \"⛔ `pw_stream_update_params()` a %ux%u ha risposto %d (%s)\",",
        "atteso": "giro «dieci»: i 9 cambi ricevono TELA(RIFIUTATA, NON_ORA) al "
                  "fondo, ⭐ e nel registro NON compare **nessuna** riga «TELA "
                  "NUOVA DAL PALCO» **dopo il primo `ADATTA_TELA`** — che e' "
                  "quel che distingue «il palco non ha obbedito» da «non gli e' "
                  "stato chiesto».  ⛔⭐ ATTESO CORRETTO DALLA MISURA, 22 agosto "
                  "2026: il conto giusto e' **1, non 0**, perche' ogni giro che "
                  "misura porta la RICONCILIAZIONE DI NASCITA (il figlio nasce "
                  "al ripiego 1920x1080 e il primo fotogramma arriva alla tela "
                  "di sessione 1280x800), e quella riga precede di mezzo secondo "
                  "il primo `ADATTA_TELA`.  ⇒ Lo zero era irraggiungibile da un "
                  "giro vero e raggiungibile SOLO da uno strumento cieco.  Il "
                  "blocco di commento in cima a questo file porta la misura, e "
                  "il confronto: G1 = 8, G3 = 1, SANO = 10",
        "regola": "non_ora >= 6 and ms_mediano > 2500 and tela_nuova_dal_palco == 1",
    },
    "G4": {
        "file": "cattura.c",
        "che_cosa": "la guardia di `STUDI.md` §kde §8.2-bis confronta il "
                    "**chiesto** invece dell'**attuale** — il difetto n° 5 dei "
                    "dieci del 15 agosto 2026",
        "cerca": "\tif (cattura->formato_noto ? (larghezza == cattura->formato.size.width\n"
                 "\t                             && altezza == cattura->formato.size.height)\n"
                 "\t                          : (larghezza == cattura->chiesta_larghezza\n"
                 "\t                             && altezza == cattura->chiesta_altezza))",
        "metti": "\tif (larghezza == cattura->chiesta_larghezza\n"
                 "\t    && altezza == cattura->chiesta_altezza) /* GUASTO G4 */",
        "atteso": "⚠ **VERDE** — e si dichiara PRIMA.  Il difetto si presenta "
                  "solo quando il compositore **non obbedisce**, e `[M]` Mutter "
                  "concede sempre esattamente quel che si chiede (30 richieste "
                  "su 30 il 14 ago; 7 su 7 sui limiti il 16 ago) ⇒ su questo "
                  "palco «chiesto» e «attuale» coincidono SEMPRE.  ⛔ Questo "
                  "guasto misura il LIMITE del banco, non il prodotto: il "
                  "difetto n° 5 resta coperto solo da `04-b31-tela.c`, col palco "
                  "finto che sa disobbedire",
        "regola": "adattate >= 9 and non_ora == 0",
    },
    "G5": {
        "file": "figlio.c",
        "che_cosa": "la riconciliazione NON aggiorna `tela_l`/`tela_a`: i 28 "
                    "byte di §6.2 continuano a dichiarare la misura VECCHIA",
        "cerca": "\t\t\t\ttela_l = fo.larghezza;\n\t\t\t\ttela_a = fo.altezza;",
        "metti": "\t\t\t\t/* GUASTO G5: la misura vera NON diventa la nostra */",
        "atteso": "⛔⭐ ATTESO RISCRITTO DALLA MISURA — 16 agosto 2026, e la "
                  "prima stesura diceva *«il client CONTINUA a ricevere "
                  "fotogrammi, tutti alla misura di partenza»*.  ⛔ Era un "
                  "ragionamento, non una misura, e sbagliava su un fatto: "
                  "`tela_l`/`tela_a` **non nascono uguali alla tela concessa** "
                  "— nascono dalla riga di comando del figlio (1920x1080) e "
                  "diventano quelli veri **solo grazie alla riconciliazione**, "
                  "che e' proprio quel che G5 toglie.  ⇒ I 28 byte dichiarano "
                  "1920x1080 mentre la tela in vigore e' quella concessa, e "
                  "`webtransport.c` li scarta TUTTI (§6.2).  ⇒ ATTESO: **zero "
                  "fotogrammi al client**, i 9 cambi a NON_ORA, e nel registro "
                  "le righe «NON lo spedisco (§6.2)» che dicono che il palco "
                  "consegnava eccome",
        "regola": "fotogrammi == 0 and non_spediti > 0",
    },
}


def usa():
    print(__doc__)
    sys.exit(2)


def main():
    if len(sys.argv) < 2:
        usa()
    cmd = sys.argv[1]
    if cmd == "elenca":
        for k in sorted(GUASTI):
            g = GUASTI[k]
            print(f"{k}  [{g['file']}]  {g['che_cosa']}")
            print(f"      ATTESO: {g['atteso']}")
            print(f"      REGOLA: {g['regola']}")
        return 0
    if len(sys.argv) < 4:
        usa()
    quale, dove = sys.argv[2], sys.argv[3]
    if quale not in GUASTI:
        print(f"⛔ guasto sconosciuto: {quale}")
        return 2
    g = GUASTI[quale]
    p = os.path.join(dove, g["file"])
    s = open(p, encoding="utf-8").read()
    if cmd == "innesta":
        a, b = g["cerca"], g["metti"]
    elif cmd == "ritira":
        a, b = g["metti"], g["cerca"]
    else:
        usa()
    n = s.count(a)
    # ⛔ ZERO e DUE sono due guasti diversi del BANCO, e vanno distinti: «non
    #    l'ho trovato» vuol dire che il codice e' cambiato sotto di me, «ne ho
    #    trovati due» vuol dire che sto innestando due guasti sotto un nome
    #    solo.  ⚠ Tacere e andare avanti produrrebbe un giro VERDE su un albero
    #    che nessuno ha guastato — la forma peggiore (`CODER.md` §3.4).
    if n != 1:
        print(f"⛔ {cmd} {quale}: il testo cercato compare {n} volte in {p} "
              f"(ne serve ESATTAMENTE una).  Non tocco niente.")
        return 3
    open(p, "w", encoding="utf-8").write(s.replace(a, b, 1))
    print(f"OK {cmd} {quale} in {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
