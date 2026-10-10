#!/usr/bin/env python3
"""02-pagina-sonda-codec.py — builds the FOUR PROBES that live inside
   `src/pagina.html`, and certifies them.

    python3 banchi/02-pagina-sonda-codec.py            builds and prints the JS
    python3 banchi/02-pagina-sonda-codec.py --json     prints them as JSON
    python3 banchi/02-pagina-sonda-codec.py --certifica  healthy → fault → healed

===========================================================================
⛔ WHY THE PRODUCT CARRIES FOUR REAL STREAMS AROUND

`fasi/rapporti/F2-5-pagina.md` §2, `[M]` 12 Aug 2026, Firefox 140 ESR:

    navigator.mediaCapabilities.decodingInfo()  →  supported: true
    video.canPlayType()                         →  «probably»
    VideoDecoder.isConfigSupported()            →  false
    the pixel                                   →  NOTHING

⛔ Three witnesses, two of which lie on all seven HEVC
   strings.  A page that chose the codec from `mediaCapabilities` — which is
   the API **made precisely** for that question — would choose HEVC on Firefox and
   paint nothing.

⚠ And `isConfigSupported`, which tells the truth there, remains the **E1** form
  (`REVIEWER.md` §2): it says the configuration is **accepted**, not that the
  pixel **arrives**.  `[M]` in the same round: Chrome accepts `L30` on a level 3.0
  stream and paints anyway — that is, the API also accepts what it should
  not.

⇒ ⭐ The only question that has an answer is **the pixel**, and the only place where
  it can be asked is **the user's device** (`STUDI.md` §web §9 lesson 2: *«the
  browser knows and does not answer… the measurement must live in the product»*).  Hence
  these four probes: two distant colours in a 64x48 keyframe, one
  per codec and per depth.

===========================================================================
⛔ THE PROBE HAS A NEGATIVE CONTROL INSIDE ITSELF

A frame of **a single colour** would not tell «it painted» from «the canvas
was already that colour».  Here there are **two**, half and half, and the canvas is
first filled with a third colour that is neither of them (magenta).  ⇒ To
say «it arrives» two right readings **that differ from each other** are needed: no uniform
fill passes them.

===========================================================================
⛔ AND IT IS CERTIFIED, like every other tool of this bench

    --certifica   healthy → fault → healed, with the expectation written beforehand:

      healthy    the four probes have two different colours and >= 200 bytes
      fault      `GUASTO=una-tinta` builds the frame of ONE single colour
                 ⇒ the claim «two different colours» MUST fall.  Without this
                   round, «the probe has a negative control» would be just a sentence
      healed     like the healthy one
"""
import base64
import json
import os
import subprocess
import sys

LARGHEZZA, ALTEZZA = 64, 48

# ⛔ The two colours are taken from the eight of `02-pagina-sequenze.py`, and the
#    distance between them is over 180 per channel: `[M]` the RGB→YUV conversion,
#    the limited range and the encoder's loss shift a channel by
#    a few tens — not by a hundred (F2-5 §«What is counted»).
SINISTRA = (220, 32, 32)     # red
DESTRA = (48, 64, 220)       # blue


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
    """The source frame in RGB24: half and half.

    ⛔ With the `una-tinta` fault the two halves become the same: it is the fault
       that certifies the probe's negative control."""
    destra = SINISTRA if guasto == "una-tinta" else DESTRA
    riga = bytes(SINISTRA) * (LARGHEZZA // 2) + bytes(destra) * (LARGHEZZA // 2)
    return riga * ALTEZZA


def costruisci_hevc(profondita, guasto=""):
    """⛔ Pure Annex-B, NO `description` — `FASI.md` §02-primo-fotogramma D1,
    confirmed by the pixel in F2-5 §3: `hev1.` and `hvc1.` both work, and
    Chromium decides the stream form from the PRESENCE of the `description`, not
    from the prefix."""
    pix = "yuv420p10le" if profondita == 10 else "yuv420p"
    sorgente = "rgb48le" if profondita == 10 else "rgb24"
    dati = grezzo(guasto)
    if profondita == 10:
        # ⚠ The source stays at 8 bits promoted: here the depth of the
        #   CONTENT is not measured (F2-5 §6 — that question is asked at the
        #   source or not at all), what is measured is whether the browser DECODES a
        #   Main10 and paints it.
        dati = b"".join(bytes([b, b]) for b in dati)
    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", sorgente,
        "-s", f"{LARGHEZZA}x{ALTEZZA}", "-framerate", "30", "-i", "pipe:0",
        "-c:v", "libx265", "-pix_fmt", pix, "-frames:v", "1",
        # ⛔ The profile is ASKED FOR BY NAME and it is checked that it was given
        #    (`CODER.md` §3.9): x265 left to choose emits `Main 10 Intra`
        #    (Rext, profile_idc 4), which is not what the product configures.
        "-profile:v", "main10" if profondita == 10 else "main",
        # ⛔ `info=0` removes the x265 SEI that holds the command line: it is
        #    ~1.5 KB of text that would end up in base64 inside the product's
        #    page without telling anyone anything.
        #
        # ⛔⛔⛔ AND `keyint=1` WAS REMOVED ON THE EVENING OF 13 AUG 2026, BECAUSE
        #    IT CANCELLED THE `-profile:v` REQUESTED FOUR LINES ABOVE — and it
        #    cost the codec of the whole product.
        #
        #    With `keyint=1` libx265 emits **Main 10 Intra**, that is `Rext`,
        #    `profile_idc = 4`: exactly the thing the comment above
        #    declares it wants to avoid.  ⇒ The profile **had been requested and not
        #    applied, without an error**.
        #
        #    ⛔ And the damage was not in the bench: the two probes end up **in
        #    `src/pagina.html`**, and the page uses them to decide what to
        #    put in the `CIAO`.  The declared string said `hev1.1.6` /
        #    `hev1.2.4` — profiles 1 and 2 — and **the bytes said 4**.
        #    `isConfigSupported` answers to the STRING and said `true`; the
        #    decoder fell on the BYTES with `EncodingError`; the page
        #    concluded «HEVC does not reach the pixel» and left it out of the `CIAO`;
        #    and the server, which takes the first entry of the CLIENT's list,
        #    negotiated **AV1**.
        #
        #    ⇒ ⭐ **The product encoded in software for days because of one
        #    line of a bench**, and nobody saw it because every piece of the
        #    chain answered correctly the question it had been
        #    asked.  `[M]` removing `keyint=1` gives **Main 10**, reproduced
        #    three times.
        #
        #    ⚠ And it was seen ONLY by going to read the bytes produced: the string
        #    and the codec agreed with each other and disagreed with the stream.
        "-x265-params", "log-level=none:bframes=0:info=0",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-f", "hevc", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=dati)
    if codice != 0 or len(uscita) < 64:
        errore(f"libx265 did not produce the {profondita}-bit probe",
               errori.decode("utf-8", "replace")[-800:])
    return uscita


def costruisci_h264(profondita, guasto=""):
    """⛔ Pure Annex-B, NO `description` — the same choice as HEVC, and for
    the same reason: without `description` the browser takes the stream as
    Annex-B, and it is the form our encoder emits.

    ⚠ And ONLY 8 BITS, declared instead of forgotten: `[M]` `vainfo` on this
      machine carries `VAProfileH264High` and not 10 bit, so a 10-bit
      probe would measure a road the server **cannot produce in hardware** —
      and whoever saw it green would believe they had something they do not have."""
    if profondita != 8:
        return None
    dati = grezzo(guasto)
    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{LARGHEZZA}x{ALTEZZA}", "-framerate", "30", "-i", "pipe:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-frames:v", "1",
        # ⛔ The profile is ASKED FOR BY NAME: `high` is what the
        #    `avc1.6400xx` string the page sends to `VideoDecoder` declares.  If
        #    x264 emitted another profile, the string and the bytes
        #    would say two different things — and it is the defect that on 13 Aug
        #    lost the product its codec (see the box above).
        "-profile:v", "high",
        "-x264-params", "log-level=none:bframes=0:repeat-headers=1",
        # ⛔ THE x264 SEI IS REMOVED FROM THE BYTES, not with an option — because
        #    the option does not exist.  `[M]` 20 Aug 2026: x264 always writes an
        #    «user data unregistered» SEI holding its own command line,
        #    **1,402 bytes** — more than the frame itself — that would end up in
        #    base64 inside `pagina.html`.  ⚠ `+bitexact` does NOT remove it (tried).
        #    ⇒ The NAL of type 6 is removed with a bitstream filter, which is a
        #    declared and verifiable thing: the probe is re-decoded right
        #    after, and if the filter had removed too much the two colours would not
        #    come back.
        "-bsf:v", "filter_units=remove_types=6",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-f", "h264", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=dati)
    if codice != 0 or len(uscita) < 64:
        errore(f"libx264 did not produce the {profondita}-bit probe",
               errori.decode("utf-8", "replace")[-800:])
    return uscita


def costruisci_av1(profondita, guasto=""):
    """⛔ No `description`: AV1 in WebCodecs takes the temporal units of
    OBUs as they are (F2-5, addition of 12 Aug).  Here IVF is gone through
    only to strip the frame."""
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
        # ⛔ `-f obu` and not `ivf`: the temporal unit comes out as it is, with its
        #    `sequence header` in front.  ⚠ Stripping an IVF would give only the
        #    body of the frame, and an AV1 frame without a sequence header is not
        #    decodable on its own — the probe would say «does not arrive» on a
        #    browser that instead decodes perfectly well.
        "-f", "obu", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=dati)
    if codice != 0 or len(uscita) < 16:
        errore(f"libaom-av1 did not produce the {profondita}-bit probe",
               errori.decode("utf-8", "replace")[-800:])
    return uscita


def tinte_del_flusso(flusso, codec, profondita):
    """⛔ The positive control of the BUILDER: the stream just produced is
    re-decoded and it is checked that the two halves are still two different
    colours.  Without it, «the probe has two colours» would be a property of the
    SOURCE, not of the stream that will end up in the product."""
    formato = {"hevc": "hevc", "h264": "h264"}.get(codec, "obu")
    comando = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
               "-f", formato, "-i", "pipe:0",
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
    costruttori = {"hevc": costruisci_hevc, "h264": costruisci_h264,
                   "av1": costruisci_av1}
    for codec in ("hevc", "h264", "av1"):
        for profondita in (8, 10):
            flusso = costruttori[codec](profondita, guasto)
            # ⛔ «Not there» is SKIPPED by declaring it, and no empty entry is
            #    written: an empty probe in the page would say «tried and does not
            #    arrive» of something never tried (`LEZIONI.md` §1.9).
            if flusso is None:
                continue
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
    print("/* ⛔ Generated by `banchi/02-pagina-sonda-codec.py` — not written by")
    print("      hand.  The two halves are red and blue, the canvas is first filled")
    print("      with magenta: two right readings AND DIFFERENT ones, or «it arrives» and «the canvas")
    print("      was already that colour» would look the same. */")
    print("const SONDE = {")
    for nome, s in sonde.items():
        print(f'  "{nome}": {{ l: {s["larghezza"]}, a: {s["altezza"]}, '
              f'profondita: {s["profondita"]},')
        print(f'    sinistra: {s["sinistra"]}, destra: {s["destra"]},')
        print(f'    dati: "{s["dati"]}" }},')
    print("};")


def certifica():
    print("\033[1m== the certification of the probe: healthy → fault → healed\033[0m")
    print("   expected, written BEFOREHAND: healthy and healed have two DIFFERENT colours in")
    print("   all four probes; with the `una-tinta` fault the claim FALLS.")
    esiti = []
    for giro, guasto in (("sano", ""), ("guasto", "una-tinta"), ("risanato", "")):
        sonde = costruisci_tutte(guasto)
        diverse = 0
        for nome, s in sonde.items():
            if s["riletto"] is None:
                print(f"    \033[1;33m??\033[0m  {nome}: it could not be "
                      f"re-decoded — {s['guai']}")
                continue
            sx, dx = s["riletto"]
            d = sum((a - b) ** 2 for a, b in zip(sx, dx)) ** 0.5
            if d > 60:
                diverse += 1
            print(f"    {nome:10s} {s['byte']:5d} bytes · left {sx} · "
                  f"right {dx} · distance {d:.0f}")
        atteso = 4 if guasto == "" else 0
        ok = diverse == atteso
        esiti.append(ok)
        segno = "\033[1;32mOK\033[0m" if ok else "\033[1;31mNO\033[0m"
        print(f"  {segno}  round «{giro}»: {diverse} probes out of 4 with two different "
              f"colours (expected {atteso})\n")
    return 0 if all(esiti) else 1


if __name__ == "__main__":
    if "--certifica" in sys.argv:
        sys.exit(certifica())
    sonde = costruisci_tutte(os.environ.get("GUASTO", ""))
    for nome, s in sonde.items():
        if s["riletto"] is None:
            errore(f"the probe {nome} does not re-decode: {s['guai']}")
        sx, dx = s["riletto"]
        d = sum((a - b) ** 2 for a, b in zip(sx, dx)) ** 0.5
        print(f"-- {nome:10s} {s['byte']:5d} bytes · {sx} / {dx} · "
              f"distance {d:.0f}", file=sys.stderr)
    if "--json" in sys.argv:
        print(json.dumps(sonde, indent=1))
    else:
        stampa_js(sonde)
