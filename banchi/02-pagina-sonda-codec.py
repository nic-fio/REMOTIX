#!/usr/bin/env python3
"""02-pagina-sonda-codec.py — builds the FOUR PROBES that live inside
   `src/pagina.html`, and certifies them.

    python3 banchi/02-pagina-sonda-codec.py            builds and prints the JS
    python3 banchi/02-pagina-sonda-codec.py --json     prints them as JSON
    python3 banchi/02-pagina-sonda-codec.py --certify  healthy → fault → healed

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

    --certify   healthy → fault → healed, with the expectation written beforehand:

      healthy    the four probes have two different colours and >= 200 bytes
      fault      `FAULT=una-tinta` builds the frame of ONE single colour
                 ⇒ the claim «two different colours» MUST fall.  Without this
                   round, «the probe has a negative control» would be just a sentence
      healed     like the healthy one
"""
import base64
import json
import os
import subprocess
import sys

WIDTH, HEIGHT = 64, 48

# ⛔ The two colours are taken from the eight of `02-pagina-sequenze.py`, and the
#    distance between them is over 180 per channel: `[M]` the RGB→YUV conversion,
#    the limited range and the encoder's loss shift a channel by
#    a few tens — not by a hundred (F2-5 §«What is counted»).
LEFT = (220, 32, 32)     # red
RIGHT = (48, 64, 220)       # blue


def failure(body_text, detail=""):
    print(f"\033[1;31mNO\033[0m  {body_text}", file=sys.stderr)
    if detail:
        print("    " + detail.replace("\n", "\n    "), file=sys.stderr)
    sys.exit(2)


def execute(command, entry=b""):
    p = subprocess.run(command, input=entry, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return p.returncode, p.stdout, p.stderr


def raw(fault=""):
    """The source frame in RGB24: half and half.

    ⛔ With the `una-tinta` fault the two halves become the same: it is the fault
       that certifies the probe's negative control."""
    right_edge = LEFT if fault == "una-tinta" else RIGHT
    row = bytes(LEFT) * (WIDTH // 2) + bytes(right_edge) * (WIDTH // 2)
    return row * HEIGHT


def build_hevc(bit_depth, fault=""):
    """⛔ Pure Annex-B, NO `description` — `FASI.md` §02-primo-fotogramma D1,
    confirmed by the pixel in F2-5 §3: `hev1.` and `hvc1.` both work, and
    Chromium decides the stream form from the PRESENCE of the `description`, not
    from the prefix."""
    pix = "yuv420p10le" if bit_depth == 10 else "yuv420p"
    source = "rgb48le" if bit_depth == 10 else "rgb24"
    data_v = raw(fault)
    if bit_depth == 10:
        # ⚠ The source stays at 8 bits promoted: here the depth of the
        #   CONTENT is not measured (F2-5 §6 — that question is asked at the
        #   source or not at all), what is measured is whether the browser DECODES a
        #   Main10 and paints it.
        data_v = b"".join(bytes([b, b]) for b in data_v)
    command = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", source,
        "-s", f"{WIDTH}x{HEIGHT}", "-framerate", "30", "-i", "pipe:0",
        "-c:v", "libx265", "-pix_fmt", pix, "-frames:v", "1",
        # ⛔ The profile is ASKED FOR BY NAME and it is checked that it was given
        #    (`CODER.md` §3.9): x265 left to choose emits `Main 10 Intra`
        #    (Rext, profile_idc 4), which is not what the product configures.
        "-profile:v", "main10" if bit_depth == 10 else "main",
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
        #    put in the `HELLO`.  The declared string said `hev1.1.6` /
        #    `hev1.2.4` — profiles 1 and 2 — and **the bytes said 4**.
        #    `isConfigSupported` answers to the STRING and said `true`; the
        #    decoder fell on the BYTES with `EncodingError`; the page
        #    concluded «HEVC does not reach the pixel» and left it out of the `HELLO`;
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
    code_v, out_dir, errors = execute(command, entry=data_v)
    if code_v != 0 or len(out_dir) < 64:
        failure(f"libx265 did not produce the {bit_depth}-bit probe",
               errors.decode("utf-8", "replace")[-800:])
    return out_dir


def build_h264(bit_depth, fault=""):
    """⛔ Pure Annex-B, NO `description` — the same choice as HEVC, and for
    the same reason: without `description` the browser takes the stream as
    Annex-B, and it is the form our encoder emits.

    ⚠ And ONLY 8 BITS, declared instead of forgotten: `[M]` `vainfo` on this
      machine carries `VAProfileH264High` and not 10 bit, so a 10-bit
      probe would measure a road the server **cannot produce in hardware** —
      and whoever saw it green would believe they had something they do not have."""
    if bit_depth != 8:
        return None
    data_v = raw(fault)
    command = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-framerate", "30", "-i", "pipe:0",
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
    code_v, out_dir, errors = execute(command, entry=data_v)
    if code_v != 0 or len(out_dir) < 64:
        failure(f"libx264 did not produce the {bit_depth}-bit probe",
               errors.decode("utf-8", "replace")[-800:])
    return out_dir


def build_av1(bit_depth, fault=""):
    """⛔ No `description`: AV1 in WebCodecs takes the temporal units of
    OBUs as they are (F2-5, addition of 12 Aug).  Here IVF is gone through
    only to strip the frame."""
    pix = "yuv420p10le" if bit_depth == 10 else "yuv420p"
    source = "rgb48le" if bit_depth == 10 else "rgb24"
    data_v = raw(fault)
    if bit_depth == 10:
        data_v = b"".join(bytes([b, b]) for b in data_v)
    command = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", source,
        "-s", f"{WIDTH}x{HEIGHT}", "-framerate", "30", "-i", "pipe:0",
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
    code_v, out_dir, errors = execute(command, entry=data_v)
    if code_v != 0 or len(out_dir) < 16:
        failure(f"libaom-av1 did not produce the {bit_depth}-bit probe",
               errors.decode("utf-8", "replace")[-800:])
    return out_dir


def stream_tints(flow, codec, bit_depth):
    """⛔ The positive control of the BUILDER: the stream just produced is
    re-decoded and it is checked that the two halves are still two different
    colours.  Without it, «the probe has two colours» would be a property of the
    SOURCE, not of the stream that will end up in the product."""
    schema = {"hevc": "hevc", "h264": "h264"}.get(codec, "obu")
    command = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
               "-f", schema, "-i", "pipe:0",
               "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    code_v, out_dir, errors = execute(command, entry=flow)
    if code_v != 0 or len(out_dir) < WIDTH * HEIGHT * 3:
        return None, errors.decode("utf-8", "replace")[-400:]

    def media(x0, x1):
        r = g = b = n = 0
        for y in range(HEIGHT // 4, HEIGHT * 3 // 4):
            for x in range(x0, x1):
                i = (y * WIDTH + x) * 3
                r += out_dir[i]; g += out_dir[i + 1]; b += out_dir[i + 2]
                n += 1
        return [r // n, g // n, b // n]

    return (media(4, WIDTH // 2 - 4), media(WIDTH // 2 + 4,
                                                WIDTH - 4)), None


def build_all(fault=""):
    outside = {}
    builders = {"hevc": build_hevc, "h264": build_h264,
                   "av1": build_av1}
    for codec in ("hevc", "h264", "av1"):
        for bit_depth in (8, 10):
            flow = builders[codec](bit_depth, fault)
            # ⛔ «Not there» is SKIPPED by declaring it, and no empty entry is
            #    written: an empty probe in the page would say «tried and does not
            #    arrive» of something never tried (`LEZIONI.md` §1.9).
            if flow is None:
                continue
            read, troubles = stream_tints(flow, codec, bit_depth)
            outside[f"{codec}-{bit_depth}"] = {
                "codec": codec, "bit_depth": bit_depth,
                "width_px": WIDTH, "height_px": HEIGHT,
                "byte": len(flow),
                "data_v": base64.b64encode(flow).decode(),
                "left_edge": list(LEFT), "right_edge": list(RIGHT),
                "reread": read, "troubles": troubles,
            }
    return outside


def print_js(probes):
    print("/* ⛔ Generated by `banchi/02-pagina-sonda-codec.py` — not written by")
    print("      hand.  The two halves are red and blue, the canvas is first filled")
    print("      with magenta: two right readings AND DIFFERENT ones, or «it arrives» and «the canvas")
    print("      was already that colour» would look the same. */")
    print("const PROBES = {")
    for label_name, s in probes.items():
        print(f'  "{label_name}": {{ l: {s["width_px"]}, a: {s["height_px"]}, '
              f'bit_depth: {s["bit_depth"]},')
        print(f'    left_edge: {s["left_edge"]}, right_edge: {s["right_edge"]},')
        print(f'    data_v: "{s["data_v"]}" }},')
    print("};")


def certify():
    print("\033[1m== the certification of the probe: healthy → fault → healed\033[0m")
    print("   expected, written BEFOREHAND: healthy and healed have two DIFFERENT colours in")
    print("   all four probes; with the `una-tinta` fault the claim FALLS.")
    outcomes = []
    for lap, fault in (("healthy", ""), ("fault", "una-tinta"), ("healed", "")):
        probes = build_all(fault)
        diverse = 0
        for label_name, s in probes.items():
            if s["reread"] is None:
                print(f"    \033[1;33m??\033[0m  {label_name}: it could not be "
                      f"re-decoded — {s['troubles']}")
                continue
            left_side, right = s["reread"]
            d = sum((a - b) ** 2 for a, b in zip(left_side, right)) ** 0.5
            if d > 60:
                diverse += 1
            print(f"    {label_name:10s} {s['byte']:5d} bytes · left {left_side} · "
                  f"right {right} · distance {d:.0f}")
        expected_val = 4 if fault == "" else 0
        ok = diverse == expected_val
        outcomes.append(ok)
        sign = "\033[1;32mOK\033[0m" if ok else "\033[1;31mNO\033[0m"
        print(f"  {sign}  round «{lap}»: {diverse} probes out of 4 with two different "
              f"colours (expected {expected_val})\n")
    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    if "--certify" in sys.argv:
        sys.exit(certify())
    probes = build_all(os.environ.get("FAULT", ""))
    for label_name, s in probes.items():
        if s["reread"] is None:
            failure(f"the probe {label_name} does not re-decode: {s['troubles']}")
        left_side, right = s["reread"]
        d = sum((a - b) ** 2 for a, b in zip(left_side, right)) ** 0.5
        print(f"-- {label_name:10s} {s['byte']:5d} bytes · {left_side} / {right} · "
              f"distance {d:.0f}", file=sys.stderr)
    if "--json" in sys.argv:
        print(json.dumps(probes, indent=1))
    else:
        print_js(probes)
