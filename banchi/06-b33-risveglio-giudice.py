#!/usr/bin/env python3
"""06-b33-risveglio-giudice.py — ⛔ IL VERDETTO DI §7.1, e non lo da' chi manda.

    python3 06-b33-risveglio-giudice.py --visto .../visto.jsonl \\
        --iniettore .../06-b33-risveglio.log --da 12 --modo tenuto \\
        --etichetta s2-tenuto --tela 1264x800 --esiti .../esiti.jsonl

⚠ Gira SUL SERVER, fuori dal contenitore, da root (i due file sono di root).
  Nessuna dipendenza oltre alla libreria standard.

===========================================================================
⛔ CHE COSA GIUDICA, E DA QUALE LATO
===========================================================================

Due fonti, e **non hanno lo stesso peso**:

  · `--visto`      quel che una finestra Wayland VERA dentro la sessione ha
                   ricevuto.  ⭐ E' la misura (`CODER.md` §3.8);
  · `--iniettore`  quel che il programma che manda **dice** di aver fatto.
                   ⛔ NON e' una prova che il desktop abbia ricevuto: si legge
                   per due sole cose — il conto `ricambi_puntatore`, che e' una
                   finestra sullo stato interno di `input.c` e non una riga di
                   registro, e la presenza delle righe che DICHIARANO un
                   ripiego, dove la domanda e' proprio «c'e' la riga?».

===========================================================================
⛔ IL DIFETTO ATTESO NON E' UN VERDE, E IL VERDE ATTESO NON E' UN ROSSO
===========================================================================

Nel modo `tenuto` ci sono casi il cui esito **giusto col mondo di oggi** e'
`DIFETTO_VIVO`: il rilascio dopo il ricambio non arriva, e il clic fresco
nemmeno.  ⇒ Si dichiara `DIFETTO_VIVO` e non `OK` — un banco che chiamasse
«verde» un difetto misurato e' la cosa che `CODER.md` §4.6 vieta — e nemmeno
`NO`, che vorrebbe dire «il banco ha trovato qualcosa che non si aspettava».

⭐ Il giorno che la cura c'e', quei casi devono diventare `OK`.  E se non
diventano, la cura non e' quella che si credeva.
"""
import argparse
import json
import re
import sys

VERDE, ROSSO, GIALLO, BLU, GRIGIO = ("\033[1;32m", "\033[1;31m", "\033[1;33m",
                                     "\033[1;34m", "\033[0m")
BTN_LEFT, KEY_ENTER, KEY_CTRL = 272, 28, 29


def leggi_visto(percorso, da):
    """Le righe del testimone con `n` > `da`.  ⛔ E si tiene il numero: e' il
    denominatore, e senza «zero eventi» e «non ho guardato» sono uguali."""
    fuori = []
    try:
        f = open(percorso, encoding="utf-8", errors="replace")
    except OSError:
        return fuori
    with f:
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


def bottone(righe, premuto, dopo=-1):
    for i, d in enumerate(righe[dopo + 1:], start=dopo + 1):
        if (d.get("tipo") == "BOTTONE" and d.get("bottone") == BTN_LEFT
                and d.get("premuto") == premuto):
            return i
    return -1


def tasto(righe, codice, premuto, dopo=-1):
    for i, d in enumerate(righe[dopo + 1:], start=dopo + 1):
        if (d.get("tipo") == "TASTO" and d.get("codice") == codice
                and d.get("premuto") == premuto):
            return i
    return -1


def main():
    p = argparse.ArgumentParser(description="06-b33 §7.1 — il verdetto")
    p.add_argument("--visto", required=True)
    p.add_argument("--iniettore", required=True)
    p.add_argument("--da", type=int, default=0)
    p.add_argument("--modo", choices=["strumento", "libero", "tenuto"],
                   default="tenuto")
    p.add_argument("--etichetta", default="giro")
    p.add_argument("--scena", default="(non dichiarata)")
    p.add_argument("--tela", default="1264x800")
    p.add_argument("--esiti", default="")
    a = p.parse_args()

    righe = leggi_visto(a.visto, a.da)
    try:
        with open(a.iniettore, encoding="utf-8", errors="replace") as f:
            ini = f.read()
    except OSError:
        ini = ""

    # ⛔ I risvegli e i loro delta, LETTI dalle righe dell'iniettore: il conto
    #    viene da `input_conto()`, che e' lo stato interno di `input.c`, non una
    #    deduzione da un registro.
    risvegli = [(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                for m in re.finditer(
                    r"RISVEGLIO n\.(\d+) esito=(-?\d+) ricambi_puntatore \d+ → \d+ "
                    r"\(delta (-?\d+)\)", ini)]
    ridim = [(int(m.group(1)), int(m.group(2)))
             for m in re.finditer(
                 r"RIDIMENSIONATO a \S+ esito=(-?\d+) ricambi_puntatore \d+ → \d+ "
                 r"\(delta (-?\d+)\)", ini)]

    casi = []

    def caso(nome, esito, dettaglio):
        casi.append({"caso": nome, "esito": esito, "dettaglio": dettaglio})

    # ---- C0: lo strumento ha visto qualcosa? ------------------------------
    # ⛔ Un giudice che dicesse «nessun BOTTONE» su un file vuoto accuserebbe il
    #    prodotto di una cosa che non ha fatto (`CODER.md` §3.10).
    #
    # ⛔⛔ E LO STRUMENTO NON E' LO STESSO IN TUTTE LE SCENE — difetto del banco
    #      trovato il 21 agosto 2026, al secondo giro.  Nella scena `libero`
    #      **non si inietta niente al testimone**: la misura e' il conto dei
    #      ricambi, che viene da `input_conto()`.  ⇒ Pretendere righe del
    #      testimone li' dentro era un rosso che accusava il banco di se stesso,
    #      e che avrebbe nascosto la misura vera.
    if a.modo == "libero":
        if not ini.strip():
            caso("C0 lo strumento ha parlato", "NO",
                 "⛔ IL BANCO: il registro dell'iniettore e' VUOTO")
            return stampa(a, casi)
        caso("C0 lo strumento ha parlato", "OK",
             f"{len(ini.splitlines())} righe dall'iniettore — ⚠ e in questa "
             f"scena il testimone NON e' lo strumento: non si inietta niente "
             f"che debba arrivargli")
    else:
        if not righe:
            caso("C0 lo strumento ha visto qualcosa", "NO",
                 f"ZERO righe del testimone dopo n={a.da}: ⛔ IL BANCO, NON IL "
                 f"PRODOTTO — il testimone non era aperto, o non aveva il fuoco")
            return stampa(a, casi)
        caso("C0 lo strumento ha visto qualcosa", "OK",
             f"{len(righe)} righe dopo n={a.da}")

    if a.modo == "strumento":
        # ⭐ IL CONTROLLO ZERO: un clic senza nessun ricambio in mezzo.  Se
        #   questo non e' verde, ogni rosso delle altre scene accusa il banco.
        g = bottone(righe, 1)
        s = bottone(righe, 0, g) if g >= 0 else -1
        caso("S0 il clic arriva quando NON c'e' nessun ricambio",
             "OK" if g >= 0 and s >= 0 else "NO",
             f"BTN_LEFT giu' {'si' if g >= 0 else 'NO'}, su {'si' if s >= 0 else 'NO'}"
             + ("" if g >= 0 and s >= 0 else
                " — ⛔ IL BANCO: senza questo verde nessun altro rosso significa niente"))
        caso("S0-bis e NESSUN risveglio e' stato chiesto",
             "OK" if not risvegli else "NO",
             f"risvegli nel registro dell'iniettore: {len(risvegli)} (atteso 0)")
        return stampa(a, casi)

    if a.modo == "libero":
        # ---- LA TESI DI §7.1, presa per smentirla -------------------------
        deltas = [d for (_n, _e, d) in risvegli]
        caso("L1 i tre risvegli sono partiti",
             "OK" if len(risvegli) == 3 and all(e for (_n, e, _d) in risvegli) else "NO",
             f"risvegli={len(risvegli)} esiti={[e for (_n, e, _d) in risvegli]} "
             f"(atteso 3, tutti esito=1)")
        caso("L2 ⭐ OGNI risveglio ricrea i dispositivi — §7.1",
             "OK" if deltas and all(d >= 1 for d in deltas) else "NO",
             f"delta di ricambi_puntatore per risveglio: {deltas} (atteso [1,1,1] "
             f"o piu').  ⛔ Se fossero zeri, §7.1 E' FALSA e va corretta: "
             f"`[R]` `meta-screen-cast-virtual-stream-src.c:283` chiama "
             f"`meta_eis_viewport_notify_changed()` a ogni `..._src_enable()`")
        caso("L3 e NESSUNO ha toccato la tela",
             "OK" if not ridim else "NO",
             f"chiamate a cattura_ridimensiona(): {len(ridim)} (atteso 0) — "
             f"e' la meta' della tesi che rende §7.1 una porta NUOVA")
        # ⚠ A mano alzata non c'e' niente di premuto: la riga degli orfani NON
        #   deve esserci.  Se ci fosse, il conto di `input.c` sarebbe sporco.
        caso("L4 a mano alzata NON ci sono orfani",
             "OK" if "erano PREMUTI sul dispositivo" not in ini else "NO",
             "nessuna riga di orfani, com'e' giusto"
             if "erano PREMUTI sul dispositivo" not in ini
             else "⛔ c'e' una riga di orfani senza che nulla fosse premuto: il "
                  "conto di input.c e' sporco")
        return stampa(a, casi)

    # ------------------------------------------------------------------ #
    #  modo «tenuto»: la scena cattiva, col risveglio o col ridimensionamento
    # ------------------------------------------------------------------ #
    porta = "risveglio" if risvegli else ("ridimensionamento" if ridim else "NESSUNA")
    deltas = ([d for (_n, _e, d) in risvegli] or [d for (_e, d) in ridim])

    caso("T0 la porta si e' aperta: i dispositivi sono ricambiati",
         "OK" if deltas and any(d >= 1 for d in deltas) else "NO",
         f"porta={porta}, delta di ricambi_puntatore={deltas} (atteso ≥1).  "
         f"⛔ Se fosse 0 il difetto NON e' stato riprodotto, e quel che segue "
         f"non misura niente")

    # ⛔ Il pulsante era GIU' PRIMA della porta?  Senza, non c'e' orfano da
    #    misurare e il rosso accuserebbe la cosa sbagliata.
    caso("T1 qualcosa era PREMUTO al momento del ricambio",
         "OK" if "erano PREMUTI sul dispositivo che il compositore ha appena tolto" in ini
         else "NO",
         "`input.c` dichiara gli orfani, dunque c'era qualcosa di premuto"
         if "erano PREMUTI sul dispositivo che il compositore ha appena tolto" in ini
         else "⛔ IL BANCO: nessun orfano dichiarato — o non si e' premuto "
              "niente, o il ricambio e' arrivato prima della pressione")

    g = bottone(righe, 1)
    caso("T2 il testimone ha visto il pulsante SCENDERE",
         "OK" if g >= 0 else "NO",
         "BTN_LEFT giu' visto" if g >= 0
         else "⛔ IL BANCO: il testimone non ha visto nemmeno la pressione")

    # ---- T3: il rilascio, DOVUNQUE sia ------------------------------------
    # ⛔ E la domanda giusta e' «il rilascio arriva?», non «arriva DOPO il
    #    ricambio»: con una cura che rilascia PRIMA, il rilascio arriva prima —
    #    e un banco che guardasse solo il «dopo» chiamerebbe rossa la cura.
    # ⛔⛔ E IL RILASCIO DEL PULSANTE TENUTO SI DISTINGUE DA QUELLO DEL CLIC
    #      FRESCO **per il press che li separa** — difetto del banco trovato il
    #      21 agosto 2026 sul gemello `06-b33-giudice.py`: prendendo «il primo
    #      rilascio dopo il press tenuto» si rischia di prendere il rilascio del
    #      clic NUOVO, e allora T3 diventa verde su un desktop bloccato.
    #  ⇒ Il confine e' il SECONDO press: quel che sta prima e' del pulsante
    #    tenuto, quel che sta dopo e' del clic fresco.
    g2 = bottone(righe, 1, g) if g >= 0 else -1
    limite = g2 if g2 >= 0 else len(righe)
    s = -1
    if g >= 0:
        cand = bottone(righe[:limite], 0, g)
        s = cand
    caso("T3 ⛔ il rilascio del pulsante arriva al desktop (prima o dopo, purche' arrivi)",
         "OK" if s >= 0 else "DIFETTO_VIVO",
         "il rilascio arriva — ⭐ allora questa porta e' curata" if s >= 0
         else "NON arriva: il posto conta il pulsante ancora giu' "
              "(`meta-seat-impl.c:899-908`), e `handle_button` "
              "(`meta-eis-client.c:612-621`) ingoia in silenzio il rilascio sul "
              "dispositivo nuovo")

    # ---- T4: ⭐ LA MISURA CHE CONTA — il desktop prende ancora i clic? -----
    s2 = bottone(righe, 0, g2) if g2 >= 0 else -1
    caso("T4 ⭐⭐ un clic FRESCO, dopo tutto, arriva ancora?",
         "OK" if g2 >= 0 and s2 >= 0 else "DIFETTO_VIVO",
         f"clic fresco: giu' {'si' if g2 >= 0 else 'NO'}, su {'si' if s2 >= 0 else 'NO'}"
         + ("" if g2 >= 0 and s2 >= 0 else
            " — ⛔ da adesso il desktop NON PRENDE PIU' UN CLIC, per tutta la "
            "sessione: e' «su Android il mouse non prende piu' i click»"))

    # ---- T5: il controllo INTERNO alla scena — la tastiera -----------------
    # ⚠ La tastiera non e' un dispositivo di viewport (`remove_viewport_devices`
    #   guarda TOUCH e POINTER_ABSOLUTE), quindi al ricambio di geometria NON
    #   ricambia e il suo rilascio DEVE arrivare.  Se non arrivasse, la causa
    #   sarebbe un'altra e T3/T4 accuserebbero la cosa sbagliata.
    #
    # ⛔⛔ E «non iniettato» NON E' «iniettato e perso» — difetto del banco
    #      trovato il 21 agosto 2026, alla prima corsa della scena `guarigione`:
    #      quella scena non batte nessun tasto, e T5/T6 uscivano ROSSI dicendo
    #      *«non arriva nemmeno il tasto»* — cioe' il banco accusava il prodotto
    #      di una cosa che nessuno gli aveva chiesto (`CODER.md` §3.10).
    #      ⇒ Se il tasto non e' stato nemmeno CHIESTO all'iniettore, il caso e'
    #      fuori scena, non rosso.
    chiesto_ctrl = "posizione 29 1 ->" in ini
    chiesto_invio = "posizione 28 1 ->" in ini
    kg = tasto(righe, KEY_CTRL, 1)
    ks = tasto(righe, KEY_CTRL, 0, kg) if kg >= 0 else -1
    if not chiesto_ctrl:
        caso("T5 il TASTO invece va giu' e torna su (controllo interno alla scena)",
             "NON_IN_SCENA",
             "questa scena non batte nessun Ctrl: non c'e' niente da giudicare")
    else:
        caso("T5 il TASTO invece va giu' e torna su (controllo interno alla scena)",
             "OK" if kg >= 0 and ks >= 0 else "NO",
             f"Ctrl giu' {'si' if kg >= 0 else 'NO'}, su {'si' if ks >= 0 else 'NO'}"
             + ("" if kg >= 0 and ks >= 0 else
                " — ⛔ non arriva nemmeno il tasto: la causa NON e' il ricambio "
                "del PUNTATORE, e T3/T4 stanno accusando la cosa sbagliata"))

    ke = tasto(righe, KEY_ENTER, 1)
    if not chiesto_invio:
        caso("T6 e un tasto FRESCO arriva ancora", "NON_IN_SCENA",
             "questa scena non batte nessun Invio: non c'e' niente da giudicare")
    else:
        caso("T6 e un tasto FRESCO arriva ancora",
             "OK" if ke >= 0 else "NO",
             "Invio visto" if ke >= 0
             else "⛔ nemmeno la tastiera funziona piu': il danno e' piu' largo "
                  "di quel che §4.6 descrive")

    # ---- T7: la riga che dichiara il ripiego -------------------------------
    # ⛔ E l'atteso dipende dal MONDO, non e' fisso: se il rilascio e' arrivato
    #    (cura presente) non c'e' nessun ripiego da dichiarare, e pretendere la
    #    riga sarebbe scrivere l'atteso del mondo col difetto vivo.
    if "NON PARTE: era premuto su un" in ini:
        caso("T7 il rilascio impossibile e' DICHIARATO nel registro", "OK",
             "la riga c'e': il registro NON dice «fatto» mentre il desktop "
             "resta bloccato")
    elif s >= 0:
        caso("T7 il rilascio impossibile e' DICHIARATO nel registro", "OK",
             "⭐ la riga non c'e' — ed e' giusto: il rilascio e' ARRIVATO, "
             "quindi non c'era nessun ripiego da dichiarare")
    else:
        caso("T7 il rilascio impossibile e' DICHIARATO nel registro", "NO",
             "⛔ il rilascio non e' arrivato E il registro tace: e' il verde "
             "che non e' vero (`CODER.md` §4.6)")

    return stampa(a, casi)


def stampa(a, casi):
    print(f"\n== 06-b33 §7.1 · giudizio «{a.etichetta}» · modo {a.modo}")
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
    if a.esiti:
        with open(a.esiti, "a", encoding="utf-8") as f:
            f.write(json.dumps({"etichetta": a.etichetta, "modo": a.modo,
                                "scena": a.scena, "casi": casi},
                               ensure_ascii=False) + "\n")
        print(f"   esiti: {a.esiti}")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
