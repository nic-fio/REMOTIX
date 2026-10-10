"""rinomina2-plan.json and the generated part of RINOMINA.md."""
import collections
import json
import os
import re


def lang_dir(f):
    parts = f.split("/")
    return parts[0] if len(parts) == 1 else "/".join(parts[:2]) if parts[0] in ("banchi", "installatore", "packaging", "docs") else parts[0]


def write(P, contracts, out, root):
    M, infos = P["M"], P["infos"]
    by_lang = collections.Counter()
    by_dir = collections.Counter()
    for n in M:
        for l in P["origin"].get(n, ()):
            by_lang[l] += 1
    for f, fi in infos.items():
        k = sum(1 for t in fi.defs if t in M)
        if k:
            by_dir[lang_dir(f)] += k
    files = file_moves(P, root)
    plan = {
        "about": "rinomina2.py plan: old → new for every name defined in code (DECISIONI.md §10.38)",
        "counts": {"names_renamed": len(M), "kept_unresolved": len(P["kept"]), "excluded": len(P["excluded"]),
                   "collisions_handled": len(P["collisions"]), "contracts": len(contracts),
                   "files_scanned": len(infos), "files_skipped": len(P["skipped"]),
                   "frozen_register_words": len(P["frozen"])},
        "by_language": dict(sorted(by_lang.items())),
        "by_directory": dict(sorted(by_dir.items())),
        "table": [{"old": n, "new": M[n], "langs": sorted(P["origin"].get(n, ())), "occurrences": P["occ"][n],
                   "how": P["resolved_by"].get(n, "vocabulary")} for n in sorted(M)],
        "kept": [{"old": n, "why": w} for n, w in sorted(P["kept"].items())],
        "excluded": [{"old": n, "why": w} for n, w in sorted(P["excluded"].items())],
        "collisions": P["collisions"],
        "contracts": contracts,
        "frozen_register_words": sorted(P["frozen"]),
        "skipped_files": {f: w for f, w in sorted(P["skipped"].items())},
        "file_moves": files,
    }
    # several old names onto one new name: allowed only where they never meet in one scope (§3); the
    # merges that DID meet are the collisions above, each with its winner and the losers' fate
    same = collections.defaultdict(list)
    for n in sorted(M):
        same[M[n]].append(n)
    plan["shared_new_names"] = {k: v for k, v in sorted(same.items()) if len(v) > 1}
    plan["counts"]["shared_new_names"] = len(plan["shared_new_names"])
    plan["counts"]["merges_met_in_a_scope"] = sum(1 for e in P["collisions"] if e["kind"] == "collision")
    plan["counts"]["data_names_dati_tsv"] = len({o for d in P["dati_files"].values() for o in d})
    plan["contract_coverage"] = coverage(P, out)
    with open(os.path.join(out, "rinomina2-plan.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    md = os.path.join(out, "RINOMINA.md")
    gen = generated_md(plan)
    if os.path.exists(md):
        text = open(md, encoding="utf-8").read()
        a, b = "<!-- generated:begin -->", "<!-- generated:end -->"
        if a in text and b in text:
            text = text[:text.index(a) + len(a)] + "\n" + gen + "\n" + text[text.index(b):]
            open(md, "w", encoding="utf-8").write(text)
    print(json.dumps(plan["counts"]))


def coverage(P, out):
    """The contract lists of the analysis (contratti/*.tsv): what the plan does with each name."""
    from rinomina2 import traduci
    M, kept, exc = P["M"], P["kept"], P["excluded"]
    dati_new = {}
    for d in P["dati_files"].values():
        dati_new.update(d)
    res = {}
    d = os.path.join(out, "contratti")
    if not os.path.isdir(d):
        return res
    for f in sorted(os.listdir(d)):
        if not f.endswith(".tsv"):
            continue
        st = collections.Counter()
        left = []
        for line in list(open(os.path.join(d, f), encoding="utf-8"))[1:]:
            for n in line.split("\t")[0].split(" / "):
                n = n.strip().lstrip("-").rstrip("=")
                if "." in n and not n.startswith("."):
                    n = n.split(".")[-1]
                if not n:
                    continue
                if n in M:
                    st["renamed by the table"] += 1
                elif n in dati_new:
                    st["renamed by dati.tsv"] += 1
                elif n in kept:
                    st["kept (unresolved collision)"] += 1
                    left.append(n)
                elif n in exc:
                    st["left out on purpose (step 2)"] += 1
                elif traduci(n) == n:
                    st["no Italian word"] += 1
                else:
                    st["not renamed (path, product name, or not found by the analysis)"] += 1
                    left.append(n)
        res[f] = {"counts": dict(st), "not_renamed": sorted(set(left))}
    return res


def file_moves(P, root):
    """Step 2, plan only: the git mv list and the references to each path."""
    from rinomina2 import traduci, git_files, skipped, load_protected
    skips = load_protected()[0]
    files = git_files(root)
    moves = []
    seen_dirs = set()
    for f in files:
        if skipped(f, skips):
            continue
        parts = f.split("/")
        newparts = []
        for p in parts:
            stem, dot, ext = p.partition(".")
            # 01-b3-cliente: the number stays, the words change (traduci refuses a leading digit)
            newparts.append((traduci("x" + stem)[1:] if stem[:1].isdigit() else traduci(stem)) + dot + ext
                            if stem else p)
        nf = "/".join(newparts)
        if nf != f:
            moves.append({"old": f, "new": nf})
    # references: by basename, in every text file
    names = {}
    for mv in moves:
        o, n = os.path.basename(mv["old"]), os.path.basename(mv["new"])
        if o != n:
            names[o] = n
    refs = collections.defaultdict(list)
    if names:
        rx = re.compile(r"(?<![A-Za-z0-9_.-])(%s)(?![A-Za-z0-9_-])" % "|".join(re.escape(x) for x in sorted(names, key=len, reverse=True)))
        for f, fi in P["infos"].items():
            for i, line in enumerate(fi.text.split("\n"), 1):
                for m in rx.finditer(line):
                    refs[m.group(1)].append("%s:%d" % (f, i))
    for mv in moves:
        b = os.path.basename(mv["old"])
        mv["references"] = len(refs.get(b, []))
        mv["referenced_at"] = refs.get(b, [])[:200]
    return moves


def generated_md(plan):
    L = []
    c = plan["counts"]
    L.append("<!-- generated by rinomina2.py plan: do not edit by hand -->\n")
    L.append("| | |\n|---|---|\n")
    for k, v in c.items():
        L.append("| %s | %d |\n" % (k.replace("_", " "), v))
    L.append("\n**Names by defining language** (a name defined in two languages counts twice)\n\n| language | names |\n|---|---|\n")
    for k, v in plan["by_language"].items():
        L.append("| %s | %d |\n" % (k, v))
    L.append("\n**Renamed names defined per directory**\n\n| directory | names |\n|---|---|\n")
    for k, v in sorted(plan["by_directory"].items(), key=lambda x: -x[1]):
        L.append("| `%s` | %d |\n" % (k, v))
    L.append("\n### Every collision and how it was resolved\n\n")
    L.append("| target | old names | winner | others → | scopes (first) |\n|---|---|---|---|---|\n")
    for e in plan["collisions"]:
        if e["kind"] == "collision":
            others = ", ".join("`%s`→%s" % (k, "`%s`" % v if v else "**kept**") for k, v in e["losers"].items())
            L.append("| `%s` | %s | `%s` | %s | %s |\n" % (e["new"], ", ".join("`%s`" % o for o in e["olds"]),
                                                       e["winner"], others, "; ".join(e["scopes"][:2])))
        elif e["kind"] == "unresolved":
            L.append("| `%s` | `%s` | (unresolved: %s) | **kept** | |\n" % (e["new"], e["old"], e["why"]))
        elif e["kind"] == "clash":
            L.append("| `%s` | `%s` | (name exists) | %s | %s |\n" % (e["new"], e["old"],
                                                                    "`%s`" % e["result"] if e["result"] else "**kept**",
                                                                    "; ".join(e["scopes"][:2])))
        else:
            L.append("| `%s` | `%s` | (forbidden: %s) | **kept** | |\n" % (e["new"], e["old"], e["why"]))
    L.append("\n### One new name for several old names, never in one scope (checked per scope, §3)\n\n")
    for k, v in plan.get("shared_new_names", {}).items():
        L.append("- `%s` ← %s\n" % (k, ", ".join("`%s`" % x for x in v)))
    L.append("\n### Names not renamed (to resolve in interi.tsv or sinonimi.tsv)\n\n")
    for k in plan["kept"]:
        L.append("- `%s` — %s\n" % (k["old"], k["why"]))
    L.append("\n### Names left out on purpose\n\n")
    for k in plan["excluded"]:
        L.append("- `%s` — %s\n" % (k["old"], k["why"]))
    L.append("\n### Cross-language contracts (every place: rinomina2-plan.json → contracts)\n\n")
    kinds = collections.Counter(k["kind"].split(" (")[0] for k in plan["contracts"])
    L.append("| kind | names |\n|---|---|\n")
    for k, v in sorted(kinds.items()):
        L.append("| %s | %d |\n" % (k, v))
    L.append("\nThe names below are the ones another program reads by spelling: data names, environment "
             "variables, options and kebab names.  The %d code names that merely occur in two languages are "
             "in the JSON only.\n\n" % kinds.get("crosses languages", 0))
    L.append("| old | new | kind | languages | places |\n|---|---|---|---|---|\n")
    for k in plan["contracts"]:
        if k["kind"] != "crosses languages":
            L.append("| `%s` | `%s` | %s | %s | %d |\n" % (k["old"], k["new"], k["kind"], ",".join(k["languages"]),
                                                       len(k["places"])))
    L.append("\n### Coverage of the contract analysis (contratti/*.tsv)\n\n")
    for f, r in plan.get("contract_coverage", {}).items():
        L.append("**%s** — %s\n\n" % (f, ", ".join("%s: %d" % kv for kv in sorted(r["counts"].items()))))
        if r["not_renamed"]:
            L.append("Not renamed: %s\n\n" % " ".join("`%s`" % n for n in r["not_renamed"]))
    L.append("\n### Step 2 (later): file and directory moves (%d)\n\nEvery reference is in rinomina2-plan.json → "
             "file_moves (first 200 per file).\n\n| old | new | references |\n|---|---|---|\n" % len(plan["file_moves"]))
    for mv in plan["file_moves"]:
        L.append("| `%s` | `%s` | %d |\n" % (mv["old"], mv["new"], mv["references"]))
    return "".join(L)
