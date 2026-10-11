# RINOMINA — the safe mechanical rename of the Italian names (track en-40)

> `DECISIONI.md` §10.38: REMOTIX is fully English — identifiers, file names, options, RCP message and
> capability names included, **no compatibility aliases**.  This document is the plan for the *names*;
> the comments and the sentences were translated by hand in step 1.
>
> ⛔ **Nothing here has been applied to the tree.**  The tool, its tables and this plan are committed;
> the rename itself is a separate, later act (§7).  The tool is deterministic: it is re-run on the final
> tree after the other en-* branches have landed, and the plan below is regenerated from that tree.
>
> ⭐ **Since en-45 (11 Oct 2026) the rename is split in two phases (§0).**  Phase A — internal code
> identifiers only, zero behaviour change — is what `rinomina2.py` does now.  Phase B — every name
> someone outside the code can see — is a later, hand-curated step.  §1–§8 describe the first design
> ("round 1"); where they say a string, a document, an option or a data name changes, §0 overrides them.

| file | what it is |
|---|---|
| `english-migration/rinomina2.py` | the tool: `plan`, `apply --root DIR`, `verify --root DIR` |
| `english-migration/lessico.py` | the lexers: C/GLSL, Go, Python (the real `tokenize`), shell/Makefile/unit files, page HTML+JS+CSS, JSON, Markdown |
| `english-migration/rinomina2_report.py` | writes `rinomina2-plan.json` and the generated part of this file |
| `english-migration/rinomina2-prova.sh` | proves the tool on a **copy** of the tree (§8) |
| `english-migration/rinomina2-plan.json` | the plan: table, collisions, kept names, contracts with every place, file moves |
| `english-migration/interi.tsv` | whole-name decisions by hand, each with its reason |
| `english-migration/sinonimi.tsv` | second English choices, tried in order when the first one collides |
| `english-migration/dati.tsv` | data names that are not identifiers (wire strings, capability values, socket verbs, log keys), each limited to the files listed |
| `english-migration/protetti.tsv` | files never touched, Italian kept on purpose (anchored line ranges), generated files |
| `english-migration/esterni-c-*.txt` | the system headers' macros and file-scope names (built in the debian13 build image) |
| `english-migration/esterni-sh-comandi.txt` | the commands of the server (`compgen -c`): a shell function may not take one of these names |
| `english-migration/contratti/*.tsv` | the contract analysis: RCP names, data names, options and environment variables, with places |

The old `rinomina.py` stays for reference: it rewrote every word of every file, and its dry run
gave 21,650 pairs, 1,346 collisions and 5,284 clashes — the reasons for this second tool.

---

## 0. Two phases: A (internal identifiers, now) and B (public and persisted names, later)

**Why.**  Round 1 (`cd66e92`, branch `rinomina`) passed every static check of §8, yet ten adversarial
reviews (`full-english-uscite/revisione-rinomina/R01…R10.md`) and two live tests (R11 release and
upgrade on 7 distributions, R12 benches against a live server) found about 110 confirmed faults.  Nearly
all of them came from renaming words **inside strings, comments that are commands, documents, and
public or persisted names**: case labels and script actions (`prodotto)`), `-D` macros in shell
strings, Makefile targets called through `sh -c`, page placeholders (`__IMPRONTA__`), log areas and
their padding, fixed slicing (`r[9:]` after `"APERTURA "`), OCR words of the Italian desktop
(«Esci»), substring greps (`FAULT` inside `DEFAULT`), English words rewritten (`serve` → `needs`),
file names on disk (certificates, `gruppi-iscritti.jsonl` keys), variables in `/etc` conf files, CLI
options with dodge names (`--label_name`, `--page_v`), wire strings (RCP capabilities, socket verbs),
and — blocking every installation — an encoder name built at run time (`codec + "_" + "gpu_card"`)
that no longer matched its table (R11 D1, R12 P1).  A rule per fault does not converge; the scope
of the rename had to shrink.

### 0.1 Phase A — what changes

| place | phase A |
|---|---|
| string literals, any language | **never** (checked: `fase_a.py check`, §0.3) |
| documents (`*.md`, the manual's chapters, `docs/*.html`) | **never**, except a Markdown code span that is **exactly** one renamed identifier holding `_` or an internal capital (`` `rcp_misura_ammessa` ``, optionally `()`), and never in `fasi/`, `memoria/`, `misure/` |
| comments | only tokens that are renamed identifiers **and** hold `_` or an internal capital (so never `serve`, `accuse`, `nobody`); never inside `«…»`, never a path piece or an option; a comment line that is a command example (`bash …`, `python3 …`, `--x`, `VAR=…`, `make …`) is left whole |
| C, Go, Python, page JavaScript | the identifiers of code regions (someone else's members excepted, as before) |
| shell | from the **shfmt syntax tree** (`fase_a.ShellFile`): `$x`/`${x…}` references, assignments and `local`/`export`/`declare`/`readonly`, `for x in`, the names of `read`/`unset`/`mapfile`/`getopts`, function definitions, and command words that call a function of ours (defined in the file or a file it sources).  Every other word — arguments, case labels, `-DNAME`, `make X`, globs, paths, words inside quotes — never.  A file shfmt cannot parse is not touched (today `banchi/01-b6-lancia.sh`) |
| Makefiles, unit/conf files, Containerfiles, spec, JSON, CSS, HTML outside `<script>`, GLSL shaders, data and history files | **never** |

### 0.2 Frozen names

A name is **frozen** — not renamed anywhere — when its exact spelling occurs as a whole token
anywhere the tool does not rename.  Conservative by construction: when in doubt, frozen.  The sources
(`fase_a.frozen()`):

- every string literal of every language (Python docstrings, JS template literals, C/Go strings,
  shell quoted words and heredocs — a `$x` inside double quotes is a reference, the rest is text);
- every document (history included: `fasi/`, `memoria/`, `misure/`), outside the exact spans above;
- every shell word that is not a reference (arguments, case labels, `-DNAME`, globs, `make X`), and
  every word of a shell file shfmt cannot parse;
- Makefiles, unit/conf/spec files, Containerfiles, JSON and JSONL, CSS, HTML attributes and text,
  GLSL shaders, logs, the generated pages;
- the components of every file name of the tree;
- `REMOTIX_*`/`RX_*` (public environment);  a shell variable read with a default
  (`${X:-…}`) on an upper-case name, or read and never assigned anywhere (an input from outside);
- options and their argparse destinations (an option is a string, and `--x-y` freezes `x_y`);
- JavaScript object-literal keys and shorthand properties (they become JSON, log lines, messages;
  with `{a}` the variable's name *is* the key), `dataset.x` members, and since round 3 (A-01) **every
  property name**: `obj.k` read or assigned, members of the `window.REMOTIX` objects, class and
  object-literal methods, class fields — JavaScript renames only variables, functions, parameters,
  classes and labels;
- Go fields without a JSON name in packages that use `encoding/json` (and their lower-case key);
- Python keyword arguments that become data or go to someone else's function (`dict(x=…)`,
  `.format(x=…)`, a keyword no function of ours declares), dataclass/NamedTuple/Enum fields, every
  name of a file that reads names at run time (`locals()`, `vars()`, `__dict__`, `asdict`), class and
  function names printed through `__name__`, and since round 3 (A-04, A-06, A-08) **every class
  deriving, directly or through a class of ours in any file, from `BaseException`** (tracebacks,
  `repr` and `type(e).__name__` print it), and every class of a file that prints a `repr` (`%r`,
  `!r`, `repr(`, `format_exc`, `print_exc`, `.exception(`);
- C arguments of a macro that stringifies (`#x`) or pastes (`##`) them;
- names built at run time from a literal piece (`"cmd_" + x`, `fn_$1`) in files that look names up
  at run time (`getattr`, `globals()`, `${!x}`, `eval`, `window[…]`).

Two old names may never become one new name in a scope (§3 unchanged), and phase A adds a per-file
role with **every** code token of the file: a new name may not land on any token already in the file,
nor on someone else's member (the class of R07 F4: two keys of one JavaScript object merged).

Round 3 adds two rules on the **new** name (`rinomina2.forbidden`); a name that breaks one takes its
next alternative from `sinonimi.tsv`, or stays as it is:

- **symmetric to the freeze** (A-06): the new name may not occur as a whole token in any text the
  tool does not rename — the same texts that freeze an old name (strings, documents, data, shell
  words, history sources).  Otherwise a reader of text finds a name it never met before: `SERVITORE`
  → `SERVER` in `15-f014`, while `15-giro.py` looks for a `SERVER = "…"` declaration in every bench;
  `otten` → `got_n`, a word `16-classifica.py` looks for in the logs.
- **no shadowing** (A-04, A-02): not a Python keyword or builtin (`exec`, `input`, `id`, `type`…);
  not a JavaScript reserved word or browser global (`name`, `status`, `event`, `top`, `parent`,
  `self`, `length`…), for any page name, not only top-level ones; not a shell reserved word or
  builtin, and a shell function not a command of the machine (`esterni-sh-comandi.txt`, `compgen -c`
  on the server); not a C keyword, system macro or file-scope name of the system headers, for any C
  name, nor a reserved C family (`str*`, `mem*`, `wcs*`, `is*`, `to*`, `E[A-Z0-9]*`, `SIG*`, `LC_*`,
  `_X`, `*_t` …).

The number of renamed and frozen names, the frozen names by reason and the **fallback names**
(collision alternates from `sinonimi.tsv` and dodge suffixes such as `_v`) are in the generated part
(§9).  A fallback name is acceptable only for an internal name; in phase A every renamed name is
internal by construction (anything public is frozen), and the list is there to be improved by hand.

### 0.3 The proof of phase A

`rinomina2-prova.sh <copy> --rilascio` (§8) with two changes:

- **1b · strings** — `fase_a.py check --root <copy>`: for every changed file, against `HEAD`, (a) the
  text with every identifier replaced by one placeholder is identical (only names changed), and (b)
  the multiset of string-literal contents is identical — Python through `ast` (every `str`/`bytes`
  constant, f-string pieces included), shell through the shfmt tree (every literal except the name
  positions phase A may change), C/Go/JS/HTML through the lexers; a Markdown file may differ only in
  its exact identifier spans; any other kind of file must not change at all.  On the round-1 tree the
  same checker flags 497 of 576 changed files.
- **5b · the binary's literals** — the server is also built from `HEAD` (before the rename) and the
  `.rodata` sections of the two `remotix` binaries must be byte-identical: every literal and format of
  the C program, and the function names that `assert()`/`g_return_if_fail()` print.  The first run of
  phase A failed here on three names (`cattura_conteggi`, `wlr_fotogramma`,
  `wlr_input_keymap_da_testo`: their `g_return_if_fail` prints the function's name), now frozen.
- **6 · benches** — the list of benches is made **once, on the tree before the rename**, and the same
  files run after it.  The old check grepped each tree for its own spelling of the option: the 15-suite
  benches get `--certifica` from the shared runner (`S.esegui`), so they never appeared in the list —
  that is why `15-f029 --certifica` (exit 0 before, 1 after on round 1) passed unseen as «62 same»
  (R07 F1).  The comparison is now: same exit code, no new `Traceback` (R05 F2: a crash with the same
  exit code), and the **same output** (digits and `/tmp` paths normalised; a traceback is compared by
  its last line, since it quotes renamed source).  `12-client-veri.py` and `12-c20-veri.py` never run
  here: their `--certifica` drives real browsers against a default URL on the rete11 box (R12 incident).

Proof of phase A, 11 Oct 2026, on `4c79004` (copy `remotix-wt-en-45-prova`, `--rilascio`): 363 files,
28,197 replacements, 5,186 names renamed, 5,195 frozen; every check green — quotes and protections,
**strings: 0 of 363 changed files with a string or structure change**, `bash -n` 154, Python 183,
`node --check` 12, installer 3 packages, C 42 objects and the link, **`.rodata` byte-identical**,
**82 benches `--certifica`: same exit code and same output**, `rilascio.sh` debian13.  Every
fault of R01–R12 re-checked on the renamed copy (`full-english-uscite/revisione-rinomina/fase-A-verifica.md`):
128 gone, 0 still there, 3 procedure items phase A does not trigger, 1 not a rename fault.  The two the
reviewers still found (R10 F8, F9: benches that compile git-history sources with today's files) are now
frozen by `fase_a.HISTORY_SOURCES`.  `gofmt -w` on the changed Go files remains part of applying (§7 step 4):
renamed fields change gofmt's alignment, and `rilascio.sh` stops on an unformatted file.

### 0.4 Phase B — later, with Nic

Everything frozen above that should still become English: options (`--nome`, `--pagina`, the benches'
options), environment variables (`REMOTIX_PORTA`, `REMOTIX_OPZIONI`, …), conf keys, RCP capability
names and socket verbs, log areas and log keys, page placeholders and ids, JSON keys of registers and
of on-disk records (`gruppi-iscritti.jsonl`, the catalogue), directory and file names on installed
machines (`/var/lib/remotix/certificati/pagina.pem` …), case labels and script actions, and the
identifiers frozen because one of those spells them.  Phase B is **a hand-curated table** (one row
per public name, its new spelling chosen by a person — no collision dodges), applied together with
**an upgrade migration** where the name is persisted (conf rewrite, certificate move, old-key readers
or a format version bump, hooks and boxes to reinstall, RCP version) and with the user's decision
where §10.38 «no aliases» meets an installed base.  `dati.tsv`, `contratti/` and the R01–R12 reviews
are its starting material; phase A does not read `dati.tsv`.

---

## 1. Which names enter the table

Only **names that occur in code**, found by a lexer of their own language with comments and string
literals set apart:

- **C** (`src/`, `banchi/*.c`, `banchi/rcp/`, the GLSL shader): every identifier in code — functions,
  variables, macros, types, struct fields, enum values.  A name that the system headers define
  (`esterni-c-*.txt`) is not ours and never changes.
- **Go** (`installatore/`, vendor excluded): every identifier in code.  The package names wait for
  step 2 with their directories.
- **Python** (benches, docs generators): the names of the real tokenizer, f-string expressions included;
  attributes count when assigned (`self.x =`) or derived by argparse from an option we define.  Local
  module names wait for step 2 with their files.
- **Shell, Makefile, packaging scripts**: functions, variables (assigned, `local`, `read`, `for`,
  `${…}`), case labels, make variables and targets.
- **The page and the bench pages**: JS identifiers, element ids and classes, CSS selectors.
- **Options** only when a parser of ours defines or compares them (`case --x)`, `add_argument`,
  `strcmp(argv…, "--x")`, `getopt_long`, Go `flag`): `--non-interactive` belongs to zypper and stays.
- **Environment variables** `REMOTIX_*` and `RX_*`.
- **Data names** in `dati.tsv` (73 today): RCP reason and sub-code names, state strings
  (`attesa-ciao`), socket verbs (`SBLOCCA`, `TOLTO`, `NON-BANNATO`), capability names and the value
  `si`, log keys (`byte_persi=`), page placeholders (`__IMPRONTA__`).  Each one changes **only in the
  files the contract analysis found it in**, and in the documents' code spans.

A member used but never declared or assigned by us (`event.altKey`, `tea.WithAltScreen`,
`st.st_mtime`) is someone else's and never changes, even when its spelling holds an Italian word.
Test accounts (`prova*`, `provanic*`, …) and `intoccabili.txt` never change.

## 2. Where they change

| region | rule |
|---|---|
| code | every identifier of the table |
| string literal | whole tokens of the table only; never a path component (§2.1); never inside `«…»`; never inside an Italian sentence (the sentence is protected, the keys around it are not: `{"formato":…,"da":"REMOTIX alla prima connessione"}`); never on a protected line of `protetti.tsv` |
| comment | as a literal; a comment that is still an Italian sentence is left whole |
| Markdown | **only** inside code spans and fenced blocks.  Never in a span holding `«`, an Italian sentence or a log line; never in an untagged block that looks like output (timestamps, `OK`/`NO` lines, ⭐⛔⚠ lines, system messages: at least half its lines); never in `«…»` |
| data, history, generated, vendor | never (`protetti.tsv` and the built-in list: `*.jsonl`, `*.log`, `misure/`, `memoria/`, `fondamenta/`, `anteprime/`, `banchi/prodotto/`, the suite reports, the archived design folders, `english-migration/`, vendor, protocol XML, the SPIR-V header, the manual's HTML, licences) |

### 2.1 Paths wait for step 2

`figlio.c`, `sessione.log`, `banchi/rcp`, `gofmt -l motore`: a token followed by a file extension, or a
component of a relative path that names something in the tree, or a bare file/directory name in a
shell command, is a path and changes with the file moves.  Absolute paths of the real machines
(`/media/REMOTIX/…`, `/home/nicfio/…`, `~/…`) never change.  A product path (`/var/lib/remotix/…`)
changes with the code that builds the same path from `filepath.Join` pieces, so the two spellings stay
one.  A shell variable is never a path (`"$qui/uscita"` renames `qui`, keeps nothing else).

### 2.2 The recorded registers

The registers themselves (`*.jsonl`, `misure/`) are never rewritten.  The benches that write them are
renamed like everything else, so **a register written after the rename has English keys** and the same
bench reads it.  What changes is the reading of **old** registers and old logs: a bench that re-reads a
past campaign (`16-riclassifica.py`, `16-classifica.py` on `misure/fase16`, `15-rapporto.py` on old
rounds, C12/C13/C15 on `11-gancio-registro.jsonl`) needs both spellings, by hand (§6).

⭐ Done on en-42 (11 Oct 2026): every such reader carries an explicit old-spelling map — a tuple
`_OLD_WORDS` (protected in `protetti.tsv`) zipped with `_WORDS_NOW` (the same words, renamed with the
code) into `OLD_SPELLING`, applied by `current_spelling()` where a row is loaded, and `spellings()`
for folder prefixes on disk (`utente-NN/`).  Before the rename the map is empty.  Readers:
`16-classifica.py`, `16-riclassifica.py`, `16-rapporto.py`, `15-rapporto.py`, C12, C13, C15,
`11-registro-unisci.py`, `04-b28-gesti.py --verdetto`, `01-b8-cronometro.py --verdetto --giro`.
Free-text forms (reasons, log rows, page diary lines) stay dual-form regexes on protected lines.

A freeze of the registers' words (1,095 keys and values kept Italian in the benches' literals) was
built and **proved harmful on the copy**: `16-risorse.py` builds one record from keyword arguments
(renamed: code) and from string keys (frozen), and its self-certification broke.  It stays in the
tool, switched off (`FREEZE_REGISTERS`).

## 3. Collisions and clashes

One mapping for the whole program (old → new): the same Italian name is the same English name in every
file and every language, so strings that two programs exchange stay equal on both sides.

### 3.1 The check is per scope and per role

Two old names may share one new name (`shared_new_names`, 284 today) as long as they **never meet**.
They meet only inside a scope:

| scope | made of |
|---|---|
| `tu:` C translation unit | the `.c` file and every project header it includes, transitively |
| `c-program:` | the file-scope names (brace and paren depth 0) of every C file of one directory: the link |
| `go-package:` | every file of the directory, tests included |
| `py:` | the file and the local modules it imports (same directory, or a unique stem) |
| `sh:` | the file and what it `source`s |
| `file:` | a page, a Makefile, a unit file: the file alone |
| product data | the data-like string literals of `src/`, `installatore/`, `banchi/rcp/`, `packaging/` together: two wire words may never become one; the literals of one file likewise, compared **whole** (`"cert.stato"`), not word by word |

Inside a scope a name has a **role**, and a new name collides only with a name of the same role:

| role | what |
|---|---|
| plain | identifiers: C the translation unit, Go the package, Python the names its syntax tree binds or reads (a keyword argument of someone else's function, `env=` of `subprocess.run`, is not a variable of ours), the page's JS, shell/make the variables, functions and labels **defined** |
| member | a member of ours after `.` or `->` (C, Python, page).  Someone else's member never collides |
| sel | the page's ids, classes, custom properties, keyframes, `data-*` attributes |
| field | Go: the fields and methods of one struct, with the structs that embed it or that it embeds; a name that is only a field or a method lives in its struct, not in the package |
| cmd | shell: words in command position — a function of ours may not take the name of a command the file runs |
| options, environment | options per parsing file; `REMOTIX_*`/`RX_*` variables are global |

So `stato` → `state` in the C server and `stato` → `state` in a bench never meet; `ragione` and `motivo`
in one Python file do, and one of them moves.

Kinds of conflict:

1. **collision** — two old names, one new name, both in one scope and one role.  The winner is pinned by
   `interi.tsv`, else the more frequent name; the other moves to its `sinonimi.tsv` alternative.  Each one
   is listed in the generated part («Every collision»): **merges met in a scope**, 38 today after the
   en-44 review (76 before it: 41 losers' names were poor English and got an `interi.tsv` row);
2. **clash** — the new name already exists in the scope and does not itself change;
3. **forbidden** — a keyword of the language, a system-header macro, a libc/glib global for a C global,
   a Go predeclared name or a method onto a well-known interface (`String`, `Error`, `Write`), a shell
   reserved word or builtin for a function, a window property for a top-level `var`/`function` of a page,
   a well-known environment variable (`USER`, `PATH`, `LINES`, `SECONDS`…) for a shell or make variable;
4. **twins** must stay twins: an option's kebab and snake spellings (`--prova-codifica` ↔
   `args.prova_codifica`), `el.dataset.fooBar` ↔ `data-foo-bar`, and a Go struct field read from
   **untagged JSON** with its lowercase key (`Utente` ↔ `"utente"`: Go matches them ignoring case).  When
   the English of an untagged field is two words the key cannot follow, and both stay for a person to
   decide (`Motivo`/`motivo`, `Amb`/`amb`).

The loop runs until nothing changes (4 rounds today); a final pass leaves **unrenamed** every name that
still conflicts (11 today).  A kept name is safe — it stays Italian everywhere — and is listed below for a
decision in `interi.tsv` or `sinonimi.tsv`.

### 3.2 Names that are not ours: the Web platform guard

`esterni-web.txt` lists the Web platform's names that are never renamed whatever the vocabulary says
(`alt` → `height` once made `AltLeft` `HeightLeft`): `KeyboardEvent.code` and `.key` values, event, DOM,
WebCodecs, WebTransport and WebAudio members, the CDP keywords the benches speak.  The tool adds,
mechanically, what each page shows to be the platform's: members of event objects (the parameter of a
listener, or `ev`/`evt`/`event`), strings compared with `.code`/`.key`, attribute names given to
`setAttribute` & co., non-`data-` attribute selectors in CSS, every `aria-*` name and its `ariaX`
reflection.  HTML tags are a lexer region of their own: an attribute name other than `data-*` never
changes, nor the value of an enumerated attribute; in CSS only selectors (compound ones included:
`#esito.bene`), custom properties and `@keyframes` names are ours.

### 3.3 Identity rows: «do not rename»

A row of `interi.tsv` whose new name equals the old one means **keep it as it is**: the name leaves the
table (listed under «Names left out on purpose», with the row's reason) and so does its twin.  Used for
platform names the guard cannot infer (`AltLeft`, `altKey`, `aria-pressed`, `DX`) and, since en-44, for
the five exports of the Opus WebAssembly module (`rx_apri`, `rx_pacchetto`, `rx_pacchetto_max`,
`rx_uscita`, `rx_decodifica`): the page and the benches call them as members of the instance's exports
(never "ours" in JS, so they would not follow), and the embedded `opus.wasm` blob carries the old export
names until it is rebuilt with `src/opus-wasm/costruisci.sh`.  Renaming them is one decision for later,
together with that rebuild.

### 3.4 Names bound to strings

A name that a program reaches through a string — `getattr(o, "x")`, `hasattr`, an argparse positional
(`add_argument("passo")` gives `a.passo`), a member assigned through `setattr` — changes only if the string
changes with it.  en-44 checked all 60 such places (`getattr`/`hasattr` strings and argparse positionals in
the benches) on an applied copy: in every one the string and the identifier still agree.

## 4. The contracts

The full list with every place is `rinomina2-plan.json` → `contracts`; the summary is in the generated
part.  What the analysis found that a whole-token rename cannot see, and how the plan stands:

| place | why it is fragile | status |
|---|---|---|
| `src/comando.c:114` `strncmp(buf, "SBLOCCA ", 8)` and `buf[8]` | the length is hard-coded | `UNBLOCK ` is 8 bytes too: holds |
| `src/costruisci.sh:187` greps `NON-BANNATO` in the built binary | text inside the binary | renamed on both sides (`dati.tsv`) |
| `01-b7-congedo.py:444` anchors on `"const MOTIVO = {"` in the page | page source read as text | `MOTIVO` is renamed in both (a whole token in the literal) |
| `01-b6-lancia.sh:365` builds `CIAO:TETTO_CIAO` pairs and upper-cases keys | names assembled | to re-check by the bench after the rename |
| `01-b11-guasto-innesta.py`, `01-b3-rcp-innesta.py` | graft anchors are multi-line C text in Python strings | renamed token by token like the C; B11/B3 must be re-run |
| page `T_APPUNTI.{ANNUNCIO,CHIEDI,TESTO}` composes type names | prefix + key | keys and full names both in the table; B9 checks |
| `nome_input()`, `NOMI_STATO` tables print names through `%s` | benches grep the printed form | tables are string literals of the table's names: renamed together |
| `data-bannato` read as `dataset.bannato` | the browser camel-cases | `dataset.x` members follow the table |
| log areas padded to 7 characters; `09-b70:1827`, `09-b79:1267` match the spacing | a new area name of another length breaks the column | **to check**: the padding is computed (`%-7s`); the two benches must be re-run |
| `09-b81` reads the format string `"linea-morta %s causa="` from the source and the binary | text read from source | `linea-morta` is a contract name (kebab) |
| thread names (`figlio.c:4659`) | 15 characters at most | **to check** every renamed `pthread_setname_np` literal |
| `-X remotix/installatore/motore.VersioneMotore` | Go ignores a missing symbol | the selector after the package path is renamed (`EngineVersion`, `interi.tsv`), the path waits for step 2 |
| `09-b70-ritmo.py`: `printf '%%s' 'CIAO'` then `wc -c` must say 4 | a payload whose LENGTH is checked, not the RCP name | protected line (`protetti.tsv`): `HELLO` is 5 bytes |
| `"memoria_" + rc`, `pag[n + ".html"]` | names and file names built at run time | handled: a literal prefix glued to a variable makes its compounds follow the renamed tail; the bare stems of a file name built at run time stay with the files |
| `make "$AZIONE"`, rpm macros `%{?rx_versione}` | names in variables and macros | make targets/variables and `rx_*` macros are in the table/`dati.tsv` |
| `--(rilievo|comando-socket|…)` regex alternations, `"--%s" % k` | options assembled or in regexes | **to check** by hand after the rename (listed in `contratti/opzioni-contratto.tsv`) |
| history readers (`16-classifica`, `16-riclassifica`, `15-rapporto`, C12/C13/C15) | old registers keep Italian keys | §2.2: both spellings by hand where old data is re-read |
| `RCPREG` (recording magic) | old recordings | not renamed |

## 5. File and directory names — step 2, plan only

`rinomina2-plan.json` → `file_moves` gives the `git mv` list (the number prefix of a bench stays,
`01-b3-cliente.py` → `01-b3-client.py`) and, for each file, every line that names it.  It is a
separate, later step because every path left untouched by step 1 (§2.1) changes there, together with
the Python module names, the Go package directories, the binary names (`remotix-figlio`), the product
paths that are files of the tree (`utenti-negati`), and `sessione.log`-like file names.

## 6. Risks

- **Meaning**: a second choice from `sinonimi.tsv` is safe but not always the best English
  (`stato` → `cur_state` in some places).  Every one is marked `sinonimi.tsv` in the table: review
  before applying.
- **Central names kept**: when even the alternatives collide, the name stays Italian (list below).  The
  rename is incomplete until those get a decision.
- **Text read by spelling** outside code (regexes, assembled names, padded columns): §4.  The benches
  that read another program's output must be re-run, not only compiled.
- **History**: §2.2.  Readers of `misure/` keep working; registers written after the rename keep the
  frozen words.
- **Branches still landing**: the plan is a function of the tree.  Re-run `plan` on the final tree;
  anchors of `protetti.tsv` are text, not line numbers, so they survive edits.

## 7. Application order

1. All en-* branches merged into `full-english`; tree clean; no campaign running on the server.
2. `python3 english-migration/rinomina2.py plan` on the final tree.  Review the generated part:
   kept names, collisions, `sinonimi.tsv` choices; decide in `interi.tsv`, `sinonimi.tsv`,
   `dati.tsv`; re-run `plan` until the review is clean.
3. Prove on a copy (§8): `git worktree add --detach <copy> HEAD`, then
   `english-migration/rinomina2-prova.sh <copy> --rilascio`.  Everything green, or back to 2.
4. Apply to the tree: `python3 english-migration/rinomina2.py apply --root .`, then `gofmt -w` on the
   changed Go files (the golang:1.25 image, as the prova script does).
5. The checks of §8 on the tree itself, plus: `cmp src/rcp.c banchi/rcp/rcp.c` (and `rcp.h`,
   `autenticazione.c`); the manual rebuilt (`docs/sources/build.py`) with `--controlla`; the
   generated files rebuilt (SPIR-V header, site pages); `ch24_glossary.py` rewritten as an English
   glossary (it lists the Italian names on purpose and is not touched by the tool).
6. One commit for the identifiers.  Step 2 (files) is a later commit with its own plan run.
7. The safety net on the server (`11-gancio.sh gira --famiglia tutto`) and the benches that read
   other programs' text (§4) before anything is called done.

## 8. The checks — and the proof on a copy

`rinomina2-prova.sh <copy>` resets the copy to its commit, applies the plan and runs:

| # | check | how |
|---|---|---|
| 1 | `«…»` of every `.md` unchanged; protected files unchanged; protected lines' literals unchanged | `rinomina2.py verify` against `HEAD` |
| 2 | shell and Python syntax | `bash -n` on every script; `compile()` on every Python file |
| 3 | page JavaScript | every `<script>` of `src/` and `banchi/` pages through `node --check` (node:22 image) |
| 4 | installer | `gofmt -w` on changed files, then `installatore/costruisci.sh prove` (gofmt -l, go vet, go test) |
| 5 | C | `make` of the server in the debian13 build image: every object, the link, the twin check |
| 6 | benches | `--certifica` of every bench that has it, same exit code as before the rename (`--certifica` or `--rilascio`) |
| 7 | release | `packaging/rilascio.sh` for debian13 into the copy (`--rilascio`) |

### 8.1 The proof, 10–11 Oct 2026, on commit `2389e66` (full-english at the start of this track)

Copy: `/media/REMOTIX/src/full-english-uscite/rinomina-prova` (a detached `git worktree`).
`rinomina2-prova.sh … --rilascio`, last run:

| | result |
|---|---|
| applied | 575 files changed, 160,654 replacements, 10,319 distinct pairs (table and `dati.tsv`) |
| 1 · quotes and protections | ✅ 5,912 `«…»` in the documents unchanged; 0 protected files changed; 39 protected regions unchanged |
| 2 · syntax | ✅ `bash -n` 153 scripts; ✅ Python `compile()` 183 files |
| 3 · page JavaScript | ✅ `node --check` 12 scripts (the page and the bench pages) |
| 4 · installer | ✅ gofmt clean after `gofmt -w`, `go vet`, `go test`: 3 packages ok |
| 5 · C | ✅ 42 objects, the server links, the twin check (`banchi/rcp/`) passes |
| 6 · benches `--certifica` | 61 of 62 benches give the same exit code as before the rename; ⛔ `16-riclassifica.py` (§8.2) |
| 7 · release | ✅ `packaging/rilascio.sh 0.99.0-1` for debian13: engine tests, `.deb`, lintian 0 E / 0 W, R13 bench-in-binary ✅, R13 bench options in the unit ✅, R14 ✅, R4 ldd ✅, the `.run` |

What broke on the way and is now handled by the tool (each was a real fault on the copy):

| fault on the copy | cause | rule now |
|---|---|---|
| `--non-interactive` → `--not-interactive` | every `--x` was taken as ours | options only where a parser of ours defines or compares them |
| `tea.WithAltScreen` → `WithHeightScreen` | an external member with an Italian-looking part | members never declared or assigned by us are not ours |
| `"ver.porta"` vs `"ver.port"` | the register freeze applied to some files only | freeze removed (§2.2) |
| catalogue not read | `catalogo.json` was one string region, skipped as prose | JSON lexed key by key |
| `"\naltro:x:1001"` not renamed | a token right after `\n` | escape letters end a token |
| `/home/altro/…` vs user `other_one` | all `/home/` paths protected | only the real machines' paths are protected |
| `appunti.txt` vs `clipboard_text.txt` | two path rules disagreed | one rule: a token followed by an extension is a file name |
| `gruppi-iscritti.jsonl` keys vs Go fields | an Italian sentence protected the whole literal | only the sentence piece is protected |
| `Utente` (Go) vs `"utente"` (JSON) | untagged struct, two different fates | case twins for untagged JSON fields |
| `nome` → `labelName` everywhere | the case-twin rule applied to every Go name | only untagged JSON fields; two-word English kept for review |
| `RX_SPORCO` unbound in `costruisci-deb.sh` | `$SPORCO` inside `«…»` was protected | a shell variable is never protected |
| `11-scatole` → `11-boxes` | `scatole` matched inside a numbered name | a token never starts after `<alnum>-` |
| `c['regola']`, `(?P<nome>…)` | `«…»` protected inside code literals | `«…»` protects comments and documents only |
| `"memoria_" + rc`, `pag[n + ".html"]` | names built at run time | prefixes and run-time file stems (§4) |
| `printf 'CIAO' \| wc -c` = 4 | a payload's length | protected line |
| `16-classifica` network rows | a protected range too wide kept the `rete-quic` regex | the range narrowed to the dual-form regexes |

### 8.2 What still blocks

- **`16-riclassifica.py --certifica`**: this bench exists to re-read **past** campaigns (`salita.jsonl`,
  `stato.jsonl`, `utente-NN/` folders, Italian reasons such as `ENTRATA FALLITA (1 entrati su 4)`).
  After the rename its keys and literals are English, so its own synthetic old-format fixtures no longer
  match.  A mechanical rename cannot write a reader of both spellings: it must be adapted by hand
  (dual forms for the keys `classe`, `ragione_classe`, the `utente-` folder prefix and the reasons), or
  declared a frozen tool of the past and excluded.  ⚠ The same holds, without a red light, for every
  bench that re-reads old data (§2.2).  ⭐ Solved on en-42 (§2.2).
- ~~**136 names are not renamed**~~ (11 today, after the scope-aware check of en-43; generated list below): mostly a second choice that collides too, and
  untagged JSON fields whose English is two words (`Stato`/`stato`, `Porta`/`porta`, `Motivo`/`motivo`,
  `Nodo`/`nodo`).  Safe (they stay Italian everywhere), but they need a decision in `interi.tsv`.
- **Word order**: the vocabulary translates word by word in Italian order (`sessione_marca` →
  `session_mark` is fine, `tela_minima` → `canvas_minimum` is not).  The options and environment
  variables reordered by the contract analysis are in `interi.tsv` (109); the rest of the code keeps
  the literal order until someone reviews it.
- **Not run on the copy**: the safety net in the boxes, the benches against a live server, and the
  manual's `--controlla` — they belong to §7 step 7 on the server.

### 8.3 The last review before applying (en-44, 11 Oct 2026)

On an applied copy of `dcfea5d`, every place where a name lives inside a string was read back against the
code that uses it.  Five real faults were found, each now a rule of the tool:

| fault on the copy | cause | rule now |
|---|---|---|
| the page's worker shell posted `perche: perche` while the function's parameter became `reason_text` (a `ReferenceError` at the first farewell on the worker path); `REMOTIX.tocco.perche()` and `R.giro.quando.size` left Italian inside the benches' JS strings | the Italian-sentence guard counted `perche`, `quando` as Italian words | a word glued to a dot is a member, not prose; one stop word repeated is a key and its value; the unaccented `perche` (an identifier used 1,200 times) is no longer a stop word |
| the worker posts `scene:` but the main thread read `s.scena` | the key lives only in a template literal, so the member looked external | the object-literal keys of a JS template literal are members of ours |
| `#esito.bene` kept in the CSS while `className = "all_ok"` | a compound selector's class was not seen as ours | compound selectors count |
| `impronta()` defined in a script, called `fingerprint` | `impronta` is also a directory of the tree, so the bare word looked like a path | a shell function or variable defined in the file is a name, not a path |
| the page and `18-a1` call `rx_apri()` on the wasm exports, the C exported `rx_open` | a member never declared in JS is external | identity rows (§3.3) |

Also checked and sound: the 60 string-bound names (§3.4); `Schermo` → `Screen` travels to the worker by
`Screen.toString()` together with every name of the shell (the bench that counted textual substitutions in
`Schermo`, `03-b16-dipinti.py`, was removed in step 1, so no count is left to match); the messages between
worker and main thread read only keys the other side sends.  The 76 merges met in a scope were read one
by one: 41 losers had a poor alternative (`_v` suffixes, `refound`, `run_it`) and got an `interi.tsv` row.

Proof on the copy with the rules above (`rinomina2-prova.sh`): 576 files, 167,429 replacements; checks
1–5 green (154 scripts, 183 Python files, 12 page scripts, 3 Go packages, 42 C objects and the link);
6 `--certifica`: 62 benches, the same exit code as before the rename in all 62 (`16-riclassifica` included).

---

## 9. The plan in numbers (generated by `rinomina2.py plan`)

<!-- generated:begin -->
<!-- generated by rinomina2.py plan: do not edit by hand -->
| | |
|---|---|
| names renamed | 4601 |
| kept unresolved | 499 |
| excluded | 5293 |
| collisions handled | 502 |
| contracts | 59 |
| files scanned | 614 |
| files skipped | 2585 |
| frozen register words | 1095 |
| shared new names | 18 |
| merges met in a scope | 3 |
| data names dati tsv | 0 |
| names frozen phase a | 5290 |
| fallback names | 84 |

**Names by defining language** (a name defined in two languages counts twice)

| language | names |
|---|---|
| c | 1989 |
| go | 467 |
| html | 238 |
| py | 1769 |
| sh | 178 |

**Renamed names defined per directory**

| directory | names |
|---|---|
| `src` | 2515 |
| `installatore/motore` | 714 |
| `banchi/15-suite` | 595 |
| `banchi/11-scatole` | 521 |
| `banchi/16-stress` | 263 |
| `banchi/rcp` | 229 |
| `banchi/09-b81-linea-morta.py` | 125 |
| `installatore/interfaccia` | 90 |
| `banchi/04-b31-tela.c` | 65 |
| `banchi/01-b3-cliente.py` | 52 |
| `banchi/19-android` | 48 |
| `banchi/06-b33-testimone.c` | 41 |
| `banchi/02-filo-fotogramma.py` | 38 |
| `banchi/19-vulkan` | 38 |
| `banchi/01-b4-validatore.py` | 36 |
| `banchi/02-cattura-fotogramma.c` | 36 |
| `banchi/09-b76-rete-cattiva.py` | 34 |
| `banchi/06-b5-esiti-cattura.c` | 32 |
| `banchi/09-b77-audio-riordino.py` | 32 |
| `banchi/02-filo-validatore.py` | 31 |
| `docs/sources` | 31 |
| `banchi/04-in8-misura.c` | 30 |
| `banchi/03-marca.py` | 28 |
| `banchi/12-client-veri.py` | 28 |
| `banchi/04-b25-tastiera.c` | 27 |
| `banchi/02-cattura-giudica.py` | 26 |
| `banchi/01-b0-bersaglio.sh` | 23 |
| `banchi/02-cattura-prodotto.c` | 22 |
| `banchi/18-software` | 21 |
| `banchi/13-w1-un-fotogramma.c` | 19 |
| `banchi/18-a1` | 18 |
| `banchi/01-b6-tetti.py` | 17 |
| `banchi/01-b7-congedo.py` | 17 |
| `banchi/02-codifica-immagine.py` | 17 |
| `banchi/01-b4-registrazioni.py` | 16 |
| `banchi/01-b8-prova-ban.c` | 16 |
| `banchi/18-scheda` | 16 |
| `banchi/07-b64-scena.py` | 15 |
| `banchi/10-f1-testimone.py` | 14 |
| `banchi/01-b8-lancia.sh` | 13 |
| `banchi/06-b33-risveglio-giudice.py` | 13 |
| `banchi/14-f1-forma.c` | 13 |
| `banchi/02-sessione-lancia.sh` | 12 |
| `banchi/06-b33-risveglio.c` | 12 |
| `banchi/01-b11-pagina.html` | 11 |
| `banchi/02-sessione-stato.py` | 11 |
| `banchi/04-b28-gesti.py` | 11 |
| `banchi/09-b84-audio-silenzio.py` | 10 |
| `banchi/01-b5-violazioni.py` | 9 |
| `banchi/01-s7-rotella.c` | 9 |
| `banchi/02-figlio-prova.py` | 9 |
| `banchi/02-pagina-sonda-codec.py` | 9 |
| `banchi/17-t7` | 9 |
| `banchi/01-b2-sonda-trasporto.py` | 8 |
| `banchi/01-b3-rcp-innesta.py` | 8 |
| `banchi/01-b7-lancia.sh` | 8 |
| `banchi/01-b9-letture.py` | 8 |
| `banchi/02-cattura-certifica.sh` | 8 |
| `banchi/attrezzi-gruppi-scheda.sh` | 8 |
| `banchi/02-pam-fermo.py` | 7 |
| `banchi/06-b33-terreno.sh` | 7 |
| `banchi/07-b64-orecchio.py` | 7 |
| `banchi/12-c20-veri.py` | 7 |
| `installatore/cmd` | 7 |
| `banchi/01-b2-lancia-wt.sh` | 6 |
| `banchi/02-filo-cliente.py` | 6 |
| `banchi/01-b0-terreno.sh` | 5 |
| `banchi/01-b11-guasto-innesta.py` | 5 |
| `banchi/01-b2-ngtcp2-wt-innesta.py` | 5 |
| `banchi/01-b2-sonda.html` | 5 |
| `banchi/17-distro` | 5 |
| `banchi/19-nvidia` | 5 |
| `banchi/00-sessione-gnome.sh` | 4 |
| `banchi/01-s7-pagina.html` | 4 |
| `banchi/02-codifica-lancia.sh` | 4 |
| `banchi/02-codifica-nal.py` | 4 |
| `banchi/04-b25-guasti.c` | 4 |
| `banchi/06-b34-tabella.c` | 4 |
| `banchi/07-b42-giudice.py` | 4 |
| `banchi/07-b64-rete.py` | 4 |
| `banchi/07-b65-datagram.py` | 4 |
| `banchi/01-b11-guasto.sh` | 3 |
| `banchi/01-b5-lancia.sh` | 3 |
| `banchi/01-b8-sblocca.py` | 3 |
| `banchi/02-figlio-accendi.sh` | 3 |
| `banchi/06-b33-risveglio-certifica.sh` | 3 |
| `banchi/06-b33-risveglio.sh` | 3 |
| `banchi/07-b46-marionette.py` | 3 |
| `banchi/09-b78-apertura.py` | 3 |
| `banchi/01-b11-lancia.sh` | 2 |
| `banchi/01-b2-costruisci.sh` | 2 |
| `banchi/01-b4-lancia.py` | 2 |
| `banchi/02-codifica-obu.py` | 2 |
| `banchi/02-pagina-misura-cdp.py` | 2 |
| `banchi/02-sessione-dispositivi.py` | 2 |
| `banchi/06-b33-risveglio-guasti.py` | 2 |
| `banchi/attrezzi-allinea-prodotto.sh` | 2 |
| `banchi/sonda` | 2 |
| `grafica` | 2 |
| `banchi/01-b0-bersaglio.py` | 1 |
| `banchi/01-b2-cliente-aioquic.py` | 1 |
| `banchi/01-b2-costruisci-ngtcp2.sh` | 1 |
| `banchi/01-b2-raccogli.py` | 1 |
| `banchi/01-casa-7448.sh` | 1 |
| `banchi/01-s7-raccogli.py` | 1 |
| `banchi/02-cattura-costruisci.sh` | 1 |
| `banchi/02-cattura-lancia.sh` | 1 |
| `banchi/02-codifica-prova.c` | 1 |
| `banchi/02-filo-lancia.sh` | 1 |
| `banchi/02-pam-i3.py` | 1 |
| `banchi/02-pam-lancia.sh` | 1 |
| `banchi/09-lucchetto.py` | 1 |
| `banchi/14-f1-forma.sh` | 1 |
| `banchi/17-t2` | 1 |
| `banchi/17-t9` | 1 |
| `banchi/attrezzi-allinea-innesto.sh` | 1 |
| `banchi/attrezzi-utenti.sh` | 1 |
| `packaging/archivio` | 1 |
| `packaging/rilascio.sh` | 1 |
| `packaging/rpm` | 1 |

### Every collision and how it was resolved

| target | old names | winner | others → | scopes (first) |
|---|---|---|---|---|
| `ADAPTER` | `ADATTATORE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ADMISSION` | `AMMISSIONE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `AREAS` | `AREE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ATTACHED` | `ATTACCATO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `TOOLS` | `ATTREZZI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Enable` | `Abilita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Previews` | `Anteprime` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Artifact` | `Artefatto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `BANDS` | `BANDE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `BINARY` | `BINARIO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SHORT` | `BREVI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ENVELOPE_MAX` | `BUSTA_MAX` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `DROPS` | `CADUTE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SAMPLE` | `CAMPIONE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `LOADS` | `CARICHI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `CATALOG` | `CATALOGO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `CELL` | `CELLA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `CYAN` | `CIANO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `COMMENT` | `COMMENTO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `CONSENT` | `CONSENSO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `COUNTER` | `CONTATORE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `COUNTS` | `CONTI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `BUILDER` | `COSTRUTTORE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Capabilities` | `Capacita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Certificate` | `Certificato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Certification` | `Certificazione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Commands` | `Comandi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Component` | `Componente` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Components` | `Componenti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Condition` | `Condizione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Knows` | `Conosce` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Consent` | `Consenso` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Count` | `Conto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DECODING` | `DECODIFICA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DIAGNOSIS` | `DIAGNOSI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DIARY` | `DIARIO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DECLARED` | `DICHIARATE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DISK` | `DISCO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DIFFERENT` | `DIVERSO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Repositories` | `Depositi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Derived` | `Derivate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Description` | `Descrizione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Detail` | `Dettaglio` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Depends` | `Dipende` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Disable` | `Disabilita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Questions` | `Domande` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `EIS_CAPABILITIES` | `EIS_CAPACITA` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `EXIT` | `ESCI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `EXCLUDED` | `ESCLUSE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `EXECUTED` | `ESEGUITO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `EXOTIC` | `ESOTICHE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `EXTERNAL` | `ESTERNO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `LBL` | `ETI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Excluded` | `Escluse` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Event` | `Evento` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `FAIL` | `FALLISCI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `FILTER` | `FILTRO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `FAKE` | `FINTE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SOURCES` | `FONTI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SENTENCE` | `FRASE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Facts` | `Fatti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Trusted` | `Fidati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Trust` | `Fiducia` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Source` | `Fonte` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Frame` | `Fotogramma` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Functions` | `Funzioni` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `TWIN` | `GEMELLA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `GESTURES` | `GESTI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DAY` | `GIORNO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ROUNDS` | `GIRI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `JUDGED` | `GIUDICATE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `GUARDIAN` | `GUARDIANO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `BROKEN` | `GUASTA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Severity` | `Gravita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `UNKNOWN` | `IGNOTO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `TRIGGER` | `INNESCO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `GRAFTS` | `INNESTI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `GRAFT` | `INNESTO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `OVERVIEW` | `INSIEME` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `HEADER` | `INTESTAZIONE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `AROUND` | `INTORNO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ISOLATION` | `ISOLAMENTO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Import` | `Importazione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Pending` | `InAttesa` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Addresses` | `Indirizzi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Installed` | `Installato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Installation` | `Installazione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `LIBRARIES` | `LIBRERIE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `FAR` | `LONTANO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Limits` | `Limiti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Matrix` | `Matrice` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Message` | `Messaggio` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Minimum` | `Minimo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Reasons` | `Motivi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `BIRTH` | `NASCITA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `NET` | `NETTO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `OUR` | `NOSTRE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `NEW` | `NUOVE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `NEW` | `NUOVI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Birth` | `Nascita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Nature` | `Natura` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `MANDATORY` | `OBBLIGATORI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `OPPOSITE` | `OPPOSTO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ORDER` | `ORDINE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ORIGINAL` | `ORIGINALE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `HOST` | `OSP` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Offer` | `Offerta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Operation` | `Operazione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `PAGES` | `PAGINE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `PANEL` | `PANNELLO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `PARTS` | `PARTI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DANGEROUS` | `PERICOLOSE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `PIECE` | `PEZZO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `CLAIM` | `PRETESA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `PROCESSES` | `PROCESSI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `PROGRAM` | `PROGRAMMA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `CLEAN` | `PULISCI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `People` | `Persone` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Default` | `Predefinito` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Take` | `Presa` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Main` | `Principale` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Product` | `Prodotto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Property` | `Proprieta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Provenance` | `Provenienza` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `QUIET` | `QUIETE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ENCLOSURES` | `RECINTI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `RULES` | `REGOLE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `RECIPE` | `RICETTA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `RECEIVED` | `RICEVUTE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `RENAMES` | `RINOMINA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `FALLBACKS` | `RIPIEGHI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `RESULT` | `RIS` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Recording` | `Registrazione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Regulator` | `Regolatore` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Reload` | `Ricarica` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Requested` | `Richiesto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Line` | `Riga` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Repair` | `Ripara` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `DRY` | `SECCO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SEQUENCE` | `SEQUENZA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SERVED` | `SERVITI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SERVER` | `SERVITORE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SESSIONS` | `SESSIONI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `EXPECTED_SECTIONS` | `SEZIONI_ATTESE` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `EXCEEDED` | `SFORATO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `FIX` | `SISTEMO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `SPECIAL` | `SPECIALI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `PRINTED` | `STAMPATE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `HISTORY` | `STORIA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `HISTORICAL` | `STORICO` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `STRIP` | `STRISCIA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Save` | `Salvataggio` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Unlock` | `Sblocca` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Expired` | `Scaduto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Screen` | `Schermata` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Signal` | `Segnale` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Sequence` | `Sequenza` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Serve` | `Servo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ActiveState` | `StatoAttivo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Supported` | `Supportato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `TERMINAL` | `TERMINALE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `HOLDS` | `TIENE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `KEEP` | `TIENI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Phone` | `Telefono` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Last` | `Ultimo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `VALIDATOR` | `VALIDATORE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `FORBIDDEN` | `VIETATE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `VIOLATIONS` | `VIOLAZIONI` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ENTRY` | `VOCE` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Old` | `Vecchia` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `Entry` | `Voce` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ZONE` | `ZONA` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `enabled` | `abilitato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `widen` | `allarga` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `surface_height` | `altezza_superficie` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `amber` | `ambra` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `admissions` | `ammissioni` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `still` | `ancora_li` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `annotated` | `annotata` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `anonymous` | `anonimi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `applied` | `applicati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `applications` | `applicazioni` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `arcs` | `archi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `tool` | `arnese` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `toplevel_listener` | `ascolto_fin` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stream_listener` | `ascolto_flusso` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `tool` | `attrezzo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `audio_silence` | `audio_silenzio` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `leftover` | `avanzo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `got` | `avuta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `got` | `avuti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `started` | `avviato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `wrapped` | `avvolta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `flags` | `bandiere` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `barriers` | `barriere` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `burn` | `bruc` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ugly` | `brutte` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ugly` | `brutti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `envelope` | `busta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `calibrate` | `calibra` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `trail` | `cammino` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `candidates` | `candidati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `canonical` | `canonico` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `capsule` | `capsula` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `loaded` | `caricate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `payload` | `carne` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `dirs` | `cartelle` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `chains` | `catene` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `bad` | `cattive` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `blind` | `ceco` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `searched` | `cercato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `called` | `chiamato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `asks` | `chieste` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `cited` | `citato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `classes` | `classi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `enc` | `codif` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `encoded` | `codificate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `coefficients` | `coefficienti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `links` | `collegamenti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `shots` | `colpi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `hit` | `colpiti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `overall` | `complessivo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `concurrent` | `concorrente` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `shared` | `condivisa` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `confirmed` | `confermati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `configure` | `configura` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `configured` | `configurata` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `compared` | `confrontate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `dismissed` | `congedate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `delivered` | `consegnate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `counts` | `conteggi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `tool_checks` | `controlli_dello_strumento` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `convert` | `converti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `script` | `copione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `created` | `creati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `credential` | `credenziale` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `growth` | `cresc` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `grows` | `cresce` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `cursors` | `cursori` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `cushion` | `cusc` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `describe` | `descrivi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `description` | `descrizione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `said` | `detta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stock` | `diSerie` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `per_session` | `di_sessione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `broadcast` | `diffusi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `tell` | `dilo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `direction` | `direzione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `descendants` | `discendenti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `divergent` | `divergente` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `duplicate` | `doppie` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `due` | `dovuti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `effective` | `effettivo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `element` | `elemento` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `ri` | `erre` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `exec` | `esec` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `foreign` | `estraneo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `failed_t` | `falliti_t` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `families` | `famiglie` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `factor` | `fatt` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stop` | `fermare` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stopped` | `fermate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `trusted` | `fidati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `finish` | `finisci` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `leaf` | `foglia` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `memory_format` | `formato_memoria` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `spa_format` | `formato_spa` | (forbidden: C name onto a libc/glib/system symbol) | **kept** | |
| `fragment` | `frammento` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `fresh` | `fresco` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `future` | `futuri` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `legs` | `gambe` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `new_generation` | `generazione_nuova` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `already_seen` | `gia_vista` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `judgeable` | `giudicabili` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `judging` | `giudicanti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `joints` | `giunti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `recoveries` | `guarigioni` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `shell` | `guscio` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `identifier` | `identificativo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `still` | `immobili` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `immutable` | `immutabile` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `listening` | `inAscolto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `incoming` | `in_arrivo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `queued` | `in_coda` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `realtime` | `in_tempo_reale` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `idle` | `inatt` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `embed` | `incastona` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `indirect` | `indirette` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `zoom_in` | `ingrandisci` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `initialized` | `inizializzato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `insecure` | `insicuri` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `interesting` | `interessanti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `internal` | `interna` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `interpret` | `interpreta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `sw` | `interr` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `intent` | `intz` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `intruder` | `invasore` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `invert` | `inverti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `irreversible` | `irreversibili` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `instants` | `istanti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `blink` | `lampeggio` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `launched` | `lanciate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `wid` | `larg` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `surface_width` | `larghezza_superficie` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `slabs` | `lastre` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `slowness` | `lentezza` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `linear` | `lineare` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `level_idc` | `livello_idc` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `dist` | `lontananza` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `luminances` | `luminanze` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `malformed` | `malformate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `masks` | `maschere` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `total_median` | `mediana_totale` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `member` | `membro` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `shuffled` | `mescola` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `jobs` | `mestieri` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `metadata` | `metadato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `best` | `migliori` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `sender` | `mittente` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `rate_control` | `modo_rc` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `mounted` | `montati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `dead` | `morti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `die` | `muori` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `nanoseconds` | `nanosecondi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `grandchild` | `nipote` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stretch_name` | `nome_tratto` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `nominal` | `nominale` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `non_black` | `non_nero` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `news` | `novita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `offer` | `offri` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `opaque` | `opachi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `sorted` | `ordinata` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `sorted` | `ordinate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `sorted` | `ordinati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `orphan` | `orfane` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `rotate` | `orienta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stubborn` | `ostinati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `got_n` | `otten` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `obtained` | `ottenuti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `pkt` | `pac` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `bundle` | `pacco` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `parents` | `padri` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `owner` | `padrone` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `panels` | `pannelli` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `lxqt_panel` | `pannello_lxqt` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stride2` | `passo2` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stride_u` | `passo_u` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stride_uv` | `passo_uv` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stride_v` | `passo_v` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `slope` | `pendenza` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `paths` | `percorsi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `lost` | `perduti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `lost` | `perse` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `weights` | `pesi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `flat` | `piatto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `peaks` | `picchi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `pool` | `piscina` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `lowest` | `piu_bassa` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `slowest` | `piu_lenta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `slower` | `piu_lento` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `newest` | `piu_nuovo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `total_pixels` | `pixel_totali` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `pump` | `pompa` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `positional` | `posizionali` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `preferred` | `preferito` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `prefixes` | `prefissi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `prepare` | `preparati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `claim` | `pretesa` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `claims` | `pretese` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `estimate` | `preventivo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `foreseen` | `previsti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `priority` | `priorita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `scheduled` | `programmate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `string_property` | `proprieta_stringa` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `published` | `pubblicato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `purities` | `purezze` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `collection` | `raccolta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `leftovers` | `residui` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `rectangle` | `rettangolo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `rebuilt` | `ricostruite` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `refused` | `rifiutate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `command_line` | `riga_comando` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `remount` | `rimonta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `reborn` | `rinasce` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `reborn` | `rinata` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `reborn` | `rinato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `restart` | `ripartenza` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `restarts` | `ripartenze` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `repeatable` | `ripetibile` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `retries` | `riprove` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `cleaned` | `ripulita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `result` | `ris` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `healed` | `risanati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `resp` | `risp` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stuff` | `roba` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `robust` | `robusta` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `broken` | `rotte` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `greeting` | `saluto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `screensaver` | `salvaschermo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `saved` | `salvate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `mistakes` | `sbagli` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `exp` | `scad` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `expired` | `scaduti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `swapped` | `scambiate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `discarded` | `scartate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `triggered` | `scattate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `choose` | `scegli` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `disconnected` | `scollegate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `unknown` | `sconosciute` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `uncovered` | `scoperti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `discover` | `scopri` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `seat_id` | `sede` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `segment` | `segmento` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `tight` | `serrate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `sess` | `ses` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `flicker` | `sfarfallio` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `evicted` | `sfrattata` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `scar` | `sfregia` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `gradient` | `sfum` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `acronyms` | `sigle` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `symbol` | `simbolo` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `sync` | `sincronizza` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `fixed` | `sistemati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `refuted` | `smentite` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `dispatch` | `smista` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `dispatcher` | `smistatore` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `summary` | `sommario` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `sums` | `somme` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `probes` | `sonde` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `replace` | `sostituisci` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `substitute` | `sostituto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `subscription` | `sottoscrizione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `overwritten` | `sovrascritti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `dirty` | `sporca` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `dirty` | `sporche` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `endpoint` | `sportello` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `shift` | `spost` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `moved` | `spostati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `printable` | `stampabile` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `estimate` | `stima` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `wrong` | `storti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stream_blocked` | `stream_bloccato` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `tight` | `strette` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stride_map` | `stride_mappa` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `throttle` | `stroz` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `throttled` | `strozzato` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `suggest` | `suggerisci` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `digest` | `sunto` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `survivor` | `superstite` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `t_exit` | `t_esci` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `cuts` | `tagli` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `many` | `tanti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `kbd` | `tas` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `canvases` | `telate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `themes` | `temi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `tiles` | `tessere` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `heads` | `teste` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `keepalive` | `tienila_viva` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `memory_type` | `tipo_memoria` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `touch` | `tocc` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `touches` | `tocchi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `removed` | `tolte` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `tone_enc` | `tono_cod` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `tone_i` | `tono_i` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `tone_next_us` | `tono_prossimo_us` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `returned` | `tornate` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `overflowed` | `traboccati` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `except` | `tranne` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `transitions` | `transizioni` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `elapsed` | `trascorsi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `elapsed` | `trascorso` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `transform` | `trasformazione` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `transparent` | `trasparenti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `stretches_sample` | `tratti_campione` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretches_compare` | `tratti_confronta` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretches_logged_us` | `tratti_detto_us` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretches_names` | `tratti_nomi` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretches_next` | `tratti_prossimo` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretches_n` | `tratti_quanti` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretches_without_pts` | `tratti_senza_pts` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretches_total` | `tratti_totale` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretches_seen` | `tratti_visti` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `stretch_of` | `tratto_di` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `too_many_blocked` | `troppi_bloccati` | (forbidden: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) | **kept** | |
| `one_line` | `una_riga` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `usr` | `ute` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `useful` | `utili` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `visit` | `visita` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `victims` | `vittime` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `vocabulary` | `vocabolario` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `volumes` | `volumi` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `empty` | `vuote` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `empty` | `vuoti` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `silence` | `zittisci` | (forbidden: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) | **kept** | |
| `app_requested` | `app_chiesti`, `app_chiesto` | `app_chiesto` | `app_chiesti`→`app_asked` | tu:banchi/rcp/rcp.c; tu:banchi/rcp/rcp.c |
| `my_base` | `mia_base`, `mio_base` | `mio_base` | `mia_base`→`own_base` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py; py:banchi/11-scatole/11-c2-una-finestra-si-apre.py |
| `now_ms` | `adesso_ms`, `ora_ms` | `ora_ms` | `adesso_ms`→`current_ms` | tu:src/figlio.c; tu:src/figlio.c |
| `Annotated` | `Annotata` | (unresolved: twin annotata is not renamed) | **kept** | |
| `Indirect` | `Indirette` | (unresolved: twin indirette is not renamed) | **kept** | |
| `Member` | `Membro` | (unresolved: twin membro is not renamed) | **kept** | |
| `Sorted` | `Ordinate` | (unresolved: twin ordinate is not renamed) | **kept** | |
| `Endpoint` | `Sportello` | (unresolved: twin sportello is not renamed) | **kept** | |

### One new name for several old names, never in one scope (checked per scope, §3)

- `IN_EFFECT` ← `IN_VIGORE`, `VIG`
- `_path` ← `_cammino`, `_perc`
- `app_log` ← `app_diario`, `registro_applicazione`
- `app_received` ← `app_ricevuti`, `app_ricevuto`
- `expected_s` ← `att_s`, `previsti_s`
- `expected_v` ← `att_v`, `atteso_v`
- `next_ingress` ← `prossima_ingresso`, `prossimo_ingresso`
- `next_serial` ← `prossima_matricola`, `prossimo_serial`
- `read_notebook` ← `leggi_il_quaderno`, `leggi_quaderno`
- `read_text` ← `leggi_il_testo`, `leggi_testo`
- `requested_height` ← `chiesta_altezza`, `chiesto_altezza`
- `requested_width` ← `chiesta_larghezza`, `chiesto_larghezza`
- `search_window` ← `cerca_finestra`, `cerca_la_finestra`
- `test_still_scene` ← `collauda_la_scena_ferma`, `prova_scena_ferma`
- `turn_off_server` ← `spegni_server`, `spegni_servitore`
- `unwanted` ← `di_troppo`, `non_ci_vuole`
- `wait_canvas` ← `aspetta_tela`, `attendi_tela`
- `wait_line` ← `aspetta_la_riga`, `aspetta_riga`

### Names not renamed (to resolve in interi.tsv or sinonimi.tsv)

- `ADATTATORE` — target ADAPTER is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `AMMISSIONE` — target ADMISSION is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `AREE` — target AREAS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ATTACCATO` — target ATTACHED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ATTREZZI` — target TOOLS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Abilita` — target Enable is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Annotata` — twin annotata is not renamed
- `Anteprime` — target Previews is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Artefatto` — target Artifact is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `BANDE` — target BANDS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `BINARIO` — target BINARY is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `BREVI` — target SHORT is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `BUSTA_MAX` — target ENVELOPE_MAX is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `CADUTE` — target DROPS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `CAMPIONE` — target SAMPLE is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `CARICHI` — target LOADS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `CATALOGO` — target CATALOG is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `CELLA` — target CELL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `CIANO` — target CYAN is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `COMMENTO` — target COMMENT is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `CONSENSO` — target CONSENT is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `CONTATORE` — target COUNTER is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `CONTI` — target COUNTS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `COSTRUTTORE` — target BUILDER is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Capacita` — target Capabilities is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Certificato` — target Certificate is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Certificazione` — target Certification is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Comandi` — target Commands is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Componente` — target Component is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Componenti` — target Components is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Condizione` — target Condition is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Conosce` — target Knows is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Consenso` — target Consent is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Conto` — target Count is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `DECODIFICA` — target DECODING is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `DIAGNOSI` — target DIAGNOSIS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `DIARIO` — target DIARY is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `DICHIARATE` — target DECLARED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `DISCO` — target DISK is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `DIVERSO` — target DIFFERENT is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Depositi` — target Repositories is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Derivate` — target Derived is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Descrizione` — target Description is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Dettaglio` — target Detail is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Dipende` — target Depends is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Disabilita` — target Disable is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Domande` — target Questions is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `EIS_CAPACITA` — target EIS_CAPABILITIES is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `ESCI` — target EXIT is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ESCLUSE` — target EXCLUDED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ESEGUITO` — target EXECUTED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ESOTICHE` — target EXOTIC is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ESTERNO` — target EXTERNAL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ETI` — target LBL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Escluse` — target Excluded is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Evento` — target Event is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `FALLISCI` — target FAIL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `FILTRO` — target FILTER is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `FINTE` — target FAKE is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `FONTI` — target SOURCES is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `FRASE` — target SENTENCE is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Fatti` — target Facts is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Fidati` — target Trusted is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Fiducia` — target Trust is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Fonte` — target Source is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Fotogramma` — target Frame is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Funzioni` — target Functions is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `GEMELLA` — target TWIN is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `GESTI` — target GESTURES is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `GIORNO` — target DAY is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `GIRI` — target ROUNDS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `GIUDICATE` — target JUDGED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `GUARDIANO` — target GUARDIAN is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `GUASTA` — target BROKEN is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Gravita` — target Severity is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `IGNOTO` — target UNKNOWN is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `INNESCO` — target TRIGGER is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `INNESTI` — target GRAFTS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `INNESTO` — target GRAFT is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `INSIEME` — target OVERVIEW is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `INTESTAZIONE` — target HEADER is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `INTORNO` — target AROUND is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ISOLAMENTO` — target ISOLATION is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Importazione` — target Import is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `InAttesa` — target Pending is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Indirette` — twin indirette is not renamed
- `Indirizzi` — target Addresses is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Installato` — target Installed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Installazione` — target Installation is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `LIBRERIE` — target LIBRARIES is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `LONTANO` — target FAR is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Limiti` — target Limits is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Matrice` — target Matrix is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Membro` — twin membro is not renamed
- `Messaggio` — target Message is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Minimo` — target Minimum is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Motivi` — target Reasons is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `NASCITA` — target BIRTH is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `NETTO` — target NET is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `NOSTRE` — target OUR is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `NUOVE` — target NEW is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `NUOVI` — target NEW is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Nascita` — target Birth is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Natura` — target Nature is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `OBBLIGATORI` — target MANDATORY is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `OPPOSTO` — target OPPOSITE is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ORDINE` — target ORDER is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ORIGINALE` — target ORIGINAL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `OSP` — target HOST is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Offerta` — target Offer is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Operazione` — target Operation is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Ordinate` — twin ordinate is not renamed
- `PAGINE` — target PAGES is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `PANNELLO` — target PANEL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `PARTI` — target PARTS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `PERICOLOSE` — target DANGEROUS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `PEZZO` — target PIECE is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `PRETESA` — target CLAIM is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `PROCESSI` — target PROCESSES is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `PROGRAMMA` — target PROGRAM is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `PULISCI` — target CLEAN is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Persone` — target People is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Predefinito` — target Default is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Presa` — target Take is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Principale` — target Main is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Prodotto` — target Product is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Proprieta` — target Property is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Provenienza` — target Provenance is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `QUIETE` — target QUIET is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `RECINTI` — target ENCLOSURES is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `REGOLE` — target RULES is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `RICETTA` — target RECIPE is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `RICEVUTE` — target RECEIVED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `RINOMINA` — target RENAMES is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `RIPIEGHI` — target FALLBACKS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `RIS` — target RESULT is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Registrazione` — target Recording is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Regolatore` — target Regulator is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Ricarica` — target Reload is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Richiesto` — target Requested is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Riga` — target Line is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Ripara` — target Repair is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `SECCO` — target DRY is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `SEQUENZA` — target SEQUENCE is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `SERVITI` — target SERVED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `SERVITORE` — target SERVER is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `SESSIONI` — target SESSIONS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `SEZIONI_ATTESE` — target EXPECTED_SECTIONS is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `SFORATO` — target EXCEEDED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `SISTEMO` — target FIX is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `SPECIALI` — target SPECIAL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `STAMPATE` — target PRINTED is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `STORIA` — target HISTORY is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `STORICO` — target HISTORICAL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `STRISCIA` — target STRIP is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Salvataggio` — target Save is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Sblocca` — target Unlock is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Scaduto` — target Expired is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Schermata` — target Screen is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Segnale` — target Signal is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Sequenza` — target Sequence is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Servo` — target Serve is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Sportello` — twin sportello is not renamed
- `StatoAttivo` — target ActiveState is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Supportato` — target Supported is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `TERMINALE` — target TERMINAL is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `TIENE` — target HOLDS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `TIENI` — target KEEP is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Telefono` — target Phone is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Ultimo` — target Last is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `VALIDATORE` — target VALIDATOR is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `VIETATE` — target FORBIDDEN is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `VIOLAZIONI` — target VIOLATIONS is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `VOCE` — target ENTRY is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Vecchia` — target Old is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `Voce` — target Entry is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ZONA` — target ZONE is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `abilitato` — target enabled is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `allarga` — target widen is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `altezza_superficie` — target surface_height is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ambra` — target amber is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ammissioni` — target admissions is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ancora_li` — target still is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `annotata` — target annotated is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `anonimi` — target anonymous is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `applicati` — target applied is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `applicazioni` — target applications is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `archi` — target arcs is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `arnese` — target tool is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ascolto_fin` — target toplevel_listener is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `ascolto_flusso` — target stream_listener is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `attrezzo` — target tool is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `audio_silenzio` — target audio_silence is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `avanzo` — target leftover is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `avuta` — target got is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `avuti` — target got is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `avviato` — target started is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `avvolta` — target wrapped is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `bandiere` — target flags is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `barriere` — target barriers is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `bruc` — target burn is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `brutte` — target ugly is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `brutti` — target ugly is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `busta` — target envelope is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `calibra` — target calibrate is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `cammino` — target trail is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `candidati` — target candidates is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `canonico` — target canonical is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `capsula` — target capsule is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `caricate` — target loaded is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `carne` — target payload is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `cartelle` — target dirs is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `catene` — target chains is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `cattive` — target bad is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ceco` — target blind is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `cercato` — target searched is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `chiamato` — target called is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `chieste` — target asks is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `citato` — target cited is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `classi` — target classes is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `codif` — target enc is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `codificate` — target encoded is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `coefficienti` — target coefficients is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `collegamenti` — target links is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `colpi` — target shots is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `colpiti` — target hit is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `complessivo` — target overall is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `concorrente` — target concurrent is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `condivisa` — target shared is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `confermati` — target confirmed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `configura` — target configure is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `configurata` — target configured is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `confrontate` — target compared is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `congedate` — target dismissed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `consegnate` — target delivered is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `conteggi` — target counts is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `controlli_dello_strumento` — target tool_checks is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `converti` — target convert is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `copione` — target script is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `creati` — target created is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `credenziale` — target credential is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `cresc` — target growth is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `cresce` — target grows is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `cursori` — target cursors is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `cusc` — target cushion is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `descrivi` — target describe is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `descrizione` — target description is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `detta` — target said is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `diSerie` — target stock is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `di_sessione` — target per_session is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `diffusi` — target broadcast is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `dilo` — target tell is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `direzione` — target direction is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `discendenti` — target descendants is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `divergente` — target divergent is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `doppie` — target duplicate is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `dovuti` — target due is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `effettivo` — target effective is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `elemento` — target element is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `erre` — target ri is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `esec` — target exec is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `estraneo` — target foreign is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `falliti_t` — target failed_t is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `famiglie` — target families is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `fatt` — target factor is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `fermare` — target stop is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `fermate` — target stopped is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `fidati` — target trusted is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `finisci` — target finish is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `foglia` — target leaf is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `formato_memoria` — target memory_format is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `formato_spa` — target spa_format is a C name onto a libc/glib/system symbol
- `frammento` — target fragment is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `fresco` — target fresh is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `futuri` — target future is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `gambe` — target legs is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `generazione_nuova` — target new_generation is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `gia_vista` — target already_seen is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `giudicabili` — target judgeable is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `giudicanti` — target judging is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `giunti` — target joints is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `guarigioni` — target recoveries is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `guscio` — target shell is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `identificativo` — target identifier is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `immobili` — target still is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `immutabile` — target immutable is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `inAscolto` — target listening is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `in_arrivo` — target incoming is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `in_coda` — target queued is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `in_tempo_reale` — target realtime is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `inatt` — target idle is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `incastona` — target embed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `indirette` — target indirect is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ingrandisci` — target zoom_in is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `inizializzato` — target initialized is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `insicuri` — target insecure is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `interessanti` — target interesting is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `interna` — target internal is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `interpreta` — target interpret is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `interr` — target sw is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `intz` — target intent is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `invasore` — target intruder is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `inverti` — target invert is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `irreversibili` — target irreversible is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `istanti` — target instants is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `lampeggio` — target blink is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `lanciate` — target launched is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `larg` — target wid is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `larghezza_superficie` — target surface_width is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `lastre` — target slabs is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `lentezza` — target slowness is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `lineare` — target linear is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `livello_idc` — target level_idc is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `lontananza` — target dist is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `luminanze` — target luminances is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `malformate` — target malformed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `maschere` — target masks is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `mediana_totale` — target total_median is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `membro` — target member is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `mescola` — target shuffled is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `mestieri` — target jobs is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `metadato` — target metadata is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `migliori` — target best is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `mittente` — target sender is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `modo_rc` — target rate_control is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `montati` — target mounted is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `morti` — target dead is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `muori` — target die is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `nanosecondi` — target nanoseconds is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `nipote` — target grandchild is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `nome_tratto` — target stretch_name is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `nominale` — target nominal is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `non_nero` — target non_black is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `novita` — target news is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `offri` — target offer is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `opachi` — target opaque is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ordinata` — target sorted is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ordinate` — target sorted is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ordinati` — target sorted is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `orfane` — target orphan is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `orienta` — target rotate is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ostinati` — target stubborn is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `otten` — target got_n is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ottenuti` — target obtained is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `pac` — target pkt is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `pacco` — target bundle is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `padri` — target parents is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `padrone` — target owner is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `pannelli` — target panels is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `pannello_lxqt` — target lxqt_panel is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `passo2` — target stride2 is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `passo_u` — target stride_u is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `passo_uv` — target stride_uv is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `passo_v` — target stride_v is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `pendenza` — target slope is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `percorsi` — target paths is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `perduti` — target lost is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `perse` — target lost is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `pesi` — target weights is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `piatto` — target flat is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `picchi` — target peaks is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `piscina` — target pool is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `piu_bassa` — target lowest is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `piu_lenta` — target slowest is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `piu_lento` — target slower is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `piu_nuovo` — target newest is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `pixel_totali` — target total_pixels is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `pompa` — target pump is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `posizionali` — target positional is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `preferito` — target preferred is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `prefissi` — target prefixes is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `preparati` — target prepare is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `pretesa` — target claim is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `pretese` — target claims is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `preventivo` — target estimate is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `previsti` — target foreseen is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `priorita` — target priority is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `programmate` — target scheduled is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `proprieta_stringa` — target string_property is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `pubblicato` — target published is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `purezze` — target purities is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `raccolta` — target collection is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `residui` — target leftovers is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `rettangolo` — target rectangle is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ricostruite` — target rebuilt is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `rifiutate` — target refused is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `riga_comando` — target command_line is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `rimonta` — target remount is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `rinasce` — target reborn is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `rinata` — target reborn is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `rinato` — target reborn is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ripartenza` — target restart is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ripartenze` — target restarts is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ripetibile` — target repeatable is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `riprove` — target retries is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ripulita` — target cleaned is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ris` — target result is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `risanati` — target healed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `risp` — target resp is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `roba` — target stuff is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `robusta` — target robust is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `rotte` — target broken is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `saluto` — target greeting is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `salvaschermo` — target screensaver is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `salvate` — target saved is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sbagli` — target mistakes is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scad` — target exp is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scaduti` — target expired is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scambiate` — target swapped is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scartate` — target discarded is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scattate` — target triggered is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scegli` — target choose is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scollegate` — target disconnected is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sconosciute` — target unknown is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scoperti` — target uncovered is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `scopri` — target discover is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sede` — target seat_id is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `segmento` — target segment is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `serrate` — target tight is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ses` — target sess is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sfarfallio` — target flicker is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sfrattata` — target evicted is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sfregia` — target scar is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sfum` — target gradient is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sigle` — target acronyms is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `simbolo` — target symbol is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sincronizza` — target sync is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sistemati` — target fixed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `smentite` — target refuted is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `smista` — target dispatch is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `smistatore` — target dispatcher is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sommario` — target summary is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `somme` — target sums is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sonde` — target probes is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sostituisci` — target replace is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sostituto` — target substitute is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sottoscrizione` — target subscription is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sovrascritti` — target overwritten is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sporca` — target dirty is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sporche` — target dirty is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sportello` — target endpoint is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `spost` — target shift is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `spostati` — target moved is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `stampabile` — target printable is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `stima` — target estimate is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `storti` — target wrong is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `stream_bloccato` — target stream_blocked is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `strette` — target tight is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `stride_mappa` — target stride_map is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `stroz` — target throttle is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `strozzato` — target throttled is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `suggerisci` — target suggest is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `sunto` — target digest is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `superstite` — target survivor is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `t_esci` — target t_exit is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tagli` — target cuts is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tanti` — target many is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tas` — target kbd is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `telate` — target canvases is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `temi` — target themes is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tessere` — target tiles is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `teste` — target heads is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tienila_viva` — target keepalive is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tipo_memoria` — target memory_type is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tocc` — target touch is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tocchi` — target touches is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tolte` — target removed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tono_cod` — target tone_enc is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tono_i` — target tone_i is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tono_prossimo_us` — target tone_next_us is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tornate` — target returned is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `traboccati` — target overflowed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tranne` — target except is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `transizioni` — target transitions is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `trascorsi` — target elapsed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `trascorso` — target elapsed is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `trasformazione` — target transform is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `trasparenti` — target transparent is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `tratti_campione` — target stretches_sample is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratti_confronta` — target stretches_compare is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratti_detto_us` — target stretches_logged_us is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratti_nomi` — target stretches_names is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratti_prossimo` — target stretches_next is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratti_quanti` — target stretches_n is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratti_senza_pts` — target stretches_without_pts is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratti_totale` — target stretches_total is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratti_visti` — target stretches_seen is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `tratto_di` — target stretch_of is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `troppi_bloccati` — target too_many_blocked is a C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)
- `una_riga` — target one_line is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `ute` — target usr is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `utili` — target useful is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `visita` — target visit is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `vittime` — target victims is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `vocabolario` — target vocabulary is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `volumi` — target volumes is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `vuote` — target empty is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `vuoti` — target empty is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)
- `zittisci` — target silence is a the new name occurs in text the tool does not rename (strings, documents, data, shell words)

### Phase A: frozen names, by reason (each name under the first reason found; every name and its reason: rinomina2-plan.json → excluded)

| reason | names |
|---|---|
| py string literal | 1242 |
| document | 1090 |
| data file | 967 |
| Python file that reads names at run time | 321 |
| a name a file builds at run time from a literal piece | 251 |
| shell word that is not a reference | 190 |
| a history source compiled with today's code | 190 |
| shell: functions of a file that runs a command named by a variable | 168 |
| Python class or function name printed through __name__ | 160 |
| shell: ${X:-…} on an upper-case name, an input from the environment | 149 |
| conf file | 123 |
| c string literal | 89 |
| html string literal | 64 |
| JavaScript property name | 53 |
| JavaScript object key or shorthand property | 53 |
| Go field without a JSON name: the key is the field | 50 |
| shell file shfmt cannot parse | 34 |
| REMOTIX_*/RX_* environment variable | 22 |
| Python class name printed through repr/%r/a traceback | 14 |
| go string literal | 12 |
| a file or directory name of the tree | 8 |
| Python keyword argument that becomes data or goes to someone else's function | 8 |
| C argument of a macro that stringifies or pastes it | 7 |
| make file | 6 |
| Python exception class: its name is printed by tracebacks, repr and type | 5 |
| shell: read but never assigned in the tree, an input from the environment | 4 |
| a shader source | 4 |
| C function whose name reaches the binary | 3 |
| json file | 2 |
| shell local -n | 1 |

### Phase A: fallback names (collision alternates and dodge suffixes) — all internal

| old | new | languages | how |
|---|---|---|---|
| `ATT` | `EXP` | sh | sinonimi.tsv: att → exp (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `ATTESO_NO` | `AWAITED_NO` | c | sinonimi.tsv: atteso → awaited (target was: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) |
| `ATTESO_PRODUCIBILE` | `AWAITED_PRODUCIBLE` | c | sinonimi.tsv: atteso → awaited (target was: C name in a reserved family (str*, mem*, wcs*, is*, to*, E*, SIG*, _X)) |
| `Acceso` | `Lit` | go | sinonimi.tsv: acceso → lit (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Aggiungi` | `Insert` | go | sinonimi.tsv: aggiungi → insert (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Atteso` | `Awaited` | c | sinonimi.tsv: atteso → awaited (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Avvia` | `Launch` | go | sinonimi.tsv: avvia → launch (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `CODICI` | `CODE_LIST` | py | sinonimi.tsv: codici → code_list (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `COLONNE` | `COLS` | py | sinonimi.tsv: colonne → cols (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `CONDIZIONI` | `CONDS` | go | sinonimi.tsv: condizioni → conds (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `CONGELATO` | `FROZEN_V` | py | sinonimi.tsv: congelato → frozen_v (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Chiama` | `Invoke` | go | sinonimi.tsv: chiama → invoke (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Chiave` | `KeyId` | go | sinonimi.tsv: chiave → key_id (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Controlli` | `Verifications` | go | sinonimi.tsv: controlli → verifications (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Creato` | `Made` | go | sinonimi.tsv: creato → made (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `DESTRA` | `RIGHT_SIDE` | py | sinonimi.tsv: destra → right_side (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `ESEGUI` | `EXECUTE` | sh | sinonimi.tsv: esegui → execute (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Elenco` | `Listing` | go | sinonimi.tsv: elenco → listing (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Esclusa` | `LeftOut` | go | sinonimi.tsv: esclusa → left_out (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `FLUSSO` | `FLOW` | sh | sinonimi.tsv: flusso → flow (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Grafica` | `Gfx` | go | sinonimi.tsv: grafica → gfx (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Grafici` | `Charts` | go | sinonimi.tsv: grafici → charts (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Livello` | `Lvl` | go | sinonimi.tsv: livello → lvl (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `MANCANO` | `LACKING` | sh | sinonimi.tsv: mancano → lacking (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `MARGINE` | `HEADROOM` | py | sinonimi.tsv: margine → headroom (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Metti` | `Place` | go | sinonimi.tsv: metti → place (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `NuovaSessione` | `FreshSession` | go | sinonimi.tsv: nuova → fresh (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Oggetto` | `Obj` | go | sinonimi.tsv: oggetto → obj (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `POLITICA` | `POLICY_V` | py | sinonimi.tsv: politica → policy_v (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Palco` | `StageV` | c | sinonimi.tsv: palco → stage_v (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Passo` | `Stride` | go | sinonimi.tsv: passo → stride (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Percorso` | `RoutePath` | go | sinonimi.tsv: percorso → route_path (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Piattaforma` | `PlatformV` | go | sinonimi.tsv: piattaforma → platform_v (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Profilo` | `ProfileV` | c,go | sinonimi.tsv: profilo → profile_v (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `RESA` | `RENDERED` | sh | sinonimi.tsv: resa → rendered (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `RIFERIMENTO` | `REF` | py | sinonimi.tsv: riferimento → ref (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `SANI` | `SOUND_OK` | sh | sinonimi.tsv: sani → sound_ok (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `SENTINELLA` | `SENTINEL_V` | py | sinonimi.tsv: sentinella → sentinel_v (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `SERRATURA` | `LOCK_V` | py | sinonimi.tsv: serratura → lock_v (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `SINISTRA` | `LEFT_SIDE` | py | sinonimi.tsv: sinistra → left_side (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Scheda` | `GpuCard` | go | sinonimi.tsv: scheda → gpu_card (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Scritto` | `Wrote` | go | sinonimi.tsv: scritto → wrote (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `TASTI` | `KEY_LIST` | py | sinonimi.tsv: tasti → key_list (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `TROVATO` | `LOCATED` | sh | sinonimi.tsv: trovato → located (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `ULTIMI` | `LATEST` | c | sinonimi.tsv: ultimi → latest (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Uscita` | `OutDir` | c | sinonimi.tsv: uscita → out_dir (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `VISTI` | `SEEN_N` | py | sinonimi.tsv: visti → seen_n (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Valore` | `Val` | go | sinonimi.tsv: valore → val (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Versione` | `Ver` | c,go | sinonimi.tsv: versione → ver (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `Versioni` | `Vers` | go | sinonimi.tsv: versioni → vers (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `_libero` | `_available` | py | sinonimi.tsv: libero → available (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `adesso_ms` | `current_ms` | c,html | sinonimi.tsv: adesso → current (lost now_ms to ora_ms) |
| `app_chiesti` | `app_asked` | c,py | sinonimi.tsv: chiesti → asked (lost app_requested to app_chiesto) |
| `campionatore` | `sampler_obj` | c,py | sinonimi.tsv: campionatore → sampler_obj (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `ci_vuole` | `required_cmd` | py | interi.tsv |
| `copia_col_danno` | `duplicate_with_damage` | c | sinonimi.tsv: copia → duplicate (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `disposizione_nell_elenco` | `layout_in_list` | c | vocabulary |
| `dt_lista` | `dt_list` | py | vocabulary |
| `elenco_client` | `client_list` | c | interi.tsv |
| `elenco_dichiarato` | `declared_list` | py | interi.tsv |
| `elenco_file` | `file_list` | py | interi.tsv |
| `esclusi_lista` | `excluded_list` | py | vocabulary |
| `go_testo` | `go_content` | py | sinonimi.tsv: testo → content (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `ha_elenco` | `has_list` | py | vocabulary |
| `in_memoria` | `in_mem` | c | sinonimi.tsv: memoria → mem (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `liberi` | `free_n` | c | interi.tsv |
| `mia_base` | `own_base` | py | sinonimi.tsv: mia → own (lost my_base to mio_base) |
| `mouse_muovi` | `mouse_shift` | py | sinonimi.tsv: muovi → shift (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `pendenti` | `outstanding` | py | sinonimi.tsv: pendenti → outstanding (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `per_nome` | `per_label_name` | py | sinonimi.tsv: nome → label_name (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `rileggi` | `reread_cmd` | c | interi.tsv |
| `rinate` | `reborn_n` | py | interi.tsv |
| `scrivi_pkt` | `put_out_pkt` | c | sinonimi.tsv: scrivi → put_out (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `sessione_bus` | `sess_bus` | c | sinonimi.tsv: sessione → sess (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `sorg` | `source_dir` | c,sh | sinonimi.tsv: sorg → source_dir (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `tardo` | `belated` | py | sinonimi.tsv: tardo → belated (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `tastiera_disposizione` | `kbd_layout` | c | sinonimi.tsv: tastiera → kbd (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `trasf` | `xform` | c,html | sinonimi.tsv: trasf → xform (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `tubo` | `pipe_fd` | c | sinonimi.tsv: tubo → pipe_fd (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `tutto_zero` | `everything_zero` | c | sinonimi.tsv: tutto → everything (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `un_accesso` | `a_access` | py | sinonimi.tsv: un → a (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `un_fotogramma` | `a_frame` | c | sinonimi.tsv: un → a (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `un_inquilino` | `a_tenant` | py | sinonimi.tsv: un → a (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |
| `wl_copia` | `wl_duplicate` | py | sinonimi.tsv: copia → duplicate (target was: the new name occurs in text the tool does not rename (strings, documents, data, shell words)) |

### Names left out on purpose (other than frozen)

- `NID_subject_alt_name` — defined outside the project (C headers)
- `OPUS_SET_PACKET_LOSS_PERC` — defined outside the project (C headers)
- `locale_t` — defined outside the project (C headers)

### Cross-language contracts (every place: rinomina2-plan.json → contracts)

| kind | names |
|---|---|
| crosses languages | 59 |

The names below are the ones another program reads by spelling: data names, environment variables, options and kebab names.  The 59 code names that merely occur in two languages are in the JSON only.

| old | new | kind | languages | places |
|---|---|---|---|---|

### Coverage of the contract analysis (contratti/*.tsv)

**dati-contratto.tsv** — left out on purpose (step 2): 367, no Italian word: 92, not renamed (path, product name, or not found by the analysis): 95

Not renamed: `#puntatore-di-ripiego` `#tastiera-comando` `BOTTONE` `BUCHI` `CONFORME` `F18ESITO` `NON-BANNATO` `NON-CAPITO` `NON-CONFORME` `RIPRESA` `SBLOCCA` `TASTO` `TOLTO` `__AVVISO__` `__IMPRONTA__` `al_secondo` `algoritmo` `altro_scatola` `ammissione_s` `banco-nel-binario` `bit_per_canale_chi_lo_dice` `blocco_max_ms` `buchi_istante` `byte_flusso` `byte_persi` `byte_persi_d` `byte_spediti` `categorie` `chi_lo_dice` `cinture` `coda_rete_us` `commit_cura` `consegna_a_F2_3` `cpu_macchina_pct` `dgram_falsi_d` `dgram_persi_d` `distinti_riciclati` `durata_lavoro_s` `errori_decodifica` `file-del-banco` `giri_fermi` `giro_eco` `giro_peggiore_ms` `h264_strada` `ha_visto_il_guasto` `hevc_strada` `inizio_finestra_t` `inizio_t` `labwc_cliente` `latenza_ms` `ldd-pulito` `legami_in_ingresso` `mem_totale_mb` `mem_usata_mb` `minimo_pacchetti` `minimo_prove` `nascita_ms` `nascita_s` `opzioni-di-banco-nell-unita` `positivo` `primari` `primo_fotogramma_ms` `primo_non_degenere_s` `processi_gpu` `recinti` `remotix-appunti` `remotix-cattura` `remotix-figlio` `remotix-invisibile` `remotix-suono` `remotix_porta` `rete-quic` `ricevuti_d` `ritardi_eco_ms` `ritardi_ms` `ritmo_arretrato` `ritmo_posti` `rpmbuild-esito` `rx_rilascio` `rx_selinux_permissivo` `rx_versione` `scartati_d` `sessioni_durante` `sessioni_remotix` `soglia_silenzio_ms` `strozzatura_frazione` `tratti keys (strada, tela, dipinti, consegnati, fuori, dentro, coda_dec, saltati_coda, tardive, eta_ms, ric_ms, costo_disegno_ms, "8_decode_richiamo", "9a_richiamo_chiamata", "9b_conversione", "10_vetro", "9_10_richiamo_vetro", "11_vetro_prossimo_quadro")` `usciti_byte` `utenti-negati` `verificato` `video_avanza`

**opzioni-contratto.tsv** — left out on purpose (step 2): 773, no Italian word: 2, not renamed (path, product name, or not found by the analysis): 30

Not renamed: `B3_SPIA` `BRUCIATORI` `C15G4_TEMPI` `FINTO_CLASSE` `FINTO_MUORE` `G7_TRACCIA` `LIVELLO` `OPERAZIONI` `PARLANTINA` `PROFONDITA` `PUNTO` `QUALITA` `REMOTIX_NOME` `SBLOCCA` `VECCHIA_X264_EXTRA` `W1_RIPRENDI` `W1_STRADA` `W1_TIENI` `a-secco` `con-guasti` `raffica` `remotix-figlio` `rx_rilascio` `rx_selinux_permissivo` `rx_versione` `senza-nastro` `senza-rete` `solo-certifica` `sul-server` `un-verso`

**rcp-contratto.tsv** — left out on purpose (step 2): 127, no Italian word: 22, not renamed (path, product name, or not found by the analysis): 35, renamed by the table: 36

Not renamed: `ACCETTATA` `APPUNTI_ANNUNCIO` `APPUNTI_CHIEDI` `APPUNTI_TESTO` `BANCO_MARCA` `BUDGET_PIENO` `COMPOSITORE_INCAPACE` `DISPOSIZIONE` `FUNZIONE_SPENTA` `GIA_ATTIVA_LOCALE` `INATTIVITA` `MISURA_FUORI_LIMITI` `NON-BANNATO` `NON_ORA` `RCPREG` `RIPRESA` `RITARDO_FUORI_LIMITI` `SBLOCCA` `SESSIONE_ABBANDONATA` `SESSIONE_LOCALE_PREVALSA` `SESSIONE_TERMINATA` `TOLTO` `attacco` `attesa-attacca` `attesa-ciao` `attesa-credenziali` `attesa-verdetto` `cliente-di-prova` `desincronizzata` `pagina-b11` `remotix-pagina` `restanoMs` `sonda-b2` `staccata-per-silenzio` `ultimo_numero`


### Step 2 (later): file and directory moves (521)

Every reference is in rinomina2-plan.json → file_moves (first 200 per file).

| old | new | references |
|---|---|---|
| `DECISIONI.md` | `DECISIONS.md` | 1088 |
| `FASI.md` | `PHASES.md` | 168 |
| `LEZIONI.md` | `LESSONS.md` | 1096 |
| `SPECIFICHE.md` | `SPECS.md` | 525 |
| `STUDI.md` | `STUDIES.md` | 407 |
| `banchi/00-sessione-gnome.sh` | `benches/00-session-gnome.sh` | 14 |
| `banchi/01-b0-bersaglio.py` | `benches/01-b0-target.py` | 7 |
| `banchi/01-b0-bersaglio.sh` | `benches/01-b0-target.sh` | 25 |
| `banchi/01-b0-terreno.sh` | `benches/01-b0-terrain.sh` | 18 |
| `banchi/01-b11-guasto-innesta.py` | `benches/01-b11-fault-graft.py` | 15 |
| `banchi/01-b11-guasto.sh` | `benches/01-b11-fault.sh` | 18 |
| `banchi/01-b11-lancia.sh` | `benches/01-b11-launch.sh` | 14 |
| `banchi/01-b11-pagina.html` | `benches/01-b11-page.html` | 11 |
| `banchi/01-b2-cliente-aioquic.py` | `benches/01-b2-client-aioquic.py` | 8 |
| `banchi/01-b2-costruisci-ngtcp2.sh` | `benches/01-b2-build-ngtcp2.sh` | 7 |
| `banchi/01-b2-costruisci.sh` | `benches/01-b2-build.sh` | 8 |
| `banchi/01-b2-lancia-wt.sh` | `benches/01-b2-launch-wt.sh` | 13 |
| `banchi/01-b2-ngtcp2-wt-innesta.py` | `benches/01-b2-ngtcp2-wt-graft.py` | 26 |
| `banchi/01-b2-raccogli.py` | `benches/01-b2-collect.py` | 9 |
| `banchi/01-b2-sonda-trasporto.py` | `benches/01-b2-probe-transport.py` | 10 |
| `banchi/01-b2-sonda.html` | `benches/01-b2-probe.html` | 8 |
| `banchi/01-b3-cliente.py` | `benches/01-b3-client.py` | 158 |
| `banchi/01-b3-rcp-innesta.py` | `benches/01-b3-rcp-graft.py` | 55 |
| `banchi/01-b4-lancia.py` | `benches/01-b4-launch.py` | 7 |
| `banchi/01-b4-registrazioni.py` | `benches/01-b4-recordings.py` | 16 |
| `banchi/01-b4-validatore.py` | `benches/01-b4-validator.py` | 61 |
| `banchi/01-b5-lancia.sh` | `benches/01-b5-launch.sh` | 13 |
| `banchi/01-b5-violazioni.py` | `benches/01-b5-violations.py` | 17 |
| `banchi/01-b6-lancia.sh` | `benches/01-b6-launch.sh` | 21 |
| `banchi/01-b6-tetti.py` | `benches/01-b6-caps.py` | 13 |
| `banchi/01-b7-congedo.py` | `benches/01-b7-farewell.py` | 14 |
| `banchi/01-b7-lancia.sh` | `benches/01-b7-launch.sh` | 10 |
| `banchi/01-b8-cronometro.py` | `benches/01-b8-stopwatch.py` | 20 |
| `banchi/01-b8-lancia.sh` | `benches/01-b8-launch.sh` | 17 |
| `banchi/01-b8-prova-ban.c` | `benches/01-b8-test-ban.c` | 9 |
| `banchi/01-b8-sblocca.py` | `benches/01-b8-unblock.py` | 38 |
| `banchi/01-b9-letture.py` | `benches/01-b9-readings.py` | 11 |
| `banchi/01-casa-7448.sh` | `benches/01-home-7448.sh` | 10 |
| `banchi/01-s7-pagina.html` | `benches/01-s7-page.html` | 5 |
| `banchi/01-s7-raccogli.py` | `benches/01-s7-collect.py` | 5 |
| `banchi/01-s7-rotella.c` | `benches/01-s7-wheel.c` | 5 |
| `banchi/01-s7-rotella.sh` | `benches/01-s7-wheel.sh` | 6 |
| `banchi/02-cattura-certifica.sh` | `benches/02-capture-certify.sh` | 6 |
| `banchi/02-cattura-costruisci.sh` | `benches/02-capture-build.sh` | 3 |
| `banchi/02-cattura-fotogramma.c` | `benches/02-capture-frame.c` | 5 |
| `banchi/02-cattura-giudica.py` | `benches/02-capture-judge.py` | 9 |
| `banchi/02-cattura-lancia.sh` | `benches/02-capture-launch.sh` | 7 |
| `banchi/02-cattura-prodotto.c` | `benches/02-capture-product.c` | 4 |
| `banchi/02-codifica-costruisci.sh` | `benches/02-encoding-build.sh` | 7 |
| `banchi/02-codifica-immagine.py` | `benches/02-encoding-image.py` | 15 |
| `banchi/02-codifica-lancia.sh` | `benches/02-encoding-launch.sh` | 6 |
| `banchi/02-codifica-nal.py` | `benches/02-encoding-nal.py` | 12 |
| `banchi/02-codifica-obu.py` | `benches/02-encoding-obu.py` | 6 |
| `banchi/02-codifica-prova.c` | `benches/02-encoding-test.c` | 2 |
| `banchi/02-figlio-accendi.sh` | `benches/02-child-turn-on.sh` | 17 |
| `banchi/02-figlio-lancia.sh` | `benches/02-child-launch.sh` | 13 |
| `banchi/02-figlio-prova.py` | `benches/02-child-test.py` | 9 |
| `banchi/02-filo-cliente.py` | `benches/02-wire-client.py` | 19 |
| `banchi/02-filo-fotogramma.py` | `benches/02-wire-frame.py` | 35 |
| `banchi/02-filo-lancia.sh` | `benches/02-wire-launch.sh` | 6 |
| `banchi/02-filo-validatore.py` | `benches/02-wire-validator.py` | 26 |
| `banchi/02-pagina-misura-cdp.py` | `benches/02-page-measure-cdp.py` | 5 |
| `banchi/02-pagina-sonda-codec.py` | `benches/02-page-probe-codec.py` | 8 |
| `banchi/02-pam-accendi.sh` | `benches/02-pam-turn-on.sh` | 15 |
| `banchi/02-pam-fermo.py` | `benches/02-pam-stopped.py` | 14 |
| `banchi/02-pam-i3.py` | `benches/02-pam-i3.py` | 0 |
| `banchi/02-pam-lancia.sh` | `benches/02-pam-launch.sh` | 11 |
| `banchi/02-sessione-dispositivi.py` | `benches/02-session-devices.py` | 4 |
| `banchi/02-sessione-guardia.sh` | `benches/02-session-guard.sh` | 7 |
| `banchi/02-sessione-lancia.sh` | `benches/02-session-launch.sh` | 14 |
| `banchi/02-sessione-scene/nera.json` | `benches/02-session-scene/black.json` | 2 |
| `banchi/02-sessione-scene/sana.json` | `benches/02-session-scene/sana.json` | 0 |
| `banchi/02-sessione-stato.py` | `benches/02-session-state.py` | 12 |
| `banchi/03-marca.py` | `benches/03-mark.py` | 25 |
| `banchi/04-b25-guasti.c` | `benches/04-b25-faults.c` | 4 |
| `banchi/04-b25-lancia.sh` | `benches/04-b25-launch.sh` | 6 |
| `banchi/04-b25-tastiera.c` | `benches/04-b25-keyboard.c` | 7 |
| `banchi/04-b28-gesti.py` | `benches/04-b28-gestures.py` | 9 |
| `banchi/04-b28-lancia.sh` | `benches/04-b28-launch.sh` | 3 |
| `banchi/04-b31-tela.c` | `benches/04-b31-canvas.c` | 13 |
| `banchi/04-in8-costruisci.sh` | `benches/04-in8-build.sh` | 2 |
| `banchi/04-in8-misura.c` | `benches/04-in8-measure.c` | 7 |
| `banchi/04-in8-parita.c` | `benches/04-in8-parita.c` | 0 |
| `banchi/06-b33-costruisci.sh` | `benches/06-b33-build.sh` | 3 |
| `banchi/06-b33-risveglio-certifica.sh` | `benches/06-b33-wakeup-certify.sh` | 6 |
| `banchi/06-b33-risveglio-costruisci.sh` | `benches/06-b33-wakeup-build.sh` | 4 |
| `banchi/06-b33-risveglio-giudice.py` | `benches/06-b33-wakeup-judge.py` | 3 |
| `banchi/06-b33-risveglio-guasti.py` | `benches/06-b33-wakeup-faults.py` | 9 |
| `banchi/06-b33-risveglio.c` | `benches/06-b33-wakeup.c` | 4 |
| `banchi/06-b33-risveglio.sh` | `benches/06-b33-wakeup.sh` | 13 |
| `banchi/06-b33-terreno.sh` | `benches/06-b33-terrain.sh` | 25 |
| `banchi/06-b33-testimone.c` | `benches/06-b33-witness.c` | 8 |
| `banchi/06-b34-tabella.c` | `benches/06-b34-table.c` | 5 |
| `banchi/06-b5-esiti-cattura.c` | `benches/06-b5-outcomes-capture.c` | 9 |
| `banchi/06-b5-esiti-cattura.sh` | `benches/06-b5-outcomes-capture.sh` | 2 |
| `banchi/07-b42-giudice.py` | `benches/07-b42-judge.py` | 6 |
| `banchi/07-b46-marionette.py` | `benches/07-b46-marionette.py` | 0 |
| `banchi/07-b64-orecchio.py` | `benches/07-b64-ear.py` | 13 |
| `banchi/07-b64-rete.py` | `benches/07-b64-network.py` | 30 |
| `banchi/07-b64-scena.py` | `benches/07-b64-scene.py` | 11 |
| `banchi/07-b64-terreno.sh` | `benches/07-b64-terrain.sh` | 36 |
| `banchi/07-b65-datagram.py` | `benches/07-b65-datagram.py` | 0 |
| `banchi/09-b70-ritmo.py` | `benches/09-b70-rate.py` | 24 |
| `banchi/09-b76-rete-cattiva.py` | `benches/09-b76-network-bad.py` | 17 |
| `banchi/09-b77-audio-riordino.py` | `benches/09-b77-audio-reorder.py` | 7 |
| `banchi/09-b78-apertura.py` | `benches/09-b78-opening.py` | 29 |
| `banchi/09-b79-cure.py` | `benches/09-b79-cure.py` | 0 |
| `banchi/09-b79-terreno.sh` | `benches/09-b79-terrain.sh` | 7 |
| `banchi/09-b81-linea-morta.py` | `benches/09-b81-line-dead.py` | 13 |
| `banchi/09-b81-terreno.sh` | `benches/09-b81-terrain.sh` | 10 |
| `banchi/09-b84-audio-silenzio.py` | `benches/09-b84-audio-silence.py` | 16 |
| `banchi/09-lucchetto.py` | `benches/09-lock.py` | 15 |
| `banchi/10-f1-testimone.py` | `benches/10-f1-witness.py` | 46 |
| `banchi/11-scatole/11-accendi.sh` | `benches/11-boxes/11-turn-on.sh` | 175 |
| `banchi/11-scatole/11-c1-nasce-e-si-vede.py` | `benches/11-boxes/11-c1-born-e-sees.py` | 43 |
| `banchi/11-scatole/11-c10-le-copie-gemelle.py` | `benches/11-boxes/11-c10-copies-twins.py` | 5 |
| `banchi/11-scatole/11-c11-allineamento.py` | `benches/11-boxes/11-c11-alignment.py` | 6 |
| `banchi/11-scatole/11-c12-il-gancio-e-vivo.py` | `benches/11-boxes/11-c12-hook-e-alive.py` | 5 |
| `banchi/11-scatole/11-c13-la-certificazione-e-recente.py` | `benches/11-boxes/11-c13-certification-e-recent.py` | 5 |
| `banchi/11-scatole/11-c14-non-si-disturbano.py` | `benches/11-boxes/11-c14-not-disturb.py` | 5 |
| `banchi/11-scatole/11-c15-la-meta-remota-gira.py` | `benches/11-boxes/11-c15-meta-remote-runs.py` | 3 |
| `banchi/11-scatole/11-c16-eccezioni.txt` | `benches/11-boxes/11-c16-exceptions.txt` | 2 |
| `banchi/11-scatole/11-c16-i-documenti-non-mentono.py` | `benches/11-boxes/11-c16-i-documents-not-mentono.py` | 3 |
| `banchi/11-scatole/11-c17-gli-appunti-vanno-nei-due-versi.py` | `benches/11-boxes/11-c17-clipboard-go-in-two-directions.py` | 5 |
| `banchi/11-scatole/11-c18-i-gruppi-li-mette-il-prodotto.py` | `benches/11-boxes/11-c18-i-groups-puts-product.py` | 6 |
| `banchi/11-scatole/11-c19-la-scatola-resta-pulita.py` | `benches/11-boxes/11-c19-box-stays-clean.py` | 8 |
| `banchi/11-scatole/11-c2-finestra.html` | `benches/11-boxes/11-c2-window.html` | 4 |
| `banchi/11-scatole/11-c2-una-finestra-si-apre.py` | `benches/11-boxes/11-c2-window-opens.py` | 13 |
| `banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py` | `benches/11-boxes/11-c20-rebirth-not-port-ghosts.py` | 9 |
| `banchi/11-scatole/11-c20-scena.html` | `benches/11-boxes/11-c20-scene.html` | 8 |
| `banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py` | `benches/11-boxes/11-c21-on-edge-shape-change.py` | 10 |
| `banchi/11-scatole/11-c22-il-bordo-si-trascina.py` | `benches/11-boxes/11-c22-edge-drag.py` | 6 |
| `banchi/11-scatole/11-c23-maiusc-e-frecce-selezionano.py` | `benches/11-boxes/11-c23-shift-e-frecce-selezionano.py` | 8 |
| `banchi/11-scatole/11-c24-l-esci-chiude-sempre.py` | `benches/11-boxes/11-c24-l-exit-closes-always.py` | 6 |
| `banchi/11-scatole/11-c3-i-fotogrammi-cambiano.py` | `benches/11-boxes/11-c3-i-frames-change.py` | 7 |
| `banchi/11-scatole/11-c3-scena.html` | `benches/11-boxes/11-c3-scene.html` | 14 |
| `banchi/11-scatole/11-c4-il-tasto-arriva-allo-schermo.py` | `benches/11-boxes/11-c4-key-arrives-to-screen.py` | 6 |
| `banchi/11-scatole/11-c5-il-suono-non-e-silenzio.py` | `benches/11-boxes/11-c5-sound-not-e-silence.py` | 6 |
| `banchi/11-scatole/11-c6-si-stacca-e-si-ritrova.py` | `benches/11-boxes/11-c6-detach-e-finds-again.py` | 5 |
| `banchi/11-scatole/11-c7-si-chiude-e-non-resta-niente.py` | `benches/11-boxes/11-c7-closes-e-not-stays-nothing.py` | 8 |
| `banchi/11-scatole/11-c8-il-secondo-apre-il-browser.py` | `benches/11-boxes/11-c8-second-opens-browser.py` | 15 |
| `banchi/11-scatole/11-c8-pagina.html` | `benches/11-boxes/11-c8-page.html` | 8 |
| `banchi/11-scatole/11-c8b-la-pagina-si-vede-dal-cliente.py` | `benches/11-boxes/11-c8b-page-sees-from-client.py` | 5 |
| `banchi/11-scatole/11-c9-il-registro-dice-di-chi.py` | `benches/11-boxes/11-c9-log-says-of-who.py` | 7 |
| `banchi/11-scatole/11-capacita-del-prodotto.sh` | `benches/11-boxes/11-capabilities-of-product.sh` | 31 |
| `banchi/11-scatole/11-gancio-remoto.sh` | `benches/11-boxes/11-hook-remote.sh` | 4 |
| `banchi/11-scatole/11-gancio.sh` | `benches/11-boxes/11-hook.sh` | 95 |
| `banchi/11-scatole/11-pam-root-negato.py` | `benches/11-boxes/11-pam-root-denied.py` | 2 |
| `banchi/11-scatole/11-passo0.sh` | `benches/11-boxes/11-step0.sh` | 5 |
| `banchi/11-scatole/11-registro-unisci.py` | `benches/11-boxes/11-log-merge.py` | 7 |
| `banchi/11-scatole/Contenitore.gnome` | `benches/11-boxes/Container.gnome` | 10 |
| `banchi/11-scatole/Contenitore.kde` | `benches/11-boxes/Container.kde` | 11 |
| `banchi/11-scatole/Contenitore.lxqt` | `benches/11-boxes/Container.lxqt` | 5 |
| `banchi/11-scatole/Contenitore.xfce` | `benches/11-boxes/Container.xfce` | 9 |
| `banchi/11-scatole/Contenitore.xrdp` | `benches/11-boxes/Container.xrdp` | 10 |
| `banchi/11-scatole/adattatore.gnome.sh` | `benches/11-boxes/adapter.gnome.sh` | 2 |
| `banchi/11-scatole/adattatore.kde.sh` | `benches/11-boxes/adapter.kde.sh` | 2 |
| `banchi/11-scatole/adattatore.lxqt.sh` | `benches/11-boxes/adapter.lxqt.sh` | 3 |
| `banchi/11-scatole/adattatore.xfce.sh` | `benches/11-boxes/adapter.xfce.sh` | 4 |
| `banchi/11-scatole/appunti-gtk.py` | `benches/11-boxes/clipboard-gtk.py` | 18 |
| `banchi/11-scatole/rifai.sh` | `benches/11-boxes/redo.sh` | 1 |
| `banchi/12-c20-veri.py` | `benches/12-c20-true.py` | 13 |
| `banchi/12-client-veri.py` | `benches/12-client-true.py` | 28 |
| `banchi/13-w1-un-fotogramma.c` | `benches/13-w1-frame.c` | 5 |
| `banchi/14-f1-forma.c` | `benches/14-f1-shape.c` | 4 |
| `banchi/14-f1-forma.sh` | `benches/14-f1-shape.sh` | 4 |
| `banchi/15-suite/.gitignore` | `benches/15-suite/.gitignore` | 0 |
| `banchi/15-suite/15-compositori.sh` | `benches/15-suite/15-compositors.sh` | 16 |
| `banchi/15-suite/15-d006-misura.py` | `benches/15-suite/15-d006-measure.py` | 2 |
| `banchi/15-suite/15-d006-server.sh` | `benches/15-suite/15-d006-server.sh` | 0 |
| `banchi/15-suite/15-d007-server.sh` | `benches/15-suite/15-d007-server.sh` | 0 |
| `banchi/15-suite/15-f001-accesso-e-prima-immagine.py` | `benches/15-suite/15-f001-access-e-before-image.py` | 5 |
| `banchi/15-suite/15-f003-lo-schermo-si-aggiorna.py` | `benches/15-suite/15-f003-screen-update.py` | 5 |
| `banchi/15-suite/15-f004-il-mouse.py` | `benches/15-suite/15-f004-il-mouse.py` | 0 |
| `banchi/15-suite/15-f005-forma-del-puntatore.py` | `benches/15-suite/15-f005-shape-of-pointer.py` | 3 |
| `banchi/15-suite/15-f006-il-bordo-si-trascina.py` | `benches/15-suite/15-f006-edge-drag.py` | 3 |
| `banchi/15-suite/15-f007-tasti-speciali.py` | `benches/15-suite/15-f007-keys-special.py` | 3 |
| `banchi/15-suite/15-f008-modificatori.py` | `benches/15-suite/15-f008-modifiers.py` | 3 |
| `banchi/15-suite/15-f009-accenti-e-altgr.py` | `benches/15-suite/15-f009-accents-e-altgr.py` | 2 |
| `banchi/15-suite/15-f010-scorciatoie-del-desktop.py` | `benches/15-suite/15-f010-shortcuts-of-desktop.py` | 2 |
| `banchi/15-suite/15-f011-la-tela-all-attacco.py` | `benches/15-suite/15-f011-canvas-all-attach.py` | 5 |
| `banchi/15-suite/15-f012-audio.py` | `benches/15-suite/15-f012-audio.py` | 0 |
| `banchi/15-suite/15-f012b-audio-dopo-esci.py` | `benches/15-suite/15-f012b-audio-after-exit.py` | 2 |
| `banchi/15-suite/15-f013-video.py` | `benches/15-suite/15-f013-video.py` | 0 |
| `banchi/15-suite/15-f014-appunti.py` | `benches/15-suite/15-f014-clipboard.py` | 5 |
| `banchi/15-suite/15-f014c-appunti-dal-computer.py` | `benches/15-suite/15-f014c-clipboard-from-computer.py` | 3 |
| `banchi/15-suite/15-f016-stacco-e-riattacco.py` | `benches/15-suite/15-f016-detach-e-reattach.py` | 6 |
| `banchi/15-suite/15-f018-riattacco-a-misura-diversa.py` | `benches/15-suite/15-f018-reattach-a-measure-different.py` | 4 |
| `banchi/15-suite/15-f018b-finestre-dentro-al-riattacco.py` | `benches/15-suite/15-f018b-windows-inside-to-reattach.py` | 2 |
| `banchi/15-suite/15-f019-la-rete-cade.py` | `benches/15-suite/15-f019-network-falls.py` | 4 |
| `banchi/15-suite/15-f020-browser-chiuso-di-colpo.py` | `benches/15-suite/15-f020-browser-closed-of-shot.py` | 2 |
| `banchi/15-suite/15-f021-esci.py` | `benches/15-suite/15-f021-exit.py` | 6 |
| `banchi/15-suite/15-f022-orologi.py` | `benches/15-suite/15-f022-clocks.py` | 3 |
| `banchi/15-suite/15-f024b-sessione-mai-toccata.py` | `benches/15-suite/15-f024b-session-never-touched.py` | 3 |
| `banchi/15-suite/15-f025-stesso-utente-due-schede.py` | `benches/15-suite/15-f025-same-user-two-cards.py` | 2 |
| `banchi/15-suite/15-f026-piu-utenti-insieme.py` | `benches/15-suite/15-f026-more-users-together.py` | 2 |
| `banchi/15-suite/15-f027-parola-e-ban.py` | `benches/15-suite/15-f027-word-e-ban.py` | 2 |
| `banchi/15-suite/15-f029-voci-pericolose-assenti.py` | `benches/15-suite/15-f029-entries-dangerous-absent.py` | 2 |
| `banchi/15-suite/15-f030-schermo-sempre-acceso.py` | `benches/15-suite/15-f030-screen-always-on.py` | 2 |
| `banchi/15-suite/15-f031-tocco.py` | `benches/15-suite/15-f031-touch.py` | 6 |
| `banchi/15-suite/15-f031b-impostazioni-intatte.py` | `benches/15-suite/15-f031b-settings-intact.py` | 5 |
| `banchi/15-suite/15-f032-la-shell-dell-utente.py` | `benches/15-suite/15-f032-shell-of-user.py` | 4 |
| `banchi/15-suite/15-g1b-comune.py` | `benches/15-suite/15-g1b-common.py` | 7 |
| `banchi/15-suite/15-g1b-esplora.py` | `benches/15-suite/15-g1b-esplora.py` | 0 |
| `banchi/15-suite/15-g2-scena.py` | `benches/15-suite/15-g2-scene.py` | 11 |
| `banchi/15-suite/15-g3-comune.py` | `benches/15-suite/15-g3-common.py` | 4 |
| `banchi/15-suite/15-g4-comune.py` | `benches/15-suite/15-g4-common.py` | 8 |
| `banchi/15-suite/15-g6-comune.py` | `benches/15-suite/15-g6-common.py` | 6 |
| `banchi/15-suite/15-g7-comune.py` | `benches/15-suite/15-g7-common.py` | 4 |
| `banchi/15-suite/15-g7-server.sh` | `benches/15-suite/15-g7-server.sh` | 0 |
| `banchi/15-suite/15-g8-comune.py` | `benches/15-suite/15-g8-common.py` | 7 |
| `banchi/15-suite/15-g8-server.sh` | `benches/15-suite/15-g8-server.sh` | 0 |
| `banchi/15-suite/15-giro.py` | `benches/15-suite/15-round.py` | 35 |
| `banchi/15-suite/15-n027-negative.py` | `benches/15-suite/15-n027-negative.py` | 0 |
| `banchi/15-suite/15-porta.sh` | `benches/15-suite/15-port.sh` | 11 |
| `banchi/15-suite/15-rapporto.py` | `benches/15-suite/15-report.py` | 13 |
| `banchi/15-suite/15-rifai-scatole.sh` | `benches/15-suite/15-redo-boxes.sh` | 9 |
| `banchi/15-suite/15-una.sh` | `benches/15-suite/15-una.sh` | 0 |
| `banchi/15-suite/19-f018-prova.sh` | `benches/15-suite/19-f018-test.sh` | 4 |
| `banchi/15-suite/19-scatole-scheda.sh` | `benches/15-suite/19-boxes-card.sh` | 7 |
| `banchi/15-suite/suite.py` | `benches/15-suite/suite.py` | 0 |
| `banchi/16-stress/16-attore-rdp.py` | `benches/16-stress/16-actor-rdp.py` | 14 |
| `banchi/16-stress/16-attore.py` | `benches/16-stress/16-actor.py` | 15 |
| `banchi/16-stress/16-banco-tela.html` | `benches/16-stress/16-bench-canvas.html` | 3 |
| `banchi/16-stress/16-campagna.sh` | `benches/16-stress/16-campaign.sh` | 9 |
| `banchi/16-stress/16-classifica.py` | `benches/16-stress/16-ranking.py` | 32 |
| `banchi/16-stress/16-coda.sh` | `benches/16-stress/16-queue.sh` | 15 |
| `banchi/16-stress/16-compositori-rdp.sh` | `benches/16-stress/16-compositors-rdp.sh` | 12 |
| `banchi/16-stress/16-compositori.sh` | `benches/16-stress/16-compositors.sh` | 11 |
| `banchi/16-stress/16-controllo-corto.py` | `benches/16-stress/16-check-short.py` | 7 |
| `banchi/16-stress/16-d023-cornice.c` | `benches/16-stress/16-d023-border.c` | 1 |
| `banchi/16-stress/16-d023-cornice.sh` | `benches/16-stress/16-d023-border.sh` | 6 |
| `banchi/16-stress/16-lavori.py` | `benches/16-stress/16-jobs.py` | 8 |
| `banchi/16-stress/16-rapporto.py` | `benches/16-stress/16-report.py` | 8 |
| `banchi/16-stress/16-riclassifica.py` | `benches/16-stress/16-reclassify.py` | 10 |
| `banchi/16-stress/16-risorse.py` | `benches/16-stress/16-resources.py` | 13 |
| `banchi/16-stress/16-salita.py` | `benches/16-stress/16-climb.py` | 31 |
| `banchi/16-stress/finti/16-attore.py` | `benches/16-stress/fake/16-actor.py` | 15 |
| `banchi/16-stress/finti/16-classifica.py` | `benches/16-stress/fake/16-ranking.py` | 32 |
| `banchi/16-stress/finti/16-risorse.py` | `benches/16-stress/fake/16-resources.py` | 13 |
| `banchi/17-distro/17-amministratore.sh` | `benches/17-distro/17-administrator.sh` | 11 |
| `banchi/17-distro/17-carico.sh` | `benches/17-distro/17-load.sh` | 5 |
| `banchi/17-distro/17-t10-giro.sh` | `benches/17-distro/17-t10-round.sh` | 6 |
| `banchi/17-distro/17-t10.sh` | `benches/17-distro/17-t10.sh` | 0 |
| `banchi/17-distro/17-t1c-browser.py` | `benches/17-distro/17-t1c-browser.py` | 0 |
| `banchi/17-distro/17-t1c-guarda.sh` | `benches/17-distro/17-t1c-look.sh` | 25 |
| `banchi/17-distro/17-t1c-installa.sh` | `benches/17-distro/17-t1c-install.sh` | 4 |
| `banchi/17-distro/17-t3-gruppi.sh` | `benches/17-distro/17-t3-groups.sh` | 8 |
| `banchi/17-distro/17-t3-impronta-arch.sh` | `benches/17-distro/17-t3-fingerprint-arch.sh` | 10 |
| `banchi/17-distro/17-t3-impronta-rpm.sh` | `benches/17-distro/17-t3-fingerprint-rpm.sh` | 16 |
| `banchi/17-distro/17-t3-impronta.sh` | `benches/17-distro/17-t3-fingerprint.sh` | 12 |
| `banchi/17-distro/17-t3-pacchetto.sh` | `benches/17-distro/17-t3-package.sh` | 12 |
| `banchi/17-distro/17-t3-prova.sh` | `benches/17-distro/17-t3-test.sh` | 6 |
| `banchi/17-distro/17-t3-rpm.sh` | `benches/17-distro/17-t3-rpm.sh` | 0 |
| `banchi/17-distro/17-t4-alma.sh` | `benches/17-distro/17-t4-alma.sh` | 0 |
| `banchi/17-distro/17-t4-motore.sh` | `benches/17-distro/17-t4-engine.sh` | 10 |
| `banchi/17-distro/17-vm.sh` | `benches/17-distro/17-vm.sh` | 0 |
| `banchi/17-distro/iso-differenze.md` | `benches/17-distro/iso-differences.md` | 3 |
| `banchi/17-distro/iso-risposte/alma10.ks` | `benches/17-distro/iso-replies/alma10.ks` | 0 |
| `banchi/17-distro/iso-risposte/arch.config.json` | `benches/17-distro/iso-replies/arch.config.json` | 0 |
| `banchi/17-distro/iso-risposte/arch.creds.json` | `benches/17-distro/iso-replies/arch.creds.json` | 0 |
| `banchi/17-distro/iso-risposte/arch.sh` | `benches/17-distro/iso-replies/arch.sh` | 0 |
| `banchi/17-distro/iso-risposte/debian13.preseed` | `benches/17-distro/iso-replies/debian13.preseed` | 0 |
| `banchi/17-distro/iso-risposte/fedora44.ks` | `benches/17-distro/iso-replies/fedora44.ks` | 0 |
| `banchi/17-distro/iso-risposte/tumbleweed.xml` | `benches/17-distro/iso-replies/tumbleweed.xml` | 0 |
| `banchi/17-distro/iso-risposte/ubuntu2604.user-data` | `benches/17-distro/iso-replies/ubuntu2604.user-data` | 0 |
| `banchi/17-distro/scatole/17-scatola.sh` | `benches/17-distro/boxes/17-box.sh` | 13 |
| `banchi/17-distro/scatole/Contenitore.alma10` | `benches/17-distro/boxes/Container.alma10` | 3 |
| `banchi/17-distro/scatole/Contenitore.arch` | `benches/17-distro/boxes/Container.arch` | 6 |
| `banchi/17-distro/scatole/Contenitore.debian13` | `benches/17-distro/boxes/Container.debian13` | 11 |
| `banchi/17-distro/scatole/Contenitore.fedora44` | `benches/17-distro/boxes/Container.fedora44` | 3 |
| `banchi/17-distro/scatole/Contenitore.suse` | `benches/17-distro/boxes/Container.suse` | 1 |
| `banchi/17-distro/scatole/Contenitore.ubuntu2604` | `benches/17-distro/boxes/Container.ubuntu2604` | 3 |
| `banchi/17-distro/scatole/comune.sh` | `benches/17-distro/boxes/common.sh` | 9 |
| `banchi/17-t2/catena.sh` | `benches/17-t2/chain.sh` | 2 |
| `banchi/17-t2/lancia.sh` | `benches/17-t2/launch.sh` | 11 |
| `banchi/17-t2/riassunto.sh` | `benches/17-t2/summary.sh` | 2 |
| `banchi/17-t2/t2-misura.py` | `benches/17-t2/t2-measure.py` | 3 |
| `banchi/17-t2/t2box.py` | `benches/17-t2/t2box.py` | 0 |
| `banchi/17-t2/tabella.sh` | `benches/17-t2/table.sh` | 1 |
| `banchi/17-t6/t6-giornale.sh` | `benches/17-t6/t6-journal.sh` | 3 |
| `banchi/17-t6/t6-giro.sh` | `benches/17-t6/t6-round.sh` | 4 |
| `banchi/17-t6/t6-leggi-pam.sh` | `benches/17-t6/t6-read-pam.sh` | 9 |
| `banchi/17-t6/t6-porta.sh` | `benches/17-t6/t6-port.sh` | 3 |
| `banchi/17-t6/t6-seguiti.sh` | `benches/17-t6/t6-seguiti.sh` | 0 |
| `banchi/17-t6/t6-vm.sh` | `benches/17-t6/t6-vm.sh` | 0 |
| `banchi/17-t7/t7-abbandono.py` | `benches/17-t7/t7-abandonment.py` | 3 |
| `banchi/17-t7/t7-aggiorna.py` | `benches/17-t7/t7-update.py` | 5 |
| `banchi/17-t7/t7-campagna.sh` | `benches/17-t7/t7-campaign.sh` | 4 |
| `banchi/17-t7/t7-fine.sh` | `benches/17-t7/t7-fine.sh` | 0 |
| `banchi/17-t7/t7box.py` | `benches/17-t7/t7box.py` | 0 |
| `banchi/17-t8/t8-browser.py` | `benches/17-t8/t8-browser.py` | 0 |
| `banchi/17-t8/t8-catenab.sh` | `benches/17-t8/t8-catenab.sh` | 0 |
| `banchi/17-t8/t8-guasta.sh` | `benches/17-t8/t8-broken.sh` | 7 |
| `banchi/17-t8/t8-porta.sh` | `benches/17-t8/t8-port.sh` | 5 |
| `banchi/17-t8/t8-terzi.sh` | `benches/17-t8/t8-third-party.sh` | 3 |
| `banchi/17-t8/t8-vm.sh` | `benches/17-t8/t8-vm.sh` | 0 |
| `banchi/17-t9/t9-gui.sh` | `benches/17-t9/t9-gui.sh` | 0 |
| `banchi/17-t9/t9-porta.sh` | `benches/17-t9/t9-port.sh` | 4 |
| `banchi/17-t9/t9-r36.sh` | `benches/17-t9/t9-r36.sh` | 0 |
| `banchi/17-t9/t9-rete.py` | `benches/17-t9/t9-network.py` | 5 |
| `banchi/17-t9/t9-vm.sh` | `benches/17-t9/t9-vm.sh` | 0 |
| `banchi/18-a1/18-a1-opus-senza-ffmpeg.c` | `benches/18-a1/18-a1-opus-without-ffmpeg.c` | 3 |
| `banchi/18-a1/audio-vecchio.c` | `benches/18-a1/audio-old.c` | 3 |
| `banchi/18-a1/chrome.html` | `benches/18-a1/chrome.html` | 0 |
| `banchi/18-a1/chrome.py` | `benches/18-a1/chrome.py` | 0 |
| `banchi/18-a1/costruisci.sh` | `benches/18-a1/build.sh` | 114 |
| `banchi/18-scheda/18-confronto.c` | `benches/18-card/18-comparison.c` | 4 |
| `banchi/18-scheda/18-confronto.sh` | `benches/18-card/18-comparison.sh` | 14 |
| `banchi/18-scheda/18-decodifica-chrome.html` | `benches/18-card/18-decoding-chrome.html` | 4 |
| `banchi/18-scheda/18-decodifica-chrome.sh` | `benches/18-card/18-decoding-chrome.sh` | 5 |
| `banchi/18-scheda/18-tabella.py` | `benches/18-card/18-table.py` | 5 |
| `banchi/18-software/18-software-confronto.c` | `benches/18-software/18-software-comparison.c` | 4 |
| `banchi/18-software/18-software-confronto.sh` | `benches/18-software/18-software-comparison.sh` | 6 |
| `banchi/18-software/18-software-openh264-vuota.c` | `benches/18-software/18-software-openh264-empty.c` | 2 |
| `banchi/18-software/18-software-webcodecs.html` | `benches/18-software/18-software-webcodecs.html` | 0 |
| `banchi/18-software/18-software-webcodecs.py` | `benches/18-software/18-software-webcodecs.py` | 0 |
| `banchi/19-android/19-android.py` | `benches/19-android/19-android.py` | 0 |
| `banchi/19-android/19-android.sh` | `benches/19-android/19-android.sh` | 0 |
| `banchi/19-android/LEGGIMI.md` | `benches/19-android/README.md` | 5 |
| `banchi/19-android/telefono.py` | `benches/19-android/phone.py` | 11 |
| `banchi/19-nvidia/19-nv-macchina.sh` | `benches/19-nvidia/19-nv-machine.sh` | 9 |
| `banchi/19-nvidia/19-nv-prova-contenitore.sh` | `benches/19-nvidia/19-nv-test-container.sh` | 4 |
| `banchi/19-nvidia/19-nv-suite.py` | `benches/19-nvidia/19-nv-suite.py` | 0 |
| `banchi/19-nvidia/19-nvidia.sh` | `benches/19-nvidia/19-nvidia.sh` | 0 |
| `banchi/19-nvidia/LEGGIMI.md` | `benches/19-nvidia/README.md` | 5 |
| `banchi/19-vulkan/19-confronto.c` | `benches/19-vulkan/19-comparison.c` | 3 |
| `banchi/19-vulkan/19-confronto.sh` | `benches/19-vulkan/19-comparison.sh` | 11 |
| `banchi/19-vulkan/19-decodifica-chrome.sh` | `benches/19-vulkan/19-decoding-chrome.sh` | 6 |
| `banchi/19-vulkan/19-shader.sh` | `benches/19-vulkan/19-shader.sh` | 0 |
| `banchi/19-vulkan/19-tabella.py` | `benches/19-vulkan/19-table.py` | 5 |
| `banchi/19-vulkan/chrome/19-chrome-corri.sh` | `benches/19-vulkan/chrome/19-chrome-run.sh` | 1 |
| `banchi/19-vulkan/chrome/19-chrome-prova.html` | `benches/19-vulkan/chrome/19-chrome-test.html` | 1 |
| `banchi/19-vulkan/chrome/19-chrome-servi.py` | `benches/19-vulkan/chrome/19-chrome-serve.py` | 1 |
| `banchi/attrezzi-allinea-innesto.sh` | `benches/tools-align-graft.sh` | 9 |
| `banchi/attrezzi-allinea-prodotto.sh` | `benches/tools-align-product.sh` | 8 |
| `banchi/attrezzi-gruppi-scheda.sh` | `benches/tools-groups-card.sh` | 36 |
| `banchi/attrezzi-utenti.sh` | `benches/tools-users.sh` | 4 |
| `banchi/rcp/autenticazione.c` | `benches/rcp/authentication.c` | 83 |
| `banchi/rcp/rcp.c` | `benches/rcp/rcp.c` | 0 |
| `banchi/rcp/rcp.h` | `benches/rcp/rcp.h` | 0 |
| `banchi/sonda/lancia.sh` | `benches/probe/launch.sh` | 11 |
| `banchi/sonda/racc.py` | `benches/probe/coll.py` | 2 |
| `banchi/sonda/sonda-rcp.html` | `benches/probe/probe-rcp.html` | 4 |
| `fasi/06-la-tela-e-la-vista.md` | `phases/06-canvas-e-view.md` | 18 |
| `fasi/07-audio-e-appunti.md` | `phases/07-audio-e-clipboard.md` | 8 |
| `fasi/08-l-anello.md` | `phases/08-l-ring.md` | 13 |
| `fasi/09-la-qualita-e-la-degradazione.md` | `phases/09-quality-e-degradation.md` | 21 |
| `fasi/10-multi-tenant-e-il-budget.md` | `phases/10-multi-tenant-e-il-budget.md` | 0 |
| `fasi/11-la-rete-di-sicurezza.md` | `phases/11-network-of-security.md` | 19 |
| `fasi/12-kde.md` | `phases/12-kde.md` | 0 |
| `fasi/13-xfce.md` | `phases/13-xfce.md` | 0 |
| `fasi/14-lxqt.md` | `phases/14-lxqt.md` | 0 |
| `fasi/15-suite-funzionale.md` | `phases/15-suite-functional.md` | 4 |
| `fasi/16-a3-radeon-vcn.md` | `phases/16-a3-radeon-vcn.md` | 0 |
| `fasi/16-stress-e-capacita.md` | `phases/16-stress-e-capabilities.md` | 10 |
| `fasi/17-l-installatore.md` | `phases/17-l-installer.md` | 55 |
| `fasi/18-senza-ffmpeg.md` | `phases/18-without-ffmpeg.md` | 30 |
| `fasi/19-nvidia.md` | `phases/19-nvidia.md` | 0 |
| `fasi/20-le-prestazioni.md` | `phases/20-performance.md` | 8 |
| `fasi/21-la-licenza.md` | `phases/21-license.md` | 5 |
| `grafica/sito-mockup/LEGGIMI.md` | `graphical/site-mockup/README.md` | 5 |
| `grafica/sito-mockup/autocontenuta.py` | `graphical/site-mockup/autocontenuta.py` | 0 |
| `grafica/sito-mockup/index.html` | `graphical/site-mockup/index.html` | 0 |
| `grafica/sito-mockup/performance.html` | `graphical/site-mockup/performance.html` | 0 |
| `grafica/sito-mockup/stile.css` | `graphical/site-mockup/style.css` | 7 |
| `grafica/tui-mockup/index.html` | `graphical/tui-mockup/index.html` | 0 |
| `installatore/.gitignore` | `installer/.gitignore` | 0 |
| `installatore/catalogo/catalogo.go` | `installer/catalog/catalog.go` | 2 |
| `installatore/catalogo/catalogo.json` | `installer/catalog/catalog.json` | 17 |
| `installatore/cmd/remotix-install/interfacce.go` | `installer/cmd/remotix-install/interfaces.go` | 3 |
| `installatore/cmd/remotix-install/main.go` | `installer/cmd/remotix-install/main.go` | 0 |
| `installatore/costruisci.sh` | `installer/build.sh` | 114 |
| `installatore/go.mod` | `installer/go.mod` | 0 |
| `installatore/interfaccia/sessione.go` | `installer/interface/session.go` | 4 |
| `installatore/interfaccia/testi.go` | `installer/interface/texts.go` | 15 |
| `installatore/interfaccia/testi_test.go` | `installer/interface/texts_test.go` | 2 |
| `installatore/interfaccia/tui/anteprima.go` | `installer/interface/tui/preview.go` | 1 |
| `installatore/interfaccia/tui/tui.go` | `installer/interface/tui/tui.go` | 0 |
| `installatore/interfaccia/tui/tui_test.go` | `installer/interface/tui/tui_test.go` | 0 |
| `installatore/interfaccia/vista.go` | `installer/interface/vista.go` | 0 |
| `installatore/motore/aggiornato.go` | `installer/engine/updated.go` | 2 |
| `installatore/motore/ambiente.go` | `installer/engine/environment.go` | 7 |
| `installatore/motore/archivio.go` | `installer/engine/archive.go` | 3 |
| `installatore/motore/azione_file.go` | `installer/engine/action_file.go` | 1 |
| `installatore/motore/azione_gruppo.go` | `installer/engine/action_group.go` | 1 |
| `installatore/motore/azione_pacchetti.go` | `installer/engine/action_packets.go` | 3 |
| `installatore/motore/azione_registri_utente.go` | `installer/engine/action_logs_user.go` | 2 |
| `installatore/motore/azione_servizio.go` | `installer/engine/action_service.go` | 1 |
| `installatore/motore/azione_sessioni.go` | `installer/engine/action_sessions.go` | 1 |
| `installatore/motore/azione_unita.go` | `installer/engine/action_unit.go` | 1 |
| `installatore/motore/azioni.go` | `installer/engine/actions.go` | 1 |
| `installatore/motore/azioni_dichiarate.go` | `installer/engine/actions_declared.go` | 2 |
| `installatore/motore/certifica.go` | `installer/engine/certify.go` | 4 |
| `installatore/motore/certifica_test.go` | `installer/engine/certify_test.go` | 2 |
| `installatore/motore/codici.go` | `installer/engine/codes.go` | 15 |
| `installatore/motore/compatibilita.go` | `installer/engine/compatibilita.go` | 0 |
| `installatore/motore/dbus.go` | `installer/engine/dbus.go` | 0 |
| `installatore/motore/disinstalla.go` | `installer/engine/uninstall.go` | 4 |
| `installatore/motore/disinstalla_test.go` | `installer/engine/uninstall_test.go` | 2 |
| `installatore/motore/epoca_test.go` | `installer/engine/epoch_test.go` | 1 |
| `installatore/motore/eventi.go` | `installer/engine/events.go` | 3 |
| `installatore/motore/fiducia.go` | `installer/engine/trust.go` | 4 |
| `installatore/motore/fiducia_test.go` | `installer/engine/trust_test.go` | 2 |
| `installatore/motore/finti2_test.go` | `installer/engine/fake2_test.go` | 2 |
| `installatore/motore/finti_test.go` | `installer/engine/fake_test.go` | 2 |
| `installatore/motore/formato.go` | `installer/engine/format.go` | 4 |
| `installatore/motore/gestore.go` | `installer/engine/handler.go` | 6 |
| `installatore/motore/grafica_utente.go` | `installer/engine/graphical_user.go` | 3 |
| `installatore/motore/inglese_test.go` | `installer/engine/english_test.go` | 6 |
| `installatore/motore/interfaccia.go` | `installer/engine/interface.go` | 3 |
| `installatore/motore/interfaccia_test.go` | `installer/engine/interface_test.go` | 2 |
| `installatore/motore/lingua.go` | `installer/engine/language.go` | 2 |
| `installatore/motore/lingua_test.go` | `installer/engine/language_test.go` | 2 |
| `installatore/motore/motore_test.go` | `installer/engine/engine_test.go` | 3 |
| `installatore/motore/occupato.go` | `installer/engine/taken.go` | 5 |
| `installatore/motore/occupato_test.go` | `installer/engine/taken_test.go` | 1 |
| `installatore/motore/operazione.go` | `installer/engine/operation.go` | 6 |
| `installatore/motore/piano.go` | `installer/engine/piano.go` | 0 |
| `installatore/motore/piano_installazione.go` | `installer/engine/plan_installation.go` | 3 |
| `installatore/motore/preflight.go` | `installer/engine/preflight.go` | 0 |
| `installatore/motore/preflight_test.go` | `installer/engine/preflight_test.go` | 0 |
| `installatore/motore/profilo.go` | `installer/engine/profile.go` | 2 |
| `installatore/motore/registro.go` | `installer/engine/log.go` | 2 |
| `installatore/motore/ripresa_test.go` | `installer/engine/resumed_test.go` | 4 |
| `installatore/motore/script_test.go` | `installer/engine/script_test.go` | 0 |
| `installatore/motore/stati.go` | `installer/engine/states.go` | 4 |
| `installatore/motore/strade.go` | `installer/engine/routes.go` | 14 |
| `installatore/motore/tabella.go` | `installer/engine/table.go` | 2 |
| `installatore/motore/testi.go` | `installer/engine/texts.go` | 15 |
| `installatore/motore/versioni.go` | `installer/engine/versions.go` | 2 |
| `installatore/prove/Contenitore.systemd` | `installer/prove/Container.systemd` | 6 |
| `installatore/prove/gruppi-desktop.sh` | `installer/prove/groups-desktop.sh` | 2 |
| `installatore/prove/impronta/main.go` | `installer/prove/fingerprint/main.go` | 0 |
| `installatore/prove/r1-contenitori.sh` | `installer/prove/r1-contenitori.sh` | 0 |
| `installatore/prove/sul-server.sh` | `installer/prove/on-server.sh` | 4 |
| `installatore/prove/systemd-giro.sh` | `installer/prove/systemd-round.sh` | 3 |
| `installatore/run.sh` | `installer/run.sh` | 0 |
| `packaging/arch/costruisci.sh` | `packaging/arch/build.sh` | 114 |
| `packaging/arch/remotix-niente-sospensione.conf` | `packaging/arch/remotix-nothing-suspend.conf` | 22 |
| `packaging/arch/utenti-negati` | `packaging/arch/users-denied` | 66 |
| `packaging/archivio/licenze.py` | `packaging/archive/licenze.py` | 0 |
| `packaging/archivio/sbom.py` | `packaging/archive/sbom.py` | 0 |
| `packaging/debian/remotix-niente-sospensione.conf` | `packaging/debian/remotix-nothing-suspend.conf` | 22 |
| `packaging/debian/utenti-negati` | `packaging/debian/users-denied` | 66 |
| `packaging/motore/PKGBUILD` | `packaging/engine/PKGBUILD` | 0 |
| `packaging/motore/README` | `packaging/engine/README` | 0 |
| `packaging/motore/pacchetti-motore.sh` | `packaging/engine/packets-engine.sh` | 12 |
| `packaging/motore/remotix-install.install` | `packaging/engine/remotix-install.install` | 0 |
| `packaging/motore/remotix-install.spec` | `packaging/engine/remotix-install.spec` | 0 |
| `packaging/rilascio.sh` | `packaging/release.sh` | 35 |
| `packaging/rpm/costruisci-rpm.sh` | `packaging/rpm/build-rpm.sh` | 20 |
| `packaging/rpm/remotix-niente-sospensione.conf` | `packaging/rpm/remotix-nothing-suspend.conf` | 22 |
| `packaging/rpm/selinux/remotix_porta.cil` | `packaging/rpm/selinux/remotix_port.cil` | 9 |
| `src/Contenitore` | `src/Container` | 81 |
| `src/aiutante.c` | `src/helper.c` | 39 |
| `src/aiutante.h` | `src/helper.h` | 19 |
| `src/appunti.c` | `src/clipboard.c` | 50 |
| `src/appunti.h` | `src/clipboard.h` | 30 |
| `src/appunti_kde.c` | `src/clipboard_kde.c` | 24 |
| `src/appunti_kde.h` | `src/clipboard_kde.h` | 9 |
| `src/autenticazione.c` | `src/authentication.c` | 83 |
| `src/cattura.c` | `src/capture.c` | 126 |
| `src/cattura.h` | `src/capture.h` | 66 |
| `src/certificati.c` | `src/certificates.c` | 23 |
| `src/certificati.h` | `src/certificates.h` | 13 |
| `src/codificatore.c` | `src/encoder.c` | 181 |
| `src/codificatore.h` | `src/encoder.h` | 37 |
| `src/colori709.c` | `src/colors709.c` | 46 |
| `src/colori709.h` | `src/colors709.h` | 9 |
| `src/comando.c` | `src/command.c` | 20 |
| `src/comando.h` | `src/command.h` | 9 |
| `src/costruisci-in-contenitore.sh` | `src/build-in-container.sh` | 18 |
| `src/costruisci.sh` | `src/build.sh` | 114 |
| `src/costruzione/Contenitore.alma10` | `src/build/Container.alma10` | 3 |
| `src/costruzione/Contenitore.arch` | `src/build/Container.arch` | 6 |
| `src/costruzione/Contenitore.debian13` | `src/build/Container.debian13` | 11 |
| `src/costruzione/Contenitore.fedora44` | `src/build/Container.fedora44` | 3 |
| `src/costruzione/Contenitore.leap16` | `src/build/Container.leap16` | 2 |
| `src/costruzione/Contenitore.tumbleweed` | `src/build/Container.tumbleweed` | 2 |
| `src/costruzione/Contenitore.ubuntu2404` | `src/build/Container.ubuntu2404` | 2 |
| `src/costruzione/Contenitore.ubuntu2604` | `src/build/Container.ubuntu2604` | 3 |
| `src/costruzione/costruisci-deb.sh` | `src/build/build-deb.sh` | 22 |
| `src/costruzione/costruisci-tutti.sh` | `src/build/build-all.sh` | 21 |
| `src/costruzione/quic-statiche.sh` | `src/build/quic-static.sh` | 37 |
| `src/cursore.c` | `src/cursor.c` | 50 |
| `src/cursore.h` | `src/cursor.h` | 38 |
| `src/figlio.c` | `src/child.c` | 366 |
| `src/figlio.h` | `src/child.h` | 34 |
| `src/forma.c` | `src/shape.c` | 18 |
| `src/forma.h` | `src/shape.h` | 20 |
| `src/opus-wasm/costruisci.sh` | `src/opus-wasm/build.sh` | 114 |
| `src/opus-wasm/decodifica.c` | `src/opus-wasm/decoding.c` | 5 |
| `src/opus-wasm/prova/confronta.mjs` | `src/opus-wasm/prova/compare.mjs` | 5 |
| `src/opus-wasm/prova/riferimento.c` | `src/opus-wasm/prova/reference.c` | 4 |
| `src/pagina.c` | `src/page.c` | 45 |
| `src/pagina.h` | `src/page.h` | 8 |
| `src/pagina.html` | `src/page.html` | 313 |
| `src/provisiona.sh` | `src/provisions.sh` | 86 |
| `src/registro.c` | `src/log.c` | 53 |
| `src/registro.h` | `src/log.h` | 107 |
| `src/remotix-niente-spegnimento.rules` | `src/remotix-nothing-shutdown.rules` | 15 |
| `src/remotix-tasti.conf` | `src/remotix-keys.conf` | 24 |
| `src/riavvia-7700.sh` | `src/restart-7700.sh` | 20 |
| `src/riavvia-7900.sh` | `src/restart-7900.sh` | 8 |
| `src/ritrovo.c` | `src/finding_again.c` | 9 |
| `src/ritrovo.h` | `src/finding_again.h` | 13 |
| `src/scrittore_bit.c` | `src/writer_bit.c` | 14 |
| `src/scrittore_bit.h` | `src/writer_bit.h` | 11 |
| `src/sentinella.c` | `src/sentinel.c` | 24 |
| `src/sentinella.h` | `src/sentinel.h` | 14 |
| `src/sessione.c` | `src/session.c` | 159 |
| `src/sessione.h` | `src/session.h` | 43 |
| `src/suono.c` | `src/sound.c` | 29 |
| `src/suono.h` | `src/sound.h` | 16 |
| `src/tastiera.c` | `src/keyboard.c` | 81 |
| `src/tastiera.h` | `src/keyboard.h` | 27 |
| `src/trasporto.c` | `src/transport.c` | 94 |
| `src/trasporto.h` | `src/transport.h` | 8 |
| `src/vadiretta.c` | `src/vadirect.c` | 47 |
| `src/vadiretta.h` | `src/vadirect.h` | 10 |

<!-- generated:end -->
