#!/usr/bin/env python3
"""02-pagina-sonda-misura.py — costruisce LA SCALA DELLE SONDE DI MISURA che
   vive dentro `src/pagina.html`, e la certifica.

    python3 banchi/02-pagina-sonda-misura.py             costruisce e stampa il JS
    python3 banchi/02-pagina-sonda-misura.py --json      la stampa come JSON
    python3 banchi/02-pagina-sonda-misura.py --certifica sano → 2 guasti → risanato

⚠ E' il gemello di `02-pagina-sonda-codec.py`, che costruisce le QUATTRO sonde
  da 64x48 con cui la pagina sceglie il CODEC.  Quello risponde a «questo
  browser decodifica AV1?»; questo risponde a «FINO A CHE MISURA?».

===========================================================================
⛔⭐ PERCHE' ESISTE — LE DUE GRANDEZZE CHE SI ERANO CONFUSE

`RCP.md` §4.3 definisce la capacita' `video.misura_massima` come

    | `video.misura_massima` | client | `LARGHEZZAxALTEZZA` **che sa
      decodificare**, es. `3840x2160` |

e tre righe sotto lo dice ancora piu' chiaro:

    ⚠ `video.misura_massima` **non** cambia la tela: e' un tetto che il server
      **DEVE** rispettare quando concede la tela (§4.5).  Esiste perche' il
      decodificatore di un telefono ha limiti **che il suo schermo non
      dichiara**.

⛔ `src/pagina.html` ci metteva dentro `screen.width x devicePixelRatio`, cioe'
   **LA MISURA DELLO SCHERMO**.  Sono due grandezze diverse, e la specifica
   nomina proprio il caso in cui divergono:

    la misura dello SCHERMO      quanti pixel ha il vetro davanti all'utente.
                                 E' la `vista` di §4.5 — dove il client
                                 DISEGNA — e §6.2 dice che il client
                                 «riscala alla VISTA, non alla tela».
    la misura del DECODIFICATORE fino a che risoluzione questo browser porta
                                 un flusso fino al pixel.  Non ha niente a
                                 che vedere col vetro: un portatile con uno
                                 schermo 2560x1080 decodifica il 4K benissimo,
                                 e un telefono con uno schermo minuscolo puo'
                                 decodificare 4K o fermarsi a 1080p a seconda
                                 del chip.

⇒ `[M]` 13 agosto 2026, registro del server sulla 7561, utente `nicfio`:

    il client dichiara video.misura_massima=2560x1010 — e' il tetto che la
      tela concessa DEVE rispettare (§4.5)
    ⚠ RIPIEGO DICHIARATO (§4.5): tela chiesta 1920x1080, tetto 2560x1010
      — CONCESSA 1794x1010
    ⛔ tela in vigore 1794x1010 ma il fotogramma catturato e' 1920x1080 —
      NON lo spedisco

  Lo schermo dell'utente e' alto 1010 pixel; il suo browser il 1080p lo
  decodifica senza fatica.  ⛔ **Su quello schermo l'immagine non sarebbe
  comparsa mai**, e nemmeno a schermo intero: `screen.height` non cambia con
  F11.

===========================================================================
⛔ E LA CURA NON PUO' ESSERE «DICHIARA 4K SEMPRE»

Sarebbe rompere §4.5 dalla parte opposta, e romperebbe **il telefono**, che e'
il dispositivo per cui quel campo esiste: un client che dichiara un tetto piu'
alto del vero riceve una tela che il suo decodificatore rifiuta, e il sintomo
non e' un errore di rete — e' `configure()` che lancia, cioe' lo stesso rosso
di `video.livello` (rilievo O12).

⇒ Il tetto **si misura**, e si misura come questa pagina misura gia' i codec:
  non chiedendolo a un'API, ma **dipingendo e rileggendo i pixel**.  Da cui
  questa scala.

===========================================================================
⛔ LA SCALA SI FERMA A 3840x2160, E NON E' UN ARROTONDAMENTO

`src/pagina.html` dichiara `video.livello = 5.1`.  Il livello 5.1 di HEVC e di
AV1 arriva a 4096x2176: ⛔ dichiarare `video.misura_massima` piu' grande del
livello che si e' appena dichiarato sarebbe una contraddizione **dentro lo
stesso `CIAO`**, e il server ha ragione a fidarsi dell'uno o dell'altro senza
sapere quale.  ⇒ L'ultimo gradino della scala e' il piu' grande che il livello
dichiarato regge.  Se un giorno `LIVELLO_DICHIARATO` sale, sale anche la scala,
e le due righe stanno una accanto all'altra apposta.

⚠ E il gradino piu' basso e' **320x240**, che e' il minimo normativo della tela
  (§4.5): sotto quello non c'e' niente da dichiarare, perche' non c'e' nessuna
  tela legale che ci stia dentro.

===========================================================================
⛔ IL PREZZO, IN BYTE, E PERCHE' E' PICCOLO

Le sonde sono **due tinte piatte, meta' e meta'**: un fotogramma chiave di
3840x2160 con dentro due campi uniformi comprime a poche centinaia di byte.
`[M]` 13 agosto 2026, questo stesso programma:

    av1  3840x2160   241 byte          hevc 3840x2160  2102 byte
    av1  1920x1080   160 byte          hevc 1920x1080   733 byte

⇒ La scala intera, per tutti e due i codec, sta sotto i 6 KB in base64 — cioe'
  meno del 7% della pagina.  ⚠ Il prezzo vero non e' in byte: e' il **tempo di
  decodifica all'avvio**, ed e' misurato dal banco `02-pagina-misura-*`, non
  qui.

===========================================================================
⛔ E SI CERTIFICA — sano → DUE guasti → risanato

    sano       ogni sonda della scala si ridecodifica, e le due meta' sono due
               tinte DIVERSE, alla misura DICHIARATA
    guasto `una-tinta`    le due meta' diventano la stessa ⇒ la pretesa «due
               tinte diverse» DEVE cadere per tutte
    guasto `misura-finta` la sonda dichiara una misura e ne porta un'altra
               (il flusso resta quello del gradino sotto) ⇒ la pretesa «la
               misura riletta e' quella dichiarata» DEVE cadere.
               ⛔ Senza questo secondo guasto, una scala in cui ogni gradino
                 portasse per sbaglio il flusso di 320x240 sarebbe VERDE, e il
                 prodotto dichiarerebbe 4K avendo misurato 320x240 — cioe'
                 esattamente il difetto che questo file esiste per non fare.
    risanato   come il sano
"""
import base64
import json
import os
import subprocess
import sys

# ⛔ Il gradino piu' basso e' il minimo normativo della tela (§4.5); il piu'
#    alto e' quel che regge `LIVELLO_DICHIARATO = "5.1"` in `src/pagina.html`.
#    ⚠ Le misure sono tutte PARI in tutti e due i versi, come §4.5 impone alla
#      tela: una scala con dentro un gradino dispari misurerebbe una tela che
#      il protocollo non permette di chiedere.
SCALA = [(320, 240), (640, 480), (1280, 720), (1920, 1080),
         (2560, 1440), (3840, 2160)]

# ⛔ La rilettura si fa su una tela PICCOLA, e non e' un risparmio qualunque:
#    `getImageData` su 3840x2160 sono 33 milioni di pixel riportati dalla GPU
#    alla memoria, per gradino e per codec.  Il fotogramma si dipinge
#    RIDOTTO — `drawImage` scala — e le due meta' restano due meta'.
#    ⚠ E la misura vera NON si legge dai pixel: si legge da
#      `VideoFrame.displayWidth/Height`, che e' quel che il decodificatore ha
#      prodotto davvero.  Le due domande sono diverse e si pongono tutt'e due.
RILETTURA_L, RILETTURA_A = 64, 48

# Le stesse due tinte delle quattro sonde del codec: la distanza fra loro e'
# oltre 180 per canale.
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


def grezzo(larghezza, altezza, guasto=""):
    """Il fotogramma sorgente in RGB24: meta' e meta'."""
    destra = SINISTRA if guasto == "una-tinta" else DESTRA
    riga = bytes(SINISTRA) * (larghezza // 2) + bytes(destra) * (larghezza // 2)
    return riga * altezza


def costruisci(codec, larghezza, altezza, guasto=""):
    """⛔ Annex-B puro per HEVC, unita' temporali di OBU per AV1, e NESSUNA
    `description` per nessuno dei due — `fasi/02-primo-fotogramma.md` D1.  Sono
    le stesse forme con cui `02-pagina-sonda-codec.py` costruisce le quattro
    sonde del codec: una sonda che arrivasse in una forma diversa da quella
    della sessione misurerebbe un percorso che non e' quello del prodotto."""
    dati = grezzo(larghezza, altezza, guasto)
    comune = ["ffmpeg", "-hide_banner", "-nostdin", "-y",
              "-f", "rawvideo", "-pix_fmt", "rgb24",
              "-s", f"{larghezza}x{altezza}", "-framerate", "30", "-i", "pipe:0"]
    colore = ["-color_primaries", "bt709", "-color_trc", "bt709",
              "-colorspace", "bt709"]
    if codec == "hevc":
        comando = comune + [
            "-c:v", "libx265", "-pix_fmt", "yuv420p", "-frames:v", "1",
            "-profile:v", "main",
            "-x265-params", "log-level=none:bframes=0:keyint=1:info=0",
        ] + colore + ["-f", "hevc", "pipe:1"]
        minimo = 64
    else:
        comando = comune + [
            "-c:v", "libaom-av1", "-pix_fmt", "yuv420p", "-frames:v", "1",
            "-crf", "20", "-b:v", "0", "-cpu-used", "8",
        ] + colore + ["-f", "obu", "pipe:1"]
        minimo = 16
    # ⚠ SI RIPROVA UNA VOLTA, E LO SI DICE.  `[M]` 13 agosto 2026: durante la
    #   certificazione — dodici `ffmpeg` di fila, ciascuno con fino a 25 MB di
    #   RGB in una pipe — `libaom` ha prodotto ZERO fotogrammi a 3840x2160 una
    #   volta su cinque giri, e lo stesso comando rilanciato da solo funziona.
    #   ⛔ Un banco che si fermasse li' direbbe «la scala non si costruisce»
    #     di una scala che si costruisce; uno che riprovasse IN SILENZIO
    #     nasconderebbe una fragilita' vera.  ⇒ Si riprova una volta sola, e la
    #     riprova compare su stderr.
    for tentativo in (1, 2):
        codice, uscita, errori = esegui(comando, entrata=dati)
        if codice == 0 and len(uscita) >= minimo:
            if tentativo == 2:
                print(f"    \033[1;33m⚠\033[0m  {codec} {larghezza}x{altezza}: "
                      f"il primo tentativo non ha prodotto niente, il secondo "
                      f"si ({len(uscita)} byte)", file=sys.stderr)
            return uscita
    errore(f"il codificatore non ha prodotto la sonda {codec} "
           f"{larghezza}x{altezza} in DUE tentativi",
           errori.decode("utf-8", "replace")[-800:])


def riletto(flusso, codec):
    """⛔ IL CONTROLLO POSITIVO DEL COSTRUTTORE, e sono DUE domande:

       1. il flusso si ridecodifica, e le due meta' sono ancora due tinte
          diverse (la stessa pretesa delle quattro sonde del codec);
       2. ⭐ e la misura che ne esce e' quella DICHIARATA.  Senza la seconda,
          una scala che portasse sei volte lo stesso flusso da 320x240 sarebbe
          verde da cima a fondo.

    ⚠ La rilettura passa da `scale=64:48` invece di riportare 25 MB di RGB per
      gradino: le due meta' restano due meta' anche ridotte, e la misura vera
      si legge da `showinfo`, non dai pixel."""
    misura = ["ffprobe", "-v", "error", "-select_streams", "v:0",
              "-show_entries", "stream=width,height", "-of", "csv=p=0",
              "-f", "hevc" if codec == "hevc" else "obu", "pipe:0"]
    codice, uscita, errori = esegui(misura, entrata=flusso)
    if codice != 0 or b"," not in uscita:
        return None, None, "ffprobe: " + errori.decode("utf-8", "replace")[-400:]
    try:
        l, a = (int(x) for x in uscita.decode().strip().split(",")[:2])
    except ValueError:
        return None, None, "ffprobe ha detto «" + uscita.decode().strip() + "»"

    comando = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
               "-f", "hevc" if codec == "hevc" else "obu", "-i", "pipe:0",
               "-vf", f"scale={RILETTURA_L}:{RILETTURA_A}",
               "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    codice, uscita, errori = esegui(comando, entrata=flusso)
    if codice != 0 or len(uscita) < RILETTURA_L * RILETTURA_A * 3:
        return (l, a), None, errori.decode("utf-8", "replace")[-400:]

    def media(x0, x1):
        r = g = b = n = 0
        for y in range(RILETTURA_A // 4, RILETTURA_A * 3 // 4):
            for x in range(x0, x1):
                i = (y * RILETTURA_L + x) * 3
                r += uscita[i]; g += uscita[i + 1]; b += uscita[i + 2]
                n += 1
        return [r // n, g // n, b // n]

    return (l, a), (media(4, RILETTURA_L // 2 - 4),
                    media(RILETTURA_L // 2 + 4, RILETTURA_L - 4)), None


def costruisci_tutte(guasto=""):
    fuori = {}
    for codec in ("hevc", "av1"):
        gradini = []
        precedente = None
        for larghezza, altezza in SCALA:
            flusso = costruisci(codec, larghezza, altezza,
                                "una-tinta" if guasto == "una-tinta" else "")
            # ⛔ Il guasto `misura-finta`: il gradino DICHIARA la sua misura ma
            #    porta il flusso di quello sotto.  E' il guasto che certifica
            #    la seconda pretesa.
            if guasto == "misura-finta" and precedente is not None:
                flusso = precedente
            precedente = flusso
            vera, tinte, guai = riletto(flusso, codec)
            gradini.append({
                "codec": codec, "larghezza": larghezza, "altezza": altezza,
                "byte": len(flusso),
                "dati": base64.b64encode(flusso).decode(),
                "sinistra": list(SINISTRA), "destra": list(DESTRA),
                "riletta": list(vera) if vera else None,
                "tinte": tinte, "guai": guai,
            })
        fuori[codec] = gradini
    return fuori


def stampa_js(scala):
    print("/* ⛔ Generato da `banchi/02-pagina-sonda-misura.py` — non si scrive a")
    print("      mano.  Una scala di fotogrammi chiave a MISURE CRESCENTI, due")
    print("      tinte piatte ciascuno: serve a misurare `video.misura_massima`")
    print("      di §4.3 — **quel che il DECODIFICATORE regge**, che non e' la")
    print("      misura dello schermo.  L'ultimo gradino e' il piu' grande che")
    print("      `LIVELLO_DICHIARATO` regge; il primo e' la tela minima di §4.5. */")
    print("const SONDE_MISURA = {")
    for codec, gradini in scala.items():
        print(f'  {codec}: [')
        for g in gradini:
            print(f'    {{ l: {g["larghezza"]}, a: {g["altezza"]}, '
                  f'rl: {RILETTURA_L}, ra: {RILETTURA_A}, profondita: 8,')
            print(f'      sinistra: {g["sinistra"]}, destra: {g["destra"]},')
            print(f'      dati: "{g["dati"]}" }},')
        print("  ],")
    print("};")


def giudica(scala, atteso_tinte, atteso_misura):
    """Conta i gradini che onorano le DUE pretese, e le conta separatamente:
    ⛔ un solo numero non distinguerebbe «la tinta e' sbagliata» da «la misura
    e' sbagliata», che sono due guasti diversi con due cure diverse."""
    tinte_ok = misura_ok = totale = 0
    for codec, gradini in scala.items():
        for g in gradini:
            totale += 1
            eti = f"{codec} {g['larghezza']}x{g['altezza']}"
            if g["tinte"] is None:
                print(f"    \033[1;33m??\033[0m  {eti}: non si e' potuto "
                      f"ridecodificare — {g['guai']}")
                continue
            sx, dx = g["tinte"]
            d = sum((a - b) ** 2 for a, b in zip(sx, dx)) ** 0.5
            if d > 60:
                tinte_ok += 1
            giusta = g["riletta"] == [g["larghezza"], g["altezza"]]
            if giusta:
                misura_ok += 1
            print(f"    {eti:16s} {g['byte']:6d} byte · riletta "
                  f"{g['riletta']} · distanza {d:.0f}"
                  f"{'' if giusta else '   ⛔ MISURA DIVERSA DA QUELLA DICHIARATA'}")
    return tinte_ok, misura_ok, totale


def certifica():
    print("\033[1m== la certificazione della scala: sano → 2 guasti → risanato\033[0m")
    print("   atteso, scritto PRIMA:")
    print("     sano/risanato   TUTTI i gradini hanno due tinte diverse E la")
    print("                     misura riletta e' quella dichiarata")
    print("     `una-tinta`     ZERO gradini con due tinte diverse")
    print("     `misura-finta`  la pretesa sulla MISURA cade su tutti i gradini")
    print("                     tranne il primo (che non ha uno sotto da cui")
    print("                     copiare), e quella sulle TINTE regge:")
    print("                     ⛔ un guasto che facesse cadere tutt'e due non")
    print("                       distinguerebbe le due pretese.\n")
    esiti = []
    n = len(SCALA) * 2
    for giro, guasto in (("sano", ""), ("guasto una-tinta", "una-tinta"),
                         ("guasto misura-finta", "misura-finta"),
                         ("risanato", "")):
        scala = costruisci_tutte(guasto)
        tinte, misura, totale = giudica(scala, None, None)
        if guasto == "una-tinta":
            atteso_t, atteso_m = 0, totale
        elif guasto == "misura-finta":
            atteso_t, atteso_m = totale, 2      # un primo gradino per codec
        else:
            atteso_t, atteso_m = totale, totale
        ok = (tinte == atteso_t and misura == atteso_m and totale == n)
        esiti.append(ok)
        segno = "\033[1;32mOK\033[0m" if ok else "\033[1;31mNO\033[0m"
        print(f"  {segno}  giro «{giro}»: {tinte}/{totale} con due tinte diverse "
              f"(atteso {atteso_t}) · {misura}/{totale} alla misura dichiarata "
              f"(atteso {atteso_m})\n")
    return 0 if all(esiti) else 1


if __name__ == "__main__":
    if "--certifica" in sys.argv:
        sys.exit(certifica())
    scala = costruisci_tutte(os.environ.get("GUASTO", ""))
    grosso = 0
    for codec, gradini in scala.items():
        for g in gradini:
            if g["tinte"] is None:
                errore(f"la sonda {codec} {g['larghezza']}x{g['altezza']} non "
                       f"si ridecodifica: {g['guai']}")
            if g["riletta"] != [g["larghezza"], g["altezza"]]:
                errore(f"la sonda {codec} {g['larghezza']}x{g['altezza']} "
                       f"porta una misura diversa: {g['riletta']}")
            grosso += len(g["dati"])
            print(f"-- {codec:5s} {g['larghezza']:5d}x{g['altezza']:<5d} "
                  f"{g['byte']:6d} byte · {g['tinte'][0]} / {g['tinte'][1]}",
                  file=sys.stderr)
    print(f"-- la scala intera, in base64: {grosso} byte", file=sys.stderr)
    if "--json" in sys.argv:
        print(json.dumps(scala, indent=1))
    else:
        stampa_js(scala)
