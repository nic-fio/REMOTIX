# Traduzione dei BANCHI di prova — passo 1

Leggi prima, e segui, le regole generali:
/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/9152ae97-53f9-48e3-af28-e968d49b4cb7/scratchpad/istruzioni-traduzione.md
(stesso deposito, stesso ramo `full-english`, stesse cose da tradurre e da NON toccare: i NOMI restano).

In più, per i banchi:

## 1. I banchi cercano il testo del prodotto: va seguito
Il prodotto (src/, installatore/, packaging/) è già tradotto. Ogni riga di log o di uscita che è
cambiata sta in `english-migration/strings/*.jsonl` (campo `prima` = testo italiano vecchio,
`dopo` = testo inglese nuovo; 3.351 righe; dove il sorgente aveva `\n` o `\"`, il jsonl li riporta
scritti così). Ogni volta che un tuo banco CERCA testo del prodotto (grep, `in`, `re.search`,
`indexOf`, `startswith`, `awk /…/`, confronti, conteggi di righe del registro, sostituzioni di testo
dentro src/pagina.html per innestare guasti, ancore cercate nei commenti della pagina), sostituisci il
pezzo italiano con quello inglese **esatto** del jsonl. Attenzione:
- il banco può cercare solo un PEZZO della riga: trova nel jsonl la riga che lo contiene e prendi il
  pezzo corrispondente nel `dopo`;
- se un pezzo cercato non si trova né nel jsonl né nel prodotto attuale (`grep -rn` in src/ e
  installatore/), il testo nel prodotto era già cambiato prima di oggi: lascialo e segnalalo;
- verifica sempre col prodotto vero: dopo la tua modifica il pezzo cercato deve comparire in src/
  (o installatore/) — `grep -rnF '<pezzo>' src installatore` — salvo che sia costruito con %s.
- Restano italiani nel prodotto, per ora, i DATI (nomi dei messaggi, capacità, chiavi, aree del
  registro, stati, frasi del CONGEDO che vanno sul filo). Se il banco cerca quelli, non toccarli.

## 2. Le parole che i banchi stampano
I banchi stampano esiti e rapporti: traducili come scritte. Ma se un altro banco o uno script legge
quel testo (11-gancio.sh legge le uscite delle suite C1…C24, i classificatori leggono i registri),
cambia insieme chi scrive e chi legge, e annota la coppia nel tuo jsonl. Le parole di esito usate come
dati (VERDE/ROSSO, OK/KO, PASS, nomi delle classi di difetto) restano come sono: le rinomina il
programma dopo.

## 3. Cosa non si tocca
- I file di dati e i registri storici (.jsonl, .json, .txt, .log, .csv, immagini): non si traducono.
- `banchi/rcp/` (copie gemelle del prodotto: le ricopio io).
- Nessun comando sul server, nessun commit.

## 4. Controlli
Come nelle regole generali (scheletro del codice identico salvo i testi cercati e le scritte,
`bash -n`, `python3 -m py_compile`, `gcc -fsyntax-only` se si può). Le uniche righe di CODICE che
possono cambiare sono le stringhe cercate (punto 1) e le scritte (punto 2).

## 5. Rapporto (in italiano)
File tradotti; quante ricerche hai allineato al prodotto (con 3-4 esempi); le ricerche che non hai
potuto allineare (file:riga e perché); i dubbi. jsonl delle tue scritte cambiate:
`/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/9152ae97-53f9-48e3-af28-e968d49b4cb7/scratchpad/stringhe/<gruppo>.jsonl`.
