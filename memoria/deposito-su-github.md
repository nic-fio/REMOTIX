---
name: deposito-su-github
description: dal 28 ago 2026 il progetto si chiama REMOTIX (non piu' _V2); dal 29 ago 2026 NON ha copia locale — fonte unica github.com/nic-fio/REMOTIX, pubblico
metadata:
  type: project
---

**Il progetto si chiama REMOTIX.** Il «_V2» e' caduto il 28 agosto 2026: serviva
a distinguerlo da v1, e v1 non esiste piu' come progetto a se'.

- ⛔ **NESSUNA cartella locale.** `~/Documenti/REMOTIX` e' stata cancellata il
  29 agosto 2026: «l'unica fonte di verita' e' il repository GitHub», per non
  avere doppioni sparsi sul tablet. ⇒ Per lavorarci **si clona**.
- deposito: `https://github.com/nic-fio/REMOTIX` — **PUBBLICO dal 29 agosto 2026**, ramo predefinito
  `fase-10-cure` (`master` e' fermo al 9 agosto, non e' il ramo di lavoro)
- ⚠ Dopo ogni clone il gancio **non c'e'**: `.git/hooks/` non e' versionato.
  ⇒ `bash banchi/11-scatole/11-gancio.sh installa pre-push`, altrimenti le
  spinte passano senza nessun controllo — e stavolta **in silenzio**, perche' un
  gancio assente non esce 127: semplicemente non c'e'.

⭐ **APERTO IL 29 AGOSTO 2026 — e la parola d'ordine resta dentro, per scelta.**

⛔ **NON e' un problema aperto, e non va riproposto.** La riga
`printf 'nicfio\n' | sudo -S ...` sta in **117 file** dei banchi e in **62
commit** della storia, e ci resta. La macchina di prova vive su una **rete
locale chiusa**: non e' raggiungibile da fuori, quindi quella parola d'ordine
non apre niente a nessuno. Deciso dall'utente il 29 agosto 2026.

⚠ Questa nota diceva il contrario fino a stamattina — «resta privato», «va
cambiata al ritorno del server». ⛔ Era la valutazione sbagliata, e valeva su
un rischio che qui non c'e'.

⚠ Il conto dei «9 file» che stava scritto qui era sbagliato di dodici volte.
`[M]` 29 ago 2026: `git grep -Il "sudo -S" | wc -l` ⇒ **117**. ⭐ Il numero si
verifica, non si cita a memoria — vale per ogni conto in queste note.

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
