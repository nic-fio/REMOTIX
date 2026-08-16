# R12-C — I documenti contro quel che è stato fatto la notte del 10 agosto

*Revisione avversariale della notte del 10-11 agosto 2026, **lente C** del
`fasi/rapporti/MANDATO-10-agosto-notte.md` §2: i `.md` dichiarano cose che il codice non fa, o
tacciono cose che il codice fa? Le `[?]` sono state promosse a fatti in silenzio? I numeri hanno la
data, la scena e la provenienza?*

⛔ **Letti prima di scrivere un rilievo**: il mandato per intero, `REVIEWER.md` §0-§4, `CODER.md` §5,
`LEZIONI.md` §1.9 e §2.3-quater, e il verdetto precedente `fasi/rapporti/R11-documenti.md` per
intero. ⛔ **Nessun rilievo di R11 è riportato qui come nuovo**: dove R11 compare, è perché ho
verificato **dove la cura è arrivata e dove no**. Il §A dice quali cure ho trovato complete.

⚠ **Il perimetro, dichiarato prima dei rilievi.** Bersaglio: `README.md`, `SPECIFICHE.md`, `RCP.md`,
`DECISIONI.md`, `PIANO.md`, `LEZIONI.md`, `CODER.md`, `REVIEWER.md`, `STUDI.md` §web,
`fasi/01-filo-nudo.md`, contro l'albero **come sta adesso** — cioè con `src/` presente, il ban in
`banchi/rcp/rcp.c`, i banchi `01-b6/b8/b9/b12/b13/c2/s*` e `web/rapporti/S-esiti-sonda.md`.

⚠ **E un fatto di cronologia che va detto prima, perché spiega la forma di metà dei rilievi e non ne
scusa nessuno**: i cinque `.md` toccati stanotte portano `mtime` **22:10-22:40**; il codice ha
continuato ad arrivare fino alle **23:24** (`src/rcp.c` 23:06, `01-b9-letture.py` 22:54,
`01-b13-*` 22:59, `01-c2-*` 22:59, `01-b12-*` 23:20, `01-s1b-*` e `01-s5-*` 23:23). ⛔ L'agente dei
documenti ha consegnato **prima** degli altri quattro. Il risultato è che la pagina che dice *«si
riparte da qui»* era già falsa nel momento della consegna: chi riprende domani legge lo stato di due
ore prima della fine, e `PIANO.md` §0.1 gli dice di partire proprio da lì.

⚠ **Questa non è una revisione verde.**

---

# I rilievi `[R]`

---

## R12C.1 — Esiste un server di prodotto, `src/`, e **nessun documento lo nomina**; il documento della fase dichiara il contrario

```
DOVE:              fasi/01-filo-nudo.md riga 550; README.md righe 361-368 («Le cartelle»);
                   e l'assenza di «src/» da tutti e dieci i documenti
COSA CONTRADDICE:  l'albero: src/ — 20 file, ~300 kB, un server completo di fase 1
                   (main.c, trasporto.c, webtransport.c, certificati.c, tls.c,
                   pagina.c, registro.c, rcp.c, Makefile, costruisci.sh, pagina.html);
                   e PIANO.md §0.2, che assegna a «Che cosa è stato sviluppato» il
                   compito di dire che cosa la fase ha prodotto
COME SI DIMOSTRA:  fasi/01-filo-nudo.md:550, che apre «Che cosa è stato sviluppato»:
                   «*Nessuna riga di **prodotto** scritta.  Quel che c'è è banco.*»
                   src/main.c:1-8: «main.c — REMOTIX_V2, il server. … E' il server di
                   `SPECIFICHE.md` §1 alla FASE 1: la stretta di mano di RCP su
                   WebTransport, dai due lati, e la pagina servita dal server stesso».
                   ⛔ `grep -n 'src/' README.md SPECIFICHE.md RCP.md DECISIONI.md
                   PIANO.md LEZIONI.md CODER.md STUDI.md §web fasi/01-filo-nudo.md` non
                   restituisce **una sola** riga che nomini questa cartella: le sole
                   occorrenze sono `v1/remotix-c/src/…`, `quiche/src/…`,
                   `/media/REMOTIX/src/…` e `src/sessione.c` di v1.  `[M]`
                   ⛔ E `README.md` §«Le cartelle» (righe 363-368) elenca **tre** voci —
                   `fasi/`, `v1/`, `reference-*/` — e non ha né `src/` né `banchi/`
                   né `web/`.  La cartella che contiene il prodotto non compare nella
                   tabella che dice che cosa contengono le cartelle.
                   ⚠ Il caso concreto, ed è quello che `PIANO.md` §0.1 costruisce: chi
                   riprende domani legge `fasi/01-filo-nudo.md`, legge «nessuna riga di
                   prodotto scritta», e **riscrive da zero un server che esiste** —
                   oppure lo trova per caso con un `ls` e non sa se sia prodotto,
                   scarto, o un esperimento di qualcuno.
                   ⛔ E la conseguenza sulla marca: dal momento in cui `src/` esiste, ogni
                   riga che dice «il server fa X» ha **due** soggetti possibili — il
                   prodotto e l'innesto di `banchi/01-b3-rcp-innesta.py` — e nessun
                   documento dichiara quale.  Il mandato lo nomina come ambiguità; qui è
                   peggio, perché uno dei due soggetti non è mai stato presentato.
MARCA:             [R]
```

---

## R12C.2 — `RCP.md` dichiara in cinque punti che «oggi non esiste nessuna implementazione», e ne esistono almeno tre

```
DOVE:              RCP.md riga 66 (§0-bis), riga 1600 (§9), riga 1388 e riga 1542 (§7.5),
                   riga 1714 (§12); DECISIONI.md riga 280
COSA CONTRADDICE:  RCP.md riga 1714 (§12) nello stesso documento — «quella era l'ultima
                   occasione»; e fasi/01-filo-nudo.md riga 562, che data il primo byte
COME SI DIMOSTRA:  RCP.md:66 (§0-bis) — «⭐ **E la finestra per farlo è adesso**: §9 vieta
                   di aggiungere tipi di messaggio dentro una versione maggiore.  Quel
                   divieto protegge le implementazioni esistenti, e **oggi non ne esiste
                   nessuna**.  Dal primo byte scritto in poi, questo documento si tocca
                   solo come dice §9.»
                   RCP.md:1600 (§9) — «⭐ **E la finestra in cui questo documento si può
                   ancora completare è adesso** … e **oggi non ne esiste nessuna**.»
                   ⛔ Le implementazioni di RCP/1 che esistono adesso, contate:
                     · `banchi/rcp/rcp.c` — **2339 righe** `[M]` (`wc -l`), che
                       `fasi/01-filo-nudo.md`:562 data «**nuovo, 10 agosto**»;
                     · `src/rcp.c` — **identico byte per byte** a quello dei banchi
                       (`diff -q`: nessuna differenza) `[M]`, dentro il server di prodotto;
                     · `banchi/01-b3-cliente.py` — il **secondo lettore**, che
                       01-filo-nudo:565 dichiara «la stretta di mano scritta una seconda
                       volta, in un linguaggio diverso»;
                     · e, a voler essere larghi, `01-b4-validatore.py` e
                       `01-b11-pagina.html`.
                   ⛔ E il documento si smentisce da sé, due sezioni dopo: RCP.md:1714
                   (§12) — «È entrata sotto la clausola di §9 — *«oggi non esiste nessuna
                   implementazione»* — e **quella era l'ultima occasione**: dal primo byte
                   di codice in poi sarebbe stata una deroga».  Il primo byte è stato
                   scritto il 10 agosto; §0-bis e §9 dicono ancora **adesso**.
                   ⚠ Perché non è pedanteria: quelle cinque righe sono l'unica cosa che
                   dice a chi legge **se il protocollo si possa ancora cambiare**.  Chi
                   apre `RCP.md` domani, trova «la finestra è adesso» e aggiunge un tipo
                   di messaggio, fa esattamente lo strappo che §12 dichiara di aver
                   chiuso — e con la benedizione scritta dell'arbitro.
MARCA:             [R]
```

---

## R12C.3 — `RCP.md` §9 conta **due** tipi entrati sotto la sua clausola; §12 e `DECISIONI.md` §1.5 ne contano **quattro**

```
DOVE:              RCP.md riga 1600-1601 (§9)
COSA CONTRADDICE:  RCP.md riga 1714 (§12); RCP.md riga 44 (§0-bis, la casella «26 su 26»);
                   DECISIONI.md righe 262 e 276-279 (§1.5 riga 26 e il paragrafo dei tipi)
COME SI DIMOSTRA:  RCP.md:1600-1601 — «I due tipi aggiunti il 9 agosto (`0x000D`, `0x000E`)
                   sono entrati sotto questa clausola.»
                   RCP.md:1714 (§12) — la funzione di banco «è **§7.5**, due tipi nuovi —
                   `BANCO_MARCA` e `BANCO_ESITO` … ⭐ *È entrata **sotto la clausola di
                   §9***».
                   RCP.md:1143-1144 (§7.1) dà i codici: `0x000F` `BANCO_MARCA`, `0x0010`
                   `BANCO_ESITO`, tutt'e due «*nuovo, 9 ago notte*».
                   DECISIONI.md:276 — «⚠ **E QUATTRO tipi di messaggio sono stati
                   aggiunti** — `RICHIEDI_CHIAVE` e `TELA` il 9 agosto, ⭐ **`BANCO_MARCA` e
                   `BANCO_ESITO` la notte del 9**».
                   ⛔ La cura di **R11.13** — «i due della funzione di banco non comparivano
                   in nessun punto di `DECISIONI.md`» — è stata applicata a `DECISIONI.md`
                   e **non alla riga di `RCP.md` §9 che tiene il conto della clausola**.
                   È la forma dominante di questo progetto, e stavolta il posto rimasto
                   scoperto è **la clausola stessa**: chi verifica quanto è stata usata
                   la finestra irripetibile, contando da §9, ne trova la metà.
MARCA:             [R]
```

---

## R12C.4 — Il «comando di sblocco» è **due comandi incompatibili**, e uno dei due porta scritta la dimostrazione che l'altro non funziona

```
DOVE:              src/main.c righe 81, 171-187; banchi/01-b3-rcp-innesta.py righe
                   1201-1240 e 1274-1286; RCP.md righe 686-690 (§4.4-bis)
COSA CONTRADDICE:  RCP.md riga 689 — «⛔ **Ogni sblocco si scrive nel registro**»;
                   DECISIONI.md riga 599; SPECIFICHE.md riga 212;
                   fasi/01-filo-nudo.md riga 151 (regola B0.3)
COME SI DIMOSTRA:  ⛔ I quattro documenti parlano del comando di sblocco **al singolare e
                   senza soggetto**: RCP.md:687 «un **comando di sblocco sul server**»;
                   README.md:55 «un comando di sblocco sul server»;
                   fasi/01-filo-nudo.md:151 «⛔ **La cura è il comando di sblocco**
                   (§4.4-bis), chiamato fra un banco e l'altro».
                   ⛔ Nell'albero ce ne sono **due, di forma diversa**:
                     · l'**innesto** espone un **socket di controllo** e risponde
                       `TOLTO` / `NON-BANNATO` / `PONG`
                       (`01-b3-rcp-innesta.py`:1228-1240), e il client è
                       `banchi/01-b8-sblocca.py`;
                     · il **prodotto** espone `remotix --sblocca IND`
                       (`src/main.c`:81, 171-187), un secondo processo che carica il file
                       dei ban, toglie la voce, riscrive il file e **esce**
                       (`return era ? 0 : 1`, riga 187).
                   ⛔ **E la seconda forma è quella che il primo agente ha scartato per
                   iscritto, con le ragioni**, in `01-b3-rcp-innesta.py`:1207-1214:
                     «⛔ un SECONDO PROCESSO con un'opzione (`bsslserver --sblocca X`) —
                      **non funziona**, e il modo in cui non funziona e' silenzioso: il ban
                      vive nella memoria del processo che serve, e un secondo processo puo'
                      solo riscrivere il file.  Il server continuerebbe a rispondere
                      `TROPPI_TENTATIVI` fino al riavvio, e ⛔ il primo `salva_ban()` — cioe'
                      il primo ban di chiunque altro — riscriverebbe il file rimettendoci
                      dentro il ban appena tolto.  Chi ha dato il comando lo ha visto uscire
                      con zero.»
                   Il caso concreto è quello per cui §4.4-bis dice che il comando esiste —
                   *«la via d'uscita di chi si banna dal proprio telefono»*: il server sta
                   **girando**, quindi `remotix --sblocca` cade esattamente nel caso
                   descritto, e chi lo ha dato lo vede uscire con `0`.
                   ⛔ **E la riga normativa non è onorata**: RCP.md:689 «Ogni sblocco si
                   scrive nel registro, o un ban tolto e un ban mai scattato hanno lo stesso
                   aspetto».  `src/main.c`:185 fa una `printf` su stdout;
                   `rcp_sblocca()` (`src/rcp.c`:593-604) chiama `salva_ban(NULL, ora)`, e
                   in `salva_ban` **ogni** chiamata a `reg()` è dentro un `if (s)`
                   (righe 487-510): con `s == NULL` nel registro **non finisce niente**.
                   L'innesto invece la onora (`01-b3-rcp-innesta.py`:1275, con il commento
                   che cita la riga).
                   ⚠ Conseguenza sulla regola B0.3, che è «il vincolo più duro del
                   capitolo»: un banco che chiami lo sblocco del prodotto e poi lo dichiari,
                   come B0.3 impone, dichiara una cosa che nel registro non c'è.
MARCA:             [R]
```

---

## R12C.5 — La finestra di **cinque minuti** del ban c'è in tre documenti e nel codice, e manca nei due da cui si scrive il banco

```
DOVE:              README.md righe 52-55; fasi/01-filo-nudo.md riga 440 e la tabella
                   «Il ban» righe 466-475
COSA CONTRADDICE:  DECISIONI.md riga 593; RCP.md riga 650; SPECIFICHE.md riga 204;
                   src/rcp.c riga 307
COME SI DIMOSTRA:  DECISIONI.md:593, con la frase dell'utente accanto — «tre autenticazioni
                   fallite dallo stesso indirizzo (**senza la porta**), ⛔ **dentro 5
                   minuti** — *regola dell'utente, stesso giorno: «i 3 tentativi falliti
                   devono avvenire entro i 5 minuti per far scattare il ban»*».
                   RCP.md:650 — «**tre** autenticazioni fallite … ⛔ **dentro una finestra di
                   5 minuti**.  **Fuori dai cinque minuti il ban non scatta**».
                   SPECIFICHE.md:204 — «Tre autenticazioni fallite dallo stesso indirizzo
                   **entro 5 minuti**».
                   src/rcp.c:307 — `#define FINESTRA 300000u  /* 5 minuti: i tre fallimenti
                   devono starci dentro */`.
                   ⛔ README.md:52-53, sotto il titolo «La regola dell'accesso è cambiata, e
                   l'ha decisa l'utente»: «Tre autenticazioni fallite **consecutive** dallo
                   stesso indirizzo, e quell'indirizzo è fuori per 12 ore.»  Nessuna
                   finestra.
                   ⛔ fasi/01-filo-nudo.md:440, il riquadro che riscrive **B8**: «tre
                   autenticazioni fallite **consecutive** dallo stesso indirizzo, e
                   quell'indirizzo è fuori per **12 ore**».  E la tabella «Il ban» che
                   segue (righe 466-475) elenca sette righe di atteso e **non nomina i
                   cinque minuti in nessuna**.
                   ⚠ «Consecutive» era la **prima** formulazione dell'utente; la finestra è
                   una **terza** frase dello stesso giorno che la stringe.  Le due regole
                   danno esiti opposti sullo stesso ingresso: tre fallimenti alle 0:00,
                   4:00 e 8:00 sono consecutivi ⇒ bannati secondo il README, e **fuori
                   finestra** ⇒ non bannati secondo il codice.
                   ⛔ Il caso concreto morde sul banco, non sulla carta: `01-filo-nudo`
                   B8 è il documento da cui si scrive il banco del ban, e come è scritto
                   ammette un banco che spazi i tre tentativi — che darebbe **rosso sul
                   codice giusto**, che è la forma di `LEZIONI.md` §2.3.
                   ⚠ E la ragione per cui succede è quella che `README.md`:388 vieta: la
                   decisione è **copiata** in quattro documenti invece che rimandata, e le
                   quattro copie non sono uguali.
MARCA:             [R]
```

---

## R12C.6 — B7: il documento della fase dichiara «**gli otto motivi** che questa fase sa produrre», il banco ne prova **sette su quindici** — e lo dichiara come contraddizione col documento

```
DOVE:              fasi/01-filo-nudo.md righe 425-427, 432, 433, 662; README.md riga 47
COSA CONTRADDICE:  banchi/01-b7-congedo.py righe 78-84, 183-192, 211-229
COME SI DIMOSTRA:  fasi/01-filo-nudo.md:425 — «Per ciascuno degli **otto** motivi che questa
                   fase sa produrre — `CHIUSO_DALL_UTENTE`, `VERSIONE_INCOMPATIBILE`,
                   `NIENTE_IN_COMUNE`, `ERRORE_PROTOCOLLO`, `TEMPO_SCADUTO`,
                   `SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`, `SERVER_IN_CHIUSURA` —».
                   Riga 433: «le **otto** frasi devono essere distinte fra loro».
                   Riga 662, nella tabella delle misure: «**B7** — otto motivi dal lato che
                   riceve … | **8 su 8 + 8 frasi distinte** | | |» — e le celle
                   «Misurato» e «Data» sono **vuote**.
                   banchi/01-b7-congedo.py:80-84: «§8.2 ha **quindici** motivi.  ⛔ Stampare
                   «8 su 8» scegliendo gli otto che si sanno provocare e' vero **per
                   costruzione**, ed e' la forma di verde piu' vuota che ci sia: il
                   denominatore va **dichiarato** … Qui i provocabili sono **sette**, e gli
                   altri otto stanno nella tabella `ESCLUSI` con la ragione di ciascuno».
                   `MOTIVI` (righe 183-192) ne elenca **15**; `ESCLUSI` (211-229) ne elenca
                   **8**; 15 − 8 = 7. `[M]`
                   ⛔ E l'ottavo che il documento elenca è proprio quello che il banco
                   **misura** di non poter produrre — `ESCLUSI`, voce `0x0C`:
                     «⛔ il server della fase 1 non ha un percorso di spegnimento:
                      `RCP_SERVER_IN_CHIUSURA` e' dichiarato in `rcp.h` e non compare in
                      nessuna riga di `rcp.c`.  ⚠ MISURATO qui sotto col grep, non supposto
                      — **e contraddice `fasi/01-filo-nudo.md` B7, che lo elenca fra «gli
                      otto motivi che questa fase sa produrre»**.»
                   ⛔ Il banco nomina la contraddizione **per file e per frase**, il
                   documento è stato modificato la stessa notte (`git status`: `M
                   fasi/01-filo-nudo.md`), e la riga è ancora lì.
                   ⚠ E il README ha recepito il numero giusto senza il documento della
                   fase: README.md:47 — «B7 (**7 motivi su 7, 15 frasi su 15**)».  I due
                   documenti dello stesso progetto dichiarano oggi due denominatori diversi
                   per lo stesso banco, e quello che li dichiara sbagliati è quello da cui
                   si riprende la fase.
MARCA:             [R]
```

---

## R12C.7 — **S7 è misurata**, con scena, data e quattro controlli, e `RCP.md` §7.3 tiene ancora la `[?]`; il rapporto che la porta non è nominato da nessun documento

```
DOVE:              RCP.md righe 1275, 1280-1296 (§7.3); fasi/01-filo-nudo.md riga 601
                   (tabella «La sonda», riga S7, celle vuote) e riga 1097
COSA CONTRADDICE:  web/rapporti/S-esiti-sonda.md §1 (righe 25-70) e riga 16
COME SI DIMOSTRA:  RCP.md:1275 — «`[?]` **Il segno è da misurare, non da decidere** — vedi il
                   riquadro», e il riquadro (1280-1296) chiude con «**Finché non è misurata,
                   questa riga resta `[?]`**».
                   web/rapporti/S-esiti-sonda.md:16 — «**S7** … ⭐ **SÌ**, completa, **quattro
                   controlli su quattro** | `ei_device_scroll_discrete(0, +120)` manda la
                   pagina **verso la fine del documento** ⇒ ⛔ **il server RCP deve invertire
                   l'asse verticale**», con la scena per intero (server 192.168.0.2, GNOME
                   headless, libmutter 48.7-0+deb13u1, libei 1.3.901, Firefox 140.13.0esr in
                   `--kiosk`), l'ora (2026-08-10 20:59 UTC), il registro
                   (`banchi/01-s7-esiti.jsonl`) e i controlli, fra cui quello che il
                   riquadro di §7.3 chiedeva — `natural-scroll` nei due stati, col
                   dispositivo rifatto da capo: «✅ **il segno NON cambia**».
                   ⛔ `git diff RCP.md | grep -ci rotella` → **0** `[M]`: `RCP.md` è stato
                   toccato stanotte in dieci punti e §7.3 non è uno di loro.
                   ⛔ fasi/01-filo-nudo.md:601, la riga S7 della tabella «La sonda»:
                   «| S7 | segno della rotella, `natural-scroll` nei due stati | ✅ server |
                   `[?]`, e **non deve cambiare** con la gsetting | | |» — «Misurato» e
                   «Data» vuote, e la misura esiste con tutt'e due.
                   ⛔ E `grep -rn 'S-esiti' --include=*.md .` non trova **nessun** rimando al
                   rapporto da nessuno dei dieci documenti `[M]`: l'unico posto in cui i
                   numeri di stanotte vivono non è raggiungibile da nessuna strada di
                   lettura.
                   ⚠ È **la terza volta** che questo progetto paga la stessa forma — misure
                   vere che i documenti non recepiscono (R11.4, R11.5) — e stavolta il
                   documento che non le recepisce è **l'arbitro**.  Chi scriverà l'iniezione
                   dell'input alla fase 4 legge §7.3, trova `[?]`, e sceglie il segno a
                   caso: il sintomo è *«la rotella va al contrario»*, che §7.3 stessa
                   dichiara essere la forma **E11**.
                   ⚠ Va detto per intero: la misura è su Mutter e §7.3 vincola cinque
                   desktop, quindi la `[?]` **non si chiude tutta** — e il rapporto lo dice
                   di suo (§1.5).  Ma «non chiusa» e «non misurata» sono due stati diversi,
                   e oggi il documento porta il secondo.
MARCA:             [R]
```

---

## R12C.8 — **S5 è misurata** e smentisce la ragione con cui `fasi/01-filo-nudo.md` giustifica il controllo; `SPECIFICHE.md` §6.1-bis e `DECISIONI.md` §5.0-quater tengono la `[?]` che la misura ha chiuso

```
DOVE:              fasi/01-filo-nudo.md riga 205; SPECIFICHE.md righe 367-372
                   (§6.1-bis, `[?]` punto 1); DECISIONI.md righe 1207-1211 (§5.0-quater)
COSA CONTRADDICE:  web/rapporti/S-esiti-sonda.md §3 (righe 160-215) e
                   banchi/01-s5-esiti.jsonl
COME SI DIMOSTRA:  fasi/01-filo-nudo.md:205, la ragione scritta accanto al controllo di S5:
                   «Ma la tela **giusta** è lo schermo in pixel fisici, che **con lo zoom non
                   cambia**: `screen.width` cala di un terzo, `devicePixelRatio` sale di un
                   mezzo, **il prodotto resta**.»
                   web/rapporti/S-esiti-sonda.md:180-183 — «⛔ **Su Chrome 151 non resta.**
                   `screen.width` **non cambia con lo zoom di pagina**, mentre
                   `devicePixelRatio` sale: il prodotto diventa `risoluzione × zoom`.  Un
                   client scritto secondo §6.1-bis, su un portatile 1920×1080 con lo zoom al
                   150 %, dichiarerebbe **2880×1620**».
                   ⛔ E il registro lo porta riga per riga —
                   `banchi/01-s5-esiti.jsonl`, giro `s5-chrome-…`: `dpr 1` →
                   `tela 1920×1080`; `dpr 1.1` → `tela 2112×1188`; `dpr 1.25` →
                   `tela 2400×1350`, con `schermo_l` fermo a **1920** in tutt'e tre `[M]`.
                   Su Firefox 140 il prodotto resta (rapporto §3.1).
                   ⛔ SPECIFICHE.md:367-370 dichiara ancora la cosa come da fare: «`[?]`
                   **Tre cose che nessuno ha misurato** … 1. ⛔ **lo zoom della pagina falsa
                   il conto** … **Va misurato quanto e su quali motori**».  È misurato, e la
                   risposta è *«su uno dei due, del 50 %»*.
                   ⛔ DECISIONI.md:1207-1211 (§5.0-quater, 🔸) tiene la stessa `[?]` — «⛔
                   *l'utente che ha premuto `Ctrl +` prima di collegarsi dichiarerebbe una
                   tela sbagliata, e resterebbe per tutta la sessione*» — e la decisione «la
                   tela = lo schermo del dispositivo in pixel fisici» **poggia su quella
                   `[?]`**, che è precisamente il caso di `LEZIONI.md` §2.3-quater: *una
                   decisione presa citando un comportamento non misurato è presa a metà*.
                   Adesso il comportamento è misurato e va nell'altro verso.
                   ⚠ E non è teoria: `SPECIFICHE.md` §6.1-bis è la formula che il client
                   userà per riempire `ATTACCA`, e una tela `2880×1620` dichiarata su uno
                   schermo `1920×1080` è il difetto che §5.0-quater dice di esistere per
                   evitare.
MARCA:             [R]
```

---

## R12C.9 — Il rimando di S1b manda a una prova che è un'altra cosa, e il rapporto della sonda lo dichiara

```
DOVE:              fasi/01-filo-nudo.md riga 167
COSA CONTRADDICE:  web/rapporti/S1-certificato.md riga 647;
                   web/rapporti/S-esiti-sonda.md righe 89-96
COME SI DIMOSTRA:  fasi/01-filo-nudo.md:167 — «### S1b — quanto dura l'eccezione su Chrome ·
                   `S1 §4.2 P5`».
                   web/rapporti/S1-certificato.md:647, che cosa è **P5**: «dalla stessa
                   pagina: `navigator.serviceWorker.register('/sw.js')`,
                   `navigator.keyboard.lock()`, `navigator.clipboard.writeText('x')`,
                   `document.body.requestPointerLock()` … e stampare
                   `window.isSecureContext` | chiude il §3.9 nella parte rimasta `[?]`».
                   ⛔ È la prova del **contesto sicuro**, e non nomina né la durata né
                   l'eccezione.
                   web/rapporti/S-esiti-sonda.md:89-96 lo dichiara: «⛔ **P5 non è questa
                   prova** … **Nel rapporto S1 non esiste nessuna prova di banco sulla
                   durata**: i sette giorni sono **solo sorgente letto** (§3.1) … ⇒ Il banco
                   qui descritto è **nuovo**, e il rimando in `fasi/01-filo-nudo.md` va
                   corretto: non c'è una procedura da seguire, ce n'era una da scrivere.»
                   ⚠ Il progetto ne ha già trovati due che mandavano nel posto sbagliato
                   (R11.2, R11.18), e la lezione era che il costo lo paga chi segue il
                   rimando: chi apriva S1 §4.2 P5 per eseguire S1b trovava cinque chiamate
                   di API e nessuna procedura, e la spiegazione più naturale è «ho sbagliato
                   io a leggere».
MARCA:             [R]
```

---

## R12C.10 — «Le etichette `S1a…S7` sono nate in `STUDI.md` §web §7»: S5, S6 e S7 **non compaiono in `STUDI.md` §web**, in nessuna riga

```
DOVE:              fasi/01-filo-nudo.md righe 162-165
COSA CONTRADDICE:  STUDI.md §web §7 (righe 379-392), e STUDI.md §web per intero
COME SI DIMOSTRA:  fasi/01-filo-nudo.md:162-165 — «⭐ **E ogni riga porta il rimando puntuale
                   al rapporto dove vive la procedura**: le etichette `S1a…S7` **sono nate in
                   `STUDI.md` §web §7** e **non compaiono in nessuno dei quattro rapporti**».
                   ⛔ `grep -n '\bS5\b\|\bS6\b\|\bS7\b' web.md` → **nessuna riga** `[M]`.
                   STUDI.md §web §7 «Il piano delle misure» (righe 384-390) elenca **sei** voci:
                   S1a, S1b, S2, S3a, S3b, S4.  S5, S6 e S7 non ci sono, e non sono da
                   nessun'altra parte di quel documento.
                   ⛔ E la frase che sbaglia è **quella che stabilisce la convenzione dei
                   rimandi**: le due righe che seguono nello stesso capitolo ne sono la
                   prova — S5 rimanda a `SPECIFICHE.md §6.1-bis · DECISIONI.md §5.0-quater`
                   (riga 200) e S7 a `RCP.md §7.3` (riga 209), cioè **non a un rapporto**,
                   perché non esiste un rapporto che le contenga.  La riga 162 dichiara una
                   regola che le sue stesse due righe successive non rispettano, e la sola
                   che rimanda a un rapporto per davvero — S1b — rimanda alla prova sbagliata
                   (R12C.9).
                   ⚠ Costa poco e vale: tre misure su cinque del Gruppo 1 non hanno una
                   provenienza, e chi le eseguirà non ha modo di sapere da quale lettura sono
                   nate né quale domanda chiudono.
MARCA:             [R]
```

---

## R12C.11 — I tre tetti di B6 hanno un numero nel README **senza marca, senza data e senza scena**, la tabella delle misure ha la cella vuota, e l'istante d'inizio ha tre formulazioni in tre documenti

```
DOVE:              README.md riga 89; fasi/01-filo-nudo.md riga 661 (cella vuota),
                   riga 401 e riga 1100; RCP.md riga 814 (§4.6)
COSA CONTRADDICE:  fasi/01-filo-nudo.md riga 155 (regola B0.6) e riga 591;
                   README.md riga 380 (la definizione di `[M]`)
COME SI DIMOSTRA:  README.md:89 — «⚠ **B6 è giallo per una parola** | i tre tetti scattano a
                   **5,0 · 60,1 · 10,0 s**, ma §4.6 riga 1 fa partire il cronometro dalla
                   **fine del TLS** mentre il codice lo fa partire dall'**apertura del canale
                   di controllo**».
                   ⛔ Tre numeri con il decimale — cioè cronometrati — e **nessuna marca,
                   nessuna data, nessuna scena, nessun dispositivo**.  README.md:380
                   definisce `[M]` come «misurato da noi, sul ferro, **con la data**», e
                   fasi/01-filo-nudo.md:155 (B0.6) e :591 pretendono «la scena, il
                   dispositivo e la **versione** dichiarati accanto a ogni numero».
                   ⛔ E non c'è dove andarli a cercare: fasi/01-filo-nudo.md:661 —
                   «| **B6** — i tre tetti | 5 s · 60 s · 10 s, **col motivo giusto** | | |»,
                   celle «Misurato» e «Data» vuote; e non esiste nessun `.jsonl` di B6
                   (`ls banchi/*.jsonl` → `b2-esiti`, `01-b12-registro`, `01-s1b-stato`,
                   `01-s5-esiti`) `[M]`.
                   ⛔ E l'istante da cui parte il primo tetto ha **tre** formulazioni:
                     · RCP.md:814 (§4.6, la riga normativa) — «**stretta di mano TLS finita**
                       | `CIAO` ricevuto | 5 s»;
                     · fasi/01-filo-nudo.md:401 (B6) — «`[?]` **apertura della SESSIONE**
                       (non «TLS finito» — vedi sotto)», e :1100 «`[?]` se il tetto parta dal
                       TLS o dall'apertura della sessione»;
                     · README.md:89 — il codice parte dall'«**apertura del canale di
                       controllo**», che è una terza cosa: `src/rcp.c`:2320-2332 confronta
                       `ora - s->da_quando`, e `s` nasce quando il canale di controllo si
                       apre.
                   ⚠ È R3.27 rimasta `[?]` mentre il banco l'ha eseguita: il README ne
                   ricava perfino il caso concreto («chi apre una sessione WebTransport e non
                   apre mai il canale non ha nessun tetto addosso e resta lì») — cioè
                   l'informazione c'è, ed è in **un solo** documento, quello che per
                   convenzione riassume e non decide.
MARCA:             [R]
```

---

## R12C.12 — `banchi/rcp/rcp.c` è dichiarato **1292 righe / 875 di codice**; ne misura **2339 / ~1346**, e la riga non nomina il ban

```
DOVE:              fasi/01-filo-nudo.md riga 562
COSA CONTRADDICE:  banchi/rcp/rcp.c e banchi/rcp/rcp.h, e la riga 644 dello stesso
                   documento, che per lo stesso tipo di numero fa la cosa giusta
COME SI DIMOSTRA:  fasi/01-filo-nudo.md:562 — «⭐⭐ `banchi/rcp/rcp.c` + `rcp.h` | **nuovo, 10
                   agosto** … `[M]` **ore 16:30**: `rcp.c` **1292 righe / 875 di codice**,
                   `rcp.h` **131 / 49**.»
                   Misurato adesso `[M]`: `wc -l banchi/rcp/rcp.c` → **2339**;
                   `wc -l banchi/rcp/rcp.h` → **182**; contando le righe non vuote e non di
                   commento, **~1346 di codice**.  Lo scarto è dell'**81 %** sul totale.
                   ⛔ E non è tutto di stanotte: al commit `1a99d8e` (l'ultimo)
                   `git show HEAD:banchi/rcp/rcp.c | wc -l` dava già **2122** `[M]`.  Il
                   numero era vecchio prima della notte e lo è di più adesso.
                   ⛔ La riga descrive `rcp.c` come «**la stretta di mano di RCP/1, in C**» e
                   **non nomina il ban dell'indirizzo**, che è il lavoro della notte
                   (`src/rcp.c`:242-604, ~360 righe: `FINESTRA`, `BAN_DURATA`, `salva_ban`,
                   `rcp_ban_carica`, `rcp_sblocca`, `rcp_bannato`) — cioè la cosa che
                   `DECISIONI.md` §1.9 dichiara essere la decisione dell'utente del giorno.
                   ⚠ E la cura esiste, nello stesso documento, per un numero della stessa
                   natura: la riga 644 porta «*Alle 08:00 la stessa misura dava 456/329: la
                   lettura della capsula di chiusura è cresciuta lì dentro*».  La riga 562
                   aveva già ricevuto lo stesso trattamento una volta («*Diceva «807 righe,
                   662 di codice»*») e stanotte no: è una cura applicata in un posto solo,
                   dentro la stessa tabella.
MARCA:             [M]  — misurato con `wc -l` e `git show HEAD:…`
```

---

## R12C.13 — «Otto banchi scritti»: ne esistono **dodici**, e i quattro che il README delega a chi li scrive sono stati scritti e non aggiunti

```
DOVE:              README.md riga 46; README.md righe 197-198; README.md righe 200-226 e 211-226;
                   fasi/01-filo-nudo.md righe 552-581
COSA CONTRADDICE:  il contenuto di banchi/
COME SI DIMOSTRA:  README.md:46 — «**Otto banchi scritti, sei verdi.** B2 · B3 · B4 · B5 ·
                   B7 · B11.  ⚠ **B6 è giallo** e **B8 non ha finito**.»
                   ⛔ I prefissi distinti in `banchi/` sono **dodici** per la fase 1 `[M]`:
                   `01-b2 01-b3 01-b4 01-b5 01-b6 01-b7 01-b8 01-b9 01-b11 01-b12 01-b13
                   01-c2`, più `00-c1`.  B9 (`01-b9-letture.py`, 41 kB), B12
                   (`01-b12-guasti.py` + `01-b12-lancia.sh` + `01-b12-registro.jsonl`),
                   B13 (`01-b13-proprieta.py` + `01-b13-lancia.sh`) e C2
                   (`01-c2-diagnosi.py` + `01-c2-lancia.sh`) esistono tutti.
                   ⛔ E il README aveva scritto il debito: righe 197-198 — «⚠ **L'elenco è
                   della sera del 10 agosto 2026**: i banchi che nascono dopo — **B9, B12,
                   B13, C2** — li aggiunge qui chi li scrive.»  Sono nati (22:54-23:20) e
                   nessuno li ha aggiunti.  ⚠ E i quattro nominati non sono tutti: l'elenco
                   non prevede nemmeno le **sette pagine della sonda** (`01-s1b-*`,
                   `01-s2-pagina.html`, `01-s3a-pagina.html`, `01-s5-*`, `01-s6-pagina.html`,
                   `01-s7-*`, `01-s-telefono.sh`), che pure esistono.
                   ⛔ Contati per file: `grep -c` su README e su 01-filo-nudo dà **zero**
                   occorrenze per `01-b9`, `01-b12`, `01-b13`, `01-c2`, `01-s1b`, `01-s2`,
                   `01-s3a`, `01-s5`, `01-s6`, `01-s7` `[M]` — dieci banchi che non sono
                   nominati da nessuno dei due documenti.  E `fasi/01-filo-nudo.md`
                   §«Che cosa è stato sviluppato» non nomina nemmeno i file di **B6, B7, B8
                   e B11**, che il README dà per chiusi o eseguiti.
                   ⚠ La regola che rende la lacuna un difetto è quella con cui **R11.21** è
                   stato chiuso, e sta scritta nel README stesso alle righe 193-196: «Un
                   banco che non è nominato dove si dice come rimettere in piedi i banchi ha
                   lo stesso destino di uno che ha bisogno di una mano: **non si può rifare
                   uguale**».  R11.21 è stato chiuso la stessa notte in cui se ne è aperta
                   una versione due volte più grande.
MARCA:             [R]
```

---

## R12C.14 — Nella tabella delle misure, la riga di B8 porta un `[M]` nella colonna dell'**atteso** e la colonna **Data** vuota — è R11.17 nella stessa tabella

```
DOVE:              fasi/01-filo-nudo.md riga 663
COSA CONTRADDICE:  fasi/01-filo-nudo.md riga 591 (l'apertura del capitolo) e riga 620
                   (l'intestazione della tabella); README.md riga 380
COME SI DIMOSTRA:  L'intestazione della tabella (riga 620) è «| Che cosa | Atteso | Misurato
                   | Data |».
                   Riga 663: «| **B8** — ≥ 1 s per campione, **e le tre mediane
                   indistinguibili** | ⚠ `[M]` parziale 10 ago: **2636 ms** di mediana sui
                   42 respinti, cioè **a governare i tempi è PAM**.  Le tre mediane restano
                   da confrontare | | |».
                   ⛔ Le quattro celle sono: *Che cosa* = l'atteso; *Atteso* = **la misura**;
                   *Misurato* = vuota; *Data* = **vuota**.  Il `[M]` sta due colonne a
                   sinistra del suo posto, e la colonna che B0.6 impone non è riempita —
                   il «10 ago» è dentro il testo, non nella cella.
                   ⚠ È esattamente **R11.17**, chiuso ieri per le tre righe di B3 con un
                   riquadro di sette righe (609-614) che spiega perché la cella conta.  La
                   riga di B8 è stata scritta o riscritta la stessa notte, tre righe sotto
                   quel riquadro, senza la cella.  ⛔ Il controllo che l'aveva trovata è
                   meccanico e costa una riga (`awk` sul numero di `|`): dà **cel=5** su
                   tutte le righe, perché il difetto qui non è il numero di celle ma il loro
                   ordine — cioè la cura è stata applicata alla forma che il rilievo
                   descriveva e non alla proprietà che il rilievo proteggeva.
MARCA:             [R]
```

---

## R12C.15 — `web/rapporti/S-esiti-sonda.md` è l'unico posto dove vivono le misure della sonda, e nessun documento lo nomina

```
DOVE:              README.md riga 291 e riga 351; STUDI.md §web riga 23; fasi/01-filo-nudo.md
                   righe 593-605
COSA CONTRADDICE:  l'esistenza di web/rapporti/S-esiti-sonda.md (238 righe, notte del
                   10 agosto), e README.md riga 392 («quando una misura contraddice un
                   documento, lo si aggiorna nello stesso momento, con la data e la fonte»)
COME SI DIMOSTRA:  `grep -rn 'S-esiti' --include=*.md .` → **nessuna riga fuori dal file
                   stesso** `[M]`.
                   README.md:291 — «📖 **il sesto studio** | `STUDI.md` §web, con **quattro
                   rapporti** in `web/rapporti/`»; README.md:351 — «con i **quattro** rapporti
                   di dettaglio in `web/rapporti/`»; STUDI.md §web:23 — «Il dettaglio sta nei
                   **quattro rapporti** in `web/rapporti/`».  In `web/rapporti/` ci sono
                   adesso **sette** file: S1, S2, S3, S4, **S-esiti-sonda**, R1, R2.
                   ⚠ Non contesto il «quattro» — sono i rapporti degli studi, ed è un
                   denominatore dichiarato.  ⛔ Contesto che il quinto, che è **l'unico che
                   porta numeri misurati** e che dichiara di suo di aggiornare sei righe di
                   `fasi/01-filo-nudo.md`, non sia raggiungibile da nessun documento: la
                   tabella «La sonda» (righe 593-605) — cioè il posto naturale — ha le sei
                   righe **vuote** e non rimanda al rapporto.
                   ⚠ Il caso concreto è quello di S7: la misura c'è, il documento dice
                   `[?]`, e l'unica strada per sapere che esiste è aprire a caso una cartella
                   di rapporti.
MARCA:             [R]
```

---

# I sospetti `[?]`

---

## R12C.16 — B12 ha girato **due volte con esiti incompatibili** e nessun documento lo dice; il suo registro dichiara due banchi certificati su dodici

```
DOVE:              banchi/01-b12-registro.jsonl (due righe); fasi/01-filo-nudo.md
                   righe 508-519 (B12) e righe 670-671 (le righe C1 e C2 della tabella
                   delle misure, vuote)
COSA CONTRADDICE:  README.md riga 46 («Otto banchi scritti, sei verdi»);
                   PIANO.md §0.3 regola 4, citata da 01-filo-nudo:509
COME SI DIMOSTRA:  `banchi/01-b12-registro.jsonl`, riga del **21:19:09** —
                   `"certificati": ["B7","C2"], "non_certificati": ["B13","B4"],
                   "mai_provati": ["B10","B11","B2","B3","B5","B6","B8","B9"]`.
                   Riga delle **23:01:46** — `"certificati": ["B4","B9"],
                   "non_certificati": [], "mai_provati": ["B10","B11","B13","B2","B3","B5",
                   "B6","B7","B8","C2"]`.
                   ⛔ Fra i due giri, **B4 passa da «non certificato» a «certificato»**, e
                   **B7 e C2 passano da «certificato» a «mai provato»**, con la stessa
                   `impronta_rcp_c` (`d839839f…`) — cioè **senza che il codice misurato sia
                   cambiato**.
                   ⛔ E il conto che ne esce, nel giro più recente: **2 banchi certificati su
                   12**, dieci «mai provati».  Nessun documento riporta questo numero, e il
                   README dichiara nello stesso momento «sei verdi».  «Verde» e
                   «certificato» sono due cose diverse — `REVIEWER.md` §1 e `MANDATO` §4
                   punto 2 — ma è la seconda che dice se la prima valga qualcosa, ed è
                   quella che non è scritta da nessuna parte.
                   ⚠ Marcato `[?]` e non `[R]` perché non so se le due righe siano due giri
                   completi o due giri parziali con selezione diversa: il registro non porta
                   il denominatore di quel che ha provato a certificare.  ⛔ Ma è proprio
                   quello il punto — `LEZIONI.md` §1.9 punto 4 — e il file è l'unico esito
                   che B12 lascia.
MARCA:             [?]  — si chiude scrivendo nel documento della fase che cosa B12 ha
                          certificato, quando, e su quale denominatore
```

---

## R12C.17 — Il prodotto dichiara **nel proprio commento** due ripieghi di fase che nessun documento registra

```
DOVE:              src/main.c righe 26-32; src/rcp.c riga 172
COSA CONTRADDICE:  SPECIFICHE.md §5.5 (righe 300-316); DECISIONI.md §4.6 (riga 1024);
                   README.md riga 392 e SPECIFICHE.md riga 781 («quando una misura
                   contraddice questo documento, lo si aggiorna nello stesso momento»)
COME SI DIMOSTRA:  src/main.c:26-32 — «⛔ **UN SOLO FILO, E VA DETTO.**  Tutto gira in un
                   ciclo `poll` solo.  ⚠ La verifica PAM **BLOCCA** quel filo … quindi la
                   stretta di mano di un utente **ritarda i pacchetti di chiunque altro**.
                   E' un ripiego dichiarato della fase 1: `SPECIFICHE.md` §5.5 vuole dieci
                   utenti insieme, e prima di allora la verifica va su un filo a parte.»
                   src/rcp.c:172 — `#define MAX_ATTACCATE 16`, con il commento «un server
                   vero lo sostituira' con la sua tabella delle sessioni».
                   ⛔ Il ripiego è dichiarato **dove non lo legge nessuno che non stia
                   leggendo quel file**: `SPECIFICHE.md` §5.5 e `DECISIONI.md` §4.6
                   promettono il multi-tenant e il budget di dieci sessioni senza una riga
                   che dica «alla fase 1 la verifica è sincrona e serializza tutti».  ⛔ E il
                   secondo fisso di §4.4-bis lo rende misurabile: con dieci utenti che
                   entrano insieme, l'ultimo aspetta dieci secondi — e il sintomo,
                   *«il server è lento quando c'è gente»*, non nomina né PAM né il filo.
                   ⚠ Marcato `[?]` e non `[R]` perché un ripiego di fase dichiarato nel
                   codice non è una promessa rotta: è una promessa **non ancora dovuta**.
                   Ma `CODER.md` §5 vuole che il documento si aggiorni «nello stesso
                   momento», e il posto in cui questo va scritto è
                   `fasi/01-filo-nudo.md` §«Che cosa NON ha funzionato» o il confine della
                   fase — non un commento in `main.c`.
MARCA:             [?]  — si chiude scrivendo i due ripieghi dove la fase dichiara i propri
                          confini, o dimostrando che sono già scritti e non li ho trovati
```

---

# §A. Che cosa ho provato a rompere senza riuscirci

*Elencato perché anche questa è informazione (`MANDATO-10-agosto-notte.md` §5), e perché impedisce al
prossimo di rifare la stessa caccia.*

| Che cosa ho provato | Che cosa ho trovato |
|---|---|
| **i rimandi `<file>.md §<n>`, tutti e dieci i documenti, meccanicamente** | uno script che estrae ogni `<file>.md §<n>` e lo confronta con le intestazioni del bersaglio dà **undici** candidati, e **nove sono falsi positivi**: intervalli (`§2.2-2.3`, `§5-bis.1-2`, `§5-bis.6-7`), voci di elenco numerato dentro una sezione (`LEZIONI.md` §9.8, §0.5, §0.3 — esistono come punti 8, 5 e 3), `STUDI.md` §kde §10.2-10.3. I due che restano sono `RCP.md §0` citato da `DECISIONI.md`:262 e :2374 — e **§0 adesso esiste** (R11.18 curato, `RCP.md`:6): non compare nel `grep -n '^#'` solo perché l'intestazione sta dentro una citazione (`> ## 0.`). ⚠ **Nessun rimando fra documenti è rotto.** I due che segnalo (R12C.9, R12C.10) non sono di questa forma: puntano a un `§` che esiste e non contiene la cosa |
| **le diciannove `[R]` e le cinque `[?]` di R11, una per una** | ⭐ **curate**: R11.1 (il 482/333 è diventato 553/373/134/46 con la scomposizione che torna, e i 972/618 sono dichiarati un'altra cosa) · R11.2 (§9 manda a §2.2, e il riquadro racconta l'errore) · R11.3 (il terzo giro rifatto, e la `[?]` sull'impronta è dichiarata aperta in tre posti) · R11.4 (B11 13 su 13 recepito) · R11.5 (le sei proprietà: `DECISIONI.md`:2023 dice «non restano `[?]`») · R11.6 (la configurazione non è più presentata come misura) · R11.7 (il paragrafo su `--togli` riscritto, con quel che resta vero) · R11.8 (`CONNECTION_CLOSE` sparito da §4.4, §8.1 e `DECISIONI.md`:247) · R11.9 (§2.5 e §5: «stream 0» è diventato un riquadro storico) · R11.10 (§4.4-bis: il rifiuto del bannato aspetta anch'esso il secondo, con il riquadro che racconta la ricaduta) · R11.11 (§5.5 ha l'eccezione del cursore nascosto, e `DECISIONI.md` riga 17 ha l'altezza) · R11.12 (i 5 ms del PCM in `DECISIONI.md` riga 15) · R11.13 (riga 26 e «quattro tipi») · R11.14 (la rotella di v1) · R11.15 (§7.5 è 🔸 in tutt'e tre i posti, con `DECISIONI.md` §7.16 aperta) · R11.16 (la riga «vale su tutti e tre i motori» è sparita) · R11.17 (le tre righe di B3 hanno la data — ⚠ ma vedi R12C.14) · R11.18 (§0 esiste, `SPECIFICHE.md §2.3` è diventato «§2 punto 3») · R11.19 (il README distingue i 38 `[R]` dalle 6 `[?]`) · R11.20 (i due conteggi hanno il denominatore scritto) · R11.21 (⚠ chiuso e riaperto più grande, R12C.13) · R11.22, R11.23, R11.15 (portate in `DECISIONI.md` §7.14, §7.15, §7.16, con le due letture, il byte che cambia e il caso concreto) · R11.24 (il README dichiara il motore solo). **Non ho trovato una cura scritta e falsa** |
| **i numeri che compaiono in più documenti** | **tornano tutti**: 553/373/134/46 (e 373+134+46 = 553) in `README`:28, `README`:164 e `01-filo-nudo`:644 · 456/329 come misura delle 08:00 in tutt'e tre · 972/618 sempre dichiarati «i due innesti insieme» · **2636 ms su 42** in `README`:87, `RCP`:699, `01-filo-nudo`:463 e :663, `DECISIONI`:247 · **1074-1085 ms** in `README`:34 e `01-filo-nudo`:651 · **972 byte** del PCM in `RCP`:923 e `01-filo-nudo`:602 e :280. ⛔ **Non ho trovato un numero con due valori** |
| **i conteggi dichiarati** | tornano: `29 + 17 = 46` (`grep -cE '^## R1\.[0-9]+'` → 29, `grep -cE '^### '` → 17) · `28 + 16 = 44` per R3 e R4 · le **tredici** trappole del README (le ho contate: `grep -q` · `\| tail` *(rifatto)* · due percorsi in una stringa · `pkill -f` *(rifatto)* · porte di ieri · `>/dev/null` sulla password · `setsid` · `kill -0` · impronta tagliata · profilo mancante · `tail -60` · `respinto-poi-congedo` · il buffer di Python = 13, con 2 rifatte = **15 occorrenze**, e il denominatore è dichiarato) · le **ventisei** righe di `DECISIONI.md` §1.5 con la 8 caduta = **venticinque** in vigore, e il documento dichiara che quel ventisei non è il ventisei dei messaggi · **26 su 26** corpi di messaggio |
| **le decisioni copiate invece che rimandate** | il ban è l'unica che si copia in quattro documenti, e la copia si è rotta (R12C.5). Le altre voci di `DECISIONI.md` toccate stanotte rimandano: `01-filo-nudo` §«Le decisioni prodotte» porta rimandi e non testo, e il riquadro alla riga 1084 lo dichiara |
| **le marche ✅ / 🔸 / ❓ delle voci nuove** | ⭐ **reggono, ed è il pezzo meglio fatto della notte**. `DECISIONI.md` §1.9 porta **due frasi virgolettate dell'utente con la data**, più una terza per la finestra dei 5 minuti; marca 🔸 la sola riga derivata («che cosa azzera il conto — *derivata da «consecutive»*») invece di stirarla a ✅; e `RCP.md` §4.4-bis marca 🔸 le due righe che non sono dell'utente (le ore che mancano, lo stato HTTP 200). §7.14, §7.15 e §7.16 sono ❓ con le due letture, **il byte che cambia sul filo** e quale sembra più difendibile. Non ho trovato **nessuna 🔸 marcata ✅** né **nessuna ✅ senza frase** |
| **`RCP.md` §4.4-bis contro il ban di `banchi/rcp/rcp.c`, riga per riga** | tiene su tutto tranne il registro dello sblocco (R12C.4): finestra 300 000 ms = 5 min · ban 43 200 000 ms = 12 h · chiave **senza porta** e fra parentesi quadre, con la normalizzazione lato server (`rcp_chiave_indirizzo`) · finestra **scorrevole** sugli ultimi tre · sfratto che non butta mai una voce bannata per una non bannata · file scritto a ogni cambiamento con `rename` atomico · `rcp_ban_carica` che distingue **-1 «non ho potuto guardare»** da **0 «nessun ban»**, che è `LEZIONI.md` §1.9 regola 1 applicata alla lettera |
| **la pagina del rifiuto** | tiene: `src/pagina.c`:252-278 serve la pagina con **`200 OK`** e scrive *«tentativi esauriti.  Riprova fra N ore e M minuti»*, cioè le due righe che §4.4-bis chiede (la 🔸 delle ore, e lo stato 200 con la ragione dell'intermediario) |
| **`src/rcp.c` contro `banchi/rcp/rcp.c`** | ⭐ **identici byte per byte** (`diff -q` su `rcp.c`, `rcp.h`, `autenticazione.c`: nessuna differenza) `[M]`. La divergenza fra i due server **non è nel protocollo**: sta in quel che ci sta attorno — ed è lì che è finito lo sblocco (R12C.4) |
| **`RCP.md` §2.4 contro `src/main.c`** | tiene: due ascoltatori sulla stessa porta 7447, UDP e TCP, con il commento che cita la sezione; e il rifiuto di partire con un `subjectAltName` `0.0.0.0` è §4.1 applicata prima di poterla violare |
| **`README.md` §«Le convenzioni» contro sé stesso** | le quattro marche, la regola della `[?]` provvisoria, «le decisioni stanno in `DECISIONI.md` una sola volta» e l'obbligo di aggiornamento sono coerenti con `CODER.md` §5 e con `LEZIONI.md` §2.3-quater. ⚠ Il difetto non è nella convenzione: è che stanotte non è stata applicata a `src/` (R12C.1) e al ban (R12C.5) |
| **`CODER.md` e `REVIEWER.md`, i rimandi a `SPECIFICA.md` e `REFERENCE.md`** | **non sono rimandi rotti**: `CODER.md`:32-37 e `LEZIONI.md`:28 dichiarano la mappa ai file di v1 (`v1/documenti/SPECIFICA.md`, `v1/documenti/REFERENCE.md`), che esistono, e dichiarano che i `§x.y` puntano alle vecchie e vanno cercati per argomento. È il modello con cui andrebbero trattati i rimandi di R12C.9 e R12C.10 |

---

# §B. Le linee di caccia, e che cosa ha dato ciascuna

| Linea | Esito |
|---|---|
| **il codice che i documenti tacciono** | ⛔ **la vena più ricca della notte, e di gran lunga**: `src/` per intero (R12C.1), dieci banchi non nominati (R12C.13), il rapporto della sonda (R12C.15), due ripieghi dichiarati solo in un commento (R12C.17). ⚠ La causa è di processo e va detta: l'agente dei documenti ha consegnato **due ore prima** degli altri quattro, e nessuno è tornato a chiudere il giro |
| **misure vere che i documenti non hanno recepito** | **tre**, ed è la terza sera di fila che questa forma è la più cara: S7 (R12C.7), S5 (R12C.8), i tre tetti di B6 (R12C.11). ⛔ In due casi su tre il documento che non recepisce è **normativo** — `RCP.md` §7.3 e `SPECIFICHE.md` §6.1-bis — cioè quello contro cui si darà torto a un'implementazione |
| **`[?]` promosse a fatti in silenzio** | ⭐ **nessuna trovata.** Ho cercato in particolare sul ban (dove sarebbe stato facile: `[?]` di `SPECIFICHE.md` §4.2 chiusa da una decisione e non da una misura — ed è dichiarata così), sulle sei proprietà di B2, sulla promozione `[S]`→`[R]` di S1b, e sul secondo fisso, che resta `[?]` **dichiarato** in quattro posti nonostante il ban. Il verso opposto è la vena |
| **`[M]` senza data, scena o dispositivo (B0.6)** | R12C.11 (i tre tetti di B6: nessuna marca, nessuna data, nessuna scena), R12C.14 (il `[M]` di B8 fuori colonna, Data vuota), R12C.12 (un `[M]` datato che il file ha superato dell'81 %). ⚠ E il verso buono va detto: le righe di S7 e S1b nel rapporto della sonda sono **le meglio corredate del progetto** — libmutter 48.7-0+deb13u1, libei 1.3.901, Firefox 140.13.0esr, l'ora in UTC, il registro |
| **numeri con due valori** | ⛔ **nessuno.** È il pezzo di R11 che ha attecchito meglio |
| **conteggi che non tornano** | R12C.13 («otto banchi» contro dodici), R12C.3 (due tipi contro quattro), R12C.6 (otto motivi contro sette su quindici), R12C.16 (due certificati su dodici, non scritto). ⚠ Gli altri sei conteggi dichiarati tornano tutti |
| **rimandi a sezioni inesistenti** | ⭐ **nessuno**, verificato meccanicamente (§A). ⛔ Ma **due rimandi che puntano a un posto reale e sbagliato**: R12C.9 e R12C.10 — una forma che il controllo meccanico **non vede**, e che il progetto ha già pagato due volte con R11.2 e R11.18 |
| **decisioni copiate invece che rimandate** | una sola, e si è rotta esattamente dove la copia perde: R12C.5 |
| **✅ / 🔸 / ❓** | ⭐ niente. §1.9 è il modello, §7.14-§7.16 sono il modo giusto di lasciare aperta una domanda |
| **cure applicate in un posto solo** | **cinque**: R12C.3 (R11.13 non arrivata a `RCP.md` §9), R12C.14 (R11.17 non arrivata alla riga di B8, tre righe sotto il suo riquadro), R12C.13 (R11.21 chiusa e riaperta più grande), R12C.5 (la finestra dei 5 minuti in tre documenti su cinque), R12C.12 (il conto delle righe curato per un file e non per l'altro nella stessa tabella). ⛔ **Resta la forma dominante di questo progetto**, e stanotte l'hanno commessa anche le mani che stavano curandone una uguale |
| **i due server** | R12C.1 e R12C.4. ⚠ La buona notizia è che il protocollo è **lo stesso file**; la cattiva è che tutto quel che gli sta attorno è stato scritto due volte, e nel punto in cui le due stesure divergono una delle due porta scritta la dimostrazione che l'altra non funziona |

---

# §C. Che cosa passa al coder, e in quale ordine

1. **R12C.1** — `src/` va presentato: `fasi/01-filo-nudo.md` §«Che cosa è stato sviluppato» e
   `README.md` §«Le cartelle». Finché non lo è, ogni riga che dice «il server» ha due soggetti.
2. **R12C.4** — le due forme dello sblocco non possono coesistere: o il prodotto prende il socket,
   o si scrive perché nel prodotto la forma a secondo processo basti. E `src/` deve scrivere lo
   sblocco nel registro, che è una riga normativa di `RCP.md` §4.4-bis.
3. **R12C.5** e **R12C.6** — i due documenti da cui si scrivono i banchi (B8 e B7) dichiarano regole
   e denominatori che il codice contraddice. Sono i due punti in cui un banco nascerà **rosso sul
   codice giusto**.
4. **R12C.7**, **R12C.8**, **R12C.11** — le tre misure di stanotte non recepite, e due di loro
   toccano un documento normativo. `RCP.md` §7.3 per prima: è l'arbitro.
5. **R12C.2** e **R12C.3** — cinque righe di `RCP.md` dicono che la finestra per cambiare il
   protocollo è aperta, e §12 dice che si è chiusa. Costa una frase e decide se il protocollo sia
   ancora modificabile.
6. **R12C.13**, **R12C.15**, **R12C.12**, **R12C.14** — il debito di elencazione e i due numeri.
   Il primo il README se l'era già scritto da sé.
7. **R12C.9**, **R12C.10**, **R12C.16**, **R12C.17** — il resto, nell'ordine in cui sta scritto.

⛔ **E il verdetto, dichiarato come tale**: questa revisione **non è verde**. Quindici `[R]` e due
`[?]` su dieci documenti, di cui quattro sono cose che il codice fa e i documenti tacciono, tre sono
misure prese stanotte che nessun documento ha ricevuto, e cinque sono cure applicate in un posto
solo — la forma che questo progetto continua a pagare. ⚠ Nessuno di questi rilievi è una prova che
il resto sia giusto: è solo quel che sono riuscito a rompere (`REVIEWER.md` §0), e il §A dice dove
ho provato e non ci sono riuscito.
