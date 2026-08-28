# I ritrovati — cinque file che vivevano SOLO fuori dal deposito

*Raccolti il 28 agosto 2026, svuotando il tablet: erano in `~/b16-albero` e in
`/var/tmp/`, cartelle che stavano per essere cancellate.*

⛔ **Nessuno di questi è mai stato committato.** Sono venuti fuori perché prima di
cancellare ho confrontato ogni `.sh`, `.py` e `.c` degli avanzi con il deposito —
⭐ e non li avrebbe trovati nessuna ricerca per nome: le cartelle si chiamavano
`b16-albero`, `rmx-L2`, `corsia-d`.

| file | da dove | che cos'è |
|---|---|---|
| `03-b16-gira.sh` | `~/b16-albero/gira.sh` | lancia un giro di **B16** sulla copia in albero e segna il codice d'uscita |
| `03-b16-innesta.py` | `~/b16-albero/innesta.py` | ⭐ **innesta e toglie il guasto di B16** sulla pagina dell'albero di prova — è la macchina che rende certificabile quel banco (§3.6) |
| `03-ff-disegno-giro.sh` | `/var/tmp/corsia-d/disegno.sh` | il cerchio che gira `03-ff-disegno.py` su Chrome e Firefox, con e senza finestra |
| `L2-gnome-shell-edit.py` | `/var/tmp/rmx-L2/edit.py` | applica tre modifiche REMOTIX a un albero di **gnome-shell 50.3** |
| `L2-filo-lock-vuoto.c` | `/var/tmp/rmx-L2/filo.c` | sonda da 22 righe: *un `LOCK` a corpo vuoto sopravvive al filo?* |

⚠ **Sono conservati com'erano, non riletti né riprovati**: il primo dovere era non
perderli. ⛔ Non c'è nessuna garanzia che girino ancora — `L2-*` in particolare
lavora su un albero di gnome-shell che qui non c'è.

⚠ E `03-ff-disegno-giro.sh` porta un percorso corretto oggi: diceva
`~/Documenti/REMOTIX_V2`, che dopo il rebranding non esiste più.

⭐ **La lezione, che oggi si è ripetuta tre volte**: quel che non ha il nome del
progetto addosso non lo trova nessuna ricerca per nome. Si trova solo
**confrontando il contenuto** con quel che il deposito ha già.
