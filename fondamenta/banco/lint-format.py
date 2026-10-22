#!/usr/bin/env python3
"""lint-format.py — cerca i SEGNAPOSTO TRADOTTI A META' nelle stringhe di formato.

    python3 -I fondamenta/banco/lint-format.py [file-o-cartella ...]   (default: benches/)

Per ogni stringa con segnaposti `%(nome)s` (operatore `%`) o `{nome}` (`.format(...)`)
confronta i nomi con le chiavi del dizionario / gli argomenti, quando questi sono
LETTERALI o costruiti nello stesso file (dict letterale, `dict(...)`, `{**a, ...}`,
una variabile assegnata a uno di questi, con `d["k"] = ...` e `d.update(...)`).
Il modello puo' essere un letterale o una variabile assegnata a una stringa nel file.

Stampa `file:riga: MANCANTI {..}` (segnaposto senza chiave: KeyError sicuro) e
`file:riga: IN PIU' {..}` (chiave che nessun segnaposto usa: di solito un nome
cambiato da una parte sola).  Le chiavi non risolvibili (dizionario che arriva da fuori)
fanno saltare il controllo dei MANCANTI e vengono contate a parte.
Uscita 1 se trova qualcosa.  Non esegue il codice controllato.
"""
import ast
import os
import re
import string
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PCT = re.compile(r"%\((\w+)\)")


def const_str(node, env):
    """Il valore di una stringa letterale / concatenazione / variabile nota, o None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = const_str(node.left, env), const_str(node.right, env)
        if a is not None and b is not None:
            return a + b
    if isinstance(node, ast.Name):
        v = env.get(node.id)
        if isinstance(v, str):
            return v
    return None


class Scope:
    """Le assegnazioni di una funzione (o del modulo): nome -> stringa o chiavi di dizionario."""

    def __init__(self, parent=None):
        self.parent = parent
        self.strs = {}
        self.dicts = {}      # nome -> [set di chiavi, completo?]

    def lookup_str(self, name):
        s = self
        while s:
            if name in s.strs:
                return s.strs[name]
            s = s.parent
        return None

    def lookup_dict(self, name):
        s = self
        while s:
            if name in s.dicts:
                return s.dicts[name]
            s = s.parent
        return None

    def env(self):
        e, chain = {}, []
        s = self
        while s:
            chain.append(s)
            s = s.parent
        for s in reversed(chain):
            e.update(s.strs)
        return e


def dict_keys(node, scope):
    """(chiavi, completo) di un'espressione-dizionario, o None se non e' un dizionario riconoscibile."""
    if isinstance(node, ast.Dict):
        keys, full = set(), True
        for k, v in zip(node.keys, node.values):
            if k is None:                       # **altro
                sub = dict_keys(v, scope)
                if sub is None:
                    full = False
                else:
                    keys |= sub[0]
                    full = full and sub[1]
            elif isinstance(k, ast.Constant) and isinstance(k.value, str):
                keys.add(k.value)
            else:
                full = False
        return keys, full
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        keys, full = set(), True
        for a in node.args:
            sub = dict_keys(a, scope)
            if sub is None:
                full = False
            else:
                keys |= sub[0]
                full = full and sub[1]
        for kw in node.keywords:
            if kw.arg is None:
                sub = dict_keys(kw.value, scope)
                if sub is None:
                    full = False
                else:
                    keys |= sub[0]
                    full = full and sub[1]
            else:
                keys.add(kw.arg)
        return keys, full
    if isinstance(node, ast.Name):
        d = scope.lookup_dict(node.id)
        if d is not None:
            return set(d[0]), d[1]
    return None


def collect(body_nodes, scope):
    """Riempie lo scope con le assegnazioni del corpo (senza scendere nelle funzioni annidate)."""
    for n in ast.walk(ast.Module(body=list(body_nodes), type_ignores=[])):
        pass
    stack = list(body_nodes)
    while stack:
        n = stack.pop(0)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        for ch in ast.iter_child_nodes(n):
            stack.append(ch)
        if isinstance(n, ast.Assign) and len(n.targets) == 1:
            t = n.targets[0]
            if isinstance(t, ast.Name):
                s = const_str(n.value, scope.env())
                if s is not None:
                    scope.strs[t.id] = s
                dk = dict_keys(n.value, scope)
                if dk is not None:
                    scope.dicts[t.id] = [set(dk[0]), dk[1]]
            elif (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                  and t.value.id in scope.dicts):
                k = t.slice
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    scope.dicts[t.value.id][0].add(k.value)
                else:
                    scope.dicts[t.value.id][1] = False
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name) and isinstance(n.op, ast.Add):
            s = const_str(n.value, scope.env())
            if n.target.id in scope.strs and s is not None:
                scope.strs[n.target.id] += s
            elif n.target.id in scope.strs:
                del scope.strs[n.target.id]
        elif (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
              and isinstance(n.value.func, ast.Attribute) and isinstance(n.value.func.value, ast.Name)
              and n.value.func.value.id in scope.dicts):
            c = n.value
            d = scope.dicts[c.func.value.id]
            if c.func.attr == "update":
                for a in c.args:
                    sub = dict_keys(a, scope)
                    if sub is None:
                        d[1] = False
                    else:
                        d[0] |= sub[0]
                        d[1] = d[1] and sub[1]
                for kw in c.keywords:
                    if kw.arg is None:
                        d[1] = False
                    else:
                        d[0].add(kw.arg)
            elif c.func.attr in ("setdefault",) and c.args and isinstance(c.args[0], ast.Constant):
                d[0].add(c.args[0].value)
            elif c.func.attr in ("pop", "clear", "popitem"):
                d[1] = False


def brace_fields(fmt):
    """(nomi, posizionali) dei campi di una stringa .format; None se non e' interpretabile."""
    names, pos = set(), set()
    auto = 0
    try:
        for _, field, _, _ in string.Formatter().parse(fmt):
            if field is None:
                continue
            head = re.split(r"[.\[]", field, maxsplit=1)[0]
            if head == "":
                pos.add(auto)
                auto += 1
            elif head.isdigit():
                pos.add(int(head))
            else:
                names.add(head)
    except ValueError:
        return None
    return names, pos


def check_file(path, rel):
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
        tree = ast.parse(src, path)
    except (SyntaxError, ValueError) as e:
        return [(rel, getattr(e, "lineno", 0) or 0, "NON ANALIZZABILE: %s" % e)], 0
    out, unresolved = [], 0

    def visit(body_nodes, scope):
        nonlocal unresolved
        collect(body_nodes, scope)
        stack = list(body_nodes)
        while stack:
            n = stack.pop(0)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(n.body, Scope(scope))
                continue
            if isinstance(n, ast.ClassDef):
                visit(n.body, Scope(scope))
                continue
            stack.extend(ast.iter_child_nodes(n))
            # ── operatore %
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod):
                fmt = const_str(n.left, scope.env())
                if fmt is None:
                    continue
                names = set(PCT.findall(fmt))
                if not names:
                    continue
                dk = dict_keys(n.right, scope)
                if dk is None:
                    unresolved += 1
                    continue
                report(rel, n.lineno, names, dk)
            # ── .format
            elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and n.func.attr == "format"):
                fmt = const_str(n.func.value, scope.env())
                if fmt is None:
                    continue
                bf = brace_fields(fmt)
                if bf is None or not (bf[0] or bf[1]):
                    continue
                names, pos = bf
                keys, full = set(), True
                for kw in n.keywords:
                    if kw.arg is None:
                        sub = dict_keys(kw.value, scope)
                        if sub is None:
                            full = False
                        else:
                            keys |= sub[0]
                            full = full and sub[1]
                    else:
                        keys.add(kw.arg)
                starred = any(isinstance(a, ast.Starred) for a in n.args)
                if pos and not starred and max(pos) >= len(n.args):
                    out.append((rel, n.lineno, "MANCANTI posizionali: servono %d argomenti, ce ne sono %d"
                                % (max(pos) + 1, len(n.args))))
                if not full and not (names - keys):
                    continue
                if not full:
                    unresolved += 1
                    continue
                report(rel, n.lineno, names, (keys, full))

    def report(rel, line, names, dk):
        keys, full = dk
        miss = names - keys
        extra = keys - names
        if miss and full:
            out.append((rel, line, "MANCANTI %s" % sorted(miss) + (
                "   (chiavi date: %s)" % sorted(keys) if keys else "")))
        if extra and full:
            out.append((rel, line, "IN PIU' %s   (segnaposto: %s)" % (sorted(extra), sorted(names))))

    visit(tree.body, Scope())
    return out, unresolved


def main(argv):
    targets = [os.path.abspath(a) for a in argv] or [os.path.join(ROOT, "benches")]
    files = []
    for t in targets:
        if os.path.isfile(t):
            files.append(t)
            continue
        for d, dirs, fs in os.walk(t):
            dirs[:] = [x for x in dirs if x not in (".git", "vendor", "__pycache__")]
            files += [os.path.join(d, f) for f in fs if f.endswith(".py")]
    count = skipped = 0
    for p in sorted(files):
        res, unres = check_file(p, os.path.relpath(p, ROOT))
        skipped += unres
        for rel, line, msg in sorted(res):
            print("%s:%d: %s" % (rel, line, msg))
            count += 1
    print("-- %d file, %d segnalazioni, %d formati con argomenti non risolvibili (non controllati)"
          % (len(files), count, skipped), file=sys.stderr)
    return 1 if count else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
