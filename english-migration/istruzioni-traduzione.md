# Traduzione in inglese del codice di REMOTIX — passo 1: commenti e scritte

Deposito: /home/nicfio/Documenti/REMOTIX, ramo `full-english` (già attivo, non cambiare ramo).
Decisione: DECISIONI.md §10.38 — REMOTIX diventa interamente inglese.

Il lavoro è in due passi. **Questo è il passo 1**: si traducono in inglese i COMMENTI e le
SCRITTE (testo leggibile da una persona). **I NOMI NON SI TOCCANO**: li rinomina dopo un programma,
in modo meccanico e uguale in tutti i file, con un vocabolario comune. Se tu cambiassi un nome,
il programma non lo troverebbe più e i file non combacerebbero.

## Cosa si traduce
- Tutti i commenti (C, Go, JS, Python, shell, Makefile, spec, conf, unit systemd, PAM…).
- Le stringhe che sono frasi per una persona: righe di log, messaggi d'errore, testo d'aiuto
  (`--help`), testi dell'interfaccia della pagina, messaggi stampati dagli script, testi della TUI.
- Le date nei commenti in formato inglese breve («12 ago 2026» → «12 Aug 2026»).

## Cosa NON si tocca (resta identico, anche se italiano)
- Identificatori di qualunque tipo: funzioni, variabili, tipi, campi, macro, costanti, etichette.
- Nomi di file e cartelle, anche quando citati in commenti o stringhe (`figlio.c`, `banchi/`,
  `DECISIONI.md §4.2`).
- Opzioni della riga di comando (`--tetto-sessioni`), variabili d'ambiente (`REMOTIX_OPZIONI`).
- Stringhe che sono dati e non frasi: nomi dei messaggi RCP (`CONGEDO`), nomi e valori delle
  capacità (`video.profondita`, `si`), chiavi JSON, nomi delle aree del registro (`sessione`,
  `cattura`), valori di stato confrontati dal codice, nomi di comandi del socket (`SBLOCCA`, `TOLTO`),
  parole chiave lette da file di configurazione.
- Specificatori di formato (`%s`, `%d`, `%.1f`), sequenze di escape, emoji-marcatore all'inizio
  delle righe di log (⭐ ⛔ 📄 ⚠ …): restano al loro posto.
- Le marche `[M]`, `[R]`, `[S]`, `[?]` e i numeri misurati.
- Codice di terze parti (vendor/, protocolli XML, file generati).

Dubbio fra «frase» e «dato»: se il codice confronta quella stringa, la cerca, la manda sul filo o
un altro programma la legge, è un dato → non toccarla e segnalala nel rapporto.

## Le righe che altri leggono — OBBLIGATORIO
I banchi di prova e l'installatore cercano certe righe di log e di uscita (grep, `in`, regex).
Per OGNI stringa letterale che traduci e che finisce in un log, su stdout/stderr o in un file,
aggiungi una riga JSON al file
`/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/9152ae97-53f9-48e3-af28-e968d49b4cb7/scratchpad/stringhe/<gruppo>.jsonl`
nella forma `{"file": "src/main.c", "prima": "<testo italiano esatto>", "dopo": "<testo inglese esatto>"}`.
Servirà a correggere i banchi che cercavano il testo vecchio. Non serve per i commenti.

## Come si scrive
- Inglese semplice e preciso, per chi mantiene il prodotto. Stessa densità e stesso tono del
  commento originale: non accorciare togliendo informazioni, non allungare.
- I termini del progetto hanno già un nome inglese: leggi prima il glossario del manuale,
  `docs/sources/technical/ch24_glossary.py` (tela → canvas, palco → stage, figlio → child,
  aiutante → helper, banco → bench, guasto → fault, cura → cure, lastra → slab, cintura → belt,
  sentinella → sentinel, congedo → farewell…). Usali sempre uguali.
- Quando un commento cita un nome italiano del codice, lascia il nome com'è (`cattura_prendi()`):
  sarà rinominato dopo.
- Le citazioni dell'utente fra «» si traducono in inglese, tenendole fra virgolette.

## Controlli prima di finire
- Il comportamento del programma NON cambia: nessuna riga di codice diversa salvo il testo delle
  stringhe-frase.
- C: le stringhe restano valide (attenzione a `"` e `\` dentro il testo, alle stringhe spezzate su
  più righe, alle larghezze fisse in `printf` come `%-20s`). Go: `gofmt -l` sul file non deve
  segnalare nulla. Shell: `bash -n file`. Python: `python3 -m py_compile file`. JS dentro HTML:
  le stringhe con apici e backtick restano bilanciate.
- `grep -nP '[àèéìòù]|\b(il|della|perché|anche|quando|sono|questo)\b'` sui tuoi file: quel che resta
  deve essere solo nomi, dati o citazioni volute.
- Non fare commit, non toccare file fuori dal tuo gruppo, non collegarti al server (gira una
  campagna di misure). Puoi dividere il lavoro fra copie di te in parallelo, un file a testa.

## Rapporto (in italiano)
Quali file hai tradotto, quante stringhe hai registrato nel jsonl, le stringhe che hai lasciato
perché sono dati (con file:riga), e i dubbi.
