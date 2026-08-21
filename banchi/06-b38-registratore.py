#!/usr/bin/env python3
"""06-b38-registratore.py — ⛔ il registratore di B3 e l'arbitro di B4 parlano la stessa lingua?

    python3 06-b38-registratore.py [cartella]

    uscita 0  la traccia che B3 scrive, B4 la sa leggere e giudicare
    uscita 1  ⛔ NO — e si dice su quale byte i due non sono d'accordo
    uscita 2  il banco non si e' potuto fare girare

---------------------------------------------------------------------------
⛔ IL DIFETTO CHE QUESTO BANCO ESISTE PER NON FAR TORNARE

Il **12 agosto 2026** il formato di `RCP.md` §11.1 e' passato a `RCPREG 0x00
0x02`: il blocco porta il campo `fine` e cresce da 16 a 17 byte.
`01-b4-validatore.py` ha imparato lo stesso giorno a **rifiutare** il formato
vecchio, com'e' giusto — §11.1: *«un validatore vecchio deve RIFIUTARE il
formato nuovo, non leggerlo di traverso»*.

⛔ **E `01-b3-cliente.py` ha continuato a scrivere `0x00 0x01` per quattro
   giorni.**  Da quel giorno ogni traccia di B3 usciva **2** dall'arbitro —
«registrazione malformata» — e le **cinque** chiamate `valida` di
`01-b3-lancia.sh` fallivano tutte, facendo uscire **1** il banco intero.

⚠ **Nessuno dei due programmi era rotto da solo**, ed e' il punto: il
  validatore faceva esattamente quel che la specifica gli chiede, e il
registratore scriveva un formato che era stato valido fino a quattro giorni
prima.  ⛔ Il difetto stava **fra** i due file, dove nessuna prova unitaria
guarda — e nessuno dei due poteva accorgersene da solo.

⭐ **E questo banco non prova il filo**: prova che i due banchi si capiscono.
   E' la sola cosa che nessuno dei due sa dire di se'.

---------------------------------------------------------------------------
⛔ E NON SI PROVA CON UNA COSTANTE, SI PROVA CON I BYTE

Confrontare `Registratore.MAGIA` con `MAGIA` del validatore sarebbe una prova
che passa anche il giorno in cui i due si accordano su un formato **sbagliato**:
due costanti uguali non sono un formato giusto.  ⇒ Qui si **scrive una traccia
vera** con il registratore di B3 e la si **fa giudicare** all'arbitro di B4.

⚠ E il cliente di B3 importa `aioquic`, che sul portatile non c'e': si importa
  il modulo con dei surrogati al posto di quella libreria, ⛔ e si dichiara —
  perche' cosi' si prova il **registratore**, non il cliente.  Il cliente
  contro un server vero e' un'altra misura, e la fa `06-b38-tela.sh`.
"""
import os
import struct
import subprocess
import sys
import types

QUI = os.path.dirname(os.path.abspath(__file__))
CLIENTE = os.path.join(QUI, "01-b3-cliente.py")
VALIDATORE = os.path.join(QUI, "01-b4-validatore.py")


def importa_il_cliente():
    """`01-b3-cliente.py` senza `aioquic`.  ⛔ E si dice che si e' fatto cosi'."""
    import importlib.util
    finti = ["aioquic", "aioquic.asyncio", "aioquic.asyncio.protocol",
             "aioquic.h3", "aioquic.h3.connection", "aioquic.h3.events",
             "aioquic.quic", "aioquic.quic.configuration",
             "aioquic.quic.events"]
    # ⛔⛔ E «c'e' aioquic?» SI CHIEDE A CHI LO SA, non a `sys.modules` — 21
    #     agosto 2026.
    #
    #     `"aioquic" in sys.modules` guarda i moduli **gia' importati**, e a
    #     questo punto del programma non ne ha importato nessuno: era **sempre
    #     falso**.  ⇒ Anche con `aioquic` installato per davvero questo banco
    #     (a) piantava i surrogati SOPRA la libreria vera e (b) stampava
    #     «SURROGATO».  ⚠ Cioe' la riga che il banco esiste per dichiarare —
    #     *«e si dichiara»* — diceva sempre la stessa cosa, e nessuno poteva
    #     accorgersene: una dichiarazione che non puo' cambiare valore non e'
    #     una dichiarazione.
    #
    # ⭐ `find_spec` risponde alla domanda vera: «si potrebbe importare?».
    try:
        vero = importlib.util.find_spec("aioquic") is not None
    except (ImportError, ValueError):
        vero = False
    if not vero:
        class Niente:
            pass
        for n in finti:
            sys.modules[n] = types.ModuleType(n)
        sys.modules["aioquic.asyncio"].connect = lambda *a, **k: None
        sys.modules["aioquic.asyncio.protocol"].QuicConnectionProtocol = Niente
        sys.modules["aioquic.h3.connection"].H3_ALPN = ["h3"]
        sys.modules["aioquic.h3.connection"].H3Connection = Niente
        sys.modules["aioquic.h3.events"].HeadersReceived = Niente
        sys.modules["aioquic.quic.configuration"].QuicConfiguration = Niente
        sys.modules["aioquic.quic.events"].QuicEvent = Niente
    spec = importlib.util.spec_from_file_location("b3_cliente", CLIENTE)
    mod = importlib.util.module_from_spec(spec)
    argv = sys.argv
    sys.argv = ["06-b38-registratore.py"]      # ⚠ il cliente legge argv
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod, vero


def s(t):
    b = t.encode("utf-8") if isinstance(t, str) else t
    return struct.pack("!H", len(b)) + b


def main():
    dove = (sys.argv[1] if len(sys.argv) > 1
            else os.path.join(QUI, "b38-registratore"))
    os.makedirs(dove, exist_ok=True)

    print("== 1. si importa il registratore di B3")
    try:
        b3, aioquic_vero = importa_il_cliente()
    except Exception as e:                       # noqa: BLE001
        print(f"   ⛔ «{CLIENTE}» non si importa: {type(e).__name__}: {e}")
        return 2
    print(f"   aioquic: {'vero' if aioquic_vero else '⚠ SURROGATO — si prova il '
                                                     'registratore, non il cliente'}")
    print(f"   magia dichiarata dal registratore: {b3.Registratore.MAGIA}")

    # ── 2. una traccia vera, scritta dal registratore di B3 ────────────────
    #    ⛔ La stessa strada che il cliente percorre contro un server: la
    #       stretta di mano, la parola OSCURATA (§11.1, §4.4), poi la tela.
    print("\n== 2. si scrive una traccia con il registratore di B3")
    import hashlib
    reg = b3.Registratore()
    reg.stream = 4                    # §4.2: il primo bidirezionale, non lo 0
    T = b3.T

    voci = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
            ("audio.codec", "opus,pcm"), ("appunti.testo", "si")]
    ciao = struct.pack("!HH", 1, len(voci))
    for n, v in voci:
        ciao += s(n) + s(v)
    reg.aggiungi(b3.CLIENT, b3.inquadra(T["CIAO"], ciao))

    ecc = struct.pack("!HH", 1, 2) + s("video.codec") + s("hevc") \
        + s("appunti.testo") + s("si")
    reg.aggiungi(b3.SERVER, b3.inquadra(T["ECCOMI"], ecc))

    utente, parola = "prova", "parola-di-prova"
    corpo = s(utente) + s(parola)
    b = b3.inquadra(T["CREDENZIALI"], corpo)
    ini = 6 + 2 + len(utente.encode()) + 2
    qua = len(parola.encode())
    reg.aggiungi(b3.CLIENT, b[:ini] + bytes([0x2A]) * qua + b[ini + qua:],
                 [(ini, qua, hashlib.sha256(parola.encode()).digest())])

    reg.aggiungi(b3.SERVER, b3.inquadra(T["AMMESSO"], b""))
    reg.aggiungi(b3.CLIENT, b3.inquadra(
        T["ATTACCA"], struct.pack("!IIII", 1264, 800, 1264, 800) + s("it")))
    reg.aggiungi(b3.SERVER, b3.inquadra(
        T["SESSIONE"],
        struct.pack("!B", 1) + struct.pack("!II", 1264, 800) + s("gnome")))
    # ⭐ e la strada nuova, che e' il motivo per cui questo banco esiste oggi
    reg.aggiungi(b3.CLIENT, b3.inquadra(T["ADATTA_TELA"],
                                        struct.pack("!II", 1600, 900)))
    reg.aggiungi(b3.SERVER, b3.inquadra(T["TELA"],
                                        struct.pack("!BBII", 1, 0, 1600, 900)))
    reg.aggiungi(b3.CLIENT, b3.inquadra(T["VISTA"],
                                        struct.pack("!II", 1600, 900)))

    traccia = os.path.join(dove, "b38-registratore.rcpreg")
    reg.scrivi(traccia)
    with open(traccia, "rb") as f:
        primi = f.read(8)
    print(f"   {traccia}")
    print(f"   {len(reg.blocchi)} blocchi · magia sul disco: {primi}")

    # ── 3. e l'arbitro di B4 la giudica ───────────────────────────────────
    print("\n== 3. l'arbitro di B4 la giudica")
    print("   ⛔ atteso, dichiarato PRIMA: uscita 0 — la traccia e' conforme,")
    print("      e la tela porta 1 coppia ADATTA_TELA/TELA chiusa")
    p = subprocess.run([sys.executable, VALIDATORE, traccia],
                       capture_output=True, text=True)
    testo = p.stdout + p.stderr
    for riga in testo.strip().splitlines():
        print(f"   | {riga}")

    # ── 4. ⭐⛔ E L'ALTRO VERSO: UN VALIDATORE **VECCHIO** DAVANTI AL FILE
    #        NUOVO — 21 agosto 2026, con il passaggio a `RCPREG 0x00 0x03`.
    #
    #  §11.1: *«un validatore vecchio deve RIFIUTARE il formato nuovo, non
    #  leggerlo di traverso»*.  ⛔ Il caso 46 di `01-b4-registrazioni.py` prova
    #  il verso facile — l'arbitro di OGGI davanti a un file di ieri.  Questo
    #  prova il verso che nessuno puo' provare senza costruirselo: **l'arbitro
    #  di IERI davanti al file di oggi**.
    #
    #  ⚠ E l'arbitro di ieri non esiste piu' in nessun albero: si FABBRICA, da
    #    una copia dell'arbitro di oggi rimessa alla magia `0x02` e al blocco da
    #    17 byte.  ⛔ Se non lo si fabbricasse, questa meta' della frase di
    #    §11.1 resterebbe una promessa — e la prima volta che serve, il 12
    #    agosto, e' costata quattro giorni.
    print("\n== 4. ⛔ e un validatore VECCHIO davanti a questo file NUOVO?")
    print("   ⛔ atteso, dichiarato PRIMA: uscita 2 (registrazione rotta) —")
    print("      ⚠ NON 0 e NON 1: leggerlo di traverso e dare un giudizio")
    print("      sarebbe la cosa peggiore delle tre")
    vecchio = os.path.join(dove, "01-b4-validatore-di-ieri.py")
    sorgente = open(VALIDATORE, encoding="utf-8").read()
    ancore = [('MAGIA = b"RCPREG\\x00\\x03"', 'MAGIA = b"RCPREG\\x00\\x02"'),
              ('BLOCCO = "!BBBIQIH"', 'BLOCCO = "!BBBQIH"'),
              ('MAGIA_V2 = b"RCPREG\\x00\\x02"', 'MAGIA_V2 = b"RCPREG\\x00\\x99"'),
              ("verso, canale, fine, istante, stream, lung, nosc = struct.unpack(",
               "istante = 0\n        verso, canale, fine, stream, lung, nosc = struct.unpack(")]
    # ⛔ L'ANCORA SI VERIFICA — la lezione di `04-b31` (G8, l'ancora scaduta):
    #    un guasto che non si innesta e' un verde che non vale niente, e va
    #    detto con la sua faccia invece di passare per un OK.
    for a, _ in ancore:
        if sorgente.count(a) != 1:
            print(f"   ?? l'ancora «{a[:40]}…» compare {sorgente.count(a)} volte:")
            print("      il validatore di ieri NON si fabbrica, e questo caso")
            print("      non prova niente.  ⛔ Non e' un verde: e' un banco rotto.")
            return 1
    for a, b_ in ancore:
        sorgente = sorgente.replace(a, b_, 1)
    open(vecchio, "w", encoding="utf-8").write(sorgente)
    pv = subprocess.run([sys.executable, vecchio, traccia],
                        capture_output=True, text=True)
    testo_v = (pv.stdout + pv.stderr).strip()
    for riga in testo_v.splitlines()[-4:]:
        print(f"   | {riga}")
    print(f"   l'arbitro di ieri esce {pv.returncode}")
    if pv.returncode != 2:
        print("   ⛔ UN VALIDATORE VECCHIO NON RIFIUTA IL FORMATO NUOVO.")
        print(f"      Esce {pv.returncode} invece di 2: se e' 0 o 1 sta")
        print("      GIUDICANDO byte scivolati di quattro, e il verdetto e' su")
        print("      un filo che nessuno ha scritto (§11.1).")
        return 1
    print("   ⭐ rifiutato con uscita 2, come §11.1 pretende: e' «un file di")
    print("      un'altra versione», non «un filo non conforme».")

    print("\n== 5. Esito")
    if p.returncode == 2 and "formato VECCHIO" in testo:
        print("   ⛔ E' TORNATO IL DIFETTO DEL 12-16 AGOSTO 2026: il")
        print("      registratore di B3 scrive un formato che l'arbitro di B4")
        print("      rifiuta.  ⚠ Nessuno dei due e' rotto da solo, e ogni giro")
        print("      di `01-b3-lancia.sh` fallira' le sue cinque validazioni.")
        return 1
    if p.returncode != 0:
        print(f"   ⛔ l'arbitro esce {p.returncode} su una traccia che il")
        print("      registratore di B3 ha appena scritto: i due non parlano la")
        print("      stessa lingua, e il difetto sta FRA i due file")
        return 1
    if "1 coppie ADATTA_TELA/TELA chiuse" not in testo:
        print("   ⛔ la traccia e' conforme ma l'arbitro non ha visto la coppia")
        print("      ADATTA_TELA/TELA: il denominatore della tela non torna, e")
        print("      «conforme» senza denominatore e' vero e vuoto (§1.9)")
        return 1
    print("   ⭐ la traccia che B3 scrive, B4 la legge e la giudica CONFORME —")
    print("      compresa la coppia ADATTA_TELA/TELA, che e' la strada nuova.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
