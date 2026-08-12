#!/usr/bin/env python3
"""02-pam-i3.py — ⛔ LE TRE COSE CHE LA CURA DI §1.10 NON DEVE AVER ROTTO.

    python3 02-pam-i3.py --caso <secondo|ban|ban-dopo-riavvio|morto|insieme|libera>

===========================================================================
⛔ PERCHE' ESISTE, SEPARATO DA `02-pam-fermo.py`

`02-pam-fermo.py` misura **quanto sta fermo chi non si autentica**, ed e' il
numero per cui la cura si fa.  ⛔ Ma una cura che facesse crollare quel numero
**rompendo l'autenticazione** sarebbe il peggior scambio possibile, e il
mandato lo nomina per primo:

    «Un aiutante che risponde "si'" per un messaggio smarrito, un tempo scaduto
     o un processo morto e' **I3 violato**, ed e' il difetto peggiore che questo
     lavoro possa produrre.  Progetta perche' il **fallimento sia un no**, non
     un forse.»

⇒ Questo file prende **il caso concreto** invece dell'argomento: si ammazza
  l'aiutante e si presenta la parola d'ordine **GIUSTA**.

⛔ E prende anche le due cose che §1.10 impone di non muovere, perche' la cura
   le ha toccate tutt'e due nel codice:

   · **il secondo fisso** di §4.4-bis — `attesa-verdetto` adesso aspetta DUE
     cose invece di una (l'orologio e la risposta), e l'ordine fra le due non
     e' garantito;
   · **il conto per indirizzo** di §4.4-bis — il `segna_fallito()` si e'
     **spostato**, da `tratta_credenziali()` a `rcp_verdetto()`, perche' e'
     li' che adesso esiste il fatto «un tentativo e' fallito».  ⚠ Uno
     spostamento e' precisamente il tipo di modifica che si legge bene e non
     fa niente — la forma che il banco **B5** ha gia' trovato una volta, con
     il contatore che valeva sempre 1.

===========================================================================
⛔ I SEI CASI, E L'ATTESO DI CIASCUNO, SCRITTO PRIMA

  secondo            parola GIUSTA          -> `AMMESSO`, e **>= 1000 ms**
                     parola SBAGLIATA       -> `RESPINTO(0x07)`, e **>= 1000 ms**
                     ⛔ il secondo vale anche per l'ammesso, o la distinzione
                        che §4.4 vieta di scrivere nel motivo si leggerebbe
                        col cronometro

  ban                tre parole sbagliate con **tre nomi utente diversi**
                     (§4.4-bis: il nome non conta, tre nomi contano tre), poi
                     il quarto tentativo con la parola **GIUSTA**
                     -> ⛔ `RESPINTO(0x08 TROPPI_TENTATIVI)`.
                     ⭐ E' la prova che distingue un ban da un contatore: chi
                        ha la parola giusta entrerebbe, se fosse un contatore

  ban-dopo-riavvio   dopo che il server e' stato spento e riacceso, la parola
                     GIUSTA -> ⛔ ancora `0x08`.  Invariante **I7**: la
                     protezione sta nel programma, non in una memoria che un
                     riavvio porta via

  morto              ⛔ l'aiutante e' stato AMMAZZATO, e si presenta la parola
                     **GIUSTA** -> deve arrivare `RESPINTO`, mai `AMMESSO`.
                     ⚠ E' il caso per cui esiste questo file

  insieme            ⛔ DUE parole sbagliate nello STESSO istante — e sono due
                     e non tre, perche' al terzo scatterebbe il ban.  Se i due
                     nipoti lavorano in parallelo il muro dura quanto il PIU'
                     LENTO (~2 s); se facessero la fila durerebbe la SOMMA
                     (~4 s).  ⭐ Chiude la `[?]` che `aiutante.h` dichiara

  libera             lo sblocco (§4.4-bis, la seconda via d'uscita) e una
                     entrata con la parola giusta: ⭐ e' il **controllo
                     positivo** di tutti i casi qui sopra — «lo strumento sa
                     far entrare qualcuno?»  Senza, un `RESPINTO` ovunque
                     sarebbe verde per la ragione sbagliata

⛔ E ogni caso stampa `OK`/`NO` con accanto il numero che ha letto, non un
   giudizio: chi rilegge il registro deve poter rifare il conto.
"""
import argparse
import asyncio
import importlib.util
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
# ⚠ Il nome del file ha dei trattini, quindi non e' un nome di modulo: si carica
#   dal percorso.  ⛔ E si carica il PROPRIO banco, non quello di qualcun altro:
#   una dipendenza da `01-b3-cliente.py` legherebbe la certificazione di questo
#   file a byte che non sono miei.
_spec = importlib.util.spec_from_file_location(
    "pamfermo", os.path.join(QUI, "02-pam-fermo.py"))
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)


async def tentativo(a, utente, parola):
    """Una connessione, una `CREDENZIALI`, e quel che torna.

    Restituisce (nome, motivo, ms).  ⛔ Non solleva su `RESPINTO`: il rifiuto
    e' la misura, non un incidente."""
    from contextlib import AsyncExitStack
    async with AsyncExitStack() as pila:
        cli = await F.apri(pila, a.indirizzo, a.porta, "/rcp/1")
        await F.fino_a_eccomi(cli)
        t0 = time.monotonic()
        cli.manda(F.inquadra(F.T["CREDENZIALI"], F.s(utente) + F.s(parola)))
        try:
            nome, corpo = await F.attendi(cli, None, attesa=40)
        except (F.Caduta, asyncio.TimeoutError) as e:
            return ("CADUTA", None, (time.monotonic() - t0) * 1000, str(e))
        ms = (time.monotonic() - t0) * 1000
        motivo = corpo[0] if (nome == "RESPINTO" and corpo) else None
        return (nome, motivo, ms, None)


def dillo(ok, testo):
    print(f"   {'⭐ OK' if ok else '⛔ NO'}  {testo}")
    return 0 if ok else 1


async def principale(a, parola):
    male = 0
    nome_motivo = F.MOTIVI

    if a.caso == "secondo":
        print("== il secondo fisso di §4.4-bis, e vale ANCHE per l'ammesso")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "AMMESSO" and ms >= 1000,
                      f"parola GIUSTA -> {n} in {ms:.0f} ms "
                      f"(atteso AMMESSO, >= 1000)")
        await asyncio.sleep(0.5)
        n, m, ms, err = await tentativo(a, a.utente, "questa-e-sbagliata")
        male += dillo(n == "RESPINTO" and m == 0x07 and ms >= 1000,
                      f"parola SBAGLIATA -> {n}"
                      f"({nome_motivo.get(m, m)}) in {ms:.0f} ms "
                      f"(atteso RESPINTO 0x07, >= 1000)")
        # ⛔ E si ripulisce: un fallito lasciato in eredita' al caso dopo
        #    falserebbe il conto di chi viene dopo.
        print(f"   ⚠ sblocco DICHIARATO: {F.sblocca(a.socket, a.indirizzo)}")

    elif a.caso == "ban":
        print("== §4.4-bis: tre falliti dallo stesso indirizzo, con TRE NOMI "
              "DIVERSI")
        print(f"   ⚠ sblocco DICHIARATO, per partire da uno stato noto: "
              f"{F.sblocca(a.socket, a.indirizzo)}")
        for i, u in enumerate(("prova", "prova2", "nessuno-di-questi"), 1):
            n, m, ms, err = await tentativo(a, u, "questa-e-sbagliata")
            print(f"   -- fallito {i}/3 (utente «{u}»): {n}"
                  f"({nome_motivo.get(m, m)}) in {ms:.0f} ms")
            male += dillo(n == "RESPINTO" and m == 0x07,
                          f"   il {i}° e' un CREDENZIALI_ERRATE, non gia' un ban")
            await asyncio.sleep(0.4)
        print("== e il QUARTO, con la parola GIUSTA")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "RESPINTO" and m == 0x08,
                      f"parola GIUSTA -> {n}({nome_motivo.get(m, m)}) in "
                      f"{ms:.0f} ms  (atteso RESPINTO 0x08 TROPPI_TENTATIVI: "
                      f"⭐ e' la prova che distingue un ban da un contatore)")

    elif a.caso == "ban-dopo-riavvio":
        print("== I7: il ban sopravvive al riavvio del server")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "RESPINTO" and m == 0x08,
                      f"dopo il riavvio, parola GIUSTA -> {n}"
                      f"({nome_motivo.get(m, m)})  (atteso 0x08)")

    elif a.caso == "morto":
        print("== ⛔ I3: l'aiutante e' morto, e si presenta la parola GIUSTA")
        print("   ⚠ Se qui comparisse AMMESSO, la cura avrebbe comprato "
              "velocita' con la guardia.")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "RESPINTO",
                      f"parola GIUSTA con l'aiutante morto -> {n}"
                      f"({nome_motivo.get(m, m)}) in {ms:.0f} ms  "
                      f"(atteso RESPINTO, MAI AMMESSO)")
        male += dillo(ms >= 1000,
                      f"   e il secondo fisso c'e' lo stesso ({ms:.0f} ms): un "
                      f"rifiuto istantaneo direbbe col cronometro quel che il "
                      f"motivo non dice")

    elif a.caso == "insieme":
        # ⛔⭐ DUE CHE SBAGLIANO LA PAROLA NELLO STESSO ISTANTE.
        #
        # `aiutante.h` dichiara un secondo guadagno oltre a quello misurato da
        # `02-pam-fermo.py`: **due che entrano insieme non fanno la fila**,
        # perche' i nipoti sono due processi.  ⚠ Una cosa dichiarata e non
        # misurata e' una `[?]`, e questo caso la chiude o la lascia aperta.
        #
        # ⛔ L'atteso, scritto prima: se i due vanno in parallelo il muro dura
        #    quanto il PIU' LENTO dei due (~2 s); se fanno la fila dura la
        #    SOMMA (~4 s).  I due numeri non si possono confondere.
        # ⚠ E sono DUE e non tre: al terzo scatterebbe il ban (§4.4-bis), e si
        #   misurerebbe un rifiuto istantaneo invece di PAM.
        print("== due parole sbagliate nello stesso istante: fila o parallelo?")
        print(f"   ⚠ sblocco DICHIARATO, per partire da uno stato noto: "
              f"{F.sblocca(a.socket, a.indirizzo)}")
        t0 = time.monotonic()
        r1, r2 = await asyncio.gather(
            tentativo(a, "prova", "questa-e-sbagliata"),
            tentativo(a, "prova2", "questa-e-sbagliata"))
        tot = (time.monotonic() - t0) * 1000
        print(f"   -- il primo:  {r1[0]}({nome_motivo.get(r1[1], r1[1])}) in {r1[2]:.0f} ms")
        print(f"   -- il secondo:{r2[0]}({nome_motivo.get(r2[1], r2[1])}) in {r2[2]:.0f} ms")
        piu_lento = max(r1[2], r2[2])
        somma = r1[2] + r2[2]
        male += dillo(r1[1] == 0x07 and r2[1] == 0x07,
                      "tutt'e due sono CREDENZIALI_ERRATE (0x07): PAM e' stata "
                      "davvero interrogata due volte")
        male += dillo(tot < somma * 0.75,
                      f"il muro totale e' {tot:.0f} ms — il piu' lento dei due "
                      f"e' {piu_lento:.0f}, la somma sarebbe {somma:.0f}.  "
                      f"⭐ In parallelo, non in fila")
        print(f"   ⚠ sblocco DICHIARATO, per non lasciare il campo sporco: "
              f"{F.sblocca(a.socket, a.indirizzo)}")

    elif a.caso == "libera":
        print("== il controllo positivo: lo sblocco (§4.4-bis) e una entrata vera")
        r = F.sblocca(a.socket, a.indirizzo)
        print(f"   -- sblocco: {r}")
        male += dillo(r.startswith("TOLTO") or r.startswith("NON-BANNATO"),
                      f"il comando di sblocco ha risposto: {r}")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "AMMESSO",
                      f"e con la parola GIUSTA si entra: {n} in {ms:.0f} ms  "
                      f"⭐ senza questo, ogni RESPINTO qui sopra sarebbe verde "
                      f"per la ragione sbagliata")

    print(f"\n== {'⭐ tutto come atteso' if male == 0 else f'⛔ {male} controlli fuori posto'}")
    return 0 if male == 0 else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7531)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola-file", required=True)
    p.add_argument("--socket", default="")
    p.add_argument("--caso", required=True,
                   choices=["secondo", "ban", "ban-dopo-riavvio", "morto",
                            "insieme", "libera"])
    a = p.parse_args()
    if F.AIOQUIC:
        print(f"   ⛔ «aioquic» non c'e': {F.AIOQUIC}")
        sys.exit(2)
    parola = F.parola_dal_file(a.parola_file)
    try:
        sys.exit(asyncio.run(principale(a, parola)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
