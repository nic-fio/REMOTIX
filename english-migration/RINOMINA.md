# RINOMINA — the safe mechanical rename of the Italian names (track en-40)

> `DECISIONI.md` §10.38: REMOTIX is fully English — identifiers, file names, options, RCP message and
> capability names included, **no compatibility aliases**.  This document is the plan for the *names*;
> the comments and the sentences were translated by hand in step 1.
>
> ⛔ **Nothing here has been applied to the tree.**  The tool, its tables and this plan are committed;
> the rename itself is a separate, later act (§7).  The tool is deterministic: it is re-run on the final
> tree after the other en-* branches have landed, and the plan below is regenerated from that tree.

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
| `english-migration/contratti/*.tsv` | the contract analysis: RCP names, data names, options and environment variables, with places |

The old `rinomina.py` stays for reference: it rewrote every word of every file, and its dry run
gave 21,650 pairs, 1,346 collisions and 5,284 clashes — the reasons for this second tool.

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
| names renamed | 10367 |
| kept unresolved | 11 |
| excluded | 16 |
| collisions handled | 148 |
| contracts | 2717 |
| files scanned | 614 |
| files skipped | 2584 |
| frozen register words | 1095 |
| shared new names | 284 |
| merges met in a scope | 38 |
| data names dati tsv | 73 |

**Names by defining language** (a name defined in two languages counts twice)

| language | names |
|---|---|
| c | 3990 |
| css | 53 |
| go | 1063 |
| html | 1091 |
| js | 7 |
| make | 18 |
| py | 4737 |
| sh | 1104 |

**Renamed names defined per directory**

| directory | names |
|---|---|
| `src` | 7200 |
| `banchi/11-scatole` | 2689 |
| `banchi/15-suite` | 2437 |
| `installatore/motore` | 2066 |
| `banchi/16-stress` | 1292 |
| `banchi/rcp` | 623 |
| `banchi/09-b81-linea-morta.py` | 346 |
| `installatore/interfaccia` | 337 |
| `banchi/01-b3-cliente.py` | 251 |
| `banchi/01-b8-cronometro.py` | 228 |
| `banchi/19-android` | 222 |
| `banchi/09-b76-rete-cattiva.py` | 217 |
| `banchi/17-distro` | 213 |
| `grafica` | 212 |
| `banchi/09-b70-ritmo.py` | 196 |
| `banchi/01-b7-congedo.py` | 178 |
| `banchi/02-filo-fotogramma.py` | 162 |
| `banchi/19-vulkan` | 161 |
| `banchi/09-b79-cure.py` | 160 |
| `docs/sources` | 154 |
| `banchi/09-b77-audio-riordino.py` | 151 |
| `banchi/18-software` | 141 |
| `banchi/12-client-veri.py` | 139 |
| `banchi/01-b4-validatore.py` | 138 |
| `banchi/19-nvidia` | 136 |
| `banchi/02-cattura-fotogramma.c` | 130 |
| `banchi/02-filo-validatore.py` | 130 |
| `banchi/01-b11-pagina.html` | 124 |
| `banchi/18-scheda` | 124 |
| `banchi/04-b28-gesti.py` | 122 |
| `banchi/18-a1` | 116 |
| `banchi/01-b6-tetti.py` | 115 |
| `banchi/03-marca.py` | 110 |
| `banchi/04-b31-tela.c` | 108 |
| `banchi/01-b5-violazioni.py` | 106 |
| `banchi/09-b84-audio-silenzio.py` | 103 |
| `banchi/02-filo-cliente.py` | 98 |
| `banchi/10-f1-testimone.py` | 93 |
| `banchi/02-pam-fermo.py` | 88 |
| `banchi/06-b5-esiti-cattura.c` | 88 |
| `banchi/06-b33-testimone.c` | 87 |
| `banchi/02-cattura-giudica.py` | 85 |
| `banchi/09-b78-apertura.py` | 85 |
| `banchi/01-b9-letture.py` | 82 |
| `banchi/02-cattura-prodotto.c` | 82 |
| `banchi/12-c20-veri.py` | 78 |
| `banchi/07-b64-rete.py` | 75 |
| `banchi/04-in8-misura.c` | 70 |
| `banchi/01-b4-registrazioni.py` | 68 |
| `banchi/17-t7` | 67 |
| `banchi/01-b8-prova-ban.c` | 66 |
| `banchi/06-b33-risveglio.c` | 64 |
| `banchi/sonda` | 63 |
| `banchi/04-b25-tastiera.c` | 62 |
| `banchi/07-b64-scena.py` | 62 |
| `banchi/02-figlio-prova.py` | 61 |
| `banchi/02-codifica-immagine.py` | 60 |
| `banchi/17-t9` | 59 |
| `banchi/01-b0-bersaglio.sh` | 58 |
| `banchi/02-sessione-stato.py` | 58 |
| `banchi/13-w1-un-fotogramma.c` | 58 |
| `banchi/02-codifica-lancia.sh` | 57 |
| `banchi/02-cattura-lancia.sh` | 54 |
| `banchi/14-f1-forma.c` | 53 |
| `banchi/17-t8` | 51 |
| `banchi/01-b2-sonda-trasporto.py` | 50 |
| `banchi/01-b8-sblocca.py` | 50 |
| `banchi/02-sessione-lancia.sh` | 49 |
| `banchi/01-b8-lancia.sh` | 48 |
| `banchi/06-b33-terreno.sh` | 48 |
| `installatore/cmd` | 48 |
| `banchi/01-b2-sonda.html` | 47 |
| `banchi/01-b6-lancia.sh` | 47 |
| `banchi/06-b33-risveglio-giudice.py` | 47 |
| `banchi/07-b65-datagram.py` | 47 |
| `banchi/07-b64-orecchio.py` | 46 |
| `banchi/02-codifica-prova.c` | 44 |
| `banchi/02-pagina-sonda-codec.py` | 41 |
| `banchi/01-b0-terreno.sh` | 40 |
| `banchi/01-b11-lancia.sh` | 37 |
| `banchi/02-codifica-nal.py` | 37 |
| `banchi/02-pagina-misura-cdp.py` | 37 |
| `banchi/02-cattura-certifica.sh` | 36 |
| `banchi/01-s7-rotella.sh` | 35 |
| `banchi/01-b3-rcp-innesta.py` | 34 |
| `banchi/01-s7-rotella.c` | 34 |
| `banchi/01-b7-lancia.sh` | 31 |
| `banchi/attrezzi-allinea-prodotto.sh` | 31 |
| `banchi/02-codifica-obu.py` | 30 |
| `banchi/02-pam-lancia.sh` | 30 |
| `banchi/04-b25-guasti.c` | 30 |
| `banchi/01-b2-ngtcp2-wt-innesta.py` | 29 |
| `banchi/17-t6` | 29 |
| `banchi/01-b11-guasto-innesta.py` | 28 |
| `banchi/07-b64-terreno.sh` | 28 |
| `banchi/02-figlio-lancia.sh` | 26 |
| `banchi/06-b33-risveglio.sh` | 26 |
| `banchi/07-b46-marionette.py` | 26 |
| `banchi/17-t2` | 26 |
| `packaging/archivio` | 26 |
| `banchi/01-b11-guasto.sh` | 24 |
| `banchi/02-sessione-dispositivi.py` | 24 |
| `banchi/07-b42-giudice.py` | 24 |
| `banchi/01-b0-bersaglio.py` | 22 |
| `banchi/02-figlio-accendi.sh` | 21 |
| `banchi/02-sessione-guardia.sh` | 21 |
| `banchi/06-b33-risveglio-certifica.sh` | 20 |
| `banchi/01-b2-lancia-wt.sh` | 19 |
| `banchi/01-b5-lancia.sh` | 19 |
| `banchi/01-s7-pagina.html` | 19 |
| `banchi/02-filo-lancia.sh` | 19 |
| `banchi/02-pam-i3.py` | 19 |
| `banchi/06-b34-tabella.c` | 19 |
| `banchi/09-lucchetto.py` | 19 |
| `banchi/09-b81-terreno.sh` | 18 |
| `banchi/01-b2-cliente-aioquic.py` | 17 |
| `banchi/01-b4-lancia.py` | 17 |
| `packaging/rpm` | 15 |
| `banchi/00-sessione-gnome.sh` | 14 |
| `banchi/02-pam-accendi.sh` | 14 |
| `installatore/prove` | 14 |
| `banchi/01-casa-7448.sh` | 13 |
| `banchi/02-cattura-costruisci.sh` | 13 |
| `banchi/09-b79-terreno.sh` | 13 |
| `banchi/attrezzi-gruppi-scheda.sh` | 13 |
| `banchi/06-b33-risveglio-guasti.py` | 12 |
| `packaging/rilascio.sh` | 12 |
| `banchi/attrezzi-allinea-innesto.sh` | 11 |
| `banchi/attrezzi-utenti.sh` | 10 |
| `packaging/arch` | 10 |
| `banchi/01-b2-raccogli.py` | 8 |
| `banchi/02-codifica-costruisci.sh` | 8 |
| `banchi/04-b25-lancia.sh` | 8 |
| `packaging/motore` | 8 |
| `banchi/01-s7-raccogli.py` | 7 |
| `banchi/04-b28-lancia.sh` | 7 |
| `banchi/01-b2-costruisci-ngtcp2.sh` | 5 |
| `installatore/run.sh` | 5 |
| `banchi/01-b2-costruisci.sh` | 4 |
| `banchi/06-b5-esiti-cattura.sh` | 3 |
| `banchi/14-f1-forma.sh` | 3 |
| `installatore/costruisci.sh` | 3 |
| `banchi/06-b33-risveglio-costruisci.sh` | 2 |
| `banchi/04-in8-costruisci.sh` | 1 |
| `banchi/04-in8-parita.c` | 1 |
| `banchi/06-b33-costruisci.sh` | 1 |
| `installatore/catalogo` | 1 |

### Every collision and how it was resolved

| target | old names | winner | others → | scopes (first) |
|---|---|---|---|---|
| `Unlock` | `Sblocca` | (forbidden: Go method onto a well-known interface method (String, Error, Write…)) | **kept** | |
| `CARD` | `SCHEDA` | (name exists) | `GPU_CARD` | sh:banchi/17-distro/scatole/17-scatola.sh |
| `COMMAND` | `COMANDO` | (name exists) | `CMD` | lit:installer |
| `Check` | `Controlla`, `Controllo` | `Controllo` | `Controlla`→`Verify` | go-package:installatore/interfaccia; go-package:installatore/motore |
| `REFUSED` | `RIFIUTATA` | (name exists) | **kept** | lit:server |
| `SCENE` | `SCENA` | (name exists) | `SCENE_V` | py:banchi/04-b28-gesti.py |
| `Type` | `Tipo` | (name exists) | `Kind` | go-package:installatore/interfaccia/tui |
| `VERIFIED` | `VERIFICATA`, `VERIFICATO` | `VERIFICATA` | `VERIFICATO`→`CHECKED` | go-package:installatore/motore |
| `absent` | `assenti` | (name exists) | **kept** | lit:server |
| `actions` | `azioni` | (name exists) | `acts` | lit:banchi/16-stress/16-attore.py |
| `active` | `attiva` | (name exists) | `live` | lit:server |
| `add` | `agg`, `aggiungi` | `agg` | `aggiungi`→`insert` | go-package:installatore/motore |
| `alive` | `vivi`, `vivo` | `vivo` | `vivi`→`living` | py:banchi/16-stress/16-salita.py |
| `all` | `tutti` | (name exists) | `all_v` | py:banchi/01-b7-congedo.py; py:banchi/04-b28-gesti.py |
| `alpha` | `alfa` | (name exists) | `alpha_ch` | lit:banchi/16-stress/16-lavori.py |
| `app_requested` | `app_chiesti`, `app_chiesto` | `app_chiesto` | `app_chiesti`→`app_asked` | tu:banchi/rcp/rcp.c; tu:banchi/rcp/rcp.c |
| `arrived` | `arrivati`, `arrivato` | `arrivati` | `arrivato`→`landed` | tu:src/cattura.c |
| `body` | `corpo` | (name exists) | `body_el` | file:banchi/01-b11-pagina.html; file:banchi/01-b2-sonda.html |
| `box` | `scatola` | (name exists) | `container_box` | lit:banchi/16-stress/16-salita.py |
| `canvas` | `tela` | (name exists) | `canvas_size` | lit:server; lit:src/pagina.html |
| `capture` | `cattura` | (name exists) | `capture_v` | lit:server |
| `card` | `scheda` | (name exists) | `gpu_card` | lit:server; lit:src/figlio.c |
| `cause` | `causa` | (name exists) | `reason_why` | lit:banchi/09-b81-linea-morta.py |
| `chroma` | `croma` | (name exists) | `chroma_v` | tu:src/codificatore.c |
| `clipboard` | `appunti` | (name exists) | `clipboard_text` | lit:server |
| `code` | `codice` | (name exists) | `code_v` | file:src/pagina.html; file:src/pagina.html |
| `compliant` | `conforme` | (name exists) | `conformant` | lit:banchi/01-b4-registrazioni.py |
| `compute` | `calcolo` | (name exists) | `calc` | lit:banchi/16-stress/16-risorse.py |
| `consumed` | `consumati` | (name exists) | `used_up` | tu:src/webtransport.c |
| `copied` | `copia` | (name exists) | **kept** | lit:server |
| `count` | `conta`, `conto` | `conto` | `conta`→`tally` | c-program:banchi/18-a1; py:banchi/09-b70-ritmo.py |
| `cursor` | `cursore` | (name exists) | `pointer_shape` | lit:server |
| `data` | `dati` | (name exists) | `data_v` | file:banchi/16-stress/16-banco-tela.html; file:banchi/18-software/18-software-webcodecs.html |
| `delivered` | `consegnata` | (name exists) | `handed` | lit:server |
| `depth` | `profondita` | (name exists) | `bit_depth` | file:src/pagina.html |
| `drawing` | `disegno` | (name exists) | `drawing_v` | lit:banchi/16-stress/16-rapporto.py |
| `empty` | `vuota`, `vuoto` | `vuota` | `vuoto`→`blank` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py; tu:src/sessione.c |
| `env` | `amb` | (name exists) | `env_vars` | go-package:installatore/motore |
| `error` | `errore` | (name exists) | `failure` | lit:banchi/12-client-veri.py |
| `fake` | `finta`, `finto` | `finto` | `finta`→`mock` | lit:installatore/motore/finti_test.go; lit:installer |
| `found` | `trovati`, `trovato` | `trovati` | `trovato`→`located` | go-package:installatore/motore; tu:src/sessione.c |
| `full` | `pieni`, `pieno` | `pieno` | `pieni`→`filled` | py:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py |
| `got` | `otten` | (name exists) | `obt` | py:banchi/11-scatole/11-c14-non-si-disturbano.py |
| `green` | `verde` | (name exists) | `green_v` | lit:banchi/02-cattura-giudica.py |
| `group` | `gruppo` | (name exists) | `grp` | tu:src/figlio.c |
| `groups` | `gruppi` | (name exists) | `group_list` | lit:installatore/interfaccia/vista.go; lit:installer |
| `height` | `alt`, `altezza` | `altezza` | `alt`→`alt_h` | tu:banchi/01-b8-prova-ban.c; tu:banchi/04-b31-tela.c |
| `height` | `altezza` | (name exists) | `height_px` | file:src/pagina.html; file:src/pagina.html |
| `hex` | `esa` | (name exists) | `hex_s` | go-package:installatore/motore |
| `how_many` | `quante`, `quanti` | `quanti` | `quante`→`how_many_n` | file:banchi/01-b11-pagina.html; file:src/pagina.html |
| `judge` | `giudica`, `giudice` | `giudica` | `giudice`→`assessor` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py; py:banchi/11-scatole/11-c4-il-tasto-arriva-allo-schermo.py |
| `judged` | `giudicati`, `giudicato` | `giudicati` | `giudicato`→`assessed` | py:banchi/01-b4-validatore.py |
| `key` | `chiave` | (name exists) | `key_id` | lit:banchi/19-vulkan/19-tabella.py; lit:server |
| `last` | `ultima`, `ultimo` | `ultimo` | `ultima`→`latest` | py:banchi/09-b76-rete-cattiva.py; py:banchi/11-scatole/11-c8b-la-pagina-si-vede-dal-cliente.py |
| `late` | `tardive`, `tardivi` | `tardivi` | `tardive`→`belated` | lit:banchi/16-stress/16-attore.py |
| `layout` | `disposizione` | (name exists) | `arrangement` | tu:banchi/04-b25-guasti.c; tu:banchi/04-b25-tastiera.c |
| `left` | `sx` | (name exists) | `left_side` | file:src/pagina.html; lit:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py |
| `level_idc` | `livello_idc` | (name exists) | `lvl_idc` | tu:src/vadiretta.c; tu:src/vadiretta.c |
| `line` | `riga` | (name exists) | `row` | lit:server |
| `lines` | `righe` | (name exists) | `line_list` | py:docs/sources/build.py; py:docs/sources/technical/ch01_introduction.py |
| `list` | `elenco` | (name exists) | `listing` | py:banchi/02-figlio-prova.py; py:banchi/09-b76-rete-cattiva.py |
| `locks` | `lucchetti` | (name exists) | `lock_set` | go-package:installatore/motore |
| `log` | `registra` | (name exists) | `record` | sh:banchi/02-cattura-lancia.sh; sh:banchi/02-cattura-lancia.sh |
| `log` | `registro` | (name exists) | `logbook` | sh:banchi/01-b11-guasto.sh; sh:banchi/02-figlio-lancia.sh |
| `machine` | `macchina` | (name exists) | `host` | lit:banchi/16-stress/16-risorse.py |
| `margin` | `margine` | (name exists) | `headroom` | lit:banchi/09-b81-linea-morta.py |
| `measure` | `misura` | (name exists) | `gauge` | lit:banchi/15-suite/15-g1b-esplora.py |
| `method` | `metodo` | (name exists) | `meth` | file:grafica/sito-mockup/performance.html |
| `mode` | `modo` | (name exists) | `manner` | file:src/pagina.html |
| `mute` | `muti`, `muto` | `muto` | `muti`→`muted` | lit:banchi/09-b84-audio-silenzio.py; py:banchi/09-b81-linea-morta.py |
| `my_base` | `mia_base`, `mio_base` | `mio_base` | `mia_base`→`own_base` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py |
| `name` | `nome` | (name exists) | `label_name` | lit:installer; py:docs/sources/build.py |
| `network` | `rete` | (name exists) | `net` | lit:banchi/12-client-veri.py |
| `next` | `prossimo` | (name exists) | `upcoming` | py:banchi/16-stress/16-salita.py |
| `none` | `nessuno` | (name exists) | `nobody` | lit:server; lit:src/figlio.c |
| `note` | `nota` | (name exists) | `remark` | file:banchi/sonda/sonda-rcp.html; file:src/pagina.html |
| `now_ms` | `adesso_ms`, `ora_ms` | `ora_ms` | `adesso_ms`→`current_ms` | tu:src/figlio.c |
| `now_us` | `adesso_us`, `ora_us` | `ora_us` | `adesso_us`→`current_us` | c-program:src |
| `old` | `vecchio` | (name exists) | `prior` | lit:banchi/18-a1/18-a1-opus-senza-ffmpeg.c |
| `on` | `accesa` | (name exists) | `lit` | lit:banchi/09-b81-linea-morta.py |
| `on` | `accesa`, `acceso` | `acceso` | `accesa`→`lit` | lit:banchi/09-b81-linea-morta.py; py:banchi/09-b81-linea-morta.py |
| `on` | `acceso` | (name exists) | `lit` | lit:banchi/09-b81-linea-morta.py; lit:banchi/12-client-veri.py |
| `open` | `aperta` | (name exists) | `is_open` | lit:banchi/19-android/19-android.py; py:banchi/09-b79-cure.py |
| `open` | `aperta`, `aperte` | `aperta` | `aperte`→`opened` | lit:banchi/09-b78-apertura.py |
| `open` | `aperte` | (name exists) | `opened` | py:banchi/09-b78-apertura.py |
| `open` | `aperti` | (name exists) | `opened` | py:banchi/16-stress/16-attore.py |
| `other` | `altro` | (name exists) | `other_one` | lit:installer |
| `our` | `nostri`, `nostro` | `nostro` | `nostri`→`ours` | go-package:installatore/motore |
| `out` | `fuori` | (name exists) | `outside` | file:src/pagina.html; go-package:installatore/motore |
| `output` | `uscita` | (name exists) | `out_dir` | file:banchi/16-stress/16-banco-tela.html |
| `page` | `pagina` | (name exists) | `page_v` | py:docs/sources/build.py; py:docs/sources/technical/ch01_introduction.py |
| `pause` | `pausa` | (name exists) | `pause_v` | lit:banchi/15-suite/15-g2-scena.py; lit:banchi/16-stress/16-attore.py |
| `photo` | `foto` | (name exists) | `picture` | lit:banchi/15-suite/15-g1b-esplora.py |
| `pipe` | `tubo` | (name exists) | `pipe_fd` | tu:src/figlio.c |
| `pointer` | `puntatore` | (name exists) | `ptr` | lit:server |
| `policy` | `politica` | (name exists) | `policy_v` | lit:banchi/07-b64-scena.py |
| `print` | `stampa` | (name exists) | `print_out` | py:banchi/02-filo-validatore.py; py:banchi/04-b28-gesti.py |
| `profile` | `profilo` | (name exists) | `profile_v` | lit:banchi/09-b77-audio-riordino.py; lit:banchi/09-b79-cure.py |
| `r` | `erre` | (name exists) | `r_ch` | py:banchi/02-cattura-giudica.py |
| `rc_mode` | `modo_rc` | (name exists) | `manner_rc` | tu:src/codificatore.c |
| `reason` | `motivo` | (name exists) | `why_text` | file:banchi/01-b11-pagina.html; file:src/pagina.html |
| `reborn` | `rinasce`, `rinate` | `rinasce` | `rinate`→`respawned` | py:banchi/11-scatole/11-c24-l-esci-chiude-sempre.py |
| `received` | `ricevuti` | (name exists) | `received_n` | lit:banchi/07-b64-rete.py |
| `requested` | `chiesti`, `chiesto` | `chiesto` | `chiesti`→`asked` | file:src/pagina.html |
| `requests` | `richieste` | (name exists) | **kept** | lit:server |
| `restart` | `riparti` | (name exists) | **kept** | lit:server |
| `resume` | `riprendi` | (name exists) | `continue_it` | lit:installer |
| `round` | `il_giro` | (name exists) | `the_round` | py:banchi/11-scatole/11-c4-il-tasto-arriva-allo-schermo.py |
| `rule` | `regola` | (name exists) | `rule_v` | lit:banchi/09-b77-audio-riordino.py |
| `run` | `esegui`, `gira` | `gira` | `esegui`→`execute` | c-program:src; py:banchi/01-b8-cronometro.py |
| `said` | `detta`, `detto` | `detto` | `detta`→`stated` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py |
| `said` | `detti`, `detto` | `detto` | `detti`→`stated` | go-package:installatore/motore |
| `save` | `salva` | (name exists) | `store` | py:banchi/15-suite/15-f003-lo-schermo-si-aggiorna.py |
| `scale` | `scala` | (name exists) | `scale_v` | py:banchi/02-sessione-stato.py |
| `seen` | `visto` | (name exists) | `seen_v` | lit:banchi/02-filo-fotogramma.py; lit:banchi/15-suite/15-f008-modificatori.py |
| `sent` | `mandati`, `spedite` | `spedite` | `mandati`→`dispatched` | file:src/pagina.html |
| `serial` | `matricola` | (name exists) | `serial_no` | tu:src/figlio.c; tu:src/figlio.c |
| `serial` | `matricola`, `serie` | `serie` | `matricola`→`serial_no` | tu:src/figlio.c |
| `serial` | `serie` | (name exists) | `series` | tu:src/figlio.c; tu:src/wlroots.c |
| `session` | `sessione` | (name exists) | `session_v` | lit:server |
| `sorted` | `ordinata` | (name exists) | `ordered` | py:banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py |
| `sorted` | `ordinate` | (name exists) | `ordered` | py:banchi/09-b81-linea-morta.py |
| `sorted` | `ordinati` | (name exists) | `ordered` | py:banchi/01-b3-cliente.py; py:banchi/07-b64-orecchio.py |
| `start` | `inizio`, `partenza` | `inizio` | `partenza`→`departure` | lit:banchi/19-android/19-android.py |
| `stop` | `ferma` | (name exists) | `halt` | py:banchi/15-suite/15-g8-comune.py |
| `stopped` | `fermato`, `fermo` | `fermo` | `fermato`→`halted` | file:src/pagina.html |
| `stream` | `flusso` | (name exists) | `flow` | file:src/pagina.html; sh:banchi/18-scheda/18-confronto.sh |
| `streams` | `flussi` | (name exists) | `flows` | lit:banchi/02-filo-validatore.py |
| `tag` | `sigla` | (name exists) | `code_tag` | py:banchi/15-suite/15-f014-appunti.py |
| `taken` | `presi`, `preso` | `preso` | `presi`→`grabbed` | py:banchi/09-b81-linea-morta.py; tu:src/cattura.c |
| `text` | `testo` | (name exists) | `body_text` | lit:banchi/12-client-veri.py; py:docs/sources/technical/ch15_installer.py |
| `title` | `titolo` | (name exists) | `heading` | lit:banchi/02-pagina-misura-cdp.py; py:docs/sources/build.py |
| `touch` | `tocco` | (name exists) | `tap` | lit:server; lit:src/pagina.html |
| `unknown` | `ignote` | (name exists) | `unrecognized` | lit:banchi/02-sessione-stato.py |
| `user` | `utente` | (name exists) | `username` | lit:server |
| `value` | `valore` | (name exists) | `value_v` | file:src/pagina.html; file:src/pagina.html |
| `version` | `versione` | (name exists) | `version_v` | lit:installer |
| `versions` | `versioni` | (name exists) | `vers` | lit:installer |
| `wait_stage` | `aspetta_il_palco`, `attesa_palco` | `attesa_palco` | `aspetta_il_palco`→`await_stage` | py:banchi/11-scatole/11-c8b-la-pagina-si-vede-dal-cliente.py |
| `wanted` | `voluti`, `voluto` | `voluto` | `voluti`→`desired` | tu:src/vulkanvideo.c |
| `wheel` | `rotella` | (name exists) | `scroll_wheel` | lit:banchi/16-stress/16-attore.py; lit:server |
| `which` | `quale`, `quali` | `quale` | `quali`→`which_ones` | tu:src/figlio.c; tu:src/main.c |
| `why` | `perche` | (name exists) | `reason_text` | lit:installer |
| `width` | `larghezza` | (name exists) | `width_px` | file:src/pagina.html; file:src/pagina.html |
| `window` | `finestra` | (name exists) | `win` | file:src/pagina.html; lit:banchi/16-stress/16-classifica.py |
| `write` | `scrivi` | (name exists) | `put_out` | tu:src/figlio.c |
| `yes` | `si` | (name exists) | **kept** | lit:server; lit:src/pagina.html |
| `lit` | `accesa`, `acceso` | `acceso` | `accesa`→`switched_on` | lit:banchi/09-b81-linea-morta.py; py:banchi/09-b81-linea-morta.py |

### One new name for several old names, never in one scope (checked per scope, §3)

- `ALL` ← `TUTTE`, `TUTTI`
- `Blocked` ← `Bloccata`, `Bloccato`
- `CELLS` ← `CASELLE`, `CELLE`
- `DIFFERENT` ← `DIVERSI`, `DIVERSO`
- `DIRTY` ← `SPORCA`, `SPORCO`
- `DONE` ← `FATTA`, `FATTE`, `FATTI`, `FATTO`
- `EMPTY` ← `VUOTA`, `VUOTO`
- `EXCLUDED` ← `ESCLUSE`, `ESCLUSI`
- `EXPECTED` ← `ATT`, `ATTESO`
- `Excluded` ← `Esclusa`, `Escluse`
- `FAILED` ← `FALLITA`, `FALLITI`
- `FORBIDDEN` ← `VIETATA`, `VIETATE`
- `FOUND` ← `TROVATI`, `TROVATO`
- `Fake` ← `Finta`, `Finto`
- `Graphical` ← `Grafica`, `Grafici`
- `HEALTHY` ← `SANI`, `SANO`
- `HOW_MANY` ← `QUANTE`, `QUANTI`
- `INSIDE_SRC` ← `DENTRO_SORG`, `DENTRO_SRC`
- `LEFT` ← `SINISTRA`, `SINISTRO`
- `LOCK` ← `LUCCHETTO`, `SERRATURA`
- `MIN_FRAMES` ← `FOTOGRAMMI_MINIMI`, `MINIMO_FOTOGRAMMI`
- `MISSING` ← `MANCA`, `MANCANO`, `MANCANTI`
- `NEW` ← `NUOVA`, `NUOVE`, `NUOVI`, `NUOVO`
- `OUR` ← `NOSTRE`, `NOSTRO`
- `READY` ← `PRONTA`, `PRONTO`
- `RIGHT` ← `DESTRA`, `DESTRO`
- `SEEN` ← `VISTI`, `VISTO`
- `SOURCE` ← `FONTE`, `SORGENTE`
- `SOURCES` ← `FONTI`, `SORGENTI`
- `STOPPED` ← `FERMATA`, `FERMO`
- `Screen` ← `Schermata`, `Schermo`
- `Stopped` ← `Fermata`, `Fermo`
- `TREE` ← `ALB`, `ALBERO`
- `TWIN` ← `GEMELLA`, `GEMELLO`
- `UNKNOWN` ← `IGNOTI`, `IGNOTO`, `NONSO`, `SCONOSCIUTO`
- `Unknown` ← `Ignota`, `Sconosciuto`
- `WATCHED` ← `GUARDATI`, `SORVEGLIATE`
- `_Fake` ← `_Finta`, `_Finto`
- `_empty` ← `_svuota`, `_vuoto`
- `_limit` ← `_limita`, `_limite`
- `_path` ← `_cammino`, `_perc`
- `_read` ← `_leggi`, `_letta`
- `_round` ← `_giro`, `_tondo`
- `accepted` ← `accettata`, `accettato`, `amm`
- `access` ← `accesso`, `un_accesso`
- `active` ← `attivi`, `attivo`
- `added` ← `aggiunta`, `aggiunti`
- `app_log` ← `app_diario`, `registro_applicazione`
- `app_received` ← `app_ricevuti`, `app_ricevuto`
- `arrived` ← `arrivata`, `arrivate`, `arrivati`
- `attached` ← `attaccate`, `attaccato`
- `attempt` ← `tenta`, `tentativo`, `un_tentativo`
- `backlog` ← `arretrati`, `arretrato`
- `bad` ← `cattive`, `cattivo`
- `bands` ← `bande`, `fasce`
- `bare` ← `nuda`, `nudo`
- `best` ← `migliore`, `migliori`
- `blind` ← `cieca`, `ciechi`, `cieco`
- `block` ← `blocca`, `blocco`
- `blocked` ← `bloccata`, `bloccate`, `bloccati`, `bloccato`
- `border` ← `cornice`, `incornicia`
- `born` ← `nata`, `nate`, `nati`, `nato`
- `broken` ← `guasta`, `rotta`, `rotte`, `rotti`, `rotto`
- `call` ← `chiama`, `chiamata`
- `canvases` ← `telate`, `tele`
- `cards` ← `carte`, `schede`
- `cell` ← `casella`, `cella`
- `cells` ← `caselle`, `celle`
- `changed` ← `cambiate`, `cambiati`, `cambiato`
- `check` ← `controlla`, `controllo`
- `checks` ← `controlli`, `verifiche`
- `chosen` ← `scelti`, `scelto`
- `clean` ← `pulisci`, `pulita`, `pulito`
- `clear_out` ← `sgombera`, `sgombra`
- `closed` ← `chiuse`, `chiuso`
- `common` ← `comune`, `comuni`
- `correct` ← `corretti`, `giusti`, `giusto`
- `counts` ← `conteggi`, `conti`
- `covered` ← `coperte`, `coperti`
- `created` ← `creati`, `creato`
- `cut` ← `tagliate`, `tagliati`, `taglio`
- `dead` ← `morti`, `morto`
- `declared` ← `dich`, `dichiarata`, `dichiarate`, `dichiarati`
- `decoded` ← `decodificati`, `decodificato`
- `delay` ← `rit`, `ritardo`
- `delay_ms` ← `rit_ms`, `ritardo_ms`
- `delivered` ← `consegnate`, `consegnati`, `consegnato`
- `dirty` ← `sporca`, `sporche`, `sporchi`, `sporco`
- `discarded` ← `buttato`, `scartate`, `scartati`
- `dismissed` ← `congedate`, `congedato`
- `divergent` ← `divergente`, `divergenti`
- `drop` ← `butta`, `caduta`
- `dropped` ← `buttati`, `caduto`
- `due` ← `dovuti`, `esigibile`
- `duplicates` ← `doppi`, `doppioni`, `duplicati`
- `elapsed` ← `trascorsi`, `trascorso`
- `empty` ← `vuota`, `vuote`, `vuoti`
- `enter` ← `entra`, `entrano`
- `entered` ← `entrati`, `entrato`
- `entry` ← `entrata`, `voce`
- `estimate` ← `preventivo`, `stima`
- `exceeded` ← `sforato`, `superato`
- `excluded` ← `esclusi`, `escluso`
- `expected_s` ← `att_s`, `previsti_s`
- `expected_v` ← `att_v`, `atteso_v`
- `expired` ← `scaduta`, `scaduti`, `scaduto`
- `explicit` ← `esplicita`, `esplicito`
- `factor` ← `fatt`, `fattore`
- `failed` ← `fallita`, `falliti`
- `fake` ← `finte`, `finto`
- `finished` ← `fatto`, `finiti`, `finito`
- `first` ← `primi`, `primo`
- `fit_canvas` ← `adatta_la_tela`, `adatta_tela`
- `fixed` ← `fissa`, `sistemati`
- `flat` ← `piatta`, `piatto`
- `forbidden` ← `vietata`, `vietate`
- `forced` ← `forzata`, `obbligate`
- `found` ← `trovate`, `trovati`
- `fourth` ← `quarta`, `quarto`
- `fourth_admitted` ← `quarta_amm`, `quarto_ammesso`
- `frame` ← `fot`, `fotogramma`
- `frames` ← `fotogrammi`, `quadri`
- `fresh` ← `fresco`, `nuovo`
- `full` ← `piena`, `pieno`
- `good` ← `buone`, `buono`
- `got` ← `avuta`, `avuti`, `avuto`
- `graft` ← `innesta`, `innesto`
- `grafted` ← `innestati`, `innestato`
- `graphical` ← `grafica`, `grafico`
- `gray` ← `grigia`, `grigio`
- `healed` ← `risanati`, `risanato`
- `held` ← `trattenuti`, `trattenuto`
- `here` ← `qua`, `qui`
- `hidden` ← `nascoste`, `nascosto`
- `hints` ← `sugg`, `suggerimenti`
- `holds` ← `regge`, `tiene`
- `hook` ← `aggancia`, `gancio`
- `how_many_before` ← `quante_prima`, `quanti_prima`
- `identifier` ← `identificativo`, `identificatore`
- `installed` ← `installati`, `installato`
- `internal` ← `interna`, `interno`
- `is_visible` ← `si_vede`, `visibile`
- `its` ← `sua`, `suo`
- `judge` ← `giud`, `giudica`
- `judge_exit` ← `giudica_uscita`, `uscita_giud`
- `judge_round` ← `giudica_giro`, `giudica_il_giro`
- `kept` ← `tenuti`, `tenuto`
- `keys` ← `chiavi`, `tasti`
- `killed` ← `uccisi`, `ucciso`
- `kind` ← `specie`, `tipo`
- `known` ← `noti`, `noto`
- `last` ← `ultime`, `ultimo`
- `late` ← `tardi`, `tardivi`, `tardo`
- `left` ← `rimaste`, `rimasto`
- `limit` ← `limita`, `limite`
- `listen` ← `ascolta`, `ascolto`
- `load` ← `carica`, `carico`
- `loaded` ← `caricate`, `caricato`
- `lock` ← `lucchetto`, `serratura`
- `long` ← `lunga`, `lungo`
- `lost` ← `perdute`, `perduti`, `perse`, `persi`
- `low` ← `bassi`, `basso`
- `mark` ← `marca`, `segna`
- `measured` ← `misurati`, `misurato`
- `missed` ← `mancate`, `mancati`
- `missing` ← `manca`, `mancano`
- `move` ← `mossa`, `sposta`
- `moved` ← `mosso`, `spostati`, `spostato`
- `my` ← `mia`, `mie`, `miei`, `mio`
- `near` ← `vicine`, `vicino`
- `needs` ← `esigenze`, `serve`
- `negotiated` ← `negoziata`, `negoziato`
- `next_ingress` ← `prossima_ingresso`, `prossimo_ingresso`
- `next_key` ← `prossima_chiave`, `prossimo_chiave`
- `next_serial` ← `prossima_matricola`, `prossimo_serial`
- `observed` ← `osservati`, `osservato`
- `obtained` ← `ottenuti`, `ottenuto`
- `off` ← `spenti`, `spento`
- `offer` ← `offerta`, `offri`
- `opened` ← `aperte`, `aperti`
- `ordered` ← `ordinata`, `ordinate`, `ordinati`
- `others` ← `altri`, `altrui`
- `our` ← `nostra`, `nostro`
- `overall` ← `complessivo`, `tutto`
- `overflowed` ← `traboccati`, `traboccato`
- `passed` ← `passata`, `passati`
- `path` ← `il_percorso`, `perc`
- `pending` ← `pendenti`, `sospesi`
- `placed` ← `messa`, `messi`
- `possible` ← `possibile`, `possibili`
- `prepare` ← `prepara`, `preparati`
- `pressed` ← `premuti`, `premuto`
- `prev` ← `prec`, `ult`
- `primary` ← `primario`, `principale`
- `queue` ← `coda`, `la_coda`
- `quiet` ← `quiete`, `tranquillo`, `zitto`
- `raw` ← `crudo`, `grezzo`
- `read` ← `lette`, `letto`
- `read_log` ← `leggi_il_registro`, `leggi_registro`
- `read_notebook` ← `leggi_il_quaderno`, `leggi_quaderno`
- `read_text` ← `leggi_il_testo`, `leggi_testo`
- `readings` ← `letti`, `letture`
- `ready` ← `pronta`, `pronti`, `pronto`
- `real` ← `vera`, `vero`
- `rearms` ← `riarma`, `riarmi`
- `reasons` ← `motivi`, `ragioni`
- `reborn` ← `rinasce`, `rinata`, `rinato`
- `recovered` ← `recuperati`, `ritrovato`
- `rect` ← `rett`, `riquadro`
- `red` ← `rosse`, `rosso`
- `refused` ← `rifiutata`, `rifiutate`, `rifiutati`, `rifiutato`
- `remaining` ← `restanti`, `rimasti`
- `removed` ← `tolta`, `tolte`, `tolti`
- `requested_height` ← `chiesta_altezza`, `chiesto_altezza`
- `requested_width` ← `chiesta_larghezza`, `chiesto_larghezza`
- `reread` ← `riletta`, `riletto`
- `resize` ← `ridim`, `ridimensiona`
- `restart` ← `riavvio`, `ripartenza`
- `restore` ← `rimetti`, `ripristina`
- `restored` ← `rimessa`, `rimessi`, `rimesso`
- `resumed` ← `ripresa`, `riprese`
- `returned` ← `tornate`, `tornato`
- `right` ← `destro`, `dx`
- `run` ← `corsa`, `gira`
- `sample` ← `campiona`, `campione`
- `saved` ← `salvate`, `salvato`
- `scroll` ← `scorri`, `scorrimento`
- `search` ← `cerca`, `ricerca`
- `search_window` ← `cerca_finestra`, `cerca_la_finestra`
- `searched` ← `cercati`, `cercato`
- `second` ← `seconda`, `secondo`
- `send_button` ← `manda_bottone`, `manda_pulsante`
- `shift` ← `maiusc`, `spost`
- `short` ← `corta`, `corte`, `corti`
- `silence` ← `silenzio`, `zittisci`
- `skip` ← `salta`, `saltare`
- `slow` ← `lente`, `lento`
- `small` ← `piccola`, `piccoli`, `piccolo`
- `snapshot` ← `fotografa`, `fotografia`
- `source` ← `fonte`, `sorgente`
- `sources` ← `fonti`, `sorgenti`
- `start` ← `avvia`, `inizio`
- `started` ← `avviato`, `partita`, `partito`
- `starts` ← `comincia`, `inizi`
- `stated` ← `detta`, `detti`
- `still` ← `ancora`, `ancora_li`, `immobili`
- `stop` ← `fermare`, `smetti`
- `stopped` ← `fermate`, `ferme`, `fermo`
- `succeeded` ← `riuscita`, `riuscito`
- `summary` ← `riassunto`, `sommario`
- `swap` ← `scambia`, `scambio`
- `t_before` ← `t_prima`, `tprima`
- `table` ← `tabella`, `tavola`
- `take` ← `prendi`, `presa`
- `taken` ← `prese`, `preso`
- `tenant` ← `inquilino`, `un_inquilino`
- `text_line` ← `linea`, `riga_testo`
- `tight` ← `serrate`, `stretta`, `strette`, `stretto`
- `times` ← `tempi`, `volte`
- `tolerated` ← `tollerate`, `tollerato`
- `tool` ← `arnese`, `attrezzo`
- `touches` ← `tocca`, `tocchi`
- `transform` ← `trasf`, `trasformazione`
- `trusted` ← `fidati`, `fidato`
- `turn_off_server` ← `spegni_server`, `spegni_servitore`
- `turn_on_scene` ← `accendi_la_scena`, `accendi_scena`
- `ugly` ← `brutte`, `brutti`
- `unknown` ← `ignoti`, `ignoto`, `sconosciute`
- `untried` ← `non_provate`, `non_provati`
- `unwanted` ← `di_troppo`, `non_ci_vuole`
- `updated` ← `aggiornati`, `aggiornato`
- `used` ← `usata`, `usato`
- `valid` ← `valida`, `valide`, `validi`, `valido`
- `vendor` ← `fornitore`, `venditore`
- `wait_canvas` ← `aspetta_tela`, `attendi_tela`, `attesa_tela`
- `wait_line` ← `aspetta_la_riga`, `aspetta_riga`, `attendi_riga`
- `wait_scene` ← `aspetta_la_scena`, `aspetta_scena`, `attesa_scena`
- `watched` ← `guardati`, `sorvegliata`
- `whole` ← `intero`, `tutta`
- `without_header` ← `senza_header`, `senza_intestazione`
- `worst` ← `peggiore`, `peggiori`
- `write_log` ← `scrivi_reg`, `scrivi_registro`
- `written` ← `scritta`, `scritte`, `scritti`
- `wrong` ← `sbagliata`, `sbagliate`, `sbagliati`, `storti`, `storto`

### Names not renamed (to resolve in interi.tsv or sinonimi.tsv)

- `Amb` — untagged JSON field: its English is two words, the key cannot follow
- `Motivo` — untagged JSON field: its English is two words, the key cannot follow
- `RIFIUTATA` — target REFUSED already exists in lit:server
- `Sblocca` — target Unlock is a Go method onto a well-known interface method (String, Error, Write…)
- `amb` — untagged JSON field Amb: its English is two words
- `assenti` — target absent already exists in lit:server
- `copia` — target copied already exists in lit:server
- `motivo` — untagged JSON field Motivo: its English is two words
- `richieste` — target requests already exists in lit:server
- `riparti` — target restart already exists in lit:server
- `si` — target yes already exists in lit:server, lit:src/pagina.html

### Names left out on purpose

- `AltLeft` — interi.tsv: kept as it is (KeyboardEvent.code "AltLeft" (key map), not Italian: must not change)
- `AltRight` — interi.tsv: kept as it is (KeyboardEvent.code "AltRight" (key map), not Italian: must not change)
- `DX` — interi.tsv: kept as it is (delta x in 15-f003 (and a mockup const), not destra: must not change)
- `NID_subject_alt_name` — defined outside the project (C headers)
- `NonConvert` — a Web platform name (esterni-web.txt, or shown by a page: event member, .code/.key value, attribute)
- `OPUS_SET_PACKET_LOSS_PERC` — defined outside the project (C headers)
- `catalogo` — a Go package name: renamed with its directory (step 2)
- `interfaccia` — a Go package name: renamed with its directory (step 2)
- `locale` — a Web platform name (esterni-web.txt, or shown by a page: event member, .code/.key value, attribute)
- `locale_t` — defined outside the project (C headers)
- `motore` — a Go package name: renamed with its directory (step 2)
- `rx_apri` — interi.tsv: kept as it is (wasm export of opus.wasm: the embedded blob keeps it until the wasm is rebuilt; the JS member is never "ours" so it would not follow)
- `rx_decodifica` — interi.tsv: kept as it is (wasm export of opus.wasm (as rx_apri))
- `rx_pacchetto` — interi.tsv: kept as it is (wasm export of opus.wasm (as rx_apri))
- `rx_pacchetto_max` — interi.tsv: kept as it is (wasm export of opus.wasm (as rx_apri))
- `rx_uscita` — interi.tsv: kept as it is (wasm export of opus.wasm (as rx_apri))

### Cross-language contracts (every place: rinomina2-plan.json → contracts)

| kind | names |
|---|---|
| crosses languages | 2269 |
| data name | 73 |
| environment variable | 82 |
| option / subcommand / kebab name | 293 |

The names below are the ones another program reads by spelling: data names, environment variables, options and kebab names.  The 2269 code names that merely occur in two languages are in the JSON only.

| old | new | kind | languages | places |
|---|---|---|---|---|
| `ACCETTATA` | `ACCEPTED` | data name (dati.tsv: log-text) | c,py | 5 |
| `APPUNTI_ANNUNCIO` | `CLIPBOARD_ANNOUNCE` | data name (dati.tsv: log-text) | c,html,py | 24 |
| `APPUNTI_CHIEDI` | `CLIPBOARD_ASK` | data name (dati.tsv: log-text) | c,html,py | 36 |
| `APPUNTI_TESTO` | `CLIPBOARD_TEXT` | data name (dati.tsv: log-text) | c,html,py | 37 |
| `BANCO_MARCA` | `BENCH_MARK` | data name (dati.tsv: log-text) | c,py | 34 |
| `BOTTONE` | `BUTTON` | data name (dati.tsv: json-value) | c,py | 3 |
| `BUCHI` | `HOLES` | data name (dati.tsv: log-marker) | html,py | 12 |
| `BUDGET_PIENO` | `BUDGET_FULL` | data name (dati.tsv: reason) | c,html,py | 20 |
| `COMPOSITORE_INCAPACE` | `COMPOSITOR_UNABLE` | data name (dati.tsv: log-text) | c,html,py | 36 |
| `CONFORME` | `COMPLIANT` | data name (dati.tsv: json-value) | html,sh | 5 |
| `DISPOSIZIONE` | `LAYOUT` | data name (dati.tsv: log-text) | c,py | 37 |
| `F18ESITO` | `F18OUTCOME` | data name (dati.tsv: log-marker) | html,py | 4 |
| `FUNZIONE_SPENTA` | `FUNCTION_OFF` | data name (dati.tsv: log-text) | c,py | 9 |
| `GIA_ATTIVA_LOCALE` | `ALREADY_ACTIVE_LOCAL` | data name (dati.tsv: reason) | c,html,py | 16 |
| `INATTIVITA` | `INACTIVITY` | data name (dati.tsv: reason) | c,html,py | 10 |
| `MISURA_FUORI_LIMITI` | `SIZE_OUT_OF_LIMITS` | data name (dati.tsv: log-text) | c,html,py | 29 |
| `NON-BANNATO` | `NOT-BANNED` | data name (dati.tsv: wire-string) | c,py,sh | 39 |
| `NON-CAPITO` | `NOT-UNDERSTOOD` | data name (dati.tsv: socket-cmd) | c,py | 7 |
| `NON-CONFORME` | `NON-COMPLIANT` | data name (dati.tsv: json-value) | html,sh | 11 |
| `NON_ORA` | `NOT_NOW` | data name (dati.tsv: log-text) | c,html,py | 74 |
| `REMOTIX_16_CHROME_IN_PIU` | `REMOTIX_16_CHROME_EXTRA` | environment variable | py | 2 |
| `REMOTIX_16_DESKTOP_DOPO` | `REMOTIX_16_DESKTOP_AFTER` | environment variable | sh | 3 |
| `REMOTIX_16_IN_PIU` | `REMOTIX_16_EXTRA` | environment variable | sh | 3 |
| `REMOTIX_16_MISURE` | `REMOTIX_16_MEASURES` | environment variable | sh | 2 |
| `REMOTIX_16_SISTEMA` | `REMOTIX_16_SYSTEM` | environment variable | py,sh | 3 |
| `REMOTIX_AIUTANTE_H` | `REMOTIX_HELPER_H` | environment variable | c | 2 |
| `REMOTIX_ANDROID_PACCHETTO` | `REMOTIX_ANDROID_PACKAGE` | environment variable | py | 2 |
| `REMOTIX_APPUNTI_H` | `REMOTIX_CLIPBOARD_H` | environment variable | c | 2 |
| `REMOTIX_APPUNTI_KDE_H` | `REMOTIX_CLIPBOARD_KDE_H` | environment variable | c | 2 |
| `REMOTIX_ATTESA_CHIAMATA_S` | `REMOTIX_CALL_WAIT_S` | environment variable | py | 1 |
| `REMOTIX_BANCHI` | `REMOTIX_BENCHES` | environment variable | py,sh | 3 |
| `REMOTIX_BANCHI_VERI` | `REMOTIX_REAL_BENCHES` | environment variable | sh | 1 |
| `REMOTIX_CATTURA_H` | `REMOTIX_CAPTURE_H` | environment variable | c | 2 |
| `REMOTIX_CERTIFICATI_H` | `REMOTIX_CERTIFICATES_H` | environment variable | c | 2 |
| `REMOTIX_CHROME_OPZIONI` | `REMOTIX_CHROME_OPTIONS` | environment variable | py,sh | 17 |
| `REMOTIX_CLASSICO` | `REMOTIX_CLASSIC` | environment variable | html,py | 13 |
| `REMOTIX_CODIFICATORE_H` | `REMOTIX_ENCODER_H` | environment variable | c | 2 |
| `REMOTIX_COLORI709_H` | `REMOTIX_COLORS709_H` | environment variable | c | 2 |
| `REMOTIX_COMANDO_H` | `REMOTIX_COMMAND_H` | environment variable | c | 2 |
| `REMOTIX_CONTROLLO` | `REMOTIX_CHECK` | environment variable | py,sh | 7 |
| `REMOTIX_CONTROLLO_ANDROID` | `REMOTIX_CHECK_ANDROID` | environment variable | py | 1 |
| `REMOTIX_CURSORE_H` | `REMOTIX_CURSOR_H` | environment variable | c | 3 |
| `REMOTIX_FIGLIO_H` | `REMOTIX_CHILD_H` | environment variable | c | 2 |
| `REMOTIX_FORMA_H` | `REMOTIX_SHAPE_H` | environment variable | c | 3 |
| `REMOTIX_INQUILINO` | `REMOTIX_TENANT` | environment variable | c,conf,py | 18 |
| `REMOTIX_MISURE_15` | `REMOTIX_MEASURES_15` | environment variable | py | 2 |
| `REMOTIX_MISURE_16` | `REMOTIX_MEASURES_16` | environment variable | py | 1 |
| `REMOTIX_MISURE_ANDROID` | `REMOTIX_MEASURES_ANDROID` | environment variable | py | 1 |
| `REMOTIX_OPZIONI` | `REMOTIX_OPTIONS` | environment variable | conf,py,sh | 28 |
| `REMOTIX_PAGINA_H` | `REMOTIX_PAGE_H` | environment variable | c | 2 |
| `REMOTIX_PAROLA` | `REMOTIX_PASSWORD` | environment variable | py | 6 |
| `REMOTIX_PAROLA_PROVA` | `REMOTIX_TEST_PASSWORD` | environment variable | sh | 12 |
| `REMOTIX_PAROLA_SUDO` | `REMOTIX_SUDO_PASSWORD` | environment variable | py,sh | 20 |
| `REMOTIX_PASSAGGIO16` | `REMOTIX_HANDOFF16` | environment variable | py | 1 |
| `REMOTIX_PORTA` | `REMOTIX_PORT` | environment variable | conf,go,py,sh | 25 |
| `REMOTIX_PRODOTTO_16` | `REMOTIX_PRODUCT_16` | environment variable | py | 1 |
| `REMOTIX_PROVA_FIGLIO` | `REMOTIX_TEST_CHILD` | environment variable | go,py | 5 |
| `REMOTIX_PUNTATORE` | `REMOTIX_POINTER` | environment variable | html,py | 29 |
| `REMOTIX_REGISTRO_H` | `REMOTIX_LOG_H` | environment variable | c | 2 |
| `REMOTIX_RETE11` | `REMOTIX_NETWORK11` | environment variable | py | 1 |
| `REMOTIX_RITROVO_H` | `REMOTIX_FINDING_AGAIN_H` | environment variable | c | 2 |
| `REMOTIX_SCATOLE_TENUTE` | `REMOTIX_KEPT_BOXES` | environment variable | py,sh | 13 |
| `REMOTIX_SCHEDA` | `REMOTIX_CARD` | environment variable | py,sh | 18 |
| `REMOTIX_SCHERMO_ANNIDATO` | `REMOTIX_NESTED_SCREEN` | environment variable | py,sh | 14 |
| `REMOTIX_SCORCIATOIE` | `REMOTIX_SHORTCUTS` | environment variable | html,py | 4 |
| `REMOTIX_SCRITTORE_BIT_H` | `REMOTIX_WRITER_BIT_H` | environment variable | c | 2 |
| `REMOTIX_SENTINELLA_H` | `REMOTIX_SENTINEL_H` | environment variable | c | 2 |
| `REMOTIX_SESSIONE_H` | `REMOTIX_SESSION_H` | environment variable | c | 2 |
| `REMOTIX_SGOMBRA_SOGLIA_MS` | `REMOTIX_CLEAR_THRESHOLD_MS` | environment variable | c,py | 3 |
| `REMOTIX_SISTEMA_15` | `REMOTIX_SYSTEM_15` | environment variable | py | 2 |
| `REMOTIX_SPORTELLO_PARLA` | `REMOTIX_ENDPOINT_SPEAKS` | environment variable | py | 1 |
| `REMOTIX_SUL_SERVER` | `REMOTIX_ON_SERVER` | environment variable | py,sh | 25 |
| `REMOTIX_SUONO_H` | `REMOTIX_SOUND_H` | environment variable | c | 2 |
| `REMOTIX_TASTIERA_H` | `REMOTIX_KEYBOARD_H` | environment variable | c | 3 |
| `REMOTIX_TELEFONO` | `REMOTIX_PHONE` | environment variable | py | 6 |
| `REMOTIX_TELEFONO_A_SECCO` | `REMOTIX_PHONE_DRY_RUN` | environment variable | py | 2 |
| `REMOTIX_TELEFONO_CDP` | `REMOTIX_PHONE_CDP` | environment variable | py | 3 |
| `REMOTIX_TELEFONO_HOST` | `REMOTIX_PHONE_HOST` | environment variable | py | 4 |
| `REMOTIX_TELEFONO_SPORTELLO` | `REMOTIX_PHONE_ENDPOINT` | environment variable | py | 3 |
| `REMOTIX_TETTO` | `REMOTIX_CAP` | environment variable | py | 5 |
| `REMOTIX_TETTO_SESSIONI` | `REMOTIX_SESSION_CAP` | environment variable | py,sh | 7 |
| `REMOTIX_TRASPORTO_H` | `REMOTIX_TRANSPORT_H` | environment variable | c | 2 |
| `REMOTIX_UTENTE_VERI` | `REMOTIX_REAL_USER` | environment variable | sh | 1 |
| `REMOTIX_VADIRETTA_H` | `REMOTIX_VADIRECT_H` | environment variable | c | 2 |
| `REMOTIX_VIVI` | `REMOTIX_ALIVE` | environment variable | sh | 1 |
| `REMOTIX_VULKAN_CONVERSIONE` | `REMOTIX_VULKAN_CONVERSION` | environment variable | c,py | 5 |
| `REMOTIX_WAYLAND_VERI` | `REMOTIX_REAL_WAYLAND` | environment variable | py,sh | 5 |
| `RIPRESA` | `RESUMED` | data name (dati.tsv: log-text) | c,html,py | 19 |
| `RITARDO_FUORI_LIMITI` | `DELAY_OUT_OF_LIMITS` | data name (dati.tsv: log-text) | c,py | 7 |
| `RX_ISO_ATTESA` | `RX_ISO_WAIT` | environment variable | sh | 1 |
| `RX_ISO_SOLO_PREPARA` | `RX_ISO_PREPARE_ONLY` | environment variable | sh | 2 |
| `RX_PERC` | `RX_PATH` | environment variable | py | 2 |
| `RX_REVISIONE` | `RX_REVISION` | environment variable | conf,py,sh | 15 |
| `RX_RIGA` | `RX_LINE` | environment variable | py | 2 |
| `RX_RILASCIO` | `RX_RELEASE` | environment variable | sh | 2 |
| `RX_RIPR` | `RX_RESUME` | environment variable | py | 2 |
| `RX_SELINUX_PERMISSIVO` | `RX_SELINUX_PERMISSIVE` | environment variable | conf,sh | 2 |
| `RX_SPORCO` | `RX_DIRTY` | environment variable | py,sh | 5 |
| `RX_VERSIONE` | `RX_VERSION` | environment variable | conf,py,sh | 25 |
| `RX_VM_CATTURA` | `RX_VM_CAPTURE` | environment variable | sh | 4 |
| `RX_VM_RETE` | `RX_VM_NETWORK` | environment variable | sh | 4 |
| `RX_VM_RIAVVIA_S` | `RX_VM_RESTART_S` | environment variable | sh | 3 |
| `RX_VM_SEME` | `RX_VM_SEED` | environment variable | sh | 4 |
| `RX_VM_TAVOLETTA` | `RX_VM_TABLET` | environment variable | sh | 4 |
| `SBLOCCA` | `UNBLOCK` | data name (dati.tsv: wire-string) | c,py,sh | 34 |
| `SESSIONE_ABBANDONATA` | `SESSION_ABANDONED` | data name (dati.tsv: reason) | c,html,py | 9 |
| `SESSIONE_LOCALE_PREVALSA` | `LOCAL_SESSION_PREVAILED` | data name (dati.tsv: reason) | c,html,py | 11 |
| `SESSIONE_TERMINATA` | `SESSION_TERMINATED` | data name (dati.tsv: reason) | c,py | 13 |
| `TASTO` | `KEY` | data name (dati.tsv: json-value) | c,py | 2 |
| `TOLTO` | `REMOVED` | data name (dati.tsv: wire-string) | c,py,sh | 33 |
| `__AVVISO__` | `__WARNING__` | data name (dati.tsv: kv-key) | c,html | 4 |
| `__IMPRONTA__` | `__FINGERPRINT__` | data name (dati.tsv: kv-key) | c,html | 5 |
| `abbandono-s` | `abandon-s` | option / subcommand / kebab name | c,py,sh | 15 |
| `accento-scuro` | `accent-dark` | option / subcommand / kebab name | css,html | 4 |
| `accesso-entra` | `access-enter` | option / subcommand / kebab name | html | 2 |
| `accesso-gira` | `access-runs` | option / subcommand / kebab name | html | 2 |
| `accesso-respira` | `access-breathes` | option / subcommand / kebab name | html | 2 |
| `accesso-scuote` | `access-shakes` | option / subcommand / kebab name | html | 2 |
| `algoritmo` | `algorithm` | data name (dati.tsv: json-key) | c | 1 |
| `altro_scatola` | `other_box` | data name (dati.tsv: json-value) | py | 12 |
| `ammazza-aiutante` | `kill-helper` | option / subcommand / kebab name | sh | 4 |
| `anche-lo-sporco` | `dirty-too` | option / subcommand / kebab name | py | 6 |
| `anche-se-non-vuoto` | `even-if-not-empty` | option / subcommand / kebab name | py | 2 |
| `anche-se-qualcuno-e-dentro` | `even-if-someone-is-inside` | option / subcommand / kebab name | py | 1 |
| `anticipo-foto-s` | `photo-lead-s` | option / subcommand / kebab name | py | 2 |
| `applicazione-che-muore` | `dying-app` | option / subcommand / kebab name | py,sh | 8 |
| `appunti-attendi` | `clipboard-wait` | option / subcommand / kebab name | py | 2 |
| `appunti-copia` | `clipboard-copy` | option / subcommand / kebab name | py | 2 |
| `appunti-scrivi` | `clipboard-write` | option / subcommand / kebab name | py | 3 |
| `argomenti-ciechi` | `blind-arguments` | option / subcommand / kebab name | py | 1 |
| `ascolto-s` | `listen-s` | option / subcommand / kebab name | py | 3 |
| `assesta-s` | `settle-s` | option / subcommand / kebab name | py | 1 |
| `attacco` | `attach` | data name (dati.tsv: wire-string) | html | 1 |
| `attesa-ammesso` | `wait-admitted` | option / subcommand / kebab name | py | 1 |
| `attesa-ammissione` | `wait-admission` | option / subcommand / kebab name | py | 1 |
| `attesa-attacca` | `waiting-attach` | data name (dati.tsv: log-text) | c,py | 6 |
| `attesa-avvio` | `wait-startup` | option / subcommand / kebab name | py | 1 |
| `attesa-biglietto` | `wait-ticket` | option / subcommand / kebab name | py | 1 |
| `attesa-browser` | `wait-browser` | option / subcommand / kebab name | py | 3 |
| `attesa-chiusura` | `wait-closing` | option / subcommand / kebab name | py,sh | 6 |
| `attesa-ciao` | `waiting-hello` | data name (dati.tsv: log-text) | c,py | 10 |
| `attesa-compositore` | `wait-compositor` | option / subcommand / kebab name | py | 1 |
| `attesa-credenziali` | `waiting-credentials` | data name (dati.tsv: log-text) | c,py | 7 |
| `attesa-crollo` | `wait-collapse` | option / subcommand / kebab name | py | 1 |
| `attesa-figlio` | `wait-child` | option / subcommand / kebab name | py | 1 |
| `attesa-finestra` | `wait-window` | option / subcommand / kebab name | py | 5 |
| `attesa-nascita` | `wait-birth` | option / subcommand / kebab name | py | 1 |
| `attesa-nascita-s` | `wait-birth-s` | option / subcommand / kebab name | py | 1 |
| `attesa-palco` | `wait-stage` | option / subcommand / kebab name | py,sh | 13 |
| `attesa-primo-fotogramma` | `wait-first-frame` | option / subcommand / kebab name | py | 1 |
| `attesa-rientro` | `wait-reentry` | option / subcommand / kebab name | py | 3 |
| `attesa-s` | `wait-s` | option / subcommand / kebab name | py | 4 |
| `attesa-scatto` | `wait-shot` | option / subcommand / kebab name | py | 6 |
| `attesa-scena` | `wait-scene` | option / subcommand / kebab name | c,py | 13 |
| `attesa-sessione` | `wait-session` | option / subcommand / kebab name | py | 1 |
| `attesa-sgombero` | `wait-clearout` | option / subcommand / kebab name | py | 5 |
| `attesa-sink` | `wait-sink` | option / subcommand / kebab name | py,sh | 3 |
| `attesa-sveglia` | `wait-wake` | option / subcommand / kebab name | py | 1 |
| `attesa-tasto` | `wait-key` | option / subcommand / kebab name | py | 1 |
| `attesa-tela` | `wait-canvas` | option / subcommand / kebab name | py | 1 |
| `attesa-uscita` | `wait-exit` | option / subcommand / kebab name | py | 2 |
| `attesa-uscita-s` | `wait-exit-s` | option / subcommand / kebab name | py | 1 |
| `attesa-verdetto` | `waiting-verdict` | data name (dati.tsv: log-text) | c,html,py | 21 |
| `audio-decodifica-ms` | `audio-decoding-ms` | option / subcommand / kebab name | py | 2 |
| `audio-passo-us` | `audio-step-us` | option / subcommand / kebab name | py | 2 |
| `audio-prova` | `audio-test` | option / subcommand / kebab name | c,conf,py,sh | 20 |
| `audio-regola` | `audio-rule` | option / subcommand / kebab name | py | 20 |
| `audio-scrivi` | `audio-write` | option / subcommand / kebab name | py | 9 |
| `avviso-muro` | `warning-wall` | option / subcommand / kebab name | html | 3 |
| `banco-nel-binario` | `bench-in-binary` | data name (dati.tsv: kv-key) | sh | 1 |
| `banco-w1` | `bench-w1` | option / subcommand / kebab name | conf,make,py | 4 |
| `bordo-blu` | `edge-blue` | option / subcommand / kebab name | html | 3 |
| `bozze-attese` | `expected-drafts` | option / subcommand / kebab name | py | 3 |
| `browser-griglia` | `browser-grid` | option / subcommand / kebab name | html | 4 |
| `browser-sez` | `browser-sect` | option / subcommand / kebab name | html | 1 |
| `byte_persi` | `byte_lost` | data name (dati.tsv: log-marker) | c,py | 10 |
| `byte_persi_d` | `byte_lost_d` | data name (dati.tsv: log-marker) | c,py | 5 |
| `byte_spediti` | `byte_shipped` | data name (dati.tsv: log-marker) | c,py | 11 |
| `caduta-s` | `drop-s` | option / subcommand / kebab name | py | 1 |
| `campo-bordo` | `field-border` | option / subcommand / kebab name | css,html | 5 |
| `campo-bordo-su` | `field-border-hover` | option / subcommand / kebab name | css,html | 5 |
| `chiaro-fondo` | `light-background` | option / subcommand / kebab name | css,html | 13 |
| `chiave-a` | `key-at` | option / subcommand / kebab name | c,sh | 6 |
| `chiave-dopo` | `key-after` | option / subcommand / kebab name | py | 2 |
| `chiavi-attese` | `expected-keys` | option / subcommand / kebab name | py,sh | 3 |
| `chiavi-ogni` | `keys-every` | option / subcommand / kebab name | c | 3 |
| `clic-dopo` | `click-after` | option / subcommand / kebab name | py | 3 |
| `clic-ogni` | `click-every` | option / subcommand / kebab name | py | 2 |
| `cliente-di-prova` | `test-client` | data name (dati.tsv: capability-value) | py | 4 |
| `coda-scatto` | `shot-tail` | option / subcommand / kebab name | py | 1 |
| `coda_rete_us` | `network_queue_us` | data name (dati.tsv: log-marker) | c,py | 3 |
| `codice-evdev` | `code-evdev` | option / subcommand / kebab name | py | 1 |
| `codificatore-fermo` | `stopped-encoder` | option / subcommand / kebab name | py,sh | 13 |
| `comando-socket` | `command-socket` | option / subcommand / kebab name | c,conf,py,sh | 48 |
| `come-al-riavvio` | `as-after-reboot` | option / subcommand / kebab name | sh | 4 |
| `conferma-no` | `confirm-no` | option / subcommand / kebab name | html | 3 |
| `conferma-si` | `confirm-yes` | option / subcommand / kebab name | html | 2 |
| `conferma-testo` | `confirm-text` | option / subcommand / kebab name | html | 2 |
| `continuita-s` | `continuity-s` | option / subcommand / kebab name | py | 2 |
| `controllo-min` | `check-min` | option / subcommand / kebab name | py | 5 |
| `controllo-rosso` | `check-red` | option / subcommand / kebab name | py | 1 |
| `controllo-testimone` | `check-witness` | option / subcommand / kebab name | py | 3 |
| `coppie-esaminate` | `examined-pairs` | option / subcommand / kebab name | py | 2 |
| `costruisci-tutte` | `build-all` | option / subcommand / kebab name | sh | 2 |
| `cpu-tutti` | `all-cpus` | option / subcommand / kebab name | py | 1 |
| `credito-atteso` | `expected-credit` | option / subcommand / kebab name | py | 2 |
| `da-scena` | `from-scene` | option / subcommand / kebab name | py | 3 |
| `dal-bus` | `from-bus` | option / subcommand / kebab name | py,sh | 7 |
| `data-agganciato` | `data-hooked` | option / subcommand / kebab name | html | 3 |
| `data-bannato` | `data-banned` | option / subcommand / kebab name | c,html,py,sh | 24 |
| `data-disposizione` | `data-arrangement` | option / subcommand / kebab name | html,py | 14 |
| `data-puntatore` | `data-ptr` | option / subcommand / kebab name | html | 3 |
| `data-restano-ms` | `data-remaining-ms` | option / subcommand / kebab name | c,html,py,sh | 12 |
| `data-scheda` | `data-gpu_card` | option / subcommand / kebab name | html | 3 |
| `data-schermo` | `data-display_screen` | option / subcommand / kebab name | html,py | 23 |
| `deb-firma` | `deb-sign` | option / subcommand / kebab name | sh | 2 |
| `desincronizzata` | `desynchronized` | data name (dati.tsv: wire-string) | c,html,py | 11 |
| `desktop-nuovo` | `new-desktop` | option / subcommand / kebab name | py,sh | 13 |
| `dgram_falsi_d` | `dgram_false_d` | data name (dati.tsv: log-marker) | c,py | 6 |
| `dgram_persi_d` | `dgram_lost_d` | data name (dati.tsv: log-marker) | c,py | 4 |
| `dipinto-dopo-reset` | `painted-after-reset` | option / subcommand / kebab name | py | 1 |
| `distro-riga` | `distro-line` | option / subcommand / kebab name | html | 4 |
| `dopo-scena` | `post-scene` | option / subcommand / kebab name | c,sh | 8 |
| `due-col` | `two-col` | option / subcommand / kebab name | html | 3 |
| `f-disp` | `f-avail` | option / subcommand / kebab name | html | 3 |
| `figlio-interno` | `internal-child` | option / subcommand / kebab name | c,py,sh | 29 |
| `file-del-banco` | `bench-files` | data name (dati.tsv: kv-key) | sh | 2 |
| `fin-ricevuto` | `fin-received` | option / subcommand / kebab name | py | 1 |
| `finestra-che-non-si-apre` | `window-that-does-not-open` | option / subcommand / kebab name | py,sh | 9 |
| `finestra-guasto` | `fault-window` | option / subcommand / kebab name | py | 3 |
| `finestra-s` | `window-s` | option / subcommand / kebab name | py | 8 |
| `forma-sbagliata` | `wrong-shape` | option / subcommand / kebab name | py,sh | 10 |
| `fotogramma-ripetuto` | `repeated-frame` | option / subcommand / kebab name | py,sh | 10 |
| `fotogrammi-prima` | `frames-before` | option / subcommand / kebab name | py | 1 |
| `frazione-coppie` | `pair-fraction` | option / subcommand / kebab name | py | 2 |
| `frazione-minima` | `minimum-fraction` | option / subcommand / kebab name | py | 3 |
| `fuori-linea` | `offline` | option / subcommand / kebab name | sh | 10 |
| `fuso-log` | `merged-log` | option / subcommand / kebab name | py | 1 |
| `giallo-b` | `yellow-b` | option / subcommand / kebab name | css | 3 |
| `giallo-f` | `yellow-f` | option / subcommand / kebab name | css | 3 |
| `giallo-t` | `yellow-t` | option / subcommand / kebab name | css | 3 |
| `gid-atteso` | `expected-gid` | option / subcommand / kebab name | py | 1 |
| `giornale-tutto` | `journal-all` | option / subcommand / kebab name | sh | 1 |
| `giri_fermi` | `stopped_rounds` | data name (dati.tsv: log-marker) | c,py | 8 |
| `giro_peggiore_ms` | `worst_round_ms` | data name (dati.tsv: log-marker) | c | 1 |
| `grafico-cpu` | `chart-cpu` | option / subcommand / kebab name | html | 2 |
| `grafico-video` | `chart-video` | option / subcommand / kebab name | html | 2 |
| `griglia-f` | `grid-f` | option / subcommand / kebab name | html | 3 |
| `guarda-s` | `look-s` | option / subcommand / kebab name | py | 2 |
| `guasto-innestato` | `grafted-fault` | option / subcommand / kebab name | py,sh | 3 |
| `h264_strada` | `h264_route` | data name (dati.tsv: json-key) | c,go | 3 |
| `hevc_strada` | `hevc_route` | data name (dati.tsv: json-key) | c,go | 3 |
| `i-portatile` | `i-laptop` | option / subcommand / kebab name | html | 3 |
| `i-telefono` | `i-phone` | option / subcommand / kebab name | html | 3 |
| `icona-d` | `icon-d` | option / subcommand / kebab name | html | 5 |
| `idle-atteso` | `expected-idle` | option / subcommand / kebab name | py,sh | 5 |
| `idr-attesi` | `expected-idr` | option / subcommand / kebab name | py,sh | 4 |
| `inattivita-s` | `inactivity-s` | option / subcommand / kebab name | c,py,sh | 13 |
| `incolla-nascosto` | `paste-hidden` | option / subcommand / kebab name | html,py | 6 |
| `iniettore-accendi` | `injector-turn-on` | option / subcommand / kebab name | sh | 7 |
| `iniettore-di` | `injector-of` | option / subcommand / kebab name | sh | 4 |
| `iniettore-dice` | `injector-says` | option / subcommand / kebab name | sh | 4 |
| `iniettore-registro` | `injector-log` | option / subcommand / kebab name | sh | 3 |
| `iniettore-spegni` | `injector-turn-off` | option / subcommand / kebab name | sh | 6 |
| `istante-us` | `instant-us` | option / subcommand / kebab name | py | 2 |
| `journal-scatola` | `box-journal` | option / subcommand / kebab name | py | 8 |
| `labwc_cliente` | `labwc_client` | data name (dati.tsv: json-value) | py | 11 |
| `lascia-acceso` | `leave-on` | option / subcommand / kebab name | py | 1 |
| `lascia-tetto` | `leave-cap` | option / subcommand / kebab name | py | 2 |
| `lascia-un-inquilino` | `leave-a-tenant` | option / subcommand / kebab name | py,sh | 8 |
| `lascia-un-processo` | `leave-a-process` | option / subcommand / kebab name | py,sh | 10 |
| `lascia-una-casa` | `leave-a-home` | option / subcommand / kebab name | py,sh | 7 |
| `ldd-pulito` | `ldd-clean` | data name (dati.tsv: kv-key) | sh | 1 |
| `linea-morta` | `dead-line` | option / subcommand / kebab name | c,py,sh | 57 |
| `linea-morta-silenzio-s` | `dead-line-silence-s` | option / subcommand / kebab name | c,py | 8 |
| `linea-morta-stallo-ms` | `dead-line-stall-ms` | option / subcommand / kebab name | c,py,sh | 9 |
| `livello-dir` | `level-dir` | option / subcommand / kebab name | py | 8 |
| `marchio-grande` | `brand-large` | option / subcommand / kebab name | css | 1 |
| `margine-filo` | `wire-margin` | option / subcommand / kebab name | py | 1 |
| `margine-soglia` | `threshold-margin` | option / subcommand / kebab name | py | 1 |
| `matrice-scorre` | `matrix-scrolls` | option / subcommand / kebab name | html | 2 |
| `minimo-dopo-scena` | `min-after-scene` | option / subcommand / kebab name | c,sh | 6 |
| `minimo_pacchetti` | `min_packets` | data name (dati.tsv: log-marker) | c,py | 3 |
| `minimo_prove` | `min_tests` | data name (dati.tsv: log-marker) | c,py | 4 |
| `minuti-ultimo` | `last-rung-minutes` | option / subcommand / kebab name | py | 4 |
| `motore-annulla` | `engine-rollback` | option / subcommand / kebab name | sh | 3 |
| `motore-cmd` | `engine-cmd` | option / subcommand / kebab name | sh | 2 |
| `motore-monta` | `engine-mount` | option / subcommand / kebab name | sh | 2 |
| `motore-smonta` | `engine-unmount` | option / subcommand / kebab name | sh | 2 |
| `muore-dopo` | `dies-after` | option / subcommand / kebab name | py | 3 |
| `niente-audio-silenzio` | `no-audio-silence` | option / subcommand / kebab name | c,py | 42 |
| `niente-linea-morta` | `no-dead-line` | option / subcommand / kebab name | c,py | 17 |
| `niente-ritmo-adattivo` | `no-adaptive-rate` | option / subcommand / kebab name | c,py,sh | 25 |
| `nome-figlio` | `child-name` | option / subcommand / kebab name | py | 1 |
| `non-collegare` | `no-connect` | option / subcommand / kebab name | py | 1 |
| `non-rifare` | `no-rebuild` | option / subcommand / kebab name | py | 2 |
| `nota-b` | `note-b` | option / subcommand / kebab name | html | 2 |
| `notte-2` | `night-2` | option / subcommand / kebab name | css | 2 |
| `notte-3` | `night-3` | option / subcommand / kebab name | css | 2 |
| `ogni-s` | `every-s` | option / subcommand / kebab name | py | 3 |
| `ombra-notte` | `ombra-night` | option / subcommand / kebab name | css | 2 |
| `opzioni-di-banco-nell-unita` | `bench-options-in-unit` | data name (dati.tsv: kv-key) | sh | 2 |
| `orologio-s` | `clock-s` | option / subcommand / kebab name | py | 1 |
| `osserva-s` | `observe-s` | option / subcommand / kebab name | py | 1 |
| `pacchetto-byte` | `package-bytes` | option / subcommand / kebab name | sh | 3 |
| `pacman-firma` | `pacman-sign` | option / subcommand / kebab name | sh | 2 |
| `pagina-b11` | `page-b11` | data name (dati.tsv: capability-value) | html | 1 |
| `parola-cattiva` | `bad-password` | option / subcommand / kebab name | py | 1 |
| `parola-file` | `password-file` | option / subcommand / kebab name | py,sh | 54 |
| `parola-sudo` | `sudo-password` | option / subcommand / kebab name | py | 1 |
| `passo-cpu` | `cpu-step` | option / subcommand / kebab name | py | 2 |
| `passo-s` | `step-s` | option / subcommand / kebab name | py | 1 |
| `passo-scena` | `scene-step` | option / subcommand / kebab name | py | 1 |
| `pausa-staccato` | `detached-pause` | option / subcommand / kebab name | py | 1 |
| `pausa-tasto` | `pause-key` | option / subcommand / kebab name | py | 1 |
| `per-caso` | `per-case` | option / subcommand / kebab name | py,sh | 3 |
| `piede-chiaro` | `foot-clear` | option / subcommand / kebab name | html | 16 |
| `porte-base` | `base-ports` | option / subcommand / kebab name | py,sh | 35 |
| `posa-scena` | `scene-settle` | option / subcommand / kebab name | py | 2 |
| `pretendi-chi` | `require-who` | option / subcommand / kebab name | c,py | 10 |
| `pretendi-pid` | `require-pid` | option / subcommand / kebab name | c,py | 4 |
| `primo-s` | `first-s` | option / subcommand / kebab name | py | 1 |
| `prova-codifica` | `encoding-test` | option / subcommand / kebab name | c,go,py,sh | 48 |
| `pss-ogni` | `pss-every` | option / subcommand / kebab name | py | 3 |
| `puntatore-di-ripiego` | `fallback-pointer` | option / subcommand / kebab name | html,py | 2 |
| `puntatore-vecchia` | `old-pointer` | option / subcommand / kebab name | py | 3 |
| `punti-v` | `points-v` | option / subcommand / kebab name | html | 7 |
| `purezza-minima` | `minimum-purity` | option / subcommand / kebab name | py | 1 |
| `qualita-a` | `quality-at` | option / subcommand / kebab name | c,sh | 4 |
| `qualita-risale` | `quality-rises` | option / subcommand / kebab name | c,py | 16 |
| `registro-byte` | `log-bytes` | option / subcommand / kebab name | sh | 1 |
| `registro-cmd` | `log-cmd` | option / subcommand / kebab name | py | 6 |
| `respiro-innesco` | `respite-trigger` | option / subcommand / kebab name | py | 2 |
| `resta-dopo` | `stay-after` | option / subcommand / kebab name | py | 2 |
| `resta-nascita` | `stay-birth` | option / subcommand / kebab name | py | 1 |
| `resta-prima` | `stay-before` | option / subcommand / kebab name | py | 4 |
| `rete-intera` | `whole-network` | option / subcommand / kebab name | py,sh | 9 |
| `rete-quic` | `network-quic` | data name (dati.tsv: log-marker) | c,py | 66 |
| `ricevuti_d` | `received_d` | data name (dati.tsv: log-marker) | c,py | 5 |
| `ridimensiona-a` | `resize-at` | option / subcommand / kebab name | c,sh | 6 |
| `rientra-subito` | `reenter-immediately` | option / subcommand / kebab name | py,sh | 9 |
| `riprova-0f` | `retry-0f` | option / subcommand / kebab name | py | 5 |
| `riprova-s` | `retry-s` | option / subcommand / kebab name | py | 1 |
| `risorse-senza-root` | `resources-without-root` | option / subcommand / kebab name | py | 1 |
| `ritira-esiti` | `fetch-outcomes` | option / subcommand / kebab name | sh | 1 |
| `ritmo-adattivo` | `adaptive-rate` | option / subcommand / kebab name | c,py | 12 |
| `ritmo-minimo` | `minimum-rate` | option / subcommand / kebab name | html,py | 8 |
| `ritmo_arretrato` | `rate_backlog` | data name (dati.tsv: log-marker) | c,py | 5 |
| `ritmo_posti` | `rate_slots` | data name (dati.tsv: log-marker) | c,py | 5 |
| `riusa-utente` | `reuse-user` | option / subcommand / kebab name | py | 3 |
| `rosso-b` | `red-b` | option / subcommand / kebab name | css | 4 |
| `rosso-f` | `red-f` | option / subcommand / kebab name | css | 4 |
| `rosso-t` | `red-t` | option / subcommand / kebab name | css | 4 |
| `rpm-firma` | `rpm-sign` | option / subcommand / kebab name | sh | 2 |
| `rpmbuild-esito` | `rpmbuild-outcome` | data name (dati.tsv: kv-key) | sh | 1 |
| `rx_rilascio` | `rx_release` | data name (dati.tsv: kv-key) | conf,sh | 5 |
| `rx_selinux_permissivo` | `rx_selinux_permissive` | data name (dati.tsv: kv-key) | conf,sh | 3 |
| `rx_versione` | `rx_version` | data name (dati.tsv: kv-key) | conf,sh | 6 |
| `salta-riaccensione` | `skip-restart` | option / subcommand / kebab name | py | 3 |
| `salva-fetta` | `save-slice` | option / subcommand / kebab name | py | 1 |
| `scala-s` | `scale-s` | option / subcommand / kebab name | py | 1 |
| `scartati_d` | `discarded_d` | data name (dati.tsv: log-marker) | c,py | 3 |
| `scarto-massimo` | `maximum-gap` | option / subcommand / kebab name | py | 3 |
| `scena-che-lampeggia` | `flashing-scene` | option / subcommand / kebab name | py,sh | 11 |
| `scena-ferma` | `still-scene` | option / subcommand / kebab name | py,sh | 15 |
| `scena-guasta` | `broken-scene` | option / subcommand / kebab name | py | 1 |
| `scena-s` | `scene-s` | option / subcommand / kebab name | py | 1 |
| `scena-soglia-stretta-ms` | `scene-tight-threshold-ms` | option / subcommand / kebab name | py | 1 |
| `scena-sorda` | `deaf-scene` | option / subcommand / kebab name | py,sh | 9 |
| `scheda-b` | `card-b` | option / subcommand / kebab name | html | 5 |
| `scorciatoie-apri` | `shortcuts-open` | option / subcommand / kebab name | html | 3 |
| `scorciatoie-bottoni` | `shortcuts-buttons` | option / subcommand / kebab name | html | 1 |
| `scorciatoie-elenco` | `shortcuts-list` | option / subcommand / kebab name | html | 1 |
| `scorciatoie-riassunto` | `shortcuts-summary` | option / subcommand / kebab name | html | 2 |
| `scorciatoie-stato` | `shortcuts-state` | option / subcommand / kebab name | html | 1 |
| `scorciatoie-voci` | `shortcuts-entries` | option / subcommand / kebab name | html | 1 |
| `segnale-scena` | `scene-signal` | option / subcommand / kebab name | c,sh | 8 |
| `segni-browser` | `browser-marks` | option / subcommand / kebab name | py | 3 |
| `seme-base` | `base-seed` | option / subcommand / kebab name | py | 3 |
| `senza-clic` | `no-click` | option / subcommand / kebab name | py | 1 |
| `senza-controllo` | `no-check` | option / subcommand / kebab name | py | 1 |
| `senza-copia` | `no-copy` | option / subcommand / kebab name | py,sh | 11 |
| `senza-coppia` | `no-pair` | option / subcommand / kebab name | py | 1 |
| `senza-cura` | `no-fix` | option / subcommand / kebab name | py,sh | 24 |
| `senza-eco` | `no-echo` | option / subcommand / kebab name | py | 7 |
| `senza-guasto` | `no-fault` | option / subcommand / kebab name | py | 6 |
| `senza-maiusc` | `no-shift` | option / subcommand / kebab name | py,sh | 7 |
| `senza-pulsante` | `no-button` | option / subcommand / kebab name | py,sh | 10 |
| `senza-riscaldamento` | `no-warmup` | option / subcommand / kebab name | py | 1 |
| `senza-scheda` | `no-card` | option / subcommand / kebab name | py | 3 |
| `senza-sessione` | `no-session` | option / subcommand / kebab name | py,sh | 9 |
| `senza-sorgente` | `no-source` | option / subcommand / kebab name | py,sh | 11 |
| `senza-sveglia` | `no-wake` | option / subcommand / kebab name | py | 2 |
| `senza-tasto` | `no-key` | option / subcommand / kebab name | py,sh | 10 |
| `senza-tela-minima` | `no-min-canvas` | option / subcommand / kebab name | py | 1 |
| `senza-usermod` | `no-usermod` | option / subcommand / kebab name | py,sh | 11 |
| `sessione-via` | `session-stop` | option / subcommand / kebab name | sh | 3 |
| `sfratto-ms` | `eviction-ms` | option / subcommand / kebab name | c,py,sh | 27 |
| `sgombra-soglia-ms` | `clear-threshold-ms` | option / subcommand / kebab name | c,py,sh | 38 |
| `soglia-coppia` | `pair-threshold` | option / subcommand / kebab name | py | 2 |
| `soglia-cpu` | `cpu-threshold` | option / subcommand / kebab name | py | 2 |
| `soglia_silenzio_ms` | `silence_threshold_ms` | data name (dati.tsv: log-marker) | c,py | 4 |
| `solo-controllo-positivo` | `positive-check-only` | option / subcommand / kebab name | py,sh | 4 |
| `solo-distacco` | `detach-only` | option / subcommand / kebab name | py,sh | 8 |
| `solo-esito` | `outcome-only` | option / subcommand / kebab name | py | 1 |
| `solo-porte` | `ports-only` | option / subcommand / kebab name | py | 2 |
| `solo-qui` | `here-only` | option / subcommand / kebab name | sh | 4 |
| `solo-strato-tecnico` | `technical-layer-only` | option / subcommand / kebab name | py | 1 |
| `sonda-b2` | `probe-b2` | data name (dati.tsv: capability-value) | html | 1 |
| `sorgente-out` | `source-out` | option / subcommand / kebab name | c,sh | 5 |
| `ssh-parola` | `ssh-password` | option / subcommand / kebab name | sh | 4 |
| `staccata-per-silenzio` | `detached-for-silence` | data name (dati.tsv: log-text) | c,py | 10 |
| `stato-iniziale` | `initial-state` | option / subcommand / kebab name | py,sh | 7 |
| `strato-tecnico` | `technical-layer` | option / subcommand / kebab name | py,sh | 5 |
| `tabella-capacita` | `capabilities-table` | option / subcommand / kebab name | html | 2 |
| `taratura-s` | `calibration-s` | option / subcommand / kebab name | py | 1 |
| `tastiera-comando` | `keyboard-command` | option / subcommand / kebab name | html,py | 5 |
| `tela-altezza` | `canvas-height` | option / subcommand / kebab name | py | 1 |
| `tela-larghezza` | `canvas-width` | option / subcommand / kebab name | py | 1 |
| `tela-video` | `canvas-video` | option / subcommand / kebab name | html | 1 |
| `tenue-fondo` | `faint-background` | option / subcommand / kebab name | css,html | 5 |
| `terminale-via` | `terminal-away` | option / subcommand / kebab name | sh | 4 |
| `testimone-via` | `witness-away` | option / subcommand / kebab name | sh | 5 |
| `tetti-codice` | `code-caps` | option / subcommand / kebab name | py,sh | 7 |
| `tetto-banda-mbit` | `bandwidth-cap-mbit` | option / subcommand / kebab name | c,py | 15 |
| `tetto-controllo-s` | `check-cap-s` | option / subcommand / kebab name | py | 1 |
| `tetto-foto-s` | `photo-cap-s` | option / subcommand / kebab name | py | 1 |
| `tetto-prova` | `test-cap` | option / subcommand / kebab name | py | 1 |
| `tetto-s` | `cap-s` | option / subcommand / kebab name | py | 12 |
| `tetto-sessioni` | `session-cap` | option / subcommand / kebab name | c,py,sh | 36 |
| `tieni-inquilino` | `keep-tenant` | option / subcommand / kebab name | py | 1 |
| `togli-nome` | `remove-name` | option / subcommand / kebab name | py,sh | 11 |
| `tolleranza-hz` | `tolerance-hz` | option / subcommand / kebab name | py | 1 |
| `tui-lingua` | `tui-language` | option / subcommand / kebab name | sh | 2 |
| `uccidi-la-sessione` | `kill-the-session` | option / subcommand / kebab name | py,sh | 10 |
| `uid-atteso` | `expected-uid` | option / subcommand / kebab name | py | 1 |
| `ultimo_numero` | `last_number` | data name (dati.tsv: log-text) | c,py | 17 |
| `usciti_byte` | `exited_bytes` | data name (dati.tsv: log-marker) | c,py,sh | 26 |
| `utente-base` | `base-user` | option / subcommand / kebab name | py | 5 |
| `utente-cattivo` | `bad-user` | option / subcommand / kebab name | py,sh | 2 |
| `verde-b` | `green-b` | option / subcommand / kebab name | css | 3 |
| `verde-f` | `green-f` | option / subcommand / kebab name | css | 3 |
| `verde-t` | `green-t` | option / subcommand / kebab name | css | 3 |
| `verificato` | `verified` | data name (dati.tsv: json-value) | py | 3 |
| `vetro-blu` | `glass-blue` | option / subcommand / kebab name | html | 4 |
| `video-profondita` | `video-depth` | option / subcommand / kebab name | py | 1 |
| `video-scrivi` | `video-write` | option / subcommand / kebab name | py | 11 |
| `video_avanza` | `video_advances` | data name (dati.tsv: json-value) | py | 10 |

### Coverage of the contract analysis (contratti/*.tsv)

**dati-contratto.tsv** — kept (unresolved collision): 4, left out on purpose (step 2): 2, no Italian word: 92, not renamed (path, product name, or not found by the analysis): 49, renamed by dati.tsv: 46, renamed by the table: 361

Not renamed: `#puntatore-di-ripiego` `#tastiera-comando` `al_secondo` `ammissione_s` `bit_per_canale_chi_lo_dice` `blocco_max_ms` `buchi_istante` `byte_flusso` `categorie` `chi_lo_dice` `cinture` `commit_cura` `consegna_a_F2_3` `cpu_macchina_pct` `distinti_riciclati` `durata_lavoro_s` `errori_decodifica` `giro_eco` `ha_visto_il_guasto` `inizio_finestra_t` `inizio_t` `latenza_ms` `legami_in_ingresso` `mem_totale_mb` `mem_usata_mb` `motivo` `nascita_ms` `nascita_s` `positivo` `primari` `primo_fotogramma_ms` `primo_non_degenere_s` `processi_gpu` `recinti` `remotix-appunti` `remotix-cattura` `remotix-figlio` `remotix-invisibile` `remotix-suono` `remotix_porta` `richieste` `ritardi_eco_ms` `ritardi_ms` `sessioni_durante` `sessioni_remotix` `si` `strozzatura_frazione` `tratti keys (strada, tela, dipinti, consegnati, fuori, dentro, coda_dec, saltati_coda, tardive, eta_ms, ric_ms, costo_disegno_ms, "8_decode_richiamo", "9a_richiamo_chiamata", "9b_conversione", "10_vetro", "9_10_richiamo_vetro", "11_vetro_prossimo_quadro")` `utenti-negati`

**opzioni-contratto.tsv** — kept (unresolved collision): 1, left out on purpose (step 2): 2, no Italian word: 2, not renamed (path, product name, or not found by the analysis): 26, renamed by dati.tsv: 4, renamed by the table: 770

Not renamed: `B3_SPIA` `BRUCIATORI` `C15G4_TEMPI` `FINTO_CLASSE` `FINTO_MUORE` `G7_TRACCIA` `LIVELLO` `OPERAZIONI` `PARLANTINA` `PROFONDITA` `PUNTO` `QUALITA` `REMOTIX_NOME` `VECCHIA_X264_EXTRA` `W1_RIPRENDI` `W1_STRADA` `W1_TIENI` `a-secco` `con-guasti` `copia` `raffica` `remotix-figlio` `senza-nastro` `senza-rete` `solo-certifica` `sul-server` `un-verso`

**rcp-contratto.tsv** — kept (unresolved collision): 3, no Italian word: 22, not renamed (path, product name, or not found by the analysis): 3, renamed by dati.tsv: 32, renamed by the table: 160

Not renamed: `RCPREG` `RIFIUTATA` `motivo` `remotix-pagina` `restanoMs` `si`


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
| `installatore/motore/epoca_test.go` | `installer/engine/epoch_test.go` | 0 |
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
| `src/pagina.html` | `src/page.html` | 309 |
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
