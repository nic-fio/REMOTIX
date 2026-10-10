#!/bin/bash
#
# 02-codifica-lancia.sh — F2.3: HEVC encoding in software, measured on the pixels.
#
#   bash banchi/02-codifica-lancia.sh              the whole round
#   bash banchi/02-codifica-lancia.sh elenco       what it would test, and with which expectations
#   LAV=/altrove bash banchi/02-codifica-lancia.sh different working folder
#
#   ⭐ CODIFICATORE=ffmpeg|prodotto   WHO encodes.  `ffmpeg` is the round this
#                                    bench was born with — when the product did not
#                                    exist.  `prodotto` points at
#                                    `src/codificatore.c` through
#                                    `02-codifica-prova` (built by
#                                    `02-codifica-costruisci.sh`).
#   ⭐ CODEC=hevc|av1                 WHICH codec.  They are TWO by decision
#                                    of the user of 12 Aug 2026
#                                    (`DECISIONI.md` §1.13): HEVC main, AV1
#                                    negotiated fallback.
#
# ⛔ And the two levers exist because a bench pointed at `ffmpeg` certifies
#    **ffmpeg**: a green round there says nothing about our encoder.  It is
#    form E10 of `REVIEWER.md` §2 — *«a green test on the wrong client»* —
#    with the wrong defendant.
#
# Exits **0** if everything holds, **1** if something is red, **2** if it could not
# look.  ⛔ And «I could not look» is NOT «fine»: they are three outcomes, not
# two (`01-b0-terreno.sh`, `LEZIONI.md` §1.9).
#
# ===========================================================================
# ⛔ WHY IT EXISTS — the measurement no eye can make
#
# This sub-phase must deliver to F2.4 and F2.5 a **Main10** HEVC stream that
# a real browser can decode.  The trouble is that **three different errors
# all look the same: an image that comes out fine.**
#
#   1. ⛔ **10 bits declared and not real.**  If the encoder is opened in
#      Main10 but the chain delivers it 8 bits, the label says Main 10,
#      `ffprobe` confirms, the decoded frame is perfect — and the
#      depth that `SPECIFICHE.md` §3.1 asks for as **desired** is not there.
#      Nobody notices by looking at the pixels: the banding on the gradients is
#      there, but an eye blames it on the bitrate.
#      ⇒ it is `REVIEWER.md` §2 **E1**, necessary mistaken for sufficient.
#
#   2. ⛔ **the wrong stream shape.**  Annex-B and hvcC are not
#      interchangeable, and whoever sends one saying it is the other gets from
#      `VideoDecoder` a **black** page, not a talking error.  The symptom
#      would show in F2.5, three links away from the cause.
#
#   3. ⛔ **the encoder that decides by itself.**  `REVIEWER.md` §2 **E2**, and it is
#      the household form: *«the encoder that falls back to CPU without saying so»*.  A
#      `-c:v hevc` instead of `-c:v libx265` lets ffmpeg choose; an
#      unrequested profile is chosen by x265; and two rounds with two different
#      encoders end up in the same report under the same label.
#
# ⇒ This bench exists to make the three **visible as numbers**, before the
#   product is written (`MANDATO-12-agosto-fase2.md` §1: the bench before the
#   product).
#
# ===========================================================================
# ⛔ THE SCENE, DECLARED — and it is STILL on purpose
#
# `CODER.md` §3.2 and `REVIEWER.md` §1 point 1 require a scene that **always
# moves**, because a compositor sends a frame only when
# something changes, and a still scene makes you measure the scene instead of the code.
#
# ⚠ **Here the scene is still, and the rule is not violated**: that rule is born
#   against whoever measures a **rate**.  Here no rate is measured — phase 2
#   is «a still image» by mandate — what is measured is **the pixel values of a
#   frame**.  ⛔ The rate is phase 3, and there the scene will have to move.
#
# The scene is instead **hostile on purpose**, which is the other half of the same
# rule: an easy image would pass any test.  It lives entirely in
# `02-codifica-immagine.py`, which declares every band and the defect it unmasks.
#
# ===========================================================================
# ⛔ THE TWO ROUNDS, AND WHY THEY CANNOT BE ONE
#
#   **round A — the chain** (`lossless=1`): it must come back **identical byte by
#   byte**.  Here, and only here, the 10 bits are measured without ambiguity.
#   **round B — the rendering** (real CRF): here *how much* is lost is measured.
#
# If the bits were measured at the real bitrate, a red would not tell *«the
# chain is 8-bit»* from *«the bitrate was low»*: two opposite diagnoses under
# the same label, that is **E2** inside the bench instead of in the product.
# The reasoning in full is in `02-codifica-immagine.py`.
#
# ===========================================================================
# ⛔ THE POSITIVE CONTROL, AND WHERE IT IS
#
# `CODER.md` §3.10: *«can this tool find something that is surely there?»*
# Here there are **four**, and they run BEFORE any measurement (step 2):
#
#   - the comparator says «equal» on a file against itself;
#   - the comparator says «different» on a copy with **a single byte flipped**;
#   - the bit meter says «real 10 bits» on the real source;
#   - ⛔ and it says «disguised 8 bits» on the **opposite case**, which this bench
#     **produces** instead of reasoning about.  It is the half that gets forgotten: a
#     tool that always said «10 bits» would pass the first three.
#
# ===========================================================================
# ⛔ THE NEGATIVE CONTROL AT THE END, AND THE SURPRISE IT PRODUCED
#
# A bench that has never seen a refusal cannot see one.  At the end the
# stream is mangled in three ways and the independent reader is required
# **not to deliver the good frame**.
#
# ⛔⭐ **And here the bench has already taught something, on 12 Aug 2026** `[M]`:
#     out of three manglings, **two were decoded with exit status 0**.
#
#       | mangling            | ffmpeg exit | frames | differing bytes |
#       |---|---|---|---|
#       | parameter sets removed | **183** | 0 | — |
#       | one byte flipped       | **0**   | 1 | 47,944 bytes out of 61,440 |
#       | stream truncated       | **0**   | 1 | 35,961 bytes out of 61,440 |
#
#     ⛔ **ffmpeg does not refuse: it conceals.**  A bench that had judged the
#     refusal on the **exit status** would have declared «corrupt stream
#     accepted» two times out of three, and it would have been a bench that cannot see
#     a refusal despite having the negative control written.
#     ⇒ Hence the criterion here is: **refused = (zero frames) OR (the
#     pixels are not those of the source)**.  And if a mangling gave
#     exit 0 **and** identical pixels, it is the BENCH that is red.
#
#     ⚠ And the same thing holds on the other side of the wire, and must be told to F2.5:
#     `S2-decodifica.md` §3.6 says `[?]` that `VideoDecoder` in steady state **does not
#     verify the bitstream** and raises no error on a lost reference.
#     Here it is `[M]` on the home reader: corruption **shows in the pixels, not
#     in the status**.
#
# ===========================================================================
# ⛔ WHAT THIS BENCH DOES **NOT** PROVE, said beforehand
#
#   - **it does not prove that a browser decodes it.**  The independent reader
#     is `ffmpeg`, which is a second reader but it is not Chromium.  The browser is
#     F2.5, and the probe on the phone is F2.6 (`PIANO.md` §«Phase 2», the two points);
#   - **it proves nothing about rate or delay.**  A single frame;
#   - **it does not touch the GPU.**  Encoding here is in software **on purpose**:
#     acceleration is phase 8, and putting it first would mean not knowing
#     which of the two pieces is wrong (`PIANO.md` §«Phase 2»);
#   - **it does not prove that capture delivers 10 bits.**  The source here is
#     built, not captured.  What really arrives from Mutter is the
#     seam asked of F2.2, and it is a live `[?]`.
#
# ===========================================================================
# ⛔ WHERE IT RUNS, AND WHY NO PORT IS NEEDED
#
# It runs where there is `ffmpeg` with `libx265`: on the CHUWI and **inside the NIC-OS
# container**, which is where the product will live.  The two ffmpegs are the **same
# version** (7.1.5-0+deb13u1) `[M]` 12 Aug 2026, and this must be rechecked at
# every round instead of remembered — step 1 does it.
#
# ⚠ **No socket, no listening, no port.**  Port **7513**
#   assigned to F2.3 by mandate §2 stays **unused**, and it is a thing to
#   declare and not to keep silent: this bench talks to nobody, so it cannot
#   collide with the benches of the other five sub-phases.
#   ⛔ And it does not touch NIC-OS: it does not switch off, switch on, or listen.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
LAV=${LAV:-/tmp/02-codifica}
ESITI=${ESITI:-$QUI/02-codifica-esiti.jsonl}
CODIFICATORE=${CODIFICATORE:-ffmpeg}
CODEC=${CODEC:-hevc}
PROVA=$QUI/02-codifica-prova
SCENA="SCENA-2.3-A · immagine nota 1920x1080 yuv420p10le BT.709 range limitato, ferma"
SCENA="$SCENA · codificatore=$CODIFICATORE · codec=$CODEC"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { OK=$((OK+1)); printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { NO=$((NO+1)); printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }
OK=0; NO=0

# ⛔ Every measurement ends up in here, and from here comes the log line: if a
#    number did not pass through here, it is not in the log — instead of being
#    copied by hand from what one remembers.
FATTI=$LAV/fatti.tsv
fatto() { printf '%s\t%s\n' "$1" "$2" >> "$FATTI"; }

# `esige <label> <expected> <obtained>` — and the expectation ALWAYS appears
# in the output, even when it matches: a bench that prints the number only
# when it is wrong forces you to reread the code to know what it was looking for.
esige() {
	if [ "$2" = "$3" ]; then ok "$1: $3 (expected $2)"; else ko "$1: $3 ⛔ EXPECTED $2"; fi
}

# ═══════════════════════════════════════════════════════════════════════════
# THE EXPECTATIONS, WRITTEN BEFORE THE ROUND  (`PIANO.md` §0.3 rule 4)
# ═══════════════════════════════════════════════════════════════════════════
if [ "$CODEC" = av1 ]; then
	# ⚠ AV1 has ONE single profile for 4:2:0 at 10 bits, and it is called «Main»: it is not
	#   a poorer profile than Main10, it is the same thing with another name —
	#   the depth sits in `high_bitdepth` of the sequence header, not in the
	#   profile.  Whoever compared the two labels would write «AV1 is 8-bit».
	A_PROFILO="Main"
	A_PIXFMT="yuv420p10le"
	A_CODEC="av1"
	# ⛔ And AV1's round A is NOT lossless, because SVT-AV1 2.3.0 has no
	#    lossless mode — `[M]` 12 Aug 2026: `lossless=1` prints «Error
	#    parsing option» and **goes on exiting 0**.  ⭐ The closest regime is
	#    CRF 1, and it is MEASURED that the 10-bit gauge holds intact there: 877
	#    levels on the real source, 220 with 1.000 of multiples of 4 on the opposite
	#    case.  ⚠ What is lost is byte-for-byte identity: here the
	#    expected differing samples are not zero, and one does not pretend they are.
	OPZIONI_GIRO_A="crf=1"
	A_BYTE_DIVERSI_LOSSLESS=-1        # ⚠ -1 = «identity is not required»
else
	A_PROFILO="Main 10"
	A_PIXFMT="yuv420p10le"
	A_CODEC="hevc"
	OPZIONI_GIRO_A="lossless=1"
fi
A_PROFILO_HEVC="Main 10"
A_LIVELLI_VERI=877          # all the integers from 64 to 940
A_LIVELLI_8IN10=220         # from 64 to 940 in steps of 4
A_M4_8IN10="1.0"            # every 8-bit sample promoted to 10 is v<<2
A_VERDETTO_VERO="10-bit-veri"
A_VERDETTO_8IN10="8-bit-travestiti"
[ "$CODEC" = av1 ] || A_BYTE_DIVERSI_LOSSLESS=0   # ⛔ lossless: identical byte by byte
A_GRUPPI_IDR_3=3            # three IDRs, three times VPS+SPS+PPS in front
A_STORPIATURE_RIFIUTATE=3   # all three, or the bench cannot see a refusal
CRF_RESA=20                 # round B.  ⚠ it is not the working point of the
                            #   product: that is phase 9

if [ "${1:-}" = elenco ]; then
	cat <<-FINE
	F2.3 — what it tests, and with which expectations written beforehand

	  1  ffmpeg/ffprobe are there, and libx265 is there  present, version printed
	  2  ⛔ positive control of the four tools            all four
	  3  round A: libx265 asked for BY NAME, Main10 lossless
	     3a  ffprobe reads from the STREAM   codec=$A_CODEC profile=«$A_PROFILO» pix_fmt=$A_PIXFMT
	     3b  ⭐ x265 confession in the stream             bitdepth=10, annexb, repeat-headers
	     3c  Annex-B shape: VPS,SPS,PPS then IDR         and the first frame is a KEYFRAME
	     3d  decoded pixels against source               $A_BYTE_DIVERSI_LOSSLESS differing bytes
	     3e  the 10 bits on the DECODED                  $A_VERDETTO_VERO, $A_LIVELLI_VERI levels
	  4  ⛔ OPPOSITE CASE: the same image passed through 8 bits
	     4a  the label STILL says «$A_PROFILO»           ⭐ and it is honest: it is the stream that lies
	     4b  the 10 bits on the decoded                  $A_VERDETTO_8IN10, $A_LIVELLI_8IN10 levels
	  5  round B: the rendering at CRF $CRF_RESA               loss > 0, and the stream holds
	  6  three frames with -g 1                         $A_GRUPPI_IDR_3 groups of parameter sets
	  7  ⛔ negative control: three manglings            $A_STORPIATURE_RIFIUTATE refused
	  8  ⛔ the REAL road, from BGRx (only CODIFICATORE=prodotto and CODEC=hevc)
	     8a  our conversion against ffmpeg's             0 differing samples
	     8b  the 8→10 promotion DECLARED                 True
	     8c  ⛔ the levels after the matrix               256, and NOT 877

	  who encodes: $CODIFICATORE          codec: $CODEC
	FINE
	exit 0
fi

mkdir -p "$LAV" || { echo "⛔ cannot create $LAV"; exit 2; }
: > "$FATTI"

# ───────────────────────────────────────────────────────────────────────────
log "1. The terrain: are the tools the ones I believe?"
# ⛔ `01-b0-terreno.sh`: twice in one day a bench was green on a
#    terrain that was not the one we believed.  Here the terrain is ffmpeg.
for prog in ffmpeg ffprobe python3; do
	if command -v "$prog" > /dev/null; then ok "$prog: $(command -v "$prog")"
	else ko "⛔ missing $prog"; exit 2; fi
done
# ⚠ No pipe in here, for the reason written ten lines further down.
VER_FFMPEG=$(ffmpeg -hide_banner -version)
VER_FFMPEG=${VER_FFMPEG%%$'\n'*}
inf "$VER_FFMPEG"
fatto ffmpeg "$VER_FFMPEG"
# ⛔ AND HERE THE BENCH BIT ITSELF, on 12 Aug 2026 — worth keeping it
#    written.  The first draft said `ffmpeg -encoders | grep -q libx265`: with
#    `set -o pipefail`, `grep -q` closes the pipe at the first match, ffmpeg dies
#    of SIGPIPE (141) and **the pipeline reports a failure precisely when the
#    thing looked for IS THERE**.  The bench declared «libx265 is not there» on a
#    machine that has it.  It is `LEZIONI.md` §1.9 the other way round — not zero read
#    as a fault, but **success** read as a fault — and it is the reason why
#    the output is captured in a variable and examined outside the pipe.
ELENCO_ENC=$(ffmpeg -hide_banner -encoders)
STATO_ENC=$?
if [ "$STATO_ENC" -ne 0 ]; then
	ko "⛔ «ffmpeg -encoders» exited $STATO_ENC: I could not look"; exit 2
fi
ATTESO_COMPONENTE=libx265
[ "$CODEC" = av1 ] && ATTESO_COMPONENTE=libsvtav1
case "$ELENCO_ENC" in
	*"$ATTESO_COMPONENTE"*) ok "$ATTESO_COMPONENTE is there — ⛔ and it will be asked for BY NAME, not with -c:v $CODEC (CODER.md §3.9)" ;;
	*) ko "⛔ $ATTESO_COMPONENTE is not there: this bench has nothing to measure"; exit 2 ;;
esac
# ⛔ And if the PRODUCT is measured, the product must be there — and it must be NEWER
#    than the source, or an old version would be measured while believing to
#    measure the one just written.  It is the lesson of the evening of 12 Aug: «the
#    product on the server was not the product we had written».
if [ "$CODIFICATORE" = prodotto ]; then
	if [ ! -x "$PROVA" ]; then
		ko "⛔ $PROVA is missing: it is built with «bash banchi/02-codifica-costruisci.sh»"
		exit 2
	fi
	if [ "$QUI/../src/codificatore.c" -nt "$PROVA" ] || [ "$QUI/../src/codificatore.h" -nt "$PROVA" ]; then
		ko "⛔ src/codificatore.c is NEWER than the tool: an old version"
		ko "   would be measured.  Rebuild before measuring"
		exit 2
	fi
	ok "product tool: $PROVA, more recent than the source"
fi
inf "working folder: $LAV"
inf "port used: ⛔ NONE (7513 assigned to F2.3 stays free: nobody listens here)"

# ───────────────────────────────────────────────────────────────────────────
log "2. The known image, and ⛔ the positive control of the tools"
if ! python3 "$QUI/02-codifica-immagine.py" --genera "$LAV" > "$LAV/scheda.json"; then
	ko "⛔ image generation failed"; exit 2
fi
ok "image generated ($(python3 -c 'import json;print(json.load(open("'"$LAV/scheda.json"'"))["byte_per_fotogramma"])') bytes per plane set)"
inf "the opposite case — the same image passed through 8 bits — is PRODUCED, not reasoned"
if python3 "$QUI/02-codifica-immagine.py" --autoprova "$LAV" > "$LAV/autoprova.json"; then
	ok "the four positive controls pass (identity, one byte flipped, 10 bits, 8 bits)"
	fatto controllo_positivo si
else
	ko "⛔ THE BENCH CANNOT MEASURE: a positive control failed"
	cat "$LAV/autoprova.json"
	fatto controllo_positivo no
	exit 1
fi

# ⛔ THE ANCHOR OF FAULT F2.3-A — see `02-codifica-guasti.py`.
#    This line is the point where the CHAIN hands the pixels to the encoder.
#    Replacing it with the opposite case, the label stays honest and the pixels do not: it is
#    exactly the defect no eye sees.
SORGENTE_VERA="$LAV/sorgente-10bit.yuv"

# ───────────────────────────────────────────────────────────────────────────
# `codifica <source> <output> <frames> <x265 options...>`
# ⛔ The encoder is asked for BY NAME and the profile is asked for EXPLICITLY.
#    No `-c:v hevc`: that choice would be made by ffmpeg, and two rounds
#    would end up in the report under the same label (CODER.md §3.9).
# ⚠ `-stream_loop` repeats the frame when more than one is needed: the
#    source is ONE only (6,220,800 bytes), and without the loop `-frames:v 3`
#    would deliver **one** frame without saying so — that is step 6 would have
#    measured three IDRs on a stream that contained one.  It happened on 12
#    Aug 2026, and it is the reason step 6 counts the groups instead of
#    trusting the number requested.
codifica_ffmpeg() {
	local sorg=$1 usc=$2 n=$3; shift 3
	local giri=$((n - 1))
	if [ "$CODEC" = av1 ]; then
		# ⛔ `-c:v libsvtav1` by name, never `-c:v av1`: in this ffmpeg there are
		#    SIX AV1 encoders and five are not this one.
		# ⚠ The quality is extracted only if it was asked for: ⛔ `${1#crf=}` on a
		#   string starting with `keyint=` returns the WHOLE string, and
		#   `-crf keyint=1` makes ffmpeg fail with an error that does not name the
		#   step.  It happened on 12 Aug 2026 at the first AV1 round.
		local crf=""
		case "$1" in crf=*) crf=${1#crf=}; crf=${crf%%:*} ;; esac
		if [ -z "$crf" ]; then
			case "$OPZIONI_GIRO_A" in crf=*) crf=${OPZIONI_GIRO_A#crf=} ;; esac
		fi
		ffmpeg -hide_banner -loglevel error -nostdin \
			-stream_loop "$giri" \
			-f rawvideo -pix_fmt yuv420p10le -s 1920x1080 -framerate 30 -i "$sorg" \
			-frames:v "$n" \
			-c:v libsvtav1 -pix_fmt yuv420p10le -preset 10 -crf "${crf:-20}" \
			-g "$([ "$n" -gt 1 ] && echo 1 || echo 999)" \
			-f obu -y "$usc"
	else
		ffmpeg -hide_banner -loglevel error -nostdin \
			-stream_loop "$giri" \
			-f rawvideo -pix_fmt yuv420p10le -s 1920x1080 -framerate 30 -i "$sorg" \
			-frames:v "$n" \
			-c:v libx265 -pix_fmt yuv420p10le -profile:v main10 \
			-x265-params "$@" \
			-f hevc -y "$usc"
	fi
}

# ⭐ The same thing, but through `src/codificatore.c`.
# ⛔ The options are NOT passed again: profile, Annex-B, bframes, GLOBAL_HEADER and the
#    16 MiB ceiling are DECISIONS of the product, and passing them from here would
#    mean measuring the command line instead of the code.  Here only what
#    the REAL caller will pass is passed — the quality and how many frames.
codifica_prodotto() {
	local sorg=$1 usc=$2 n=$3; shift 3
	local opz=$1
	# ⚠ When the caller does not say the quality (step 6 asks only for the
	#   keyframes), that of round A applies — which is NOT the same for the two codecs:
	#   HEVC lossless, AV1 at CRF 1 because SVT-AV1 has no lossless mode.
	#   ⛔ Without this line step 6 asked AV1 for «lossless» and the
	#   product REFUSED it — rightly — and the bench read «encoding
	#   failed» instead of «I did not ask properly».
	local qualita
	case "$OPZIONI_GIRO_A" in
		crf=*) qualita=(--crf "${OPZIONI_GIRO_A#crf=}") ;;
		*)     qualita=(--lossless) ;;
	esac
	case "$opz" in
		crf=*) qualita=(--crf "$(printf '%s' "${opz#crf=}" | cut -d: -f1)") ;;
	esac
	"$PROVA" --codec "$CODEC" --sorgente "$sorg" --uscita "$usc" \
		--misura 1920x1080 --fotogrammi "$n" "${qualita[@]}" \
		--confessione "${usc%.*}-prodotto.json" > /dev/null
}

codifica() {
	if [ "$CODIFICATORE" = prodotto ]; then codifica_prodotto "$@"; else codifica_ffmpeg "$@"; fi
}

# `decodifica <stream> <output>` — with the INDEPENDENT READER.
# ⛔ `-pix_fmt` is NOT passed on output: forcing it would silently convert
#    an 8-bit stream into a 10-bit file (`v<<2`), and the bench would measure its
#    own conversion instead of the stream.  It would be **E2 inside the measuring
#    tool**.  Without it, the file comes out in the NATIVE format of the stream — and if it
#    were not yuv420p10le the SIZE would not match, and the reader shouts it.
# ⚠ The reader's name is NOT the codec's name: the demuxer of a raw AV1
#   stream is called `obu`, not `av1`.  ⛔ With the wrong name ffmpeg fails
#   on EVERY stream, healthy ones included — and step 7 would say «three manglings
#   refused» having refused zero, that is the negative control would pass
#   **for the wrong reason**.  It really happened on 12 Aug 2026, and it is
#   trap no. 2 of `01-b12-guasti.py` taken from another direction.
FORMATO_LETTORE=hevc
[ "$CODEC" = av1 ] && FORMATO_LETTORE=obu
decodifica() {
	ffmpeg -hide_banner -loglevel error -nostdin -f "$FORMATO_LETTORE" -i "$1" -f rawvideo -y "$2"
}

# ⭐ The shape of the stream, read on the bytes: two twin files, one per codec.
#    ⛔ One does not pretend AV1 is Annex-B: they are two different shapes, and a reader
#       that knew only one would say «this stream has no parameter sets»
#       of a stream that must not have any.
verifica_forma() {
	local file=$1 attesi=$2 fuori=$3
	if [ "$CODEC" = av1 ]; then
		python3 "$QUI/02-codifica-obu.py" --verifica "$file" --chiavi-attese "$attesi" > "$fuori"
	else
		python3 "$QUI/02-codifica-nal.py" --verifica "$file" --idr-attesi "$attesi" > "$fuori"
	fi
}
# ⚠ The key can be nested («Y.campioni_diversi»): a reader that
#   could read only the first level would force writing python
#   inside bash quotes, which is the place where a quoting goes wrong
#   and the bench reads an empty string **without complaining**.
leggi_forma() {
	python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'):
    d = d.get(k) if isinstance(d, dict) else None
print(d)" "$1" "$2"
}
storpia_flusso() {
	if [ "$CODEC" = av1 ]; then
		python3 "$QUI/02-codifica-obu.py" --storpia "$1" "$2" "$3"
	else
		python3 "$QUI/02-codifica-nal.py" --storpia "$1" "$2" "$3"
	fi
}

# `interroga <stream> <field>` — the independent witness, which reads the SPS.
interroga() {
	ffprobe -hide_banner -v error -select_streams v:0 \
		-show_entries "stream=$2" -of "default=nk=1:nw=1" "$1"
}

# ───────────────────────────────────────────────────────────────────────────
log "3. Round A — the CHAIN: Main10 lossless, and it must come back identical"
inf "lossless because at a real bitrate HEVC destroys a 1-LSB ramp anyway,"
inf "and then a red would not tell «8 bits» from «low bitrate» — two opposite diagnoses"
FLUSSO=$LAV/A.$CODEC
if ! codifica "$SORGENTE_VERA" "$FLUSSO" 1 "$OPZIONI_GIRO_A:log-level=error"; then
	ko "⛔ lossless encoding failed: nothing to measure"; exit 1
fi
BYTE_A=$(stat -c%s "$FLUSSO")
ok "stream produced: $BYTE_A bytes"
fatto byte_flusso_lossless "$BYTE_A"

# 3a — the first witness: ffprobe, which derives the profile from the SPS
esige "3a codec, read from the stream"  "$A_CODEC"   "$(interroga "$FLUSSO" codec_name)"
esige "3a profile, read from the SPS"   "$A_PROFILO" "$(interroga "$FLUSSO" profile)"
esige "3a pixel format, from the SPS"   "$A_PIXFMT"  "$(interroga "$FLUSSO" pix_fmt)"
fatto profilo "$(interroga "$FLUSSO" profile)"
fatto pix_fmt "$(interroga "$FLUSSO" pix_fmt)"

# 3b — ⭐ the second witness, and it is the encoder itself
leggi_conf() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2]))" "$LAV/A-confessione.json" "$1"; }
if [ "$CODEC" = hevc ]; then
	python3 "$QUI/02-codifica-nal.py" --confessione "$FLUSSO" > "$LAV/A-confessione.json"
	inf "x265 confession: $(cat "$LAV/A-confessione.json")"
	esige "3b depth stated by the encoder"        "10"   "$(leggi_conf bitdepth)"
	esige "3b the encoder says ANNEX-B"           "True" "$(leggi_conf annexb)"
	esige "3b parameter sets repeated"            "True" "$(leggi_conf repeat_headers)"
	B_NON_CHIESTI=$(leggi_conf bframes)
	if [ "$CODIFICATORE" = prodotto ]; then
		# ⛔ Here the expectation is DIFFERENT, and the difference is the product's decision:
		#    x265 does `bframes=4` and `open-gop` by itself, and both cost a
		#    frame of DELAY against the 50 ms of SPECIFICHE.md §3.2.  The
		#    product FORBIDS them, and the confession must say so — or the decision
		#    was written in the report and not in the code.
		esige "3b ⭐ B frames, DECIDED and not inherited" "0" "$B_NON_CHIESTI"
		case "$(cat "$LAV/A-confessione.json")" in
			*open-gop*) ko "⛔ 3b open-gop is on: a keyframe that does not decode on its own contradicts RCP.md §5.2" ;;
			*) ok "3b open-gop off: the keyframe decodes on its own (RCP.md §5.2)" ;;
		esac
	else
		inf "⚠ and something NOBODY asked for: bframes=$B_NON_CHIESTI, open-gop, keyint=$(leggi_conf keyint)"
		inf "   ⛔ B frames cost a frame of DELAY, and v1 forbade them"
		inf "   (v1 src/codificatore.c:241 max_b_frames=0).  It is a decision the"
		inf "   product must take, not inherit silently"
	fi
	fatto bframes_non_chiesti "$B_NON_CHIESTI"
else
	# ⛔ AND THIS IS A MEASUREMENT, not a shortcoming of the bench: `[M]` 12 Aug 2026,
	#    **SVT-AV1 writes no confession in the stream**.  On HEVC the
	#    independent witnesses are two (ffprobe on the SPS and the x265 SEI); on
	#    AV1 they would be ONE, if the product did not read the sequence header by itself.
	inf "⚠ AV1: no confession in the stream — SVT-AV1 does not write one [M]"
	if [ "$CODIFICATORE" = prodotto ] && [ -f "$LAV/A-prodotto.json" ]; then
		inf "⭐ the second witness is the product itself: $(cat "$LAV/A-prodotto.json" | tr -d '\n' | cut -c1-200)"
		esige "3b the product read the sequence header from the bytes" "True" \
			"$(python3 -c "import json;print(json.load(open('$LAV/A-prodotto.json'))['letto_dal_flusso'])")"
		esige "3b depth read IN THE BYTES by the product" "10" \
			"$(python3 -c "import json;print(json.load(open('$LAV/A-prodotto.json'))['profondita_flusso'])")"
	else
		# ⚠ And it is not a red: it is a LIMIT OF THE ROUND, declared.  A red here
		#   would accuse the stream, and the real accusation goes to the tool — with
		#   `CODIFICATORE=ffmpeg` there is no second witness on AV1.
		#   ⛔ The round that certifies E2 on AV1 is `CODIFICATORE=prodotto`.
		inf "⛔ THIS ROUND DOES NOT CERTIFY E2 ON AV1: with ffmpeg the witness is ONE"
		inf "   only (ffprobe), and a component that ignores an option looks the same"
		inf "   as one that obeyed.  Redo it with CODIFICATORE=prodotto"
		fatto testimoni_indipendenti 1
	fi
	fatto bframes_non_chiesti "n/a"
fi

# 3c — the shape, read on the bytes
if verifica_forma "$FLUSSO" 1 "$LAV/A-forma.json"; then
	ok "3c the shape is the one promised to F2.5, and the first frame is a KEYFRAME"
else
	ko "⛔ 3c the stream shape is not the one F2.5 will give VideoDecoder"
	cat "$LAV/A-forma.json"
fi
inf "sequence: $(python3 -c "import json;print(' '.join(json.load(open('$LAV/A-forma.json'))['sequenza']))")"

# 3d — the PIXELS, with the independent reader
if ! decodifica "$FLUSSO" "$LAV/A.yuv"; then
	ko "⛔ 3d the independent reader did not decode the stream"
else
	DIFF_A=$(python3 -c "
import json,subprocess,sys
e=json.loads(subprocess.run([sys.executable,'$QUI/02-codifica-immagine.py','--confronta','$SORGENTE_VERA','$LAV/A.yuv'],capture_output=True,text=True).stdout)
print(0 if not e.get('confrontabili') is False and e.get('identici') else (e['Y']['campioni_diversi']+e['U']['campioni_diversi']+e['V']['campioni_diversi'] if e.get('confrontabili') else -1))
")
	if [ "$A_BYTE_DIVERSI_LOSSLESS" = -1 ]; then
		# ⚠ AV1: byte-for-byte identity is not required, and the reason is in
		#   the expectations.  ⛔ But one does NOT stop looking: the loss is required
		#   to be there and to be SMALL, or «CRF 1» would be just a word.
		inf "3d AV1 at CRF 1: differing samples $DIFF_A (identity is not required)"
		fatto campioni_diversi_lossless "$DIFF_A"
	else
		esige "3d differing samples after the lossless round" "$A_BYTE_DIVERSI_LOSSLESS" "$DIFF_A"
		fatto campioni_diversi_lossless "$DIFF_A"
	fi
fi

# 3e — ⛔ THE 10 BITS, on the DECODED and not on the source
M_VERO=$(python3 "$QUI/02-codifica-immagine.py" --livelli "$LAV/A.yuv")
inf "bit measurement on the decoded: $M_VERO"
V_VERO=$(python3 -c "import json;print(json.loads('''$M_VERO''')['verdetto'])")
L_VERO=$(python3 -c "import json;print(json.loads('''$M_VERO''')['livelli_distinti'])")
if [ "$V_VERO" = "$A_VERDETTO_VERO" ]; then
	ok "3e the 10 bits are REAL: $V_VERO"
else
	# ⛔ THE MARK OF FAULT F2.3-A.  The healthy round does not print this sentence.
	ko "⛔ 10 BITS DECLARED BUT NOT REAL: the stream declares itself $A_PROFILO and the pixels say $V_VERO"
fi
esige "3e distinct levels in the ramp" "$A_LIVELLI_VERI" "$L_VERO"
fatto verdetto_bit_vero "$V_VERO"
fatto livelli_vero "$L_VERO"

# ───────────────────────────────────────────────────────────────────────────
log "4. ⛔ THE OPPOSITE CASE — what the contrary would look like (LEZIONI.md §1.11)"
inf "the SAME image passed through 8 bits and put back in a 10-bit container."
inf "⭐ If the bench did not tell this round from the previous one, it would not be"
inf "   measuring the 10 bits: it would be measuring that the stream exists."
OPPOSTO=$LAV/O.$CODEC
if ! codifica "$LAV/sorgente-8in10.yuv" "$OPPOSTO" 1 "$OPZIONI_GIRO_A:log-level=error"; then
	ko "⛔ encoding of the opposite case failed"
else
	# 4a — ⭐ and the label stays HONEST: it is the content that lies
	esige "4a profile of the opposite case" "$A_PROFILO" "$(interroga "$OPPOSTO" profile)"
	esige "4a pix_fmt of the opposite case" "$A_PIXFMT"  "$(interroga "$OPPOSTO" pix_fmt)"
	inf "⭐ here is the point: the label is IDENTICAL to that of the real round, and it is correct."
	inf "   The encoder IS Main10.  It is the CHAIN that gave it 8 bits."
	inf "   Whoever stopped at ffprobe would write «10 bits» in the report (E1)."
	if decodifica "$OPPOSTO" "$LAV/O.yuv"; then
		M_OPP=$(python3 "$QUI/02-codifica-immagine.py" --livelli "$LAV/O.yuv")
		inf "bit measurement on the opposite case: $M_OPP"
		V_OPP=$(python3 -c "import json;print(json.loads('''$M_OPP''')['verdetto'])")
		L_OPP=$(python3 -c "import json;print(json.loads('''$M_OPP''')['livelli_distinti'])")
		esige "4b verdict on the opposite case"  "$A_VERDETTO_8IN10" "$V_OPP"
		esige "4b levels on the opposite case"   "$A_LIVELLI_8IN10"  "$L_OPP"
		fatto verdetto_bit_opposto "$V_OPP"
		fatto livelli_opposto "$L_OPP"
	else
		ko "⛔ 4b the opposite case did not decode"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "5. Round B — the RENDERING: how much is lost at CRF $CRF_RESA"
inf "⚠ CRF $CRF_RESA is not the working point of the product — that is phase 9."
inf "   Here it only serves to know that the stream holds also when it is not lossless."
RESA=$LAV/B.$CODEC
if ! codifica "$SORGENTE_VERA" "$RESA" 1 "crf=$CRF_RESA:log-level=error"; then
	ko "⛔ 5 encoding at CRF $CRF_RESA failed"
else
	BYTE_B=$(stat -c%s "$RESA")
	inf "stream: $BYTE_B bytes against the $BYTE_A of the lossless"
	esige "5 profile also at CRF $CRF_RESA" "$A_PROFILO" "$(interroga "$RESA" profile)"
	if verifica_forma "$RESA" 1 "$LAV/B-forma.json"; then
		ok "5 the shape holds also at CRF $CRF_RESA"
	else
		ko "⛔ 5 the shape changes with the bitrate"; cat "$LAV/B-forma.json"
	fi
	if decodifica "$RESA" "$LAV/B.yuv"; then
		C_B=$(python3 "$QUI/02-codifica-immagine.py" --confronta "$SORGENTE_VERA" "$LAV/B.yuv")
		inf "loss at CRF $CRF_RESA: $C_B"
		MAXY=$(python3 -c "import json;print(json.loads('''$C_B''')['Y']['differenza_massima'])")
		# ⛔ ZERO loss at CRF 20 would mean that CRF was not applied,
		#    and it would be an E2 (the option silently ignored), not a success.
		if [ "$MAXY" -gt 0 ]; then ok "5 there is loss, as there must be: maximum Y difference = $MAXY"
		else ko "⛔ 5 ZERO loss at CRF $CRF_RESA: the option was not applied"; fi
		fatto perdita_massima_y_crf "$MAXY"
		fatto byte_flusso_crf "$BYTE_B"
	else
		ko "⛔ 5 the stream at CRF $CRF_RESA does not decode"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "6. The parameter sets in front of EVERY keyframe — the half that gets forgotten"
inf "a single frame has them necessarily.  The trouble comes in phase 3, when a"
inf "client connects midway and receives a NAKED IDR: black screen WITH the frames"
inf "arriving.  v1 forbade it by hand (src/codificatore.c:268-272)."
TRE=$LAV/G.$CODEC
if ! codifica "$SORGENTE_VERA" "$TRE" 3 "keyint=1:min-keyint=1:log-level=error"; then
	ko "⛔ 6 encoding with three keyframes failed"
else
	if verifica_forma "$TRE" "$A_GRUPPI_IDR_3" "$LAV/G-forma.json"; then
		ok "6 the parameter sets in front of all $A_GRUPPI_IDR_3 keyframes"
	else
		ko "⛔ 6 the parameter sets do NOT precede every keyframe"; cat "$LAV/G-forma.json"
	fi
	if [ "$CODEC" = av1 ]; then
		G_GRUPPI=$(leggi_forma "$LAV/G-forma.json" sequenze_prima_di_una_chiave)
	else
		G_GRUPPI=$(leggi_forma "$LAV/G-forma.json" gruppi_parametri_prima_di_un_IDR)
	fi
	esige "6 groups of parameter sets" "$A_GRUPPI_IDR_3" "$G_GRUPPI"
	fatto gruppi_parametri "$G_GRUPPI"
fi

# ───────────────────────────────────────────────────────────────────────────
log "7. ⛔ NEGATIVE CONTROL — a mangled stream MUST be refused"
inf "and «refused» here does NOT mean «exit status other than zero»:"
inf "⛔ two manglings out of three pass with exit 0 and ffmpeg CONCEALS (measured)."
inf "   Refused = zero frames OR pixels different from the source."
RIFIUTATE=0
MODI="senza-parametri byte-girato troncato"
[ "$CODEC" = av1 ] && MODI="senza-sequenza byte-girato troncato"
for MODO in $MODI; do
	storpia_flusso "$FLUSSO" "$MODO" "$LAV/S-$MODO.$CODEC" > "$LAV/S-$MODO.json"
	# ⛔ The exit status is CAPTURED, not thrown into a chain of pipes.
	decodifica "$LAV/S-$MODO.$CODEC" "$LAV/S-$MODO.yuv"
	USCITA=$?
	BYTE=$(stat -c%s "$LAV/S-$MODO.yuv" 2> "$LAV/S-$MODO.stat" || echo 0)
	if [ "$BYTE" = 0 ]; then
		ok "7 «$MODO»: refused — zero frames (exit $USCITA)"
		RIFIUTATE=$((RIFIUTATE+1))
	elif cmp -s "$SORGENTE_VERA" "$LAV/S-$MODO.yuv"; then
		# ⛔ This is the case that condemns the BENCH, not the stream.
		ko "⛔ 7 «$MODO»: exit $USCITA AND PIXELS IDENTICAL TO THE SOURCE."
		ko "   the mangling did not bite: this bench CANNOT SEE A REFUSAL"
	else
		DIVERSI=$(cmp -l "$SORGENTE_VERA" "$LAV/S-$MODO.yuv" | wc -l)
		ok "7 «$MODO»: refused in the PIXELS — $DIVERSI differing bytes (exit $USCITA)"
		RIFIUTATE=$((RIFIUTATE+1))
	fi
done
esige "7 manglings refused" "$A_STORPIATURE_RIFIUTATE" "$RIFIUTATE"
fatto storpiature_rifiutate "$RIFIUTATE"

# ───────────────────────────────────────────────────────────────────────────
# ⛔⭐ 8. THE REAL ROAD — the one starting from BGRx, that is from CAPTURE
#
# Steps 1 to 7 enter from an image already in 10-bit YCbCr: it is the known
# scene, and it serves to measure **the encoder** without measuring at the same time the
# colour conversion.  ⛔ But the GNOME capture does not deliver that:
# it delivers **8-bit BGRx** (`[M]` F2.2, Mutter does only BGRx/BGRA).
#
# ⇒ This step measures the road the product will really travel, and finds
#   two things none of the other seven could find.
if [ "$CODIFICATORE" = prodotto ] && [ "$CODEC" = hevc ]; then
	log "8. ⛔ The REAL road: from BGRx, as the capture delivers"
	if ! ffmpeg -hide_banner -loglevel error -nostdin -f rawvideo -pix_fmt yuv420p10le \
		-s 1920x1080 -i "$SORGENTE_VERA" -pix_fmt bgr0 -f rawvideo -y "$LAV/scena.bgrx"; then
		ko "⛔ 8 the BGRx source was not built"
	elif ! "$PROVA" --codec hevc --formato bgrx --sorgente "$LAV/scena.bgrx" \
		--uscita "$LAV/X.hevc" --lossless --confessione "$LAV/X.json" > /dev/null; then
		ko "⛔ 8 the product did not encode the BGRx road"
	else
		# 8a — ⭐ THE MATRIX IS THE ONE WE SAY, and the witness is independent.
		#      The same BGRx is converted with ffmpeg's swscale declaring the
		#      SAME four things (BT.709, full source, limited output), and
		#      **byte-for-byte identity** is required.  ⛔ If they differed, our
		#      conversion would use a matrix different from the declared one — and
		#      F2.6, which compares pixels, would measure the matrix instead of the
		#      chain.
		ffmpeg -hide_banner -loglevel error -nostdin -f rawvideo -pix_fmt bgr0 -s 1920x1080 \
			-i "$LAV/scena.bgrx" \
			-vf "scale=in_range=full:out_range=limited:in_color_matrix=bt709:out_color_matrix=bt709:sws_flags=bilinear" \
			-pix_fmt yuv420p10le -f rawvideo -y "$LAV/X-ffmpeg.yuv"
		decodifica "$LAV/X.hevc" "$LAV/X.yuv"
		python3 "$QUI/02-codifica-immagine.py" --confronta "$LAV/X-ffmpeg.yuv" "$LAV/X.yuv" \
			> "$LAV/X-confronto.json"
		X_DIFF=$(( $(leggi_forma "$LAV/X-confronto.json" Y.campioni_diversi) \
		         + $(leggi_forma "$LAV/X-confronto.json" U.campioni_diversi) \
		         + $(leggi_forma "$LAV/X-confronto.json" V.campioni_diversi) ))
		esige "8a our BGRx→YUV conversion against ffmpeg's" "0" "$X_DIFF"
		fatto conversione_diversa_da_ffmpeg "$X_DIFF"

		# 8b — ⛔ THE PROMOTION, DECLARED.  The source has 8 real bits; the stream
		#      will say «Main 10» anyway.  `DECISIONI.md` §2.7: a silent
		#      fallback stays forbidden even when the fault is not ours.
		esige "8b the product DECLARES the 8→10 promotion" "True" \
			"$(leggi_forma "$LAV/X.json" promozione_8_a_10)"

		# 8c — ⛔⛔ AND HERE THE BENCH SAYS SOMETHING NOBODY WANTED TO HEAR.
		#      On steps 3-4 the 10-bit gauge tells 877 from 220 and 0.25 from
		#      1.000.  ⛔ After an RGB→YUV conversion **the signature of the multiples of
		#      4 does NOT survive**: the matrix scatters the values, and the meter
		#      says «10-bit-veri» of a chain that carries EIGHT.
		#      ⇒ On this road the meter's verdict is a FALSE GREEN, and
		#        what remains is the LEVEL COUNT: 256 instead of 877.
		#      ⚠ The same thing had already been written for probe S2 of phase 1
		#        (`FASI.md` §02-primo-fotogramma): real bits are measured AT THE
		#        SOURCE, or not at all.
		python3 "$QUI/02-codifica-immagine.py" --livelli "$LAV/X.yuv" > "$LAV/X-livelli.json"
		inf "bit measurement after the conversion: $(cat "$LAV/X-livelli.json")"
		X_LIV=$(leggi_forma "$LAV/X-livelli.json" livelli_distinti)
		X_VER=$(leggi_forma "$LAV/X-livelli.json" verdetto)
		esige "8c distinct levels on the BGRx road (8 bits promoted)" "256" "$X_LIV"
		if [ "$X_VER" = "10-bit-veri" ]; then
			inf "⛔ and the VERDICT here says «$X_VER» of an EIGHT-bit chain:"
			inf "   the signature of the multiples of 4 does not survive the RGB→YUV matrix."
			inf "   ⇒ on this road the gauge that counts is the COUNT ($X_LIV against 877),"
			inf "     and the rest is said by the product declaring the promotion (8b)"
		fi
		fatto livelli_strada_bgrx "$X_LIV"
		fatto verdetto_strada_bgrx "$X_VER"
		X_CONV=$(leggi_forma "$LAV/X.json" us_conversione)
		fatto us_conversione_bgrx "$X_CONV"
		inf "⚠ conversion: $X_CONV µs at 1920x1080.  v1 had measured 12.5 ms at"
		inf "   2560x1024 in NV12 and called it a bottleneck: the number must be"
		inf "   reread every time, not copied"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "The log, and the verdict"
python3 - "$FATTI" "$ESITI" "$SCENA" "$OK" "$NO" <<'PYFINE'
import json, sys, datetime, os, socket
fatti, esiti, scena, ok, no = sys.argv[1:6]
d = {}
with open(fatti) as f:
    for r in f:
        if "\t" in r:
            k, _, v = r.rstrip("\n").partition("\t")
            d[k] = v
riga = {
    "banco": "F2.3-codifica",
    "scena": scena,
    "macchina": socket.gethostname(),
    "ora": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "controlli_passati": int(ok), "controlli_falliti": int(no),
    "esito": "verde" if int(no) == 0 else "rosso",
    "misure": d,
}
with open(esiti, "a") as f:
    f.write(json.dumps(riga, ensure_ascii=False) + "\n")
print(json.dumps(riga, ensure_ascii=False, indent=2))
PYFINE
inf "line appended to $ESITI"

printf '\n'
if [ "$NO" -eq 0 ]; then
	printf '\033[1;32m  VERDE — %d checks passed, 0 failed\033[0m\n' "$OK"
	printf '  ⚠ and «green» here means: the stream is real Main10, Annex-B, with the first\n'
	printf '    frame a keyframe, and a second reader re-decodes it identical.\n'
	printf '    ⛔ It does NOT mean that a browser decodes it: that is F2.5, and the\n'
	printf '    phone is F2.6.\n'
	exit 0
else
	printf '\033[1;31m  ROSSO — %d checks failed out of %d\033[0m\n' "$NO" "$((OK+NO))"
	exit 1
fi
