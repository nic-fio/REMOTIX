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
- **Data names** in `dati.tsv` (75 today): RCP reason and sub-code names, state strings
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

A conflict is checked **in every scope where two names can meet**:

| scope | made of |
|---|---|
| C translation unit | the `.c` file and every project header it includes, transitively |
| C program | the file-scope names (brace and paren depth 0) of every C file of one directory: the link |
| Go package | every file of the directory, tests included |
| Python | the file and the local modules it imports |
| shell | the file and what it `source`s |
| page | the HTML file: JS, ids, classes, CSS |
| product data | the data-like string literals of `src/`, `installatore/`, `banchi/rcp/`, `packaging/` together: two wire words may never become one |

Kinds of conflict, by role (a struct member never clashes with a variable):

1. **collision** — two old names, one new name, both in one scope.  The winner is pinned by
   `interi.tsv`, else the more frequent name; the other moves to its `sinonimi.tsv` alternative;
2. **clash** — the new name already exists in the scope and does not itself change;
3. **forbidden** — a keyword of the language, a system-header macro, a libc/glib global for a C global,
   a Go predeclared name, a shell reserved word or builtin for a function, a window property for a
   top-level `var`/`function` of a page, a well-known environment variable (`USER`, `PATH`, `LINES`,
   `SECONDS`…) for a shell or make variable;
4. **twins** must stay twins: an option's kebab and snake spellings (`--prova-codifica` ↔
   `args.prova_codifica`), and a Go struct field read from **untagged JSON** with its lowercase key
   (`Utente` ↔ `"utente"`: Go matches them ignoring case).  When the English of an untagged field is
   two words the key cannot follow, and both stay for a person to decide.

The loop runs until nothing changes (5 rounds today); a final pass leaves **unrenamed** every name that
still conflicts.  A kept name is safe — it stays Italian everywhere — and is listed below for a
decision in `interi.tsv` or `sinonimi.tsv`.

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
- **136 names are not renamed** (generated list below): mostly a second choice that collides too, and
  untagged JSON fields whose English is two words (`Stato`/`stato`, `Porta`/`porta`, `Motivo`/`motivo`,
  `Nodo`/`nodo`).  Safe (they stay Italian everywhere), but they need a decision in `interi.tsv`.
- **Word order**: the vocabulary translates word by word in Italian order (`sessione_marca` →
  `session_mark` is fine, `tela_minima` → `canvas_minimum` is not).  The options and environment
  variables reordered by the contract analysis are in `interi.tsv` (109); the rest of the code keeps
  the literal order until someone reviews it.
- **Not run on the copy**: the safety net in the boxes, the benches against a live server, and the
  manual's `--controlla` — they belong to §7 step 7 on the server.

---

## 9. The plan in numbers (generated by `rinomina2.py plan`)

<!-- generated:begin -->
<!-- generated by rinomina2.py plan: do not edit by hand -->
| | |
|---|---|
| names renamed | 10244 |
| kept unresolved | 136 |
| excluded | 6 |
| collisions handled | 497 |
| contracts | 2655 |
| files scanned | 612 |
| files skipped | 2566 |
| frozen register words | 1095 |
| data names dati tsv | 75 |

**Names by defining language** (a name defined in two languages counts twice)

| language | names |
|---|---|
| c | 3938 |
| css | 52 |
| go | 1006 |
| html | 1072 |
| js | 5 |
| make | 18 |
| py | 4647 |
| sh | 1082 |

**Renamed names defined per directory**

| directory | names |
|---|---|
| `src` | 7054 |
| `banchi/11-scatole` | 2596 |
| `banchi/15-suite` | 2381 |
| `installatore/motore` | 1909 |
| `banchi/16-stress` | 1235 |
| `banchi/rcp` | 616 |
| `banchi/09-b81-linea-morta.py` | 341 |
| `installatore/interfaccia` | 303 |
| `banchi/01-b3-cliente.py` | 244 |
| `banchi/01-b8-cronometro.py` | 219 |
| `banchi/19-android` | 214 |
| `banchi/09-b76-rete-cattiva.py` | 211 |
| `banchi/17-distro` | 206 |
| `grafica` | 206 |
| `banchi/09-b70-ritmo.py` | 192 |
| `banchi/01-b7-congedo.py` | 171 |
| `banchi/02-filo-fotogramma.py` | 160 |
| `banchi/19-vulkan` | 158 |
| `banchi/09-b79-cure.py` | 157 |
| `docs/sources` | 153 |
| `banchi/09-b77-audio-riordino.py` | 149 |
| `banchi/18-software` | 137 |
| `banchi/01-b4-validatore.py` | 133 |
| `banchi/12-client-veri.py` | 129 |
| `banchi/19-nvidia` | 129 |
| `banchi/02-filo-validatore.py` | 127 |
| `banchi/02-cattura-fotogramma.c` | 124 |
| `banchi/18-scheda` | 121 |
| `banchi/01-b11-pagina.html` | 120 |
| `banchi/18-a1` | 118 |
| `banchi/04-b28-gesti.py` | 115 |
| `banchi/01-b6-tetti.py` | 109 |
| `banchi/03-marca.py` | 109 |
| `banchi/04-b31-tela.c` | 107 |
| `banchi/01-b5-violazioni.py` | 101 |
| `banchi/09-b84-audio-silenzio.py` | 101 |
| `banchi/02-filo-cliente.py` | 92 |
| `banchi/10-f1-testimone.py` | 90 |
| `banchi/06-b5-esiti-cattura.c` | 87 |
| `banchi/02-cattura-giudica.py` | 85 |
| `banchi/02-pam-fermo.py` | 84 |
| `banchi/06-b33-testimone.c` | 82 |
| `banchi/02-cattura-prodotto.c` | 81 |
| `banchi/09-b78-apertura.py` | 81 |
| `banchi/01-b9-letture.py` | 79 |
| `banchi/12-c20-veri.py` | 76 |
| `banchi/07-b64-rete.py` | 74 |
| `banchi/01-b4-registrazioni.py` | 68 |
| `banchi/17-t7` | 66 |
| `banchi/01-b8-prova-ban.c` | 65 |
| `banchi/04-in8-misura.c` | 65 |
| `banchi/06-b33-risveglio.c` | 62 |
| `banchi/sonda` | 61 |
| `banchi/02-codifica-immagine.py` | 60 |
| `banchi/02-figlio-prova.py` | 59 |
| `banchi/04-b25-tastiera.c` | 59 |
| `banchi/07-b64-scena.py` | 57 |
| `banchi/13-w1-un-fotogramma.c` | 57 |
| `banchi/17-t9` | 57 |
| `banchi/01-b0-bersaglio.sh` | 56 |
| `banchi/02-codifica-lancia.sh` | 56 |
| `banchi/02-sessione-stato.py` | 55 |
| `banchi/02-cattura-lancia.sh` | 52 |
| `banchi/14-f1-forma.c` | 52 |
| `banchi/01-b8-sblocca.py` | 50 |
| `banchi/01-b2-sonda-trasporto.py` | 49 |
| `banchi/01-b8-lancia.sh` | 48 |
| `banchi/17-t8` | 48 |
| `banchi/02-sessione-lancia.sh` | 47 |
| `banchi/06-b33-terreno.sh` | 47 |
| `banchi/01-b6-lancia.sh` | 46 |
| `banchi/07-b65-datagram.py` | 46 |
| `banchi/01-b2-sonda.html` | 45 |
| `banchi/06-b33-risveglio-giudice.py` | 45 |
| `banchi/07-b64-orecchio.py` | 45 |
| `installatore/cmd` | 43 |
| `banchi/01-b0-terreno.sh` | 41 |
| `banchi/02-codifica-prova.c` | 41 |
| `banchi/02-pagina-sonda-codec.py` | 39 |
| `banchi/01-b11-lancia.sh` | 37 |
| `banchi/02-cattura-certifica.sh` | 36 |
| `banchi/02-codifica-nal.py` | 36 |
| `banchi/01-s7-rotella.sh` | 34 |
| `banchi/02-pagina-misura-cdp.py` | 34 |
| `banchi/01-s7-rotella.c` | 33 |
| `banchi/01-b3-rcp-innesta.py` | 32 |
| `banchi/01-b7-lancia.sh` | 31 |
| `banchi/attrezzi-allinea-prodotto.sh` | 30 |
| `banchi/02-codifica-obu.py` | 29 |
| `banchi/02-pam-lancia.sh` | 29 |
| `banchi/01-b11-guasto-innesta.py` | 27 |
| `banchi/01-b2-ngtcp2-wt-innesta.py` | 27 |
| `banchi/04-b25-guasti.c` | 27 |
| `banchi/07-b64-terreno.sh` | 27 |
| `banchi/17-t6` | 27 |
| `banchi/17-t2` | 26 |
| `packaging/archivio` | 26 |
| `banchi/06-b33-risveglio.sh` | 25 |
| `banchi/07-b46-marionette.py` | 25 |
| `banchi/02-figlio-lancia.sh` | 24 |
| `banchi/01-b11-guasto.sh` | 23 |
| `banchi/07-b42-giudice.py` | 23 |
| `banchi/02-sessione-dispositivi.py` | 22 |
| `banchi/01-b0-bersaglio.py` | 21 |
| `banchi/02-figlio-accendi.sh` | 20 |
| `banchi/02-sessione-guardia.sh` | 20 |
| `banchi/06-b33-risveglio-certifica.sh` | 20 |
| `banchi/01-b2-lancia-wt.sh` | 19 |
| `banchi/01-b5-lancia.sh` | 19 |
| `banchi/02-filo-lancia.sh` | 19 |
| `banchi/06-b34-tabella.c` | 18 |
| `banchi/01-s7-pagina.html` | 17 |
| `banchi/09-b81-terreno.sh` | 17 |
| `banchi/09-lucchetto.py` | 17 |
| `banchi/01-b4-lancia.py` | 16 |
| `banchi/02-pam-i3.py` | 16 |
| `banchi/01-b2-cliente-aioquic.py` | 15 |
| `banchi/02-pam-accendi.sh` | 14 |
| `installatore/prove` | 14 |
| `packaging/rpm` | 14 |
| `banchi/02-cattura-costruisci.sh` | 13 |
| `banchi/attrezzi-gruppi-scheda.sh` | 13 |
| `banchi/00-sessione-gnome.sh` | 12 |
| `banchi/01-casa-7448.sh` | 12 |
| `banchi/06-b33-risveglio-guasti.py` | 12 |
| `banchi/09-b79-terreno.sh` | 12 |
| `packaging/rilascio.sh` | 12 |
| `banchi/attrezzi-allinea-innesto.sh` | 11 |
| `banchi/04-b25-lancia.sh` | 9 |
| `banchi/attrezzi-utenti.sh` | 9 |
| `banchi/02-codifica-costruisci.sh` | 8 |
| `packaging/motore` | 8 |
| `banchi/04-b28-lancia.sh` | 7 |
| `banchi/01-b2-raccogli.py` | 6 |
| `packaging/arch` | 6 |
| `banchi/01-b2-costruisci-ngtcp2.sh` | 5 |
| `banchi/01-s7-raccogli.py` | 5 |
| `installatore/run.sh` | 5 |
| `banchi/01-b2-costruisci.sh` | 4 |
| `banchi/06-b5-esiti-cattura.sh` | 3 |
| `banchi/14-f1-forma.sh` | 3 |
| `banchi/06-b33-risveglio-costruisci.sh` | 2 |
| `installatore/costruisci.sh` | 2 |
| `banchi/04-in8-costruisci.sh` | 1 |
| `banchi/04-in8-parita.c` | 1 |
| `banchi/06-b33-costruisci.sh` | 1 |
| `installatore/catalogo` | 1 |

### Every collision and how it was resolved

| target | old names | winner | others → | scopes (first) |
|---|---|---|---|---|
| `HOME` | `CASA` | (forbidden: well-known environment variable) | **kept** | |
| `from` | `dal` | (forbidden: Python keyword or builtin) | **kept** | |
| `in` | `nella` | (forbidden: Python keyword or builtin) | **kept** | |
| `true` | `veri` | (forbidden: Go keyword or predeclared name) | **kept** | |
| `Add` | `Aggiungi` | (name exists) | `Append` | go-package:installatore/motore |
| `After` | `Dopo` | (name exists) | `Afterwards` | go-package:installatore/motore |
| `CARD` | `SCHEDA` | (name exists) | `GPU_CARD` | sh:banchi/17-distro/scatole/17-scatola.sh |
| `COMMAND` | `COMANDO` | (name exists) | `CMD` | go-package:installatore/motore |
| `Call` | `Chiama` | (name exists) | `Invoke` | file:installatore/motore/dbus.go; go-package:installatore/motore |
| `Check` | `Controlla`, `Controllo` | `Controllo` | `Controlla`→`Verify` | file:installatore/interfaccia/sessione.go; file:installatore/interfaccia/tui/tui.go |
| `Do` | `Fai` | (name exists) | `Make` | go-package:installatore/motore |
| `Done` | `Fatti`, `Fatto` | `Fatto` | `Fatti`→**kept** | file:installatore/motore/profilo.go; go-package:installatore/motore |
| `EXPECTED` | `ATTESI`, `ATTESO` | `ATTESO` | `ATTESI`→`AWAITED` | sh:banchi/01-b11-lancia.sh |
| `Env` | `Amb` | (name exists) | `EnvVars` | go-package:installatore/motore |
| `Error` | `Errore` | (name exists) | `Failure` | file:installatore/interfaccia/sessione.go; file:installatore/interfaccia/tui/tui.go |
| `Excluded` | `Esclusa`, `Escluse` | `Escluse` | `Esclusa`→`LeftOut` | file:installatore/motore/compatibilita.go; go-package:installatore/motore |
| `Format` | `Formato` | (name exists) | `Fmt` | file:installatore/motore/formato.go; go-package:installatore/motore |
| `Graphical` | `Grafica`, `Grafici` | `Grafica` | `Grafici`→`Charts` | file:installatore/motore/azione_sessioni.go; go-package:installatore/motore |
| `Minimum` | `Minima`, `Minimo` | `Minima` | `Minimo`→`MinV` | file:installatore/motore/compatibilita.go; go-package:installatore/motore |
| `Mode` | `Modo` | (name exists) | `Manner` | file:installatore/motore/azione_file.go; file:installatore/motore/azione_registri_utente.go |
| `Name` | `Nome` | (name exists) | `LabelName` | go-package:installatore/motore |
| `Node` | `Nodo` | (name exists) | `NodeV` | go-package:installatore/motore |
| `Note` | `Nota` | (name exists) | `Remark` | file:installatore/cmd/remotix-install/main.go; file:installatore/motore/compatibilita.go |
| `Now` | `Adesso` | (name exists) | `Current` | file:installatore/motore/operazione.go; go-package:installatore/motore |
| `Now` | `Adesso`, `Ora` | `Ora` | `Adesso`→`Current` | file:installatore/motore/finti_test.go; file:installatore/motore/operazione.go |
| `Now` | `Ora` | (name exists) | `Current` | go-package:installatore/motore |
| `Object` | `Oggetto` | (name exists) | `Obj` | go-package:installatore/motore |
| `Open` | `Aperta` | (name exists) | `Opened` | go-package:installatore/motore |
| `Path` | `Percorso` | (name exists) | `RoutePath` | go-package:installatore/motore |
| `REASON` | `MOT`, `MOTIVO` | `MOT` | `MOTIVO`→`CAUSE` | file:src/pagina.html |
| `Remove` | `Togli` | (name exists) | **kept** | file:installatore/motore/certifica_test.go; file:installatore/motore/disinstalla.go |
| `Run` | `Esegui` | (name exists) | `Execute` | file:installatore/motore/ambiente.go; file:installatore/motore/certifica_test.go |
| `SCENE` | `SCENA` | (name exists) | `SCENE_V` | py:banchi/04-b28-gesti.py |
| `SLOT_TAKEN` | `POSTO_OCCUPATO`, `POSTO_PRESO` | `POSTO_PRESO` | `POSTO_OCCUPATO`→`SLOT_V_TAKEN` | tu:banchi/rcp/rcp.c; tu:src/rcp.c |
| `Signal` | `Segnale` | (name exists) | `Sig` | go-package:installatore/motore |
| `TREE` | `ALB`, `ALBERO` | `ALBERO` | `ALB`→`TREE_DIR` | py:banchi/07-b64-rete.py; py:banchi/07-b64-scena.py |
| `Text` | `Testo` | (name exists) | `Content` | go-package:installatore/motore |
| `Type` | `Tipo` | (name exists) | `TypeName` | go-package:installatore/interfaccia/tui |
| `VERIFIED` | `VERIFICATA`, `VERIFICATO` | `VERIFICATA` | `VERIFICATO`→`CHECKED` | go-package:installatore/motore |
| `Value` | `Valore` | (name exists) | `Val` | go-package:installatore/motore |
| `Write` | `Scrivi` | (name exists) | `PutOut` | go-package:installatore/motore |
| `action` | `azione` | (name exists) | `act` | py:banchi/15-suite/15-giro.py; py:banchi/16-stress/16-attore-rdp.py |
| `actions` | `azioni` | (name exists) | `acts` | py:banchi/16-stress/16-attore.py |
| `active` | `attiva` | (name exists) | `live` | file:grafica/sito-mockup/stile.css |
| `active` | `attiva`, `attive` | `attiva` | `attive`→**kept** | go-package:installatore/motore |
| `active` | `attivo` | (name exists) | `live` | file:src/pagina.html |
| `add` | `agg`, `aggiungi` | `agg` | `aggiungi`→`insert` | go-package:installatore/motore |
| `add` | `aggiungi` | (name exists) | `insert` | py:banchi/01-b3-cliente.py |
| `admitted` | `amm`, `ammesso` | `ammesso` | `amm`→`adm` | py:banchi/15-suite/15-f025-stesso-utente-due-schede.py; py:banchi/15-suite/15-f027-parola-e-ban.py |
| `after` | `dopo` | (name exists) | `afterwards` | file:src/pagina.html |
| `after_scene` | `dopo_la_scena`, `dopo_scena` | `dopo_la_scena` | `dopo_scena`→`afterwards_scene` | tu:banchi/02-cattura-fotogramma.c; tu:banchi/02-cattura-prodotto.c |
| `aligned` | `allineate`, `allineati` | `allineate` | `allineati`→`in_line` | py:banchi/16-stress/16-attore.py |
| `alive` | `vivi`, `vivo` | `vivo` | `vivi`→`living` | py:banchi/16-stress/16-salita.py |
| `all` | `tutte` | (name exists) | **kept** | py:banchi/01-b8-cronometro.py; py:banchi/16-stress/16-classifica.py |
| `all` | `tutti`, `tutto` | `tutti` | `tutto`→`everything` | go-package:installatore/motore |
| `all` | `tutti` | (name exists) | `all_v` | py:banchi/01-b7-congedo.py; py:banchi/04-b28-gesti.py |
| `all` | `tutti`, `tutto` | `tutti` | `tutto`→`everything` | py:banchi/15-suite/15-f008-modificatori.py |
| `all` | `tutto` | (name exists) | `everything` | file:packaging/debian/rules; py:banchi/15-suite/15-f008-modificatori.py |
| `alpha` | `alfa` | (name exists) | `alpha_ch` | py:banchi/16-stress/16-lavori.py |
| `app_requested` | `app_chiesti`, `app_chiesto` | `app_chiesto` | `app_chiesti`→`app_asked` | tu:banchi/rcp/rcp.c; tu:src/rcp.c |
| `args` | `argomenti` | (name exists) | **kept** | go-package:installatore/motore; py:banchi/11-scatole/11-c2-una-finestra-si-apre.py |
| `arrived` | `arrivata`, `arrivati` | `arrivati` | `arrivata`→`landed` | py:banchi/01-b7-congedo.py |
| `arrived` | `arrivati`, `arrivato` | `arrivati` | `arrivato`→`landed` | tu:src/cattura.c |
| `attached` | `attaccata`, `attaccate` | `attaccate` | `attaccata`→`attached_to` | tu:banchi/rcp/rcp.c; tu:src/rcp.c |
| `background` | `fondo` | (name exists) | `backstop` | file:grafica/sito-mockup/stile.css |
| `banned` | `bannate`, `bannati`, `bannato` | `bannato` | `bannate`→**kept**, `bannati`→**kept** | py:banchi/01-b8-cronometro.py |
| `before` | `prima` | (name exists) | `earlier` | file:src/pagina.html |
| `body` | `corpo` | (name exists) | `body_el` | file:banchi/01-b11-pagina.html; file:banchi/01-b2-sonda.html |
| `border` | `cornice` | (name exists) | `frame_border` | file:src/pagina.html |
| `born` | `nati`, `nato` | `nato` | `nati`→`spawned` | py:banchi/16-stress/16-salita.py |
| `box` | `scat`, `scatola` | `scatola` | `scat`→`bx` | py:banchi/16-stress/16-risorse.py |
| `box` | `scatola` | (name exists) | `container_box` | py:banchi/16-stress/16-salita.py |
| `broken` | `guasta`, `rotta` | `guasta` | `rotta`→`damaged` | py:banchi/09-b78-apertura.py |
| `broken` | `guasta`, `rotto` | `rotto` | `guasta`→`faulty` | go-package:installatore/motore |
| `build` | `costruisci` | (name exists) | `make_build` | sh:banchi/11-scatole/11-accendi.sh; sh:banchi/17-distro/scatole/17-scatola.sh |
| `button` | `bottone` | (name exists) | **kept** | file:banchi/01-s7-pagina.html; py:banchi/15-suite/15-g1b-comune.py |
| `button` | `pulsante` | (name exists) | `btn_el` | file:grafica/sito-mockup/performance.html |
| `buttons` | `bottoni` | (name exists) | `btns` | file:src/pagina.html |
| `buttons` | `bottoni`, `pulsanti` | `bottoni` | `pulsanti`→**kept** | tu:src/input.c |
| `call` | `chiama` | (name exists) | `invoke` | file:src/pagina.html |
| `candidate` | `candidata` | (name exists) | **kept** | c-program:src; tu:src/ritrovo.c |
| `candidate` | `candidato` | (name exists) | **kept** | c-program:src |
| `canvas` | `tela` | (name exists) | `canvas_size` | file:src/pagina.html |
| `capture` | `cattura` | (name exists) | `capture_v` | tu:src/figlio.c |
| `card` | `scheda` | (name exists) | `gpu_card` | sh:banchi/19-nvidia/19-nv-macchina.sh; tu:src/figlio.c |
| `cause` | `causa` | (name exists) | `reason_why` | py:banchi/09-b81-linea-morta.py |
| `cell` | `casella`, `una_casella` | `casella` | `una_casella`→`a_cell` | py:banchi/09-b79-cure.py |
| `check` | `controlla` | (name exists) | `inspect` | py:docs/sources/build.py; py:docs/sources/technical/ch01_introduction.py |
| `check` | `controllo` | (name exists) | `verification` | file:installatore/interfaccia/tui/tui.go; go-package:installatore/interfaccia/tui |
| `checks` | `controlli` | (name exists) | `verifications` | file:installatore/motore/testi.go; go-package:installatore/motore |
| `choices` | `scelte` | (name exists) | `picks` | py:banchi/19-nvidia/19-nv-suite.py |
| `chroma` | `croma` | (name exists) | `chroma_v` | tu:src/codificatore.c |
| `clipboard` | `appunti` | (name exists) | `clipboard_text` | file:banchi/01-b11-pagina.html; file:src/pagina.html |
| `closed` | `chiusa` | (name exists) | **kept** | file:src/pagina.html |
| `closing` | `chiusura` | (name exists) | **kept** | py:banchi/01-b7-congedo.py |
| `code` | `codice` | (name exists) | `code_v` | file:src/pagina.html; py:banchi/15-suite/15-f009-accenti-e-altgr.py |
| `color` | `colore` | (name exists) | `colour` | file:grafica/sito-mockup/performance.html |
| `command` | `comanda`, `comando` | `comando` | `comanda`→**kept** | file:src/pagina.html; py:banchi/15-suite/15-f004-il-mouse.py |
| `command` | `comando` | (name exists) | `command_v` | sh:banchi/02-figlio-accendi.sh; sh:installatore/run.sh |
| `complete` | `completi`, `completo` | `completo` | `completi`→**kept** | file:src/pagina.html |
| `compliant` | `conforme` | (name exists) | `conformant` | py:banchi/01-b4-registrazioni.py |
| `compute` | `calcolo` | (name exists) | `calc` | py:banchi/16-stress/16-risorse.py |
| `conditions` | `condizioni` | (name exists) | `conds` | file:installatore/motore/testi.go; go-package:installatore/motore |
| `confirm` | `conferma`, `conferma-si` | `conferma` | `conferma-si`→`ack` | data:all; file:src/pagina.html |
| `connect` | `collega` | (name exists) | `link_up` | file:src/pagina.html |
| `consumed` | `consumati` | (name exists) | `used_up` | tu:src/webtransport.c |
| `context` | `contesto` | (name exists) | `context_v` | go-package:installatore/motore |
| `copy` | `copia` | (name exists) | **kept** | py:banchi/16-stress/16-risorse.py |
| `count` | `conta`, `conto` | `conto` | `conta`→`tally` | c-program:banchi/18-a1; py:banchi/09-b70-ritmo.py |
| `create` | `crea` | (name exists) | `spawn` | sh:banchi/17-distro/17-vm.sh |
| `created` | `creato` | (name exists) | `made` | tu:src/wlroots.c |
| `crop` | `ritaglia` | (name exists) | **kept** | py:banchi/15-suite/15-g4-comune.py |
| `cursor_metadata` | `cursore_metadati`, `cursore_metadato` | `cursore_metadato` | `cursore_metadati`→`pointer_shape_metadata` | tu:banchi/02-cattura-prodotto.c; tu:banchi/06-b33-risveglio.c |
| `data` | `dati` | (name exists) | `data_v` | file:banchi/16-stress/16-banco-tela.html; file:banchi/18-software/18-software-webcodecs.html |
| `days` | `giorni` | (name exists) | `day_count` | py:banchi/11-scatole/11-c12-il-gancio-e-vivo.py; py:banchi/11-scatole/11-c15-la-meta-remota-gira.py |
| `dead` | `morta`, `morto` | `morto` | `morta`→`dead_v` | py:banchi/09-b76-rete-cattiva.py |
| `declared` | `dichiarata`, `dichiarato` | `dichiarata` | `dichiarato`→**kept** | data:all; file:installatore/motore/testi.go |
| `degenerate` | `degenere`, `degeneri` | `degenere` | `degeneri`→`degenerate_v` | py:banchi/12-client-veri.py |
| `delivered` | `consegnata`, `consegnati` | `consegnati` | `consegnata`→`handed` | file:src/pagina.html |
| `delivered` | `consegnati`, `consegnato` | `consegnati` | `consegnato`→`handed` | py:banchi/01-b3-cliente.py |
| `depth` | `profondita` | (name exists) | `bit_depth` | file:src/pagina.html |
| `detail` | `dett`, `dettaglio` | `dettaglio` | `dett`→`det` | tu:banchi/04-b25-tastiera.c; tu:banchi/rcp/rcp.c |
| `distribution` | `distribuzione` | (name exists) | **kept** | sh:banchi/19-nvidia/19-nv-macchina.sh |
| `done` | `fatta`, `fatti` | `fatti` | `fatta`→**kept** | go-package:installatore/motore |
| `done` | `fatti` | (name exists) | **kept** | sh:banchi/02-codifica-lancia.sh |
| `drawing` | `disegno` | (name exists) | `drawing_v` | py:banchi/16-stress/16-rapporto.py |
| `empty` | `vuota`, `vuoto` | `vuota` | `vuoto`→`blank` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py; tu:src/sessione.c |
| `empty` | `vuoto` | (name exists) | `blank` | py:banchi/11-scatole/11-c8-il-secondo-apre-il-browser.py |
| `entries` | `voci` | (name exists) | `items_list` | file:banchi/01-b11-pagina.html |
| `env` | `amb` | (name exists) | `env_vars` | go-package:installatore/motore; py:banchi/02-sessione-dispositivi.py |
| `equal` | `uguale`, `uguali` | `uguali` | `uguale`→**kept** | tu:src/sessione.c |
| `error` | `errore` | (name exists) | `failure` | py:banchi/12-client-veri.py; py:banchi/16-stress/16-attore-rdp.py |
| `errors` | `errori` | (name exists) | `errs` | py:banchi/01-b8-cronometro.py; py:banchi/12-client-veri.py |
| `exists` | `esiste` | (name exists) | **kept** | py:banchi/16-stress/16-lavori.py |
| `exited` | `usciti`, `uscito` | `usciti` | `uscito`→`exited_v` | tu:src/figlio.c |
| `expected` | `att`, `attesi` | `att` | `attesi`→`awaited` | file:src/opus-wasm/prova/confronta.mjs |
| `expected` | `att`, `atteso` | `atteso` | `att`→**kept** | py:banchi/01-b5-violazioni.py; py:banchi/01-b6-tetti.py |
| `expected` | `attesi`, `atteso` | `atteso` | `attesi`→`awaited` | py:banchi/01-b2-sonda-trasporto.py; py:banchi/07-b64-orecchio.py |
| `expected` | `atteso` | (name exists) | `awaited` | py:banchi/01-b5-violazioni.py |
| `expected` | `atteso`, `previsti` | `atteso` | `previsti`→**kept** | py:banchi/11-scatole/11-c24-l-esci-chiude-sempre.py |
| `expression` | `espressione` | (name exists) | **kept** | py:banchi/02-pagina-misura-cdp.py |
| `failed` | `fallita` | (name exists) | `unsuccessful` | file:installatore/interfaccia/testi.go; go-package:installatore/interfaccia |
| `failed` | `fallita`, `fallito` | `fallita` | `fallito`→`unsuccessful` | file:installatore/interfaccia/tui/anteprima.go; file:installatore/motore/operazione.go |
| `failed` | `fallite` | (name exists) | `unsuccessful` | tu:src/wlroots.c |
| `failed` | `fallite`, `falliti` | `falliti` | `fallite`→`unsuccessful` | tu:banchi/13-w1-un-fotogramma.c; tu:src/cattura.c |
| `failed` | `fallite`, `falliti`, `fallito` | `falliti` | `fallite`→`unsuccessful`, `fallito`→`unsuccessful` | tu:src/wlroots.c |
| `failed` | `fallite`, `fallito` | `fallito` | `fallite`→`unsuccessful` | sh:banchi/11-scatole/11-gancio.sh |
| `failed` | `falliti` | (name exists) | `unsuccessful` | tu:src/wlroots.c |
| `failed` | `fallito` | (name exists) | `unsuccessful` | tu:src/wlroots.c |
| `fake` | `finta`, `finto` | `finto` | `finta`→`mock` | data:all; file:installatore/motore/finti_test.go |
| `family_compute` | `fam_calcolo`, `famiglia_calcolo` | `fam_calcolo` | `famiglia_calcolo`→`kin_compute` | tu:src/vulkanvideo.c |
| `family_encoding` | `fam_codifica`, `famiglia_codifica` | `fam_codifica` | `famiglia_codifica`→`kin_encoding` | tu:src/vulkanvideo.c |
| `fingerprint` | `impronta` | (name exists) | `fingerprint_v` | file:installatore/motore/testi.go; go-package:installatore/motore |
| `finished` | `fatto`, `finita` | `fatto` | `finita`→**kept** | file:banchi/01-b11-pagina.html; py:banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py |
| `fit_canvas` | `adatta_la_tela`, `adatta_tela` | `adatta_tela` | `adatta_la_tela`→`adapt_canvas` | py:banchi/02-filo-validatore.py |
| `focus` | `fuoco` | (name exists) | `focused` | file:src/pagina.html |
| `format` | `formato` | (name exists) | `format_v` | file:banchi/16-stress/16-banco-tela.html; file:banchi/18-software/18-software-webcodecs.html |
| `forward` | `avanti` | (name exists) | `ahead` | py:banchi/19-android/19-android.py |
| `found` | `trovata`, `trovati`, `trovato` | `trovati` | `trovata`→`located`, `trovato`→`located` | go-package:installatore/motore |
| `found` | `trovata`, `trovato` | `trovato` | `trovata`→`located` | py:banchi/09-b77-audio-riordino.py |
| `found` | `trovati`, `trovato` | `trovati` | `trovato`→`located` | tu:src/sessione.c |
| `found_again` | `ritrovati`, `ritrovato` | `ritrovati` | `ritrovato`→`refound` | tu:src/main.c |
| `fourth` | `quarta`, `quarto` | `quarto` | `quarta`→`fourth_v` | py:banchi/15-suite/15-f027-parola-e-ban.py |
| `frames` | `fotogrammi` | (name exists) | `frame_count` | sh:banchi/02-codifica-lancia.sh |
| `free` | `libera` | (name exists) | **kept** | tu:src/figlio.c; tu:src/vulkanvideo.c |
| `free` | `liberi`, `libero` | `libero` | `liberi`→**kept** | tu:src/figlio.c |
| `free` | `libero` | (name exists) | **kept** | tu:banchi/rcp/rcp.c; tu:src/figlio.c |
| `fresh` | `nuova`, `nuovo` | `nuovo` | `nuova`→`new_v` | tu:src/figlio.c; tu:src/input.c |
| `fresh` | `nuove`, `nuovi` | `nuove` | `nuovi`→**kept** | py:banchi/12-client-veri.py; py:banchi/16-stress/16-riclassifica.py |
| `fresh` | `nuove`, `nuovo` | `nuovo` | `nuove`→**kept** | go-package:installatore/motore |
| `frozen` | `congelata`, `congelato` | `congelata` | `congelato`→`frozen_v` | py:banchi/11-scatole/11-c3-i-fotogrammi-cambiano.py |
| `full` | `pieni`, `pieno` | `pieno` | `pieni`→`filled` | py:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py |
| `good` | `buona`, `buoni`, `buono` | `buono` | `buona`→**kept**, `buoni`→**kept** | py:banchi/01-b8-cronometro.py |
| `got` | `otten` | (name exists) | `obt` | py:banchi/11-scatole/11-c14-non-si-disturbano.py |
| `graphical` | `grafica`, `grafico` | `grafico` | `grafica`→`gfx` | go-package:installatore/motore |
| `green` | `verde` | (name exists) | `green_v` | py:banchi/02-cattura-giudica.py |
| `green` | `verde`, `verdi` | `verde` | `verdi`→**kept** | py:banchi/04-b28-gesti.py |
| `grid` | `griglia` | (name exists) | `grid_v` | file:grafica/sito-mockup/performance.html |
| `group` | `gruppo` | (name exists) | `grp` | file:installatore/motore/azione_gruppo.go; go-package:installatore/motore |
| `groups` | `gruppi` | (name exists) | `group_list` | file:installatore/interfaccia/tui/anteprima.go; file:installatore/interfaccia/tui/tui.go |
| `healthy` | `sani`, `sano` | `sano` | `sani`→`sound_ok` | py:banchi/15-suite/15-f008-modificatori.py |
| `height` | `alt`, `altezza` | `altezza` | `alt`→`alt_h` | py:banchi/01-b3-cliente.py; py:banchi/01-b4-validatore.py |
| `height` | `altezza` | (name exists) | `height_px` | file:src/pagina.html; tu:banchi/14-f1-forma.c |
| `hex` | `esa` | (name exists) | `hex_s` | go-package:installatore/motore |
| `hide` | `nascondi` | (name exists) | `conceal` | file:src/pagina.html |
| `hook_local` | `gancio_locale`, `gancio_locali` | `gancio_locale` | `gancio_locali`→`hook_fn_local` | c-program:src; tu:src/webtransport.c |
| `hook_local_ctx` | `gancio_locale_ctx`, `gancio_locali_ctx` | `gancio_locale_ctx` | `gancio_locali_ctx`→`hook_fn_local_ctx` | c-program:src; tu:src/webtransport.c |
| `how_many` | `quante`, `quanti` | `quanti` | `quante`→`how_many_n` | file:banchi/01-b11-pagina.html; file:src/pagina.html |
| `image` | `immagine` | (name exists) | `picture` | tu:src/vulkanvideo.c |
| `installed` | `installata`, `installati` | `installati` | `installata`→`set_up` | file:installatore/motore/disinstalla_test.go |
| `installed` | `installata`, `installati`, `installato` | `installato` | `installata`→`set_up`, `installati`→`set_up` | go-package:installatore/motore |
| `installed` | `installati`, `installato` | `installato` | `installati`→`set_up` | py:banchi/11-scatole/11-c12-il-gancio-e-vivo.py |
| `job` | `mestiere` | (name exists) | **kept** | file:installatore/motore/testi.go; go-package:installatore/motore |
| `judge` | `giudica`, `giudice` | `giudica` | `giudice`→`assessor` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py; py:banchi/11-scatole/11-c3-i-fotogrammi-cambiano.py |
| `judged` | `giudicati`, `giudicato` | `giudicati` | `giudicato`→`assessed` | py:banchi/01-b4-validatore.py |
| `key` | `chiave` | (name exists) | `key_id` | file:src/pagina.html; py:banchi/03-marca.py |
| `key` | `chiave`, `tasto` | `chiave` | `tasto`→`keycap` | py:banchi/19-android/19-android.py |
| `key` | `tasto` | (name exists) | `keycap` | py:banchi/12-client-veri.py; py:banchi/16-stress/16-attore.py |
| `keyboard` | `tastiera` | (name exists) | **kept** | file:src/pagina.html |
| `keyboard_open` | `tastiera_aperta`, `tastiera_apri` | `tastiera_apri` | `tastiera_aperta`→`kbd_open` | file:src/pagina.html |
| `keys` | `tasti` | (name exists) | `keys_v` | file:src/pagina.html |
| `kill` | `uccidi` | (name exists) | `terminate` | py:banchi/15-suite/15-g6-comune.py; py:banchi/16-stress/16-salita.py |
| `kind` | `genere`, `tipo` | `tipo` | `genere`→**kept** | tu:src/webtransport.c |
| `label` | `etich`, `etichetta` | `etichetta` | `etich`→**kept** | file:grafica/sito-mockup/performance.html |
| `label` | `etichetta` | (name exists) | `tag_label` | file:grafica/sito-mockup/stile.css; file:src/pagina.html |
| `language` | `lingua` | (name exists) | `lang` | file:banchi/sonda/sonda-rcp.html; file:src/pagina.html |
| `laptop` | `portatile` | (name exists) | **kept** | file:grafica/sito-mockup/index.html |
| `last` | `ult`, `ultimo` | `ultimo` | `ult`→`lst` | py:banchi/01-b3-cliente.py |
| `last` | `ultima`, `ultimi` | `ultima` | `ultimi`→`latest` | py:banchi/11-scatole/11-c13-la-certificazione-e-recente.py |
| `last` | `ultima`, `ultimo` | `ultimo` | `ultima`→`latest` | py:banchi/09-b76-rete-cattiva.py; py:banchi/11-scatole/11-c8b-la-pagina-si-vede-dal-cliente.py |
| `last` | `ultimi`, `ultimo` | `ultimo` | `ultimi`→`latest` | py:banchi/11-scatole/11-c15-la-meta-remota-gira.py |
| `late` | `tardive`, `tardivi` | `tardivi` | `tardive`→`belated` | py:banchi/16-stress/16-attore.py |
| `late` | `tardivi`, `tardo` | `tardivi` | `tardo`→`belated` | py:banchi/01-b3-cliente.py |
| `layout` | `disposizione` | (name exists) | `arrangement` | tu:banchi/04-b25-guasti.c; tu:banchi/04-b25-tastiera.c |
| `left` | `sinistra` | (name exists) | **kept** | file:src/pagina.html |
| `left` | `sx` | (name exists) | `sx_l` | file:src/pagina.html; py:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py |
| `level_idc` | `livello_idc` | (name exists) | `lvl_idc` | tu:src/vadiretta.c; tu:src/vulkanvideo.c |
| `line` | `linea`, `riga` | `riga` | `linea`→`row` | py:banchi/09-b70-ritmo.py; py:banchi/17-t8/t8-browser.py |
| `line` | `riga` | (name exists) | `row` | file:grafica/tui-mockup/index.html |
| `line` | `riga`, `una_riga` | `riga` | `una_riga`→`a_line` | py:banchi/19-android/19-android.py |
| `lines` | `righe` | (name exists) | `line_list` | py:docs/sources/build.py; py:docs/sources/technical/ch01_introduction.py |
| `list` | `elenca`, `elenco` | `elenco` | `elenca`→**kept** | tu:src/sessione.c |
| `list` | `elenco` | (name exists) | `listing` | py:banchi/02-figlio-prova.py; py:banchi/09-b76-rete-cattiva.py |
| `list` | `elenco`, `lista` | `elenco` | `lista`→**kept** | tu:src/vulkanvideo.c |
| `local` | `locale` | (name exists) | `local_v` | tu:src/trasporto.c |
| `lock` | `lucchetto`, `serratura` | `lucchetto` | `serratura`→`lock_v` | go-package:installatore/motore |
| `locks` | `lucchetti` | (name exists) | `lock_set` | go-package:installatore/motore |
| `log` | `registra` | (name exists) | `record` | sh:banchi/02-cattura-lancia.sh; sh:banchi/02-sessione-guardia.sh |
| `log` | `registra`, `registro` | `registro` | `registra`→`record` | tu:src/comando.c; tu:src/figlio.c |
| `log` | `registro` | (name exists) | `logbook` | file:installatore/interfaccia/testi.go; go-package:installatore/interfaccia |
| `long` | `lunga`, `lunghe` | `lunga` | `lunghe`→`lengthy` | py:banchi/15-suite/15-giro.py |
| `lost` | `persa`, `persi`, `perso` | `persi` | `persa`→**kept**, `perso`→**kept** | py:banchi/09-b76-rete-cattiva.py |
| `machine` | `macchina` | (name exists) | `host` | py:banchi/16-stress/16-risorse.py |
| `margin` | `margine` | (name exists) | `headroom` | py:banchi/09-b81-linea-morta.py |
| `mark` | `marca`, `segna` | `marca` | `segna`→`mark_it` | py:banchi/01-b4-validatore.py |
| `maximum` | `massima`, `massimo` | `massimo` | `massima`→`max_v` | py:banchi/01-b4-validatore.py; py:banchi/02-cattura-giudica.py |
| `measure` | `misura` | (name exists) | `gauge` | py:banchi/15-suite/15-g1b-esplora.py |
| `memory` | `memoria` | (name exists) | **kept** | tu:banchi/02-cattura-fotogramma.c; tu:banchi/02-cattura-prodotto.c |
| `method` | `metodo` | (name exists) | `meth` | file:grafica/sito-mockup/performance.html; py:banchi/04-b28-gesti.py |
| `minimum` | `minima`, `minimo` | `minimo` | `minima`→**kept** | go-package:installatore/motore |
| `missed` | `mancati`, `mancati--` | `mancati` | `mancati--`→**kept** | file:src/pagina.html |
| `missing` | `manca`, `mancano` | `manca` | `mancano`→`lacking` | data:all; file:installatore/interfaccia/vista.go |
| `missing` | `manca`, `mancano`, `mancanti` | `manca` | `mancano`→`lacking`, `mancanti`→**kept** | go-package:installatore/motore |
| `missing` | `manca`, `mancante` | `manca` | `mancante`→**kept** | py:banchi/01-b7-congedo.py |
| `mode` | `modo` | (name exists) | `manner` | file:src/pagina.html |
| `model` | `modello` | (name exists) | `pattern` | file:src/pagina.html |
| `modifier` | `modificatore` | (name exists) | `modifier_key` | tu:src/cattura.c; tu:src/wlroots.c |
| `move` | `muovi` | (name exists) | **kept** | py:banchi/12-client-veri.py |
| `mute` | `muta` | (name exists) | `muted` | py:banchi/11-scatole/11-c14-non-si-disturbano.py |
| `mute` | `muta`, `muti` | `muti` | `muta`→`muted` | py:banchi/09-b70-ritmo.py |
| `mute` | `muti`, `muto` | `muto` | `muti`→`muted` | py:banchi/09-b81-linea-morta.py; py:banchi/09-b84-audio-silenzio.py |
| `my_base` | `mia_base`, `mio_base` | `mio_base` | `mia_base`→`own_base` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py |
| `name` | `nome` | (name exists) | `label_name` | file:banchi/01-b11-pagina.html; file:src/pagina.html |
| `names` | `nomi`, `nomina` | `nomi` | `nomina`→`naming` | py:banchi/01-b8-cronometro.py |
| `network` | `rete` | (name exists) | `net` | py:banchi/12-client-veri.py |
| `next` | `prossimo` | (name exists) | `upcoming` | file:src/pagina.html; py:banchi/16-stress/16-salita.py |
| `node` | `nodo` | (name exists) | `node_v` | sh:banchi/16-stress/16-d023-cornice.sh |
| `none` | `nessuno` | (name exists) | `nobody` | file:installatore/interfaccia/vista.go; file:installatore/motore/testi.go |
| `nonexistent` | `inesistente`, `inesistenti` | `inesistente` | `inesistenti`→`missing_ones` | py:banchi/01-b8-cronometro.py |
| `notStillDone` | `nonAncoraFatta`, `nonAncoraFatti` | `nonAncoraFatta` | `nonAncoraFatti`→`noStillDone` | file:installatore/motore/azioni_dichiarate.go; go-package:installatore/motore |
| `not_measured` | `non_misurate`, `non_misurato` | `non_misurato` | `non_misurate`→`no_measured` | py:banchi/16-stress/16-classifica.py |
| `note` | `nota` | (name exists) | `remark` | file:banchi/sonda/sonda-rcp.html; file:installatore/catalogo/catalogo.json |
| `now` | `adesso` | (name exists) | `now_v` | file:src/pagina.html |
| `now` | `adesso`, `ora` | `ora` | `adesso`→`now_v` | file:installatore/motore/operazione.go; file:src/pagina.html |
| `now` | `ora` | (name exists) | `time_now` | file:banchi/01-s7-pagina.html; file:banchi/16-stress/16-banco-tela.html |
| `now_ms` | `adesso_ms`, `ora_ms` | `ora_ms` | `adesso_ms`→`current_ms` | tu:src/figlio.c |
| `now_us` | `adesso_us`, `ora_us` | `ora_us` | `adesso_us`→`current_us` | c-program:src |
| `number` | `numero` | (name exists) | **kept** | py:docs/sources/build.py; py:docs/sources/technical/ch01_introduction.py |
| `obscured` | `oscurati`, `oscurato` | `oscurati` | `oscurato`→`darkened` | py:banchi/01-b4-validatore.py |
| `old` | `vecchi`, `vecchia` | `vecchia` | `vecchi`→`prior` | file:src/pagina.html; py:banchi/01-b3-cliente.py |
| `old` | `vecchie`, `vecchio` | `vecchio` | `vecchie`→**kept** | tu:src/sessione.c |
| `old` | `vecchio` | (name exists) | `prior` | tu:banchi/18-a1/18-a1-opus-senza-ffmpeg.c |
| `on` | `accesa` | (name exists) | `lit` | py:banchi/09-b81-linea-morta.py |
| `on` | `accesa`, `accese` | `accesa` | `accese`→`lit` | sh:banchi/17-distro/scatole/17-scatola.sh |
| `on` | `accesa`, `acceso` | `acceso` | `accesa`→`lit` | py:banchi/09-b81-linea-morta.py; tu:src/codificatore.c |
| `on` | `accese`, `acceso` | `acceso` | `accese`→`lit` | py:banchi/19-android/19-android.py |
| `on` | `acceso` | (name exists) | `lit` | py:banchi/09-b81-linea-morta.py; py:banchi/12-client-veri.py |
| `open` | `aperta` | (name exists) | `is_open` | go-package:installatore/motore; py:banchi/09-b79-cure.py |
| `open` | `aperta`, `aperte` | `aperta` | `aperte`→`opened` | py:banchi/09-b78-apertura.py |
| `open` | `aperta`, `aperto` | `aperta` | `aperto`→`is_open` | py:banchi/09-b81-linea-morta.py |
| `open` | `aperte` | (name exists) | `opened` | py:banchi/09-b78-apertura.py |
| `open` | `aperti` | (name exists) | `opened` | py:banchi/16-stress/16-attore.py |
| `open` | `aperto` | (name exists) | `is_open` | py:banchi/09-b81-linea-morta.py; tu:src/figlio.c |
| `opt` | `opz` | (name exists) | `opts` | sh:banchi/11-scatole/11-gancio.sh |
| `origin` | `origine` | (name exists) | `source_origin` | py:banchi/15-suite/15-f014-appunti.py |
| `other` | `altra` | (name exists) | **kept** | file:installatore/interfaccia/vista.go; go-package:installatore/interfaccia |
| `other` | `altre`, `altro` | `altro` | `altre`→**kept** | go-package:installatore/interfaccia |
| `other` | `altro` | (name exists) | `other_one` | file:installatore/interfaccia/tui/tui.go; go-package:installatore/interfaccia |
| `our` | `nostre`, `nostri`, `nostro` | `nostro` | `nostre`→`ours`, `nostri`→`ours` | go-package:installatore/motore |
| `out` | `fuori` | (name exists) | `outside` | file:src/pagina.html; go-package:installatore/motore |
| `outcomes` | `esiti`, `esiti_` | `esiti` | `esiti_`→**kept** | py:banchi/11-scatole/11-c8b-la-pagina-si-vede-dal-cliente.py |
| `output` | `uscita` | (name exists) | `out_dir` | file:banchi/16-stress/16-banco-tela.html; sh:banchi/15-suite/15-compositori.sh |
| `package` | `pacchetto` | (name exists) | **kept** | go-package:installatore/motore |
| `page` | `pag`, `pagina` | `pagina` | `pag`→`pg` | py:banchi/04-b28-gesti.py; py:banchi/15-suite/15-f022-orologi.py |
| `page` | `pagina` | (name exists) | `page_v` | py:docs/sources/build.py; py:docs/sources/technical/ch01_introduction.py |
| `painted` | `dipinta`, `dipinti`, `dipinto` | `dipinti` | `dipinta`→**kept**, `dipinto`→**kept** | file:src/pagina.html |
| `path` | `cammino`, `percorso` | `percorso` | `cammino`→**kept** | go-package:installatore/motore |
| `path` | `il_percorso`, `percorso` | `percorso` | `il_percorso`→`the_path` | py:banchi/01-b5-violazioni.py |
| `path` | `perc`, `percorso` | `percorso` | `perc`→`pth` | py:banchi/09-b81-linea-morta.py; py:banchi/10-f1-testimone.py |
| `path` | `percorso` | (name exists) | `route_path` | py:banchi/01-b7-congedo.py; py:banchi/02-cattura-giudica.py |
| `pause` | `pausa` | (name exists) | `pause_v` | py:banchi/15-suite/15-g2-scena.py; py:banchi/15-suite/15-g7-comune.py |
| `pending` | `pendenti`, `sospesi` | `sospesi` | `pendenti`→`outstanding` | py:banchi/16-stress/16-attore.py |
| `pending` | `sospesi`, `sospeso` | `sospesi` | `sospeso`→**kept** | file:src/pagina.html |
| `photo` | `foto` | (name exists) | `picture` | py:banchi/15-suite/15-g1b-esplora.py; sh:banchi/17-t6/t6-giro.sh |
| `photo` | `foto`, `fotografia` | `foto` | `fotografia`→**kept** | py:banchi/17-t7/t7-aggiorna.py |
| `pipe` | `tubo` | (name exists) | `pipe_fd` | tu:src/figlio.c |
| `platform` | `piattaforma` | (name exists) | `platform_v` | file:src/pagina.html |
| `point` | `punto` | (name exists) | **kept** | py:banchi/16-stress/16-lavori.py |
| `pointer` | `puntatore` | (name exists) | `ptr` | file:src/pagina.html |
| `policy` | `politica` | (name exists) | `policy_v` | py:banchi/07-b64-scena.py |
| `port` | `porta` | (name exists) | `port_n` | file:installatore/interfaccia/tui/tui.go; file:installatore/interfaccia/vista.go |
| `prefix` | `prefisso` | (name exists) | `pfx` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py; py:banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py |
| `present` | `presente`, `presenti` | `presenti` | `presente`→`there` | c-program:src; tu:src/main.c |
| `primary` | `princ`, `principale` | `principale` | `princ`→**kept** | file:installatore/motore/azione_gruppo.go; go-package:installatore/motore |
| `print` | `stampa` | (name exists) | `print_out` | py:banchi/02-filo-validatore.py; py:banchi/04-b28-gesti.py |
| `probe` | `sonda`, `sonda_una` | `sonda` | `sonda_una`→`probe_v` | file:src/pagina.html |
| `profile` | `profilo` | (name exists) | `profile_v` | py:banchi/09-b77-audio-riordino.py; py:banchi/09-b79-cure.py |
| `push` | `spingi` | (name exists) | `shove` | file:src/pagina.html |
| `put` | `metti` | (name exists) | `place` | sh:banchi/02-figlio-lancia.sh |
| `r` | `erre` | (name exists) | `r_ch` | py:banchi/02-cattura-giudica.py |
| `read` | `letta` | (name exists) | `was_read` | file:src/pagina.html |
| `read` | `letta`, `letto` | `letto` | `letta`→`was_read` | file:src/pagina.html; py:banchi/09-b79-cure.py |
| `read` | `letti` | (name exists) | `bytes_read` | tu:src/appunti.c; tu:src/figlio.c |
| `read` | `letti`, `letto` | `letto` | `letti`→`bytes_read` | py:banchi/15-suite/15-g6-comune.py |
| `read` | `letto` | (name exists) | `was_read` | file:src/pagina.html |
| `read_mark` | `leggi_la_marca`, `leggi_marca` | `leggi_la_marca` | `leggi_marca`→`read_it_mark` | py:banchi/10-f1-testimone.py |
| `ready` | `pronta`, `pronte` | `pronta` | `pronte`→`prepared` | tu:src/forma.c |
| `ready` | `pronto` | (name exists) | `prepared` | file:src/pagina.html; tu:src/wlroots.c |
| `reason` | `mot` | (name exists) | **kept** | file:banchi/01-b11-pagina.html; file:src/pagina.html |
| `reason` | `motivo` | (name exists) | `why_text` | file:banchi/01-b11-pagina.html; file:src/pagina.html |
| `reason` | `motivo`, `ragione` | `motivo` | `ragione`→`reason_v` | py:banchi/15-suite/15-f008-modificatori.py; py:banchi/16-stress/16-attore-rdp.py |
| `reborn` | `rinasce`, `rinate` | `rinasce` | `rinate`→`respawned` | py:banchi/11-scatole/11-c24-l-esci-chiude-sempre.py |
| `received` | `ricevuti` | (name exists) | `got_n` | py:banchi/07-b64-rete.py |
| `received` | `ricevuti`, `ricevuto` | `ricevuti` | `ricevuto`→**kept** | py:banchi/01-b3-cliente.py; py:banchi/16-stress/16-attore.py |
| `red` | `rosse`, `rosso` | `rosso` | `rosse`→`reds` | py:banchi/02-cattura-giudica.py |
| `remedy` | `rimedio` | (name exists) | **kept** | file:installatore/motore/testi.go; go-package:installatore/motore |
| `remote` | `remoto` | (name exists) | `far_end` | tu:src/trasporto.c |
| `requested` | `chiesta`, `chiesti`, `chiesto` | `chiesto` | `chiesta`→`asked`, `chiesti`→`asked` | file:src/pagina.html |
| `requested` | `chieste`, `chiesti` | `chiesti` | `chieste`→`asked` | tu:banchi/13-w1-un-fotogramma.c; tu:src/cattura.c |
| `requested` | `chieste`, `chiesto` | `chiesto` | `chieste`→`asked` | py:banchi/09-b76-rete-cattiva.py |
| `reread` | `rileggi`, `rilette`, `riletto` | `riletto` | `rileggi`→`read_again`, `rilette`→`read_again` | tu:src/sessione.c |
| `resize_a` | `ridim_a`, `ridimensiona_a` | `ridim_a` | `ridimensiona_a`→`rescale_a` | tu:banchi/18-scheda/18-confronto.c; tu:banchi/19-vulkan/19-confronto.c |
| `resolve` | `risolvi` | (name exists) | `resolve_it` | file:src/pagina.html |
| `restart` | `riavvia` | (name exists) | `reboot` | sh:banchi/17-distro/scatole/17-scatola.sh |
| `restart` | `riavvia`, `riavvio` | `riavvio` | `riavvia`→`reboot` | sh:banchi/17-distro/17-t10.sh |
| `restart` | `riavvio` | (name exists) | `reboot` | sh:banchi/19-nvidia/19-nv-macchina.sh |
| `restored` | `rimessa`, `rimessi` | `rimessi` | `rimessa`→`put_back` | py:banchi/09-b76-rete-cattiva.py |
| `resume` | `riprendi` | (name exists) | `continue_it` | go-package:installatore/motore |
| `right` | `destra` | (name exists) | **kept** | file:grafica/sito-mockup/index.html; file:grafica/sito-mockup/performance.html |
| `right` | `destro`, `dx` | `dx` | `destro`→`right_side` | py:banchi/11-scatole/11-c22-il-bordo-si-trascina.py; py:banchi/15-suite/15-f003-lo-schermo-si-aggiorna.py |
| `right` | `dx` | (name exists) | `dx_r` | file:src/pagina.html |
| `round` | `il_giro` | (name exists) | `the_round` | py:banchi/11-scatole/11-c4-il-tasto-arriva-allo-schermo.py |
| `round` | `un_giro` | (name exists) | `a_round` | py:banchi/09-b78-apertura.py; py:banchi/11-scatole/11-c2-una-finestra-si-apre.py |
| `rule` | `regola` | (name exists) | `rule_v` | py:banchi/09-b77-audio-riordino.py |
| `run` | `corri` | (name exists) | `run_it` | py:banchi/11-scatole/11-c17-gli-appunti-vanno-nei-due-versi.py; py:banchi/12-client-veri.py |
| `run` | `corri`, `esegui` | `esegui` | `corri`→`run_it` | py:banchi/16-stress/16-attore.py |
| `run` | `corsa` | (name exists) | `run_n` | sh:banchi/02-cattura-lancia.sh |
| `run` | `esegui` | (name exists) | `execute` | py:banchi/15-suite/15-d006-misura.py; py:banchi/15-suite/15-f001-accesso-e-prima-immagine.py |
| `run` | `esegui`, `gira` | `gira` | `esegui`→`execute` | c-program:src; py:banchi/01-b8-cronometro.py |
| `said` | `detta`, `detto` | `detto` | `detta`→`stated` | py:banchi/11-scatole/11-c2-una-finestra-si-apre.py |
| `said` | `detti`, `detto` | `detto` | `detti`→`stated` | go-package:installatore/motore |
| `said_format_card` | `detto_formato_scheda`, `detto_il_formato_scheda` | `detto_formato_scheda` | `detto_il_formato_scheda`→`stated_format_card` | tu:src/wlroots.c |
| `sampler` | `campionatore` | (name exists) | `sampler_obj` | tu:src/vulkanvideo.c |
| `save` | `salva` | (name exists) | `store` | py:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py; py:banchi/12-client-veri.py |
| `scale` | `scala` | (name exists) | `scale_v` | py:banchi/02-sessione-stato.py |
| `scan` | `scansiona`, `scansione` | `scansione` | `scansiona`→`scan_it` | py:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py |
| `scene` | `la_scena`, `scena` | `scena` | `la_scena`→`the_scene` | py:banchi/15-suite/15-f014c-appunti-dal-computer.py |
| `search` | `ricerca` | (name exists) | `lookup` | py:banchi/16-stress/16-salita.py |
| `second` | `seconda` | (name exists) | `second_v` | py:banchi/16-stress/16-classifica.py |
| `second` | `seconda`, `secondo` | `secondo` | `seconda`→`second_v` | py:banchi/15-suite/15-f014c-appunti-dal-computer.py |
| `sections` | `sezioni` | (name exists) | **kept** | py:docs/sources/build.py; py:docs/sources/technical/ch01_introduction.py |
| `seen` | `visti` | (name exists) | `seen_n` | py:banchi/16-stress/16-risorse.py |
| `seen` | `visti`, `visto` | `visto` | `visti`→`seen_n` | go-package:installatore/motore; py:banchi/09-b77-audio-riordino.py |
| `seen` | `visto` | (name exists) | `seen_v` | py:banchi/02-filo-fotogramma.py; py:banchi/15-suite/15-f008-modificatori.py |
| `sent` | `mandati`, `spedite` | `spedite` | `mandati`→`dispatched` | file:src/pagina.html |
| `sentinel_local` | `sentinella_locale`, `sentinella_locali` | `sentinella_locali` | `sentinella_locale`→`sentinel_v_local` | c-program:src; tu:src/figlio.c |
| `serial` | `matricola` | (name exists) | `serial_no` | tu:src/figlio.c |
| `serial` | `matricola`, `seriale`, `serie` | `serie` | `matricola`→`serial_no`, `seriale`→`serial_v` | tu:src/figlio.c |
| `serial` | `seriale` | (name exists) | `serial_v` | file:banchi/02-sessione-scene/sana.json; py:banchi/02-sessione-stato.py |
| `serial` | `seriale`, `serie` | `serie` | `seriale`→`serial_v` | tu:src/sessione.c |
| `serial` | `serie` | (name exists) | `series` | tu:src/figlio.c; tu:src/wlroots.c |
| `service` | `servizio` | (name exists) | `svc` | file:installatore/interfaccia/tui/anteprima.go; file:installatore/interfaccia/tui/tui.go |
| `session` | `sessione` | (name exists) | `session_v` | go-package:installatore/motore; sh:banchi/06-b33-terreno.sh |
| `show` | `mostra` | (name exists) | **kept** | file:src/pagina.html |
| `sig` | `segnale` | (name exists) | **kept** | py:banchi/15-suite/15-f013-video.py; py:banchi/16-stress/16-salita.py |
| `size` | `dimensiona` | (name exists) | **kept** | py:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py; py:banchi/11-scatole/11-c23-maiusc-e-frecce-selezionano.py |
| `skewed` | `storte`, `storte_la` | `storte` | `storte_la`→`crooked` | py:banchi/11-scatole/11-registro-unisci.py |
| `snapshot` | `fotografa` | (name exists) | `capture_shot` | sh:banchi/17-distro/17-vm.sh |
| `sorted` | `ordinata` | (name exists) | `ordered` | py:banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py |
| `sorted` | `ordinate` | (name exists) | `ordered` | py:banchi/09-b81-linea-morta.py |
| `sorted` | `ordinati` | (name exists) | `ordered` | py:banchi/01-b3-cliente.py; py:banchi/07-b64-orecchio.py |
| `source` | `fonte`, `sorgente` | `fonte` | `sorgente`→`src_ref` | file:src/pagina.html |
| `src` | `sorg` | (name exists) | `source_dir` | sh:banchi/01-b0-bersaglio.sh; sh:banchi/01-b5-lancia.sh |
| `start` | `avvia` | (name exists) | `launch` | py:banchi/16-stress/16-attore-rdp.py; py:banchi/16-stress/16-salita.py |
| `start` | `avvia`, `inizio` | `inizio` | `avvia`→`launch` | py:banchi/16-stress/16-attore-rdp.py; py:banchi/16-stress/16-attore.py |
| `start` | `avvia`, `partenza` | `avvia` | `partenza`→`departure` | sh:banchi/01-s7-rotella.sh |
| `start` | `inizio` | (name exists) | `begin` | file:src/pagina.html |
| `start` | `inizio`, `partenza` | `inizio` | `partenza`→`departure` | py:banchi/11-scatole/11-c4-il-tasto-arriva-allo-schermo.py; py:banchi/19-android/19-android.py |
| `started` | `avviata`, `partito` | `partito` | `avviata`→**kept** | tu:src/sessione.c |
| `state` | `stato` | (name exists) | `cur_state` | file:installatore/motore/operazione.go; file:installatore/motore/testi.go |
| `step` | `passo` | (name exists) | `stage_step` | sh:banchi/17-distro/17-t3-pacchetto.sh; sh:banchi/17-distro/17-t3-rpm.sh |
| `step` | `passo`, `un_passo` | `passo` | `un_passo`→`a_step` | py:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py |
| `stop` | `ferma` | (name exists) | `halt` | py:banchi/15-suite/15-g8-comune.py; sh:banchi/17-distro/scatole/17-scatola.sh |
| `stop` | `ferma`, `fermati` | `ferma` | `fermati`→**kept** | py:banchi/11-scatole/11-c3-i-fotogrammi-cambiano.py; py:banchi/16-stress/16-attore-rdp.py |
| `stop` | `smetti` | (name exists) | `cease` | file:src/pagina.html |
| `stopped` | `fermato`, `fermo` | `fermo` | `fermato`→`halted` | file:src/pagina.html |
| `stopped` | `fermi`, `fermo` | `fermo` | `fermi`→`halted` | py:banchi/02-pam-fermo.py; py:banchi/15-suite/15-g4-comune.py |
| `stream` | `flusso` | (name exists) | `flow` | file:src/pagina.html; sh:banchi/18-scheda/18-confronto.sh |
| `streams` | `flussi` | (name exists) | `flows` | py:banchi/02-filo-validatore.py |
| `sum` | `som` | (name exists) | **kept** | py:banchi/16-stress/16-classifica.py |
| `sum` | `somma` | (name exists) | **kept** | py:banchi/07-b42-giudice.py; py:banchi/09-b77-audio-riordino.py |
| `supported` | `supportato` | (name exists) | `handled` | file:banchi/18-scheda/18-decodifica-chrome.html; file:banchi/18-software/18-software-webcodecs.html |
| `surface` | `superficie` | (name exists) | `surf` | tu:src/codificatore.c |
| `system` | `sistema` | (name exists) | **kept** | sh:banchi/19-nvidia/19-nv-macchina.sh |
| `table` | `tabella` | (name exists) | `tbl` | file:grafica/sito-mockup/performance.html |
| `tag` | `sigla` | (name exists) | `code_tag` | py:banchi/15-suite/15-f014-appunti.py |
| `taken` | `presi`, `preso` | `preso` | `presi`→`grabbed` | py:banchi/09-b81-linea-morta.py; tu:src/cattura.c |
| `target` | `bersaglio` | (name exists) | `goal` | file:src/pagina.html |
| `tell` | `dillo`, `dilo` | `dilo` | `dillo`→**kept** | c-program:banchi |
| `text` | `testo` | (name exists) | `body_text` | file:src/pagina.html; py:banchi/01-b2-ngtcp2-wt-innesta.py |
| `time` | `tempo` | (name exists) | **kept** | file:installatore/motore/ambiente.go; file:installatore/motore/gestore.go |
| `times` | `tempi`, `volte` | `tempi` | `volte`→`times_n` | py:banchi/16-stress/16-attore.py |
| `title` | `titolo` | (name exists) | `heading` | file:src/pagina.html; py:banchi/02-pagina-misura-cdp.py |
| `tolerated` | `tollerate`, `tollerati` | `tollerate` | `tollerati`→`allowed_n` | file:src/pagina.html |
| `tolerated` | `tollerati`, `tollerato` | `tollerato` | `tollerati`→`allowed_n` | py:banchi/02-filo-validatore.py |
| `touch` | `tocco` | (name exists) | **kept** | file:src/pagina.html |
| `transform` | `trasf` | (name exists) | `xform` | file:src/pagina.html |
| `trust` | `fiducia` | (name exists) | **kept** | file:installatore/cmd/remotix-install/main.go; file:installatore/motore/operazione.go |
| `undo` | `disfa` | (name exists) | `unmake` | file:installatore/motore/disinstalla.go; go-package:installatore/motore |
| `unit` | `unita` | (name exists) | `unit_v` | file:installatore/motore/azione_unita.go; go-package:installatore/motore |
| `unknown` | `ignote` | (name exists) | `unrecognized` | py:banchi/02-sessione-stato.py |
| `unknown` | `ignoti` | (name exists) | `unrecognized` | sh:banchi/11-scatole/11-accendi.sh |
| `update` | `aggiorna` | (name exists) | **kept** | py:banchi/16-stress/16-salita.py; sh:banchi/19-nvidia/19-nv-macchina.sh |
| `used` | `usate`, `usati` | `usati` | `usate`→**kept** | go-package:installatore/motore |
| `used` | `usati`, `usato` | `usato` | `usati`→**kept** | tu:src/figlio.c |
| `user` | `utente` | (name exists) | `username` | go-package:installatore/motore; sh:banchi/06-b33-terreno.sh |
| `users` | `utenti` | (name exists) | `usr_list` | sh:banchi/19-nvidia/19-nv-macchina.sh |
| `value` | `valore` | (name exists) | `value_v` | file:src/pagina.html |
| `vendor` | `forn` | (name exists) | `supplier` | sh:banchi/17-distro/17-amministratore.sh |
| `vendor` | `forn`, `fornitore` | `fornitore` | `forn`→`supplier` | file:installatore/motore/compatibilita.go; go-package:installatore/motore |
| `verb` | `verbo` | (name exists) | `action_verb` | sh:banchi/17-distro/scatole/17-scatola.sh |
| `verify` | `verifica` | (name exists) | `check_it` | go-package:installatore/motore |
| `version` | `versione` | (name exists) | `version_v` | file:installatore/interfaccia/vista.go; file:src/pagina.html |
| `video_open` | `video_aperto`, `video_apri` | `video_aperto` | `video_apri`→`video_open_it` | tu:banchi/rcp/rcp.c; tu:src/rcp.c |
| `visible` | `visibile` | (name exists) | **kept** | py:banchi/15-suite/15-n027-negative.py |
| `wait_for` | `attendi` | (name exists) | **kept** | py:banchi/01-b7-congedo.py |
| `wait_scene` | `aspetta_la_scena`, `attesa_scena` | `attesa_scena` | `aspetta_la_scena`→`await_scene` | py:banchi/11-scatole/11-c4-il-tasto-arriva-allo-schermo.py |
| `wait_stage` | `aspetta_il_palco`, `attesa_palco` | `attesa_palco` | `aspetta_il_palco`→`await_stage` | py:banchi/11-scatole/11-c8b-la-pagina-si-vede-dal-cliente.py |
| `waits_canvas` | `attese_tela`, `attese_tela--` | `attese_tela` | `attese_tela--`→`waitings_canvas` | file:src/pagina.html |
| `wanted` | `voluti`, `voluto` | `voluto` | `voluti`→`desired` | tu:src/vulkanvideo.c |
| `wheel` | `rotella` | (name exists) | `scroll_wheel` | file:src/pagina.html; py:banchi/16-stress/16-attore.py |
| `which` | `quale`, `quali` | `quale` | `quali`→`which_ones` | py:banchi/02-cattura-giudica.py; tu:src/figlio.c |
| `why` | `perche` | (name exists) | `reason_text` | file:installatore/motore/testi.go; go-package:installatore/motore |
| `width` | `larg`, `larghezza` | `larghezza` | `larg`→**kept** | py:banchi/02-sessione-stato.py |
| `width` | `larghezza` | (name exists) | `width_px` | file:src/pagina.html; tu:banchi/14-f1-forma.c |
| `window` | `finestra` | (name exists) | `win` | file:src/pagina.html; py:banchi/16-stress/16-classifica.py |
| `without_fix` | `senza_cura`, `senza_cura_` | `senza_cura` | `senza_cura_`→`no_fix` | py:banchi/11-scatole/11-c8b-la-pagina-si-vede-dal-cliente.py |
| `worst_ms` | `peggior_ms`, `peggiore_ms` | `peggior_ms` | `peggiore_ms`→`worst_v_ms` | tu:src/main.c |
| `write` | `scrivi` | (name exists) | `put_out` | file:banchi/01-b11-pagina.html; file:banchi/01-b2-sonda.html |
| `written` | `scritti`, `scritto` | `scritti` | `scritto`→`wrote` | tu:src/figlio.c |
| `wrong` | `sbagliata`, `sbagliate` | `sbagliata` | `sbagliate`→`incorrect` | file:banchi/01-b11-pagina.html |
| `wrong` | `sbagliata`, `storto` | `sbagliata` | `storto`→`crooked` | tu:banchi/01-b8-prova-ban.c |
| `wt_local_hook` | `wt_locale_gancio`, `wt_locali_gancio` | `wt_locale_gancio` | `wt_locali_gancio`→`wt_local_vars_hook` | c-program:src; tu:src/main.c |
| `yes` | `si` | (name exists) | **kept** | file:installatore/interfaccia/testi.go; file:src/pagina.html |
| `Current` | `Adesso`, `Ora` | `Ora` | `Adesso`→`NowV` | file:installatore/motore/finti_test.go; file:installatore/motore/operazione.go |
| `asked` | `chiesta`, `chiesti` | `chiesti` | `chiesta`→**kept** | file:src/pagina.html |
| `asked` | `chieste`, `chiesti` | `chiesti` | `chieste`→**kept** | tu:banchi/13-w1-un-fotogramma.c; tu:src/cattura.c |
| `awaited` | `attesi`, `atteso` | `atteso` | `attesi`→**kept** | py:banchi/01-b2-sonda-trasporto.py; py:banchi/07-b64-orecchio.py |
| `current` | `adesso`, `corrente` | `adesso` | `corrente`→**kept** | tu:src/appunti_kde.c |
| `fmt` | `formato` | (name exists) | **kept** | tu:banchi/02-cattura-prodotto.c; tu:banchi/06-b33-risveglio.c |
| `is_open` | `aperta`, `aperto` | `aperta` | `aperto`→**kept** | py:banchi/09-b81-linea-morta.py |
| `latest` | `ultima`, `ultimi` | `ultima` | `ultimi`→**kept** | py:banchi/11-scatole/11-c13-la-certificazione-e-recente.py |
| `lit` | `accesa`, `accese` | `accesa` | `accese`→`switched_on` | sh:banchi/17-distro/scatole/17-scatola.sh |
| `lit` | `accesa`, `acceso` | `acceso` | `accesa`→`switched_on` | py:banchi/09-b81-linea-morta.py; tu:src/codificatore.c |
| `lit` | `accese`, `acceso` | `acceso` | `accese`→`switched_on` | py:banchi/19-android/19-android.py |
| `located` | `trovata`, `trovato` | `trovato` | `trovata`→**kept** | go-package:installatore/motore; py:banchi/09-b77-audio-riordino.py |
| `muted` | `muta`, `muti` | `muti` | `muta`→**kept** | py:banchi/09-b70-ritmo.py |
| `ours` | `nostre`, `nostri` | `nostri` | `nostre`→**kept** | go-package:installatore/motore |
| `picture` | `foto`, `immagine` | `foto` | `immagine`→**kept** | py:banchi/15-suite/15-f013-video.py; py:banchi/15-suite/15-f018-riattacco-a-misura-diversa.py |
| `read_again` | `rileggi`, `rilette` | `rileggi` | `rilette`→**kept** | tu:src/sessione.c |
| `reboot` | `riavvia`, `riavvio` | `riavvio` | `riavvia`→**kept** | sh:banchi/17-distro/17-t10.sh |
| `row` | `linea`, `riga` | `riga` | `linea`→**kept** | py:banchi/09-b70-ritmo.py; py:banchi/17-t8/t8-browser.py |
| `set_up` | `installata`, `installati` | `installati` | `installata`→**kept** | file:installatore/motore/disinstalla_test.go; go-package:installatore/motore |
| `unsuccessful` | `fallita`, `fallito` | `fallita` | `fallito`→**kept** | file:installatore/interfaccia/tui/anteprima.go; file:installatore/motore/operazione.go |
| `unsuccessful` | `fallite`, `falliti` | `falliti` | `fallite`→**kept** | tu:banchi/13-w1-un-fotogramma.c; tu:src/cattura.c |
| `was_read` | `letta`, `letto` | `letto` | `letta`→**kept** | file:src/pagina.html; py:banchi/09-b79-cure.py |
| `switched_on` | `accesa`, `accese` | `accesa` | `accese`→**kept** | sh:banchi/17-distro/scatole/17-scatola.sh |
| `Distribution` | `Distribuzione` | (unresolved: twin distribuzione is not renamed) | **kept** | |
| `Trust` | `Fiducia` | (unresolved: twin fiducia is not renamed) | **kept** | |
| `Finished` | `Finita` | (unresolved: twin finita is not renamed) | **kept** | |
| `Image` | `Immagine` | (unresolved: twin immagine is not renamed) | **kept** | |
| `Job` | `Mestiere` | (unresolved: twin mestiere is not renamed) | **kept** | |
| `Minimum` | `Minima` | (unresolved: twin minima is not renamed) | **kept** | |
| `Point` | `Punto` | (unresolved: twin punto is not renamed) | **kept** | |
| `Remedy` | `Rimedio` | (unresolved: twin rimedio is not renamed) | **kept** | |
| `Sig` | `Segnale` | (unresolved: twin segnale is not renamed) | **kept** | |
| `Keyboard` | `Tastiera` | (unresolved: twin tastiera is not renamed) | **kept** | |

### Names not renamed (to resolve in interi.tsv or sinonimi.tsv)

- `Adesso` — untagged JSON field: its English is two words, the key cannot follow
- `Amb` — untagged JSON field: its English is two words, the key cannot follow
- `CASA` — target HOME is a well-known environment variable
- `Distribuzione` — twin distribuzione is not renamed
- `Fatti` — loses Done to Fatto (scopes: file:installatore/motore/profilo.go, go-package:installatore/motore)
- `Fiducia` — twin fiducia is not renamed
- `Finita` — twin finita is not renamed
- `Formato` — case twin formato is not renamed
- `Immagine` — twin immagine is not renamed
- `Mestiere` — twin mestiere is not renamed
- `Minima` — twin minima is not renamed
- `Motivo` — untagged JSON field: its English is two words, the key cannot follow
- `Nodo` — untagged JSON field: its English is two words, the key cannot follow
- `Origine` — untagged JSON field: its English is two words, the key cannot follow
- `Porta` — untagged JSON field: its English is two words, the key cannot follow
- `Punto` — twin punto is not renamed
- `Rimedio` — twin rimedio is not renamed
- `Segnale` — twin segnale is not renamed
- `Stato` — untagged JSON field: its English is two words, the key cannot follow
- `Tastiera` — twin tastiera is not renamed
- `Togli` — target Remove already exists in file:installatore/motore/certifica_test.go, file:installatore/motore/disinstalla.go, go-package:installatore/motore
- `accese` — loses switched_on to accesa (scopes: sh:banchi/17-distro/scatole/17-scatola.sh)
- `adesso` — untagged JSON field Adesso: its English is two words
- `aggiorna` — target update already exists in py:banchi/16-stress/16-salita.py, sh:banchi/19-nvidia/19-nv-macchina.sh
- `altra` — target other already exists in file:installatore/interfaccia/vista.go, go-package:installatore/interfaccia
- `altre` — loses other to altro (scopes: go-package:installatore/interfaccia)
- `amb` — untagged JSON field Amb: its English is two words
- `aperto` — loses is_open to aperta (scopes: py:banchi/09-b81-linea-morta.py)
- `argomenti` — target args already exists in go-package:installatore/motore, py:banchi/11-scatole/11-c2-una-finestra-si-apre.py, py:banchi/17-t7/t7-aggiorna.py
- `att` — loses expected to atteso (scopes: py:banchi/01-b5-violazioni.py, py:banchi/01-b6-tetti.py, py:banchi/02-filo-cliente.py)
- `attendi` — target wait_for already exists in py:banchi/01-b7-congedo.py
- `attesi` — loses awaited to atteso (scopes: py:banchi/01-b2-sonda-trasporto.py, py:banchi/07-b64-orecchio.py, py:banchi/09-b77-audio-riordino.py)
- `attive` — loses active to attiva (scopes: go-package:installatore/motore)
- `avviata` — loses started to partito (scopes: tu:src/sessione.c)
- `bannate` — loses banned to bannato (scopes: py:banchi/01-b8-cronometro.py)
- `bannati` — loses banned to bannato (scopes: py:banchi/01-b8-cronometro.py)
- `bottone` — target button already exists in file:banchi/01-s7-pagina.html, py:banchi/15-suite/15-g1b-comune.py
- `buona` — loses good to buono (scopes: py:banchi/01-b8-cronometro.py)
- `buoni` — loses good to buono (scopes: py:banchi/01-b8-cronometro.py)
- `cammino` — loses path to percorso (scopes: go-package:installatore/motore)
- `candidata` — target candidate already exists in c-program:src, tu:src/ritrovo.c
- `candidato` — target candidate already exists in c-program:src
- `chiesta` — loses asked to chiesti (scopes: file:src/pagina.html)
- `chieste` — loses asked to chiesti (scopes: tu:banchi/13-w1-un-fotogramma.c, tu:src/cattura.c, tu:src/figlio.c)
- `chiusa` — target closed already exists in file:src/pagina.html
- `chiusura` — target closing already exists in py:banchi/01-b7-congedo.py
- `comanda` — loses command to comando (scopes: file:src/pagina.html, py:banchi/15-suite/15-f004-il-mouse.py, py:banchi/15-suite/15-f014-appunti.py)
- `completi` — loses complete to completo (scopes: file:src/pagina.html)
- `copia` — target copy already exists in py:banchi/16-stress/16-risorse.py
- `corrente` — loses current to adesso (scopes: tu:src/appunti_kde.c)
- `dal` — target from is a Python keyword or builtin
- `destra` — target right already exists in file:grafica/sito-mockup/index.html, file:grafica/sito-mockup/performance.html, file:src/pagina.html
- `dichiarato` — loses declared to dichiarata (scopes: data:all, file:installatore/motore/testi.go, go-package:installatore/motore)
- `dillo` — loses tell to dilo (scopes: c-program:banchi)
- `dimensiona` — target size already exists in py:banchi/11-scatole/11-c21-sul-bordo-la-forma-cambia.py, py:banchi/11-scatole/11-c23-maiusc-e-frecce-selezionano.py, py:banchi/15-suite/15-f003-lo-schermo-si-aggiorna.py
- `dipinta` — loses painted to dipinti (scopes: file:src/pagina.html)
- `dipinto` — loses painted to dipinti (scopes: file:src/pagina.html)
- `distribuzione` — target distribution already exists in sh:banchi/19-nvidia/19-nv-macchina.sh
- `elenca` — loses list to elenco (scopes: tu:src/sessione.c)
- `esiste` — target exists already exists in py:banchi/16-stress/16-lavori.py
- `esiti_` — loses outcomes to esiti (scopes: py:banchi/11-scatole/11-c8b-la-pagina-si-vede-dal-cliente.py)
- `espressione` — target expression already exists in py:banchi/02-pagina-misura-cdp.py
- `etich` — loses label to etichetta (scopes: file:grafica/sito-mockup/performance.html)
- `fallite` — loses unsuccessful to falliti (scopes: tu:banchi/13-w1-un-fotogramma.c, tu:src/cattura.c, tu:src/figlio.c)
- `fallito` — loses unsuccessful to fallita (scopes: file:installatore/interfaccia/tui/anteprima.go, file:installatore/motore/operazione.go, go-package:installatore/interfaccia/tui)
- `fatta` — loses done to fatti (scopes: go-package:installatore/motore)
- `fatti` — target done already exists in sh:banchi/02-codifica-lancia.sh
- `fermati` — loses stop to ferma (scopes: py:banchi/11-scatole/11-c3-i-fotogrammi-cambiano.py, py:banchi/16-stress/16-attore-rdp.py)
- `fiducia` — target trust already exists in file:installatore/cmd/remotix-install/main.go, file:installatore/motore/operazione.go, file:installatore/motore/testi.go
- `finita` — loses finished to fatto (scopes: file:banchi/01-b11-pagina.html, py:banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py)
- `formato` — target fmt already exists in tu:banchi/02-cattura-prodotto.c, tu:banchi/06-b33-risveglio.c, tu:banchi/06-b5-esiti-cattura.c
- `fotografia` — loses photo to foto (scopes: py:banchi/17-t7/t7-aggiorna.py)
- `genere` — loses kind to tipo (scopes: tu:src/webtransport.c)
- `immagine` — loses picture to foto (scopes: py:banchi/15-suite/15-f013-video.py, py:banchi/15-suite/15-f018-riattacco-a-misura-diversa.py, py:banchi/15-suite/15-f018b-finestre-dentro-al-riattacco.py)
- `installata` — loses set_up to installati (scopes: file:installatore/motore/disinstalla_test.go, go-package:installatore/motore)
- `larg` — loses width to larghezza (scopes: py:banchi/02-sessione-stato.py)
- `letta` — loses was_read to letto (scopes: file:src/pagina.html, py:banchi/09-b79-cure.py)
- `libera` — target free already exists in tu:src/figlio.c, tu:src/vulkanvideo.c
- `liberi` — loses free to libero (scopes: tu:src/figlio.c)
- `libero` — target free already exists in tu:banchi/rcp/rcp.c, tu:src/figlio.c, tu:src/main.c
- `linea` — loses row to riga (scopes: py:banchi/09-b70-ritmo.py, py:banchi/17-t8/t8-browser.py, tu:banchi/06-b33-risveglio.c)
- `lista` — loses list to elenco (scopes: tu:src/vulkanvideo.c)
- `mancante` — loses missing to manca (scopes: py:banchi/01-b7-congedo.py)
- `mancanti` — loses missing to manca (scopes: go-package:installatore/motore)
- `mancati--` — loses missed to mancati (scopes: file:src/pagina.html)
- `memoria` — target memory already exists in tu:banchi/02-cattura-fotogramma.c, tu:banchi/02-cattura-prodotto.c, tu:src/vulkanvideo.c
- `mestiere` — target job already exists in file:installatore/motore/testi.go, go-package:installatore/motore
- `minima` — loses minimum to minimo (scopes: go-package:installatore/motore)
- `mostra` — target show already exists in file:src/pagina.html
- `mot` — target reason already exists in file:banchi/01-b11-pagina.html, file:src/pagina.html
- `motivo` — untagged JSON field Motivo: its English is two words
- `muovi` — target move already exists in py:banchi/12-client-veri.py
- `muta` — loses muted to muti (scopes: py:banchi/09-b70-ritmo.py)
- `nella` — target in is a Python keyword or builtin
- `nodo` — untagged JSON field Nodo: its English is two words
- `nostre` — loses ours to nostri (scopes: go-package:installatore/motore)
- `numero` — target number already exists in py:docs/sources/build.py, py:docs/sources/technical/ch01_introduction.py, py:docs/sources/technical/ch02_architecture.py
- `nuove` — loses fresh to nuovo (scopes: go-package:installatore/motore)
- `nuovi` — loses fresh to nuove (scopes: py:banchi/12-client-veri.py, py:banchi/16-stress/16-riclassifica.py)
- `origine` — untagged JSON field Origine: its English is two words
- `pacchetto` — target package already exists in go-package:installatore/motore
- `persa` — loses lost to persi (scopes: py:banchi/09-b76-rete-cattiva.py)
- `perso` — loses lost to persi (scopes: py:banchi/09-b76-rete-cattiva.py)
- `porta` — untagged JSON field Porta: its English is two words
- `portatile` — target laptop already exists in file:grafica/sito-mockup/index.html
- `previsti` — loses expected to atteso (scopes: py:banchi/11-scatole/11-c24-l-esci-chiude-sempre.py)
- `princ` — loses primary to principale (scopes: file:installatore/motore/azione_gruppo.go, go-package:installatore/motore)
- `pulsanti` — loses buttons to bottoni (scopes: tu:src/input.c)
- `punto` — target point already exists in py:banchi/16-stress/16-lavori.py
- `riavvia` — loses reboot to riavvio (scopes: sh:banchi/17-distro/17-t10.sh)
- `ricevuto` — loses received to ricevuti (scopes: py:banchi/01-b3-cliente.py, py:banchi/16-stress/16-attore.py)
- `rilette` — loses read_again to rileggi (scopes: tu:src/sessione.c)
- `rimedio` — target remedy already exists in file:installatore/motore/testi.go, go-package:installatore/motore, py:docs/sources/technical/ch15_installer.py
- `ritaglia` — target crop already exists in py:banchi/15-suite/15-g4-comune.py
- `segnale` — target sig already exists in py:banchi/15-suite/15-f013-video.py, py:banchi/16-stress/16-salita.py
- `sezioni` — target sections already exists in py:docs/sources/build.py, py:docs/sources/technical/ch01_introduction.py, py:docs/sources/technical/ch02_architecture.py
- `si` — target yes already exists in file:installatore/interfaccia/testi.go, file:src/pagina.html, go-package:installatore/interfaccia
- `sinistra` — target left already exists in file:src/pagina.html
- `sistema` — target system already exists in sh:banchi/19-nvidia/19-nv-macchina.sh
- `som` — target sum already exists in py:banchi/16-stress/16-classifica.py
- `somma` — target sum already exists in py:banchi/07-b42-giudice.py, py:banchi/09-b77-audio-riordino.py, py:banchi/11-scatole/11-c5-il-suono-non-e-silenzio.py
- `sospeso` — loses pending to sospesi (scopes: file:src/pagina.html)
- `stato` — untagged JSON field Stato: its English is two words
- `tastiera` — target keyboard already exists in file:src/pagina.html
- `tempo` — target time already exists in file:installatore/motore/ambiente.go, file:installatore/motore/gestore.go, go-package:installatore/motore
- `tocco` — target touch already exists in file:src/pagina.html
- `trovata` — loses located to trovato (scopes: go-package:installatore/motore, py:banchi/09-b77-audio-riordino.py)
- `tutte` — target all already exists in py:banchi/01-b8-cronometro.py, py:banchi/16-stress/16-classifica.py, py:banchi/19-android/19-android.py
- `uguale` — loses equal to uguali (scopes: tu:src/sessione.c)
- `ultimi` — loses latest to ultima (scopes: py:banchi/11-scatole/11-c13-la-certificazione-e-recente.py)
- `usate` — loses used to usati (scopes: go-package:installatore/motore)
- `usati` — loses used to usato (scopes: tu:src/figlio.c)
- `vecchie` — loses old to vecchio (scopes: tu:src/sessione.c)
- `verdi` — loses green to verde (scopes: py:banchi/04-b28-gesti.py)
- `veri` — target true is a Go keyword or predeclared name
- `visibile` — target visible already exists in py:banchi/15-suite/15-n027-negative.py

### Names left out on purpose

- `NID_subject_alt_name` — defined outside the project (C headers)
- `OPUS_SET_PACKET_LOSS_PERC` — defined outside the project (C headers)
- `catalogo` — a Go package name: renamed with its directory (step 2)
- `interfaccia` — a Go package name: renamed with its directory (step 2)
- `locale_t` — defined outside the project (C headers)
- `motore` — a Go package name: renamed with its directory (step 2)

### Cross-language contracts (every place: rinomina2-plan.json → contracts)

| kind | names |
|---|---|
| crosses languages | 2204 |
| data name | 75 |
| environment variable | 83 |
| option / subcommand / kebab name | 293 |

The names below are the ones another program reads by spelling: data names, environment variables, options and kebab names.  The 2204 code names that merely occur in two languages are in the JSON only.

| old | new | kind | languages | places |
|---|---|---|---|---|
| `ACCETTATA` | `ACCEPTED` | data name (dati.tsv: log-text) | c,py | 5 |
| `APPUNTI_ANNUNCIO` | `CLIPBOARD_ANNOUNCE` | data name (dati.tsv: log-text) | c,html,py | 24 |
| `APPUNTI_CHIEDI` | `CLIPBOARD_ASK` | data name (dati.tsv: log-text) | c,html,py | 36 |
| `APPUNTI_TESTO` | `CLIPBOARD_TEXT` | data name (dati.tsv: log-text) | c,html,py | 37 |
| `BANCO_MARCA` | `BENCH_MARK` | data name (dati.tsv: log-text) | c,py | 34 |
| `BOTTONE` | `BUTTON` | data name (dati.tsv: json-value) | c,py | 3 |
| `BUCHI` | `HOLES` | data name (dati.tsv: log-marker) | html,py | 8 |
| `BUDGET_PIENO` | `BUDGET_FULL` | data name (dati.tsv: reason) | c,html,py | 20 |
| `COMPOSITORE_INCAPACE` | `COMPOSITOR_UNABLE` | data name (dati.tsv: log-text) | c,html,py | 36 |
| `CONFORME` | `COMPLIANT` | data name (dati.tsv: json-value) | html,sh | 5 |
| `DISPOSIZIONE` | `LAYOUT` | data name (dati.tsv: log-text) | c,py | 37 |
| `F18ESITO` | `F18OUTCOME` | data name (dati.tsv: log-marker) | html,py | 4 |
| `FUNZIONE_SPENTA` | `FUNCTION_OFF` | data name (dati.tsv: log-text) | c,py | 9 |
| `GIA_ATTIVA_LOCALE` | `ALREADY_ACTIVE_LOCAL` | data name (dati.tsv: reason) | c,html,py | 16 |
| `INATTIVITA` | `INACTIVITY` | data name (dati.tsv: reason) | c,html,py | 10 |
| `MISURA_FUORI_LIMITI` | `SIZE_OUT_OF_LIMITS` | data name (dati.tsv: log-text) | c,html,py | 29 |
| `NON-BANNATO` | `NOT-BANNED` | data name (dati.tsv: wire-string) | c,py,sh | 37 |
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
| `REMOTIX_INQUILINO` | `REMOTIX_TENANT` | environment variable | c,conf,py | 14 |
| `REMOTIX_MISURE_15` | `REMOTIX_MEASURES_15` | environment variable | py | 2 |
| `REMOTIX_MISURE_16` | `REMOTIX_MEASURES_16` | environment variable | py | 1 |
| `REMOTIX_MISURE_ANDROID` | `REMOTIX_MEASURES_ANDROID` | environment variable | py | 1 |
| `REMOTIX_NOME` | `REMOTIX_NAME` | environment variable | conf,py | 7 |
| `REMOTIX_OPZIONI` | `REMOTIX_OPTIONS` | environment variable | conf,py,sh | 25 |
| `REMOTIX_PAGINA_H` | `REMOTIX_PAGE_H` | environment variable | c | 2 |
| `REMOTIX_PAROLA` | `REMOTIX_WORD` | environment variable | py | 6 |
| `REMOTIX_PAROLA_PROVA` | `REMOTIX_TEST_WORD` | environment variable | sh | 12 |
| `REMOTIX_PAROLA_SUDO` | `REMOTIX_SUDO_WORD` | environment variable | py,sh | 20 |
| `REMOTIX_PASSAGGIO16` | `REMOTIX_PASS16` | environment variable | py | 1 |
| `REMOTIX_PORTA` | `REMOTIX_PORT` | environment variable | conf,go,py,sh | 24 |
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
| `REMOTIX_SGOMBRA_SOGLIA_MS` | `REMOTIX_CLEAR_OUT_THRESHOLD_MS` | environment variable | c,py | 3 |
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
| `RX_ISO_SOLO_PREPARA` | `RX_ISO_ONLY_PREPARE` | environment variable | sh | 2 |
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
| `TOLTO` | `REMOVED` | data name (dati.tsv: wire-string) | c,py,sh | 31 |
| `__AVVISO__` | `__WARNING__` | data name (dati.tsv: kv-key) | c,html | 4 |
| `__IMPRONTA__` | `__FINGERPRINT__` | data name (dati.tsv: kv-key) | c,html | 5 |
| `abbandono-s` | `abandonment-s` | option / subcommand / kebab name | c,py,sh | 15 |
| `accento-scuro` | `accent-dark` | option / subcommand / kebab name | css,html | 4 |
| `accesso-entra` | `access-enter` | option / subcommand / kebab name | html | 2 |
| `accesso-gira` | `access-runs` | option / subcommand / kebab name | html | 2 |
| `accesso-respira` | `access-breathes` | option / subcommand / kebab name | html | 2 |
| `accesso-scuote` | `access-shakes` | option / subcommand / kebab name | html | 2 |
| `algoritmo` | `algorithm` | data name (dati.tsv: json-key) | c | 1 |
| `altro_scatola` | `other_box` | data name (dati.tsv: json-value) | py | 10 |
| `ammazza-aiutante` | `kill-helper` | option / subcommand / kebab name | sh | 4 |
| `anche-lo-sporco` | `dirty-too` | option / subcommand / kebab name | py | 6 |
| `anche-se-non-vuoto` | `even-if-not-empty` | option / subcommand / kebab name | py | 2 |
| `anche-se-qualcuno-e-dentro` | `even-if-someone-is-inside` | option / subcommand / kebab name | py | 1 |
| `anticipo-foto-s` | `photo-lead-s` | option / subcommand / kebab name | py | 2 |
| `applicazione-che-muore` | `application-that-dies` | option / subcommand / kebab name | py,sh | 8 |
| `appunti-attendi` | `clipboard-wait` | option / subcommand / kebab name | py | 2 |
| `appunti-copia` | `clipboard-copy` | option / subcommand / kebab name | py | 2 |
| `appunti-scrivi` | `clipboard-write` | option / subcommand / kebab name | py | 3 |
| `argomenti-ciechi` | `arguments-blind` | option / subcommand / kebab name | py | 1 |
| `aria-current` | `air-current` | option / subcommand / kebab name | html | 2 |
| `aria-pressed` | `air-pressed` | option / subcommand / kebab name | html | 7 |
| `ascolto-s` | `listen-s` | option / subcommand / kebab name | py | 3 |
| `assesta-s` | `settles-s` | option / subcommand / kebab name | py | 1 |
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
| `attesa-uscita` | `wait-output` | option / subcommand / kebab name | py | 2 |
| `attesa-uscita-s` | `wait-output-s` | option / subcommand / kebab name | py | 1 |
| `attesa-verdetto` | `waiting-verdict` | data name (dati.tsv: log-text) | c,html,py | 21 |
| `attese_tela--` | `waitings_canvas` | option / subcommand / kebab name |  | 0 |
| `audio-decodifica-ms` | `audio-decoding-ms` | option / subcommand / kebab name | py | 2 |
| `audio-passo-us` | `audio-step-us` | option / subcommand / kebab name | py | 2 |
| `audio-prova` | `audio-test` | option / subcommand / kebab name | c,conf,py,sh | 20 |
| `audio-regola` | `audio-rule` | option / subcommand / kebab name | py | 20 |
| `audio-scrivi` | `audio-write` | option / subcommand / kebab name | py | 9 |
| `avviso-muro` | `warning-muro` | option / subcommand / kebab name | html | 3 |
| `banco-nel-binario` | `bench-in-binary` | data name (dati.tsv: kv-key) | sh | 1 |
| `banco-w1` | `bench-w1` | option / subcommand / kebab name | conf,make,py | 4 |
| `bordo-blu` | `edge-blue` | option / subcommand / kebab name | html | 3 |
| `bozze-attese` | `expected-drafts` | option / subcommand / kebab name | py | 3 |
| `browser-griglia` | `browser-grid` | option / subcommand / kebab name | html | 4 |
| `browser-sez` | `browser-sect` | option / subcommand / kebab name | html | 1 |
| `byte_persi` | `byte_lost` | data name (dati.tsv: log-marker) | c,py | 7 |
| `byte_persi_d` | `byte_lost_d` | data name (dati.tsv: log-marker) | c,py | 4 |
| `byte_spediti` | `byte_shipped` | data name (dati.tsv: log-marker) | c,py | 8 |
| `caduta-s` | `drop-s` | option / subcommand / kebab name | py | 1 |
| `campo-bordo` | `field-edge` | option / subcommand / kebab name | css,html | 5 |
| `campo-bordo-su` | `field-edge-on` | option / subcommand / kebab name | css,html | 5 |
| `chiaro-fondo` | `clear-background` | option / subcommand / kebab name | css,html | 13 |
| `chiave-a` | `key-a` | option / subcommand / kebab name | c,sh | 6 |
| `chiave-dopo` | `key-after` | option / subcommand / kebab name | py | 2 |
| `chiavi-attese` | `expected-keys` | option / subcommand / kebab name | py,sh | 3 |
| `chiavi-ogni` | `keys-every` | option / subcommand / kebab name | c | 3 |
| `clic-dopo` | `click-after` | option / subcommand / kebab name | py | 3 |
| `clic-ogni` | `click-every` | option / subcommand / kebab name | py | 2 |
| `cliente-di-prova` | `test-client` | data name (dati.tsv: capability-value) | py | 4 |
| `coda-scatto` | `queue-shot` | option / subcommand / kebab name | py | 1 |
| `coda_rete_us` | `network_queue_us` | data name (dati.tsv: log-marker) | c,py | 3 |
| `codice-evdev` | `code-evdev` | option / subcommand / kebab name | py | 1 |
| `codificatore-fermo` | `stopped-encoder` | option / subcommand / kebab name | py,sh | 13 |
| `comando-socket` | `command-socket` | option / subcommand / kebab name | c,conf,py,sh | 48 |
| `come-al-riavvio` | `as-after-reboot` | option / subcommand / kebab name | sh | 4 |
| `conferma-no` | `confirm-no` | option / subcommand / kebab name | html | 3 |
| `conferma-si` | `ack` | option / subcommand / kebab name | html | 2 |
| `conferma-testo` | `confirm-text` | option / subcommand / kebab name | html | 2 |
| `continuita-s` | `continuity-s` | option / subcommand / kebab name | py | 2 |
| `controllo-min` | `check-min` | option / subcommand / kebab name | py | 5 |
| `controllo-rosso` | `check-red` | option / subcommand / kebab name | py | 1 |
| `controllo-testimone` | `check-witness` | option / subcommand / kebab name | py | 3 |
| `coppie-esaminate` | `pairs-examined` | option / subcommand / kebab name | py | 2 |
| `costruisci-tutte` | `build-all` | option / subcommand / kebab name | sh | 2 |
| `cpu-tutti` | `all-cpus` | option / subcommand / kebab name | py | 1 |
| `credito-atteso` | `expected-credit` | option / subcommand / kebab name | py | 2 |
| `da-scena` | `from-scene` | option / subcommand / kebab name | py | 3 |
| `dal-bus` | `from-bus` | option / subcommand / kebab name | py,sh | 7 |
| `data-agganciato` | `data-hooked` | option / subcommand / kebab name | html | 3 |
| `data-bannato` | `data-banned` | data name (dati.tsv: wire-string) | c,html,py,sh | 24 |
| `data-disposizione` | `data-layout` | option / subcommand / kebab name | html,py | 14 |
| `data-puntatore` | `data-pointer` | option / subcommand / kebab name | html | 3 |
| `data-restano-ms` | `data-remaining-ms` | data name (dati.tsv: wire-string) | c,html,py,sh | 12 |
| `data-schermo` | `data-screen` | option / subcommand / kebab name | html,py | 23 |
| `deb-firma` | `deb-sign` | option / subcommand / kebab name | sh | 2 |
| `desincronizzata` | `desynchronized` | data name (dati.tsv: wire-string) | c,html,py | 11 |
| `desktop-nuovo` | `new-desktop` | option / subcommand / kebab name | py,sh | 13 |
| `dgram_falsi_d` | `dgram_false_d` | data name (dati.tsv: log-marker) | c,py | 6 |
| `dgram_persi_d` | `dgram_lost_d` | data name (dati.tsv: log-marker) | c,py | 4 |
| `dipinto-dopo-reset` | `painted-after-reset` | option / subcommand / kebab name | py | 1 |
| `distro-riga` | `distro-line` | option / subcommand / kebab name | html | 4 |
| `dopo-scena` | `afterwards-scene` | option / subcommand / kebab name | c,sh | 8 |
| `due-col` | `two-with` | option / subcommand / kebab name | html | 3 |
| `f-disp` | `f-avail` | option / subcommand / kebab name | html | 3 |
| `figlio-interno` | `internal-child` | option / subcommand / kebab name | c,py,sh | 29 |
| `file-del-banco` | `bench-files` | data name (dati.tsv: kv-key) | sh | 2 |
| `fin-ricevuto` | `fin-received` | option / subcommand / kebab name | py | 1 |
| `finestra-che-non-si-apre` | `window-that-does-not-open` | option / subcommand / kebab name | py,sh | 9 |
| `finestra-guasto` | `window-fault` | option / subcommand / kebab name | py | 3 |
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
| `grafico-cpu` | `graphical-cpu` | option / subcommand / kebab name | html | 2 |
| `grafico-video` | `graphical-video` | option / subcommand / kebab name | html | 2 |
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
| `journal-scatola` | `journal-box` | option / subcommand / kebab name | py | 8 |
| `labwc_cliente` | `labwc_client` | data name (dati.tsv: json-value) | py | 9 |
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
| `minimo-dopo-scena` | `minimum-after-scene` | option / subcommand / kebab name | c,sh | 6 |
| `minimo_pacchetti` | `min_packets` | data name (dati.tsv: log-marker) | c,py | 3 |
| `minimo_prove` | `min_tests` | data name (dati.tsv: log-marker) | c,py | 4 |
| `minuti-ultimo` | `minutes-last` | option / subcommand / kebab name | py | 4 |
| `motore-annulla` | `engine-rollback` | option / subcommand / kebab name | sh | 3 |
| `motore-cmd` | `engine-cmd` | option / subcommand / kebab name | sh | 2 |
| `motore-monta` | `engine-mount` | option / subcommand / kebab name | sh | 2 |
| `motore-smonta` | `engine-unmount` | option / subcommand / kebab name | sh | 2 |
| `muore-dopo` | `dies-after` | option / subcommand / kebab name | py | 3 |
| `niente-audio-silenzio` | `no-audio-silence` | option / subcommand / kebab name | c,py | 42 |
| `niente-linea-morta` | `no-dead-line` | option / subcommand / kebab name | c,py | 17 |
| `niente-ritmo-adattivo` | `no-adaptive-rate` | option / subcommand / kebab name | c,py,sh | 25 |
| `nome-figlio` | `child-name` | option / subcommand / kebab name | py | 1 |
| `non-collegare` | `not-connect` | option / subcommand / kebab name | py | 1 |
| `non-rifare` | `not-redo` | option / subcommand / kebab name | py | 2 |
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
| `parola-cattiva` | `bad-word` | option / subcommand / kebab name | py | 1 |
| `parola-file` | `word-file` | option / subcommand / kebab name | py,sh | 54 |
| `parola-sudo` | `word-sudo` | option / subcommand / kebab name | py | 1 |
| `passo-cpu` | `step-cpu` | option / subcommand / kebab name | py | 2 |
| `passo-s` | `step-s` | option / subcommand / kebab name | py | 1 |
| `passo-scena` | `step-scene` | option / subcommand / kebab name | py | 1 |
| `pausa-staccato` | `detached-pause` | option / subcommand / kebab name | py | 1 |
| `pausa-tasto` | `pause-key` | option / subcommand / kebab name | py | 1 |
| `per-caso` | `per-case` | option / subcommand / kebab name | py,sh | 3 |
| `piede-chiaro` | `foot-clear` | option / subcommand / kebab name | html | 16 |
| `porte-base` | `base-ports` | option / subcommand / kebab name | py,sh | 35 |
| `posa-scena` | `places-scene` | option / subcommand / kebab name | py | 2 |
| `pretendi-chi` | `require-who` | option / subcommand / kebab name | c,py | 10 |
| `pretendi-pid` | `require-pid` | option / subcommand / kebab name | c,py | 4 |
| `primo-s` | `first-s` | option / subcommand / kebab name | py | 1 |
| `prova-codifica` | `encoding-test` | option / subcommand / kebab name | c,go,py,sh | 48 |
| `pss-ogni` | `pss-every` | option / subcommand / kebab name | py | 3 |
| `puntatore-di-ripiego` | `pointer-of-fallback` | option / subcommand / kebab name | html,py | 2 |
| `puntatore-vecchia` | `old-pointer` | option / subcommand / kebab name | py | 3 |
| `punti-v` | `points-v` | option / subcommand / kebab name | html | 7 |
| `purezza-minima` | `minimum-purity` | option / subcommand / kebab name | py | 1 |
| `qualita-a` | `quality-a` | option / subcommand / kebab name | c,sh | 4 |
| `qualita-risale` | `quality-rises` | option / subcommand / kebab name | c,py | 16 |
| `registro-byte` | `log-bytes` | option / subcommand / kebab name | sh | 1 |
| `registro-cmd` | `log-cmd` | option / subcommand / kebab name | py | 6 |
| `respiro-innesco` | `respite-trigger` | option / subcommand / kebab name | py | 2 |
| `resta-dopo` | `stays-after` | option / subcommand / kebab name | py | 2 |
| `resta-nascita` | `stays-birth` | option / subcommand / kebab name | py | 1 |
| `resta-prima` | `stays-before` | option / subcommand / kebab name | py | 4 |
| `rete-intera` | `whole-network` | option / subcommand / kebab name | py,sh | 9 |
| `rete-quic` | `network-quic` | data name (dati.tsv: log-marker) | c,py | 62 |
| `ricevuti_d` | `received_d` | data name (dati.tsv: log-marker) | c,py | 4 |
| `ridimensiona-a` | `rescale-a` | option / subcommand / kebab name | c,sh | 6 |
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
| `segnale-scena` | `signal-scene` | option / subcommand / kebab name | c,sh | 8 |
| `segni-browser` | `signs-browser` | option / subcommand / kebab name | py | 3 |
| `seme-base` | `base-seed` | option / subcommand / kebab name | py | 3 |
| `senza-clic` | `without-click` | option / subcommand / kebab name | py | 1 |
| `senza-controllo` | `without-check` | option / subcommand / kebab name | py | 1 |
| `senza-copia` | `without-copy` | option / subcommand / kebab name | py,sh | 11 |
| `senza-coppia` | `without-pair` | option / subcommand / kebab name | py | 1 |
| `senza-cura` | `without-fix` | option / subcommand / kebab name | py,sh | 24 |
| `senza-eco` | `without-echo` | option / subcommand / kebab name | py | 7 |
| `senza-guasto` | `without-fault` | option / subcommand / kebab name | py | 6 |
| `senza-maiusc` | `without-shift` | option / subcommand / kebab name | py,sh | 7 |
| `senza-pulsante` | `without-button` | option / subcommand / kebab name | py,sh | 10 |
| `senza-riscaldamento` | `without-warmup` | option / subcommand / kebab name | py | 1 |
| `senza-scheda` | `without-card` | option / subcommand / kebab name | py | 3 |
| `senza-sessione` | `without-session` | option / subcommand / kebab name | py,sh | 9 |
| `senza-sorgente` | `without-source` | option / subcommand / kebab name | py,sh | 11 |
| `senza-sveglia` | `without-wake` | option / subcommand / kebab name | py | 2 |
| `senza-tasto` | `without-key` | option / subcommand / kebab name | py,sh | 10 |
| `senza-tela-minima` | `without-canvas-minimum` | option / subcommand / kebab name | py | 1 |
| `senza-usermod` | `without-usermod` | option / subcommand / kebab name | py,sh | 11 |
| `sessione-via` | `session-away` | option / subcommand / kebab name | sh | 3 |
| `sfratto-ms` | `eviction-ms` | option / subcommand / kebab name | c,py,sh | 27 |
| `sgombra-soglia-ms` | `clear-out-threshold-ms` | option / subcommand / kebab name | c,py,sh | 38 |
| `soglia-coppia` | `pair-threshold` | option / subcommand / kebab name | py | 2 |
| `soglia-cpu` | `cpu-threshold` | option / subcommand / kebab name | py | 2 |
| `soglia_silenzio_ms` | `silence_threshold_ms` | data name (dati.tsv: log-marker) | c,py | 4 |
| `solo-controllo-positivo` | `only-check-positive` | option / subcommand / kebab name | py,sh | 4 |
| `solo-distacco` | `only-detachment` | option / subcommand / kebab name | py,sh | 8 |
| `solo-esito` | `only-outcome` | option / subcommand / kebab name | py | 1 |
| `solo-porte` | `only-ports` | option / subcommand / kebab name | py | 2 |
| `solo-qui` | `only-here` | option / subcommand / kebab name | sh | 4 |
| `solo-strato-tecnico` | `technical-layer-only` | option / subcommand / kebab name | py | 1 |
| `sonda-b2` | `probe-b2` | data name (dati.tsv: capability-value) | html | 1 |
| `sorgente-out` | `source-out` | option / subcommand / kebab name | c,sh | 5 |
| `ssh-parola` | `ssh-word` | option / subcommand / kebab name | sh | 4 |
| `staccata-per-silenzio` | `detached-for-silence` | data name (dati.tsv: log-text) | c,py | 10 |
| `stato-iniziale` | `initial-state` | option / subcommand / kebab name | py,sh | 5 |
| `strato-tecnico` | `technical-layer` | option / subcommand / kebab name | py,sh | 5 |
| `tabella-capacita` | `table-capabilities` | option / subcommand / kebab name | html | 2 |
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
| `verificato` | `verified` | data name (dati.tsv: json-value) | py | 1 |
| `vetro-blu` | `glass-blue` | option / subcommand / kebab name | html | 4 |
| `video-profondita` | `video-depth` | option / subcommand / kebab name | py | 1 |
| `video-scrivi` | `video-write` | option / subcommand / kebab name | py | 11 |
| `video_avanza` | `video_advances` | data name (dati.tsv: json-value) | py | 8 |

### Coverage of the contract analysis (contratti/*.tsv)

**dati-contratto.tsv** — kept (unresolved collision): 22, left out on purpose (step 2): 2, no Italian word: 92, not renamed (path, product name, or not found by the analysis): 49, renamed by dati.tsv: 48, renamed by the table: 341

Not renamed: `#puntatore-di-ripiego` `#tastiera-comando` `al_secondo` `ammissione_s` `bit_per_canale_chi_lo_dice` `blocco_max_ms` `bottone` `buchi_istante` `byte_flusso` `categorie` `chi_lo_dice` `cinture` `commit_cura` `consegna_a_F2_3` `cpu_macchina_pct` `distinti_riciclati` `durata_lavoro_s` `errori_decodifica` `formato` `giro_eco` `ha_visto_il_guasto` `immagine` `inizio_finestra_t` `inizio_t` `latenza_ms` `legami_in_ingresso` `mem_totale_mb` `mem_usata_mb` `motivo` `nascita_ms` `nascita_s` `nodo` `origine` `pacchetto` `positivo` `primari` `primo_fotogramma_ms` `primo_non_degenere_s` `processi_gpu` `recinti` `remotix-appunti` `remotix-cattura` `remotix-figlio` `remotix-invisibile` `remotix-suono` `remotix_porta` `ritardi_eco_ms` `ritardi_ms` `sessioni_durante` `sessioni_remotix` `si` `sistema` `stato` `strozzatura_frazione` `tastiera` `tocco` `tratti keys (strada, tela, dipinti, consegnati, fuori, dentro, coda_dec, saltati_coda, tardive, eta_ms, ric_ms, costo_disegno_ms, "8_decode_richiamo", "9a_richiamo_chiamata", "9b_conversione", "10_vetro", "9_10_richiamo_vetro", "11_vetro_prossimo_quadro")` `utenti-negati`

**opzioni-contratto.tsv** — kept (unresolved collision): 19, left out on purpose (step 2): 2, no Italian word: 2, not renamed (path, product name, or not found by the analysis): 25, renamed by dati.tsv: 4, renamed by the table: 753

Not renamed: `B3_SPIA` `BRUCIATORI` `C15G4_TEMPI` `CASA` `FINTO_CLASSE` `FINTO_MUORE` `G7_TRACCIA` `LIVELLO` `OPERAZIONI` `PARLANTINA` `PROFONDITA` `PUNTO` `QUALITA` `VECCHIA_X264_EXTRA` `W1_RIPRENDI` `W1_STRADA` `W1_TIENI` `a-secco` `aggiorna` `argomenti` `con-guasti` `copia` `dipinto` `elenca` `formato` `fotografia` `nodo` `porta` `raffica` `remotix-figlio` `riavvia` `segnale` `senza-nastro` `senza-rete` `sistema` `solo-certifica` `stato` `sul-server` `tutte` `ultimi` `un-verso` `visibile`

**rcp-contratto.tsv** — kept (unresolved collision): 5, no Italian word: 22, not renamed (path, product name, or not found by the analysis): 3, renamed by dati.tsv: 34, renamed by the table: 156

Not renamed: `RCPREG` `finita` `motivo` `remotix-pagina` `restanoMs` `si` `stato` `tocco`


### Step 2 (later): file and directory moves (520)

Every reference is in rinomina2-plan.json → file_moves (first 200 per file).

| old | new | references |
|---|---|---|
| `DECISIONI.md` | `DECISIONS.md` | 1087 |
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
| `banchi/16-stress/16-classifica.py` | `benches/16-stress/16-ranking.py` | 31 |
| `banchi/16-stress/16-coda.sh` | `benches/16-stress/16-queue.sh` | 15 |
| `banchi/16-stress/16-compositori-rdp.sh` | `benches/16-stress/16-compositors-rdp.sh` | 12 |
| `banchi/16-stress/16-compositori.sh` | `benches/16-stress/16-compositors.sh` | 11 |
| `banchi/16-stress/16-controllo-corto.py` | `benches/16-stress/16-check-short.py` | 7 |
| `banchi/16-stress/16-d023-cornice.c` | `benches/16-stress/16-d023-border.c` | 1 |
| `banchi/16-stress/16-d023-cornice.sh` | `benches/16-stress/16-d023-border.sh` | 6 |
| `banchi/16-stress/16-lavori.py` | `benches/16-stress/16-jobs.py` | 8 |
| `banchi/16-stress/16-rapporto.py` | `benches/16-stress/16-report.py` | 8 |
| `banchi/16-stress/16-riclassifica.py` | `benches/16-stress/16-reclassify.py` | 9 |
| `banchi/16-stress/16-risorse.py` | `benches/16-stress/16-resources.py` | 13 |
| `banchi/16-stress/16-salita.py` | `benches/16-stress/16-climb.py` | 31 |
| `banchi/16-stress/finti/16-attore.py` | `benches/16-stress/fake/16-actor.py` | 15 |
| `banchi/16-stress/finti/16-classifica.py` | `benches/16-stress/fake/16-ranking.py` | 31 |
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
| `banchi/18-a1/costruisci.sh` | `benches/18-a1/build.sh` | 111 |
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
| `installatore/costruisci.sh` | `installer/build.sh` | 111 |
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
| `installatore/motore/occupato.go` | `installer/engine/taken.go` | 4 |
| `installatore/motore/occupato_test.go` | `installer/engine/taken_test.go` | 0 |
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
| `packaging/arch/costruisci.sh` | `packaging/arch/build.sh` | 111 |
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
| `src/costruisci.sh` | `src/build.sh` | 111 |
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
| `src/figlio.c` | `src/child.c` | 365 |
| `src/figlio.h` | `src/child.h` | 34 |
| `src/forma.c` | `src/shape.c` | 18 |
| `src/forma.h` | `src/shape.h` | 20 |
| `src/opus-wasm/costruisci.sh` | `src/opus-wasm/build.sh` | 111 |
| `src/opus-wasm/decodifica.c` | `src/opus-wasm/decoding.c` | 5 |
| `src/opus-wasm/prova/confronta.mjs` | `src/opus-wasm/prova/compare.mjs` | 5 |
| `src/opus-wasm/prova/riferimento.c` | `src/opus-wasm/prova/reference.c` | 4 |
| `src/pagina.c` | `src/page.c` | 44 |
| `src/pagina.h` | `src/page.h` | 8 |
| `src/pagina.html` | `src/page.html` | 309 |
| `src/provisiona.sh` | `src/provisions.sh` | 86 |
| `src/registro.c` | `src/log.c` | 53 |
| `src/registro.h` | `src/log.h` | 106 |
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
