#!/usr/bin/env python3
"""06-b40-isola.py — ⛔ i TRE file dell'isola `0x02` parlano la lingua di oggi?

    python3 06-b40-isola.py [cartella]

    uscita 0  chi scrive e i due che leggono sono d'accordo, e le versioni
              vecchie le rifiutano tutt'e due
    uscita 1  ⛔ NO — e si dice quale coppia non si capisce
    uscita 2  il banco non si e' potuto far girare

---------------------------------------------------------------------------
⛔ L'ISOLA, E PERCHE' ERA PERICOLOSA PROPRIO PERCHE' GALLEGGIAVA

Il 21 agosto 2026 `RCP.md` §11.1 e' passato a `RCPREG 0x00 0x03`.  `01-b3` e
`01-b4` sono andati insieme — quella meta' la tiene `06-b38-registratore.py`.

⛔ Ma **tre altri file conoscevano il formato**, e sono rimasti a `0x02`:

    banchi/02-filo-cliente.py       scrive
    banchi/02-filo-validatore.py    legge (ed e' il SECONDO arbitro del filo)
    banchi/04-b20-desktop-vero.py   legge (il giudice della shell sul vero)

⚠ E **non si rompeva niente**, ed e' il punto: `04-b20-lancia.sh` fa scrivere
  al primo e leggere al terzo, quindi i tre andavano d'accordo **fra loro**.
  Un'isola coerente non da' nessun sintomo.  ⛔ Ma l'albero portava due formati
  vivi sotto una specifica sola — la condizione esatta del difetto del 12
  agosto, solo piu' grande — e la miccia era gia' posata:
  `04-b20-lancia.sh:105` copia `01-b3-cliente.py` nello stesso albero.

⭐ **E questo banco non prova il filo**: prova che i tre si capiscono, e che
   quando NON dovrebbero capirsi (una versione vecchia) lo dicono tutti e due
   allo stesso modo.  E' la sola cosa che nessuno dei tre sa dire di se'.

---------------------------------------------------------------------------
⛔ QUEL CHE QUESTO BANCO **NON** PROVA

  · **non prova il prodotto**: qui la traccia e' costruita, non catturata.  Il
    giro vero — `02-filo-cliente.py` contro un server acceso, e la stessa
    traccia data ai due lettori — vuole la macchina di prova;
  · **non prova i pixel**: `04-b20-desktop-vero.py` qui si ferma alla lettura
    dei blocchi.  Il suo giudizio sulla shell e' `--certifica`, e sta da se'.
"""
import importlib.util
import io
import os
import struct
import sys

QUI = os.path.dirname(os.path.abspath(__file__))


def porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def giudica(val, percorso):
    """`(codice, frase)` da `02-filo-validatore.valida()`.

    ⛔ Quel file ALZA invece di tornare 2, e il codice lo mette il suo `main`:
       qui si rifa' la stessa corrispondenza, in un posto solo — e la si nomina,
       perche' due traduzioni della stessa eccezione in due file sono due
       traduzioni che divergono.
    """
    try:
        codice, _ = val.valida(percorso, stampa=False)
        return codice, ""
    except val.Malformata as e:
        return 2, str(e)
    except val.NonConforme as e:
        return 1, str(e)
    except val.NienteDaGiudicare as e:
        return 3, str(e)


def main():
    dove = (sys.argv[1] if len(sys.argv) > 1
            else os.path.join(QUI, "b40-isola"))
    os.makedirs(dove, exist_ok=True)
    bene = 0

    print("== 1. si importano i tre file dell'isola")
    try:
        cli = porta("filo_cliente", "02-filo-cliente.py")
        val = porta("filo_validatore", "02-filo-validatore.py")
        b20 = porta("b20", "04-b20-desktop-vero.py")
        f24 = porta("f24", "02-filo-fotogramma.py")
    except Exception as e:                                    # noqa: BLE001
        print(f"   ⛔ non si importano: {type(e).__name__}: {e}")
        return 2
    for nome, m in (("02-filo-cliente", cli), ("02-filo-validatore", val),
                    ("04-b20-desktop-vero", b20)):
        print(f"   {nome:<22s} magia {m.MAGIA}  blocco {m.BLOCCO} "
              f"({struct.calcsize(m.BLOCCO)} byte)")

    # ⛔ E le costanti si CONFRONTANO, ma non basta e va detto: due costanti
    #    uguali non sono un formato giusto (e' la stessa riga di
    #    `06-b38-registratore.py`).  Serve un file vero, scritto e riletto.
    print("\n== 2. le tre magie sono la stessa?")
    magie = {cli.MAGIA, val.MAGIA, b20.MAGIA}
    if len(magie) != 1:
        print(f"   ⛔ NO: {magie} — l'isola non e' rientrata")
        bene = 1
    else:
        print(f"   {magie.pop()} in tutti e tre")
    misure = {struct.calcsize(m.BLOCCO) for m in (cli, val, b20)}
    if len(misure) != 1:
        print(f"   ⛔ le misure del blocco non coincidono: {misure}")
        bene = 1

    # ── 3. una traccia VERA, scritta dal registratore di `02-filo-cliente` ──
    print("\n== 3. si scrive una traccia con CHI SCRIVE dell'isola")
    sessione = (val.SERVER, val.CONTROLLO, cli.CONTINUA, 0,
                struct.pack("!HI", 0x0007, 0))
    fotogramma = f24.intestazione() + b"\x00" * 512
    blocchi = [
        # (verso, canale, stream, carico, oscurati, fine, istante)
        (val.CLIENT, 0x00, 0, struct.pack("!HI", 0x0001, 0), [],
         cli.CONTINUA, 0),
        (val.SERVER, 0x00, 0, sessione[4], [], cli.CONTINUA, 10),
        (val.SERVER, 0x03, 8, fotogramma, [], cli.FIN, 40),
    ]
    traccia = os.path.join(dove, "isola.rcpreg")
    n = cli.scrivi_registrazione(traccia, blocchi)
    with io.open(traccia, "rb") as f:
        primi = f.read(16)
    print(f"   {traccia}")
    print(f"   {n} blocchi · magia sul disco: {primi[:8]} · orologio "
          f"{primi[12]}")

    # ── 4. i DUE lettori la leggono ────────────────────────────────────────
    print("\n== 4. i due lettori dell'isola la leggono")
    print("   ⛔ atteso, dichiarato PRIMA: l'arbitro esce 0, e il giudice della")
    print("      shell trova 1 flusso video con dentro l'intestazione di §6.2")
    # ⛔ `valida()` NON torna un codice d'uscita: torna `(codice, conti)` e
    #    ALZA `Malformata`.  Il 2 lo produce il `main` di quel file.  ⚠ La
    #    prima stesura di questo banco leggeva la tupla come se fosse un
    #    numero, e dichiarava rotta un'isola sana: un difetto di QUESTO file
    #    con la faccia di un difetto degli altri tre.
    esito, _ = giudica(val, traccia)
    print(f"   02-filo-validatore.valida -> {esito}")
    if esito != 0:
        print("   ⛔ l'arbitro dell'isola NON legge quel che l'isola scrive")
        bene = 1

    try:
        flussi = b20.blocchi_video(traccia)
    except Exception as e:                                    # noqa: BLE001
        print(f"   ⛔ `04-b20-desktop-vero.py` non la legge: "
              f"{type(e).__name__}: {e}")
        return 1
    print(f"   04-b20-desktop-vero.blocchi_video -> {len(flussi)} flussi, "
          f"{sum(len(d) for _, d in flussi)} byte")
    if len(flussi) != 1 or len(flussi[0][1]) != len(fotogramma):
        print("   ⛔ il giudice della shell non ritrova il fotogramma intero")
        bene = 1

    # ── 5. ⛔ E LE VERSIONI VECCHIE: LE RIFIUTANO TUTT'E DUE? ───────────────
    #    §11.1 lo chiede per nome, e senza questo passo la riga che rifiuta
    #    resterebbe un ramo che nessuno fa girare.
    print("\n== 5. ⛔ e i formati di ieri li rifiutano tutt'e due?")
    print("   ⛔ atteso, dichiarato PRIMA: `0x01` e `0x02` ⇒ l'arbitro esce 2")
    print("      e il giudice della shell ALZA — ⚠ non «zero flussi», che")
    print("      sarebbe «il desktop era vuoto»")
    for etichetta, magia in (("0x01", val.MAGIA_V1), ("0x02", val.MAGIA_V2)):
        vecchia = os.path.join(dove, f"isola-{etichetta}.rcpreg")
        val.scrivi_reg(vecchia,
                       [sessione,
                        (val.SERVER, val.VIDEO, cli.FIN, 8, fotogramma)],
                       magia=magia)
        e_val, detto = giudica(val, vecchia)
        alzato = None
        try:
            b20.blocchi_video(vecchia)
        except ValueError as e:
            alzato = str(e)
        except Exception as e:                                # noqa: BLE001
            alzato = f"⚠ {type(e).__name__}: {e}"
        print(f"   {etichetta}: arbitro -> {e_val} ({detto[:48]}…) · "
              f"giudice della shell -> "
              + ("ALZA" if alzato else "⛔ NON alza"))
        if "vecchi" not in detto.lower() and "versione" not in detto.lower() \
                and "agosto" not in detto.lower():
            print(f"      ⚠ l'arbitro esce {e_val} ma senza nominare la "
                  f"VERSIONE: «file rotto» e «altra versione» hanno due cure "
                  f"diverse")
            bene = 1
        if e_val != 2:
            print(f"      ⛔ l'arbitro doveva uscire 2 e ha detto {e_val}")
            bene = 1
        if not alzato:
            print("      ⛔ il giudice della shell l'ha letta di traverso: "
                  "leggerebbe blocchi scivolati e direbbe qualcosa su byte "
                  "che nessuno ha scritto")
            bene = 1
        elif "vecchia" not in alzato.lower() and "versione" not in alzato.lower():
            print(f"      ⚠ alza, ma senza nominare la VERSIONE: «{alzato[:70]}»")
            print("        ⛔ «file rotto» e «altra versione» hanno due cure "
                  "diverse")
            bene = 1

    print("\n== 6. Esito")
    if bene == 0:
        print("   ⭐ l'isola e' rientrata: chi scrive e i due che leggono")
        print("      parlano `RCPREG 0x00 0x03`, e le versioni di ieri le")
        print("      rifiutano tutt'e due nominandole.")
    else:
        print("   ⛔ l'isola NON e' rientrata: sopra c'e' quale coppia non si")
        print("      capisce.  ⚠ E il sintomo, quando arrivera', sara' «la")
        print("      registrazione e' malformata» su un filo sanissimo.")
    return bene


if __name__ == "__main__":
    sys.exit(main())
