#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b65 — WHEN THE PIPE IS NARROW, WHO PAYS: THE AUDIO OR THE VIDEO?

⛔ Where it comes from.  `[M]` by A1, from a real session: **2 200 datagrams discarded
   by the server**, the page lost **684 blocks = 13.7 s of audio (9.43 %)**,
   and in a 25 s window **47 %**.  ⛔⛔ In the SAME session the video
   streams lost nothing: 5 334 delivered, 5 334 painted.
   ⇒ The disproportion is not the network: it is **how we treat datagrams compared
   with streams** inside our transport.

⭐⭐ AND THE FIRST THING THIS BENCH HAD TO LEARN IS THAT THE DEFECT DOES NOT
    REPRODUCE ON A WIDE PIPE.  `[M]` 21 August 2026, loopback, real video
    (1 279 frames 1920x1080 in 40 s) and PCM audio at 1.56 Mbit/s:
    **8 006 sent, 0 thrown away, 0 refused, 0 postponed**.  ⇒ On a bottomless
    pipe the pacer never closes and nobody gives way.  The defect lives **only where
    bandwidth is not enough**, and that is where one has to go and build it.

⛔ THE FOUR DOORS THROUGH WHICH A DATAGRAM MAY FAIL TO GO OUT, in order, and each has
   its own counter (`src/webtransport.c`):

   | # | where | counter | who decides |
   |---|---|---|---|
   | 1 | `dgram_accoda`, queue full (8 slots) | `audio_buttati` | **us**: the oldest leaves to make room for the new one |
   | 2 | `dgram_scrivi_uno`, `dgram_rimando_ts == ts` | — | **us**: one single attempt per pass |
   | 3 | `writev_datagram` returns 0 | `audio_rimandati` | **the pacer / ngtcp2's window** |
   | 4 | 4096 postponements in a row | `audio_rifiutati` | **us**, so as not to keep it forever |

⛔⛔ AND THE ASYMMETRY LIES IN THE FORM, not in a policy written
    anywhere: video travels on **streams** — if it does not get through now, ngtcp2
    keeps it, splits it and retransmits it, so it can only arrive **late**;
    audio travels on **datagrams**, which §6.3 forbids retransmitting and which
    have an eight-slot queue that overwrites itself.  ⇒ Every scarcity of
    transmission opportunities is paid **entirely by the audio**, and nobody ever
    decided it: it is what happens when nothing is decided.

⭐ This bench builds the scarcity with `tc netem rate` (plus a delay,
   or the congestion window has no way to count) and measures, at each
   step: how much audio leaves, how much is thrown away and **through which of the four
   doors**, how many frames arrive all the same, and how what remains SOUNDS.

⛔ THE NETWORK IS TOUCHED WITH THE SAME DISCIPLINE AS `07-b64-rete.py`:
   only `lo`, only port 7801, `enp7s0` (ssh and the user's 7730) never; and a
   detached guardian puts the qdisc back even if this script dies.

⛔⛔⛔ WHAT IT FOUND — 21 August 2026, evening, and the cause is NOT the one
      the mandate suspected.  The scene is always the same: session of
      `provar7` on 7801, 440 Hz tone in the sink, `04-b30-scena` on the captured
      monitor, test client inside the container, `netem` on `lo`
      restricted to port 7801 only.  Thirty seconds per step.

  1 · THE WIDE PIPE LOSES NOTHING.  Without a limit and at 15 Mbit/s:
      **8 006 / 6 002 blocks sent, 0 thrown away, 0 refused**, purity 1.000.
      ⇒ The defect does not exist as long as there is bandwidth to spare.

  2 · ⛔ AT 3 Mbit/s WITH THE DESKTOP MOVING the audio is destroyed:
      **397 blocks sent out of ~6 000, 6 061 refused** (PCM), purity 0.18.

  3 · ⭐⭐ BUT AT 3 Mbit/s WITH THE DESKTOP STILL the audio is PERFECT:
      **6 009 sent, 3 refused, 0 thrown away**, yield 0.9995, purity **1.000**,
      and 1.82 Mbit/s out of 3 available pass on the wire.
      ⇒ **It is not the bandwidth: it is the video.**  Same bandwidth, same audio, two
        opposite outcomes — and only one thing changes.

  4 · ⭐⭐ AND IT IS NOT EVEN WHAT THE AUDIO COSTS.  Same step, same
      moving desktop, but **Opus** instead of PCM — that is **1/32** of the
      bandwidth (48 kbit/s against 1.56 Mbit/s): **624 blocks out of 1 500, 896
      refused, 58 % lost all the same**.  ⇒ Reducing what the audio asks for
      does not save it: the room is not there anyway.

  5 · ⛔⛔⛔ THE CAUSE, AND IT IS A SPIRAL THE CODE HAD ALREADY NAMED.
      In all the narrow runs the video delivers **only KEY frames**
      (144/144, 148/148, 107/107, 138/138, 149/149) against 2 keys out of 1 019 at
      15 Mbit.  The log counts **806 keyframe requests (§5.2)** and **173
      lines «KEYFRAME N still holds ~60 000 bytes in the queue and §5.2 forbids
      abandoning it: we WAIT»**.
        · a 60 KB keyframe on a 3 Mbit pipe occupies the window for
          **160 ms**;
        · `WT_CHIAVE_RICHIESTA_MS` grants one **every 150 ms**;
        · in those 160 ms 32 PCM blocks are born (8 for Opus) and each finds
          `cwnd_left = 0`.
      ⇒ It is not a policy that makes the audio give way to the video: it is that the video,
        when bandwidth is short, **asks for more** (§5.2), and the datagram — which
        does not split, is not retransmitted and cannot wait — is the only one that
        can pay.  ⚠ The comment in `webtransport.c` at line ~728 called it
        «the spiral of §5.2» as a hypothesis: here it is measured.

  6 · ⛔ AND FOUR VARIANTS OF THE TRANSPORT CHANGE NOTHING, tried one by
      one on the build tree only, at the same step (blocks
      sent): **base 397 · without the early return per pass 278 ·
      without `PADDING` 406 · without `MORE` (its own packet) 514 · with the RESERVE
      (the video yields the pass when there are datagrams in the queue) 371**.
      ⇒ ⭐ The why is the part that counts: **the window is not contended, it is
        already full** of video bytes in flight.  Giving up writing more
        video does not free what has already left and has not yet been
        acknowledged.  No cleverness in the write order can manufacture
        room that is not there.

Usage (from the laptop):
    python3 banchi/07-b65-datagram.py sonda            # the steps, one by one
    python3 banchi/07-b65-datagram.py sonda --scena no # ⭐ the control of point 3
    python3 banchi/07-b65-datagram.py rimetti          # ⛔ and it is checked
"""
import argparse, json, os, re, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "7801"))
UTENTE = os.environ.get("UTENTE", "provar7")
UID_B = int(os.environ.get("UID_B", "1018"))
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/07-r-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/07-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/07-r")
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
                                "84687524-93d6-4003-8cd1-1ed07aa63454/scratchpad/r7")

VIETATA = "enp7s0"   # ssh and the user's 7730 go through it
DEV = "lo"

# ⭐ The steps.  The scene costs `[M]` 1.56 Mbit/s of PCM audio + ~0.5 of video:
#    the first step sits above the sum, the last one well below.  ⛔ And there is
#    always a delay: without RTT the congestion window has no way to
#    fill up, and the pacer notices nothing.
GRADINI = [
    ("g0-largo",   [],                                    "no limit: the denominator"),
    ("g1-15mbit",  ["delay", "15ms", "rate", "15mbit"],   "three times the needed bandwidth: nobody must give way"),
    ("g2-3mbit",   ["delay", "15ms", "rate", "3mbit"],    "just above the sum (2.1): the first narrow step"),
    ("g3-2mbit",   ["delay", "15ms", "rate", "2mbit"],    "below the sum: someone MUST give way, and we watch who"),
    ("g4-1mbit",   ["delay", "15ms", "rate", "1mbit"],    "half the sum"),
    ("g5-500kbit", ["delay", "15ms", "rate", "500kbit"],  "a third of the audio alone: the desperate case"),
]


def rem(comando, tetto=300):
    """⛔ No redirection AROUND ssh: the sudo prompt goes to stderr."""
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=300):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando), tetto)


def qdisc():
    return root("/usr/sbin/tc qdisc show dev %s" % DEV)[1].strip()



# ── ⛔ THE GUARDIAN IS ARMED AND DISARMED BY PID, NOT BY PATTERN ─────────
GUARDIANO = LAV + "/.guardiano.pid"


def guardiano_arma(secondi):
    """Born with `setsid`: it leads its own group, and the group is killed whole."""
    guardiano_disarma()
    # ⛔ The `&` and the `echo $!` must run INSIDE root's shell, or the
    #    redirect to `$LAV` (which belongs to root) fails and the pid is not written:
    #    `[M]` the first run printed «pid ?», that is a guardian that could not
    #    have been disarmed by pid — the cure without its other half.
    root('bash -c "setsid sh -c \'sleep %d; /usr/sbin/tc qdisc del dev %s root\' '
         '>/dev/null 2>&1 & echo \\$! > %s"' % (secondi, DEV, GUARDIANO))
    rc, out, _ = root("cat %s 2>/dev/null" % GUARDIANO)
    print("   OK  guardian armed for %d s (pid %s): the network goes back as it was "
          "EVEN if I die" % (secondi, out.strip() or "?"))


def guardiano_disarma():
    """⛔ The GROUP is killed, so `sh` never reaches the `tc` line."""
    rc, out, _ = root("cat %s 2>/dev/null || true" % GUARDIANO)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % GUARDIANO)


def rimetti(dillo=True):
    guardiano_disarma()
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q and "tbf" not in q
    if dillo:
        print("   %s «%s» is now: %s" % ("OK " if ok else "NO ", DEV, q or "(none)"))
        print("   --  %s (ssh + 7730): %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s" % VIETATA)[1].split("\n")[0]))
    return ok


def stringi(regole):
    if not regole:
        root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
        return True, "(no limit)"
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem %s"
        % (DEV, " ".join(regole)),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4" % (DEV, PORTA),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4" % (DEV, PORTA),
    ]
    for c in passi:
        rc, _, err = root(c)
        if rc != 0 and "del dev" not in c:
            rimetti()
            return False, "⛔ tc refused: %s" % err[:200]
    return True, qdisc()


# ── ⛔ FIRST OF ALL A SESSION IS OPENED, or there is nothing to play into ───
#
# `[M]` 21 August 2026, and the bench stopped by itself saying so: the «remotix»
# sink is created by the CHILD, and the child is born when a client comes in.  On a
# freshly restarted server the sink does not exist, `pw-play --target remotix` binds
# to nothing and the tone is silent.  ⇒ A short session is opened on purpose: the stage
# and the sink outlive it (invariant I4), and from then on there is somewhere to play.
# ⚠ It also serves the SCENE, which wants the monitor name from the log.
def innesca_sessione(secondi=8):
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--adatta 1920x1080 --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 180)
    return "SESSIONE" in (out + err)


# ── the tone, which must play for the WHOLE run ───────────────────────────
def tono_fabbrica(hz=440, secondi=70, ampiezza=0.5):
    """⛔ The tone is built HERE if missing, and the amplitude is KNOWN: the expected RMS
       is a calculation (A/sqrt2), not an estimate.  ⚠ And the file must be readable
       by the session's user, who is not root."""
    f = "%s/tono-%d.wav" % (LAV, hz)
    rc, out, _ = root("test -s %s && stat -c %%s %s || echo 0" % (f, f))
    if out.strip().isdigit() and int(out.strip()) > 48000 * secondi * 2:
        return f
    root("mkdir -p %s && chmod 755 %s" % (LAV, LAV))
    copione = (
        "import math,struct,wave;"
        "w=wave.open('%s','wb');w.setnchannels(2);w.setsampwidth(2);"
        "w.setframerate(48000);d=bytearray();"
        "[d.extend(struct.pack('<hh',v,v)) for v in "
        "[int(%f*math.sin(2*math.pi*%d*n/48000)*32767) for n in range(48000*%d)]];"
        "w.writeframes(bytes(d));w.close()" % (f, ampiezza, hz, secondi))
    root("python3 -c \"%s\" && chmod 644 %s" % (copione, f), 300)
    return f


def tono_accendi():
    tono_fabbrica()
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus "
         "sh -c 'while :; do pw-play --target remotix %s/tono-440.wav; done' "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, UID_B, LAV))
    for _ in range(30):
        time.sleep(0.4)
        if legami() > 0:
            return True
    return False


def legami():
    rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 %s/banchi/"
                      "07-b64-scena.py grafo" % (UTENTE, UID_B, LAV, ALB))
    try:
        return json.loads(out).get("legami_in_ingresso", 0)
    except Exception:
        return -1


def tono_spegni():
    root("pkill -u %d -f 'while :; do pw-play'; pkill -u %d -x pw-play; true"
         % (UID_B, UID_B))


# ── the scene that makes the encoder work ─────────────────────────────────
def scena_accendi():
    rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -1" % LAV)
    m = re.findall("monitor «([^»]*)»", out)
    usc = m[-1] if m and m[-1] else None
    if not usc:
        return None
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
         "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena --uscita %s "
         "--movimento barra --shm /07-b65 --giro b65 >/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, usc))
    time.sleep(1.5)
    rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % UID_B)
    return usc if out.strip() else None


def scena_spegni():
    root("pkill -u %d -f 04-b30-scena; true" % UID_B)


# ── ⭐ THE REAL BYTES ON THE WIRE, which are the other half of the question ──
#
# ⛔ The payload of a PCM block is 972 bytes, but the packet that carries it
#    can be much bigger: `dgram_scrivi_uno` asks for
#    `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING`, and the padding fills the packet
#    up to full size.  ⇒ If the datagram does NOT manage to share the
#    packet with the video, every audio block costs 1452 bytes instead of 972:
#    49 % more bandwidth than what the sound contains.
#
# ⚠ It is not deduced: the outgoing bytes are counted, and the counter is already
#   kept by the `netem` qdisc this bench installs.
def byte_sul_filo():
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev %s" % DEV)
    import re as _re
    blocchi = out.split("qdisc netem 40:")
    if len(blocchi) < 2:
        return None
    m = _re.search(r"Sent (\d+) bytes (\d+) pkt", blocchi[1])
    return (int(m.group(1)), int(m.group(2))) if m else None


# ── one run: the client inside the container, audio + video ────────────────
def giro(nome, codec, secondi):
    root("rm -f %s/%s.jsonl %s/%s.265; true" % (LAV, nome, LAV, nome))
    # ⛔ The number of log lines is taken BEFORE, so that the «final
    #    count» read afterwards belongs to THIS session and not to the one before.
    rc, out, _ = root("wc -l < %s/registro.log" % LAV)
    try:
        riga0 = int(out.strip())
    except Exception:
        riga0 = 0
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec %s "
              "--audio-scrivi %s/%s.jsonl --adatta 1920x1080 "
              "--video-scrivi %s/%s.265 --resta %d"
              # ⛔ `opus` ALONE IS NOT ENOUGH, and the server is right to
              #   refuse it: RCP §4.3 makes PCM the mandatory base at both
              #   ends, and a CIAO that declares only Opus gets
              #   CONGEDO(NIENTE_IN_COMUNE 0x09).  The bench had taken it for
              #   a fault for two runs.
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV,
                 "opus,pcm" if codec == "opus" else codec,
                 DENTRO_LAV, nome, DENTRO_LAV, nome, secondi))
    prima_filo = byte_sul_filo()
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 240)
    dopo_filo = byte_sul_filo()
    testo = out + err
    r = {"cliente": {}}
    for x in testo.splitlines():
        if "[audio] received" in x:
            r["cliente"]["audio"] = x.strip()
        if "[audio] discarded" in x:
            r["cliente"]["scartati"] = x.strip()
        if "[vid]" in x:
            r["cliente"]["video"] = x.strip()
    # ⛔ The SERVER's count, and only the lines born in this run.
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -aE 'final count|cwnd_left' "
                      "| tail -4" % (riga0 + 1, LAV))
    r["server"] = [x.strip() for x in out.splitlines()]
    if prima_filo and dopo_filo:
        b = dopo_filo[0] - prima_filo[0]
        pk = dopo_filo[1] - prima_filo[1]
        r["filo"] = {"byte": b, "pacchetti": pk,
                     "byte_per_pacchetto": round(b / pk, 1) if pk else None,
                     "mbit_s": round(b * 8 / secondi / 1e6, 3)}
    return r


def giudica(nome, codec):
    """⛔ With Opus we do not listen: the judge does not decode it, and saying so is
       better than pretending (`CODER.md` §3.10)."""
    j = os.path.join(FUORI, nome + ".jsonl")
    subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                   "cat %s/%s.jsonl\" > %s" % (MACCHINA, PAROLA_SUDO, LAV, nome, j),
                   shell=True)
    if codec != "pcm":
        return {"esito": "NON GIUDICATO — Opus: the judge does not decode it, "
                         "here the transport is counted"}
    if not os.path.exists(j) or os.path.getsize(j) == 0:
        return {"esito": "NIENTE DA GIUDICARE — no blocks"}
    p = subprocess.run(["python3", os.path.join(QUI, "07-b64-orecchio.py"), j,
                        "--hz", "440"], capture_output=True)
    try:
        d = json.loads(p.stdout.decode())["nostro"]
    except Exception as e:
        return {"esito": "the judge did not answer: %s" % e}
    return {"blocchi": d["blocchi"], "resa_campioni": d.get("resa_campioni"),
            "scoppiettii_al_s": d["scoppiettii"]["al_secondo"], "tono": d["tono"]}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["sonda", "rimetti", "stato"])
    p.add_argument("--secondi", type=int, default=30)
    p.add_argument("--codec", default="pcm", choices=["pcm", "opus"])
    p.add_argument("--solo", default="")
    p.add_argument("--scena", default="si", choices=["si", "no"],
                   help="the moving desktop (and so the video that weighs)")
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    if a.passo in ("rimetti", "stato"):
        return 0 if rimetti() else 2

    print("== 07-b65 · who pays when the pipe is narrow — port %d, dev «%s»"
          % (PORTA, DEV))
    print("   ⛔ «%s» (ssh + the user's 7730) is NOT touched" % VIETATA)
    print("   --  «%s» before: %s" % (DEV, qdisc() or "(none)"))
    totale = (a.secondi + 150) * len(GRADINI) + 300
    guardiano_arma(totale)
    print("   OK  guardian armed for %d s" % totale)

    esiti = []
    try:
        print("   --  opening a short session to bring the stage and the sink to life")
        if not innesca_sessione():
            print("   NO  the session does not open: I do not measure"); return 2
        if not tono_accendi():
            print("   NO  the tone does not play: I do not measure"); return 2
        usc = scena_accendi() if a.scena == "si" else None
        # ⭐ `--scena no` is the CONTROL that separates the two suspects: with the
        #    desktop still the video asks for very little, and if in that
        #    condition the audio gets through, then it is not «the audio always gives way» —
        #    it is «the video eats the window».
        print("   %s scene on monitor %s" % ("OK " if usc else "-- ", usc))
        for nome, regole, atteso in GRADINI:
            if a.solo and a.solo not in nome:
                continue
            print("\n-- %s · %s" % (nome, atteso))
            ok, q = stringi(regole)
            if not ok:
                print("   ", q); break
            print("    tc: %s" % " ".join(q.split("\n")[:2])[:150])
            leg = legami()
            print("    M3: incoming links to the sink = %s" % leg)
            if leg <= 0:
                print("   NO  the tone is silent: I do NOT judge this step")
                esiti.append({"gradino": nome, "esito": "the tone was silent"})
                continue
            r = giro(nome, a.codec, a.secondi)
            for k in ("audio", "scartati", "video"):
                if k in r["cliente"]:
                    print("    %s" % r["cliente"][k])
            if "filo" in r:
                print("    FILO %s" % json.dumps(r["filo"], ensure_ascii=False))
            for x in r["server"]:
                print("    SERVER %s" % x[:190])
            g = giudica(nome, a.codec)
            print("    ear: %s" % json.dumps(g, ensure_ascii=False))
            esiti.append({"gradino": nome, "regole": regole, "atteso": atteso,
                          "cliente": r["cliente"], "server": r["server"],
                          "orecchio": g})
    finally:
        scena_spegni()
        tono_spegni()
        print("\n== ⛔ THE NETWORK IS PUT BACK AS IT WAS")
        rimetti()
    json.dump(esiti, open(os.path.join(FUORI, "b65-esiti.json"), "w"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
