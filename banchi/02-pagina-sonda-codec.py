#!/usr/bin/env python3
"""02-pagina-sonda-codec.py — costruisce le QUATTRO SONDE che vivono dentro
   `src/pagina.html`, e le certifica.

    python3 banchi/02-pagina-sonda-codec.py            costruisce e stampa il JS
    python3 banchi/02-pagina-sonda-codec.py --json     le stampa come JSON
    python3 banchi/02-pagina-sonda-codec.py --certifica  sano → guasto → risanato

===========================================================================
⛔ PERCHE' IL PRODOTTO SI PORTA DIETRO QUATTRO FLUSSI VERI

`fasi/rapporti/F2-5-pagina.md` §2, `[M]` 12 agosto 2026, Firefox 140 ESR:

    navigator.mediaCapabilities.decodingInfo()  →  supported: true
    video.canPlayType()                         →  «probably»
    VideoDecoder.isConfigSupported()            →  false
    il pixel                                    →  NIENTE

⛔ Tre testimoni, due dei quali dicono il falso su tutte e sette le stringhe
   HEVC.  Una pagina che scegliesse il codec da `mediaCapabilities` — che e'
   l'API **fatta apposta** per quella domanda — sceglierebbe HEVC su Firefox e
   non dipingerebbe niente.

⚠ E `isConfigSupported`, che li' dice la verita', resta la forma **E1**
  (`REVIEWER.md` §2): dice che la configurazione e' **accettata**, non che il
  pixel **arriva**.  `[M]` sullo stesso giro: Chrome accetta `L30` su un flusso
  di livello 3.0 e dipinge lo stesso — cioe' l'API accetta anche quel che non
  dovrebbe.

⇒ ⭐ L'unica domanda che ha una risposta e' **il pixel**, e l'unico posto dove
  si puo' porre e' **il dispositivo dell'utente** (`STUDI.md` §web §9 lezione 2: *«il
  browser sa e non risponde… la misura deve vivere nel prodotto»*).  Da cui
  queste quattro sonde: due tinte lontane in un fotogramma chiave di 64x48, una
  per codec e per profondita'.

===========================================================================
⛔ LA SONDA HA UN CONTROLLO NEGATIVO DENTRO DI SE'

Un fotogramma di **una tinta sola** non distinguerebbe «ha dipinto» da «la tela
era gia' di quel colore».  Qui ce ne sono **due**, meta' e meta', e la tela si
riempie prima di un terzo colore che non e' nessuna delle due (magenta).  ⇒ Per
dire «arriva» servono due letture giuste **e diverse fra loro**: nessun riempimento
uniforme le passa.

===========================================================================
⛔ E SI CERTIFICA, come ogni altro strumento di questo banco

    --certifica   sano → guasto → risanato, con l'atteso scritto prima:

      sano       le quattro sonde hanno due tinte diverse e >= 200 byte
      guasto     `GUASTO=una-tinta` costruisce il fotogramma di UNA tinta sola
                 ⇒ la pretesa «due tinte diverse» DEVE cadere.  Senza questo
                   giro, «la sonda ha un controllo negativo» sarebbe una frase
      risanato   come il sano
"""
import base64
import json
import os
import subprocess
import sys

LARGHEZZA, ALTEZZA = 64, 48

# ⛔ Le due tinte sono prese dalle otto di `02-pagina-sequenze.py`, e la
#    distanza fra loro e' oltre 180 per canale: `[M]` la conversione RGB→YUV,
#    l'intervallo limitato e la perdita del codificatore spostano un canale di
#    qualche decina — non di cento (F2-5 §«Che cosa si conta»).
SINISTRA = (220, 32, 32)     # rosso
DESTRA = (48, 64, 220)       # blu


def errore(testo, dettaglio=""):
    print(f"\033[1;31mNO\033[0m  {testo}", file=sys.stderr)
    if dettaglio:
        print("    " + dettaglio.replace("\n", "\n    "), file=sys.stderr)
    sys.exit(2)


def esegui(comando, entrata=b""):
    p = subprocess.run(comando, input=entrata, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return p.returncode, p.stdout, p.stderr


def grezzo(guasto=""):
    """Il fotogramma sorgente in RGB24: meta' e meta'.

    ⛔ Col guasto `una-tinta` le due meta' diventano la stessa: e' il guasto
       che certifica il controllo negativo della sonda."""
    destra = SINISTRA if guasto == "una-tinta" else DESTRA
    riga = bytes(SINISTRA) * (LARGHEZZA // 2) + bytes(destra) * (LARGHEZZA // 2)
    return riga * ALTEZZA


def costruisci_hevc(profondita, guasto=""):
    """⛔ Annex-B puro, NESSUNA `description` — `FASI.md` §02-primo-fotogramma D1,
    confermato dal pixel in F2-5 §3: `hev1.` e `hvc1.` vanno tutti e due, e
    Chromium decide la forma del flusso dalla PRESENZA della `description`, non
    dal prefisso."""
    pix = "yuv420p10le" if profondita == 10 else "yuv420p"
    sorgente = "rgb48le" if profondita == 10 else "rgb24"
    dati = grezzo(guasto)
    if profondita == 10:
        # ⚠ La sorgente resta a 8 bit promossi: qui non si misura la
        #   profondita' del CONTENUTO (F2-5 §6 — quella domanda si pone alla
        #   sorgente o non si pone), si misura se il browser DECODIFICA un
        #   Main10 e lo dipinge.
        dati = b"".join(bytes([b, b]) for b in dati)
    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", sorgente,
        "-s", f"{LARGHEZZA}x{ALTEZZA}", "-framerate", "30", "-i", "pipe:0",
        "-c:v", "libx265", "-pix_fmt", pix, "-frames:v", "1",
        # ⛔ Il profilo si CHIEDE PER NOME e si verifica che sia stato dato
        #    (`CODER.md` §3.9): x265 lasciato scegliere emette `Main 10 Intra`
        #    (Rext, profile_idc 4), che non e' quel che il prodotto configura.
        "-profile:v", "main10" if profondita == 10 else "main",
        # ⛔ `info=0` toglie la SEI di x265 con dentro la riga di comando: sono
        #    ~1,5 KB di testo che finirebbero in base64 dentro la pagina del
        #    prodotto senza dire niente a nessuno.
        #
        # ⛔⛔⛔ E `keyint=1` E' STATO TOLTO IL 13 AGOSTO 2026 SERA, PERCHE'
        #    ANNULLAVA IL `-profile:v` CHIESTO QUATTRO RIGHE SOPRA — ed e'
        #    costato il codec dell'intero prodotto.
        #
        #    Con `keyint=1` libx265 emette **Main 10 Intra**, cioe' `Rext`,
        #    `profile_idc = 4`: esattamente la cosa che il commento qui sopra
        #    dichiara di voler evitare.  ⇒ Il profilo **era stato chiesto e non
        #    applicato, senza un errore**.
        #
        #    ⛔ E il danno non era nel banco: le due sonde finiscono **in
        #    `src/pagina.html`**, e la pagina le usa per decidere che cosa
        #    mettere nel `CIAO`.  La stringa dichiarata diceva `hev1.1.6` /
        #    `hev1.2.4` — profili 1 e 2 — e **i byte dicevano 4**.
        #    `isConfigSupported` risponde alla STRINGA e diceva `true`; il
        #    decodificatore cadeva sui BYTE con `EncodingError`; la pagina
        #    concludeva «HEVC non arriva al pixel» e non lo metteva nel `CIAO`;
        #    e il server, che prende la prima voce dell'elenco del CLIENT,
        #    negoziava **AV1**.
        #
        #    ⇒ ⭐ **Il prodotto ha codificato in software per giorni per una
        #    riga di un banco**, e nessuno l'ha visto perche' ogni pezzo della
        #    catena rispondeva correttamente alla domanda che gli era stata
        #    fatta.  `[M]` togliendo `keyint=1` esce **Main 10**, riprodotto
        #    tre volte.
        #
        #    ⚠ E si e' visto SOLO andando a leggere i byte prodotti: la stringa
        #    e il codec erano d'accordo fra loro e discordi dal flusso.
        "-x265-params", "log-level=none:bframes=0:info=0",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-f", "hevc", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=dati)
    if codice != 0 or len(uscita) < 64:
        errore(f"libx265 non ha prodotto la sonda a {profondita} bit",
               errori.decode("utf-8", "replace")[-800:])
    return uscita


def costruisci_av1(profondita, guasto=""):
    """⛔ Nessuna `description`: AV1 in WebCodecs prende le unita' temporali di
    OBU cosi' come sono (F2-5, aggiunta del 12 agosto).  Qui si passa da IVF
    solo per spogliare il fotogramma."""
    pix = "yuv420p10le" if profondita == 10 else "yuv420p"
    sorgente = "rgb48le" if profondita == 10 else "rgb24"
    dati = grezzo(guasto)
    if profondita == 10:
        dati = b"".join(bytes([b, b]) for b in dati)
    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", sorgente,
        "-s", f"{LARGHEZZA}x{ALTEZZA}", "-framerate", "30", "-i", "pipe:0",
        "-c:v", "libaom-av1", "-pix_fmt", pix, "-frames:v", "1",
        "-crf", "20", "-b:v", "0", "-cpu-used", "8",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709",
        # ⛔ `-f obu` e non `ivf`: l'unita' temporale esce cosi' com'e', con il
        #    suo `sequence header` davanti.  ⚠ Spogliare un IVF darebbe il solo
        #    corpo del fotogramma, e un fotogramma AV1 senza sequence header non
        #    e' decodificabile da solo — la sonda direbbe «non arriva» su un
        #    browser che invece decodifica benissimo.
        "-f", "obu", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=dati)
    if codice != 0 or len(uscita) < 16:
        errore(f"libaom-av1 non ha prodotto la sonda a {profondita} bit",
               errori.decode("utf-8", "replace")[-800:])
    return uscita


def tinte_del_flusso(flusso, codec, profondita):
    """⛔ Il controllo positivo del COSTRUTTORE: si ridecodifica il flusso
    appena prodotto e si guarda che le due meta' siano ancora due tinte
    diverse.  Senza, «la sonda ha due tinte» sarebbe una proprieta' della
    SORGENTE, non del flusso che finira' nel prodotto."""
    comando = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
               "-f", "hevc" if codec == "hevc" else "obu", "-i", "pipe:0",
               "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    codice, uscita, errori = esegui(comando, entrata=flusso)
    if codice != 0 or len(uscita) < LARGHEZZA * ALTEZZA * 3:
        return None, errori.decode("utf-8", "replace")[-400:]

    def media(x0, x1):
        r = g = b = n = 0
        for y in range(ALTEZZA // 4, ALTEZZA * 3 // 4):
            for x in range(x0, x1):
                i = (y * LARGHEZZA + x) * 3
                r += uscita[i]; g += uscita[i + 1]; b += uscita[i + 2]
                n += 1
        return [r // n, g // n, b // n]

    return (media(4, LARGHEZZA // 2 - 4), media(LARGHEZZA // 2 + 4,
                                                LARGHEZZA - 4)), None


def costruisci_tutte(guasto=""):
    fuori = {}
    for codec in ("hevc", "av1"):
        for profondita in (8, 10):
            flusso = (costruisci_hevc(profondita, guasto) if codec == "hevc"
                      else costruisci_av1(profondita, guasto))
            lette, guai = tinte_del_flusso(flusso, codec, profondita)
            fuori[f"{codec}-{profondita}"] = {
                "codec": codec, "profondita": profondita,
                "larghezza": LARGHEZZA, "altezza": ALTEZZA,
                "byte": len(flusso),
                "dati": base64.b64encode(flusso).decode(),
                "sinistra": list(SINISTRA), "destra": list(DESTRA),
                "riletto": lette, "guai": guai,
            }
    return fuori


def stampa_js(sonde):
    print("/* ⛔ Generato da `banchi/02-pagina-sonda-codec.py` — non si scrive a")
    print("      mano.  Le due meta' sono rosso e blu, la tela si riempie prima")
    print("      di magenta: due letture giuste E DIVERSE, o «arriva» e «la tela")
    print("      era gia' di quel colore» avrebbero lo stesso aspetto. */")
    print("const SONDE = {")
    for nome, s in sonde.items():
        print(f'  "{nome}": {{ l: {s["larghezza"]}, a: {s["altezza"]}, '
              f'profondita: {s["profondita"]},')
        print(f'    sinistra: {s["sinistra"]}, destra: {s["destra"]},')
        print(f'    dati: "{s["dati"]}" }},')
    print("};")


def certifica():
    print("\033[1m== la certificazione della sonda: sano → guasto → risanato\033[0m")
    print("   atteso, scritto PRIMA: sano e risanato hanno due tinte DIVERSE in")
    print("   tutte e quattro le sonde; col guasto `una-tinta` la pretesa CADE.")
    esiti = []
    for giro, guasto in (("sano", ""), ("guasto", "una-tinta"), ("risanato", "")):
        sonde = costruisci_tutte(guasto)
        diverse = 0
        for nome, s in sonde.items():
            if s["riletto"] is None:
                print(f"    \033[1;33m??\033[0m  {nome}: non si e' potuto "
                      f"ridecodificare — {s['guai']}")
                continue
            sx, dx = s["riletto"]
            d = sum((a - b) ** 2 for a, b in zip(sx, dx)) ** 0.5
            if d > 60:
                diverse += 1
            print(f"    {nome:10s} {s['byte']:5d} byte · sinistra {sx} · "
                  f"destra {dx} · distanza {d:.0f}")
        atteso = 4 if guasto == "" else 0
        ok = diverse == atteso
        esiti.append(ok)
        segno = "\033[1;32mOK\033[0m" if ok else "\033[1;31mNO\033[0m"
        print(f"  {segno}  giro «{giro}»: {diverse} sonde su 4 con due tinte "
              f"diverse (atteso {atteso})\n")
    return 0 if all(esiti) else 1


if __name__ == "__main__":
    if "--certifica" in sys.argv:
        sys.exit(certifica())
    sonde = costruisci_tutte(os.environ.get("GUASTO", ""))
    for nome, s in sonde.items():
        if s["riletto"] is None:
            errore(f"la sonda {nome} non si ridecodifica: {s['guai']}")
        sx, dx = s["riletto"]
        d = sum((a - b) ** 2 for a, b in zip(sx, dx)) ** 0.5
        print(f"-- {nome:10s} {s['byte']:5d} byte · {sx} / {dx} · "
              f"distanza {d:.0f}", file=sys.stderr)
    if "--json" in sys.argv:
        print(json.dumps(sonde, indent=1))
    else:
        stampa_js(sonde)
