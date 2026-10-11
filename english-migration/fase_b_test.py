"""fase_b_test.py — fase_b.py on synthetic trees and tables:  python3 english-migration/fase_b_test.py"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fase_b  # noqa: E402

TOOL = os.path.join(HERE, "fase_b.py")

FILES = {
    "src/main.c": (
        '#include <stdio.h>\n'
        'static const char *opt = "--nome";\n'
        'if (!strcmp(a, "--nome-file")) x = 1;\n'
        'const char *p = getenv("REMOTIX_PORTA");\n'
        'printf("esito=%s nodo=%d\\n", e, n);\n'
        'n = nome->campo; m = nome-1;\n'
    ),
    "packaging/rx.sh": (
        '#!/bin/sh\n'
        'case "$1" in\n'
        'avvia) echo go ;;\n'
        'avvia-tutto) echo all ;;\n'
        'esac\n'
        'echo "${REMOTIX_PORTA:-8080}" /var/lib/remotix/certificati/pagina.pem\n'
        'ls /var/lib/remotix/pagina\n'
    ),
    "src/pagina.html": (
        '<div id="barra" class="barra barra-alta"></div>\n'
        '<script>let u = "?nome=1&nomi=2"; o["esito"] = 1;</script>\n'
    ),
    "docs/guida.md": (
        'Run `remotix --nome X`; the file is `pagina.pem` in certificati.\n'
        'The word nome here is Italian prose kept on purpose.\n'
    ),
    "fasi/FASE-01.md": 'history: --nome and REMOTIX_PORTA stay\n',
    "dati/vecchio.jsonl": '{"esito": 1}\n',
}

TABLE_A = (
    "old\tnew\tkind\tplaces\twhy\n"
    "--nome\t--name\toption\tsrc/main.c:2,docs/guida.md:1,fasi/FASE-01.md:1\tthe option\n"
    "--nome-file\t--name-file\toption\tsrc/main.c:3\tits twin\n"
    "REMOTIX_PORTA\tREMOTIX_PORT\tenv-var\tsrc/main.c:4,packaging/rx.sh:6\tport\n"
    "esito\toutcome\tlog-key\tsrc/main.c:5,src/pagina.html:2\tlog and json key\n"
    "avvia\tstart\tcase-label\tpackaging/rx.sh:3\taction\n"
    "certificati\tcertificates\tpath\tpackaging/rx.sh:6,docs/guida.md:1\tdirectory\n"
    "pagina.pem\tpage.pem\tpath\tpackaging/rx.sh:6,docs/guida.md:1\tcertificate\n"
    "barra\tbar\tcss-class\tsrc/pagina.html:1\tid and class\n"
    "nome\tname\turl-param\tsrc/pagina.html:2\tthe page parameter\n"
    "nome\t-\tkeep\tdocs/guida.md:2\tItalian prose\n"
    "#! src/main.c:5 pads esito to 8 columns\n"
)


def git(root, *a):
    return subprocess.run(["git", "-C", root] + list(a), check=True, capture_output=True, text=True).stdout


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="fase-b-test-")
        self.root = os.path.join(self.d, "tree")
        self.tables = os.path.join(self.d, "tables")
        os.makedirs(self.tables)
        for f, t in FILES.items():
            p = os.path.join(self.root, f)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write(t)
        subprocess.run(["git", "init", "-q", self.root], check=True)
        git(self.root, "add", "-A")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
        self.merged = os.path.join(self.d, "merged.tsv")

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_tool(self, *a):
        r = subprocess.run([sys.executable, TOOL] + list(a), capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def table(self, name, text):
        open(os.path.join(self.tables, name), "w").write(text)

    def merge(self):
        return self.run_tool("merge", "--tables", self.tables, "--root", self.root, "--out", self.merged)

    def read(self, f):
        return open(os.path.join(self.root, f)).read()


class Boundaries(unittest.TestCase):
    def m(self, old, kind, s):
        return bool(fase_b.token_rx(old, kind).search(s))

    def test_option(self):
        self.assertTrue(self.m("--nome", "option", 'x "--nome" y'))
        self.assertTrue(self.m("--nome", "option", "--nome=3"))
        self.assertFalse(self.m("--nome", "option", "--nome-file"))
        self.assertFalse(self.m("--nome", "option", "---nome"))

    def test_identifier(self):
        self.assertTrue(self.m("nome", "c-identifier", "nome->campo"))
        self.assertTrue(self.m("nome", "c-identifier", "nome-1"))
        self.assertTrue(self.m("nome", "py-attr", "args.nome"))
        self.assertFalse(self.m("nome", "c-identifier", "--nome"))
        self.assertFalse(self.m("nome", "c-identifier", "nome-file"))
        self.assertFalse(self.m("nome", "c-identifier", "x-nome"))
        self.assertFalse(self.m("nome", "c-identifier", "nomex"))

    def test_env(self):
        self.assertTrue(self.m("REMOTIX_PORTA", "env-var", "${REMOTIX_PORTA:-80}"))
        self.assertFalse(self.m("REMOTIX_PORTA", "env-var", "REMOTIX_PORTA_WEB"))

    def test_path(self):
        self.assertTrue(self.m("pagina", "path", "/var/lib/pagina/x"))
        self.assertTrue(self.m("pagina", "path", "is in pagina."))
        self.assertTrue(self.m("pagina", "path", "pagina.pem"))         # the stem; pagina.pem's own row wins
        self.assertFalse(self.m("pem", "path", "pagina.pem"))
        self.assertFalse(self.m("pagina", "path", "pagina-ban.html"))

    def test_css_and_case(self):
        self.assertTrue(self.m("barra", "css-class", 'class="x barra y"'))
        self.assertFalse(self.m("barra", "css-class", "barra-alta"))
        self.assertTrue(self.m("avvia", "case-label", "avvia) x"))
        self.assertFalse(self.m("avvia", "case-label", "avvia-tutto) x"))

    def test_shell_and_escapes(self):
        self.assertTrue(self.m("PREFISSO", "make-var+env", "R=$PREFISSO-regime.raw"))
        self.assertFalse(self.m("PREFISSO", "make-var+env", "R=PREFISSO-regime"))
        self.assertTrue(self.m("REMOTIX_OPZIONI", "conf-key", r"printf 'A=1\nREMOTIX_OPZIONI=x'"))
        self.assertTrue(self.m("nome", "option", "$nome-x"))

    def test_log_key(self):
        self.assertTrue(self.m("esito", "log-key", "esito=%s"))
        self.assertTrue(self.m("esito", "json-key", '{"esito":'))

    def test_places(self):
        pl, bad = fase_b.parse_places("a.c:3,5; b.py:7-9 c.md:*, d.sh:4[via import], e.go:2 (struct)")
        self.assertEqual(bad, [])
        self.assertEqual(pl, [("a.c", 3), ("a.c", 5), ("b.py", 7), ("b.py", 8), ("b.py", 9), ("c.md", None),
                              ("d.sh", 4), ("e.go", 2)])
        self.assertEqual(fase_b.parse_places("12, x")[1], ["12", "x"])

    def test_words_and_style(self):
        self.assertEqual(fase_b.words("--prova-esce"), ("prova", "esce"))
        self.assertEqual(fase_b.words("ProvaEsce"), ("prova", "esce"))
        self.assertEqual(fase_b.words("REMOTIX_PROVA_ESCE"), ("remotix", "prova", "esce"))
        self.assertEqual(fase_b.style("--a-b"), "--kebab-lower")
        self.assertNotEqual(fase_b.style("a_b"), fase_b.style("a-b"))

    def test_replace_line_simultaneous(self):
        R = fase_b.Row
        rows = [R("a", "b", "c-identifier", [], "", "", ""), R("b", "a", "c-identifier", [], "", "", "")]
        self.assertEqual(fase_b.replace_line("a + b", rows)[0], "b + a")
        rows = [R("nome", "name", "c-identifier", [], "", "", ""), R("--nome-file", "--name-file", "option", [], "", "", "")]
        self.assertEqual(fase_b.replace_line("nome --nome-file", rows)[0], "name --name-file")


class Merge(Base):
    def test_good(self):
        self.table("A.tsv", TABLE_A)
        rc, out = self.merge()
        self.assertEqual(rc, 0, out)
        t = open(self.merged).read()
        self.assertNotIn("fasi/", t.split("#!")[0])              # history place dropped
        self.assertIn("history/generated files dropped", out)
        self.assertIn("#! [A] src/main.c:5 pads", t)
        first = t
        self.merge()
        self.assertEqual(first, open(self.merged).read())       # deterministic

    def test_duplicate_rows_join(self):
        self.table("A.tsv", "esito\toutcome\tlog-key\tsrc/main.c:5\tlog\n")
        self.table("B.tsv", "esito\toutcome\tlog-key\tsrc/pagina.html:2\tjson\n")
        rc, out = self.merge()
        self.assertEqual(rc, 0, out)
        row = [l for l in open(self.merged) if l.startswith("esito\t")]
        self.assertEqual(len(row), 1)
        self.assertIn("src/main.c:5,src/pagina.html:2", row[0])
        self.assertTrue(row[0].rstrip().endswith("A+B"))

    def test_two_news(self):
        self.table("A.tsv", "esito\toutcome\tlog-key\tsrc/main.c:5\t\n")
        self.table("B.tsv", "esito\tresult\tlog-key\tsrc/pagina.html:2\t\n")
        rc, out = self.merge()
        self.assertEqual(rc, 1)
        self.assertIn("esito (log-key) has two news", out)

    def test_two_news_same_line(self):
        self.table("A.tsv", "esito\toutcome\tlog-key\tsrc/main.c:5\t\nesito\tresult\tjson-key\tsrc/main.c:5\t\n")
        rc, out = self.merge()
        self.assertIn("which one?", out)

    def test_two_olds_one_new(self):
        self.table("A.tsv", "esito\tresult\tlog-key\tsrc/main.c:5\t\nnodo\tresult\tlog-key\tsrc/main.c:5\t\n")
        rc, out = self.merge()
        self.assertEqual(rc, 1)
        self.assertIn("both become result in src/main.c", out)

    def test_twins(self):
        self.table("A.tsv", "--nome\t--name\toption\tsrc/main.c:2\t\nnome\tlabel\turl-param\tsrc/pagina.html:2\t\n")
        rc, out = self.merge()
        self.assertEqual(rc, 1)
        self.assertIn("casing twins disagree", out)
        self.table("A.tsv", "--nome\t--name\toption\tsrc/main.c:2\t\nnome\tlabel\turl-param\tsrc/pagina.html:2\tnot a twin: the page's label\n")
        rc, out = self.merge()
        self.assertEqual(rc, 0, out)

    def test_stale_and_malformed(self):
        self.table("A.tsv", "esito\toutcome\tlog-key\tdocs/guida.md:1\t\nnodo\tnode\tlog-key\tsrc/main.c\t\n")
        rc, out = self.merge()
        self.assertEqual(rc, 1)
        self.assertIn("stale: esito: docs/guida.md:1", out)
        self.assertIn("malformed places src/main.c", out)

    def test_new_already_there(self):
        self.table("A.tsv", "nodo\tesito\tlog-key\tsrc/main.c:5\t\n")
        rc, out = self.merge()
        self.assertIn("esito already occurs in src/main.c:5", out)

    def test_file_name_hazards(self):
        self.table("A.tsv", "pagina\tpage\tc-identifier\tpackaging/rx.sh:7\t\n")
        rc, out = self.merge()
        self.assertIn("pagina (c-identifier) at packaging/rx.sh:7 looks like part of a file name", out)
        self.assertIn("pagina: tree files carry this name (src/pagina.html)", out)


class Apply(Base):
    def prep(self, text=TABLE_A):
        self.table("A.tsv", text)
        rc, out = self.merge()
        self.assertEqual(rc, 0, out)

    def apply(self, *extra):
        return self.run_tool("apply", "--root", self.root, "--table", self.merged, *extra)

    def test_apply_and_check(self):
        self.prep()
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        c = self.read("src/main.c")
        self.assertIn('"--name"', c)
        self.assertIn('"--name-file"', c)
        self.assertIn('getenv("REMOTIX_PORT")', c)
        self.assertIn("outcome=%s nodo=", c)
        self.assertIn("nome->campo", c)                 # not a listed place
        s = self.read("packaging/rx.sh")
        self.assertIn("start) echo go", s)
        self.assertIn("avvia-tutto)", s)
        self.assertIn("${REMOTIX_PORT:-8080}\" /var/lib/remotix/certificates/page.pem", s)
        self.assertIn("ls /var/lib/remotix/pagina\n", s)
        h = self.read("src/pagina.html")
        self.assertIn('id="bar" class="bar barra-alta"', h)
        self.assertIn('"?name=1&nomi=2"', h)
        self.assertIn('o["outcome"]', h)
        d = self.read("docs/guida.md")
        self.assertIn("`remotix --name X`; the file is `page.pem` in certificates.", d)
        self.assertIn("The word nome here", d)
        self.assertEqual(self.read("fasi/FASE-01.md"), FILES["fasi/FASE-01.md"])
        rc, out = self.run_tool("check", "--root", self.root, "--table", self.merged)
        self.assertEqual(rc, 0, out)
        self.assertIn("✅ structure: 4 changed files, 0 with changes", out)
        self.assertIn("nome kept at docs/guida.md:2 — Italian prose", out)
        # a change outside the table is caught
        p = os.path.join(self.root, "src/main.c")
        t = open(p).read()
        rc, out = self.run_tool("check", "--root", self.root, "--table", self.merged)
        self.assertIn("nome (→ name): 1 left: src/main.c:6", out)      # nome->campo: not a listed place
        open(p, "w").write(t.replace("stdio", "stdlib"))
        rc, out = self.run_tool("check", "--root", self.root, "--table", self.merged)
        self.assertEqual(rc, 1)
        self.assertIn("src/main.c:1: more than the table's names changed", out)

    def test_leftovers(self):
        self.prep("REMOTIX_PORTA\tREMOTIX_PORT\tenv-var\tsrc/main.c:4\tport\n")
        self.apply()
        rc, out = self.run_tool("check", "--root", self.root, "--table", self.merged)
        self.assertEqual(rc, 0)
        self.assertIn("REMOTIX_PORTA (→ REMOTIX_PORT): 1 left: packaging/rx.sh:6", out)
        self.assertNotIn("fasi/", out)
        rc, out = self.run_tool("check", "--root", self.root, "--table", self.merged, "--strict")
        self.assertEqual(rc, 1)

    def test_shift_within_window(self):
        self.prep()
        for f in ("src/main.c", "packaging/rx.sh"):
            p = os.path.join(self.root, f)
            t = open(p).read().split("\n")
            open(p, "w").write("\n".join(t[:1] + ["// a", "// b"] + t[1:]))
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        self.assertIn('getenv("REMOTIX_PORT")', self.read("src/main.c"))

    def test_since_maps_big_shifts(self):
        self.prep()
        base = git(self.root, "rev-parse", "HEAD").strip()
        p = os.path.join(self.root, "src/main.c")
        t = open(p).read().split("\n")
        open(p, "w").write("\n".join(t[:1] + ["// x"] * 40 + t[1:]))
        rc, out = self.apply()
        self.assertEqual(rc, 1)
        self.assertIn("not on the line", out)
        self.assertEqual(open(p).read().count("--nome"), 2)    # nothing written
        rc, out = self.apply("--since", base)
        self.assertEqual(rc, 0, out)
        self.assertIn('getenv("REMOTIX_PORT")', open(p).read())

    def test_stale_fails_loudly(self):
        self.prep()
        p = os.path.join(self.root, "src/pagina.html")
        open(p, "w").write(open(p).read().replace("esito", "risultato"))
        rc, out = self.apply()
        self.assertEqual(rc, 1)
        self.assertIn("esito: src/pagina.html:2", out)
        self.assertIn("nothing written", out)
        self.assertIn("REMOTIX_PORTA", self.read("src/main.c"))

    def test_dry_run(self):
        self.prep()
        rc, out = self.apply("--dry-run")
        self.assertEqual(rc, 0, out)
        self.assertIn("dry run", out)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_helpers(self):
        self.prep()
        rc, out = self.run_tool("new", "REMOTIX_PORTA", "--table", self.merged)
        self.assertEqual(out.strip(), "REMOTIX_PORT")
        rc, out = self.run_tool("new", "PIPPO", "--table", self.merged)
        self.assertEqual(out.strip(), "PIPPO")
        rows = fase_b.read_merged(self.merged)
        a = fase_b.map_text("esito=1 --nome x REMOTIX_PORTA", rows, "before")
        b = fase_b.map_text("outcome=1 --name x REMOTIX_PORT", rows, "after")
        self.assertEqual(a, b)


class DiffMap(Base):
    def test_map(self):
        base = git(self.root, "rev-parse", "HEAD").strip()
        p = os.path.join(self.root, "src/main.c")
        t = open(p).read().split("\n")      # 7 entries, lines 1..6 + ""
        t = ["// new"] * 3 + t[:2] + t[3:]   # 3 lines in front, line 3 deleted
        open(p, "w").write("\n".join(t))
        f = fase_b.diff_map(self.root, base, "src/main.c")
        self.assertEqual(f(1), 4)
        self.assertEqual(f(2), 5)
        self.assertEqual(f(4), 6)
        self.assertEqual(f(6), 8)


if __name__ == "__main__":
    os.environ.setdefault("TMPDIR", "/media/REMOTIX/src/full-english-uscite/tmp")
    tempfile.tempdir = os.environ["TMPDIR"] if os.path.isdir(os.environ["TMPDIR"]) else None
    warnings.simplefilter("ignore", ResourceWarning)
    unittest.main(verbosity=1, warnings="ignore")
