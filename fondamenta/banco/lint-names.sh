#!/bin/bash
#
# lint-names.sh — cerca i NOMI TRADOTTI A META' negli script di shell.
#
#   bash fondamenta/banco/lint-names.sh [file-o-cartella ...]
#
# Il controllo shellcheck (SC2154) non guarda le variabili TUTTE MAIUSCOLE, perche' le
# prende per variabili d'ambiente: ed e' li' che si nasconde il difetto
# «assegno COST_C1_ROUND, leggo COSTO_C1_GIRO».  Questo controllo le guarda.
#
# Per ogni *.sh sotto benches/, fondamenta/, installer/tests/, packaging/
# (non installer/vendor/) stampa `file:riga: NOME` per ogni variabile MAIUSCOLA
# letta ($NOME, ${NOME...}) e mai assegnata nello stesso file ne' nei file che
# include con `source`/`.` (se il percorso e' risolvibile).  Assegnare vale:
# NOME=, local, declare, export, readonly, read, for NOME in, mapfile/readarray,
# printf -v, getopts.  Escluse le variabili d'ambiente note e REMOTIX_*.
# Uscita 0 se non c'e' nulla da dire, 1 altrimenti.
exec python3 -I - "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" "$@" <<'PY'
import os, re, sys

root, args = sys.argv[1], sys.argv[2:]
if args:
    targets = [os.path.abspath(a) for a in args]
else:
    targets = [os.path.join(root, d) for d in ("benches", "fondamenta", "installer/tests", "packaging")]

files = []
for t in targets:
    if os.path.isfile(t):
        files.append(t)
        continue
    for d, dirs, fs in os.walk(t):
        dirs[:] = [x for x in dirs if x not in (".git", "vendor")]
        files += [os.path.join(d, f) for f in fs if f.endswith(".sh")]
files = sorted(f for f in files if os.path.basename(f) != "lint-names.sh")

KNOWN = set("HOME PATH USER UID EUID PWD OLDPWD SHELL TERM LANG DISPLAY WAYLAND_DISPLAY RANDOM SECONDS LINENO "
            "HOSTNAME OSTYPE PPID IFS OPTARG OPTIND TMPDIR PIPESTATUS REPLY FUNCNAME".split())
KNOWN_PREFIX = ("LC_", "XDG_", "DBUS_", "SUDO_", "BASH_", "REMOTIX_")
NAME = r"[A-Z][A-Z0-9_]*"
ASSIGN = [
    re.compile(r"(?<![\w$])(%s)(?:\[[^\]]*\])?\+?=" % NAME),
    re.compile(r"\b(?:local|declare|typeset|export|readonly)\b([^;&|\n]*)"),
    re.compile(r"\bread\b([^;&|\n]*)"),
    re.compile(r"\bfor\s+(%s)\s+in\b" % NAME),
    re.compile(r"\b(?:mapfile|readarray)\b([^;&|\n]*)"),
    re.compile(r"\bprintf\s+-v\s+(%s)" % NAME),
    re.compile(r"\bgetopts\s+\S+\s+(%s)" % NAME),
    re.compile(r"\bunset\b([^;&|\n]*)"),
]
USE = re.compile(r"\$(%s)(?![A-Za-z0-9_])|\$\{!?(%s)(?![A-Za-z0-9_])" % (NAME, NAME))
ARITH = re.compile(r"\$?\(\((.*?)\)\)")
BARE = re.compile(r"(?<![\w$#{])(%s)(?![\w(])(?!\s*\+?=[^=])" % NAME)
SRC = re.compile(r"(?:^|[;&|(]\s*|\s)(?:source|\.)\s+(\S+)")
WORDS = re.compile(r"(?<![\w$])(%s)\b" % NAME)

def known(n):
    return n in KNOWN or n.startswith(KNOWN_PREFIX)

def strip(line):
    # toglie il commento (intero o a fine riga, fuori dalle virgolette) e le stringhe
    # tra apici singoli: li' dentro $NOME e' testo per un altro shell, awk o python
    if line.lstrip().startswith("#"):
        return ""
    out, q, i = [], None, 0
    while i < len(line):
        c = line[i]
        if q is None:
            if c == "\\" and i + 1 < len(line):
                out.append(line[i:i+2]); i += 2; continue
            if c in "'\"":
                q = c
                if c == "\"":
                    out.append(c)
            elif c == "#" and (i == 0 or line[i-1] in " \t;"):
                break
            else:
                out.append(c)
        else:
            if c == "\\" and q == "\"" and i + 1 < len(line):
                out.append(line[i:i+2]); i += 2; continue
            if c == q:
                q = None
                if c == "\"":
                    out.append(c)
            elif q == "\"":
                out.append(c)
        i += 1
    return "".join(out)

def assigned(text, out):
    for line in text.splitlines():
        line = strip(line)
        if not line:
            continue
        for rx in ASSIGN:
            for m in rx.finditer(line):
                if m.lastindex and rx.pattern.startswith(r"(?<![\w$])"):
                    out.add(m.group(1))
                elif rx.pattern.startswith(r"\bfor") or "printf" in rx.pattern or "getopts" in rx.pattern:
                    out.add(m.group(1))
                else:
                    # fuori dai valori: via $((..)), $(..), ${..}, $x e le stringhe
                    v = re.sub(r"\$\(\(.*?\)\)|\$\(.*?\)|\$\{[^}]*\}|\$\w+|\"[^\"]*\"|'[^']*'", "", m.group(1))
                    v = re.sub(r"=\S*", "=", v)
                    for w in WORDS.findall(v):
                        out.add(w)

def includes(path, text, seen):
    d = os.path.dirname(path)
    found = []
    for line in text.splitlines():
        line = strip(line)
        for m in SRC.finditer(line):
            p = m.group(1).strip("\"'")
            p = p.replace("$HERE", d).replace("${HERE}", d).replace("$BASE", d).replace("${BASH_SOURCE[0]%/*}", d)
            p = re.sub(r'\$\(dirname[^)]*\)', d, p)
            q = p if os.path.isabs(p) else os.path.join(d, p)
            if "$" in p:
                # percorso non risolvibile: se un file con lo stesso nome sta accanto, e' quello
                q = os.path.join(d, os.path.basename(p))
                if "$" in q:
                    continue
            if os.path.isfile(q) and q not in seen:
                found.append(q)
    return found

def all_assigned(path, seen=None):
    seen = seen if seen is not None else set()
    seen.add(path)
    with open(path, errors="replace") as f:
        text = f.read()
    out = set()
    assigned(text, out)
    for q in includes(path, text, seen):
        out |= all_assigned(q, seen)
    return out

count = 0
for path in files:
    try:
        ass = all_assigned(path)
        with open(path, errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        continue
    rel = os.path.relpath(path, root)
    for i, line in enumerate(lines, 1):
        if strip(line) == "":
            continue
        for m in USE.finditer(strip(line)):
            n = m.group(1) or m.group(2)
            if known(n) or n in ass:
                continue
            print("%s:%d: %s" % (rel, i, n))
            count += 1
        # dentro $(( )) e (( )) i nomi si leggono senza `$`
        for a in ARITH.finditer(strip(line)):
            for b in BARE.finditer(a.group(1)):
                n = b.group(1)
                if known(n) or n in ass:
                    continue
                print("%s:%d: %s" % (rel, i, n))
                count += 1
sys.exit(1 if count else 0)
PY
