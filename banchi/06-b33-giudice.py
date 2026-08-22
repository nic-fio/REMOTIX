#!/usr/bin/env python3
"""06-b33-giudice.py — ⛔ IL VERDETTO, e non lo da' chi manda.

    python3 06-b33-giudice.py --visto /media/REMOTIX/tmp/06-i/visto.jsonl \\
        --registro /media/REMOTIX/tmp/06-i/registro.log --da 5 \\
        --modo comanda --etichetta g7 --esiti .../06-b33-esiti.jsonl

⚠ Gira SUL SERVER, fuori dal contenitore, da root (i due file sono di root).
  Non ha nessuna dipendenza oltre alla libreria standard: e' voluto, cosi' il
  giudice si puo' eseguire anche quando il contenitore non c'e'.

===========================================================================
⛔ CHE COSA GIUDICA, E CHE COSA NON PUO' GIUDICARE
===========================================================================

Giudica **quel che una finestra vera dentro la sessione ha ricevuto** — cioe'
`CODER.md` §3.8, il lato che consuma.  ⛔ NON giudica il registro del server come
prova che l'input sia arrivato: quello dice che abbiamo chiamato una funzione.
Il registro si legge solo per le righe che **dichiarano un ripiego**, dove la
domanda e' proprio *«c'e' la riga?»*.

⛔⛔ E NON C'E' NESSUN BROWSER IN QUESTO BANCO, ne' Xvfb.  Il testimone e' una
    finestra Wayland nativa e il cliente e' un QUIC nativo.  ⇒ `LEZIONI.md`
    §1.15 — *su Xvfb `requestAnimationFrame` non gira mai, e in Blink l'evento
    `resize` si consegna dentro il giro di rendering* — **non tocca nessuna
    misura di questo banco**, e per la stessa ragione questo banco **non puo'
    dire niente** sulla scala di disegno, su `pixelated`, ne' sul cammino della
    pagina che segue la finestra: quelli vivono nel browser e sono di 6.5.

===========================================================================
⛔ IL DIFETTO ATTESO NON E' UN VERDE
===========================================================================

Nel modo `tenuto` c'e' un caso il cui esito **giusto col mondo col difetto
vivo** e' rosso: il rilascio del pulsante dopo il ricambio non arriva.  ⇒ Si
dichiara `DIFETTO_VIVO` e non `OK`: un banco che chiamasse «verde» un difetto
misurato sarebbe la cosa che `CODER.md` §4.6 vieta.

===========================================================================
⛔⛔ E TRE ATTESI ERANO SCRITTI PER IL MONDO COL DIFETTO VIVO — 21 ago 2026
===========================================================================

*Corretto oggi, e la ragione sta nel documento di fase §7.1: «va corretto
l'atteso del banco, non il prodotto».  ⚠ E' un banco nato il 16 agosto: il
difetto e' di allora, non del prodotto.*

Con la cura di `figlio.c:3964` — `input_rilascia_tutto()` **prima** di
`cattura_ridimensiona()` — al momento del ricambio **non c'e' piu' niente di
premuto**.  ⇒ Tre attesi diventavano rossi PROPRIO PERCHE' la cura c'era:

| era | perche' era sbagliato | adesso |
|---|---|---|
| **T3** pretendeva il rilascio del TASTO **dopo** il `RITELA` | con la cura il tasto e' gia' su **prima** | si chiede che il rilascio **arrivi**, prima o dopo — l'invariante e' «il desktop non resta con un tasto giu'», non «il rilascio arriva tardi» |
| **R1** pretendeva la riga degli ORFANI | senza niente di premuto non ci sono orfani da dichiarare | si pretende **solo nel mondo col difetto vivo**, e il mondo si legge dal registro |
| **R2** pretendeva la riga «il rilascio NON PARTE» | idem | idem |

⭐ E si aggiunge il caso che mancava, ed e' quello che conta davvero: **T4 — un
clic FRESCO, dopo il ricambio, arriva ancora?**  E' il danno vero (il conto del
posto rimasto a 1, `meta-seat-impl.c:899-908`), e nel banco di ieri **non lo
misurava nessuno**.

⛔ IL MONDO SI LEGGE, NON SI ASSUME: la riga che lo dichiara e' quella che
   `figlio.c` scrive quando rilascia prima di ridimensionare.  Un banco che
   assumesse il mondo darebbe rosso alla cura o verde al difetto, a seconda di
   quale dei due giorni e' stato scritto.
"""
import argparse
import json
import os
import sys

VERDE, ROSSO, GIALLO, BLU, GRIGIO = ("\033[1;32m", "\033[1;31m", "\033[1;33m",
                                     "\033[1;34m", "\033[0m")
BTN_LEFT, KEY_ENTER, KEY_A, KEY_CTRL = 272, 28, 30, 29

# ⛔ LE RIGHE DEL PRODOTTO CHE IL GIUDICE CERCA, in un posto solo e con accanto
#    chi le scrive: un marcatore sparso nel codice del giudice e' un marcatore
#    che nessuno aggiorna il giorno in cui la riga cambia.
#
# ⛔⛔ E il marcatore degli ORFANI e' **dei PULSANTI**, non generico — rilievo
#      della revisione avversariale, 21 agosto 2026.  `segna_orfani()`
#      (`src/input.c:666`) scrive la stessa frase per «pulsanti» e per «tasti»
#      (`%u %s erano PREMUTI…`), e il guasto G3 toglie la chiamata **solo sui
#      pulsanti**: cercando la frase generica, con il Ctrl giu' la riga dei
#      TASTI si scrive lo stesso e R1 restava verde col guasto innestato.
#
# ⚠ E lo spazio davanti a «pulsanti»/«tasti» ci sta apposta: e' il `%u %s`, e
#   ancora il marcatore alla parola intera invece che a una sua coda.
M_ORFANI_PULSANTI = " pulsanti erano PREMUTI sul dispositivo che il compositore ha appena tolto"
M_ORFANI_TASTI = " tasti erano PREMUTI sul dispositivo che il compositore ha appena tolto"
# ⛔ E col SEGUITO: «era premuto su un…» da solo combacia sia con «su UN
#    DISPOSITIVO» (il puntatore) sia con «su UNA TASTIERA».
M_NON_PARTE_PULSANTE = "NON PARTE: era premuto su un dispositivo"
M_NON_PARTE_TASTO = "NON PARTE: era premuto su una tastiera"
# ⛔⛔ La riga della CURA, `figlio.c` — ed e' UNA riga, non due sottostringhe
#      indipendenti.  *Corretta il 22 agosto 2026: erano `"RILASCIATI"` e
#      `"PRIMA di ridimensionare"` cercate separatamente, e due frammenti presi
#      da DUE righe diverse del registro avrebbero dichiarato «mondo curato»
#      senza che la cura fosse mai scattata.*  ⚠ E' la stessa forma del rilievo
#      sul `%s`: chi conta deve cercare la forma COMPLETA.
M_CURA = "fra tasti e pulsanti PRIMA di ridimensionare"
# `cattura_ridimensiona()` — e SOLO lei: il risveglio scrive un'altra frase
M_TELA_CHIESTA = "tela CHIESTA al produttore"
M_RISVEGLIO = "flusso RIAVVIATO alla stessa misura"
M_TOLTO_PUNTATORE = "il puntatore e' stato TOLTO dal compositore"
M_TOLTA_TASTIERA = "la tastiera e' stata TOLTA dal compositore"


def leggi_visto(percorso, da):
    """Le righe del testimone con `n` > `da`.  ⛔ E si tiene il numero: e' il
    denominatore, e senza «zero eventi» e «non ho guardato» sono uguali."""
    fuori = []
    with open(percorso, encoding="utf-8", errors="replace") as f:
        for riga in f:
            riga = riga.strip()
            if not riga.startswith("{"):
                continue
            try:
                d = json.loads(riga)
            except ValueError:
                continue
            if d.get("n", 0) > da:
                fuori.append(d)
    return fuori


def indice(righe, prova):
    for i, d in enumerate(righe):
        if prova(d):
            return i
    return -1


def tasto(righe, codice, premuto, dopo=-1):
    return indice(righe[dopo + 1:], lambda d: d.get("tipo") == "TASTO"
                  and d.get("codice") == codice
                  and d.get("premuto") == premuto)


def main():
    p = argparse.ArgumentParser(description="06-b33 — il verdetto")
    p.add_argument("--visto", required=True)
    p.add_argument("--registro", required=True)
    p.add_argument("--da", type=int, default=0)
    p.add_argument("--modo", choices=["comanda", "tenuto", "cura"],
                   default="comanda")
    p.add_argument("--etichetta", default="giro")
    p.add_argument("--scena", default="(non dichiarata)")
    p.add_argument("--tela-b", default="1000x640")
    p.add_argument("--esiti", default="")
    a = p.parse_args()

    righe = leggi_visto(a.visto, a.da)
    try:
        with open(a.registro, encoding="utf-8", errors="replace") as f:
            reg = f.read()
    except OSError:
        reg = ""
    bl, ba = (int(x) for x in a.tela_b.lower().split("x"))

    casi = []

    def caso(nome, esito, dettaglio):
        casi.append({"caso": nome, "esito": esito, "dettaglio": dettaglio})

    # ⛔ IL CONTROLLO ZERO: lo strumento ha visto QUALCOSA?  Un giudice che
    #    dicesse «nessun BOTTONE» su un file vuoto accuserebbe il prodotto di
    #    una cosa che non ha fatto (`CODER.md` §3.10, e §3.3 al rovescio).
    if not righe:
        caso("C0 lo strumento ha visto qualcosa", "NO",
             f"ZERO righe del testimone dopo n={a.da}: ⛔ IL BANCO, NON IL "
             f"PRODOTTO — il testimone non era aperto, o non aveva il fuoco")
        stampa(a, casi)
        return 3
    caso("C0 lo strumento ha visto qualcosa", "OK",
         f"{len(righe)} righe dopo n={a.da}")

    # ---- C1: il RITELA, dal lato che riceve -------------------------------
    i_rit = indice(righe, lambda d: d.get("tipo") == "RITELA")
    if i_rit >= 0:
        r = righe[i_rit]
        ok = (r.get("a_l"), r.get("a_a")) == (bl, ba)
        caso("C1 il compositore ha ridimensionato sotto una finestra APERTA",
             "OK" if ok else "NO",
             f"RITELA {r.get('da_l')}x{r.get('da_a')} → "
             f"{r.get('a_l')}x{r.get('a_a')} (atteso …→{bl}x{ba})")
    else:
        caso("C1 il compositore ha ridimensionato sotto una finestra APERTA",
             "NO", "nessuna riga RITELA: la finestra non e' stata "
                   "ridimensionata, quindi i dispositivi non sono ricambiati "
                   "⇒ ⛔ IL BANCO, NON IL PRODOTTO")
        i_rit = -1

    dopo = righe[i_rit + 1:] if i_rit >= 0 else []

    if a.modo in ("comanda", "cura"):
        # ---- C2: il puntatore, alle coordinate ESATTE ---------------------
        # ⛔ Esatte, non «e' arrivato qualcosa»: §7.3 vieta al server di
        #    trasformare le coordinate, e una scala silenziosa e' proprio il
        #    difetto che `input.c` dichiara invece di applicare.
        attesi = [(bl // 4, ba // 4), (bl * 3 // 4, ba * 3 // 4)]
        visti = [(d.get("x"), d.get("y")) for d in dopo
                 if d.get("tipo") in ("PUNTATORE", "PUNTATORE_ENTRA")]
        mancano = [q for q in attesi
                   if not any(abs(vx - q[0]) < 1 and abs(vy - q[1]) < 1
                              for vx, vy in visti)]
        caso("C2 il puntatore arriva DOPO il riattacco, alle coordinate esatte",
             "OK" if not mancano else "NO",
             f"attesi {attesi}, visti {visti}"
             + (f" — MANCANO {mancano}" if mancano else ""))

        # ---- C3: il tasto -------------------------------------------------
        g = tasto(dopo, KEY_ENTER, 1)
        s = tasto(dopo, KEY_ENTER, 0, g) if g >= 0 else -1
        caso("C3 il TASTO arriva DOPO il riattacco (Invio giu' e su)",
             "OK" if g >= 0 and s >= 0 else "NO",
             f"KEY_ENTER giu' {'si' if g >= 0 else 'NO'}, "
             f"su {'si' if s >= 0 else 'NO'}")

        # ---- C4: la LETTERA, cioe' la disposizione riletta -----------------
        g = tasto(dopo, KEY_A, 1)
        caso("C4 la LETTERA «a» esce come posizione 30 (disposizione riletta)",
             "OK" if g >= 0 else "NO",
             "KEY_A visto" if g >= 0 else "nessun KEY_A: la keymap non e' "
                                          "stata riletta, o la lettera non e' "
                                          "producibile")

        # ---- C5: il CLIC --------------------------------------------------
        g = indice(dopo, lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT and d.get("premuto") == 1)
        s = indice(dopo[g + 1:], lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT
                   and d.get("premuto") == 0) if g >= 0 else -1
        caso("C5 il CLIC arriva DOPO il riattacco (BTN_LEFT giu' e su)",
             "OK" if g >= 0 and s >= 0 else "NO",
             f"BTN_LEFT giu' {'si' if g >= 0 else 'NO'}, "
             f"su {'si' if s >= 0 else 'NO'}")

    if a.modo == "cura":
        # ⭐ Il rilascio PRIMA del ricambio: e' la cura, simulata dal filo.
        prima = righe[:i_rit] if i_rit >= 0 else righe
        s = indice(prima, lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT and d.get("premuto") == 0)
        caso("K1 il rilascio PRIMA del ricambio arriva", "OK" if s >= 0 else "NO",
             "BTN_LEFT su visto prima del RITELA" if s >= 0
             else "⛔ non arriva nemmeno prima: la cura proposta non e' quella")

    if a.modo == "tenuto":
        # ⛔⛔ IL MONDO SI LEGGE DAL REGISTRO, e da qui in giu' gli attesi
        #      dipendono da lui.  ⚠ La riga e' quella di `figlio.c`, che
        #      rilascia PRIMA di ridimensionare: se c'e', al ricambio non c'era
        #      piu' niente di premuto, e pretendere le righe dei ripieghi
        #      sarebbe scrivere l'atteso di un mondo che non e' questo.
        curato = M_CURA in reg
        caso("T0 in quale mondo siamo — e si LEGGE, non si assume",
             "OK",
             ("⭐ CURATO: `figlio.c` dichiara di aver rilasciato PRIMA di "
              "ridimensionare ⇒ al ricambio non c'era niente di premuto"
              if curato else
              "⛔ DIFETTO VIVO: nessuna riga «RILASCIATI … PRIMA di "
              "ridimensionare» ⇒ il pulsante e' arrivato giu' al ricambio"))

        prima = righe[:i_rit] if i_rit >= 0 else righe
        g = indice(prima, lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT and d.get("premuto") == 1)
        caso("T1 il pulsante era GIU' prima del ricambio",
             "OK" if g >= 0 else "NO",
             "BTN_LEFT giu' visto prima del RITELA" if g >= 0
             else "⛔ IL BANCO: non si e' mai premuto niente, quindi non c'e' "
                  "nessun orfano da misurare")

        # ---- T2: il rilascio arriva, PRIMA O DOPO, purche' arrivi ---------
        # ⛔ E la domanda giusta e' questa, non «arriva DOPO»: l'invariante di
        #    `RCP.md` §11 e' «il desktop non resta con un pulsante giu'».  Con
        #    la cura il rilascio arriva PRIMA del ricambio, ed e' un successo,
        #    non un fallimento — l'atteso di ieri lo chiamava rosso.
        # ⛔⛔ E IL RILASCIO TENUTO SI DISTINGUE DAL RILASCIO DEL CLIC FRESCO
        #      **per il press che li separa**, non per la posizione rispetto al
        #      `RITELA` — difetto del banco trovato il 21 agosto 2026, e dava un
        #      giallo falso.
        #
        #      `[M]` Con la cura, il rilascio del pulsante tenuto arriva
        #      nell'istante del ridimensionamento, e se il testimone lo scrive
        #      **dopo** la sua riga `RITELA` — cosa che dipende dall'ordine con
        #      cui Wayland gli consegna configure e button, cioe' da una corsa —
        #      il vecchio conto lo scambiava per il rilascio del clic FRESCO.
        #      ⇒ T2 diventava «arriva» sul rilascio sbagliato e T4 non trovava
        #      piu' nessun clic dopo di lui.
        #
        # ⇒ Il confine e' il PRESS FRESCO: tutto quel che sta prima appartiene al
        #   pulsante tenuto, tutto quel che sta dopo al clic nuovo.
        i_fresco = indice(dopo, lambda d: d.get("tipo") == "BOTTONE"
                          and d.get("bottone") == BTN_LEFT and d.get("premuto") == 1)
        fino_al_fresco = dopo[:i_fresco] if i_fresco >= 0 else dopo
        s_prima = indice(prima, lambda d: d.get("tipo") == "BOTTONE"
                         and d.get("bottone") == BTN_LEFT and d.get("premuto") == 0)
        s_dopo = indice(fino_al_fresco, lambda d: d.get("tipo") == "BOTTONE"
                        and d.get("bottone") == BTN_LEFT and d.get("premuto") == 0)
        dove = ("prima del ricambio" if s_prima >= 0
                else "dopo il ricambio, e prima del clic fresco" if s_dopo >= 0
                else "MAI")
        caso("T2 ⛔ il rilascio del pulsante ARRIVA al desktop (prima o dopo)",
             "OK" if (s_prima >= 0 or s_dopo >= 0) else "DIFETTO_VIVO",
             f"BTN_LEFT su: {dove}"
             + ("" if (s_prima >= 0 or s_dopo >= 0) else
                " — il posto conta il pulsante ancora giu' e da adesso nessun "
                "clic funziona (`meta-seat-impl.c:899-908`)"))

        # ---- T3: il TASTO, con la stessa domanda --------------------------
        # ⚠ Controllo INTERNO alla scena: la tastiera non e' un dispositivo di
        #   viewport e non ricambia al cambio di GEOMETRIA, quindi il suo
        #   rilascio deve arrivare comunque.  Se non arrivasse, la causa
        #   sarebbe un'altra e T2 accuserebbe la cosa sbagliata.
        k_prima = indice(prima, lambda d: d.get("tipo") == "TASTO"
                         and d.get("codice") == KEY_CTRL and d.get("premuto") == 0)
        k_dopo = indice(dopo, lambda d: d.get("tipo") == "TASTO"
                        and d.get("codice") == KEY_CTRL and d.get("premuto") == 0)
        dovek = ("prima del ricambio" if k_prima >= 0
                 else "dopo il ricambio" if k_dopo >= 0 else "MAI")
        caso("T3 il rilascio del TASTO arriva (controllo interno alla scena)",
             "OK" if (k_prima >= 0 or k_dopo >= 0) else "NO",
             f"Ctrl su: {dovek}"
             + ("" if (k_prima >= 0 or k_dopo >= 0) else
                " — ⛔ non arriva nemmeno il tasto: la causa NON e' il ricambio "
                "del puntatore, e T2 sta accusando la cosa sbagliata"))

        # ---- T4: ⭐⭐ IL CASO CHE MANCAVA, ed e' il danno vero -------------
        # ⛔ «Il rilascio non arriva» e' il sintomo; «il desktop non prende piu'
        #    un clic» e' il DANNO, ed e' quel che l'utente ha descritto il 15
        #    agosto.  Il banco di ieri non lo misurava in modo `tenuto`.
        # ⛔ Il clic fresco e' il PRIMO press dopo il `RITELA` col suo rilascio:
        #    il pulsante tenuto non produce nessun press qui dentro (era gia'
        #    giu' da prima), quindi il primo «giu'» che si vede e' per forza il
        #    nuovo.
        gf = i_fresco
        sf = indice(dopo[gf + 1:], lambda d: d.get("tipo") == "BOTTONE"
                    and d.get("bottone") == BTN_LEFT
                    and d.get("premuto") == 0) if gf >= 0 else -1
        caso("T4 ⭐⭐ un clic FRESCO, dopo il ricambio, arriva ancora?",
             "OK" if gf >= 0 and sf >= 0 else "DIFETTO_VIVO",
             f"clic fresco: giu' {'si' if gf >= 0 else 'NO'}, "
             f"su {'si' if sf >= 0 else 'NO'}"
             + ("" if gf >= 0 and sf >= 0 else
                " — ⛔ da adesso il desktop NON PRENDE PIU' UN CLIC per tutta "
                "la sessione: e' «su Android il mouse non prende piu' i click»"))

        # ---- le righe che DEVONO esserci, e SOLO nel mondo giusto ----------
        # ⛔ Qui la domanda e' «c'e' la riga?», l'unica a cui il registro di chi
        #    manda risponda onestamente.  ⚠ E si pretende **solo col difetto
        #    vivo**: col tasto gia' rilasciato non c'e' nessun ripiego da
        #    dichiarare, e chiederlo lo stesso e' l'atteso di ieri.
        for nome, pezzo in (
                ("R1 il ricambio coi PULSANTI premuti e' DICHIARATO", M_ORFANI_PULSANTI),
                ("R2 il rilascio impossibile del PULSANTE e' DICHIARATO",
                 M_NON_PARTE_PULSANTE)):
            if pezzo in reg:
                caso(nome, "OK", "la riga c'e'")
            elif curato:
                caso(nome, "NON_IN_SCENA",
                     "⭐ la riga non c'e' — ed e' GIUSTO: la cura ha rilasciato "
                     "prima del ricambio, quindi non c'era nessun orfano da "
                     "dichiarare.  ⛔ Pretenderla qui era l'atteso del mondo col "
                     "difetto vivo (§7.1)")
            else:
                # ⚠ E si dice se c'e' la riga dell'ALTRO dispositivo: e' la
                #   forma d'errore che la revisione del 22 agosto ha trovato nel
                #   banco gemello, e qui non deve nascere.
                altro = ""
                if pezzo == M_ORFANI_PULSANTI and M_ORFANI_TASTI in reg:
                    altro = ".  ⚠ C'e' quella dei TASTI, che e' un'altra cosa"
                elif pezzo == M_NON_PARTE_PULSANTE and M_NON_PARTE_TASTO in reg:
                    altro = ".  ⚠ C'e' quella della TASTIERA, che e' un'altra cosa"
                caso(nome, "NO",
                     "⛔ la riga NON c'e' e la cura nemmeno: il registro dice "
                     "«fatto» mentre il desktop resta bloccato — `CODER.md` §4.6"
                     + altro)

    # ---- i ricambi, LETTI e non dedotti -----------------------------------
    #
    # ⛔⛔ E SI CONTANO NELLA FINESTRA DEL RIDIMENSIONAMENTO, non su tutto il
    #      registro — rilievo della revisione avversariale, 21 agosto 2026.
    #
    #      `[M]` 21 agosto (banco `06-b33-risveglio`): **ogni
    #      `cattura_risveglia()` ricrea i dispositivi**, 3 risvegli → 3 ricambi.
    #      ⇒ Un `rp >= 1` contato su tutto il registro e' soddisfatto dai
    #      risvegli, e resterebbe verde **anche se il cambio di geometria
    #      smettesse del tutto di toccare il puntatore**: cioe' C6 sarebbe cieco
    #      proprio sulla cosa che deve vedere.
    #
    # ⇒ La finestra comincia all'ULTIMA `tela CHIESTA al produttore`, che scrive
    #   **solo** `cattura_ridimensiona()` — il risveglio scrive un'altra frase.
    i_tela = reg.rfind(M_TELA_CHIESTA)
    coda = reg[i_tela:] if i_tela >= 0 else ""
    rp_tot = reg.count(M_TOLTO_PUNTATORE)
    rt_tot = reg.count(M_TOLTA_TASTIERA)
    rp = coda.count(M_TOLTO_PUNTATORE)
    rt = coda.count(M_TOLTA_TASTIERA)
    risv = reg.count(M_RISVEGLIO)
    if i_tela < 0:
        caso("C6 il puntatore ricambia, la tastiera NO (al cambio di GEOMETRIA)",
             "NO",
             "⛔ IL BANCO: nel registro non c'e' nessuna «tela CHIESTA al "
             "produttore» ⇒ non c'e' stato nessun ridimensionamento, e non c'e' "
             "niente da contare")
    else:
        caso("C6 il puntatore ricambia, la tastiera NO (al cambio di GEOMETRIA)",
             "OK" if rp >= 1 and rt == 0 else "NO",
             f"DOPO l'ultimo ridimensionamento: ricambi_puntatore={rp} "
             f"ricambi_tastiera={rt} — atteso ≥1 e 0 "
             f"(`meta-eis-client.c:197-206`: `remove_viewport_devices` guarda "
             f"solo TOUCH e POINTER_ABSOLUTE).  ⚠ Su TUTTO il giro erano "
             f"{rp_tot} e {rt_tot}, con {risv} risvegli del flusso: ogni "
             f"risveglio ricrea i dispositivi da se' (§7.1, `[M]` 21 ago 2026), "
             f"ed e' per questo che il conto totale non serve")

    return stampa(a, casi)


def stampa(a, casi):
    """⛔⛔ E QUI SI SCRIVE ANCHE **SE LA SCENA REGGE** — rilievo della revisione
    avversariale, 21 agosto 2026.

    Il giudice **sapeva gia'** dire *«IL BANCO, NON IL PRODOTTO»* (C0 e C1), ma
    lo diceva **solo a schermo**: negli esiti finiva un caso rosso come tutti
    gli altri.  ⇒ `06-b33-certifica.sh` faceva un test di APPARTENENZA sui
    rossi, e un giro **completamente fallito** — client che non regge la
    stretta di mano, testimone senza fuoco — produceva un insieme di rossi che
    **contiene** il caso dichiarato, e il certificatore dichiarava successo.

    ⇒ `scena_valida: false` e' il campo che chi certifica deve guardare PRIMA
      di credere a qualunque rosso.
    """
    banco = [c["caso"] for c in casi
             if c["esito"] == "NO" and "IL BANCO" in c["dettaglio"]]
    print(f"\n== 06-b33 · giudizio «{a.etichetta}» · modo {a.modo}")
    print(f"   scena: {a.scena}")
    rossi = 0
    for c in casi:
        col = {"OK": VERDE, "NO": ROSSO, "DIFETTO_VIVO": GIALLO,
               "NON_IN_SCENA": BLU}[c["esito"]]
        print(f"   {col}{c['esito']:12s}{GRIGIO} {c['caso']}")
        print(f"                {c['dettaglio']}")
        if c["esito"] == "NO":
            rossi += 1
    vivi = sum(1 for c in casi if c["esito"] == "DIFETTO_VIVO")
    fuori = sum(1 for c in casi if c["esito"] == "NON_IN_SCENA")
    print(f"\n   {len(casi)} casi · {rossi} rossi · {vivi} difetti vivi "
          f"dichiarati · {fuori} fuori scena")
    if banco:
        print(f"   {ROSSO}⛔ LA SCENA NON REGGE{GRIGIO}: {', '.join(banco)} ⇒ "
              f"nessun rosso di questo giro accusa il prodotto")
    if a.esiti:
        with open(a.esiti, "a", encoding="utf-8") as f:
            f.write(json.dumps({"etichetta": a.etichetta, "modo": a.modo,
                                "scena": a.scena, "scena_valida": not banco,
                                "casi": casi}, ensure_ascii=False) + "\n")
        print(f"   esiti: {a.esiti}")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
