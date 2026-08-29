---
name: deposito-su-github
description: dal 28 ago 2026 il progetto si chiama REMOTIX (non piu' _V2), sta in ~/Documenti/REMOTIX e su github.com/nic-fio/REMOTIX, PUBBLICO dal 29 ago 2026
metadata:
  type: project
---

**Il progetto si chiama REMOTIX.** Il «_V2» e' caduto il 28 agosto 2026: serviva
a distinguerlo da v1, e v1 non esiste piu' come progetto a se'.

- cartella: `~/Documenti/REMOTIX`
- deposito: `https://github.com/nic-fio/REMOTIX` — **PUBBLICO dal 29 agosto 2026**, ramo predefinito
  `fase-10-cure` (`master` e' fermo al 9 agosto, non e' il ramo di lavoro)

⛔ **APERTO IL 29 AGOSTO 2026, con la parola d'ordine ancora dentro.** Scelta
dichiarata dall'utente quel giorno: quella parola d'ordine **non conta piu'**.

⚠ Quel che e' pubblico, detto per intero — non erano 9 file, erano **117**, e
la storia ne porta **62 commit**: la riga `printf 'nicfio\n' | sudo -S ...` si
legge oggi da chiunque, nell'albero e all'indietro. ⛔ Cancellarla adesso non
basta e non e' mai bastato: la storia di git non dimentica, e il deposito e'
gia' stato letto pubblicamente.

⇒ **La parola d'ordine `nicfio` della macchina di prova va considerata bruciata
per sempre**, non «da cambiare quando capita». Al ritorno del server: cambiarla,
e da li' in poi farla leggere da un file fuori dal deposito — mai piu' una
parola d'ordine dentro un file che si committa.

⚠ Il conto dei «9 file» stava scritto qui ed era sbagliato di dodici volte. `[M]`
29 ago 2026: `git grep -Il "sudo -S" | wc -l` ⇒ 117.

⭐ **Quel che era v1 sta sotto `fondamenta/`** (rinominata il 28 ago 2026: «non voglio
riferimenti a cose passate»)** e NON e' un archivio, e NON e' un archivio**:
`fondamenta/strumenti/sshpw.py` (39 richiami), `fondamenta/remotix-c/src` (34), `fondamenta/banco/enter.sh`
e i filmati di `fondamenta/calibrazione/` sono attrezzatura viva dei banchi.
Vedi [[costruire-serve-il-contenitore]] e [[riavvio-perde-la-chiave-ssh]].

⚠ **I registri di misura non sono stati rinominati**: `*.jsonl` e `*.log` portano
ancora «REMOTIX_V2», e devono. Sono verbali di misure fatte, e dicono con che nome
girava il prodotto quel giorno. ⭐ Un registro si aggiunge, non si corregge.

⚠ **Il rebranding non e' stato riprovato sul ferro** (macchina in assistenza dal
27 agosto): al ritorno del server, il primo giro della rete anti-regressione vale
anche come collaudo. La marca d'avvio e' cambiata su tutt'e due i lati insieme —
`src/main.c` la scrive, `01-b0-bersaglio`, `10-b96`, `10-b90` e `11-c9` la
controllano. Vedi [[progetto-in-pausa-agosto-2026]].

⚠ Fuori dal deposito e NON su GitHub: `~/SERVER.ssh` e `~/.ssh/id_ed25519`,
CANCELLATE il 28 ago 2026: vedi [[credenziali-da-rigenerare]].

⛔⛔ **IL GANCIO PORTA UN PERCORSO ASSOLUTO, e sta FUORI dal deposito.**
`.git/hooks/pre-push` non e' versionato e contiene il percorso scritto per esteso:
rinominare la cartella del progetto lo **uccide in silenzio**, e da quel momento
`git push` viene RIFIUTATO (il gancio esce 127). ⚠ E con `git push --quiet` il
messaggio non si vede: sembra andata, e il commit resta a casa.
⇒ Dopo ogni spostamento della cartella: `bash banchi/11-scatole/11-gancio.sh installa pre-push`,
e poi si CONTROLLA che il commit sia su GitHub — non ci si fida dell'uscita del comando.
