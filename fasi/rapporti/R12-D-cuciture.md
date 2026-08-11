# R12 — lente D: le cuciture fra i cinque

*Revisione avversariale della notte del 10-11 agosto 2026. Mandato:
`fasi/rapporti/MANDATO-10-agosto-notte.md` §2, riga «D — le cuciture fra i cinque».
Non ho letto gli altri rapporti di stanotte, per la ragione scritta nel mandato §2.*

⛔ **La domanda che ho tenuto in mano**: *se questi cinque pezzi si mettono in fila, il risultato
regge — o regge solo perché nessuno ha provato a farli lavorare insieme?*

⛔ **La risposta breve, e sta tutta in una riga**: **nessuno li ha messi in fila.** Il pezzo nuovo
della notte — il server di prodotto in `src/` — non è acceso da nessun banco, non è nominato da
nessun documento, non è in git, e nei tre punti in cui tocca il lavoro degli altri quattro fa la
stessa cosa in un modo diverso. Le cuciture *dentro* il vecchio impianto (innesto ↔ `rcp.c` ↔ B8)
reggono e sono le meglio scritte del progetto; quelle *verso* il pezzo nuovo non esistono ancora.

---

## 0. Che cosa ho eseguito, e su che cosa

⚠ Non ho misurato niente sul ferro (`REVIEWER.md` §5) e non ho toccato la macchina di prova. Quel che
ho eseguito è **confronto di file**, e lo dichiaro col denominatore (`LEZIONI.md` §1.9 punto 4):

| Strumento | Su che cosa | Controllo positivo |
|---|---|---|
| `md5sum` · `diff` | `banchi/rcp/{rcp.c,rcp.h,autenticazione.c}` contro `src/` (3 coppie su 3) | i tre `diff` sono vuoti e i tre `md5` combaciano |
| `grep -c` | 6 documenti alla radice e in `fasi/`, tutti i `banchi/01-*`, tutta `src/` | ogni ricerca «zero» ha accanto una ricerca che **trova**: es. `data-bannato` → 0 in `src/`, **2** in `banchi/01-b3-rcp-innesta.py` |
| `python3` | l'aritmetica di S1b, sui due numeri pubblicati dal documento | ricalcolata due volte, dai microsecondi del `.jsonl` e dalla data del `.md` |

⛔ **Quel che NON ho potuto guardare**, e va detto perché ogni rilievo che segue vale entro questo
confine: `/media/REMOTIX` non è montata su questa macchina (`ls` → *File o directory non
esistente*), quindi **non ho visto né `b2/ngtcp2/examples/rcp.c` né il binario `bsslserver`**. Tutto
quel che dico della «copia compilata» è letto negli script che la producono, non nella copia.

---

## R12.1 ⛔⭐ Lo sblocco di §4.4-bis esiste in due forme, e la forma del prodotto è quella che l'altro autore ha scritto per esteso che **non funziona**

**DOVE**
- `src/main.c:79-81` (`--sblocca IND   toglie il ban a un indirizzo e esce`), `:117-118`, `:171-188`
- `banchi/01-b3-rcp-innesta.py:1198-1226`, e in particolare **`:1207-1214`**
- `banchi/01-b8-sblocca.py:5-6, 85, 132` (parla su un **socket**, mai su un'opzione)

**COSA CONTRADDICE**
`banchi/01-b3-rcp-innesta.py:1207-1214`, che è l'analisi scritta dall'agente 1 la stessa notte:

> ⛔ un SECONDO PROCESSO con un'opzione (`bsslserver --sblocca X`) — **non funziona**, e il modo in
> cui non funziona è silenzioso: il ban vive nella memoria del processo che serve, e un secondo
> processo può solo riscrivere il file. Il server continuerebbe a rispondere `TROPPI_TENTATIVI`
> fino al riavvio, e ⛔ il primo `salva_ban()` — cioè il primo ban di chiunque altro — riscriverebbe
> il file rimettendoci dentro il ban appena tolto. **Chi ha dato il comando lo ha visto uscire con
> zero.**

E contraddice `RCP.md:686-687, 732, 741` («si esce in due modi») insieme a `LEZIONI.md` §1.9: un
comando che risponde sempre la stessa cosa non ha nessun sintomo.

**COME SI DIMOSTRA** — un caso concreto, tre righe di codice del prodotto:

1. il server è acceso con `--ban /var/lib/remotix/ban` (`src/main.c:93`). Un indirizzo fallisce tre
   volte: `src/rcp.c:551-557` scrive `tentativi[i].bannato_fino` **nella memoria di quel processo**
   (`src/rcp.c:311-321`, `static struct … tentativi[MAX_TENTATIVI]`) e chiama `salva_ban()`;
2. il padrone di casa dà `remotix --sblocca 192.168.0.2`. È un **processo nuovo**: `main.c:154`
   chiama `rcp_ban_carica()`, che ricostruisce la tabella *del nuovo processo* dal file
   (`src/rcp.c:640-654`); `main.c:184` chiama `rcp_sblocca()`, che toglie la voce **dalla tabella
   del nuovo processo** e riscrive il file (`src/rcp.c:593-604`); `main.c:185-187` stampa **«era
   bannato, adesso è libero»** e **esce 0**;
3. il processo che *serve* non ha visto niente: la sua `tentativi[]` è intatta. Il quarto tentativo
   riceve ancora `TROPPI_TENTATIVI` (0x08) e la pagina dice ancora «esauriti». E al primo ban
   successivo di **chiunque altro**, `salva_ban()` (`src/rcp.c:496-503`) riscrive il file dalla
   memoria stantia: **il ban tolto ritorna anche su disco.**

⛔ Il danno non è che non funziona: è che **esce 0 dicendo che ha funzionato**. È la settima veste di
`LEZIONI.md` §1.9 applicata a un comando invece che a un banco.

**MARCA** `[R]`

> ### R12.1-bis — e per lo stesso motivo `01-b8-sblocca.py` non può parlare col prodotto
>
> **DOVE** `banchi/01-b8-sblocca.py:132` (`--socket`, predefinito `/srv/src/b8-comando.sock`) contro
> `src/main.c:102-125`, dove `--comando-socket` **non è fra le opzioni** e qualunque opzione
> sconosciuta stampa `aiuto()` ed esce **2**.
> **COME SI DIMOSTRA** `grep -rn "comando-socket"` su tutto il repo: **13 occorrenze**, tutte in
> `banchi/`, **zero** in `src/`. Il denominatore: la stessa ricerca trova `--sblocca` **2 volte, solo
> in `src/main.c`**, e zero nei banchi.
> ⛔ Quindi la regola **B0.3** di `fasi/01-filo-nudo.md` — *«fra un banco e l'altro si chiama il
> comando di sblocco»*, che `01-b8-sblocca.py:14-26` chiama «il vincolo più duro del capitolo» — **non
> è applicabile al server di prodotto**: contro `src/`, `01-b8-sblocca.py` esce 3 con «il socket non
> esiste». ⚠ Almeno esce 3 e non 0: quella parte è scritta bene (vedi §Reggono).
> **MARCA** `[R]`

---

## R12.2 ⛔ La pagina del rifiuto ha due formati, e B8 misura i marcatori che **solo l'innesto** produce

**DOVE**
- il misuratore: `banchi/01-b8-cronometro.py:407` `re.search(r'data-bannato="(si|no)"', corpo)`,
  `:410` `data-restano-ms="(\d+)"`, `:419` `"tentativi esauriti" in corpo`
- il misurato numero uno: `banchi/01-b3-rcp-innesta.py:1105-1139` (`remotix_pagina_html`)
- il misurato numero due: `src/pagina.c:253-263` + `src/pagina.html:55, 104`

**COSA CONTRADDICE** La forma d'errore **E2** di `REVIEWER.md` §2 — *due misure diverse sotto la
stessa etichetta*. L'etichetta è «la pagina che §4.4-bis pretende»; i due comportamenti sono due
documenti HTML senza un solo campo in comune.

**COME SI DIMOSTRA** — `grep -c` sui tre marcatori che B8 cerca, con il controllo positivo accanto:

| marcatore che B8 pretende | `src/pagina.c` | `src/pagina.html` | `01-b3-rcp-innesta.py` |
|---|---|---|---|
| `data-bannato` | **0** | **0** | 2 |
| `data-restano-ms` | **0** | **0** | 2 |
| `tentativi esauriti` (sottostringa esatta) | **0** | **0** | 3 |

Il prodotto la stessa cosa la dice così (`src/pagina.c:257-262`): *«I tentativi di accesso da questo
indirizzo sono **esauriti**. Riprova fra %llu ore e %llu minuti…»* — sette parole in mezzo, quindi
la sottostringa che B8 cerca non c'è; e il numero di millisecondi residui **non compare affatto** nel
documento servito, perché il prodotto lo formatta già in ore e minuti e butta il resto.

⛔ Conseguenza concreta: il giorno in cui qualcuno punta `01-b8-cronometro.py` al server di `src/`,
i tre controlli della pagina diventano **rossi su un server che il ban lo fa**, e il rosso finisce
sull'imputato sbagliato — che il mandato §0 chiama «il difetto più caro di questo progetto».

**MARCA** `[R]`

> ⚠ E un secondo scarto nello stesso punto, che nessun banco vedrebbe perché nessuno lo guarda: nel
> prodotto la frase sta in `<div id="avviso" **hidden**>__AVVISO__</div>` (`src/pagina.html:55`) e a
> toglierle `hidden` è **JavaScript** (`:82`). Nell'innesto la frase è nel corpo, in chiaro
> (`01-b3-rcp-innesta.py:1129-1132`). ⛔ §4.4-bis vuole che chi è bannato **legga** perché; nel
> prodotto lo legge solo se lo script gira. `[?]`

---

## R12.3 ⛔ Tre copie di `rcp.c`, e il confronto che esiste ne guarda solo due

**DOVE**
- copia A — il banco: `banchi/rcp/rcp.c` · `rcp.h` · `autenticazione.c`
- copia B — la compilata: `…/b2/ngtcp2/examples/rcp.c`, prodotta da `banchi/01-b3-rcp-innesta.py`
- copia C — il prodotto: `src/rcp.c` · `src/rcp.h` · `src/autenticazione.c`, compilata da
  `src/Makefile:33-34`
- il solo confronto esistente: `banchi/01-b6-lancia.sh:220-239` (`SORGENTE_RCP=$FUORI/rcp/rcp.c`,
  `COMPILATO_RCP=$FUORI/b2/ngtcp2/examples/rcp.c`) — **A contro B**, e **solo sui `#define TETTO_*`**

**COSA CONTRADDICE** `banchi/01-b6-lancia.sh:197-206`, che è il progetto stesso che scrive la regola:
*«Leggere solo il sorgente direbbe un numero che nel server in esecuzione potrebbe non esserci… Qui
si leggono tutt'e due e si pretende che combacino.»* La copia C è nata stanotte e quella pretesa non
la copre.

**COME SI DIMOSTRA** — oggi le copie A e C sono **identiche**, e l'ho verificato:

```
495befc76f883b7a797c09e858134323  banchi/rcp/rcp.c
495befc76f883b7a797c09e858134323  src/rcp.c
165b2b5be2cfefb6db40a91a74c61754  banchi/rcp/rcp.h   (= src/rcp.h)
47ac586faeaeec838005cbb2e2210b76  banchi/rcp/autenticazione.c  (= src/autenticazione.c)
```

⛔ **E questo è precisamente il rilievo, non la sua assenza.** Sono identiche *per fortuna*, non per
costruzione: nessun file del repo confronta C con A. Il caso concreto: si cambia `BAN_DURATA`
(`src/rcp.c:308`) da `43200000` a `3600000`. Il prodotto banna un'ora invece di dodici; `01-b6-lancia.sh`
resta verde perché guarda A e B; B8 resta verde perché accende `bsslserver`; nessun `.md` cita `src/`.
**Il difetto non cambia colore a niente.** ⚠ E il verso opposto è già in moto: `git status` dice
`M banchi/rcp/rcp.c` e `?? src/` — le due copie hanno **due storie diverse** da stanotte, una tracciata
e una no.

⭐ Quale delle due è il prodotto? `src/rcp.h:11-14` dichiara che il modulo *«potrà passare dal server
d'esempio di ngtcp2 al server vero senza riscriverlo»* — cioè si presenta come **uno**. Ne sono due.

**MARCA** `[R]`

---

## R12.4 ⛔ B12 guasta un file e registra l'impronta di un altro

**DOVE** `banchi/01-b12-guasti.py:76` (`ESEMPI = …/b2/ngtcp2/examples`), i guasti a
`ESEMPI/rcp.c` (`:142, :208, :228-231, :247, :294, :312`) — contro `:636`
`sorgente = os.path.join(QUI, "rcp", "rcp.c")`, e `:642` `"impronta_rcp_c": impronta_file(sorgente)`.

**COSA CONTRADDICE** `banchi/01-b12-guasti.py:648-649`, il commento che accompagna quella riga:
*«La certificazione ha una DATA e l'impronta del sorgente: un banco certificato su un codice che nel
frattempo…»*. L'impronta scritta **non è del codice su cui il banco è stato certificato**: è del
sorgente che B12 non tocca, mentre il guasto vive nella copia dentro `examples/`.

**COME SI DIMOSTRA** Il registro prodotto stanotte,
`banchi/01-b12-registro.jsonl`, due righe a 1 h 42 min di distanza:

```
{"quando":"2026-08-10T21:19:09", …, "impronta_rcp_c":"d839839f2edef5a09b748365ca12377e"}
{"quando":"2026-08-10T23:01:46", …, "impronta_rcp_c":"d839839f2edef5a09b748365ca12377e"}
```

E ho verificato che quella è la SHA-256 (primi 32 caratteri) di `banchi/rcp/rcp.c`:
`d839839f2edef5a09b748365ca12377e`. ⛔ Il guasto **B6** di quel catalogo sostituisce
`#define TETTO_CIAO 5000` con `500` in `ESEMPI/rcp.c` (`:228-231`): durante il giro guasto quel file
è **diverso da qualunque impronta il registro possa scrivere**, e l'impronta registrata resta la
stessa prima, durante e dopo. Il registro risponde a *«che sorgente c'era in `banchi/rcp/`?»*
mentre dichiara di rispondere a *«su che codice è certificato questo banco?»*.

**MARCA** `[R]`

---

## R12.5 ⛔ B13 giudica il codice del server acceso leggendo una copia che non è quella compilata

**DOVE** `banchi/01-b13-proprieta.py:736` (`sorgente = os.path.join(QUI, "rcp", "rcp.c")`, proprietà 6
— il ramo `RIPRESA`) contro `banchi/01-b13-lancia.sh:58` e `:134`, dove il server acceso è
`…/b2/ngtcp2/build/examples/bsslserver`, compilato da `examples/rcp.c`.

**COSA CONTRADDICE** `banchi/01-b6-lancia.sh:197-206` — il banco gemello, scritto dalla **stessa
mano** (agente 3), che per la stessa domanda legge **tutt'e due** le copie e pretende che combacino.
Due banchi dello stesso autore, due regole diverse per la stessa cosa.

**COME SI DIMOSTRA** B13 ha un controllo positivo, e lo dichiara (`:744-750`): *«"SESSIONE" si trova
in rcp.c, quindi il file è quello giusto»*. ⛔ Quel controllo risponde a *«sto leggendo un `rcp.c`?»*,
non a *«sto leggendo quello che è dentro il binario che ho appena acceso?»* — che è la domanda
dell'ottava veste di `LEZIONI.md` §1.9 (*«"il file c'è" e "il file è quello che ho appena costruito"
sono due domande diverse»*). Caso concreto: si aggiunge un ramo `RIPRESA` a `examples/rcp.c` senza
ricopiarlo in `banchi/rcp/rcp.c`; il server lo esegue, B13 legge l'altro file, non trova la parola,
e stampa **«nel codice il ramo RIPRESA non esiste»** (`:763-764`) — verde, sulla metà del giudizio
che il filo non può vedere.

**MARCA** `[R]`

---

## R12.6 ⛔ S1b — «604 800 s esatti» non discende dai due numeri che il documento pubblica, e lo strumento citato come provenienza dice un'altra cosa

**DOVE** `web/rapporti/S-esiti-sonda.md:17` e `:107` — *«scade il **2026-08-17T21:09:47Z**, cioè
**604 800 s esatti** dalla concessione»* — contro `banchi/01-s1b-stato.jsonl` riga 1.

**COSA CONTRADDICE** `LEZIONI.md` §1.9 punto 5 (*«un denominatore si legge dove la cosa succede»*) e
**E5** di `REVIEWER.md` §2: un fatto che era una deduzione mai misurata. ⛔ E la nota di §1.9: *«un
denominatore falso è peggio di nessun denominatore, perché dà alla misura l'aria di essere già stata
controllata»*.

**COME SI DIMOSTRA** — l'aritmetica, sui due numeri che il documento stesso pubblica:

```
concessione (jsonl, riga 1)   2026-08-10T21:10:01+00:00
scadenza  (13431474587889370 µs dal 1601, decodificata)
                              2026-08-17T21:09:47.889+00:00
differenza                    604 786,889 s        ⛔  non 604 800
sette giorni esatti sarebbero 2026-08-17T21:10:01Z ⛔  non 21:09:47Z
```

**Mancano 13,1 secondi**, e il documento scrive «esatti» **due volte**. ⚠ L'unica lettura che salva
la frase — *Chrome conta 7 giorni dall'istante del clic, che è avvenuto 13 s prima della riga di
registro* — è plausibile e **non è scritta da nessuna parte**: e proprio quella lettura farebbe di
«604 800 s esatti» una **deduzione**, non la misura che la tabella degli esiti presenta.

⛔ **E il secondo scarto, che è il più netto**: il documento cita come provenienza il registro dello
strumento, e il registro **non contiene quel numero**. `banchi/01-s1b-stato.jsonl` riga 1 dice
letteralmente:

```json
"scadenza_memorizzata":"valore non interpretabile: '13431474587889370'"
```

mentre `banchi/01-s1b-eccezione.sh:282-297` porta un commento che dichiara quel difetto **già
risolto** (*«il banco stampava "valore non interpretabile" su un numero perfettamente sano»*, con la
formula `float(scadenza)/1e6 - 11644473600`). Delle due l'una, e in tutt'e due i casi è una cucitura
rotta: o il dato grezzo di stanotte è stato prodotto da uno strumento **anteriore** alla cura che il
suo stesso file documenta, o la cura c'è e non ha funzionato. La decodifica pubblicata nel `.md` è
stata fatta **a mano**, e la riga che la accredita rimanda a un file che dice «non interpretabile».

**MARCA** `[R]` per l'aritmetica (l'ho ricalcolata) · `[?]` per quale delle due letture spieghi il
`.jsonl`

---

## R12.7 ⛔ I numeri della notte non sono entrati nel posto in cui il progetto tiene i numeri

**DOVE** `fasi/01-filo-nudo.md:595-605` (tabella «la sonda») e `:661-671` (tabella dei banchi) —
colonne **«Misurato»** e **«Data»** contro `web/rapporti/S-esiti-sonda.md:14-21`.

**COSA CONTRADDICE** Il mandato §0 riga 4 (l'agente 4 misura, l'agente 5 scrive i documenti) e la
regola del progetto per cui un numero vive nella tabella di fase con la data accanto.

**COME SI DIMOSTRA** Le due tabelle, riga per riga:

| | `S-esiti-sonda.md` dice | `fasi/01-filo-nudo.md` ha in «Misurato / Data» |
|---|---|---|
| S7 | *«⭐ **SÌ**, completa, quattro controlli su quattro»*, `deltaY = +114`, 2026-08-10 20:59 UTC | riga 601: **vuote** |
| S1b | *«⏳ AVVIATA: giorno 0 preso»*, impronta e scadenza | riga 597: **vuote** |
| S5 | *«⚠ metà»*, Chrome 150 % → **2880×1620** | riga 600: **vuote** |

⛔ E S7 non porta solo un numero: porta una **prescrizione per il prodotto** — *«il server RCP deve
invertire l'asse verticale»* (`S-esiti-sonda.md:16, 41, 336`). `RCP.md:1275` tiene ancora *«`[?]` Il
segno è da misurare, non da decidere»*, e `RCP.md:1280-1300` è ancora il riquadro «va misurato». ⛔ La
misura è stata fatta stanotte e **l'arbitro non lo sa**: la `[?]` è aperta in `RCP.md` e chiusa in un
rapporto che `RCP.md` non cita. È la forma «una cosa che tutti danno per fatta da un altro», e qui
per fortuna nel verso innocuo (una `[?]` rimasta aperta) invece che in quello caro (una `[?]`
promossa a fatto in silenzio).

**MARCA** `[R]`

---

## R12.8 ⛔ Il server di prodotto non ha nessuna strada dichiarata per arrivare dove i banchi lavorano — e il suo nome collide con la loro cartella

**DOVE** `src/costruisci.sh:6` (`bash /srv/src/remotix/costruisci.sh`) contro
`banchi/01-b8-lancia.sh:61` (`DENTRO=/srv/src`), `banchi/01-b6-lancia.sh:130-131`
(`FUORI=/media/REMOTIX/src`), `banchi/01-b13-lancia.sh:55-56`.

**COSA CONTRADDICE** `LEZIONI.md` §1.9 ottava veste, e `banchi/01-b8-lancia.sh:178-215`, che è il
modello scritto dallo stesso progetto: *«CHE SERVER È QUELLO CHE STO PER ACCENDERE»*, con il conto
delle righe innestate nei due sorgenti e il confronto delle date fra binario e sorgente.

**COME SI DIMOSTRA** Tre fatti, ciascuno con la sua ricerca e il suo denominatore:

1. **nessun banco lo accende.** Su 9 script `01-b*-lancia.sh` + `01-c2-lancia.sh`, il binario è
   sempre `…/b2/ngtcp2/build/examples/bsslserver`; `remotix` compare **zero volte** (denominatore:
   10 script di lancio). Controllo positivo: la stessa ricerca trova `bsslserver` in **14 file** di
   `banchi/`;
2. **nessun documento lo nomina.** `grep` di `src/main.c`, `src/rcp.c`, `src/trasporto.c`,
   `src/costruisci.sh` su `README.md`, `fasi/01-filo-nudo.md`, `DECISIONI.md`, `RCP.md`,
   `SPECIFICHE.md`, `PIANO.md`: **zero occorrenze in tutti e sei**. Controllo positivo: la stessa
   ricerca trova `banchi/rcp/rcp.c` **2 volte** in `fasi/01-filo-nudo.md`. E `DECISIONI.md:1881`
   dice ancora, in presente: *«il bersaglio è **il loro server d'esempio**, `bsslserver`, non un
   server nostro»*;
3. **la cartella dove `costruisci.sh` si aspetta di stare non è quella dove i banchi vivono.**
   `/srv/src` è la cartella **dei banchi** (`01-b8-lancia.sh:8`:
   `bash /media/REMOTIX/src/01-b8-lancia.sh`); `costruisci.sh` chiede `/srv/src/**remotix**/`, e
   nessuno script del repo copia niente lì.

⛔ Il costo: `src/costruisci.sh` è scritto bene — butta il binario vecchio prima di ricostruire
(`:93-99`), controlla **cinque marche dentro il binario** (`:137-145`) e ha il **controllo positivo
dello strumento** (`:157-165`), che è il rimedio esatto all'ottava veste. ⚠ Tutto questo non è mai
stato eseguito da nessuna parte in questo repo: `src/` non contiene né `remotix` né alcun `.o`, e
`git status` la dà **untracked**, mai committata. ⭐ Un costruttore che si difende dall'ottava veste
è esattamente il pezzo che non si può dare per buono senza averlo acceso una volta.

**MARCA** `[R]` per la mancanza di strada e per l'assenza dai documenti · `[?]` se il binario sia mai
stato costruito (non posso vedere la macchina di prova)

---

## R12.9 ⛔ La stessa opzione, due nomi; la stessa costante, tre scritture

**DOVE e COME SI DIMOSTRA** — due casi concreti, entrambi verificati con `grep`:

**a) il file dei ban.** `src/main.c:115` `strcmp(a, "--ban")` contro
`banchi/01-b3-rcp-innesta.py:1511` `{"ban-file", required_argument, …}` e
`banchi/01-b8-lancia.sh:231` `"--ban-file=$BAN_FILE"`. ⛔ Chi porta al prodotto la riga di comando che
i banchi usano da stanotte ottiene `aiuto()` e **uscita 2** (`src/main.c:121-124`) — cioè un
fallimento chiaro, che è il modo giusto di sbagliare. ⚠ Ma è la **stessa opzione con due nomi**, e la
`[?]` è quale dei due `RCP.md` intenda: nessuno dei sei documenti nomina l'uno o l'altro
(`grep` di `--ban`, `--ban-file`, `--sblocca`, `--comando-socket` sui sei: **zero occorrenze**, con
controllo positivo su «comando di sblocco», che compare **14 volte** in 5 dei 6 — tutte e sole
descrizioni a parole, mai un meccanismo). `[R]`

**b) le dodici ore.** Sono scritte tre volte, in tre formati:

| dove | come | che cosa dice a chi ha 2 ore residue |
|---|---|---|
| `src/rcp.c:308` | `#define BAN_DURATA 43200000u` | — (è la verità) |
| `src/pagina.c:257-262` | calcolata da `restano/3600000` | «riprova fra **2** ore e N minuti» ✔ |
| `src/pagina.html:104` | stringa fissa: *«riprova fra **dodici ore**»* | ⛔ «dodici ore» — **falso** |

⛔ E le due frasi convivono nella **stessa pagina**: `pagina.c` la inietta in `__AVVISO__`
(`src/pagina.c:271`), `pagina.html:104` la stampa come motivo `0x08` quando il congedo arriva da RCP.
Due comportamenti sotto la stessa etichetta, **E2**, dentro un solo documento HTML. `[R]`

---

## R12.10 ⚠ B6 certifica il proprio cronometro con una finestra larga abbastanza da contenere entrambe le risposte alla `[?]` che B8 ha aperto

**DOVE** `banchi/01-b6-tetti.py:1039` `ok_cr = ms_fisso is not None and 1000 <= ms_fisso <= 3000`, e
`:1044` il testo che stampa: *«il secondo fisso di §4.4-bis misurato {…} ms **(B3: 1074-1085 ms)**»*.

**COSA CONTRADDICE** `RCP.md:699` e `fasi/01-filo-nudo.md:463`, che portano la misura di **B8** della
stessa notte: *«la mediana dei tentativi respinti è **2636 ms** su 42 campioni, dove questa [regola]
vuole ~1000»*, con la conclusione *«a governare i tempi è **PAM**, non noi»* — una `[?]` dichiarata
**aperta**.

**COME SI DIMOSTRA** La finestra `[1000, 3000]` accetta `1074` (il ritardo è nostro) **e** `2636`
(il ritardo è di PAM): due esiti che rispondono in modo opposto alla `[?]`, indistinguibili per lo
strumento che B6 dichiara «certificato». ⛔ Nel caso limite in cui il ritardo fisso di §4.4-bis
sparisse del tutto e restasse solo PAM, `ms_fisso` cadrebbe ancora dentro la finestra e la riga
`cert-cronometro` sarebbe **verde**: il controllo positivo di B6 non sa distinguere lo strumento che
funziona dal prodotto che ha perso una protezione. ⚠ E il numero che B6 stampa come riferimento
(`1074-1085`, di B3) è quello che B8 ha appena rimesso in discussione, nella stessa notte, senza che
B6 lo sappia.

**MARCA** `[?]` — è un sospetto sullo strumento, e la chiude una misura, non io

---

## Quel che ho provato a rompere e non si è rotto

⭐ Si scrive, perché impedisce al prossimo di rifare la stessa caccia (mandato §5).

1. **La forma canonica della chiave dell'indirizzo, in tutt'e quattro i posti.** Era il sospetto
   principale del mandato, ed è la cucitura **meglio riuscita** della notte. Ho seguito il valore da
   capo a fondo su tutt'e due i server:

   | | chi produce la stringa | che forma ha | chi la normalizza |
   |---|---|---|---|
   | prodotto, sessione | `src/trasporto.c:113` `snprintf(fuori, cap, "[%.60s]:%.7s", …)` | `[192.168.0.2]:5218` | `solo_indirizzo()` |
   | prodotto, pagina | `src/pagina.c:430-435` `getnameinfo` + `"[%s]:%s"` per IPv6 | vedi sotto | `rcp_chiave_indirizzo()` `:214` |
   | prodotto, sblocco | quel che digita una persona | `192.168.0.2` | `rcp_chiave_indirizzo()` `main.c:183` |
   | innesto, pagina e comando | `util::straddr()` | `[127.0.0.1]:55680` | `rcp_chiave_indirizzo()` `:1162, :1273` |

   ⭐ Tutti e quattro passano per `rcp_chiave_indirizzo()` (`src/rcp.c:393-417`) o per una stringa che
   già porta le quadre, e ho verificato a mano che la funzione sia **idempotente** sui tre ingressi
   che le arrivano davvero: `[192.168.0.2]:5218` → `[192.168.0.2]`; `[192.168.0.2]` → `[192.168.0.2]`;
   `192.168.0.2` → `[192.168.0.2]`. La guardia di `solo_indirizzo()` per l'indirizzo **senza porta**
   (`src/rcp.c:365`, *«se finisce con `]` la porta non c'è»*) regge sul caso IPv6 nudo che la
   romperebbe. E `RCP.md:729-733` **dichiara la stessa regola a parole**, che è l'unico punto in cui
   documento e codice si confermano a vicenda senza intermediari. ⛔ Provato a rompere, **non si è
   rotto**.

   ⚠ Un solo `[?]` resta, e non l'ho potuto chiudere: `src/pagina.c:432-433` mette le quadre **solo
   se `da.ss_family == AF_INET6`**, mentre `src/trasporto.c:113` le mette **sempre**. Il caso in cui
   la differenza si vedrebbe è un client IPv4 che carica la pagina: `provenienza` diventa
   `192.168.0.2:5218` senza quadre — ma `rcp_chiave_indirizzo()` a `:214` le rimette, e la chiave
   torna uguale. **Regge oggi**, e regge per una funzione sola: se qualcuno togliesse quella riga
   214, la pagina direbbe «puoi entrare» a un indirizzo bannato. È la fragilità che `rcp.h:168-178`
   descrive per iscritto, e il codice la rispetta.

2. **B8 non accusa il server sbagliato, e ha il controllo che lo impedisce.** `01-b8-lancia.sh:178-215`
   conta le righe `REMOTIX B3` nei **due** sorgenti innestati, pretende ≥3 e ≥5, e confronta le date
   di binario e sorgenti uscendo **3** se il binario è più vecchio. Cioè B8 sa dire *quale* server ha
   acceso, ed è l'unico banco che lo verifica su due file. Non l'ho rotto.

3. **I contratti di `rcp.h` fra i due ospiti.** Ho confrontato l'insieme delle funzioni chiamate:
   `rcp_apri` · `rcp_ricevi` · `rcp_tempo` · `rcp_libera` · `rcp_violazione` · `rcp_canale_chiuso` ·
   `rcp_chiusa_dal_client` · `rcp_e_finita` · `rcp_stato_nome` · `rcp_bannato` · `rcp_sblocca` ·
   `rcp_ban_carica` · `rcp_chiave_indirizzo`. ⭐ **I due ospiti chiamano lo stesso insieme**: nessuna
   funzione che uno chiama e l'altro no, e nessun contratto cambiato — comprese le tre delicate
   (`rcp_canale_chiuso`, `rcp_chiusa_dal_client`, `rcp_violazione`), che sono quelle in cui l'ospite
   *deve* dire al modulo qualcosa che solo lui vede. ⚠ `rcp_azzera_registro_sessioni()` non è chiamata
   da nessuno dei due, ed è giusto: `rcp.h:135-137` dice «serve SOLO al banco».

4. **`rcp_ban_carica` che restituisce −1, e i due chiamanti.** `src/main.c:154-167` non parte;
   `01-b3-rcp-innesta.py:1338-1347` non parte. **Tutt'e due** distinguono i tre casi — file assente,
   file vuoto, file illeggibile — e tutt'e due lo scrivono. È `LEZIONI.md` §1.9 regola 1 applicata
   nello stesso modo da due mani diverse, e ho provato a trovare uno scarto fra loro senza riuscirci.

5. **`01-b8-sblocca.py` che confonde «non era bannato» con «non ho parlato con nessuno».** Non lo fa:
   `:73-107` restituisce `(risposta, guasto)` con uno dei due sempre `None`, `:157-161` esce **3** sul
   guasto e **0** sul «NON-BANNATO», e la differenza è stampata. Il caso più insidioso — socket
   assente — è quello che gestisce meglio (`:83-88`).

---

## ⭐ Quali cuciture reggono e quali no

| Cucitura | Chi con chi | Verdetto |
|---|---|---|
| la **chiave dell'indirizzo** in quattro posti | 1 · 2 · 5 | ⭐ **regge**, ed è l'unica confermata da tre parti indipendenti (codice, innesto, `RCP.md`) |
| l'**API di `rcp.h`** fra i due ospiti | 1 · 2 | ⭐ **regge**: stesso insieme di chiamate, nessun contratto cambiato |
| **«zero ban» ≠ «non ho potuto leggere»** nei due avvii | 1 · 2 | ⭐ **regge**, scritta due volte allo stesso modo |
| **B8 ↔ l'innesto** (quale server accendo) | 1 · 1 | ⭐ **regge**: è l'unico banco che verifica *due* sorgenti e la data del binario |
| **B6 ↔ la copia compilata** (i tetti) | 3 · 1 | ⚠ **regge per i `#define TETTO_*`**, e per null'altro: nessun hash, nessun `diff`, solo tre numeri (R12.3) |
| il **comando di sblocco** | 1 · 2 | ⛔ **NON regge**: due forme, e quella del prodotto esce 0 dichiarando un successo che non c'è (R12.1) |
| la **pagina del rifiuto** | 1 · 2 · 3 | ⛔ **NON regge**: due formati senza un campo in comune; B8 contro `src/` darebbe tre rossi sull'imputato sbagliato (R12.2) |
| **`src/rcp.c` ↔ `banchi/rcp/rcp.c`** | 2 · 1 | ⛔ **NON regge**: identiche oggi per fortuna, non per costruzione; due storie git diverse da stanotte (R12.3) |
| **B12 ↔ il sorgente che guasta** | 3 · 1 | ⛔ **NON regge**: registra l'impronta di un file che non tocca (R12.4) |
| **B13 ↔ il binario che accende** | 3 · 1 | ⛔ **NON regge**: giudica il codice leggendo l'altra copia, senza il controllo che il banco gemello ha (R12.5) |
| i **numeri della sonda ↔ le tabelle di fase** | 4 · 5 | ⛔ **NON regge**: S7, S1b, S5 misurate e non registrate; la `[?]` del segno della rotella resta aperta in `RCP.md` (R12.7) |
| **S1b ↔ il suo stesso registro** | 4 · 4 | ⛔ **NON regge**: «604 800 esatti» sono 604 786,9, e il `.jsonl` dice «valore non interpretabile» (R12.6) |
| il **server di prodotto ↔ tutto il resto** | 2 · 1,3,4,5 | ⛔ **NON ESISTE**: nessun banco lo accende, nessun documento lo nomina, non è in git, e la cartella dove il suo costruttore si aspetta di stare è quella dei banchi (R12.8) |

⛔ **Il quadro che ne esce, e vale più della somma dei rilievi.** Le cuciture che reggono sono tutte
**dentro** il perimetro dell'innesto: quattro mani su cinque hanno lavorato attorno a `bsslserver` e
si sono trovate, perché avevano un oggetto comune contro cui sbattere. La quinta ha scritto un server
intero — ben scritto, con difese contro le vesti di `LEZIONI.md` §1.9 che i banchi non hanno — e **non
ha sbattuto contro niente**: nessuno l'ha acceso, nessuno l'ha misurato, nessuno l'ha nominato. I
tre punti in cui tocca il lavoro degli altri (lo sblocco, la pagina, la copia di `rcp.c`) sono
esattamente i tre punti in cui diverge, e in **due** di quei tre la divergenza è invisibile a
qualunque banco esistente.

⛔ **Il rischio che questo lascia in eredità, e che è la ragione per cui la lente D esisteva**: la
prima volta che qualcuno punterà un banco di stanotte al server di `src/` — cosa che prima o poi si
farà, perché è il prodotto — otterrà **rossi su un server che le cose le fa**, in tre punti
contemporaneamente. E il precedente di questo progetto dice che quando un banco è rosso e il codice
sembra funzionare, si cerca nel codice per ore prima di sospettare della misura.

⭐ **Il verdetto si dichiara come vuole `REVIEWER.md` §5**: non è un'assoluzione di quel che non ho
segnalato. **Dieci rilievi trovati, di cui sette `[R]` e tre `[?]`**, su **cinque** cuciture che ho
provato a rompere senza riuscirci — quelle le ho elencate, perché siano il denominatore di questa
revisione e non un silenzio.

---

*R12, lente D. Non ho misurato, non ho riscritto, non ho toccato la macchina di prova, non ho fatto
nessun commit. Le cure sono del coder.*
