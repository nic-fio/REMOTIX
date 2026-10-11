#!/bin/bash
#
# 02-encoding-launch.sh — F2.3: HEVC encoding in software, measured on the pixels.
#
#   bash benches/02-encoding-launch.sh              the whole round
#   bash benches/02-encoding-launch.sh list       what it would test, and with which expectations
#   WORKDIR=/altrove bash benches/02-encoding-launch.sh different working folder
#
#   ⭐ ENCODER=ffmpeg|product   WHO encodes.  `ffmpeg` is the round this
#                                    bench was born with — when the product did not
#                                    exist.  `product` points at
#                                    `src/encoder.c` through
#                                    `02-encoding-test` (built by
#                                    `02-encoding-build.sh`).
#   ⭐ CODEC=hevc|av1                 WHICH codec.  They are TWO by decision
#                                    of the user of 12 Aug 2026
#                                    (`DECISIONS.md` §1.13): HEVC main, AV1
#                                    negotiated fallback.
#
# ⛔ And the two levers exist because a bench pointed at `ffmpeg` certifies
#    **ffmpeg**: a green round there says nothing about our encoder.  It is
#    form E10 of `REVIEWER.md` §2 — *«a green test on the wrong client»* —
#    with the wrong defendant.
#
# Exits **0** if everything holds, **1** if something is red, **2** if it could not
# look.  ⛔ And «I could not look» is NOT «fine»: they are three outcomes, not
# two (`LESSONS.md` §1.9; it was born in `01-b0-terreno.sh`, retired 11 Oct 2026).
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
#      depth that `SPECS.md` §3.1 asks for as **desired** is not there.
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
# `02-encoding-image.py`, which declares every band and the defect it unmasks.
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
# The reasoning in full is in `02-encoding-image.py`.
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
#     F2.5, and the probe on the phone is F2.6 (`PLAN.md` §«Phase 2», the two points);
#   - **it proves nothing about rate or delay.**  A single frame;
#   - **it does not touch the GPU.**  Encoding here is in software **on purpose**:
#     acceleration is phase 8, and putting it first would mean not knowing
#     which of the two pieces is wrong (`PLAN.md` §«Phase 2»);
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

HERE=$(cd "$(dirname "$0")" && pwd)
WORKDIR=${WORKDIR:-/tmp/02-codifica}
OUTCOMES=${OUTCOMES:-$HERE/02-encoding-outcomes.jsonl}
ENCODER=${ENCODER:-ffmpeg}
CODEC=${CODEC:-hevc}
TEST=$HERE/02-encoding-test
SCENE="SCENE-2.3-A · known image 1920x1080 yuv420p10le BT.709 limited range, still"
SCENE="$SCENE · codificatore=$ENCODER · codec=$CODEC"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { OK=$((OK+1)); printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { NO=$((NO+1)); printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }
OK=0; NO=0

# ⛔ Every measurement ends up in here, and from here comes the log line: if a
#    number did not pass through here, it is not in the log — instead of being
#    copied by hand from what one remembers.
DONE=$WORKDIR/fatti.tsv
completed() { printf '%s\t%s\n' "$1" "$2" >> "$DONE"; }

# `require <label> <expected> <obtained>` — and the expectation ALWAYS appears
# in the output, even when it matches: a bench that prints the number only
# when it is wrong forces you to reread the code to know what it was looking for.
require() {
	if [ "$2" = "$3" ]; then ok "$1: $3 (expected $2)"; else ko "$1: $3 ⛔ EXPECTED $2"; fi
}

# ═══════════════════════════════════════════════════════════════════════════
# THE EXPECTATIONS, WRITTEN BEFORE THE ROUND  (`PLAN.md` §0.3 rule 4)
# ═══════════════════════════════════════════════════════════════════════════
if [ "$CODEC" = av1 ]; then
	# ⚠ AV1 has ONE single profile for 4:2:0 at 10 bits, and it is called «Main»: it is not
	#   a poorer profile than Main10, it is the same thing with another name —
	#   the depth sits in `high_bitdepth` of the sequence header, not in the
	#   profile.  Whoever compared the two labels would write «AV1 is 8-bit».
	A_PROFILE="Main"
	A_PIXFMT="yuv420p10le"
	A_CODEC="av1"
	# ⛔ And AV1's round A is NOT lossless, because SVT-AV1 2.3.0 has no
	#    lossless mode — `[M]` 12 Aug 2026: `lossless=1` prints «Error
	#    parsing option» and **goes on exiting 0**.  ⭐ The closest regime is
	#    CRF 1, and it is MEASURED that the 10-bit gauge holds intact there: 877
	#    levels on the real source, 220 with 1.000 of multiples of 4 on the opposite
	#    case.  ⚠ What is lost is byte-for-byte identity: here the
	#    expected differing samples are not zero, and one does not pretend they are.
	ROUND_A_OPTIONS="crf=1"
	A_DIFFERENT_BYTES_LOSSLESS=-1        # ⚠ -1 = «identity is not required»
else
	A_PROFILE="Main 10"
	A_PIXFMT="yuv420p10le"
	A_CODEC="hevc"
	ROUND_A_OPTIONS="lossless=1"
fi
A_PROFILE_HEVC="Main 10"
A_REAL_LEVELS=877          # all the integers from 64 to 940
A_LEVELS_8IN10=220         # from 64 to 940 in steps of 4
A_M4_8IN10="1.0"            # every 8-bit sample promoted to 10 is v<<2
A_VERDICT_REAL="10-bit-veri"
A_VERDICT_8IN10="8-bit-travestiti"
[ "$CODEC" = av1 ] || A_DIFFERENT_BYTES_LOSSLESS=0   # ⛔ lossless: identical byte by byte
A_GROUPS_IDR_3=3            # three IDRs, three times VPS+SPS+PPS in front
A_REFUSED_MANGLINGS=3   # all three, or the bench cannot see a refusal
RENDER_CRF=20                 # round B.  ⚠ it is not the working point of the
                            #   product: that is phase 9

if [ "${1:-}" = list ]; then
	cat <<-FINE
	F2.3 — what it tests, and with which expectations written beforehand

	  1  ffmpeg/ffprobe are there, and libx265 is there  present, version printed
	  2  ⛔ positive control of the four tools            all four
	  3  round A: libx265 asked for BY NAME, Main10 lossless
	     3a  ffprobe reads from the STREAM   codec=$A_CODEC profile=«$A_PROFILE» pix_fmt=$A_PIXFMT
	     3b  ⭐ x265 confession in the stream             bitdepth=10, annexb, repeat-headers
	     3c  Annex-B shape: VPS,SPS,PPS then IDR         and the first frame is a KEYFRAME
	     3d  decoded pixels against source               $A_DIFFERENT_BYTES_LOSSLESS differing bytes
	     3e  the 10 bits on the DECODED                  $A_VERDICT_REAL, $A_REAL_LEVELS levels
	  4  ⛔ OPPOSITE CASE: the same image passed through 8 bits
	     4a  the label STILL says «$A_PROFILE»           ⭐ and it is honest: it is the stream that lies
	     4b  the 10 bits on the decoded                  $A_VERDICT_8IN10, $A_LEVELS_8IN10 levels
	  5  round B: the rendering at CRF $RENDER_CRF               loss > 0, and the stream holds
	  6  three frames with -g 1                         $A_GROUPS_IDR_3 groups of parameter sets
	  7  ⛔ negative control: three manglings            $A_REFUSED_MANGLINGS refused
	  8  ⛔ the REAL road, from BGRx (only ENCODER=product and CODEC=hevc)
	     8a  our conversion against ffmpeg's             0 differing samples
	     8b  the 8→10 promotion DECLARED                 True
	     8c  ⛔ the levels after the matrix               256, and NOT 877

	  who encodes: $ENCODER          codec: $CODEC
	FINE
	exit 0
fi

mkdir -p "$WORKDIR" || { echo "⛔ cannot create $WORKDIR"; exit 2; }
: > "$DONE"

# ───────────────────────────────────────────────────────────────────────────
log "1. The terrain: are the tools the ones I believe?"
# ⛔ The lesson of `01-b0-terreno.sh` (retired, DECISIONI §10.44): twice in one day a bench was green on a
#    terrain that was not the one we believed.  Here the terrain is ffmpeg.
for prog in ffmpeg ffprobe python3; do
	if command -v "$prog" > /dev/null; then ok "$prog: $(command -v "$prog")"
	else ko "⛔ missing $prog"; exit 2; fi
done
# ⚠ No pipe in here, for the reason written ten lines further down.
VER_FFMPEG=$(ffmpeg -hide_banner -version)
VER_FFMPEG=${VER_FFMPEG%%$'\n'*}
inf "$VER_FFMPEG"
completed ffmpeg "$VER_FFMPEG"
# ⛔ AND HERE THE BENCH BIT ITSELF, on 12 Aug 2026 — worth keeping it
#    written.  The first draft said `ffmpeg -encoders | grep -q libx265`: with
#    `set -o pipefail`, `grep -q` closes the pipe at the first match, ffmpeg dies
#    of SIGPIPE (141) and **the pipeline reports a failure precisely when the
#    thing looked for IS THERE**.  The bench declared «libx265 is not there» on a
#    machine that has it.  It is `LESSONS.md` §1.9 the other way round — not zero read
#    as a fault, but **success** read as a fault — and it is the reason why
#    the output is captured in a variable and examined outside the pipe.
LIST_ENC=$(ffmpeg -hide_banner -encoders)
ENC_STATUS=$?
if [ "$ENC_STATUS" -ne 0 ]; then
	ko "⛔ «ffmpeg -encoders» exited $ENC_STATUS: I could not look"; exit 2
fi
EXPECTED_COMPONENT=libx265
[ "$CODEC" = av1 ] && EXPECTED_COMPONENT=libsvtav1
case "$LIST_ENC" in
	*"$EXPECTED_COMPONENT"*) ok "$EXPECTED_COMPONENT is there — ⛔ and it will be asked for BY NAME, not with -c:v $CODEC (CODER.md §3.9)" ;;
	*) ko "⛔ $EXPECTED_COMPONENT is not there: this bench has nothing to measure"; exit 2 ;;
esac
# ⛔ And if the PRODUCT is measured, the product must be there — and it must be NEWER
#    than the source, or an old version would be measured while believing to
#    measure the one just written.  It is the lesson of the evening of 12 Aug: «the
#    product on the server was not the product we had written».
if [ "$ENCODER" = product ]; then
	if [ ! -x "$TEST" ]; then
		ko "⛔ $TEST is missing: it is built with «bash benches/02-encoding-build.sh»"
		exit 2
	fi
	if [ "$HERE/../src/encoder.c" -nt "$TEST" ] || [ "$HERE/../src/encoder.h" -nt "$TEST" ]; then
		ko "⛔ src/encoder.c is NEWER than the tool: an old version"
		ko "   would be measured.  Rebuild before measuring"
		exit 2
	fi
	ok "product tool: $TEST, more recent than the source"
fi
inf "working folder: $WORKDIR"
inf "port used: ⛔ NONE (7513 assigned to F2.3 stays free: nobody listens here)"

# ───────────────────────────────────────────────────────────────────────────
log "2. The known image, and ⛔ the positive control of the tools"
if ! python3 "$HERE/02-encoding-image.py" --generate "$WORKDIR" > "$WORKDIR/scheda.json"; then
	ko "⛔ image generation failed"; exit 2
fi
ok "image generated ($(python3 -c 'import json;print(json.load(open("'"$WORKDIR/scheda.json"'"))["byte_per_fotogramma"])') bytes per plane set)"
inf "the opposite case — the same image passed through 8 bits — is PRODUCED, not reasoned"
if python3 "$HERE/02-encoding-image.py" --selftest "$WORKDIR" > "$WORKDIR/autoprova.json"; then
	ok "the four positive controls pass (identity, one byte flipped, 10 bits, 8 bits)"
	completed controllo_positivo si
else
	ko "⛔ THE BENCH CANNOT MEASURE: a positive control failed"
	cat "$WORKDIR/autoprova.json"
	completed controllo_positivo no
	exit 1
fi

# ⛔ THE ANCHOR OF FAULT F2.3-A — see `02-codifica-guasti.py`.
#    This line is the point where the CHAIN hands the pixels to the encoder.
#    Replacing it with the opposite case, the label stays honest and the pixels do not: it is
#    exactly the defect no eye sees.
REAL_SOURCE="$WORKDIR/sorgente-10bit.yuv"

# ───────────────────────────────────────────────────────────────────────────
# `encode <source> <output> <frames> <x265 options...>`
# ⛔ The encoder is asked for BY NAME and the profile is asked for EXPLICITLY.
#    No `-c:v hevc`: that choice would be made by ffmpeg, and two rounds
#    would end up in the report under the same label (CODER.md §3.9).
# ⚠ `-stream_loop` repeats the frame when more than one is needed: the
#    source is ONE only (6,220,800 bytes), and without the loop `-frames:v 3`
#    would deliver **one** frame without saying so — that is step 6 would have
#    measured three IDRs on a stream that contained one.  It happened on 12
#    Aug 2026, and it is the reason step 6 counts the groups instead of
#    trusting the number requested.
encode_ffmpeg() {
	local source_dir=$1 usc=$2 n=$3; shift 3
	local rounds=$((n - 1))
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
			case "$ROUND_A_OPTIONS" in crf=*) crf=${ROUND_A_OPTIONS#crf=} ;; esac
		fi
		ffmpeg -hide_banner -loglevel error -nostdin \
			-stream_loop "$rounds" \
			-f rawvideo -pix_fmt yuv420p10le -s 1920x1080 -framerate 30 -i "$source_dir" \
			-frames:v "$n" \
			-c:v libsvtav1 -pix_fmt yuv420p10le -preset 10 -crf "${crf:-20}" \
			-g "$([ "$n" -gt 1 ] && echo 1 || echo 999)" \
			-f obu -y "$usc"
	else
		ffmpeg -hide_banner -loglevel error -nostdin \
			-stream_loop "$rounds" \
			-f rawvideo -pix_fmt yuv420p10le -s 1920x1080 -framerate 30 -i "$source_dir" \
			-frames:v "$n" \
			-c:v libx265 -pix_fmt yuv420p10le -profile:v main10 \
			-x265-params "$@" \
			-f hevc -y "$usc"
	fi
}

# ⭐ The same thing, but through `src/encoder.c`.
# ⛔ The options are NOT passed again: profile, Annex-B, bframes, GLOBAL_HEADER and the
#    16 MiB ceiling are DECISIONS of the product, and passing them from here would
#    mean measuring the command line instead of the code.  Here only what
#    the REAL caller will pass is passed — the quality and how many frames.
encode_product() {
	local source_dir=$1 usc=$2 n=$3; shift 3
	local opt=$1
	# ⚠ When the caller does not say the quality (step 6 asks only for the
	#   keyframes), that of round A applies — which is NOT the same for the two codecs:
	#   HEVC lossless, AV1 at CRF 1 because SVT-AV1 has no lossless mode.
	#   ⛔ Without this line step 6 asked AV1 for «lossless» and the
	#   product REFUSED it — rightly — and the bench read «encoding
	#   failed» instead of «I did not ask properly».
	local quality
	case "$ROUND_A_OPTIONS" in
		crf=*) quality=(--crf "${ROUND_A_OPTIONS#crf=}") ;;
		*)     quality=(--lossless) ;;
	esac
	case "$opt" in
		crf=*) quality=(--crf "$(printf '%s' "${opt#crf=}" | cut -d: -f1)") ;;
	esac
	"$TEST" --codec "$CODEC" --source "$source_dir" --output "$usc" \
		--size 1920x1080 --frames "$n" "${quality[@]}" \
		--confession "${usc%.*}-prodotto.json" > /dev/null
}

encode() {
	if [ "$ENCODER" = product ]; then encode_product "$@"; else encode_ffmpeg "$@"; fi
}

# `decode <stream> <output>` — with the INDEPENDENT READER.
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
READER_FORMAT=hevc
[ "$CODEC" = av1 ] && READER_FORMAT=obu
decode() {
	ffmpeg -hide_banner -loglevel error -nostdin -f "$READER_FORMAT" -i "$1" -f rawvideo -y "$2"
}

# ⭐ The shape of the stream, read on the bytes: two twin files, one per codec.
#    ⛔ One does not pretend AV1 is Annex-B: they are two different shapes, and a reader
#       that knew only one would say «this stream has no parameter sets»
#       of a stream that must not have any.
verify_shape() {
	local file=$1 expected_vals=$2 report=$3
	if [ "$CODEC" = av1 ]; then
		python3 "$HERE/02-encoding-obu.py" --verify "$file" --expected-keys "$expected_vals" > "$report"
	else
		python3 "$HERE/02-encoding-nal.py" --verify "$file" --expected-idr "$expected_vals" > "$report"
	fi
}
# ⚠ The key can be nested («Y.campioni_diversi»): a reader that
#   could read only the first level would force writing python
#   inside bash quotes, which is the place where a quoting goes wrong
#   and the bench reads an empty string **without complaining**.
read_shape() {
	python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'):
    d = d.get(k) if isinstance(d, dict) else None
print(d)" "$1" "$2"
}
mangle_stream() {
	if [ "$CODEC" = av1 ]; then
		python3 "$HERE/02-encoding-obu.py" --mangle "$1" "$2" "$3"
	else
		python3 "$HERE/02-encoding-nal.py" --mangle "$1" "$2" "$3"
	fi
}

# `queries <stream> <field>` — the independent witness, which reads the SPS.
queries() {
	ffprobe -hide_banner -v error -select_streams v:0 \
		-show_entries "stream=$2" -of "default=nk=1:nw=1" "$1"
}

# ───────────────────────────────────────────────────────────────────────────
log "3. Round A — the CHAIN: Main10 lossless, and it must come back identical"
inf "lossless because at a real bitrate HEVC destroys a 1-LSB ramp anyway,"
inf "and then a red would not tell «8 bits» from «low bitrate» — two opposite diagnoses"
FLOW=$WORKDIR/A.$CODEC
if ! encode "$REAL_SOURCE" "$FLOW" 1 "$ROUND_A_OPTIONS:log-level=error"; then
	ko "⛔ lossless encoding failed: nothing to measure"; exit 1
fi
BYTE_A=$(stat -c%s "$FLOW")
ok "stream produced: $BYTE_A bytes"
completed byte_flusso_lossless "$BYTE_A"

# 3a — the first witness: ffprobe, which derives the profile from the SPS
require "3a codec, read from the stream"  "$A_CODEC"   "$(queries "$FLOW" codec_name)"
require "3a profile, read from the SPS"   "$A_PROFILE" "$(queries "$FLOW" profile)"
require "3a pixel format, from the SPS"   "$A_PIXFMT"  "$(queries "$FLOW" pix_fmt)"
completed profilo "$(queries "$FLOW" profile)"
completed pix_fmt "$(queries "$FLOW" pix_fmt)"

# 3b — ⭐ the second witness, and it is the encoder itself
read_conf() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2]))" "$WORKDIR/A-confessione.json" "$1"; }
if [ "$CODEC" = hevc ]; then
	python3 "$HERE/02-encoding-nal.py" --confession "$FLOW" > "$WORKDIR/A-confessione.json"
	inf "x265 confession: $(cat "$WORKDIR/A-confessione.json")"
	require "3b depth stated by the encoder"        "10"   "$(read_conf bitdepth)"
	require "3b the encoder says ANNEX-B"           "True" "$(read_conf annexb)"
	require "3b parameter sets repeated"            "True" "$(read_conf repeat_headers)"
	B_UNREQUESTED=$(read_conf bframes)
	if [ "$ENCODER" = product ]; then
		# ⛔ Here the expectation is DIFFERENT, and the difference is the product's decision:
		#    x265 does `bframes=4` and `open-gop` by itself, and both cost a
		#    frame of DELAY against the 50 ms of SPECS.md §3.2.  The
		#    product FORBIDS them, and the confession must say so — or the decision
		#    was written in the report and not in the code.
		require "3b ⭐ B frames, DECIDED and not inherited" "0" "$B_UNREQUESTED"
		case "$(cat "$WORKDIR/A-confessione.json")" in
			*open-gop*) ko "⛔ 3b open-gop is on: a keyframe that does not decode on its own contradicts RCP.md §5.2" ;;
			*) ok "3b open-gop off: the keyframe decodes on its own (RCP.md §5.2)" ;;
		esac
	else
		inf "⚠ and something NOBODY asked for: bframes=$B_UNREQUESTED, open-gop, keyint=$(read_conf keyint)"
		inf "   ⛔ B frames cost a frame of DELAY, and v1 forbade them"
		inf "   (v1 src/encoder.c:241 max_b_frames=0).  It is a decision the"
		inf "   product must take, not inherit silently"
	fi
	completed bframes_non_chiesti "$B_UNREQUESTED"
else
	# ⛔ AND THIS IS A MEASUREMENT, not a shortcoming of the bench: `[M]` 12 Aug 2026,
	#    **SVT-AV1 writes no confession in the stream**.  On HEVC the
	#    independent witnesses are two (ffprobe on the SPS and the x265 SEI); on
	#    AV1 they would be ONE, if the product did not read the sequence header by itself.
	inf "⚠ AV1: no confession in the stream — SVT-AV1 does not write one [M]"
	if [ "$ENCODER" = product ] && [ -f "$WORKDIR/A-prodotto.json" ]; then
		inf "⭐ the second witness is the product itself: $(cat "$WORKDIR/A-prodotto.json" | tr -d '\n' | cut -c1-200)"
		require "3b the product read the sequence header from the bytes" "True" \
			"$(python3 -c "import json;print(json.load(open('$WORKDIR/A-prodotto.json'))['letto_dal_flusso'])")"
		require "3b depth read IN THE BYTES by the product" "10" \
			"$(python3 -c "import json;print(json.load(open('$WORKDIR/A-prodotto.json'))['profondita_flusso'])")"
	else
		# ⚠ And it is not a red: it is a LIMIT OF THE ROUND, declared.  A red here
		#   would accusations the stream, and the real accusation goes to the tool — with
		#   `ENCODER=ffmpeg` there is no second witness on AV1.
		#   ⛔ The round that certifies E2 on AV1 is `ENCODER=product`.
		inf "⛔ THIS ROUND DOES NOT CERTIFY E2 ON AV1: with ffmpeg the witness is ONE"
		inf "   only (ffprobe), and a component that ignores an option looks the same"
		inf "   as one that obeyed.  Redo it with ENCODER=product"
		completed testimoni_indipendenti 1
	fi
	completed bframes_non_chiesti "n/a"
fi

# 3c — the shape, read on the bytes
if verify_shape "$FLOW" 1 "$WORKDIR/A-forma.json"; then
	ok "3c the shape is the one promised to F2.5, and the first frame is a KEYFRAME"
else
	ko "⛔ 3c the stream shape is not the one F2.5 will give VideoDecoder"
	cat "$WORKDIR/A-forma.json"
fi
inf "sequence: $(python3 -c "import json;print(' '.join(json.load(open('$WORKDIR/A-forma.json'))['sequenza']))")"

# 3d — the PIXELS, with the independent reader
if ! decode "$FLOW" "$WORKDIR/A.yuv"; then
	ko "⛔ 3d the independent reader did not decode the stream"
else
	DIFF_A=$(python3 -c "
import json,subprocess,sys
e=json.loads(subprocess.run([sys.executable,'$HERE/02-encoding-image.py','--compare','$REAL_SOURCE','$WORKDIR/A.yuv'],capture_output=True,text=True).stdout)
print(0 if not e.get('confrontabili') is False and e.get('identici') else (e['Y']['campioni_diversi']+e['U']['campioni_diversi']+e['V']['campioni_diversi'] if e.get('confrontabili') else -1))
")
	if [ "$A_DIFFERENT_BYTES_LOSSLESS" = -1 ]; then
		# ⚠ AV1: byte-for-byte identity is not required, and the reason is in
		#   the expectations.  ⛔ But one does NOT stop looking: the loss is required
		#   to be there and to be SMALL, or «CRF 1» would be just a word.
		inf "3d AV1 at CRF 1: differing samples $DIFF_A (identity is not required)"
		completed campioni_diversi_lossless "$DIFF_A"
	else
		require "3d differing samples after the lossless round" "$A_DIFFERENT_BYTES_LOSSLESS" "$DIFF_A"
		completed campioni_diversi_lossless "$DIFF_A"
	fi
fi

# 3e — ⛔ THE 10 BITS, on the DECODED and not on the source
M_REAL=$(python3 "$HERE/02-encoding-image.py" --levels "$WORKDIR/A.yuv")
inf "bit measurement on the decoded: $M_REAL"
V_REAL=$(python3 -c "import json;print(json.loads('''$M_REAL''')['verdict'])")
L_REAL=$(python3 -c "import json;print(json.loads('''$M_REAL''')['distinct_levels'])")
if [ "$V_REAL" = "$A_VERDICT_REAL" ]; then
	ok "3e the 10 bits are REAL: $V_REAL"
else
	# ⛔ THE MARK OF FAULT F2.3-A.  The healthy round does not print this sentence.
	ko "⛔ 10 BITS DECLARED BUT NOT REAL: the stream declares itself $A_PROFILE and the pixels say $V_REAL"
fi
require "3e distinct levels in the ramp" "$A_REAL_LEVELS" "$L_REAL"
completed verdetto_bit_vero "$V_REAL"
completed livelli_vero "$L_REAL"

# ───────────────────────────────────────────────────────────────────────────
log "4. ⛔ THE OPPOSITE CASE — what the contrary would look like (LESSONS.md §1.11)"
inf "the SAME image passed through 8 bits and put back in a 10-bit container."
inf "⭐ If the bench did not tell this round from the previous one, it would not be"
inf "   measuring the 10 bits: it would be measuring that the stream exists."
OPPOSITE=$WORKDIR/O.$CODEC
if ! encode "$WORKDIR/sorgente-8in10.yuv" "$OPPOSITE" 1 "$ROUND_A_OPTIONS:log-level=error"; then
	ko "⛔ encoding of the opposite case failed"
else
	# 4a — ⭐ and the label stays HONEST: it is the content that lies
	require "4a profile of the opposite case" "$A_PROFILE" "$(queries "$OPPOSITE" profile)"
	require "4a pix_fmt of the opposite case" "$A_PIXFMT"  "$(queries "$OPPOSITE" pix_fmt)"
	inf "⭐ here is the point: the label is IDENTICAL to that of the real round, and it is correct."
	inf "   The encoder IS Main10.  It is the CHAIN that gave it 8 bits."
	inf "   Whoever stopped at ffprobe would write «10 bits» in the report (E1)."
	if decode "$OPPOSITE" "$WORKDIR/O.yuv"; then
		M_OPP=$(python3 "$HERE/02-encoding-image.py" --levels "$WORKDIR/O.yuv")
		inf "bit measurement on the opposite case: $M_OPP"
		V_OPP=$(python3 -c "import json;print(json.loads('''$M_OPP''')['verdict'])")
		L_OPP=$(python3 -c "import json;print(json.loads('''$M_OPP''')['distinct_levels'])")
		require "4b verdict on the opposite case"  "$A_VERDICT_8IN10" "$V_OPP"
		require "4b levels on the opposite case"   "$A_LEVELS_8IN10"  "$L_OPP"
		completed verdetto_bit_opposto "$V_OPP"
		completed livelli_opposto "$L_OPP"
	else
		ko "⛔ 4b the opposite case did not decode"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "5. Round B — the RENDERING: how much is lost at CRF $RENDER_CRF"
inf "⚠ CRF $RENDER_CRF is not the working point of the product — that is phase 9."
inf "   Here it only serves to know that the stream holds also when it is not lossless."
RENDERED=$WORKDIR/B.$CODEC
if ! encode "$REAL_SOURCE" "$RENDERED" 1 "crf=$RENDER_CRF:log-level=error"; then
	ko "⛔ 5 encoding at CRF $RENDER_CRF failed"
else
	BYTE_B=$(stat -c%s "$RENDERED")
	inf "stream: $BYTE_B bytes against the $BYTE_A of the lossless"
	require "5 profile also at CRF $RENDER_CRF" "$A_PROFILE" "$(queries "$RENDERED" profile)"
	if verify_shape "$RENDERED" 1 "$WORKDIR/B-forma.json"; then
		ok "5 the shape holds also at CRF $RENDER_CRF"
	else
		ko "⛔ 5 the shape changes with the bitrate"; cat "$WORKDIR/B-forma.json"
	fi
	if decode "$RENDERED" "$WORKDIR/B.yuv"; then
		C_B=$(python3 "$HERE/02-encoding-image.py" --compare "$REAL_SOURCE" "$WORKDIR/B.yuv")
		inf "loss at CRF $RENDER_CRF: $C_B"
		MAXY=$(python3 -c "import json;print(json.loads('''$C_B''')['Y']['differenza_massima'])")
		# ⛔ ZERO loss at CRF 20 would mean that CRF was not applied,
		#    and it would be an E2 (the option silently ignored), not a success.
		if [ "$MAXY" -gt 0 ]; then ok "5 there is loss, as there must be: maximum Y difference = $MAXY"
		else ko "⛔ 5 ZERO loss at CRF $RENDER_CRF: the option was not applied"; fi
		completed perdita_massima_y_crf "$MAXY"
		completed byte_flusso_crf "$BYTE_B"
	else
		ko "⛔ 5 the stream at CRF $RENDER_CRF does not decode"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "6. The parameter sets in front of EVERY keyframe — the half that gets forgotten"
inf "a single frame has them necessarily.  The trouble comes in phase 3, when a"
inf "client connects midway and receives a NAKED IDR: black screen WITH the frames"
inf "arriving.  v1 forbade it by hand (src/encoder.c:268-272)."
TRE=$WORKDIR/G.$CODEC
if ! encode "$REAL_SOURCE" "$TRE" 3 "keyint=1:min-keyint=1:log-level=error"; then
	ko "⛔ 6 encoding with three keyframes failed"
else
	if verify_shape "$TRE" "$A_GROUPS_IDR_3" "$WORKDIR/G-forma.json"; then
		ok "6 the parameter sets in front of all $A_GROUPS_IDR_3 keyframes"
	else
		ko "⛔ 6 the parameter sets do NOT precede every keyframe"; cat "$WORKDIR/G-forma.json"
	fi
	if [ "$CODEC" = av1 ]; then
		G_GROUPS=$(read_shape "$WORKDIR/G-forma.json" sequenze_prima_di_una_chiave)
	else
		G_GROUPS=$(read_shape "$WORKDIR/G-forma.json" gruppi_parametri_prima_di_un_IDR)
	fi
	require "6 groups of parameter sets" "$A_GROUPS_IDR_3" "$G_GROUPS"
	completed gruppi_parametri "$G_GROUPS"
fi

# ───────────────────────────────────────────────────────────────────────────
log "7. ⛔ NEGATIVE CONTROL — a mangled stream MUST be refused"
inf "and «refused» here does NOT mean «exit status other than zero»:"
inf "⛔ two manglings out of three pass with exit 0 and ffmpeg CONCEALS (measured)."
inf "   Refused = zero frames OR pixels different from the source."
REFUSED=0
MODES="senza-parametri byte-girato troncato"
[ "$CODEC" = av1 ] && MODES="senza-sequenza byte-girato troncato"
for MODE in $MODES; do
	mangle_stream "$FLOW" "$MODE" "$WORKDIR/S-$MODE.$CODEC" > "$WORKDIR/S-$MODE.json"
	# ⛔ The exit status is CAPTURED, not thrown into a chain of pipes.
	decode "$WORKDIR/S-$MODE.$CODEC" "$WORKDIR/S-$MODE.yuv"
	OUTPUT=$?
	BYTE=$(stat -c%s "$WORKDIR/S-$MODE.yuv" 2> "$WORKDIR/S-$MODE.stat" || echo 0)
	if [ "$BYTE" = 0 ]; then
		ok "7 «$MODE»: refused — zero frames (exit $OUTPUT)"
		REFUSED=$((REFUSED+1))
	elif cmp -s "$REAL_SOURCE" "$WORKDIR/S-$MODE.yuv"; then
		# ⛔ This is the case that condemns the BENCH, not the stream.
		ko "⛔ 7 «$MODE»: exit $OUTPUT AND PIXELS IDENTICAL TO THE SOURCE."
		ko "   the mangling did not bite: this bench CANNOT SEE A REFUSAL"
	else
		DIFFERENT=$(cmp -l "$REAL_SOURCE" "$WORKDIR/S-$MODE.yuv" | wc -l)
		ok "7 «$MODE»: refused in the PIXELS — $DIFFERENT differing bytes (exit $OUTPUT)"
		REFUSED=$((REFUSED+1))
	fi
done
require "7 manglings refused" "$A_REFUSED_MANGLINGS" "$REFUSED"
completed storpiature_rifiutate "$REFUSED"

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
if [ "$ENCODER" = product ] && [ "$CODEC" = hevc ]; then
	log "8. ⛔ The REAL road: from BGRx, as the capture delivers"
	if ! ffmpeg -hide_banner -loglevel error -nostdin -f rawvideo -pix_fmt yuv420p10le \
		-s 1920x1080 -i "$REAL_SOURCE" -pix_fmt bgr0 -f rawvideo -y "$WORKDIR/scena.bgrx"; then
		ko "⛔ 8 the BGRx source was not built"
	elif ! "$TEST" --codec hevc --format bgrx --source "$WORKDIR/scena.bgrx" \
		--output "$WORKDIR/X.hevc" --lossless --confession "$WORKDIR/X.json" > /dev/null; then
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
			-i "$WORKDIR/scena.bgrx" \
			-vf "scale=in_range=full:out_range=limited:in_color_matrix=bt709:out_color_matrix=bt709:sws_flags=bilinear" \
			-pix_fmt yuv420p10le -f rawvideo -y "$WORKDIR/X-ffmpeg.yuv"
		decode "$WORKDIR/X.hevc" "$WORKDIR/X.yuv"
		python3 "$HERE/02-encoding-image.py" --compare "$WORKDIR/X-ffmpeg.yuv" "$WORKDIR/X.yuv" \
			> "$WORKDIR/X-confronto.json"
		X_DIFF=$(( $(read_shape "$WORKDIR/X-confronto.json" Y.campioni_diversi) \
		         + $(read_shape "$WORKDIR/X-confronto.json" U.campioni_diversi) \
		         + $(read_shape "$WORKDIR/X-confronto.json" V.campioni_diversi) ))
		require "8a our BGRx→YUV conversion against ffmpeg's" "0" "$X_DIFF"
		completed conversione_diversa_da_ffmpeg "$X_DIFF"

		# 8b — ⛔ THE PROMOTION, DECLARED.  The source has 8 real bits; the stream
		#      will say «Main 10» anyway.  `DECISIONS.md` §2.7: a silent
		#      fallback stays forbidden even when the fault is not ours.
		require "8b the product DECLARES the 8→10 promotion" "True" \
			"$(read_shape "$WORKDIR/X.json" promozione_8_a_10)"

		# 8c — ⛔⛔ AND HERE THE BENCH SAYS SOMETHING NOBODY WANTED TO HEAR.
		#      On steps 3-4 the 10-bit gauge tells 877 from 220 and 0.25 from
		#      1.000.  ⛔ After an RGB→YUV conversion **the signature of the multiples of
		#      4 does NOT survive**: the matrix scatters the values, and the meter
		#      says «10-bit-veri» of a chain that carries EIGHT.
		#      ⇒ On this road the meter's verdict is a FALSE GREEN, and
		#        what remains is the LEVEL COUNT: 256 instead of 877.
		#      ⚠ The same thing had already been written for probe S2 of phase 1
		#        (`PHASES.md` §02-primo-fotogramma): real bits are measured AT THE
		#        SOURCE, or not at all.
		python3 "$HERE/02-encoding-image.py" --levels "$WORKDIR/X.yuv" > "$WORKDIR/X-livelli.json"
		inf "bit measurement after the conversion: $(cat "$WORKDIR/X-livelli.json")"
		X_LIV=$(read_shape "$WORKDIR/X-livelli.json" livelli_distinti)
		X_VER=$(read_shape "$WORKDIR/X-livelli.json" verdetto)
		require "8c distinct levels on the BGRx road (8 bits promoted)" "256" "$X_LIV"
		if [ "$X_VER" = "10-bit-veri" ]; then
			inf "⛔ and the VERDICT here says «$X_VER» of an EIGHT-bit chain:"
			inf "   the signature of the multiples of 4 does not survive the RGB→YUV matrix."
			inf "   ⇒ on this road the gauge that counts is the COUNT ($X_LIV against 877),"
			inf "     and the rest is said by the product declaring the promotion (8b)"
		fi
		completed livelli_strada_bgrx "$X_LIV"
		completed verdetto_strada_bgrx "$X_VER"
		X_CONV=$(read_shape "$WORKDIR/X.json" us_conversione)
		completed us_conversione_bgrx "$X_CONV"
		inf "⚠ conversion: $X_CONV µs at 1920x1080.  v1 had measured 12.5 ms at"
		inf "   2560x1024 in NV12 and called it a bottleneck: the number must be"
		inf "   reread every time, not copied"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "The log, and the verdict"
python3 - "$DONE" "$OUTCOMES" "$SCENE" "$OK" "$NO" <<'PYFINE'
import json, sys, datetime, os, socket
fatti, esiti, scena, ok, no = sys.argv[1:6]
d = {}
with open(fatti) as f:
    for r in f:
        if "\t" in r:
            k, _, v = r.rstrip("\n").partition("\t")
            d[k] = v
riga = {
    "bench": "F2.3-codifica",
    "scene": scene,
    "machine": socket.gethostname(),
    "time": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "checks_passed": int(ok), "checks_failed": int(no),
    "outcome": "green" if int(no) == 0 else "red",
    "measurements": d,
}
with open(esiti, "a") as f:
    f.write(json.dumps(riga, ensure_ascii=False) + "\n")
print(json.dumps(riga, ensure_ascii=False, indent=2))
PYFINE
inf "line appended to $OUTCOMES"

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
