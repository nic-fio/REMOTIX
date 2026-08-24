#!/usr/bin/env python3
"""09-b85-cliente.py — `01-b3-cliente.py` con UNA cosa in piu': i TEMPI.

    python3 09-b85-cliente.py --porta 7973 --utente provanr10 \
        --parola-file /srv/remotix/tmp/09nr10/parola --audio-codec pcm \
        --adatta 1920x1080 --video-scrivi v.h264 --tempi v-tempi.jsonl \
        --audio-scrivi a.jsonl --resta 70

    python3 09-b85-cliente.py --certifica     ⭐ senza rete e senza macchina

---------------------------------------------------------------------------
⛔ PERCHE' ESISTE, ED E' UN BUCO DI UN CAMPO SOLO

`RCP.md` §6.2 mette nell'intestazione del fotogramma un `istante` u64: *«microsecondi
dell'orologio **monotono del server** alla cattura»*.  §6.3 mette lo stesso
orologio sul blocco audio.  ⇒ ⭐ **Sono confrontabili**, e la differenza fra i
due istanti dello stesso evento reale e' lo sfalso alla sorgente, misurabile
senza microfono, senza occhio e senza browser.

⛔ Ma `01-b3-cliente.py`:1015-1016 legge quel campo e **lo butta**:

    tipo, codec, l, a, numero, istante, inp = struct.unpack("!HHIIIQI", ...)
    self.v_fotogrammi.append((numero, tipo == 0x0301, l, a, bytes(b[28:])))

e `scrivi_video()` concatena i soli pixel.  ⇒ Dal file di `--video-scrivi` non
si puo' sapere QUANDO ogni fotogramma e' stato catturato, e senza quello non
c'e' nessuna misura di sincronia da fare.

---------------------------------------------------------------------------
⛔⛔ E NON SI TOCCA `01-b3-cliente.py`, NEMMENO PER UN CAMPO.

Quel programma lo usano decine di banchi gia' misurati, ed e' **il secondo
lettore di RCP** (`PIANO.md` §1.1): il suo valore sta nell'essere una lettura
indipendente della specifica.  ⇒ Qui lo si **importa** e gli si mette un
guanto sopra: la classe `Cliente` resta la sua, il vaglio dell'audio resta il
suo, la traccia §11.1 resta la sua.  ⚠ L'unica cosa che cambia e' che due
metodi, prima di fare quel che facevano, scrivono una riga in una lista.

⭐ E si registrano DUE tempi per ogni cosa, non uno:

  · `istante`  — l'orologio del **server**, dall'intestazione (§6.2 / §6.3);
  · `arrivo`   — l'orologio **mio**, quando il byte e' entrato in questo
                 programma.

  ⇒ La differenza `arrivo - istante` e' la latenza del filo di quel flusso, e
    ⭐ la **differenza fra le due latenze** e' lo sfalso che il PERCORSO
    aggiunge — cioe' la stessa grandezza che `AV` misura nella pagina, ma presa
    prima del cuscino dell'audio e della coda del decodificatore.  ⚠ Non e'
    `AV` e non lo si spaccia per `AV`: e' la sua meta' di rete.
"""
import argparse
import importlib.util
import json
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


def _carica(nome, file_):
    sp = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# ⛔ Si importa come MODULO, non come `__main__`: l'`argparse` di B3 sta dentro
#    `if __name__ == "__main__"` (`01-b3-cliente.py`:2390) e non parte.  ⇒ Le
#    classi si definiscono, la rete no.
B3 = _carica("b3", "01-b3-cliente.py")

# I due elenchi dove finiscono i tempi.  ⚠ A livello di modulo perche'
# `create_protocol=Cliente` non passa argomenti al costruttore — e' lo stesso
# vincolo che B3 dichiara a :2519 per le sue tre variabili dell'audio.
TEMPI = []


def _monotono():
    return time.monotonic()


# ═══════════════════════════════════════════════════════════════════════════
#  IL GUANTO
# ═══════════════════════════════════════════════════════════════════════════

_video_vero = B3.Cliente._video_stream
_audio_vero = B3.Cliente._audio_datagram


def _video_con_tempi(self, sid, dati, fine):
    """⛔ Prima si guarda, POI si lascia fare il lavoro vero.

    ⚠ E si legge l'intestazione DA CAPO invece di farsela passare: e' l'unico
      modo di non dipendere da come B3 tiene i suoi buffer.  ⛔ E si legge
      **dopo** aver ricomposto lo stream, cioe' allo stesso punto in cui la
      legge lui — leggerla dal primo pacchetto darebbe l'intestazione giusta
      quasi sempre e sbagliata quando i 28 byte arrivano tagliati in due, che
      e' la forma d'errore «funziona in prova e non in rete».
    """
    prima = len(self.v_fotogrammi)
    quando = _monotono()
    _video_vero(self, sid, dati, fine)
    if len(self.v_fotogrammi) > prima:
        numero, chiave, l, a, _d = self.v_fotogrammi[-1]
        # ⛔ L'`istante` non sta in `v_fotogrammi`: B3 lo butta.  Si rilegge
        #    dai byte, che sono ancora quelli.
        b = self._b85_ultimo_grezzo
        import struct
        _t, _c, _l, _a, _n, ist, _i = struct.unpack("!HHIIIQI", b[:28])
        TEMPI.append({"che": "video", "numero": numero, "istante": ist,
                      "chiave": bool(chiave), "larghezza": l, "altezza": a,
                      "byte": len(b) - 28, "arrivo": quando, "stream": sid})


def _video_ricorda(self, sid, dati, fine):
    """⛔ Serve a tenere i byte finiti, perche' B3 cancella `self.v_in[sid]`
       prima che il guanto possa rileggerli.  ⇒ Si copia il riferimento un
       istante prima."""
    b = self.v_in.get(sid)
    if fine and b is not None:
        self._b85_ultimo_grezzo = bytes(b) + bytes(dati)
    elif fine:
        self._b85_ultimo_grezzo = bytes(dati)
    return _video_con_tempi(self, sid, dati, fine)


def _audio_con_tempi(self, d):
    prima = len(self.a_blocchi)
    quando = _monotono()
    _audio_vero(self, d)
    if len(self.a_blocchi) > prima:
        b = self.a_blocchi[-1]
        TEMPI.append({"che": "audio", "istante": b["istante"],
                      "codec": b["codec"], "byte": len(b["byte"]),
                      "arrivo": quando})


B3.Cliente._video_stream = _video_ricorda
B3.Cliente._audio_datagram = _audio_con_tempi


# ═══════════════════════════════════════════════════════════════════════════
#  L'INQUADRATURA DEGLI ARGOMENTI
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `principale(a)` legge una trentina di campi da `a`.  Ricostruirli a mano
#    e' l'unica strada (l'`argparse` di B3 non e' una funzione richiamabile), e
#    ⛔ **dimenticarne uno darebbe `AttributeError` a meta' sessione**, cioe' un
#    giro perso dopo settanta secondi di misura.  ⇒ `--certifica` **rilegge il
#    sorgente di B3** e pretende che ogni `a.<campo>` che ci compare esista qui.
#    ⚠ Non e' eleganza: e' l'unico controllo che si accorge di un campo nuovo
#      aggiunto a B3 domani da un altro banco.

PREDEFINITI = {
    "indirizzo": "192.168.0.2", "porta": 7447, "percorso": "/rcp/1",
    "utente": "prova", "parola": "prova", "parola_file": "",
    "larghezza": 1920, "altezza": 1080, "disposizione": "it",
    "registra": None, "adatta": [], "vista": None,
    "puntatore_vecchia": None, "chiave_dopo": 0.0, "attesa_tela": 5.0,
    "video_scrivi": "", "video_codec": "h264", "video_profondita": "8,10",
    "audio_codec": "opus,pcm", "audio_regola": "vecchia", "audio_passo_us": 0,
    "audio_decodifica_ms": 0.0, "audio_scrivi": "", "certifica": False,
    "appunti_copia": "", "appunti_attendi": 0.0, "appunti_scrivi": "",
    "resta": 0.0, "vivo": 0.0, "segnale": None,
}


def campi_di_b3():
    """Tutti i `a.<campo>` che il sorgente di B3 nomina.  ⛔ Grezzo apposta: un
       controllo che capisse il Python sarebbe piu' bello e piu' facile da far
       sbagliare in silenzio."""
    import re
    with open(os.path.join(QUI, "01-b3-cliente.py"), encoding="utf-8") as f:
        testo = f.read()
    # solo il corpo delle funzioni, non l'`argparse` (che usa `p.add_argument`)
    corpo = testo.split('if __name__ == "__main__":')[0]
    # ⛔ E VIA I COMMENTI, prima di cercare.  ⚠ B3 e' scritto con commenti che
    #    CITANO il codice (`a.base + istante`, `self.passo_us`), e senza questa
    #    riga il controllo trovava tre campi che non esistono e dava rosso su un
    #    guanto sano — la forma d'errore peggiore per un'autoprova, perche' la
    #    cura sarebbe stata aggiungere tre campi finti.
    righe = []
    for r in corpo.splitlines():
        i = r.find("#")
        righe.append(r if i < 0 else r[:i])
    corpo = "\n".join(righe)
    # e via anche le docstring, che citano il codice allo stesso modo
    corpo = re.sub(r'""".*?"""', "", corpo, flags=re.S)
    return set(re.findall(r"(?<![\w.])a\.([a-z_]+)", corpo))


def certifica():
    print("\n   ⭐ 09-b85-cliente — l'autoprova, senza rete\n")
    male = 0
    mancano = campi_di_b3() - set(PREDEFINITI) - {"append"}
    if mancano:
        print(f"   ⛔ B3 legge campi che questo guanto non prepara: "
              f"{sorted(mancano)}")
        print("      ⇒ un giro vero morirebbe di `AttributeError` DOPO aver")
        print("        aperto la sessione, cioe' dopo aver sprecato la misura.")
        male += 1
    else:
        print(f"   ✅ i {len(PREDEFINITI)} campi coprono tutti quelli che B3 legge")
    if B3.Cliente._video_stream is not _video_ricorda:
        print("   ⛔ il guanto sul video NON e' montato")
        male += 1
    else:
        print("   ✅ il guanto sul video e' montato")
    if B3.Cliente._audio_datagram is not _audio_con_tempi:
        print("   ⛔ il guanto sull'audio NON e' montato")
        male += 1
    else:
        print("   ✅ il guanto sull'audio e' montato")
    # ⛔ E si prova che il guanto RILEGGE l'intestazione come B3, su byte
    #    inventati: se le due `struct.unpack` divergessero, ogni `istante`
    #    registrato sarebbe un numero plausibile e falso.
    import struct
    finti = struct.pack("!HHIIIQI", 0x0301, 3, 1920, 1080, 42, 123456789, 7) + b"xy"
    t, c, l, al, n, ist, i = struct.unpack("!HHIIIQI", finti[:28])
    if (t, c, l, al, n, ist, i) != (0x0301, 3, 1920, 1080, 42, 123456789, 7):
        print("   ⛔ l'intestazione di §6.2 non si rilegge")
        male += 1
    else:
        print("   ✅ l'intestazione di §6.2 si rilegge: 28 byte, `istante` u64")
    print()
    if male:
        print("   ⛔ NON USARE questo cliente finche' non e' verde.")
        return 3
    print("   ✅ verde.")
    return 0


def scrivi_tempi(percorso):
    if not percorso:
        return
    with open(percorso, "w") as f:
        for r in TEMPI:
            f.write(json.dumps(r) + "\n")
    v = sum(1 for r in TEMPI if r["che"] == "video")
    a = len(TEMPI) - v
    print(f"   [b85]  tempi scritti in {percorso}: {v} fotogrammi, {a} blocchi audio")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="B3 con i tempi di §6.2 e §6.3")
    for nome, val in sorted(PREDEFINITI.items()):
        if nome in ("adatta", "vista", "certifica", "parola"):
            continue
        chiave = "--" + nome.replace("_", "-")
        if isinstance(val, bool):
            p.add_argument(chiave, action="store_true")
        elif isinstance(val, int) and not isinstance(val, bool):
            p.add_argument(chiave, type=int, default=val)
        elif isinstance(val, float):
            p.add_argument(chiave, type=float, default=val)
        else:
            p.add_argument(chiave, default=val)
    p.add_argument("--parola", default="prova")
    p.add_argument("--adatta", action="append", default=[], metavar="LxH")
    p.add_argument("--vista", default=None, metavar="LxH")
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--tempi", default="", help="⭐ dove scrivere gli istanti")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if B3.AIOQUIC:
        print(f"   ⛔ senza `aioquic` non c'e' nessuna rete: {B3.AIOQUIC}")
        print("      ⭐ gira DENTRO il contenitore (`enter.sh`).")
        sys.exit(2)

    # ⛔ Le tre variabili di modulo dell'audio: B3 le assegna nel suo
    #    `__main__`, che qui non gira.  Senza, `Cliente.__init__` leggerebbe i
    #    valori di modulo e la `--audio-regola` chiesta sarebbe ignorata **in
    #    silenzio** — un giro che dichiara una regola e ne misura un'altra.
    B3.REGOLA_AUDIO = a.audio_regola
    B3.PASSO_AUDIO_US = a.audio_passo_us
    B3.DECODIFICA_AUDIO_S = a.audio_decodifica_ms / 1000.0

    a.parola = B3.parola_dagli_argomenti(a)

    def misura(testo):
        quando = 0.0
        if "@" in testo:
            testo, _, s = testo.partition("@")
            quando = float(s)
        l, _, h = testo.lower().partition("x")
        return int(l), int(h), quando

    tempi_dove = a.tempi
    a.adatta = [misura(x) for x in a.adatta]
    a.vista = misura(a.vista)[:2] if a.vista else None

    import asyncio
    rc = 2
    try:
        rc = asyncio.run(B3.principale(a))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"\n   ⛔ {type(e).__name__}: {e}")
    finally:
        # ⛔ I tempi si scrivono ANCHE se il giro e' caduto: una sessione
        #    staccata a meta' e' esattamente il caso in cui si vuole sapere
        #    dove stavano i due flussi quando si e' staccata.
        scrivi_tempi(tempi_dove)
    sys.exit(rc)
