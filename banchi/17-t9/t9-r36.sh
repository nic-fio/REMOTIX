#!/bin/bash
#
# ⛔ HISTORY: the installer's GUI was removed on 10 Oct 2026 (DECISIONI §10.31). This bench
# tested R36/R37 on 30 Sep and no longer runs (remotix-install-gui is missing); it stays as a record of the test.
#
# t9-r36.sh — phase 17, T9, R36: the same installation driven by CLI, TUI and GUI on three copies of the
# same machine (the "client" snapshot, prepared the same way by t9-gui.sh turn_on) gives the same
# plan, the same resolved set, the same log (apart from the times) and the same certificate.
#
#   (on the server)   sg kvm -c 'bash t9-r36.sh <machine> <step>'
#
#   collect <which>   (which = cli · tui · gui) the objects of the VM's CONFIRMED operation in
#                      /media/REMOTIX/vm17/t9-gui/r36/<machine>/<which>/
#   cli                on the running VM (t9-gui.sh turn_on): remotix-install install, with the
#                      "si" confirmation at the terminal (a real terminal, pty)
#   tui [language]     on the running VM: remotix-install tui, driven with keys (Enter at each screen);
#                      <output>.steps = where, in the terminal stream, each screen was (for the text
#                      photos: a terminal emulator replays the stream up to there)
#   tui-language <LANG>  only the first screen with that LANG, then "q" (R42)
#   compare          the three, normalised (identifiers, times, approval, engine digest)
#
# ⚠ The three copies use the SAME binary: the build with the window (motore/remotix-install-gui),
# which also has CLI and TUI (DECISIONI §10.19). The static build has another digest, and the plan
# carries it written (motore.digest): with two different binaries the comparison removes it and says so.
set -uo pipefail
m=${1:?machine}; step=${2:?step}
R=/media/REMOTIX/vm17
D=$R/t9-gui/r36/$m
V="bash $R/17-vm.sh"
ARCH=http://10.0.2.2:8727
mkdir -p "$D"
vm() { $V ssh "$m" "$@"; }

take_engine() {
	vm "curl -s -o /tmp/remotix-install-gui $ARCH/motore/remotix-install-gui && curl -s -o /tmp/remotix-install-gui.sha256 $ARCH/motore/remotix-install-gui.sha256 && (cd /tmp && sha256sum -c remotix-install-gui.sha256) && mv /tmp/remotix-install-gui /tmp/remotix-install && chmod 755 /tmp/remotix-install"
}

# pty: a real terminal for the command in the VM (ssh -tt), and the keys sent when the screen
# shows the expected text
drive() { # drive <output-file> <remote command> <wait1> <keys1> [<wait2> <keys2> …]
	python3 - "$@" <<'PY'
import os, pty, sys, time, re, select
out_dir, command, steps = sys.argv[1], sys.argv[2], sys.argv[3:]
key_id = "/media/REMOTIX/vm17/ssh/id_ed25519"
port = os.environ["SSH_PORT"]
pid, fd = pty.fork()
if pid == 0:
    os.execvp("ssh", ["ssh", "-tt", "-i", key_id, "-p", port, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                      "-o", "LogLevel=ERROR", "nicfio@127.0.0.1", command])
import fcntl, termios, struct
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 45, 120, 0, 0))  # 120×45, like the text photos
buf = b""
out = open(out_dir, "wb")
def read_it(t):
    global buf
    fine = time.time() + t
    while time.time() < fine:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try: d = os.read(fd, 65536)
            except OSError: return False
            if not d: return False
            buf += d; out.write(d); out.flush()
    return True
def clean():
    return re.sub(rb"\x1b\[[0-9;?]*[a-zA-Z]", b"", buf).decode("utf-8", "replace")
for i in range(0, len(steps), 2):
    expected_val, keys = steps[i], steps[i + 1].encode().decode("unicode_escape").encode()
    fine = time.time() + 900
    while expected_val not in clean() and time.time() < fine:
        if not read_it(1): break
    print("  saw \"%s\", sending %r (byte %d of the stream)" % (expected_val, keys, out.tell()), flush=True)
    open(out_dir + ".steps", "a").write("%d %s\n" % (out.tell(), expected_val))
    buf = b""
    time.sleep(1)
    os.write(fd, keys)
read_it(20)
out.close()
PY
}

case $m in
debian13-*) n=1 ;; ubuntu2604-*) n=2 ;; fedora44-*) n=3 ;; arch-*) n=4 ;; *) echo "machine?"; exit 2 ;;
esac
k=0; case ${m#*-} in gnome) k=1 ;; kde) k=2 ;; xfce) k=3 ;; lxqt) k=4 ;; esac
export SSH_PORT=$((2300 + 10 * n + k))

case $step in
collect)
	q=${3:?cli · tui · gui}
	rm -rf "${D:?}/$q"; mkdir -p "$D/$q"
	vm "sudo sh -c 'cd /var/lib/remotix/operations && d=\$(ls -1 | tail -1) && tar -C \$d -cf - piano.json approvazione.json insieme-risolto.json insieme-risolto-pacchetti.json registro.jsonl certificato.json verifica.json state'" | tar -C "$D/$q" -xf -
	ls "$D/$q"; cat "$D/$q/state"
	;;
cli)
	take_engine
	drive "$D/cli.txt" "sudo /tmp/remotix-install installa --archivio $ARCH --lingua it" "per confermare" 'si\r'
	tail -5 "$D/cli.txt"
	;;
tui)
	take_engine
	rm -f "$D/tui.txt.steps"
	# Check → Enter; Choices (the default port) → Enter; Plan → Enter; at the end Enter closes
	drive "$D/tui.txt" "sudo /tmp/remotix-install tui --archivio $ARCH --lingua it" \
		"Ho controllato" '\r' "da decidere" '\r' "Ecco che cosa" '\r' "REMOTIX è pronto" '\r'
	tail -3 "$D/tui.txt"
	;;
tui-language)
	take_engine
	L=${3:?LANG}
	rm -f "$D/tui-$L.txt.steps"
	# sudo cleans the environment: the language is passed by env, as someone setting it in the session would
	drive "$D/tui-$L.txt" "sudo env LANG=$L LANGUAGE=${4:-} /tmp/remotix-install tui --archive $ARCH" "7447" 'q'
	;;
compare)
	python3 - "$D" <<'PY'
import json, sys, os, re
D = sys.argv[1]
VIA = {"id", "created", "now", "approvazione", "operazione", "digest_piano", "n", "folder"}
def norm(x):
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items() if k not in VIA}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, str):
        x = re.sub(r"\d{8}T\d{6}Z-[0-9a-f]{8}", "<ID>", x)          # plan and operation identifiers
        x = re.sub(r"\d{4}-\d\d-\d\dT[\d:.]+Z", "<NOW>", x)
        x = re.sub(r"/tmp/remotix-install[.\w]*", "<ENGINE>", x)
        x = re.sub(r"(apt|dpkg|dnf)[^ ]*\.(log|tmp)\S*", "<TMP>", x)
        return x
    return x
def read_it(q, f):
    p = os.path.join(D, q, f)
    if f.endswith(".jsonl"):
        return [norm(json.loads(r)) for r in open(p) if r.strip()]
    return norm(json.load(open(p)))
outcome = 0
for f in ["piano.json", "insieme-risolto.json", "insieme-risolto-pacchetti.json", "registro.jsonl", "certificato.json"]:
    vv = {q: read_it(q, f) for q in ("cli", "tui", "gui")}
    equal = vv["cli"] == vv["tui"] == vv["gui"]
    print("%-32s %s" % (f, "SAME in all three" if equal else "DIFFERENT"))
    if not equal:
        outcome = 1
        for q in ("tui", "gui"):
            a, b = json.dumps(vv["cli"], indent=1, sort_keys=True).splitlines(), json.dumps(vv[q], indent=1, sort_keys=True).splitlines()
            import difflib
            d = [l for l in difflib.unified_diff(a, b, "cli", q, n=0, lineterm="") if not l.startswith("@@")]
            print("   cli ↔ %s: %d lines differ" % (q, len(d)))
            for l in d[:12]: print("     " + l[:160])
for q in ("cli", "tui", "gui"):
    a = json.load(open(os.path.join(D, q, "approvazione.json")))
    print("approval %-4s %s, by %s" % (q, a["manner"], a["da"]))
sys.exit(outcome)
PY
	;;
*) sed -n 3,19p "$0"; exit 2 ;;
esac
